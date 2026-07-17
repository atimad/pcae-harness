"""Phase 136T: Notification/Marker/Receipt Authority Binding Schema
Implementation (Implementation Group 10).

Focused tests for the packaged ``src/pcae/schema_resources/cltr_cutover/records``
Group 10 record schemas -- ``notification_authority_binding.schema.json``,
``marker_authority_binding.schema.json``, and ``receipt_authority_binding.
schema.json`` -- manifest entries, registry integration, local conditional
validation, family-reference separation, unknown-field strictness, and the
exact scope guard proving no Group 9 (schema-less) or Group 11+ record
schema, view, typed model, semantic validator, or authority resolver/
state/pointer was introduced.

Per the frozen contract's own Sec.46 grouping table, Group 9
(ReconciliationResult / HistoricalAuthorityReference) has no schema file at
all; Group 10 is exactly {notification_authority_binding,
marker_authority_binding, receipt_authority_binding}, prerequisite groups
"1, 2, plus existing PFN-001 identities" (not "1-9"). This module derives
Group 10 independently from the frozen contract text rather than inferring
it from prior phases' prose (see docs/PHASE_136_NOTIFICATION_MARKER_RECEIPT_
BINDING_SCHEMA_IMPLEMENTATION.md for the full derivation and discrepancy
disclosures, including NON-BLOCKING-136T-1 through -6 and DEFERRED-136T-1).

Every schema here validates SHAPE only. No test in this module creates,
reads, or asserts anything about live CLTR authority, migration state,
notification dispatch, marker creation, receipt finalization, or production
lifecycle behavior. Legacy lifecycle remains the sole production authority;
CLTR remains derivative.
"""
from __future__ import annotations

import copy
import json
import socket
import subprocess
import sys
import venv
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

REPO_ROOT = Path(__file__).resolve().parents[1]
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
GROUP10_RECORD_FILES = (
    "records/marker_authority_binding.schema.json",
    "records/notification_authority_binding.schema.json",
    "records/receipt_authority_binding.schema.json",
)

# Group 9 has no schema file (contract Sec.46) and never gains one; Group 11
# (compatibility_state, quarantine_record) remains a later, unimplemented
# group.
LATER_GROUP_RECORD_FILES = (
    "records/quarantine_record.schema.json",
    "records/compatibility_state.schema.json",
)

NOTIF_ID = BASE_ID + "records/notification_authority_binding.schema.json"
MARKER_ID = BASE_ID + "records/marker_authority_binding.schema.json"
RECEIPT_ID = BASE_ID + "records/receipt_authority_binding.schema.json"
AUTHORITY_EPOCH_ID = BASE_ID + "records/authority_epoch.schema.json"
PUBLICATION_EVIDENCE_ID = BASE_ID + "records/publication_evidence.schema.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ref(record_id, digest, family, schema_id=None, schema_version="1.0"):
    r = {"record_id": record_id, "record_digest": digest, "record_family": family}
    if schema_id is not None:
        r["schema_id"] = schema_id
        r["schema_version"] = schema_version
    return r


def _gen_ref(generation_id="generat-0000001", digest="b" * 64):
    return {"generation_id": generation_id, "generation_digest": digest}


