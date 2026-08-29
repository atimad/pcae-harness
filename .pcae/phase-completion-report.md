# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.4 Complete — Gate-8 Process Containment (Shell Gate) Coordinator Integration Implementation

Status: completed. **IMPLEMENTED — INDEPENDENT VERIFICATION PENDING — NOT
CLOSED.**

Implements only the RDGO-001 v3.0 §9 **Gate 8 (process containment and live
preflight — the Shell Gate boundary)** production-consumption slice frozen
by `.1R.13.1` §5 / §11 / §12 / §16 / §25. No Gate-9 consumption code, no
Gate-10 adapter/dispatch code. No execution enabled. No normative contract
modified. Runtime remains `not_implemented / Observed / observe /
unavailable`; POL-005 unchanged; real execution UNAVAILABLE.

- **Phase-entry SHA:** `6a9d650f54fb7a5c02652180f0bbcc3a41080198`
  (`.1R.13.3` completion).
- **`.1R.13.1` planning baseline:** the frozen Gate-8 model in §5, §11,
  §12, §16, §25.
- **`.1R.13.3` Gate-7 prerequisite:** Gate 7 was implemented in `.1R.13.2`
  and **independently closed** in `.1R.13.3` — §17 criterion (2) satisfied,
  which unblocks this phase.
- **Production files changed:** exactly one —
  `src/pcae/core/runtime_dispatch_gate8.py` (new).
  `git diff --name-only 6a9d650f HEAD -- src/pcae` → **exactly** that file.
  `git diff 6a9d650f HEAD -- docs/contracts` is **empty**.

Canonical evidence:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_13_4_GATE_8_PROCESS_CONTAINMENT_SHELL_GATE_COORDINATOR_INTEGRATION_IMPLEMENTATION.md`
and
`tests/test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py`
(63 tests, all passing).

## Independent Gate-8 call flow

`run_gate8_process_containment(gate7_result, *, gate5_result, identity,
inputs, authority_current_time, repo_root, effect_plan, descriptor_resolver)`:

1. `is_gate7_result(gate7_result)` (exact-object registry membership) →
   else `gate8_untrusted_gate7_result`; type guards for `identity` /
   `inputs` / `authority_current_time` / `repo_root` / `effect_plan` /
   `descriptor_resolver`.
2. **`gate7_result.decision == "ALLOW"`** (exact string equality) → else
   `gate8_gate7_decision_not_allow` — **before** any Shell Gate evaluation.
   Trusted provenance is not enough; a trusted `Gate7Result(decision="DENY")`
   (what the real Gate-7 coordinator returns under the current posture) is a
   hard stop.
3. `is_gate5_result(gate5_result)` → else `gate8_untrusted_gate5_result`;
   `invocation_id` / `attempt_id` equal across `Gate5Result` / `Gate7Result`
   / `identity` → else `gate8_invocation_binding_mismatch`.
4. `_validate_construction_inputs(inputs)` re-check → `gate8_request_currentness_drift:<f>`.
5. `is_trusted_validated_authority_projection(projection)` +
   `revalidate_validated_authority_projection(projection,
   current_time=authority_current_time)` (re-runs `validate_approval`) →
   else `gate8_stale_validated_authority_projection`.
6. `_expected_subject_scope_binding_digest(identity, inputs) ==
   projection.subject_scope_binding_digest` → else
   `gate8_authority_subject_scope_mismatch`.
7. `descriptor_resolver(inputs) -> ResolvedExecutable` (trusted,
   coordinator-supplied) + shell-metacharacter refusal on the executable
   path and every argv element → `gate8_caller_shell_string_rejected`.
8. Structured-audit-record establishment (`Gate8Result(containment_established=False,
   causing_reason_ids=…)`): effect-plan executable binding; descriptor/config
   drift; runtime-target drift; `os.stat` + SHA-256 executable identity vs
   descriptor pin (a file stat + hash read, **never** an execution); canonical
   repository-scoped cwd; env-allowlist names; child-process / resource /
   time / supervision profile; `network_denied` / `credentials_required`;
   and the **mature 88P `shell_gate.build_shell_gate`** category cross-check
   (pytest/tox/nox/unittest programs refused **before** the call →
   `gate8_shell_gate_preflight_side_effect_refused`, so the classifier runs
   only on a proven-inert input; classifier exception →
   `gate8_shell_gate_internal_error`; hard-block / preflight-required / any
   of 18 mutation-network-secret-environment flags / denied or
   non-allowlisted category or decision → `gate8_shell_gate_category_denied`).
9. Whole body wrapped in `try/except Exception` →
   `(None, ("gate8_internal_error_fail_closed",))`.

## Key properties

- **Sole owner:** `git grep` → `run_gate8_process_containment` /
  `_GATE8_RESULTS` live only in `runtime_dispatch_gate8.py`. `Gate8Result` /
  `is_gate8_result` have **zero** downstream production consumers. Gate 8 is
  the **only** new `Gate7Result` / `is_gate7_result` consumer
  (`hits <= {gate7, gate8}`). It references **no** `Gate6Decision` /
  `is_gate6_decision` / `run_gate6_permission_broker` /
  `run_gate7_runtime_enforcement` / `resolve_runtime_enforcement_posture`
  symbol at all.
- **Trusted provenance ≠ progression:** `is_gate8_result(x) == True` proves
  origin only; a future Gate 9 MUST additionally require
  `x.containment_established is True`. A `containment_established=False`
  `Gate8Result` is a structured audit record, never partial success.
- **No positive production Gate-8 path today:** the real `run_gate5` returns
  nothing (permanent NON-REAL upstream) and a real `Gate7Result` is always
  `DENY` — every real Gate-8 call fails closed at the Gate-7-decision hard
  stop. The positive containment branch is `# pragma: no cover` and is
  exercised only through a clearly-labelled test-boundary provenance
  substitution against a real inert executable (`/bin/echo`); no
  `ValidatedAuthorityProjection`, approval, runtime capability, or positive
  `Gate7Result` is manufactured; the real runtime posture is unchanged.
