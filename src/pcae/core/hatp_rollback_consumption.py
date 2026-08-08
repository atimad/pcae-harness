"""HATP Mandatory Rollback Evidence Consumption Adapter (Phase 149O.18B,
Wave B of the 149O.17 implementation plan).

Implements the requirement subset owned by `CONS` in the 149O.17
HMRC-REQ-001..085 traceability table (`docs/PHASE_149O_17_HATP_MANDATORY_
PRODUCTION_CONSUMPTION_IMPLEMENTATION_PLAN.md` Sec.6/Sec.9.2), per
`docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
(HMRC-001 v1.0) Sec.9-12.

This module owns, and only owns: explicit evidence-ID input, canonical
`HATPEvidenceStore.load`, fresh HATP verification via the existing,
unmodified RAE/HATP engine, gated RAE/HATP approval derivation, truthful
Permission Broker request construction, and a typed, non-persistent
consumption result (HMRC-REQ-017). It performs NO rollback mutation
(HMRC-REQ-036 `_run_git_revert`/file-write loop are never called from
here) and NO cutover-mode resolution (`hatp_mandatory_cutover.py` and the
AG3/AG5 effect functions own that -- 149O.18C/D, not this phase).

Canonical load-and-consumption chain (HMRC-REQ-017), evaluated fresh on
every call, no cache, no persistence (HMRC-REQ-052, HMRC-REQ-076):

    1. explicit evidence_id (caller-supplied, HSCE-REQ-056 domain-checked
       before any I/O, HMRC-REQ-010)
    2. HATPEvidenceStore.load(evidence_id) -> HATPSignedEvidenceEnvelope
       (HSCE-001, existing, unmodified)
    3. resolve_rollback_approval_evidence_with_hatp(...) (RAE-001/HATP-001,
       existing, unmodified) -- reuses the exact three-term conjunction
       (`_derive_hatp_gated_approval_present`) this contract does not
       duplicate (HMRC-REQ-021/022). Looked up under the *proof's own*
       `binding_id` field (the RAE Binding this proof self-asserts it
       attests to) -- `HATPEvidenceStore` and `RollbackApprovalEvidenceStore`
       are two independently-keyed stores (HSCE-REQ-007), so the caller's
       single HSCE `evidence_id` cannot itself double as the RAE lookup
       key; `verify_hatp_proof`'s own identity check independently
       re-derives the *expected* `binding_id` from whichever RAE Binding
       is actually resolved at that key and compares it back against this
       same proof field, so this is never a caller-controllable pointer.
    4. build_permission_broker_request(...) (existing shape, HMRC-REQ-025)
    5. PermissionBroker().evaluate(request) -> ALLOW | DENY | HUMAN_REVIEW
    6. Effect-Truthful PB Requirement (MC-14): the real-effect entrypoint
       always constructs a truthful `simulation_only=False` request; no
       caller can force `simulation_only=True` for it.
    7. only then: the caller's own effect boundary (not reached here --
       this module never performs the effect)

A load failure (missing/corrupt/malformed/digest-mismatched evidence) is
not special-cased into a second code path: it is represented internally
as `hatp_proof=None`, which `verify_hatp_proof` (unmodified) already
maps to `HATPVerificationStatus.MISSING` by construction (HATP-001,
"no_proof_supplied") -- the load-error's specific diagnostic is preserved
separately in the result's `reasons` tuple (HMRC-001 Sec.10's 5-layer
diagnostic-separation discipline) without inventing a parallel failure
chain or a caller-visible fifth result field (HMRC-REQ-075's exact field
list: `evidence_id`, `hatp_status`, `pb_decision`, `reasons`).

Does not overload `hatp_ag_authority.py` (149O.17 plan Sec.9.2): that
module remains completely unmodified, still serving exactly its existing
pre-cutover/`PREPARED` advisory-only role
(`resolve_ag3_gated_rollback_authority`/`resolve_ag5_gated_rollback_
authority`, unconditionally `simulation_only=True`). This module is a
separate, new call path for the actual mandatory gate, because
`hatp_ag_authority._evaluate_rollback_permission` hardcodes
`simulation_only=True` -- structurally incompatible with MC-14's
requirement that a real-effect attempt construct a truthful
`simulation_only=False` request. This module calls the lower-level RAE/
HATP engine (`resolve_rollback_approval_evidence_with_hatp`) directly
instead, exactly as 149O.17 Sec.9.2 selected (option B: move PB
construction out to the new adapter, never add a caller-controlled
`simulation_only` parameter to the existing hardcoded call).

Production dependency closure (F-2 closure pattern, mirrors
`hatp_ag_authority.py:124-125`): `evaluate_for_real_effect`/
`evaluate_for_advisory` resolve `HATPTrustStore`, the hardware provider,
and repository/deployment identity internally -- no production-callable
parameter here accepts a provider/trust-store/evidence-store override
(HMRC-REQ-073). The private, test-only `_internal_consume_hatp_rollback_
evidence` seam accepts explicit overrides for deterministic unit tests.

No public entrypoint accepts a caller-supplied `approval_present`,
`hatp_status`/verification-result, `pb_decision`, provider, trust store,
or `simulation_only` boolean (HMRC-REQ-073, MC-5). The only lever a
caller has over `simulation_only` is *which named function it calls* --
`evaluate_for_real_effect` always uses `False`; `evaluate_for_advisory`
always uses `True` -- never a parameter on either (149O.17 plan Sec.10.1,
item 125's "structural, not caller-supplied Boolean" requirement).

Imports nothing from `hatp_mandatory_cutover.py` (mode-agnostic by
design, 149O.17 plan Sec.9.2 dependency ordering), `agent.py`,
`commands/agent.py`, or `cli.py` (HMRC-REQ-065/068: CLI/effect-function
wiring is a future phase's concern, not this one's).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

from pcae.core.hatp_bootstrap import HATPTrustStore, resolve_canonical_deployment_root
from pcae.core.hatp_evidence_store import HATPEvidenceStore, HATPEvidenceStoreError
from pcae.core.hatp_providers import (
    HATP_HARDWARE_PROVIDER_V1,
    HATPProofVerifierProvider,
    create_production_hardware_provider,
)
from pcae.core.hatp_signed_evidence import HATPSignedEvidenceError, validate_evidence_id
from pcae.core.human_approval_trusted_provenance import (
    HATPVerificationEvidence,
    HATPVerificationStatus,
)
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import (
    ACTION_ROLLBACK,
    DECISION_DENY,
    EXECUTION_CLASS_ROLLBACK,
    PermissionBroker,
    build_permission_broker_request,
)
from pcae.core.repository_identity import read_repository_identity
from pcae.core.rollback_approval_evidence import (
    Ag3RollbackApprovalContext,
    Ag5RollbackApprovalContext,
    RollbackApprovalContext,
    RollbackApprovalEvidenceStore,
    resolve_rollback_approval_evidence_with_hatp,
)

_ROLLBACK_PERMISSION_BROKER_COMPONENT = "COMP-008"  # "Rollback Boundary"

_CAPABILITY_BY_CONTEXT_TYPE = {
    Ag3RollbackApprovalContext: "execute_rollback",
    Ag5RollbackApprovalContext: "build_rollback_execution",
}


class HATPRollbackConsumptionError(Exception):
    """Raised only for a structurally malformed *request* (invalid
    `evidence_id` domain, unrecognized `operation_context` type) --
    rejected before any store access or evaluation is attempted
    (HMRC-REQ-010/014, cheap, no I/O). Never raised for a legitimate
    Consumption Attempt's own outcome (missing evidence, failed
    verification, PB `DENY`/`HUMAN_REVIEW`) -- those are reported through
    `HATPRollbackConsumptionResult` instead, never as an exception
    (mirrors RAE-REQ-042 / the HATP-family fail-closed-but-typed
    discipline)."""


@dataclass(frozen=True)
class HATPRollbackConsumptionRequest:
    """Immutable, authority-neutral consumption request (HMRC-REQ-010/
    013). `operation_context` is exactly one of the two existing,
    unmodified RAE operation-context types (`Ag3RollbackApprovalContext`/
    `Ag5RollbackApprovalContext`) -- the site (AG3/AG5) is determined
    structurally by which type is supplied, not by a second, independent
    free-text `site` field that could disagree with it; an unrecognized
    type is rejected outright (HMRC-001 Sec.6's "unknown site rejected,
    no fallback"). Carries no authority-bearing field: no
    `approval_present`, `hatp_valid`, `verified`, `pb_decision`, `allow`,
    `trusted`, `operational`, or `provider`/`trust_store` field exists on
    this type, by design."""

    evidence_id: str
    operation_context: RollbackApprovalContext

    def __post_init__(self) -> None:
        validate_evidence_id(self.evidence_id)
        if not isinstance(self.operation_context, (Ag3RollbackApprovalContext, Ag5RollbackApprovalContext)):
            raise HATPRollbackConsumptionError(
                "operation_context must be an Ag3RollbackApprovalContext or "
                f"Ag5RollbackApprovalContext, got {type(self.operation_context).__name__} "
                "(unknown rollback site rejected, no fallback)."
            )


@dataclass(frozen=True)
class HATPRollbackConsumptionResult:
    """The sole return type (HMRC-REQ-075's exact field list). No
    `approval_present` field is exposed here (HMRC-REQ-023: the derived
    approval fact stays local to this module's own PB-request
    construction, never a generically reusable `is_approved()`-shaped
    capability). No `executed`/`rollback_succeeded`/`capability_available`
    field exists -- this module never performs an effect and never
    claims execution capability (MC-11/MC-12); whether an effect follows
    is entirely the caller's (a future AG3/AG5 gate's) own decision after
    receiving this result. Attempt-local only: never cached, never
    persisted, never reused across a later Consumption Attempt
    (HMRC-REQ-076)."""

    evidence_id: str
    hatp_status: HATPVerificationStatus
    pb_decision: str
    reasons: Tuple[str, ...]


def _requested_capability_for(operation_context: RollbackApprovalContext) -> str:
    return _CAPABILITY_BY_CONTEXT_TYPE[type(operation_context)]


def _load_envelope_proof_and_assertion(
    evidence_store: HATPEvidenceStore,
    evidence_id: str,
) -> Tuple[Optional[object], HATPVerificationEvidence, Optional[str]]:
    """Step 2 of the HMRC-REQ-017 chain. Returns `(proof, evidence,
    load_error_reason)`. On any load/parse failure, `proof` is `None`
    and `evidence` carries an empty assertion -- `verify_hatp_proof`
    (unmodified) already maps a `None` proof to `HATPVerificationStatus.
    MISSING` ("no_proof_supplied"), so no second, parallel fail-closed
    path is invented here; the specific error class is preserved in
    `load_error_reason` for the result's `reasons` tuple only."""

    try:
        envelope = evidence_store.load(evidence_id)
    except (HATPEvidenceStoreError, HATPSignedEvidenceError) as exc:
        return None, HATPVerificationEvidence(assertion=b""), f"evidence_load_failed:{type(exc).__name__}"
    return envelope.proof, HATPVerificationEvidence(assertion=envelope.provider_assertion), None


def _internal_consume_hatp_rollback_evidence(
    request: HATPRollbackConsumptionRequest,
    *,
    simulation_only: bool,
    hatp_provider: HATPProofVerifierProvider,
    hatp_trust_store: HATPTrustStore,
    current_repository_id: str,
    canonical_deployment_root: str,
    evaluation_time: datetime,
    evidence_store: HATPEvidenceStore,
    rae_evidence_store: Optional[RollbackApprovalEvidenceStore] = None,
    rae_publication_root: Optional[object] = None,
) -> HATPRollbackConsumptionResult:
    """Test-only/internal seam: accepts every dependency explicitly, for
    deterministic unit tests (149O.17 plan item 27's "strong safe
    design"). Never called directly by a production caller -- production
    entrypoints (`evaluate_for_real_effect`/`evaluate_for_advisory`)
    resolve every one of these dependencies themselves and are the only
    functions in this module a production AG3/AG5 caller may use."""

    try:
        proof, hatp_evidence, load_error_reason = _load_envelope_proof_and_assertion(
            evidence_store, request.evidence_id
        )

        # `HATPEvidenceStore` (keyed by the caller-supplied HSCE
        # evidence_id, a 64-hex digest of the proof's own canonical
        # payload) and `RollbackApprovalEvidenceStore` (keyed by the RAE
        # Binding's own, independently-generated `rae-<uuid>`-shaped
        # `evidence_id`) are two separately-keyed stores (HSCE-REQ-007);
        # the caller's single HSCE evidence_id cannot double as the RAE
        # lookup key. The proof itself already carries the pointer to
        # which RAE Binding it attests to (`binding_id`, HATP-001's own
        # field, self-asserted at this point) -- that is the correct RAE
        # lookup key, and `verify_hatp_proof`'s own `_operation_matches`
        # independently re-derives the *expected* `binding_id` from the
        # RAE Binding actually resolved at that key and compares it back
        # against this same proof field, so a mismatched/spoofed pointer
        # cannot itself manufacture a `VALID` result. On a load failure
        # (no proof available), the caller's own evidence_id is reused as
        # a harmless placeholder lookup key -- `hatp_proof=None` already
        # forces `HATPVerificationStatus.MISSING` regardless of whatever,
        # if anything, that placeholder key happens to resolve to.
        rae_evidence_id = proof.binding_id if proof is not None else request.evidence_id

        approval_evidence = resolve_rollback_approval_evidence_with_hatp(
            request.operation_context,
            rae_evidence_id,
            hatp_proof=proof,
            hatp_evidence=hatp_evidence,
            hatp_provider=hatp_provider,
            hatp_trust_store=hatp_trust_store,
            current_repository_id=current_repository_id,
            canonical_deployment_root=canonical_deployment_root,
            evaluation_time=evaluation_time,
            evidence_store=rae_evidence_store,
            publication_root=rae_publication_root,
        )

        pb_request = build_permission_broker_request(
            action_type=ACTION_ROLLBACK,
            execution_class=EXECUTION_CLASS_ROLLBACK,
            requested_component=_ROLLBACK_PERMISSION_BROKER_COMPONENT,
            requested_capability=_requested_capability_for(request.operation_context),
            task_id=request.operation_context.task_id,
            evidence_available=True,
            approval_present=approval_evidence.approval_present,
            simulation_only=simulation_only,
        )
        decision = PermissionBroker().evaluate(pb_request)

        # Diagnostic-layering discipline (HMRC-001 Sec.10 items 85/86):
        # every distinct layer's own diagnostic is preserved in `reasons`
        # -- evidence-load error, RAE result, HATP reasons, substrate
        # readiness, and PB's own decision reason -- never collapsed into
        # one generic "denied" string, even though the closed-vocabulary
        # `pb_decision`/`hatp_status` fields alone cannot carry all of it.
        reasons: Tuple[str, ...] = tuple(
            reason
            for reason in (
                (load_error_reason,)
                + (f"rae_result:{approval_evidence.rae_result.value}",)
                + ((approval_evidence.rae_diagnostic,) if approval_evidence.rae_diagnostic else ())
                + approval_evidence.hatp_reasons
                + approval_evidence.activation_reasons
                + (decision.decision_reason,)
            )
            if reason
        )

        return HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id,
            hatp_status=approval_evidence.hatp_status,
            pb_decision=decision.decision,
            reasons=reasons,
        )
    except Exception as exc:  # noqa: BLE001 - fail-closed umbrella, mirrors RAE-REQ-042/HATP-family discipline
        return HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id,
            hatp_status=HATPVerificationStatus.MALFORMED,
            pb_decision=DECISION_DENY,
            reasons=(f"consumption_internal_error:{type(exc).__name__}",),
        )


