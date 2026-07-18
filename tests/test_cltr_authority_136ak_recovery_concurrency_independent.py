"""Phase 136AK: Stage 3 Typed Authority Model Recovery and Concurrency
Independent Verification.

Independent re-derivation and verification of Phase 136AJ's Typed Model
Implementation Group 6 (``ConcurrencyConflict``, ``RecoveryJournalEntry``)
against the frozen contracts and live executable schemas
(``records/concurrency_conflict.schema.json``,
``records/recovery_journal_entry.schema.json``,
``shared/references.schema.json``, ``shared/digest.schema.json``,
``shared/identity.schema.json``, ``shared/enums.schema.json``) --
independently, without trusting the 136AJ implementation, its own test
suite, its report, its comments, or any prior verification report. Every
fixture and assertion below was derived directly from the executable
schema files and the frozen contract text quoted in their
``description`` fields, then compared against
``src/pcae/cltr/authority/recovery_concurrency.py``.

Scope: Implementation Group 6 only (``ConcurrencyConflict``,
``RecoveryJournalEntry``). No later record-family model
(``NotificationAuthorityBinding``, ``MarkerAuthorityBinding``,
``FinalizationReceiptAuthorityBinding``, ``CompatibilityState``,
``QuarantineRecord``) is implemented or exercised here.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import recovery_concurrency as rc
from pcae.cltr.authority.errors import (
    TypedModelConstructionError,
    TypedModelInternalInvariantError,
    UnsupportedSchemaVersionError,
    WrongFamilyReferenceError,
)
from pcae.cltr.authority.sentinels import ABSENT
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
RECOVERY_CONCURRENCY_MODULE = AUTHORITY_PACKAGE_DIR / "recovery_concurrency.py"

CONCURRENCY_CONFLICT_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/concurrency_conflict.schema.json"
)
RECOVERY_JOURNAL_ENTRY_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/recovery_journal_entry.schema.json"
)
CUTOVER_REQUEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/cutover_request.schema.json"

ELEVEN_IMPLEMENTED_RECORD_FAMILIES = (
    "AuthorityEpoch",
    "AuthorityState",
    "CutoverRequest",
    "ReadinessPackage",
    "HumanAuthorization",
    "CutoverCandidate",
    "Certification",
    "PublicationAttempt",
    "PublicationEvidence",
    "ConcurrencyConflict",
    "RecoveryJournalEntry",
)

# Narrowed by Phase 136AL: `NotificationAuthorityBinding` (Group 7) is now
# authorized, legitimately-implemented record-family model -- removed from
# this still-forbidden list. Narrowed further by Phase 136AN:
# `MarkerAuthorityBinding` (Group 8) is now authorized, legitimately-
# implemented record-family model -- removed from this still-forbidden
# list. Narrowed further by Phase 136AP: `FinalizationReceiptAuthorityBinding`
# (Group 9) is now authorized, legitimately-implemented record-family
# model -- removed from this still-forbidden list.
# Narrowed further by Phase 136AR (Typed Model Implementation Group
# 10): `CompatibilityState` is now authorized, legitimately-
# implemented record-family model -- removed from this
# still-forbidden list.
FIVE_MUST_NOT_EXIST_RECORD_FAMILIES = (
    "QuarantineRecord",
)


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def _assert_schema_valid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is OutcomeStatus.VALID, result.issues


def _assert_schema_invalid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is not OutcomeStatus.VALID


def _sha256(fill: str) -> str:
    assert len(fill) == 1
    return fill * 64


def _disclosure(role: str = "derivative") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "Independent-verification schema-validated non-authoritative record.",
    }


def _ref(record_id: str, digest_fill: str, family: str, *, with_schema: str | None = None) -> dict:
    out = {"record_id": record_id, "record_digest": _sha256(digest_fill), "record_family": family}
    if with_schema is not None:
        out["schema_id"] = with_schema
        out["schema_version"] = "1.0"
    return out


def _request_ref(record_id: str = "cutreq-00000001", digest: str = "a") -> dict:
    return _ref(record_id, digest, "cutover_request", with_schema=CUTOVER_REQUEST_SCHEMA_ID)


def _authority_state_ref(record_id: str = "authstat-0000001", digest: str = "2") -> dict:
    return _ref(record_id, digest, "authority_state")


def _publication_attempt_ref(record_id: str = "pubattem-0000001", digest: str = "0") -> dict:
    return _ref(record_id, digest, "publication_attempt")


def _generation_ref(gen_id: str = "generatn-0000001", digest: str = "6") -> dict:
    return {"generation_id": gen_id, "generation_digest": _sha256(digest)}


def _cc_wire(**overrides) -> dict:
    record = {
        "schema_id": CONCURRENCY_CONFLICT_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "concurrency_conflict",
        "record_id": "concflct-0000001",
        "record_digest": _sha256("0"),
        "created_at": "2026-07-18T12:00:00Z",
        "migration_epoch": "epoch-001",
        "actors": ["operator@example.com", _publication_attempt_ref()],
        "requests": [_request_ref()],
        "type": "dual_writer",
        "winner": None,
        "recovery_requirement": "operator_review_required",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


def _rje_wire(**overrides) -> dict:
    record = {
        "schema_id": RECOVERY_JOURNAL_ENTRY_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "recovery_journal_entry",
        "record_id": "recjrnl-00000001",
        "record_digest": _sha256("4"),
        "created_at": "2026-07-18T12:00:00Z",
        "migration_epoch": "epoch-001",
        "transition_id": "trans-0000001",
        "sequence": 0,
        "prior_entry_digest": None,
        "operation_reference": _request_ref(),
        "prior_state_reference": _authority_state_ref("authstat-0000002", "3"),
        "new_state_reference": _authority_state_ref("authstat-0000003", "5"),
        "authority_state_reference": _authority_state_ref("authstat-0000004", "7"),
        "generation_reference": _generation_ref(),
        "external_effect_state": "none",
        "retry_replay_classification": "original",
        "state": "recorded",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


# ---------------------------------------------------------------------------
# 1. Inventory verification (independent AST + runtime introspection,
#    package export, and registry discovery)
# ---------------------------------------------------------------------------


def test_136ak_exactly_eleven_record_family_classes_exist_via_ast():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        class_names |= {
            node.name for node in ast.walk(ast.parse(path.read_text())) if isinstance(node, ast.ClassDef)
        }
    for expected in ELEVEN_IMPLEMENTED_RECORD_FAMILIES:
        assert expected in class_names, f"missing expected record family class {expected!r}"
    for forbidden in FIVE_MUST_NOT_EXIST_RECORD_FAMILIES:
        assert forbidden not in class_names, f"forbidden record family class {forbidden!r} exists"
    # Exactly eleven -- no twelfth undisclosed family class either.
    present_record_families = class_names & set(ELEVEN_IMPLEMENTED_RECORD_FAMILIES + FIVE_MUST_NOT_EXIST_RECORD_FAMILIES)
    assert present_record_families == set(ELEVEN_IMPLEMENTED_RECORD_FAMILIES)


def test_136ak_package_export_inventory_via_runtime_import():
    for expected in ELEVEN_IMPLEMENTED_RECORD_FAMILIES:
        assert hasattr(auth, expected)
        assert isinstance(getattr(auth, expected), type)
        assert expected in auth.__all__
    for forbidden in FIVE_MUST_NOT_EXIST_RECORD_FAMILIES:
        assert not hasattr(auth, forbidden)
        assert forbidden not in auth.__all__


def test_136ak_group_6_module_defines_exactly_its_own_two_families():
    tree = ast.parse(RECOVERY_CONCURRENCY_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_names = class_names & set(
        ELEVEN_IMPLEMENTED_RECORD_FAMILIES + FIVE_MUST_NOT_EXIST_RECORD_FAMILIES
    )
    assert record_family_names == {"ConcurrencyConflict", "RecoveryJournalEntry"}


def test_136ak_no_forbidden_family_source_file_exists():
    # Narrowed by Phase 136AR: `compatibility_quarantine.py` (Group 10,
    # `CompatibilityState` only) is now a legitimate, authorized module;
    # removed from this still-forbidden list. No other later-group source
    # file (i.e. one containing `QuarantineRecord`) exists.
    for forbidden_file in ():
        assert not (AUTHORITY_PACKAGE_DIR / forbidden_file).exists()
    assert (AUTHORITY_PACKAGE_DIR / "compatibility_quarantine.py").exists()


def test_136ak_schema_registry_discovers_both_group_6_schemas(schema_registry):
    assert CONCURRENCY_CONFLICT_SCHEMA_ID in schema_registry.schema_ids
    assert RECOVERY_JOURNAL_ENTRY_SCHEMA_ID in schema_registry.schema_ids
    assert schema_registry.document(CONCURRENCY_CONFLICT_SCHEMA_ID) is not None
    assert schema_registry.document(RECOVERY_JOURNAL_ENTRY_SCHEMA_ID) is not None


# ---------------------------------------------------------------------------
# 2. Independent schema re-derivation: valid wire round-trips against the
#    live executable schema registry (not the Python model's own opinion)
# ---------------------------------------------------------------------------


def test_136ak_minimal_valid_concurrency_conflict_is_schema_valid_and_constructs(schema_registry):
    wire = _cc_wire()
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136ak_minimal_valid_recovery_journal_entry_is_schema_valid_and_constructs(schema_registry):
    wire = _rje_wire()
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136ak_cas_mismatch_conflict_with_expected_observed_state_valid(schema_registry):
    wire = _cc_wire(
        type="cas_mismatch",
        expected_state=_authority_state_ref("authstat-0000005", "8"),
        observed_state=_authority_state_ref("authstat-0000006", "9"),
        winner=_publication_attempt_ref("pubattem-0000002", "1"),
    )
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.expected_state.record_id.value == "authstat-0000005"
    assert model.observed_state.record_id.value == "authstat-0000006"
    assert model.winner.record_id.value == "pubattem-0000002"


def test_136ak_journal_entry_with_all_optional_fields_populated_valid(schema_registry):
    wire = _rje_wire(
        sequence=1,
        prior_entry_digest=_sha256("f"),
        publication_attempt_reference=_publication_attempt_ref(),
        state="actioned",
        operator_review={"notes": "Reviewed by operator."},
        recovery_action={"description": "Re-issued the publication attempt."},
    )
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.publication_attempt_reference.record_family.value == "publication_attempt"
    assert model.operator_review.notes == "Reviewed by operator."
    assert model.recovery_action.description == "Re-issued the publication attempt."


# ---------------------------------------------------------------------------
# 3. Required-field re-derivation: dropping any required key must be
#    rejected both by the live schema and by the model
# ---------------------------------------------------------------------------


CONCURRENCY_CONFLICT_REQUIRED_FIELDS = (
    "schema_id", "schema_version", "contract_version", "record_type", "record_id",
    "record_digest", "created_at", "migration_epoch", "actors", "requests", "type",
    "winner", "recovery_requirement", "limitations", "authority_disclosure",
)

RECOVERY_JOURNAL_ENTRY_REQUIRED_FIELDS = (
    "schema_id", "schema_version", "contract_version", "record_type", "record_id",
    "record_digest", "created_at", "migration_epoch", "transition_id", "sequence",
    "prior_entry_digest", "operation_reference", "prior_state_reference",
    "new_state_reference", "authority_state_reference", "generation_reference",
    "external_effect_state", "retry_replay_classification", "state", "limitations",
    "authority_disclosure",
)


@pytest.mark.parametrize("field", CONCURRENCY_CONFLICT_REQUIRED_FIELDS)
def test_136ak_concurrency_conflict_missing_required_field_rejected(field, schema_registry):
    wire = _cc_wire()
    del wire[field]
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, KeyError, TypedModelInternalInvariantError)):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("field", RECOVERY_JOURNAL_ENTRY_REQUIRED_FIELDS)
def test_136ak_recovery_journal_entry_missing_required_field_rejected(field, schema_registry):
    wire = _rje_wire()
    del wire[field]
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, KeyError, TypedModelInternalInvariantError)):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_concurrency_conflict_unknown_field_rejected(schema_registry):
    wire = _cc_wire(unknown_field_xyz="nope")
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_recovery_journal_entry_unknown_field_rejected(schema_registry):
    wire = _rje_wire(unknown_field_xyz="nope")
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 4. Discriminator / schema_id / schema_version / contract_version fidelity
# ---------------------------------------------------------------------------


def test_136ak_concurrency_conflict_wrong_record_type_rejected(schema_registry):
    wire = _cc_wire(record_type="recovery_journal_entry")
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_concurrency_conflict_wrong_schema_id_rejected(schema_registry):
    wire = _cc_wire(schema_id=RECOVERY_JOURNAL_ENTRY_SCHEMA_ID)
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_recovery_journal_entry_wrong_contract_version_rejected(schema_registry):
    wire = _rje_wire(contract_version="2.0")
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_unsupported_schema_version_rejected_before_payload_inspection():
    wire = _cc_wire()
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="2.0")
    wire2 = _rje_wire()
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.RecoveryJournalEntry.from_dict(wire2, schema_version="9.9")


# ---------------------------------------------------------------------------
# 5. Enum verification -- every valid member, plus invalid/case/whitespace/
#    null/omission/int/bool per family-local enum.
# ---------------------------------------------------------------------------


CONFLICT_TYPE_MEMBERS = ("cas_mismatch", "dual_writer", "stale_expectation", "unknown_winner")
EXTERNAL_EFFECT_STATE_MEMBERS = ("none", "pending", "applied", "unknown")
RETRY_REPLAY_CLASSIFICATION_MEMBERS = ("original", "retry", "replay")
JOURNAL_STATE_MEMBERS = ("recorded", "reviewed", "actioned", "superseded")


@pytest.mark.parametrize("member", CONFLICT_TYPE_MEMBERS)
def test_136ak_conflict_type_every_valid_member_accepted(member, schema_registry):
    if member == "cas_mismatch":
        wire = _cc_wire(
            type=member,
            expected_state=_authority_state_ref("authstat-0000007", "1"),
            observed_state=_authority_state_ref("authstat-0000008", "2"),
        )
    else:
        wire = _cc_wire(type=member)
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.type.value == member


@pytest.mark.parametrize(
    "bad_value", ["CAS_MISMATCH", "cas mismatch", " dual_writer", "dual_writer ", "unknown", "", None, 1, True]
)
def test_136ak_conflict_type_invalid_values_rejected(bad_value, schema_registry):
    wire = _cc_wire(type=bad_value)
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_conflict_type_field_omission_rejected(schema_registry):
    wire = _cc_wire()
    del wire["type"]
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("member", EXTERNAL_EFFECT_STATE_MEMBERS)
def test_136ak_external_effect_state_every_valid_member_accepted(member, schema_registry):
    wire = _rje_wire(external_effect_state=member)
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.external_effect_state.value == member


@pytest.mark.parametrize("bad_value", ["NONE", "Applied", "pending ", "", None, 0, False])
def test_136ak_external_effect_state_invalid_values_rejected(bad_value, schema_registry):
    wire = _rje_wire(external_effect_state=bad_value)
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("member", RETRY_REPLAY_CLASSIFICATION_MEMBERS)
def test_136ak_retry_replay_classification_every_valid_member_accepted(member, schema_registry):
    wire = _rje_wire(retry_replay_classification=member)
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.retry_replay_classification.value == member


@pytest.mark.parametrize("bad_value", ["Original", "re-try", "REPLAY", "resumed", "", None, 2])
def test_136ak_retry_replay_classification_invalid_values_rejected(bad_value, schema_registry):
    wire = _rje_wire(retry_replay_classification=bad_value)
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("member", JOURNAL_STATE_MEMBERS)
def test_136ak_journal_state_every_valid_member_accepted_with_conditional_satisfaction(member, schema_registry):
    kwargs = {"state": member}
    if member in ("reviewed", "actioned", "superseded"):
        kwargs["operator_review"] = {"notes": "Independent-verification note."}
    if member == "actioned":
        kwargs["recovery_action"] = {"description": "Independent-verification action."}
    wire = _rje_wire(**kwargs)
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.state.value == member


@pytest.mark.parametrize("bad_value", ["RECORDED", "closed", "", None, 3, False])
def test_136ak_journal_state_invalid_values_rejected(bad_value, schema_registry):
    wire = _rje_wire(state=bad_value)
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_recovery_requirement_uses_shared_ten_value_recovery_state(schema_registry):
    from pcae.cltr.authority.enums import RecoveryState

    all_ten = {
        "none_required", "resume_safe", "retry_required", "operator_review_required",
        "reconciliation_required", "quarantine_required", "conflict_unresolved",
        "publication_uncertain_unresolved", "terminal_recovered", "terminal_unrecoverable",
    }
    assert {m.value for m in RecoveryState} == all_ten
    for member in all_ten:
        wire = _cc_wire(recovery_requirement=member)
        _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
        model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
        assert model.recovery_requirement.value == member


# ---------------------------------------------------------------------------
# 6. Conditional-rule verification: both positive and negative cases,
#    guarding against unauthorized semantic strengthening not present in
#    the executable schema (e.g. no cross-linking retry<->failure,
#    rollback<->publication, resume<->checkpoint anywhere in this group).
# ---------------------------------------------------------------------------


def test_136ak_cas_mismatch_without_expected_state_rejected(schema_registry):
    wire = _cc_wire(type="cas_mismatch", observed_state=_authority_state_ref())
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_cas_mismatch_without_observed_state_rejected(schema_registry):
    wire = _cc_wire(type="cas_mismatch", expected_state=_authority_state_ref())
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("non_cas_type", ["dual_writer", "stale_expectation", "unknown_winner"])
def test_136ak_non_cas_mismatch_forbids_expected_state(non_cas_type, schema_registry):
    wire = _cc_wire(type=non_cas_type, expected_state=_authority_state_ref())
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("non_cas_type", ["dual_writer", "stale_expectation", "unknown_winner"])
def test_136ak_non_cas_mismatch_forbids_observed_state(non_cas_type, schema_registry):
    wire = _cc_wire(type=non_cas_type, observed_state=_authority_state_ref())
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_winner_key_always_required_even_when_null():
    wire = _cc_wire()
    del wire["winner"]
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_sequence_zero_requires_null_prior_entry_digest(schema_registry):
    wire = _rje_wire(sequence=0, prior_entry_digest=_sha256("b"))
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_sequence_nonzero_requires_non_null_prior_entry_digest(schema_registry):
    wire = _rje_wire(sequence=1, prior_entry_digest=None)
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_sequence_nonzero_with_well_formed_prior_digest_accepted(schema_registry):
    wire = _rje_wire(sequence=42, prior_entry_digest=_sha256("c"))
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.sequence == 42


def test_136ak_sequence_negative_rejected(schema_registry):
    wire = _rje_wire(sequence=-1, prior_entry_digest=_sha256("c"))
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_sequence_boolean_rejected():
    # bool is a subclass of int in Python; the schema requires a genuine
    # integer, so True/False must not silently pass as sequence values.
    wire = _rje_wire(sequence=True, prior_entry_digest=None)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("state", ["reviewed", "actioned", "superseded"])
def test_136ak_operator_review_required_states_reject_absence(state, schema_registry):
    kwargs = {"state": state}
    if state == "actioned":
        kwargs["recovery_action"] = {"description": "x"}
    wire = _rje_wire(**kwargs)
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_recorded_state_forbids_operator_review(schema_registry):
    wire = _rje_wire(state="recorded", operator_review={"notes": "should not be here"})
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("state", ["recorded", "reviewed", "superseded"])
def test_136ak_non_actioned_states_forbid_recovery_action(state, schema_registry):
    kwargs = {"state": state}
    if state in ("reviewed", "superseded"):
        kwargs["operator_review"] = {"notes": "x"}
    kwargs["recovery_action"] = {"description": "should not be here"}
    wire = _rje_wire(**kwargs)
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_actioned_without_recovery_action_rejected(schema_registry):
    wire = _rje_wire(state="actioned", operator_review={"notes": "x"})
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_no_unauthorized_retry_requires_failure_strengthening(schema_registry):
    """The schema does not link retry_replay_classification='retry' to any
    other field (no failure/error field exists on this record at all); a
    'retry' classification must be accepted standalone with no additional
    requirement invented by the implementation."""

    wire = _rje_wire(retry_replay_classification="retry")
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_no_unauthorized_rollback_requires_publication_strengthening(schema_registry):
    """publication_attempt_reference is freely optional (NON-BLOCKING-136R-1
    in the schema description); no retry/replay/rollback value may force
    it to be required, and no rollback-shaped value exists in this
    record's vocabulary at all."""

    wire = _rje_wire(retry_replay_classification="replay")
    assert "publication_attempt_reference" not in wire
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.publication_attempt_reference is ABSENT


