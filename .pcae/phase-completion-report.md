# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.5 Complete — Independent Verification of the Gate-8 Process Containment (Shell Gate) Coordinator Integration

Status: completed. **VERIFIED WITH NON-BLOCKING FINDINGS — GATE-8 — CLOSED**
at the RDGO-001 v3.0 §9 process-containment / Shell-Gate consumption
boundary for `runtime_dispatch`.

Independent verification (RE-DERIVE, DO NOT TRUST) of the `.1R.13.4` Gate-8
Process Containment (Shell Gate) coordinator integration
(`run_gate8_process_containment`), against RDGO-001 v3.0 §9 / §1 row 8 / §10
/ §13 / §15 / §19, the `.1R.13.1` planning document §5 / §11 / §12 / §16 /
§17 / §25, the mature 88P `shell_gate` classifier **source**, PBRD-001 v2.0
§6 / §14, RPAC-001 v1.0, POL-005, and the independently-verified Gate-5 /
Gate-6 / Gate-7 boundaries — **not** from the `.1R.13.4` report, its
implementation document, its 63 tests, function/type names,
result-registry membership, or aggregate counts.

- **Verification-entry SHA:** `72898361` (`.1R.13.4` completion).
- **Immutable pre-`.1R.13.4` baseline:** `6a9d650f54fb7a5c02652180f0bbcc3a41080198`
  (`.1R.13.3` completion).
- **`.1R.13.4` implementation range (independently reconstructed):**
  `cda5c2fa..72898361`; the **only functional commit** is `df00c43c`
  (`src/pcae/core/runtime_dispatch_gate8.py` new + the canonical document +
  the 63-test suite + the twelve V-13-1 guard extensions). The phase
  prompt's reported list omits the two finalization-staging commits
  `b77bf4d2` / `72898361`.
- **No defect repair. No `src/` change** — `git diff --name-only 6a9d650f
  HEAD -- src/pcae` is **exactly** `src/pcae/core/runtime_dispatch_gate8.py`,
  unchanged from `.1R.13.4`. **No Gate-9/10 code. No execution enabled.**
- **`git diff 6a9d650f HEAD -- docs/contracts` is empty.**

