"""Weight, reinforcement, decay, and pruning.

The book this project is named after says a new relationship starts at a
lower weight and may fade if it is not reused. It does not give numbers.
The policy below is ours, and both presets are plain data.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeightPolicy:
    """One mechanism: start, reinforce, decay, prune.

    ``initial`` is the weight of a relationship the first time it is taught.
    ``reinforce`` is added when the same source, relation, and target are
    taught again. ``use_reinforce`` is added when a recall reads the thought.
    ``decay`` is subtracted once per later ``teach`` call that does not
    restate that relationship. A thought is removed when its weight is
    strictly below ``prune_below``. Nothing is raised above ``ceiling``.
    """

    initial: float = 1.0
    reinforce: float = 0.25
    use_reinforce: float = 0.25
    decay: float = 0.0
    prune_below: float = 0.0
    ceiling: float = 1.0

    def __post_init__(self) -> None:
        if min(self.initial, self.reinforce, self.use_reinforce, self.decay, self.prune_below) < 0:
            raise ValueError("weights cannot be negative")
        if self.ceiling <= 0 or self.ceiling < self.initial:
            raise ValueError("ceiling must sit at or above the initial weight")


# No decay. A fact taught once is still there after later episodes.
KEEP = WeightPolicy(
    initial=1.0,
    reinforce=0.25,
    use_reinforce=0.25,
    decay=0.0,
    prune_below=0.0,
    ceiling=1.0,
)

# Low start, and one step of decay per later episode.
# The fractions are powers of two so the arithmetic stays exact.
# After a recall the weight is initial + use_reinforce (0.75).
# One quiet episode leaves 0.5, which is still kept.
# A second quiet episode leaves 0.25, which is pruned.
FADE = WeightPolicy(
    initial=0.5,
    reinforce=0.5,
    use_reinforce=0.25,
    decay=0.25,
    prune_below=0.5,
    ceiling=1.0,
)
