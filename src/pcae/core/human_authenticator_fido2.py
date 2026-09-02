"""RHAMP-001 v1.0 §12 / §33 / §37 — ``FIDO2HumanAuthenticator`` for the
real ``hpac.fido2.uv_presence.v2`` mechanism.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (merged RHAMP-REQ-156 ``.1R.30``
bundle). Implements the mechanism-neutral
:class:`pcae.core.human_authenticator.HumanAuthenticator` protocol and, in
addition, drives the native CTAP2 ``authenticatorGetAssertion`` ceremony
(RHAMP-REQ-039 single-assertion, step-up-at-approval-time model B/D).

**This authenticator is not approval** (RHAMP-REQ-037): a successful
assertion is credential-presence + UV evidence. The HPAC verifier
(:mod:`pcae.core.hpac_verifier`, §18) is what turns proof material into a
trusted result, and only in conjunction with the resolved protected
presentation and the explicit observed election — neither of which this
phase implements (RHAMP-REQ-156 ``.1R.30``: "No protected approval UI. No
real approval-authority production path yet.").

The signed assertion is carried in a closed, versioned **assertion
envelope** (``RHAMP-FIDO2-ASSERTION/1.0``) inside the mechanism-neutral
``HumanAuthenticationProof.assertion`` (base64url) field — the
``HPAC-PROOF/2.0`` schema is byte-unchanged (RHAMP-REQ-121). The envelope
carries the raw ``authenticatorData``, the raw ``signature``, the raw CTAP2
``credential_id``, and the exact ``RHAMP-CLIENT-CONTEXT/1.0`` object the
assertion was produced over. The verifier reconstructs the canonical
client-data from **trusted state** and rejects any envelope-field
disagreement (RHAMP-REQ-025).
"""

from __future__ import annotations

import base64
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Final, Optional

from pcae.core.hpac_foundation import canonical_digest, canonical_json_bytes
from pcae.core.human_authenticator import (
    AssuranceLevel,
    Challenge,
    HumanAuthenticator,
    MechanismDescriptor,
    MechanismStatus,
    MechanismStatusValue,
    ProofMaterial,
)
from pcae.core.hpac_rhamp_client_context import (
    MECHANISM_ID,
    RhampClientContext,
    build_client_context,
    validate_client_context_document,
)
from pcae.core.hpac_rhamp_ctap2 import (
    Ctap2Provider,
    GetAssertionResult,
    MakeCredentialResult,
)
from pcae.core.hpac_rhamp_terminal_reasons import RhampTerminalError, TerminalReasonCode

__all__ = [
    "FIDO2_MECHANISM_ID",
    "ASSERTION_ENVELOPE_SCHEMA",
    "RHAMP_CHALLENGE_MAX_TTL_SECONDS",
    "RHAMP_MAX_PROOF_AGE_SECONDS",
    "CHALLENGE_DOMAIN_SEPARATOR",
    "CHALLENGE_VERSION",
    "PROOF_SCHEMA_VERSION",
    "AssertionEnvelope",
    "encode_assertion_envelope",
    "decode_assertion_envelope",
    "FIDO2HumanAuthenticator",
]

FIDO2_MECHANISM_ID: Final[str] = MECHANISM_ID  # hpac.fido2.uv_presence.v2
ASSERTION_ENVELOPE_SCHEMA: Final[str] = "RHAMP-FIDO2-ASSERTION/1.0"

#: RHAMP-REQ-074 / RHAMP-REQ-076.
RHAMP_CHALLENGE_MAX_TTL_SECONDS: Final[int] = 120
RHAMP_MAX_PROOF_AGE_SECONDS: Final[int] = 300

