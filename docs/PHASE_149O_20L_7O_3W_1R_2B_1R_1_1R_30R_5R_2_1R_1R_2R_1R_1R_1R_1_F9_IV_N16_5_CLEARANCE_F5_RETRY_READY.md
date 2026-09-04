# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1

**Independent Verification of the F-9 Immutable F-7-Repair-Suite Deployment-Evidence Guard Repair + Final N-16-5 Moving-History Clearance + F-5 Retry Readiness Adjudication**

Verification-only phase. No repair, no deployment, no protected-root/helper/PAWA/human/hardware interaction, no N-16-5 closure, no N-16-6/N-16-7 work.

## CPIPC Lineage

Confirmed the exact CPIPC-valid successor of `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R` (F-9, completed) is `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1`, by the same lineage precedent used throughout this chapter (a completed repair phase's own IV appends `.1`). No discrepancy found; scope preserved exactly as directed.

- `V` (this IV's phase-entry SHA) = `a3a0494807ed6c8de10a2eb8db14e41655039fdd`
- `F9_ENTRY` = `54327556c832a9b7699cb2b6b7c99dc29ca65539`
- `F4R_LOWER` = `3fbc12d7ad671ed6c9348cb29ffb5c2d35447e5f` (independently confirmed as F-4 repair phase entry; parent of `a40f8163`)
- `F4R_UPPER` = `90510428422e451382549ce76111610752aaafb4` (independently confirmed as the last commit at this phase's own ID before the F-4-IV successor phase begins)
- F-9 repair commits: `3cec7921` (test repair), `863e7de1` (task contract), `1a41408b` (task lifecycle close)

## Objective 1 — F-9 Independent Verification

Independently reconstructed (not trusted from F-9 report prose) the original semantics and bounds of all three repaired nodes in `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_f4_immutable_scope_repair.py`:

- `test_31_no_protected_root_mutation_in_repo_diff`
- `test_32_no_helper_installation_artifact_added`
- `test_43_f4_change_is_test_only`

**Original defect** (verified against the F-9-entry blob): all three used `git("diff", "--name-only", R0)` — an implicit-`HEAD` upper bound. As the repository moves forward, this makes an assertion about the *fixed* F-4-repair phase's own file scope silently depend on live/current state, which is exactly the COMPLETED HISTORICAL FACT + MOVING HEAD defect family.

**Repair** (verified against current source): all three now use `git("diff", "--name-only", R0, F4_REPAIR_FINALIZED)`, bounding the assertion to the file's own immutable historical range.

**Four-way validation performed independently** (fresh disposable synthetic git repos, not the F-9 suite's own assertions):

| Test | Historical | Current successor | Future successor | Negative (forbidden condition in scope) |
|---|---|---|---|---|
| test_31 | PASS | PASS | PASS | FAIL (correctly) |
| test_32 | PASS | PASS | PASS | FAIL (correctly) |
| test_43 | PASS | PASS | PASS | FAIL (correctly) |

No test weakening found: test count in the owner file unchanged (43), no skip/xfail/wildcard/fnmatch/rename-to-evade in the repaired nodes, no live-HEAD reference remaining in the repaired nodes.

**F-9: INDEPENDENTLY VERIFIED REPAIRED**

- `test_31_no_protected_root_mutation_in_repo_diff`: INDEPENDENTLY VERIFIED REPAIRED
- `test_32_no_helper_installation_artifact_added`: INDEPENDENTLY VERIFIED REPAIRED
- `test_43_f4_change_is_test_only`: INDEPENDENTLY VERIFIED REPAIRED

## Objective 2 — Final N-16-5 Moving-History Clearance

Derived the bounded N-16-5 prerequisite chain (F-3 → F-4 → F-6 → F-7 → F-8 → F-9 repair/IV suites, plus the RHAMP/PAWA/CTAP2/protected-presentation suites that actually gate F-5 deployment and final certification) and performed a read-only scan for the `<fixed SHA>..HEAD`/live-worktree moving-authority pattern within it.

One relevant pre-existing, already-disclosed hit was independently re-confirmed: `test_30_repair_suite_contains_a_stale_live_head_assertion_finding_f3` in the human-election IV suite is a self-documenting finding test whose target string is no longer present in the referenced repair suite (the underlying stale assertion it was tracking has already been removed); the tracking test itself is now stale. This is a housekeeping mismatch, not a live moving-historical-authority hole — it does not let any false historical claim pass, and it was already disclosed identically by the predecessor F-9 report. Classified: **PRE-EXISTING NONBLOCKING**.

All other `HEAD`-referencing assertions found within the bounded chain (e.g. `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py`, the CTAP2 repair/IV suites) bind between two fixed commits, or use a fixed lower bound against current `HEAD` for a genuinely current currency/byte-identity assertion ("has production changed since entry X"), not a historical-fact assertion — classified **SAFE CURRENT-STATE CHECK**.

No new blocking historical-moving-authority defect was found.

**NO ADDITIONAL BLOCKING HISTORICAL-MOVING-AUTHORITY DEFECT FOUND IN CURRENT N-16-5 PREREQUISITE CHAIN.**

**N-16-5 PREREQUISITE MOVING-HISTORY CLEARANCE: VERIFIED**

This clears verification-provenance prerequisites only. It does NOT close N-16-5.

## Regression Sweep

- Fresh F-9 IV suite (this phase, 55 tests): 55 passed, 0 failed
- F-9 repair suite (68 tests): 68 passed, 0 failed
- F-4-repair / F-4-IV / F-6-repair / F-6-IV / F-7-repair / F-8-repair chain (564 tests total across 9 files): 564 passed, 0 failed
- Broad deterministic sweep — Gate5 (x2), Gate9 (x4), hpac_verifier (x4), PAWA (x2), RHAMP (x2), CTAP2 (x2): 768 passed, 2 failed

**2 pre-existing, unrelated failures** in `test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py` (`test_object_dunder_new_bypasses_trusted_construction_seal`, `test_forged_via_object_new_would_report_real_runtime_eligible`) — independently confirmed present, byte-identical, at the F-9 phase-entry commit (`54327556`) as well as at current `HEAD`; first disclosed as BLOCKING in the unrelated historical phase `149O.20L.7O.3W.1R.2B.1R.1.1R.5.1` (mechanism-neutral HPAC verifier / principal-registry consumption boundary track). Unrelated to the N-16-5 moving-history defect family and to F-5 deployment readiness as literally enumerated by this phase's readiness criteria. Not repaired here (out of scope; verification-only). Together with the test_30 election-IV finding above, this reproduces exactly the same 3 pre-existing failures the predecessor F-9 report already disclosed — no new regression.

No production source change, no production script change, no dependency change, no normative contract change since this IV's phase entry (`git diff --name-only a3a0494 -- src/pcae scripts pyproject.toml docs/contracts` empty).

## Objective 3 — F-5 Retry Readiness

F-5 read-only host inspection: production protected root absent, no `*installation*` or `*current-generation*` descriptor found under `/Library/Application Support/PCAE/HPAC/`. No mutation performed. No administrator, human, or YubiKey interaction occurred.

All 20 readiness conditions independently checked:

1. F-9 independently verified repaired — YES
2. test_31 retains original negative protection — YES
3. test_32 retains original negative protection — YES
4. test_43 retains original negative protection — YES
5. F-7 remains independently verified repaired — YES
6. F-8 remains independently verified repaired — YES
7. F-3 remains independently verified repaired — YES
8. F-4 remains independently verified repaired — YES
9. F-6 remains independently verified repaired — YES
10. Final bounded moving-history clearance VERIFIED — YES
11. No other current prerequisite blocker — YES (the 3 pre-existing failures are unrelated/disclosed, not prerequisite blockers)
12. F-5 remains absent and untouched — YES
13. No production source changed — YES
14. No production script changed — YES
15. No normative contract changed — YES
16. No dependency changed — YES
17. Runtime remains Observed/observe/unavailable — YES
18. Plugins remain 0 — YES
19. Capabilities remain 0 — YES
20. First governed runtime external effect remains absent/unreachable — YES

**F-5 RETRY: READY**

**F-5: OPEN / ABSENT / UNCHANGED**

No deployment occurs in this phase. READY means only that a fresh, separately governed deployment-preparation retry may be authorized.

## N-16-5 Status

N-16-5 remains **NOT CLOSED**. Remaining mandatory chain: F-5 deployment preparation → independent deployment-state IV → final real protected-human + genuine YubiKey presentation-bound certification → N-16-5 closure only if every requirement is satisfied and no blocker remains.

## Preserved Flexibility

`hpac.fido2.uv_presence.v2` (FIDO2/YubiKey) remains one certified, real-hardware-verified, **supported-not-exclusive** authentication profile. `pcae-protected-local-presentation/1.0` (local TTY) remains one **supported-not-exclusive** protected-presentation profile. Mobile-only authentication and protected approval (platform authenticators, mobile passkeys, biometric platform user verification, NFC roaming authenticators, mobile protected-approval transport) remain explicitly **OPEN / PLANNED** future architecture, not implemented here, not made an N-16-5 blocker.

## Boundaries Preserved

No protected-root mutation, no helper installation, no installation/current-generation descriptor created, no PAWA deployment authority issued or consumed, no administrator credentials requested, no protected APPROVE/REJECT requested, no YubiKey touch, no FIDO2 PIN request, no presentation evidence created, no PRODUCTION `AuthenticatedHumanPrincipal` minted, no Gate 5 final certification performed, N-16-5 not closed, N-16-6 not begun, N-16-7 not begun, Slice C not begun, first governed runtime external effect not implemented or called, execution not enabled.

Runtime: not_implemented / Observed / observe / unavailable, 0 plugins, 0 capabilities. First effect absent / unreachable. N-16-6/N-16-7 untouched.

## Successor

Per Objective 3's READY verdict, the exact CPIPC-valid successor for a NEW, separately authorized deployment-preparation retry phase is `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1` (conceptual title: Production Protected-Root / Protected-Presentation Helper Deployment Preparation Retry). Not begun here. The historical BLOCKED F-5 deployment-preparation attempt and the historical BLOCKED combined F-7/F-8 IV report remain immutable and are not rewritten.

## Governance

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved. This phase was executed and finalized by the primary human-authorized operator context.