def test_136ak_conflict_requires_expected_ne_observed_is_not_enforced(schema_registry):
    """The schema never compares expected_state and observed_state for
    inequality -- a cas_mismatch conflict whose expected and observed
    references are identical must still be schema-valid and constructible
    (semantic plausibility is explicitly Layer 4, never enforced here)."""

    same_ref = _authority_state_ref("authstat-0000009", "3")
    wire = _cc_wire(type="cas_mismatch", expected_state=same_ref, observed_state=same_ref)
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.expected_state == model.observed_state


# ---------------------------------------------------------------------------
# 7. Reference verification: target family, schema_id/schema_version
#    cross-family requirement, wrapper type, nullability, forward
#    references, no lookup.
# ---------------------------------------------------------------------------


def test_136ak_request_reference_wrong_family_rejected(schema_registry):
    wire = _cc_wire(requests=[_ref("authstat-0000010", "1", "authority_state", with_schema=CUTOVER_REQUEST_SCHEMA_ID)])
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, WrongFamilyReferenceError)):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_request_reference_missing_schema_id_rejected(schema_registry):
    bare_request = {"record_id": "cutreq-00000002", "record_digest": _sha256("d"), "record_family": "cutover_request"}
    wire = _cc_wire(requests=[bare_request])
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_authority_state_reference_wrong_family_rejected(schema_registry):
    wire = _rje_wire(
        authority_state_reference=_ref("cutreq-00000003", "e", "cutover_request", with_schema=CUTOVER_REQUEST_SCHEMA_ID)
    )
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, WrongFamilyReferenceError)):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_publication_attempt_reference_wrong_family_rejected(schema_registry):
    wire = _rje_wire(publication_attempt_reference=_authority_state_ref("authstat-0000011", "4"))
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, WrongFamilyReferenceError)):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_operation_prior_new_state_references_accept_any_family_no_restriction(schema_registry):
    """Sec.28 names no family restriction for operation_reference,
    prior_state_reference, or new_state_reference (NON-BLOCKING-136R-3);
    an out-of-the-ordinary family here (e.g. certification) must still be
    schema-valid -- inventing a restriction the schema does not declare
    would itself be an unauthorized strengthening."""

    wire = _rje_wire(
        operation_reference=_ref("certfctn-0000001", "1", "certification"),
        prior_state_reference=_ref("certfctn-0000002", "2", "certification"),
        new_state_reference=_ref("certfctn-0000003", "3", "certification"),
    )
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.operation_reference.record_family.value == "certification"


