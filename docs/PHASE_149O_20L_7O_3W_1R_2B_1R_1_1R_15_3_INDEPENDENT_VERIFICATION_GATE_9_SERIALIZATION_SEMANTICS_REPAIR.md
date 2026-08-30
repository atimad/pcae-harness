# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.3 — Independent Verification of the Gate-9 Atomic-Consumption Serialization-Semantics Repair

**Status: INDEPENDENTLY VERIFIED — GATE-9 SERIALIZATION-SEMANTICS REPAIR COMPLETE**
with the explicit qualification: **DURABLE GATE-10 GENERATION-SNAPSHOT
REPRESENTATION: DEFERRED TO `.1R.15.4` CONTRACT NORMALIZATION.**

- **V-15-1 — CLOSED FOR THE GATE-9 SERIALIZATION WINDOW.** Durable Gate-10
  snapshot representation deferred to `.1R.15.4` (not conflated with the
  window closure).
- **V-15-2 — CLOSED.**
- **V-15-3 — CLOSED.**

RE-DERIVE, DO NOT TRUST. No `.1R.15.2` claim was accepted because it appears
in that phase's report, its 44 tests, helper names,
`AuthorityGenerationSnapshot`, `_GATE9_RESULTS` membership, or its pass
counts. Every conclusion below is re-derived from the primary contracts
(RDGO-001 v3.0 §10 / §15 / §17, HPAC-REQ-095 / 098 / 099 / 100 / 101,
`.1R.9` §12 / §18, `.1R.15.1` §14 / §17 / §19 / §20) and current production
source.

**No production defect was repaired in this phase. No normative contract
was modified. `.1R.15.4` was not begun. Gate 10 was not planned, designed,
or assigned an ID. Execution was not enabled.** Runtime remains
`not_implemented / Observed / observe / unavailable`; POL-005 byte-unchanged;
real execution UNAVAILABLE; deterministic authentication NON_REAL.

---

## 0. Verification coordinates

| Item | Value |
|---|---|
| **Verification-entry SHA** | `735674f7` (`.1R.15.2` completion — "reconcile governed push state") |
| **Immutable pre-repair baseline** | `d78d9676` (`.1R.15.2` phase-entry — "open dedicated governed phase task"; `runtime_dispatch_gate9.py` still pre-repair here) |
| **`origin/main` at entry** | `735674f7`; `git rev-list --count origin/main..HEAD` = 0 |
| **Fresh verification suite** | `tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py` — 56 tests, 0 failed, independently constructed (own `_Recorder` call-order instrumentation, own source-slice analyzer, own real-store mutators; the `.1R.14` provenance-substitution rig + `tmp_path` store reused verbatim as `.1R.15` did) |

### 0.1 Exact `.1R.15.2` implementation range (reconstructed from fixed SHAs, not commit subjects)

| SHA | Role | `src/pcae` touched |
|---|---|---|
| `07ba5f99` | standalone task-memory hygiene (pre-entry, pushed): stale `post-…1R.12` idle task → `tasks/done/` + `tasks/DONE.md` | none |
| `d78d9676` | **governed phase-entry** — opens the `.1R.15.2` task only | none |
| `b32619e5` | **the sole production implementation commit** — `runtime_dispatch_gate9.py` `+262/−0` (net); the 599-line `.1R.15.2` focused suite; V-15-2 guard conversions in 3 suites; V-15-3 monkeypatch conversions + `authority_generation_resolver` DI wiring in the `.1R.14` / `.1R.15` suites | `runtime_dispatch_gate9.py` **only** |
| `866a6cdb` | PROJECT_STATUS + CHANGELOG + phase-task allowed-file finalize | none |
| `89160046` | close phase task → idle | none |
| `369b4736` | stage canonical completion metadata + report | none |
| `c45983af` | expand idle-task allowed-file zone | none |
| `735674f7` | reconcile governed push state | none |

`git diff --name-only d78d9676 735674f7 -- src/` = **exactly**
`src/pcae/core/runtime_dispatch_gate9.py`. The only functional commit is
`b32619e5`. `git diff d78d9676 735674f7 -- docs/contracts schemas` = **empty**.

### 0.2 Initial repository inspection (phase prompt §4)

```
git status --short                      -> clean (only the new .1R.15.3 verification suite untracked, pre-commit)
git status --branch --short             -> ## main...origin/main
git log --oneline origin/main..HEAD     -> (empty)
git rev-list --count origin/main..HEAD  -> 0
pcae health                             -> healthy; agent lock claude-local; continuity verified; git clean
pcae check                              -> passed
pcae status coherence                   -> coherent
pcae doctor task-memory                 -> warning-only historical tasks/DONE.md omissions (pre-existing O4); no current-phase error
pcae push check                         -> nothing_to_push; phase-report trust + identity passed
pcae runtime inspect                    -> not_implemented / Observed / observe / unavailable; 0 plugins; 0 capabilities; PB execution_unavailable; non-executing
source ~/.config/pcae/telegram.env; pcae notify status -> configured, enabled, outbound-ready
pcae phase-report show --latest         -> .1R.15.2 completed, report complete, pushed, origin/main..HEAD 0
```

Confirmed: `.1R.15.2` is the latest completed phase; repository clean; no
active governed phase before this phase's task was opened; runtime
`Observed / observe / unavailable` unchanged.

### 0.3 Primary sources read in full

Contracts (`docs/contracts/`, current frozen text): RDGO-001 v3.0
(`RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md`) §10 / §11 / §15 / §16,
HPAC-001 v2.0 (`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md`) §40–§42
(HPAC-REQ-094 / 095 / 096 / 097 / 098 / 099 / 100 / 101 / 102), RIHAC-001
v2.0, RIASC-001 v3.0, PBRD-001 v2.0, RPAC-001 v1.0, PBPA-001, POL-005.
Phase docs `.1R.15.2` (repair), `.1R.15.1` (planning/reconciliation, full),
`.1R.15` (Gate-9 verification), `.1R.14` (Gate-9 implementation), `.1R.9`
§10–§19 (Gate-5/9 planning), `.1R.13.5` (Gate-8 verification), `.1R.13.1`
§16 (Gate-8→Gate-9 handoff). Production source line-by-line:
`runtime_dispatch_gate9.py` (1177 lines, post-repair),
`runtime_invocation_authority_consumption.py` (214 lines),
`runtime_dispatch_gate5/permission/gate7/gate8.py` at the boundaries
relevant to each check. The three V-15-2 guard suites + the V-15-3-touched
`.1R.14` suite in full; the `.1R.15.2` 44-test suite in full (§18 below).

---

## 1. Independently reconstructed repaired call flow

`run_gate9_atomic_authority_consumption` (production source, re-derived by
reading, by `ast` walk, and by instrumented execution — not from the
`.1R.15.2` §4.1 diagram):

```
1   is_gate8_result(gate8_result)                       exact-object provenance
2   gate8_result.containment_established is True         hard stop, before any store access
3   is_gate7_result + ALLOW; is_gate6_decision + ALLOW; is_gate5_result
4   structural guards (identity / inputs / times / repo_root / resolvers / stores)
      + callable(authority_generation_resolver)          [new; gate9_invalid_authority_generation_resolver]
5   single invocation/attempt/request across every link (RDGO §10a)
6   _validate_construction_inputs(inputs)               canonical construction re-check
7   _gate7_result_digest cross-check vs gate8_result.gate7_result_digest
7a  early projection pre-check (is_trusted + subject/scope digest)
8   run_gate8_process_containment RE-RUN + read-back of every containment digest   [V-13-5-1; BEFORE S1]
── serialization boundary = the per-proof_id create-only primitive (no lock object) ──
9   is_trusted_validated_authority_projection + revalidate_validated_authority_projection
      (re-runs validate_approval -> principal/credential/proof/approval currentness,
       expiry, revocation, prior-consumption) + subject/scope digest re-compare
11  read-only sequence-3 PROOF_VERIFIED_AND_BOUND confirm (resolve_gate5_binding_event)
12  exact proof + approval pairing (gate5_result.{approval_id,proof_id} == projection.*)
13  capability_snapshot_resolver() re-read -> fail closed unless still `unavailable`
14  consumption_store.resolve(proof_id) absence check -> present => deterministic already_consumed
14a S1 = _capture_authority_generation_snapshot(...)     [ONLY after 9-14 succeed]
15  descriptor_resolver(inputs) + hashing + _build_consumption_record(...)   NO WRITE
15a S2 = _capture_authority_generation_snapshot(...)     [immediately before create]
      if s2_reasons: fail closed
      if s2["consumption_generation"] != ("absent",): deterministic already_consumed
      drift = _first_authority_generation_drift(s1, s2)
      if drift: return ("gate9_authority_generation_drift:<token>",)   NO consumption.json
16  consumption_store.create(proof_id, consumption_record)   the sole linearization point
17  read-back resolve + record_digest compare -> Gate9Result(status="consumed")
```

