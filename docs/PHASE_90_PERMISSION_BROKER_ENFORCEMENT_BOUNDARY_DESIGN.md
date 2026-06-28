# Phase 90A — Permission Broker Enforcement Boundary Design

```
phase_name    = phase_90a_permission_broker_enforcement_boundary_design
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 90B — Full-Suite Baseline Inspection and Scope/Preflight Repair
```

## 1. Purpose

Define the boundary between the existing permission broker / advisory / shell-gate / dry-run simulation layers and any future enforcement path. Establish what the permission broker may decide, what it may not decide, where enforcement boundaries would sit, what inputs/outputs are stable, what audit/rollback/approval evidence is required, and what must remain simulation-only until readiness gates are satisfied.

This is a **design-only boundary phase**. No implementation, enforcement, blocking, or interception is performed in 90A.

## 2. Scope

In scope (design only):

- Define the permission broker enforcement boundary
- Define what remains advisory-only
- Define what remains dry-run simulation-only
- Define what the broker may decide in future enforcement
- Define what the broker must never decide alone
- Define hard-block, human-review, accepted-risk, operator-approval, audit-event, rollback-evidence, and readiness-gate ownership
- Define command parsing, shell-gate, and backend invocation boundaries
- Define failure-mode behavior
- Define inputs/outputs for a future enforcement broker decision
- Define no-go conditions before implementation
- Record the known full-suite baseline issue and 90B repair plan
- Recommend the next phase

Out of scope:

- Implementing enforcement, blocking, shell interception, shell wrappers
- Modifying shell configuration
- Executing requested command text, invoking backends, sending prompts
- Capturing outputs, performing intake/adoption
- Granting real authorization
- Persisting advisory/broker/shell-gate/dry-run/enforcement state
- Adding persistent cache
- Allowing human approval or accepted risk to override hard blocks
- Changing advisory, shell-gate, permission-broker, dry-run, audit, approval, readiness, or lifecycle behavior
- Repairing full-suite failures
- Raw git commit, raw git push, force push

## 3. Non-Goals

90A must not and does not:

- Implement real enforcement
- Implement real blocking
- Implement shell interception
- Install shell wrappers
- Modify shell configuration
- Execute requested command text
- Invoke backends
- Send prompts
- Capture outputs
- Perform intake/adoption
- Grant real authorization
- Persist advisory/broker/shell-gate/dry-run/enforcement state
- Add persistent cache
- Allow human approval or accepted risk to override hard blocks
- Change advisory, shell-gate, permission-broker, dry-run, audit, approval, readiness, or lifecycle behavior
- Repair full-suite failures
- Raw git commit
- Raw git push
- Force push

## 4. Starting Point from 89L–89N

### 4.1 Completed Batch Summary

| Phase | Name | Type | Key Deliverable |
|-------|------|------|----------------|
| 89L | Enforcement Audit/Rollback Prototype | simulation-only | `enforcement_audit.py`, `enforcement_rollback.py`, 87 tests |
| 89M | Enforcement Approval/Risk Policy Prototype | simulation-only | `enforcement_approval.py`, 62 tests |
| 89N | Enforcement Readiness Evidence Bundle and Gate Status Reporter | simulation-only | `enforcement_readiness.py`, CLI command, 70 tests |

### 4.2 Design Precursors

| Phase | Name | Type | Key Outcomes |
|-------|------|------|-------------|
| 89G | Threat Model & Safety Case | design | 34 threats, 10 safety claims, 20 controls, 10 must-not-proceed |
| 89H | Audit & Rollback Model Design | design | 16 event types, 5 schemas, chain integrity, ~60 test plan |
| 89I | Approval & Risk Policy Design | design | 7 principles, 5 roles, 4 risk levels, hard-block non-overridable |
| 89J | Gate Checklist & Go/No-Go Criteria | design | 69 gates, 8 dimensions, go/no-go matrix |
| 89K | Test Plan & Fixture Design | design | ~304 tests, 13 fixture types, 25 test categories |

### 4.3 Existing Layer Architecture

The current PCAE architecture consists of these layers, each simulation-only:

```
Operator Command
       │
       ▼
┌──────────────────┐
│   Shell Gate     │  Classifies commands (88P), never blocks
│   (classifier)   │  Produces: category, decision, flags
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Permission       │  Aggregates governance evidence (88R)
│ Broker           │  Produces: broker decision, hard_block_present
│ (decision agg)   │  Never executes, never authorizes
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Advisory Mode    │  Wraps broker output in would-* decisions (88X)
│ (presentation)   │  Produces: advisory_decision, operator_message
│                  │  States non-authorization explicitly
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Dry-Run          │  Simulation envelope around advisory (89B–89E)
│ Simulation       │  Produces: simulation_decision, severity
│ (preview)        │  States "simulation only" in every output
└──────────────────┘
```

### 4.4 Simulation-Only Prototype Modules (89L–89N)

```
┌──────────────────────────┐
│ enforcement_audit.py     │  AuditEvent, 16 event types, sub-schemas
│ (data model only)        │  no_execution=True, no_enforcement=True
├──────────────────────────┤
│ enforcement_rollback.py  │  RollbackEvidence, PreMutationSnapshot
│ (data model only)        │  no_execution=True, no_enforcement=True
├──────────────────────────┤
│ enforcement_approval.py  │  ApprovalRecord, AcceptedRiskRecord
│ (data model only)        │  is_authorization=False, hard_block_override=False
├──────────────────────────┤
│ enforcement_readiness.py │  GateStatus, EnforcementReadinessReport
│ (reporter only)          │  enforcement_authorized=False, enforcement_ready=False
└──────────────────────────┘
```

These modules are pure data models and reporters. They do not enforce, block, intercept, execute, invoke, or authorize anything.

## 5. Current Readiness State

### 5.1 Gate Status (from 89N)

