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

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5.2 repair (F1, BLOCKING, found by
``...1R.5.1``): the ``_VERIFIER_CONSTRUCTOR_SEAL`` check inside ``__init__``
is real but insufficient on its own -- ``object.__new__(cls)`` allocates a
bare instance without ever calling ``__init__``, so a caller can populate
every ``__slots__`` attribute directly and obtain an ``isinstance``-true,
field-identical lookalike that was never produced by
:func:`verify_human_authentication`. No field-based seal, sentinel, or
constructor restriction can close this in pure Python: ``object.__new__``
bypasses *any* subclass ``__new__`` override too (it is a call to a
different, unrelated method, not a call that goes through the subclass's
MRO), and copying/reconstructing an object's ``__slots__`` state
reproduces every field including a copied sentinel. Object shape,
constructor path, private fields, and non-serializability are therefore
never sufficient proof that a value came from a real §18 verification --
this is the exact "forgeable-seal" mistake B1
(``149O.20L.7O.3W.1R.2`` §9) already named, applied here to a different
class.

The actual trust boundary is :func:`is_verifier_authenticated_principal`,
which does not inspect the candidate's fields at all: it checks whether
*this exact Python object* (by identity) is present in this module's own
process-local identity registry, ``_AUTHENTIC_PRINCIPAL_REGISTRY``, which
only :func:`verify_human_authentication`'s own return path ever adds to.
A caller-manufactured lookalike -- however it was allocated
(``object.__new__``, a subclass, ``copy``/``deepcopy``, manual slot
injection, or reflection) -- is a different Python object and is
therefore never a member, regardless of what its fields say. Every future
consumer of a verification result (a later Gate 5, PB projection, or any
other production code) MUST call :func:`is_verifier_authenticated_principal`
before trusting a value's ``assurance_class``/``is_real_runtime_eligible``;
``isinstance()`` alone, or reading any attribute, is not sufficient and
was never meant to be (this module still has zero production consumers,
so no such call site exists yet -- this is the boundary a future consumer
is required to use, not a change to a call site that exists today).

The existing ``_seal`` check in ``__init__`` is retained as defense in
depth against the ordinary, common-case direct-construction call
(``AuthenticatedHumanPrincipal(...)``) -- it gives a clear error for that
case and costs nothing -- but it is not, and was never, the actual trust
boundary; the identity registry is.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from pcae.core.hpac_foundation import (
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACResolvedRecord,
    HPACWriterCapability,
    canonical_digest,
    require_nonempty_str,
    require_timestamp,
)
from pcae.core.human_authenticator import Challenge
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
    "is_verifier_authenticated_principal",
    "reverify_authenticated_principal",
]

