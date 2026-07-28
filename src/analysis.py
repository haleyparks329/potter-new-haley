"""Curated phases and optional grounded Ollama interpretation."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import asdict
from typing import Any

from .models import PHASE_IDS, RELATIONSHIP_SCALE, Chapter, Evidence, validate_analysis


PHASES = (
    {
        "id": "before_hogwarts", "label": "Before Hogwarts", "symbol": "🏠",
        "chapters": list(range(1, 6)),
        "purpose": "Establish that the trio does not yet exist.",
    },
    {
        "id": "new_classmates", "label": "New Classmates", "symbol": "🚂",
        "chapters": list(range(6, 9)),
        "purpose": "Harry and Ron connect while Hermione remains socially separate.",
    },
    {
        "id": "early_tension", "label": "Early Tension", "symbol": "📚",
        "chapters": [9],
        "purpose": "The three interact, but irritation and conflict dominate.",
    },
    {
        "id": "the_troll", "label": "The Troll", "symbol": "🧌🪄",
        "chapters": [10],
        "purpose": "Shared danger becomes the friendship's turning point.",
    },
    {
        "id": "working_as_a_team", "label": "Working as a Team", "symbol": "♟️🗝️",
        "chapters": list(range(11, 18)),
        "purpose": "The trio investigates and faces the final challenges together.",
    },
)

PROJECT = {
    "title": "The Making of a Trio",
    "book": "Harry Potter and the Sorcerer's Stone (book one)",
    "analysis_scope": "Harry, Ron, and Hermione friendship development",
    "relationship_scale": {str(k): v for k, v in RELATIONSHIP_SCALE.items()},
    "measurement_note": (
        "Relationship values are interpreted visual stages, not scientific measurements."
    ),
}

STRING_ARRAY = {"type": "array", "items": {"type": "string"}}
RELATIONSHIP_SCHEMA = {
    "type": "object",
    "properties": {
        "level": {"type": "integer", "minimum": 0, "maximum": 5},
        "label": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["level", "label", "reason"],
}
PHASE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "enum": list(PHASE_IDS)},
        "label": {"type": "string"},
        "symbol": {"type": "string"},
        "chapter_numbers": {"type": "array", "items": {"type": "integer"}},
        "friendship_stage": {"type": "string"},
        "summary": {"type": "string"},
        "change_from_previous_phase": {"type": "string"},
        "character_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "character": {"type": "string"},
                    "action": {"type": "string"},
                    "relationship_effect": {"type": "string"},
                },
                "required": ["character", "action", "relationship_effect"],
            },
        },
        "cooperation": STRING_ARRAY,
        "conflict": STRING_ARRAY,
        "relationships": {
            "type": "object",
            "properties": {pair: RELATIONSHIP_SCHEMA for pair in (
                "harry_ron", "harry_hermione", "ron_hermione"
            )},
            "required": ["harry_ron", "harry_hermione", "ron_hermione"],
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "chapter": {"type": "integer"},
                    "characters": STRING_ARRAY,
                    "excerpt": {"type": "string"},
                    "relevance": {"type": "string"},
                },
                "required": ["chapter", "characters", "excerpt", "relevance"],
            },
        },
        "limitations": STRING_ARRAY,
    },
    "required": [
        "id", "label", "symbol", "chapter_numbers", "friendship_stage",
        "summary", "change_from_previous_phase", "character_actions",
        "cooperation", "conflict", "relationships", "evidence", "limitations",
    ],
}
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "phases": {
            "type": "array", "items": PHASE_SCHEMA, "minItems": 5, "maxItems": 5
        }
    },
    "required": ["phases"],
}


def build_candidates(chapters: list[Chapter], retriever: Any) -> dict[str, list[Evidence]]:
    available = {chapter.number for chapter in chapters}
    return {
        phase["id"]: retriever(
            chapters, [number for number in phase["chapters"] if number in available]
        )
        for phase in PHASES
    }


def build_deterministic_timeline(
    candidates: dict[str, list[Evidence]],
) -> dict[str, Any]:
    """Build a validated frontend contract without interpretive model output."""
    pair_characters = {
        "harry_ron": {"Harry", "Ron"},
        "harry_hermione": {"Harry", "Hermione"},
        "ron_hermione": {"Ron", "Hermione"},
    }
    phases = []
    for phase in PHASES:
        evidence = candidates[phase["id"]]
        relationships = {}
        for pair, characters in pair_characters.items():
            co_mentions = sum(
                characters.issubset(set(item.characters)) for item in evidence
            )
            level = 2 if co_mentions else 0
            reason = (
                f"Explicit co-mention appears in {co_mentions} retrieved "
                f"candidate{'s' if co_mentions != 1 else ''}; trust and friendship "
                "require optional interpretation."
                if co_mentions
                else "No explicit co-mention appears in the retained evidence."
            )
            relationships[pair] = {
                "level": level,
                "label": RELATIONSHIP_SCALE[level],
                "reason": reason,
            }
        phases.append({
            "id": phase["id"],
            "label": phase["label"],
            "symbol": phase["symbol"],
            "chapter_numbers": phase["chapters"],
            "friendship_stage": (
                "Candidate interactions found" if evidence else "No retained interactions"
            ),
            "summary": phase["purpose"],
            "change_from_previous_phase": "",
            "character_actions": [],
            "cooperation": [],
            "conflict": [],
            "relationships": relationships,
            "evidence": [{
                "chapter": item.chapter,
                "characters": item.characters,
                "excerpt": item.excerpt,
                "relevance": item.relevance,
            } for item in evidence],
            "limitations": [
                "Deterministic retrieval only; interpretive fields are intentionally "
                "empty until optional LLM enrichment.",
                "Full pronoun and coreference resolution is outside scope.",
            ],
        })
    return validate_analysis({"project": PROJECT, "phases": phases})


def _prompt(candidates: dict[str, list[Evidence]]) -> str:
    payload = []
    for phase in PHASES:
        payload.append({
            **phase,
            "evidence": [asdict(item) for item in candidates[phase["id"]]],
        })
    contract = {
        "project": PROJECT,
        "phases": [{
            "id": "<phase id>", "label": "<label>", "symbol": "<symbol>",
            "chapter_numbers": [1], "friendship_stage": "<concise stage>",
            "summary": "<grounded summary>", "change_from_previous_phase": "<change>",
            "character_actions": [{
                "character": "Harry", "action": "<action>",
                "relationship_effect": "<effect>",
            }],
            "cooperation": ["<moment>"], "conflict": ["<moment>"],
            "relationships": {
                pair: {"level": 0, "label": "No relationship", "reason": "<reason>"}
                for pair in ("harry_ron", "harry_hermione", "ron_hermione")
            },
            "evidence": [{
                "chapter": 1, "characters": ["Harry"], "excerpt": "<max 70 words>",
                "relevance": "<why it supports the claim>",
            }],
            "limitations": ["<uncertainty>"],
        }],
    }
    return (
        "Return JSON only. Analyze friendship development using ONLY the supplied "
        "passages; do not use memory of the book, invent scenes, or infer unsupported "
        "facts. Be concise. Express uncertainty instead of guessing. Include all five "
        f"phases in this exact order: {', '.join(PHASE_IDS)}. Include all three pair "
        "relationships in every phase. Relationship levels must be integers 0-5 and "
        "labels must exactly match the supplied scale. Evidence excerpts must be copied "
        "from supplied evidence and be at most 70 words. Use empty lists where evidence "
        "does not support a category.\n\n"
        f"OUTPUT SHAPE:\n{json.dumps(contract, ensure_ascii=False)}\n\n"
        f"CURATED PHASES AND RETRIEVED EVIDENCE:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def analyze_with_ollama(
    candidates: dict[str, list[Evidence]], model: str = "llama3.1:8b",
    base_url: str = "http://127.0.0.1:11434",
) -> dict[str, Any]:
    body = json.dumps({
        "model": model,
        "prompt": _prompt(candidates),
        "stream": False,
        "format": OUTPUT_SCHEMA,
        "options": {"temperature": 0},
    }).encode()
    request = urllib.request.Request(
        f"{base_url}/api/generate", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.load(response)
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(f"Ollama request failed: {error}") from error
    try:
        analysis = json.loads(result["response"])
    except (KeyError, json.JSONDecodeError) as error:
        raise RuntimeError("Ollama did not return valid JSON") from error
    # Invariant metadata belongs to the application rather than the model.
    if isinstance(analysis, list):
        analysis = {"phases": analysis}
    if not isinstance(analysis, dict):
        raise RuntimeError("Ollama returned JSON with an invalid root")
    analysis["project"] = PROJECT
    phases = analysis.get("phases")
    if not isinstance(phases, list) and isinstance(analysis.get("analysis"), list):
        phases = analysis["analysis"]
        analysis["phases"] = phases
    if not isinstance(phases, list) and all(
        isinstance(analysis.get(phase_id), dict) for phase_id in PHASE_IDS
    ):
        phases = [
            {"id": phase_id, **analysis[phase_id]} for phase_id in PHASE_IDS
        ]
        analysis["phases"] = phases
    if isinstance(phases, list):
        phase_config = {phase["id"]: phase for phase in PHASES}
        for phase in phases:
            if isinstance(phase, dict) and phase.get("id") in phase_config:
                config = phase_config[phase["id"]]
                phase["label"] = config["label"]
                phase["symbol"] = config["symbol"]
                phase["chapter_numbers"] = config["chapters"]
    return validate_analysis(analysis)
