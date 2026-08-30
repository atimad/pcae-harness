# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.16 — Gate-10 First External Effect Architecture and Implementation Planning

**Type:** architecture / planning only.
**Status:** COMPLETE.
**Production source changed:** none (`git diff --name-only <entry> HEAD -- src/pcae` empty).
**Normative contracts changed:** none.
**Gate 10:** architecture derived; **not implemented**. No `runtime_dispatch_gate10.py`, no `run_gate10*` symbol, no `DispatchEnvelope` mint, no adapter call. No implementation phase begun.
**Execution:** not enabled. Runtime remains `not_implemented / Observed / observe / unavailable`; POL-005 unchanged; 0 plugins / 0 capabilities.
**Phase-entry SHA:** `c7a50c10` (`origin/main` synced; `origin/main..HEAD = 0`).
**Governance:** governed `pcae` lifecycle only. The delegated `.3` finalization / commit / push incident remains **UNAUTHORIZED**; only the primary human-authorized operator holds `.1R.16` lifecycle authority. Delegated workers may assist within explicit scope only and may not autonomously commit / finalize / push.

This document is the canonical planning artifact required by the phase
prompt §70. The required final report is §30.

---

## 1. Current independently verified architecture (established; not reopened)

Treated as verified unless fresh primary evidence in this document disproves
it (none does):

| Component | State | Verifying phase | Primary re-check this phase |
|---|---|---|---|
| Human-principal / HPAC foundation | VERIFIED | `.1R.3` / `.1R.8` | `hpac_verifier.py` / `hpac_lifecycle.py` call-graph spot-read |
| Mechanism-neutral HPAC verifier | VERIFIED | `.1R.5.2.1` / `.1R.8` | — |
| B1 / B7 / N1 / N2 production-authority repair | CLOSED | `.1R.8` | — |
| Gate 5 — Approval Validation coordinator | CLOSED | `.1R.11` | `runtime_dispatch_gate5.py` unchanged since `4d480553` (`.1R.15.5` §10) |
| Gate 6 — Permission Broker production consumer | CLOSED | `.1R.13` | `runtime_dispatch_permission.py` unchanged since `4d480553` |
| Gate 7 — Runtime Enforcement coordinator | CLOSED | `.1R.13.3` | `runtime_dispatch_gate7.py` unchanged since `4d480553` |
| Gate 8 — Process Containment (Shell Gate) coordinator | CLOSED | `.1R.13.5` | `runtime_dispatch_gate8.py` unchanged since `4d480553`; `Gate8EffectPlan` / `Gate8Result` re-read |
| Gate 9 — Atomic Authority Consumption coordinator | CLOSED | `.1R.15` | `runtime_dispatch_gate9.py` re-read line-by-line (§5, §9, §13, §17, §18) |
| Gate-9 serialization window (V-15-1) | CLOSED | `.1R.15.3` | `S1`/`S2` source order re-confirmed (`i_s1 < i_build < i_s2 < i_create`) |
| Runtime-dispatch contract normalization | CLOSED | `.1R.15.5` | RDGO v3.1 / PBRD v2.1 / HPAC v2.1 / RIASC §9 errata / RE-registry 1.1 read in full |
| Durable authority-generation binding (`HPAC-AUTHORITY-CONSUMPTION/2.1`) | CLOSED | `.1R.15.5` | `runtime_invocation_authority_consumption.py` re-read in full |
| N-15-3-2 resolver completeness | CLOSED | `.1R.15.5` | `build_production_authority_generation_resolver` re-read |

**Current runtime:** State `Observed`; Maximum Capability `observe`; Execution
Availability `unavailable` (`pcae runtime inspect`, `runtime_introspection.py`
constants `CURRENT_RUNTIME_STATE` / `CURRENT_MAXIMUM_PLUGIN_CAPABILITY` /
`EXECUTION_AVAILABILITY`, read directly). Gate 10 is absent and has no phase ID.

**`.1R.15.1` §20 Gate-10 prerequisite items 1, 8, 10 are SATISFIED**
(`.1R.15.5` §14). Item 9 remains separately tracked — adjudicated in §7.

---

## 2. Initial repository inspection (phase prompt §4)

Executed at phase entry (before the `.1R.16` task was opened):

```
git status --short                       -> clean
git status --branch --short              -> ## main...origin/main
git log --oneline -40                    -> HEAD c7a50c10 (.1R.15.5 governance push-check trust-field correction)
git log --oneline origin/main..HEAD      -> (empty)
git rev-list --count origin/main..HEAD   -> 0
pcae health                              -> Overall status: healthy; agent lock claude-local; continuity verified; git clean
pcae check                               -> PCAE check passed
pcae status coherence                    -> passed
pcae doctor task-memory                  -> warning-only: historical tasks/DONE.md omissions (pre-existing O4 hygiene debt); no current-phase error
pcae push check                          -> Mode: nothing_to_push; phase-report trust + identity: passed
pcae runtime inspect                     -> not_implemented / Observed / observe / unavailable; 0 plugins; 0 capabilities;
                                            Permission Broker status: execution_unavailable; governance posture: non-executing
source ~/.config/pcae/telegram.env; pcae notify status
                                         -> Telegram configured, enabled, outbound-ready
pcae phase-report show --latest          -> .1R.15.5 — VERIFIED WITH NON-BLOCKING FINDINGS — CONTRACT NORMALIZATION COMPLETE; notification sent; report consistent
```

**Confirmed:** `.1R.15.5` is the latest completed phase; repository clean; no
active governed phase existed before this phase's task was opened;
`origin/main..HEAD = 0`; runtime remains `Observed / observe / unavailable`.

### 2.1 Primary sources read in full

**Contracts** (`docs/contracts/`, current frozen text): RDGO-001 v3.1
(`RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md`), PBRD-001 v2.1
(`PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md`, §12 in full), HPAC-001 v2.1
(`HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`, §41 authority-consumption
schema), RIHAC-001 v2.0 (`RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md`,
§14 / §19), RIASC-001 v3.0 + §9 errata
(`RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md`), RPAC-001 v1.0
(`RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`, read in full — §7, §9, §10, §13,
§16, §17), PBPA-001 (`PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`),
POL-005 (`ExecutionDisabledRule`, `permission_broker_foundation.py:695`),
RE No-Go Registry (`RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`, schema 1.1).

**Phase documents:** `.1R.15.5` (contract-normalization IV), `.1R.15.4`
(contract normalization impl), `.1R.15.3` (Gate-9 serialization repair IV),
`.1R.15.2` (Gate-9 serialization repair), `.1R.15` (Gate-9 IV), `.1R.14`
(Gate-9 impl), `.1R.15.1` (normalization planning — §19 normalized
gate-chain model, §20 prerequisites, §22 forward invariant, §24 phase-ID
conventions), `.1R.13.5` (Gate-8 IV), `.1R.13.3` (Gate-7 IV), `.1R.13.1`
(Gate-7/8 planning — §16.2 handoff invariants), `.1R.13` (Gate-6 IV),
`.1R.11` (Gate-5 IV), `.1R.9` (Gate-5/9 planning), `.1R.13`/`.1R.11`
gate-verification anchors; `3S.2.1` (production dry-lifecycle IV — §62
MUST-FIX findings).

**Current production source read line-by-line:**
`runtime_dispatch_gate9.py` (1339 lines — full),
`runtime_invocation_authority_consumption.py` (full),
`runtime_introspection.py` (full — capability source),
`runtime_adapter.py` (full — RPAC mock-v1 scaffolding, `DispatchReceipt`,
`simulate_invocation`), `runtime_dispatch_gate8.py`
(`Gate8EffectPlan` / `Gate8Result` / `ResolvedExecutable`),
`mock_runtime_adapter.py` (surface), `backend_invocations.py` (header),
`delivery_receipt.py` (header), `permission_broker_foundation.py`
(`ExecutionDisabledRule`).

Where a phase summary and the primary contract / source diverged, the
contract / source text governs (phase prompt §3).

---

## 3. Purpose and the planning question

Define the exact Gate-10 architecture for the first external effect and
freeze the safe implementation sequence.

**The planning question (phase prompt §2).** How may PCAE cross from
independently verified, durably consumed Gate-9 authority into the first
external effect without allowing **stale authority, stale capability, stale
containment state, replay, or a copied result** to authorize dispatch?

