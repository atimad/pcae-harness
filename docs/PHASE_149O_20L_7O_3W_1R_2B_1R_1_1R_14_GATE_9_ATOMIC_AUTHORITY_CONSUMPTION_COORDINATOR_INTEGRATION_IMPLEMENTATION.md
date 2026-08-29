# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.14 — Gate-9 Atomic Authority Consumption Coordinator Integration Implementation

Status: **IMPLEMENTED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**

Gate-9 Atomic Authority Consumption Coordinator: **IMPLEMENTED**. Not
verified. Not execution-ready. `.1R.15` (Independent Verification of Gate-9)
is the required next phase and is **not begun**.

Phase-entry SHA: `c1ea2c8b` (`.1R.13.5` complete — Gate 8 CLOSED, verified).
Implementation commits: `9103d9cf` (coordinator + V-13-1 guard extensions) →
`9fba3251` (concurrency-loser / crash-after-commit hardening + last guard
conversion). Pushed status / `origin/main..HEAD`: recorded by the governed
finalization sequence.

---

## 1. Scope and authorization

This phase implements **only** the Gate-9 authority-consumption slice
frozen by `.1R.9` §16.1 (slice 3) / §16.2 (`.1R.14` phase ID) and unblocked
by `.1R.13.5` (all eight `.1R.13.1` §17 criteria SATISFIED, Gate-8 CLOSED,
the §16 Gate-8 → Gate-9 handoff contract independently re-reviewed). The
explicit human authorization for this phase also records the **test-path-
first scope** of `.1R.9` §16.1 row 3 / §29 — production Gate 9 is
structurally unreachable (permanent NON-REAL upstream; the real Gate-7
coordinator always returns `DENY`), so the atomic-consumption envelope is
exercised only through a clearly-labelled test-only substitution of the
upstream provenance predicates against a test-scoped consumption store.

Not done (frozen out): `.1R.15` not begun; Gate 10 not implemented and not
assigned an ID; no runtime execution enabled; no real FIDO2 / WebAuthn /
CTAP / protected UI / trusted display / enrollment ceremony; no contract
modified.

Defensive engineering on PCAE source and local repository state only. No
third-party system, unrelated account, external credential, provider API,
external network, physical authenticator, or the Dell deployment target was
accessed. Local subprocesses used: `pytest`, read-only `git` inspection, one
`git worktree` at `c1ea2c8b` (removed), and the `pcae` governance CLI.

---

## 2. Governing prerequisites (verified current)

| Gate | State | Evidence |
|---|---|---|
| Gate 5 | CLOSED — non-consuming; NON-REAL hard stop | `.1R.11` |
| Gate 6 | CLOSED — permission only; POL-005 preserved | `.1R.13` |
| Gate 7 | CLOSED — current posture DENY; no consumption | `.1R.13.3` |
| Gate 8 | CLOSED — containment validation only; no effect; no consumption | `.1R.13.5` (HEAD `c1ea2c8b`) |

Gate 9 is the **first authority-consumption boundary**. Gate 10 remains the
first external-effect boundary and is untouched.

```text
Gate 5/6/7/8 = validation / decision / containment = consume nothing
Gate 9       = atomic one-shot authority consumption
Gate 10      = first external effect
```

Runtime at phase entry and exit: `not_implemented / Observed / observe /
unavailable`; registry empty; POL-005 byte-unchanged; real execution
UNAVAILABLE.

---

## 3. Primary source material read in full

- `PROJECT_STATUS.md`, `CHANGELOG.md` (current tree).
- Phase documents: `.1R.9` (Gate-5/Gate-9 planning — §6-§25, esp. §10-§19,
  §16, §25 production-file matrix, §21 NON-REAL, §29 STOP conditions),
  `.1R.13.1` (Gate-7/Gate-8 planning — §16 Gate-8 → Gate-9 handoff contract,
  §17 unblocking criteria, §18 no consumption at 7/8, §22 V-13-1
  disposition), `.1R.13.4` (Gate-8 impl), `.1R.13.5` (Gate-8 independent
  verification — V-13-5-1 / V-13-5-2 / V-13-5-3), `.1R.13.3` (Gate-7
  verification — V-13-3-1 / V-13-3-2), `.1R.13` (Gate-6 verification — V-4),
  `.1R.11` (Gate-5 verification — V-2 / V-3, IF-1), `.1R.8` (B1/B7/N1/N2
  verification — O1-O4, F2/F3/F4/F7).
- Contracts (byte-identity re-confirmed since `c1ea2c8b`, see §14):
  RDGO-001 v3.0, RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-001 v2.0,
  PBRD-001 v2.0, RPAC-001 v1.0, PBPA-001 / POL-005
  (`permission_broker_foundation.ExecutionDisabledRule`),
  `RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` §10 (Gate 9).
- Production source: `runtime_invocation_authority_consumption.py` (inert
  Gate-9 model/store — `RuntimeInvocationAuthorityConsumption`,
  `_BINDING_FIELD_SETS`, `RuntimeInvocationAuthorityConsumptionStore.create`
  / `.resolve`, `...DurabilityUncertainError`, `new_inert_consumption_record`),
  `runtime_dispatch_gate8.py` (`run_gate8_process_containment`, `Gate8Result`,
  `is_gate8_result`, `Gate8EffectPlan`, `ResolvedExecutable`,
  `_gate7_result_digest`), `runtime_dispatch_gate7.py` (`Gate7Result`,
  `is_gate7_result`), `runtime_dispatch_permission.py` (`Gate6Decision`,
  `is_gate6_decision`, `RuntimeDispatchIdentity`,
  `RuntimeDispatchRequestConstructionInput`,
  `_expected_subject_scope_binding_digest`, `_validate_construction_inputs`),
  `runtime_dispatch_gate5.py` (`Gate5Result`, `is_gate5_result`),
  `runtime_authority.py` (`ValidatedAuthorityProjection`,
  `is_trusted_validated_authority_projection`,
  `revalidate_validated_authority_projection`, `compute_canonical_digest`,
  `PROMPT_HASH_PROFILE`), `hpac_lifecycle.py`
  (`HPACLifecycleStore.resolve_gate5_binding_event`,
  `STATE_PROOF_VERIFIED_AND_BOUND`, `LifecycleEvent`), `hpac_foundation.py`
  (`write_atomic_create_only`, `HPACDuplicateError`, `canonical_digest`,
  `reject_symlink`, `HPAC_PROTECTED_ROOT` resolution),
  `runtime_introspection.py` (frozen `Observed / observe / unavailable`).

Gate-9 semantics were re-derived from RDGO-001 §10 / RIHAC-001 §17,§19 /
HPAC-REQ-098/099/100/101/102, not inferred from helper names.

---

## 4. Gate-9 core contract (re-derived)

```text
full current-state revalidation inside the protected serialization boundary
                              +
atomic one-shot proof + approval consumption

Required invariant:   proof consumed  IFF  approval consumed
There is no valid state where only one of {proof, approval} is consumed.
```

RDGO-001 §10: one create-only, crash-consistent, read-back-verified commit
of the closed eight-item `HPAC-AUTHORITY-CONSUMPTION/2.0` record at
`<root>/proofs/v2/<proof_id>/consumption.json`, completed **before** Gate
10. `dispatch_attempted` is the single atomic
presentation/challenge/proof/approval consumption point and at-most-once
guard (HPAC-REQ-098). No mutable `consumed` field anywhere; "consumed" ≡
"one complete valid record exists at the proof's protected path". The RIHAC
repository approval store is never mutated (HPAC-REQ-102). In-boundary
revalidation is mandatory and never substituted by Gate-5 validation
(HPAC-REQ-099). Only two recoverable crash outcomes: final artifact absent
(not consumed; no Gate-10 effect) or one complete valid artifact present
(consumed; replay rejected) — anything else is durability-uncertain → fail
closed, never reusable authority (HPAC-REQ-100/101).

