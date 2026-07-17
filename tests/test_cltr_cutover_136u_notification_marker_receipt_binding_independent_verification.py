"""Phase 136U: Notification/Marker/Receipt Authority Binding Schema Independent
Verification (Implementation Group 10).

Independent, adversarial re-derivation of Phase 136T's claims about Group 10
(``NotificationAuthorityBinding``, ``MarkerAuthorityBinding``,
``FinalizationReceiptAuthorityBinding``). This module does not import or
reuse 136T's test helpers, fixtures, or assertions -- every fixture and graph
below is authored fresh from the schema files and the frozen contract
(CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Sec.9, Sec.16, Sec.31, Sec.32,
Sec.33, Sec.46) and attempts, wherever plausible, to falsify 136T's reported
inventory, field tables, conditional logic, sibling independence, and scope
claims rather than merely restate them.

Every schema validated here proves shape only. No test asserts, implies, or
depends on any live notification dispatch, marker creation, receipt
finalization, publication outcome, or CLTR authority. Legacy lifecycle
remains the sole production authority; CLTR remains derivative.
"""
from __future__ import annotations

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

BASE_ID = "https://pcae.local/schemas/cltr_cutover/"
NOTIF_ID = BASE_ID + "records/notification_authority_binding.schema.json"
MARKER_ID = BASE_ID + "records/marker_authority_binding.schema.json"
RECEIPT_ID = BASE_ID + "records/receipt_authority_binding.schema.json"
MANIFEST_SCHEMA_ID = BASE_ID + "manifest.schema.json"

REPO_ROOT = Path(__file__).resolve().parents[1]


def _ref(record_id: str, digest: str, family: str, schema_id: str | None = None) -> dict:
    r = {"record_id": record_id, "record_digest": digest, "record_family": family}
    if schema_id is not None:
        r["schema_id"] = schema_id
        r["schema_version"] = "1.0"
    return r


def _gen_ref(gen_id: str = "generatn-1000001", digest: str = "1" * 64) -> dict:
    return {"generation_id": gen_id, "generation_digest": digest}


def _disclosure(role: str = "derivative") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "136U adversarial fixture; not authoritative.",
    }


