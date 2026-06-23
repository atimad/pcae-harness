# Second Backend Capture Preflight

## Purpose

Verify that all preconditions are met for a future governed backend capture of REAL-CAPTURED-TASK-002. This preflight does not invoke any backend. Actual invocation is deferred to Phase 81D.

## Contract Verified

- **Contract:** `docs/SECOND_REAL_CAPTURED_TASK_CONTRACT.md`
- **Task ID:** REAL-CAPTURED-TASK-002
- **Task title:** Draft lifecycle command documentation snippet
- **Task type:** documentation_only
- **Expected output:** markdown-only, 50-150 lines, single file
- **Contract readable:** yes
- **Contract contains task ID:** yes
- **Contract contains prompt:** yes

## Selected Backend for Future Capture

- **Backend name:** claude-local
- **Backend command:** claude
- **Backend available:** yes
- **Agent lock owner:** claude-local
- **Lock status:** active
- **Execution authorized:** false

The backend identified for future capture is the currently locked backend (`claude-local`, command `claude`). The backend was not invoked in this preflight phase.

## Backend Invocation Status

**No backend invocation occurred in Phase 81C.** This phase is preflight and readiness verification only.

## Authorization Status

| Authorization | Status |
|---------------|--------|
| backend_invocation_authorized_now | false |
| backend_invocation_allowed_in_future_phase | true |
| send_authorized | false |
| execution_authorized | false |
| adoption_authorized | false |
| commit_authorized | false |
| push_authorized | false |

Future backend invocation requires Phase 81D with its own explicit authorization.

## Repository Baseline

| Check | Result |
|-------|--------|
| Working tree | clean |
| HEAD | 89892b403c69c94be1a972f42b7a2818ffbb90e4 |
| origin/main | 89892b403c69c94be1a972f42b7a2818ffbb90e4 |
| HEAD == origin/main | yes |
| origin/main..HEAD count | 0 |
| pcae health | healthy (idle) |
| pcae check | passed |
| pcae doctor task-memory | clean |
| pcae push check | nothing_to_push |
| Lifecycle summary | summarized, current_state=closed |

## Mutation Guard Baseline

| Item | Value |
|------|-------|
| docs/REAL_CAPTURED_TASKS.md exists | yes |
| docs/REAL_CAPTURED_TASKS.md SHA256 prefix | 1cb1f79314496bb0 |
| docs/REAL_CAPTURED_TASKS.md modified in this phase | no |
| git status before preflight | clean |
| Untracked files before preflight | none |
| Staged files before preflight | none |

If the backend produces an unexpected repository mutation during 81D, the mutation guard will detect it by comparing post-capture git status against this baseline.

## Prompt Package Summary

The prompt for REAL-CAPTURED-TASK-002 is defined in `docs/SECOND_REAL_CAPTURED_TASK_CONTRACT.md`. It asks the backend to draft a concise markdown documentation snippet describing PCAE's lifecycle command family (status, next, run-gate --dry-run, approve-gate, summary).

The prompt package is not sent in this phase. Send authorization is explicitly false.

## Allowed Future Adoption Files

- `README.md`
- `docs/LIFECYCLE_STATE_MACHINE.md`

## Forbidden Files

- `src/**`
- `tests/**`
- `docs/REAL_CAPTURED_TASKS.md`
- `.pcae/**`
- `.githooks/**`
- `pyproject.toml`

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Backend produces repo mutation | Low | Mutation guard compares pre/post git status |
| Backend produces source code | Very low | Content safety scan blocks source references |
| Backend ignores prompt scope | Low | Output intake classifies and quarantines |
| Capture timeout | Low | Timeout policy: 300s default |
| Working tree becomes dirty | Low | Preflight verifies clean baseline |

## Capture Timeout Policy

Default capture timeout: 300 seconds. If the backend does not respond within this window, the capture will be classified as a timeout failure and a retry policy will be evaluated.

## Preconditions for 81D

All of the following must be true before 81D backend capture:

1. This preflight (81C) must report `ready_for_future_81d_capture`.
2. Contract must still be readable and unchanged.
3. Repository must be clean (no staged, unstaged, or untracked files except PCAE artifacts).
4. Backend lock must be held.
5. Agent lock must match expected backend.
6. Operator must explicitly authorize backend invocation in 81D.
7. Send authorization must be granted in 81D (not here).

## Blockers

None. All preflight checks passed.

## Preflight Outcome

| Field | Value |
|-------|-------|
| second_backend_capture_preflight_status | ready_for_backend_capture |
| preflight_outcome | ready_for_future_81d_capture |
| backend_invoked | false |
| blockers | none |

## Recommended Next Phase

**81D — Second Backend Capture**

81D should invoke the backend with the governed prompt from the contract, capture the output, and run the mutation guard. Backend invocation authorization must be granted explicitly in 81D.
