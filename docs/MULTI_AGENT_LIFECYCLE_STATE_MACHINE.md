# Multi-Agent Lifecycle State Machine

## Purpose

Define a lifecycle state machine for governed multi-agent work, connecting the four schemas (prompt package, capture metadata, output intake, adoption candidate) into a unified model with explicit states, transitions, guards, artifact requirements, authorization flags, failure handling, and closure conditions.

## Scope

State machine documentation only. This artifact defines states, transitions, guards, and rules. It does not implement validators, CLI commands, or executable state storage.

## Non-Goals

- State machine implementation in code.
- CLI command implementation.
- Backend invocation or prompt sending.
- Output capture, intake, or adoption.
- Executable state files outside docs.

## Motivation from 83A–83L and 84B–84E

The 83A–83L lifecycle proved that governed multi-agent work is feasible but required 12 manually orchestrated phases. The four schemas (84B–84E) structure the data at each stage. This state machine connects those schemas into a unified lifecycle model, enabling future command-line orchestration.

## State Machine Design Principles

1. **Forward-only.** State transitions are monotonic unless explicitly blocked or quarantined.
2. **Guard-gated.** Every transition requires guards to pass before proceeding.
3. **Artifact-backed.** Every state requires specific artifacts to exist.
4. **Flag-driven.** Authorization flags track what is permitted at each state.
5. **Failure-explicit.** Every failure mode has a defined handling path.
6. **Human-gated downstream.** Adoption, commit, and push always require human approval.
7. **Schema-linked.** Each state maps to one or more schema instances from 84B–84E.

---

## Lifecycle Entities

| Entity | Schema | Description |
|--------|--------|-------------|
| contract | 83A design | Multi-agent task contract defining roles, agents, scope |
| route | 83D approval | Approved routing path for the contract |
| prompt_package | 84B schema | Structured prompt package with role/agent/prompt bindings |
| prompt_invocation_approval | 83F artifact | Approval to send prompts and invoke backends |
| capture_metadata | 84C schema | Structured capture results from backend invocations |
| output_intake | 84D schema | Classification of captured outputs |
| adoption_candidate_set | 84E schema | Candidates, deferred items, rejected items |
| adoption_approval | 83J artifact | Approval of specific candidates |
| adoption_execution | 83K artifact | Execution record of approved candidates |
| final_verification | 83L artifact | End-to-end lifecycle verification |
| deferred_item_tracker | future | Tracking of deferred items across lifecycles |

---

## Core Lifecycle States

```
draft → contracted → route_approved → prompt_package_drafted → prompt_invocation_approved
    → prompt_sent_captured → output_intaked → adoption_reviewed → adoption_approved
    → adoption_executed → verified → closed

Any active state → blocked (on policy/safety failure)
prompt_sent_captured → quarantined (on mutation detected)
Any state → failed (on unrecoverable error)
```

### State List

| # | State | Description |
|---|-------|-------------|
| 1 | `draft` | Lifecycle initiated, no artifacts yet |
| 2 | `contracted` | Multi-agent contract created with roles and scope |
| 3 | `route_approved` | Routing path approved for the contract |
| 4 | `prompt_package_drafted` | Prompt package prepared with agent/role/prompt bindings |
| 5 | `prompt_invocation_approved` | Operator approved sending prompts to approved backends |
| 6 | `prompt_sent_captured` | Prompts sent, outputs captured with metadata |
| 7 | `output_intaked` | Captured outputs classified through intake |
| 8 | `adoption_reviewed` | Intake findings reviewed for adoption candidacy |
| 9 | `adoption_approved` | Specific candidates approved for execution |
| 10 | `adoption_executed` | Approved candidates applied to target files |
| 11 | `verified` | End-to-end lifecycle verification complete |
| 12 | `closed` | Lifecycle formally closed |
| 13 | `blocked` | Policy, safety, or validation failure prevents progress |
| 14 | `quarantined` | Mutation detected during capture; evidence preserved |
| 15 | `failed` | Unrecoverable error; requires new contract or explicit closure |

---

## State Definitions

### 1. draft

