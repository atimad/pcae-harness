"""Phase 143O unit/integration tests: Session Coordination & Publication
Handoff Integration (IWC-001 v1.1 §2, §11.4, §18.4, IWC-REQ-171).

Covers: deterministic eight-stage workflow sequencing
(``WorkflowOrchestrator``), component invocation order, dependency
isolation (no lateral component-to-component calls), orchestration
repeatability; Publication Readiness Package immutability, completeness
validation, serialization, readiness determination
(``PublicationHandoff``); boundary protection (publication cannot occur,
CHGR cannot be created, lifecycle commands cannot be invoked, runtime
authority remains absent); ``SessionCoordinator``'s new
``build_orchestrator``/``orchestrate_evidence``/``perform_confirmation``
delegation and its permanently-``NotImplementedError``
``perform_publication``; and regression checks confirming Session
Infrastructure (143K), Transition Engine (143L),
Evidence/Clarification/Audit (143M), Preview/Confirmation (143N), and
runtime state are unchanged. No test in this module exercises
publication, CHGR creation, or lifecycle command invocation -- 143O's
explicit no-go boundary.
"""

from __future__ import annotations

import pytest

from pcae.interactive_workflow.audit.models import AuditEvent
from pcae.interactive_workflow.audit.recorder import AuditRecorder
from pcae.interactive_workflow.clarification.controller import ClarificationController
from pcae.interactive_workflow.clarification.models import Clarification
from pcae.interactive_workflow.confirmation.controller import ConfirmationController
from pcae.interactive_workflow.confirmation.models import (
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationResult,
)
from pcae.interactive_workflow.errors import (
    InvalidWorkflowSequenceError,
    MissingWorkflowComponentError,
    PublicationHandoffIncompleteError,
    PublicationHandoffSerializationError,
    ReplayDetectedError,
    UnsupportedVersionError,
    WorkflowCompositionError,
    WorkflowInitializationError,
)
from pcae.interactive_workflow.evidence.coordinator import EvidenceCoordinator
from pcae.interactive_workflow.evidence.models import EvidenceAvailability, EvidenceItem
from pcae.interactive_workflow.models.session import Session, SessionState
from pcae.interactive_workflow.orchestration.coordinator import WorkflowOrchestrator
from pcae.interactive_workflow.orchestration.models import (
    ORCHESTRATION_SCHEMA_VERSION,
    STAGE_ORDER,
    OrchestrationStage,
    OrchestrationState,
)
from pcae.interactive_workflow.preview.builder import PreviewBuilder
from pcae.interactive_workflow.publication_handoff.handoff import PublicationHandoff
from pcae.interactive_workflow.publication_handoff.models import (
    PUBLICATION_HANDOFF_SCHEMA_VERSION,
    PublicationReadinessPackage,
)
from pcae.interactive_workflow.serialization import publication_handoff_schema
from pcae.interactive_workflow.session.coordinator import SessionCoordinator
from pcae.interactive_workflow.session.identity import generate_session_id
from pcae.interactive_workflow.state_machine.engine import TransitionEngine

_TS = "2026-07-24T10:00:00+00:00"


@pytest.fixture()
def session_id() -> str:
    return generate_session_id()


def _session(session_id: str, state: SessionState = SessionState.CREATED) -> Session:
    return Session(
        session_id=session_id,
        owner_identity="human-1",
        template_ref="template-1",
        subject_ref="subject-1",
        session_state=state,
        created_at=_TS,
        updated_at=_TS,
    )


def _components(session_id: str):
    return {
        "evidence_coordinator": EvidenceCoordinator(session_id),
        "clarification_controller": ClarificationController(session_id),
        "audit_recorder": AuditRecorder(session_id),
        "preview_builder": PreviewBuilder(),
        "confirmation_controller": ConfirmationController(session_id),
        "transition_engine": TransitionEngine(),
    }


def _orchestrator(session_id: str) -> WorkflowOrchestrator:
    return WorkflowOrchestrator(session_id=session_id, **_components(session_id))


# --- OrchestrationState / OrchestrationStage --------------------------------


def test_orchestration_state_starts_empty(session_id):
    state = OrchestrationState(session_id=session_id)
    assert state.completed_stages == ()
    assert state.next_stage is OrchestrationStage.SESSION_INITIALIZATION
    assert not state.is_complete()
    assert state.schema_version == ORCHESTRATION_SCHEMA_VERSION


