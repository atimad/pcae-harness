# Phase 88J Commit/Push Preflight Design

## 1. Purpose

Define the commit/push preflight boundary for PCAE: how PCAE should evaluate
proposed commit and push actions before any commit is created or push performed.
Preserves existing governed commit/push concepts while making future checks
explicit, non-authorizing, evidence-based, and deny-by-default.

88J defines the commit/push preflight boundary but does not implement it. No
commit is created, no push is performed, no raw git push is executed, no force
push is allowed, and no commit/push permission is granted in this phase.

## 2. Scope

Design and planning only.

## 3. Non-Goals

Implementing commit/push preflight, altering pcae push, or implementing
broker/shell gate.

## 4. Starting Point from 88A–88I

Three explicit preflight commands exist: `pcae preflight scope` (88B),
`pcae preflight backend` (88E), `pcae preflight mutation` (88H). Each
hardened with edge-case tests and false-positive/false-negative review
(88C, 88F, 88I). Commit/push preflight completes the preflight chain.

## 5. Relationship to Existing Governed Commit Lifecycle

PCAE's `pcae commit implementation` creates governed commits with pcae check
validation, task scope enforcement, and session continuity. Commit/push
preflight would sit before commit creation, evaluating evidence.

## 6. Relationship to Existing Governed Push Lifecycle

`pcae push` is the governed push path: validates health, check, task-memory,
push-check, then pushes. Commit/push preflight would evaluate push readiness
without replacing pcae push.

## 7. Relationship to pcae push check

`pcae push check` validates branch, working tree, unpushed commits, health,
check, task-memory, and lifecycle review. Commit/push preflight would consume
push-check results as evidence.

## 8. Relationship to pcae push

`pcae push` remains the only governed push path. Commit/push preflight must
not replace it. Future integration: preflight could become an additional
evidence gate that pcae push consumes.

## 9–11. Relationship to Scope/Backend/Mutation Preflight

Commit/push preflight consumes evidence from scope, backend, and mutation
preflights. Scope allow + backend review + mutation review together still
do not authorize commit/push — commit/push preflight adds its own checks.

## 12. Why Commit/Push Is High Risk

1. **Persistence.** Commits create permanent git history.
2. **Distribution.** Push distributes changes to remote/shared state.
3. **Irreversibility.** Force push can destroy upstream history.
4. **Raw push bypass.** Raw git push bypasses all governance.
5. **Chain finality.** Push is the final step in the mutation chain.

## 13. Commit Request Model

| Field | Type | Required |
|-------|------|----------|
| `requested_action` | string | yes |
| `requested_files` | list[string] | no |
| `staged_files` | list[string] | no |
| `unstaged_files` | list[string] | no |
| `untracked_files` | list[string] | no |
| `diff_present` | boolean | no |
| `diff_hash` | string | no |
| `commit_message_present` | boolean | yes |
| `commit_message` | string | no |
| `commit_message_hash` | string | no |
| `task_contract_detected` | boolean | yes |
| `task_contract_path` | string | no |
| `scope_preflight_decision` | string | no |
| `backend_preflight_decision` | string | no |
| `mutation_preflight_decision` | string | no |
| `adoption_preflight_decision` | string | no |
| `human_approval` | object | no |
| `risk_register` | object | no |
| `decision_log` | object | no |
| `project_state` | object | no |
| `lifecycle_state` | string | yes |
| `current_branch` | string | no |
| `head_commit` | string | no |
| `base_commit` | string | no |
| `origin_main_ahead_count` | integer | no |
| `origin_main_behind_count` | integer | no |

## 14. Push Request Model

| Field | Type | Required |
|-------|------|----------|
| `requested_action` | string | yes |
| `current_branch` | string | yes |
| `remote_name` | string | no |
| `remote_branch` | string | no |
| `upstream_branch` | string | no |
| `head_commit` | string | no |
| `local_ahead_count` | integer | no |
| `local_behind_count` | integer | no |
| `origin_main_ahead_count` | integer | no |
| `origin_main_behind_count` | integer | no |
| `push_check_result` | string | no |
| `pcae_check_result` | string | no |
| `pcae_health_result` | string | no |
| `pcae_doctor_result` | string | no |
| `full_suite_result` | string | no |
| `quick_suite_result` | string | no |
| `task_contract_detected` | boolean | yes |
| `task_contract_path` | string | no |
| `human_approval` | object | no |
| `risk_register` | object | no |
| `decision_log` | object | no |
| `project_state` | object | no |
| `lifecycle_state` | string | yes |
| `force_push_requested` | boolean | yes |
| `raw_git_push_requested` | boolean | yes |

## 15. Commit/Push Preflight Output Model

48 fields including preflight_type, requested_action, decision, reason_codes,
all preflight evidence fields, git state fields, check/health/doctor/test
results, and safety flags (authorization_granted, execution_authorized,
commit_performed, push_performed, raw_git_push_performed, force_push_performed,
repo_mutation_performed, storage_written — all always false).