| Field | Value |
|-------|-------|
| purpose | Lifecycle initiated |
| entry_conditions | None (initial state) |
| required_artifacts | None |
| allowed_actions | Create contract |
| forbidden_actions | All invocation, capture, intake, adoption, commit, push |
| exit_conditions | Contract artifact created |
| allowed_next_states | `contracted` |
| blocked_next_states | All others |

### 2. contracted

| Field | Value |
|-------|-------|
| purpose | Contract defines roles, agents, scope, and governance requirements |
| entry_conditions | Contract artifact exists with valid roles and scope |
| required_artifacts | Contract instance (83C schema) |
| allowed_actions | Route approval |
| forbidden_actions | Invocation, capture, intake, adoption, commit, push |
| authorization_flags | `routing_authorized=false`, all others false |
| exit_conditions | Route approval artifact created |
| allowed_next_states | `route_approved`, `blocked` |

### 3. route_approved

| Field | Value |
|-------|-------|
| purpose | Routing path approved; agents bound to roles |
| entry_conditions | Routing approval artifact exists; agents verified available |
| required_artifacts | Routing approval (83D) |
| allowed_actions | Prompt package drafting |
| forbidden_actions | Invocation, capture, intake, adoption, commit, push |
| authorization_flags | `routing_authorized=true`, all others false |
| exit_conditions | Prompt package artifact created |
| allowed_next_states | `prompt_package_drafted`, `blocked` |

### 4. prompt_package_drafted

| Field | Value |
|-------|-------|
| purpose | Prompt package prepared with exact prompt text, role bindings, safety constraints |
| entry_conditions | Prompt package artifact exists; validation passes |
| required_artifacts | Prompt package (84B schema) |
| allowed_actions | Prompt invocation approval |
| forbidden_actions | Sending prompts, invocation, capture, intake, adoption |
| authorization_flags | `routing_authorized=true`, `prompts_authorized=false` |
| exit_conditions | Invocation approval artifact created |
| allowed_next_states | `prompt_invocation_approved`, `blocked` |

### 5. prompt_invocation_approved

| Field | Value |
|-------|-------|
| purpose | Operator approved sending the exact prepared prompts |
| entry_conditions | Invocation approval artifact exists |
| required_artifacts | Invocation approval (83F) |
| allowed_actions | Send prompts, invoke backends, capture output |
| forbidden_actions | Intake, adoption, commit of adopted content, push of adopted content |
| authorization_flags | `routing_authorized=true`, `backend_invocation_authorized=true`, `prompts_authorized=true` |
| exit_conditions | Capture metadata artifact created |
| allowed_next_states | `prompt_sent_captured`, `quarantined`, `blocked`, `failed` |

### 6. prompt_sent_captured

| Field | Value |
|-------|-------|
| purpose | Prompts sent, outputs captured with metadata; no mutation detected |
| entry_conditions | Capture metadata exists; mutation guard passed |
| required_artifacts | Capture metadata (84C schema) |
| allowed_actions | Output intake |
| forbidden_actions | Adoption, commit of adopted content, push of adopted content |
| authorization_flags | `prompts_sent=true`, `backend_invocation_performed=true` |
| exit_conditions | Intake artifact created |
| allowed_next_states | `output_intaked`, `blocked` |

### 7. output_intaked

| Field | Value |
|-------|-------|
| purpose | Captured outputs classified; prompt adherence, safety, contract fit verified |
| entry_conditions | Intake artifact exists; all checks recorded |
| required_artifacts | Output intake (84D schema) |
| allowed_actions | Adoption review |
| forbidden_actions | Adoption execution, commit of adopted content, push of adopted content |
| authorization_flags | `outputs_intaked=true`, `adoption_authorized=false` |
| exit_conditions | Adoption review artifact created |
| allowed_next_states | `adoption_reviewed`, `blocked` |

### 8. adoption_reviewed

