"""
HPAC-001 v2.0 §38-§39 — `CanonicalRuntimeApprovalSubject`,
`ProtectedApprovalPresentationMechanism` interface,
`TrustedApprovalPresentationEvidence` model, and its canonical store.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3 (Layer 1-2 foundation). This module
freezes the presentation-evidence model/store and the mechanism-neutral
interface exactly (HPAC-REQ-089/090/091/092/093); it does **not**
implement HPAC-018's full verification sequence (Phase 3, out of scope).

Phase .3.2 adds the bounded protected-mechanism installation and writer-
provenance seam needed by the foundation. ``resolve_structural`` remains an
explicit candidate-data API for historical fixtures. Only
``resolve_canonical`` returns a resolver-sealed record, after verifying the
installed descriptor, exact attestation bytes, writer provenance, and root.
No real device attestation or production verifier is implemented here.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from pcae.core.hpac_foundation import (
    HPACAuthorityError,
    HPACDuplicateError,
    HPACMalformedError,
    HPACResolvedRecord,
    HPACStoreAuthority,
    HPACWriterCapability,
    ProtectedAdminCapability,
    canonical_digest,
    canonical_json_bytes,
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
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_APPROVAL_ID_RE = re.compile(r"^ria-[0-9a-f]{32}$")


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

    _WRITER_ROLE = "presentation_mechanism_installer"

    def __init__(self, root: Path | HPACStoreAuthority) -> None:
        self._authority = root if isinstance(root, HPACStoreAuthority) else HPACStoreAuthority.fixture(Path(root))
        self._root = self._authority.root

    @classmethod
    def production(cls) -> "PresentationMechanismDescriptorStore":
        return cls(HPACStoreAuthority.production())

    @property
    def authority(self) -> HPACStoreAuthority:
        return self._authority

    def fixture_installer(self, mechanism_id: str) -> HPACWriterCapability:
        return self._authority.writer(self._WRITER_ROLE, subject=mechanism_id)

    def _path(self, mechanism_id: str) -> Path:
        return self._root / "presentation-mechanisms" / "v2" / mechanism_id / "descriptor.json"

    def _writer(
        self,
        capability: ProtectedAdminCapability | HPACWriterCapability,
        mechanism_id: str,
    ) -> HPACWriterCapability:
        try:
            if isinstance(capability, HPACWriterCapability):
                self._authority.require_writer(capability, self._WRITER_ROLE, subject=mechanism_id)
                return capability
            return self._authority.legacy_fixture_writer(
                capability, self._WRITER_ROLE, subject=mechanism_id
            )
        except HPACAuthorityError as exc:
            raise ApprovalPresentationError(str(exc)) from exc

    def install(
        self,
        capability: ProtectedAdminCapability | HPACWriterCapability,
        descriptor: PresentationMechanismDescriptor,
    ) -> PresentationMechanismDescriptor:
        writer = self._writer(capability, descriptor.mechanism_id)
        _validate_descriptor(descriptor, allow_empty_digest=True)
        body_for_digest = descriptor.to_document(include_digest=False)
        digest = canonical_digest(body_for_digest)
        sealed = PresentationMechanismDescriptor(
            **{**descriptor.__dict__, "descriptor_digest": digest}
        )
        payload_document = sealed.to_document(include_digest=True)
        path = self._path(descriptor.mechanism_id)
        write_atomic_create_only(path, canonical_json_bytes(payload_document))
        self._authority.record_write(
            path,
            digest,
            writer,
            role=self._WRITER_ROLE,
            subject=descriptor.mechanism_id,
        )
        return sealed

    def resolve(self, mechanism_id: str) -> Optional[PresentationMechanismDescriptor]:
        _validate_mechanism_id(mechanism_id)
        path = self._path(mechanism_id)
        reject_symlink(path)
        if not path.exists():
            return None
        document = read_canonical_json_document(path)
        if not isinstance(document, dict):
            raise HPACMalformedError("presentation-mechanism descriptor is not an object")
        _validate_descriptor_document(document)
        digest = document.get("descriptor_digest")
        without_digest = {k: v for k, v in document.items() if k != "descriptor_digest"}
        recomputed = canonical_digest(without_digest)
        if digest != recomputed:
            raise HPACMalformedError(f"presentation-mechanism descriptor digest mismatch for {mechanism_id}")
        return PresentationMechanismDescriptor(descriptor_digest=digest, **without_digest)

    def resolve_canonical(
        self, mechanism_id: str
    ) -> Optional[HPACResolvedRecord[PresentationMechanismDescriptor]]:
        descriptor = self.resolve(mechanism_id)
        if descriptor is None:
            return None
        return self._authority.resolve_record(
            record=descriptor,
            record_path=self._path(mechanism_id),
            record_digest=descriptor.descriptor_digest,
            roles=frozenset({self._WRITER_ROLE}),
            subject=mechanism_id,
        )


_DESCRIPTOR_ALLOWED_FIELDS = frozenset(
    {
        "descriptor_schema_version", "mechanism_id", "descriptor_version",
        "verifier_kind", "verifier_configuration_digest", "renderer_profile",
        "protected_output", "agent_substitution_resistant",
        "canonical_subject_rendering", "explicit_election_support", "status",
        "descriptor_digest",
    }
)


def _validate_descriptor(descriptor: PresentationMechanismDescriptor, *, allow_empty_digest: bool) -> None:
    if descriptor.descriptor_schema_version != PRESENTATION_MECHANISM_SCHEMA_VERSION:
        raise HPACMalformedError("presentation descriptor schema version is invalid")
    _validate_mechanism_id(descriptor.mechanism_id)
    require_nonempty_str(descriptor.descriptor_version, context="descriptor.descriptor_version")
    require_nonempty_str(descriptor.verifier_kind, context="descriptor.verifier_kind")
    require_nonempty_str(descriptor.verifier_configuration_digest, context="descriptor.verifier_configuration_digest")
    require_nonempty_str(descriptor.renderer_profile, context="descriptor.renderer_profile")
    require_status(descriptor.status, context="descriptor")
    if not all(
        value is True
        for value in (
            descriptor.protected_output,
            descriptor.agent_substitution_resistant,
            descriptor.canonical_subject_rendering,
            descriptor.explicit_election_support,
        )
    ):
        raise HPACMalformedError("presentation descriptor protection guarantees must all be true")
    if not allow_empty_digest and not descriptor.descriptor_digest:
        raise HPACMalformedError("presentation descriptor digest is empty")


def _validate_mechanism_id(mechanism_id: object) -> str:
    value = require_nonempty_str(mechanism_id, context="descriptor.mechanism_id")
    if value in {".", ".."} or "/" in value or "\\" in value:
        raise HPACMalformedError("presentation mechanism_id is not one safe path component")
    return value


def _validate_descriptor_document(document: dict) -> None:
    if set(document) != _DESCRIPTOR_ALLOWED_FIELDS:
        raise HPACMalformedError("presentation descriptor has an incorrect closed field set")
    _validate_descriptor(PresentationMechanismDescriptor(**document), allow_empty_digest=False)


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
    if not _APPROVAL_ID_RE.fullmatch(str(document.get("approval_id", ""))):
        raise HPACMalformedError("approval_id does not match ^ria-[0-9a-f]{32}$")
    for field in (
        "presentation_digest", "approval_subject_digest",
        "human_visible_representation_digest", "mechanism_attestation_digest",
    ):
        if not _DIGEST_RE.fullmatch(str(document.get(field, ""))):
            raise HPACMalformedError(f"{field} is not a lowercase SHA-256 digest")
    canonical_subject = document.get("canonical_subject")
    if not isinstance(canonical_subject, dict) or set(canonical_subject) != {
        "subject_schema_version", "subject", "approval_scope",
        "approval_preview_digest", "expires_at", "attempt_limit",
    }:
        raise HPACMalformedError("canonical_subject has an incorrect closed field set")
    if canonical_subject.get("subject_schema_version") != APPROVAL_SUBJECT_SCHEMA_VERSION:
        raise HPACMalformedError("canonical_subject schema version is invalid")
    if canonical_subject.get("attempt_limit") != 1:
        raise HPACMalformedError("canonical_subject attempt_limit must be one")
    mechanism_ref = document.get("mechanism_ref")
    if not isinstance(mechanism_ref, dict) or set(mechanism_ref) != {
        "mechanism_id", "descriptor_version", "descriptor_digest"
    }:
        raise HPACMalformedError("mechanism_ref has an incorrect closed field set")
    _validate_mechanism_id(mechanism_ref.get("mechanism_id"))
    if not _DIGEST_RE.fullmatch(str(mechanism_ref.get("descriptor_digest", ""))):
        raise HPACMalformedError("mechanism_ref.descriptor_digest is invalid")
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
    require_timestamp(document.get("presented_at"), context="presentation.presented_at")
    require_timestamp(election.get("occurred_at"), context="presentation.election.occurred_at")


class TrustedApprovalPresentationStore:
    """`<root>/presentations/v2/<presentation_id>/presentation.json`
    (HPAC-REQ-093). Create-only, atomic, lookup only by the closed
    `(presentation_id, presentation_digest)` pair."""

    _WRITER_ROLE = "protected_presentation_mechanism"

    def __init__(self, root: Path | HPACStoreAuthority) -> None:
        self._authority = root if isinstance(root, HPACStoreAuthority) else HPACStoreAuthority.fixture(Path(root))
        self._root = self._authority.root

    @classmethod
    def production(cls) -> "TrustedApprovalPresentationStore":
        return cls(HPACStoreAuthority.production())

    @property
    def authority(self) -> HPACStoreAuthority:
        return self._authority

    def fixture_mechanism_writer(self, mechanism_id: str) -> HPACWriterCapability:
        return self._authority.writer(self._WRITER_ROLE, subject=mechanism_id)

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
        _validate_evidence_document({**body_without_digest, "presentation_digest": "0" * 64})
        recomputed_digest = canonical_digest(body_without_digest)
        if recomputed_digest != evidence.presentation_digest:
            raise ApprovalPresentationTrustError("presentation_digest does not match canonical evidence bytes")
        payload_document = evidence.to_document(include_presentation_digest=True)
        payload = canonical_json_bytes(payload_document)
        write_atomic_create_only(self._path(evidence.presentation_id), payload)
        return evidence

    def create_canonical(
        self,
        writer: HPACWriterCapability,
        evidence: TrustedApprovalPresentationEvidence,
        installed_descriptor: HPACResolvedRecord[PresentationMechanismDescriptor],
    ) -> TrustedApprovalPresentationEvidence:
        descriptor = self._authority.require_resolution(installed_descriptor)
        mechanism_id = descriptor.mechanism_id
        self._authority.require_writer(writer, self._WRITER_ROLE, subject=mechanism_id)
        if evidence.mechanism_ref != {
            "mechanism_id": mechanism_id,
            "descriptor_version": descriptor.descriptor_version,
            "descriptor_digest": descriptor.descriptor_digest,
        }:
            raise ApprovalPresentationTrustError("evidence does not bind the installed mechanism descriptor exactly")
        self._validate_visible_subject_binding(evidence)
        self._verify_installed_attestation(evidence, installed_descriptor)
        created = self.create(evidence)
        self._authority.record_write(
            self._path(evidence.presentation_id),
            evidence.presentation_digest,
            writer,
            role=self._WRITER_ROLE,
            subject=mechanism_id,
        )
        return created

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

        attestation_bytes = _decode_attestation(document["mechanism_attestation"])
        expected_attestation_digest = hashlib.sha256(attestation_bytes).hexdigest()
        if document["mechanism_attestation_digest"] != expected_attestation_digest:
            raise ApprovalPresentationTrustError(
                "mechanism_attestation_digest does not match decoded mechanism evidence bytes"
            )
        if not document.get("mechanism_attestation"):
            raise ApprovalPresentationTrustError("mechanism_attestation is empty (blind touch is ineligible)")
        resolved = TrustedApprovalPresentationEvidence(
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
        try:
            attestation_object = json.loads(attestation_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApprovalPresentationTrustError("mechanism attestation object is malformed") from exc
        if not isinstance(attestation_object, dict):
            raise ApprovalPresentationTrustError("mechanism attestation object is not a closed object")
        expected_attestation = presentation_attestation_object(resolved)
        if attestation_object != expected_attestation or canonical_json_bytes(attestation_object) != attestation_bytes:
            raise ApprovalPresentationTrustError("mechanism attestation object does not bind the evidence exactly")
        return resolved

    def resolve_canonical(
        self,
        *,
        presentation_id: str,
        presentation_digest: str,
        descriptor_store: PresentationMechanismDescriptorStore,
    ) -> HPACResolvedRecord[TrustedApprovalPresentationEvidence]:
        evidence = self.resolve_structural(
            presentation_id=presentation_id,
            presentation_digest=presentation_digest,
        )
        mechanism_id = evidence.mechanism_ref.get("mechanism_id")
        if not isinstance(mechanism_id, str):
            raise ApprovalPresentationTrustError("mechanism_ref.mechanism_id is malformed")
        installed = descriptor_store.resolve_canonical(mechanism_id)
        if installed is None:
            raise ApprovalPresentationTrustError("presentation mechanism is not authoritatively installed")
        try:
            descriptor = self._authority.require_resolution(installed)
        except HPACAuthorityError as exc:
            raise ApprovalPresentationTrustError("installed descriptor belongs to another HPAC root") from exc
        if descriptor.status != "active":
            raise ApprovalPresentationTrustError("installed presentation mechanism is not active")
        expected_ref = {
            "mechanism_id": descriptor.mechanism_id,
            "descriptor_version": descriptor.descriptor_version,
            "descriptor_digest": descriptor.descriptor_digest,
        }
        if evidence.mechanism_ref != expected_ref:
            raise ApprovalPresentationTrustError("presentation mechanism/version/digest substitution")
        self._validate_visible_subject_binding(evidence)
        self._verify_installed_attestation(evidence, installed)
        try:
            return self._authority.resolve_record(
                record=evidence,
                record_path=self._path(presentation_id),
                record_digest=presentation_digest,
                roles=frozenset({self._WRITER_ROLE}),
                subject=mechanism_id,
            )
        except HPACAuthorityError as exc:
            raise ApprovalPresentationTrustError(str(exc)) from exc

    @staticmethod
    def _validate_visible_subject_binding(evidence: TrustedApprovalPresentationEvidence) -> None:
        subject = evidence.canonical_subject.get("subject")
        facts = evidence.human_visible_facts
        if not isinstance(subject, dict):
            raise ApprovalPresentationTrustError("canonical subject.subject is malformed")
        bindings = {
            "repository_identity": "repository_identity",
            "task_id": "task_id",
            "runtime_target_id": "runtime_target_id",
            "prompt_hash": "prompt_hash",
            "invocation_id": "invocation_id",
        }
        for fact_key, subject_key in bindings.items():
            if facts.get(fact_key) != subject.get(subject_key):
                raise ApprovalPresentationTrustError(f"human-visible {fact_key} is not bound to canonical subject")
        if facts.get("expires_at") != evidence.canonical_subject.get("expires_at"):
            raise ApprovalPresentationTrustError("human-visible expiry is not bound to canonical subject")
        if facts.get("one_shot_notice") is not True or evidence.canonical_subject.get("attempt_limit") != 1:
            raise ApprovalPresentationTrustError("one-shot presentation binding is invalid")

    @staticmethod
    def _verify_installed_attestation(
        evidence: TrustedApprovalPresentationEvidence,
        installed: HPACResolvedRecord[PresentationMechanismDescriptor],
    ) -> None:
        descriptor = installed.record
        if descriptor.verifier_kind != "deterministic-test-fixture":
            raise ApprovalPresentationTrustError(
                "no real protected-presentation attestation verifier is implemented in this phase"
            )
        if descriptor.verifier_configuration_digest != canonical_digest({"fixture": "deterministic"}):
            raise ApprovalPresentationTrustError("deterministic verifier configuration is not the installed fixture configuration")
        attestation_bytes = _decode_attestation(evidence.mechanism_attestation)
        if hashlib.sha256(attestation_bytes).hexdigest() != evidence.mechanism_attestation_digest:
            raise ApprovalPresentationTrustError("mechanism attestation digest does not bind decoded evidence bytes")
        try:
            attestation_object = json.loads(attestation_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApprovalPresentationTrustError("deterministic mechanism attestation is malformed") from exc
        expected = presentation_attestation_object(evidence)
        if attestation_object != expected or canonical_json_bytes(attestation_object) != attestation_bytes:
            raise ApprovalPresentationTrustError("mechanism attestation does not verify against installed descriptor state")


def _decode_attestation(value: object) -> bytes:
    if not isinstance(value, str) or not value:
        raise ApprovalPresentationTrustError("mechanism_attestation is empty or malformed")
    try:
        padded = value + "=" * (-len(value) % 4)
        return base64.b64decode(padded.encode("ascii"), altchars=b"-_", validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise ApprovalPresentationTrustError("mechanism_attestation is not base64url") from exc


def presentation_attestation_object(
    evidence: TrustedApprovalPresentationEvidence,
) -> dict:
    """HPAC-REQ-092's exact closed attested object.

    Only these eight fields are permitted; no other or omitted field is
    contract-conformant. Installation/writer authority and the deterministic
    mechanism's permanent non-real assurance class are established by
    separate channels -- the store's writer-provenance sidecar
    (`HPACStoreAuthority.record_write`/`verify_record`) and the installed
    descriptor's `verifier_kind`/`HPACAuthorityClass` -- and must never be
    smuggled into this attested object itself.
    """

    return {
        "attestation_version": PRESENTATION_ATTESTATION_VERSION,
        "presentation_id": evidence.presentation_id,
        "approval_id": evidence.approval_id,
        "approval_subject_digest": evidence.approval_subject_digest,
        "human_visible_representation_digest": evidence.human_visible_representation_digest,
        "descriptor_digest": evidence.mechanism_ref.get("descriptor_digest"),
        "election": evidence.election,
        "presented_at": evidence.presented_at,
    }


def new_presentation_id() -> str:
    return new_hpac_id("hpe")


def new_election_event_id() -> str:
    return new_hpac_id("hpevt")
