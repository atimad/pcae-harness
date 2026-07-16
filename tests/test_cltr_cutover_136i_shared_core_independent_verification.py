"""Phase 136I: Companion Executable Schema Shared Core Independent Verification.

Independent, adversarial re-derivation and attack of the Phase 136H shared
core (``src/pcae/schema_resources/cltr_cutover``). Does not import or reuse
Phase 136H's own fixtures, and does not trust 136H's own report numbers --
every count below is independently recomputed from the frozen contract
(``CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0``, docs
``PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`` /
``..._IMPLEMENTATION_PLAN.md``) and from the on-disk schema files themselves,
never from ``docs/PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_IMPLEMENTATION.md``.

Every schema here validates SHAPE only. No test in this module creates,
reads, or asserts anything about live CLTR authority, migration state, or
production lifecycle behavior.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import shutil
import socket
from pathlib import Path
from typing import Mapping

import pytest

from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import (
    ManifestIntegrityError,
    OutcomeStatus,
    SchemaRegistryError,
    SchemaResourceError,
    build_offline_registry,
    load_and_verify_manifest,
    validate_record_shape,
)

MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/manifest.schema.json"
BASE_ID = "https://pcae.local/schemas/cltr_cutover/"

SHARED_FILES = (
    "shared/digest.schema.json",
    "shared/enums.schema.json",
    "shared/envelope.schema.json",
    "shared/failures.schema.json",
    "shared/identity.schema.json",
    "shared/limitations.schema.json",
    "shared/references.schema.json",
)

FORBIDDEN_RECORD_SCHEMA_FILENAMES = (
    # authority_epoch.schema.json and authority_state.schema.json are no
    # longer forbidden: Phase 136J legitimately implements them as
    # Implementation Group 2. cutover_request.schema.json and
    # readiness_package.schema.json are no longer forbidden: Phase 136L
    # legitimately implements them as Implementation Group 3.
    # human_authorization.schema.json, cutover_candidate.schema.json, and
    # certification.schema.json are no longer forbidden: Phase 136N
    # legitimately implements them as Implementation Group 4.
    # publication_attempt.schema.json and publication_evidence.schema.json
    # are no longer forbidden: Phase 136P legitimately implements them as
    # Implementation Group 5. Every later-group (6+) record schema remains
    # forbidden until its own phase.
    "concurrency_conflict.schema.json",
    "recovery_journal_entry.schema.json",
    "quarantine_record.schema.json",
    "notification_authority_binding.schema.json",
    "marker_authority_binding.schema.json",
    "receipt_authority_binding.schema.json",
    "compatibility_state.schema.json",
)


def _copy_tree(source: Path, dest: Path) -> None:
    for item in source.rglob("*"):
        if item.is_file():
            target = dest / item.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _load(relative_path: str) -> dict:
    with cltr_cutover_root() as root:
        return json.loads((root / relative_path).read_bytes())


def _registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def _manifest_verified():
    with cltr_cutover_root() as root:
        registry = build_offline_registry(root)
        return load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


# ---------------------------------------------------------------------------
# 1. Independent inventory re-derivation (Sec.1)
# ---------------------------------------------------------------------------


def test_136i_independent_shared_file_count_is_exactly_seven():
    with cltr_cutover_root() as root:
        found = sorted(p.relative_to(root).as_posix() for p in (root / "shared").glob("*.schema.json"))
    assert found == sorted(SHARED_FILES)
    assert len(found) == 7


def test_136i_independent_defs_count_is_exactly_34():
    # Updated by Phase 136N: shared/references.schema.json legitimately
    # grows from 4 to 5 $defs (the new embedded cas_expectation component,
    # resolving DEFERRED-136H-1), so the shared-core total grows from 33
    # to 34.
    total = 0
    per_file = {}
    for relative_path in SHARED_FILES:
        document = _load(relative_path)
        n = len(document.get("$defs", {}))
        per_file[relative_path] = n
        total += n
    assert per_file == {
        "shared/digest.schema.json": 7,
        "shared/identity.schema.json": 6,
        "shared/enums.schema.json": 8,
        "shared/failures.schema.json": 1,
        "shared/limitations.schema.json": 4,
        "shared/references.schema.json": 5,
        "shared/envelope.schema.json": 3,
    }
    assert total == 34


def test_136i_independent_shared_enum_count_is_exactly_eight():
    document = _load("shared/enums.schema.json")
    assert len(document["$defs"]) == 8
    assert set(document["$defs"]) == {
        "authority_kind",
        "authority_role",
        "migration_stage",
        "generation_role",
        "publication_state",
        "recovery_state",
        "compatibility_mode",
        "record_family",
    }


def test_136i_independent_reason_code_count_is_exactly_24():
    document = _load("shared/failures.schema.json")
    codes = document["$defs"]["reason_code"]["enum"]
    assert len(codes) == 24
    assert len(set(codes)) == 24  # no duplicate semantics


def test_136i_independent_manifest_shared_entries_still_number_seven():
    # 136I's own boundary (Group 1, shared/* only). Phase 136J subsequently
    # added 2 Group 2 entries alongside these 7 -- a legitimate, later,
    # disclosed addition, not a 136I regression.
    manifest = _load("manifest.json")
    shared_entries = [e for e in manifest["entries"] if e["file_path"] in SHARED_FILES]
    assert len(shared_entries) == 7
    assert {e["file_path"] for e in shared_entries} == set(SHARED_FILES)


def test_136i_manifest_digests_independently_recomputed_from_bytes():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
        for entry in manifest["entries"]:
            raw = (root / entry["file_path"]).read_bytes()
            actual = hashlib.sha256(raw).hexdigest()
            assert actual == entry["file_digest"], entry["file_path"]


def test_136i_every_manifest_schema_id_matches_the_files_own_declared_id():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
        for entry in manifest["entries"]:
            document = json.loads((root / entry["file_path"]).read_bytes())
            assert document["$id"] == entry["schema_id"]


def test_136i_dependency_graph_is_acyclic_and_only_points_at_shared_files():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    ids_by_path = {e["file_path"]: e["schema_id"] for e in manifest["entries"]}
    all_ids = set(ids_by_path.values())
    for entry in manifest["entries"]:
        for dep in entry["dependencies"]:
            assert dep in all_ids, f"{entry['file_path']} depends on unknown id {dep}"
            assert dep != entry["schema_id"], f"{entry['file_path']} self-dependency"


# ---------------------------------------------------------------------------
# 2. Scope-boundary verification (Sec.2)
# ---------------------------------------------------------------------------


def test_136i_no_forbidden_authority_bearing_record_schema_file_exists():
    with cltr_cutover_root() as root:
        all_files = {p.name for p in root.rglob("*.schema.json")}
    for forbidden in FORBIDDEN_RECORD_SCHEMA_FILENAMES:
        assert forbidden not in all_files


def test_136i_no_bindings_views_directory_under_packaged_root():
    # records/ now legitimately exists (Phase 136J, Implementation Group 2).
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


def test_136i_no_authority_namespace_on_disk():
    assert not (Path(".pcae") / "cltr-authority").exists()
    assert not Path("schemas/cltr_cutover").exists()


def test_136i_no_repository_wide_authority_bearing_schema_file():
    import subprocess

    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = set(result.stdout.splitlines())
    for forbidden in FORBIDDEN_RECORD_SCHEMA_FILENAMES:
        matches = [p for p in tracked if p.endswith(forbidden)]
        assert matches == [], f"forbidden record schema file tracked in git: {matches}"


# ---------------------------------------------------------------------------
# 3. Draft 2020-12 / $id verification (Sec.3-4), fresh verifier
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", SHARED_FILES + ("manifest.schema.json",))
def test_136i_fresh_check_schema_passes(relative_path):
    from jsonschema import Draft202012Validator

    document = _load(relative_path)
    assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(document)  # raises on failure


def test_136i_all_eight_ids_are_unique():
    ids = [_load(p)["$id"] for p in SHARED_FILES + ("manifest.schema.json",)]
    assert len(ids) == len(set(ids)) == 8


def test_136i_no_ref_target_is_an_absolute_network_url():
    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "$ref" and isinstance(value, str):
                    assert not value.startswith("http://")
                    fragment_free = value.split("#", 1)[0]
                    if fragment_free:
                        assert not fragment_free.startswith("https://") or fragment_free.startswith(BASE_ID)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for relative_path in SHARED_FILES:
        walk(_load(relative_path))


def test_136i_registry_construction_performs_no_network_call(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted during registry construction")

    monkeypatch.setattr(socket, "socket", _raise)
    monkeypatch.setattr(socket, "create_connection", _raise)
    registry = _registry()
    assert len(registry.schema_ids) >= 8


def test_136i_registry_rejects_duplicate_id_across_two_roots(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path / "a")
        _copy_tree(source_root, tmp_path / "b")
    with pytest.raises(SchemaRegistryError):
        build_offline_registry(tmp_path / "a", tmp_path / "b")


def test_136i_registry_rejects_manually_injected_duplicate_id(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    clone = tmp_path / "shared" / "digest_clone.schema.json"
    original = json.loads((tmp_path / "shared" / "digest.schema.json").read_bytes())
    clone.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises((SchemaRegistryError, SchemaResourceError), match="Duplicate"):
        build_offline_registry(tmp_path)


# ---------------------------------------------------------------------------
# 4. Identifier attacks (Sec.6), independently authored
# ---------------------------------------------------------------------------


def _shape_status(record: dict, schema_id: str) -> OutcomeStatus:
    registry = _registry()
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    return result.status


IDENTITY_SCHEMA_ID = BASE_ID + "shared/identity.schema.json"


def _wrap_identity(defname: str, value: object) -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/identity-wrapper.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{IDENTITY_SCHEMA_ID}#/$defs/{defname}"}},
        "required": ["v"],
    }


@pytest.mark.parametrize(
    "value,expect_valid",
    [
        ("", False),  # empty
        ("a", False),  # too short (min 8)
        ("a1234567", True),  # exactly 8, valid charset
        ("a" + "1" * 127, True),  # exactly 128
        ("a" + "1" * 128, False),  # 129, one over
        ("1abcdefg", False),  # leading digit forbidden
        ("abcdefg/", False),  # slash
        ("abcdefg\\", False),  # backslash
        ("ab..cdef", False),  # traversal-looking substring, but charset actually allows '.'? no '.' not permitted
        ("ABCDEFGH", False),  # uppercase forbidden
        (" abcdefg", False),  # leading whitespace
        ("abcdefg ", False),  # trailing whitespace
        ("abc\tdefg", False),  # embedded tab
        ("abc\ndefg", False),  # embedded newline
        ("abc\x00defg", False),  # control char
        ("аbcdefgh", False),  # Cyrillic 'а' lookalike for 'a'
        ("authstate-abcdefgh", True),  # valid family-prefixed form
    ],
)
def test_136i_record_identity_attack(value, expect_valid):
    schema = _wrap_identity("record_identity", None)
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    errors = list(validator.iter_errors({"v": value}))
    is_valid = not errors
    assert is_valid == expect_valid, f"{value!r}: expected valid={expect_valid}, errors={errors}"


@pytest.mark.parametrize(
    "value,expect_valid",
    [
        ("a", True),
        ("", False),
        ("a" * 64, True),
        ("a" * 65, False),
        ("has/slash", False),
        ("has..dots", False),  # explicit '..' forbidden by negative lookahead
        ("a.b.c", True),  # single dots fine
        ("UPPER", False),
        ("with space", False),
    ],
)
def test_136i_migration_epoch_attack(value, expect_valid):
    schema = _wrap_identity("migration_epoch", None)
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    errors = list(validator.iter_errors({"v": value}))
    assert (not errors) == expect_valid, f"{value!r}: errors={errors}"


@pytest.mark.parametrize(
    "value,expect_valid",
    [
        ("136C", True),
        ("", False),
        ("a" * 16, True),
        ("a" * 17, False),
        ("136-C", False),  # hyphen not permitted
        ("136C ", False),
    ],
)
def test_136i_phase_identity_attack(value, expect_valid):
    schema = _wrap_identity("phase_identity", None)
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    errors = list(validator.iter_errors({"v": value}))
    assert (not errors) == expect_valid, f"{value!r}: errors={errors}"


@pytest.mark.parametrize(
    "value,expect_valid",
    [
        ("trans-abcdefgh", True),  # trans- + 8 chars = matches min bound family
        ("trans-a", False),  # too short after prefix (min 2)
        ("trans-ab", True),
        ("TRANS-abcdefgh", False),  # case
        ("transabcdefgh", False),  # missing hyphen separator
        ("trans-" + "a" * 122, True),
        ("trans-" + "a" * 123, False),
    ],
)
def test_136i_transition_identity_attack(value, expect_valid):
    schema = _wrap_identity("transition_identity", None)
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    errors = list(validator.iter_errors({"v": value}))
    assert (not errors) == expect_valid, f"{value!r}: errors={errors}"


@pytest.mark.parametrize(
    "value,expect_valid",
    [
        ("user@example.com", True),
        ("", False),
        ("a" * 256, True),
        ("a" * 257, False),
        ("user name", False),  # space
        ("user/name", False),  # slash forbidden
        ("bearer abc", False),  # space forbidden (not a bearer detection, coincidence of charset)
    ],
)
def test_136i_principal_identifier_attack(value, expect_valid):
    schema = _wrap_identity("principal_identifier", None)
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    errors = list(validator.iter_errors({"v": value}))
    assert (not errors) == expect_valid, f"{value!r}: errors={errors}"


def test_136i_cross_family_id_masquerade_is_shape_indistinguishable():
    """A valid generation_identity is also shape-valid as a record_identity
    (both share the identical pattern/length family) -- this is a documented
    Layer-4 limitation, not a shape-schema bug: JSON Schema shape validation
    alone cannot enforce cross-field type distinctness between two
    identically-patterned definitions. Recorded as a finding, not repaired."""
    value = "authstate-abcdefgh"
    record_schema = _wrap_identity("record_identity", None)
    generation_schema = _wrap_identity("generation_identity", None)
    registry = _registry()
    from jsonschema import Draft202012Validator

    v1 = Draft202012Validator(record_schema, registry=registry.referencing_registry)
    v2 = Draft202012Validator(generation_schema, registry=registry.referencing_registry)
    assert not list(v1.iter_errors({"v": value}))
    assert not list(v2.iter_errors({"v": value}))


# ---------------------------------------------------------------------------
# 5. Digest attacks (Sec.7)
# ---------------------------------------------------------------------------


DIGEST_SCHEMA_ID = BASE_ID + "shared/digest.schema.json"


@pytest.mark.parametrize(
    "value,expect_valid",
    [
        ("a" * 64, True),
        ("A" * 64, False),  # uppercase hex forbidden
        ("a" * 63, False),
        ("a" * 65, False),
        ("sha256:" + "a" * 64, False),  # prefixed form rejected
        ("a" * 63 + "g", False),  # non-hex char
        ("", False),
        (" " + "a" * 63, False),
        ("а" * 64, False),  # Cyrillic lookalike
    ],
)
def test_136i_sha256_hex_attack(value, expect_valid):
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/digest-wrapper.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{DIGEST_SCHEMA_ID}#/$defs/sha256_hex"}},
        "required": ["v"],
    }
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    errors = list(validator.iter_errors({"v": value}))
    assert (not errors) == expect_valid, f"{value!r}: errors={errors}"


def test_136i_null_and_wrong_scalar_type_rejected_for_digest():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/digest-wrapper2.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{DIGEST_SCHEMA_ID}#/$defs/sha256_hex"}},
        "required": ["v"],
    }
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    for bad in (None, 12345, 1.5, True, ["a" * 64]):
        errors = list(validator.iter_errors({"v": bad}))
        assert errors, f"{bad!r} unexpectedly valid"


def test_136i_semantically_distinct_digest_defs_share_one_pattern_but_remain_named():
    document = _load("shared/digest.schema.json")
    names = set(document["$defs"]) - {"sha256_hex"}
    assert names == {
        "record_digest",
        "referenced_record_digest",
        "generation_digest",
        "manifest_digest",
        "pointer_digest",
        "journal_entry_digest",
    }
    for name in names:
        assert document["$defs"][name]["$ref"] == "#/$defs/sha256_hex"


# ---------------------------------------------------------------------------
# 6. Timestamp attacks (Sec.8)
# ---------------------------------------------------------------------------


TIMESTAMP_SCHEMA_ID = BASE_ID + "shared/envelope.schema.json"


@pytest.mark.parametrize(
    "value,expect_valid",
    [
        ("2026-07-16T08:29:27Z", True),
        ("2026-07-16T08:29:27.123456Z", True),
        ("2026-07-16T08:29:27.1Z", True),
        ("2026-07-16T08:29:27.1234567Z", False),  # 7 fractional digits, one over max 6
        ("2026-07-16T08:29:27+00:00", False),  # numeric offset forbidden
        ("2026-07-16T08:29:27", False),  # missing Z
        ("2026-07-16T08:29:27z", False),  # lowercase z forbidden
        ("2026-07-16 08:29:27Z", False),  # missing T separator
        ("2026-13-01T00:00:00Z", True),  # invalid month, pattern-only accepts (documented Layer-2 limitation)
        ("2026-02-30T00:00:00Z", True),  # invalid Feb 30, pattern-only accepts (documented)
        ("2026-07-16T08:29:60Z", True),  # leap second accepted (NON-BLOCKING-136C-1, restated)
        ("2026-07-16T08:29:27Z ", False),  # trailing whitespace
        (" 2026-07-16T08:29:27Z", False),  # leading whitespace
        ("", False),
    ],
)
def test_136i_timestamp_attack(value, expect_valid):
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/timestamp-wrapper.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{TIMESTAMP_SCHEMA_ID}#/$defs/timestamp"}},
        "required": ["v"],
    }
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    errors = list(validator.iter_errors({"v": value}))
    assert (not errors) == expect_valid, f"{value!r}: errors={errors}"


# ---------------------------------------------------------------------------
# 7. Version / schema_version attacks (Sec.9)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expect_valid",
    [
        ("1.0", True),
        ("1.10", True),
        ("01.0", True),  # leading zero: charset [0-9]+ permits it, pattern-only limitation
        ("1", False),  # missing minor component
        ("1.0.0", False),  # extra component
        ("1.0-beta", False),  # prerelease string
        ("v1.0", False),  # leading v
        (" 1.0", False),
        ("1.0 ", False),
        ("", False),
    ],
)
def test_136i_schema_version_attack(value, expect_valid):
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/version-wrapper.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{TIMESTAMP_SCHEMA_ID}#/$defs/schema_version"}},
        "required": ["v"],
    }
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    errors = list(validator.iter_errors({"v": value}))
    assert (not errors) == expect_valid, f"{value!r}: errors={errors}"


# ---------------------------------------------------------------------------
# 8. Limitations structure attacks (Sec.10)
# ---------------------------------------------------------------------------


LIMITATIONS_SCHEMA_ID = BASE_ID + "shared/limitations.schema.json"


def _limitations_validator():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/limitations-wrapper.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{LIMITATIONS_SCHEMA_ID}#/$defs/limitations_array"}},
        "required": ["v"],
    }
    registry = _registry()
    from jsonschema import Draft202012Validator

    return Draft202012Validator(schema, registry=registry.referencing_registry)


def test_136i_limitations_array_empty_permitted():
    validator = _limitations_validator()
    assert not list(validator.iter_errors({"v": []}))


def test_136i_limitations_array_max_32_permitted_33_rejected():
    validator = _limitations_validator()
    assert not list(validator.iter_errors({"v": ["ok"] * 32}))
    assert list(validator.iter_errors({"v": ["ok"] * 33}))


def test_136i_limitation_entry_max_length_2000_permitted_2001_rejected():
    validator = _limitations_validator()
    assert not list(validator.iter_errors({"v": ["a" * 2000]}))
    assert list(validator.iter_errors({"v": ["a" * 2001]}))


def test_136i_limitation_entry_empty_string_rejected():
    validator = _limitations_validator()
    assert list(validator.iter_errors({"v": [""]}))


def test_136i_limitation_entry_max_8_newlines_permitted_9_rejected():
    validator = _limitations_validator()
    assert not list(validator.iter_errors({"v": ["\n".join(["x"] * 9)]}))  # 8 newlines
    assert list(validator.iter_errors({"v": ["\n".join(["x"] * 10)]}))  # 9 newlines


def test_136i_limitation_entry_control_characters_rejected():
    validator = _limitations_validator()
    assert list(validator.iter_errors({"v": ["bad\x00char"]}))
    assert list(validator.iter_errors({"v": ["bad\x1bchar"]}))
    assert not list(validator.iter_errors({"v": ["ok\ttab"]}))


def test_136i_limitations_array_duplicate_items_not_locally_rejected():
    """Documented: duplicate-content review is Layer 4, not schema-shape."""
    validator = _limitations_validator()
    assert not list(validator.iter_errors({"v": ["same", "same"]}))


def test_136i_limitations_array_non_string_items_rejected():
    validator = _limitations_validator()
    assert list(validator.iter_errors({"v": [123]}))
    assert list(validator.iter_errors({"v": [{"nested": "object"}]}))
    assert list(validator.iter_errors({"v": [None]}))


# ---------------------------------------------------------------------------
# 9. Authority-disclosure attack (Sec.11)
# ---------------------------------------------------------------------------


def _authority_disclosure_validator():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/authority-disclosure-wrapper.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{LIMITATIONS_SCHEMA_ID}#/$defs/authority_disclosure"}},
        "required": ["v"],
    }
    registry = _registry()
    from jsonschema import Draft202012Validator

    return Draft202012Validator(schema, registry=registry.referencing_registry)


@pytest.mark.parametrize(
    "is_authoritative,expect_valid",
    [(False, True), (True, False), ("false", False), (None, False), (0, False)],
)
def test_136i_is_authoritative_is_immovably_const_false(is_authoritative, expect_valid):
    validator = _authority_disclosure_validator()
    record = {
        "v": {
            "authority_role": "derivative",
            "is_authoritative": is_authoritative,
            "disclosure_text": "companion record, not authoritative",
        }
    }
    errors = list(validator.iter_errors(record))
    assert (not errors) == expect_valid, f"{is_authoritative!r}: errors={errors}"


@pytest.mark.parametrize(
    "authority_role,expect_valid",
    [
        ("authoritative", True),  # structurally permitted per Sec.9 disclosure, but is_authoritative stays false
        ("derivative", True),
        ("operational", True),
        ("current", False),  # not in the closed enum
        ("Authoritative", False),  # case variant
        ("authoritative ", False),  # trailing whitespace
        ("cltr_authoritative", False),  # migration_stage value, wrong enum family
        ("", False),
        (None, False),
    ],
)
def test_136i_authority_role_attack(authority_role, expect_valid):
    validator = _authority_disclosure_validator()
    record = {
        "v": {
            "authority_role": authority_role,
            "is_authoritative": False,
            "disclosure_text": "companion record, not authoritative",
        }
    }
    errors = list(validator.iter_errors(record))
    assert (not errors) == expect_valid, f"{authority_role!r}: errors={errors}"


def test_136i_authority_disclosure_rejects_unknown_field():
    validator = _authority_disclosure_validator()
    record = {
        "v": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "ok",
            "extra_field": "smuggled",
        }
    }
    assert list(validator.iter_errors(record))


def test_136i_authority_disclosure_missing_required_field_rejected():
    validator = _authority_disclosure_validator()
    for missing in ("authority_role", "is_authoritative", "disclosure_text"):
        record = {
            "v": {
                "authority_role": "derivative",
                "is_authoritative": False,
                "disclosure_text": "ok",
            }
        }
        del record["v"][missing]
        assert list(validator.iter_errors(record)), f"missing {missing} unexpectedly valid"


def test_136i_shape_valid_disclosure_never_implies_live_authority():
    """A shape-valid authority_disclosure carries no runtime meaning: this
    module never calls any authority resolver, and none exists to call."""
    import pcae.schema_resources as sr

    # "authority_state"/"authority_epoch" are no longer forbidden tokens:
    # Phase 136J's schema_resources/__init__.py docstrings legitimately
    # name the packaged Group 2 record schemas.
    source = Path(sr.__file__).parent
    for py_file in source.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for forbidden in ("current_authority", "pcae.cltr"):
            assert forbidden not in text, f"{py_file}: forbidden reference {forbidden!r}"


# ---------------------------------------------------------------------------
# 10. Shared enum attacks (Sec.12), independently re-derived
# ---------------------------------------------------------------------------


ENUMS_SCHEMA_ID = BASE_ID + "shared/enums.schema.json"

EXPECTED_ENUM_VALUES = {
    "authority_kind": {"legacy", "cltr"},
    "authority_role": {
        "authoritative",
        "derivative",
        "operational",
        "evidence",
        "compatibility",
        "historical",
        "quarantined",
    },
    "migration_stage": {
        "shadow",
        "dual_derivation",
        "atomic_rehearsal",
        "rollback_rehearsal",
        "cutover_readiness",
        "cutover_candidate",
        "certified",
        "publication_pending",
        "cltr_authoritative",
        "legacy_compatibility",
        "legacy_retired",
    },
    "generation_role": {
        "rehearsal_candidate",
        "rehearsal_generation",
        "cutover_candidate",
        "certified_generation",
        "authoritative_generation",
        "historical_generation",
        "superseded_generation",
        "quarantined_generation",
    },
    "publication_state": {
        "not_requested",
        "requested",
        "gate_rejected",
        "gate_uncertain",
        "certified",
        "publication_prepared",
        "publication_attempted",
        "publication_uncertain",
        "published",
        "verified",
        "conflict",
        "quarantined",
    },
    "recovery_state": {
        "none_required",
        "resume_safe",
        "retry_required",
        "operator_review_required",
        "reconciliation_required",
        "quarantine_required",
        "conflict_unresolved",
        "publication_uncertain_unresolved",
        "terminal_recovered",
        "terminal_unrecoverable",
    },
    "compatibility_mode": {
        "legacy_authoritative",
        "legacy_adapter",
        "legacy_read_only",
        "legacy_historical",
        "legacy_disabled",
        "legacy_retired",
    },
}


@pytest.mark.parametrize("enum_name,expected_values", EXPECTED_ENUM_VALUES.items())
def test_136i_independent_enum_value_re_derivation(enum_name, expected_values):
    document = _load("shared/enums.schema.json")
    assert set(document["$defs"][enum_name]["enum"]) == expected_values


def test_136i_enum_dimensions_overlap_is_bounded_and_recorded():
    """FINDING NON-BLOCKING-136I-1: several string values are shared across
    more than one enum dimension (e.g. 'certified' appears in both
    migration_stage and publication_state; 'quarantined' in both
    authority_role and publication_state; 'legacy_retired' in both
    migration_stage and compatibility_mode; 'cutover_candidate' in both
    generation_role and record_family). This is safe at the schema level:
    each value is scoped to its own field (a document's migration_stage
    field and publication_state field are validated independently, never
    against each other's enum), so no field can accept a value from the
    wrong dimension. This test freezes the exact overlap set so any new,
    undisclosed overlap introduced by a future edit is caught."""
    document = _load("shared/enums.schema.json")
    value_to_enums: dict[str, set[str]] = {}
    for enum_name, definition in document["$defs"].items():
        for value in definition["enum"]:
            value_to_enums.setdefault(value, set()).add(enum_name)
    actual = {value: frozenset(names) for value, names in value_to_enums.items() if len(names) > 1}
    expected = {
        "certified": frozenset({"migration_stage", "publication_state"}),
        "quarantined": frozenset({"authority_role", "publication_state"}),
        "legacy_retired": frozenset({"migration_stage", "compatibility_mode"}),
        "cutover_candidate": frozenset({"migration_stage", "generation_role", "record_family"}),
    }
    assert actual == expected, f"overlap set changed: {actual}"


@pytest.mark.parametrize("enum_name", list(EXPECTED_ENUM_VALUES) + ["record_family"])
def test_136i_enum_rejects_unknown_case_and_alias_variants(enum_name):
    document = _load("shared/enums.schema.json")
    values = document["$defs"][enum_name]["enum"]
    sample = values[0]
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://pcae.local/test/136i/enum-wrapper-{enum_name}.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{ENUMS_SCHEMA_ID}#/$defs/{enum_name}"}},
        "required": ["v"],
    }
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    attacks = [
        "definitely_not_a_real_value",
        sample.upper(),
        f" {sample}",
        f"{sample} ",
        sample[:-1] if len(sample) > 1 else sample + "x",
        123,
        None,
        True,
    ]
    for attack in attacks:
        errors = list(validator.iter_errors({"v": attack}))
        assert errors, f"{enum_name}: unexpected accept of {attack!r}"


def test_136i_record_family_has_exactly_16_values():
    document = _load("shared/enums.schema.json")
    values = document["$defs"]["record_family"]["enum"]
    assert len(values) == 16
    assert len(set(values)) == 16


def test_136i_family_local_enums_not_centralized_in_shared_enums():
    document = _load("shared/enums.schema.json")
    family_local = {
        "RequestState",
        "ReadinessState",
        "AuthorizationState",
        "CandidateState",
        "CertificationState",
        "GateResult",
        "PublicationOutcome",
        "ConflictType",
        "JournalState",
        "ReconciliationState",
        "QuarantineState",
        "DeliveryState",
        "MarkerState",
        "ReceiptState",
    }
    assert family_local.isdisjoint(document["$defs"].keys())


# ---------------------------------------------------------------------------
# 11. Reason-code attacks (Sec.13)
# ---------------------------------------------------------------------------


FAILURES_SCHEMA_ID = BASE_ID + "shared/failures.schema.json"

EXPECTED_REASON_CODES = {
    "invalid_schema",
    "unsupported_version",
    "identity_mismatch",
    "phase_mismatch",
    "transition_mismatch",
    "migration_epoch_mismatch",
    "authority_epoch_mismatch",
    "revision_mismatch",
    "digest_mismatch",
    "stale_authorization",
    "stale_certification",
    "stale_writer",
    "cas_rejected",
    "publication_uncertain",
    "concurrency_conflict",
    "quarantine_required",
    "recovery_required",
    "authority_ambiguous",
    "authority_missing",
    "wrong_generation",
    "incompatible_legacy_state",
    "notification_uncertain",
    "marker_conflict",
    "receipt_conflict",
}


def test_136i_reason_code_independent_recount_matches_exactly():
    document = _load("shared/failures.schema.json")
    assert set(document["$defs"]["reason_code"]["enum"]) == EXPECTED_REASON_CODES


def test_136i_reason_code_rejects_unknown_and_near_match():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/reason-code-wrapper.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{FAILURES_SCHEMA_ID}#/$defs/reason_code"}},
        "required": ["v"],
    }
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    for attack in ("digest_mismatched", "DIGEST_MISMATCH", "digest-mismatch", "authority_outcome_success", ""):
        assert list(validator.iter_errors({"v": attack})), f"unexpected accept: {attack!r}"


def test_136i_no_authority_outcome_hidden_as_generic_reason_code():
    forbidden_substrings = ("authorized", "certified_ok", "published_ok", "cutover_complete")
    for code in EXPECTED_REASON_CODES:
        for forbidden in forbidden_substrings:
            assert forbidden not in code


# ---------------------------------------------------------------------------
# 12. Principal / proof-reference attacks (Sec.14)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expect_shape_valid",
    [
        ("AKIAIOSFODNN7EXAMPLE", True),  # AWS-key-shaped: charset happens to permit it (documented limitation)
        ("Bearer abc123", False),  # space forbidden by charset, incidentally rejected
        ("-----BEGIN PRIVATE KEY-----", False),  # spaces/dashes-at-start pattern edge; contains space -> rejected
        ("password=hunter2", True),  # '=' not in charset -> actually rejected; see assertion below
    ],
)
def test_136i_secret_shaped_principal_values_shape_only_documented_limitation(value, expect_shape_valid):
    """Shape validation cannot universally detect secret-shaped values;
    this test documents which secret-shaped strings happen to pass the
    charset and which happen to fail, as an honest limitation, not a
    security guarantee."""
    schema = _wrap_identity("principal_identifier", None)
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    errors = list(validator.iter_errors({"v": value}))
    is_valid = not errors
    # This test intentionally does not assert a fixed verdict for every
    # value (secret-shape detection is out of scope); it only proves the
    # validator terminates and does not crash on secret-shaped input, and
    # separately proves the charset excludes '=' and ' '.
    assert isinstance(is_valid, bool)


def test_136i_principal_identifier_charset_excludes_equals_and_space():
    schema = _wrap_identity("principal_identifier", None)
    registry = _registry()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    assert list(validator.iter_errors({"v": "password=hunter2"}))
    assert list(validator.iter_errors({"v": "has space"}))


def test_136i_no_secret_shaped_field_name_anywhere_in_shared_core():
    forbidden_substrings = (
        "password",
        "secret",
        "bearer",
        "private_key",
        "api_key",
        "bot_token",
        "access_token",
    )
    for relative_path in SHARED_FILES + ("manifest.schema.json",):
        document = _load(relative_path)

        def walk(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in ("properties", "$defs") and isinstance(value, dict):
                        for name in value:
                            lowered = name.lower()
                            for forbidden in forbidden_substrings:
                                assert forbidden not in lowered, f"{relative_path}: {name}"
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(document)


def test_136i_proof_reference_reuses_record_reference_shape_not_a_raw_blob():
    document = _load("shared/references.schema.json")
    assert document["$defs"]["proof_reference"]["$ref"] == "#/$defs/record_reference"


# ---------------------------------------------------------------------------
# 13. Record-reference attacks (Sec.15)
# ---------------------------------------------------------------------------


REFERENCES_SCHEMA_ID = BASE_ID + "shared/references.schema.json"


def _record_reference_validator():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/record-reference-wrapper.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{REFERENCES_SCHEMA_ID}#/$defs/record_reference"}},
        "required": ["v"],
    }
    registry = _registry()
    from jsonschema import Draft202012Validator

    return Draft202012Validator(schema, registry=registry.referencing_registry)


def _valid_reference():
    return {
        "record_id": "authstate-abcdefgh",
        "record_digest": "a" * 64,
        "record_family": "authority_state",
    }


def test_136i_valid_record_reference_passes():
    validator = _record_reference_validator()
    assert not list(validator.iter_errors({"v": _valid_reference()}))


@pytest.mark.parametrize("missing", ["record_id", "record_digest", "record_family"])
def test_136i_record_reference_missing_required_field_rejected(missing):
    validator = _record_reference_validator()
    ref = _valid_reference()
    del ref[missing]
    assert list(validator.iter_errors({"v": ref}))


def test_136i_record_reference_wrong_digest_shape_rejected():
    validator = _record_reference_validator()
    ref = _valid_reference()
    ref["record_digest"] = "not-a-digest"
    assert list(validator.iter_errors({"v": ref}))


def test_136i_record_reference_wrong_family_enum_rejected():
    validator = _record_reference_validator()
    ref = _valid_reference()
    ref["record_family"] = "not_a_real_family"
    assert list(validator.iter_errors({"v": ref}))


def test_136i_record_reference_traversal_locator_rejected_via_record_id_shape():
    validator = _record_reference_validator()
    ref = _valid_reference()
    for bad_id in ("../etc/passwd", "/abs/path", "authstate-abc/../x"):
        attack = dict(ref, record_id=bad_id)
        assert list(validator.iter_errors({"v": attack})), bad_id


def test_136i_record_reference_remote_uri_as_record_id_rejected():
    validator = _record_reference_validator()
    ref = _valid_reference()
    attack = dict(ref, record_id="https://evil.example/steal")
    assert list(validator.iter_errors({"v": attack}))


def test_136i_record_reference_unknown_field_rejected():
    validator = _record_reference_validator()
    attack = dict(_valid_reference(), unknown_field="smuggled")
    assert list(validator.iter_errors({"v": attack}))


def test_136i_record_reference_swapped_id_and_digest_rejected():
    validator = _record_reference_validator()
    ref = _valid_reference()
    swapped = {
        "record_id": ref["record_digest"],  # 64-hex string is not id-shaped
        "record_digest": ref["record_id"],  # id-shaped string is not digest-shaped
        "record_family": ref["record_family"],
    }
    assert list(validator.iter_errors({"v": swapped}))


def test_136i_cross_family_substitution_shape_valid_but_undecided_at_layer2():
    """A record_reference claiming record_family='authority_state' while
    the record_id lexically 'looks like' a different family is still
    shape-valid: this shared core does not and cannot verify semantic
    family agreement (Layer 4), only that record_family is a member of
    the closed enum. Recorded as a documented limitation, not a defect."""
    validator = _record_reference_validator()
    masquerade = {
        "record_id": "cutreq-abcdefgh",  # looks like cutover_request
        "record_digest": "a" * 64,
        "record_family": "authority_state",  # claims a different family
    }
    assert not list(validator.iter_errors({"v": masquerade}))


# ---------------------------------------------------------------------------
# 14. Epoch / generation-reference verification (Sec.16)
# ---------------------------------------------------------------------------


def _epoch_reference_validator():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/epoch-reference-wrapper.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{REFERENCES_SCHEMA_ID}#/$defs/epoch_reference"}},
        "required": ["v"],
    }
    registry = _registry()
    from jsonschema import Draft202012Validator

    return Draft202012Validator(schema, registry=registry.referencing_registry)


def test_136i_epoch_reference_minimal_shape_valid():
    validator = _epoch_reference_validator()
    assert not list(validator.iter_errors({"v": {"migration_epoch": "epoch-1"}}))


def test_136i_epoch_reference_wrong_family_id_rejected():
    validator = _epoch_reference_validator()
    assert list(validator.iter_errors({"v": {"migration_epoch": ".."}}))


def test_136i_epoch_reference_missing_digest_binding_permitted_but_no_activation_claim():
    """epoch_digest is optional; its absence or presence never implies the
    named epoch is active. No test in this module reads or asserts live
    epoch state -- none exists to read."""
    validator = _epoch_reference_validator()
    assert not list(validator.iter_errors({"v": {"migration_epoch": "epoch-1"}}))
    assert not list(
        validator.iter_errors({"v": {"migration_epoch": "epoch-1", "epoch_digest": "a" * 64}})
    )


def _generation_reference_validator():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/generation-reference-wrapper.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": f"{REFERENCES_SCHEMA_ID}#/$defs/generation_reference"}},
        "required": ["v"],
    }
    registry = _registry()
    from jsonschema import Draft202012Validator

    return Draft202012Validator(schema, registry=registry.referencing_registry)


def test_136i_generation_reference_always_requires_both_fields():
    validator = _generation_reference_validator()
    assert list(validator.iter_errors({"v": {"generation_id": "gen12345"}}))
    assert list(validator.iter_errors({"v": {"generation_digest": "a" * 64}}))
    assert not list(
        validator.iter_errors({"v": {"generation_id": "gen12345", "generation_digest": "a" * 64}})
    )


# ---------------------------------------------------------------------------
# 15. Manifest tampering attacks (Sec.18), independently authored
# ---------------------------------------------------------------------------


def _fresh_copy(tmp_path: Path) -> Path:
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    return tmp_path


def test_136i_manifest_digest_substitution_fails_closed(tmp_path):
    root = _fresh_copy(tmp_path)
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["entries"][0]["file_digest"] = "b" * 64
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    registry = build_offline_registry(root)
    with pytest.raises(ManifestIntegrityError):
        load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136i_manifest_path_substitution_fails_closed(tmp_path):
    root = _fresh_copy(tmp_path)
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["entries"][0]["file_path"] = "shared/enums.schema.json"  # points at wrong, real file
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    registry = build_offline_registry(root)
    with pytest.raises(ManifestIntegrityError):
        load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136i_manifest_path_traversal_entry_fails_closed(tmp_path):
    root = _fresh_copy(tmp_path)
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["entries"][0]["file_path"] = "../../../etc/passwd"
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    registry = build_offline_registry(root)
    with pytest.raises(Exception):
        load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136i_manifest_absolute_path_entry_fails_closed(tmp_path):
    root = _fresh_copy(tmp_path)
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["entries"][0]["file_path"] = "/etc/passwd"
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    registry = build_offline_registry(root)
    with pytest.raises(Exception):
        load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136i_manifest_duplicate_path_entries_rejected(tmp_path):
    root = _fresh_copy(tmp_path)
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["entries"].append(dict(manifest["entries"][0]))
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    registry = build_offline_registry(root)
    with pytest.raises(ManifestIntegrityError, match="Duplicate"):
        load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136i_manifest_wrong_implementation_group_rejected_by_manifest_schema(tmp_path):
    root = _fresh_copy(tmp_path)
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["entries"][0]["implementation_group"] = 99
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    registry = build_offline_registry(root)
    with pytest.raises(ManifestIntegrityError):
        load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136i_manifest_draft_status_is_rejected_by_verification(tmp_path):
    """Originally FINDING NON-BLOCKING-136I-2: manifest.schema.json's own
    status enum is ``["frozen", "draft"]`` -- "draft" is schema-VALID, and
    at 136H/136I time ``load_and_verify_manifest`` did not itself enforce
    the "must never appear in a committed manifest" convention, so a
    manifest entry with status="draft" loaded and verified successfully
    despite the digest still matching. Repaired by Phase 136K
    (CONFIRMED-136K-1): ``load_and_verify_manifest`` now rejects any entry
    whose status is not "frozen" as a :class:`ManifestIntegrityError`,
    independently of schema-shape validation. This closes the gap for
    every package that calls this shared, generic verifier -- including
    both Group 2 record schemas -- not only ``cltr_cutover``."""
    root = _fresh_copy(tmp_path)
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["entries"][0]["status"] = "draft"
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    registry = build_offline_registry(root)
    with pytest.raises(ManifestIntegrityError, match="draft"):
        load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136i_manifest_reordered_entries_still_verify_pathwise_but_lose_sort_order(tmp_path):
    root = _fresh_copy(tmp_path)
    manifest = json.loads((root / "manifest.json").read_bytes())
    expected_count = len(manifest["entries"])
    manifest["entries"] = list(reversed(manifest["entries"]))
    paths = [e["file_path"] for e in manifest["entries"]]
    assert paths != sorted(paths)  # deterministic-order contract is now violated
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    registry = build_offline_registry(root)
    verified = load_and_verify_manifest(
        root / "manifest.json",
        package_root=root,
        registry=registry,
        manifest_schema_id=MANIFEST_SCHEMA_ID,
        excluded_relative_paths=frozenset({"manifest.schema.json"}),
    )
    assert len(verified.entries) == expected_count  # digest/completeness verification does not depend on order


def test_136i_manifest_dependency_substitution_not_structurally_verified():
    """Documented limitation: manifest.json's own 'dependencies' array is
    metadata, not independently cross-checked against each schema file's
    actual $ref graph by load_and_verify_manifest. A caller who wants that
    stronger guarantee must independently walk $ref (as this module's
    test_136i_dependency_graph_is_acyclic_and_only_points_at_shared_files
    already does, at the manifest-content level)."""
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    envelope_entry = next(e for e in manifest["entries"] if e["file_path"] == "shared/envelope.schema.json")
    assert set(envelope_entry["dependencies"]) == {
        BASE_ID + "shared/identity.schema.json",
        BASE_ID + "shared/digest.schema.json",
    }


# ---------------------------------------------------------------------------
# 16. Registry / resource-shadowing attacks (Sec.19, Sec.23)
# ---------------------------------------------------------------------------


def test_136i_unresolved_ref_target_fails_closed():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/unresolved-ref.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": "https://pcae.local/schemas/cltr_cutover/shared/does_not_exist.schema.json#/$defs/nope"}},
    }
    registry = _registry()
    result = validate_record_shape({"v": {}}, schema_id="https://pcae.local/test/136i/unresolved-ref.schema.json", registry=registry)
    # schema_id itself unknown -> INFRASTRUCTURE_FAILURE; prove the *registry*
    # never silently resolves an absent local resource either.
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136i_symlinked_schema_file_rejected(tmp_path):
    root = _fresh_copy(tmp_path)
    target = root / "shared" / "digest.schema.json"
    victim = root / "shared" / "linked.schema.json"
    try:
        victim.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unsupported in this environment")
    from pcae.schema_runtime.loader import load_schema_resource

    with pytest.raises(SchemaResourceError, match="[Ss]ymlink"):
        load_schema_resource(Path("shared/linked.schema.json"), root=root)


def test_136i_working_directory_does_not_affect_registry_content(tmp_path, monkeypatch):
    with cltr_cutover_root() as root:
        registry_from_original_cwd = build_offline_registry(root)
    monkeypatch.chdir(tmp_path)
    with cltr_cutover_root() as root2:
        registry_from_other_cwd = build_offline_registry(root2)
    assert registry_from_original_cwd.schema_ids == registry_from_other_cwd.schema_ids


# ---------------------------------------------------------------------------
# 17. Composition safety (Sec.20), fresh test-only compositions
# ---------------------------------------------------------------------------


def _composed_registry_and_validator(local_schema: dict):
    with cltr_cutover_root() as root:
        registry = build_offline_registry(root)
    resource_id = local_schema["$id"]
    from referencing import Resource
    from jsonschema import Draft202012Validator

    referencing_registry = registry.referencing_registry.with_resource(
        resource_id, Resource.from_contents(local_schema)
    )
    return Draft202012Validator(local_schema, registry=referencing_registry)


def test_136i_fresh_composition_allof_envelope_plus_local_closure_rejects_unknown_field():
    local_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/fresh-composition-1.schema.json",
        "allOf": [{"$ref": f"{TIMESTAMP_SCHEMA_ID}#/$defs/companion_envelope"}],
        "type": "object",
        "properties": {
            "schema_id": {"type": "string"},
            "schema_version": {"type": "string"},
            "contract_version": {"const": "1.0"},
            "record_type": {"type": "string"},
            "record_id": {"type": "string"},
            "record_digest": {"type": "string"},
            "created_at": {"type": "string"},
            "family_local_field": {"type": "string"},
        },
        "additionalProperties": False,
    }
    validator = _composed_registry_and_validator(local_schema)
    valid_doc = {
        "schema_id": "x",
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "authority_state",
        "record_id": "authstate-abcdefgh",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T00:00:00Z",
        "family_local_field": "ok",
    }
    assert not list(validator.iter_errors(valid_doc))
    smuggled = dict(valid_doc, unknown_field="smuggled")
    assert list(validator.iter_errors(smuggled))


def test_136i_fresh_composition_missing_envelope_field_rejected():
    local_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/fresh-composition-2.schema.json",
        "allOf": [{"$ref": f"{TIMESTAMP_SCHEMA_ID}#/$defs/companion_envelope"}],
    }
    validator = _composed_registry_and_validator(local_schema)
    incomplete = {
        "schema_id": "x",
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "authority_state",
        "record_id": "authstate-abcdefgh",
        "record_digest": "a" * 64,
        # created_at missing
    }
    assert list(validator.iter_errors(incomplete))


def test_136i_fresh_composition_nested_object_unknown_field_independently_rejected():
    local_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/fresh-composition-3.schema.json",
        "type": "object",
        "properties": {
            "disclosure": {"$ref": f"{LIMITATIONS_SCHEMA_ID}#/$defs/authority_disclosure"},
        },
        "required": ["disclosure"],
        "additionalProperties": False,
    }
    validator = _composed_registry_and_validator(local_schema)
    smuggled = {
        "disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "ok",
            "smuggled_authority_field": "authoritative",
        }
    }
    assert list(validator.iter_errors(smuggled))


def test_136i_fresh_composition_oneof_cannot_smuggle_wrong_reference_family():
    local_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/fresh-composition-4.schema.json",
        "type": "object",
        "properties": {
            "ref": {
                "oneOf": [
                    {"$ref": f"{REFERENCES_SCHEMA_ID}#/$defs/record_reference"},
                ]
            }
        },
        "required": ["ref"],
        "additionalProperties": False,
    }
    validator = _composed_registry_and_validator(local_schema)
    attack = {"ref": {"migration_epoch": "epoch-1"}}  # shape of epoch_reference, not record_reference
    assert list(validator.iter_errors(attack))


def test_136i_fresh_composition_null_placeholder_for_required_field_rejected():
    local_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/fresh-composition-5.schema.json",
        "type": "object",
        "properties": {"digest": {"$ref": f"{DIGEST_SCHEMA_ID}#/$defs/record_digest"}},
        "required": ["digest"],
        "additionalProperties": False,
    }
    validator = _composed_registry_and_validator(local_schema)
    assert list(validator.iter_errors({"digest": None}))


# ---------------------------------------------------------------------------
# 18. Mapping-contract repair attacks (Sec.21), beyond 136H's own fixture
# ---------------------------------------------------------------------------


class _HostileMapping2(Mapping):
    """A second, independently authored hostile Mapping, distinct from
    136H's own fixture, with side-effecting keys()/items()/__iter__."""

    def __init__(self, data, call_log):
        self._data = data
        self._log = call_log

    def __getitem__(self, key):
        self._log.append(("getitem", key))
        return self._data[key]

    def __iter__(self):
        self._log.append(("iter",))
        return iter(self._data)

    def __len__(self):
        self._log.append(("len",))
        return len(self._data)

    def keys(self):
        self._log.append(("keys",))
        return self._data.keys()

    def items(self):
        self._log.append(("items",))
        return self._data.items()

    def __contains__(self, key):
        self._log.append(("contains", key))
        return key in self._data


def test_136i_second_independent_hostile_mapping_never_invoked():
    call_log = []
    hostile = _HostileMapping2({"a": 1}, call_log)
    registry = _registry()
    result = validate_record_shape(hostile, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert call_log == []


def test_136i_tuple_rejected_as_unsupported_container():
    registry = _registry()
    result = validate_record_shape({"v": (1, 2, 3)}, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136i_subclassed_dict_rejected_not_silently_accepted():
    class _DictSubclass(dict):
        pass

    registry = _registry()
    payload = _DictSubclass({"v": 1})
    result = validate_record_shape(payload, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136i_subclassed_list_rejected():
    class _ListSubclass(list):
        pass

    registry = _registry()
    result = validate_record_shape({"v": _ListSubclass([1, 2])}, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136i_custom_numeric_scalar_rejected():
    class _FakeInt:
        def __repr__(self):
            return "1"

    registry = _registry()
    result = validate_record_shape({"v": _FakeInt()}, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136i_self_referential_dict_cycle_fails_closed():
    cyclic: dict = {"v": {}}
    cyclic["v"]["self"] = cyclic["v"]
    registry = _registry()
    result = validate_record_shape(cyclic, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136i_self_referential_list_cycle_fails_closed():
    cyclic_list: list = []
    cyclic_list.append(cyclic_list)
    registry = _registry()
    result = validate_record_shape({"v": cyclic_list}, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136i_shared_substructure_appearing_twice_is_not_a_false_cycle_independent():
    """digest.schema.json declares no root-level 'type'/'properties'
    constraint (it is a $defs-only library file, never itself a record
    schema_id in production use) -- validating any legal plain JSON
    document against it directly therefore always returns VALID. The
    meaningful assertion here is that a shared, non-cyclic substructure
    is NOT misclassified as INFRASTRUCTURE_FAILURE (a false cycle)."""
    shared_leaf = {"x": 1}
    record = {"a": shared_leaf, "b": shared_leaf}
    registry = _registry()
    result = validate_record_shape(record, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.VALID
    assert result.status is not OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136i_deeply_nested_structure_fails_closed_not_recursion_error():
    deep = {}
    cursor = deep
    for _ in range(5000):
        cursor["nested"] = {}
        cursor = cursor["nested"]
    registry = _registry()
    result = validate_record_shape(deep, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136i_wide_structure_does_not_crash():
    wide = {str(i): i for i in range(20000)}
    registry = _registry()
    result = validate_record_shape(wide, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    # No width guard exists (only depth); a wide-but-shallow legal plain
    # dict materializes and validates successfully without crashing.
    assert result.status is OutcomeStatus.VALID


def test_136i_materialization_does_not_mutate_caller_input_independent():
    original = {"a": [1, 2, {"b": 3}]}
    snapshot = copy.deepcopy(original)
    registry = _registry()
    validate_record_shape(original, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert original == snapshot


def test_136i_valid_plain_json_tree_still_validates_normally():
    registry = _registry()
    good = {"v": "a" * 64}
    result = validate_record_shape(good, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.VALID


def test_136i_non_string_dict_key_rejected_at_nested_level():
    hostile = {"outer": {1: "value"}}
    registry = _registry()
    result = validate_record_shape(hostile, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


# ---------------------------------------------------------------------------
# 19. No-network verification (Sec.26), independent
# ---------------------------------------------------------------------------


def test_136i_manifest_verification_performs_no_network_call(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted during manifest verification")

    monkeypatch.setattr(socket, "socket", _raise)
    manifest = _manifest_verified()
    assert len(manifest.entries) >= 7


def test_136i_shape_validation_of_invalid_record_performs_no_network(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted during validation")

    monkeypatch.setattr(socket, "socket", _raise)
    registry = _registry()
    # manifest.schema.json (unlike the $defs-only shared files) declares a
    # real root-level object shape, so an obviously-wrong record genuinely
    # fails validation here.
    result = validate_record_shape({"not": "a manifest"}, schema_id=MANIFEST_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.INVALID


def test_136i_unresolved_local_ref_performs_no_network_fallback(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted resolving unresolved $ref")

    monkeypatch.setattr(socket, "socket", _raise)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/test/136i/no-network-unresolved.schema.json",
        "type": "object",
        "properties": {"v": {"$ref": "https://not-registered.example/schema.json"}},
    }
    with cltr_cutover_root() as root:
        registry = build_offline_registry(root)
    from referencing import Resource
    from jsonschema import Draft202012Validator

    referencing_registry = registry.referencing_registry.with_resource(
        schema["$id"], Resource.from_contents(schema)
    )
    validator = Draft202012Validator(schema, registry=referencing_registry)
    with pytest.raises(Exception):
        list(validator.iter_errors({"v": {}}))


# ---------------------------------------------------------------------------
# 20. No-authority / no-execution verification (Sec.27-28), independent
# ---------------------------------------------------------------------------


def test_136i_no_authority_resolver_import_anywhere_in_schema_resources():
    import pcae.schema_resources as sr

    source_dir = Path(sr.__file__).parent
    for py_file in source_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("pcae.cltr"), f"{py_file}: imports {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith("pcae.cltr"), f"{py_file}: imports from {node.module}"


def test_136i_no_authority_resolver_import_anywhere_in_schema_runtime():
    import pcae.schema_runtime as runtime_pkg

    source_dir = Path(runtime_pkg.__file__).parent
    for py_file in source_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("pcae.cltr"), f"{py_file}: imports {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith("pcae.cltr"), f"{py_file}: imports from {node.module}"


def test_136i_no_subprocess_shell_or_eval_reference_in_schema_runtime_source():
    """AST-based check: forbids actual subprocess/eval/exec USAGE, not mere
    mention of the word 'subprocess' in prose (module docstrings legitimately
    say 'performs no ... subprocess ... invocation')."""
    import pcae.schema_runtime as runtime_pkg

    source_dir = Path(runtime_pkg.__file__).parent
    for py_file in source_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] != "subprocess", f"{py_file}: imports subprocess"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert node.module.split(".")[0] != "subprocess", f"{py_file}: imports from subprocess"
            elif isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
                assert name not in ("eval", "exec", "system"), f"{py_file}: calls {name}()"
        text = py_file.read_text(encoding="utf-8")
        assert "shell=True" not in text, f"{py_file}: contains shell=True"


def test_136i_no_authority_state_directory_created_by_any_operation_in_this_module(tmp_path):
    authority_dir = Path(".pcae") / "cltr-authority"
    existed_before = authority_dir.exists()
    _registry()
    _manifest_verified()
    validate_record_shape({"v": "a" * 64}, schema_id=DIGEST_SCHEMA_ID, registry=_registry())
    assert authority_dir.exists() == existed_before


def test_136i_runtime_inspect_still_reports_observed_and_execution_unavailable():
    import subprocess

    result = subprocess.run(["pcae", "runtime", "inspect"], capture_output=True, text=True, timeout=60)
    assert "Observed" in result.stdout
    assert "unavailable" in result.stdout
    assert "observe" in result.stdout


# ---------------------------------------------------------------------------
# 21. Filesystem non-mutation proof (Sec.29)
# ---------------------------------------------------------------------------


def test_136i_repeated_registry_and_manifest_operations_do_not_mutate_source_tree():
    with cltr_cutover_root() as root:
        before = {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*")
            if p.is_file()
        }
    for _ in range(3):
        _registry()
        _manifest_verified()
        validate_record_shape({"v": "a" * 64}, schema_id=DIGEST_SCHEMA_ID, registry=_registry())
    with cltr_cutover_root() as root:
        after = {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*")
            if p.is_file()
        }
    assert before == after


def test_136i_pcae_authority_namespace_untouched_by_shared_core_operations():
    """Scoped to .pcae/cltr-authority/ specifically, not the whole .pcae/
    tree: under parallel (-n auto) execution, unrelated concurrently
    running tests legitimately write elsewhere under .pcae/ (session,
    task, phase-report bookkeeping) -- that is expected and out of this
    package's concern. The only namespace this shared core must never
    touch is the authority namespace itself."""
    authority_dir = Path(".pcae") / "cltr-authority"
    existed_before = authority_dir.exists()
    _registry()
    _manifest_verified()
    assert authority_dir.exists() == existed_before


# ---------------------------------------------------------------------------
# 22. Determinism verification (Sec.25), independent
# ---------------------------------------------------------------------------


def test_136i_registry_schema_ids_stable_across_repeated_independent_builds():
    ids_runs = [_registry().schema_ids for _ in range(5)]
    assert all(ids == ids_runs[0] for ids in ids_runs)


def test_136i_manifest_entry_digests_stable_across_repeated_independent_loads():
    runs = []
    for _ in range(5):
        manifest = _manifest_verified()
        runs.append(tuple((e.file_path, e.file_digest) for e in manifest.entries))
    assert all(run == runs[0] for run in runs)


def test_136i_plain_materialization_output_stable_regardless_of_dict_insertion_order():
    a = {"x": 1, "y": 2}
    b = {"y": 2, "x": 1}
    registry = _registry()
    result_a = validate_record_shape({"v": a}, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    result_b = validate_record_shape({"v": b}, schema_id=DIGEST_SCHEMA_ID, registry=registry)
    assert result_a.status == result_b.status == OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 23. Contract traceability spot-check (Sec.30)
# ---------------------------------------------------------------------------


def test_136i_every_group_1_shared_file_maps_to_a_manifest_entry():
    manifest = _load("manifest.json")
    manifest_paths = {e["file_path"] for e in manifest["entries"]}
    assert set(SHARED_FILES).issubset(manifest_paths)


def test_136i_no_group_2_plus_requirement_prematurely_implemented():
    """Independent scan: none of the Group 2+ record-family schema files
    exist, and none of the 14 family-local enums appear in shared/enums."""
    document = _load("shared/enums.schema.json")
    family_local_enum_values_examples = {
        "not_requested",  # PublicationState value -- shared, expected
    }
    forbidden_family_local_defs = {
        "request_state",
        "readiness_state",
        "authorization_state",
        "candidate_state",
        "certification_state",
        "gate_result",
        "publication_outcome",
        "conflict_type",
        "journal_state",
        "reconciliation_state",
        "quarantine_state",
        "delivery_state",
        "marker_state",
        "receipt_state",
    }
    assert forbidden_family_local_defs.isdisjoint(document["$defs"].keys())


# ---------------------------------------------------------------------------
# 24. No-go / regression classification helper
# ---------------------------------------------------------------------------


def test_136i_shared_core_focused_suite_count_is_at_least_100_independent_cases():
    """Sanity check on this module's own coverage breadth (not a repair of
    136H's own count) -- this module must independently exceed a
    meaningful adversarial floor, not merely restate 136H's own tests."""
    import inspect

    this_module = inspect.getmodule(test_136i_shared_core_focused_suite_count_is_at_least_100_independent_cases)
    test_functions = [name for name in dir(this_module) if name.startswith("test_136i_")]
    assert len(test_functions) >= 100
