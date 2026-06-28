"""Simulation-only enforcement rollback evidence model.

Defines pure data-model schemas and validation helpers for rollback
evidence artifacts.  No real enforcement, no command execution, no
persistent database, no authorization state.

Schema version: 1.0 (simulation-only)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.0"

ROLLBACK_STATUS_CREATED = "created"
ROLLBACK_STATUS_RESTORED = "restored"
ROLLBACK_STATUS_EXPIRED = "expired"
ROLLBACK_STATUS_INVALID = "invalid"

_ALL_ROLLBACK_STATUSES: frozenset[str] = frozenset({
    ROLLBACK_STATUS_CREATED,
    ROLLBACK_STATUS_RESTORED,
    ROLLBACK_STATUS_EXPIRED,
    ROLLBACK_STATUS_INVALID,
})

# Required keys for a rollback evidence dict
_REQUIRED_KEYS: frozenset[str] = frozenset({
    "rollback_id", "status", "schema_version", "created_at",
})


# ---------------------------------------------------------------------------
# Pre-mutation snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PreMutationSnapshot:
    """A snapshot of file state before a governed mutation."""
    file_path: str
    content_hash: str
    size_bytes: int
    mode: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "file_path": self.file_path,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
        }
        if self.mode is not None:
            result["mode"] = self.mode
        return result


# ---------------------------------------------------------------------------
# Rollback evidence
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RollbackPreconditions:
    """Preconditions that must be satisfied for a safe rollback."""
    working_tree_clean: bool = False
    health_check_passed: bool = False
    no_active_enforcement: bool = True
    operator_confirmation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "working_tree_clean": self.working_tree_clean,
            "health_check_passed": self.health_check_passed,
            "no_active_enforcement": self.no_active_enforcement,
            "operator_confirmation": self.operator_confirmation,
        }

    def all_satisfied(self) -> bool:
        """Return True if all preconditions are met."""
        return all((
            self.working_tree_clean,
            self.health_check_passed,
            self.no_active_enforcement,
            self.operator_confirmation,
        ))


@dataclass(frozen=True)
class RollbackLimitations:
    """Documented limitations of rollback capability."""
    cannot_undo_network_operations: bool = True
    cannot_undo_external_side_effects: bool = True
    cannot_restore_deleted_repos: bool = True
    cannot_recover_overwritten_secrets: bool = True
    limited_to_tracked_files: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "cannot_undo_network_operations": self.cannot_undo_network_operations,
            "cannot_undo_external_side_effects": self.cannot_undo_external_side_effects,
            "cannot_restore_deleted_repos": self.cannot_restore_deleted_repos,
            "cannot_recover_overwritten_secrets": self.cannot_recover_overwritten_secrets,
            "limited_to_tracked_files": self.limited_to_tracked_files,
        }


@dataclass(frozen=True)
class RollbackEvidence:
    """Rollback evidence artifact.

    Simulation-only: captures what *would* be needed for rollback
    without actually performing any file mutations, enforcement actions,
    or command execution.

    All enforcement-related flags remain simulation-only.
    """

    rollback_id: str
    status: str
    schema_version: str = SCHEMA_VERSION
    created_at: str = ""
    operation: str = "simulation"
    action_description: str = ""
    preconditions: RollbackPreconditions | None = None
    limitations: RollbackLimitations | None = None
    snapshots: tuple[PreMutationSnapshot, ...] = ()
    audit_event_ids: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()

    # Invariant flags
    no_execution: bool = True
    no_enforcement: bool = True

    # Recovery metadata
    recovery_steps: tuple[str, ...] = ()
    failure_modes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dict."""
        result: dict[str, Any] = {
            "rollback_id": self.rollback_id,
            "status": self.status,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "operation": self.operation,
            "action_description": self.action_description,
            "no_execution": self.no_execution,
            "no_enforcement": self.no_enforcement,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "audit_event_ids": list(self.audit_event_ids),
            "evidence_references": list(self.evidence_references),
            "recovery_steps": list(self.recovery_steps),
            "failure_modes": list(self.failure_modes),
        }
        if getattr(self, "preconditions", None) is not None:
            result["preconditions"] = self.preconditions.to_dict()
        if getattr(self, "limitations", None) is not None:
            result["limitations"] = self.limitations.to_dict()
        return result


