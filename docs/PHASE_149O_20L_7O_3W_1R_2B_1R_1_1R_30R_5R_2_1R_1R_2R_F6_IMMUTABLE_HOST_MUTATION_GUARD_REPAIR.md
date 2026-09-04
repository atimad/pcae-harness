# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R

## F-6 Immutable F-4-IV Host-Mutation Evidence Guard Repair

## Verdict

**COMPLETE. F-6: REPAIRED / FRESH INDEPENDENT VERIFICATION PENDING. F-5:
OPEN / ABSENT / UNCHANGED. N-16-5: NOT CLOSED.**

CPIPC-001 accepts the exact requested repair identifier. This phase changes
one historical verification node and adds its repair suite; it changes no
production source, production script, dependency, normative contract, or
protected host state.

## Immutable lineage and reconstruction

- `P = 7124c019bf3f46eb07456b81146484609197dbc2` — finalized F-4 IV head.
- `B = R0 = 2eaf536d05b6852c6bc6692cec139afab1083f84` — finalized BLOCKED F-5
  deployment-preparation attempt and this repair's entry.
- `V4 = 90510428422e451382549ce76111610752aaafb4` — actual F-4 IV entry, the
  finalized F-4 repair head.
- `U4 = 7124c019bf3f46eb07456b81146484609197dbc2` — immutable finalized F-4 IV
  endpoint.

The first F-4-IV commit `f1b4b85b` has parent `V4`. Immutable completion
metadata at `U4` identifies the completed F-4 IV, and the first-parent interval
`V4..U4` is exactly four commits: implementation/verification, task closure,
completion staging, and pushed-state reconciliation. Its exact ten-file diff
contains the fresh IV test, report, status, decisions, task lifecycle, and
completion metadata only.

At immutable pre-repair `B`, retained node
`test_43_no_protected_root_mutation_is_in_iv_diff` calls
`git diff --name-only V` with no upper bound. Git therefore supplies the live
working-tree/HEAD endpoint. At the legitimate F-5 task successor it absorbs a
task filename containing `production-protected-root...` and fails, although
the completed F-4 IV performed no host deployment.

The original semantic invariant is: the completed F-4 IV's own repository
change interval contains no protected-root deployment/mutation indicator. It
is not a claim that later phases may never discuss or prepare deployment.

## Narrow repair

The retained node, name, substring detector, and assertion are unchanged in
strength. Its range alone is corrected from implicit `V..HEAD` to explicit
`V4..U4` using `F4_IV_FINALIZED = U4`. There is no live `HEAD`, `origin/main`,
live completion metadata, `PROJECT_STATUS`, successor allowlist, phase-prefix
filter, wildcard, glob, `fnmatch`, skip, xfail, removal, or rename.

Direct historical and current evaluation passes. In an isolated disposable
repository, a later file named `successor-protected-root-preparation.txt`
trips the old moving range but is excluded by the repaired immutable range.
When `protected-root-forbidden.txt` is committed inside the simulated
historical interval, the retained detector fails as required.

## Test results

- Fresh F-6 repair suite: **57 passed, 0 failed**.
- Complete predecessor F-4 IV plus fresh F-6 suite: **113 passed, 0 failed**.
- Focused status guard plus both suites: **114 passed, 0 failed**.
- Broad deterministic F-6/F-4/F-3/H-2/F-2/H-1/PAWA/PPA/RHAMP and historical
  prerequisite sweep: **691 passed, 0 failed, 0 skipped, 0 errors**.
- Fixed-SHA attribution: only the retained F-4-IV node and fresh repair suite
  change verification behavior; `src/pcae`, `scripts`, `pyproject.toml`, and
  `docs/contracts` have an empty `R0..candidate` diff.
- No-test-weakening result: zero removed or renamed tests; zero skip, skipif,
  `pytest.skip`, xfail, wildcard, glob, or `fnmatch` broadening.

## Same-defect-family scan

The targeted scan covered **1,086 prerequisite test definitions in 25
`.30R*` files**. It found **48 textual Git/HEAD pattern lines in 15 files**.
Manual semantic classification found the following:

- Safe current-state checks: contract/source immutability requirements that
  explicitly assert a property must remain true at current HEAD; descendant
  topology checks where HEAD is only the subject; and already-fixed
  historical checks with immutable endpoints.
- Repaired historical-moving-authority defect: F-4-IV `test_43`.
- Additional latent historical-moving-authority matches, not currently
  failing and not repaired here: F-4-IV `test_44`, `test_46`, and `test_56`.
  Their names and assertions speak about what happened *in the completed IV*
  but still use implicit `V..HEAD`. They do not prevent the current clean
  prerequisite baseline because no successor has changed their path-limited
  subjects. They are recorded for fresh IV adjudication rather than silently
  changed outside this phase's exact node authorization.

Thus no **additional currently blocking** moving-history defect was found in
the N-16-5 prerequisite chain. The fresh F-6 IV must independently adjudicate
the three disclosed latent matches before authorizing a deployment retry.

## Product and host boundaries

F-3 and the F-4 core immutable source-scope repair remain independently
verified. H-1, H-2, and F-2 production bytes are unchanged. The production
protected root `/Library/Application Support/PCAE/HPAC/protected-root` remains
absent. No directory, helper, installation descriptor, current generation,
PAWA deployment capability, administrator prompt, human election, YubiKey
interaction, presentation evidence, principal, or Gate certification was
created.

Runtime remains `not_implemented / Observed / observe / unavailable`, with
zero plugins and zero capabilities. No `adapter.dispatch()`, runtime effect,
N-16-6, N-16-7, Slice C, or first governed runtime external effect became
reachable.

## Successor sequence

The exact CPIPC-valid sequence is derived and not begun:

1. `.30R.5R.2.1R.1R.2R.1` — Independent Verification of the F-6 Immutable
   F-4-IV Host-Mutation Evidence Guard Repair, including adjudication of the
   disclosed latent sibling guards.
2. `.30R.5R.2.1R.1R.2.1` — fresh Production Protected-Root /
   Protected-Presentation Helper Deployment Preparation retry after a clean
   IV verdict (the reused `.2.1` conceptual identifier must be rechecked
   against canonical lineage before opening).
3. A separately derived deployment-state IV successor.
4. `.30R.5R.2.1R.1R.3` — Final Real Protected-Presentation Human Election +
   Presentation-Bound N-16-5 Certification and Closure.

FIDO2/YubiKey remains one supported, verified authentication profile, not
exclusive. Local protected TTY remains one supported presentation profile,
not exclusive. Mechanism-neutral human authentication and protected approval,
including mobile-only profiles, remain open planned future architecture and
are not prerequisites for unrelated non-effecting development.

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.**
