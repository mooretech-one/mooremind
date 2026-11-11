"""Capturing a relationship, qualifiers, and re-teaching it."""

import pytest

from helpers import fact
from mooremind.store import ThoughtStore
from mooremind.weights import FADE, KEEP, WeightPolicy


def test_one_fact_is_recalled_at_the_initial_weight():
    store = ThoughtStore(KEEP)
    store.teach([fact("nim", "at", "loft", timeframe="t1", confidence="high", origin="note")])
    recall = store.where_now("nim")
    assert recall is not None
    assert recall.phrase == "in the loft"
    thought = recall.thoughts[0]
    assert thought.weight == KEEP.initial
    assert thought.timeframe == "t1"
    assert thought.confidence == "high"
    assert thought.origin == "note"
    assert thought.current is True


def test_reteach_reinforces_the_same_relationship_up_to_the_ceiling():
    store = ThoughtStore(FADE)
    store.teach([fact("nim", "at", "loft")])
    store.teach([fact("nim", "at", "loft")])
    thought = store.where_now("nim").thoughts[0]
    assert thought.weight == min(FADE.ceiling, FADE.initial + FADE.reinforce)
    assert len([item for item in store.thoughts if item.source == "nim"]) == 1


def test_use_reinforces_every_hop_that_was_read():
    store = ThoughtStore(FADE)
    store.teach(
        [
            fact("peg", "in", "tin"),
            fact("tin", "held_by", "brin"),
            fact("brin", "at", "shed"),
        ]
    )
    recall = store.where_now("peg")
    assert [item.relation for item in recall.thoughts] == ["in", "held_by", "at"]
    before = [item.weight for item in recall.thoughts]
    store.reinforce_used(recall.thoughts)
    for thought, weight in zip(recall.thoughts, before, strict=True):
        assert thought.weight == weight + FADE.use_reinforce


def test_structure_wins_over_a_misleading_sentence():
    store = ThoughtStore(KEEP)
    store.teach(
        [
            fact(
                "nim",
                "at",
                "loft",
                text="Nim is in the cellar.",
            )
        ]
    )
    assert store.where_now("nim").phrase == "in the loft"


def test_reset_drops_names_and_thoughts():
    store = ThoughtStore(KEEP)
    store.teach([fact("nim", "at", "loft")])
    store.reset()
    assert store.thoughts == []
    assert store.where_now("nim") is None


def test_a_negative_decay_is_rejected():
    with pytest.raises(ValueError):
        WeightPolicy(decay=-0.1)
