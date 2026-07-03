# Phase 108A — Permission Broker Foundation

## Purpose

Implement the foundational Permission Broker for PCAE as an isolated
policy-evaluation subsystem: the single policy decision point future
execution-track components must eventually ask. This is the first
implementation phase after the governance architecture (107A–107E) was
frozen. The broker evaluates proposed actions and returns a decision. It
never executes anything.

## Scope

Implementation only for the Permission Broker foundation. Produces
`src/pcae/core/permission_broker_foundation.py` and
`tests/test_permission_broker_foundation.py`. Additively references the new
`COMP-NNN` component registry in `docs/V0_2_AUTONOMY_CONTRACT.md` (107B)
and `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (107C) without altering
either document's frozen substance. No runtime execution, shell mediation,
subprocess mediation, backend invocation, adapter invocation, Telegram
inbound, audit persistence, rollback execution, emergency stop
implementation, execution enablement, execution capability, command
execution, file mutation (beyond this phase's own governed source/doc/test
changes), or automatic apply is implemented.

## Architecture

`PermissionBroker` is a single, stateless class with one public method:
`evaluate(request: PermissionBrokerRequest) -> PermissionBrokerDecision`.
It holds no state between calls, performs no file I/O, no network access,
and no subprocess invocation. It is intentionally isolated from every
execution-adjacent PCAE module — it does not import
`pcae.core.shell_gate`, `pcae.core.backend_invocations`,
`pcae.core.notifications`, or any other module that knows how to run a
command, invoke a backend, or send a message. The module's only imports
are Python standard library (`uuid`, `dataclasses`, `datetime`,
`__future__`), verified by a dedicated test that walks the module's AST and
asserts every import resolves to an allowed standard-library name.

This isolation is the architectural expression of design principle 2
("Policy separated from execution"): the broker cannot accidentally gain an
execution capability through a transitive dependency, because it has no
dependency capable of executing anything.

## Responsibilities

- Evaluate a `PermissionBrokerRequest` and return exactly one
  `PermissionBrokerDecision`.
- Apply fail-closed logic: unknown, missing, or unsupported inputs always
  resolve toward `DENY` or `HUMAN_REVIEW`, never `ALLOW`.
- Map every decision to the frozen `NG-NNN` no-go gates (107C) and
  `INV-NNN` invariants (107B) that justify it.
- Serve as the single source of authorization logic for what policy would
  permit — never as an execution mechanism.

The broker does **not**: execute commands, invoke backends, send messages,
mutate files, acquire locks, read or write `.pcae/` state, or depend on
repository state of any kind. Every `evaluate()` call is a pure function of
its input.

## Request Model

`PermissionBrokerRequest` (frozen dataclass) fields: `request_id`,
`timestamp`, `action_type`, `execution_class`, `task_id`, `phase_id`,
`requested_component`, `requested_capability`, `requested_resource`,
`evidence_available`, `approval_present`, `simulation_only` (defaults to
`True`). `build_permission_broker_request(...)` is the constructor helper
that generates `request_id` (`pbr-<uuid12>`) and `timestamp` automatically.

`simulation_only` defaults to `True` because this foundation has no
execution boundary (`COMP-002` is `not_implemented`): every request
evaluated today is inherently a policy simulation, never a real execution
attempt, unless explicitly marked otherwise — and even then, see below.

## Decision Model

`PermissionBrokerDecision` (frozen dataclass) fields: `decision`
(`ALLOW`/`DENY`/`HUMAN_REVIEW`), `decision_reason`, `matched_no_go_ids`
(tuple of `NG-NNN`), `matched_invariants` (tuple of `INV-NNN`),
`required_remediation` (tuple of human-readable remediation steps),
`requires_human` (bool), `simulation_only` (bool), and
`implementation_status` — which is **unconditionally**
`"execution_unavailable"` on every decision this broker returns, including
`ALLOW`. `ALLOW` means "policy would allow this if execution existed," not
an executable authorization (`INV-008`).

## Fail-Closed Philosophy

Every evaluation path that encounters something unknown, missing, or
unsupported returns `DENY` (or `HUMAN_REVIEW` specifically for missing
human approval, per `NG-008`'s own remediation path — the human's approval
*is* the resolution, not an override). The broker never defaults to
`ALLOW` on ambiguity. Checks run in this fixed priority order:

1. Structurally invalid request → `DENY` (`NG-023` / `INV-009`).
2. Unknown `action_type` → `DENY` (`NG-024` / `INV-004`).
3. Unsupported `execution_class` → `DENY` (`NG-015` / `INV-001`).
4. Unrecognized `requested_component` (not a registered `COMP-NNN`) →
   `DENY` (`NG-025` / `INV-001`).
5. Missing `task_id` → `DENY` (`NG-001` / `INV-002`).
6. Missing evidence (`evidence_available=False`) → `DENY` (`NG-023` /
   `INV-009`).
7. Missing approval (`approval_present=False`) → `HUMAN_REVIEW` (`NG-008` /
   `INV-003`).
8. A real (non-simulation) execution attempt → `DENY` (`NG-025` /
   `INV-001`) — unconditionally, because no execution boundary exists yet.
9. Everything else passes, and the request is simulation-only → `ALLOW`
   (`INV-008`), still marked `implementation_status=execution_unavailable`.

## Mapping to INV (docs/V0_2_AUTONOMY_CONTRACT.md)

| Invariant | Used by |
|---|---|
| INV-001 | Unsupported execution class, unrecognized component, real execution attempt |
| INV-002 | Missing active task contract |
| INV-003 | Missing human approval |
| INV-004 | Unknown action type (policy ambiguity), fail-closed default |
| INV-008 | The ALLOW outcome itself — capability/policy-allow never implies authorization |
| INV-009 | Structurally invalid request, missing evidence |

## Mapping to NG (docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md)

| Gate | Used by |
|---|---|
| NG-001 | Missing active task contract |
| NG-008 | Missing human approval |
| NG-015 | Unsupported execution class |
| NG-023 | Structurally invalid request, missing evidence |
| NG-024 | Unknown action type |
| NG-025 | Unrecognized component, real (non-simulation) execution attempt |

The remaining 19 gates (`NG-002`–`NG-007`, `NG-009`–`NG-014`, `NG-016`–
`NG-022`) describe conditions this foundation does not yet evaluate (task
scope matching, health/check/doctor/push-check evidence, rollback/audit/
emergency-stop readiness, unknown shell/backend/adapter actions, branch
protection conflicts, registry mismatches, execution enablement, Telegram
inbound) — they remain the responsibility of future phases (108B onward)
and the components that don't exist yet.

## Mapping to COMP (Component Registry)

Ten canonical component IDs are frozen by this phase:

| ID | Name | Status |
|---|---|---|
| COMP-001 | Permission Broker | **foundation_implemented** |
| COMP-002 | Execution Boundary | not_implemented |
| COMP-003 | Human Approval Gate | not_implemented |
| COMP-004 | Shell Boundary | not_implemented |
| COMP-005 | Backend Boundary | not_implemented |
| COMP-006 | Adapter Boundary | not_implemented |
| COMP-007 | Audit Boundary | not_implemented |
| COMP-008 | Rollback Boundary | not_implemented |
| COMP-009 | Emergency Stop | not_implemented |
| COMP-010 | Execution Enablement | not_implemented |

`docs/V0_2_AUTONOMY_CONTRACT.md`'s twelve named components each gained a
`(COMP-NNN)` suffix on their section header where a canonical ID applies
(ten of the twelve — No-Go Registry and PR / Branch Protection Workflow
are not part of this registry). `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`'s
25 gate detail sections and its Gate Index table each gained a component-ID
reference alongside the existing `Related Component` text. Both edits are
additive only — no frozen prose, invariant, gate condition, or remediation
text was altered.

## Future Integration Points

- **108B — Permission Broker Policy Engine** (recommended next phase):
  extend `evaluate()` with the remaining 19 no-go gates (task scope
  matching, health/check/doctor/push-check evidence, rollback/audit/
  emergency-stop readiness) — still without any execution dependency.
- **Execution Boundary (COMP-002):** once implemented, will be the only
  code path permitted to act on a broker `ALLOW`. This foundation's `ALLOW`
  outcome carries no authority to invoke it.
- **Human Approval Gate (COMP-003):** once implemented, will formally
  record the human action that resolves a `HUMAN_REVIEW` decision. Today,
  `approval_present` is supplied directly on the request by the caller;
  there is no gate implementation to record it.
- **Shell/Backend/Adapter Boundaries (COMP-004/005/006):** each will
  eventually submit requests to this broker before acting, using
  `requested_component` values matching their own COMP-ID, but none of
  them exist yet and this broker has no dependency on any of them.
- **Audit Boundary (COMP-007):** every decision this broker returns is a
  candidate audit record; this foundation does not persist anything —
  durable audit persistence is explicitly out of scope for this phase and
  remains Phase 112A's responsibility per `docs/V0_2_AUTONOMY_CONTRACT.md`.
- **Rollback Readiness Boundary (COMP-008):** a future evaluation path
  (NG-012) will check rollback-plan existence before `ALLOW`; not
  implemented here.

## No-Go Confirmations

No runtime execution. No shell mediation. No subprocess mediation. No
backend invocation. No adapter invocation. No Telegram inbound. No audit
persistence. No rollback execution. No emergency stop implementation. No
execution enablement. No execution capability. No command execution. No
file mutation beyond this phase's own governed source/test/doc changes. No
automatic apply. Every `PermissionBrokerDecision.implementation_status` is
unconditionally `"execution_unavailable"`. `ALLOW` never results in
executable behavior — it only represents "policy would allow this if
execution existed." `v0.1.0-rc1` remains non-executing by design; v0.2
remains the autonomy target (Level 3, not Level 4/5). GitHub Release for
`v0.1.0-rc1` and branch protection on `main` are unchanged. No new tag. No
new GitHub Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**108B — Permission Broker Policy Engine.** Extend the foundation's
`evaluate()` logic to cover the remaining no-go gates this phase does not
yet evaluate, still without introducing any execution dependency.
