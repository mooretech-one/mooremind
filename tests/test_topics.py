"""Examples and fixtures stay off the Mooretech topic ban."""

from __future__ import annotations

import re
from pathlib import Path

_BANNED = re.compile(
    r"\b(tax|taxes|fiscal|government|governmental|parliament|minister|"
    r"municipal|council|welfare|taxpayer|administration|benefit|benefits)\b",
    re.IGNORECASE,
)
_SUFFIXES = {".py", ".md", ".json", ".txt", ".yml", ".yaml", ".toml"}
_SKIP = {"test_topics.py", "README.md", "CONTRIBUTING.md", "LICENSE"}


def test_examples_and_fixtures_avoid_banned_topics():
    root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    for folder in (root / "src", root / "tests", root / "docs"):
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in _SUFFIXES:
                continue
            if path.name in _SKIP:
                continue
            if _BANNED.search(path.read_text(encoding="utf-8")):
                offenders.append(str(path.relative_to(root)))
    assert offenders == []
