"""Publication Handoff interface (IWC-001 v1.1 §2, §11.4, §18.4,
IWC-REQ-171; Phase 143O).

The sole production owner of Publication Readiness Package construction,
package completeness validation, publication-readiness exposure, and
providing an immutable handoff artifact (this phase's governing prompt,
"Architectural Ownership": "Publication Handoff shall become the sole
owner of: publication readiness package, publication interface,
publication boundary validation"). No other production component in this
phase constructs a ``PublicationReadinessPackage``.

This class does not, and per IWC-REQ-171 and this phase's own explicit
No-Go list never will on this class, publish, notify, create a CHGR, or
invoke a PCAE lifecycle command. Those methods do not exist here -- there
is nothing to disable. IWC-001 v1.1 §18.4 and IWC-REQ-171 leave
Publication Handoff *execution* ownership an explicitly open question for
a future, separately governed phase; this class implements only the
readiness *package* and its *interface*, never execution, exactly the
distinction this phase's own governing prompt draws between "Publication
Handoff interface" (in scope) and "publication" (out of scope, explicit
No-Go item).

``build_package`` requires an already-accepted ``ConfirmationResponse``
(i.e. one ``ConfirmationController.register_response`` has already
returned successfully) as structural proof that staleness, replay, and
digest-consistency checks already ran and passed at Confirmation
Controller's own hands (Phase 143N) -- this class never re-implements or
re-runs those checks itself, matching "Dependency Enforcement": "No
component shall call another component laterally."
"""

from __future__ import annotations

from typing import Any, Dict, Iterable

from pcae.interactive_workflow.confirmation.models import ConfirmationRequest, ConfirmationResponse
from pcae.interactive_workflow.errors import PublicationHandoffIncompleteError
from pcae.interactive_workflow.models.session import Session, SessionState
from pcae.interactive_workflow.orchestration.models import OrchestrationState
from pcae.interactive_workflow.preview.models import Preview
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage


