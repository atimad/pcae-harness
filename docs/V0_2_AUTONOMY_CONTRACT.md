# PCAE v0.2 Autonomy Contract

**Frozen by**: Phase 107B | **Status**: contract/design only — no enforcement or execution capability implemented by this document or this phase.

## Purpose

Freeze, in one canonical document, what PCAE v0.2 autonomy actually
means, before any enforcement or execution implementation begins. This
contract is the single source of truth that phases 108A onward must
build against; it does not itself implement runtime enforcement,
autonomous execution, shell/subprocess mediation, backend invocation,
adapter execution, Telegram inbound, durable audit storage, rollback
execution, an emergency stop mechanism, an execution enablement flag/
toggle, automatic apply, or patch execution. Everything below describes
what must exist before execution is possible — not what exists today.

## v0.2 Autonomy Target

**PCAE v0.2 targets Autonomy Level 3 — Governed Human-Approved Bounded
Execution** (see `docs/V0_2_AUTONOMY_ROADMAP.md` for the full six-level
model). This is a deliberate, narrow target:

- **v0.1 remains non-executing.** `v0.1.0-rc1` is Level 0. Nothing in
  this contract changes that; `v0.1.0-rc1` is unaffected by this
  document.
- **Execution remains unavailable now.** This contract freezes intent
  and design; it grants no execution capability. Every authorization
  flag in the shared safety/authorization contract remains `False`
  after this phase.
- v0.2 does **not** target Level 4 (policy-brokered autonomy without a
  human in the loop) or Level 5 (broad multi-agent autonomy). Those
  remain explicitly out of scope until Level 3 has been implemented,
  tested, and proven safe in production use.

## Permission Broker Role

The permission broker is the single authority that decides whether a
proposed action may proceed. Its decision is one of exactly three
values: `allow`, `deny`, or `human_review`. No component may execute an
action the broker has not evaluated. The broker's decision is
**fail-closed** (INV-004): any error, missing input, or ambiguous
evidence resolves to `deny`, never to `allow`.

## Human Approval Requirement

For v0.2 Level 3, **every** authorized execution requires an explicit,
affirmative human approval action — not an inferred signal, not a
timeout-based default, not an absence of objection. The human approval
gate sits between `AWAITING_HUMAN_APPROVAL` and `AUTHORIZED` in the
execution lifecycle (below) and cannot be skipped, bypassed, or
satisfied by any automated process.

## Shell/Subprocess/Network Boundaries

Any shell command, subprocess invocation, or network call that is part
of a mediated execution action must pass through the Shell/Subprocess/
Network Boundary component (below) — not be issued directly by any
other part of PCAE. This boundary is distinct from, and does not
authorize, the existing lifecycle/test/docs/git-remote-verification
subprocess and network behavior PCAE already performs today (e.g. `pcae
push`, `python -m pytest`, `gh api` branch-protection calls) — those
remain ordinary governed-tooling operations, not "execution" under this
contract.

## Backend/Adapter Invocation Boundaries

Real AI backend calls and adapter execution must each pass through a
dedicated boundary component. Neither exists today (RE-NOGO-003,
RE-NOGO-004). Both boundaries are subject to the same permission-broker
decision and human-approval requirement as any other mediated action —
there is no separate, lower-trust path for backend or adapter calls.

## Audit Requirements

Every execution decision — `allow`, `deny`, or `human_review`, and every
lifecycle-state transition that follows — must produce an audit artifact
(INV-005). For v0.2, that artifact must be durably persisted (survives
process restart, is queryable) — not merely an in-memory value or a
Markdown/JSON phase-completion report, which is v0.1's existing
evidence mechanism and is insufficient on its own for execution audit
(RE-NOGO-009). The durable audit store's exact storage mechanism is
undecided by this contract and is Phase 112A's responsibility; this
contract only freezes the *requirement*, not the implementation.

## Rollback Readiness Requirements

