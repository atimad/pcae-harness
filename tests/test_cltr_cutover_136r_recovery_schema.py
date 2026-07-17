"""Phase 136R: Recovery Schema Implementation (Implementation Group 8).

Focused tests for the packaged ``src/pcae/schema_resources/cltr_cutover/records``
Group 8 record schemas -- ``concurrency_conflict.schema.json`` and
``recovery_journal_entry.schema.json`` -- manifest entries, registry
integration, local conditional validation, family-reference separation,
unknown-field strictness, and the exact scope guard proving no Group 9+
record schema, binding, view, typed model, semantic validator, or authority
resolver/state/pointer was introduced.

Per the frozen contract's own Sec.46 grouping table, Group 8 is exactly
{concurrency_conflict, recovery_journal_entry}, paired atomically per
CSCH-EXEC-REQ-062 -- NOT the task-prompt's textual framing, which asked for
a "recovery schema" while separately excluding ConcurrencyConflict by name.
Per explicit user confirmation obtained before this phase began coding, the
frozen contract governs: Group 8 is implemented in full. This discrepancy
is documented in ``docs/PHASE_136_RECOVERY_SCHEMA_IMPLEMENTATION.md``.

Every schema here validates SHAPE only. No test in this module creates,
reads, or asserts anything about live CLTR authority, migration state,
recovery success, reconciliation truth, quarantine, or production lifecycle
behavior. Legacy lifecycle remains the sole production authority; CLTR
remains derivative.
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

LATER_GROUP_RECORD_FILES = (
    "records/quarantine_record.schema.json",
    "records/compatibility_state.schema.json",
)

CONFLICT_ID = BASE_ID + "records/concurrency_conflict.schema.json"
JOURNAL_ID = BASE_ID + "records/recovery_journal_entry.schema.json"
CUTOVER_REQUEST_ID = BASE_ID + "records/cutover_request.schema.json"
AUTHORITY_STATE_ID = BASE_ID + "records/authority_state.schema.json"
PUBLICATION_ATTEMPT_ID = BASE_ID + "records/publication_attempt.schema.json"

ALL_FAMILIES = (
    "authority_epoch", "authority_state", "cutover_request", "readiness_package",
    "human_authorization", "cutover_candidate", "certification",
    "publication_attempt", "publication_evidence", "concurrency_conflict",
    "recovery_journal_entry", "quarantine_record", "notification_authority_binding",
    "marker_authority_binding", "receipt_authority_binding", "compatibility_state",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ref(record_id, digest, family, schema_id=None):
    r = {"record_id": record_id, "record_digest": digest, "record_family": family}
    if schema_id is not None:
        r["schema_id"] = schema_id
        r["schema_version"] = "1.0"
    return r


def _valid_conflict(**overrides) -> dict:
    record = {
        "schema_id": CONFLICT_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "concurrency_conflict",
        "record_id": "concconf-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-17T12:00:00Z",
        "migration_epoch": "epoch-001",
        "actors": [
            "operator@example.test",
            _ref("pubattmp-0000001", "b" * 64, "publication_attempt"),
        ],
        "requests": [_ref("cutreq-00000001", "c" * 64, "cutover_request", CUTOVER_REQUEST_ID)],
        "type": "dual_writer",
        "winner": None,
        "recovery_requirement": "none_required",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "operational",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_journal_entry(**overrides) -> dict:
    record = {
        "schema_id": JOURNAL_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "recovery_journal_entry",
        "record_id": "recjrnl-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-17T12:00:00Z",
        "migration_epoch": "epoch-001",
        "transition_id": "trans-00000001",
        "sequence": 0,
        "prior_entry_digest": None,
        "operation_reference": _ref("cutreq-00000001", "b" * 64, "cutover_request"),
        "prior_state_reference": _ref("authstate-0000001", "c" * 64, "authority_state"),
        "new_state_reference": _ref("authstate-0000002", "d" * 64, "authority_state"),
        "authority_state_reference": _ref(
            "authstate-0000001", "e" * 64, "authority_state", AUTHORITY_STATE_ID
        ),
        "generation_reference": {"generation_id": "generat-0000001", "generation_digest": "f" * 64},
        "external_effect_state": "none",
        "retry_replay_classification": "original",
        "state": "recorded",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "operational",
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


def test_136r_exact_group1_through_group8_file_inventory():
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
    )


def test_136r_no_bindings_or_views_directory_exists():
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


def test_136r_records_directory_contains_exactly_eleven_files():
    with cltr_cutover_root() as root:
        files = sorted(p.name for p in (root / "records").glob("*.schema.json"))
    assert files == [
        "authority_epoch.schema.json",
        "authority_state.schema.json",
        "certification.schema.json",
        "concurrency_conflict.schema.json",
        "cutover_candidate.schema.json",
        "cutover_request.schema.json",
        "human_authorization.schema.json",
        "marker_authority_binding.schema.json",
        "notification_authority_binding.schema.json",
        "publication_attempt.schema.json",
        "publication_evidence.schema.json",
        "readiness_package.schema.json",
        "receipt_authority_binding.schema.json",
        "recovery_journal_entry.schema.json",
    ]


@pytest.mark.parametrize("relative_path", LATER_GROUP_RECORD_FILES)
def test_136r_no_group9plus_record_schema_exists(relative_path):
    with cltr_cutover_root() as root:
        assert not (root / relative_path).exists()


def test_136r_no_group9plus_filename_tracked_anywhere_in_repository():
    repo_root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_stems = (
        "quarantine_record.schema",
        "notification_authority_binding.schema",
        "marker_authority_binding.schema",
        "receipt_authority_binding.schema",
        "compatibility_state.schema",
        "reconciliation_result.schema",
        "historical_authority_reference.schema",
    )
    hits = [
        path
        for path in tracked
        if any(stem in path for stem in forbidden_stems) and "docs/" not in path and path.endswith(".json")
    ]
    assert hits == []


def test_136r_no_standalone_cas_expectation_record_schema_exists():
    with cltr_cutover_root() as root:
        names = {p.name for p in (root / "records").glob("*.schema.json")}
    assert not any("cas_expectation" in n for n in names), names


def test_136r_no_typed_python_record_model_introduced():
    repo_root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files", "src/pcae"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_names = (
        "concurrency_conflict.py",
        "recovery_journal_entry.py",
        "authority_model.py",
        "typed_authority.py",
    )
    hits = [path for path in tracked if Path(path).name in forbidden_names]
    assert hits == []


def test_136r_no_cltr_authority_namespace_directory_exists():
    repo_root = Path(__file__).resolve().parents[1]
    assert not (repo_root / ".pcae" / "cltr-authority").exists()


@pytest.mark.parametrize("relative_path", GROUP8_RECORD_FILES)
def test_136r_every_resource_declares_draft_2020_12(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("relative_path", GROUP8_RECORD_FILES)
def test_136r_every_resource_id_matches_frozen_namespace(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$id"] == BASE_ID + relative_path


def test_136r_registry_loads_exactly_nineteen_resources_with_unique_ids(registry):
    assert len(registry.schema_ids) == 22
    assert len(set(registry.schema_ids)) == 22
    assert CONFLICT_ID in registry.schema_ids
    assert JOURNAL_ID in registry.schema_ids


def test_136r_concurrency_conflict_is_tier2_extensions_only():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/concurrency_conflict.schema.json").read_bytes())
    assert document["additionalProperties"] is False
    assert "_extensions" in document["properties"]
    assert document["properties"]["_extensions"]["additionalProperties"] == {"type": "string"}


def test_136r_recovery_journal_entry_is_tier2_extensions_only():
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/recovery_journal_entry.schema.json").read_bytes())
    assert document["additionalProperties"] is False
    assert "_extensions" in document["properties"]
    assert document["properties"]["_extensions"]["additionalProperties"] == {"type": "string"}


# ---------------------------------------------------------------------------
# 2. Manifest
# ---------------------------------------------------------------------------


def test_136r_manifest_verifies_cleanly():
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        manifest = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    assert len(manifest.entries) == 21
    assert {e.file_path for e in manifest.entries} == (
        set(SHARED_FILES)
        | set(GROUP2_RECORD_FILES)
        | set(GROUP3_RECORD_FILES)
        | set(GROUP4_RECORD_FILES)
        | set(GROUP5_RECORD_FILES)
        | set(GROUP8_RECORD_FILES)
        | set(GROUP10_RECORD_FILES)
    )


def test_136r_manifest_new_entries_are_group_eight():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    for path, family, schema_id in (
        ("records/concurrency_conflict.schema.json", "concurrency_conflict", CONFLICT_ID),
        ("records/recovery_journal_entry.schema.json", "recovery_journal_entry", JOURNAL_ID),
    ):
        entry = by_path[path]
        assert entry["implementation_group"] == 8
        assert entry["family"] == family
        assert entry["status"] == "frozen"
        assert entry["schema_id"] == schema_id


def test_136r_manifest_group1_through_group5_entries_unchanged():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    shared_entries = [e for e in manifest["entries"] if e["family"] == "shared"]
    assert len(shared_entries) == 7
    assert all(e["implementation_group"] == 1 for e in shared_entries)
    group5_entries = [e for e in manifest["entries"] if e["family"] in ("publication_attempt", "publication_evidence")]
    assert len(group5_entries) == 2
    assert all(e["implementation_group"] == 5 for e in group5_entries)


def test_136r_manifest_entries_in_deterministic_sorted_order():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    paths = [e["file_path"] for e in manifest["entries"]]
    assert paths == sorted(paths)


def test_136r_manifest_entry_count_matches_group1_through_8_exactly():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    assert len(manifest["entries"]) == 21


def test_136r_manifest_detects_content_tamper_on_new_record(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    tampered = tmp_path / "records" / "concurrency_conflict.schema.json"
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


def test_136r_manifest_detects_missing_evidence_file(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    (tmp_path / "records" / "recovery_journal_entry.schema.json").unlink()

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


def test_136r_conflict_valid_minimal(registry):
    assert _validate(_valid_conflict(), CONFLICT_ID, registry).status is OutcomeStatus.VALID


def test_136r_journal_entry_valid_minimal(registry):
    assert _validate(_valid_journal_entry(), JOURNAL_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize("conflict_type", ["dual_writer", "stale_expectation", "unknown_winner"])
def test_136r_conflict_valid_every_non_cas_mismatch_type(conflict_type, registry):
    record = _valid_conflict(type=conflict_type)
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.VALID


def test_136r_conflict_cas_mismatch_with_expected_and_observed_state_valid(registry):
    record = _valid_conflict(
        type="cas_mismatch",
        expected_state=_ref("authstate-0000001", "1" * 64, "authority_state"),
        observed_state=_ref("authstate-0000002", "2" * 64, "authority_state"),
    )
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.VALID


def test_136r_conflict_winner_present_non_null_valid(registry):
    record = _valid_conflict(winner=_ref("pubattmp-0000001", "3" * 64, "publication_attempt"))
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize(
    "recovery_requirement",
    [
        "none_required", "resume_safe", "retry_required", "operator_review_required",
        "reconciliation_required", "quarantine_required", "conflict_unresolved",
        "publication_uncertain_unresolved", "terminal_recovered", "terminal_unrecoverable",
    ],
)
def test_136r_conflict_valid_every_recovery_state(recovery_requirement, registry):
    record = _valid_conflict(recovery_requirement=recovery_requirement)
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize("state", ["recorded", "reviewed", "actioned", "superseded"])
def test_136r_journal_entry_valid_every_state_with_required_conditionals(state, registry):
    overrides = {"state": state}
    if state in ("reviewed", "actioned", "superseded"):
        overrides["operator_review"] = {"notes": "Operator reviewed this entry."}
    if state == "actioned":
        overrides["recovery_action"] = {"description": "Resumed publication retry."}
    record = _valid_journal_entry(**overrides)
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.VALID


def test_136r_journal_entry_nonzero_sequence_with_digest_valid(registry):
    record = _valid_journal_entry(sequence=1, prior_entry_digest="4" * 64)
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.VALID


def test_136r_journal_entry_with_publication_attempt_reference_valid(registry):
    record = _valid_journal_entry(
        publication_attempt_reference=_ref(
            "pubattmp-0000001", "5" * 64, "publication_attempt", PUBLICATION_ATTEMPT_ID
        )
    )
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize("effect_state", ["none", "pending", "applied", "unknown"])
def test_136r_journal_entry_valid_every_external_effect_state(effect_state, registry):
    record = _valid_journal_entry(external_effect_state=effect_state)
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize("classification", ["original", "retry", "replay"])
def test_136r_journal_entry_valid_every_retry_replay_classification(classification, registry):
    record = _valid_journal_entry(retry_replay_classification=classification)
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 4. Local conditional validation
# ---------------------------------------------------------------------------


def test_136r_conflict_cas_mismatch_without_expected_observed_rejected(registry):
    record = _valid_conflict(type="cas_mismatch")
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_conflict_cas_mismatch_missing_only_observed_state_rejected(registry):
    record = _valid_conflict(
        type="cas_mismatch",
        expected_state=_ref("authstate-0000001", "1" * 64, "authority_state"),
    )
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_conflict_non_cas_mismatch_with_stray_expected_state_rejected(registry):
    record = _valid_conflict(
        type="dual_writer",
        expected_state=_ref("authstate-0000001", "1" * 64, "authority_state"),
    )
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_conflict_winner_absent_key_rejected(registry):
    record = _valid_conflict()
    del record["winner"]
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_sequence_zero_with_nonnull_prior_digest_rejected(registry):
    record = _valid_journal_entry(sequence=0, prior_entry_digest="9" * 64)
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_nonzero_sequence_with_null_prior_digest_rejected(registry):
    record = _valid_journal_entry(sequence=1, prior_entry_digest=None)
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_prior_entry_digest_absent_key_rejected(registry):
    record = _valid_journal_entry()
    del record["prior_entry_digest"]
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize("state", ["reviewed", "actioned", "superseded"])
def test_136r_journal_entry_reviewed_or_later_without_operator_review_rejected(state, registry):
    overrides = {"state": state}
    if state == "actioned":
        overrides["recovery_action"] = {"description": "x"}
    record = _valid_journal_entry(**overrides)
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_recorded_with_stray_operator_review_rejected(registry):
    record = _valid_journal_entry(state="recorded", operator_review={"notes": "premature"})
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_actioned_without_recovery_action_rejected(registry):
    record = _valid_journal_entry(state="actioned", operator_review={"notes": "reviewed"})
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_non_actioned_with_stray_recovery_action_rejected(registry):
    record = _valid_journal_entry(
        state="reviewed",
        operator_review={"notes": "reviewed"},
        recovery_action={"description": "premature"},
    )
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 5. Enum strictness
# ---------------------------------------------------------------------------


def test_136r_conflict_unknown_type_rejected(registry):
    for bogus in ("CAS_MISMATCH", "", "unknown", "dualwriter"):
        record = _valid_conflict(type=bogus)
        assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


def test_136r_conflict_unknown_recovery_state_rejected(registry):
    for bogus in ("NONE_REQUIRED", "", "unknown"):
        record = _valid_conflict(recovery_requirement=bogus)
        assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


def test_136r_journal_entry_unknown_state_rejected(registry):
    for bogus in ("RECORDED", "", "unknown", "closed"):
        record = _valid_journal_entry(state=bogus)
        assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


def test_136r_journal_entry_unknown_external_effect_state_rejected(registry):
    for bogus in ("NONE", "", "not_a_value", "partial"):
        record = _valid_journal_entry(external_effect_state=bogus)
        assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


def test_136r_journal_entry_unknown_retry_replay_classification_rejected(registry):
    for bogus in ("ORIGINAL", "", "unknown", "duplicate"):
        record = _valid_journal_entry(retry_replay_classification=bogus)
        assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


# ---------------------------------------------------------------------------
# 6. Family-specific reference / wrong-family substitution attacks
# ---------------------------------------------------------------------------


def test_136r_conflict_requests_wrong_family_every_other_family_rejected(registry):
    for family in ALL_FAMILIES:
        if family == "cutover_request":
            continue
        record = _valid_conflict(requests=[_ref("x" * 8, "7" * 64, family)])
        result = _validate(record, CONFLICT_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"requests must reject family {family!r}"


@pytest.mark.parametrize("field,correct_family", [("authority_state_reference", "authority_state")])
def test_136r_journal_entry_wrong_family_reference_every_other_family_rejected(field, correct_family, registry):
    for family in ALL_FAMILIES:
        if family == correct_family:
            continue
        record = _valid_journal_entry(**{field: _ref("x" * 8, "7" * 64, family)})
        result = _validate(record, JOURNAL_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"{field} must reject family {family!r}"


def test_136r_journal_entry_publication_attempt_reference_wrong_family_rejected(registry):
    for family in ALL_FAMILIES:
        if family == "publication_attempt":
            continue
        record = _valid_journal_entry(publication_attempt_reference=_ref("x" * 8, "7" * 64, family))
        result = _validate(record, JOURNAL_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"publication_attempt_reference must reject family {family!r}"


def test_136r_human_authorization_cannot_substitute_for_authority_state_in_journal_entry(registry):
    record = _valid_journal_entry(
        authority_state_reference=_ref(
            "humanaut-0000001", "d" * 64, "human_authorization",
            BASE_ID + "records/human_authorization.schema.json",
        )
    )
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_conflict_actors_accepts_both_shapes_and_rejects_neither(registry):
    record = _valid_conflict(actors=["operator@example.test", "second.operator@example.test"])
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.VALID
    record2 = _valid_conflict(
        actors=[
            _ref("pubattmp-0000001", "1" * 64, "publication_attempt"),
            _ref("pubattmp-0000002", "2" * 64, "publication_attempt"),
        ]
    )
    assert _validate(record2, CONFLICT_ID, registry).status is OutcomeStatus.VALID


def test_136r_conflict_actors_malformed_entry_rejected(registry):
    record = _valid_conflict(actors=[123, "operator@example.test"])
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_conflict_actors_too_few_entries_rejected(registry):
    record = _valid_conflict(actors=["only.one@example.test"])
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_conflict_requests_empty_array_rejected(registry):
    record = _valid_conflict(requests=[])
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 7. Unknown-field / strictness attacks
# ---------------------------------------------------------------------------


def test_136r_conflict_unknown_top_level_field_rejected(registry):
    record = _valid_conflict(unexpected_field="surprise")
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_unknown_top_level_field_rejected(registry):
    record = _valid_journal_entry(unexpected_field="surprise")
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_conflict_extensions_key_valid_tier2(registry):
    record = _valid_conflict(_extensions={"note": "permitted on Tier 2"})
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.VALID


def test_136r_journal_entry_extensions_key_valid_tier2(registry):
    record = _valid_journal_entry(_extensions={"note": "permitted on Tier 2"})
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.VALID


def test_136r_conflict_extensions_non_string_value_rejected(registry):
    record = _valid_conflict(_extensions={"note": 123})
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_extensions_non_string_value_rejected(registry):
    record = _valid_journal_entry(_extensions={"note": 123})
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_conflict_missing_required_field_rejected(registry):
    record = _valid_conflict()
    del record["type"]
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_missing_required_field_rejected(registry):
    record = _valid_journal_entry()
    del record["sequence"]
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_conflict_malformed_digest_rejected(registry):
    record = _valid_conflict(record_digest="not-a-digest")
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_malformed_digest_rejected(registry):
    record = _valid_journal_entry(record_digest="not-a-digest")
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_conflict_malformed_timestamp_rejected(registry):
    record = _valid_conflict(created_at="not-a-timestamp")
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_malformed_timestamp_rejected(registry):
    record = _valid_journal_entry(created_at="not-a-timestamp")
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_conflict_empty_limitations_array_valid(registry):
    record = _valid_conflict(limitations=[])
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.VALID


def test_136r_journal_entry_empty_limitations_array_valid(registry):
    record = _valid_journal_entry(limitations=[])
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.VALID


def test_136r_conflict_authoritative_role_forbidden(registry):
    record = _valid_conflict(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "attempted authority claim",
        }
    )
    assert _validate(record, CONFLICT_ID, registry).status is OutcomeStatus.INVALID


def test_136r_journal_entry_authoritative_role_forbidden(registry):
    record = _valid_journal_entry(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "attempted authority claim",
        }
    )
    assert _validate(record, JOURNAL_ID, registry).status is OutcomeStatus.INVALID


def test_136r_no_field_named_password_token_or_secret():
    with cltr_cutover_root() as root:
        for path in GROUP8_RECORD_FILES:
            document = json.loads((root / path).read_bytes())
            for name in document.get("properties", {}):
                lowered = name.lower()
                assert "password" not in lowered
                assert "secret" not in lowered
                assert lowered not in ("token", "bearer_token", "private_key")


# ---------------------------------------------------------------------------
# 8. Identity/digest/$ref graph acyclicity and creation order
# ---------------------------------------------------------------------------


def test_136r_conflict_references_only_earlier_groups():
    """ConcurrencyConflict's cross-family references (requests, winner as
    used here) target Group 3/5 families, never a Group 9+ family -- proving
    no forward cycle."""
    record = _valid_conflict(winner=_ref("pubattmp-0000001", "1" * 64, "publication_attempt"))
    referenced_families = {r["record_family"] for r in record["requests"]}
    referenced_families.add(record["winner"]["record_family"])
    assert referenced_families <= {"cutover_request", "publication_attempt"}
    assert "quarantine_record" not in referenced_families
    assert "compatibility_state" not in referenced_families


def test_136r_journal_entry_references_only_earlier_groups():
    """RecoveryJournalEntry's cross-family references (authority_state,
    publication_attempt) target Groups 2 and 5/7, never a Group 9+ family."""
    record = _valid_journal_entry(
        publication_attempt_reference=_ref("pubattmp-0000001", "1" * 64, "publication_attempt")
    )
    referenced_families = {
        record["authority_state_reference"]["record_family"],
        record["publication_attempt_reference"]["record_family"],
    }
    assert referenced_families == {"authority_state", "publication_attempt"}


def test_136r_journal_entry_hash_chain_is_strictly_backward_referencing():
    """sequence == 0 has a null prior_entry_digest (no predecessor to
    reference); a non-zero sequence's prior_entry_digest points strictly
    backward (to an earlier entry's own digest), never forward or to
    itself -- non-circular by construction."""
    genesis = _valid_journal_entry(sequence=0, prior_entry_digest=None)
    assert genesis["prior_entry_digest"] is None
    successor = _valid_journal_entry(sequence=1, prior_entry_digest=genesis["record_digest"])
    assert successor["prior_entry_digest"] == genesis["record_digest"]
    assert successor["sequence"] > genesis["sequence"]


def test_136r_conflict_and_journal_entry_do_not_reference_each_other():
    """Neither Group 8 sibling's field table names the other family --
    confirming no manifest-declared or $ref cycle between them."""
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    conflict_deps = by_path["records/concurrency_conflict.schema.json"]["dependencies"]
    journal_deps = by_path["records/recovery_journal_entry.schema.json"]["dependencies"]
    assert not any("recovery_journal_entry" in d for d in conflict_deps)
    assert not any("concurrency_conflict" in d for d in journal_deps)


def test_136r_manifest_group8_dependencies_are_direct_ref_targets(registry):
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
        by_path = {e["file_path"]: e for e in manifest["entries"]}
        for path in GROUP8_RECORD_FILES:
            text = (root / path).read_text(encoding="utf-8")
            deps = by_path[path]["dependencies"]
            for dep in deps:
                dep_filename = dep.rsplit("/", 1)[-1]
                assert dep_filename in text, f"{path} declares unused dependency {dep!r}"


# ---------------------------------------------------------------------------
# 9. No-persistence / no-authority / no-execution / no-network / no-recovery
# ---------------------------------------------------------------------------


def test_136r_no_subprocess_shell_socket_or_dynamic_execution_in_new_files():
    with cltr_cutover_root() as root:
        for relative in GROUP8_RECORD_FILES:
            text = (root / relative).read_text(encoding="utf-8")
            for banned in ("subprocess", "socket.socket", "eval(", "exec(", "os.system"):
                assert banned not in text


def test_136r_no_network_during_registry_and_validation(monkeypatch):
    def _blocked(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        result = validate_record_shape(_valid_conflict(), schema_id=CONFLICT_ID, registry=reg)
    assert result.status is OutcomeStatus.VALID


def test_136r_validation_never_mutates_input_record(registry):
    record = _valid_journal_entry()
    original = copy.deepcopy(record)
    _validate(record, JOURNAL_ID, registry)
    assert record == original


def test_136r_no_persistence_directory_created_during_validation(tmp_path, registry):
    before = set(tmp_path.iterdir())
    _validate(_valid_conflict(), CONFLICT_ID, registry)
    _validate(_valid_journal_entry(), JOURNAL_ID, registry)
    after = set(tmp_path.iterdir())
    assert before == after


def test_136r_no_authority_resolver_symbol_referenced_in_new_schema_text():
    with cltr_cutover_root() as root:
        texts = [(root / path).read_text(encoding="utf-8") for path in GROUP8_RECORD_FILES]
    for text in texts:
        for banned in ("resolve_authority", "current_authority", "AuthorityResolver"):
            assert banned not in text


def test_136r_no_authority_pointer_or_state_persistence_path_referenced():
    with cltr_cutover_root() as root:
        texts = [(root / path).read_text(encoding="utf-8") for path in GROUP8_RECORD_FILES]
    for text in texts:
        assert ".pcae/cltr-authority" not in text


def test_136r_no_recovery_coordinator_or_retry_executor_symbol_referenced():
    with cltr_cutover_root() as root:
        texts = [(root / path).read_text(encoding="utf-8") for path in GROUP8_RECORD_FILES]
    for text in texts:
        for banned in (
            "RecoveryCoordinator", "RetryExecutor", "PointerRepair",
            "ReconciliationEngine", "QuarantineEnforcer", "ConflictResolver",
        ):
            assert banned not in text


# ---------------------------------------------------------------------------
# 10. Packaging / installed-wheel
# ---------------------------------------------------------------------------


def test_136r_group8_schemas_load_from_editable_install(registry):
    assert CONFLICT_ID in registry.schema_ids
    assert JOURNAL_ID in registry.schema_ids


def test_136r_group8_fixtures_validate_outside_repository_checkout(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    reg = build_offline_registry(tmp_path)
    result = validate_record_shape(_valid_conflict(), schema_id=CONFLICT_ID, registry=reg)
    assert result.status is OutcomeStatus.VALID
    result = validate_record_shape(_valid_journal_entry(), schema_id=JOURNAL_ID, registry=reg)
    assert result.status is OutcomeStatus.VALID
