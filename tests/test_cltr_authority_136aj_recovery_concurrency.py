"""Phase 136AJ: Stage 3 Typed Authority Model Recovery and Concurrency
Implementation (Typed Model Implementation Group 6).

Focused tests for ``src/pcae/cltr/authority/recovery_concurrency.py``: the
``ConcurrencyConflict`` and ``RecoveryJournalEntry`` typed record models.
Covers exact field mapping, strict constructor behavior, family-
restriction enforcement, conditional branches, enum fidelity, schema
conformance, no-later-group-model inventory, no-conflict-detection/no-CAS-
execution/no-recovery-execution/no-journal-persistence semantics,
no-side-effect, and runtime-isolation.

This module implements only Typed Model Implementation Group 6
(``ConcurrencyConflict``, ``RecoveryJournalEntry``). No other
record-family model (``NotificationAuthorityBinding``,
``MarkerAuthorityBinding``, ``FinalizationReceiptAuthorityBinding``,
``CompatibilityState``, ``QuarantineRecord``) is implemented or exercised
here.
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
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
RECOVERY_CONCURRENCY_MODULE = AUTHORITY_PACKAGE_DIR / "recovery_concurrency.py"

PRODUCTION_SCAN_ROOTS = (
    REPO_ROOT / "src" / "pcae" / "commands",
    REPO_ROOT / "src" / "pcae" / "core",
    REPO_ROOT / "src" / "pcae" / "cltr",
    REPO_ROOT / "src" / "pcae" / "runtime",
)

FORBIDDEN_SYMBOLS = (
    "detect_conflict",
    "has_conflict",
    "compare_expected_observed",
    "check_generation",
    "load_current_state",
    "current_state_mismatch",
    "compare_and_swap",
    "execute_cas",
    "retry_on_conflict",
    "acquire_lock",
    "release_lock",
    "atomic_replace",
    "recover",
    "execute_recovery",
    "resume",
    "replay",
    "rollback",
    "repair_state",
    "apply_checkpoint",
    "restore",
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
LATER_GROUP_MODEL_NAMES = (
    "QuarantineRecord",
)

CONCURRENCY_CONFLICT_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/concurrency_conflict.schema.json"
)
RECOVERY_JOURNAL_ENTRY_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/recovery_journal_entry.schema.json"
)
CUTOVER_REQUEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/cutover_request.schema.json"
PUBLICATION_ATTEMPT_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/publication_attempt.schema.json"
)


def _sha256_hex(fill: str) -> str:
    assert len(fill) == 1
    return fill * 64


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def _assert_schema_valid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is OutcomeStatus.VALID, result.issues


# ---------------------------------------------------------------------------
# Wire fixtures
# ---------------------------------------------------------------------------


def _disclosure(role: str = "derivative") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "Non-authoritative schema-validated companion record.",
    }


def _ref(record_id: str, digest: str, family: str, *, with_schema: str | None = None) -> dict:
    out = {"record_id": record_id, "record_digest": _sha256_hex(digest), "record_family": family}
    if with_schema is not None:
        out["schema_id"] = with_schema
        out["schema_version"] = "1.0"
    return out


def _request_ref(record_id: str = "cutreq-00000001", digest: str = "a") -> dict:
    return _ref(record_id, digest, "cutover_request", with_schema=CUTOVER_REQUEST_SCHEMA_ID)


def _attempt_ref_bare(record_id: str = "pubattem-0000001", digest: str = "0") -> dict:
    return _ref(record_id, digest, "publication_attempt")


def _authority_state_ref_bare(record_id: str = "authstat-0000001", digest: str = "2") -> dict:
    return _ref(record_id, digest, "authority_state")


def _generation_ref(gen_id: str = "generatn-0000001", digest: str = "6") -> dict:
    return {"generation_id": gen_id, "generation_digest": _sha256_hex(digest)}


def _valid_concurrency_conflict_wire(**overrides) -> dict:
    record = {
        "schema_id": CONCURRENCY_CONFLICT_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "concurrency_conflict",
        "record_id": "concflct-0000001",
        "record_digest": _sha256_hex("0"),
        "created_at": "2026-07-18T12:00:00Z",
        "migration_epoch": "epoch-001",
        "actors": ["operator@example.com", _attempt_ref_bare()],
        "requests": [_request_ref()],
        "type": "dual_writer",
        "winner": None,
        "recovery_requirement": "operator_review_required",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


def _valid_recovery_journal_entry_wire(**overrides) -> dict:
    record = {
        "schema_id": RECOVERY_JOURNAL_ENTRY_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "recovery_journal_entry",
        "record_id": "recjrnl-00000001",
        "record_digest": _sha256_hex("4"),
        "created_at": "2026-07-18T12:00:00Z",
        "migration_epoch": "epoch-001",
        "transition_id": "trans-0000001",
        "sequence": 0,
        "prior_entry_digest": None,
        "operation_reference": _request_ref(),
        "prior_state_reference": _authority_state_ref_bare("authstat-0000002", "3"),
        "new_state_reference": _authority_state_ref_bare("authstat-0000003", "5"),
        "authority_state_reference": _authority_state_ref_bare("authstat-0000004", "7"),
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
# 1. Inventory
# ---------------------------------------------------------------------------


def test_136aj_exactly_eleven_record_family_models_exist_in_package():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names |= {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for expected in (
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
    ):
        assert expected in class_names
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136aj_no_later_group_model_class_exists_in_recovery_concurrency_module():
    tree = ast.parse(RECOVERY_CONCURRENCY_MODULE.read_text())
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert class_names & {"ConcurrencyConflict", "RecoveryJournalEntry"} == {
        "ConcurrencyConflict",
        "RecoveryJournalEntry",
    }
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136aj_expected_public_exports_present():
    for name in (
        "ConcurrencyConflict",
        "RecoveryJournalEntry",
        "ConflictType",
        "ExternalEffectState",
        "RetryReplayClassification",
        "JournalState",
        "OperatorReview",
        "RecoveryAction",
    ):
        assert hasattr(auth, name)
        assert name in auth.__all__


def test_136aj_public_exports_exact():
    assert set(rc.__all__) == {
        "ConflictType",
        "ExternalEffectState",
        "RetryReplayClassification",
        "JournalState",
        "OperatorReview",
        "RecoveryAction",
        "ConcurrencyConflict",
        "RecoveryJournalEntry",
    }


def test_136aj_wildcard_import_matches_all():
    namespace: dict = {}
    exec("from pcae.cltr.authority.recovery_concurrency import *", namespace)
    exported = {k for k in namespace if not k.startswith("_")}
    assert exported == set(rc.__all__)


def test_136aj_models_are_frozen_dataclasses():
    for model in (auth.ConcurrencyConflict, auth.RecoveryJournalEntry):
        assert dataclasses.is_dataclass(model)
        assert model.__dataclass_params__.frozen


# ---------------------------------------------------------------------------
# 2. ConcurrencyConflict: construction / round trip
# ---------------------------------------------------------------------------


def test_136aj_concurrency_conflict_minimal_valid_construction(schema_registry):
    wire = _valid_concurrency_conflict_wire()
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.expected_state is auth.ABSENT
    assert model.observed_state is auth.ABSENT
    assert model.winner is None
    assert model.to_dict() == wire


def test_136aj_concurrency_conflict_cas_mismatch_maximal(schema_registry):
    wire = _valid_concurrency_conflict_wire(
        type="cas_mismatch",
        expected_state=_authority_state_ref_bare("authstat-0000005", "8"),
        observed_state=_authority_state_ref_bare("authstat-0000006", "9"),
        winner=_request_ref(),
        _extensions={"note": "annotation"},
    )
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.expected_state.record_id.value == "authstat-0000005"
    assert model.observed_state.record_id.value == "authstat-0000006"
    assert model.winner is not None
    assert model.to_dict() == wire


def test_136aj_concurrency_conflict_expected_and_observed_may_be_equal(schema_registry):
    same = _authority_state_ref_bare("authstat-0000007", "1")
    wire = _valid_concurrency_conflict_wire(
        type="cas_mismatch", expected_state=same, observed_state=same
    )
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.expected_state == model.observed_state


def test_136aj_concurrency_conflict_cas_mismatch_without_expected_state_rejected():
    wire = _valid_concurrency_conflict_wire(
        type="cas_mismatch", observed_state=_authority_state_ref_bare()
    )
    with pytest.raises(Exception):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_cas_mismatch_without_observed_state_rejected():
    wire = _valid_concurrency_conflict_wire(
        type="cas_mismatch", expected_state=_authority_state_ref_bare()
    )
    with pytest.raises(Exception):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_non_cas_mismatch_with_expected_state_rejected():
    wire = _valid_concurrency_conflict_wire(expected_state=_authority_state_ref_bare())
    with pytest.raises(Exception):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_non_cas_mismatch_with_observed_state_rejected():
    wire = _valid_concurrency_conflict_wire(observed_state=_authority_state_ref_bare())
    with pytest.raises(Exception):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_actors_minimum_two_enforced():
    wire = _valid_concurrency_conflict_wire(actors=["operator@example.com"])
    with pytest.raises(Exception):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_actors_all_principal_identifiers(schema_registry):
    wire = _valid_concurrency_conflict_wire(actors=["a@example.com", "b@example.com"])
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert all(isinstance(a, auth.PrincipalIdentifier) for a in model.actors)
    assert model.to_dict() == wire


def test_136aj_concurrency_conflict_actors_all_record_references(schema_registry):
    wire = _valid_concurrency_conflict_wire(
        actors=[_attempt_ref_bare("pubattem-0000002", "1"), _attempt_ref_bare("pubattem-0000003", "2")]
    )
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert all(isinstance(a, auth.RecordReference) for a in model.actors)
    assert model.to_dict() == wire


def test_136aj_concurrency_conflict_requests_minimum_one_enforced():
    wire = _valid_concurrency_conflict_wire(requests=[])
    with pytest.raises(Exception):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_requests_multiple(schema_registry):
    wire = _valid_concurrency_conflict_wire(
        requests=[_request_ref("cutreq-00000001", "a"), _request_ref("cutreq-00000002", "b")]
    )
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert len(model.requests) == 2


def test_136aj_concurrency_conflict_requests_wrong_family_rejected():
    wire = _valid_concurrency_conflict_wire(
        requests=[_ref("pubattem-0000001", "0", "publication_attempt", with_schema=PUBLICATION_ATTEMPT_SCHEMA_ID)]
    )
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_requests_require_schema_id_and_version():
    ref = _request_ref()
    del ref["schema_id"]
    wire = _valid_concurrency_conflict_wire(requests=[ref])
    with pytest.raises(auth.TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_winner_reference_no_family_restriction(schema_registry):
    wire = _valid_concurrency_conflict_wire(winner=_attempt_ref_bare())
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    assert model.winner.record_family is auth.RecordFamily.PUBLICATION_ATTEMPT


def test_136aj_concurrency_conflict_winner_null_serializes_as_null(schema_registry):
    wire = _valid_concurrency_conflict_wire(winner=None)
    _assert_schema_valid(wire, CONCURRENCY_CONFLICT_SCHEMA_ID, schema_registry)
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    out = model.to_dict()
    assert "winner" in out
    assert out["winner"] is None


def test_136aj_concurrency_conflict_unknown_field_rejected():
    wire = _valid_concurrency_conflict_wire(scope="global")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_extensions_string_only():
    wire = _valid_concurrency_conflict_wire(_extensions={"note": 5})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_extensions_null_rejected():
    wire = _valid_concurrency_conflict_wire(_extensions=None)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_extensions_reserved_key_collision_rejected():
    wire = _valid_concurrency_conflict_wire(_extensions={"type": "collides"})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_unsupported_schema_version_rejected():
    wire = _valid_concurrency_conflict_wire()
    with pytest.raises(auth.UnsupportedSchemaVersionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="2.0")


def test_136aj_concurrency_conflict_wrong_schema_id_rejected():
    wire = _valid_concurrency_conflict_wire(schema_id="https://pcae.local/wrong.json")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_wrong_record_type_rejected():
    wire = _valid_concurrency_conflict_wire(record_type="recovery_journal_entry")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_missing_required_field_rejected():
    wire = _valid_concurrency_conflict_wire()
    del wire["recovery_requirement"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_forbids_authoritative_role():
    wire = _valid_concurrency_conflict_wire(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "x",
        }
    )
    with pytest.raises(Exception):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_type_enum_members_match_schema():
    assert {m.value for m in rc.ConflictType} == {
        "cas_mismatch",
        "dual_writer",
        "stale_expectation",
        "unknown_winner",
    }


def test_136aj_concurrency_conflict_type_enum_strictness():
    wire = _valid_concurrency_conflict_wire(type="DUAL_WRITER")
    with pytest.raises(ValueError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("bad_value", ["", " ", "unknown_value", "cas-mismatch"])
def test_136aj_concurrency_conflict_type_unknown_string_rejected(bad_value):
    wire = _valid_concurrency_conflict_wire(type=bad_value)
    with pytest.raises(ValueError):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


def test_136aj_concurrency_conflict_recovery_requirement_enum_members_match_shared():
    assert {m.value for m in auth.RecoveryState} == {
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
    }


def test_136aj_concurrency_conflict_top_level_assignment_raises():
    wire = _valid_concurrency_conflict_wire()
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.type = rc.ConflictType.DUAL_WRITER


@pytest.mark.parametrize(
    "actor_value",
    [1, 1.5, True, None, ["nested"], {"record_id": "bad"}],
)
def test_136aj_concurrency_conflict_actor_invalid_shapes_rejected(actor_value):
    wire = _valid_concurrency_conflict_wire(actors=["operator@example.com", actor_value])
    with pytest.raises(Exception):
        auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 3. RecoveryJournalEntry: construction / round trip
# ---------------------------------------------------------------------------


def test_136aj_recovery_journal_entry_minimal_valid_construction(schema_registry):
    wire = _valid_recovery_journal_entry_wire()
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.publication_attempt_reference is auth.ABSENT
    assert model.operator_review is auth.ABSENT
    assert model.recovery_action is auth.ABSENT
    assert model.prior_entry_digest is None
    assert model.to_dict() == wire


def test_136aj_recovery_journal_entry_maximal_valid_construction_actioned(schema_registry):
    wire = _valid_recovery_journal_entry_wire(
        sequence=1,
        prior_entry_digest=_sha256_hex("7"),
        publication_attempt_reference=_ref(
            "pubattem-0000001", "0", "publication_attempt", with_schema=PUBLICATION_ATTEMPT_SCHEMA_ID
        ),
        state="actioned",
        operator_review={"notes": "reviewed by operator"},
        recovery_action={"description": "retry publication manually"},
        _extensions={"note": "annotation"},
    )
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.prior_entry_digest.value == _sha256_hex("7")
    assert model.operator_review.notes == "reviewed by operator"
    assert model.recovery_action.description == "retry publication manually"
    assert model.to_dict() == wire


def test_136aj_recovery_journal_entry_self_reference_permitted(schema_registry):
    # The schema shape-checks prior_entry_digest only; it never verifies
    # the referenced digest actually names a distinct, existing entry.
    own_digest = _sha256_hex("0")
    wire = _valid_recovery_journal_entry_wire(
        sequence=1, prior_entry_digest=own_digest, record_digest=own_digest
    )
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.prior_entry_digest.value == model.envelope.record_digest.value


def test_136aj_recovery_journal_entry_genesis_requires_null_prior_digest():
    wire = _valid_recovery_journal_entry_wire(sequence=0, prior_entry_digest=_sha256_hex("1"))
    with pytest.raises(auth.TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_nonzero_sequence_requires_digest():
    wire = _valid_recovery_journal_entry_wire(sequence=1, prior_entry_digest=None)
    with pytest.raises(auth.TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_negative_sequence_rejected():
    wire = _valid_recovery_journal_entry_wire(sequence=-1)
    with pytest.raises(auth.TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_boolean_sequence_rejected():
    wire = _valid_recovery_journal_entry_wire(sequence=True)
    with pytest.raises(auth.TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_duplicate_sequence_across_documents_both_constructible(
    schema_registry,
):
    wire_a = _valid_recovery_journal_entry_wire(sequence=0, record_id="recjrnl-00000005")
    wire_b = _valid_recovery_journal_entry_wire(sequence=0, record_id="recjrnl-00000006")
    _assert_schema_valid(wire_a, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    _assert_schema_valid(wire_b, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model_a = auth.RecoveryJournalEntry.from_dict(wire_a, schema_version="1.0")
    model_b = auth.RecoveryJournalEntry.from_dict(wire_b, schema_version="1.0")
    assert model_a.sequence == model_b.sequence == 0


@pytest.mark.parametrize("state", ["reviewed", "actioned", "superseded"])
def test_136aj_recovery_journal_entry_states_require_operator_review(state):
    wire = _valid_recovery_journal_entry_wire(state=state)
    with pytest.raises(auth.TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_recorded_forbids_operator_review():
    wire = _valid_recovery_journal_entry_wire(operator_review={"notes": "x"})
    with pytest.raises(auth.TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("state", ["reviewed", "superseded"])
def test_136aj_recovery_journal_entry_reviewed_or_superseded_forbid_recovery_action(
    schema_registry, state
):
    wire = _valid_recovery_journal_entry_wire(state=state, operator_review={"notes": "x"})
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.recovery_action is auth.ABSENT


def test_136aj_recovery_journal_entry_actioned_without_recovery_action_rejected():
    wire = _valid_recovery_journal_entry_wire(state="actioned", operator_review={"notes": "x"})
    with pytest.raises(auth.TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_non_actioned_with_recovery_action_rejected():
    wire = _valid_recovery_journal_entry_wire(
        state="reviewed", operator_review={"notes": "x"}, recovery_action={"description": "y"}
    )
    with pytest.raises(auth.TypedModelInternalInvariantError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_operator_review_unknown_field_rejected():
    wire = _valid_recovery_journal_entry_wire(
        state="reviewed", operator_review={"notes": "x", "extra": "y"}
    )
    with pytest.raises(auth.TypedModelConstructionError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_recovery_action_unknown_field_rejected():
    wire = _valid_recovery_journal_entry_wire(
        state="actioned",
        operator_review={"notes": "x"},
        recovery_action={"description": "y", "extra": "z"},
    )
    with pytest.raises(auth.TypedModelConstructionError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_operator_review_empty_notes_rejected():
    wire = _valid_recovery_journal_entry_wire(state="reviewed", operator_review={"notes": ""})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_publication_attempt_reference_wrong_family_rejected():
    wire = _valid_recovery_journal_entry_wire(
        publication_attempt_reference=_request_ref()
    )
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_authority_state_reference_wrong_family_rejected():
    wire = _valid_recovery_journal_entry_wire(authority_state_reference=_request_ref())
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_operation_reference_no_family_restriction(schema_registry):
    wire = _valid_recovery_journal_entry_wire(operation_reference=_attempt_ref_bare())
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.operation_reference.record_family is auth.RecordFamily.PUBLICATION_ATTEMPT


def test_136aj_recovery_journal_entry_prior_and_new_state_reference_may_reference_same_record(
    schema_registry,
):
    same = _authority_state_ref_bare("authstat-0000009", "9")
    wire = _valid_recovery_journal_entry_wire(prior_state_reference=same, new_state_reference=same)
    _assert_schema_valid(wire, RECOVERY_JOURNAL_ENTRY_SCHEMA_ID, schema_registry)
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert model.prior_state_reference == model.new_state_reference


def test_136aj_recovery_journal_entry_unknown_field_rejected():
    wire = _valid_recovery_journal_entry_wire(scope="global")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_extensions_string_only():
    wire = _valid_recovery_journal_entry_wire(_extensions={"note": 5})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_unsupported_schema_version_rejected():
    wire = _valid_recovery_journal_entry_wire()
    with pytest.raises(auth.UnsupportedSchemaVersionError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="2.0")


def test_136aj_recovery_journal_entry_wrong_schema_id_rejected():
    wire = _valid_recovery_journal_entry_wire(schema_id="https://pcae.local/wrong.json")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_wrong_record_type_rejected():
    wire = _valid_recovery_journal_entry_wire(record_type="concurrency_conflict")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_missing_required_field_rejected():
    wire = _valid_recovery_journal_entry_wire()
    del wire["generation_reference"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_forbids_authoritative_role():
    wire = _valid_recovery_journal_entry_wire(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "x",
        }
    )
    with pytest.raises(Exception):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_external_effect_state_enum_members_match_schema():
    assert {m.value for m in rc.ExternalEffectState} == {"none", "pending", "applied", "unknown"}


def test_136aj_recovery_journal_entry_retry_replay_classification_enum_members_match_schema():
    assert {m.value for m in rc.RetryReplayClassification} == {"original", "retry", "replay"}


def test_136aj_recovery_journal_entry_journal_state_enum_members_match_schema():
    assert {m.value for m in rc.JournalState} == {"recorded", "reviewed", "actioned", "superseded"}


def test_136aj_recovery_journal_entry_state_enum_strictness():
    wire = _valid_recovery_journal_entry_wire(state="RECORDED")
    with pytest.raises(ValueError):
        auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")


def test_136aj_recovery_journal_entry_top_level_assignment_raises():
    wire = _valid_recovery_journal_entry_wire()
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.sequence = 99


def test_136aj_recovery_journal_entry_generation_reference_returned_type_is_shared_class():
    wire = _valid_recovery_journal_entry_wire()
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    assert isinstance(model.generation_reference, auth.GenerationReference)


# ---------------------------------------------------------------------------
# 4. Schema field-set parity
# ---------------------------------------------------------------------------


def test_136aj_concurrency_conflict_schema_field_set_matches_model_known_keys():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "concurrency_conflict.schema.json").read_text())
    assert set(schema["properties"].keys()) == rc._CONCURRENCY_CONFLICT_KNOWN_KEYS


def test_136aj_recovery_journal_entry_schema_field_set_matches_model_known_keys():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "recovery_journal_entry.schema.json").read_text())
    assert set(schema["properties"].keys()) == rc._RECOVERY_JOURNAL_ENTRY_KNOWN_KEYS


def test_136aj_concurrency_conflict_required_set_matches_schema():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "concurrency_conflict.schema.json").read_text())
    wire = _valid_concurrency_conflict_wire()
    assert set(schema["required"]) <= set(wire.keys())


def test_136aj_recovery_journal_entry_required_set_matches_schema():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "recovery_journal_entry.schema.json").read_text())
    wire = _valid_recovery_journal_entry_wire()
    assert set(schema["required"]) <= set(wire.keys())


# ---------------------------------------------------------------------------
# 5. Equality / immutability
# ---------------------------------------------------------------------------


def test_136aj_concurrency_conflict_structural_equality():
    wire = _valid_concurrency_conflict_wire()
    a = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    b = auth.ConcurrencyConflict.from_dict(copy.deepcopy(wire), schema_version="1.0")
    assert a == b


def test_136aj_concurrency_conflict_field_difference_breaks_equality():
    a = auth.ConcurrencyConflict.from_dict(_valid_concurrency_conflict_wire(), schema_version="1.0")
    b = auth.ConcurrencyConflict.from_dict(
        _valid_concurrency_conflict_wire(type="stale_expectation"), schema_version="1.0"
    )
    assert a != b


def test_136aj_concurrency_conflict_actors_order_observable():
    a = auth.ConcurrencyConflict.from_dict(
        _valid_concurrency_conflict_wire(actors=["a@example.com", "b@example.com"]),
        schema_version="1.0",
    )
    b = auth.ConcurrencyConflict.from_dict(
        _valid_concurrency_conflict_wire(actors=["b@example.com", "a@example.com"]),
        schema_version="1.0",
    )
    assert a != b


def test_136aj_recovery_journal_entry_structural_equality():
    wire = _valid_recovery_journal_entry_wire()
    a = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    b = auth.RecoveryJournalEntry.from_dict(copy.deepcopy(wire), schema_version="1.0")
    assert a == b


def test_136aj_recovery_journal_entry_sequence_difference_breaks_equality(schema_registry):
    wire_a = _valid_recovery_journal_entry_wire(sequence=0, record_id="recjrnl-00000010")
    wire_b = _valid_recovery_journal_entry_wire(
        sequence=1, prior_entry_digest=_sha256_hex("1"), record_id="recjrnl-00000011"
    )
    a = auth.RecoveryJournalEntry.from_dict(wire_a, schema_version="1.0")
    b = auth.RecoveryJournalEntry.from_dict(wire_b, schema_version="1.0")
    assert a != b


def test_136aj_concurrency_conflict_and_journal_entry_not_equal_across_types():
    conflict = auth.ConcurrencyConflict.from_dict(_valid_concurrency_conflict_wire(), schema_version="1.0")
    entry = auth.RecoveryJournalEntry.from_dict(
        _valid_recovery_journal_entry_wire(), schema_version="1.0"
    )
    assert conflict != entry


def test_136aj_concurrency_conflict_hashable():
    model = auth.ConcurrencyConflict.from_dict(_valid_concurrency_conflict_wire(), schema_version="1.0")
    hash(model)


def test_136aj_recovery_journal_entry_hashable():
    model = auth.RecoveryJournalEntry.from_dict(
        _valid_recovery_journal_entry_wire(), schema_version="1.0"
    )
    hash(model)


def test_136aj_concurrency_conflict_extensions_present_not_hashable():
    model = auth.ConcurrencyConflict.from_dict(
        _valid_concurrency_conflict_wire(_extensions={"note": "x"}), schema_version="1.0"
    )
    with pytest.raises(TypeError):
        hash(model)


def test_136aj_concurrency_conflict_mutation_of_source_dict_after_construction_does_not_affect_model():
    wire = _valid_concurrency_conflict_wire(_extensions={"note": "x"})
    original_actors = list(wire["actors"])
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    wire["actors"].append("mutated@example.com")
    wire["_extensions"]["note"] = "mutated"
    assert list(model.to_dict()["actors"]) == original_actors
    assert model.to_dict()["_extensions"]["note"] == "x"


# ---------------------------------------------------------------------------
# 6. No-conflict-detection / no-CAS-execution / no-recovery-execution /
#    no-journal-persistence / no-later-model
# ---------------------------------------------------------------------------


def test_136aj_no_forbidden_symbols_defined_in_source():
    tree = ast.parse(RECOVERY_CONCURRENCY_MODULE.read_text())
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_SYMBOLS:
        assert forbidden not in defined_names


def test_136aj_no_repository_or_persistence_symbols_in_source():
    source = RECOVERY_CONCURRENCY_MODULE.read_text()
    for forbidden in ("Repository", "save(", "persist(", "def load(", "requests.", "urllib", "append("):
        assert forbidden not in source


def test_136aj_no_production_module_imports_authority_package():
    for root_dir in PRODUCTION_SCAN_ROOTS:
        if not root_dir.exists():
            continue
        for path in root_dir.rglob("*.py"):
            if AUTHORITY_PACKAGE_DIR in path.parents or path.parent == AUTHORITY_PACKAGE_DIR:
                continue
            source = path.read_text()
            assert "from pcae.cltr.authority" not in source, path
            assert "import pcae.cltr.authority" not in source, path


def test_136aj_recovery_concurrency_module_imports_no_production_lifecycle_module():
    source = RECOVERY_CONCURRENCY_MODULE.read_text()
    for forbidden_import in (
        "pcae.core.finalization",
        "pcae.core.notification",
        "pcae.commands",
        "pcae.runtime",
    ):
        assert forbidden_import not in source


def test_136aj_recovery_concurrency_module_does_not_import_production_lifecycle_modules_ast():
    forbidden_modules = (
        "pcae.cltr.lifecycle",
        "pcae.cltr.finalization",
        "pcae.cltr.notification",
        "pcae.cltr.marker",
        "pcae.cltr.receipt",
        "pcae.commands",
        "pcae.core",
        "pcae.runtime",
    )
    tree = ast.parse(RECOVERY_CONCURRENCY_MODULE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in forbidden_modules:
                    assert not alias.name.startswith(forbidden), (RECOVERY_CONCURRENCY_MODULE, alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for forbidden in forbidden_modules:
                assert not node.module.startswith(forbidden), (RECOVERY_CONCURRENCY_MODULE, node.module)


def test_136aj_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    wire = _valid_recovery_journal_entry_wire()
    model = auth.RecoveryJournalEntry.from_dict(wire, schema_version="1.0")
    model.to_dict()


def test_136aj_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    wire = _valid_concurrency_conflict_wire()
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    model.to_dict()
    wire2 = _valid_recovery_journal_entry_wire()
    model2 = auth.RecoveryJournalEntry.from_dict(wire2, schema_version="1.0")
    model2.to_dict()


def test_136aj_no_filesystem_write_during_construction_or_serialization(monkeypatch, tmp_path):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError(f"unexpected filesystem write attempted: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    wire = _valid_concurrency_conflict_wire()
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136aj_package_import_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    import importlib

    importlib.reload(rc)


def test_136aj_no_current_state_comparison_instrumentation(monkeypatch):
    """Instrument equality/hash on the embedded reference types used for
    expected_state/observed_state; construction and serialization must
    never invoke a comparison between the two beyond the plain dataclass
    ``__eq__`` a caller might separately choose to invoke."""

    calls: list = []
    original_eq = auth.RecordReference.__eq__

    def _tracking_eq(self, other):
        calls.append((self, other))
        return original_eq(self, other)

    monkeypatch.setattr(auth.RecordReference, "__eq__", _tracking_eq)
    wire = _valid_concurrency_conflict_wire(
        type="cas_mismatch",
        expected_state=_authority_state_ref_bare("authstat-0000005", "8"),
        observed_state=_authority_state_ref_bare("authstat-0000006", "9"),
    )
    calls.clear()
    model = auth.ConcurrencyConflict.from_dict(wire, schema_version="1.0")
    model.to_dict()
    assert calls == []


# ---------------------------------------------------------------------------
# 7. Scope-guard verification (narrowed by 136AJ; must still forbid the
#    remaining five later record families and permit only this group's two
#    new families).
# ---------------------------------------------------------------------------


SCOPE_GUARDED_TEST_FILES = (
    REPO_ROOT / "tests" / "test_cltr_authority_136z_shared_core.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136aa_shared_core_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ab_authority_core.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ac_authority_core_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ad_request_readiness.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ae_request_readiness_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136af_authorization_candidate.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ag_authorization_candidate_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ah_publication.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ai_publication_independent.py",
)


def test_136aj_adjacent_scope_guard_test_files_still_forbid_all_later_models():
    still_forbidden_after_136aj = (
        "NotificationAuthorityBinding",
        "MarkerAuthorityBinding",
        "FinalizationReceiptAuthorityBinding",
        "CompatibilityState",
        "QuarantineRecord",
    )
    for path in SCOPE_GUARDED_TEST_FILES:
        if not path.exists():
            continue
        text = path.read_text()
        if "LATER_MODEL_CLASS_NAMES" not in text and "LATER_GROUP_MODEL_NAMES" not in text and "_LATER_GROUP_MODEL_NAMES" not in text:
            continue
        for later in still_forbidden_after_136aj:
            assert later in text, f"{path} no longer names {later} as forbidden"


def test_136aj_own_module_scope_guard_matches_exactly_the_two_new_families():
    tree = ast.parse(RECOVERY_CONCURRENCY_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_models = class_names & {
        "ConcurrencyConflict", "RecoveryJournalEntry", *LATER_GROUP_MODEL_NAMES,
        "AuthorityEpoch", "AuthorityState", "CutoverRequest", "ReadinessPackage",
        "HumanAuthorization", "CutoverCandidate", "Certification",
        "PublicationAttempt", "PublicationEvidence",
    }
    assert record_family_models == {"ConcurrencyConflict", "RecoveryJournalEntry"}


# ---------------------------------------------------------------------------
# 8. Packaging verification
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_136aj_wheel_contains_recovery_concurrency_module_no_later_family(tmp_path: Path):
    import subprocess as _subprocess

    dist_dir = tmp_path / "dist"
    _subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"

    import zipfile

    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()

    assert "pcae/cltr/authority/recovery_concurrency.py" in names
    for forbidden in ("bindings", "compatibility_quarantine"):
        assert f"pcae/cltr/authority/{forbidden}.py" not in names


@pytest.mark.slow
def test_136aj_sdist_includes_recovery_concurrency_module(tmp_path: Path):
    import subprocess as _subprocess

    dist_dir = tmp_path / "dist"
    _subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert len(sdists) == 1, f"expected exactly one sdist, found {sdists}"

    import tarfile

    with tarfile.open(sdists[0]) as archive:
        names = archive.getnames()

    assert any(name.endswith("pcae/cltr/authority/recovery_concurrency.py") for name in names)


@pytest.mark.slow
def test_136aj_isolated_wheel_installation_constructs_both_new_models(tmp_path: Path):
    import subprocess as _subprocess
    import venv

    dist_dir = tmp_path / "dist"
    _subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "isolated_venv"
    venv.create(venv_dir, with_pip=True)
    venv_python = venv_dir / "bin" / "python"

    _subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--quiet", str(wheels[0])],
        check=True, capture_output=True, text=True,
    )

    script = tmp_path / "verify.py"
    script.write_text(
        "from pcae.cltr import authority as auth\n"
        "for name in ('AuthorityEpoch', 'AuthorityState', 'CutoverRequest', "
        "'ReadinessPackage', 'HumanAuthorization', 'CutoverCandidate', "
        "'Certification', 'PublicationAttempt', 'PublicationEvidence', "
        "'ConcurrencyConflict', 'RecoveryJournalEntry'):\n"
        "    assert hasattr(auth, name), name\n"
        "for name in ('NotificationAuthorityBinding', 'MarkerAuthorityBinding', "
        "'FinalizationReceiptAuthorityBinding', 'CompatibilityState', "
        "'QuarantineRecord'):\n"
        "    assert not hasattr(auth, name), name\n"
        "disclosure = {'authority_role': 'derivative', 'is_authoritative': False, "
        "'disclosure_text': 'x'}\n"
        "def sha(fill):\n"
        "    return fill * 64\n"
        "def ref(rid, digest, family, with_schema=None):\n"
        "    out = {'record_id': rid, 'record_digest': sha(digest), "
        "'record_family': family}\n"
        "    if with_schema:\n"
        "        out['schema_id'] = with_schema\n"
        "        out['schema_version'] = '1.0'\n"
        "    return out\n"
        "cc_wire = {\n"
        "    'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/"
        "concurrency_conflict.schema.json',\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'concurrency_conflict', "
        "'record_id': 'concflct-0000001', 'record_digest': sha('0'),\n"
        "    'created_at': '2026-07-18T12:00:00Z', 'migration_epoch': 'epoch-001',\n"
        "    'actors': ['a@example.com', 'b@example.com'],\n"
        "    'requests': [ref('cutreq-00000001', 'a', 'cutover_request', "
        "with_schema='https://pcae.local/schemas/cltr_cutover/records/"
        "cutover_request.schema.json')],\n"
        "    'type': 'dual_writer', 'winner': None, "
        "'recovery_requirement': 'operator_review_required',\n"
        "    'limitations': [], 'authority_disclosure': disclosure,\n"
        "}\n"
        "cc = auth.ConcurrencyConflict.from_dict(cc_wire, schema_version='1.0')\n"
        "assert cc.to_dict() == cc_wire\n"
        "rje_wire = {\n"
        "    'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/"
        "recovery_journal_entry.schema.json',\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'recovery_journal_entry', "
        "'record_id': 'recjrnl-00000001', 'record_digest': sha('4'),\n"
        "    'created_at': '2026-07-18T12:00:00Z', 'migration_epoch': 'epoch-001',\n"
        "    'transition_id': 'trans-0000001', 'sequence': 0, "
        "'prior_entry_digest': None,\n"
        "    'operation_reference': ref('cutreq-00000001', 'a', 'cutover_request'),\n"
        "    'prior_state_reference': ref('authstat-0000001', '2', "
        "'authority_state'),\n"
        "    'new_state_reference': ref('authstat-0000002', '3', "
        "'authority_state'),\n"
        "    'authority_state_reference': ref('authstat-0000003', '5', "
        "'authority_state'),\n"
        "    'generation_reference': {'generation_id': 'generatn-0000001', "
        "'generation_digest': sha('6')},\n"
        "    'external_effect_state': 'none', "
        "'retry_replay_classification': 'original', 'state': 'recorded',\n"
        "    'limitations': [], 'authority_disclosure': disclosure,\n"
        "}\n"
        "rje = auth.RecoveryJournalEntry.from_dict(rje_wire, schema_version='1.0')\n"
        "assert rje.to_dict() == rje_wire\n"
        "print('isolated wheel verification OK')\n"
    )
    result = _subprocess.run(
        [str(venv_python), str(script)],
        check=True, capture_output=True, text=True, cwd=str(tmp_path),
    )
    assert "isolated wheel verification OK" in result.stdout
