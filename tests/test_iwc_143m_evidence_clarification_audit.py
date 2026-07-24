"""Phase 143M unit tests: Evidence Coordination, Clarification, and Audit
infrastructure (IWC-001 v1.1 §8, §9, §13).

Covers evidence registration/ordering/duplication/missing-reporting/
serialization; clarification request/response lifecycle, immutable
history, and the informational-boundary rejection of recommendation/
persuasion/approval/authorization/decision classification; audit
append-only behavior, deterministic ordering, serialization, immutable
retrieval, and duplicate rejection; and regression checks confirming
Session Infrastructure (143K), Transition Engine (143L), and runtime
state are unchanged. No test in this module exercises Preview Digest
generation, confirmation, publication, or CHGR creation -- 143M's
explicit no-go boundary.
"""

from __future__ import annotations

import pytest

from pcae.interactive_workflow.audit.models import AUDIT_SCHEMA_VERSION, AuditEvent
from pcae.interactive_workflow.audit.recorder import AuditRecorder
from pcae.interactive_workflow.clarification.controller import ClarificationController
from pcae.interactive_workflow.clarification.models import (
    CLARIFICATION_SCHEMA_VERSION,
    Clarification,
    ClarificationState,
    validate_classification_tag,
)
from pcae.interactive_workflow.errors import (
    AuditSerializationFailureError,
    DuplicateAuditEventError,
    DuplicateClarificationError,
    DuplicateEvidenceError,
    InvalidClarificationError,
    SerializationFailureError,
    UnknownEvidenceError,
    UnsupportedVersionError,
)
from pcae.interactive_workflow.evidence.coordinator import EvidenceCoordinator
from pcae.interactive_workflow.evidence.models import (
    EVIDENCE_SCHEMA_VERSION,
    EvidenceAvailability,
    EvidenceItem,
)
from pcae.interactive_workflow.serialization import audit_schema, clarification_schema, evidence_schema
from pcae.interactive_workflow.session.identity import generate_session_id, validate_session_id


@pytest.fixture()
def session_id() -> str:
    return generate_session_id()


# --- Evidence: model -----------------------------------------------------


def test_evidence_item_requires_all_fields():
    with pytest.raises(ValueError):
        EvidenceItem(
            evidence_id="",
            evidence_type="doc",
            provenance_ref="p",
            collected_at="t",
            availability=EvidenceAvailability.AVAILABLE,
        )


def test_evidence_item_rejects_non_enum_availability():
    with pytest.raises(ValueError):
        EvidenceItem(
            evidence_id="e1",
            evidence_type="doc",
            provenance_ref="p",
            collected_at="t",
            availability="Available",  # type: ignore[arg-type]
        )


def test_evidence_item_metadata_is_frozen():
    item = EvidenceItem(
        evidence_id="e1",
        evidence_type="doc",
        provenance_ref="p",
        collected_at="2026-01-01T00:00:00Z",
        availability=EvidenceAvailability.AVAILABLE,
        metadata={"k": "v"},
    )
    with pytest.raises(TypeError):
        item.metadata["k"] = "other"  # type: ignore[index]


def test_evidence_item_carries_no_authority_or_confirmation_fields():
    field_names = set(EvidenceItem.__dataclass_fields__)
    forbidden = {
        "authority",
        "approved",
        "approval",
        "confirmed",
        "confirmation",
        "chgr_ref",
        "chgr_id",
    }
    assert field_names.isdisjoint(forbidden)


# --- Evidence: coordinator ------------------------------------------------


def _evidence(evidence_id: str, collected_at: str, availability=EvidenceAvailability.AVAILABLE) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        evidence_type="doc",
        provenance_ref=f"path/{evidence_id}",
        collected_at=collected_at,
        availability=availability,
    )


def test_evidence_coordinator_registers_and_retrieves(session_id):
    coordinator = EvidenceCoordinator(session_id)
    item = _evidence("e1", "2026-01-01T00:00:00Z")
    coordinator.register(item)
    assert coordinator.get("e1") is item


def test_evidence_coordinator_rejects_duplicate_identifier(session_id):
    coordinator = EvidenceCoordinator(session_id)
    coordinator.register(_evidence("e1", "2026-01-01T00:00:00Z"))
    with pytest.raises(DuplicateEvidenceError):
        coordinator.register(_evidence("e1", "2026-01-02T00:00:00Z"))


