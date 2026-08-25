# Phase 149O.20L.7O.3F Complete — Permission Broker Rollback Default-Path Consumption Integration

**Verdict: BOUNDED SOURCE-MODIFYING INTEGRATION COMPLETE.** Human-selected
Plan B from `149O.20L.7O.3E`. Closed the sole remaining Permission Broker
production-coverage gap: `pcae rollback`'s default (non-`HATP_MANDATORY`)
dispatch path (`core/agent.py::build_rollback_execution`), which
previously had zero Permission Broker evaluation at all. Runtime unchanged
(`Observed`/`observe`/`unavailable`).

## Summary

**Baseline:** phase-entry commit `97bb9cda`, working tree clean, `origin/
main..HEAD` = 0, `v0.4.0` unchanged.

**Integration:** added `mutation_permission.evaluate_rollback_permission()`
— a new Wave-1-style adapter reusing the existing `ACTION_ROLLBACK`
literal paired with `EXECUTION_CLASS_MUTATION` (deliberately not
`EXECUTION_CLASS_ROLLBACK`, which would have triggered `POL-004`
`HUMAN_REVIEW` unconditionally and invented a new human-approval
requirement outside this phase's authorization), `COMP-008` component id
and `build_rollback_execution` capability literal (both already
registered by `hatp_ag_authority.py` for the separate HATP-gated AG5
evaluation). No new decision state, policy vocabulary, or shadow broker
was invented.

**Gate placement:** in `build_rollback_execution`, immediately after the
pre-existing, byte-unchanged `HATP_MANDATORY` gate block and immediately
before the restore/remove effect boundary, active only outside
`HATP_MANDATORY` mode — the separate, stricter, HATP-integrated gate
keeps its own untouched coverage.

**Results:** `ALLOW` permits the pre-existing dispatch behavior unchanged.
`DENY`/broker-failure/malformed-result all fail closed with zero file
mutation and a new terminal `aborted_permission_denied` RollbackExecutionRecord
status. Dry-run rollback readiness/evidence generation is entirely
unaffected — it returns before the new gate and was never gated. Human
authority (`pcae rollback --per-id X`) and runtime posture are unchanged
— permission is not execution capability.

**Production diff:** exactly two files (`core/mutation_permission.py`,
`core/agent.py`). 21 new tests added. Existing rollback (142 tests) and
Permission Broker Foundation/push/publication/policy (983 tests)
regression suites re-run with zero attributable behavioral change
(pre-existing failures in both groups confirmed identical before/after
via `git stash` comparison). Full Fast Green run twice (baseline via
`git stash` isolation, current against the diff); every one of the 19
newly-failing and 2 newly-passing node IDs individually classified as
either a frozen historical-phase source-diff/git-status tripwire
(necessarily triggered by this phase's mandated file changes) or
confirmed `pytest -n auto` parallel-execution flakiness (verified via
serial re-run: 3 passed, 0 failed).

**BLOCKING: 0. MUST-FIX: 0. Attributable functional regressions: 0.**

**Not self-certified.** Recommends **149O.20L.7O.3F.1 — Independent
End-to-End Rollback Permission-Boundary Verification** next, not begun.

See
`docs/PHASE_149O_20L_7O_3F_PERMISSION_BROKER_ROLLBACK_DEFAULT_PATH_CONSUMPTION_INTEGRATION.md`
for the full evidence trail.
