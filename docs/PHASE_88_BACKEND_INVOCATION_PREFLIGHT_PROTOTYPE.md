# Phase 88E Backend Invocation Preflight Prototype

## 1. Purpose

Implement the backend invocation preflight prototype: an explicit command that
evaluates whether a proposed backend invocation has sufficient evidence to
proceed to a future human-reviewed backend call. Returns structured JSON with
a preflight decision, reason codes, prompt evidence status, scope relationship,
human review requirements, and safety notes.

## 2. Scope

88E implements:

- `pcae preflight backend` command with `--json`, `--requested-backend`,
  `--requested-action`, `--requested-file`, `--prompt-present`, and
  `--prompt-hash` arguments.
- Core backend preflight evaluator in `src/pcae/core/backend_preflight.py`.
- Command runner in `src/pcae/commands/backend_preflight.py`.
- CLI registration in `src/pcae/cli.py`.
- 42 tests in `tests/test_backend_preflight.py`.

## 3. Non-Goals

- Invoking any backend.
- Sending prompts.
- Capturing outputs.
- Permission broker or shell gate.
- Mutation/adoption/commit/push preflight.
- Storage, cache, or `.pcae` persistent state.

## 4. Relationship to 88D

Phase 88D (Backend Invocation Preflight Design) defined the backend preflight
boundary: 6 backend identities, 16-field request model, 25-field output model,
11 decision values, 12 deny-by-default rules, 14 human review triggers, prompt
handling model, and 15 safety invariants. 88E implements the prototype command
based on that design.

## 5. Command Behavior

```
pcae preflight backend --json --requested-backend BACKEND --requested-action ACTION \
    [--requested-file PATH ...] [--prompt-present] [--prompt-hash HASH]
```

The command:

1. Identifies whether the backend is known or unknown.
2. Checks for active task contract.
3. Evaluates prompt presence and hash status.
4. Evaluates file scope relationship when files are provided.
5. Applies deny-by-default decision rules.
6. Returns structured JSON with the preflight decision.
7. Does not invoke any backend.
8. Does not send any prompt.
9. Does not capture any output.

## 6. JSON Output Model

### Envelope

schema_version, generated_at, source_command, repository_root, preflight,
warnings, errors, safety_notes.

### Preflight Object

preflight_type, requested_backend, requested_action, requested_files, decision,
reason_codes, backend_known, backend_allowed_by_policy, prompt_present,
prompt_required, prompt_hash_present, prompt_hash_required,
scope_preflight_required, scope_preflight_decision, human_review_required,
more_evidence_required, task_contract_detected, task_contract_path,
lifecycle_state, evidence_sources, backend_notes, authorization_granted,
execution_authorized, backend_invocation_performed, prompt_sent,
capture_performed, repo_mutation_performed, storage_written.

## 7. Backend Identities

claude, claude-deepseek, claude-kimi, codex, subagent (known).
All other values treated as unknown and denied.

## 8. Decision Values

allow_preflight, deny_preflight, requires_human_review, requires_more_evidence,
blocked_by_backend_policy, blocked_by_missing_task_contract,
blocked_by_missing_prompt, blocked_by_scope, blocked_by_lifecycle_state,
blocked_by_risk, unknown.

## 9. Reason Codes

backend_known, backend_unknown, task_contract_detected, missing_task_contract,
prompt_present, missing_prompt, prompt_hash_present, missing_prompt_hash,
scope_preflight_required, scope_preflight_missing, scope_preflight_allowed,
scope_preflight_denied, human_review_required, more_evidence_required,
unknown_action, backend_preflight_only_not_execution_authorization.

## 10. Prompt Evidence Handling

- Prompt-requiring actions (docs_mutation, source_mutation, test_mutation,
  adoption, backend_invocation) require --prompt-present.
- --prompt-hash provides audit traceability when prompt is present.
- Missing prompt blocks; present prompt without hash requires more evidence;
  prompt with hash proceeds to human review.

## 11. Scope Preflight Relationship

- File-related actions (read, docs_mutation, source_mutation, test_mutation,
  adoption) with requested files trigger scope evaluation.
- Forbidden files → blocked_by_scope.
- Scope allow still requires human review for backend invocation.

## 12. Human Review Behavior

All backend invocation requests set human_review_required=true. Known backend
with prompt and hash proceeds to requires_human_review (not allow_preflight).

## 13. Non-Authorizing Boundary

- authorization_granted always false.
- execution_authorized always false.
- backend_invocation_performed always false.
- prompt_sent always false.
- capture_performed always false.

## 14. No-Backend/No-Prompt/No-Capture Behavior

The command never invokes Claude, Claude DeepSeek, Claude Kimi, Codex, or
subagents. It never sends prompts, captures output, performs intake, or
performs adoption.

## 15. No-Write/No-Storage Behavior

No cache, state, or .pcae files created. No repository mutation.

## 16. Safety Notes

15 safety notes including backend_preflight_only, does_not_invoke_backends,
does_not_send_prompts, does_not_capture_outputs, scope_preflight_is_separate,
permission_broker_not_implemented, shell_gate_not_implemented,
storage_not_implemented.

## 17. Test Coverage

42 tests covering: command exists, JSON envelope, preflight fields, all 5 known
backends recognized, unknown backend denied, task contract detection, prompt
missing/present/hash handling, file scope evaluation, scope allow does not
authorize backend, human review always required, unknown action handling, all
safety flags false, no .pcae files created, no repository mutation, existing
scope preflight works, gate-dry-run works, intelligence commands work, safety
notes verified, reason code disclaimer present, plain text output.

## 18. Known Limitations

The backend invocation preflight prototype evaluates proposed backend invocation
only. It does not invoke Claude, Claude DeepSeek, Claude Kimi, Codex, or
subagents; it does not send prompts, capture output, perform intake, perform
adoption, mutate files, stage, commit, push, write storage, implement the
permission broker, or implement the shell gate.

## 19. Recommended Next Phase

**88F — Backend Invocation Preflight Tests and False-Positive Review.**

After the backend preflight prototype exists, review edge cases and false
positives/negatives before moving to mutation/adoption preflight design.

---

phase_88e_name=backend_invocation_preflight_prototype
phase_88e_version=0.1
phase_88e_status=implemented
command_name=pcae preflight backend
test_count=42
backend_identities=5_known
decision_values=11
reason_codes=16
prompt_present_supported=true
prompt_hash_supported=true
requested_file_supported=true
authorization_granted=false
execution_authorized=false
backend_invocation_performed=false
prompt_sent=false
capture_performed=false
recommended_next=88F
