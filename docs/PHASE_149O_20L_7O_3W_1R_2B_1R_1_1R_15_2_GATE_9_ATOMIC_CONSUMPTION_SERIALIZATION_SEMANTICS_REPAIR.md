# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.2 — Gate-9 Atomic-Consumption Serialization-Semantics Repair

**Type:** narrow production repair (V-15-1) + bundled test-hygiene (V-15-2, V-15-3).
**Status:** IMPLEMENTED — INDEPENDENT VERIFICATION PENDING.
**Production source changed:** `src/pcae/core/runtime_dispatch_gate9.py` **only**.
**Normative contracts changed:** none.
**Consumption-record schema:** unchanged (`runtime_invocation_authority_consumption.py` byte-unchanged).
**Gate 10:** not planned, designed, or referenced beyond the frozen `.1R.15.1` §22 forward invariant.
**Execution:** not enabled. Runtime remains `not_implemented / Observed / observe / unavailable`.
**Phase-entry SHA:** `d78d9676` (`Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.2: open dedicated governed phase task`); `origin/main` at `07ba5f99` (`origin/main..HEAD = 1` at entry — the governed task-open commit).
**.1R.15.1 planning baseline:** `a56bd253` (`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_15_1_...PLANNING.md`), which froze V-15-1 = C, Path C staged (repair first), and Option B (§14).
**Governance:** governed `pcae` lifecycle only. The delegated `.3` finalization / commit / push incident remains **UNAUTHORIZED**. Only the primary human-authorized operator holds `.1R.15.2` lifecycle authority.

---

## 1. Scope as authorized

Implement **only** the narrow V-15-1 repair frozen by `.1R.15.1` (Option B),
plus the explicitly bundled V-15-2 guard conversion and V-15-3 test-hygiene
fix. Not begun: `.1R.15.3`, `.1R.15.4`. Not touched: normative contracts,
Gate 10, execution enablement, runtime capability registration, earlier
gates.

A **standalone task-memory hygiene commit** (`07ba5f99`, pushed) preceded
phase entry, reconciling one stale `active` idle task
(`post-…1R.12`) into `tasks/done/` + `tasks/DONE.md`. It changed no
`src/`, no contract, no `.1R.15.2` artifact; `pcae doctor task-memory`'s
"2 active task files" warning cleared.

## 2. Initial repository inspection (phase prompt §5)

```
git status --short                      -> clean
git status --branch --short             -> ## main...origin/main
git log --oneline origin/main..HEAD     -> (empty at bootstrap; a56bd253 latest)
git rev-list --count origin/main..HEAD  -> 0
pcae health                             -> healthy; agent lock claude-local; continuity verified
pcae check                              -> passed
pcae status coherence                   -> coherent
pcae doctor task-memory                 -> "2 active task files" (pre-existing) + historical DONE.md gaps (O4)
pcae push check                         -> nothing_to_push; phase-report trust + identity passed
pcae runtime inspect                    -> not_implemented / Observed / observe / unavailable; 0 plugins; 0 capabilities; PB execution_unavailable; non-executing
source ~/.config/pcae/telegram.env; pcae notify status -> configured, enabled, outbound-ready
pcae phase-report show --latest         -> .1R.15.1 completed, complete, pushed, origin/main..HEAD 0
```

Confirmed: `.1R.15.1` was the latest completed phase; repository clean;
no active governed phase before task open; runtime unchanged.

### 2.1 Primary source read in full

- `.1R.15.1` planning/reconciliation document (1469 lines) — Option B
  (§14), V-15-2 subset-invariant plan (§15.2), V-15-3 fix (§16.2),
  normalized gate-chain semantics (§19), Gate-10 prerequisites (§20).
- `src/pcae/core/runtime_dispatch_gate9.py` (pre-repair, 920 lines).
- `src/pcae/core/runtime_invocation_authority_consumption.py` (214 lines,
  line-by-line — the closed `_BINDING_FIELD_SETS` / `HPACMalformedError`
  exact-key check).