---

## 5. Production file changed

| File | Change | Authority sensitivity |
|---|---|---|
| `src/pcae/core/runtime_dispatch_gate9.py` **(new, ~640 lines)** | Gate-9 atomic-consumption coordinator: serialization boundary, in-boundary revalidation battery, closed 8-item record construction, `RuntimeInvocationAuthorityConsumptionStore.create` call, crash/replay/concurrency disposition, ephemeral `Gate9Result` | **Critical** |

`git diff c1ea2c8b HEAD -- src/pcae` = exactly
`src/pcae/core/runtime_dispatch_gate9.py`. No other production source
touched. `runtime_invocation_authority_consumption.py` (the inert store) is
consumed **unchanged** — its create-only atomicity, duplicate rejection,
symlink rejection, digest self-check, and durability-uncertain
classification already satisfy every Gate-9 need (`.1R.9` §10.2 / §16.2;
prompt §5 / §16.1 slice 3). Gate 5/6/7/8, `permission_broker_foundation.py`,
`shell_gate.py`, `runtime_introspection.py`, and all nine contracts are
byte-unchanged (§14).

Test files touched: the new `.1R.14` suite plus **phase-aware V-13-1 guard
extensions** in ten earlier suites (§13).

---

## 6. Sole Gate-9 owner

`run_gate9_atomic_authority_consumption(...)` in `runtime_dispatch_gate9.py`
is the frozen **sole** production owner of the RDGO-001 §10 boundary. It
owns: the serialization boundary acquisition, the HPAC-REQ-099 in-boundary
revalidation battery, the closed 8-item record build, outcome encoding, and
the crash/replay/concurrency disposition. The store
(`RuntimeInvocationAuthorityConsumptionStore`) owns **only** the atomic
create-only persistence primitive (`write_atomic_create_only` — `O_EXCL`
temp sibling + atomic link-if-absent + fsync + read-back) and duplicate
rejection (`HPACDuplicateError`). No semantic ownership is split ambiguously
across caller and store.

`git grep -E "run_gate9_atomic_authority_consumption|_GATE9_RESULTS" -- src/pcae`
→ `{runtime_dispatch_gate9.py}` only.

Signature (frozen, all keyword-only after the first positional):

```python
run_gate9_atomic_authority_consumption(
    gate8_result, *, gate7_result, gate6_decision, gate5_result,
    identity, inputs, authority_current_time, repo_root, effect_plan,
    descriptor_resolver, lifecycle_store, consumption_store,
    capability_snapshot_resolver,
) -> tuple[Optional[Gate9Result], tuple[str, ...]]
```

This is the `.1R.13.1` §16.3 in-process assembly of the five trusted
objects + `identity` + `inputs` + a fresh capability snapshot, passed as
explicit keyword arguments. Not serialized, not persisted before the atomic
write, not a bearer token.

---

## 7. Gate8Result provenance + §8 affirmative-containment requirement

Gate 9's first check is `runtime_dispatch_gate8.is_gate8_result(gate8_result)`
— exact-object registry membership, never type / fields / digest / copied /
reconstructed / serialized / `object.__new__` (RDGO-001 §9/§10; the B1
class). `Gate8Result.__reduce__` raises; `copy.deepcopy` raises; a bare
`object.__new__(Gate8Result)` is not a registry member.

**Provenance is not containment success.** Immediately after the provenance
check, Gate 9 requires `gate8_result.containment_established is True` (by
identity). A trusted **negative** `Gate8Result(containment_established=False)`
— the real Gate-8 output today whenever any containment check fails — is a
hard stop `gate9_gate8_containment_not_established` **before** any lock-side
consumption attempt, before proof consumption, before approval consumption.
Test `test_trusted_negative_gate8_result_rejected_before_any_consumption`
proves the store's `create` spy is never called and no `consumption.json`
is written.

---

## 8. Current positive production reachability

Production Gate 9 is **structurally unreachable** today, for independent
reasons any one of which is sufficient:

- the real `run_gate5` never returns a `Gate5Result` (permanent NON-REAL
  hard stop at `validate_approval` — `non_real_authenticated_principal_cannot_validate_production_approval`);
- the real `run_gate7_runtime_enforcement` always returns
  `Gate7Result(decision="DENY")` (current posture: `RE-NOGO-002` etc.), so
  Gate 8's positive branch is unreachable and no positive `Gate8Result`
  exists;
- `full_chain(simulation_only=False)` yields `projection is None`.

No production-real `Gate8Result` / `Gate7Result` / `Gate6Decision` /
`Gate5Result` / `ValidatedAuthorityProjection` / approval / runtime
capability was fabricated. The consumption branches are reached only through
a clearly-labelled substitution of the upstream provenance predicates
(`monkeypatch` on `is_gate5_result` / `is_gate6_decision` / `is_gate7_result`
and the projection-trust predicates in the `runtime_dispatch_gate8` /
`runtime_dispatch_gate9` namespaces) plus a `tmp_path` consumption store and
a **real** HPAC lifecycle sequence-3 event built through the canonical
fixture writers (`test_hpac_verifier._Rig`). This is the `.1R.9` §21.4
test-only path, not a development bypass: it exercises the store's and
coordinator's atomicity / crash / replay / concurrency behaviour against a
structurally correct payload and cannot produce production authority.

`test_real_predicates_make_production_gate9_unreachable` confirms that with
NO substitution a hand-built synthetic upstream is refused at the first
gate. `test_non_real_gate5_never_yields_gate5result_for_gate9` confirms the
real `run_gate5` on a canonical deterministic chain returns no
`Gate5Result`.

---

## 9. Gate-8 → Gate-9 handoff (`.1R.13.1` §16 — every field mapped)

Gate 9 independently maps every `Gate8Result` field it uses. Names are the
exact current source names.

| `.1R.13.1` §16.1 category | `Gate8Result` field(s) consumed by Gate 9 | How Gate 9 uses it |
|---|---|---|
| containment state | `containment_established` | must be `True` (§7) |
| containment evidence reference | `containment_evidence_digest` | recomputed + compared (§11) |
| invocation ID | `invocation_id` | equal across g5/g6/g7/g8/identity (§10) |
| attempt ID | `attempt_id` | equal across g6/g7/g8/identity (§10) |
| request ID | `request_id` | equal across g6/g7/g8 (§10) |
| Gate7 lineage digest | `gate7_result_digest` | `== runtime_dispatch_gate8._gate7_result_digest(gate7_result)` → `gate9_gate7_lineage_mismatch` |
| effect-plan digest | `effect_plan_digest` | recomputed + compared (§13) |
| live-preflight digest | `live_preflight_digest` | recomputed + compared |
| shell-gate decision/category | `shell_gate_decision` / `shell_gate_category` | carried into the recompute cross-check via the Gate-8 re-run |
| expiry / evaluated time | `expires_at` / `evaluated_at` | carried transitively via the Gate-7 result and the re-run |
| causing reason IDs | `causing_reason_ids` | only meaningful on the negative branch — a negative result is refused at §7 |

Gate 9 also re-derives the `Gate7Result` (via `is_gate7_result` + exact
`decision == "ALLOW"`), the `Gate6Decision` (via `is_gate6_decision` + exact
`decision == "ALLOW"`), and the `Gate5Result` (via `is_gate5_result`);
carries `RuntimeDispatchIdentity`
(`invocation_id`/`attempt_id`/`idempotency_key`) and
`RuntimeDispatchRequestConstructionInput`
(repository/task/target/prompt/adapter bindings); and re-reads a fresh
capability snapshot inside the boundary (§13 of this doc).

### `.1R.13.1` §16.2 handoff invariants — all enforced

1. **Exact-object provenance at every link** — `is_gate8_result` /
   `is_gate7_result` / `is_gate6_decision` / `is_gate5_result`; no
   field-reconstruction, copy, or serialized clone accepted at any link.
