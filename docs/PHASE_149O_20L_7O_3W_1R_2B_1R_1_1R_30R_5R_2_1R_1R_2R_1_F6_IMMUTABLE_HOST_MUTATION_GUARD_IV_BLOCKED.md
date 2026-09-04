# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1

## Independent Verification of the F-6 Immutable F-4-IV Host-Mutation Evidence Guard Repair

## Verdict

**BLOCKED. F-6: INDEPENDENTLY VERIFIED REPAIRED. THREE SIBLING
HISTORICAL-MOVING-AUTHORITY DEFECTS: CONFIRMED / REPAIR REQUIRED. F-5 RETRY:
NOT READY. F-5: OPEN / ABSENT / UNCHANGED. N-16-5: NOT CLOSED.**

CPIPC-001 accepts the exact requested identifier. This verification changes no
predecessor test, production source, production script, dependency, normative
contract, or protected host state.

## Independent F-6 reconstruction

- `P = 2eaf536d05b6852c6bc6692cec139afab1083f84` — finalized BLOCKED F-5
  deployment-preparation attempt.
- `R = V = 8dcca97bb1a88a99cac3afe610f3651adcc58295` — finalized F-6 repair and
  this IV's repository entry.
- `V4 = 90510428422e451382549ce76111610752aaafb4` — F-4-IV entry, independently
  proven as the parent of its first implementation/verification commit.
- `U4 = 7124c019bf3f46eb07456b81146484609197dbc2` — finalized F-4-IV endpoint,
  independently proven by immutable phase metadata and the immediate later
  F-5 task-opening successor.

The exact first-parent interval `V4..U4` contains four F-4-IV commits and ten
files: the fresh IV suite, canonical report, status/changelog/decisions, task
lifecycle, and phase-completion metadata. At immutable `P`, retained
`test_43_no_protected_root_mutation_is_in_iv_diff` used implicit `V4..HEAD`.
The repair retains its identity, substring detector, and assertion but binds it
to explicit `V4..U4` via `F4_IV_FINALIZED`.

Historical and current evaluation pass. A disposable Git topology proves a
later deployment-like filename is excluded by the fixed endpoint while the old
moving interval sees it. A forbidden `protected-root` indicator committed
inside the historical interval is still detected. There is no HEAD/current
metadata special case, successor allowlist, phase-prefix filter, wildcard,
glob, `fnmatch`, skip, xfail, removal, rename, or vacuous assertion.

Accordingly F-6 is **INDEPENDENTLY VERIFIED REPAIRED**.

## Sibling safety matrix

| Sibling | Semantic scope | Moving authority | Valid? | F-5 repository changes expected to trip it? | Blocking before F-5? | Action |
|---|---|---|---|---|---|---|
| F-4-IV `test_44_no_helper_installation_or_pawa_write_in_iv` | Completed F-4 IV | implicit `V4..HEAD` file list | No — category B | No, if F-5 obeys its no-production/no-certification repository scope | Yes: mandatory prerequisite remains historically unsound | Narrow immutable-bound repair |
| F-4-IV `test_46_no_yubikey_or_certification_evidence_minted` | Completed F-4 IV | implicit `V4..HEAD` path-limited diff | No — category B | No, F-5 must mint no certification evidence | Yes | Narrow immutable-bound repair |
| F-4-IV `test_56_iv_changes_no_product_contract_or_dependency_bytes` | Completed F-4 IV | implicit `V4..HEAD` path-limited diff | No — category B | No, F-5 must change no production/contracts/dependencies | Yes | Narrow immutable-bound repair |

The test names, historical F-4-IV task contract, and immutable report define
facts about the completed IV. Live successors therefore cannot be their
historical authority. Their current green result is incidental to no successor
yet changing the selected paths, not proof that the ranges are sound. This IV
does not alter them.

The targeted prerequisite scan covers 1,086 test definitions in 25 `.30R*`
files and 48 Git/HEAD pattern lines. Other matches are safe rolling current-
state invariants, descendant/topology checks where HEAD is the subject, or
fixed-end historical checks. No additional category-B blocker beyond the three
disclosed siblings was identified.

## Verification and boundaries

- F-6 repair suite unchanged: **57 passed, 0 failed**.
- Complete F-4 IV plus F-6 repair suite: **113 passed, 0 failed**.
- Fresh F-6 IV suite: **65 passed, 0 failed**.
- F-6/F-4/F-3 history group: **321 passed, 0 failed**.
- H-2/F-2 software IV: **84 passed, 0 failed**, with one preserved obsolete
  F-3 demonstration deselected.
- Broad Gate 5/Gate 9/verifier/PAWA/PPA/RHAMP/FIDO2/presentation group:
  **882 passed, 0 failed**. The separately run old verifier finding suite
  reproduced its historical intentional construction-seal failure; the
  repaired verifier/IV suites are included in the clean 882-test group.
- Total clean deterministic evidence: **1,287 passed, 0 attributable failures**.
- No-test-weakening: no existing test changed, removed, renamed, skipped, or
  xfailed; no wildcard/glob/`fnmatch` broadening.
- Fixed-SHA attribution: IV artifacts only; `src/pcae`, `scripts`,
  `pyproject.toml`, and `docs/contracts` are unchanged from `V`.

F-3 and F-4 remain independently verified. H-1/H-2/F-2 production bytes and
prior evidence remain unchanged. The production protected root
`/Library/Application Support/PCAE/HPAC/protected-root` remains absent. No
helper, descriptor, current generation, PAWA deployment capability,
administrator interaction, protected election, YubiKey interaction,
presentation evidence, principal, or Gate certification was created.

Runtime remains `not_implemented / Observed / observe / unavailable`, with zero
plugins/capabilities and first effect absent. N-16-6/N-16-7 remain untouched.
FIDO2 and local presentation remain supported-not-exclusive; mechanism-neutral
mobile-only authentication and protected approval remain open/planned.

## Successor decision

F-5 RETRY is **NOT READY**. Recommended next, not begun:

1. `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R` — F-7 Immutable
   Remaining F-4-IV Evidence Guard Repair, limited exactly to tests 44, 46,
   and 56.
2. `.30R.5R.2.1R.1R.2R.1R.1` — fresh independent verification of F-7.
3. A freshly derived, separately authorized F-5 deployment-preparation retry.
4. Separate deployment-state IV.
5. `.30R.5R.2.1R.1R.3` — final real protected-presentation human election +
   presentation-bound N-16-5 certification and closure.

None is begun. N-16-5 remains NOT CLOSED.

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.**
