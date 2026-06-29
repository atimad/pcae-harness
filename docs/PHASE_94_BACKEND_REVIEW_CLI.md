# Phase 94M — Backend Review CLI

```
phase_name    = phase_94m_backend_review_cli
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 94N — Backend Apply Plan CLI
```

## 1. Purpose

Implement a safe Backend Review CLI that exposes the review state model from Phase 94J through CLI commands. Operators can create, view, approve, and reject review artifacts without triggering any apply execution, file mutation, backend invocation, or enforcement.

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
- Authorize commit or push

## 3. Commands Added

```
pcae backend review show --latest [--json]
pcae backend review create --request-id <id> --output-hash <hash> [--phase-id <phase>] [--backend <id>] [--output-artifact-path <path>] [--prompt-hash <hash>] [--prompt-artifact-path <path>] [--json]
pcae backend review approve --review-id <id> --output-hash <hash> --operator <name> --reason <text> [--json]
pcae backend review reject --review-id <id> --output-hash <hash> --operator <name> --reason <text> [--json]
```

## 4. Review Create Behavior

- Creates a `ReviewArtifact` with safe defaults: `approved_for_apply=False`, `apply_ready=False`, `rejected=False`
- Sets initial state to `review_pending`
- Binds to `request_id` and `output_hash`
- Persists to `.pcae/backend-reviews/` with timestamped filename
- Updates `latest.json` pointer
- Does not apply anything, mutate files, invoke backends, or run subprocesses

## 5. Approval Behavior

- Creates an `ApprovalArtifact` bound to exact `review_id` and `output_hash`
- Requires `--operator` and `--reason`
- **Hard blocks prevent effective approval**: if `hard_blocks` is non-empty in the review, approval is rejected with a hard-block error
- **Accepted risk cannot override hard blocks**: no `--accept-risk` bypass exists
- Approval sets `review_state = approved_for_apply` and `approved_for_apply = True`
- Approval does NOT execute apply
- Approval does NOT authorize commit or push
- Output remains quarantined after approval
- `apply_ready` remains controlled by the apply readiness validator (94L), not approval alone
- Conflict guard: cannot approve a rejected review

## 6. Rejection Behavior

- Creates a `RejectionArtifact` bound to exact `review_id` and `output_hash`
- Requires `--operator` and `--reason`
- Sets `review_state = rejected` and `rejected = True`
- Prevents same artifact from being both approved and rejected (conflict guard on CLI)
- Does not modify source files
- Output remains quarantined

## 7. Hash Binding

- All review/approval/rejection operations require exact `--output-hash` matching the stored review
- Mismatch → immediate hard-block error, non-zero exit code
- Review ID mismatch → immediate error
- Hash binding ensures review artifacts cannot be reused across different outputs

## 8. Hard-Block Dominance

- Hard blocks in the review artifact prevent effective approval
- No human operator, no accepted risk flag, no reason string can override a hard block
- Hard blocks include: `output_not_quarantined`, `output_already_applied`, `forbidden_file:*`, `approval_has_hard_blocks`, `output_hash_mismatch`, etc.
- Hard block errors return non-zero exit code and `"hard_block": true` in JSON output

## 9. Safe Defaults

| Field | Default | Notes |
|-------|---------|-------|
| `approved_for_apply` | `False` | Never set to True unless explicitly approved |
| `apply_ready` | `False` | Not set by CLI; controlled by 94L validator |
| `rejected` | `False` | Set to True only on explicit rejection |
| `review_state` | `review_pending` | Changed by approve/reject |
| `hard_blocks` | `[]` | Checked before any approval |

## 10. Artifact Persistence

Review artifacts persist under:
```
.pcae/backend-reviews/
  latest.json                                   # latest review state
  YYYYMMDD-HHMMSS-<review-id>.json             # timestamped review
  YYYYMMDD-HHMMSS-<approval-id>.json           # timestamped approval
  YYYYMMDD-HHMMSS-<rejection-id>.json          # timestamped rejection
```

This directory is listed in `.pcae/.gitignore` and does not create tracked dirty files.

## 11. JSON Output

All review commands support `--json` output:
- Deterministic field structure
- No raw prompt or output content
- No secrets (no API keys, tokens, credentials)
- Includes IDs, state, decision, output_hash, artifact paths, safe defaults, and no-execution flags
- Multi-part phase IDs preserved (e.g., `94M.1.2`)

## 12. Report Consistency

`show --latest` displays metadata only — no raw prompt or output content is printed regardless of what was captured.

## 13. No-Go Conditions

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

## 14. Deferred Work

| Item | Target |
|------|--------|
| Apply Plan CLI | 94N |
| Manual Apply Package | 94O |
| Apply Execution Design | 94P+ |
| Patch Parsing | Future |
| Real Backend Invocation | Future |
| Claude/DeepSeek/Codex/Qwen Adapters | Future (v2) |

## 15. Files Changed

- `src/pcae/core/backend_invocations.py` — Added `RejectionArtifact.to_dict()`, `RejectionArtifact.validate()`, `persist_approval()`, `persist_rejection()`
- `src/pcae/commands/backend.py` — Added `run_backend_review_show()`, `run_backend_review_create()`, `run_backend_review_approve()`, `run_backend_review_reject()`
- `src/pcae/cli.py` — Registered `pcae backend review` subcommand group
- `tests/test_backend_invocations.py` — Added 17 tests (166 total backend model tests)
- `tests/test_backend_cli.py` — Added 29 tests (50 total backend CLI tests)
- `docs/PHASE_94_BACKEND_REVIEW_CLI.md` — This document

---

*Phase 94M is CLI-only. No apply execution, patch parsing, file mutation, backend invocation, subprocess, network, shell interception, wrappers, enforcement, autonomous mutation, or command execution was implemented.*