def test_orchestration_state_rejects_invalid_session_id():
    with pytest.raises(Exception):
        OrchestrationState(session_id="not-a-session-id")


def test_orchestration_state_advances_in_fixed_order(session_id):
    state = OrchestrationState(session_id=session_id)
    for stage in STAGE_ORDER:
        state = state.with_stage_completed(stage)
    assert state.is_complete()
    assert state.completed_stages == STAGE_ORDER
    assert state.next_stage is None


def test_orchestration_state_rejects_out_of_order_stage(session_id):
    state = OrchestrationState(session_id=session_id)
    with pytest.raises(InvalidWorkflowSequenceError):
        state.with_stage_completed(OrchestrationStage.EVIDENCE_AVAILABILITY)


def test_orchestration_state_rejects_duplicate_stage(session_id):
    state = OrchestrationState(session_id=session_id)
    state = state.with_stage_completed(OrchestrationStage.SESSION_INITIALIZATION)
    with pytest.raises(InvalidWorkflowSequenceError):
        state.with_stage_completed(OrchestrationStage.SESSION_INITIALIZATION)


def test_orchestration_state_is_immutable(session_id):
    state = OrchestrationState(session_id=session_id)
    with pytest.raises(Exception):
        state.session_id = "CDS-x"  # type: ignore[misc]


# --- WorkflowOrchestrator: composition / dependency enforcement ------------


def test_workflow_orchestrator_requires_all_six_components(session_id):
    components = _components(session_id)
    for missing_key in components:
        incomplete = dict(components)
        incomplete[missing_key] = None
        with pytest.raises(MissingWorkflowComponentError):
            WorkflowOrchestrator(session_id=session_id, **incomplete)


def test_workflow_orchestrator_rejects_wrong_typed_component(session_id):
    components = _components(session_id)
    components["evidence_coordinator"] = "not-an-evidence-coordinator"
    with pytest.raises(MissingWorkflowComponentError):
        WorkflowOrchestrator(session_id=session_id, **components)


def test_workflow_orchestrator_rejects_mismatched_session_scoped_component(session_id):
    other_session_id = generate_session_id()
    components = _components(session_id)
    components["evidence_coordinator"] = EvidenceCoordinator(other_session_id)
    with pytest.raises(WorkflowCompositionError):
        WorkflowOrchestrator(session_id=session_id, **components)


def test_workflow_orchestrator_scoped_to_one_session_id(session_id):
    orchestrator = _orchestrator(session_id)
    assert orchestrator.session_id == session_id
    assert orchestrator.state.session_id == session_id


# --- WorkflowOrchestrator: deterministic sequencing -------------------------


def test_stage_session_initialization_rejects_mismatched_session(session_id):
    orchestrator = _orchestrator(session_id)
    other_session = _session(generate_session_id())
    with pytest.raises(WorkflowInitializationError):
        orchestrator.stage_session_initialization(other_session)


def test_full_eight_stage_sequence_completes_deterministically(session_id):
    orchestrator = _orchestrator(session_id)
    session = _session(session_id)

    state = orchestrator.stage_session_initialization(session)
    assert state.completed_stages == (OrchestrationStage.SESSION_INITIALIZATION,)

    missing = orchestrator.stage_evidence_availability(["ev-1"])
    assert missing == ("ev-1",)

    history = orchestrator.stage_clarification_lifecycle()
    assert history == ()

    preview, digest = orchestrator.stage_preview_construction(
        preview_id="preview-1",
        preview_timestamp=_TS,
        transition_sequence_number=0,
        evidence_refs=(),
        clarification_refs=(),
        audit_refs=(),
    )
    assert digest == PreviewBuilder().compute_digest(preview)

    orchestrator.stage_preview_validation(preview, preview_digest=digest)

    request = ConfirmationRequest(
        request_id="req-1",
        session_id=session_id,
        preview_id=preview.preview_id,
        preview_digest=digest,
        created_at=_TS,
    )
    orchestrator.stage_confirmation_request(request)

    response = ConfirmationResponse(
        response_id="resp-1",
        request_id="req-1",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest=digest,
    )
    accepted = orchestrator.stage_confirmation_validation(
        "req-1", response, preview, current_transition_sequence_number=0
    )
    assert accepted.response_id == "resp-1"

    confirmed_session = session.with_state(SessionState.CONFIRMED, _TS)
    completed = orchestrator.stage_terminal_completion(confirmed_session)
    assert completed.session_state is SessionState.CONFIRMED

    assert orchestrator.state.is_complete()


