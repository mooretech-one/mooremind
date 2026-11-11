"""Surface form of one stored relation.

The wording matches the harness choices (``in the shed``, ``held by veda``)
so a known fact can be reported as a choice letter. ``at`` is rendered as
``in``, and it does not walk any further. This is a renderer, not a parser.
"""

from __future__ import annotations

import re

_CUP_LABEL = re.compile(r"cup [A-Z]")


def needs_the(name: str) -> bool:
    """A labeled cup such as ``cup A`` is used without an article."""
    return _CUP_LABEL.fullmatch(name) is None


def in_phrase(name: str) -> str:
    if needs_the(name):
        return f"in the {name}"
    return f"in {name}"


def on_phrase(name: str) -> str:
    if needs_the(name):
        return f"on the {name}"
    return f"on {name}"


def relation_phrase(relation: str, name: str) -> str:
    if relation in {"at", "in"}:
        return in_phrase(name)
    if relation == "on":
        return on_phrase(name)
    if relation == "held_by":
        return f"held by {name}"
    return name
