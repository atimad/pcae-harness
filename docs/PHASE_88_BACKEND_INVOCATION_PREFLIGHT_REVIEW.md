# Phase 88F Backend Invocation Preflight Tests and False-Positive Review

## 1. Purpose

Harden and review the backend invocation preflight prototype (88E) before
expanding to mutation/adoption preflight. Verify conservative behavior across
edge cases, document false-positive and false-negative risks, and record a
readiness decision.

## 2. Scope

88F adds 47 focused edge-case tests and this review artifact. No source changes.

## 3. Non-Goals

- Mutation/adoption preflight.
- Commit/push preflight.
- Permission broker or shell gate.
- Backend invocation or prompt sending.
- Storage, cache, or CLI expansion.

## 4. Relationship to 88E

Phase 88E implemented `pcae preflight backend` with 42 tests. 88F adds 47
additional edge-case tests and this false-positive/false-negative review.

## 5. Test Coverage Added

47 tests covering:

- All 5 known backends recognized (claude, claude-deepseek, claude-kimi, codex, subagent)
- Unknown backend denied (unknown_backend, random name, empty string)
- All known backends require human review
- Backend recognition does not authorize (authorization_granted=false, backend_allowed_by_policy=false)
- Missing prompt blocks (backend_invocation, source_mutation)
- Prompt present without hash requires more evidence
- Prompt present with hash requires human review
- Empty prompt hash treated as missing
- File-related request evaluates scope
- Scope allow still requires human review (does not authorize backend)
- Scope denied blocks (README.md, REAL_CAPTURED_TASKS.md)
- Out-of-scope file requires review/evidence
- Multi-file all in scope (allowed decision, still review)
- Multi-file mixed allowed/forbidden (blocked)
- Multi-file mixed allowed/unknown (partial scope)
- Unknown action requires review
- Unrecognized action requires review
- High-risk actions non-authorizing (commit, push, adoption, storage_write, rollback)
- All safety flags false on allow/deny/blocked paths
- No .pcae artifacts created after multiple runs
- No repository mutation after multiple runs
- Scope preflight still works
- Gate-dry-run still works (15 gates)
- All 6 intelligence commands still work
- Reason code disclaimer on review/deny/blocked paths
- Deterministic output
- Read action non-authorizing

## 6. Edge Cases Reviewed

| Edge Case | Behavior | Status |
|-----------|----------|--------|
| Known backend recognition | Recognized but not authorized | Correct |
| Unknown backend | Denied | Correct |
| Empty-string backend | Denied (unknown) | Correct |
| All backends require review | human_review_required=true | Correct |
| Missing prompt | blocked_by_missing_prompt | Correct |
| Prompt, no hash | requires_more_evidence | Correct |
| Prompt + hash | requires_human_review | Correct |
| Empty hash | Treated as missing | Correct |
| File scope allowed | Still requires review | Correct |
| File scope denied | blocked_by_scope | Correct |
| Multi-file allowed | requires_human_review | Correct |
| Multi-file forbidden | blocked_by_scope | Correct |
| Multi-file unknown | partial scope, review | Correct |
| Unknown action | requires_human_review | Correct |
| High-risk actions | Non-authorizing | Correct |
| Deterministic | Same decision/codes | Correct |

## 7. False-Positive Risks

| Risk | Description | Severity | Status |
|------|-------------|----------|--------|
| FP-001 Recognition as authorization | Known backend recognition could be misread as permission | Medium | Mitigated: backend_allowed_by_policy=false, authorization_granted=false |
| FP-002 Prompt-present as approval | prompt_present=true could be misread as prompt approved | Medium | Mitigated: requires_human_review or requires_more_evidence |
| FP-003 Prompt hash as approval | Hash presence could be misread as content approval | Low | Mitigated: still requires_human_review |
| FP-004 Scope allow as backend permission | scope allow could be misread as backend authorization | Medium | Mitigated: backend still requires_human_review |
| FP-005 File request missing scope | File-related request without scope evaluation | Low | Mitigated: scope_preflight_required=true for file actions |
| FP-006 Unknown backend normalized | Unknown backend could be coerced into known | Low | Mitigated: strict string match against known list |
| FP-007 Subagent low-risk | Subagent could be treated as lower risk than claude | Low | Mitigated: all backends require same human review |
| FP-008 Read as safe backend | Read action could be treated as safe for backend | Low | Mitigated: still non-authorizing |
| FP-009 Accepted risk as mitigation | Risk acceptance could bypass policy | Medium | Deferred: risk register not integrated |
| FP-010 Stale task contract | Old contract with wrong scope | Medium | Deferred: stale detection not implemented |
| FP-011 Wrong task selected | Multiple contracts → wrong scope | Medium | Deferred: single-contract convention |

