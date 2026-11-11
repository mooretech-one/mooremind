"""The external-learner adapter: letters, fallback, history cues, and no gold."""

from helpers import Choice, Item, fact
from mooremind.learner import FALLBACK, FadeLearner, KeepLearner, MooreMind
from mooremind.weights import FADE, KEEP


def test_constructors_take_no_arguments_so_the_harness_can_load_them():
    assert MooreMind().policy == KEEP
    assert KeepLearner().policy == KEEP
    assert FadeLearner().policy == FADE
    for learner in (KeepLearner(), FadeLearner()):
        assert callable(learner.reset)
        assert callable(learner.teach)
        assert callable(learner.answer)


def test_a_known_chain_is_returned_as_the_matching_choice_letter():
    learner = KeepLearner()
    learner.teach(
        [
            fact("button", "in", "cup"),
            fact("cup", "in", "crate"),
            fact("crate", "at", "garage"),
        ]
    )
    item = Item(
        "Where is the button?",
        [
            Choice("A", "in the shed"),
            Choice("B", "in the cup, in the crate, in the garage"),
            Choice("C", "held by veda"),
        ],
    )
    assert learner.answer(item) == "B"
    assert learner.stats() == {"from_store": 1, "fell_back": 0}


def test_colour_inheritance_and_history_cues_do_not_read_gold_fields():
    learner = KeepLearner()
    learner.teach(
        [
            fact("zindle", "color", "blue", scope="default"),
            fact("mio", "is_a", "zindle"),
            fact("mio", "color", "red"),
            fact("brin", "is_a", "zindle"),
        ]
    )
    colour = Item(
        "What colour is Mio?",
        [Choice("A", "blue"), Choice("B", "red"), Choice("C", "green")],
    )
    assert learner.answer(colour) == "B"

    learner.reset()
    learner.teach(
        [
            fact("nim", "at", "porch", timeframe="t1"),
            fact("nim", "at", "pantry", timeframe="t2"),
            fact("nim", "at", "yard", timeframe="t3"),
        ]
    )
    assert (
        learner.answer(
            Item(
                "Where is Nim now?",
                [Choice("A", "in the porch"), Choice("B", "in the yard")],
            )
        )
        == "B"
    )
    assert (
        learner.answer(
            Item(
                "Where was Nim earlier?",
                [Choice("A", "in the yard"), Choice("B", "in the pantry")],
            )
        )
        == "B"
    )
    assert (
        learner.answer(
            Item(
                "Where did Nim start?",
                [Choice("A", "in the yard"), Choice("B", "in the porch")],
            )
        )
        == "B"
    )
    assert (
        learner.answer(
            Item(
                "Where was Nim at the second stop?",
                [Choice("A", "in the porch"), Choice("B", "in the pantry")],
            )
        )
        == "B"
    )
    assert (
        learner.answer(
            Item(
                "Which place was the middle stop for Nim?",
                [Choice("A", "in the pantry"), Choice("B", "in the yard")],
            )
        )
        == "A"
    )
    assert (
        learner.answer(
            Item(
                "Which place did Nim leave last?",
                [Choice("A", "in the porch"), Choice("B", "in the pantry")],
            )
        )
        == "B"
    )
    assert (
        learner.answer(
            Item(
                "Where was Nim just before the end?",
                [Choice("A", "in the porch"), Choice("B", "in the pantry")],
            )
        )
        == "B"
    )
    assert (
        learner.answer(
            Item(
                "Which place is Nim in at the end?",
                [Choice("A", "in the pantry"), Choice("B", "in the yard")],
            )
        )
        == "B"
    )
    assert learner.fell_back == 0


def test_fallback_does_not_pick_a_choice_when_the_store_has_no_answer():
    learner = KeepLearner()
    learner.teach([fact("nim", "at", "loft")])
    item = Item(
        "Where is Veda?",
        [
            Choice("A", "in the loft"),
            Choice("B", FALLBACK),
            Choice("C", "in the yard"),
        ],
    )
    assert learner.answer(item) == FALLBACK
    assert learner.fell_back == 1
    assert learner.from_store == 0


def test_reset_drops_facts_and_keeps_the_run_counts():
    learner = KeepLearner()
    learner.teach([fact("nim", "at", "loft")])
    assert learner.answer(Item("Where is Nim?", [Choice("A", "in the loft")])) == "A"
    learner.reset()
    assert learner.answer(Item("Where is Nim?", [Choice("A", "in the loft")])) == FALLBACK
    assert learner.stats() == {"from_store": 1, "fell_back": 1}


def test_fade_forgets_a_fact_that_keep_still_answers():
    taught = [fact("nim", "at", "loft")]
    question = Item("Where is Nim?", [Choice("A", "in the loft"), Choice("B", "in the yard")])
    keep = KeepLearner()
    fade = FadeLearner()
    for learner in (keep, fade):
        learner.teach(taught)
        assert learner.answer(question) == "A"
        learner.teach([fact("kit", "at", "yard")])
        learner.teach([fact("kit", "at", "porch")])
    assert keep.answer(question) == "A"
    assert keep.from_store == 2
    assert fade.answer(question) == FALLBACK
    assert fade.fell_back == 1
    assert fade.from_store == 1


def test_a_wrong_subtype_label_does_not_change_the_answer():
    learner = KeepLearner()
    learner.teach([fact("nim", "at", "loft")])

    class Tagged(Item):
        @property
        def learn_subtype(self) -> str:
            return "refresh"

    item = Tagged("Where is Nim?", [Choice("C", "in the loft"), Choice("A", "in the yard")])
    assert learner.answer(item) == "C"