No mutating action may be authorized unless rollback readiness already
exists for that specific action *before* authorization is granted
(INV-006) — rollback readiness is a precondition, not a follow-up step.
"Readiness" means: a concrete, validated rollback plan exists for the
specific action, not a generic statement that rollback is theoretically
possible. Rollback *execution* itself (actually running the rollback) is
explicitly out of scope for this contract and for v0.2's initial
implementation phases — see `docs/V0_2_AUTONOMY_ROADMAP.md`'s staged
sequence (113A is rollback governance *design*, not rollback execution).

## Emergency Stop Requirement

An emergency stop/abort mechanism must exist and must be capable of
halting an in-progress mediated execution at any point in the lifecycle
(INV-007). Emergency stop overrides every other authorization — a
human-approved, broker-allowed, in-progress execution must still be
abortable. This contract only freezes the requirement; implementing the
mechanism is Phase 114A's responsibility, and no such mechanism exists
today.

## Execution Enablement Model (Future / Default-Off)

Execution enablement is modeled as an explicit, narrow, reversible
flag/toggle — **not implemented by this contract or this phase**. When it
is eventually implemented (a future phase, gated behind everything else
in this contract being complete and tested), its default value must be
off, and enabling it must be an explicit, documented, human-driven
action, not an inferred or automatic state change. No such flag exists
in the codebase today; this contract only fixes its future shape and
default.

## Hard No-Go Conditions

Execution must remain unavailable until every condition in
`docs/V0_2_AUTONOMY_ROADMAP.md`'s "Hard No-Go Conditions" section is
true, and until every architectural invariant below is implemented and
tested — not merely documented. This contract does not weaken, replace,
or duplicate the frozen `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`
(RE-NOGO-001 through RE-NOGO-017); it is additive and references that
registry as authoritative for existing entries.

## Branch-Protected Main / PR Workflow Implications

All v0.2 contract, design, and (eventually) implementation phases
continue through the same governed PCAE lifecycle used throughout v0.1
and 106M, on a branch-protected `main` (1 required approving PR review,
stale-review dismissal, force-push/deletion blocked, conversation
resolution required, admin enforcement currently off transitionally —
106M). This contract does not change branch protection. Per
`docs/V0_2_AUTONOMY_ROADMAP.md`, Phase 107D is dedicated to designing what
the governed lifecycle's final push step becomes if/when
`enforce_admins: true` is ever adopted; this contract assumes that design
work happens before any execution-capable code is merged, not
concurrently with it.

## Explicit Out-of-Scope Items (This Contract and This Phase)

- Runtime enforcement implementation.
- Autonomous execution of any kind.
- Shell mediation or subprocess mediation implementation.
- Real backend invocation implementation.
- Adapter execution implementation.
- Telegram inbound, polling, or remote command reception (outbound-only
  remains the design; RE-NOGO-013).
- Durable audit storage implementation.
- Rollback execution implementation.
- Emergency stop implementation.
- An execution enablement flag/toggle in code.
- Automatic apply or patch execution.
- Any change to `v0.1.0-rc1`, its GitHub Release, or branch protection on
  `main`.

## Architectural Invariants

These ten invariants are frozen by this phase. They are binding
constraints on every future v0.2 implementation phase (108A onward); no
phase may implement a capability that violates one of these without
first amending this contract through a dedicated, explicit phase.

| ID | Invariant |
|---|---|
| **INV-001** | Execution occurs only through a PCAE-controlled execution boundary. |
| **INV-002** | No executable action is authorized without an active task contract. |
| **INV-003** | Human approval is mandatory before mutating execution. |
| **INV-004** | Permission broker decisions are fail-closed. |
| **INV-005** | Every execution decision produces an audit artifact. |
| **INV-006** | Rollback readiness must exist before execution authorization. |
| **INV-007** | Emergency stop overrides all execution authorization. |
| **INV-008** | Execution capability does not imply execution authorization. |
| **INV-009** | Missing evidence results in denial. |
| **INV-010** | v0.2 Level 3 never permits autonomous execution. |

