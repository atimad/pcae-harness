"""Phase 143N unit tests: Preview and Confirmation infrastructure
(IWC-001 v1.1 §2, §10).

Covers Preview construction determinism, Preview Digest determinism and
tamper detection, Preview immutability, Preview validation (schema
version, missing/duplicate references, digest consistency), Preview
serialization; Confirmation request/response lifecycle, digest
verification, replay rejection, stale-preview rejection, duplicate
rejection, and Confirmation serialization; and regression checks
confirming Session Infrastructure (143K), Transition Engine (143L),
Evidence/Clarification/Audit (143M), and runtime state are unchanged. No
test in this module exercises session orchestration, publication, or
CHGR creation -- 143N's explicit no-go boundary.
"""

from __future__ import annotations

import pytest

from pcae.interactive_workflow.confirmation.controller import ConfirmationController
from pcae.interactive_workflow.confirmation.models import (
    CONFIRMATION_SCHEMA_VERSION,
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationResult,
)
from pcae.interactive_workflow.errors import (
    ConfirmationSerializationFailureError,
    DuplicateConfirmationError,
    InvalidConfirmationError,
    InvalidPreviewError,
    PreviewDigestMismatchError,
    ReplayDetectedError,
    SerializationFailureError,
    StalePreviewError,
    UnsupportedVersionError,
)
from pcae.interactive_workflow.preview.builder import PreviewBuilder
from pcae.interactive_workflow.preview.models import PREVIEW_SCHEMA_VERSION, Preview
from pcae.interactive_workflow.serialization import (
    confirmation_schema,
    preview_schema,
)
from pcae.interactive_workflow.session.identity import generate_session_id, validate_session_id

_TS = "2026-07-24T05:00:00+00:00"


@pytest.fixture()
def session_id() -> str:
    return generate_session_id()


@pytest.fixture()
def builder() -> PreviewBuilder:
    return PreviewBuilder()


# --- Preview: model --------------------------------------------------------


def test_preview_requires_all_fields(session_id):
    with pytest.raises(ValueError):
        Preview(
            preview_id="",
            session_id=session_id,
            preview_timestamp=_TS,
            transition_sequence_number=0,
        )
    with pytest.raises(ValueError):
        Preview(
            preview_id="preview-1",
            session_id=session_id,
            preview_timestamp="",
            transition_sequence_number=0,
        )


def test_preview_rejects_invalid_session_id():
    with pytest.raises(Exception):
        Preview(
            preview_id="preview-1",
            session_id="not-a-session-id",
            preview_timestamp=_TS,
            transition_sequence_number=0,
        )


def test_preview_rejects_negative_transition_sequence_number(session_id):
    with pytest.raises(ValueError):
        Preview(
            preview_id="preview-1",
            session_id=session_id,
            preview_timestamp=_TS,
            transition_sequence_number=-1,
        )


def test_preview_rejects_non_int_transition_sequence_number(session_id):
    with pytest.raises(ValueError):
        Preview(
            preview_id="preview-1",
            session_id=session_id,
            preview_timestamp=_TS,
            transition_sequence_number=True,
        )
    with pytest.raises(ValueError):
        Preview(
            preview_id="preview-1",
            session_id=session_id,
            preview_timestamp=_TS,
            transition_sequence_number="0",
        )


def test_preview_carries_no_authorization_approval_execution_publication_or_chgr_field(session_id):
    preview = Preview(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    forbidden_field_names = {
        "authorization",
        "authorized",
        "approval",
        "approved",
        "execution",
        "executable",
        "publication",
        "published",
        "chgr_id",
        "chgr_ref",
    }
    field_names = set(preview.__dataclass_fields__.keys())
    assert field_names.isdisjoint(forbidden_field_names)


def test_preview_is_immutable(session_id):
    preview = Preview(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    with pytest.raises(Exception):
        preview.preview_id = "preview-2"  # type: ignore[misc]


def test_preview_no_evaluate_recommend_confirm_or_publish_method_exists(session_id):
    preview = Preview(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    forbidden_method_names = {"evaluate", "recommend", "confirm", "publish", "authorize", "execute"}
    for name in forbidden_method_names:
        assert not hasattr(preview, name)


# --- Preview: builder --------------------------------------------------


def test_preview_builder_constructs_deterministic_preview(builder, session_id):
    preview, digest = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
        evidence_refs=["ev-2", "ev-1"],
        clarification_refs=["cl-1"],
        audit_refs=["au-1"],
        transition_summary="Created -> EvidenceReady",
        metadata={"note": "example"},
    )
    assert preview.evidence_refs == ("ev-1", "ev-2")
    assert digest == builder.compute_digest(preview)


def test_preview_digest_is_deterministic_independent_of_ref_registration_order(builder, session_id):
    preview_a, digest_a = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
        evidence_refs=["ev-1", "ev-2", "ev-3"],
        clarification_refs=["cl-2", "cl-1"],
        audit_refs=["au-1"],
    )
    preview_b, digest_b = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
        evidence_refs=["ev-3", "ev-1", "ev-2"],
        clarification_refs=["cl-1", "cl-2"],
        audit_refs=["au-1"],
    )
    assert preview_a == preview_b
    assert digest_a == digest_b


