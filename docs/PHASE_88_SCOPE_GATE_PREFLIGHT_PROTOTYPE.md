# Phase 88B Scope Gate Preflight Prototype

## 1. Purpose

Implement the first narrow scope gate preflight prototype: an explicit command
that evaluates whether a requested action and requested files are permitted by
the active task contract scope. Returns structured JSON with a preflight
decision, reason codes, scope matches, evidence, and safety notes.

## 2. Scope

88B implements:

- `pcae preflight scope` command with `--json`, `--requested-action`, and
  `--requested-file` arguments.
- Core preflight evaluator in `src/pcae/core/scope_preflight.py`.
- Command runner in `src/pcae/commands/scope_preflight.py`.
- CLI registration in `src/pcae/cli.py`.
- 66 tests in `tests/test_scope_preflight.py`.

## 3. Non-Goals

- Shell interception.
- Permission broker implementation.
- Shell gate implementation.
- Backend invocation preflight.
- Mutation/adoption preflight beyond explicit scope evaluation.
- Commit/push preflight beyond explicit scope evaluation.
- Storage, cache, or `.pcae` persistent state.
- Wrapper scripts or shell config modification.
- Broad enforcement.

## 4. Relationship to 88A

Phase 88A (First Narrow Enforced Gate Boundary) designed the enforcement
boundary and selected `scope_gate_preflight` as the first candidate. 88B
implements the prototype command based on that design. 88B does not implement
enforcement interception — it provides an explicit command only.

## 5. Command Behavior

```
pcae preflight scope --json --requested-action ACTION [--requested-file PATH ...]
```

The command:

1. Reads the active task contract from `tasks/active/`.
2. Extracts allowed and forbidden file patterns.
3. Evaluates each requested file against allowed/forbidden scope.
4. Evaluates the requested action as known/unknown/scope-decidable.
5. Returns structured JSON with the preflight decision.
6. Does not mutate the repository.
7. Does not stage, commit, or push.
8. Does not invoke backends.
9. Does not write storage or cache.
10. Does not intercept shell commands.

## 6. JSON Output Model

### Envelope

| Field | Type |
|-------|------|
| `schema_version` | string |
| `generated_at` | string (ISO 8601) |
| `source_command` | string |
| `repository_root` | string |
| `preflight` | object |
| `warnings` | list[string] |
| `errors` | list[string] |
| `safety_notes` | object |

### Preflight Object

| Field | Type |
|-------|------|
| `preflight_type` | string |
| `requested_action` | string |
| `requested_files` | list[string] |
| `decision` | string |
| `reason_codes` | list[string] |
| `task_contract_detected` | boolean |
| `task_contract_path` | string or null |
| `lifecycle_state` | string |
| `allowed_files` | list[string] |
| `forbidden_files` | list[string] |
| `matched_allowed_files` | list[string] |
| `matched_forbidden_files` | list[string] |
| `unknown_files` | list[string] |
| `human_review_required` | boolean |
| `more_evidence_required` | boolean |
| `evidence_sources` | list[string] |
| `scope_notes` | string |
| `authorization_granted` | boolean (always false) |
| `execution_authorized` | boolean (always false) |
| `repo_mutation_performed` | boolean (always false) |
| `storage_written` | boolean (always false) |
| `backend_invocation_performed` | boolean (always false) |

## 7. Decision Values

| Decision | Meaning |
|----------|---------|
| `allow_preflight` | Scope check passed (not execution authorization) |
| `deny_preflight` | Scope check failed (conflicting scope) |
| `requires_human_review` | Human must review |
| `requires_more_evidence` | Evidence missing |
| `blocked_by_scope` | File out of scope |
| `blocked_by_lifecycle_state` | Lifecycle wrong |
| `blocked_by_missing_task_contract` | No contract |
| `blocked_by_must_never_repeat_control` | Hard constraint |
| `blocked_by_risk` | Active risk |
| `unknown` | Cannot determine; deny |

## 8. Reason Codes

- `scope_allowed`
- `scope_denied`
- `forbidden_file_requested`
- `file_outside_allowed_scope`
- `unknown_file_scope`
- `missing_task_contract`
- `lifecycle_state_not_ready`
- `human_review_required`
- `more_evidence_required`
- `unknown_action`
- `accepted_risk_not_mitigation`
- `must_never_repeat_control_applies`
- `preflight_only_not_execution_authorization`

