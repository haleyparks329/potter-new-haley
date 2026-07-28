import copy

import pytest

from src.analysis import build_deterministic_timeline
from src.models import Evidence, PHASE_IDS, RELATIONSHIP_SCALE, validate_analysis


def valid_output():
    relationship = {"level": 0, "label": RELATIONSHIP_SCALE[0], "reason": "No evidence."}
    phase = {
        "id": "", "label": "Label", "symbol": "x", "chapter_numbers": [1],
        "friendship_stage": "Stage", "summary": "Summary",
        "change_from_previous_phase": "None", "character_actions": [],
        "cooperation": [], "conflict": [],
        "relationships": {
            "harry_ron": relationship,
            "harry_hermione": relationship,
            "ron_hermione": relationship,
        },
        "evidence": [], "limitations": [],
    }
    return {
        "project": {"title": "Test"},
        "phases": [{**copy.deepcopy(phase), "id": phase_id} for phase_id in PHASE_IDS],
    }


def test_relationship_bounds_are_validated():
    output = valid_output()
    output["phases"][0]["relationships"]["harry_ron"] = {
        "level": 6, "label": "Too high", "reason": "Invalid"
    }
    with pytest.raises(ValueError, match="integer from 0 to 5"):
        validate_analysis(output)


def test_valid_contract_passes():
    assert validate_analysis(valid_output())


def test_deterministic_timeline_uses_the_frontend_contract():
    candidates = {phase_id: [] for phase_id in PHASE_IDS}
    candidates["new_classmates"] = [
        Evidence(6, ["Harry", "Ron"], "Harry and Ron spoke.", "pair interaction", 10)
    ]

    timeline = build_deterministic_timeline(candidates)

    assert validate_analysis(timeline)
    relationship = timeline["phases"][1]["relationships"]["harry_ron"]
    assert relationship["level"] == 2
    assert relationship["label"] == "Interacting"
    assert timeline["phases"][1]["evidence"][0]["chapter"] == 6
