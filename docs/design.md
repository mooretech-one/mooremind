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

## English front end

`KeepLearner` and `FadeLearner` still take structured assertions. `TextKeepLearner` and `TextFadeLearner` do not. MooreSense's external mode calls `teach` with assertion objects (`source`, `type`, `target`, `text`, `qualifiers`) and `answer` with the whole item. The text classes read `text` on each assertion, plus `question` and the choice text. They do not read `source`, `type`, `target`, `qualifiers`, `answer`, `world_state`, `trace`, `context`, or the item's `teach` list while answering. `item.id` is copied onto a trace line when `MOOREMIND_TRACE` is set. It is not used to choose the reply.

`read_sentence` splits a sentence on "and", "but", and semicolons, rewrites a cleft ("it is X that Y") to "X Y", then tries one list of patterns. A clause that matches becomes one or more store facts. A clause that does not match is counted and skipped. Nothing is invented to fill the gap. The episode still counts, so `fade` still decays.

The patterns cover location, containment, holding, a from-to move (the start is stored, then the end), class membership, colour, and "every kind is C except Name, who is D". Inverted order ("In the loft sits Nim", "Holding the pot is Tess") is the same relations with the place or the holder first. A possessive determiner is stripped to its head ("Nim's basket has the pebble" is the pebble in the basket). "Name's colour is C" is a colour fact. "Is in", "is inside", "stays", "sits", "stands", "begins", "was left", and "moves to" are stored as `in`. For a place with no further location, that phrase is the same as the harness's `at`. Colour words come from a fixed ordinary list. Anything else after a bare "is" is refused when it is not in that list.

Pronouns bind inside one `teach` call and are dropped when that call returns. "he", "she", "it", "they", "him", "her", and "them" bind to the most recent named subject. "one" binds to the most recent class. "in it" is the container idiom, not a pronoun. A pronoun with no antecedent refuses the clause. It is not given a guessed name.

A question is accepted when it contains "where", "which", "who", "whom", "colour", "color", or "hue" anywhere, not only at the start. "hue" is read as colour. The cue list then picks where-now, a previous place, an ordinal, or a colour. Any other question is `I don't know`.

Still refused:

- a telegraphic list ("First the kitchen, afterwards the hall, for Tess")
- a compressed biography ("Once in the shed, later the garden: that is Veda")
- residence, tucking, hosting, and "hands are on"
- a question with none of the cue words above ("Point to Nim")
- negation, and relative clauses other than "who is <colour>"

The bare "is <colour>" rule will also accept a long subject that merely ends in a colour word. That over-match was left in place after the one-shot measurement.

Weights are the original policies. This front end does not change them.

The public learn sentences are twenty-five skeletons. The grammar covers those skeletons, so a perfect score on that slice does not mean the front end reads open English. `tests/paraphrase_heldout.py` was the previous held-out set and is development data now. `tests/paraphrase_fresh.py` is the one-shot batch: it was committed before this widening, scored once, and not used to add a rule. After this pull request it too is development data.

## Language-model translator

The rule front end does not generalise. The fresh 60-question batch scored 0.000. The store stays the memory: inheritance, exceptions, history, multi-hop recall, and decay. A small local model is only a translator. It does not answer the question itself on that path.

`LlmKeepLearner` and `LlmFadeLearner` call an OpenAI-compatible chat endpoint with the standard library. The default base URL is `http://localhost:11434/v1` (Ollama). The model name is `MOOREMIND_LLM_MODEL`. An optional key is `MOOREMIND_LLM_API_KEY` or `OPENAI_API_KEY`. Thinking is off (`think` false, `reasoning_effort` `none`, a `/no_think` prefix). Temperature is 0, the seed defaults to 0, and the generation cap defaults to 512 tokens.

Each episode's sentences go out as one `TASK teach` call. The reply must be one JSON object, `{"assertions":[...]}`, using `in`, `on`, `at`, `held_by`, `is_a`, `color`, `shape`, `material`, `size`, or `texture`, and lowercase slugs. The question goes out as one `TASK question` call and must come back as `{"kind":...,"entity":...}` with kind `where`, `before`, `index`, `middle`, `time`, or `color`. The prompt has three short examples (a kettle on a stove, Dot moving from the larder to the courtyard and joining the pibbles, and a second-stop question). Those sentences are not MooreSense items and not rows from the paraphrase files.

