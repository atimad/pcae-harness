# Phase 108B — Permission Broker Policy Rule Framework

## Purpose

Transform the Permission Broker from a broker containing hardcoded
decision logic (Phase 108A) into a broker that orchestrates an extensible
policy rule framework. The broker itself no longer knows any policy
condition; it delegates to a registry of independent `PolicyRule`
instances and composes their results. This is the second implementation
phase in the execution-track sequence (107A–107E design/freeze, 108A
foundation, 108B this phase).

## Scope

Extends only the policy framework inside
`src/pcae/core/permission_broker_foundation.py` and adds
`tests/test_permission_broker_policy_rule_framework.py`. No runtime
execution, shell mediation, subprocess mediation, backend invocation,
adapter invocation, Telegram inbound, audit persistence, rollback
execution, emergency stop implementation, execution enablement, execution
capability, command execution, file mutation beyond this phase's own
governed source/test/doc changes, or automatic apply is implemented.
`tests/test_permission_broker_foundation.py` (108A) is unmodified and
re-verified to pass unchanged against the refactored implementation — this
phase is a pure internal restructuring, not a behavior change for any
previously-tested scenario.

## Architecture

Three new layers sit between the `PermissionBroker` and its decision:

```
PermissionBroker
  |
  v
PolicyRegistry
  |
  v
PolicyRule 1 . PolicyRule 2 . ... . PolicyRule 12
  |
  v
Decision Composition
  |
  v
PermissionBrokerDecision
```

`PermissionBroker.evaluate(request)` still performs one thing itself:
structural validation of the request object (fail-closed on a malformed
input, before any policy question is even askable). Everything else is
delegated: it asks its `PolicyRegistry` to evaluate every rule, then
composes the results. The broker's `evaluate()` method body contains no
policy-specific `NG-`/`INV-` literal beyond the structural guard and the
ALLOW default's own `INV-008` (which describes the meaning of "ALLOW"
itself, not a duplicated per-policy condition) — verified by a dedicated
test.

## Policy Registry

`PolicyRegistry` holds an ordered tuple of `PolicyRule` instances
(`DEFAULT_POLICY_RULES`, 12 entries, `POL-001`..`POL-012` in numeric
order) and one method: `evaluate_all(request) -> tuple[PolicyResult, ...]`.
Every registered rule evaluates on every request — evaluation is never
short-circuited, so `evaluated_policy_ids` on the final decision always
lists all 12 IDs regardless of outcome. Future rule addition means
constructing a new `PolicyRegistry` with an extended rule tuple; the
broker's constructor accepts an optional registry
(`PermissionBroker(registry=...)`, defaulting to a fresh
`PolicyRegistry()`), so the broker itself never needs to change to
accommodate new or swapped-in rules. No plugin system — a plain, explicit
tuple is sufficient, per this phase's own design instruction.

## Policy Interface

```python
class PolicyRule:
    policy_id: str
    name: str
    implementation_status: str  # "implemented" | "not_implemented"

    def evaluate(self, request: PermissionBrokerRequest) -> PolicyResult:
        ...
```

`PolicyResult` (frozen dataclass): `policy_id`, `triggered`, `decision`
(`None` unless triggered), `decision_reason`, `matched_no_go_ids`,
`matched_invariants`, `matched_component_ids`, `required_remediation`,
`requires_human`, `simulation_only`. A rule evaluates exactly one policy
question and takes only `request` as input — verified structurally by a
test that inspects every rule's `evaluate` signature. Rules never inspect
another rule's result and never call another rule.

Six rules carry real logic, reproducing 108A's exact prior checks under
their new `POL-NNN` identity: `MissingActiveTaskRule` (`POL-001`),
`MissingEvidenceRule` (`POL-003`), `MissingHumanApprovalRule` (`POL-004`),
`ExecutionDisabledRule` (`POL-005`), `UnknownCapabilityRule` (`POL-006` —
covers both `action_type` and `execution_class`, since both describe the
fundamental nature of the requested capability), and
`UnknownComponentRule` (`POL-007`). Six more are registered as
`StubPolicyRule` placeholders (`POL-002`, `POL-008`–`POL-012`) — they are
still evaluated on every request (satisfying "evaluated policies"), but
can never trigger, because the current request model does not yet carry
the evidence those policies would need (no task-scope fields, no
emergency-stop flag, no audit-boundary handle, no rollback-plan
reference, no backend/adapter identity field). Registering the ID now
keeps `POL-NNN` identifiers stable across phases without fabricating a
check the broker cannot honestly perform.

