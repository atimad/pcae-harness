"""Production tests for the Authority Evaluation Service integration
(Phase 147M, AESIC-001 v1.3).

Covers: Stage1EvaluationResult/AER/CanonicalPointer construction,
serialization, and digest handling; Decision Template Resolution and its
failure taxonomy; the two-tier AER store (immutable primary + canonical
pointer); Stage 1/Stage 2 evaluation, idempotency, supersession, and
Stage 1 handoff validation; canonical pointer corruption/update-failure
detection; recovery (AER committed, pointer not yet advanced); and the
Interactive Workflow / Readiness / CHGR integration touchpoints.
"""

from __future__ import annotations

import json

import pytest

from pcae.authority_evaluation.models import (
    AuthorityEvaluationOutcome,
    EligibleAuthorityDeclaration,
    EvaluationResult,
)
from pcae.aesic.errors import (
    AuthorityEvaluationRecordConflictError,
    CanonicalPointerCorruptError,
    CanonicalPointerUpdateFailedError,
    DecisionTemplateCitationEmptyError,
    DecisionTemplateNotFoundError,
    Stage1HandoffInvalidError,
    Stage1HandoffInvalidReason,
)
from pcae.aesic.records import (
    AuthorityEvaluationRecord,
    CanonicalPointer,
    Stage1EvaluationResult,
    aer_from_payload,
    aer_to_payload,
    pointer_from_payload,
    pointer_to_payload,
    stage_1_evidence_equivalent,
    stage_1_result_from_payload,
    stage_1_result_to_payload,
    verify_aer_digest,
    verify_pointer_digest,
)
from pcae.aesic.registry_filesystem import FilesystemAuthorityRegistry
from pcae.aesic.resolution import DecisionTemplateResolution
from pcae.aesic.service import AuthorityEvaluationService
from pcae.aesic.storage import AuthorityEvaluationRecordStore
from pcae.aesic.template_store import read_template, write_template
from pcae.governance.publication.record import build_publication_record, compute_record_digest
from pcae.governance.publication.models import PublicationAuthorizationEvent
from pcae.interactive_workflow.models.session import Session, SessionState
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.identity import generate_session_id

_TS = "2026-01-01T00:00:00Z"


def _outcome(
    *,
    template_ref="tpl-1",
    template_version="v1",
    claimed_identity="alice",
    result=EvaluationResult.ELIGIBLE,
    citation_text="Only Finance may approve.",
    declaration_ref="tpl-1::v1",
) -> AuthorityEvaluationOutcome:
    if result is not EvaluationResult.ELIGIBLE:
        citation_text = None
    return AuthorityEvaluationOutcome(
        template_ref=template_ref,
        template_version=template_version,
        claimed_identity=claimed_identity,
        evaluation_result=result,
        declaration_ref=declaration_ref,
        citation_text=citation_text,
        evaluated_at=_TS,
        evaluator_version="aem-evaluator/1.0",
    )


def _session(session_id=generate_session_id(), owner_identity="alice", template_ref="tpl-1", template_version="v1"):
    return Session(
        session_id=session_id,
        owner_identity=owner_identity,
        template_ref=template_ref,
        subject_ref="subj-1",
        session_state=SessionState.CONFIRMED,
        created_at=_TS,
        updated_at=_TS,
        template_version=template_version,
    )


def _build_service(tmp_path, eligible=("alice",)):
    tpl_root = tmp_path / "templates"
    reg_root = tmp_path / "registry"
    store_root = tmp_path / "records"
    write_template("tpl-1", "v1", "Only Finance may approve.", root=tpl_root)
    registry = FilesystemAuthorityRegistry(root=reg_root)
    registry.write_declaration(
        EligibleAuthorityDeclaration(
            template_ref="tpl-1",
            template_version="v1",
            eligible_identities=frozenset(eligible),
            declared_at=_TS,
            declared_by="governance",
        )
    )
    store = AuthorityEvaluationRecordStore(root=store_root)
    service = AuthorityEvaluationService(registry, store, template_root=tpl_root)
    return service, store, registry


# --- Unit: Stage1EvaluationResult ------------------------------------------