def test_136ak_valid_but_nonexistent_reference_succeeds_no_lookup_performed(schema_registry, monkeypatch):
    """A reference naming a plausible-but-never-registered record_id must
    construct successfully -- no filesystem/registry lookup may be
    performed to check existence."""

    def _boom(*a, **k):
        raise AssertionError("unexpected filesystem access during reference construction")

    monkeypatch.setattr("builtins.open", _boom)
    wire = _cc_wire(requests=[_request_ref("cutreq-99999999", "f")])
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.requests[0].record_id.value == "cutreq-99999999"


def test_136ak_generation_reference_wrapper_type_and_pairing(schema_registry):
    wire = _rje_wire()
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert type(model.generation_reference).__name__ == "GenerationReference"
    assert model.generation_reference.generation_id.value == "generatn-0000001"
    assert model.generation_reference.generation_digest.value == _sha256("6")


def test_136ak_actor_entry_accepts_principal_identifier_string_form(schema_registry):
    wire = _cc_wire(actors=["operator-a@example.com", "operator-b@example.com"])
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert all(type(a).__name__ == "PrincipalIdentifier" for a in model.actors)


def test_136ak_actor_entry_accepts_record_reference_form(schema_registry):
    wire = _cc_wire(actors=[_publication_attempt_ref("pubattem-0000003", "2"), _publication_attempt_ref("pubattem-0000004", "3")])
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert all(type(a).__name__ == "RecordReference" for a in model.actors)


