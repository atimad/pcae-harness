"""Immutable Publication Readiness Package model (IWC-001 v1.1 §2, §11.4,
§18.4, IWC-REQ-171; Phase 143O).

A ``PublicationReadinessPackage`` carries only structural readiness
references -- to the session, the transition state it was assembled at,
and the evidence/clarification/audit/preview/confirmation artifacts a
future, separately governed Publication implementation would need as its
input (IWC-001 v1.1 §11.4: "A future implementation that builds
Publication takes, as its sole input, a session in state Confirmed: its
bound template reference, its captured decision content, its exact
Preview and Preview Digest, and its Confirmation evidence"). This model
deliberately carries no publication-state field, no publication-result
field, no CHGR identifier field, and no authority-token field -- IWC-REQ-
171 leaves Publication Handoff *execution* ownership an explicitly open
question for a future, separately governed phase, and a field that
recorded a publication outcome or authority claim would itself be
evidence of executing (or claiming to authorize) that undecided
responsibility. There is nothing to omit at serialization time because
none of those fields exist on this class at all (this phase's governing
prompt, "Publication Readiness Package": "Do not include: publication
state, publication result, CHGR identifier, authority tokens").

Field values are identifiers/references (strings, an int sequence number,
a ``SessionState`` member) rather than full payload copies of the cited
artifacts, per this phase's governing prompt's own "Include references
to" wording -- mirroring how ``Preview`` itself stores only
``evidence_refs``/``clarification_refs``/``audit_refs`` (Phase 143N)
rather than copying the underlying Evidence/Clarification/Audit content
inline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Optional

from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.session.identity import validate_session_id

PUBLICATION_HANDOFF_SCHEMA_VERSION = "interactive-workflow-publication-handoff/0.1"


def _frozen_metadata(value: Optional[Mapping[str, object]]) -> Mapping[str, object]:
    if value is None:
        return MappingProxyType({})
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class PublicationReadinessPackage:
    """A single, immutable snapshot of publication-readiness structural
    references for one Decision Session.

    Every field below is a reference (an identifier or a small scalar),
    never a payload copy, never a publication outcome, and never an
    authority claim. ``PublicationHandoff.build_package``
    (``pcae.interactive_workflow.publication_handoff.handoff``) is the
    sole production constructor of well-formed instances of this class;
    this ``__post_init__`` enforces only structural field presence, the
    same discipline every other frozen model in this package follows
    (e.g. ``Preview.__post_init__``, Phase 143N).
    """

    package_id: str
    session_id: str
    session_state: SessionState
    transition_sequence_number: int
    evidence_refs: tuple
    clarification_refs: tuple
    audit_refs: tuple
    preview_id: str
    preview_digest: str
    confirmation_request_id: str
    confirmation_response_id: str
    built_at: str
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    schema_version: str = PUBLICATION_HANDOFF_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.package_id:
            raise ValueError("PublicationReadinessPackage.package_id must be non-empty.")
        validate_session_id(self.session_id)
        if not isinstance(self.session_state, SessionState):
            raise ValueError(
                "PublicationReadinessPackage.session_state must be a SessionState "
                f"member, got {self.session_state!r}."
            )
        if isinstance(self.transition_sequence_number, bool) or not isinstance(
            self.transition_sequence_number, int
        ):
            raise ValueError(
                "PublicationReadinessPackage.transition_sequence_number must be an "
                f"int, got {self.transition_sequence_number!r}."
            )
        if self.transition_sequence_number < 0:
            raise ValueError(
                "PublicationReadinessPackage.transition_sequence_number must be "
                f"non-negative, got {self.transition_sequence_number!r}."
            )
        if not self.preview_id:
            raise ValueError("PublicationReadinessPackage.preview_id must be non-empty.")
        if not self.preview_digest:
            raise ValueError("PublicationReadinessPackage.preview_digest must be non-empty.")
        if not self.confirmation_request_id:
            raise ValueError(
                "PublicationReadinessPackage.confirmation_request_id must be non-empty."
            )
        if not self.confirmation_response_id:
            raise ValueError(
                "PublicationReadinessPackage.confirmation_response_id must be non-empty."
            )
        if not self.built_at:
            raise ValueError("PublicationReadinessPackage.built_at must be non-empty.")
        if not self.schema_version:
            raise ValueError("PublicationReadinessPackage.schema_version must be non-empty.")
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        object.__setattr__(self, "clarification_refs", tuple(self.clarification_refs))
        object.__setattr__(self, "audit_refs", tuple(self.audit_refs))
        object.__setattr__(self, "metadata", _frozen_metadata(self.metadata))


__all__ = [
    "PUBLICATION_HANDOFF_SCHEMA_VERSION",
    "PublicationReadinessPackage",
]
