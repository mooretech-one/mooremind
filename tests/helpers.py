"""Small stand-ins for a taught assertion and a multiple-choice item."""

from __future__ import annotations


class Choice:
    def __init__(self, label: str, text: str) -> None:
        self.label = label
        self.text = text


class Item:
    """Question and choices only.

    Reading ``answer``, ``world_state``, or ``trace`` raises. A learner that
    peeks at gold fields fails the test that uses this object.
    """

    def __init__(self, question: str, choices: list[Choice] | None) -> None:
        self._question = question
        self._choices = choices

    def __getattribute__(self, name: str):
        if name in {"answer", "world_state", "trace"}:
            raise AssertionError(f"learner read {name}")
        return object.__getattribute__(self, name)

    @property
    def question(self) -> str:
        return self._question

    @property
    def choices(self) -> list[Choice] | None:
        return self._choices


def fact(
    source: str,
    relation: str,
    target: str,
    *,
    timeframe: str | None = None,
    confidence: str | None = None,
    origin: str | None = None,
    scope: str | None = None,
    text: str | None = None,
) -> dict[str, object]:
    qualifiers: dict[str, str] = {}
    if timeframe:
        qualifiers["timeframe"] = timeframe
    if confidence:
        qualifiers["confidence"] = confidence
    if origin:
        qualifiers["source"] = origin
    if scope:
        qualifiers["scope"] = scope
    return {
        "source": source,
        "type": relation,
        "target": target,
        "text": text or f"{source} {relation} {target}",
        "qualifiers": qualifiers,
    }
