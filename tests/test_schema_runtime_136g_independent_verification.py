"""Phase 136G: independent adversarial verification of Phase 136F's generic
Draft 2020-12 validation-engine, strict-parser, loader, and registry
infrastructure.

These tests deliberately do NOT reuse 136F's own fixtures or duplicate its
own test assertions. Every fixture schema here is new, and every attack is
constructed independently against the public API in
``pcae.schema_runtime``. This module attacks: Draft 2020-12 feature
coverage not exercised by 136F (prefixItems, contains/minContains/
maxContains, dependentRequired, $anchor references, Boolean schemas);
strict-parser edge cases (leading zeros, exponents, negative zero, BOM,
NUL bytes, lone surrogates, multiple top-level values, empty/whitespace
input); the nesting-depth defect discovered and repaired in this phase;
resource-limit boundaries; loader containment beyond 136F's own cases;
registry no-network behavior against additional transport primitives;
determinism across insertion order and hash seeds; duplicate-$id
byte-identical rejection; shape-validation API robustness against
non-mapping/self-referential input; dead/unreachable error-vocabulary
codes; and filesystem non-mutation.
"""
from __future__ import annotations

import copy
import hashlib
import os
import socket
import sys
from pathlib import Path

import pytest

from pcae.schema_runtime import (
    DEFAULT_MAX_NESTING_DEPTH,
    DEFAULT_MAX_RECORD_DEPTH,
    OutcomeStatus,
    SchemaRegistryError,
    SchemaResourceError,
    build_offline_registry,
    parse_strict_json,
    validate_record_shape,
)
from pcae.schema_runtime.loader import load_schema_resource

FIXTURES_136G = Path(__file__).parent / "fixtures" / "schema_runtime_136g"
FIXTURES_136F = Path(__file__).parent / "fixtures" / "schema_runtime"

FEATURE_MATRIX_ID = (
    "https://pcae.test/schema_runtime_136g/conformance_package/feature-matrix.schema.json"
)


def _feature_registry():
    return build_offline_registry(FIXTURES_136G / "conformance_package")


# ---------------------------------------------------------------------------
# 1. Draft 2020-12 conformance attack (fresh features, fresh fixture)
# ---------------------------------------------------------------------------


def test_136g_prefixitems_and_items_false_enforced():
    registry = _feature_registry()
    ok = {"tuple": ["label", 5]}
    assert validate_record_shape(ok, schema_id=FEATURE_MATRIX_ID, registry=registry).ok

    extra = {"tuple": ["label", 5, "extra"]}
    result = validate_record_shape(extra, schema_id=FEATURE_MATRIX_ID, registry=registry)
    assert result.status is OutcomeStatus.INVALID


def test_136g_anchor_reference_resolves_and_enforces_constraint():
    registry = _feature_registry()
    negative = {"tuple": ["label", -1]}
    result = validate_record_shape(negative, schema_id=FEATURE_MATRIX_ID, registry=registry)
    assert result.status is OutcomeStatus.INVALID


def test_136g_contains_mincontains_maxcontains():
    registry = _feature_registry()
    missing_tag = {"tuple": ["x", 1], "tagged": ["nope"]}
    assert validate_record_shape(missing_tag, schema_id=FEATURE_MATRIX_ID, registry=registry).status is (
        OutcomeStatus.INVALID
    )

    exactly_one = {"tuple": ["x", 1], "tagged": ["required-tag", "other"]}
    assert validate_record_shape(exactly_one, schema_id=FEATURE_MATRIX_ID, registry=registry).ok

    too_many = {"tuple": ["x", 1], "tagged": ["required-tag"] * 3}
    result = validate_record_shape(too_many, schema_id=FEATURE_MATRIX_ID, registry=registry)
    assert result.status is OutcomeStatus.INVALID


def test_136g_dependentrequired_enforced():
    registry = _feature_registry()
    missing_escort = {"tuple": ["x", 1], "conditionalGroup": {"partner": "p"}}
    result = validate_record_shape(missing_escort, schema_id=FEATURE_MATRIX_ID, registry=registry)
    assert result.status is OutcomeStatus.INVALID

    with_escort = {"tuple": ["x", 1], "conditionalGroup": {"partner": "p", "escort": "e"}}
    assert validate_record_shape(with_escort, schema_id=FEATURE_MATRIX_ID, registry=registry).ok


def test_136g_boolean_schema_false_rejects_any_value():
    registry = _feature_registry()
    blocked = {"tuple": ["x", 1], "blockedField": "anything-at-all"}
    result = validate_record_shape(blocked, schema_id=FEATURE_MATRIX_ID, registry=registry)
    assert result.status is OutcomeStatus.INVALID