class TestStage1EvaluationResult:
    def test_construction_and_fields(self):
        outcome = _outcome()
        result = Stage1EvaluationResult(outcome=outcome, evaluation_id="aeval-1", session_id="sess-1")
        assert result.outcome is outcome
        assert result.evaluation_id == "aeval-1"
        assert result.session_id == "sess-1"

    def test_rejects_non_outcome(self):
        with pytest.raises(Exception):
            Stage1EvaluationResult(outcome="not-an-outcome", evaluation_id="a", session_id="s")

    def test_rejects_empty_evaluation_id(self):
        with pytest.raises(Exception):
            Stage1EvaluationResult(outcome=_outcome(), evaluation_id="", session_id="s")

    def test_serialization_round_trip(self):
        result = Stage1EvaluationResult(outcome=_outcome(), evaluation_id="aeval-1", session_id="sess-1")
        payload = stage_1_result_to_payload(result)
        restored = stage_1_result_from_payload(payload)
        assert restored == result

    def test_immutable(self):
        result = Stage1EvaluationResult(outcome=_outcome(), evaluation_id="aeval-1", session_id="sess-1")
        with pytest.raises(Exception):
            result.evaluation_id = "other"  # type: ignore[misc]

    def test_equality(self):
        a = Stage1EvaluationResult(outcome=_outcome(), evaluation_id="aeval-1", session_id="sess-1")
        b = Stage1EvaluationResult(outcome=_outcome(), evaluation_id="aeval-1", session_id="sess-1")
        assert a == b


class TestStage1EvidenceEquivalence:
    def test_both_absent_equivalent(self):
        assert stage_1_evidence_equivalent(None, None) is True

    def test_one_absent_not_equivalent(self):
        r = Stage1EvaluationResult(outcome=_outcome(), evaluation_id="aeval-1", session_id="sess-1")
        assert stage_1_evidence_equivalent(None, r) is False
        assert stage_1_evidence_equivalent(r, None) is False

    def test_both_present_equal_content_equivalent_despite_different_evaluation_id(self):
        a = Stage1EvaluationResult(outcome=_outcome(), evaluation_id="aeval-1", session_id="sess-1")
        b = Stage1EvaluationResult(outcome=_outcome(), evaluation_id="aeval-2", session_id="sess-1")
        assert stage_1_evidence_equivalent(a, b) is True

    def test_differing_outcome_not_equivalent(self):
        a = Stage1EvaluationResult(outcome=_outcome(result=EvaluationResult.ELIGIBLE), evaluation_id="aeval-1", session_id="sess-1")
        b = Stage1EvaluationResult(
            outcome=_outcome(result=EvaluationResult.INELIGIBLE, citation_text=None),
            evaluation_id="aeval-2",
            session_id=generate_session_id(),
        )
        assert stage_1_evidence_equivalent(a, b) is False

    def test_evaluated_at_excluded(self):
        outcome_a = _outcome()
        outcome_b = AuthorityEvaluationOutcome(
            template_ref=outcome_a.template_ref,
            template_version=outcome_a.template_version,
            claimed_identity=outcome_a.claimed_identity,
            evaluation_result=outcome_a.evaluation_result,
            declaration_ref=outcome_a.declaration_ref,
            citation_text=outcome_a.citation_text,
            evaluated_at="2026-06-01T00:00:00Z",
            evaluator_version=outcome_a.evaluator_version,
        )
        a = Stage1EvaluationResult(outcome=outcome_a, evaluation_id="aeval-1", session_id="sess-1")
        b = Stage1EvaluationResult(outcome=outcome_b, evaluation_id="aeval-2", session_id="sess-1")
        assert stage_1_evidence_equivalent(a, b) is True


# --- Unit: AuthorityEvaluationRecord ---------------------------------------