def test_preview_digest_changes_when_content_changes(builder, session_id):
    _, digest_a = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
        evidence_refs=["ev-1"],
    )
    _, digest_b = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
        evidence_refs=["ev-1", "ev-2"],
    )
    assert digest_a != digest_b


def test_preview_digest_stable_across_repeated_calls(builder, session_id):
    preview, digest = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=3,
        evidence_refs=["ev-1"],
    )
    recomputed = [builder.compute_digest(preview) for _ in range(5)]
    assert all(d == digest for d in recomputed)


def test_preview_builder_rejects_duplicate_evidence_refs(builder, session_id):
    with pytest.raises(InvalidPreviewError):
        builder.build(
            preview_id="preview-1",
            session_id=session_id,
            preview_timestamp=_TS,
            transition_sequence_number=0,
            evidence_refs=["ev-1", "ev-1"],
        )


def test_preview_builder_rejects_duplicate_clarification_refs(builder, session_id):
    with pytest.raises(InvalidPreviewError):
        builder.build(
            preview_id="preview-1",
            session_id=session_id,
            preview_timestamp=_TS,
            transition_sequence_number=0,
            clarification_refs=["cl-1", "cl-1"],
        )


def test_preview_builder_rejects_duplicate_audit_refs(builder, session_id):
    with pytest.raises(InvalidPreviewError):
        builder.build(
            preview_id="preview-1",
            session_id=session_id,
            preview_timestamp=_TS,
            transition_sequence_number=0,
            audit_refs=["au-1", "au-1"],
        )


def test_preview_builder_verify_digest_accepts_matching_digest(builder, session_id):
    preview, digest = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    builder.verify_digest(preview, digest)  # does not raise


def test_preview_builder_verify_digest_rejects_mismatched_digest(builder, session_id):
    preview, _ = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    with pytest.raises(PreviewDigestMismatchError):
        builder.verify_digest(preview, "0" * 64)


# --- Preview: validation -------------------------------------------------


def test_preview_validate_accepts_well_formed_preview(builder, session_id):
    preview, digest = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
        evidence_refs=["ev-1"],
    )
    builder.validate(preview, preview_digest=digest, required_evidence_refs=["ev-1"])


def test_preview_validate_rejects_unsupported_schema_version(builder, session_id):
    preview = Preview(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
        schema_version="interactive-workflow-preview/99.0",
    )
    with pytest.raises(InvalidPreviewError):
        builder.validate(preview)


def test_preview_validate_rejects_missing_required_evidence_reference(builder, session_id):
    preview, _ = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
        evidence_refs=["ev-1"],
    )
    with pytest.raises(InvalidPreviewError):
        builder.validate(preview, required_evidence_refs=["ev-1", "ev-2"])


def test_preview_validate_rejects_missing_required_clarification_reference(builder, session_id):
    preview, _ = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    with pytest.raises(InvalidPreviewError):
        builder.validate(preview, required_clarification_refs=["cl-1"])


def test_preview_validate_rejects_missing_required_audit_reference(builder, session_id):
    preview, _ = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    with pytest.raises(InvalidPreviewError):
        builder.validate(preview, required_audit_refs=["au-1"])


def test_preview_validate_rejects_digest_mismatch(builder, session_id):
    preview, _ = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    with pytest.raises(PreviewDigestMismatchError):
        builder.validate(preview, preview_digest="0" * 64)


