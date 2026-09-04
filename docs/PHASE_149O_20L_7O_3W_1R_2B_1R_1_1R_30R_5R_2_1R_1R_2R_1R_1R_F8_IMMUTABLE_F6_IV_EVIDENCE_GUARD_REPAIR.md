# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R

## F-8 Immutable F-6-IV Sibling-Adjudication Evidence Guard Repair

## Verdict

**COMPLETE. F-8: REPAIRED / FRESH IV PENDING. F-6-IV TESTS 36/38/40/44:
REPAIRED. F-7: REPAIRED / FRESH IV PENDING. F-5 RETRY: PENDING FRESH
F-7/F-8 IV. F-5: OPEN / ABSENT / UNCHANGED. N-16-5: NOT CLOSED.**

CPIPC-001 accepts the exact requested repair identifier. The only predecessor
test changes are the four authorized F-6-IV nodes.

## Immutable reconstruction

- `P = 7ef7ae0e9b0632ef0bd3c352e4598c03a9b05c69` — finalized BLOCKED F-6 IV.
- `R7 = R0 = 6de3d6971536b8bca6bd585d47cccc0f8fec5b0a` — finalized BLOCKED F-7
  repair and this F-8 phase entry.
- `V6 = 8dcca97bb1a88a99cac3afe610f3651adcc58295` — finalized F-6 repair and
  exact F-6-IV entry.
- `U6 = 7ef7ae0e9b0632ef0bd3c352e4598c03a9b05c69` — finalized F-6-IV endpoint.

The first F-6-IV implementation commit has parent `V6`. The exact first-parent
interval `V6..U6` contains four commits (`be4575a2`, `edf3bd08`, `cb0e5e9b`,
`7ef7ae0e`) and ten verification/lifecycle files. Immutable completion metadata
at `U6` identifies the phase and its BLOCKED verdict; the immediate successor
belongs to F-7.

Tests 36, 38, and 40 record the completed F-6 IV's adjudication of the three
then-unrepaired F-4-IV sibling guards. Their historical authority is therefore
the F-4-IV owner blob at `U6`, not today's post-F-7 owner file. Test 44 records
that F-6 IV itself did not silently repair the owner or F-6 repair suite; its
authority is the fixed path-limited interval `V6..U6`, not `V6..HEAD`.

## Narrow repair and strength

- F-6-IV test 36 reads the owner blob with `git show U6:<owner>` and retains
  the exact moving-form and historical-name assertions.
- F-6-IV test 38 reads the same immutable blob and retains its exact
  certification-path moving-form assertion.
- F-6-IV test 40 reads the same immutable blob and retains its exact product /
  contract moving-form and historical-name assertions.
- F-6-IV test 44 changes only the upper bound of its existing path-limited Git
  diff from implicit live HEAD to `U6`.

Historical evaluation passes. Current successor evaluation passes even though
F-7 legitimately changed the live owner file. Disposable Git topologies show
that later owner changes cannot alter a fixed historical blob/range, while a
forbidden owner/repair change inside the historical interval is still detected.
No HEAD/origin-main/live metadata authority, successor exception, phase
allowlist, wildcard, glob, `fnmatch`, skip, xfail, removal, rename, or vacuous
assertion was introduced.

## Final bounded prerequisite scan

The bounded prerequisite scan covered 28 `.30R*` suites, 1,326 test
definitions, and 118 textual HEAD/origin-main references after adding this
fresh suite. The remaining executable uses are **SAFE CURRENT-STATE CHECKS**
when they intentionally protect rolling contract/product/runtime invariants,
descendant/topology checks when current HEAD is the subject, historical
reproduction strings, or already-fixed immutable endpoint checks. No additional
historical-moving-authority blocker was found. No additional node was repaired.

**NO ADDITIONAL BLOCKING HISTORICAL-MOVING-AUTHORITY DEFECT FOUND IN CURRENT
N-16-5 PREREQUISITE CHAIN.**

## Verification and boundaries

- Complete F-6-IV suite: **65 passed, 0 failed**.
- F-7 repair suite: **79 passed, 0 failed**.
- Complete F-4-IV suite: **56 passed, 0 failed**.
- Fresh F-8 repair suite: **96 passed, 0 failed**.
- F-8/F-7/F-6/F-4/F-3 history group: **496 passed, 0 failed**.
- H-2/F-2 software group: **155 passed, 0 failed**, with one preserved obsolete
  F-3 demonstration deselected.
- Broad deterministic Gate 5/Gate 9/verifier/PAWA/PPA/RHAMP/FIDO2/presentation
  group: **823 passed, 0 failed**.
- Whole `.30R` history-sensitive sweep: **1,510 passed, 5 pre-existing
  historical/obsolete failures**. Those failures are in superseded `.30R.3.3R`,
  `.30R.5`, and `.30R.5R.2.1` guards; all reproduce independently of this
  repair and none is in the current F-5 prerequisite baseline.
- No-test-weakening: four retained nodes changed only their immutable evidence
  source/bound; zero test removal, rename, skip, skipif, `pytest.skip`, xfail,
  wildcard, glob, or `fnmatch` broadening.
- Fixed-SHA attribution: test-only verification logic and fresh lifecycle
  artifacts; `src/pcae`, `scripts`, `pyproject.toml`, and `docs/contracts` are
  unchanged from `R0`.

F-3, F-4, and F-6 remain independently verified repaired. F-7 remains repaired
with fresh IV pending. H-1/H-2/F-2 production bytes and prior evidence are
preserved.

The production protected root remains absent. No helper installation occurred.
No PAWA deployment capability was issued or consumed. No administrator interaction
occurred. No human election or YubiKey interaction occurred. No presentation evidence
was created. No PRODUCTION principal or Gate certification was created.

Runtime remains `not_implemented / Observed / observe / unavailable`, with zero
plugins/capabilities; the first external effect remains absent and
N-16-6/N-16-7 remain untouched. FIDO2 and local presentation remain supported-not-exclusive;
mobile-only authentication and protected approval remain open/planned.

## Successor sequence

F-5 RETRY is **PENDING FRESH F-7/F-8 IV**. Recommended next, not begun:

1. `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1` —
   Independent Verification of the F-7 and F-8 Immutable Historical Evidence
   Guard Repairs + Final N-16-5 Prerequisite Moving-History Clearance.
2. Only if that IV says READY: a separately authorized F-5 deployment retry.
3. Separate deployment-state IV.
4. Final real protected-presentation human election + genuine YubiKey,
   presentation-bound N-16-5 certification and closure.

None is begun. N-16-5 remains NOT CLOSED.

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.**