def test_136g_boolean_schema_true_accepts_any_value():
    registry = _feature_registry()
    allowed = {"tuple": ["x", 1], "always": {"anything": ["goes", 1, None]}}
    assert validate_record_shape(allowed, schema_id=FEATURE_MATRIX_ID, registry=registry).ok


def test_136g_selected_validator_is_explicitly_draft202012_not_inferred():
    # The validator class is hard-selected in source (validation.py imports
    # Draft202012Validator directly); it must not be chosen dynamically from
    # a record- or schema-supplied $schema value at validation time.
    import inspect

    import pcae.schema_runtime.validation as validation_module

    source = inspect.getsource(validation_module)
    assert "Draft202012Validator" in source
    assert "validator_for(" not in source, (
        "validation.py must not dynamically select a validator class via "
        "jsonschema.validators.validator_for() based on untrusted schema content"
    )


def test_136g_schema_with_unsupported_dialect_declared_via_missing_field_rejected():
    # A schema resource with $schema entirely absent (distinct from 136F's
    # "wrong dialect value" fixture) must also be rejected, not silently
    # treated as Draft 2020-12 by default.
    with pytest.raises(SchemaResourceError, match="Draft 2020-12 dialect"):
        load_schema_resource(
            FIXTURES_136G / "unsupported_dialect_no_schema_field" / "no_schema_field.schema.json",
            root=FIXTURES_136G / "unsupported_dialect_no_schema_field",
        )


def test_136g_invalid_schema_itself_rejected_by_meta_schema_check(tmp_path: Path):
    # A schema whose own structure violates the Draft 2020-12 meta-schema
    # (a "required" keyword that is a string, not an array) must be
    # rejected at load time, not accepted and only fail at validation time.
    # Uses pytest's tmp_path (already a fully resolved path), consistent
    # with every other containment test in this suite -- an unresolved
    # symlinked root (e.g. raw tempfile.TemporaryDirectory() on macOS,
    # where /var is a symlink to /private/var) is a separate, disclosed
    # 136G finding (see test_136g_unresolved_symlinked_root_causes_false_rejection).
    from pcae.schema_runtime import SchemaResourceError as _SRE

    root = tmp_path / "root"
    root.mkdir()
    (root / "bad.schema.json").write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", '
        '"$id": "https://pcae.test/136g/bad", "required": "not-an-array"}',
        encoding="utf-8",
    )
    with pytest.raises(_SRE, match="Draft 2020-12 schema checking"):
        load_schema_resource(root / "bad.schema.json", root=root)


def test_136g_unresolved_symlinked_root_causes_false_rejection_not_a_security_hole():
    # 136G finding (non-blocking, disclosed): if a caller passes an
    # *unresolved* root that itself sits behind a filesystem symlink (e.g.
    # macOS's /var -> /private/var, which affects the default temp
    # directory), a perfectly legitimate same-root candidate path can be
    # rejected as "escapes trusted root", because containment compares a
    # lexically-normalized (non-symlink-following) candidate against a
    # fully symlink-resolved root. This is fail-closed (safe direction: a
    # legitimate load is refused, never an illegitimate one accepted) but
    # is a real usability surprise for callers who do not pre-resolve their
    # trusted root before calling. Documented, not fixed, since "always
    # fail closed on ambiguity" is the correct posture for this loader.
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        unresolved_root = Path(td)
        if unresolved_root.resolve() == unresolved_root:
            pytest.skip("this platform's temp directory is not behind a symlink; finding not reproducible here")
        (unresolved_root / "ok.schema.json").write_text(
            '{"$schema": "https://json-schema.org/draft/2020-12/schema", '
            '"$id": "https://pcae.test/136g/symlinked-root", "type": "object"}',
            encoding="utf-8",
        )
        with pytest.raises(SchemaResourceError, match="escapes trusted root"):
            load_schema_resource(unresolved_root / "ok.schema.json", root=unresolved_root)
        # Pre-resolving the root (the documented workaround) succeeds.
        loaded = load_schema_resource(
            unresolved_root.resolve() / "ok.schema.json", root=unresolved_root.resolve()
        )
        assert loaded.info.schema_id == "https://pcae.test/136g/symlinked-root"


# ---------------------------------------------------------------------------
# 2. Strict parser attack (independent edge cases beyond 136F's own suite)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        "",
        "   ",
        "\t\n\r  ",
    ],
)
def test_136g_empty_and_whitespace_only_input_rejected(payload):
    result = parse_strict_json(payload)
    assert not result.ok
    assert result.errors[0].code == "invalid_json"


