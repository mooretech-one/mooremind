"""One-shot held-out batch for the widened front end.

Written before that widening. Wording, order, and questions differ from the
MooreSense templates and from both PR2 paraphrase files. After this pull
request the batch is development data; the score below is the single
measurement and is not a target to chase.
"""

from __future__ import annotations

from paraphrase_data import Beat, Story, _f

FRESH: tuple[Story, ...] = (
    # --- one_shot: 10 ---
    Story(
        "fresh.one_shot.residence",
        "one_shot",
        "fresh",
        (
            Beat(
                ("Willa has taken up residence in the attic.",),
                _f(("willa", "in", "attic")),
                "Willa's whereabouts at this moment?",
                entity="willa",
            ),
        ),
    ),
    Story(
        "fresh.one_shot.tucked",
        "one_shot",
        "fresh",
        (
            Beat(
                ("You will find the ladle tucked within the jar.",),
                _f(("ladle", "in", "jar")),
                "Got a spot for the ladle?",
                entity="ladle",
            ),
        ),
    ),
    Story(
        "fresh.one_shot.hands",
        "one_shot",
        "fresh",
        (
            Beat(
                ("Corin's hands are on the thimble.",),
                _f(("thimble", "held_by", "corin")),
                "The thimble sits with whom?",
                entity="thimble",
            ),
        ),
    ),
    Story(
        "fresh.one_shot.container",
        "one_shot",
        "fresh",
        (
            Beat(
                ("The bead's container is the caddy.",),
                _f(("bead", "in", "caddy")),
                "Find the bead's container.",
                entity="bead",
            ),
        ),
    ),
    Story(
        "fresh.one_shot.keeps",
        "one_shot",
        "fresh",
        (
            Beat(
                ("Moss keeps to the scullery.",),
                _f(("moss", "in", "scullery")),
                "Moss, location now.",
                entity="moss",
            ),
        ),
    ),
    Story(
        "fresh.one_shot.withher",
        "one_shot",
        "fresh",
        (
            Beat(
                ("Hettie has the spool with her.",),
                _f(("spool", "held_by", "hettie")),
                "Whose charge is the spool?",
                entity="spool",
            ),
        ),
    ),
    Story(
        "fresh.one_shot.care",
        "one_shot",
        "fresh",
        (
            Beat(
                ("The walnut rests under the hamper's care.",),
                _f(("walnut", "in", "hamper")),
                "The walnut, what houses it?",
                entity="walnut",
            ),
        ),
    ),
    Story(
        "fresh.one_shot.checking",
        "one_shot",
        "fresh",
        (
            Beat(
                ("Sable can be located by checking the greenhouse.",),
                _f(("sable", "in", "greenhouse")),
                "Sable's place in the building?",
                entity="sable",
            ),
        ),
    ),
    Story(
        "fresh.one_shot.belongs",
        "one_shot",
        "fresh",
        (
            Beat(
                ("The cork belongs with the pail.",),
                _f(("cork", "in", "pail")),
                "Cork: housed in what, roughly?",
                entity="cork",
            ),
        ),
    ),
    Story(
        "fresh.one_shot.hosts",
        "one_shot",
        "fresh",
        (
            Beat(
                ("The nook currently hosts Willa.",),
                _f(("willa", "in", "nook")),
                "Anyone keeping track of Willa?",
                entity="willa",
            ),
        ),
    ),
    # --- update: 10 ---
    Story(
        "fresh.update.afternoon",
        "update",
        "fresh",
        (
            Beat(
                ("Willa began the afternoon resident in the attic and closed it in the yard.",),
                _f(("willa", "in", "attic"), ("willa", "in", "yard")),
                "Willa's whereabouts at this moment?",
                entity="willa",
            ),
        ),
    ),
    Story(
        "fresh.update.settled",
        "update",
        "fresh",
        (
            Beat(
                ("Corin left the porch behind and is settled in the pantry.",),
                _f(("corin", "in", "porch"), ("corin", "in", "pantry")),
                "Earlier spot for Corin?",
                kind="before",
                entity="corin",
            ),
        ),
    ),
    Story(
        "fresh.update.wander",
        "update",
        "fresh",
        (
            Beat(
                ("Moss's wander ran scullery, then hallway, then garden.",),
                _f(("moss", "in", "scullery"), ("moss", "in", "hallway"), ("moss", "in", "garden")),
                "Middle of Moss's wander?",
                kind="middle",
                entity="moss",
            ),
        ),
    ),
    Story(
        "fresh.update.list",
        "update",
        "fresh",
        (
            Beat(
                ("Hettie's list reads attic, scullery, nook, yard.",),
                _f(
                    ("hettie", "in", "attic"),
                    ("hettie", "in", "scullery"),
                    ("hettie", "in", "nook"),
                    ("hettie", "in", "yard"),
                ),
                "Second pause on Hettie's list?",
                kind="index",
                entity="hettie",
                index=1,
            ),
        ),
    ),
    Story(
        "fresh.update.opening",
        "update",
        "fresh",
        (
            Beat(
                ("Sable's opening spot was the greenhouse, and the yard came after.",),
                _f(("sable", "in", "greenhouse"), ("sable", "in", "yard")),
                "Sable's opening spot?",
                kind="index",
                entity="sable",
                index=0,
            ),
        ),
    ),
    Story(
        "fresh.update.through",
        "update",
        "fresh",
        (
            Beat(
                ("Having been in the cellar, Lumen is through to the kitchen.",),
                _f(("lumen", "in", "cellar"), ("lumen", "in", "kitchen")),
                "The place Lumen left behind?",
                kind="before",
                entity="lumen",
            ),
        ),
    ),
    Story(
        "fresh.update.diary",
        "update",
        "fresh",
        (
            Beat(
                ("Diary for Bramble: shed, then hallway, then porch, then attic.",),
                _f(
                    ("bramble", "in", "shed"),
                    ("bramble", "in", "hallway"),
                    ("bramble", "in", "porch"),
                    ("bramble", "in", "attic"),
                ),
                "Bramble's final spot?",
                entity="bramble",
            ),
        ),
    ),
    Story(
        "fresh.update.path",
        "update",
        "fresh",
        (
            Beat(
                ("Tess's path runs porch, then loft, and she is done.",),
                _f(("tess", "in", "porch"), ("tess", "in", "loft")),
                "Tess's finishing spot?",
                entity="tess",
            ),
        ),
    ),
    Story(
        "fresh.update.beginning",
        "update",
        "fresh",
        (
            Beat(
                ("The garden was Nim's beginning; the workshop is the end.",),
                _f(("nim", "in", "garden"), ("nim", "in", "workshop")),
                "Nim's starting point?",
                kind="index",
                entity="nim",
                index=0,
            ),
        ),
    ),
    Story(
        "fresh.update.previous",
        "update",
        "fresh",
        (
            Beat(
                ("Veda quit the scullery for the nook.",),
                _f(("veda", "in", "scullery"), ("veda", "in", "nook")),
                "Veda's previous room?",
                kind="before",
                entity="veda",
            ),
        ),
    ),
    # --- inheritance: 10 ---
    Story(
        "fresh.inheritance.spoken",
        "inheritance",
        "fresh",
        (
            Beat(
                ("Dapples are spoken of as ivory.", "Willa is of that sort."),
                _f(("dapple", "color", "ivory"), ("willa", "is_a", "dapple")),
                "Tell me Willa's shade.",
                kind="color",
                entity="willa",
            ),
        ),
    ),
    Story(
        "fresh.inheritance.alone",
        "inheritance",
        "fresh",
        (
            Beat(
                ("Most dapples are ivory.", "Willa alone comes across as teal."),
                _f(("dapple", "color", "ivory"), ("willa", "color", "teal")),
                "Tell me Willa's shade.",
                kind="color",
                entity="willa",
            ),
        ),
    ),
    Story(
        "fresh.inheritance.line",
        "inheritance",
        "fresh",
        (
            Beat(
                ("The tawny line is copper.", "Corin counts in that line."),
                _f(("tawny", "color", "copper"), ("corin", "is_a", "tawny")),
                "Shade attached to Corin?",
                kind="color",
                entity="corin",
            ),
        ),
    ),
    Story(
        "fresh.inheritance.stock",
        "inheritance",
        "fresh",
        (
            Beat(
                ("Dapples show navy.", "A pippin is a dapple.", "Moss is pippin-stock."),
                _f(
                    ("dapple", "color", "navy"),
                    ("pippin", "is_a", "dapple"),
                    ("moss", "is_a", "pippin"),
                ),
                "Shade attached to Moss?",
                kind="color",
                entity="moss",
            ),
        ),
    ),
    Story(
        "fresh.inheritance.family",
        "inheritance",
        "fresh",
        (
            Beat(
                ("Ivory is the family look for tawnies, except Hettie, who shows lilac.",),
                _f(
                    ("tawny", "color", "ivory"),
                    ("hettie", "is_a", "tawny"),
                    ("hettie", "color", "lilac"),
                ),
                "Shade attached to Hettie?",
                kind="color",
                entity="hettie",
            ),
        ),
    ),
    Story(
        "fresh.inheritance.unlike",
        "inheritance",
        "fresh",
        (
            Beat(
                ("Sable, unlike other pippins, shows lilac.", "Pippins otherwise show navy."),
                _f(
                    ("sable", "color", "lilac"),
                    ("sable", "is_a", "pippin"),
                    ("pippin", "color", "navy"),
                ),
                "Shade attached to Sable?",
                kind="color",
                entity="sable",
            ),
        ),
    ),
    Story(
        "fresh.inheritance.default",
        "inheritance",
        "fresh",
        (
            Beat(
                ("People call a dapple teal when they mean the usual look.", "Lumen is a dapple."),
                _f(("dapple", "color", "teal"), ("lumen", "is_a", "dapple")),
                "Shade attached to Lumen?",
                kind="color",
                entity="lumen",
            ),
        ),
    ),
    Story(
        "fresh.inheritance.group",
        "inheritance",
        "fresh",
        (
            Beat(
                ("Lumen belongs to the tawny group, whose usual shade is pearl.",),
                _f(("lumen", "is_a", "tawny"), ("tawny", "color", "pearl")),
                "Shade attached to Lumen?",
                kind="color",
                entity="lumen",
            ),
        ),
    ),
    Story(
        "fresh.inheritance.exception",
        "inheritance",
        "fresh",
        (
            Beat(
                ("Bramble is the teal exception among dapples that otherwise look ivory.",),
                _f(
                    ("bramble", "color", "teal"),
                    ("bramble", "is_a", "dapple"),
                    ("dapple", "color", "ivory"),
                ),
                "Shade attached to Bramble?",
                kind="color",
                entity="bramble",
            ),
        ),
    ),
    Story(
        "fresh.inheritance.expect",
        "inheritance",
        "fresh",
        (
            Beat(
                ("If it is a pippin, expect navy, and Tess is one of them.",),
                _f(("pippin", "color", "navy"), ("tess", "is_a", "pippin")),
                "Shade attached to Tess?",
                kind="color",
                entity="tess",
            ),
        ),
    ),
    # --- composition: 10 asks ---
    Story(
        "fresh.composition.bead",
        "composition",
        "fresh",
        (
            Beat(
                ("Willa has taken up residence in the attic.",),
                _f(("willa", "in", "attic")),
                "Willa's whereabouts at this moment?",
                entity="willa",
            ),
            Beat(
                ("The bead's container is the caddy.", "Corin's hands are on the caddy."),
                _f(("bead", "in", "caddy"), ("caddy", "held_by", "corin")),
                "Find the bead's container.",
                entity="bead",
            ),
        ),
    ),
    Story(
        "fresh.composition.ladle",
        "composition",
        "fresh",
        (
            Beat(
                ("The ladle is tucked within the jar.",),
                _f(("ladle", "in", "jar")),
                "Got a spot for the ladle?",
                entity="ladle",
            ),
            Beat(
                ("Hettie has the jar with her.", "Hettie keeps to the scullery."),
                _f(("jar", "held_by", "hettie"), ("hettie", "in", "scullery")),
                "Got a spot for the ladle?",
                entity="ladle",
            ),
        ),
    ),
    Story(
        "fresh.composition.hosts",
        "composition",
        "fresh",
        (
            Beat(
                ("The nook currently hosts the pail.",),
                _f(("pail", "in", "nook")),
                "Anyone keeping track of the pail?",
                entity="pail",
            ),
        ),
    ),
    Story(
        "fresh.composition.walnut",
        "composition",
        "fresh",
        (
            Beat(
                ("The walnut rests under the hamper's care, and Moss's hands are on that hamper.",),
                _f(("walnut", "in", "hamper"), ("hamper", "held_by", "moss")),
                "The walnut, what houses it?",
                entity="walnut",
            ),
        ),
    ),
    Story(
        "fresh.composition.cork",
        "composition",
        "fresh",
        (
            Beat(
                ("Sable can be located by checking the greenhouse.", "The cork belongs with the pail."),
                _f(("sable", "in", "greenhouse"), ("cork", "in", "pail")),
                "Cork: housed in what, roughly?",
                entity="cork",
            ),
        ),
    ),
    Story(
        "fresh.composition.spool",
        "composition",
        "fresh",
        (
            Beat(
                ("The spool travelled with Tess, who keeps to the porch.",),
                _f(("spool", "held_by", "tess"), ("tess", "in", "porch")),
                "Whose charge is the spool?",
                entity="spool",
            ),
        ),
    ),
    Story(
        "fresh.composition.thimble",
        "composition",
        "fresh",
        (
            Beat(
                ("Check the jar if you need the thimble; the jar stays by Corin in the pantry.",),
                _f(("thimble", "in", "jar"), ("jar", "held_by", "corin"), ("corin", "in", "pantry")),
                "The thimble sits with whom?",
                entity="thimble",
            ),
        ),
    ),
    Story(
        "fresh.composition.bead_only",
        "composition",
        "fresh",
        (
            Beat(
                ("Nothing but the caddy is relevant to the bead.",),
                _f(("bead", "in", "caddy")),
                "Find the bead's container.",
                entity="bead",
            ),
        ),
    ),
    # --- interference: 10 asks ---
    Story(
        "fresh.interference.gap",
        "interference",
        "fresh",
        (
            Beat(
                ("Tess has taken up residence in the workshop.",),
                _f(("tess", "in", "workshop")),
                "Anyone keeping track of Tess?",
                entity="tess",
            ),
            Beat(
                ("The ladle is tucked within the jar.",),
                _f(("ladle", "in", "jar")),
                "Got a spot for the ladle?",
                entity="ladle",
            ),
            Beat(
                ("Bramble keeps to the yard.",),
                _f(("bramble", "in", "yard")),
                "Anyone keeping track of Tess?",
                entity="tess",
                fade_miss=True,
            ),
        ),
    ),
    Story(
        "fresh.interference.moss",
        "interference",
        "fresh",
        (
            Beat(
                ("Moss keeps to the scullery.",),
                _f(("moss", "in", "scullery")),
                "Moss, location now.",
                entity="moss",
            ),
            Beat(
                ("Hettie has the spool with her.",),
                _f(("spool", "held_by", "hettie")),
                "Whose charge is the spool?",
                entity="spool",
            ),
            Beat(
                ("The nook currently hosts Sable.",),
                _f(("sable", "in", "nook")),
                "Moss, location now.",
                entity="moss",
                fade_miss=True,
            ),
        ),
    ),
    Story(
        "fresh.interference.willa",
        "interference",
        "fresh",
        (
            Beat(
                ("The attic currently hosts Willa.",),
                _f(("willa", "in", "attic")),
                "Anyone keeping track of Willa?",
                entity="willa",
            ),
        ),
    ),
    Story(
        "fresh.interference.corin",
        "interference",
        "fresh",
        (
            Beat(
                ("Corin's hands are on the thimble, though the thimble's tale is a distraction.",),
                _f(("thimble", "held_by", "corin")),
                "The thimble sits with whom?",
                entity="thimble",
            ),
        ),
    ),
    Story(
        "fresh.interference.bead",
        "interference",
        "fresh",
        (
            Beat(
                ("Ignore the yard talk; the bead's container is the caddy.",),
                _f(("bead", "in", "caddy")),
                "Find the bead's container.",
                entity="bead",
            ),
        ),
    ),
    Story(
        "fresh.interference.lumen",
        "interference",
        "fresh",
        (
            Beat(
                ("Lumen is spoken of only as a resident of the cellar.",),
                _f(("lumen", "in", "cellar")),
                "Anyone keeping track of Lumen?",
                entity="lumen",
            ),
        ),
    ),
    # --- refresh: 10 asks ---
    Story(
        "fresh.refresh.gap",
        "refresh",
        "fresh",
        (
            Beat(
                ("Lumen keeps to the cellar.",),
                _f(("lumen", "in", "cellar")),
                "Anyone keeping track of Lumen?",
                entity="lumen",
            ),
            Beat(
                ("The cork belongs with the pail.",),
                _f(("cork", "in", "pail")),
                "Cork: housed in what, roughly?",
                entity="cork",
            ),
            Beat(
                ("The walnut rests under the hamper's care.",),
                _f(("walnut", "in", "hamper")),
                "Anyone keeping track of Lumen?",
                entity="lumen",
                fade_miss=True,
            ),
        ),
    ),
    Story(
        "fresh.refresh.willa",
        "refresh",
        "fresh",
        (
            Beat(
                ("Willa has taken up residence in the attic.",),
                _f(("willa", "in", "attic")),
                "Willa's whereabouts at this moment?",
                entity="willa",
            ),
            Beat(
                ("Sable can be located by checking the greenhouse.",),
                _f(("sable", "in", "greenhouse")),
                "Sable's place in the building?",
                entity="sable",
            ),
            Beat(
                ("Corin's hands are on the thimble.",),
                _f(("thimble", "held_by", "corin")),
                "Willa's whereabouts at this moment?",
                entity="willa",
                fade_miss=True,
            ),
        ),
    ),
    Story(
        "fresh.refresh.moss",
        "refresh",
        "fresh",
        (
            Beat(
                ("Moss keeps to the scullery even after the chatter moves on.",),
                _f(("moss", "in", "scullery")),
                "Moss, location now.",
                entity="moss",
            ),
        ),
    ),
    Story(
        "fresh.refresh.hettie",
        "refresh",
        "fresh",
        (
            Beat(
                ("Hettie has the spool with her still, nobody restated it.",),
                _f(("spool", "held_by", "hettie")),
                "Whose charge is the spool?",
                entity="spool",
            ),
        ),
    ),
    Story(
        "fresh.refresh.jar",
        "refresh",
        "fresh",
        (
            Beat(
                ("You will find the ladle tucked within the jar, same as before.",),
                _f(("ladle", "in", "jar")),
                "Got a spot for the ladle?",
                entity="ladle",
            ),
        ),
    ),
    Story(
        "fresh.refresh.nook",
        "refresh",
        "fresh",
        (
            Beat(
                ("The nook currently hosts the pail and that was not repeated.",),
                _f(("pail", "in", "nook")),
                "Anyone keeping track of the pail?",
                entity="pail",
            ),
        ),
    ),
)
