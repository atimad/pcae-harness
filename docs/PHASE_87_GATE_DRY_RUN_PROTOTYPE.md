# Phase 87 Gate Dry-Run Prototype

## 1. Purpose

Document the read-only gate dry-run evaluator (`pcae gate-dry-run [--json]`),
the first Phase 87 implementation. Reports hypothetical gate decisions without
enforcing, authorizing, or writing persistent state.

## 2. Scope

Implementation summary. Describes the command, JSON output, gate evaluation,
safety guarantees, and tests.

## 3. Non-Goals

- Enforcing gate decisions.
- Authorizing actions from gate output.
- Implementing permission broker, shell gate, or storage.
- Modifying existing read-only commands.

## 4. Command

```
pcae gate-dry-run --json
```

Evaluates all 15 gates from the 87B taxonomy in dry-run mode. Emits JSON to
stdout. Does not enforce, authorize, invoke, mutate, or store.

## 5. JSON Envelope

| Field | Type | Value |
|-------|------|-------|
| `schema_version` | string | `"0.1"` |
| `generated_at` | string | ISO 8601 UTC |
| `source_command` | string | `"pcae gate-dry-run"` |
| `repository_root` | string | Absolute path |
| `dry_run` | boolean | `true` |
| `taxonomy_version` | string | `"0.1"` |
| `gate_count` | integer | 15 |
| `gates` | list | Gate result objects |
| `warnings` | list | Warnings |
| `errors` | list | Errors |
| `safety_notes` | object | Safety flags |

## 6. Gate Result Model

Each gate result includes 24 fields:

gate_id, gate_name, gate_category, protected_action, risk_level, decision,
reason_codes, human_review_required, evidence_artifacts, evidence_events,
evidence_decisions, evidence_risks, allowed_scope, denied_scope,
requested_action, requested_actor, requested_files, dry_run,
enforcement_performed, authorization_granted, safety_notes, generated_at,
schema_version.

## 7. Decisions and Reason Codes

No gate produces `allow` in the initial dry-run. Decisions used:

- `deny` — for high-risk and not-implemented gates
- `requires_human_review` — for write-capable gates needing human sign-off
- `requires_more_evidence` — for gates needing more context

20 reason codes from 87B taxonomy are available.

## 8. Source Integration

Reuses existing read-only builders internally:

- `build_artifact_index`
- `build_memory_snapshot`
- `build_governance_timeline`
- `build_decision_log`
- `build_risk_register`
- `build_project_state`

## 9. Safety Guarantees

The dry-run evaluator reports hypothetical gate decisions only. It does not
enforce, authorize, invoke, mutate, adopt, commit, push, or write persistent
state.

| Safety Note | Value |
|-------------|-------|
| `gate_dry_run_only` | `true` |
| `gate_dry_run_does_not_authorize_action` | `true` |
| `gate_dry_run_does_not_enforce_action` | `true` |
| `gate_dry_run_does_not_invoke_backends` | `true` |
| `gate_dry_run_does_not_mutate_repo` | `true` |
| `gate_dry_run_does_not_write_storage` | `true` |
| `permission_broker_not_implemented` | `true` |
| `shell_gate_not_implemented` | `true` |
| `storage_not_implemented` | `true` |
| `backend_invocation_performed` | `false` |
| `repo_mutation_performed` | `false` |
| `storage_written` | `false` |

## 10. No-Write/No-Storage Behavior

- No files written
- No cache created
- No .pcae storage created
- No gate state files created
- No schema files created

## 11. Test Coverage

29 tests in `tests/test_gate_dry_run.py`:

Exit success, valid JSON, envelope fields, dry_run true, taxonomy version,
gate count 15, all 15 gates present, required gate fields, valid decisions,
reason codes lists, enforcement false, authorization false, no backend,
no repo mutation, no storage, permission broker not implemented, shell gate
not implemented, storage not implemented, high-risk no auto-allow, write-
capable no auto-allow, no allow from recommendation, no cache created, no
repository mutation, plus 6 existing-command compatibility tests.

## 12. Known Limitations

- Dry-run only; no enforcement capability
- No gate produces `allow` in initial implementation
- Gate evaluation does not consume task contract dynamically
- Evidence references are illustrative, not deeply linked
- Gate decisions are not persisted or auditable beyond stdout

## 13. Recommended Next Phase

**87D — Scope Gate Prototype.**

---

gate_dry_run_prototype_name=phase_87_gate_dry_run_prototype
gate_dry_run_prototype_version=0.1
gate_dry_run_prototype_status=implemented
gate_dry_run_command=pcae gate-dry-run --json
gates_evaluated=15
tests_added=29
total_test_count=7151
read_only=true
enforcement_performed=false
authorization_granted=false
storage_created=false
backend_invocation_performed=false
recommended_next=87D
