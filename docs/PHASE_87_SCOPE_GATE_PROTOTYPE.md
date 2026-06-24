# Phase 87 Scope Gate Prototype

## 1. Purpose

Document the scope gate prototype added to `pcae gate-dry-run [--json]`.
Evaluates file/action scope against task contract evidence in dry-run mode.

## 2. Scope

Implementation summary. Extends the gate dry-run evaluator with concrete
scope evaluation logic, optional CLI flags, and scope-specific tests.

## 3. Non-Goals

- Enforcing scope decisions.
- Authorizing mutation, commits, pushes, or backend invocation.
- Implementing permission broker, shell gate, or storage.

## 4. Command Behavior

```
pcae gate-dry-run --json
pcae gate-dry-run --json --requested-action <action> --requested-file <path>
```

The `--requested-action` and `--requested-file` flags are optional. When
provided, the scope_check_gate evaluates those files against the active
task contract. Without flags, a default evaluation runs using current state.

## 5. Scope Gate Model

The scope_check_gate now includes a `scope_evaluation` field with detailed
scope analysis results.

## 6. Scope Evaluation Fields

| Field | Type | Description |
|-------|------|-------------|
| `scope_status` | string | in_scope, out_of_scope, partially_in_scope, unknown, requires_human_review |
| `requested_files` | list | Files requested for evaluation |
| `allowed_files` | list | Patterns from task contract allowed files |
| `forbidden_files` | list | Patterns from task contract forbidden files |
| `matched_allowed_files` | list | Files matching allowed patterns |
| `matched_forbidden_files` | list | Files matching forbidden patterns |
| `unknown_files` | list | Files not matching any pattern |
| `task_contract_detected` | boolean | Whether a task contract was found |
| `task_contract_path` | string | Path to detected task contract |
| `evidence_sources` | list | Sources consulted |
| `scope_notes` | string | Additional context |

## 7. Requested Action Handling

| Action | Scope Gate Behavior |
|--------|-------------------|
| `read` | Evaluates scope, does not authorize |
| `source_mutation` | In-scope files → requires_human_review (not allow) |
| `test_mutation` | In-scope files → requires_human_review (not allow) |
| `docs_mutation` | In-scope files → requires_human_review (not allow) |
| `commit` | Requires human review regardless of scope |
| `push` | Requires human review regardless of scope |
| `backend_invocation` | Denied by scope gate |
| `prompt_send` | Denied by scope gate |
| `adoption` | Denied by scope gate |
| `storage_write` | Denied by scope gate |
| `shell_command` | Denied by scope gate |
| `unknown` | Requires more evidence |

## 8. Decision Mapping

| Scope Status | Decision |
|-------------|----------|
| `in_scope` (write action) | `requires_human_review` |
| `in_scope` (high-risk action) | `deny` |
| `in_scope` (other) | `requires_more_evidence` |
| `out_of_scope` | `blocked_by_scope` |
| `partially_in_scope` | `blocked_by_scope` |
| `unknown` | `requires_more_evidence` |
| no task contract | `deny` |

## 9. Reason Codes

scope_not_authorized, missing_task_contract, human_approval_required,
source_mutation_not_authorized, backend_invocation_not_authorized, etc.

## 10. Safety Guarantees

| Safety Note | Value |
|-------------|-------|
| `scope_gate_dry_run_only` | `true` |
| `scope_gate_does_not_authorize_mutation` | `true` |
| `scope_gate_does_not_authorize_commit` | `true` |
| `scope_gate_does_not_authorize_push` | `true` |
| `scope_gate_does_not_authorize_backend_invocation` | `true` |
| `scope_gate_does_not_authorize_shell_execution` | `true` |
| `scope_in_scope_is_not_overall_authorization` | `true` |

In-scope is necessary but not sufficient. authorization_granted remains false.

## 11. No-Write/No-Storage Behavior

- No files written
- No cache created
- No .pcae storage created
- No scope state files created

## 12. Test Coverage

22 tests in `tests/test_scope_gate.py`:

Default works, scope_check_gate present, has scope_evaluation, required fields,
valid default, read allowed file, source mutation allowed file, source mutation
forbidden file, test/docs/commit/push/backend/shell/storage mutation does not
authorize, unknown action requires evidence, out-of-scope blocked, all gates
auth false, envelope safety flags, no cache created, no repo mutation, existing
commands work.

## 13. Known Limitations

- Task contract parsing is simple pattern matching (fnmatch)
- Does not support complex glob patterns or exclusion syntax
- Scope evaluation does not check git-tracked status of files
- In-scope does not mean authorized — other gates must also pass
- Only one task contract (first in tasks/active/) is evaluated

## 14. Recommended Next Phase

**87E — Backend Invocation Gate Dry-Run.**

---

scope_gate_prototype_name=phase_87_scope_gate_prototype
scope_gate_prototype_version=0.1
scope_gate_prototype_status=implemented
scope_gate_command=pcae gate-dry-run --json --requested-action <action> --requested-file <path>
tests_added=22
total_test_count=7173
read_only=true
enforcement_performed=false
authorization_granted=false
storage_created=false
backend_invocation_performed=false
recommended_next=87E
