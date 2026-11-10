"""Tests for response parsing utilities."""

from mlx_llm.parsing import extract_json, parses_affirmative


def test_extract_json_finds_json_in_prose():
    text = 'The answer is {"capital": "Paris"} I believe.'
    assert extract_json(text) == {"capital": "Paris"}


def test_extract_json_handles_complex_nested_json():
    text = 'Here is the data: {"person": {"name": "Alice", "age": 30}} as requested.'
    assert extract_json(text) == {"person": {"name": "Alice", "age": 30}}


def test_extract_json_returns_none_for_malformed_json():
    text = 'The answer is {this is not valid json} at the end.'
    assert extract_json(text) is None


def test_extract_json_returns_none_when_no_braces():
    text = "This is just plain text with no JSON."
    assert extract_json(text) is None


def test_extract_json_returns_none_for_empty_string():
    assert extract_json("") is None


def test_extract_json_handles_json_with_newlines():
    text = 'Result:\n{"key": "value",\n"nested": {"inner": true}}\nDone.'
    assert extract_json(text) == {"key": "value", "nested": {"inner": True}}


def test_parses_affirmative_returns_true_for_yes():
    assert parses_affirmative("YES") is True


def test_parses_affirmative_returns_true_for_yes_lowercase():
    assert parses_affirmative("yes") is True


def test_parses_affirmative_returns_true_for_yes_with_reason():
    assert parses_affirmative("YES, because that is correct.") is True


def test_parses_affirmative_returns_true_for_yes_with_leading_space():
    assert parses_affirmative("  YES  ") is True


def test_parses_affirmative_returns_false_for_no():
    assert parses_affirmative("NO") is False


def test_parses_affirmative_returns_false_for_no_lowercase():
    assert parses_affirmative("no") is False


def test_parses_affirmative_returns_false_for_no_with_punctuation():
    assert parses_affirmative("No.") is False


def test_parses_affirmative_returns_false_for_no_with_trailing_space():
    assert parses_affirmative("  no  ") is False


def test_parses_affirmative_returns_none_for_ambiguous_response():
    assert parses_affirmative("Maybe, I'm not sure.") is None


def test_parses_affirmative_returns_none_for_empty_string():
    assert parses_affirmative("") is None


def test_parses_affirmative_returns_none_for_unknown_prefix():
    assert parses_affirmative("I don't know.") is None
