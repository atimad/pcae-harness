"""HATP PIV Hardware Provider -- Phase 149O.2, Wave 5 (documented
fallback strategy per 149O.1D plan §23).

149O.1D plan §23's stop condition: "if the FIDO2 spike (§23) cannot
bind HATP's exact canonical payload as the signed challenge, switch to
the PIV fallback strategy before continuing." The FIDO2 spike in
`hatp_fido2_provider.py` succeeded (see that module's docstring for the
exact demonstration) -- PIV therefore remains, per the plan's own
conditional wording, "documented fallback," not a strategy this phase
is required to bring to full conformance.

This module still defines PIV's structural interface (item 55: "derive
exact slot, certificate, key algorithm, PIN/touch policy, attestation
capability from plan/provider assumptions -- do not invent generic
smart-card behavior"), so a future phase has a concrete, narrow surface
to complete rather than starting from nothing. It does NOT implement a
real PKCS#11/smart-card binding: no `pyscard`, `python-pkcs11`, or
platform middleware dependency is added by this phase (149O.1D plan
§25 lists this as the anticipated PIV dependency class, contingent on
PIV actually being needed -- it is not, this phase, per the spike
result above). Per item 56/57/137:

    "If the hardware/API cannot prove that requirement: PIV fallback
    may be structurally unavailable rather than silently accepted."
    "If PIV cannot satisfy Root2A attestation equivalently to FIDO2:
    document and fail readiness accordingly. Do not weaken HATP to make
    fallback pass."

`discover_piv()` and `PivHardwareProvider` are therefore honest about
this: every method unconditionally reports/raises unavailability. No
method fabricates a successful PIV signing or verification path. This
is a deliberate, documented `NOT_CONFORMANT (this phase)` posture, not
an oversight -- see the phase documentation's PIV capability-matrix row.
"""
from __future__ import annotations

from pcae.core.hatp_providers import (
    HATP_HARDWARE_PROVIDER_V1,
    HardwareProviderAvailability,
    HardwareProviderCapabilities,
    HardwareProviderConformance,
    HATPProviderUnavailableError,
    HATPProviderVerificationOutcome,
    ProviderAssertion,
)

PROTOCOL_NAME = "PIV"

_UNAVAILABLE_REASON = (
    "PIV fallback is structurally deferred this phase (149O.1D plan §23's FIDO2 spike"
    " succeeded, so PIV was not required to reach full conformance); no PKCS#11/smart-card"
    " library is installed or selected, and no PIV hardware is present in this development"
    " environment. See docs/PHASE_149O_2_HATP_HARDWARE_PROVIDER_IMPLEMENTATION.md for the"
    " capability-matrix disposition (NOT_CONFORMANT, this phase)."
)


def discover_piv() -> HardwareProviderAvailability:
    """Always reports unavailable, honestly (item 63/89/137): no
    PKCS#11 library dependency exists in this codebase to probe with."""

    return HardwareProviderAvailability(
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        protocol_name=PROTOCOL_NAME,
        library_installed=False,
        device_detected=False,
        notes=(_UNAVAILABLE_REASON,),
    )


class PivHardwareProvider:
    """Structural placeholder implementing the same shapes as
    `Fido2HardwareProvider` (`HATPHardwareSigner` +
    `HATPProofVerifierProvider`, both structurally) so a future phase
    can complete it without changing any caller. Every method
    unconditionally fails closed -- there is no code path here that
    could accidentally accept a software key or an unproven-presence
    signature (items 13/17/56)."""

    def capabilities(self) -> HardwareProviderCapabilities:
        return HardwareProviderCapabilities(
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            protocol_name=PROTOCOL_NAME,
            non_exportable_key=False,
            fresh_touch_per_operation=False,
            credential_identity=False,
            signature_verification=False,
            device_attestation=False,
            hatp_conformant=HardwareProviderConformance.NOT_CONFORMANT,
            notes=(_UNAVAILABLE_REASON,),
        )

    def credential_identity(self) -> str:
        raise HATPProviderUnavailableError(_UNAVAILABLE_REASON)

    def request_signature(
        self,
        payload: bytes,
        *,
        signer_key_id: str,
        provider_profile: str,
        presence_timeout_s: float = 30.0,
    ) -> ProviderAssertion:
        raise HATPProviderUnavailableError(_UNAVAILABLE_REASON)

    def verify(
        self,
        *,
        canonical_payload: bytes,
        signer_key_id: str,
        provider_profile: str,
        assertion: bytes,
    ) -> HATPProviderVerificationOutcome:
        # Deliberately fail-closed rather than raise here: `verify()`'s
        # contract (see `HATPProofVerifierProvider.verify`) is
        # "MUST NOT raise for an invalid/unrecognized assertion." A
        # structurally-unavailable provider treats every assertion as
        # unrecognized, not as a provider-level fault.
        return HATPProviderVerificationOutcome(signature_valid=False, human_presence_proven=False)
