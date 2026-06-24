# Phase 85 Risk Register Prototype

## 1. Purpose

Document the implementation of the read-only risk register command
(`pcae risk-register [--json]`), the fifth Phase 85 CLI command prototype
following the artifact index (86C), memory snapshot (86D), governance
timeline (86E), and decision log (86F).

## 2. Scope

Implementation summary only. Describes the implemented command, JSON envelope,
risk model, provenance inputs, ordering rules, safety boundaries, and tests.

## 3. Non-Goals

- Implementing project state snapshot.
- Creating `.pcae` storage, generated cache, or machine-readable state files.
- Backend invocation, prompt sending, capture, intake, or adoption.
- Modifying README.md or existing design/prototype artifacts.

## 4. Implemented Command

```
pcae risk-register --json
```

Emits risk records as JSON to stdout. Read-only: no file writes, no cache,
no .pcae storage, no authorization inference.

Without `--json`, prints a human-readable summary.

## 5. JSON Envelope

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | `"0.1"` |
| `generated_at` | string | ISO 8601 UTC timestamp |
| `source_command` | string | `"pcae risk-register"` |
| `repository_root` | string | Absolute path to repository |
| `risks` | list | Ordered list of RiskRecord objects |
| `risk_count` | integer | Number of risks |
| `warnings` | list | Warning messages |
| `errors` | list | Error messages |
| `safety_notes` | object | Safety flags |

## 6. RiskRecord Fields

32 fields per 86B data model design:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `risk_id` | string | yes | Stable SHA256-based identifier |
| `risk_type` | string | yes | From implemented risk types |
| `risk_status` | string | yes | active, accepted, mitigated, deferred, etc. |
| `risk_title` | string | yes | Short title |
| `risk_description` | string | yes | Description |
| `risk_severity` | string | yes | low/medium/high/critical/unknown |
| `risk_likelihood` | string | yes | unlikely/possible/likely/observed/unknown |
| `risk_exposure` | string | yes | low/medium/high/critical/unknown |
| `source_phase` | string | yes | Phase where identified |
| `source_artifact` | string | yes | Artifact path or `"unknown"` |
| `source_event` | string | yes | Event ID or `"unknown"` |
| `source_decision` | string | yes | Decision ID or `"unknown"` |
| `source_commit` | string | yes | Commit hash or `"unknown"` |
| `risk_owner` | string | no | Responsible party |
| `human_review_required` | boolean | yes | Whether human review needed |
| `affected_files` | list | yes | Files affected |
| `affected_agents` | list | yes | Agents affected |
| `affected_commands` | list | yes | Commands affected |
| `blocking_condition` | string | no | What this blocks |
| `mitigation` | string | no | Mitigation evidence (null for accepted risks) |
| `acceptance_rationale` | string | no | Why accepted (null for non-accepted) |
| `accepted_by` | string | no | Who accepted |
| `supersedes` | string | no | Risk ID this supersedes |
| `superseded_by` | string | no | Risk ID that supersedes this |
| `related_risks` | list | yes | Related risk IDs |
| `related_artifacts` | list | yes | Related artifact IDs |
| `related_events` | list | yes | Related event IDs |
| `related_decisions` | list | yes | Related decision IDs |
| `evidence_level` | string | yes | `repo_committed_artifact` |
| `last_reviewed_phase` | string | no | Last review phase |
| `next_review_phase` | string | no | Next review phase |
| `safety_notes` | string | no | Additional safety notes |

## 7. Risk Types Implemented

| Risk Type | Description |
|-----------|-------------|
| `read_only_boundary_risk` | Read-only boundary must remain enforced |
| `storage_boundary_risk` | No storage/cache/.pcae creation without gate |
| `backend_invocation_risk` | Backend invocation remains forbidden |
| `authority_inference_risk` | Authority inference from output remains forbidden |
| `raw_push_exception_risk` | Raw git push must not be normalized |
| `hook_bypass_exception_risk` | Hook bypass must not be normalized |
| `stale_signal_risk` | Structural stale signals remain visible |
| `implementation_scope_risk` | Implementation scope must remain bounded |
| `test_coverage_risk` | Test coverage must accompany implementation |
| `next_phase_risk` | Phase sequencing must be preserved |
| `accepted_risk` | Explicitly accepted risk with rationale |
| `permission_broker_risk` | Permission broker remains future direction |
| `must_never_repeat_risk` | Must-never-repeat controls remain visible |

## 8. Risk Status/Severity/Likelihood/Exposure Values

| Status | Used |
|--------|------|
| `active` | yes |
| `accepted` | yes |
| `deferred` | yes |
| `stale_signal` | yes |

| Severity | Used |
|----------|------|
| `low` | yes |
| `medium` | yes |
| `high` | yes |
| `critical` | yes |

| Likelihood | Used |
|------------|------|
| `unlikely` | yes |
| `possible` | yes |
| `observed` | yes |

| Exposure | Used |
|----------|------|
| `low` | yes |
| `medium` | yes |
| `high` | yes |

## 9. Provenance Inputs

- Artifact index from 86C (`build_artifact_index`)
- Memory snapshot from 86D (`build_memory_snapshot`)
- Governance timeline from 86E (`build_governance_timeline`)
- Decision log from 86F (`build_decision_log`)
- Phase 84H–86F committed artifacts
- 85E risk register design