def test_136g_top_level_scalar_accepted_when_object_not_required():
    for payload in ['"just a string"', "42", "true", "null"]:
        result = parse_strict_json(payload)
        assert result.ok, payload


def test_136g_multiple_top_level_values_rejected():
    result = parse_strict_json("{} {}")
    assert not result.ok
    assert result.errors[0].code == "invalid_json"


def test_136g_leading_zero_rejected():
    result = parse_strict_json("01")
    assert not result.ok
    assert result.errors[0].code == "invalid_json"


def test_136g_negative_zero_accepted_as_ordinary_number():
    result = parse_strict_json("-0")
    assert result.ok
    assert result.value == 0


def test_136g_exponent_forms_accepted():
    for payload in ["1e10", "1E10", "1e+10", "1e-10", "1.5e3"]:
        result = parse_strict_json(payload)
        assert result.ok, payload


def test_136g_very_large_integer_accepted_without_overflow():
    # Python ints are arbitrary precision; this must not raise or silently
    # truncate.
    huge = "9" * 400
    result = parse_strict_json(huge)
    assert result.ok
    assert result.value == int(huge)


def test_136g_utf8_bom_is_not_silently_stripped():
    payload = ("﻿{}").encode("utf-8")
    result = parse_strict_json(payload)
    # A leading BOM is not valid JSON per RFC 8259; the parser must not
    # silently accept it as if the BOM were absent.
    assert not result.ok
    assert result.errors[0].code == "invalid_json"


def test_136g_embedded_nul_in_string_is_preserved_not_truncated():
    payload = '{"a": "x\\u0000y"}'
    result = parse_strict_json(payload)
    assert result.ok
    assert result.value["a"] == "x\x00y"
    assert len(result.value["a"]) == 3


def test_136g_unescaped_control_character_in_string_rejected():
    # A literal (unescaped) NUL byte inside a JSON string is not valid per
    # RFC 8259 (control characters must be escaped).
    payload = '{"a": "x\x00y"}'
    result = parse_strict_json(payload)
    assert not result.ok
    assert result.errors[0].code == "invalid_json"


def test_136g_lone_high_surrogate_is_preserved_as_lone_surrogate():
    # \ud800 with no following low surrogate: the parser must not crash and
    # must not silently drop or replace the code unit.
    payload = '{"a": "\\ud800"}'
    result = parse_strict_json(payload)
    assert result.ok
    assert result.value["a"] == "\ud800"


def test_136g_malformed_unicode_escape_rejected():
    for payload in ['{"a": "\\u12"}', '{"a": "\\uZZZZ"}', '{"a": "\\u"}']:
        result = parse_strict_json(payload)
        assert not result.ok, payload
        assert result.errors[0].code == "invalid_json"


def test_136g_invalid_backslash_escape_rejected():
    result = parse_strict_json('{"a": "\\q"}')
    assert not result.ok
    assert result.errors[0].code == "invalid_json"


def test_136g_invalid_utf8_continuation_byte_rejected():
    result = parse_strict_json(b'{"a": "\x80\x80"}')
    assert not result.ok
    assert result.errors[0].code == "invalid_utf8"


def test_136g_duplicate_key_precedes_schema_validation_ordering():
    # Layer-1 (parsing) must reject a duplicate key before any Layer-2
    # (schema) concern is even reachable -- there is no code path where a
    # document with a duplicate key ever reaches validate_record_shape.
    result = parse_strict_json('{"a": 1, "a": 2}')
    assert result.status is OutcomeStatus.INVALID
    assert result.value is None  # no partially-parsed value is exposed


def test_136g_error_messages_do_not_echo_full_secret_like_values_unbounded():
    # A very long "secret-like" string value inside otherwise-invalid JSON
    # should not cause unbounded-size error messages; this is a documentation
    # test of current behavior (message length is not artificially capped
    # by this parser), included so a future silent regression to unbounded
    # message growth is visible in the fixture diff, not merely assumed.
    long_value = "s" * 10000
    payload = '{"a": "%s", "a": "dup"}' % long_value
    result = parse_strict_json(payload)
    assert not result.ok
    assert result.errors[0].code == "duplicate_key"
    # message must not itself contain the 10000-char secret value (only the
    # short duplicated key name, not the value, is included in the message)
    assert long_value not in result.errors[0].message


# ---------------------------------------------------------------------------
# 3. Nesting-depth attack (136G-discovered defect + regression proof)
# ---------------------------------------------------------------------------


