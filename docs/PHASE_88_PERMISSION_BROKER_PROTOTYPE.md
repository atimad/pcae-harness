# Phase 88R — Permission Broker Prototype

## Summary

Phase 88R implements the first permission broker prototype: a read-only decision
aggregator that consumes PCAE governance evidence and returns a conservative broker
decision envelope.  The broker never executes commands, invokes backends, sends
prompts, writes storage, or grants real execution authorization.

## Command

```
pcae permission-broker evaluate \
  --requested-action <action> \
  [--requested-file <path>]...    \  # repeatable
  [--requested-command <cmd>]     \  # classified but never executed
  [--source-backend <backend>]    \  # context only
  [--commit-message <msg>]        \  # context only
  [--push-target <target>]        \  # context only
  [--health-passed]               \  # explicit evidence flag
  [--check-passed]                \
  [--doctor-passed]               \
  [--push-check-passed]           \
  [--tests-present]               \
  [--tests-passed]                \
  [--human-review-present]        \
  [--human-approval-present]      \
  [--accepted-risk-present]       \
  [--json]
```

## Architecture

### Core module: `src/pcae/core/permission_broker.py`

`build_permission_broker(repo_root, requested_action, ...)` returns the full
JSON envelope with a `broker` key containing the decision and all evidence.

Evidence is collected in two ways:

| Evidence | Collection method |
|---|---|
| Task contract | Internal: `_detect_task_contract` |
| Shell gate | Internal: `_classify_command` + `_decide` |
| Scope preflight | Internal: `build_scope_preflight` (when action+files given) |
| Doctor test-run | Subprocess: `pcae doctor test-run --json` (only if expensive test detected) |
| Health, check, doctor, push-check, tests | Explicit evidence flags from caller |
| Human review / approval / accepted risk | Explicit evidence flags from caller |

### Broker decision values (24)

Defined in `BPE_DECISIONS`:

| Decision | Meaning |
|---|---|
| `allow_preflight_only` | All evidence passes — not authorization |
| `requires_more_evidence` | Key evidence missing |
| `requires_human_review` | Human review gate not satisfied |
| `blocked_by_task_contract` | No active task for mutating action |
| `blocked_by_scope` | Scope preflight denied |
| `blocked_by_backend_policy` | Backend policy violation |
| `blocked_by_shell_gate` | Shell gate hard block |
| `blocked_by_force_push` | Force push detected |
| `blocked_by_raw_git_push` | Raw git push detected |
| `blocked_by_failed_health` | Explicit health failure |
| `blocked_by_failed_check` | Explicit check failure |
| `blocked_by_failed_doctor` | Explicit doctor failure |
| `blocked_by_failed_tests` | Explicit test failure |
| `blocked_by_push_check` | Push check failed |
| `blocked_by_test_run_lock` | Test run lock active |
| `blocked_by_lifecycle_state` | Wrong lifecycle state |
| `blocked_by_mutation_policy` | Mutation policy violation |
| `blocked_by_commit_policy` | Commit policy violation |
| `blocked_by_push_policy` | Push policy violation |
| `blocked_by_must_never_repeat` | Must-never-repeat constraint |
| `blocked_by_risk` | Risk threshold exceeded |
| `blocked_by_conflicting_evidence` | Conflicting evidence |
| `deny` | Generic denial |
| `unknown` | Unknown state |

### Decision priority chain

1. Shell gate hard blocks (force push > raw push > raw commit > destructive > other)
2. Explicit evidence failures (health > check > doctor > tests > push check)
3. Test run lock (when expensive test execution detected)
4. Missing active task for mutating actions
5. Scope preflight denial
6. Missing evidence → `requires_more_evidence`
7. Human review gate → `requires_human_review`
8. All clear → `allow_preflight_only`

### Performed / authorization flag invariant

14 flags are unconditionally `false` in every broker response, regardless of inputs:

`authorization_granted`, `execution_authorized`, `command_executed`,
`repo_mutation_performed`, `backend_invocation_performed`, `prompt_sent`,
`capture_performed`, `intake_performed`, `adoption_performed`, `commit_performed`,
`push_performed`, `raw_git_push_performed`, `force_push_performed`, `storage_written`

## Tests

`tests/test_permission_broker.py` — 150 tests.

- `TestEnvelopeInvariants` — JSON envelope shape
- `TestBrokerKeyInvariants` — broker key fields
- `TestPerformedFlagInvariants` — 14 flags × 4 scenarios = 56 parametrized tests
- `TestSafetyNotes` — safety note assertions
- `TestAllowPreflightOnly` — positive decision path
- `TestRequiresMoreEvidence` — missing evidence scenarios
- `TestRequiresHumanReview` — human gate
- `TestBlockedByTaskContract` — no active task
- `TestShellGateHardBlocks` — shell gate hard block pass-through
- `TestEvidenceFailures` — explicit evidence failure scenarios
- `TestScopePreflight` — scope preflight integration
- `TestBPEConstants` — constant validity
- `TestEvidenceProvided` — evidence passthrough
- `TestPermissionBrokerCLI` — subprocess CLI tests (slow/integration)

Fast-green count: 2,384 (was 2,234; +150 broker tests).

## Boundaries

The broker prototype does **not**:
- Execute shell commands
- Intercept the shell
- Invoke backends
- Send prompts
- Capture outputs
- Perform intake or adoption
- Mutate the repository
- Create commits (except normal phase commits)
- Push (except final governed `pcae push`)
- Grant real execution authorization
- Replace human review
- Override hard blocks
- Implement shell gate enforcement
- Install shell wrappers
- Write persistent broker state or cache

## Next phase

88S — Permission Broker Expansion (scope not yet defined).
