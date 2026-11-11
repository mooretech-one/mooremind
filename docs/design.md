# Design

MooreMind stores knowledge as atomic thoughts and can use a fact as soon as it has been taught. There is no training run and no language model. This note says what the store does, which choices are ours, and where the prototype stops.

## A thought

A thought is one relationship:

```text
[source -> relation -> target]
```

plus a weight and optional qualifiers. The qualifiers we keep are `timeframe`, `confidence`, `source` (stored as `origin`, so it is not confused with the entity the link starts from), and `scope`. Attribute values such as a colour are targets, not entities. A link target (`in`, `on`, `at`, `held_by`, `is_a`) is another entity. The display name is the id with underscores turned into spaces. We do not read the English sentence on the assertion. The sentence can be wrong and the structure still wins.

## The store

`ThoughtStore.teach` applies a list of assertions in order. That list is one episode.

Slots that cannot all be current at once:

- one current location (`in`, `on`, `at`, or `held_by`)
- one current value per attribute (`color`, `shape`, `material`, `size`, `texture`)
- one current class (`is_a`)

A new assertion for a slot takes the slot. The previous thought stays in the list with `current` false. That is the history. Asking where something is now walks the current locations. Asking where it was before, or at a timeframe, reads the direct hop only: the place recorded on that thought, not the chain through whatever held it later. A current `where` does walk the chain. `in`, `on`, and `held_by` continue. `at` stops, and it is rendered as "in the …", because that is the surface form the choices use. A cycle has no answer.

Class membership is a link. Colour lookup returns the entity's own colour if it has one. Otherwise it walks `is_a`. A nearer class beats a parent. An exception on the member beats the class. Setting the exception does not delete the class default, so another member of the class still inherits it. Specificity decides this, not weight. If the exception is later pruned, the default shows through again.

## The cycle, as we run it

The book names the cycle match, capture, compete, consolidate, prune. It does not specify the steps tightly enough to copy. This is the version in `ThoughtStore.teach`:

1. **Match.** A relationship that is already the current fact for the same source, relation, and target is the same thought.
2. **Decay, then prune.** Every other thought loses `decay` weight. A thought strictly below `prune_below` is removed. `keep` uses a decay of zero, so this step changes nothing.
3. **Capture.** A matched thought is kept and its qualifiers are refreshed. An unmatched assertion is a new thought at `initial` weight.
4. **Compete.** The new thought takes the exclusive slot. The thought that held the slot becomes history. It is not deleted.
5. **Consolidate.** A re-teach adds `reinforce`, up to `ceiling`. A later recall adds `use_reinforce` to each thought the answer actually read.
6. **Prune again.** A brand-new thought whose initial weight is already below the floor would not stick. Neither preset does that.

Confidence is stored and does not scale the weight. One mechanism is enough for this prototype.

## Weights

Both presets are `WeightPolicy` values. `MooreMind` and `KeepLearner` use `keep`. `FadeLearner` uses `fade`. The harness constructs the class with no arguments, which is why the presets are classes.

| | initial | re-teach | use | decay per later episode | prune below | ceiling |
| --- | --- | --- | --- | --- | --- | --- |
| `keep` | 1 | 0.25 | 0.25 | 0 | 0 | 1 |
| `fade` | 0.5 | 0.5 | 0.25 | 0.25 | 0.5 | 1 |

The fractions are powers of two so the sums stay exact. After `fade` teaches a fact and the learner reads it, the weight is 0.75. One later episode that does not restate it leaves 0.5, which is kept. A second such episode leaves 0.25, which is removed. That gap is the whole difference between the presets. It is not a table of item ids.

An episode is one `teach` call. The harness does not call `teach` for a pause that has no assertions, so a pause sentence by itself does not decay anything. Decay happens when a later episode teaches some other fact.

`reset` drops thoughts and names. It does not clear the store-versus-fallback counts. Those belong to the run.

## Answering

`answer` may read `question` and `choices`. It must not read `answer`, `world_state`, or `trace`. A test passes an object that raises if those fields are touched.

The question is English, and the public item has no structured query. `mooremind.query` is a closed cue list, not a parser:

- `colour` or `color` reads colour, including inheritance
- `earlier`, `before`, `previous`, or `leave` reads the previous place
- `start` or `first` reads the earliest place on the timeline
- `second`, `third`, `fourth`, `fifth` read that position (zero-based index 1, 2, 3, 4)
- `middle` reads the middle of the captured timeline
- `t1`, `t2`, and so on read that timeframe tag
- anything else reads where the entity is now

The focus is the longest stored name that appears as a word or phrase. `start` is the first place, not the previous one. A two-stop story makes those the same; a longer story does not.

If the store produces a phrase, and a choice's text matches it ignoring case, the reply is that choice's letter. That is how a known answer is reported. If no choice matches, the reply is the phrase itself. If the store has no phrase, the reply is `I don't know`. The choices are not looked at on that path, even when one of them is the same string. The learner counts `from_store` and `fell_back`. Set `MOOREMIND_ACCOUNTING` to a path and each answer rewrites a small JSON file with those totals.

## What is ours, and what is only a claim in the book

The book claims an atomic thought is the smallest reusable unit, that a relationship is itself a thought, that class membership unlocks inherited attributes, that an exception overrides a default without erasing it, that a move keeps its timeframe, and that new knowledge is available immediately and does not wipe old knowledge. The store follows those shapes.

The book also names weighting, fading, and a learning cycle, without a formula we could copy. The policy table, the decision that specificity beats weight, the decision that a direct hop is the history answer, the cue list, and the fallback string are ours.

## Limits and open questions

- There is no perception, planning, dialogue, or parser. A sentence that is not one of the cues above is treated as "where now".
- Ordinals assume the places were taught in order. A question that says "second" means the second captured place, not a search for the tag `t2`, unless the question actually contains `t2`.
- A faded hop shortens the chain instead of withholding it. The shortened phrase can be one of the wrong choices. The count still says the answer came from the store, because a phrase was produced.
- History below the prune floor is gone. A "where before" after that prune falls back.
- `fade` will forget a fact the harness still marks correct. MooreSense does not treat fading as part of the gold rule. The miss is the preset working, not a gold leak.
- We have not tried contradictory facts that arrive with different confidence and no exclusive slot. Confidence would need a rule we do not have yet.
- Names are slugs. A surface form that is not the slug with spaces, or two entities whose names overlap in a way the longest-match rule gets wrong, will focus the wrong entity or none.