def test_136g_deeply_nested_array_fails_closed_instead_of_crashing():
    # Phase 136G finding: prior to this phase's repair, sufficiently deep
    # (but byte-size-tiny) nested JSON raised an uncaught RecursionError,
    # violating parse_strict_json's own documented "never raises on
    # ordinary invalid input" contract. This is the regression test for
    # the repair (DEFAULT_MAX_NESTING_DEPTH in limits.py).
    depth = 5000
    payload = "[" * depth + "1" + "]" * depth
    result = parse_strict_json(payload)
    assert result.status is OutcomeStatus.INVALID
    assert result.errors[0].code == "invalid_json"
    assert "nesting depth" in result.errors[0].message


def test_136g_deeply_nested_object_fails_closed_instead_of_crashing():
    depth = 5000
    payload = '{"a":' * depth + "1" + "}" * depth
    result = parse_strict_json(payload)
    assert result.status is OutcomeStatus.INVALID
    assert result.errors[0].code == "invalid_json"


def test_136g_nesting_just_under_limit_still_accepted():
    depth = DEFAULT_MAX_NESTING_DEPTH - 10
    payload = "[" * depth + "1" + "]" * depth
    result = parse_strict_json(payload)
    assert result.ok


def test_136g_max_depth_is_configurable_per_call():
    payload = "[" * 50 + "1" + "]" * 50
    result = parse_strict_json(payload, max_depth=10)
    assert not result.ok
    assert result.errors[0].code == "invalid_json"


def _self_referential_array_registry(tmp_path: Path):
    root = tmp_path / "recursive_schema_root"
    root.mkdir()
    (root / "r.schema.json").write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", '
        '"$id": "https://pcae.test/136g/self-referential-array", '
        '"type": "array", "items": {"$ref": "#"}}',
        encoding="utf-8",
    )
    return build_offline_registry(root)


