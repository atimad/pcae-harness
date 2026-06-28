"""Simulation-only enforcement audit event model.

Defines pure data-model schemas and validation helpers for enforcement
audit events.  No real enforcement, no command execution, no persistent
database, no authorization state.

Schema version: 1.0 (simulation-only)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.0"

# All 16 event types from Phase 89H §6
EVENT_TYPE_ENFORCEMENT_DECISION = "enforcement.decision"
EVENT_TYPE_ENFORCEMENT_BLOCKED = "enforcement.blocked"
EVENT_TYPE_ENFORCEMENT_ALLOWED = "enforcement.allowed"
EVENT_TYPE_ENFORCEMENT_GATED_REVIEW = "enforcement.gated_review"
EVENT_TYPE_ENFORCEMENT_DENIED = "enforcement.denied"
EVENT_TYPE_ENFORCEMENT_BYPASS_DETECTED = "enforcement.bypass_detected"
EVENT_TYPE_ENFORCEMENT_ERROR = "enforcement.error"
EVENT_TYPE_APPROVAL_GRANTED = "approval.granted"
EVENT_TYPE_APPROVAL_EXPIRED = "approval.expired"
EVENT_TYPE_APPROVAL_REVOKED = "approval.revoked"
EVENT_TYPE_RISK_ACCEPTED = "risk.accepted"
EVENT_TYPE_RISK_EXPIRED = "risk.expired"
EVENT_TYPE_ROLLBACK_CREATED = "rollback.created"
EVENT_TYPE_ROLLBACK_RESTORED = "rollback.restored"
EVENT_TYPE_ENFORCEMENT_DISABLED = "enforcement.disabled"
EVENT_TYPE_ENFORCEMENT_ENABLED = "enforcement.enabled"

_ALL_EVENT_TYPES: frozenset[str] = frozenset({
    EVENT_TYPE_ENFORCEMENT_DECISION,
    EVENT_TYPE_ENFORCEMENT_BLOCKED,
    EVENT_TYPE_ENFORCEMENT_ALLOWED,
    EVENT_TYPE_ENFORCEMENT_GATED_REVIEW,
    EVENT_TYPE_ENFORCEMENT_DENIED,
    EVENT_TYPE_ENFORCEMENT_BYPASS_DETECTED,
    EVENT_TYPE_ENFORCEMENT_ERROR,
    EVENT_TYPE_APPROVAL_GRANTED,
    EVENT_TYPE_APPROVAL_EXPIRED,
    EVENT_TYPE_APPROVAL_REVOKED,
    EVENT_TYPE_RISK_ACCEPTED,
    EVENT_TYPE_RISK_EXPIRED,
    EVENT_TYPE_ROLLBACK_CREATED,
    EVENT_TYPE_ROLLBACK_RESTORED,
    EVENT_TYPE_ENFORCEMENT_DISABLED,
    EVENT_TYPE_ENFORCEMENT_ENABLED,
})

# Required top-level keys in every audit event dict
_REQUIRED_KEYS: frozenset[str] = frozenset({
    "event_id", "event_type", "timestamp", "schema_version",
})

# ---------------------------------------------------------------------------
# Audit event dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditOperator:
    """Operator identity for an audit event."""
    user: str
    agent_id: str | None = None
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "user": self.user,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
        }


@dataclass(frozen=True)
class AuditCommand:
    """Command information, always with redacted text."""
    text_hash: str
    text_redacted: str
    category: str = "unknown"
    action: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "text_hash": self.text_hash,
            "text_redacted": self.text_redacted,
            "category": self.category,
            "action": self.action,
        }


@dataclass(frozen=True)
class AuditDecision:
    """The enforcement decision that was made."""
    broker: str = "simulation"
    shell_gate: str = "simulation"
    simulation: str = "simulation"
    severity: str = "info"
    hard_block: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "broker": self.broker,
            "shell_gate": self.shell_gate,
            "simulation": self.simulation,
            "severity": self.severity,
            "hard_block": self.hard_block,
        }


@dataclass(frozen=True)
class AuditOutcome:
    """What happened as a result of the decision."""
    action: str
    enforced: bool
    governed_alternative: str | None = None
    operator_bypassed: bool = False

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "action": self.action,
            "enforced": self.enforced,
            "operator_bypassed": self.operator_bypassed,
        }
        if self.governed_alternative is not None:
            result["governed_alternative"] = self.governed_alternative
        return result


@dataclass(frozen=True)
class AuditRepository:
    """Repository context for the event."""
    root: str
    commit: str | None = None
    branch: str | None = None
    task_contract: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "commit": self.commit,
            "branch": self.branch,
            "task_contract": self.task_contract,
        }


@dataclass(frozen=True)
class AuditEvidence:
    """Evidence sources that informed the decision."""
    health_passed: bool = False
    check_passed: bool = False
    sources: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "health_passed": self.health_passed,
            "check_passed": self.check_passed,
            "sources": list(self.sources),
        }


@dataclass(frozen=True)
class AuditIntegrity:
    """Integrity metadata for tamper-evidence."""
    schema_version: str = SCHEMA_VERSION
    checksum: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "checksum": self.checksum,
        }


# ---------------------------------------------------------------------------
# Hard-block event sub-schema
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditHardBlock:
    """Non-overridable hard-block detail (88V §16 permanent invariant)."""
    reason: str
    source: str
    overridable: bool = False
    overridden_by: str | None = None
    overridden: bool = False
    permanent: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason": self.reason,
            "source": self.source,
            "overridable": self.overridable,
            "overridden_by": self.overridden_by,
            "overridden": self.overridden,
            "permanent": self.permanent,
        }


# ---------------------------------------------------------------------------
# Approval sub-schema
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditApproval:
    """Approval detail for approval.* event types."""
    approved_by: str
    approved_action: str
    approved_command_hash: str
    scope: tuple[str, ...] = ()
    expires_at: str | None = None
    revocable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved_by": self.approved_by,
            "approved_action": self.approved_action,
            "approved_command_hash": self.approved_command_hash,
            "scope": list(self.scope),
            "expires_at": self.expires_at,
            "revocable": self.revocable,
        }


# ---------------------------------------------------------------------------
# Accepted-risk sub-schema
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditRisk:
    """Accepted-risk detail for risk.* event types."""
    accepted_by: str
    risk_level: str
    risk_description: str
    scope: tuple[str, ...] = ()
    expires_at: str | None = None
    hard_block_override: bool = False
    hard_block_note: str = "Accepted risk never overrides hard blocks (88V §16)"

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted_by": self.accepted_by,
            "risk_level": self.risk_level,
            "risk_description": self.risk_description,
            "scope": list(self.scope),
            "expires_at": self.expires_at,
            "hard_block_override": self.hard_block_override,
            "hard_block_note": self.hard_block_note,
        }


# ---------------------------------------------------------------------------
# Decline context for decision events
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditDecisionContext:
    """Decision context linking original decision to approval/risk event."""
    original_decision: str = "unknown"
    hard_block_present: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_decision": self.original_decision,
            "hard_block_present": self.hard_block_present,
        }


# ---------------------------------------------------------------------------
# Master AuditEvent
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditEvent:
    """Complete enforcement audit event.

    Simulation-only: no enforcement, no command execution, no persistence.
    All enforcement-related flags remain simulation-only.
    """

    event_id: str
    event_type: str
    timestamp: str
    schema_version: str = SCHEMA_VERSION
    operator: AuditOperator | None = None
    command: AuditCommand | None = None
    decision: AuditDecision | None = None
    outcome: AuditOutcome | None = None
    repository: AuditRepository | None = None
    evidence: AuditEvidence | None = None
    integrity: AuditIntegrity | None = None
    hard_block: AuditHardBlock | None = None
    approval: AuditApproval | None = None
    risk: AuditRisk | None = None
    decision_context: AuditDecisionContext | None = None

    # Invariant flags — always simulation-only
    no_execution: bool = True
    no_enforcement: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dict."""
        result: dict[str, Any] = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "schema_version": self.schema_version,
            "no_execution": self.no_execution,
            "no_enforcement": self.no_enforcement,
        }
        if self.operator is not None:
            result["operator"] = self.operator.to_dict()
        if self.command is not None:
            result["command"] = self.command.to_dict()
        if self.decision is not None:
            result["decision"] = self.decision.to_dict()
        if self.outcome is not None:
            result["outcome"] = self.outcome.to_dict()
        if self.repository is not None:
            result["repository"] = self.repository.to_dict()
        if self.evidence is not None:
            result["evidence"] = self.evidence.to_dict()
        if self.integrity is not None:
            result["integrity"] = self.integrity.to_dict()
        if self.hard_block is not None:
            result["hard_block"] = self.hard_block.to_dict()
        if self.approval is not None:
            result["approval"] = self.approval.to_dict()
        if self.risk is not None:
            result["risk"] = self.risk.to_dict()
        if self.decision_context is not None:
            result["decision_context"] = self.decision_context.to_dict()
        return result