Confirmed structurally: `ast` walk finds **exactly one**
`consumption_store.create(` call node; **exactly two**
`_capture_authority_generation_snapshot(` call sites; **no** `threading` /
`fcntl` / `filelock` / `multiprocessing` / `asyncio` import and **no**
`Lock(` / `RLock(` / `Semaphore(` / `flock(` / `FileLock(` token — the
repair introduced **no** lock primitive (`.1R.9` §18 honoured).

---

## 2. S1 ordering — captured only after the full battery

**Independently proven two ways:**

1. **Source order** (`inspect.getsource` + string index): the step-13
   capability re-read marker precedes the step-14a S1 marker precedes the
   step-15a S2 marker precedes the `consumption_store.create` call.
2. **Instrumented execution** (`_Recorder` wraps the resolver, the
   capability resolver, `store.resolve`, `store.create`, and
   `resolve_canonical_chain` and records call order). On the (test-path)
   success path the **first** `authority_generation_resolver` call (S1) is
   preceded in the recorded trace by both `capability_snapshot_resolver`
   (battery step 13) and `store.resolve` (battery step 14 absence check).

A revocation / disablement / eligibility change / record replacement /
lifecycle invalidation landing **before** the battery is caught by the
battery itself (`revalidate_validated_authority_projection` re-runs
`validate_approval`). S1 is never captured before current-state validation.

---

## 3. Record preparation between S1 and S2 (phase prompt §9)

Everything between step 14a (S1) and step 15a (S2) is step 15:
`descriptor_resolver(inputs)` (a descriptor **read**, re-resolving the
executable identity for `executable_identity_digest`), `compute_canonical_digest`
(pure), and `_build_consumption_record` → `new_inert_consumption_record`
(pure field assembly + `canonical_digest`; **no write**, no mutable-store
read, no policy evaluation, no effectful op, no time-sensitive derivation).

- The `descriptor_resolver` read is **not an authority-generation source**;
  the executable/descriptor/containment dimensions were recomputed and
  read-back-verified at step 8 (the Gate-8 re-run) **before** S1, and any
  drift there is a step-8 rejection. Re-resolving the descriptor at step 15
  to hash it into the record does not "reopen the authority window" — it
  reopens the *containment* view, which S2 does not (and need not) token,
  because step-8's recomputation already bound it.
- `_build_consumption_record` uses the already-validated projection /
  gate objects / genesis binding; it performs **no** fresh mutable-authority
  read. Confirmed by `ast` + source inspection of
  `_build_consumption_record`, `_authority_binding_fields`, and
  `new_inert_consumption_record`.

**Conclusion:** record preparation uses already-validated state and does not
silently reopen the authority window. The only descriptor re-resolution is
a containment-view read whose drift is already bound by step 8.

---

## 4. S2 ordering — immediately before create; zero effectful I/O between decision and create

**Independent source slice** (own delimiters: from
`_first_authority_generation_drift(s1, s2)` to
`consumption_store.create(proof_id, consumption_record)`): the span contains
**exactly one `return`** (the drift fail-closed branch) and **none** of
`resolve(`, `resolver(`, `run_gate8`, `descriptor_resolver`, `subprocess`,
`socket`, `open(`, `revalidate_`, `_capture_authority_generation_snapshot`,
`compute_canonical_digest`, `_build_consumption_record`.

**Instrumented order** (`_Recorder`): on the success path the recorded event
immediately preceding `store.create` belongs to the S2 capture cluster
(`store.resolve` / `lifecycle.resolve_canonical_chain` /
`authority_generation_resolver`); **no** `capability_snapshot_resolver`
appears between the two S1/S2 resolver calls; the S2 cluster is the last
authority read before the create.

Within `_capture_authority_generation_snapshot`, S2's reads occur in the
order: (1) `authority_generation_resolver()` → principal / credential /
approval digests; (2) `_lifecycle_generation_token` → full chain read;
(3) `_consumption_generation_token` → `consumption_store.resolve`. So the
consumption-record read is the **last** canonical read before the
comparison and the create — the tightest possible for the consumption race.

---

## 5. Token inventory — re-derived, not trusted (phase prompt §13–§18)

`_capture_authority_generation_snapshot` returns a mapping of **exactly
five** keys (independently asserted):

| Token | Canonical source | Re-derived completeness argument |
|---|---|---|
| `principal_generation` | trusted `authority_generation_resolver()` → (test rig) `registry.resolve_canonical_principal(principal_id).record_digest` | **whole-record canonical digest.** Real `registry.revoke_principal` flips `status active→revoked` and adds `revoked_at` **in the same canonical record**, so `record_digest` moves. Independently confirmed by real mutation (`test_principal_token_moves_on_real_revocation`). Disablement / eligibility change / record replacement are likewise whole-record edits. |
| `credential_generation` | resolver → `registry.resolve_canonical_credential(credential_id).record_digest` | same — real `registry.revoke_credential` moves the digest (`test_credential_token_moves_on_real_revocation`). N-15-2-1 carried: the shared principal+credential registry document means a credential revocation **also** moves `principal_generation`; fail-safe (either token moving blocks the create). |
| `approval_generation` | resolver-supplied (opaque to the coordinator) | **resolver-delegated — see finding N-15-3-2 §6.** The coordinator imports no approval-store symbol; it validates the returned string's shape only. Drift is detected **when the resolver surfaces it** (`test_approval_drift_is_detected_when_the_resolver_surfaces_it`). |
| `lifecycle_generation` | `compute_canonical_digest([{sequence, state, event_digest} for each event in lifecycle_store.resolve_canonical_chain(proof_id)])` | **digest over every event of the provenance-checked chain.** A terminal `EXPIRED` / `REVOKED` / `REJECTED` append moves it (`test_lifecycle_token_moves_on_terminal_event`, `..._is_over_every_chain_event_not_just_the_head`). A fork → `resolve_canonical_chain` raises → `gate9_internal_error_fail_closed`. **Subsumes the proof-state token** — proof lifecycle status / expiry / revocation / canonical identity are all events in this same hash-chained lifecycle (§5.1 below). |
| `consumption_generation` | `consumption_store.resolve(proof_id)` → `("absent",)` / `("present", record_digest)`; `…DurabilityUncertainError` **propagates** → `gate9_consumption_state_durability_uncertain` | exact canonical store state; a partial / corrupt record is never read as absent or present (`test_durability_uncertain_consumption_token_propagates`). |

The drift comparison order
`(principal, credential, approval, lifecycle)_generation` is a module
constant; `consumption_generation` is compared by the caller (present →
deterministic `already_consumed`, **not** a drift rejection).

**None uses a wall-clock timestamp, an mtime, a process-local nonce, or an
incomplete selected-field digest** — `ast` scan of the four snapshot
functions finds no `time(` / `now(` / `utcnow` / `random` / `token_hex` /
`uuid` / `id(` / `getmtime` / `st_mtime` / `monotonic` / `perf_counter`.

### 5.1 Proof-state subsumption — independently proven

