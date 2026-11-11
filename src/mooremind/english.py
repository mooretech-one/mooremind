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
from dataclasses import dataclass, field

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

# Still refused after the clause segmenter, inverted order, possessives,
# from-to moves, clefts, and pronoun substitution. Telegraphic lists and
# questions with none of the cue words stay unread.
UNHANDLED = (
    "a telegraphic list, such as 'First the kitchen, afterwards the hall, for Tess'",
    "a compressed biography, such as 'Once in the shed, later the garden: that is Veda'",
    "residence, tucking, hosting, or 'hands are on' wordings",
    "a question with no where, which, who, whom, colour, color, or hue",
    "negation, and relative clauses other than 'who is <colour>'",
)

_LEAD = re.compile(r"^(?:at first|then|after that|next|later)\s+")
_ARTICLE = ("the", "a", "an", "that")
_SPLIT = re.compile(r"\s*;\s*|\s*,\s+and\s+|\s+and\s+|\s*,\s+but\s+|\s+but\s+")
_UNLIKE = re.compile(r",\s+unlike\b.*$")
_CLEFT = re.compile(r"^it is (.+?) that (.+)$")
_SUBJECTS = re.compile(r"\b(he|she|it|they|him|her|them)\b")
_ONE = re.compile(r"\bone\b")