| Dimension | Total | Satisfied | Unsatisfied | Conditional | Deferred |
|-----------|-------|-----------|-------------|-------------|----------|
| design | 13 | 6 | 7 | 0 | 0 |
| implementation | 11 | 0 | 10 | 0 | 1 |
| test | 15 | 4 | 11 | 0 | 0 |
| audit | 8 | 1 | 7 | 0 | 0 |
| rollback | 5 | 1 | 4 | 0 | 0 |
| approval | 7 | 6 | 0 | 0 | 1 |
| secret | 5 | 2 | 3 | 0 | 0 |
| bypass | 5 | 0 | 5 | 0 | 0 |
| **Total** | **69** | **20** | **47** | **0** | **2** |

**Enforcement authorized: NO**
**Enforcement ready: NO**

### 5.2 Hard-Block Invariants Preserved

All invariants from 88V §16 and 89G–89N remain intact:

- `no_execution=True` — no command execution
- `no_enforcement=True` — no enforcement applied
- `hard_block_override=False` — accepted risk never overrides hard blocks
- `is_authorization=False` — approval is never authorization
- `enforcement_authorized=False` — enforcement not authorized
- `enforcement_ready=False` — enforcement not ready
- No shell interception, no wrappers, no backend invocation
- No persistent audit database, no persistent authorization state
- No prompt sending, no output capture, no intake/adoption

## 6. Known Full-Suite Baseline Issue

### 6.1 Status After 89N

| Suite | Result |
|-------|--------|
| quick tier | 8767/8768 passed in 250.63s, **1 pre-existing failure** |
| full suite | 9342/9530 passed in 1333.88s, **188 pre-existing scope/preflight idle-state failures** |
| fast-green | 3221/3221 passed |

### 6.2 Characterization

The 188 full-suite failures are **pre-existing** and related to scope/preflight idle-state behavior. They predate the 89L–89N batch and were present at the completion of 89K. They are NOT caused by any 89L–89N prototype code.

### 6.3 Impact on 90A

90A is design-only and proceeds with this known baseline issue. The 188 failures do not affect design boundary definitions.

### 6.4 Required Resolution

A dedicated follow-up phase (90B) must inspect and repair/classify these 188 failures before any 90-series implementation or prototype begins. See §27.

## 7. Boundary Principles

### 7.1 Core Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| **BP-1** | **The broker decides; it does not enforce.** | The permission broker's role is to aggregate evidence and produce a decision. Turning that decision into enforcement (blocking, allowing, gating) is a separate concern owned by a future enforcement executor. |
| **BP-2** | **Advisory/simulation output is never enforcement.** | Every output from advisory and dry-run simulation states non-authorization. This distinction must survive into any enforcement design. |
| **BP-3** | **Hard blocks are non-overridable by any actor.** | 88V §16 permanent invariant. No human, no approval, no accepted risk, no operator override can bypass a hard block. |
| **BP-4** | **The shell gate classifies; the broker judges.** | Shell gate is a classifier (category, flags, initial decision). The broker is the judge that weighs all evidence (shell gate + scope + health + check + task contract + human factors) and produces the authoritative governance decision. |
| **BP-5** | **Approval is not authorization.** | 89I P1. Human approval records consent. It does not mean PCAE authorizes execution. PCAE never authorizes execution. |
| **BP-6** | **Evidence before enforcement.** | 89G SC-7: PCAE must fail closed when evidence is missing. Every enforcement action must be traceable to the evidence that produced it. |
| **BP-7** | **Rollback before mutation.** | 89H: rollback artifact must be created before any governed mutation. Enforcement without rollback is irreversible. |
| **BP-8** | **Audit every enforcement action.** | 89H: every enforcement decision must produce an auditable, tamper-evident record. Enforcement without audit is unaccountable. |
| **BP-9** | **Fail closed.** | Any uncertainty, missing evidence, contradiction, or internal error must result in blocking the command — never allowing it. |
| **BP-10** | **The operator is always authoritative.** | PCAE governs; the human operator retains ultimate authority. The operator can always disable enforcement, run commands directly in the shell, or override non-hard-block decisions. |

### 7.2 Boundary Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     OPERATOR (always authoritative)               │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  SHELL (bash/zsh/sh)                         │ │
│  │  Operator types commands directly. PCAE never intercepts.   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│         │                                                         │
│         │ Command text (read-only, no execution)                  │
│         ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  SHELL GATE (classifier)                 [simulation-only]   │ │
│  │  _classify_command() → category, flags, initial decision    │ │
│  │  BOUNDARY: classification only, never blocks                │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  PERMISSION BROKER (decision aggregator) [simulation-only]   │ │
│  │  _broker_decide() → broker_decision, hard_block_present     │ │
│  │  BOUNDARY: decision only, never enforces                    │ │
│  │                                                              │ │
│  │  ┌───────────────────────────────────────────────────────┐  │ │
│  │  │  FUTURE ENFORCEMENT BOUNDARY (NOT IMPLEMENTED)         │  │ │
│  │  │                                                        │  │ │
│  │  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │  │ │
│  │  │  │ Enforcement  │  │ Audit Logger │  │ Rollback     │  │  │ │
│  │  │  │ Executor     │  │ (immutable)  │  │ Artifact     │  │  │ │
│  │  │  │ (block/allow │  │              │  │ Creator      │  │  │ │
│  │  │  │ /gate/deny)  │  │              │  │              │  │  │ │
│  │  │  └─────────────┘  └──────────────┘  └──────────────┘  │  │ │
│  │  │                                                        │  │ │
│  │  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │  │ │
│  │  │  │ Approval     │  │ Risk          │  │ Readiness    │  │  │ │
│  │  │  │ Validator    │  │ Validator     │  │ Gate Check   │  │  │ │
│  │  │  └─────────────┘  └──────────────┘  └──────────────┘  │  │ │
│  │  └───────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  ADVISORY MODE (presentation)            [simulation-only]   │ │
│  │  build_advisory() → would-* advisory decision               │ │
│  │  BOUNDARY: presentation only, "would" not "will"            │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  DRY-RUN SIMULATION (preview)            [simulation-only]   │ │
│  │  build_simulation() → simulation_decision, severity         │ │
│  │  BOUNDARY: preview only, "SIMULATED BLOCK" not real block   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## 8. Layer Responsibilities

### 8.1 Shell Gate

