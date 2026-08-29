"""
Gate-5 approval-validation coordinator — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.10.

Implements RDGO-001 v3.0 §6 Gate 5 as the frozen `.1R.9` §6 decision:
**Option C (layered)** — one trusted component that OWNS "Gate 5 ran" by
sequencing the already-independently-verified sub-checks in RIHAC-001 v2.0
§16 order, confirming the HPAC lifecycle sequence-3 ``PROOF_VERIFIED_AND_BOUND``
binding (HPAC-REQ-097), and owning the fail-closed envelope plus the
ephemeral, non-transferable result. It duplicates no authority semantics —
each sub-check keeps its existing single owner:

* approval validation (RIASC-001 shape/version, record digest, producer and
  human provenance, repository/task/phase/session binding, invocation and
  exact target, prompt hash, capability/scope/adapter descriptor, the seven
  freshness conditions, expiry against a trusted clock, prior
  consumption/cancellation/uncertainty/completion, RIHAC-001 §16 steps 1-12)
  → :func:`runtime_authority.validate_approval`;
* principal provenance + the complete HPAC-REQ-054 reverification (including
  Step 4 independent challenge-digest recomputation, credential currentness,
  proof/challenge/presentation freshness, and the §40 lifecycle chain)
  → the mechanism-neutral HPAC verifier, reached through
  ``validate_approval``'s mandatory ``reverify_authenticated_principal`` call;
* the HPAC lifecycle sequence-3 ``PROOF_VERIFIED_AND_BOUND`` event
  → :class:`hpac_lifecycle.HPACLifecycleStore`. The verifier's HPAC-REQ-054
  step 10 performs the atomic create / same-binding-idempotent accept while
  it reverifies the principal; this coordinator OWNS that transition by
  re-resolving the canonical, provenance-checked chain, confirming the exact
  binding, and carrying the event digest in its ephemeral result. It never
  manufactures the event and holds no lifecycle writer capability.

The deterministic NON-REAL hard stop is **inherited, not re-implemented**:
``validate_approval`` (``runtime_authority.py`` line ~1093) rejects unless
``principal.assurance_class is HPACAuthorityClass.PRODUCTION``, and no
deterministically-writable HPAC store can carry ``PRODUCTION`` assurance
(``hpac_foundation.HPACStoreAuthority.writer``). The fully wired Gate-5
coordinator therefore returns fail-closed in production for every real
request until a real assurance mechanism exists. A complete deterministic
local HPAC path that satisfies canonical principal / presentation / proof /
UP=UV=true / verifier provenance / canonical approval / exact invocation
binding still fails Gate-5 eligibility on
``non_real_authenticated_principal_cannot_validate_production_approval``.

Non-responsibilities (frozen by `.1R.9` §16.1 / §20-§23 / §34-§37): this
module performs no Permission Broker evaluation and produces no ALLOW/DENY
decision (Gate 6, `.1R.12`); it calls no Gate-9 atomic-consumption primitive
and creates no ``consumption.json`` (Gate 9, `.1R.14`); it performs no
subprocess, provider, network, adapter, credential, or hardware operation
(Gate 10). It **consumes nothing** — no approval, proof, presentation,
challenge, or nonce state changes, and Gate 5 is idempotently repeatable.

This module imports no ``subprocess``, ``socket``, provider SDK, HTTP
client, or FIDO2/WebAuthn/CTAP/smartcard/USB module (enforced by an AST
guard in the `.1R.10` suite).

Output model (`.1R.9` §8): :class:`Gate5Result` is identity-only
(``eq=False``), non-serializable (``__reduce__`` raises), process-local, and
never reconstructable from its fields — the same discipline as
``AuthenticatedHumanPrincipal`` and ``ValidatedAuthorityProjection``.
Possession of a ``Gate5Result`` or the projection it references is **never**
sufficient downstream: every consumer MUST re-check
``is_trusted_validated_authority_projection`` and re-run
``revalidate_validated_authority_projection`` at its own point of use
(exactly as ``runtime_dispatch_permission.project_human_authority_binding``
already does). A persisted lifecycle event, by itself, recreates neither
trusted result (HPAC-REQ-097 / §40.2).
"""

from __future__ import annotations

from typing import Optional

from pcae.core.hpac_lifecycle import HPACLifecycleStore, STATE_PROOF_VERIFIED_AND_BOUND
from pcae.core.runtime_authority import (
    ConsumptionLookup,
    InvocationRequestContext,
    ValidatedAuthorityProjection,
    is_trusted_validated_authority_projection,
    trusted_projection_gate5_binding,
    validate_approval,
)

__all__ = [
    "Gate5Result",
    "is_gate5_result",
    "run_gate5",
    "GATE5_ADVISORY_REASONS",
]

