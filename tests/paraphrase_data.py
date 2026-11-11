"""Our own English items.

Dev stories use sentence shapes the front end is allowed to learn.
Held-out stories were written after that front end was frozen. They use
other word orders and other question forms. Gold comes from the structured
facts on each beat, not from the text learner.
"""

from __future__ import annotations

from dataclasses import dataclass


def fact(source: str, relation: str, target: str) -> dict[str, str]:
    return {
        "qualifiers": "",
        "source": source,
        "target": target,
        "text": f"{source} {relation} {target}",
        "type": relation,
    }


@dataclass(frozen=True)
class Beat:
    sentences: tuple[str, ...]
    facts: tuple[dict[str, str], ...]
    question: str = ""
    kind: str = "where"
    entity: str = ""
    index: int | None = None
    # True when fade, by the published weight rule, should miss the full gold.
    fade_miss: bool = False


@dataclass(frozen=True)
class Story:
    id: str
    subtype: str
    split: str
    beats: tuple[Beat, ...]


def _f(*triples: tuple[str, str, str]) -> tuple[dict[str, str], ...]:
    return tuple(fact(*triple) for triple in triples)


DEV: tuple[Story, ...] = (
    Story(
        "dev.one_shot.loft",
        "one_shot",
        "dev",
        (Beat(("Nim is in the loft.",), _f(("nim", "in", "loft")), "Where is Nim?", entity="nim"),),
    ),
    Story(
        "dev.one_shot.inside",
        "one_shot",
        "dev",
        (
            Beat(
                ("The spoon is inside the cup.",),
                _f(("spoon", "in", "cup")),
                "Where is the spoon?",
                entity="spoon",
            ),
        ),
    ),
    Story(
        "dev.one_shot.carries",
        "one_shot",
        "dev",
        (
            Beat(
                ("Veda carries the ribbon.",),
                _f(("ribbon", "held_by", "veda")),
                "Who has the ribbon?",
                entity="ribbon",
            ),
        ),
    ),
    Story(
        "dev.one_shot.contains",
        "one_shot",
        "dev",
        (
            Beat(
                ("The basket contains the pebble.",),
                _f(("pebble", "in", "basket")),
                "Which place has the pebble?",
                entity="pebble",
            ),
        ),
    ),
    Story(
        "dev.one_shot.left",
        "one_shot",
        "dev",
        (
            Beat(
                ("The tin was left in the shed.",),
                _f(("tin", "in", "shed")),
                "Where is the tin?",
                entity="tin",
            ),
        ),
    ),
    Story(
        "dev.one_shot.stays",
        "one_shot",
        "dev",
        (
            Beat(
                ("Pock stays in the workshop.",),
                _f(("pock", "in", "workshop")),
                "Which place is Pock in?",
                entity="pock",
            ),
        ),
    ),
    Story(
        "dev.update.now",
        "update",
        "dev",
        (
            Beat(
                ("At first Nim is in the loft.", "Then Nim moves to the yard."),
                _f(("nim", "in", "loft"), ("nim", "in", "yard")),
                "Where is Nim now?",
                entity="nim",
            ),
        ),
    ),
    Story(
        "dev.update.earlier",
        "update",
        "dev",
        (
            Beat(
                ("Bramble begins in the porch.", "After that Bramble is in the pantry."),
                _f(("bramble", "in", "porch"), ("bramble", "in", "pantry")),
                "Where was Bramble earlier?",
                kind="before",
                entity="bramble",
            ),
        ),
    ),
    Story(
        "dev.update.middle",
        "update",
        "dev",
        (
            Beat(
                (
                    "At first Tess is in the kitchen.",
                    "Next Tess is in the hallway.",
                    "Later Tess is in the garden.",
                ),
                _f(("tess", "in", "kitchen"), ("tess", "in", "hallway"), ("tess", "in", "garden")),
                "Which place was the middle stop for Tess?",
                kind="middle",
                entity="tess",
            ),
        ),
    ),
    Story(
        "dev.update.second",
        "update",
        "dev",
        (
            Beat(
                (
                    "At first Lumen is in the cellar.",
                    "Then Lumen moves to the shed.",
                    "Next Lumen is in the yard.",
                    "Later Lumen is in the porch.",
                ),
                _f(
                    ("lumen", "in", "cellar"),
                    ("lumen", "in", "shed"),
                    ("lumen", "in", "yard"),
                    ("lumen", "in", "porch"),
                ),
                "Where was Lumen at the second stop?",
                kind="index",
                entity="lumen",
                index=1,
            ),
        ),
    ),
    Story(
        "dev.update.start",
        "update",
        "dev",
        (
            Beat(
                (
                    "At first Pock is in the workshop.",
                    "Then Pock moves to the loft.",
                    "After that Pock is in the garden.",
                ),
                _f(("pock", "in", "workshop"), ("pock", "in", "loft"), ("pock", "in", "garden")),
                "Where did Pock start?",
                kind="index",
                entity="pock",
                index=0,
            ),
        ),
    ),
    Story(
        "dev.update.leave",
        "update",
        "dev",
        (
            Beat(
                (
                    "At first Veda is in the kitchen.",
                    "Then Veda moves to the hallway.",
                    "Next Veda is in the yard.",
                    "Later Veda is in the shed.",
                ),
                _f(
                    ("veda", "in", "kitchen"),
                    ("veda", "in", "hallway"),
                    ("veda", "in", "yard"),
                    ("veda", "in", "shed"),
                ),
                "Which place did Veda leave last?",
                kind="before",
                entity="veda",
            ),
        ),
    ),
    Story(
        "dev.inheritance.default",
        "inheritance",
        "dev",
        (
            Beat(
                ("A mottle is rust.", "Nim is a mottle."),
                _f(("mottle", "color", "rust"), ("nim", "is_a", "mottle")),
                "What colour is Nim?",
                kind="color",
                entity="nim",
            ),
        ),
    ),
    Story(
        "dev.inheritance.exception",
        "inheritance",
        "dev",
        (
            Beat(
                (
                    "A mottle is rust.",
                    "Nim is a mottle.",
                    "Nim alone is olive.",
                    "Veda is a mottle.",
                ),
                _f(
                    ("mottle", "color", "rust"),
                    ("nim", "is_a", "mottle"),
                    ("nim", "color", "olive"),
                    ("veda", "is_a", "mottle"),
                ),
                "What colour is Veda?",
                kind="color",
                entity="veda",
            ),
        ),
    ),
    Story(
        "dev.inheritance.own",
        "inheritance",
        "dev",
        (
            Beat(
                ("A mottle is rust.", "Nim is a mottle.", "Nim alone is olive."),
                _f(
                    ("mottle", "color", "rust"),
                    ("nim", "is_a", "mottle"),
                    ("nim", "color", "olive"),
                ),
                "What colour is Nim?",
                kind="color",
                entity="nim",
            ),
        ),
    ),
    Story(
        "dev.inheritance.kind",
        "inheritance",
        "dev",
        (
            Beat(
                ("The brindle kind is pearl.", "Tess counts as a brindle."),
                _f(("brindle", "color", "pearl"), ("tess", "is_a", "brindle")),
                "Which colour does Tess have?",
                kind="color",
                entity="tess",
            ),
        ),
    ),
    Story(
        "dev.inheritance.two_level",
        "inheritance",
        "dev",
        (
            Beat(
                ("A mottle is navy.", "A snip is a mottle.", "Pock is a snip."),
                _f(
                    ("mottle", "color", "navy"),
                    ("snip", "is_a", "mottle"),
                    ("pock", "is_a", "snip"),
                ),
                "What colour is Pock?",
                kind="color",
                entity="pock",
            ),
        ),
    ),
    Story(
        "dev.inheritance.kind_link",
        "inheritance",
        "dev",
        (
            Beat(
                (
                    "The mottle kind is rust.",
                    "The snip kind counts as a mottle.",
                    "Lumen counts as a snip.",
                ),
                _f(
                    ("mottle", "color", "rust"),
                    ("snip", "is_a", "mottle"),
                    ("lumen", "is_a", "snip"),
                ),
                "Which colour does Lumen have?",
                kind="color",
                entity="lumen",
            ),
        ),
    ),
    Story(
        "dev.composition.chain",
        "composition",
        "dev",
        (
            Beat(
                ("Nim is in the loft.",),
                _f(("nim", "in", "loft")),
                "Where is Nim?",
                entity="nim",
            ),
            Beat(
                ("The pebble is in the basket.", "The basket is held by Nim."),
                _f(("pebble", "in", "basket"), ("basket", "held_by", "nim")),
                "Where is the pebble?",
                entity="pebble",
            ),
        ),
    ),
    Story(
        "dev.composition.late_holder",
        "composition",
        "dev",
        (
            Beat(
                ("Veda is in the shed.",),
                _f(("veda", "in", "shed")),
                "Where is Veda?",
                entity="veda",
            ),
            Beat(
                ("The spoon is in the cup.",),
                _f(("spoon", "in", "cup")),
                "Where is the spoon?",
                entity="spoon",
            ),
            Beat(
                ("Veda is holding the cup.",),
                _f(("cup", "held_by", "veda")),
                "Where is the spoon?",
                entity="spoon",
                fade_miss=True,
            ),
        ),
    ),
    Story(
        "dev.composition.who",
        "composition",
        "dev",
        (
            Beat(
                ("The crate is held by Pock.",),
                _f(("crate", "held_by", "pock")),
                "Who has the crate?",
                entity="crate",
            ),
        ),
    ),
    Story(
        "dev.interference.nim",
        "interference",
        "dev",
        (
            Beat(
                ("Nim is in the loft.",),
                _f(("nim", "in", "loft")),
                "Where is Nim?",
                entity="nim",
            ),
            Beat(
                ("Veda is in the pantry.",),
                _f(("veda", "in", "pantry")),
                "Where is Veda?",
                entity="veda",
            ),
            Beat(
                ("The ribbon was left in the yard.",),
                _f(("ribbon", "in", "yard")),
                "Where is Nim?",
                entity="nim",
                fade_miss=True,
            ),
        ),
    ),
    Story(
        "dev.interference.pock",
        "interference",
        "dev",
        (
            Beat(
                ("Pock stays in the workshop.",),
                _f(("pock", "in", "workshop")),
                "Where is Pock?",
                entity="pock",
            ),
            Beat(
                ("The spoon is in the cup.",),
                _f(("spoon", "in", "cup")),
                "Where is the spoon?",
                entity="spoon",
            ),
            Beat(
                ("Tess is in the garden.",),
                _f(("tess", "in", "garden")),
                "Where is Pock?",
                entity="pock",
                fade_miss=True,
            ),
        ),
    ),
    Story(
        "dev.refresh.lumen",
        "refresh",
        "dev",
        (
            Beat(
                ("Lumen is in the cellar.",),
                _f(("lumen", "in", "cellar")),
                "Where is Lumen?",
                entity="lumen",
            ),
            Beat(
                ("The marble is in the tin.",),
                _f(("marble", "in", "tin")),
                "Where is the marble?",
                entity="marble",
            ),
            Beat(
                ("Bramble is in the porch.",),
                _f(("bramble", "in", "porch")),
                "Where is Lumen?",
                entity="lumen",
                fade_miss=True,
            ),
        ),
    ),
    Story(
        "dev.refresh.tess",
        "refresh",
        "dev",
        (
            Beat(
                ("Tess is in the kitchen.",),
                _f(("tess", "in", "kitchen")),
                "Where is Tess?",
                entity="tess",
            ),
            Beat(
                ("Pock is in the yard.",),
                _f(("pock", "in", "yard")),
                "Where is Pock?",
                entity="pock",
            ),
            Beat(
                ("The basket was left in the shed.",),
                _f(("basket", "in", "shed")),
                "Where is Tess?",
                entity="tess",
                fade_miss=True,
            ),
        ),
    ),
    Story(
        "dev.refresh.short",
        "refresh",
        "dev",
        (
            Beat(
                ("Nim is in the shed.",),
                _f(("nim", "in", "shed")),
                "Where can I find Nim?",
                entity="nim",
            ),
            Beat(
                ("Veda is in the loft.",),
                _f(("veda", "in", "loft")),
                "Where is Nim?",
                entity="nim",
            ),
        ),
    ),
)


def asks(stories: tuple[Story, ...]) -> list[tuple[Story, int]]:
    found: list[tuple[Story, int]] = []
    for story in stories:
        for index, beat in enumerate(story.beats):
            if beat.question:
                found.append((story, index))
    return found