def test_preview_validate_rejects_malformed_preview(builder):
    with pytest.raises(InvalidPreviewError):
        builder.validate(object())  # type: ignore[arg-type]


# --- Preview: stale detection --------------------------------------------


def test_detect_staleness_accepts_current_preview(builder, session_id):
    preview, digest = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=2,
    )
    builder.detect_staleness(
        preview, digest, current_session_id=session_id, current_transition_sequence_number=2
    )


def test_detect_staleness_rejects_advanced_transition_sequence(builder, session_id):
    preview, digest = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=2,
    )
    with pytest.raises(StalePreviewError):
        builder.detect_staleness(
            preview, digest, current_session_id=session_id, current_transition_sequence_number=3
        )


def test_detect_staleness_rejects_mismatched_session_identity(builder, session_id):
    preview, digest = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    other_session_id = generate_session_id()
    with pytest.raises(StalePreviewError):
        builder.detect_staleness(
            preview,
            digest,
            current_session_id=other_session_id,
            current_transition_sequence_number=0,
        )


def test_detect_staleness_rejects_tampered_digest(builder, session_id):
    preview, _ = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    with pytest.raises(PreviewDigestMismatchError):
        builder.detect_staleness(
            preview,
            "0" * 64,
            current_session_id=session_id,
            current_transition_sequence_number=0,
        )


def test_detect_staleness_performs_no_automatic_refresh(builder, session_id):
    preview, digest = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=0,
    )
    try:
        builder.detect_staleness(
            preview, digest, current_session_id=session_id, current_transition_sequence_number=1
        )
    except StalePreviewError:
        pass
    # The original preview object is unchanged -- no in-place refresh.
    assert preview.transition_sequence_number == 0


# --- Preview: serialization -----------------------------------------------


def test_preview_serialization_round_trips(builder, session_id):
    preview, _ = builder.build(
        preview_id="preview-1",
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=1,
        evidence_refs=["ev-1"],
        clarification_refs=["cl-1"],
        audit_refs=["au-1"],
        transition_summary="Created -> EvidenceReady",
        metadata={"k": "v"},
    )
    payload = preview_schema.to_payload(preview)
    restored = preview_schema.from_payload(payload)
    assert restored == preview


def test_preview_serialization_rejects_unsupported_version():
    with pytest.raises(UnsupportedVersionError):
        preview_schema.from_payload({"schema_version": "bogus/9.9"})


def test_preview_serialization_rejects_malformed_payload():
    with pytest.raises(SerializationFailureError):
        preview_schema.from_payload({"schema_version": PREVIEW_SCHEMA_VERSION})


# --- Confirmation: models --------------------------------------------------


def test_confirmation_request_requires_all_fields(session_id):
    with pytest.raises(ValueError):
        ConfirmationRequest(
            request_id="",
            session_id=session_id,
            preview_id="preview-1",
            preview_digest="d" * 64,
            created_at=_TS,
        )


def test_confirmation_request_rejects_invalid_session_id():
    with pytest.raises(Exception):
        ConfirmationRequest(
            request_id="req-1",
            session_id="not-a-session-id",
            preview_id="preview-1",
            preview_digest="d" * 64,
            created_at=_TS,
        )


def test_confirmation_response_requires_all_fields():
    with pytest.raises(ValueError):
        ConfirmationResponse(
            response_id="",
            request_id="req-1",
            confirmed_at=_TS,
            confirmation_result=ConfirmationResult.ACCEPTED,
            preview_digest="d" * 64,
        )
    with pytest.raises(ValueError):
        ConfirmationResponse(
            response_id="resp-1",
            request_id="req-1",
            confirmed_at=_TS,
            confirmation_result="Accepted",  # not an enum member
            preview_digest="d" * 64,
        )


def test_confirmation_models_carry_no_authority_token_publication_state_or_chgr_identifier(session_id):
    request = ConfirmationRequest(
        request_id="req-1",
        session_id=session_id,
        preview_id="preview-1",
        preview_digest="d" * 64,
        created_at=_TS,
    )
    response = ConfirmationResponse(
        response_id="resp-1",
        request_id="req-1",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest="d" * 64,
    )
    forbidden = {"authority_token", "publication_state", "chgr_id", "chgr_ref", "published"}
    assert forbidden.isdisjoint(request.__dataclass_fields__.keys())
    assert forbidden.isdisjoint(response.__dataclass_fields__.keys())


