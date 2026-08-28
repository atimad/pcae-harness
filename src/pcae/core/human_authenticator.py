"""
HPAC-001 v2.0 §10-§17, §20 — `HumanAuthenticator` mechanism-neutral
interface and its static/dynamic descriptor models.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3 (Layer 1-2 foundation). This module
freezes the interface's semantic responsibilities only (HPAC-REQ-033); it
contains no implementation, no authority-validation logic, no PB logic,
and no registry-mutation logic (HPAC-REQ-034/035). A real
`FIDO2HumanAuthenticator` (Phase 3) and the deterministic test double
(`human_authenticator_deterministic.py`, this phase) both implement this
same `Protocol`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


class MechanismStatusValue(str, Enum):
    """HPAC-REQ-037's closed dynamic-status vocabulary. Distinct from
    mechanism *registration* -- status is never conflated with it."""

    CONFIGURED = "configured"
    CREDENTIAL_AVAILABLE = "credential_available"
    VERIFIER_AVAILABLE = "verifier_available"
    HEALTHY = "healthy"
    UNAVAILABLE = "unavailable"
    REVOKED = "revoked"


class AssuranceLevel(str, Enum):
    """HPAC-REQ-059's closed assurance vocabulary. Each property is
    verified independently; none silently implies another."""

    ASSERTED = "ASSERTED"
    CREDENTIAL_PRESENCE = "CREDENTIAL_PRESENCE"
    PRINCIPAL_VERIFIED_INTENT = "PRINCIPAL_VERIFIED_INTENT"


@dataclass(frozen=True)
class MechanismDescriptor:
    """HPAC-REQ-040's static descriptor fields, mechanism-neutral (the
    exact field set named for the primary v2 FIDO2 mechanism; a
    deterministic test mechanism populates the same shape with its own
    non-real values, never with `hpac.fido2.uv_presence.v2`)."""

    mechanism_id: str
    assurance_level: AssuranceLevel
    offline_capable: bool
    presence_support: bool
    verification_support: str  # "required" | "optional" | "unsupported"
    platform_compat: tuple[str, ...]


@dataclass(frozen=True)
class MechanismStatus:
    status: MechanismStatusValue


@dataclass(frozen=True)
class Challenge:
    """HPAC-REQ-049's exact canonical challenge object. Nonce origin,
    uniqueness, and lifetime are the trusted challenge-construction
    component's responsibility (HPAC-REQ-050), never the authenticator's."""

    domain_separator: str
    challenge_version: str
    proof_schema_version: str
    principal_id: str
    credential_id: str
    approval_subject_digest: str
    trusted_presentation_digest: str
    nonce: str
    issued_at: str
    expires_at: str
    challenge_digest: str


@dataclass(frozen=True)
class ProofMaterial:
    """The **untrusted, unverified** parsed output of
    `HumanAuthenticator.verify_response` -- HPAC-001's own "Untrusted
    parsed proof" layer (plan §17 item 2), distinct from a canonical
    `HumanAuthenticationProof` (HPAC-REQ-052). No consumer may treat this
    type as trusted authority: it is transient input to the HPAC verifier
    (§18, Phase 3, out of this phase's scope)."""

    mechanism_id: str
    challenge_digest: str
    assertion: str  # base64url mechanism bytes
    up: bool
    uv: bool
    authenticated_at: str


@runtime_checkable
class HumanAuthenticator(Protocol):
    """HPAC-REQ-032's minimal, non-collapsible interface. No
    implementation of this Protocol may itself decide authority
    (HPAC-REQ-034) or become a Permission Broker input (HPAC-REQ-035)."""

    def describe(self) -> MechanismDescriptor:
        """Return this mechanism's static descriptor (§14)."""
        ...

    def status(self) -> MechanismStatus:
        """Return this mechanism's current dynamic status (§13)."""
        ...

    def prepare_challenge(self, subject_digest: str, presentation_digest: str) -> Challenge:
        """Bind a fresh, single-use challenge to an exact approval
        subject/presentation digest (§16)."""
        ...

    def verify_response(self, challenge: Challenge, response: bytes) -> ProofMaterial:
        """Return unverified-but-parsed proof material only. The HPAC
        verifier (§18, a separate component, Phase 3) is what turns this
        into a trusted `AuthenticatedHumanPrincipal` -- this method never
        performs that verification itself."""
        ...

    def resolve_principal(self, verified_proof: ProofMaterial) -> tuple[str, str]:
        """Given proof material, return the `(principal_id,
        credential_id)` pair it claims to have been produced under. This
        is a claim extracted from the proof, not itself a trust
        decision -- the caller (Phase 3's verifier) still independently
        resolves and checks registry state."""
        ...