## 9. Scope Matching Rules

1. Each requested file is matched against allowed_files and forbidden_files
   patterns from the active task contract.
2. Pattern matching uses exact match, fnmatch glob, and prefix match.
3. Forbidden match takes priority over allowed match.
4. Files matching neither allowed nor forbidden are classified as unknown.

## 10. Human Review Behavior

Human review is required for:

- Unknown action type.
- Not-scope-decidable actions (adoption, backend_invocation, commit, push,
  rollback, storage_write).
- Mixed allowed and unknown files.

## 11. Non-Authorizing Boundary

- `allow_preflight` does NOT mean `execution_authorized=true`.
- `allow_preflight` does NOT authorize backend invocation.
- `allow_preflight` does NOT authorize mutation by an agent.
- `allow_preflight` does NOT authorize commit or push.
- `allow_preflight` does NOT bypass pcae check, hooks, commit governance,
  push governance, or human review.
- `authorization_granted` is always `false`.
- `execution_authorized` is always `false`.

## 12. No-Write/No-Storage Behavior

The command:

- Does not create cache files.
- Does not create preflight state files.
- Does not create gate state files.
- Does not create broker state files.
- Does not create shell gate state files.
- Does not create `.pcae` persistent storage.
- Does not mutate requested files.
- Does not stage files.
- Does not commit.
- Does not push.

## 13. Safety Notes

All safety note values are `true`:

- `scope_preflight_only`
- `scope_preflight_does_not_intercept_shell`
- `scope_preflight_does_not_authorize_execution`
- `scope_preflight_does_not_invoke_backends`
- `scope_preflight_does_not_send_prompts`
- `scope_preflight_does_not_capture_outputs`
- `scope_preflight_does_not_perform_intake`
- `scope_preflight_does_not_perform_adoption`
- `scope_preflight_does_not_mutate_repo`
- `scope_preflight_does_not_commit`
- `scope_preflight_does_not_push`
- `scope_preflight_does_not_write_storage`
- `permission_broker_not_implemented`
- `shell_gate_not_implemented`
- `storage_not_implemented`

## 14. Test Coverage

66 tests in `tests/test_scope_preflight.py` covering:

- Command exists and returns valid JSON.
- JSON envelope fields present.
- Preflight object fields present.
- Active task contract detected.
- Allowed file returns `allow_preflight`.
- Forbidden file returns `blocked_by_scope` or `deny_preflight`.
- Out-of-scope file returns `requires_more_evidence` or `requires_human_review`.
- Unknown action returns `requires_human_review`.
- Multiple requested files handled deterministically.
- Conflicting allowed/forbidden match denies.
- `allow_preflight` does not set `execution_authorized=true`.
- `authorization_granted` always false.
- `repo_mutation_performed` always false.
- `storage_written` always false.
- `backend_invocation_performed` always false.
- No cache/state/.pcae files created.
- No repository mutation.
- No staging performed.
- Existing gate-dry-run still works.
- Existing read-only intelligence commands still work.
- All 15 safety notes verified.
- Not-scope-decidable actions (adoption, backend_invocation, commit, push,
  rollback, storage_write) all require human review.
- No files requested returns requires_more_evidence.
- Plain text output works.

## 15. Known Limitations

The scope gate preflight prototype evaluates requested action/file scope only.
It does not intercept shell commands, invoke backends, mutate files, perform
adoption, stage, commit, push, write storage, implement the permission broker,
or implement the shell gate.

## 16. Recommended Next Phase

**88C — Scope Gate Preflight Tests and False-Positive Review.**

After the prototype exists, review test coverage and false positives before
expanding to backend/mutation/commit/push enforcement.

---

phase_88b_name=scope_gate_preflight_prototype
phase_88b_version=0.1
phase_88b_status=implemented
implementation_status=complete
command_name=pcae preflight scope
test_count=66
decision_values=10
reason_codes=13
known_actions=11
scope_decidable_actions=4
not_scope_decidable_actions=6
safety_notes=15
authorization_granted=false
execution_authorized=false
repo_mutation_performed=false
storage_written=false
backend_invocation_performed=false
recommended_next=88C
