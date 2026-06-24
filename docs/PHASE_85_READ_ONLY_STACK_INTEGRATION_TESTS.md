# Phase 85 Read-Only Stack Integration Tests

## 1. Purpose

Document the integration test coverage for the complete Phase 85 read-only
project-intelligence stack implemented in phases 86C through 86H.

## 2. Scope

Integration test summary only. No new CLI features, no storage, no cache.

## 3. Non-Goals

- Adding new CLI commands.
- Creating storage, cache, or `.pcae` files.
- Backend invocation, prompt sending, capture, intake, or adoption.
- Modifying README.md or existing design/prototype artifacts.

## 4. Commands Covered

| Command | Phase | Layer |
|---------|-------|-------|
| `pcae artifact-index --json` | 86C | Evidence lookup |
| `pcae memory-snapshot --json` | 86D | Entity state |
| `pcae governance-timeline --json` | 86E | Temporal ordering |
| `pcae decision-log --json` | 86F | Durable decisions |
| `pcae risk-register --json` | 86G | Risk state |
| `pcae project-state --json` | 86H | Integrated answer |

## 5. Integration Guarantees Tested

- All six commands exit successfully
- All six commands emit valid JSON
- All six commands include schema_version, source_command, repository_root
- All six commands include warnings, errors, safety_notes
- Each command includes its expected primary data structure

## 6. Cross-Layer Consistency Checks

- project-state layer_summary.artifact_index.record_count matches artifact-index record_count
- project-state layer_summary.governance_timeline.event_count matches governance-timeline event_count
- project-state layer_summary.decision_log.decision_count matches decision-log decision_count
- project-state layer_summary.risk_register.risk_count matches risk-register risk_count
- project-state evidence_artifacts matches artifact-index current artifact paths
- project-state active_risks matches risk-register active risk IDs
- project-state accepted_risks matches risk-register accepted risk IDs
- project-state stale_signals matches risk-register stale_signal risk IDs

## 7. Read-Only / No-Storage Checks

- No .pcae/cache, .pcae/state, .pcae/snapshots, .pcae/timelines, .pcae/decisions,
  .pcae/risks, .pcae/memory, .pcae/index directories created
- No repository mutation (git status --porcelain unchanged after running all commands)

## 8. Authority-Inference Checks

- All six commands have safety notes confirming no execution authorization
- Five commands (memory-snapshot through project-state) confirm no backend invocation authorization
- All six commands confirm no adoption authorization
- All six commands confirm no commit/push authorization
- project-state high-risk authorization booleans all false
- decision-log authorization flags all false for high-risk keys
- next_safe_actions are explicitly labeled as recommendations, not authorizations

## 9. Accepted-Risk / Stale-Signal / Must-Never-Repeat Checks

- Accepted risks are separate from active risks (no ID overlap)
- Accepted risk not treated as mitigated (mitigation=null, acceptance_rationale set)
- Stale signals visible in project-state
- Must-never-repeat controls visible in project-state
- Must-never-repeat risk types visible in risk-register (raw_push, hook_bypass, must_never_repeat)

## 10. Tests Added

38 tests in `tests/test_phase85_integration.py`:

1. `test_all_commands_exit_successfully`
2. `test_all_commands_emit_valid_json`
3. `test_all_commands_have_schema_version`
4. `test_all_commands_have_source_command`
5. `test_all_commands_have_repository_root`
6. `test_all_commands_have_warnings_errors_safety_notes`
7. `test_artifact_index_has_records`
8. `test_memory_snapshot_has_snapshot`
9. `test_governance_timeline_has_events`
10. `test_decision_log_has_decisions`
11. `test_risk_register_has_risks`
12. `test_project_state_has_snapshot`
13. `test_project_state_layer_summary_reflects_artifact_index`
14. `test_project_state_layer_summary_reflects_timeline`
15. `test_project_state_layer_summary_reflects_decision_log`
16. `test_project_state_layer_summary_reflects_risk_register`
17. `test_project_state_latest_completed_phase_populated`
18. `test_project_state_recommended_next_phase_populated`
19. `test_project_state_active_risks_from_risk_register`
20. `test_project_state_accepted_risks_from_risk_register`
21. `test_project_state_stale_signals_from_risk_register`
22. `test_project_state_evidence_from_artifact_index`
23. `test_accepted_risk_separate_from_active`
24. `test_accepted_risk_not_treated_as_mitigated`
25. `test_stale_signals_visible_in_project_state`
26. `test_must_never_repeat_visible_in_project_state`
27. `test_must_never_repeat_visible_in_risk_register`
28. `test_project_state_forbidden_actions`
29. `test_project_state_next_safe_actions_are_recommendations`
30. `test_project_state_high_risk_auth_false`
31. `test_decision_log_auth_flags_all_false`
32. `test_all_commands_no_execution_authorization`
33. `test_all_commands_no_backend_invocation_authorization`
34. `test_all_commands_no_adoption_authorization`
35. `test_all_commands_no_commit_push_authorization`
36. `test_no_cache_or_state_created_by_stack`
37. `test_no_repository_mutation_by_stack`
38. `test_commands_deterministic_counts`

## 11. Validation Results

- `python -m pytest -n auto`: 7122 passed (38 new integration, 0 regressions)
- All six commands work independently and together
- Cross-layer counts match
- No storage/cache/.pcae creation
- No authority inference
- Deterministic counts across runs

## 12. Known Limitations

- Integration tests run commands via subprocess (CLI-level, not unit-level)
- Cross-layer checks validate count/ID equality, not deep field-by-field consistency
- Does not validate all possible edge cases for empty repositories
- Test runtime is significant (~4 minutes for integration suite alone due to subprocess overhead)

## 13. Recommended Next Phase

86J — Phase 86 Read-Only Stack Documentation Update.

---

integration_test_name=phase_85_read_only_stack_integration_tests
integration_test_version=0.1
integration_test_status=implemented
commands_covered=6
integration_tests_added=38
total_test_count=7122
cross_layer_consistency_checks=8
authority_inference_checks=6
no_storage_checks=2
determinism_checks=1
source_files_changed=0
backend_invocation_performed=false
phase_85_implementation_sequence_complete=true