| Field | Value |
|-------|-------|
| purpose | Findings classified as candidates, deferred, or rejected |
| entry_conditions | Adoption review artifact exists |
| required_artifacts | Adoption review (83I), Adoption candidate set (84E schema) |
| allowed_actions | Adoption approval |
| forbidden_actions | Adoption execution, commit of adopted content, push of adopted content |
| authorization_flags | `adoption_candidates_identified=true`, `adoption_authorized=false` |
| exit_conditions | Adoption approval artifact created |
| allowed_next_states | `adoption_approved`, `blocked` |

### 9. adoption_approved

| Field | Value |
|-------|-------|
| purpose | Specific candidates approved with target files and scope |
| entry_conditions | Adoption approval artifact exists |
| required_artifacts | Adoption approval (83J) |
| allowed_actions | Adoption execution |
| forbidden_actions | Commit/push of adopted content (separate governance) |
| authorization_flags | `adoption_authorized=true`, `adoption_execution_authorized=false` |
| exit_conditions | Adoption execution artifact created |
| allowed_next_states | `adoption_executed`, `blocked` |

### 10. adoption_executed

| Field | Value |
|-------|-------|
| purpose | Approved candidates applied to target files |
| entry_conditions | Execution artifact exists; scope verified |
| required_artifacts | Adoption execution (83K) |
| allowed_actions | Verification |
| forbidden_actions | New adoption without new lifecycle |
| authorization_flags | `adoption_performed=true` |
| exit_conditions | Verification artifact created |
| allowed_next_states | `verified`, `blocked` |

### 11. verified

| Field | Value |
|-------|-------|
| purpose | End-to-end lifecycle verification complete |
| entry_conditions | Verification artifact exists; all boundaries confirmed |
| required_artifacts | Final verification (83L) |
| allowed_actions | Closure |
| authorization_flags | `lifecycle_verified=true` |
| exit_conditions | Governed push complete, clean state |
| allowed_next_states | `closed` |

### 12. closed

| Field | Value |
|-------|-------|
| purpose | Lifecycle formally closed |
| entry_conditions | All artifacts present; repo clean; origin/main..HEAD=0 |
| required_artifacts | All lifecycle artifacts |
| allowed_actions | None (terminal state) |
| authorization_flags | `lifecycle_closed=true` |
| exit_conditions | None (terminal) |
| allowed_next_states | None |

### 13. blocked

| Field | Value |
|-------|-------|
| purpose | Progress halted due to policy, safety, or validation failure |
| entry_conditions | Any guard failure or policy violation |
| allowed_actions | Human review, remediation, explicit closure |
| exit_conditions | Issue resolved and guard re-checked, or explicit no-op closure |
| allowed_next_states | Previous state (after fix), `failed`, `closed` (explicit no-op) |

### 14. quarantined

| Field | Value |
|-------|-------|
| purpose | Mutation detected during capture; evidence preserved |
| entry_conditions | Mutation guard detected unexpected changes |
| allowed_actions | Preserve evidence, human review, intake with quarantine classification |
| forbidden_actions | Adoption, commit, push until resolved |
| exit_conditions | Quarantine resolved through intake review |
| allowed_next_states | `output_intaked` (with quarantine findings), `blocked`, `failed` |

### 15. failed

| Field | Value |
|-------|-------|
| purpose | Unrecoverable error |
| entry_conditions | Critical failure (backend crash, data corruption, irreconcilable state) |
| allowed_actions | Explicit closure, new contract |
| exit_conditions | Explicit closure artifact |
| allowed_next_states | `closed` (with failure documentation) |

---

## Allowed Transitions

