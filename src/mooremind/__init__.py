"""MooreMind stores atomic thoughts and learns a fact when it is taught."""

from mooremind.learner import FALLBACK, FadeLearner, KeepLearner, MooreMind
from mooremind.store import ThoughtStore
from mooremind.weights import FADE, KEEP, WeightPolicy

__version__ = "0.1.0"

__all__ = [
    "FADE",
    "FALLBACK",
    "KEEP",
    "FadeLearner",
    "KeepLearner",
    "MooreMind",
    "ThoughtStore",
    "WeightPolicy",
    "__version__",
]
