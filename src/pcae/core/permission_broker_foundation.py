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
ACTION_TYPE_RUNTIME_DISPATCH = "runtime_dispatch"
"""PBRD-001 v1.1 §1 -- additive local-CLI real-runtime dispatch action.
Reuses `EXECUTION_CLASS_ADAPTER` (no new execution class needed). Adding
this one recognized action/class pair is purely additive: no existing
action's mapping changes (PBRD-001 §1/§13)."""

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
    ACTION_TYPE_RUNTIME_DISPATCH,
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
class RuntimeDispatchLifecycleContext:
    """PBRD-001 §4 fact 6 -- one immutable binding fact despite its closed
    subfields. `session_id` is present iff actually session-scoped."""

    phase_id: str
    session_id: str | None = None


@dataclass(frozen=True)
class RuntimeDispatchAdapterDescriptorBinding:
    """PBRD-001 §4 fact 8."""

    adapter_id: str
    descriptor_version: str
    descriptor_digest: str
    target_config_digest: str


@dataclass(frozen=True)
class RuntimeDispatchFilesystemScopeRef:
    """PBRD-001 §4 fact 13 -- immutable ID/digest reference. Declares scope
    for audit/containment; grants no mutation by itself."""

    scope_id: str
    scope_digest: str


@dataclass(frozen=True)
class RuntimeDispatchHumanAuthorityBinding:
    """PBRD-001 §4 fact 14 -- a reference plus a validated-evidence-
    projection digest, never raw authority or a caller-settable boolean.
    Only the trusted RIHAC-001 gate-5 validator may cause this to be
    constructed with real values (see `runtime_dispatch_permission.py`)."""

    approval_id: str
    approval_record_digest: str
    validation_evidence_digest: str


@dataclass(frozen=True)
class RuntimeDispatchRequestFacts:
    """PBRD-001 v1.1 §4 -- the exact fourteen immutable binding facts for
    one `runtime_dispatch` request. Only a trusted, contract-fixed PCAE
    integration point may construct this (§5); an adapter, runtime, or
    caller payload SHALL NOT set any of these fields directly (§15) --
    enforced by `runtime_dispatch_permission.py` never accepting these as
    raw caller input, only as the output of its own trusted builder.
    """

    invocation_id: str
    attempt_id: str
    idempotency_key: str
    repository_identity: str
    task_id: str
    lifecycle_context: RuntimeDispatchLifecycleContext
    runtime_target_id: str
    adapter_descriptor_binding: RuntimeDispatchAdapterDescriptorBinding
    prompt_hash: str
    requested_capability: str
    filesystem_scope_ref: RuntimeDispatchFilesystemScopeRef
    human_authority_binding: RuntimeDispatchHumanAuthorityBinding
    transport_type: str = "local_cli"
    network_requirement: bool = False


