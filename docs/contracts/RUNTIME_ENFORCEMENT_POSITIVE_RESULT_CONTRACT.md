# REPRC-001 v1.0 — Runtime Enforcement Positive Result Contract

## Contract identity and status

**Contract:** REPRC-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26 — N-16-4 Real Positive
Single-Attempt Runtime Enforcement Gate Implementation.
**Independent verification:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.27.
**Trust-boundary freeze this contract implements:** Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.25 — N-16-4 Positive Runtime Enforcement
Contract and Trust-Boundary Freeze (B-1 = Model B1-B, B-2 = Model B2-D,
B-3 = Currentness B).
**Scope:** the schema, non-bearer trust model, logical identity,
currentness/lifetime, replay/stale semantics, positive-rationale
vocabulary, duplicate/restart behaviour, and the finite downstream-consumer
set of a **positive** Gate-7 Runtime Enforcement result
(`Gate7Result` with `decision == "ALLOW"`) for `runtime_dispatch`.
**Production surface:** `src/pcae/core/runtime_dispatch_gate7.py` only.
**Related contracts:** RDGO-001 v3.1 (§8 Gate 7 — the state-machine text
this contract's positive result already sits within; §10 item 7 — the
durable Gate-7 verdict reference; §0 walls), PBNDE-001 v1.0 (§7
downstream-gate independence), PBRD-001 v3.0 (§14 the Gate-6 → Gate-7
projection), HPAC-001 v2.1 / `HPAC-AUTHORITY-CONSUMPTION/2.1`
(`runtime_invocation_authority_consumption.py` — item 7
`runtime_enforcement_binding`, unchanged), RIASC-001 v3.0 / RIHAC-001 v2.0
(the `ValidatedAuthorityProjection` currentness anchor), RPAC-001 v1.0
(RPAC-REQ-029 `DispatchEnvelope` — a Gate-10 artifact this contract
references, never modifies), the RE No-Go Registry (schema 1.1, unchanged),
`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (NG-025 annotation,
unchanged).

REPRC-001 freezes result semantics only. It does not launch a process,
invoke an external runtime, register an adapter, access credentials, enable
network/execution, consume human authority, or move any runtime capability.
A positive Gate-7 result is **unreachable in production** — the N-16-5
real-human-authority wall, the N-16-6 supply-chain-admission wall, and the
current Runtime Enforcement no-go posture each independently block it. The
positive branch is exercised only through a clearly-labelled, in-memory,
documented test-only substitution of the runtime-enforcement posture
resolver (§17).

REPRC-001 is a **companion** contract (the PBNDE-001 / PBRD-001 shape). It
introduces no RDGO-001 state-machine change, no gate reorder, no
first-effect-boundary move, no merge of the authority / permission /
enforcement / containment concerns, no freshness weakening, and no effect
scope widening. RDGO-001 stays v3.1; HPAC-001 stays v2.1;
`HPAC-AUTHORITY-CONSUMPTION` stays `/2.1`; PBRD-001, PBNDE-001, PBPA-001,
RPAC-001, RIHAC-001, RIASC-001, and the RE No-Go Registry are byte-unchanged
by the N-16-4 track. The only version movement in the entire N-16-4 track
is REPRC-001 v1.0 (initial freeze).

## 0. Normative language

`SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`, `MAY` are normative. Unknown,
missing, conflicting, malformed, or unverifiable facts fail closed: no
`Gate7Result` is created and Runtime Enforcement returns `(None, reasons)`,
or — where an evaluation completed — `Gate7Result(decision="DENY")`. A
positive result is produced only by the affirmative satisfaction of every
predicate in §2; the absence of a denial is never a positive result.

## 1. `reprc_schema_version`

Every `Gate7Result` (positive or negative) SHALL carry a
`reprc_schema_version` field whose value under this contract is exactly the
literal string:

```
REPRC-001/1.0
```

`reprc_schema_version` is a closed-field-set marker. A consumer that does
not recognise the schema version SHALL treat the result as untrusted. A
future REPRC-001 MINOR or MAJOR SHALL change this literal, which by §3
changes every `runtime_enforcement_result_id` and so invalidates every
result minted under a prior schema version. `reprc_schema_version` mirrors
`DISPATCH_ENVELOPE_SCHEMA_VERSION` (RPAC-REQ-029) as an additive schema
anchor; it is not itself an authority input.

## 2. Meaning of a positive Gate-7 result

A `Gate7Result` with `decision == "ALLOW"` and `is_gate7_result(result) ==
True` asserts one thing and only one thing:

> the exact bound `runtime_dispatch` invocation/attempt satisfied Runtime
> Enforcement's independent fail-closed conjunction — structural validity of
> the fourteen binding facts, a consumed Gate-6 `Gate6Decision` with
> `decision == "ALLOW"`, a re-trusted and re-validating Gate-5
> `ValidatedAuthorityProjection`, a recomputed subject/scope binding, a
> target within `bounded_local_process_dispatch` /
> `RUNTIME_DISPATCH_LOCAL_CLI_V1` scope with `network_requirement is False`,
> an available runtime posture, and an empty per-decision Runtime
> Enforcement no-go set — as of `evaluated_at`, and MAY therefore proceed
> to Gate 8.

### 2.1 A positive Gate-7 result is explicitly NOT

- permission to execute, dispatch, spawn a process, or cause any external
  effect;
- runtime capability, adapter availability, or an enabled backend;
- effect authorization or a licence to call `adapter.dispatch()`;
- human authority — created, consumed, refreshed, or attested;
- a Permission Broker permission or a re-run of PB policy;
- adapter supply-chain admission (an N-16-6 concern; §13);
- a `DispatchEnvelope` (RPAC-REQ-029) or any Gate-10 pre-effect artifact;
- Gate-8 containment success, Gate-9 durable-record success, or Gate-9
  atomic authority consumption;
- a substitute for, or a waiver of, Gates 8, 9, or the Gate-10 pre-effect
  read-back;
- a bearer token, a cache, a reusable grant, or a durable record of any
  kind.

The durable record of the Runtime Enforcement verdict is Gate 9's
`consumption.json` `runtime_enforcement_binding` (§10). **Audit evidence is
not authority.** Every consumer that runs after Gate 9 SHALL re-read that
durable reference and re-verify it against a fresh authority-generation
re-derivation rather than trust a `Gate7Result` handle.

### 2.2 Decision vocabulary

Gate 7 is a binary whether-to-invoke gate: `decision` is `"ALLOW"` or
`"DENY"` (`GATE7_DECISION_VALUES`), by exact string equality. There is no
`HUMAN_REVIEW` at Gate 7 — `HUMAN_REVIEW` is a Gate-6 concept and is a hard
stop **before** Gate-7 evaluation. The positive result reuses
`decision == "ALLOW"` (Option A of `.1R.24` §11) because the entire
downstream chain already tests `gate7_result.decision == "ALLOW"` by exact
equality and RDGO-001 §8 already says "Runtime Enforcement ALLOW". The
non-authority semantics are carried by the §4 provenance wall, the §5
non-serializability, the §2.1 negative list, and the fact that every
downstream gate independently re-validates — not by the string.

## 3. `runtime_enforcement_result_id` — logical identity

Every `Gate7Result` SHALL carry a `runtime_enforcement_result_id`: a
canonical digest, computed with the repository-standard NFC-normalized
sorted-key-JSON SHA-256 canonicalization
(`runtime_authority.compute_canonical_digest`), over exactly the following
ordered ingredients:

| key | value |
|---|---|
| `invocation_id` | `identity.invocation_id` |
| `attempt_id` | `identity.attempt_id` |
| `idempotency_key` | `identity.idempotency_key` (Gate-2 canonical content digest) |
| `pb_decision_digest` | `_pb_decision_digest(gate6_decision)` — the canonical Gate-6 decision binding |
| `evaluated_input_digest` | the frozen RDGO §8 projection digest (§8) |
| `authority_freshness_digest` | `projection.freshness_verdict_digest or projection.evidence_digest()` |
| `runtime_posture_digest` | `RuntimeEnforcementPosture.digest()` |
| `reprc_schema_version` | the literal `"REPRC-001/1.0"` |

`runtime_enforcement_result_id` is a digest over lower-level canonical
digests, never over itself: there is no circular identity. It does not
include `decision`, `expires_at`, or `evaluated_at`. It does not include a
separate `currentness_binding` (there is none — §8) and does not include
adapter-admission evidence (there is none at Gate 7 — §13); the digests it
does commit already transitively bind `runtime_target_id`, the adapter
descriptor/config digests, the subject/scope binding, the request
construction facts, and the per-decision no-go set.

### 3.1 Identity challenges (REPRC-INV-001)

Changing any of the following SHALL change or invalidate
`runtime_enforcement_result_id`, and a downstream consumer that observes a
mismatch against a freshly recomputed value SHALL reject:

`invocation_id`, `attempt_id`, `idempotency_key`, the PB decision digest,
the evaluated-input digest (including any of its components — runtime
target, adapter descriptor/config digests, filesystem/repository scope,
requested capability, task binding), the authority-freshness digest, the
runtime-posture digest (including the per-decision no-go set), and
`reprc_schema_version`.

No identity collision is permitted through an omitted security-critical
field. `runtime_enforcement_result_id` is a **logical identity for audit
and replay-challenge assertions**, never a bearer credential: knowing or
reconstructing it grants nothing (§4).

## 4. Non-bearer trust model

The following are each insufficient, alone or in combination, to make a
`Gate7Result` trusted:

```
structure            != trust
field equality       != trust
digest consistency   != trust
serialized form      != trust
a known runtime_enforcement_result_id != trust
```

A **trusted** `Gate7Result` requires **all** of:

1. construction by `run_gate7_runtime_enforcement` under the process-local
   `_GATE7_RESULT_CONSTRUCTOR_SEAL` — direct construction raises `TypeError`;
2. membership in the process-local identity registry `_GATE7_RESULTS`
   (`Gate7Result.__eq__` / `__hash__` are identity-only; the only insertion
   point is `run_gate7_runtime_enforcement`'s completed-evaluation return
   path);
3. every bound field populated and immutable (§6);
4. successful downstream re-validation of currentness (§8) and lineage
   (§9, §10, §11).

`is_gate7_result(candidate)` SHALL return `True` only for the literal object
a prior `run_gate7_runtime_enforcement` call returned on a completed
evaluation — never on the basis of `isinstance`, fields, equality, or any
shape property. It SHALL fail closed for a forgery, a copy, a
`deepcopy`, a field-reconstruction, an `object.__new__` instance, or a
handle from a previous process.

**No new trust registry.** The non-bearer property is carried entirely by
the existing `_GATE7_RESULTS` identity registry and the constructor seal.
This contract adds none.

## 5. Serialization and reconstruction

`Gate7Result` SHALL remain non-transferable:

- `Gate7Result.__reduce__` SHALL raise `TypeError`; `pickle.dumps` fails.
- `copy.copy` / `copy.deepcopy` of a `Gate7Result` SHALL NOT yield a
  registry member (they raise via `__reduce__`, or produce a non-member).
- `object.__new__(Gate7Result)` SHALL NOT be a registry member.
- Manual field reconstruction SHALL NOT be a registry member.
- A dict / dataclass / document projection of a `Gate7Result`, if ever
  produced for observability (§16), is inert: it grants nothing and
  `is_gate7_result` rejects it.
- `Gate7Result.__init_subclass__` SHALL raise `TypeError`.

There is no durable `Gate7Result` store (§15).

## 6. Immutability

`Gate7Result` SHALL be immutable after construction. It has `__slots__` (no
`__dict__`); every field is bound exactly once inside the sealed
constructor. A `__setattr__` guard mirroring `DispatchEnvelope`'s
("`Gate7Result is immutable`") SHALL reject any post-construction attribute
set once `_seal` is bound. Reflective bypass via `object.__setattr__` on a
`__slots__` class remains possible only for code executing arbitrary
Python in-process — the F7 boundary (same-account autonomous-agent
assumption) is carried verbatim and is not broadened; such a mutated object
is still not a `_GATE7_RESULTS` member and `is_gate7_result` rejects it.

## 7. `evaluated_at`, `authority_current_time`, and `expires_at` (TTL)

- `authority_current_time` is a bounded ISO-8601 string supplied by the
  trusted invocation coordinator. It is **not a trust input** — a caller
  cannot lengthen a result's usable life by passing a future time; the §8
  currentness owners dominate.
- `evaluated_at` SHALL equal the `authority_current_time` passed to the
  evaluation.
- For the **positive (`ALLOW`) branch**, `expires_at` SHALL equal
  `evaluated_at + REPRC_MAX_RESULT_TTL`, where `REPRC_MAX_RESULT_TTL` is a
  REPRC-001 contract constant **frozen at 300 seconds**, computed by
  ISO-8601 string/time arithmetic on the single `authority_current_time`
  string the whole sequence threads (no second clock read, no monotonic
  clock, no `time.time()`, no PID, no nonce — restart-reconstructible from
  the two strings). If `authority_current_time` cannot be parsed as an
  ISO-8601 instant the evaluation fails closed
  (`gate7_internal_error_fail_closed`); no positive result with an
  unbounded or malformed `expires_at` is produced.
- For the **negative (`DENY`) branch**, `expires_at` MAY equal
  `evaluated_at` (a negative result is never consumed forward), preserving
  the byte-current behaviour.
- **TTL is a bounded wall-clock backstop only, NOT the currentness
  mechanism.** Its sole purposes are (a) so a stalled governed sequence
  cannot carry a positive result forward indefinitely, and (b) so a fresh
  positive result is not immediately `gate10_re_decision_expired` at Gate 10
  step 11 (which requires `re_expires_at` strictly after its own
  `authority_current_time`).
- **Stale generation overrides TTL.** Even within the 300-second window, a
  generation drift detected at Gate 8's mandatory Gate-7 re-run or at
  Gate 10 step 13's mandatory generation re-derivation SHALL reject the
  result. TTL never rescues a generationally-stale result.
- The projection's own wall-clock expiry is **not** folded into
  `expires_at`: `ValidatedAuthorityProjection.expiry_verdict` is a verdict
  string, not a timestamp. Projection expiry is enforced by
  `revalidate_validated_authority_projection` (which re-runs
  `validate_approval` against the current time) at Gate 7 creation, at
  Gate 8, at Gate 9, and at Gate 10 — not by `expires_at`.

## 8. Currentness — Currentness B

`run_gate7_runtime_enforcement`'s signature is **unchanged**. There is **no**
`authority_generation_resolver` parameter, **no** `principal_registry` /
`approval_store` / `lifecycle_store` handle at Gate 7, and **no**
`currentness_binding` slot on `Gate7Result`.

Gate-7 currentness is anchored by the currentness **already carried by the
trusted upstream evidence** plus the revalidation Gate 7 already performs:

1. **Bound** at creation by the existing `authority_freshness_digest`
   (`projection.freshness_verdict_digest or projection.evidence_digest()`),
   which is a component of `evaluated_input_digest` and thence of
   `runtime_enforcement_result_id`.
2. **Re-validated at Gate 7 creation** by
   `is_trusted_validated_authority_projection(projection)` +
   `revalidate_validated_authority_projection(projection,
   current_time=authority_current_time)`, which re-runs `validate_approval`
   — catching principal / credential / proof / approval / expiry /
   consumption drift → `gate7_stale_validated_authority_projection`, **no
   `Gate7Result`**.
3. **Re-checked in-process** by Gate 8, which re-runs
   `run_gate7_runtime_enforcement` over freshly re-resolved `Gate6Decision`
   / `Gate5Result` objects (RDGO-001 §8 mandate). A projection stale at
   Gate 8 fails the re-run.
4. **Re-derived restart-safe** by Gate 10 step 13, which calls its trusted
   `authority_generation_resolver()` and compares the live generation vector
   against the durable item-9 `authority_generation_binding` snapshot
   (`_first_generation_drift` → `gate10_authority_generation_drift:<source>`).

TTL (§7) is the wall-clock defence-in-depth backstop over the top of these.

### 8.1 Mandatory stale-rejection owners (REPRC-INV-002)

| # | Owner | Check | Classification |
|---|---|---|---|
| 1 | Gate 7, creation time | `is_trusted_validated_authority_projection` + `revalidate_validated_authority_projection` (re-runs `validate_approval`); failure → `(None, ("gate7_stale_validated_authority_projection",))` | MANDATORY |
| 2 | Gate 8, consumer | re-runs `run_gate7_runtime_enforcement` over freshly re-resolved objects; a stale projection fails the re-run; a trusted **negative** `Gate7Result` is a hard stop at `gate8_gate7_decision_not_allow` before Shell Gate evaluation | MANDATORY |
| 3 | Gate 10 step 13 | `authority_generation_resolver()` → `_first_generation_drift(durable_snapshot, current_markers)` vs. item-9 `authority_generation_binding`; drift → `gate10_authority_generation_drift:<source>` (restart-safe) | MANDATORY |
| 4 | Gate 10 step 11 | durable `re_binding.verdict == "ALLOW"` and `re_expires_at` strictly after `authority_current_time` (else `gate10_re_decision_expired`) | DEFENCE-IN-DEPTH (bounded wall-clock backstop; §7) |

Gate 9 additionally re-derives the Gate-7 lineage and captures its own S1/S2
authority-generation snapshot; it records item 7 as a **reference**, not a
re-run (§10). Gate 10 step 12's runtime-capability re-read is independent of
Gate 7 (§11/§14).

A future independent verification SHALL be able to locate each of owners
1–4 by its exact function/step name from source.

### 8.2 Non-bearer proof under Currentness B (REPRC-INV-003)

- **Stale generation.** A positive `Gate7Result(ALLOW)` for `(inv=A,
  att=1)` whose principal / credential / approval / proof / lifecycle
  generation changes before use cannot traverse the next legitimate
  consumer chain: Gate 8's Gate-7 re-run re-runs `validate_approval`
  against current state and returns `gate7_stale_validated_authority_
  projection`; on a restart / cross-process path Gate 10 step 13 re-derives
  the generation vector from durable stores and rejects at
  `gate10_authority_generation_drift:<source>`. Gate 9 records no
  consumption for a Gate-8 rejection.
- **Copied / reconstructed / serialized result; known id.** `copy.copy` /
  `copy.deepcopy` → not a `_GATE7_RESULTS` member; `object.__new__` → not a
  member; direct construction → `TypeError`; `pickle.dumps` → `TypeError`;
  a dict/dataclass reconstruction → not a member; a known
  `runtime_enforcement_result_id` alone → grants nothing (`is_gate7_result`
  requires registry membership, populated only by
  `run_gate7_runtime_enforcement`). Every such object fails
  `is_gate7_result` at Gate 8 / Gate 9 / Gate 10
  (`gate8_untrusted_gate7_result` / `gate9_untrusted_gate7_result` /
  `gate10_untrusted_gate7_result`).

## 9. Gate 8 relationship

```
Gate-7 ALLOW  ->  ONLY permits Gate 8 evaluation
```

Gate 8 remains independently authoritative over its own
containment/effect constraints — executable resolution, cwd/argv/env
allowlist, child-process prohibition, resource limits, network-denied and
no-credentials confirmation, the three-layer containment model. A positive
Gate-7 result grants no containment. A trusted **negative** `Gate7Result`
is a hard stop at `gate8_gate7_decision_not_allow` **before** Shell Gate
evaluation; no code path in Gate 8 converts a non-`ALLOW` Gate-7 result into
forward progress. `_gate7_result_digest` (11 fields, Gate 8) is
**unchanged** by this contract — the three additive `Gate7Result` slots are
not hashed into it.

## 10. Gate 9 relationship

```
Gate-7 result  !=  authority consumption
```

Gate 9 is the **sole** owner of authority consumption (approval + proof +
presentation + challenge, atomically, once). Gate 7 consumes nothing —
no approval, HPAC proof, presentation, challenge, nonce, `Gate5Result`,
`Gate6Decision`, authority record, or lifecycle record is created, deleted,
or mutated; no `consumption.json` is written; no Gate-9 primitive is
called. Gate 9 re-derives the Gate-7 lineage and writes
`runtime_enforcement_binding` = `{decision_id, decision_digest, verdict,
expires_at, evaluated_input_digest}` as a **reference**, not a re-run.
**B-1 = Model B1-B: the `HPAC-AUTHORITY-CONSUMPTION/2.1` schema, the closed
5-field `runtime_enforcement_binding` set, `runtime_invocation_authority_
consumption.py`, and HPAC-001 v2.1 §41 are byte-unchanged by the N-16-4
track.** A positive Gate-7 result does not make Gate 9's atomic consumption
optional; a failed Gate 9 does not "un-decide" Gate 7 (Gate 7 has no
durable state — §15).

## 11. Gate 10 relationship

```
Gate-7 ALLOW  ->  does NOT manufacture a DispatchEnvelope or effect authority
```

Gate 10's pre-effect eligibility battery is unchanged. Under Currentness B,
Gate 10 step 13's authority-generation re-derivation against the durable
item-9 snapshot is a **mandatory primary** stale-protection owner (§8.1),
step 11's `re_expires_at` check is the wall-clock backstop, and step 12's
fresh runtime-capability re-read (`== Observed/observe/unavailable`, else
`gate10_runtime_capability_not_unavailable`) is **independent of Gate 7**.
A synthetic positive `Gate7Result` combined with a real runtime-capability
re-read still fails closed at Gate 10 step 12. `run_gate10_pre_effect_
eligibility` mints a `DispatchEnvelope` only after its full battery; a
`DispatchEnvelope` "authorizes nothing" (RPAC-REQ-029).

## 12. Slice-B attempt binding

```
one invocation/attempt  ->  one bounded Gate-7 positive decision
```

`Gate7Result` SHALL stay bound to one `invocation_id` / `attempt_id` /
`idempotency_key` / `request_id`. It permits no retry and no duplicate
effect attempt. The at-most-once guard is Slice B's `dispatch_attempted`
marker keyed by `attempt_id`, recorded at Gate 9 — not anything Gate 7
owns. Gate 7 never reads or writes the Slice-B `RuntimeInvocationRecord`. A
new `attempt_id` (fresh Gate-2 pass, fresh approval) means a fresh Gate-7
evaluation. A `Gate7Result` for `(A, 1)` presented for `(A, 2)` or `(B, 1)`,
or with a changed `idempotency_key`, SHALL be rejected downstream
(`gate*_invocation_binding_mismatch` / lineage / digest mismatch).

## 13. Adapter supply-chain admission — B-2 = Model B2-D

Gate 7 SHALL bind **no** adapter supply-chain admission evidence and SHALL
perform **no** admission lookup. It reads no `admission_record_digest` and
no `admission_class` field, imports no `SupplyChainAdmissionResolver`, and
`_pb_decision_digest`'s composition is **unchanged** (finding N-16-4-2 and
finding N-16-4-3 as framed are **withdrawn** by the `.1R.25` freeze).

Supply-chain admission is an N-16-6 concern, already gated three times and
independently of Gate 7:

- **Gate 6** — POL-013's `P_supply_chain_admission` predicate (N-16-3); the
  `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile is productionally unsatisfiable
  because the sole production `SupplyChainAdmissionResolver` admits nothing,
  so `Gate6Decision(decision="DENY")` → Gate 7 step 2
  `gate7_pb_decision_not_allow:DENY`.
