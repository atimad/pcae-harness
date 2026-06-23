# Second Real Captured Task Contract

## Task ID

REAL-CAPTURED-TASK-002

## Task Title

Draft lifecycle command documentation snippet

## Task Type

documentation_only

## Selected Task Source

Phase 81A — Second Real Captured Task Selection (`docs/SECOND_REAL_CAPTURED_TASK_SELECTION.md`)

## Exact Backend Prompt

```
Draft a concise markdown documentation snippet describing PCAE's backend-output-adoption
lifecycle command family:

- `pcae lifecycle backend-output-adoption status`
- `pcae lifecycle backend-output-adoption next`
- `pcae lifecycle backend-output-adoption run-gate --dry-run`
- `pcae lifecycle backend-output-adoption approve-gate`
- `pcae lifecycle backend-output-adoption summary`

The snippet should explain that these commands provide lifecycle visibility, advisory next
steps, dry-run gate evaluation, approval recording without execution, and final summary
reporting.

The snippet must explicitly state:
- non-dry-run gate execution is not implemented,
- approval is separate from execution,
- `execution_authorized=false` remains the safety default,
- the lifecycle commands are governance/advisory tooling, not autonomous execution.
```

## Expected Output Format

- Markdown-only text (.md)
- Single file
- Concise (50-150 lines)
- No source code
- No tests
- No dependency changes
- No shell commands
- No backend invocation requests
- No push/commit instructions
- No secrets or credentials

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

## Safety Constraints

- Backend must not modify the repository directly.
- If the backend produces an unexpected repo mutation, PCAE will detect and quarantine it.
- Output must be reviewed before any adoption, commit, or push.
- Content safety scan must pass before approval.
- No governance bypass instructions allowed in output.
- No force push or raw push instructions allowed in output.

## Authorization Status

| Authorization | Status |
|---------------|--------|
| backend_invocation_status | not_invoked |
| execution_authorized | false |
| send_authorized | false |
| adoption_authorized | false |
| commit_authorized | false |
| push_authorized | false |

All authorization flags are false. No authorization has been granted. Each authorization requires a separate future governed phase with explicit operator approval.

## Required Future Gates

| Phase | Gate | Description |
|-------|------|-------------|
| 81C | Backend capture preflight | Validate all preconditions for backend invocation |
| 81D | Backend capture | Invoke backend with governed prompt; capture output |
| 81E | Output intake | Classify capture result; detect mutation if any |
| — | Quarantine review | Review quarantined output if mutation detected |
| — | Adoption preflight | Validate readiness for adoption review |
| — | Adoption review | Content safety review |
| — | Adoption approval | Explicit operator approval |
| — | Adoption execution preflight | Safety gates before staging |
| — | Adoption execution | Stage approved file |
| — | Commit approval | Explicit operator approval for commit |
| — | Commit execution | Create governed commit |
| — | Push approval | Explicit operator approval for push |
| — | Push execution | Execute governed push |
| — | Final verification | Verify local and remote state |

No gate may be skipped. Each gate with an approval requirement needs explicit operator sign-off.

## Review Criteria

The backend output should be accepted if:

1. It is markdown-only text.
2. It correctly names all five lifecycle commands.
3. It correctly describes what each command does.
4. It states that `run-gate` requires `--dry-run`.
5. It states that `approve-gate` records approval without executing.
6. It states that `non_dry_run_runner_command=false`.
7. It states that `execution_authorized=false` always.
8. It does not contain secrets, credentials, or API keys.
9. It does not contain governance bypass instructions.
10. It does not contain force push or raw push instructions.
11. It does not reference or modify source code files.
12. It is between 50 and 200 lines.

## Blockers

None. The contract is prepared and ready for preflight in Phase 81C.

## Recommended Next Phase

**81C — Second Backend Capture Preflight**

81C should validate all preconditions before the backend is invoked in 81D.