- `src/pcae/core/runtime_authority.py` boundaries — `ValidatedAuthorityProjection`,
  `validate_approval`, `revalidate_validated_authority_projection`,
  `_ProjectionRevalidationContext`.
- `src/pcae/core/hpac_lifecycle.py` — `HPACLifecycleStore.resolve_canonical_chain` /
  `resolve_gate5_binding_event` / `terminate*`.
- `src/pcae/core/hpac_verifier.py` — `reverify_authenticated_principal`,
  `_resolve_principal` / `_resolve_credential`.
- `src/pcae/core/human_principal_registry.py` — `resolve_canonical_principal` /
  `resolve_canonical_credential` (return `HPACResolvedRecord.record_digest`),
  `revoke_principal` / `revoke_credential`.
- Contracts (read-only authority): HPAC-001 v2.0 §41 (HPAC-REQ-095 /
  098 / 099 / 100 / 101), RDGO-001 v3.0 §10 / §10a / §15 / §17,
  RIHAC-001 v2.0 §16, RIASC-001 v3.0, PBRD-001 v2.0.
- Phase docs `.1R.15` (Gate-9 verification), `.1R.14` (Gate-9
  implementation), `.1R.9` §12 / §13.5 / §18 (Gate-9 planning).

---

## 3. The contract-embedding decision (phase prompt §6, §23, §24)

`.1R.15.1` §14 Option B specifies embedding the authority-generation
snapshot into the consumption record's `authority_binding` so Gate 10 can
re-read it. **Primary-source analysis shows the current record contract
does not permit this**, and per the phase prompt §6 / §24 the decision was
surfaced to and adjudicated by the primary operator.

### 3.1 `authority_binding` is a closed field set with no extensibility

- **HPAC-REQ-098** (`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md:1104`):
  "The eight closed binding objects contain **exactly**:" — `authority_binding`
  is exactly 12 named fields; no `additionalProperties`, no extension clause.
- **`runtime_invocation_authority_consumption.py:150`** enforces it hard:
  `set(value.keys()) != expected_fields` -> `HPACMalformedError`.
- **RDGO-001 §10 item 5** matches: "proof-validation/current-registry
  **digests**".

Adding a 13th field (`authority_generation_snapshot`) is normative schema
drift on the frozen `HPAC-AUTHORITY-CONSUMPTION/2.0` record — forbidden in
this phase (§26 / §57 / §69), assigned to `.1R.15.4`.

### 3.2 `registry_state_digest` cannot carry the snapshot within grammar

The operator authorized folding the tokens into an existing field **only
if** primary-source analysis proves `registry_state_digest` already
normatively means a digest of the *complete current registry/configuration
state* and that doing so changes neither its grammar nor its contractual
semantics.

- **HPAC-REQ-095** (`:1045`): `registry_state_digest` is "either null or
  64 lowercase hex" — a flat digest tied to the "registry ... verify"
  check at `PROOF_VERIFIED` (`:1059`).
- **HPAC-REQ-099** (`:1129`): gate 9 compares against "the exact current
  **registry/configuration** state digest and sequence-3 event." In
  HPAC/RDGO grammar (`HPAC:691`, `RDGO:160,172`) "registry/configuration"
  is enumerated **separately** from `principal / credential / presentation /
  proof / lifecycle / approval` currentness — it denotes the trust /
  installed-mechanism registry + descriptor configuration.
- **HPAC:1117**: "all other strings/digests use their owning contract
  grammar."

Folding the full mutable-authority-generation vector into
`registry_state_digest`'s pre-image would **broaden its contractual
meaning** (registry/config digest -> registry/config + all-mutable-authority-generation
digest). **That semantic permission is not provable from the frozen
contracts.**

### 3.3 Disposition

Per the operator's explicit fallback instruction: **the persisted
consumption record is left unchanged; `runtime_invocation_authority_consumption.py`
is byte-unchanged; durable / re-readable generation-state commitment for
Gate 10's second line of defense is DEFERRED TO `.1R.15.4` contract
normalization** (RDGO-001 v3.1 / HPAC-001 errata), not silently satisfied.