- **Gate 8** — re-resolves the descriptor/config and re-hashes the exact
  executable.
- **Gate 10** — re-checks the admission binding live (lineage-binding
  comparison against `record.target_binding`).

The `.1R.13.1` Gate-6 / Gate-7 trust boundary is preserved verbatim:
`runtime_dispatch_permission.py` is byte-unchanged; `Gate6Decision` is
byte/schema-unchanged; no PB-request object is exposed to Gate 7; Gate 7
performs no policy re-evaluation, no admission revalidation, and no
authority creation.

## 14. PB consumed, not re-run

Gate 7 consumes the already-trusted `Gate6Decision` (via
`runtime_dispatch_permission.is_gate6_decision`, the exact registry object).
It SHALL NOT import or invoke `PolicyRegistry`, `_compose`, any `POL-*` rule
class, `NarrowLocalCliDispatchEligibilityRule`, `ExecutionDisabledRule`, or
`PermissionBroker` evaluation logic. A PB `ALLOW` is necessary but not
sufficient for a Gate-7 `ALLOW`: a trusted Gate-6 `ALLOW` combined with a
Runtime Enforcement violation (an unavailable posture or a matched
per-decision no-go) SHALL yield `Gate7Result(decision="DENY")`. A PB
re-evaluation with a different outcome yields a different `pb.decision` /
`pb.causing_policy_ids` / `pb.decision_reason` → a different
`_pb_decision_digest` → the Gate-7 result is invalidated on Gate 8's
re-run. A stale PB `policy_version` is resolved by re-entering Gate 6, never
by Gate 7.