CHALLENGE_DOMAIN_SEPARATOR: Final[str] = "pcae.hpac.runtime-invocation-approval.v2"
CHALLENGE_VERSION: Final[str] = "HPAC-CHALLENGE/2.0"
PROOF_SCHEMA_VERSION: Final[str] = "HPAC-PROOF/2.0"


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _unb64u(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


@dataclass(frozen=True)
class AssertionEnvelope:
    """Closed ``RHAMP-FIDO2-ASSERTION/1.0`` object. Structurally NON_REAL
    until the full §37 sequence passes over a ``PRODUCTION`` credential."""

    authenticator_data: bytes
    signature: bytes
    raw_credential_id: bytes
    client_context: RhampClientContext
    sign_count: int
    up: bool
    uv: bool

    def to_document(self) -> dict:
        return {
            "envelope_schema_version": ASSERTION_ENVELOPE_SCHEMA,
            "authenticator_data": _b64u(self.authenticator_data),
            "signature": _b64u(self.signature),
            "raw_credential_id": _b64u(self.raw_credential_id),
            "client_context": self.client_context.to_document(),
            "sign_count": self.sign_count,
            "up": self.up,
            "uv": self.uv,
        }


_ENVELOPE_FIELDS = frozenset(
    {
        "envelope_schema_version",
        "authenticator_data",
        "signature",
        "raw_credential_id",
        "client_context",
        "sign_count",
        "up",
        "uv",
    }
)


def encode_assertion_envelope(envelope: AssertionEnvelope) -> str:
    """base64url of the canonical JSON of the closed envelope object."""

    return _b64u(canonical_json_bytes(envelope.to_document()))


def decode_assertion_envelope(assertion: str) -> AssertionEnvelope:
    """RHAMP-REQ-006 — fail closed on any schema / grammar deviation."""

    try:
        raw = _unb64u(assertion)
        import json

        document = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RhampTerminalError(
            TerminalReasonCode.INTERNAL_VERIFICATION_ERROR, f"assertion envelope is not decodable: {exc}"
        ) from exc
    if not isinstance(document, dict) or set(document) != _ENVELOPE_FIELDS:
        raise RhampTerminalError(
            TerminalReasonCode.INTERNAL_VERIFICATION_ERROR, "assertion envelope closed-field-set violation"
        )
    if document["envelope_schema_version"] != ASSERTION_ENVELOPE_SCHEMA:
        raise RhampTerminalError(
            TerminalReasonCode.INTERNAL_VERIFICATION_ERROR, "assertion envelope schema version is unknown"
        )
    if not isinstance(document["sign_count"], int) or isinstance(document["sign_count"], bool) or document["sign_count"] < 0:
        raise RhampTerminalError(
            TerminalReasonCode.INTERNAL_VERIFICATION_ERROR, "assertion envelope sign_count is invalid"
        )
    if not isinstance(document["up"], bool) or not isinstance(document["uv"], bool):
        raise RhampTerminalError(
            TerminalReasonCode.INTERNAL_VERIFICATION_ERROR, "assertion envelope up/uv must be bools"
        )
    context = validate_client_context_document(document["client_context"])
    return AssertionEnvelope(
        authenticator_data=_unb64u(document["authenticator_data"]),
        signature=_unb64u(document["signature"]),
        raw_credential_id=_unb64u(document["raw_credential_id"]),
        client_context=context,
        sign_count=document["sign_count"],
        up=document["up"],
        uv=document["uv"],
    )


@dataclass
class FIDO2HumanAuthenticator:
    """RHAMP-REQ-032 — the real ``HumanAuthenticator`` for exactly
    ``hpac.fido2.uv_presence.v2``. Mechanism-specific; never an approval
    mechanism (RHAMP-REQ-037).

    Bound at construction to one ``(principal_id, credential_id)`` and one
    CTAP2 provider (native in production; the deterministic NON_REAL
    fixture in CI — RHAMP-REQ-047/048/§63: the fixture is reachable only by
    explicit test construction).
    """

    principal_id: str
    credential_id: str
    provider: Ctap2Provider
    allow_credential_ids: tuple[bytes, ...]
    #: The digests + ids the ceremony binds into the canonical client context.
    invocation_id: str
    attempt_id: str

    MECHANISM_ID: Final[str] = FIDO2_MECHANISM_ID

    def describe(self) -> MechanismDescriptor:
        return MechanismDescriptor(
            mechanism_id=FIDO2_MECHANISM_ID,
            assurance_level=AssuranceLevel.PRINCIPAL_VERIFIED_INTENT,
            offline_capable=True,
            presence_support=True,
            verification_support="required",  # RHAMP-REQ-033 — UV is a floor.
            platform_compat=("macos", "linux"),
        )

    def status(self) -> MechanismStatus:
        try:
            available = self.provider.available()
        except Exception:  # noqa: BLE001
            available = False
        if not available:
            return MechanismStatus(MechanismStatusValue.UNAVAILABLE)
        return MechanismStatus(MechanismStatusValue.HEALTHY)

    # ── HPAC-REQ-049 challenge construction (RHAMP-REQ-023/074/079) ──

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def prepare_challenge(
        self,
        subject_digest: str,
        presentation_digest: str,
        *,
        issued_at: Optional[str] = None,
        ttl_seconds: int = RHAMP_CHALLENGE_MAX_TTL_SECONDS,
    ) -> Challenge:
        if ttl_seconds > RHAMP_CHALLENGE_MAX_TTL_SECONDS:
            raise RhampTerminalError(
                TerminalReasonCode.INTERNAL_VERIFICATION_ERROR,
                f"challenge TTL {ttl_seconds}s exceeds the RHAMP-001 v1.0 ceiling of {RHAMP_CHALLENGE_MAX_TTL_SECONDS}s",
            )
        issued = (
            datetime.fromisoformat(issued_at.removesuffix("Z") + "+00:00")
            if issued_at
            else self._now()
        )
        expires = issued + timedelta(seconds=ttl_seconds)
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        payload = {
            "domain_separator": CHALLENGE_DOMAIN_SEPARATOR,
            "challenge_version": CHALLENGE_VERSION,
            "proof_schema_version": PROOF_SCHEMA_VERSION,
            "principal_id": self.principal_id,
            "credential_id": self.credential_id,
            "approval_subject_digest": subject_digest,
            "trusted_presentation_digest": presentation_digest,
            # RHAMP-REQ-079: CSPRNG, >= 256 bits.
            "nonce": secrets.token_hex(32),
            "issued_at": issued.strftime(fmt),
            "expires_at": expires.strftime(fmt),
        }
        digest = canonical_digest(payload)
        return Challenge(challenge_digest=digest, **payload)

    # ── the native CTAP2 getAssertion ceremony (RHAMP-REQ-033/§33) ──

    def build_client_context(self, challenge: Challenge) -> RhampClientContext:
        return build_client_context(
            ceremony_kind="runtime-invocation-approval",
            challenge_digest=challenge.challenge_digest,
            approval_subject_digest=challenge.approval_subject_digest,
            trusted_presentation_digest=challenge.trusted_presentation_digest,
            principal_id=challenge.principal_id,
            credential_id=challenge.credential_id,
            invocation_id=self.invocation_id,
            attempt_id=self.attempt_id,
            nonce=challenge.nonce,
            issued_at=challenge.issued_at,
            expires_at=challenge.expires_at,
        )

    def run_assertion_ceremony(self, challenge: Challenge) -> AssertionEnvelope:
        """RHAMP-REQ-033 — build the canonical client context, drive the
        native CTAP2 ``getAssertion`` over ``client_data_hash``, the
        canonical ``allow_list``, and ``rp_id = "hpac.pcae.local"``, and
        return the closed assertion envelope (still **unverified**)."""

        if not self.allow_credential_ids:
            raise RhampTerminalError(
                TerminalReasonCode.CREDENTIAL_NOT_ACTIVE,
                "no active credential resolves to a canonical allowList entry",
            )
        context = self.build_client_context(challenge)
        result: GetAssertionResult = self.provider.get_assertion(
            client_data_hash=context.client_data_hash,
            allow_credential_ids=list(self.allow_credential_ids),
        )
        return AssertionEnvelope(
            authenticator_data=result.authenticator_data,
            signature=result.signature,
            raw_credential_id=result.raw_credential_id,
            client_context=context,
            sign_count=result.sign_count,
            up=result.up,
            uv=result.uv,
        )

    def verify_response(self, challenge: Challenge, response: bytes) -> ProofMaterial:
        """HPAC-REQ-032 — return **unverified-but-parsed** proof material.
        ``response`` is the CBOR/JSON-agnostic serialised envelope
        (:func:`encode_assertion_envelope` bytes). The HPAC verifier (§18)
        performs the real verification."""

        try:
            envelope = decode_assertion_envelope(response.decode("ascii"))
        except UnicodeDecodeError:
            envelope = decode_assertion_envelope(_b64u(response))
        return ProofMaterial(
            mechanism_id=FIDO2_MECHANISM_ID,
            challenge_digest=challenge.challenge_digest,
            assertion=encode_assertion_envelope(envelope),
            up=envelope.up,
            uv=envelope.uv,
            authenticated_at=challenge.issued_at,
        )

    def resolve_principal(self, verified_proof: ProofMaterial) -> tuple[str, str]:
        return (self.principal_id, self.credential_id)


# Structural Protocol conformance, exercised at import time so a signature
# drift fails immediately, not only inside a test run.
def _assert_protocol_conformance() -> None:
    from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider

    instance = FIDO2HumanAuthenticator(
        principal_id="hp-x",
        credential_id="hpc-x",
        provider=DeterministicCtap2Provider(),
        allow_credential_ids=(),
        invocation_id="iv-x",
        attempt_id="at-x",
    )
    assert isinstance(instance, HumanAuthenticator)


_assert_protocol_conformance()
