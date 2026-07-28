import pytest

from src.corpus import parse_chapters


def test_detects_word_and_numeric_chapter_headings():
    text = """
Book title

CHAPTER ONE

""" + "First invented paragraph. " * 12 + """

Chapter 2 - Another Day

""" + "Second invented paragraph. " * 12
    chapters = parse_chapters(text)
    assert [chapter.number for chapter in chapters] == [1, 2]
    assert chapters[1].heading == "Chapter 2: Another Day"


def test_rejects_text_without_credible_chapters():
    with pytest.raises(ValueError, match="credible chapter sequence"):
        parse_chapters("An invented story with no headings.")