## 15. Duplicate evaluation and restart

### 15.1 Duplicate evaluation

If `run_gate7_runtime_enforcement` evaluates the same exact invocation /
attempt twice under an unchanged posture:

- **deterministic same `decision`** (`ALLOW → ALLOW` or `DENY → DENY`);
- **deterministic same `runtime_enforcement_result_id` and
  `evaluated_input_digest`** — both are pure functions of the bound inputs
  (`evaluated_at` / `expires_at` differ only if `authority_current_time`
  differs; `expires_at` is not in `runtime_enforcement_result_id`);
- **new object identity each call** — `_GATE7_RESULTS.add(result)` on every
  completed evaluation; the two objects compare `!=` (identity-only
  equality);
- **no durable state, no "attempt consumed"** — Gate 7 stays idempotently
  repeatable. Duplicate evaluation SHALL NOT create transferable authority.

The at-most-once guard is Gate 9's `dispatch_attempted` marker, not Gate 7.
`.1R.26` need not reject a duplicate Gate-7 call — it is harmless.

### 15.2 Restart / persistence — Model A

```
process restart  ->  _GATE7_RESULTS is process-local  ->  a prior Gate7Result is gone
                 ->  is_gate7_result(anything reconstructed) is False
                 ->  Gate 7 MUST be re-run from a freshly re-resolved
                     Gate6Decision + Gate5Result
```