def test_136ak_actors_below_minimum_two_rejected(schema_registry):
    wire = _cc_wire(actors=["only-one@example.com"])
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_requests_below_minimum_one_rejected(schema_registry):
    wire = _cc_wire(requests=[])
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 8. Absent vs null verification for every optional field
# ---------------------------------------------------------------------------


def test_136ak_concurrency_conflict_expected_observed_state_omitted_by_default():
    wire = _cc_wire()
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.expected_state is ABSENT
    assert model.observed_state is ABSENT
    assert "expected_state" not in model.to_dict()
    assert "observed_state" not in model.to_dict()


def test_136ak_concurrency_conflict_expected_state_explicit_null_rejected_not_collapsed_to_absent(schema_registry):
    """Sec.7.4's absent-versus-null contract: expected_state is 'omitted
    (never null)' when not applicable -- an explicit null must be
    rejected, never silently treated the same as omission."""

    wire = _cc_wire(type="dual_writer")
    wire["expected_state"] = None
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_recovery_journal_entry_publication_attempt_reference_absent_by_default():
    wire = _rje_wire()
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.publication_attempt_reference is ABSENT
    assert "publication_attempt_reference" not in model.to_dict()


def test_136ak_recovery_journal_entry_operator_review_recovery_action_absent_by_default():
    wire = _rje_wire()
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.operator_review is ABSENT
    assert model.recovery_action is ABSENT
    serialized = model.to_dict()
    assert "operator_review" not in serialized
    assert "recovery_action" not in serialized


