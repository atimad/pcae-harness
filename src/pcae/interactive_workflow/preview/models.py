"""Immutable Preview domain model (IWC-001 v1.1 §2, §10.1, Phase 143N).

A ``Preview`` is the exact, verbatim rendering of the content Confirmation
would cause to be published, generated deterministically from Decision
Capture's current state (IWC-001 v1.1 §2 "Preview"; IWC-REQ-010). This
module deliberately carries no authorization field, no approval field, no
execution-capability field, no publication field, and no CHGR reference --
a Preview remains informational only, never itself evidence of a
governance act (IWC-001 v1.1 §1, §7).

``transition_sequence_number`` is the snapshot input Preview Builder's
stale-preview detection (``pcae.interactive_workflow.preview.builder``)
compares against a session's current transition sequence number (Phase
143L's ``TransitionMetadata.transition_sequence_number``) to determine
whether the underlying session state has moved on since this Preview was
built (IWC-001 v1.1 §10.2, §12 "stale evidence"/"stale preview").

Reference collections (``evidence_refs``, ``clarification_refs``,
``audit_refs``) are stored pre-canonicalized (sorted, deduplicated) by the
Preview Builder before construction, mirroring
``EvidenceCoordinator.ordered_view``'s content-deterministic-ordering
discipline (Phase 143M) -- so two independent builds over the same content
in different assembly order produce byte-identical Preview content, and
therefore an identical Preview Digest (IWC-REQ-079, IWC-REQ-020).

``rendered_content`` was added by Phase 144F (IWC-001 v1.2 §26,
IWC-REQ-188): the exact, literal rendered Preview text the human actually
reviewed, captured exactly once at Preview-generation time, immutable and
included in Preview Digest computation (``preview.builder._canonical_
payload``) so tampering with it after the fact is detected exactly like
tampering with any other Preview field. Distinct from
``transition_summary``, which remains purely informational.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Optional, Tuple

from pcae.interactive_workflow.session.identity import validate_session_id

PREVIEW_SCHEMA_VERSION = "interactive-workflow-preview/0.1"


def _frozen_metadata(value: Optional[Mapping[str, object]]) -> Mapping[str, object]:
    if value is None:
        return MappingProxyType({})
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class Preview:
    """A single, immutable Preview snapshot.

    Fields mirror IWC-001 v1.1 §2/§10.1's Preview discipline: an
    identifier, the session it was rendered for, the moment it was
    rendered, the transition sequence number it was rendered against
    (the stale-preview detection input), the evidence/clarification/audit
    references it cites, an informational transition summary, and a
    metadata container for future-compatible extension -- never an
    authorization, approval, execution-capability, publication, or CHGR
    field.
    """

    preview_id: str
    session_id: str
    preview_timestamp: str
    transition_sequence_number: int
    evidence_refs: Tuple[str, ...] = ()
    clarification_refs: Tuple[str, ...] = ()
    audit_refs: Tuple[str, ...] = ()
    transition_summary: str = ""
    rendered_content: str = ""
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    schema_version: str = PREVIEW_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.preview_id:
            raise ValueError("Preview.preview_id must be non-empty.")
        validate_session_id(self.session_id)
        if not self.preview_timestamp:
            raise ValueError("Preview.preview_timestamp must be non-empty.")
        if isinstance(self.transition_sequence_number, bool) or not isinstance(
            self.transition_sequence_number, int
        ):
            raise ValueError(
                "Preview.transition_sequence_number must be an int, "
                f"got {self.transition_sequence_number!r}."
            )
        if self.transition_sequence_number < 0:
            raise ValueError(
                "Preview.transition_sequence_number must be non-negative, "
                f"got {self.transition_sequence_number!r}."
            )
        if not isinstance(self.transition_summary, str):
            raise ValueError(
                f"Preview.transition_summary must be a string, got {self.transition_summary!r}."
            )
        if not isinstance(self.rendered_content, str):
            raise ValueError(
                f"Preview.rendered_content must be a string, got {self.rendered_content!r}."
            )
        if not self.schema_version:
            raise ValueError("Preview.schema_version must be non-empty.")
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        object.__setattr__(self, "clarification_refs", tuple(self.clarification_refs))
        object.__setattr__(self, "audit_refs", tuple(self.audit_refs))
        object.__setattr__(self, "metadata", _frozen_metadata(self.metadata))


__all__ = [
    "PREVIEW_SCHEMA_VERSION",
    "Preview",
]