Session restart and machine restart behave identically. There SHALL be no
durable Gate-7 authority store. The durable truth that survives restart is
Gate 9's `consumption.json` `runtime_enforcement_binding` — **audit /
verification evidence, explicitly not `Gate7Result` trust**. Gate 10
re-reads it and re-verifies against a fresh authority-generation
re-derivation (step 13); it does not resurrect a `Gate7Result` handle.
Model B (durable positive-result store) and Model C (hybrid) are
**REJECTED**.

## 16. Observability and audit

- `pcae runtime inspect` / governance reporting MAY expose, for audit, a
  Gate-7 result's `decision`, `causing_reason_ids`, `matched_no_go_ids`,
  and `runtime_enforcement_result_id`. It MUST NOT expose secrets,
  credential material, or the raw approval / projection.
- **Observability MUST NOT become authority.** A displayed
  `runtime_enforcement_result_id` grants nothing — `is_gate7_result` still
  requires registry membership.
- Any `pcae runtime inspect` JSON change to carry such a field MUST be
  additive and optional and MUST preserve the current JSON contract.
  REPRC-001 v1.0 makes **no** `pcae runtime inspect` JSON schema change.
- The durable postmortem proof is Gate 9's `runtime_enforcement_binding`
  (verdict, expiry, `evaluated_input_digest`, `decision_digest`). The
  record proves *what was decided*, never *permits a redo*.