def test_confirmation_request_and_response_are_immutable(session_id):
    request = ConfirmationRequest(
        request_id="req-1",
        session_id=session_id,
        preview_id="preview-1",
        preview_digest="d" * 64,
        created_at=_TS,
    )
    response = ConfirmationResponse(
        response_id="resp-1",
        request_id="req-1",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest="d" * 64,
    )
    with pytest.raises(Exception):
        request.request_id = "req-2"  # type: ignore[misc]
    with pytest.raises(Exception):
        response.response_id = "resp-2"  # type: ignore[misc]


# --- Confirmation: helpers -------------------------------------------------


def _build_preview(builder, session_id, transition_sequence_number=0, preview_id="preview-1"):
    return builder.build(
        preview_id=preview_id,
        session_id=session_id,
        preview_timestamp=_TS,
        transition_sequence_number=transition_sequence_number,
        evidence_refs=["ev-1"],
    )


def _make_request(session_id, digest, request_id="req-1", preview_id="preview-1"):
    return ConfirmationRequest(
        request_id=request_id,
        session_id=session_id,
        preview_id=preview_id,
        preview_digest=digest,
        created_at=_TS,
    )


def _make_response(digest, request_id="req-1", response_id="resp-1"):
    return ConfirmationResponse(
        response_id=response_id,
        request_id=request_id,
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest=digest,
    )


# --- Confirmation: controller request lifecycle ----------------------------


def test_confirmation_controller_registers_request(builder, session_id):
    preview, digest = _build_preview(builder, session_id)
    controller = ConfirmationController(session_id)
    request = _make_request(session_id, digest)
    registered = controller.register_request(request)
    assert registered == request
    assert controller.get_request("req-1") == request
    assert controller.request_history() == (request,)


def test_confirmation_controller_rejects_duplicate_request_id(builder, session_id):
    preview, digest = _build_preview(builder, session_id)
    controller = ConfirmationController(session_id)
    controller.register_request(_make_request(session_id, digest))
    with pytest.raises(DuplicateConfirmationError):
        controller.register_request(_make_request(session_id, digest))


def test_confirmation_controller_rejects_request_scoped_to_different_session(builder, session_id):
    other_session_id = generate_session_id()
    preview, digest = _build_preview(builder, session_id)
    controller = ConfirmationController(other_session_id)
    with pytest.raises(InvalidConfirmationError):
        controller.register_request(_make_request(session_id, digest))


def test_confirmation_controller_get_unknown_request_raises(session_id):
    controller = ConfirmationController(session_id)
    with pytest.raises(InvalidConfirmationError):
        controller.get_request("nonexistent")


# --- Confirmation: controller response lifecycle ---------------------------


def test_confirmation_controller_accepts_matching_response(builder, session_id):
    preview, digest = _build_preview(builder, session_id)
    controller = ConfirmationController(session_id)
    controller.register_request(_make_request(session_id, digest))
    response = _make_response(digest)
    accepted = controller.register_response(
        "req-1", response, preview, current_transition_sequence_number=0
    )
    assert accepted == response
    assert controller.get_response("resp-1") == response
    assert controller.response_history() == (response,)


def test_confirmation_controller_rejects_response_for_unknown_request(builder, session_id):
    preview, digest = _build_preview(builder, session_id)
    controller = ConfirmationController(session_id)
    with pytest.raises(InvalidConfirmationError):
        controller.register_response(
            "missing-req", _make_response(digest), preview, current_transition_sequence_number=0
        )


def test_confirmation_controller_rejects_response_request_id_mismatch(builder, session_id):
    preview, digest = _build_preview(builder, session_id)
    controller = ConfirmationController(session_id)
    controller.register_request(_make_request(session_id, digest))
    mismatched = _make_response(digest, request_id="other-req")
    with pytest.raises(InvalidConfirmationError):
        controller.register_response(
            "req-1", mismatched, preview, current_transition_sequence_number=0
        )


def test_confirmation_controller_rejects_preview_id_mismatch(builder, session_id):
    preview, digest = _build_preview(builder, session_id)
    other_preview, _ = _build_preview(builder, session_id, preview_id="preview-other")
    controller = ConfirmationController(session_id)
    controller.register_request(_make_request(session_id, digest))
    with pytest.raises(InvalidConfirmationError):
        controller.register_response(
            "req-1", _make_response(digest), other_preview, current_transition_sequence_number=0
        )


