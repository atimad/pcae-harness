# PCAE v0.2 Permission Broker Command-Path Integration Design

**Frozen by**: Phase 109A | **Status**: architecture/design only — no broker
command-path integration, runtime execution, shell mediation, subprocess
mediation, backend invocation, adapter invocation, execution enablement,
execution capability, audit persistence, rollback execution, emergency
stop, Telegram inbound, automatic apply, command execution, Permission
Broker enforcement, shell boundary implementation, or backend boundary
implementation is performed by this document or this phase.

## Purpose

Design the first command-path integration architecture for the Permission
Broker (`src/pcae/core/permission_broker_foundation.py`, frozen and
hardened across 108A–108D) — the canonical flow by which a future,
still-unimplemented execution capability would consult the broker before
any mediated action, and the canonical set of command categories,
integration points, and contract obligations that design must satisfy.
This document freezes intent and shape; it grants no execution capability
and connects nothing. Every claim below about a component's status is
either "already true today" (the broker exists, evaluate-only) or
"not implemented" (everything downstream of it).

This document builds on `docs/V0_2_AUTONOMY_CONTRACT.md` (107B — the ten
architectural invariants, the canonical execution lifecycle, and the
twelve named components), `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`
(107C — the 25 no-go gates), `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md`
(107E — Git approval vs. execution approval), and
`docs/PHASE_108_PERMISSION_BROKER_POLICY_COMPOSITION_HARDENING.md` /
`docs/PHASE_108_PERMISSION_BROKER_VERIFICATION_COMPATIBILITY.md` (108C/D —
the frozen `POL-NNN` policy rules and the confirmed fact that the broker
is not imported by any real command path today). It changes none of them.

## 1. Canonical Command-Path Integration Architecture

The future flow, once implemented (not implemented by this phase):

```
AI Agent
  |
  v
Permission Broker (COMP-001)
  |
  v
Command Boundary  [pattern, not a standing component — see below]
  |
  v
Execution Boundary (COMP-002)
  |
  v
Human Approval Gate (COMP-003)
  |
  v
Shell / Backend / Adapter Boundary (COMP-004 / COMP-005 / COMP-006)
  |
  v
Audit Boundary (COMP-007)
  |
  v
Rollback Boundary (COMP-008)
```

**"Command Boundary" is a design pattern, not a new frozen component.**
This phase deliberately does not assign it a canonical `COMP-NNN` ID.
It names the point where a specific integration point (`pcae commit`,
`pcae push`, a future shell-mediation call, etc. — see §3) constructs a
`PermissionBrokerRequest` and calls `PermissionBroker.evaluate()`, before
anything downstream can act. Every integration point follows this same
pattern independently; there is no shared "Command Boundary service" to
implement. A future phase may choose to formalize shared logic across
integration points into its own component if implementation reveals
enough duplication to justify it — this phase does not pre-decide that.

Every stage from `Permission Broker` onward already has a frozen identity
(`COMP-001`–`COMP-008`, all named in `docs/V0_2_AUTONOMY_CONTRACT.md`).
Current implementation status, restated here for this design's context:

| Stage | Component | Status |
|---|---|---|
| Permission Broker | COMP-001 | **foundation_implemented** (108A–108D) — evaluate-only, not wired to anything |
| Command Boundary | *(pattern, no ID)* | not_implemented — no integration point exists yet |
| Execution Boundary | COMP-002 | not_implemented |
| Human Approval Gate | COMP-003 | not_implemented |
| Shell Boundary | COMP-004 | not_implemented |
| Backend Boundary | COMP-005 | not_implemented |
| Adapter Boundary | COMP-006 | not_implemented |
| Audit Boundary | COMP-007 | not_implemented |
| Rollback Boundary | COMP-008 | not_implemented |

## 2. Command Categories

Eleven canonical command classes are frozen. Each is described by
examples, risk level, broker involvement (today and future), future
approval requirement, and current implementation status.

### Read-only

- **Examples:** `cat`, `git log`, `pcae health`, `pcae inspect`.
- **Risk level:** none.
- **Broker involvement (future):** not required — read-only actions have
  no mutating effect to authorize.
- **Future approval requirement:** none.
- **Current implementation status:** fully available today; already
  unmediated by design (nothing to mediate).