| Responsibility | Current State | Future Enforcement |
|---------------|---------------|-------------------|
| Classify command text | ✅ Implemented (88P, 88Q, 89A) | Unchanged |
| Detect hard blocks (force push, destructive fs, etc.) | ✅ Implemented | Unchanged |
| Detect secrets (env vars, secret files) | ✅ Implemented (88V.1) | Unchanged |
| Split compound commands (&&, \|\|, ;, \|) | ✅ Implemented (89A) | Unchanged |
| Classify shell-embedded commands (-c, -lc, eval, source) | ✅ Implemented (89A) | Unchanged |
| Produce initial decision (allow_*, blocked_*, requires_*) | ✅ Implemented | Unchanged |
| **Block commands** | ❌ Not implemented | **Future enforcement executor** |
| **Modify shell behavior** | ❌ Not implemented | **Never — hard boundary** |
| **Install wrappers** | ❌ Not implemented | **Never — hard boundary** |

### 8.2 Permission Broker

| Responsibility | Current State | Future Enforcement |
|---------------|---------------|-------------------|
| Aggregate shell gate evidence | ✅ Implemented (88R) | Unchanged |
| Aggregate scope preflight evidence | ✅ Implemented | Unchanged |
| Aggregate health/check/doctor evidence | ✅ Implemented | Unchanged |
| Detect contradictions in evidence | ✅ Implemented | Unchanged |
| Produce broker decision | ✅ Implemented | Unchanged |
| Determine hard_block_present | ✅ Implemented | Unchanged |
| Collect missing evidence | ✅ Implemented | Unchanged |
| **Enforce broker decision** | ❌ Not implemented | **Future enforcement executor** |
| **Block commands** | ❌ Not implemented | **Future enforcement executor** |
| **Write audit events** | ❌ Not implemented | **Future audit logger** |
| **Create rollback artifacts** | ❌ Not implemented | **Future rollback creator** |
| **Validate approvals** | ❌ Not implemented | **Future approval validator** |
| **Validate accepted risks** | ❌ Not implemented | **Future risk validator** |

### 8.3 Advisory Mode

| Responsibility | Current State | Future Enforcement |
|---------------|---------------|-------------------|
| Map broker decision to would-* advisory | ✅ Implemented (88X) | Unchanged |
| Produce operator messages | ✅ Implemented | Unchanged |
| State non-authorization | ✅ Implemented | Unchanged |
| Recommend next action | ✅ Implemented | Unchanged |
| **Grant authorization** | ❌ Never | **Never — hard boundary** |
| **Change broker decision** | ❌ Never | **Never — hard boundary** |

### 8.4 Dry-Run Simulation

| Responsibility | Current State | Future Enforcement |
|---------------|---------------|-------------------|
| Wrap advisory in simulation envelope | ✅ Implemented (89C) | Unchanged |
| Add severity model | ✅ Implemented | Unchanged |
| Add governed alternatives | ✅ Implemented | Unchanged |
| Add enforcement readiness preview | ✅ Implemented | Unchanged |
| State "simulation only" | ✅ Implemented | Unchanged |
| **Become enforcement** | ❌ Never | **Never — separate path** |

### 8.5 Future Enforcement Executor (not implemented)

The enforcement executor is a **separate component** that consumes the broker decision and applies it. It does not exist today. When implemented:

| Responsibility | Owner |
|---------------|-------|
| Block commands based on broker decision | Enforcement executor |
| Allow commands that pass all checks | Enforcement executor |
| Gate commands for human review | Enforcement executor |
| Deny permanently blocked commands | Enforcement executor |
| Write audit events for every action | Audit logger |
| Create rollback artifacts before mutation | Rollback creator |
| Validate approval records | Approval validator |
| Validate accepted-risk records | Risk validator |
| Check readiness gates | Readiness gate checker |
| Degrade to simulation on audit failure | Enforcement executor |

## 9. Permission Broker Responsibility

### 9.1 What the Broker Decides (Current and Future)

The permission broker is the **central governance decision authority**. It decides:

1. **Whether a command would be blocked** — based on shell gate classification, scope preflight, governance evidence (health, check, doctor, push check, tests), task contract state, contradiction detection, and human factors (review, approval, accepted risk).

2. **Whether a hard block is present** — hard blocks are non-overridable by any actor (88V §16). The broker identifies hard blocks from shell gate decisions and scope preflight denials.

3. **What evidence is missing** — when evidence is insufficient, the broker reports what's missing rather than making an uninformed decision.

4. **Whether human review is required** — for high-risk actions (adoption, backend invocation, rollback, storage write, push, commit), the broker gates on human review.

5. **Whether contradictions exist** — contradictory evidence (e.g., hard block alongside human approval, allow decision for mutating action with read-only shell gate decision) is detected and results in `blocked_by_conflicting_evidence`.

### 9.2 What the Broker Must Never Decide Alone

The broker must never, under any circumstances:

1. **Execute a command** — execution is always the operator's action, never PCAE's.
2. **Grant authorization** — "allow" means "would pass governance checks," not "PCAE authorizes execution."
3. **Override hard blocks** — no evidence, no approval, no accepted risk can override a hard block.
4. **Bypass human review for high-risk actions** — adoption, backend invocation, rollback, storage write, push, and commit always require human review.
5. **Proceed with missing evidence for mutating actions** — mutating actions require health and check evidence.
6. **Proceed with failed governance checks** — failed health, check, doctor, push check, or tests are absolute stops.
7. **Replace the operator's judgment** — the broker provides governance decisions; the operator retains ultimate authority.

### 9.3 Broker Decision Vocabulary (24 values, stable)

The broker's 24 decisions from 88R are the stable interface between governance evaluation and any future enforcement:

```
allow_preflight_only
deny
requires_human_review
requires_more_evidence
blocked_by_scope
blocked_by_backend_policy
blocked_by_mutation_policy
blocked_by_commit_policy
blocked_by_push_policy
blocked_by_lifecycle_state
blocked_by_task_contract
blocked_by_risk
blocked_by_must_never_repeat
blocked_by_failed_check
blocked_by_failed_health
blocked_by_failed_doctor
blocked_by_failed_tests
blocked_by_push_check
blocked_by_raw_git_push
blocked_by_force_push
blocked_by_shell_gate
blocked_by_test_run_lock
blocked_by_conflicting_evidence
unknown
```

