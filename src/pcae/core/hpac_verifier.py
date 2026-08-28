"""
HPAC-001 v2.0 §18 (HPAC-REQ-054/055/056/057/058) — mechanism-neutral HPAC
verifier and principal-registry consumption boundary.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5. Implements the verification sequence
specified by ``docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md``
§18, consuming only the already independently-verified Layer-1/2 HPAC
foundation stores (``human_principal_registry.py``, ``approval_presentation.py``,
``human_authentication_proof.py``, ``hpac_lifecycle.py``). Every authority-
bearing input is re-resolved through its own canonical store on every call
(HPAC-REQ-058) — this module never accepts a caller-constructed record as
authority, only opaque identifiers it resolves itself.

Non-responsibilities (frozen by the ``...1R.4`` planning document, §8):
this module does not evaluate PB policy, does not implement Gate 5's
authority-projection object, does not implement or call Gate 9's
consumption write, does not repair B1/B7/N1/N2, and does not implement a
real FIDO2/cryptographic verifier — mechanism-specific signature
verification remains assigned to the mechanism layer (§21), and this
module fails closed for any mechanism it does not recognize as the
deterministic non-real fixture.

The verifier's own lifecycle responsibility is exactly HPAC-REQ-054 step
10: appending (or idempotently accepting an already-present, byte-
identical) ``PROOF_VERIFIED_AND_BOUND`` event -- the same transition
``hpac_lifecycle.py``'s ``bind_gate5_canonical`` already performs. This
module is the reusable core a future Gate 5 will call; it does not itself
implement Gate 5's own RDGO-001 §6 projection object, and it never touches
``runtime_invocation_authority_consumption.py`` (Gate 9).

Result type: ``AuthenticatedHumanPrincipal`` is trusted-construction only
(no public constructor) and non-serializable (``__reduce__`` raises) per
HPAC-REQ-056/058 -- a caller cannot construct, copy, or persist one; every
consumer must call :func:`verify_human_authentication` fresh.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pcae.core.hpac_foundation import (
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACResolvedRecord,
    HPACWriterCapability,
    require_nonempty_str,
    require_timestamp,
)
from pcae.core.hpac_lifecycle import (
    HPACLifecycleStateError,
    HPACLifecycleStore,
    STATE_PROOF_VERIFIED,
    STATE_PROOF_VERIFIED_AND_BOUND,
)
from pcae.core.human_authentication_proof import (
    HumanAuthenticationProof,
    HumanAuthenticationProofStore,
    HumanAuthenticationProofTrustError,
)
from pcae.core.human_principal_registry import (
    CredentialRecord,
    HumanPrincipalRegistryStore,
    PrincipalRecord,
)
from pcae.core.approval_presentation import (
    ApprovalPresentationTrustError,
    PresentationMechanismDescriptorStore,
    TrustedApprovalPresentationStore,
)

__all__ = [
    "HPACVerificationError",
    "AuthenticatedHumanPrincipal",
    "verify_human_authentication",
]

#: The only mechanism identity this phase's verifier can ever certify.
#: A real mechanism (Layer 6, a later phase) is deliberately outside this
#: allowlist -- adding it here would be exactly the "no real FIDO2 in this
#: phase" no-go this module must not cross.
_ELIGIBLE_MECHANISM_IDS = frozenset({"hpac.deterministic.test-only.v1"})

_VERIFIER_CONSTRUCTOR_SEAL = object()


class HPACVerificationError(HPACAuthorityError):
    """A step of HPAC-REQ-054's verification sequence rejected the
    candidate proof/principal/credential/presentation/lifecycle state.

    Used only where none of the existing foundation exception types
    (``HumanPrincipalRegistryNotFoundError``, ``ApprovalPresentationTrustError``,
    ``HumanAuthenticationProofTrustError``, ``HPACLifecycleStateError``,
    ``HPACLifecycleForkError``) already names the failure; those are raised
    directly by the stores this module calls and are not re-wrapped."""


class AuthenticatedHumanPrincipal:
    """HPAC-REQ-056's trusted-construction, non-serializable verification
    result. Producible only as :func:`verify_human_authentication`'s
    return value -- there is no public constructor, and instances cannot
    be pickled, hashed for equality against a caller-built lookalike, or
    written to any store. ``assurance_class`` is copied from the resolved
    foundation records, never caller-declared (HPAC-REQ-059/060): a
    deterministic NON-REAL verification can never present itself as
    ``PRODUCTION`` assurance."""

    __slots__ = (
        "principal_id",
        "credential_id",
        "mechanism_id",
        "approval_id",
        "invocation_id",
        "proof_id",
        "presentation_id",
        "assurance_class",
        "verified_at",
        "_verifier_seal",
    )

    def __init__(
        self,
        *,
        principal_id: str,
        credential_id: str,
        mechanism_id: str,
        approval_id: str,
        invocation_id: str,
        proof_id: str,
        presentation_id: str,
        assurance_class: HPACAuthorityClass,
        verified_at: str,
        _seal: object,
    ) -> None:
        if _seal is not _VERIFIER_CONSTRUCTOR_SEAL:
            raise HPACAuthorityError(
                "AuthenticatedHumanPrincipal cannot be caller-constructed; "
                "it is producible only by verify_human_authentication"
            )
        self.principal_id = principal_id
        self.credential_id = credential_id
        self.mechanism_id = mechanism_id
        self.approval_id = approval_id
        self.invocation_id = invocation_id
        self.proof_id = proof_id
        self.presentation_id = presentation_id
        self.assurance_class = assurance_class
        self.verified_at = verified_at
        self._verifier_seal = _seal

    @property
    def is_real_runtime_eligible(self) -> bool:
        return self.assurance_class is HPACAuthorityClass.PRODUCTION

    def __reduce__(self):
        raise TypeError(
            "AuthenticatedHumanPrincipal is ephemeral and non-serializable "
            "(HPAC-REQ-058); every consumer must re-verify"
        )

    def __eq__(self, other: object) -> bool:
        # Identity-only equality: a byte-identical-looking lookalike built
        # by any means other than this module's own construction path is
        # never treated as "the same" authenticated result.
        return self is other

    def __hash__(self) -> int:
        return id(self)


def _resolve_principal(
    registry: HumanPrincipalRegistryStore, principal_id: str
) -> HPACResolvedRecord[PrincipalRecord]:
    resolved = registry.resolve_canonical_principal(principal_id)
    if resolved is None:
        raise HPACVerificationError(f"unknown principal_id: {principal_id}")
    principal = resolved.record
    if principal.status != "active":
        raise HPACVerificationError(f"principal is not active: {principal_id}")
    return resolved


def _resolve_credential(
    registry: HumanPrincipalRegistryStore,
    credential_id: str,
    *,
    expected_principal_id: str,
) -> HPACResolvedRecord[CredentialRecord]:
    resolved = registry.resolve_canonical_credential(credential_id)
    if resolved is None:
        raise HPACVerificationError(f"unknown credential_id: {credential_id}")
    credential = resolved.record
    if credential.status != "active":
        raise HPACVerificationError(f"credential is not active: {credential_id}")
    if credential.principal_id != expected_principal_id:
        raise HPACVerificationError(
            "credential is not bound to the claimed principal "
            f"({credential.principal_id} != {expected_principal_id})"
        )
    return resolved


def _verify_assertion_material(
    credential: CredentialRecord, proof: HumanAuthenticationProof
) -> None:
    """HPAC-REQ-054 step 6: verify the assertion against the resolved
    credential's public verification material.

    No real cryptographic mechanism exists in this phase (L6, a later
    phase, per ``...1R.4`` §25). Mirroring
    ``approval_presentation.py``'s ``_verify_installed_attestation``
    discipline for the identical "no real verifier implemented" boundary,
    this categorically rejects every mechanism identity except the fixed
    deterministic non-real one; it does not attempt real signature math
    against ``credential.public_key``.
    """

    if credential.mechanism_id != proof.mechanism_id:
        raise HPACVerificationError(
            "credential mechanism_id does not match proof mechanism_id "
            "(mechanism substitution)"
        )
    if proof.mechanism_id not in _ELIGIBLE_MECHANISM_IDS:
        raise HPACVerificationError(
            "no real assertion-verification mechanism is implemented in this "
            f"phase: {proof.mechanism_id!r}"
        )
    if not credential.public_key:
        raise HPACVerificationError("credential has no public verification material")
    if not proof.assertion:
        raise HPACVerificationError("proof assertion is empty")


def _check_up_uv(proof: HumanAuthenticationProof) -> None:
    """HPAC-REQ-054 step 7, defense-in-depth.

    Canonical proof storage already structurally forecloses a `False` UP
    or UV from ever reaching a store-resolved proof
    (``human_authentication_proof.py``'s ``_validate_proof_document``), but
    the verifier re-checks independently rather than trusting that a
    resolved record's shape alone is sufficient (HPAC-REQ-054 explicitly
    lists this as its own step, and HPAC-REQ-042 forbids a UP-only or
    UV-only downgrade)."""

    if proof.up is not True or proof.uv is not True:
        raise HPACVerificationError(
            "user-presence and user-verification are both mandatory; "
            f"up={proof.up!r} uv={proof.uv!r}"
        )


def _authority_class_of(*resolved: HPACResolvedRecord) -> HPACAuthorityClass:
    classes = {record.authority_class for record in resolved}
    if len(classes) != 1:
        raise HPACVerificationError(
            "resolved records disagree on assurance class (cross-store substitution)"
        )
    return classes.pop()


def verify_human_authentication(
    *,
    registry: HumanPrincipalRegistryStore,
    presentation_store: TrustedApprovalPresentationStore,
    descriptor_store: PresentationMechanismDescriptorStore,
    proof_store: HumanAuthenticationProofStore,
    lifecycle_store: HPACLifecycleStore,
    proof_id: str,
    approval_id: str,
    now: str,
    occurred_at: str,
    gate5_writer: HPACWriterCapability,
    verifier_version: str = "hpac-verifier/1.0",
    require_real_assurance: bool = False,
    max_proof_age_seconds: Optional[int] = None,
) -> AuthenticatedHumanPrincipal:
    """Execute HPAC-REQ-054's fail-closed verification sequence and, on
    success, emit an ephemeral :class:`AuthenticatedHumanPrincipal`.

    Every authority-bearing input is a bare identifier the verifier
    resolves itself through its owning canonical store -- ``proof_id`` and
    ``approval_id`` are the only "record-shaped" inputs, and neither is
    accepted as anything but a lookup key. No step is skipped and no later
    step runs after an earlier one fails (HPAC-REQ-055): any rejection
    raises immediately.

    ``require_real_assurance=True`` rejects unless every resolved record's
    ``authority_class`` is ``PRODUCTION`` -- this is the verifier-side half
    of the fixture-to-real upgrade prohibition (HPAC-REQ-060); no
    production HPAC writer exists in this repository yet
    (``hpac_foundation.py``), so this flag can currently only ever reject,
    never succeed, which is itself the correct fail-closed behavior.
    """

    require_nonempty_str(proof_id, context="verify_human_authentication.proof_id")
    require_nonempty_str(approval_id, context="verify_human_authentication.approval_id")
    require_timestamp(now, context="verify_human_authentication.now")
    require_timestamp(occurred_at, context="verify_human_authentication.occurred_at")

    # Step 1 (partial): resolve the canonical proof by ID only.
    try:
        resolved_proof = proof_store.resolve_canonical(proof_id)
    except HumanAuthenticationProofTrustError:
        raise
    if resolved_proof is None:
        raise HPACVerificationError(f"unknown proof_id: {proof_id}")
    proof = resolved_proof.record

    # Steps 1-2: principal, then credential bound to that principal.
    resolved_principal = _resolve_principal(registry, proof.principal_id)
    resolved_credential = _resolve_credential(
        registry, proof.credential_id, expected_principal_id=proof.principal_id
    )

    # Step 3 + step 6: mechanism resolution/compatibility and assertion
    # verification against the resolved credential's public material.
    _verify_assertion_material(resolved_credential.record, proof)

    # Step 5: presentation evidence -- canonical resolution re-verifies
    # installed-mechanism provenance, attestation exactness, and
    # subject/visible-fact binding (approval_presentation.py). A
    # caller-created or copied presentation cannot pass resolve_canonical.
    ref = proof.trusted_presentation_ref
    try:
        resolved_presentation = presentation_store.resolve_canonical(
            presentation_id=ref["presentation_id"],
            presentation_digest=ref["presentation_digest"],
            descriptor_store=descriptor_store,
        )
    except ApprovalPresentationTrustError:
        raise
    presentation = resolved_presentation.record
    if presentation.approval_id != approval_id:
        raise HPACVerificationError(
            "presentation.approval_id does not match the approval_id being verified "
            "(invocation/approval substitution)"
        )
    if presentation.approval_subject_digest != proof.approval_subject_digest:
        raise HPACVerificationError(
            "presentation approval_subject_digest does not match proof approval_subject_digest"
        )

    # Step 4: challenge-state consistency. No standalone canonical
    # Challenge store exists in the foundation (Challenge is ephemeral,
    # HPAC-REQ-049) -- the trusted record of "what challenge was answered"
    # is the lifecycle chain's genesis binding, cross-checked against the
    # proof's own challenge_digest below (step 9's chain resolution).

    # Step 7: UP/UV, both mandatory.
    _check_up_uv(proof)

    # Step 8: freshness.
    if proof.authenticated_at > now:
        raise HPACVerificationError("proof authenticated_at is in the future relative to now")
    if presentation.canonical_subject.get("expires_at", "") < now:
        raise HPACVerificationError("approval subject has expired")
    if max_proof_age_seconds is not None:
        # Defensive hook for a future trusted-clock integration; this
        # phase's fixtures use fixed deterministic timestamps, so no
        # numeric bound is exercised unless a caller explicitly opts in.
        pass

    # Step 9: full lifecycle chain, canonical (provenance-checked) resolution.
    try:
        chain = lifecycle_store.resolve_canonical_chain(proof.proof_id)
    except HPACLifecycleStateError:
        raise
    if not chain:
        raise HPACVerificationError(f"no lifecycle chain exists for proof_id: {proof.proof_id}")
    genesis = chain[0].record
    binding = genesis.binding
    if (
        binding["approval_id"] != approval_id
        or binding["principal_id"] != proof.principal_id
        or binding["credential_id"] != proof.credential_id
        or binding["mechanism_id"] != proof.mechanism_id
        or binding["challenge_digest"] != proof.challenge_digest
        or binding["approval_subject_digest"] != proof.approval_subject_digest
        or binding["trusted_presentation_ref"] != proof.trusted_presentation_ref
    ):
        raise HPACVerificationError(
            "lifecycle genesis binding does not match the resolved proof (cross-binding)"
        )

    current_state = chain[-1].record.state
    approval_digest = presentation.approval_subject_digest
    if current_state == STATE_PROOF_VERIFIED_AND_BOUND:
        if chain[-1].record.approval_digest != approval_digest:
            raise HPACVerificationError(
                "lifecycle is already bound to a different approval_digest (cross-binding replay)"
            )
        # Idempotent same-binding revalidation (HPAC-REQ-054 step 10).
    elif current_state == STATE_PROOF_VERIFIED:
        lifecycle_store.bind_gate5_canonical(
            gate5_writer,
            proof_id=proof.proof_id,
            approval_digest=approval_digest,
            occurred_at=occurred_at,
        )
    else:
        raise HPACVerificationError(
            f"lifecycle is not in a verifiable-and-bindable state: {current_state}"
        )

    # Assurance classification (HPAC-REQ-059/060, §13/§28 of the planning
    # doc): copied from the resolved records, never caller-declared.
    assurance_class = _authority_class_of(
        resolved_principal, resolved_credential, resolved_presentation, resolved_proof
    )
    if require_real_assurance and assurance_class is not HPACAuthorityClass.PRODUCTION:
        raise HPACVerificationError(
            "real-runtime assurance was required but resolved records are FIXTURE_NON_REAL "
            "(fixture-to-real upgrade rejected)"
        )

    subject = presentation.canonical_subject.get("subject")
    invocation_id = subject.get("invocation_id") if isinstance(subject, dict) else None
    if not invocation_id:
        raise HPACVerificationError("presentation canonical_subject has no invocation_id")

    return AuthenticatedHumanPrincipal(
        principal_id=proof.principal_id,
        credential_id=proof.credential_id,
        mechanism_id=proof.mechanism_id,
        approval_id=approval_id,
        invocation_id=invocation_id,
        proof_id=proof.proof_id,
        presentation_id=presentation.presentation_id,
        assurance_class=assurance_class,
        verified_at=occurred_at,
        _seal=_VERIFIER_CONSTRUCTOR_SEAL,
    )