## 17. The synthetic / test-only positive path

The positive branch of `run_gate7_runtime_enforcement` is
`# pragma: no cover - unreachable in production` and SHALL remain
production-unreachable (§18). It is exercised **only** through a
clearly-labelled, documented, in-memory test-only substitution of the
runtime-enforcement posture resolver
(`monkeypatch.setattr(runtime_dispatch_gate7,
"resolve_runtime_enforcement_posture", <substitute>)` returning a
`RuntimeEnforcementPosture` with `execution_available is True` and an empty
`matched_no_go_ids`), together with the existing test-boundary provenance
substitutions (`is_gate6_decision` / `is_gate5_result` /
`is_trusted_validated_authority_projection` /
`revalidate_validated_authority_projection`) and a synthetic
registry-provenanced `Gate6Decision(decision="ALLOW")` — exactly the
`.1R.13` / `.1R.13.2` accepted boundary and the pattern Gates 5–10 already
use. The substitution:

- SHALL remain local / in-memory and SHALL be restored on test teardown;
- SHALL NOT be reachable from any production call site — there is no
  posture parameter on `run_gate7_runtime_enforcement` (§8), no production
  code assigns `resolve_runtime_enforcement_posture`, and no environment
  variable or configuration path enables a positive posture;
- SHALL NOT call an adapter, `adapter.dispatch()`, or a production
  `SupplyChainAdmissionResolver`;
