"""Turn English into store facts with a small local model.

The model is only a translator. Invalid JSON, an off-vocabulary field, or
an empty assertion list is a failure: the text is skipped. This module does
not repair spelling, case, or a missing key, and it does not call the
rule-based front end.
"""

from __future__ import annotations

import json
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


def _assertion(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    allowed = {"source", "type", "target", "qualifiers"}
    if set(value) - allowed:
        return None
    source = _slug(value.get("source"))
    relation = value.get("type")
    target = _slug(value.get("target"))
    if source is None or target is None or relation not in ASSERTION_TYPES:
        return None
    qualifiers = _qualifiers(value.get("qualifiers"))
    if qualifiers is None:
        return None
    fact: dict[str, object] = {
        "qualifiers": qualifiers,
        "source": source,
        "target": target,
        "text": "",
        "type": relation,
    }
    return fact


def parse_teach(raw: str) -> Outcome:
    payload = _json_object(raw)
    if isinstance(payload, str):
        return _fail("json_invalid", payload)
    if set(payload) != {"assertions"} or not isinstance(payload["assertions"], list):
        return _fail("off_vocabulary", "teach object must be exactly {assertions: [...]}")
    if payload["assertions"] == []:
        return _fail("empty", "assertions list is empty")
    facts: list[dict[str, object]] = []
    for item in payload["assertions"]:
        fact = _assertion(item)
        if fact is None:
            return _fail("off_vocabulary", "an assertion was off vocabulary")
        facts.append(fact)
    return Outcome(status="ok", assertions=facts)


def parse_question_json(raw: str) -> Outcome:
    payload = _json_object(raw)
    if isinstance(payload, str):
        return _fail("json_invalid", payload)
    if not isinstance(payload.get("kind"), str) or payload["kind"] not in QUERY_KINDS:
        return _fail("off_vocabulary", "query kind is off vocabulary")
    entity = _slug(payload.get("entity"))
    if entity is None:
        return _fail("off_vocabulary", "query entity is not a slug")
    kind = str(payload["kind"])
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


class Translator:
    """Two calls: one for an episode's sentences, one for a question."""

    def __init__(self, client: ChatClient) -> None:
        self.client = client

    def translate_episode(self, sentences: list[str]) -> Outcome:
        numbered = "\n".join(
            f"{index}. {sentence}" for index, sentence in enumerate(sentences, start=1)
        )
        return self._call("TASK teach\n" + numbered, parse_teach)

    def translate_question(self, question: str) -> Outcome:
        return self._call("TASK question\n" + question.strip(), parse_question_json)

    def _call(self, task: str, parse: Callable[[str], Outcome]) -> Outcome:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": with_no_think(task)},
        ]
        try:
            raw = self.client.complete(messages)
        except TransportError as exc:
            return _fail("transport", f"{exc.kind}: {exc}")
        return parse(raw)
