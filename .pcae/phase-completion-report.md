# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.23 Complete — Independent Verification of the N-16-3 Narrow-Eligibility Policy (BLOCKED independent-verification result — Option B)

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.23
**Type:** independent verification of `.1R.22` (N-16-3 Narrow-Eligibility Policy and Contract Implementation)
**Status:** BLOCKED INDEPENDENT-VERIFICATION RESULT — finalized (Option B)
**Verification-entry SHA:** `15aeb269` (`.1R.22` finalize head; `HEAD == origin/main`; `origin/main..HEAD = 0` at entry)
**Immutable pre-`.1R.22` baseline (independently reconstructed):** `8603fe6a` (`.1R.21` push-reconcile head; parent of the `.1R.22` implementation commit `1dadeb21`; `git rev-list --count 8603fe6a..HEAD = 9`; `git diff --name-only 8603fe6a HEAD -- src/pcae` = exactly the two authorized files)
**First external effect:** ABSENT — no `adapter.dispatch(` / `subprocess` / `socket` / `Popen` / `os.system` / `urllib` / `requests` / `httpx` added in the `8603fe6a..HEAD` `src/pcae` diff; no `runtime_dispatch_gate10.py`; no real adapter; two independent production blockers keep the profile unsatisfiable
**Execution:** not enabled — runtime `not_implemented / Observed / observe / unavailable`; POL-005 DENY body byte-unchanged; 0 plugins / 0 capabilities; `pcae runtime inspect` posture byte-identical at entry and finalization
**Production source changed by this phase:** none
**Normative contracts changed by this phase:** none
**Scope-fence / guard files changed by this phase:** none — the 16 undisclosed `.1R.22`-attributable point-in-time guard-freeze test failures (N-23-3) are NOT repaired inside `.1R.23`; referred to `149O.20L.7O.3W.1R.2B.1R.1.1R.22R`

## Substantive dispositions (independently RE-DERIVED, not trusted from `.1R.22`)

