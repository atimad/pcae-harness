# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1

## Independent Verification of the N-16-4 Scope-Fence / Verification-Evidence Reconciliation

**Verdict: BLOCKED — `.1R.26R` NOT VERIFIED.**

The two intended repairs are exact and the independently derived historical attributable set is exactly 42. The finalized `.1R.26R` repair suite nevertheless fails against its own committed content. Repair is required; this IV stopped without repairing it.

## Immutable identities

| Identity | SHA |
|---|---|
| V — verification entry | `e52d2f8e9175015a2b344a547bea0c11058a92c8` |
| A — pre-`.1R.26` | `28b8b2b7` |
| I — implementation before reconciliation | `99d85106` |
| B — finalized `.1R.26` | `9d28f7ef` |
| C — finalized `.1R.27` BLOCKED | `ba4d21c3` |
| R — finalized `.1R.26R` | `e52d2f8e9175015a2b344a547bea0c11058a92c8` |

`8b762a35^ == C`: B is the repair's semantic comparison base, not its literal Git parent after `.1R.27` finalization.

## Reproductions and repair strength

First node: `tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py::test_runtime_posture_unchanged_and_no_new_first_effect_call_site` — PASS A, FAIL B (exactly missing authorized `runtime_dispatch_gate7.py`), PASS R. Literal exact equality is retained. Fresh direct challenges reject an unauthorized fourth source, a missing Gate7 source, and a substituted runtime source. Runtime-posture and no-new-first-effect assertions remain.

Second node: `tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py::test_53_test_importers_of_gate7_symbols_are_a_known_finite_set` — PASS B, FAIL C (the legitimate `.1R.27` importer), PASS R. The allowlist is literal and finite, uses real import-statement detection, and reports missing and unexpected importers. Fresh direct challenges reject an unauthorized synthetic importer and a missing authorized importer.

## Fixed-SHA A/B evidence

14-suite A/I: A 769 pass / 8 fail (777); I 728 pass / 49 fail (777). Eight common and exactly 41 I-only = 40 originally reconciled plus the first missed node. The independently reproduced B-pass/C-fail importer node makes the true total **42**.

14-suite A/B/R: A 769/8 (777); B 766/9 (775); R 767/8 (775). A/B candidate-only = 1 (first node). A/R candidate-only = 0.

Broader AST-derived 69-file deterministic guard sweep: A 3,387 pass / 185 fail / 5 skip (3,577); B 3,385 / 186 / 5 (3,576); R 3,386 / 185 / 5 (3,576). All 185 failures common. A/B candidate-only = first node only; A/R candidate-only and unexplained attributable regressions = 0.

## Exact 42-node table

Rows 1–36 and 38–41 are the 40 original reconciliations. Row 37 and row 42 were missed. Every row is attributable because only the authorized Gate7/REPRC change trips its historical exact scope, byte, contract, or importer guard.

