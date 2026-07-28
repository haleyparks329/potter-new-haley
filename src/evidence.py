"""Explainable character-interaction retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Chapter, Evidence


ALIASES = {
    "Harry": ("Harry Potter", "Harry"),
    "Ron": ("Ron Weasley", "Ron"),
    "Hermione": ("Hermione Granger", "Hermione"),
}
ACTION_TERMS = (
    "said", "asked", "told", "shouted", "whispered", "looked", "went",
    "ran", "helped", "gave", "took", "followed", "saved",
)
COOPERATION_TERMS = ("together", "help", "agree", "plan", "team", "trust", "friend")
CONFLICT_TERMS = ("argue", "angry", "annoy", "hate", "fight", "insult", "upset")


@dataclass(frozen=True)
class Paragraph:
    chapter: int
    index: int
    text: str


def characters_in(text: str) -> set[str]:
    found: set[str] = set()
    for character, aliases in ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", text, re.I) for alias in aliases):
            found.add(character)
    return found


def split_paragraphs(chapter: Chapter) -> list[Paragraph]:
    raw_chunks = re.split(r"\n\s*\n+", chapter.text)
    chunks: list[str] = []
    for raw in raw_chunks:
        normalized = re.sub(r"\s+", " ", raw).strip()
        if len(normalized.split()) <= 180:
            chunks.append(normalized)
            continue
        # PDF extraction often preserves visual line wraps but loses paragraph
        # gaps. Create compact sentence windows rather than treating a page as
        # one enormous paragraph.
        sentences = re.split(
            r"(?:(?<=[.!?])|(?<=[.!?][\"'”]))\s+(?=[A-Z“\"])", normalized
        )
        window: list[str] = []
        for sentence in sentences:
            if window and len((" ".join(window + [sentence])).split()) > 120:
                chunks.append(" ".join(window))
                window = []
            window.append(sentence)
        if window:
            chunks.append(" ".join(window))
    return [
        Paragraph(chapter.number, index, chunk)
        for index, chunk in enumerate(chunks)
        if chunk.strip()
    ]


def _score(text: str, characters: set[str]) -> float:
    lower = text.lower()
    score = len(characters) * 5
    score += min(text.count('"') + text.count("“") + text.count("”"), 4)
    score += sum(1.2 for term in ACTION_TERMS if re.search(rf"\b{term}\w*\b", lower))
    score += sum(1.8 for term in COOPERATION_TERMS if re.search(rf"\b{term}\w*\b", lower))
    score += sum(1.5 for term in CONFLICT_TERMS if re.search(rf"\b{term}\w*\b", lower))
    words = len(text.split())
    if 25 <= words <= 150:
        score += 2
    elif words > 250:
        score -= 3
    return round(score, 2)


def _short_excerpt(text: str, limit: int = 70) -> str:
    words = text.split()
    if len(words) <= limit:
        return text
    return " ".join(words[:limit]).rstrip(" ,;:") + "…"


def retrieve_evidence(
    chapters: list[Chapter], chapter_numbers: list[int], limit: int = 6
) -> list[Evidence]:
    paragraphs = [
        paragraph
        for chapter in chapters if chapter.number in chapter_numbers
        for paragraph in split_paragraphs(chapter)
    ]
    candidates: list[Evidence] = []
    for index, paragraph in enumerate(paragraphs):
        explicit = characters_in(paragraph.text)
        if not explicit:
            continue
        start, end = max(0, index - 1), min(len(paragraphs), index + 2)
        context_parts = [
            item.text for item in paragraphs[start:end] if item.chapter == paragraph.chapter
        ]
        context = " ".join(context_parts)
        characters = characters_in(context)
        relevance = (
            "trio interaction" if len(characters) == 3
            else "pair interaction" if len(characters) == 2
            else "explicit character action"
        )
        candidates.append(Evidence(
            chapter=paragraph.chapter,
            characters=sorted(characters),
            excerpt=_short_excerpt(context),
            relevance=relevance,
            score=_score(context, characters),
        ))

    ranked = sorted(candidates, key=lambda item: (-item.score, item.chapter))
    selected: list[Evidence] = []
    seen: set[tuple[int, str]] = set()
    for candidate in ranked:
        signature = (candidate.chapter, " ".join(candidate.excerpt.lower().split()[:12]))
        if signature in seen:
            continue
        # Reject candidates with a large shared prefix, a sign of overlapping windows.
        tokens = set(candidate.excerpt.lower().split())
        if any(
            candidate.chapter == other.chapter
            and len(tokens & set(other.excerpt.lower().split())) / max(1, len(tokens)) > 0.75
            for other in selected
        ):
            continue
        seen.add(signature)
        selected.append(candidate)
        if len(selected) == limit:
            break
    return selected
