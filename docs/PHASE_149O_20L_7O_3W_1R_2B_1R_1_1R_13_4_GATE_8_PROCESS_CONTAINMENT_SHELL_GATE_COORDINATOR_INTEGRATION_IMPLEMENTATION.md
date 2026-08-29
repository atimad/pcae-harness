# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.4 — Gate-8 Process Containment (Shell Gate) Coordinator Integration Implementation

Status: **IMPLEMENTED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**

Implements only the RDGO-001 v3.0 §9 **Gate 8 (process containment and live
preflight — the Shell Gate boundary)** production-consumption slice frozen
by `149O.20L.7O.3W.1R.2B.1R.1.1R.13.1` (the authoritative plan, §5 / §11 /
§12 / §16 / §25). No Gate-9 consumption code, no Gate-10 adapter/dispatch
code. No execution enabled. No normative contract modified. Runtime remains
`not_implemented / Observed / observe / unavailable`; POL-005 unchanged;
real execution UNAVAILABLE.

- **Phase-entry SHA:** `6a9d650f54fb7a5c02652180f0bbcc3a41080198`
  (`.1R.13.3` completion — "reconcile governed push state").
- **`.1R.13.1` planning baseline:** the frozen Gate-8 model in §5, §11,
  §12, §16, §25, plus the §22 V-13-1 disposition and the §27 frozen phase
  IDs.
- **`.1R.13.3` Gate-7 prerequisite:** Gate 7 was implemented in `.1R.13.2`
  and **independently closed** in `.1R.13.3` (VERIFIED WITH NON-BLOCKING
  FINDINGS — GATE-7 CLOSED at the RDGO-001 §8 boundary; V-13-1 CLOSED). The
  §17 criterion (2) "Gate-7 independently verified" is satisfied, which
  unblocks this phase.
- **Production files changed:** exactly one —
  `src/pcae/core/runtime_dispatch_gate8.py` (new).

---

## 1. `.1R.13.1` Gate-8 mapping

| `.1R.13.1` element | Where implemented |
|---|---|
| §5.3 one-sentence freeze — process-containment boundary: re-resolve drift, refuse caller shell strings, construct + attest one bounded launch environment; no dispatch, no consumption | `run_gate8_process_containment` |
| §11.1 Gate-7 → Gate-8 handoff — trusted `Gate7Result` + `decision == "ALLOW"` + identity/inputs + re-resolved `Gate5Result` + a coordinator-assembled canonical effect plan | coordinator input: `gate7_result` (registry-provenanced) + `decision == "ALLOW"` exact-eq + `gate5_result` (registry-provenanced, re-trusted) + `identity` / `inputs` (14 facts) + `effect_plan` (argv vector, bound to the resolved executable) + `descriptor_resolver` (trusted, coordinator-supplied) |
| §11.2 anti-substitution binding matrix | steps 6, 8a–8h of the coordinator (subject/scope digest recompute; executable identity; descriptor/config drift; runtime-target drift; cwd; env allowlist; caller shell string) |
| §12.1 owner = new `runtime_dispatch_gate8.py` coordinator; **consumes** the mature 88P `shell_gate.py` classifier, does not replace/extend it | this module; `from pcae.core.shell_gate import build_shell_gate` (function-local, read-only) |
| §12.4 wall `Shell Gate validation != subprocess execution` | AST-guarded no-effect import set; `build_shell_gate` invoked only on a proven-inert input (pytest/tox/nox/unittest programs refused first) |
| §12.5 input shape | `run_gate8_process_containment(gate7_result, *, gate5_result, identity, inputs, authority_current_time, repo_root, effect_plan, descriptor_resolver)` |
| §12.6 output model — ephemeral, identity-only, non-serializable, registry-provenanced `Gate8Result` (`containment_established` bool + `containment_evidence_digest`); not an execution token | `Gate8Result` + `_GATE8_RESULTS` + `is_gate8_result` |
| §12.7 provenance — `is_gate8_result` = exact-object membership | implemented; provenance-only (does not imply `containment_established`) |
| §12.8 no-effect guarantee | no `subprocess`/`socket`/`spawn`/`exec`/`pty`/provider SDK/HTTP import; executable-identity check is `os.stat` + hash read |
| §12.9 structurally unreachable in production today | Gate 7 always returns `Gate7Result(decision="DENY")` (`.1R.13.2` / `.1R.13.3`); the real `run_gate5` returns nothing — every real Gate-8 call fails closed at the `gate8_untrusted_gate7_result` / `gate8_gate7_decision_not_allow` hard stop |
| §12.10 stale-state / failure / idempotency | steps 4–8; fail-closed reason ids; `Gate8Result(containment_established=False, …)` as a structured audit record; Gate 8 consumes nothing and is idempotently repeatable |
| §16 Gate-8 → Gate-9 handoff (contract frozen; Gate 9 NOT implemented) | `Gate8Result` carries `invocation_id` / `attempt_id` / `request_id` / `gate7_result_digest` / `effect_plan_digest` / `containment_evidence_digest` / `live_preflight_digest` — exactly what a future Gate 9 re-derives; no consumer, no serialization, no persisted handoff created |
| §22 V-13-1 | the phase-aware scope guards extended to include `runtime_dispatch_gate8.py` (§8 below) |
| §25 defensive validation matrix (20 cases) | `tests/test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py` (63 focused tests) |

---

## 2. Gate-8 sole ownership

`run_gate8_process_containment` is the **single** production owner of the
RDGO-001 §9 Gate-8 process-containment / Shell-Gate consumption boundary for
`runtime_dispatch`. There is no parallel Gate-8 path.

Inventory of production Shell Gate callers, classified:

| Caller | Class | Relationship to Gate 8 |
|---|---|---|
| `src/pcae/commands/shell_gate.py` (`pcae shell-gate` CLI) | existing unrelated use — advises on arbitrary proposed shell commands | unchanged; independent consumer of `build_shell_gate` |
| `src/pcae/core/gate_dry_run*.py` / `permission_broker*.py` | advisory / design-only classification use | unchanged |
| `src/pcae/core/runtime_dispatch_gate8.py` (**new**) | **the canonical Gate-8 consumer** — one read-only `build_shell_gate` call site for the executable/argv category cross-check | authorized `.1R.13.4` |
| any other | — | none; a consumer-inventory scan (`git grep`) confirms no unexpected parallel production path |

No bypass route is created: `build_shell_gate` is called only after the
executable is resolved through the trusted `descriptor_resolver`, only on a
metacharacter-free argv vector, and only when the program is proven not to
drive Shell Gate's `pcae doctor test-run` lock probe.

`runtime_dispatch_gate8` was built new because there is **no production
process-containment mechanism** — `.1R.13.1` §3.4 / §5 independently
established this. `shell_gate.py` is a read-only 24-category / 26-decision
classifier that never executes classified command text; the new coordinator
owns containment establishment + drift re-resolution + the `Gate8Result`,
and consumes the classifier unchanged.

---

## 3. Gate7Result provenance handling — and trusted-provenance is not enough

Gate 8 consumes a `Gate7Result` **only** through
`runtime_dispatch_gate7.is_gate7_result` — exact-object membership in that
module's process-local `_GATE7_RESULTS` registry, the exact object a prior
successful Gate-7 runtime-enforcement evaluation returned. Never
`isinstance`, fields, equality, a copied object, a reconstructed object, a
serialized form, or a caller-supplied `decision="ALLOW"` object.

Structurally enforced by the existing `.1R.13.2` code (`Gate7Result.__reduce__`
raises; `is_gate7_result` is exact-object registry membership;
`__init_subclass__` raises) — Gate 8 calls the predicate and fails closed
(`gate8_untrusted_gate7_result`) for anything it does not vouch for.

**Trusted provenance is NOT enough.** `is_gate7_result(x) == True` proves
only "produced by Gate 7". Gate 8 **additionally** requires
`gate7_result.decision == "ALLOW"` by exact string equality. A trusted
**negative** `Gate7Result(decision="DENY")` — which is what the real Gate-7
coordinator returns under the current runtime posture — is rejected with
`gate8_gate7_decision_not_allow` **before** any Shell Gate evaluation, drift
re-resolution, or containment establishment. No code path in this module
converts a non-`ALLOW` `Gate7Result` into a positive containment result.

```
caller-created / copied / reconstructed / serialized Gate7Result lookalike
    != trusted Gate-7 output          →  gate8_untrusted_gate7_result
trusted Gate7Result(decision="DENY")
    → rejected before Shell Gate      →  gate8_gate7_decision_not_allow
```

Tests: `test_none_gate7_result_fails_closed`,
`test_caller_constructed_gate7_result_rejected`,
`test_copied_reconstructed_serialized_gate7_result_rejected`,
`test_real_negative_gate7_result_is_not_trusted_by_shape`,
`test_trusted_gate7_deny_rejected_before_shell_gate`,
`test_unknown_gate7_decision_value_fails_closed`,
`test_is_gate8_result_means_provenance_not_containment`.

---

## 4. No current positive production Gate-8 path

**Is a legitimate positive production Gate-8 success currently possible? NO.**
Two independent reasons, either sufficient:

1. The real Gate-6 → Gate-7 chain never yields a positive `Gate7Result`:
   `run_gate5` never returns a `Gate5Result` on any obtainable path
   (permanent NON-REAL upstream), so `run_gate6_permission_broker` never
   returns a `Gate6Decision`, so `run_gate7_runtime_enforcement` is never
   even called with a trusted decision — and when driven through a labelled
   provenance substitution it still returns `Gate7Result(decision="DENY")`
   under the current posture (`.1R.13.2` / `.1R.13.3`).
2. Gate 8's own first checks after provenance are
   `is_gate7_result` + `decision == "ALLOW"`; a DENY fails the second by
   exact equality.

Every real Gate-8 call therefore fails closed at the
`gate8_untrusted_gate7_result` / `gate8_gate7_decision_not_allow` hard stop.
The positive containment-establishment branch
(`containment_established=True`) is marked
`# pragma: no cover - production-unreachable positive branch`.

**No fabricated capability.** No production code path exposes a test-only
seam. The suite exercises the production hard stop directly, and reaches the
Gate-8 establishment envelope only via a **test-boundary substitution** of
the provenance predicates (`monkeypatch` on `is_gate7_result` /
`is_gate5_result` and, where the freshness re-resolution is not under test,
the projection-trust predicates in the `runtime_dispatch_gate8` namespace) —
the same accepted boundary the `.1R.13` / `.1R.13.2` / `.1R.13.3` suites
use. No `ValidatedAuthorityProjection`, approval, runtime capability, or
positive `Gate7Result` is manufactured; the real runtime posture is
unchanged in every test.

---

## 5. Gate7 → Gate8 handoff (RDGO-001 §9 / `.1R.13.1` §11)

| # | `.1R.13.1` §11.1 item | Trusted source at Gate 8 | Gate-8 use |
|---|---|---|---|
| 1 | trusted `Gate7Result` | `is_gate7_result` (exact-object membership) | provenance gate; drives `gate7_result_digest` |
| 2 | `Gate7Result.decision == "ALLOW"` (exact eq) | `gate7_result.decision` | hard stop on any non-`ALLOW` |
| 3 | `RuntimeDispatchIdentity` + `RuntimeDispatchRequestConstructionInput` | exact type guards + `_validate_construction_inputs` | descriptor / repository / prompt / adapter-config re-resolution; drives `evaluated`-input binding |
| 4 | re-resolved `Gate5Result` reference | `is_gate5_result` + `is_trusted_validated_authority_projection` + `revalidate_validated_authority_projection` | the §9 "recheck … current policy/RE decision" + invocation binding |
| 5 | canonical **effect plan** — exact executable (descriptor-pinned, resolved by Gate 8 itself), argv vector, cwd, env allowlist | `descriptor_resolver(inputs) -> ResolvedExecutable` + `Gate8EffectPlan` bound to `resolved.path` | never a caller shell string; argv vector only |

