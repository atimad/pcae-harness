# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1

## Independent Verification of the F-7 and F-8 Immutable Historical Evidence Guard Repairs + Final N-16-5 Prerequisite Moving-History Clearance

## Verdict

**BLOCKED. F-7: INDEPENDENTLY VERIFIED REPAIRED. F-8: INDEPENDENTLY VERIFIED
REPAIRED. ONE NEW HISTORICAL-MOVING-AUTHORITY DEFECT: CONFIRMED / REPAIR
REQUIRED (IN THE F-7 REPAIR SUITE ITSELF). F-5 RETRY: NOT READY. F-5: OPEN /
ABSENT / UNCHANGED. N-16-5: NOT CLOSED.**

CPIPC-001 accepts the exact requested identifier as the successor of
`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R`. This verification
changes no predecessor test, production source, production script,
dependency, normative contract, or protected host state.

## Lineage correction (discrepancy record)

- `P = U6 = 7ef7ae0e9b0632ef0bd3c352e4598c03a9b05c69` — finalized F-6 IV
  BLOCKED head. Confirmed correct.
- `R7 = 8b18babdad71be850095aca979106925769d6721` ("repair F-7 and disclose
  F-8 blocker") — the actual finalized F-7 repair head. The prior report's
  `R7 = R0 = 6de3d6971536b8bca6bd585d47cccc0f8fec5b0a` is **incorrect**: that
  commit is the stage-blocked-completion-metadata commit, two commits after
  the real F-7 repair. Corrected here; no historical report is rewritten.
- `R8 = 8c93fd25f70d013e08721089a0b1a7b0c4a8e969` ("repair F-8 immutable
  F-6-IV evidence guards"). Confirmed correct.
- `V = 29ba3458...` (current IV phase-entry SHA, this repository's `HEAD` at
  phase entry). Confirmed correct.

## Independent F-7 reconstruction

- `F4_IV_FINALIZED = 7124c019bf3f46eb07456b81146484609197dbc2` — finalized
  F-4-IV endpoint, independently confirmed via `.pcae/phase-completion-metadata.json`
  at that commit (`status: completed`).
- Pre-repair, `F-4-IV test_44`, `test_46`, and `test_56` called
  `git("diff", "--name-only", V)` with no upper bound — diffing a fixed
  historical commit against the live working tree, a moving target.
- Repaired to `git("diff", "--name-only", V, F4_IV_FINALIZED)`, a fixed
  two-commit historical range. No live-HEAD/origin-main/live-metadata
  dependency remains. Historical, current, and future-successor cases pass;
  forbidden in-range evidence remains detectable. No skip/xfail/wildcard/
  fnmatch/deletion/rename. Test count (56) matches the pre-repair count.

Accordingly F-7 is **INDEPENDENTLY VERIFIED REPAIRED**:
`F-4-IV test_44`: VERIFIED. `test_46`: VERIFIED. `test_56`: VERIFIED.

## Independent F-8 reconstruction

- `F6_IV_FINALIZED = 8dcca97bb1a88a99cac3afe610f3651adcc58295` — finalized
  F-6-IV endpoint (also `V6` in the F-8 report), confirmed.
- Pre-repair, `F-6-IV test_36/38/40/44` read `OWNER.read_text()` — the live
  working-tree copy of the sibling F-4-IV owner file — as historical
  evidence. Once F-7 repaired that file, these sibling-adjudication tests
  would have silently begun reading the *new, fixed* content instead of the
  original defective content they exist to attest to: a moving-successor
  dependency masquerading as historical evidence.
- Repaired to `show(F6_IV_FINALIZED, OWNER_REL)`, pinning to the immutable
  historical blob at the F-6-IV finalized commit. Historical, current, and
  future-successor cases pass; forbidden in-range evidence remains
  detectable. No skip/xfail/wildcard/fnmatch/deletion/rename. Test count (65)
  matches the pre-repair count. `F-6-IV test_44` is confirmed distinct from
  `F-4-IV test_44` throughout.

Accordingly F-8 is **INDEPENDENTLY VERIFIED REPAIRED**:
`F-6-IV test_36`: VERIFIED. `test_38`: VERIFIED. `test_40`: VERIFIED.
`test_44`: VERIFIED.

## Final bounded moving-history prerequisite scan

The bounded current N-16-5 prerequisite chain (F-3/F-4/F-6/F-7/F-8 repair
and IV suites, plus Gate 5/Gate 9/hpac_verifier/PAWA/RHAMP/CTAP2/
protected-presentation groups) was scanned for the unbounded
`git("diff", "--name-only", <fixed>)` pattern (no upper bound → live
worktree as moving authority) and equivalent live-metadata/HEAD-as-historical-
authority idioms.

| File | Nodes | Classification |
|---|---|---|
| `test_..._30r_5r_2_1r_1r_f4_immutable_scope_repair.py` (the F-7 repair suite) | `test_31_no_protected_root_mutation_in_repo_diff`, `test_32_no_helper_installation_artifact_added`, `test_43_f4_change_is_test_only` | **HISTORICAL-MOVING-AUTHORITY DEFECT.** Each calls `git("diff", "--name-only", R0)` with `R0` fixed but no upper bound, i.e. against the live working tree. Framed as permanent historical-repair-verification assertions, not named or scoped as current-state checks — the same defect shape just repaired in F-7/F-8 itself. Currently passing (3/3) only because no successor has yet touched a path these tests inspect; unstable and unbounded going forward. |
| `test_..._30r_5r_2_1_protected_presentation_human_election_iv...py` `test_31_current_phase_changes_no_production_or_contract` | 1 node | SAFE CURRENT-STATE CHECK — name and design explicitly assert a current-phase-in-progress property, not a completed historical fact. |
| All other `git("diff"/"show", <fixed>, ...)` matches across `f7_..._repair.py`, `f8_..._repair.py`, `f6_..._iv.py`, `f6_..._repair.py` | — | SAFE — each reconstructs *what the pre-repair code used to say* via a fixed two-commit range or a `show` at a fixed historical SHA; none uses live worktree/HEAD as historical authority. |

No new defect was repaired. Per the phase's VALID BLOCKED CONDITIONS, a
newly identified historical-moving-authority defect that would block the
next F-5 retry mandates BLOCK.

**Conclusion: NOT CLEAN.** One additional blocking historical-moving-
authority defect found in the current N-16-5 prerequisite chain (F-7 repair
suite tests 31/32/43).

## Verification and boundaries

- F-7 repair suite + F-8 repair suite + full F-4-IV suite + full F-6-IV
  suite (combined): **296 passed, 0 failed**.
- Broad non-regression sweep (F-3 repair, PAWA, RHAMP mechanism+IV, CTAP2
  repair+IV, protected-presentation real-assurance+IV, Gate 5 ×2, Gate 9 ×4,
  hpac_verifier ×4, election-repair+IV): **1003 passed, 3 failed**. The 3
  failures (2 in `test_hpac_verifier_independent_verification...` —
  `object.__new__` forgery detection; 1 in the election-IV file's
  `test_30_repair_suite_contains_a_stale_live_head_assertion_finding_f3`)
  are pre-existing and unrelated to F-7/F-8: independently reproduced by
  checking out those two files at `P` (pre-F-7/F-8) in isolation; working
  tree restored, `git status` clean afterward.
- No-test-weakening scanner: 0 skip/skipif/pytest.skip/xfail/fnmatch/glob
  calls in either owner file (all matches are self-checking assertion
  strings); 0 test deletions; 0 renames.
- Fixed-SHA attribution: `git diff --name-only P..HEAD -- src/pcae scripts`
  empty; `-- docs/contracts` empty; `-- pyproject.toml` empty. No production,
  script, contract, or dependency change anywhere in the lineage.
- F-5 read-only inspection: `/Library/Application Support/PCAE/HPAC/protected-root`
  and its parent directory do not exist. F-5 confirmed **OPEN / ABSENT /
  UNCHANGED**.
- No new IV test/artifact files were created; the existing owner and repair
  suite files, read via `git show`/`git diff` at fixed historical SHAs plus
  live-file AST inspection, were sufficient to independently reconstruct and
  validate all seven nodes without new synthetic scaffolding.

F-3, F-4, and F-6 remain independently verified. H-1/H-2/F-2 production
bytes and prior evidence remain unchanged. No helper, descriptor, current
generation, PAWA deployment capability, administrator interaction,
protected election, YubiKey interaction, presentation evidence, principal,
or Gate certification was created.

Runtime remains `not_implemented / Observed / observe / unavailable`, with
zero plugins/capabilities and first effect absent. N-16-6/N-16-7 remain
untouched. FIDO2 and local presentation remain supported-not-exclusive;
mechanism-neutral mobile-only authentication and protected approval remain
open/planned.

## Successor decision

F-5 RETRY is **NOT READY**. Recommended next, not begun:

1. A narrow repair phase scoped exactly to `test_31_no_protected_root_mutation_in_repo_diff`,
   `test_32_no_helper_installation_artifact_added`, and
   `test_43_f4_change_is_test_only` in
   `test_..._30r_5r_2_1r_1r_f4_immutable_scope_repair.py`, applying the same
   fixed-upper-bound pattern (`git diff --name-only <fixed>, <fixed-upper>`)
   already used to repair F-7 and F-8.
2. A fresh, bounded independent verification of that repair, and a repeat of
   the final bounded prerequisite-chain moving-history scan.
3. Only then, a freshly derived, separately authorized F-5
   deployment-preparation retry.
4. Separate deployment-state IV.
5. Final real protected-presentation human election + presentation-bound
   N-16-5 certification and closure.

None is begun. N-16-5 remains NOT CLOSED.

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.**
