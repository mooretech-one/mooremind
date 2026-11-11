"""An atomic thought: one relationship, its weight, and its qualifiers."""

from __future__ import annotations

from dataclasses import dataclass, field

LOCATION_TYPES = ("in", "on", "at", "held_by")
ATTRIBUTE_TYPES = ("color", "shape", "material", "size", "texture")
LINK_TYPES = frozenset({*LOCATION_TYPES, "is_a"})


@dataclass
class Thought:
    """``[source -> relation -> target]`` plus weight and optional qualifiers.

    ``relation`` is the type of the link. ``origin`` stores a qualifier named
    ``source`` so it is not confused with the entity the relationship starts
    from. ``current`` is false once a more recent fact has taken the same slot.
    The older thought stays in the store.
    """

    source: str
    relation: str
    target: str
    weight: float
    current: bool = True
    timeframe: str | None = None
    confidence: str | None = None
    origin: str | None = None
    scope: str | None = None
    text: str = ""
    episode: int = 0
    seq: int = 0
    qualifiers: dict[str, str] = field(default_factory=dict)


@dataclass
class Recall:
    """A phrase read out of the store, and the thoughts that supported it."""

    phrase: str
    thoughts: list[Thought]
