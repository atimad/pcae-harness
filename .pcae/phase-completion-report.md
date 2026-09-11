# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1 — Privileged Helper Replay-Durability Repair: Cross-Process Spent-Request Preservation

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1`
- Alias: **N16-5-F-5-TB-REPLAY-REPAIR** (operator readability only; the full canonical CPIPC id is authoritative)
- Status: **COMPLETE**
- Predecessor: **N16-5-F-5-TB-HELPER-IV** (COMPLETE — NOT VERIFIED / BLOCKED), entry HEAD == `origin/main` == `319bac5d`
- CPIPC: valid direct `.1` successor of the predecessor — independently re-derived via `pcae.core.phase_id` (`is_valid` True; `normalize(id) == id`; same series `149`; same branch `O`; exactly one appended `.1` segment, 58 vs 57; exact canonical text; unique against `git log --all` and `git grep` across the working tree; no conflicting active governed phase); alias display-only, no discrepancy

## Summary

Implemented durable, cross-process, crash-surviving replay state
(`src/pcae/core/hpac_pawa_helper_replay_state.py`) closing the
REPLAY-AFTER-RESTART defect confirmed by predecessor N16-5-F-5-TB-HELPER-IV,
reusing the existing `<HPAC_PROTECTED_ROOT>/pawa-helper/` protected-root
trust boundary — no new trust root, datastore, schema,
`pawa_failure_code`, or RHAMP `terminal_reason_code`. `ReplayLedger` gained
an optional `durable_store=` backing; the in-memory default is unchanged so
the predecessor's 51-test foundation baseline stays byte-identical;
`open_durable_replay_ledger(...)` is the production entry point.

Atomic reservation publishes a fully-written, fsynced temp record via
`link()` (a bare `O_CREAT|O_EXCL` was tried first and a concurrency test
caught it publishing the record name before its content — a real bug found
and fixed); state transitions use temp + `os.replace()`; all filesystem
operations are `dir_fd`-relative through an `O_NOFOLLOW|O_DIRECTORY` chain.
Precise durability claim: atomic against concurrent helper processes and
durable across process death (verified with real `SIGKILL`); power-loss
durability explicitly not claimed.

69 new subprocess-isolated tests (`tests/test_n16_5_f_5_tb_replay_repair.py`),
all 69 passed, covering every mandatory scenario: concurrent-duplicate race,
clean restart, response loss, crash after `MUTATION_ATTEMPT_STARTED` (real
`SIGKILL`) yielding `RECONCILIATION_REQUIRED`, crash before the attempt
boundary, commit/finalize gap, conflicting replay, 13 malformed-durable-state
variants, restart-dead-authority-vs-persistent-history,
ordinary-caller-cannot-reset, per-operation/per-role semantics, retention,
and generation/installation mismatch as CONFLICTING (a real gap found and
closed during implementation).

Regression: foundation suite unmodified (51 passed / 0 failed / 1 skipped,
unchanged); combined suite 120 passed / 1 skipped, stable across 3 runs.
Governed structured `fast_green` attribution evidence (`pcae phase
fast-green-attribution`, baseline method
`parent_of_oldest_phase_attributed_commit`): 0 attributable failures.
Contract trio (HPAC-PAWA-001 v2.0 / HPAC-PAWA-HELPER-001 v1.0 / HPAC-PPA-001
v2.0) sha256-verified byte-unchanged. No schema or dependency change. macOS
same-file-object profile untouched, still FAIL-CLOSED / NOT IMPLEMENTED. 0
live protected-host writes; 0 real ceremony.

## Status

- Replay-after-restart: **REPAIRED / IV PENDING**
- Durable spent-request semantics: **IMPLEMENTED**
- Helper/protocol foundation: **REPAIRED / FRESH IV REQUIRED**
- F-5-B2: **BLOCKED PENDING FRESH HELPER IV + REMAINING MIGRATION SLICES**
- F-5: **CERTIFICATION BLOCKED**
- N-16-5: **NOT CLOSED**
- N-16-6 / N-16-7: **OPEN / UNTOUCHED** (N-16-7 strictly last)

Recommended next (derived, **NOT begun**): **N16-5-F-5-TB-HELPER-IV-R** — a
fresh helper-IV retry under a new CPIPC-valid successor identity, restarting
independent verification from the beginning.

Full detail: `docs/PHASE_N16_5_F_5_TB_REPLAY_REPAIR.md`.