## 10. Ordering Rules

- Risks sorted by (source_phase, risk_type, risk_id)
- Deterministic: identical output across repeated runs on same repo state
- Risk IDs are SHA256-based, stable across runs for the same source evidence

## 11. Accepted Risk Versus Mitigation Handling

- Accepted risks have `acceptance_rationale` set and `mitigation` null
- Mitigated risks would have `mitigation` set (not used in initial prototype)
- Test verifies: accepted risk must not have mitigation
- Safety note: `accepted_risk_is_not_mitigation=true`

## 12. Stale Signal Handling

- Stale signal risks have `risk_status="stale_signal"`
- 84K.3 structural signals preserved as stale_signal risk
- Test verifies: stale_signal risks visible in output

## 13. Must-Never-Repeat Handling

- `must_never_repeat_risk` type documents 8 controls from 85E
- `raw_push_exception_risk` and `hook_bypass_exception_risk` explicitly preserved
- Test verifies: must-never-repeat risks visible in output

## 14. Read-Only Behavior

- Command emits JSON to stdout only
- No files written during command execution
- No cache files created
- No `.pcae` storage created or modified
- No repository files modified
- Exit 0 on success, nonzero on actual command failure

## 15. Storage Behavior

- No storage directories created
- No cache files created
- No machine-readable state files created
- No `.pcae` directory created or modified

## 16. Safety Boundaries

| Safety Note | Value |
|-------------|-------|
| `risk_register_is_read_only` | `true` |
| `risk_register_does_not_authorize_execution` | `true` |
| `risk_register_does_not_authorize_backend_invocation` | `true` |
| `risk_register_does_not_authorize_adoption` | `true` |
| `risk_register_does_not_authorize_commit_or_push` | `true` |
| `accepted_risk_is_not_mitigation` | `true` |
| `generated_cache_created` | `false` |
| `pcae_storage_created` | `false` |
| `artifact_index_used` | `true` |
| `memory_snapshot_used` | `true` |
| `governance_timeline_used` | `true` |
| `decision_log_used` | `true` |

## 17. Tests Added

31 tests in `tests/test_risk_register.py`:

1. `test_risk_register_exits_successfully`
2. `test_risk_register_output_is_valid_json`
3. `test_risk_register_envelope_fields`
4. `test_risk_register_risks_is_list`
5. `test_risk_register_risk_count_matches`
6. `test_risk_register_required_fields`
7. `test_risk_register_risks_are_deterministic`
8. `test_risk_register_risks_ordered_deterministically`
9. `test_risk_register_risk_ids_stable`
10. `test_risk_register_has_required_initial_risks`
11. `test_risk_register_status_values_explicit`
12. `test_risk_register_severity_likelihood_exposure_explicit`
13. `test_risk_register_accepted_risk_not_treated_as_mitigation`
14. `test_risk_register_accepted_risk_safety_note`
15. `test_risk_register_stale_signal_visible`
16. `test_risk_register_must_never_repeat_visible`
17. `test_risk_register_artifact_index_used`
18. `test_risk_register_memory_snapshot_used`
19. `test_risk_register_governance_timeline_used`
20. `test_risk_register_decision_log_used`
21. `test_risk_register_unknown_not_encoded_as_false`
22. `test_risk_register_no_cache_files_created`
23. `test_risk_register_no_repository_files_created`
24. `test_risk_register_no_authority_inference`
25. `test_risk_register_no_generated_cache`
26. `test_risk_register_schema_version`
27. `test_risk_register_source_command`
28. `test_artifact_index_still_works`
29. `test_memory_snapshot_still_works`
30. `test_governance_timeline_still_works`
31. `test_decision_log_still_works`

## 18. Validation Results

- `python -m pytest -n auto`: 7050 passed (31 new, 0 regressions)
- `pcae risk-register --json`: valid JSON, 13 risks, 13 risk types
- `pcae artifact-index --json`: 14 records, still works
- `pcae memory-snapshot --json`: still works
- `pcae governance-timeline --json`: still works
- `pcae decision-log --json`: 84 decisions, still works
- Risk IDs deterministic across repeated runs
- Accepted risk not treated as mitigation (tested)
- Stale signal visible (tested)
- Must-never-repeat visible (tested)
- No cache/state/.pcae files created

## 19. Known Limitations

- Risk register uses standing risk catalog, not dynamic extraction from artifact prose
- Does not link to specific timeline event IDs or decision IDs (source_event/decision="unknown")
- Does not implement risk lifecycle transitions or supersession chains
- Severity/likelihood/exposure are assigned by catalog, not computed
- Does not extract risks from within individual phase artifacts beyond the catalog

## 20. Recommended Next Phase

86H — Project State Snapshot CLI.

---

risk_register_prototype_name=phase_85_risk_register_prototype
risk_register_prototype_version=0.1
risk_register_prototype_status=implemented
risk_register_command=pcae risk-register --json
risk_count=13
risk_types_implemented=13
risk_statuses_used=4
tests_added=31
total_test_count=7050
artifact_index_reused=true
memory_snapshot_reused=true
governance_timeline_reused=true
decision_log_reused=true
read_only=true
storage_created=false
cache_created=false
pcae_storage_created=false
authorization_inference=false
accepted_risk_is_not_mitigation=true
stale_signal_visible=true
must_never_repeat_visible=true
backend_invocation_performed=false
