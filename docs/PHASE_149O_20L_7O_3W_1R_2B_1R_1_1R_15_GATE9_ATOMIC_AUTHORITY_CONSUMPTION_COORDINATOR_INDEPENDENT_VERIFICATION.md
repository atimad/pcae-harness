# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15 — Independent Verification of the Gate-9 Atomic Authority Consumption Coordinator Integration

> **Erratum — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4.** This verification
> is against RDGO-001 **v3.0** and `HPAC-AUTHORITY-CONSUMPTION/**2.0**`, and
> its non-blocking findings V-15-1 / V-15-2 / V-15-3 were carried forward.
> V-15-2 and V-15-3 were independently CLOSED by `.1R.15.3`. V-15-1 (the
> revalidation battery being adjacent to, not atomic with, the create-only
> linearization) was repaired by `.1R.15.2`, independently verified by
> `.1R.15.3`, and normalized by `.1R.15.4`: no held lock; battery + a
> zero-effectful-I/O `S1`/`S2` authority-generation-token re-check
> immediately before the create; the exact `S1` durably committed as the
> ninth binding object `authority_generation_binding` of
> `HPAC-AUTHORITY-CONSUMPTION/**2.1**` (RDGO-001 v3.1 §10; HPAC-001 v2.1
> HPAC-REQ-098/098a/099). The GATE-9 CLOSED verdict stands.

Status: **GATE-9 — CLOSED. VERIFIED WITH NON-BLOCKING FINDINGS.**

Final verdict: **VERIFIED WITH NON-BLOCKING FINDINGS — GATE-9 ATOMIC
AUTHORITY CONSUMPTION COORDINATOR INTEGRATION COMPLETE.**

Independent verification (RE-DERIVE, DO NOT TRUST) of the
`149O.20L.7O.3W.1R.2B.1R.1.1R.14` Gate-9 Atomic Authority Consumption
coordinator integration, against RDGO-001 v3.0 §10 / §10a / §1 row 9 / §17 /
§18 / §19, RIHAC-001 v2.0 §17–§19, HPAC-REQ-098/099/100/101/102, the
`.1R.9` planning document §10–§19, the `.1R.13.1` §16 Gate-8 → Gate-9
handoff contract, and the independently-verified Gate-5 / Gate-6 / Gate-7 /
Gate-8 boundaries. **No `.1R.14` claim was accepted because it appears in
that phase's report, implementation document, 63 tests, class / function
names, `_GATE9_RESULTS` membership, final file contents, or aggregate pass
counts.**

No defect was repaired. No Gate-10 code was written. No execution was
enabled. No real FIDO2 / protected UI was implemented. Runtime remains
`not_implemented / Observed / observe / unavailable`; POL-005 byte-unchanged;
real execution UNAVAILABLE.

