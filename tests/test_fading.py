"""keep never decays. fade drops a once-used fact on the second later episode."""

from helpers import fact
from mooremind.store import ThoughtStore
from mooremind.weights import FADE, KEEP


def _quiet(store: ThoughtStore, *places: str) -> None:
    for place in places:
        store.teach([fact("kit", "at", place)])


def test_keep_still_recalls_after_later_episodes():
    store = ThoughtStore(KEEP)
    store.teach([fact("nim", "at", "loft")])
    store.reinforce_used(store.where_now("nim").thoughts)
    _quiet(store, "yard", "porch", "cellar")
    assert store.where_now("nim").phrase == "in the loft"


def test_fade_survives_one_quiet_episode_and_drops_on_the_second():
    store = ThoughtStore(FADE)
    store.teach([fact("nim", "at", "loft")])
    store.reinforce_used(store.where_now("nim").thoughts)
    _quiet(store, "yard")
    assert store.where_now("nim") is not None
    assert store.where_now("nim").phrase == "in the loft"
    _quiet(store, "porch")
    assert store.where_now("nim") is None


def test_reteach_after_a_prune_captures_the_fact_again():
    store = ThoughtStore(FADE)
    store.teach([fact("nim", "at", "loft")])
    store.reinforce_used(store.where_now("nim").thoughts)
    _quiet(store, "yard", "porch")
    assert store.where_now("nim") is None
    store.teach([fact("nim", "at", "loft")])
    assert store.where_now("nim").phrase == "in the loft"
    assert store.where_now("nim").thoughts[0].weight == FADE.initial


def test_presets_differ_only_by_the_published_policy():
    assert KEEP.decay == 0.0
    assert FADE.decay > 0.0
    assert FADE.initial < KEEP.initial
    assert FADE.initial >= FADE.prune_below
    used = FADE.initial + FADE.use_reinforce - FADE.decay
    used_twice = used - FADE.decay
    assert used >= FADE.prune_below
    assert used_twice < FADE.prune_below