**Anti-substitution binding (§11.2):**

| Substitution | Reject reason | containment_established |
|---|---|---|
| `Gate7Result` A + invocation B (`invocation_id` / `attempt_id`) | `gate8_invocation_binding_mismatch` | n/a — `(None, reasons)` |
| effect plan B (different executable) | `gate8_effect_plan_binding_mismatch` | `False` |
| changed `runtime_target_id` since Gate 7 | `gate8_runtime_target_drift` | `False` |
| changed executable identity/hash vs descriptor pin | `gate8_executable_identity_mismatch` | `False` |
| changed cwd / path substitution / traversal | `gate8_cwd_outside_repository_scope` | `False` |
| changed environment allowlist | `gate8_environment_not_allowlisted` | `False` |
| changed descriptor/config digest | `gate8_descriptor_config_drift` | `False` |
| any caller shell string / shell metacharacter | `gate8_caller_shell_string_rejected` | n/a — `(None, reasons)` |
| recomputed `subject_scope_binding_digest` disagrees (target / prompt / repo / task / capability / effect-class / adapter change) | `gate8_authority_subject_scope_mismatch` | n/a — `(None, reasons)` |

The binding is enforced by recomputing the exact
`subject_scope_binding_digest` from `identity` + `inputs` via the shared
`runtime_dispatch_permission._expected_subject_scope_binding_digest` (exactly
as Gate 6 / Gate 7 do), plus a fresh executable-hash comparison
(`os.stat` + SHA-256 read) against the `descriptor_resolver`-supplied pin.

---

## 6. Command representation, cwd, environment, runtime-target binding

- **Command representation:** an **argument vector**
  (`Gate8EffectPlan.argv: tuple[str, ...]`), never a shell string. There is
  no `command_text` / `shell` parameter. Every argv element and the
  executable path are checked for shell metacharacters
  (`; & | < > $ \` newline * ? ( ) [ ] { } ! \ " '`); any presence →
  `gate8_caller_shell_string_rejected`. The Shell Gate classifier receives a
  plain space-joined string built **only** from already-proven-inert tokens
  — it is not a shell string and cannot be evaluated as one.
- **cwd:** `_canonical_cwd_within_repository` resolves the path
  (`Path.resolve()`) and accepts it only if it is the repository root or a
  directory beneath it; anything else → `gate8_cwd_outside_repository_scope`.
- **Environment:** `Gate8EffectPlan.env_allowlist` is an exact set of
  variable **names**; the ambient process environment is never passed. A
  blank / non-string name → `gate8_environment_not_allowlisted`.
- **Runtime target:** `ResolvedExecutable.runtime_target_id` (echoed by the
  trusted resolver) must equal `inputs.runtime_target_id` →
  `gate8_runtime_target_drift` on mismatch. The `subject_scope_binding_digest`
  recompute also binds the target.
- **Child-process / resource / time / supervision:**
  `child_process_policy ∈ {"prohibited", "single_child_limit"}` and bounded
  `resource_limit_ref` / `time_limit_ref` / `supervision_ref` →
  `gate8_containment_profile_invalid` otherwise.
- **Network / credentials:** `network_denied is True` and
  `credentials_required is False` → `gate8_network_not_deniable` /
  `gate8_credentials_required` otherwise.

---

## 7. Shell Gate classifier consumption + no-effect proof

Gate 8 owns: trusted-input validation, exact binding, construction of the
Shell Gate evaluation input, invocation of the classifier, normalisation
into `Gate8Result`. The **mature 88P `shell_gate.build_shell_gate`** remains
authoritative for command classification — Gate 8 re-implements none of it
(`test_shell_gate_classifier_is_the_canonical_existing_one` asserts the
absence of `_classify_command` / `SGP_CATEGORIES` from the coordinator).

**Decision mapping:** the resolved executable + argv must classify as an
allowlisted category (`read_only_inspection` / `pcae_governed_lifecycle`)
with an allowlisted decision (`allow_read_only` / `allow_governed`), with no
`hard_block_present`, no `test_run_preflight_required`, and none of the 18
mutation / network / secret / environment detected flags set. Any other
outcome — including an **unknown** category and any of the
`GATE8_DENIED_SHELL_GATE_CATEGORIES` — fails closed with
`gate8_shell_gate_category_denied`. A classifier exception →
`gate8_shell_gate_internal_error`. Neither is ever treated as permissive.

**Side-effect audit (`.1R.13.1` §12.4, phase-prompt §19):**
`build_shell_gate` is pure for the inputs Gate 8 supplies. Its only
`subprocess.run` call (`_call_doctor_test_run`, a governed read-only
`pcae doctor test-run --json` lock probe) fires **only** when
`command_category == "test_execution"` **and**
`expensive_test_execution_detected`. A `runtime_dispatch` adapter effect
plan is never an expensive pytest command; Gate 8 additionally refuses any
plan whose program basename is `pytest` / `py.test` / `tox` / `nox` /
`unittest` **before** calling `build_shell_gate`
(`gate8_shell_gate_preflight_side_effect_refused`), and treats a returned
`test_run_preflight_required` as a denial. `build_shell_gate` is therefore
invoked only on a proven-inert input — no process is spawned, no network
opened, no repository state modified, no external state written, no command
content executed. Gate 10 remains the first external effect.

Tests: `test_shell_gate_call_has_no_external_effect` (spies the call and
fails the test if `_call_doctor_test_run` is invoked),
`test_shell_gate_category_denied_fails_closed`,
`test_shell_gate_internal_error_fails_closed`,
`test_pytest_effect_plan_refused_before_shell_gate`.