#: Reasons that ``validate_approval`` may return alongside a valid
#: projection (RIHAC-001 §13 policy-drift disposition) — non-fatal, surfaced
#: so a later PB evaluation re-runs rather than reusing a cached decision.
GATE5_ADVISORY_REASONS: frozenset[str] = frozenset(
    {"policy_drift_requires_fresh_pb_re_evaluation"}
)

_GATE5_RESULT_CONSTRUCTOR_SEAL = object()


class Gate5Result:
    """The ephemeral, non-transferable evidence the Gate-5 coordinator emits
    on success (`.1R.9` §8).

    Carries a reference to the ``ValidatedAuthorityProjection`` (itself
    identity-only and registry-provenanced), the confirmed HPAC lifecycle
    sequence-3 ``PROOF_VERIFIED_AND_BOUND`` event digest, the ``proof_id``,
    and the advisory reason tuple. Like ``AuthenticatedHumanPrincipal`` and
    ``ValidatedAuthorityProjection`` this type is:

    * **not** caller-constructable — the ``_seal`` guard rejects direct
      construction, and (the real boundary) :func:`is_gate5_result` checks
      membership in this module's process-local identity registry, which
      only :func:`run_gate5`'s own success path ever populates;
    * **not** serializable — ``__reduce__`` raises;
    * identity-only for ``==`` / ``hash`` — a copied, ``deepcopy``-d, or
      field-reconstructed lookalike is a different object and is never a
      member of the identity registry, whatever its fields say;
    * **not** a bearer token — possession authorizes nothing. Downstream
      consumers re-resolve the projection freshly (HPAC-REQ-097 / §40.2).
    """

    __slots__ = (
        "_projection",
        "sequence3_event_digest",
        "proof_id",
        "approval_id",
        "invocation_id",
        "advisory_reasons",
        "validated_at",
        "_seal",
    )

    def __init_subclass__(cls, **kwargs) -> None:
        raise TypeError("Gate5Result must not be subclassed")

    def __init__(
        self,
        *,
        projection: ValidatedAuthorityProjection,
        sequence3_event_digest: str,
        proof_id: str,
        approval_id: str,
        invocation_id: str,
        advisory_reasons: tuple[str, ...],
        validated_at: str,
        _seal: object,
    ) -> None:
        if _seal is not _GATE5_RESULT_CONSTRUCTOR_SEAL:
            raise TypeError(
                "Gate5Result cannot be caller-constructed; it is producible "
                "only by runtime_dispatch_gate5.run_gate5"
            )
        self._projection = projection
        self.sequence3_event_digest = sequence3_event_digest
        self.proof_id = proof_id
        self.approval_id = approval_id
        self.invocation_id = invocation_id
        self.advisory_reasons = advisory_reasons
        self.validated_at = validated_at
        self._seal = _seal

    @property
    def projection(self) -> ValidatedAuthorityProjection:
        """The referenced Gate-5 projection. Reading it is not trusting it —
        a consumer MUST still call ``is_trusted_validated_authority_projection``
        and ``revalidate_validated_authority_projection`` at its own point of
        use."""
        return self._projection

    def __reduce__(self):
        raise TypeError(
            "Gate5Result is ephemeral and non-serializable; Gate 5 must be "
            "re-run and the projection re-resolved by every consumer"
        )

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return (
            f"<Gate5Result proof_id={self.proof_id!r} "
            f"approval_id={self.approval_id!r} identity={id(self):#x}>"
        )


#: The actual provenance boundary for a Gate-5 result: exact-object
#: membership, keyed by identity (``Gate5Result.__hash__``/``__eq__`` are
#: ``id(self)``/``self is other``). Nothing outside this module adds to it;
#: the only insertion point is :func:`run_gate5`'s success return path.
_GATE5_RESULTS: "set[Gate5Result]" = set()


def is_gate5_result(candidate: object) -> bool:
    """Return ``True`` only for the literal object a past :func:`run_gate5`
    call returned on success — never based on ``isinstance``, fields,
    equality, or any shape property. Fails closed for a forgery, a copy, a
    reconstruction, or a stale handle."""
    return isinstance(candidate, Gate5Result) and candidate in _GATE5_RESULTS


