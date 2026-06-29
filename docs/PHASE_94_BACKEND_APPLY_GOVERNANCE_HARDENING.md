# Phase 94P — Backend Apply Governance Hardening

## Overview

Phase 94P hardens the backend review/apply governance chain against negative cases,
stale artifacts, malformed artifacts, contradictory metadata, unsafe paths, unsafe
packages, and trust/reporting drift. No apply execution was implemented. No file
mutation outside `.pcae/` artifact directories was performed.

## Boundary

| Constraint | Status |
|------------|--------|
| No apply execution | ✅ enforced |
| No patch parsing for mutation | ✅ enforced |
| No file mutation outside artifact dirs | ✅ enforced |
| No backend invocation | ✅ enforced |
| No subprocess | ✅ enforced |
| No network | ✅ enforced |
| No automatic tests | ✅ enforced |
| No automatic pcae check | ✅ enforced |
| No commit/push authorization | ✅ enforced |
| No real AI backend calls | ✅ enforced |

## New Validation Functions

All defined in `src/pcae/core/backend_invocations.py` (Phase 94P section).

### `validate_operation_path(path, *, forbidden_files, forbidden_patterns)`

Validates a single operation target path for safety. Returns a list of hard-block
reason strings. Empty list means safe.

| Check | Hard-block reason |
|-------|------------------|
| Empty / whitespace-only path | `empty_target_path` |
| Absolute path (starts with `/`) | `absolute_path:<path>` |
| Parent traversal (`..` in components) | `parent_traversal_path:<path>` |
| Matches forbidden pattern (`.env`, `.pcae/session.json`, etc.) | `forbidden_path_pattern:<path>` |
| Matches `forbidden_files` list | `forbidden_file:<path>` |

### `validate_operations_list(operations, *, forbidden_files)`

Validates a list of `ApplyOperation` objects for path safety and duplicates.

| Check | Result |
|-------|--------|
| Each path via `validate_operation_path()` | Hard block |
| Delete / Rename operation | Hard block `destructive_op` |
| Unknown operation | Hard block `unknown_operation` |
| Same path, different op types | Hard block `conflicting_operations` |
| Same path, same op type | Warning `duplicate_operation` |

### `validate_hash_chain(...)`

Validates `output_hash` and `request_id` chain across all evidence artifacts.
Any mismatch → hard block. Human approval cannot override. Accepted risk cannot override.

| Pair | Hard-block reason |
|------|-----------------|
| review ↔ approval output_hash | `review_approval_output_hash_mismatch` |
| review ↔ approval request_id | `review_approval_request_id_mismatch` |
| review ↔ plan output_hash | `review_plan_output_hash_mismatch` |
| review ↔ plan request_id | `review_plan_request_id_mismatch` |
| approval ↔ plan output_hash | `approval_plan_output_hash_mismatch` |
| plan ↔ package output_hash | `plan_package_output_hash_mismatch` |
| plan ↔ package request_id | `plan_package_request_id_mismatch` |
| plan ↔ package apply_plan_id | `plan_package_apply_plan_id_mismatch` |
| assessment ↔ package assessment_id | `assessment_package_id_mismatch` |

### `validate_artifact_freshness(artifact, *, expected_*)`

Validates that a loaded artifact dict is non-null, non-empty, and consistent with
expected identifiers. Fail-closed on `None` or `{}`.

| Input | Result |
|-------|--------|
| `None` | Hard block `<label>_missing` |
| Empty dict `{}` or non-dict | Hard block `<label>_malformed` |
| `output_hash` mismatch | Hard block `<label>_output_hash_mismatch` |
| `output_hash` present in expected but absent in artifact | Missing evidence |
| `request_id` mismatch | Hard block `<label>_request_id_mismatch` |
| `phase_id` mismatch (if non-empty) | Hard block `<label>_phase_id_mismatch` |

### `read_artifact_json_safe(path)`

