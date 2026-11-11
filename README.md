# MooreMind

MooreMind is a small Python learner. It stores knowledge as atomic thoughts, relationships of the form `[source -> relation -> target]` with a weight and optional qualifiers, and a fact is usable the moment it is taught. There is no training run and no language model.

It is not a chatbot or a planner. It does not see pixels, and it does not call a network. `KeepLearner` reads structured assertions. `TextKeepLearner` reads the English sentence on each assertion and a small list of sentence shapes. That list is not a general parser. A separate cue list reads a recognised question far enough to choose which stored fact to report.

The sibling benchmark is [MooreSense](https://github.com/mooretech-one/mooresense). MooreMind implements that project's external-learner protocol (`reset`, `teach`, `answer`) and is scored on the public dev learn items. MooreSense is a read-only dependency. This repo does not modify it and does not contain its private test split.

## Install

Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check .
```

```python
from mooremind import MooreMind

mind = MooreMind()
mind.teach(
    [
        {
            "source": "nim",
            "type": "at",
            "target": "kitchen",
            "text": "Nim is in the kitchen.",
            "qualifiers": {"timeframe": "t1"},
        },
        {
            "source": "nim",
            "type": "at",
            "target": "garden",
            "text": "Nim moves to the garden.",
            "qualifiers": {"timeframe": "t2"},
        },
    ]
)


class Question:
    question = "Where is Nim now?"
    choices = None


print(mind.answer(Question()))  # in the garden
```

`MooreMind()` is the `keep` preset: later episodes do not decay a fact. `FadeLearner` uses a lower starting weight and drops a fact on the second episode that does not restate it. `TextKeepLearner` and `TextFadeLearner` are the same two policies fed from English. The numbers, and how they differ from the book they are loosely drawn from, are in [docs/design.md](docs/design.md).

## Score with MooreSense

Tested against MooreSense commit `de388dc80807fbb232aef98d6593f52808f8769e` (the `main` tip when this prototype was measured). The dev learn slice is 144 items, 48 seeds, six sub-types. Filter to `category == learn` yourself. Passing the whole dev file makes the harness call a chat model for the other categories.

```bash
pip install -e ".[eval]"
# or: pip install "mooresense @ git+https://github.com/mooretech-one/mooresense.git@de388dc80807fbb232aef98d6593f52808f8769e"

python - << 'PY'
from pathlib import Path
from mooresense.schema import dumps_item, load_jsonl

items = [
    item
    for item in load_jsonl(Path("path/to/mooresense/data/dev.jsonl"))
    if item.category.value == "learn"
]
Path("/tmp/mooresense-learn.jsonl").write_text(
    "".join(dumps_item(item) + "\n" for item in items),
    encoding="utf-8",
)
print(len(items))
PY

MOOREMIND_ACCOUNTING=results/keep.accounting.json \
mooresense eval \
  --teach-mode external \
  --learner mooremind.learner:KeepLearner \
  --items /tmp/mooresense-learn.jsonl \
  --out results/keep.jsonl

MOOREMIND_ACCOUNTING=results/fade.accounting.json \
mooresense eval \
  --teach-mode external \
  --learner mooremind.learner:FadeLearner \
  --items /tmp/mooresense-learn.jsonl \
  --out results/fade.jsonl

# English sentences only. The trace records which sentences and questions were read.
MOOREMIND_ACCOUNTING=results/text-keep.accounting.json \
MOOREMIND_TRACE=results/text-keep.trace.jsonl \
mooresense eval \
  --teach-mode external \
  --learner mooremind.learner:TextKeepLearner \
  --items /tmp/mooresense-learn.jsonl \
  --out results/text-keep.jsonl
```

`MOOREMIND_ACCOUNTING` is optional. When it is set, the learner rewrites that file with how many answers came from the store and how many fell back to `I don't know`. A fallback does not look at the choices. The measured dev numbers are in [docs/results.md](docs/results.md).

## Running the model evaluation

This step needs Ollama on the machine that has the models. CI does not call a model. The model is only a translator. The store still does the remembering. Thinking is off, temperature is 0, and the cap is 512 tokens.

Paraphrase sets (all development data now: the first file, the PR2 set, and the fresh 60). One command per model. A re-run resumes from the JSONL. `--restart` starts over.

```bash
python -m mooremind.paraphrase_eval --model gemma3:1b
python -m mooremind.paraphrase_eval --model qwen3:1.7b
python -m mooremind.paraphrase_eval --model qwen3:8b
```

Each command writes `results/paraphrase-<model>.jsonl`, a `.summary.json`, and a `.md` table. Optional: `MOOREMIND_LLM_BASE_URL` (default `http://localhost:11434/v1`), `MOOREMIND_LLM_API_KEY`, `MOOREMIND_LLM_TIMEOUT`, `MOOREMIND_LLM_SEED`.

The 144 public MooreSense learn items, through the external learner. Filter to `category == learn` first, as in the section above. Point `--learner` at `mooremind.learner:LlmKeepLearner` or `LlmFadeLearner`. The class is constructed with no arguments, so the model comes from the environment.

```bash
export MOOREMIND_LLM_BASE_URL=http://localhost:11434/v1
export MOOREMIND_LLM_MODEL=gemma3:1b

mooresense eval \
  --teach-mode external \
  --learner mooremind.learner:LlmKeepLearner \
  --items /tmp/mooresense-learn.jsonl \
  --out results/llm-keep-gemma3-1b.jsonl

MOOREMIND_LLM_MODEL=gemma3:1b \
mooresense eval \
  --teach-mode external \
  --learner mooremind.learner:LlmFadeLearner \
  --items /tmp/mooresense-learn.jsonl \
  --out results/llm-fade-gemma3-1b.jsonl
```

Repeat with `MOOREMIND_LLM_MODEL=qwen3:1.7b` and `qwen3:8b`, and change the `--out` name to match. A bad reply is counted and skipped. It does not stop the run.

## Topic rule

No tax, fiscal, government, or public-administration content in code, tests, examples, or docs. Examples stay in ordinary kitchens, pets, toys, gardens, and workshops. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