| # | From | To | Guard |
|---|------|----|-------|
| T1 | `draft` | `contracted` | Contract artifact created and validated |
| T2 | `contracted` | `route_approved` | Route approval artifact created |
| T3 | `route_approved` | `prompt_package_drafted` | Prompt package created and validated |
| T4 | `prompt_package_drafted` | `prompt_invocation_approved` | Invocation approval created |
| T5 | `prompt_invocation_approved` | `prompt_sent_captured` | Prompts sent, capture metadata created, no mutation |
| T6 | `prompt_invocation_approved` | `quarantined` | Mutation detected during capture |
| T7 | `prompt_sent_captured` | `output_intaked` | Intake artifact created, checks passed |
| T8 | `output_intaked` | `adoption_reviewed` | Review artifact created with candidate classifications |
| T9 | `adoption_reviewed` | `adoption_approved` | Approval artifact created with approved candidates |
| T10 | `adoption_approved` | `adoption_executed` | Execution artifact created, scope verified |
| T11 | `adoption_executed` | `verified` | Verification artifact created, boundaries confirmed |
| T12 | `verified` | `closed` | Governed push complete, clean state |
| T13 | any active | `blocked` | Any guard failure or policy violation |
| T14 | `quarantined` | `output_intaked` | Quarantine resolved through intake review |
| T15 | `blocked` | previous | Issue remediated, guard re-passed |
| T16 | `blocked` | `closed` | Explicit no-op closure with documentation |
| T17 | `failed` | `closed` | Explicit failure closure |

**17 allowed transitions.**

## Blocked Transitions

| # | From | To | Reason |
|---|------|----|--------|
| B1 | `draft` | `prompt_sent_captured` | Cannot skip contract, route, package, approval |
| B2 | `contracted` | `prompt_sent_captured` | Cannot skip route, package, approval |
| B3 | `route_approved` | `prompt_sent_captured` | Cannot skip package and approval |
| B4 | `prompt_package_drafted` | `prompt_sent_captured` | Cannot skip invocation approval |
| B5 | `prompt_sent_captured` | `adoption_executed` | Cannot skip intake and adoption review/approval |
| B6 | `output_intaked` | `adoption_executed` | Cannot skip adoption review and approval |
| B7 | `adoption_reviewed` | `adoption_executed` | Cannot skip adoption approval |
| B8 | `adoption_approved` | `closed` | Cannot skip execution and verification (or explicit no-op) |
| B9 | any | `commit_authorized` | Commit requires governed commit path, not state transition |
| B10 | any | `push_authorized` | Push requires governed push path, not state transition |
| B11 | any | `source_mutation_authorized` | Requires explicit source scope approval |
| B12 | any | `test_mutation_authorized` | Requires explicit test scope approval |
| B13 | any | `docs_real_mutation` | Requires explicit approval |
| B14 | `blocked` | `closed` | Cannot close without verification unless explicit no-op |
| B15 | `quarantined` | `adoption_approved` | Cannot approve adoption from quarantine without intake |

**15 blocked transitions.**

---

## Transition Guard Fields

Each transition guard:

| Field | Type | Description |
|-------|------|-------------|
| `transition_id` | string | Unique transition identifier |
| `from_state` | string | Source state |
| `to_state` | string | Target state |
| `required_artifacts` | list[string] | Artifacts that must exist |
| `required_authorization_flags` | dict | Flags that must be true |
| `required_checks` | list[string] | Checks that must pass |
| `forbidden_flags` | dict | Flags that must be false |
| `forbidden_file_patterns` | list[string] | Files that must not be modified |
| `requires_human_review` | boolean | Whether human must approve |
| `requires_mutation_guard` | boolean | Whether pre/post git comparison needed |
| `requires_capture_metadata` | boolean | Whether capture metadata must exist |
| `requires_output_intake` | boolean | Whether intake must be complete |
| `requires_adoption_approval` | boolean | Whether adoption approval must exist |

---

## Required Artifact Matrix

| State | Required Artifact | Schema |
|-------|-------------------|--------|
| `contracted` | Contract instance | 83A design |
| `route_approved` | Routing approval | 83D |
| `prompt_package_drafted` | Prompt package | 84B schema |
| `prompt_invocation_approved` | Invocation approval | 83F |
| `prompt_sent_captured` | Capture metadata | 84C schema |
| `output_intaked` | Output intake | 84D schema |
| `adoption_reviewed` | Adoption review + candidate set | 84E schema |
| `adoption_approved` | Adoption approval | 83J |
| `adoption_executed` | Adoption execution | 83K |
| `verified` | Final verification | 83L |
| `closed` | All above + clean repo + governed push | — |

---

## Authorization Flag Matrix

