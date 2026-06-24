# Phase 85 Project State Snapshot Prototype

## 1. Purpose

Document the implementation of the read-only project state snapshot command
(`pcae project-state [--json]`), the sixth and capstone Phase 85 CLI command
prototype that integrates all five read-only layers: artifact index (86C),
memory snapshot (86D), governance timeline (86E), decision log (86F), and
risk register (86G).

## 2. Scope

Implementation summary only. Describes the implemented command, JSON envelope,
snapshot model, integrated layers, answer surface, safety boundaries, and tests.

## 3. Non-Goals

- Implementing permission broker or shell gate.
- Creating `.pcae` storage, generated cache, or machine-readable state files.
- Backend invocation, prompt sending, capture, intake, or adoption.
- Modifying README.md or existing design/prototype artifacts.
- Converting recommendations into authorizations.

## 4. Implemented Command

```
pcae project-state --json
```

Emits a project-state snapshot as JSON to stdout. Read-only: no file writes,
no cache, no .pcae storage, no authorization inference.

Without `--json`, prints a human-readable summary.

## 5. JSON Envelope

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | `"0.1"` |
| `generated_at` | string | ISO 8601 UTC timestamp |
| `source_command` | string | `"pcae project-state"` |
| `repository_root` | string | Absolute path to repository |
| `snapshot` | object | ProjectStateSnapshot object |
| `layer_summary` | object | Aggregate counts from each layer |
| `warnings` | list | Warning messages |
| `errors` | list | Error messages |
| `safety_notes` | object | Safety flags |

## 6. ProjectStateSnapshot Fields

42 fields integrating all five layers:

| Field | Type | Notes |
|-------|------|-------|
| `snapshot_id` | string | SHA256-based, stable per git state |
| `snapshot_version` | string | `"0.1"` |
| `snapshot_status` | string | `"current"` |
| `snapshot_created_at` | string | ISO 8601 UTC |
| `source_phase` | string | `"86H"` |
| `latest_completed_phase` | string | From memory snapshot |
| `current_active_phase` | string | From memory snapshot |
| `current_lifecycle_state` | string | From memory snapshot |
| `roadmap_position` | string | From memory snapshot |
| `recommended_next_phase` | string | `"86I"` (recommendation only) |
| `repository_clean` | boolean | From git status |
| `branch` | string | Current git branch |
| `origin_sync_status` | string | synced/ahead_by_N/unknown |
| `origin_main_head_count` | integer | Commits ahead of origin |
| `health_status` | string | `"unknown"` (not run inline) |
| `check_status` | string | `"unknown"` (not run inline) |
| `doctor_status` | string | `"unknown"` (not run inline) |
| `push_check_status` | string | `"unknown"` (not run inline) |
| `execution_authorized` | boolean | `false` |
| `backend_invocation_authorized` | boolean | `false` |
| `prompt_sending_authorized` | boolean | `false` |
| `capture_authorized` | boolean | `false` |
| `intake_authorized` | boolean | `false` |
| `adoption_authorized` | boolean | `false` |
| `source_mutation_authorized` | boolean | `false` |
| `test_mutation_authorized` | boolean | `false` |
| `readme_mutation_authorized` | boolean | `false` |
| `docs_real_captured_tasks_mutation_authorized` | boolean | `false` |
| `active_blockers` | list | Currently empty |
| `active_deferred_items` | list | From risk register (deferred) |
| `active_rejected_items` | list | Currently empty |
| `active_risks` | list | From risk register (active) |
| `accepted_risks` | list | From risk register (accepted) |
| `must_never_repeat_controls` | list | From risk register |
| `stale_signals` | list | From risk register (stale_signal) |
| `evidence_artifacts` | list | From artifact index (current) |
| `evidence_commits` | list | HEAD commit |
| `next_safe_actions` | list | Recommendations only |
| `forbidden_actions` | list | Explicit forbidden list |
| `human_review_required` | boolean | `false` |
| `confidence` | string | `"high"` |
| `safety_notes` | string | Read-only and recommendation flags |

## 7. Integrated Read-Only Layers

| Layer | Source | Data Used |
|-------|--------|-----------|
| Artifact Index | 86C | Record counts, evidence artifact paths |
| Memory Snapshot | 86D | Current/completed phase, lifecycle state, roadmap |
| Governance Timeline | 86E | Event count |
| Decision Log | 86F | Decision count |
| Risk Register | 86G | Active/accepted/deferred/stale risks, must-never-repeat |

## 8. Answer Surface

| Question | Snapshot Field |
|----------|----------------|
| What phase are we in? | `current_active_phase` |
| What was most recently completed? | `latest_completed_phase` |
| What is recommended next? | `recommended_next_phase` |
| What risks are active? | `active_risks` |
| What risk was accepted? | `accepted_risks` |
| What is deferred? | `active_deferred_items` |
| What stale signals remain? | `stale_signals` |
| What must never be repeated? | `must_never_repeat_controls` |
| What can be safely done next? | `next_safe_actions` (recommendations) |
| What is forbidden? | `forbidden_actions` |
| What evidence supports this? | `evidence_artifacts`, `evidence_commits` |

