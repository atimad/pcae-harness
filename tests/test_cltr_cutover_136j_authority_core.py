"""Phase 136J: Authority Core Schema Implementation (Implementation Group 2).

Focused tests for the packaged ``src/pcae/schema_resources/cltr_cutover/records``
Group 2 record schemas -- ``authority_epoch.schema.json`` and
``authority_state.schema.json`` -- plus their manifest entries, registry
integration, reference-family separation, local conditional validation,
unknown-field strictness, and the exact scope guard proving no later-group
(Group 3+) record schema, binding, view, typed model, semantic validator, or
authority resolver/state/pointer was introduced.

Every schema here validates SHAPE only. No test in this module creates,
reads, or asserts anything about live CLTR authority, migration state, or
production lifecycle behavior. Legacy lifecycle remains the sole production
authority; CLTR remains derivative.
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

RECORD_FILES = (
    "records/authority_epoch.schema.json",
    "records/authority_state.schema.json",
)

AUTHORITY_EPOCH_ID = BASE_ID + "records/authority_epoch.schema.json"
AUTHORITY_STATE_ID = BASE_ID + "records/authority_state.schema.json"

# Phase 136L legitimately implements Group 3 (cutover_request,
# readiness_package) as standalone files, and Phase 136N legitimately
# implements Group 4 (human_authorization, cutover_candidate,
# certification); none of these five is part of LATER_GROUP_RECORD_FILES
# any longer, but none is part of this module's own RECORD_FILES/
# AUTHORITY_*_ID constants either, which remain scoped to Group 2.
GROUP3_RECORD_FILES = (
    "records/cutover_request.schema.json",
    "records/readiness_package.schema.json",
)

GROUP4_RECORD_FILES = (
    "records/human_authorization.schema.json",
    "records/cutover_candidate.schema.json",
    "records/certification.schema.json",
)

# Phase 136P legitimately implements Group 5 (publication_attempt,
# publication_evidence) as standalone files; they are no longer part of
# LATER_GROUP_RECORD_FILES.
GROUP5_RECORD_FILES = (
    "records/publication_attempt.schema.json",
    "records/publication_evidence.schema.json",
)

# Phase 136R legitimately implements contract Group 8 (concurrency_conflict,
# recovery_journal_entry), paired atomically per CSCH-EXEC-REQ-062; they are
# no longer part of LATER_GROUP_RECORD_FILES.
GROUP8_RECORD_FILES = (
    "records/concurrency_conflict.schema.json",
    "records/recovery_journal_entry.schema.json",
)

# Phase 136T legitimately implements contract Group 10
# (notification_authority_binding, marker_authority_binding,
# receipt_authority_binding); they are no longer part of
# LATER_GROUP_RECORD_FILES.
GROUP10_RECORD_FILES = (
    "records/notification_authority_binding.schema.json",
    "records/marker_authority_binding.schema.json",
    "records/receipt_authority_binding.schema.json",
)

# Phase 136V legitimately implements contract Group 11
# (compatibility_state, quarantine_record) -- the final of the 11 frozen
# executable-schema implementation groups; they are no longer part of
# LATER_GROUP_RECORD_FILES.
GROUP11_RECORD_FILES = (
    "records/compatibility_state.schema.json",
    "records/quarantine_record.schema.json",
)

LATER_GROUP_RECORD_FILES = ()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _valid_epoch(**overrides) -> dict:
    record = {
        "schema_id": AUTHORITY_EPOCH_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "authority_epoch",
        "record_id": "authepoch-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T12:00:00Z",
        "migration_epoch": "epoch-001",
        "authority_kind": "legacy",
        "activation_state": "active",
        "predecessor_epoch": None,
        "generation_binding": {"generation_id": "gen-0000001", "generation_digest": "b" * 64},
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_state(**overrides) -> dict:
    record = {
        "schema_id": AUTHORITY_STATE_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "authority_state",
        "record_id": "authstate-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T12:00:00Z",
        "migration_epoch": "epoch-001",
        "transition_id": "trans-00000001",
        "active_authority_epoch": {
            "record_id": "authepoch-0000001",
            "record_digest": "a" * 64,
            "record_family": "authority_epoch",
        },
        "authority_kind": "cltr",
        "authoritative_generation": {"generation_id": "gen-0000001", "generation_digest": "b" * 64},
        "publication_evidence_reference": {
            "record_id": "pubevidence-0000001",
            "record_digest": "c" * 64,
            "record_family": "publication_evidence",
        },
        "pointer_digest": "d" * 64,
        "verification_state": "verified",
        "compatibility_mode": "legacy_adapter",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "Resolved-authority claim; schema validity does not itself establish current authority.",
        },
    }
    record.update(overrides)
    return record


@pytest.fixture(scope="module")
def registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def _validate(record, schema_id, registry):
    return validate_record_shape(record, schema_id=schema_id, registry=registry)


# ---------------------------------------------------------------------------
# 1. Package integrity / exact scope guard
# ---------------------------------------------------------------------------


def test_136j_exact_group1_plus_group2_file_inventory():
    # Updated by Phase 136L (Group 3) and Phase 136N (Group 4): this test's
    # own name is retained as historical Group-2-phase authorship context,
    # but it now verifies current repository state, matching this
    # repository's established convention (mirroring 136K's in-place
    # repair of 136I's own test).
    with cltr_cutover_root() as root:
        schema_files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.schema.json"))
    assert schema_files == sorted(
        ("manifest.schema.json",)
        + SHARED_FILES
        + RECORD_FILES
        + GROUP3_RECORD_FILES
        + GROUP4_RECORD_FILES
        + GROUP5_RECORD_FILES
        + GROUP8_RECORD_FILES
        + GROUP10_RECORD_FILES
        + GROUP11_RECORD_FILES
    )


def test_136j_no_bindings_or_views_directory_exists():
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


def test_136j_records_directory_contains_exactly_two_files():
    # Updated by Phase 136L (Group 3) and Phase 136N (Group 4): records/
    # now legitimately contains the two Group 2 files, the two Group 3
    # files, and the three Group 4 files (seven total).
    with cltr_cutover_root() as root:
        files = sorted(p.name for p in (root / "records").glob("*.schema.json"))
    assert files == [
        "authority_epoch.schema.json",
        "authority_state.schema.json",
        "certification.schema.json",
        "compatibility_state.schema.json",
        "concurrency_conflict.schema.json",
        "cutover_candidate.schema.json",
        "cutover_request.schema.json",
        "human_authorization.schema.json",
        "marker_authority_binding.schema.json",
        "notification_authority_binding.schema.json",
        "publication_attempt.schema.json",
        "publication_evidence.schema.json",
        "quarantine_record.schema.json",
        "readiness_package.schema.json",
        "receipt_authority_binding.schema.json",
        "recovery_journal_entry.schema.json",
    ]


@pytest.mark.parametrize("relative_path", LATER_GROUP_RECORD_FILES)
def test_136j_no_later_group_record_schema_exists(relative_path):
    with cltr_cutover_root() as root:
        assert not (root / relative_path).exists()


def test_136j_no_later_group_filename_tracked_anywhere_in_repository():
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_stems = (
        # cutover_request.schema and readiness_package.schema are no longer
        # forbidden: Phase 136L legitimately tracks them as Group 3.
        # human_authorization.schema, cutover_candidate.schema, and
        # certification.schema are no longer forbidden: Phase 136N
        # legitimately tracks them as Group 4.
        # publication_attempt.schema and publication_evidence.schema are no
        # longer forbidden: Phase 136P legitimately tracks them as Group 5.
        # concurrency_conflict.schema and recovery_journal_entry.schema are
        # no longer forbidden: Phase 136R legitimately tracks them as
        # contract Group 8. quarantine_record.schema and
        # compatibility_state.schema are no longer forbidden: Phase 136V
        # legitimately tracks them as contract Group 11 -- the final group.
        # Empty: no later group remains.
    )
    hits = [
        path
        for path in tracked
        if any(stem in path for stem in forbidden_stems) and "docs/" not in path and path.endswith(".json")
    ]
    assert hits == []


def test_136j_no_typed_python_record_model_introduced():
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files", "src/pcae"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_names = ("authority_epoch.py", "authority_state.py", "authority_model.py", "typed_authority.py")
    hits = [path for path in tracked if Path(path).name in forbidden_names]
    assert hits == []


def test_136j_no_cltr_authority_namespace_directory_exists():
    repo_root = Path(__file__).resolve().parents[1]
    assert not (repo_root / ".pcae" / "cltr-authority").exists()


@pytest.mark.parametrize("relative_path", RECORD_FILES)
def test_136j_every_resource_declares_draft_2020_12(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("relative_path", RECORD_FILES)
def test_136j_every_resource_id_matches_frozen_namespace(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$id"] == BASE_ID + relative_path


def test_136j_registry_loads_exactly_ten_resources_with_unique_ids(registry):
    # Updated by Phase 136L (12), Phase 136N (15), Phase 136P (17),
    # Phase 136R (19), Phase 136T (22), and Phase 136V: registry now
    # legitimately loads 24 resources (23 manifest entries + the manifest
    # schema itself), reflecting contract Group 11's 2 new record schemas.
    assert len(registry.schema_ids) == 24
    assert len(set(registry.schema_ids)) == 24
    assert AUTHORITY_EPOCH_ID in registry.schema_ids
    assert AUTHORITY_STATE_ID in registry.schema_ids


# ---------------------------------------------------------------------------
# 2. Manifest
# ---------------------------------------------------------------------------


def test_136j_manifest_verifies_cleanly():
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        manifest = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    # Updated by Phase 136L (11), Phase 136N (14), Phase 136P (16),
    # Phase 136R (18), Phase 136T (21), and Phase 136V: manifest now
    # legitimately carries 23 entries.
    assert len(manifest.entries) == 23
    assert {e.file_path for e in manifest.entries} == (
        set(SHARED_FILES)
        | set(RECORD_FILES)
        | set(GROUP3_RECORD_FILES)
        | set(GROUP4_RECORD_FILES)
        | set(GROUP5_RECORD_FILES)
        | set(GROUP8_RECORD_FILES)
        | set(GROUP10_RECORD_FILES)
        | set(GROUP11_RECORD_FILES)
    )


def test_136j_manifest_new_entries_are_group_two():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    epoch_entry = by_path["records/authority_epoch.schema.json"]
    state_entry = by_path["records/authority_state.schema.json"]
    assert epoch_entry["implementation_group"] == 2
    assert state_entry["implementation_group"] == 2
    assert epoch_entry["family"] == "authority_epoch"
    assert state_entry["family"] == "authority_state"
    assert epoch_entry["status"] == "frozen"
    assert state_entry["status"] == "frozen"
    assert epoch_entry["schema_id"] == AUTHORITY_EPOCH_ID
    assert state_entry["schema_id"] == AUTHORITY_STATE_ID


def test_136j_manifest_shared_entries_unchanged_group_one():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    shared_entries = [e for e in manifest["entries"] if e["family"] == "shared"]
    assert len(shared_entries) == 7
    assert all(e["implementation_group"] == 1 for e in shared_entries)


def test_136j_manifest_entries_in_deterministic_sorted_order():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    paths = [e["file_path"] for e in manifest["entries"]]
    assert paths == sorted(paths)


def test_136j_manifest_entry_count_matches_group1_plus_group2_exactly():
    # Updated by Phase 136L, Phase 136N, Phase 136P, and Phase 136R:
    # manifest now legitimately carries 18 entries (Group 1: 7, Group 2: 2,
    # Group 3: 2, Group 4: 3, Group 5: 2, Group 8: 2).
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    assert len(manifest["entries"]) == 23


def test_136j_manifest_detects_content_tamper_on_new_record(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    tampered = tmp_path / "records" / "authority_epoch.schema.json"
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


def test_136j_manifest_detects_missing_record_file(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    (tmp_path / "records" / "authority_state.schema.json").unlink()

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
# 3. AuthorityEpoch -- valid state branches
# ---------------------------------------------------------------------------


def test_136j_epoch_valid_active_with_binding(registry):
    result = _validate(_valid_epoch(), AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136j_epoch_valid_proposed_without_binding(registry):
    record = _valid_epoch(activation_state="proposed")
    record.pop("generation_binding")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136j_epoch_valid_superseded_without_binding(registry):
    record = _valid_epoch(activation_state="superseded")
    record.pop("generation_binding")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136j_epoch_valid_superseded_with_predecessor(registry):
    record = _valid_epoch(
        activation_state="superseded",
        predecessor_epoch={"record_id": "authepoch-0000000", "record_digest": "e" * 64, "record_family": "authority_epoch"},
    )
    record.pop("generation_binding")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136j_epoch_valid_cltr_kind(registry):
    result = _validate(_valid_epoch(authority_kind="cltr"), AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 4. AuthorityEpoch -- local conditional / adversarial shape
# ---------------------------------------------------------------------------


def test_136j_epoch_active_without_generation_binding_rejected(registry):
    record = _valid_epoch()
    record.pop("generation_binding")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_proposed_with_generation_binding_rejected(registry):
    record = _valid_epoch(activation_state="proposed")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_missing_required_field_rejected(registry):
    for field in (
        "migration_epoch",
        "authority_kind",
        "activation_state",
        "predecessor_epoch",
        "limitations",
        "authority_disclosure",
    ):
        record = _valid_epoch()
        record.pop(field)
        result = _validate(record, AUTHORITY_EPOCH_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"missing {field} should be rejected"


def test_136j_epoch_unknown_top_level_field_rejected(registry):
    record = _valid_epoch(unexpected_field="smuggled")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_unknown_nested_field_in_generation_binding_rejected(registry):
    record = _valid_epoch()
    record["generation_binding"]["extra"] = "smuggled"
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_unknown_field_in_authority_disclosure_rejected(registry):
    record = _valid_epoch()
    record["authority_disclosure"]["extra"] = "x"
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_wrong_enum_activation_state_rejected(registry):
    record = _valid_epoch(activation_state="deprecated")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_case_variant_activation_state_rejected(registry):
    record = _valid_epoch(activation_state="Active")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_wrong_id_family_record_id_rejected(registry):
    record = _valid_epoch(record_id="Not-A-Valid-ID")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_malformed_digest_rejected(registry):
    record = _valid_epoch(record_digest="not-hex")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_uppercase_digest_rejected(registry):
    record = _valid_epoch(record_digest="A" * 64)
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_wrong_schema_version_rejected(registry):
    record = _valid_epoch(schema_version="not-a-version")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_wrong_contract_version_rejected(registry):
    record = _valid_epoch(contract_version="2.0")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_wrong_record_type_rejected(registry):
    record = _valid_epoch(record_type="authority_state")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_null_vs_absent_predecessor_epoch(registry):
    record = _valid_epoch()
    record.pop("predecessor_epoch")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID, "predecessor_epoch is a required key, not optional"


def test_136j_epoch_wrong_reference_family_for_predecessor_rejected(registry):
    record = _valid_epoch(
        predecessor_epoch={"record_id": "cutreq-0000001", "record_digest": "e" * 64, "record_family": "cutover_request"}
    )
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_authoritative_authority_role_forbidden(registry):
    record = _valid_epoch(
        authority_disclosure={"authority_role": "authoritative", "is_authoritative": False, "disclosure_text": "x"}
    )
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_is_authoritative_true_forbidden(registry):
    record = _valid_epoch(
        authority_disclosure={"authority_role": "derivative", "is_authoritative": True, "disclosure_text": "x"}
    )
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_forbidden_disclosure_vocabulary_rejected(registry):
    for forbidden in ("current_authority", "production_authority", "cutover_complete"):
        record = _valid_epoch(
            authority_disclosure={"authority_role": forbidden, "is_authoritative": False, "disclosure_text": "x"}
        )
        result = _validate(record, AUTHORITY_EPOCH_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"{forbidden} must not be a valid authority_role"


def test_136j_epoch_oversized_limitations_rejected(registry):
    record = _valid_epoch(limitations=["x"] * 33)
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_traversal_like_migration_epoch_rejected(registry):
    record = _valid_epoch(migration_epoch="../../etc/passwd")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_path_separator_in_record_id_rejected(registry):
    record = _valid_epoch(record_id="authepoch/0000001")
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 5. AuthorityState -- valid state branches
# ---------------------------------------------------------------------------


def test_136j_state_valid_cltr_with_generation(registry):
    result = _validate(_valid_state(), AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136j_state_valid_legacy_without_generation(registry):
    record = _valid_state(authority_kind="legacy")
    record.pop("authoritative_generation")
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136j_state_valid_unverified_with_uncertainty(registry):
    record = _valid_state(verification_state="unverified", uncertainty={"reason": "pending independent recheck"})
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136j_state_valid_verification_failed_without_uncertainty(registry):
    record = _valid_state(verification_state="verification_failed")
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136j_state_valid_derivative_authority_role(registry):
    record = _valid_state(
        authority_disclosure={"authority_role": "derivative", "is_authoritative": False, "disclosure_text": "x"}
    )
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 6. AuthorityState -- local conditional / adversarial shape
# ---------------------------------------------------------------------------


def test_136j_state_cltr_without_generation_rejected(registry):
    record = _valid_state()
    record.pop("authoritative_generation")
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_verified_with_uncertainty_rejected(registry):
    record = _valid_state(uncertainty={"reason": "should not coexist with verified"})
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_unverified_without_uncertainty_rejected(registry):
    record = _valid_state(verification_state="unverified")
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_missing_required_field_rejected(registry):
    for field in (
        "migration_epoch",
        "transition_id",
        "active_authority_epoch",
        "authority_kind",
        "publication_evidence_reference",
        "pointer_digest",
        "verification_state",
        "compatibility_mode",
        "limitations",
        "authority_disclosure",
    ):
        record = _valid_state()
        record.pop(field)
        result = _validate(record, AUTHORITY_STATE_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"missing {field} should be rejected"


def test_136j_state_unknown_top_level_field_rejected(registry):
    record = _valid_state(unexpected_field="smuggled")
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_unknown_nested_field_in_uncertainty_rejected(registry):
    record = _valid_state(
        verification_state="unverified",
        uncertainty={"reason": "x", "extra": "smuggled"},
    )
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_wrong_enum_verification_state_rejected(registry):
    record = _valid_state(verification_state="approved")
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_wrong_enum_compatibility_mode_rejected(registry):
    record = _valid_state(compatibility_mode="cltr_authoritative")
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_case_variant_verification_state_rejected(registry):
    record = _valid_state(verification_state="Verified")
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_malformed_pointer_digest_rejected(registry):
    record = _valid_state(pointer_digest="not-hex")
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_wrong_transition_id_pattern_rejected(registry):
    record = _valid_state(transition_id="not-prefixed-correctly")
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_is_authoritative_true_forbidden_even_when_role_authoritative(registry):
    record = _valid_state(
        authority_disclosure={"authority_role": "authoritative", "is_authoritative": True, "disclosure_text": "x"}
    )
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_forbidden_disclosure_vocabulary_rejected(registry):
    for forbidden in ("current_authority", "production_authority", "cutover_complete"):
        record = _valid_state(
            authority_disclosure={"authority_role": forbidden, "is_authoritative": False, "disclosure_text": "x"}
        )
        result = _validate(record, AUTHORITY_STATE_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"{forbidden} must not be a valid authority_role"


def test_136j_state_oversized_limitations_rejected(registry):
    record = _valid_state(limitations=["x"] * 33)
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_secret_like_disclosure_text_rejected_when_over_bound(registry):
    record = _valid_state(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "x" * 501,
        }
    )
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 7. Reference-family separation
# ---------------------------------------------------------------------------


def test_136j_state_wrong_family_for_active_authority_epoch_rejected(registry):
    record = _valid_state(
        active_authority_epoch={
            "record_id": "cutreq-0000001",
            "record_digest": "a" * 64,
            "record_family": "cutover_request",
        }
    )
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_wrong_family_for_publication_evidence_reference_rejected(registry):
    record = _valid_state(
        publication_evidence_reference={
            "record_id": "authepoch-0000001",
            "record_digest": "a" * 64,
            "record_family": "authority_epoch",
        }
    )
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_state_readiness_package_reference_not_substitutable_for_publication_evidence(registry):
    record = _valid_state(
        publication_evidence_reference={
            "record_id": "readypkg-0000001",
            "record_digest": "a" * 64,
            "record_family": "readiness_package",
        }
    )
    result = _validate(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136j_epoch_generation_reference_shape_not_a_record_reference(registry):
    # generation_binding must be {generation_id, generation_digest}, never a
    # record_reference {record_id, record_digest, record_family} tuple.
    record = _valid_epoch(
        generation_binding={"record_id": "authepoch-0000002", "record_digest": "b" * 64, "record_family": "authority_epoch"}
    )
    result = _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 8. No-authority / no-execution proof
# ---------------------------------------------------------------------------


def test_136j_no_subprocess_shell_socket_or_dynamic_execution_in_new_files():
    with cltr_cutover_root() as root:
        pass
    repo_root = Path(__file__).resolve().parents[1]
    for relative in RECORD_FILES:
        py_equivalent = repo_root / "src" / "pcae" / "schema_resources" / "cltr_cutover" / relative
        assert py_equivalent.suffix == ".json"  # these are data files, not code

    # AST-walk schema_resources and schema_runtime for forbidden constructs,
    # matching the 136H/136I convention.
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


def test_136j_no_network_during_registry_and_validation(monkeypatch):
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
        _validate(_valid_epoch(), AUTHORITY_EPOCH_ID, reg)
        _validate(_valid_state(), AUTHORITY_STATE_ID, reg)

    assert calls == []


def test_136j_validation_never_mutates_input_record(registry):
    record = _valid_epoch()
    before = copy.deepcopy(record)
    _validate(record, AUTHORITY_EPOCH_ID, registry)
    assert record == before


def test_136j_no_authority_epoch_or_state_persistence_directory_created(tmp_path, registry):
    # Validating records must never write anything to disk.
    before = set(tmp_path.iterdir())
    _validate(_valid_epoch(), AUTHORITY_EPOCH_ID, registry)
    _validate(_valid_state(), AUTHORITY_STATE_ID, registry)
    after = set(tmp_path.iterdir())
    assert before == after


# ---------------------------------------------------------------------------
# 9. Determinism
# ---------------------------------------------------------------------------


def test_136j_registry_schema_ids_stable_across_repeated_builds():
    with cltr_cutover_root() as root:
        first = build_offline_registry(root).schema_ids
        second = build_offline_registry(root).schema_ids
    assert first == second


def test_136j_manifest_digests_stable_across_repeated_loads():
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        first = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
        second = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    assert first.entries == second.entries
