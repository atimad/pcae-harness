# Phase 94L — Backend Apply Readiness Validator

```
phase_name    = phase_94l_backend_apply_readiness_validator
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 94M — Backend Review CLI
```

## 1. Purpose

Implement a backend apply readiness validator for backend apply plans. PCAE can now classify whether an apply plan is ready, incomplete, blocked, or requires human review based on review artifacts, approval artifacts, output hash binding, allowed/forbidden files, rollback requirements, tests/check requirements, and hard blocks.

## 2. Non-Goals

This phase does NOT:
- Execute apply
- Parse patches for mutation
- Modify files
- Invoke backends
- Run subprocesses
- Run tests automatically
- Enforce anything
- Commit or push

## 3. Readiness Assessment Model

### BackendApplyReadinessAssessment

| Field | Type | Description |
|-------|------|-------------|
| `assessment_id` | str | Unique ID (ra-<uuid12>) |
| `apply_plan_id` | str | Referenced apply plan |
| `review_id` | str | Referenced review artifact |
| `approval_id` | str | Referenced approval artifact |
| `request_id` | str | Backend invocation request |
| `phase_id` | str | Active phase |
| `task_id` | str | Active task |
| `backend_id` | str | Target backend |
| `status` | str | ready/blocked/missing_evidence/needs_human_review/incomplete/untrusted |
| `apply_ready` | bool | All gates passed |
| `trust_level` | str | complete/partial/incomplete/untrusted |
| `output_hash_verified` | bool | Output hash matches plan |
| `approval_bound_to_output_hash` | bool | Approval confirms exact output hash |
| `review_state_valid` | bool | Review is approved/reviewed, not rejected |
| `output_quarantined` | bool | Output is quarantined |
| `output_not_applied` | bool | Output not previously applied |
| `allowed_files_present` | bool | No forbidden files detected |
| `forbidden_files_present` | bool | Plan has forbidden files defined |
| `operations_valid` | bool | No forbidden/high-risk/unknown/destructive ops |
| `rollback_ready` | bool | Rollback plan provided |
| `tests_defined` | bool | Tests to run defined |
| `check_required` | bool | Governance checks required |
| `hard_blocks` | list[str] | Non-overridable blocks |
| `missing_evidence` | list[str] | Required evidence not provided |
| `warnings` | list[str] | Advisory warnings |
| `recommended_action` | str | manual_apply_package_ready / blocked_hard / gather_evidence / needs_human_review / untrusted |
| `created_at_utc` | str | Assessment timestamp |
| `schema_version` | str | Schema version (1.0) |

### Statuses

| Status | Meaning |
|--------|---------|
| `ready` | All evidence complete, no hard blocks |
| `blocked` | Hard blocks present |
| `missing_evidence` | Required evidence missing |
| `needs_human_review` | Requires operator attention |
| `incomplete` | No assessment yet (default) |
| `untrusted` | Trust assessment failed |

## 4. Fail-Closed Behavior

The validator is fail-closed by default:

- Missing apply plan → blocked
- Missing review → missing_evidence
- Missing approval → missing_evidence
- Missing trust assessment → missing_evidence
- Missing operations → missing_evidence
- Missing rollback plan → missing_evidence
- Missing tests/check plan → missing_evidence
- `apply_ready=False` by default unless all evidence exists

## 5. Hard-Block Dominance

Hard blocks cannot be overridden:

- Approval output_hash mismatch → hard block
- Apply plan output_hash mismatch → hard block
- Output already applied → hard block
- Output not quarantined → hard block
- Forbidden file operation → hard block
- Unknown operation → hard block
- Delete/rename operation → hard block
- Trust assessment blocked → hard block
- Human approval cannot override hard blocks
- Accepted risk cannot override hard blocks
- Commit/push authorization remains separate and absent

## 6. Hash Binding Validation

- Approval must bind to the exact output_hash in the apply plan
- Output artifact metadata must match the plan's output_hash
- Mismatch → hard block (non-overridable)

## 7. File Scope Validation

- Allowed files list provides scope context (warns if empty)
- Forbidden files in proposed change set → hard block
- Operations with `forbidden=True` → hard block