---

## 8. V-13-1 — phase-aware scope-guard extension (`.1R.13.1` §22)

The authorised addition of `runtime_dispatch_gate8.py` deterministically
trips the same class of point-in-time frozen-baseline production-scope /
consumer-inventory guards that `.1R.13.2` converted for Gate 7. Per
`.1R.13.1` §22 these are **extended** (not deleted, not broadly xfailed, not
permanently re-frozen): `runtime_dispatch_gate8.py` is added to each
authorised-surface / authorised-consumer set, keeping the **subset**
orientation (`changed - AUTHORIZED == set()` / `x <= {AUTHORIZED}`) so an
*unauthorised* production-file / projection-consumer / Gate7Result-consumer
expansion still fails, and the exact-empty `gate9` / `hpac` asserts stay
exact.

### 8.1 Guards extended

| Test file :: test | Change |
|---|---|
| `test_gate5_..._1r10.py :: test_only_expected_production_files_changed_since_baseline` | `runtime_dispatch_gate8.py` added to `_AUTHORIZED_RUNTIME_DISPATCH_CHAIN_SURFACE` |
| `test_gate5_..._1r11.py :: test_production_scope_is_exactly_the_three_planned_files` | added to `_AUTHORIZED_GATE_CHAIN_SURFACE` |
| `test_gate6_..._1r12.py :: test_only_expected_production_file_changed_since_baseline` | added to the `<= {…}` subset bound |
| `test_gate6_..._1r13.py :: test_1r12_production_diff_is_exactly_one_file` | added to `_AUTHORIZED_POST_1R12_CHAIN_SURFACE` |
| `test_gate6_..._1r13.py :: test_known_pre_existing_point_in_time_scope_guard_failures_are_attributable` | subset bound widened to `{gate7, gate8}` |
| `test_runtime_authority_production_repair_..._117.py :: test_production_file_allowlist_matches_frozen_phase_matrix` | added to `_authorized_surface` |
| `test_runtime_authority_production_repair_..._117.py :: test_consumer_inventory_is_bounded_and_gate9_stays_unwired` | added to the `projection_consumers <= {…}` bound; `gate9_consumers == set()` kept exact |
| `test_b1_b7_n1_n2_..._1r8.py :: test_isolation_only_three_production_files_changed_since_baseline` | added to `_authorized` |
| `test_b1_b7_n1_n2_..._1r8.py :: test_isolation_no_gate_coordinator_or_gate9_consumption_wiring` | added to `projection_consumers <= {…}`; `gate9_callers == set()` and `hpac_consumers == {…}` kept exact |
| `test_gate7_..._1r13_2.py :: test_production_scope_since_baseline_is_the_single_new_gate7_file` | converted from `== {gate7}` to `gate7 in changed and changed <= {gate7, gate8}` |
| `test_gate7_..._1r13_3.py :: test_no_downstream_production_consumer_of_gate7_result` | converted from `== {gate7}` to `hits <= {gate7, gate8}` (Gate 8 is the sole authorised downstream `Gate7Result` consumer) |
| `test_gate7_..._1r13_3.py :: test_runtime_introspection_constants_unchanged_since_baseline` | converted to `out <= {gate7, gate8}` + explicit `runtime_introspection.py not in out` |

All are **non-functional** frozen-diff / consumer-inventory hygiene
assertions. Every `.1R.8` / `.1R.10` / `.1R.11` / `.1R.12` / `.1R.13` /
`.1R.13.2` / `.1R.13.3` *functional* closure is intact and untouched. The
Gate-8 docstring deliberately uses the hyphenated forms "Gate-6 decision" /
"Gate-7 runtime-enforcement evaluation" in prose so the
`run_gate7_runtime_enforcement` / `resolve_runtime_enforcement_posture` /
`Gate6Decision` / `is_gate6_decision` sole-owner greps in the `.1R.13.2` /
`.1R.13.3` suites stay accurate (Gate 8 owns none of those symbols).

### 8.2 Fixed-SHA A/B attribution

- **Baseline:** `6a9d650f54fb7a5c02652180f0bbcc3a41080198` (`.1R.13.3`
  completion), materialised in an isolated `git worktree`.
- **Candidate:** `HEAD` (this phase).
- **Method:** `-p no:randomly`, `-n0`, explicit file list of every suite
  referencing `runtime_dispatch_gate8` / `runtime_dispatch_gate7` /
  `runtime_dispatch_gate5` / `runtime_dispatch_permission` / `shell_gate` /
  `is_gate7_result` / `Gate7Result`.

_(Filled in at finalisation — see the phase report and
`.pcae/phase-completion-metadata.json`.)_

```
CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0
UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS       = 0
```

### 8.3 Disposition

> **V-13-1 — extended, INDEPENDENT VERIFICATION PENDING.** Not self-closed.
> `.1R.13.5` re-confirms the extensions preserve the original security
> intent with no functional regression behind them.

---

## 9. Gate8Result model — ephemeral, identity-only, non-serializable, registry-provenanced