def test_stage_terminal_completion_rejects_non_terminal_session(session_id):
    orchestrator = _orchestrator(session_id)
    session = _session(session_id)
    orchestrator.stage_session_initialization(session)
    orchestrator.stage_evidence_availability([])
    orchestrator.stage_clarification_lifecycle()
    preview, digest = orchestrator.stage_preview_construction(
        preview_id="preview-1", preview_timestamp=_TS, transition_sequence_number=0
    )
    orchestrator.stage_preview_validation(preview, preview_digest=digest)
    request = ConfirmationRequest(
        request_id="req-1",
        session_id=session_id,
        preview_id=preview.preview_id,
        preview_digest=digest,
        created_at=_TS,
    )
    orchestrator.stage_confirmation_request(request)
    response = ConfirmationResponse(
        response_id="resp-1",
        request_id="req-1",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest=digest,
    )
    orchestrator.stage_confirmation_validation("req-1", response, preview, 0)
    with pytest.raises(InvalidWorkflowSequenceError):
        orchestrator.stage_terminal_completion(session)  # still Created, not terminal


def test_out_of_order_invocation_rejected(session_id):
    orchestrator = _orchestrator(session_id)
    with pytest.raises(InvalidWorkflowSequenceError):
        orchestrator.stage_evidence_availability([])


def test_duplicate_orchestration_of_same_stage_rejected(session_id):
    orchestrator = _orchestrator(session_id)
    orchestrator.stage_session_initialization(_session(session_id))
    with pytest.raises(InvalidWorkflowSequenceError):
        orchestrator.stage_session_initialization(_session(session_id))


def test_preview_validation_failure_does_not_advance_stage(session_id):
    orchestrator = _orchestrator(session_id)
    orchestrator.stage_session_initialization(_session(session_id))
    orchestrator.stage_evidence_availability([])
    orchestrator.stage_clarification_lifecycle()
    preview, digest = orchestrator.stage_preview_construction(
        preview_id="preview-1", preview_timestamp=_TS, transition_sequence_number=0
    )
    with pytest.raises(Exception):
        orchestrator.stage_preview_validation(preview, preview_digest="wrong-digest")
    assert orchestrator.state.next_stage is OrchestrationStage.PREVIEW_VALIDATION


def test_confirmation_validation_replay_propagates_through_orchestrator(session_id):
    # Two orchestrator instances sharing the same underlying components
    # (particularly the same ConfirmationController) so a digest confirmed
    # via the first orchestrator's run is provably replayed against the
    # second -- exercising ReplayDetectedError propagation *through*
    # WorkflowOrchestrator.stage_confirmation_validation, not merely at
    # ConfirmationController directly (already covered by 143N's own
    # regression-preserved test).
    components = _components(session_id)
    orchestrator1 = WorkflowOrchestrator(session_id=session_id, **components)
    orchestrator1.stage_session_initialization(_session(session_id))
    orchestrator1.stage_evidence_availability([])
    orchestrator1.stage_clarification_lifecycle()
    preview, digest = orchestrator1.stage_preview_construction(
        preview_id="preview-1", preview_timestamp=_TS, transition_sequence_number=0
    )
    orchestrator1.stage_preview_validation(preview, preview_digest=digest)
    request1 = ConfirmationRequest(
        request_id="req-1",
        session_id=session_id,
        preview_id=preview.preview_id,
        preview_digest=digest,
        created_at=_TS,
    )
    orchestrator1.stage_confirmation_request(request1)
    response1 = ConfirmationResponse(
        response_id="resp-1",
        request_id="req-1",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest=digest,
    )
    orchestrator1.stage_confirmation_validation("req-1", response1, preview, 0)

    orchestrator2 = WorkflowOrchestrator(session_id=session_id, **components)
    orchestrator2.stage_session_initialization(_session(session_id))
    orchestrator2.stage_evidence_availability([])
    orchestrator2.stage_clarification_lifecycle()
    preview2, digest2 = orchestrator2.stage_preview_construction(
        preview_id="preview-1", preview_timestamp=_TS, transition_sequence_number=0
    )
    orchestrator2.stage_preview_validation(preview2, preview_digest=digest2)
    request2 = ConfirmationRequest(
        request_id="req-2",
        session_id=session_id,
        preview_id=preview2.preview_id,
        preview_digest=digest2,
        created_at=_TS,
    )
    orchestrator2.stage_confirmation_request(request2)
    response2 = ConfirmationResponse(
        response_id="resp-2",
        request_id="req-2",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest=digest2,
    )
    with pytest.raises(ReplayDetectedError):
        orchestrator2.stage_confirmation_validation("req-2", response2, preview2, 0)
    # Confirmed the failure was not silently swallowed: the stage must not
    # have advanced.
    assert orchestrator2.state.next_stage is OrchestrationStage.CONFIRMATION_VALIDATION