## 8. Operation Safety

| Operation | Behavior |
|-----------|----------|
| `create_file` | Allowed if in scope |
| `modify_file` | Allowed if in scope |
| `delete_file` | Hard block (destructive) |
| `rename_file` | Hard block (destructive) |
| `manual_instruction` | Allowed, requires review |
| `unknown` | Hard block |
| `forbidden=True` | Hard block |

## 9. Distinction Between Apply-Ready and Apply-Executed

The validator may return `apply_ready=True` only if evidence is complete and no hard blocks exist. Even then, it does NOT:
- Apply changes to source files
- Mutate files
- Run tests
- Run `pcae check`
- Commit
- Push

The recommended action is `manual_apply_package_ready` — **never** "execute apply."

## 10. Persistence

Readiness assessments are persisted under:

```
.pcae/backend-apply-readiness/
  latest.json
  YYYYMMDD-HHMMSS-<assessment-id>.json
```

This directory is ignored by `.pcae/.gitignore`.

## 11. CLI

Read-only CLI subcommands:

```
pcae backend apply-readiness show --latest [--json]
pcae backend apply-readiness validate --plan <path> [--review <path>] [--approval <path>] [--output <path>] [--trust <path>] [--json]
```

- `show`: Displays the latest persisted assessment
- `validate`: Reads an apply plan JSON, validates readiness, persists and displays the assessment
- Both support `--json` for machine-readable output
- Neither executes apply, mutates files, or invokes backends

## 12. No-Go Conditions

- Apply execution: NOT implemented
- Patch parsing for mutation: NOT implemented
- File mutation: NOT implemented
- Real backend invocation: NOT implemented
- Subprocess execution: NOT implemented
- Network calls: NOT implemented
- Shell interception/wrappers: NOT implemented
- Command mediation: NOT implemented
- Telegram inbound commands: NOT implemented
- Remote shell: NOT implemented
- /run: NOT implemented
- Enforcement: NOT implemented
- Autonomous mutation: NOT implemented
- Automatic apply: NOT implemented
- Commit/push authorization: NOT implemented

## 13. Deferred Work

| Item | Target |
|------|--------|
| Backend Review CLI | 94M |
| Apply Plan CLI | 94N |
| Manual Apply Package | 94O |
| Apply Execution Design | 94P+ |
| Patch Parsing | Future |
| Real Backend Invocation | Future |
| Claude/DeepSeek/Codex/Qwen Adapters | Future (v2) |

## 14. Test Coverage (~40 tests)

- Complete evidence → apply_ready=True
- Missing approval → missing_evidence
- Missing review → missing_evidence
- Output hash mismatch → hard block
- Approval hash mismatch → hard block
- Forbidden file target → hard block
- Unknown operation → hard block
- Delete/rename operation blocked
- Output already applied → hard block
- Output not quarantined → hard block
- Missing rollback plan → missing_evidence
- Missing tests/check plan → missing_evidence
- Hard blocks dominate approval
- Accepted risk cannot override hard blocks
- apply_ready=False by default
- Readiness assessment serialization round-trip
- Readiness artifact persistence
- Latest readiness updated on new write
- No source files modified
- No patch parsing for mutation
- No backend/subprocess/network/shell execution
- Multi-part phase IDs preserved
- No secrets serialized

## 15. Files Changed

- `src/pcae/core/backend_invocations.py` — Added BackendApplyReadinessAssessment model, validate_backend_apply_readiness(), persist_apply_readiness(), read_latest_apply_readiness()
- `src/pcae/commands/backend.py` — Added run_backend_apply_readiness_show(), run_backend_apply_readiness_validate()
- `src/pcae/cli.py` — Registered apply-readiness subcommands
- `tests/test_backend_invocations.py` — Added 40 tests (149 total backend tests)
- `.pcae/.gitignore` — Added backend-apply-readiness/ directory

---

*Phase 94L is validation-only. No apply execution, patch parsing, file mutation, backend invocation, subprocess, network, shell interception, wrappers, enforcement, autonomous mutation, or command execution was implemented.*