# ---------------------------------------------------------------------------
# Constructors
# ---------------------------------------------------------------------------


def _make_event_id() -> str:
    """Generate a deterministic-style event ID."""
    return f"evt-{uuid.uuid4().hex[:12]}"


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def make_audit_event(
    event_type: str,
    *,
    event_id: str | None = None,
    timestamp: str | None = None,
    operator: AuditOperator | None = None,
    command: AuditCommand | None = None,
    decision: AuditDecision | None = None,
    outcome: AuditOutcome | None = None,
    repository: AuditRepository | None = None,
    evidence: AuditEvidence | None = None,
    integrity: AuditIntegrity | None = None,
    hard_block: AuditHardBlock | None = None,
    approval: AuditApproval | None = None,
    risk: AuditRisk | None = None,
    decision_context: AuditDecisionContext | None = None,
) -> AuditEvent:
    """Construct a validated audit event.

    Always sets no_execution=True and no_enforcement=True.
    Raises ValueError for invalid event types or missing required identity.
    """
    if event_type not in _ALL_EVENT_TYPES:
        raise ValueError(
            f"Invalid event_type: {event_type!r}. "
            f"Must be one of the 16 defined types."
        )

    return AuditEvent(
        event_id=event_id or _make_event_id(),
        event_type=event_type,
        timestamp=timestamp or _utc_now_iso(),
        schema_version=SCHEMA_VERSION,
        operator=operator,
        command=command,
        decision=decision,
        outcome=outcome,
        repository=repository,
        evidence=evidence,
        integrity=integrity or AuditIntegrity(),
        hard_block=hard_block,
        approval=approval,
        risk=risk,
        decision_context=decision_context,
        no_execution=True,
        no_enforcement=True,
    )


