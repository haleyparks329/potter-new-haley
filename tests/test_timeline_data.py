import json

import pytest

from src.timeline_data import TimelineDataError, chapter_range, load_timeline


def timeline_fixture():
    phases = []
    for phase_id, label in (
        ("before_hogwarts", "Before Hogwarts"),
        ("new_classmates", "New Classmates"),
        ("early_tension", "Early Tension"),
        ("the_troll", "The Troll"),
        ("working_as_a_team", "Working as a Team"),
    ):
        phases.append({
            "id": phase_id,
            "label": label,
            "relationships": {
                pair: {"level": 0, "label": "No relationship"}
                for pair in ("harry_ron", "harry_hermione", "ron_hermione")
            },
        })
    return {"project": {"title": "The Making of a Trio"}, "phases": phases}


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_real_timeline_is_preferred(tmp_path):
    real = tmp_path / "friendship_timeline.json"
    demo = tmp_path / "demo.json"
    write_json(real, timeline_fixture())
    write_json(demo, timeline_fixture())

    result = load_timeline(real, demo)

    assert result.source == "local"
    assert not result.notice


def test_missing_real_timeline_uses_demo_with_command(tmp_path):
    real = tmp_path / "friendship_timeline.json"
    demo = tmp_path / "demo.json"
    write_json(demo, timeline_fixture())

    result = load_timeline(real, demo)

    assert result.source == "demo"
    assert "python -m scripts.analyze --no-llm" in result.notice


def test_invalid_real_timeline_uses_demo(tmp_path):
    real = tmp_path / "friendship_timeline.json"
    demo = tmp_path / "demo.json"
    real.write_text("{not json", encoding="utf-8")
    write_json(demo, timeline_fixture())

    assert load_timeline(real, demo).source == "demo"


def test_missing_real_and_demo_raise_helpful_error(tmp_path):
    with pytest.raises(TimelineDataError, match="scripts.analyze --no-llm"):
        load_timeline(tmp_path / "real.json", tmp_path / "demo.json")


def test_chapter_range():
    assert chapter_range([10]) == "Chapter 10"
    assert chapter_range([11, 12, 13]) == "Chapters 11–13"