| # | File | Node | Original | Missed | Current | Strength |
|---:|---|---|---|---|---|---|
| 1 | `tests/test_dispatch_attempt_durable_lifecycle_3w1r2b1r1_1r19.py` | `test_gate5_through_gate9_byte_unchanged` | yes | no | PASS at R | finite exact/semantic freeze |
| 2 | `tests/test_dispatch_attempt_durable_lifecycle_3w1r2b1r1_1r19.py` | `test_no_contract_file_changed` | yes | no | PASS at R | finite exact/semantic freeze |
| 3 | `tests/test_dispatch_attempt_durable_lifecycle_iv_3w1r2b1r1_1r20.py` | `test_no_normative_contract_changed_since_baseline` | yes | no | PASS at R | finite exact/semantic freeze |
| 4 | `tests/test_dispatch_attempt_durable_lifecycle_iv_3w1r2b1r1_1r20.py` | `test_slice_a_and_closed_gate_modules_are_byte_unchanged_since_baseline` | yes | no | PASS at R | finite exact/semantic freeze |
| 5 | `tests/test_dispatch_attempt_durable_lifecycle_iv_3w1r2b1r1_1r20.py` | `test_slice_b_production_scope_since_baseline_is_exactly_the_authorized_set` | yes | no | PASS at R | finite exact/semantic freeze |
| 6 | `tests/test_dispatch_attempt_durable_lifecycle_reconciliation_3w1r2b1r1_1r19r.py` | `test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap` | yes | no | PASS at R | finite exact/semantic freeze |
| 7 | `tests/test_dispatch_attempt_durable_lifecycle_reconciliation_3w1r2b1r1_1r19r.py` | `test_no_contract_change_since_r20_head` | yes | no | PASS at R | finite exact/semantic freeze |
| 8 | `tests/test_gate10_pre_effect_eligibility_coordinator_3w1r2b1r1_1r17.py` | `test_earlier_gates_and_contracts_bytes_unchanged_since_baseline` | yes | no | PASS at R | finite exact/semantic freeze |
| 9 | `tests/test_gate10_pre_effect_eligibility_coordinator_3w1r2b1r1_1r17.py` | `test_production_scope_since_baseline_is_the_single_new_file` | yes | no | PASS at R | finite exact/semantic freeze |
| 10 | `tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py` | `test_file_byte_unchanged_since_phase_entry_baseline[src/pcae/core/runtime_dispatch_gate7.py]` | yes | no | PASS at R | finite exact/semantic freeze |
| 11 | `tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py` | `test_no_unpushed_divergence_at_verification_entry` | yes | no | PASS at R | finite exact/semantic freeze |
| 12 | `tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py` | `test_production_scope_since_baseline_is_exactly_one_new_file` | yes | no | PASS at R | finite exact/semantic freeze |
| 13 | `tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py` | `test_widened_guard_module_passes_at_head[test_gate9_serialization_semantics_repair_3w1r2b1r1_1r15_2]` | yes | no | PASS at R | finite exact/semantic freeze |
| 14 | `tests/test_gate10_slice_a_reconciliation_independent_verification_3w1r2b1r1_1r17r_1.py` | `test_gate_5_perm_7_8_are_byte_unchanged_since_r153_baseline` | yes | no | PASS at R | finite exact/semantic freeze |
| 15 | `tests/test_gate10_slice_a_reconciliation_independent_verification_3w1r2b1r1_1r17r_1.py` | `test_gate_5_to_9_and_neighbour_modules_byte_identical_since_baseline` | yes | no | PASS at R | finite exact/semantic freeze |
| 16 | `tests/test_gate10_slice_a_reconciliation_independent_verification_3w1r2b1r1_1r17r_1.py` | `test_no_normative_contract_changed_since_baseline` | yes | no | PASS at R | finite exact/semantic freeze |
| 17 | `tests/test_gate10_slice_a_reconciliation_independent_verification_3w1r2b1r1_1r17r_1.py` | `test_no_production_source_changed_since_the_r17_head_except_authorized_slice_b` | yes | no | PASS at R | finite exact/semantic freeze |
| 18 | `tests/test_gate10_slice_a_reconciliation_independent_verification_3w1r2b1r1_1r17r_1.py` | `test_production_scope_since_baseline_is_the_one_r17_file_plus_authorized_slice_b` | yes | no | PASS at R | finite exact/semantic freeze |
| 19 | `tests/test_gate10_slice_a_scope_fence_reconciliation_3w1r2b1r1_1r17r.py` | `test_gate5_permission_gate7_gate8_still_byte_unchanged_since_r153` | yes | no | PASS at R | finite exact/semantic freeze |
| 20 | `tests/test_gate10_slice_a_scope_fence_reconciliation_3w1r2b1r1_1r17r.py` | `test_no_contract_file_changed_since_baseline` | yes | no | PASS at R | finite exact/semantic freeze |
| 21 | `tests/test_gate10_slice_a_scope_fence_reconciliation_3w1r2b1r1_1r17r.py` | `test_no_production_source_changed_since_baseline_except_the_one_r17_file` | yes | no | PASS at R | finite exact/semantic freeze |
| 22 | `tests/test_gate9_serialization_semantics_repair_3w1r2b1r1_1r15_2.py` | `test_earlier_gate_modules_unchanged[runtime_dispatch_gate7.py]` | yes | no | PASS at R | finite exact/semantic freeze |
| 23 | `tests/test_n16_3_reconciliation_iv_3w1r2b1r1_1r22r1.py` | `test_29_meta_guard_inventory_independently_discovered_and_run` | yes | no | PASS at R | finite exact/semantic freeze |
| 24 | `tests/test_n16_3_reconciliation_iv_3w1r2b1r1_1r22r1.py` | `test_38_n23_2_contract_wording_left_untouched_since_r23_head` | yes | no | PASS at R | finite exact/semantic freeze |
| 25 | `tests/test_n16_3_reconciliation_iv_3w1r2b1r1_1r22r1.py` | `test_39_no_production_or_contract_diff_since_r22r1_entry` | yes | no | PASS at R | finite exact/semantic freeze |
| 26 | `tests/test_n16_3_reconciliation_iv_3w1r2b1r1_1r22r1.py` | `test_3_production_scope_since_baseline_is_exactly_the_two_authorized_files` | yes | no | PASS at R | finite exact/semantic freeze |
| 27 | `tests/test_n16_3_scope_fence_reconciliation_3w1r2b1r1_1r22r.py` | `test_first_external_effect_absent` | yes | no | PASS at R | finite exact/semantic freeze |
| 28 | `tests/test_n16_3_scope_fence_reconciliation_3w1r2b1r1_1r22r.py` | `test_n23_2_deferred_no_contract_change_by_this_phase` | yes | no | PASS at R | finite exact/semantic freeze |
| 29 | `tests/test_n16_3_scope_fence_reconciliation_3w1r2b1r1_1r22r.py` | `test_no_normative_contract_diff_since_baseline_beyond_the_authorized_set` | yes | no | PASS at R | finite exact/semantic freeze |
| 30 | `tests/test_n16_3_scope_fence_reconciliation_3w1r2b1r1_1r22r.py` | `test_no_production_source_diff_by_this_phase` | yes | no | PASS at R | finite exact/semantic freeze |
| 31 | `tests/test_n16_3_scope_fence_reconciliation_3w1r2b1r1_1r22r.py` | `test_production_scope_since_baseline_is_exactly_the_two_authorized_files` | yes | no | PASS at R | finite exact/semantic freeze |
| 32 | `tests/test_narrow_eligibility_policy_iv_3w1r2b1r1_1r23.py` | `test_gate7_and_gate9_and_gate10_modules_byte_unchanged` | yes | no | PASS at R | finite exact/semantic freeze |
| 33 | `tests/test_narrow_eligibility_policy_iv_3w1r2b1r1_1r23.py` | `test_only_authorized_contract_files_changed_since_baseline` | yes | no | PASS at R | finite exact/semantic freeze |
| 34 | `tests/test_narrow_eligibility_policy_iv_3w1r2b1r1_1r23.py` | `test_only_two_production_files_changed_since_baseline` | yes | no | PASS at R | finite exact/semantic freeze |
| 35 | `tests/test_runtime_dispatch_contract_normalization_independent_verification_3w1r2b1r1_1r15_5.py` | `test_gate_5_6_7_8_production_modules_byte_unchanged_since_baseline` | yes | no | PASS at R | finite exact/semantic freeze |
| 36 | `tests/test_runtime_dispatch_contract_normalization_independent_verification_3w1r2b1r1_1r15_5.py` | `test_no_unplanned_contract_file_changed_since_task_open` | yes | no | PASS at R | finite exact/semantic freeze |
| 37 | `tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py` | `test_runtime_posture_unchanged_and_no_new_first_effect_call_site` | no | yes | PASS at R | finite exact/semantic freeze |
| 38 | `tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py` | `test_n20_4_lifecycle_diff_since_r20_head_is_only_the_remap` | yes | no | PASS at R | finite exact/semantic freeze |
| 39 | `tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py` | `test_no_normative_contract_change_since_baseline` | yes | no | PASS at R | finite exact/semantic freeze |
| 40 | `tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py` | `test_no_slice_a_gate_or_item9_drift_since_r19_head[src/pcae/core/runtime_dispatch_gate7.py]` | yes | no | PASS at R | finite exact/semantic freeze |
| 41 | `tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py` | `test_production_diff_since_r19_head_is_exactly_the_n20_4_remap` | yes | no | PASS at R | finite exact/semantic freeze |
| 42 | `tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py` | `test_53_test_importers_of_gate7_symbols_are_a_known_finite_set` | no | yes | PASS at R | finite exact/semantic freeze |