## 8. False-Negative Risks

| Risk | Description | Severity | Status |
|------|-------------|----------|--------|
| FN-001 Backend alias | Backend name variant not recognized (e.g., "Claude" vs "claude") | Low | Accepted: case-sensitive by design |
| FN-002 Valid prompt, no hash | Legitimate prompt blocked because hash missing | Low | Correct: conservative; hash required for audit |
| FN-003 Read-only scope unavailable | Scope evaluation unavailable for read-only request | Low | Mitigated: read without files doesn't require scope |
| FN-004 Multi-file one unknown | One unknown file blocks entire request | Low | Correct: conservative is intentional |
| FN-005 Backend naming change | Backend renamed in future → unknown | Low | Accepted: update known list when backends change |
| FN-006 Missing backend metadata | Task contract lacks backend-specific info | Low | Deferred: contract schema doesn't include backends |
| FN-007 Validation as invocation | Preflight check mistaken for actual invocation | Low | Mitigated: preflight never invokes |

## 9. Conservative Decision Policy

1. Unknown backend → deny_preflight
2. Missing task contract → blocked_by_missing_task_contract
3. Missing prompt when required → blocked_by_missing_prompt
4. Prompt without hash → requires_more_evidence
5. Known backend + prompt + hash → requires_human_review
6. File scope denied → blocked_by_scope
7. Unknown action → requires_human_review
8. All paths → authorization_granted=false, execution_authorized=false

No path reaches allow_preflight without human review. No path invokes a backend.

## 10. Non-Authorizing Boundary

Verified by tests:

- authorization_granted=false on all paths
- execution_authorized=false on all paths
- backend_invocation_performed=false on all paths
- prompt_sent=false on all paths
- capture_performed=false on all paths

## 11. No-Backend/No-Prompt/No-Capture Verification

Verified: no backend subprocess invoked, no prompt files created, no capture
files created, no intake or adoption artifacts created.

## 12. No-Write/No-Storage Verification

Verified: no .pcae directories created, no state files created, no repository
mutation after multiple preflight runs.

## 13. Remaining Limitations

1. No risk register integration.
2. No lifecycle state integration beyond "active".
3. No must-never-repeat control integration.
4. No human-approval flag (deferred).
5. No stale task contract detection.
6. No multi-contract disambiguation.
7. Case-sensitive backend matching only.
8. Backend preflight is not sufficient for automatic backend execution.

## 14. Readiness Decision

**ready_for_mutation_adoption_preflight_design**

The backend invocation preflight prototype behaves conservatively across all
tested edge cases. No critical false-positive or false-negative flaws found.
The deny-by-default and human-review-required policies are verified. The
non-authorizing boundary is confirmed. The command is ready to serve as
foundation while mutation/adoption preflight is designed.

## 15. Recommended Next Phase

**88G — Mutation/Adoption Preflight Design.**

After backend invocation preflight has been tested, the next phase should
design mutation/adoption preflight boundaries.

---

phase_88f_name=backend_invocation_preflight_tests_and_false_positive_review
phase_88f_version=0.1
phase_88f_status=complete
review_tests_added=47
false_positive_risks_documented=11
false_negative_risks_documented=7
critical_flaws_found=0
source_changes_required=false
conservative_decision_policy=documented
non_authorizing_boundary=verified
no_backend_no_prompt_no_capture=verified
no_write_no_storage=verified
readiness_decision=ready_for_mutation_adoption_preflight_design
recommended_next=88G
backend_invocation_performed=false
