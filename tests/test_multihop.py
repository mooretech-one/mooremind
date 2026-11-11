"""Where-now walks in, on, and held-by. An at link stops the walk."""

from helpers import fact
from mooremind.store import ThoughtStore
from mooremind.weights import KEEP


def test_three_containers_compose_one_location():
    store = ThoughtStore(KEEP)
    store.teach(
        [
            fact("button", "in", "cup"),
            fact("cup", "in", "crate"),
            fact("crate", "at", "garage"),
        ]
    )
    assert store.where_now("button").phrase == "in the cup, in the crate, in the garage"


def test_held_by_then_a_room():
    store = ThoughtStore(KEEP)
    store.teach(
        [
            fact("spoon", "held_by", "veda"),
            fact("veda", "at", "kitchen"),
        ]
    )
    assert store.where_now("spoon").phrase == "held by veda, in the kitchen"


def test_on_is_a_direct_phrase_and_at_does_not_walk_further():
    store = ThoughtStore(KEEP)
    store.teach([fact("cup", "on", "tray")])
    assert store.where_now("cup").phrase == "on the tray"

    store.reset()
    store.teach(
        [
            fact("spoon", "in", "cup"),
            fact("cup", "at", "shed"),
            fact("shed", "at", "garden"),
        ]
    )
    assert store.where_now("spoon").phrase == "in the cup, in the shed"


def test_a_location_cycle_has_no_answer():
    store = ThoughtStore(KEEP)
    store.teach([fact("basket", "in", "crate"), fact("crate", "in", "basket")])
    assert store.where_now("basket") is None


def test_the_longer_name_is_the_focus_when_both_names_occur():
    store = ThoughtStore(KEEP)
    store.teach(
        [
            fact("red_box", "at", "loft"),
            fact("box", "at", "yard"),
        ]
    )
    assert store.focus("Where is the red box?") == "red_box"
    assert store.where_now("red_box").phrase == "in the loft"
    assert store.where_now("box").phrase == "in the yard"