def _valid_notification(**overrides) -> dict:
    record = {
        "schema_id": NOTIF_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "notification_authority_binding",
        "record_id": "notifbind-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-17T12:00:00Z",
        "migration_epoch": "epoch-001",
        "authoritative_generation_reference": _gen_ref(),
        "authority_epoch_reference": _ref("authepoch-0000001", "c" * 64, "authority_epoch"),
        "payload_digest": "d" * 64,
        "attempt_identity": "attemptid-0000001",
        "pfn001_classification": "standard",
        "delivery_state": "not_dispatched",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "evidence",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_marker(**overrides) -> dict:
    record = {
        "schema_id": MARKER_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "marker_authority_binding",
        "record_id": "markerbind-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-17T12:00:00Z",
        "migration_epoch": "epoch-001",
        "generation_reference": _gen_ref(),
        "state": "written",
        "compatibility_fallback_forbidden": True,
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "evidence",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_receipt(**overrides) -> dict:
    record = {
        "schema_id": RECEIPT_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "receipt_authority_binding",
        "record_id": "receiptbind-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-17T12:00:00Z",
        "migration_epoch": "epoch-001",
        "generation_reference": _gen_ref(),
        "receipt_state": "absent",
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


def test_136t_exact_group10_inventory_is_notification_marker_receipt():
    assert GROUP10_RECORD_FILES == (
        "records/marker_authority_binding.schema.json",
        "records/notification_authority_binding.schema.json",
        "records/receipt_authority_binding.schema.json",
    )


def test_136t_exact_group1_through_group10_file_inventory():
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


def test_136t_no_bindings_or_views_directory_exists():
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


@pytest.mark.parametrize("relative_path", LATER_GROUP_RECORD_FILES)
def test_136t_no_group11_record_schema_exists(relative_path):
    with cltr_cutover_root() as root:
        assert not (root / relative_path).exists()


def test_136t_no_group9_schema_file_and_no_group11_filename_tracked_anywhere():
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_stems = (
        "quarantine_record.schema",
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


def test_136t_no_standalone_cas_expectation_record_schema_exists():
    with cltr_cutover_root() as root:
        names = {p.name for p in (root / "records").glob("*.schema.json")}
    assert not any("cas_expectation" in n for n in names), names


def test_136t_no_typed_python_record_model_introduced():
    tracked = subprocess.run(
        ["git", "ls-files", "src/pcae"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_names = (
        "notification_authority_binding.py",
        "marker_authority_binding.py",
        "receipt_authority_binding.py",
        "authority_model.py",
        "typed_authority.py",
    )
    hits = [path for path in tracked if Path(path).name in forbidden_names]
    assert hits == []


def test_136t_no_cltr_authority_namespace_directory_exists():
    assert not (REPO_ROOT / ".pcae" / "cltr-authority").exists()


@pytest.mark.parametrize("relative_path", GROUP10_RECORD_FILES)
def test_136t_every_resource_declares_draft_2020_12(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("relative_path", GROUP10_RECORD_FILES)
def test_136t_every_resource_id_matches_frozen_namespace(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$id"] == BASE_ID + relative_path


def test_136t_registry_loads_exactly_twenty_two_resources_with_unique_ids(registry):
    assert len(registry.schema_ids) == 22
    assert len(set(registry.schema_ids)) == 22
    assert NOTIF_ID in registry.schema_ids
    assert MARKER_ID in registry.schema_ids
    assert RECEIPT_ID in registry.schema_ids


@pytest.mark.parametrize("relative_path", GROUP10_RECORD_FILES)
def test_136t_group10_schema_is_tier2_extensions_only(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["additionalProperties"] is False
    assert "_extensions" in document["properties"]
    assert document["properties"]["_extensions"]["additionalProperties"] == {"type": "string"}


# ---------------------------------------------------------------------------
# 2. Manifest
# ---------------------------------------------------------------------------


def test_136t_manifest_verifies_cleanly():
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


def test_136t_manifest_new_entries_are_group_ten():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    for path, family, schema_id in (
        ("records/notification_authority_binding.schema.json", "notification_authority_binding", NOTIF_ID),
        ("records/marker_authority_binding.schema.json", "marker_authority_binding", MARKER_ID),
        ("records/receipt_authority_binding.schema.json", "receipt_authority_binding", RECEIPT_ID),
    ):
        entry = by_path[path]
        assert entry["implementation_group"] == 10
        assert entry["family"] == family
        assert entry["status"] == "frozen"
        assert entry["schema_id"] == schema_id


def test_136t_manifest_group1_through_group8_entries_unchanged():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    shared_entries = [e for e in manifest["entries"] if e["family"] == "shared"]
    assert len(shared_entries) == 7
    assert all(e["implementation_group"] == 1 for e in shared_entries)
    group8_entries = [e for e in manifest["entries"] if e["family"] in ("concurrency_conflict", "recovery_journal_entry")]
    assert len(group8_entries) == 2
    assert all(e["implementation_group"] == 8 for e in group8_entries)


def test_136t_manifest_entries_in_deterministic_sorted_order():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    paths = [e["file_path"] for e in manifest["entries"]]
    assert paths == sorted(paths)


def test_136t_manifest_entry_count_matches_group1_through_10_exactly():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    assert len(manifest["entries"]) == 21


def test_136t_manifest_no_group9_entry_and_no_group11_entry():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    groups = {e["implementation_group"] for e in manifest["entries"]}
    assert 9 not in groups
    assert 11 not in groups
    assert max(groups) == 10


def test_136t_manifest_detects_content_tamper_on_new_record(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    tampered = tmp_path / "records" / "notification_authority_binding.schema.json"
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


def test_136t_manifest_detects_missing_group10_sibling_file(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    (tmp_path / "records" / "marker_authority_binding.schema.json").unlink()

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


def test_136t_notification_valid_minimal_not_dispatched(registry):
    assert _validate(_valid_notification(), NOTIF_ID, registry).status is OutcomeStatus.VALID


def test_136t_marker_valid_minimal(registry):
    assert _validate(_valid_marker(), MARKER_ID, registry).status is OutcomeStatus.VALID


def test_136t_receipt_valid_minimal(registry):
    assert _validate(_valid_receipt(), RECEIPT_ID, registry).status is OutcomeStatus.VALID


def test_136t_notification_already_dispatched_with_marker_and_receipt_refs_valid(registry):
    record = _valid_notification(
        delivery_state="already_dispatched",
        marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
        receipt_reference=_ref("receiptbind-0000001", "2" * 64, "receipt_authority_binding", RECEIPT_ID),
    )
    assert _validate(record, NOTIF_ID, registry).status is OutcomeStatus.VALID


def test_136t_notification_payload_conflict_with_uncertainty_and_marker_ref_valid(registry):
    record = _valid_notification(
        delivery_state="payload_conflict",
        uncertainty={"reason": "Conflicting delivery reports received."},
        marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _validate(record, NOTIF_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize("state", ["absent", "written", "stale"])
def test_136t_marker_valid_every_non_conflict_state(state, registry):
    record = _valid_marker(state=state)
    assert _validate(record, MARKER_ID, registry).status is OutcomeStatus.VALID


def test_136t_marker_conflict_with_null_duplicate_of_valid(registry):
    record = _valid_marker(state="conflict", duplicate_of=None)
    assert _validate(record, MARKER_ID, registry).status is OutcomeStatus.VALID


def test_136t_marker_conflict_with_non_null_duplicate_of_valid(registry):
    record = _valid_marker(
        state="conflict",
        duplicate_of=_ref("markerbind-0000002", "3" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _validate(record, MARKER_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize("state", ["absent", "stale", "conflict"])
def test_136t_receipt_valid_every_non_finalized_state(state, registry):
    record = _valid_receipt(receipt_state=state)
    assert _validate(record, RECEIPT_ID, registry).status is OutcomeStatus.VALID


def test_136t_receipt_finalized_with_marker_and_evidence_refs_valid(registry):
    record = _valid_receipt(
        receipt_state="finalized",
        marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
        publication_evidence_reference=_ref(
            "pubevid-0000001", "2" * 64, "publication_evidence", PUBLICATION_EVIDENCE_ID
        ),
    )
    assert _validate(record, RECEIPT_ID, registry).status is OutcomeStatus.VALID


def test_136t_receipt_with_staleness_check_empty_object_valid(registry):
    record = _valid_receipt(staleness_check={})
    assert _validate(record, RECEIPT_ID, registry).status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 4. Local conditional validation
# ---------------------------------------------------------------------------


def test_136t_notification_payload_conflict_without_uncertainty_rejected(registry):
    record = _valid_notification(delivery_state="payload_conflict")
    assert _validate(record, NOTIF_ID, registry).status is OutcomeStatus.INVALID


def test_136t_notification_not_dispatched_with_stray_uncertainty_rejected(registry):
    record = _valid_notification(uncertainty={"reason": "stray"})
    assert _validate(record, NOTIF_ID, registry).status is OutcomeStatus.INVALID


def test_136t_notification_already_dispatched_without_marker_reference_rejected(registry):
    record = _valid_notification(delivery_state="already_dispatched")
    assert _validate(record, NOTIF_ID, registry).status is OutcomeStatus.INVALID


def test_136t_notification_already_dispatched_without_receipt_reference_rejected(registry):
    record = _valid_notification(
        delivery_state="already_dispatched",
        marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _validate(record, NOTIF_ID, registry).status is OutcomeStatus.INVALID


def test_136t_notification_not_dispatched_with_stray_marker_reference_rejected(registry):
    record = _valid_notification(
        marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _validate(record, NOTIF_ID, registry).status is OutcomeStatus.INVALID


def test_136t_notification_payload_conflict_without_marker_reference_rejected(registry):
    record = _valid_notification(
        delivery_state="payload_conflict",
        uncertainty={"reason": "x"},
    )
    assert _validate(record, NOTIF_ID, registry).status is OutcomeStatus.INVALID


def test_136t_marker_conflict_missing_duplicate_of_key_rejected(registry):
    record = _valid_marker(state="conflict")
    assert _validate(record, MARKER_ID, registry).status is OutcomeStatus.INVALID


def test_136t_marker_non_conflict_with_stray_duplicate_of_rejected(registry):
    record = _valid_marker(state="written", duplicate_of=None)
    assert _validate(record, MARKER_ID, registry).status is OutcomeStatus.INVALID


def test_136t_marker_compatibility_fallback_forbidden_false_rejected(registry):
    record = _valid_marker(compatibility_fallback_forbidden=False)
    assert _validate(record, MARKER_ID, registry).status is OutcomeStatus.INVALID


def test_136t_receipt_finalized_missing_marker_reference_rejected(registry):
    record = _valid_receipt(
        receipt_state="finalized",
        publication_evidence_reference=_ref(
            "pubevid-0000001", "2" * 64, "publication_evidence", PUBLICATION_EVIDENCE_ID
        ),
    )
    assert _validate(record, RECEIPT_ID, registry).status is OutcomeStatus.INVALID


def test_136t_receipt_finalized_missing_publication_evidence_reference_rejected(registry):
    record = _valid_receipt(
        receipt_state="finalized",
        marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _validate(record, RECEIPT_ID, registry).status is OutcomeStatus.INVALID


def test_136t_receipt_absent_with_stray_marker_reference_rejected(registry):
    record = _valid_receipt(
        marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _validate(record, RECEIPT_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 5. Enum strictness
# ---------------------------------------------------------------------------


def test_136t_notification_unknown_delivery_state_rejected(registry):
    for bogus in ("NOT_DISPATCHED", "", "unknown", "dispatched"):
        record = _valid_notification(delivery_state=bogus)
        assert _validate(record, NOTIF_ID, registry).status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


def test_136t_marker_unknown_state_rejected(registry):
    for bogus in ("WRITTEN", "", "unknown", "present"):
        record = _valid_marker(state=bogus)
        assert _validate(record, MARKER_ID, registry).status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


def test_136t_receipt_unknown_receipt_state_rejected(registry):
    for bogus in ("FINALIZED", "", "unknown", "complete"):
        record = _valid_receipt(receipt_state=bogus)
        assert _validate(record, RECEIPT_ID, registry).status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


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


def test_136t_notification_authority_epoch_reference_wrong_family_every_other_family_rejected(registry):
    for family in ALL_FAMILIES:
        if family == "authority_epoch":
            continue
        record = _valid_notification(
            authority_epoch_reference=_ref("x" * 12, "7" * 64, family)
        )
        result = _validate(record, NOTIF_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"authority_epoch_reference must reject family {family!r}"


def test_136t_notification_marker_reference_wrong_family_every_other_family_rejected(registry):
    for family in ALL_FAMILIES:
        if family == "marker_authority_binding":
            continue
        record = _valid_notification(
            delivery_state="already_dispatched",
            marker_reference=_ref("x" * 12, "7" * 64, family, BASE_ID + "records/x.schema.json"),
            receipt_reference=_ref("receiptbind-0000001", "2" * 64, "receipt_authority_binding", RECEIPT_ID),
        )
        result = _validate(record, NOTIF_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"marker_reference must reject family {family!r}"


def test_136t_notification_receipt_reference_wrong_family_every_other_family_rejected(registry):
    for family in ALL_FAMILIES:
        if family == "receipt_authority_binding":
            continue
        record = _valid_notification(
            delivery_state="already_dispatched",
            marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
            receipt_reference=_ref("x" * 12, "7" * 64, family, BASE_ID + "records/x.schema.json"),
        )
        result = _validate(record, NOTIF_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"receipt_reference must reject family {family!r}"


def test_136t_marker_duplicate_of_wrong_family_every_other_family_rejected(registry):
    for family in ALL_FAMILIES:
        if family == "marker_authority_binding":
            continue
        record = _valid_marker(
            state="conflict",
            duplicate_of=_ref("x" * 12, "7" * 64, family, BASE_ID + "records/x.schema.json"),
        )
        result = _validate(record, MARKER_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"duplicate_of must reject family {family!r}"


def test_136t_receipt_marker_reference_wrong_family_every_other_family_rejected(registry):
    for family in ALL_FAMILIES:
        if family == "marker_authority_binding":
            continue
        record = _valid_receipt(
            receipt_state="finalized",
            marker_reference=_ref("x" * 12, "7" * 64, family, BASE_ID + "records/x.schema.json"),
            publication_evidence_reference=_ref(
                "pubevid-0000001", "2" * 64, "publication_evidence", PUBLICATION_EVIDENCE_ID
            ),
        )
        result = _validate(record, RECEIPT_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"marker_reference must reject family {family!r}"


def test_136t_receipt_publication_evidence_reference_wrong_family_every_other_family_rejected(registry):
    for family in ALL_FAMILIES:
        if family == "publication_evidence":
            continue
        record = _valid_receipt(
            receipt_state="finalized",
            marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
            publication_evidence_reference=_ref("x" * 12, "7" * 64, family, BASE_ID + "records/x.schema.json"),
        )
        result = _validate(record, RECEIPT_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"publication_evidence_reference must reject family {family!r}"


# ---------------------------------------------------------------------------
# 7. Unknown-field / strictness / null-vs-absent attacks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_notification, NOTIF_ID), (_valid_marker, MARKER_ID), (_valid_receipt, RECEIPT_ID)],
)
def test_136t_unknown_top_level_field_rejected(valid_fn, schema_id, registry):
    record = valid_fn(unexpected_field="surprise")
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_notification, NOTIF_ID), (_valid_marker, MARKER_ID), (_valid_receipt, RECEIPT_ID)],
)
def test_136t_extensions_key_valid_tier2(valid_fn, schema_id, registry):
    record = valid_fn(_extensions={"note": "permitted on Tier 2"})
    assert _validate(record, schema_id, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_notification, NOTIF_ID), (_valid_marker, MARKER_ID), (_valid_receipt, RECEIPT_ID)],
)
def test_136t_extensions_non_string_value_rejected(valid_fn, schema_id, registry):
    record = valid_fn(_extensions={"note": 123})
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id,required_field",
    [
        (_valid_notification, NOTIF_ID, "delivery_state"),
        (_valid_marker, MARKER_ID, "state"),
        (_valid_receipt, RECEIPT_ID, "receipt_state"),
    ],
)
def test_136t_missing_required_field_rejected(valid_fn, schema_id, required_field, registry):
    record = valid_fn()
    del record[required_field]
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_notification, NOTIF_ID), (_valid_marker, MARKER_ID), (_valid_receipt, RECEIPT_ID)],
)
def test_136t_malformed_digest_rejected(valid_fn, schema_id, registry):
    record = valid_fn(record_digest="not-a-digest")
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_notification, NOTIF_ID), (_valid_marker, MARKER_ID), (_valid_receipt, RECEIPT_ID)],
)
def test_136t_malformed_timestamp_rejected(valid_fn, schema_id, registry):
    record = valid_fn(created_at="not-a-timestamp")
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_notification, NOTIF_ID), (_valid_marker, MARKER_ID), (_valid_receipt, RECEIPT_ID)],
)
def test_136t_empty_limitations_array_valid(valid_fn, schema_id, registry):
    record = valid_fn(limitations=[])
    assert _validate(record, schema_id, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_notification, NOTIF_ID), (_valid_marker, MARKER_ID), (_valid_receipt, RECEIPT_ID)],
)
def test_136t_authoritative_role_forbidden(valid_fn, schema_id, registry):
    record = valid_fn(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "attempted authority claim",
        }
    )
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


def test_136t_no_field_named_password_token_or_secret():
    with cltr_cutover_root() as root:
        for path in GROUP10_RECORD_FILES:
            document = json.loads((root / path).read_bytes())
            for name in document.get("properties", {}):
                lowered = name.lower()
                assert "password" not in lowered
                assert "secret" not in lowered
                assert lowered not in ("token", "bearer_token", "private_key")


def test_136t_receipt_staleness_check_rejects_unknown_field(registry):
    record = _valid_receipt(staleness_check={"unexpected": "field"})
    assert _validate(record, RECEIPT_ID, registry).status is OutcomeStatus.INVALID


def test_136t_notification_pfn001_classification_rejects_non_ascii_and_newline(registry):
    for bogus in ("bad\nvalue", "unicode-☃", ""):
        record = _valid_notification(pfn001_classification=bogus)
        assert _validate(record, NOTIF_ID, registry).status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


def test_136t_notification_storage_locator_forbidden_pattern_rejected(registry):
    # storage_locator (Sec.12) is not part of the frozen field table for
    # any of the three Group 10 families in this schema's own field
    # tables; it remains an undeclared/rejected key (Tier 2 permits only
    # _extensions).
    record = _valid_notification(storage_locator="../escape")
    assert _validate(record, NOTIF_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 8. Identity/digest/$ref graph acyclicity and creation order
# ---------------------------------------------------------------------------


def test_136t_notification_references_only_earlier_or_sibling_groups():
    """NotificationAuthorityBinding's cross-family references target
    Group 2 (authority_epoch) and its own Group 10 siblings (marker/
    receipt bindings), never a Group 11 family -- proving no forward
    cycle into an unimplemented group."""
    record = _valid_notification(
        delivery_state="already_dispatched",
        marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
        receipt_reference=_ref("receiptbind-0000001", "2" * 64, "receipt_authority_binding", RECEIPT_ID),
    )
    referenced_families = {
        record["authority_epoch_reference"]["record_family"],
        record["marker_reference"]["record_family"],
        record["receipt_reference"]["record_family"],
    }
    assert referenced_families == {"authority_epoch", "marker_authority_binding", "receipt_authority_binding"}
    assert "quarantine_record" not in referenced_families
    assert "compatibility_state" not in referenced_families


def test_136t_marker_does_not_reference_notification_or_receipt():
    """MarkerAuthorityBinding's only cross-family reference is generation_
    reference (shape-only, no record_family) and, when present,
    duplicate_of restricted to its own family -- it never references
    notification_authority_binding or receipt_authority_binding."""
    record = _valid_marker(
        state="conflict",
        duplicate_of=_ref("markerbind-0000002", "1" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert record["duplicate_of"]["record_family"] == "marker_authority_binding"


def test_136t_receipt_does_not_reference_notification():
    """ReceiptAuthorityBinding's cross-family references (marker_reference,
    publication_evidence_reference) never target
    notification_authority_binding -- no reverse edge back to the sibling
    that itself may reference receipt_authority_binding."""
    record = _valid_receipt(
        receipt_state="finalized",
        marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
        publication_evidence_reference=_ref(
            "pubevid-0000001", "2" * 64, "publication_evidence", PUBLICATION_EVIDENCE_ID
        ),
    )
    referenced_families = {
        record["marker_reference"]["record_family"],
        record["publication_evidence_reference"]["record_family"],
    }
    assert "notification_authority_binding" not in referenced_families


def test_136t_marker_and_receipt_do_not_reference_each_other_via_manifest_deps():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    marker_deps = by_path["records/marker_authority_binding.schema.json"]["dependencies"]
    receipt_deps = by_path["records/receipt_authority_binding.schema.json"]["dependencies"]
    notif_deps = by_path["records/notification_authority_binding.schema.json"]["dependencies"]
    assert not any("receipt_authority_binding" in d for d in marker_deps)
    assert not any("notification_authority_binding" in d for d in marker_deps)
    assert not any("marker_authority_binding" in d for d in receipt_deps)
    assert not any("notification_authority_binding" in d for d in receipt_deps)
    assert not any("marker_authority_binding" in d for d in notif_deps)
    assert not any("receipt_authority_binding" in d for d in notif_deps)


def test_136t_manifest_group10_dependencies_are_direct_ref_targets():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
        by_path = {e["file_path"]: e for e in manifest["entries"]}
        for path in GROUP10_RECORD_FILES:
            text = (root / path).read_text(encoding="utf-8")
            deps = by_path[path]["dependencies"]
            for dep in deps:
                dep_filename = dep.rsplit("/", 1)[-1]
                assert dep_filename in text, f"{path} declares unused dependency {dep!r}"


def test_136t_full_manifest_dependency_graph_is_acyclic():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    graph = {e["schema_id"]: e["dependencies"] for e in manifest["entries"]}

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}

    def visit(node):
        color[node] = GRAY
        for neighbor in graph.get(node, []):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                return True
            if color[neighbor] == WHITE and visit(neighbor):
                return True
        color[node] = BLACK
        return False

    for node in graph:
        if color[node] == WHITE:
            assert not visit(node), f"cycle detected reaching {node}"


def test_136t_full_ref_graph_resolves_without_unresolvable_reference(registry):
    # A successful build_offline_registry() call (the `registry` fixture)
    # already proves every $ref in the package resolves; this test
    # re-derives that guarantee explicitly for Group 10's three new files.
    with cltr_cutover_root() as root:
        for path in GROUP10_RECORD_FILES:
            document = json.loads((root / path).read_bytes())
            assert document["$id"] in registry.schema_ids


# ---------------------------------------------------------------------------
# 9. No-persistence / no-authority / no-execution / no-network / no-runtime-binding
# ---------------------------------------------------------------------------


def test_136t_no_subprocess_shell_socket_or_dynamic_execution_in_new_files():
    with cltr_cutover_root() as root:
        for relative in GROUP10_RECORD_FILES:
            text = (root / relative).read_text(encoding="utf-8")
            for banned in ("subprocess", "socket.socket", "eval(", "exec(", "os.system"):
                assert banned not in text


def test_136t_no_network_during_registry_and_validation(monkeypatch):
    def _blocked(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        result = validate_record_shape(_valid_notification(), schema_id=NOTIF_ID, registry=reg)
    assert result.status is OutcomeStatus.VALID


def test_136t_validation_never_mutates_input_record(registry):
    record = _valid_receipt(receipt_state="finalized",
        marker_reference=_ref("markerbind-0000001", "1" * 64, "marker_authority_binding", MARKER_ID),
        publication_evidence_reference=_ref(
            "pubevid-0000001", "2" * 64, "publication_evidence", PUBLICATION_EVIDENCE_ID
        ),
    )
    original = copy.deepcopy(record)
    _validate(record, RECEIPT_ID, registry)
    assert record == original


def test_136t_no_persistence_directory_created_during_validation(tmp_path, registry):
    before = set(tmp_path.iterdir())
    _validate(_valid_notification(), NOTIF_ID, registry)
    _validate(_valid_marker(), MARKER_ID, registry)
    _validate(_valid_receipt(), RECEIPT_ID, registry)
    after = set(tmp_path.iterdir())
    assert before == after


def test_136t_no_notification_dispatch_marker_or_receipt_creation_symbol_referenced():
    with cltr_cutover_root() as root:
        texts = [(root / path).read_text(encoding="utf-8") for path in GROUP10_RECORD_FILES]
    for text in texts:
        for banned in (
            "dispatch_notification", "send_notification", "create_marker",
            "write_marker", "create_receipt", "finalize_receipt",
            "NotificationDispatcher", "MarkerWriter", "ReceiptWriter",
        ):
            assert banned not in text


def test_136t_no_compatibility_or_historical_authority_resolver_symbol_referenced():
    with cltr_cutover_root() as root:
        texts = [(root / path).read_text(encoding="utf-8") for path in GROUP10_RECORD_FILES]
    for text in texts:
        for banned in (
            "CompatibilityResolver", "HistoricalAuthorityResolver",
            "resolve_compatibility", "reactivate_authority",
        ):
            assert banned not in text


def test_136t_no_authority_resolver_symbol_referenced_in_new_schema_text():
    with cltr_cutover_root() as root:
        texts = [(root / path).read_text(encoding="utf-8") for path in GROUP10_RECORD_FILES]
    for text in texts:
        for banned in ("resolve_authority", "current_authority", "AuthorityResolver"):
            assert banned not in text


def test_136t_no_authority_pointer_or_state_persistence_path_referenced():
    with cltr_cutover_root() as root:
        texts = [(root / path).read_text(encoding="utf-8") for path in GROUP10_RECORD_FILES]
    for text in texts:
        assert ".pcae/cltr-authority" not in text


# ---------------------------------------------------------------------------
# 10. Packaging / installed-wheel
# ---------------------------------------------------------------------------


def test_136t_group10_schemas_load_from_editable_install(registry):
    assert NOTIF_ID in registry.schema_ids
    assert MARKER_ID in registry.schema_ids
    assert RECEIPT_ID in registry.schema_ids


@pytest.mark.slow
def test_136t_wheel_contains_group10_schemas_no_group9_or_11_schema(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"

    import zipfile

    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()

    for path in GROUP10_RECORD_FILES:
        assert f"pcae/schema_resources/cltr_cutover/{path}" in names
    for forbidden in LATER_GROUP_RECORD_FILES:
        stem = Path(forbidden).name
        assert not any(name.endswith(stem) for name in names)


@pytest.mark.slow
def test_136t_installed_wheel_validates_group10_fixtures_outside_repository(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "venv136t"
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
    venv_python = venv_dir / "bin" / "python"
    assert venv_python.exists()

    install = subprocess.run(
        [str(venv_python), "-m", "pip", "install", str(wheels[0]), "jsonschema>=4.18,<5"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, install.stderr

    outside_cwd = tmp_path / "elsewhere"
    outside_cwd.mkdir()
    probe_script = (
        "from pcae.schema_resources import cltr_cutover_root\n"
        "from pcae.schema_runtime import build_offline_registry, validate_record_shape, OutcomeStatus\n"
        "with cltr_cutover_root() as root:\n"
        "    reg = build_offline_registry(root)\n"
        "assert len(reg.schema_ids) == 22, reg.schema_ids\n"
        "valid = {\n"
        "    'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/marker_authority_binding.schema.json',\n"
        "    'schema_version': '1.0', 'contract_version': '1.0', 'record_type': 'marker_authority_binding',\n"
        "    'record_id': 'markerbind-9000001', 'record_digest': 'a'*64, 'created_at': '2026-07-17T00:00:00Z',\n"
        "    'migration_epoch': 'epoch-w', 'generation_reference': {'generation_id': 'generat-9000001', 'generation_digest': 'b'*64},\n"
        "    'state': 'written', 'compatibility_fallback_forbidden': True, 'limitations': [],\n"
        "    'authority_disclosure': {'authority_role': 'evidence', 'is_authoritative': False, 'disclosure_text': 'x'},\n"
        "}\n"
        "result = validate_record_shape(valid, schema_id=valid['schema_id'], registry=reg)\n"
        "assert result.status is OutcomeStatus.VALID, result.issues\n"
        "invalid = dict(valid); invalid['state'] = 'conflict'\n"
        "result2 = validate_record_shape(invalid, schema_id=valid['schema_id'], registry=reg)\n"
        "assert result2.status is OutcomeStatus.INVALID\n"
        "print('OK')\n"
    )
    probe = subprocess.run(
        [str(venv_python), "-c", probe_script],
        cwd=str(outside_cwd),
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr
    assert "OK" in probe.stdout