- **Verification-entry SHA:** `b618f353` (`.1R.14` completion — "reconcile
  governed push state").
- **Immutable pre-`.1R.14` baseline:** `c1ea2c8b` (`.1R.13.5` completion).
- **`.1R.14` implementation range (independently reconstructed from fixed
  SHAs, not commit subjects):**
  - `9103d9cf` — **production implementation**: `runtime_dispatch_gate9.py`
    new (+901), the 954-line `.1R.14` test suite, and the V-13-1 phase-aware
    guard conversions across 10 earlier suites.
  - `9fba3251` — **concurrency-hardening**: `runtime_dispatch_gate9.py` +19
    (non-duplicate create error now re-resolves → deterministic
    `already_consumed` when a complete durable record is present), + one
    more V-13-1 Gate7Result-consumer guard conversion, + test updates.
  - `2806e3d9` — canonical implementation document + PROJECT_STATUS +
    CHANGELOG.
  - `e2cc7d9c` — governed task lifecycle.
  - `d90b4135` / `45a2fc14` / `b618f353` — completion-metadata / report
    staging, idle allowed-file expansion, push-state reconcile.

  The phase prompt's §5 list (`9103d9cf 9fba3251 2806e3d9 e2cc7d9c`) omits
  the three finalization commits. The true range is `9103d9cf..b618f353`;
  the only functional commits are `9103d9cf` and `9fba3251`. The production
  source diff `git diff c1ea2c8b b618f353 -- src/pcae` is **exactly**
  `src/pcae/core/runtime_dispatch_gate9.py`, `+920` lines, nothing else.
- **Fresh verification suite:**
  `tests/test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py`
  — **78 tests, 0 failed**, independently constructed (own synthetic
  provenance-substitution harness, own resolver / effect-plan / synthetic
  upstream builders, own instrumentation for the ordering proof).

---

## 1. Contracts and source inspected (in full)

RDGO-001 v3.0 (`RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md`), RIHAC-001 v2.0
(`RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md`), RIASC-001 v3.0
(`RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md`), HPAC-001 v2.0
(`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` +
`HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`), PBRD-001 v2.0
(`PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md`), RPAC-001 v1.0
(`RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`), PBPA-001
(`PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`),
`PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`, POL-005; the `.1R.9`
§10–§19 planning document, the `.1R.13.1` §16 handoff, the `.1R.13.5` Gate-8
verification, the `.1R.14` implementation document + diff;
`src/pcae/core/runtime_dispatch_gate9.py`,
`runtime_invocation_authority_consumption.py`, `runtime_dispatch_gate8.py`,
`runtime_dispatch_gate7.py`, `runtime_dispatch_permission.py`,
`runtime_dispatch_gate5.py`, `hpac_foundation.py`, `hpac_lifecycle.py`,
`runtime_authority.py`, `runtime_introspection.py`; the `.1R.14` 63-test
suite in full.

## 2. Re-derived Gate-9 contract

```
Gate 9 =
    trusted Gate8Result provenance (exact object)  +  affirmative containment
  + exact Gate7/Gate6/Gate5 lineage of ONE invocation
  + independent re-derivation of the full containment evidence
  + revalidation of mutable authority state immediately before the
    create-only atomic primitive
  + exactly one create-only, crash-consistent, read-back-verified commit of
    the closed 8-item HPAC-AUTHORITY-CONSUMPTION/2.0 record
```

Required invariant (RDGO-001 §10, §11 of `.1R.9`): **proof consumed IFF
approval consumed** — one durable record, no mutable `consumed` field, no
two-write protocol, no partial state.

## 3. Sole Gate-9 owner and consumer inventory

- `run_gate9_atomic_authority_consumption` (in
  `src/pcae/core/runtime_dispatch_gate9.py`) is the **sole** semantic owner.
  `git grep` for `run_gate9_atomic_authority_consumption` /
  `_GATE9_RESULTS` / `_GATE9_RESULT_CONSTRUCTOR_SEAL` in `src/pcae` returns
  only that file.
- `RuntimeInvocationAuthorityConsumptionStore` has exactly two references in
  `src/pcae`: its defining module and the Gate-9 coordinator. **No alternate
  semantic owner, no parallel consumption path.**
- `Gate9Result` / `is_gate9_result` have **zero** downstream production
  consumers. No `run_gate10` / `Gate10` / `adapter_dispatch` /
  `DispatchReceipt` / `SimulationDispatchEnvelope` / `.dispatch(` token
  anywhere in `runtime_dispatch_gate9.py`. The pre-existing adapter
  transports (`runtime_adapter.py`, `mock_runtime_adapter.py`) do not import
  the Gate-9 coordinator.
- `Gate8Result` / `is_gate8_result` new consumers ⊆ `{gate8, gate9}` with
  gate9 present.

## 4. Serialization boundary

The serialization boundary is the **per-`proof_id` create-only atomic
primitive itself** (`RuntimeInvocationAuthorityConsumptionStore.create` →
`hpac_foundation.write_atomic_create_only` → `O_EXCL` temp sibling + atomic
link-if-absent), exactly as frozen by `.1R.9` §18 ("do not invent a new
lock — the protected create-only commit is itself the atomic transaction").
Independently confirmed:

- gate9.py imports no `threading` / `fcntl` / `filelock` / `multiprocessing`
  / `asyncio`; defines/uses no `Lock` / `RLock` / `flock` / `Semaphore` /
  `FileLock` (AST scan).
- exactly **one** `.create(` call site in the module.
- no second transaction mechanism, no advisory lock, no nested acquisition.

Call flow (source-level): steps 1–8 (provenance + lineage + Gate-7 digest +
early authority pre-check + Gate-8 re-run for containment recomputation) →
step 9 projection re-trust + `revalidate_validated_authority_projection`
(re-runs `validate_approval`) → step 9 subject/scope digest re-compare →
step 11 sequence-3 `PROOF_VERIFIED_AND_BOUND` confirm (read-only
`resolve_gate5_binding_event`) → step 12 exact proof+approval pairing →
step 13 capability-snapshot re-read (fail closed unless still `unavailable`)
→ step 14 record-absence `resolve` → step 15 pure in-memory record build →
step 16 the one `create` → step 17 read-back `resolve` + digest compare.

## 5. Independently verified operation order (§19 / §20)

Instrumented (`.1R.15` suite `test_critical_ordering_...`) spies on
`revalidate_validated_authority_projection`,
`resolve_gate5_binding_event`, the capability resolver, `store.resolve`,
`store.create`. Observed order on the (test-path-only) success path:

```
revalidate_projection  <  sequence3_resolve  <  capability_reread
     <  store_resolve (absence check)  <  store_create   (exactly once)
```

- revalidation strictly precedes the single durable create;
- the absence-check `resolve` is **immediately** before `create` (adjacent
  in the instrumented trace);
- capability re-read occurs **after** projection revalidation (inside the
  battery, not merely at entry);
- `test_no_effectful_step_between_last_revalidation_and_create` slices the
  source between step 13 and step 16 and confirms no `subprocess` / `open(`
  / `socket` / `Popen` / `sleep` / network token — only pure record
  construction and the single absence-check `resolve`.

**Finding V-15-1 (LOW, non-blocking).** RDGO-001 §10 ("gate 9 revalidates …
**while holding the protected evidence-store serialization boundary**") and
`.1R.13.1` §16.2 invariant 4 (same wording) describe a held lock spanning
the revalidation battery. The implementation holds **no** lock across the
battery; it revalidates *immediately before* the create-only primitive.
`.1R.9` §18 is itself internally inconsistent — it says both "acquire [the
lock] before the §12 battery so two racers cannot both pass revalidation"
**and** "do not invent a new lock — the create IS the transaction." The
implementation follows the latter. Consequence, demonstrated by
`test_v15_1_residual_revalidate_to_create_window`: a revocation landing
*after* the in-boundary revalidation but *before* the atomic create is not
caught — the record is still written (residual TOCTOU window = one racer's
step-9→16 duration). **Non-blocking** because (a) `.1R.9` §18 froze the
create-only primitive as the boundary and forbids a second lock; (b) **no
Gate-10 effect follows** consumption; (c) Gate 10 MUST independently re-read
the durable record + re-validate — `is_gate9_result` is provenance-only, a
frozen forward invariant enforced in-source; (d) the production path is
unreachable; (e) Gates 5–8 were all CLOSED with the identical
"revalidate-immediately-before-the-atomic-step" pattern. Same doc-vs-impl
class as V-13-5-1. **Recommend the contract-clarification phase reconcile
RDGO-001 §10 / `.1R.13.1` §16.2-inv-4 / `.1R.9` §18** to the create-only-
primitive-as-boundary model.

## 6. Gate8 provenance and affirmative containment

- `is_gate8_result` is exact-object registry membership only. `None`,
  `object.__new__(Gate8Result)`, a duck-typed lookalike, `copy.copy` /
  `copy.deepcopy` / `pickle` (all raise `TypeError`) → rejected
  `gate9_untrusted_gate8_result`.
- Provenance ≠ containment: a **trusted negative** `Gate8Result`
  (`is_gate8_result(neg) is True`, real Gate-8 output for `installed=False`)
  is a hard stop `gate9_gate8_containment_not_established` **before any store
  access** — instrumented `store.create` **and** `store.resolve` spies both
  show **zero** calls; zero `consumption.json` written.

## 7. Gate7 / Gate6 / Gate5 lineage results

- Gate 7: `is_gate7_result` required **and** `decision == "ALLOW"`;
  `Gate7Result(DENY)` (the real Gate-7 output today) → hard stop.
- Gate 6: `is_gate6_decision` required **and** `decision == "ALLOW"`.
- Gate 5: `is_gate5_result` required.
- Gate-7 lineage digest: `gate8_result.gate7_result_digest` is cross-checked
  against `_gate7_result_digest(gate7_result)` recomputed from the handed
  trusted `Gate7Result`; a tampered `evaluated_input_digest` → rejected
  `gate9_gate7_lineage_mismatch`. Gate8Result is **not** a bearer shortcut.
- Single invocation: `invocation_id` + `attempt_id` equal across
  g5/g6/g7/g8/identity, `request_id` equal across g6/g7/g8; any
  cross-invocation / cross-attempt / cross-request mixture → rejected
  `gate9_invocation_binding_mismatch`.

## 8. Attempt / request lineage (§17; V-13-5-2 carried)

`Gate5Result.__slots__` carries **no** `attempt_id`. The coordinator never
references `gate5_result.attempt_id`; attempt binding is **transitive**
through `gate6_decision.attempt_id` / `gate7_result.attempt_id` /
`gate8_result.attempt_id` == `identity.attempt_id`. **V-13-5-2 confirmed
exact** — the implementation makes no direct Gate-5 attempt-binding claim.

## 9. Sequence-3 binding (§25; V-2 / V-3 carried)

Gate 9 confirms sequence-3 read-only via
`lifecycle_store.resolve_gate5_binding_event(proof_id)`: requires
`record.state == PROOF_VERIFIED_AND_BOUND`, `binding.approval_id` /
`invocation_id` / `principal_id` match, `record.event_digest ==
event.record_digest` **and** `== gate5_result.sequence3_event_digest`. A
tampered `sequence3_event_digest` → `gate9_sequence3_event_digest_unverified`;
a cross-binding approval → `gate9_sequence3_cross_binding`; absent → the
structural lifecycle-store type guard fires first
(`gate9_invalid_lifecycle_store`), else
`gate9_sequence3_proof_verified_and_bound_absent`. Gate 9 derives authority
from the re-trusted `gate5_result.projection` object and the trusted
lifecycle event, **never** the disputed "which gate creates sequence 3"
wording (V-2 / V-3) — **NOT blocking at consumption**.

## 10. In-boundary drift (principal / credential / proof / approval)

`revalidate_validated_authority_projection` re-runs `validate_approval`
(RIHAC-001 §16) inside the battery → principal revocation, credential
revocation, proof expiry, approval expiry, prior-consumption state, and
principal-identity drift after Gates 5–8 all fail closed
`gate9_stale_validated_authority_projection` with **zero**
`consumption.json`. A projection that is trusted at the step-7a pre-check
but untrusted at the step-9 in-boundary check (spy flips on 2nd call) →
rejected, no record. `proof A + approval B` (projection.approval_id ≠
gate5_result.approval_id) → `gate9_proof_approval_pairing_mismatch` /
`gate9_sequence3_cross_binding`.

## 11. Containment-evidence read-back (V-13-5-1 — decisive, §27)

Gate 9 **re-runs `run_gate8_process_containment`** over the same trusted
upstream objects + a freshly re-resolved descriptor / executable /
repository-scoped cwd (instrumented spy confirms the re-run happens), then
requires `containment_evidence_digest` / `effect_plan_digest` /
`live_preflight_digest` / `gate7_result_digest` to **equal** the handed
`Gate8Result`'s. This is **not a digest self-comparison**: feeding a
structurally-valid but *different* effect plan (cwd `/tmp`, argv change,
env-allowlist change, `network_denied=False`, `child_process_policy`
change, `supervision_ref` change, `resource_limit_ref` change) or a
different executable (`sha256` / `version` change) → rejected
`gate9_containment_recomputation_failed` /
`gate9_containment_evidence_recomputation_mismatch` **before any store
write**; the identical-input positive control reconciles and consumes.

**V-13-5-1 — SATISFIED / CLOSED FOR THE RUNTIME-DISPATCH CONSUMPTION
PATH.** The previously-deferred cwd / env / containment-profile dimensions
are covered here because the Gate-8 re-run recomputes
`containment_evidence_digest` over the freshly re-resolved cwd + effect
plan, and Gate 9 read-back-verifies it. The residual `.1R.13.1` §11.2 / §25
contract-text inconsistency (no bound `cwd_ref` / `env_allowlist_ref` field
in `RuntimeDispatchRequestConstructionInput`; the "transport drift" row) is
**documentation debt for the contract-clarification phase**, not a
binding / decision defect.

## 12. cwd / env / profile / executable / argv / descriptor / target drift

All rejected by the §11 containment re-run before commit — see the
parametrized `test_containment_evidence_drift_rejected_before_commit`
(7 vectors) + `test_effect_plan_digest_independently_reconstructed`.

## 13. effect-plan / live-preflight / Gate7-result digest; capability snapshot

- effect-plan digest independently reconstructed by the Gate-8 re-run (a
  handed digest is not self-authenticating).
- live-preflight digest re-derived by the Gate-8 re-run and compared.
- Gate7-result digest compared against the current trusted `Gate7Result`
  (§7).
- capability snapshot: `capability_snapshot_resolver()` is **called** inside
  the battery (spy confirms); anything other than
  `Observed / observe / unavailable` (including `None`, `{}`, a partial
  dict, a string, a list) → `gate9_runtime_execution_available_unexpected`,
  zero records. No capability elevation — `runtime_introspection` constants
  byte-unchanged and re-asserted after Gate 9 runs.

## 14. NON-REAL defense in depth

With no provenance substitution, hand-built synthetic upstream objects are
not registry members → Gate 9 fails closed at the first gate
(`gate9_untrusted_gate8_result`). The real `run_gate5` on a canonical
deterministic chain returns `(None,
("non_real_authenticated_principal_cannot_validate_production_approval",))`
— **no `Gate5Result` is ever produced in production**, so Gate 9 can never
receive one. Positive production Gate-9 consumption path reachable today =
**NO**.

## 15. Canonical consumption-record schema (§41–§44)

`HPAC-AUTHORITY-CONSUMPTION/2.0`, top-level keys exactly
`{consumption_schema_version, record_digest, request_identity,
repository_task_binding, target_binding, prompt_binding, authority_binding,
pb_binding, runtime_enforcement_binding, dispatch_binding}`.
`request_identity` = `{invocation_id, attempt_id, idempotency_key}`.
`authority_binding` = the 12-field closed set with `authority_contract_version
== "RIHAC-001/2.0"`. `dispatch_binding.state == "dispatch_attempted"`. No
extra uncontracted field, no missing required field (the inert store's
closed-field-set check enforces this on `create` **and** `resolve`).

## 16. Single-record atomicity; RIHAC immutability

- proof + approval + presentation + challenge are consumed by **one**
  create-only write; there is **no mutable `consumed` field** anywhere
  (`grep` for `consumed = True` / `consumed=True` in gate9.py → none).
- gate9.py does not import `runtime_invocation_approval_store`, holds no
  `approval_store` reference, and calls no lifecycle writer
  (`record_verified` / `record_assertion` / `open_challenge` / `fixture_`);
  the RIHAC repository approval store is **never mutated** (HPAC-REQ-102).

## 17. Store provenance / containment (§45–§46)

- A schema-shaped file planted by hand at a **different** `proof_id` root
  does not make *this* invocation's proof consumed.
- Traversal / absolute / `..` `proof_id` values are refused
  (`require_safe_relative_id_component`) before any write — Gate 9 surfaces
  a `gate9_sequence3_*` / `gate9_internal_error_fail_closed` fail-closed.

## 18. First consumption / replay / concurrency (§47–§55)

- **First consumption** (test-path only): exactly one durable record,
  `status == "consumed"`, `reasons == ()`, read-back digest match, **zero**
  writes anywhere under the repo tree.
- **Identical replay** (×3): deterministic
  `Gate9Result(status="already_consumed")` + `("gate9_already_consumed",)`,
  never a second write, never a retriable error.
- **Same handed `Gate8Result` replay**, **same proof / different approval**,
  **different proof / same approval** → never a second success (rejected or
  `already_consumed`); still exactly one record.
- **True concurrency**: 4, 8, and 16 barrier-synchronized contenders against
  the same canonical proof/approval pair → **`consumed` count == 1**; every
  other racer ∈ `{already_consumed, fail_closed}`; exactly one complete
  read-back-valid record. Repeated **12×** with fresh proof roots and 6
  contenders each → `consumed` count == 1 and record count == 1 **every
  time**.
- **Concurrency-loser classification** (`.1R.14` `9fba3251` hardening,
  independently confirmed): a loser receiving `HPACDuplicateError` **or** a
  non-duplicate create error, when a complete valid canonical record is
  durably present, deterministically resolves to `already_consumed` — no
  ambiguous retry state.

## 19. Crash / restart / corrupt-record (§56–§61)

- **Crash before commit** (`create` raises): `gate9_atomic_commit_failed`,
  `resolve` → `None`, zero records, authority **unconsumed**; a retry after
  "restart" (real `create`) then succeeds — proving nothing was consumed.
- **Crash during the atomic primitive**: `write_atomic_create_only`'s
  `O_EXCL` temp sibling + atomic link means a partial temp artifact never
  becomes authoritative; the canonical record is either absent or complete.
- **Crash after commit** (`create` succeeds then raises): the coordinator
  detects the durable record → `already_consumed`, one record, never a
  second write, never continue-to-Gate-10; an independent retry also reports
  `already_consumed`.
- **Restart**: after `_GATE9_RESULTS.clear()` (fresh-process simulation) a
  brand-new store object over the same root still reports `already_consumed`
  — the **durable record alone** determines consumed state, no dependency on
  the process-local registry.
- **Restart after pre-commit failure**: fresh store sees `resolve` →
  `None` (unconsumed).
- **Corrupt / truncated record** and **`record_digest` mismatch**:
  `resolve` raises `...DurabilityUncertainError` →
  `gate9_consumption_state_durability_uncertain`, fail closed; corruption is
  **never** treated as "unconsumed → retry"; the file count stays 1.

## 20. Gate9Result provenance / anti-transfer / not-success (§62–§65)

- not caller-constructable (`_seal` guard), not subclassable
  (`__init_subclass__` raises), not serializable (`__reduce__` raises),
  identity-only `==` / `hash` (`self is other` / `id(self)`).
- `object.__new__(Gate9Result)`, `None`, a `copy` / `deepcopy` /
  `pickle` → `is_gate9_result` **False**.
- `is_gate9_result(x) is True` means **only** "produced by Gate 9" — both
  the `consumed` and the `already_consumed` results are registry members.
  It does **not** mean successful consumption. The in-source forward
  invariant for Gate 10 (`status == "consumed"` **and** re-read the durable
  record) is present verbatim.
- A trusted non-success (`already_consumed`) result carries **no** Gate-10
  licence.

## 21. Absolute Gate-9 / Gate-10 separation; runtime zero-effect (§66–§67, §81)

- AST scan: gate9.py imports no `subprocess` / `socket` / `pty` / `os` /
  `requests` / `httpx` / `urllib` / `asyncio` / `multiprocessing` /
  `ctypes` / `fcntl` / `ssl` / `selectors` / `threading` / `fido2` /
  `webauthn` / `ctap` / `runtime_adapter` / `mock_runtime_adapter`; no
  `Popen` / `os.system` / `.dispatch` / `.run` / `.connect` / `.sendall` /
  `.spawn*` / `.exec*` call node.
- The only effect of a Gate-9 run is **one create-only write to the
  caller-supplied local canonical consumption store** (a `tmp_path` store in
  every test — never the production-resolved `HPAC_PROTECTED_ROOT`).
- `runtime_introspection` constants (`Observed` / `observe` /
  `unavailable`) re-asserted unchanged after Gate 9 runs.
- Subprocesses used by this verification: `pytest`, read-only `git`
  inspection, one `git worktree` at `c1ea2c8b` (removed), the `pcae`
  governance CLI. **Runtime subprocess = 0; adapter invocation = 0;
  provider / network = 0; credential operations = 0; hardware operations =
  0; Gate-10 effects = 0.**

## 22. V-13-1 guard extension (§74) + new finding V-15-2

The 10 phase-aware SUBSET conversions in `.1R.14` were re-checked
guard-by-guard: subset orientation (`changed - AUTHORIZED == set()` /
`x <= {AUTHORIZED}`) still fails an unauthorized production-file /
projection-consumer / Gate-symbol-consumer expansion; the `hpac_verifier`
consumer-inventory asserts stay EXACT; the Gate-10-consumer exact-empty
asserts and the `_GATE8_RESULTS` owner assert stay EXACT. Fixed-SHA A/B of
all 10 touched suites: **511 passed / 0 failed at BOTH `c1ea2c8b` and
`b618f353`.**

**Finding V-15-2 (LOW, non-functional, process).** `.1R.14`'s V-13-1
extension is **incomplete**: three additional point-in-time
"zero-production-consumers" guards were **not** converted and now trip on
gate9.py's legitimate imports of `hpac_foundation` /
`runtime_invocation_authority_consumption` / `hpac_lifecycle`:

- `test_hpac_foundation_independent_verification_3w1r2b1r111r31.py::test_new_hpac_modules_have_zero_preexisting_production_consumers`
- `test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py::test_hpac_repair_has_zero_preexisting_production_consumers`
- `test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py::test_foundation_has_no_production_consumers_or_gate_wiring`

Fixed-SHA A/B: **PASS at `c1ea2c8b`, FAIL at `b618f353`.** These assert
historical import-scope, not behavior — non-functional. Recommend the future
hygiene / contract-clarification phase re-baseline them exactly as `.1R.14`
did for the other 10 (add `runtime_dispatch_gate9.py` to the sanctioned
consumer set).

## 23. Gate-5 / 6 / 7 / 8 regressions (§75)

None. Gate 5, 6, 7, 8 coordinators + `shell_gate.py` +
`runtime_introspection.py` + `permission_broker_foundation.py` +
`hpac_verifier.py` + `hpac_lifecycle.py` + `runtime_authority.py` +
`runtime_invocation_authority_consumption.py` are **byte-identical**
`c1ea2c8b → b618f353`. Gate 5–8 provenance / no-effect / non-consumption
semantics unweakened. **Gate 5 CLOSED / Gate 6 CLOSED / Gate 7 CLOSED /
Gate 8 CLOSED — all reconfirmed.**

## 24. Production-file scope (§76) + contract identity (§77)

- `git diff --name-only c1ea2c8b b618f353 -- src/pcae` = **exactly**
  `["src/pcae/core/runtime_dispatch_gate9.py"]`.
- RDGO-001, RIHAC-001, RIASC-001, HPAC-001 (both files), PBRD-001, RPAC-001,
  PBPA-001, PB-production-consumption contract + the 11 adjacent modules
  listed in §23 — **`git diff c1ea2c8b b618f353 -- <path>` empty for every
  one.** No contract cleanup in `.1R.15`.

## 25. `.1R.14` test-quality review (§79) + new finding V-15-3

The 63 `.1R.14` tests were classified: provenance (7), lineage (8),
in-boundary revalidation (9), containment read-back (4), atomicity (4),
concurrency (2), crash/recovery (5), result discipline (6), isolation /
no-effect (7), invariant guards / scope (11). Coverage is genuine and the
assertions match what the names claim, with these notes:

- `test_sequence3_absent_rejected` asserts
  `gate9_invalid_lifecycle_store` (the structural type guard fires before
  the sequence-3 lookup) — the name slightly overstates; it proves the
  type guard, not a sequence-3-absent path. Minor, non-blocking.
- `test_copied_reconstructed_serialized_gate8_result_rejected` feeds
  `object()` when `copy.copy` raises — it proves "a non-registry object is
  rejected," which is correct, but the copy-branch is never actually
  exercised (Gate8Result is copy-protected). Harmless.

**Finding V-15-3 (INFO, test-quality).** Three `.1R.14` tests
(`test_sequence3_cross_binding_rejected`,
`test_proof_approval_pairing_mismatch_rejected` neighbours, and
`test_consumption_store_rejects_traversal_proof_id` — lines ~503 / ~623 /
~865) mutate `runtime_dispatch_gate5.is_gate5_result` by **raw module
assignment** (`_g5mod.is_gate5_result = lambda ...`) instead of
`monkeypatch.setattr`. `monkeypatch` teardown in later tests then captures
and restores the **stale closure**, not the original function, leaving
`runtime_dispatch_gate5.is_gate5_result` pointing at a dead lambda after the
file completes. No functional production impact and harmless within the file
(every test re-substitutes via the `chain` fixture); the `.1R.15` suite uses
`monkeypatch` exclusively. Recommend a one-line fix in the hygiene phase.

## 26. Fixed-SHA A/B (§80) + contention stress

Baseline `c1ea2c8b` in an isolated `git worktree`; deterministic
`-p no:randomly -n0` for the guard suites and `-n auto` for the wide sweep.

| Selection | `c1ea2c8b` | `b618f353` | Delta |
|---|---|---|---|
| 10 V-13-1-touched guard suites | 511 pass / 0 fail | 511 pass / 0 fail | none |
| wide `-k "gate5 or gate6 or gate7 or gate8 or gate9 or permission_broker or runtime_dispatch or runtime_authority or hpac"` | 41 fail / ~2400 pass | 45 fail / 2412 pass | +4 nonpassing |
| `.1R.15` suite (78) — random ×3 + xdist | n/a (file absent) | 78 pass every run | stable |
| `.1R.15` + `.1R.14` together (139) | n/a | 139 pass | — |

The **4** wide-sweep nodes failing at HEAD-but-not-baseline:

1–3. The three V-15-2 HPAC-foundation scope guards — **attributable,
   non-functional**, disclosed above.
4. `test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py::test_concurrent_conflicting_successors_have_one_canonical_winner`
   — **pre-existing repo flake**: reproduces **2/5 in isolation at
   `c1ea2c8b`** with gate9.py absent. This is the carried **V-13-5-3**
   (`_GATE6_DECISIONS` / successor cross-file pollution), **not
   candidate-attributable**. The comm-diff mis-listed it only because the
   single wide run happened to pass it at baseline and fail it at HEAD;
   isolated repetition confirms it is order/contention-sensitive at both
   SHAs.

The remaining 41 wide-sweep failures reproduce identically at `c1ea2c8b`
(point-in-time "no PB files touched" / "byte-unchanged-since-freeze" /
"consumer scope inventory" guards from unrelated earlier phases, and the
V-2/V-3/B7 contract-wording debt tests) — pre-existing, not
candidate-attributable.

**CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0.**
**UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.**
(3 attributable **non-functional** guard trips = V-15-2, disclosed.)

## 27. Carried non-blocking debt — disposition at actual consumption

| ID | Disposition |
|---|---|
| **V-2 / V-3** | Gate 9 confirms sequence-3 via the trusted lifecycle event + re-trusted projection; never relies on "which gate creates sequence 3" wording. **NOT blocking.** One-shot authority semantics are unaffected. |
| **V-4** | Gate 9 consumes the trusted `gate5_result.projection` object + trusted upstream gate objects and their digests; it never reopens the 3-vs-7-field `human_authority_binding` shape. No security distinction lost. **NOT blocking.** |
| **V-13-3-1** | Gate 9 invents **no** PB-policy re-evaluation at consumption; `GATE9_ADVISORY_REASONS` surfaces `policy_drift_requires_fresh_pb_re_evaluation` as **advisory only** (mirrors Gate 5/7), never a licence to skip a check. **NOT blocking.** |
| **V-13-3-2** | Gate 9 does not treat `matched_no_go_ids` completeness as authority; it records `list(gate6_decision.matched_no_go_ids)` into `pb_binding` as evidence only. **NOT blocking.** |
| **V-13-5-1** | **SATISFIED / CLOSED for the runtime-dispatch consumption path** (§11). Residual §11.2/§25 contract-text inconsistency = documentation debt for the contract-clarification phase. |
| **V-13-5-2** | Transitive attempt-id semantics **confirmed exact** (§8). |
| **V-13-5-3** | Pre-existing `_GATE6_DECISIONS` cross-file flake, reproduces at baseline (§26). Not Gate-9. |

## 28. New findings this phase

| ID | Severity | Summary |
|---|---|---|
| **V-15-1** | LOW / non-blocking | The §12 in-boundary revalidation battery is **not** executed under a held serialization lock; it runs immediately before the create-only atomic primitive. RDGO-001 §10 / `.1R.13.1` §16.2-inv-4 "while holding the protected serialization boundary" vs `.1R.9` §18 "do not invent a new lock / the create IS the transaction" — internally inconsistent frozen text; implementation follows §18. Residual revalidate→create TOCTOU window; **no Gate-10 effect possible**; Gate 10 must re-read + re-validate. Reconcile in the contract-clarification phase. |
| **V-15-2** | LOW / non-functional | `.1R.14`'s V-13-1 extension missed 3 point-in-time HPAC-foundation "zero-production-consumers" guards; they trip on gate9.py's legitimate `hpac_foundation` / `runtime_invocation_authority_consumption` / `hpac_lifecycle` imports. A/B PASS at `c1ea2c8b`, FAIL at `b618f353`. Re-baseline in the hygiene phase. |
| **V-15-3** | INFO / test-quality | 3 `.1R.14` tests raw-assign `runtime_dispatch_gate5.is_gate5_result` instead of `monkeypatch.setattr`, leaving a stale closure module-installed after the file. No functional impact. |

## 29. Gate-9 adjudication

**GATE-9 — CLOSED.** Independent proof established that:

- Gate8 provenance (exact object) **and** affirmative
  `containment_established is True` are enforced, the latter as a hard stop
  before any store access;
- the entire gate lineage (Gate 7 ALLOW + digest, Gate 6 ALLOW, Gate 5
  provenance, one invocation / attempt / request) is exact;
- mutable authority state is revalidated immediately before the create-only
  atomic primitive — **subject to V-15-1** (revalidation is not performed
  under a held lock; the frozen plan `.1R.9` §18 defines the create-only
  primitive as the boundary and forbids a second lock, and the residual
  window produces no effect);
- the full containment evidence is **recomputed** (Gate-8 re-run), not
  echoed — **V-13-5-1 closed for this path**;
- proof + approval are consumed **atomically** by one durable record;
- **exactly one** concurrent winner exists (4 / 8 / 16 + 12×6 stress);
- replay is **deterministic** `already_consumed`;
- crash-before → unconsumed / retriable; crash-after → durably consumed;
  corrupt → fail closed;
- **canonical durable state controls restart** (no dependency on
  `_GATE9_RESULTS`);
- result provenance (`is_gate9_result`) is **not** confused with success;
- **no Gate 10 / no external effect** exists or is reachable.

## 30. Next chapter after closure (§84)

Gate 9 closes; **do not immediately implement Gate 10.** Gate 10 has **no
frozen phase ID** — do not invent one. Recommended next step (each needs its
own explicit human authorization; this phase begins neither and grants no
authorization):

1. **A dedicated contract-clarification / normalization phase** reconciling
   V-2 / V-3 / V-4 / V-13-3-1 / V-13-3-2 / **V-13-5-1** / **V-15-1** against
   PBRD-001 §4 / §14 and RDGO-001 §4 / §6 / §9 / §10 / §11, and folding in
   the **V-15-2** guard re-baseline and the **V-15-3** test-quality fix; or
2. **a Gate-10 architecture / planning phase**, only after (1).

## 31. Governance

DELEGATED `.3` FINALIZATION / COMMIT / PUSH: **UNAUTHORIZED** — preserved.
No delegated worker committed, finalized, or pushed. No raw `git commit` /
`git push`, no `--no-verify`, no force push, no history rewrite, no hook
bypass, no rollback. All lifecycle actions ran through the governed `pcae`
CLI under the primary human-authorized operator's `.1R.15` authority.

## 32. `.1R.15` commits / pushed status / origin

- Commits: `9e9175d8` (task lifecycle) … (test suite, this document,
  PROJECT_STATUS + CHANGELOG, task close, staged completion metadata +
  report, push reconcile) — see the changelog and `git log` for the exact
  final range.
- Pushed: recorded at finalization.
- `origin/main..HEAD` after finalization: recorded at finalization.

---
*Canonical independent-verification report. `.1R.15`.*