### 9.4 Broker Input/Output Contract

**Inputs** (stable, from `build_permission_broker`):

| Input | Type | Required For |
|-------|------|-------------|
| `repo_root` | Path | All decisions |
| `requested_action` | str | Action classification |
| `requested_files` | list[str] | Scope preflight |
| `requested_command` | str | Shell gate classification |
| `health_passed` | bool\|None | Mutating actions |
| `check_passed` | bool\|None | Mutating actions |
| `doctor_passed` | bool\|None | Test execution |
| `push_check_passed` | bool\|None | Push actions |
| `tests_passed` | bool\|None | Test-dependent actions |
| `human_review_present` | bool | High-risk actions |
| `human_approval_present` | bool | Approval-dependent actions |
| `accepted_risk_present` | bool | Risk-dependent actions |

**Outputs** (stable, from broker envelope):

| Output | Type | Always Present |
|--------|------|---------------|
| `broker.decision` | str (24 values) | Yes |
| `broker.hard_block_present` | bool | Yes |
| `broker.reason_codes` | list[str] | Yes |
| `broker.missing_evidence` | list[str] | Yes |
| `shell_gate_evidence.command_category` | str | When command provided |
| `shell_gate_evidence.decision` | str | When command provided |
| `shell_gate_evidence.hard_block_present` | bool | When command provided |
| `shell_gate_evidence.secret_access_detected` | bool | When command provided |
| `scope_preflight.decision` | str | When files provided |
| `evidence_sources` | list[str] | Yes |
| `warnings` | list[str] | Yes |
| `errors` | list[str] | Yes |
| `safety_notes.*` | dict[str, bool] | Yes (all true) |

## 10. Advisory Responsibility

### 10.1 Current Role

The advisory mode (88X) wraps broker output in would-* decisions for human consumption. It is a **presentation layer**, not a decision layer.

### 10.2 What Advisory Does

- Maps broker decisions to would-* advisory decisions (19 values)
- Produces human-readable operator messages
- States non-authorization explicitly
- Recommends next actions
- Tracks performed flags (always false)

### 10.3 What Advisory Must Never Do

- Change the broker's decision
- Grant authorization
- Execute commands
- Override hard blocks
- Become enforcement

### 10.4 Advisory in Future Enforcement

When enforcement is implemented, advisory mode remains unchanged. It continues to present would-* decisions. The enforcement executor consumes the broker decision directly — not the advisory decision. Advisory and enforcement are parallel consumers of the broker, not a chain.

```
Broker Decision
    ├──→ Advisory Mode (would-* for humans)
    └──→ Enforcement Executor (block/allow/gate for real)
```

## 11. Shell Gate Responsibility

### 11.1 Current Role

The shell gate (88P, hardened in 88Q, 89A, 88V.1) is a **command classifier**. It analyzes command text and produces a category, detected flags, and an initial decision.

### 11.2 What Shell Gate Does

- Classifies commands into 24 categories (read_only_inspection through unknown)
- Detects dangerous patterns (force push, destructive filesystem, raw git push/commit, etc.)
- Detects secret patterns in env vars and file paths
- Splits compound commands on operators (&&, ||, ;, |)
- Classifies shell-embedded commands (-c, -lc, eval, source)
- Produces an initial decision (allow_*, blocked_*, requires_*, deny)

### 11.3 What Shell Gate Must Never Do

- Block commands
- Modify shell behavior
- Install wrappers or hooks
- Modify shell configuration files
- Execute any command text
- Invoke subprocesses for classification (pure string analysis)

### 11.4 Shell Gate → Broker Relationship

The shell gate is a **evidence provider** to the broker. The broker treats shell gate hard-block decisions as authoritative but validates them through contradiction detection. The mapping from shell gate decisions to broker decisions is defined in `_SG_HARD_BLOCK_TO_BROKER` (88R).

### 11.5 Shell Gate in Future Enforcement

Shell gate classification remains unchanged. The enforcement executor consumes shell gate evidence through the broker — it does not call shell gate directly.

## 12. Dry-Run Simulation Responsibility

### 12.1 Current Role

Dry-run simulation (89B–89E) provides a **preview** of what enforcement would decide without applying any enforcement. It wraps advisory output in a simulation envelope.

### 12.2 What Simulation Does

- Wraps advisory in simulation-specific envelope
- Adds severity model (info, caution, review_required, blocked)
- Adds governed alternatives (pcae push, pcae commit)
- Adds enforcement readiness preview
- States "simulation only" in every output
- All safety invariants remain true

### 12.3 What Simulation Must Never Do

- Apply real enforcement
- Block commands
- Become enforcement
- Change the broker or advisory decision
- Grant authorization

### 12.4 Simulation as Evidence for Future Enforcement

Simulation decisions are **preview-only**. They demonstrate what enforcement would decide but do not constitute authorization. When enforcement is implemented:

1. Simulation results can be used as **evidence of expected behavior** — showing that the enforcement path matches the simulation path for the same inputs.
2. Simulation remains available as a **dry-run preview** even after enforcement is active — operators can preview enforcement decisions without applying them.
3. Simulation never becomes enforcement — the execution path is separate.

## 13. Audit Responsibility

### 13.1 Current State

The audit event model (`enforcement_audit.py`, 89L) defines pure data structures for audit events. It does not write to disk, does not persist state, and does not enforce anything.

### 13.2 Audit Ownership

Audit is **owned by a future audit logger component**, not by the broker, shell gate, advisory, or simulation layers.

**What audit owns:**

| Responsibility | Description |
|---------------|-------------|
| Event recording | Write an audit event for every enforcement action |
| Chain integrity | Checksum-chain audit records for tamper-evidence |
| Redaction | Never write raw secret text to audit logs |
| Retention | Enforce log rotation and retention policies |
| Degradation trigger | Signal enforcement degradation when audit fails |

**What audit does not own:**

| Non-Responsibility | Owned By |
|-------------------|----------|
| Deciding what to audit | Broker (decides) → Enforcement executor (acts) |
| Deciding whether to block | Broker → Enforcement executor |
| Creating rollback artifacts | Rollback creator |
| Validating approvals | Approval validator |

