"""HATP Production Authority Adapter for AG3/AG5 — Phase 149O.6, Wave 7
(HATP-REQ-105/106).

This module is the "future AG3/AG5 adapter" `rollback_approval_evidence.
resolve_rollback_approval_evidence_with_hatp`'s own docstring names but
does not itself construct (Wave 6, 149O.4/149O.5): the sole production
entry point through which AG3 (`execute_rollback`) and AG5
(`build_rollback_execution`) may obtain a HATP-gated `approval_present`
fact and consult Permission Broker policy about it.

F-2 closure (149O.5 finding, non-blocking/deferred at the time): the
public functions below accept no `hatp_provider` / `hatp_trust_store`
parameter at all. Every HATP dependency is resolved internally,
exclusively through the Wave-5/Wave-2 production factories
(`hatp_providers.create_production_hardware_provider`,
`hatp_bootstrap.HATPTrustStore.production()`). There is structurally no
argument on `resolve_ag3_gated_rollback_authority` or
`resolve_ag5_gated_rollback_authority` through which an ordinary
production caller -- or a test -- could substitute a test provider or an
arbitrary trust store; this is a stronger guarantee than a runtime
`isinstance` check against a structural `typing.Protocol`, which by
design cannot reliably reject a structurally-conforming fake.

Runtime/execution boundary discipline (unchanged by this module):
Permission Broker's own architecture (`permission_broker_foundation.py`)
remains advisory/`execution_unavailable` system-wide -- no `COMP-002`
execution boundary exists anywhere in PCAE yet. This module therefore
*evaluates* Permission Broker policy against the gated approval fact and
returns the decision for the caller's own governance/audit use, but it
does not itself execute, block, or otherwise gate the real `git revert`
/ file-restore mutation AG3/AG5 perform -- that remains governed exactly
as before this phase, by AG3/AG5's own pre-existing, unchanged
preconditions (`rollback_approval_state`, PER status/divergence checks).
"HATP operational" is not "PCAE Runtime Execution capability"; "Permission
Broker ALLOW" is not "execution" (HATP-001, 149O.1D plan invariants).

Every function here fails closed: any dependency-resolution error
(unsupported platform, unreadable trust store, no hardware provider)
yields `approval_present=False`, never an exception propagated to the
caller and never a silent "treat as approved."
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Union

from pcae.core.hatp_bootstrap import HATPTrustStore, resolve_canonical_deployment_root
from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1, create_production_hardware_provider
from pcae.core.human_approval_trusted_provenance import (
    HATPVerificationEvidence,
    HATPVerificationStatus,
    HumanApprovalProvenanceProof,
)
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import (
    ACTION_ROLLBACK,
    EXECUTION_CLASS_ROLLBACK,
    PermissionBroker,
    PermissionBrokerDecision,
    build_permission_broker_request,
)
from pcae.core.repository_identity import read_repository_identity
from pcae.core.rollback_approval_evidence import (
    Ag3RollbackApprovalContext,
    Ag5RollbackApprovalContext,
    HATPIntegratedApprovalEvidence,
    RepositoryStateBinding,
    RollbackApprovalEvidenceStore,
    RollbackApprovalValidationResult,
    resolve_rollback_approval_evidence_with_hatp,
)

_ROLLBACK_PERMISSION_BROKER_COMPONENT = "COMP-008"  # "Rollback Boundary"


class HATPAuthorityUnavailableError(Exception):
    """Internal-only: production HATP dependency resolution failed.
    Never propagated to a caller of this module's public functions --
    every public function below catches this and every other exception
    and returns a fail-closed `approval_present=False` result instead
    (mirrors RAE-REQ-042 / the Wave-6 fail-closed umbrella)."""


@dataclass(frozen=True)
class GatedRollbackAuthorityResult:
    """The Wave-7 production wiring result for one AG3/AG5 invocation:
    the gated HATP/RAE approval derivation plus the resulting Permission
    Broker evaluation. Carries no execution/dispatch field -- see the
    module docstring's runtime-boundary discipline note."""

    approval_evidence: HATPIntegratedApprovalEvidence
    permission_decision: PermissionBrokerDecision


def _resolve_production_repository_context(root: HarnessPath) -> tuple[str, str]:
    identity = read_repository_identity(root)
    if identity is None:
        raise HATPAuthorityUnavailableError(
            "no repository identity provisioned for this deployment (run 'pcae init')."
        )
    canonical_deployment_root = resolve_canonical_deployment_root(root.path)
    return identity.repository_instance_id, canonical_deployment_root


