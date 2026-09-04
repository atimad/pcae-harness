# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R

## F-7 Immutable Remaining F-4-IV Evidence Guard Repair

## Verdict

**BLOCKED. F-7: REPAIRED / FRESH IV PENDING. TESTS 44/46/56: REPAIRED.
F-8: OPEN / BLOCKING. F-5 RETRY: NOT READY. F-5: OPEN / ABSENT / UNCHANGED.
N-16-5: NOT CLOSED.**

CPIPC-001 accepts the exact requested repair identifier. The only predecessor
test changes are the three authorized F-4-IV nodes.

## Immutable reconstruction

- `P = 8dcca97bb1a88a99cac3afe610f3651adcc58295` — finalized F-6 repair.
- `V = R0 = 7ef7ae0e9b0632ef0bd3c352e4598c03a9b05c69` — finalized BLOCKED F-6 IV
  and this repair's entry.
- `V4 = 90510428422e451382549ce76111610752aaafb4` — independently re-derived
  F-4-IV entry.
- `U4 = 7124c019bf3f46eb07456b81146484609197dbc2` — independently re-derived
  finalized F-4-IV endpoint.

Each node’s name and original phase task/report independently establish its
historical scope:

- Test 44 asks whether the completed IV installed a helper, changed production
  implementation/scripts, or wrote certification state.
- Test 46 asks whether the completed IV minted YubiKey/certification evidence.
- Test 56 asks whether the completed IV changed product, contract, or dependency
  bytes.

For each invariant, the lower bound is the F-4-IV entry and the upper bound is
the finalized F-4-IV head. The interval is exactly four first-parent commits
and ten lifecycle/verification files. Its path-limited production, script,
certification, dependency, and contract evidence sets are empty.

## Narrow repair and strength

Only the missing immutable upper bound was added:

- test 44: `git diff --name-only V F4_IV_FINALIZED`;
- test 46: `git diff --name-only V F4_IV_FINALIZED -- .pcae/certification`;
- test 56: `git diff --name-only V F4_IV_FINALIZED -- src/pcae scripts
  pyproject.toml docs/contracts`.

The names, path scopes, predicates, and assertions are unchanged. Disposable
Git topologies prove harmless later production/script/certification/contract
files are excluded by the immutable endpoint while equivalent forbidden files
inside the historical interval are still detected. No HEAD/live metadata,
successor allowlist, phase filter, wildcard, glob, `fnmatch`, skip, xfail,
removal, rename, or vacuous assertion was introduced.

## F-8 prerequisite finding

The mandatory F-6-IV regression suite is not future-repair resilient. Its
`test_36_sibling_1_is_historical_moving_authority`,
`test_38_sibling_2_is_historical_moving_authority`, and
`test_40_sibling_3_is_historical_moving_authority`, and
`test_44_no_additional_defect_is_silently_repaired` inspect today's live F-4-IV
owner file or the moving `V..HEAD` owner diff and require the pre-F-7 state to
remain current. After the authorized repair, all four fail.

Those assertions describe the completed F-6 IV's historical reconstruction of
the pre-F-7 state. Their authority must be the immutable F-7 entry blob, not
today's repaired file. This is F-8, a separate historical-moving-authority
defect outside the authorized nodes. It is classified and not repaired here.
Therefore F-5 RETRY remains NOT READY.

## Verification

- Fresh F-7 repair suite: **79 passed, 0 failed**.
- Complete F-4-IV suite: **56 passed, 0 failed**.
- F-6-IV regression: **61 passed, 4 failed** at tests 36/38/40/44, all the same
  disclosed F-8 class. No F-7-attributable product failure exists.
- Production, scripts, dependencies, and normative contracts are byte-identical
  to `R0`.
- F-5 protected root remains absent; no host mutation occurred.
- Additional deterministic F-6/F-4/F-3/H-2/F-2 group: **284 passed, 0 failed,
  1 preserved obsolete F-3 demonstration deselected**.
- Gate 5/Gate 9/verifier/PAWA/PPA/RHAMP/FIDO2/presentation group: **882 passed,
  0 failed**. Total clean evidence: **1,301 passed**.

No administrator interaction, protected human election, or YubiKey interaction
occurred. No helper installation, PAWA deployment capability, presentation
evidence, production principal, or Gate certification was created.

F-3, F-4, and F-6 remain independently verified repaired. H-1/H-2/F-2 bytes
and evidence are preserved. Runtime remains
`not_implemented / Observed / observe / unavailable`, zero plugins/capabilities,
first effect absent, and N-16-6/N-16-7 untouched.

FIDO2 and local protected presentation remain supported-not-exclusive.
Mechanism-neutral mobile-only authentication and protected approval remain
open/planned.

## Successor sequence

Next, not begun:

1. `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R` — F-8
   Immutable F-6-IV Sibling-Adjudication Evidence Guard Repair, limited to the
   four newly identified F-6-IV nodes.
2. Fresh independent verification of F-8 and F-7.
3. Only if that IV says READY: a separately derived F-5 deployment retry.
4. Separate deployment-state IV.
5. `.30R.5R.2.1R.1R.3` final real protected-presentation + YubiKey N-16-5
   certification and closure.

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.**
