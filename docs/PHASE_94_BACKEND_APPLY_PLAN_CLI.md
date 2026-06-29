# Phase 94N — Backend Apply Plan CLI

```
phase_name    = phase_94n_backend_apply_plan_cli
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 94O — Backend Manual Apply Package
```

## 1. Purpose

Implement a safe Backend Apply Plan CLI that exposes the apply plan model from Phase 94K and the readiness validator from Phase 94L through CLI commands. Operators can create, view, and validate apply plan artifacts without triggering any apply execution, patch parsing, file mutation, backend invocation, or enforcement.

## 2. Non-Goals

This phase does NOT:
- Execute apply
- Parse patches for mutation
- Modify source files
- Invoke real AI backends
- Run subprocesses
- Make network calls
- Implement shell interception or wrappers
- Accept inbound Telegram commands
- Run tests automatically
- Run `pcae check` automatically
- Authorize commit or push

## 3. Commands Added

```
pcae backend apply-plan show --latest [--json]
pcae backend apply-plan create --review-id <id> --output-hash <hash> [--approval-id <id>] [--request-id <id>] [--phase-id <phase>] [--backend <id>] [--operation TYPE:TARGET] [--operations-file <path>] [--json]
pcae backend apply-plan validate [--plan <path>] [--review <path>] [--approval <path>] [--json]
```

## 4. Show Behavior

- Shows latest apply plan metadata only
- Never prints raw backend output or prompt content
- Handles missing apply plan directory or latest plan cleanly (non-zero exit, error JSON)
- Supports `--json` for machine-readable output
- Fields shown: plan_id, review_id, approval_id, request_id, phase_id, backend_id, output_hash, apply_ready, rollback_required, check_required, risk_level, operations (type:target), hard_blocks, missing_evidence, warnings, created_at_utc

## 5. Create Behavior

- Creates an `ApplyPlan` artifact with safe defaults:
  - `apply_ready=False` — never set True by create alone
  - `rollback_required=True`
  - `check_required=True`
- Binds to `review_id`, `approval_id` (if provided), `request_id`, and `output_hash`
- Accepts descriptive operations via `--operation TYPE:TARGET` (repeatable) or `--operations-file <path>` (JSON array)
- Operations are metadata only — no patch parsing, no file mutation
- Sets hard block for high-risk operation types (`delete_file`, `rename_file`, `unknown`)
- Sets warning for unrecognized operation types
- Missing `approval_id` goes to `missing_evidence`, not hard block
- Persists to `.pcae/backend-apply-plans/` with timestamped filename
- Updates `latest.json` pointer
- JSON output includes `no_execution`, `no_apply`, `no_patch_parsing`, `no_source_files_modified` flags

## 6. Validate Behavior

- Reads latest apply plan (or `--plan <path>` if specified)
- Optionally accepts `--review <path>` and `--approval <path>` for richer evidence
- Calls `validate_backend_apply_readiness()` — fail-closed validator from Phase 94L
- Produces a `BackendApplyReadinessAssessment`
- Persists the assessment to `.pcae/backend-apply-readiness/`
- Clearly states: `ready` / `blocked` / `missing_evidence` / `needs_human_review` / `incomplete` / `untrusted`
- Returns exit code 0 only when `apply_ready=True`; exit code 1 otherwise
- Does NOT execute apply
- Does NOT run tests automatically
- Does NOT run `pcae check`
- Does NOT mutate source files
- JSON output includes `no_execution`, `no_apply`, `no_tests_run`, `no_pcae_check_run`, `no_source_files_modified` flags
- `recommended_action` is never `execute` — always `manual_apply_package_ready`, `blocked_hard`, `gather_evidence`, `needs_human_review`, or `untrusted`

## 7. Descriptive Operation Metadata

Operations are descriptive metadata, not executable instructions:

| Operation Type | Hard Block? | Notes |
|---------------|------------|-------|
| `manual_instruction` | No | Fully safe; operator-interpreted |
| `create_file` | No | Allowed if in scope |
| `modify_file` | No | Allowed if in scope |
| `delete_file` | Yes (`high_risk_op`) | Destructive — hard blocked |
| `rename_file` | Yes (`high_risk_op`) | Destructive — hard blocked |
| `unknown` | Yes (`high_risk_op`) | Unknown type — hard blocked |
| Other | Warning | Added to `warnings`, type mapped to `unknown` |

Operations format: `TYPE:TARGET` (e.g., `manual_instruction:src/foo.py`). Target path is descriptive only — no file is touched.

## 8. Hash Binding

