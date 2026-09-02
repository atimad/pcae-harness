"""RHAMP-001 v1.0 §37 — the real ``hpac.fido2.uv_presence.v2`` assertion
verification sequence (RHAMP-REQ-102/103).

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (merged RHAMP-REQ-156 ``.1R.30``
bundle). This is the pure verification core :mod:`pcae.core.hpac_verifier`
calls for the real mechanism branch — kept in its own module so the
cryptographic sequence is unit-testable in isolation and
``hpac_verifier.py``'s diff stays small.

Uses the pinned ``fido2`` library's primitives and **no custom
cryptography** (RHAMP-REQ-062/107). Every failure maps deterministically to
exactly one RHAMP-001 §49 ``terminal_reason_code`` (RHAMP-REQ-129).

RHAMP-REQ-103: this sequence is only ever invoked by ``hpac_verifier`` after
it has resolved every record as ``PRODUCTION`` and confirmed the resolved
``mechanism_id`` is in the §4 real allowlist. A ``FIXTURE_NON_REAL``
credential never reaches here.
"""

from __future__ import annotations

from pcae.core.human_authentication_proof import HumanAuthenticationProof
from pcae.core.human_authenticator import Challenge
from pcae.core.human_principal_registry import CredentialRecord
from pcae.core.hpac_rhamp_client_context import build_client_context
from pcae.core.hpac_rhamp_counter_state import CounterDecision, CounterState, evaluate_signcount
from pcae.core.hpac_rhamp_credential_sidecar import (
    Fido2CredentialSidecar,
    decode_raw_credential_id,
)
from pcae.core.hpac_rhamp_ctap2 import verify_assertion_signature_material
from pcae.core.hpac_rhamp_terminal_reasons import RhampTerminalError, TerminalReasonCode
from pcae.core.human_authenticator_fido2 import FIDO2_MECHANISM_ID, decode_assertion_envelope

__all__ = ["verify_real_fido2_assertion", "RealFido2AssertionResult"]


from dataclasses import dataclass


@dataclass(frozen=True)
class RealFido2AssertionResult:
    """A passing §37 real-assertion verification. ``counter_decision`` is
    ``accepted`` (a regression would have raised) and is what the verifier
    applies to the ``RHAMP-COUNTER-STATE/1.0`` record after step 10
    (RHAMP-REQ-071.3)."""

    counter_decision: CounterDecision
    observed_sign_count: int