@dataclass(frozen=True)
class PermissionBrokerRequest:
    """A canonical, evaluate-only request. The broker never executes this.

    `simulation_only` defaults to True: this foundation has no execution
    boundary (`COMP-002` is `not_implemented`), so every request the
    broker evaluates today is inherently a policy simulation, never a
    real execution attempt.

    `runtime_dispatch_context` (PBRD-001 v1.1 §17, Phase 149O.20L.7O.3V.2
    Option B): an optional nested runtime-dispatch-specific fact bundle.
    Every existing action type leaves this `None`; only `runtime_dispatch`
    requests populate it. This is additive and backward compatible --
    existing `build_permission_broker_request` callers are unaffected.
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
    runtime_dispatch_context: RuntimeDispatchRequestFacts | None = None


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
    runtime_dispatch_context: RuntimeDispatchRequestFacts | None = None,
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
        runtime_dispatch_context=runtime_dispatch_context,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Decision model
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ReasonChainLink:
    """One link in a decision's machine-readable reason chain:
    Policy ID -> No-Go ID(s) -> Invariant ID(s) -> Component ID(s). One
    link per policy rule that contributed to the final decision (Phase
    108C). For a single-cause decision, `PermissionBrokerDecision.reason_chain`
    has exactly one link; for a multi-cause decision (e.g. two
    simultaneously-triggered DENY rules), it has one link per contributor,
    in registry order.
    """

    policy_id: str
    no_go_ids: tuple[str, ...]
    invariant_ids: tuple[str, ...]
    component_ids: tuple[str, ...]


@dataclass(frozen=True)
class PermissionBrokerDecision:
    """The broker's evaluation result. Never an execution authorization.

    `evaluated_policy_ids` lists every policy rule the registry ran for
    this request (all of them, always — rules evaluate independently and
    are never short-circuited). `triggered_policy_ids` lists every rule
    whose condition fired, regardless of whether it determined the final
    decision. `causing_policy_id` names the single, primary rule (first
    in registry order among those matching the winning decision category)
    — kept for simple single-cause explainability and Phase 108B backward
    compatibility. `causing_policy_ids` (Phase 108C) lists *every* rule
    that contributed to the winning category, preserving all relevant
    causes when multiple rules agree on the same outcome (e.g. two
    simultaneously-triggered DENY rules). `matched_no_go_ids`,
    `matched_invariants`, `matched_component_ids`, and
    `required_remediation` are the order-preserving, deduplicated union
    across every contributing rule — not just the primary one.
    `reason_chain` is the same information restructured as one
    `ReasonChainLink` per contributing rule. `precedence_reason` states,
    in one sentence, which precedence rule decided the outcome.
    """

    decision: str
    decision_reason: str
    matched_no_go_ids: tuple[str, ...]
    matched_invariants: tuple[str, ...]
    required_remediation: tuple[str, ...]
    requires_human: bool
    simulation_only: bool
    implementation_status: str = IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE
    matched_component_ids: tuple[str, ...] = ()
    evaluated_policy_ids: tuple[str, ...] = ()
    triggered_policy_ids: tuple[str, ...] = ()
    causing_policy_id: str | None = None
    causing_policy_ids: tuple[str, ...] = ()
    reason_chain: tuple[ReasonChainLink, ...] = ()
    precedence_reason: str = ""
    applicable_policy_ids: tuple[str, ...] = ()
    non_applicable_policy_ids: tuple[str, ...] = ()
    """Phase 148C.6 (PBPA-001 PBPA-REQ-081): every policy resolved
    applicable / not applicable for this request, in registry order.
    `evaluated_policy_ids` is, from this phase forward, exactly
    `applicable_policy_ids` — non-applicable policies are registry
    placeholders, never passed to `evaluate()` (Section 5)."""


def _decision(
    decision: str,
    decision_reason: str,
    *,
    matched_no_go_ids: tuple[str, ...] = (),
    matched_invariants: tuple[str, ...] = (),
    required_remediation: tuple[str, ...] = (),
    requires_human: bool = False,
    simulation_only: bool = True,
    matched_component_ids: tuple[str, ...] = (),
    evaluated_policy_ids: tuple[str, ...] = (),
    triggered_policy_ids: tuple[str, ...] = (),
    causing_policy_id: str | None = None,
    causing_policy_ids: tuple[str, ...] = (),
    reason_chain: tuple[ReasonChainLink, ...] = (),
    precedence_reason: str = "",
    applicable_policy_ids: tuple[str, ...] = (),
    non_applicable_policy_ids: tuple[str, ...] = (),
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
        matched_component_ids=matched_component_ids,
        evaluated_policy_ids=evaluated_policy_ids,
        triggered_policy_ids=triggered_policy_ids,
        causing_policy_id=causing_policy_id,
        causing_policy_ids=causing_policy_ids,
        reason_chain=reason_chain,
        precedence_reason=precedence_reason,
        applicable_policy_ids=applicable_policy_ids,
        non_applicable_policy_ids=non_applicable_policy_ids,
    )


def _dedup_ordered(*sequences: tuple[str, ...]) -> tuple[str, ...]:
    """Order-preserving, deduplicated concatenation of ID tuples."""
    seen: set[str] = set()
    out: list[str] = []
    for seq in sequences:
        for item in seq:
            if item not in seen:
                seen.add(item)
                out.append(item)
    return tuple(out)


# ═══════════════════════════════════════════════════════════════════════════
# Policy Rule Framework — Phase 108B
# ═══════════════════════════════════════════════════════════════════════════
#
# The broker no longer contains hardcoded decision logic. Each policy is a
# small, independent PolicyRule; a PolicyRegistry holds the canonical set;
# the broker orchestrates evaluation and composes the results. Rules never
# know about one another and never short-circuit each other — every
# registered rule evaluates on every request, producing one PolicyResult
# each. This is what makes the broker explainable: every decision names
# exactly which policy (or policies) were evaluated and which one caused
# the outcome.

POLICY_STATUS_IMPLEMENTED = "implemented"
POLICY_STATUS_NOT_IMPLEMENTED = "not_implemented"


@dataclass(frozen=True)
class PolicyResult:
    """One policy rule's independent evaluation of one request.

    `triggered=False` means this policy's condition did not fire for this
    request — the remaining fields are then irrelevant and left at their
    defaults. A rule with `POLICY_STATUS_NOT_IMPLEMENTED` is a registered
    placeholder for a future phase: it is still evaluated on every
    request (satisfying "evaluated policies"), but can never trigger,
    because the request model does not yet carry the evidence that
    policy would need.
    """

    policy_id: str
    triggered: bool
    decision: str | None = None
    decision_reason: str | None = None
    matched_no_go_ids: tuple[str, ...] = ()
    matched_invariants: tuple[str, ...] = ()
    matched_component_ids: tuple[str, ...] = ()
    required_remediation: tuple[str, ...] = ()
    requires_human: bool = False
    simulation_only: bool = True
    applicable: bool = True
    """Phase 148C.6 (PBPA-001 PBPA-REQ-014): whether this policy governed
    this request at all, resolved strictly before `triggered`. Defaults
    to True so every existing call site that predates PBPA-001 — which
    always came from an actually-evaluated rule — is unaffected."""


class PolicyRule:
    """Base class for one independently-evaluated policy.

    Subclasses implement `evaluate(request) -> PolicyResult` and evaluate
    exactly one policy question. A rule must never inspect another rule's
    result and must never itself execute anything — evaluation only.
    """

    policy_id: str = ""
    name: str = ""
    implementation_status: str = POLICY_STATUS_NOT_IMPLEMENTED
    applicable_execution_classes: frozenset[str] | None = None
    """Phase 148C.6 (PBPA-001 PBPA-REQ-018): the frozen domain of
    `execution_class` values this policy governs. `None` (the default)
    means universal — applicable to every `execution_class`, identical to
    every rule's behavior before this phase (PBPA-REQ-044)."""

    def evaluate(self, request: PermissionBrokerRequest) -> PolicyResult:
        raise NotImplementedError

    def applies_to(self, request: PermissionBrokerRequest) -> bool:
        """Phase 148C.6 (PBPA-001 PBPA-REQ-050/051-056): the single,
        generic, policy-owned applicability predicate — pure,
        deterministic, side-effect-free, a function of only
        `self.applicable_execution_classes` and `request.execution_class`.
        Not overridden per-subclass, so no rule can define a second,
        competing notion of its own domain (PBPA-REQ-021)."""
        return (
            self.applicable_execution_classes is None
            or request.execution_class in self.applicable_execution_classes
        )


