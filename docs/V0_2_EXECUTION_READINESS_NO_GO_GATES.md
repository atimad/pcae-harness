# PCAE v0.2 Execution Readiness No-Go Gates

**Frozen by**: Phase 107C | **Status**: contract/freeze only — no runtime enforcement of these gates is implemented by this document or this phase.

## Purpose

Freeze the canonical no-go gates (`NG-001` through `NG-025`) that must
block any future execution attempt, before any enforcement or execution
implementation begins (Phase 108A onward). This document does not
implement runtime enforcement, autonomous execution, shell/subprocess
mediation, backend invocation, adapter execution, Telegram inbound,
durable audit storage, rollback execution, an emergency stop mechanism,
an execution enablement flag/toggle, automatic apply, patch execution, or
no-go gate runtime enforcement itself. Execution remains unavailable now.

## Relationship to Existing Frozen Artifacts

This document is **additive to, not a replacement for**:

- `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` (Phase 104B, `RE-NOGO-001`
  through `RE-NOGO-017`) — the existing frozen registry of
  execution-blocking conditions.
- `docs/V0_2_AUTONOMY_CONTRACT.md` (Phase 107B) — the ten architectural
  invariants (`INV-001`–`INV-010`), the canonical execution lifecycle, and
  the twelve components.

Where an `NG-` gate corresponds to an existing `RE-NOGO-` entry, this
document references it rather than duplicating its prose. `NG-` gates
are scoped specifically to the *execution readiness* decision point —
the moment just before a proposed action would move from `READY` to
`AWAITING_HUMAN_APPROVAL` in the execution lifecycle — whereas
`RE-NOGO-` entries describe broader runtime-enforcement-stack conditions.

## Hard Rule: Fail-Closed

**Missing evidence, ambiguity, an unavailable permission broker, an
unavailable audit boundary, an unavailable rollback-readiness boundary,
or an unavailable execution boundary must fail closed.** In every one of
these cases, the correct outcome is `deny` (or blocking the transition to
the next lifecycle state), never `allow`. This mirrors and restates
`INV-004` ("Permission broker decisions are fail-closed") and `INV-009`
("Missing evidence results in denial") from
`docs/V0_2_AUTONOMY_CONTRACT.md`; it is not a new invariant, but a
restatement scoped to how the no-go gates below must behave once they
are eventually enforced.

## Gate Field Schema

Each gate below is defined with exactly these fields:

- **ID** — stable identifier, `NG-NNN`.
- **Name** — short human-readable name.
- **Condition** — the precise condition that triggers this gate.
- **Rationale** — why this condition must block execution.
- **Required Remediation** — what must happen before the gate can clear.
- **Recoverable** — whether the condition can be resolved and the gate
  re-evaluated (`yes`) or whether it represents a terminal block for that
  action (`no`).
- **Human Override Allowed** — whether a human can override this gate.
  **Default is `no` for every gate in this document**, per this phase's
  operating rule; any future exception requires an explicit, separate,
  documented decision — none is granted here.
- **Related Invariant** — the `INV-NNN` from
  `docs/V0_2_AUTONOMY_CONTRACT.md` this gate enforces.
- **Related Component** — the component from
  `docs/V0_2_AUTONOMY_CONTRACT.md`'s "Components" section responsible for
  evaluating or clearing this gate.
- **Current Implementation Status** — always **not enforced / future**
  in this document; no gate here is runtime-enforced by this phase.

## Gates

### NG-001 — Missing Active Task Contract

- **Condition:** No active PCAE task contract exists for the agent/
  session attempting the action.
- **Rationale:** `INV-002` requires an active task contract to authorize
  any executable action; without one, there is no declared scope to
  validate against.
- **Required Remediation:** Create and activate a task contract
  (`pcae task new`) before the action can be re-evaluated.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-002.
- **Related Component:** Execution Boundary (COMP-002).
- **Current Implementation Status:** not enforced / future.

### NG-002 — Task Scope Does Not Authorize Action

