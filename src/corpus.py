"""Locate and parse a local plain-text book into chapters."""

from __future__ import annotations

import re
from pathlib import Path

from .models import Chapter


NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20,
}
HEADING_RE = re.compile(
    r"(?im)^[ \t]*(?:chapter|ch\.?)[ \t]+"
    r"(?P<number>\d{1,2}|[ivxlcdm]{1,6}|"
    + "|".join(NUMBER_WORDS)
    + r")[ \t]*(?:(?:[-:–—])[ \t]*(?P<title>[^\n]+))?[ \t]*$"
)
ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}


def find_input_file(input_dir: Path) -> Path:
    files = sorted(input_dir.glob("*.txt"), key=lambda path: path.name.lower())
    if not files:
        raise FileNotFoundError(
            f"No source text found. Place a legally obtained .txt file in {input_dir}."
        )
    return files[0]


def read_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def _number(raw: str) -> int:
    raw = raw.lower()
    if raw.isdigit():
        return int(raw)
    if raw in NUMBER_WORDS:
        return NUMBER_WORDS[raw]
    total = previous = 0
    for character in reversed(raw):
        value = ROMAN[character]
        total += -value if value < previous else value
        previous = max(previous, value)
    return total


def parse_chapters(text: str) -> list[Chapter]:
    matches = list(HEADING_RE.finditer(text))
    if len(matches) < 2:
        raise ValueError(
            "Could not detect a credible chapter sequence. Expected headings such as "
            "'CHAPTER ONE' or 'Chapter 1 - Title'."
        )

    candidates: list[Chapter] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        number = _number(match.group("number"))
        title = (match.group("title") or "").strip()
        heading = f"Chapter {number}" + (f": {title}" if title else "")
        candidates.append(Chapter(number, heading, body))

    # A contents page produces many tiny duplicate headings. Start from the
    # longest credible consecutive run whose chapters contain actual prose.
    runs: list[list[Chapter]] = []
    run: list[Chapter] = []
    for chapter in candidates:
        credible = len(chapter.text.split()) >= 20
        if credible and (not run or chapter.number == run[-1].number + 1):
            run.append(chapter)
        elif credible:
            if run:
                runs.append(run)
            run = [chapter]
        elif run:
            runs.append(run)
            run = []
    if run:
        runs.append(run)
    chapters = max(runs, key=lambda item: (len(item), sum(len(c.text) for c in item)), default=[])
    if len(chapters) < 2 or chapters[0].number not in (1, 2):
        raise ValueError(
            "Chapter headings were found, but they did not form a credible consecutive "
            "sequence with substantial text."
        )
    return chapters


def load_book(input_dir: Path) -> tuple[Path, list[Chapter]]:
    path = find_input_file(input_dir)
    return path, parse_chapters(read_text(path))