## 9. Next Safe Actions Handling

Next safe actions are **recommendations only, not authorizations**. The snapshot
explicitly labels them as such. The safety note
`next_safe_actions_are_recommendations_not_authorizations=true` is set.
Tests verify this.

## 10. Forbidden Actions Handling

Forbidden actions include backend invocation, prompt sending, adoption without
lifecycle, commit/push without governance, force push, raw git push,
storage/cache creation, mutation outside scope, and README mutation.

## 11. Accepted Risk and Stale Signal Handling

- Accepted risks are listed separately from active risks
- Stale signals are listed separately with preserved visibility
- Must-never-repeat controls are listed explicitly
- Tests verify each category is populated and separate

## 12. Read-Only Behavior

- Command emits JSON to stdout only
- No files written during command execution
- No cache files created
- No `.pcae` storage created or modified
- No repository files modified

## 13. Storage Behavior

- No storage directories created
- No cache files created
- No machine-readable state files created

## 14. Safety Boundaries

| Safety Note | Value |
|-------------|-------|
| `project_state_is_read_only` | `true` |
| `project_state_does_not_authorize_execution` | `true` |
| `project_state_does_not_authorize_backend_invocation` | `true` |
| `project_state_does_not_authorize_adoption` | `true` |
| `project_state_does_not_authorize_commit_or_push` | `true` |
| `next_safe_actions_are_recommendations_not_authorizations` | `true` |
| `generated_cache_created` | `false` |
| `pcae_storage_created` | `false` |
| `artifact_index_used` | `true` |
| `memory_snapshot_used` | `true` |
| `governance_timeline_used` | `true` |
| `decision_log_used` | `true` |
| `risk_register_used` | `true` |

## 15. Tests Added

34 tests in `tests/test_project_state.py`:

1. `test_project_state_exits_successfully`
2. `test_project_state_output_is_valid_json`
3. `test_project_state_envelope_fields`
4. `test_project_state_snapshot_is_dict`
5. `test_project_state_required_fields`
6. `test_project_state_latest_completed_phase`
7. `test_project_state_recommended_next_phase`
8. `test_project_state_active_risks_populated`
9. `test_project_state_accepted_risks_separate`
10. `test_project_state_stale_signals_visible`
11. `test_project_state_must_never_repeat_visible`
12. `test_project_state_next_safe_actions_present`
13. `test_project_state_next_safe_actions_are_recommendations`
14. `test_project_state_forbidden_actions_present`
15. `test_project_state_authorization_booleans_explicit`
16. `test_project_state_high_risk_auth_false`
17. `test_project_state_artifact_index_used`
18. `test_project_state_memory_snapshot_used`
19. `test_project_state_governance_timeline_used`
20. `test_project_state_decision_log_used`
21. `test_project_state_risk_register_used`
22. `test_project_state_unknown_not_encoded_as_false`
23. `test_project_state_no_cache_files_created`
24. `test_project_state_no_repository_files_created`
25. `test_project_state_no_authority_inference`
26. `test_project_state_no_generated_cache`
27. `test_project_state_schema_version`
28. `test_project_state_source_command`
29. `test_project_state_layer_summary`
30. `test_artifact_index_still_works`
31. `test_memory_snapshot_still_works`
32. `test_governance_timeline_still_works`
33. `test_decision_log_still_works`
34. `test_risk_register_still_works`

## 16. Validation Results

- `python -m pytest -n auto`: 7084 passed (34 new, 0 regressions)
- `pcae project-state --json`: valid JSON, all layers integrated
- All five layer commands still work independently
- Authorization booleans all false
- Next safe actions labeled as recommendations
- Active/accepted/stale/must-never-repeat all populated

## 17. Known Limitations

- health_status/check_status/doctor_status/push_check_status are "unknown" (not run inline)
- snapshot_id depends on git HEAD, not full content hash
- Does not run PCAE health/check/doctor commands within the snapshot generation
- Layer summary is count-level, not full detail

## 18. Recommended Next Phase

86I — Phase 85 Integration Tests.

---

project_state_prototype_name=phase_85_project_state_snapshot_prototype
project_state_prototype_version=0.1
project_state_prototype_status=implemented
project_state_command=pcae project-state --json
snapshot_fields=42
layers_integrated=5
tests_added=34
total_test_count=7084
artifact_index_reused=true
memory_snapshot_reused=true
governance_timeline_reused=true
decision_log_reused=true
risk_register_reused=true
read_only=true
storage_created=false
cache_created=false
pcae_storage_created=false
authorization_inference=false
next_safe_actions_are_recommendations=true
backend_invocation_performed=false