2. **Single consistent invocation** — `invocation_id` and `attempt_id`
   equal across Gate5Result / Gate6Decision / Gate7Result / Gate8Result /
   identity; `request_id` equal across g6/g7/g8. Cross-invocation
   consumption → `gate9_invocation_binding_mismatch`.
3. **Containment binding** — `containment_evidence_digest` recomputed by
   Gate 9 from current canonical inputs and compared (§11).
4. **In-boundary revalidation** — projection re-trust + revalidate
   (re-runs `validate_approval` → registry / credential / proof / approval
   / expiry / consumption-state), subject/scope digest recompute, sequence-3
   binding compare, capability re-read, absence-of-record check — all
   performed at the point immediately before the atomic create. A
   `Gate7Result` / `Gate8Result` valid moments earlier but now stale fails
   closed with no `consumption.json`.
5. **Consumption happens only at Gate 9** — neither the `Gate7Result` nor
   the `Gate8Result` is consumed by being handed to Gate 9; the atomic
   `dispatch_attempted` write is the single consumption point.
6. **No effect** — the handoff carries data only; Gate 9's write is a local
   canonical-store write, categorically distinct from any external process
   effect (§12 of this doc; §50 evidence).

---

## 10. Invocation / attempt / request lineage (§14 of the prompt)

`gate9_invocation_binding_mismatch` is returned unless **all** of:

```text
gate5_result.invocation_id == gate6_decision.invocation_id == gate7_result.invocation_id
    == gate8_result.invocation_id == identity.invocation_id
gate6_decision.attempt_id == gate7_result.attempt_id == gate8_result.attempt_id == identity.attempt_id
gate7_result.request_id == gate6_decision.request_id == gate8_result.request_id
```

Subject / scope lineage is re-enforced by recomputing
`_expected_subject_scope_binding_digest(identity, inputs)` and requiring
`projection.subject_scope_binding_digest ==` it
(`gate9_authority_subject_scope_mismatch`) — done both early (step 7a) and
again inside the boundary (step 9). Tests: `test_invocation_mismatch_rejected`,
`test_attempt_mismatch_rejected`, `test_request_id_mismatch_rejected`,
`test_subject_scope_binding_mismatch_rejected`.

---

## 11. V-13-5-1 as a Gate-9 acceptance condition (§11-§13 of the prompt)

`.1R.13.5` accepted incomplete direct cwd/environment/transport drift
detection at Gate 8 **only because Gate 9 is required to read back and
recompute the full containment evidence** (V-13-5-1, LOW). This phase closes
that dependency:

**Gate 9 independently reconstructs the current containment evidence from
current canonical inputs and requires the recomputed digests to equal the
ones carried by the handed `Gate8Result` — no stored digest is treated as
self-authenticating.**

Mechanism: Gate 9 re-runs the **Gate-8 owner**
`run_gate8_process_containment` over the *same* trusted upstream objects
(`gate7_result`, `gate5_result`, `identity`, `inputs`) + a **freshly
re-resolved** `descriptor_resolver` (executable identity/hash), a
freshly-resolved repository-scoped `cwd`, `env_allowlist`, containment
profile, network-denied, credentials-required, argv, descriptor/config
identity, and runtime target — every bound field frozen by
`.1R.13.1` §11.2 / §25 and `.1R.13.5`. It then requires:

```text
fresh_gate8 is not None  and  fresh_gate8.containment_established is True
fresh_gate8.containment_evidence_digest == gate8_result.containment_evidence_digest
fresh_gate8.effect_plan_digest          == gate8_result.effect_plan_digest
fresh_gate8.live_preflight_digest        == gate8_result.live_preflight_digest
fresh_gate8.gate7_result_digest          == gate8_result.gate7_result_digest
```

Any material drift → `gate9_containment_recomputation_failed` or
`gate9_containment_evidence_recomputation_mismatch`, **before** consumption,
with no `consumption.json`. Re-running the Gate-8 owner (rather than
duplicating its digest formulas) keeps Gate 8 the single owner of
containment-evidence computation (`.1R.9` §10.1 "no split ownership") while
giving Gate 9 a genuine independent recomputation from current canonical
state. The re-run consumes nothing, writes nothing, and — because
`run_gate8_process_containment` imports no effectful module and refuses any
pytest-class program before touching the Shell Gate classifier — performs
no external effect. Tests:
`test_effect_plan_drift_rejected_by_recomputation`,
`test_executable_drift_rejected_by_recomputation`,
`test_cwd_outside_repository_rejected_by_recomputation`,
`test_gate7_lineage_digest_mismatch_rejected`.

### V-13-5-1 disposition

> **V-13-5-1 — SATISFIED AT GATE 9 (no longer a carried finding for the
> runtime-dispatch consumption path).** Gate 9's containment-evidence
> read-back + recomputation is the mechanism `.1R.13.5` §11.2/§25 named as
> the reason Gate 8's incomplete direct drift detection was non-blocking.
> The frozen `.1R.13.1` §11.2/§25 wording remains internally inconsistent
> (the `gate8_transport_drift` row has no enforcing check anywhere, and the
> `RuntimeDispatchRequestConstructionInput` still binds no cwd/env ref) —
> that **contract-text** cleanup is still owed and belongs to the dedicated
> contract-clarification phase alongside V-2/V-3/V-4/V-13-3-1/V-13-3-2. It
> is not a Gate-9 defect and does not block `.1R.15`.

---

## 12. Serialization boundary + revalidation-after-lock (§21-§22 of the prompt)

**Lock/transaction owner:** the Gate-9 coordinator. **Scope:** exactly the
per-`proof_id` protected directory `<root>/proofs/v2/<proof_id>/`.
**Mechanism:** the create-only atomic primitive `write_atomic_create_only`
(`O_EXCL` on the temp sibling + atomic `os.link`-if-absent + `fsync` +
`fsync` parent) **is itself the serialization boundary** — `.1R.9` §18
"Do not invent a new lock; the protected create-only commit is itself the
atomic transaction". No second transaction mechanism is introduced.
**Ordering:** a single boundary per Gate-9 invocation, entered after the
five trusted objects are assembled and the Gate-8 re-run has recomputed the
containment evidence, exited when `create` returns or raises. **Lifetime:**
the duration of the in-boundary battery + the atomic create. **Deadlock:**
impossible — one primitive, no nested acquisition. **Crash while held:** the
OS releases nothing to release; on-disk state is governed solely by
HPAC-REQ-100's two-outcome rule. **Stale lock:** n/a — there is no advisory
lock file; the record's presence/absence is the only fact.

**Revalidation occurs after the boundary is entered, not before it.** The
order is exactly:

```text
enter the per-proof_id create-only boundary
  ↓  re-trust + revalidate the projection      (re-runs validate_approval)
  ↓  recompute + compare subject/scope digest
  ↓  confirm HPAC lifecycle sequence-3 binding  (read-only)
  ↓  confirm exact proof + approval pairing
  ↓  re-read the runtime capability snapshot
  ↓  check absence of a consumption record
  ↓  atomic create-only commit
  ↓  read-back verify
```

An early (cheap) projection-trust + subject/scope pre-check runs *before*
the Gate-8 re-run as an additional early stop — it is **not** a substitute
for the in-boundary battery, which re-runs every mutable-state check.
Tests: `test_stale_projection_rejected_inside_boundary`,
`test_untrusted_projection_rejected_inside_boundary`.

---

## 13. In-boundary revalidation — principal / credential / proof / approval