def test_confirmation_controller_rejects_double_response_to_same_request(builder, session_id):
    preview, digest = _build_preview(builder, session_id)
    controller = ConfirmationController(session_id)
    controller.register_request(_make_request(session_id, digest))
    controller.register_response(
        "req-1", _make_response(digest), preview, current_transition_sequence_number=0
    )
    with pytest.raises(DuplicateConfirmationError):
        controller.register_response(
            "req-1",
            _make_response(digest, response_id="resp-2"),
            preview,
            current_transition_sequence_number=0,
        )


def test_confirmation_controller_rejects_duplicate_response_id_across_requests(builder, session_id):
    controller = ConfirmationController(session_id)

    preview_a, digest_a = _build_preview(builder, session_id, preview_id="preview-a")
    controller.register_request(_make_request(session_id, digest_a, request_id="req-a", preview_id="preview-a"))
    controller.register_response(
        "req-a",
        _make_response(digest_a, request_id="req-a", response_id="resp-shared"),
        preview_a,
        current_transition_sequence_number=0,
    )

    preview_b, digest_b = _build_preview(builder, session_id, transition_sequence_number=1, preview_id="preview-b")
    controller.register_request(_make_request(session_id, digest_b, request_id="req-b", preview_id="preview-b"))
    with pytest.raises(DuplicateConfirmationError):
        controller.register_response(
            "req-b",
            _make_response(digest_b, request_id="req-b", response_id="resp-shared"),
            preview_b,
            current_transition_sequence_number=1,
        )


def test_confirmation_controller_rejects_response_digest_mismatch(builder, session_id):
    preview, digest = _build_preview(builder, session_id)
    controller = ConfirmationController(session_id)
    controller.register_request(_make_request(session_id, digest))
    wrong_digest_response = ConfirmationResponse(
        response_id="resp-1",
        request_id="req-1",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest="f" * 64,
    )
    with pytest.raises(PreviewDigestMismatchError):
        controller.register_response(
            "req-1", wrong_digest_response, preview, current_transition_sequence_number=0
        )


def test_confirmation_controller_rejects_stale_preview(builder, session_id):
    preview, digest = _build_preview(builder, session_id, transition_sequence_number=0)
    controller = ConfirmationController(session_id)
    controller.register_request(_make_request(session_id, digest))
    with pytest.raises(StalePreviewError):
        controller.register_response(
            "req-1", _make_response(digest), preview, current_transition_sequence_number=5
        )


def test_confirmation_controller_rejects_replayed_preview_digest_across_requests(builder, session_id):
    controller = ConfirmationController(session_id)
    preview_a, digest = _build_preview(builder, session_id, preview_id="preview-a")

    controller.register_request(_make_request(session_id, digest, request_id="req-a", preview_id="preview-a"))
    controller.register_response(
        "req-a",
        _make_response(digest, request_id="req-a", response_id="resp-a"),
        preview_a,
        current_transition_sequence_number=0,
    )

    # A second request happens to bind to the exact same digest (e.g. a
    # forged replay attempt reusing old confirmation evidence).
    preview_a_dup, digest_dup = _build_preview(builder, session_id, preview_id="preview-a")
    assert digest_dup == digest
    controller.register_request(_make_request(session_id, digest, request_id="req-b", preview_id="preview-a"))
    with pytest.raises(ReplayDetectedError):
        controller.register_response(
            "req-b",
            _make_response(digest, request_id="req-b", response_id="resp-b"),
            preview_a_dup,
            current_transition_sequence_number=0,
        )


def test_confirmation_controller_get_unknown_response_raises(session_id):
    controller = ConfirmationController(session_id)
    with pytest.raises(InvalidConfirmationError):
        controller.get_response("nonexistent")


def test_confirmation_controller_deterministic_retrieval_preserves_order(builder, session_id):
    controller = ConfirmationController(session_id)
    previews = []
    for i in range(3):
        preview, digest = _build_preview(
            builder, session_id, transition_sequence_number=i, preview_id=f"preview-{i}"
        )
        previews.append((preview, digest))
        controller.register_request(
            _make_request(session_id, digest, request_id=f"req-{i}", preview_id=f"preview-{i}")
        )

    assert [r.request_id for r in controller.request_history()] == ["req-0", "req-1", "req-2"]

    for i, (preview, digest) in enumerate(previews):
        controller.register_response(
            f"req-{i}",
            _make_response(digest, request_id=f"req-{i}", response_id=f"resp-{i}"),
            preview,
            current_transition_sequence_number=i,
        )

    assert [r.response_id for r in controller.response_history()] == ["resp-0", "resp-1", "resp-2"]