def test_evidence_coordinator_unknown_evidence_raises(session_id):
    coordinator = EvidenceCoordinator(session_id)
    with pytest.raises(UnknownEvidenceError):
        coordinator.get("does-not-exist")


def test_evidence_coordinator_ordering_is_deterministic_by_content_not_registration_order(session_id):
    a = EvidenceCoordinator(session_id)
    b = EvidenceCoordinator(session_id)
    items = [
        _evidence("e3", "2026-01-03T00:00:00Z"),
        _evidence("e1", "2026-01-01T00:00:00Z"),
        _evidence("e2", "2026-01-02T00:00:00Z"),
    ]
    for item in items:
        a.register(item)
    for item in reversed(items):
        b.register(item)

    order_a = [item.evidence_id for item in a.ordered_view()]
    order_b = [item.evidence_id for item in b.ordered_view()]
    assert order_a == order_b == ["e1", "e2", "e3"]


def test_evidence_coordinator_ordering_tiebreaks_by_id_when_timestamps_equal(session_id):
    coordinator = EvidenceCoordinator(session_id)
    coordinator.register(_evidence("z", "2026-01-01T00:00:00Z"))
    coordinator.register(_evidence("a", "2026-01-01T00:00:00Z"))
    order = [item.evidence_id for item in coordinator.ordered_view()]
    assert order == ["a", "z"]


def test_evidence_coordinator_reports_missing_declared_evidence(session_id):
    coordinator = EvidenceCoordinator(session_id)
    coordinator.register(_evidence("e1", "2026-01-01T00:00:00Z"))
    missing = coordinator.report_missing(["e1", "e2", "e3"])
    assert missing == ("e2", "e3")


def test_evidence_coordinator_reports_no_gaps_when_all_present(session_id):
    coordinator = EvidenceCoordinator(session_id)
    coordinator.register(_evidence("e1", "2026-01-01T00:00:00Z"))
    assert coordinator.report_missing(["e1"]) == ()


def test_evidence_coordinator_scoped_to_valid_session_id():
    with pytest.raises(Exception):
        EvidenceCoordinator("not-a-session-id")


def test_evidence_coordinator_has_no_evaluation_scoring_or_transition_methods(session_id):
    coordinator = EvidenceCoordinator(session_id)
    forbidden_methods = ("evaluate", "score", "recommend", "decide_readiness", "transition")
    for name in forbidden_methods:
        assert not hasattr(coordinator, name)


# --- Evidence: serialization ----------------------------------------------


def test_evidence_serialization_round_trips(session_id):
    item = _evidence("e1", "2026-01-01T00:00:00Z", EvidenceAvailability.CONFLICTED)
    payload = evidence_schema.to_payload(item)
    assert payload["schema_version"] == EVIDENCE_SCHEMA_VERSION
    restored = evidence_schema.from_payload(payload)
    assert restored == item


def test_evidence_serialization_rejects_unknown_schema_version():
    payload = {
        "schema_version": "interactive-workflow-evidence/9.9",
        "evidence_id": "e1",
        "evidence_type": "doc",
        "provenance_ref": "p",
        "collected_at": "t",
        "availability": "Available",
        "metadata": {},
    }
    with pytest.raises(UnsupportedVersionError):
        evidence_schema.from_payload(payload)


def test_evidence_serialization_rejects_malformed_payload():
    payload = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "evidence_id": "e1",
        # missing required keys
    }
    with pytest.raises(SerializationFailureError):
        evidence_schema.from_payload(payload)


# --- Clarification: model -------------------------------------------------


def test_clarification_requires_request_fields():
    with pytest.raises(ValueError):
        Clarification(clarification_id="c1", request_text="", requested_at="t")


def test_clarification_starts_requested():
    clarification = Clarification(
        clarification_id="c1", request_text="what is x", requested_at="2026-01-01T00:00:00Z"
    )
    assert clarification.lifecycle_state is ClarificationState.REQUESTED
    assert clarification.response_text is None