# ---------------------------------------------------------------------------
# Constructors
# ---------------------------------------------------------------------------


def _make_rollback_id() -> str:
    """Generate a deterministic-style rollback ID."""
    return f"rb-{uuid.uuid4().hex[:12]}"


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def make_rollback_evidence(
    *,
    rollback_id: str | None = None,
    status: str = ROLLBACK_STATUS_CREATED,
    operation: str = "simulation",
    action_description: str = "",
    snapshots: tuple[PreMutationSnapshot, ...] = (),
    audit_event_ids: tuple[str, ...] = (),
    evidence_references: tuple[str, ...] = (),
    preconditions: RollbackPreconditions | None = None,
    limitations: RollbackLimitations | None = None,
    recovery_steps: tuple[str, ...] = (),
    failure_modes: tuple[str, ...] = (),
) -> RollbackEvidence:
    """Construct a validated rollback evidence artifact.

    Always sets no_execution=True and no_enforcement=True.
    Raises ValueError for invalid status.
    """
    if status not in _ALL_ROLLBACK_STATUSES:
        raise ValueError(
            f"Invalid status: {status!r}. "
            f"Must be one of: {', '.join(sorted(_ALL_ROLLBACK_STATUSES))}"
        )

    return RollbackEvidence(
        rollback_id=rollback_id or _make_rollback_id(),
        status=status,
        schema_version=SCHEMA_VERSION,
        created_at=_utc_now_iso(),
        operation=operation,
        action_description=action_description,
        preconditions=preconditions or RollbackPreconditions(),
        limitations=limitations or RollbackLimitations(),
        snapshots=snapshots,
        audit_event_ids=audit_event_ids,
        evidence_references=evidence_references,
        recovery_steps=recovery_steps,
        failure_modes=failure_modes,
        no_execution=True,
        no_enforcement=True,
    )


def make_rollback_for_blocked_command(
    *,
    command_description: str = "",
    hard_block_reason: str = "",
    audit_event_id: str | None = None,
    snapshots: tuple[PreMutationSnapshot, ...] = (),
) -> RollbackEvidence:
    """Construct rollback evidence for a command that was hard-blocked.

    Since the command was blocked, the snapshots list is typically empty
    (no mutation occurred).  The rollback evidence exists to document
    that nothing needs to be undone.
    """
    audit_ids = (audit_event_id,) if audit_event_id else ()
    return make_rollback_evidence(
        status=ROLLBACK_STATUS_CREATED,
        operation="blocked_command_rollback",
        action_description=(
            f"Rollback evidence for blocked command: {command_description}. "
            f"Hard block reason: {hard_block_reason}. "
            "No mutation occurred; nothing to undo."
        ),
        snapshots=snapshots,
        audit_event_ids=audit_ids,
        preconditions=RollbackPreconditions(
            working_tree_clean=True,
            health_check_passed=True,
            no_active_enforcement=True,
            operator_confirmation=True,
        ),
        recovery_steps=(
            "1. Confirm no files were mutated by the blocked command.",
            "2. Verify git status is clean.",
            "3. No rollback action required.",
        ),
        failure_modes=(
            "F1: Operator bypassed the block — manual inspection required.",
        ),
    )