| Item | Result |
|---|---|
| PBRD-001 v3.0 MAJOR trigger (§16 "weakening POL-005 eligibility", present verbatim at `8603fe6a`) | VERIFIED |
| PBRD-001 v3.0 explicit migration completeness / no silent auto-upgrade / no compatibility default | VERIFIED |
| Legacy v2.x request → no marker → POL-005 DENY | VERIFIED |
| Trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` classification — 13 predicates (AST-counted), builder-owned, sole `profile_classification` writer | VERIFIED |
| Forged / `dataclasses.replace`-transplanted / incomplete-marker / complete-without-marker / seal-stripped → structural DENY (live recomputation) | VERIFIED |
| N-16-6 admission interface + fail-closed non-admitting production stub | VERIFIED |
| Private `_supply_chain_admission_resolver` override — no production call site; sole production builder call omits it | VERIFIED |
| **`RUNTIME_DISPATCH_LOCAL_CLI_V1` PRODUCTIONALLY UNSATISFIABLE — two independent blockers (B1 N-16-6, B2 N-16-5)** | VERIFIED |
| No production PB `ALLOW` for a real `runtime_dispatch` | VERIFIED |
| POL-005 amended semantics — exact one-profile carve-out; DENY body byte-identical; universal applicability retained | VERIFIED |
| POL-013 statically never `ALLOW` / never `HUMAN_REVIEW` (AST); dynamic vocabulary DENY-or-neutral; adapter-only; registered last; canonical POL-001..013 | VERIFIED |
| `_compose` / `_structural_request_failure` / `_decision` whole-function byte-unchanged; `DENY > HUMAN_REVIEW > ALLOW` intact | VERIFIED |
| Human authority alone never exempts POL-005 | VERIFIED |
| Broader effect classes (provider/network/credential/shell/argv/wrong-target/missing-admission) all blocked | VERIFIED |
| NON_REAL / real-human-authority wall (N-16-5) — upstream, unchanged | VERIFIED |
| Gate 5/7/8/9/10 modules byte-unchanged; N-16-4 independence; runtime posture unchanged; NG-025 in the correct file; PBPA-001 v1.1 additive-only | VERIFIED |
| No test weakening in the `.1R.22` diff (0 removed defs, 0 xfail, 1 scoped skip, no rename) | VERIFIED |
| **Fixed-SHA A/B regression attribution / `.1R.22` verification-evidence completeness** | **BLOCKED — N-23-3** |

## Adjudications

- **N-16-3 — PARTIALLY CLOSED** (model verified; not fully CLOSED solely due to N-23-3).
- **PBRD-001 v3.0 MAJOR MIGRATION — VERIFIED.**
- **POL-005 NARROW MATCH-DOMAIN EVOLUTION — VERIFIED.**
- **POL-013 — VERIFIED; NEVER EMITS ALLOW OR HUMAN_REVIEW.**
- **`RUNTIME_DISPATCH_LOCAL_CLI_V1` PRODUCTIONALLY UNSATISFIABLE — VERIFIED** (B1 N-16-6 + B2 N-16-5).
- **`.3` delegated finalization / commit / push — remains UNAUTHORIZED** (preserved verbatim; no precedent).
- **N-16-4 / N-16-5 / N-16-6 / N-16-7 — OPEN.** Slice C / Slice D — no phase ID. First external effect — ABSENT.

## Blocker — N-23-3

The fixed-SHA A/B (`git worktree` at `8603fe6a`, deterministic, no xdist; B `15aeb269` ≡ C `origin/main`) finds **16 functional guard-test nodes that PASS at `8603fe6a` and FAIL at `15aeb269`**, attributable to the two authorized `.1R.22` changes (add POL-013; PBPA-001 v1.0→v1.1 + PBRD v2.1→v3.0 + POL-005 §12a), across ≥9 test files — `test_permission_broker_policy_rule_framework.py` (×5, incl. `test_registry_has_twelve_policies`); `test_permission_broker_observation_verification.py::test_broker_default_policy_rule_count_unchanged`; `test_phase_149d_rwmpc_contract_independent_verification.py::TestContractsUnamended::test_pbpc_and_pbpa_contract_files_unchanged_since_before_chapter_149`; `test_phase_149o_16_hatp_mandatory_consumption_contract_independent_verification.py::TestMC14EffectTruthfulnessAgainstCurrentSource::test_pol_005_denies_unconditionally_when_simulation_only_false`; `test_phase_149o_18c_ag3_mandatory_consumption_integration.py` / `test_phase_149o_18d_ag5_...` / `test_phase_149o_18e_cli_legacy_authority_migration_integration.py` (each `::TestContractByteIdentity::test_contract_byte_unchanged[PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md]`); `test_phase_149o_19_3r_hmic_frozen_file_set_contract_repair.py::test_upstream_contract_byte_unchanged_by_this_repair[PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md]`; `test_phase_149o_20l_7o_3v_1r_1_contract_verification.py::TestBoundariesUnchanged::test_pol_005_unchanged_claim_present`; `test_phase_149o_20l_7o_3v_1r_contract_repair.py::TestNoNewContradictions::test_no_go_statements_preserved`; `test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py::test_pbrd_remains_projection_only_and_pol005_remains_hard_deny` + `::test_rpac_companion_contract_is_byte_identical_and_riasc_pbrd_only_normalized`.

**None** is named in the `.1R.22` canonical artifact §11.1 guard-impact inventory or disclosed in §12 — directly contradicting its "0 unexplained attributable functional regressions" (§12 / PROJECT_STATUS) and "each was widened … and is listed here" (§11.1) claims. All 16 are stale point-in-time **text/count freeze** guards (registry cardinality 12→13; PBPA-001 byte-freeze → v1.1; PBRD/POL-005 text-freeze → v3.0 wording), **not behavioural** Permission-Broker regressions — but real failing nodes, re-run individually at both SHAs (not order-dependent). This is the identical failure mode that BLOCKED `.1R.18` (17 undisclosed `.1R.17` guard regressions → `.1R.17R`) and `.1R.20` (3 undisclosed `.1R.19` guard regressions → `.1R.19R`). Repair requires guard **test**-file edits across ≥9 phases plus a provenance-preserving `.1R.22` §11/§12 erratum — a dedicated repair phase, not this IV.

## Non-blocking findings

- **N-23-1** — a structurally-complete (test-built, sealed) profile with nothing else triggering composes to the `_compose` INV-008 non-executable default `ALLOW` (`policy_would_allow_if_execution_existed`, `implementation_status = EXECUTION_UNAVAILABLE`). Contract-sanctioned (PBRD §12a.4/.5), unreachable in production (B1 + B2), every downstream gate still blocks. `.1R.22`'s own `test_case_12` asserts this.
- **N-23-2** — PBNDE-001 §3 / PBRD §12a.1 say the marker is "committed into the request canonical digest"; it is not literally in the digest. PBRD §5's "derived commitments" paragraph describes the real mechanism (live structural recomputation, at least as strong). Wording only.

## Evidence

Fresh IV suite `tests/test_narrow_eligibility_policy_iv_3w1r2b1r1_1r23.py` — **55 tests, 55 passed, 0 failed** (deterministic, no xdist). Targeted affected-suite run at HEAD: 566 passed / 3 skipped / 1 pre-existing failure (reproduces byte-identically at `8603fe6a`). Gate/Slice suite run at HEAD: 696 passed. `.1R.23`-attributable functional regressions = 0. 4 known pre-existing failures reproduce identically at both SHAs (0 delta) and match the `.1R.22` §12 disclosure.

## Governance

`pcae health` healthy · `pcae check` passed · `pcae status coherence` coherent · `pcae doctor task-memory` warning-only historical `tasks/DONE.md` omissions · `pcae runtime inspect` `not_implemented / Observed / observe / unavailable` byte-identical. Governed `pcae` lifecycle only; the historical delegated `.3` finalization / commit / push incident remains **UNAUTHORIZED — preserved**. Only the primary human-authorized operator holds `.1R.23` lifecycle authority. This phase is **not self-closed**.

## Required human decision / recommended next

Authorize **`149O.20L.7O.3W.1R.2B.1R.1.1R.22R` — N-16-3 Scope-Fence / Verification-Evidence Reconciliation and Repair** (widen the 16 stale guards to the authorized change set, no wildcard, each still rejecting an unauthorized change; provenance-preserving `.1R.22` §11/§12 erratum; no production or normative-contract change), then **`.1R.22R.1`** — its Independent Verification. **Do not skip to N-16-4.** N-16-4 / N-16-5 / N-16-6 / N-16-7 — OPEN. Do not implement Slice C, the first external effect, or execution enablement.

Canonical artifact: `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_23_INDEPENDENT_VERIFICATION_OF_THE_N_16_3_NARROW_ELIGIBILITY_POLICY.md`.
