"""Thought store: match, capture, compete, consolidate, prune.

Each ``teach`` call is one episode. Inside a call the assertions are applied
in order, so a move in the same episode keeps the earlier place as history.
Decay runs once at the start of the next episode, and only for relationships
that episode does not restate.
"""

from __future__ import annotations

from typing import Any

from mooremind.phrases import relation_phrase
from mooremind.query import focus_entity
from mooremind.thought import (
    ATTRIBUTE_TYPES,
    LINK_TYPES,
    LOCATION_TYPES,
    Recall,
    Thought,
)
from mooremind.weights import WeightPolicy


class _Cycle(Exception):
    """A location chain walked back into itself."""


def _slot(relation: str) -> str | None:
    """Relations that cannot all be current for one entity at once."""
    if relation in LOCATION_TYPES:
        return "location"
    if relation in ATTRIBUTE_TYPES or relation == "is_a":
        return relation
    return None


def _read(assertion: Any) -> tuple[str, str, str, str, dict[str, str]]:
    if isinstance(assertion, dict):
        raw = assertion
        source = raw["source"]
        relation = raw["type"]
        target = raw["target"]
        text = raw.get("text") or ""
        qualifiers = raw.get("qualifiers") or {}
    else:
        source = assertion.source
        relation = assertion.type
        target = assertion.target
        text = getattr(assertion, "text", "") or ""
        qualifiers = getattr(assertion, "qualifiers", {}) or {}
    return (
        str(source),
        str(relation),
        str(target),
        str(text),
        {str(key): str(value) for key, value in dict(qualifiers).items()},
    )