| Property | Implementation |
|---|---|
| not caller-constructable | `_seal` guard (`_GATE8_RESULT_CONSTRUCTOR_SEAL`); `is_gate8_result` = exact-object membership in `_GATE8_RESULTS` |
| only insertion point | `run_gate8_process_containment`'s completed-establishment return path (both the `containment_established=True` unreachable branch and the `False` audit-record branch); no `(None, reasons)` path inserts |
| non-serializable | `__reduce__` raises |
| identity-only equality | `__eq__` is `self is other`; `__hash__` is `id(self)` |
| not subclassable | `__init_subclass__` raises |
| `containment_established` | `bool` only — validated in `__init__` |
| carried fields | `causing_reason_ids`, `invocation_id`, `attempt_id`, `request_id`, `gate7_result_digest`, `effect_plan_digest`, `containment_evidence_digest`, `live_preflight_digest`, `shell_gate_decision`, `shell_gate_category`, `expires_at`, `evaluated_at` |
| not an execution token | `containment_established=True` means only "a bounded launch environment is established and attested" (RDGO-001 §0 wall `process permission != dispatch completion`); not the process running, not consumption, not dispatch |
| provenance ≠ progression | `is_gate8_result(x) == True` proves origin only; a future Gate 9 MUST additionally require `x.containment_established is True` |
| negative result discipline | `Gate8Result(containment_established=False, …)` is a structured audit record carrying `causing_reason_ids`; a downstream gate MUST NOT treat it as partial success |

**Anti-transfer:** direct construction / `object.__new__` / `copy` /
`deepcopy` / `pickle` / field-reconstruction / subclassing all rejected.
Non-serializability is **not** the sole trust mechanism — exact-object
registry membership is.

Tests: `test_gate8_result_not_caller_constructable`,
`test_gate8_result_non_transferable`,
`test_gate8_result_identity_equality_only`,
`test_gate8_result_not_subclassable`,
`test_object_new_gate8_result_not_a_registry_member`,
`test_is_gate8_result_means_provenance_not_containment`.

---

## 10. Idempotency / no consumption / no Gate-9 / no Gate-10 effect

Gate 8 **consumes nothing**: no approval, HPAC proof, presentation,
challenge, nonce, `Gate5Result`, Gate-6 decision, `Gate7Result`, authority
record, or lifecycle record is created, deleted, or mutated. No durable
authority-consumption record is written. No
`runtime_invocation_authority_consumption` primitive is called. Both
re-resolutions (projection revalidation, executable hash read) are **reads**.

```
attempt 1  ->  Gate8Result(containment_established=False, …)   [same containment_evidence_digest]
attempt 2  ->  Gate8Result(containment_established=False, …)   [fresh object, same digests]
              no durable consumption record, no approval/proof/lifecycle write, no state mutation
```

| Boundary | Evidence |
|---|---|
| **No Gate-9 call** | AST: no `runtime_invocation_authority_consumption` / `runtime_dispatch_gate9` import; no `dispatch_attempted`; no durable consumption record created (behavioral test, repo-wide `consumption.json` count unchanged) |
| **No Gate-10 effect** | AST forbidden-import guard: no `subprocess`, `socket`, `requests` / `httpx` / `urllib`, `asyncio`, `multiprocessing`, `ctypes`, `pty`, `fcntl`, `signal`, `ssl`, `selectors`; no `.dispatch(` / `Popen(` / `os.system(`; no adapter import |
| **Shell Gate no-effect** | `build_shell_gate` proven pure for the supplied inputs; pytest/tox/nox/unittest programs refused before the call; `_call_doctor_test_run` spy fails the test if invoked |
| **Runtime unchanged** | after Gate-8 runs, `CURRENT_RUNTIME_STATE == "Observed"`, `CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"`, `EXECUTION_AVAILABILITY == "unavailable"` |

Tests: `test_repeated_run_consumes_nothing_and_is_deterministic`,
`test_module_imports_nothing_effectful`,
`test_no_gate9_or_gate10_symbol_referenced`,
`test_no_consumption_or_lifecycle_write_call`,
`test_runtime_state_unchanged_after_gate8_runs`,
`test_internal_error_fails_closed_with_no_partial_output`.

---

## 11. Fail-closed model + call discipline

| Condition | Reason id | Result |
|---|---|---|
| missing / untrusted `Gate7Result` | `gate8_untrusted_gate7_result` | `(None, reasons)` |
| trusted `Gate7Result.decision != "ALLOW"` | `gate8_gate7_decision_not_allow` | `(None, reasons)` — **before** Shell Gate |
| `identity` / `inputs` / `authority_current_time` / `repo_root` / `effect_plan` / `descriptor_resolver` wrong type | `gate8_invalid_*` | `(None, reasons)` |
| missing / untrusted `Gate5Result` | `gate8_untrusted_gate5_result` | `(None, reasons)` |
| `invocation_id` / `attempt_id` not equal across `Gate5Result` / `Gate7Result` / `identity` | `gate8_invocation_binding_mismatch` | `(None, reasons)` |
| `inputs` fail the canonical construction re-check | `gate8_request_currentness_drift:<detail>` | `(None, reasons)` |
| target / effect-class not local-CLI-v1 representable | `gate8_runtime_target_ineligible` | `(None, reasons)` |
| projection not (or no longer) trusted / revalidating at Gate 8 | `gate8_stale_validated_authority_projection` | `(None, reasons)` |
| recomputed `subject_scope_binding_digest` disagrees | `gate8_authority_subject_scope_mismatch` | `(None, reasons)` |
| shell metacharacter in executable path or any argv element | `gate8_caller_shell_string_rejected` | `(None, reasons)` |
| effect-plan executable ≠ resolved executable | `gate8_effect_plan_binding_mismatch` | `Gate8Result(containment_established=False)` |
| descriptor / config digest drift | `gate8_descriptor_config_drift` | `Gate8Result(False)` |
| runtime-target drift since Gate 7 | `gate8_runtime_target_drift` | `Gate8Result(False)` |
| executable not installed / not a regular file | `gate8_executable_not_installed` | `Gate8Result(False)` |
| executable hash ≠ descriptor pin | `gate8_executable_identity_mismatch` | `Gate8Result(False)` |
| cwd outside the repository scope / traversal | `gate8_cwd_outside_repository_scope` | `Gate8Result(False)` |
| env allowlist contains a blank / non-string name | `gate8_environment_not_allowlisted` | `Gate8Result(False)` |
| child-process / resource / time / supervision profile invalid | `gate8_containment_profile_invalid` | `Gate8Result(False)` |
| network not deniable | `gate8_network_not_deniable` | `Gate8Result(False)` |
| credential access required | `gate8_credentials_required` | `Gate8Result(False)` |
| pytest/tox/nox/unittest program in the effect plan | `gate8_shell_gate_preflight_side_effect_refused` | `Gate8Result(False)` |
| Shell Gate classifier exception | `gate8_shell_gate_internal_error` | `Gate8Result(False)` |
| Shell Gate category / decision denied | `gate8_shell_gate_category_denied` | `Gate8Result(False)` |
| any unexpected exception from the bounded establishment path | `gate8_internal_error_fail_closed` | `(None, reasons)` — no partial output |

