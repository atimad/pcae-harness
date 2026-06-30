"""Human approval gate model — Phase 97D.

Design-only models for human approval requests, decisions, scopes, denial
reasons, expiry, revocation, and verification.  All artifacts are non-executing
and non-authorizing in the current system.

No real backend invocation, no adapter execution, no subprocess, no network,
no shell, no apply, no commit, no push.
"""

from __future__ import annotations

import hashlib
import json as _json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "1.0"

# ── Approval decision statuses ─────────────────────────────────────────────

APPROVAL_DECISION_APPROVED = "approved"
APPROVAL_DECISION_DENIED = "denied"
APPROVAL_DECISION_REVOKED = "revoked"
APPROVAL_DECISION_EXPIRED = "expired"

VALID_APPROVAL_DECISIONS: frozenset[str] = frozenset({
    APPROVAL_DECISION_APPROVED,
    APPROVAL_DECISION_DENIED,
    APPROVAL_DECISION_REVOKED,
    APPROVAL_DECISION_EXPIRED,
})

# ── Approval request statuses ──────────────────────────────────────────────

APPROVAL_STATUS_PENDING = "pending"
APPROVAL_STATUS_APPROVED = "approved"
APPROVAL_STATUS_DENIED = "denied"
APPROVAL_STATUS_REVOKED = "revoked"
APPROVAL_STATUS_EXPIRED = "expired"

VALID_APPROVAL_STATUSES: frozenset[str] = frozenset({
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_DENIED,
    APPROVAL_STATUS_REVOKED,
    APPROVAL_STATUS_EXPIRED,
})

# ── Approval scopes ────────────────────────────────────────────────────────

SCOPE_READINESS_REVIEW = "readiness_review"
SCOPE_BACKEND_INVOCATION_PREFLIGHT_REVIEW = "backend_invocation_preflight_review"
SCOPE_ADAPTER_INVOCATION_PREFLIGHT_REVIEW = "adapter_invocation_preflight_review"
SCOPE_BACKEND_INVOCATION = "backend_invocation"
SCOPE_ADAPTER_EXECUTION = "adapter_execution"
SCOPE_OUTPUT_REVIEW = "output_review"
SCOPE_APPLY = "apply"
SCOPE_COMMIT = "commit"
SCOPE_PUSH = "push"

VALID_APPROVAL_SCOPES: frozenset[str] = frozenset({
    SCOPE_READINESS_REVIEW,
    SCOPE_BACKEND_INVOCATION_PREFLIGHT_REVIEW,
    SCOPE_ADAPTER_INVOCATION_PREFLIGHT_REVIEW,
    SCOPE_BACKEND_INVOCATION,
    SCOPE_ADAPTER_EXECUTION,
    SCOPE_OUTPUT_REVIEW,
    SCOPE_APPLY,
    SCOPE_COMMIT,
    SCOPE_PUSH,
})

# Scopes that are review-only (no execution even in future)
REVIEW_ONLY_SCOPES: frozenset[str] = frozenset({
    SCOPE_READINESS_REVIEW,
    SCOPE_BACKEND_INVOCATION_PREFLIGHT_REVIEW,
    SCOPE_ADAPTER_INVOCATION_PREFLIGHT_REVIEW,
    SCOPE_OUTPUT_REVIEW,
})

# Scopes that are execution-adjacent (future execution phases)
EXECUTION_SCOPES: frozenset[str] = frozenset({
    SCOPE_BACKEND_INVOCATION,
    SCOPE_ADAPTER_EXECUTION,
})

# Scopes that are mutation-adjacent (future apply/commit/push phases)
MUTATION_SCOPES: frozenset[str] = frozenset({
    SCOPE_APPLY,
    SCOPE_COMMIT,
    SCOPE_PUSH,
})

# ── Denial reasons ─────────────────────────────────────────────────────────

