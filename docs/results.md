# Dev learn results

Measured with MooreSense `0.1.0.dev0` at commit `de388dc80807fbb232aef98d6593f52808f8769e` (`main` on 2026-11-11). The file was the public dev learn slice only: 144 items, 48 seeds, three variants each. The other dev categories were not sent to a model server. `meta.base_url` in the summary JSON is the CLI default and was not called.

```bash
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
```

The harness reports chance `0.250` on this slice. Per-item rows are `results/*.jsonl`. Aggregates are `results/*.summary.json`. Store-versus-fallback totals are `results/*.accounting.json`.

## MooreMind

| preset | accuracy | one_shot | update | inheritance | composition | interference | refresh | retention (18) | seed consistency | from store | fell back |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| keep | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 144 | 0 |
| fade | 0.875 | 1.000 | 1.000 | 1.000 | 0.750 | 0.750 | 0.750 | 0.333 | 0.875 | 132 | 12 |

Each sub-type has 24 items. `keep` answered all 144 from the store. `fade` answered 132 from the store and fell back 12 times. Six of those 132 store answers were wrong, so 126 of 144 are correct. Seed consistency `0.875` is 42 of 48 seeds with every variant correct. The six seeds that miss, miss in all three variants. The learner is deterministic, and a variant only changes names.

`fade` parse failures are `0.104` (15 of 144), all `malformed`: twelve `I don't know` replies and three phrases that are not a choice. Nothing was truncated.

## What fade misses, and why

The weights were fixed before this run. Nothing here was patched because a particular seed failed.

`fade` removes a thought on the second later episode that does not restate it. One quiet episode leaves it in place. That is the whole gap.

- **Retention, 6 of 18.** The short re-query (one later episode) is still answered. The two longer re-queries, in `interference` and `refresh`, are `I don't know`. Those twelve replies are the fallback count. The fact is gone, so the choices are not consulted. MooreSense still marks the old fact correct: fading is not a gold rule there. The miss is the preset.
- **Composition, 18 of 24.** The first two episodes of a chain are intact. On the last episode the chain needs a hop taught two episodes earlier.
  - In the session that adds "held by" last, the room is gone and the reply stops at "in the tin, held by …". That string is not a choice, so the scorer calls it malformed.
  - In the session that adds the object last, the "held by" link from the first episode is gone. The reply is only "in the crate" (or the same shape under another name). That short phrase is a distractor letter, so the scorer counts a wrong answer rather than a fallback. The letter came from the phrase the store still had.

`one_shot`, `update`, and `inheritance` are one episode. Decay never runs before the question, so the two presets match.

`keep` scores 1.000 because the assertions are already structured and the cue list covers the question forms in this slice. It is not a claim about unseen wording, and it is not a claim that the same program would score 1.000 on the private split. The private split was not used.

## Text path

`TextKeepLearner` and `TextFadeLearner` read `assertion.text`, the question, and the choice strings. They do not read the structured fields. Same commit, same 144 items.

Every one of the 348 teach sentences matched a rule (`unparsed_rate` 0). Every question matched the question gate. The text path therefore repeats the structured scores, including the same 18 `fade` misses. Those 18 are class `store_or_decay`. There is no parse failure, no unrecognised question, and no bare fallback on this slice. The detail is `results/text-failures.json`.

| preset | accuracy | one_shot | update | inheritance | composition | interference | refresh | retention (18) | seed consistency | from store | fell back | sentences unread |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| text-keep | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 144 | 0 | 0 / 348 |
| text-fade | 0.875 | 1.000 | 1.000 | 1.000 | 0.750 | 0.750 | 0.750 | 0.333 | 0.875 | 132 | 12 | 0 / 348 |

The public learn English is twenty-five sentence skeletons. Covering them is why this table matches the structured one. It is not evidence that the front end reads other English.

### Failure classes

A miss is labelled in this order: a pronoun was substituted in that episode (`wrong_pronoun`); a teach sentence was not fully read (`parse_failure`); the question form was not recognised (`unrecognised_question`); the question was read and the reply was still wrong or empty because of the store, including decay (`store_or_decay`); otherwise `fallback`.

