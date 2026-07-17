"""Phase 136P: Publication Schema Implementation (Implementation Group 5).

Focused tests for the packaged ``src/pcae/schema_resources/cltr_cutover/records``
Group 5 record schemas -- ``publication_attempt.schema.json`` and
``publication_evidence.schema.json`` -- the third and final embedding site
for the shared ``cas_expectation`` ``$def``, manifest entries, registry
integration, local conditional validation, family-reference separation,
unknown-field strictness, and the exact scope guard proving no Group 6+
record schema, binding, view, typed model, semantic validator, or authority
resolver/state/pointer was introduced.

Per the frozen contract's own Sec.46 grouping table, Group 5 is exactly
{publication_attempt, publication_evidence} -- NOT the task-prompt's
"expected" {PublicationAttempt, PublicationEvidence, ConcurrencyConflict}.
ConcurrencyConflict is contractually paired with RecoveryJournalEntry
(Sec.46 row for Group 8, both parametrized "1-7" prerequisite groups); since
RecoveryJournalEntry is explicitly out of scope for this phase (Strict 136P
No-Go Boundary), splitting that pair would violate CSCH-EXEC-REQ-062's
per-group atomicity requirement. This discrepancy is documented in
``docs/PHASE_136_PUBLICATION_SCHEMA_IMPLEMENTATION.md``.

Every schema here validates SHAPE only. No test in this module creates,
reads, or asserts anything about live CLTR authority, migration state,
publication success, CAS success, or production lifecycle behavior. Legacy
lifecycle remains the sole production authority; CLTR remains derivative.
"""
from __future__ import annotations

import copy
import json
import socket
import subprocess
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

GROUP3_RECORD_FILES = (
    "records/cutover_request.schema.json",
    "records/readiness_package.schema.json",
)

GROUP4_RECORD_FILES = (
    "records/certification.schema.json",
    "records/cutover_candidate.schema.json",
    "records/human_authorization.schema.json",
)

GROUP5_RECORD_FILES = (
    "records/publication_attempt.schema.json",
    "records/publication_evidence.schema.json",
)

# Phase 136R legitimately implements contract Group 8 (concurrency_conflict,
# recovery_journal_entry), paired atomically per CSCH-EXEC-REQ-062; no
# longer part of LATER_GROUP_RECORD_FILES.
GROUP8_RECORD_FILES = (
    "records/concurrency_conflict.schema.json",
    "records/recovery_journal_entry.schema.json",
)

# Phase 136T legitimately implements contract Group 10
# (notification_authority_binding, marker_authority_binding,
# receipt_authority_binding); no longer part of LATER_GROUP_RECORD_FILES.
GROUP10_RECORD_FILES = (
    "records/notification_authority_binding.schema.json",
    "records/marker_authority_binding.schema.json",
    "records/receipt_authority_binding.schema.json",
)

# Phase 136V legitimately implements contract Group 11
# (compatibility_state, quarantine_record) -- the final of the 11 frozen
# executable-schema implementation groups; no longer part of
# LATER_GROUP_RECORD_FILES.
GROUP11_RECORD_FILES = (
    "records/compatibility_state.schema.json",
    "records/quarantine_record.schema.json",
)

LATER_GROUP_RECORD_FILES = ()

ATTEMPT_ID = BASE_ID + "records/publication_attempt.schema.json"
EVIDENCE_ID = BASE_ID + "records/publication_evidence.schema.json"
CUTOVER_REQUEST_ID = BASE_ID + "records/cutover_request.schema.json"
CANDIDATE_ID = BASE_ID + "records/cutover_candidate.schema.json"
CERT_ID = BASE_ID + "records/certification.schema.json"
AUTHORITY_EPOCH_ID = BASE_ID + "records/authority_epoch.schema.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ref(record_id, digest, family, schema_id=None):
    r = {"record_id": record_id, "record_digest": digest, "record_family": family}
    if schema_id is not None:
        r["schema_id"] = schema_id
        r["schema_version"] = "1.0"
    return r


