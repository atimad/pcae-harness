"""Simulation-only enforcement approval and accepted-risk policy model.

Defines pure data-model schemas and policy evaluation helpers for
operator approval and accepted-risk decisions.  No real authorization,
no persistent approval store, no enforcement.

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

# Risk levels from Phase 89I §10
RISK_LEVEL_LOW = "low"
RISK_LEVEL_MEDIUM = "medium"
RISK_LEVEL_HIGH = "high"
RISK_LEVEL_CRITICAL = "critical"

_ALL_RISK_LEVELS: frozenset[str] = frozenset({
    RISK_LEVEL_LOW,
    RISK_LEVEL_MEDIUM,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_CRITICAL,
})

# Approval scopes from Phase 89I §7
SCOPE_SINGLE_COMMAND = "single_command"
SCOPE_COMMAND_CATEGORY = "command_category"
SCOPE_FILE_SET = "file_set"
SCOPE_TASK_DURATION = "task_duration"
SCOPE_SESSION = "session"

_ALL_SCOPES: frozenset[str] = frozenset({
    SCOPE_SINGLE_COMMAND,
    SCOPE_COMMAND_CATEGORY,
    SCOPE_FILE_SET,
    SCOPE_TASK_DURATION,
    SCOPE_SESSION,
})

# Default expiry durations per scope (Phase 89I §8)
DEFAULT_EXPIRY_MINUTES: dict[str, int] = {
    SCOPE_SINGLE_COMMAND: 5,
    SCOPE_COMMAND_CATEGORY: 30,
    SCOPE_FILE_SET: 60,
    SCOPE_TASK_DURATION: 480,  # 8 hours
    SCOPE_SESSION: 1440,  # 24 hours
}

MAX_EXPIRY_MINUTES: dict[str, int] = {
    SCOPE_SINGLE_COMMAND: 60,
    SCOPE_COMMAND_CATEGORY: 240,
    SCOPE_FILE_SET: 480,
    SCOPE_TASK_DURATION: 540,  # 9 hours (task end + 1)
    SCOPE_SESSION: 2880,  # 48 hours
}

# Policy classification outcomes
CLASSIFICATION_APPROVAL_NOT_RELEVANT = "approval_not_relevant"
CLASSIFICATION_APPROVAL_REQUIRED = "approval_required"
CLASSIFICATION_APPROVAL_PRESENT_BUT_NOT_AUTHORIZATION = "approval_present_but_not_authorization"
CLASSIFICATION_ACCEPTED_RISK_NOT_RELEVANT = "accepted_risk_not_relevant"
CLASSIFICATION_ACCEPTED_RISK_RELEVANT_BUT_NOT_OVERRIDE = "accepted_risk_relevant_but_not_override"
CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE = "hard_block_non_overridable"

_ALL_CLASSIFICATIONS: frozenset[str] = frozenset({
    CLASSIFICATION_APPROVAL_NOT_RELEVANT,
    CLASSIFICATION_APPROVAL_REQUIRED,
    CLASSIFICATION_APPROVAL_PRESENT_BUT_NOT_AUTHORIZATION,
    CLASSIFICATION_ACCEPTED_RISK_NOT_RELEVANT,
    CLASSIFICATION_ACCEPTED_RISK_RELEVANT_BUT_NOT_OVERRIDE,
    CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE,
})

# Required keys for an approval record dict
_APPROVAL_REQUIRED_KEYS: frozenset[str] = frozenset({
    "approval_id", "approved_by", "approved_action",
    "scope", "granted_at", "expires_at", "revocable",
})

# Required keys for an accepted-risk record dict
_RISK_REQUIRED_KEYS: frozenset[str] = frozenset({
    "risk_id", "accepted_by", "risk_level", "risk_description",
    "accepted_at",
})


# ---------------------------------------------------------------------------
# Approval record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ApprovalRecord:
    """Operator approval record (Phase 89I §9).

    Approval is not authorization.  It records that a human reviewed
    and consented to a specific action.  It does not mean PCAE
    authorizes execution.

    All authorization flags remain False.
    """

    approval_id: str
    approved_by: str
    approved_action: str
    approved_command_hash: str
    scope: str = SCOPE_SINGLE_COMMAND
    granted_at: str = ""
    expires_at: str = ""
    revocable: bool = True
    revoked_at: str | None = None
    decision_context: str = ""
    hard_block_present: bool = False

    # Invariant flags
    is_authorization: bool = False
    no_enforcement: bool = True

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "approval_id": self.approval_id,
            "approved_by": self.approved_by,
            "approved_action": self.approved_action,
            "approved_command_hash": self.approved_command_hash,
            "scope": self.scope,
            "granted_at": self.granted_at,
            "expires_at": self.expires_at,
            "revocable": self.revocable,
            "revoked_at": self.revoked_at,
            "decision_context": self.decision_context,
            "hard_block_present": self.hard_block_present,
            "is_authorization": self.is_authorization,
            "no_enforcement": self.no_enforcement,
        }
        return result

    def is_expired(self, at_time: str | None = None) -> bool:
        """Check whether the approval has expired."""
        if self.revoked_at is not None:
            return True
        if not self.expires_at:
            return True
        compare = at_time or _utc_now_iso()
        return self.expires_at < compare

    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_valid(self) -> bool:
        """Approval is valid if not expired and not revoked."""
        return not self.is_expired() and not self.is_revoked()


# ---------------------------------------------------------------------------
# Accepted-risk record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AcceptedRiskRecord:
    """Accepted-risk record (Phase 89I §10–11).

    Records that an operator has acknowledged and accepted a specific
    risk.  Accepted risk never overrides hard blocks (88V §16).

    All authorization and override flags remain False.
    """

    risk_id: str
    accepted_by: str
    risk_level: str
    risk_description: str
    accepted_at: str = ""
    expires_at: str = ""
    scope: tuple[str, ...] = ()
    revoked_at: str | None = None

    # Invariants
    hard_block_override: bool = False
    hard_block_note: str = "Accepted risk never overrides hard blocks (88V §16)"
    is_authorization: bool = False
    no_enforcement: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "accepted_by": self.accepted_by,
            "risk_level": self.risk_level,
            "risk_description": self.risk_description,
            "accepted_at": self.accepted_at,
            "expires_at": self.expires_at,
            "scope": list(self.scope),
            "revoked_at": self.revoked_at,
            "hard_block_override": self.hard_block_override,
            "hard_block_note": self.hard_block_note,
            "is_authorization": self.is_authorization,
            "no_enforcement": self.no_enforcement,
        }

    def is_expired(self, at_time: str | None = None) -> bool:
        if self.revoked_at is not None:
            return True
        if not self.expires_at:
            return True
        compare = at_time or _utc_now_iso()
        return self.expires_at < compare

    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_valid(self) -> bool:
        return not self.is_expired() and not self.is_revoked()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Constructors
# ---------------------------------------------------------------------------


def make_approval_record(
    *,
    approved_by: str,
    approved_action: str,
    approved_command_hash: str,
    scope: str = SCOPE_SINGLE_COMMAND,
    approval_id: str | None = None,
    granted_at: str | None = None,
    expires_at: str | None = None,
    decision_context: str = "",
    hard_block_present: bool = False,
) -> ApprovalRecord:
    """Construct a validated approval record.

    Always sets is_authorization=False and no_enforcement=True.
    Raises ValueError for invalid scope or hard_block_present conflict.
    """
    if scope not in _ALL_SCOPES:
        raise ValueError(
            f"Invalid scope: {scope!r}. Must be one of: "
            f"{', '.join(sorted(_ALL_SCOPES))}"
        )

    if hard_block_present:
        # Hard block is present — approval must not be valid
        # (Phase 89I §12: approval never overrides hard blocks)
        pass  # Record it but mark is_authorization=False

    now = _utc_now_iso()
    return ApprovalRecord(
        approval_id=approval_id or _make_id("appr"),
        approved_by=approved_by,
        approved_action=approved_action,
        approved_command_hash=approved_command_hash,
        scope=scope,
        granted_at=granted_at or now,
        expires_at=expires_at or "",
        revocable=True,  # Phase 89I P4: always revocable
        decision_context=decision_context,
        hard_block_present=hard_block_present,
        is_authorization=False,  # P1: approval is not authorization
        no_enforcement=True,
    )


def make_accepted_risk_record(
    *,
    accepted_by: str,
    risk_level: str,
    risk_description: str,
    risk_id: str | None = None,
    accepted_at: str | None = None,
    expires_at: str | None = None,
    scope: tuple[str, ...] = (),
) -> AcceptedRiskRecord:
    """Construct a validated accepted-risk record.

    Always sets hard_block_override=False and is_authorization=False.
    Raises ValueError for invalid risk_level.
    """
    if risk_level not in _ALL_RISK_LEVELS:
        raise ValueError(
            f"Invalid risk_level: {risk_level!r}. Must be one of: "
            f"{', '.join(sorted(_ALL_RISK_LEVELS))}"
        )

    return AcceptedRiskRecord(
        risk_id=risk_id or _make_id("risk"),
        accepted_by=accepted_by,
        risk_level=risk_level,
        risk_description=risk_description,
        accepted_at=accepted_at or _utc_now_iso(),
        expires_at=expires_at or "",
        scope=scope,
        hard_block_override=False,
        is_authorization=False,
        no_enforcement=True,
    )


def revoke_approval(
    record: ApprovalRecord,
    revoked_at: str | None = None,
) -> ApprovalRecord:
    """Return a new ApprovalRecord with revoked_at set.

    Does not mutate the original (frozen dataclass).
    """
    ts = revoked_at or _utc_now_iso()
    return ApprovalRecord(
        approval_id=record.approval_id,
        approved_by=record.approved_by,
        approved_action=record.approved_action,
        approved_command_hash=record.approved_command_hash,
        scope=record.scope,
        granted_at=record.granted_at,
        expires_at=record.expires_at,
        revocable=record.revocable,
        revoked_at=ts,
        decision_context=record.decision_context,
        hard_block_present=record.hard_block_present,
        is_authorization=False,
        no_enforcement=True,
    )


def revoke_accepted_risk(
    record: AcceptedRiskRecord,
    revoked_at: str | None = None,
) -> AcceptedRiskRecord:
    """Return a new AcceptedRiskRecord with revoked_at set."""
    ts = revoked_at or _utc_now_iso()
    return AcceptedRiskRecord(
        risk_id=record.risk_id,
        accepted_by=record.accepted_by,
        risk_level=record.risk_level,
        risk_description=record.risk_description,
        accepted_at=record.accepted_at,
        expires_at=record.expires_at,
        scope=record.scope,
        revoked_at=ts,
        hard_block_override=False,
        is_authorization=False,
        no_enforcement=True,
    )


# ---------------------------------------------------------------------------
# Policy classification helpers
# ---------------------------------------------------------------------------


def classify_hard_block(
    hard_block_present: bool,
) -> str:
    """Classify whether a hard block exists and is non-overridable.

    Always returns CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE if a hard
    block is present — no approval or accepted risk can override it.
    """
    if hard_block_present:
        return CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE
    return CLASSIFICATION_APPROVAL_NOT_RELEVANT


def classify_approval(
    approval: ApprovalRecord | None,
    hard_block_present: bool = False,
) -> str:
    """Classify the approval state for a given decision context.

    Returns one of:
    - hard_block_non_overridable — hard block present, approval irrelevant
    - approval_required — no approval present, action requires human review
    - approval_present_but_not_authorization — approval exists but is not auth
    - approval_not_relevant — action does not require approval
    """
    # Check explicit parameter first, then record's own flag
    if hard_block_present or (approval is not None and approval.hard_block_present):
        return CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE

    if approval is None:
        return CLASSIFICATION_APPROVAL_REQUIRED

    # Approval exists, but it is never authorization
    if not approval.is_valid():
        return CLASSIFICATION_APPROVAL_REQUIRED  # expired/revoked

    return CLASSIFICATION_APPROVAL_PRESENT_BUT_NOT_AUTHORIZATION


def classify_accepted_risk(
    accepted_risk: AcceptedRiskRecord | None,
    hard_block_present: bool = False,
) -> str:
    """Classify the accepted-risk state.

    Accepted risk never overrides hard blocks.  Even when relevant,
    it does not grant authorization.
    """
    if hard_block_present:
        return CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE

    if accepted_risk is None:
        return CLASSIFICATION_ACCEPTED_RISK_NOT_RELEVANT

    if accepted_risk.hard_block_override:
        # Should never be True (constructor enforces False)
        return CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE

    return CLASSIFICATION_ACCEPTED_RISK_RELEVANT_BUT_NOT_OVERRIDE


def is_valid_risk_level(level: str) -> bool:
    return level in _ALL_RISK_LEVELS


def is_valid_scope(scope: str) -> bool:
    return scope in _ALL_SCOPES


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_approval_record(record: ApprovalRecord) -> list[str]:
    """Return a list of validation issues (empty = valid)."""
    issues: list[str] = []

    if not record.approval_id:
        issues.append("approval_id is empty")
    if not record.approved_by:
        issues.append("approved_by is empty")
    if not record.approved_action:
        issues.append("approved_action is empty")
    if not record.approved_command_hash:
        issues.append("approved_command_hash is empty")
    if record.scope not in _ALL_SCOPES:
        issues.append(f"invalid scope: {record.scope!r}")
    if not record.granted_at:
        issues.append("granted_at is empty")

    # Invariants
    if record.is_authorization:
        issues.append("is_authorization must be False (approval is not authorization)")
    if not record.no_enforcement:
        issues.append("no_enforcement must be True")
    if not record.revocable:
        issues.append("revocable must be True (Phase 89I P4)")

    # Hard-block check
    if record.hard_block_present:
        issues.append(
            "hard_block_present is True — approval cannot be valid "
            "when a hard block exists (Phase 89I §12)"
        )

    return issues


def validate_accepted_risk_record(record: AcceptedRiskRecord) -> list[str]:
    """Return a list of validation issues (empty = valid)."""
    issues: list[str] = []

    if not record.risk_id:
        issues.append("risk_id is empty")
    if not record.accepted_by:
        issues.append("accepted_by is empty")
    if record.risk_level not in _ALL_RISK_LEVELS:
        issues.append(f"invalid risk_level: {record.risk_level!r}")
    if not record.risk_description:
        issues.append("risk_description is empty")
    if not record.accepted_at:
        issues.append("accepted_at is empty")

    # Invariants
    if record.hard_block_override:
        issues.append(
            "hard_block_override must be False "
            "(accepted risk never overrides hard blocks)"
        )
    if record.is_authorization:
        issues.append(
            "is_authorization must be False "
            "(accepted risk is not authorization)"
        )
    if not record.no_enforcement:
        issues.append("no_enforcement must be True")

    return issues


def validate_approval_record_dict(d: dict[str, Any]) -> list[str]:
    """Validate a serialized approval record dict."""
    issues: list[str] = []

    for key in _APPROVAL_REQUIRED_KEYS:
        if key not in d:
            issues.append(f"missing required key: {key!r}")

    scope = d.get("scope")
    if scope is not None and scope not in _ALL_SCOPES:
        issues.append(f"invalid scope: {scope!r}")

    is_auth = d.get("is_authorization")
    if is_auth is not None and is_auth:
        issues.append("is_authorization must be False")

    no_enf = d.get("no_enforcement")
    if no_enf is not None and not no_enf:
        issues.append("no_enforcement must be True")

    revocable = d.get("revocable")
    if revocable is not None and not revocable:
        issues.append("revocable must be True")

    hard_block = d.get("hard_block_present")
    if hard_block:
        issues.append("hard_block_present is True — approval invalid with hard block")

    return issues


def validate_accepted_risk_record_dict(d: dict[str, Any]) -> list[str]:
    """Validate a serialized accepted-risk record dict."""
    issues: list[str] = []

    for key in _RISK_REQUIRED_KEYS:
        if key not in d:
            issues.append(f"missing required key: {key!r}")

    risk_level = d.get("risk_level")
    if risk_level is not None and risk_level not in _ALL_RISK_LEVELS:
        issues.append(f"invalid risk_level: {risk_level!r}")

    hb_override = d.get("hard_block_override")
    if hb_override is not None and hb_override:
        issues.append("hard_block_override must be False")

    is_auth = d.get("is_authorization")
    if is_auth is not None and is_auth:
        issues.append("is_authorization must be False")

    no_enf = d.get("no_enforcement")
    if no_enf is not None and not no_enf:
        issues.append("no_enforcement must be True")

    return issues
