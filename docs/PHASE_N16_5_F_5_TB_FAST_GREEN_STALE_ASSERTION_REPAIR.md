# Phase N16-5-F-5-TB-FAST-GREEN-STALE-ASSERTION-REPAIR

## Phase ID

`150B` (alias **N16-5-F-5-TB-FAST-GREEN-STALE-ASSERTION-REPAIR**), a fresh short top-level CPIPC number (`pcae.core.phase_id` `is_valid` True, no collision against `git log --all`), used in place of a mechanical `.1` successor of the immediately preceding dot-chain lineage (`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2....1.1`).

**Why not `.1`:** live-tested this phase's own canonical-report write against a `.1`-extended candidate of that lineage and it failed with `OSError: [Errno 63] File name too long` inside `write_phase_report`'s timestamped-artifact path (`.pcae/phase-reports/{ts}-{safe_id}.md`) — the exact unpatched OS filename-length limit that blocks 150A, this phase's own successor recommendation. Switching to `150B` (sibling to 150A's own established short-top-level-number precedent) resolved it with zero source changes, matching this phase's forbidden-scope constraint (`src/pcae/core/filename_safety.py`/`phase_reports.py`/`tasks.py` are 150A's exclusive scope, untouched here).

## Topology / worktree proof

Rooted at `origin/main` == `c4c9f554106965e10a057db96a106f85f72f8f65` in an isolated worktree/branch (`n16-5-f-5-tb-fast-green-stale-assertion-repair`), **not** built on local `main` (which sits 2 commits ahead of `origin/main`, carrying the held source-conformance IV commits). Verified absent from this branch's ancestry before any mutation and again before push:

- held IV: `6c7f5cf4`, `2b8ad2aa` — absent
- blocked 150A: `72cdba16`, `d0b2a75a` — absent

Neither is modified, cherry-picked, rebased, merged, or published by this phase.

## Defect

Two assertions in `tests/test_n16_5_f_5_tb_fast_green_baseline_freeze_evidence_repair.py` bound a historical, phase-local claim to `HEAD`/live disk instead of to the originating phase's own fixed terminal boundary:

1. `test_no_production_source_changed_in_this_phase` computed `git diff --name-only <this-phase-entry> HEAD -- src/pcae` and required it empty forever. Confirmed with real repo evidence: the blocked 150A attempt (`72cdba16`, on an isolated unmerged local branch) legitimately touches `src/pcae/core/filename_safety.py`, `phase_reports.py`, and `tasks.py` — none of which this phase touches. Were 150A (or any other legitimate future `src/pcae/**` edit) ever merged past this phase's entry commit, this assertion would break by construction, despite this phase's own historical claim ("I touched zero `src/pcae/**` files") remaining true.
2. `test_stale_assumption_fails_against_modern_head_for_a_legitimate_reason` hashed **live disk bytes** against `docs/evidence/helper-installation-identity/baseline.json` and asserted the differing paths were a subset of exactly the three files touched by the immediate predecessor's source-conformance repair. Any later legitimate edit to a different `src/pcae/**` file (again, e.g. 150A's three files) would add unexpected paths to `now_differs`, breaking the subset assertion — even though the assertion's real target (the source-conformance repair's own three-file scope) never changed.

Both were verified live: `git diff --name-only c4c9f554 recovery/pcae-lifecycle-filename-length-hardening -- src/pcae` returns exactly `filename_safety.py`, `phase_reports.py`, `tasks.py` — none overlapping the three protected helper-conformance files, confirming these two assertions are the disease this phase's authorization describes, not a hypothetical.

## Historical reconstruction

- This repaired phase's own entry commit: `4ddd5dd460355c39e842cf25e92532933b3343e9` (`Close housekeeping push task...`, immediately after the source-conformance-repair phase closed).
- Its own implementation commit: `3dbd28082e407f65686cd8d754252f46c89a073f` (`repair stale historical full-tree src/pcae hash-freeze test`) — touches only `PROJECT_STATUS.md`, a new evidence doc, and two test files; zero `src/pcae/**`.
- Its own final (task-close) commit: `c4c9f554106965e10a057db96a106f85f72f8f65` (`Close N16-5-F-5-TB-FAST-GREEN-BASELINE-FREEZE-EVIDENCE-REPAIR task...`).
- `git diff --name-only 4ddd5dd4 c4c9f554 -- src/pcae` is empty — independently confirms the phase's real historical claim ("this test/evidence-only phase changed zero `src/pcae/**` paths") at its own boundary.
- The three helper-conformance files are byte-identical between `4ddd5dd4` and current disk (verified via `git diff --quiet`), confirming they have not moved since; the historical "legitimate divergence from `baseline.json`" fact is therefore correctly, permanently readable at that fixed commit rather than at live disk.

Neither assertion encodes a permanent global invariant; both describe a specific historical phase's own bounded claim. Repairing them does not weaken unauthorized-drift detection — see Mutation sensitivity below.

## Repair (Model FG-E, consistent with the predecessor's own selected model)

- Added `_THIS_PHASE_FINAL_COMMIT = 'c4c9f554106965e10a057db96a106f85f72f8f65'`.
- `test_no_production_source_changed_in_this_phase`: diff endpoint changed from `'HEAD'` to `_THIS_PHASE_FINAL_COMMIT`; added an ancestor-of-HEAD sanity assertion for that pinned commit.
- `test_stale_assumption_fails_against_modern_head_for_a_legitimate_reason`: replaced `(ROOT / path).read_bytes()` (live disk) with `git show <_THIS_PHASE_ENTRY_COMMIT>:<path>` (pinned historical blob) when computing `now_differs`.

