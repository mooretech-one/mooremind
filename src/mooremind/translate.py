"""Turn English into store facts with a small local model.

The model is only a translator. Invalid JSON, an off-vocabulary field, or
an empty assertion list is a failure: the text is skipped. This module does
not repair spelling, case, or a missing key, and it does not call the
rule-based front end.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from mooremind.llm_http import ChatClient, TransportError, with_no_think
from mooremind.query import Query
from mooremind.thought import ATTRIBUTE_TYPES, LOCATION_TYPES

ASSERTION_TYPES = frozenset({*LOCATION_TYPES, *ATTRIBUTE_TYPES, "is_a"})
QUERY_KINDS = frozenset({"where", "before", "index", "middle", "time", "color"})
QUALIFIER_KEYS = frozenset({"timeframe", "confidence", "scope", "source"})
_SLUG = re.compile(r"^[a-z][a-z0-9_]*$")

# Near-miss names only. Direction-reversing words such as "contains" are
# absent on purpose. Nothing here is copied from a paraphrase item.
RELATION_ALIASES = {
    "at": "at",
    "atop": "on",
    "belongs_to": "held_by",
    "color": "color",
    "colors": "color",
    "colour": "color",
    "colours": "color",
    "held_by": "held_by",
    "in": "in",
    "inside": "in",
    "inside_of": "in",
    "instance_of": "is_a",
    "into": "in",
    "is_a": "is_a",
    "is_an": "is_a",
    "is_in": "in",
    "isa": "is_a",
    "kind_of": "is_a",
    "lives_in": "in",
    "located_in": "in",
    "material": "material",
    "materials": "material",
    "member_of": "is_a",
    "on": "on",
    "on_top_of": "on",
    "onto": "on",
    "owned_by": "held_by",
    "possessed_by": "held_by",
    "shape": "shape",
    "shapes": "shape",
    "size": "size",
    "sizes": "size",
    "subclass_of": "is_a",
    "texture": "texture",
    "textures": "texture",
    "type_of": "is_a",
    "was_in": "in",
}
QUERY_ALIASES = {
    "before": "before",
    "color": "color",
    "colour": "color",
    "current": "where",
    "earlier": "before",
    "index": "index",
    "location": "where",
    "middle": "middle",
    "midpoint": "middle",
    "ordinal": "index",
    "previous": "before",
    "prior": "before",
    "time": "time",
    "timeframe": "time",
    "when": "time",
    "where": "where",
    "where_before": "before",
    "where_now": "where",
}

CHECK_PROMPT = """\
You check a translation against the English. Reply with one JSON object only.
{"decision":"keep"} if the JSON matches the English.
{"decision":"drop"} if it should not be stored.
{"decision":"fix","assertions":[...]} when the task was teach, or
{"decision":"fix","kind":"...","entity":"..."} when the task was a question.
Use the same types and lowercase slugs as the proposal. Do not add a note.
"""

# Three worked examples. Names and sentences are not copied from MooreSense
# or from the paraphrase files in tests/.
SYSTEM_PROMPT = """\
You translate English into JSON for a fact store. Reply with one JSON object
and no other text. Do not explain. Do not wrap the JSON in a list.

When the user says TASK teach, reply:
{"assertions":[{"source":"slug","type":"TYPE","target":"slug"}]}
TYPE is one of: in, on, at, held_by, is_a, color, shape, material, size, texture.
source and target are lowercase slugs made of letters, digits, and underscores.
No spaces and no capitals. Use in when something is in a place or a container,
on when it is on a surface, at only when the sentence says at, held_by when
someone has the thing (source is the thing, target is the holder), is_a when
the source is a member or a subclass of the target, and color when the target
is the colour word. Keep the order of the sentences. A move is two assertions,
the earlier place first. If you cannot represent a sentence in this vocabulary,
do not invent a fact and do not add a note. An optional qualifiers object may
hold timeframe, confidence, scope, or source, each a non-empty string.

When the user says TASK question, reply:
{"kind":"KIND","entity":"slug"}
KIND is one of: where, before, index, middle, time, color.
where asks where it is now. before asks for the previous place. index asks
for a place on the timeline and must include "index" (0 is the first place,
1 the second). middle asks for the middle stop and omits index. time asks for
a timeframe tag and must include "timeframe" such as t1. color asks for the
colour. Omit keys that do not apply.

Example teach. English: The kettle is on the stove.
{"assertions":[{"source":"kettle","type":"on","target":"stove"}]}

Example teach. English: Dot's morning starts in the larder. Dot finishes in the courtyard.
A pibble is cream. Dot is a pibble.
{"assertions":[
 {"source":"dot","type":"in","target":"larder"},
 {"source":"dot","type":"in","target":"courtyard"},
 {"source":"pibble","type":"color","target":"cream"},
 {"source":"dot","type":"is_a","target":"pibble"}
]}

