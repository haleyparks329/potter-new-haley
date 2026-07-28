"""Load the cached friendship timeline with a safe demo fallback."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PHASE_IDS = (
    "before_hogwarts",
    "new_classmates",
    "early_tension",
    "the_troll",
    "working_as_a_team",
)
PAIR_KEYS = ("harry_ron", "harry_hermione", "ron_hermione")
GENERATE_COMMAND = "python -m scripts.analyze --no-llm"


class TimelineDataError(ValueError):
    """Raised when neither the local nor demo timeline can be loaded."""


@dataclass(frozen=True)
class TimelineResult:
    data: dict[str, Any]
    source: str
    notice: str = ""


def _read_and_validate(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise TimelineDataError(f"{path.name} is not valid JSON: {error.msg}") from error
    except OSError as error:
        raise TimelineDataError(f"Could not read {path.name}: {error}") from error

    if not isinstance(data, dict) or not isinstance(data.get("project"), dict):
        raise TimelineDataError(f"{path.name} is missing project data")
    phases = data.get("phases")
    if not isinstance(phases, list):
        raise TimelineDataError(f"{path.name} is missing its phases list")
    phase_ids = [phase.get("id") for phase in phases if isinstance(phase, dict)]
    if phase_ids != list(PHASE_IDS):
        raise TimelineDataError(f"{path.name} does not contain all five phases in order")
    for phase in phases:
        relationships = phase.get("relationships")
        if not isinstance(relationships, dict) or set(relationships) != set(PAIR_KEYS):
            raise TimelineDataError(
                f"{path.name} phase {phase['id']} is missing relationship data"
            )
        for pair in PAIR_KEYS:
            level = relationships[pair].get("level")
            label = relationships[pair].get("label")
            if type(level) is not int or not 0 <= level <= 5 or not isinstance(label, str):
                raise TimelineDataError(
                    f"{path.name} phase {phase['id']} has invalid {pair} data"
                )
    return data


def load_timeline(real_path: Path, demo_path: Path) -> TimelineResult:
    """Prefer validated real output, falling back to a validated demo fixture."""
    local_issue = ""
    if real_path.exists():
        try:
            return TimelineResult(_read_and_validate(real_path), "local")
        except TimelineDataError as error:
            local_issue = str(error)
    else:
        local_issue = f"{real_path.name} was not found"

    try:
        demo = _read_and_validate(demo_path)
    except TimelineDataError as error:
        raise TimelineDataError(
            f"{local_issue}. Demo fallback also failed: {error}. "
            f"Generate local data with: {GENERATE_COMMAND}"
        ) from error
    return TimelineResult(
        demo,
        "demo",
        f"{local_issue}. Showing demo data. Generate local data with: {GENERATE_COMMAND}",
    )


def chapter_range(numbers: list[int]) -> str:
    if not numbers:
        return "Chapters unavailable"
    if len(numbers) == 1:
        return f"Chapter {numbers[0]}"
    return f"Chapters {min(numbers)}–{max(numbers)}"


def phase_status(phase: dict[str, Any], source: str) -> str:
    if source == "demo":
        return "Demo data"
    limitations = " ".join(phase.get("limitations") or []).lower()
    return "Deterministic retrieval" if "deterministic" in limitations else "LLM-enriched"
