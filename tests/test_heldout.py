"""Held-out paraphrases, scored once and locked.

A change in these numbers means the front end or the items moved. Do not
raise them by adding a parse rule for a held-out sentence.
"""

from collections import Counter

from mooremind.learner import TextFadeLearner, TextKeepLearner, classify_miss
from paraphrase_data import asks
from paraphrase_heldout import HOLDOUT
from test_paraphrase import _gold, _reply


def _classes(learner_cls: type[TextKeepLearner]) -> tuple[int, int, Counter[str]]:
    correct = 0
    labels: Counter[str] = Counter()
    for story, index in asks(HOLDOUT):
        learner = learner_cls()
        gold = _gold(story.beats, index).casefold()
        reply = _reply(learner, story, index).casefold()
        if reply == gold:
            correct += 1
            continue
        labels[classify_miss(learner.events[-1])] += 1
    total = sum(1 for _story, _index in asks(HOLDOUT))
    return correct, total, labels


def test_each_subtype_has_at_least_six_heldout_asks():
    counts: Counter[str] = Counter(story.subtype for story, _index in asks(HOLDOUT))
    assert set(counts) == {
        "one_shot",
        "update",
        "inheritance",
        "composition",
        "interference",
        "refresh",
    }
    assert all(count >= 6 for count in counts.values())


def test_heldout_keep_score_is_the_recorded_run():
    correct, total, labels = _classes(TextKeepLearner)
    assert (correct, total) == (14, 36)
    assert dict(labels) == {"parse_failure": 15, "unrecognised_question": 7}


def test_heldout_fade_score_is_the_recorded_run():
    correct, total, labels = _classes(TextFadeLearner)
    assert (correct, total) == (12, 36)
    assert dict(labels) == {
        "parse_failure": 15,
        "store_or_decay": 2,
        "unrecognised_question": 7,
    }
