"""
HPAC-001 v2.0 §38-§39 — `CanonicalRuntimeApprovalSubject`,
`ProtectedApprovalPresentationMechanism` interface,
`TrustedApprovalPresentationEvidence` model, and its canonical store.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3 (Layer 1-2 foundation). This module
freezes the presentation-evidence model/store and the mechanism-neutral
interface exactly (HPAC-REQ-089/090/091/092/093); it does **not**
implement HPAC-018's full verification sequence (Phase 3, out of scope).

`TrustedApprovalPresentationStore.resolve_structural` performs only
structural/shape checks: field-set closure, digest self-consistency, and
election ordering. It explicitly does **not** perform cryptographic
`mechanism_attestation` signature verification against a real installed
verifier configuration -- that is HPAC-018 step 5's job (Phase 3). Calling
code MUST NOT treat a structural pass from this module as
`PRINCIPAL_VERIFIED_INTENT`-grade trust.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from pcae.core.hpac_foundation import (
    HPACDuplicateError,
    HPACMalformedError,
    ProtectedAdminCapability,
    canonical_digest,
    id_pattern_matches,
    new_hpac_id,
    read_canonical_json_document,
    reject_symlink,
    require_nonempty_str,
    require_status,
    require_timestamp,
    write_atomic_create_only,
)

APPROVAL_SUBJECT_SCHEMA_VERSION = "HPAC-APPROVAL-SUBJECT/2.0"
PRESENTATION_EVIDENCE_SCHEMA_VERSION = "HPAC-PRESENTATION-EVIDENCE/2.0"
PRESENTATION_MECHANISM_SCHEMA_VERSION = "HPAC-PRESENTATION-MECHANISM/2.0"
PRESENTATION_ATTESTATION_VERSION = "HPAC-PRESENTATION-ATTESTATION/2.0"


class ApprovalPresentationError(Exception):
    """Base error for presentation evidence/store operations."""


class ApprovalPresentationTrustError(ApprovalPresentationError):
    """A structural or attestation-shape check failed -- the evidence
    (or a caller-constructed lookalike) is not trustworthy, per
    HPAC-REQ-005's non-authority rule."""


# ═══════════════════════════════════════════════════════════════════════
# CanonicalRuntimeApprovalSubject (HPAC-REQ-089)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CanonicalRuntimeApprovalSubject:
    subject_schema_version: str
    subject: dict
    approval_scope: dict
    approval_preview_digest: str
    expires_at: str
    attempt_limit: int = 1

    def to_document(self) -> dict:
        return {
            "subject_schema_version": self.subject_schema_version,
            "subject": self.subject,
            "approval_scope": self.approval_scope,
            "approval_preview_digest": self.approval_preview_digest,
            "expires_at": self.expires_at,
            "attempt_limit": self.attempt_limit,
        }

    def digest(self) -> str:
        return canonical_digest(self.to_document())


def new_canonical_runtime_approval_subject(
    *, subject: dict, approval_scope: dict, approval_preview_digest: str, expires_at: str
) -> CanonicalRuntimeApprovalSubject:
    if not isinstance(subject, dict):
        raise HPACMalformedError("subject must be a closed object")
    if not isinstance(approval_scope, dict):
        raise HPACMalformedError("approval_scope must be a closed object")
    return CanonicalRuntimeApprovalSubject(
        subject_schema_version=APPROVAL_SUBJECT_SCHEMA_VERSION,
        subject=subject,
        approval_scope=approval_scope,
        approval_preview_digest=require_nonempty_str(approval_preview_digest, context="approval_preview_digest"),
        expires_at=require_timestamp(expires_at, context="expires_at"),
        attempt_limit=1,
    )


