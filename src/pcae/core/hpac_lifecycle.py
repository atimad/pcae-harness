"""
HPAC-001 v2.0 §40 — canonical, hash-chained proof lifecycle.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3 (Layer 1-2 foundation). Implements
`HumanAuthenticationProofLifecycleEvent` (HPAC-REQ-095) and
`HPACLifecycleStore`'s narrow transition API (plan §20): `open_challenge`,
`record_assertion`, `record_verified`, `bind_gate5`, `terminate`. No
caller can construct a `LifecycleEvent` directly and have it accepted --
only the store computes `event_digest`, chains `previous_event_digest`,
and enforces HPAC-REQ-095's entry/exit table.

Genesis gating (HPAC-REQ-096, plan §19): `open_challenge` requires the
caller to pass an already-resolved `TrustedApprovalPresentationEvidence`
for the exact `approval_id` being challenged (via
`approval_presentation.TrustedApprovalPresentationStore.resolve_structural`,
called by the caller before invoking this method and the resolved
evidence's own `approval_id` cross-checked here) -- there is no bare
"create sequence 0 from an approval_id string alone" code path.

hash consistency != canonical authority: fork/gap/duplicate-sequence
detection here proves *chain* integrity, not that the *writer* is the
trusted challenge coordinator -- HPAC-REQ-096's genesis authority
requirement is enforced structurally instead, via the presentation-
resolution dependency above, not merely by a checkable field.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.core.approval_presentation import TrustedApprovalPresentationEvidence
from pcae.core.hpac_foundation import (
    HPACMalformedError,
    canonical_digest,
    id_pattern_matches,
    new_hpac_id,
    read_canonical_json_document,
    reject_symlink,
    write_atomic_create_only,
)

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

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    def _dir(self, proof_id: str) -> Path:
        return self._root / "proofs" / "v2" / proof_id / "lifecycle"

    def _path(self, proof_id: str, sequence: int) -> Path:
        return self._dir(proof_id) / f"{sequence:04d}.json"

    def _load_chain(self, proof_id: str) -> list[LifecycleEvent]:
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
            document = read_canonical_json_document(path)
            _validate_event_document(document)
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
        return events

    def _append(self, proof_id: str, *, state: str, binding: dict, evidence_fields: dict, terminal_reason_code: Optional[str] = None) -> LifecycleEvent:
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
        import json

        payload = json.dumps(payload_document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        write_atomic_create_only(self._path(proof_id, sequence), payload)
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
        return self._append(
            proof_id,
            state=STATE_CHALLENGE_CREATED,
            binding=binding,
            evidence_fields={"occurred_at": occurred_at},
        )

    def record_assertion(self, *, proof_id: str, assertion_digest: str, occurred_at: str) -> LifecycleEvent:
        chain = self._load_chain(proof_id)
        if not chain or chain[-1].state != STATE_CHALLENGE_CREATED:
            raise HPACLifecycleStateError(f"record_assertion requires current state CHALLENGE_CREATED for {proof_id}")
        return self._append(
            proof_id,
            state=STATE_ASSERTION_RECEIVED,
            binding=chain[0].binding,
            evidence_fields={"occurred_at": occurred_at, "assertion_digest": assertion_digest},
        )

    def record_verified(
        self,
        *,
        proof_id: str,
        proof_digest: str,
        registry_state_digest: str,
        verifier_version: str,
        occurred_at: str,
    ) -> LifecycleEvent:
        chain = self._load_chain(proof_id)
        if not chain or chain[-1].state != STATE_ASSERTION_RECEIVED:
            raise HPACLifecycleStateError(f"record_verified requires current state ASSERTION_RECEIVED for {proof_id}")
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
        )

    def bind_gate5(self, *, proof_id: str, approval_digest: str, occurred_at: str) -> LifecycleEvent:
        chain = self._load_chain(proof_id)
        if not chain:
            raise HPACLifecycleStateError(f"bind_gate5 requires an existing chain for {proof_id}")
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
        )

    def terminate(self, *, proof_id: str, state: str, reason_code: str, occurred_at: str) -> LifecycleEvent:
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
        )

    def resolve_chain(self, proof_id: str) -> tuple[LifecycleEvent, ...]:
        return tuple(self._load_chain(proof_id))
