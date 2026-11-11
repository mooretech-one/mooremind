"""The text path reads sentences, not structured fields or gold."""

from helpers import Choice, Item
from mooremind.learner import FALLBACK, TextKeepLearner


class _Sentence:
    """Only ``text`` is readable. Structured fields raise."""

    def __init__(self, text: str) -> None:
        self._text = text

    def __getattribute__(self, name: str):
        if name in {"source", "type", "target", "qualifiers"}:
            raise AssertionError(f"text path read {name}")
        return object.__getattribute__(self, name)

    @property
    def text(self) -> str:
        return self._text


class _Question(Item):
    def __getattribute__(self, name: str):
        if name in {"answer", "world_state", "trace", "teach", "context"}:
            raise AssertionError(f"text path read {name}")
        return object.__getattribute__(self, name)


def test_text_path_learns_from_the_sentence_and_ignores_hidden_fields():
    learner = TextKeepLearner()
    learner.teach([_Sentence("Nim is in the loft.")])
    item = _Question(
        "Where is Nim?",
        [Choice("A", "in the cellar"), Choice("B", "in the loft")],
    )
    assert learner.answer(item) == "B"
    assert learner.sentences_parsed == 1
    assert learner.sentences_unparsed == 0
    assert learner.fell_back == 0


def test_an_unknown_sentence_is_counted_and_does_not_guess():
    learner = TextKeepLearner()
    learner.teach([_Sentence("In the loft sits Nim.")])
    item = _Question(
        "Where is Nim?",
        [Choice("A", "in the loft"), Choice("B", FALLBACK)],
    )
    assert learner.answer(item) == FALLBACK
    assert learner.sentences_unparsed == 1
    assert learner.stats()["unparsed_rate"] == 1
    assert learner.fell_back == 1


def test_an_unknown_question_form_falls_back_without_reading_choices_for_a_guess():
    learner = TextKeepLearner()
    learner.teach([_Sentence("Nim is in the loft.")])
    item = _Question(
        "In which room do we find Nim?",
        [Choice("A", "in the loft"), Choice("B", "in the yard")],
    )
    assert learner.answer(item) == FALLBACK
    assert learner.from_store == 0
