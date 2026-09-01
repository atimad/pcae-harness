# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R.1 — Independent Verification of the N-16-4 Reconciliation IV Evidence-Harness Repair

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R.1
**Type:** governed reconciliation/repair phase — narrow scope-fence widening, no production/contract change
**Status:** REPAIRED — INDEPENDENT VERIFICATION PENDING `.1R.26R.1`. N-16-4 implementation semantics UNCHANGED; N-16-4 remains NOT CLOSED
**Phase-entry SHA:** `9d28f7ef` (`.1R.26` finalized head; `.1R.27`'s own governed finalization commits landed between phase-entry and this phase's task start, attributed to `.1R.27`, not this phase)
**Production source changed:** none (`git diff 9d28f7ef HEAD -- src/pcae` = empty)
**Normative contracts changed:** none (`git diff 9d28f7ef HEAD -- docs/contracts` = empty)
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; `pcae runtime inspect` byte-unchanged; FIRST EXTERNAL EFFECT ABSENT; execution NOT enabled

## Summary

Repairs the one undisclosed `.1R.26`-attributable stale point-in-time scope-fence guard that `.1R.27`'s independent verification discovered and BLOCKED on:

```
tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py::test_runtime_posture_unchanged_and_no_new_first_effect_call_site
```

Independently reproduced by the primary operator in a dedicated `git worktree` at `28b8b2b7`: **PASS**. At `.1R.26` finalized head `9d28f7ef` (pre-repair): **FAIL** — its `.1R.22`-baseline-rooted (`8603fe6a`) exact `src/pcae` current-state file-set assertion was never widened to include `.1R.26`'s authorized single-file addition `runtime_dispatch_gate7.py`. **N-16-4 implementation semantics UNCHANGED — verification-evidence / scope-fence defect only, not a product or contract defect.**

## Repair

Widened the guard's exact-equality set from `{permission_broker_foundation.py, runtime_dispatch_permission.py}` to `{permission_broker_foundation.py, runtime_dispatch_permission.py, runtime_dispatch_gate7.py}` — exact-set equality preserved (no wildcard, no `fnmatch`, no prefix, no subset/superset tolerance); the guard's other two assertions (runtime posture unchanged; no new `adapter.dispatch(` call site) untouched.

## Second discovery (beyond the delegated investigation's original A/B)

A direct primary-operator run of the full Gate-7-referencing suite family (27 test files matched by `git grep -l 'Gate7Result\|is_gate7_result\|runtime_dispatch_gate7' -- tests/`) surfaced **one further same-class stale guard** the delegated investigation's narrower fixed-SHA A/B had missed:

```
tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py::test_53_test_importers_of_gate7_symbols_are_a_known_finite_set
```

`.1R.26`'s own finite `AUTHORIZED_GATE7_TEST_IMPORTERS` allowlist did not admit the later-authorized `.1R.27` independent-verification suite (which legitimately imports Gate-7 symbols for its production-bypass and new-slot-transplant challenges). **Repaired identically** — the allowlist was widened by exactly one entry, with an explicit `.1R.26R` citation comment; it stays exact and finite, no wildcard.

**True attributable stale-guard count for this class: 42** (40 originally disclosed and reconciled in `.1R.26`, plus 2 this phase). No further same-class stale guard was found.

## Unrelated pre-existing finding (disclosed, not repaired)

The same broad sweep also surfaced:

```
tests/test_gate6_permission_broker_production_consumption_integration_independent_verification_3w1r2b1r1_1r13.py::test_no_downstream_production_consumer_of_gate6_symbols
```

failing because `runtime_dispatch_gate10_eligibility.py` references Gate-6 symbols outside that guard's frozen subset allowlist. **Independently confirmed via a dedicated `git worktree` at the unmodified `9d28f7ef` head (zero `.1R.26R` changes applied) that this failure already exists there identically** — it is unrelated to `runtime_dispatch_gate7.py`, unrelated to any `.1R.26` or `.1R.26R` change, and pre-dates both. **NOT `.1R.26`-attributable — out of scope for `.1R.26R`; not repaired.** Disclosed as a carried, unattributed pre-existing finding; no phase ID assigned by this repair.

## Provenance