def run_gate5(
    approval_id: object,
    *,
    approval_store: object = None,
    authenticated_principal: object = None,
    context: InvocationRequestContext,
    consumption_lookup: ConsumptionLookup,
    lifecycle_store: object,
) -> tuple[Optional[Gate5Result], tuple[str, ...]]:
    """Run RDGO-001 v3.0 Gate 5 for one ``runtime_dispatch`` request.

    Sequences, in RIHAC-001 v2.0 §16 order, the already-verified sub-checks
    and confirms the HPAC lifecycle sequence-3 binding. Every authority-
    bearing input is an opaque identifier or a type-enforced canonical
    store; caller-constructed approval objects, lookalike stores, forged or
    copied principals, and copied projections all fail closed. No later step
    substitutes for an earlier failure.

    Returns ``(Gate5Result, advisory_reasons)`` on success — where
    ``advisory_reasons`` is ``()`` or a subset of
    :data:`GATE5_ADVISORY_REASONS` — and ``(None, reasons)`` on any failure,
    creating no ``Gate5Result`` and consuming nothing. On the deterministic
    NON-REAL path this returns
    ``(None, ("non_real_authenticated_principal_cannot_validate_production_approval",))``.

    ``lifecycle_store`` MUST be a concrete :class:`HPACLifecycleStore`
    resolving the same protected root the authentication used; a wrong or
    lookalike store fails closed (the sequence-3 event will not resolve).
    This coordinator never resolves a canonical store's raw path itself and
    never trusts a caller-provided approval / principal / challenge / proof
    / lifecycle object as authority.
    """
    # --- provenance precheck (defensive; validate_approval re-checks) -----
    from pcae.core.hpac_verifier import is_verifier_authenticated_principal

    if type(lifecycle_store) is not HPACLifecycleStore:
        return None, ("gate5_canonical_lifecycle_store_required",)
    if not is_verifier_authenticated_principal(authenticated_principal):
        return None, ("authenticated_principal_not_verifier_issued",)

    # --- RIHAC-001 §16 steps 1-12 (+ HPAC-REQ-054 reverification, + the
    #     inherited NON-REAL hard stop). validate_approval fails closed and
    #     short-circuits on the first failing step. ------------------------
    projection, reasons = validate_approval(
        approval_id,
        approval_store=approval_store,
        authenticated_principal=authenticated_principal,
        context=context,
        consumption_lookup=consumption_lookup,
    )
    if projection is None:
        return None, reasons

    # A valid projection must still be trusted through the registry
    # predicate before this coordinator will build on it (B1 discipline).
    binding = trusted_projection_gate5_binding(projection)
    if binding is None:
        return None, ("gate5_untrusted_validated_authority_projection",)
    bound_approval_id, bound_proof_id, bound_invocation_id = binding

    # --- HPAC-REQ-097 sequence-3 confirmation (coordinator ownership) -----
    # The verifier's HPAC-REQ-054 step 10 created (or idempotently accepted)
    # the PROOF_VERIFIED_AND_BOUND event during reverification. Re-resolve
    # the canonical, provenance-checked chain and confirm the exact binding;
    # capture the event digest for the ephemeral result. Read-only.
    event = lifecycle_store.resolve_gate5_binding_event(bound_proof_id)
    if event is None:
        return None, ("gate5_sequence3_proof_verified_and_bound_absent",)
    record = event.record
    if record.state != STATE_PROOF_VERIFIED_AND_BOUND:
        return None, ("gate5_sequence3_not_bound",)
    genesis_binding = record.binding
    if (
        genesis_binding.get("approval_id") != bound_approval_id
        or genesis_binding.get("invocation_id") != bound_invocation_id
        or genesis_binding.get("principal_id") != projection.principal_id
    ):
        # The verifier's HPAC-REQ-054 chain check (hpac_verifier.py, §40
        # genesis binding compare) already rejects credential / mechanism /
        # challenge / presentation cross-binding before any projection is
        # emitted; this coordinator re-confirms the approval / invocation /
        # principal identity of the sequence-3 event it will vouch for.
        return None, ("gate5_sequence3_cross_binding",)
    if bound_invocation_id != context.invocation_id:
        return None, ("gate5_sequence3_invocation_mismatch",)
    if record.event_digest != event.record_digest:
        return None, ("gate5_sequence3_event_digest_unverified",)

    advisory = tuple(r for r in reasons if r in GATE5_ADVISORY_REASONS)
    unexpected = tuple(r for r in reasons if r not in GATE5_ADVISORY_REASONS)
    if unexpected:
        # validate_approval returned a projection with an unrecognized
        # companion reason — treat as fail-closed rather than guess.
        return None, ("gate5_unexpected_validation_reason:" + ",".join(unexpected),)

    result = Gate5Result(
        projection=projection,
        sequence3_event_digest=record.event_digest,
        proof_id=bound_proof_id,
        approval_id=bound_approval_id,
        invocation_id=bound_invocation_id,
        advisory_reasons=advisory,
        validated_at=projection.validated_at,
        _seal=_GATE5_RESULT_CONSTRUCTOR_SEAL,
    )
    _GATE5_RESULTS.add(result)
    return result, advisory
