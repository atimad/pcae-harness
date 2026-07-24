"""Preview Builder (IWC-001 v1.1 §2, §10.1-§10.2, Phase 143J §16, Phase 143N).

The sole production owner of preview construction, preview validation,
Preview Digest generation, and preview integrity verification (this
phase's governing prompt, "Architectural Ownership"). No other production
component may duplicate these responsibilities; the Confirmation
Controller (``pcae.interactive_workflow.confirmation.controller``) calls
into this module for digest recomputation and staleness detection rather
than reimplementing either.

Preview Builder is deliberately stateless (Phase 143J §16 Preview Builder
row: "Adopt, as a pure function, not a stateful component" -- IWC-REQ-098
requires a Preview to be "a pure function of captured content," and
IWC-REQ-020/IWC-REQ-079 require two independent builds over identical
inputs to converge on an identical Preview). ``PreviewBuilder`` carries no
instance state; every method's output is a pure function of its
arguments.

This builder does not, and per its governing phase prompt never will,
publish, execute, authorize, recommend, or confirm. Those methods do not
exist on this class.
"""

from __future__ import annotations

import hashlib
import json
from typing import Iterable, Mapping, Optional, Tuple

from pcae.interactive_workflow.errors import (
    InvalidPreviewError,
    PreviewDigestMismatchError,
    StalePreviewError,
)
from pcae.interactive_workflow.preview.models import PREVIEW_SCHEMA_VERSION, Preview

_KNOWN_SCHEMA_VERSIONS = frozenset({PREVIEW_SCHEMA_VERSION})


def _canonicalize_refs(label: str, refs: Iterable[str]) -> Tuple[str, ...]:
    """Deduplicate-check and sort ``refs`` into canonical order.

    Raises ``InvalidPreviewError`` if a duplicate is present within the
    collection -- Preview Validation's "duplicate references" check
    (this phase's governing prompt), performed before construction so a
    ``Preview`` can never be built holding a duplicate reference.
    """

    materialized = list(refs)
    seen = set()
    duplicates = set()
    for ref in materialized:
        if ref in seen:
            duplicates.add(ref)
        seen.add(ref)
    if duplicates:
        raise InvalidPreviewError(
            f"{label} contains duplicate reference(s): {sorted(duplicates)!r}."
        )
    return tuple(sorted(materialized))


def _canonical_payload(preview: Preview) -> Mapping[str, object]:
    """The exact, canonical content Preview Digest is computed over.

    Uses only the Preview's own content -- never wall-clock time, random
    state, or iteration-order-dependent structures -- so the digest is
    deterministic, repeatable, and independent of runtime ordering
    (this phase's governing prompt, "Preview Digest").
    """

    return {
        "schema_version": preview.schema_version,
        "preview_id": preview.preview_id,
        "session_id": preview.session_id,
        "preview_timestamp": preview.preview_timestamp,
        "transition_sequence_number": preview.transition_sequence_number,
        "evidence_refs": list(preview.evidence_refs),
        "clarification_refs": list(preview.clarification_refs),
        "audit_refs": list(preview.audit_refs),
        "transition_summary": preview.transition_summary,
        "metadata": dict(preview.metadata),
    }