### 13.3 Audit Boundary

```
Broker Decision → Enforcement Executor → Audit Logger
                                             │
                                             ├── Write audit event
                                             ├── Validate chain integrity
                                             ├── Redact secrets
                                             └── Signal degradation on failure
```

The audit logger is a **consumer** of enforcement actions. It does not influence the decision — it records it. If audit logging fails, enforcement degrades to simulation-only (fail-closed).

## 14. Rollback Responsibility

### 14.1 Current State

The rollback evidence model (`enforcement_rollback.py`, 89L) defines pure data structures for rollback artifacts. It does not create files, does not mutate state, and does not enforce anything.

### 14.2 Rollback Ownership

Rollback is **owned by a future rollback creator component**, separate from the broker and enforcement executor.

**What rollback owns:**

| Responsibility | Description |
|---------------|-------------|
| Pre-mutation snapshot | Capture file state before governed mutation |
| Artifact creation | Create rollback artifact with checksums |
| Artifact validation | Verify artifact integrity before use |
| Restoration | Restore files to pre-mutation state |
| Fallback | Use git reflog when artifacts are corrupted/missing |

**What rollback does not own:**

| Non-Responsibility | Owned By |
|-------------------|----------|
| Deciding when to create artifacts | Enforcement executor |
| Deciding when to rollback | Operator (explicit action) |
| Deciding what mutations are allowed | Broker |

### 14.3 Rollback Boundary

```
Before Mutation:
  Enforcement Executor → Rollback Creator → Create snapshot artifact

After Mutation (if rollback requested):
  Operator → pcae enforcement rollback restore → Rollback Creator → Restore files
```

Rollback is a **safety mechanism**, not a decision authority. It exists to undo mutations, not to decide which mutations are permitted.

## 15. Approval/Risk Responsibility

### 15.1 Current State

The approval and accepted-risk models (`enforcement_approval.py`, 89M) define pure data structures for approval records and accepted-risk records. They do not persist state, do not grant authorization, and do not enforce anything.

### 15.2 Approval/Risk Ownership

Approval and risk validation are **owned by future validators**, separate from the broker.

**What approval/risk owns:**

| Responsibility | Description |
|---------------|-------------|
| Record creation | Create approval/risk records with required fields |
| Expiration enforcement | Reject expired approvals/risks |
| Revocation enforcement | Reject revoked approvals/risks |
| Hard-block refusal | Refuse to apply approval/risk when hard block present |
| Scope validation | Validate approval/risk scope matches command |
| Audit recording | Record approval/risk events in audit log |

**What approval/risk does not own:**

| Non-Responsibility | Owned By |
|-------------------|----------|
| Deciding whether approval is needed | Broker |
| Granting authorization | **Never — hard boundary** |
| Overriding hard blocks | **Never — hard boundary (88V §16)** |

### 15.3 Approval/Risk Boundary

```
Broker Decision: requires_human_review
         │
         ▼
Enforcement Executor → Approval Validator
         │                    │
         │                    ├── Validate approval exists
         │                    ├── Validate not expired/revoked
         │                    ├── Validate hard_block_present=false
         │                    ├── Validate scope matches
         │                    └── Return: valid / invalid
         │
         ▼
    Block or Allow
```

Critical invariant: if `hard_block_present=true`, the approval validator must refuse to validate — the hard block stands regardless of any approval.

## 16. Readiness Reporter Responsibility

### 16.1 Current State

The readiness reporter (`enforcement_readiness.py`, 89N, CLI command) reports gate status without authorizing enforcement. It is purely informational.

### 16.2 Readiness Ownership

Readiness reporting is **owned by the readiness reporter**, which already exists as a simulation-only component.

**What readiness owns:**

| Responsibility | Description |
|---------------|-------------|
| Gate registry | Maintain the 69-gate registry from 89J |
| Gate status tracking | Track SATISFIED/NOT_SATISFIED/CONDITIONAL/DEFERRED |
| Evidence mapping | Map gates to evidence references |
| Report generation | Produce human-readable and JSON reports |
| Authorization status | Report enforcement_authorized and enforcement_ready |

**What readiness does not own:**

| Non-Responsibility | Owned By |
|-------------------|----------|
| Authorizing enforcement | Operator (explicit action) |
| Satisfying gates | Implementation phases (90-series) |
| Changing gate criteria | Design governance phases |

### 16.3 Readiness Gate in Future Enforcement

The readiness reporter is the **gatekeeper** for enforcement implementation. Before any enforcement executor can be activated:

1. All 69 gates must be SATISFIED or DEFERRED with documented rationale
2. `enforcement_ready` must be `true` (all gates satisfied)
3. Operator must explicitly authorize enforcement
4. Readiness report must be generated and reviewed

## 17. Future Enforcement Boundary

### 17.1 Enforcement Executor Design

The enforcement executor is the **future component** that consumes broker decisions and applies enforcement actions. It does not exist today.

### 17.2 What the Enforcement Executor Will Do

| Action | Trigger | Behavior |
|--------|---------|----------|
| **Block** | Broker decision in BPE_HARD_BLOCK_DECISIONS | Refuse to execute; log audit event; suggest governed alternative |
| **Allow (preflight only)** | Broker decision = allow_preflight_only | Allow command to proceed; log audit event; state non-authorization |
| **Gate for review** | Broker decision = requires_human_review | Pause; request human review; log audit event |
| **Request evidence** | Broker decision = requires_more_evidence | Report missing evidence; log audit event |
| **Deny** | Broker decision = deny | Permanently refuse; log audit event; no workaround |

### 17.3 What the Enforcement Executor Must Never Do

- Change the broker's decision
- Override hard blocks
- Bypass human review for high-risk actions
- Proceed with missing evidence
- Proceed with failed governance checks
- Fail open (allow on error)
- Execute commands itself
- Grant authorization

### 17.4 Enforcement State Machine