- **Shell Gate consumed read-only, proven non-effecting:** no
  `_classify_command` / `SGP_CATEGORIES` in the coordinator; a
  `_call_doctor_test_run` spy fails the test if invoked; `build_shell_gate`
  runs only on a metacharacter-free argv whose program is not
  pytest/tox/nox/unittest.
- **Anti-transfer:** direct construction / `object.__new__` / `copy` /
  `deepcopy` / `pickle` / field-reconstruction / subclassing all rejected.
- **Consumes nothing; no Gate-9/10 symbol or effectful import; runtime
  state unchanged** (re-asserted after driving the establishment envelope).
  Idempotent — repeated evaluation returns fresh distinct objects with
  identical `containment_evidence_digest` / `effect_plan_digest` and zero
  durable consumption record repo-wide.

## V-13-1 — extended (INDEPENDENT VERIFICATION PENDING)

Twelve point-in-time production-scope / consumer-inventory guards across the
`.1R.8` (2), `.1R.10` (1), `.1R.11` (1), `.1R.12` (1), `.1R.13` (2),
`.1R.117` (2), `.1R.13.2` (1), `.1R.13.3` (2) suites were **extended** to
include `runtime_dispatch_gate8.py` in each authorised-surface /
authorised-consumer set. Every assertion keeps the **subset** orientation
(`changed - AUTHORIZED == set()` / `x <= {AUTHORIZED}`) — an unauthorised
production-file / `ValidatedAuthorityProjection` consumer / `Gate7Result`
consumer expansion still fails; `gate9_callers == set()` /
`gate9_consumers == set()` / `hpac_consumers == {…}` kept **exact**. Three
former `== {gate7}` equality assertions were converted to `<= {gate7,
gate8}` (with `gate7 in changed` retained where applicable, and an explicit
`runtime_introspection.py not in out`). All are **non-functional**
frozen-diff / consumer-inventory hygiene assertions; every functional
closure is intact.

## Fixed-SHA A/B regression attribution

Immutable baseline `6a9d650f` checked out in an isolated `git worktree`;
`-p no:randomly -n0`.

| | baseline `6a9d650f` | HEAD |
|---|---|---|
| explicit affected-file A/B (10 suites) | 363 passed / 0 failed | 426 passed / 0 failed (363 + 63 new Gate-8 tests) |
| wide `-k` A/B (gate7/gate8/gate5/gate6/runtime_dispatch/shell_gate/runtime_enforcement/permission_broker) | 2784 passed / 13 failed | 2847 passed / 13 failed (2784 + 63) |

- **HEAD-only failing-node set = EMPTY** against the identical 13-node
  baseline failure set (pre-existing permission-broker
  consumer-scope-inventory + B7/HPAC contract-freeze
  contradiction-documentation class; none touch
  `runtime_dispatch_gate8.py`).
- One transient HEAD-only node
  (`test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`, a
  ~13s subprocess-heavy CLI audit-verify test) appeared **once** under
  concurrent-runner contention and does **not** reproduce (5/5 isolated
  pass at HEAD; passes in the uncontended wide re-run) — recorded as
  finding **V-13-4-1** (INFO), not candidate-attributable.

```
CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0
UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS       = 0
```

## Findings

- **V-13-4-1 (INFO, process transparency):** the transient
  `test_audit_verify_cli` flake above. Pre-existing environment/timing
  sensitivity; not candidate-attributable; no repair.
- **V-2 / V-3 / V-4** carried unchanged / non-blocking — **no Gate-8
  impact** (Gate 8 imports nothing from `hpac_lifecycle` / `hpac_verifier`,
  consumes only the trusted upstream objects, reconstructs no disputed
  3-field-vs-7-field `human_authority_binding`).
- **V-13-3-1 / V-13-3-2 / V-13-3-3** carried, **not amplified** — Gate 8
  makes no claim it revalidates PB policy and does not interpret Gate 7's
  `matched_no_go_ids` as capability.
- **O1–O4 / F2–F4 / F7** carried unchanged; **F7 threat model NOT
  broadened** (stated verbatim in the module docstring).
- **Gate 5 still CLOSED, Gate 6 still CLOSED, Gate 7 still CLOSED.**

None blocks the implementation. Gate 8 is **NOT independently verified** and
`.1R.13.4` is **NOT self-closed**.

## Governance

`pcae health` healthy; `pcae check` passed; `pcae status coherence`
coherent; `pcae doctor task-memory` warning-only historical `tasks/DONE.md`
omissions (pre-existing hygiene debt); `pcae runtime inspect` →
`not_implemented / Observed / observe / unavailable`, PB
`execution_unavailable`, posture `non-executing` — **unchanged**.
`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved;
governed PCAE lifecycle only.

## Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.13.5` — Independent Verification of the
Gate-8 Process Containment (Shell Gate) Coordinator Integration.** Frozen by
`.1R.13.1`; **not begun**; requires its own separate explicit human
authorization. `.1R.14` / `.1R.15` (Gate 9) remain frozen, BLOCKED, and NOT
renumbered — they unblock only after `.1R.13.2`–`.1R.13.5` all close
VERIFIED with no blocking findings (`.1R.13.1` §17) and still require their
own explicit human authorization. A dedicated V-2 / V-3 / V-4 (+ V-13-3-1 /
V-13-3-2) contract-clarification phase is an alternative non-blocking next
step, also requiring its own explicit authorization.