def test_orchestrator_no_publish_or_lateral_component_method_exists(session_id):
    orchestrator = _orchestrator(session_id)
    forbidden = {"publish", "notify", "create_chgr", "invoke_lifecycle", "execute"}
    for name in forbidden:
        assert not hasattr(orchestrator, name)


def test_orchestrator_module_does_not_import_publication_or_chgr_symbols():
    import ast
    import inspect

    import pcae.interactive_workflow.orchestration.coordinator as orchestration_module

    source = inspect.getsource(orchestration_module)
    tree = ast.parse(source)
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported_names.update(alias.asname or alias.name for alias in node.names)
    forbidden = {"PublicationHandoff", "HumanGovernanceRecord"}
    assert imported_names.isdisjoint(forbidden)


# --- SessionCoordinator: orchestration delegation ---------------------------


class _InMemoryRepository:
    """Minimal in-memory ``SessionRepository`` stand-in for coordinator
    tests; not a production repository implementation."""

    def __init__(self):
        self._store = {}

    def create(self, session):
        self._store[session.session_id] = session

    def load(self, session_id):
        return self._store[session_id]

    def persist(self, session):
        self._store[session.session_id] = session

    def exists(self, session_id):
        return session_id in self._store

    def list_session_ids(self):
        return tuple(self._store.keys())


def test_session_coordinator_build_orchestrator_delegates(session_id):
    coordinator = SessionCoordinator(_InMemoryRepository())
    orchestrator = coordinator.build_orchestrator(session_id, **_components(session_id))
    assert isinstance(orchestrator, WorkflowOrchestrator)
    assert orchestrator.session_id == session_id


def test_session_coordinator_orchestrate_evidence_delegates(session_id):
    coordinator = SessionCoordinator(_InMemoryRepository())
    orchestrator = coordinator.build_orchestrator(session_id, **_components(session_id))
    orchestrator.stage_session_initialization(_session(session_id))
    missing = coordinator.orchestrate_evidence(orchestrator, ["ev-1", "ev-2"])
    assert missing == ("ev-1", "ev-2")


def test_session_coordinator_perform_confirmation_delegates(session_id):
    coordinator = SessionCoordinator(_InMemoryRepository())
    orchestrator = coordinator.build_orchestrator(session_id, **_components(session_id))
    orchestrator.stage_session_initialization(_session(session_id))
    orchestrator.stage_evidence_availability([])
    orchestrator.stage_clarification_lifecycle()
    preview, digest = orchestrator.stage_preview_construction(
        preview_id="preview-1", preview_timestamp=_TS, transition_sequence_number=0
    )
    orchestrator.stage_preview_validation(preview, preview_digest=digest)
    request = ConfirmationRequest(
        request_id="req-1",
        session_id=session_id,
        preview_id=preview.preview_id,
        preview_digest=digest,
        created_at=_TS,
    )
    orchestrator.stage_confirmation_request(request)
    response = ConfirmationResponse(
        response_id="resp-1",
        request_id="req-1",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest=digest,
    )
    accepted = coordinator.perform_confirmation(orchestrator, "req-1", response, preview, 0)
    assert accepted.response_id == "resp-1"


def test_session_coordinator_perform_publication_always_raises(session_id):
    coordinator = SessionCoordinator(_InMemoryRepository())
    with pytest.raises(NotImplementedError):
        coordinator.perform_publication()
    with pytest.raises(NotImplementedError):
        coordinator.perform_publication(session_id, "anything")


# --- PublicationReadinessPackage / PublicationHandoff -----------------------


