"""Closed cues for the question the harness asks.

Assertions arrive already structured. The question does not: it is one
English sentence. This is not a parser. It looks for a stored name and a
handful of cue words the learn questions actually use.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_ORDINALS = {"second": 1, "third": 2, "fourth": 3, "fifth": 4}


@dataclass(frozen=True)
class Query:
    kind: str
    entity: str | None
    index: int | None = None
    timeframe: str | None = None


def focus_entity(question: str, names: dict[str, str]) -> str | None:
    """Longest stored name that occurs as a whole word or phrase."""
    folded = question.casefold()
    best: str | None = None
    best_len = -1
    best_at = -1
    for entity, surface in names.items():
        pattern = rf"\b{re.escape(surface.casefold())}\b"
        found = list(re.finditer(pattern, folded))
        if not found:
            continue
        length = len(surface)
        position = found[-1].start()
        if length > best_len or (length == best_len and position > best_at):
            best = entity
            best_len = length
            best_at = position
    return best


def interpret(question: str, names: dict[str, str]) -> Query:
    """Map a question onto a store lookup.

    Colour is an attribute. ``start`` and ``first`` are the earliest place.
    ``second`` and the other ordinals are positions on that timeline.
    ``earlier``, ``before``, and ``leave`` are the place just before the
    current one. Anything else asks where the entity is now.
    """
    entity = focus_entity(question, names)
    folded = question.casefold()
    if re.search(r"\bcolou?r\b", folded):
        return Query("color", entity)
    if re.search(r"\b(earlier|before|previous|leave)\b", folded):
        return Query("before", entity)
    if re.search(r"\b(start|first)\b", folded):
        return Query("index", entity, index=0)
    ordinal = re.search(r"\b(second|third|fourth|fifth)\b", folded)
    if ordinal:
        return Query("index", entity, index=_ORDINALS[ordinal.group(1)])
    if re.search(r"\bmiddle\b", folded):
        return Query("middle", entity)
    tagged = re.search(r"\bt(\d+)\b", folded)
    if tagged:
        return Query("time", entity, timeframe=f"t{tagged.group(1)}")
    return Query("where", entity)
