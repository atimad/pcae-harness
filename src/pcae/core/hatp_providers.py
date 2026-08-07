"""HATP Provider-Neutral Verification Interface + Deterministic Test
Provider -- Phase 149O.1I, Wave 4 (subsystems E/K of the 149O.1D plan,
narrowly scoped to what Wave 4's verification engine needs to be
independently testable without hardware).

This module defines only the *interface* a hardware provider (Wave 5:
FIDO2 primary, PIV fallback, per 149O.1D plan §23) will implement, plus a
deterministic in-memory test provider (HATP-REQ-022, subsystem K). It
implements NO real hardware/protocol binding -- no `fido2`, `pyscard`, or
`ykman` dependency is introduced (HATP-REQ-021: a local software signing
key never silently substitutes for a required hardware signer; the test
provider below is explicitly non-production, never selectable as
`HATP_HARDWARE_PROVIDER_V1`-compliant production authority).

Mandatory boundary, restated from the governing phase prompt and
HATP-001 itself:

    A provider-neutral verification *outcome* (signature validity, human
    presence, attestation) is evidence a verifier consumes -- it is not
    itself a HATP verification status, not an authorization, and not an
    approval. `pcae.core.human_approval_trusted_provenance.verify_hatp_proof`
    (Wave 4) is the sole place that combines this evidence with protected
    trust-store facts to reach a closed-vocabulary HATP verification
    status.

`TestHATPProofVerifierProvider` (K) cannot make production HATP trust
reachable: no production code path constructs it, references it by name,
or accepts it as a default/fallback (HATP-REQ-022). It is a plain
importable class with no registration mechanism, no environment-variable
selection, and no CLI flag -- there is structurally nothing for a
production caller to "accidentally" select.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Protocol, Tuple, runtime_checkable


@dataclass(frozen=True)
class HATPProviderVerificationOutcome:
    """Provider-neutral verification facts returned by a
    `HATPProofVerifierProvider.verify()` call. This is raw evidence, not
    a HATP verification status (HATP-REQ-078) and not an authorization
    fact -- it carries no `approved`/`authorized`/`valid` field. The
    Wave-4 verifier combines these facts with protected trust-store
    lookups to reach a closed-vocabulary status.
    """

    signature_valid: bool
    human_presence_proven: bool
    #: `None` means the provider profile does not perform/require device
    #: attestation (HATP-REQ-023-025 leave attestation optional per
    #: profile); `True`/`False` means the provider evaluated it.
    attestation_valid: Optional[bool] = None


@runtime_checkable
class HATPProofVerifierProvider(Protocol):
    """Provider-neutral verification interface (HATP-REQ-019(e),
    HATP-REQ-025, HATP-REQ-077): a concrete provider translates its own
    protocol-specific assertion bytes into provider-neutral facts. The
    Wave-4 verifier never inspects provider-internal assertion formats
    directly, and never trusts a public key or attestation root supplied
    by the proof itself -- only this interface's return value.
    """

    def verify(
        self,
        *,
        canonical_payload: bytes,
        signer_key_id: str,
        provider_profile: str,
        assertion: bytes,
    ) -> HATPProviderVerificationOutcome:
        """Verify `assertion` was produced over exactly `canonical_payload`
        by the credential identified by `signer_key_id` under
        `provider_profile`. MUST NOT raise for an invalid/unrecognized
        assertion -- return `signature_valid=False` instead; raising is
        reserved for genuine provider-level failure (e.g. hardware I/O
        error), which the caller (Wave 4 verifier) treats as fail-closed,
        never as an accidental pass-through."""
        ...


def _fake_assertion(canonical_payload: bytes, signer_key_id: str, provider_profile: str) -> bytes:
    """Deterministic, non-cryptographic stand-in for a real hardware
    signature: a SHA-256 digest binding the exact canonical payload
    bytes, signer identity, and provider profile. Test-only -- carries no
    security property beyond exact-byte sensitivity, which is precisely
    what Wave-4 test-provider fixtures need to exercise mutation/replay
    rejection deterministically."""

    return hashlib.sha256(
        canonical_payload + b"\x00" + signer_key_id.encode("utf-8") + b"\x00" + provider_profile.encode("utf-8")
    ).digest()


class TestHATPProofVerifierProvider:
    """Deterministic, explicitly non-production in-memory fake provider
    (HATP-REQ-022, subsystem K). Exists solely so Wave 4's verification
    engine can be exercised without a real hardware signer.

    `sign()` is a *test-fixture helper*, not part of the production
    `HATPProofVerifierProvider` interface -- it lets a test construct a
    genuine, byte-exact "assertion" for a given canonical payload so that
    mutating any signed field of a proof (and therefore its canonical
    bytes) provably invalidates previously-produced evidence, exactly as
    a real hardware signature would.

    This class is never constructed by any `src/pcae/core/*.py` module
    other than this one, and `human_approval_trusted_provenance.py`
    imports only the `HATPProofVerifierProvider` Protocol from this
    module, never this class -- see the Wave-4 no-production-activation
    test in `tests/test_hatp_verification_engine.py`.
    """

    #: Not a pytest test class despite the `Test`-prefixed name (which
    #: mirrors HATP-001's own "test provider" terminology, HATP-REQ-022) --
    #: silences pytest's collection heuristic.
    __test__ = False

    def __init__(
        self,
        *,
        human_presence_proven: bool = True,
        attestation_valid: Optional[bool] = None,
        raise_on_verify: Optional[BaseException] = None,
    ) -> None:
        self.human_presence_proven = human_presence_proven
        self.attestation_valid = attestation_valid
        self.raise_on_verify = raise_on_verify
        self.received_payloads: List[bytes] = []

    def sign(self, canonical_payload: bytes, *, signer_key_id: str, provider_profile: str) -> bytes:
        """Test-fixture helper: produce a fake assertion that `verify()`
        (this same instance) will accept for exactly these bytes/signer/
        profile, and no other combination."""

        return _fake_assertion(canonical_payload, signer_key_id, provider_profile)

    def verify(
        self,
        *,
        canonical_payload: bytes,
        signer_key_id: str,
        provider_profile: str,
        assertion: bytes,
    ) -> HATPProviderVerificationOutcome:
        self.received_payloads.append(canonical_payload)
        if self.raise_on_verify is not None:
            raise self.raise_on_verify
        expected = _fake_assertion(canonical_payload, signer_key_id, provider_profile)
        return HATPProviderVerificationOutcome(
            signature_valid=(assertion == expected),
            human_presence_proven=self.human_presence_proven,
            attestation_valid=self.attestation_valid,
        )


# ═══════════════════════════════════════════════════════════════════════════
# Wave 5 -- Real Hardware Provider Abstraction (Phase 149O.2)
# ═══════════════════════════════════════════════════════════════════════════
#
# Everything below extends the Wave-4 verification interface above with the
# production signing-side abstraction, discovery, and factory machinery a
# real hardware provider needs (149O.1D plan §23, HATP-REQ-019..025).
#
# Nothing below imports `fido2`, `cryptography`, or any other hardware/
# crypto library at module level -- this module remains importable with
# zero optional dependencies installed and with no hardware attached
# (no import-time hardware failure, no import-time device probe). Concrete
# provider implementations live in `hatp_fido2_provider.py` /
# `hatp_piv_provider.py` and are imported lazily, only from inside
# `discover_hardware_providers()` / `create_production_hardware_provider()`.

#: Frozen provider profile name (HATP-REQ-019): "defined by required
#: security properties, not by vendor or protocol branding." A conformant
#: FIDO2 adapter and a conformant PIV adapter may legitimately claim this
#: same profile string -- the Wave-2 trust store's per-signer
#: `provider_profile` field is what's authoritative, not a protocol tag.
HATP_HARDWARE_PROVIDER_V1 = "HATP_HARDWARE_PROVIDER_V1"

#: Closed allowlist consulted by `create_production_hardware_provider`.
#: Never includes any test/fake profile name (HATP-REQ-022).
_PRODUCTION_HARDWARE_PROVIDER_PROFILES = (HATP_HARDWARE_PROVIDER_V1,)


class HATPHardwareProviderError(Exception):
    """Base class for Wave-5 hardware-provider-layer errors. Distinct
    from `HATPTrustStoreError` (Wave 2) and from `HumanApprovalProvenanceError`
    family (Wave 3/4) -- this module stays independent of both."""


class HATPProviderUnavailableError(HATPHardwareProviderError):
    """No compatible library and/or device is available. Raised by
    discovery/factory functions; never papered over as a successful
    result (item 63/89: report unavailable honestly, never fabricate)."""


class HATPProviderCancelledError(HATPHardwareProviderError):
    """The human cancelled the presence/touch request, or it timed out
    (items 68-69). MUST NOT be silently treated as a valid assertion."""


class HATPProviderDeviceError(HATPHardwareProviderError):
    """A genuine hardware/transport failure (I/O error, device removed
    mid-operation, transport/protocol exception) (items 67, 70). Distinct
    from an invalid/unrecognized assertion, which `verify()` MUST NOT
    raise for -- see `HATPProofVerifierProvider.verify` above."""


class HardwareProviderConformance(str, Enum):
    """Item 138's required per-provider verdict vocabulary. A *design*
    verdict, independent of whether a physical device happens to be
    attached to this machine right now -- that is a separate fact,
    `HardwareProviderAvailability.device_detected`."""

    CONFORMANT = "CONFORMANT"
    CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS = "CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS"
    NOT_CONFORMANT = "NOT_CONFORMANT"


@dataclass(frozen=True)
class HardwareProviderCapabilities:
    """Item 58's capability matrix, as a first-class factual object
    rather than only prose. `hatp_conformant` MUST NOT describe an
    unavailable capability as implemented (item 138)."""

    provider_profile: str
    protocol_name: str
    non_exportable_key: bool
    fresh_touch_per_operation: bool
    credential_identity: bool
    signature_verification: bool
    device_attestation: bool
    hatp_conformant: HardwareProviderConformance
    notes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class HardwareProviderAvailability:
    """Discovery facts only (item 34): availability, never trust, never
    itself a readiness or authorization claim."""

    provider_profile: str
    protocol_name: str
    library_installed: bool
    device_detected: bool
    notes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ProviderAssertion:
    """Immutable, opaque-to-Wave-4 evidence produced by a real signing
    operation (item 29). `evidence` is that provider's own strictly-
    versioned, closed-schema serialization -- see each concrete provider
    module for its exact format (items 30-32). This is the raw output of
    a *signing* request; it is not itself a `HATPProviderVerificationOutcome`
    and is consumed only by that same provider's own `verify()`."""

    credential_id: str
    provider_profile: str
    algorithm: str
    evidence: bytes


