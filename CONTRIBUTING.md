# Contributing to MooreMind

MooreMind is a small Python package. A useful change is one that a reviewer can read in a sitting: a clearer store rule, a test for a case the store gets wrong, or a note in `docs/design.md` about a limit.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest
```

Python 3.10 or newer. The package has no runtime dependencies. Scoring against MooreSense is optional and is described in the README. Do not vendor MooreSense, and do not copy its private test split.

## Topic rule

No tax, fiscal, government, or public-administration content anywhere in this repository: code, tests, examples, docs, and fixtures. Examples stay in ordinary kitchens, pets, toys, gardens, and workshops, and they use invented names. This is a standing rule for the Mooretech organisation.

`tests/test_topics.py` scans `src/`, `tests/`, and `docs/` for those words. The policy files that name the rule (`README.md`, `CONTRIBUTING.md`) are not part of that scan.

## What not to add

- A general English parser, or a learned one. Sentence shapes for the text path live in `mooremind.english` and should stay a short list. Question cues for the structured path live in `mooremind.query`. Do not add a shape in order to lift `tests/paraphrase_heldout.py`.
- An LLM call, a network call, or a secret.
- A special case for a MooreSense item id, seed, name, or gold answer.
- Reads of gold fields (`answer`, `world_state`, `trace`) from the learner.

## License

Code is Apache-2.0. See `LICENSE`.
