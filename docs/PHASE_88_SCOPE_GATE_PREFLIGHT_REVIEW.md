# Phase 88C Scope Gate Preflight Tests and False-Positive Review

## 1. Purpose

Harden and review the scope gate preflight prototype (88B) before expanding
to later preflight gates. Verify conservative behavior across edge cases,
document false-positive and false-negative risks, and record a readiness
decision.

## 2. Scope

88C adds:

- 63 focused edge-case tests in `tests/test_scope_preflight_review.py`.
- This review artifact documenting false-positive and false-negative risks.

88C does not modify the scope preflight implementation.

## 3. Non-Goals

- Backend invocation preflight implementation.
- Mutation/adoption preflight implementation.
- Commit/push preflight implementation.
- Shell interception.
- Permission broker or shell gate.
- Storage, cache, or `.pcae` persistent state.
- CLI command expansion.
- Broad enforcement.

## 4. Relationship to 88B

Phase 88B implemented `pcae preflight scope` with 66 tests. 88C adds 63
additional edge-case tests and this false-positive/false-negative review
without modifying the implementation.

## 5. Test Coverage Added

63 tests covering:

- Allowed file exact match (PROJECT_STATUS.md, CHANGELOG.md, task contract)
- Allowed file glob match (test file, docs review file)
- Forbidden file exact match (README.md, docs/REAL_CAPTURED_TASKS.md, LinkedIn)
- Forbidden file glob match (.pcae/**, .githooks/**)
- Allowed/forbidden conflict (forbidden wins, single forbidden blocks all)
- Multiple files all allowed (2 files, 3 files)
- Multiple files mixed allowed/forbidden (1+1, 2+1)
- Multiple files mixed allowed/unknown (1+1 combinations)
- Unknown file with known action (read, source_mutation)
- Known file with unknown action (allowed file, forbidden file)
- Unknown action with unknown file
- Read action on docs file (allowed docs, forbidden docs)
- docs_mutation on allowed docs file
- docs_mutation on docs/REAL_CAPTURED_TASKS.md (blocked)
- source_mutation on allowed src file
- source_mutation on unknown src file
- source_mutation on docs file (allowed — scope matching is path-based)
- test_mutation on test file (allowed)
- test_mutation on src file (allowed — scope matching is path-based)
- adoption action (requires_human_review, not_scope_decidable)
- backend_invocation not broadly authorized
- commit not broadly authorized
- push not broadly authorized
- rollback not broadly authorized
- storage_write not broadly authorized
- allow_preflight never sets execution_authorized=true
- allow_preflight never sets authorization_granted=true
- Multi-file allow_preflight still non-authorizing
- All negative decisions preserve repo_mutation_performed=false
- All negative decisions preserve storage_written=false
- All negative decisions preserve backend_invocation_performed=false
- No .pcae cache/state directories created
- No .pcae state files created
- No repository mutation after multiple runs
- gate-dry-run still works (15 gates, dry_run=true)
- All 6 read-only intelligence commands still work
- Reason code preflight_only_not_execution_authorization always present
- Deterministic output for allow and deny
- Empty-string action handled as unknown

## 6. Edge Cases Reviewed

| Edge Case | Behavior | Status |
|-----------|----------|--------|
| Allowed exact match | allow_preflight | Correct |
| Allowed glob match | allow_preflight | Correct |
| Forbidden exact match | blocked_by_scope | Correct |
| Forbidden glob match (.pcae/**) | matched_forbidden or requires_human_review | Correct |
| Allowed + forbidden conflict | deny_preflight (forbidden wins) | Correct |
| Multiple files all allowed | allow_preflight | Correct |
| Mixed allowed + forbidden | deny_preflight | Correct |
| Mixed allowed + unknown | requires_human_review | Correct |
| Unknown file, known action | requires_more_evidence | Correct |
| Known file, unknown action | requires_human_review | Correct |
| Unknown action + unknown file | requires_human_review | Correct |
| Not-scope-decidable actions | requires_human_review | Correct |
| Empty-string action | requires_human_review (unknown_action) | Correct |
| Deterministic repeated calls | Same decision/reason_codes | Correct |
| No files requested | requires_more_evidence | Correct |

## 7. False-Positive Risks

Risks where PCAE could incorrectly **allow**:

| Risk | Description | Severity | Status |
|------|-------------|----------|--------|
| FP-001 Glob too broad | An allowed_files glob like `src/**` could match files the operator did not intend | Medium | Mitigated: task contracts should use specific paths |
| FP-002 Docs file treated as safe | `docs_mutation` on an allowed docs path returns allow_preflight even if the content is sensitive | Low | Accepted: scope preflight evaluates path only, not content |
| FP-003 Read confused with mutation | `read` action returns allow_preflight; if caller then mutates, scope preflight did not prevent it | Medium | Mitigated: allow_preflight does not authorize execution |
| FP-004 Multi-file hides forbidden | If many allowed files accompany one forbidden file, the forbidden is still caught (deny_preflight) | Low | Mitigated: verified by test — forbidden always blocks |
| FP-005 Unknown action treated as low-risk | Unknown actions return requires_human_review, not allow | Low | Mitigated: unknown_action reason code + human_review_required=true |
| FP-006 Accepted risk as mitigation | allow_preflight might be misinterpreted as accepted-risk mitigation | Medium | Mitigated: authorization_granted=false, execution_authorized=false |
| FP-007 Task contract stale | Active task contract might reference old/wrong allowed files | Medium | Deferred: stale contract detection not yet implemented |
| FP-008 Unexpected task discovery | _detect_task_contract picks first .md in tasks/active/ — multiple contracts could cause wrong selection | Medium | Deferred: only one active task expected by convention |
| FP-009 Path-based scope ignores action type | source_mutation on a docs file returns allow_preflight if the path matches | Low | Accepted: scope preflight evaluates path scope only |

## 8. False-Negative Risks

Risks where PCAE could incorrectly **block**:

| Risk | Description | Severity | Status |
|------|-------------|----------|--------|
| FN-001 Allowed glob too narrow | Task contract uses exact paths instead of globs, missing legitimate files | Medium | Mitigated: task contracts can use glob patterns |
| FN-002 Generated docs not recognized | docs/COMMANDS.md is generated but may not appear in allowed_files | Medium | Mitigated: add docs/COMMANDS.md to task contract |
| FN-003 Renamed files not covered | If a file is renamed, the old path won't match allowed patterns | Low | Accepted: task contract should be updated when files are renamed |
| FN-004 Multi-file blocked by one unknown | Two allowed files + one unknown file → requires_human_review instead of allow | Low | Correct behavior: conservative is intentional |
| FN-005 Missing explicit docs path | Task contract lists `docs/PHASE_88_*.md` but not all docs files | Low | Mitigated: use broader glob if needed |
| FN-006 Active but stale contract | Task contract is marked complete but still in tasks/active/ | Low | Deferred: contract lifecycle validation not implemented |
| FN-007 Validation command mistaken for mutation | `read` on a forbidden file returns blocked_by_scope — correct but potentially surprising | Low | Correct behavior: forbidden means forbidden for all actions |

## 9. Conservative Decision Policy

The scope gate preflight follows a deny-by-default, conservative decision policy:

1. **No task contract** → blocked_by_missing_task_contract
2. **Forbidden file** → blocked_by_scope or deny_preflight
3. **Unknown file** → requires_more_evidence or requires_human_review
4. **Unknown action** → requires_human_review
5. **Not-scope-decidable action** → requires_human_review
6. **All files allowed, scope-decidable action** → allow_preflight (only case)
7. **allow_preflight** → does NOT set authorization_granted or execution_authorized

The only path to allow_preflight requires: (a) active task contract, (b) known
scope-decidable action, (c) all requested files match allowed patterns, (d) no
requested files match forbidden patterns.

## 10. Non-Authorizing Boundary

Verified by tests:

- allow_preflight never sets `execution_authorized=true`
- allow_preflight never sets `authorization_granted=true`
- All decisions preserve `repo_mutation_performed=false`
- All decisions preserve `storage_written=false`
- All decisions preserve `backend_invocation_performed=false`
- `preflight_only_not_execution_authorization` reason code always present

## 11. No-Write/No-Storage Verification

Verified by tests:

- No `.pcae/cache`, `.pcae/gates`, `.pcae/scope`, `.pcae/preflight`,
  `.pcae/broker`, `.pcae/shell_gate` directories created
- No `.pcae/preflight_state.json`, `.pcae/scope_preflight.json`,
  `.pcae/gate_state.json`, `.pcae/scope_decisions.json`,
  `.pcae/preflight_log.json` files created
- No repository mutation after multiple preflight runs
- gate-dry-run and all read-only intelligence commands still work

## 12. Remaining Limitations

1. Scope preflight evaluates path scope only — it does not enforce action type
   against file type (e.g., source_mutation on a docs file is path-allowed if
   the path matches).
2. No stale task contract detection.
3. No multi-contract disambiguation.
4. No human-approval bypass flag exists — human-approval bypass testing deferred.
5. No lifecycle state integration beyond "active" when task contract exists.
6. No must-never-repeat control integration.
7. No risk register integration.
8. Scope preflight is not sufficient for automatic shell enforcement or broad
   action authorization.

## 13. Readiness Decision

**ready_for_backend_invocation_preflight_design**

The scope gate preflight prototype behaves conservatively across all tested
edge cases. No critical false-positive or false-negative flaws found. The
deny-by-default policy correctly prevents unauthorized access. The non-authorizing
boundary is verified. The command is ready to serve as the foundation while
the next preflight gate (backend invocation) is designed.

## 14. Recommended Next Phase

**88D — Backend Invocation Preflight Design.**

After the scope preflight prototype has been tested for false positives and
negatives, the next phase should design backend invocation preflight boundaries
before implementing any backend-related enforcement.

---

phase_88c_name=scope_gate_preflight_tests_and_false_positive_review
phase_88c_version=0.1
phase_88c_status=complete
review_tests_added=63
false_positive_risks_documented=9
false_negative_risks_documented=7
critical_flaws_found=0
source_changes_required=false
conservative_decision_policy=documented
non_authorizing_boundary=verified
no_write_no_storage=verified
readiness_decision=ready_for_backend_invocation_preflight_design
recommended_next=88D
backend_invocation_performed=false