| run | wrong_pronoun | parse_failure | unrecognised_question | store_or_decay | fallback |
| --- | ---: | ---: | ---: | ---: | ---: |
| text-keep, 144 dev items | 0 | 0 | 0 | 0 | 0 |
| text-fade, 144 dev items | 0 | 0 | 0 | 18 | 0 |

The widening did not move the 144. Unread sentences are still 0 of 348. The 18 fade misses are the same items as the structured fade run.

Shapes still not read: a telegraphic list, a compressed biography ("Once in the shed, later the garden: that is Veda"), residence / tucking / hosting / "hands are on", a question with no where, which, who, whom, colour, color, or hue, and negation. A long subject that merely ends in "is <colour>" or "is a …" is accepted, which is an over-match, not a reading.

## Paraphrases written here

These items are not MooreSense. Gold is the phrase the store produces from the structured facts shipped with each item.

The original development file has 38 questions (refresh has 8, the others 6). The PR2 held-out file (36 questions, 6 per sub-type) is development data for this round: the grammar was allowed to move those scores. The fresh file (`tests/paraphrase_fresh.py`, 60 questions, 10 per sub-type) was committed before the grammar change, scored once, and not used to add a rule. That 0.000 is a disappointing one-shot result. It is reported as measured. After this pull request the fresh file is development data too.

| split | preset | accuracy | one_shot | update | inheritance | composition | interference | refresh |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development, first file | text-keep | 1.000 (38/38) | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 8/8 |
| development, first file | text-fade | 0.868 (33/38) | 6/6 | 6/6 | 6/6 | 5/6 | 4/6 | 6/8 |
| development, PR2 held-out | text-keep | 0.889 (32/36) | 5/6 | 4/6 | 6/6 | 6/6 | 5/6 | 6/6 |
| development, PR2 held-out | text-fade | 0.833 (30/36) | 5/6 | 4/6 | 6/6 | 6/6 | 4/6 | 5/6 |
| one-shot fresh | text-keep | 0.000 (0/60) | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 |
| one-shot fresh | text-fade | 0.000 (0/60) | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 |

PR2 per-sub-type counts above were recomputed with the widened grammar. The four keep misses there are two unrecognised questions ("Point to …") and two unread sentences (the telegraphic list, and the compressed biography). Fade adds the two long-gap store misses.

One-shot failure classes, both presets, because nothing in that file was readable enough for decay to matter:

| preset | wrong_pronoun | parse_failure | unrecognised_question | store_or_decay | fallback |
| --- | ---: | ---: | ---: | ---: | ---: |
| text-keep | 0 | 58 | 1 | 0 | 1 |
| text-fade | 0 | 58 | 1 | 0 | 1 |

The unrecognised question is "Shade attached to Lumen?". The fallback is "The thimble sits with whom?": the cue word is recognised, but the sentence was swallowed by the bare "is a" rule as a nonsense class membership, so the thimble was never stored. Fifty-eight sentences were refused outright. No rule was added after seeing this table.

## Frozen-model reference points

Same 144 items, as reported for the frozen models. Those runs put the teach sentences in the prompt (`in-context`) or withhold them (`no-teach`). The structured MooreMind rows see assertions. The text rows see the same sentences a model sees, through the rule list above. A higher MooreMind score on the templated dev slice is not a win at reading open English. The held-out table is the check against other wording.

| arm | system | learn accuracy |
| --- | --- | ---: |
| external, structured, no decay | MooreMind `keep` | 1.000 |
| external, structured, decay | MooreMind `fade` | 0.875 |
| external, English, no decay | MooreMind `text-keep` | 1.000 |
| external, English, decay | MooreMind `text-fade` | 0.875 |
| in-context | qwen3:8b | 0.889 |
| in-context | qwen3:1.7b | 0.694 |
| in-context | gemma3:1b | 0.333 |
| no-teach | qwen3:8b | 0.312 |
| no-teach | qwen3:1.7b | 0.236 |
| no-teach | gemma3:1b | 0.194 |
| chance | uniform over the choices | 0.250 |

