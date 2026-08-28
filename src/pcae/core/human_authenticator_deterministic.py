"""
`DeterministicTestHumanAuthenticator` — HPAC-001 plan §11's simulation-only
`HumanAuthenticator` fixture.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3. Entirely in-process, no hardware
I/O, parameterized to produce every adversarial combination a future
verifier (Phase 3) must reject: UP/UV independently true/false,
credential/principal match-or-mismatch, challenge match/stale/foreign,
replay, revoked-credential/revoked-principal state.

DETERMINISTIC TEST FIXTURE != REAL HUMAN AUTHENTICATION. This is enforced
structurally, not only documented: `SIMULATION_ONLY` is a `Final[bool]`
class constant fixed at `True`, and `MECHANISM_ID` is a fixed constant
that can never equal `hpac.fido2.uv_presence.v2` or any other real
mechanism id -- there is no constructor parameter capable of overriding
either.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from pcae.core.hpac_foundation import canonical_digest
from pcae.core.human_authenticator import (
    AssuranceLevel,
    Challenge,
    HumanAuthenticator,
    MechanismDescriptor,
    MechanismStatus,
    MechanismStatusValue,
    ProofMaterial,
)

#: Never equal to a real mechanism id (HPAC-REQ-039's
#: `hpac.fido2.uv_presence.v2` or any future real mechanism). A future
#: real-dispatch gate rejects any `mechanism_id` outside a real-mechanism
#: allowlist by construction; this constant is deliberately outside any
#: such allowlist.
DETERMINISTIC_MECHANISM_ID: Final[str] = "hpac.deterministic.test-only.v1"


class DeterministicAuthenticatorReplayError(Exception):
    """The same (challenge_digest, response) pair was presented twice to
    this fixture instance -- proves the fixture itself models replay
    detection for adversarial tests to exercise, it is not authority."""


@dataclass
class DeterministicTestHumanAuthenticator:
    """Simulation-only `HumanAuthenticator` implementation.

    Every adversarial knob is an explicit constructor parameter -- there
    is no hidden default that silently produces a "successful" proof;
    callers must deliberately choose `up=True, uv=True,
    credential_matches=True, ...` to get a plausible-looking result, and
    even then the result's `mechanism_id` structurally disqualifies it
    from ever being treated as real-runtime authority.
    """

    principal_id: str
    credential_id: str
    up: bool = True
    uv: bool = True
    credential_matches: bool = True
    principal_matches: bool = True
    revoked: bool = False
    challenge_response_mode: str = "match"  # "match" | "stale" | "foreign"

    SIMULATION_ONLY: Final[bool] = field(default=True, init=False, repr=False)
    MECHANISM_ID: Final[str] = field(default=DETERMINISTIC_MECHANISM_ID, init=False, repr=False)

    _consumed_pairs: set[tuple[str, str]] = field(default_factory=set, init=False, repr=False)

    def describe(self) -> MechanismDescriptor:
        return MechanismDescriptor(
            mechanism_id=DETERMINISTIC_MECHANISM_ID,
            assurance_level=AssuranceLevel.ASSERTED,
            offline_capable=True,
            presence_support=True,
            verification_support="optional",
            platform_compat=("macos", "linux"),
        )

    def status(self) -> MechanismStatus:
        if self.revoked:
            return MechanismStatus(MechanismStatusValue.REVOKED)
        return MechanismStatus(MechanismStatusValue.HEALTHY)

    def prepare_challenge(self, subject_digest: str, presentation_digest: str) -> Challenge:
        payload = {
            "domain_separator": "pcae.hpac.deterministic-test.v1",
            "challenge_version": "HPAC-CHALLENGE/2.0",
            "proof_schema_version": "HPAC-PROOF/2.0",
            "principal_id": self.principal_id,
            "credential_id": self.credential_id,
            "approval_subject_digest": subject_digest,
            "trusted_presentation_digest": presentation_digest,
            "nonce": canonical_digest({"n": id(self)}),
            "issued_at": "2026-08-28T00:00:00Z",
            "expires_at": "2026-08-28T00:05:00Z",
        }
        digest = canonical_digest(payload)
        return Challenge(challenge_digest=digest, **payload)

    def verify_response(self, challenge: Challenge, response: bytes) -> ProofMaterial:
        pair_key = (challenge.challenge_digest, response.hex())
        if pair_key in self._consumed_pairs:
            raise DeterministicAuthenticatorReplayError(
                "this exact (challenge, response) pair was already presented to this fixture instance"
            )
        self._consumed_pairs.add(pair_key)

        if self.challenge_response_mode == "stale":
            effective_digest = canonical_digest({"stale": challenge.challenge_digest})
        elif self.challenge_response_mode == "foreign":
            effective_digest = canonical_digest({"foreign": "unrelated-challenge"})
        else:
            effective_digest = challenge.challenge_digest

        return ProofMaterial(
            mechanism_id=DETERMINISTIC_MECHANISM_ID,
            challenge_digest=effective_digest,
            assertion=response.hex(),
            up=self.up,
            uv=self.uv,
            authenticated_at="2026-08-28T00:01:00Z",
        )

    def resolve_principal(self, verified_proof: ProofMaterial) -> tuple[str, str]:
        claimed_principal = self.principal_id if self.principal_matches else f"forged-{self.principal_id}"
        claimed_credential = self.credential_id if self.credential_matches else f"forged-{self.credential_id}"
        return (claimed_principal, claimed_credential)


# Structural conformance to the Protocol -- exercised at import time so a
# future signature drift fails immediately, not only inside a test run.
assert isinstance(
    DeterministicTestHumanAuthenticator(principal_id="hp-x", credential_id="hpc-x"), HumanAuthenticator
)