def _not_triggered(policy_id: str) -> PolicyResult:
    return PolicyResult(policy_id=policy_id, triggered=False)


class MissingActiveTaskRule(PolicyRule):
    """POL-001 — Missing Active Task."""

    policy_id = "POL-001"
    name = "Missing Active Task"
    implementation_status = POLICY_STATUS_IMPLEMENTED

    def evaluate(self, request: PermissionBrokerRequest) -> PolicyResult:
        if request.task_id:
            return _not_triggered(self.policy_id)
        return PolicyResult(
            policy_id=self.policy_id,
            triggered=True,
            decision=DECISION_DENY,
            decision_reason="missing_active_task_contract",
            matched_no_go_ids=("NG-001",),
            matched_invariants=("INV-002",),
            matched_component_ids=("COMP-002",),
            required_remediation=(
                "Create and activate a task contract (pcae task new) "
                "before the action can be re-evaluated.",
            ),
        )


class MissingEvidenceRule(PolicyRule):
    """POL-003 — Missing Evidence."""

    policy_id = "POL-003"
    name = "Missing Evidence"
    implementation_status = POLICY_STATUS_IMPLEMENTED

    def evaluate(self, request: PermissionBrokerRequest) -> PolicyResult:
        if request.evidence_available:
            return _not_triggered(self.policy_id)
        return PolicyResult(
            policy_id=self.policy_id,
            triggered=True,
            decision=DECISION_DENY,
            decision_reason="missing_evidence",
            matched_no_go_ids=("NG-023",),
            matched_invariants=("INV-009",),
            matched_component_ids=("COMP-001",),
            required_remediation=(
                "Supply or restore the missing evidence, then re-evaluate.",
            ),
        )