def make_rollback_for_mutation(
    *,
    action_description: str = "",
    snapshots: tuple[PreMutationSnapshot, ...] = (),
    audit_event_ids: tuple[str, ...] = (),
) -> RollbackEvidence:
    """Construct rollback evidence for a governed mutation.

    Includes pre-mutation snapshots so that the mutation can be undone
    if needed.  The preconditions are unsatisfied by default because
    rollback is a deliberate operator action.
    """
    return make_rollback_evidence(
        status=ROLLBACK_STATUS_CREATED,
        operation="governed_mutation",
        action_description=action_description,
        snapshots=snapshots,
        audit_event_ids=audit_event_ids,
        preconditions=RollbackPreconditions(
            working_tree_clean=False,  # rollback itself is a mutation
            health_check_passed=False,
            no_active_enforcement=True,
            operator_confirmation=False,
        ),
        recovery_steps=(
            "1. Review the rollback evidence and preconditions.",
            "2. Confirm operator intent to rollback.",
            "3. Restore files from pre-mutation snapshots.",
            "4. Verify git status after restoration.",
            "5. Run pcae check and pcae health.",
        ),
        failure_modes=(
            "F1: Snapshot hash mismatch — file changed since snapshot.",
            "F2: Working tree not clean — cannot safely rollback.",
            "F3: Rollback would overwrite uncommitted changes.",
        ),
    )


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def is_valid_rollback_status(status: str) -> bool:
    """Check whether *status* is a recognised rollback status."""
    return status in _ALL_ROLLBACK_STATUSES


def validate_rollback_evidence(rb: RollbackEvidence) -> list[str]:
    """Return a list of validation issues (empty = valid)."""
    issues: list[str] = []

    if not rb.rollback_id:
        issues.append("rollback_id is empty")
    if rb.status not in _ALL_ROLLBACK_STATUSES:
        issues.append(f"invalid status: {rb.status!r}")
    if rb.schema_version != SCHEMA_VERSION:
        issues.append(
            f"schema_version {rb.schema_version!r} != expected {SCHEMA_VERSION!r}"
        )
    if not rb.created_at:
        issues.append("created_at is empty")

    # Invariant flags
    if not rb.no_execution:
        issues.append("no_execution must be True (simulation-only invariant)")
    if not rb.no_enforcement:
        issues.append("no_enforcement must be True (simulation-only invariant)")

    # Preconditions: all_must_be_false by default (rollback is deliberate)
    if rb.preconditions is not None:
        pc = rb.preconditions
        if pc.no_active_enforcement is False:
            # Actually this is fine — no_active_enforcement can be True or False
            pass

    # Snapshots should have required fields
    for i, snap in enumerate(rb.snapshots):
        if not snap.file_path:
            issues.append(f"snapshots[{i}].file_path is empty")
        if not snap.content_hash:
            issues.append(f"snapshots[{i}].content_hash is empty")
        if snap.size_bytes < 0:
            issues.append(f"snapshots[{i}].size_bytes is negative")

    return issues


def validate_rollback_evidence_dict(rb_dict: dict[str, Any]) -> list[str]:
    """Validate a serialized rollback evidence dict."""
    issues: list[str] = []

    for key in _REQUIRED_KEYS:
        if key not in rb_dict:
            issues.append(f"missing required key: {key!r}")

    status = rb_dict.get("status")
    if status is not None and status not in _ALL_ROLLBACK_STATUSES:
        issues.append(f"invalid status: {status!r}")

    schema_version = rb_dict.get("schema_version")
    if schema_version is not None and schema_version != SCHEMA_VERSION:
        issues.append(
            f"schema_version {schema_version!r} != expected {SCHEMA_VERSION!r}"
        )

    no_exec = rb_dict.get("no_execution")
    if no_exec is not None and not no_exec:
        issues.append("no_execution must be True")

    no_enf = rb_dict.get("no_enforcement")
    if no_enf is not None and not no_enf:
        issues.append("no_enforcement must be True")

    # Validate preconditions in dict form
    pc = rb_dict.get("preconditions")
    if isinstance(pc, dict):
        # Precondition keys check
        valid_pc_keys = {
            "working_tree_clean", "health_check_passed",
            "no_active_enforcement", "operator_confirmation",
        }
        for key in pc:
            if key not in valid_pc_keys:
                issues.append(f"unknown precondition key: {key!r}")

    return issues