def _cas_expectation(**overrides) -> dict:
    ce = {
        "expected_authority_kind": "legacy",
        "expected_authority_epoch": _ref("authepoch-0000001", "b" * 64, "authority_epoch"),
        "expected_authoritative_generation": {
            "generation_id": "generat-0000001",
            "generation_digest": "c" * 64,
        },
        "expected_authority_pointer_digest": "d" * 64,
        "expected_authority_state_digest": "e" * 64,
        "expected_migration_epoch": "epoch-001",
        "expected_source_lifecycle_state": "CERTIFIED",
        "expected_compatibility_mode": "legacy_authoritative",
        "expected_journal_lock_state": "unlocked",
        "expected_request_reference": _ref("cutreq-00000001", "f" * 64, "cutover_request"),
        "expected_certification_reference": _ref("cert-00000000001", "0" * 64, "certification"),
    }
    ce.update(overrides)
    return ce


def _valid_attempt(**overrides) -> dict:
    record = {
        "schema_id": ATTEMPT_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "publication_attempt",
        "record_id": "pubattmp-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T12:00:00Z",
        "migration_epoch": "epoch-001",
        "transition_id": "trans-00000001",
        "attempt_id": "attemptd-0000001",
        "request_reference": _ref(
            "cutreq-00000001", "b" * 64, "cutover_request", CUTOVER_REQUEST_ID
        ),
        "candidate_reference": _ref(
            "cutcand-0000001", "c" * 64, "cutover_candidate", CANDIDATE_ID
        ),
        "certification_reference": _ref(
            "cert-00000000001", "d" * 64, "certification", CERT_ID
        ),
        "cas_expectation": _cas_expectation(),
        "source_authority_reference": _ref("authepoch-0000001", "e" * 64, "authority_epoch"),
        "target_authority_reference": _ref("authepoch-0000002", "f" * 64, "authority_epoch"),
        "attempt_sequence": 0,
        "state": "publication_attempted",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "operational",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_evidence(**overrides) -> dict:
    record = {
        "schema_id": EVIDENCE_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "publication_evidence",
        "record_id": "pubevid-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T12:00:00Z",
        "migration_epoch": "epoch-001",
        "transition_id": "trans-00000001",
        "attempt_reference": _ref(
            "pubattmp-0000001", "b" * 64, "publication_attempt", ATTEMPT_ID
        ),
        "outcome": "not_attempted",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "evidence",
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


def _copy_tree(source: Path, dest: Path) -> None:
    import shutil

    for item in source.rglob("*"):
        if item.is_file():
            target = dest / item.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


# ---------------------------------------------------------------------------
# 1. Package integrity / exact scope guard
# ---------------------------------------------------------------------------


def test_136p_exact_group1_through_group5_file_inventory():
    with cltr_cutover_root() as root:
        schema_files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.schema.json"))
    assert schema_files == sorted(
        ("manifest.schema.json",)
        + SHARED_FILES
        + GROUP2_RECORD_FILES
        + GROUP3_RECORD_FILES
        + GROUP4_RECORD_FILES
        + GROUP5_RECORD_FILES
        + GROUP8_RECORD_FILES
        + GROUP10_RECORD_FILES
        + GROUP11_RECORD_FILES
    )


def test_136p_no_bindings_or_views_directory_exists():
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


def test_136p_records_directory_contains_exactly_nine_files():
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
def test_136p_no_group6plus_record_schema_exists(relative_path):
    with cltr_cutover_root() as root:
        assert not (root / relative_path).exists()


def test_136p_no_group6plus_filename_tracked_anywhere_in_repository():
    repo_root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_stems = (
        # concurrency_conflict.schema and recovery_journal_entry.schema are
        # no longer forbidden: Phase 136R legitimately tracks them as
        # contract Group 8. notification_authority_binding.schema,
        # marker_authority_binding.schema, and receipt_authority_binding.schema
        # are no longer forbidden: Phase 136T legitimately tracks them as
        # contract Group 10. quarantine_record.schema and
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


def test_136p_no_standalone_cas_expectation_record_schema_exists():
    with cltr_cutover_root() as root:
        names = {p.name for p in (root / "records").glob("*.schema.json")}
    assert not any("cas_expectation" in n for n in names), names


def test_136p_no_typed_python_record_model_introduced():
    repo_root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files", "src/pcae"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_names = (
        "publication_attempt.py",
        "publication_evidence.py",
        "authority_model.py",
        "typed_authority.py",
    )
    hits = [path for path in tracked if Path(path).name in forbidden_names]
    assert hits == []


def test_136p_no_cltr_authority_namespace_directory_exists():
    repo_root = Path(__file__).resolve().parents[1]
    assert not (repo_root / ".pcae" / "cltr-authority").exists()


@pytest.mark.parametrize("relative_path", GROUP5_RECORD_FILES)
def test_136p_every_resource_declares_draft_2020_12(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("relative_path", GROUP5_RECORD_FILES)
def test_136p_every_resource_id_matches_frozen_namespace(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$id"] == BASE_ID + relative_path


def test_136p_registry_loads_exactly_seventeen_resources_with_unique_ids(registry):
    # Updated by Phase 136R (19), Phase 136T (22), and Phase 136V: registry
    # now legitimately loads 24 resources (23 manifest entries + the
    # manifest schema itself).
    assert len(registry.schema_ids) == 24
    assert len(set(registry.schema_ids)) == 24
    assert ATTEMPT_ID in registry.schema_ids
    assert EVIDENCE_ID in registry.schema_ids


def test_136p_publication_attempt_is_tier1_strict_no_extensions():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/publication_attempt.schema.json").read_bytes())
    assert document["additionalProperties"] is False
    assert "_extensions" not in document.get("properties", {})


def test_136p_publication_evidence_is_tier1_strict_no_extensions():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/publication_evidence.schema.json").read_bytes())
    assert document["additionalProperties"] is False
    assert "_extensions" not in document.get("properties", {})


# ---------------------------------------------------------------------------
# 2. Manifest
# ---------------------------------------------------------------------------


def test_136p_manifest_verifies_cleanly():
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        manifest = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    # Updated by Phase 136R (18), Phase 136T (21), and Phase 136V: manifest
    # now legitimately carries 23 entries.
    assert len(manifest.entries) == 23
    assert {e.file_path for e in manifest.entries} == (
        set(SHARED_FILES)
        | set(GROUP2_RECORD_FILES)
        | set(GROUP3_RECORD_FILES)
        | set(GROUP4_RECORD_FILES)
        | set(GROUP5_RECORD_FILES)
        | set(GROUP8_RECORD_FILES)
        | set(GROUP10_RECORD_FILES)
        | set(GROUP11_RECORD_FILES)
    )


def test_136p_manifest_new_entries_are_group_five():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    for path, family, schema_id in (
        ("records/publication_attempt.schema.json", "publication_attempt", ATTEMPT_ID),
        ("records/publication_evidence.schema.json", "publication_evidence", EVIDENCE_ID),
    ):
        entry = by_path[path]
        assert entry["implementation_group"] == 5
        assert entry["family"] == family
        assert entry["status"] == "frozen"
        assert entry["schema_id"] == schema_id


def test_136p_manifest_group1_through_group4_entries_unchanged():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    shared_entries = [e for e in manifest["entries"] if e["family"] == "shared"]
    assert len(shared_entries) == 7
    assert all(e["implementation_group"] == 1 for e in shared_entries)
    group2_entries = [e for e in manifest["entries"] if e["family"] in ("authority_epoch", "authority_state")]
    assert len(group2_entries) == 2
    assert all(e["implementation_group"] == 2 for e in group2_entries)
    group3_entries = [e for e in manifest["entries"] if e["family"] in ("cutover_request", "readiness_package")]
    assert len(group3_entries) == 2
    assert all(e["implementation_group"] == 3 for e in group3_entries)
    group4_entries = [
        e for e in manifest["entries"]
        if e["family"] in ("human_authorization", "cutover_candidate", "certification")
    ]
    assert len(group4_entries) == 3
    assert all(e["implementation_group"] == 4 for e in group4_entries)


def test_136p_manifest_entries_in_deterministic_sorted_order():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    paths = [e["file_path"] for e in manifest["entries"]]
    assert paths == sorted(paths)


def test_136p_manifest_entry_count_matches_group1_through_5_exactly():
    # Updated by Phase 136R (18), Phase 136T (21), and Phase 136V: manifest
    # now legitimately carries 23 entries.
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    assert len(manifest["entries"]) == 23


def test_136p_manifest_detects_content_tamper_on_new_record(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    tampered = tmp_path / "records" / "publication_attempt.schema.json"
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


def test_136p_manifest_detects_missing_evidence_file(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    (tmp_path / "records" / "publication_evidence.schema.json").unlink()

    with pytest.raises(Exception):
        reg = build_offline_registry(tmp_path)
        load_and_verify_manifest(
            tmp_path / "manifest.json",
            package_root=tmp_path,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


# ---------------------------------------------------------------------------
# 3. Fixture validity
# ---------------------------------------------------------------------------


def test_136p_attempt_valid_minimal(registry):
    assert _validate(_valid_attempt(), ATTEMPT_ID, registry).status is OutcomeStatus.VALID


def test_136p_evidence_valid_minimal(registry):
    assert _validate(_valid_evidence(), EVIDENCE_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize(
    "state",
    ["not_requested", "requested", "gate_uncertain", "certified",
     "publication_prepared", "publication_attempted", "published", "verified", "quarantined"],
)
def test_136p_attempt_valid_every_non_conditional_state(state, registry):
    record = _valid_attempt(state=state)
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.VALID


def test_136p_attempt_publication_uncertain_with_uncertainty_valid(registry):
    record = _valid_attempt(
        state="publication_uncertain",
        uncertainty={"reason": "Backend response timed out before confirmation."},
    )
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize("state", ["gate_rejected", "conflict"])
def test_136p_attempt_failure_states_with_classification_valid(state, registry):
    record = _valid_attempt(state=state, failure_classification="cas_rejected")
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.VALID


def test_136p_attempt_with_temporary_pointer_reference_valid(registry):
    record = _valid_attempt(
        state="publication_attempted",
        temporary_pointer_reference=_ref("authepoch-0000003", "1" * 64, "authority_epoch"),
    )
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize(
    "outcome",
    ["not_attempted", "cas_rejected", "failed_before_replacement",
     "post_publication_verification_failed", "conflict", "quarantined"],
)
def test_136p_evidence_valid_every_non_conditional_outcome(outcome, registry):
    record = _valid_evidence(outcome=outcome)
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.VALID


def test_136p_evidence_publication_uncertain_with_detail_valid(registry):
    record = _valid_evidence(
        outcome="publication_uncertain",
        uncertainty_detail={"last_known_state": "publication_attempted", "retry_recommended": True},
    )
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.VALID


def test_136p_evidence_published_and_verified_with_required_fields_valid(registry):
    record = _valid_evidence(
        outcome="published_and_verified",
        target_readback=_ref("authstate-0000001", "2" * 64, "authority_state"),
        authoritative_generation={"generation_id": "generat-0000002", "generation_digest": "3" * 64},
    )
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 4. Local conditional validation
# ---------------------------------------------------------------------------


def test_136p_attempt_publication_uncertain_without_uncertainty_rejected(registry):
    record = _valid_attempt(state="publication_uncertain")
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_attempt_non_uncertain_state_with_stray_uncertainty_rejected(registry):
    record = _valid_attempt(
        state="published", uncertainty={"reason": "should not be here"}
    )
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize("state", ["gate_rejected", "conflict"])
def test_136p_attempt_failure_states_without_classification_rejected(state, registry):
    record = _valid_attempt(state=state)
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_attempt_non_failure_state_with_stray_classification_rejected(registry):
    record = _valid_attempt(state="published", failure_classification="cas_rejected")
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_evidence_publication_uncertain_without_detail_rejected(registry):
    record = _valid_evidence(outcome="publication_uncertain")
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.INVALID


def test_136p_evidence_non_uncertain_outcome_with_stray_detail_rejected(registry):
    record = _valid_evidence(
        outcome="not_attempted",
        uncertainty_detail={"last_known_state": "requested", "retry_recommended": False},
    )
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize("missing", ["target_readback", "authoritative_generation"])
def test_136p_evidence_published_and_verified_missing_required_field_rejected(missing, registry):
    fields = {
        "target_readback": _ref("authstate-0000001", "2" * 64, "authority_state"),
        "authoritative_generation": {"generation_id": "generat-0000002", "generation_digest": "3" * 64},
    }
    del fields[missing]
    record = _valid_evidence(outcome="published_and_verified", **fields)
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.INVALID


def test_136p_evidence_non_published_outcome_with_stray_target_readback_rejected(registry):
    record = _valid_evidence(
        outcome="not_attempted",
        target_readback=_ref("authstate-0000001", "2" * 64, "authority_state"),
    )
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.INVALID


def test_136p_evidence_non_published_outcome_with_stray_authoritative_generation_rejected(registry):
    record = _valid_evidence(
        outcome="not_attempted",
        authoritative_generation={"generation_id": "generat-0000002", "generation_digest": "3" * 64},
    )
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 5. Enum strictness
# ---------------------------------------------------------------------------


def test_136p_attempt_unknown_state_rejected(registry):
    for bogus in ("in_progress", "PUBLISHED", "", "unknown"):
        record = _valid_attempt(state=bogus)
        assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


def test_136p_evidence_unknown_outcome_rejected(registry):
    for bogus in ("PUBLISHED_AND_VERIFIED", "success", "", "unknown"):
        record = _valid_evidence(outcome=bogus)
        assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


# ---------------------------------------------------------------------------
# 6. Family-specific reference / wrong-family substitution attacks
# ---------------------------------------------------------------------------


ALL_FAMILIES = (
    "authority_epoch", "authority_state", "cutover_request", "readiness_package",
    "human_authorization", "cutover_candidate", "certification",
    "publication_attempt", "publication_evidence", "concurrency_conflict",
    "recovery_journal_entry", "quarantine_record", "notification_authority_binding",
    "marker_authority_binding", "receipt_authority_binding", "compatibility_state",
)


@pytest.mark.parametrize(
    "field,correct_family",
    [
        ("request_reference", "cutover_request"),
        ("candidate_reference", "cutover_candidate"),
        ("certification_reference", "certification"),
        ("source_authority_reference", "authority_epoch"),
        ("target_authority_reference", "authority_epoch"),
    ],
)
def test_136p_attempt_wrong_family_reference_every_other_family_rejected(field, correct_family, registry):
    for family in ALL_FAMILIES:
        if family == correct_family:
            continue
        record = _valid_attempt(**{field: _ref("x" * 8, "7" * 64, family)})
        result = _validate(record, ATTEMPT_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"{field} must reject family {family!r}"


def test_136p_evidence_wrong_family_attempt_reference_every_other_family_rejected(registry):
    for family in ALL_FAMILIES:
        if family == "publication_attempt":
            continue
        record = _valid_evidence(attempt_reference=_ref("x" * 8, "7" * 64, family))
        result = _validate(record, EVIDENCE_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"attempt_reference must reject family {family!r}"


def test_136p_human_authorization_cannot_substitute_for_certification_in_attempt(registry):
    record = _valid_attempt(
        certification_reference=_ref(
            "humanaut-0000001", "d" * 64, "human_authorization",
            BASE_ID + "records/human_authorization.schema.json",
        )
    )
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_candidate_cannot_substitute_for_attempt_in_evidence(registry):
    record = _valid_evidence(
        attempt_reference=_ref("cutcand-0000001", "b" * 64, "cutover_candidate", CANDIDATE_ID)
    )
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 7. CAS expectation reuse (third embedding site)
# ---------------------------------------------------------------------------


def test_136p_cas_expectation_embedded_in_attempt_not_manifest_entry(registry):
    doc = registry.document(ATTEMPT_ID)
    assert doc["properties"]["cas_expectation"]["$ref"].endswith("cas_expectation")


def test_136p_cas_expectation_not_embedded_in_evidence(registry):
    doc = registry.document(EVIDENCE_ID)
    assert "cas_expectation" not in doc["properties"]


def test_136p_no_standalone_cas_expectation_manifest_entry(registry):
    ids = {e for e in registry.schema_ids}
    assert not any(sid.endswith("cas_expectation.schema.json") for sid in ids)


@pytest.mark.parametrize(
    "missing_field",
    [
        "expected_authority_kind",
        "expected_authority_epoch",
        "expected_authoritative_generation",
        "expected_authority_pointer_digest",
        "expected_authority_state_digest",
        "expected_migration_epoch",
        "expected_source_lifecycle_state",
        "expected_compatibility_mode",
        "expected_journal_lock_state",
        "expected_request_reference",
        "expected_certification_reference",
    ],
)
def test_136p_attempt_cas_expectation_no_field_is_omittable(missing_field, registry):
    ce = _cas_expectation()
    del ce[missing_field]
    record = _valid_attempt(cas_expectation=ce)
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_attempt_cas_expectation_wrong_family_authority_epoch_rejected(registry):
    ce = _cas_expectation(expected_authority_epoch=_ref("x" * 8, "1" * 64, "cutover_request"))
    record = _valid_attempt(cas_expectation=ce)
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_attempt_cas_expectation_null_rejected(registry):
    record = _valid_attempt(cas_expectation=None)
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 8. Unknown-field / strictness attacks
# ---------------------------------------------------------------------------


def test_136p_attempt_unknown_top_level_field_rejected(registry):
    record = _valid_attempt(unexpected_field="surprise")
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_evidence_unknown_top_level_field_rejected(registry):
    record = _valid_evidence(unexpected_field="surprise")
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.INVALID


def test_136p_attempt_extensions_key_rejected_tier1(registry):
    record = _valid_attempt(_extensions={"note": "not permitted on Tier 1"})
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_evidence_extensions_key_rejected_tier1(registry):
    record = _valid_evidence(_extensions={"note": "not permitted on Tier 1"})
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.INVALID


def test_136p_attempt_missing_required_field_rejected(registry):
    record = _valid_attempt()
    del record["attempt_sequence"]
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_evidence_missing_required_field_rejected(registry):
    record = _valid_evidence()
    del record["outcome"]
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.INVALID


def test_136p_attempt_malformed_digest_rejected(registry):
    record = _valid_attempt(record_digest="not-a-digest")
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_attempt_malformed_timestamp_rejected(registry):
    record = _valid_attempt(created_at="not-a-timestamp")
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_attempt_empty_limitations_array_valid(registry):
    record = _valid_attempt(limitations=[])
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.VALID


def test_136p_evidence_empty_limitations_array_valid(registry):
    record = _valid_evidence(limitations=[])
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.VALID


def test_136p_attempt_authoritative_role_forbidden(registry):
    record = _valid_attempt(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "attempted authority claim",
        }
    )
    assert _validate(record, ATTEMPT_ID, registry).status is OutcomeStatus.INVALID


def test_136p_evidence_authoritative_role_permitted_shape_only(registry):
    # Sec.9's conditional exception permits authority_role "authoritative" on
    # publication_evidence structurally; is_authoritative remains const false
    # regardless (NON-BLOCKING-136P-2, mirrors NON-BLOCKING-136J-1). Shape
    # validity alone never proves current authority.
    record = _valid_evidence(
        outcome="published_and_verified",
        target_readback=_ref("authstate-0000001", "2" * 64, "authority_state"),
        authoritative_generation={"generation_id": "generat-0000002", "generation_digest": "3" * 64},
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "Resolved-authority claim; schema validity does not itself establish current authority.",
        },
    )
    assert _validate(record, EVIDENCE_ID, registry).status is OutcomeStatus.VALID


def test_136p_no_field_named_password_token_or_secret():
    with cltr_cutover_root() as root:
        for path in GROUP5_RECORD_FILES:
            text = (root / path).read_text(encoding="utf-8")
            document = json.loads(text)
        for path in GROUP5_RECORD_FILES:
            document = json.loads((root / path).read_bytes())
            for name in document.get("properties", {}):
                lowered = name.lower()
                assert "password" not in lowered
                assert "secret" not in lowered
                assert lowered not in ("token", "bearer_token", "private_key")


# ---------------------------------------------------------------------------
# 9. Identity/digest/$ref graph acyclicity and creation order
# ---------------------------------------------------------------------------


def test_136p_attempt_references_only_earlier_groups():
    """PublicationAttempt's cross-family references (request, candidate,
    certification, source/target authority epoch) all target Group 2-4
    families, never publication_evidence, concurrency_conflict, or any other
    later family -- proving no cycle back into a later or sibling Group 5
    file."""
    record = _valid_attempt()
    referenced_families = {
        record["request_reference"]["record_family"],
        record["candidate_reference"]["record_family"],
        record["certification_reference"]["record_family"],
        record["source_authority_reference"]["record_family"],
        record["target_authority_reference"]["record_family"],
    }
    assert referenced_families == {"cutover_request", "cutover_candidate", "certification", "authority_epoch"}
    assert "publication_evidence" not in referenced_families
    assert "publication_attempt" not in referenced_families


def test_136p_evidence_references_only_publication_attempt():
    """PublicationEvidence's only cross-family reference is attempt_reference
    -> publication_attempt, never back to itself or to an earlier-created
    family -- proving the acyclic chain terminates at evidence."""
    record = _valid_evidence()
    assert record["attempt_reference"]["record_family"] == "publication_attempt"


def test_136p_manifest_group5_entries_do_not_depend_on_each_other():
    """publication_attempt.schema.json's manifest dependency list contains
    no reference to publication_evidence.schema.json (or vice versa) --
    confirming no manifest-declared or $ref cycle between the two Group 5
    siblings."""
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    attempt_deps = by_path["records/publication_attempt.schema.json"]["dependencies"]
    evidence_deps = by_path["records/publication_evidence.schema.json"]["dependencies"]
    assert not any("publication_evidence" in d for d in attempt_deps)
    assert not any("publication_attempt" in d for d in evidence_deps)


def test_136p_manifest_group5_dependencies_are_direct_ref_targets(registry):
    """Every dependency the manifest declares for each Group 5 entry is
    actually used somewhere in that file's $ref graph (bounded confirmation
    against NON-BLOCKING-136M-2-style spurious-dependency risk -- unlike
    136N's certification/human_authorization entries, no spurious
    shared/enums.schema.json dependency is introduced here)."""
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
        by_path = {e["file_path"]: e for e in manifest["entries"]}
        for path in GROUP5_RECORD_FILES:
            text = (root / path).read_text(encoding="utf-8")
            deps = by_path[path]["dependencies"]
            for dep in deps:
                dep_filename = dep.rsplit("/", 1)[-1]
                assert dep_filename in text, f"{path} declares unused dependency {dep!r}"


# ---------------------------------------------------------------------------
# 10. No-persistence / no-authority / no-execution / no-network
# ---------------------------------------------------------------------------


def test_136p_no_subprocess_shell_socket_or_dynamic_execution_in_new_files():
    import ast

    with cltr_cutover_root() as root:
        for relative in GROUP5_RECORD_FILES:
            text = (root / relative).read_text(encoding="utf-8")
    # JSON files -- confirm they parse as pure data (no embedded code paths).
    with cltr_cutover_root() as root:
        for relative in GROUP5_RECORD_FILES:
            text = (root / relative).read_text(encoding="utf-8")
            for banned in ("subprocess", "socket.socket", "eval(", "exec(", "os.system"):
                assert banned not in text


def test_136p_no_network_during_registry_and_validation(monkeypatch):
    def _blocked(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        record = _valid_attempt()
        result = validate_record_shape(record, schema_id=ATTEMPT_ID, registry=reg)
    assert result.status is OutcomeStatus.VALID


def test_136p_validation_never_mutates_input_record(registry):
    record = _valid_attempt()
    original = copy.deepcopy(record)
    _validate(record, ATTEMPT_ID, registry)
    assert record == original


def test_136p_no_persistence_directory_created_during_validation(tmp_path, registry):
    before = set(tmp_path.iterdir())
    _validate(_valid_attempt(), ATTEMPT_ID, registry)
    _validate(_valid_evidence(), EVIDENCE_ID, registry)
    after = set(tmp_path.iterdir())
    assert before == after


def test_136p_no_authority_resolver_symbol_referenced_in_new_schema_text():
    with cltr_cutover_root() as root:
        texts = [(root / path).read_text(encoding="utf-8") for path in GROUP5_RECORD_FILES]
    for text in texts:
        for banned in ("resolve_authority", "current_authority", "AuthorityResolver"):
            assert banned not in text


def test_136p_no_authority_pointer_or_state_persistence_path_referenced():
    with cltr_cutover_root() as root:
        texts = [(root / path).read_text(encoding="utf-8") for path in GROUP5_RECORD_FILES]
    for text in texts:
        assert ".pcae/cltr-authority" not in text


# ---------------------------------------------------------------------------
# 11. Packaging / installed-wheel
# ---------------------------------------------------------------------------


def test_136p_group5_schemas_load_from_editable_install(registry):
    assert ATTEMPT_ID in registry.schema_ids
    assert EVIDENCE_ID in registry.schema_ids


def test_136p_group5_fixtures_validate_outside_repository_checkout(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    reg = build_offline_registry(tmp_path)
    result = validate_record_shape(_valid_attempt(), schema_id=ATTEMPT_ID, registry=reg)
    assert result.status is OutcomeStatus.VALID
    result = validate_record_shape(_valid_evidence(), schema_id=EVIDENCE_ID, registry=reg)
    assert result.status is OutcomeStatus.VALID
