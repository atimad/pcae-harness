# Phase 94Q — Backend Lifecycle End-to-End Mock Demo

```
phase_name    = phase_94q_backend_lifecycle_end_to_end_mock_demo
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 94Q.1 — Bootstrap Resume and Telegram Runtime Hardening
```

## 1. Purpose

Implement a complete end-to-end mock backend lifecycle demo that exercises the full governed backend flow — from planning through prompt capture, mock output capture, audit, trust/readiness, review, approval/rejection, apply plan, apply readiness, and final reporting — without real backend invocation and without applying changes.

The demo serves as:
- An integration smoke test for the full 94-series backend governance chain
- A demonstration artifact for operators to understand the lifecycle
- A safe, repeatable exercise that can be run without side effects

## 2. Non-Goals

This phase does NOT:
- Implement real backend invocation (Claude, DeepSeek, Codex, Qwen)
- Execute apply against source files
- Parse patches for mutation
- Modify files outside `.pcae/` artifact directories
- Run subprocesses, network calls, or shell commands
- Implement shell interception, wrappers, or command mediation
- Implement Telegram inbound commands, remote shell, or /run
- Implement enforcement, autonomous mutation, or automatic apply
- Implement automatic test execution or automatic `pcae check`
- Authorize commit or push
- Implement real AI backend calls of any kind
- Implement backend adapter design or real invocation preflight

## 3. Lifecycle Steps Exercised

The demo runs the following steps in sequence, all using the mock backend only:

| Step | Component | Phase | Artifact Created |
|------|-----------|-------|-----------------|
| 1 | Backend plan | 94E | `InvocationRequest` (in-memory) |
| 2 | Prompt artifact capture | 94C | `.pcae/backend-invocations/<ts>-<id>-prompt.md` |
| 3 | Mock backend output capture | 94F | `.pcae/backend-invocations/<ts>-<id>-output.md` |
| 4 | Backend invocation audit | 94G | `.pcae/backend-invocations/audit/<ts>-<id>.json` |
| 5 | Trust/readiness assessment | 94H | In-memory assessment dict |
| 6 | Review artifact creation | 94J | `.pcae/backend-reviews/<ts>-<id>.json` |
| 7 | Approval/rejection artifact | 94M | `.pcae/backend-reviews/<ts>-<id>.json` |
| 8 | Apply plan creation | 94K | `.pcae/backend-apply-plans/<ts>-<id>.json` |
| 9 | Apply readiness validation | 94L | `.pcae/backend-apply-readiness/<ts>-<id>.json` |
| 10 | Demo summary artifact | 94Q | `.pcae/backend-lifecycle-demos/<ts>-<id>.json` |

All steps use mock backend only. No real backend is invoked at any point.

## 4. Demo Artifact Model

### BackendLifecycleDemo

Persisted under `.pcae/backend-lifecycle-demos/` (gitignored).

| Field | Type | Description |
|-------|------|-------------|
| `demo_id` | str | Unique ID (`demo-<uuid12>`) |
| `phase_id` | str | Active phase ID |
| `task_id` | str | Active task ID |
| `backend_id` | str | Backend used (always `mock`) |
| `request_id` | str | Invocation request ID |
| `prompt_artifact_path` | str | Path to persisted prompt artifact |
| `prompt_hash` | str | SHA-256 of prompt text (redacted in demo) |
| `output_artifact_path` | str | Path to persisted output artifact |
| `output_hash` | str | SHA-256 of output text |
| `audit_id` | str | Audit record ID |
| `trust_assessment_id` | str | Trust assessment ID |
| `review_id` | str | Review artifact ID |
| `approval_id` | str | Approval artifact ID (empty if rejected) |
| `rejection_id` | str | Rejection artifact ID (empty if approved) |
| `apply_plan_id` | str | Apply plan ID |
| `apply_readiness_assessment_id` | str | Readiness assessment ID |
| `lifecycle_status` | str | `completed`, `blocked`, `partial`, or `failed` |
| `hard_blocks` | list[str] | Non-overridable hard blocks |
| `missing_evidence` | list[str] | Required evidence not provided |
| `warnings` | list[str] | Advisory warnings |
| `no_real_backend_invoked` | bool | Always `True` |
| `no_apply_execution` | bool | Always `True` |
| `no_file_mutation` | bool | Always `True` |
| `no_subprocess` | bool | Always `True` |
| `no_network` | bool | Always `True` |
| `no_shell_interception` | bool | Always `True` |
| `created_at_utc` | str | ISO 8601 timestamp |
| `schema_version` | str | `"1.0"` |