class TestAuthorityEvaluationRecord:
    def test_construction_defaults(self):
        record = AuthorityEvaluationRecord(
            record_id="aer-1", package_id="pkg-1", evaluation_id="ev-1", outcome=_outcome(), evaluated_at=_TS
        )
        assert record.record_family == "authority_evaluation_record"
        assert record.stage == "stage_2"
        assert record.stage_1_outcome_ref is None

    def test_rejects_wrong_record_family(self):
        with pytest.raises(Exception):
            AuthorityEvaluationRecord(
                record_id="aer-1",
                package_id="pkg-1",
                evaluation_id="ev-1",
                outcome=_outcome(),
                evaluated_at=_TS,
                record_family="something_else",
            )

    def test_digest_computed_and_verifiable(self):
        record = AuthorityEvaluationRecord(
            record_id="aer-1", package_id="pkg-1", evaluation_id="ev-1", outcome=_outcome(), evaluated_at=_TS
        )
        payload = aer_to_payload(record)
        assert payload["record_digest"]
        assert verify_aer_digest(payload) is True

    def test_tampered_payload_fails_digest_verification(self):
        record = AuthorityEvaluationRecord(
            record_id="aer-1", package_id="pkg-1", evaluation_id="ev-1", outcome=_outcome(), evaluated_at=_TS
        )
        payload = aer_to_payload(record)
        payload["outcome"]["citation_text"] = "Tampered."
        assert verify_aer_digest(payload) is False

    def test_round_trip_with_stage_1_ref(self):
        stage1 = Stage1EvaluationResult(outcome=_outcome(), evaluation_id="aeval-1", session_id="sess-1")
        record = AuthorityEvaluationRecord(
            record_id="aer-1",
            package_id="pkg-1",
            evaluation_id="ev-1",
            outcome=_outcome(),
            evaluated_at=_TS,
            stage_1_outcome_ref=stage1,
        )
        payload = aer_to_payload(record)
        restored = aer_from_payload(payload)
        assert restored.stage_1_outcome_ref == stage1
        assert restored.record_id == record.record_id


class TestCanonicalPointer:
    def test_digest_covers_all_four_fields(self):
        pointer = CanonicalPointer(package_id="pkg-1", evaluation_id="ev-1", record_id="aer-1", record_digest="d" * 64)
        payload = pointer_to_payload(pointer)
        assert payload["pointer_digest"]
        assert verify_pointer_digest(payload) is True

        tampered = dict(payload)
        tampered["record_id"] = "aer-substituted"
        assert verify_pointer_digest(tampered) is False

    def test_round_trip(self):
        pointer = CanonicalPointer(package_id="pkg-1", evaluation_id="ev-1", record_id="aer-1", record_digest="d" * 64)
        payload = pointer_to_payload(pointer)
        restored = pointer_from_payload(payload)
        assert restored.package_id == pointer.package_id
        assert restored.pointer_digest == payload["pointer_digest"]


# --- Unit: Decision Template Resolution ------------------------------------