**No partial containment output** — a rejection creates no `Gate8Result`
with `containment_established=True` that any later gate could treat as
partial success.

---

## 12. Gate-8 → Gate-9 handoff (not implemented — documented only)

Gate 9 does not exist. `run_gate8_process_containment` **terminates after
its own containment decision**:

```
Gate 7  ->  Gate 8 establishment  ->  REJECT (Gate7Result is DENY today)  ->  STOP
```

No Gate-9 primitive call, no `runtime_dispatch_gate9` symbol, no durable
record. The `Gate8Result` carries exactly the fields (`invocation_id`,
`attempt_id`, `request_id`, `gate7_result_digest`, `effect_plan_digest`,
`containment_evidence_digest`, `live_preflight_digest`,
`shell_gate_decision`, `shell_gate_category`, `expires_at`) that a future
Gate 9 will re-derive per `.1R.13.1` §16.1 — but this phase creates no
consumer, no serialization, and no persisted handoff. The §16 handoff
contract is unchanged.

---

## 13. V-13-3-1 / V-13-3-2 / V-13-3-3 (carried from `.1R.13.3` — not amplified)

- **V-13-3-1** — the `.1R.13.2` "PB-policy drift covered transitively via
  projection revalidation" wording overstates
  `revalidate_validated_authority_projection`. **Gate 8 does not amplify
  this.** Gate 8 consumes a trusted `Gate7Result` and process/effect
  context, **not** PB policy state, and makes **no** claim that it
  revalidates PB policy. The Gate-8 docstring and this document say only
  that Gate 8 re-checks "current policy/RE decision" by requiring a live
  trusted `Gate7Result(decision="ALLOW")` and a still-revalidating
  projection — policy re-evaluation remains Gate 6's contract
  responsibility.
- **V-13-3-2** — Gate 7's `matched_no_go_ids` omits registry-mandatory
  RE-NOGO-009/013/015/016/017 by frozen design. **Gate 8 does not depend on
  the completeness of that diagnostic list.** It trusts the Gate-7
  `decision` / provenance boundary (`is_gate7_result` + `decision == "ALLOW"`),
  never a `matched_no_go_ids` string, for authority.
- **V-13-3-3** — the concurrency-flake attribution correction. Carried as
  informational; not reopened.

---

## 14. V-2 / V-3 / V-4 / F7 (carried unchanged — no Gate-8 impact)

- **V-2 / V-3** (RDGO-001 §4/§6 "which gate creates the sequence-3 event"):
  Gate 8 imports **nothing** from `hpac_lifecycle` or `hpac_verifier`
  (AST-verified), derives authority solely from `gate5_result.projection`
  re-trusted at point of use, and depends on no sequence-3 wording. **No
  Gate-8 impact, no amplification, no STOP.**
- **V-4** (PBRD-001 §4 fact 14 literal 7-field `human_authority_binding` vs
  the 3-field `RuntimeDispatchHumanAuthorityBinding`): Gate 8 consumes only
  the trusted upstream **objects** (`Gate7Result`, `Gate5Result.projection`),
  never the 3-field or 7-field binding. `test_gate8_never_consumes_a_gate6_decision`
  and the AST import checks confirm the module references neither
  `RuntimeDispatchHumanAuthorityBinding` nor the PBRD fact-14 subfields.
  **No Gate-8 impact, no STOP.**
- **F7** — the `_GATE8_RESULTS` identity registry and Gate 8's consumption
  of `Gate7Result` / `Gate5Result` run under the **same-account
  autonomous-agent assumption**. They resist caller-supplied **data**
  forgery — **not** arbitrary same-process Python code execution. Stated
  **verbatim** in the module docstring; **threat model NOT broadened**. This
  phase does not claim a registry-backed `Gate8Result` withstands arbitrary
  mutation of trusted process memory.

All three of V-2 / V-3 / V-4 remain non-blocking contract-alignment debt and
candidates for a dedicated, separately-authorized contract-clarification
phase. This phase modifies no contract.

---

## 15. Production files changed

| File | Change | Lines |
|---|---|---|
| `src/pcae/core/runtime_dispatch_gate8.py` **(new)** | Gate-8 coordinator: `run_gate8_process_containment`, `Gate8Result`, `is_gate8_result`, `_GATE8_RESULTS`, `Gate8EffectPlan`, `ResolvedExecutable`, `GATE8_ALLOWED_SHELL_GATE_CATEGORIES` / `_DECISIONS` / `GATE8_DENIED_SHELL_GATE_CATEGORIES`, helper functions | ~620 (incl. the frozen-model docstring) |

`git diff --name-only 6a9d650f HEAD -- src/pcae` → **exactly**
`src/pcae/core/runtime_dispatch_gate8.py`.

**Not changed:** `runtime_dispatch_gate7.py`, `runtime_dispatch_permission.py`,
`runtime_dispatch_gate5.py`, `runtime_enforcement_safety_authorization.py`,
`runtime_introspection.py`, `shell_gate.py`, `permission_broker_foundation.py`
(POL-005), `policy.py`, `runtime_adapter.py` / `mock_runtime_adapter.py`,
`runtime_invocation_authority_consumption.py`, `hpac_*`, all 9 normative
contracts, schema packages, version/build config, `pcae runtime inspect`.

