"""RHAMP-001 v1.0 §20 / §21 / §22 — the protected per-credential
``RHAMP-COUNTER-STATE/1.0`` signature-counter artifact and its frozen
accept/block + linearization rules.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (merged RHAMP-REQ-156 ``.1R.30``
bundle). Canonical path:

    <HPAC_PROTECTED_ROOT>/credentials/<credential_id>/counter-state.json

RHAMP-REQ-065: RHAMP-001 v1.0 does **not** assert "the signature counter
must always increment" — modern / passkey authenticators legitimately report
``signCount == 0`` permanently. RHAMP-REQ-067: a counter anomaly is a
**security signal, not proof of cloning**; a regression fails the current
authentication closed, is audited, and marks the credential for
protected-admin review — it **never auto-revokes**.

RHAMP-REQ-069: created at enrollment with all-zero state; updated by
**atomic replace** (new canonical file → fsync → atomic rename → read-back).
A missing / corrupt record for an ``active`` credential → **fail closed**
(``protected_root_invalid``); it is **never** silently treated as "counter 0"
(RHAMP-REQ-069).

RHAMP-REQ-070: the counter-state artifact is **not** a ``CredentialRecord``
schema change and is **not** an authority-generation input — it is
anti-clone / audit evidence only.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

from pcae.core.hpac_foundation import (
    HPACAuthorityError,
    HPACMalformedError,
    HPACResolvedRecord,
    HPACStoreAuthority,
    HPACWriterCapability,
    canonical_digest,
    canonical_json_bytes,
    read_canonical_json_document,
    reject_symlink,
    require_nonempty_str,
    require_safe_relative_id_component,
    require_timestamp,
    write_atomic_create_only,
    write_atomic_replace,
)

__all__ = [
    "RHAMP_SCHEMA_VERSION",
    "COUNTER_STATE_SCHEMA",
    "COUNTER_STATE_WRITER_ROLES",
    "COUNTER_STATE_ENROLLMENT_ROLE",
    "COUNTER_STATE_VERIFIER_ROLE",
    "RhampCounterStateError",
    "RhampCounterRegressionError",
    "CounterState",
    "CounterDecision",
    "evaluate_signcount",
    "provenance_ref_for",
    "HpacRhampCounterStateStore",
]

RHAMP_SCHEMA_VERSION = "RHAMP-001/1.0"
COUNTER_STATE_SCHEMA = "RHAMP-COUNTER-STATE/1.0"

#: Created inside the one bounded ``enroll_credential`` PAWA transaction.
COUNTER_STATE_ENROLLMENT_ROLE = "human_principal_registry_admin"
#: Atomic-replace-updated by the trusted verifier after a successful
#: assertion (RHAMP-REQ-071), and cleared by a protected-admin review op.
COUNTER_STATE_VERIFIER_ROLE = "hpac_rhamp_counter_state_verifier"
COUNTER_STATE_WRITER_ROLES = frozenset(
    {COUNTER_STATE_ENROLLMENT_ROLE, COUNTER_STATE_VERIFIER_ROLE}
)

_COUNTER_FIELDS = frozenset(
    {
        "rhamp_schema_version",
        "artifact_schema_version",
        "record_digest",
        "credential_id",
        "last_accepted_meaningful",
        "last_observed_raw",
        "generation",
        "updated_at",
        "writer_provenance_ref",
        "review_flag",
    }
)


class RhampCounterStateError(HPACMalformedError):
    """A ``RHAMP-COUNTER-STATE/1.0`` record fails closed schema / canonical /
    digest / provenance / linearization validation (RHAMP-REQ-068/069/073)."""


class RhampCounterRegressionError(RhampCounterStateError):
    """RHAMP-REQ-066/067 — a non-zero meaningful signature-counter regression
    or non-increment. Fails the current authentication closed; the credential
    is marked for protected-admin review; **never** auto-revoked."""


def _require_non_negative_int(value: object, *, context: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RhampCounterStateError(f"{context}: expected a non-negative integer")
    return value


def _self_excluding_digest(document: dict) -> str:
    projected = dict(document)
    projected["record_digest"] = ""
    return canonical_digest(projected)


def provenance_ref_for(relative_record_posix: str) -> str:
    """The ``.authority/provenance/<key>.json`` relative reference the
    :class:`HPACStoreAuthority` writes for ``relative_record_posix`` — the
    same ``sha256(relative)`` key ``_provenance_path`` uses."""

    key = hashlib.sha256(relative_record_posix.encode("utf-8")).hexdigest()
    return f"provenance/{key}.json"


@dataclass(frozen=True)
class CounterState:
    """The closed ``RHAMP-COUNTER-STATE/1.0`` object (RHAMP-REQ-068)."""

    credential_id: str
    last_accepted_meaningful: int
    last_observed_raw: int
    generation: int
    updated_at: str
    writer_provenance_ref: str
    review_flag: bool

    def to_document(self, *, include_digest: bool) -> dict:
        document = {
            "rhamp_schema_version": RHAMP_SCHEMA_VERSION,
            "artifact_schema_version": COUNTER_STATE_SCHEMA,
            "credential_id": self.credential_id,
            "last_accepted_meaningful": self.last_accepted_meaningful,
            "last_observed_raw": self.last_observed_raw,
            "generation": self.generation,
            "updated_at": self.updated_at,
            "writer_provenance_ref": self.writer_provenance_ref,
            "review_flag": self.review_flag,
        }
        if include_digest:
            document["record_digest"] = _self_excluding_digest(document)
        return document

    @property
    def record_digest(self) -> str:
        return _self_excluding_digest(self.to_document(include_digest=False))


@dataclass(frozen=True)
class CounterDecision:
    """The result of evaluating one authenticator ``signCount`` report
    against the current :class:`CounterState` (RHAMP-REQ-066)."""

    accepted: bool
    reason: str
    next_last_accepted_meaningful: int
    next_last_observed_raw: int
    review_flag: bool


def evaluate_signcount(state: CounterState, observed: int) -> CounterDecision:
    """RHAMP-REQ-066 — the frozen accept/block table, evaluated against
    ``state.last_accepted_meaningful``. ``observed`` is the raw value the
    authenticator reported (``0`` if absent, per the CTAP2 spec)."""

    observed = _require_non_negative_int(observed, context="observed signCount")
    last = state.last_accepted_meaningful

    if observed == 0:
        # "signCount absent, or == 0" → accept; record 0; "non-counter
        # authenticator". Does not lower an already-adopted meaningful value.
        return CounterDecision(
            accepted=True,
            reason="non_counter_authenticator",
            next_last_accepted_meaningful=last,
            next_last_observed_raw=observed,
            review_flag=state.review_flag,
        )
    if last == 0:
        # "last_accepted_meaningful == 0 (non-counter authenticator) and a
        # later report is non-zero" → accept; adopt as new meaningful
        # (a one-time transition).
        return CounterDecision(
            accepted=True,
            reason="meaningful_counter_adopted",
            next_last_accepted_meaningful=observed,
            next_last_observed_raw=observed,
            review_flag=state.review_flag,
        )
    if observed > last:
        return CounterDecision(
            accepted=True,
            reason="meaningful_increase",
            next_last_accepted_meaningful=observed,
            next_last_observed_raw=observed,
            review_flag=state.review_flag,
        )
    # observed != 0, last != 0, observed <= last → regression / non-increment.
    return CounterDecision(
        accepted=False,
        reason="signature_counter_regression",
        next_last_accepted_meaningful=last,
        next_last_observed_raw=observed,
        review_flag=True,
    )


def _parse_counter_document(document: object) -> CounterState:
    if not isinstance(document, dict):
        raise RhampCounterStateError("counter-state record is not an object")
    if set(document) != _COUNTER_FIELDS:
        raise RhampCounterStateError(
            f"counter-state closed-field-set violation: {sorted(set(document) ^ _COUNTER_FIELDS)}"
        )
    if document["rhamp_schema_version"] != RHAMP_SCHEMA_VERSION:
        raise RhampCounterStateError("rhamp_schema_version is not the frozen const")
    if document["artifact_schema_version"] != COUNTER_STATE_SCHEMA:
        raise RhampCounterStateError("artifact_schema_version is not the frozen const")
    stored_digest = require_nonempty_str(document["record_digest"], context="record_digest")
    if _self_excluding_digest(document) != stored_digest:
        raise RhampCounterStateError("record_digest does not recompute over the canonical bytes")
    credential_id = require_nonempty_str(document["credential_id"], context="credential_id")
    last_accepted = _require_non_negative_int(
        document["last_accepted_meaningful"], context="last_accepted_meaningful"
    )
    last_observed = _require_non_negative_int(document["last_observed_raw"], context="last_observed_raw")
    generation = _require_non_negative_int(document["generation"], context="generation")
    updated_at = require_timestamp(document["updated_at"], context="counter.updated_at")
    provenance_ref = require_nonempty_str(document["writer_provenance_ref"], context="writer_provenance_ref")
    review_flag = document["review_flag"]
    if not isinstance(review_flag, bool):
        raise RhampCounterStateError("review_flag must be a bool")
    return CounterState(
        credential_id=credential_id,
        last_accepted_meaningful=last_accepted,
        last_observed_raw=last_observed,
        generation=generation,
        updated_at=updated_at,
        writer_provenance_ref=provenance_ref,
        review_flag=review_flag,
    )


class HpacRhampCounterStateStore:
    """``<root>/credentials/<credential_id>/counter-state.json``.

    Create at enrollment (RHAMP-REQ-069); atomic-replace update after a
    verified assertion (RHAMP-REQ-071). A missing / corrupt record for an
    ``active`` credential fails closed — never "counter 0".
    """

    def __init__(self, root: Path | HPACStoreAuthority) -> None:
        self._authority = root if isinstance(root, HPACStoreAuthority) else HPACStoreAuthority.fixture(Path(root))
        self._root = self._authority.root

    @classmethod
    def production(cls) -> "HpacRhampCounterStateStore":
        return cls(HPACStoreAuthority.production())

    @property
    def authority(self) -> HPACStoreAuthority:
        return self._authority

    def _path(self, credential_id: str) -> Path:
        component = require_safe_relative_id_component(credential_id, context="credential_id")
        return self._root / "credentials" / component / "counter-state.json"

    def path(self, credential_id: str) -> Path:
        return self._path(credential_id)

    # ── enrollment (create-only, inside the bounded PAWA transaction) ──

    def initialize_canonical(
        self,
        writer: HPACWriterCapability,
        *,
        credential_id: str,
        updated_at: str,
        transaction_subject: str,
    ) -> CounterState:
        """RHAMP-REQ-069 — create the record with all-zero state."""

        reject_symlink(self._root)
        try:
            self._authority.require_writer(
                writer, COUNTER_STATE_ENROLLMENT_ROLE, subject=transaction_subject
            )
        except HPACAuthorityError as exc:
            raise RhampCounterStateError(str(exc)) from exc
        path = self._path(credential_id)
        relative = path.relative_to(self._root).as_posix()
        state = CounterState(
            credential_id=require_nonempty_str(credential_id, context="credential_id"),
            last_accepted_meaningful=0,
            last_observed_raw=0,
            generation=0,
            updated_at=require_timestamp(updated_at, context="updated_at"),
            writer_provenance_ref=provenance_ref_for(relative),
            review_flag=False,
        )
        document = state.to_document(include_digest=True)
        write_atomic_create_only(path, canonical_json_bytes(document))
        self._authority.record_write(
            path,
            document["record_digest"],
            writer,
            role=COUNTER_STATE_ENROLLMENT_ROLE,
            subject=transaction_subject,
        )
        readback = read_canonical_json_document(path)
        if readback != document:
            raise RhampCounterStateError("counter-state read-back verification failed after create")
        return _parse_counter_document(readback)

    # ── verification-time read + linearized update (RHAMP-REQ-071/§12) ──

    def resolve(self, credential_id: str) -> CounterState:
        """RHAMP-REQ-069 — fail closed on absent/corrupt; never 'counter 0'."""

        reject_symlink(self._root)
        path = self._path(credential_id)
        reject_symlink(path)
        if not path.exists():
            raise RhampCounterStateError(
                f"no counter-state record for {credential_id} (RHAMP-REQ-069 fail closed — not 'counter 0')"
            )
        return _parse_counter_document(read_canonical_json_document(path))

    def resolve_canonical(
        self, credential_id: str
    ) -> HPACResolvedRecord[CounterState]:
        state = self.resolve(credential_id)
        try:
            return self._authority.resolve_record(
                record=state,
                record_path=self._path(credential_id),
                record_digest=state.record_digest,
                roles=COUNTER_STATE_WRITER_ROLES,
            )
        except HPACAuthorityError as exc:
            raise RhampCounterStateError(str(exc)) from exc

    def evaluate(self, credential_id: str, observed_signcount: int) -> tuple[CounterState, CounterDecision]:
        """Read the current record and evaluate ``observed_signcount``
        against it (RHAMP-REQ-066). No write — this is step 1 of the
        verify sequence (RHAMP-REQ-071.1), run *before* any proof mints."""

        state = self.resolve(credential_id)
        return state, evaluate_signcount(state, observed_signcount)

    def apply_after_verification(
        self,
        writer: HPACWriterCapability,
        *,
        credential_id: str,
        expected_current: CounterState,
        decision: CounterDecision,
        updated_at: str,
    ) -> CounterState:
        """RHAMP-REQ-071.3 / §12 — the linearized update: re-read current,
        verify it is byte-identical to ``expected_current`` (else a lost
        update / concurrent writer → fail closed), then atomic-replace.

        Called **only** for an ``accepted`` decision, **after** the proof's
        ``PROOF_VERIFIED_AND_BOUND`` lifecycle event (RHAMP-REQ-071.2), and
        **before** the ``AuthenticatedHumanPrincipal`` is returned.
        """

        reject_symlink(self._root)
        if not decision.accepted:
            raise RhampCounterStateError("apply_after_verification requires an accepted counter decision")
        try:
            self._authority.require_writer(
                writer, COUNTER_STATE_VERIFIER_ROLE, subject=credential_id
            )
        except HPACAuthorityError as exc:
            raise RhampCounterStateError(str(exc)) from exc
        current = self.resolve(credential_id)
        if current.to_document(include_digest=True) != expected_current.to_document(include_digest=True):
            raise RhampCounterStateError(
                "counter-state changed after read; refusing stale/conflicting update (RHAMP-REQ-071 linearization)"
            )
        updated = replace(
            current,
            last_accepted_meaningful=decision.next_last_accepted_meaningful,
            last_observed_raw=decision.next_last_observed_raw,
            generation=current.generation + 1,
            updated_at=require_timestamp(updated_at, context="updated_at"),
            review_flag=decision.review_flag or current.review_flag,
        )
        document = updated.to_document(include_digest=True)
        path = self._path(credential_id)
        with self._authority.writer_transaction(writer, COUNTER_STATE_VERIFIER_ROLE, subject=credential_id):
            reread = self.resolve(credential_id)
            if reread.to_document(include_digest=True) != current.to_document(include_digest=True):
                raise RhampCounterStateError("counter-state changed inside the transaction; refusing overwrite")
            write_atomic_replace(path, canonical_json_bytes(document))
            self._authority.record_write(
                path,
                document["record_digest"],
                writer,
                role=COUNTER_STATE_VERIFIER_ROLE,
                subject=credential_id,
                replace=True,
            )
            readback = read_canonical_json_document(path)
            if readback != document:
                raise RhampCounterStateError("counter-state read-back verification failed after update")
        return _parse_counter_document(document)
