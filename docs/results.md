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

A miss is labelled in this order: a teach sentence in that episode was not read (`parse_failure`); the question form was not recognised (`unrecognised_question`); the question was read and the reply was still wrong or empty because of the store, including decay (`store_or_decay`); otherwise `fallback`.

| run | parse_failure | unrecognised_question | store_or_decay | fallback |
| --- | ---: | ---: | ---: | ---: |
| text-keep, 144 dev items | 0 | 0 | 0 | 0 |
| text-fade, 144 dev items | 0 | 0 | 18 | 0 |

Shapes the front end does not read: inverted order ("In the loft sits Nim"), a possessive, two facts in one sentence, "from the porch to the yard" as one sentence, a pronoun standing in for a name, and a question that does not start with where, which place, which container, who has, or colour.

## Paraphrases written here

These items are not MooreSense. Gold is the phrase the store produces from the structured facts shipped with each item. The development split is what the rules were allowed to grow on. The held-out split was written after the rules were frozen and was not used to add a rule. Development has 38 questions (refresh has 8, the others 6). Held-out has 6 per sub-type, 36 in all.

| split | preset | accuracy | one_shot | update | inheritance | composition | interference | refresh |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development | text-keep | 1.000 (38/38) | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 8/8 |
| development | text-fade | 0.868 (33/38) | 6/6 | 6/6 | 6/6 | 5/6 | 4/6 | 6/8 |
| held-out | text-keep | 0.389 (14/36) | 2/6 | 2/6 | 2/6 | 2/6 | 3/6 | 3/6 |
| held-out | text-fade | 0.333 (12/36) | 2/6 | 2/6 | 2/6 | 2/6 | 2/6 | 2/6 |

Development `fade` misses are the five marked long gaps: four `I don't know` replies and one composition chain that lost the room. All five are `store_or_decay`.

Held-out misses:

| preset | parse_failure | unrecognised_question | store_or_decay | fallback |
| --- | ---: | ---: | ---: | ---: |
| text-keep | 15 | 7 | 0 | 0 |
| text-fade | 15 | 7 | 2 | 0 |

The two extra `fade` misses are the long gaps whose sentences the front end could read. One held-out composition episode was only partly read: "The pot contains the marble" matched, and "Holding that pot is Tess" did not, so the reply was "in the pot". That miss is a `parse_failure` because the episode was not fully read.

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