DENIED_MISSING_READINESS = "denied_missing_readiness"
DENIED_MISSING_BACKEND_REQUEST = "denied_missing_backend_request"
DENIED_MISSING_ADAPTER_REQUEST = "denied_missing_adapter_request"
DENIED_MISSING_EVIDENCE_CHAIN = "denied_missing_evidence_chain"
DENIED_MISSING_ARTIFACT_VERIFICATION = "denied_missing_artifact_verification"
DENIED_NO_GO_CONDITION_PRESENT = "denied_no_go_condition_present"
DENIED_SCOPE_MISMATCH = "denied_scope_mismatch"
DENIED_TASK_MISMATCH = "denied_task_mismatch"
DENIED_PHASE_MISMATCH = "denied_phase_mismatch"
DENIED_EXPIRED = "denied_expired"
DENIED_REVOKED = "denied_revoked"
DENIED_STALE_ARTIFACT = "denied_stale_artifact"
DENIED_FAILED_VERIFICATION = "denied_failed_verification"
DENIED_FORBIDDEN_SCOPE = "denied_forbidden_scope"
DENIED_BYPASS_PERMISSIONS = "denied_bypass_permissions"
DENIED_RAW_GIT_PATH = "denied_raw_git_path"
DENIED_NO_VERIFY_ATTEMPT = "denied_no_verify_attempt"
DENIED_FORCE_PUSH_ATTEMPT = "denied_force_push_attempt"
DENIED_UNKNOWN_SCHEMA = "denied_unknown_schema"
DENIED_CONFLICTING_SAFETY_FLAGS = "denied_conflicting_safety_flags"
DENIED_REQUESTED_AUTHORIZATION_OUT_OF_SCOPE = "denied_requested_authorization_out_of_scope"

VALID_DENIAL_REASONS: frozenset[str] = frozenset({
    DENIED_MISSING_READINESS,
    DENIED_MISSING_BACKEND_REQUEST,
    DENIED_MISSING_ADAPTER_REQUEST,
    DENIED_MISSING_EVIDENCE_CHAIN,
    DENIED_MISSING_ARTIFACT_VERIFICATION,
    DENIED_NO_GO_CONDITION_PRESENT,
    DENIED_SCOPE_MISMATCH,
    DENIED_TASK_MISMATCH,
    DENIED_PHASE_MISMATCH,
    DENIED_EXPIRED,
    DENIED_REVOKED,
    DENIED_STALE_ARTIFACT,
    DENIED_FAILED_VERIFICATION,
    DENIED_FORBIDDEN_SCOPE,
    DENIED_BYPASS_PERMISSIONS,
    DENIED_RAW_GIT_PATH,
    DENIED_NO_VERIFY_ATTEMPT,
    DENIED_FORCE_PUSH_ATTEMPT,
    DENIED_UNKNOWN_SCHEMA,
    DENIED_CONFLICTING_SAFETY_FLAGS,
    DENIED_REQUESTED_AUTHORIZATION_OUT_OF_SCOPE,
})

# ── Default expiry per scope (minutes) ─────────────────────────────────────

DEFAULT_EXPIRY_MINUTES: dict[str, int] = {
    SCOPE_READINESS_REVIEW: 480,   # 8 hours
    SCOPE_BACKEND_INVOCATION_PREFLIGHT_REVIEW: 240,  # 4 hours
    SCOPE_ADAPTER_INVOCATION_PREFLIGHT_REVIEW: 240,
    SCOPE_BACKEND_INVOCATION: 60,   # 1 hour
    SCOPE_ADAPTER_EXECUTION: 60,
    SCOPE_OUTPUT_REVIEW: 120,       # 2 hours
    SCOPE_APPLY: 30,                # 30 minutes
    SCOPE_COMMIT: 15,               # 15 minutes
    SCOPE_PUSH: 10,                 # 10 minutes
}

MAX_EXPIRY_MINUTES: dict[str, int] = {
    SCOPE_READINESS_REVIEW: 1440,  # 24 hours
    SCOPE_BACKEND_INVOCATION_PREFLIGHT_REVIEW: 720,
    SCOPE_ADAPTER_INVOCATION_PREFLIGHT_REVIEW: 720,
    SCOPE_BACKEND_INVOCATION: 240,
    SCOPE_ADAPTER_EXECUTION: 240,
    SCOPE_OUTPUT_REVIEW: 480,
    SCOPE_APPLY: 120,
    SCOPE_COMMIT: 60,
    SCOPE_PUSH: 30,
}


def _utc_now() -> datetime:
    """Return current UTC datetime (pluggable for testing)."""
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    """Return a new UUID string."""
    return str(uuid.uuid4())