class MissingHumanApprovalRule(PolicyRule):
    """POL-004 — Missing Human Approval.

    Routes to HUMAN_REVIEW, not a hard deny, per NG-008's own remediation
    path — the human's approval is the resolution, not an override.
    """

    policy_id = "POL-004"
    name = "Missing Human Approval"
    implementation_status = POLICY_STATUS_IMPLEMENTED
    applicable_execution_classes = frozenset({
        EXECUTION_CLASS_SHELL,
        EXECUTION_CLASS_BACKEND,
        EXECUTION_CLASS_ADAPTER,
        EXECUTION_CLASS_ROLLBACK,
    })
    """Phase 148C.6 (PBPA-001 PBPA-REQ-063): scoped to mediated-execution
    classes only. `EXECUTION_CLASS_NONE` and `EXECUTION_CLASS_MUTATION`
    are excluded — a general rule applied uniformly to every
    execution_class, not a push-specific carve-out (PBPA-REQ-064)."""

    def evaluate(self, request: PermissionBrokerRequest) -> PolicyResult:
        if request.approval_present:
            return _not_triggered(self.policy_id)
        return PolicyResult(
            policy_id=self.policy_id,
            triggered=True,
            decision=DECISION_HUMAN_REVIEW,
            decision_reason="missing_human_approval",
            matched_no_go_ids=("NG-008",),
            matched_invariants=("INV-003",),
            matched_component_ids=("COMP-003",),
            required_remediation=(
                "Obtain and record an explicit, affirmative human "
                "approval action before this action can proceed.",
            ),
            requires_human=True,
        )


class ExecutionDisabledRule(PolicyRule):
    """POL-005 — Execution Disabled.

    A real (non-simulation) execution attempt always denies: no execution
    boundary exists yet (COMP-002 not_implemented). Unconditionally
    active by construction (NG-025).
    """

    policy_id = "POL-005"
    name = "Execution Disabled"
    implementation_status = POLICY_STATUS_IMPLEMENTED

    def evaluate(self, request: PermissionBrokerRequest) -> PolicyResult:
        if request.simulation_only:
            return _not_triggered(self.policy_id)
        return PolicyResult(
            policy_id=self.policy_id,
            triggered=True,
            decision=DECISION_DENY,
            decision_reason="execution_boundary_unavailable",
            matched_no_go_ids=("NG-025",),
            matched_invariants=("INV-001",),
            matched_component_ids=("COMP-002",),
            required_remediation=(
                "No execution boundary exists today. This gate cannot "
                "be satisfied until a future phase implements and "
                "verifies COMP-002.",
            ),
            simulation_only=False,
        )


class UnknownCapabilityRule(PolicyRule):
    """POL-006 — Unknown Capability.

    Covers both `action_type` and `execution_class`: both describe the
    fundamental nature of the requested capability, so one policy
    question ("is this capability recognized?") evaluates both fields.
    """

    policy_id = "POL-006"
    name = "Unknown Capability"
    implementation_status = POLICY_STATUS_IMPLEMENTED

    def evaluate(self, request: PermissionBrokerRequest) -> PolicyResult:
        if request.action_type not in KNOWN_ACTION_TYPES:
            return PolicyResult(
                policy_id=self.policy_id,
                triggered=True,
                decision=DECISION_DENY,
                decision_reason="unknown_action_type",
                matched_no_go_ids=("NG-024",),
                matched_invariants=("INV-004",),
                matched_component_ids=("COMP-001",),
                required_remediation=(
                    "Resolve the policy ambiguity: use a known "
                    "action_type or extend the broker's known-action "
                    "vocabulary through a dedicated amendment phase.",
                ),
            )
        if request.execution_class not in KNOWN_EXECUTION_CLASSES:
            return PolicyResult(
                policy_id=self.policy_id,
                triggered=True,
                decision=DECISION_DENY,
                decision_reason="unsupported_execution_class",
                matched_no_go_ids=("NG-015",),
                matched_invariants=("INV-001",),
                matched_component_ids=("COMP-002",),
                required_remediation=(
                    "Define and implement explicit support for this "
                    "execution class in a dedicated future phase, or "
                    "reclassify the action under an already-supported "
                    "class.",
                ),
            )
        return _not_triggered(self.policy_id)