def test_136g_deeply_nested_record_against_recursive_schema_fails_closed_instead_of_crashing(
    tmp_path: Path,
):
    # 136G finding: Draft202012Validator.iter_errors() recurses once per
    # nesting level of a *self-referential* schema traversing a deeply
    # nested record, and can raise an uncaught RecursionError at a
    # materially shallower record depth than parse_strict_json's own
    # nesting-depth limit alone would suggest is safe. This is the
    # regression test for the validate_record_shape() repair
    # (DEFAULT_MAX_RECORD_DEPTH / _exceeds_max_depth in validation.py).
    registry = _self_referential_array_registry(tmp_path)
    depth = 5000
    value: list = []
    for _ in range(depth):
        value = [value]
    result = validate_record_shape(value, schema_id="https://pcae.test/136g/self-referential-array", registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert result.issues[0].code == "internal_validation_error"


def test_136g_record_depth_just_under_limit_still_validated(tmp_path: Path):
    registry = _self_referential_array_registry(tmp_path)
    depth = DEFAULT_MAX_RECORD_DEPTH - 10
    value: list = []
    for _ in range(depth):
        value = [value]
    result = validate_record_shape(value, schema_id="https://pcae.test/136g/self-referential-array", registry=registry)
    assert result.status is OutcomeStatus.VALID


def test_136g_record_depth_guard_is_configurable_per_call(tmp_path: Path):
    registry = _self_referential_array_registry(tmp_path)
    value: list = []
    for _ in range(50):
        value = [value]
    result = validate_record_shape(
        value, schema_id="https://pcae.test/136g/self-referential-array", registry=registry, max_record_depth=10
    )
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert result.issues[0].code == "internal_validation_error"


def test_136g_record_depth_guard_uses_iterative_not_recursive_walk_and_survives_extreme_depth(
    tmp_path: Path,
):
    # The depth guard itself must not be vulnerable to the same class of
    # attack it defends against: even an extremely deep record (well beyond
    # what any recursive Python walk could handle) must be rejected
    # cleanly, not crash while being *measured*.
    registry = _self_referential_array_registry(tmp_path)
    depth = 200_000
    value: list = []
    for _ in range(depth):
        value = [value]
    result = validate_record_shape(value, schema_id="https://pcae.test/136g/self-referential-array", registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert result.issues[0].code == "internal_validation_error"


# ---------------------------------------------------------------------------
# 4. Resource-limit attack
# ---------------------------------------------------------------------------


def test_136g_input_exactly_at_byte_limit_accepted():
    payload = "1"
    encoded = payload.encode("utf-8")
    result = parse_strict_json(encoded, max_bytes=len(encoded))
    assert result.ok


def test_136g_input_one_byte_over_limit_rejected():
    payload = "12"
    encoded = payload.encode("utf-8")
    result = parse_strict_json(encoded, max_bytes=len(encoded) - 1)
    assert not result.ok
    assert result.errors[0].code == "input_too_large"


def test_136g_multibyte_utf8_near_limit_counts_bytes_not_codepoints():
    # A JSON string value containing a single multibyte character (the
    # quoted 4-byte-in-UTF-8 emoji "🎯": 1 code point, 4 UTF-8 bytes) must
    # be measured in bytes, not code points, against max_bytes -- the
    # str-input and bytes-input call paths must agree at the boundary.
    text = '"🎯"'  # valid JSON string literal: quote + 4-byte codepoint + quote
    encoded = text.encode("utf-8")
    assert len(encoded) == 6  # 2 quote bytes + 4 UTF-8 bytes for U+1F3AF
    assert len(text) == 3  # 2 quote chars + 1 Python str code point (astral, no surrogate pair here)

    # one byte under the true UTF-8 length must reject on both call paths
    result_text = parse_strict_json(text, max_bytes=len(encoded) - 1)
    assert not result_text.ok
    assert result_text.errors[0].code == "input_too_large"
    result_bytes = parse_strict_json(encoded, max_bytes=len(encoded) - 1)
    assert not result_bytes.ok
    assert result_bytes.errors[0].code == "input_too_large"

    # both accept at the true byte length
    assert parse_strict_json(text, max_bytes=len(encoded)).ok
    assert parse_strict_json(encoded, max_bytes=len(encoded)).ok


def test_136g_max_issues_zero_returns_no_issues_but_marks_invalid():
    registry = _feature_registry()
    record = {"blockedField": "x"}  # missing required "tuple" AND extra unknown field rejected by additionalProperties
    result = validate_record_shape(record, schema_id=FEATURE_MATRIX_ID, registry=registry, max_issues=0)
    assert result.status is OutcomeStatus.INVALID
    assert result.issues == ()


def test_136g_max_issues_one_returns_exactly_one():
    registry = _feature_registry()
    record = {"blockedField": "x", "always": True}
    result = validate_record_shape(record, schema_id=FEATURE_MATRIX_ID, registry=registry, max_issues=1)
    assert len(result.issues) == 1


def test_136g_excessive_max_issues_does_not_error():
    registry = _feature_registry()
    record = {"blockedField": "x"}
    result = validate_record_shape(record, schema_id=FEATURE_MATRIX_ID, registry=registry, max_issues=1_000_000)
    assert result.status is OutcomeStatus.INVALID


def test_136g_registry_resource_count_limit_bypass_attempt_via_multiple_roots(tmp_path: Path):
    # Confirm the max_resources ceiling is enforced across the *sum* of
    # multiple roots, not merely per-root (a caller cannot bypass the limit
    # by splitting resources across several trusted roots).
    root_a = tmp_path / "a"
    root_a.mkdir()
    root_b = tmp_path / "b"
    root_b.mkdir()
    for i in range(3):
        (root_a / f"s{i}.schema.json").write_text(
            '{"$schema": "https://json-schema.org/draft/2020-12/schema", '
            '"$id": "https://pcae.test/136g/limit-a-%d", "type": "object"}' % i,
            encoding="utf-8",
        )
    for i in range(3):
        (root_b / f"s{i}.schema.json").write_text(
            '{"$schema": "https://json-schema.org/draft/2020-12/schema", '
            '"$id": "https://pcae.test/136g/limit-b-%d", "type": "object"}' % i,
            encoding="utf-8",
        )
    with pytest.raises(SchemaRegistryError, match="exceeding the configured maximum"):
        build_offline_registry(root_a, root_b, max_resources=5)


# ---------------------------------------------------------------------------
# 5. Loader containment attack
# ---------------------------------------------------------------------------


def test_136g_empty_relative_path_rejected_or_contained(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    from pcae.schema_runtime import SchemaResourceNotFoundError

    with pytest.raises((SchemaResourceError, SchemaResourceNotFoundError, IsADirectoryError, FileNotFoundError)):
        load_schema_resource(Path(""), root=root)


def test_136g_current_directory_relative_path_is_contained(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    good = root / "ok.schema.json"
    good.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://pcae.test/136g/ok", '
        '"type": "object"}',
        encoding="utf-8",
    )
    loaded = load_schema_resource(Path("./ok.schema.json"), root=root)
    assert loaded.info.schema_id == "https://pcae.test/136g/ok"


def test_136g_repeated_traversal_sequences_rejected(tmp_path: Path):
    root = tmp_path / "nested" / "root"
    root.mkdir(parents=True)
    secret = tmp_path / "secret.schema.json"
    secret.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://pcae.test/136g/secret", '
        '"type": "object"}',
        encoding="utf-8",
    )
    with pytest.raises(SchemaResourceError, match="escapes trusted root"):
        load_schema_resource(Path("../../secret.schema.json"), root=root)


def test_136g_hard_link_inside_root_is_treated_as_ordinary_contained_file(tmp_path: Path):
    # Documents current, deliberate behavior: a hard link (not a symlink)
    # placed inside the trusted root is indistinguishable from an ordinary
    # file, because containment is a trust boundary on the *root directory*
    # itself (assumed to be under the caller's control), not a defense
    # against an attacker who can already write into the trusted root. This
    # is a documented assumption (136G finding), not a defect: the loader's
    # symlink defenses guard against a *link* redirecting outside an
    # otherwise-trusted root, not against a compromised root.
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.schema.json"
    outside.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://pcae.test/136g/hardlink", '
        '"type": "object"}',
        encoding="utf-8",
    )
    linked = root / "linked.schema.json"
    try:
        os.link(outside, linked)
    except OSError:
        pytest.skip("hard links unsupported across this filesystem boundary")
    loaded = load_schema_resource(linked, root=root)
    assert loaded.info.schema_id == "https://pcae.test/136g/hardlink"


def test_136g_replacing_resource_content_between_discovery_and_read_is_read_fresh(tmp_path: Path):
    # discover_schema_files() only enumerates paths; content is read fresh
    # by load_schema_resource() at call time, not cached from discovery.
    # This test proves the two-step API does not silently serve stale
    # content, though it cannot eliminate true concurrent TOCTOU
    # replacement (documented as a residual risk, not exploitable through
    # this synchronous API without a second execution thread).
    from pcae.schema_runtime.loader import discover_schema_files

    root = tmp_path / "root"
    root.mkdir()
    target = root / "s.schema.json"
    target.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://pcae.test/136g/v1", '
        '"type": "object"}',
        encoding="utf-8",
    )
    (discovered,) = discover_schema_files(root)
    target.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://pcae.test/136g/v2", '
        '"type": "object"}',
        encoding="utf-8",
    )
    loaded = load_schema_resource(discovered, root=root)
    assert loaded.info.schema_id == "https://pcae.test/136g/v2"