## Model plus store, to be filled after the tower run

Not measured in this pull request. The tower has Ollama. The commands are in the README section "Running the model evaluation". The paraphrase files (the first development set, the PR2 held-out set, and the fresh 60) are all development data. Fill the cells from `results/paraphrase-<model>.md` after each run. Do not treat a filled table as a held-out score.

| split | arm | accuracy | one_shot | update | inheritance | composition | interference | refresh |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev | llm-keep | — | — | — | — | — | — | — |
| dev | llm-fade | — | — | — | — | — | — | — |
| dev | model-alone | — | — | — | — | — | — | — |
| heldout | llm-keep | — | — | — | — | — | — | — |
| heldout | llm-fade | — | — | — | — | — | — | — |
| heldout | model-alone | — | — | — | — | — | — | — |
| fresh | llm-keep | — | — | — | — | — | — | — |
| fresh | llm-fade | — | — | — | — | — | — | — |
| fresh | model-alone | — | — | — | — | — | — | — |

Failure counts for the store arms, same runs. `baseline_miss` is only for `model-alone`.

| split | arm | transport | json_invalid | empty | off_vocabulary | wrong_query | wrong_assertion | store_or_decay | fallback | baseline_miss |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dev | llm-keep | — | — | — | — | — | — | — | — | — |
| dev | llm-fade | — | — | — | — | — | — | — | — | — |
| dev | model-alone | — | — | — | — | — | — | — | — | — |
| heldout | llm-keep | — | — | — | — | — | — | — | — | — |
| heldout | llm-fade | — | — | — | — | — | — | — | — | — |
| heldout | model-alone | — | — | — | — | — | — | — | — | — |
| fresh | llm-keep | — | — | — | — | — | — | — | — | — |
| fresh | llm-fade | — | — | — | — | — | — | — | — | — |
| fresh | model-alone | — | — | — | — | — | — | — | — | — |

One label per miss, in this order: transport, JSON invalid, empty assertions, off-vocabulary, wrong query, wrong assertion, store/decay, fallback. A correct row is not labelled.

## Hardened translator, to be filled after the tower run

Not measured yet. The alias list and the self-check are general. They were not written against the fresh split. Resume is the same JSONL. Arms are `llm-keep-<variant>`, `llm-fade-<variant>`, `model-alone` (old prompt), and `model-alone-examples` (the three plain scenes).

```bash
python -m mooremind.paraphrase_eval --model qwen3:8b --variant baseline
python -m mooremind.paraphrase_eval --model qwen3:8b --variant mapping
python -m mooremind.paraphrase_eval --model qwen3:8b --variant selfcheck
python -m mooremind.paraphrase_eval --model qwen3:8b --variant all
python -m mooremind.paraphrase_eval --model qwen3:8b --baseline-prompt old --baseline-prompt examples
```

Repeat for `qwen3:1.7b` and `gemma3:1b`. The default command, with no `--variant`, runs every variant and both prompts.

| model | split | arm | accuracy | json_invalid | off_vocabulary | wrong_query | wrong_assertion | store_or_decay | dropped |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen3:8b | fresh | llm-keep-baseline | — | — | — | — | — | — | — |
| qwen3:8b | fresh | llm-keep-mapping | — | — | — | — | — | — | — |
| qwen3:8b | fresh | llm-keep-selfcheck | — | — | — | — | — | — | — |
| qwen3:8b | fresh | llm-keep-all | — | — | — | — | — | — | — |
| qwen3:8b | fresh | llm-fade-all | — | — | — | — | — | — | — |
| qwen3:8b | fresh | model-alone | — | — | — | — | — | — | — |
| qwen3:8b | fresh | model-alone-examples | — | — | — | — | — | — | — |

Copy the same rows for `dev` and `heldout`, and for the other two models, from `results/paraphrase-<model>.md`. The first tower section above is the unhardened path. `model-alone-examples` sees the same three scenes as the translator. `model-alone` does not, so that comparison can be repeated. A wrong assertion still persists, and `fade` still counts a failed teach as an episode.
