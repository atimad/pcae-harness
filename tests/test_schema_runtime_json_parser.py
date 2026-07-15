"""Phase 136F: focused tests for the strict JSON parser (Layer-1)."""
from __future__ import annotations

import pytest

from pcae.schema_runtime import OutcomeStatus, parse_strict_json


def test_136f_valid_object_round_trips():
    result = parse_strict_json('{"a": 1, "b": [1, 2, 3], "c": null}')
    assert result.status is OutcomeStatus.VALID
    assert result.ok
    assert result.value == {"a": 1, "b": [1, 2, 3], "c": None}
    assert result.errors == ()


def test_136f_accepts_bytes_utf8():
    result = parse_strict_json('{"name": "café"}'.encode("utf-8"))
    assert result.ok
    assert result.value == {"name": "café"}


def test_136f_rejects_invalid_utf8_bytes():
    result = parse_strict_json(b"\xff\xfe{}")
    assert not result.ok
    assert result.status is OutcomeStatus.INVALID
    assert result.errors[0].code == "invalid_utf8"


def test_136f_rejects_malformed_json():
    result = parse_strict_json("{not valid json")
    assert not result.ok
    assert result.errors[0].code == "invalid_json"


def test_136f_rejects_trailing_data():
    result = parse_strict_json('{"a": 1} garbage')
    assert result.errors[0].code == "invalid_json"


def test_136f_top_level_object_required_when_requested():
    result = parse_strict_json("[1, 2, 3]", require_top_level_object=True)
    assert not result.ok
    assert result.errors[0].code == "top_level_not_object"


def test_136f_top_level_object_not_required_by_default():
    result = parse_strict_json("[1, 2, 3]")
    assert result.ok
    assert result.value == [1, 2, 3]


def test_136f_duplicate_key_top_level():
    result = parse_strict_json('{"a": 1, "b": 2, "a": 3}')
    assert not result.ok
    assert result.errors[0].code == "duplicate_key"
    assert result.errors[0].instance_path == "/a"


def test_136f_duplicate_key_nested():
    result = parse_strict_json('{"outer": {"inner": 1, "inner": 2}}')
    assert not result.ok
    assert result.errors[0].code == "duplicate_key"
    assert result.errors[0].instance_path == "/outer/inner"


def test_136f_duplicate_key_inside_array_object():
    result = parse_strict_json('{"items": [{"x": 1}, {"y": 1, "y": 2}]}')
    assert not result.ok
    assert result.errors[0].code == "duplicate_key"
    assert result.errors[0].instance_path == "/items/1/y"


def test_136f_duplicate_key_deep_nesting():
    result = parse_strict_json('{"a": {"b": {"c": [{"d": {"e": 1, "e": 2}}]}}}')
    assert not result.ok
    assert result.errors[0].instance_path == "/a/b/c/0/d/e"


def test_136f_same_looking_but_distinct_unicode_keys_are_not_duplicates():
    # "a" (U+0061) vs Cyrillic "а" (U+0430) are visually similar but distinct.
    result = parse_strict_json('{"a": 1, "а": 2}')
    assert result.ok
    assert result.value == {"a": 1, "а": 2}


def test_136f_repeated_keys_with_different_values_still_rejected():
    result = parse_strict_json('{"k": "first", "k": "second"}')
    assert not result.ok
    assert result.errors[0].code == "duplicate_key"


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_136f_rejects_non_finite_numbers(literal):
    result = parse_strict_json(f'{{"value": {literal}}}')
    assert not result.ok
    assert result.errors[0].code == "non_finite_number"
    assert result.errors[0].instance_path == "/value"


def test_136f_accepts_ordinary_floats_and_negatives():
    result = parse_strict_json('{"a": -1.5, "b": 2.0e10, "c": 0}')
    assert result.ok
    assert result.value == {"a": -1.5, "b": 2.0e10, "c": 0}


def test_136f_input_size_limit_bytes():
    payload = ("[" + "1," * 1000 + "1]").encode("utf-8")
    result = parse_strict_json(payload, max_bytes=10)
    assert not result.ok
    assert result.errors[0].code == "input_too_large"


def test_136f_input_size_limit_text():
    payload = "[" + "1," * 1000 + "1]"
    result = parse_strict_json(payload, max_bytes=10)
    assert not result.ok
    assert result.errors[0].code == "input_too_large"


def test_136f_wrong_type_raises_programmer_error():
    with pytest.raises(TypeError):
        parse_strict_json(12345)  # type: ignore[arg-type]


def test_136f_does_not_mutate_input_string():
    original = '{"a": 1}'
    parse_strict_json(original)
    assert original == '{"a": 1}'


def test_136f_deterministic_pointer_escaping():
    result = parse_strict_json('{"a/b": {"c~d": 1, "c~d": 2}}')
    assert not result.ok
    assert result.errors[0].instance_path == "/a~1b/c~0d"