def test_clarification_with_response_produces_new_instance():
    original = Clarification(
        clarification_id="c1", request_text="what is x", requested_at="2026-01-01T00:00:00Z"
    )
    responded = original.with_response("x is y", "2026-01-01T00:01:00Z")
    assert original.lifecycle_state is ClarificationState.REQUESTED
    assert responded.lifecycle_state is ClarificationState.RESPONDED
    assert responded.response_text == "x is y"
    assert responded is not original


def test_clarification_with_response_twice_raises():
    original = Clarification(
        clarification_id="c1", request_text="what is x", requested_at="2026-01-01T00:00:00Z"
    )
    responded = original.with_response("x is y", "2026-01-01T00:01:00Z")
    with pytest.raises(InvalidClarificationError):
        responded.with_response("x is z", "2026-01-01T00:02:00Z")


@pytest.mark.parametrize(
    "label",
    ["recommendation", "Recommendation", "PERSUASION", "approval", "Authorization", "decision"],
)
def test_clarification_rejects_forbidden_classification_tags(label):
    with pytest.raises(InvalidClarificationError):
        validate_classification_tag(label)


@pytest.mark.parametrize("label", ["factual", "template-scope", "evidence-conflict"])
def test_clarification_accepts_informational_tags(label):
    assert validate_classification_tag(label) == label


def test_clarification_with_tag_rejects_forbidden_label():
    original = Clarification(
        clarification_id="c1", request_text="what is x", requested_at="2026-01-01T00:00:00Z"
    )
    with pytest.raises(InvalidClarificationError):
        original.with_tag("Decision")


def test_clarification_with_tag_appends_permitted_label():
    original = Clarification(
        clarification_id="c1", request_text="what is x", requested_at="2026-01-01T00:00:00Z"
    )
    tagged = original.with_tag("factual")
    assert tagged.tags == ("factual",)
    assert original.tags == ()


# --- Clarification: controller --------------------------------------------


def test_clarification_controller_registers_request_and_response(session_id):
    controller = ClarificationController(session_id)
    controller.register_request("c1", "what is x", "2026-01-01T00:00:00Z")
    responded = controller.register_response("c1", "x is y", "2026-01-01T00:01:00Z")
    assert responded.lifecycle_state is ClarificationState.RESPONDED


def test_clarification_controller_rejects_duplicate_request_id(session_id):
    controller = ClarificationController(session_id)
    controller.register_request("c1", "what is x", "2026-01-01T00:00:00Z")
    with pytest.raises(DuplicateClarificationError):
        controller.register_request("c1", "what is y", "2026-01-01T00:00:01Z")


def test_clarification_controller_rejects_response_to_unknown_request(session_id):
    controller = ClarificationController(session_id)
    with pytest.raises(InvalidClarificationError):
        controller.register_response("does-not-exist", "answer", "2026-01-01T00:00:00Z")


def test_clarification_controller_rejects_double_response(session_id):
    controller = ClarificationController(session_id)
    controller.register_request("c1", "what is x", "2026-01-01T00:00:00Z")
    controller.register_response("c1", "x is y", "2026-01-01T00:01:00Z")
    with pytest.raises(InvalidClarificationError):
        controller.register_response("c1", "x is z", "2026-01-01T00:02:00Z")


def test_clarification_controller_history_preserves_request_order(session_id):
    controller = ClarificationController(session_id)
    controller.register_request("c2", "second", "2026-01-01T00:00:02Z")
    controller.register_request("c1", "first", "2026-01-01T00:00:01Z")
    history = controller.history()
    assert [c.clarification_id for c in history] == ["c2", "c1"]


def test_clarification_controller_history_is_immutable_tuple(session_id):
    controller = ClarificationController(session_id)
    controller.register_request("c1", "what is x", "2026-01-01T00:00:00Z")
    history = controller.history()
    assert isinstance(history, tuple)
    controller.register_request("c2", "what is y", "2026-01-01T00:00:01Z")
    assert len(history) == 1  # earlier snapshot unaffected


def test_clarification_controller_tag_rejects_recommendation_semantics(session_id):
    controller = ClarificationController(session_id)
    controller.register_request("c1", "what is x", "2026-01-01T00:00:00Z")
    with pytest.raises(InvalidClarificationError):
        controller.tag("c1", "recommendation")


