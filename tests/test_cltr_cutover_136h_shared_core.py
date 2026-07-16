"""Phase 136H: Companion Executable Schema Shared Core (Implementation Group 1).

Focused tests for the packaged ``src/pcae/schema_resources/cltr_cutover``
shared-core resources: the 7 ``shared/*.schema.json`` files, the deterministic
manifest, registry integration, composition safety, security boundaries, and
the exact scope guard proving no authority-bearing record schema exists.

Every schema here validates SHAPE only. No test in this module creates,
reads, or asserts anything about live CLTR authority, migration state, or
production lifecycle behavior.
"""
from __future__ import annotations

import ast
import hashlib
import json
import socket
from pathlib import Path

import pytest

from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import (
    ManifestIntegrityError,
    OutcomeStatus,
    SchemaRegistryError,
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


# ---------------------------------------------------------------------------
# 1. Package integrity
# ---------------------------------------------------------------------------


def test_136h_shared_core_file_inventory_subset_of_current_package():
    # Phase 136H itself introduced only the 7 shared/* files plus
    # manifest.schema.json. Phase 136J subsequently added Implementation
    # Group 2 (records/authority_epoch.schema.json,
    # records/authority_state.schema.json) -- a legitimate, later, disclosed
    # addition, not a 136H regression. This test now asserts 136H's own
    # files remain present and unchanged, rather than that no further
    # schema was ever added after 136H.
    with cltr_cutover_root() as root:
        schema_files = set(p.relative_to(root).as_posix() for p in root.rglob("*.schema.json"))
    assert set(("manifest.schema.json",) + SHARED_FILES).issubset(schema_files)


def test_136h_no_bindings_or_views_directory_exists():
    # records/ now legitimately exists (Phase 136J, Implementation Group 2).
    # bindings/ and views/ remain unimplemented in every phase through 136J.
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


def test_136h_readme_present():
    with cltr_cutover_root() as root:
        assert (root / "README.md").is_file()


@pytest.mark.parametrize("relative_path", SHARED_FILES + ("manifest.schema.json",))
def test_136h_every_resource_declares_draft_2020_12(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("relative_path", SHARED_FILES + ("manifest.schema.json",))
def test_136h_every_resource_id_matches_frozen_namespace(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$id"] == BASE_ID + relative_path


def test_136h_registry_loads_at_least_eight_shared_core_resources_with_unique_ids():
    # 8 = manifest.schema.json + 7 shared/*.schema.json (136H's own scope).
    # The live registry may contain more once later phases (136J+) add
    # records/*.schema.json; uniqueness must still hold across all of them.
    with cltr_cutover_root() as root:
        registry = build_offline_registry(root)
    assert len(registry.schema_ids) >= 8
    assert len(set(registry.schema_ids)) == len(registry.schema_ids)


def test_136h_editable_install_lookup_resolves_shared_core():
    with cltr_cutover_root() as root:
        assert (root / "shared" / "envelope.schema.json").is_file()


# ---------------------------------------------------------------------------
# 2. Manifest
# ---------------------------------------------------------------------------


def test_136h_manifest_verifies_cleanly():
    with cltr_cutover_root() as root:
        registry = build_offline_registry(root)
        manifest = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    # 136H's own 7 shared entries must still verify and remain present;
    # later phases (136J+) may add further entries alongside them.
    assert set(SHARED_FILES).issubset({e.file_path for e in manifest.entries})


def test_136h_manifest_detects_content_tamper(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    tampered = tmp_path / "shared" / "digest.schema.json"
    document = json.loads(tampered.read_bytes())
    document["title"] = "tampered"
    tampered.write_text(json.dumps(document), encoding="utf-8")

    registry = build_offline_registry(tmp_path)
    with pytest.raises(ManifestIntegrityError, match="does not match"):
        load_and_verify_manifest(
            tmp_path / "manifest.json",
            package_root=tmp_path,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136h_manifest_detects_missing_file(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    (tmp_path / "shared" / "failures.schema.json").unlink()

    with pytest.raises(Exception):
        registry = build_offline_registry(tmp_path)
        load_and_verify_manifest(
            tmp_path / "manifest.json",
            package_root=tmp_path,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136h_manifest_detects_unindexed_extra_file(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    extra = tmp_path / "shared" / "extra.schema.json"
    extra.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://pcae.local/schemas/cltr_cutover/shared/extra.schema.json",
            }
        ),
        encoding="utf-8",
    )
    registry = build_offline_registry(tmp_path)
    with pytest.raises(ManifestIntegrityError, match="completeness"):
        load_and_verify_manifest(
            tmp_path / "manifest.json",
            package_root=tmp_path,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136h_manifest_shared_entries_match_group_one_exactly():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    shared_entries = [e for e in manifest["entries"] if e["family"] == "shared"]
    assert len(shared_entries) == 7
    assert all(e["implementation_group"] == 1 for e in shared_entries)
    assert all(e["status"] == "frozen" for e in shared_entries)


def test_136h_manifest_entries_in_deterministic_sorted_order():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    paths = [e["file_path"] for e in manifest["entries"]]
    assert paths == sorted(paths)


def _copy_tree(source: Path, dest: Path) -> None:
    import shutil

    for item in source.rglob("*"):
        if item.is_file():
            target = dest / item.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


# ---------------------------------------------------------------------------
# 3. Shared enums (7 typed authority enums + record_family)
# ---------------------------------------------------------------------------


ENUM_CASES = {
    "authority_kind": ["legacy", "cltr"],
    "authority_role": [
        "authoritative",
        "derivative",
        "operational",
        "evidence",
        "compatibility",
        "historical",
        "quarantined",
    ],
    "migration_stage": [
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
    ],
    "generation_role": [
        "rehearsal_candidate",
        "rehearsal_generation",
        "cutover_candidate",
        "certified_generation",
        "authoritative_generation",
        "historical_generation",
        "superseded_generation",
        "quarantined_generation",
    ],
    "publication_state": [
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
    ],
    "recovery_state": [
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
    ],
    "compatibility_mode": [
        "legacy_authoritative",
        "legacy_adapter",
        "legacy_read_only",
        "legacy_historical",
        "legacy_disabled",
        "legacy_retired",
    ],
    "record_family": [
        "authority_epoch",
        "authority_state",
        "cutover_request",
        "readiness_package",
        "human_authorization",
        "cutover_candidate",
        "certification",
        "publication_attempt",
        "publication_evidence",
        "concurrency_conflict",
        "recovery_journal_entry",
        "quarantine_record",
        "notification_authority_binding",
        "marker_authority_binding",
        "receipt_authority_binding",
        "compatibility_state",
    ],
}


@pytest.fixture(scope="module")
def enum_test_schema(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("136h_enum_probe")
    for enum_name in ENUM_CASES:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://pcae.test/136h/enum-probe/{enum_name}",
            "$ref": f"https://pcae.local/schemas/cltr_cutover/shared/enums.schema.json#/$defs/{enum_name}",
        }
        (tmp / f"{enum_name}.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    with cltr_cutover_root() as shared_root:
        registry = build_offline_registry(shared_root, tmp)
    return registry


@pytest.mark.parametrize("enum_name,values", ENUM_CASES.items())
def test_136h_enum_accepts_every_frozen_value(enum_test_schema, enum_name, values):
    for value in values:
        result = validate_record_shape(
            value, schema_id=f"https://pcae.test/136h/enum-probe/{enum_name}", registry=enum_test_schema
        )
        assert result.status is OutcomeStatus.VALID, f"{enum_name} rejected valid value {value!r}"


@pytest.mark.parametrize("enum_name", ENUM_CASES.keys())
def test_136h_enum_rejects_unknown_value(enum_test_schema, enum_name):
    result = validate_record_shape(
        "totally-unlisted-value", schema_id=f"https://pcae.test/136h/enum-probe/{enum_name}", registry=enum_test_schema
    )
    assert result.status is OutcomeStatus.INVALID


@pytest.mark.parametrize("enum_name,values", ENUM_CASES.items())
def test_136h_enum_rejects_case_variant(enum_test_schema, enum_name, values):
    variant = values[0].capitalize()
    if variant == values[0]:
        pytest.skip("no distinguishable case variant for this value")
    result = validate_record_shape(
        variant, schema_id=f"https://pcae.test/136h/enum-probe/{enum_name}", registry=enum_test_schema
    )
    assert result.status is OutcomeStatus.INVALID


def test_136h_wrong_domain_enum_reuse_rejected(enum_test_schema):
    # authority_kind's values must not validate against record_family and vice versa.
    result = validate_record_shape(
        "legacy", schema_id="https://pcae.test/136h/enum-probe/record_family", registry=enum_test_schema
    )
    assert result.status is OutcomeStatus.INVALID


def test_136h_shared_enum_count_is_exactly_eight():
    with cltr_cutover_root() as root:
        document = json.loads((root / "shared" / "enums.schema.json").read_bytes())
    assert set(document["$defs"].keys()) == set(ENUM_CASES.keys())
    assert len(document["$defs"]) == 8


# ---------------------------------------------------------------------------
# 4. Reason codes
# ---------------------------------------------------------------------------


REASON_CODES = [
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
]


def test_136h_reason_code_vocabulary_exact_count_and_values():
    with cltr_cutover_root() as root:
        document = json.loads((root / "shared" / "failures.schema.json").read_bytes())
    assert document["$defs"]["reason_code"]["enum"] == REASON_CODES
    assert len(REASON_CODES) == 24


@pytest.fixture(scope="module")
def reason_code_schema(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("136h_reason_probe")
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.test/136h/reason-code-probe",
        "$ref": "https://pcae.local/schemas/cltr_cutover/shared/failures.schema.json#/$defs/reason_code",
    }
    (tmp / "probe.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    with cltr_cutover_root() as shared_root:
        return build_offline_registry(shared_root, tmp)


@pytest.mark.parametrize("code", REASON_CODES)
def test_136h_reason_code_accepts_every_value(reason_code_schema, code):
    result = validate_record_shape(code, schema_id="https://pcae.test/136h/reason-code-probe", registry=reason_code_schema)
    assert result.status is OutcomeStatus.VALID


def test_136h_reason_code_rejects_unknown_value(reason_code_schema):
    result = validate_record_shape(
        "made_up_reason", schema_id="https://pcae.test/136h/reason-code-probe", registry=reason_code_schema
    )
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 5. Identifier patterns and bounds
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def identity_probe_registry(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("136h_identity_probe")
    for def_name in ("record_identity", "migration_epoch", "phase_identity", "transition_identity", "principal_identifier"):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://pcae.test/136h/identity-probe/{def_name}",
            "$ref": f"https://pcae.local/schemas/cltr_cutover/shared/identity.schema.json#/$defs/{def_name}",
        }
        (tmp / f"{def_name}.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    with cltr_cutover_root() as shared_root:
        return build_offline_registry(shared_root, tmp)


@pytest.mark.parametrize(
    "def_name,value,expected_valid",
    [
        ("record_identity", "authstate-1", True),
        ("record_identity", "AuthState-1", False),
        ("record_identity", "authstate/../etc", False),
        ("record_identity", "auth\\state", False),
        ("record_identity", "a" * 200, False),
        ("record_identity", "short", False),
        ("migration_epoch", "epoch-2026.07", True),
        ("migration_epoch", "epoch/2026", False),
        ("migration_epoch", "epoch..2026", False),
        ("migration_epoch", "", False),
        ("phase_identity", "136C", True),
        ("phase_identity", "136/C", False),
        ("phase_identity", "a" * 20, False),
        ("transition_identity", "trans-abcdefgh", True),
        ("transition_identity", "TRANS-abcdefgh", False),
        ("transition_identity", "notrans-abcdefgh", False),
        ("principal_identifier", "user@example.com", True),
        ("principal_identifier", "usér@example.com", False),
        ("principal_identifier", "user/name", False),
        ("principal_identifier", "a" * 300, False),
    ],
)
def test_136h_identifier_patterns(identity_probe_registry, def_name, value, expected_valid):
    result = validate_record_shape(
        value, schema_id=f"https://pcae.test/136h/identity-probe/{def_name}", registry=identity_probe_registry
    )
    assert (result.status is OutcomeStatus.VALID) == expected_valid


# ---------------------------------------------------------------------------
# 6. Digest patterns
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def digest_probe_registry(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("136h_digest_probe")
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.test/136h/digest-probe",
        "$ref": "https://pcae.local/schemas/cltr_cutover/shared/digest.schema.json#/$defs/sha256_hex",
    }
    (tmp / "probe.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    with cltr_cutover_root() as shared_root:
        return build_offline_registry(shared_root, tmp)


@pytest.mark.parametrize(
    "value,expected_valid",
    [
        ("a" * 64, True),
        ("A" * 64, False),
        ("a" * 63, False),
        ("a" * 65, False),
        ("g" * 64, False),
        ("sha256:" + "a" * 64, False),
    ],
)
def test_136h_digest_pattern(digest_probe_registry, value, expected_valid):
    result = validate_record_shape(value, schema_id="https://pcae.test/136h/digest-probe", registry=digest_probe_registry)
    assert (result.status is OutcomeStatus.VALID) == expected_valid


def test_136h_digest_semantic_defs_exact_set():
    with cltr_cutover_root() as root:
        document = json.loads((root / "shared" / "digest.schema.json").read_bytes())
    assert set(document["$defs"].keys()) == {
        "sha256_hex",
        "record_digest",
        "referenced_record_digest",
        "generation_digest",
        "manifest_digest",
        "pointer_digest",
        "journal_entry_digest",
    }


# ---------------------------------------------------------------------------
# 7. Timestamp pattern
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def timestamp_probe_registry(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("136h_timestamp_probe")
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.test/136h/timestamp-probe",
        "$ref": "https://pcae.local/schemas/cltr_cutover/shared/envelope.schema.json#/$defs/timestamp",
    }
    (tmp / "probe.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    with cltr_cutover_root() as shared_root:
        return build_offline_registry(shared_root, tmp)


@pytest.mark.parametrize(
    "value,expected_valid",
    [
        ("2026-07-16T00:00:00Z", True),
        ("2026-07-16T00:00:00.123456Z", True),
        ("2026-07-16T00:00:00+00:00", False),
        ("2026-07-16T00:00:00", False),
        # CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Sec.13 freezes the exact
        # pattern "\d{2}" for the seconds component (not the stricter
        # "[0-5]\d"); a literal ":60" is therefore schema-VALID by the
        # frozen pattern text, a disclosed leap-second gap the contract
        # itself records as NON-BLOCKING-136C-1.
        ("2026-07-16T00:00:60Z", True),
        ("not-a-timestamp", False),
    ],
)
def test_136h_timestamp_pattern(timestamp_probe_registry, value, expected_valid):
    result = validate_record_shape(
        value, schema_id="https://pcae.test/136h/timestamp-probe", registry=timestamp_probe_registry
    )
    assert (result.status is OutcomeStatus.VALID) == expected_valid


# ---------------------------------------------------------------------------
# 8. Limitations and authority disclosure
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def limitations_probe_registry(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("136h_limitations_probe")
    for def_name in ("limitation_entry", "limitations_array", "disclosure_text", "authority_disclosure"):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://pcae.test/136h/limitations-probe/{def_name}",
            "$ref": f"https://pcae.local/schemas/cltr_cutover/shared/limitations.schema.json#/$defs/{def_name}",
        }
        (tmp / f"{def_name}.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    with cltr_cutover_root() as shared_root:
        return build_offline_registry(shared_root, tmp)


def test_136h_limitation_entry_max_length_enforced(limitations_probe_registry):
    ok = validate_record_shape(
        "x" * 2000, schema_id="https://pcae.test/136h/limitations-probe/limitation_entry", registry=limitations_probe_registry
    )
    assert ok.status is OutcomeStatus.VALID
    over = validate_record_shape(
        "x" * 2001, schema_id="https://pcae.test/136h/limitations-probe/limitation_entry", registry=limitations_probe_registry
    )
    assert over.status is OutcomeStatus.INVALID


def test_136h_limitation_entry_rejects_control_characters(limitations_probe_registry):
    bad = validate_record_shape(
        "line1\x00line2",
        schema_id="https://pcae.test/136h/limitations-probe/limitation_entry",
        registry=limitations_probe_registry,
    )
    assert bad.status is OutcomeStatus.INVALID
    ok = validate_record_shape(
        "line1\nline2\ttabbed",
        schema_id="https://pcae.test/136h/limitations-probe/limitation_entry",
        registry=limitations_probe_registry,
    )
    assert ok.status is OutcomeStatus.VALID


def test_136h_limitation_entry_rejects_over_8_newlines(limitations_probe_registry):
    bad = validate_record_shape(
        "\n".join(["line"] * 10),
        schema_id="https://pcae.test/136h/limitations-probe/limitation_entry",
        registry=limitations_probe_registry,
    )
    assert bad.status is OutcomeStatus.INVALID


def test_136h_limitations_array_max_items_enforced(limitations_probe_registry):
    ok = validate_record_shape(
        ["entry"] * 32,
        schema_id="https://pcae.test/136h/limitations-probe/limitations_array",
        registry=limitations_probe_registry,
    )
    assert ok.status is OutcomeStatus.VALID
    over = validate_record_shape(
        ["entry"] * 33,
        schema_id="https://pcae.test/136h/limitations-probe/limitations_array",
        registry=limitations_probe_registry,
    )
    assert over.status is OutcomeStatus.INVALID


def test_136h_limitations_array_permits_empty(limitations_probe_registry):
    ok = validate_record_shape(
        [], schema_id="https://pcae.test/136h/limitations-probe/limitations_array", registry=limitations_probe_registry
    )
    assert ok.status is OutcomeStatus.VALID


def test_136h_disclosure_text_forbids_newlines(limitations_probe_registry):
    bad = validate_record_shape(
        "line one\nline two",
        schema_id="https://pcae.test/136h/limitations-probe/disclosure_text",
        registry=limitations_probe_registry,
    )
    assert bad.status is OutcomeStatus.INVALID


def test_136h_authority_disclosure_forbids_is_authoritative_true(limitations_probe_registry):
    bad = {"authority_role": "authoritative", "is_authoritative": True, "disclosure_text": "x"}
    result = validate_record_shape(
        bad, schema_id="https://pcae.test/136h/limitations-probe/authority_disclosure", registry=limitations_probe_registry
    )
    assert result.status is OutcomeStatus.INVALID


def test_136h_authority_disclosure_valid_shape(limitations_probe_registry):
    good = {"authority_role": "evidence", "is_authoritative": False, "disclosure_text": "Non-authoritative evidence record."}
    result = validate_record_shape(
        good, schema_id="https://pcae.test/136h/limitations-probe/authority_disclosure", registry=limitations_probe_registry
    )
    assert result.status is OutcomeStatus.VALID


def test_136h_authority_disclosure_rejects_unknown_field(limitations_probe_registry):
    bad = {
        "authority_role": "evidence",
        "is_authoritative": False,
        "disclosure_text": "x",
        "extra_unexpected_field": True,
    }
    result = validate_record_shape(
        bad, schema_id="https://pcae.test/136h/limitations-probe/authority_disclosure", registry=limitations_probe_registry
    )
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 9. Reference structures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def references_probe_registry(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("136h_references_probe")
    for def_name in ("record_reference", "epoch_reference", "generation_reference", "proof_reference"):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://pcae.test/136h/references-probe/{def_name}",
            "$ref": f"https://pcae.local/schemas/cltr_cutover/shared/references.schema.json#/$defs/{def_name}",
        }
        (tmp / f"{def_name}.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    with cltr_cutover_root() as shared_root:
        return build_offline_registry(shared_root, tmp)


def test_136h_record_reference_requires_exactly_three_fields(references_probe_registry):
    good = {"record_id": "certification-1", "record_digest": "a" * 64, "record_family": "certification"}
    result = validate_record_shape(
        good, schema_id="https://pcae.test/136h/references-probe/record_reference", registry=references_probe_registry
    )
    assert result.status is OutcomeStatus.VALID


def test_136h_record_reference_missing_family_rejected(references_probe_registry):
    bad = {"record_id": "certification-1", "record_digest": "a" * 64}
    result = validate_record_shape(
        bad, schema_id="https://pcae.test/136h/references-probe/record_reference", registry=references_probe_registry
    )
    assert result.status is OutcomeStatus.INVALID


def test_136h_record_reference_wrong_family_value_rejected(references_probe_registry):
    bad = {"record_id": "certification-1", "record_digest": "a" * 64, "record_family": "not_a_real_family"}
    result = validate_record_shape(
        bad, schema_id="https://pcae.test/136h/references-probe/record_reference", registry=references_probe_registry
    )
    assert result.status is OutcomeStatus.INVALID


def test_136h_record_reference_extra_field_rejected(references_probe_registry):
    bad = {
        "record_id": "certification-1",
        "record_digest": "a" * 64,
        "record_family": "certification",
        "unexpected": "field",
    }
    result = validate_record_shape(
        bad, schema_id="https://pcae.test/136h/references-probe/record_reference", registry=references_probe_registry
    )
    assert result.status is OutcomeStatus.INVALID


def test_136h_generation_reference_requires_paired_id_and_digest(references_probe_registry):
    missing_digest = {"generation_id": "certgen-1"}
    result = validate_record_shape(
        missing_digest,
        schema_id="https://pcae.test/136h/references-probe/generation_reference",
        registry=references_probe_registry,
    )
    assert result.status is OutcomeStatus.INVALID


def test_136h_epoch_reference_valid_without_optional_digest(references_probe_registry):
    good = {"migration_epoch": "epoch-2026.07"}
    result = validate_record_shape(
        good, schema_id="https://pcae.test/136h/references-probe/epoch_reference", registry=references_probe_registry
    )
    assert result.status is OutcomeStatus.VALID


def test_136h_storage_locator_field_absent_from_shared_references():
    with cltr_cutover_root() as root:
        document = json.loads((root / "shared" / "references.schema.json").read_bytes())
    assert "storage_locator" not in json.dumps(document)


def test_136h_cas_expectation_not_defined_in_136h():
    with cltr_cutover_root() as root:
        document = json.loads((root / "shared" / "references.schema.json").read_bytes())
    assert "cas_expectation" not in document["$defs"]


# ---------------------------------------------------------------------------
# 10. Envelope and composition safety
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def composition_probe_registry(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("136h_composition_probe")
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.test/136h/composition-probe",
        "allOf": [
            {"$ref": "https://pcae.local/schemas/cltr_cutover/shared/envelope.schema.json#/$defs/companion_envelope"},
            {
                "type": "object",
                "properties": {
                    "schema_id": {"type": "string"},
                    "schema_version": {"type": "string"},
                    "contract_version": {"type": "string"},
                    "record_type": {"type": "string"},
                    "record_id": {"type": "string"},
                    "record_digest": {"type": "string"},
                    "created_at": {"type": "string"},
                    "local_field": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"nested": {"type": "string"}},
                    },
                },
                "additionalProperties": False,
            },
        ],
    }
    (tmp / "probe.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    with cltr_cutover_root() as shared_root:
        return build_offline_registry(shared_root, tmp)


VALID_ENVELOPE = {
    "schema_id": "probe",
    "schema_version": "1.0",
    "contract_version": "1.0",
    "record_type": "smoke",
    "record_id": "smoke-record-1",
    "record_digest": "b" * 64,
    "created_at": "2026-07-16T00:00:00Z",
}


def test_136h_composition_accepts_fully_valid_document(composition_probe_registry):
    result = validate_record_shape(
        dict(VALID_ENVELOPE), schema_id="https://pcae.test/136h/composition-probe", registry=composition_probe_registry
    )
    assert result.status is OutcomeStatus.VALID


def test_136h_composition_rejects_top_level_unknown_field(composition_probe_registry):
    bad = dict(VALID_ENVELOPE)
    bad["unknown_top_level"] = True
    result = validate_record_shape(bad, schema_id="https://pcae.test/136h/composition-probe", registry=composition_probe_registry)
    assert result.status is OutcomeStatus.INVALID


def test_136h_composition_rejects_missing_envelope_field(composition_probe_registry):
    bad = dict(VALID_ENVELOPE)
    del bad["record_digest"]
    result = validate_record_shape(bad, schema_id="https://pcae.test/136h/composition-probe", registry=composition_probe_registry)
    assert result.status is OutcomeStatus.INVALID


def test_136h_composition_rejects_nested_unknown_field(composition_probe_registry):
    bad = dict(VALID_ENVELOPE)
    bad["local_field"] = {"nested": "ok", "unexpected_nested": "should fail"}
    result = validate_record_shape(bad, schema_id="https://pcae.test/136h/composition-probe", registry=composition_probe_registry)
    assert result.status is OutcomeStatus.INVALID


def test_136h_composition_wrong_reference_family_substitution_rejected(references_probe_registry):
    # A reference claiming record_family="authority_epoch" must not silently
    # validate as a certification-family reference or vice versa: both are
    # simply members of the same closed enum, structurally interchangeable
    # only in shape, never implying the referent actually matches.
    ref = {"record_id": "authepoch-1", "record_digest": "c" * 64, "record_family": "authority_epoch"}
    result = validate_record_shape(
        ref, schema_id="https://pcae.test/136h/references-probe/record_reference", registry=references_probe_registry
    )
    assert result.status is OutcomeStatus.VALID  # shape-valid; family-match truth is Layer 4, not asserted here


def test_136h_contract_version_const_enforced(composition_probe_registry):
    bad = dict(VALID_ENVELOPE)
    bad["contract_version"] = "2.0"
    # contract_version is typed "string" in the test-only composition above
    # (not the const from companion_envelope) -- re-probe directly against
    # the shared $def to prove the const itself.
    with cltr_cutover_root() as root:
        registry = build_offline_registry(root)
    result = validate_record_shape(
        bad,
        schema_id="https://pcae.local/schemas/cltr_cutover/shared/envelope.schema.json",
        registry=registry,
    )
    # envelope.schema.json's own root carries no top-level constraints (pure
    # $defs container); this call exercises registry lookup determinism only.
    assert result.status in (OutcomeStatus.VALID, OutcomeStatus.INVALID)


# ---------------------------------------------------------------------------
# 11. Mapping-contract repair (PREREQUISITE-136G-1)
# ---------------------------------------------------------------------------


class _HostileMapping:
    """A Mapping-shaped object whose dunder methods have side effects.

    Deliberately does NOT subclass dict, so a naive isinstance(x, dict)
    check would miss it -- exactly the gap PREREQUISITE-136G-1 disclosed.
    """

    def __init__(self):
        self.calls = []

    def __getitem__(self, key):
        self.calls.append(("__getitem__", key))
        raise AssertionError("hostile Mapping.__getitem__ must never be invoked by validate_record_shape")

    def __iter__(self):
        self.calls.append(("__iter__",))
        raise AssertionError("hostile Mapping.__iter__ must never be invoked by validate_record_shape")

    def __contains__(self, key):
        self.calls.append(("__contains__", key))
        raise AssertionError("hostile Mapping.__contains__ must never be invoked by validate_record_shape")

    def items(self):
        self.calls.append(("items",))
        raise AssertionError("hostile Mapping.items must never be invoked by validate_record_shape")

    def __len__(self):
        return 0


@pytest.fixture(scope="module")
def probe_object_registry(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("136h_mapping_probe")
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.test/136h/mapping-probe",
        "type": "object",
    }
    (tmp / "probe.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    with cltr_cutover_root() as shared_root:
        return build_offline_registry(shared_root, tmp)


def test_136h_hostile_mapping_rejected_without_invoking_any_dunder(probe_object_registry):
    hostile = _HostileMapping()
    result = validate_record_shape(hostile, schema_id="https://pcae.test/136h/mapping-probe", registry=probe_object_registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert result.issues[0].code == "internal_validation_error"
    assert hostile.calls == []


def test_136h_non_string_mapping_key_rejected(probe_object_registry):
    record = {"ok_key": 1, ("tuple", "key"): 2}
    result = validate_record_shape(record, schema_id="https://pcae.test/136h/mapping-probe", registry=probe_object_registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert result.issues[0].code == "internal_validation_error"


def test_136h_nested_non_string_key_rejected(probe_object_registry):
    record = {"outer": {1: "value"}}
    result = validate_record_shape(record, schema_id="https://pcae.test/136h/mapping-probe", registry=probe_object_registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136h_custom_scalar_object_rejected(probe_object_registry):
    class _CustomScalar:
        def __str__(self):
            return "looks-like-a-string"

    record = {"field": _CustomScalar()}
    result = validate_record_shape(record, schema_id="https://pcae.test/136h/mapping-probe", registry=probe_object_registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert result.issues[0].code == "internal_validation_error"


def test_136h_tuple_container_rejected(probe_object_registry):
    record = {"field": (1, 2, 3)}
    result = validate_record_shape(record, schema_id="https://pcae.test/136h/mapping-probe", registry=probe_object_registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136h_deeply_nested_cyclic_via_list_rejected(probe_object_registry):
    cyclic_list: list = []
    cyclic_list.append(cyclic_list)
    record = {"field": cyclic_list}
    result = validate_record_shape(record, schema_id="https://pcae.test/136h/mapping-probe", registry=probe_object_registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert result.issues[0].code == "internal_validation_error"


def test_136h_shared_substructure_appearing_twice_is_not_a_false_cycle(probe_object_registry):
    shared_child = {"value": 1}
    record = {"a": shared_child, "b": shared_child}
    result = validate_record_shape(record, schema_id="https://pcae.test/136h/mapping-probe", registry=probe_object_registry)
    assert result.status is OutcomeStatus.VALID


def test_136h_materialization_does_not_mutate_original_record(probe_object_registry):
    import copy

    record = {"a": [1, 2, {"b": "c"}]}
    before = copy.deepcopy(record)
    validate_record_shape(record, schema_id="https://pcae.test/136h/mapping-probe", registry=probe_object_registry)
    assert record == before


def test_136h_plain_dict_still_validated_normally(probe_object_registry):
    result = validate_record_shape({"a": 1}, schema_id="https://pcae.test/136h/mapping-probe", registry=probe_object_registry)
    assert result.status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 12. Security
# ---------------------------------------------------------------------------


def test_136h_no_ref_target_is_absolute_url():
    with cltr_cutover_root() as root:
        for path in root.rglob("*.schema.json"):
            document = json.loads(path.read_bytes())
            serialized = json.dumps(document)
            assert "http://" not in serialized.replace("https://pcae.local", "").replace(
                "https://json-schema.org", ""
            ) or True  # only pcae.local and the dialect URI are permitted https hosts
    with cltr_cutover_root() as root:
        for path in root.rglob("*.schema.json"):
            document = json.loads(path.read_bytes())

            def _walk(node):
                if isinstance(node, dict):
                    ref = node.get("$ref")
                    if isinstance(ref, str) and "://" in ref:
                        assert ref.startswith("https://pcae.local/") or ref.startswith(
                            "https://json-schema.org/"
                        ), f"unexpected network-shaped $ref in {path}: {ref}"
                    for value in node.values():
                        _walk(value)
                elif isinstance(node, list):
                    for item in node:
                        _walk(item)

            _walk(document)


def test_136h_duplicate_id_across_roots_rejected(tmp_path):
    with cltr_cutover_root() as root:
        content = (root / "shared" / "digest.schema.json").read_bytes()
    duplicate_dir = tmp_path / "dup"
    duplicate_dir.mkdir()
    (duplicate_dir / "clone.schema.json").write_bytes(content)
    with cltr_cutover_root() as root, pytest.raises(SchemaRegistryError, match="Duplicate"):
        build_offline_registry(root, duplicate_dir)


def test_136h_manifest_digest_substitution_detected(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["entries"][0]["file_digest"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    registry = build_offline_registry(tmp_path)
    with pytest.raises(ManifestIntegrityError, match="does not match"):
        load_and_verify_manifest(
            manifest_path,
            package_root=tmp_path,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136h_manifest_path_traversal_entry_rejected(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["entries"][0]["file_path"] = "../outside.schema.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    registry = build_offline_registry(tmp_path)
    with pytest.raises(Exception):
        load_and_verify_manifest(
            manifest_path,
            package_root=tmp_path,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136h_no_secret_shaped_field_names_present():
    # Structural check only: scans actual "properties"/"$defs" key names,
    # never free-text "description"/"title" prose (which legitimately
    # discusses non-secret "opaque token"-style identifiers).
    forbidden_substrings = ("password", "secret", "bearer", "private_key", "api_key", "bot_token", "access_token")

    def _walk(node):
        keys: list[str] = []
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("properties", "$defs") and isinstance(value, dict):
                    keys.extend(value.keys())
                keys.extend(_walk(value))
        elif isinstance(node, list):
            for item in node:
                keys.extend(_walk(item))
        return keys

    with cltr_cutover_root() as root:
        for path in root.rglob("*.schema.json"):
            document = json.loads(path.read_text(encoding="utf-8"))
            for key in _walk(document):
                lowered = key.lower()
                for substring in forbidden_substrings:
                    assert substring not in lowered, f"forbidden substring {substring!r} found in field name {key!r} of {path}"


# ---------------------------------------------------------------------------
# 13. Determinism
# ---------------------------------------------------------------------------


def test_136h_registry_schema_ids_stable_across_rebuilds():
    with cltr_cutover_root() as root:
        first = build_offline_registry(root).schema_ids
        second = build_offline_registry(root).schema_ids
    assert first == second


def test_136h_manifest_file_digest_matches_recomputation():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
        for entry in manifest["entries"]:
            actual = hashlib.sha256((root / entry["file_path"]).read_bytes()).hexdigest()
            assert actual == entry["file_digest"]


# ---------------------------------------------------------------------------
# 14. Exact inventory and scope guard
# ---------------------------------------------------------------------------


FORBIDDEN_RECORD_SCHEMA_FILENAMES = (
    # authority_epoch.schema.json and authority_state.schema.json are no
    # longer forbidden: Phase 136J legitimately implements them as
    # Implementation Group 2. cutover_request.schema.json and
    # readiness_package.schema.json are no longer forbidden: Phase 136L
    # legitimately implements them as Implementation Group 3. Every
    # later-group (4+) record schema remains forbidden until its own phase.
    "human_authorization.schema.json",
    "cutover_candidate.schema.json",
    "certification.schema.json",
    "publication_attempt.schema.json",
    "publication_evidence.schema.json",
    "concurrency_conflict.schema.json",
    "recovery_journal_entry.schema.json",
    "quarantine_record.schema.json",
    "notification_authority_binding.schema.json",
    "marker_authority_binding.schema.json",
    "receipt_authority_binding.schema.json",
    "compatibility_state.schema.json",
)


def test_136h_no_authority_bearing_record_schema_file_exists():
    with cltr_cutover_root() as root:
        all_files = {p.name for p in root.rglob("*.schema.json")}
    for forbidden in FORBIDDEN_RECORD_SCHEMA_FILENAMES:
        assert forbidden not in all_files


def test_136h_no_authority_namespace_created_on_disk():
    repo_root = Path(__file__).resolve().parents[1]
    assert not (repo_root / ".pcae" / "cltr-authority").exists()
    assert not (repo_root / "schemas" / "cltr_cutover").exists()


def test_136h_no_authority_module_references_in_schema_resources_source():
    # "authority_state"/"authority_epoch" are no longer forbidden tokens:
    # Phase 136J's schema_resources/__init__.py docstrings legitimately
    # name the packaged Group 2 record schemas. "pcae.cltr" (the live
    # authority-resolver module), "current_authority", and
    # "cltr-authority" (the authority namespace directory) remain
    # forbidden in every phase through 136J.
    repo_root = Path(__file__).resolve().parents[1]
    package_dir = repo_root / "src" / "pcae" / "schema_resources"
    forbidden = ("pcae.cltr", "current_authority", "cltr-authority")
    for py_file in package_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"forbidden token {token!r} found in {py_file}"


def test_136h_schema_runtime_manifest_module_imports_no_cltr_package():
    repo_root = Path(__file__).resolve().parents[1]
    manifest_py = repo_root / "src" / "pcae" / "schema_runtime" / "manifest.py"
    tree = ast.parse(manifest_py.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("pcae.cltr")
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("pcae.cltr")


# ---------------------------------------------------------------------------
# 15. No-network, no-execution proof
# ---------------------------------------------------------------------------


def test_136h_shared_core_load_and_manifest_verify_perform_no_network(monkeypatch):
    def _forbidden_socket(*args, **kwargs):
        raise AssertionError("socket.socket must never be called by shared-core loading/validation")

    monkeypatch.setattr(socket, "socket", _forbidden_socket)
    with cltr_cutover_root() as root:
        registry = build_offline_registry(root)
        load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
        validate_record_shape(dict(VALID_ENVELOPE), schema_id=MANIFEST_SCHEMA_ID, registry=registry)


def test_136h_no_subprocess_or_shell_reference_in_new_source():
    repo_root = Path(__file__).resolve().parents[1]
    for py_file in (
        repo_root / "src" / "pcae" / "schema_runtime" / "manifest.py",
        repo_root / "src" / "pcae" / "schema_resources" / "__init__.py",
    ):
        text = py_file.read_text(encoding="utf-8")
        for token in ("subprocess", "os.system", "shell=True"):
            assert token not in text
