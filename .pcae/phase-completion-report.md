# Phase 149F Complete — Repository-Wide Mutation Permission Coverage Wave 1 Implementation

**Phase ID:** 149F
**Mode:** Bounded production implementation of RWMPC-001 v1.0 Wave 1
(six sites: AG1, AG2, AG4, PH1, PH2, PH3; no contract amendment; no
`POL-001..012` semantic change; no `POL-013+`; no runtime capability
change)
**Predecessor:** 149E (Repository-Wide Mutation Permission Coverage
Implementation Plan — completed, verdict IMPLEMENTATION PLAN COMPLETE,
WAVE 1 READY)
**Date:** 2026-08-03
**Status:** completed
**Pushed:** not_pushed (staged pre-push; promote via `pcae phase
complete` after `pcae push`)

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149F_REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_WAVE_1_IMPLEMENTATION.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149F implements RWMPC-001 v1.0 Wave 1: broker-wires AG1
(`commit_file_changes`), AG2 (`push_file_changes`), AG4
(`build_promotion_execution`), and PH1 (backend-created-output-adoption
commit, consolidated with AG1); canonically routes PH2 and PH3
(backend-created-output-adoption push, final-verification-tooling push)
through AG2's new shared dispatcher `agent._dispatch_governed_push` —
zero independent `git push` dispatch remains in `phase.py`.

**Architecture:** new shared module `src/pcae/core/mutation_permission.py`
is the sole non-`pcae push` `PermissionBrokerRequest` constructor in the
codebase, generalizing `push.py`'s certified
`_evaluate_push_permission`/`_PushDecisionSnapshot`/
`_validate_push_permission_freshness` pattern. Commit-class freshness
binds `(HEAD, git write-tree staged-content identity, task_id)`;
alternate-push freshness binds `(HEAD, unpushed-commit count against
<remote>/<branch>, task_id)`; promotion freshness binds `(EPR id, ECP
id, approved_paths identity, task_id)`, reusing the existing ECP/EPR/PER
integrity model, zero new digest invented. `push.py`, `task.py`,
`permission_broker_foundation.py`, `permission_broker.py`, and
`docs/contracts/**` are all byte-unchanged.

AG3, AG5 (rollback) and TK1, TK2, TK3 (task-finish) remain untouched and
explicitly unresolved, per RWMPC-001 §12.1/Section 14 — not silently
dropped. AG4's self-modification risk (`pcae promote` targeting
`src/pcae/**`) still has no new mechanical hard block, per RWMPC-REQ-019;
the permission boundary applies identically regardless of target,
directly confirmed by test.

New AST-based mutation inventory guard classifies all 13 sites with zero
`UNKNOWN` and confirms no 14th mutation-dispatch site exists anywhere in
`src/pcae/`. Full 30-file historical Permission-Broker-guard sweep
(closing 149E's F-149E-1 partial-scope finding) found and narrowly
repaired one genuinely stale invariant. 51 new Wave-1 tests across 6
files; `test_agent.py` (4236 tests) and the lifecycle/phase suite (954
tests) both fully green after narrow fixture repairs (missing
active-task contracts — now a genuine precondition for AG1/AG2/AG4's
real permission evaluation). Fast Green: 4391 passed, identical to the
pre-149F baseline.

**Verdict: WAVE 1 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION.**
Zero Blocking findings; three Observation-level findings recorded.

Production diff: `git diff --stat 5392a7cd..HEAD -- src/pcae/` shows
`src/pcae/commands/phase.py` and `src/pcae/core/agent.py` changed, plus
new `src/pcae/core/mutation_permission.py`; `push.py`, `task.py`,
`permission_broker_foundation.py`, and `permission_broker.py` are all
byte-unchanged (empty diffs). Existing-contract diff: `git diff
--name-only 5392a7cd..HEAD -- docs/contracts/` empty (RWMPC-001 remains
v1.0, PBPC-001 remains v1.2, PBPA-001 remains v1.0, all unamended).
Runtime reconfirmed Observed/observe/unavailable before and after.
Recommended next phase: **149G — Repository-Wide Mutation Permission
Coverage Wave 1 Independent Verification**, before any Chapter 149
completion claim. See
`docs/PHASE_149F_REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_WAVE_1_IMPLEMENTATION.md`
for full detail.