- Create binds `output_hash` from `--output-hash`
- Validate checks that the plan's `output_hash` is present (absence → hard block)
- Approval binding (via `--approval`) cross-checks `output_hash` against plan during validation

## 9. Hard-Block Dominance

Hard blocks cannot be overridden by any operator, accepted risk, or approval:
- `apply_plan_missing` — no plan provided
- `output_hash_missing` — plan has no output hash
- `high_risk_op:delete_file:*` — destructive file operation
- `high_risk_op:rename_file:*` — rename operation
- `high_risk_op:unknown:*` — unknown operation type
- `forbidden_file:*` — file outside allowed scope
- `approval_has_hard_blocks` — approval itself carries hard blocks
- `output_hash_mismatch` — plan/approval/review hash mismatch
- `output_already_applied` — output not quarantined

Hard blocks cause `apply_ready=False` and `status=blocked` regardless of other evidence.

## 10. Safe Defaults

| Field | Default | Notes |
|-------|---------|-------|
| `apply_ready` | `False` | Never set True by create; only by validator when all evidence passes |
| `rollback_required` | `True` | Always required |
| `check_required` | `True` | Always required |
| `hard_blocks` | `[]` | Populated by high-risk/forbidden ops |
| `missing_evidence` | `[]` | Populated by missing approval, rollback plan, operations |
| `approved_for_apply` | N/A | Controlled by approval artifact (94M), not apply plan |

## 11. Artifact Persistence

```
.pcae/backend-apply-plans/
  latest.json                                   # latest apply plan
  YYYYMMDD-HHMMSS-<plan-id>.json               # timestamped plan

.pcae/backend-apply-readiness/
  latest.json                                   # latest readiness assessment
  YYYYMMDD-HHMMSS-<assessment-id>.json         # timestamped assessment
```

Both directories are listed in `.pcae/.gitignore` and do not create tracked dirty files.

## 12. JSON Output

All apply-plan commands support `--json` output:
- Deterministic field structure
- No raw prompt or output content
- No secrets (no API keys, tokens, credentials)
- Includes IDs, output_hash, operations metadata, hard_blocks, missing_evidence, warnings, readiness status, safe defaults
- Multi-part phase IDs preserved (e.g., `94N.1.2`)

## 13. Model Addition — read_latest_apply_plan()

Added `read_latest_apply_plan()` to `src/pcae/core/backend_invocations.py`:
- Reads `.pcae/backend-apply-plans/latest.json`
- Deserializes `ApplyPlan` and nested `ApplyOperation` objects
- Returns `None` if absent or unreadable
- Used by both `show` and `validate` when no `--plan` path provided

## 14. No-Go Conditions

| Capability | Status |
|-----------|--------|
| Apply execution | NOT implemented |
| Patch parsing for mutation | NOT implemented |
| Source file mutation | NOT implemented |
| Real backend invocation | NOT implemented |
| Subprocess execution | NOT implemented |
| Network calls | NOT implemented |
| Shell interception/wrappers | NOT implemented |
| Telegram inbound commands | NOT implemented |
| Remote shell / /run | NOT implemented |
| Enforcement | NOT implemented |
| Autonomous mutation | NOT implemented |
| Automatic apply | NOT implemented |
| Commit/push authorization | NOT implemented |
| Real AI backend calls | NOT implemented |
| Automatic test execution | NOT implemented |
| Automatic pcae check | NOT implemented |

## 15. Deferred Work

| Item | Target |
|------|--------|
| Manual Apply Package | 94O |
| Apply Governance Hardening | 94P |
| End-to-End Mock Demo | Future |
| Real Adapter Design | Future |
| Claude/DeepSeek/Codex/Qwen Adapters | Future (v2) |
| Patch Parsing | Future (gated by governance design) |
| Apply Execution | Future (gated by governance design) |

## 16. Files Changed

- `src/pcae/core/backend_invocations.py` — Added `read_latest_apply_plan()`
- `src/pcae/commands/backend.py` — Added `run_backend_apply_plan_show()`, `run_backend_apply_plan_create()`, `run_backend_apply_plan_validate()`
- `src/pcae/cli.py` — Registered `pcae backend apply-plan` subcommand group
- `tests/test_backend_invocations.py` — Added 29 tests (195 total backend model tests)
- `tests/test_backend_cli.py` — Added 42 tests (92 total backend CLI tests)
- `docs/PHASE_94_BACKEND_APPLY_PLAN_CLI.md` — This document

---

*Phase 94N is CLI-only. No apply execution, patch parsing, file mutation, backend invocation, subprocess, network, shell interception, wrappers, enforcement, autonomous mutation, automatic apply, automatic test execution, or real AI backend calls were implemented.*