def _resolve_gated_approval(
    root: HarnessPath,
    operation_context: Union[Ag3RollbackApprovalContext, Ag5RollbackApprovalContext],
    *,
    evidence_id: str,
    hatp_proof: Optional[HumanApprovalProvenanceProof],
    hatp_evidence: HATPVerificationEvidence,
    evaluation_time: Optional[datetime],
    evidence_store: Optional[RollbackApprovalEvidenceStore] = None,
    publication_root: Optional[object] = None,
) -> HATPIntegratedApprovalEvidence:
    """The sole path through which a production AG3/AG5 caller obtains a
    HATP-gated `approval_present` fact. See module docstring for the F-2
    closure this function's signature enforces."""

    eval_time = evaluation_time if evaluation_time is not None else datetime.now(timezone.utc)
    try:
        repository_id, canonical_deployment_root = _resolve_production_repository_context(root)
        hatp_trust_store = HATPTrustStore.production()
        hatp_provider = create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)
    except Exception as exc:  # noqa: BLE001 - fail-closed umbrella
        return HATPIntegratedApprovalEvidence(
            approval_present=False,
            rae_result=RollbackApprovalValidationResult.INVALID,
            rae_diagnostic=None,
            hatp_status=HATPVerificationStatus.MISSING,
            hatp_reasons=("production_hatp_dependency_resolution_failed",),
            activation_operational=False,
            activation_reasons=(),
            diagnostic=f"HATP production authority dependency resolution failed (fail-closed): {exc}",
        )

    return resolve_rollback_approval_evidence_with_hatp(
        operation_context,
        evidence_id,
        hatp_proof=hatp_proof,
        hatp_evidence=hatp_evidence,
        hatp_provider=hatp_provider,
        hatp_trust_store=hatp_trust_store,
        current_repository_id=repository_id,
        canonical_deployment_root=canonical_deployment_root,
        evaluation_time=eval_time,
        evidence_store=evidence_store,
        publication_root=publication_root,
    )


def _evaluate_rollback_permission(
    *,
    task_id: Optional[str],
    requested_capability: str,
    approval_present: bool,
) -> PermissionBrokerDecision:
    """Constructs and evaluates a Permission Broker request for the
    rollback execution_class, with `approval_present` sourced
    exclusively from the caller's already-derived gated fact -- never a
    raw caller-supplied boolean (this function has no such parameter)."""

    request = build_permission_broker_request(
        action_type=ACTION_ROLLBACK,
        execution_class=EXECUTION_CLASS_ROLLBACK,
        requested_component=_ROLLBACK_PERMISSION_BROKER_COMPONENT,
        requested_capability=requested_capability,
        task_id=task_id,
        evidence_available=True,
        approval_present=approval_present,
        simulation_only=True,
    )
    return PermissionBroker().evaluate(request)


def resolve_ag3_gated_rollback_authority(
    root: HarnessPath,
    *,
    job_id: str,
    original_commit_sha: str,
    task_id: Optional[str],
    repository_state: RepositoryStateBinding,
    evidence_id: str,
    hatp_proof: Optional[HumanApprovalProvenanceProof],
    hatp_evidence: HATPVerificationEvidence,
    evaluation_time: Optional[datetime] = None,
    evidence_store: Optional[RollbackApprovalEvidenceStore] = None,
    publication_root: Optional[object] = None,
) -> GatedRollbackAuthorityResult:
    """AG3 (`execute_rollback`) production authority-consumption entry
    point (HATP-REQ-105). No caller-supplied `approval_present` boolean
    parameter exists on this signature. `evidence_store`/
    `publication_root` mirror `resolve_rollback_approval_evidence_with_
    hatp`'s own optional overrides (RAE evidence *location*, not a
    trust/authority dependency -- unrelated to F-2, which concerns only
    `hatp_provider`/`hatp_trust_store`); both default to the real
    production locations."""

    context = Ag3RollbackApprovalContext(
        job_id=job_id,
        original_commit_sha=original_commit_sha,
        task_id=task_id,
        repository_state=repository_state,
    )
    approval_evidence = _resolve_gated_approval(
        root,
        context,
        evidence_id=evidence_id,
        hatp_proof=hatp_proof,
        hatp_evidence=hatp_evidence,
        evaluation_time=evaluation_time,
        evidence_store=evidence_store,
        publication_root=publication_root,
    )
    decision = _evaluate_rollback_permission(
        task_id=task_id,
        requested_capability="execute_rollback",
        approval_present=approval_evidence.approval_present,
    )
    return GatedRollbackAuthorityResult(approval_evidence=approval_evidence, permission_decision=decision)


def resolve_ag5_gated_rollback_authority(
    root: HarnessPath,
    *,
    per_id: str,
    ecp_id: str,
    task_id: Optional[str],
    repository_state: RepositoryStateBinding,
    evidence_id: str,
    hatp_proof: Optional[HumanApprovalProvenanceProof],
    hatp_evidence: HATPVerificationEvidence,
    evaluation_time: Optional[datetime] = None,
    evidence_store: Optional[RollbackApprovalEvidenceStore] = None,
    publication_root: Optional[object] = None,
) -> GatedRollbackAuthorityResult:
    """AG5 (`build_rollback_execution`) production authority-consumption
    entry point (HATP-REQ-105/106). Mirrors
    `resolve_ag3_gated_rollback_authority`; no caller-supplied
    `approval_present` boolean parameter exists on this signature."""

    context = Ag5RollbackApprovalContext(
        per_id=per_id,
        ecp_id=ecp_id,
        task_id=task_id,
        repository_state=repository_state,
    )
    approval_evidence = _resolve_gated_approval(
        root,
        context,
        evidence_id=evidence_id,
        hatp_proof=hatp_proof,
        hatp_evidence=hatp_evidence,
        evaluation_time=evaluation_time,
        evidence_store=evidence_store,
        publication_root=publication_root,
    )
    decision = _evaluate_rollback_permission(
        task_id=task_id,
        requested_capability="build_rollback_execution",
        approval_present=approval_evidence.approval_present,
    )
    return GatedRollbackAuthorityResult(approval_evidence=approval_evidence, permission_decision=decision)


__all__ = [
    "HATPAuthorityUnavailableError",
    "GatedRollbackAuthorityResult",
    "resolve_ag3_gated_rollback_authority",
    "resolve_ag5_gated_rollback_authority",
]
