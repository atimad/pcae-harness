# Phase 134B.1 Complete — External Notification Investigation & Isolation Repair

## 1. Phase Identity

- **Phase ID:** `134B.1`
- **Status:** completed
- **Phase class:** dedicated implementation repair
- **Report completeness:** complete
- **Runtime:** Observed; maximum capability `observe`; execution unavailable

## 2. Executive Summary

Phase 134B.1 verified that pytest inherited live Telegram configuration from a
sourced operator shell. Ordinary synthetic report tests and child processes
could therefore invoke production finalization against the external operator
channel. A minimal test-wide environment boundary now disables external
delivery for ordinary tests while preserving explicit governed live opt-in and
unchanged production PFN-001 behavior.

## 3. Architectural Findings

No architecture changed. The defect sat at the test boundary, not in PFN-001,
production adapter selection, idempotency, retry, or phase completion.
Production correctly honored its environment; synthetic tests supplied the
wrong authority context by ambient inheritance.

## 4. Implementation Findings

`tests/conftest.py` now clears notification enablement, sink selection,
Telegram enablement, token, and chat ID before every ordinary test. Subprocesses
inherit the isolated parent environment. `PCAE_TEST_ALLOW_LIVE_NOTIFICATIONS=1`
preserves deliberate governed live integration testing. Four focused tests
cover in-process isolation, subprocess inheritance, pre-existing live config,
and opt-in.

## 5. Verification Findings

Repository artifacts prove eight synthetic filesystem notification events in
the incident window. The 134B idempotency marker proves one legitimate logical
delivery and the explicit second completion skipped. Telegram has no durable
per-attempt local ledger, so the exact external message count is not
reconstructible from repository evidence. No retry, replay, cache, duplicate
logical completion, or second production path was found.

## 6. Technical Debt Review

The missing durable per-attempt Telegram receipt ledger remains Track 134 debt
and prevents exact after-the-fact external count reconstruction. Filesystem
test diagnostics and mixed test environment styles are non-external-risk debt.
No broader notification or lifecycle work was performed.

## 7. Notable Engineering Knowledge

Production-disabled-by-default is not a test isolation guarantee when the test
runner inherits an enabled production environment. A safe boundary must remove
ambient external authority before both in-process code and child processes.
Exactly-once logical delivery remains distinct from Telegram's message plus
document physical artifacts.

## 8. Governance Results

- `pcae check`: passed.
- task memory: clean.
- governed commit/push commands only.
- Telegram remains configured for the one genuine completion delivery.
- Runtime remains Observed; execution unavailable.

## 9. Test Results

- Focused external-notification/finalization regressions: 298 passed.
- Fast-green: 4390 passed.
- `compileall`: passed.
- Production notification behavior remains covered by existing fake-adapter
  tests; no live test dispatch was required.

## 10. No-Go Confirmation

No 134C, notification/PFN redesign, Track 134 lifecycle implementation,
Canonical Engineering Evidence, Operator Report, Repository Intelligence,
adapter, production source, schema, runtime, or execution work occurred. No raw
git commit/push, `--no-verify`, or force push was used.

## 11. Architectural Boundary Confirmation

PFN-001 remains mandatory and unchanged. Exactly-once certification and marker
behavior are untouched. Production commands outside pytest resolve and deliver
the same configuration as before. Future Track 134 receipt architecture remains
deferred.

## 12. Track Progress

134B.1 is a dedicated repair inserted after contract freeze. It restores safe
test isolation without advancing the 134C verification or 134D–134F
implementation sequence.

## 13. Next Phase

Recommended: **134C — Canonical Phase Finalization & Reporting Lifecycle
Contract Verification**. Phase 134C has not begun.
