from src.evidence import characters_in, retrieve_evidence
from src.models import Chapter


def test_alias_matching_is_conservative():
    assert characters_in("Harry Potter met Ron Weasley and Hermione Granger.") == {
        "Harry", "Ron", "Hermione"
    }
    assert "Ron" not in characters_in("Mrs Weasley waved.")


def test_pair_and_trio_detection_in_compact_context():
    chapter = Chapter(
        1,
        "Chapter 1",
        (
            'Harry said, "Let us help together," and Ron agreed.\n\n'
            "Hermione joined Harry and Ron, and the three made a plan.\n\n"
            "An invented unrelated paragraph."
        ),
    )
    evidence = retrieve_evidence([chapter], [1], limit=4)
    relevances = {item.relevance for item in evidence}
    assert "trio interaction" in relevances
    assert any({"Harry", "Ron"}.issubset(item.characters) for item in evidence)