### Lifecycle Statuses

| Status | Meaning |
|--------|---------|
| `completed` | All artifacts created, no hard blocks, no missing evidence |
| `blocked` | Hard blocks present — apply not permitted |
| `partial` | Missing evidence — some steps incomplete |
| `failed` | Demo encountered an unexpected error |

## 5. CLI Behavior

### `pcae backend demo mock-lifecycle [--json] [--negative]`

Runs a complete end-to-end mock lifecycle demo. Uses mock backend only.

- `--json`: Output machine-readable JSON
- `--negative`: Exercise negative path (forbidden path → blocked lifecycle)
- `--phase-id`: Override phase ID (default: `94Q`)
- `--task-id`: Override task ID (default: auto-generated)

The command:
- Uses mock backend only
- Produces all lifecycle artifacts
- Prints compact artifact IDs and statuses
- Never prints raw secrets
- Never applies output
- Never mutates source files
- Never invokes real AI backends
- Never runs subprocess/network/shell commands
- Never runs tests automatically
- Never runs `pcae check` automatically

### `pcae backend demo show --latest [--json]`

Shows the latest lifecycle demo summary. Read-only.

- `--latest`: Show latest demo (default)
- `--json`: Output machine-readable JSON
- Returns non-zero exit with error message when no demo exists

## 6. Negative Demo Path

When `--negative` is specified:

1. A forbidden file path (`.env`) is targeted
2. The review gets a hard block (`forbidden_path_pattern:.env`)
3. Approval is attempted but blocked by hard blocks
4. Review is rejected instead of approved
5. Apply plan has hard blocks
6. Apply readiness assessment is `blocked`
7. Demo lifecycle status is `blocked`

The negative path still:
- Does not mutate files
- Does not invoke real backends
- Does not execute apply
- Does not run subprocess/network/shell

## 7. Safety Boundaries

| Boundary | Enforced |
|----------|----------|
| No real backend invocation | ✅ Always |
| No apply execution | ✅ Always |
| No file mutation outside `.pcae/` | ✅ Always |
| No subprocess execution | ✅ Always |
| No network calls | ✅ Always |
| No shell interception/wrappers | ✅ Always |
| No Telegram inbound | ✅ Always |
| No remote shell / /run | ✅ Always |
| No enforcement | ✅ Always |
| No autonomous mutation | ✅ Always |
| No automatic apply | ✅ Always |
| No automatic tests | ✅ Always |
| No automatic `pcae check` | ✅ Always |
| No commit/push authorization | ✅ Always |
| Output remains quarantined | ✅ Always |
| No raw secrets in demo output | ✅ Always |

## 8. Successful Demo Criteria

A successful demo (`lifecycle_status: completed` or `partial`) requires:

1. All 10 lifecycle steps exercised
2. All expected artifact IDs created (request, audit, trust, review, approval/rejection, apply plan, readiness assessment)
3. Output hash preserved through the artifact chain
4. Request ID preserved through the artifact chain
5. Output remains quarantined (`quarantined=True`, `applied_to_repo=False`)
6. Apply plan created but `apply_ready=False` (rollback/tests not satisfied in mock scenario)
7. Apply readiness generated but no apply executed
8. No hard blocks on the happy path
9. No real backend invoked
10. No subprocess/network/shell execution

Note: The happy-path demo may report `partial` status due to missing rollback plan and tests — this is expected behavior for the mock scenario where full rollback/test plans are not supplied.

## 9. Relationship to Existing Components

| Component | Phase | Role in Demo |
|-----------|-------|-------------|
| Backend registry | 94B | Provides mock backend definition |
| Invocation request | 94B | Request metadata for the demo |
| Prompt capture | 94C | Captures and redacts prompt text |
| Output capture | 94D | Captures and quarantines mock output |
| Mock backend invocation | 94F | Generates deterministic mock output |
| Audit trail | 94G | Records invocation evidence |
| Trust/readiness gate | 94H | Assesses lifecycle trust |
| Review state model | 94J | Creates review artifact |
| Review/approval | 94I/94M | Approves or rejects based on evidence |
| Apply plan model | 94K | Creates apply plan with operations |
| Apply readiness validator | 94L | Validates readiness, fail-closed |
| Governance hardening | 94P | Path safety, hash chains, freshness |