def _compute_digest(data: dict[str, Any]) -> str:
    """Compute a SHA-256 digest of a JSON-serializable dict (sorted keys)."""
    canonical = _json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# Approval Request
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ApprovalRequest:
    """A human approval request.  Non-executing — metadata/intent only.

    All authorization flags are forced false.  Even if approved later,
    this request artifact does not authorize execution.
    """

    approval_request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    requested_by: str = ""
    requested_at_utc: str = ""
    requested_action_class: str = ""
    requested_scope: str = ""
    readiness_artifact_ref: str = ""
    backend_invocation_request_ref: str = ""
    adapter_invocation_request_ref: str = ""
    evidence_chain_ref: str = ""
    artifact_verification_ref: str = ""
    execution_boundary_proof_ref: str = ""
    no_go_conditions: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    risk_summary: str = ""
    requested_authorizations: list[str] = field(default_factory=list)
    explicitly_not_requested: list[str] = field(default_factory=list)
    expires_at_utc: str = ""
    human_review_required: bool = True
    approval_status: str = APPROVAL_STATUS_PENDING
    execution_available: bool = False
    execution_authorized: bool = False
    backend_invocation_authorized: bool = False
    adapter_execution_authorized: bool = False
    apply_authorized: bool = False
    commit_authorized: bool = False
    push_authorized: bool = False
    simulation_only: bool = True
    no_execution: bool = True
    schema_version: str = SCHEMA_VERSION
    digest: str = ""

    def __post_init__(self) -> None:
        if not self.approval_request_id:
            self.approval_request_id = _new_uuid()
        if not self.requested_at_utc:
            self.requested_at_utc = _utc_now().isoformat()
        # Force non-executing invariants
        self.execution_available = False
        self.execution_authorized = False
        self.backend_invocation_authorized = False
        self.adapter_execution_authorized = False
        self.apply_authorized = False
        self.commit_authorized = False
        self.push_authorized = False
        self.simulation_only = True
        self.no_execution = True
        self.human_review_required = True

    def validate(self) -> list[str]:
        """Validate the approval request. Returns list of issue strings."""
        issues: list[str] = []
        if not self.approval_request_id:
            issues.append("approval_request_id is required")
        if not self.phase_id:
            issues.append("phase_id is required")
        if not self.task_id:
            issues.append("task_id is required")
        if not self.requested_by:
            issues.append("requested_by is required")
        if self.requested_scope and self.requested_scope not in VALID_APPROVAL_SCOPES:
            issues.append(f"invalid requested_scope: {self.requested_scope!r}")
        if self.approval_status not in VALID_APPROVAL_STATUSES:
            issues.append(f"invalid approval_status: {self.approval_status!r}")
        if self.execution_available:
            issues.append("execution_available must be False")
        if self.execution_authorized:
            issues.append("execution_authorized must be False")
        if not self.simulation_only:
            issues.append("simulation_only must be True")
        if not self.no_execution:
            issues.append("no_execution must be True")
        if not self.schema_version:
            issues.append("schema_version is required")
        return issues

    def compute_digest(self) -> str:
        """Compute and return the digest of this request's core fields."""
        payload = {
            "approval_request_id": self.approval_request_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "requested_by": self.requested_by,
            "requested_at_utc": self.requested_at_utc,
            "requested_action_class": self.requested_action_class,
            "requested_scope": self.requested_scope,
            "readiness_artifact_ref": self.readiness_artifact_ref,
            "backend_invocation_request_ref": self.backend_invocation_request_ref,
            "adapter_invocation_request_ref": self.adapter_invocation_request_ref,
            "evidence_chain_ref": self.evidence_chain_ref,
            "artifact_verification_ref": self.artifact_verification_ref,
            "execution_boundary_proof_ref": self.execution_boundary_proof_ref,
            "no_go_conditions": sorted(self.no_go_conditions),
            "missing_evidence": sorted(self.missing_evidence),
            "risk_summary": self.risk_summary,
            "requested_authorizations": sorted(self.requested_authorizations),
            "explicitly_not_requested": sorted(self.explicitly_not_requested),
            "expires_at_utc": self.expires_at_utc,
            "schema_version": self.schema_version,
        }
        self.digest = _compute_digest(payload)
        return self.digest

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "approval_request_id": self.approval_request_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "requested_by": self.requested_by,
            "requested_at_utc": self.requested_at_utc,
            "requested_action_class": self.requested_action_class,
            "requested_scope": self.requested_scope,
            "readiness_artifact_ref": self.readiness_artifact_ref,
            "backend_invocation_request_ref": self.backend_invocation_request_ref,
            "adapter_invocation_request_ref": self.adapter_invocation_request_ref,
            "evidence_chain_ref": self.evidence_chain_ref,
            "artifact_verification_ref": self.artifact_verification_ref,
            "execution_boundary_proof_ref": self.execution_boundary_proof_ref,
            "no_go_conditions": self.no_go_conditions,
            "missing_evidence": self.missing_evidence,
            "risk_summary": self.risk_summary,
            "requested_authorizations": self.requested_authorizations,
            "explicitly_not_requested": self.explicitly_not_requested,
            "expires_at_utc": self.expires_at_utc,
            "human_review_required": self.human_review_required,
            "approval_status": self.approval_status,
            "execution_available": self.execution_available,
            "execution_authorized": self.execution_authorized,
            "backend_invocation_authorized": self.backend_invocation_authorized,
            "adapter_execution_authorized": self.adapter_execution_authorized,
            "apply_authorized": self.apply_authorized,
            "commit_authorized": self.commit_authorized,
            "push_authorized": self.push_authorized,
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "digest": self.digest,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ApprovalRequest":
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in field_names})

    def is_non_executing(self) -> bool:
        """Confirm the request is non-executing (all flags forced false)."""
        return (
            not self.execution_available
            and not self.execution_authorized
            and not self.backend_invocation_authorized
            and not self.adapter_execution_authorized
            and not self.apply_authorized
            and not self.commit_authorized
            and not self.push_authorized
            and self.simulation_only
            and self.no_execution
        )