@runtime_checkable
class HATPHardwareSigner(Protocol):
    """Production signing-request interface (items 27-28): kept
    deliberately separate from the verification-only
    `HATPProofVerifierProvider` above so a caller cannot conflate "can
    sign" with "can (self-)verify." No HATP-001 symbol defines this
    exact shape -- it is Wave-5's own narrow addition, not a frozen
    contract interface; `HATPProofVerifierProvider.verify` remains the
    sole frozen-contract-adjacent surface."""

    def capabilities(self) -> HardwareProviderCapabilities: ...

    def credential_identity(self) -> str:
        """Stable key/credential identifier (HATP-REQ-019(d)), usable
        for enrollment by a future Wave-2/7 administrative surface. This
        method only reports the identity -- it enrolls nothing itself
        (item 12: enrollment substrate is out of Wave-5 scope)."""
        ...

    def request_signature(
        self,
        payload: bytes,
        *,
        signer_key_id: str,
        provider_profile: str,
        presence_timeout_s: float = 30.0,
    ) -> ProviderAssertion:
        """Request a fresh, hardware-enforced human-presence signing
        operation over `payload` -- the exact
        `canonicalize_hatp_proof_payload(proof)` bytes (item 8/10: no
        second canonicalizer; a provider derives whatever digest its own
        protocol needs from these bytes itself, never from a
        caller-supplied pre-digested value, and never rebuilds proof
        JSON independently).

        MUST raise `HATPProviderCancelledError` on user cancellation or
        presence timeout, and `HATPProviderDeviceError` on a genuine
        hardware/transport fault (items 68-71) -- MUST NOT return an
        evidence object papering over either failure, and MUST NOT
        accept or honor any caller-supplied presence boolean (item 17)."""
        ...