**Answer, in one paragraph (full derivation §5–§28).** Gate 10 owns the
front-half **pre-effect eligibility + read-back battery** (RDGO-001 v3.1
§11's six mandatory checks) and the **one `adapter.dispatch()` call site**
across the established containment; it owns *neither* a second authority
record *nor* a second PB / RE policy evaluation. The authoritative,
create-only, immutable `HPAC-AUTHORITY-CONSUMPTION/2.1` record written at
Gate 9 is the *at-most-once authority-consumption* truth; Gate 10 re-reads
it byte-for-byte and re-derives current mutable authority + the
authority-generation vector against its durable snapshot. A **separate,
non-authoritative, append-only repository-side mirror record** (RPAC-REQ-067)
carries the dispatch-attempt lifecycle — `PREPARED → EFFECT_ATTEMPT_STARTED
→ {RECEIPT_CAPTURED | DISPATCH_UNCERTAIN | DISPATCH_NOT_STARTED}` — written
**before** the adapter call (write-before-effect; Model A + a two-state
lifecycle, Model C). PCAE can guarantee only **at-most-once dispatch
attempt with fail-closed uncertainty**, never exactly-once for an arbitrary
external system. A Gate-10 eligibility failure **before** any effect
produces no effect and does **not** un-consume Gate-9 authority; a fresh
`invocation_id` + fresh human approval + fresh proof is required for any new
attempt. **No positive production Gate-10 path exists today** (§23) and none
is created; a structural, non-effecting Gate-10 eligibility coordinator MAY
nonetheless be implemented now, exactly as Gates 5–9 were — its effect
branch is unreachable behind the capability-unavailable hard stop
(Option A + C, §22).

Implementation is *not* ready merely because Gate 9 is closed (§7, §22,
§23).

---

## 4. Re-derived RDGO-001 v3.1 Gate-10 contract responsibility (phase prompt §5)

Derived from RDGO-001 v3.1 §1 (table row 10), §11, §14, §15, §17, §19 —
read directly, not inferred from "run subprocess".

### 4.1 What Gate 10 owns

| # | Responsibility | Contract anchor |
|---|---|---|
| G10-a | **Dispatch-attempt authorization consumption check** — require a trusted `Gate9Result` with `status == "consumed"` (not `already_consumed`, not provenance alone) | RDGO §11 items 1–2; §10 last ¶; `.1R.15.1` §22 |
| G10-b | **Final durable read-back** — fresh re-read of the canonical `consumption.json` (`HPAC-AUTHORITY-CONSUMPTION/2.1`) + containment evidence, byte-verified against `x.record_digest`, `authority_generation_binding` present and valid | RDGO §11 item 3; HPAC-001 v2.1 §41 |
| G10-c | **Exact lineage / binding match** — `invocation_id` / `attempt_id` / `idempotency_key` / `proof_id` / `approval_id` equal across the durable record **and** the live request | RDGO §11 item 4; §10a; §16 |
| G10-d | **Final runtime-capability check** — execution availability, adapter registration, containment re-established, at Gate-10 entry | RDGO §11 item 5; §10 last ¶ |
| G10-e | **Re-validation of all mutable authority** as-of Gate-10 entry (principal / credential / proof / approval / lifecycle) **and** re-derivation of the current authority-generation vector, compared against the durable `authority_generation_binding` snapshot | RDGO §11 item 6 (the V-15-1 second line of defence) |
| G10-f | **Final containment / effect-plan read-back** — re-establish and re-attest the exact effect Gate 8 validated and Gate 9 consumed; recompute `containment_evidence_digest` and compare | RDGO §9(c); §11 item 5; §15 TOCTOU table |
| G10-g | **Executable identity re-stat / re-hash immediately before effect** | RDGO §15 row "Adapter executable identity → Yes, exact hash before spawn"; §9 |
| G10-h | **DispatchEnvelope mint** — immutable `InvocationRequest` + fresh target-status digest + approval digest + PB decision digest(s) + RE decision digest + durable record reference + expiration | RPAC-REQ-029; RDGO §11 "immutable dispatch envelope" |
| G10-i | **Effect invocation** — exactly one `adapter.dispatch(envelope)` through already-established containment, argument vector (never shell), no scope widening | RDGO §11; RPAC-REQ-031/032/048 |
| G10-j | **Attempt-receipt observation** — capture one `DispatchReceipt` **or** an `uncertain` / `failure` state; record it on the non-authoritative mirror | RDGO §1 row 10 "one process-spawn/dispatch receipt or uncertain/failure state"; §11; §17 |
| G10-k | **Failure / no-retry semantics** — a pre-effect rejection produces no effect; consumed authority stays consumed; no automatic replay | RDGO §11; §17; §18; RPAC-REQ-071/072 |

### 4.2 What Gate 10 does NOT own

| Not Gate 10's | Owner | Anchor |
|---|---|---|
| Adapter / backend / target **selection** | Gate 2 (explicit `runtime_target_id`; no fallback) | RDGO §3; RPAC-REQ-053 |
| **PB policy evaluation** (re-run) | Gate 6 only | RDGO §7, §8 (V-13-3-1 clarification); §15 |
| **RE policy / no-go re-evaluation** | Gate 7 (Gate 10 revalidates *currentness*, not policy) | RDGO §8 |
| **Approval / proof / presentation / challenge consumption** | Gate 9 only (the single `dispatch_attempted` atomic write) | RDGO §10; `.1R.13.1` handoff table row |
| **The durable pre-dispatch `dispatch_attempted` marker itself** | Gate 9 (item 8 of the nine) | RDGO §1 row 9; §10 |
| **Result normalization / intake / review / promotion** | Gate 11 + existing producer-neutral intake | RDGO §12; RPAC-REQ-080 |
| **Effect-plan assembly** (cwd / argv / env) | trusted invocation coordinator, from descriptor/config (never caller) | RDGO §9 |

### 4.3 Consequence — Gate 10 is a *validating gate that ends in exactly one effect call*

RDGO §1 explicitly places the durable-before-effect marker at **Gate 9**
(row 9, "no process effect yet") and Gate 10's *input* is "Immutable
dispatch envelope and established containment", its *output* "One
process-spawn/dispatch receipt or uncertain/failure state". Gate 10
therefore does **not** need its own pre-effect *authority* write — the
authoritative durable-before-effect commit already exists. Gate 10's only
new durable footprint is on the **non-authoritative mirror** (§9, §11).
Failure / retry / crash semantics are **frozen at the contract level in
RDGO §17 / §18** and Gate 10's architecture must *realize*, not redefine,
them.

---

## 5. The exact first-effect boundary (phase prompt §6)

### 5.1 Inventory of every current source location that could perform an external effect

| Effect class | Where it *would* live | Current state | Called in the RDGO Gate 5–11 chain? |
|---|---|---|---|
| subprocess / process spawn | `RuntimeAdapter.dispatch()` real impl for a `local_cli` target (`descriptor.execution_effect == "local_process"`) | **does not exist** — no real adapter implementation, `RuntimeAdapterResolver` has no callable instance for a real target | No |
| provider / network invocation | `RuntimeAdapter.dispatch()` real impl for an `api_provider` target (`execution_effect == "remote_request"`) | does not exist | No |
| runtime adapter call (mock) | `runtime_adapter.simulate_invocation()` → `resolved.adapter.dispatch(envelope)` (line 488); `MockDryRuntimeAdapter.dispatch()` | exists; `simulation_only=True`, `execution_effect="none"`, fixed local fixtures, **no** subprocess/network | No — `simulate_invocation` is the RPAC mock-v1 coordinator (3R plan §23 order), **not** wired to `run_gate5..run_gate9` |
| repository mutation | intake / promotion governance (Gate 11 downstream) | governed; not a Gate-10 concern | No |
| backend invocation | `backend_invocations.py` (Phase 94B) | simulation/validation only; RPAC-REQ-097 "historical execution surface, not an RPAC-conformant adapter" | No |
| external API call (notification) | `delivery_receipt.py` (Phase 134E.7), Telegram delivery | "not yet active lifecycle authority"; unrelated to runtime dispatch | No |
| credential-backed operation | future just-in-time secret resolver | **does not exist** — RPAC-REQ-084 "explicit blocker for a real authenticated adapter" | No |
| hardware operation | HATP hardware-credential path | out of the runtime-dispatch chain | No |

### 5.2 Which exact operation is Gate 10's first effect

**The single call site `adapter.dispatch(envelope)` inside the future
Gate-10 coordinator, invoking a *real* (non-mock) `RuntimeAdapter`
implementation whose `RuntimeDescriptor.execution_effect` is `local_process`
(RPAC-REQ-095: the first post-mock implementation SHOULD be a generic,
fixed-argv external executable adapter tested with a deterministic non-AI
fixture).** For that adapter the concrete effect is an `os.posix_spawn` /
`subprocess.Popen`-class process creation with the frozen argv, the
repository-bound cwd, the sanitised env allowlist, network denied, and no
credential access (`Gate8EffectPlan.credentials_required == False`).

**No such adapter is registered, implemented, or reachable today.** The
`simulate_invocation` path is the *simulation analogue* and is deliberately
kept out of the Gate 5–11 sequence (RDGO §20: "The dry
`adapter_invocation`/`simulation_only=true` path remains unchanged and is
not migrated into this sequence").

**This phase calls none of them.**

---

## 6. Gate9Result provenance and success requirements (phase prompt §8)

Re-derived from `runtime_dispatch_gate9.py` (`Gate9Result`,
`is_gate9_result`, `_GATE9_RESULTS`) and RDGO §11 items 1–2.

- `is_gate9_result(x)` returns `True` **only** for the literal object a past
  `run_gate9_atomic_authority_consumption` call returned and inserted into
  the module-local `_GATE9_RESULTS` identity set (`__eq__`/`__hash__` are
  `id`-based; `__reduce__` raises; `__init_subclass__` raises; the `_seal`
  guard rejects direct construction). A copy, `deepcopy`, field-reconstruct,
  `object.__new__`, pickle round-trip, or duck-typed lookalike fails
  (independently re-confirmed `.1R.15.5` §16).
- **`provenance != successful consumption`.** `is_gate9_result(x) is True`
  is satisfied by *both* `status == "consumed"` and
  `status == "already_consumed"`.
- **Gate 10 MUST additionally require `x.status == "consumed"`** — the exact
  normalized success status. `already_consumed` means "some prior valid
  consumption exists; this call was a replay / concurrency-loser /
  crash-after-commit retry" and is **never** a re-entry licence to Gate 10
  (RDGO §10 "a byte-identical record is 'already consumed', not a re-entry
  licence"; RDGO §18).

**Frozen forward requirement F-G10-1:** `is_gate9_result(x) and x.status ==
"consumed"` is the necessary (not sufficient) gate. All of §6's, §8's, §9's,
§10's checks are additionally required.

---

## 7. Prerequisite item 9 adjudication (phase prompt §7)

### 7.1 Re-derivation of `.1R.15.1` §20 item 9

`.1R.15.1` §20 item 9 (verbatim): *"The two 3S.2.1 prerequisite repairs
(malformed-result handling; runtime-inspect repair) at their required
reachability point (PBRD-001 §12 items 9–10) — tracked separately, blocking
before the first non-mock adapter, surfaced here for completeness."*

Cross-referenced to primary source:

- **PBRD-001 §12** (POL-005 evolution boundary) enumerates eleven
  separately-implemented-and-verified conditions before `runtime_dispatch`
  may become POL-005-eligible; item **9** = "the two 3S.2.1 prerequisite
  repairs at their required reachability point"; item **10** =
  "runtime-inspect repair before any real adapter availability claim".
- **3S.2.1 §62** — the two MUST-FIX items, both explicitly **non-blocking**:
  1. `simulate_invocation` (`runtime_adapter.py` ~501) calls
     `store.write_result()` on an unvalidated `adapter.collect()` return; a
     non-`RuntimeInvocationResult` raises an uncaught `AttributeError`
     instead of a clean `FAILURE_MALFORMED_RESULT` outcome. **Reachability:
     none in current production** — `_run_with_context` only instantiates
     `MockDryRuntimeAdapter()`, which always returns a well-formed result;
     "this gap only matters for a future, non-mock adapter implementation".
  2. `RuntimeInvocationStore` does not sanitise `invocation_id` against path
     traversal. **Reachability: none in current production** — both public
     entry points internally generate the id; recorded as defence-in-depth
     debt "for any future caller of the store".
  3S.2.1 §65/§67: "both non-blocking to the production-consumption verdict —
  neither is reachable through the current production entry point today …
  can be folded into whichever prerequisite phase touches
  `RuntimeInvocationStore` next, rather than justifying a standalone repair
  phase right now."
- **RDGO §12** (Gate 11): "This contract does not repair the existing
  3S.2.1 malformed-result finding; that repair is **blocking before the
  first non-mock adapter becomes reachable**."
- **runtime-inspect repair** (3S.2.1 §62 observation 2 / §44 / §61) —
  `pcae runtime inspect` does not surface the dry-consumption capability;
  classified `TRUTHFUL_WITH_LIMITATION`, "not blocking".

### 7.2 Disposition

| Question | Verdict | Evidence |
|---|---|---|
| SATISFIED? | **NO** — neither 3S.2.1 repair is implemented; runtime-inspect discoverability gap open | 3S.2.1 §62; `pcae runtime inspect` output §2 |
| NOT SATISFIED but not blocking this planning phase? | **YES** | 3S.2.1 §62/§65/§67; RDGO §12; `.1R.15.5` §14 ("tracked separately … not this phase's scope") |
| BLOCKING for Gate-10 *planning*? | **NO** | phase-prompt §7 test: item 9 does not require an implementation/contract phase *before Gate-10 planning can continue*; the items are downstream of the effect, not of the architecture |
| BLOCKING for a *structural, non-effecting* Gate-10 eligibility coordinator (Slice A / `.1R.17`)? | **NO** | the eligibility battery + envelope mint never touch `RuntimeInvocationStore.write_result` or a non-mock adapter; the malformed-result path is a Gate-11 result-capture concern |
| BLOCKING for the dispatch-attempt durable lifecycle (Slice B / `.1R.19`)? | **PARTIAL — fold in** | Slice B *does* touch `RuntimeInvocationStore` / the mirror record; per 3S.2.1 §65 the two repairs "can be folded into whichever prerequisite phase touches `RuntimeInvocationStore` next" — that phase is Slice B. Recommendation: Slice B's scope explicitly includes both 3S.2.1 MUST-FIX repairs + the runtime-inspect repair |
| BLOCKING for the first concrete effect adapter integration (Slice C)? | **YES — hard prerequisite** | RDGO §12; PBRD §12 items 9–10; 3S.2.1 malformed-result "blocking before the first non-mock adapter becomes reachable" |
| DEFERRED? | **YES** — to Slice B (repairs) and gated for Slice C | as above |

**Item 9 does NOT block safe Gate-10 planning.** It is `NOT SATISFIED /
DEFERRED`, folded into Slice B, and a hard prerequisite for Slice C. **This
planning phase continues** (no STOP condition triggered — phase prompt
"Valid early STOP conditions" clause 2 requires item 9 to be *Blocking and
require an implementation/contract phase before Gate-10 planning can
continue*; it is neither).

---

## 8. Durable `/2.1` consumption-record re-read (phase prompt §9)

Re-derived from `runtime_invocation_authority_consumption.py`
(`RuntimeInvocationAuthorityConsumptionStore.resolve`,
`_TOP_ALLOWED_FIELDS`, `_BINDING_FIELD_SETS`,
`_validate_authority_generation_binding`) and RDGO §11 item 3.

**Frozen mandatory re-read F-G10-2.** Gate 10 SHALL, at entry, freshly call
`RuntimeInvocationAuthorityConsumptionStore(root).resolve(proof_id)` and:

| Check | Mechanism | Fail-closed on |
|---|---|---|
| **Lookup key** | `proof_id` (from `Gate9Result.proof_id`), sanitised by `require_safe_relative_id_component`; canonical path `<root>/proofs/v2/<proof_id>/consumption.json` | traversal / symlink → `DurabilityUncertainError` |
| **Canonical store** | the bound proof's protected `consumption.json` under the production-resolved `HPAC_PROTECTED_ROOT` (RDGO §10; HPAC-001 §41) — **not** a repository mirror | absent → `resolve` returns `None` → **no Gate-10 effect** (not "unconsumed authority to reuse"; a fresh invocation is required) |
| **Provenance / integrity** | `read_canonical_json_document`; recomputed `canonical_digest(without_digest) == stored record_digest`; closed top-level field set exactly `_TOP_ALLOWED_FIELDS` (11 keys) | mismatch / partial / corrupt → `DurabilityUncertainError` → fail closed, **never** replay |
| **Schema version** | `consumption_schema_version == "HPAC-AUTHORITY-CONSUMPTION/2.1"` | `/2.0` → Gate-10-**ineligible** (§10); any other → `DurabilityUncertainError` |
| **Digest binding** | byte-verify the resolved `record.record_digest == Gate9Result.record_digest` (and, transitively, every binding sub-object) | mismatch → fail closed |
| **`Gate9Result` ↔ durable-record binding** | `Gate9Result.proof_id == record`'s bound proof; `Gate9Result.approval_id == authority_binding.approval_id`; `Gate9Result.invocation_id == request_identity.invocation_id`; `Gate9Result.attempt_id == request_identity.attempt_id`; `dispatch_binding.state == "dispatch_attempted"` | any mismatch → fail closed |

Gate 10 trusts **the durable record**, re-derived from disk, never the
in-memory `Gate9Result` fields beyond using them as the lookup + comparison
key. The `Gate9Result` may not even survive the process that produced it
(§9); the durable record is the sole cross-restart truth.

---

## 9. `/2.0` ineligibility (phase prompt §10)

`runtime_invocation_authority_consumption.py:resolve` is version-aware: a
well-formed `/2.0` document (closed field set `_TOP_ALLOWED_FIELDS_LEGACY_2_0`
= the 11 keys minus `authority_generation_binding`) round-trips with
`authority_generation_binding is None`. RDGO §10 / §11 item 3 / phase-prompt
§18: a `/2.0` record is **readable historical/test data but NOT eligible for
Gate 10** — the durable authority-generation snapshot RDGO §11 item 6
requires is structurally absent.

**Frozen F-G10-3.** Gate 10 SHALL fail closed
(`gate10_consumption_record_generation_snapshot_absent`) when
`resolved.authority_generation_binding is None` **or** the schema version is
not exactly `/2.1`. **No compatibility fallback** may treat a `/2.0` record
as executable authority. (`.1R.15.5` §8: `git grep` restricted to
`consumption.json` paths → **zero `/2.0` records exist anywhere in the
repository**; this is defence-in-depth with nothing live depending on it —
N-15-4-1, informational.)

---

## 10. Durable generation-snapshot read-back (phase prompt §11)

`authority_generation_binding` is the closed 6-field
`HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0` object
(`_BINDING_FIELD_SETS["authority_generation_binding"]`:
`snapshot_schema_version`, `principal_generation`, `credential_generation`,
`approval_generation`, `lifecycle_generation`, `consumption_generation`).
It is the exact `S1` Gate 9 captured after its in-boundary revalidation
battery and verified unchanged at `S2` immediately before the atomic create
(built at step 15 from the step-14a capture, **never** rebuilt from post-`S2`
state — `.1R.15.5` §7 source-order proof).

**Frozen F-G10-4.** Gate 10 SHALL independently validate, from the durable
record:

| Sub-check | Mechanism |
|---|---|
| schema | `snapshot_schema_version == AUTHORITY_GENERATION_SNAPSHOT_SCHEMA_VERSION` (`_validate_authority_generation_binding`, re-run) |
| integrity | each `*_generation` a non-empty ≤256-char stripped string; whole-object inside the record's `record_digest` |
| generation fields present | all five markers present and well-formed |
| relationship to the consumed Gate-9 record | the object is a member of *this* `proof_id`'s `consumption.json`; `consumption_generation == "absent"` (Gate 9 only ever writes `absent` — a present/uncertain record short-circuits before the create; `_serialize_consumption_generation`) |

**Snapshot possession is not authority** (RDGO §11 last ¶; HPAC-001 v2.1
"verification evidence, not execution authority"; `.1R.15.5` §16 — no key
contains `capab`/`authoriz`/`allow`/`grant`/`bearer`/`execut`). Its sole
use: the comparison target for §11's current-state re-derivation.

---

## 11. Current generation-state re-read (phase prompt §12)

**Frozen F-G10-5.** Gate 10 SHALL, at entry, re-resolve current canonical
generation state for **at least** the five sources, from durable stores
only — **never** the Gate-9 in-memory `S1`/`S2` and never a cached
`Gate5Result.projection`:

| Source | Canonical resolver (production factory required — §11.1) | Compared against |
|---|---|---|
| principal | `principal_registry.resolve_canonical_principal(principal_id).record_digest` | `authority_generation_binding.principal_generation` |
| credential | `principal_registry.resolve_canonical_credential(credential_id).record_digest` | `.credential_generation` |
| approval | `canonical_digest({approval_id, approval.record_digest, revocation_artifact_digest=None})` (RIHAC-001 §14 forward hook) | `.approval_generation` |
| lifecycle / proof | `compute_canonical_digest` over the ordered `(sequence, state, event_digest)` triples of the entire `resolve_canonical_chain(proof_id)` | `.lifecycle_generation` |
| consumption state | `consumption_store.resolve(proof_id)` → `("present", record_digest)` (Gate 10 expects the record it is validating) | `.consumption_generation` was `"absent"` at Gate 9; Gate 10 sees `"present"` — this is **expected and correct**, not drift (the record's own creation was the transition) |

Any **principal / credential / approval / lifecycle** mismatch → **fail
closed, no effect** (`gate10_authority_generation_drift:<source>`). This
must work **after a restart** — every token is a digest over durable state,
carrying no wall-clock / nonce / process identity (`.1R.15.2` §7,
re-confirmed `.1R.15.5` §7).

### 11.1 Finding N-16-1 — no production `authority_generation_resolver` / `capability_snapshot_resolver` factory for the Gate-10 shape

`build_production_authority_generation_resolver` (`.1R.15.4`, N-15-3-2)
exists **for Gate 9** and returns `{principal_generation,
credential_generation, approval_generation}` (three keys). Gate 10 needs the
equivalent **plus** the `lifecycle_generation` / `consumption_generation`
re-derivation and a `capability_snapshot_resolver` that reads
`runtime_introspection` (§13). No such Gate-10 factory exists. `grep` for
`capability_snapshot_resolver` / `build_production.*capability` in
`src/pcae/` returns only the Gate-9 DI parameter and its structural guard —
**tests supply their own** (Gate 9 is structurally unreachable, so it never
mattered). **N-16-1 is a Slice A implementation prerequisite, not a blocker
for this planning phase** (analogous to how N-15-3-2 was folded into
`.1R.15.4`). Slice A (`.1R.17`) MUST wire a production
`build_gate10_authority_generation_resolver` + a production
`build_gate10_capability_snapshot_resolver` reading the canonical
`runtime_introspection` constants, and SHOULD re-express the Gate-9
resolver in terms of it (no Gate-9 behaviour change; contract-neutral
refactor deferred to Slice A's own IV to confirm).

---

## 12. Post-consumption drift semantics (phase prompt §13) — central

Gate-10 behaviour when authority changes **after Gate 9 consumed it but
before Gate 10 attempts the first effect**:

| Drift | Detected by | Gate-10 eligibility | Consumption record |
|---|---|---|---|
| principal revoked / disabled | `principal_generation` mismatch (§11); `revalidate_validated_authority_projection` re-run (`validate_approval` → principal currentness) | **INVALIDATED — no effect** | unchanged (create-only, immutable) |
| credential revoked / disabled | `credential_generation` mismatch; `validate_approval` credential currentness | **INVALIDATED** | unchanged |
| approval currentness change (record replaced / removed / tampered) | `approval_generation` mismatch; `approval_store.load` raises / `None` → resolver raises → fail closed | **INVALIDATED** | unchanged |
| approval wall-clock expiry | `validate_approval` step-9 expiry verdict against Gate-10-entry `authority_current_time` | **INVALIDATED** | unchanged |
| lifecycle / proof state change (successor event, terminal `EXPIRED`/`REVOKED`/`REJECTED`, fork) | `lifecycle_generation` mismatch; `resolve_canonical_chain` raises on a fork → fail closed | **INVALIDATED** | unchanged |
| runtime capability change (anything other than `Observed/observe/unavailable`) | `_runtime_execution_unavailable`-shape check on the fresh capability snapshot (§13) | **INVALIDATED — no effect** (a runtime that *could* now act is exactly the case Gate 9's check exists to prevent; Gate 10 re-applies it) — this is the one case where a *positive* capability is still a **hard stop**, because a positive capability with drifted authority must never dispatch | unchanged |
| containment / effect-plan change (executable hash, argv, cwd, env, descriptor/config, network/credential posture) | `containment_evidence_digest` recomputation mismatch (§16); executable re-hash mismatch (§17) | **INVALIDATED** | unchanged |
| PB decision / RE decision no longer current (policy version drift, RE expiry) | `pb_binding` / `runtime_enforcement_binding` byte-compare + RE `expires_at` vs entry time; **advisory only** `policy_drift_requires_fresh_pb_re_evaluation` (never a positive basis) | RE expiry / verdict-not-ALLOW → **INVALIDATED**; PB policy drift → advisory, re-entry to Gate 6 is the fix, not a Gate-10 bypass | unchanged |

**Consumption does NOT guarantee future execution.** RDGO §17 crash-state
table row `DISPATCH_ATTEMPTED`: "None proven yet / No automatic retry".
Every drift above is a fail-closed pre-effect rejection.

---

## 13. Runtime capability final revalidation (phase prompt §18)

**Canonical capability source (frozen F-G10-6):** the
`pcae.core.runtime_introspection` module — constants
`CURRENT_RUNTIME_STATE = "Observed"`, `CURRENT_MAXIMUM_PLUGIN_CAPABILITY =
"observe"`, `EXECUTION_AVAILABILITY = "unavailable"`, surfaced through
`get_health()` → `HealthInfo{current_runtime_state,
current_maximum_plugin_capability, execution_availability, runtime_status,
registry_status, plugin_count, capability_count}`. This is the **same shape**
`runtime_dispatch_gate9._runtime_execution_unavailable` already checks
(a dict with `current_runtime_state` / `current_maximum_plugin_capability` /
`execution_availability`).

**Frozen F-G10-7.** Gate 10 SHALL re-read the current capability snapshot
**inside its own pre-effect battery, immediately before minting the
envelope**, through a trusted production
`build_gate10_capability_snapshot_resolver` (N-16-1), and fail closed unless
**all** hold:

```
current_runtime_state          == "Observed"
current_maximum_plugin_capability == "observe"
execution_availability          == "unavailable"
```

i.e. **`Observed / observe / unavailable` → Gate 10 CANNOT perform the
effect.** Gate-7's earlier decision is **not** trusted indefinitely (RDGO
§15 "Runtime Enforcement has no cache validity across … policy change";
§8 "Gate 7 … revalidate … using … the PB decision … as inputs").

This is the structural hard stop that keeps a future Gate-10 coordinator
**non-effecting on every reachable path today** — identical to the reason
`run_gate9_atomic_authority_consumption` is safe to have shipped (§23).

---

## 14. Consumed authority stays consumed (phase prompt §14)

**Frozen F-G10-8.** `post-consumption drift != authority becomes
unconsumed`. If Gate 10 rejects after Gate 9 already consumed authority:

- the `consumption.json` record **remains durable and unchanged**
  (`RuntimeInvocationAuthorityConsumptionStore` is create-only; HPAC-REQ-100;
  there is no update / delete primitive);
- the approval, proof, presentation, and challenge **are not restored** —
  they were consumed *together* by the single Gate-9 write (`.1R.14` §11);
- the RIHAC repository approval store was never mutated (HPAC-REQ-102), but
  the one-shot `attempt_limit=1` is spent for that `attempt_id` (RDGO §10a
  "once gate 9 durably records `dispatch_attempted` for a given `attempt_id`,
  that attempt is consumed");
- the human MAY need to authorize a **new invocation** — a fresh
  `invocation_id` + fresh `attempt_id` (new gate-2 pass) + fresh approval +
  fresh proof — for any further attempt (RDGO §18; RPAC-REQ-072; §15).

There is **no consumption rollback** (§28; RDGO §18 — the presence of one
valid HPAC §41 consumption record rejects replay).

---

## 15. No automatic retry from consumed authority (phase prompt §15)

**Frozen F-G10-9.** `consumed authority + Gate-10 eligibility failure → NO
automatic authority restoration or reuse.` Three distinct cases:

| Case | State (RDGO §17) | Retry from the same consumed authority? | New human approval required? |
|---|---|---|---|
| **eligibility failure BEFORE any effect** (any §6–§13 check fails; no `adapter.dispatch()` call made) | `DISPATCH_NOT_STARTED` iff trusted evidence proves gate 10 never began (mirror shows no `EFFECT_ATTEMPT_STARTED`); else `DISPATCH_UNCERTAIN` | **No** | **Yes** — fresh `invocation_id`/`attempt_id`/approval/proof (RDGO §18) |
| **effect-attempt failure with CONFIRMED non-delivery** (adapter reports it could not establish the effect boundary — `dispatch_error`, RPAC-REQ-073; RPAC-REQ-071 "transient transport failure with confirmed non-delivery") | `DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER` (adapter's own confirmed-non-acceptance evidence) | **No** — RPAC-REQ-072 "every retry requires a new attempt ID, fresh capability/status, fresh PB and RE decisions, and human authorization when the prior approval's attempt limit/expiry does not cover it" — and `attempt_limit` is always 1 | **Yes** |
| **effect result UNCERTAIN** (spawn API ambiguous, provider timeout after send, adapter crash after dispatch) | `DISPATCH_UNCERTAIN` | **Never** (RPAC-REQ-071 "unknown delivery … ambiguous process termination SHALL NOT retry automatically") | **Yes**, and a **human decision** on whether a new attempt is even safe (RDGO §17: "fresh human decision/approval for any new attempt") |

The `idempotency_key` alone **never** authorizes redispatch (RDGO §10a).

---

## 16. Final containment / effect-plan read-back (phase prompt §16, §21)

Gate 8 already commits the complete established launch environment into a
single `containment_evidence_digest` (RDGO §9(b), three-layer model) and
Gate 9 independently recomputes it and fails closed on mismatch (§9(c)).
Gate 10's `Gate8Result` is **ephemeral, non-serializable, and gone after a
restart** — so Gate 10 cannot "trust a stale `Gate8Result`" even if it
wanted to.

**Frozen F-G10-10 — minimal contract-consistent read-back.** Gate 10 SHALL,
at entry, re-establish the exact effect Gate 8 validated and Gate 9
consumed, and verify against the **durable** `consumption.json`:

| Item | Source of truth | Gate-10 action |
|---|---|---|
| effect-plan digest | `dispatch_binding` / recomputed | re-resolve the descriptor/config; re-assemble the `Gate8EffectPlan` from descriptor/config (never caller); recompute `effect_plan_digest`; compare |
| containment-evidence digest | `dispatch_binding.containment_evidence_ref.digest` | re-run the Gate-8 containment establishment (three-layer) over freshly re-resolved inputs; require the recomputed `containment_evidence_digest` to equal the durable one (mirrors `runtime_dispatch_gate9.py` step 8 exactly) |
| executable identity | `target_binding.executable_identity_digest` | §17 (re-stat/re-hash) |
| argv / cwd / environment allowlist | inside `containment_evidence_digest` (layer b commits working-directory + environment-value bytes) | covered by the digest recomputation — no separate reference diff (RDGO §9 last ¶) |
| descriptor / config digest | `target_binding.descriptor_digest` / `.target_config_digest` | re-resolve; compare |
| runtime target | `target_binding.runtime_target_id` | compare to the live request |
| containment profile (child-process policy, resource/time/supervision refs) | inside `effect_plan_digest` | covered by digest recomputation |
| network / credential / supervision state | `Gate8EffectPlan.network_denied is True`, `.credentials_required is False` | re-assert both; **any credential requirement → fail closed** (§43) |

**Decision (phase prompt §21): Gate 10 does NOT re-run Gate 8 as a policy
decision; it re-runs the Gate-8 *containment establishment* mechanism to
recompute the evidence digest and compares against the frozen durable value
— "recomputes containment evidence directly" + "reads a canonical effect
snapshot".** This is the exact pattern Gate 9 already uses
(`run_gate8_process_containment` re-invocation + four-digest equality). No
new mechanism is invented; no stale `Gate8Result` is trusted.

---

## 17. Executable identity at the effect boundary (phase prompt §17)

RDGO §15 TOCTOU table, row "Adapter executable identity": snapshot-bound
`No` (descriptor-pinned, not approval-bound); "Recheck before dispatch:
**Yes, exact hash before spawn**"; failure "No dispatch; repair/reselect
target; fresh late-gate decisions".

Analyse the interval `Gate 9 consumed → time passes → executable file
changes → Gate 10 dispatch`: the executable is a filesystem object outside
PCAE's control; between Gate 9's `executable_identity_digest` capture and
Gate 10's spawn it may be replaced, patched, or removed.

**Frozen F-G10-11.** Gate 10's final read-back is **mandatory** and SHALL,
**immediately before** the `adapter.dispatch()` call (after the envelope is
minted, with no intervening effectful I/O), re-`stat` and re-`sha256` the
exact resolved executable and require the hash to equal
`consumption.json.target_binding.executable_identity_digest`. Drift /
absence / permission change / symlink → **fail closed, no effect**
(`gate10_executable_identity_drift`). Installation and current local
availability are re-confirmed at the same point (RDGO §9).

---

## 18. POL-005 relationship (phase prompt §19)

**POL-005 (`ExecutionDisabledRule`) remains hard DENY upstream at Gate 6**
(`permission_broker_foundation.py:695`, `policy_id = "POL-005"`, universal,
denies every truthful non-simulation `runtime_dispatch`). PBRD §12: it is
"unchanged in production by this freeze".

**Frozen F-G10-12.** Gate 10 SHALL:

- **trust the durable Gate-6 lineage / decision** — byte-compare
  `consumption.json.pb_binding` (`request_digest`, `decision_digest`,
  `decision`, `policy_version`, `causing_policy_ids`, `matched_no_go_ids`)
  against the frozen record; require `decision == "ALLOW"`;
- **independently assert** that the consumed lineage represents a valid
  prior permission decision — the record exists only because Gate 6 ALLOWed
  (which today is impossible for a truthful non-simulation request: POL-005
  DENYs), and the digest chain is inside `record_digest`;
- **NOT re-run PB policy** (RDGO §7/§8/§15 — Gate 6 owns PB policy
  evaluation exclusively; `.1R.15.5` §6: `grep evaluate_pb_policy` across
  gate7/gate9 → zero hits). A stale `policy_version` detected after Gate 6
  is resolved by **re-entering Gate 6**, never by Gate 10; Gate 10 MAY
  surface `policy_drift_requires_fresh_pb_re_evaluation` as an **advisory
  reason only** — never a licence to skip a check, never a positive basis;
- **NOT invent another PB policy evaluation layer.**

Trusted consumed authority does **not** override POL-005 (§54).

---

## 19. Runtime Enforcement relationship (phase prompt §20)

**Frozen F-G10-13.** Gate 10 re-checks **from Gate 7** (durable, byte-compare
against `consumption.json.runtime_enforcement_binding`): `decision_id`,
`decision_digest`, `verdict` (must be `ALLOW` — Gate 7 emits no
`HUMAN_REVIEW`), `expires_at` (must be in the future at Gate-10 entry —
RDGO §8 "single-attempt, expiring"), `evaluated_input_digest`.

Gate 10 re-reads **from current runtime capability** (not Gate 7's snapshot):
execution availability (§13).

`matched_no_go_ids` is a **per-decision diagnostic projection, not an
authority input** (RDGO §8; `.1R.15.1` §19; RE No-Go Registry schema 1.1
"Enforcement class" column — `matched_no_go_ids` scopes Gate-7's *sole
source* claim to the per-decision subset). Gate 10 SHALL NOT treat
`matched_no_go_ids` as authority or as an allow/deny input.

---

## 20. Dispatch-attempt semantics (phase prompt §26)

Two distinct linearization points, deliberately not conflated:

| Term | Linearization point | Where recorded | Meaning |
|---|---|---|---|
| **`dispatch_attempted`** (the durable authority-consumption marker) | Gate 9's per-`proof_id` `write_atomic_create_only` (`O_EXCL` temp sibling + atomic link-if-absent) | `consumption.json.dispatch_binding.state` (immutable) | "authority for this `attempt_id` is spent; at-most-once guard armed" — **NOT** "the adapter was invoked" |
| **`effect_attempt_started`** (the dispatch-attempt-lifecycle marker) | the instant the mirror record transitions `PREPARED → EFFECT_ATTEMPT_STARTED`, **immediately before** `adapter.dispatch(envelope)` | RPAC-REQ-067 `RuntimeInvocationRecord` (repository-side, non-authoritative, append-only) | "PCAE is about to cross / has crossed the effect boundary for this attempt" |

**Frozen F-G10-14.** `dispatch attempted != effect succeeded`
(RDGO §0 wall `dispatch completion != accepted change`; §11 "A dispatch call
or receipt does not prove completion"; §1 row 10 "one process-spawn/dispatch
receipt **or uncertain/failure state**"). Any ambiguity after entry to
Gate 10 is `DISPATCH_UNCERTAIN` until stronger evidence exists (RDGO §11).

The "effect attempted" observation is written **before** the adapter call
(write-before-effect — §22 of this doc's §32 analysis) so that a crash
between the write and the call, or during the call, is recoverable as
`DISPATCH_UNCERTAIN` rather than as a silent "never happened".

---

## 21. Failure-before-effect semantics (phase prompt §27)

**Frozen F-G10-15.** If any Gate-10 pre-effect check (§6–§19) fails **before
`adapter.dispatch()` is called**:

- **no effect** — the adapter is never invoked; the mirror record shows
  `PREPARED` (or is never created) with no `EFFECT_ATTEMPT_STARTED`;
- **consumed authority remains consumed** (§14; `consumption.json`
  untouched);
- a **durable reason** is recorded on the mirror record
  (`gate10_pre_effect_rejected:<reason_id>`) — the fail-closed reason ids
  mirror the Gate-9 style (`gate10_untrusted_gate9_result`,
  `gate10_gate9_status_not_consumed`,
  `gate10_consumption_record_read_back_failed`,
  `gate10_consumption_record_generation_snapshot_absent`,
  `gate10_lineage_binding_mismatch`,
  `gate10_authority_generation_drift:<source>`,
  `gate10_stale_validated_authority_projection`,
  `gate10_runtime_capability_not_unavailable`,
  `gate10_adapter_not_registered`,
  `gate10_containment_evidence_recomputation_mismatch`,
  `gate10_executable_identity_drift`,
  `gate10_re_decision_expired`, `gate10_pb_lineage_not_allow`,
  `gate10_effect_plan_requires_credentials`);
- **no automatic replay** unless explicitly authorized (a fresh human
  approval — §15).

---

## 22. Failure-at-effect-boundary semantics + write-before/after decision (phase prompt §28, §32, §33)

### 22.1 The three crash scenarios (RDGO §17, RPAC-REQ-068)

| Scenario | What is durable | Restart determination | Retry |
|---|---|---|---|
| **crash before effect** (after Gate 9 commit, before `adapter.dispatch`) | `consumption.json` present; mirror shows no `EFFECT_ATTEMPT_STARTED` | `resolve(proof_id)` → record → **consumed**; mirror proves gate 10 did not begin → `DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER` (RDGO §17) | none from this authority; fresh invocation/approval (§15) |
| **crash during effect** (`adapter.dispatch` in flight; spawn API ambiguous; provider timeout after send) | `consumption.json` present; mirror shows `EFFECT_ATTEMPT_STARTED`, no terminal | **`DISPATCH_UNCERTAIN`** (RDGO §17) — fail closed, **never blindly retry** | never automatic; human decision required |
| **crash after effect, before the mirror's terminal write** | `consumption.json` present; mirror shows `EFFECT_ATTEMPT_STARTED`, no `RECEIPT_CAPTURED` | indistinguishable from "crash during effect" → **`DISPATCH_UNCERTAIN`** — the architecture MUST represent "effect outcome uncertain" and prohibit automatic retry (RDGO §17 "absence of a result is never proof that dispatch did not occur") | never automatic |

### 22.2 Model A vs B vs C (phase prompt §32) — decision

- **Model A — durably write `EFFECT_ATTEMPT_STARTED` before the external
  effect.** Pro: a crash after the write prevents a duplicate retry (the
  next process sees `EFFECT_ATTEMPT_STARTED` and refuses). Con: the mirror
  may say "attempted" even if the external call never actually issued.
- **Model B — effect first, durable record after.** Pro: the record
  reflects the actual call path. Con: a crash after the effect but before
  the record permits a **duplicate retry** — unsafe.
- **Model C — two-state lifecycle** (`PREPARED → {EFFECT_ATTEMPT_STARTED} →
  {RECEIPT_CAPTURED | DISPATCH_UNCERTAIN | DISPATCH_NOT_STARTED}`).

**Selected: Model A combined with Model C.** Rationale (derived, not by
convenience):

1. **Security posture prefers over-counting attempts to under-counting
   effects.** Model A's failure mode (a false "attempted" after a crash) is
   *fail-closed* — the attempt is treated as `DISPATCH_UNCERTAIN` and a
   fresh human approval is required, wasting one one-shot authority at
   worst. Model B's failure mode (a duplicate effect after a crash) is
   *fail-open* — an external process runs twice. RDGO §17 / RPAC-REQ-068
   ("record `ambiguous_outcome` and SHALL NOT automatically redispatch")
   mandate the Model-A posture.
2. **Consistency with the existing contract.** The authoritative
   durable-before-effect commit is *already* write-before-effect at Gate 9
   (RDGO §1 row 9). Model A on the mirror is the same discipline one layer
   out.
3. **Two-state (Model C) is required** because a single "attempted" flag
   cannot distinguish "about to call" from "call returned uncertain" from
   "receipt captured" — RPAC-REQ-040 "State transitions SHALL be
   append-only observations … SHALL NOT be collapsed into one success flag".

### 22.3 Gate-10 canonical transaction model (phase prompt §33)

**The mirror record is a durable, append-only, non-authoritative
`RuntimeInvocationRecord` (RPAC-REQ-067) — NOT a second canonical authority
truth.** The authoritative one-shot record stays `consumption.json`
(create-only, immutable, HPAC-canonical). The mirror carries the
state-transition log; its transitions are authoritative-*transitions*
(the trusted Gate-10 coordinator writes them; the adapter never does —
RPAC-REQ-034), append-only, each an observation with a timestamp and the
prior-state hash. Minimum states: `PREPARED`, `EFFECT_ATTEMPT_STARTED`,
`RECEIPT_CAPTURED`, `DISPATCH_UNCERTAIN`, `DISPATCH_NOT_STARTED`. No mutable
state machine that can go backwards; `DISPATCH_UNCERTAIN` and
`DISPATCH_NOT_STARTED` are terminal.

---

## 23. Current positive-path reachability (phase prompt §23)

**Answer: NO. No positive production Gate-10 path exists today.** Each of
the following **independently** blocks it (re-derived from primary source):

| Blocker | Evidence |
|---|---|
| deterministic HPAC remains **NON_REAL** | `validate_approval:~1114` hard stop (`.1R.11` §7.4; `.1R.15.1` §21) — `run_gate5` never returns a `Gate5Result` on any production-obtainable path |
| real Gate 7 returns **DENY** | `runtime_dispatch_gate9.py` module docstring: "the real Gate-7 coordinator always returns `Gate7Result(decision="DENY")`" → `run_gate9` structurally unreachable → no `Gate9Result(status="consumed")` can be produced → Gate 10 has no valid input |
| runtime capability **unavailable** | `runtime_introspection` constants; `pcae runtime inspect` (§2); F-G10-7 hard stop |
| no registered real adapter | `RuntimeRegistry` empty; `RuntimeAdapterResolver` has no callable instance for a real target; only `MockDryRuntimeAdapter` (`execution_effect="none"`, `simulation_only=True`) |
| POL-005 hard DENY at Gate 6 | `ExecutionDisabledRule`; PBRD §12 (eleven unmet conditions) |
| no protected human-approval UI | `.1R.15.1` §21 |
| no real FIDO2 / WebAuthn / CTAP | `.1R.15.1` §21; RPAC-REQ-084 (credential blocker) |

**A positive Gate-10 path is not fabricated.** Any "positive" Gate-10
behaviour is reachable **only** through a clearly-labelled test-only
substitution of upstream provenance predicates + a `tmp_path` store, exactly
as Gates 5–9 are exercised today (`runtime_dispatch_gate9.py` docstring "No
positive production Gate-9 path today"; `.1R.15.1` §21).

---

## 24. Gate-10 structural implementation scope (phase prompt §24, §25)

### 24.1 What may be implemented now without effect

| Component | Effect? | Safe now? | Slice |
|---|---|---|---|
| Gate-10 pre-effect eligibility battery (F-G10-1 … F-G10-13) | none | **Yes** — pure control-plane reads + digest comparisons; identical risk profile to Gate 9 | A (`.1R.17`) |
| Final read-back coordinator (durable `consumption.json` + generation-state + containment recomputation) | none | **Yes** | A |
| DispatchEnvelope builder (RPAC-REQ-029) | none — it is a data structure | **Yes** | A |
| production `build_gate10_authority_generation_resolver` + `build_gate10_capability_snapshot_resolver` (N-16-1) | none | **Yes** | A |
| dispatch-attempt durable lifecycle / mirror `RuntimeInvocationRecord` (RPAC-REQ-067/068/069/070; states, crash/restart determination, `DISPATCH_UNCERTAIN`) + the two 3S.2.1 MUST-FIX repairs + runtime-inspect repair (§7) | none — records only, `tmp_path` in tests | **Yes** | B (`.1R.19`) |
| the single `adapter.dispatch(envelope)` **call site** | **YES — first external effect** | **No** | C (no phase ID) |
| a real (non-mock) `RuntimeAdapter` implementation | **YES** | **No** | C |

### 24.2 Naming decision (phase prompt §24 last ¶, §25)

RDGO §11 defines Gate 10 *specifically* as the first external effect, and
lists the six-item read-back as the "Gate-10 forward read-back
prerequisite" — i.e. **the read-back battery is already inside Gate 10, not
a new gate**. Therefore:

- **Do NOT invent a "Gate 9.5".** No contract evolution is required; the
  battery is contract-consistent Gate-10 pre-effect validation (RDGO §11
  items 1–6 verbatim).
- **Slice A implements a `run_gate10_pre_effect_eligibility` coordinator**
  that performs RDGO §11 items 1–6 + §16/§17 read-back + mints and returns
  the `DispatchEnvelope` (or a structured negative), and **contains no
  `adapter.dispatch()` call site at all** (a stronger property than "the
  call is unreachable" — it structurally cannot occur; matches phase-prompt
  §24's enumeration "…effect-envelope builder; **no actual adapter call**").
- The **module name and phase title deliberately say "Pre-Effect
  Eligibility and Dispatch-Envelope"**, not "Gate 10", to make explicit
  that the effect itself (the `adapter.dispatch()` call, Slice C) is a
  separate, unbuilt, human-authority-gated boundary. Slice C adds the call
  site and, at that point, the module *becomes* the full Gate-10
  coordinator.

This is the "split structural Gate-10 eligibility and actual effect
dispatch into separate phases" option (phase prompt §22 Option C),
combined with §22 Option A ("a structural Gate-10 implementation may safely
exist … but the current positive production Gate-10 path remains
unreachable").

---

## 25. Idempotency strategy (phase prompt §29, §30, §50)

### 25.1 Exactly-once vs at-most-once (phase prompt §29)

**PCAE can guarantee only: at-most-once *dispatch attempt* with fail-closed
uncertainty.** It cannot promise exactly-once execution for an arbitrary
external system (RDGO §17 "Exactly-once execution is not promised.
At-most-once attempt is enforced where durable state proves it; otherwise
uncertainty is explicit").

- **at-most-once *authority consumption* per `proof_id`** — guaranteed by
  the Gate-9 `O_EXCL` create-only primitive (a second create →
  `HPACDuplicateError` → deterministic `already_consumed`).
- **at-most-once *effect attempt* per `attempt_id`** — enforced by the
  mirror's `EFFECT_ATTEMPT_STARTED` write-before-effect: a second Gate-10
  entry for the same `attempt_id` sees the marker and refuses
  (`gate10_attempt_id_already_entered`).
- **exactly-once *effect*** — **NOT achievable generically**; when a crash
  leaves the outcome `DISPATCH_UNCERTAIN`, PCAE fails closed and requires a
  human decision.

Likely safer target adopted: **at-most-once dispatch attempt with durable
uncertainty**, unless a specific adapter provides a provider-side
idempotency key (§25.2).

### 25.2 External idempotency keys (phase prompt §30)

- **Current adapters:** `MockDryRuntimeAdapter.dispatch()` returns
  `DispatchReceipt(invocation_id, attempt_id, accepted, simulation_only)` —
  **no idempotency-key parameter, no provider idempotency semantics**. No
  real adapter exists.
- **RPAC-REQ-065** defines `idempotency_key` = SHA-256 of canonical
  versioned request content (excluding timestamps / attempt-specific
  observations). **RPAC-REQ-064** defines `attempt_id` = unique per try.
- **Binding recommendation** (for a future adapter that *does* support a
  provider idempotency token): pass **`attempt_id`** as the external
  idempotency token — it is unique per concrete try, so a provider that
  de-dupes on it collapses a PCAE-level retry that reused the token (which
  PCAE never does — every retry mints a new `attempt_id`) and, more
  importantly, lets a provider recognise a network-level duplicate of the
  *same* try. `idempotency_key` identifies the logical operation for
  PCAE-side replay detection (RPAC-REQ-070's candidate identity =
  `f(invocation_id, attempt_id, result_digest)`), not for the provider.
- **Do not assume provider semantics** — each future adapter's descriptor
  declares whether it supports an idempotency token, and the Gate-10
  coordinator passes it only when declared.

### 25.3 Attempt identity relationships (phase prompt §50)

| Identifier | Minted | Scope | Stable across |
|---|---|---|---|
| `invocation_id` | Gate 2 (crypto-random, `.1R` `RuntimeDispatchIdentity`) | one logical invocation | its attempts |
| `attempt_id` | Gate 2 per try (`att-<32hex>`) | exactly one concrete dispatch try | gates 2–11 unchanged (RDGO §10a) |
| `idempotency_key` | Gate 2 (SHA-256 canonical content) | one logical dispatch operation's content | genuine retries of unchanged content (RPAC-REQ-072) |
| Gate-9 durable `attempt_id` | recorded at Gate 9 item 1 | the consumed attempt | — |
| future dispatch-attempt / mirror record id | Slice B — recommend `derive_intake_candidate_id`-style `f(invocation_id, attempt_id)` | the mirror record | — |
| provider / process request id | observed from the adapter's `DispatchReceipt` | one external call | — |

No ambiguous retries: every retry mints a **new `attempt_id`** through a
fresh Gate-2 pass (RDGO §18; §10a); `idempotency_key` stays identical only
when the canonical content is unchanged, and never by itself authorizes
redispatch.

---

## 26. Effect receipt semantics (phase prompt §37, §38)

- **Does the adapter return a receipt?** Yes — `RuntimeAdapter.dispatch()`
  returns a `DispatchReceipt` (RPAC-REQ-029/031). The current mock's is
  `DispatchReceipt(invocation_id, attempt_id, accepted: bool,
  simulation_only: bool = True)`.
- **Frozen F-G10-16 — `receipt = evidence of effect/result, NOT
  permission/authority`.** A receipt MAY establish: invocation accepted,
  process id, provider request id, exit/result status. It SHALL NOT
  authorize another effect (RPAC-REQ-036; RDGO §19 "Adapter cannot
  self-authorize"; §0 wall `dispatch completion != accepted change`). A
  receipt with `accepted=True` is **not** proof of completion (RDGO §11).
- **`Gate10Result` / `DispatchReceipt` internal type (if Slice C needs
  one):** it MUST follow the Gate5–9Result pattern exactly — exact-object
  registry provenance (`_GATE10_RESULTS` id-keyed set),
  `is_gate10_result` = provenance only (never shape / isinstance / fields),
  non-serializable (`__reduce__` raises), non-subclassable, identity-only
  `==`/`hash`, `_seal` guard. `status ∈ {dispatched, dispatch_uncertain,
  dispatch_not_started}`. **Not durable, not transferable** — on a restart
  it is gone and the durable truth is `consumption.json` (authority) +
  the mirror `RuntimeInvocationRecord` (attempt lifecycle). **Do not repeat
  the "object shape = trust" mistake** (the B1 defect class;
  `runtime_dispatch_gate9.py` F7 boundary note).

---

## 27. Adapter ownership and inventory (phase prompt §39, §40, §41, §42, §44)

### 27.1 Ownership (phase prompt §39)

**The future Gate-10 coordinator owns:** the pre-effect battery, the
`DispatchEnvelope` mint, the mirror-record transitions, and **the single
`adapter.dispatch()` call site**. **The selected `RuntimeAdapter`
implementation owns:** process/API mechanics, capture, cancellation,
timeout enforcement, normalized transport results — **under
kernel-supplied constraints** (RPAC-REQ-034). Neither **Shell Gate** (Gate
8 — owns *how* a local command is constructed/launched, i.e. containment;
RPAC-REQ-047) nor **`backend_invocations.py`** (legacy; RPAC-REQ-097
"historical execution surface … SHALL NOT be grandfathered as alternate
dispatch authorities") owns dispatch. **No duplicate execution logic** —
exactly one call site, in the Gate-10 coordinator.

### 27.2 Runtime adapter inventory (phase prompt §40)

| Adapter / component | Class | State | Activate? |
|---|---|---|---|
| `MockDryRuntimeAdapter` (`mock_runtime_adapter.py`) | mock/test-only | `simulation_only=True`, `execution_effect="none"`, fixed local fixtures, no subprocess/network | **No** |
| `RuntimeAdapter` Protocol (`runtime_adapter.py`) | interface only | five frozen operations (`describe`/`preflight`/`dispatch`/`collect`/`cancel`); **no real implementation** | **No** |
| `simulate_invocation` coordinator (`runtime_adapter.py`) | RPAC mock-v1 coordinator | runs the mock-v1 gate sequence; **not wired to the RDGO Gate 5–11 chain** | **No** |
| `backend_invocations.py` (Phase 94B) | legacy | simulation/validation only; RPAC-REQ-097 historical | **No** |
| `delivery_receipt.py` (Phase 134E.7) | external-delivery receipt model | "not yet active lifecycle authority"; unrelated to runtime dispatch | **No** |
| `RuntimeRegistry` | canonical catalog | **empty** (0 plugins / 0 capabilities); valid empty state (RPAC-REQ-055) | **No** |

**No real-effect adapter exists anywhere. This phase activates none.**

### 27.3 Subprocess effect path (phase prompt §41)

For a `local_cli` first-effect target (RPAC-REQ-057, RPAC-REQ-095):
argv/cwd/env transfer from the `Gate8EffectPlan` (kernel-assembled, never
caller); containment handoff = the established bounded process environment
(Gate 8 layer b, re-attested by Gate 10 §16); finite timeout
(`time_limit_ref`); process-group / tree ownership; child-process
prohibition (`child_process_policy`); signal handling / termination
escalation; result capture bounded (RPAC-REQ-057). **Planning only —
`descriptor.execution_effect` for the first target is `local_process`; the
`os.posix_spawn`-class call lives in the Slice-C adapter implementation, not
the Gate-10 coordinator.**

### 27.4 Provider / network effect path (phase prompt §42)

If a future `api_provider` target exists (`execution_effect ==
"remote_request"`): provider/endpoint identity, TLS/egress policy, opaque
credential reference (RPAC-REQ-058/084 — **blocked**, no secret resolver),
finite connection + total timeouts, rate-limit handling, ambiguous-delivery
handling (RPAC-REQ-059). **Do not assume subprocess semantics apply.** The
common Gate-10 abstraction is the `DispatchEnvelope` + the five-operation
`RuntimeAdapter` Protocol; per-adapter behaviour lives behind `dispatch()`.
The first effect SHOULD be `local_cli`, not provider (RPAC-REQ-095).

### 27.5 Gate-10 capability check vs adapter readiness (phase prompt §44)

**Four independent conditions, none collapsed:**

1. **PCAE global execution capability** — `runtime_introspection`
   `execution_availability == "unavailable"` today → hard stop (§13).
2. **Selected adapter availability** — a callable instance registered in
   `RuntimeAdapterResolver` for the exact `runtime_target_id`, with matching
   descriptor digest (RPAC-REQ-053); none today.
3. **Backend / target health** — `RuntimeStatus.health` from the adapter's
   status probe (RPAC-REQ-015); `simulation_ready` is a distinct
   non-collapsing term (RPAC-REQ-017).
4. **Invocation-specific eligibility** — the full §6–§19 battery for *this*
   `proof_id` / `attempt_id`.

All four MUST hold for the effect. Gate 10 checks all four; today condition
1 alone is dispositive.

---

## 28. Credential boundary (phase prompt §43)

**Frozen F-G10-17 — `authorization to execute != blanket credential
authority`.** Gate 10 itself SHALL NOT access credentials. The first effect
MUST be a **no-credential local process** (`Gate8EffectPlan.credentials_required
is False`; RDGO §9 "confirm … no credential access is required"). RPAC-REQ-058
(a local adapter SHALL NOT inherit the full PCAE environment; credentials
resolved just-in-time by a future secret resolver, exposed only to the
narrow child, omitted from records, redacted from output) and RPAC-REQ-084
("PCAE has no adequate general credential-reference/resolution
implementation today; that is an explicit blocker for a real authenticated
adapter") mean credential-backed effects require a **separate governed
credential boundary** — out of scope for this phase and for Slices A/B/C.

---

## 29. Threat model (phase prompt §47)

**F7 carried verbatim; NOT broadened.** Same-process arbitrary Python code
execution remains **outside** current protection (`runtime_dispatch_gate9.py`
F7 boundary note; `.1R.15.1` §4). A future `_GATE10_RESULTS` identity
registry and the Gate-10 consumption of upstream trusted objects would
resist caller-supplied **data** forgery (reconstruction, copy, serialized
clone, duck-typed lookalike, a schema-valid `consumption.json` planted
outside the authoritative writer) — they do **not** resist arbitrary
same-process code execution. No UID / username / process-ownership / stdio /
Git identity / PCAE session identity / producer identity is trusted; only
the verified HPAC provenance chain establishes human authentication, only
exact-object registry membership establishes gate-result provenance, only
the store's create-only atomic primitive establishes consumed state, and
only a re-stat/re-hash establishes executable identity at the boundary.
Gate 10 SHALL NOT overclaim process-local provenance as a hardware security
boundary. **A process-isolation / hardening chapter is a separate,
unscheduled, non-prerequisite topic.**

---

## 30. Real FIDO2 / protected UI prerequisite decision (phase prompt §22, §53, §58)

**Question:** May a structural Gate-10 implementation safely exist before
real FIDO2 and real protected approval UI?

**Decision: Option A + Option C.**

- **Option A — Yes**, a structural Gate-10 pre-effect eligibility
  coordinator (Slice A) and the dispatch-attempt durable lifecycle (Slice B)
  may safely exist now. They are pure control-plane, non-effecting, and
  structurally unreachable on any production path (§23) — the exact
  situation under which Gates 5–9 were all implemented and independently
  verified. The current positive production Gate-10 path **remains
  unreachable**.
- **Option C — Split** structural Gate-10 eligibility (Slices A/B) from the
  actual effect dispatch (Slice C) into separate phases. Slice C's
  `adapter.dispatch()` call site is the first external effect and MUST NOT
  be built until real human authority exists.

**Rejected: Option B** ("No, real human authority is required before
implementing the effect *boundary*") — the *boundary definition and the
non-effecting eligibility machinery* do not require real authority; only
the *effect itself* does. Implementing eligibility now is the same
risk-controlled pattern the whole `.1R` gate chain has followed.

### 30.1 Where the Gate-10 architecture additionally ensures a NON_REAL lineage cannot dispatch (phase prompt §53)

Defence in depth — a NON_REAL lineage is blocked at **five** independent
points, not one:

1. Gate 5 — `validate_approval:~1114` NON-REAL hard stop (no `Gate5Result`).
2. Gate 7 — real coordinator returns `DENY` (no `Gate7Result(ALLOW)`).
3. Gate 9 — `revalidate_validated_authority_projection` re-runs
   `validate_approval` inside the boundary → NON-REAL fails closed (no
   `consumption.json`).
4. Gate 10 F-G10-1 / F-G10-13 — `Gate9Result.status == "consumed"` required
   **and** `revalidate_validated_authority_projection` re-run at Gate-10
   entry (§12) → a NON-REAL projection fails closed.
5. Gate 10 F-G10-7 — `execution_availability == "unavailable"` hard stop
   (independent of authority).

### 30.2 Sequencing (phase prompt §58)

Derived (not assumed) safe order:

```
.1R.16  Gate-10 architecture (this phase)
   ->
.1R.17  non-effecting Gate-10 pre-effect eligibility + envelope coordinator + N-16-1 factories   (Slice A)
   ->
.1R.18  independent verification of Slice A
   ->
.1R.19  dispatch-attempt durable lifecycle + mirror RuntimeInvocationRecord + 3S.2.1 MUST-FIX x2 + runtime-inspect repair   (Slice B)
   ->
.1R.20  independent verification of Slice B
   ->
[ SEPARATE TRACK, each its own explicit human authorization, no IDs reserved here ]
   real FIDO2 / WebAuthn / CTAP  (HATP integration into the RDGO chain)
   real protected human-approval UI
   PBRD-001 §12 POL-005 narrow-eligibility rule for the exact local-CLI runtime_dispatch profile + its independent verification
   RPAC-REQ-095 generic fixed-argv external-executable adapter (deterministic non-AI fixture) + supply-chain admission
   runtime capability enablement (Observed -> Approved/Executable transition; a governed, separately verified step)
   ->
Slice C  first concrete effect adapter integration  (the adapter.dispatch() call site added; first external effect)   -- NO PHASE ID
   ->
Slice D  independent end-to-end verification of the first external effect   -- NO PHASE ID
```

The Slices-A/B track and the FIDO2/UI/capability track are **independent up
to Slice C**, which requires **both** complete.

---

## 31. Restart models (phase prompt §45, §46)

### 31.1 Restart after Gate 9 but before Gate 10 (phase prompt §45)

Recovery uses **durable state only** — no in-memory gate result may be
required:

- `consumption.json` (`HPAC-AUTHORITY-CONSUMPTION/2.1`) — `resolve(proof_id)`
  → present → authority **consumed**; the `authority_generation_binding`
  snapshot, `authority_binding`, `target_binding`, `dispatch_binding`
  (effect-plan / containment commitments) are all re-readable;
- the mirror `RuntimeInvocationRecord` — if absent or `PREPARED` with no
  `EFFECT_ATTEMPT_STARTED` → gate 10 did not begin →
  `DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER`; a fresh invocation/approval
  is required for any new attempt (RDGO §18).

A restarted Gate-10 attempt re-runs the **entire** §6–§19 battery from
disk (§11 "This must work after restart").

### 31.2 Restart after a Gate-10 attempt (phase prompt §46)

The durable state that determines the outcome (never process memory):

| Durable signal | Determination |
|---|---|
| `consumption.json` absent | Gate 9 never completed → no attempt; fresh invocation |
| `consumption.json` present, mirror absent / `PREPARED` | consumed, `DISPATCH_NOT_STARTED` → no effect occurred; fresh invocation required |
| mirror `EFFECT_ATTEMPT_STARTED`, no terminal | **`DISPATCH_UNCERTAIN`** → retry **prohibited**; human decision required |
| mirror `RECEIPT_CAPTURED` | result known → Gate 11 intake path; no new attempt |
| mirror `DISPATCH_UNCERTAIN` / `DISPATCH_NOT_STARTED` (terminal) | as recorded; retry prohibited without fresh human approval |

---

## 32. Gate-10 result lineage (phase prompt §51)

**Frozen F-G10-18.** Any future `Gate10Result` / `DispatchReceipt` /
mirror-record terminal state SHALL bind:

- exact `HPAC-AUTHORITY-CONSUMPTION/2.1` `record_digest`;
- `effect_plan_digest`;
- `containment_evidence_digest`;
- `runtime_target_id`;
- `adapter_id` + adapter implementation digest;
- attempt identity (`invocation_id` / `attempt_id` / `idempotency_key` /
  `proof_id` / `approval_id`);
- the observed provider / process request id (when the adapter supplies
  one).

No result / receipt is authority (F-G10-16).

---

## 33. Runtime posture and real-authority hard stops (phase prompt §52, §53, §54)

- **§52** — planning preserves `Observed / observe / unavailable`. Even
  when a structural Gate-10 coordinator exists (Slice A), `execution
  unavailable → no external effect` (F-G10-7). **No automatic capability
  promotion is planned** — the `Observed → Approved/Executable` transition
  is a governed, separately verified step on the FIDO2/UI/capability track
  (§30.2).
- **§53** — a NON_REAL lineage is blocked at five independent points
  (§30.1).
- **§54** — **POL-005 remains hard DENY.** No Gate-10 architecture bypasses
  it. Trusted consumed authority does **not** override policy (F-G10-12).

---

## 34. Defensive validation matrix (phase prompt §55)

Cases to be implemented / verified across Slices A–D (a test in Slice A/B
where the mechanism exists there; a Slice-C/D test where it needs the
effect boundary). Every case fails closed with **no external effect**.

| # | Case | Slice | Mechanism |
|---|---|---|---|
| 1 | trusted `Gate9Result` required | A | `is_gate10_gate9_input` = `is_gate9_result` |
| 2 | `status == "consumed"` required (not `already_consumed`, not provenance) | A | F-G10-1 |
| 3 | copied / forged / reconstructed / pickled / `object.__new__` `Gate9Result` rejected | A | exact-object registry |
| 4 | fresh durable `consumption.json` re-read required | A | F-G10-2 |
| 5 | `/2.0` record rejected for Gate-10 eligibility | A | F-G10-3 |
| 6 | durable `authority_generation_binding` snapshot required (absent → reject) | A | F-G10-3 / F-G10-4 |
| 7 | current principal-generation mismatch rejected | A | F-G10-5 |
| 8 | current credential-generation mismatch rejected | A | F-G10-5 |
| 9 | current approval-generation mismatch (record replaced / removed / tamper) rejected | A | F-G10-5; resolver raises → fail closed |
| 10 | lifecycle / proof generation mismatch (successor / terminal / fork) rejected | A | F-G10-5 |
| 11 | effect-plan digest mismatch rejected | A | F-G10-10 |
| 12 | containment-evidence digest recomputation mismatch rejected | A | F-G10-10 |
| 13 | executable identity drift (re-stat/re-hash) rejected | A | F-G10-11 |
| 14 | cwd / env / descriptor / config / profile drift rejected | A | inside F-G10-10 digests |
| 15 | runtime capability not `unavailable` → rejected | A | F-G10-7 |
| 16 | selected adapter not registered / digest drift → rejected | A | §27.5 cond. 2 |
| 17 | PB lineage invalid / `decision != ALLOW` → rejected | A | F-G10-12 |
| 18 | RE decision expired / `verdict != ALLOW` → rejected | A | F-G10-13 |
| 19 | NON_REAL lineage rejected (5 independent points) | A | §30.1 |
| 20 | `revalidate_validated_authority_projection` re-run at Gate-10 entry; post-Gate-9 revocation/expiry rejected | A | §12 |
| 21 | pre-effect validation failure produces **no effect** | A | F-G10-15 |
| 22 | consumed authority remains consumed after any rejection | A | F-G10-8 (record byte-unchanged) |
| 23 | `idempotency_key` alone does not authorize redispatch | A | F-G10-9 |
| 24 | crash before effect → no effect; `DISPATCH_NOT_STARTED` | B | §22.1 / §31 |
| 25 | crash during effect → `DISPATCH_UNCERTAIN`; no auto-retry | C/D | §22.1 |
| 26 | crash after effect, before terminal mirror write → `DISPATCH_UNCERTAIN`; no auto-retry | C/D | §22.1 |
| 27 | duplicate Gate-10 entry for the same `attempt_id` prohibited | B | mirror `EFFECT_ATTEMPT_STARTED` guard |
| 28 | receipt cannot authorize another effect | C/D | F-G10-16 |
| 29 | restart reads durable state only (no in-memory gate result required) | B | §31 |
| 30 | no raw bearer-token execution; snapshot possession grants nothing | A | F-G10-4 / §29 |
| 31 | first external effect occurs only at Gate 10 (`adapter.dispatch()` single call site) | C/D | §27.1 |
| 32 | `Gate10Result` non-serializable / non-transferable / identity-only | C | F-G10-16 pattern |
| 33 | credential-requiring effect plan rejected | A | F-G10-17 |
| 34 | mock/simulation path never mints real `DISPATCHED`/`COMPLETED` or changes `pcae runtime inspect` | A–D | RPAC-REQ-041/091 |

---

## 35. Gate-10 prerequisite matrix (phase prompt §63) — rebuilt

"Blocks planning" = must be resolved before *this* `.1R.16` can be
authored. "Blocks implementation" = before Slice A/B. "Blocks positive
production path" = before Slice C / real effect.

| # | Prerequisite | Status | Evidence | Blocks planning? | Blocks Slice A/B? | Blocks positive production path? |
|---:|---|---|---|:--:|:--:|:--:|
| 1 | Contract model internally consistent + independently verified (RDGO v3.1 / PBRD v2.1 / HPAC v2.1 / RIASC errata / RE-registry 1.1) | **SATISFIED** | `.1R.15.5` §14 item 1; re-read §2.1 | No | No | No |
| 2 | V-15-1 resolved (Gate-9 serialization atomic to practical limit) | **SATISFIED** | `.1R.15.3` + `.1R.15.5` §7 | No | No | No |
| 3 | Gate-9 semantics normalized (single create-only linearization model) | **SATISFIED** | `.1R.15.5` §7 / §10 | No | No | No |
| 4 | Runtime-capability model frozen (`Observed/observe/unavailable`; same shape Gate 9 & Gate 10 check) | **SATISFIED** | §13; `runtime_introspection.py` | No | No | No |
| 5 | Real human-authority status accurately NON_REAL | **SATISFIED (as a truthful representation)** | `.1R.15.1` §21; §23 | No | No | — |
| 6 | `Gate9Result` success semantics frozen (`status == "consumed"`) | **SATISFIED** | RDGO §11; `.1R.15.5` §6/§16; §6 | No | No | No |
| 7 | Durable consumption read-back + re-validation forward invariant frozen (RDGO §11) | **SATISFIED** | RDGO §11 items 1–6; §8–§13 | No | No | No |
| 8 | No unresolved blocking findings from `.1R.15.2`–`.1R.15.5` | **SATISFIED** | `.1R.15.5` §14 item 8, §18 (two non-blocking: N-15-5-1, N-15-5-2) | No | No | No |
| 9 | The two 3S.2.1 prerequisite repairs (malformed-result; store path-traversal) + runtime-inspect repair, at their required reachability point (PBRD §12 items 9–10) | **NOT SATISFIED / DEFERRED** | §7; 3S.2.1 §62; RDGO §12; PBRD §12 | **No** | **No** (fold into Slice B) | **YES** |
| 10 | Independent verification of the contract normalization (`.1R.15.5`) | **SATISFIED** | `.1R.15.5` (that IV) | No | No | No |
| 11 *(new — N-16-1)* | Production `build_gate10_authority_generation_resolver` + `build_gate10_capability_snapshot_resolver` factories (Gate-10 shape: 5-marker + capability dict) | **NOT SATISFIED** | §11.1 — `grep` shows no such factory; Gate 9 takes DI only | No | **YES (Slice A scope)** | YES |
| 12 *(new — N-16-2)* | Dispatch-attempt durable lifecycle / mirror `RuntimeInvocationRecord` (RPAC-REQ-067/068/069/070) — the durable place a `DISPATCH_UNCERTAIN` / restart outcome lives | **NOT SATISFIED** | §22.3 — `RuntimeInvocationStore` exists for the *dry* path only; no Gate 5–11-wired mirror | No | **YES (Slice B scope)** | YES |
| 13 *(new — N-16-3)* | PBRD-001 §12 POL-005 narrow-eligibility rule for the exact local-CLI `runtime_dispatch` profile + its independent verification (item 4 of the eleven) | **NOT SATISFIED** | PBRD §12 | No | No | **YES** |
| 14 *(new — N-16-4)* | Real, positive, single-attempt Runtime Enforcement gate over the full RDGO v3.1 projection (PBRD §12 item 5) — real Gate 7 currently DENYs | **NOT SATISFIED** | §23; PBRD §12 item 5 | No | No | **YES** |
| 15 *(new — N-16-5)* | Real FIDO2 / WebAuthn / CTAP + protected human-approval UI (PBRD §12 item 3) | **NOT SATISFIED** | `.1R.15.1` §21; RPAC-REQ-084 | No | No | **YES** |
| 16 *(new — N-16-6)* | RPAC-REQ-095 generic fixed-argv external-executable adapter (deterministic non-AI fixture) + supply-chain admission (RPAC-REQ-054/086) | **NOT SATISFIED** | §27.2; RPAC-REQ-095 | No | No | **YES** |
| 17 *(new — N-16-7)* | Runtime capability enablement (`Observed → Approved/Executable`), a governed + separately verified transition | **NOT SATISFIED** | §33; RPAC-REQ-055 | No | No | **YES** |
| 18 *(carried — N-15-5-1)* | PBRD-001 v2.1 duplicate section "4a" — documentation hygiene | **NOT SATISFIED (non-blocking)** | `.1R.15.5` §5/§18 | No | No | No (fold into Slice A doc scope or a micro doc-phase — §37) |

**Item 9 and items 11–17 do not block this planning phase.** Items 11–12
are Slice A/B implementation scope. Items 9, 13–17 are the Slice-C
prerequisite set.

---

## 36. Implementation packaging and phase IDs (phase prompt §56, §57, §64, §65)

### 36.1 Decomposition (phase prompt §56)

| Slice | Content | Effect? | Trust-bearing? |
|---|---|---|---|
| **A** | Gate-10 pre-effect eligibility + dispatch-envelope coordinator (F-G10-1 … F-G10-13, §16, §17); production `build_gate10_authority_generation_resolver` + `build_gate10_capability_snapshot_resolver`; **no `adapter.dispatch()` call site** | none | yes — new eligibility boundary |
| **B** | Dispatch-attempt durable lifecycle: mirror `RuntimeInvocationRecord` (RPAC-REQ-067), state machine + crash/restart determination + `DISPATCH_UNCERTAIN`, idempotency (RPAC-REQ-065/069/070), `EFFECT_ATTEMPT_STARTED` write-before-effect guard; **+ 3S.2.1 MUST-FIX #1 (malformed-result fail-closed) + #2 (store path-traversal sanitisation) + runtime-inspect repair** (item 9) | none | yes — durable attempt truth |
| **C** | First concrete effect adapter integration: the single `adapter.dispatch()` call site added to the coordinator; a real RPAC-REQ-095 fixed-argv external-executable adapter; supply-chain admission | **YES — first external effect** | yes |
| **D** | Independent end-to-end verification of the first external effect | observes only | — |

Do **not** over-bundle the first external effect with all adapter semantics
(RPAC-REQ-095: local-CLI fixed-argv non-AI fixture first; named AI targets
strictly later). Every trust-bearing / effect-bearing slice gets its own
implementation + independent-verification pair.

### 36.2 Frozen phase IDs (phase prompt §57, §65) — repository convention `149O.20L.7O.3W.1R.2B.1R.1.1R.N`

| ID | Title | Scope (one line) | Authorization |
|---|---|---|---|
| `149O.20L.7O.3W.1R.2B.1R.1.1R.16` | Gate-10 First External Effect Architecture and Implementation Planning | **this phase** | (this phase) |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.17` | Gate-10 Pre-Effect Eligibility and Dispatch-Envelope Coordinator Implementation | Slice A — non-effecting; `run_gate10_pre_effect_eligibility` + `DispatchEnvelope` builder + N-16-1 factories; no adapter call site; `src/pcae/core/runtime_dispatch_gate10_eligibility.py` (new), `runtime_dispatch_gate9.py` (optional contract-neutral resolver-refactor), tests | separate explicit human authorization required |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.18` | Independent Verification of the Gate-10 Pre-Effect Eligibility Coordinator | Slice A IV — RE-DERIVE the F-G10-1..13 battery against RDGO v3.1 §11 / §15 / §17 and current source; prove no effect, no positive production path, no `Gate9Result` trust bypass; fixed-SHA A/B; confirm no Gate 5–9 regression | separate explicit human authorization required |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.19` | Dispatch-Attempt Durable Lifecycle, Idempotency, and 3S.2.1 Prerequisite Repairs | Slice B — mirror `RuntimeInvocationRecord`, state machine, crash/restart/`DISPATCH_UNCERTAIN`, idempotency; **+ the two 3S.2.1 MUST-FIX repairs + runtime-inspect repair (item 9)**; `runtime_invocation.py` / `runtime_adapter.py` / a new mirror-record module, tests | separate explicit human authorization required |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.20` | Independent Verification of the Dispatch-Attempt Durable Lifecycle | Slice B IV — RE-DERIVE the crash/restart/idempotency model against RDGO §17/§18, RPAC-REQ-064–072, and the repaired code; confirm the 3S.2.1 repairs; fixed-SHA A/B | separate explicit human authorization required |
| *(no ID — Slice C)* | First Concrete Effect Adapter Integration (the first external effect) | **NOT assigned** — hard-blocked on N-16-3..7 (POL-005 eligibility rule + IV, real RE gate, real FIDO2/UI, RPAC-REQ-095 adapter, capability enablement); each its own explicit human authorization; do not invent an ID | — |
| *(no ID — Slice D)* | Independent End-to-End Verification of the First External Effect | **NOT assigned** | — |

`.1R.17`–`.1R.20` are **recommended**, not reserved; each phase's own task
contract re-confirms its exact scope. No IDs above `.1R.20` are reserved.
Gate 10's *effect* keeps **no phase ID** until N-16-3..7 are all satisfied.

---

## 37. N-15-5-1 documentation hygiene (phase prompt §61)

PBRD-001 v2.1 has two sections both numbered "4a" (the new V-4
representation-equivalence clause nested under §4, plus the pre-existing
top-level "## 4a. Attempt/idempotency ownership"). This is **non-blocking**
(both bodies correct; each uniquely identifiable by full heading text;
`.1R.15.5` §5). Cross-references are **not** ambiguous — no PBRD or RDGO
text references "§4a" without adjacent disambiguating words.

**Plan:** fold the renumber (new clause → `§4b`) into **Slice A (`.1R.17`)**
as a one-line contract-doc edit under that phase's allowed-file zone, OR a
standalone documentation-hygiene micro-phase if Slice A's authorization
scope excludes `docs/contracts/**`. **Not a Gate-10 planning or
implementation blocker.**

## 37.1 N-15-5-2 (phase prompt §62)

Preserved historically as informational: the missing production-resolver
end-to-end coverage was closed by `.1R.15.5` §9. **No new work** unless
fresh evidence appears (none in this phase).

---

## 38. Production file matrix (phase prompt §66)

Anticipated source touch-points per future slice. "Effect sensitivity":
whether the file's change could bring an external effect closer.

| File | Current role | Proposed change | Slice | Effect sensitivity | Durable state? | Verification surface |
|---|---|---|---|---|---|---|
| `src/pcae/core/runtime_dispatch_gate10_eligibility.py` *(new)* | — | `run_gate10_pre_effect_eligibility` coordinator: F-G10-1..13 + §16/§17 read-back + `DispatchEnvelope` mint; `Gate10EligibilityResult` (identity-only, non-serializable); **no adapter call** | A | medium (defines the boundary; still non-effecting) | no (reads durable, writes none) | new — full battery, no-effect proof, no-positive-path proof |
| `src/pcae/core/runtime_dispatch_gate9.py` | Gate-9 coordinator | *(optional, contract-neutral)* re-express the DI `authority_generation_resolver` in terms of the shared N-16-1 factory; **no behaviour change** | A | none | no | byte-diff + Gate-9 regression suite must be unchanged in outcome |
| `src/pcae/core/runtime_introspection.py` | capability source (`CURRENT_*` constants) | *(no change in A)* — Slice B may add a dry-consumption discoverability field (item 9 / runtime-inspect repair) | B | none | no | `pcae runtime inspect` output contract |
| `src/pcae/core/runtime_invocation.py` | dry-path `RuntimeInvocationStore` / `RuntimeInvocationResult` | 3S.2.1 MUST-FIX #2 (sanitise `invocation_id` path component); mirror-record state machine | B | low | **yes** (mirror record) | path-traversal rejection; state-machine crash/restart tests |
| `src/pcae/core/runtime_adapter.py` | RPAC mock-v1 coordinator | 3S.2.1 MUST-FIX #1 (validate `adapter.collect()` return → `FAILURE_MALFORMED_RESULT`, not uncaught `AttributeError`) | B | low | no | malformed-result fail-closed test |
| `src/pcae/core/<mirror_record>.py` *(new — name TBD in B)* | — | RPAC-REQ-067 `RuntimeInvocationRecord`: append-only state-transition log, digest integrity, crash/restart determination | B | medium | **yes** | full — RPAC-REQ-064–070; `DISPATCH_UNCERTAIN` |
| `src/pcae/core/runtime_dispatch_gate10.py` *(new — Slice C only)* | — | adds the single `adapter.dispatch(envelope)` call site + `Gate10Result` + `_GATE10_RESULTS` registry | **C** | **HIGH — first external effect** | via mirror | Slice D end-to-end |
| a real RPAC-REQ-095 adapter module *(new — Slice C only)* | — | fixed-argv external-executable transport; `describe`/`preflight`/`dispatch`/`collect`/`cancel` | **C** | **HIGH** | no (adapter owns none) | Slice D |
| `permission_broker_foundation.py` (`ExecutionDisabledRule`) | POL-005 hard DENY | PBRD §12 narrow `runtime_dispatch` eligibility rule (N-16-3) | *(separate track, no ID)* | **HIGH** | no | its own IV |
| `docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` | PBRD-001 v2.1 | N-15-5-1 renumber `§4a → §4b` | A or micro-phase | none | no | doc-hygiene diff |

**No file in this table is modified by this planning phase.**

---

## 39. Contract traceability (phase prompt §67)

Every Gate-10 responsibility (§4.1) maps to normative text:

| Gate-10 responsibility | RDGO v3.1 | HPAC v2.1 | PBRD v2.1 | RPAC-001 | POL-005 | RE registry |
|---|---|---|---|---|---|---|
| G10-a trusted `Gate9Result` + `status=="consumed"` | §11 items 1–2; §10 last ¶ | — | — | — | — | — |
| G10-b durable `consumption.json` read-back | §11 item 3; §10 | §41 (`/2.1` nine closed objects) | — | RPAC-REQ-087 | — | — |
| G10-c lineage / binding match | §11 item 4; §10a; §16 | §41 | fact 14 `human_authority_binding` (§4a) | RPAC-REQ-064/065/066 | — | — |
| G10-d final runtime-capability check | §11 item 5; §10 last ¶ | — | — | RPAC-REQ-055/091 | — | — |
| G10-e mutable-authority re-validation + generation-vector compare | §11 item 6 | §41 `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`; HPAC-REQ-098/099 | — | RPAC-REQ-046 | — | — |
| G10-f containment / effect-plan read-back | §9(c); §11 item 5; §15 | — | — | RPAC-REQ-047/057/062 | — | — |
| G10-g executable re-hash before effect | §15 (TOCTOU row); §9 | — | — | RPAC-REQ-086 | — | — |
| G10-h DispatchEnvelope mint | §11 | — | — | RPAC-REQ-029/030 | — | — |
| G10-i one `adapter.dispatch()` | §11; §1 row 10 | — | — | RPAC-REQ-031/032/034/048 | — | — |
| G10-j receipt / uncertain observation | §11; §17 | — | — | RPAC-REQ-035/036/068 | — | — |
| G10-k failure / no-retry | §11; §17; §18; §19 | — | — | RPAC-REQ-071/072/075 | — | — |
| trust durable Gate-6 lineage; no PB re-run | §7; §8; §15 | — | §7 (PB never consumes); §12 | — | universal DENY upstream | — |
| revalidate RE currentness; `matched_no_go_ids` not authority | §8 | — | — | RPAC-REQ-045/046 | — | schema 1.1 "Enforcement class" |

**No undocumented effect semantics** are introduced.

---

## 40. Runtime zero-effect validation (phase prompt §68)

This phase is planning only. Evidence:

```
runtime subprocess    = 0   (no code executed; only git / pcae governance CLI)
adapter invocation    = 0
provider / network    = 0
credential operation  = 0
hardware operation    = 0
Gate10 effect         = 0
```

`git diff --name-only <entry> HEAD -- src/pcae` is empty. No test file
added or changed (planning-only). `pcae runtime inspect` at authoring time
and at finalization: `not_implemented / Observed / observe / unavailable` —
unchanged.

---

## 41. Governance (phase prompt §69)

No raw `git commit`, no raw `git push`, no `--no-verify`, no force push, no
history rewrite, no hook bypass. Governed `pcae` lifecycle only
(`pcae task` / `pcae commit` / `pcae push` / `pcae phase complete`). Only
the primary human-authorized operator holds `.1R.16` lifecycle authority.
The delegated `.3` finalization / commit / push incident remains
**UNAUTHORIZED** and is not authorized by this phase. No delegated worker
committed, finalized, or pushed.

---

## 42. No production / no contract change (phase prompt §59, §60)

- `src/pcae/**` — untouched. No Gate-10 module. No `run_gate10*` symbol.
- `docs/contracts/**` — untouched. No normative contract edited.
- Allowed changes this phase: this planning document, `PROJECT_STATUS.md`,
  `CHANGELOG.md`, task-lifecycle artifacts, `.pcae/phase-completion-*`.
- **No contract gap was exposed that requires a dedicated contract phase
  before Gate-10 planning could complete.** RDGO v3.1 §11 already carries
  the full six-item forward prerequisite; HPAC v2.1 §41 already carries the
  durable snapshot; RPAC-001 §13 already carries the crash/idempotency/retry
  model; PBRD §12 already carries the POL-005 eleven-item evolution
  boundary. The Gate-10 architecture is fully derivable from the **current
  frozen contracts** — no normative wording is missing or contradictory for
  Gate-10 purposes. (N-15-5-1 is a numbering defect, not a semantic gap —
  §37.) **No STOP condition triggered.**

---

## 43. Completeness checklist (phase prompt §71)

| # | Step | § |
|---:|---|---|
| 1 | primary-source reads complete | §2.1 |
| 2 | Gate-10 contract responsibility re-derived | §4 |
| 3 | first-effect source boundary identified | §5 |
| 4 | prerequisite item 9 adjudicated | §7 |
| 5 | Gate-10 prerequisite matrix built | §35 |
| 6 | final read-back model derived | §8–§10, §16, §17 |
| 7 | post-consumption drift semantics derived | §12, §14, §15 |
| 8 | runtime-capability final check derived | §13 |
| 9 | dispatch-attempt durability / idempotency model derived | §20, §22, §25 |
| 10 | crash / restart / retry model derived | §22, §31 |
| 11 | FIDO2 / UI / capability sequencing derived | §30 |
| 12 | implementation packaging chosen | §36 |
| 13 | exact future phase IDs frozen (where justified) | §36.2 |
| 14 | production-file matrix complete | §38 |
| 15 | defensive validation matrix complete | §34 |
| 16 | canonical `.1R.16` planning document created | this file |
| 17 | `PROJECT_STATUS.md` updated | (finalization) |
| 18 | `CHANGELOG.md` updated | (finalization) |
| 19 | task-lifecycle artifacts updated | (finalization) |
| 20 | completion metadata / report generated | (finalization) |
| 21 | final `pcae health` / `check` / `status coherence` / `doctor task-memory` / `push check` / `runtime inspect` | (finalization) |
| 22 | governed `pcae` commit lifecycle | (finalization) |
| 23 | governed `pcae` push lifecycle | (finalization) |
| 24 | `origin/main..HEAD = 0` confirmed | (finalization) |
| 25 | governed `pcae phase complete` | (finalization) |
| 26 | Telegram notification | (finalization, via `pcae phase complete`) |
| 27 | final canonical Phase Report | §30 |

---

## 30. REQUIRED FINAL REPORT (phase prompt §72, §73, §74)

**Phase ID / title.** `149O.20L.7O.3W.1R.2B.1R.1.1R.16` — Gate-10 First
External Effect Architecture and Implementation Planning.

**Status / completeness.** COMPLETE. Architecture/planning only. Every
numbered requirement of the phase prompt (§1–§74) is addressed; the §71
completion sequence steps 1–16 and 21 are done in-document; steps 17–27 are
the governed finalization performed after this artifact is committed. **No
BLOCKED condition was reached** — item 9 is `NOT SATISFIED / DEFERRED` but
does not require a prior implementation/contract phase for Gate-10 planning
to continue (§7); no contract gap requires a dedicated contract phase
(§42). **No "Remaining" section** — all authorized planning work is
complete.

**Sources / contracts inspected.** §2.1 — RDGO-001 v3.1 (full), PBRD-001
v2.1 (incl. §12 full), HPAC-001 v2.1 §41, RIHAC-001 v2.0 §14/§19, RIASC-001
v3.0 + §9 errata, RPAC-001 v1.0 (full), PBPA-001, POL-005
(`ExecutionDisabledRule`), RE No-Go Registry 1.1. Phase docs `.1R.9`,
`.1R.11`, `.1R.13`, `.1R.13.1`, `.1R.13.3`, `.1R.13.5`, `.1R.14`, `.1R.15`,
`.1R.15.1`–`.1R.15.5`, `3S.2.1`. Production source line-by-line:
`runtime_dispatch_gate9.py`, `runtime_invocation_authority_consumption.py`,
`runtime_introspection.py`, `runtime_adapter.py`, `runtime_dispatch_gate8.py`
(shapes), `mock_runtime_adapter.py`, `backend_invocations.py` /
`delivery_receipt.py` (headers), `permission_broker_foundation.py`
(POL-005).

**Current Gate-5→9 verified state.** All CLOSED (§1). Gate 5 / 6 / 7 / 8
production modules byte-unchanged since `4d480553` (`.1R.15.5` §10). Gate 9
verified with the V-15-1 serialization window CLOSED and the durable
`authority_generation_binding` CLOSED (`.1R.15.5`).

**Current runtime state.** `not_implemented / Observed / observe /
unavailable`; 0 plugins / 0 capabilities; PB `execution_unavailable`;
non-executing. Unchanged at entry and finalization.

**Exact Gate-10 contract responsibility.** §4 — G10-a…G10-k: the six-item
RDGO §11 pre-effect read-back battery + §16/§17 containment & executable
read-back + `DispatchEnvelope` mint + exactly one `adapter.dispatch()` call
+ receipt/uncertainty observation + no-retry semantics. **Not** Gate 10's:
adapter/target selection (Gate 2), PB policy (Gate 6), RE policy (Gate 7),
authority consumption / the `dispatch_attempted` marker (Gate 9), result
normalization / intake (Gate 11), effect-plan assembly (trusted
coordinator).

**Exact first-effect boundary.** §5 — the single `adapter.dispatch(envelope)`
call site inside the future Gate-10 coordinator, invoking a real (non-mock)
`RuntimeAdapter` with `execution_effect == "local_process"` (an
`os.posix_spawn`-class process creation with frozen argv / repo-bound cwd /
sanitised env / network denied / no credentials). No such adapter exists,
is registered, or is reachable today. Not called by this phase.

**Prerequisite item 9 disposition.** §7 — **NOT SATISFIED / DEFERRED**. The
two 3S.2.1 MUST-FIX repairs (malformed-result fail-closed; store
path-traversal) + the runtime-inspect discoverability repair. Both 3S.2.1
items are explicitly non-blocking and unreachable through the current
production entry point; RDGO §12 makes them "blocking before the first
non-mock adapter becomes reachable". **Not blocking** this planning phase
or Slices A/B; **folded into Slice B (`.1R.19`)**; **hard prerequisite for
Slice C** (the first concrete effect adapter).

**Full Gate-10 prerequisite matrix.** §35 — 18 rows. Items 1–8, 10
SATISFIED (`.1R.15.5`); item 9 + new items 11–17 NOT SATISFIED (11–12 =
Slice A/B scope; 9, 13–17 = Slice C prerequisites); item 18 (N-15-5-1)
non-blocking. **Nothing in the matrix blocks this planning phase or Slice
A/B.**

**Gate9Result provenance / success requirements.** §6 — `is_gate9_result`
is exact-object registry provenance only; Gate 10 additionally requires
`status == "consumed"` (F-G10-1). `already_consumed` is never a re-entry
licence.

**/2.1 durable record read-back.** §8 — F-G10-2: fresh
`RuntimeInvocationAuthorityConsumptionStore.resolve(proof_id)`; canonical
protected `consumption.json`; provenance + integrity + `record_digest`
byte-verify against `Gate9Result.record_digest`; exact `Gate9Result` ↔
durable-record binding on `proof_id` / `approval_id` / `invocation_id` /
`attempt_id` / `dispatch_binding.state`.

**/2.0 ineligibility.** §9 — F-G10-3: a `/2.0` record (or any non-`/2.1`
schema) → fail closed; no compatibility fallback; no `/2.0` record exists
anywhere in the repo (N-15-4-1, informational).

**Generation-snapshot current-state comparison.** §10, §11 — F-G10-4 /
F-G10-5: validate the durable `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`
(schema, integrity, five markers); re-derive current principal /
credential / approval / lifecycle / consumption generation from durable
stores only; principal/credential/approval/lifecycle mismatch → fail
closed; `consumption_generation` transitioning `absent → present` is
expected, not drift. Restart-safe (digests over durable state, no
wall-clock/nonce).

**Post-consumption drift semantics.** §12 — every drift (principal /
credential / approval / expiry / lifecycle / capability / containment / RE
expiry) invalidates Gate-10 eligibility with no effect; the immutable
consumption record is unchanged in every case. A *positive* runtime
capability with drifted authority is still a hard stop.

**Consumed-authority permanence.** §14 — F-G10-8: `post-consumption drift
!= authority becomes unconsumed`; record stays durable; approval / proof /
presentation / challenge not restored; `attempt_limit=1` spent; human may
need a new invocation. **No consumption rollback** (§28 / F-G10-9).

**Final containment / effect read-back.** §16 — F-G10-10: re-run the
Gate-8 containment establishment over freshly re-resolved inputs; recompute
`containment_evidence_digest` / `effect_plan_digest` and require equality
with the durable `consumption.json` values (the exact pattern Gate 9 uses);
`network_denied is True` and `credentials_required is False` re-asserted;
Gate 10 does **not** re-run Gate 8 as a *decision* and does not trust a
stale `Gate8Result` (it is ephemeral / gone after restart).

**Executable identity revalidation.** §17 — F-G10-11: re-`stat` + re-`sha256`
the exact resolved executable immediately before `adapter.dispatch()`, with
no intervening effectful I/O; compare against
`target_binding.executable_identity_digest`; drift / absence / permission
change / symlink → fail closed. Mandatory (RDGO §15 TOCTOU row).

**Capability final revalidation.** §13 — F-G10-6 / F-G10-7: canonical
source is `runtime_introspection` (`CURRENT_RUNTIME_STATE` /
`CURRENT_MAXIMUM_PLUGIN_CAPABILITY` / `EXECUTION_AVAILABILITY`), the same
shape Gate 9 checks; re-read inside the Gate-10 battery; `Observed /
observe / unavailable` → Gate 10 **cannot** perform the effect. Gate-7's
earlier decision is not trusted indefinitely. **N-16-1**: no production
`build_gate10_capability_snapshot_resolver` / `authority_generation_resolver`
factory exists — Slice A scope.

**POL-005 relationship.** §18 — F-G10-12: trust the durable Gate-6 lineage
(byte-compare `pb_binding`, require `decision == "ALLOW"`); independently
assert the consumed lineage represents a valid prior permission decision;
**do not re-run PB policy** (Gate 6 owns it exclusively); a stale
`policy_version` is fixed by re-entering Gate 6, surfaced only as an
advisory reason, never a positive basis; **do not invent another PB
evaluation layer**. POL-005 remains hard DENY; trusted consumed authority
does not override it.

**Runtime Enforcement relationship.** §19 — F-G10-13: re-check from Gate 7
the durable `runtime_enforcement_binding` (byte-compare; `verdict == ALLOW`;
`expires_at` in the future); re-read execution availability from *current*
runtime capability; `matched_no_go_ids` is a per-decision diagnostic, **not
authority**.

**Real FIDO2 / UI prerequisite decision.** §30 — **Option A + Option C**: a
structural, non-effecting Gate-10 eligibility coordinator (Slice A) and the
dispatch-attempt lifecycle (Slice B) may be built now (same pattern as
Gates 5–9; positive production path remains unreachable); the actual
effect (Slice C) is split into a separate, human-authority-gated phase. A
NON_REAL lineage is blocked at five independent points (§30.1).

**Positive-path reachability.** §23 — **NO positive production Gate-10 path
exists today**; seven independent blockers (NON_REAL HPAC, real Gate 7
DENY, capability unavailable, no real adapter, POL-005, no protected UI, no
real FIDO2). Not fabricated.

**Dispatch-attempt definition.** §20 — two distinct linearization points:
`dispatch_attempted` (Gate 9's `O_EXCL` create; authority spent) vs
`effect_attempt_started` (mirror record, written **before** the adapter
call). `dispatch attempted != effect succeeded`; any post-entry ambiguity
is `DISPATCH_UNCERTAIN`.

**Exactly-once / at-most-once decision.** §25.1 — PCAE guarantees
**at-most-once dispatch attempt with fail-closed uncertainty**; at-most-once
authority consumption per `proof_id` (Gate-9 `O_EXCL`); at-most-once effect
attempt per `attempt_id` (mirror guard); **exactly-once effect is NOT
achievable generically** — a crash yields `DISPATCH_UNCERTAIN` + human
decision.

**Idempotency-key strategy.** §25.2 — no current adapter supports a
provider idempotency token; for a future one, pass `attempt_id` as the
external token; `idempotency_key` (RPAC-REQ-065 SHA-256 canonical content)
is PCAE-side replay identity (RPAC-REQ-070), never provider-facing, never
by itself an authorization to redispatch.

**Dispatch-attempt durable model / write-before vs write-after / two-state
decision.** §22 — **Model A (write-before-effect) + Model C (two-state
lifecycle)** on a **non-authoritative, append-only repository-side mirror
`RuntimeInvocationRecord`** (RPAC-REQ-067); the authoritative one-shot truth
stays `consumption.json` (create-only, immutable). Rationale: Model A's
failure mode is fail-closed (a false "attempted" → `DISPATCH_UNCERTAIN` +
fresh approval), Model B's is fail-open (a duplicate external effect);
RDGO §17 / RPAC-REQ-068 mandate the Model-A posture; consistent with Gate
9's own write-before-effect discipline.

**Crash-before-effect.** §22.1 / §31 — `consumption.json` present, mirror
without `EFFECT_ATTEMPT_STARTED` → consumed, `DISPATCH_NOT_STARTED`; no
effect; fresh invocation/approval required.

**Crash-during-effect.** §22.1 — `DISPATCH_UNCERTAIN`; fail closed; never
blindly retry.

**Crash-after-effect-before-record.** §22.1 — indistinguishable from
crash-during → `DISPATCH_UNCERTAIN`; the architecture represents "effect
outcome uncertain" and prohibits automatic retry (RDGO §17: absence of a
result is never proof dispatch did not occur).

**Restart behaviour.** §31 — recovery from durable state only
(`consumption.json` + mirror record); no in-memory gate result may be
required; a restarted Gate-10 attempt re-runs the entire §6–§19 battery
from disk.

**Retry / new-approval semantics.** §15 — three cases: pre-effect
eligibility failure, confirmed-non-delivery effect failure, uncertain
result — **none** may retry from the same consumed authority; each requires
a fresh `invocation_id` / `attempt_id` / approval / proof (RDGO §18;
RPAC-REQ-072; `attempt_limit` is always 1); an uncertain result
additionally requires a human decision on whether a new attempt is safe.

**Effect receipt semantics.** §26 — F-G10-16: `receipt = evidence of
effect/result, NOT permission/authority`; may establish invocation
accepted / process id / provider request id / exit status; cannot authorize
another effect; `accepted=True` is not proof of completion. Any
`Gate10Result` follows the Gate5–9Result pattern (exact-object registry,
non-serializable, identity-only, not durable) — no "object shape = trust".

**Adapter ownership.** §27.1 — the Gate-10 coordinator owns the pre-effect
battery, envelope mint, mirror transitions, and the **single**
`adapter.dispatch()` call site; the `RuntimeAdapter` implementation owns
process/API mechanics under kernel constraints; neither Shell Gate (Gate 8,
containment) nor `backend_invocations.py` (legacy) owns dispatch; no
duplicate execution logic.

**Credential boundary.** §28 — F-G10-17: Gate 10 SHALL NOT access
credentials; the first effect is a no-credential local process
(`credentials_required is False`); credential-backed effects require a
separate governed boundary (RPAC-REQ-058/084 — no secret resolver exists).

**Threat model.** §29 — F7 carried verbatim, NOT broadened: same-process
arbitrary Python code execution is outside protection; data-forgery
resistance only; no OS/stdio/git/session identity trusted; process
isolation is a separate unscheduled topic; no overclaim of process-local
provenance as a hardware boundary.

**Defensive validation matrix.** §34 — 34 cases mapped to Slices A–D; every
case fails closed with no external effect.

**Selected implementation packaging.** §36 — Slice A (`.1R.17`) non-effecting
eligibility + envelope coordinator + N-16-1 factories → Slice A IV
(`.1R.18`); Slice B (`.1R.19`) dispatch-attempt durable lifecycle + item-9
repairs → Slice B IV (`.1R.20`); Slice C (no ID) first concrete effect
adapter → Slice D (no ID) end-to-end IV. Every trust/effect-bearing slice
gets its own implementation + IV pair.

**Exact future phase IDs / titles.** §36.2 — `.1R.17`–`.1R.20` recommended
(not reserved); Slice C / D keep **no ID** until N-16-3..7 satisfied. No ID
above `.1R.20` reserved.

**Gate-10 implementation readiness status.** Slice A/B: **READY to be
human-authorized** (prerequisites 1–8, 10 satisfied; 9 non-blocking for
these slices; 11–12 are their own scope). Slice C (first external effect):
**NOT READY** — blocked on N-16-3 (POL-005 eligibility rule + IV), N-16-4
(real positive RE gate), N-16-5 (real FIDO2 + protected UI), N-16-6
(RPAC-REQ-095 adapter + supply-chain admission), N-16-7 (capability
enablement), and item 9.

**Production-file matrix.** §38 — 10 anticipated touch-points across Slices
A–C + the separate POL-005/doc track; **none touched by this phase**.

**Contract traceability.** §39 — every G10-a…G10-k responsibility mapped to
RDGO v3.1 / HPAC v2.1 / PBRD v2.1 / RPAC-001 / POL-005 / RE-registry text;
no undocumented effect semantics.

**N-15-5-1 disposition.** §37 — non-blocking PBRD duplicate "§4a"; fold the
renumber into Slice A or a doc-hygiene micro-phase; cross-references are
not ambiguous. **N-15-5-2** (§37.1): informational, closed by `.1R.15.5`,
no new work.

**Gate 10 still not implemented.** Confirmed — no `runtime_dispatch_gate10*`
module, no `run_gate10*` symbol, no `DispatchEnvelope` mint, no
`_GATE10_RESULTS` registry, no adapter call. `DispatchReceipt` exists only
in the pre-existing, byte-unchanged RPAC mock-v1 simulation scaffolding
(`runtime_adapter.py` / `mock_runtime_adapter.py`), unrelated to the Gate
5–11 chain. Gate 10 keeps **no phase ID**; `.1R.17`–`.1R.20` are the
recommended *precursor* IDs, none of which is Gate 10's effect.

**Runtime / no-effect evidence.** §40 — 0 subprocess, 0 adapter, 0
provider/network, 0 credential, 0 hardware, 0 Gate-10 effect; `src/pcae`
diff empty; no test file changed; `pcae runtime inspect` unchanged.

**`.3` governance incident status.** `DELEGATED .3 FINALIZATION / COMMIT /
PUSH: UNAUTHORIZED` — preserved unchanged. Not authorized by this phase. No
delegated worker committed, finalized, or pushed.

**Commits / pushed status / `origin/main..HEAD`.** Recorded in
`.pcae/phase-completion-metadata.json` after governed finalization;
`pushed_status: pushed`; `origin/main..HEAD = 0` after the governed push.

**Final verdict.** **GATE-10 FIRST EXTERNAL EFFECT ARCHITECTURE COMPLETE —
PLANNING ONLY — GATE 10 NOT IMPLEMENTED, NO EFFECT ENABLED.** Slices A and
B (`.1R.17`–`.1R.20`) are ready for separate explicit human authorization;
the first external effect (Slice C) remains blocked on the real-authority /
capability / POL-005 / adapter prerequisite set and keeps no phase ID.

---

## No-Go Confirmations

- No production source file was created, modified, or deleted by this phase;
  `git diff --name-only <entry> HEAD -- src/pcae` is empty.
- No `runtime_dispatch_gate10.py`, `run_gate10*` symbol, `Gate10Result`,
  `_GATE10_RESULTS` registry, `DispatchEnvelope` mint, or adapter call site
  was introduced.
- No normative contract file was edited (RDGO / PBRD / HPAC / RIHAC / RIASC
  / RPAC / PBPA / POL-005 / RE registry all byte-unchanged).
- No Gate 10 was implemented, designed to the code level, or assigned a
  phase ID; `.1R.17`–`.1R.20` are recommended precursor IDs and none is the
  first-effect boundary.
- No execution was enabled; runtime remains `not_implemented / Observed /
  observe / unavailable`; 0 plugins / 0 capabilities; POL-005 unchanged and
  still hard DENY.
- No runtime capability was elevated or promoted; no `Observed → Approved /
  Executable` transition was performed or planned to occur automatically.
- No adapter (mock or real) was registered, implemented, activated, or
  called; `RuntimeRegistry` remains empty.
- No subprocess, process spawn, `os.system` / `popen` / `spawn` / `exec*`,
  `pty`, provider SDK, HTTP client, socket, or FIDO2 / WebAuthn / CTAP /
  smartcard / USB path was created or invoked.
- No real FIDO2 / WebAuthn / CTAP was implemented; deterministic
  authentication remains NON_REAL.
- No protected human-approval UI was implemented.
- No credential was accessed, resolved, embedded, or referenced; no secret
  resolver was created.
- No approval / proof / presentation / challenge / nonce was consumed on any
  path; no `consumption.json` was written anywhere (no code ran).
- No external repository, third-party system, unrelated account, provider
  API, external network, or deployment target was accessed or mutated.
- No third-party or other machine was contacted.
- No test was added, removed, weakened, or skipped (planning-only phase; no
  test change).
- No raw `git commit` / `git push`, no `--no-verify`, no force push, no
  history rewrite, no hook bypass — governed `pcae` lifecycle only.
- No delegated worker committed, finalized, or pushed; only the primary
  human-authorized operator holds `.1R.16` lifecycle authority.
- No authorization of the historical delegated `.3` finalization / commit /
  push; it remains UNAUTHORIZED.
- No MAJOR or MINOR contract version was bumped, forced, or overridden.
- No closed gate boundary (Gate 5 / 6 / 7 / 8 / 9) was reopened; their
  production modules remain byte-unchanged since `4d480553`.
- No "Gate 9.5" or other new validation-only gate was invented; the
  Gate-10 pre-effect battery is RDGO v3.1 §11 items 1–6 verbatim, inside
  Gate 10.
- No positive production Gate-10 path was fabricated; §23's seven
  independent blockers stand.
- No STOP / BLOCKED condition was reached; prerequisite item 9 is
  NOT-SATISFIED / DEFERRED but does not block Gate-10 planning or Slices
  A/B.

---
*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.16.*