def test_clarification_controller_has_no_recommend_persuade_or_transition_methods(session_id):
    controller = ClarificationController(session_id)
    forbidden_methods = ("recommend", "persuade", "prioritize", "decide", "transition")
    for name in forbidden_methods:
        assert not hasattr(controller, name)


def test_clarification_controller_scoped_to_valid_session_id():
    with pytest.raises(Exception):
        ClarificationController("not-a-session-id")


# --- Clarification: serialization ------------------------------------------


def test_clarification_serialization_round_trips(session_id):
    controller = ClarificationController(session_id)
    controller.register_request("c1", "what is x", "2026-01-01T00:00:00Z")
    responded = controller.register_response("c1", "x is y", "2026-01-01T00:01:00Z")
    payload = clarification_schema.to_payload(responded)
    assert payload["schema_version"] == CLARIFICATION_SCHEMA_VERSION
    restored = clarification_schema.from_payload(payload)
    assert restored == responded


def test_clarification_serialization_rejects_unknown_schema_version():
    payload = {
        "schema_version": "interactive-workflow-clarification/9.9",
        "clarification_id": "c1",
        "request_text": "what is x",
        "requested_at": "t",
        "lifecycle_state": "Requested",
        "response_text": None,
        "responded_at": None,
        "tags": [],
    }
    with pytest.raises(UnsupportedVersionError):
        clarification_schema.from_payload(payload)


# --- Audit: model -----------------------------------------------------------


def test_audit_event_requires_all_fields():
    with pytest.raises(ValueError):
        AuditEvent(event_id="", session_id="s", event_type="t", timestamp="ts")


def test_audit_event_payload_is_frozen():
    event = AuditEvent(
        event_id="ae1",
        session_id="s",
        event_type="evidence",
        timestamp="2026-01-01T00:00:00Z",
        payload={"k": "v"},
    )
    with pytest.raises(TypeError):
        event.payload["k"] = "other"  # type: ignore[index]


def test_audit_event_carries_no_authority_metadata_beyond_session_identity():
    field_names = set(AuditEvent.__dataclass_fields__)
    forbidden = {"authority", "approved", "confirmed", "publication_ref", "chgr_ref"}
    assert field_names.isdisjoint(forbidden)


# --- Audit: recorder ----------------------------------------------------------


def test_audit_recorder_appends_and_retrieves(session_id):
    recorder = AuditRecorder(session_id)
    event = AuditEvent(
        event_id="ae1",
        session_id=session_id,
        event_type="clarification",
        timestamp="2026-01-01T00:00:00Z",
    )
    recorder.append(event)
    assert recorder.get("ae1") is event


def test_audit_recorder_rejects_duplicate_event_id(session_id):
    recorder = AuditRecorder(session_id)
    event = AuditEvent(
        event_id="ae1",
        session_id=session_id,
        event_type="clarification",
        timestamp="2026-01-01T00:00:00Z",
    )
    recorder.append(event)
    with pytest.raises(DuplicateAuditEventError):
        recorder.append(event)


def test_audit_recorder_history_preserves_append_order(session_id):
    recorder = AuditRecorder(session_id)
    for i in range(5):
        recorder.append(
            AuditEvent(
                event_id=f"ae{i}",
                session_id=session_id,
                event_type="evidence",
                timestamp=f"2026-01-01T00:0{i}:00Z",
            )
        )
    history = recorder.history()
    assert [event.event_id for event in history] == [f"ae{i}" for i in range(5)]


def test_audit_recorder_history_filters_by_event_type(session_id):
    recorder = AuditRecorder(session_id)
    recorder.append(
        AuditEvent(event_id="ae1", session_id=session_id, event_type="clarification", timestamp="t1")
    )
    recorder.append(
        AuditEvent(event_id="ae2", session_id=session_id, event_type="evidence", timestamp="t2")
    )
    recorder.append(
        AuditEvent(event_id="ae3", session_id=session_id, event_type="clarification", timestamp="t3")
    )
    filtered = recorder.history(event_type="clarification")
    assert [event.event_id for event in filtered] == ["ae1", "ae3"]


def test_audit_recorder_history_is_immutable_snapshot(session_id):
    recorder = AuditRecorder(session_id)
    recorder.append(
        AuditEvent(event_id="ae1", session_id=session_id, event_type="evidence", timestamp="t1")
    )
    history = recorder.history()
    assert isinstance(history, tuple)
    recorder.append(
        AuditEvent(event_id="ae2", session_id=session_id, event_type="evidence", timestamp="t2")
    )
    assert len(history) == 1


