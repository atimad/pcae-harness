"""
Permission Broker Foundation — Phase 108A.

The single policy decision point for future execution. The broker
evaluates proposed actions and returns a decision. It never executes
anything.

Isolation (by design, verified by tests reading this module's own source):
this module imports nothing from `pcae.core.shell_gate`,
`pcae.core.backend_invocations`, `pcae.core.notifications`, or any other
execution-adjacent module, and it uses no `subprocess`, no shell, no
network, and no file mutation. It knows nothing about *how* an action
would be carried out — only whether policy would permit it, if execution
existed.

Design principles (frozen by this phase):

1. Fail closed. If anything is unknown, unavailable, or unsupported, the
   decision is DENY.
2. Policy separated from execution. The broker never runs commands.
3. Single source of authorization. Future components must eventually ask
   this broker; no duplicated authorization logic.

Current implementation status: **execution unavailable**. Every decision
this broker returns — including ALLOW — carries
`implementation_status="execution_unavailable"`, because no execution
boundary (`COMP-002`) exists yet (see `NG-025`). ALLOW represents "policy
would allow this if execution existed," never an executable authorization.

See `docs/PHASE_108_PERMISSION_BROKER_FOUNDATION.md` and
`docs/V0_2_AUTONOMY_CONTRACT.md` (INV-001..010) and
`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (NG-001..025), which this
module maps decisions against.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════════════════
# Decision values
# ═══════════════════════════════════════════════════════════════════════════

DECISION_ALLOW = "ALLOW"
DECISION_DENY = "DENY"
DECISION_HUMAN_REVIEW = "HUMAN_REVIEW"

DECISION_VALUES: tuple[str, ...] = (DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW)

IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE = "execution_unavailable"

# ═══════════════════════════════════════════════════════════════════════════
# Component registry (COMP-001..010)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ComponentRegistryEntry:
    """A single canonical component ID entry."""

    component_id: str
    name: str
    implementation_status: str


COMPONENT_REGISTRY: tuple[ComponentRegistryEntry, ...] = (
    ComponentRegistryEntry("COMP-001", "Permission Broker", "foundation_implemented"),
    ComponentRegistryEntry("COMP-002", "Execution Boundary", "not_implemented"),
    ComponentRegistryEntry("COMP-003", "Human Approval Gate", "not_implemented"),
    ComponentRegistryEntry("COMP-004", "Shell Boundary", "not_implemented"),
    ComponentRegistryEntry("COMP-005", "Backend Boundary", "not_implemented"),
    ComponentRegistryEntry("COMP-006", "Adapter Boundary", "not_implemented"),
    ComponentRegistryEntry("COMP-007", "Audit Boundary", "not_implemented"),
    ComponentRegistryEntry("COMP-008", "Rollback Boundary", "not_implemented"),
    ComponentRegistryEntry("COMP-009", "Emergency Stop", "not_implemented"),
    ComponentRegistryEntry("COMP-010", "Execution Enablement", "not_implemented"),
)

COMPONENT_IDS: frozenset[str] = frozenset(e.component_id for e in COMPONENT_REGISTRY)
_COMPONENT_BY_ID: dict[str, ComponentRegistryEntry] = {
    e.component_id: e for e in COMPONENT_REGISTRY
}


def get_component(component_id: str) -> ComponentRegistryEntry | None:
    """Look up a component registry entry by COMP-xxx ID. None if unknown."""
    return _COMPONENT_BY_ID.get(component_id)


# ═══════════════════════════════════════════════════════════════════════════
# Known request vocabulary
# ═══════════════════════════════════════════════════════════════════════════

ACTION_READ = "read"
ACTION_SOURCE_MUTATION = "source_mutation"
ACTION_DOCS_MUTATION = "docs_mutation"
ACTION_TEST_MUTATION = "test_mutation"
ACTION_COMMIT = "commit"
ACTION_PUSH = "push"
ACTION_ROLLBACK = "rollback"
ACTION_SHELL_COMMAND = "shell_command"
ACTION_BACKEND_INVOCATION = "backend_invocation"
ACTION_ADAPTER_INVOCATION = "adapter_invocation"

KNOWN_ACTION_TYPES: frozenset[str] = frozenset({
    ACTION_READ,
    ACTION_SOURCE_MUTATION,
    ACTION_DOCS_MUTATION,
    ACTION_TEST_MUTATION,
    ACTION_COMMIT,
    ACTION_PUSH,
    ACTION_ROLLBACK,
    ACTION_SHELL_COMMAND,
    ACTION_BACKEND_INVOCATION,
    ACTION_ADAPTER_INVOCATION,
})

EXECUTION_CLASS_NONE = "none"
EXECUTION_CLASS_MUTATION = "mutation"
EXECUTION_CLASS_SHELL = "shell"
EXECUTION_CLASS_BACKEND = "backend"
EXECUTION_CLASS_ADAPTER = "adapter"
EXECUTION_CLASS_ROLLBACK = "rollback"

KNOWN_EXECUTION_CLASSES: frozenset[str] = frozenset({
    EXECUTION_CLASS_NONE,
    EXECUTION_CLASS_MUTATION,
    EXECUTION_CLASS_SHELL,
    EXECUTION_CLASS_BACKEND,
    EXECUTION_CLASS_ADAPTER,
    EXECUTION_CLASS_ROLLBACK,
})

# ═══════════════════════════════════════════════════════════════════════════
# Request model
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PermissionBrokerRequest:
    """A canonical, evaluate-only request. The broker never executes this.

    `simulation_only` defaults to True: this foundation has no execution
    boundary (`COMP-002` is `not_implemented`), so every request the
    broker evaluates today is inherently a policy simulation, never a
    real execution attempt.
    """

    request_id: str
    timestamp: str
    action_type: str
    execution_class: str
    task_id: str | None
    phase_id: str | None
    requested_component: str
    requested_capability: str
    requested_resource: str | None
    evidence_available: bool
    approval_present: bool
    simulation_only: bool = True


def build_permission_broker_request(
    *,
    action_type: str,
    execution_class: str,
    requested_component: str,
    requested_capability: str,
    task_id: str | None = None,
    phase_id: str | None = None,
    requested_resource: str | None = None,
    evidence_available: bool = False,
    approval_present: bool = False,
    simulation_only: bool = True,
) -> PermissionBrokerRequest:
    """Build a `PermissionBrokerRequest` with a generated ID and timestamp."""
    return PermissionBrokerRequest(
        request_id=f"pbr-{uuid.uuid4().hex[:12]}",
        timestamp=datetime.now(timezone.utc).isoformat(),
        action_type=action_type,
        execution_class=execution_class,
        task_id=task_id,
        phase_id=phase_id,
        requested_component=requested_component,
        requested_capability=requested_capability,
        requested_resource=requested_resource,
        evidence_available=evidence_available,
        approval_present=approval_present,
        simulation_only=simulation_only,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Decision model
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PermissionBrokerDecision:
    """The broker's evaluation result. Never an execution authorization."""

    decision: str
    decision_reason: str
    matched_no_go_ids: tuple[str, ...]
    matched_invariants: tuple[str, ...]
    required_remediation: tuple[str, ...]
    requires_human: bool
    simulation_only: bool
    implementation_status: str = IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE


def _decision(
    decision: str,
    decision_reason: str,
    *,
    matched_no_go_ids: tuple[str, ...] = (),
    matched_invariants: tuple[str, ...] = (),
    required_remediation: tuple[str, ...] = (),
    requires_human: bool = False,
    simulation_only: bool = True,
) -> PermissionBrokerDecision:
    return PermissionBrokerDecision(
        decision=decision,
        decision_reason=decision_reason,
        matched_no_go_ids=matched_no_go_ids,
        matched_invariants=matched_invariants,
        required_remediation=required_remediation,
        requires_human=requires_human,
        simulation_only=simulation_only,
        implementation_status=IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Broker
# ═══════════════════════════════════════════════════════════════════════════


class PermissionBroker:
    """The single policy decision point for future execution.

    Evaluates proposed actions. Never executes them, never has side
    effects. Fail-closed: anything unknown, unavailable, or unsupported
    resolves to DENY.

    This broker is deliberately isolated from execution mechanics — it
    has no knowledge of shell commands, subprocess invocation, real AI
    backend calls, adapter execution, or Telegram. Those concerns belong
    to future, separately-gated components (`COMP-004`..`COMP-006`,
    `COMP-009`); this broker only decides policy, never carries it out.
    """

    def evaluate(self, request: PermissionBrokerRequest) -> PermissionBrokerDecision:
        """Evaluate a proposed action. Returns a decision. Never executes
        anything; has no side effects."""

        # 0. Structural validation — fail closed on malformed input.
        if not isinstance(request, PermissionBrokerRequest):
            return _decision(
                DECISION_DENY,
                "invalid_request_object",
                matched_no_go_ids=("NG-023",),
                matched_invariants=("INV-009",),
                required_remediation=(
                    "Submit a valid PermissionBrokerRequest instance.",
                ),
            )

        # 1. Unknown action type.
        if request.action_type not in KNOWN_ACTION_TYPES:
            return _decision(
                DECISION_DENY,
                "unknown_action_type",
                matched_no_go_ids=("NG-024",),
                matched_invariants=("INV-004",),
                required_remediation=(
                    "Resolve the policy ambiguity: use a known action_type "
                    "or extend the broker's known-action vocabulary through "
                    "a dedicated amendment phase.",
                ),
            )

        # 2. Unsupported execution class.
        if request.execution_class not in KNOWN_EXECUTION_CLASSES:
            return _decision(
                DECISION_DENY,
                "unsupported_execution_class",
                matched_no_go_ids=("NG-015",),
                matched_invariants=("INV-001",),
                required_remediation=(
                    "Define and implement explicit support for this "
                    "execution class in a dedicated future phase, or "
                    "reclassify the action under an already-supported class.",
                ),
            )

        # 3. Unrecognized component — cannot confirm an execution boundary.
        if request.requested_component not in COMPONENT_IDS:
            return _decision(
                DECISION_DENY,
                "unrecognized_component",
                matched_no_go_ids=("NG-025",),
                matched_invariants=("INV-001",),
                required_remediation=(
                    "Restore/verify the execution boundary for a "
                    "recognized component before this action can be "
                    "attempted.",
                ),
            )

        # 4. Missing active task contract.
        if not request.task_id:
            return _decision(
                DECISION_DENY,
                "missing_active_task_contract",
                matched_no_go_ids=("NG-001",),
                matched_invariants=("INV-002",),
                required_remediation=(
                    "Create and activate a task contract (pcae task new) "
                    "before the action can be re-evaluated.",
                ),
            )

        # 5. Missing evidence.
        if not request.evidence_available:
            return _decision(
                DECISION_DENY,
                "missing_evidence",
                matched_no_go_ids=("NG-023",),
                matched_invariants=("INV-009",),
                required_remediation=(
                    "Supply or restore the missing evidence, then "
                    "re-evaluate.",
                ),
            )

        # 6. Missing human approval — routed to human review, not a hard
        #    deny, per NG-008's remediation path (the human's approval is
        #    the resolution, not an override).
        if not request.approval_present:
            return _decision(
                DECISION_HUMAN_REVIEW,
                "missing_human_approval",
                matched_no_go_ids=("NG-008",),
                matched_invariants=("INV-003",),
                required_remediation=(
                    "Obtain and record an explicit, affirmative human "
                    "approval action before this action can proceed.",
                ),
                requires_human=True,
            )

        # 7. Real (non-simulation) execution attempts always deny: no
        #    execution boundary exists yet (COMP-002 not_implemented).
        #    This gate is unconditionally active by construction (NG-025).
        if not request.simulation_only:
            return _decision(
                DECISION_DENY,
                "execution_boundary_unavailable",
                matched_no_go_ids=("NG-025",),
                matched_invariants=("INV-001",),
                required_remediation=(
                    "No execution boundary exists today. This gate "
                    "cannot be satisfied until a future phase implements "
                    "and verifies COMP-002.",
                ),
                simulation_only=False,
            )

        # 8. All checks pass and this is a simulation-only evaluation:
        #    policy would allow the action if execution existed. This is
        #    never an executable authorization (INV-008).
        return _decision(
            DECISION_ALLOW,
            "policy_would_allow_if_execution_existed",
            matched_invariants=("INV-008",),
        )