## Decision Composition

`_compose(triggered)` implements the fixed priority ladder: **DENY >
HUMAN_REVIEW > ALLOW**, fail-closed. It scans triggered results for a
`DENY` first (in registry order, for deterministic tie-breaking among
simultaneously-triggered `DENY` rules); if none, scans for a
`HUMAN_REVIEW`; if neither, the broker's ALLOW default applies
(`decision_reason="policy_would_allow_if_execution_existed"`,
`matched_invariants=("INV-008",)`). This means `DENY` always wins over
`HUMAN_REVIEW` even when a `HUMAN_REVIEW`-triggering rule sits earlier in
registry order than the `DENY`-triggering one — precedence is checked by
decision *category* first, registry position second.

## Precedence Rules

1. Any triggered `DENY` → the first such result (by registry order) wins.
2. No `DENY`, but a triggered `HUMAN_REVIEW` → the first such result wins.
3. Nothing triggered → `ALLOW` (the composition default).

Verified directly: `test_deny_precedence_over_human_review`,
`test_human_review_precedence_over_allow`,
`test_allow_precedence_when_nothing_triggers`,
`test_composition_picks_first_deny_in_registry_order`.

## Policy Identifiers

| ID | Name | Status |
|---|---|---|
| POL-001 | Missing Active Task | implemented |
| POL-002 | Task Outside Scope | not_implemented (stub) |
| POL-003 | Missing Evidence | implemented |
| POL-004 | Missing Human Approval | implemented |
| POL-005 | Execution Disabled | implemented |
| POL-006 | Unknown Capability | implemented |
| POL-007 | Unknown Component | implemented |
| POL-008 | Emergency Stop Active | not_implemented (stub, future placeholder) |
| POL-009 | Audit Unavailable | not_implemented (stub) |
| POL-010 | Rollback Unavailable | not_implemented (stub) |
| POL-011 | Unknown Backend | not_implemented (stub) |
| POL-012 | Unknown Adapter | not_implemented (stub) |

IDs are frozen as stable identifiers as of this phase; names may evolve,
IDs should not.

## Explainability

Every `PermissionBrokerDecision` now carries three fields dedicated to
explainability, in addition to the fields introduced in 108A:
`evaluated_policy_ids` (all 12 IDs, always), `triggered_policy_ids` (the
subset whose condition fired), and `causing_policy_id` (the single ID
that composition selected — `None` only for the structural-guard rejection
and the ALLOW default, neither of which is caused by a specific policy).
A caller can always answer "why this decision?" by reading
`causing_policy_id` and cross-referencing it against the policy table
above, without needing to inspect broker internals.

## Extension Model

Adding a policy in a future phase requires: (1) a new `PolicyRule`
subclass implementing `evaluate()`, (2) adding it to a `PolicyRegistry`
rule tuple, (3) nothing else — `PermissionBroker` is unmodified. Swapping
a stub for a real implementation (e.g., turning `POL-002` from a
placeholder into a real task-scope check once the request model gains
scope fields) means replacing that one tuple entry; every other rule, the
registry's iteration logic, and the composition logic are untouched. This
was verified directly: `test_custom_registry_composition` and
`test_broker_evaluate_delegates_to_registry` inject entirely custom
registries and confirm the broker follows whatever registry it is given,
never its own hardcoded logic.

## No-Go Confirmations

No runtime execution. No shell mediation. No subprocess mediation. No
backend invocation. No adapter invocation. No Telegram inbound. No audit
persistence. No rollback execution. No emergency stop implementation. No
execution enablement. No execution capability. No command execution. No
file mutation beyond this phase's own governed source/test/doc changes.
No automatic apply. `implementation_status` remains unconditionally
`"execution_unavailable"` on every decision. `ALLOW` never results in
executable behavior. The module remains fully isolated: no dependency on
`shell_gate`, `backend_invocations`, `notifications`, or any other
execution-adjacent module (unchanged from 108A, re-verified by 108A's own
unmodified isolation tests passing against this phase's refactored code).
`v0.1.0-rc1` remains non-executing by design; v0.2 remains the autonomy
target (Level 3, not Level 4/5). GitHub Release for `v0.1.0-rc1` and
branch protection on `main` are unchanged. No new tag. No new GitHub
Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**108C — Permission Broker Policy Composition & Hardening.**
