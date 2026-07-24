"""Canonical Session domain model (IWC-001 v1.1 §4, Phase 143J §4/§6.1).

Translates IWC-001 v1.1's ten-state session model and identity/ownership/
binding rules into a concrete, immutable (frozen dataclass) type. Nothing
here performs I/O. Construction checks are limited to structurally-required-
field presence (``ValueError`` on a structurally impossible construction);
semantic validation (known-state checks, terminal-state integrity, version
compatibility) lives in ``pcae.interactive_workflow.validation``.

Evidence snapshots, confirmation evidence, clarification logs, and Preview
Digest content are explicitly excluded from this model -- Phase 143K's
governing scope excludes evidence orchestration, clarification, preview,
and confirmation (deferred to 143M/143N). This model carries only identity,
ownership, template/subject binding, Decision Capture fields, and session
state -- the slice of IWC-001 §4 in scope for 143K.

``template_version``, ``options_presented``, and
``decision_maker_evidence_kind`` were added by Phase 144F (IWC-001 v1.2
§26, IWC-REQ-185) so that ``PublicationHandoff.build_package`` can copy
the bound Decision Template's version, the full closed option-id set
actually presented, and the decision-maker's identity-evidence kind
verbatim into the widened ``PublicationReadinessPackage`` -- additive,
defaulted fields; no existing field is removed, renamed, or
reinterpreted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Optional, Tuple


SCHEMA_VERSION = "interactive-workflow-session/0.1"


class SessionState(str, Enum):
    """The ten canonical session states (IWC-001 v1.1 §4.4, IWC-REQ-040).

    No additional production states, no hidden transitional states, no
    persistence-specific states (IWC-REQ-042). This enum is the single
    authoritative enumeration -- every other module in this package
    references these members rather than re-declaring state names.
    """

    CREATED = "Created"
    EVIDENCE_READY = "EvidenceReady"
    AWAITING_DECISION = "AwaitingDecision"
    AWAITING_CLARIFICATION = "AwaitingClarification"
    DECISION_SELECTED = "DecisionSelected"
    AWAITING_CONFIRMATION = "AwaitingConfirmation"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    EXPIRED = "Expired"
    ABANDONED = "Abandoned"


TERMINAL_STATES: frozenset[SessionState] = frozenset(
    {
        SessionState.CONFIRMED,
        SessionState.CANCELLED,
        SessionState.EXPIRED,
        SessionState.ABANDONED,
    }
)
"""Terminal states admit no exit (IWC-001 v1.1 §4.4 rule, IWC-REQ-042)."""


def _frozen_metadata(value: Optional[Mapping[str, object]]) -> Mapping[str, object]:
    if value is None:
        return MappingProxyType({})
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class Session:
    """A single Interactive Workflow session record.

    Fields mirror Phase 143J §4 (Session Coordinator responsibility
    matrix) and §6.1 (persisted-field table), restricted to the identity/
    ownership/binding/Decision-Capture slice in scope for 143K.
    """

    session_id: str
    owner_identity: str
    template_ref: str
    subject_ref: str
    session_state: SessionState
    schema_version: str = SCHEMA_VERSION
    created_at: str = ""
    updated_at: str = ""
    human_selection_id: Optional[str] = None
    human_rationale_text: Optional[str] = None
    human_conditions_text: Optional[str] = None
    disclosure_acknowledgements: Tuple[str, ...] = field(default_factory=tuple)
    template_version: str = ""
    options_presented: Tuple[str, ...] = field(default_factory=tuple)
    decision_maker_evidence_kind: str = "typed_confirmation_only"
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("Session.session_id must be non-empty.")
        if not self.owner_identity:
            raise ValueError("Session.owner_identity must be non-empty.")
        if not self.template_ref:
            raise ValueError("Session.template_ref must be non-empty.")
        if not self.subject_ref:
            raise ValueError("Session.subject_ref must be non-empty.")
        if not isinstance(self.session_state, SessionState):
            raise ValueError(
                f"Session.session_state must be a SessionState member, got {self.session_state!r}."
            )
        if not self.created_at:
            raise ValueError("Session.created_at must be non-empty.")
        if not self.updated_at:
            raise ValueError("Session.updated_at must be non-empty.")
        object.__setattr__(
            self, "disclosure_acknowledgements", tuple(self.disclosure_acknowledgements)
        )
        if self.decision_maker_evidence_kind not in (
            "typed_confirmation_only",
            "os_authenticated_user",
        ):
            raise ValueError(
                "Session.decision_maker_evidence_kind must be 'typed_confirmation_only' "
                f"or 'os_authenticated_user', got {self.decision_maker_evidence_kind!r}."
            )
        object.__setattr__(self, "options_presented", tuple(self.options_presented))
        object.__setattr__(self, "metadata", _frozen_metadata(self.metadata))

    def is_terminal(self) -> bool:
        return self.session_state in TERMINAL_STATES

    def with_state(self, new_state: SessionState, updated_at: str) -> "Session":
        """Return a new ``Session`` with ``session_state`` replaced.

        Structural helper only -- it performs no transition-legality
        check. Transition legality is the State Machine's sole
        responsibility (``pcae.interactive_workflow.state_machine``).
        """

        return Session(
            session_id=self.session_id,
            owner_identity=self.owner_identity,
            template_ref=self.template_ref,
            subject_ref=self.subject_ref,
            session_state=new_state,
            schema_version=self.schema_version,
            created_at=self.created_at,
            updated_at=updated_at,
            human_selection_id=self.human_selection_id,
            human_rationale_text=self.human_rationale_text,
            human_conditions_text=self.human_conditions_text,
            disclosure_acknowledgements=self.disclosure_acknowledgements,
            template_version=self.template_version,
            options_presented=self.options_presented,
            decision_maker_evidence_kind=self.decision_maker_evidence_kind,
            metadata=self.metadata,
        )


__all__ = [
    "SCHEMA_VERSION",
    "Session",
    "SessionState",
    "TERMINAL_STATES",
]
