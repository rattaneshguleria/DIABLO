"""Tests for memory extraction heuristics."""

from memory.extractor import contains_sensitive_data, extract_memories


def test_extract_name() -> None:
    results = extract_memories("Hi, my name is Alex")
    assert len(results) == 1
    assert results[0].category == "fact"
    assert results[0].key == "name"
    assert results[0].value == "Alex"


def test_extract_preference() -> None:
    results = extract_memories("I prefer Python for backend work")
    assert len(results) == 1
    assert results[0].category == "preference"


def test_extract_remember_note() -> None:
    results = extract_memories("Remember that my project is called Diablo")
    assert len(results) == 1
    assert results[0].category == "note"


def test_sensitive_data_is_ignored() -> None:
    assert contains_sensitive_data("my password is secret123")
    assert extract_memories("my password is secret123") == []