class UnknownComponentRule(PolicyRule):
    """POL-007 — Unknown Component."""

    policy_id = "POL-007"
    name = "Unknown Component"
    implementation_status = POLICY_STATUS_IMPLEMENTED

    def evaluate(self, request: PermissionBrokerRequest) -> PolicyResult:
        if request.requested_component in COMPONENT_IDS:
            return _not_triggered(self.policy_id)
        return PolicyResult(
            policy_id=self.policy_id,
            triggered=True,
            decision=DECISION_DENY,
            decision_reason="unrecognized_component",
            matched_no_go_ids=("NG-025",),
            matched_invariants=("INV-001",),
            matched_component_ids=("COMP-002",),
            required_remediation=(
                "Restore/verify the execution boundary for a "
                "recognized component before this action can be "
                "attempted.",
            ),
        )


class StubPolicyRule(PolicyRule):
    """A registered, always-evaluated placeholder for a policy this
    foundation cannot yet check — the request model does not carry the
    evidence the policy would need (e.g. no emergency-stop flag, no
    audit-boundary handle, no rollback-plan reference, no backend/adapter
    identity field). Registering the ID now keeps `POL-NNN` identifiers
    stable across phases (per this phase's design principle) without
    fabricating a check the broker cannot honestly perform.
    """

    def __init__(self, policy_id: str, name: str) -> None:
        self.policy_id = policy_id
        self.name = name
        self.implementation_status = POLICY_STATUS_NOT_IMPLEMENTED

    def evaluate(self, request: PermissionBrokerRequest) -> PolicyResult:
        return _not_triggered(self.policy_id)


# ── Canonical policy ID registry (POL-001..012) ─────────────────────────
#
# Registry order is POL-001..012 numeric order. Decision composition (see
# PermissionBroker.evaluate) prioritizes DENY over HUMAN_REVIEW globally
# regardless of registry position; registry order only breaks ties among
# multiple simultaneously-triggered rules of the *same* decision value.

DEFAULT_POLICY_RULES: tuple[PolicyRule, ...] = (
    MissingActiveTaskRule(),
    StubPolicyRule("POL-002", "Task Outside Scope"),
    MissingEvidenceRule(),
    MissingHumanApprovalRule(),
    ExecutionDisabledRule(),
    UnknownCapabilityRule(),
    UnknownComponentRule(),
    StubPolicyRule("POL-008", "Emergency Stop Active"),
    StubPolicyRule("POL-009", "Audit Unavailable"),
    StubPolicyRule("POL-010", "Rollback Unavailable"),
    StubPolicyRule("POL-011", "Unknown Backend"),
    StubPolicyRule("POL-012", "Unknown Adapter"),
)

POLICY_IDS: tuple[str, ...] = tuple(rule.policy_id for rule in DEFAULT_POLICY_RULES)

POLICY_IDS_CANONICAL: frozenset[str] = frozenset(f"POL-{n:03d}" for n in range(1, 13))
"""Phase 148C.6 (PBPA-001 PBPA-REQ-073): the independent canonical
reference a constructed `PolicyRegistry`'s rule tuple is validated
against. Fixed, not derived from `DEFAULT_POLICY_RULES` — validating
completeness against a set derived from the same registry would be
circular."""


_VALID_RESULT_DECISIONS = frozenset(DECISION_VALUES)


def _sanitize_result(rule: PolicyRule, raw: object) -> PolicyResult:
    """Fail-closed guard against a malformed or failing `PolicyRule`
    (Phase 108C, design principle 1: "if anything is unknown,
    unavailable, or unsupported: Decision = DENY").

    A rule that raised an exception (`raw is None` here — the caller
    already caught it), returned something other than a `PolicyResult`,
    or returned `triggered=True` with a `decision` outside
    ALLOW/DENY/HUMAN_REVIEW is never silently ignored and never treated
    as a pass-through ALLOW — it is converted into a DENY-triggering
    result, still labeled with the rule's own `policy_id` when available.
    """
    policy_id = getattr(rule, "policy_id", None) or "POL-000"

    if isinstance(raw, PolicyResult):
        if not raw.triggered or raw.decision in _VALID_RESULT_DECISIONS:
            return raw
        policy_id = raw.policy_id or policy_id

    return PolicyResult(
        policy_id=policy_id,
        triggered=True,
        decision=DECISION_DENY,
        decision_reason="invalid_policy_result",
        matched_no_go_ids=("NG-024",),
        matched_invariants=("INV-004",),
        matched_component_ids=("COMP-001",),
        required_remediation=(
            "Repair the malfunctioning policy rule; fail-closed until "
            "it returns a valid PolicyResult with a recognized decision.",
        ),
    )


