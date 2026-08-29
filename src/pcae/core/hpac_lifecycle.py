"""
HPAC-001 v2.0 §40 — canonical, hash-chained proof lifecycle.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3 (Layer 1-2 foundation). Implements
`HumanAuthenticationProofLifecycleEvent` (HPAC-REQ-095) and
`HPACLifecycleStore`'s narrow transition API (plan §20): `open_challenge`,
`record_assertion`, `record_verified`, `bind_gate5`, `terminate`. No
caller can construct a `LifecycleEvent` directly and have it accepted --
only the store computes `event_digest`, chains `previous_event_digest`,
and enforces HPAC-REQ-095's entry/exit table.

Phase .3.2 preserves the historical structural transition API for non-real
fixtures and adds a distinct canonical API. Canonical genesis requires a
resolver-sealed presentation, an exact challenge object, and the bound
challenge-coordinator writer. Every later event carries an independently
verified role-specific provenance sidecar. ``resolve_canonical_chain``
validates the complete transition/evidence table back to that genesis;
hash consistency by itself remains non-authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.core.approval_presentation import TrustedApprovalPresentationEvidence
from pcae.core.hpac_foundation import (
    HPACAuthorityError,
    HPACMalformedError,
    HPACResolvedRecord,
    HPACStoreAuthority,
    HPACWriterCapability,
    canonical_digest,
    canonical_json_bytes,
    id_pattern_matches,
    new_hpac_id,
    read_canonical_json_document,
    reject_symlink,
    require_safe_relative_id_component,
    write_atomic_create_only,
)
from pcae.core.human_authenticator import Challenge

LIFECYCLE_SCHEMA_VERSION = "HPAC-PROOF-LIFECYCLE-EVENT/2.0"

STATE_CHALLENGE_CREATED = "CHALLENGE_CREATED"
STATE_ASSERTION_RECEIVED = "ASSERTION_RECEIVED"
STATE_PROOF_VERIFIED = "PROOF_VERIFIED"
STATE_PROOF_VERIFIED_AND_BOUND = "PROOF_VERIFIED_AND_BOUND"
STATE_EXPIRED = "EXPIRED"
STATE_REVOKED = "REVOKED"
STATE_REJECTED = "REJECTED"

_NON_TERMINAL_ORDER = (
    STATE_CHALLENGE_CREATED,
    STATE_ASSERTION_RECEIVED,
    STATE_PROOF_VERIFIED,
    STATE_PROOF_VERIFIED_AND_BOUND,
)
_TERMINAL_STATES = frozenset({STATE_EXPIRED, STATE_REVOKED, STATE_REJECTED})
_ALL_STATES = frozenset(_NON_TERMINAL_ORDER) | _TERMINAL_STATES

_EVENT_ALLOWED_FIELDS = frozenset(
    {
        "lifecycle_schema_version",
        "event_id",
        "event_digest",
        "sequence",
        "previous_event_digest",
        "proof_id",
        "state",
        "occurred_at",
        "binding",
        "assertion_digest",
        "proof_digest",
        "approval_digest",
        "registry_state_digest",
        "verifier_version",
        "terminal_reason_code",
    }
)

_BINDING_ALLOWED_FIELDS = frozenset(
    {
        "approval_id",
        "invocation_id",
        "attempt_id",
        "principal_id",
        "credential_id",
        "mechanism_id",
        "approval_subject_digest",
        "trusted_presentation_ref",
        "challenge_digest",
    }
)


class HPACLifecycleError(Exception):
    """Base error for lifecycle-store operations."""


class HPACLifecycleForkError(HPACLifecycleError):
    """A drifted repeat of the sequence-0 `binding` object, or a second
    distinct event at an already-occupied sequence number, was detected.
    Fails closed (HPAC-REQ-094/095)."""


class HPACLifecycleGapError(HPACLifecycleError):
    """A requested transition would create a non-contiguous sequence
    number. Fails closed."""


class HPACLifecycleStateError(HPACLifecycleError):
    """A requested transition's entry condition (HPAC-REQ-095's table) is
    not satisfied by current chain state."""


@dataclass(frozen=True)
class LifecycleEvent:
    lifecycle_schema_version: str
    event_id: str
    event_digest: str
    sequence: int
    previous_event_digest: Optional[str]
    proof_id: str
    state: str
    occurred_at: str
    binding: dict
    assertion_digest: Optional[str]
    proof_digest: Optional[str]
    approval_digest: Optional[str]
    registry_state_digest: Optional[str]
    verifier_version: Optional[str]
    terminal_reason_code: Optional[str]

    def to_document(self, *, include_digest: bool) -> dict:
        doc = {
            "lifecycle_schema_version": self.lifecycle_schema_version,
            "event_id": self.event_id,
            "sequence": self.sequence,
            "previous_event_digest": self.previous_event_digest,
            "proof_id": self.proof_id,
            "state": self.state,
            "occurred_at": self.occurred_at,
            "binding": self.binding,
            "assertion_digest": self.assertion_digest,
            "proof_digest": self.proof_digest,
            "approval_digest": self.approval_digest,
            "registry_state_digest": self.registry_state_digest,
            "verifier_version": self.verifier_version,
            "terminal_reason_code": self.terminal_reason_code,
        }
        if include_digest:
            doc["event_digest"] = self.event_digest
        return doc


def _validate_binding(binding: dict) -> None:
    if not isinstance(binding, dict) or set(binding.keys()) != _BINDING_ALLOWED_FIELDS:
        raise HPACMalformedError("lifecycle event 'binding' has an incorrect closed field set")


def _validate_event_document(document: dict) -> None:
    if not isinstance(document, dict):
        raise HPACMalformedError("lifecycle event is not an object")
    unknown = set(document.keys()) - _EVENT_ALLOWED_FIELDS
    if unknown:
        raise HPACMalformedError(f"lifecycle event has unrecognized fields: {sorted(unknown)}")
    missing = _EVENT_ALLOWED_FIELDS - set(document.keys())
    if missing:
        raise HPACMalformedError(f"lifecycle event missing required fields: {sorted(missing)}")
    if document.get("lifecycle_schema_version") != LIFECYCLE_SCHEMA_VERSION:
        raise HPACMalformedError("lifecycle event has unknown/wrong lifecycle_schema_version")
    if not id_pattern_matches("hpl", document.get("event_id")):
        raise HPACMalformedError("event_id does not match ^hpl-[0-9a-f]{32}$")
    if document.get("state") not in _ALL_STATES:
        raise HPACMalformedError(f"lifecycle event has unknown state: {document.get('state')!r}")
    _validate_binding(document.get("binding"))


class HPACLifecycleStore:
    """`<root>/proofs/v2/<proof_id>/lifecycle/<sequence-4-digits>.json`
    (HPAC-REQ-094). Only the five narrow transition methods below can
    produce an accepted event; there is no generic "append any event"
    method."""

    _GENESIS_WRITER_ROLE = "hpac_challenge_coordinator"
    _ASSERTION_WRITER_ROLE = "hpac_assertion_recorder"
    _VERIFIED_WRITER_ROLE = "human_authentication_proof_verifier"
    _BOUND_WRITER_ROLE = "hpac_gate5_binder"
    _TERMINAL_WRITER_ROLE = "hpac_lifecycle_terminator"

    def __init__(self, root: Path | HPACStoreAuthority) -> None:
        self._authority = root if isinstance(root, HPACStoreAuthority) else HPACStoreAuthority.fixture(Path(root))
        self._root = self._authority.root

    @classmethod
    def production(cls) -> "HPACLifecycleStore":
        return cls(HPACStoreAuthority.production())

    @property
    def authority(self) -> HPACStoreAuthority:
        return self._authority

    def fixture_genesis_writer(self, proof_id: str) -> HPACWriterCapability:
        return self._authority.writer(self._GENESIS_WRITER_ROLE, subject=proof_id)

    def fixture_assertion_writer(self, proof_id: str) -> HPACWriterCapability:
        return self._authority.writer(self._ASSERTION_WRITER_ROLE, subject=proof_id)

    def fixture_verifier_writer(self, proof_id: str) -> HPACWriterCapability:
        return self._authority.writer(self._VERIFIED_WRITER_ROLE, subject=proof_id)

    def fixture_gate5_writer(self, proof_id: str) -> HPACWriterCapability:
        return self._authority.writer(self._BOUND_WRITER_ROLE, subject=proof_id)

    def fixture_terminal_writer(self, proof_id: str) -> HPACWriterCapability:
        return self._authority.writer(self._TERMINAL_WRITER_ROLE, subject=proof_id)

    def _dir(self, proof_id: str) -> Path:
        safe_proof_id = require_safe_relative_id_component(proof_id, context="proof_id")
        return self._root / "proofs" / "v2" / safe_proof_id / "lifecycle"

    def _path(self, proof_id: str, sequence: int) -> Path:
        return self._dir(proof_id) / f"{sequence:04d}.json"

    def _load_chain(self, proof_id: str, *, provenance_required: bool = False) -> list[LifecycleEvent]:
        if provenance_required and not id_pattern_matches("hap", proof_id):
            raise HPACLifecycleStateError("proof_id does not match ^hap-[0-9a-f]{32}$")
        reject_symlink(self._root)
        directory = self._dir(proof_id)
        if not directory.exists():
            return []
        reject_symlink(directory)
        events: list[LifecycleEvent] = []
        filenames = sorted(p.name for p in directory.iterdir() if p.is_file() or p.is_symlink())
        for index, filename in enumerate(filenames):
            if filename != f"{index:04d}.json":
                # Gap, duplicate, or unknown filename -- fail closed.
                raise HPACLifecycleGapError(
                    f"lifecycle chain for {proof_id} has a gap/duplicate/unknown file at position {index}: {filename}"
                )
            path = directory / filename
            reject_symlink(path)
            if provenance_required:
                try:
                    document = read_canonical_json_document(path)
                except HPACMalformedError as exc:
                    raise HPACLifecycleForkError(
                        f"lifecycle event {filename} is not canonical (fork or tamper)"
                    ) from exc
            else:
                try:
                    document = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise HPACLifecycleForkError(
                        f"lifecycle event {filename} is malformed (fork or tamper)"
                    ) from exc
            _validate_event_document(document)
            if document["proof_id"] != proof_id:
                raise HPACLifecycleForkError(
                    f"lifecycle event {filename} names a different proof_id"
                )
            stored_digest = document.get("event_digest")
            without_digest = {k: v for k, v in document.items() if k != "event_digest"}
            recomputed = canonical_digest(without_digest)
            if recomputed != stored_digest:
                raise HPACLifecycleError(f"lifecycle event {filename} for {proof_id} has a broken digest")
            if document["sequence"] != index:
                raise HPACLifecycleGapError(f"lifecycle event {filename} declares sequence {document['sequence']}, expected {index}")
            expected_previous = events[-1].event_digest if events else None
            if document["previous_event_digest"] != expected_previous:
                raise HPACLifecycleForkError(
                    f"lifecycle event {filename} for {proof_id} has a broken hash link (fork or tamper)"
                )
            if events and document["binding"] != events[0].binding:
                raise HPACLifecycleForkError(
                    f"lifecycle event {filename} for {proof_id} has a drifted 'binding' object relative to sequence 0 (fork)"
                )
            events.append(
                LifecycleEvent(
                    event_digest=stored_digest,
                    **without_digest,
                )
            )
            self._validate_transition(events)
            if provenance_required:
                role = self._role_for_state(events[-1].state)
                try:
                    self._authority.verify_record(
                        path,
                        stored_digest,
                        roles=frozenset({role}),
                        subject=proof_id,
                    )
                except HPACAuthorityError as exc:
                    raise HPACLifecycleStateError(
                        f"lifecycle event {filename} lacks authoritative writer provenance"
                    ) from exc
        return events

    @classmethod
    def _role_for_state(cls, state: str) -> str:
        return {
            STATE_CHALLENGE_CREATED: cls._GENESIS_WRITER_ROLE,
            STATE_ASSERTION_RECEIVED: cls._ASSERTION_WRITER_ROLE,
            STATE_PROOF_VERIFIED: cls._VERIFIED_WRITER_ROLE,
            STATE_PROOF_VERIFIED_AND_BOUND: cls._BOUND_WRITER_ROLE,
            STATE_EXPIRED: cls._TERMINAL_WRITER_ROLE,
            STATE_REVOKED: cls._TERMINAL_WRITER_ROLE,
            STATE_REJECTED: cls._TERMINAL_WRITER_ROLE,
        }[state]

    @staticmethod
    def _validate_transition(events: list[LifecycleEvent]) -> None:
        event = events[-1]
        if event.sequence == 0:
            if event.state != STATE_CHALLENGE_CREATED or event.previous_event_digest is not None:
                raise HPACLifecycleStateError("sequence 0 must be authoritative CHALLENGE_CREATED genesis")
            if any(
                value is not None
                for value in (
                    event.assertion_digest,
                    event.proof_digest,
                    event.approval_digest,
                    event.registry_state_digest,
                    event.verifier_version,
                    event.terminal_reason_code,
                )
            ):
                raise HPACLifecycleStateError("genesis contains fields forbidden at sequence 0")
            return
        previous = events[-2]
        if previous.state in _TERMINAL_STATES:
            raise HPACLifecycleStateError("no lifecycle event may follow a terminal state")
        if event.state in _TERMINAL_STATES:
            if not event.terminal_reason_code:
                raise HPACLifecycleStateError("terminal lifecycle event requires reason code")
            return
        expected_state = {
            STATE_CHALLENGE_CREATED: STATE_ASSERTION_RECEIVED,
            STATE_ASSERTION_RECEIVED: STATE_PROOF_VERIFIED,
            STATE_PROOF_VERIFIED: STATE_PROOF_VERIFIED_AND_BOUND,
        }.get(previous.state)
        if event.state != expected_state:
            raise HPACLifecycleStateError(
                f"invalid lifecycle predecessor relation: {previous.state} -> {event.state}"
            )
        if event.state == STATE_ASSERTION_RECEIVED:
            if not event.assertion_digest or any(
                value is not None
                for value in (
                    event.proof_digest, event.approval_digest,
                    event.registry_state_digest, event.verifier_version,
                    event.terminal_reason_code,
                )
            ):
                raise HPACLifecycleStateError("ASSERTION_RECEIVED staged evidence is invalid")
        elif event.state == STATE_PROOF_VERIFIED:
            if not all(
                (event.assertion_digest, event.proof_digest, event.registry_state_digest, event.verifier_version)
            ) or event.approval_digest is not None or event.terminal_reason_code is not None:
                raise HPACLifecycleStateError("PROOF_VERIFIED staged evidence is invalid")
        elif event.state == STATE_PROOF_VERIFIED_AND_BOUND:
            if not all(
                (
                    event.assertion_digest, event.proof_digest, event.approval_digest,
                    event.registry_state_digest, event.verifier_version,
                )
            ) or event.terminal_reason_code is not None:
                raise HPACLifecycleStateError("PROOF_VERIFIED_AND_BOUND staged evidence is invalid")

    def _append(
        self,
        proof_id: str,
        *,
        state: str,
        binding: dict,
        evidence_fields: dict,
        terminal_reason_code: Optional[str] = None,
        writer: Optional[HPACWriterCapability] = None,
    ) -> LifecycleEvent:
        chain = self._load_chain(proof_id)
        sequence = len(chain)
        previous_digest = chain[-1].event_digest if chain else None
        if chain:
            if chain[-1].binding != binding:
                raise HPACLifecycleForkError("binding must repeat sequence-0's binding object byte-for-byte")
        body_without_digest = {
            "lifecycle_schema_version": LIFECYCLE_SCHEMA_VERSION,
            "event_id": new_hpac_id("hpl"),
            "sequence": sequence,
            "previous_event_digest": previous_digest,
            "proof_id": proof_id,
            "state": state,
            "occurred_at": evidence_fields.get("occurred_at"),
            "binding": binding,
            "assertion_digest": evidence_fields.get("assertion_digest"),
            "proof_digest": evidence_fields.get("proof_digest"),
            "approval_digest": evidence_fields.get("approval_digest"),
            "registry_state_digest": evidence_fields.get("registry_state_digest"),
            "verifier_version": evidence_fields.get("verifier_version"),
            "terminal_reason_code": terminal_reason_code,
        }
        digest = canonical_digest(body_without_digest)
        payload_document = {**body_without_digest, "event_digest": digest}
        path = self._path(proof_id, sequence)
        write_atomic_create_only(path, canonical_json_bytes(payload_document))
        if writer is not None:
            role = self._role_for_state(state)
            self._authority.record_write(
                path,
                digest,
                writer,
                role=role,
                subject=proof_id,
            )
        return LifecycleEvent(event_digest=digest, **body_without_digest)

    # ── narrow transition API (plan §20) ──────────────────────────────

    def open_challenge(
        self,
        *,
        proof_id: str,
        approval_id: str,
        invocation_id: str,
        attempt_id: str,
        principal_id: str,
        credential_id: str,
        mechanism_id: str,
        approval_subject_digest: str,
        challenge_digest: str,
        occurred_at: str,
        resolved_presentation: TrustedApprovalPresentationEvidence,
        _writer: Optional[HPACWriterCapability] = None,
    ) -> LifecycleEvent:
        """Sequence 0. Genesis-gated (HPAC-REQ-096, plan §19): the caller
        MUST already hold a `resolve_structural`-resolved presentation
        evidence record for this exact `approval_id` -- a caller without
        that antecedent has no way to construct
        `resolved_presentation` other than by calling the presentation
        store's own resolution path first, which independently
        re-validates the evidence on every call."""

        if not isinstance(resolved_presentation, TrustedApprovalPresentationEvidence):
            raise HPACLifecycleStateError("open_challenge requires a resolved TrustedApprovalPresentationEvidence")
        if resolved_presentation.approval_id != approval_id:
            raise HPACLifecycleStateError(
                "resolved_presentation.approval_id does not match the approval_id being challenged"
            )
        if resolved_presentation.approval_subject_digest != approval_subject_digest:
            raise HPACLifecycleStateError(
                "resolved_presentation.approval_subject_digest does not match approval_subject_digest"
            )
        existing = self._load_chain(proof_id)
        if existing:
            raise HPACLifecycleForkError(f"proof_id {proof_id} already has a lifecycle chain; open_challenge is genesis-only")
        binding = {
            "approval_id": approval_id,
            "invocation_id": invocation_id,
            "attempt_id": attempt_id,
            "principal_id": principal_id,
            "credential_id": credential_id,
            "mechanism_id": mechanism_id,
            "approval_subject_digest": approval_subject_digest,
            "trusted_presentation_ref": {
                "presentation_id": resolved_presentation.presentation_id,
                "presentation_digest": resolved_presentation.presentation_digest,
            },
            "challenge_digest": challenge_digest,
        }
        if _writer is not None:
            self._authority.require_writer(
                _writer, self._GENESIS_WRITER_ROLE, subject=proof_id
            )
        return self._append(
            proof_id,
            state=STATE_CHALLENGE_CREATED,
            binding=binding,
            evidence_fields={"occurred_at": occurred_at},
            writer=_writer,
        )

    def open_challenge_canonical(
        self,
        writer: HPACWriterCapability,
        *,
        proof_id: str,
        approval_id: str,
        invocation_id: str,
        attempt_id: str,
        principal_id: str,
        credential_id: str,
        mechanism_id: str,
        occurred_at: str,
        resolved_presentation: HPACResolvedRecord[TrustedApprovalPresentationEvidence],
        challenge: Challenge,
    ) -> LifecycleEvent:
        """Create authoritative sequence 0 from resolved presentation + challenge."""

        try:
            presentation = self._authority.require_resolution(resolved_presentation)
            self._authority.require_writer(
                writer, self._GENESIS_WRITER_ROLE, subject=proof_id
            )
        except HPACAuthorityError as exc:
            raise HPACLifecycleStateError(str(exc)) from exc
        challenge_body = {
            "domain_separator": challenge.domain_separator,
            "challenge_version": challenge.challenge_version,
            "proof_schema_version": challenge.proof_schema_version,
            "principal_id": challenge.principal_id,
            "credential_id": challenge.credential_id,
            "approval_subject_digest": challenge.approval_subject_digest,
            "trusted_presentation_digest": challenge.trusted_presentation_digest,
            "nonce": challenge.nonce,
            "issued_at": challenge.issued_at,
            "expires_at": challenge.expires_at,
        }
        if canonical_digest(challenge_body) != challenge.challenge_digest:
            raise HPACLifecycleStateError("challenge_digest does not match canonical challenge bytes")
        if (
            challenge.principal_id != principal_id
            or challenge.credential_id != credential_id
            or challenge.approval_subject_digest != presentation.approval_subject_digest
            or challenge.trusted_presentation_digest != presentation.presentation_digest
        ):
            raise HPACLifecycleStateError("challenge/presentation/principal/credential substitution")
        subject = presentation.canonical_subject.get("subject")
        if not isinstance(subject, dict) or subject.get("invocation_id") != invocation_id:
            raise HPACLifecycleStateError("presentation invocation binding does not match lifecycle")
        return self.open_challenge(
            proof_id=proof_id,
            approval_id=approval_id,
            invocation_id=invocation_id,
            attempt_id=attempt_id,
            principal_id=principal_id,
            credential_id=credential_id,
            mechanism_id=mechanism_id,
            approval_subject_digest=presentation.approval_subject_digest,
            challenge_digest=challenge.challenge_digest,
            occurred_at=occurred_at,
            resolved_presentation=presentation,
            _writer=writer,
        )

    def record_assertion(
        self,
        *,
        proof_id: str,
        assertion_digest: str,
        occurred_at: str,
        _writer: Optional[HPACWriterCapability] = None,
    ) -> LifecycleEvent:
        chain = self._load_chain(proof_id)
        if not chain or chain[-1].state != STATE_CHALLENGE_CREATED:
            raise HPACLifecycleStateError(f"record_assertion requires current state CHALLENGE_CREATED for {proof_id}")
        if _writer is not None:
            self._authority.require_writer(
                _writer, self._ASSERTION_WRITER_ROLE, subject=proof_id
            )
        return self._append(
            proof_id,
            state=STATE_ASSERTION_RECEIVED,
            binding=chain[0].binding,
            evidence_fields={"occurred_at": occurred_at, "assertion_digest": assertion_digest},
            writer=_writer,
        )

    def record_assertion_canonical(
        self, writer: HPACWriterCapability, *, proof_id: str, assertion_digest: str, occurred_at: str
    ) -> LifecycleEvent:
        # Require canonical predecessor, not a merely structural chain.
        self.resolve_canonical_chain(proof_id)
        return self.record_assertion(
            proof_id=proof_id,
            assertion_digest=assertion_digest,
            occurred_at=occurred_at,
            _writer=writer,
        )

    def record_verified(
        self,
        *,
        proof_id: str,
        proof_digest: str,
        registry_state_digest: str,
        verifier_version: str,
        occurred_at: str,
        _writer: Optional[HPACWriterCapability] = None,
    ) -> LifecycleEvent:
        chain = self._load_chain(proof_id)
        if not chain or chain[-1].state != STATE_ASSERTION_RECEIVED:
            raise HPACLifecycleStateError(f"record_verified requires current state ASSERTION_RECEIVED for {proof_id}")
        if _writer is not None:
            self._authority.require_writer(
                _writer, self._VERIFIED_WRITER_ROLE, subject=proof_id
            )
        return self._append(
            proof_id,
            state=STATE_PROOF_VERIFIED,
            binding=chain[0].binding,
            evidence_fields={
                "occurred_at": occurred_at,
                "assertion_digest": chain[-1].assertion_digest,
                "proof_digest": proof_digest,
                "registry_state_digest": registry_state_digest,
                "verifier_version": verifier_version,
            },
            writer=_writer,
        )

    def record_verified_canonical(
        self,
        writer: HPACWriterCapability,
        *,
        resolved_proof: HPACResolvedRecord,
        registry_state_digest: str,
        verifier_version: str,
        occurred_at: str,
    ) -> LifecycleEvent:
        from pcae.core.human_authentication_proof import HumanAuthenticationProof

        try:
            proof = self._authority.require_resolution(resolved_proof)
        except HPACAuthorityError as exc:
            raise HPACLifecycleStateError(str(exc)) from exc
        if not isinstance(proof, HumanAuthenticationProof):
            raise HPACLifecycleStateError("record_verified_canonical requires canonical proof record")
        chain = self.resolve_canonical_chain(proof.proof_id)
        binding = chain[0].record.binding
        if any(
            (
                proof.principal_id != binding["principal_id"],
                proof.credential_id != binding["credential_id"],
                proof.mechanism_id != binding["mechanism_id"],
                proof.challenge_digest != binding["challenge_digest"],
                proof.approval_subject_digest != binding["approval_subject_digest"],
                proof.trusted_presentation_ref != binding["trusted_presentation_ref"],
            )
        ):
            raise HPACLifecycleStateError("canonical proof does not match lifecycle binding")
        return self.record_verified(
            proof_id=proof.proof_id,
            proof_digest=proof.proof_digest,
            registry_state_digest=registry_state_digest,
            verifier_version=verifier_version,
            occurred_at=occurred_at,
            _writer=writer,
        )

    def bind_gate5(
        self,
        *,
        proof_id: str,
        approval_digest: str,
        occurred_at: str,
        _writer: Optional[HPACWriterCapability] = None,
    ) -> LifecycleEvent:
        chain = self._load_chain(proof_id)
        if not chain:
            raise HPACLifecycleStateError(f"bind_gate5 requires an existing chain for {proof_id}")
        if _writer is not None:
            self._authority.require_writer(
                _writer, self._BOUND_WRITER_ROLE, subject=proof_id
            )
        if chain[-1].state == STATE_PROOF_VERIFIED_AND_BOUND:
            if chain[-1].approval_digest == approval_digest:
                # Idempotent same-binding revalidation (HPAC-REQ-097).
                return chain[-1]
            raise HPACLifecycleForkError("bind_gate5 called with a different approval_digest than the existing binding (cross-binding)")
        if chain[-1].state != STATE_PROOF_VERIFIED:
            raise HPACLifecycleStateError(f"bind_gate5 requires current state PROOF_VERIFIED for {proof_id}")
        return self._append(
            proof_id,
            state=STATE_PROOF_VERIFIED_AND_BOUND,
            binding=chain[0].binding,
            evidence_fields={
                "occurred_at": occurred_at,
                "assertion_digest": chain[-1].assertion_digest,
                "proof_digest": chain[-1].proof_digest,
                "approval_digest": approval_digest,
                "registry_state_digest": chain[-1].registry_state_digest,
                "verifier_version": chain[-1].verifier_version,
            },
            writer=_writer,
        )

    def bind_gate5_canonical(
        self,
        writer: HPACWriterCapability,
        *,
        proof_id: str,
        approval_digest: str,
        occurred_at: str,
    ) -> LifecycleEvent:
        self.resolve_canonical_chain(proof_id)
        return self.bind_gate5(
            proof_id=proof_id,
            approval_digest=approval_digest,
            occurred_at=occurred_at,
            _writer=writer,
        )

    def terminate(
        self,
        *,
        proof_id: str,
        state: str,
        reason_code: str,
        occurred_at: str,
        _writer: Optional[HPACWriterCapability] = None,
    ) -> LifecycleEvent:
        if state not in _TERMINAL_STATES:
            raise HPACLifecycleStateError(f"terminate requires a terminal state, got {state!r}")
        chain = self._load_chain(proof_id)
        if not chain:
            raise HPACLifecycleStateError(f"terminate requires an existing chain for {proof_id}")
        if chain[-1].state in _TERMINAL_STATES:
            raise HPACLifecycleStateError(f"lifecycle for {proof_id} is already terminal ({chain[-1].state}); no further event permitted")
        if not reason_code:
            raise HPACLifecycleStateError("terminate requires a non-empty reason_code")
        last = chain[-1]
        if _writer is not None:
            self._authority.require_writer(
                _writer, self._TERMINAL_WRITER_ROLE, subject=proof_id
            )
        return self._append(
            proof_id,
            state=state,
            binding=chain[0].binding,
            evidence_fields={
                "occurred_at": occurred_at,
                "assertion_digest": last.assertion_digest,
                "proof_digest": last.proof_digest,
                "approval_digest": last.approval_digest,
                "registry_state_digest": last.registry_state_digest,
                "verifier_version": last.verifier_version,
            },
            terminal_reason_code=reason_code,
            writer=_writer,
        )

    def terminate_canonical(
        self,
        writer: HPACWriterCapability,
        *,
        proof_id: str,
        state: str,
        reason_code: str,
        occurred_at: str,
    ) -> LifecycleEvent:
        self.resolve_canonical_chain(proof_id)
        return self.terminate(
            proof_id=proof_id,
            state=state,
            reason_code=reason_code,
            occurred_at=occurred_at,
            _writer=writer,
        )

    def resolve_gate5_binding_event(
        self, proof_id: str
    ) -> Optional[HPACResolvedRecord[LifecycleEvent]]:
        """Return the canonical, provenance-checked sequence-3
        ``PROOF_VERIFIED_AND_BOUND`` event for ``proof_id`` iff the chain is
        currently in that state, else ``None`` (Phase
        149O.20L.7O.3W.1R.2B.1R.1.1R.10, `.1R.9` §25 minimal support).

        Read-only: it resolves the full canonical chain (re-running every
        digest, hash-link, no-fork, transition, and writer-provenance check
        via :meth:`resolve_canonical_chain`), creates nothing, writes
        nothing, and consumes nothing. The Gate-5 approval-validation
        coordinator uses it to CONFIRM HPAC-REQ-097's sequence-3 binding
        after the verifier's HPAC-REQ-054 step 10 has created (or
        idempotently accepted) the event, and to capture the event digest
        for its ephemeral result. It never manufactures the event — the
        create / same-binding-idempotent path remains
        :meth:`bind_gate5_canonical`, unchanged.
        """
        chain = self.resolve_canonical_chain(proof_id)
        if not chain:
            return None
        last = chain[-1]
        if last.record.state != STATE_PROOF_VERIFIED_AND_BOUND:
            return None
        return last

    def resolve_chain(self, proof_id: str) -> tuple[LifecycleEvent, ...]:
        """Return validated lifecycle data, without conferring canonical authority."""
        return tuple(self._load_chain(proof_id))

    def resolve_canonical_chain(
        self, proof_id: str
    ) -> tuple[HPACResolvedRecord[LifecycleEvent], ...]:
        events = self._load_chain(proof_id, provenance_required=True)
        if not events:
            return ()
        resolved: list[HPACResolvedRecord[LifecycleEvent]] = []
        for event in events:
            resolved.append(
                self._authority.resolve_record(
                    record=event,
                    record_path=self._path(proof_id, event.sequence),
                    record_digest=event.event_digest,
                    roles=frozenset({self._role_for_state(event.state)}),
                    subject=proof_id,
                )
            )
        return tuple(resolved)