- **Condition:** An active task contract exists, but the proposed
  action falls outside its allowed files/zones/dependencies.
- **Rationale:** `INV-002` requires the active task contract to actually
  authorize the specific action, not merely exist.
- **Required Remediation:** Narrow the action to fit the existing
  contract, or update the contract's allowed scope through the governed
  task-update path before re-attempting.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-002.
- **Related Component:** Execution Boundary (COMP-002).
- **Current Implementation Status:** not enforced / future.

### NG-003 — Phase State Invalid

- **Condition:** The current phase/task lifecycle state (as tracked by
  PCAE's existing task/phase governance) is inconsistent, stale, or does
  not support the proposed action (e.g., attempting to execute against a
  completed or superseded phase).
- **Rationale:** Execution against an invalid phase state risks acting on
  stale intent or duplicating already-completed work.
- **Required Remediation:** Resolve the phase-state inconsistency via
  existing governed commands (`pcae check`, `pcae task show`) before
  re-attempting.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-002.
- **Related Component:** Execution Boundary (COMP-002).
- **Current Implementation Status:** not enforced / future.

### NG-004 — `pcae health` Not Healthy

- **Condition:** `pcae health` reports a status other than healthy
  (active or idle).
- **Rationale:** An unhealthy repository state is itself evidence the
  environment cannot be trusted to evaluate or carry out an action
  safely; `INV-009` requires missing/invalid evidence to result in
  denial.
- **Required Remediation:** Resolve the health failure and re-run `pcae
  health` until it passes.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-009.
- **Related Component:** Permission Broker (COMP-001).
- **Current Implementation Status:** not enforced / future.

### NG-005 — `pcae check` Not Passed

- **Condition:** `pcae check` reports violations.
- **Rationale:** Same as NG-004 — a failing governance check is missing/
  invalid evidence of a safe-to-act state.
- **Required Remediation:** Resolve the reported violations and re-run
  `pcae check` until it passes.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-009.
- **Related Component:** Permission Broker (COMP-001).
- **Current Implementation Status:** not enforced / future.

### NG-006 — Task-Memory Not Clean

- **Condition:** `pcae doctor task-memory` reports inconsistencies.
- **Rationale:** Stale or inconsistent task-memory state undermines
  confidence that the declared active-task evidence (NG-001/NG-002) is
  accurate.
- **Required Remediation:** Resolve reported task-memory inconsistencies
  and re-run `pcae doctor task-memory` until clean.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-009.
- **Related Component:** Permission Broker (COMP-001).
- **Current Implementation Status:** not enforced / future.

### NG-007 — Push-Check Not Clean

- **Condition:** `pcae push check` does not report a ready/clean state.
- **Rationale:** An action that depends on a clean, pushable repository
  state cannot be trusted to proceed if that precondition doesn't hold —
  `INV-009` treats this as missing evidence.
- **Required Remediation:** Resolve the reported push-check blockers and
  re-run `pcae push check` until clean.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-009.
- **Related Component:** Permission Broker (COMP-001).
- **Current Implementation Status:** not enforced / future.

### NG-008 — Missing Human Approval

- **Condition:** The action has reached `AWAITING_HUMAN_APPROVAL` but no
  explicit, affirmative human approval has been recorded.
- **Rationale:** `INV-003` makes human approval mandatory before any
  mutating execution; absence of approval is not equivalent to approval.
- **Required Remediation:** Obtain and record an explicit human approval
  action before the action can move to `AUTHORIZED`.
- **Recoverable:** yes.
- **Human Override Allowed:** no (approval itself is the human action;
  there is no "override" of the requirement to have one).
- **Related Invariant:** INV-003.
- **Related Component:** Human Approval Gate (COMP-003).
- **Current Implementation Status:** not enforced / future.

### NG-009 — Permission Broker Unavailable

- **Condition:** The permission broker cannot be reached or cannot
  produce a decision.
- **Rationale:** `INV-004` requires fail-closed behavior; an unavailable
  broker cannot have produced an `allow`, so the only safe outcome is
  denial.
- **Required Remediation:** Restore permission broker availability, then
  re-submit the action for evaluation.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-004.
- **Related Component:** Permission Broker (COMP-001).
- **Current Implementation Status:** not enforced / future.

### NG-010 — Permission Broker Denial

- **Condition:** The permission broker explicitly returns `deny` for the
  proposed action.
- **Rationale:** A `deny` decision is authoritative; nothing downstream
  may override it.
- **Required Remediation:** Revise the proposed action so it no longer
  triggers denial, then re-submit for a fresh decision.
- **Recoverable:** yes (for a revised action); no (for the original,
  denied action as submitted).
- **Human Override Allowed:** no.
- **Related Invariant:** INV-004.
- **Related Component:** Permission Broker (COMP-001).
- **Current Implementation Status:** not enforced / future.

### NG-011 — Permission Broker Uncertainty

- **Condition:** The permission broker cannot confidently resolve
  `allow` or `deny` and would otherwise return an ambiguous or
  low-confidence result.
- **Rationale:** `INV-004`'s fail-closed requirement means uncertainty
  must resolve toward `human_review`/denial, never toward `allow` by
  default.
- **Required Remediation:** Route to `human_review`; a human must resolve
  the ambiguity explicitly before the action can proceed.
- **Recoverable:** yes.
- **Human Override Allowed:** no (the human's `human_review` decision
  *is* the resolution path, not an override of this gate).
- **Related Invariant:** INV-004.
- **Related Component:** Permission Broker (COMP-001).
- **Current Implementation Status:** not enforced / future.

### NG-012 — Rollback Readiness Missing

- **Condition:** No concrete, validated rollback plan exists for the
  specific proposed action.
- **Rationale:** `INV-006` requires rollback readiness to exist *before*
  execution authorization — it is a precondition, not a follow-up.
- **Required Remediation:** Produce and validate a rollback plan specific
  to this action before authorization can be granted.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-006.
- **Related Component:** Rollback Readiness Boundary (COMP-008).
- **Current Implementation Status:** not enforced / future.

### NG-013 — Audit Readiness Missing

- **Condition:** The audit boundary cannot confirm it will be able to
  produce a durable audit artifact for this action.
- **Rationale:** `INV-005` requires every execution decision to produce
  an audit artifact; if audit readiness cannot be confirmed in advance,
  proceeding would risk an unaudited action.
- **Required Remediation:** Restore audit boundary availability/
  readiness before re-attempting.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-005.
- **Related Component:** Audit Boundary (COMP-007).
- **Current Implementation Status:** not enforced / future.

### NG-014 — Emergency Stop Active

- **Condition:** The emergency stop/abort mechanism has been triggered
  (globally or for the relevant scope) and has not been explicitly
  cleared.
- **Rationale:** `INV-007` states emergency stop overrides all execution
  authorization — an active stop condition must block every subsequent
  action, not just the one in flight when it was triggered.
- **Required Remediation:** A human must explicitly clear the emergency
  stop condition through a dedicated, auditable action before any new
  action may proceed.
- **Recoverable:** yes (once explicitly cleared).
- **Human Override Allowed:** no (clearing the stop is itself a
  deliberate human action, not an "override" of the block while it's
  active).
- **Related Invariant:** INV-007.
- **Related Component:** Emergency Stop Boundary (COMP-009).
- **Current Implementation Status:** not enforced / future.

### NG-015 — Unsupported Execution Class

- **Condition:** The proposed action belongs to a class of execution the
  execution boundary does not yet support/recognize.
- **Rationale:** `INV-001` requires execution to occur only through a
  PCAE-controlled execution boundary; an unrecognized execution class
  cannot be safely routed through that boundary.
- **Required Remediation:** Define and implement explicit support for the
  execution class (a dedicated future phase), or reclassify the action
  under an already-supported class.
- **Recoverable:** no (for this action as classified); yes (after the
  execution class is explicitly added in a future phase).
- **Human Override Allowed:** no.
- **Related Invariant:** INV-001.
- **Related Component:** Execution Boundary (COMP-002).
- **Current Implementation Status:** not enforced / future.

### NG-016 — Unknown Shell/Subprocess/Network Action

- **Condition:** A shell command, subprocess invocation, or network call
  is proposed that the Shell/Subprocess/Network Boundary does not
  recognize or has no policy for.
- **Rationale:** An unrecognized action cannot be evaluated against a
  policy that doesn't cover it; per the fail-closed rule, absence of a
  known policy is treated as missing evidence.
- **Required Remediation:** Define explicit policy coverage for the
  action class before it can be attempted.
- **Recoverable:** yes (after policy coverage is added).
- **Human Override Allowed:** no.
- **Related Invariant:** INV-001.
- **Related Component:** Shell/Subprocess/Network Boundary (COMP-004).
- **Current Implementation Status:** not enforced / future.

### NG-017 — Unknown Backend

- **Condition:** A real AI backend call is proposed to a backend the
  Backend Invocation Boundary does not recognize or has no policy for.
- **Rationale:** Same reasoning as NG-016, scoped to backend invocation.
- **Required Remediation:** Define explicit policy coverage for the
  backend before it can be invoked.
- **Recoverable:** yes (after policy coverage is added).
- **Human Override Allowed:** no.
- **Related Invariant:** INV-001.
- **Related Component:** Backend Invocation Boundary (COMP-005).
- **Current Implementation Status:** not enforced / future.

### NG-018 — Unknown Adapter

- **Condition:** An adapter execution is proposed for an adapter the
  Adapter Invocation Boundary does not recognize or has no policy for.
- **Rationale:** Same reasoning as NG-016/NG-017, scoped to adapter
  execution.
- **Required Remediation:** Define explicit policy coverage for the
  adapter before it can be invoked.
- **Recoverable:** yes (after policy coverage is added).
- **Human Override Allowed:** no.
- **Related Invariant:** INV-001.
- **Related Component:** Adapter Invocation Boundary (COMP-006).
- **Current Implementation Status:** not enforced / future.

### NG-019 — Protected Branch / PR Policy Conflict

- **Condition:** The proposed action would conflict with GitHub branch
  protection or the PR-first contribution workflow on `main` (e.g., it
  would require a direct push that protection now disallows for a
  non-admin, or it would attempt to bypass required review).
- **Rationale:** Branch protection (106M) is a GitHub-level repository-
  authority control that sits above PCAE's own governance; PCAE must
  never attempt to route around it.
- **Required Remediation:** Route the change through the PR-first
  workflow (`docs/CONTRIBUTOR_WORKFLOW.md`) instead of attempting a
  direct push; if `enforce_admins` is ever turned on, use the
  PR-compatible workflow designed in Phase 107D instead of any bypass.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-001.
- **Related Component:** PR / Branch Protection Workflow.
- **Current Implementation Status:** not enforced / future (branch
  protection itself is live per 106M; this gate's *automatic* detection
  and blocking is not yet implemented).

### NG-020 — No-Go Registry Mismatch

- **Condition:** The proposed action's evaluation contradicts an entry in
  the frozen `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`
  (`RE-NOGO-001`–`RE-NOGO-017`) or in this document's own gates, or two
  evaluations of the same action produce different registry-based
  outcomes.
- **Rationale:** The no-go registry is meant to be a single, stable
  source of truth; a mismatch means something in the evaluation path is
  inconsistent with frozen contract.
- **Required Remediation:** Resolve the inconsistency (fix the evaluator,
  not the registry) before re-attempting; if the registry itself needs to
  change, that requires a dedicated, explicit amendment phase, not an
  ad-hoc override.
- **Recoverable:** yes (after the inconsistency is fixed).
- **Human Override Allowed:** no.
- **Related Invariant:** INV-009.
- **Related Component:** No-Go Registry.
- **Current Implementation Status:** not enforced / future.

### NG-021 — Execution Enablement Unavailable/Default-Off

- **Condition:** The (future) execution enablement flag/toggle is off, or
  does not exist yet.
- **Rationale:** `INV-010` requires v0.2 Level 3 to never permit
  autonomous execution, and the roadmap/contract require execution
  enablement to default off; if it's off (or absent), no execution may
  proceed regardless of any other gate's outcome.
- **Required Remediation:** An explicit, documented, reversible human
  action to enable execution — not performed by this phase or any prior
  phase; no such flag exists in the codebase today.
- **Recoverable:** yes (once the flag exists and is explicitly enabled by
  a human, in a future phase).
- **Human Override Allowed:** no (enabling it is the designed path, not
  an "override" of this gate).
- **Related Invariant:** INV-010.
- **Related Component:** Execution Enablement Model (COMP-010).
- **Current Implementation Status:** not enforced / future (there is
  currently no flag to check; its absence itself satisfies this gate's
  fail-closed condition).

### NG-022 — Telegram Inbound/Out-of-Band Command Attempted

- **Condition:** Any inbound Telegram message, poll response, or other
  out-of-band channel is used, or attempted to be used, to trigger,
  approve, or influence an execution decision.
- **Rationale:** Telegram remains outbound-only by design
  (`RE-NOGO-013`); no inbound command-reception path exists or is
  permitted to influence execution.
- **Required Remediation:** None — this is a hard, structural block, not
  a remediable condition, until (and unless) a dedicated, separately
  gated future phase explicitly adds and reviews an inbound capability.
- **Recoverable:** no (for this contract's scope).
- **Human Override Allowed:** no.
- **Related Invariant:** INV-001.
- **Related Component:** Execution Boundary (COMP-002).
- **Current Implementation Status:** not enforced / future (there is
  categorically no inbound handler in `core/notifications.py` today;
  this gate documents the requirement that none be added without a
  dedicated phase).

### NG-023 — Missing Evidence

- **Condition:** Any input required to evaluate an action (task contract,
  health/check state, broker decision, audit confirmation, rollback
  plan, etc.) is absent, corrupted, or unverifiable.
- **Rationale:** `INV-009` — missing evidence results in denial, as a
  general catch-all beneath the more specific gates above.
- **Required Remediation:** Supply or restore the missing evidence, then
  re-evaluate.
- **Recoverable:** yes.
- **Human Override Allowed:** no.
- **Related Invariant:** INV-009.
- **Related Component:** Permission Broker (COMP-001).
- **Current Implementation Status:** not enforced / future.

### NG-024 — Policy Ambiguity

- **Condition:** Two or more applicable policies (task contract, no-go
  registry, this document's gates, branch protection) produce
  conflicting or ambiguous guidance for the same proposed action.
- **Rationale:** `INV-004`'s fail-closed requirement extends to policy
  conflicts — ambiguity must resolve toward denial, not toward whichever
  policy happens to be evaluated last or most permissively.
- **Required Remediation:** Resolve the policy conflict explicitly
  (amend the conflicting policy through its own governed process) before
  re-attempting.
- **Recoverable:** yes (after the conflict is resolved).
- **Human Override Allowed:** no.
- **Related Invariant:** INV-004.
- **Related Component:** Permission Broker (COMP-001).
- **Current Implementation Status:** not enforced / future.

### NG-025 — Execution Boundary Unavailable

- **Condition:** The execution boundary component itself is unavailable,
  uninitialized, or cannot be verified to be the actual code path an
  action would run through.
- **Rationale:** `INV-001` requires execution to occur only through a
  PCAE-controlled execution boundary; if that boundary cannot be
  confirmed available, no action may proceed, per the fail-closed rule
  for unavailable boundaries.
- **Required Remediation:** Restore/verify the execution boundary before
  any action can be attempted. (Today, no execution boundary exists at
  all — this gate is unconditionally active by construction.)
- **Recoverable:** yes (once the execution boundary exists and is
  verified, in a future phase).
- **Human Override Allowed:** no.
- **Related Invariant:** INV-001.
- **Related Component:** Execution Boundary (COMP-002).
- **Current Implementation Status:** not enforced / future.
- **Canonical-statement annotation (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 —
  N-16-3; additive, parallels the RE No-Go Registry schema-1.1 V-13-3-2
  annotation precedent — schema, blocking verdict, and human-override posture
  are unchanged):** NG-025 is unconditionally active for every non-simulation
  request **except the single trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1`
  execution profile** defined by PBRD-001 v3.0 §12a and PBNDE-001 v1.0. That
  profile is **productionally unsatisfiable** pending N-16-4..7 (the N-16-6
  supply-chain admission binding has no admitting implementation), so no
  production request ever escapes this gate. POL-005 retains its policy ID
  and continues to hard-DENY every other non-simulation request. Human
  override remains `no`.

## Gate Index

| ID | Name | Related Invariant | Related Component | Component ID |
|---|---|---|---|---|
| NG-001 | Missing active task contract | INV-002 | Execution Boundary | COMP-002 |
| NG-002 | Task scope does not authorize action | INV-002 | Execution Boundary | COMP-002 |
| NG-003 | Phase state invalid | INV-002 | Execution Boundary | COMP-002 |
| NG-004 | `pcae health` not healthy | INV-009 | Permission Broker | COMP-001 |
| NG-005 | `pcae check` not passed | INV-009 | Permission Broker | COMP-001 |
| NG-006 | Task-memory not clean | INV-009 | Permission Broker | COMP-001 |
| NG-007 | Push-check not clean | INV-009 | Permission Broker | COMP-001 |
| NG-008 | Missing human approval | INV-003 | Human Approval Gate | COMP-003 |
| NG-009 | Permission broker unavailable | INV-004 | Permission Broker | COMP-001 |
| NG-010 | Permission broker denial | INV-004 | Permission Broker | COMP-001 |
| NG-011 | Permission broker uncertainty | INV-004 | Permission Broker | COMP-001 |
| NG-012 | Rollback readiness missing | INV-006 | Rollback Readiness Boundary | COMP-008 |
| NG-013 | Audit readiness missing | INV-005 | Audit Boundary | COMP-007 |
| NG-014 | Emergency stop active | INV-007 | Emergency Stop Boundary | COMP-009 |
| NG-015 | Unsupported execution class | INV-001 | Execution Boundary | COMP-002 |
| NG-016 | Unknown shell/subprocess/network action | INV-001 | Shell/Subprocess/Network Boundary | COMP-004 |
| NG-017 | Unknown backend | INV-001 | Backend Invocation Boundary | COMP-005 |
| NG-018 | Unknown adapter | INV-001 | Adapter Invocation Boundary | COMP-006 |
| NG-019 | Protected branch / PR policy conflict | INV-001 | PR / Branch Protection Workflow | — |
| NG-020 | No-go registry mismatch | INV-009 | No-Go Registry | — |
| NG-021 | Execution enablement unavailable/default-off | INV-010 | Execution Enablement Model | COMP-010 |
| NG-022 | Telegram inbound/out-of-band command attempted | INV-001 | Execution Boundary | COMP-002 |
| NG-023 | Missing evidence | INV-009 | Permission Broker | COMP-001 |
| NG-024 | Policy ambiguity | INV-004 | Permission Broker | COMP-001 |
| NG-025 | Execution boundary unavailable | INV-001 | Execution Boundary | COMP-002 |

## Default Human-Override Posture

**Human override is `no` for every gate in this document.** This is a
deliberate, uniform default — no gate above grants an exception. Any
future proposal to allow human override of a specific gate requires a
dedicated, explicit contract-amendment phase; it is not something an
implementation phase (108A onward) may introduce incidentally.

## Recommended Next Phase

**107D — PR-Compatible Governed Development Workflow Design.** Design
what the governed PCAE lifecycle's final push step becomes if/when
GitHub branch protection's `enforce_admins` is turned on, before any
enforcement implementation (108A) begins — per `NG-019`'s remediation
path and `docs/V0_2_AUTONOMY_ROADMAP.md`'s staged sequence.