## 10. Deferred Work

| Item | Target Phase |
|------|-------------|
| Real backend adapter design | 94R |
| Real backend invocation preflight | TBD |
| Artifact-only real backend invocation | TBD |
| Apply execution | TBD (future, gated) |
| Patch parsing for mutation | Future |
| Commit/push authorization | Future (separate governance) |
| Claude/DeepSeek/Codex/Qwen adapters | Future (v2 pluggability) |
| Telegram inbound commands | Future (v2+) |
| Bootstrap resume hardening | 94Q.1 |
| Telegram runtime hardening | 94Q.1 |

## 11. Files Changed

- `src/pcae/core/backend_invocations.py` — Added `BackendLifecycleDemo` model (28 fields), `run_mock_lifecycle_demo()`, `persist_lifecycle_demo()`, `read_latest_lifecycle_demo()`, lifecycle status constants
- `src/pcae/commands/backend.py` — Added `run_backend_demo_mock_lifecycle()`, `run_backend_demo_show()`, fixed dead code (duplicate return)
- `src/pcae/cli.py` — Registered `pcae backend demo` subparser with `mock-lifecycle` and `show` commands
- `.pcae/.gitignore` — Added `backend-lifecycle-demos/`
- `tests/test_backend_invocations.py` — Added 41 tests (Test94QLifecycleDemoModel, Test94QHappyPathDemo, Test94QNegativePathDemo, Test94QDemoPersistence, Test94QNoExecutionGuarantees)
- `tests/test_backend_cli.py` — Added 20 tests (Test94QDemoCLIHappyPath, Test94QDemoCLINegativePath, Test94QDemoCLIShow, Test94QDemoCLISafety)

## 12. Test Coverage

**Model tests (41 new, 370 total):**
- `Test94QLifecycleDemoModel` (10 tests): validation, serialization, from_dict, deterministic JSON, no secrets
- `Test94QHappyPathDemo` (10 tests): all artifacts created, request ID chain, output hash chain, quarantine, no execution, no subprocess/network, no secrets, multi-part phase ID
- `Test94QNegativePathDemo` (6 tests): blocked status, hard blocks, rejection, no approval, no execution
- `Test94QDemoPersistence` (5 tests): persist/read round-trip, latest updated, absent returns None, latest.json created, timestamped files
- `Test94QNoExecutionGuarantees` (8 tests): no subprocess/network/Telegram in source, execution flags always True, mock-only backend

**CLI tests (20 new, 169 total):**
- `Test94QDemoCLIHappyPath` (4 tests): text output, JSON output, demo IDs, all steps present
- `Test94QDemoCLINegativePath` (5 tests): text output, rejection ID, JSON blocked status, hard blocks, no approval
- `Test94QDemoCLIShow` (4 tests): show text after lifecycle, show JSON, missing demo text, missing demo JSON
- `Test94QDemoCLISafety` (7 tests): no secrets in JSON, no raw prompt, text no secrets, no subprocess/network/Telegram in commands, gitignore entry

## 13. No-Go Confirmations

| Item | Status |
|------|--------|
| Real backend invocation | NOT implemented ✅ |
| Apply execution | NOT implemented ✅ |
| Patch parsing for mutation | NOT implemented ✅ |
| Source file mutation | NOT implemented ✅ |
| Subprocess execution | NOT implemented ✅ |
| Network calls | NOT implemented ✅ |
| Shell interception/wrappers | NOT implemented ✅ |
| Command mediation | NOT implemented ✅ |
| Telegram inbound commands | NOT implemented ✅ |
| Remote shell / /run | NOT implemented ✅ |
| Enforcement | NOT implemented ✅ |
| Autonomous mutation | NOT implemented ✅ |
| Automatic apply | NOT implemented ✅ |
| Automatic test execution | NOT implemented ✅ |
| Automatic pcae check | NOT implemented ✅ |
| Commit/push authorization | NOT implemented ✅ |
| Real AI backend calls | NOT implemented ✅ |

---

*Phase 94Q is a mock-only integration demo. No real backend invocation, apply execution, patch parsing, file mutation, subprocess, network, shell interception, enforcement, or autonomous mutation was implemented. The demo exercises the full governed backend lifecycle safely and deterministically.*
