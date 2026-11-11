"""Development paraphrases. Held-out items live in paraphrase_heldout.py."""

from collections import Counter

from mooremind.learner import FALLBACK, TextFadeLearner, TextKeepLearner
from mooremind.store import ThoughtStore
from mooremind.weights import KEEP
from paraphrase_data import DEV, Beat, Story, asks


def _gold(beats: tuple[Beat, ...], upto: int) -> str:
    store = ThoughtStore(KEEP)
    for beat in beats[: upto + 1]:
        if beat.facts:
            cleaned = []
            for raw in beat.facts:
                item = dict(raw)
                item["qualifiers"] = {}
                cleaned.append(item)
            store.teach(cleaned)
    beat = beats[upto]
    if beat.kind == "color":
        recall = store.color(beat.entity)
    elif beat.kind == "before":
        recall = store.where_before(beat.entity)
    elif beat.kind == "middle":
        recall = store.where_middle(beat.entity)
    elif beat.kind == "index":
        recall = store.where_index(beat.entity, 0 if beat.index is None else beat.index)
    else:
        recall = store.where_now(beat.entity)
    assert recall is not None, (beat.question, beat.entity)
    return recall.phrase


def _reply(learner: TextKeepLearner, story: Story, upto: int) -> str:
    class _Text:
        def __init__(self, text: str) -> None:
            self.text = text

    class _Ask:
        def __init__(self, question: str) -> None:
            self.question = question
            self.choices = None

    learner.reset()
    reply = ""
    for index, beat in enumerate(story.beats[: upto + 1]):
        if beat.sentences:
            learner.teach([_Text(sentence) for sentence in beat.sentences])
        # Earlier questions are asked too. A recall reinforces the thoughts
        # it reads, which is what the harness does between episodes.
        if beat.question:
            got = learner.answer(_Ask(beat.question))
            if index == upto:
                reply = got
    return reply


def _score(learner_cls: type[TextKeepLearner]) -> tuple[int, int, list[str]]:
    misses: list[str] = []
    total = 0
    for story, index in asks(DEV):
        total += 1
        gold = _gold(story.beats, index).casefold()
        reply = _reply(learner_cls(), story, index).casefold()
        if reply != gold:
            misses.append(story.id if index == 0 else f"{story.id}#{index}")
    return total - len(misses), total, misses


def test_each_subtype_has_at_least_six_dev_asks():
    counts: Counter[str] = Counter()
    for story, _index in asks(DEV):
        counts[story.subtype] += 1
    assert set(counts) == {
        "one_shot",
        "update",
        "inheritance",
        "composition",
        "interference",
        "refresh",
    }
    assert all(count >= 6 for count in counts.values())


def test_dev_keep_matches_gold_built_from_the_facts():
    correct, total, misses = _score(TextKeepLearner)
    assert misses == []
    assert correct == total


def test_dev_fade_misses_only_the_marked_long_gaps():
    expected = sorted(
        story.id if index == 0 else f"{story.id}#{index}"
        for story, index in asks(DEV)
        if story.beats[index].fade_miss
    )
    _correct, _total, misses = _score(TextFadeLearner)
    assert sorted(misses) == expected
    # The marked misses are real fallbacks or shortened chains, not gold leaks.
    learner = TextFadeLearner()
    for story, index in asks(DEV):
        if not story.beats[index].fade_miss:
            continue
        reply = _reply(learner, story, index)
        gold = _gold(story.beats, index)
        assert reply.casefold() != gold.casefold()
        if story.subtype != "composition":
            assert reply == FALLBACK