Final disposition distinguishes:
- **V-15-1 production race window: REPAIRED — independent verification pending**
- **durable Gate-10 generation-snapshot representation: DEFERRED TO `.1R.15.4` CONTRACT NORMALIZATION**

The in-memory `S1`/`S2` linearization-window closure — the substantive
V-15-1 defect — is fully implementable within the current schema and is
implemented here.

---

## 4. V-15-1 repair architecture (Option B, in-memory)

### 4.1 Sequence

```
Gate-8 lineage/provenance checks (steps 1-7)
  -> Gate-8 containment recomputation + read-back (step 8) [before S1]
  -> ── serialization boundary ──
  -> in-boundary revalidation battery:
       step 9   re-trust + revalidate_validated_authority_projection (re-runs validate_approval)
       step 9   recompute subject/scope binding digest
       step 11  read-only sequence-3 PROOF_VERIFIED_AND_BOUND confirm
       step 12  exact proof + approval pairing
       step 13  in-boundary runtime capability snapshot re-read
       step 14  consumption-record absence check (early already_consumed short-circuit)
  -> step 14a  CAPTURE S1 = AuthorityGenerationSnapshot   [only after the full battery]
  -> step 15   build the closed 8-item consumption record (descriptor re-resolve + hashing; NO write)
  -> step 15a  RE-READ S2 = AuthorityGenerationSnapshot
                 if S2.consumption_generation != ("absent",):  deterministic already_consumed
                 drift = first differing token in {principal, credential, approval, lifecycle}_generation
                 if drift: return ("gate9_authority_generation_drift:<token>",)  -- consume nothing
  -> step 16   consumption_store.create(proof_id, prebuilt_record)   [the sole linearization point]
```

**Zero intervening effectful I/O** between the `S2 == S1` decision and
`create`: the only statements are the comparison, the already-consumed
short-circuit, and the `create` call (asserted by
`test_no_effectful_call_between_s2_comparison_and_create`, which slices the
source between those two markers and rejects `resolve(`, `descriptor_resolver(`,
`run_gate8`, `subprocess`, `socket`, `open(`, `capability_snapshot_resolver(`,
`revalidate_`, `_capture_authority_generation_snapshot(`).

The per-`proof_id` create-only atomic primitive (`write_atomic_create_only`:
`O_EXCL` temp sibling + atomic link-if-absent) **remains the sole
linearization point and the single transaction mechanism** — no second
global lock (`.1R.9` §18). Option-A per-`proof_id` advisory serialization
was **not** added (`.1R.15.2` §22 default; no implementation evidence
justified it).

### 4.2 `AuthorityGenerationSnapshot` — token inventory

| Token | Canonical source | Derivation | Completeness argument |
|---|---|---|---|
| `principal_generation` | principal registry canonical record | `authority_generation_resolver()["principal_generation"]` = `registry.resolve_canonical_principal(principal_id).record_digest` | whole-record canonical digest: revocation (`status active->revoked` + `revoked_at`), disablement, eligibility change, or record replacement all change the record's canonical bytes; the digest is over the full record, not selected fields |
| `credential_generation` | credential registry canonical record | `...["credential_generation"]` = `registry.resolve_canonical_credential(credential_id).record_digest` | whole-record canonical digest: revocation, replacement, mechanism/public-key/binding change, status change |
| `approval_generation` | canonical approval record | `...["approval_generation"]` (trusted-resolver-supplied canonical approval digest) | whole-record digest of the immutable RIASC approval + any revocation-store state the resolver includes |
| `lifecycle_generation` | full proof lifecycle chain | `compute_canonical_digest([{sequence, state, event_digest} for each event in lifecycle_store.resolve_canonical_chain(proof_id)])` | digest over **every** event of the provenance-checked chain: a new successor, a terminal `EXPIRED`/`REVOKED`/`REJECTED` append, a transition, or a fork (`resolve_canonical_chain` raises -> fail closed) all change the tuple; **subsumes the proof-state token** (§12) — proof lifecycle status, expiry, revocation, and canonical identity are all events in this same chain, so the proof-state projection adds no coverage (deduplication proven: the chain digest is a superset commitment) |
| `consumption_generation` | `<root>/proofs/v2/<proof_id>/consumption.json` | `("absent",)` / `("present", record_digest)` / `RuntimeInvocationAuthorityConsumptionDurabilityUncertainError` propagates -> fail closed | exact canonical store state; a partial / corrupt record is never read as absent or present |