| Flag | draft | contracted | route_approved | pkg_drafted | invoc_approved | sent_captured | intaked | reviewed | approved | executed | verified | closed |
|------|-------|-----------|---------------|-------------|---------------|--------------|---------|----------|----------|----------|----------|--------|
| routing_authorized | F | F | **T** | T | T | T | T | T | T | T | T | T |
| backend_invocation_authorized | F | F | F | F | **T** | T | T | T | T | T | T | T |
| prompts_authorized | F | F | F | F | **T** | T | T | T | T | T | T | T |
| prompts_sent | F | F | F | F | F | **T** | T | T | T | T | T | T |
| backend_invocation_performed | F | F | F | F | F | **T** | T | T | T | T | T | T |
| outputs_intaked | F | F | F | F | F | F | **T** | T | T | T | T | T |
| adoption_candidates_identified | F | F | F | F | F | F | F | **T** | T | T | T | T |
| adoption_authorized | F | F | F | F | F | F | F | F | **T** | T | T | T |
| adoption_performed | F | F | F | F | F | F | F | F | F | **T** | T | T |
| lifecycle_verified | F | F | F | F | F | F | F | F | F | F | **T** | T |
| lifecycle_closed | F | F | F | F | F | F | F | F | F | F | F | **T** |
| execution_authorized | F | F | F | F | F | F | F | F | F | F | F | F |
| subagent_invocation_authorized | F | F | F | F | F | F | F | F | F | F | F | F |
| commit_authorized | F | F | F | F | F | F | F | F | F | F | F | F |
| push_authorized | F | F | F | F | F | F | F | F | F | F | F | F |

`execution_authorized`, `subagent_invocation_authorized`, `commit_authorized`, and `push_authorized` remain **false throughout** the multi-agent lifecycle. Commits and pushes use the governed PCAE path, not lifecycle authorization flags.

---

## Boundary Rules

1. Prompt approval does not imply adoption approval.
2. Capture does not imply intake.
3. Intake does not imply adoption approval.
4. Adoption approval does not imply adoption execution.
5. Adoption execution does not imply commit approval.
6. Commit approval does not imply push approval.
7. Push must remain governed (`pcae push`).
8. Blocked agents cannot receive prompts at any state.
9. Unknown agents are disabled by default at any state.
10. Subagents require discovery and approval (not available in current lifecycle).
11. Mutation detection forces `quarantined` or `blocked` state.
12. Raw git push remains disallowed at any state.
13. Force push remains disallowed at any state.
14. Hook bypass must remain exceptional and reconciled.

---

## Failure and Quarantine States

| State | Trigger | Evidence | Recovery |
|-------|---------|----------|----------|
| `blocked` | Guard failure, policy violation, safety check failure | Blocker documented in artifact | Fix issue, re-check guard, or explicit no-op closure |
| `quarantined` | Mutation detected during capture | Pre/post git state preserved | Intake with quarantine classification, then human review |
| `failed` | Backend crash, data corruption, irreconcilable state | Failure documented | Explicit closure with failure record, or new contract |
| `partial_capture` | Some invocations succeeded, some failed | Per-invocation status in capture metadata | Retry with approval, or proceed with partial intake |

## Recovery and Retry Rules

1. Retry requires explicit human approval.
2. Retry must preserve original capture metadata (append, not overwrite).
3. Retry must not overwrite failed evidence.
4. Mutation quarantine must preserve all changed files.
5. Blocked state requires human review before resuming.
6. Failed state requires explicit closure or new contract.
7. Prompt hash mismatch requires new invocation approval.
8. Missing capture storage requires intake warning or recapture approval.
9. Recovery transitions re-check all guards for the target state.

## Closure Rules

1. All required artifacts present for the reached state.
2. All boundary checks passed at the reached state.
3. All approved adoption candidates either executed or explicitly closed as no-op.
4. Deferred items documented and carried forward.
5. Rejected items remain rejected with documented reasons.
6. Forbidden files unchanged (src, tests, README, docs/REAL_CAPTURED_TASKS.md).
7. pcae health, check, doctor task-memory clean.
8. pcae push check clean.
9. origin/main..HEAD count = 0 after governed push.
10. No phase beyond closure started.