Reads a JSON file, returning `None` on any error (missing file, invalid JSON, non-dict).
Never raises. Never mutates.

### `ApplyOperation.path_hard_blocks(*, forbidden_files)`

New method on `ApplyOperation`. Returns hard-block reasons for the operation's target
path. Separate from `validate()` so callers can collect hard blocks without raising.
Skips path checks for `manual_instruction` and `unknown` operations.

## Strengthened Existing Functions

### `approve_review()` — reject already-rejected reviews

```python
def approve_review(review, operator, reason):
    if review.rejected or review.review_state == REVIEW_REJECTED:
        raise ValueError("Cannot approve: review is already rejected")
    ...
```

### `create_apply_plan()` — path safety and duplicate detection

- Uses `op.path_hard_blocks()` on each operation to collect absolute-path and
  traversal-path hard blocks
- Detects duplicate operations (same path, same type → warning)
- Detects conflicting operations (same path, different types → hard block)

## Artifact Freshness Rules

| Rule | Enforcement |
|------|------------|
| `latest.json` absent → fail closed, return `None` | All `read_latest_*` functions |
| `latest.json` malformed → return `None` | `read_artifact_json_safe()` |
| `output_hash` mismatch against expected → hard block | `validate_artifact_freshness()` |
| `request_id` mismatch against expected → hard block | `validate_artifact_freshness()` |
| `phase_id` mismatch against expected → hard block | `validate_artifact_freshness()` |

## Hash/Request Binding Rules

1. Every hash comparison is symmetric and non-empty guarded — empty hashes skip the check.
2. Hash mismatches produce hard blocks, not warnings.
3. Hard blocks cannot be overridden by human approval or accepted risk.
4. The chain is: review → approval → plan → assessment → package.
5. Any broken link in the chain is a hard block.

## State-Transition Rules

| Rule | Enforcement |
|------|------------|
| Rejected review cannot be approved | `approve_review()` raises ValueError |
| Hard blocks prevent approval | `approve_review()` raises ValueError |
| Approval does not set `apply_ready` | `ReviewArtifact.apply_ready` stays False |
| `apply_ready` does not imply `applied` | No `applied` state in model |
| `applied`, `apply_failed`, `rolled_back` not in `VALID_REVIEW_STATES` | Verified in tests |
| `apply_ready=True` + `hard_blocks` → validation error | `ApplyPlan.validate()` |

## Path / Operation Safety Rules

| Rule | Enforcement |
|------|------------|
| Empty target path → hard block | `validate_operation_path()` |
| Absolute path → hard block | `validate_operation_path()`, `create_apply_plan()` |
| Parent traversal (`../`) → hard block | `validate_operation_path()`, `create_apply_plan()` |
| Forbidden file → hard block | `validate_operation_path()`, `create_apply_plan()` |
| Delete operation → hard block | `validate_operations_list()` |
| Rename operation → hard block | `validate_operations_list()` |
| Unknown operation → hard block | `validate_operations_list()` |
| Conflicting ops same path → hard block | `validate_operations_list()`, `create_apply_plan()` |
| Duplicate ops same path → warning | `validate_operations_list()`, `create_apply_plan()` |

## Manual Package Safety Rules

| Rule | Enforcement |
|------|------------|
| Hard blocks from plan included in package | `create_backend_manual_apply_package()` |
| Hard blocks from assessment included (deduplicated) | `create_backend_manual_apply_package()` |
| Hard blocks visible in `to_dict()` | `BackendManualApplyPackage.to_dict()` |
| Hard blocks visible in `render_markdown()` | `BackendManualApplyPackage.render_markdown()` |
| `commit_authorized`, `push_authorized` never in `to_dict()` | Verified in tests |
| `backend_invoked` never in `to_dict()` | Verified in tests |
| `no_execution_performed=True` always | Hard default, verified in tests |
| `tests_to_run` preserved as advisory, not executed | Verified in tests |
| `checks_to_run` preserved as advisory, not executed | Verified in tests |
| No raw prompt/output body in package | Verified in tests |