def test_audit_recorder_has_no_mutate_delete_publish_or_notify_methods(session_id):
    recorder = AuditRecorder(session_id)
    forbidden_methods = ("delete", "remove", "clear", "mutate", "publish", "notify", "create_report", "create_chgr")
    for name in forbidden_methods:
        assert not hasattr(recorder, name)


def test_audit_recorder_scoped_to_valid_session_id():
    with pytest.raises(Exception):
        AuditRecorder("not-a-session-id")


def test_audit_recorder_get_returns_none_for_unknown_event(session_id):
    recorder = AuditRecorder(session_id)
    assert recorder.get("does-not-exist") is None


# --- Audit: serialization -----------------------------------------------------


def test_audit_serialization_round_trips(session_id):
    event = AuditEvent(
        event_id="ae1",
        session_id=session_id,
        event_type="evidence",
        timestamp="2026-01-01T00:00:00Z",
        payload={"k": "v"},
    )
    payload = audit_schema.to_payload(event)
    assert payload["schema_version"] == AUDIT_SCHEMA_VERSION
    restored = audit_schema.from_payload(payload)
    assert restored == event


def test_audit_serialization_rejects_unknown_schema_version():
    payload = {
        "schema_version": "interactive-workflow-audit/9.9",
        "event_id": "ae1",
        "session_id": "s",
        "event_type": "evidence",
        "timestamp": "t",
        "payload": {},
    }
    with pytest.raises(UnsupportedVersionError):
        audit_schema.from_payload(payload)


def test_audit_serialization_rejects_malformed_payload_with_audit_specific_error():
    payload = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "event_id": "ae1",
        # missing required keys
    }
    with pytest.raises(AuditSerializationFailureError):
        audit_schema.from_payload(payload)


# --- Integration boundary: passive coupling to session identity -----------


def test_all_three_coordinators_accept_the_same_valid_session_id(session_id):
    evidence = EvidenceCoordinator(session_id)
    clarification = ClarificationController(session_id)
    audit = AuditRecorder(session_id)
    assert evidence.session_id == clarification.session_id == audit.session_id == session_id
    assert validate_session_id(session_id) == session_id


def test_evidence_clarification_audit_modules_do_not_import_session_coordinator_or_transition_engine():
    import ast
    import inspect

    import pcae.interactive_workflow.audit.recorder as audit_recorder_module
    import pcae.interactive_workflow.clarification.controller as clarification_controller_module
    import pcae.interactive_workflow.evidence.coordinator as evidence_coordinator_module

    forbidden_imports = {"SessionCoordinator", "TransitionEngine"}
    for module in (
        evidence_coordinator_module,
        clarification_controller_module,
        audit_recorder_module,
    ):
        source = inspect.getsource(module)
        tree = ast.parse(source)
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported_names.update(alias.asname or alias.name for alias in node.names)
        assert imported_names.isdisjoint(forbidden_imports), (
            f"{module.__name__} imports a forbidden orchestration symbol: "
            f"{imported_names & forbidden_imports}"
        )


# --- Regression: Session Infrastructure (143K) and Transition Engine (143L) --


def test_regression_session_infrastructure_untouched():
    from pcae.interactive_workflow.models.session import SCHEMA_VERSION, Session, SessionState

    assert SCHEMA_VERSION == "interactive-workflow-session/0.1"
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
    from pcae.interactive_workflow.models.session import Session, SessionState
    from pcae.interactive_workflow.state_machine.engine import TransitionEngine

    engine = TransitionEngine()
    session = Session(
        session_id=generate_session_id(),
        owner_identity="human-1",
        template_ref="template-1",
        subject_ref="subject-1",
        session_state=SessionState.CREATED,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    result = engine.apply(session, SessionState.EVIDENCE_READY, sequence_number=1)
    assert result.session.session_state is SessionState.EVIDENCE_READY


def test_regression_runtime_state_unchanged():
    import subprocess

    result = subprocess.run(
        ["pcae", "runtime", "inspect", "--json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    output = result.stdout
    assert '"observe"' in output or "observe" in output
