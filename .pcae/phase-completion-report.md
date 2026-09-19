# Phase 150B Complete — Stale Fast Green Historical Assertions Repaired / Trust Gate Clean

Canonical Phase ID: `150B`

Alias: **N16-5-F-5-TB-FAST-GREEN-STALE-ASSERTION-REPAIR**

Status: **COMPLETE — STALE FAST GREEN HISTORICAL ASSERTIONS REPAIRED / TRUST GATE CLEAN.** Test/evidence/governance repair phase only; no production source change; no contract change.

CPIPC: a fresh short top-level phase number (`pcae.core.phase_id` `is_valid` True, no collision against `git log --all`), used instead of a mechanical `.1` successor of the immediately preceding dot-chain lineage (`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2....1.1`). That lineage's numeric ID is already long enough that any canonical phase-report write for a `.1` child of it trips the same unpatched OS filename-length limit that blocks 150A itself (independently confirmed live: `write_phase_report`'s own timestamped-artifact path failed with `OSError: [Errno 63] File name too long` for the `.1`-extended ID before this phase switched to `150B`). `150A` already established the precedent of a short top-level number for exactly this reason; `150B` is its sibling.

Predecessor: N16-5-F-5-TB-FAST-GREEN-BASELINE-FREEZE-EVIDENCE-REPAIR — **COMPLETE — FAST GREEN BASELINE-FREEZE EVIDENCE REPAIRED / TRUST GATE CLEAN.**

## What this phase did

Diagnosed and repaired two current-`HEAD`-bound stale assertions in `tests/test_n16_5_f_5_tb_fast_green_baseline_freeze_evidence_repair.py`, itself the immediately preceding phase's own deliverable:

1. `test_no_production_source_changed_in_this_phase` compared that phase's own entry commit (`4ddd5dd4`) to live `HEAD` instead of its own final/task-close commit (`c4c9f554`), so it would break by construction the moment any later legitimate phase touched a different `src/pcae/**` file.
2. `test_stale_assumption_fails_against_modern_head_for_a_legitimate_reason` hashed **live disk bytes** against a pinned historical baseline (`baseline.json`) instead of a pinned historical commit, with the identical staleness failure mode.

Confirmed the defect live, not hypothetically: `git diff --name-only c4c9f554 <blocked-150A-commit> -- src/pcae` returns exactly `filename_safety.py`, `phase_reports.py`, `tasks.py` — none overlapping the three protected helper-conformance files — the concrete shape that would have broken both old assertions.

Repaired both to **Model FG-E** (pinned historical-boundary commits), the identical pattern the predecessor phase itself already used and documented for the earlier stale test: added `_THIS_PHASE_FINAL_COMMIT = 'c4c9f554...'` and rebound assertion (1) to `diff(entry, final)` instead of `diff(entry, HEAD)`; rebound assertion (2) to read bytes via `git show <entry>:<path>` instead of live disk. No test was skipped, xfail'd, deleted, or broadened with today's file list.

Added a fresh 10-test suite (`tests/test_n16_5_f_5_tb_fast_green_stale_assertion_repair.py`, all passing) covering: held/blocked-commit ancestry absence from this branch, zero production/contract delta, pinned-boundary reachability, absence of the old `entry, 'HEAD'`-shaped pattern (with legitimate current-state checks elsewhere in the file confirmed preserved), the full repaired target module passing standalone, two synthetic scratch-repo mutation-sensitivity proofs (unauthorized in-scope drift still detected; unrelated later out-of-scope edits no longer perturb the pinned check), and one real (non-synthetic) proof using the actual blocked 150A commit's own `src/pcae/**` diff.

Bounded sibling-disease scan of related Fast Green/baseline-freeze/provisioning-repair test files found two suspicious-but-narrower siblings in the same file (`test_helper_source_conformance_repair_remains_byte_identical`, `test_current_contracts_remain_byte_identical`) — same entry-vs-live-disk shape, but bounded to 3 pinned helper files + 3 pinned contracts, none touched by any currently known future work including the blocked filename-length hardening attempt, so not currently failing. Left unrepaired per this phase's own narrow-scope authorization; flagged for a future phase if that scope ever changes. No other same-class defect found.

Files changed: `tests/test_n16_5_f_5_tb_fast_green_baseline_freeze_evidence_repair.py` (2 of 13 assertions repaired), `tests/test_n16_5_f_5_tb_fast_green_stale_assertion_repair.py` (new, 10 tests), `docs/PHASE_N16_5_F_5_TB_FAST_GREEN_STALE_ASSERTION_REPAIR.md` (new, full evidence), `PROJECT_STATUS.md`, plus task-lifecycle bookkeeping. Zero `src/pcae/**` changes; zero `docs/contracts/**` changes.

Governed Fast Green attribution (`pcae phase fast-green-attribution`, method `baseline_vs_candidate_isolated_worktree`): baseline `c4c9f554106965e10a057db96a106f85f72f8f65` (origin/main), candidate `c2b73f428e81d09a4152ca83c5e6f3ed56c0d708` (this phase's own checkpoint commit). One candidate-only failure surfaced, `tests/test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record` — independently confirmed as a long-known-flaky, order/filesystem-state-dependent node: it appears as attributable in roughly half of all historical attribution runs across unrelated commit pairs recorded in this repository's own `.pcae/fast-green-attribution/` history, including on the identical baseline/candidate pair (`4ddd5dd4` → `3dbd2808`) recorded by the immediately preceding phase's own canonical evidence file. Adjudicated via the tool's own `--rerun-node` isolated-rerun mechanism (not a manual override or silent re-run-until-green). Final run: **`attributable_failures: []`.**

Machine artifact: `.pcae/fast-green-attribution/524463f1e0294f36a2260d39bdaf3ddbcbb64419c2a1bdd0e4f2d5058bdcbe7c.json`.

Regression suites: `test_n16_5_f_5_tb_helper_installation_identity_contract_repair.py` + `test_n16_5_f5_tb_prov_repair_iv.py` + `test_n16_5_f5_tb_prov_repair_contract.py` + `test_n16_5_f_5_tb_provisioning_source_conformance_repair.py`: 4 failed / 115 passed / 1 skipped, identical failure set on a `git stash`-isolated pre-edit baseline — zero new failures, zero regressions. `pcae check` passed.

## Disposition

**COMPLETE — STALE FAST GREEN HISTORICAL ASSERTIONS REPAIRED / TRUST GATE CLEAN.** Not claimed: N-16-5 closure, independent verification of the source-conformance repair, or completion of the filename-length hardening successor. No contract change, no foundation repair, no helper-admission implementation, no production source change, no live host mutation. N-16-5 remains **NOT CLOSED**; N-16-6/N-16-7 untouched; runtime remains Observed / observe / unavailable.

Recommended next (not begun): re-attempt `PCAE-LIFECYCLE-FILENAME-LENGTH-HARDENING` (150A) from updated `origin/main`, now unblocked against a clean Fast Green trust gate.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved as historical governance evidence from a predecessor phase; not retroactively authorized, amended, erased, or normalized by this phase.