# ═══════════════════════════════════════════════════════════════════════════
# Approval Decision
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ApprovalDecision:
    """A human approval decision.  Non-executing — intent record only.

    Even an "approved" decision does not authorize execution in the
    current phase.  All authorization flags are forced false.
    """

    approval_decision_id: str = ""
    approval_request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    decided_by: str = ""
    decided_at_utc: str = ""
    decision: str = APPROVAL_DECISION_APPROVED
    approved_action_classes: list[str] = field(default_factory=list)
    denied_action_classes: list[str] = field(default_factory=list)
    approval_scope: str = ""
    approval_constraints: list[str] = field(default_factory=list)
    approval_exclusions: list[str] = field(default_factory=list)
    expiry: str = ""
    revocation_ref: str = ""
    readiness_artifact_ref: str = ""
    backend_invocation_request_ref: str = ""
    adapter_invocation_request_ref: str = ""
    evidence_chain_ref: str = ""
    artifact_verification_ref: str = ""
    human_confirmation_text: str = ""
    non_transferable: bool = True
    no_override_no_go: bool = True
    no_override_failed_verification: bool = True
    no_override_scope_violation: bool = True
    no_raw_git_allowed: bool = True
    no_no_verify_allowed: bool = True
    no_force_push_allowed: bool = True
    execution_available: bool = False
    execution_authorized: bool = False
    backend_invocation_authorized: bool = False
    adapter_execution_authorized: bool = False
    apply_authorized: bool = False
    commit_authorized: bool = False
    push_authorized: bool = False
    simulation_only: bool = True
    no_execution: bool = True
    schema_version: str = SCHEMA_VERSION
    digest: str = ""

    def __post_init__(self) -> None:
        if not self.approval_decision_id:
            self.approval_decision_id = _new_uuid()
        if not self.decided_at_utc:
            self.decided_at_utc = _utc_now().isoformat()
        # Force non-executing invariants regardless of decision value
        self.execution_available = False
        self.execution_authorized = False
        self.backend_invocation_authorized = False
        self.adapter_execution_authorized = False
        self.apply_authorized = False
        self.commit_authorized = False
        self.push_authorized = False
        self.simulation_only = True
        self.no_execution = True
        self.non_transferable = True
        self.no_override_no_go = True
        self.no_override_failed_verification = True
        self.no_override_scope_violation = True
        self.no_raw_git_allowed = True
        self.no_no_verify_allowed = True
        self.no_force_push_allowed = True

    def validate(self) -> list[str]:
        """Validate the approval decision. Returns list of issue strings."""
        issues: list[str] = []
        if not self.approval_decision_id:
            issues.append("approval_decision_id is required")
        if not self.approval_request_id:
            issues.append("approval_request_id is required")
        if not self.phase_id:
            issues.append("phase_id is required")
        if not self.task_id:
            issues.append("task_id is required")
        if not self.decided_by:
            issues.append("decided_by is required")
        if self.decision not in VALID_APPROVAL_DECISIONS:
            issues.append(f"invalid decision: {self.decision!r}")
        if self.approval_scope and self.approval_scope not in VALID_APPROVAL_SCOPES:
            issues.append(f"invalid approval_scope: {self.approval_scope!r}")
        if self.execution_available:
            issues.append("execution_available must be False")
        if self.execution_authorized:
            issues.append("execution_authorized must be False")
        if not self.simulation_only:
            issues.append("simulation_only must be True")
        if not self.no_execution:
            issues.append("no_execution must be True")
        if not self.non_transferable:
            issues.append("non_transferable must be True")
        if not self.no_override_no_go:
            issues.append("no_override_no_go must be True")
        if not self.no_raw_git_allowed:
            issues.append("no_raw_git_allowed must be True")
        if not self.no_no_verify_allowed:
            issues.append("no_no_verify_allowed must be True")
        if not self.no_force_push_allowed:
            issues.append("no_force_push_allowed must be True")
        return issues

    def compute_digest(self) -> str:
        """Compute and return the digest of this decision's core fields."""
        payload = {
            "approval_decision_id": self.approval_decision_id,
            "approval_request_id": self.approval_request_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "decided_by": self.decided_by,
            "decided_at_utc": self.decided_at_utc,
            "decision": self.decision,
            "approved_action_classes": sorted(self.approved_action_classes),
            "denied_action_classes": sorted(self.denied_action_classes),
            "approval_scope": self.approval_scope,
            "approval_constraints": sorted(self.approval_constraints),
            "approval_exclusions": sorted(self.approval_exclusions),
            "expiry": self.expiry,
            "revocation_ref": self.revocation_ref,
            "readiness_artifact_ref": self.readiness_artifact_ref,
            "backend_invocation_request_ref": self.backend_invocation_request_ref,
            "adapter_invocation_request_ref": self.adapter_invocation_request_ref,
            "evidence_chain_ref": self.evidence_chain_ref,
            "artifact_verification_ref": self.artifact_verification_ref,
            "human_confirmation_text": self.human_confirmation_text,
            "schema_version": self.schema_version,
        }
        self.digest = _compute_digest(payload)
        return self.digest

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "approval_decision_id": self.approval_decision_id,
            "approval_request_id": self.approval_request_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "decided_by": self.decided_by,
            "decided_at_utc": self.decided_at_utc,
            "decision": self.decision,
            "approved_action_classes": self.approved_action_classes,
            "denied_action_classes": self.denied_action_classes,
            "approval_scope": self.approval_scope,
            "approval_constraints": self.approval_constraints,
            "approval_exclusions": self.approval_exclusions,
            "expiry": self.expiry,
            "revocation_ref": self.revocation_ref,
            "readiness_artifact_ref": self.readiness_artifact_ref,
            "backend_invocation_request_ref": self.backend_invocation_request_ref,
            "adapter_invocation_request_ref": self.adapter_invocation_request_ref,
            "evidence_chain_ref": self.evidence_chain_ref,
            "artifact_verification_ref": self.artifact_verification_ref,
            "human_confirmation_text": self.human_confirmation_text,
            "non_transferable": self.non_transferable,
            "no_override_no_go": self.no_override_no_go,
            "no_override_failed_verification": self.no_override_failed_verification,
            "no_override_scope_violation": self.no_override_scope_violation,
            "no_raw_git_allowed": self.no_raw_git_allowed,
            "no_no_verify_allowed": self.no_no_verify_allowed,
            "no_force_push_allowed": self.no_force_push_allowed,
            "execution_available": self.execution_available,
            "execution_authorized": self.execution_authorized,
            "backend_invocation_authorized": self.backend_invocation_authorized,
            "adapter_execution_authorized": self.adapter_execution_authorized,
            "apply_authorized": self.apply_authorized,
            "commit_authorized": self.commit_authorized,
            "push_authorized": self.push_authorized,
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "digest": self.digest,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ApprovalDecision":
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in field_names})

    def is_non_executing(self) -> bool:
        """Confirm the decision is non-executing (all flags forced false)."""
        return (
            not self.execution_available
            and not self.execution_authorized
            and not self.backend_invocation_authorized
            and not self.adapter_execution_authorized
            and not self.apply_authorized
            and not self.commit_authorized
            and not self.push_authorized
            and self.simulation_only
            and self.no_execution
        )


