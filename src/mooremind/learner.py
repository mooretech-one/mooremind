"""MooreSense external learner.

``load_learner`` constructs the class with no arguments, then calls
``reset``, ``teach``, and ``answer``. ``KeepLearner`` and ``FadeLearner``
are the two presets. The default ``MooreMind`` is ``keep``.

``answer`` reads the question and the choices. It does not read the gold
label, the world state, or the trace. Choices are used only to turn a
phrase the store already produced into that choice's letter. When the
store has no phrase, the reply is ``I don't know`` and the choices are
not consulted.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from mooremind.english import parse_question, parse_sentence
from mooremind.query import Query, interpret
from mooremind.store import ThoughtStore
from mooremind.weights import FADE, KEEP, WeightPolicy

FALLBACK = "I don't know"


class MooreMind:
    """Teach structured assertions and answer from the thought store."""

    policy: WeightPolicy = KEEP
    preset_name: str = "keep"

    def __init__(
        self,
        policy: WeightPolicy | None = None,
        preset_name: str | None = None,
    ) -> None:
        self.policy = type(self).policy if policy is None else policy
        self.preset_name = type(self).preset_name if preset_name is None else preset_name
        self.store = ThoughtStore(self.policy)
        self.from_store = 0
        self.fell_back = 0

    def reset(self) -> None:
        """Drop every fact from the session that just finished.

        The store-versus-fallback counts belong to the run, so they stay.
        """
        self.store.reset()

    def teach(self, assertions: list[Any]) -> None:
        self.store.teach(assertions)

    def answer(self, item: Any) -> str:
        query = interpret(item.question, self.store.names)
        recall = None if query.entity is None else self._recall(query)
        if recall is None:
            self._tally(fell_back=True)
            return FALLBACK
        self.store.reinforce_used(recall.thoughts)
        self._tally(fell_back=False)
        for choice in list(item.choices or []):
            if choice.text.casefold() == recall.phrase.casefold():
                return str(choice.label)
        return recall.phrase

    def stats(self) -> dict[str, int]:
        return {"fell_back": self.fell_back, "from_store": self.from_store}

    def _recall(self, query: Query) -> Any:
        entity = query.entity
        if entity is None:
            return None
        if query.kind == "color":
            return self.store.color(entity)
        if query.kind == "before":
            return self.store.where_before(entity)
        if query.kind == "index":
            return self.store.where_index(entity, 0 if query.index is None else query.index)
        if query.kind == "middle":
            return self.store.where_middle(entity)
        if query.kind == "time":
            return self.store.where_at(entity, query.timeframe or "")
        return self.store.where_now(entity)

    def _tally(self, *, fell_back: bool) -> None:
        if fell_back:
            self.fell_back += 1
        else:
            self.from_store += 1
        path = os.environ.get("MOOREMIND_ACCOUNTING")
        if not path:
            return
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "fell_back": self.fell_back,
            "from_store": self.from_store,
            "preset": self.preset_name,
        }
        destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class KeepLearner(MooreMind):
    """No decay. Later episodes do not erase an unrehearsed fact."""

    policy = KEEP
    preset_name = "keep"


class FadeLearner(MooreMind):
    """Low initial weight and decay. A second quiet episode drops a fact."""

    policy = FADE
    preset_name = "fade"


def _surface(assertion: Any) -> str:
    """The English sentence only. Structured fields are not read."""
    if isinstance(assertion, str):
        return assertion.strip()
    if isinstance(assertion, dict):
        return str(assertion["text"]).strip() if "text" in assertion else ""
    return str(assertion.text).strip()


def _item_id(item: Any) -> str | None:
    try:
        value = item.id
    except Exception:
        return None
    return str(value) if value else None


class TextMooreMind(MooreMind):
    """Same store as ``MooreMind``, fed from English sentences.

    ``teach`` reads each assertion's ``text`` and ignores ``source``,
    ``type``, ``target``, and ``qualifiers``. ``answer`` reads the question
    and the choices. A sentence or a question form the front end does not
    know is a counted miss, not a guess.
    """

    preset_name = "text-keep"

    def __init__(
        self,
        policy: WeightPolicy | None = None,
        preset_name: str | None = None,
    ) -> None:
        super().__init__(policy=policy, preset_name=preset_name)
        self.sentences = 0
        self.sentences_parsed = 0
        self.sentences_unparsed = 0
        self.unparsed_texts: list[str] = []
        self.session_unparsed: list[str] = []
        self._episode_unparsed: list[str] = []
        self.events: list[dict[str, Any]] = []

    def reset(self) -> None:
        super().reset()
        self.session_unparsed = []
        self._episode_unparsed = []

    def teach(self, assertions: list[Any]) -> None:
        parsed: list[dict[str, object]] = []
        episode_unparsed: list[str] = []
        for assertion in assertions:
            text = _surface(assertion)
            self.sentences += 1
            fact = parse_sentence(text) if text else None
            if fact is None:
                self.sentences_unparsed += 1
                episode_unparsed.append(text)
                self.session_unparsed.append(text)
                self.unparsed_texts.append(text)
            else:
                self.sentences_parsed += 1
                parsed.append(fact)
        self._episode_unparsed = episode_unparsed
        # An empty list is still an episode, so decay still runs.
        self.store.teach(parsed)

    def answer(self, item: Any) -> str:
        question = item.question
        query = parse_question(question, self.store.names)
        recognised = query is not None
        entity = None if query is None else query.entity
        recall = None if query is None or entity is None else self._recall(query)
        phrase = None if recall is None else recall.phrase
        if recall is None:
            reply = FALLBACK
            fell_back = True
        else:
            self.store.reinforce_used(recall.thoughts)
            reply = phrase or FALLBACK
            fell_back = False
            for choice in list(item.choices or []):
                if choice.text.casefold() == reply.casefold():
                    reply = str(choice.label)
                    break
        self._tally(fell_back=fell_back)
        self._event(
            item,
            question=question,
            recognised=recognised,
            entity=entity,
            outcome="fallback" if fell_back else "store",
            phrase=phrase,
            reply=reply,
        )
        return reply

    def stats(self) -> dict[str, int | float | str]:
        seen = self.sentences
        rate = None if seen == 0 else self.sentences_unparsed / seen
        return {
            "fell_back": self.fell_back,
            "from_store": self.from_store,
            "sentences": self.sentences,
            "sentences_parsed": self.sentences_parsed,
            "sentences_unparsed": self.sentences_unparsed,
            "unparsed_rate": 0 if rate is None else rate,
        }

    def _accounting_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "fell_back": self.fell_back,
            "from_store": self.from_store,
            "preset": self.preset_name,
        }
        payload.update(self.stats())
        return payload

    def _tally(self, *, fell_back: bool) -> None:
        if fell_back:
            self.fell_back += 1
        else:
            self.from_store += 1
        path = os.environ.get("MOOREMIND_ACCOUNTING")
        if not path:
            return
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self._accounting_payload(), indent=2) + "\n",
            encoding="utf-8",
        )

    def _event(
        self,
        item: Any,
        *,
        question: str,
        recognised: bool,
        entity: str | None,
        outcome: str,
        phrase: str | None,
        reply: str,
    ) -> None:
        event = {
            "entity": entity,
            "episode_unparsed": list(self._episode_unparsed),
            "id": _item_id(item),
            "outcome": outcome,
            "phrase": phrase,
            "question": question,
            "question_recognised": recognised,
            "reply": reply,
            "session_unparsed": len(self.session_unparsed),
        }
        self.events.append(event)
        path = os.environ.get("MOOREMIND_TRACE")
        if not path:
            return
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


class TextKeepLearner(TextMooreMind):
    """Text front end with the ``keep`` weight policy."""

    policy = KEEP
    preset_name = "text-keep"


class TextFadeLearner(TextMooreMind):
    """Text front end with the ``fade`` weight policy. Weights are unchanged."""

    policy = FADE
    preset_name = "text-fade"


def classify_miss(event: dict[str, Any]) -> str:
    """One label for a wrong reply on the text path.

    Order: a sentence this episode did not read, then a question form we do
    not know, then a reply that came from the store and was still wrong or
    empty because the fact is missing, then a bare fallback.
    """
    if event.get("episode_unparsed"):
        return "parse_failure"
    if not event.get("question_recognised"):
        return "unrecognised_question"
    if event.get("outcome") == "store" or event.get("entity"):
        return "store_or_decay"
    return "fallback"
