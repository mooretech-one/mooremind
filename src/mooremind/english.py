"""Rule-based English front end.

The harness can hand the learner a finished assertion. This module does not
read that structure. It reads one sentence and, when the sentence matches a
shape below, emits ``source``, ``relation``, and ``target`` for the store.

A sentence that matches none of the shapes is refused. The caller counts
those refusals. There is no guess and no learned model.

Question forms are a separate gate. A question that is not one of the forms
below is refused, even if a stored name happens to appear in it.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from mooremind.query import Query, interpret

# Ordinary colour words. A class or a member "is <colour>" is a colour fact.
# Anything else after "is" is refused, so an unknown word is not stored as a colour.
COLOURS = frozenset(
    {
        "amber",
        "azure",
        "beige",
        "black",
        "blue",
        "bronze",
        "brown",
        "copper",
        "coral",
        "cream",
        "crimson",
        "cyan",
        "gold",
        "gray",
        "green",
        "grey",
        "indigo",
        "ivory",
        "khaki",
        "lilac",
        "lime",
        "magenta",
        "maroon",
        "mint",
        "navy",
        "olive",
        "orange",
        "peach",
        "pearl",
        "pink",
        "plum",
        "purple",
        "red",
        "rose",
        "rust",
        "scarlet",
        "silver",
        "tan",
        "teal",
        "turquoise",
        "violet",
        "white",
        "yellow",
    }
)

# Shapes this front end will not read. The list is the contract for the
# held-out paraphrases: do not add a shape here and then quietly parse it.
UNHANDLED = (
    "inverted order, such as 'In the loft sits Nim'",
    "a possessive, such as 'Nim's spoon' or 'Veda's arm'",
    "two facts joined in one sentence",
    "a move told as 'from the porch to the yard' in one sentence",
    "pronouns standing in for a name, such as 'it is the cup that holds the marble'",
    "questions that do not start with where, which place, which container, who has, or colour",
)

_LEAD = re.compile(r"^(?:at first|then|after that|next|later)\s+")
_ARTICLE = ("the", "a", "an")

_QUESTION = re.compile(
    r"^(?:"
    r"where (?:is|was|did|can)\b|"
    r"which place\b|"
    r"which container\b|"
    r"who (?:has|is holding|holds)\b|"
    r"what colou?r\b|"
    r"which colou?r\b"
    r")",
    re.IGNORECASE,
)


def _np(text: str) -> str:
    words = text.strip().split()
    if words and words[0] in _ARTICLE:
        words = words[1:]
    return "_".join(words)


def _colour(text: str) -> str:
    word = text.strip()
    if word not in COLOURS:
        return ""
    return word


def _link(source: str, relation: str, target: str, text: str) -> dict[str, object] | None:
    src = _np(source)
    dst = _colour(target) if relation == "color" else _np(target)
    if not src or not dst:
        return None
    return {
        "qualifiers": {},
        "source": src,
        "target": dst,
        "text": text,
        "type": relation,
    }


def _in(match: re.Match[str], text: str) -> dict[str, object] | None:
    return _link(match.group(1), "in", match.group(2), text)


def _held(match: re.Match[str], text: str) -> dict[str, object] | None:
    return _link(match.group(1), "held_by", match.group(2), text)


def _holder_verb(match: re.Match[str], text: str) -> dict[str, object] | None:
    """'Veda is holding the cup' and 'Veda carries the cup'."""
    return _link(match.group(2), "held_by", match.group(1), text)


def _contains(match: re.Match[str], text: str) -> dict[str, object] | None:
    return _link(match.group(2), "in", match.group(1), text)


def _kind_colour(match: re.Match[str], text: str) -> dict[str, object] | None:
    return _link(match.group(1), "color", match.group(2), text)


def _is_a(match: re.Match[str], text: str) -> dict[str, object] | None:
    return _link(match.group(1), "is_a", match.group(2), text)


def _plain_colour(match: re.Match[str], text: str) -> dict[str, object] | None:
    return _link(match.group(1), "color", match.group(2), text)


_Build = Callable[[re.Match[str], str], dict[str, object] | None]

# First match wins. Location and holding come before the bare "is" colour rule.
_RULES: tuple[tuple[re.Pattern[str], _Build], ...] = (
    (re.compile(r"^(.+?) is held by (.+)$"), _held),
    (re.compile(r"^(.+?) is holding (?:the |a |an )?(.+)$"), _holder_verb),
    (re.compile(r"^(.+?) is carrying (?:the |a |an )?(.+)$"), _holder_verb),
    (re.compile(r"^(.+?) carries (?:the |a |an )?(.+)$"), _holder_verb),
    (re.compile(r"^(.+?) contains (?:the |a |an )?(.+)$"), _contains),
    (re.compile(r"^(.+?) has (?:the |a |an )?(.+?) inside it$"), _contains),
    (re.compile(r"^(.+?) has (?:the |a |an )?(.+?) in it$"), _contains),
    (re.compile(r"^(.+?) was left in the (.+)$"), _in),
    (re.compile(r"^(.+?) moves to the (.+)$"), _in),
    (re.compile(r"^(.+?) (?:is|stays|sits|stands|begins) (?:in|inside) the (.+)$"), _in),
    (re.compile(r"^the (.+?) kind counts as (?:a |an )?(.+)$"), _is_a),
    (re.compile(r"^the (.+?) kind is (.+)$"), _kind_colour),
    (re.compile(r"^(.+?) counts as (?:a |an )?(.+)$"), _is_a),
    (re.compile(r"^(.+?) alone is (.+)$"), _plain_colour),
    (re.compile(r"^a (.+?) is (?:a |an )(.+)$"), _is_a),
    (re.compile(r"^an (.+?) is (?:a |an )(.+)$"), _is_a),
    (re.compile(r"^a (.+?) is (.+)$"), _plain_colour),
    (re.compile(r"^an (.+?) is (.+)$"), _plain_colour),
    (re.compile(r"^(.+?) is (?:a |an )(.+)$"), _is_a),
    (re.compile(r"^(.+?) is (.+)$"), _plain_colour),
)


def parse_sentence(text: str) -> dict[str, object] | None:
    """One sentence, or None when the shape is not one we read."""
    original = text.strip()
    body = original.rstrip(".!").strip().casefold()
    body = _LEAD.sub("", body)
    body = re.sub(r"\s+", " ", body).strip()
    if not body:
        return None
    for pattern, build in _RULES:
        match = pattern.fullmatch(body)
        if match is None:
            continue
        built = build(match, original)
        if built is not None:
            return built
    return None


def question_recognised(question: str) -> bool:
    """True when the question starts with a form this front end accepts."""
    folded = question.strip().casefold()
    return _QUESTION.match(folded) is not None


def parse_question(question: str, names: dict[str, str]) -> Query | None:
    """A store query, or None when the question form is not recognised.

    Recognised questions still use the cue list in ``query.interpret`` to
    choose where-now, a previous place, an ordinal, or a colour. An
    unrecognised form is not quietly treated as where-now.
    """
    if not question_recognised(question):
        return None
    return interpret(question, names)