- SHALL NOT alter runtime capability — production
  `resolve_runtime_enforcement_posture()` is untouched and continues to
  return `execution_available is False`;
- SHALL NOT access network, credential, hardware, FIDO2, WebAuthn, or CTAP
  surfaces.

If an ordinary production call path can supply the substitution and obtain a
trusted positive `Gate7Result`, the implementation is non-conformant and
the implementing phase STOPS (BLOCKED).

## 18. Production positive path — unreachable

Using production-only builders, resolvers, and state, a positive
`Gate7Result` SHALL be unreachable. Every one of the following independently
blocks it, and this contract weakens none:

- **N-16-5 (real human authority).** `validate_approval` hard-stops on the
  NON_REAL deterministic-authentication lineage, so no real
  `ValidatedAuthorityProjection` — and therefore no real `Gate5Result` —
  exists for a real request; Gate 7 step 5 rejects with
  `gate7_stale_validated_authority_projection`.
- **N-16-6 (supply-chain admission).** The sole production
  `SupplyChainAdmissionResolver` admits nothing → POL-013 DENY →
  `Gate6Decision(decision="DENY")` → Gate 7 step 2
  `gate7_pb_decision_not_allow:DENY`.
- **Runtime Enforcement no-go posture.** Under the current posture the
  per-decision no-go set is non-empty (at least RE-NOGO-001, RE-NOGO-002,
  RE-NOGO-010, RE-NOGO-011) and `execution_available is False`; Gate 7
  step 7 returns `Gate7Result(decision="DENY")`.