def test_136ak_winner_null_is_distinct_from_absent_and_always_serialized():
    wire = _cc_wire(winner=None)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.winner is None
    serialized = model.to_dict()
    assert "winner" in serialized
    assert serialized["winner"] is None


def test_136ak_prior_entry_digest_null_is_distinct_from_absent_and_always_serialized():
    wire = _rje_wire(sequence=0, prior_entry_digest=None)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.prior_entry_digest is None
    serialized = model.to_dict()
    assert "prior_entry_digest" in serialized
    assert serialized["prior_entry_digest"] is None


def test_136ak_extensions_absent_by_default_and_explicit_null_rejected(schema_registry):
    wire = _cc_wire()
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model._extensions is ABSENT
    wire_with_null_ext = _cc_wire(_extensions=None)
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire_with_null_ext, schema_version="1.0")


def test_136ak_extensions_populated_string_valued_map_round_trips(schema_registry):
    wire = _cc_wire(_extensions={"note": "independent-verification-tag"})
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.to_dict()["_extensions"] == {"note": "independent-verification-tag"}


def test_136ak_extensions_non_string_value_rejected(schema_registry):
    wire = _cc_wire(_extensions={"note": 123})
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_extensions_reserved_key_collision_rejected():
    wire = _cc_wire(_extensions={"migration_epoch": "shadowing-attempt"})
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 9. Authority-role locally-forbidden 'authoritative' verification
# ---------------------------------------------------------------------------


