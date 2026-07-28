"""Small dependency-free output models and validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


RELATIONSHIP_SCALE = {
    0: "No relationship",
    1: "Aware of one another",
    2: "Interacting",
    3: "Developing trust",
    4: "Established friendship",
    5: "Strong team",
}
PAIR_KEYS = ("harry_ron", "harry_hermione", "ron_hermione")
PHASE_IDS = (
    "before_hogwarts",
    "new_classmates",
    "early_tension",
    "the_troll",
    "working_as_a_team",
)


@dataclass
class Chapter:
    number: int
    heading: str
    text: str


@dataclass
class Evidence:
    chapter: int
    characters: list[str]
    excerpt: str
    relevance: str
    score: float = 0.0


@dataclass
class Relationship:
    level: int
    label: str
    reason: str


@dataclass
class CharacterAction:
    character: str
    action: str
    relationship_effect: str


@dataclass
class PhaseAnalysis:
    id: str
    label: str
    symbol: str
    chapter_numbers: list[int]
    friendship_stage: str
    summary: str
    change_from_previous_phase: str
    character_actions: list[CharacterAction]
    cooperation: list[str]
    conflict: list[str]
    relationships: dict[str, Relationship]
    evidence: list[Evidence]
    limitations: list[str] = field(default_factory=list)


def _require(value: Any, expected: type, path: str) -> None:
    if not isinstance(value, expected):
        raise ValueError(f"{path} must be {expected.__name__}")


def validate_analysis(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the frontend JSON contract, returning it unchanged."""
    _require(data, dict, "root")
    _require(data.get("project"), dict, "project")
    phases = data.get("phases")
    _require(phases, list, "phases")
    ids = [phase.get("id") for phase in phases if isinstance(phase, dict)]
    if ids != list(PHASE_IDS):
        raise ValueError(f"phases must be present in order: {', '.join(PHASE_IDS)}")

    required = {
        "id", "label", "symbol", "chapter_numbers", "friendship_stage",
        "summary", "change_from_previous_phase", "character_actions",
        "cooperation", "conflict", "relationships", "evidence", "limitations",
    }
    for index, phase in enumerate(phases):
        _require(phase, dict, f"phases[{index}]")
        missing = required - phase.keys()
        if missing:
            raise ValueError(f"phases[{index}] missing: {', '.join(sorted(missing))}")
        relationships = phase["relationships"]
        _require(relationships, dict, f"phases[{index}].relationships")
        if set(relationships) != set(PAIR_KEYS):
            raise ValueError(f"phases[{index}] must contain all three relationship pairs")
        for pair, relationship in relationships.items():
            level = relationship.get("level")
            if type(level) is not int or level not in RELATIONSHIP_SCALE:
                raise ValueError(f"{phase['id']}.{pair}.level must be an integer from 0 to 5")
            if relationship.get("label") != RELATIONSHIP_SCALE[level]:
                raise ValueError(f"{phase['id']}.{pair}.label does not match its level")
        for evidence in phase["evidence"]:
            excerpt = evidence.get("excerpt", "")
            if not isinstance(excerpt, str) or len(excerpt.split()) > 80:
                raise ValueError(f"{phase['id']} contains an evidence excerpt over 80 words")
    return data


def phase_to_dict(phase: PhaseAnalysis) -> dict[str, Any]:
    return asdict(phase)