Gate 9 re-trusts the referenced `ValidatedAuthorityProjection`
(`is_trusted_validated_authority_projection` — exact-object registry +
recomputed content-binding digest) and calls
`revalidate_validated_authority_projection(projection,
current_time=authority_current_time)`. `revalidate` **re-runs
`validate_approval`**, which re-resolves: canonical principal state
(revoked / disabled / identity mismatch), canonical credential state
(revoked / invalid), proof canonical provenance / identity / lifecycle
state / expiry / revocation / already-consumed, canonical approval
provenance / invocation binding / principal binding / expiry / revocation /
already-consumed. Any of these failing → `False` →
`gate9_stale_validated_authority_projection`, no `consumption.json`
(HPAC-REQ-099; `.1R.9` §12). Gate-5's earlier validation is an advisory
prerequisite, never the final currentness authority (`.1R.9` §12; prompt
§16-§19, §22).

**Proof + approval exact pairing** (§20 of the prompt): Gate 9 requires
`gate5_result.approval_id == projection.approval_id`,
`gate5_result.proof_id == projection.proof_id`, and
`gate5_result.invocation_id == identity.invocation_id`
(`gate9_proof_approval_pairing_mismatch`). Proof A + approval B, or a
proof/approval from another invocation/challenge/principal, is refused. The
HPAC lifecycle sequence-3 `PROOF_VERIFIED_AND_BOUND` event is re-resolved
through the trusted read-only `HPACLifecycleStore.resolve_gate5_binding_event`
and its genesis binding (`approval_id`, `invocation_id`, `principal_id`) and
canonical `event_digest` are re-confirmed — cross-binding →
`gate9_sequence3_cross_binding`, absent → `...proof_verified_and_bound_absent`.

**Current principal / credential state inside the boundary** (§16-§17 of the
prompt): established transitively through `revalidate` (which re-runs
`reverify_authenticated_principal` inside `validate_approval` — HPAC-REQ-054
steps 1-2 principal + credential currentness). Gate 9 does not re-implement
principal resolution; it composes the already-verified owner. Tests:
`test_stale_projection_rejected_inside_boundary`,
`test_proof_approval_pairing_mismatch_rejected`,
`test_sequence3_cross_binding_rejected`.

---

## 14. Contract byte-identity (§45 of the prompt)

`git diff c1ea2c8b HEAD -- docs/contracts src/pcae/core/permission_broker_foundation.py
src/pcae/core/shell_gate.py src/pcae/core/runtime_dispatch_gate5.py
src/pcae/core/runtime_dispatch_gate7.py src/pcae/core/runtime_dispatch_gate8.py
src/pcae/core/runtime_dispatch_permission.py src/pcae/core/runtime_introspection.py
src/pcae/core/runtime_invocation_authority_consumption.py src/pcae/core/hpac_lifecycle.py
src/pcae/core/runtime_authority.py`
→ **empty**. Verified in-suite by
`test_contracts_and_earlier_gates_bytes_unchanged_since_baseline`
(`.1R.14`) and by the unchanged `.1R.13.4` / `.1R.13.5` contract-identity
guards. RDGO-001 v3.0, RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-001 v2.0,
PBRD-001 v2.0, RPAC-001 v1.0, PBPA-001 / POL-005 — all byte-unchanged. No
contract cleanup in `.1R.14`.

---

## 15. Gate9Result model + forward invariant (§30-§31 of the prompt)

`Gate9Result` (`__slots__`, sealed constructor, `__reduce__` raises,
`__eq__`/`__hash__` are `id`-based, `__init_subclass__` raises). Fields:
`status` ∈ `{"consumed", "already_consumed"}`, `proof_id`, `approval_id`,
`record_digest`, `dispatch_state` (`"dispatch_attempted"`), `invocation_id`,
`attempt_id`, `consumed_at`, `advisory_reasons`.

- **Not caller-constructable** — `test_gate9_result_not_caller_constructable`.
- **Not serializable / not transferable** — `pickle.dumps` raises,
  `copy.deepcopy` raises, `object.__new__(Gate9Result)` is not a registry
  member — `test_gate9_result_non_transferable_and_non_serializable`.
- **Identity equality only** — `test_gate9_result_identity_equality_only`.
- **Not subclassable** — `test_gate9_result_not_subclassable`.
- **Distinguishes** consumption success (`status == "consumed"`) from
  already-consumed (`status == "already_consumed"`); a denied / stale /
  conflict outcome returns `(None, reasons)`, not a `Gate9Result`.

**`is_gate9_result` is provenance only, not success.** It is `isinstance` +
`_GATE9_RESULTS` membership — nothing else. Both a `"consumed"` and an
`"already_consumed"` result are registry members. **Frozen forward
invariant:** a future Gate 10 MUST NOT treat `is_gate9_result(x) is True` as
sufficient — it MUST additionally require `x.status == "consumed"` **and**
re-read the durable `consumption.json` + containment evidence, never trust
the in-memory marker. Stated verbatim in the module docstring and in
`Gate9Result`'s class docstring; `test_is_gate9_result_is_provenance_not_success`
pins it. `Gate9Result` has **zero downstream production consumers** (Gate 10
does not exist) —
`git grep -E "Gate9Result|is_gate9_result" -- src/pcae` →
`{runtime_dispatch_gate9.py}` only.

---

## 16. One-shot / replay / concurrency / crash (§24-§29 of the prompt)

| Case | Behaviour | Test |
|---|---|---|
| first valid consumption (test path only) | one valid `consumption.json`; `status == "consumed"`; read-back verified | `test_first_valid_consumption_succeeds_in_test_path_only` |
| duplicate identical request | `status == "already_consumed"`, `("gate9_already_consumed",)`; no second record | `test_duplicate_identical_request_reports_already_consumed` |
| same `Gate8Result` replayed | already-consumed, never a second success | `test_replayed_stale_gate8_result_second_attempt_never_a_second_success` |
| copied / reconstructed / `object.__new__` `Gate8Result` | `gate9_untrusted_gate8_result` | `test_object_new_gate8_result_rejected`, `test_copied_reconstructed_serialized_gate8_result_rejected` |
| trusted negative `Gate8Result` | `gate9_gate8_containment_not_established` — no lock-side attempt, no proof/approval consumption | `test_trusted_negative_gate8_result_rejected_before_any_consumption` |
| different proof + already-consumed approval | sequence-3 for the new proof id does not resolve → fail closed; no second record | `test_different_proof_same_consumed_approval_is_rejected` |
| cross-invocation request | `gate9_invocation_binding_mismatch` | §10 tests |
| concurrent requests (4 threads, same authority) | exactly one `"consumed"`; the other 3 are `"already_consumed"` or fail-closed; exactly one canonical record; no split-brain | `test_concurrent_requests_yield_exactly_one_success` (stable over repeated runs) |
| crash before commit | `create` raises without writing → `gate9_atomic_commit_failed`; `resolve` → `None`; proof & approval unconsumed; no Gate-10 effect | `test_crash_before_commit_leaves_both_unconsumed` |
| crash after commit | record durably present → coordinator detects it and returns `already_consumed`; never a second write; never continue-to-effect | `test_crash_after_commit_retry_reports_consumed` |
| ambiguous / partial / corrupt record | `...DurabilityUncertainError` → `gate9_consumption_state_durability_uncertain` → fail closed, never replay | `test_ambiguous_durability_uncertain_fails_closed` |
| restart | a fresh store object over the same root resolves the record → `already_consumed`; canonical durable state is the authority, not the (absent) process-local `Gate9Result` | `test_canonical_durable_record_is_authority_across_restart` |
| no partial consumption | a single record covers proof + approval; one file only | `test_no_partial_consumption_single_record_covers_proof_and_approval` |

Concurrency-loser hardening (`9fba3251`): a non-duplicate `create` error
that races another creator for the same fresh proof directory now
re-resolves — if a complete valid record is durably present, the outcome is
deterministically `already_consumed`; otherwise nothing was consumed and it
fails closed. No second success is ever produced.

---

## 17. Atomic single-record model (§23 of the prompt)

