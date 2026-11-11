"""A move keeps the earlier place, keyed by order and by timeframe."""

from helpers import fact
from mooremind.store import ThoughtStore
from mooremind.weights import KEEP


def _moved() -> ThoughtStore:
    store = ThoughtStore(KEEP)
    store.teach(
        [
            fact("nim", "at", "porch", timeframe="t1"),
            fact("nim", "at", "pantry", timeframe="t2"),
            fact("nim", "at", "yard", timeframe="t3"),
        ]
    )
    return store


def test_where_now_is_the_latest_place_and_the_earlier_places_remain():
    store = _moved()
    assert store.where_now("nim").phrase == "in the yard"
    assert store.where_before("nim").phrase == "in the pantry"
    kept = [thought.target for thought in store.thoughts if thought.source == "nim"]
    assert kept == ["porch", "pantry", "yard"]
    assert [thought.current for thought in store.thoughts if thought.source == "nim"] == [
        False,
        False,
        True,
    ]


def test_a_timeframe_and_a_timeline_index_both_find_the_old_place():
    store = _moved()
    assert store.where_at("nim", "t1").phrase == "in the porch"
    assert store.where_index("nim", 0).phrase == "in the porch"
    assert store.where_index("nim", 1).phrase == "in the pantry"
    assert store.where_middle("nim").phrase == "in the pantry"
    assert store.where_at("nim", "t9") is None


def test_a_later_episode_still_keeps_the_history():
    store = ThoughtStore(KEEP)
    store.teach([fact("nim", "at", "porch", timeframe="t1")])
    store.teach([fact("nim", "at", "yard", timeframe="t2")])
    assert store.where_now("nim").phrase == "in the yard"
    assert store.where_before("nim").phrase == "in the porch"