class PreviewBuilder:
    """Constructs, validates, and digests immutable Previews.

    Stateless: an instance holds no mutable data and may be freely shared
    or reconstructed; every method below is a pure function of its
    arguments.
    """

    def build(
        self,
        preview_id: str,
        session_id: str,
        preview_timestamp: str,
        transition_sequence_number: int,
        evidence_refs: Iterable[str] = (),
        clarification_refs: Iterable[str] = (),
        audit_refs: Iterable[str] = (),
        transition_summary: str = "",
        metadata: Optional[Mapping[str, object]] = None,
    ) -> Tuple[Preview, str]:
        """Construct an immutable ``Preview`` and its Preview Digest.

        Returns ``(preview, preview_digest)``. Raises
        ``InvalidPreviewError`` if any reference collection contains a
        duplicate.
        """

        preview = Preview(
            preview_id=preview_id,
            session_id=session_id,
            preview_timestamp=preview_timestamp,
            transition_sequence_number=transition_sequence_number,
            evidence_refs=_canonicalize_refs("evidence_refs", evidence_refs),
            clarification_refs=_canonicalize_refs("clarification_refs", clarification_refs),
            audit_refs=_canonicalize_refs("audit_refs", audit_refs),
            transition_summary=transition_summary,
            metadata=metadata,
        )
        return preview, self.compute_digest(preview)

    def compute_digest(self, preview: Preview) -> str:
        """Deterministically compute the Preview Digest of ``preview``.

        Repeatable and stable across replay: calling this twice on
        equal-content ``Preview`` instances always returns the same
        digest, independent of process, worker, or call order.
        """

        canonical = json.dumps(_canonical_payload(preview), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify_digest(self, preview: Preview, preview_digest: str) -> None:
        """Raise ``PreviewDigestMismatchError`` unless ``preview_digest``
        equals the digest recomputed from ``preview``'s exact content."""

        recomputed = self.compute_digest(preview)
        if recomputed != preview_digest:
            raise PreviewDigestMismatchError(
                f"Preview {preview.preview_id!r}: supplied digest {preview_digest!r} does "
                f"not match the digest recomputed from its exact content ({recomputed!r})."
            )

    def validate(
        self,
        preview: Preview,
        preview_digest: Optional[str] = None,
        required_evidence_refs: Iterable[str] = (),
        required_clarification_refs: Iterable[str] = (),
        required_audit_refs: Iterable[str] = (),
    ) -> None:
        """Validate ``preview`` for completeness and structural
        consistency. Fails closed: raises ``InvalidPreviewError`` (or
        ``PreviewDigestMismatchError`` for the digest-consistency check)
        on the first defect found; never repairs or defaults.

        Checks, in order: schema version, missing required references,
        duplicate references, and (if ``preview_digest`` is supplied)
        digest consistency.
        """

        try:
            schema_version = preview.schema_version
            evidence_refs = preview.evidence_refs
            clarification_refs = preview.clarification_refs
            audit_refs = preview.audit_refs
        except AttributeError as exc:
            raise InvalidPreviewError(f"Preview is malformed: {exc}") from exc

        if schema_version not in _KNOWN_SCHEMA_VERSIONS:
            raise InvalidPreviewError(f"Unsupported Preview schema_version: {schema_version!r}.")

        missing_evidence = sorted(set(required_evidence_refs) - set(evidence_refs))
        if missing_evidence:
            raise InvalidPreviewError(
                f"Preview {preview.preview_id!r} is missing required evidence "
                f"reference(s): {missing_evidence!r}."
            )
        missing_clarification = sorted(set(required_clarification_refs) - set(clarification_refs))
        if missing_clarification:
            raise InvalidPreviewError(
                f"Preview {preview.preview_id!r} is missing required clarification "
                f"reference(s): {missing_clarification!r}."
            )
        missing_audit = sorted(set(required_audit_refs) - set(audit_refs))
        if missing_audit:
            raise InvalidPreviewError(
                f"Preview {preview.preview_id!r} is missing required audit "
                f"reference(s): {missing_audit!r}."
            )

        for label, refs in (
            ("evidence_refs", evidence_refs),
            ("clarification_refs", clarification_refs),
            ("audit_refs", audit_refs),
        ):
            if len(set(refs)) != len(refs):
                raise InvalidPreviewError(
                    f"Preview {preview.preview_id!r} carries duplicate reference(s) in "
                    f"{label}."
                )

        if preview_digest is not None:
            self.verify_digest(preview, preview_digest)

    def detect_staleness(
        self,
        preview: Preview,
        preview_digest: str,
        current_session_id: str,
        current_transition_sequence_number: int,
    ) -> None:
        """Reject a stale or tampered Preview, fail closed, never
        auto-refreshed (this phase's governing prompt, "Stale Preview
        Detection": "No automatic refresh. Only deterministic
        rejection.").

        Compares session identity, transition sequence, and Preview
        Digest inputs (recomputed from ``preview``'s own content, which
        structurally includes ``preview_timestamp``) against the current
        values supplied by the caller.
        """

        if preview.session_id != current_session_id:
            raise StalePreviewError(
                f"Preview {preview.preview_id!r} was built for session "
                f"{preview.session_id!r}, not the current session {current_session_id!r}."
            )
        self.verify_digest(preview, preview_digest)
        if preview.transition_sequence_number != current_transition_sequence_number:
            raise StalePreviewError(
                f"Preview {preview.preview_id!r} was built at transition sequence "
                f"{preview.transition_sequence_number!r}, but the current transition "
                f"sequence is {current_transition_sequence_number!r}: the underlying "
                "session state has changed since this Preview was built."
            )


__all__ = ["PreviewBuilder"]