# ═══════════════════════════════════════════════════════════════════════════
# Approval Verifier
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ApprovalVerificationResult:
    """Result of verifying an approval decision against a request context."""

    verified: bool = False
    denial_reasons: list[str] = field(default_factory=list)
    checked_fields: list[str] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "denial_reasons": self.denial_reasons,
            "checked_fields": self.checked_fields,
            "detail": self.detail,
        }


def verify_approval(
    decision: ApprovalDecision,
    request: ApprovalRequest,
    expected_task_id: str = "",
    expected_phase_id: str = "",
    expected_backend_request_ref: str = "",
    expected_adapter_request_ref: str = "",
    expected_evidence_chain_ref: str = "",
    expected_artifact_verification_ref: str = "",
    expected_readiness_ref: str = "",
    no_go_conditions_present: list[str] | None = None,
    artifact_verification_failed: bool = False,
    bypass_permissions_detected: bool = False,
    raw_git_detected: bool = False,
    no_verify_detected: bool = False,
    force_push_detected: bool = False,
) -> ApprovalVerificationResult:
    """Verify an approval decision against a request and context.

    This function is always fail-closed: if any check fails, verified=False.
    Execution remains unavailable regardless of verification outcome.
    """
    denial_reasons: list[str] = []
    checked: list[str] = []

    # 1. Schema version
    checked.append("schema_version")
    if decision.schema_version != SCHEMA_VERSION:
        denial_reasons.append(DENIED_UNKNOWN_SCHEMA)

    # 2. Decision status
    checked.append("decision_status")
    if decision.decision == APPROVAL_DECISION_DENIED:
        denial_reasons.append("denied_by_operator")
    elif decision.decision == APPROVAL_DECISION_REVOKED:
        denial_reasons.append(DENIED_REVOKED)
    elif decision.decision == APPROVAL_DECISION_EXPIRED:
        denial_reasons.append(DENIED_EXPIRED)
    elif decision.decision != APPROVAL_DECISION_APPROVED:
        denial_reasons.append(f"denied_unknown_decision_{decision.decision}")

    # 3. Non-transferable
    checked.append("non_transferable")
    if not decision.non_transferable:
        denial_reasons.append("denied_transferable_approval")

    # 4. Safety flag invariants
    checked.append("safety_flags")
    if not decision.no_override_no_go:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if not decision.no_override_failed_verification:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if not decision.no_override_scope_violation:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)

    # 5. Git protection flags
    checked.append("git_protection_flags")
    if not decision.no_raw_git_allowed:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if not decision.no_no_verify_allowed:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if not decision.no_force_push_allowed:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)

    # 6. Authorization flags must be false
    checked.append("authorization_flags")
    if decision.execution_available:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if decision.execution_authorized:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if decision.backend_invocation_authorized:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if decision.adapter_execution_authorized:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if decision.apply_authorized:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if decision.commit_authorized:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if decision.push_authorized:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if not decision.simulation_only:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)
    if not decision.no_execution:
        denial_reasons.append(DENIED_CONFLICTING_SAFETY_FLAGS)

    # 7. Task ID
    checked.append("task_id")
    if expected_task_id and decision.task_id != expected_task_id:
        denial_reasons.append(DENIED_TASK_MISMATCH)
    if expected_task_id and request.task_id != expected_task_id:
        denial_reasons.append(DENIED_TASK_MISMATCH)

    # 8. Phase ID
    checked.append("phase_id")
    if expected_phase_id and decision.phase_id != expected_phase_id:
        denial_reasons.append(DENIED_PHASE_MISMATCH)
    if expected_phase_id and request.phase_id != expected_phase_id:
        denial_reasons.append(DENIED_PHASE_MISMATCH)

    # 9. Expiry
    checked.append("expiry")
    if decision.expiry:
        try:
            expiry_dt = datetime.fromisoformat(decision.expiry)
            if expiry_dt <= _utc_now():
                denial_reasons.append(DENIED_EXPIRED)
        except (ValueError, TypeError):
            denial_reasons.append(DENIED_EXPIRED)
    if request.expires_at_utc:
        try:
            req_expiry = datetime.fromisoformat(request.expires_at_utc)
            if req_expiry <= _utc_now():
                denial_reasons.append(DENIED_EXPIRED)
        except (ValueError, TypeError):
            denial_reasons.append(DENIED_EXPIRED)

    # 10. Revocation
    checked.append("revocation")
    if decision.revocation_ref:
        denial_reasons.append(DENIED_REVOKED)

    # 11. Scope
    checked.append("scope")
    if decision.approval_scope and request.requested_scope:
        if decision.approval_scope != request.requested_scope:
            denial_reasons.append(DENIED_SCOPE_MISMATCH)

    # 12. Scope exclusions
    checked.append("scope_exclusions")
    if request.requested_action_class in decision.approval_exclusions:
        denial_reasons.append(DENIED_FORBIDDEN_SCOPE)
    if request.requested_scope in decision.approval_exclusions:
        denial_reasons.append(DENIED_FORBIDDEN_SCOPE)

    # 13. Readiness ref
    checked.append("readiness_ref")
    if expected_readiness_ref:
        if decision.readiness_artifact_ref != expected_readiness_ref:
            denial_reasons.append(DENIED_MISSING_READINESS)
        if request.readiness_artifact_ref != expected_readiness_ref:
            denial_reasons.append(DENIED_MISSING_READINESS)
    if not decision.readiness_artifact_ref:
        denial_reasons.append(DENIED_MISSING_READINESS)

    # 14. Backend request ref
    checked.append("backend_request_ref")
    if expected_backend_request_ref:
        if decision.backend_invocation_request_ref != expected_backend_request_ref:
            denial_reasons.append(DENIED_MISSING_BACKEND_REQUEST)
    scope_needs_backend = decision.approval_scope in {
        SCOPE_BACKEND_INVOCATION,
        SCOPE_BACKEND_INVOCATION_PREFLIGHT_REVIEW,
    }
    if scope_needs_backend and not decision.backend_invocation_request_ref:
        denial_reasons.append(DENIED_MISSING_BACKEND_REQUEST)

    # 15. Adapter request ref
    checked.append("adapter_request_ref")
    if expected_adapter_request_ref:
        if decision.adapter_invocation_request_ref != expected_adapter_request_ref:
            denial_reasons.append(DENIED_MISSING_ADAPTER_REQUEST)
    scope_needs_adapter = decision.approval_scope in {
        SCOPE_ADAPTER_EXECUTION,
        SCOPE_ADAPTER_INVOCATION_PREFLIGHT_REVIEW,
    }
    if scope_needs_adapter and not decision.adapter_invocation_request_ref:
        denial_reasons.append(DENIED_MISSING_ADAPTER_REQUEST)

    # 16. Evidence chain ref
    checked.append("evidence_chain_ref")
    if expected_evidence_chain_ref:
        if decision.evidence_chain_ref != expected_evidence_chain_ref:
            denial_reasons.append(DENIED_MISSING_EVIDENCE_CHAIN)
    if not decision.evidence_chain_ref:
        denial_reasons.append(DENIED_MISSING_EVIDENCE_CHAIN)

    # 17. Artifact verification ref
    checked.append("artifact_verification_ref")
    if expected_artifact_verification_ref:
        if decision.artifact_verification_ref != expected_artifact_verification_ref:
            denial_reasons.append(DENIED_MISSING_ARTIFACT_VERIFICATION)

    # 18. Artifact verification failed
    checked.append("artifact_verification_passed")
    if artifact_verification_failed:
        denial_reasons.append(DENIED_FAILED_VERIFICATION)

    # 19. No-go conditions
    checked.append("no_go_conditions")
    actual_no_gos = no_go_conditions_present or []
    if actual_no_gos:
        denial_reasons.append(DENIED_NO_GO_CONDITION_PRESENT)

    # 20. Bypass permissions
    checked.append("bypass_permissions")
    if bypass_permissions_detected:
        denial_reasons.append(DENIED_BYPASS_PERMISSIONS)

    # 21. Raw git
    checked.append("raw_git")
    if raw_git_detected:
        denial_reasons.append(DENIED_RAW_GIT_PATH)

    # 22. No-verify
    checked.append("no_verify")
    if no_verify_detected:
        denial_reasons.append(DENIED_NO_VERIFY_ATTEMPT)

    # 23. Force push
    checked.append("force_push")
    if force_push_detected:
        denial_reasons.append(DENIED_FORCE_PUSH_ATTEMPT)

    # 24. Digest verification — compute fresh without mutating stored digest
    checked.append("digest")
    if decision.digest:
        stored = decision.digest
        fresh = _compute_digest({
            "approval_decision_id": decision.approval_decision_id,
            "approval_request_id": decision.approval_request_id,
            "phase_id": decision.phase_id,
            "task_id": decision.task_id,
            "decided_by": decision.decided_by,
            "decided_at_utc": decision.decided_at_utc,
            "decision": decision.decision,
            "approved_action_classes": sorted(decision.approved_action_classes),
            "denied_action_classes": sorted(decision.denied_action_classes),
            "approval_scope": decision.approval_scope,
            "approval_constraints": sorted(decision.approval_constraints),
            "approval_exclusions": sorted(decision.approval_exclusions),
            "expiry": decision.expiry,
            "revocation_ref": decision.revocation_ref,
            "readiness_artifact_ref": decision.readiness_artifact_ref,
            "backend_invocation_request_ref": decision.backend_invocation_request_ref,
            "adapter_invocation_request_ref": decision.adapter_invocation_request_ref,
            "evidence_chain_ref": decision.evidence_chain_ref,
            "artifact_verification_ref": decision.artifact_verification_ref,
            "human_confirmation_text": decision.human_confirmation_text,
            "schema_version": decision.schema_version,
        })
        if fresh != stored:
            denial_reasons.append(DENIED_STALE_ARTIFACT)

    # 25. Decision-request link
    checked.append("request_decision_link")
    if decision.approval_request_id != request.approval_request_id:
        denial_reasons.append("denied_request_decision_mismatch")

    verified = len(denial_reasons) == 0

    return ApprovalVerificationResult(
        verified=verified,
        denial_reasons=denial_reasons,
        checked_fields=checked,
        detail="All checks passed" if verified else f"Denied: {', '.join(denial_reasons)}",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Approval Revocation
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ApprovalRevocation:
    """Records revocation of a prior approval decision."""

    revocation_id: str = ""
    approval_decision_id: str = ""
    approval_request_id: str = ""
    revoked_by: str = ""
    revoked_at_utc: str = ""
    reason: str = ""
    phase_id: str = ""
    task_id: str = ""
    schema_version: str = SCHEMA_VERSION
    digest: str = ""

    def __post_init__(self) -> None:
        if not self.revocation_id:
            self.revocation_id = _new_uuid()
        if not self.revoked_at_utc:
            self.revoked_at_utc = _utc_now().isoformat()

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.revocation_id:
            issues.append("revocation_id is required")
        if not self.approval_decision_id:
            issues.append("approval_decision_id is required")
        if not self.revoked_by:
            issues.append("revoked_by is required")
        if not self.reason:
            issues.append("reason is required")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "revocation_id": self.revocation_id,
            "approval_decision_id": self.approval_decision_id,
            "approval_request_id": self.approval_request_id,
            "revoked_by": self.revoked_by,
            "revoked_at_utc": self.revoked_at_utc,
            "reason": self.reason,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "digest": self.digest,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Approval Denial
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ApprovalDenial:
    """Records denial of an approval request."""

    denial_id: str = ""
    approval_request_id: str = ""
    denied_by: str = ""
    denied_at_utc: str = ""
    denial_reasons: list[str] = field(default_factory=list)
    phase_id: str = ""
    task_id: str = ""
    schema_version: str = SCHEMA_VERSION
    digest: str = ""

    def __post_init__(self) -> None:
        if not self.denial_id:
            self.denial_id = _new_uuid()
        if not self.denied_at_utc:
            self.denied_at_utc = _utc_now().isoformat()

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.denial_id:
            issues.append("denial_id is required")
        if not self.approval_request_id:
            issues.append("approval_request_id is required")
        if not self.denied_by:
            issues.append("denied_by is required")
        if not self.denial_reasons:
            issues.append("at least one denial_reason is required")
        for reason in self.denial_reasons:
            if reason not in VALID_DENIAL_REASONS:
                issues.append(f"invalid denial_reason: {reason!r}")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "denial_id": self.denial_id,
            "approval_request_id": self.approval_request_id,
            "denied_by": self.denied_by,
            "denied_at_utc": self.denied_at_utc,
            "denial_reasons": self.denial_reasons,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "digest": self.digest,
        }