### Repository inspection

- **Examples:** `pcae status coherence`, `pcae governance audit`,
  `pcae artifact-index`.
- **Risk level:** none.
- **Broker involvement (future):** not required.
- **Future approval requirement:** none.
- **Current implementation status:** fully available today, unmediated.

### Documentation mutation

- **Examples:** editing a `.md` file within an active task's allowed
  files.
- **Risk level:** low.
- **Broker involvement (future):** would be consulted (`POL-001` active
  task, `POL-002` task-scope once implemented).
- **Future approval requirement:** Git approval only (PR review or the
  Owner's governed push per `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md`)
  — no execution approval concept applies, since this is a Git-tracked
  content change, not a mediated execution action.
- **Current implementation status:** governed today via `pcae check`'s
  independent task-contract scope logic, not broker-mediated (confirmed
  in 108D: `commit.py`/`push.py` contain zero broker references).

### Source mutation

- **Examples:** editing a `.py` file within an active task's allowed
  files.
- **Risk level:** medium.
- **Broker involvement (future):** would be consulted (`POL-001`,
  `POL-002`).
- **Future approval requirement:** Git approval only, same reasoning as
  documentation mutation.
- **Current implementation status:** governed today via `pcae check`,
  not broker-mediated.

### Test execution

- **Examples:** `python -m pytest -n auto`.
- **Risk level:** low–medium (local, sandboxed, no network by default).
- **Broker involvement (future):** would be consulted once a Shell
  Boundary (`COMP-004`) exists and mediates all subprocess invocation,
  including test runners.
- **Future approval requirement:** none anticipated — routine test
  execution is not "execution" in the autonomy-contract sense (it does
  not mutate the repository's governed state); it is ordinary developer/
  agent activity.
- **Current implementation status:** entirely unmediated today, by any
  component — this is normal, expected, and not a gap this design
  proposes to close for test execution specifically.

### Git lifecycle

- **Examples:** `pcae commit implementation`, `pcae task finish
  --commit`, `pcae push`.
- **Risk level:** medium.
- **Broker involvement (future):** would be consulted (`POL-001`,
  `POL-003` evidence, `POL-004` approval where applicable).
- **Future approval requirement:** Git approval (branch protection PR
  review, or the Owner's transitional direct-push exemption) — not
  execution approval; committing/pushing tracked content is not a
  mediated execution action under `docs/V0_2_AUTONOMY_CONTRACT.md`.
- **Current implementation status:** governed today via `pcae check` /
  `pcae push check` / GitHub branch protection; zero broker references
  in `commit.py` or `push.py` (confirmed 108D).

### Git lifecycle: shell execution

- **Examples:** a raw shell command an AI coding agent's own tool-use
  layer runs (e.g. an editor/CLI agent's `Bash` tool), outside PCAE's own
  governed CLI surface entirely.
- **Risk level:** high.
- **Broker involvement (future):** mandatory, once `COMP-004` exists.
- **Future approval requirement:** mandatory human approval (`COMP-003`)
  for anything beyond a narrow pre-approved read-only allowlist.
- **Current implementation status:** **entirely unmediated today** — no
  component anywhere in this codebase intercepts, classifies, or gates
  shell commands an agent's own tooling issues. This is the largest,
  most consequential gap this design exists to eventually close (see §7).

### Backend invocation

- **Examples:** a real call to an AI model API.
- **Risk level:** high.
- **Broker involvement (future):** mandatory, once `COMP-005` exists.
- **Future approval requirement:** mandatory.
- **Current implementation status:** not_implemented anywhere in this
  codebase (`RE-NOGO-003`, `NG-017`).

### Adapter invocation

- **Examples:** a runtime adapter acting on PCAE's behalf.
- **Risk level:** high.
- **Broker involvement (future):** mandatory, once `COMP-006` exists.
- **Future approval requirement:** mandatory.
- **Current implementation status:** not_implemented (`RE-NOGO-004`,
  `NG-018`).

### Network

- **Examples:** an outbound HTTP call beyond the existing, already-
  governed exceptions (git remote/GitHub verification, Telegram outbound
  notification).
- **Risk level:** medium–high.
- **Broker involvement (future):** mandatory for anything beyond the
  existing pre-approved exceptions.
- **Future approval requirement:** mandatory for new network
  destinations; the two existing exceptions remain governed by their own
  established mechanisms (git/GitHub tooling, `pcae notify`), not
  retroactively re-gated by this design.
- **Current implementation status:** no general network mediation exists;
  only the two named exceptions are wired today, and neither goes
  through the broker.

### High-risk

- **Examples:** rollback execution, clearing an emergency stop condition,
  force-push, destructive filesystem operations.
- **Risk level:** critical.
- **Broker involvement (future):** mandatory, with multiple downstream
  gates (`COMP-007` Audit, `COMP-008` Rollback, and the not-yet-frozen
  Emergency Stop boundary `COMP-009`).
- **Future approval requirement:** mandatory; a future phase may require
  more than a single approval for this category specifically (not
  decided by this design).
- **Current implementation status:** not_implemented; several of these
  are additionally hard-blocked today at the shell-gate/hook level
  (force-push, `--no-verify`) as a separate, existing, non-broker
  mechanism (`docs/PHASE_106_REPOSITORY_CONTRIBUTION_SAFETY_BRANCH_PROTECTION.md`,
  108E's pre-push hook) — this design does not replace or weaken those.

## 3. Integration Points

Every future command-path that may eventually consult the broker,
identified and scoped — none integrated by this phase.

| Integration point | Current status | Future integration | Rationale |
|---|---|---|---|
| `pcae commit implementation` | Not broker-integrated; gated by `pcae check`'s independent scope logic. | Would construct a request with `action_type=commit`, `execution_class=mutation`, before performing the commit. | Single source of authorization (108B design principle 3) instead of duplicated ad hoc scope logic. |
| `pcae push` | Not broker-integrated; gated by `pcae push check` + GitHub branch protection. | Would construct a request with `action_type=push`. | Same as above; also lets the broker's fail-closed guarantees extend to the push path uniformly. |
| Shell mediation (future) | Does not exist. No shell command an agent's tooling runs today passes through any PCAE component. | Would be the primary consumer of `execution_class=shell`, mandatory per §2. | Closes the largest command-path gap (§7). |
| Subprocess mediation (future) | Does not exist as a general concept; individual PCAE commands already invoke `subprocess` internally for their own read-only diagnostics (e.g. `pcae doctor git-lock`), which is a different, already-reviewed use — not what this row refers to. | A future execution boundary would mediate subprocess invocation *on an agent's behalf*, distinct from PCAE's own internal read-only subprocess use. | Same boundary as shell mediation; kept as a distinct row because "subprocess" and "shell" are not always the same code path in every future runtime adapter. |
| Backend invocation (future) | Does not exist (`RE-NOGO-003`). | Would consume `execution_class=backend`. | Per §2's Backend invocation category. |
| Adapter invocation (future) | Does not exist (`RE-NOGO-004`). | Would consume `execution_class=adapter`. | Per §2's Adapter invocation category. |
| Future execution API | Does not exist — no unified entry point for mediated actions exists anywhere in this codebase today. | Would be the single call surface every other integration point in this table eventually funnels through, so `COMP-002` Execution Boundary has exactly one way in. | Prevents duplicated authorization logic from re-accumulating across shell/backend/adapter paths independently (the same failure mode 108B's refactor eliminated inside the broker itself). |

**No integration in this table is implemented, connected, or enabled by
this phase.** Every row describes a future call site, not a present one.

## 4. Broker Interaction Contract

Specified against the existing, unmodified `PermissionBrokerRequest` /
`PermissionBrokerDecision` models (108A, extended 108C) — this section
does not change either model; it specifies how a future integration
point would use them.

- **Broker input:** a `PermissionBrokerRequest` — `action_type`,
  `execution_class`, `task_id`, `phase_id`, `requested_component`,
  `requested_capability`, `requested_resource`, `evidence_available`,
  `approval_present`, `simulation_only`. A future integration point is
  responsible for populating every field truthfully before calling
  `evaluate()`; the broker trusts nothing it isn't given and fails closed
  on anything missing (`NG-023`).
- **Broker output:** a `PermissionBrokerDecision` — `decision`
  (`ALLOW`/`DENY`/`HUMAN_REVIEW`), `decision_reason`, `matched_no_go_ids`,
  `matched_invariants`, `matched_component_ids`, `required_remediation`,
  `requires_human`, `causing_policy_id`/`causing_policy_ids`,
  `reason_chain`, `precedence_reason`, and an `implementation_status`
  that today is unconditionally `"execution_unavailable"`.
- **Decision lifecycle:** a broker `evaluate()` call corresponds to the
  `READY -> AWAITING_HUMAN_APPROVAL` transition in
  `docs/V0_2_AUTONOMY_CONTRACT.md`'s canonical execution lifecycle
  (`PLANNED -> READY -> AWAITING_HUMAN_APPROVAL -> AUTHORIZED ->
  EXECUTING -> {COMPLETED|FAILED|ABORTED}`): an action must already be
  `READY` (passed whatever preflight validation a future Command Boundary
  performs) before the broker is asked to decide; a `DENY` returns the
  action to a terminal `FAILED` state without ever reaching
  `AWAITING_HUMAN_APPROVAL`; an `ALLOW` or `HUMAN_REVIEW` moves it to
  `AWAITING_HUMAN_APPROVAL`, where the (not-yet-implemented) Human
  Approval Gate takes over — the broker's `ALLOW` is never itself the
  transition to `AUTHORIZED` (`INV-008`).
- **Required metadata:** at minimum, `task_id` (`NG-001`), evidence of
  the preconditions the specific action category requires
  (`evidence_available`, `NG-023`), and, for anything beyond a
  simulation-only preflight, `approval_present` (`NG-008`) before the
  action can move past `AWAITING_HUMAN_APPROVAL`.
- **Policy evaluation order:** exactly as frozen in 108B/108C — all
  twelve `POL-NNN` rules evaluate independently and unconditionally
  (never short-circuited); composition is `DENY > HUMAN_REVIEW > ALLOW`,
  with order-preserving deduplication across every contributing rule.
  This design does not add, remove, or reorder any policy rule.
- **Failure behavior:** fail-closed, unconditionally. If a future
  integration point cannot construct a valid request (missing required
  context), fails to reach the broker, or receives a malformed response,
  the correct behavior is `DENY` — never proceed, never silently skip
  the broker call. This mirrors the exact guarantee `_sanitize_result`
  already enforces *inside* the broker for malformed policy-rule output
  (108C); a future integration point must apply the same discipline
  *outside* the broker.
- **Audit expectations:** every `PermissionBrokerDecision` is a candidate
  audit record. A future integration point must **not** persist audit
  records itself, ad hoc — that is `COMP-007` Audit Boundary's
  responsibility exclusively (per `docs/V0_2_AUTONOMY_CONTRACT.md`'s
  single-source-of-truth requirement, `INV-005`). Until `COMP-007`
  exists, no integration point may claim to have produced a durable audit
  trail; today's Markdown/JSON phase-completion reports remain v0.1's
  non-execution-track evidence mechanism, not execution audit
  (`RE-NOGO-009`).

## 5. Execution Pipeline

The canonical pipeline is frozen as the eight-stage flow in §1, restated
here as the authoritative sequence with no boundary skipped and no
boundary merged:

```
AI Agent -> Permission Broker -> Command Boundary (pattern)
  -> Execution Boundary -> Human Approval Gate
  -> Shell / Backend / Adapter Boundary -> Audit Boundary
  -> Rollback Boundary
```

No action may reach `Shell / Backend / Adapter Boundary` without first
passing through `Human Approval Gate` (`INV-003`), and no action may
reach `Human Approval Gate` without first receiving a non-`DENY` decision
from the `Permission Broker` (`INV-004`). Every boundary in this pipeline
is either `foundation_implemented` (Permission Broker only) or
`not_implemented` today — no boundary is partially implemented, and this
phase does not implement any of them.

## 6. Design Compatibility

- **Autonomy Contract (107B):** this design introduces no new invariant
  and contradicts none of the existing ten. It reuses `INV-001`
  (execution only through the boundary), `INV-002` (active task
  required), `INV-003` (human approval mandatory), `INV-004` (fail-
  closed), `INV-005` (audit required), `INV-008` (capability does not
  imply authorization) exactly as frozen, and extends none of them.
- **No-Go Gates (107C):** every gate this design's command categories
  and integration points reference (`NG-001`, `NG-008`, `NG-009`,
  `NG-012`–`NG-018`, `NG-021`–`NG-025`) is used as already frozen; no
  gate condition, remediation, or override posture is altered.
- **Local Governance (108E):** the pre-push hook (`pcae health`,
  `pcae check`, `pcae doctor task-memory`, `pcae push check`) and this
  design's future broker-mediated Git-lifecycle integration points are
  complementary, not overlapping — the hook governs the Git-approval
  boundary (§2's Git lifecycle category); the broker, once wired,
  would govern the same category through a different, policy-driven
  mechanism, at the same integration points. Neither replaces the other.
- **Branch Protection (106M, 107E):** branch protection remains the
  GitHub-side authority over what merges to `main`; this design's future
  Execution Boundary governs an entirely different concern (whether a
  *mediated execution action* may run at all), never routes around
  branch protection, and never grants Git approval on its own (§7).
- **Existing lifecycle commands:** `pcae commit implementation`,
  `pcae push`, `pcae task new/finish`, and every other governed lifecycle
  command continue to operate exactly as they do today; this design
  changes none of their current behavior, and 108D's confirmed fact that
  none of them import the broker remains true after this phase.

## 7. Repository Protection Implications

- **How command-path integration would strengthen repository
  protection:** it would close the single largest gap identified across
  108A–108E's own investigation — that shell/subprocess actions an AI
  agent's tooling issues are entirely unmediated by any PCAE component
  today (§2, §3). Git-lifecycle actions already have two independent
  protections (local hooks since 108E, GitHub branch protection since
  106M); shell-class actions currently have none.
- **How it differs from hooks:** hooks (108E) are local, git-native,
  fire only at two fixed points (`pre-commit`, `pre-push`), and are
  fundamentally bypassable by a deliberate `--no-verify` — a client-side
  convention, not an unbypassable gate. Command-path integration, once
  implemented, would be in-process, evaluated at the point of *every*
  mediated action (not just two git lifecycle events), and driven by
  explicit policy rules rather than a fixed shell script.
- **How it differs from branch protection:** branch protection (106M) is
  GitHub-server-side, applies only to what merges into `main` via a PR,
  and has no visibility into individual commands, working-directory-only
  changes, or anything that never reaches a push. Command-path
  integration would apply to actions regardless of whether they ever
  touch git at all (e.g. a shell command with no repository-visible
  effect) — a strictly broader and structurally different surface.
- **Why it remains fail-closed:** every property that makes the broker
  fail-closed today (108A's design principle 1; 108C's malformed-rule and
  empty-registry hardening) is a property of the broker itself, not of
  being wired into a command path. Nothing in this design weakens or
  special-cases that guarantee for any integration point — a future
  Command Boundary that cannot reach the broker, or that receives an
  ambiguous response, must deny, exactly as the broker itself already
  does internally for its own malformed inputs.

## Explicit Non-Goals (This Document and This Phase)

- No broker command-path integration.
- No runtime execution.
- No shell mediation.
- No subprocess mediation.
- No backend invocation.
- No adapter invocation.
- No execution enablement.
- No execution capability.
- No audit persistence.
- No rollback execution.
- No emergency stop.
- No Telegram inbound.
- No automatic apply.
- No command execution.
- No Permission Broker enforcement.
- No shell boundary implementation.
- No backend boundary implementation.

`v0.1.0-rc1` remains non-executing by design; v0.2 remains the autonomy
target (Level 3, not Level 4/5). No change to `v0.1.0-rc1`, its GitHub
Release, or branch protection on `main`.

## Recommended Next Phase

**109B — First Command-Path Integration Prototype (Disabled by
Default).** Implement the first, narrowest integration point from §3
(most likely `pcae commit implementation` or `pcae push`, the
lowest-risk Git-lifecycle category from §2) as a prototype that
constructs a real request and calls `PermissionBroker.evaluate()` —
disabled by default, its result logged/displayed but not yet
authoritative over whether the underlying action proceeds, so today's
existing `pcae check`-based gating remains the real safety mechanism
throughout the prototype phase.