Canonical evidence:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_13_5_INDEPENDENT_VERIFICATION_OF_GATE_8_PROCESS_CONTAINMENT_SHELL_GATE_COORDINATOR_INTEGRATION.md`
and
`tests/test_gate8_process_containment_coordinator_independent_verification_3w1r2b1r1_1r13_5.py`
(**120 fresh independent tests**, all passing — own synthetic provenance
substitution, own resolver / effect-plan builders).

## Independently confirmed

- **Sole owner:** `git grep -E "run_gate8_process_containment|_GATE8_RESULTS"
  -- src/pcae` → exactly `runtime_dispatch_gate8.py`; `Gate8Result` /
  `is_gate8_result` have **zero** downstream production consumers; Gate 8 is
  the **only** new `Gate7Result` consumer (`git grep` → `{gate7, gate8}`).
- **Gate-7 provenance (`is_gate7_result`, exact object) AND
  `decision == "ALLOW"` (exact string equality) are BOTH required** —
  freshly tested against `None`, `object.__new__` with forged slots,
  bare-`ALLOW`, `copy` / `deepcopy` (raise), `pickle` (raises); a trusted
  `Gate7Result(decision="DENY")` — driven through the **real**
  `run_gate7_runtime_enforcement` negative branch — is rejected
  (`gate8_gate7_decision_not_allow`) at flow step 3 with `build_shell_gate`
  call-count **0** (spied), before any Shell Gate / drift / containment
  work. No permissive normalization.
- **Current production reachability = NO:** `full_chain(simulation_only=False)`
  → `projection is None` (permanent NON-REAL hard stop); no `Gate5Result` →
  no `Gate6Decision` → no `Gate7Result`; a real `Gate7Result` is always
  `DENY`; positive containment branch is `pragma: no cover`.
- **Gate-5 provenance + projection re-trust + `revalidate_validated_authority_projection`**
  (re-runs `validate_approval`) at Gate 8's own point of use; the revalidate
  receives the Gate-8 `authority_current_time`; trust runs before revalidate.
- **Invocation lineage** (`invocation_id` across Gate5/Gate7/identity,
  `attempt_id` across Gate7/identity) and **`subject_scope_binding_digest`
  recompute** via the shared `_expected_subject_scope_binding_digest`.
- **Executable identity** by `os.stat` regular-file gate + streamed SHA-256
  **content** hash vs the descriptor pin — same path + changed bytes →
  `gate8_executable_identity_mismatch`; a symlink to different-content
  target → same (proves content hash, not path equality); **never** an
  execution.
- **Shell-metacharacter refusal** of the executable path and every argv
  token (12-case sweep); non-string token refused.
- **Canonical 88P `shell_gate.build_shell_gate` consumed read-only** — no
  `_classify_command` / `SGP_CATEGORIES` in the coordinator; `shell_gate.py`
  byte-unchanged. `_call_doctor_test_run` **proven structurally unreachable
  from any Gate-8 input** (fires only for a `pytest` program / `-m pytest`,
  all refused on the executable basename **or any argv token** before
  `build_shell_gate` — 5-case parametric proof, call-count 0; AST confirms
  it is `shell_gate.py`'s only `subprocess.run` site). With `subprocess.run`
  / `.Popen` / `_call_doctor_test_run` all patched to fail, Gate-8 runs
  spawn nothing.
- **`Gate8Result` anti-transfer** — identity-only `==` / `hash`,
  `__reduce__` raises, `__init_subclass__` raises, `object.__new__` and
  field-reconstructed lookalikes rejected. **`is_gate8_result` is
  membership-only** (AST: single `return`, no `if`, no
  `containment_established` in the return expression) — provenance, never
  containment success. A `Gate8Result(containment_established=False)` is a
  registry member but an explicit non-progression audit record.
- **Gate 8 consumes nothing** — `consumption.json` count invariant; no
  lifecycle / Gate-9 call (AST); no Gate-9/10 symbol or effectful import;
  runtime `Observed / observe / unavailable` after every path.
- **§16 Gate-8 → Gate-9 handoff contract independently re-reviewed**
  (satisfies `.1R.13.1` §17 criterion 8) — `Gate8Result` carries exactly
  the frozen §16.1 fields; no consumer / serialization / persisted handoff;
  the six §16.2 invariants hold or are correctly deferred to Gate 9's
  in-boundary revalidation.
- **V-13-1 — REMAINS CLOSED; GATE-8 EXTENSION VERIFIED** — all twelve guard
  extensions inspected guard-by-guard; subset orientation kept
  (`- AUTHORIZED == set()` / `<= {gate7, gate8}`), `gate9` / `hpac` asserts
  kept exact-equality, two `.1R.13.2`/`.1R.13.3` guards converted `==` →
  subset; orientation actively challenged with a synthetic
  `{gate7, gate8, runtime_adapter}` set (every guard rejects it); no
  functional earlier-phase closure weakened.
- **Gate-5 / Gate-6 / Gate-7 regressions re-confirmed CLOSED** —
  `runtime_dispatch_gate5.py` / `runtime_dispatch_gate7.py` /
  `runtime_dispatch_permission.py` / `permission_broker_foundation.py`
  (POL-005) byte-unchanged since `6a9d650f`.
- **Contract identity** — RDGO-001 / PBRD-001 / RPAC-001 / RIHAC-001 /
  RIASC-001 / HPAC-001 / PBPA-001 / POL-005 / `shell_gate.py` /
  `runtime_introspection.py` / `runtime_enforcement_safety_authorization.py`
  byte-unchanged.

## Fixed-SHA A/B regression evidence

- **Baseline** `6a9d650f` (isolated `git worktree`, since removed) vs
  **candidate** `72898361`; `-p no:randomly -n0`.
- Two Gate-8 suites: **183 passed, 0 failed** (120 new + 63 `.1R.13.4`).
- 8 affected earlier-phase suites: **327 passed / 1 failed at BOTH SHAs** —
  the identical node
  `test_gate6_permission_broker_production_consumption_3w1r2b1r1_1r12.py::test_gate5_results_registry_stays_empty_on_every_reject`,
  a **pre-existing cross-file `_GATE6_DECISIONS` pollution flake** that
  passes in isolation and reproduces byte-identically at `6a9d650f`
  (finding **V-13-5-3**).
- `tests/test_shell_gate.py` 118/118 (V-13-4-1 not reproduced).
- Wide `-k "gate8 or shell_gate or process_containment"` 848/848 at HEAD.
- Wide gate-chain `-k` 2967 passed / 13 pre-existing fail (HPAC / PB-freeze
  / contract-wording repo baseline; 5 sampled reproduce identically at
  `6a9d650f`).

```
CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0
UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS       = 0
```

## Non-blocking findings

- **V-13-5-1 (LOW):** the frozen `.1R.13.1` §11.2 / §25 `gate8_cwd_drift` /
  `gate8_environment_allowlist_drift` / `gate8_transport_drift` rows are
  implemented as a repository-scope check
  (`gate8_cwd_outside_repository_scope`), a well-formedness check
  (`gate8_environment_not_allowlisted`), and **no** check respectively —
  there is **no bound cwd / env reference** in
  `RuntimeDispatchRequestConstructionInput` to diff against (the frozen §12.5
  `containment_profile` parameter was dropped for the coordinator-assembled
  `effect_plan`), and the frozen plan's own stated mechanism (the
  subject/scope digest) does not cover cwd/env either — the inconsistency
  originates in the frozen `.1R.13.1` plan. `transport_type` is a fixed
  `local_cli` constant and provider/backend drift is covered by
  `gate8_descriptor_config_drift`. **Mitigated:** `effect_plan` is
  trusted-coordinator-assembled (frozen §11.1 item 5); cwd / env / the full
  containment profile **are** bound into `containment_evidence_digest`,
  which frozen §16.2 invariant 3 requires the future Gate 9 to recompute and
  read-back-verify — so a replayed `Gate7Result(ALLOW)` + a changed cwd/env
  is caught at the Gate-8 → Gate-9 boundary; the executable identity/hash,
  argv, descriptor digests, runtime-target, effect-plan-executable,
  `network_denied`, `credentials_required` and repository-scope cwd rows
  **are** independently enforced; Gate 8 is structurally unreachable in
  production. **Not** a GATE-8 EFFECT-PLAN BINDING or DECISION-SEMANTICS
  DEFECT. The `.1R.13.4` §5 table silently substitutes the reason ids and
  drops the transport row without flagging the deviation (documentation
  transparency gap, folded here); the `.1R.13.4` tests are honestly named.
  Recommendation: the separately-authorized V-2 / V-3 / V-4
  contract-clarification phase should add `cwd_ref` / `env_allowlist_ref`
  to the request model **or** reword §11.2 / §25 rows 8–9 and strike the
  transport row.
- **V-13-5-2 (INFO):** `Gate5Result` carries no `attempt_id` by its frozen
  `.1R.10` model; Gate 8's `attempt_id` binding is transitive via Gate 7,
  not direct. No exploitable gap; the future Gate-9 handoff spec should say
  so.
- **V-13-5-3 (INFO):** the pre-existing `_GATE6_DECISIONS` cross-file
  pollution flake above — not candidate-attributable; recommend an autouse
  registry-clear fixture in a future hygiene pass.
- **Carried, re-checked:** V-13-4-1 (INFO) not reproduced;
  V-13-3-1 / V-13-3-2 (LOW) confirmed **not amplified**; V-2 / V-3 / V-4
  (LOW) no Gate-8 impact; O1–O4 / F2–F4 / F7 unchanged, F7 threat model
  **NOT broadened** (stated verbatim in `runtime_dispatch_gate8.py`).

## Verdict

> **VERIFIED WITH NON-BLOCKING FINDINGS — GATE-8 PROCESS CONTAINMENT (SHELL
> GATE) COORDINATOR INTEGRATION COMPLETE.** GATE-8 — CLOSED. No STOP
> condition met: no Shell Gate path can cause an effect; no executable/
> effect substitution that matters remains possible; no trusted negative
> result can progress.

## Gate-9 unblocking

All eight `.1R.13.1` §17 criteria are met on promotion of this report.

> **`.1R.14` PRECONDITIONS SATISFIED — STILL REQUIRES SEPARATE EXPLICIT
> HUMAN AUTHORIZATION.** `.1R.14` (Gate-9 Atomic Authority Consumption
> Coordinator Integration Implementation) and `.1R.15` (its verification)
> remain **frozen, BLOCKED pending their own explicit human authorization,
> and NOT renumbered**. This phase begins neither and grants no
> authorization. A dedicated V-2 / V-3 / V-4 / V-13-3-1 / V-13-3-2 /
> **V-13-5-1** contract-clarification phase is an alternative non-blocking
> next step, also requiring its own explicit authorization.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.
Governed PCAE lifecycle only. Runtime remains `not_implemented / Observed /
observe / unavailable`; POL-005 unchanged; real execution UNAVAILABLE.
