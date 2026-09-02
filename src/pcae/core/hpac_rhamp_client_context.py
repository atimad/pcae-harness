"""RHAMP-001 v1.0 §7 / §8 / §36 — the PCAE-owned canonical native-CTAP2
client-data context (``RHAMP-CLIENT-CONTEXT/1.0``).

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4. RHAMP-001 v1.0 does **not** use
a WebAuthn browser ``clientDataJSON`` and does **not** treat any string as a
browser security origin (RHAMP-REQ-022/027/028). Instead the trusted
challenge-construction component builds this closed object, canonically
serialises it (HPAC-REQ-089 verbatim), and passes
``client_data_hash = SHA-256(client_data_bytes)`` to the CTAP2 call as its
``clientDataHash`` (RHAMP-REQ-024). The signed assertion therefore binds
``authenticatorData ‖ client_data_hash`` — transitively binding every field
below.

No field of this object is caller-selectable (RHAMP-REQ-026). The requesting
agent MAY ask that a ceremony begin; it SHALL NOT supply, influence, or
observe the nonce, the digests, or the timestamps.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

from pcae.core.hpac_foundation import (
    HPACMalformedError,
    canonical_json_bytes,
    require_nonempty_str,
    require_timestamp,
)

__all__ = [
    "CLIENT_CONTEXT_SCHEMA",
    "RP_ID",
    "RP_ID_HASH",
    "MECHANISM_ID",
    "CEREMONY_KINDS",
    "CONTEXT_IDENTIFIER",
    "DOMAIN_SEPARATOR",
    "RhampClientContextError",
    "RhampClientContext",
    "build_client_context",
    "validate_client_context_document",
]

#: RHAMP-REQ-023.
CLIENT_CONTEXT_SCHEMA = "RHAMP-CLIENT-CONTEXT/1.0"

#: RHAMP-REQ-017 — a compiled-in PCAE constant, distinct from HATP's
#: ``hatp.pcae.local`` (HPAC-REQ-047/084 domain separation). Not a web
#: origin (RHAMP-REQ-020). Not varied by repo / cwd / env / agent / host
#: (RHAMP-REQ-019) — it is a constant string, identical on every host.
RP_ID = "hpac.pcae.local"
#: RHAMP-REQ-018 — ``authenticatorData.rpIdHash`` SHALL equal this.
RP_ID_HASH = hashlib.sha256(RP_ID.encode("utf-8")).digest()

#: RHAMP-REQ-011 — the single real-authority-eligible ``mechanism_id``.
MECHANISM_ID = "hpac.fido2.uv_presence.v2"

#: RHAMP-REQ-023 — ``ceremony_kind`` is a frozen const per operation.
CEREMONY_KINDS = ("runtime-invocation-approval", "credential-enrollment")

#: RHAMP-REQ-023 / §8 — a PCAE-internal domain-separation constant,
#: classified explicitly as **not** a browser security origin
#: (RHAMP-REQ-028). One per ceremony kind.
CONTEXT_IDENTIFIER = {
    "runtime-invocation-approval": "pcae-hpac://hpac.pcae.local/runtime-invocation-approval.v2",
    "credential-enrollment": "pcae-hpac://hpac.pcae.local/credential-enrollment.v2",
}
#: RHAMP-REQ-023 / HPAC-REQ-047.
DOMAIN_SEPARATOR = {
    "runtime-invocation-approval": "pcae.hpac.runtime-invocation-approval.v2",
    "credential-enrollment": "pcae.hpac.credential-enrollment.v2",
}

_HEX64 = frozenset("0123456789abcdef")


class RhampClientContextError(HPACMalformedError):
    """A ``RHAMP-CLIENT-CONTEXT/1.0`` object fails closed schema / grammar /
    frozen-constant validation."""


def _require_digest(value: object, *, context: str) -> str:
    text = require_nonempty_str(value, context=context)
    if len(text) != 64 or any(ch not in _HEX64 for ch in text):
        raise RhampClientContextError(f"{context}: expected 64 lowercase hex characters")
    return text


@dataclass(frozen=True)
class RhampClientContext:
    """The closed 15-field ``RHAMP-CLIENT-CONTEXT/1.0`` object (RHAMP-REQ-023)
    plus the derived canonical bytes / hash (RHAMP-REQ-024).

    ``client_data_bytes`` is the HPAC-REQ-089 canonical serialisation of the
    15 schema fields only (never of the derived bytes/hash). ``client_data_hash``
    is ``SHA-256(client_data_bytes)`` and is what the CTAP2
    ``makeCredential`` / ``getAssertion`` call passes as its ``clientDataHash``.
    """

    client_context_schema: str
    ceremony_kind: str
    context_identifier: str
    domain_separator: str
    challenge_digest: str
    approval_subject_digest: str
    trusted_presentation_digest: str
    principal_id: str
    credential_id: str
    invocation_id: str
    attempt_id: str
    nonce: str
    issued_at: str
    expires_at: str
    mechanism_id: str

    def to_document(self) -> dict:
        return {
            "client_context_schema": self.client_context_schema,
            "ceremony_kind": self.ceremony_kind,
            "context_identifier": self.context_identifier,
            "domain_separator": self.domain_separator,
            "challenge_digest": self.challenge_digest,
            "approval_subject_digest": self.approval_subject_digest,
            "trusted_presentation_digest": self.trusted_presentation_digest,
            "principal_id": self.principal_id,
            "credential_id": self.credential_id,
            "invocation_id": self.invocation_id,
            "attempt_id": self.attempt_id,
            "nonce": self.nonce,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "mechanism_id": self.mechanism_id,
        }

    @property
    def client_data_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_document())

    @property
    def client_data_hash(self) -> bytes:
        return hashlib.sha256(self.client_data_bytes).digest()


_SCHEMA_FIELDS = frozenset(RhampClientContext.__dataclass_fields__)


def build_client_context(
    *,
    ceremony_kind: Literal["runtime-invocation-approval", "credential-enrollment"],
    challenge_digest: str,
    approval_subject_digest: str,
    trusted_presentation_digest: str,
    principal_id: str,
    credential_id: str,
    invocation_id: str,
    attempt_id: str,
    nonce: str,
    issued_at: str,
    expires_at: str,
) -> RhampClientContext:
    """RHAMP-REQ-022/023/026 — construct the canonical client-data context
    from **trusted** state only. The frozen constants (schema id,
    ``context_identifier``, ``domain_separator``, ``mechanism_id``) are
    supplied here, never by a caller.
    """

    if ceremony_kind not in CEREMONY_KINDS:
        raise RhampClientContextError(f"ceremony_kind is not a frozen constant: {ceremony_kind!r}")
    context = RhampClientContext(
        client_context_schema=CLIENT_CONTEXT_SCHEMA,
        ceremony_kind=ceremony_kind,
        context_identifier=CONTEXT_IDENTIFIER[ceremony_kind],
        domain_separator=DOMAIN_SEPARATOR[ceremony_kind],
        challenge_digest=_require_digest(challenge_digest, context="challenge_digest"),
        approval_subject_digest=_require_digest(
            approval_subject_digest, context="approval_subject_digest"
        ),
        trusted_presentation_digest=_require_digest(
            trusted_presentation_digest, context="trusted_presentation_digest"
        ),
        principal_id=require_nonempty_str(principal_id, context="principal_id"),
        credential_id=require_nonempty_str(credential_id, context="credential_id"),
        invocation_id=require_nonempty_str(invocation_id, context="invocation_id"),
        attempt_id=require_nonempty_str(attempt_id, context="attempt_id"),
        nonce=_require_nonce(nonce),
        issued_at=require_timestamp(issued_at, context="issued_at"),
        expires_at=require_timestamp(expires_at, context="expires_at"),
        mechanism_id=MECHANISM_ID,
    )
    return context


def _require_nonce(value: object) -> str:
    """RHAMP-REQ-079 — the challenge nonce is CSPRNG bytes, hex-encoded,
    ≥ 256 bits (64 hex chars). A deterministic NON_REAL test fixture MAY use
    a fixed value; this grammar check does not distinguish real from fixture
    — the structural NON_REAL wall (RHAMP-REQ-155 / §41) is elsewhere."""

    text = require_nonempty_str(value, context="nonce")
    if len(text) < 64 or any(ch not in _HEX64 for ch in text):
        raise RhampClientContextError("nonce: expected >= 64 lowercase hex characters (>= 256 bits)")
    return text


def validate_client_context_document(document: object) -> RhampClientContext:
    """Reconstruct + fail-closed-validate a persisted / transmitted
    ``RHAMP-CLIENT-CONTEXT/1.0`` object (RHAMP-REQ-006/025)."""

    if not isinstance(document, dict):
        raise RhampClientContextError("client context is not an object")
    if set(document) != _SCHEMA_FIELDS:
        raise RhampClientContextError(
            f"client context closed-field-set violation: {sorted(set(document) ^ _SCHEMA_FIELDS)}"
        )
    if document["client_context_schema"] != CLIENT_CONTEXT_SCHEMA:
        raise RhampClientContextError("client_context_schema is not the frozen const")
    ceremony_kind = document["ceremony_kind"]
    if ceremony_kind not in CEREMONY_KINDS:
        raise RhampClientContextError("ceremony_kind is not a frozen constant")
    if document["context_identifier"] != CONTEXT_IDENTIFIER[ceremony_kind]:
        raise RhampClientContextError("context_identifier is not the frozen const for this ceremony_kind")
    if document["domain_separator"] != DOMAIN_SEPARATOR[ceremony_kind]:
        raise RhampClientContextError("domain_separator is not the frozen const for this ceremony_kind")
    if document["mechanism_id"] != MECHANISM_ID:
        raise RhampClientContextError("mechanism_id is not the frozen const")
    return build_client_context(
        ceremony_kind=ceremony_kind,
        challenge_digest=document["challenge_digest"],
        approval_subject_digest=document["approval_subject_digest"],
        trusted_presentation_digest=document["trusted_presentation_digest"],
        principal_id=document["principal_id"],
        credential_id=document["credential_id"],
        invocation_id=document["invocation_id"],
        attempt_id=document["attempt_id"],
        nonce=document["nonce"],
        issued_at=document["issued_at"],
        expires_at=document["expires_at"],
    )