def _base_notification(**overrides) -> dict:
    record = {
        "schema_id": NOTIF_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "notification_authority_binding",
        "record_id": "notifbnd-1000001",
        "record_digest": "2" * 64,
        "created_at": "2026-07-17T00:00:00Z",
        "migration_epoch": "epoch-136u",
        "authoritative_generation_reference": _gen_ref(),
        "authority_epoch_reference": _ref("authepoc-1000001", "3" * 64, "authority_epoch"),
        "payload_digest": "4" * 64,
        "attempt_identity": "notifattmpt-100000",
        "pfn001_classification": "phase-finalization-notification",
        "delivery_state": "not_dispatched",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


def _base_marker(**overrides) -> dict:
    record = {
        "schema_id": MARKER_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "marker_authority_binding",
        "record_id": "markerbd-1000001",
        "record_digest": "5" * 64,
        "created_at": "2026-07-17T00:00:00Z",
        "migration_epoch": "epoch-136u",
        "generation_reference": _gen_ref(),
        "state": "absent",
        "compatibility_fallback_forbidden": True,
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


def _base_receipt(**overrides) -> dict:
    record = {
        "schema_id": RECEIPT_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "receipt_authority_binding",
        "record_id": "receiptb-1000001",
        "record_digest": "6" * 64,
        "created_at": "2026-07-17T00:00:00Z",
        "migration_epoch": "epoch-136u",
        "generation_reference": _gen_ref(),
        "receipt_state": "absent",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


@pytest.fixture(scope="module")
def registry():
    with cltr_cutover_root() as root:
        yield build_offline_registry(root)


def _outcome(record, schema_id, registry):
    return validate_record_shape(record, schema_id=schema_id, registry=registry)


# ---------------------------------------------------------------------------
# 1. Group 9 exclusion / exact Group 10 inventory / Section 46 prerequisites
# ---------------------------------------------------------------------------


def test_136u_group9_has_no_schema_file_anywhere():
    with cltr_cutover_root() as root:
        names = {p.name for p in root.rglob("*.schema.json")}
    forbidden_group9_guesses = (
        "reconciliation_result.schema.json",
        "historical_authority_reference.schema.json",
    )
    for name in forbidden_group9_guesses:
        assert name not in names


def test_136u_manifest_has_no_group9_entry():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    assert 9 not in {e["implementation_group"] for e in manifest["entries"]}


def test_136u_manifest_records_exactly_three_group10_entries():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    group10 = [e for e in manifest["entries"] if e["implementation_group"] == 10]
    families = sorted(e["family"] for e in group10)
    assert families == [
        "marker_authority_binding",
        "notification_authority_binding",
        "receipt_authority_binding",
    ]


def test_136u_no_generic_or_versioned_binding_families_exist():
    with cltr_cutover_root() as root:
        names = {p.name for p in (root / "records").glob("*.schema.json")}
    forbidden = (
        "authority_binding.schema.json",
        "notification_authority_binding_v2.schema.json",
        "marker_authority_binding_v2.schema.json",
        "receipt_authority_binding_v2.schema.json",
        "delivery_authority_binding.schema.json",
    )
    for name in forbidden:
        assert name not in names


def test_136u_manifest_total_counts_exact():
    # Updated by Phase 136V: manifest now legitimately carries 23 entries
    # (7 shared + 16 records), reflecting contract Group 11's 2 new record
    # schemas -- the final of the 11 frozen groups.
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    entries = manifest["entries"]
    assert len(entries) == 23
    assert len([e for e in entries if e["implementation_group"] == 1]) == 7
    assert len([e for e in entries if e["implementation_group"] != 1]) == 16
    assert max(e["implementation_group"] for e in entries) == 11
    assert 12 not in {e["implementation_group"] for e in entries}


def test_136u_registry_has_exactly_twenty_two_resources(registry):
    # Updated by Phase 136V: registry now legitimately loads 24 resources
    # (23 manifest entries + the manifest schema itself).
    assert len(registry.schema_ids) == 24
    assert MANIFEST_SCHEMA_ID in registry.schema_ids
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    manifest_entry_ids = {e["schema_id"] for e in manifest["entries"]}
    # manifest.schema.json is a registry resource but deliberately never a
    # manifest.json entry itself -- this is the source of the 24-vs-23 gap.
    assert MANIFEST_SCHEMA_ID not in manifest_entry_ids
    assert set(registry.schema_ids) - manifest_entry_ids == {MANIFEST_SCHEMA_ID}


def test_136u_group10_prerequisites_are_group1_group2_and_pfn001_only():
    """Section 46 assigns Group 10 prerequisites as Group 1, Group 2, and
    existing PFN-001 identities -- NOT the full 3-8 conceptual chain. Verify
    this structurally: none of the three Group 10 manifest entries declares
    a dependency on any Group 3-8 schema_id."""
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    by_id = {e["schema_id"]: e for e in manifest["entries"]}
    group10 = [e for e in manifest["entries"] if e["implementation_group"] == 10]
    for entry in group10:
        for dep in entry["dependencies"]:
            dep_entry = by_id[dep]
            assert dep_entry["implementation_group"] == 1, (
                f"{entry['family']} declares a dependency on group "
                f"{dep_entry['implementation_group']} ({dep_entry['family']}); "
                "Section 46 authorizes only Group 1 (shared) as a manifest-declared prerequisite"
            )


def test_136u_no_group10_manifest_dependency_on_authority_epoch_or_authority_state_files():
    """Section 46 lists Group 2 (AuthorityEpoch/AuthorityState) as a
    conceptual/semantic prerequisite (the record_family enum values and the
    authority_epoch_reference family restriction reuse Group-2 vocabulary),
    but NOT as a direct manifest $ref/dependency edge -- Group 10 schemas
    reference authority_epoch only via the closed record_family enum
    string, never via a $ref to authority_epoch.schema.json itself."""
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    group10 = [e for e in manifest["entries"] if e["implementation_group"] == 10]
    epoch_id = BASE_ID + "records/authority_epoch.schema.json"
    state_id = BASE_ID + "records/authority_state.schema.json"
    for entry in group10:
        assert epoch_id not in entry["dependencies"]
        assert state_id not in entry["dependencies"]


# ---------------------------------------------------------------------------
# 2. NotificationAuthorityBinding field table (Section 31)
# ---------------------------------------------------------------------------


def test_136u_notification_valid_record_passes_registry(registry):
    assert _outcome(_base_notification(), NOTIF_ID, registry).status == OutcomeStatus.VALID


REQUIRED_NOTIF_FIELDS = (
    "schema_id", "schema_version", "contract_version", "record_type", "record_id",
    "record_digest", "created_at", "migration_epoch",
    "authoritative_generation_reference", "authority_epoch_reference",
    "payload_digest", "attempt_identity", "pfn001_classification",
    "delivery_state", "limitations", "authority_disclosure",
)


@pytest.mark.parametrize("field", REQUIRED_NOTIF_FIELDS)
def test_136u_notification_each_required_field_rejected_if_absent(registry, field):
    record = _base_notification()
    del record[field]
    assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID


def test_136u_notification_unknown_top_level_field_rejected(registry):
    record = _base_notification(dispatch_status="sent")
    assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID


def test_136u_notification_phase_id_and_transition_id_are_prohibited(registry):
    for field, value in (("phase_id", "136U"), ("transition_id", "trans-00000001")):
        record = _base_notification(**{field: value})
        assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID, field


def test_136u_notification_delivery_state_enum_rejects_unknown_values(registry):
    for bogus in ("sent", "delivered", "dispatched", "PAYLOAD_CONFLICT", ""):
        record = _base_notification(delivery_state=bogus)
        assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID, bogus


def test_136u_notification_authoritative_generation_reference_is_generation_shape_not_record_reference(registry):
    """A record_reference (id+digest+family) must NOT satisfy
    authoritative_generation_reference -- only the narrower id+digest-only
    generation_reference shape is accepted."""
    record = _base_notification(
        authoritative_generation_reference=_ref("authstat-1000001", "7" * 64, "authority_state")
    )
    assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID


def test_136u_notification_authority_epoch_reference_locked_to_authority_epoch_family(registry):
    record = _base_notification(
        authority_epoch_reference=_ref("authstat-1000001", "7" * 64, "authority_state")
    )
    assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID


def test_136u_notification_payload_digest_rejects_non_hex_and_wrong_length(registry):
    for bogus in ("g" * 64, "a" * 63, "a" * 65, "sha256:" + "a" * 64, ("A" * 64)):
        record = _base_notification(payload_digest=bogus)
        assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID, bogus


# ---------------------------------------------------------------------------
# 3. Notification delivery_state conditional branches (uncertainty/marker/receipt)
# ---------------------------------------------------------------------------


def test_136u_notification_not_dispatched_forbids_marker_and_receipt_and_uncertainty(registry):
    record = _base_notification(
        delivery_state="not_dispatched",
        marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID


def test_136u_notification_already_dispatched_requires_marker_and_receipt(registry):
    incomplete = _base_notification(delivery_state="already_dispatched")
    assert _outcome(incomplete, NOTIF_ID, registry).status == OutcomeStatus.INVALID

    only_marker = _base_notification(
        delivery_state="already_dispatched",
        marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _outcome(only_marker, NOTIF_ID, registry).status == OutcomeStatus.INVALID

    complete = _base_notification(
        delivery_state="already_dispatched",
        marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
        receipt_reference=_ref("receiptb-1000001", "9" * 64, "receipt_authority_binding", RECEIPT_ID),
    )
    assert _outcome(complete, NOTIF_ID, registry).status == OutcomeStatus.VALID


def test_136u_notification_already_dispatched_forbids_uncertainty(registry):
    record = _base_notification(
        delivery_state="already_dispatched",
        marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
        receipt_reference=_ref("receiptb-1000001", "9" * 64, "receipt_authority_binding", RECEIPT_ID),
        uncertainty={"reason": "unexpected uncertainty"},
    )
    assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID


def test_136u_notification_payload_conflict_requires_uncertainty_and_marker_but_forbids_receipt(registry):
    missing_uncertainty = _base_notification(
        delivery_state="payload_conflict",
        marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _outcome(missing_uncertainty, NOTIF_ID, registry).status == OutcomeStatus.INVALID

    missing_marker = _base_notification(
        delivery_state="payload_conflict",
        uncertainty={"reason": "conflicting payload observed"},
    )
    assert _outcome(missing_marker, NOTIF_ID, registry).status == OutcomeStatus.INVALID

    with_receipt = _base_notification(
        delivery_state="payload_conflict",
        marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
        receipt_reference=_ref("receiptb-1000001", "9" * 64, "receipt_authority_binding", RECEIPT_ID),
        uncertainty={"reason": "conflicting payload observed"},
    )
    assert _outcome(with_receipt, NOTIF_ID, registry).status == OutcomeStatus.INVALID

    valid = _base_notification(
        delivery_state="payload_conflict",
        marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
        uncertainty={"reason": "conflicting payload observed"},
    )
    assert _outcome(valid, NOTIF_ID, registry).status == OutcomeStatus.VALID


def test_136u_notification_marker_reference_locked_to_marker_family_wrong_family_rejected(registry):
    record = _base_notification(
        delivery_state="payload_conflict",
        marker_reference=_ref("receiptb-1000001", "8" * 64, "receipt_authority_binding", RECEIPT_ID),
        uncertainty={"reason": "wrong family probe"},
    )
    assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID


def test_136u_notification_receipt_reference_locked_to_receipt_family_wrong_family_rejected(registry):
    record = _base_notification(
        delivery_state="already_dispatched",
        marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
        receipt_reference=_ref("markerbd-1000002", "9" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 4. MarkerAuthorityBinding field table (Section 32)
# ---------------------------------------------------------------------------


def test_136u_marker_valid_record_passes_registry(registry):
    assert _outcome(_base_marker(), MARKER_ID, registry).status == OutcomeStatus.VALID


REQUIRED_MARKER_FIELDS = (
    "schema_id", "schema_version", "contract_version", "record_type", "record_id",
    "record_digest", "created_at", "migration_epoch", "generation_reference",
    "state", "compatibility_fallback_forbidden", "limitations", "authority_disclosure",
)


@pytest.mark.parametrize("field", REQUIRED_MARKER_FIELDS)
def test_136u_marker_each_required_field_rejected_if_absent(registry, field):
    record = _base_marker()
    del record[field]
    assert _outcome(record, MARKER_ID, registry).status == OutcomeStatus.INVALID


def test_136u_marker_unknown_top_level_field_rejected(registry):
    record = _base_marker(filesystem_path="/tmp/marker")
    assert _outcome(record, MARKER_ID, registry).status == OutcomeStatus.INVALID


def test_136u_marker_state_enum_rejects_unknown_values(registry):
    for bogus in ("created", "WRITTEN", "missing", ""):
        record = _base_marker(state=bogus)
        assert _outcome(record, MARKER_ID, registry).status == OutcomeStatus.INVALID, bogus


def test_136u_marker_compatibility_fallback_forbidden_is_pinned_true(registry):
    record = _base_marker(compatibility_fallback_forbidden=False)
    assert _outcome(record, MARKER_ID, registry).status == OutcomeStatus.INVALID


def test_136u_marker_duplicate_of_required_only_when_state_conflict(registry):
    absent_conflict = _base_marker(state="conflict")
    assert _outcome(absent_conflict, MARKER_ID, registry).status == OutcomeStatus.INVALID

    non_conflict_with_duplicate = _base_marker(
        state="written",
        duplicate_of=_ref("markerbd-1000002", "a" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _outcome(non_conflict_with_duplicate, MARKER_ID, registry).status == OutcomeStatus.INVALID

    conflict_null = _base_marker(state="conflict", duplicate_of=None)
    assert _outcome(conflict_null, MARKER_ID, registry).status == OutcomeStatus.VALID

    conflict_ref = _base_marker(
        state="conflict",
        duplicate_of=_ref("markerbd-1000002", "a" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _outcome(conflict_ref, MARKER_ID, registry).status == OutcomeStatus.VALID


def test_136u_marker_duplicate_of_wrong_family_rejected(registry):
    record = _base_marker(
        state="conflict",
        duplicate_of=_ref("notifbnd-1000002", "a" * 64, "notification_authority_binding", NOTIF_ID),
    )
    assert _outcome(record, MARKER_ID, registry).status == OutcomeStatus.INVALID


def test_136u_marker_generation_reference_is_generation_shape_not_record_reference(registry):
    record = _base_marker(
        generation_reference=_ref("authstat-1000001", "7" * 64, "authority_state")
    )
    assert _outcome(record, MARKER_ID, registry).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 5. FinalizationReceiptAuthorityBinding field table (Section 33) + Section 16
# ---------------------------------------------------------------------------


def test_136u_receipt_valid_record_passes_registry(registry):
    assert _outcome(_base_receipt(), RECEIPT_ID, registry).status == OutcomeStatus.VALID


REQUIRED_RECEIPT_FIELDS = (
    "schema_id", "schema_version", "contract_version", "record_type", "record_id",
    "record_digest", "created_at", "migration_epoch", "generation_reference",
    "receipt_state", "limitations", "authority_disclosure",
)


@pytest.mark.parametrize("field", REQUIRED_RECEIPT_FIELDS)
def test_136u_receipt_each_required_field_rejected_if_absent(registry, field):
    record = _base_receipt()
    del record[field]
    assert _outcome(record, RECEIPT_ID, registry).status == OutcomeStatus.INVALID


def test_136u_receipt_unknown_top_level_field_rejected(registry):
    record = _base_receipt(exactly_once=True)
    assert _outcome(record, RECEIPT_ID, registry).status == OutcomeStatus.INVALID


def test_136u_receipt_state_enum_rejects_unknown_values(registry):
    for bogus in ("complete", "FINALIZED", "pending", ""):
        record = _base_receipt(receipt_state=bogus)
        assert _outcome(record, RECEIPT_ID, registry).status == OutcomeStatus.INVALID, bogus


def test_136u_receipt_finalized_requires_marker_and_publication_evidence_together(registry):
    """Section 16's explicit if/then: receipt_state == finalized requires
    marker_reference, publication_evidence_reference, and
    generation_reference all together. generation_reference is already
    unconditionally required (independent of state); the other two must
    become required exactly when, and only when, state is 'finalized'."""
    bare_finalized = _base_receipt(receipt_state="finalized")
    assert _outcome(bare_finalized, RECEIPT_ID, registry).status == OutcomeStatus.INVALID

    only_marker = _base_receipt(
        receipt_state="finalized",
        marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _outcome(only_marker, RECEIPT_ID, registry).status == OutcomeStatus.INVALID

    only_evidence = _base_receipt(
        receipt_state="finalized",
        publication_evidence_reference=_ref("pubevid-1000001", "8" * 64, "publication_evidence", BASE_ID + "records/publication_evidence.schema.json"),
    )
    assert _outcome(only_evidence, RECEIPT_ID, registry).status == OutcomeStatus.INVALID

    complete = _base_receipt(
        receipt_state="finalized",
        marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
        publication_evidence_reference=_ref("pubevid-1000001", "9" * 64, "publication_evidence", BASE_ID + "records/publication_evidence.schema.json"),
    )
    assert _outcome(complete, RECEIPT_ID, registry).status == OutcomeStatus.VALID


def test_136u_receipt_non_finalized_states_forbid_marker_and_evidence_references(registry):
    for state in ("absent", "stale", "conflict"):
        record = _base_receipt(
            receipt_state=state,
            marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
            publication_evidence_reference=_ref("pubevid-1000001", "9" * 64, "publication_evidence", BASE_ID + "records/publication_evidence.schema.json"),
        )
        assert _outcome(record, RECEIPT_ID, registry).status == OutcomeStatus.INVALID, state


def test_136u_receipt_generation_reference_required_regardless_of_receipt_state(registry):
    """NON-BLOCKING-136T-6's resolution: generation_reference stays
    unconditionally required even for non-finalized states, unlike
    marker_reference/publication_evidence_reference."""
    for state in ("absent", "stale", "conflict", "finalized"):
        record = _base_receipt(receipt_state=state)
        del record["generation_reference"]
        if state == "finalized":
            record["marker_reference"] = _ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID)
            record["publication_evidence_reference"] = _ref(
                "pubevid-1000001", "9" * 64, "publication_evidence", BASE_ID + "records/publication_evidence.schema.json"
            )
        assert _outcome(record, RECEIPT_ID, registry).status == OutcomeStatus.INVALID, state


def test_136u_receipt_marker_reference_locked_to_marker_family(registry):
    record = _base_receipt(
        receipt_state="finalized",
        marker_reference=_ref("notifbnd-1000001", "8" * 64, "notification_authority_binding", NOTIF_ID),
        publication_evidence_reference=_ref("pubevid-1000001", "9" * 64, "publication_evidence", BASE_ID + "records/publication_evidence.schema.json"),
    )
    assert _outcome(record, RECEIPT_ID, registry).status == OutcomeStatus.INVALID


def test_136u_receipt_publication_evidence_reference_locked_to_publication_evidence_family(registry):
    record = _base_receipt(
        receipt_state="finalized",
        marker_reference=_ref("markerbd-1000001", "8" * 64, "marker_authority_binding", MARKER_ID),
        publication_evidence_reference=_ref("markerbd-1000002", "9" * 64, "marker_authority_binding", MARKER_ID),
    )
    assert _outcome(record, RECEIPT_ID, registry).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 6. staleness_check disposition (DEFERRED-136T-1)
# ---------------------------------------------------------------------------


def test_136u_receipt_staleness_check_is_optional(registry):
    record = _base_receipt()
    assert "staleness_check" not in record
    assert _outcome(record, RECEIPT_ID, registry).status == OutcomeStatus.VALID


def test_136u_receipt_staleness_check_accepts_only_empty_object(registry):
    record_empty = _base_receipt(staleness_check={})
    assert _outcome(record_empty, RECEIPT_ID, registry).status == OutcomeStatus.VALID

    for bogus in ({"checked_at": "2026-07-17T00:00:00Z"}, None, "stale", 1, [], True):
        record = _base_receipt(staleness_check=bogus)
        assert _outcome(record, RECEIPT_ID, registry).status == OutcomeStatus.INVALID, bogus


# ---------------------------------------------------------------------------
# 7. Authority-role prohibition (Section 9) -- all three binding schemas
# ---------------------------------------------------------------------------


ALLOWED_NON_AUTHORITATIVE_ROLES = (
    "derivative", "operational", "evidence", "compatibility", "historical", "quarantined"
)


@pytest.mark.parametrize("role", ALLOWED_NON_AUTHORITATIVE_ROLES)
def test_136u_notification_permits_every_non_authoritative_role(registry, role):
    record = _base_notification(authority_disclosure=_disclosure(role))
    assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.VALID, role


@pytest.mark.parametrize("role", ALLOWED_NON_AUTHORITATIVE_ROLES)
def test_136u_marker_permits_every_non_authoritative_role(registry, role):
    record = _base_marker(authority_disclosure=_disclosure(role))
    assert _outcome(record, MARKER_ID, registry).status == OutcomeStatus.VALID, role


@pytest.mark.parametrize("role", ALLOWED_NON_AUTHORITATIVE_ROLES)
def test_136u_receipt_permits_every_non_authoritative_role(registry, role):
    record = _base_receipt(authority_disclosure=_disclosure(role))
    assert _outcome(record, RECEIPT_ID, registry).status == OutcomeStatus.VALID, role


@pytest.mark.parametrize("schema_id, base_fn", (
    (NOTIF_ID, _base_notification),
    (MARKER_ID, _base_marker),
    (RECEIPT_ID, _base_receipt),
))
def test_136u_authoritative_role_locally_forbidden_on_all_three_bindings(registry, schema_id, base_fn):
    record = base_fn(authority_disclosure=_disclosure("authoritative"))
    assert _outcome(record, schema_id, registry).status == OutcomeStatus.INVALID


@pytest.mark.parametrize("schema_id, base_fn", (
    (NOTIF_ID, _base_notification),
    (MARKER_ID, _base_marker),
    (RECEIPT_ID, _base_receipt),
))
def test_136u_authoritative_role_case_variant_not_a_bypass(registry, schema_id, base_fn):
    for variant in ("Authoritative", "AUTHORITATIVE", "authoritative "):
        record = base_fn(authority_disclosure=_disclosure(variant))
        # A case/whitespace variant is not itself the enum value "authoritative",
        # but it must also not be one of the 7 valid enum values, so it is
        # still rejected -- distinctly, via the enum closed-vocabulary check,
        # not the "not: const authoritative" restriction. Confirms no variant
        # sneaks past either gate.
        assert _outcome(record, schema_id, registry).status == OutcomeStatus.INVALID, variant


@pytest.mark.parametrize("schema_id, base_fn", (
    (NOTIF_ID, _base_notification),
    (MARKER_ID, _base_marker),
    (RECEIPT_ID, _base_receipt),
))
def test_136u_is_authoritative_cannot_be_forced_true(registry, schema_id, base_fn):
    disclosure = _disclosure("derivative")
    disclosure["is_authoritative"] = True
    record = base_fn(authority_disclosure=disclosure)
    assert _outcome(record, schema_id, registry).status == OutcomeStatus.INVALID


@pytest.mark.parametrize("schema_id, base_fn", (
    (NOTIF_ID, _base_notification),
    (MARKER_ID, _base_marker),
    (RECEIPT_ID, _base_receipt),
))
def test_136u_extensions_cannot_smuggle_authoritative_claim(registry, schema_id, base_fn):
    """_extensions is a string-valued map only; even if a key named
    'authority_role' or 'authoritative' is injected there, it can never
    override the top-level authority_disclosure.authority_role field --
    confirm the record remains valid (since _extensions strings never carry
    schema-level authority meaning) rather than somehow becoming forbidden
    or granting authority."""
    record = base_fn(_extensions={"authority_role": "authoritative", "is_authoritative": "true"})
    assert _outcome(record, schema_id, registry).status == OutcomeStatus.VALID
    # And the top-level field, independently, still governs and still forbids:
    record2 = base_fn(
        authority_disclosure=_disclosure("authoritative"),
        _extensions={"note": "irrelevant"},
    )
    assert _outcome(record2, schema_id, registry).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 8. Tier 2 / _extensions boundary
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("schema_id, base_fn", (
    (NOTIF_ID, _base_notification),
    (MARKER_ID, _base_marker),
    (RECEIPT_ID, _base_receipt),
))
def test_136u_extensions_absent_is_valid(registry, schema_id, base_fn):
    record = base_fn()
    assert "_extensions" not in record
    assert _outcome(record, schema_id, registry).status == OutcomeStatus.VALID


@pytest.mark.parametrize("schema_id, base_fn", (
    (NOTIF_ID, _base_notification),
    (MARKER_ID, _base_marker),
    (RECEIPT_ID, _base_receipt),
))
def test_136u_extensions_rejects_nested_structure(registry, schema_id, base_fn):
    record = base_fn(_extensions={"a": {"nested": "object"}})
    assert _outcome(record, schema_id, registry).status == OutcomeStatus.INVALID


@pytest.mark.parametrize("schema_id, base_fn", (
    (NOTIF_ID, _base_notification),
    (MARKER_ID, _base_marker),
    (RECEIPT_ID, _base_receipt),
))
def test_136u_extensions_rejects_non_string_values(registry, schema_id, base_fn):
    for bogus in ({"a": 1}, {"a": None}, {"a": True}, {"a": ["x"]}):
        record = base_fn(_extensions=bogus)
        assert _outcome(record, schema_id, registry).status == OutcomeStatus.INVALID, bogus


@pytest.mark.parametrize("schema_id, base_fn", (
    (NOTIF_ID, _base_notification),
    (MARKER_ID, _base_marker),
    (RECEIPT_ID, _base_receipt),
))
def test_136u_second_extension_key_name_still_rejected(registry, schema_id, base_fn):
    """Only the single literal key '_extensions' is a permitted extra
    top-level key; a differently-named extension-shaped key must still be
    rejected under additionalProperties: false."""
    record = base_fn()
    record["extensions"] = {"a": "b"}
    assert _outcome(record, schema_id, registry).status == OutcomeStatus.INVALID
    record2 = base_fn()
    record2["_extension"] = {"a": "b"}
    assert _outcome(record2, schema_id, registry).status == OutcomeStatus.INVALID


@pytest.mark.parametrize("schema_id, base_fn", (
    (NOTIF_ID, _base_notification),
    (MARKER_ID, _base_marker),
    (RECEIPT_ID, _base_receipt),
))
def test_136u_extensions_null_and_scalar_rejected(registry, schema_id, base_fn):
    for bogus in (None, "scalar", 1, True, []):
        record = base_fn(_extensions=bogus)
        assert _outcome(record, schema_id, registry).status == OutcomeStatus.INVALID, bogus


# ---------------------------------------------------------------------------
# 9. Null-versus-absent behavior
# ---------------------------------------------------------------------------


def test_136u_notification_required_reference_field_null_is_rejected(registry):
    record = _base_notification(authoritative_generation_reference=None)
    assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID


def test_136u_marker_generation_reference_null_is_rejected(registry):
    record = _base_marker(generation_reference=None)
    assert _outcome(record, MARKER_ID, registry).status == OutcomeStatus.INVALID


def test_136u_marker_duplicate_of_null_only_valid_when_state_conflict(registry):
    record = _base_marker(state="written")
    record["duplicate_of"] = None
    assert _outcome(record, MARKER_ID, registry).status == OutcomeStatus.INVALID


def test_136u_receipt_generation_reference_null_is_rejected(registry):
    record = _base_receipt(generation_reference=None)
    assert _outcome(record, RECEIPT_ID, registry).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 10. Sibling independence + dependency/identity/digest graphs
# ---------------------------------------------------------------------------


def test_136u_manifest_group10_siblings_declare_no_cross_sibling_dependency():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    group10_ids = {
        e["schema_id"] for e in manifest["entries"] if e["implementation_group"] == 10
    }
    for entry in manifest["entries"]:
        if entry["implementation_group"] != 10:
            continue
        other_siblings = group10_ids - {entry["schema_id"]}
        for dep in entry["dependencies"]:
            assert dep not in other_siblings, (
                f"{entry['family']} manifest-declares a dependency on a Group 10 sibling {dep}"
            )


def test_136u_all_three_bindings_creatable_independently_no_forced_ordering(registry):
    """Each of the three Group 10 records validates successfully with no
    reference to the other two present at all (the optional marker_reference/
    receipt_reference on notification, when absent under not_dispatched, and
    the absence of any binding-to-binding required field on marker/receipt in
    their minimal non-finalized/non-conflict forms)."""
    notif = _base_notification()  # not_dispatched: no marker/receipt reference
    marker = _base_marker()  # absent: no duplicate_of
    receipt = _base_receipt()  # absent: no marker/evidence reference
    assert _outcome(notif, NOTIF_ID, registry).status == OutcomeStatus.VALID
    assert _outcome(marker, MARKER_ID, registry).status == OutcomeStatus.VALID
    assert _outcome(receipt, RECEIPT_ID, registry).status == OutcomeStatus.VALID


def test_136u_full_ref_graph_has_no_self_cycle_or_group10_sibling_cycle():
    """Build the complete $ref-derived schema-to-schema dependency graph from
    the manifest and confirm it is acyclic (topological sort succeeds), and
    specifically that no Group 10 sibling ever depends (directly or
    transitively) on another Group 10 sibling."""
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    by_id = {e["schema_id"]: e for e in manifest["entries"]}

    visiting, visited = set(), set()

    def dfs(node):
        if node in visited:
            return
        assert node not in visiting, f"cycle detected at {node}"
        visiting.add(node)
        for dep in by_id[node]["dependencies"]:
            dfs(dep)
        visiting.remove(node)
        visited.add(node)

    for schema_id in by_id:
        dfs(schema_id)
    assert visited == set(by_id)

    group10_ids = {e["schema_id"] for e in manifest["entries"] if e["implementation_group"] == 10}

    def transitive_deps(node, seen=None):
        seen = seen or set()
        for dep in by_id[node]["dependencies"]:
            if dep not in seen:
                seen.add(dep)
                transitive_deps(dep, seen)
        return seen

    for gid in group10_ids:
        assert not (transitive_deps(gid) & (group10_ids - {gid}))


def test_136u_creation_order_shared_before_group10_no_forward_deps():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    by_family = {e["family"]: e for e in manifest["entries"]}
    for family in ("notification_authority_binding", "marker_authority_binding", "receipt_authority_binding"):
        deps = by_family[family]["dependencies"]
        for dep in deps:
            dep_entry = next(e for e in manifest["entries"] if e["schema_id"] == dep)
            assert dep_entry["implementation_group"] <= 10


def test_136u_record_identity_shapes_are_indistinguishable_by_pattern_alone():
    """All three Group 10 record_id values match the same generic
    record_identity pattern; family enforcement happens via record_type
    const/schema_id, not via the identity pattern -- confirming no
    identity-pattern-level dependency exists between the three siblings."""
    import re

    pattern = re.compile(r"^[a-z][a-z0-9-]{7,127}$")
    assert pattern.match("notifbnd-1000001")
    assert pattern.match("markerbd-1000001")
    assert pattern.match("receiptb-1000001")


def test_136u_record_digest_fields_are_independent_sha256_hex_shapes_no_shared_derivation():
    """Each binding's record_digest is an independently shape-checked
    sha256_hex string; assigning colliding digest strings across the three
    families is schema-valid (Layer 2 does not cross-check digests across
    documents) -- confirming digest fields carry no structural cross-record
    binding at the shape level."""
    shared_digest = "f" * 64
    notif = _base_notification(record_digest=shared_digest)
    marker = _base_marker(record_digest=shared_digest)
    receipt = _base_receipt(record_digest=shared_digest)
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
    assert _outcome(notif, NOTIF_ID, reg).status == OutcomeStatus.VALID
    assert _outcome(marker, MARKER_ID, reg).status == OutcomeStatus.VALID
    assert _outcome(receipt, RECEIPT_ID, reg).status == OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 11. Atomic group completeness
# ---------------------------------------------------------------------------


def test_136u_group10_partial_manifest_is_structurally_distinguishable(registry, tmp_path):
    with cltr_cutover_root() as root:
        for item in root.rglob("*"):
            if item.is_file():
                target = tmp_path / item.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(item.read_bytes())
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["entries"] = [e for e in manifest["entries"] if e["family"] != "receipt_authority_binding"]
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ManifestIntegrityError):
        load_and_verify_manifest(
            manifest_path,
            package_root=tmp_path,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136u_manifest_digests_match_actual_files_on_disk(registry):
    with cltr_cutover_root() as root:
        verified = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    assert len(verified.entries) == 23


def test_136u_manifest_rejects_tampered_group10_digest(registry, tmp_path):
    with cltr_cutover_root() as root:
        for item in root.rglob("*"):
            if item.is_file():
                target = tmp_path / item.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(item.read_bytes())
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for entry in manifest["entries"]:
        if entry["family"] == "notification_authority_binding":
            entry["file_digest"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ManifestIntegrityError):
        load_and_verify_manifest(
            manifest_path,
            package_root=tmp_path,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


# ---------------------------------------------------------------------------
# 12. Wrong-family substitution attacks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("wrong_family", (
    "authority_epoch", "authority_state", "cutover_request", "publication_evidence",
    "marker_authority_binding", "receipt_authority_binding",
))
def test_136u_notification_epoch_reference_rejects_every_non_epoch_family(registry, wrong_family):
    if wrong_family == "authority_epoch":
        pytest.skip("positive case covered elsewhere")
    record = _base_notification(authority_epoch_reference=_ref("someid-0000001", "a" * 64, wrong_family))
    assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 13. Secret-like value probes (opaque-data boundary, not comprehensive scanning)
# ---------------------------------------------------------------------------


SECRET_LIKE_STRINGS = (
    "bot123456789:AAExampleTelegramBotTokenValueHere000",
    "AKIAABCDEFGHIJKLMNOP",
    "Bearer sk-live-1234567890abcdef",
)


@pytest.mark.parametrize("secret", SECRET_LIKE_STRINGS)
def test_136u_notification_pfn001_classification_treats_secret_like_strings_as_opaque_data(registry, secret):
    """This schema performs no secret detection: a secret-like string in a
    bounded printable-ASCII field is schema-valid (opaque data), which is
    exactly what the contract documents -- confirm no accidental rejection
    OR accidental special-casing occurs; the shape gate is charset/length
    only, printable-ASCII, <= 256 chars."""
    if len(secret) <= 256:
        record = _base_notification(pfn001_classification=secret)
        assert _outcome(record, NOTIF_ID, registry).status == OutcomeStatus.VALID


def test_136u_notification_pfn001_classification_rejects_control_characters():
    """Printable-ASCII-only pattern must reject embedded control characters
    (e.g. a newline-smuggled secret-adjacent payload)."""
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
    record = _base_notification(pfn001_classification="line1\nline2")
    assert _outcome(record, NOTIF_ID, reg).status == OutcomeStatus.INVALID


def test_136u_no_real_credentials_appear_in_group10_schema_files():
    with cltr_cutover_root() as root:
        for name in (
            "notification_authority_binding.schema.json",
            "marker_authority_binding.schema.json",
            "receipt_authority_binding.schema.json",
        ):
            text = (root / "records" / name).read_text()
            assert "BEGIN PRIVATE KEY" not in text
            assert "xox" not in text  # Slack-token-shaped prefix probe
            assert "AKIA" not in text  # AWS-access-key-shaped prefix probe


# ---------------------------------------------------------------------------
# 14. No-network / no-dispatch / no-marker-creation / no-receipt-creation /
#     no-authority / no-execution probes
# ---------------------------------------------------------------------------


def test_136u_registry_construction_performs_no_network_access(monkeypatch):
    def _forbidden(*args, **kwargs):
        raise AssertionError("Network access attempted during registry construction")

    monkeypatch.setattr(socket, "socket", _forbidden)
    monkeypatch.setattr(socket, "create_connection", _forbidden)
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
    assert NOTIF_ID in reg.schema_ids
    assert MARKER_ID in reg.schema_ids
    assert RECEIPT_ID in reg.schema_ids


def test_136u_validation_performs_no_network_access(monkeypatch, registry):
    def _forbidden(*args, **kwargs):
        raise AssertionError("Network access attempted during validation")

    monkeypatch.setattr(socket, "socket", _forbidden)
    monkeypatch.setattr(socket, "create_connection", _forbidden)
    assert _outcome(_base_notification(), NOTIF_ID, registry).status == OutcomeStatus.VALID
    assert _outcome(_base_marker(), MARKER_ID, registry).status == OutcomeStatus.VALID
    assert _outcome(_base_receipt(), RECEIPT_ID, registry).status == OutcomeStatus.VALID


def test_136u_no_dispatcher_marker_writer_receipt_writer_or_resolver_module_exists():
    forbidden_paths = (
        "src/pcae/cltr/notification_dispatcher.py",
        "src/pcae/cltr/telegram_dispatcher.py",
        "src/pcae/cltr/marker_writer.py",
        "src/pcae/cltr/marker_creator.py",
        "src/pcae/cltr/receipt_writer.py",
        "src/pcae/cltr/receipt_finalizer.py",
        "src/pcae/cltr/binding_evaluator.py",
        "src/pcae/cltr/authority_resolver.py",
        "src/pcae/cltr/current_authority.py",
    )
    for rel in forbidden_paths:
        assert not (REPO_ROOT / rel).exists(), rel


def test_136u_no_authority_pointer_directory_or_file():
    assert not (REPO_ROOT / ".pcae" / "cltr-authority").exists()


def test_136u_no_runtime_code_references_group10_families_outside_schema_resources():
    tracked = subprocess.run(
        ["git", "grep", "-l", "-e", "notification_authority_binding", "-e", "marker_authority_binding",
         "-e", "receipt_authority_binding", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    hits = [
        line for line in tracked.stdout.splitlines()
        if "schema_resources" not in line
    ]
    assert hits == [], hits


def test_136u_no_execution_capability_module_added_for_group10():
    tracked = subprocess.run(
        ["git", "ls-files", "src/pcae"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_names = {
        "notification_authority_binding.py",
        "marker_authority_binding.py",
        "receipt_authority_binding.py",
        "notification_dispatcher.py",
        "marker_writer.py",
        "receipt_writer.py",
    }
    hits = [p for p in tracked if Path(p).name in forbidden_names]
    assert hits == []


def test_136u_no_bindings_or_views_directories():
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


def test_136u_no_compatibility_state_or_quarantine_or_group11_files_present():
    # Updated by Phase 136V: compatibility_state.schema.json and
    # quarantine_record.schema.json are no longer forbidden -- Phase 136V
    # legitimately implements them as contract Group 11, the final of the
    # 11 frozen executable-schema groups. Empty: no later group remains.
    forbidden = ()
    with cltr_cutover_root() as root:
        present = {p.name for p in (root / "records").glob("*.schema.json")}
    for name in forbidden:
        assert name not in present