Example question. English: What place was second for Dot?
{"kind":"index","entity":"dot","index":1}
"""


@dataclass
class Outcome:
    """One translator call. ``status`` is ok only when every field checked out."""

    status: str
    detail: str = ""
    assertions: list[dict[str, object]] = field(default_factory=list)
    query: Query | None = None
    mapped: list[str] = field(default_factory=list)
    retried: bool = False
    checked: str = ""
    calls: int = 0


def _fail(status: str, detail: str) -> Outcome:
    return Outcome(status=status, detail=detail)


def _slug(value: object) -> str | None:
    if not isinstance(value, str) or _SLUG.fullmatch(value) is None:
        return None
    return value


def _qualifiers(value: object) -> dict[str, str] | None:
    if value is None:
        return {}
    if not isinstance(value, dict):
        return None
    cleaned: dict[str, str] = {}
    for key, item in value.items():
        if key not in QUALIFIER_KEYS or not isinstance(item, str) or not item.strip():
            return None
        if item != item.strip():
            return None
        cleaned[key] = item
    return cleaned


def _alias_key(value: str) -> str:
    return value.strip().casefold().replace("-", "_").replace(" ", "_")


def _map_token(
    value: object, table: dict[str, str], *, mapping: bool
) -> tuple[str | None, str | None]:
    """Return the canonical name, and a note when the text was rewritten."""
    if not isinstance(value, str):
        return None, None
    if not mapping:
        if value in table and table[value] == value:
            return value, None
        return None, None
    key = _alias_key(value)
    if key not in table:
        return None, None
    mapped = table[key]
    note = None if mapped == value else f"{value}->{mapped}"
    return mapped, note


def _assertion(
    value: object, *, mapping: bool = False
) -> tuple[dict[str, object] | None, list[str]]:
    if not isinstance(value, dict):
        return None, []
    allowed = {"source", "type", "target", "qualifiers"}
    if set(value) - allowed:
        return None, []
    source = _slug(value.get("source"))
    relation, relation_note = _map_token(value.get("type"), RELATION_ALIASES, mapping=mapping)
    target = _slug(value.get("target"))
    if source is None or target is None or relation is None:
        return None, []
    qualifiers = _qualifiers(value.get("qualifiers"))
    if qualifiers is None:
        return None, []
    fact: dict[str, object] = {
        "qualifiers": qualifiers,
        "source": source,
        "target": target,
        "text": "",
        "type": relation,
    }
    notes = [relation_note] if relation_note else []
    return fact, notes


def parse_teach(raw: str, *, mapping: bool = False) -> Outcome:
    payload = _json_object(raw)
    if isinstance(payload, str):
        return _fail("json_invalid", payload)
    if set(payload) != {"assertions"} or not isinstance(payload["assertions"], list):
        return _fail("off_vocabulary", "teach object must be exactly {assertions: [...]}")
    if payload["assertions"] == []:
        return _fail("empty", "assertions list is empty")
    facts: list[dict[str, object]] = []
    notes: list[str] = []
    for item in payload["assertions"]:
        fact, fact_notes = _assertion(item, mapping=mapping)
        notes.extend(fact_notes)
        if fact is None:
            failed = _fail("off_vocabulary", "an assertion was off vocabulary")
            failed.mapped = notes
            return failed
        facts.append(fact)
    return Outcome(status="ok", assertions=facts, mapped=notes)


def parse_question_json(raw: str, *, mapping: bool = False) -> Outcome:
    payload = _json_object(raw)
    if isinstance(payload, str):
        return _fail("json_invalid", payload)
    kind, kind_note = _map_token(payload.get("kind"), QUERY_ALIASES, mapping=mapping)
    if kind is None:
        return _fail("off_vocabulary", "query kind is off vocabulary")
    entity = _slug(payload.get("entity"))
    if entity is None:
        failed = _fail("off_vocabulary", "query entity is not a slug")
        failed.mapped = [kind_note] if kind_note else []
        return failed
    allowed = {"kind", "entity"}
    index: int | None = None
    timeframe: str | None = None
    if kind == "index":
        allowed.add("index")
        index_value = payload.get("index")
        if isinstance(index_value, bool) or not isinstance(index_value, int) or index_value < 0:
            return _fail("off_vocabulary", "index must be a non-negative integer")
        index = index_value
    if kind == "time":
        allowed.add("timeframe")
        timeframe_value = payload.get("timeframe")
        if _slug(timeframe_value) is None:
            return _fail("off_vocabulary", "timeframe is not a slug")
        timeframe = str(timeframe_value)
    if set(payload) != allowed:
        return _fail("off_vocabulary", "query has a missing or extra key")
    return Outcome(
        status="ok",
        mapped=[kind_note] if kind_note else [],
        query=Query(kind=kind, entity=entity, index=index, timeframe=timeframe),
    )


def _json_object(raw: str) -> dict[str, object] | str:
    """Parse one JSON object. A single fence is accepted. Prose is not."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) < 3 or not lines[-1].strip().startswith("```"):
            return "not a single JSON object"
        text = "\n".join(lines[1:-1]).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return "JSON did not parse"
    if not isinstance(payload, dict):
        return "JSON was not an object"
    return payload


def env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().casefold() not in {"0", "false", "no", "off"}


class Translator:
    """Episode and question calls, plus optional mapping, retry, and a check."""

    def __init__(
        self,
        client: ChatClient,
        *,
        mapping: bool = True,
        self_check: bool = True,
        retry: bool = True,
    ) -> None:
        self.client = client
        self.mapping = mapping
        self.self_check = self_check
        self.retry = retry
        self.calls = 0

    def translate_episode(self, sentences: list[str]) -> Outcome:
        numbered = "\n".join(
            f"{index}. {sentence}" for index, sentence in enumerate(sentences, start=1)
        )
        return self._translate("TASK teach\n" + numbered, parse_teach, "teach")

    def translate_question(self, question: str) -> Outcome:
        task = "TASK question\n" + question.strip()
        return self._translate(task, parse_question_json, "question")

    def _translate(self, task: str, parse: Callable[..., Outcome], mode: str) -> Outcome:
        outcome = self._once(task, parse)
        if outcome.status == "json_invalid" and self.retry:
            retried = self._once(
                task + "\n\nRejected: " + outcome.detail + "\nReply with one JSON object only.",
                parse,
            )
            retried.retried = True
            retried.calls = outcome.calls + retried.calls
            outcome = retried
        if outcome.status == "ok" and self.self_check:
            outcome = self._check(task, outcome, mode)
        return outcome

    def _once(self, task: str, parse: Callable[..., Outcome]) -> Outcome:
        self.calls += 1
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": with_no_think(task)},
        ]
        try:
            raw = self.client.complete(messages)
        except TransportError as exc:
            failed = _fail("transport", f"{exc.kind}: {exc}")
            failed.calls = 1
            return failed
        outcome = parse(raw, mapping=self.mapping)
        outcome.calls = 1
        return outcome

    def _check(self, task: str, proposal: Outcome, mode: str) -> Outcome:
        proposed = _proposed_json(proposal, mode)
        check_task = "TASK check\nEnglish:\n" + task + "\nProposed:\n" + proposed
        self.calls += 1
        messages = [
            {"role": "system", "content": CHECK_PROMPT},
            {"role": "user", "content": with_no_think(check_task)},
        ]
        try:
            raw = self.client.complete(messages)
        except TransportError as exc:
            failed = _fail("transport", f"{exc.kind}: {exc}")
            failed.calls = proposal.calls + 1
            failed.mapped = list(proposal.mapped)
            return failed
        decision = _decision(raw, mode, mapping=self.mapping)
        decision.calls = proposal.calls + 1
        decision.retried = proposal.retried
        if decision.checked == "keep":
            proposal.checked = "keep"
            proposal.calls = decision.calls
            return proposal
        if decision.checked == "fix" and decision.status == "ok":
            decision.mapped = list(proposal.mapped) + list(decision.mapped)
            return decision
        if decision.checked == "drop" or decision.status != "ok":
            dropped = _fail("dropped", decision.detail or "self-check did not keep the proposal")
            dropped.checked = decision.checked or "drop"
            dropped.calls = decision.calls
            dropped.mapped = list(proposal.mapped)
            dropped.retried = proposal.retried
            return dropped
        return decision


def _proposed_json(proposal: Outcome, mode: str) -> str:
    if mode == "teach":
        body = {"assertions": _public_assertions(proposal.assertions)}
    else:
        query = proposal.query
        kind = "" if query is None else query.kind
        entity = "" if query is None else query.entity
        body = {"entity": entity, "kind": kind}
        if query is not None and query.kind == "index":
            body["index"] = query.index
        if query is not None and query.kind == "time":
            body["timeframe"] = query.timeframe
    return json.dumps(body)


def _public_assertions(facts: list[dict[str, object]]) -> list[dict[str, object]]:
    shown: list[dict[str, object]] = []
    for fact in facts:
        item: dict[str, object] = {
            "source": fact["source"],
            "target": fact["target"],
            "type": fact["type"],
        }
        qualifiers = fact.get("qualifiers") or {}
        if qualifiers:
            item["qualifiers"] = qualifiers
        shown.append(item)
    return shown


def _decision(raw: str, mode: str, *, mapping: bool) -> Outcome:
    payload = _json_object(raw)
    if isinstance(payload, str):
        failed = _fail("json_invalid", payload)
        failed.checked = ""
        return failed
    decision = payload.get("decision")
    if decision not in {"keep", "fix", "drop"}:
        failed = _fail("off_vocabulary", "decision must be keep, fix, or drop")
        return failed
    if decision == "keep":
        kept = Outcome(status="ok", checked="keep")
        return kept
    if decision == "drop":
        dropped = _fail("dropped", "self-check dropped the proposal")
        dropped.checked = "drop"
        return dropped
    if mode == "teach":
        if "assertions" not in payload:
            return _fail("off_vocabulary", "fix is missing assertions")
        fixed = parse_teach(json.dumps({"assertions": payload["assertions"]}), mapping=mapping)
    else:
        query_body = {key: value for key, value in payload.items() if key != "decision"}
        fixed = parse_question_json(json.dumps(query_body), mapping=mapping)
    fixed.checked = "fix"
    return fixed
