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
from typing import List, Optional, Protocol, runtime_checkable


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