Parsing is strict. A single markdown fence is accepted. Prose around a JSON object is not. Entity slugs are not case-repaired. Relation and query names are rewritten only when they are on the alias list. A bad field still rejects the whole call. An empty assertion list is a failure. Timeouts and HTTP errors are failures. Nothing is passed to the rule parser to be repaired. A failed teach stores nothing for that episode, and the episode still counts for decay, so a translator miss can erase a fact under `fade` and can also leave a wrong fact in place when a later call succeeds with a bad but valid assertion. A wrong fact stays until a later assertion replaces that slot. That is a limit: translator errors become memory.

The choices are not sent to the translator. After the store has a phrase, a matching choice letter is returned, as with the other learners.

The comparison arm asks the same model, with thinking off and the same token cap, to answer from the English directly. Its default prompt now includes the same three scenes in plain question and answer form, so the pair is even. `--baseline-prompt old` leaves those examples out and reproduces the first tower prompt. On a paraphrase story the store arm is asked every earlier question too, so a recall can reinforce a fact. The model-alone arm sees the accumulated sentences once, at the question being scored.

Three optional steps sit on the translator. They default on for `LlmKeepLearner` and `LlmFadeLearner`, and the paraphrase script can turn each one off.

- Mapping rewrites a listed relation or query name before validation (`inside` to `in`, `colour` to `color`, `owned_by` to `held_by`, plus plural and tense forms in `RELATION_ALIASES` and `QUERY_ALIASES`). The list is closed. A name that is not on it is still rejected. Each rewrite is stored on the outcome so it can be counted. Entity slugs are not rewritten, and words that would swap the two ends of a fact, such as "contains", are not on the list.
- A self-check is a second call, same model and the same temperature, seed, and thinking settings. It sees the source text and the proposed JSON and answers keep, fix, or drop. Only a keep, or a fix that itself validates, is stored.
- One retry runs only when the first reply is not valid JSON. The validator's short error is appended. It does not retry an off-vocabulary reply.

A one-sentence episode plus its question is two calls on the original path. With a valid first reply, the self-check adds one call to the teach and one to the question. The retry adds a call only when that first reply is invalid JSON, and the self-check then runs on the retried reply if it parses. Sentences that share an episode still share one teach call. These rules are general aliases and a check step. They are not written for any fresh-split sentence.

## What is ours, and what is only a claim in the book

The book claims an atomic thought is the smallest reusable unit, that a relationship is itself a thought, that class membership unlocks inherited attributes, that an exception overrides a default without erasing it, that a move keeps its timeframe, and that new knowledge is available immediately and does not wipe old knowledge. The store follows those shapes.

The book also names weighting, fading, and a learning cycle, without a formula we could copy. The policy table, the decision that specificity beats weight, the decision that a direct hop is the history answer, the cue list, and the fallback string are ours.

## Limits and open questions

- There is no perception, planning, or dialogue. The structured path has no sentence parser. The rule-based text path refuses a sentence outside its list. The translator path refuses invalid JSON instead. On the structured path, a question that is not one of the cues is treated as "where now". On the rule-based text path, that question is refused.
- Ordinals assume the places were taught in order. A question that says "second" means the second captured place, not a search for the tag `t2`, unless the question actually contains `t2`.
- A faded hop shortens the chain instead of withholding it. The shortened phrase can be one of the wrong choices. The count still says the answer came from the store, because a phrase was produced.
- History below the prune floor is gone. A "where before" after that prune falls back.
- `fade` will forget a fact the harness still marks correct. MooreSense does not treat fading as part of the gold rule. The miss is the preset working, not a gold leak.
- We have not tried contradictory facts that arrive with different confidence and no exclusive slot. Confidence would need a rule we do not have yet.
- Names are slugs. A surface form that is not the slug with spaces, or two entities whose names overlap in a way the longest-match rule gets wrong, will focus the wrong entity or none.