```
                  ┌──────────┐
                  │ DISABLED │ ←── Default state. No enforcement.
                  └────┬─────┘
                       │ pcae enforcement enable
                       ▼
                  ┌──────────┐
                  │  ENABLED │ ←── Enforcement active.
                  └────┬─────┘
                       │ Audit failure / chain break
                       ▼
                  ┌──────────┐
                  │ DEGRADED │ ←── Enforcement degraded to simulation-only.
                  └────┬─────┘  Audit events still produced (best-effort).
                       │ pcae enforcement disable (any state)
                       ▼
                  ┌──────────┐
                  │ DISABLED │
                  └──────────┘
```

### 17.5 Enforcement Mode Flag

Enforcement is controlled by an explicit flag — never implicit:

- **Per-repository** (`.pcae/enforcement/mode.toml`): `enabled = true/false`
- **Per-session** (environment variable): `PCAE_ENFORCEMENT=1` or session flag
- **Disable always available**: `pcae enforcement disable` works regardless of state
- **Enable requires explicit operator confirmation**

## 18. Broker Decision Input Model

### 18.1 Input Categories

The broker accepts evidence from five categories:

| Category | Sources | Required For |
|----------|---------|-------------|
| **Command evidence** | Shell gate classification, command text (redacted if secrets) | All command evaluations |
| **Scope evidence** | Scope preflight, task contract, allowed/forbidden files | Mutating actions |
| **Governance evidence** | Health, check, doctor, push check, test results | Mutating actions |
| **Human factors** | Human review present, human approval present, accepted risk present | High-risk actions |
| **State evidence** | Active task detection, test run lock, lifecycle state | All evaluations |

### 18.2 Input Validation

Before using any input, the broker validates:

1. Shell gate evidence schema version matches expected (`0.1`)
2. Performed/authorization flags in shell gate evidence are all false
3. No contradiction between shell gate hard block and allow decision
4. No contradiction between flags (force_push_detected) and decision
5. No secret access with unredacted command text
6. No human approval alongside shell gate hard block
7. No accepted risk alongside shell gate hard block

Any validation failure → `blocked_by_conflicting_evidence`.

### 18.3 Input Stability Contract

The broker input model is **stable**. New fields may be added; existing fields will not be removed or change type. This stability contract enables the enforcement executor, audit logger, and other future components to depend on the broker interface without breaking.

## 19. Broker Decision Output Model

### 19.1 Output Categories

The broker produces one of four outcome categories:

| Outcome | Decisions | Meaning |
|---------|-----------|---------|
| **Preflight only** | `allow_preflight_only` | All checks pass; not execution authorization |
| **Gated** | `requires_human_review`, `requires_more_evidence` | Additional input required |
| **Blocked** | `blocked_by_*`, `deny` | Command blocked; reason provided |
| **Unknown** | `unknown` | Insufficient evidence to decide |

### 19.2 Output Stability Contract

The broker output model is **stable**:

- 24 decision values — may add, will not remove or rename
- `hard_block_present` boolean — always present
- `reason_codes` list — machine-readable reasons
- `missing_evidence` list — what's needed before re-evaluation
- `evidence_sources` list — what evidence was consulted
- `warnings` and `errors` lists — non-fatal issues detected

### 19.3 Hard Block Output Properties

When `hard_block_present` is true:

- `overridable` is always false
- `overridden` is always false
- `overridden_by` is always null
- `permanent` is always true
- Human approval cannot change the decision
- Accepted risk cannot change the decision
- The operator is informed: "This is a permanent hard block. No override exists."

## 20. Hard-Block Non-Overridable Model

### 20.1 Permanent Invariant (88V §16)

```
Accepted risk MUST NOT override hard blocks.
Human approval MUST NOT override hard blocks.
No operator, administrator, or automated system MAY override hard blocks.

This is a permanent, non-negotiable safety invariant.
```

### 20.2 Hard Blocks (Exhaustive List)

| Hard Block | Trigger | Source |
|-----------|---------|--------|
| `blocked_by_force_push` | `git push --force`, `-f`, `--force-with-lease`, `+refspec`, `--delete` | Shell gate |
| `blocked_by_destructive_filesystem` | `rm -rf`, `git clean` | Shell gate |
| `blocked_by_policy_forbidden_file` | Write to README.md, docs/REAL_CAPTURED_TASKS.md, docs/LINKEDIN_ARTICLE_DRAFT.md | Shell gate → Broker |
| `blocked_by_history_rewrite` | `git rebase`, `git reset --hard`, `git cherry-pick` | Shell gate |
| `blocked_by_raw_git_push` | `git push` (not via pcae push) | Shell gate |
| `blocked_by_raw_git_commit` | `git commit` (not via pcae commit) | Shell gate |
| `blocked_by_shell_gate` | Shell gate categorical block | Shell gate → Broker |
| `blocked_by_conflicting_evidence` | Contradictory evidence detected | Broker |
| `blocked_by_scope` | Requested files outside task scope | Scope preflight → Broker |
| `blocked_by_task_contract` | No active task for mutating action | Broker |
| `blocked_by_failed_health` | Health check failed | Broker |
| `blocked_by_failed_check` | Governance check failed | Broker |
| `blocked_by_failed_doctor` | Doctor check failed | Broker |
| `blocked_by_failed_tests` | Tests failed | Broker |
| `blocked_by_push_check` | Push readiness check failed | Broker |
| `blocked_by_test_run_lock` | Test run already in progress | Broker |
| `deny` | Shell gate or broker unconditional deny | Shell gate/Broker |

### 20.3 Verification Code Path

Any code that applies human approval or accepted risk must:

```python
if hard_block_present:
    # Refuse to apply approval or accepted risk
    # Log audit event: hard_block_non_overridable
    # Return the hard block decision unchanged
    return original_hard_block_decision
```

This check must be in the enforcement executor, approval validator, and risk validator — three independent code paths that must all refuse to override hard blocks.

## 21. Human-Review Model

### 21.1 When Human Review Is Required

| Action | Human Review Required |
|--------|----------------------|
| Read-only inspection | No |
| Governed lifecycle (pcae health, check, etc.) | No |
| Test execution (pytest) | No |
| Filesystem write within task scope | No (if task active) |
| Governed commit (pcae commit) | Yes |
| Governed push (pcae push) | Yes |
| Backend invocation | Yes |
| Adoption of backend output | Yes |
| Rollback execution | Yes |
| Storage write | Yes |

