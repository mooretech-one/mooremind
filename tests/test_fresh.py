"""One-shot score of tests/paraphrase_fresh.py.

Recorded after a single run. The grammar was not edited to move these
numbers. A later change that moves them is a new measurement and should be
described as one.
"""

from collections import Counter

from mooremind.learner import TextFadeLearner, TextKeepLearner, classify_miss
from paraphrase_data import asks
from paraphrase_fresh import FRESH
from test_paraphrase import _gold, _reply


def _classes(learner_cls: type[TextKeepLearner]) -> tuple[int, int, Counter[str]]:
    correct = 0
    labels: Counter[str] = Counter()
    for story, index in asks(FRESH):
        learner = learner_cls()
        gold = _gold(story.beats, index).casefold()
        reply = _reply(learner, story, index).casefold()
        if reply == gold:
            correct += 1
        else:
            labels[classify_miss(learner.events[-1])] += 1
    total = sum(1 for _story, _index in asks(FRESH))
    return correct, total, labels


def test_each_subtype_has_at_least_ten_fresh_asks():
    counts: Counter[str] = Counter(story.subtype for story, _index in asks(FRESH))
    assert set(counts) == {
        "one_shot",
        "update",
        "inheritance",
        "composition",
        "interference",
        "refresh",
    }
    assert all(count >= 10 for count in counts.values())


def test_fresh_keep_is_the_one_shot_measurement():
    correct, total, labels = _classes(TextKeepLearner)
    assert (correct, total) == (0, 60)
    assert dict(labels) == {
        "fallback": 1,
        "parse_failure": 58,
        "unrecognised_question": 1,
    }


def test_fresh_fade_is_the_one_shot_measurement():
    correct, total, labels = _classes(TextFadeLearner)
    assert (correct, total) == (0, 60)
    assert dict(labels) == {
        "fallback": 1,
        "parse_failure": 58,
        "unrecognised_question": 1,
    }