---

## Example Lifecycle Trace

Based on MULTI-AGENT-DRY-RUN-001 (83A–83L):

| Step | State | Phase | Artifact | Key Flag Set |
|------|-------|-------|----------|-------------|
| 1 | `draft` → `contracted` | 83A–83C | Contract instance | — |
| 2 | `contracted` → `route_approved` | 83D | Routing approval | `routing_authorized=true` |
| 3 | `route_approved` → `prompt_package_drafted` | 83E | Prompt package | — |
| 4 | `prompt_package_drafted` → `prompt_invocation_approved` | 83F | Invocation approval | `backend_invocation_authorized=true`, `prompts_authorized=true` |
| 5 | `prompt_invocation_approved` → `prompt_sent_captured` | 83G | Capture metadata | `prompts_sent=true`, `backend_invocation_performed=true` |
| 6 | `prompt_sent_captured` → `output_intaked` | 83H | Output intake | `outputs_intaked=true` |
| 7 | `output_intaked` → `adoption_reviewed` | 83I | Adoption review | `adoption_candidates_identified=true` |
| 8 | `adoption_reviewed` → `adoption_approved` | 83J | Adoption approval | `adoption_authorized=true` |
| 9 | `adoption_approved` → `adoption_executed` | 83K | Adoption execution | `adoption_performed=true` |
| 10 | `adoption_executed` → `verified` | 83L | Final verification | `lifecycle_verified=true` |
| 11 | `verified` → `closed` | 83L | Governed push | `lifecycle_closed=true` |

Route: claude-local (planner) → claude-deepseek (reviewer) → human/operator (governance).
Capture: 2 invocations, no mutation. Intake: reviewable_candidate. Adoption: AC-1, AC-2, AC-3 executed (4 lines across 2 files). Final: verified/closed_successfully.

---

## Validation Rule Set