## Provenance and unchanged semantics

The `.1R.26` original is an exact byte-prefix of the amended report: 49,728 original bytes plus 4,210 appended bytes; original and current-prefix SHA-256 are both `95cb3976d4c769199ca1cbfd58e02cf52c62e11cd35c162dcf0b62a914ab45fd`. The erratum truthfully records 40 original, `.1R.27` discovery, second `.1R.26R` discovery, final 42, non-behavioural classification, and honest chronology.

`.1R.27` remains BLOCKED in its report and completion metadata. Its IV suite is owned by `.1R.27` commit `cca6b304`; `C..R` leaves it unchanged.

The unrelated Gate6-consumer node passes at `1f8b9c76`, first fails at `302f5aba` (`.1R.17` Gate10), and fails at A and B. Source/contract review classifies it as a stale historical guard over the intentional Gate6-to-Gate10 fail-closed dependency (A/B), not a product/security defect. It predates `.1R.26` and remains future adjudication debt.

`B..R`, `C..R`, and this IV are empty under `src/pcae` and `docs/contracts`; REPRC is byte-identical. Runtime is Observed / observe / unavailable, plugins 0, capabilities 0. No new or production-reachable first-effect call exists; the historical mock/dry call is unchanged. First external effect remains ABSENT. N-16-5/6/7 remain OPEN. N-23-2 remains INFO / DEFERRED.

