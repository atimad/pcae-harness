# Phase 149O.20L.7O.3C.3.1 Complete — Auto-Publish Corrupt-Store Fail-Closed Repair

**Verdict: AUTO-PUBLISH CORRUPT-STORE DEFECT REPAIRED — INDEPENDENT
VERIFICATION PENDING — NOT CLOSED. UNRELATED CORRUPT SESSION NO LONGER
CRASHES `pcae phase complete`. RELEVANT CORRUPT SESSION FAILS CLOSED
(`application_error`, no session fabricated). PLAN B+ HAPPY PATH, HUMAN
AUTHORITY, CHGR UNIQUENESS, AND PERMISSION BROKER COVERAGE ALL PRESERVED.
DUPLICATE-`subject_ref` AMBIGUITY EXPLICITLY NOT REPAIRED, CARRIED
FORWARD UNCHANGED. RUNTIME: Observed / observe / unavailable. RELEASE:
BLOCKED PENDING INDEPENDENT REPAIR VERIFICATION (149O.20L.7O.3C.3.2).**

## Summary

Repairs BLOCKING finding `B-149O.20L.7O.3C.3-1`, independently found by
Phase 149O.20L.7O.3C.3: an unrelated, corrupt/unreadable Interactive
Workflow session file anywhere under `.pcae/decision-sessions/` crashed
`pcae phase complete` with an uncaught `SessionStoreCorruptError`/
`PersistenceUnavailableError`, for phases that have nothing to do with
Interactive Workflow.

**Historical crash reproduction:** independently confirmed at phase
entry, before any production source was touched — via `git show` against
the fixed phase-entry commit (`2fd7fe3a`), 3C.3's own existing
regression test, and a fresh literal subprocess-level `pcae phase
complete` E2E run once against unmodified source (exit code 1, full
Python traceback ending in `SessionStoreCorruptError`).

**Root cause / exact call graph:** `pcae phase complete` →
`run_phase_complete()` → `auto_publish_confirmed_session()` →
`find_confirmed_session()` → `SessionApplicationService.
find_session_by_subject_ref()`'s full-scan loop (`SessionCoordinator.
list_session_ids()` + `load_session()` for every id) → `Filesystem
SessionRepository.load()` raises `SessionStoreCorruptError` on malformed
JSON. The scan loop caught only `SessionNotFoundError`;
`auto_publish_confirmed_session`'s own `except` clauses covered only
`ApplicationServiceError` (a sibling, unrelated hierarchy), and only
around the later publish calls, not the lookup call itself.
`run_phase_complete` wraps the whole block in no `try`/`except`.

**Chosen error-ownership layer:** `SessionApplicationService.
find_session_by_subject_ref` (the method that owns the scan loop), with
a consistent second layer at `auto_publish_confirmed_session` (which
already owns exception-to-outcome translation for every other
`ApplicationServiceError` on the publish path).

**Unrelated-vs-relevant corruption semantics:** the scan loop now
catches and translates `SessionStoreCorruptError`/
`PersistenceUnavailableError` per record, continues scanning
deterministically (every id still visited regardless of which is
corrupt), and (a) returns a genuinely readable match for `subject_ref`
unconditionally if one exists — corruption elsewhere cannot mask a real
match; (b) if no readable match exists and corruption was encountered,
raises the translated application error instead of returning `None` —
possibly-relevant corruption is never laundered into "no governance
state exists". `auto_publish_confirmed_session` converts that exception
into the existing `STATUS_APPLICATION_ERROR` outcome.

**Production files changed (2):** `src/pcae/interactive_workflow/
application/session_service.py`, `src/pcae/commands/
governance_auto_publication.py`. `run_phase_complete` (`phase.py`) is
unchanged.

**Duplicate-`subject_ref` ambiguity** (3C.3's separate NON-BLOCKING
finding): explicitly **not repaired**, per this phase's own narrow
scope — carried forward unchanged and pinned by a regression test.

**Tests:** 14 new (`tests/test_phase_149o_20l_7o_3c_3_1_auto_publish_
corrupt_store_fail_closed_repair.py`), including a mandatory literal
subprocess-level `pcae phase complete` E2E (before-repair crash
reproduction and after-repair confirmation). 3C.3's own 22-test suite
re-run with one test's assertions updated in place to match the now-
repaired behavior (the prior "raises uncaught `SessionStoreCorruptError`"
expectation *was* the documented defect); 21 of 22 unchanged.

**Regressions:** 3C.2's 117-test suite, session/publication lifecycle
suites (284 tests), architecture/policy suites (180 tests), CHGR/
Permission Broker/publication-coordinator/task-finish suites (585 tests,
2 pre-existing unrelated `python -m build` wheel-packaging failures,
independently reproduced identical against `git stash`-clean phase-entry
source), the full `test_phase.py` (886 tests), `test_session.py` (145
tests), and notification suites (56 tests) — all pass.

**Fast Green:** genuine A/B via disposable `git worktree` at phase-entry
commit `2fd7fe3a`. Baseline: 335 failed/8692 passed/9 errors. With this
phase's diff: 351 failed/8676 passed/9 errors. Every one of the 17
newly-failing + 1 newly-passing nodeid-level deltas individually
investigated: 16 are the pre-existing "working tree dirty" sentinel-test
category (documented precedent in 3C.2's own report), the remaining 2
(1 newly-failing + 1 newly-passing) are confirmed test-order/collection
flakes (pass in isolation, touch no file this phase's diff modifies);
two further transient-concurrency flakes surfaced during background
commit activity, also confirmed passing in isolation. Deselecting the
union (354 nodeids): **0 failed, 8673 passed, 5 skipped, 9 pre-existing
errors.** Zero attributable regressions.

**Runtime:** `Observed`/`observe`/`unavailable`, unchanged before and
after this phase's work.

**Release:** v0.3.2 remains **NOT RELEASED**. No tag, GitHub Release,
artifact upload, or PyPI publication occurred. No version changed. The
unpinned-`hatchling` reproducible-build issue remains open, carried
forward unmodified. The article track remains stopped;
`~/repos/pcae-deepseek-research` was not inspected, modified, or
imported from.

**This phase does not close its own finding.** Recommended next phase:
`149O.20L.7O.3C.3.2 — Auto-Publish Corrupt-Store Repair Independent
Verification`.

See `docs/PHASE_149O_20L_7O_3C_3_1_AUTO_PUBLISH_CORRUPT_STORE_FAIL_CLOSED_REPAIR.md`
for the full call-graph/root-cause narrative and complete test/evidence
inventory.
