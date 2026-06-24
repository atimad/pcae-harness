# Phase 85 Decision Log Prototype

## 1. Purpose

Document the implementation of the read-only decision log command
(`pcae decision-log [--json]`), the fourth Phase 85 CLI command prototype
following the artifact index (86C), memory snapshot (86D), and governance
timeline (86E).

## 2. Scope

Implementation summary only. Describes the implemented command, JSON envelope,
decision model, provenance inputs, ordering rules, safety boundaries, and tests.

## 3. Non-Goals

- Implementing risk register or project state snapshot.
- Creating `.pcae` storage, generated cache, or machine-readable state files.
- Backend invocation, prompt sending, capture, intake, or adoption.
- Modifying README.md or existing design/prototype artifacts.

## 4. Implemented Command

```
pcae decision-log --json
```

Emits decision records as JSON to stdout. Read-only: no file writes, no cache,
no .pcae storage, no authorization inference.

Without `--json`, prints a human-readable summary.

## 5. JSON Envelope

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | `"0.1"` |
| `generated_at` | string | ISO 8601 UTC timestamp |
| `source_command` | string | `"pcae decision-log"` |
| `repository_root` | string | Absolute path to repository |
| `decisions` | list | Ordered list of DecisionRecord objects |
| `decision_count` | integer | Number of decisions |
| `warnings` | list | Warning messages |
| `errors` | list | Error messages |
| `safety_notes` | object | Safety flags |

## 6. DecisionRecord Fields

25 fields per 86B data model design:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `decision_id` | string | yes | Stable SHA256-based identifier |
| `decision_type` | string | yes | From implemented decision types |
| `decision_status` | string | yes | approved, recorded, etc. |
| `decision_timestamp` | string | yes | ISO 8601 or `"unknown"` |
| `source_phase` | string | yes | Phase that produced this decision |
| `source_artifact` | string | yes | Artifact path or `"unknown"` |
| `source_event` | string | yes | Event ID or `"unknown"` |
| `source_commit` | string | yes | Commit hash or `"unknown"` |
| `decision_maker` | string | yes | `"governance"` |
| `human_required` | boolean | yes | Whether human authority required |
| `approved_scope` | string | no | What was approved |
| `denied_scope` | string | no | What was denied (null if not denial) |
| `deferred_scope` | string | no | What was deferred (null if not deferral) |
| `rejected_scope` | string | no | What was rejected (null if not rejection) |
| `affected_files` | list | yes | Files affected |
| `affected_agents` | list | yes | Agents affected |
| `authorization_flags` | dict | yes | Explicit auth flags (all high-risk false) |
| `risk_level` | string | no | low/medium/high/critical |
| `supersedes` | string | no | Decision ID this supersedes |
| `superseded_by` | string | no | Decision ID that supersedes this |
| `related_decisions` | list | yes | Related decision IDs |
| `related_artifacts` | list | yes | Related artifact IDs |
| `related_events` | list | yes | Related event IDs |
| `evidence_level` | string | yes | `repo_committed_artifact` |
| `safety_notes` | string | no | Additional safety notes |

## 7. Decision Types Implemented

| Decision Type | Description |
|---------------|-------------|
| `phase_completion_decision` | Phase was completed |
| `implementation_scope_decision` | Phase scope was defined and bounded |
| `read_only_boundary_decision` | Read-only boundary enforced |
| `no_storage_boundary_decision` | No storage/cache/.pcae creation |
| `no_backend_invocation_decision` | No backend invocation performed |
| `no_authority_inference_decision` | No authority inference from output presence |
| `recommended_next_phase_decision` | Recommended next phase recorded |

## 8. Decision Status Values

| Status | Meaning |
|--------|---------|
| `approved` | Boundary/scope decision approved by governance |
| `recorded` | Informational decision recorded (e.g., next phase recommendation) |

## 9. Provenance Inputs

- Artifact index from 86C (`build_artifact_index`)
- Memory snapshot from 86D (`build_memory_snapshot`)
- Governance timeline from 86E (`build_governance_timeline`)
- `tasks/completed/**` task contract files
- Phase 84L–86E committed artifacts
- Git commit history for timestamps and commit refs

## 10. Ordering Rules

- Decisions sorted by (source_phase, decision_timestamp, decision_id)
- Decisions with unknown timestamps sort after known timestamps within same phase
- Deterministic: identical output across repeated runs on same repo state
- Decision IDs are SHA256-based, stable across runs for the same source evidence