# ---------------------------------------------------------------------------
# 6. Registry no-network attack (additional transport primitives)
# ---------------------------------------------------------------------------


def test_136g_registry_refuses_various_unregistered_uri_schemes_without_any_socket_call(
    monkeypatch: pytest.MonkeyPatch,
):
    registry = build_offline_registry(FIXTURES_136G / "conformance_package")

    calls: list[str] = []

    def _forbidden(*args, **kwargs):
        calls.append("blocked")
        raise AssertionError("network primitive invoked")

    monkeypatch.setattr(socket, "socket", _forbidden)
    monkeypatch.setattr(socket, "create_connection", _forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", _forbidden)

    for uri in (
        "https://example.com/schema.json",
        "http://example.com/schema.json",
        "file:///etc/passwd",
        "data:application/json,{}",
        "ftp://example.com/schema.json",
        "custom-scheme://foo/bar",
        FEATURE_MATRIX_ID + "-does-not-exist",
    ):
        with pytest.raises(Exception):
            registry.referencing_registry.get_or_retrieve(uri)

    assert calls == []


def test_136g_urllib_not_imported_transitively_during_validation(monkeypatch: pytest.MonkeyPatch):
    # Blocks urllib.request.urlopen directly (in case some transitive path
    # attempted an HTTP(S) fetch through it rather than raw sockets).
    import urllib.request

    def _forbidden(*args, **kwargs):
        raise AssertionError("urllib.request.urlopen invoked during validation")

    monkeypatch.setattr(urllib.request, "urlopen", _forbidden)

    registry = build_offline_registry(FIXTURES_136G / "conformance_package")
    result = validate_record_shape({"tuple": ["x", 1]}, schema_id=FEATURE_MATRIX_ID, registry=registry)
    assert result.ok


# ---------------------------------------------------------------------------
# 7. Registry determinism attack
# ---------------------------------------------------------------------------


def test_136g_registry_schema_ids_stable_regardless_of_root_insertion_order(tmp_path: Path):
    root_a = tmp_path / "a"
    root_a.mkdir()
    root_b = tmp_path / "b"
    root_b.mkdir()
    (root_a / "one.schema.json").write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://pcae.test/136g/one", '
        '"type": "object"}',
        encoding="utf-8",
    )
    (root_b / "two.schema.json").write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://pcae.test/136g/two", '
        '"type": "object"}',
        encoding="utf-8",
    )
    forward = build_offline_registry(root_a, root_b)
    backward = build_offline_registry(root_b, root_a)
    assert forward.schema_ids == backward.schema_ids