None uses a wall-clock timestamp alone, an mtime, a selected-field digest
without a completeness argument, or a process-local nonce (`.1R.15.2` §7).
Every token is reconstructible from durable state after a restart
(`.1R.15.2` §40) — the resolver reads canonical stores, `lifecycle_generation`
is a pure function of the on-disk chain, `consumption_generation` is a pure
function of the on-disk record.

`authority_generation_resolver: Callable[[], object]` is a new **trusted,
caller-supplied** dependency, mirroring the existing `descriptor_resolver`
/ `capability_snapshot_resolver` / `lifecycle_store` / `consumption_store`
DI on the coordinator. It is never request/adapter/runtime input. The
coordinator validates its return shape: a mapping of exactly
`{principal_generation, credential_generation, approval_generation}` to
non-empty (<= 256 char, stripped) strings, else
`gate9_authority_generation_snapshot_incomplete`. Non-callable ->
`gate9_invalid_authority_generation_resolver`.

### 4.3 `S1` capture point / `S2` re-read point / `S2 -> create` order

- **`S1`:** step 14a — immediately after step 14 confirms no consumption
  record exists, i.e. after the full HPAC-REQ-099 battery (steps 9-14).
  Not before current-state validation.
- **`S2`:** step 15a — immediately after step 15 finishes building the
  record (all reads, no write) and immediately before step 16's `create`.
- **`S2 -> create`:** in source order —
  `s2, s2_reasons = _capture_authority_generation_snapshot(...)` ->
  (uncertain? -> fail closed) -> (`s2_reasons`? -> fail closed) ->
  (`s2["consumption_generation"] != ("absent",)`? -> deterministic
  `already_consumed`) -> `drift = _first_authority_generation_drift(s1, s2)`
  -> (`drift`? -> `("gate9_authority_generation_drift:"+drift,)`) ->
  `consumption_store.create(proof_id, consumption_record)`.

### 4.4 New fail-closed reason ids

- `gate9_invalid_authority_generation_resolver`
- `gate9_authority_generation_snapshot_incomplete`
- `gate9_authority_generation_drift:principal_generation`
- `gate9_authority_generation_drift:credential_generation`
- `gate9_authority_generation_drift:approval_generation`
- `gate9_authority_generation_drift:lifecycle_generation`

(`consumption_generation` drift is not a rejection — a present record is a
deterministic `already_consumed`; a durability-uncertain record is
`gate9_consumption_state_durability_uncertain`, an existing reason.)

---

## 5. Threat-model results — drift injected in the S1->S2 window (phase prompt §26-§34)

All injected from inside `_build_consumption_record` (the coordinator calls
it exactly once, at step 15 — strictly after `S1`, strictly before `S2`),
mutating **real canonical stores** (not monkeypatched expectations,
`.1R.15.2` §60):

| Injection | Result | Consumption records written |
|---|---|---|
| **Principal revocation** (`registry.revoke_principal`) | `gate9_authority_generation_drift:principal_generation`; fail closed | 0 |
| **Credential revocation** (`registry.revoke_credential`) | `gate9_authority_generation_drift:...` (the shared principal/credential registry document is rewritten, so the fixed comparison order reports the first differing token — `principal_generation`; RDGO-001 §15 / `.1R.15.2` §32 first/aggregate mismatch); fail closed | 0 |
| **Lifecycle-head change** (`lifecycle_store.terminate_canonical(state="REVOKED")`) | `gate9_authority_generation_drift:lifecycle_generation`; fail closed | 0 |
| **Approval-state change** (resolver returns a changed `approval_generation` on the S2 re-read) | `gate9_authority_generation_drift:approval_generation`; fail closed | 0 |
| **Consumption record appears** (a valid canonical record installed between S1 and S2) | deterministic `already_consumed` (`gate9_already_consumed`); **no second create** | 1 (the pre-installed one) |
| **Multiple simultaneous drifts** (principal + credential) | `gate9_authority_generation_drift:principal_generation` (first in fixed order); fail closed, no create attempted | 0 |
| **Stable tokens** (side effect touches no authority source) | `status == "consumed"` — exactly one create | 1 |