def _confirmed_package_inputs(session_id: str):
    components = _components(session_id)
    components["evidence_coordinator"].register(
        EvidenceItem(
            evidence_id="ev-1",
            evidence_type="type-a",
            provenance_ref="ref-a",
            collected_at=_TS,
            availability=EvidenceAvailability.AVAILABLE,
        )
    )
    orchestrator = WorkflowOrchestrator(session_id=session_id, **components)
    session = _session(session_id)
    orchestrator.stage_session_initialization(session)
    orchestrator.stage_evidence_availability(["ev-1"])
    orchestrator.stage_clarification_lifecycle()
    preview, digest = orchestrator.stage_preview_construction(
        preview_id="preview-1",
        preview_timestamp=_TS,
        transition_sequence_number=0,
        evidence_refs=["ev-1"],
    )
    orchestrator.stage_preview_validation(preview, preview_digest=digest)
    request = ConfirmationRequest(
        request_id="req-1",
        session_id=session_id,
        preview_id=preview.preview_id,
        preview_digest=digest,
        created_at=_TS,
    )
    orchestrator.stage_confirmation_request(request)
    response = ConfirmationResponse(
        response_id="resp-1",
        request_id="req-1",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest=digest,
    )
    orchestrator.stage_confirmation_validation("req-1", response, preview, 0)
    confirmed_session = session.with_state(SessionState.CONFIRMED, _TS)
    orchestrator.stage_terminal_completion(confirmed_session)
    return {
        "orchestrator": orchestrator,
        "session": confirmed_session,
        "preview": preview,
        "request": request,
        "response": response,
    }


def test_publication_handoff_builds_package_from_confirmed_session(session_id):
    inputs = _confirmed_package_inputs(session_id)
    handoff = PublicationHandoff()
    package = handoff.build_package(
        package_id="pkg-1",
        session=inputs["session"],
        orchestration_state=inputs["orchestrator"].state,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview=inputs["preview"],
        confirmation_request=inputs["request"],
        confirmation_response=inputs["response"],
        built_at=_TS,
    )
    assert package.session_id == session_id
    assert package.session_state is SessionState.CONFIRMED
    assert package.preview_id == inputs["preview"].preview_id
    assert package.confirmation_request_id == "req-1"
    assert package.confirmation_response_id == "resp-1"
    assert handoff.is_ready(package)


def test_publication_handoff_rejects_non_confirmed_session(session_id):
    inputs = _confirmed_package_inputs(session_id)
    handoff = PublicationHandoff()
    not_confirmed = inputs["session"].with_state(SessionState.CREATED, _TS)
    with pytest.raises(PublicationHandoffIncompleteError):
        handoff.build_package(
            package_id="pkg-1",
            session=not_confirmed,
            orchestration_state=inputs["orchestrator"].state,
            transition_sequence_number=0,
            evidence_refs=("ev-1",),
            clarification_refs=(),
            audit_refs=(),
            preview=inputs["preview"],
            confirmation_request=inputs["request"],
            confirmation_response=inputs["response"],
            built_at=_TS,
        )


def test_publication_handoff_rejects_incomplete_orchestration(session_id):
    handoff = PublicationHandoff()
    orchestrator = _orchestrator(session_id)
    session = _session(session_id, state=SessionState.CONFIRMED)
    preview_builder = PreviewBuilder()
    preview, digest = preview_builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    request = ConfirmationRequest(
        request_id="req-1",
        session_id=session_id,
        preview_id=preview.preview_id,
        preview_digest=digest,
        created_at=_TS,
    )
    response = ConfirmationResponse(
        response_id="resp-1",
        request_id="req-1",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest=digest,
    )
    with pytest.raises(PublicationHandoffIncompleteError):
        handoff.build_package(
            package_id="pkg-1",
            session=session,
            orchestration_state=orchestrator.state,  # empty -- incomplete
            transition_sequence_number=0,
            evidence_refs=(),
            clarification_refs=(),
            audit_refs=(),
            preview=preview,
            confirmation_request=request,
            confirmation_response=response,
            built_at=_TS,
        )


def test_publication_handoff_rejects_mismatched_confirmation_response(session_id):
    inputs = _confirmed_package_inputs(session_id)
    handoff = PublicationHandoff()
    mismatched_response = ConfirmationResponse(
        response_id="resp-x",
        request_id="req-x",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest="deadbeef",
    )
    with pytest.raises(PublicationHandoffIncompleteError):
        handoff.build_package(
            package_id="pkg-1",
            session=inputs["session"],
            orchestration_state=inputs["orchestrator"].state,
            transition_sequence_number=0,
            evidence_refs=("ev-1",),
            clarification_refs=(),
            audit_refs=(),
            preview=inputs["preview"],
            confirmation_request=inputs["request"],
            confirmation_response=mismatched_response,
            built_at=_TS,
        )