class TestDecisionTemplateResolution:
    def test_not_found(self, tmp_path):
        with pytest.raises(DecisionTemplateNotFoundError):
            read_template("missing", "v1", root=tmp_path)

    def test_empty_citation(self, tmp_path):
        write_template("tpl-x", "v1", "   ", root=tmp_path)
        with pytest.raises(DecisionTemplateCitationEmptyError):
            read_template("tpl-x", "v1", root=tmp_path)

    def test_resolves_citation_text_and_declaration(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        resolution = DecisionTemplateResolution(service._registry, tmp_path / "templates")
        result = resolution.resolve("tpl-1", "v1")
        assert result.citation_text == "Only Finance may approve."
        assert result.declaration is not None

    def test_version_is_part_of_key(self, tmp_path):
        write_template("tpl-1", "v1", "Text v1.", root=tmp_path)
        write_template("tpl-1", "v2", "Text v2.", root=tmp_path)
        assert read_template("tpl-1", "v1", root=tmp_path).eligible_authority == "Text v1."
        assert read_template("tpl-1", "v2", root=tmp_path).eligible_authority == "Text v2."


# --- Persistence: AuthorityEvaluationRecordStore ---------------------------


class TestAuthorityEvaluationRecordStore:
    def _record(self, evaluation_id="ev-1", package_id="pkg-1"):
        return AuthorityEvaluationRecord(
            record_id=f"aer-{evaluation_id}",
            package_id=package_id,
            evaluation_id=evaluation_id,
            outcome=_outcome(),
            evaluated_at=_TS,
        )

    def test_write_then_read_record(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record = self._record()
        store.write_record(record)
        read_back = store.read_record("pkg-1", "ev-1")
        assert read_back.record_id == record.record_id

    def test_missing_record_returns_none(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        assert store.read_record("pkg-none", "ev-none") is None

    def test_identical_rewrite_is_idempotent_noop(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record = self._record()
        store.write_record(record)
        store.write_record(record)  # no-op, not an error

    def test_conflicting_rewrite_raises(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        store.write_record(self._record())
        conflicting = AuthorityEvaluationRecord(
            record_id="aer-different",
            package_id="pkg-1",
            evaluation_id="ev-1",
            outcome=_outcome(),
            evaluated_at="2026-06-01T00:00:00Z",
        )
        with pytest.raises(AuthorityEvaluationRecordConflictError):
            store.write_record(conflicting)

    def test_pointer_round_trip_and_canonical_read(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record = self._record()
        store.write_record(record)
        digest = aer_to_payload(record)["record_digest"]
        store.write_pointer(
            CanonicalPointer(package_id="pkg-1", evaluation_id="ev-1", record_id=record.record_id, record_digest=digest)
        )
        canonical = store.read_canonical("pkg-1")
        assert canonical.record_id == record.record_id

    def test_no_canonical_returns_none(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        assert store.read_canonical("pkg-none") is None

    def test_corrupted_pointer_digest_raises(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record = self._record()
        store.write_record(record)
        digest = aer_to_payload(record)["record_digest"]
        store.write_pointer(
            CanonicalPointer(package_id="pkg-1", evaluation_id="ev-1", record_id=record.record_id, record_digest=digest)
        )
        pointer_path = tmp_path / "pointers" / "pkg-1.json"
        payload = json.loads(pointer_path.read_text())
        payload["record_digest"] = "f" * 64
        pointer_path.write_text(json.dumps(payload))
        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-1")

    def test_pointer_naming_missing_record_raises(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        store.write_pointer(
            CanonicalPointer(package_id="pkg-1", evaluation_id="ev-missing", record_id="aer-missing", record_digest="a" * 64)
        )
        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-1")

    def test_list_evaluation_ids(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        store.write_record(self._record(evaluation_id="ev-1"))
        store.write_record(self._record(evaluation_id="ev-2"))
        assert store.list_evaluation_ids("pkg-1") == ("ev-1", "ev-2")
        assert store.list_evaluation_ids("pkg-none") == ()


# --- Service: Stage 1 / Stage 2 lifecycle -----------------------------------


class TestStage1Evaluation:
    def test_returns_advisory_outcome(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        session = _session()
        result = service.evaluate_stage_1(session=session)
        assert result.outcome.evaluation_result is EvaluationResult.ELIGIBLE
        assert result.session_id == session.session_id

    def test_never_persists(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        service.evaluate_stage_1(session=_session())
        assert store.read_canonical("anything") is None

    def test_repeated_invocation_recomputes(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        a = service.evaluate_stage_1(session=_session())
        b = service.evaluate_stage_1(session=_session())
        assert a.evaluation_id != b.evaluation_id
        assert a.outcome.evaluation_result == b.outcome.evaluation_result


class TestStage2Evaluation:
    def test_first_attempt_persists_and_publishes_pointer(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        aer = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        assert store.read_canonical("pkg-1").record_id == aer.record_id

    def test_idempotent_retry_returns_same_record(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        aer1 = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        aer2 = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        assert aer1.record_id == aer2.record_id

    def test_registry_evolution_supersedes(self, tmp_path):
        service, _, registry = _build_service(tmp_path)
        aer1 = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        registry.write_declaration(
            EligibleAuthorityDeclaration(
                template_ref="tpl-1",
                template_version="v1",
                eligible_identities=frozenset({"bob"}),
                declared_at="2026-06-01T00:00:00Z",
                declared_by="governance",
            )
        )
        aer2 = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        assert aer2.record_id != aer1.record_id
        assert aer2.outcome.evaluation_result is EvaluationResult.INELIGIBLE

    def test_stage_1_present_to_absent_transition_supersedes(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        s1 = service.evaluate_stage_1(session=_session())
        aer1 = service.evaluate_stage_2(session=_session(), package_id="pkg-1", stage_1_result=s1)
        assert aer1.stage_1_outcome_ref is not None
        aer2 = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        assert aer2.record_id != aer1.record_id
        assert aer2.stage_1_outcome_ref is None

    def test_stage_1_absent_to_present_transition_supersedes(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        aer1 = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        s1 = service.evaluate_stage_1(session=_session())
        aer2 = service.evaluate_stage_2(session=_session(), package_id="pkg-1", stage_1_result=s1)
        assert aer2.record_id != aer1.record_id
        assert aer2.stage_1_outcome_ref is not None

    def test_equivalent_stage_1_evidence_no_op(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        s1 = service.evaluate_stage_1(session=_session())
        aer1 = service.evaluate_stage_2(session=_session(), package_id="pkg-1", stage_1_result=s1)
        s1b = service.evaluate_stage_1(session=_session())  # different evaluation_id, same content
        aer2 = service.evaluate_stage_2(session=_session(), package_id="pkg-1", stage_1_result=s1b)
        assert aer1.record_id == aer2.record_id

    def test_distinct_package_ids_never_collide(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        aer1 = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        aer2 = service.evaluate_stage_2(session=_session(), package_id="pkg-2")
        assert aer1.record_id != aer2.record_id

    def test_ineligible_outcome_carries_no_citation(self, tmp_path):
        service, _, _ = _build_service(tmp_path, eligible=("someone-else",))
        aer = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        assert aer.outcome.evaluation_result is EvaluationResult.INELIGIBLE
        assert aer.outcome.citation_text is None


class TestStage1HandoffValidation:
    def test_malformed_rejected(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        with pytest.raises(Stage1HandoffInvalidError) as exc_info:
            service.evaluate_stage_2(session=_session(), package_id="pkg-1", stage_1_result="not-a-result")
        assert exc_info.value.reason is Stage1HandoffInvalidReason.MALFORMED

    def test_session_mismatch_rejected(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        s1 = service.evaluate_stage_1(session=_session(session_id="sess-1"))
        with pytest.raises(Stage1HandoffInvalidError) as exc_info:
            service.evaluate_stage_2(session=_session(session_id="sess-2"), package_id="pkg-1", stage_1_result=s1)
        assert exc_info.value.reason is Stage1HandoffInvalidReason.SESSION_MISMATCH

    def test_identity_mismatch_rejected(self, tmp_path):
        service, _, _ = _build_service(tmp_path, eligible=("alice", "bob"))
        s1 = service.evaluate_stage_1(session=_session(owner_identity="alice"))
        forged = Stage1EvaluationResult(
            outcome=_outcome(claimed_identity="bob"), evaluation_id=s1.evaluation_id, session_id=s1.session_id
        )
        with pytest.raises(Stage1HandoffInvalidError) as exc_info:
            service.evaluate_stage_2(session=_session(owner_identity="alice"), package_id="pkg-1", stage_1_result=forged)
        assert exc_info.value.reason is Stage1HandoffInvalidReason.IDENTITY_MISMATCH

    def test_template_mismatch_rejected(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        write_template("tpl-2", "v1", "Different template.", root=tmp_path / "templates")
        s1 = service.evaluate_stage_1(session=_session(template_ref="tpl-1"))
        forged = Stage1EvaluationResult(
            outcome=_outcome(template_ref="tpl-2"), evaluation_id=s1.evaluation_id, session_id=s1.session_id
        )
        with pytest.raises(Stage1HandoffInvalidError) as exc_info:
            service.evaluate_stage_2(session=_session(template_ref="tpl-1"), package_id="pkg-1", stage_1_result=forged)
        assert exc_info.value.reason is Stage1HandoffInvalidReason.TEMPLATE_MISMATCH

    def test_invalid_handoff_produces_no_side_effects(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        with pytest.raises(Stage1HandoffInvalidError):
            service.evaluate_stage_2(session=_session(), package_id="pkg-1", stage_1_result="garbage")
        assert store.read_canonical("pkg-1") is None

    def test_none_is_always_valid(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        aer = service.evaluate_stage_2(session=_session(), package_id="pkg-1", stage_1_result=None)
        assert aer.stage_1_outcome_ref is None


# --- Recovery ----------------------------------------------------------------


class TestRecovery:
    def test_aer_committed_pointer_absent_recovers_on_retry(self, tmp_path):
        """AESIC-REQ-130: simulate a crash between AER commit and pointer
        write by writing the record directly (bypassing the pointer step),
        then confirm a fresh evaluate_stage_2 call discovers no canonical
        AER (pointer absent) and completes normally -- persisting another
        AER and publishing the pointer -- never treating the orphaned
        first AER as canonical merely because it exists."""

        service, store, _ = _build_service(tmp_path)
        orphaned = AuthorityEvaluationRecord(
            record_id="aer-orphan",
            package_id="pkg-1",
            evaluation_id="ev-orphan",
            outcome=_outcome(),
            evaluated_at=_TS,
        )
        store.write_record(orphaned)
        assert store.read_canonical("pkg-1") is None  # uncommitted candidate, never auto-canonical

        aer = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        assert aer.record_id != "aer-orphan"
        assert store.read_canonical("pkg-1").record_id == aer.record_id
        # The orphaned candidate remains durably retrievable -- disclosed
        # surplus history, never data loss.
        assert store.read_record("pkg-1", "ev-orphan") is not None

    def test_pointer_write_failure_raises_and_preserves_committed_aer(self, tmp_path, monkeypatch):
        service, store, _ = _build_service(tmp_path)

        def _boom(self, pointer):
            raise OSError("simulated pointer write failure")

        monkeypatch.setattr(AuthorityEvaluationRecordStore, "write_pointer", _boom)
        with pytest.raises(CanonicalPointerUpdateFailedError):
            service.evaluate_stage_2(session=_session(), package_id="pkg-1")

        # The AER itself was committed before the simulated pointer failure.
        evaluation_ids = store.list_evaluation_ids("pkg-1")
        assert len(evaluation_ids) == 1
        assert store.read_canonical("pkg-1") is None

    def test_retry_after_pointer_failure_succeeds(self, tmp_path, monkeypatch):
        service, store, _ = _build_service(tmp_path)

        def _boom(self, pointer):
            raise OSError("simulated pointer write failure")

        monkeypatch.setattr(AuthorityEvaluationRecordStore, "write_pointer", _boom)
        with pytest.raises(CanonicalPointerUpdateFailedError):
            service.evaluate_stage_2(session=_session(), package_id="pkg-1")

        monkeypatch.undo()
        aer = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        assert store.read_canonical("pkg-1").record_id == aer.record_id
        # Two distinct AERs now exist for pkg-1: the one from the failed
        # attempt (surplus, harmless) and the one the retry made canonical.
        assert len(store.list_evaluation_ids("pkg-1")) == 2


# --- Security ------------------------------------------------------------


class TestSecurity:
    def test_cross_session_stage_1_evidence_rejected(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        victim_s1 = service.evaluate_stage_1(session=_session(session_id="victim-session"))
        with pytest.raises(Stage1HandoffInvalidError) as exc_info:
            service.evaluate_stage_2(
                session=_session(session_id="attacker-session"), package_id="pkg-1", stage_1_result=victim_s1
            )
        assert exc_info.value.reason is Stage1HandoffInvalidReason.SESSION_MISMATCH

    def test_tampered_aer_content_fails_digest_verification(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        aer = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        record_path = tmp_path / "records" / "records" / "pkg-1" / f"{aer.evaluation_id}.json"
        payload = json.loads(record_path.read_text())
        payload["outcome"]["citation_text"] = "Forged citation."
        record_path.write_text(json.dumps(payload))
        from pcae.aesic.errors import AuthorityEvaluationRecordCorruptError

        with pytest.raises(AuthorityEvaluationRecordCorruptError):
            store.read_record("pkg-1", aer.evaluation_id)

    def test_pointer_record_id_substitution_detected(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        service.evaluate_stage_1(session=_session())  # unrelated, no persistence

        # Establish a second, unrelated AER under the same package via a
        # direct store write (simulating an attacker substituting the
        # pointer's record_id to name it instead of the legitimate one).
        rogue = AuthorityEvaluationRecord(
            record_id="aer-rogue",
            package_id="pkg-1",
            evaluation_id="ev-rogue",
            outcome=_outcome(claimed_identity="mallory", result=EvaluationResult.INDETERMINATE, citation_text=None, declaration_ref=None),
            evaluated_at=_TS,
        )
        store.write_record(rogue)

        pointer_path = tmp_path / "records" / "pointers" / "pkg-1.json"
        payload = json.loads(pointer_path.read_text())
        payload["record_id"] = "aer-rogue"
        payload["evaluation_id"] = "ev-rogue"
        # pointer_digest deliberately left stale (not recomputed) -- this
        # is exactly the tamper this mechanism must catch.
        pointer_path.write_text(json.dumps(payload))

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-1")


# --- Integration: Readiness package + CHGR citation ------------------------


class TestPublicationReadinessPackageIntegration:
    def test_authority_evaluation_ref_requires_citation_text(self):
        with pytest.raises(ValueError):
            PublicationReadinessPackage(
                package_id="prp-1",
                session_id=generate_session_id(),
                session_state=SessionState.CONFIRMED,
                transition_sequence_number=1,
                evidence_refs=(),
                clarification_refs=(),
                audit_refs=(),
                preview_id="pv-1",
                preview_digest="d" * 64,
                confirmation_request_id="req-1",
                confirmation_response_id="resp-1",
                built_at=_TS,
                authority_evaluation_ref={"record_id": "aer-1", "record_digest": "d" * 64, "record_family": "authority_evaluation_record"},
                citation_text=None,
            )

    def test_citation_text_requires_authority_evaluation_ref(self):
        with pytest.raises(ValueError):
            PublicationReadinessPackage(
                package_id="prp-1",
                session_id=generate_session_id(),
                session_state=SessionState.CONFIRMED,
                transition_sequence_number=1,
                evidence_refs=(),
                clarification_refs=(),
                audit_refs=(),
                preview_id="pv-1",
                preview_digest="d" * 64,
                confirmation_request_id="req-1",
                confirmation_response_id="resp-1",
                built_at=_TS,
                citation_text="orphan citation",
            )

    def test_absent_pair_is_backward_compatible(self):
        package = PublicationReadinessPackage(
            package_id="prp-1",
            session_id=generate_session_id(),
            session_state=SessionState.CONFIRMED,
            transition_sequence_number=1,
            evidence_refs=(),
            clarification_refs=(),
            audit_refs=(),
            preview_id="pv-1",
            preview_digest="d" * 64,
            confirmation_request_id="req-1",
            confirmation_response_id="resp-1",
            built_at=_TS,
        )
        assert package.authority_evaluation_ref is None
        assert package.citation_text is None


def _base_package_kwargs(**overrides):
    kwargs = dict(
        package_id="prp-1",
        session_id=generate_session_id(),
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=1,
        evidence_refs=(),
        clarification_refs=(),
        audit_refs=(),
        preview_id="pv-1",
        preview_digest="d" * 64,
        confirmation_request_id="req-1",
        confirmation_response_id="resp-1",
        built_at=_TS,
        decision_subject="subj-1",
        template_id="tpl-1",
        template_version="1.0",
        selected_option_id="approve",
        options_presented=("approve", "reject"),
        decision_maker_identity_evidence={"evidence_kind": "typed_confirmation_only", "identifier": "alice", "captured_at": _TS},
        preview_rendered_content="Rendered preview.",
        confirmation_statement="confirmed",
        confirmation_timestamp=_TS,
    )
    kwargs.update(overrides)
    return kwargs


def _event(package: PublicationReadinessPackage) -> PublicationAuthorizationEvent:
    return PublicationAuthorizationEvent(
        event_id="pubauth-1", operator_id="alice", package_id=package.package_id, invoked_at=_TS
    )


class TestChgrCitationIntegration:
    def test_citation_populated_when_package_carries_evaluation_ref(self):
        package = PublicationReadinessPackage(
            **_base_package_kwargs(
                authority_evaluation_ref={
                    "record_id": "aer-1",
                    "record_digest": "d" * 64,
                    "record_family": "authority_evaluation_record",
                },
                citation_text="Only Finance may approve.",
            )
        )
        bundle = build_publication_record(package, _event(package), "chgr-00000001", _TS)
        hgr = bundle["human_governance_record"]
        assert hgr["authority_basis_claimed"] == "Only Finance may approve."
        assert not any("authority_basis_claimed" in entry for entry in hgr["limitations"])

    def test_citation_absent_discloses_limitation(self):
        package = PublicationReadinessPackage(**_base_package_kwargs())
        bundle = build_publication_record(package, _event(package), "chgr-00000001", _TS)
        hgr = bundle["human_governance_record"]
        assert "authority_basis_claimed" not in hgr
        assert any("authority_basis_claimed" in entry for entry in hgr["limitations"])