The `.1R.15.2` claim that `lifecycle_generation` subsumes a separate
proof-state token is **CORRECT**. Re-derived from HPAC-REQ-094 / 095: the
proof lifecycle **is** the hash-chained sequence of immutable
`HumanAuthenticationProofLifecycleEvent` files ("not a mutable state
flag"). Every proof-authority-relevant mutation — a state transition, a
terminal `EXPIRED` / `REVOKED` / `REJECTED`, expiry recorded as an event,
canonical-identity binding — **is** an event appended to that exact chain,
and the token digests **every** event's `(sequence, state, event_digest)`.
There is no proof-authority-relevant mutation that leaves the canonical
lifecycle-chain representation unchanged. A terminal `EXPIRED` append (a
proof-state change) moves the token (`test_lifecycle_token_subsumes_proof_state`).
**Subsumption proven; the token set is complete for the principal /
credential / lifecycle sources.**

### 5.2 Approval-state completeness (phase prompt §18) — finding N-15-3-2

The coordinator delegates `approval_generation` entirely to the trusted
`authority_generation_resolver` and holds **no** approval-store reference
(`grep`-confirmed: no `runtime_invocation_approval_store`, no
`approval_store` symbol in `runtime_dispatch_gate9.py`). This mirrors the
existing `descriptor_resolver` / `capability_snapshot_resolver` DI pattern
and is not itself a defect. **But:** unlike principal/credential (whose
revocation is a whole-record edit that moves `record_digest`), a RIASC
approval `record` is **immutable** and HPAC-REQ-102 keeps approval
revocation "in RIHAC's repository governance store" — a *separate* store.
An `approval_generation` computed as the immutable approval `record_digest`
**alone** would **not** move on an approval revocation in the S1→S2 window.

- **Non-blocking now:** `run_gate9_atomic_authority_consumption` has **no
  production caller** (real Gate 7 always DENYs; real `run_gate5` never
  yields a `Gate5Result`). No production `authority_generation_resolver`
  exists yet.
- **Carried to `.1R.15.4`:** the production `authority_generation_resolver`
  wiring MUST fold approval-revocation-store currentness (e.g. a revocation
  digest / generation counter) into `approval_generation`, or approval
  revocation in the S1→S2 window is not caught. The `.1R.15.2` §4.2 table
  row acknowledges "+ any revocation-store state the resolver includes";
  this makes it an explicit `.1R.15.4` requirement, not an option.
- Within the battery (step 9), `revalidate_validated_authority_projection`
  re-runs `validate_approval`, which **does** check approval revocation —
  so an approval revocation landing **before** S1 is caught. The gap is
  strictly the S1→S2 window, strictly dependent on the (not-yet-written)
  production resolver.

This is **INFO / carried**, not blocking, and does **not** prevent V-15-1
closure for the Gate-9 serialization window — see §11.

---

## 6. Restart reconstructibility / no mtime|clock|nonce (phase prompt §20–§21)

Re-deriving the snapshot from a **brand-new**
`RuntimeInvocationAuthorityConsumptionStore` object over the same root
yields byte-identical tokens (`test_tokens_are_pure_functions_of_durable_state`).
`lifecycle_generation` is a pure function of the on-disk hash-chained
lifecycle; `consumption_generation` a pure function of the on-disk record;
the resolver digests read canonical registry records. **No process-local
identity, randomness, mtime, or wall clock participates** — every token is
reconstructible after a restart from canonical durable state alone.

---

## 7. Drift injection — each source, fail closed (phase prompt §22–§28)

Injections fired from **inside `_build_consumption_record`** (step 15,
strictly after S1 / step 14a, strictly before S2 / step 15a — injection
point independently re-derived, not assumed) mutating **real canonical
stores**, or via a resolver whose returned dict flips on the 2nd
(S2) call:

| Injection | Mechanism | Result | `consumption.json` written |
|---|---|---|---|
| Principal drift | resolver flips `principal_generation` on S2 | `gate9_authority_generation_drift:principal_generation` | 0 |
| Principal revocation (real) | `registry.revoke_principal` between S1/S2, real resolver | `gate9_authority_generation_drift:principal_generation` | 0 |
| Credential drift | resolver flips `credential_generation` on S2 | `gate9_authority_generation_drift:credential_generation` | 0 |
| Lifecycle drift (real) | `lifecycle_store.terminate_canonical(state="REVOKED")` between S1/S2 | `gate9_authority_generation_drift:lifecycle_generation` | 0 |
| Approval drift | resolver flips `approval_generation` on S2 | `gate9_authority_generation_drift:approval_generation` | 0 |
| Consumption record appears | valid canonical record planted between S1/S2 | **deterministic `already_consumed`** (`gate9_already_consumed`), **not** a drift rejection (§14/§31) | 1 (the planted one; no second create) |
| Multi-source drift | resolver flips principal **and** credential on S2 | `gate9_authority_generation_drift:principal_generation` (first in fixed order — deterministic) | 0 |
| Consumption durability-uncertain | `store.resolve` raises | `gate9_consumption_state_durability_uncertain` | 0 |
| Stable tokens | no authority source touched | `status == "consumed"` — exactly one create | 1 |

In **every** drift case: fail-closed, **no `Gate9Result`**, **no external
effect** (Gate 10 absent; its `.1R.15.1` §22 forward invariant mandates a
full re-read + re-validation + containment re-establishment before any
effect). The one-shot authority is **burned, never escalated**.

**No stale snapshot across a retry:** after a drift-blocked attempt, a
fresh call re-derives S1 from **current** canonical state
(`test_retry_after_drift_rejection_re_derives_from_current_state`) — no
cached S1/S2 is resumed.

---

## 8. Concurrency / one-shot (phase prompt §30–§31)

- **6 barrier-synchronised contenders** against the same canonical
  proof/approval pair → **exactly one `status == "consumed"`**, exactly one
  durable canonical record; every other racer ∈
  `{already_consumed, fail_closed}` — **never a second success**. Stress:
  **8 consecutive loop runs**, one winner every run, one record every run.
- **Concurrent authority mutation** straddling a contender's S1→S2 window
  (real `registry.revoke_principal` between S1 and S2) → that contender
  rejects `gate9_authority_generation_drift:*`; **no consumption from a
  stale snapshot** (`test_concurrent_authority_mutation_straddling_the_window_rejects`).
- Generation-token logic **does not disturb** the existing one-shot
  atomicity: the winner is still decided purely by the `O_EXCL`
  create-only primitive; the loser still maps `HPACDuplicateError` →
  deterministic `already_consumed`.

---

## 9. Crash semantics (phase prompt §32–§36)

| Scenario | Behaviour | Records |
|---|---|---|
| Crash before S1 (`authority_generation_resolver` raises) | `gate9_internal_error_fail_closed`; nothing consumed | 0 |
| Crash after S1, before S2 (exception in `_build_consumption_record`) | `gate9_internal_error_fail_closed`; nothing consumed | 0 |
| Crash after S2 comparison, before create (`store.create` raises) | fail closed; `resolve` → `None`; nothing consumed | 0 |
| Crash after create, before read-back (`store.create` succeeds then raises) | coordinator resolves, finds the durable record, returns **deterministic `already_consumed`** — never a second write, never a crash | 1 |
| Fresh retry after crash-after-create (`_GATE9_RESULTS.clear()` + new store object) | deterministic `already_consumed` — **canonical durable state controls restart** | 1 |

`S2` itself is **not durable authority** — a fresh retry after a
crash-after-S2/pre-create revalidates and produces a **fresh** S1/S2
(no cached S1). Confirmed: the `.1R.15.2` repair adds **no** persisted
token, so it cannot introduce a stale-token durability path — the crash
table is exactly `.1R.14`'s, unchanged.

---

## 10. Practical-limit / residual micro-window (phase prompt §37) — HONEST CHARACTERIZATION

**What is closed.** The TOCTOU window that `.1R.15` finding V-15-1
identified was "one racer's step-9→step-16 duration" — the entire
revalidation battery **plus** the full record build (descriptor
re-resolution, hashing, record construction). The repair narrows it to
**the pure statements between S2's last canonical read
(`consumption_store.resolve` inside the S2 capture) and
`consumption_store.create`** — a drift comparison and the create call, with
**zero effectful I/O** (§4). Any principal / credential / approval /
lifecycle change, or a consumption record appearing, in the (now much
larger) S1→build→S2 span is a **fail-closed pre-`create` rejection**.

**What micro-window remains.** **No lock spans S2→create.** At the
CPU/instruction level, a mutation to the principal / credential / approval /
lifecycle canonical stores landing *after* S2's resolver/chain reads but
*before* `consumption_store.create` completes is **not** detected for the
current attempt. This residual window is:

- **bounded to a few pure Python statements + one create syscall path** —
  microseconds; no I/O, no `sleep`, no subprocess, no lock wait;
- **NOT closable without extending the create primitive** into a
  conditional-create that atomically verifies an expected-generation vector
  (Option D in `.1R.15.1` §14) — explicitly out of the authorized
  narrow-repair scope and rejected there as over-scoped (a new HPAC-REQ);
- **fully closed for the consumption race specifically** — a consumption
  record appearing in the residual window causes the `O_EXCL` create to
  raise `HPACDuplicateError` → deterministic `already_consumed`. The
  `O_EXCL` primitive **is** atomic for its own domain. Only the
  cross-store authority facts have the residual instruction-level window.

**Why it is acceptable under the current frozen contract.** RDGO-001 §10
says "revalidate … while holding the protected evidence-store serialization
boundary … without a TOCTOU allowance"; `.1R.9` §18 says "do not invent a
new lock — the protected create-only commit is itself the atomic
transaction". These are **internally inconsistent** (recorded as V-15-1's
contract-side defect in `.1R.15.1` §12.1). The `.1R.15.2` repair honours
`.1R.9` §18 (the frozen architectural constraint) and realizes "no TOCTOU
allowance" **to the practical limit** achievable without a second lock. The
residual window **produces no external effect**: Gate 10 does not exist, has
no phase ID, and its frozen `.1R.15.1` §22 forward invariant mandates a
full re-read of `consumption.json` + re-validation of **all** mutable
authority + containment re-establishment before the first effect. A
stale-authority consumption record written through the residual window is
therefore caught by Gate 10's mandatory re-validation → no dispatch. The
one-shot authority is burned (a denial), never escalated.

