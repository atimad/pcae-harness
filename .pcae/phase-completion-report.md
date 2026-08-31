# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 Complete — N-16-3 Narrow-Eligibility Policy and Contract Implementation

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.22
**Type:** implementation (policy + MAJOR contract evolution)
**Status:** IMPLEMENTED — INDEPENDENT VERIFICATION PENDING (the recommended IV phase)
**Phase-entry SHA:** `8603fe6a` (`.1R.21` finalize head; `origin/main..HEAD = 0` at entry)
**First external effect:** ABSENT — the `src/pcae` diff since `8603fe6a` is exactly the two authorized files and adds no `adapter.dispatch(` line; no `runtime_dispatch_gate10.py`; no real adapter; no subprocess / socket / provider / credential path
**Execution:** not enabled — runtime `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; `RuntimeRegistry` empty; `pcae runtime inspect` byte-identical at entry and finalization; POL-005 hard-DENYs every ordinary non-simulation request (re-verified live)
**Production source changed:** `src/pcae/core/permission_broker_foundation.py` (POL-005 §12a one-profile carve-out + POL-013 + the two derived fields + the predicate conjunction + the classification-consistency / complete-without-marker-forgery checks + `POLICY_IDS_CANONICAL` → POL-001..013) and `src/pcae/core/runtime_dispatch_permission.py` (N-16-6 supply-chain admission **interface** + fail-closed **non-admitting** production stub; the trusted-builder classification derivation; the test-boundary `_supply_chain_admission_resolver` kwarg) — exactly the `.1R.21` §39 anticipated set. `policy.py` untouched (it enumerates no POL IDs).
**Normative contracts changed:** `PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` — **PBRD-001 v2.1 → v3.0 (MAJOR)** with new §12a and §16 inline explicit migration semantics; new `PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md` — **PBNDE-001 v1.0**; `PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` — **PBPA-001 v1.0 → v1.1 (additive)**; `V0_2_EXECUTION_READINESS_NO_GO_GATES.md` — NG-025 canonical-statement annotation. The mechanical `PBRD-001 v2.1` → `v3.0` "Related contracts" edits in RDGO-001 / RIHAC-001 and their siblings are **deferred to a dedicated contract-normalization pass** (the `.1R.15.4` precedent; PBRD-001 v3.0 §16 point 5 records this normatively) — attempting them in `.1R.22` cascaded 51 failures across the RIHAC/HPAC contract-freeze suites and is out of scope.

## Versioning adjudication

`.1R.21` §31 / §34 planned the PBRD change as **v2.2 (MINOR)**. On `.1R.22`
primary-source review this was found to conflict with **PBRD-001 v2.1 §16**,
which lists *"weakening POL-005 eligibility"* among the changes that *"require
a new MAJOR plus explicit migration and independent verification."* §12a is
exactly that clause. The phase was **BLOCKED at primary-source review** (no
repository mutation; no task opened at that point) and the primary
human-authorized operator adjudicated: **carry N-16-3 as PBRD-001 v3.0 —
MAJOR**, with inline explicit migration semantics (§16) and independent
verification in `.1R.23`; do not implement the v2.2 MINOR path. Repository
convention (RDGO-001 v2 → v3.0; PBRD-001 v1.1 → v2.0) carries a contract MAJOR
**inline** in its implementing/freeze phase with the migration statement in
the contract's own versioning section, so `.1R.22` authored the migration
artifact inline and did **not** re-STOP. `.1R.21` §38's NG-025 annotation
target (`RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`) is a planning-document
location error — NG-025 is owned by `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`,
where the annotation was applied; no `RE-NOGO-*` entry was created.

## Dispositions

| Item | Result |
|---|---|
| N-16-3 NARROW-ELIGIBILITY POLICY AND CONTRACT | IMPLEMENTED — IV PENDING (`.1R.23`) |
| `RUNTIME_DISPATCH_LOCAL_CLI_V1` (trusted-derived profile) | IMPLEMENTED — PRODUCTIONALLY UNSATISFIABLE — IV PENDING |
| `POL-013` (Narrow Local-CLI Dispatch Eligibility) | IMPLEMENTED — NEVER EMITS ALLOW OR HUMAN_REVIEW — IV PENDING |
| POL-005 canonical-statement v2 amendment (ID retained) | IMPLEMENTED — IV PENDING |
| PBRD-001 v2.1 → v3.0 (MAJOR) + inline explicit migration | IMPLEMENTED — IV MANDATED (`.1R.23`) |
| PBNDE-001 v1.0 (new policy contract) | FROZEN — IV PENDING |
| PBPA-001 v1.0 → v1.1 (POL-013 applicability row) | FROZEN — IV PENDING |
| NG-025 canonical-statement annotation | APPLIED (correct owner) |
| N-16-6 supply-chain admission interface + fail-closed stub | IMPLEMENTED (non-admitting; profile unsatisfiable in production) |
| FIRST EXTERNAL EFFECT | ABSENT |
| N-16-4 / N-16-5 / N-16-6 (store) / N-16-7 | OPEN — not begun |
| Slice C / Slice D | NO PHASE ID |
| DELEGATED `.3` FINALIZATION / COMMIT / PUSH | UNAUTHORIZED (preserved) |

## Frozen Option C + D architecture, implemented unchanged

A trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile lies **outside**
POL-005's categorical hard-block match domain — POL-005's `evaluate` gains one
`_not_triggered` carve-out (`_is_trusted_narrow_local_cli_dispatch_v1`, which
reads **only** the derived marker + the construction seal); the body of the
unconditional `DENY` (NG-025 / INV-001 / COMP-002) is byte-unchanged. A
dedicated conjunctive **`POL-013`** (`NarrowLocalCliDispatchEligibilityRule`,
`execution_class=adapter`-scoped, trigger narrowed inside `evaluate()` to
`action_type == runtime_dispatch` + `simulation_only is False`) checks the
full P1–P21 predicate conjunction: all predicates hold → *not-triggered*; any
missing / malformed / untrusted / broader predicate → `DENY`
(`narrow_local_cli_dispatch_profile_incomplete`) which **reinforces** POL-005
(both DENY). **POL-013 has exactly the `_not_triggered` and `DECISION_DENY`
return shapes — statically verified it never returns `ALLOW` or
`HUMAN_REVIEW`.** `_compose`'s `DENY > HUMAN_REVIEW > ALLOW` precedence is
byte-unchanged; no specificity tier / weight / override. Human approval is one
predicate among the fourteen checked, necessary and never sufficient, and it
does not touch POL-005's match logic (`if human_approved: ignore POL-005` and
`trusted principal → ALLOW` remain rejected and not expressible in the code).

## Trusted-derived classification and digest binding

`profile_classification` is derived **last** by
`build_runtime_dispatch_permission_broker_request` from the fully bound
provisional request; it is never caller input.
`_valid_runtime_dispatch_request` recomputes it and fails closed on any
inconsistency — a marker set without a complete profile **and** a complete
profile that lacks the trusted marker (a post-construction admission-field
forgery) are both structural `DENY` before POL-005 / POL-013 evaluate. The
N-16-6 admission sub-fields are inside `canonical_runtime_dispatch_projection`
→ the `idempotency_key` canonical-content digest (mutation → `build_…`
key-match failure). `_expected_subject_scope_binding_digest` is deliberately
**not** extended (admission is a PB-policy predicate, not part of the
human-authority scope binding) — no Gate-5 projection test changes.

## Production profile is unsatisfiable

`_PRODUCTION_SUPPLY_CHAIN_ADMISSION_RESOLVER` (`_NonAdmittingSupplyChainAdmissionResolver`)
admits **nothing** for any adapter — `admitted=False`,
`admission_class="unadmitted"`. `_resolve_supply_chain_admission` fail-closes
a broken / exception-raising / malformed resolver to `unadmitted`. Therefore
`P_supply_chain_admission` always fails, `profile_classification == ""` on
**every** production path, POL-005 keeps its hard-DENY match, and POL-013
DENYs. **No production PB `ALLOW` for the first-effect local-CLI profile is
reachable; Gate 6 itself remains non-positive.** N-16-5 independently keeps it
unsatisfiable (`validate_approval` NON_REAL hard-stop; there is no test or
production path to a trusted `ValidatedAuthorityProjection`).

## Test evidence

- New defensive suite `tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py`
  — **43 passed** (the `.1R.21` §37 25 cases + cases 26–33 + the phase-prompt
  §50 static-never-ALLOW AST scan + §53/§54 seal / reconstruction / provenance
  challenges + the §63 contract-production equivalence map; every case asserts
  no external effect — runtime posture unchanged, the `.1R.22` `src/pcae`
  diff is exactly the two authorized files and adds no `adapter.dispatch(`
  line).
- **Scope-fence + meta-guard reconciliation:** ~20 assertions across `.1R.8` /
  `.1R.11` / `.1R.15.2` / `.1R.15.5` / `.1R.17` / `.1R.17R` / `.1R.17R.1` /
  `.1R.18` / `.1R.19` / `.1R.19R` / `.1R.19R.1` / `.1R.20` plus the PBPC /
  PBPA / composition-hardening count assertions — subset checks over the
  exact authorized filename set, no wildcard; Gate 5 / 7 / 8 / 9 + Slice-A
  freezes and every adversarial companion preserved; the two `.1R.19R` /
  `.1R.19R.1` `test_meta_guards_byte_unchanged_since_r20_head` meta-guards
  keep `.1R.15.3` byte-frozen and assert `.1R.18` is not weakened (`"*"`
  count, `fnmatch` count, `def test_` count unchanged / non-decreasing vs
  `e05f0ea3`). **No reconciliation renamed a test function or removed an
  assertion decorator** (`.1R.19R.1::test_no_test_weakening_in_the_r19r_diff`
  passes unmodified).
- **Fixed-SHA A/B** vs the immutable pre-`.1R.22` baseline `8603fe6a`
  (deterministic, `-p no:randomly`, no xdist): *(numbers finalized in the
  completion metadata)*. **CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING
  NODES = 0; UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.** Four
  pre-existing failures reproduce identically with `.1R.22`'s changes stashed:
  `.1R.13::test_no_downstream_production_consumer_of_gate6_symbols` (Slice-A
  `.1R.17` added the `runtime_dispatch_gate10_eligibility.py` consumer),
  `3w1::test_only_content_bound_projection_registry_is_added_to_authority_module`
  (`_GATE6_DECISIONS` is a `.1R.12` module-level set),
  `.148f::test_permission_broker_consumer_scope_inventory` (a `.148f`
  consumer-inventory guard already listing later-phase consumers),
  `.148g2::test_actual_git_push_dispatch_site_in_core_agent_remains_unwired`
  (unrelated to PB policy).

## New findings

- **N-16-3-1** — `.1R.21`'s versioning adjudication (PBRD change = v2.2 MINOR)
  conflicts with PBRD-001 v2.1 §16 ("weakening POL-005 eligibility … requires
  a new MAJOR"). Corrected to PBRD-001 v3.0 (MAJOR) with inline explicit
  migration + `.1R.23` IV (human-authorized).
- **N-16-3-2** — `.1R.21` §38 lists the NG-025 canonical-statement annotation
  against `RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`, which contains no NG-025.
  Corrected to `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`.

## Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.23` — Independent Verification of the N-16-3
Narrow-Eligibility Policy. Requires its own explicit human authorization. Not
begun. Do not proceed to N-16-4..7; do not implement Slice C; do not call the
first external effect; do not enable execution.

Canonical artifact: `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_22_N_16_3_NARROW_ELIGIBILITY_POLICY_AND_CONTRACT_IMPLEMENTATION.md`.