## 16. Commit Decision Model

Commit requires: task contract, commit message, staged changes matching scope,
passing pcae check. Source/test changes require mutation preflight evidence.
Backend-originated changes require backend evidence.

## 17. Push Decision Model

Push requires: clean working tree, passing push check, passing pcae check,
passing health, passing doctor, passing tests, known branch/upstream, no
raw git push, no force push. Governed pcae push is the only valid path.

## 18. Deny-by-Default Rules

1. Missing task contract → deny
2. Dirty git state without commit context → deny
3. Missing commit message → blocked_by_missing_commit_message
4. Missing diff/staged evidence → requires_more_evidence
5. Scope denied → blocked_by_scope
6. Mutation denied → blocked_by_mutation_policy
7. Backend denied → blocked_by_backend_policy
8. Missing tests → blocked_by_missing_tests
9. Failed tests → blocked_by_failed_tests
10. Failed check → blocked_by_failed_check
11. Failed health → blocked_by_failed_health
12. Failed doctor → blocked_by_failed_doctor
13. Failed push check → blocked_by_push_check
14. Raw git push → blocked_by_raw_git_push
15. Force push → blocked_by_force_push
16. Unknown branch/upstream → blocked_by_branch_state
17. Active risk → blocked_by_risk
18. Must-never-repeat → deny
19. Unknown action → unknown
20. Human approval without evidence → not enough
21. Accepted risk → not mitigation

## 19. Human Review Model

Required for: any commit, any push, source/test/governance changes, push to
main, branch divergence, failed/missing tests/checks, untracked files,
generated artifacts, backend-originated output, adoption execution, raw git
push attempt, force push attempt, accepted-risk/must-never-repeat overrides,
missing/stale contract, unknown action/branch.

## 20. Evidence Model

Active task contract, changed files, staged/unstaged/untracked state, diff
hash, commit message/hash, scope/backend/mutation preflight decisions, test
results, pcae check/health/doctor/push-check results, branch/upstream state,
risk/decision/project-state evidence, human approval.

## 21. Git State Model

Clean working tree before push. Known branch/upstream. Known ahead/behind.
No untracked files unless explicitly accounted. No raw git push. No force
push. Governed pcae push only.

## 22. Diff/Staging Model

Commit preflight must know what will be committed. Staged changes must match
task scope. Unstaged/untracked files are risk signals.

## 23. Commit Message Model

Must be explicit and match phase/task intent. Presence is not approval.

## 24. Branch/Remote/Upstream Model

Known branch, known remote, known upstream, known ahead/behind counts.
Branch divergence requires human review.

## 25. Raw Git Push / Force Push Controls

Raw git push: forbidden in governed lifecycle. Force push: denied unless
future emergency rollback policy defines otherwise.

## 26. Existing pcae push Preservation

pcae push remains the only governed push path. Commit/push preflight does
not replace it.

## 27–28. Permission Broker / Shell Gate Relationship

Future broker may combine all preflights + checks + branch state + human
review. Shell gate mediates actual git commit/push execution.

## 29. Audit Requirements

13 future audit events including commit/push preflight request/decision/denied/
review/evidence and raw_git_push/force_push attempt detection.

## 30. Storage/Cache Policy

No storage in 88J. Future requires separate phase.

## 31. Failure Handling

Missing contract → deny. Missing commit message → deny. Failed tests/check/
health/doctor/push-check → deny. Raw git push → deny. Force push → deny.
Unknown state → never allow.

## 32. Safety Invariants

21 invariants: 88J does not implement/create/push/force/mutate/invoke/capture.
Future must deny by default, require human review, not bypass preflights/tests/
checks, not permit raw/force push, preserve evidence.

## 33. Future Test Strategy

27 test areas for 88K covering commit/push requests with various evidence
combinations, raw/force push blocking, and all safety flags remaining false.

## 34. Future Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| **88K** | Commit/Push Preflight Prototype |
| **88L** | Commit/Push Preflight Tests and False-Positive Review |
| **88M** | Scope + Backend + Mutation + Commit/Push Preflight Integration Verification |
| **88N** | Permission Broker Design Reconciliation |
| **88O** | Shell Gate Design Reconciliation |

## 35. Recommended Next Phase

**88K — Commit/Push Preflight Prototype.**

---

commit_push_preflight_design_name=phase_88_commit_push_preflight_design
commit_push_preflight_design_version=0.1
commit_push_preflight_design_status=draft_documented
implementation_status=not_started
commit_actions=10
commit_request_model_fields=26
push_request_model_fields=25
output_model_fields=48
decision_values=23
deny_by_default_rules=21
human_review_triggers=19
audit_event_types=13
failure_conditions=15
safety_invariants=21
future_test_areas=27
recommended_next=88K
backend_invocation_performed=false
commit_performed=false
push_performed=false