The fresh suite collects 26 tests covering the 37 required axes and passes 26/26 in 91.23 seconds. No production test was removed/renamed and no skip-to-pass, expected-failure marker, wildcard widening, or loose containment was added.

## Blocking evidence

At R/current, `tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py` fails:

1. `test_14_no_test_weakening_in_the_r26r_diff`: its `B..HEAD` scan sees the repair suite's own added `xfail` literal.
2. `test_15_no_wildcard_or_fnmatch_introduced_in_the_r26r_diff`: the same scan sees the repair suite's own added `fnmatch` literals.

Combined evidence result before stop: **782 passed, 2 failed**. This is `.1R.26R`-attributable verification-evidence debt, not pre-existing and not a production/contract defect. The affected artifact is the `.1R.26R` repair suite. It is self-referential and cannot pass its finalized asserted invariant.

## Adjudication

- `.1R.26R`: **NOT VERIFIED**.
- `.1R.26` evidence blocker: **NOT CLOSED**.
- N-16-4: **IMPLEMENTED — FRESH INDEPENDENT VERIFICATION REQUIRED**.
- `.1R.27`: historically **BLOCKED**.
- `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`.

Required next phase: a separately authorized `.1R.26R` verification-evidence repair/adjudication successor that bounds the no-weakening scan to the immutable substantive repair diff (or an equally restrictive non-self-referential design), followed by a new IV. This IV did not repair it. Canonical IDs are unique, so a later runtime-gate IV must use `.1R.27R` or the exact repository-governed successor, never rewrite/reuse `.1R.27`.

No production, normative-contract, runtime/effect, N-16-5/6/7, Slice C, or execution state changed.

## Successor annotation — `.1R.26R.1R`

The original BLOCKED verdict above remains historical and is not converted
into success. Successor repair phase `.1R.26R.1R` independently reproduced
both named failures at finalized `.1R.26R.1` SHA `7d60eda6` and established
that they were verification-harness self-reference defects only:

- `test_14_no_test_weakening_in_the_r26r_diff` matched quoted expected-failure
  marker text in its own scanner source; no executable expected-failure use
  existed.
- `test_15_no_wildcard_or_fnmatch_introduced_in_the_r26r_diff` matched its own
  explanatory/scanner literals; no live wildcard allowlist or executable
  `fnmatch` broadening existed.

`.1R.26R.1R` replaced raw added-line text matching with syntax-aware executable
structure inspection and added adversarial proof that real violations remain
detected. It also corrected the IV SHA check to bind immutable finalized `V`
as an ancestor rather than equating it with moving `HEAD`. These are harness
repairs only: the two substantive `.1R.26R` guards, production source, and
normative contracts remain byte-identical. The evidence-harness repair remains
pending its own `.1R.26R.1R.1` independent verification.