#: The closed set of mechanism identities this verifier can certify.
#:
#: Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (merged RHAMP-REQ-156
#: ``.1R.30`` bundle) widens this frozenset literal by **exactly**
#: ``{"hpac.fido2.uv_presence.v2"}`` per RHAMP-001 v1.0 §4 (RHAMP-REQ-011 /
#: RHAMP-REQ-109): one entry, no wildcard, no prefix match, no glob. The
#: deterministic test mechanism stays isolated by its
#: ``hpac.deterministic.*`` prefix and is permanently outside the real
#: allowlist (RHAMP-REQ-013).
#:
#: The real ``hpac.fido2.uv_presence.v2`` branch is **only reachable when
#: every resolved record is ``PRODUCTION``** (RHAMP-REQ-103): a
#: ``FIXTURE_NON_REAL`` credential carrying that ``mechanism_id`` is rejected
#: before any real signature math.
#:
#: Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1 — HPAC-PPA-001 v1.0 makes the
#: real ``pcae-protected-local-presentation/1.0`` presentation descriptor
#: kind acceptable (``approval_presentation._verify_installed_attestation``
#: → ``protected_presentation.verify_protected_presentation_evidence``). A
#: ``PRODUCTION`` ``AuthenticatedHumanPrincipal`` is therefore now reachable
#: end-to-end **only** through the coupled real path: a real
#: ``hpac.fido2.uv_presence.v2`` credential/proof **and** a real
#: ``pcae-protected-local-presentation/1.0`` presentation evidence with
#: matching live bindings (HPAC-PPA-REQ-057, RHAMP-REQ-038). N-16-5 remains
#: NOT CLOSED pending fresh IV + mandatory real-CTAP2-hardware verification.
_ELIGIBLE_MECHANISM_IDS = frozenset(
    {"hpac.deterministic.test-only.v1", "hpac.fido2.uv_presence.v2"}
)
#: HPAC-PPA-REQ-008 — the sole real presentation mechanism id. A resolved
#: presentation whose ``mechanism_ref.mechanism_id`` is this value went
#: through the real ``pcae-protected-local-presentation/1.0`` attestation
#: verifier (deterministic fixtures use a permanently distinct id).
_REAL_PRESENTATION_MECHANISM_ID = "pcae-protected-local-presentation"
#: The subset of :data:`_ELIGIBLE_MECHANISM_IDS` that requires the real
#: native-CTAP2 signature branch (RHAMP-001 §4). Exact-match only.
_REAL_ELIGIBLE_MECHANISM_IDS = frozenset({"hpac.fido2.uv_presence.v2"})

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
    ``PRODUCTION`` assurance.

    This object's fields, type, ``repr``/``hash``/equality, and the
    ``_seal`` check in ``__init__`` are data-shape properties, not the
    trust boundary -- all of them can be reproduced by a caller via
    ``object.__new__``, a subclass, ``copy``/``deepcopy``, or manual
    slot injection, without ever calling
    :func:`verify_human_authentication` (see this module's docstring,
    F1 of ``...1R.5.1``). The actual, authoritative trust boundary is
    :func:`is_verifier_authenticated_principal`: an instance is a
    genuine verification result if and only if it is a member of this
    module's own process-local identity registry, which only this
    class's construction inside :func:`verify_human_authentication`
    populates. Every consumer that needs to know whether a value came
    from a real verification MUST call that function; ``isinstance()``
    and attribute access are insufficient by design."""

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

    def __init_subclass__(cls, **kwargs) -> None:
        # A subclass could define its own __init__ that never checks
        # _VERIFIER_CONSTRUCTOR_SEAL at all, trivially recreating the same
        # "isinstance-true, never verified" shape this phase repairs.
        # There is no legitimate reason to subclass a trusted-construction
        # result type, so subclassing itself is refused at definition time.
        raise HPACAuthorityError(
            "AuthenticatedHumanPrincipal must not be subclassed"
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
        # never treated as "the same" authenticated result. This is a
        # data-equality property only -- two objects being unequal (or a
        # single object being equal only to itself) does not by itself
        # grant or deny authority; see is_verifier_authenticated_principal
        # for the actual authority check, which this hash/eq scheme makes
        # possible (identity-keyed registry membership below).
        return self is other

    def __hash__(self) -> int:
        return id(self)


#: HPAC-REQ-056's actual provenance boundary (see the module and class
#: docstrings above for why a field/seal check inside __init__ is
#: insufficient). Membership is keyed by object identity -- this class's
#: __hash__/__eq__ are already identity-only (id(self)/`self is other`),
#: so a caller-manufactured lookalike, whatever its field values, can
#: never collide with a genuine entry here. Nothing outside this module
#: ever adds to this registry -- the only insertion point is
#: verify_human_authentication's own return path, below.
#:
#: This holds ordinary strong references, not weak ones: adding
#: "__weakref__" to __slots__ above (the usual way to let instances be
#: weakly referenced, so a registry entry would disappear on its own once
#: every caller-held reference is dropped) would break
#: `...1R.5.1`'s already-verified historical evidence test
#: (`test_verifier_result_attribute_copy_produces_a_distinguishable_object`
#: in `tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py`),
#: which iterates the literal `__slots__` tuple and `setattr`s every
#: entry -- `__weakref__` has no attribute setter, so that historical test
#: (preserved unmodified per this phase's own instructions) would start
#: raising `AttributeError`. This is a deliberate, documented trade-off:
#: every genuine verification result stays referenced by this module for
#: the life of the process, rather than being freed once the caller drops
#: it. `hpac_verifier.py` has zero production consumers today (see this
#: module's docstring and the zero-consumer tests), so unbounded growth is
#: not a live concern; a future phase wiring a real, long-running
#: production consumer of this module must revisit this (e.g. a bounded/
#: LRU registry, or adding "__weakref__" together with updating the
#: historical test) before that consumption path is trusted.
_AUTHENTIC_PRINCIPAL_REGISTRY: "set[AuthenticatedHumanPrincipal]" = set()


@dataclass(frozen=True)
class _PrincipalVerificationContext:
    """Verifier-owned inputs needed to re-resolve a result at consumption.

    This context is deliberately process-local and keyed by exact result
    identity.  It is neither authority-bearing data nor serializable state;
    losing it (including across process restart) makes the old result
    unusable and requires a new authentication ceremony.
    """

    registry: HumanPrincipalRegistryStore
    presentation_store: TrustedApprovalPresentationStore
    descriptor_store: PresentationMechanismDescriptorStore
    proof_store: HumanAuthenticationProofStore
    lifecycle_store: HPACLifecycleStore
    challenge: Challenge
    proof_id: str
    approval_id: str
    gate5_writer: HPACWriterCapability
    verifier_version: str
    max_proof_age_seconds: Optional[int]


_AUTHENTIC_PRINCIPAL_CONTEXTS: dict[
    AuthenticatedHumanPrincipal, _PrincipalVerificationContext
] = {}


def is_verifier_authenticated_principal(candidate: object) -> bool:
    """HPAC-REQ-056's authoritative trust check.

    Returns ``True`` only if ``candidate`` is the literal object a past
    call to :func:`verify_human_authentication` returned -- never based on
    ``isinstance``, field values, equality, or any other shape property,
    all of which a caller can reproduce without ever verifying anything
    (``object.__new__``, a copy, manual slot injection, or reflection).
    Fails closed: any input that is not a genuine, still-referenced
    verification result -- including a well-formed-looking forgery, a
    stale/garbage-collected handle, or a non-``AuthenticatedHumanPrincipal``
    value -- returns ``False``. There is no fallback field comparison.

    This is the boundary every future consumer of a verification result
    (a later Gate 5, PB projection, or other production code) MUST call
    before trusting ``candidate.assurance_class`` or
    ``candidate.is_real_runtime_eligible``; this module itself has zero
    production consumers today, so no call site exists yet -- this
    function is the contract those future consumers are required to use.
    """

    return (
        isinstance(candidate, AuthenticatedHumanPrincipal)
        and candidate in _AUTHENTIC_PRINCIPAL_REGISTRY
        and candidate in _AUTHENTIC_PRINCIPAL_CONTEXTS
    )


def reverify_authenticated_principal(
    candidate: object,
    *,
    now: str,
    occurred_at: str,
    require_real_assurance: bool = False,
) -> AuthenticatedHumanPrincipal:
    """Freshly re-run the complete canonical verification for ``candidate``.

    Registry membership proves only that the exact object was emitted by a
    past verifier call.  Authority consumption must also re-resolve current
    principal, credential, proof, presentation, and lifecycle state.  This
    helper owns that second half of HPAC-REQ-058 and deliberately has no
    fallback based on object shape or copied fields.
    """

    require_timestamp(now, context="reverify_authenticated_principal.now")
    require_timestamp(occurred_at, context="reverify_authenticated_principal.occurred_at")
    if not is_verifier_authenticated_principal(candidate):
        raise HPACVerificationError(
            "authenticated principal is not a current verifier-issued result"
        )
    assert isinstance(candidate, AuthenticatedHumanPrincipal)
    context = _AUTHENTIC_PRINCIPAL_CONTEXTS.get(candidate)
    if context is None:
        raise HPACVerificationError("authenticated principal verification context is unavailable")
    refreshed = verify_human_authentication(
        registry=context.registry,
        presentation_store=context.presentation_store,
        descriptor_store=context.descriptor_store,
        proof_store=context.proof_store,
        lifecycle_store=context.lifecycle_store,
        challenge=context.challenge,
        proof_id=context.proof_id,
        approval_id=context.approval_id,
        now=now,
        occurred_at=occurred_at,
        gate5_writer=context.gate5_writer,
        verifier_version=context.verifier_version,
        require_real_assurance=require_real_assurance,
        max_proof_age_seconds=context.max_proof_age_seconds,
    )
    try:
        if (
            refreshed.principal_id != candidate.principal_id
            or refreshed.credential_id != candidate.credential_id
            or refreshed.mechanism_id != candidate.mechanism_id
            or refreshed.approval_id != candidate.approval_id
            or refreshed.invocation_id != candidate.invocation_id
            or refreshed.proof_id != candidate.proof_id
            or refreshed.presentation_id != candidate.presentation_id
        ):
            raise HPACVerificationError(
                "fresh verification result does not match the consumed principal binding"
            )
    finally:
        # ``refreshed`` is verification evidence for this consumption, not
        # a separately issued authority object.  Keeping it registered would
        # grow the strong-reference provenance registry on every recheck.
        _AUTHENTIC_PRINCIPAL_CONTEXTS.pop(refreshed, None)
    return candidate


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
    credential: CredentialRecord,
    proof: HumanAuthenticationProof,
    *,
    authority_class: HPACAuthorityClass,
    challenge: Challenge,
    sidecar_store: object = None,
    counter_state_store: object = None,
    invocation_id: Optional[str] = None,
    attempt_id: Optional[str] = None,
) -> Optional[object]:
    """HPAC-REQ-054 step 6 / RHAMP-001 §37: verify the assertion against the
    resolved credential's public verification material.

    Deterministic NON_REAL mechanism (``hpac.deterministic.test-only.v1``):
    the historical shallow check — categorically no real signature math
    (mirrors ``approval_presentation.py``'s ``_verify_installed_attestation``
    discipline for the identical boundary).

    Real mechanism (``hpac.fido2.uv_presence.v2``, Phase .1R.30R.3.4): the
    native-CTAP2 signature sequence (RHAMP-REQ-102) — rpIdHash, COSE
    signature over ``authenticatorData ‖ client_data_hash``, ``FLAG.UP`` and
    ``FLAG.UV``, the reconstructed canonical client-data (§7/§25), and the
    §20 signature-counter policy against the §21 counter-state record.
    RHAMP-REQ-103: the real branch is reachable **only** when every resolved
    record is ``PRODUCTION``; a ``FIXTURE_NON_REAL`` credential carrying the
    real ``mechanism_id`` is rejected here (``mechanism_unknown``) before any
    signature math.

    Returns a ``RealFido2AssertionResult`` for the real branch (the caller
    applies its ``counter_decision`` after step 10, RHAMP-REQ-071.3), or
    ``None`` for the deterministic branch.
    """

    if not credential.public_key:
        raise HPACVerificationError("credential has no public verification material")
    if not proof.assertion:
        raise HPACVerificationError("proof assertion is empty")

    if proof.mechanism_id not in _REAL_ELIGIBLE_MECHANISM_IDS:
        return None

    # ── real ``hpac.fido2.uv_presence.v2`` branch (RHAMP-REQ-102/103) ──
    if authority_class is not HPACAuthorityClass.PRODUCTION:
        # RHAMP-REQ-103 / RHAMP-REQ-113 — a fixture-root credential carrying
        # the real mechanism_id never reaches real signature verification.
        raise HPACVerificationError(
            "a FIXTURE_NON_REAL credential can never reach real FIDO2 assertion "
            "verification (RHAMP-001 §37 / RHAMP-REQ-103)"
        )
    if sidecar_store is None or counter_state_store is None:
        raise HPACVerificationError(
            "real FIDO2 assertion verification requires the RHAMP-001 sidecar and "
            "counter-state stores (RHAMP-REQ-102 steps 1/6)"
        )
    if not invocation_id or not attempt_id:
        raise HPACVerificationError(
            "real FIDO2 assertion verification requires the lifecycle-bound "
            "invocation_id / attempt_id (RHAMP-REQ-025)"
        )
    from pcae.core.hpac_rhamp_assertion_verify import verify_real_fido2_assertion
    from pcae.core.hpac_rhamp_terminal_reasons import RhampTerminalError

    try:
        resolved_sidecar = sidecar_store.resolve_canonical(credential.credential_id)
        if resolved_sidecar is None:
            raise HPACVerificationError("no RHAMP-FIDO2-CREDENTIAL/1.0 sidecar for the resolved credential")
        counter_state = counter_state_store.resolve(credential.credential_id)
        result = verify_real_fido2_assertion(
            credential=credential,
            sidecar=resolved_sidecar.record,
            proof=proof,
            challenge=challenge,
            invocation_id=invocation_id,
            attempt_id=attempt_id,
            counter_state=counter_state,
        )
    except RhampTerminalError as exc:
        raise HPACVerificationError(
            f"real FIDO2 assertion rejected ({exc.terminal_reason_code}): {exc.detail}"
        ) from exc
    return result


def _verify_mechanism_eligibility(
    credential: CredentialRecord, proof: HumanAuthenticationProof
) -> None:
    """HPAC-REQ-054 step 3, kept separate from step-6 assertion checks."""

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
    challenge: Challenge,
    proof_id: str,
    approval_id: str,
    now: str,
    occurred_at: str,
    gate5_writer: HPACWriterCapability,
    verifier_version: str = "hpac-verifier/1.0",
    require_real_assurance: bool = False,
    max_proof_age_seconds: Optional[int] = None,
    sidecar_store: object = None,
    counter_state_store: object = None,
    counter_state_writer: Optional[HPACWriterCapability] = None,
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
    if type(challenge) is not Challenge:
        raise HPACVerificationError("exact Challenge state is required for digest recomputation")

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

    # Step 3: mechanism resolution/compatibility and minimum eligibility.
    _verify_mechanism_eligibility(resolved_credential.record, proof)

    # Step 4: independently recompute the digest from the complete exact
    # ephemeral challenge state.  A lifecycle/proof agreement is not a
    # substitute for this computation: two records can agree on the same
    # caller-manufactured digest.  The exact field set mirrors
    # HPACLifecycleStore.open_challenge_canonical and HPAC-REQ-049.
    challenge_body = {
        "domain_separator": challenge.domain_separator,
        "challenge_version": challenge.challenge_version,
        "proof_schema_version": challenge.proof_schema_version,
        "principal_id": challenge.principal_id,
        "credential_id": challenge.credential_id,
        "approval_subject_digest": challenge.approval_subject_digest,
        "trusted_presentation_digest": challenge.trusted_presentation_digest,
        "nonce": challenge.nonce,
        "issued_at": challenge.issued_at,
        "expires_at": challenge.expires_at,
    }
    recomputed_challenge_digest = canonical_digest(challenge_body)
    if recomputed_challenge_digest != challenge.challenge_digest:
        raise HPACVerificationError(
            "challenge_digest does not match independently recomputed challenge state"
        )
    if challenge.challenge_digest != proof.challenge_digest:
        raise HPACVerificationError("challenge state does not match the canonical proof")
    if (
        challenge.principal_id != proof.principal_id
        or challenge.credential_id != proof.credential_id
        or challenge.approval_subject_digest != proof.approval_subject_digest
        or challenge.trusted_presentation_digest
        != proof.trusted_presentation_ref.get("presentation_digest")
    ):
        raise HPACVerificationError(
            "challenge state does not match proof principal/credential/subject/presentation binding"
        )

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

    # Lifecycle chain resolved here (a pure provenance-checked read) so the
    # genesis binding's invocation_id / attempt_id are available to the real
    # RHAMP-001 §37 client-data reconstruction (RHAMP-REQ-025). The state
    # machine / cross-binding checks stay at step 9, below, unchanged.
    try:
        chain = lifecycle_store.resolve_canonical_chain(proof.proof_id)
    except HPACLifecycleStateError:
        raise
    if not chain:
        raise HPACVerificationError(f"no lifecycle chain exists for proof_id: {proof.proof_id}")
    genesis = chain[0].record
    binding = genesis.binding

    # Assurance class of every resolved record (HPAC-REQ-059/060). Computed
    # here too (it is also recomputed at the end) so the RHAMP-001 §37 real
    # branch is gated on PRODUCTION per RHAMP-REQ-103.
    _pre_assurance_class = _authority_class_of(
        resolved_principal, resolved_credential, resolved_presentation, resolved_proof
    )

    # Step 6: assertion verification against the resolved credential's
    # public material.  Kept after challenge and presentation binding so
    # HPAC-REQ-054's fail-closed sequence is literal, not merely complete.
    # For ``hpac.fido2.uv_presence.v2`` this is the real native-CTAP2
    # signature sequence (RHAMP-001 §37); for the deterministic mechanism it
    # is the historical shallow check.
    _real_assertion_result = _verify_assertion_material(
        resolved_credential.record,
        proof,
        authority_class=_pre_assurance_class,
        challenge=challenge,
        sidecar_store=sidecar_store,
        counter_state_store=counter_state_store,
        invocation_id=binding.get("invocation_id"),
        attempt_id=binding.get("attempt_id"),
    )

    # Step 7: UP/UV, both mandatory.
    _check_up_uv(proof)

    # Step 8: freshness.
    presentation_expires_at = presentation.canonical_subject.get("expires_at", "")
    for timestamp_name, timestamp in (
        ("challenge.issued_at", challenge.issued_at),
        ("challenge.expires_at", challenge.expires_at),
        ("proof.authenticated_at", proof.authenticated_at),
        ("presentation.expires_at", presentation_expires_at),
        ("now", now),
    ):
        require_timestamp(timestamp, context=timestamp_name)

    def _instant(value: str) -> datetime:
        return datetime.fromisoformat(value.removesuffix("Z") + "+00:00").astimezone(
            timezone.utc
        )

    if _instant(challenge.expires_at) <= _instant(challenge.issued_at):
        raise HPACVerificationError("challenge expiry is not after issuance")
    if _instant(proof.authenticated_at) > _instant(now):
        raise HPACVerificationError("proof authenticated_at is in the future relative to now")
    if _instant(now) >= _instant(presentation_expires_at):
        raise HPACVerificationError("approval subject has expired")
    if not (
        _instant(challenge.issued_at)
        <= _instant(proof.authenticated_at)
        < _instant(challenge.expires_at)
    ):
        raise HPACVerificationError("proof authentication is outside the challenge lifetime")
    if _instant(now) >= _instant(challenge.expires_at):
        raise HPACVerificationError("challenge has expired")
    if max_proof_age_seconds is not None:
        if max_proof_age_seconds < 0:
            raise HPACVerificationError("max_proof_age_seconds must not be negative")
        proof_age = (_instant(now) - _instant(proof.authenticated_at)).total_seconds()
        if proof_age > max_proof_age_seconds:
            raise HPACVerificationError("proof is older than the configured maximum age")

    # Step 9: full lifecycle chain state / cross-binding checks (the chain
    # itself was resolved before step 6, above).
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
    if require_real_assurance:
        # HPAC-PPA-REQ-057 / RHAMP-REQ-038 — REAL authentication and REAL
        # protected presentation with matching live bindings are *jointly*
        # required; neither alone, and no fixture, can satisfy this.
        if assurance_class is not HPACAuthorityClass.PRODUCTION:
            raise HPACVerificationError(
                "real-runtime assurance was required but resolved records are FIXTURE_NON_REAL "
                "(fixture-to-real upgrade rejected)"
            )
        if proof.mechanism_id not in _REAL_ELIGIBLE_MECHANISM_IDS:
            raise HPACVerificationError(
                "real-runtime assurance requires a real authentication mechanism "
                f"(got {proof.mechanism_id!r})"
            )
        real_presentation_mechanism = presentation.mechanism_ref.get("mechanism_id")
        if real_presentation_mechanism != _REAL_PRESENTATION_MECHANISM_ID:
            raise HPACVerificationError(
                "real-runtime assurance requires a real protected-presentation mechanism "
                f"(got {real_presentation_mechanism!r}); authentication alone is insufficient"
            )

    subject = presentation.canonical_subject.get("subject")
    invocation_id = subject.get("invocation_id") if isinstance(subject, dict) else None
    if not invocation_id:
        raise HPACVerificationError("presentation canonical_subject has no invocation_id")

    # RHAMP-REQ-071.3 / §12 — for the real mechanism, atomically apply the
    # linearized counter-state update **immediately after** step 10 succeeds
    # and **before** the AuthenticatedHumanPrincipal is returned. A crash
    # here leaves the proof single-use and the nonce consumed (RHAMP-REQ-072).
    if _real_assertion_result is not None and current_state == STATE_PROOF_VERIFIED:
        if counter_state_store is None or counter_state_writer is None:
            raise HPACVerificationError(
                "real FIDO2 verification requires a counter-state writer to linearize "
                "the post-verification counter update (RHAMP-REQ-071/073)"
            )
        from pcae.core.hpac_rhamp_counter_state import RhampCounterStateError

        try:
            _current_counter = counter_state_store.resolve(proof.credential_id)
            counter_state_store.apply_after_verification(
                counter_state_writer,
                credential_id=proof.credential_id,
                expected_current=_current_counter,
                decision=_real_assertion_result.counter_decision,
                updated_at=occurred_at,
            )
        except RhampCounterStateError as exc:
            raise HPACVerificationError(
                f"real FIDO2 counter-state linearization failed: {exc}"
            ) from exc

    result = AuthenticatedHumanPrincipal(
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
    # This is the only place anything is ever added to the identity
    # registry that is_verifier_authenticated_principal checks -- the
    # actual HPAC-REQ-056 provenance boundary (see module/class docstrings).
    _AUTHENTIC_PRINCIPAL_REGISTRY.add(result)
    _AUTHENTIC_PRINCIPAL_CONTEXTS[result] = _PrincipalVerificationContext(
        registry=registry,
        presentation_store=presentation_store,
        descriptor_store=descriptor_store,
        proof_store=proof_store,
        lifecycle_store=lifecycle_store,
        challenge=challenge,
        proof_id=proof_id,
        approval_id=approval_id,
        gate5_writer=gate5_writer,
        verifier_version=verifier_version,
        max_proof_age_seconds=max_proof_age_seconds,
    )
    return result