class PublicationHandoff:
    """Constructs, validates, and exposes readiness for an immutable
    ``PublicationReadinessPackage``. Stateless: every method's output is
    a pure function of its arguments, mirroring ``PreviewBuilder``'s own
    statelessness discipline (Phase 143N)."""

    def build_package(
        self,
        package_id: str,
        session: Session,
        orchestration_state: OrchestrationState,
        transition_sequence_number: int,
        evidence_refs: Iterable[str],
        clarification_refs: Iterable[str],
        audit_refs: Iterable[str],
        preview: Preview,
        confirmation_request: ConfirmationRequest,
        confirmation_response: ConfirmationResponse,
        built_at: str,
    ) -> PublicationReadinessPackage:
        """Construct an immutable ``PublicationReadinessPackage``.

        Raises ``PublicationHandoffIncompleteError`` (fail closed,
        constructs nothing) unless every one of the following holds:

        - ``session.session_state`` is ``SessionState.CONFIRMED``
          (IWC-001 v1.1 §11.4: Publication's sole input is "a session in
          state Confirmed");
        - ``orchestration_state.is_complete()`` -- every one of this
          phase's eight orchestration stages has already run;
        - ``preview.session_id``, ``confirmation_request.session_id``,
          and ``session.session_id`` all agree;
        - ``confirmation_response.request_id`` matches
          ``confirmation_request.request_id`` and
          ``confirmation_response.preview_digest`` matches
          ``confirmation_request.preview_digest`` (the same exact-content
          binding ``ConfirmationController.register_response`` already
          enforced at acceptance time, restated here as a precondition on
          the values this method was handed, never recomputed).

        Never publishes, notifies, creates a CHGR, or invokes a lifecycle
        command -- there is no code path in this method capable of any
        of the four.
        """

        if session.session_state is not SessionState.CONFIRMED:
            raise PublicationHandoffIncompleteError(
                f"Session {session.session_id!r} is in state "
                f"{session.session_state!r}, not Confirmed; a Publication "
                "Readiness Package's sole permitted input session state is "
                "Confirmed (IWC-001 v1.1 §11.4)."
            )
        if not orchestration_state.is_complete():
            raise PublicationHandoffIncompleteError(
                f"OrchestrationState for session {orchestration_state.session_id!r} "
                f"is incomplete (next stage: {orchestration_state.next_stage!r}); a "
                "Publication Readiness Package cannot be built until all eight "
                "orchestration stages have completed."
            )
        if orchestration_state.session_id != session.session_id:
            raise PublicationHandoffIncompleteError(
                f"OrchestrationState session {orchestration_state.session_id!r} does "
                f"not match Session {session.session_id!r}."
            )
        if preview.session_id != session.session_id:
            raise PublicationHandoffIncompleteError(
                f"Preview {preview.preview_id!r} is scoped to session "
                f"{preview.session_id!r}, not {session.session_id!r}."
            )
        if confirmation_request.session_id != session.session_id:
            raise PublicationHandoffIncompleteError(
                f"ConfirmationRequest {confirmation_request.request_id!r} is scoped "
                f"to session {confirmation_request.session_id!r}, not "
                f"{session.session_id!r}."
            )
        if confirmation_response.request_id != confirmation_request.request_id:
            raise PublicationHandoffIncompleteError(
                f"ConfirmationResponse {confirmation_response.response_id!r} answers "
                f"request {confirmation_response.request_id!r}, not the supplied "
                f"request {confirmation_request.request_id!r}."
            )
        if confirmation_response.preview_digest != confirmation_request.preview_digest:
            raise PublicationHandoffIncompleteError(
                f"ConfirmationResponse {confirmation_response.response_id!r} digest "
                f"{confirmation_response.preview_digest!r} does not match "
                f"ConfirmationRequest {confirmation_request.request_id!r} digest "
                f"{confirmation_request.preview_digest!r}."
            )
        if confirmation_request.preview_id != preview.preview_id:
            raise PublicationHandoffIncompleteError(
                f"ConfirmationRequest {confirmation_request.request_id!r} is bound to "
                f"preview {confirmation_request.preview_id!r}, not the supplied "
                f"preview {preview.preview_id!r}."
            )
        if not session.human_selection_id:
            raise PublicationHandoffIncompleteError(
                f"Session {session.session_id!r} has no human_selection_id; a "
                "Confirmed session's Publication Readiness Package cannot carry a "
                "verbatim selected option identifier it never captured (IWC-REQ-185)."
            )

        # IWC-REQ-185 (Phase 144F): every added field below is copied
        # unmodified from the Session/Preview/ConfirmationResponse this
        # method already received as arguments -- never re-derived,
        # re-rendered, reconstructed, or independently fetched.
        decision_maker_identity_evidence = {
            "evidence_kind": session.decision_maker_evidence_kind,
            "identifier": session.owner_identity,
            "captured_at": confirmation_response.confirmed_at,
        }
        package = PublicationReadinessPackage(
            package_id=package_id,
            session_id=session.session_id,
            session_state=session.session_state,
            transition_sequence_number=transition_sequence_number,
            evidence_refs=tuple(evidence_refs),
            clarification_refs=tuple(clarification_refs),
            audit_refs=tuple(audit_refs),
            preview_id=preview.preview_id,
            preview_digest=confirmation_request.preview_digest,
            confirmation_request_id=confirmation_request.request_id,
            confirmation_response_id=confirmation_response.response_id,
            built_at=built_at,
            decision_subject=session.subject_ref,
            template_id=session.template_ref,
            template_version=session.template_version,
            selected_option_id=session.human_selection_id,
            rationale_text=session.human_rationale_text,
            conditions_text=session.human_conditions_text,
            options_presented=tuple(session.options_presented),
            decision_maker_identity_evidence=decision_maker_identity_evidence,
            preview_rendered_content=preview.rendered_content,
            confirmation_statement=confirmation_response.confirmation_result.value,
            confirmation_timestamp=confirmation_response.confirmed_at,
        )
        self.validate_completeness(package)
        return package

    def validate_completeness(self, package: PublicationReadinessPackage) -> None:
        """Raise ``PublicationHandoffIncompleteError`` unless every
        reference field on ``package`` is present and well-formed.

        Fails closed on the first missing reference found; never repairs
        or defaults a missing field.
        """

        required_scalars = {
            "package_id": package.package_id,
            "session_id": package.session_id,
            "preview_id": package.preview_id,
            "preview_digest": package.preview_digest,
            "confirmation_request_id": package.confirmation_request_id,
            "confirmation_response_id": package.confirmation_response_id,
            "built_at": package.built_at,
            # IWC-REQ-185 (Phase 144F): required verbatim provenance
            # content. rationale_text/conditions_text are deliberately
            # excluded -- IWC-REQ-185 marks them "where supplied", never
            # required.
            "decision_subject": package.decision_subject,
            "template_id": package.template_id,
            "template_version": package.template_version,
            "selected_option_id": package.selected_option_id,
            "preview_rendered_content": package.preview_rendered_content,
            "confirmation_statement": package.confirmation_statement,
            "confirmation_timestamp": package.confirmation_timestamp,
        }
        missing = [name for name, value in required_scalars.items() if not value]
        if not package.options_presented:
            missing.append("options_presented")
        if not package.decision_maker_identity_evidence:
            missing.append("decision_maker_identity_evidence")
        missing.sort()
        if missing:
            raise PublicationHandoffIncompleteError(
                f"PublicationReadinessPackage {package.package_id!r} is missing "
                f"required reference field(s): {missing!r}."
            )
        if not isinstance(package.session_state, SessionState):
            raise PublicationHandoffIncompleteError(
                f"PublicationReadinessPackage {package.package_id!r}.session_state "
                f"must be a SessionState member, got {package.session_state!r}."
            )
        if package.session_state is not SessionState.CONFIRMED:
            raise PublicationHandoffIncompleteError(
                f"PublicationReadinessPackage {package.package_id!r}.session_state "
                f"{package.session_state!r} is not Confirmed."
            )

    def is_ready(self, package: PublicationReadinessPackage) -> bool:
        """Return whether ``package`` is structurally ready for a
        future, separately authorized Publication implementation to
        consume. Never raises -- reports readiness only, and never
        itself performs, triggers, or schedules publication."""

        try:
            self.validate_completeness(package)
        except PublicationHandoffIncompleteError:
            return False
        return True

    def serialize(self, package: PublicationReadinessPackage) -> Dict[str, Any]:
        """Serialize ``package`` deterministically.

        Delegates to
        ``pcae.interactive_workflow.serialization.publication_handoff_schema``
        -- this method exists for interface symmetry with
        ``deserialize`` and to avoid callers importing the serialization
        submodule directly, mirroring no equivalent precedent forced by
        143K-143N (those phases expose serialization only via the
        top-level ``serialization`` package), so this convenience method
        is this phase's own addition, documented as a judgment call in
        this phase's report.
        """

        from pcae.interactive_workflow.serialization import publication_handoff_schema

        return publication_handoff_schema.to_payload(package)

    def deserialize(self, payload: Dict[str, Any]) -> PublicationReadinessPackage:
        """Deserialize ``payload`` into a ``PublicationReadinessPackage``.
        See ``serialize`` for why this delegates to the sibling
        serialization module rather than reimplementing the logic here.
        """

        from pcae.interactive_workflow.serialization import publication_handoff_schema

        return publication_handoff_schema.from_payload(payload)


__all__ = ["PublicationHandoff"]