**What `.1R.15.4` must say.** RDGO-001 §10 / `.1R.13.1` §16.2-inv-4 /
`.1R.9` §12/§18 must be normalized to the single coherent model: *the
per-`proof_id` create-only atomic primitive is the linearization point and
the sole transaction mechanism; the revalidation battery plus a final
zero-effectful-I/O authority-generation-token re-check run immediately
before it; any monotonic-token change fails closed; this realizes "no
TOCTOU allowance" to the practical limit without a second global lock*.
`.1R.15.1` §17 / §19 already scoped exactly this text. The residual
instruction-level window is consistent with the intended semantics **only
because Gate 10 re-validates**; RDGO v3.1 must carry that dependency
explicitly (it already scopes the §22 forward invariant into RDGO v3.1).

**Verdict on §37:** the remaining micro-window does **not** contradict the
intended semantics given the frozen `.1R.9` §18 constraint and the absent,
re-validating Gate 10. **V-15-1's Gate-9 serialization window CAN close** at
this phase, with the durable representation explicitly deferred.

---

## 11. Durable-snapshot contract analysis (phase prompt §38–§42) — RE-DERIVED

`.1R.15.2` §3 deferred the durable / re-readable generation-snapshot to
`.1R.15.4`, citing HPAC-REQ-098's closed `authority_binding` and
`registry_state_digest`'s grammar. **Independently re-derived from primary
source — the deferral is CONFIRMED CORRECT.**

### 11.1 `authority_binding` is a closed 12-field set with no extension

- **HPAC-REQ-098** (`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md:1112`):
  `authority_binding` "contain **exactly**" — `approval_id`,
  `approval_digest`, `authority_projection_id`, `authority_projection_digest`,
  `authority_contract_version` (const `RIHAC-001/2.0`), `proof_id`,
  `proof_digest`, `proof_validation_digest`, `registry_state_digest`,
  `approval_subject_digest`, `trusted_presentation_ref`, `challenge_digest`.
  12 fields. "Arrays retain order and all other strings/digests use their
  **owning contract grammar**." No `additionalProperties`, no extension
  clause; the contract's schema-artifact rule
  (`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md:148`) forbids
  `additionalProperties: true` anywhere.
- **`runtime_invocation_authority_consumption.py:150`** enforces it hard:
  `set(value.keys()) != expected_fields` → `HPACMalformedError` on
  `create`; and on `resolve`, an unknown top-level key →
  `…DurabilityUncertainError` (`:203`, `unknown or missing`).
- Independently exercised: `new_inert_consumption_record` with a 13th
  `authority_generation_snapshot` field in `authority_binding` raises
  `HPACMalformedError` (`test_no_thirteenth_authority_binding_field_can_be_created`).

Adding a 13th field is **normative schema drift** on the frozen
`HPAC-AUTHORITY-CONSUMPTION/2.0` record — forbidden in a repair/verification
phase.

### 11.2 `registry_state_digest` cannot carry the vector within grammar

- **HPAC-REQ-095** (`:1046`): `registry_state_digest` is "either null or 64
  lowercase hex exactly as the state table requires" — a **flat** digest.
  In the lifecycle-event state table it is the sequence-2 evidence tied to
  "signature, subject, presentation, UP, UV, freshness, domain, **registry**,
  and assertion verify for approval creation" (`:1059`).
- **HPAC-REQ-099** (`:1123–1129`): gate 9 "compare-and-creates
  `consumption.json` against **the exact current registry/configuration
  state digest** and sequence-3 event." The contract's own list of what
  gate 9 *rechecks* enumerates "current principal/credential/descriptor
  status, presentation attestation and expiry, challenge/proof/lifecycle
  chain, approval freshness/expiry, exact gate-5 binding, PB/Runtime
  Enforcement freshness, and absence of a consumption record" — and the
  thing it **compare-and-creates against** is the
  "registry/configuration state digest and sequence-3 event", **not** a
  principal/credential/approval/lifecycle generation vector.