def verify_real_fido2_assertion(
    *,
    credential: CredentialRecord,
    sidecar: Fido2CredentialSidecar,
    proof: HumanAuthenticationProof,
    challenge: Challenge,
    invocation_id: str,
    attempt_id: str,
    counter_state: CounterState,
) -> RealFido2AssertionResult:
    """Execute RHAMP-REQ-102 steps 1–6 (credential/sidecar cross-check,
    rpIdHash, signature, client-data, UP/UV, counter) for the real
    mechanism. Raises :class:`RhampTerminalError` on any failure; never a
    signature bypass.
    """

    if credential.mechanism_id != FIDO2_MECHANISM_ID:
        raise RhampTerminalError(
            TerminalReasonCode.MECHANISM_UNKNOWN,
            f"resolved CredentialRecord.mechanism_id is not the real RHAMP mechanism: {credential.mechanism_id!r}",
        )
    if proof.mechanism_id != FIDO2_MECHANISM_ID:
        raise RhampTerminalError(
            TerminalReasonCode.MECHANISM_UNKNOWN, "proof mechanism_id is not the real RHAMP mechanism"
        )

    # RHAMP-REQ-102 step 1 — credential lookup / principal ownership.
    if credential.principal_id != proof.principal_id:
        raise RhampTerminalError(
            TerminalReasonCode.CREDENTIAL_PRINCIPAL_MISMATCH,
            "credential is not bound to the resolved principal",
        )
    if sidecar.principal_id != credential.principal_id:
        raise RhampTerminalError(
            TerminalReasonCode.CREDENTIAL_PRINCIPAL_MISMATCH,
            "sidecar principal_id disagrees with the registry CredentialRecord",
        )

    # RHAMP-REQ-058 — sidecar / registry public-key cross-check.
    if sidecar.cose_public_key != credential.public_key:
        raise RhampTerminalError(
            TerminalReasonCode.PROTECTED_ROOT_INVALID,
            "sidecar cose_public_key disagrees with the registry public_key",
        )
    try:
        cose_public_key_bytes = bytes.fromhex(credential.public_key)
    except ValueError as exc:
        raise RhampTerminalError(
            TerminalReasonCode.INTERNAL_VERIFICATION_ERROR,
            f"registry public_key is not hex(cbor(COSE_Key)): {exc}",
        ) from exc

    envelope = decode_assertion_envelope(proof.assertion)

    # RHAMP-REQ-102 step 1 — raw credential id must match the sidecar.
    if envelope.raw_credential_id != decode_raw_credential_id(sidecar.raw_credential_id):
        raise RhampTerminalError(
            TerminalReasonCode.CREDENTIAL_PRINCIPAL_MISMATCH,
            "assertion raw_credential_id does not match the canonical sidecar",
        )

    # RHAMP-REQ-025 — reconstruct the canonical client-data object from
    # trusted state and reject any envelope-field disagreement.
    trusted_context = build_client_context(
        ceremony_kind="runtime-invocation-approval",
        challenge_digest=challenge.challenge_digest,
        approval_subject_digest=challenge.approval_subject_digest,
        trusted_presentation_digest=challenge.trusted_presentation_digest,
        principal_id=challenge.principal_id,
        credential_id=challenge.credential_id,
        invocation_id=invocation_id,
        attempt_id=attempt_id,
        nonce=challenge.nonce,
        issued_at=challenge.issued_at,
        expires_at=challenge.expires_at,
    )
    got = envelope.client_context
    if (
        got.ceremony_kind != trusted_context.ceremony_kind
        or got.context_identifier != trusted_context.context_identifier
        or got.domain_separator != trusted_context.domain_separator
        or got.mechanism_id != trusted_context.mechanism_id
    ):
        raise RhampTerminalError(
            TerminalReasonCode.CLIENT_DATA_CONTEXT_MISMATCH,
            "assertion client-data ceremony_kind / context_identifier is not the frozen constant",
        )
    if got.to_document() != trusted_context.to_document():
        raise RhampTerminalError(
            TerminalReasonCode.CLIENT_DATA_HASH_MISMATCH,
            "assertion client-data context does not match the canonical object reconstructed from trusted state",
        )

    # RHAMP-REQ-102 steps 2/3/5 — rpIdHash, signature, UP, UV.
    check = verify_assertion_signature_material(
        cose_public_key=cose_public_key_bytes,
        authenticator_data=envelope.authenticator_data,
        signature=envelope.signature,
        client_data_hash=trusted_context.client_data_hash,
    )
    if not check.rp_id_hash_ok:
        raise RhampTerminalError(
            TerminalReasonCode.RP_ID_HASH_MISMATCH,
            'authenticatorData.rpIdHash != SHA-256("hpac.pcae.local")',
        )
    if not check.signature_ok:
        raise RhampTerminalError(TerminalReasonCode.SIGNATURE_INVALID, "COSE signature verification failed")
    if not check.up:
        raise RhampTerminalError(TerminalReasonCode.USER_PRESENCE_MISSING, "FLAG.UP not set")
    if not check.uv:
        raise RhampTerminalError(
            TerminalReasonCode.USER_VERIFICATION_MISSING, "FLAG.UV not set (UP-only assertion — floor violation)"
        )

    # RHAMP-REQ-102 step 6 — the §20 signature-counter policy against the
    # §21 counter-state record. A regression rejects BEFORE any proof mints.
    decision = evaluate_signcount(counter_state, check.sign_count)
    if not decision.accepted:
        raise RhampTerminalError(
            TerminalReasonCode.SIGNATURE_COUNTER_REGRESSION,
            f"non-zero signature-counter regression: observed {check.sign_count} <= "
            f"last accepted {counter_state.last_accepted_meaningful}",
        )
    return RealFido2AssertionResult(counter_decision=decision, observed_sign_count=check.sign_count)