## CLI Failure Modes

| Scenario | Behavior |
|----------|----------|
| `show --latest` with no artifacts | Non-zero exit, clean error message |
| `show --latest --json` with no artifacts | Non-zero exit, `{"error": "..."}` |
| `create` with missing required args | Non-zero exit, usage error |
| `create` with high-risk op | Exit 0, plan has `hard_blocks` in JSON |
| `validate` plan not ready | Exit 1, assessment has `hard_blocks` |
| Any command with secrets | Secrets never printed |
| Any command | Never prints raw prompt/output body |

## Test-Infrastructure Hardening

Added `addopts = "--dist=loadfile"` to `pyproject.toml`. This ensures that CLI tests
from the same file (which share `.pcae/` artifact state) run in the same pytest-xdist
worker, preventing state-contamination races under `-n auto`.

## Deferred Work

The following items remain out of scope for 94P and are deferred to future phases:

| Item | Target Phase |
|------|-------------|
| End-to-end mock demo of full review/approve/plan/assess/package flow | 94Q |
| Real adapter design and preflight | TBD |
| Real adapter artifact-only invocation | TBD |
| Apply-plan expiry / freshness timeout enforcement | TBD |
| CLI `--review-id` / `--plan-id` for selecting non-latest artifacts | TBD |
| Approval expiry check | TBD |
| Rollback plan artifact model | TBD |

## Test Coverage Summary

**Model tests added** (`tests/test_backend_invocations.py`, ~85 new tests, classes `Test94P*`):
- `Test94PArtifactFreshness` — `validate_artifact_freshness()`: None, empty, mismatch, match
- `Test94PReadArtifactJsonSafe` — missing file, malformed JSON, non-dict, valid, empty
- `Test94PValidateOperationPath` — empty, absolute, traversal, forbidden, safe paths
- `Test94PValidateOperationsList` — empty, safe, duplicate, conflict, destructive, unknown, absolute, traversal, forbidden
- `Test94PHashChain` — all 7 mismatch combinations, empty hash skip, full-chain pass
- `Test94PStateTransition` — rejected-can't-approve, hard-blocks-prevent-approval, approval-not-apply-ready, apply-ready-not-applied, package-not-apply-ready, approved-not-apply-ready, future states not in VALID_REVIEW_STATES, hard-blocks-with-apply-ready, rejection-after-approval
- `Test94POperationPathHardening` — absolute/traversal in path_hard_blocks(), empty path validate(), absolute/traversal/duplicate/conflict/forbidden in create_apply_plan()
- `Test94PPackageHardening` — hard blocks from plan, hard blocks in markdown, hard blocks in to_dict, no commit/push auth, no backend invocation auth, tests advisory not executed, checks advisory not executed, no execution even when apply_ready, assessment hard blocks merged, no raw prompt, no secrets
- `Test94PValidateReadinessHardening` — hash mismatch blocks, accepted risk doesn't override, human approval doesn't override, missing plan blocks, rejected review blocks
- `Test94PNoExecutionGuarantees` — no subprocess, no network, no Telegram inbound, multi-part phase ID, deterministic JSON

**CLI tests added** (`tests/test_backend_cli.py`, ~27 new tests, classes `TestHardening*`):
- `TestHardeningReviewCLI` — show missing json, show missing text, create no secrets, create no execution flags, create no raw content, create structure deterministic
- `TestHardeningApplyPlanCLI` — show missing json, create high-risk hard blocks, create unknown hard blocks, create no secrets, validate no tests run, create no raw content
- `TestHardeningManualApplyPackageCLI` — show missing json, create hard blocks from plan, create hard blocks in markdown, create no commit/push auth, no execution true, no automatic tests, no automatic pcae check, create no secrets, show no raw content, json errors secret safe
- `TestHardeningNoSubprocess` — no subprocess/shell in commands, no network in commands, no subprocess in core, all dirs gitignored, no Telegram inbound