**INV-008 is the invariant that governs this exact phase and every
subsequent design/implementation phase up to 115A:** building a
capability (e.g., a permission broker implementation in 108A, a shell
mediation prototype in 109B) never, by itself, authorizes that
capability to run. Authorization is always a separate, later, explicit
decision — never an automatic consequence of a capability existing.

## Canonical Execution Lifecycle

Every mediated action, once v0.2 execution eventually exists, moves
through exactly these states, in this order (a state may terminate at
`FAILED` or `ABORTED` from any point after `AUTHORIZED`):

```
PLANNED
  -> READY
       -> AWAITING_HUMAN_APPROVAL
            -> AUTHORIZED
                 -> EXECUTING
                      -> COMPLETED
                      -> FAILED
                      -> ABORTED
```

| State | Meaning |
|---|---|
| `PLANNED` | An action has been proposed but not yet validated against contracts/evidence. |
| `READY` | The action has passed preflight validation (task contract, no-go registry) and is eligible for a broker decision. |
| `AWAITING_HUMAN_APPROVAL` | The permission broker returned `allow` or `human_review`, and the system is waiting for an explicit human approval action. |
| `AUTHORIZED` | A human has explicitly approved the action; rollback readiness and audit-artifact creation have both been confirmed. |
| `EXECUTING` | The action is running through the mediated execution boundary. |
| `COMPLETED` | The action finished successfully; a completion audit artifact exists. |
| `FAILED` | The action did not complete successfully; a failure audit artifact exists. |
| `ABORTED` | The action was halted by the emergency stop mechanism before or during execution; an abort audit artifact exists. |

No action may skip a state in this lifecycle. No action may reach
`EXECUTING` without having passed through `AUTHORIZED`, and no action may
reach `AUTHORIZED` without an explicit human approval recorded at
`AWAITING_HUMAN_APPROVAL`.

## Components

For each component: **Purpose**, **Responsibilities**, **Current
Status**.

### Permission Broker

- **Purpose:** Decide, for any proposed action, whether it is `allow`,
  `deny`, or `human_review`.
- **Responsibilities:** Evaluate task-contract scope, no-go registry
  entries, and available evidence; return a fail-closed decision;
  produce a decision record.
- **Current Status:** **Not implemented.** A simulation/prototype exists
  (Phases 87–91: `docs/PHASE_87_PERMISSION_BROKER_ARCHITECTURE.md`,
  `docs/PHASE_88_PERMISSION_BROKER_PROTOTYPE.md`,
  `docs/PHASE_91_PERMISSION_BROKER_SIMULATION_PROTOTYPE.md`), but it does
  not gate any real action. Real implementation is Phase 108A.

### Execution Boundary

- **Purpose:** The single code path through which any mediated action
  may actually run.
- **Responsibilities:** Enforce that no action reaches `EXECUTING` without
  a valid `AUTHORIZED` state; enforce INV-001 and INV-002.
- **Current Status:** **Not implemented.** No execution boundary exists
  in this codebase today; PCAE has no code path that executes
  agent-authored commands or invokes a real backend.

### Human Approval Gate

- **Purpose:** Require and record an explicit human approval before an
  action can move from `AWAITING_HUMAN_APPROVAL` to `AUTHORIZED`.
- **Responsibilities:** Present the proposed action clearly; capture an
  unambiguous approve/deny decision from a human; refuse to infer
  approval from silence, timeout, or any automated signal.
- **Current Status:** **Not implemented.** Enforcement of this gate is
  Phase 111A.

### Shell/Subprocess/Network Boundary

- **Purpose:** Mediate every shell command, subprocess invocation, or
  network call that is part of a mediated execution action.
- **Responsibilities:** Intercept and evaluate the command/call against
  the permission broker's decision; log it to the audit boundary; refuse
  anything not explicitly authorized.
- **Current Status:** **Not implemented.** The narrow shell gate
  (Phases 87–95) is a prototype with an audit evidence model, not an
  enforced gate. Design is Phase 109A; prototype (disabled by default)
  is 109B; hardening is 109C.

### Backend Invocation Boundary