Gate 9 populates the closed eight binding groups of
`RuntimeInvocationAuthorityConsumption` (via the unchanged
`new_inert_consumption_record`, which enforces the exact
`_BINDING_FIELD_SETS` closed field sets) from **real** Gate-1..8 evidence:
`request_identity` from `identity`; `repository_task_binding` /
`target_binding` / `prompt_binding` from `inputs`; `authority_binding` from
the re-trusted projection + `gate5_result` + the sequence-3 genesis
binding; `pb_binding` / `runtime_enforcement_binding` from `gate6_decision`
/ `gate7_result`; `dispatch_binding` from the freshly-recomputed Gate-8
containment evidence with `state = "dispatch_attempted"` and
`consumed_at = authority_current_time`. The record is committed by exactly
one `RuntimeInvocationAuthorityConsumptionStore.create(proof_id, record)`
call. No independent "mark proof consumed" then "mark approval consumed"
writes exist. The RIHAC repository approval store is never mutated
(HPAC-REQ-102). Read-back verification (`resolve(proof_id).record_digest ==
record.record_digest`) follows every successful create
(`gate9_read_back_verification_failed` otherwise).

---

## 18. Canonical-store containment + durable-record provenance (§40-§42 of the prompt)

The consumption store cannot escape its canonical root: `proof_id` passes
through `require_safe_relative_id_component` (rejects absolute paths, `..`,
traversal); `reject_symlink` guards the root and the record path. A
schema-shaped file placed by hand at a *different* `proof_id` root does not
make this invocation's proof consumed — the store resolves strictly by the
bound `proof_id` (`test_planted_foreign_record_outside_writer_is_not_authoritative`).
A traversal `proof_id` fails closed before any write
(`test_consumption_store_rejects_traversal_proof_id`). Only the
Gate-9/store-authorized writer creates the canonical transition — a
caller-created record object is not authoritative; the store recomputes and
verifies `record_digest` on both `create` and `resolve`. Earlier confinement
guarantees (`.1R.3`, `HPAC_PROTECTED_ROOT` deployment-scoped `production()`
fail-closed) are intact and unmodified.

---

## 19. NON-REAL ineligibility (§34 of the prompt)

Reconfirmed: no deterministic NON-REAL path produces a legitimate Gate-8
containment success or reaches production Gate 9. `HPACStoreAuthority.writer`
raises unless `authority_class is FIXTURE_NON_REAL`; no `PRODUCTION` writer
exists; both authority-construction points reject non-`PRODUCTION`
assurance. Defense in depth: Gate 9's capability re-read
(`gate9_runtime_execution_available_unexpected`) and its refusal of any
non-`ALLOW` / non-registry upstream fail closed if an ineligible lineage
somehow appeared. No real human authority is fabricated. Tests:
`test_real_predicates_make_production_gate9_unreachable`,
`test_non_real_gate5_never_yields_gate5result_for_gate9`,
`test_runtime_execution_available_inside_boundary_fails_closed`.

---

## 20. V-13-5-2 attempt-id semantics (§35 of the prompt)

`.1R.13.5` records that `Gate5Result` has no direct `attempt_id`; attempt
identity is established at **Gate 2** on `RuntimeDispatchIdentity`
(`attempt_id`, minted by `new_runtime_dispatch_identity`) and carried
unchanged through Gate 7 (RDGO-001 §10a). Gate 9 preserves this exactly: it
confirms `identity.attempt_id == gate6_decision.attempt_id ==
gate7_result.attempt_id == gate8_result.attempt_id` and records
`identity.attempt_id` in `request_identity.attempt_id`. **Gate 9 makes no
direct Gate-5 attempt binding claim** — the binding is transitive through
the identity triple and Gate 7, exactly as frozen. Documented verbatim in
the module docstring.

---

## 21. Contract-alignment debt carried (§36 of the prompt)

Each re-evaluated for whether it becomes blocking once authority is actually
consumed. **None does.**