# ═══════════════════════════════════════════════════════════════════════
# Presentation mechanism descriptor (HPAC-REQ-090) + store
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PresentationMechanismDescriptor:
    descriptor_schema_version: str
    mechanism_id: str
    descriptor_version: str
    verifier_kind: str
    verifier_configuration_digest: str
    renderer_profile: str
    protected_output: bool
    agent_substitution_resistant: bool
    canonical_subject_rendering: bool
    explicit_election_support: bool
    status: str
    descriptor_digest: str = ""

    def to_document(self, *, include_digest: bool) -> dict:
        doc = {
            "descriptor_schema_version": self.descriptor_schema_version,
            "mechanism_id": self.mechanism_id,
            "descriptor_version": self.descriptor_version,
            "verifier_kind": self.verifier_kind,
            "verifier_configuration_digest": self.verifier_configuration_digest,
            "renderer_profile": self.renderer_profile,
            "protected_output": self.protected_output,
            "agent_substitution_resistant": self.agent_substitution_resistant,
            "canonical_subject_rendering": self.canonical_subject_rendering,
            "explicit_election_support": self.explicit_election_support,
            "status": self.status,
        }
        if include_digest:
            doc["descriptor_digest"] = self.descriptor_digest
        return doc


class PresentationMechanismDescriptorStore:
    """`<root>/presentation-mechanisms/v2/<mechanism_id>/descriptor.json`
    (HPAC-REQ-090). Installation/revocation gated behind
    `ProtectedAdminCapability` -- an honest, non-production marker, not a
    real ceremony (see `hpac_foundation.ProtectedAdminCapability`)."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    def _path(self, mechanism_id: str) -> Path:
        return self._root / "presentation-mechanisms" / "v2" / mechanism_id / "descriptor.json"

    def install(
        self, capability: ProtectedAdminCapability, descriptor: PresentationMechanismDescriptor
    ) -> PresentationMechanismDescriptor:
        if not isinstance(capability, ProtectedAdminCapability):
            raise ApprovalPresentationError("installing a presentation-mechanism descriptor requires protected-admin capability")
        body_for_digest = descriptor.to_document(include_digest=False)
        digest = canonical_digest(body_for_digest)
        sealed = PresentationMechanismDescriptor(
            **{**descriptor.__dict__, "descriptor_digest": digest}
        )
        payload_document = sealed.to_document(include_digest=True)
        import json

        payload = json.dumps(payload_document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        write_atomic_create_only(self._path(descriptor.mechanism_id), payload)
        return sealed

    def resolve(self, mechanism_id: str) -> Optional[PresentationMechanismDescriptor]:
        path = self._path(mechanism_id)
        reject_symlink(path)
        if not path.exists():
            return None
        document = read_canonical_json_document(path)
        if not isinstance(document, dict):
            raise HPACMalformedError("presentation-mechanism descriptor is not an object")
        digest = document.get("descriptor_digest")
        without_digest = {k: v for k, v in document.items() if k != "descriptor_digest"}
        recomputed = canonical_digest(without_digest)
        if digest != recomputed:
            raise HPACMalformedError(f"presentation-mechanism descriptor digest mismatch for {mechanism_id}")
        return PresentationMechanismDescriptor(descriptor_digest=digest, **without_digest)


# ═══════════════════════════════════════════════════════════════════════
# TrustedApprovalPresentationEvidence (HPAC-REQ-091/092)
# ═══════════════════════════════════════════════════════════════════════

_EVIDENCE_ALLOWED_TOP_FIELDS = frozenset(
    {
        "presentation_schema_version",
        "presentation_id",
        "presentation_digest",
        "approval_id",
        "canonical_subject",
        "approval_subject_digest",
        "mechanism_ref",
        "human_visible_facts",
        "human_visible_representation_digest",
        "presented_at",
        "election",
        "mechanism_attestation",
        "mechanism_attestation_digest",
    }
)

_HUMAN_VISIBLE_FACTS_FIELDS = frozenset(
    {
        "repository_identity",
        "repository_display",
        "task_id",
        "task_display",
        "runtime_target_id",
        "runtime_target_display",
        "operation_effect_scope_display",
        "prompt_hash",
        "prompt_instruction_display",
        "invocation_id",
        "invocation_display",
        "expires_at",
        "one_shot_notice",
    }
)


@dataclass(frozen=True)
class TrustedApprovalPresentationEvidence:
    presentation_schema_version: str
    presentation_id: str
    presentation_digest: str
    approval_id: str
    canonical_subject: dict
    approval_subject_digest: str
    mechanism_ref: dict
    human_visible_facts: dict
    human_visible_representation_digest: str
    presented_at: str
    election: dict
    mechanism_attestation: str
    mechanism_attestation_digest: str

    def to_document(self, *, include_presentation_digest: bool) -> dict:
        doc = {
            "presentation_schema_version": self.presentation_schema_version,
            "presentation_id": self.presentation_id,
            "approval_id": self.approval_id,
            "canonical_subject": self.canonical_subject,
            "approval_subject_digest": self.approval_subject_digest,
            "mechanism_ref": self.mechanism_ref,
            "human_visible_facts": self.human_visible_facts,
            "human_visible_representation_digest": self.human_visible_representation_digest,
            "presented_at": self.presented_at,
            "election": self.election,
            "mechanism_attestation": self.mechanism_attestation,
            "mechanism_attestation_digest": self.mechanism_attestation_digest,
        }
        if include_presentation_digest:
            doc["presentation_digest"] = self.presentation_digest
        return doc


@runtime_checkable
class ProtectedApprovalPresentationMechanism(Protocol):
    """HPAC-001 §39.1/plan §12's mechanism-neutral interface. Only
    `present()` is a valid path to a `TrustedApprovalPresentationEvidence`
    instance -- ordinary code building the dataclass directly produces a
    schema-valid but untrusted lookalike (enforced by
    `TrustedApprovalPresentationStore.resolve_structural`, not by
    Python's own construction rules, which cannot prevent direct
    dataclass instantiation)."""

    def descriptor(self) -> PresentationMechanismDescriptor: ...

    def present(self, canonical_subject: CanonicalRuntimeApprovalSubject, approval_id: str) -> TrustedApprovalPresentationEvidence: ...


def _validate_evidence_document(document: dict) -> None:
    if not isinstance(document, dict):
        raise HPACMalformedError("presentation evidence is not an object")
    unknown = set(document.keys()) - _EVIDENCE_ALLOWED_TOP_FIELDS
    if unknown:
        raise HPACMalformedError(f"presentation evidence has unrecognized fields: {sorted(unknown)}")
    missing = _EVIDENCE_ALLOWED_TOP_FIELDS - set(document.keys())
    if missing:
        raise HPACMalformedError(f"presentation evidence missing required fields: {sorted(missing)}")
    if document.get("presentation_schema_version") != PRESENTATION_EVIDENCE_SCHEMA_VERSION:
        raise HPACMalformedError("presentation evidence has unknown/wrong presentation_schema_version")
    if not id_pattern_matches("hpe", document.get("presentation_id")):
        raise HPACMalformedError("presentation_id does not match ^hpe-[0-9a-f]{32}$")
    facts = document.get("human_visible_facts")
    if not isinstance(facts, dict) or set(facts.keys()) != _HUMAN_VISIBLE_FACTS_FIELDS:
        raise HPACMalformedError("human_visible_facts has an incorrect/incomplete closed field set")
    election = document.get("election")
    if not isinstance(election, dict) or set(election.keys()) != {"event_id", "action", "occurred_at"}:
        raise HPACMalformedError("election object has an incorrect closed field set")
    if election.get("action") != "approve":
        raise HPACMalformedError("election.action must be the const 'approve'")
    if not isinstance(election.get("event_id"), str) or not election["event_id"].startswith("hpevt-"):
        raise HPACMalformedError("election.event_id does not match the hpevt- grammar")


class TrustedApprovalPresentationStore:
    """`<root>/presentations/v2/<presentation_id>/presentation.json`
    (HPAC-REQ-093). Create-only, atomic, lookup only by the closed
    `(presentation_id, presentation_digest)` pair."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    def _path(self, presentation_id: str) -> Path:
        return self._root / "presentations" / "v2" / presentation_id / "presentation.json"

    def create(self, evidence: TrustedApprovalPresentationEvidence) -> TrustedApprovalPresentationEvidence:
        """The only path into this store. Ordinary code cannot call this
        with a hand-built evidence object and expect it to become
        canonical merely by writing successfully -- `resolve_structural`
        (the only read path) independently re-validates every structural
        invariant on every read, so a forged write that skipped this
        method's own checks (impossible via the public API, since this is
        the only writer) still could not silently establish trust."""

        reject_symlink(self._root)
        body_without_digest = evidence.to_document(include_presentation_digest=False)
        _validate_evidence_document({**body_without_digest, "presentation_digest": "placeholder"})
        recomputed_digest = canonical_digest(body_without_digest)
        if recomputed_digest != evidence.presentation_digest:
            raise ApprovalPresentationTrustError("presentation_digest does not match canonical evidence bytes")
        payload_document = evidence.to_document(include_presentation_digest=True)
        import json

        payload = json.dumps(payload_document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        write_atomic_create_only(self._path(evidence.presentation_id), payload)
        return evidence

    def resolve_structural(
        self, *, presentation_id: str, presentation_digest: str
    ) -> TrustedApprovalPresentationEvidence:
        """Structural-only resolution (see module docstring): validates
        closed-schema shape, digest self-consistency, and election
        ordering. Does **not** perform cryptographic
        `mechanism_attestation` verification -- callers needing full
        HPAC-018 trust must wait for the Phase 3 verifier."""

        if not id_pattern_matches("hpe", presentation_id):
            raise ApprovalPresentationTrustError("presentation_id does not match the hpe- grammar")
        reject_symlink(self._root)
        path = self._path(presentation_id)
        reject_symlink(path)
        if not path.exists():
            raise ApprovalPresentationTrustError(f"no presentation evidence at {presentation_id}")
        document = read_canonical_json_document(path)
        _validate_evidence_document(document)
        stored_digest = document.get("presentation_digest")
        without_digest = {k: v for k, v in document.items() if k != "presentation_digest"}
        recomputed_digest = canonical_digest(without_digest)
        if recomputed_digest != stored_digest:
            raise ApprovalPresentationTrustError("stored presentation_digest does not match canonical bytes")
        if stored_digest != presentation_digest:
            raise ApprovalPresentationTrustError("caller-supplied presentation_digest does not match resolved record")

        canonical_subject = document["canonical_subject"]
        subject_digest = canonical_digest(canonical_subject)
        if subject_digest != document["approval_subject_digest"]:
            raise ApprovalPresentationTrustError("approval_subject_digest does not match canonical_subject bytes")
        if canonical_subject.get("approval_preview_digest") != document["human_visible_representation_digest"]:
            # HPAC-REQ-092: approval_preview_digest SHALL equal the
            # human_visible_representation_digest; inequality fails closed.
            raise ApprovalPresentationTrustError(
                "canonical_subject.approval_preview_digest does not match human_visible_representation_digest"
            )

        presented_at = document["presented_at"]
        election = document["election"]
        if election["occurred_at"] < presented_at:
            raise ApprovalPresentationTrustError("election.occurred_at precedes presented_at (ordering violation)")

        attestation_object = {
            "attestation_version": PRESENTATION_ATTESTATION_VERSION,
            "presentation_id": document["presentation_id"],
            "approval_id": document["approval_id"],
            "approval_subject_digest": document["approval_subject_digest"],
            "human_visible_representation_digest": document["human_visible_representation_digest"],
            "descriptor_digest": document["mechanism_ref"].get("descriptor_digest"),
            "election": election,
            "presented_at": presented_at,
        }
        expected_attestation_digest = canonical_digest(attestation_object)
        if document["mechanism_attestation_digest"] != expected_attestation_digest:
            # Structural-shape check only (see module docstring): this
            # proves the recorded digest is internally self-consistent
            # with the attestation object's declared bytes; it is NOT a
            # cryptographic signature verification against a real
            # installed verifier configuration.
            raise ApprovalPresentationTrustError(
                "mechanism_attestation_digest does not match the expected attestation object bytes "
                "(structural check only, not cryptographic verification)"
            )
        if not document.get("mechanism_attestation"):
            raise ApprovalPresentationTrustError("mechanism_attestation is empty (blind touch is ineligible)")

        return TrustedApprovalPresentationEvidence(
            presentation_schema_version=document["presentation_schema_version"],
            presentation_id=document["presentation_id"],
            presentation_digest=stored_digest,
            approval_id=document["approval_id"],
            canonical_subject=canonical_subject,
            approval_subject_digest=document["approval_subject_digest"],
            mechanism_ref=document["mechanism_ref"],
            human_visible_facts=document["human_visible_facts"],
            human_visible_representation_digest=document["human_visible_representation_digest"],
            presented_at=presented_at,
            election=election,
            mechanism_attestation=document["mechanism_attestation"],
            mechanism_attestation_digest=document["mechanism_attestation_digest"],
        )


def new_presentation_id() -> str:
    return new_hpac_id("hpe")


def new_election_event_id() -> str:
    return new_hpac_id("hpevt")