class ThoughtStore:
    """Relationships, class links, and the history of a move."""

    def __init__(self, policy: WeightPolicy) -> None:
        self.policy = policy
        self.thoughts: list[Thought] = []
        self.names: dict[str, str] = {}
        self.episode = 0
        self._seq = 0

    def reset(self) -> None:
        self.thoughts = []
        self.names = {}
        self.episode = 0
        self._seq = 0

    def teach(self, assertions: list[Any]) -> None:
        """Match, decay, capture, then prune. Available as soon as this returns."""
        parsed = [_read(assertion) for assertion in assertions]
        restated = {(source, relation, target) for source, relation, target, _text, _q in parsed}
        self.episode += 1
        for thought in self.thoughts:
            if (thought.source, thought.relation, thought.target) not in restated:
                thought.weight -= self.policy.decay
        self._prune()
        for source, relation, target, text, qualifiers in parsed:
            self._capture(source, relation, target, text, qualifiers)
        self._prune()

    def reinforce_used(self, thoughts: list[Thought]) -> None:
        """Consolidate thoughts a recall actually read."""
        live = {id(thought) for thought in self.thoughts}
        for thought in thoughts:
            if id(thought) not in live:
                continue
            thought.weight = min(self.policy.ceiling, thought.weight + self.policy.use_reinforce)

    def focus(self, question: str) -> str | None:
        return focus_entity(question, self.names)

    def where_now(self, entity: str) -> Recall | None:
        try:
            described = self._describe(entity, set())
        except _Cycle:
            return None
        if described is None:
            return None
        phrase, thoughts = described
        return Recall(phrase, thoughts)

    def where_before(self, entity: str) -> Recall | None:
        history = [thought for thought in self._locations(entity) if not thought.current]
        if not history:
            return None
        thought = history[-1]
        return Recall(self._direct(thought), [thought])

    def where_at(self, entity: str, timeframe: str) -> Recall | None:
        matches = [thought for thought in self._locations(entity) if thought.timeframe == timeframe]
        if not matches:
            return None
        thought = matches[-1]
        return Recall(self._direct(thought), [thought])

    def where_index(self, entity: str, index: int) -> Recall | None:
        locations = self._locations(entity)
        if index < 0 or index >= len(locations):
            return None
        thought = locations[index]
        return Recall(self._direct(thought), [thought])

    def where_middle(self, entity: str) -> Recall | None:
        locations = self._locations(entity)
        if not locations:
            return None
        return self.where_index(entity, len(locations) // 2)

    def color(self, entity: str) -> Recall | None:
        found = self._color(entity, set())
        if found is None:
            return None
        phrase, thoughts = found
        return Recall(phrase, thoughts)

    def _capture(
        self,
        source: str,
        relation: str,
        target: str,
        text: str,
        qualifiers: dict[str, str],
    ) -> None:
        self._entity(source)
        if relation in LINK_TYPES:
            self._entity(target)
        # Match: the same relationship is already the current fact.
        same = self._find_current(source, relation, target)
        if same is not None:
            # Consolidate: another telling strengthens it. The old record stays.
            same.weight = min(self.policy.ceiling, same.weight + self.policy.reinforce)
            self._apply_qualifiers(same, text, qualifiers)
            same.episode = self.episode
            return
        # Compete: a new value takes the slot. The previous value is history.
        self._supersede(source, relation)
        self._seq += 1
        self.thoughts.append(
            Thought(
                source=source,
                relation=relation,
                target=target,
                weight=self.policy.initial,
                timeframe=qualifiers.get("timeframe") or None,
                confidence=qualifiers.get("confidence") or None,
                origin=qualifiers.get("source") or None,
                scope=qualifiers.get("scope") or None,
                text=text,
                episode=self.episode,
                seq=self._seq,
                qualifiers=dict(qualifiers),
            )
        )

    def _apply_qualifiers(self, thought: Thought, text: str, qualifiers: dict[str, str]) -> None:
        if text:
            thought.text = text
        if qualifiers.get("timeframe"):
            thought.timeframe = qualifiers["timeframe"]
        if qualifiers.get("confidence"):
            thought.confidence = qualifiers["confidence"]
        if qualifiers.get("source"):
            thought.origin = qualifiers["source"]
        if qualifiers.get("scope"):
            thought.scope = qualifiers["scope"]
        thought.qualifiers.update(qualifiers)

    def _supersede(self, source: str, relation: str) -> None:
        slot = _slot(relation)
        if slot is None:
            return
        for thought in self.thoughts:
            if thought.current and thought.source == source and _slot(thought.relation) == slot:
                thought.current = False

    def _find_current(self, source: str, relation: str, target: str) -> Thought | None:
        for thought in reversed(self.thoughts):
            if (
                thought.current
                and thought.source == source
                and thought.relation == relation
                and thought.target == target
            ):
                return thought
        return None

    def _prune(self) -> None:
        floor = self.policy.prune_below
        self.thoughts = [thought for thought in self.thoughts if thought.weight >= floor]

    def _entity(self, entity: str) -> None:
        self.names.setdefault(entity, entity.replace("_", " "))

    def _locations(self, entity: str) -> list[Thought]:
        return [
            thought
            for thought in self.thoughts
            if thought.source == entity and thought.relation in LOCATION_TYPES
        ]

    def _current_location(self, entity: str) -> Thought | None:
        found = [
            thought
            for thought in self.thoughts
            if thought.current and thought.source == entity and thought.relation in LOCATION_TYPES
        ]
        if not found:
            return None
        for relation in LOCATION_TYPES:
            matches = [thought for thought in found if thought.relation == relation]
            if matches:
                return matches[-1]
        return found[-1]

    def _direct(self, thought: Thought) -> str:
        name = self.names.get(thought.target, thought.target.replace("_", " "))
        return relation_phrase(thought.relation, name)

    def _describe(self, entity: str, seen: set[str]) -> tuple[str, list[Thought]] | None:
        if entity in seen or len(seen) > 6:
            raise _Cycle()
        location = self._current_location(entity)
        if location is None:
            return None
        phrase = self._direct(location)
        # ``at`` is the room. The chain stops, matching the harness phrase.
        if location.relation == "at" or self._current_location(location.target) is None:
            return phrase, [location]
        rest = self._describe(location.target, seen | {entity})
        if rest is None:
            return phrase, [location]
        tail, thoughts = rest
        return f"{phrase}, {tail}", [location, *thoughts]

    def _color(self, entity: str, seen: set[str]) -> tuple[str, list[Thought]] | None:
        if entity in seen:
            return None
        own = [
            thought
            for thought in self.thoughts
            if thought.current and thought.source == entity and thought.relation == "color"
        ]
        if own:
            thought = own[-1]
            return thought.target, [thought]
        links = [
            thought
            for thought in self.thoughts
            if thought.current and thought.source == entity and thought.relation == "is_a"
        ]
        if not links:
            return None
        link = links[-1]
        parent = self._color(link.target, seen | {entity})
        if parent is None:
            return None
        phrase, thoughts = parent
        return phrase, [link, *thoughts]
