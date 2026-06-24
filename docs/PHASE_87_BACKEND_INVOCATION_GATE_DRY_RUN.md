# Phase 87 Backend Invocation Gate Dry-Run

## 1. Purpose

Document the backend invocation gate dry-run added to `pcae gate-dry-run [--json]`.
Evaluates proposed backend invocation without invoking backends, sending prompts,
or capturing output.

## 2. Scope

Implementation summary. Extends the gate dry-run evaluator with concrete backend
invocation evaluation, optional CLI flags, and backend-specific tests.

## 3. Non-Goals

- Invoking any backend (Claude, Claude DeepSeek, Claude Kimi, Codex, subagents).
- Sending prompts.
- Capturing backend output.
- Authorizing backend invocation.
- Enforcing backend invocation policy.
- Implementing permission broker, shell gate, or storage.

## 4. Command Behavior

```
pcae gate-dry-run --json
pcae gate-dry-run --json --requested-action backend_invocation --requested-backend claude
pcae gate-dry-run --json --requested-action backend_invocation --requested-backend claude --prompt-present
```

The `--requested-backend` and `--prompt-present` flags are optional. When provided,
the backend_invocation_gate evaluates the proposed invocation. Without flags, a
default evaluation runs.

## 5. Backend Invocation Gate Model

The backend_invocation_gate now includes a `backend_evaluation` field with detailed
backend invocation analysis.

## 6. Backend Evaluation Fields

| Field | Type | Description |
|-------|------|-------------|
| `backend_status` | string | Evaluation result status |
| `requested_backend` | string | Backend name requested |
| `requested_action` | string | Action type |
| `prompt_present` | boolean | Whether prompt evidence exists |
| `backend_allowed_by_scope` | boolean | Always false in dry-run |
| `backend_approval_detected` | boolean | Always false in dry-run |
| `human_approval_detected` | boolean | Always false in dry-run |
| `task_contract_detected` | boolean | Whether task contract found |
| `task_contract_path` | string | Path to task contract |
| `evidence_sources` | list | Sources consulted |
| `backend_notes` | string | Additional context |

## 7. Requested Backend Handling

All known backends (claude, claude-deepseek, claude-kimi, codex, subagent)
and unknown backends are evaluated. None are invoked.

## 8. Prompt Presence Handling

`--prompt-present` indicates a prompt is available for evaluation. This does
not authorize invocation — it shifts the decision from `requires_more_evidence`
to `requires_human_review`.

## 9. Decision Mapping

| Status | Decision |
|--------|----------|
| not_requested | requires_more_evidence |
| requested_requires_human_review | requires_human_review |
| requested_requires_more_evidence | requires_more_evidence |
| requested_blocked | deny |
| requested_unknown | requires_more_evidence |

No backend invocation gate produces `allow`.

## 10. Reason Codes

backend_invocation_not_authorized, human_approval_required,
missing_artifact_evidence, must_never_repeat_control_applies,
unknown_state, risk_active.

## 11. Safety Guarantees

| Safety Note | Value |
|-------------|-------|
| `backend_gate_dry_run_only` | `true` |
| `backend_gate_does_not_invoke_backend` | `true` |
| `backend_gate_does_not_send_prompt` | `true` |
| `backend_gate_does_not_capture_output` | `true` |
| `backend_gate_does_not_authorize_backend_invocation` | `true` |
| `backend_gate_requires_human_review_for_invocation` | `true` |
| `requested_backend_is_not_approval` | `true` |
| `prompt_presence_is_not_approval` | `true` |
| `scope_match_is_not_backend_approval` | `true` |

## 12. No-Invocation/No-Prompt/No-Capture Behavior

- No backend is invoked
- No prompt is sent to any backend or subagent
- No backend output is captured
- No prompt files are created
- No capture files are created

## 13. No-Write/No-Storage Behavior

- No files written
- No cache created
- No .pcae storage created
- No backend gate state files created

## 14. Test Coverage

23 tests in `tests/test_backend_gate.py`:

Default works, backend gate present, has backend_evaluation, required fields,
default evaluation, claude/deepseek/kimi/codex/subagent/unknown do not invoke,
prompt present does not authorize, does not send prompts, does not capture,
backend_invocation_performed false, all gates auth false, envelope safety notes,
repo mutation false, storage false, scope gate still works, no cache created,
no repo mutation, existing commands work.

## 15. Known Limitations

- Dry-run only; no actual backend availability checking
- No backend produces `allow` in initial implementation
- Does not validate prompt content or hash
- Does not check agent identity against guard design
- Backend evaluation does not consume decision-log approval records

## 16. Recommended Next Phase

**87F — Adoption and Mutation Gate Dry-Run.**

---

backend_gate_prototype_name=phase_87_backend_invocation_gate_dry_run
backend_gate_prototype_version=0.1
backend_gate_prototype_status=implemented
tests_added=23
total_test_count=7196
read_only=true
enforcement_performed=false
authorization_granted=false
backend_invocation_performed=false
prompt_sent=false
output_captured=false
storage_created=false
recommended_next=87F