`test_no_snapshot_cached_across_retry`: after a drift-blocked attempt, a
fresh call re-derives `S1` from current (now-mutated) canonical state; with
the projection-revalidation predicate monkeypatched open, `S1 == S2` (both
observe the post-mutation state) and the create proceeds — proving the
token is a pure function of **current** durable state and no stale `S1`/`S2`
is resumed.

Per `.1R.15.1` §13 / phase §26-§34: in **every** case the outcome is
fail-safe (the one-shot authority is burned, never escalated) and produces
**no external effect** — Gate 10 is absent and its frozen forward
invariant (`.1R.15` §22) mandates a full re-read + re-validation +
containment re-establishment before any effect.

---

## 6. Crash / concurrency / restart (phase prompt §35-§40)

| Scenario | Behaviour | Consumption records |
|---|---|---|
| **Crash before S2** (exception during record preparation) | `gate9_internal_error_fail_closed`; nothing consumed | 0 |
| **Crash after S2 comparison, before create** (`store.create` raises) | fail closed; nothing consumed | 0 |
| **Crash after create, before read-back** (`store.create` succeeds then raises) | the coordinator resolves, finds the durable record, returns deterministic `already_consumed` — never a second write, never a crash | 1 |
| **Retry after crash-after-create** | deterministic `already_consumed` | 1 |
| **4 concurrent contenders** (barrier-synchronised) | exactly one `status == "consumed"`; exactly one durable canonical record; the other three are `already_consumed` or fail closed — never a second success (mirrors the `.1R.14` convention, unchanged by the repair) | 1 |
| **Concurrent authority mutation** (revocation straddles a contender's S1->S2) | that contender rejects with `gate9_authority_generation_drift:*`; no consumption from a stale snapshot | 0 for that contender |

Generation tokens are reconstructible from durable state after a restart
(no process-local token required to interpret a consumption record);
record creation cannot emit malformed token bindings because **no token
binding is emitted into the record at all in this phase** (§3.3 deferral).

---

## 7. Regression preservation

| Property | Evidence |
|---|---|
| **V-13-5-1 containment read-back** | unchanged — `run_gate8_process_containment` recomputation + `gate9_containment_evidence_recomputation_mismatch` run at step 8, **before** `S1` (`test_v13_5_1_containment_readback_still_enforced` asserts source order) |
| **Gate-9 atomicity** | one canonical create-only record; proof + approval consumed together; no separate mutable consumption flags — token validation is in-memory only, emits nothing durable |
| **Replay** | identical replay -> `already_consumed`; same-proof/different-approval and cross-binding still fail closed (`.1R.14` suite, 63/63) |
| **Crash semantics** | `.1R.14` crash-before/during/after tests, unchanged (63/63) |
| **Gate9Result discipline** | `is_gate9_result` is provenance-only; `__reduce__` raises; no new downstream consumer; no bearer semantics |
| **No Gate 10** | no adapter / subprocess / socket / provider / credential / hardware import (`test_no_gate10_effect_symbols_introduced`) |
| **Runtime state** | `_runtime_execution_unavailable` check unchanged; `gate9_runtime_execution_available_unexpected` still returned for a non-`unavailable` snapshot |
| **Gates 5 / 6 / 7 / 8 production modules** | **byte-unchanged** (`git diff d78d9676 -- src/pcae/core/runtime_dispatch_{gate5,permission,gate7,gate8}.py` empty; `test_earlier_gate_modules_unchanged` parametrized) |
| **Normative contracts** | byte-unchanged (`git diff d78d9676 -- docs/contracts` empty) |
| **Consumption-record schema** | `runtime_invocation_authority_consumption.py` byte-unchanged (`test_store_module_has_no_1r15_2_edits`; `test_consumption_record_schema_is_unchanged_by_this_phase` asserts the exact 12-key `authority_binding` frozenset) |

---

## 8. V-15-2 — guard normalization (phase prompt §43-§45)

The three HPAC-foundation point-in-time zero-consumer guards trip at
baseline (`d78d9676`) on `runtime_dispatch_gate9.py`'s legitimate,
`.1R.14`/`.1R.15`-authorized imports of `hpac_foundation`,
`hpac_lifecycle`, and `runtime_invocation_authority_consumption`:

| Suite | Test |
|---|---|
| `test_hpac_foundation_independent_verification_3w1r2b1r111r31.py` | `test_new_hpac_modules_have_zero_preexisting_production_consumers` |
| `test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py` | `test_hpac_repair_has_zero_preexisting_production_consumers` |
| `test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py` | `test_foundation_has_no_production_consumers_or_gate_wiring` |

Each converted to a **phase-aware SUBSET invariant** (mirroring the ten
`.1R.14` V-13-1 conversions):

```python
AUTHORIZED_CONSUMERS = {
    ("runtime_dispatch_gate5.py", "pcae.core.hpac_lifecycle"),                          # .1R.10 / .1R.11
    ("runtime_dispatch_gate9.py", "pcae.core.hpac_foundation"),                         # .1R.14 / .1R.15
    ("runtime_dispatch_gate9.py", "pcae.core.hpac_lifecycle"),                          # .1R.14 / .1R.15
    ("runtime_dispatch_gate9.py", "pcae.core.runtime_invocation_authority_consumption"),# .1R.14 / .1R.15
}
unauthorized = set(consumers) - AUTHORIZED_CONSUMERS
assert unauthorized == set(), ...
```

The authorized set was derived by `grep` over `src/pcae/core/*.py`, not
guessed. Direction is `observed - allowed == set()` (`.1R.15.2` §44), not
reversed. No `startswith(` / wildcard allowance. Unauthorized future
consumers still fail (`test_v15_2_unauthorized_future_consumer_still_fails`
proves an extra `runtime_dispatch_gate10.py` entry makes `unauthorized`
non-empty). The HPAC-verifier trust-root asserts, the `_GATE9_RESULTS`
owner asserts, and any Gate-10 exact-empty asserts elsewhere are **not**
subset-relaxed.

**Fixed-SHA A/B:** each of the three — FAIL at `d78d9676`, PASS at HEAD
after conversion.

V-15-2 — **REPAIRED — INDEPENDENT VERIFICATION PENDING**.

---

## 9. V-15-3 — test hygiene (phase prompt §46-§48)

Three tests in
`test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py`
raw-assigned `runtime_dispatch_gate5.is_gate5_result` via
`import pcae.core.runtime_dispatch_gate5 as _g5mod; _g5mod.is_gate5_result = lambda ...`
— `test_sequence3_cross_binding_rejected`,
`test_different_proof_same_consumed_approval_is_rejected`,
`test_consumption_store_rejects_traversal_proof_id`. Each converted to
`monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is chain.g5)`
(the test signatures gained `monkeypatch`), so teardown is deterministic
and ordered. `test_v15_3_no_raw_is_gate5_result_assignment_remains` asserts
neither `_g5mod.is_gate5_result =` nor `is_gate5_result = lambda` remains
in the file; `test_v15_3_is_gate5_result_restored_after_this_module`
asserts the module attribute is the original callable after the suite.

**Cross-test pollution:** the `.1R.14` suite (63), the `.1R.15` suite (76),
and the new `.1R.15.2` suite (44) all pass run individually, together, and
interleaved; no monkeypatch state leaks across boundaries.

V-15-3 — **REPAIRED — INDEPENDENT VERIFICATION PENDING**.

---

## 10. Fixed-SHA A/B regression attribution (phase prompt §59)

**Baseline SHA:** `d78d9676` (phase entry). **Method:** `git stash` of the
working tree, run the deterministic suites, `git stash pop`. No xdist for
attribution.

Targeted set (Gate-9 impl/verify + affected HPAC-foundation guards +
adjacent Gate 5-8 suites + consumption-store suite):

| Set | Baseline `d78d9676` | HEAD (post-repair) | Delta |
|---|---|---|---|
| `.1R.14` Gate-9 integration | 63 passed | 63 passed | 0 |
| `.1R.15` Gate-9 verification | (n/a — call-signature) | 76 passed | resolver param wired; 0 functional |
| `.1R.15.2` new focused suite | — | 44 passed | new |
| 3 HPAC-foundation guard suites | 16 failed / 110 passed | 13 failed / 113 passed | **+3 pass** (the V-15-2 zero-consumer guards); the 13 remaining are pre-existing, identical at baseline |
| Gate 5 / 6 / 7 / 8 integration + verification + B1/B7/N1/N2 + runtime-authority | 383 passed | 383 passed | 0 |
| `test_hpac_authority_consumption.py` + `.1R.13.5` | 127 passed | 127 passed | 0 |

**Pre-existing, non-attributable failures** (identical set at baseline and
HEAD; unrelated to `.1R.15.2` — HPAC-foundation reproduction fixtures and
an unrelated HATP contract byte-identity test):
`test_blocking_reproduction_*` (10), `test_deterministic_authenticator_is_non_real_but_no_real_verifier_exists_to_enforce_allowlist`,
`test_deterministic_attestation_encoding_has_contract_extra_fields`,
`test_concurrent_conflicting_successors_have_one_canonical_winner`,
`test_phase_149o_18{c,d}...::test_contract_byte_unchanged[HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md]` (2).

**CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0.**
**UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.**

Concurrency stress (`test_concurrent_contenders_one_winner`,
`test_concurrent_requests_yield_exactly_one_success`): run separately in a
loop; exactly one winner every run; no second record.

`fast_green` for finalization: the targeted affected suites —
`183 passed` (`.1R.15.2` 44 + `.1R.14` 63 + `.1R.15` 76), `0 failed`. The
repo-wide `-m fast_green` marker carries ~344 pre-existing failures
unrelated to this phase and is not used as the structured field (per the
repo's finalization convention).

---

## 11. Production consumer inventory (phase prompt §61)

- **Gate-9 coordinator consumers:** none new. `run_gate9_atomic_authority_consumption`
  has no production caller (the positive path is unreachable — real Gate 7
  DENYs, real `run_gate5` never yields a `Gate5Result`).
- **Generation-token helpers** (`_capture_authority_generation_snapshot`,
  `_lifecycle_generation_token`, `_consumption_generation_token`,
  `_first_authority_generation_drift`): private to `runtime_dispatch_gate9.py`;
  no external consumer.
- **Consumption-store callers:** unchanged — only `runtime_dispatch_gate9.py`.
- **`Gate9Result` consumers:** none new; no Gate-10 consumer; no
  alternative consumption owner.

---

## 12. Runtime zero-effect proof (phase prompt §63)

At completion, over the `.1R.15.2` + `.1R.14` + `.1R.15` suites:

```
canonical local consumption writes = expected (tmp_path stores only; 0 under the repo tree)
runtime subprocess    = 0   (test infrastructure: git subprocess in 3 diff-scope assertions, disclosed)
adapter invocation    = 0
provider / network    = 0
credential operations = 0
hardware operations   = 0
Gate-10 effects       = 0
```

`pcae runtime inspect` at finalization: `not_implemented / Observed /
observe / unavailable`; 0 plugins; 0 capabilities; PB `execution_unavailable`;
non-executing — unchanged.

---

## 13. New findings

- **N-15-2-1 (informational).** `registry.revoke_credential` rewrites the
  shared principal+credential registry document, so
  `resolve_canonical_principal(...).record_digest` also moves on a pure
  credential revocation. This makes `principal_generation` and
  `credential_generation` correlated for registry-document mutations. It
  is **fail-safe** (either token moving blocks the create) and consistent
  with RDGO-001 §15's "first/aggregate mismatch" reporting convention. A
  future hardening slice could split the registry document per record;
  **not** a prerequisite for anything.
- **N-15-2-2 (carried to `.1R.15.4`).** The durable Gate-10
  generation-snapshot representation (§3.3) requires
  `authority_binding` extension or a new binding object — a normative
  schema change deferred to `.1R.15.4`. Until then, Gate 10's §22
  forward-invariant "re-validate all mutable authority as-of Gate-10
  entry" remains the only durable check; it is sufficient because Gate 10
  does not exist.
- No new **blocking** findings.

---

## 14. Implementation verdict

**GATE-9 SERIALIZATION-SEMANTICS REPAIR: IMPLEMENTED — INDEPENDENT
VERIFICATION PENDING — V-15-1 NOT YET CLOSED.**

- **V-15-1 production race window: REPAIRED — INDEPENDENT VERIFICATION PENDING.**
- **durable Gate-10 generation-snapshot representation: DEFERRED TO `.1R.15.4` CONTRACT NORMALIZATION** (not silently satisfied).
- **V-15-2 REPAIRED — VERIFICATION PENDING.**
- **V-15-3 REPAIRED — VERIFICATION PENDING.**

Final Gate-9 normalization is **not** complete; it awaits `.1R.15.3`
(verification of this repair) and `.1R.15.4` (contract normalization) +
`.1R.15.5`.

---

## 15. Recommended next phase (phase prompt §65)

**`149O.20L.7O.3W.1R.2B.1R.1.1R.15.3` — Independent Verification of the
Gate-9 Serialization-Semantics Repair.** Not begun. Requires its own
explicit human authorization. Do not begin `.1R.15.4`. Do not plan or
implement Gate 10.

The `.1R.15.3` verification must additionally re-derive the §3
contract-embedding analysis and confirm the deferral is correct (or
identify that a schema-safe durable representation was missed).

---

## 16. Governance (phase prompt §66-§67)

Governed `pcae` lifecycle only: `pcae session bootstrap`,
`pcae task transition` / `update`, `pcae commit implementation`,
`pcae phase complete`, `pcae push`. No raw `git commit` / `git push`, no
`--no-verify`, no force push, no history rewrite, no hook bypass. Only the
primary human-authorized operator holds `.1R.15.2` lifecycle authority. No
delegated worker committed, finalized, or pushed. The delegated `.3`
finalization / commit / push incident remains **UNAUTHORIZED**.

---

## 17. No-Go Confirmations

- No normative contract file changed; RDGO-001, PBRD-001, RIHAC-001, RIASC-001, HPAC-001, RPAC-001, PBPA-001, POL-005 all byte-unchanged.
- No consumption-record schema change; `runtime_invocation_authority_consumption.py` byte-unchanged; `authority_binding` remains the closed 12-field set.
- No 13th `authority_binding` field; no structured value smuggled into an existing digest field; durable snapshot representation explicitly DEFERRED to `.1R.15.4`, not silently satisfied.
- No second global lock, transaction system, or bearer object; the per-`proof_id` create-only primitive remains the sole linearization point.
- No Gate-10 design, module, symbol, phase ID, adapter, subprocess, provider, network, credential, or hardware path.
- No execution enabled; runtime remains `not_implemented / Observed / observe / unavailable`; no capability registration.
- No real FIDO2 / WebAuthn / CTAP / protected UI / physical authenticator access.
- No approval / proof / presentation / challenge / nonce consumed on any production path; no `consumption.json` created outside disposable `tmp_path` test stores.
- No third-party system, unrelated account, external credential, provider API, external network, or Dell deployment target accessed.
- No test weakened to pass; concurrency-loser tests retain the RDGO-001 §18 one-winner / one-record guarantee.
- No raw `git commit` / `git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass.
- No delegated worker committed, finalized, or pushed; only the primary human-authorized operator holds `.1R.15.2` lifecycle authority.
- No begin of `.1R.15.3` / `.1R.15.4` / `.1R.15.5`; each needs its own explicit human authorization.
- No reopening of a closed gate boundary (Gate 5 / 6 / 7 / 8); their production modules are byte-unchanged.
- No self-close of V-15-1 / V-15-2 / V-15-3; all remain INDEPENDENT VERIFICATION PENDING.

---
*Canonical implementation artifact. Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.2.*