No test was skipped, xfail'd, deleted, or broadened with today's file list. No production source or contract file was touched.

## Mutation sensitivity

Fresh suite `tests/test_n16_5_f_5_tb_fast_green_stale_assertion_repair.py` (10 tests, all passing) proves:

- Held/blocked commits absent from this branch's ancestry.
- Zero `src/pcae/**`/`docs/contracts/**` changes in this phase's own diff.
- The repaired target-file boundary commits are pinned and reachable.
- Neither repaired assertion still contains an `entry, 'HEAD'`-shaped diff call or a live-disk-vs-pinned-hash comparison; legitimate current-state checks elsewhere in the file (ancestor-of-HEAD, `head != _HISTORICAL_FINAL_COMMIT`) are preserved, not collateral damage.
- The full repaired target module (13 tests) passes as a subprocess-isolated check.
- A synthetic scratch-repo proof that the "no production source changed" pinned-boundary mechanism still flags an unauthorized in-scope mutation and is immune to a later out-of-scope edit (whereas the old entry→HEAD pattern would have been broken by that same later edit — asserted directly).
- A synthetic scratch-repo proof that the pinned-boundary allowlist mechanism still flags an unexpected file inside the protected historical range, and remains immune to unrelated later HEAD movement.
- A real, non-synthetic proof using the actual blocked 150A commit (`72cdba16`, read diagnostically only — never merged, cherry-picked, or otherwise touched) confirming it legitimately touches exactly three `src/pcae/**` files outside the helper-conformance allowlist: the concrete shape that would have broken the old assertions.

## Sibling disease inventory (bounded; not auto-repaired)

Scanned `tests/test_n16_5_f_5_tb_fast_green_baseline_freeze_evidence_repair.py`, `test_n16_5_f5_tb_prov_repair_iv.py`, `test_n16_5_f5_tb_prov_repair_contract.py`, `test_n16_5_f_5_tb_provisioning_source_conformance_repair.py`, `test_n16_5_f_5_tb_helper_installation_identity_contract_repair.py`:

- **Confirmed same defect (repaired):** the two named assertions above.
- **Suspicious sibling, not repaired (same file):** `test_helper_source_conformance_repair_remains_byte_identical` and `test_current_contracts_remain_byte_identical` also compare `_THIS_PHASE_ENTRY_COMMIT` against **live disk** rather than a pinned final commit. Narrower blast radius than the two repaired assertions (bounded to 3 helper files + 3 contract files, which are pinned/protected and not touched by any currently known future work, including 150A), so they do not currently fail and were left out of this phase's narrow scope per its own authorization (§12/§18: no automatic scope broadening). Flagged for a future dedicated phase if any future work is ever authorized to touch those specific files.
- **Safe/current-state (not a defect):** `test_22_production_diff_confined_to_expected_three_files` / `test_23`/`test_24` in `test_n16_5_f_5_tb_provisioning_source_conformance_repair.py` use `git diff --name-only HEAD` (working-tree-vs-HEAD, i.e. uncommitted changes at that phase's own authoring time), not a historical-commit-vs-modern-HEAD freeze — different semantic category, out of scope.
- No other occurrence of an `<entry-commit>, 'HEAD'`-shaped diff call or live-disk-vs-pinned-baseline-hash comparison was found in the scanned files.

## Files changed

- `tests/test_n16_5_f_5_tb_fast_green_baseline_freeze_evidence_repair.py` (repair)
- `tests/test_n16_5_f_5_tb_fast_green_stale_assertion_repair.py` (new, 10 tests)
- `docs/PHASE_N16_5_F_5_TB_FAST_GREEN_STALE_ASSERTION_REPAIR.md` (this file)
- `PROJECT_STATUS.md`
- `tasks/**` (task lifecycle)

`src/pcae/**`: 0 files changed. `docs/contracts/**`: 0 files changed.

## Regressions

`tests/test_n16_5_f_5_tb_helper_installation_identity_contract_repair.py` + `test_n16_5_f5_tb_prov_repair_iv.py` + `test_n16_5_f5_tb_prov_repair_contract.py` + `test_n16_5_f_5_tb_provisioning_source_conformance_repair.py`: 4 failed / 115 passed / 1 skipped, identical failure set on a `git stash`-isolated pre-edit baseline (`test_current_contract_versions_and_gap_free_unique_requirements[HPAC-PAWA-HELPER-001]`, `[HPAC-PAWA-001]`, `test_LOAD_BEARING_source_still_implements_removed_vocabulary`, `test_LOAD_BEARING_store_adapter_still_dispatches_configure_privileged_helper_through_h`) — all pre-existing historical `LOAD_BEARING`/version-gap pin failures unrelated to this diff. Zero new failures, zero regressions.

## Runtime / posture

Runtime: Observed / observe / unavailable (unchanged). N-16-5 remains **NOT CLOSED**. N-16-6/N-16-7 untouched.

## Disposition

**COMPLETE — STALE FAST GREEN HISTORICAL ASSERTIONS REPAIRED / TRUST GATE CLEAN.**

Recommended next (not begun by this phase): re-attempt `PCAE-LIFECYCLE-FILENAME-LENGTH-HARDENING` (150A) from updated `origin/main`.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved as historical governance evidence from a predecessor phase; not retroactively authorized, amended, erased, or normalized by this phase.
