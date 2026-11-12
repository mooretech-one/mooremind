"""Compare a translator-plus-store with the same model answering alone.

The paraphrase files are development data. This script does not score
MooreSense. Run it on the tower, where Ollama is available. A bad model
reply is logged and skipped. A re-run resumes from the JSONL already written.

    python -m mooremind.paraphrase_eval --model gemma3:1b
    python -m mooremind.paraphrase_eval --model qwen3:1.7b
    python -m mooremind.paraphrase_eval --model qwen3:8b
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from mooremind.learner import FALLBACK, LlmFadeLearner, LlmKeepLearner, LlmMooreMind
from mooremind.llm_http import ChatClient, UrllibChat, settings_from_env

_FAILURES = (
    "translator_transport",
    "translator_json_invalid",
    "translator_empty",
    "translator_off_vocabulary",
    "translator_dropped",
    "wrong_query",
    "wrong_assertion",
    "store_or_decay",
    "fallback",
)
_STATUS = {
    "dropped": "translator_dropped",
    "empty": "translator_empty",
    "json_invalid": "translator_json_invalid",
    "off_vocabulary": "translator_off_vocabulary",
    "transport": "translator_transport",
}
_VARIANTS = {
    "baseline": {"mapping": False, "retry": False, "self_check": False},
    "mapping": {"mapping": True, "retry": False, "self_check": False},
    "selfcheck": {"mapping": False, "retry": False, "self_check": True},
    "all": {"mapping": True, "retry": True, "self_check": True},
}


def _stories() -> list[tuple[str, Any]]:
    root = Path(__file__).resolve().parents[2]
    tests = root / "tests"
    if str(tests) not in sys.path:
        sys.path.insert(0, str(tests))
    from paraphrase_data import DEV, asks
    from paraphrase_fresh import FRESH
    from paraphrase_heldout import HOLDOUT
    from test_paraphrase import _gold

    grouped = [("dev", DEV), ("heldout", HOLDOUT), ("fresh", FRESH)]
    rows: list[tuple[str, Any]] = []
    for name, stories in grouped:
        for story, index in asks(stories):
            rows.append((name, story, index, _gold))
    return rows


def gold_facts(beats: tuple[Any, ...], upto: int) -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    for beat in beats[: upto + 1]:
        for raw in beat.facts:
            found.append((str(raw["source"]), str(raw["type"]), str(raw["target"])))
    return found


def query_matches(learner: LlmMooreMind, beat: Any) -> bool:
    outcome = learner.query_outcome
    if outcome is None or outcome.query is None or outcome.status != "ok":
        return False
    query = outcome.query
    if query.kind != beat.kind or query.entity != beat.entity:
        return False
    if beat.kind == "index" and query.index != (0 if beat.index is None else beat.index):
        return False
    return True


def classify_store_miss(
    learner: LlmMooreMind,
    beat: Any,
    beats: tuple[Any, ...],
    upto: int,
    reply: str,
) -> str:
    """One label for a wrong store reply. Transport and JSON come first."""
    outcomes = list(learner.teach_outcomes)
    if learner.query_outcome is not None:
        outcomes.append(learner.query_outcome)
    statuses = {item.status for item in outcomes}
    for status, label in _STATUS.items():
        if status in statuses:
            return label
    if not query_matches(learner, beat):
        return "wrong_query"
    if learner.accepted_facts != gold_facts(beats, upto):
        return "wrong_assertion"
    if reply.strip().casefold() == FALLBACK.casefold():
        return "store_or_decay" if learner.accepted_facts else "fallback"
    return "store_or_decay"


def _norm(text: str) -> str:
    """Case and punctuation only, so 'in the loft.' matches 'in the loft'."""
    cleaned = re.sub(r"[^a-z0-9\s]", " ", text.casefold())
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_answer(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        folded = line.casefold()
        if folded.startswith("answer:"):
            return line.split(":", 1)[1].strip()
    return text.strip()


def baseline_examples() -> str:
    """The same three scenes as the translator, in plain question and answer form."""
    return "\n".join(
        [
            "Scene: The kettle is on the stove.",
            "Question: Where is the kettle?",
            "Answer: on the stove",
            "",
            "Scene: Dot's morning starts in the larder. Dot finishes in the courtyard.",
            "A pibble is cream. Dot is a pibble.",
            "Question: What colour is Dot?",
            "Answer: cream",
            "",
            "Scene: Dot's morning starts in the larder. Dot finishes in the courtyard.",
            "Question: What place was second for Dot?",
            "Answer: in the courtyard",
        ]
    )


def baseline_prompt(sentences: list[str], question: str, *, examples: bool = False) -> str:
    """MooreSense free-text shape: the story, the question, an Answer line.

    ``examples`` adds the three plain scenes. The old prompt leaves them out
    so the previous tower numbers can be reproduced.
    """
    parts = [
        "Reply with the short answer.",
        "End with a final line exactly in this form: Answer: <value>.",
        "That line is what gets scored.",
        "",
    ]
    if examples:
        parts.extend(["Worked examples:", baseline_examples(), ""])
    for sentence in sentences:
        parts.append(sentence)
    parts.extend(
        [
            "",
            question,
            "",
            "The last line must be exactly `Answer: ` followed by the short answer "
            "on that same line and no other words.",
        ]
    )
    return "\n".join(parts)


class Baseline:
    def __init__(self, client: ChatClient, *, examples: bool = False) -> None:
        self.client = client
        self.examples = examples

    def answer(self, sentences: list[str], question: str) -> str:
        prompt = baseline_prompt(sentences, question, examples=self.examples)
        messages = [
            {
                "role": "system",
                "content": "You answer questions about a small everyday scene.",
            },
            {"role": "user", "content": "/no_think\n\n" + prompt},
        ]
        try:
            return extract_answer(self.client.complete(messages))
        except Exception as exc:  # a bad reply must not stop the run
            return f"[transport] {exc}"


def _key(model: str, arm: str, split: str, story_id: str, index: int) -> str:
    return f"{model}|{arm}|{split}|{story_id}|{index}"


def _load_done(path: Path) -> dict[str, dict[str, Any]]:
    done: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return done
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        done[str(row["key"])] = row
    return done


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()


def _run_store(
    learner: LlmMooreMind,
    story: Any,
    upto: int,
) -> tuple[str, str]:
    class _Text:
        def __init__(self, text: str) -> None:
            self.text = text

    class _Ask:
        def __init__(self, question: str) -> None:
            self.question = question
            self.choices = None

    learner.reset()
    reply = FALLBACK
    # Earlier questions are asked too, so a recall can reinforce a fact
    # before a later episode. That is what the MooreSense harness does.
    for index, beat in enumerate(story.beats[: upto + 1]):
        if beat.sentences:
            try:
                learner.teach([_Text(sentence) for sentence in beat.sentences])
            except Exception as exc:
                print(f"teach error {story.id}: {exc}", file=sys.stderr)
                traceback.print_exc()
        if not beat.question:
            continue
        try:
            got = learner.answer(_Ask(beat.question))
        except Exception as exc:
            print(f"answer error {story.id}: {exc}", file=sys.stderr)
            got = FALLBACK
        if index == upto:
            reply = got
    label = classify_store_miss(learner, story.beats[upto], story.beats, upto, reply)
    return reply, label


def _run_baseline(baseline: Baseline, story: Any, upto: int) -> str:
    sentences: list[str] = []
    question = ""
    for index, beat in enumerate(story.beats[: upto + 1]):
        sentences.extend(beat.sentences)
        if beat.question and index == upto:
            question = beat.question
    try:
        return baseline.answer(sentences, question)
    except Exception as exc:
        return f"[transport] {exc}"


def _store_arms(client: ChatClient, variants: tuple[str, ...]) -> list[tuple[str, LlmMooreMind]]:
    arms: list[tuple[str, LlmMooreMind]] = []
    for name in variants:
        flags = _VARIANTS[name]
        for label, cls in (("keep", LlmKeepLearner), ("fade", LlmFadeLearner)):
            arms.append((f"llm-{label}-{name}", cls(client=client, **flags)))
    return arms


def evaluate(
    client: ChatClient,
    out_path: Path,
    model: str,
    stories: list[tuple[str, Any, int, Any]] | None = None,
    *,
    variants: tuple[str, ...] = ("baseline", "mapping", "selfcheck", "all"),
    baselines: tuple[str, ...] = ("old", "examples"),
) -> dict[str, Any]:
    """Score each translator variant and both model-alone prompts.

    Resume from ``out_path``. The arm name is part of the resume key.
    """
    done = _load_done(out_path)
    arms = _store_arms(client, variants)
    alone = {
        "model-alone": Baseline(client, examples=False),
        "model-alone-examples": Baseline(client, examples=True),
    }
    for split, story, index, gold_of in stories if stories is not None else _stories():
        gold = gold_of(story.beats, index)
        for arm, learner in arms:
            key = _key(model, arm, split, story.id, index)
            if key in done:
                continue
            reply, label = _run_store(learner, story, index)
            correct = _norm(reply) == _norm(gold)
            row = {
                "arm": arm,
                "correct": correct,
                "failure": None if correct else label,
                "gold": gold,
                "index": index,
                "key": key,
                "model": model,
                "prediction": reply,
                "split": split,
                "story": story.id,
                "subtype": story.subtype,
            }
            _append(out_path, row)
            done[key] = row
            print(f"{arm} {split} {story.id}#{index} {'ok' if correct else label}", flush=True)
        for arm, baseline in alone.items():
            if arm == "model-alone" and "old" not in baselines:
                continue
            if arm == "model-alone-examples" and "examples" not in baselines:
                continue
            key = _key(model, arm, split, story.id, index)
            if key in done:
                continue
            reply = _run_baseline(baseline, story, index)
            correct = _norm(reply) == _norm(gold)
            row = {
                "arm": arm,
                "correct": correct,
                "failure": None if correct else "baseline_miss",
                "gold": gold,
                "index": index,
                "key": key,
                "model": model,
                "prediction": reply,
                "split": split,
                "story": story.id,
                "subtype": story.subtype,
            }
            _append(out_path, row)
            done[key] = row
            mark = "ok" if correct else "miss"
            print(f"{arm} {split} {story.id}#{index} {mark}", flush=True)
    summary = summarize(list(done.values()), model)
    summary_path = out_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    markdown = render_markdown(summary)
    out_path.with_suffix(".md").write_text(markdown, encoding="utf-8")
    print(markdown)
    return summary


def summarize(rows: list[dict[str, Any]], model: str) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("model") != model:
            continue
        grouped[(str(row["split"]), str(row["arm"]))].append(row)
    report: dict[str, Any] = {"model": model, "splits": {}}
    for split, arm in sorted(grouped):
        items = grouped[(split, arm)]
        flags = [bool(item["correct"]) for item in items]
        by_sub: dict[str, list[bool]] = defaultdict(list)
        failures: Counter[str] = Counter()
        for item in items:
            by_sub[str(item["subtype"])].append(bool(item["correct"]))
            if not item["correct"] and item.get("failure"):
                failures[str(item["failure"])] += 1
        block = report["splits"].setdefault(split, {})
        block[arm] = {
            "accuracy": (sum(flags) / len(flags)) if flags else None,
            "by_subtype": {
                name: {
                    "accuracy": sum(bits) / len(bits),
                    "correct": sum(bits),
                    "n": len(bits),
                }
                for name, bits in sorted(by_sub.items())
            },
            "failures": {name: failures.get(name, 0) for name in (*_FAILURES, "baseline_miss")},
            "n": len(flags),
            "n_correct": sum(flags),
        }
    return report


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [f"# Paraphrase eval {summary['model']}", ""]
    lines.append(
        "| split | arm | accuracy | one_shot | update | inheritance | composition | "
        "interference | refresh |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    subtypes = ("one_shot", "update", "inheritance", "composition", "interference", "refresh")
    for split, arms in summary["splits"].items():
        for arm, block in arms.items():
            cells = []
            for name in subtypes:
                sub = block["by_subtype"].get(name)
                cells.append("" if sub is None else f"{sub['correct']}/{sub['n']}")
            accuracy = block["accuracy"]
            if accuracy is None:
                shown = ""
            else:
                shown = f"{accuracy:.3f} ({block['n_correct']}/{block['n']})"
            lines.append("| " + " | ".join([split, arm, shown, *cells]) + " |")
    lines.append("")
    lines.append(
        "| split | arm | transport | json_invalid | empty | off_vocabulary | "
        "wrong_query | wrong_assertion | store_or_decay | fallback | dropped | baseline_miss |"
    )
    lines.append(
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    keys = (
        "translator_transport",
        "translator_json_invalid",
        "translator_empty",
        "translator_off_vocabulary",
        "wrong_query",
        "wrong_assertion",
        "store_or_decay",
        "fallback",
        "translator_dropped",
        "baseline_miss",
    )
    for split, arms in summary["splits"].items():
        for arm, block in arms.items():
            counts = [str(block["failures"].get(key, 0)) for key in keys]
            lines.append("| " + " | ".join([split, arm, *counts]) + " |")
    lines.append("")
    return "\n".join(lines)


def _slug(model: str) -> str:
    return model.replace(":", "-").replace("/", "-")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Translator plus store versus the model alone.")
    parser.add_argument("--model", required=True, help="Model name, for example gemma3:1b")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Defaults to MOOREMIND_LLM_BASE_URL or local Ollama",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="JSONL path. Default results/paraphrase-<model>.jsonl",
    )
    parser.add_argument("--restart", action="store_true", help="Delete the JSONL and start over")
    parser.add_argument(
        "--variant",
        action="append",
        choices=tuple(_VARIANTS),
        dest="variants",
        help="Repeat to select translator variants. Default: baseline, mapping, selfcheck, all.",
    )
    parser.add_argument(
        "--baseline-prompt",
        action="append",
        choices=("old", "examples"),
        dest="baselines",
        help="Repeat to select model-alone prompts. Default: both.",
    )
    args = parser.parse_args(argv)
    variants = tuple(args.variants or _VARIANTS)
    baselines = tuple(args.baselines or ("old", "examples"))
    settings = settings_from_env()
    if args.base_url:
        settings = type(settings)(
            base_url=args.base_url.rstrip("/"),
            model=args.model,
            api_key=settings.api_key,
            timeout=settings.timeout,
            max_tokens=settings.max_tokens,
            seed=settings.seed,
        )
    else:
        settings = type(settings)(
            base_url=settings.base_url,
            model=args.model,
            api_key=settings.api_key,
            timeout=settings.timeout,
            max_tokens=settings.max_tokens,
            seed=settings.seed,
        )
    root = Path(__file__).resolve().parents[2]
    out = args.out or (root / "results" / f"paraphrase-{_slug(args.model)}.jsonl")
    if args.restart and out.is_file():
        out.unlink()
    evaluate(UrllibChat(settings), out, args.model, variants=variants, baselines=baselines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