The original `.1R.26` canonical report/doc is preserved unrewritten; a provenance-preserving erratum was appended to it (additive only, §21) recording the original claim (40 attributable nodes / 0 unexplained regressions), the `.1R.27` discovery, this repair, and the corrected true count (42).

`.1R.27`'s BLOCKED verdict is preserved as historical record, not converted into a successful IV — its own evidence suite (`tests/test_gate7_positive_runtime_enforcement_independent_verification_3w1r2b1r1_1r27.py`) was committed and finalized under `.1R.27`'s own dedicated governed phase (mirroring the `.1R.18` BLOCKED-finalization precedent), entirely before this `.1R.26R` phase's task was opened. This repair's new suite (test 17) verifies that attribution directly via `git log` commit-subject inspection, not mere untracked-ness — it asserts the file's last commit is attributed to `.1R.27`, never to `.1R.26R`.

## New repair suite

`tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py` — **20 adversarial cases, all passing**: exact 3-file authorized set passes; a synthetic 4th unauthorized file fails; a missing authorized file fails; a substituted (wrong) runtime module fails; runtime-posture / no-first-effect assertions preserved; no-wildcard / no-test-weakening / provenance audits pass.

## Test evidence

- Directly-relevant combined suite (`test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py` + `test_runtime_dispatch_1r26r_scope_fence_reconciliation.py` + `test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py` + `test_gate7_positive_runtime_enforcement_independent_verification_3w1r2b1r1_1r27.py` + both `.1R.13.2`/`.1R.13.3` Gate-7 suites): **292 passed, 0 failed**.
- Broader 22-file whole-tests Gate-7-referencing family: **1148 passed, 6 failed, 3 skipped** — 5 are `.1R.26`'s own already-disclosed pre-existing baseline-common failures (identical test node names); 1 is the newly-disclosed unrelated pre-existing Gate-6/Gate-10-eligibility finding above, independently confirmed pre-existing.
- **CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES beyond these 6 disclosed/classified failures = 0. UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.**
- No-test-weakening audit: `git diff 9d28f7ef HEAD -- tests/` contains zero removed `def test_` lines and zero added `@pytest.mark.skip`/`xfail` decorator lines.

## Hard requirements verified

- `git diff --name-only 9d28f7ef HEAD -- src/pcae` → empty.
- `git diff --name-only 9d28f7ef HEAD -- docs/contracts` → empty.
- Runtime `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; unchanged.
- First external effect ABSENT.
- N-16-5 / N-16-6 / N-16-7 remain OPEN, untouched.
- N-23-2 carried (INFO / DEFERRED).

## Verdict

**N-16-4 implementation: UNCHANGED (IMPLEMENTED).** `.1R.26` verification-evidence / scope-fence defect: **REPAIRED — INDEPENDENT VERIFICATION PENDING `.1R.26R.1`.** N-16-4 remains **not** CLOSED — `.1R.27` did not resume or complete its adjudication in this phase.

## `.3` governance incident — preserved

```
DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
```

Only the primary human-authorized operator holds `.1R.26R` lifecycle authority. The initial repair-and-investigation body was performed by a delegated background investigation under the primary operator's direction; the delegated worker did not commit, finalize, or push — all commits and the governed push were performed directly by the primary operator, who also independently re-verified the delegated investigation's key claims and discovered the second stale guard and the unrelated pre-existing finding above. No raw `git commit` / `git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass — governed `pcae` lifecycle only.

## Recommended next phase

Repair phase required first (own explicit human authorization, ID recommended not reserved): `149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1` — **Independent Verification of the N-16-4 Scope-Fence / Verification-Evidence Reconciliation**. RE-DERIVE, do not trust this phase's report or suite: independently reproduce the repaired node's PASS at HEAD; independently confirm no other `.1R.26`-attributable stale guard remains via a fresh broad fixed-SHA A/B; independently verify the erratum's provenance and quantitative truth (42); independently confirm `.1R.27`'s BLOCKED verdict was not altered; independently confirm the unrelated Gate-6/Gate-10-eligibility finding is genuinely unattributable to `.1R.26`/`.1R.26R`. After `.1R.26R.1` closes, recommend a fresh/restarted `.1R.27` IV from this repaired baseline — do not skip directly to N-16-5. Do not begin N-16-5/6/7, Slice C, the first external effect, or execution enablement.

---
*Canonical report artifact. Schema version 1.0.*
