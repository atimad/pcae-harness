# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.5 — Independent Verification of the Gate-8 Process Containment (Shell Gate) Coordinator Integration

Status: **GATE-8 — CLOSED. VERIFIED WITH NON-BLOCKING FINDINGS.**

Independent verification (re-derive, do not trust) of the
`149O.20L.7O.3W.1R.2B.1R.1.1R.13.4` Gate-8 Process Containment (Shell Gate)
coordinator integration, against RDGO-001 v3.0 §9 / §1 row 8 / §10 / §13 /
§15 / §19, the `.1R.13.1` planning document §5 / §11 / §12 / §16 / §17 /
§25, the mature 88P `shell_gate` classifier **source**, PBRD-001 v2.0 §6 /
§14, RPAC-001 v1.0, POL-005, and the independently-verified Gate-5 / Gate-6
/ Gate-7 boundaries. **No `.1R.13.4` claim was accepted because it appears
in that phase's report, implementation document, 63 tests, function/type
names, result-registry membership, or aggregate pass counts.**

No defect was repaired. No Gate-9 or Gate-10 code was written. No execution
was enabled. Runtime remains `not_implemented / Observed / observe /
unavailable`; POL-005 byte-unchanged; real execution UNAVAILABLE.

- **Verification-entry SHA:** `72898361` (`.1R.13.4` completion — "reconcile
  governed push state").
- **Immutable pre-`.1R.13.4` baseline:** `6a9d650f54fb7a5c02652180f0bbcc3a41080198`
  (`.1R.13.3` completion).
- **`.1R.13.4` implementation range (independently reconstructed):**
  `cda5c2fa` (governed task transition from post-`.1R.13.3` idle) → `df00c43c`
  (**the sole production + test + guard-extension commit**:
  `src/pcae/core/runtime_dispatch_gate8.py` new, the canonical document, the
  63-test suite, the twelve V-13-1 guard extensions) → `99ba32e3`
  (PROJECT_STATUS) → `d8a19880` (close task → idle) → `6b517dc5` (idle
  allowed-file expansion) → `b77bf4d2` (staged completion metadata + report)
  → `72898361` (push-state reconcile). The phase prompt's reported list
  (`cda5c2fa df00c43c 99ba32e3 d8a19880 6b517dc5`) omits the two
  finalization-staging commits `b77bf4d2` / `72898361`; the true range is
  `cda5c2fa..72898361` and the only functional commit is `df00c43c`.
- **Fresh verification suite:**
  `tests/test_gate8_process_containment_coordinator_independent_verification_3w1r2b1r1_1r13_5.py`
  — **120 tests, 0 failed**, independently constructed (own synthetic
  provenance substitution, own resolver / effect-plan builders).

---

## 1. Contracts / source inspected in full

RDGO-001 v3.0 §9 (verbatim, via `.1R.13.1` §5.1) + §1 row 8 + §10 (eight
durable items) + §13 (static-vs-live preflight) + §15 (stale state) + §19
(fail-closed); `.1R.13.1` §5 / §6 / §11 / §12 / §16 / §17 / §22 / §25 / §26
/ §28 / §29; the `.1R.13.4` implementation document and its full diff
(`df00c43c`); the `.1R.13.3` Gate-7 independent verification; `.1R.13.2`
Gate-7 implementation; `.1R.13` Gate-6 independent verification; `.1R.11`
Gate-5 independent verification; PROJECT_STATUS.md. Current source read in
full: `runtime_dispatch_gate8.py` (884 lines), `runtime_dispatch_gate7.py`,
`runtime_dispatch_gate5.py`, `runtime_dispatch_permission.py`
(`RuntimeDispatchRequestConstructionInput`, `RuntimeDispatchIdentity`,
`_expected_subject_scope_binding_digest`, `_validate_construction_inputs`,
`canonical_runtime_dispatch_projection`), `shell_gate.py` (`build_shell_gate`,
`_classify_command`, `_classify_single`, `_decide`, `_call_doctor_test_run`),
`runtime_introspection.py`, `runtime_enforcement_safety_authorization.py`.

---

## 2. Independent Gate-8 call flow (re-derived from source)

`run_gate8_process_containment(gate7_result, *, gate5_result, identity,
inputs, authority_current_time, repo_root, effect_plan, descriptor_resolver)`:

1. **Gate-7 provenance** — `is_gate7_result(gate7_result)` (function-local
   import of `runtime_dispatch_gate7`); False → `(None,
   ("gate8_untrusted_gate7_result",))`. Then `assert isinstance(…,
   Gate7Result)`.
2. **Structural input guards** — `type(identity) is RuntimeDispatchIdentity`;
   `type(inputs) is RuntimeDispatchRequestConstructionInput`;
   `_bounded_string(authority_current_time, 64)`; `isinstance(repo_root,
   Path)`; `type(effect_plan) is Gate8EffectPlan`; `callable(descriptor_resolver)`
   — each → its own `gate8_invalid_*` reason.
3. **Gate-7 decision** — `gate7_result.decision != "ALLOW"` (exact string
   equality) → `(None, ("gate8_gate7_decision_not_allow",))`. **This is
   before any Shell Gate call, drift re-resolution, or containment work.**
4. **Gate-5 provenance** — `is_gate5_result(gate5_result)`; False →
   `gate8_untrusted_gate5_result`. Then `assert isinstance(…, Gate5Result)`.
5. **Invocation lineage** — `gate5_result.invocation_id ==
   identity.invocation_id` **and** `gate7_result.invocation_id ==
   identity.invocation_id` **and** `gate7_result.attempt_id ==
   identity.attempt_id` → else `gate8_invocation_binding_mismatch`.
6. **Canonical construction re-check** — `_validate_construction_inputs(inputs)`
   → `gate8_request_currentness_drift:<detail>`; then `effect_class ==
   "bounded_local_process_dispatch"` + `network_requirement is False` +
   bounded `runtime_target_id` → else `gate8_runtime_target_ineligible`.
7. **Projection re-trust + revalidation at Gate 8's own point of use** —
   `is_trusted_validated_authority_projection(gate5_result.projection)` and
   `revalidate_validated_authority_projection(projection,
   current_time=authority_current_time)` (the latter re-runs
   `validate_approval`) → else `gate8_stale_validated_authority_projection`.
8. **Subject/scope digest recompute** —
   `_expected_subject_scope_binding_digest(identity=identity, inputs=inputs)`
   compared to `projection.subject_scope_binding_digest` → else
   `gate8_authority_subject_scope_mismatch`.
9. **Executable resolution** — `descriptor_resolver(inputs)`; `type(resolved)
   is ResolvedExecutable` → else `gate8_invalid_descriptor_resolver`.
10. **Caller-shell-string refusal** — `_bounded_string(executable_path, 4096)`
    and no shell metacharacter in `executable_path` or any `argv` token
    (`; & | < > $ \` \n \r \t * ? ( ) [ ] { } ! \ " '`); non-string token
    also refused → `gate8_caller_shell_string_rejected`.
11. **From here a `Gate8Result` is always returned** (`containment_established`
    True or False); the following are appended to `failure_reasons`, never
    `(None, reasons)`:
    - 8a `effect_plan.executable_path != resolved.path` →
      `gate8_effect_plan_binding_mismatch`
    - 8b `resolved.descriptor_digest / target_config_digest` ≠
      `inputs.adapter_descriptor_binding.*` → `gate8_descriptor_config_drift`
    - 8c `resolved.runtime_target_id != inputs.runtime_target_id` →
      `gate8_runtime_target_drift`
    - 8d `not resolved.installed` → `gate8_executable_not_installed`; else
      `_hash_file(resolved.path)` (`os.stat` regular-file check + SHA-256
      read, **never an execution**) — `None` →
      `gate8_executable_not_installed`; `!= resolved.sha256` →
      `gate8_executable_identity_mismatch`
    - 8e `_canonical_cwd_within_repository(effect_plan.cwd, repo_root)` is
      `None` → `gate8_cwd_outside_repository_scope`
    - 8f any `env_allowlist` name blank / non-string / not stripped →
      `gate8_environment_not_allowlisted`
    - 8g `child_process_policy ∉ {"prohibited","single_child_limit"}` or any
      of `resource_limit_ref` / `time_limit_ref` / `supervision_ref` not a
      bounded string → `gate8_containment_profile_invalid`
    - 8h `network_denied is not True` → `gate8_network_not_deniable`;
      `credentials_required is not False` → `gate8_credentials_required`
    - 8i **Shell Gate cross-check** — if the executable basename or any argv
      token basename ∈ `{pytest, py.test, tox, nox, unittest}` →
      `gate8_shell_gate_preflight_side_effect_refused` (**before**
      `build_shell_gate`). Otherwise
      `build_shell_gate(repo_root, "<exe> <argv…>")` (all tokens
      already proven metacharacter-free); exception →
      `gate8_shell_gate_internal_error`; then deny
      (`gate8_shell_gate_category_denied`) if `hard_block_present`, or
      `test_run_preflight_required`, or any of 18 mutation/network/secret/
      env detected flags, or category ∈ `GATE8_DENIED_SHELL_GATE_CATEGORIES`,
      or category ∉ `{read_only_inspection, pcae_governed_lifecycle}`, or
      decision ∉ `{allow_read_only, allow_governed}`.
12. **Evidence assembly** — `_gate7_result_digest`, `_effect_plan_digest`,
    `live_preflight_digest`, `containment_evidence_digest` (over executable
    identity + argv + cwd + env allowlist + child/resource/time/supervision
    + `network_denied=True` + `credentials_required=False` + invocation +
    `gate7_result_digest` + `effect_plan_digest` +
    `subject_scope_binding_digest`).
13. `established = not failure_reasons`. Positive branch (`pragma: no cover -
    production-unreachable`) → `Gate8Result(containment_established=True)`,
    inserted into `_GATE8_RESULTS`. Else `Gate8Result(containment_established
    =False, causing_reason_ids=<ordered>)`, **also** inserted into
    `_GATE8_RESULTS`, returned with the ordered reason tuple.
14. Any unexpected exception → `(None, ("gate8_internal_error_fail_closed",))`
    — no `Gate8Result`, no partial output.

This flow was verified line-by-line against `runtime_dispatch_gate8.py` and
exercised by the 120-test verification suite.

---

## 3. Findings by verification area

| Area (phase-prompt §) | Result |
|---|---|
| §7 sole-owner inventory | **CONFIRMED.** `git grep -E "run_gate8_process_containment\|_GATE8_RESULTS" -- src/pcae` → exactly `runtime_dispatch_gate8.py`. Other `build_shell_gate` callers (`pcae shell-gate` CLI, `gate_dry_run*`, `permission_broker*`) are pre-existing, unrelated, advisory. No parallel Gate-8 production path, no bypass route. |
| §8 Gate7Result provenance | **CONFIRMED.** `is_gate7_result` = exact-object `_GATE7_RESULTS` membership. Freshly tested: `None`, `object.__new__(Gate7Result)` with forged slots, `deepcopy` (raises), `pickle` (raises), bare `decision="ALLOW"` object — all → `gate8_untrusted_gate7_result`. |
| §9 provenance ≠ success | **CONFIRMED.** `is_gate7_result(x) is True` + `decision ∈ {"DENY","HUMAN_REVIEW","MAYBE","allow","ALLOW "}` → `gate8_gate7_decision_not_allow`, no `Gate8Result`. Exact string equality; no permissive normalization. |
| §10 trusted DENY hard stop | **CONFIRMED.** A genuine `_GATE7_RESULTS` member with `decision="DENY"` — driven through the real `run_gate7_runtime_enforcement` negative branch (the only thing it produces today) — is rejected at the decision gate with `build_shell_gate` call-count **0** (spied). The rejection is at flow step 3, before steps 6–13. |
| §11 unknown/non-ALLOW fail-closed | **CONFIRMED.** See §9 row. |
| §12 current production reachability | **CONFIRMED NO.** `full_chain(simulation_only=False)` → `projection is None` (permanent NON-REAL hard stop at `validate_approval`), so no `Gate5Result` → no `Gate6Decision` → no `Gate7Result` exists to hand to Gate 8; and a real `Gate7Result` is always `DENY`. Positive containment branch is `pragma: no cover`. |
| §13 structural test seam is inert | **CONFIRMED.** The verification fixture substitutes `is_gate7_result` / `is_gate5_result` / the two projection predicates in the `runtime_dispatch_gate8` namespace **only**. `_REAL_IS_GATE7(synthetic) is False`; `_REAL_IS_GATE5(synthetic) is False`; runtime constants unchanged. No `ValidatedAuthorityProjection`, approval, capability, or positive `Gate7Result` manufactured. Cannot be imported as a production bypass (predicates are module attributes, not injectable in production). |
| §14 Gate5Result provenance + lineage | **CONFIRMED.** `is_gate5_result` False → `gate8_untrusted_gate5_result`; trusted-Gate7 + forged-Gate5 → same; `gate5.invocation_id` ≠ identity → `gate8_invocation_binding_mismatch`. See finding **V-13-5-2**. |
| §15 projection re-trust / revalidation | **CONFIRMED.** Untrusted projection → `gate8_stale_validated_authority_projection`; a projection that no longer revalidates → same; `revalidate_validated_authority_projection` receives the Gate-8 `authority_current_time` verbatim; trust runs before revalidate. `revalidate` re-runs `validate_approval`, so revoke / expiry / consumption / principal drift after Gate 5/6/7 fails closed here. |
| §16 invocation lineage | **CONFIRMED** for `invocation_id` (Gate5/Gate7/identity) and `attempt_id` (Gate7/identity). `Gate5Result` structurally carries no `attempt_id` → **V-13-5-2** (INFO, transitively covered). |
| §17 subject/scope digest recompute | **CONFIRMED.** `_expected_subject_scope_binding_digest(identity, inputs)` compared to `projection.subject_scope_binding_digest`; a changed `runtime_target_id` / `prompt_hash` / `requested_capability` / `task_id` / `repository_identity` breaks the binding (or trips the construction re-check first). Same shared helper Gate 6 / Gate 7 use. |
| §18 anti-substitution matrix (§11.2 / §25) | **CONFIRMED for:** effect-plan executable (`gate8_effect_plan_binding_mismatch`), argv (every metacharacter class + non-string), runtime target (`gate8_runtime_target_drift`), descriptor/config digests (`gate8_descriptor_config_drift`), executable identity/hash (`gate8_executable_identity_mismatch`), invocation (`gate8_invocation_binding_mismatch`), shell-string (`gate8_caller_shell_string_rejected`). **PARTIAL for cwd / env-allowlist / transport** → **V-13-5-1** (non-blocking). |
| §19–§23 executable identity model / descriptor provenance / symlink / TOCTOU | **CONFIRMED.** Identity = descriptor-supplied absolute `path` + `sha256` pin; verification = `os.stat` regular-file gate + streamed SHA-256 read. Independently tested: same path + changed bytes → `gate8_executable_identity_mismatch`; a symlink to a different-content target → same (`Path` is not resolved before hashing, but the hash of the link target's bytes ≠ pin). `descriptor_resolver` is trusted-coordinator-supplied (frozen §12.5, like `run_gate5`'s `lifecycle_store`); a caller cannot inject an arbitrary descriptor. **Residual TOCTOU:** `os.stat` → SHA-256 read → `Gate8Result` creation is not atomic; a replace between the stat and the read would be observed as `gate8_executable_not_installed` / `_identity_mismatch` (fail-closed) or, in the vanishing window between read and result, a stale-but-consistent hash. **Gate 8 performs no execution**, so this is non-blocking today; the frozen §16 Gate-8→Gate-9 handoff correctly does **not** claim the path stays immutable forever — Gate 9's in-boundary revalidation (§16.2 invariant 4) must re-hash. Documented honestly, no overclaim in source or handoff contract. |
| §24 argv binding | **CONFIRMED.** Argument count / order / value / empty / command-like payloads all change `_effect_plan_digest` and `containment_evidence_digest`; metacharacter-bearing values are refused outright. |
| §25 shell metacharacter rejection | **CONFIRMED.** 12-case parametric sweep (`;`, `&&`, `|`, `$(…)`, `>`, backtick, `&`, newline, `*`, `'`, `"`) all → `gate8_caller_shell_string_rejected`; the classifier receives a plain space-joined string built only from already-proven-inert tokens. |
| §26 cwd binding | **PARTIAL** → **V-13-5-1**. `/etc` and `../..` traversal → `gate8_cwd_outside_repository_scope`; but any repo-scoped path (incl. `src/`) passes — cwd is not diffed against a bound reference. |
| §27 environment binding | **PARTIAL** → **V-13-5-1**. Blank / non-string name → `gate8_environment_not_allowlisted`; but an arbitrary well-formed name (`AWS_SECRET_ACCESS_KEY`) passes. The ambient environment is never read (only a name list). The value **is** bound into `containment_evidence_digest`. |
| §28 runtime-target binding | **CONFIRMED.** Resolver-echoed `runtime_target_id` ≠ `inputs.runtime_target_id` → `gate8_runtime_target_drift`; also bound into the subject/scope digest. No backend probing. |
| §29 containment profile binding | **CONFIRMED.** `child_process_policy ∈ {"prohibited","single_child_limit"}`, bounded `resource_limit_ref` / `time_limit_ref` / `supervision_ref`, `network_denied is True`, `credentials_required is False` — each independently tested; all bound into `containment_evidence_digest`; a change invalidates the digest. |
| §30 canonical Shell Gate classifier | **CONFIRMED.** `from pcae.core.shell_gate import build_shell_gate` (function-local, read-only, one call site); the coordinator contains no `_classify_command` / `SGP_CATEGORIES`. `shell_gate.py` byte-unchanged since baseline. |
| §31 Shell Gate decision vocabulary | **CONFIRMED.** `GATE8_ALLOWED_SHELL_GATE_CATEGORIES` / `_DECISIONS` re-derived against `shell_gate._decide` source: `read_only_inspection → allow_read_only` and `pcae_governed_lifecycle → allow_governed` are the only allowlisted pairs. `pcae_governed_commit` / `_push` (decision `allow_governed` but category not allowlisted), `test_execution`, `unknown` (`blocked_by_unknown_command` → `hard_block_present`) all → `gate8_shell_gate_category_denied`. Unknown category / decision fail closed. |
| §32 Shell Gate non-effecting property | **CONFIRMED.** `build_shell_gate` → `_classify_command` ("Does not touch the filesystem. Does not call subprocesses.") + `_detect_task_contract` (repo file reads only) + `_decide` (pure). Verified by AST: the only `subprocess.run(` call site in `shell_gate.py` is inside `_call_doctor_test_run`. With `subprocess.run` / `subprocess.Popen` / `sg._call_doctor_test_run` all monkeypatched to fail the test, Gate 8 runs (allowlisted + denied categories) spawn nothing. |
| §33 `_call_doctor_test_run` reachability | **CONFIRMED UNREACHABLE from Gate-8 input.** `_call_doctor_test_run` fires only when `command_category == "test_execution" AND expensive_test_execution_detected`, which `_classify_command` sets **only** for `program ∈ {pytest, py.test}` or `python -m pytest`. Gate 8 refuses program basename ∈ `{pytest, py.test, tox, nox, unittest}` on the executable path **or any argv token** — which is a superset of the pytest trigger — with `gate8_shell_gate_preflight_side_effect_refused` **before** calling `build_shell_gate`. 5-case parametric proof (`/usr/bin/pytest`, `/opt/py.test`, `python -m pytest`, `tox`, `nox`), each with `build_shell_gate` spied: call-count 0. |
| §34 other effectful Shell Gate helpers | **CONFIRMED none reachable.** AST call-node scan: `subprocess.run` / `.Popen` / `os.system` / `os.popen` appear only in `_call_doctor_test_run`. No `socket` / `pty` open in any helper reachable from `build_shell_gate`. |
| §35 Gate8Result construction authority | **CONFIRMED.** `_seal` guard (`_GATE8_RESULT_CONSTRUCTOR_SEAL`); `containment_established` type-checked `bool`; both the True (unreachable) and False branches insert into `_GATE8_RESULTS`; no `(None, reasons)` path inserts. Trust terminates in coordinator-owned identity-registry membership. |
| §36 is_gate8_result semantics | **CONFIRMED provenance-only.** AST of `is_gate8_result`: single `return isinstance(candidate, Gate8Result) and candidate in _GATE8_RESULTS`; **no `if` node**, no reference to `containment_established` in the return expression. The docstring correctly instructs a future Gate 9 to additionally require `containment_established is True`. |
| §37 trusted negative Gate8Result semantics | **CONFIRMED.** `Gate8Result(containment_established=False)` is a registry member (`is_gate8_result` True) carrying `causing_reason_ids` — a structured audit record, explicitly not partial success. Forward-compat test added. |
| §38 Gate8Result anti-transfer | **CONFIRMED.** `object.__new__` → not a member; direct construction → `TypeError`; `pickle.dumps` / `copy.deepcopy` → `TypeError` (`__reduce__` raises); `__init_subclass__` raises; a field-reconstructed lookalike with `containment_established=True` → `is_gate8_result` False; `__eq__` is `self is other`, `__hash__` is `id(self)`. |
| §39 cross-invocation transfer | **CONFIRMED.** Identity-only equality + `invocation_id` / `attempt_id` carried on the result; a result for invocation A can never satisfy `is_gate8_result` for a different object. |
| §40 cross-effect-plan transfer | **CONFIRMED.** Changing argv / cwd / env / any `*_ref` changes both `effect_plan_digest` and `containment_evidence_digest`; a future Gate 9's §16.2-invariant-3 read-back rejects a mismatched containment object. |
| §41 context expiry / cache invalidation | **CONFIRMED.** `expires_at = evaluated_at = authority_current_time`; `__reduce__` docstring: "process containment must be re-established … by every consumer". Result is invalid across any descriptor / executable / repository / policy / RE-decision change (digests differ). |
| §42 idempotency | **CONFIRMED.** Two runs over identical trusted inputs → two distinct objects, identical `containment_evidence_digest` / `effect_plan_digest`; repo-wide `consumption.json` count unchanged; no approval/proof/lifecycle write; Gate 5/6/7 state untouched. |
| §43 no consumption | **CONFIRMED.** AST: no `runtime_invocation_authority_consumption` / `runtime_dispatch_gate9` import; no `dispatch_attempted`; no `Gate9Result`; no `.consume(` / `.record_consumption(` / `.write_text(` / `.mkdir(` call; `consumption.json` count invariant across every test. |
| §44 Gate-8 → Gate-9 handoff contract | **RE-CHECKED — see §4 below.** `Gate8Result` carries exactly `containment_established`, `invocation_id`, `attempt_id`, `request_id`, `gate7_result_digest`, `effect_plan_digest`, `containment_evidence_digest`, `live_preflight_digest`, `causing_reason_ids`, `shell_gate_decision`, `shell_gate_category`, `expires_at`, `evaluated_at`. No consumer, no serialization, no persisted handoff created. §16 contract unchanged. |
| §45 Gate8Result ≠ Gate-9 eligibility | **CONFIRMED / frozen.** `is_gate8_result` proves provenance only; forward invariant asserted in the verification suite. |
| §46 eight Gate-9 unblocking criteria | **See §6.** |
| §47–§49 V-13-1 extension | **VERIFIED — REMAINS CLOSED; GATE-8 EXTENSION VERIFIED.** See §5. |
| §50 V-13-3-1 | **CONFIRMED not amplified.** Gate 8 source contains no "PB policy" / "permission broker" re-evaluation claim; it re-checks "current policy/RE decision" only by requiring a live trusted `Gate7Result(decision="ALLOW")` + a still-revalidating projection. |
| §51 V-13-3-2 | **CONFIRMED not amplified.** Progression depends on `decision == "ALLOW"` + provenance; `matched_no_go_ids` is only digested, never gated on. A trusted ALLOW with a deliberately-incomplete no-go list still proceeds. |
| §52 V-13-3-3 / V-13-4-1 | **RE-CHECKED.** `test_shell_gate.py` 118/118 pass; isolated `-k audit_verify_cli` 1 pass. Not reproduced, not candidate-attributable. |
| §53 V-2 / V-3 / V-4 / F7 | **CONFIRMED no amplification.** Gate 8 imports nothing from `hpac_lifecycle` / `hpac_verifier`; consumes only trusted upstream objects (`Gate7Result`, `Gate5Result.projection`); references neither `RuntimeDispatchHumanAuthorityBinding` nor `Gate6Decision`. F7 boundary stated verbatim ("same-account", "arbitrary same-process Python code execution", "threat model NOT broadened"). No claim of resistance to arbitrary in-process memory mutation. |
| §54 Gate-5 regression | **CONFIRMED CLOSED.** `full_chain(simulation_only=False)` → `projection is None`; `runtime_dispatch_gate5.py` byte-unchanged since baseline; consumes nothing. |
| §55 Gate-6 regression | **CONFIRMED CLOSED.** `runtime_dispatch_permission.py` + `permission_broker_foundation.py` (POL-005) byte-unchanged since baseline; precedence / POL-005 / provenance intact. |
| §56 Gate-7 regression | **CONFIRMED CLOSED.** `runtime_dispatch_gate7.py` byte-unchanged since baseline (`git diff 6a9d650f HEAD` empty); `GATE7_DECISION_VALUES == {"ALLOW","DENY"}`; a trusted `DENY` is not success; current posture still yields `DENY`; consumes nothing. |
| §57 production-file scope | **CONFIRMED.** `git diff --name-only 6a9d650f HEAD -- src/pcae` → **exactly** `src/pcae/core/runtime_dispatch_gate8.py`. |
| §58 consumer inventory | **CONFIRMED.** `git grep -E "Gate7Result\|is_gate7_result" -- src/pcae` → exactly `{gate7, gate8}` (Gate 8 = sole authorized new consumer). `git grep -E "Gate8Result\|is_gate8_result" -- src/pcae` → exactly `{gate8}` (zero downstream consumers). |
| §59 contract identity | **CONFIRMED byte-unchanged since `6a9d650f`:** RDGO-001, PBRD-001, RPAC-001, RIHAC-001, RIASC-001, HPAC-001, PBPA-001 (all under `docs/contracts/`), POL-005 (`permission_broker_foundation.py`), `shell_gate.py`, `runtime_dispatch_gate5/gate7/permission.py`, `runtime_introspection.py`, `runtime_enforcement_safety_authorization.py`. `git diff 6a9d650f HEAD -- docs/contracts` empty. |
| §63 runtime zero-effect proof | **CONFIRMED.** After every test: `CURRENT_RUNTIME_STATE == "Observed"`, `CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"`, `EXECUTION_AVAILABILITY == "unavailable"`. Shell Gate classification = validation only; runtime subprocess = 0; adapter invocation = 0; provider/network = 0; credential = 0; hardware = 0; Gate-9 consumption = 0; Gate-10 effects = 0. Verification/test subprocesses disclosed separately in §7. |

---

## 4. Gate-8 → Gate-9 handoff contract (`.1R.13.1` §16) — independently re-checked

| Handoff element | Trusted source at Gate 9 | Binding | Freshness requirement | Gate-9 future revalidation responsibility |
|---|---|---|---|---|
| `Gate8Result` | `is_gate8_result` (exact object) | identity-registry membership | must also require `containment_established is True` | re-check provenance; reject a copy / reconstruction / `object.__new__` |
| `containment_evidence_digest` | `Gate8Result.containment_evidence_digest` | SHA-256 over the closed containment object | recomputed & compared by Gate 9 (§16.2 inv. 3, "read-back-verified") | re-derive from the referenced containment object; mismatch → fail closed, no `consumption.json` |
| `Gate7Result` decision/digest lineage | `is_gate7_result` + `Gate8Result.gate7_result_digest` cross-check | `_gate7_result_digest` over 11 Gate-7 fields | `Gate7Result.expires_at` / posture change invalidates | re-trust `Gate7Result`; re-check `decision == "ALLOW"`; re-evaluate posture in-boundary |
| `Gate6Decision` lineage | `is_gate6_decision` (Gate 9 re-derives) | not held by `Gate8Result` — Gate 9 assembles it | PB policy version | in-boundary PB re-check |
| `Gate5Result` lineage | `is_gate5_result` (Gate 9 re-derives) | not held by `Gate8Result` | approval expiry / consumption / registry drift | in-boundary `validate_approval` re-run |
| `RuntimeDispatchIdentity` | `invocation_id` / `attempt_id` on every gate result | equal across Gate5/6/7/8/identity (§16.2 inv. 2) | n/a | assert single consistent invocation |
| `RuntimeDispatchRequestConstructionInput` | Gate 9 keyword arg | `_validate_construction_inputs` + subject/scope digest | repository / HEAD / task / prompt / adapter drift | fresh trusted read + digest compare |
| fresh capability snapshot | re-read inside the Gate-9 serialization boundary | RDGO-001 §10 last ¶ | re-read at consumption | Gate 9 resolves it itself |

**§16.2 invariants — status:** (1) exact-object provenance at every link —
`Gate8Result` supports it (identity-only, `is_gate8_result`); (2) single
consistent invocation — supported (`invocation_id` on the result; `attempt_id`
on the result — note `Gate5Result` carries no `attempt_id`, **V-13-5-2**);
(3) containment binding read-back — supported (`containment_evidence_digest`);
(4) in-boundary revalidation — Gate 9's responsibility, **not** pre-empted
here; (5) consumption only at Gate 9 — Gate 8 consumes nothing (verified);
(6) no effect — verified. **The §16 handoff contract is unchanged by
`.1R.13.4` and is independently reviewed by this phase (satisfies §17
criterion 8).**

---

## 5. V-13-1 extension adjudication — **REMAINS CLOSED; GATE-8 EXTENSION VERIFIED**

The authorised addition of `runtime_dispatch_gate8.py` trips **twelve**
point-in-time frozen-baseline production-scope / consumer-inventory guards.
All twelve were independently inspected guard-by-guard:

| Guard | Prior invariant | Authorised Gate-8 expansion | New invariant | Security property preserved | Unauthorised case that still fails |
|---|---|---|---|---|---|
| `test_gate5_..1r10 :: test_only_expected_production_files_changed_since_baseline` | `changed - _AUTHORIZED == set()` | `runtime_dispatch_gate8.py` added to `_AUTHORIZED_RUNTIME_DISPATCH_CHAIN_SURFACE` | same subset form | any file outside the authorised set → `unexpected != set()` | a 3rd unauthorised `src/pcae/**` file |
| `test_gate5_..1r11 :: test_production_scope_is_exactly_the_three_planned_files` | `changed - _AUTHORIZED_GATE_CHAIN_SURFACE == set()` + `{gate5, authority, hpac_lifecycle} <= changed` | added to `_AUTHORIZED_GATE_CHAIN_SURFACE` | same | subset + mandatory-core-present | any unauthorised file |
| `test_gate6_..1r12 :: test_only_expected_production_file_changed_since_baseline` | `set(...) <= {permission}` | `<= {permission, gate7, gate8}` | subset bound | still `<=` | any 4th file |
| `test_gate6_..1r13 :: test_1r12_production_diff_is_exactly_one_file` | `changed - _AUTHORIZED_POST_1R12_CHAIN_SURFACE == set()` + `permission in changed` | added to `_AUTHORIZED_POST_1R12_CHAIN_SURFACE` | same | subset + permission-present | any unauthorised file |
| `test_gate6_..1r13 :: test_known_pre_existing_point_in_time_scope_guard_failures_are_attributable` | `<= {gate7}` | `<= {gate7, gate8}` | subset | still `<=` | any 3rd file |
| `test_runtime_authority_..117 :: test_production_file_allowlist_matches_frozen_phase_matrix` | `changed - _authorized_surface == set()` | added to `_authorized_surface` | same | subset | any unauthorised file |
| `test_runtime_authority_..117 :: test_consumer_inventory_is_bounded_and_gate9_stays_unwired` | `projection_consumers <= {permission, gate5, gate7}` + `gate9_consumers == set()` | added `gate8` to the `<=` bound | subset; **`gate9_consumers == set()` kept EXACT** | projection consumer must be an authorised gate module; **no Gate-9 consumer** | any other projection consumer; any Gate-9 wiring |
| `test_b1_b7_..1r8 :: test_isolation_only_three_production_files_changed_since_baseline` | `set(changed) - _authorized == set()` | added `gate8` to `_authorized` | same | subset | any unauthorised file |
| `test_b1_b7_..1r8 :: test_isolation_no_gate_coordinator_or_gate9_consumption_wiring` | `projection_consumers <= {permission, gate5, gate7}` + `gate9_callers == set()` + `hpac_consumers == {runtime_authority}` | added `gate8` to the `<=` bound | subset; **`gate9_callers == set()` and `hpac_consumers == {…}` kept EXACT** | as above | any Gate-9 caller; any new HPAC consumer |
| `test_gate7_..1r13_2 :: test_production_scope_since_baseline_is_the_single_new_gate7_file` | `set(changed) == {gate7}` | `gate7 in changed and changed <= {gate7, gate8}` | **converted `==` → subset + presence** | gate7 still present; no unauthorised expansion | any 3rd file |
| `test_gate7_..1r13_3 :: test_no_downstream_production_consumer_of_gate7_result` | `hits == {gate7}` | `hits <= {gate7, gate8}` | **converted `==` → subset** | Gate 8 is the sole authorised downstream `Gate7Result` consumer | any 3rd consumer of `Gate7Result` / `is_gate7_result` |
| `test_gate7_..1r13_3 :: test_runtime_introspection_constants_unchanged_since_baseline` | `out == ["gate7"]` | `out <= {gate7, gate8}` + explicit `runtime_introspection.py not in out` | **converted `==` → subset + explicit exclusion** | `runtime_introspection.py` in particular untouched | any unauthorised file; any `runtime_introspection.py` change |

**Actively challenged (not merely "current state passes"):** a synthetic
change-set `{gate7, gate8, runtime_adapter}` was checked against the
`<= {gate7, gate8}` / `- AUTHORIZED == set()` forms — every guard rejects it
(`unexpected != set()` / `not (set <= authorized)`). The `gate9` / `hpac`
asserts remain exact-equality (`== set()` / `== {…}`), so a synthetic
Gate-9 caller / consumer / new HPAC consumer still fails. Orientation
correct in all twelve. No *functional* closure from `.1R.8` / `.1R.10` /
`.1R.11` / `.1R.12` / `.1R.13` / `.1R.13.2` / `.1R.13.3` / `.1R.117` was
weakened.

> **V-13-1 — REMAINS CLOSED; GATE-8 EXTENSION VERIFIED.**

---

## 6. Gate-9 unblocking criteria (`.1R.13.1` §17) — individual status

| # | Criterion | Status |
|---|---|---|
| 1 | Gate-7 implementation complete (`.1R.13.2` closed, `run_gate7_runtime_enforcement` with the §10 model) | **SATISFIED** — verified present + byte-unchanged. |
| 2 | Gate-7 independently verified (`.1R.13.3` closed, VERIFIED) | **SATISFIED** — `.1R.13.3` closed GATE-7. |
| 3 | Gate-8 implementation complete (`.1R.13.4` closed, `run_gate8_process_containment` with the §12 model) | **SATISFIED** — verified present, §12 model independently confirmed. |
| 4 | Gate-8 independently verified (`.1R.13.5` closed, VERIFIED, re-deriving §12 + §11.2) | **SATISFIED on promotion of this report** — verdict below. |
| 5 | §16 Gate-8 → Gate-9 handoff contract frozen & unchanged | **SATISFIED** — `git diff 6a9d650f HEAD -- docs` shows no `.1R.13.1` change; §16 re-reviewed here (§4). |
| 6 | No unresolved **blocking** findings from `.1R.13.2`–`.1R.13.5` | **SATISFIED** — all findings this chain are LOW / INFO non-blocking. |
| 7 | Runtime still non-executing (`not_implemented / Observed / observe / unavailable`; POL-005 unchanged; no real adapter) | **SATISFIED** — `pcae runtime inspect` unchanged; POL-005 byte-identical. |
| 8 | Independent verification of the §16 handoff contract | **SATISFIED** — folded into this phase (§4). |

> **`.1R.14` PRECONDITIONS SATISFIED — STILL REQUIRES SEPARATE EXPLICIT
> HUMAN AUTHORIZATION.**
>
> All eight §17 criteria are met once this report is promoted. `.1R.14`
> (Gate-9 Atomic Authority Consumption Coordinator Integration
> Implementation) and `.1R.15` (its verification) remain **frozen, BLOCKED
> pending explicit human authorization, and NOT renumbered**. This phase
> begins neither and grants no authorization. A dedicated V-2 / V-3 / V-4
> (+ V-13-3-1 / V-13-3-2 / **V-13-5-1**) contract-clarification phase remains
> an alternative non-blocking next step, also requiring its own explicit
> authorization.

---

## 7. Fixed-SHA A/B regression evidence

- **Baseline:** `6a9d650f54fb7a5c02652180f0bbcc3a41080198` (`.1R.13.3`
  completion), materialised in an isolated `git worktree` (since removed).
- **Candidate:** `72898361` (`.1R.13.4` completion = this verification's
  entry SHA).
- **Method:** `python -m pytest -p no:randomly -n0`.

| Scope | Baseline `6a9d650f` | Candidate `HEAD` | Delta |
|---|---|---|---|
| `.1R.13.4` Gate-8 suite | (file absent) | **63 passed, 0 failed** | new |
| **`.1R.13.5` verification suite (this phase)** | (file absent) | **120 passed, 0 failed** | new |
| 8 affected earlier-phase suites (`1r8`, `1r10`, `1r11`, `1r12`, `1r13`, `1r13_2`, `1r13_3`, `117`) | 327 passed, **1 failed** | 327 passed, **1 failed** | **identical** — same node |
| `tests/test_shell_gate.py` | 118 passed | 118 passed | 0 |
| wide `-k "gate8 or shell_gate or process_containment"` | n/a (no gate8) | 848 passed, 0 failed | — |
| wide `-k "gate5 or gate6 or gate7 or runtime_dispatch or permission_broker or shell_gate or process_containment or runtime_enforcement"` | pre-existing failure set | 2967 passed, 13 failed (pre-existing) | sampled 5/13 reproduce **identically** at baseline |

The one earlier-phase failure —
`test_gate6_permission_broker_production_consumption_3w1r2b1r1_1r12.py::test_gate5_results_registry_stays_empty_on_every_reject`
— is a **pre-existing cross-file test-pollution flake** (module-global
`runtime_dispatch_permission._GATE6_DECISIONS` retains objects created by
the Gate-7 suites earlier in the same process). It **passes in isolation**
and **reproduces byte-identically at `6a9d650f`** (same 4-count, same DENY
objects). The 13-node wide failure set is the HPAC / PB-freeze /
contract-wording pre-existing repo baseline; 5 sampled nodes reproduce
identically at `6a9d650f`. **`test_audit_verify_cli` (V-13-4-1) not
reproduced.**

```
CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0
UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS       = 0
```

**Verification/test subprocesses used (disclosed separately):** `pytest`;
read-only `git` history/diff/grep inspection; one isolated `git worktree`
at `6a9d650f` for the A/B (since removed); the `pcae` governance CLI. No
runtime subprocess, provider/network, credential, or hardware operation.

---

## 8. `.1R.13.4` test-quality review

63 tests inspected after independent derivation. Classification: provenance
(7), trusted-decision (3), Gate5/lineage (3), structural input guards (7),
freshness/subject-scope (4), shell-string/argv (2), effect-plan/descriptor/
executable-identity (5), cwd/env/profile/network/credential (6), Shell Gate
behaviour + no-effect (5), structural positive branch (2), Gate8Result model
(6), idempotency/no-consumption/no-Gate-9-10 (8), sole-ownership + consumer
inventory + scope (5). Every case reproduces on the current source.

**Naming honesty:** the `.1R.13.4` tests for the cwd and env rows are named
`test_cwd_outside_repository_scope_rejected` and
`test_environment_not_allowlisted_rejected` — i.e. they honestly describe
the implemented *scope / well-formedness* check, **not** the frozen §11.2
`gate8_cwd_drift` / `gate8_environment_allowlist_drift` *drift* rows. No test
name overclaims. The gap is disclosed by the honest naming (see
**V-13-5-1**) but the `.1R.13.4` implementation-document §5 anti-substitution
table silently substitutes the reason ids and drops the transport row
without flagging the deviation from the frozen matrix — a documentation
transparency gap, folded into V-13-5-1.

**No test whose name overstates what it proves** was found. The broad
four-predicate substitution in the `chain` fixture / `_synthetic_*` helpers
is clearly labelled and mirrors the accepted `.1R.13` / `.1R.13.2` /
`.1R.13.3` boundary.

---

## 9. New findings

### V-13-5-1 — LOW (non-blocking): frozen §11.2 / §25 cwd / env-allowlist / transport rows are not implemented as drift comparisons

**Finding.** The `.1R.13.1` §11.2 anti-substitution matrix and the §25
defensive-validation matrix specify three drift-rejection rows that the
`.1R.13.4` implementation does not enforce as drift comparisons:

| Frozen row | Frozen reason id | Implemented as |
|---|---|---|
| "changed cwd" (§11.2) / "cwd substitution" (§25 case 8) | `gate8_cwd_drift` | `gate8_cwd_outside_repository_scope` — a *repository-scope containment* check only. Any path at or beneath the repo root (including `src/`) passes. |
| "changed environment allowlist" (§11.2) / "environment-allowlist substitution / widening" (§25 case 9) | `gate8_environment_allowlist_drift` | `gate8_environment_not_allowlisted` — a *well-formedness* check only (non-blank, stripped `str`). An arbitrary well-formed name (e.g. `AWS_SECRET_ACCESS_KEY`) passes. |
| "changed provider/backend / transport" (§11.2) | `gate8_transport_drift` | **no implementation.** `transport_type` is the constant `"local_cli"` inside `_expected_subject_scope_binding_digest`. |

**Root cause.** `RuntimeDispatchRequestConstructionInput` (frozen `.1R.7` /
`.1R.9` §25 "no change to the 14-fact shape") carries **no cwd field and no
environment-allowlist field**, and the frozen §12.5 `containment_profile`
parameter was dropped from the implemented signature in favour of the
coordinator-assembled `effect_plan`. There is therefore **no bound
reference** in the authority chain against which Gate 8 could diff cwd or
env — a true "drift" check is not constructible without a contract change.
The frozen plan's own stated enforcement mechanism (§11.2: "recomputing the
exact `subject_scope_binding_digest` … plus a fresh executable-hash
comparison") does **not** actually cover cwd/env either, so this
inconsistency originates in the frozen `.1R.13.1` plan and is inherited by
the implementation.

**Why non-blocking (per phase-prompt §65):**
1. `effect_plan` is coordinator-assembled and trusted by frozen `.1R.13.1`
   §11.1 item 5 ("assembled by the trusted coordinator … NOT from caller
   input") — the same trust class as `descriptor_resolver`.
2. cwd, the env allowlist, and the full containment profile **are** bound
   into `containment_evidence_digest`. Frozen §16.2 invariant 3 requires the
   future Gate 9 to recompute and read-back-verify that digest against the
   referenced containment object — so a replayed `Gate7Result(ALLOW)`
   presented with a changed cwd or env allowlist produces a **different**
   `containment_evidence_digest` and is caught at the Gate-8 → Gate-9
   boundary.
3. The independently-enforced rows still hold: executable identity/hash,
   argv, descriptor/config digests, runtime-target, effect-plan-executable
   binding, `network_denied is True`, `credentials_required is False`,
   repository-scope cwd, subject/scope digest.
4. Gate 8 is **structurally unreachable in production** — no real
   `Gate7Result(ALLOW)` exists.

This is therefore **not** a "GATE-8 EFFECT-PLAN BINDING DEFECT" and **not** a
"GATE-8 DECISION-SEMANTICS DEFECT" — an executable/effect substitution that
matters (the program that would run, its identity, its arguments, its
target, its network/credential posture) **is** rejected, and cross-effect-
plan reuse is caught by the containment-evidence digest.

**Recommendation.** The separately-authorized V-2 / V-3 / V-4
contract-clarification phase should, for Gate 8, choose one of:
(a) add `cwd_ref` / `env_allowlist_ref` (or fold them into the existing
`filesystem_scope_ref` / `process_profile_ref`) to
`RuntimeDispatchRequestConstructionInput` and the subject/scope digest, so
Gate 8 can perform a true drift comparison and emit `gate8_cwd_drift` /
`gate8_environment_allowlist_drift`; **or**
(b) reword `.1R.13.1` §11.2 / §25 rows 8–9 and the `.1R.13.4` §5 table to
match the implemented "establish + attest + digest-bind" semantics and
explicitly note that cwd/env drift is caught only at the Gate-9 read-back.
Either way, the `.1R.13.1` §11.2 `gate8_transport_drift` row should be
struck or re-scoped, since `transport_type` is fixed at `local_cli` in
local-CLI-v1 and provider/backend drift is already covered by
`gate8_descriptor_config_drift`.

### V-13-5-2 — INFO: `Gate5Result` carries no `attempt_id`

Frozen §16.2 invariant 2 requires `invocation_id` **and** `attempt_id`
equal across `Gate5Result` / `Gate6Decision` / `Gate7Result` /
`Gate8Result` / `identity`. `Gate5Result` (frozen `.1R.10` model) has slots
`{_projection, sequence3_event_digest, proof_id, approval_id,
invocation_id, advisory_reasons, validated_at, _seal}` — **no
`attempt_id`**. Gate 8's lineage check binds `gate5_result.invocation_id ==
identity.invocation_id` only. The `attempt_id` binding is covered
**transitively**: Gate 7 already bound `gate5.invocation_id == identity` and
`gate6.attempt_id == identity`, and Gate 8 binds `gate7.attempt_id ==
identity.attempt_id`. No exploitable gap. The future Gate-9 handoff spec
should state the `Gate5Result` `attempt_id` binding is transitive, not
direct.

### V-13-5-3 — INFO: pre-existing cross-file test-pollution flake

`test_gate6_permission_broker_production_consumption_3w1r2b1r1_1r12.py::test_gate5_results_registry_stays_empty_on_every_reject`
asserts `len(runtime_dispatch_permission._GATE6_DECISIONS) == 0`, but that
module-global set is populated by `Gate6Decision` objects created in the
Gate-7 suites (`.1R.13.2` / `.1R.13.3` `_drive_real_*` helpers) earlier in
the same pytest process. **Passes in isolation; reproduces byte-identically
at baseline `6a9d650f`** — **not candidate-attributable to `.1R.13.4`**.
Recommend an `autouse` fixture that clears `_GATE6_DECISIONS` /
`_GATE7_RESULTS` / `_GATE8_RESULTS` per test in a future hygiene pass (same
class as O4 / the `.1R.13.3` V-13-3-3 concurrency-flake correction).

### Carried, re-checked, unchanged

- **V-13-4-1** (INFO) — `test_shell_gate.py::test_audit_verify_cli`
  transient flake under runner contention. Not reproduced here (118/118;
  isolated `-k` 1 pass). Not candidate-attributable.
- **V-13-3-1 / V-13-3-2** (LOW) — Gate 8 does **not** amplify (§3 rows
  §50 / §51).
- **V-2 / V-3 / V-4** (LOW, contract-alignment) — no Gate-8 impact; carried
  for the dedicated contract-clarification phase.
- **O1–O4 / F2–F4 / F7** — carried unchanged; F7 boundary stated verbatim
  in `runtime_dispatch_gate8.py`, threat model not broadened.

---

## 10. Gate-8 adjudication

Independent evidence confirms, for `run_gate8_process_containment`:

- Gate-7 **provenance** (`is_gate7_result`, exact-object) **and**
  `decision == "ALLOW"` (exact string equality) are **both** required —
  ✔ verified, freshly, against forged/copied/serialized/bare objects.
- A trusted `Gate7Result(decision="DENY")` **cannot reach Shell Gate** —
  ✔ rejected at flow step 3 with `build_shell_gate` call-count 0.
- Gate-5 **provenance** + **projection re-trust + revalidation** at Gate 8's
  own point of use — ✔ verified (revalidate re-runs `validate_approval`).
- **invocation / subject / scope exactness** — ✔ verified (with V-13-5-2 as
  INFO).
- **effect-plan anti-substitution** — ✔ for executable identity/hash, argv,
  descriptor digests, runtime target, effect-plan executable, shell-string;
  ▲ **partial** for cwd / env / transport (**V-13-5-1**, non-blocking —
  caught at the Gate-9 read-back).
- **executable-identity validation is sound for this non-effecting
  boundary** — ✔ `os.stat` + SHA-256 read, content hash not path equality,
  symlink-content caught; residual non-atomic TOCTOU is fail-closed and not
  overclaimed in the handoff.
- **canonical Shell Gate classifier used** — ✔ `build_shell_gate` read-only,
  no re-implementation, `shell_gate.py` byte-unchanged.
- **all Gate-8-reachable Shell Gate paths are non-effecting** — ✔
  `_call_doctor_test_run` proven structurally unreachable from Gate-8 input;
  no other effectful helper reachable.
- **Gate8Result is non-transferable** — ✔ identity-only, `__reduce__`
  raises, not subclassable, `object.__new__` rejected.
- **provenance ≠ containment success** — ✔ `is_gate8_result` is
  membership-only (no `if`, no `containment_established` in the return).
- **Gate 8 consumes nothing** — ✔ no consumption / lifecycle / Gate-9 call;
  `consumption.json` count invariant.
- **Gate-9 / Gate-10 remain absent** — ✔ AST forbidden-import + symbol scan.
- **runtime remains unchanged** — ✔ `Observed / observe / unavailable`
  after every path.

> **GATE-8 — CLOSED** at the RDGO-001 §9 process-containment / Shell-Gate
> consumption boundary for `runtime_dispatch`.

---

## 11. Final verdict

> **VERIFIED WITH NON-BLOCKING FINDINGS — GATE-8 PROCESS CONTAINMENT (SHELL
> GATE) COORDINATOR INTEGRATION COMPLETE.**
>
> `.1R.13.4`'s Gate-8 model, the `.1R.13.1` §11.2 anti-substitution matrix
> (with the disclosed non-blocking cwd/env/transport gap **V-13-5-1**), the
> Shell Gate non-effecting property, the `Gate8Result` anti-transfer
> discipline, the provenance-not-containment semantics, the
> no-consumption / no-Gate-9/10 boundary, the runtime-unchanged state, and
> the §16 Gate-8 → Gate-9 handoff contract were all **independently
> re-derived** from the primary sources and current source — not trusted
> from the `.1R.13.4` report or its tests — and hold.
>
> **Non-blocking findings:** V-13-5-1 (LOW — frozen cwd/env/transport
> anti-substitution rows implemented as scope/well-formedness checks +
> digest-binding, not drift comparisons; no bound reference exists in the
> request model; caught at the Gate-9 read-back), V-13-5-2 (INFO —
> `Gate5Result` has no `attempt_id`; binding is transitive), V-13-5-3 (INFO
> — pre-existing cross-file `_GATE6_DECISIONS` pollution flake, reproduces
> at baseline). V-13-1 REMAINS CLOSED (Gate-8 guard extensions verified,
> orientation actively challenged). No STOP condition met: no Shell Gate
> path can cause an effect; no executable/effect substitution that matters
> remains possible; no trusted negative result can progress.

---

## 12. Exact next-phase status

- **`.1R.13.5` — this phase — CLOSE.** Independent verification report
  returned. GATE-8 CLOSED (verified with non-blocking findings).
- **`.1R.14` (Gate-9 Atomic Authority Consumption Coordinator Integration
  Implementation) — PRECONDITIONS SATISFIED on promotion of this report;
  STILL FROZEN, BLOCKED pending its own separate explicit human
  authorization, NOT renumbered.** Do not begin. Do not implement Gate 9.
- **`.1R.15` (Gate-9 independent verification) — FROZEN behind `.1R.14`.**
- **Gate 10 — not implemented, not frozen with an ID.** Do not implement.
- **Alternative non-blocking next step:** a dedicated contract-clarification
  phase reconciling **V-2 / V-3 / V-4 / V-13-3-1 / V-13-3-2 / V-13-5-1**
  against PBRD-001 §4 / §14 and RDGO-001 §4 / §6 / §9 — also requiring its
  own explicit authorization.
- **`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`** — preserved.
  No delegated worker may autonomously commit / finalize / push. Only the
  primary human-authorized operator holds `.1R.13.5` lifecycle authority.
  Governed PCAE lifecycle only — no raw `git commit` / `push`, no
  `--no-verify`, no force push, no history rewrite, no hook bypass, no
  rollback.

## 13. `.1R.13.5` commits / push status

_(Filled in at finalisation — see the phase report and
`.pcae/phase-completion-metadata.json`.)_

- Fresh verification suite: 120 passed, 0 failed.
- Production source changed: **none** (`git diff --name-only <baseline> HEAD
  -- src/pcae` unchanged from `.1R.13.4`: the single
  `runtime_dispatch_gate8.py`).
- `origin/main..HEAD` at verification entry: **0**.
- Commits: `<filled at finalisation>`. Pushed: `<filled at finalisation>`.