- **Purpose:** Mediate any real AI backend call PCAE itself makes.
- **Responsibilities:** Route backend calls through the permission broker
  decision and human approval gate; no direct, unmediated backend call
  path.
- **Current Status:** **Not implemented.** No real backend invocation
  exists anywhere in this codebase (RE-NOGO-003). Implementation
  (disabled by default) is Phase 110A.

### Adapter Invocation Boundary

- **Purpose:** Mediate any adapter execution (e.g., a runtime adapter
  acting on PCAE's behalf).
- **Responsibilities:** Same mediation guarantee as the backend boundary,
  scoped to adapter execution specifically.
- **Current Status:** **Not implemented.** Adapter design docs are
  evidence-only (RE-NOGO-004). Implementation (disabled by default) is
  Phase 110B.

### Audit Boundary

- **Purpose:** Produce a durable, queryable audit artifact for every
  execution decision and lifecycle-state transition.
- **Responsibilities:** Persist decisions and transitions in a form that
  survives process restart; make them queryable; never silently drop a
  record.
- **Current Status:** **Not implemented.** Current evidence (Markdown/JSON
  phase-completion reports) is v0.1's non-execution-track mechanism and
  is not durable execution audit persistence (RE-NOGO-009).
  Implementation is Phase 112A.

### Rollback Readiness Boundary

- **Purpose:** Confirm a concrete, validated rollback plan exists for a
  specific action *before* that action can be authorized.
- **Responsibilities:** Block authorization if no rollback plan exists;
  validate that the plan is specific to the action, not generic.
- **Current Status:** **Not implemented.** Rollback/promote commands
  referenced in `docs/RELEASE_HANDOFF_V0_1_RC1.md`'s "v0.2 Autonomy
  Boundary" note are evidence-only design tracks. Design is Phase 113A;
  this remains design-only, not rollback execution.

### Emergency Stop Boundary

- **Purpose:** Halt an in-progress mediated execution at any point,
  overriding any prior authorization.
- **Responsibilities:** Be reachable and effective regardless of the
  current lifecycle state; produce an `ABORTED` audit artifact.
- **Current Status:** **Not implemented.** No abort mechanism exists
  today (RE-NOGO-015). Implementation is Phase 114A.

### Execution Enablement Model

- **Purpose:** Gate whether execution is possible at all, independent of
  any single action's authorization.
- **Responsibilities:** Default off; require explicit, documented,
  reversible human action to enable; must not be inferable or
  automatically toggled.
- **Current Status:** **Not implemented — future, default-off by
  design.** No such flag/toggle exists in the codebase today
  (RE-NOGO-010). This contract fixes its required shape; a future phase
  (after 111A–114A are complete) will implement it.

### No-Go Registry

- **Purpose:** Canonical, stable reference for execution-blocking no-go
  conditions.
- **Responsibilities:** Provide stable IDs (`RE-NOGO-NNN`) other phases
  reference instead of restating prose.
- **Current Status:** **Implemented and frozen** (Phase 104B).
  `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`, 17 entries. This contract
  is additive to it, not a replacement (Phase 107C will formally freeze
  the *execution readiness* no-go gate built on top of this registry).

### PR / Branch Protection Workflow

- **Purpose:** Ensure every v0.2 phase's changes reach `main` through the
  governed lifecycle, respecting GitHub branch protection.
- **Responsibilities:** Preserve PR-first workflow for non-admin
  contributors; keep the governed `pcae push` path working for the
  admin operator during the transitional (`enforce_admins: false`)
  period; design a PR-compatible replacement before that period ends.
- **Current Status:** **Implemented for v0.1/106M state; not yet
  adapted for a future `enforce_admins: true` world.** Branch protection
  itself (106M) is live and unchanged. The adaptation design is Phase
  107D.

## Recommended Next Phase

**107C — Execution Readiness No-Go Gate Freeze.** Freeze the execution
readiness no-go gate model (building on the existing frozen
`docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` and this contract's
architectural invariants and lifecycle) before any enforcement
implementation begins in 108A.
