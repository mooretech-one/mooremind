"""Translator validation, with no model server."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from helpers import Choice, Item
from mooremind.learner import FALLBACK, LlmKeepLearner
from mooremind.llm_http import LlmSettings, TransportError, UrllibChat
from mooremind.translate import SYSTEM_PROMPT, parse_question_json, parse_teach


class _Sentence:
    def __init__(self, text: str) -> None:
        self._text = text

    def __getattribute__(self, name: str):
        if name in {"source", "type", "target", "qualifiers"}:
            raise AssertionError(f"translator path read {name}")
        return object.__getattribute__(self, name)

    @property
    def text(self) -> str:
        return self._text


class _Question(Item):
    def __getattribute__(self, name: str):
        if name in {"answer", "world_state", "trace", "teach", "context"}:
            raise AssertionError(f"translator path read {name}")
        return object.__getattribute__(self, name)


class _Script:
    def __init__(self, teach: str, question: str) -> None:
        self.teach = teach
        self.question = question
        self.seen: list[str] = []

    def complete(self, messages: list[dict[str, str]]) -> str:
        user = messages[-1]["content"]
        self.seen.append(user)
        if "TASK teach" in user:
            return self.teach
        if "TASK question" in user:
            return self.question
        raise AssertionError(user)


def test_prompt_examples_are_not_copied_from_the_paraphrase_files():
    for banned in (
        "Paxo",
        "zindle",
        "has taken up residence",
        "In the loft sits",
        "Where is Nim",
        "mooresense",
    ):
        assert banned not in SYSTEM_PROMPT


def test_valid_teach_and_question_json():
    taught = parse_teach('{"assertions":[{"source":"kettle","type":"on","target":"stove"}]}')
    assert taught.status == "ok"
    assert taught.assertions[0]["target"] == "stove"
    asked = parse_question_json('{"kind":"index","entity":"dot","index":1}')
    assert asked.status == "ok"
    assert asked.query is not None
    assert asked.query.index == 1


def test_a_fence_is_accepted_and_prose_around_json_is_not():
    fenced = '```json\n{"assertions":[{"source":"dot","type":"in","target":"larder"}]}\n```'
    assert parse_teach(fenced).status == "ok"
    prose = 'Here you go {"assertions":[{"source":"dot","type":"in","target":"larder"}]}'
    assert parse_teach(prose).status == "json_invalid"


def test_invalid_json_off_vocabulary_and_empty_are_separate():
    assert parse_teach("{not json").status == "json_invalid"
    assert parse_teach('{"assertions":[]}').status == "empty"
    loved = '{"assertions":[{"source":"dot","type":"loves","target":"yard"}]}'
    assert parse_teach(loved).status == "off_vocabulary"
    capital = '{"assertions":[{"source":"Dot","type":"in","target":"larder"}]}'
    assert parse_teach(capital).status == "off_vocabulary"
    extra = '{"assertions":[{"source":"dot","type":"in","target":"larder","note":"x"}]}'
    assert parse_teach(extra).status == "off_vocabulary"
    flagged = parse_question_json('{"kind":"index","entity":"dot","index":true}')
    assert flagged.status == "off_vocabulary"


def test_learner_uses_only_text_and_does_not_guess_past_a_bad_reply():
    client = _Script(
        json.dumps({"assertions": [{"source": "nim", "type": "in", "target": "loft"}]}),
        json.dumps({"kind": "where", "entity": "nim"}),
    )
    learner = LlmKeepLearner(client=client, mapping=False, self_check=False, retry=False)
    learner.teach([_Sentence("Nim is in the loft.")])
    item = _Question(
        "Where is Nim?",
        [Choice("A", "in the cellar"), Choice("B", "in the loft")],
    )
    assert learner.answer(item) == "B"
    assert all("in the cellar" not in message for message in client.seen)
    bad = LlmKeepLearner(
        client=_Script("this is not json", "also not json"),
        mapping=False,
        self_check=False,
        retry=False,
    )
    bad.teach([_Sentence("Nim is in the loft.")])
    assert bad.answer(_Question("Where is Nim?", [Choice("A", "in the loft")])) == FALLBACK
    assert bad.translator_failures["json_invalid"] == 2


def test_off_vocabulary_teaches_nothing():
    client = _Script(
        '{"assertions":[{"source":"nim","type":"loves","target":"loft"}]}',
        '{"kind":"where","entity":"nim"}',
    )
    learner = LlmKeepLearner(client=client, mapping=False, self_check=False, retry=False)
    learner.teach([_Sentence("Nim is in the loft.")])
    assert learner.accepted_facts == []
    assert learner.teach_outcomes[-1].status == "off_vocabulary"


def test_a_timeout_is_a_transport_failure_not_a_crash():
    class _Slow:
        def complete(self, messages: list[dict[str, str]]) -> str:
            raise TransportError("timeout", "slow")

    learner = LlmKeepLearner(client=_Slow(), mapping=False, self_check=False, retry=False)
    learner.teach([_Sentence("Nim is in the loft.")])
    assert learner.teach_outcomes[-1].status == "transport"
    assert learner.answer(_Question("Where is Nim?", None)) == FALLBACK


def test_mapping_rewrites_a_listed_alias_and_rejects_the_rest():
    raw = '{"assertions":[{"source":"kettle","type":"inside","target":"cup"}]}'
    mapped = parse_teach(raw, mapping=True)
    assert mapped.status == "ok"
    assert mapped.assertions[0]["type"] == "in"
    assert mapped.mapped == ["inside->in"]
    assert parse_teach(raw, mapping=False).status == "off_vocabulary"
    colour = parse_question_json('{"kind":"colour","entity":"dot"}', mapping=True)
    assert colour.status == "ok"
    assert colour.query is not None and colour.query.kind == "color"
    assert parse_question_json('{"kind":"colour","entity":"dot"}').status == "off_vocabulary"


class _Check:
    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.seen: list[str] = []

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.seen.append(messages[-1]["content"])
        return self.replies.pop(0)


def test_self_check_keep_fix_and_drop():
    keep = _Check(
        [
            '{"assertions":[{"source":"kettle","type":"on","target":"stove"}]}',
            '{"decision":"keep"}',
        ]
    )
    learner = LlmKeepLearner(client=keep, mapping=False, self_check=True, retry=False)
    learner.teach([_Sentence("The kettle is on the stove.")])
    assert learner.accepted_facts == [("kettle", "on", "stove")]
    assert learner.teach_outcomes[-1].checked == "keep"
    assert learner.translator.calls == 2

    fix = _Check(
        [
            '{"assertions":[{"source":"kettle","type":"on","target":"floor"}]}',
            '{"decision":"fix","assertions":[{"source":"kettle","type":"on","target":"stove"}]}',
        ]
    )
    fixed = LlmKeepLearner(client=fix, mapping=False, self_check=True, retry=False)
    fixed.teach([_Sentence("The kettle is on the stove.")])
    assert fixed.accepted_facts == [("kettle", "on", "stove")]
    assert fixed.teach_outcomes[-1].checked == "fix"

    drop = _Check(
        [
            '{"assertions":[{"source":"kettle","type":"on","target":"stove"}]}',
            '{"decision":"drop"}',
        ]
    )
    dropped = LlmKeepLearner(client=drop, mapping=False, self_check=True, retry=False)
    dropped.teach([_Sentence("The kettle is on the stove.")])
    assert dropped.accepted_facts == []
    assert dropped.teach_outcomes[-1].status == "dropped"


def test_one_retry_feeds_the_validator_error_back():
    client = _Check(
        [
            "not json",
            '{"assertions":[{"source":"kettle","type":"on","target":"stove"}]}',
        ]
    )
    learner = LlmKeepLearner(client=client, mapping=False, self_check=False, retry=True)
    learner.teach([_Sentence("The kettle is on the stove.")])
    assert learner.accepted_facts == [("kettle", "on", "stove")]
    assert learner.teach_outcomes[-1].retried is True
    assert "Rejected:" in client.seen[1]
    assert learner.translator.calls == 2


def test_urllib_client_posts_think_off_and_reads_content():
    seen: dict[str, object] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            seen["payload"] = payload
            body = json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"assertions":[{"source":"kettle",'
                                    '"type":"on","target":"stove"}]}'
                                )
                            }
                        }
                    ]
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        client = UrllibChat(
            LlmSettings(
                base_url=f"http://127.0.0.1:{port}/v1",
                model="gemma3:1b",
                api_key="",
                timeout=2,
                max_tokens=512,
                seed=0,
            )
        )
        raw = client.complete(
            [
                {"role": "system", "content": "test"},
                {
                    "role": "user",
                    "content": "/no_think\n\nTASK teach\n1. The kettle is on the stove.",
                },
            ]
        )
    finally:
        server.shutdown()
    assert "kettle" in raw
    payload = seen["payload"]
    assert isinstance(payload, dict)
    assert payload["think"] is False
    assert payload["reasoning_effort"] == "none"
    assert payload["temperature"] == 0
    assert payload["max_tokens"] == 512
    assert str(payload["messages"][1]["content"]).startswith("/no_think")


def test_urllib_timeout_is_reported():
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            import time

            time.sleep(1.5)
            self.send_response(200)
            self.end_headers()

        def log_message(self, fmt: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        client = UrllibChat(
            LlmSettings(
                base_url=f"http://127.0.0.1:{port}/v1",
                model="gemma3:1b",
                api_key="",
                timeout=0.2,
                max_tokens=512,
                seed=0,
            )
        )
        try:
            client.complete([{"role": "user", "content": "hello"}])
            raised = False
        except TransportError as exc:
            raised = exc.kind == "timeout"
    finally:
        server.shutdown()
    assert raised