class PolicyRegistry:
    """Holds the canonical set of policy rules and evaluates all of them.

    Future rule addition means constructing a new `PolicyRegistry` with
    an extended rule tuple — the broker itself never needs to change. No
    plugin system; a plain, explicit tuple is sufficient.
    """

    def __init__(self, rules: tuple[PolicyRule, ...] = DEFAULT_POLICY_RULES) -> None:
        # Phase 148C.6 (PBPA-001 PBPA-REQ-073/075): construction-time
        # registry validation — a missing canonical policy or a duplicate
        # policy_id is a registry-construction defect, not a request-time
        # condition, and fails closed by raising rather than by silently
        # accepting an incomplete or ambiguous rule set.
        ids = tuple(rule.policy_id for rule in rules)
        if len(ids) != len(set(ids)):
            raise ValueError("PolicyRegistry: duplicate policy_id in rule set")
        missing = POLICY_IDS_CANONICAL - set(ids)
        if missing:
            raise ValueError(
                f"PolicyRegistry: missing canonical policy id(s): {sorted(missing)}"
            )
        self._rules = rules

    @property
    def policy_ids(self) -> tuple[str, ...]:
        return tuple(rule.policy_id for rule in self._rules)

    def evaluate_all(self, request: PermissionBrokerRequest) -> tuple[PolicyResult, ...]:
        """Evaluate every applicable registered rule independently. Never
        short-circuits; every applicable rule always runs. A rule that
        raises or returns a malformed result never crashes evaluation or
        is silently dropped — it is sanitized into a fail-closed DENY.

        Phase 148C.6 (PBPA-001 PBPA-REQ-015/021): a rule for which
        `applies_to(request)` is False is never passed to its own
        `evaluate()` — the registry synthesizes a `PolicyResult` with
        `applicable=False, triggered=False` (the registry's own
        "not-run" default, never a synthesized judgment) instead.

        Phase 148C.6 (PBPA-001 PBPA-REQ-097): a predicate that cannot
        resolve (raises, or is missing entirely on a malformed rule)
        SHALL NOT silently produce `NOT_APPLICABLE` — it is sanitized
        into the same fail-closed path as an `evaluate()` failure,
        never skipped.
        """
        results: list[PolicyResult] = []
        for rule in self._rules:
            try:
                applies = rule.applies_to(request)
            except Exception:
                results.append(_sanitize_result(rule, None))
                continue
            if not applies:
                results.append(
                    PolicyResult(
                        policy_id=rule.policy_id,
                        triggered=False,
                        applicable=False,
                    )
                )
                continue
            try:
                raw = rule.evaluate(request)
            except Exception:
                raw = None
            results.append(_sanitize_result(rule, raw))
        return tuple(results)