def test_confirmation_controller_no_publish_transition_or_chgr_method_exists(session_id):
    controller = ConfirmationController(session_id)
    forbidden_method_names = {
        "publish",
        "transition_session",
        "create_chgr",
        "invoke_session_coordinator",
        "authorize",
    }
    for name in forbidden_method_names:
        assert not hasattr(controller, name)


# --- Confirmation: serialization -------------------------------------------


def test_confirmation_request_serialization_round_trips(session_id):
    request = ConfirmationRequest(
        request_id="req-1",
        session_id=session_id,
        preview_id="preview-1",
        preview_digest="d" * 64,
        created_at=_TS,
    )
    payload = confirmation_schema.request_to_payload(request)
    restored = confirmation_schema.request_from_payload(payload)
    assert restored == request


def test_confirmation_response_serialization_round_trips():
    response = ConfirmationResponse(
        response_id="resp-1",
        request_id="req-1",
        confirmed_at=_TS,
        confirmation_result=ConfirmationResult.ACCEPTED,
        preview_digest="d" * 64,
        metadata={"k": "v"},
    )
    payload = confirmation_schema.response_to_payload(response)
    restored = confirmation_schema.response_from_payload(payload)
    assert restored == response


def test_confirmation_request_serialization_rejects_unsupported_version():
    with pytest.raises(UnsupportedVersionError):
        confirmation_schema.request_from_payload({"schema_version": "bogus/9.9"})


def test_confirmation_response_serialization_rejects_unsupported_version():
    with pytest.raises(UnsupportedVersionError):
        confirmation_schema.response_from_payload({"schema_version": "bogus/9.9"})


def test_confirmation_request_serialization_rejects_malformed_payload():
    with pytest.raises(ConfirmationSerializationFailureError):
        confirmation_schema.request_from_payload({"schema_version": CONFIRMATION_SCHEMA_VERSION})


def test_confirmation_response_serialization_rejects_malformed_payload():
    with pytest.raises(ConfirmationSerializationFailureError):
        confirmation_schema.response_from_payload({"schema_version": CONFIRMATION_SCHEMA_VERSION})


# --- Integration boundary: passive coupling to session identity -----------


def test_preview_builder_and_confirmation_controller_accept_the_same_valid_session_id(builder, session_id):
    preview, digest = _build_preview(builder, session_id)
    controller = ConfirmationController(session_id)
    assert preview.session_id == controller.session_id == session_id
    assert validate_session_id(session_id) == session_id


def test_confirmation_controller_module_does_not_import_session_coordinator_or_transition_engine():
    import ast
    import inspect

    import pcae.interactive_workflow.confirmation.controller as confirmation_controller_module
    import pcae.interactive_workflow.preview.builder as preview_builder_module

    forbidden_imports = {"SessionCoordinator", "TransitionEngine"}
    for module in (confirmation_controller_module, preview_builder_module):
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


# --- Regression: Session Infrastructure (143K), Transition Engine (143L), --
# --- Evidence/Clarification/Audit (143M) -----------------------------------


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
        created_at=_TS,
        updated_at=_TS,
    )
    result = engine.apply(session, SessionState.EVIDENCE_READY, sequence_number=1)
    assert result.session.session_state is SessionState.EVIDENCE_READY


def test_regression_evidence_coordinator_untouched(session_id):
    from pcae.interactive_workflow.evidence.coordinator import EvidenceCoordinator
    from pcae.interactive_workflow.evidence.models import EvidenceAvailability, EvidenceItem

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
    from pcae.interactive_workflow.clarification.controller import ClarificationController

    controller = ClarificationController(session_id)
    clarification = controller.register_request("cl-1", "What does this mean?", _TS)
    assert clarification.clarification_id == "cl-1"
    with pytest.raises(Exception):
        controller.tag("cl-1", "recommendation")


def test_regression_audit_recorder_untouched(session_id):
    from pcae.interactive_workflow.audit.models import AuditEvent
    from pcae.interactive_workflow.audit.recorder import AuditRecorder

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
