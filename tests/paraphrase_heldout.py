"""PR2 paraphrase batch.

This was the held-out set for that pull request. It is development data now:
the front end may be tuned against it. The one-shot batch is
``paraphrase_fresh.py``.
"""

from __future__ import annotations

from paraphrase_data import Beat, Story, _f

HOLDOUT: tuple[Story, ...] = (
    Story(
        "hold.one_shot.inside",
        "one_shot",
        "heldout",
        (
            Beat(
                ("The marble is inside the pot.",),
                _f(("marble", "in", "pot")),
                "Where is the marble?",
                entity="marble",
            ),
        ),
    ),
    Story(
        "hold.one_shot.carries",
        "one_shot",
        "heldout",
        (
            Beat(
                ("Bramble carries the button.",),
                _f(("button", "held_by", "bramble")),
                "Who has the button?",
                entity="button",
            ),
        ),
    ),
    Story(
        "hold.one_shot.inverted",
        "one_shot",
        "heldout",
        (
            Beat(
                ("In the workshop sits Lumen.",),
                _f(("lumen", "in", "workshop")),
                "Where is Lumen?",
                entity="lumen",
            ),
        ),
    ),
    Story(
        "hold.one_shot.keeps",
        "one_shot",
        "heldout",
        (
            Beat(
                ("The shed is where Tess keeps the bell.",),
                _f(("bell", "in", "shed")),
                "Where is the bell?",
                entity="bell",
            ),
        ),
    ),
    Story(
        "hold.one_shot.room",
        "one_shot",
        "heldout",
        (
            Beat(
                ("Pock is in the cellar.",),
                _f(("pock", "in", "cellar")),
                "In which room do we find Pock?",
                entity="pock",
            ),
        ),
    ),
    Story(
        "hold.one_shot.point",
        "one_shot",
        "heldout",
        (
            Beat(
                ("The ribbon is in the sack.",),
                _f(("ribbon", "in", "sack")),
                "Point to the ribbon.",
                entity="ribbon",
            ),
        ),
    ),
    Story(
        "hold.update.inside",
        "update",
        "heldout",
        (
            Beat(
                ("At first Nim is inside the porch.", "Then Nim moves to the yard."),
                _f(("nim", "in", "porch"), ("nim", "in", "yard")),
                "Where is Nim now?",
                entity="nim",
            ),
        ),
    ),
    Story(
        "hold.update.earlier",
        "update",
        "heldout",
        (
            Beat(
                ("Lumen begins in the cellar.", "After that Lumen is in the kitchen."),
                _f(("lumen", "in", "cellar"), ("lumen", "in", "kitchen")),
                "Where was Lumen earlier?",
                kind="before",
                entity="lumen",
            ),
        ),
    ),
    Story(
        "hold.update.fromto",
        "update",
        "heldout",
        (
            Beat(
                ("Nim went from the porch to the yard.",),
                _f(("nim", "in", "porch"), ("nim", "in", "yard")),
                "Where is Nim now?",
                entity="nim",
            ),
        ),
    ),
    Story(
        "hold.update.firstline",
        "update",
        "heldout",
        (
            Beat(
                ("First the kitchen, afterwards the hall, for Tess.",),
                _f(("tess", "in", "kitchen"), ("tess", "in", "hallway")),
                "Where did Tess start?",
                kind="index",
                entity="tess",
                index=0,
            ),
        ),
    ),
    Story(
        "hold.update.question",
        "update",
        "heldout",
        (
            Beat(
                ("At first Pock is in the shed.", "Then Pock moves to the loft."),
                _f(("pock", "in", "shed"), ("pock", "in", "loft")),
                "Before the end, where had Pock been?",
                kind="before",
                entity="pock",
            ),
        ),
    ),
    Story(
        "hold.update.once",
        "update",
        "heldout",
        (
            Beat(
                ("Once in the shed, later the garden: that is Veda.",),
                _f(("veda", "in", "shed"), ("veda", "in", "garden")),
                "Where is Veda?",
                entity="veda",
            ),
        ),
    ),
    Story(
        "hold.inheritance.default",
        "inheritance",
        "heldout",
        (
            Beat(
                ("A brindle is olive.", "Tess is a brindle."),
                _f(("brindle", "color", "olive"), ("tess", "is_a", "brindle")),
                "What colour is Tess?",
                kind="color",
                entity="tess",
            ),
        ),
    ),
    Story(
        "hold.inheritance.exception",
        "inheritance",
        "heldout",
        (
            Beat(
                ("The mottle kind is navy.", "Pock counts as a mottle.", "Pock alone is rust."),
                _f(
                    ("mottle", "color", "navy"),
                    ("pock", "is_a", "mottle"),
                    ("pock", "color", "rust"),
                ),
                "Which colour does Pock have?",
                kind="color",
                entity="pock",
            ),
        ),
    ),
    Story(
        "hold.inheritance.describes",
        "inheritance",
        "heldout",
        (
            Beat(
                ("Olive describes a brindle, and Tess is one.",),
                _f(("brindle", "color", "olive"), ("tess", "is_a", "brindle")),
                "What colour is Tess?",
                kind="color",
                entity="tess",
            ),
        ),
    ),
    Story(
        "hold.inheritance.possessive",
        "inheritance",
        "heldout",
        (
            Beat(
                ("Nim's colour is rust, unlike other mottles.",),
                _f(("nim", "color", "rust")),
                "What colour is Nim?",
                kind="color",
                entity="nim",
            ),
        ),
    ),
    Story(
        "hold.inheritance.question",
        "inheritance",
        "heldout",
        (
            Beat(
                ("A snip is pearl.", "Lumen is a snip."),
                _f(("snip", "color", "pearl"), ("lumen", "is_a", "snip")),
                "Name the colour Lumen wears.",
                kind="color",
                entity="lumen",
            ),
        ),
    ),
    Story(
        "hold.inheritance.every",
        "inheritance",
        "heldout",
        (
            Beat(
                ("Every mottle is navy except Bramble, who is pearl.",),
                _f(
                    ("mottle", "color", "navy"),
                    ("bramble", "is_a", "mottle"),
                    ("bramble", "color", "pearl"),
                ),
                "What colour is Bramble?",
                kind="color",
                entity="bramble",
            ),
        ),
    ),
    Story(
        "hold.composition.chain",
        "composition",
        "heldout",
        (
            Beat(
                ("Lumen is in the hallway.",),
                _f(("lumen", "in", "hallway")),
                "Where is Lumen?",
                entity="lumen",
            ),
            Beat(
                ("The bell is inside the sack.", "Lumen carries the sack."),
                _f(("bell", "in", "sack"), ("sack", "held_by", "lumen")),
                "Where is the bell?",
                entity="bell",
            ),
        ),
    ),
    Story(
        "hold.composition.inverted",
        "composition",
        "heldout",
        (
            Beat(
                ("In the garden sits the pot.",),
                _f(("pot", "in", "garden")),
                "Where is the pot?",
                entity="pot",
            ),
        ),
    ),
    Story(
        "hold.composition.holding",
        "composition",
        "heldout",
        (
            Beat(
                ("The pot contains the marble.", "Holding that pot is Tess."),
                _f(("marble", "in", "pot"), ("pot", "held_by", "tess")),
                "Where is the marble?",
                entity="marble",
            ),
        ),
    ),
    Story(
        "hold.composition.question",
        "composition",
        "heldout",
        (
            Beat(
                (
                    "Nim is in the loft.",
                    "The pebble is in the basket.",
                    "The basket is held by Nim.",
                ),
                _f(
                    ("nim", "in", "loft"),
                    ("pebble", "in", "basket"),
                    ("basket", "held_by", "nim"),
                ),
                "Show me where the pebble ended up.",
                entity="pebble",
            ),
        ),
    ),
    Story(
        "hold.composition.possessive",
        "composition",
        "heldout",
        (
            Beat(
                ("Nim's basket has the pebble.",),
                _f(("pebble", "in", "basket")),
                "Where is the pebble?",
                entity="pebble",
            ),
        ),
    ),
    Story(
        "hold.interference.gap",
        "interference",
        "heldout",
        (
            Beat(
                ("Tess is inside the workshop.",),
                _f(("tess", "in", "workshop")),
                "Where is Tess?",
                entity="tess",
            ),
            Beat(
                ("The spoon is in the cup.",),
                _f(("spoon", "in", "cup")),
                "Where is the spoon?",
                entity="spoon",
            ),
            Beat(
                ("Bramble is in the yard.",),
                _f(("bramble", "in", "yard")),
                "Where is Tess?",
                entity="tess",
                fade_miss=True,
            ),
        ),
    ),
    Story(
        "hold.interference.inverted",
        "interference",
        "heldout",
        (
            Beat(
                ("In the cellar sits Pock.",),
                _f(("pock", "in", "cellar")),
                "Where is Pock?",
                entity="pock",
            ),
        ),
    ),
    Story(
        "hold.interference.point",
        "interference",
        "heldout",
        (
            Beat(
                ("Veda is in the porch.",),
                _f(("veda", "in", "porch")),
                "Point to Veda.",
                entity="veda",
            ),
        ),
    ),
    Story(
        "hold.interference.fromto",
        "interference",
        "heldout",
        (
            Beat(
                ("From the loft Nim shifted to the shed.",),
                _f(("nim", "in", "shed")),
                "Where is Nim?",
                entity="nim",
            ),
        ),
    ),
    Story(
        "hold.refresh.gap",
        "refresh",
        "heldout",
        (
            Beat(
                ("Lumen stays in the cellar.",),
                _f(("lumen", "in", "cellar")),
                "Where can I find Lumen?",
                entity="lumen",
            ),
            Beat(
                ("The marble is inside the tin.",),
                _f(("marble", "in", "tin")),
                "Where is the marble?",
                entity="marble",
            ),
            Beat(
                ("The ribbon was left in the yard.",),
                _f(("ribbon", "in", "yard")),
                "Where is Lumen?",
                entity="lumen",
                fade_miss=True,
            ),
        ),
    ),
    Story(
        "hold.refresh.inverted",
        "refresh",
        "heldout",
        (
            Beat(
                ("In the pantry sits the bell.",),
                _f(("bell", "in", "pantry")),
                "Where is the bell?",
                entity="bell",
            ),
        ),
    ),
    Story(
        "hold.refresh.question",
        "refresh",
        "heldout",
        (
            Beat(
                ("Pock is in the workshop.",),
                _f(("pock", "in", "workshop")),
                "Which corner holds Pock?",
                entity="pock",
            ),
        ),
    ),
    Story(
        "hold.refresh.pronoun",
        "refresh",
        "heldout",
        (
            Beat(
                ("It is the crate that holds the tile.",),
                _f(("tile", "in", "crate")),
                "Where is the tile?",
                entity="tile",
            ),
        ),
    ),
)