def test_publication_readiness_package_is_immutable(session_id):
    inputs = _confirmed_package_inputs(session_id)
    handoff = PublicationHandoff()
    package = handoff.build_package(
        package_id="pkg-1",
        session=inputs["session"],
        orchestration_state=inputs["orchestrator"].state,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview=inputs["preview"],
        confirmation_request=inputs["request"],
        confirmation_response=inputs["response"],
        built_at=_TS,
    )
    with pytest.raises(Exception):
        package.package_id = "pkg-2"  # type: ignore[misc]


def test_publication_readiness_package_carries_no_publication_state_result_chgr_or_authority(
    session_id,
):
    inputs = _confirmed_package_inputs(session_id)
    handoff = PublicationHandoff()
    package = handoff.build_package(
        package_id="pkg-1",
        session=inputs["session"],
        orchestration_state=inputs["orchestrator"].state,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview=inputs["preview"],
        confirmation_request=inputs["request"],
        confirmation_response=inputs["response"],
        built_at=_TS,
    )
    forbidden_field_names = {
        "publication_state",
        "publication_result",
        "published",
        "chgr_id",
        "chgr_ref",
        "authority_token",
        "authorization",
    }
    field_names = set(package.__dataclass_fields__.keys())
    assert field_names.isdisjoint(forbidden_field_names)


def test_publication_handoff_validate_completeness_rejects_missing_fields():
    handoff = PublicationHandoff()

    class _Blank:
        package_id = ""
        session_id = ""
        session_state = None
        preview_id = ""
        preview_digest = ""
        confirmation_request_id = ""
        confirmation_response_id = ""
        built_at = ""

    with pytest.raises(PublicationHandoffIncompleteError):
        handoff.validate_completeness(_Blank())


def test_publication_handoff_is_ready_never_raises_on_incomplete_package():
    handoff = PublicationHandoff()

    class _Blank:
        package_id = ""
        session_id = ""
        session_state = None
        preview_id = ""
        preview_digest = ""
        confirmation_request_id = ""
        confirmation_response_id = ""
        built_at = ""

    assert handoff.is_ready(_Blank()) is False


def test_publication_handoff_serialization_round_trips(session_id):
    inputs = _confirmed_package_inputs(session_id)
    handoff = PublicationHandoff()
    package = handoff.build_package(
        package_id="pkg-1",
        session=inputs["session"],
        orchestration_state=inputs["orchestrator"].state,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview=inputs["preview"],
        confirmation_request=inputs["request"],
        confirmation_response=inputs["response"],
        built_at=_TS,
    )
    payload = handoff.serialize(package)
    restored = handoff.deserialize(payload)
    assert restored == package
    assert payload["schema_version"] == PUBLICATION_HANDOFF_SCHEMA_VERSION


def test_publication_handoff_schema_round_trips_directly(session_id):
    inputs = _confirmed_package_inputs(session_id)
    handoff = PublicationHandoff()
    package = handoff.build_package(
        package_id="pkg-1",
        session=inputs["session"],
        orchestration_state=inputs["orchestrator"].state,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview=inputs["preview"],
        confirmation_request=inputs["request"],
        confirmation_response=inputs["response"],
        built_at=_TS,
    )
    payload = publication_handoff_schema.to_payload(package)
    restored = publication_handoff_schema.from_payload(payload)
    assert restored == package


def test_publication_handoff_schema_rejects_unsupported_version():
    with pytest.raises(UnsupportedVersionError):
        publication_handoff_schema.from_payload({"schema_version": "not-a-real-version"})


def test_publication_handoff_schema_rejects_malformed_payload():
    with pytest.raises(PublicationHandoffSerializationError):
        publication_handoff_schema.from_payload(
            {"schema_version": PUBLICATION_HANDOFF_SCHEMA_VERSION}
        )


# --- Boundary Protection -----------------------------------------------------


def test_publication_handoff_has_no_publish_notify_create_chgr_or_invoke_lifecycle_method():
    handoff = PublicationHandoff()
    forbidden = {"publish", "notify", "create_chgr", "invoke_lifecycle", "execute"}
    for name in forbidden:
        assert not hasattr(handoff, name)


