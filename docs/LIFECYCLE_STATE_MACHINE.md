# Lifecycle State Machine Design

## Purpose

Define a state model for the backend-output-adoption lifecycle so PCAE can report where a lifecycle is and what action is next, without executing anything.

## Scope

This design covers the backend-output-adoption lifecycle type only. The state machine is read-only and advisory. It does not run gates, approve gates, invoke backends, or mutate state.

## Lifecycle Type

`backend-output-adoption`

## State Model

| State ID | Label | Approval Required | Execution Boundary |
|----------|-------|-------------------|-------------------|
| idle | Idle | No | No |
| backend_capture_attempted | Backend Capture Attempted | No | No |
| mutation_detected | Mutation Detected | No | No |
| quarantined | Quarantined | No | No |
| adoption_review_ready | Adoption Review Ready | No | No |
| adoption_reviewed | Adoption Reviewed | Yes | No |
| adoption_approved | Adoption Approved | No | No |
| adoption_execution_ready | Execution Ready | No | Yes |
| staged_for_commit | Staged for Commit | Yes | No |
| commit_approved | Commit Approved | No | Yes |
| committed_for_push | Committed for Push | No | No |
| hook_bypass_reconciled | Hook Bypass Reconciled | Yes | No |
| push_approved | Push Approved | No | Yes |
| pushed | Pushed | No | No |
| final_verified | Final Verified | No | No |
| closed | Closed | No | No |
| blocked | Blocked | No | No |

## Transition Model

States progress linearly from `idle` through `closed`. Transitions are determined by artifact presence and status field values. Any state can transition to `blocked` if governance checks fail.

## Gate Model

Each gate corresponds to a state transition. Gates are classified as:

- **Read-only gates**: status inspection, next recommendation.
- **Approval gates**: require explicit operator sign-off (adoption approval, commit approval, push approval).
- **Execution gates**: perform repository mutations (staging, commit, push).

Read-only gates are safe to automate. Approval and execution gates require human authorization.

## Approval Boundaries

Three states require operator approval before the next execution boundary:

1. `adoption_reviewed` -> `adoption_approved` (adoption approval)
2. `staged_for_commit` -> `commit_approved` (commit approval)
3. `hook_bypass_reconciled` -> `push_approved` (push approval)

## Execution Boundaries

Three states cross execution boundaries:

1. `adoption_execution_ready` -> `staged_for_commit` (git add)
2. `commit_approved` -> `committed_for_push` (git commit)
3. `push_approved` -> `pushed` (git push)

## Artifact Requirements

State is derived from `.pcae/` artifact files. Each state maps to an artifact directory and a status field/value pair. State detection reads the most advanced artifact that matches.

## Read-Only Command Behavior

- `pcae lifecycle backend-output-adoption status` reads artifacts and reports current state.
- `pcae lifecycle backend-output-adoption next` recommends the next governed action.
- Neither command creates, modifies, stages, commits, pushes, or deletes files.
- Both commands set `read_only=true` and all execution flags to `false`.

## Non-Goals

- This design does not implement gate runners (deferred to 80D-80E).
- This design does not implement lifecycle summary (deferred to 80F).
- This design does not implement multi-lifecycle tracking.
- This design does not add automatic gate execution.

## Future Phases

| Phase | Description |
|-------|-------------|
| 80D | Lifecycle Gate Runner Dry-Run |
| 80E | Lifecycle Gate Runner With Human Approval |
| 80F | Lifecycle Final Summary Command |

## Safety Principles

- One adoption path may modify the repository at a time.
- Execution gates and approval gates are separate.
- Commit and push are separate boundaries.
- Backend invocation is separately governed.
- Lifecycle automation may recommend but must not silently execute dangerous gates.
- Human authority is absolute.
