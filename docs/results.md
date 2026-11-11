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

## Frozen-model reference points

Same 144 items, as reported for the frozen models. Those runs put the teach sentences in the prompt (`in-context`) or withhold them (`no-teach`). MooreMind never sees that prose. It sees the structured assertions. The numbers sit side by side so the interface difference is visible. A higher MooreMind score is not a win at reading English.

| arm | system | learn accuracy |
| --- | --- | ---: |
| external, no decay | MooreMind `keep` | 1.000 |
| external, decay | MooreMind `fade` | 0.875 |
| in-context | qwen3:8b | 0.889 |
| in-context | qwen3:1.7b | 0.694 |
| in-context | gemma3:1b | 0.333 |
| no-teach | qwen3:8b | 0.312 |
| no-teach | qwen3:1.7b | 0.236 |
| no-teach | gemma3:1b | 0.194 |
| chance | uniform over the choices | 0.250 |