def test_publication_readiness_package_has_no_publish_related_method(session_id):
    inputs = _confirmed_package_inputs(session_id)
    handoff = PublicationHandoff()
    package = handoff.build_package(
        package_id="pkg-1",
        session=inputs["session"],
        orchestration_state=inputs["orchestrator"].state,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview=inputs["preview"],
        confirmation_request=inputs["request"],
        confirmation_response=inputs["response"],
        built_at=_TS,
    )
    forbidden = {"publish", "notify", "create_chgr", "invoke_lifecycle", "execute"}
    for name in forbidden:
        assert not hasattr(package, name)


def test_publication_handoff_module_does_not_import_lifecycle_or_chgr_symbols():
    import ast
    import inspect

    import pcae.interactive_workflow.publication_handoff.handoff as handoff_module

    source = inspect.getsource(handoff_module)
    tree = ast.parse(source)
    imported_names = set()
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported_names.update(alias.asname or alias.name for alias in node.names)
            if node.module:
                imported_modules.add(node.module)
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
    assert not any("lifecycle" in module for module in imported_modules)
    assert not any("governance_record" in module for module in imported_modules)
    assert "HumanGovernanceRecord" not in imported_names


def test_session_coordinator_module_permanently_lacks_publication_execution():
    import inspect

    from pcae.interactive_workflow.session import coordinator as coordinator_module

    source = inspect.getsource(coordinator_module.SessionCoordinator.perform_publication)
    assert "NotImplementedError" in source
    assert "raise NotImplementedError" in source


# --- Regression: 143K-143N infrastructure and runtime unchanged ------------


def test_regression_session_infrastructure_untouched():
    from pcae.interactive_workflow.models.session import SCHEMA_VERSION as SESSION_SCHEMA_VERSION

    assert SESSION_SCHEMA_VERSION == "interactive-workflow-session/0.1"
    assert {s.value for s in SessionState} == {
        "Created",
        "EvidenceReady",
        "AwaitingDecision",
        "AwaitingClarification",
        "DecisionSelected",
        "AwaitingConfirmation",
        "Confirmed",
        "Cancelled",
        "Expired",
        "Abandoned",
    }


def test_regression_transition_engine_untouched():
    engine = TransitionEngine()
    session = _session(generate_session_id())
    result = engine.apply(session, SessionState.EVIDENCE_READY, sequence_number=1)
    assert result.session.session_state is SessionState.EVIDENCE_READY


def test_regression_evidence_coordinator_untouched(session_id):
    coordinator = EvidenceCoordinator(session_id)
    item = coordinator.register(
        EvidenceItem(
            evidence_id="ev-1",
            evidence_type="type-a",
            provenance_ref="ref-a",
            collected_at=_TS,
            availability=EvidenceAvailability.AVAILABLE,
        )
    )
    assert coordinator.get("ev-1") == item


def test_regression_clarification_controller_untouched(session_id):
    controller = ClarificationController(session_id)
    clarification = controller.register_request("cl-1", "What does this mean?", _TS)
    assert clarification.clarification_id == "cl-1"
    with pytest.raises(Exception):
        controller.tag("cl-1", "recommendation")


def test_regression_audit_recorder_untouched(session_id):
    recorder = AuditRecorder(session_id)
    event = recorder.append(
        AuditEvent(
            event_id="audit-1",
            session_id=session_id,
            event_type="proposal",
            timestamp=_TS,
        )
    )
    assert recorder.get("audit-1") == event


def test_regression_preview_confirmation_untouched(session_id):
    builder = PreviewBuilder()
    controller = ConfirmationController(session_id)
    preview, digest = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    request = ConfirmationRequest(
        request_id="req-1",
        session_id=session_id,
        preview_id=preview.preview_id,
        preview_digest=digest,
        created_at=_TS,
    )
    controller.register_request(request)
    response = ConfirmationResponse(
        response_id="resp-1",
        request_id="req-1",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest=digest,
    )
    accepted = controller.register_response(
        "req-1", response, preview, current_transition_sequence_number=0
    )
    assert accepted.response_id == "resp-1"


def test_regression_runtime_state_unchanged():
    import subprocess

    result = subprocess.run(
        ["pcae", "runtime", "inspect", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert '"observe"' in result.stdout
