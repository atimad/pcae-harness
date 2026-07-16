"""Phase 136L: Request and Readiness Schema Implementation (Implementation Group 3).

Focused tests for the packaged ``src/pcae/schema_resources/cltr_cutover/records``
Group 3 record schemas -- ``cutover_request.schema.json`` and
``readiness_package.schema.json`` -- plus their manifest entries, registry
integration, creation-order/non-circularity, reference-family separation,
local conditional validation, unknown-field strictness, and the exact scope
guard proving no later-group (Group 4+) record schema, binding, view, typed
model, semantic validator, or authority resolver/state/pointer was
introduced.

Every schema here validates SHAPE only. No test in this module creates,
reads, or asserts anything about live CLTR authority, migration state,
readiness truth, human authorization, or production lifecycle behavior.
Legacy lifecycle remains the sole production authority; CLTR remains
derivative.
"""
from __future__ import annotations

import ast
import copy
import json
import socket
from pathlib import Path

import pytest

from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import (
    ManifestIntegrityError,
    OutcomeStatus,
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

GROUP2_RECORD_FILES = (
    "records/authority_epoch.schema.json",
    "records/authority_state.schema.json",
)

RECORD_FILES = (
    "records/cutover_request.schema.json",
    "records/readiness_package.schema.json",
)

CUTOVER_REQUEST_ID = BASE_ID + "records/cutover_request.schema.json"
READINESS_PACKAGE_ID = BASE_ID + "records/readiness_package.schema.json"
AUTHORITY_EPOCH_ID = BASE_ID + "records/authority_epoch.schema.json"

LATER_GROUP_RECORD_FILES = (
    "records/human_authorization.schema.json",
    "records/cutover_candidate.schema.json",
    "records/certification.schema.json",
    "records/publication_attempt.schema.json",
    "records/publication_evidence.schema.json",
    "records/concurrency_conflict.schema.json",
    "records/recovery_journal_entry.schema.json",
    "records/quarantine_record.schema.json",
    "records/notification_authority_binding.schema.json",
    "records/marker_authority_binding.schema.json",
    "records/receipt_authority_binding.schema.json",
    "records/compatibility_state.schema.json",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _epoch_ref(record_id="authepoch-0000001", digest="b" * 64, family="authority_epoch"):
    return {"record_id": record_id, "record_digest": digest, "record_family": family}


def _readiness_ref(record_id="readypkg-0000001", digest="a" * 64, family="readiness_package"):
    return {
        "record_id": record_id,
        "record_digest": digest,
        "record_family": family,
        "schema_id": READINESS_PACKAGE_ID,
        "schema_version": "1.0",
    }


def _valid_readiness_package(**overrides) -> dict:
    record = {
        "schema_id": READINESS_PACKAGE_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "readiness_package",
        "record_id": "readypkg-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T12:00:00Z",
        "phase_id": "136L",
        "transition_id": "trans-00000001",
        "migration_epoch": "epoch-001",
        "evidence_references": [],
        "prerequisite_status": "unknown",
        "findings": [],
        "state": "unknown",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_cutover_request(**overrides) -> dict:
    record = {
        "schema_id": CUTOVER_REQUEST_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "cutover_request",
        "record_id": "cutreq-00000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T12:00:00Z",
        "phase_id": "136L",
        "migration_epoch": "epoch-001",
        "target": "cltr",
        "source_authority": "legacy",
        "source_epoch": _epoch_ref("authepoch-0000001", "b" * 64),
        "target_epoch": _epoch_ref("authepoch-0000002", "c" * 64),
        "evidence_requirements": [],
        "readiness_package_reference": _readiness_ref(),
        "authorization_requirement": True,
        "final_revision": "rev-001",
        "state": "pending",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


@pytest.fixture(scope="module")
def registry():
    with cltr_cutover_root() as root:
        yield build_offline_registry(root)


def _validate(record, schema_id, registry):
    return validate_record_shape(record, schema_id=schema_id, registry=registry)


# ---------------------------------------------------------------------------
# 1. Package integrity / exact scope guard
# ---------------------------------------------------------------------------


def test_136l_exact_group1_plus_group2_plus_group3_file_inventory():
    with cltr_cutover_root() as root:
        schema_files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.schema.json"))
    assert schema_files == sorted(
        ("manifest.schema.json",) + SHARED_FILES + GROUP2_RECORD_FILES + RECORD_FILES
    )


def test_136l_no_bindings_or_views_directory_exists():
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


def test_136l_records_directory_contains_exactly_four_files():
    with cltr_cutover_root() as root:
        files = sorted(p.name for p in (root / "records").glob("*.schema.json"))
    assert files == [
        "authority_epoch.schema.json",
        "authority_state.schema.json",
        "cutover_request.schema.json",
        "readiness_package.schema.json",
    ]


@pytest.mark.parametrize("relative_path", LATER_GROUP_RECORD_FILES)
def test_136l_no_later_group_record_schema_exists(relative_path):
    with cltr_cutover_root() as root:
        assert not (root / relative_path).exists()


def test_136l_no_later_group_filename_tracked_anywhere_in_repository():
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_stems = (
        "human_authorization.schema",
        "cutover_candidate.schema",
        "certification.schema",
        "publication_attempt.schema",
        "publication_evidence.schema",
        "concurrency_conflict.schema",
        "recovery_journal_entry.schema",
        "quarantine_record.schema",
        "compatibility_state.schema",
    )
    hits = [
        path
        for path in tracked
        if any(stem in path for stem in forbidden_stems) and "docs/" not in path and path.endswith(".json")
    ]
    assert hits == []


def test_136l_no_typed_python_record_model_introduced():
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files", "src/pcae"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_names = ("cutover_request.py", "readiness_package.py", "authority_model.py", "typed_authority.py")
    hits = [path for path in tracked if Path(path).name in forbidden_names]
    assert hits == []


def test_136l_no_cltr_authority_namespace_directory_exists():
    repo_root = Path(__file__).resolve().parents[1]
    assert not (repo_root / ".pcae" / "cltr-authority").exists()


@pytest.mark.parametrize("relative_path", RECORD_FILES)
def test_136l_every_resource_declares_draft_2020_12(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("relative_path", RECORD_FILES)
def test_136l_every_resource_id_matches_frozen_namespace(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$id"] == BASE_ID + relative_path


def test_136l_registry_loads_exactly_twelve_resources_with_unique_ids(registry):
    assert len(registry.schema_ids) == 12
    assert len(set(registry.schema_ids)) == 12
    assert CUTOVER_REQUEST_ID in registry.schema_ids
    assert READINESS_PACKAGE_ID in registry.schema_ids


def test_136l_cutover_request_is_tier1_strict_no_extensions():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/cutover_request.schema.json").read_bytes())
    assert document["additionalProperties"] is False
    assert "_extensions" not in document.get("properties", {})


def test_136l_readiness_package_is_tier2_extensions_only():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    assert document["additionalProperties"] is False
    assert "_extensions" in document["properties"]


# ---------------------------------------------------------------------------
# 2. Manifest
# ---------------------------------------------------------------------------


def test_136l_manifest_verifies_cleanly():
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        manifest = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    assert len(manifest.entries) == 11
    assert {e.file_path for e in manifest.entries} == set(SHARED_FILES) | set(GROUP2_RECORD_FILES) | set(RECORD_FILES)


def test_136l_manifest_new_entries_are_group_three():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    request_entry = by_path["records/cutover_request.schema.json"]
    readiness_entry = by_path["records/readiness_package.schema.json"]
    assert request_entry["implementation_group"] == 3
    assert readiness_entry["implementation_group"] == 3
    assert request_entry["family"] == "cutover_request"
    assert readiness_entry["family"] == "readiness_package"
    assert request_entry["status"] == "frozen"
    assert readiness_entry["status"] == "frozen"
    assert request_entry["schema_id"] == CUTOVER_REQUEST_ID
    assert readiness_entry["schema_id"] == READINESS_PACKAGE_ID


def test_136l_manifest_group1_and_group2_entries_unchanged():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    shared_entries = [e for e in manifest["entries"] if e["family"] == "shared"]
    assert len(shared_entries) == 7
    assert all(e["implementation_group"] == 1 for e in shared_entries)
    group2_entries = [e for e in manifest["entries"] if e["family"] in ("authority_epoch", "authority_state")]
    assert len(group2_entries) == 2
    assert all(e["implementation_group"] == 2 for e in group2_entries)


def test_136l_manifest_entries_in_deterministic_sorted_order():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    paths = [e["file_path"] for e in manifest["entries"]]
    assert paths == sorted(paths)


def test_136l_manifest_entry_count_matches_group1_plus_2_plus_3_exactly():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    assert len(manifest["entries"]) == 11


def test_136l_manifest_detects_content_tamper_on_new_record(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    tampered = tmp_path / "records" / "cutover_request.schema.json"
    document = json.loads(tampered.read_bytes())
    document["title"] = "tampered"
    tampered.write_text(json.dumps(document), encoding="utf-8")

    reg = build_offline_registry(tmp_path)
    with pytest.raises(ManifestIntegrityError, match="does not match"):
        load_and_verify_manifest(
            tmp_path / "manifest.json",
            package_root=tmp_path,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136l_manifest_detects_missing_readiness_package_file(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    (tmp_path / "records" / "readiness_package.schema.json").unlink()

    with pytest.raises(Exception):
        reg = build_offline_registry(tmp_path)
        load_and_verify_manifest(
            tmp_path / "manifest.json",
            package_root=tmp_path,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def _copy_tree(source: Path, dest: Path) -> None:
    import shutil

    for item in source.rglob("*"):
        if item.is_file():
            target = dest / item.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


# ---------------------------------------------------------------------------
# 3. CutoverRequest -- valid branches
# ---------------------------------------------------------------------------


def test_136l_request_valid_minimal(registry):
    result = _validate(_valid_cutover_request(), CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.VALID


@pytest.mark.parametrize(
    "state",
    [
        "pending",
        "evidence_gathering",
        "ready",
        "authorized",
        "certified",
        "publication_pending",
        "published",
        "rejected",
        "withdrawn",
        "expired",
    ],
)
def test_136l_request_valid_every_state_value(registry, state):
    record = _valid_cutover_request(state=state)
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.VALID, f"state {state} should be a valid RequestState value"


def test_136l_request_valid_with_evidence_requirements(registry):
    record = _valid_cutover_request(evidence_requirements=["digest_mismatch", "stale_certification"])
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136l_request_valid_with_optional_reason_code(registry):
    record = _valid_cutover_request(state="rejected", reason_code="authority_ambiguous")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 4. CutoverRequest -- local conditional / adversarial shape
# ---------------------------------------------------------------------------


def test_136l_request_target_not_cltr_rejected(registry):
    record = _valid_cutover_request(target="legacy")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_source_authority_not_legacy_rejected(registry):
    record = _valid_cutover_request(source_authority="cltr")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_authorization_requirement_false_rejected(registry):
    record = _valid_cutover_request(authorization_requirement=False)
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_missing_readiness_package_reference_rejected(registry):
    record = _valid_cutover_request()
    del record["readiness_package_reference"]
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_readiness_reference_wrong_family_rejected(registry):
    record = _valid_cutover_request(
        readiness_package_reference=_readiness_ref(family="authority_epoch")
    )
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_readiness_reference_missing_schema_id_rejected(registry):
    record = _valid_cutover_request()
    del record["readiness_package_reference"]["schema_id"]
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_readiness_reference_missing_schema_version_rejected(registry):
    record = _valid_cutover_request()
    del record["readiness_package_reference"]["schema_version"]
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_source_epoch_wrong_family_rejected(registry):
    record = _valid_cutover_request(source_epoch=_epoch_ref(family="readiness_package"))
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_target_epoch_wrong_family_rejected(registry):
    record = _valid_cutover_request(target_epoch=_epoch_ref(family="cutover_request"))
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_missing_required_field_rejected(registry):
    for field in (
        "phase_id",
        "migration_epoch",
        "target",
        "source_authority",
        "source_epoch",
        "target_epoch",
        "evidence_requirements",
        "readiness_package_reference",
        "authorization_requirement",
        "final_revision",
        "state",
        "limitations",
        "authority_disclosure",
    ):
        record = _valid_cutover_request()
        record.pop(field)
        result = _validate(record, CUTOVER_REQUEST_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"missing {field} should be rejected"


def test_136l_request_unknown_top_level_field_rejected(registry):
    record = _valid_cutover_request(unexpected_field="smuggled")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_unknown_nested_field_in_readiness_reference_rejected(registry):
    record = _valid_cutover_request()
    record["readiness_package_reference"]["extra"] = "smuggled"
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_unknown_field_in_authority_disclosure_rejected(registry):
    record = _valid_cutover_request()
    record["authority_disclosure"]["extra"] = "x"
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_extensions_key_rejected_tier1(registry):
    record = _valid_cutover_request(_extensions={"k": "v"})
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_wrong_enum_state_rejected(registry):
    record = _valid_cutover_request(state="made_up")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_case_variant_state_rejected(registry):
    record = _valid_cutover_request(state="Pending")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_wrong_id_family_record_id_rejected(registry):
    record = _valid_cutover_request(record_id="Not-A-Valid-ID")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_malformed_digest_rejected(registry):
    record = _valid_cutover_request(record_digest="not-hex")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_uppercase_digest_rejected(registry):
    record = _valid_cutover_request(record_digest="A" * 64)
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_wrong_schema_version_rejected(registry):
    record = _valid_cutover_request(schema_version="not-a-version")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_wrong_contract_version_rejected(registry):
    record = _valid_cutover_request(contract_version="2.0")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_wrong_record_type_rejected(registry):
    record = _valid_cutover_request(record_type="readiness_package")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_null_evidence_requirements_rejected(registry):
    record = _valid_cutover_request(evidence_requirements=None)
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_unknown_reason_code_value_rejected(registry):
    record = _valid_cutover_request(evidence_requirements=["not_a_real_reason_code"])
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_authoritative_authority_role_forbidden(registry):
    record = _valid_cutover_request(
        authority_disclosure={"authority_role": "authoritative", "is_authoritative": False, "disclosure_text": "x"}
    )
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_is_authoritative_true_forbidden(registry):
    record = _valid_cutover_request(
        authority_disclosure={"authority_role": "derivative", "is_authoritative": True, "disclosure_text": "x"}
    )
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_forbidden_disclosure_vocabulary_rejected(registry):
    for forbidden in ("current_authority", "cutover_authorized", "cutover_complete", "published", "production_ready"):
        record = _valid_cutover_request(
            authority_disclosure={"authority_role": forbidden, "is_authoritative": False, "disclosure_text": "x"}
        )
        result = _validate(record, CUTOVER_REQUEST_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"{forbidden} must not be a valid authority_role"


def test_136l_request_oversized_limitations_rejected(registry):
    record = _valid_cutover_request(limitations=["x"] * 33)
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_traversal_like_migration_epoch_rejected(registry):
    record = _valid_cutover_request(migration_epoch="../../etc/passwd")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_path_separator_in_record_id_rejected(registry):
    record = _valid_cutover_request(record_id="cutreq/0000001")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_oversized_final_revision_rejected(registry):
    record = _valid_cutover_request(final_revision="x" * 257)
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_non_ascii_final_revision_rejected(registry):
    record = _valid_cutover_request(final_revision="révision")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_request_evidence_requirements_too_many_rejected(registry):
    from pcae.schema_resources import cltr_cutover_root as _root

    with _root() as root:
        enums_doc = json.loads((root / "shared/failures.schema.json").read_bytes())
    all_reason_codes = enums_doc["$defs"]["reason_code"]["enum"]
    record = _valid_cutover_request(evidence_requirements=list(all_reason_codes) + [all_reason_codes[0]])
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 5. ReadinessPackage -- valid branches
# ---------------------------------------------------------------------------


def test_136l_readiness_valid_minimal(registry):
    result = _validate(_valid_readiness_package(), READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID


@pytest.mark.parametrize("state", ["unknown", "stale", "partial", "ready"])
def test_136l_readiness_valid_non_conflict_states(registry, state):
    record = _valid_readiness_package(state=state)
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136l_readiness_valid_conflict_with_blocking_finding(registry):
    record = _valid_readiness_package(
        state="conflict",
        findings=[{"id": "f1", "verdict": "BLOCKING", "title": "unresolved conflict"}],
    )
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID


@pytest.mark.parametrize("status_value", ["unknown", "unmet", "met"])
def test_136l_readiness_valid_every_prerequisite_status(registry, status_value):
    record = _valid_readiness_package(prerequisite_status=status_value)
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID


@pytest.mark.parametrize("gate_value", ["eligible", "ineligible", "uncertain", "conflict"])
def test_136l_readiness_valid_optional_gate_result(registry, gate_value):
    record = _valid_readiness_package(gate_result=gate_value)
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136l_readiness_valid_with_evidence_references(registry):
    record = _valid_readiness_package(
        evidence_references=[_epoch_ref("authepoch-0000001", "b" * 64)]
    )
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136l_readiness_valid_with_extensions(registry):
    record = _valid_readiness_package(_extensions={"note": "informational"})
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 6. ReadinessPackage -- local conditional / adversarial shape
# ---------------------------------------------------------------------------


def test_136l_readiness_conflict_without_blocking_finding_rejected(registry):
    record = _valid_readiness_package(state="conflict")
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_conflict_with_only_non_blocking_finding_rejected(registry):
    record = _valid_readiness_package(
        state="conflict",
        findings=[{"id": "f1", "verdict": "NON-BLOCKING", "title": "minor issue"}],
    )
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_missing_required_field_rejected(registry):
    for field in (
        "phase_id",
        "transition_id",
        "migration_epoch",
        "evidence_references",
        "prerequisite_status",
        "findings",
        "state",
        "limitations",
        "authority_disclosure",
    ):
        record = _valid_readiness_package()
        record.pop(field)
        result = _validate(record, READINESS_PACKAGE_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"missing {field} should be rejected"


def test_136l_readiness_unknown_top_level_field_rejected(registry):
    record = _valid_readiness_package(unexpected_field="smuggled")
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_extensions_must_be_string_valued(registry):
    record = _valid_readiness_package(_extensions={"note": 123})
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_unknown_field_in_finding_rejected(registry):
    record = _valid_readiness_package(
        findings=[{"id": "f1", "verdict": "CONFIRMED", "title": "x", "extra": "smuggled"}]
    )
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_unknown_field_in_authority_disclosure_rejected(registry):
    record = _valid_readiness_package()
    record["authority_disclosure"]["extra"] = "x"
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_wrong_enum_state_rejected(registry):
    record = _valid_readiness_package(state="made_up")
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_wrong_enum_prerequisite_status_rejected(registry):
    record = _valid_readiness_package(prerequisite_status="maybe")
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_wrong_finding_verdict_rejected(registry):
    record = _valid_readiness_package(findings=[{"id": "f1", "verdict": "MAYBE", "title": "x"}])
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_case_variant_state_rejected(registry):
    record = _valid_readiness_package(state="Ready")
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_wrong_id_family_record_id_rejected(registry):
    record = _valid_readiness_package(record_id="Not-A-Valid-ID")
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_malformed_digest_rejected(registry):
    record = _valid_readiness_package(record_digest="not-hex")
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_wrong_transition_id_pattern_rejected(registry):
    record = _valid_readiness_package(transition_id="not-a-transition-id")
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_wrong_record_type_rejected(registry):
    record = _valid_readiness_package(record_type="cutover_request")
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_authoritative_authority_role_forbidden(registry):
    record = _valid_readiness_package(
        authority_disclosure={"authority_role": "authoritative", "is_authoritative": False, "disclosure_text": "x"}
    )
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_is_authoritative_true_forbidden(registry):
    record = _valid_readiness_package(
        authority_disclosure={"authority_role": "derivative", "is_authoritative": True, "disclosure_text": "x"}
    )
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_oversized_limitations_rejected(registry):
    record = _valid_readiness_package(limitations=["x"] * 33)
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_traversal_like_migration_epoch_rejected(registry):
    record = _valid_readiness_package(migration_epoch="../../etc/passwd")
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_evidence_reference_missing_family_rejected(registry):
    record = _valid_readiness_package(
        evidence_references=[{"record_id": "authepoch-0000001", "record_digest": "b" * 64}]
    )
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_readiness_evidence_reference_unknown_family_rejected(registry):
    record = _valid_readiness_package(
        evidence_references=[_epoch_ref(family="not_a_real_family")]
    )
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 7. Request/readiness creation-order and non-circularity
# ---------------------------------------------------------------------------


def test_136l_request_binds_to_independently_fixtured_readiness_package(registry):
    """Proves the BLOCKING-136D-1 repair is reflected in actual schema
    behavior: a readiness_package fixture, fixtured entirely on its own
    with no cutover_request in existence, is a valid target for a
    cutover_request's readiness_package_reference."""
    readiness = _valid_readiness_package(record_id="readypkg-0000042", record_digest="d" * 64)
    readiness_result = _validate(readiness, READINESS_PACKAGE_ID, registry)
    assert readiness_result.status is OutcomeStatus.VALID

    request = _valid_cutover_request(
        readiness_package_reference=_readiness_ref(record_id="readypkg-0000042", digest="d" * 64)
    )
    request_result = _validate(request, CUTOVER_REQUEST_ID, registry)
    assert request_result.status is OutcomeStatus.VALID


def test_136l_readiness_package_carries_no_cutover_request_reference_field():
    """ReadinessPackage's own field set (Sec.20) has no back-reference to
    any cutover_request -- confirming the repaired non-circular creation
    order (readiness_package first, cutover_request second) rather than
    merely asserting it in prose."""
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    properties = set(document["properties"])
    assert not any("request" in name for name in properties)


def test_136l_no_ref_from_readiness_package_into_cutover_request_schema():
    with cltr_cutover_root() as root:
        rp_text = (root / "records/readiness_package.schema.json").read_text(encoding="utf-8")
    assert "cutover_request.schema.json" not in rp_text


def test_136l_no_ref_from_cutover_request_into_readiness_package_schema_file():
    """cutover_request references readiness_package only via the opaque
    record_reference shape (id+digest+family), never via a live $ref into
    readiness_package.schema.json itself."""
    with cltr_cutover_root() as root:
        cr_text = (root / "records/cutover_request.schema.json").read_text(encoding="utf-8")
    assert '"$ref": "../records/readiness_package.schema.json' not in cr_text


def test_136l_request_readiness_reference_is_opaque_reference_not_ref_edge():
    with cltr_cutover_root() as root:
        cr = json.loads((root / "records/cutover_request.schema.json").read_bytes())
    rp_ref_def = cr["$defs"]["readiness_package_reference"]
    serialized = json.dumps(rp_ref_def)
    assert "references.schema.json" in serialized
    assert "readiness_package.schema.json" not in serialized


def test_136l_group3_no_ref_dependency_on_group2_record_files():
    """Sec.9.2/Sec.13 of the implementation plan: Group 3 depends only on
    Group 1 shared files, not on Group 2's authority_epoch/authority_state
    schema files via $ref (only via the generic record_reference shape,
    which is itself a Group 1 shared definition)."""
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    for path in RECORD_FILES:
        deps = by_path[path]["dependencies"]
        for dep in deps:
            dep_path = dep.replace(BASE_ID, "")
            assert dep_path.startswith("shared/"), (
                f"{path} depends on {dep_path!r}, which is not a Group 1 shared file"
            )


def test_136l_no_versioned_request_v2_concept_in_schema_fields():
    """No field name or $def anywhere in cutover_request.schema.json
    encodes a second, separately-versioned request document (the repaired
    non-circular model uses a single-version request, Sec.19.1)."""
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/cutover_request.schema.json").read_bytes())
    names = set(document.get("properties", {})) | set(document.get("$defs", {}))
    for name in names:
        lowered = name.lower()
        assert "v2" not in lowered
        assert "version_2" not in lowered


def test_136l_readiness_reference_family_not_substitutable_for_epoch_reference(registry):
    record = _valid_cutover_request(
        source_epoch=_readiness_ref(record_id="readypkg-0000001", digest="a" * 64)
    )
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136l_epoch_reference_family_not_substitutable_for_readiness_reference(registry):
    record = _valid_cutover_request(
        readiness_package_reference={
            "record_id": "authepoch-0000001",
            "record_digest": "b" * 64,
            "record_family": "authority_epoch",
            "schema_id": AUTHORITY_EPOCH_ID,
            "schema_version": "1.0",
        }
    )
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 8. No-authority / no-execution proof
# ---------------------------------------------------------------------------


def test_136l_no_subprocess_shell_socket_or_dynamic_execution_in_new_files():
    with cltr_cutover_root() as root:
        pass
    repo_root = Path(__file__).resolve().parents[1]
    for relative in RECORD_FILES:
        json_path = repo_root / "src" / "pcae" / "schema_resources" / "cltr_cutover" / relative
        assert json_path.suffix == ".json"  # these are data files, not code

    forbidden_names = {"subprocess", "eval", "exec", "socket"}
    for py_file in (repo_root / "src" / "pcae" / "schema_resources").rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in forbidden_names, f"{py_file}: {alias.name}"
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden_names, f"{py_file}: {node.module}"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec"}, f"{py_file}: {node.func.id}(...)"


def test_136l_no_network_during_registry_and_validation(monkeypatch):
    calls = []

    def _blocked(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Network access attempted during offline schema operations")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)

    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
        _validate(_valid_cutover_request(), CUTOVER_REQUEST_ID, reg)
        _validate(_valid_readiness_package(), READINESS_PACKAGE_ID, reg)

    assert calls == []


def test_136l_validation_never_mutates_input_record(registry):
    record = _valid_cutover_request()
    before = copy.deepcopy(record)
    _validate(record, CUTOVER_REQUEST_ID, registry)
    assert record == before

    record2 = _valid_readiness_package()
    before2 = copy.deepcopy(record2)
    _validate(record2, READINESS_PACKAGE_ID, registry)
    assert record2 == before2


def test_136l_no_request_or_readiness_persistence_directory_created(tmp_path, registry):
    before = set(tmp_path.iterdir())
    _validate(_valid_cutover_request(), CUTOVER_REQUEST_ID, registry)
    _validate(_valid_readiness_package(), READINESS_PACKAGE_ID, registry)
    after = set(tmp_path.iterdir())
    assert before == after


def test_136l_no_authority_resolver_symbol_referenced_in_new_schema_text():
    with cltr_cutover_root() as root:
        cr_text = (root / "records/cutover_request.schema.json").read_text(encoding="utf-8")
        rp_text = (root / "records/readiness_package.schema.json").read_text(encoding="utf-8")
    for text in (cr_text, rp_text):
        assert "resolve_authority" not in text
        assert "AuthorityResolver" not in text


# ---------------------------------------------------------------------------
# 9. Determinism
# ---------------------------------------------------------------------------


def test_136l_registry_schema_ids_stable_across_repeated_builds():
    with cltr_cutover_root() as root1:
        reg1 = build_offline_registry(root1)
    with cltr_cutover_root() as root2:
        reg2 = build_offline_registry(root2)
    assert reg1.schema_ids == reg2.schema_ids


def test_136l_manifest_digests_stable_across_repeated_loads():
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        m1 = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
        m2 = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    assert m1.entries == m2.entries