| # | Rule ID | Description |
|---|---------|-------------|
| 1 | `TRANSITION_VALID` | Only allowed transitions may be taken |
| 2 | `TRANSITION_SEQUENTIAL` | States must be reached in order unless blocked/quarantined |
| 3 | `ARTIFACT_REQUIRED` | Each state requires its specified artifact to exist |
| 4 | `FLAGS_CONSISTENT` | Authorization flags must match the current state |
| 5 | `FLAGS_MONOTONIC` | Once a flag becomes true, it remains true (except in blocked/failed) |
| 6 | `BLOCKED_TRANSITION_PREVENTED` | Blocked transitions must be refused |
| 7 | `BLOCKED_AGENT_NO_PROMPT` | Blocked agents cannot receive prompts at any state |
| 8 | `UNKNOWN_AGENT_DISABLED` | Unknown agents are disabled at any state |
| 9 | `PROMPT_HASH_STABLE` | Sent prompt hash must match approved package hash |
| 10 | `CAPTURE_METADATA_REQUIRED` | Capture metadata must exist before intake |
| 11 | `MUTATION_GUARD_REQUIRED` | Mutation guard must run before and after every invocation |
| 12 | `MUTATION_FORCES_QUARANTINE` | Mutation detected must transition to quarantined or blocked |
| 13 | `INTAKE_BEFORE_ADOPTION` | Intake must complete before adoption review |
| 14 | `REVIEW_BEFORE_APPROVAL` | Adoption review must complete before adoption approval |
| 15 | `APPROVAL_BEFORE_EXECUTION` | Adoption approval must precede adoption execution |
| 16 | `COMMIT_SEPARATE` | Commit authorization is separate from adoption authorization |
| 17 | `PUSH_SEPARATE` | Push authorization is separate from commit authorization |
| 18 | `PUSH_GOVERNED` | Push must use governed `pcae push` |
| 19 | `NO_FORCE_PUSH` | Force push is forbidden at all states |
| 20 | `NO_RAW_PUSH` | Raw git push is forbidden at all states |
| 21 | `FORBIDDEN_FILES_PROTECTED` | src/**, tests/**, README.md, docs/REAL_CAPTURED_TASKS.md protected |
| 22 | `SOURCE_REQUIRES_AUTH` | Source mutation requires explicit authorization |
| 23 | `TEST_REQUIRES_AUTH` | Test mutation requires explicit authorization |
| 24 | `README_REQUIRES_AUTH` | README mutation requires explicit authorization |
| 25 | `REAL_CAPTURED_REQUIRES_AUTH` | docs/REAL_CAPTURED_TASKS.md mutation requires explicit authorization |
| 26 | `QUARANTINE_PRESERVES_EVIDENCE` | Quarantine must preserve all changed files |
| 27 | `RETRY_REQUIRES_APPROVAL` | Retry requires explicit human approval |
| 28 | `FAILED_REQUIRES_CLOSURE` | Failed state requires explicit closure |
| 29 | `CLOSURE_REQUIRES_ARTIFACTS` | Closure requires all reached-state artifacts |
| 30 | `CLOSURE_REQUIRES_CLEAN` | Closure requires clean repo and governed push |
| 31 | `DEFERRED_CARRIED_FORWARD` | Deferred items must be documented at closure |
| 32 | `EXECUTION_AUTH_ALWAYS_FALSE` | `execution_authorized` remains false throughout lifecycle |
| 33 | `SUBAGENT_AUTH_ALWAYS_FALSE` | `subagent_invocation_authorized` remains false (current lifecycle) |
| 34 | `NO_AUTO_ADOPTION` | Backend output must not be auto-adopted at any state |
| 35 | `HUMAN_GATES_DOWNSTREAM` | Adoption, commit, push require human approval |

**35 validation rules.**

---

## Failure Cases

| # | Failure | State Impact | Handling |
|---|---------|-------------|----------|
| 1 | Missing required artifact | Block transition | Create artifact before proceeding |
| 2 | Invalid state transition | Refused | Document and stay in current state |
| 3 | Prompt sent before approval | `blocked` | Quarantine output, investigate |
| 4 | Backend invoked before approval | `blocked` | Quarantine output, investigate |
| 5 | Unknown agent routed | `blocked` | Refuse routing |
| 6 | Blocked agent invoked | `blocked` | Quarantine output, refuse |
| 7 | Subagent invoked without discovery | `blocked` | Refuse, require discovery phase |
| 8 | Capture metadata missing | `blocked` at intake | Require recapture |
| 9 | Mutation guard missing | `blocked` | Require guard before proceeding |
| 10 | Mutation detected | `quarantined` | Preserve evidence, human review |
| 11 | Output intake skipped | `blocked` at adoption | Require intake |
| 12 | Adoption approved before intake | `blocked` | Require intake first |
| 13 | Adoption executed before approval | `blocked` | Refuse execution |
| 14 | Forbidden file changed | `blocked` | Revert or quarantine |
| 15 | Source/test changed without auth | `blocked` | Refuse, require explicit auth |
| 16 | README changed without auth | `blocked` | Refuse, require explicit auth |
| 17 | docs/REAL_CAPTURED_TASKS.md changed | `blocked` | Refuse, require explicit auth |
| 18 | Commit/push boundary collapsed | `blocked` | Separate governance required |
| 19 | Raw git push used | `blocked` | Refuse; require governed push |
| 20 | Force push used | `blocked` | Refuse unconditionally |
| 21 | Closure with dirty tree | `blocked` | Clean before closure |
| 22 | Closure with unpushed commits | `blocked` | Push before closure |

**22 failure cases.**

---

## Schema Status

| Field | Value |
|-------|-------|
| state_machine_name | multi_agent_lifecycle |
| state_machine_version | 0.1 |
| state_machine_status | draft_documented |
| state_machine_implementation_status | not_started |

## Recommended Next Phase

**84G — Multi-Agent Lifecycle Command Dry-Run**

84G should design the dry-run command surface for inspecting lifecycle state, checking transition guards, and showing next allowed transitions, still without implementing real execution unless separately scoped. This would give PCAE a `pcae multi-agent status`, `pcae multi-agent next`, and `pcae multi-agent check-guard` command surface analogous to the existing single-agent lifecycle commands.