## 11. Read-Only Behavior

- Command emits JSON to stdout only
- No files written during command execution
- No cache files created
- No `.pcae` storage created or modified
- No repository files modified
- Exit 0 on success, nonzero on actual command failure

## 12. Storage Behavior

- No storage directories created
- No cache files created
- No machine-readable state files created
- No `.pcae` directory created or modified

## 13. Safety Boundaries

| Safety Note | Value |
|-------------|-------|
| `decision_log_is_read_only` | `true` |
| `decision_log_does_not_authorize_execution` | `true` |
| `decision_log_does_not_authorize_backend_invocation` | `true` |
| `decision_log_does_not_authorize_adoption` | `true` |
| `decision_log_does_not_authorize_commit_or_push` | `true` |
| `generated_cache_created` | `false` |
| `pcae_storage_created` | `false` |
| `artifact_index_used` | `true` |
| `memory_snapshot_used` | `true` |
| `governance_timeline_used` | `true` |

Decision presence does not authorize execution, backend invocation, adoption,
or commit/push. Decision log output is observational only.

Authorization flags in each DecisionRecord are explicit. All 11 high-risk flags
(execution, backend_invocation, prompt_sending, capture, intake, adoption,
source_mutation, test_mutation, commit, push, storage) are false.

## 14. Tests Added

28 tests in `tests/test_decision_log.py`:

1. `test_decision_log_exits_successfully`
2. `test_decision_log_output_is_valid_json`
3. `test_decision_log_envelope_fields`
4. `test_decision_log_decisions_is_list`
5. `test_decision_log_decision_count_matches`
6. `test_decision_log_required_fields`
7. `test_decision_log_decisions_are_deterministic`
8. `test_decision_log_decisions_ordered_deterministically`
9. `test_decision_log_decision_ids_stable`
10. `test_decision_log_86c_evidence`
11. `test_decision_log_86d_evidence`
12. `test_decision_log_86e_evidence`
13. `test_decision_log_authorization_flags_explicit`
14. `test_decision_log_high_risk_auth_flags_false`
15. `test_decision_log_denied_deferred_rejected_fields_exist`
16. `test_decision_log_artifact_index_used`
17. `test_decision_log_memory_snapshot_used`
18. `test_decision_log_governance_timeline_used`
19. `test_decision_log_unknown_not_encoded_as_false`
20. `test_decision_log_no_cache_files_created`
21. `test_decision_log_no_repository_files_created`
22. `test_decision_log_no_authority_inference`
23. `test_decision_log_no_generated_cache`
24. `test_decision_log_schema_version`
25. `test_decision_log_source_command`
26. `test_artifact_index_still_works`
27. `test_memory_snapshot_still_works`
28. `test_governance_timeline_still_works`

## 15. Validation Results

- `python -m pytest -n auto`: 7019 passed (28 new, 0 regressions)
- `pcae decision-log --json`: valid JSON, 84 decisions, 7 decision types
- `pcae artifact-index --json`: 14 records, still works
- `pcae memory-snapshot --json`: still works
- `pcae governance-timeline --json`: still works
- Decision IDs deterministic across repeated runs
- All authorization flags explicitly false
- No cache/state/.pcae files created

## 16. Known Limitations

- Decision log covers Phase 84L–86E evidence from completed task contracts
- Does not extract approval/denial/deferral/rejection from within artifact prose
- Does not link to specific governance timeline event IDs (source_event="unknown")
- Decision types are conservative governance boundary decisions, not fine-grained
- Does not implement decision lifecycle transitions or supersession chains
- Risk levels are uniformly "low" for boundary decisions

## 17. Recommended Next Phase

86G — Risk Register Extraction.

---

decision_log_prototype_name=phase_85_decision_log_prototype
decision_log_prototype_version=0.1
decision_log_prototype_status=implemented
decision_log_command=pcae decision-log --json
decision_count=84
decision_types_implemented=7
decision_statuses_used=2
tests_added=28
total_test_count=7019
artifact_index_reused=true
memory_snapshot_reused=true
governance_timeline_reused=true
read_only=true
storage_created=false
cache_created=false
pcae_storage_created=false
authorization_inference=false
authorization_flags_explicit=true
high_risk_flags_all_false=true
backend_invocation_performed=false
