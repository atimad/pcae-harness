# Lifecycle Command Consolidation Plan

## Purpose

Consolidate the 15+ individual phase commands from the 77J-77V.1 backend-created output adoption lifecycle into a governed lifecycle state machine with a unified command family. This plan is documentation-only; it does not implement any commands.

## Current Problem

The completed lifecycle required 15 phases, each with its own `pcae phase <name>` command, its own artifact directory, and its own gate checks. An operator must know the exact sequence, run each command individually, and verify gate status between steps. This is correct for safety but unsustainable for repeated use.

Key friction points:

- No single command shows lifecycle progress.
- No command recommends the next legal action.
- No command summarizes the full lifecycle state.
- Gate ordering is implicit in phase naming, not enforced by a state machine.
- Approval bindings can become stale when implementation commits expand the unpushed range.

## Current Lifecycle Gates

| Gate | Phase | Command (current) | Boundary |
|------|-------|--------------------|----------|
| Backend capture | 77F/77J | `pcae phase real-captured-task-backend-capture` | Backend invocation |
| Mutation intake | 77G/77K | `pcae phase backend-retry-mutation-result-intake` | Classification |
| Quarantine review | 77L | `pcae phase backend-created-output-quarantine-review` | File validation |
| Adoption preflight | 77M | `pcae phase backend-created-output-adoption-preflight` | Readiness |
| Adoption review | 77N | `pcae phase backend-created-output-adoption-review` | Content safety |
| Adoption approval | 77O | `pcae phase backend-created-output-adoption-approval` | Human approval |
| Execution preflight | 77P | `pcae phase backend-created-output-adoption-execution-preflight` | Safety gates |
| Adoption execution | 77Q | `pcae phase backend-created-output-adoption-execution` | Staging |
| Commit approval | 77R | `pcae phase backend-created-output-adoption-commit-approval` | Human approval |
| Commit execution | 77S | `pcae phase backend-created-output-adoption-commit-execution` | Commit |
| Hook-bypass reconciliation | 77S.1 | `pcae phase adoption-commit-hook-bypass-reconcile` | Exception |
| Push approval | 77T | `pcae phase backend-created-output-adoption-push-approval` | Human approval |
| Push execution | 77U | `pcae phase backend-created-output-adoption-push-execution` | Push |
| Final verification | 77V | `pcae phase backend-created-output-adoption-final-verification` | Verification |
| Tooling closure | 77V.1 | `pcae phase final-verification-tooling-push-decision` | Closure |

## Proposed Lifecycle Command Family

```
pcae lifecycle backend-output-adoption status [--json]
pcae lifecycle backend-output-adoption next [--json]
pcae lifecycle backend-output-adoption summary [--json]
pcae lifecycle backend-output-adoption gate-status [--json]
pcae lifecycle backend-output-adoption run-gate --gate <gate> --dry-run [--json]
pcae lifecycle backend-output-adoption approve --gate <gate> --approved-by <operator> --reason <reason> [--json]
```

These commands do not replace the individual phase commands. They provide a coordination layer that reads existing artifacts and recommends or validates the next action.

## State Model

The lifecycle state machine tracks the current state of a backend-output adoption lifecycle. States are mutually exclusive.

```
idle
  -> backend_capture_ready
  -> backend_capture_attempted
  -> mutation_detected
  -> mutation_intake_classified
  -> quarantined
  -> adoption_review_ready
  -> adoption_approved
  -> adoption_execution_ready
  -> staged_for_commit
  -> commit_approved
  -> committed_for_push
  -> hook_bypass_reconciled
  -> push_approved
  -> pushed
  -> final_verified
  -> closed
  -> blocked (from any state)
```

State is derived from artifacts, not stored separately. The `status` command reads all relevant artifact files and determines the current state.

## Gate Model

Each gate corresponds to a boundary that must be crossed with evidence. Gates have three statuses:

- **not_reached** — the lifecycle has not progressed to this gate yet.
- **ready** — prerequisites are met and the gate can be attempted.
- **passed** — the gate has been crossed with evidence.
- **blocked** — the gate cannot be crossed due to a governance issue.

Gates are ordered. A gate cannot be `ready` unless all prior gates are `passed`.

## Approval Model

Three gates require explicit human/operator approval:

1. **Adoption approval** — authorizes staging the backend-created file.
2. **Commit approval** — authorizes creating a commit containing the staged file.
3. **Push approval** — authorizes pushing the commit bundle to the remote.

Approvals bind to specific artifact state (SHA256, commit range, file metadata). If the state changes after approval (e.g., new implementation commits), the approval must be refreshed.

The `approve` command records approval in the existing artifact format. It does not execute the approved action.

## Artifact Model

The lifecycle command family reads from existing `.pcae/` artifact directories. It does not create new artifact types. Each gate's status is derived from:

- Artifact existence in the expected directory.
- Artifact status field matching the expected value.
- SHA256/metadata consistency across artifacts.

The `summary` command aggregates all artifact states into a single report.

## Safe Automation Boundaries

The lifecycle command family may safely automate:

- **Status derivation** — reading artifacts and determining current state.
- **Next-step recommendation** — identifying which gate is next and what command to run.
- **Gate readiness check** — verifying prerequisites for a specific gate.
- **Dry-run gate execution** — running a gate command in dry-run mode to preview the result.
- **Summary generation** — aggregating lifecycle state into a report.

## Human Approval Boundaries

The lifecycle command family must NOT automate:

- **Approval granting** — approvals require explicit `--approve` with operator identity.
- **Backend invocation** — backend capture requires separate authorization.
- **Commit execution** — `git commit` requires explicit `--execute`.
- **Push execution** — `git push` requires explicit `--execute`.
- **Hook bypass** — `--no-verify` requires explicit bounded exception documentation.
- **Force push** — never.

## Commands to Add Later

These commands are not part of the initial consolidation but may be added in future phases:

```
pcae lifecycle backend-output-adoption history [--json]
pcae lifecycle backend-output-adoption rollback --to <state> --dry-run [--json]
pcae lifecycle backend-output-adoption compare --lifecycle-id <id> [--json]
```

## Non-Goals

- This plan does not propose a general-purpose lifecycle engine. It targets specifically the backend-created output adoption lifecycle.
- This plan does not propose removing individual phase commands. The consolidated commands are a coordination layer, not a replacement.
- This plan does not propose automatic execution of dangerous gates. Automation is limited to status, recommendations, and dry-runs.
- This plan does not implement any commands. Implementation is deferred to phases 80A through 80F.

## Risks

1. **State derivation complexity.** Reading 10+ artifact files to determine state adds latency and failure modes. Artifacts may be missing, corrupted, or from a different lifecycle instance.
2. **Stale approval detection.** Detecting when an approval is stale (because the commit range changed) requires comparing artifact state at approval time with current git state.
3. **Multi-lifecycle confusion.** If a second lifecycle starts before the first is closed, the state machine must distinguish between them. This plan assumes one active lifecycle at a time.
4. **Backward compatibility.** The consolidated commands must work with artifacts produced by the existing phase commands without migration.

## Proposed Implementation Phases

| Phase | Description |
|-------|-------------|
| 80A | Lifecycle state machine design (state derivation logic) |
| 80B | Lifecycle status command |
| 80C | Lifecycle next-step recommendation |
| 80D | Lifecycle gate runner dry-run |
| 80E | Lifecycle gate runner with human approval |
| 80F | Lifecycle final summary command |

Each phase should be independently testable and should not require the later phases to function.

## Key Constraints

- Only one adoption path may modify the repository at a time.
- Execution gates must remain separate from approval gates.
- Commit and push remain separate boundaries.
- Backend invocation remains separately governed.
- Lifecycle automation may recommend next actions but must not silently execute dangerous gates.