def _resolve_production_dependencies(
    root: HarnessPath,
) -> Tuple[str, str, HATPTrustStore, HATPProofVerifierProvider]:
    identity = read_repository_identity(root)
    if identity is None:
        raise HATPRollbackConsumptionError(
            "no repository identity provisioned for this deployment (run 'pcae init')."
        )
    canonical_deployment_root = resolve_canonical_deployment_root(root.path)
    hatp_trust_store = HATPTrustStore.production()
    hatp_provider = create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)
    return identity.repository_instance_id, canonical_deployment_root, hatp_trust_store, hatp_provider


def _production_consume(
    request: HATPRollbackConsumptionRequest,
    *,
    root: HarnessPath,
    simulation_only: bool,
) -> HATPRollbackConsumptionResult:
    evaluation_time = datetime.now(timezone.utc)
    try:
        (
            current_repository_id,
            canonical_deployment_root,
            hatp_trust_store,
            hatp_provider,
        ) = _resolve_production_dependencies(root)
    except Exception as exc:  # noqa: BLE001 - fail-closed umbrella, mirrors hatp_ag_authority.py
        return HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id,
            hatp_status=HATPVerificationStatus.MISSING,
            pb_decision=DECISION_DENY,
            reasons=(f"production_hatp_dependency_resolution_failed:{type(exc).__name__}",),
        )

    return _internal_consume_hatp_rollback_evidence(
        request,
        simulation_only=simulation_only,
        hatp_provider=hatp_provider,
        hatp_trust_store=hatp_trust_store,
        current_repository_id=current_repository_id,
        canonical_deployment_root=canonical_deployment_root,
        evaluation_time=evaluation_time,
        evidence_store=HATPEvidenceStore(root),
    )