def make_enforcement_blocked_event(
    *,
    operator: AuditOperator | None = None,
    command: AuditCommand | None = None,
    hard_block: AuditHardBlock | None = None,
    decision: AuditDecision | None = None,
    repository: AuditRepository | None = None,
    evidence: AuditEvidence | None = None,
) -> AuditEvent:
    """Construct an enforcement.blocked event (simulation-only)."""
    return make_audit_event(
        event_type=EVENT_TYPE_ENFORCEMENT_BLOCKED,
        operator=operator,
        command=command,
        decision=decision or AuditDecision(
            broker="would_block",
            shell_gate="would_block",
            simulation="would_block",
            severity="critical",
            hard_block=True,
        ),
        outcome=AuditOutcome(action="blocked", enforced=False),
        repository=repository,
        evidence=evidence,
        hard_block=hard_block,
    )


def make_enforcement_allowed_event(
    *,
    operator: AuditOperator | None = None,
    command: AuditCommand | None = None,
    repository: AuditRepository | None = None,
    evidence: AuditEvidence | None = None,
) -> AuditEvent:
    """Construct an enforcement.allowed event (simulation-only)."""
    return make_audit_event(
        event_type=EVENT_TYPE_ENFORCEMENT_ALLOWED,
        operator=operator,
        command=command,
        decision=AuditDecision(
            broker="would_allow",
            shell_gate="would_allow",
            simulation="would_allow",
            severity="info",
            hard_block=False,
        ),
        outcome=AuditOutcome(action="allowed", enforced=False),
        repository=repository,
        evidence=evidence,
    )


def make_human_review_event(
    *,
    operator: AuditOperator | None = None,
    command: AuditCommand | None = None,
    repository: AuditRepository | None = None,
    evidence: AuditEvidence | None = None,
) -> AuditEvent:
    """Construct an enforcement.gated_review event (simulation-only)."""
    return make_audit_event(
        event_type=EVENT_TYPE_ENFORCEMENT_GATED_REVIEW,
        operator=operator,
        command=command,
        decision=AuditDecision(
            broker="would_require_human_review",
            shell_gate="would_require_human_review",
            simulation="would_require_human_review",
            severity="warning",
            hard_block=False,
        ),
        outcome=AuditOutcome(
            action="gated_review",
            enforced=False,
            governed_alternative="human review required",
        ),
        repository=repository,
        evidence=evidence,
    )


def make_hard_block_event(
    *,
    reason: str,
    source: str = "shell_gate",
    operator: AuditOperator | None = None,
    command: AuditCommand | None = None,
    repository: AuditRepository | None = None,
) -> AuditEvent:
    """Construct a hard-blocked enforcement event.

    Hard blocks are non-overridable (88V §16).  Even accepted risk
    and human approval cannot override them.
    """
    return make_audit_event(
        event_type=EVENT_TYPE_ENFORCEMENT_BLOCKED,
        operator=operator,
        command=command,
        decision=AuditDecision(
            broker="would_block",
            shell_gate="would_block",
            simulation="would_block",
            severity="critical",
            hard_block=True,
        ),
        outcome=AuditOutcome(action="blocked", enforced=False),
        repository=repository,
        hard_block=AuditHardBlock(
            reason=reason,
            source=source,
            overridable=False,
            overridden=False,
            permanent=True,
        ),
    )


