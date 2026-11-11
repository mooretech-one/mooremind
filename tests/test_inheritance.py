"""Class defaults, a nearer class, and an exception that leaves the default in place."""

from helpers import fact
from mooremind.store import ThoughtStore
from mooremind.weights import KEEP


def test_own_colour_overrides_the_class_default_without_erasing_it():
    store = ThoughtStore(KEEP)
    store.teach(
        [
            fact("zindle", "color", "blue", scope="default"),
            fact("mio", "is_a", "zindle"),
            fact("mio", "color", "red"),
            fact("brin", "is_a", "zindle"),
        ]
    )
    assert store.color("mio").phrase == "red"
    assert store.color("brin").phrase == "blue"
    defaults = [
        thought
        for thought in store.thoughts
        if thought.source == "zindle" and thought.relation == "color" and thought.current
    ]
    assert len(defaults) == 1
    assert defaults[0].target == "blue"
    assert defaults[0].scope == "default"


def test_a_child_class_colour_beats_the_parent_and_an_exception_beats_both():
    store = ThoughtStore(KEEP)
    store.teach(
        [
            fact("brelk", "color", "green", scope="default"),
            fact("morp", "is_a", "brelk"),
            fact("morp", "color", "blue"),
            fact("wisp", "is_a", "morp"),
            fact("wisp", "color", "copper"),
            fact("nox", "is_a", "morp"),
            fact("pim", "is_a", "brelk"),
        ]
    )
    assert store.color("nox").phrase == "blue"
    assert store.color("wisp").phrase == "copper"
    assert store.color("pim").phrase == "green"
    parent = next(thought for thought in store.thoughts if thought.source == "brelk")
    assert parent.current is True
    assert parent.target == "green"
