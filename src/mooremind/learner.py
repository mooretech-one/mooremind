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