def discover_hardware_providers() -> Tuple[HardwareProviderAvailability, ...]:
    """Report availability facts for every hardware-provider protocol
    Wave 5 defines. Availability only -- never trust, never a readiness
    claim (item 34/79). Never raises for a missing optional dependency
    or absent device; reports the fact instead (item 63)."""

    results: List[HardwareProviderAvailability] = []

    try:
        from pcae.core.hatp_fido2_provider import discover_fido2 as _discover_fido2
    except ImportError as exc:
        results.append(
            HardwareProviderAvailability(
                provider_profile=HATP_HARDWARE_PROVIDER_V1,
                protocol_name="FIDO2",
                library_installed=False,
                device_detected=False,
                notes=(f"fido2_library_not_installed:{exc.__class__.__name__}",),
            )
        )
    else:
        results.append(_discover_fido2())

    try:
        from pcae.core.hatp_piv_provider import discover_piv as _discover_piv
    except ImportError as exc:
        results.append(
            HardwareProviderAvailability(
                provider_profile=HATP_HARDWARE_PROVIDER_V1,
                protocol_name="PIV",
                library_installed=False,
                device_detected=False,
                notes=(f"piv_library_not_installed:{exc.__class__.__name__}",),
            )
        )
    else:
        results.append(_discover_piv())

    return tuple(results)