def make_accepted_risk_event(
    *,
    accepted_by: str,
    risk_level: str,
    risk_description: str,
    original_decision: str = "would_require_human_review",
    scope: tuple[str, ...] = (),
    expires_at: str | None = None,
    hard_block_override: bool = False,
) -> AuditEvent:
    """Construct a risk.accepted event (simulation-only).

    hard_block_override is always False — accepted risk never overrides
    hard blocks.
    """
    return make_audit_event(
        event_type=EVENT_TYPE_RISK_ACCEPTED,
        risk=AuditRisk(
            accepted_by=accepted_by,
            risk_level=risk_level,
            risk_description=risk_description,
            scope=scope,
            expires_at=expires_at,
            hard_block_override=False,  # forced
        ),
        decision_context=AuditDecisionContext(
            original_decision=original_decision,
            hard_block_present=False,
        ),
    )


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def is_valid_event_type(event_type: str) -> bool:
    """Check whether *event_type* is one of the 16 defined types."""
    return event_type in _ALL_EVENT_TYPES


def validate_audit_event(event: AuditEvent) -> list[str]:
    """Return a list of validation issues (empty = valid)."""
    issues: list[str] = []

    if not event.event_id:
        issues.append("event_id is empty")
    if event.event_type not in _ALL_EVENT_TYPES:
        issues.append(f"unknown event_type: {event.event_type!r}")
    if not event.timestamp:
        issues.append("timestamp is empty")
    if event.schema_version != SCHEMA_VERSION:
        issues.append(
            f"schema_version {event.schema_version!r} != expected {SCHEMA_VERSION!r}"
        )

    # Invariant flags
    if not event.no_execution:
        issues.append("no_execution must be True (simulation-only invariant)")
    if not event.no_enforcement:
        issues.append("no_enforcement must be True (simulation-only invariant)")

    # Hard-block invariants
    if event.hard_block is not None:
        hb = event.hard_block
        if hb.overridable:
            issues.append("hard_block.overridable must be False")
        if hb.overridden:
            issues.append("hard_block.overridden must be False")
        if not hb.permanent:
            issues.append("hard_block.permanent must be True")

    # Accepted-risk invariants
    if event.risk is not None and event.risk.hard_block_override:
        issues.append(
            "risk.hard_block_override must be False "
            "(accepted risk never overrides hard blocks)"
        )

    # Approval is not authorization
    if event.approval is not None:
        if event.event_type == EVENT_TYPE_APPROVAL_GRANTED:
            if event.outcome is not None and event.outcome.enforced:
                issues.append(
                    "approval.granted must not have outcome.enforced=True "
                    "(approval is not authorization)"
                )

    return issues


def validate_audit_event_dict(event_dict: dict[str, Any]) -> list[str]:
    """Validate a serialized audit event dict."""
    issues: list[str] = []

    for key in _REQUIRED_KEYS:
        if key not in event_dict:
            issues.append(f"missing required key: {key!r}")

    event_type = event_dict.get("event_type")
    if event_type is not None and event_type not in _ALL_EVENT_TYPES:
        issues.append(f"unknown event_type: {event_type!r}")

    schema_version = event_dict.get("schema_version")
    if schema_version is not None and schema_version != SCHEMA_VERSION:
        issues.append(
            f"schema_version {schema_version!r} != expected {SCHEMA_VERSION!r}"
        )

    no_exec = event_dict.get("no_execution")
    if no_exec is not None and not no_exec:
        issues.append("no_execution must be True")

    no_enf = event_dict.get("no_enforcement")
    if no_enf is not None and not no_enf:
        issues.append("no_enforcement must be True")

    # Check hard_block invariants in dict form
    hb = event_dict.get("hard_block")
    if isinstance(hb, dict):
        if hb.get("overridable"):
            issues.append("hard_block.overridable must be False")
        if hb.get("overridden"):
            issues.append("hard_block.overridden must be False")
        if not hb.get("permanent", True):
            issues.append("hard_block.permanent must be True")

    # Check risk invariants
    risk = event_dict.get("risk")
    if isinstance(risk, dict):
        if risk.get("hard_block_override"):
            issues.append(
                "risk.hard_block_override must be False"
            )

    return issues