def _compose(results: tuple[PolicyResult, ...]) -> PermissionBrokerDecision:
    """Centralized decision composition — the single place a
    `PermissionBrokerDecision` is ever assembled from policy results.

    Precedence: DENY > HUMAN_REVIEW > ALLOW, fail closed. When multiple
    rules trigger the same winning category, every one of their
    `matched_no_go_ids` / `matched_invariants` / `matched_component_ids`
    / `required_remediation` is preserved (order-preserving, deduplicated
    union) — "all relevant causes preserved" (Phase 108C, objective 3).
    `causing_policy_id` names the first contributor in registry order
    (108B compatibility); `causing_policy_ids` names every contributor.
    An empty `results` tuple (no policy was evaluated at all) cannot
    vouch for ALLOW and fails closed to DENY.
    """
    triggered = tuple(r for r in results if r.triggered)
    triggered_ids = tuple(r.policy_id for r in triggered)
    # Phase 148C.6 (PBPA-001 PBPA-REQ-081): additive explainability
    # fields, computed from data already present in `results` — no new
    # data source, no change to precedence logic below. `evaluated_ids`
    # is redefined by PBPA-REQ-081 to mean exactly "every policy actually
    # passed to evaluate()" — i.e. applicable_ids — since non-applicable
    # results are registry-synthesized placeholders never evaluated.
    applicable_ids = tuple(r.policy_id for r in results if r.applicable)
    non_applicable_ids = tuple(r.policy_id for r in results if not r.applicable)
    evaluated_ids = applicable_ids

    if not results:
        return _decision(
            DECISION_DENY,
            "no_applicable_policy",
            matched_no_go_ids=("NG-009",),
            matched_invariants=("INV-004",),
            required_remediation=(
                "Register at least one policy rule before evaluating "
                "requests; an empty registry cannot vouch for ALLOW.",
            ),
            precedence_reason="fail_closed_no_policies_registered",
        )

    for decision_value in (DECISION_DENY, DECISION_HUMAN_REVIEW):
        matching = tuple(r for r in triggered if r.decision == decision_value)
        if not matching:
            continue
        primary = matching[0]
        plural = "y" if len(matching) == 1 else "ies"
        return _decision(
            decision_value,
            primary.decision_reason or decision_value.lower(),
            matched_no_go_ids=_dedup_ordered(*(r.matched_no_go_ids for r in matching)),
            matched_invariants=_dedup_ordered(*(r.matched_invariants for r in matching)),
            matched_component_ids=_dedup_ordered(*(r.matched_component_ids for r in matching)),
            required_remediation=_dedup_ordered(*(r.required_remediation for r in matching)),
            requires_human=any(r.requires_human for r in matching),
            simulation_only=primary.simulation_only,
            evaluated_policy_ids=evaluated_ids,
            triggered_policy_ids=triggered_ids,
            applicable_policy_ids=applicable_ids,
            non_applicable_policy_ids=non_applicable_ids,
            causing_policy_id=primary.policy_id,
            causing_policy_ids=tuple(r.policy_id for r in matching),
            reason_chain=tuple(
                ReasonChainLink(
                    policy_id=r.policy_id,
                    no_go_ids=r.matched_no_go_ids,
                    invariant_ids=r.matched_invariants,
                    component_ids=r.matched_component_ids,
                )
                for r in matching
            ),
            precedence_reason=(
                f"{decision_value.lower()}_precedence: {len(matching)} "
                f"{decision_value}-triggering polic{plural} present"
            ),
        )

    # Nothing triggered: policy would allow this if execution existed.
    # Never an executable authorization (INV-008).
    return _decision(
        DECISION_ALLOW,
        "policy_would_allow_if_execution_existed",
        matched_invariants=("INV-008",),
        evaluated_policy_ids=evaluated_ids,
        triggered_policy_ids=triggered_ids,
        applicable_policy_ids=applicable_ids,
        non_applicable_policy_ids=non_applicable_ids,
        precedence_reason="allow_default: no policy triggered a block",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Broker
# ═══════════════════════════════════════════════════════════════════════════


class PermissionBroker:
    """The single policy decision point for future execution.

    Evaluates proposed actions. Never executes them, never has side
    effects. Fail-closed: anything unknown, unavailable, or unsupported
    resolves to DENY.

    As of Phase 108B, the broker is an orchestrator, not a policy
    author: it delegates to a `PolicyRegistry`, which evaluates every
    registered `PolicyRule` independently, and composes the results
    (DENY > HUMAN_REVIEW > ALLOW). The broker contains no policy logic
    of its own beyond structural request validation and composition.

    This broker is deliberately isolated from execution mechanics — it
    has no knowledge of shell commands, subprocess invocation, real AI
    backend calls, adapter execution, or Telegram. Those concerns belong
    to future, separately-gated components (`COMP-004`..`COMP-006`,
    `COMP-009`); this broker only decides policy, never carries it out.
    """

    def __init__(self, registry: PolicyRegistry | None = None) -> None:
        self._registry = registry if registry is not None else PolicyRegistry()

    def evaluate(self, request: PermissionBrokerRequest) -> PermissionBrokerDecision:
        """Evaluate a proposed action. Returns a decision. Never executes
        anything; has no side effects."""

        # Structural validation — fail closed on malformed input. This is
        # request-shape validation, not a policy question, so it happens
        # before any PolicyRule is asked to evaluate anything.
        if not isinstance(request, PermissionBrokerRequest):
            return _decision(
                DECISION_DENY,
                "invalid_request_object",
                matched_no_go_ids=("NG-023",),
                matched_invariants=("INV-009",),
                required_remediation=(
                    "Submit a valid PermissionBrokerRequest instance.",
                ),
                precedence_reason="fail_closed_invalid_request",
            )

        results = self._registry.evaluate_all(request)
        return _compose(results)