def evaluate_for_real_effect(
    request: HATPRollbackConsumptionRequest,
    *,
    root: HarnessPath,
) -> HATPRollbackConsumptionResult:
    """The real-effect production entrypoint (149O.17 plan Sec.10.1):
    always constructs a truthful `simulation_only=False` Permission
    Broker request, structurally, never from a caller-supplied boolean.
    Under the current runtime posture (`Observed/observe/unavailable`,
    `COMP-002` `not_implemented`), POL-005 unconditionally denies any
    `simulation_only=False` request -- this is expected, accepted
    behavior (HMRC-001 Sec.4/Sec.32), not weakened or worked around here.
    This function never performs the rollback effect itself; it returns
    a typed result only. A future AG3/AG5 mandatory gate (149O.18C/D)
    calls this immediately before its own effect boundary, never after."""

    return _production_consume(request, root=root, simulation_only=False)


def evaluate_for_advisory(
    request: HATPRollbackConsumptionRequest,
    *,
    root: HarnessPath,
) -> HATPRollbackConsumptionResult:
    """The advisory/dry-run production entrypoint (149O.17 plan
    Sec.10.1): always constructs `simulation_only=True`. Not used by any
    real production call site as of this phase -- the existing pre-
    cutover/`PREPARED` advisory path continues to use `hatp_ag_
    authority.py` unchanged, not this module (149O.17 plan Sec.9.2).
    This entrypoint exists solely so this module's own test suite can
    exercise the full chain without a production real-effect call site
    depending on it, and so a future AG5 `--dry-run` preview (if HMRC-001
    ever assigns this module a role there) has a truthful, structurally
    `simulation_only=True` entrypoint already available. Never performs
    an effect."""

    return _production_consume(request, root=root, simulation_only=True)


__all__ = [
    "HATPRollbackConsumptionError",
    "HATPRollbackConsumptionRequest",
    "HATPRollbackConsumptionResult",
    "evaluate_for_real_effect",
    "evaluate_for_advisory",
]