def test_136g_duplicate_id_byte_identical_across_roots_still_rejected(tmp_path: Path):
    # Per the phase brief: "Duplicate IDs must fail closed even when
    # contents match ... Prefer rejection."
    root_a = tmp_path / "a"
    root_a.mkdir()
    root_b = tmp_path / "b"
    root_b.mkdir()
    identical_content = (
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", '
        '"$id": "https://pcae.test/136g/dup-identical", "type": "object"}'
    )
    (root_a / "x.schema.json").write_text(identical_content, encoding="utf-8")
    (root_b / "y.schema.json").write_text(identical_content, encoding="utf-8")
    assert hashlib.sha256((root_a / "x.schema.json").read_bytes()).digest() == hashlib.sha256(
        (root_b / "y.schema.json").read_bytes()
    ).digest()
    with pytest.raises(SchemaRegistryError, match="Duplicate \\$id"):
        build_offline_registry(root_a, root_b)


# ---------------------------------------------------------------------------
# 8. Shape-validation API attack
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_record", [[1, 2, 3], "a string", 12345, None, True, 3.14])
def test_136g_non_mapping_input_fails_closed_not_raises(bad_record):
    registry = _feature_registry()
    result = validate_record_shape(bad_record, schema_id=FEATURE_MATRIX_ID, registry=registry)
    assert result.status is OutcomeStatus.INVALID


def test_136g_self_referential_mapping_does_not_crash_validator():
    registry = _feature_registry()
    record: dict = {"tuple": ["x", 1]}
    record["cycle"] = record  # a true cycle: infinitely "deep" by construction
    # A genuine self-reference is, correctly, indistinguishable from
    # unbounded depth: the iterative depth guard (added by this phase's
    # record-depth repair) detects it and fails closed as
    # INFRASTRUCTURE_FAILURE without ever calling the underlying validator
    # or looping forever. This must never hang, never raise RecursionError,
    # and never report VALID.
    result = validate_record_shape(record, schema_id=FEATURE_MATRIX_ID, registry=registry)
    assert result.status is not OutcomeStatus.VALID
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert result.issues[0].code == "internal_validation_error"