- **N-16-7 (runtime capability).** `execution_availability == "unavailable"`;
  Gate 10 step 12 re-reads capability and fails closed.

The production `run_gate7_runtime_enforcement(...)` SHALL still return `DENY`
(or `(None, reasons)`) for every currently constructible real production
request. The synthetic test path (§17) is the only positive path.

## 19. No-go semantics

Any applicable unresolved hard Runtime Enforcement no-go SHALL yield
`Gate7Result(decision="DENY")`. The positive branch is reached **only** when
`posture.execution_available is True` **and** `posture.matched_no_go_ids`
(the per-decision subset) is **empty** — there is no "trusted narrow
profile" shortcut around Runtime Enforcement no-go semantics. A positive
result SHALL carry an empty `matched_no_go_ids`. The RE No-Go Registry
(schema 1.1) is byte-unchanged: no ID, class, or statement change, no new
entry, no annotation — the synthetic path substitutes a *resolver*, not the
`DEFAULT_AUTHORIZATION_FLAGS` / `DEFAULT_SAFETY_FLAGS` constants or the
`AUTH_FLAG_TO_NO_GO` map. Environmental-readiness no-gos (009, 013, 015,
016, 017) are enforced separately by the execution-enablement readiness
process; Gate 7's per-decision projection deliberately does not carry them.

## 20. Positive rationale vocabulary

The positive branch SHALL set a stable, REPRC-owned positive
`causing_reason_ids` vocabulary — never an empty tuple, never ad-hoc
prose-only rationale. Minimally:

```
gate7_runtime_enforcement_satisfied
gate7_pb_decision_allow_consumed
gate7_authority_projection_revalidated
gate7_runtime_target_within_local_cli_v1_scope
gate7_no_blocking_re_no_go_matched
gate7_synthetic_evaluation_path
```

`gate7_synthetic_evaluation_path` SHALL be present whenever the posture
resolver was substituted (§17) — i.e. on every currently reachable positive
result. Negative-branch reasons remain the current fail-closed set
(`gate7_runtime_execution_unavailable`, `gate7_safety_no_go:<id>`,
`gate7_stale_validated_authority_projection`, `gate7_pb_decision_not_allow:<value>`,
`gate7_invocation_binding_mismatch`, `gate7_runtime_target_ineligible`,
`gate7_authority_subject_scope_mismatch`,
`gate7_request_currentness_drift:<fact>`,
`gate7_internal_error_fail_closed`, …), unchanged.

## 21. Sole constructor and consumers

The sole production constructor of a `Gate7Result` is
`run_gate7_runtime_enforcement` in `src/pcae/core/runtime_dispatch_gate7.py`
— the sole production owner of the RDGO-001 §8 Gate-7 boundary. No generic
public constructor grants authority through structure. This contract adds no
second constructor and no signature change.