def test_136ak_concurrency_conflict_authoritative_role_rejected(schema_registry):
    wire = _cc_wire(authority_disclosure=_disclosure(role="authoritative"))
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_recovery_journal_entry_authoritative_role_rejected(schema_registry):
    wire = _rje_wire(authority_disclosure=_disclosure(role="authoritative"))
    _assert_schema_invalid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136ak_is_authoritative_true_rejected():
    disclosure = _disclosure()
    disclosure["is_authoritative"] = True
    wire = _cc_wire(authority_disclosure=disclosure)
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 10. Immutability verification (recursive; mutating source after
#     construction must never affect the model)
# ---------------------------------------------------------------------------


def test_136ak_concurrency_conflict_is_frozen_dataclass():
    model = auth.ConcurrencyConflict.from_dict(_cc_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.type = rc.ConflictType.DUAL_WRITER


def test_136ak_recovery_journal_entry_is_frozen_dataclass():
    model = auth.RecoveryJournalEntry.from_dict(_rje_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.sequence = 999


def test_136ak_actors_and_requests_are_immutable_tuples_not_lists():
    model = auth.ConcurrencyConflict.from_dict(_cc_wire(), schema_version="1.0")
    assert isinstance(model.actors, tuple)
    assert isinstance(model.requests, tuple)


def test_136ak_mutating_source_actors_list_after_construction_does_not_affect_model():
    source_actors = ["a@example.com", "b@example.com"]
    wire = _cc_wire(actors=list(source_actors))
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    wire["actors"].append("c@example.com")
    wire["actors"][0] = "tampered@example.com"
    assert len(model.actors) == 2
    assert model.actors[0].value == "a@example.com"


def test_136ak_mutating_source_requests_list_after_construction_does_not_affect_model():
    wire = _cc_wire()
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    original_request_id = model.requests[0].record_id.value
    wire["requests"][0]["record_id"] = "cutreq-99999998"
    assert model.requests[0].record_id.value == original_request_id


def test_136ak_mutating_source_limitations_list_after_construction_does_not_affect_model():
    source_limitations = ["limitation one"]
    wire = _cc_wire(limitations=source_limitations)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    source_limitations.append("limitation two (added after construction)")
    assert len(model.limitations.entries) == 1


def test_136ak_mutating_source_extensions_mapping_after_construction_does_not_affect_model(schema_registry):
    source_extensions = {"note": "original"}
    wire = _cc_wire(_extensions=source_extensions)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    source_extensions["note"] = "tampered"
    source_extensions["new_key"] = "also tampered"
    assert model.to_dict()["_extensions"] == {"note": "original"}


def test_136ak_deep_copy_of_model_produces_structurally_equal_but_independent_object():
    model = auth.RecoveryJournalEntry.from_dict(_rje_wire(), schema_version="1.0")
    duplicate = copy.deepcopy(model)
    assert duplicate == model
    assert duplicate is not model


# ---------------------------------------------------------------------------
# 11. Equality verification: structural, not identifier-only/digest-only
# ---------------------------------------------------------------------------


def test_136ak_concurrency_conflict_equality_changes_when_any_field_changes():
    base = auth.ConcurrencyConflict.from_dict(_cc_wire(), schema_version="1.0")
    same = auth.ConcurrencyConflict.from_dict(_cc_wire(), schema_version="1.0")
    assert base == same

    different_type = auth.ConcurrencyConflict.from_dict(_cc_wire(type="stale_expectation"), schema_version="1.0")
    assert base != different_type

    different_epoch = auth.ConcurrencyConflict.from_dict(_cc_wire(migration_epoch="epoch-002"), schema_version="1.0")
    assert base != different_epoch

    different_recovery = auth.ConcurrencyConflict.from_dict(
        _cc_wire(recovery_requirement="retry_required"), schema_version="1.0"
    )
    assert base != different_recovery


def test_136ak_recovery_journal_entry_equality_rejects_identifier_only_and_digest_only_comparison():
    base = auth.RecoveryJournalEntry.from_dict(_rje_wire(), schema_version="1.0")
    same_identity_different_state = auth.RecoveryJournalEntry.from_dict(
        _rje_wire(external_effect_state="pending"), schema_version="1.0"
    )
    # Same record_id/record_digest (envelope identity) but a different
    # non-identity field -- structural equality must still report unequal.
    assert base.envelope.record_id == same_identity_different_state.envelope.record_id
    assert base.envelope.record_digest == same_identity_different_state.envelope.record_digest
    assert base != same_identity_different_state


def test_136ak_reference_equality_is_structural_not_family_only():
    ref_a = auth.RecordReference(
        record_id=auth.RecordId("cutreq-00000001"),
        record_digest=auth.ReferencedRecordDigest(_sha256("a")),
        record_family=auth.RecordFamily.CUTOVER_REQUEST,
    )
    ref_b = auth.RecordReference(
        record_id=auth.RecordId("cutreq-00000002"),
        record_digest=auth.ReferencedRecordDigest(_sha256("b")),
        record_family=auth.RecordFamily.CUTOVER_REQUEST,
    )
    assert ref_a != ref_b


# ---------------------------------------------------------------------------
# 12. Error-behavior determinism verification
# ---------------------------------------------------------------------------


def test_136ak_invalid_digest_wrapper_rejected():
    with pytest.raises(Exception):
        auth.ConcurrencyConflict.from_dict(
            _cc_wire(record_digest="not-a-valid-sha256-hex"), schema_version="1.0"
        )


def test_136ak_invalid_identifier_wrapper_rejected():
    with pytest.raises(Exception):
        auth.RecoveryJournalEntry.from_dict(
            _rje_wire(transition_id="not-trans-prefixed"), schema_version="1.0"
        )


def test_136ak_malformed_reference_missing_record_family_rejected(schema_registry):
    malformed = {"record_id": "cutreq-00000004", "record_digest": _sha256("1")}
    wire = _cc_wire(requests=[malformed])
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_invalid_array_shape_actors_not_a_list_rejected(schema_registry):
    wire = _cc_wire(actors="not-a-list")
    _assert_schema_invalid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136ak_construction_errors_are_deterministic_across_repeated_attempts():
    bad_wire = _cc_wire(type="not-a-real-type")
    errors = []
    for _ in range(3):
        try:
            auth.ConcurrencyConflict.from_dict(bad_wire, schema_version="1.0")
        except Exception as exc:  # noqa: BLE001
            errors.append(type(exc))
    assert len(errors) == 3
    assert len(set(errors)) == 1


# ---------------------------------------------------------------------------
# 13. Purely-representational behavior: reject any operational capability
# ---------------------------------------------------------------------------


FORBIDDEN_OPERATIONAL_SYMBOLS = (
    "detect_conflict", "resolve_conflict", "select_winner", "compare_and_swap",
    "execute_cas", "acquire_lock", "release_lock", "retry_publication",
    "retry", "replay", "rollback", "resume", "execute_recovery", "repair_state",
    "persist", "append_to_journal", "validate_sequence_continuity",
)


def test_136ak_module_defines_no_operational_function_or_method():
    tree = ast.parse(RECOVERY_CONCURRENCY_MODULE.read_text())
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_OPERATIONAL_SYMBOLS:
        assert forbidden not in defined_names, f"forbidden operational symbol {forbidden!r} defined"


def test_136ak_module_source_never_imports_filesystem_socket_or_subprocess():
    tree = ast.parse(RECOVERY_CONCURRENCY_MODULE.read_text())
    forbidden_modules = ("socket", "subprocess", "os.path", "shutil", "requests", "urllib")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(f) for f in forbidden_modules)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(f) for f in forbidden_modules)


def test_136ak_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    model = auth.RecoveryJournalEntry.from_dict(_rje_wire(), schema_version="1.0")
    model.to_dict()
    repr(model)


def test_136ak_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    model_a = auth.ConcurrencyConflict.from_dict(_cc_wire(), schema_version="1.0")
    model_a.to_dict()
    model_b = auth.RecoveryJournalEntry.from_dict(_rje_wire(), schema_version="1.0")
    model_b.to_dict()


def test_136ak_no_filesystem_write_during_construction_serialization_equality_repr(monkeypatch):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError(f"unexpected filesystem write attempted: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    model = auth.ConcurrencyConflict.from_dict(_cc_wire(), schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136ak_package_reimport_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    import importlib

    importlib.reload(rc)


# ---------------------------------------------------------------------------
# 14. Runtime isolation: no production import of pcae.cltr.authority
# ---------------------------------------------------------------------------


def test_136ak_no_production_module_imports_authority_package():
    forbidden_prefixes = ("pcae.cltr.authority",)
    scan_roots = (
        REPO_ROOT / "src" / "pcae" / "commands",
        REPO_ROOT / "src" / "pcae" / "core",
        REPO_ROOT / "src" / "pcae" / "cltr",
        REPO_ROOT / "src" / "pcae" / "runtime",
    )
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if "authority" in path.parts:
                continue
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in forbidden_prefixes:
                            assert not alias.name.startswith(forbidden), (path, alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    for forbidden in forbidden_prefixes:
                        assert not node.module.startswith(forbidden), (path, node.module)


def test_136ak_authority_recovery_concurrency_module_does_not_import_lifecycle_execution():
    forbidden_modules = (
        "pcae.cltr.notification", "pcae.cltr.marker", "pcae.cltr.receipt",
        "pcae.commands", "pcae.core", "pcae.runtime",
    )
    tree = ast.parse(RECOVERY_CONCURRENCY_MODULE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in forbidden_modules:
                    assert not alias.name.startswith(forbidden)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for forbidden in forbidden_modules:
                assert not node.module.startswith(forbidden)


# ---------------------------------------------------------------------------
# 15. Packaging verification (fresh wheel/sdist build, isolated install)
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_136ak_wheel_build_contains_group_6_module_and_no_later_family(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    import zipfile

    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()
    assert "pcae/cltr/authority/recovery_concurrency.py" in names
    for forbidden in ("bindings", "compatibility_quarantine"):
        assert f"pcae/cltr/authority/{forbidden}.py" not in names


@pytest.mark.slow
def test_136ak_isolated_install_all_eleven_families_import_and_round_trip(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, capture_output=True, text=True)
    venv_python = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--quiet", str(wheels[0])],
        check=True, capture_output=True, text=True,
    )
    probe = (
        "from pcae.cltr import authority as auth\n"
        "for name in " + repr(ELEVEN_IMPLEMENTED_RECORD_FAMILIES) + ":\n"
        "    assert hasattr(auth, name), name\n"
        "for name in " + repr(FIVE_MUST_NOT_EXIST_RECORD_FAMILIES) + ":\n"
        "    assert not hasattr(auth, name), name\n"
        "wire = {\n"
        "    'schema_id': " + repr(CONCURRENCY_CONFLICT_SCHEMA_ID) + ",\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'concurrency_conflict', 'record_id': 'concflct-0000099',\n"
        "    'record_digest': '0'*64, 'created_at': '2026-07-18T12:00:00Z',\n"
        "    'migration_epoch': 'epoch-001',\n"
        "    'actors': ['operator@example.com', 'operator2@example.com'],\n"
        "    'requests': [{'record_id': 'cutreq-00000099', 'record_digest': 'a'*64,\n"
        "                  'record_family': 'cutover_request',\n"
        "                  'schema_id': " + repr(CUTOVER_REQUEST_SCHEMA_ID) + ", 'schema_version': '1.0'}],\n"
        "    'type': 'dual_writer', 'winner': None,\n"
        "    'recovery_requirement': 'operator_review_required',\n"
        "    'limitations': [], 'authority_disclosure': {'authority_role': 'derivative',\n"
        "        'is_authoritative': False, 'disclosure_text': 'ok'},\n"
        "}\n"
        "model = auth.ConcurrencyConflict.from_dict(wire, schema_version='1.0')\n"
        "assert model.to_dict() == wire\n"
        "print('ISOLATED_INSTALL_OK')\n"
    )
    result = subprocess.run(
        [str(venv_python), "-c", probe], check=True, capture_output=True, text=True,
    )
    assert "ISOLATED_INSTALL_OK" in result.stdout