def create_production_hardware_provider(
    provider_profile: str,
    *,
    allow_piv_fallback: bool = False,
) -> "HATPProofVerifierProvider":
    """Production factory (item 77): resolves ONLY a contract-approved
    provider profile string to a real provider instance. Never resolves
    `TestHATPProofVerifierProvider` -- that class is not imported by
    this function, this module's import graph, or anything it calls
    (item 78/112). Raises `HATPProviderUnavailableError` for any
    unrecognized profile string, missing optional dependency, or absent
    device; never silently falls back to a weaker/software provider
    (item 21/113).

    FIDO2 is always attempted first (primary, per 149O.1D plan §23).
    PIV is attempted only if `allow_piv_fallback=True` is passed
    explicitly by the caller -- an explicit, observable fallback (item
    6/7), never an automatic/silent one."""

    if provider_profile not in _PRODUCTION_HARDWARE_PROVIDER_PROFILES:
        raise HATPProviderUnavailableError(f"unrecognized production provider profile: {provider_profile!r}")

    try:
        from pcae.core.hatp_fido2_provider import Fido2HardwareProvider
    except ImportError as exc:
        fido2_error: Optional[BaseException] = exc
    else:
        return Fido2HardwareProvider()

    if not allow_piv_fallback:
        raise HATPProviderUnavailableError(f"fido2 provider unavailable and PIV fallback not requested: {fido2_error}")

    try:
        from pcae.core.hatp_piv_provider import PivHardwareProvider
    except ImportError as exc:
        raise HATPProviderUnavailableError(
            f"fido2 provider unavailable ({fido2_error}); piv fallback also unavailable: {exc}"
        ) from exc
    return PivHardwareProvider()