_QUESTION = re.compile(
    r"\b(where|which|who|whom|colou?r|color|hue)\b",
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


@dataclass
class Memory:
    """Names mentioned while one episode is being read.

    ``subject`` is the latest named subject. ``kind`` is the latest class.
    Pronouns bind to those, and only inside the episode that is open.
    """

    subject: str | None = None
    kind: str | None = None
    pronouns: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Read:
    facts: list[dict[str, object]]
    unparsed: list[str]
    pronouns: list[tuple[str, str]]


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


def _inverted_in(match: re.Match[str], text: str) -> dict[str, object] | None:
    """'In the loft sits Nim'."""
    return _link(match.group(2), "in", match.group(1), text)


def _inverted_hold(match: re.Match[str], text: str) -> dict[str, object] | None:
    """'Holding the pot is Tess'."""
    return _link(match.group(1), "held_by", match.group(2), text)


def _poss_has(match: re.Match[str], text: str) -> dict[str, object] | None:
    """'Nim's basket has the pebble' -> the pebble is in the basket."""
    return _link(match.group(3), "in", match.group(2), text)


def _where_keeps(match: re.Match[str], text: str) -> dict[str, object] | None:
    """'The shed is where Tess keeps the bell' -> the bell is in the shed."""
    return _link(match.group(3), "in", match.group(1), text)


def _many(text: str, *facts: dict[str, object] | None) -> list[dict[str, object]] | None:
    built = [fact for fact in facts if fact is not None]
    if len(built) != len(facts):
        return None
    for fact in built:
        fact["text"] = text
    return built


def _from_to(match: re.Match[str], text: str) -> list[dict[str, object]] | None:
    return _many(
        text,
        _link(match.group(1), "in", match.group(2), text),
        _link(match.group(1), "in", match.group(3), text),
    )


def _from_to_front(match: re.Match[str], text: str) -> list[dict[str, object]] | None:
    """'From the loft Nim shifted to the shed'."""
    return _many(
        text,
        _link(match.group(2), "in", match.group(1), text),
        _link(match.group(2), "in", match.group(3), text),
    )


def _describes(match: re.Match[str], text: str) -> dict[str, object] | None:
    """'Olive describes a brindle' -> the brindle kind is olive."""
    if not _colour(match.group(1)):
        return None
    return _link(match.group(2), "color", match.group(1), text)


def _except(match: re.Match[str], text: str) -> list[dict[str, object]] | None:
    """'Every mottle is navy except Bramble, who is pearl'."""
    kind, usual, member, own = match.groups()
    return _many(
        text,
        _link(kind, "color", usual, text),
        _link(member, "is_a", kind, text),
        _link(member, "color", own, text),
    )


def _note(memory: Memory, facts: list[dict[str, object]]) -> None:
    for fact in facts:
        source = str(fact["source"])
        relation = str(fact["type"])
        target = str(fact["target"])
        if relation == "is_a":
            memory.kind = target
        elif relation == "color" and source not in COLOURS:
            # A member's own colour must not wipe the class just recorded.
            if memory.kind is None or source == memory.kind:
                memory.kind = source
        memory.subject = source


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
    (
        re.compile(
            r"^(?:in|inside|on|at) the (.+?) "
            r"(?:sits|is|stands|lies|remains|rests|lives) (.+)$"
        ),
        _inverted_in,
    ),
    (re.compile(r"^holding (?:the |a |an |that )?(.+?) is (.+)$"), _inverted_hold),
    (
        re.compile(r"^the (.+?) is where (.+?) keeps (?:the |a |an )?(.+)$"),
        _where_keeps,
    ),
    (
        re.compile(r"^(.+?) (?:went|goes|moved|moves|shifted) from the (.+?) to the (.+)$"),
        _from_to,
    ),
    (
        re.compile(r"^from the (.+?) (.+?) (?:went|shifted|moved|moves) to the (.+)$"),
        _from_to_front,
    ),
    (
        re.compile(r"^every (.+?) is (.+?) except (.+?), who is (.+)$"),
        _except,
    ),
    (re.compile(r"^(.+?) describes (?:a |an )?(.+)$"), _describes),
    (re.compile(r"^(.+?) holds (?:the |a |an |that )?(.+)$"), _contains),
    (
        re.compile(r"^([a-z][a-z0-9]*)'s ([a-z][a-z0-9]*) has (?:the |a |an )?([a-z][a-z0-9]*)$"),
        _poss_has,
    ),
    (re.compile(r"^(.+?) has (?:the |a |an )?([a-z][a-z0-9]*)$"), _contains),
    (re.compile(r"^([a-z][a-z0-9]*)'s colou?r is ([a-z]+)$"), _plain_colour),
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


def _apply(clause: str, text: str) -> list[dict[str, object]] | None:
    for pattern, build in _RULES:
        match = pattern.fullmatch(clause)
        if match is None:
            continue
        built = build(match, text)
        if built is None:
            continue
        if isinstance(built, list):
            return built
        return [built]
    return None


def _resolve(clause: str, memory: Memory) -> tuple[str, list[tuple[str, str]]] | None:
    """Replace he/she/it/they and 'one'. Refuse the clause if one is unbound.

    'in it' / 'inside it' is a container idiom, not a pronoun.
    """
    used: list[tuple[str, str]] = []
    clause = clause.replace(" inside it", " inside ITOK").replace(" in it", " in ITOK")
    if _SUBJECTS.search(clause):
        if memory.subject is None:
            return None
        surface = memory.subject.replace("_", " ")

        def _subject(match: re.Match[str]) -> str:
            used.append((match.group(1), memory.subject or ""))
            return surface

        clause = _SUBJECTS.sub(_subject, clause)
    clause = clause.replace(" ITOK", " it")
    if _ONE.search(clause):
        if memory.kind is None:
            return None
        surface = memory.kind.replace("_", " ")

        def _kind(match: re.Match[str]) -> str:
            used.append(("one", memory.kind or ""))
            return f"a {surface}"

        clause = _ONE.sub(_kind, clause)
    return clause, used


def _prepare(text: str) -> str:
    body = text.strip().rstrip(".!").strip().casefold()
    body = _LEAD.sub("", body)
    body = _UNLIKE.sub("", body)
    return re.sub(r"\s+", " ", body).strip()


def read_sentence(text: str, memory: Memory | None = None) -> Read:
    """Facts from one sentence, plus any clause that was refused.

    Coordination (and / but / semicolon) is split. A cleft 'it is X that Y'
    is rewritten to 'X Y' before the rules run. Pronouns bind inside
    ``memory``, which the caller keeps for one episode and then drops.
    """
    remembered = memory if memory is not None else Memory()
    body = _prepare(text)
    if not body:
        return Read([], [text.strip()], [])
    cleft = _CLEFT.fullmatch(body)
    pieces = [f"{cleft.group(1)} {cleft.group(2)}"] if cleft else _SPLIT.split(body)
    facts: list[dict[str, object]] = []
    missed: list[str] = []
    bound: list[tuple[str, str]] = []
    for piece in pieces:
        clause = piece.strip(" ,")
        if not clause:
            continue
        resolved = _resolve(clause, remembered)
        if resolved is None:
            missed.append(clause)
            continue
        clause, used = resolved
        built = _apply(clause, text.strip())
        if not built:
            missed.append(clause)
            continue
        facts.extend(built)
        bound.extend(used)
        remembered.pronouns.extend(used)
        _note(remembered, built)
    return Read(facts, missed, bound)


def parse_sentence(text: str) -> dict[str, object] | None:
    """One fact, or None when the sentence is not exactly one fact."""
    read = read_sentence(text, Memory())
    if read.unparsed or len(read.facts) != 1:
        return None
    return read.facts[0]


def question_recognised(question: str) -> bool:
    """True when a cue word occurs anywhere, not only at the start."""
    return _QUESTION.search(question.strip()) is not None


def parse_question(question: str, names: dict[str, str]) -> Query | None:
    """A store query, or None when the question form is not recognised.

    Recognised questions still use the cue list in ``query.interpret`` to
    choose where-now, a previous place, an ordinal, or a colour. An
    unrecognised form is not quietly treated as where-now.
    """
    if not question_recognised(question):
        return None
    query = interpret(question, names)
    if re.search(r"\bhue\b", question, re.IGNORECASE):
        return Query("color", query.entity)
    return query
