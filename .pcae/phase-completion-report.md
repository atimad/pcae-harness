# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1 — Fresh Independent Verification of the Privileged Helper / HPAC-PAWA-HELPER-001 Protocol Foundation

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1`
- Alias: **N16-5-F-5-TB-HELPER-IV** (operator readability only; the full canonical CPIPC id is authoritative)
- Status: **COMPLETE — NOT VERIFIED / BLOCKED**
- Predecessor: **N16-5-F-5-TB-HELPER-IMPL.1** (COMPLETE — SCOPE-FENCE RECONCILIATION), entry HEAD == `origin/main` == `7dcfcd7f`
- CPIPC: valid direct `.1` successor of the predecessor — independently re-derived via `pcae.core.phase_id` (`is_valid` True; `normalize(id) == id`; same series `149`; same branch `O`; exactly one appended `.1` segment, 57 vs 56; exact canonical text; unique against `git log --all` and `git grep` across the working tree; no conflicting active governed phase); alias display-only, no `<digit><letter>` token, no discrepancy

## Predecessor-identity correction

A separate, not-yet-authorized `N16-5-F-5-TB-REPLAY-REPAIR` authorization
prompt presupposed a predecessor `N16-5-F-5-TB-HELPER-IV` already
COMPLETE / BLOCKED. Direct repository inspection (`git log --all`,
`PROJECT_STATUS.md`'s own "NOT begun" language, absence of any
task/report/metadata artifact) proved that phase had never run at all.
Correctly derived the real predecessor as **N16-5-F-5-TB-HELPER-IMPL.1**
and ran this IV for real before any repair phase could be considered.

## Verdict

- **N16-5-F-5-TB-HELPER-IV: COMPLETE — NOT VERIFIED / BLOCKED.**
- **Blocking finding — REPLAY-AFTER-RESTART, CONFIRMED**, independently
  reproduced across two genuinely separate OS processes (`subprocess.run`,
  not two objects in one process): a fresh helper process reports a
  previously-admitted-and-consumed `(request_id, nonce)` as `FRESH`,
  because `ReplayLedger` is constructed fresh per process with no durable
  backing. Same result under response-loss and
  crash-before-terminal-disposition framings. Root cause structurally
  confirmed via `inspect.getsource` (no filesystem/network I/O anywhere in
  `ReplayLedger`/`ProtectedStoreFoundation`, no durable-location
  constructor argument).
- macOS same-file-object execution reconfirmed fail-closed on the actual
  unpatched current platform (`execute_verified` raises
  `UnsupportedPlatformProfile`), closing a gap in the existing suite's
  `monkeypatch`-only coverage of this path. Not implemented (out of
  scope).
- 7 new disposable, subprocess-isolated verification tests added, **all 7
  PASS**. Helper-foundation focused suite (unmodified) unchanged: **51
  passed / 0 failed / 1 skipped**. `fast_green`: independently re-run
  against both the candidate tree and the entry baseline (`git stash`);
  the two raw `FAILED` node-id lists diffed **byte-identical, zero
  difference** — zero attributable regressions (pre-existing
  floating-`ENTRY`-baseline noise, unrelated to this phase). Full unmarked
  `pytest -n auto` blocked by a pre-existing `pytest-xdist`
  worker-collection-mismatch defect, independently confirmed pre-existing
  via the same stash method, not attributable to this phase, not fixed
  (out of scope); single-process `--collect-only` succeeds cleanly at
  42,665 tests / 0 errors.
- Zero `src/pcae`, contract, schema, or dependency change; helper
  production files byte-unchanged. Zero live protected-host writes. Zero
  real ceremony/hardware code paths. Runtime `Observed` / `observe` /
  `unavailable`; 0 plugins / 0 capabilities; first governed runtime
  external effect **ABSENT / UNREACHABLE**.
- F-5-B2 **BLOCKED PENDING HELPER IMPLEMENTATION REPAIR**; F-5
  **CERTIFICATION BLOCKED**; **N-16-5 NOT CLOSED**; N-16-6 / N-16-7 **OPEN
  / UNTOUCHED** (N-16-7 strictly last).

Full detail: `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1_1_1_1_1_1_1_1_1_1_N16_5_F_5_TB_HELPER_IV.md`.

Recommended next (derived, NOT begun): `N16-5-F-5-TB-REPLAY-REPAIR` — implement durable, reconstructible spent-request state under the existing protected-root trust boundary to close the confirmed REPLAY-AFTER-RESTART defect. Not begun.