Test files changed: 1 new
(`test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py`,
63 focused cases) + 8 earlier-phase files whose point-in-time guards were
extended to include `runtime_dispatch_gate8.py` (§8.1) — no *functional*
earlier-phase test weakened.

---

## 16. Consumer inventory (`.1R.13.1` §29)

| Symbol | Consumer(s) | Classification | Alternate path? |
|---|---|---|---|
| `Gate7Result` / `is_gate7_result` | `runtime_dispatch_gate7.py` (defines) + `runtime_dispatch_gate8.run_gate8_process_containment` **only** (sole authorised downstream consumer) | authorized `.1R.13.4` | No — `git grep` → exactly `{gate7, gate8}` |
| `Gate5Result` / `is_gate5_result` | Gate 6 + Gate 7 (pre-existing) + Gate 8 (one added registry-check call site) | authorized | No new authority path (re-trust + revalidate only) |
| `ValidatedAuthorityProjection` re-trust predicates | `runtime_dispatch_{permission,gate5,gate7}` (pre-existing) + `runtime_dispatch_gate8` (added) | authorized | subset of the authorized gate-chain modules; `gate9_consumers` / `gate9_callers` stay empty |
| `shell_gate.build_shell_gate` | `pcae shell-gate` CLI (pre-existing) + `runtime_dispatch_gate8` (one read-only call site) | authorized | No behavioral change to the classifier |
| `Gate8Result` / `is_gate8_result` | **none** — Gate 9 does not exist until `.1R.14` | expected zero | — |
| `Gate6Decision` / `is_gate6_decision` / `run_gate6_permission_broker` / `run_gate7_runtime_enforcement` / `resolve_runtime_enforcement_posture` | **not referenced by `runtime_dispatch_gate8.py` at all** | — | Gate 8 owns none of these symbols |

**Expected downstream production consumers of `Gate8Result` = zero** (Gate 9
not built). No unexpected alternate authority path.

Tests: `test_gate8_is_sole_production_owner_of_containment_boundary`,
`test_gate8_is_the_only_new_gate7_result_consumer`,
`test_gate8_never_consumes_a_gate6_decision`,
`test_gate8result_has_zero_downstream_production_consumers`.

---

## 17. Contract identity

`git diff 6a9d650f HEAD -- docs/contracts` is **empty**. Byte-unchanged and
asserted by `test_contracts_and_pol005_bytes_unchanged_since_baseline`:

- `RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` (RDGO-001 v3.0)
- `PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` (PBRD-001 v2.0)
- `RUNTIME_PROVIDER_ADAPTER_CONTRACT.md` (RPAC-001 v1.0)
- `RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` (RIHAC-001 v2.0)
- `RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` (RIASC-001 v3.0)
- `HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (HPAC-001 v2.0)
- `PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` (PBPA-001)
- `src/pcae/core/permission_broker_foundation.py` (POL-005) — byte-unchanged
- `src/pcae/core/shell_gate.py` — byte-unchanged
- `src/pcae/core/runtime_dispatch_gate5.py` / `runtime_dispatch_gate7.py` /
  `runtime_dispatch_permission.py` / `runtime_introspection.py` —
  byte-unchanged

No normative contract repair was performed. No inter-contract contradiction
requiring a STOP was found (`.1R.13.1` §31): RDGO-001 §9 + PBRD-001 §6/§14
are internally consistent and sufficient to specify Gate 8 at this level.

---

## 18. Contract traceability

| Implemented element | RDGO-001 | PBRD-001 | Shell Gate | RPAC / capability |
|---|---|---|---|---|
| Gate-7 → Gate-8 handoff (trusted result + ALLOW + effect plan) | §9 input row; §1 row 8 | §14 | — | — |
| independent containment establishment, no re-decide | §9 "recheck … current policy/RE decision" | — | — | — |
| exact executable, no caller shell string | §9; §11 "argument vector, not unrestricted shell evaluation" | §6 "untrusted executable or shell command strings" | "never executes" invariant | RPAC executable identity |
| executable identity / hash / installation | §9 | §12 item 6 | — | RPAC descriptor pin |
| descriptor/config + repository/HEAD/task/target/prompt re-check | §9; §13 live-preflight column | §14 | — | — |
| cwd / argv / env allowlist / child-process / resource / supervision | §9 | §11 (process/fs/network/credential distinctions) | — | — |
| network denied + no credential access | §9 | §11 | — | — |
| bind containment evidence to invocation | §9 "bind the established containment evidence to the invocation"; §10 item 8 | — | — | — |
| Shell Gate category cross-check | §9 | §6 | `shell_gate` 24-category / 26-decision model | — |
| no effect (no dispatch yet) | §9 "No dispatch yet"; §11 (Gate 10 first effect) | §11 | — | adapter contract untouched |
| Gate8Result anti-transfer / provenance | §9 discipline | §5/§9 pattern | — | — |
| Gate-8 → Gate-9 handoff (data only) | §10 (eight items); §10 last ¶ | §14 | — | — |

No undocumented semantics: every implemented element maps to a frozen
contract clause.

---

## 19. Regression evidence

_(Filled in at finalisation — see the phase report and
`.pcae/phase-completion-metadata.json`.)_

- **Gate-8 suite:** `tests/test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py`
  — 63 passed, 0 failed.
- **Targeted affected-suite A/B** (baseline `6a9d650f` via isolated `git
  worktree` vs `HEAD`, `-p no:randomly -n0`): `CANDIDATE-ONLY UNEXPLAINED
  FUNCTIONAL NONPASSING NODES = 0`; `UNEXPLAINED ATTRIBUTABLE FUNCTIONAL
  REGRESSIONS = 0`.
- **Governance:** `pcae health` healthy; `pcae check` passed; `pcae status
  coherence` coherent; `pcae runtime inspect` → `not_implemented / Observed
  / observe / unavailable`, PB `execution_unavailable`, posture
  `non-executing` — **unchanged**.
- The full `-m fast_green` marker (~344 pre-existing repo-wide failures) is
  **not** the authoritative signal; the deterministic explicit-file A/B is.

---

## 20. Limitations (not defects)

- No positive production `Gate8Result` (`containment_established=True`) is
  exercised on the production path — the permanent NON-REAL upstream makes a
  real trusted `Gate7Result(decision="ALLOW")` unobtainable, and a real
  `Gate7Result` is always `DENY`. The positive branch
  (`pragma: no cover`) is exercised only through the labelled provenance
  substitution against a real inert executable (`/bin/echo`); the real
  runtime posture is unchanged.
- Gate 8 performs no git/repository resolution of its own beyond canonical
  cwd resolution and the executable hash read; it re-checks `inputs`
  structurally and binds them into the containment-evidence digest,
  mirroring the whole chain's discipline.
- `descriptor_resolver` is a trusted, coordinator-supplied dependency
  (exactly like `run_gate5`'s `lifecycle_store`). A real
  descriptor-resolution / adapter-registry integration is a future
  concern; it is not fabricated here.
- Gate 9, Gate 10 are not implemented. `.1R.14` / `.1R.15` remain frozen and
  BLOCKED.

---

## 21. `.3` governance incident

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.
History retained; creates no precedent. No delegated worker may
autonomously commit, finalize, or push. Only the primary human-authorized
operator holds `.1R.13.4` lifecycle authority. Governed PCAE lifecycle
only — no raw `git commit` / `push`, no `--no-verify`, no force push, no
history rewrite, no hook bypass, no rollback.

---

## 22. Disposition

> **GATE-8 PROCESS CONTAINMENT COORDINATOR: IMPLEMENTED — INDEPENDENT
> VERIFICATION PENDING — NOT CLOSED.**
>
> `run_gate8_process_containment` is the frozen single Gate-8 owner:
> consumes a registry-provenanced `Gate7Result` only, **additionally**
> requires `decision == "ALLOW"` (a trusted `DENY` is a hard stop before
> Shell Gate evaluation), consumes a registry-provenanced `Gate5Result` and
> re-trusts + revalidates its projection at its own point of use, recomputes
> the subject/scope digest and the invocation lineage, resolves the exact
> executable through a trusted coordinator-supplied `descriptor_resolver`
> (never a caller shell string), refuses shell metacharacters in the argv
> vector, consumes the mature 88P `shell_gate` classifier read-only for a
> defensive category cross-check (proven non-effecting for the supplied
> inputs), establishes + attests one bounded launch environment, and returns
> exactly one ephemeral, identity-only, non-serializable,
> registry-provenanced `Gate8Result` (`containment_established` ∈
> `{True, False}`) or `(None, reasons)`. **Under the current posture Gate 8
> is structurally unreachable — every real call fails closed at the
> Gate-7-decision hard stop; no positive production Gate-8 success is
> possible today.** Gate 8 consumes nothing, is idempotently repeatable, and
> its result is expiring / cache-invalid across any drift. No Gate-9
> consumption, no Gate-10 effect. `shell_gate.py` / `runtime_dispatch_gate7.py`
> / POL-005 / all 9 contracts byte-unchanged; runtime remains
> `not_implemented / Observed / observe / unavailable`.
>
> **V-13-1 — extended, INDEPENDENT VERIFICATION PENDING.** Twelve
> point-in-time guards across the `.1R.8` / `.1R.10` / `.1R.11` / `.1R.12` /
> `.1R.13` / `.1R.13.2` / `.1R.13.3` / `.1R.117` suites extended to include
> `runtime_dispatch_gate8.py`, preserving the subset orientation and the
> exact-empty `gate9` / `hpac` asserts. Full A/B disclosure in §8.2.
>
> `.1R.13.4` is **NOT self-closed** and Gate 8 is **NOT verified**.

---

## 23. Recommended next phase

> **`149O.20L.7O.3W.1R.2B.1R.1.1R.13.5` — Independent Verification of the
> Gate-8 Process Containment (Shell Gate) Coordinator Integration.**
>
> Independently re-derive `.1R.13.1` §5, §11, §12, §16, §25 against this
> implementation — not trusted from this report or its tests. Independently
> confirm: the `is_gate7_result` provenance boundary **and** the
> `decision == "ALLOW"` requirement (a trusted `DENY` rejected before Shell
> Gate evaluation); the `is_gate5_result` provenance + projection re-trust +
> revalidation; the invocation lineage + subject/scope digest recompute; the
> §11.2 anti-substitution matrix (executable / argv / cwd / env / target /
> descriptor / shell-string); the Shell Gate classifier is the canonical
> existing one and is non-effecting for the supplied inputs; the
> `Gate8Result` anti-transfer discipline; `is_gate8_result` proves
> provenance not containment; the no-consumption / no-Gate-9/10 boundary;
> the runtime-unchanged state; the §16 Gate-8 → Gate-9 handoff contract; and
> that the V-13-1 guard extensions preserve the original security intent
> with no functional regression behind them.
>
> Requires its own separate explicit human authorization to begin; this
> phase grants none. **Do not begin `.1R.13.5`. Do not begin `.1R.14`
> (Gate 9). Do not implement Gate 9 or Gate 10. Do not enable execution.**
> `.1R.14` / `.1R.15` remain frozen, BLOCKED, and NOT renumbered — they
> unblock only after `.1R.13.2`–`.1R.13.5` all close VERIFIED with no
> blocking findings (`.1R.13.1` §17) and still require their own explicit
> human authorization. A dedicated V-2 / V-3 / V-4 (+ V-13-3-1 / V-13-3-2)
> contract-clarification phase remains an alternative non-blocking next
> step, also requiring its own authorization.
