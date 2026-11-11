"""The paraphrase comparison runs without a model server."""

import json

from mooremind.paraphrase_eval import evaluate
from paraphrase_data import DEV


class _Client:
    def __init__(self, teach: str, question: str, baseline: str) -> None:
        self.teach = teach
        self.question = question
        self.baseline = baseline
        self.calls = 0

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls += 1
        user = messages[-1]["content"]
        if "TASK teach" in user:
            return self.teach
        if "TASK question" in user:
            return self.question
        return self.baseline


def _one_story():
    from test_paraphrase import _gold

    story = next(story for story in DEV if story.id == "dev.one_shot.loft")
    return [("dev", story, 0, _gold)]


def test_a_wrong_target_is_a_wrong_assertion_and_resume_skips_it(tmp_path):
    teach = '{"assertions":[{"source":"nim","type":"in","target":"cellar"}]}'
    question = '{"kind":"where","entity":"nim"}'
    client = _Client(teach, question, "Answer: in the loft")
    out = tmp_path / "run.jsonl"
    summary = evaluate(client, out, "fake", stories=_one_story())
    keep = summary["splits"]["dev"]["llm-keep"]
    assert keep["n_correct"] == 0
    assert keep["failures"]["wrong_assertion"] == 1
    alone = summary["splits"]["dev"]["model-alone"]
    assert alone["n_correct"] == 1
    calls = client.calls
    evaluate(client, out, "fake", stories=_one_story())
    assert client.calls == calls
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3


def test_invalid_json_is_labelled_and_does_not_raise(tmp_path):
    client = _Client("not json", "not json", "Answer: somewhere")
    summary = evaluate(client, tmp_path / "bad.jsonl", "fake", stories=_one_story())
    failures = summary["splits"]["dev"]["llm-keep"]["failures"]
    assert failures["translator_json_invalid"] == 1