def test_136g_unknown_schema_id_never_raises():
    registry = _feature_registry()
    result = validate_record_shape({}, schema_id="https://pcae.test/136g/totally-unknown", registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert result.issues[0].code == "unknown_schema"


def test_136g_record_is_never_mutated_by_validation():
    registry = _feature_registry()
    record = {"tuple": ["x", 1], "extra_unexpected_field": True}
    before = copy.deepcopy(record)
    validate_record_shape(record, schema_id=FEATURE_MATRIX_ID, registry=registry)
    assert record == before


def test_136g_issue_ordering_stable_across_ten_repeated_calls():
    registry = _feature_registry()
    record = {"blockedField": "x", "tagged": ["nope"], "conditionalGroup": {"partner": "p"}}
    runs = [
        tuple((i.code, i.instance_path) for i in validate_record_shape(
            record, schema_id=FEATURE_MATRIX_ID, registry=registry
        ).issues)
        for _ in range(10)
    ]
    assert len(set(runs)) == 1


# ---------------------------------------------------------------------------
# 9. Error vocabulary verification -- dead-code disclosure
# ---------------------------------------------------------------------------


def test_136g_discloses_unreachable_error_vocabulary_codes():
    # 136G finding (non-blocking, disclosed): two codes declared in the
    # frozen ERROR_CODES set are never actually attached to any
    # ValidationIssue produced by the current implementation:
    # "unsupported_schema_version" and "unsupported_dialect". Loader-level
    # dialect/version rejection currently surfaces as a plain
    # SchemaResourceError exception (still fail-closed), not as a
    # structured ValidationIssue carrying one of these codes.
    # "internal_validation_error" -- also originally unreachable -- became
    # reachable as a side effect of this phase's own record-depth-guard
    # repair in validate_record_shape() (validation.py), which now uses it
    # to report a record rejected for exceeding DEFAULT_MAX_RECORD_DEPTH.
    # This test pins the current fact so a future silent change in either
    # direction (a code becoming reachable, or additional codes becoming
    # unreachable) is visible in the test diff.
    from pcae.schema_runtime.errors import ERROR_CODES

    import pcae.schema_runtime as schema_runtime_pkg

    src_dir = Path(schema_runtime_pkg.__file__).parent
    # errors.py itself only *declares* the vocabulary; scan every other
    # source file's raw text for each code appearing as a string literal
    # anywhere a ValidationIssue/_StrictJsonError could plausibly carry it.
    codes_seen: set[str] = set()
    for path in src_dir.glob("*.py"):
        if path.name == "errors.py":
            continue
        text = path.read_text(encoding="utf-8")
        for code in ERROR_CODES:
            if f'"{code}"' in text or f"'{code}'" in text:
                codes_seen.add(code)

    unreachable = ERROR_CODES - codes_seen
    expected_unreachable = {"unsupported_schema_version", "unsupported_dialect"}
    assert unreachable == expected_unreachable, (
        f"Unreachable error-code set changed (now {unreachable!r}); update this test and "
        "the 136G verification report's error-vocabulary finding to match."
    )


# ---------------------------------------------------------------------------
# 10. No-authority / no-execution: dynamic-import defeat attempt
# ---------------------------------------------------------------------------


def test_136g_no_dynamic_import_mechanism_exists_to_defeat_static_ast_scan():
    # 136F's own doc flags this as an open independent-verification item:
    # "verify the AST/text-scan proofs ... cannot be defeated by dynamic
    # imports (importlib.import_module with a computed string) that a
    # static scan would miss." Confirm no such mechanism exists at all --
    # not merely that today's computed string doesn't currently resolve to
    # something forbidden.
    import pcae.schema_runtime as schema_runtime_pkg
    import pcae.schema_resources as schema_resources_pkg

    forbidden_dynamic_markers = ("importlib.import_module", "__import__(", "getattr(sys.modules", "exec(", "eval(")
    for package in (schema_runtime_pkg, schema_resources_pkg):
        src_dir = Path(package.__file__).parent
        for path in src_dir.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for marker in forbidden_dynamic_markers:
                assert marker not in text, f"{path} contains dynamic-execution marker {marker!r}"


def test_136g_no_authority_pointer_files_exist_anywhere_under_pcae_dir():
    repo_root = Path(__file__).resolve().parents[1]
    pcae_dir = repo_root / ".pcae"
    forbidden_names = ("cltr-authority", "current-authority", "authority-pointer", "authority-epoch")
    for path in pcae_dir.rglob("*"):
        lowered = path.name.lower()
        for marker in forbidden_names:
            assert marker not in lowered, f"Unexpected authority-looking artifact: {path}"


# ---------------------------------------------------------------------------
# 11. Filesystem-mutation proof
# ---------------------------------------------------------------------------


def _snapshot(paths: list[Path]) -> dict[str, tuple[float, int] | None]:
    snap: dict[str, tuple[float, int] | None] = {}
    for p in paths:
        if p.exists():
            st = p.stat()
            snap[str(p)] = (st.st_mtime_ns, st.st_size)
        else:
            snap[str(p)] = None
    return snap


def test_136g_parsing_and_validation_do_not_mutate_repository_state():
    repo_root = Path(__file__).resolve().parents[1]
    watched = [
        repo_root / ".pcae",
        repo_root / "schemas",
        repo_root / "tasks",
        repo_root / "PROJECT_STATUS.md",
        repo_root / "CHANGELOG.md",
    ]
    before = _snapshot(watched)

    # Exercise a representative cross-section: parsing, loading, registry
    # construction, valid and invalid shape validation, and an
    # unresolved-reference infrastructure failure.
    parse_strict_json('{"a": 1, "a": 2}')
    registry = _feature_registry()
    validate_record_shape({"tuple": ["x", 1]}, schema_id=FEATURE_MATRIX_ID, registry=registry)
    validate_record_shape({"blockedField": "x"}, schema_id=FEATURE_MATRIX_ID, registry=registry)
    validate_record_shape({}, schema_id="https://pcae.test/136g/unknown", registry=registry)

    after = _snapshot(watched)
    assert before == after


# ---------------------------------------------------------------------------
# 12. Dependency-failure / version-pinning sanity (independent re-derivation)
# ---------------------------------------------------------------------------


def test_136g_installed_jsonschema_version_independently_confirmed_in_range():
    from importlib.metadata import version

    installed = version("jsonschema")
    major, minor = (int(part) for part in installed.split(".")[:2])
    assert (major, minor) >= (4, 18)
    assert major < 5


def test_136g_draft202012validator_class_identity_stable_not_alias_of_latest():
    # jsonschema exposes a "validators.validator_for" auto-selection and a
    # "_LATEST_VERSION" concept; confirm Draft202012Validator is imported by
    # its own explicit name and is the class actually used, independent of
    # whatever the "latest" draft happens to be in a future jsonschema
    # release (a future 2023-... draft must not silently become "latest"
    # and get selected by an unqualified reference anywhere in this
    # package).
    from jsonschema import Draft202012Validator

    assert Draft202012Validator.META_SCHEMA["$id"] == "https://json-schema.org/draft/2020-12/schema"
    import pcae.schema_runtime.loader as loader_module
    import pcae.schema_runtime.validation as validation_module

    assert loader_module.Draft202012Validator is Draft202012Validator
    assert validation_module.Draft202012Validator is Draft202012Validator
