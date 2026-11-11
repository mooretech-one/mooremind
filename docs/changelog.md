# Changelog

## Unreleased

- Text-path learners `TextKeepLearner` and `TextFadeLearner`. They read the English teach sentence and the question, and they refuse a sentence or a question form they do not know. The structured learners are unchanged. Dev learn scores for both paths are in `docs/results.md`.
- The text front end now splits coordinated clauses, reads inverted order, possessives, from-to moves, clefts, and pronouns bound to the latest subject or class in the episode. Question cues may sit anywhere in the question. Dev learn text scores stay 1.000 and 0.875. A new 60-question paraphrase batch, written before that change, scored 0.000 for both presets on the single measurement.
- `LlmKeepLearner` and `LlmFadeLearner` use a local OpenAI-compatible model only to translate English into store JSON. Invalid output is skipped. `python -m mooremind.paraphrase_eval` compares that path with the same model answering from the English. The tower run is not in this commit.