The **finite** set of legitimate production consumers of a `Gate7Result` is
exactly:

```
src/pcae/core/runtime_dispatch_gate8.py            (Gate 8)
src/pcae/core/runtime_dispatch_gate9.py            (Gate 9)
src/pcae/core/runtime_dispatch_gate10_eligibility.py  (Gate 10 pre-effect eligibility)
```

Each consumes the result via a function-local import and validates
`is_gate7_result(result)` + `result.decision == "ALLOW"` by exact string
equality before any downstream progression, and treats it as authority for
nothing (§2.1). `runtime_dispatch_gate8._gate7_result_digest` imported by
`runtime_dispatch_gate10_eligibility` is an intra-family helper import, not
a fourth consumer. The implementing phase and its independent verification
SHALL each carry a consumer-inventory guard: an **exact finite** production
allowlist (no wildcard, no `fnmatch`, no package prefix, no
"contains-at-least") plus a separate explicit finite test allowlist,
rejecting any other importer.

## 22. Contract-production equivalence obligation

Every normative requirement of REPRC-001 SHALL be mapped, by the
implementing phase and re-derived by its independent verification, to exact
production-source and test evidence — `decision` meaning (§2), non-bearer
trust (§4), schema (§1), result identity (§3), immutability (§6), TTL (§7),
Currentness B and the four stale-rejection owners (§8), serialization /
restart (§5, §15), Gate-8 / Gate-9 / Gate-10 / Slice-B independence
(§9–§12), PB-consumed-not-re-run (§14), no-go semantics (§19), the positive
vocabulary (§20), the finite consumer set (§21). No prose-only guarantee.

## 23. Invariants

| ID | Statement |
|---|---|
| REPRC-INV-001 | A positive `Gate7Result` is invalid across any change to `invocation_id`, `attempt_id`, `idempotency_key`, the PB decision digest, the evaluated-input digest (any component), the authority-freshness digest, the runtime-posture digest, or `reprc_schema_version` (§3.1). |
| REPRC-INV-002 | A stale positive `Gate7Result` is rejected by a **named** owner — Gate 7 creation-time projection revalidation, Gate 8's Gate-7 re-run, or Gate 10 step 13 — before it can acquire meaningful downstream authority; TTL (Gate 10 step 11) is the wall-clock backstop (§8.1). |
| REPRC-INV-003 | A `Gate7Result` is non-bearer and non-transferable: structure, field equality, digest consistency, serialized form, and a known `runtime_enforcement_result_id` are each insufficient; only construction under the seal + `_GATE7_RESULTS` membership + live re-validation confer trust (§4, §5, §8.2). |
| REPRC-INV-004 | Gate 7 consumes nothing, writes no `consumption.json`, calls no Gate-9 primitive, binds no adapter-admission evidence, re-runs no PB policy, and mutates no runtime capability (§10, §13, §14, §18). |
| REPRC-INV-005 | A positive `Gate7Result` permits progression to Gate 8 evaluation only; Gates 8, 9, and the Gate-10 pre-effect read-back each remain independently required and independently authoritative (§9–§11). |
| REPRC-INV-006 | The production positive path is unreachable (§18); the synthetic positive path (§17) is local, in-memory, restored on teardown, and unreachable from any production call site. |

## 24. Versioning and freeze verdict

REPRC-001 uses contract `MAJOR.MINOR`. **v1.0 is the initial freeze.** A
MINOR re-states verified behaviour and adds no incompatible change. A change
that alters the `decision` meaning of §2, removes an §8.1 mandatory owner,
makes `Gate7Result` bearer or durable, changes the §3 identity composition
incompatibly, or widens the §21 consumer set requires a new MAJOR plus
explicit human authorization and independent verification. A change to
`reprc_schema_version` (§1) is at least MINOR and invalidates every prior
`runtime_enforcement_result_id`.

The N-16-4 track makes **no** change to RDGO-001 (stays v3.1), HPAC-001
(stays v2.1), `HPAC-AUTHORITY-CONSUMPTION` (stays `/2.1`), PBRD-001,
PBNDE-001, PBPA-001, RPAC-001, RIHAC-001, RIASC-001, the RE No-Go Registry,
or NG-025. A future RDGO-001 v3.2 MINOR §8 cross-reference to REPRC-001 is a
separate, deferred normalization item; REPRC-001 v1.0 is self-standing and
cross-references RDGO-001, not the reverse. N-23-2 remains INFO / DEFERRED
NORMALIZATION DEBT and is not touched here.

**REPRC-001 v1.0: FROZEN.** A positive Gate-7 Runtime Enforcement result is
single-attempt, expiring, non-bearer, non-transferable, invocation/attempt-
bound, currentness-anchored by Currentness B, subordinate to Gates 8/9/10
and the Slice-B lifecycle, and unreachable in production.