| Finding | Re-evaluation at consumption | Disposition |
|---|---|---|
| **V-2 / V-3** (RDGO §4/§6 "Gate 5 creates `PROOF_VERIFIED_AND_BOUND`" vs IF-1: verifier step 10 creates it at Gate-3 time, Gate 5 confirms) | Gate 9 **confirms** the sequence-3 event read-only via `resolve_gate5_binding_event` and re-checks its genesis binding + canonical digest; it never creates, mutates, or depends on "which gate created it". Proof-lifecycle **currentness** at consumption is enforced by `revalidate` (re-runs `validate_approval` → proof lifecycle / expiry / already-consumed), not by the disputed wording. **No ambiguity introduced.** | NON-BLOCKING, carried unchanged; contract-clarification phase candidate |
| **V-4** (PBRD §4 fact 14 7-field `human_authority_binding` vs 3-field production shape) | Gate 9 consumes the trusted upstream **objects** (`Gate5Result.projection`, `Gate6Decision`, `Gate7Result`, `Gate8Result`), never the raw 3- or 7-field binding. `.1R.13` §10 verified the digest-collapse lossless. Gate 9 references neither `RuntimeDispatchHumanAuthorityBinding` nor the PBRD fact-14 subfields (`"RuntimeDispatchHumanAuthorityBinding" not in G9_SRC`). **No dependence.** | NON-BLOCKING, carried unchanged |
| **V-13-3-1** (`.1R.13.2`'s "PB-policy drift covered transitively via projection revalidation" overstates `revalidate` — it does not re-read live PB policy) | Gate 9 revalidates the projection (re-runs `validate_approval`, which re-checks `policy_version` drift and tolerates `policy_drift_requires_fresh_pb_re_evaluation` as advisory) and consumes the trusted `Gate6Decision` object; it does **not** re-run PB policy (that is Gate 6's job) and makes no PB-policy re-evaluation claim (`"pb policy" not in G9_SRC.lower()`). Under the always-DENY posture no positive path exists anyway. | NON-BLOCKING, carried unchanged |
| **V-13-3-2** (Gate 7's `matched_no_go_ids` omits some registry-mandatory RE-NOGO ids by frozen design) | Gate 9 trusts `gate7_result.decision == "ALLOW"` + exact-object provenance, never the completeness of `matched_no_go_ids`. | NON-BLOCKING, carried unchanged |
| **V-13-5-1** (frozen `.1R.13.1` §11.2/§25 cwd/env/transport rows are scope/well-formedness checks + digest-binding, not drift comparisons) | **SATISFIED at Gate 9** by containment-evidence read-back + recomputation (§11 of this doc). The residual contract-text inconsistency (unenforced `gate8_transport_drift` row; no bound cwd/env ref on `RuntimeDispatchRequestConstructionInput`) is a documentation cleanup for the contract-clarification phase — not a Gate-9 defect. | Runtime-dispatch consumption path: satisfied. Contract text: still owed |
| **V-13-5-2** (`Gate5Result` has no `attempt_id`; binding transitive via Gate 7) | Preserved exactly (§20 of this doc). | INFO, carried unchanged |

**No finding became semantically blocking. No STOP condition met.** No
contradiction was found between RDGO-001 / RIHAC-001 / RIASC-001 / HPAC-001
/ PBRD-001 / RPAC-001 / POL-005 and the Gate-9 wiring implemented here.

---

## 22. No policy re-evaluation invented (§37 of the prompt)

Gate 9 invents no PB or Runtime Enforcement policy semantics. It revalidates
only what the frozen contracts require at consumption time (HPAC-REQ-099
battery) and re-reads the capability snapshot. It runs no unrelated policy
engine. `"permission broker" not in G9_SRC.lower()` (only prohibition
prose); no `run_gate6_permission_broker` / `run_gate7_runtime_enforcement`
call.

---

## 23. Gate-9 defensive validation matrix (§38 of the prompt)

The 41-case matrix is covered by 63 focused tests in
`tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py`.
Coverage highlights (matrix # → test):

1-4 provenance / affirmative containment → `test_none_gate8_result_fails_closed`,
`test_object_new_gate8_result_rejected`,
`test_copied_reconstructed_serialized_gate8_result_rejected`,
`test_trusted_negative_gate8_result_rejected_before_any_consumption`;
5-8 lineage decisions → `test_untrusted_gate7_result_rejected`,
`test_gate7_decision_not_allow_rejected`,
`test_untrusted_gate6_decision_rejected`,
`test_gate6_decision_not_allow_rejected`,
`test_untrusted_gate5_result_rejected`;
5-7 invocation/attempt/request → `test_invocation_mismatch_rejected`,
`test_attempt_mismatch_rejected`, `test_request_id_mismatch_rejected`;
8 Gate7 lineage → `test_gate7_lineage_digest_mismatch_rejected`;
9-10 effect-plan / containment-evidence recompute →
`test_effect_plan_drift_rejected_by_recomputation`;
11-17 cwd/env/profile/executable/argv/descriptor/target drift →
`test_executable_drift_rejected_by_recomputation`,
`test_cwd_outside_repository_rejected_by_recomputation`;
18-19 principal / credential revocation inside boundary →
`test_stale_projection_rejected_inside_boundary` (transitive via `revalidate`);
20-24 proof/approval expiry / lifecycle / already-consumed →
`test_stale_projection_rejected_inside_boundary`,
`test_proof_approval_pairing_mismatch_rejected`;
25 proof/approval cross-pair → `test_proof_approval_pairing_mismatch_rejected`;
26 first consumption (test path) → `test_first_valid_consumption_succeeds_in_test_path_only`;
27-29 duplicate / same-proof-diff-approval / diff-proof-same-approval →
`test_duplicate_identical_request_reports_already_consumed`,
`test_different_proof_same_consumed_approval_is_rejected`;
30 concurrency one-winner → `test_concurrent_requests_yield_exactly_one_success`;
31-33 crash-before / crash-after / retry →
`test_crash_before_commit_leaves_both_unconsumed`,
`test_crash_after_commit_retry_reports_consumed`;
34 no partial consumption → `test_no_partial_consumption_single_record_covers_proof_and_approval`;
35 durable-record authoritative across restart →
`test_canonical_durable_record_is_authority_across_restart`;
36-37 Gate9Result model / not Gate-10 authority →
`test_gate9_result_non_transferable_and_non_serializable`,
`test_is_gate9_result_is_provenance_not_success`;
38 no Gate-10 call → `test_no_gate10_symbol_or_adapter_call`;
39 runtime unchanged → `test_runtime_state_unchanged_after_gate9_runs`;
40 NON-REAL unreachable → `test_real_predicates_make_production_gate9_unreachable`,
`test_non_real_gate5_never_yields_gate5result_for_gate9`;
41 Gate-5/6/7/8 regressions intact → the ten V-13-1-extended suites all pass
(§13 of this doc; §24 of this doc).

---

## 24. Fixed-SHA regression attribution (§48 of the prompt)

Immutable baseline: `c1ea2c8b` (`.1R.13.5` complete). Candidate: HEAD
`9fba3251`. Method: deterministic (`-p no:randomly`) affected-suite run at
HEAD, then A/B of every non-passing node against a `git worktree` at
`c1ea2c8b`.

**Affected-suite selection** (`-k "gate5 or gate6 or gate7 or gate8 or gate9
or runtime_dispatch or runtime_authority or hpac* or permission_broker or
b1_b7_n1_n2 or consumption or lifecycle or introspection"`): see the
finalization metadata for the exact recorded counts.

**Non-passing nodes at HEAD and their A/B disposition:**

- The initial wide run surfaced 19 non-passing nodes. **17 reproduce
  identically at `c1ea2c8b`** (pre-existing, NOT attributable):
  `test_hpac_trust_root_repair_independent_verification_...::test_blocking_reproduction_inert_gate9_absolute_proof_id_escapes_root`,
  `test_hpac_verifier_independent_verification_...::test_object_dunder_new_bypasses_trusted_construction_seal`
  and `::test_forged_via_object_new_would_report_real_runtime_eligible`,
  `test_phase_148f_...::test_permission_broker_consumer_scope_inventory`,
  `test_phase_148g2_...::test_actual_git_push_dispatch_site_in_core_agent_remains_unwired`,
  `test_phase_149m_...::test_no_permission_broker_request_construction_uses_approval_present_true`,
  `test_phase_149o_12b_...::test_no_permission_broker_module_modified`,
  `test_phase_149o_18c/18d/18e_...::test_no_permission_broker_files_touched` (×3),
  `test_phase_149o_1f_...::test_rae_permission_broker_agent_still_byte_unchanged_since_freeze`,
  `test_phase_149o_3_...::test_rae_permission_broker_and_agent_do_not_reference_wave5`,
  `test_runtime_authority_pb_verification_3w1::test_only_content_bound_projection_registry_is_added_to_authority_module`,
  `test_runtime_human_principal_contract_freeze_blocking_repair_...::test_b7_gate5_consumption_conflicts_with_revalidation`,
  `test_runtime_human_principal_contract_freeze_verification_...::test_gate5_proof_consumption_conflicts_with_required_pre_gate9_revalidation`,
  `test_runtime_human_principal_cross_contract_freeze_repair_...::test_proof_lifecycle_binds_at_gate5_and_consumes_at_gate9`,
  `test_runtime_human_principal_cross_contract_freeze_repair_independent_verification_...::test_gate5_gate9_lifecycle_wording_closes_original_b7_contradiction`.
  These are the documented pre-existing HPAC/runtime-selection
  contradiction-documentation and point-in-time PB-freeze guard failures
  (`.1R.8` §26; `.1R.13.5` V-13-5-3 class).
- **2 were attributable to this phase and are FIXED in-phase:**
  - `test_gate8_..._1r13_5::test_gate7_result_consumer_grep_is_exactly_gate7_and_gate8_today`
    — a point-in-time consumer-inventory equality guard tripped by
    `runtime_dispatch_gate9.py` legitimately referencing `is_gate7_result`
    per the `.1R.13.1` §16 handoff. **Converted** to a phase-aware subset
    invariant (`hits <= {gate7, gate8, gate9}`) — V-13-1 (§13 of this doc).
  - `test_gate9_...::test_concurrent_requests_yield_exactly_one_success` —
    a genuine intermittent flake in this phase's *own* new concurrency
    test: a transient contention error racing another creator for the same
    fresh proof directory was surfaced as a fail-closed for the loser
    rather than `already_consumed`. **Fixed** by hardening the coordinator's
    non-duplicate `create`-error path to re-resolve and report
    `already_consumed` when a complete valid record is durably present
    (`9fba3251`); the test now passes deterministically over repeated runs
    and still enforces "exactly one success, one canonical record".

```text
CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0
UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS       = 0
```

**Concurrency failures were investigated with particular care** (prompt §48)
— the one concurrency non-pass was this phase's own test, root-caused to a
proof-directory-creation race, fixed at the coordinator, and re-verified
stable.

---

## 25. Atomicity verification instrumentation (§49 of the prompt)

The `.1R.14` suite instruments the store/coordinator sufficiently to prove:
lock acquisition = the atomic create-only primitive (no separate lock);
revalidation ordering (early pre-check vs in-boundary battery, both
exercised); exactly-one create under 4-thread contention with exactly one
`consumption.json`; no pre-lock durable mutation (`create` spy shows zero
calls on every fail-closed path before the boundary —
`test_trusted_negative_gate8_result_rejected_before_any_consumption`,
`test_internal_error_fails_closed_with_no_partial_output`); no post-lock
partial write (read-back verification; `...DurabilityUncertainError`
handling). Final-file-content assertions are backed by ordering assertions
(spy call counts, `_count_consumption_json` before/after), not relied on
alone.

---

## 26. Runtime zero-effect proof (§32-§33, §50 of the prompt)

- `test_module_imports_nothing_effectful` — AST scan: no `subprocess`,
  `socket`, `pty`, `os.system`, `requests`, `httpx`, `urllib`, `asyncio`,
  `multiprocessing`, `ctypes`, `fcntl`, `ssl`, `selectors`,
  `runtime_adapter`, `mock_runtime_adapter`, `fido2`, `webauthn`, `ctap`;
  no `Popen(` / `os.system(` / `.dispatch(` in source.
- `test_no_gate10_symbol_or_adapter_call` — no `dispatch` / `Popen` /
  `spawn` / `execv` / `system` call attribute; no `run_gate10` / `Gate10` /
  `adapter_dispatch` / `DispatchReceipt` symbol.
- `test_gate9_writes_only_the_canonical_local_consumption_store` — after a
  successful consumption, `consumption.json` count under the repo tree is
  unchanged; exactly one under the test-scoped store root.
- `test_runtime_state_unchanged_after_gate9_runs` —
  `CURRENT_RUNTIME_STATE == "Observed"`,
  `CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"`,
  `EXECUTION_AVAILABILITY == "unavailable"`.

```text
Gate-9 persistence calls  = the expected canonical local consumption store only
runtime subprocess        = 0
adapter invocation        = 0
provider / network        = 0
credential operations     = 0
hardware operations       = 0
Gate-10 effects           = 0
```

Local canonical consumption-store writes are the **expected Gate-9
authority-consumption effect** and are categorically distinct from external
runtime effects. Gate 9 ends after durable consumption / result
normalization — no continue-to-Gate-10.

---

## 27. Consumer inventory (§43 of the prompt)

`git grep` over `src/pcae` at HEAD:

| Symbol | Consumers | Expected |
|---|---|---|
| `Gate8Result` / `is_gate8_result` | `runtime_dispatch_gate8.py` (defines), `runtime_dispatch_gate9.py` (only authorized downstream consumer, `.1R.13.1` §16) | ✅ |
| `run_gate8_process_containment` | `runtime_dispatch_gate8.py` (defines), `runtime_dispatch_gate9.py` (re-run for containment-evidence recomputation) | ✅ |
| `_GATE8_RESULTS` | `runtime_dispatch_gate8.py` only (Gate 8 remains sole owner) | ✅ |
| `run_gate9_atomic_authority_consumption` / `_GATE9_RESULTS` | `runtime_dispatch_gate9.py` only | ✅ |
| `Gate9Result` / `is_gate9_result` | `runtime_dispatch_gate9.py` only — **zero downstream production consumers** (Gate 10 does not exist) | ✅ |
| `Gate7Result` / `is_gate7_result` | `runtime_dispatch_gate7.py`, `runtime_dispatch_gate8.py`, `runtime_dispatch_gate9.py` (authorized) | ✅ |
| `Gate6Decision` / `is_gate6_decision` | `runtime_dispatch_permission.py`, `runtime_dispatch_gate7.py`, `runtime_dispatch_gate9.py` (authorized) | ✅ |
| `runtime_invocation_authority_consumption` (inert Gate-9 store) | `runtime_dispatch_gate9.py` only — the single authorized production importer | ✅ |

Gate 9 is the only newly authorized production consumer of `Gate8Result`.
`Gate9Result` has zero downstream production consumers.

---

## 28. V-13-1 invariant guard extensions (§47 of the prompt)

The authorized single-file `runtime_dispatch_gate9.py` addition
deterministically trips point-in-time production-scope / consumer-inventory
guards frozen by earlier phases. Each was **converted to a phase-aware
subset invariant** (never re-baselined to a permanently-stale frozen-diff
snapshot; the subset orientation still fails an unauthorized expansion), and
every conversion is disclosed here with A/B attribution (§24):

| Suite | Guard(s) converted | New form |
|---|---|---|
| `.1R.8` | `test_isolation_only_three_production_files_changed_since_baseline`, `test_isolation_no_gate_coordinator_or_gate9_consumption_wiring` | `_authorized` set += `gate9.py`; `gate9_callers <= {gate9.py}` (was `== set()`) |
| `.117` | `test_production_file_allowlist_matches_frozen_phase_matrix`, `test_consumer_inventory_is_bounded_and_gate9_stays_unwired` | `_authorized_surface` += `gate9.py`; `projection_consumers <= {…, gate9.py}`; `gate9_consumers <= {gate9.py}` (was `== set()`) |
| `.1R.10` | `test_only_expected_production_files_changed_since_baseline` | `_AUTHORIZED_RUNTIME_DISPATCH_CHAIN_SURFACE` += `gate9.py` |
| `.1R.11` | `test_production_scope_is_exactly_the_three_planned_files`, `test_no_gate9_consumption_store_wiring_anywhere_new` | `_AUTHORIZED_GATE_CHAIN_SURFACE` += `gate9.py`; store-importer assert → `<= {gate9.py}` (was `== []`) |
| `.1R.12` | `test_only_expected_production_file_changed_since_baseline` | authorized `<=` set += `gate9.py` |
| `.1R.13` | `test_no_downstream_production_consumer_of_gate6_symbols`, `test_1r12_production_diff_is_exactly_one_file`, `test_known_pre_existing_point_in_time_scope_guard_failures_are_attributable` | allowed Gate-6-symbol consumers `<=` += `gate9.py`; `_AUTHORIZED_POST_1R12_CHAIN_SURFACE` += `gate9.py` |
| `.1R.13.2` | `test_gate7_is_sole_production_consumer_of_is_gate6_decision`, `test_production_scope_since_baseline_is_the_single_new_gate7_file` | `== {…}` → `<= {…, gate9.py}` |
| `.1R.13.3` | `test_no_downstream_production_consumer_of_gate7_result`, `test_gate7_is_the_only_new_gate6_decision_consumer`, `test_runtime_introspection_constants_unchanged_since_baseline`, `test_converted_guards_keep_hpac_exact_and_gate9_bounded_asserts` | `<=` sets += `gate9.py`; the meta-guard's expected form updated to the phase-aware subset assert |
| `.1R.13.4` | `test_gate8_is_sole_production_owner_of_containment_boundary`, `test_gate8_is_the_only_new_gate7_result_consumer`, `test_gate8result_has_zero_downstream_production_consumers`, `test_production_scope_since_baseline_is_the_single_new_gate8_file` | owner guard split into `_GATE8_RESULTS` (still `==`) + `run_gate8_process_containment` caller (`<= {gate8, gate9}`); other `==` → `<=` += `gate9.py` |
| `.1R.13.5` | `test_sole_production_owner_of_gate8_boundary`, `test_no_gate9_consumer_of_gate8result_exists_yet`, `test_gate7_result_consumer_grep_is_exactly_gate7_and_gate8_today`, `test_production_diff_since_baseline_is_exactly_one_new_file`, `test_gate9_and_hpac_asserts_stay_exact_after_extension` | `==` → `<= {…, gate9.py}` (owner guard split as in `.1R.13.4`); meta-guard updated for the bounded (not exact-empty) Gate-9 asserts; hpac_verifier consumer asserts remain **exact and unweakened** |

The `gate10` / Gate-10-consumer exact-empty asserts are **preserved
verbatim** — Gate 10 has zero consumers, and every converted guard still
rejects a synthetic unauthorized extra production file (the `.1R.13.5`
`test_synthetic_unauthorized_third_production_file_would_fail_the_subset_guards`
and `.1R.13.3`
`test_synthetic_unauthorized_file_would_fail_the_subset_invariant` remain
green). The `hpac_verifier` consumer-inventory asserts remain exact
equality — not weakened.

---

## 29. Earlier-gate regressions (§46 of the prompt)

Reconfirmed by the full V-13-1-extended suites (all pass at HEAD):

- **Gate 5** — CLOSED / non-consuming / NON-REAL hard stop
  (`test_non_real_gate5_never_yields_gate5result_for_gate9`; `.1R.10` /
  `.1R.11` suites green).
- **Gate 6** — CLOSED / permission only / POL-005 preserved (`.1R.12` /
  `.1R.13` suites green; POL-005 byte-unchanged).
- **Gate 7** — CLOSED / current posture DENY / no consumption (`.1R.13.2` /
  `.1R.13.3` suites green; `runtime_dispatch_gate7.py` byte-unchanged).
- **Gate 8** — CLOSED / containment validation only / no effect / no
  consumption (`.1R.13.4` / `.1R.13.5` suites green;
  `runtime_dispatch_gate8.py` byte-unchanged; the Gate-8 re-run inside Gate
  9 consumes nothing and writes nothing).

Gate 9 weakens no earlier boundary.

---

## 30. Implementation disposition

```text
GATE-9 ATOMIC AUTHORITY CONSUMPTION COORDINATOR:
    IMPLEMENTED
    — INDEPENDENT VERIFICATION PENDING
    — NOT CLOSED
```

Gate 9 is **not** verified. No execution readiness is claimed. Runtime
remains `not_implemented / Observed / observe / unavailable`.

New findings this phase: **none blocking.** V-13-5-1 is now satisfied at
Gate 9 for the runtime-dispatch consumption path (the frozen contract-text
inconsistency remains a documentation cleanup, not a defect). The
concurrency-loser disposition was hardened in-phase. All V-13-1 guard
conversions are disclosed with A/B attribution (§24, §28).

---

## 31. Historical `.3` governance incident

```text
DELEGATED `.3` FINALIZATION / COMMIT / PUSH:  UNAUTHORIZED
```

Preserved unchanged. No delegated worker committed, finalized, or pushed in
this phase; no raw `git commit` / `git push`, `--no-verify`, force push,
history rewrite, or hook bypass was used — the governed `pcae` lifecycle
only. Only the primary human-authorized operator holds `.1R.14` lifecycle
authority.

---

## 32. Recommended next phase

```text
149O.20L.7O.3W.1R.2B.1R.1.1R.15 — Independent Verification of Gate-9 Atomic
Authority Consumption Coordinator Integration
```

**Not begun.** Requires its own separate explicit human authorization.
Scope: independently re-derive §4's core contract, §9-§13's handoff and
in-boundary revalidation, §16's crash/replay/concurrency disposition,
§11's V-13-5-1 read-back, and §24's fixed-SHA attribution against the
`.1R.14` implementation — not trusted from this report or this phase's own
tests. Discipline per `.1R.13.3` / `.1R.13.5`.

Gate 10 remains **unplanned** — no ID is assigned. Gate-10 planning waits
until `.1R.15` verifies Gate 9 and the accumulated contract-alignment debt
(V-2/V-3/V-4/V-13-3-1/V-13-3-2/V-13-5-1 contract text) is reviewed in a
dedicated contract-clarification phase.

---

## 33. Final report

- **Phase ID / title:** `149O.20L.7O.3W.1R.2B.1R.1.1R.14` — Gate-9 Atomic
  Authority Consumption Coordinator Integration Implementation.
- **Phase-entry SHA:** `c1ea2c8b`.
- **Prerequisite verification state:** all eight `.1R.13.1` §17 criteria
  SATISFIED (Gate 5/6/7/8 CLOSED + verified; §16 handoff frozen +
  independently re-reviewed by `.1R.13.5`; no blocking findings; runtime
  non-executing); test-path-first scope explicitly human-authorized.
- **Contracts / source inspected:** §3.
- **Production files changed:** exactly `src/pcae/core/runtime_dispatch_gate9.py`
  (new).
- **Sole Gate-9 owner:** `run_gate9_atomic_authority_consumption`.
- **Serialization / lock owner:** the Gate-9 coordinator; scope
  `<root>/proofs/v2/<proof_id>/`; mechanism = the store's create-only
  atomic primitive (no second transaction mechanism).
- **Gate8Result provenance:** `is_gate8_result` (exact-object registry).
- **Affirmative-containment requirement:** `containment_established is True`
  — a trusted negative result is a hard stop before any consumption.
- **Invocation / attempt / request binding:** equal across g5/g6/g7/g8 +
  identity (§10).
- **Gate7 lineage binding:** `gate8_result.gate7_result_digest ==
  _gate7_result_digest(gate7_result)`.
- **Effect-plan recomputation / containment-evidence recomputation:** via a
  fresh `run_gate8_process_containment` over re-resolved inputs; every
  digest compared (§11).
- **V-13-5-1 cwd/env/profile read-back:** SATISFIED at Gate 9 (§11, §21).
- **Principal / credential / proof / approval in-boundary revalidation:**
  via `revalidate_validated_authority_projection` (re-runs
  `validate_approval`), inside the boundary, before compare-and-create
  (§12-§13).
- **Proof / approval pairing:** exact same-lineage pair required (§13).
- **Already-consumed behaviour:** deterministic `already_consumed` status;
  never a second success; never continue-to-effect (§16).
- **Atomic single-record model:** one create-only
  `HPAC-AUTHORITY-CONSUMPTION/2.0` record; proof + approval consumed
  together; no mutable `consumed` field; RIHAC store never mutated (§17).
- **Concurrency result:** exactly one winner over 4-thread contention;
  exactly one canonical record; no split-brain (§16, §24).
- **Crash-before-commit result:** unconsumed; no Gate-10 effect (§16).
- **Crash-after-commit result:** consumed; detected as `already_consumed`;
  no second write (§16).
- **Restart / retry behaviour:** canonical durable record is the authority;
  a fresh store resolves it → `already_consumed` (§16).
- **Durable-record provenance / canonical-store containment:** traversal /
  symlink / planted-foreign-record all fail closed; only the store-
  authorized writer creates the transition (§18).
- **Gate9Result model / provenance:** identity-only, non-serializable,
  sealed, registry-provenanced; `is_gate9_result` is provenance ≠ success;
  frozen forward invariant for Gate 10 (§15).
- **No-Gate-10 evidence:** §26.
- **NON-REAL isolation:** §8, §19.
- **V-2 / V-3 / V-4 / V-13-3-1 / V-13-3-2 / V-13-5-1 / V-13-5-2
  dispositions:** §21 — none blocking; V-13-5-1 satisfied at Gate 9.
- **Gate-5/6/7/8 regressions:** intact (§29).
- **V-13-1 invariant extension:** ten suites converted to phase-aware
  subset invariants, disclosed with A/B (§28).
- **Fresh focused tests:** 63, in
  `tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py`.
- **Fixed-SHA A/B:** baseline `c1ea2c8b` vs HEAD; CANDIDATE-ONLY UNEXPLAINED
  FUNCTIONAL NONPASSING = 0; UNEXPLAINED ATTRIBUTABLE REGRESSIONS = 0; 17
  pre-existing failures reproduce at baseline; 2 attributable
  guard/test-only issues fixed in-phase (§24).
- **Candidate-only functional regression count:** 0.
- **Consumer inventory:** §27.
- **Contract identity:** §14 — all nine contracts + POL-005 + Shell Gate +
  Gate 5/6/7/8 + the inert consumption store byte-unchanged.
- **Runtime / no-effect evidence:** §26.
- **All new findings:** none blocking (§30).
- **Implementation verdict:** GATE-9 — IMPLEMENTED, INDEPENDENT
  VERIFICATION PENDING, NOT CLOSED.
- **Commits:** `9103d9cf`, `9fba3251` (implementation) + the governed
  finalization commits.
- **Pushed status / `origin/main..HEAD`:** recorded by the governed
  finalization sequence (`origin/main..HEAD = 0` after the governed push).
- **Exact `.1R.15` recommendation:** §32.

---

## 34. Stop condition

This phase completes only `149O.20L.7O.3W.1R.2B.1R.1.1R.14`. `.1R.15` is
not begun. Gate 10 is not implemented and not assigned an ID. No execution
is enabled. No real FIDO2 / protected UI is implemented. The canonical
implementation report above is returned for human review.