### 21.2 Human Review Properties

| Property | Value |
|----------|-------|
| Review is explicit | Must be declared; not inferred |
| Review is per-action | Not a blanket approval |
| Review is recorded | Audit event produced |
| Review is not authorization | PCAE never authorizes execution |
| Review cannot override hard blocks | 88V §16 permanent invariant |

### 21.3 Human Review Flow

```
Broker: requires_human_review
    │
    ▼
Enforcement Executor: gate
    │
    ▼
Operator: provides human review evidence
    │
    ▼
Broker (re-evaluate with human_review_present=true)
    │
    ▼
Enforcement Executor: allow (preflight only) or block
```

## 22. Accepted-Risk Model

### 22.1 Risk Levels

| Level | Description | Required for Acceptance | Max Duration |
|-------|-------------|----------------------|-------------|
| **Low** | Read-only command with uncertain classification | Self-acknowledgment | 1 hour |
| **Medium** | Filesystem write in task scope, network access to known endpoint | Self-acknowledgment + active task | 4 hours |
| **High** | Backend invocation, adoption, push, commit | Human review + acknowledgment | 1 hour |
| **Critical** | Hard blocks, force push, destructive fs | **Cannot be accepted** | N/A |

### 22.2 Accepted-Risk Properties

| Property | Value |
|----------|-------|
| Risk description is mandatory | Operator must see what specific risk they're accepting |
| Non-overridable for hard blocks | 88V §16 permanent invariant |
| Auditable | Every risk acceptance recorded |
| Time-bound | Risk acceptance expires |
| Revocable | Risk acceptance can be withdrawn |
| Scoped | Risk acceptance applies to specific command/action |

### 22.3 Accepted-Risk Boundary

Critical distinction: accepted risk is a mechanism for operators to acknowledge known risks and proceed despite them. It is **not** a mechanism to bypass governance rules. The boundary is:

- **Acceptable:** "I know this command accesses the network, and I accept the risk for this specific endpoint."
- **Not acceptable:** "I know this is a force push, but I accept the risk." (Hard block — cannot be accepted.)

## 23. Operator-Approval Model

### 23.1 Approval Roles

| Role | Who | What They Can Approve |
|------|-----|----------------------|
| **Self-Approver** | The operator proposing the action | Read-only commands with uncertain classification (low risk) |
| **Task Owner** | The operator who created the active task | Filesystem writes within task scope (medium risk) |
| **Reviewer** | A different human operator | Backend invocation, network access, adoption (high risk) |
| **Administrator** | Designated PCAE administrator | Enforcement enable/disable, configuration changes (critical) |
| **No One** | No human, no role | Hard blocks — force push, destructive filesystem, policy-forbidden files |

### 23.2 Approval Properties

| Property | Value |
|----------|-------|
| Approval is not authorization (89I P1) | PCAE never authorizes execution |
| Approval is specific (89I P2) | Names the exact command/action |
| Approval is time-bound (89I P3) | Expires; default 5 min to 1 hour depending on scope |
| Approval is revocable (89I P4) | Operator can always revoke |
| Approval is auditable (89I P5) | Every grant, expiration, revocation recorded |
| Approval never overrides hard blocks (89I P6) | 88V §16 permanent invariant |
| Approval requires explicit action (89I P7) | No click-through, no default-yes, no auto-approval |

### 23.3 Approval Scopes

| Scope | Description | Default Expiry |
|-------|-------------|---------------|
| `single_command` | Approval for one specific command (exact text hash) | 5 minutes |
| `command_category` | Approval for commands in a category | 30 minutes |
| `file_set` | Approval for mutations to specific files | 1 hour |
| `task_duration` | Approval valid for the duration of the active task | Task end |
| `session` | Approval valid for the current PCAE session | Session end |

## 24. Audit/Rollback Evidence Model

### 24.1 Evidence Chain

Every enforcement action must be traceable through:

```
command_text → shell_gate classification → broker decision
  → simulation decision → enforcement action → audit record
```

### 24.2 Audit Evidence Requirements

| Requirement | Description |
|-------------|-------------|
| Event recorded for every enforcement action | All 16 event types from 89H §6 |
| Records are checksummed (SHA-256) | Tamper-evident per record |
| Chain integrity | Each record references previous record's checksum |
| Redaction | No raw secret text in any audit record |
| Append-only | Records cannot be modified or deleted |
| Retention | 30 days minimum, 10MB max per file, 100 files max |
| Degradation trigger | Chain break → enforcement degraded to simulation |

### 24.3 Rollback Evidence Requirements

| Requirement | Description |
|-------------|-------------|
| Pre-mutation snapshot | File state captured before every governed mutation |
| Artifact checksummed | Rollback artifact integrity verifiable |
| Restore tested | Rollback restore proven to work |
| Git reflog fallback | When artifact is corrupted or missing |
| Reversible | Rollback can be re-applied after restore |

### 24.4 Evidence Ownership

- **Audit evidence:** Owned by audit logger. Broker and enforcement executor produce the events; audit logger records them.
- **Rollback evidence:** Owned by rollback creator. Enforcement executor triggers creation; rollback creator captures and stores artifacts.

## 25. Failure Modes and Fail-Closed Behavior

### 25.1 Fail-Closed Principle

**Any failure, uncertainty, missing evidence, contradiction, or error must result in blocking the command — never allowing it.**

### 25.2 Failure Mode Catalog