- In HPAC/RDGO grammar "registry/configuration" is enumerated **separately**
  from `principal / credential / presentation / proof / lifecycle /
  approval` currentness (RDGO-001 §10 item 5 lists "proof-validation/
  current-registry digests"; HPAC-REQ-095 state table). It denotes the
  trust / installed-mechanism registry + descriptor configuration digest.

Independently exercised: `registry_state_digest`'s production computation
(`runtime_dispatch_gate9.py` step 15) is the **byte-unchanged** flat 3-key
digest over `{projection_digest, sequence3_event_digest,
gate8_containment_evidence_digest}` — the `.1R.15.2` diff hunk does **not**
touch `_authority_binding_fields` or the `registry_state_digest =
compute_canonical_digest(...)` block
(`test_registry_state_digest_computation_is_unchanged_from_1r14`). The
generation vector was **not** smuggled into any existing digest's preimage.

### 11.3 `registry_state_digest` semantic test (phase prompt §40)

> **Can the generation vector legally become part of the preimage of
> `registry_state_digest` under the frozen contracts?**
>
> **NO.** `registry_state_digest`'s normative meaning is a digest of the
> *registry/configuration* state (HPAC-REQ-095 state table; HPAC-REQ-099
> "registry/configuration state digest"), a category the frozen grammar
> enumerates **separately** from principal / credential / proof / approval /
> lifecycle currentness. Folding the full mutable-authority-generation
> vector into its preimage broadens its contractual meaning from
> "registry/config digest" to "registry/config + all-mutable-authority-
> generation digest". No frozen contract clause grants that broadening.
> HPAC-REQ-098's "all other strings/digests use their owning contract
> grammar" forecloses redefining it here.

### 11.4 Durable deferral adjudication (phase prompt §41)

> **DURABLE SNAPSHOT DEFERRAL — CONFIRMED CORRECT.**
>
> No existing `authority_binding` field legally permits the generation
> snapshot or a complete commitment to it without changing semantic
> meaning; a 13th field is a closed-set violation. A schema-safe durable
> representation requires either `authority_binding` extension or a new
> binding object — a **normative schema change** (HPAC-001 errata / RDGO-001
> v3.1), correctly assigned to `.1R.15.4`. `.1R.15.2`'s deferral is not
> "CONTRACT AMBIGUOUS — BLOCKING": the contracts are unambiguous that the
> current record **cannot** carry it, and unambiguous (`.1R.15.1` §17/§19)
> that `.1R.15.4` is where the normative representation is added. This
> phase found **no schema-safe representation that `.1R.15.2` missed.**

### 11.5 Gate-10 implication (phase prompt §42)

Confirmed and kept distinct:

- **`.1R.15.2` CAN close V-15-1's Gate-9 serialization-window repair**
  without the durable snapshot — the in-memory S1/S2 guard closes the
  window to the practical limit (§10).
- **Gate 10 still MUST NOT be planned or implemented** until `.1R.15.4` /
  `.1R.15.5` normalize and verify the durable generation-snapshot semantics
  **and** the 10-item `.1R.15.1` §20 prerequisite list is satisfied. The
  absence of a durable snapshot means Gate 10's **only** current durable
  cross-check would be its §22 forward-invariant full re-validation — which
  is sufficient *because Gate 10 does not exist*, and which `.1R.15.4` must
  give a durable companion.

These two facts are **not** blurred: V-15-1's window closes here; the
durable Gate-10 second line of defense does not exist yet and is deferred.

---

## 12. V-15-2 independent verification (phase prompt §43–§45)

### 12.1 The three previously-stale guards

| Suite | Test |
|---|---|
| `test_hpac_foundation_independent_verification_3w1r2b1r111r31.py` | `test_new_hpac_modules_have_zero_preexisting_production_consumers` |
| `test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py` | `test_hpac_repair_has_zero_preexisting_production_consumers` |
| `test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py` | `test_foundation_has_no_production_consumers_or_gate_wiring` |

### 12.2 Each is now a phase-aware SUBSET invariant — re-derived from source

Each test's body (independently sliced and asserted per-suite) now:

- computes `consumers` by `ast`-walking `src/pcae/core/*.py` imports of the
  HPAC Layer-1/2 modules;
- defines `AUTHORIZED_CONSUMERS` as an **explicit 4-tuple set**:
  `("runtime_dispatch_gate5.py", "pcae.core.hpac_lifecycle")` +
  `("runtime_dispatch_gate9.py", "pcae.core.hpac_foundation")` +
  `(…gate9…, "pcae.core.hpac_lifecycle")` +
  `(…gate9…, "pcae.core.runtime_invocation_authority_consumption")`;
- asserts `set(consumers) - AUTHORIZED_CONSUMERS == set()` — the **correct
  orientation** (observed − allowed; an unauthorized consumer makes the
  difference non-empty and fails);
- contains **no** `startswith(` / wildcard allowance.

The authorized Gate-9 imports match the actual production source (`grep`
over `src/pcae/core/runtime_dispatch_gate9.py`: `from pcae.core.hpac_foundation
import HPACDuplicateError`; `from pcae.core.hpac_lifecycle import
STATE_PROOF_VERIFIED_AND_BOUND`; `from pcae.core.runtime_invocation_authority_consumption
import …`). The gate5 entry is `.1R.10`/`.1R.11`-authorized and unchanged.

### 12.3 Unauthorized future consumer still fails (phase prompt §44)

Independently exercised: a synthetic
`("runtime_dispatch_gate10.py", "pcae.core.hpac_foundation")` added to the
observed set makes `observed - AUTHORIZED_CONSUMERS` non-empty — the assert
fails. The guard is **not** defeated
(`test_v15_2_unauthorized_future_consumer_would_still_trip_the_guard`).

### 12.4 EXACT asserts not subset-relaxed

Re-checked: the same three suites' **HPAC-verifier trust-root** asserts,
the **`_GATE9_RESULTS` owner** invariant, and any **Gate-10 exact-empty**
consumer asserts elsewhere in those files are **not** converted to subset
form — only the three named zero-consumer guards were touched (the
`.1R.15.2` diff shows exactly three hunks in these three files).

### 12.5 Fixed-SHA A/B

Deterministic `-p no:randomly -n0`, 3 guard suites isolated:

| SHA | Result |
|---|---|
| `d78d9676` (baseline) | **16 failed / 110 passed** |
| `735674f7` (HEAD) | **13 failed / 113 passed** |

The **+3 passes** are exactly the three converted guards. The **13
remaining** failures at HEAD are a strict subset of the 16 at baseline
(the pre-existing `test_blocking_reproduction_*` ×8 in r31 + ×3 in r321,
`test_deterministic_authenticator_…`, `test_deterministic_attestation_encoding_…`)
— identical set, identical at baseline. `test_v15_2_guards_pass_at_head`
(this suite) subprocess-runs the three node IDs → `3 passed`.

### 12.6 V-15-2 adjudication

> **V-15-2 — CLOSED.** Three phase-aware subset invariants with an explicit
> enumerated `AUTHORIZED_CONSUMERS`, correct orientation, no wildcard,
> unauthorized future consumers still fail, EXACT asserts preserved.
> Fixed-SHA A/B: FAIL@`d78d9676` → PASS@`735674f7` for each.

---

## 13. V-15-3 independent verification (phase prompt §46–§48)

### 13.1 The three previously-raw assignments

In `test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py`:
`test_sequence3_cross_binding_rejected`,
`test_different_proof_same_consumed_approval_is_rejected`,
`test_consumption_store_rejects_traversal_proof_id`. Each previously did
`import pcae.core.runtime_dispatch_gate5 as _g5mod; _g5mod.is_gate5_result = lambda …`.

### 13.2 Now scoped monkeypatch — re-derived from the file

Independently confirmed (raw text scan of the current `.1R.14` suite):
`"_g5mod.is_gate5_result ="` **absent**; `"is_gate5_result = lambda"`
**absent**; `monkeypatch.setattr(gate5, "is_gate5_result"` appears **≥ 3**
times; each of the three test signatures gained `monkeypatch`. The
repository-standard scoped form (`monkeypatch.setattr` on the module object)
is used — deterministic, ordered teardown.

### 13.3 Restoration / no cross-test pollution

- `gate5.is_gate5_result.__module__ == "pcae.core.runtime_dispatch_gate5"`
  **after** importing and exercising the `.1R.14` helpers — no dead closure
  installed at import time (`test_v15_3_is_gate5_result_is_the_original_callable_now`).
- The `.1R.14` (63), `.1R.15` (76), `.1R.15.2` (44), and this `.1R.15.3`
  (56) suites all pass **individually, together (239 in one process), and
  in random order** — no monkeypatch state leaks across module boundaries.

### 13.4 V-15-3 adjudication

> **V-15-3 — CLOSED.** All three raw assignments replaced with scoped
> `monkeypatch.setattr`; `is_gate5_result` is the original callable after
> the file; no cross-test pollution across the four gate-9 suites in any
> order.

---

## 14. Regression preservation (phase prompt §49–§57)

| Property | Independent evidence |
|---|---|
| **V-13-5-1 containment read-back** | `run_gate8_process_containment` re-run + `gate9_containment_evidence_recomputation_mismatch` are at step 8, **before** S1 — source-index asserted (`test_v13_5_1_containment_readback_runs_before_s1`); `effect_plan` structural drift still `gate9_invalid_effect_plan` |
| **Replay** | identical replay ×3 → deterministic `already_consumed` + `("gate9_already_consumed",)`; one record (`test_replay_is_deterministic_already_consumed`) |
| **Durability** | crash-before/after-S2, crash-after-create — §9; fresh-store retry → `already_consumed` (durable record controls restart) |
| **`Gate9Result` discipline** | `__reduce__` raises; `==` / `hash` identity-only; `object.__new__(Gate9Result)` → `is_gate9_result` False; provenance ≠ success (both `consumed` and `already_consumed` are registry members) |
| **No Gate 10** | `ast` import scan: no `subprocess` / `socket` / `pty` / `requests` / `httpx` / `runtime_adapter` / `mock_runtime_adapter` / `fido2` / `webauthn`; code-only scan (docstrings stripped): no `run_gate10` / `Gate10Result` / `adapter_dispatch` / `.dispatch(` / `os.system` / `Popen` / `subprocess` / `socket` node |
| **Runtime unchanged** | capability snapshot anything but `Observed/observe/unavailable` → `gate9_runtime_execution_available_unexpected`; `pcae runtime inspect` at entry and finalization: `not_implemented / Observed / observe / unavailable`, 0 plugins, 0 capabilities, PB `execution_unavailable`, non-executing |
| **Gate 5 / 6 / 7 / 8 + consumption store + `runtime_authority` + `hpac_*`** | `git diff d78d9676 735674f7 -- src/pcae/core/<file>` **empty** for `runtime_dispatch_gate5.py`, `runtime_dispatch_permission.py`, `runtime_dispatch_gate7.py`, `runtime_dispatch_gate8.py`, `runtime_invocation_authority_consumption.py`, `runtime_authority.py`, `hpac_lifecycle.py`, `hpac_verifier.py`, `hpac_foundation.py` — byte-identical; parametrized `test_earlier_gate_and_store_modules_byte_identical_since_baseline`. Gate 5/6/7/8 + consumption suites: **430 passed** at HEAD, identical at baseline by construction (modules **and** their test files byte-unchanged). **Gate 5 CLOSED / Gate 6 CLOSED / Gate 7 CLOSED / Gate 8 CLOSED — reconfirmed.** |
| **Production-file scope** | `git diff --name-only d78d9676 735674f7 -- src/` = exactly `["src/pcae/core/runtime_dispatch_gate9.py"]`; `runtime_invocation_authority_consumption.py` byte-unchanged (`test_only_gate9_py_changed_in_src_since_baseline`) |
| **Contract identity** | `git diff --name-only d78d9676 735674f7 -- docs/contracts schemas` = **empty** (`test_no_normative_contract_changed_since_baseline`); RDGO-001 v3.0, HPAC-001 v2.0, RIHAC-001 v2.0, RIASC-001 v3.0, PBRD-001 v2.0, RPAC-001 v1.0, PBPA-001, POL-005 byte-unchanged |
| **Consumption-record schema** | `_BINDING_FIELD_SETS["authority_binding"]` = the exact 12-key frozenset; exact-key enforcement on create + unknown-key rejection on resolve (`test_authority_binding_is_a_closed_twelve_field_set_with_no_extension`) |

---

## 15. Fresh independent verification suite (phase prompt §58)

`tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py`
— **56 tests, 0 failed**. Coverage map to the §58 minimum list:

1 exact call sequence — §1 (`test_coordinator_has_exactly_one_create_call_site`,
`test_no_lock_primitive_introduced_by_the_repair`,
`test_snapshot_capture_helper_reads_only_canonical_state`); 2 S1-after-battery
— §2 (`test_s1_is_captured_only_after_the_revalidation_battery`); 3 record
prep between S1/S2 — §3 (structural); 4 S2 immediately before create — §4
(`test_s2_is_the_last_authority_read_before_create`); 5 no effectful I/O
S2→create — §4 (`test_zero_effectful_io_between_drift_decision_and_create`);
6 no hidden mutable reads after S2 — §4; 7 token inventory — §5
(`test_snapshot_carries_five_tokens_…`); 8–10 principal/credential/lifecycle
token completeness — §5; 11 proof-state subsumption — §5.1
(`test_lifecycle_token_subsumes_proof_state`); 12 approval-state
completeness — §5.2 (`test_approval_generation_is_resolver_delegated`,
`test_approval_drift_is_detected_when_the_resolver_surfaces_it`); 13
consumption-state token — §5 (`test_consumption_token_states`,
`test_durability_uncertain_consumption_token_propagates`); 14 restart
reconstructibility — §6 (`test_tokens_are_pure_functions_of_durable_state`);
15 no mtime/clock/nonce — §6 (`test_no_wallclock_mtime_or_nonce_token_in_the_module`);
16–20 principal/credential/lifecycle/approval drift blocks create + consumption
appears + multi-drift — §7; 21 consumption appears before S2 — §7
(`…is_already_consumed_not_drift`); 23 stable path — §7/§8; 24 concurrent
mutation stale contender rejected — §8; 25 concurrent consumers one winner —
§8 (`test_concurrent_contenders_exactly_one_winner`); 26–29 crash before S1 /
after S1 / after S2-pre-create / after create — §9; 31 practical-limit — §10
(`test_residual_window_between_s2_reads_and_create_is_not_lock_protected`);
32 closed 12-field schema re-derived — §11.1; 33 `registry_state_digest`
semantic analysis — §11.2 (`test_registry_state_digest_computation_is_unchanged_from_1r14`);
34 schema-safe persistence search — §11 (none found);
35 durable deferral adjudication — §11.4; 36 V-15-2 three guards — §12
(parametrized `test_v15_2_guard_is_subset_invariant_with_explicit_authorized_set`);
37 unauthorized V-15-2 consumer challenge — §12.3; 38 V-15-3 scoped
monkeypatch — §13; 39 restoration / cross-test pollution — §13.3;
40 V-13-5-1 regression — §14; 41 replay/concurrency regression — §8/§14;
42 durability regression — §9; 43 `Gate9Result` discipline — §14;
44 no Gate 10 — §14; 45 runtime unchanged — §14; 46 Gate-5/6/7/8 regression
— §14 (parametrized byte-identity + scope).

Plus N-15-3-1 test-quality note (`test_1r15_2_suite_token_count_name_overstates_body`).

Stability: 56 passed run individually, in random order, and interleaved
with the `.1R.14` + `.1R.15` + `.1R.15.2` suites (**239 passed** in one
process). Concurrency stress: 8 consecutive loop runs, one winner every run.

---

## 16. `.1R.15.2` test-quality review (phase prompt §59)

The 44 `.1R.15.2` tests classified: token derivation (9 — snapshot shape,
per-token canonical source, resolver shape rejection, mutation-moves-token),
ordering (5 — S1-after-battery, S2-before-create, zero-I/O slice, two
captures), drift injection (8 — principal / credential / lifecycle /
approval / multi / consumption-appears / stable-after-window /
no-cache-across-retry), concurrency (2), crash/restart (3), guard hygiene
(2 — V-15-2 subset shape + unauthorized future consumer), monkeypatch
hygiene (2 — no raw assignment + restoration), regression/isolation (13 —
schema unchanged, store byte-unchanged, only-gate9-touched, V-13-5-1
before-S1, `Gate9Result` discipline, no-Gate-10 symbols, runtime check,
earlier-gates parametrized, deferral-documented-in-source).

Coverage is **genuine** — assertions match the mechanism, drift is injected
against **real canonical stores** (not monkeypatched expectations). One
**name-vs-proof overstatement** (finding N-15-3-1):

- **`test_snapshot_has_exactly_the_six_generation_tokens`** — the body
  asserts **exactly FIVE** tokens (`principal`, `credential`, `approval`,
  `lifecycle`, `consumption`). The "`_six_`" in the name is a harmless
  overstatement; the body is correct. Same class as the name-vs-proof notes
  `.1R.15` §25 recorded for the `.1R.14` suite. **INFO, non-blocking.**

No `.1R.15.2` test was found to assert less than its name claims in a way
that would mask a defect. `test_approval_drift_between_s1_and_s2_blocks_create`
uses a synthetic flipping resolver rather than a real approval-store
mutation — correct given N-15-3-2 (the coordinator delegates
`approval_generation`), and disclosed there.

---

## 17. Fixed-SHA A/B regression attribution (phase prompt §60)

**Baseline:** `d78d9676`. **Method:** dedicated `git worktree` at the
baseline SHA; `-p no:randomly -n0` for primary attribution (no xdist);
`git worktree remove` after. Concurrency stress run separately.

### 17.1 Deterministic `-n0` targeted set (Gate-9 impl/verify + 3 V-15-2 guard suites + adjacent Gate 5-8 + consumption store + `.1R.13.5`)

| Set | `d78d9676` | `735674f7` | Delta |
|---|---|---|---|
| `.1R.14` Gate-9 integration | 63 passed | 63 passed | 0 |
| `.1R.15` Gate-9 verification | 76 passed | 76 passed | 0 (resolver DI wired; 0 functional) |
| `.1R.15.2` focused suite | (file absent) | 44 passed | new |
| `.1R.15.3` this suite | (file absent) | 56 passed | new |
| 3 V-15-2 guard suites (isolated) | 16 failed / 110 passed | 13 failed / 113 passed | **+3 pass** (the converted guards) |
| Gate 5 / 6 / 7 / 8 + consumption store | 430 passed | 430 passed | 0 (modules + test files byte-identical) |

Aggregate targeted `-n0` at HEAD (14 files + 2 new suites): **12 failed /
783 passed**. The 12 failures are **a strict subset** of the 16 at
baseline: `test_blocking_reproduction_*` (×10), `test_deterministic_authenticator_is_non_real_but_no_real_verifier_exists_to_enforce_allowlist`,
`test_deterministic_attestation_encoding_has_contract_extra_fields` — all
pre-existing HPAC-foundation-reproduction / deterministic-fixture guards
from unrelated earlier phases, identical at `d78d9676`. The 4 that flipped
FAIL→PASS: the 3 V-15-2 guards (intended) + `test_concurrent_conflicting_successors_have_one_canonical_winner`
(the carried V-13-5-3 `_GATE6_DECISIONS` cross-file flake — passed the
deterministic HEAD run, failed the deterministic baseline run;
order/contention-sensitive at **both** SHAs, non-attributable — `.1R.15`
§26 recorded exactly this).

### 17.2 Wide advisory sweep (`-k "gate5 or gate6 or gate7 or gate8 or gate9 or permission_broker or runtime_dispatch or runtime_authority or hpac"`, `-n auto`)

HEAD: 42 failed / 2515 passed. Baseline: 44 failed / (comparable). The
`comm` diff of the sorted failure sets shows the 3 V-15-2 guards +
`test_concurrent_conflicting_successors_…` FAIL@baseline → not-in-HEAD-list,
and **one** node in the HEAD list not in the baseline list:
`test_gate6_permission_broker_production_consumption_3w1r2b1r1_1r12.py::test_gate5_results_registry_stays_empty_on_every_reject`.
**Investigated and dismissed as an xdist cross-file-pollution flake:** it
**passes** deterministically `-n0` at HEAD (isolated, in its full file, and
run immediately after this `.1R.15.3` suite); the Gate-6 production module
and its test file are **byte-identical** `d78d9676→735674f7`, so an
attributable regression is structurally impossible. This is the same
`_GATE5_RESULTS` / `_GATE6_DECISIONS` cross-file pollution class as
V-13-5-3, and the same "the single wide run happened to distribute it into
a polluting neighbourhood" phenomenon `.1R.15` §26 documented. Per phase
prompt §60, **xdist is not used for primary attribution**; the deterministic
`-n0` attribution (§17.1) is the authority.

### 17.3 Verdict

> **CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0.**
> **UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.**
> The only HEAD-vs-baseline functional delta is **+3 intended passes** (the
> V-15-2 guard conversions) and **+100 new passing tests** (the `.1R.15.2`
> and `.1R.15.3` suites). No production behavior regressed.

### 17.4 Concurrency stress

`test_concurrent_contenders_exactly_one_winner` (this suite),
`test_concurrent_authority_mutation_straddling_the_window_rejects`,
`.1R.15.2::test_concurrent_contenders_one_winner`,
`.1R.15::test_concurrency_repeated_no_second_record_ever` — run in an
8-iteration loop: **exactly one `consumed` and exactly one durable record
every iteration**; no second success; no `gate9_authority_generation_drift`
false positive on the stable path.

---

## 18. Runtime zero-effect proof (phase prompt §61)

Over the `.1R.15.3` + `.1R.15.2` + `.1R.14` + `.1R.15` suites at completion:

```
canonical local consumption-store writes = expected (tmp_path stores only; 0 under the repo tree — `find . -name consumption.json` clean)
runtime subprocess    = 0
adapter invocation    = 0
provider / network    = 0
credential operations = 0
hardware operations   = 0
Gate-10 effects       = 0
```

Test/git/PCAE CLI subprocesses (disclosed separately): `pytest`; read-only
`git diff` in this suite's ~8 scope/identity assertions + the `.1R.15.2`
suite's 3; one `git worktree add`/`remove` at `d78d9676` (removed); one
`sys.executable -m pytest` subprocess in `test_v15_2_guards_pass_at_head`;
the `pcae` governance CLI. `runtime_dispatch_gate9.py` imports nothing
effectful (`ast`-verified) and calls no Gate-10 adapter/subprocess/provider
primitive. `pcae runtime inspect` at finalization: `not_implemented /
Observed / observe / unavailable` — unchanged.

---

## 19. Findings

| ID | Severity | Summary | Disposition |
|---|---|---|---|
| **N-15-3-1** | INFO / test-quality | `.1R.15.2`'s `test_snapshot_has_exactly_the_six_generation_tokens` body asserts **five** tokens; the name says "six". Harmless overstatement (same class as `.1R.15` §25 notes). | Cosmetic; may be renamed in a future hygiene touch. **Not** a Gate-10 prerequisite. |
| **N-15-3-2** | INFO / carried to `.1R.15.4` | `approval_generation` is fully resolver-delegated; the coordinator holds no approval-store reference. An `approval_generation` computed as the immutable RIASC `record_digest` alone would **not** move on an approval revocation (HPAC-REQ-102 keeps revocation in a separate store) — so approval revocation **in the S1→S2 window** depends entirely on the (not-yet-written) production resolver. Non-blocking now (no production caller; approval revocation **before** S1 is caught by the step-9 `validate_approval` re-run). | **`.1R.15.4` requirement** (not option): the production `authority_generation_resolver` wiring MUST fold approval-revocation-store currentness into `approval_generation`. |
| **N-15-2-1** | INFO (carried from `.1R.15.2`) | Shared principal+credential registry document → a pure credential revocation also moves `principal_generation`. | Fail-safe (either token blocks the create); RDGO-001 §15 first/aggregate-mismatch convention. Confirmed correct. Not a prerequisite. |
| **N-15-2-2** | carried to `.1R.15.4` | Durable Gate-10 generation-snapshot representation requires a normative schema change. | `.1R.15.4`. Confirmed correct (§11). |

**No new blocking findings. No finding reopens a closed gate boundary. No
finding is class E (blocking clarification required).**

---

## 20. Adjudications (phase prompt §45, §48, §62, §63)

### V-15-1 (phase prompt §62)

> **V-15-1 — CLOSED FOR THE GATE-9 SERIALIZATION WINDOW.
> DURABLE GATE-10 SNAPSHOT REPRESENTATION DEFERRED (`.1R.15.4`).**
>
> Independently established: complete token coverage of the mutable
> authority sources the coordinator can token (principal / credential /
> lifecycle whole-record/full-chain digests; proof-state subsumed;
> consumption exact-state), with `approval_generation` correctly
> resolver-delegated (N-15-3-2 → `.1R.15.4`); S1 captured only after the
> full HPAC-REQ-099 battery; S2 re-read immediately before the create-only
> linearization with zero effectful I/O between the S2==S1 decision and
> `create`; fail-closed drift detection for every injected case (real-store
> and resolver-flip), zero `consumption.json` written; no stale contender
> success under concurrent mutation; one-shot / replay / crash / durability
> behavior **unchanged** from `.1R.14`. The residual instruction-level
> S2-reads→`create` micro-window (no lock spans it — `.1R.9` §18 forbids a
> second lock) is the **practical limit** without extending the create
> primitive (Option D, out of scope), produces **no external effect**
> (Gate 10 absent; §22 forward invariant re-validates), and is consistent
> with the intended semantics given that dependency. The durable /
> re-readable snapshot embedding is **correctly deferred** to `.1R.15.4`
> (HPAC-REQ-098 closed 12-field `authority_binding`; `registry_state_digest`
> cannot carry the vector within its grammar — independently re-derived,
> §11).

### V-15-2 (phase prompt §45)

> **V-15-2 — CLOSED.** §12.6.

### V-15-3 (phase prompt §48)

> **V-15-3 — CLOSED.** §13.4.

### Overall repair verdict (phase prompt §63)

> **INDEPENDENTLY VERIFIED — GATE-9 SERIALIZATION-SEMANTICS REPAIR
> COMPLETE**, with the explicit qualification: **DURABLE GATE-10
> GENERATION-SNAPSHOT REPRESENTATION: DEFERRED TO `.1R.15.4` CONTRACT
> NORMALIZATION.**
>
> V-15-1's Gate-9 serialization window closes; V-15-2 and V-15-3 close.
> Token coverage and ordering are complete for the sources the coordinator
> can token; the one carried gap (`approval_generation` resolver-delegation,
> N-15-3-2) is a `.1R.15.4` resolver-wiring requirement, not a hole in this
> repair. `.1R.15.2`'s production diff is `runtime_dispatch_gate9.py` only;
> no contract, POL-005, Gate 5/6/7/8, consumption-store-schema, or
> runtime-capability change. Fixed-SHA A/B (baseline `d78d9676`): 0
> candidate-only unexplained functional nonpassing nodes; 0 unexplained
> attributable functional regressions.

---

## 21. Gate-9 / Gate-10 separation (phase prompt §52–§53)

- `is_gate9_result(x) is True` means **provenance only** — both `consumed`
  and `already_consumed` results are `_GATE9_RESULTS` members; a future
  Gate 10 MUST additionally require `x.status == "consumed"` **and** re-read
  the durable `consumption.json` + containment evidence (in-source forward
  invariant, verbatim; `.1R.15.1` §22, unchanged).
- Production source has **no** Gate-10 module, **no** Gate-10 caller, **no**
  adapter dispatch, **no** external effect path from Gate 9 (`ast` +
  code-only scan, §14).
- Runtime: `State: Observed / Maximum Capability: observe / Execution
  Availability: unavailable`; **no** capability or plugin registration
  (§18).

---

## 22. Next phase (phase prompt §64)

> **`149O.20L.7O.3W.1R.2B.1R.1.1R.15.4` — Runtime-Dispatch Contract
> Normalization Implementation.**
>
> Scope (from `.1R.15.1` §24, unchanged): apply the §7–§18 proposed deltas
> — RDGO-001 → v3.1 (V-2 / V-3 / V-13-3-1 / V-13-5-1 / **V-15-1**);
> PBRD-001 → v2.1 (V-4); RIASC-001 errata; RE No-Go Registry → schema 1.1
> (V-13-3-2); phase-document errata (`.1R.9` §13.5, `.1R.13.1` §11.2 / §13 /
> §16.2, `.1R.13.2` prose) — **PLUS** the durable generation-snapshot
> representation deferred from `.1R.15.2` (§11.4; a new `authority_binding`
> field or a new binding object — a normative schema change) **PLUS** the
> production `authority_generation_resolver` completeness requirement from
> **N-15-3-2** (fold approval-revocation-store currentness into
> `approval_generation`).
>
> **NOT begun. Requires its own separate explicit human authorization.**

**Gate 10 remains WITHOUT a phase ID** until `.1R.15.5` closes VERIFIED and
the 10-item `.1R.15.1` §20 prerequisite list is satisfied (items 1 & 3 —
internally consistent contract model, Gate-9 semantics normalized — are
what `.1R.15.4` delivers; item 2 — V-15-1 resolved and verified — is
delivered by **this phase** for the serialization window). Do not invent an
ID.

---

## 23. Historical `.3` governance incident (phase prompt §65)

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED** — preserved
unchanged. No delegated worker committed, finalized, or pushed in this
phase. Only the primary human-authorized operator holds `.1R.15.3`
lifecycle authority.

---

## 24. Governance (phase prompt §66)

Governed `pcae` lifecycle only: `pcae session bootstrap`, `pcae task
transition` / `update`, `pcae commit implementation`, `pcae phase complete`,
`pcae push`. No raw `git commit` / `git push`, no `--no-verify`, no force
push, no history rewrite, no hook bypass, no rollback. The `git worktree`
at `d78d9676` was read-only (removed after the A/B).

---

## 25. Required final report (phase prompt §69)

- **Phase ID / title:** 149O.20L.7O.3W.1R.2B.1R.1.1R.15.3 — Independent
  Verification of the Gate-9 Atomic-Consumption Serialization-Semantics
  Repair.
- **Verification-entry SHA:** `735674f7`. **Immutable baseline:** `d78d9676`.
- **Exact `.1R.15.2` range:** §0.1 — functional commit `b32619e5` only;
  `git diff --name-only d78d9676 735674f7 -- src/` = `runtime_dispatch_gate9.py`.
- **Primary contracts / source inspected:** §0.3.
- **Independently reconstructed repair call flow:** §1.
- **S1 ordering:** captured only after battery steps 9–14 — §2 (source +
  instrumented).
- **S2 ordering:** immediately before `create` — §4.
- **S2→create operation inventory:** drift comparison + fail-closed return +
  `create`; **zero effectful I/O** — §4.
- **Zero-effectful-I/O result:** CONFIRMED (independent source slice) — §4.
- **Token inventory:** 5 tokens over 4 mutable authority sources + exact
  consumption state — §5.
- **Per-token completeness proofs:** principal/credential = whole-record
  digest moves on real revocation; lifecycle = full-chain digest moves on
  terminal event — §5.
- **Proof-state subsumption result:** SUBSUMED by `lifecycle_generation` —
  proven from HPAC-REQ-094/095 — §5.1.
- **Approval-state completeness result:** resolver-delegated; **N-15-3-2**
  → `.1R.15.4` resolver-wiring requirement — §5.2.
- **Consumption-state token result:** `("absent",)` / `("present", digest)`
  / durability-uncertain propagates fail-closed — §5.
- **Restart-reconstructibility:** all tokens pure functions of durable
  state; no process-local input — §6.
- **Principal / credential / lifecycle / approval / consumption-appearance /
  multi drift:** all fail closed, 0 records (consumption-appears →
  deterministic `already_consumed`, 1 pre-installed record) — §7.
- **Stable path:** exactly one create — §7/§8.
- **Concurrent mutation:** stale contender rejected, 0 records — §8.
- **Concurrency one-winner regression:** exactly one winner, 8/8 stress —
  §8/§17.4.
- **Crash before S1 / after S1 / after S2-pre-create / after create:**
  unconsumed / unconsumed / unconsumed / deterministic `already_consumed`
  (durable record controls restart) — §9.
- **Post-consumption drift:** consumption is durable history; retry cannot
  consume again; no retroactive delete — §9 + §14 (replay).
- **Practical-limit / remaining micro-window analysis:** §10 — window closed
  to the pure S2-reads→`create` span; residual instruction-level window is
  the practical limit without Option D; no external effect; `.1R.15.4` must
  normalize the contract text.
- **Independent closed-schema analysis:** `authority_binding` = closed
  12-field, no extension; 13th field → `HPACMalformedError` — §11.1.
- **`registry_state_digest` analysis:** flat registry/config digest; cannot
  carry the generation vector within grammar; computation byte-unchanged —
  §11.2/§11.3.
- **Durable representation search:** none found that `.1R.15.2` missed —
  §11.
- **Durable deferral adjudication:** **DURABLE SNAPSHOT DEFERRAL —
  CONFIRMED CORRECT** — §11.4.
- **V-15-1 adjudication:** **CLOSED FOR THE GATE-9 SERIALIZATION WINDOW;
  durable Gate-10 snapshot representation deferred** — §20.
- **V-15-2 adjudication:** **CLOSED** — §12.6.
- **V-15-3 adjudication:** **CLOSED** — §13.4.
- **V-13-5-1 regression:** containment read-back at step 8, before S1 —
  preserved — §14.
- **Replay / durability regressions:** deterministic `already_consumed`;
  crash table unchanged — §9/§14.
- **`Gate9Result` discipline:** provenance-only; `__reduce__` raises;
  identity-only `==`/`hash`; no new consumer — §14/§21.
- **Gate-10 isolation:** no module / caller / adapter / effect path — §21.
- **Runtime state:** `not_implemented / Observed / observe / unavailable`;
  0 plugins / 0 capabilities — §18/§21.
- **Gate-5/6/7/8 regressions:** none — production modules byte-identical;
  430 suite passes; Gate 5/6/7/8 reconfirmed CLOSED — §14.
- **Production-file scope:** `runtime_dispatch_gate9.py` only;
  `runtime_invocation_authority_consumption.py` byte-unchanged — §14.
- **Contract identity:** all 8 normative contracts byte-unchanged — §14.
- **Fresh independent tests:** 56, 0 failed — §15.
- **`.1R.15.2` test-quality review:** genuine coverage; one name-vs-proof
  overstatement (N-15-3-1) — §16.
- **Fixed-SHA A/B:** deterministic `-n0`; 0 candidate-only unexplained
  functional nonpassing nodes; 0 unexplained attributable functional
  regressions; +3 intended guard passes — §17.
- **Concurrency stress:** 8/8 one-winner — §17.4.
- **Candidate-only regression count:** **0.**
- **Runtime / no-effect proof:** 0 subprocess / adapter / provider /
  credential / hardware / Gate-10 effect — §18.
- **Overall verdict:** **INDEPENDENTLY VERIFIED — GATE-9
  SERIALIZATION-SEMANTICS REPAIR COMPLETE; durable Gate-10
  generation-snapshot representation DEFERRED TO `.1R.15.4`.**
- **`.1R.15.4` recommendation:** §22 — Runtime-Dispatch Contract
  Normalization Implementation (the `.1R.15.1` §7–§18 deltas + the deferred
  durable representation + the N-15-3-2 resolver-completeness requirement).
  NOT begun.
- **`.1R.15.3` commits:** see `.pcae/phase-completion-metadata.json`
  `phase_commits` after governed finalization.
- **Pushed status:** recorded at finalization (`pushed`).
- **`origin/main..HEAD` after finalization:** `0`.

---

## No-Go Confirmations

- No production source changed; `git diff --name-only 735674f7 HEAD -- src/pcae` is empty for this phase (verification only — one new test file).
- No normative contract file changed; RDGO-001, PBRD-001, RIHAC-001, RIASC-001, HPAC-001, RPAC-001, PBPA-001, POL-005 all byte-unchanged.
- No production defect repaired in this phase; V-15-1's in-memory linearization guard, V-15-2's guard conversion, and V-15-3's monkeypatch fix are all `.1R.15.2` work, independently verified here, not re-implemented.
- No consumption-record schema change; `runtime_invocation_authority_consumption.py` byte-unchanged; `authority_binding` remains the closed 12-field set.
- No durable generation-snapshot representation added; the deferral to `.1R.15.4` is CONFIRMED CORRECT, not overridden.
- No second global lock, transaction system, or bearer object introduced or recommended for `.1R.15.3`.
- No Gate-10 design, module, symbol, phase ID, adapter, subprocess, provider, network, credential, or hardware path.
- No `.1R.15.4` work begun; no contract edited, no phase-document erratum applied, no durable-snapshot representation designed.
- No execution enabled; runtime remains `not_implemented / Observed / observe / unavailable`; no capability registration.
- No real FIDO2 / WebAuthn / CTAP / protected UI / physical authenticator access.
- No approval / proof / presentation / challenge / nonce consumed on any production path; no `consumption.json` created outside disposable `tmp_path` test stores.
- No third-party system, unrelated account, external credential, provider API, external network, or deployment target accessed.
- No test weakened; the concurrency-loser tests retain the RDGO-001 §18 one-winner / one-record guarantee.
- No raw `git commit` / `git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass; the baseline `git worktree` was read-only and removed.
- No delegated worker committed, finalized, or pushed; only the primary human-authorized operator holds `.1R.15.3` lifecycle authority.
- No begin of `.1R.15.4` / `.1R.15.5`; each needs its own explicit human authorization.
- No reopening of a closed gate boundary (Gate 5 / 6 / 7 / 8); their production modules are byte-unchanged.
- No self-authored closure without evidence: V-15-1 (window) / V-15-2 / V-15-3 closures each rest on independently re-derived primary-source analysis + a fresh 56-test suite + fixed-SHA A/B.
- No Gate-10 phase ID invented; Gate 10 stays WITHOUT an ID until `.1R.15.5` closes VERIFIED and the §20 prerequisites hold.

---
*Canonical independent-verification report. Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.3.*