| # | Failure | Detection | Behavior |
|---|---------|-----------|----------|
| F1 | Shell gate classification error | Exception during `_classify_command` | Block as `blocked_by_shell_gate` |
| F2 | Broker decision error | Exception during `_broker_decide` | Block as `blocked_by_conflicting_evidence` |
| F3 | Scope preflight error | Exception during `build_scope_preflight` | Block as `blocked_by_scope` |
| F4 | Audit write failure | Write error, disk full | Degrade enforcement to simulation |
| F5 | Audit chain broken | Chain validation on read | Degrade enforcement to simulation |
| F6 | Rollback artifact corrupted | Checksum verification fails | Use git reflog fallback |
| F7 | Rollback artifact missing | File not found | Use git reflog fallback |
| F8 | Enforcement state corrupted | State file parse failure | Default to disabled/degraded |
| F9 | Race condition (state change between check and enforce) | Version mismatch | Atomic check-and-enforce; re-check on mismatch |
| F10 | Concurrent audit writes | File lock contention | Retry with exponential backoff |
| F11 | Missing evidence for mutating action | `missing_evidence` non-empty | Block as `requires_more_evidence` |
| F12 | Shell hook fails to load | Import error, config error | All commands pass through (fail open for shell hook only — enforcement layer still blocks) |
| F13 | Classification timeout | >500ms for classification | Allow with warning; log audit event |
| F14 | Memory exhaustion | OOM during classification | Process terminates; state preserved; enforcement degrades on restart |

### 25.3 Degraded Mode

When audit integrity cannot be verified:

1. Enforcement automatically degrades to simulation-only
2. Operator notified: "Enforcement degraded: audit integrity cannot be verified"
3. All commands evaluated but not blocked
4. Audit events still produced (best-effort) for the degradation itself
5. Operator must run `pcae enforcement enable` to re-enable after repair

## 26. No-Go Conditions

### 26.1 Absolute Blocks on Enforcement Implementation

Enforcement implementation must not start if ANY of these is true:

| # | Condition | Source |
|---|-----------|--------|
| **STOP-1** | Any mandatory gate in 89J §6–13 is NOT SATISFIED | 89J |
| **STOP-2** | Full test suite is not green (zero failures) | 89J |
| **STOP-3** | No enforcement task contract exists | 89J |
| **STOP-4** | Operator has not explicitly authorized enforcement phase | 89J |
| **STOP-5** | Any safety invariant test fails | 89J |
| **STOP-6** | Hard-block override is possible by any code path | 88V §16 |
| **STOP-7** | Secret redaction can be bypassed in any output path | 89G |
| **STOP-8** | Audit chain can be broken without detection | 89H |
| **STOP-9** | Rollback does not work or is not tested | 89H |
| **STOP-10** | Emergency disable does not work or is not tested | 89G |

### 26.2 90A-Specific No-Go Conditions

| # | Condition | Rationale |
|---|-----------|-----------|
| **90A-STOP-1** | No enforcement boundary design document | Design is the authority; implementation without design is ungoverned |
| **90A-STOP-2** | Full-suite baseline not inspected/repaired | 188 pre-existing failures must be classified before implementation |
| **90A-STOP-3** | No explicit operator authorization for enforcement implementation | Human authority is absolute |
| **90A-STOP-4** | Readiness gates not tracked against 90A boundary decisions | Each boundary decision must map to specific gates |

## 27. 90B Full-Suite Baseline Repair Plan

### 27.1 Problem Statement

After 89N, the full suite has 188 pre-existing scope/preflight idle-state failures (9342/9530 passed). These failures predate the 89L–89N batch and are not caused by any prototype code. They must be inspected and repaired/classified before any 90-series implementation or prototype begins.

### 27.2 90B Scope

| Activity | Description |
|----------|-------------|
| Inspect | Categorize all 188 failures by root cause |
| Repair | Fix failures caused by stale test expectations, idle-state assumptions, or scope/preflight drift |
| Classify | Document failures that cannot be immediately repaired (deferred defects, platform-specific, etc.) |
| Prevent | Add regression guards to prevent recurrence |

### 27.3 90B Constraints

| Constraint | Description |
|------------|-------------|
| 90B is inspection/repair only | No new features, no enforcement, no prototype code |
| 90B must not change enforcement behavior | No blocking, interception, or authorization |
| 90B must not regress fast-green | Fast-green remains at 3221/3221 |
| 90B must not regress quick tier | Quick tier failures must not increase |
| 90B should target zero full-suite failures | 9530/9530 passed, or all remaining failures classified as known/deferred |

### 27.4 90B Success Criteria

| Criterion | Target |
|-----------|--------|
| Full suite failures classified | All 188 failures inspected and categorized |
| Repairable failures fixed | Zero repairable failures remaining |
| Unrepairable failures documented | Each with root cause and deferral rationale |
| Fast-green unchanged | 3221/3221 |
| New tests added | Regression guards for repaired failure categories |

### 27.5 Recommended Approach

1. Run full suite and capture failure output
2. Group failures by test module and error type
3. For each group: identify root cause (stale expectation, idle-state assumption, scope/preflight drift, platform-specific, pre-existing known issue)
4. Fix repairable failures
5. Document unrepairable failures as deferred defects
6. Add regression tests for fixed categories
7. Run full suite to verify

## 28. Recommended Next Phase

### 28.1 Primary Recommendation

**90B — Full-Suite Baseline Inspection and Scope/Preflight Repair**

**Rationale:** Before any 90-series implementation or prototype begins, the 188 pre-existing full-suite failures must be inspected and repaired/classified. 90A has defined the enforcement boundary; 90B ensures the test foundation is solid before any code crosses that boundary.

### 28.2 Future Phases (After 90B)

| Phase | Name | Type | Depends On |
|-------|------|------|-----------|
| 90C | Enforcement Executor Prototype (simulation-only) | Implementation | 90B (green suite) |
| 90D | Audit Logger Implementation (simulation-only) | Implementation | 90C |
| 90E | Rollback Creator Implementation (simulation-only) | Implementation | 90C |
| 90F | Gate Satisfaction — Design Gates (D9–D13) | Design | 90A boundary design |
| 90G | Gate Satisfaction — Test Gates (T1–T13) | Tests | 90C–90E |
| 90H | Enforcement Integration Verification | Tests | 90C–90G |

### 28.3 Decision Required

The operator must explicitly authorize 90B before it begins. 90A is complete upon acceptance of this design document.

---

*Phase 90A completes the permission broker enforcement boundary design. This is a design-only phase. No enforcement, blocking, interception, or authorization has been implemented. All simulation-only invariants remain intact. The next recommended phase is 90B — Full-Suite Baseline Inspection and Scope/Preflight Repair.*
