# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.24 — N-16-4 Real Positive Single-Attempt Runtime Enforcement Gate Architecture and Contract Planning

**Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.24`
**Type:** planning / primary-source analysis / contract-impact analysis / threat-modeling / decision-freezing only
**Phase-entry SHA:** `1ca1f6ab` (`origin/main` synced; `origin/main..HEAD = 0` at entry)
**Production source changed:** none (`git diff --name-only 1ca1f6ab HEAD -- src/pcae` empty)
**Normative contracts changed:** none (`git diff --name-only 1ca1f6ab HEAD -- docs/contracts docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` empty)
**Gate-7 source:** `src/pcae/core/runtime_dispatch_gate7.py` byte-identical
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; real execution UNAVAILABLE; deterministic authentication NON_REAL; first external effect ABSENT
**Verdict:** **N-16-4 ARCHITECTURE / CONTRACT PLAN COMPLETE — IMPLEMENTATION NOT BEGUN.** REAL POSITIVE GATE-7 RESULT: ARCHITECTURE FROZEN — NON-BEARER — INVOCATION/ATTEMPT BOUND — DOWNSTREAM GATES STILL REQUIRED.

---

## 0. Governing prerequisite state (phase prompt §1), treated as current

| Item | State |
|---|---|
| N-16-3 | **CLOSED** (`.1R.22R.1` IV — independently verified with non-blocking findings) |
| PBRD-001 v3.0 migration | VERIFIED (MAJOR; inline §16 migration) |
| POL-005 narrow evolution | VERIFIED (match-domain evolution; DENY body byte-identical) |
| POL-013 | VERIFIED / NEVER POSITIVE (statically DENY-or-neutral only) |
| `RUNTIME_DISPATCH_LOCAL_CLI_V1` | PRODUCTIONALLY UNSATISFIABLE (sole production N-16-6 resolver admits nothing; no trusted `ValidatedAuthorityProjection` reachable) |
| N-16-4 | **OPEN** — this phase plans it, does not implement it |
| N-16-5, N-16-6, N-16-7 | OPEN — strictly later; not begun |
| Gate 5 | CLOSED (`.1R.11`) |
| Gate 6 | CLOSED (`.1R.13` / N-16-3 `.1R.22R.1`) |
| Gate 7 | **currently negative-only** — `run_gate7_runtime_enforcement` always returns `Gate7Result(decision="DENY")` on the production path; the `ALLOW` branch is structurally present, `# pragma: no cover - unreachable in production` |
| Gate 8 | CLOSED (`.1R.13.5`) |
| Gate 9 | CLOSED (`.1R.15` / `.1R.15.3`) |
| Slice A (Gate-10 pre-effect eligibility + `DispatchEnvelope`) | CLOSED (`.1R.17R.1`) |
| Slice B (dispatch-attempt durable lifecycle) | CLOSED (`.1R.19R.1`) |
| First external effect | ABSENT |
| Runtime | Observed / observe / unavailable |

N-16-3 is **not reopened** — no direct contradictory primary evidence was discovered in this phase.

---

## 1. Primary sources inspected (phase prompt §3, §78)

Read in full or to the complete relevant normative scope:

**Normative / current contracts.**

- `docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` — **RDGO-001 v3.1** (all 21 sections; §0 walls, §1 eleven-gate table, §8 Gate 7, §9 Gate 8, §10 Gate 9 nine items incl. item 7 Runtime Enforcement binding and item 9 authority-generation binding, §10a attempt/idempotency identity, §11 Gate 10 forward read-back prerequisite six items, §15 TOCTOU seven facts, §16 cross-contract identifiers, §17 crash/recovery states, §19 security invariants, §21 versioning — `MAJOR.MINOR`, "adding a later post-result gate may be additive only if …", "merging authority/permission/enforcement/containment … requires a further new MAJOR").
- `docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md` — **PBNDE-001 v1.0** (§2 POL-005 v2 statement, §4 POL-013 result vocabulary, §5 precedence, §7 downstream-gate independence — "POL-013 … MUST NOT read, reference, or carry any Gate-7 result or expectation. Gate 7 receives the PB decision as an input and independently re-validates", §8 attempt-count / decision-lifetime, §10 versioning).
- `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` — **RE No-Go Registry schema 1.1** (RE-NOGO-001..017; enforcement-class column: per-decision {001–008, 010, 011}, environmental-readiness {009, 013, 015, 016, 017}, advisory {012, 014}; the scoping paragraph — "Gate-7 progression depends on the authoritative Gate-7 decision, **not** on the completeness of `matched_no_go_ids`").
- `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` — NG-025 ("Execution Boundary Unavailable"), unconditionally active for every non-simulation request except the one trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile (PBNDE-001 §9 annotation), human override `no`.
- Runtime Enforcement decision/result contracts — **legacy Phase-102 `RuntimeEnforcementDecision`** (`docs/PHASE_102_RUNTIME_ENFORCEMENT_DECISION_ENGINE_CONTRACT_FREEZE.md`, schema `"1.0"`: 9 statuses, 12 blocking results, 22 fail-closed rules, no-go propagation, authorization/safety flag semantics, "future-only execution decision constraints") and **Phase-103 `RUNTIME_ENFORCEMENT_COORDINATOR` freeze**. These govern the *design-only* decision engine / coordinator, **not** the RDGO Gate-7 `runtime_dispatch` coordinator; they are consumed as vocabulary, not re-defined.
- `docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` (RIHAC-001 v2.0), `RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` (RIASC-001 v3.0), `HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (HPAC-001 v2.1), `PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` (PBRD-001 v3.0), `RUNTIME_PROVIDER_ADAPTER_CONTRACT.md` (RPAC-001 v1.0 — RPAC-REQ-029 `DispatchEnvelope`, RPAC-REQ-030 version check), `PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` (PBPA-001 v1.1).

**Production source.**

- `src/pcae/core/runtime_dispatch_gate7.py` (699 lines, **read in full**) — `Gate7Result`, `is_gate7_result`, `run_gate7_runtime_enforcement`, `RuntimeEnforcementPosture`, `resolve_runtime_enforcement_posture`, `_matched_blocking_no_go_ids`, `_pb_decision_digest`, `GATE7_DECISION_VALUES`, the `_GATE7_RESULTS` identity registry, the `_GATE7_RESULT_CONSTRUCTOR_SEAL`.
- `src/pcae/core/runtime_dispatch_gate10_eligibility.py` (986 lines, **read in full**) — `run_gate10_pre_effect_eligibility` (the 18-step battery), `DispatchEnvelope`, `is_dispatch_envelope`, `_gate7_result_digest` usage, `_GATE10_AUTHORITY_GENERATION_KEYS`, `GATE10_ELIGIBILITY_REASON_IDS` (incl. `gate10_untrusted_gate7_result`, `gate10_gate7_decision_not_allow`, `gate10_gate7_lineage_mismatch`, `gate10_re_lineage_not_allow`, `gate10_re_decision_expired`).
- `src/pcae/core/runtime_dispatch_gate8.py` (headers + `_gate7_result_digest` L418–434 + consumption path L499–591, L798–868) — Gate 8 consumes `Gate7Result` via `is_gate7_result` + `decision == "ALLOW"` exact string equality; binds `gate7_result_digest` into `Gate8Result` and the containment evidence.
- `src/pcae/core/runtime_dispatch_gate9.py` (headers + `runtime_enforcement_binding` write L787–792) — Gate 9 item 7 durable record: `{decision_id: gate7_result.request_id, decision_digest: fresh_gate8.gate7_result_digest, verdict: gate7_result.decision, expires_at: gate7_result.expires_at, evaluated_input_digest: gate7_result.evaluated_input_digest}`.
- `src/pcae/core/runtime_enforcement_safety_authorization.py` (imported symbols: `AUTH_FLAG_TO_NO_GO`, `AUTHORIZATION_FLAG_NAMES`, `DEFAULT_AUTHORIZATION_FLAGS`, `DEFAULT_SAFETY_FLAGS`, `SAFETY_FLAG_NAMES`, `SAFETY_FLAG_TO_NO_GO`) — the design-only flag→no-go vocabulary Gate 7 consumes verbatim.
- `src/pcae/core/runtime_dispatch_permission.py` — `Gate6Decision`, `is_gate6_decision`, `RuntimeDispatchIdentity`, `RuntimeDispatchRequestConstructionInput`, `_validate_construction_inputs`, `_expected_subject_scope_binding_digest`, `build_runtime_dispatch_permission_broker_request`, `_RUNTIME_DISPATCH_REQUEST_SEAL`.
- `src/pcae/core/runtime_authority.py` — `compute_canonical_digest`, `is_trusted_validated_authority_projection`, `revalidate_validated_authority_projection`, `ValidatedAuthorityProjection`.
- `src/pcae/core/runtime_introspection.py` — `CURRENT_RUNTIME_STATE` / `CURRENT_MAXIMUM_PLUGIN_CAPABILITY` / `EXECUTION_AVAILABILITY` constants (the canonical capability source both Gate 7 and Gate 10 read).

**Phase artifacts.**

- `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_16_...PLANNING.md` — the Gate-10 architecture / plan (§11.1 N-16-1, §23 "No positive production Gate-10 path exists", §35 row 14 = the N-16-4 mandate, §36.2 slice-ID freeze — IDs above `.1R.20` are **recommended not reserved**).
- `.1R.21` — N-16-3 planning (structure precedent for this document; Option-selection method; versioning-adjudication method).
- `.1R.22` / `.1R.23` / `.1R.22R` / `.1R.22R.1` — N-16-3 implementation, BLOCKED IV, reconciliation, reconciliation IV (the guard-impact / stale-freeze history that §50/§51 of this plan must pre-empt; the "RE-DERIVE, DO NOT TRUST" and fixed-SHA-A/B discipline).
- `.1R.13.1` / `.1R.13.2` / `.1R.13.3` — Gate-7 planning, implementation, IV (the frozen file matrix `runtime_dispatch_permission.py`: "None anticipated"; the §10.4 freshness-re-resolution decision; the §10.7 PB-policy-drift decision; the §21 expiry / single-attempt decision — all reconstructed below in §6).
- `.1R.13.5` (Gate 8 IV), `.1R.15` / `.1R.15.3` (Gate 9 IV), `.1R.17` / `.1R.17R` / `.1R.17R.1` (Slice A), `.1R.19` / `.1R.19R` / `.1R.19R.1` (Slice B), `.1R.15.4` (RDGO-001 v3.0→v3.1 normalization).

Repository inspection (phase prompt §4) confirmed at entry: `.1R.22R.1` latest completed phase; repository clean; no active governed phase before startup; `origin/main..HEAD = 0`; runtime `not_implemented / Observed / observe / unavailable`; `pcae health` healthy, `pcae check` passed, `pcae status coherence` coherent, `pcae push check` `nothing_to_push`; `pcae doctor task-memory` warning-only historical `DONE.md` omissions (pre-existing hygiene debt, no current-phase error).

**No design was made from report prose alone.** Every structural claim below is anchored to a byte-current source file or a frozen contract section.

---

## 2. Core semantic walls preserved (phase prompt §2)

This plan preserves, unchanged, every wall in RDGO-001 v3.1 §0 and PBNDE-001 §5/§7, and adds nothing that weakens them:

```
PB eligibility                != Runtime Enforcement approval
Runtime Enforcement ALLOW     != runtime capability
Runtime Enforcement ALLOW     != adapter admission
Runtime Enforcement ALLOW     != DispatchEnvelope authority
Runtime Enforcement ALLOW     != Gate-8 success
Runtime Enforcement ALLOW     != Gate-9 authority consumption
Runtime Enforcement ALLOW     != permission to perform an external effect
Runtime Enforcement result    != bearer token
attempt identity              != reusable authority
human approval  != PB permission  != Runtime Enforcement  != runtime capability  != execution
```

And the pipeline invariant:

```
one PB-eligible invocation/attempt
  -> at most one bounded positive Runtime Enforcement result
  -> still subject to Gates 8, 9, Gate-10 pre-effect eligibility,
     Slice-B attempt lifecycle, adapter admission, and runtime capability
```

The positive Gate-7 result this plan freezes is a **subordinate, single-attempt, currentness-bound, non-transferable evaluation record** — never a licence, never a token, never a step that can be skipped past.

---

## 3. Exact N-16-4 mandate, re-derived in normative form (phase prompt §5, §78)

### 3.1 Primary-source wording

`.1R.16` §35 prerequisite table, **row 14 (verbatim):**

> **14 *(new — N-16-4)*** | Real, positive, single-attempt Runtime Enforcement gate over the full RDGO v3.1 projection (PBRD §12 item 5) — real Gate 7 currently DENYs | **NOT SATISFIED** | §23; PBRD §12 item 5 | No | No | **YES**

RDGO-001 v3.1 §8 (Gate 7), the load-bearing sentences:

> "It independently evaluates the complete bound request. It SHALL NOT infer approval from PB ALLOW, permission from approval, capability from the target name, or containment from a planned profile."
> "Its positive decision is single-attempt, expiring, and invalid across any relevant input or policy change. A denial, failure, stale input, unavailable target, or unresolved no-go stops the flow. No real process has been launched at this gate."

RDGO-001 v3.1 §10 item 7 (what Gate 9 durably records **from** a positive Gate-7 decision):

> "**Runtime Enforcement binding:** decision ID/digest, verdict, expiry, and evaluated-input digest."

RDGO-001 v3.1 §11 item 5–6 (what a future Gate 10 does **with** it):

> "runtime capability eligible … at gate-10 entry; re-validation of all mutable authority … as-of gate-10 entry, **and** re-derivation of the current authority-generation vector and comparison against the durable `authority_generation_binding` snapshot".

### 3.2 Normative statement of N-16-4 (frozen)

> **N-16-4** defines and freezes the architecture and contract ownership for the **first legitimate positive Runtime Enforcement (Gate-7) result** for a **single** bound `runtime_dispatch` invocation/attempt, evaluated over the **complete RDGO-001 v3.1 §8-item-1..4 projection**, such that:
> 1. the positive result means **only** "the exact bound invocation/attempt satisfies Runtime Enforcement constraints sufficiently to proceed to the next governed gate" — it is **not** permission to execute, dispatch, or perform an external effect, **not** runtime capability, **not** adapter availability, **not** PB permission, and **not** human authority;
> 2. it is **non-transferable, non-bearer, invocation/attempt-bound**, and **invalid across any relevant input, PB-decision, authority-currentness, or runtime-posture change**;
> 3. it **consumes** already-produced Gate-6/PB decision evidence and Gate-5 validated-authority evidence as **inputs** — it never re-runs PB policy, never manufactures PB `ALLOW`, and never re-authenticates the human;
> 4. it remains **strictly subordinate** to Gate 8 (containment), Gate 9 (durable authority consumption), Gate-10 pre-effect eligibility (the RDGO §11 six-item read-back), the Slice-B attempt lifecycle, adapter admission (N-16-6), and runtime capability (N-16-7) — none of which it may pre-empt, satisfy, or substitute for;
> 5. under the current production posture it still leads to **overall execution unavailable**, and after N-16-4 alone the first external effect remains **unreachable** because N-16-5, N-16-6, N-16-7, and Slice C stay open.

N-16-4 **is not**: implementing Gate 7's positive branch as a reachable production path (that is the recommended `.1R.25`); real human authentication (N-16-5); a real fixed-argv adapter or supply-chain admission (N-16-6); capability enablement (N-16-7); the first effect (Slice C).

### 3.3 Which contract owns N-16-4 semantics

See §29. **Decision (frozen): a new dedicated contract — `REPRC-001` (Runtime Enforcement Positive-Result Contract) v1.0** — analogous to how PBNDE-001 v1.0 was created for N-16-3, plus a **RDGO-001 v3.1 → v3.2 MINOR** clarifying cross-reference in §8. This is the same precedent shape the repository already used (`.1R.22` created PBNDE-001 for the N-16-3 rule; RDGO carried the corresponding cross-ref).

---

## 4. Current Gate-7 behavior, independently reconstructed from `runtime_dispatch_gate7.py` (phase prompt §6, §78)

### 4.1 Current Gate-7 component matrix (CANONICAL MATRIX #1 — phase prompt §70.1)

| Dimension | Current behavior (byte-current source) |
|---|---|
| **Input object** | `run_gate7_runtime_enforcement(gate6_decision, *, gate5_result, identity: RuntimeDispatchIdentity, inputs: RuntimeDispatchRequestConstructionInput, authority_current_time: str)` — no request field carries posture; no `execution_available` parameter |
| **Trusted producer of each input** | `gate6_decision` → exact object from `run_gate6_permission_broker` (via `is_gate6_decision`, `_GATE6_*` registry); `gate5_result` → exact object from `run_gate5` (via `is_gate5_result`); `identity` / `inputs` → `type(x) is …` exact-type check + `_validate_construction_inputs`; `authority_current_time` → bounded string only |
| **Decision vocabulary** | `GATE7_DECISION_VALUES = frozenset({"ALLOW", "DENY"})` — binary whether-to-invoke; **no `HUMAN_REVIEW`** (a Gate-6 concept, hard stop before Gate 7) |
| **Fail-closed behavior** | 12 pre-evaluation reason ids, each returned as `(None, (reason,))` creating no `Gate7Result`: `gate7_untrusted_gate6_decision`, `gate7_pb_decision_not_allow:<value>`, `gate7_untrusted_gate5_result`, `gate7_invocation_binding_mismatch`, `gate7_invalid_authority_current_time` / `_invalid_identity` / `_invalid_construction_input`, `gate7_stale_validated_authority_projection`, `gate7_authority_subject_scope_mismatch`, `gate7_request_currentness_drift:<fact>`, `gate7_runtime_target_ineligible`, `gate7_internal_error_fail_closed` (bare `except Exception`) |
| **No-go handling** | `_matched_blocking_no_go_ids(auth_flags, safety_flags)` maps the design-only `DEFAULT_AUTHORIZATION_FLAGS` (all `False`) + `DEFAULT_SAFETY_FLAGS` (all `True`) through `AUTH_FLAG_TO_NO_GO` / `SAFETY_FLAG_TO_NO_GO` to a sorted tuple ⊇ `{RE-NOGO-001, RE-NOGO-002, RE-NOGO-010, RE-NOGO-011}` — always non-empty today |
| **Result object** | `Gate7Result` — `__slots__`: `decision`, `matched_no_go_ids`, `causing_reason_ids`, `invocation_id`, `attempt_id`, `request_id`, `pb_decision_digest`, `authority_freshness_digest`, `evaluated_input_digest`, `runtime_posture_digest`, `expires_at`, `evaluated_at`, `_seal` |
| **Caller(s) / consumers** | `runtime_dispatch_gate8.run_gate8_process_containment` (arg `gate7_result`), `runtime_dispatch_gate9.run_gate9_atomic_authority_consumption` (arg `gate7_result`), `runtime_dispatch_gate10_eligibility.run_gate10_pre_effect_eligibility` (arg `gate7_result`) — each via `is_gate7_result` + `decision == "ALLOW"` |
| **Digest / binding behavior** | `evaluated_input_digest` = `compute_canonical_digest` over {invocation_id, attempt_id, idempotency_key, subject_scope_binding_digest, runtime_target_id, requested_capability, prompt_hash, repository_identity, base_commit, task_id, task_contract_digest, adapter_descriptor_digest, adapter_target_config_digest, pb_decision_digest, authority_freshness_digest, runtime_posture_digest}; `pb_decision_digest` over the Gate-6 decision evidence; `runtime_posture_digest` = `RuntimeEnforcementPosture.digest()`; `authority_freshness_digest` = `projection.freshness_verdict_digest or projection.evidence_digest()` |
| **Authority meaning of a positive result** | Per the class docstring: "an `ALLOW` would mean only 'Runtime Enforcement would permit the invocation if execution capability existed'; it is **not** runtime capability, not process containment (Gate 8), not durable authority consumption (Gate 9), and not dispatch (Gate 10)." |
| **Failure semantics** | Fail closed on any unexpected exception (`gate7_internal_error_fail_closed`), no partial output; a negative `Gate7Result(decision="DENY")` is a structured audit record carrying `matched_no_go_ids` / `causing_reason_ids` — "a downstream gate MUST NOT treat it as partial success" |
| **Consumption** | **Gate 7 consumes nothing** — no approval / proof / presentation / challenge / nonce / `Gate5Result` / `Gate6Decision` / lifecycle record is created, deleted, or mutated; no `consumption.json`; no Gate-9 primitive is called; idempotently repeatable (attempt 1 → reject, attempt 2 → reject, no state mutation) |
| **Currentness / expiry** | `expires_at = authority_current_time` (the evaluation instant); `evaluated_at = authority_current_time`; the docstring §21 note: "context/lifecycle-based, not wall-clock … a future Gate 8 MUST re-run Gate 7 rather than reuse a `Gate7Result`" |
| **Persistence** | none — `Gate7Result` is ephemeral, `__reduce__` raises, identity-only `==`/`hash` |

### 4.2 Reason it cannot produce a usable positive result today (two independent walls)

1. **Wall A — POL-005 hard stop upstream.** The real `Gate6Decision` for a truthful non-simulation `runtime_dispatch` request is `DENY` (`causing_policy_ids=("POL-005",)`). Even after N-16-3, POL-005's carve-out applies only to the `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile, which is **productionally unsatisfiable** (N-16-6 resolver admits nothing; N-16-5 gives no trusted `ValidatedAuthorityProjection`). Gate 7's step 2 rejects any non-`ALLOW` decision `(None, ("gate7_pb_decision_not_allow:DENY",))` **before** its own evaluation.
2. **Wall B — matched blocking RE-NOGOs.** Even given a hypothetical `Gate6Decision(decision="ALLOW")`, `resolve_runtime_enforcement_posture()` returns `execution_available == False` and `matched_no_go_ids ⊇ {RE-NOGO-001, RE-NOGO-002, RE-NOGO-010, RE-NOGO-011}`, so step 7's `if not posture.execution_available or blocking_no_gos:` branch fires and returns `Gate7Result(decision="DENY")`.

The positive branch (step 8, `# pragma: no cover - unreachable in production`) is reached only if execution is available **and** no blocking RE-NOGO matches — which cannot happen while the runtime is `not_implemented / Observed / observe / unavailable`.

### 4.3 The positive branch already exists — N-16-4 is fundamentally a **contract-freeze**, not a green-field build

`runtime_dispatch_gate7.py` **already** contains a complete, sealed, non-serializable, registry-provenanced `Gate7Result(decision="ALLOW", …)` construction (lines 678–694). The downstream chain **already** consumes it: Gate 8 binds `_gate7_result_digest(gate7_result)` into the containment evidence; Gate 9 writes `runtime_enforcement_binding = {verdict: gate7_result.decision, expires_at: gate7_result.expires_at, …}` into the durable `consumption.json`; Gate 10 pre-effect eligibility requires `is_gate7_result(gate7_result)` + `gate7_result.decision == "ALLOW"` + `gate8_result.gate7_result_digest == _gate7_result_digest(gate7_result)` + `record.runtime_enforcement_binding.verdict == "ALLOW"` + `re_expires_at > authority_current_time`.

**What is missing is not code — it is a frozen contract that governs what that positive object means, how its trust is anchored, how long it is valid, and what its identity is.** RDGO-001 §8 gives one paragraph; there is no dedicated `Gate7Result` schema/semantics contract equivalent to PBNDE-001. N-16-4 supplies it, and (the recommended `.1R.25`) makes the positive branch a *reachable* production path once the upstream trusted inputs exist.

### 4.4 Finding N-16-4-1 (non-blocking, feeds `.1R.25`) — the current `expires_at` model is unusable for a real positive path

`runtime_dispatch_gate7.py` sets `expires_at = authority_current_time` (the evaluation instant). `runtime_dispatch_gate10_eligibility.py` step 11 requires `re_expires_at > authority_current_time` **strictly**. If Gate 10 ran at the same wall-clock string, a real positive `Gate7Result` would be **immediately expired** and rejected `gate10_re_decision_expired`. The current code is internally consistent only because the positive path is unreachable. §16 of this plan freezes the replacement currentness model (a **generational/currentness condition** carried alongside a bounded wall-clock upper bound), and §57 assigns its implementation to `.1R.25`.

---

## 5. Structural vs. temporary negative behavior (phase prompt §7) — CANONICAL MATRIX #2 (§70.2)

Every current Gate-7 denial condition, classified. **N-16-4 does not turn any existing `DENY` into an `ALLOW`.** It defines a *new positive path that only opens when every predicate below that is "temporary" has been independently satisfied by a later prerequisite.*

| # | Denial condition (source) | Classification | Owner of any future change |
|---|---|---|---|
| D1 | `gate7_untrusted_gate6_decision` — not an exact `run_gate6_permission_broker` object | **STRUCTURAL / MUST REMAIN** | — (permanent provenance wall) |
| D2 | `gate7_pb_decision_not_allow:<value>` — Gate-6 decision is `DENY` / `HUMAN_REVIEW` / non-`ALLOW` | **OWNED BY LATER PREREQUISITE** — becomes non-triggered only when N-16-3's `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile is satisfiable, which needs N-16-5 (trusted projection) + N-16-6 (admission) | N-16-5, N-16-6 (Gate 6 remains the sole owner of the PB decision) |
| D3 | `gate7_untrusted_gate5_result` — not an exact `run_gate5` object | **STRUCTURAL / MUST REMAIN** | — |
| D4 | `gate7_invocation_binding_mismatch` — `invocation_id`/`attempt_id` disagree across Gate 5 / Gate 6 / identity | **STRUCTURAL / MUST REMAIN** | — (RDGO §10a identity wall) |
| D5 | `gate7_invalid_identity` / `_invalid_construction_input` / `_invalid_authority_current_time` — structural input guards | **STRUCTURAL / MUST REMAIN** | — |
| D6 | `gate7_stale_validated_authority_projection` — projection not (or no longer) trusted + revalidating at Gate 7's point of use | **STRUCTURAL / MUST REMAIN** — but the *reachability* of a projection that revalidates depends on N-16-5 | N-16-5 (deterministic auth is NON_REAL → `validate_approval` hard-stops → no valid `human_authority_binding` today) |
| D7 | `gate7_authority_subject_scope_mismatch` — recomputed `subject_scope_binding_digest` disagrees with the projection | **STRUCTURAL / MUST REMAIN** | — |
| D8 | `gate7_request_currentness_drift:<fact>` — `inputs` fail the canonical construction re-check | **STRUCTURAL / MUST REMAIN** | — (RDGO §15 TOCTOU) |
| D9 | `gate7_runtime_target_ineligible` — `effect_class != "bounded_local_process_dispatch"` or `network_requirement is not False` or malformed target | **STRUCTURAL / MUST REMAIN** — narrows the positive path to exactly the local-CLI-v1 effect class | — (this is the deliberate N-16-4 scope fence) |
| D10 | `gate7_runtime_execution_unavailable` — `posture.execution_available is False` | **TEMPORARY / N-16-4 CANDIDATE for its *positive-path meaning*, resolved by N-16-7** — the flag itself only flips on the governed `Observed → Approved/Executable` transition | N-16-7 (strictly last). N-16-4 defines what a positive result means *given* this is still `False` for the synthetic path; production positive still `DENY`s here until N-16-7 |
| D11 | `gate7_safety_no_go:RE-NOGO-001` (runtime_enforcement_absent) | **TEMPORARY** — this is the very gap N-16-4/`.1R.25` implementation closes for the local-CLI-v1 profile | N-16-4 impl (`.1R.25`) — a real positive Gate-7 evaluation path *is* "a Runtime Enforcement implementation" for this one profile |
| D12 | `gate7_safety_no_go:RE-NOGO-002` (execution_boundary_absent) | **OWNED BY LATER PREREQUISITE** — Slice A/B built the pre-effect boundary; Slice C adds the effect | Slice C (no phase ID) |
| D13 | `gate7_safety_no_go:RE-NOGO-010` (execution_enablement_absent) | **OWNED BY LATER PREREQUISITE** | N-16-7 |
| D14 | `gate7_safety_no_go:RE-NOGO-011` (end_to_end_safety_proof_absent) | **OWNED BY LATER PREREQUISITE** | Slice D (end-to-end IV, no phase ID) |
| D15 | `gate7_safety_no_go:RE-NOGO-003..008` (backend / adapter / shell / apply / rollback / commit-push) | **OWNED BY LATER PREREQUISITE** | N-16-6, Slice C, and the respective governance tracks |
| D16 | `gate7_internal_error_fail_closed` — bare `except Exception` | **STRUCTURAL / MUST REMAIN** | — |

**Conclusion.** No purely-temporary denial can be lifted by N-16-4 in isolation. N-16-4's positive path is `DENY` in production until **every** "OWNED BY LATER PREREQUISITE" row above is closed (N-16-5, N-16-6, N-16-7, Slice C). The only thing N-16-4/`.1R.25` legitimately does now is (a) freeze the meaning/identity/lifetime/trust model of the positive object, and (b) make the positive branch a real, tested, synthetic-only evaluation path with a per-decision RE-NOGO-001 that is *not matched for a fully-satisfied `RUNTIME_DISPATCH_LOCAL_CLI_V1` synthetic profile* — while RE-NOGO-002/010/011 and the capability check keep production `DENY`.

---

## 6. Frozen Gate-7 design decisions carried from `.1R.13.1` (reconstructed from the module docstring + code)

| `.1R.13.1` open question | Frozen decision (byte-current `runtime_dispatch_gate7.py`) | N-16-4 disposition |
|---|---|---|
| §10.4 Freshness re-resolution | Gate 7 re-trusts + revalidates the referenced `ValidatedAuthorityProjection` (`is_trusted_validated_authority_projection` + `revalidate_validated_authority_projection`, which re-runs `validate_approval`); it does **not** re-run `run_gate5` | **KEEP unchanged.** The positive path uses the identical revalidation. |
| §10.7 PB policy-version drift | `Gate6Decision` carries no `policy_version` field (outside the frozen `.1R.13.1` §28 file matrix); drift is covered *transitively* via projection revalidation; `gate7_pb_decision_stale_policy_version` is a reserved id for a future `Gate6Decision` shape | **KEEP unchanged.** REPRC-001 records that a positive result binds `pb_decision_digest` (over the Gate-6 evidence incl. its decision reason and causing policy ids) so any PB re-evaluation with a different outcome yields a different digest and invalidates the result. |
| §14 Runtime-posture source | Always resolved internally from `runtime_introspection` + the design-only `runtime_enforcement_safety_authorization` DEFAULT flag tables; no caller parameter; one coherent snapshot per evaluation | **KEEP unchanged.** REPRC-001 binds `runtime_posture_digest` into the result identity; the synthetic positive path substitutes the posture resolver the same test-boundary way Gates 8–10 substitute their upstream provenance (see §25). |
| §21 Expiry / single-attempt | `expires_at = evaluation instant`; "invalid the moment any bound input, the PB decision digest, the authority freshness digest, or the runtime posture changes"; single-attempt enforced structurally (exact-object registry + bound digests), no durable "attempt consumed" state | **EVOLVE (N-16-4-1).** Keep the structural single-attempt model; replace the "expires_at = now" placeholder with the §16 currentness model (generational binding + bounded wall-clock upper bound) so a real Gate 10 can consume it within the same governed sequence. |

---

## 7. Full RDGO-001 v3.1 projection Gate 7 must evaluate (phase prompt §8) — CANONICAL MATRIX #4 (§70.4)

Reconstructed from RDGO-001 v3.1 §8 items 1–4, §10 items 1–9, §10a, §15, and the byte-current `evaluated_input_digest` composition in `run_gate7_runtime_enforcement`. **This list is authoritative for `.1R.25`; it is not assumed complete — `.1R.25` re-derives it against the then-current source.**

| Projected fact | In the current `evaluated_input_digest`? | Trusted producer | Currentness owner |
|---|---|---|---|
| `invocation_id` | Yes | Gate 2 coordinator (`RuntimeDispatchIdentity`) | immutable (RDGO §10a) |
| `attempt_id` | Yes | Gate 2 coordinator | immutable |
| `idempotency_key` | Yes | Gate 2 coordinator (canonical content digest) | immutable |
| `subject_scope_binding_digest` | Yes (recomputed via `_expected_subject_scope_binding_digest`) | recomputed by Gate 7 from `identity` + `inputs`; compared to the projection | Gate 7 (live recompute) |
| task/repository authority (`repository_identity`, `base_commit`, `task_id`, `task_contract_digest`) | Yes | `RuntimeDispatchRequestConstructionInput` + `_validate_construction_inputs` | Gates 5/8/9 re-read; Gate 7 re-checks construction |
| PB decision binding (`pb_decision_digest` over decision / decision_reason / causing_policy_ids / matched_no_go_ids / requires_human / simulation_only / implementation_status / request_id / invocation_id / attempt_id) | Yes | `Gate6Decision` via `is_gate6_decision` | Gate 6 (exclusive PB-policy owner) |
| human-authority lineage (`authority_freshness_digest` = `projection.freshness_verdict_digest`) | Yes | `Gate5Result.projection`, re-trusted + revalidated | Gate 5 create / Gate 7 revalidate / Gate 9 consume |
| runtime target (`runtime_target_id`) | Yes | `inputs.runtime_target_id` (bounded string, ≤128) | Gates 2/4/8 |
| requested capability (`requested_capability`) | Yes | `inputs.requested_capability` | Gate 4 static / Gate 8 live |
| adapter identity/class (`adapter_descriptor_digest`, `adapter_target_config_digest`) | Yes | `inputs.adapter_descriptor_binding` | Gates 4/8 (descriptor pin) |
| adapter admission evidence/class (`admission_record_digest`, `admission_class`) | **No — NOT in the current `evaluated_input_digest`** | N-16-6 `SupplyChainAdmissionResolver` (via the trusted builder) | **N-16-6** — **finding N-16-4-2 (non-blocking):** `.1R.25` SHOULD add `adapter_descriptor_binding.admission_record_digest` / `admission_class` to the Gate-7 `evaluated_input_digest` so a positive Gate-7 result is bound to the exact admission binding it evaluated (defence in depth; today the digest is bound at Gate 6 and re-checked at Gate 8/10). This is an *additive* internal binding, not an N-16-6 implementation. |
| effect/execution class (`effect_class == "bounded_local_process_dispatch"`) | checked (step 4, not hashed separately — folded into the construction re-check) | `inputs.effect_class` | Gate 7 scope fence (D9) |
| filesystem containment (`filesystem_scope_ref`) | via `subject_scope_binding_digest` / construction re-check | `inputs` | Gate 8 (establishes actual containment) |
| network prohibition (`network_requirement is False`) | checked (step 4) | `inputs.network_requirement` | Gates 4/8/10 |
| credential prohibition | structural (PBRD §6 defines no credential field) + Gate 10 `gate10_effect_plan_requires_credentials` | construction | Gate 8/10 |
| fixed argv | descriptor-pinned; Gate 8 `_hash_file` + argv vector | descriptor/config | Gate 8 |
| shell prohibition | structural (no caller shell string field anywhere) | construction | Gate 8 "refusal of any caller-supplied shell/command string" |
| idempotency identity | `idempotency_key` (above) | Gate 2 | immutable |
| authority-generation / currentness evidence | **No — NOT in the current Gate-7 result** (Gate 9 captures `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`; Gate 10 re-derives) | HPAC-001 v2.1 HPAC-REQ-098 | Gate 9 capture / Gate 10 re-read — **§16 folds a currentness token into REPRC-001** |
| Gate-5/6 lineage | `invocation_id`/`attempt_id` equality checks | Gates 5/6 | Gate 7 |
| no-go facts | `posture.matched_no_go_ids` (per-decision subset) | `runtime_enforcement_safety_authorization` | Gate 7 |

---

## 8. Gate-6 consumption wall (phase prompt §9) — CANONICAL MATRIX #6 (§70.6)

RDGO-001 v3.1 §8 "PB policy ownership (v3.1 clarification — V-13-3-1)": *PB policy evaluation is owned exclusively by gate 6. Gate 7 (and gate 9) revalidate authority currentness and runtime-enforcement posture … Neither gate 7 nor gate 9 re-runs PB policy.*

| Requirement | How the current code satisfies it | N-16-4 disposition |
|---|---|---|
| Gate 7 must **consume** an already-produced Gate-6/PB outcome, not re-derive it | `is_gate6_decision(gate6_decision)` — exact object from `run_gate6_permission_broker`; a caller-built / reconstructed / `deepcopy` / serialized / bare `decision="ALLOW"` object fails closed | KEEP. REPRC-001 §"trusted inputs" freezes this as MUST. |
| Must **not** re-run PB policy independently | Gate 7 imports no `PolicyRegistry` / `_compose` / POL-* rule; it reads only `gate6_decision.pb_decision.*` fields | KEEP + freeze as an explicit REPRC-001 invariant (`REPRC-INV-004`). |
| Must **not** manufacture PB `ALLOW` | The only path past step 2 requires `gate6_decision.decision == "ALLOW"` by exact string equality on a registry-provenanced object; no code converts `DENY`/`HUMAN_REVIEW` | KEEP. |
| Must **not** reinterpret human approval as PB permission | Gate 7 reads `gate5_result.projection` for *authority currentness*, never as a permission grant; POL-004's `HUMAN_REVIEW` is a Gate-6 outcome that stops the flow before Gate 7 | KEEP. |
| Must **not** drop causing policy IDs or PB decision identity | `_pb_decision_digest` hashes `causing_policy_ids`, `matched_no_go_ids`, `decision_reason`, `request_id`, `invocation_id`, `attempt_id` | KEEP — the digest is part of the positive result's identity (§13). |
| Must **not** accept a caller boolean `pb_allowed=True` as authority | There is no such parameter; the decision comes only from the trusted `Gate6Decision` object | KEEP + freeze (`REPRC-INV-005`). |

**Exact trusted Gate-6 output Gate 7 consumes:** the `Gate6Decision` object returned by `run_gate6_permission_broker`, carrying `pb_decision` (with `decision`, `decision_reason`, `causing_policy_ids`, `matched_no_go_ids`, `requires_human`, `simulation_only`, `implementation_status`), `request_id`, `invocation_id`, `attempt_id`. Provenance is established by `is_gate6_decision` (identity-registry membership), never by shape.

---

## 9. Positive Gate-7 result — exact frozen meaning (phase prompt §10) — CANONICAL MATRIX #9 partial

**Frozen semantic form (REPRC-001 §2):**

> A positive Gate-7 result (`Gate7Result(decision="ALLOW", …)` with `is_gate7_result(...) == True`) asserts **exactly**:
> *"The exact bound `runtime_dispatch` invocation/attempt identified by this result's `invocation_id` / `attempt_id` / `evaluated_input_digest`, as evaluated at `evaluated_at` against the Gate-6 decision digest `pb_decision_digest`, the Gate-5 authority-freshness digest `authority_freshness_digest`, and the runtime posture `runtime_posture_digest`, satisfies Runtime Enforcement constraints sufficiently to **proceed to the next governed gate (Gate 8)** — provided every currentness condition in §16 still holds at the point of use."*

**Explicitly NOT (frozen negative list, REPRC-001 §2.1):**

- not permission to execute
- not permission to dispatch
- not runtime capability / adapter availability
- not effect authorization
- not human authority (does not create, consume, or refresh it)
- not PB permission (does not create or replace the Gate-6 decision)
- not a `DispatchEnvelope` and not a substitute for the RDGO §11 Gate-10 read-back
- not durable — it is ephemeral evaluation evidence; the durable truth is Gate 9's `consumption.json` `runtime_enforcement_binding`, which every later consumer re-reads

**Vocabulary decision:** keep `decision="ALLOW"` (Option A of §11), because the entire downstream chain (Gates 8/9/10) already tests `gate7_result.decision == "ALLOW"` by exact string equality and RDGO-001 §8's own text says "Runtime Enforcement ALLOW". The non-authority semantics are carried by (a) the `is_gate7_result` provenance wall, (b) the `__reduce__`-raises non-serializability, (c) the explicit REPRC-001 §2.1 negative list, and (d) the fact that every downstream gate independently re-validates. Overloading is contained by making REPRC-001 the single normative home of "what ALLOW here means".

---

## 10. Result-vocabulary options A–D (phase prompt §11) — CANONICAL MATRIX #11 (§70.11)

| Option | Description | Verdict | Reason |
|---|---|---|---|
| **A — reuse existing `ALLOW` / `DENY`** | Positive result is `Gate7Result(decision="ALLOW")`, bounded by explicit non-authority semantics in REPRC-001 | **SELECTED** | Zero downstream churn: Gates 8/9/10 already branch on `decision == "ALLOW"` by exact string equality; RDGO-001 §8 already says "Runtime Enforcement ALLOW"; `GATE7_DECISION_VALUES` is already `{"ALLOW","DENY"}`. The non-bearer / non-authority meaning is fully carried by provenance + non-serializability + the REPRC-001 negative list. Lowest-risk, no contract-incompatible change. |
| **B — `ELIGIBLE` / `SATISFIED` vocabulary** | Rename the positive verdict to avoid overloading `ALLOW` | **REJECTED** | Requires changing `GATE7_DECISION_VALUES`, the `Gate7Result.__init__` validation, and the `decision == "ALLOW"` check in **three** downstream coordinators + their frozen IV suites — a cross-module breaking change for a purely cosmetic gain. RDGO-001 §8's own frozen text uses "ALLOW". The overloading risk is real but is better mitigated by a dedicated contract (REPRC-001) than by a rename that ripples through frozen gates. |
| **C — typed `RuntimeEnforcementSatisfied` result** (decision + non-transferable bound evidence) | A distinct result type separate from `Gate7Result` | **REJECTED** | `Gate7Result` **already is** this typed, sealed, non-transferable, digest-bound object. Adding a second type means Gates 8/9/10 must accept both, doubling the provenance surface. The "typed bound evidence" requirement is met by enriching `Gate7Result` (add a currentness token — §16), not by a new type. |
| **D — keep DENY-only Gate 7 + separate prerequisite certificate** | Gate 7 never emits a positive result; a separate object carries "RE satisfied" | **REJECTED** | Introduces a new authority-bearing artifact between Gate 7 and Gate 8 — precisely the "extra bearer token" the phase prompt §2 forbids. It also contradicts RDGO-001 §8 ("Its positive decision is single-attempt, expiring …") and §10 item 7 (Gate 9 records the Gate-7 *verdict*). The DispatchEnvelope (Slice A) is already the only pre-effect binding artifact and it sits at Gate 10, after Gate 9 — not between 7 and 8. |

**Selected: Option A.** Rejected: B, C, D (each explicitly, above).

---

## 11. Non-bearer trust model (phase prompt §12) — CANONICAL MATRIX #12 partial

The positive Gate-7 object must never become transferable bearer authority. Mechanisms analyzed and the frozen ownership of trust:

| Mechanism | Present today? | Frozen role in REPRC-001 |
|---|---|---|
| process-local trusted-result registry (`_GATE7_RESULTS`, keyed by `id(self)`) | **Yes** | **PRIMARY trust anchor.** `is_gate7_result(x)` = `isinstance(x, Gate7Result) and x in _GATE7_RESULTS`. Only `run_gate7_runtime_enforcement`'s completed-evaluation return path inserts. `shape != provenance`. |
| canonical sealed object (`_GATE7_RESULT_CONSTRUCTOR_SEAL`) | **Yes** | Rejects direct construction — `Gate7Result(...)` without the seal raises `TypeError`. |
| exact invocation/attempt binding | **Yes** (`invocation_id`, `attempt_id`, `request_id`, `evaluated_input_digest`) | Frozen as MUST — a result for `(A,1)` carries `(A,1)` and every downstream gate checks equality against `identity`. |
| generation / currentness resolver | **No** (only `expires_at = now`) | **ADDED by `.1R.25` per §16** — a `currentness_binding` digest/marker over the durable authority-generation vector as-of evaluation, which Gate 8/9/10 re-derive and compare. |
| monotonic creation store | not required | The result is ephemeral; no durable "created at" store. Gate 9's `consumption.json` is the durable record. |
| consumer-side live recomputation | **Yes** (Gate 8 recomputes `_gate7_result_digest`; Gate 10 re-reads the durable `runtime_enforcement_binding` and re-derives the authority-generation vector) | Frozen as MUST for every consumer. |
| one-time consumption | structural (single-attempt via `attempt_id`; Gate 9 consumes the *approval*, not the Gate-7 result) | The Gate-7 result itself is never "consumed" — it is re-evaluated. Gate 9's `dispatch_attempted` marker is the at-most-once guard. |
| no serialization as authority | **Yes** (`__reduce__` raises; `to_reference_document`-style dict projections, if added, grant nothing) | Frozen as MUST — REPRC-001 §5 "the durable truth is `consumption.json`; a serialized `Gate7Result` is inert". |

**Which mechanism owns trust (frozen):** the **process-local exact-object identity registry `_GATE7_RESULTS`**, backed by the constructor seal and the non-serializable / identity-only `==`/`hash`. Everything else (digests, invocation binding, currentness token) is *content that a consumer re-verifies*, not the trust root. This is byte-identical to how `Gate5Result` / `Gate6Decision` / `Gate8Result` / `Gate9Result` / `DispatchEnvelope` already work — N-16-4 adds no new trust primitive, it documents and freezes the existing one.

**F7 boundary (carried verbatim, threat model NOT broadened):** the registry resists caller-supplied **data** forgery (reconstruction, copy, serialized clone, duck-typed lookalike), **not** arbitrary same-process Python code execution. Same-account autonomous-agent assumption. No UID / username / process-ownership / stdio / Git identity / PCAE session identity / producer identity is trusted.

---

## 12. Result identity (phase prompt §13)

**Frozen (REPRC-001 §3).** The positive Gate-7 result's logical identity is the tuple of digests it already carries, made explicit as `runtime_enforcement_result_id`:

```
runtime_enforcement_result_id = compute_canonical_digest({
    "invocation_id":            identity.invocation_id,
    "attempt_id":               identity.attempt_id,
    "idempotency_key":          identity.idempotency_key,
    "pb_decision_digest":       <_pb_decision_digest(gate6_decision)>,
    "evaluated_input_digest":   <the existing §7 composition>,
    "authority_freshness_digest": <projection.freshness_verdict_digest or evidence_digest()>,
    "runtime_posture_digest":   <RuntimeEnforcementPosture.digest()>,
    "currentness_binding":      <§16 authority-generation token as-of evaluation>,   # NEW in .1R.25
    "reprc_contract_version":   "REPRC-001/1.0",
})
```

**Not frozen as the exact formula** — `.1R.25` derives the repository-compatible identity from the then-current `evaluated_input_digest` composition and adds `runtime_enforcement_result_id` as a new `Gate7Result.__slots__` field (additive; the existing `evaluated_input_digest` stays). The digest MUST include `reprc_contract_version` so a contract-version change invalidates every prior result.

---

## 13. Invocation/attempt specificity (phase prompt §14) — hard requirement, already met, frozen

A positive Gate-7 result for `invocation=A, attempt=1` MUST NOT validate for `invocation=A, attempt=2`, `invocation=B, attempt=1`, or any copied/transplanted request.

**Current enforcement (byte-current, three independent layers):**
1. `is_gate7_result(x)` — a copy / `deepcopy` / reconstruction of the `(A,1)` result is a different object, not a `_GATE7_RESULTS` member → `False`.
2. Gate 8 / Gate 9 / Gate 10 each check `gate7_result.invocation_id == identity.invocation_id` and `gate7_result.attempt_id == identity.attempt_id` against the *live* `identity` object, and `gate7_result.request_id == gate6_decision.request_id`.
3. `_gate7_result_digest(gate7_result)` (bound into `Gate8Result` and thence the durable containment evidence and `consumption.json`) hashes `invocation_id`, `attempt_id`, `request_id`, `evaluated_input_digest` — a transplanted result produces a digest mismatch at `gate10_gate7_lineage_mismatch`.

**Frozen as REPRC-001 §4 (`REPRC-INV-001`)** with the §34 replay matrix as its test obligation.

---

## 14. Single-attempt semantics and ordering vs. Slice B (phase prompt §15) — CANONICAL MATRIX #9 partial (downstream-gate relationship)

**Slice-B lifecycle (RDGO-001 §17; `runtime_dispatch_attempt_lifecycle.py`):** `PREPARED → EFFECT_ATTEMPT_STARTED → {RECEIPT_CAPTURED | DISPATCH_UNCERTAIN | DISPATCH_NOT_STARTED}`; no automatic retry; `dispatch_attempted` durably recorded at Gate 9 is the at-most-once guard.

**Frozen ordering of Gate 7 relative to the rest (REPRC-001 §6):**

```
Gate 2 mints invocation_id / attempt_id / idempotency_key
Gate 3 human authority creation
Gate 4 static preflight
Gate 5 approval validation  -> Gate5Result (+ ValidatedAuthorityProjection)
Gate 6 Permission Broker    -> Gate6Decision
Gate 7 Runtime Enforcement  -> Gate7Result  <-- runs HERE, over Gate 5/6 outputs, BEFORE any RuntimeInvocationRecord
Gate 8 process containment  -> Gate8Result  (binds _gate7_result_digest)
   [ RuntimeInvocationRecord PREPARED — Slice B mirror created here, non-authoritative ]
Gate 9 durable pre-dispatch record + atomic approval consumption
       -> consumption.json item 7 runtime_enforcement_binding {verdict, expires_at, evaluated_input_digest, decision_digest}
Gate 10 pre-effect eligibility (RDGO §11 six-item read-back) -> DispatchEnvelope
   [ RuntimeInvocationRecord EFFECT_ATTEMPT_STARTED — Slice B, immediately before the (absent) effect ]
Gate 10 adapter dispatch  <-- FIRST EXTERNAL EFFECT — Slice C, no phase ID
```

Gate 7 runs **once per `attempt_id`**, before the `RuntimeInvocationRecord` exists, and is **re-run** (not reused) by Gate 8 and Gate 10 (each re-derives / re-checks). It creates no lifecycle state. A new `attempt_id` (fresh Gate-2 pass, fresh approval) means a fresh Gate-7 evaluation. **Frozen: Gate 7 never reads or writes the Slice-B `RuntimeInvocationRecord`.**

---

## 15. Gate-7 result lifetime (phase prompt §16) — CANONICAL MATRIX #8 (§70.8)

| Property | Frozen decision (REPRC-001 §7) |
|---|---|
| **Creation time** | `evaluated_at` = the `authority_current_time` string passed to `run_gate7_runtime_enforcement` |
| **Expiry / currentness condition** | **Dual bound.** (a) a *generational currentness condition*: the result is invalid the moment `pb_decision_digest`, `authority_freshness_digest`, `runtime_posture_digest`, `evaluated_input_digest`, or the §16 `currentness_binding` no longer matches a fresh re-derivation; (b) a *bounded wall-clock upper bound*: `expires_at` = the earlier of the Gate-5 projection's expiry verdict time and `evaluated_at + REPRC_MAX_RESULT_TTL` (a small contract constant, e.g. 300 s), so a stalled sequence cannot carry a stale positive result forward. **Wall-clock alone is insufficient** — generational currentness is the real requirement; the TTL is a backstop. |
| **Generation binding** | `currentness_binding` = a digest over the current authority-generation vector (principal / credential / approval / lifecycle generation tokens — the same `HPAC-AUTHORITY-GENERATION-SNAPSHOT` markers Gate 9 captures), as-of evaluation. Restart-reconstructible; no wall clock / nonce / PID. |
| **Mutable-dependency revalidation** | Gate 8 re-runs Gate 7 (per RDGO §8 "a future Gate 8 MUST re-run Gate 7"); Gate 9 re-derives the full revalidation battery; Gate 10 re-reads the durable `runtime_enforcement_binding` and re-derives the authority-generation vector. |
| **Invalidation events** | any PB re-evaluation with a different outcome; principal / credential / approval / lifecycle revocation or generation bump; approval expiry; runtime-posture change (e.g. an `Observed → Approved` transition would *change* `runtime_posture_digest` and invalidate a result computed under the old posture); any `inputs` drift (`gate7_request_currentness_drift`); projection revocation (`gate7_stale_validated_authority_projection`). |
| **Whether wall-clock expiry is required or insufficient** | **Insufficient alone.** Required as a backstop only. The frozen model is generational-first. |

---

## 16. Mutable-dependency currentness (phase prompt §17) — CANONICAL MATRIX #8 (§70.8, continued)

| Dependency | Frozen classification (REPRC-001 §8) |
|---|---|
| PB policy version | **owned by another gate** (Gate 6, exclusively). Gate 7 binds `pb_decision_digest`; a stale `policy_version` is resolved by re-entering Gate 6, never by Gate 7. Advisory reason `policy_drift_requires_fresh_pb_re_evaluation` only. |
| runtime target admission (N-16-6) | **snapshot-bound at evaluation + live-revalidated later.** Gate 7 binds `admission_record_digest` (finding N-16-4-2 — additive); Gate 8/10 re-check the admission binding live. Gate 7 does not perform an admission lookup (see §22). |
| repository state (HEAD, fingerprint, task) | **snapshot-bound at evaluation (`inputs` construction re-check) + live-revalidated at Gates 8/9/10.** |
| authority generation (principal / credential / approval / lifecycle) | **snapshot-bound into `currentness_binding` + must invalidate the Gate-7 result** if it drifts before the result is used. Gate 8 re-runs Gate 7 (fresh snapshot); Gate 9 `S1`/`S2` re-check; Gate 10 re-derives + compares against the durable snapshot. |
| filesystem containment assumptions | **owned by Gate 8** (establishes actual containment); Gate 7 only checks `network_requirement is False` + the scope digest. |
| runtime capability (`execution_availability`) | **owned by Gate 7 for its own decision + re-read by Gate 10** (`gate10_runtime_capability_not_unavailable`). Bound into `runtime_posture_digest`. N-16-7 owns any change to the flag. |
| adapter registry | **owned by Gate 10 / Slice C** (`adapter_registration` re-checked at the dispatch call site). Gate 7 binds only the descriptor/config digests. |
| no-go registry | **snapshot-bound into `runtime_posture_digest`** (the per-decision `matched_no_go_ids`); the registry itself is a frozen contract. A registry change would change `RuntimeEnforcementPosture.digest()` and invalidate the result. |
| task scope | **snapshot-bound (`task_id`, `task_contract_digest` in `evaluated_input_digest`) + live-revalidated at Gates 5/8/9.** |

---

## 17. Gate-8 relationship (phase prompt §18) — CANONICAL MATRIX #9

**RDGO-001 v3.1 §9:** Gate 8 is owned by Shell Gate / an equivalent process-containment mechanism; "it is not an extension of PB's policy decision". Three-layer containment model: direct validation → canonical commitment → gate-9 recomputation.

**Frozen (REPRC-001 §9):**
```
Gate-7 ALLOW  ->  Gate-8 still independently required
```
- Gate 8 independently: re-resolves the descriptor/config, resolves + hashes the exact executable, establishes cwd / argv / env allowlist / child-process prohibition / resource limits, confirms network denied + no credentials, and **binds `_gate7_result_digest(gate7_result)` into `containment_evidence_digest`**.
- Gate 8 rejects a trusted **negative** `Gate7Result(decision="DENY")` at `gate8_gate7_decision_not_allow` **before** any Shell Gate evaluation. No code path converts a non-`ALLOW` Gate-7 result into a positive Gate-8 result.
- **No duplicated responsibility:** Gate 7 decides *whether to invoke*; Gate 8 decides *how the one permitted process may be launched* and proves containment. Gate 7 performs no executable resolution, no cwd/env establishment, no live preflight. The one deliberate overlap — both re-check `network_requirement`/credentials — is intentional defence in depth and is documented as such.

---

## 18. Gate-9 relationship (phase prompt §19)

**RDGO-001 v3.1 §10:** Gate 9 atomically persists the minimum effect-bound evidence and **consumes the approval + proof + presentation + challenge** in one create-only write; item 7 records the Runtime Enforcement binding.

**Frozen (REPRC-001 §10):**
```
Gate-7 result  !=  authority consumption
```
- Gate 9 remains the **sole owner** of authority consumption. Gate 7 consumes nothing.
- Gate 9 re-derives the Gate-7 lineage (`is_gate7_result` + `decision == "ALLOW"` + `gate8_result.gate7_result_digest` cross-check) and writes `runtime_enforcement_binding = {decision_id, decision_digest, verdict, expires_at, evaluated_input_digest}` into `consumption.json` — a **reference**, not a re-run.
- A positive Gate-7 result does not make Gate 9's atomic consumption optional, and a failed Gate 9 does not "un-decide" Gate 7 (Gate 7 has no durable state to roll back).
- `.1R.25` adds `currentness_binding` to the fields Gate 9 records (so Gate 10's re-derivation has a durable anchor), consistent with RDGO §10 item 9's authority-generation snapshot — **additive, not a Gate-9 behaviour change to items 1–8.**

---

## 19. Gate-10 (pre-effect eligibility / DispatchEnvelope) relationship (phase prompt §20) — CANONICAL MATRIX #9

**Interface direction (frozen, byte-current from `runtime_dispatch_gate10_eligibility.py`):** Gate-10 pre-effect eligibility consumes **both**:
1. the **`Gate7Result` object directly** — `is_gate7_result(gate7_result)` + `gate7_result.decision == "ALLOW"` + `gate8_result.gate7_result_digest == _gate7_result_digest(gate7_result)` (provenance + exact lineage); **and**
2. the **durable `runtime_enforcement_binding`** re-read from `consumption.json` — `re_binding.verdict == "ALLOW"` + `re_expires_at > authority_current_time` (the durable, restart-safe truth).

Gate 10 does **not** re-run RE policy. `matched_no_go_ids` is "a per-decision diagnostic, NOT an authority input — not consulted here".

**Frozen (REPRC-001 §11):**
```
Gate-7 ALLOW  ->  does NOT manufacture a DispatchEnvelope or effect authority
```
The `DispatchEnvelope` is minted only after Gate 10's full 18-step battery (fresh consumption.json read-back, authority-generation re-derivation, capability re-read = exactly `Observed/observe/unavailable`, containment recomputation, executable re-hash). The envelope "authorizes nothing"; `is_dispatch_envelope` proves "process-local provenance only". `.1R.25`'s only Gate-10 obligation is the `expires_at` fix (finding N-16-4-1) so a fresh positive Gate-7 result is not immediately `gate10_re_decision_expired`.

---

## 20. Runtime-capability relationship (phase prompt §21)

**Frozen (REPRC-001 §12).** N-16-7 remains strictly later. N-16-4 introduces **no capability mutation** — `resolve_runtime_enforcement_posture()` stays a pure read of frozen `runtime_introspection` constants; it "registers no capability, enables no backend, promotes no implementation status".

A future positive Gate-7 result under the current production state (`execution_availability == "unavailable"`) still leads to **overall execution unavailable**: Gate 7's own step 7 `DENY`s on `not posture.execution_available` for the production path, and even a hypothetical positive result is rejected downstream at `gate10_runtime_capability_not_unavailable` if capability drifted, or simply never reaches an effect because Slice C has no call site.

`.1R.25` implementation acceptance condition: `pcae runtime inspect` remains `not_implemented / Observed / observe / unavailable`, 0 plugins / 0 capabilities, before and after.

---

## 21. Adapter-admission relationship (phase prompt §22)

**Frozen (REPRC-001 §13).** N-16-6 remains later. Gate 7 **evaluates only the admission evidence already bound by Gate 6** (via the trusted builder's `admission_record_digest` / `admission_class` on `adapter_descriptor_binding`, computed inside `build_runtime_dispatch_permission_broker_request`). Gate 7 performs **no live admission lookup** and calls **no `SupplyChainAdmissionResolver`**. Live admission re-checks are deferred to Gate 8 / Gate 10 / Slice C.

Finding N-16-4-2 (§7): `.1R.25` SHOULD *bind* `admission_record_digest` / `admission_class` into the Gate-7 `evaluated_input_digest` (defence in depth) — this is an additive internal digest field, **not** an N-16-6 admission-store implementation and **not** a new resolver call.

---

## 22. Real-human-authority relationship (phase prompt §23)

**Frozen (REPRC-001 §14).** N-16-5 remains later. Gate 7 MUST NOT:
- perform FIDO2 / WebAuthn / CTAP;
- authenticate the human again;
- treat NON_REAL evidence as real;
- consume approval.

Gate 7 **may consume only already-trusted lineage**: it re-trusts + revalidates the `ValidatedAuthorityProjection` referenced by the `Gate5Result` (`is_trusted_validated_authority_projection` + `revalidate_validated_authority_projection`, which re-runs `validate_approval`). Today `validate_approval` hard-stops on a NON_REAL lineage, so **no valid `human_authority_binding` for a real request exists** — the production positive Gate-7 path is unreachable through this wall until N-16-5. The synthetic positive path (§25) substitutes a trusted projection the same test-boundary way Gates 8–10 do.

---

## 23. Current no-go registry analysis (phase prompt §24) — CANONICAL MATRIX #5 (§70.5)

| No-Go ID | Current meaning | Gate-7 relevance | Can ever become non-triggered? | Which prerequisite owns the change? | N-16-4 effect |
|---|---|---|---|---|---|
| RE-NOGO-001 | No Runtime Enforcement Implementation | **per-decision** — matched today (auth flag `False`) | Yes, for the exact `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile | **N-16-4 impl (`.1R.25`)** — a real positive Gate-7 evaluation path *is* the RE implementation for that one profile | The auth flag that maps to RE-NOGO-001 flips to `True` **only** for a fully-satisfied synthetic profile; production stays `False` |
| RE-NOGO-002 | No Execution-Capable Boundary | per-decision — matched | Yes | Slice C (the `adapter.dispatch()` call site) | unchanged — still matched after N-16-4 |
| RE-NOGO-003..008 | backend / adapter / shell / apply / rollback / commit-push governance absent | per-decision — matched | Yes | N-16-6, Slice C, respective governance tracks | unchanged |
| RE-NOGO-009 | No audit persistence | environmental-readiness (not a per-decision projection) | Yes | execution-enablement readiness process | out of Gate-7 per-decision scope — unchanged |
| RE-NOGO-010 | No Execution Enablement Design | per-decision — matched | Yes | **N-16-7** | unchanged — still matched after N-16-4 |
| RE-NOGO-011 | No End-to-End Runtime Safety Proof | per-decision — matched | Yes | **Slice D** (end-to-end IV) | unchanged — still matched after N-16-4 |
| RE-NOGO-012 | Pre-existing fast-green failures | advisory | none | test hygiene | unchanged |
| RE-NOGO-013 | No Telegram inbound control | environmental-readiness | Yes | outbound-only confirmation design | out of Gate-7 per-decision scope |
| RE-NOGO-014 | task-memory warnings | advisory | none | task hygiene | unchanged |
| RE-NOGO-015..017 | emergency abort / output capture / recovery absent | environmental-readiness | Yes | execution-enablement readiness | out of Gate-7 per-decision scope |
| NG-025 | Execution Boundary Unavailable (`V0_2_EXECUTION_READINESS_NO_GO_GATES.md`) | referenced by POL-005 / POL-013; **not** a `RE-NOGO-*` | annotated (PBNDE-001 §9) — active for every non-sim request except the unsatisfiable `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile; human override `no` | Yes, when the profile becomes satisfiable (N-16-5..7) | **no change in N-16-4** — REPRC-001 references NG-025's existing annotation; no new `RE-NOGO-*` entry created |

**Frozen: N-16-4 weakens no global no-go semantics.** The only movement is RE-NOGO-001's per-decision projection becoming *not-matched for a synthetic fully-satisfied `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile*, while RE-NOGO-002/010/011 keep every production and end-to-end path blocked.

### 23.1 Positive-path no-go semantics (phase prompt §25)

**Frozen (REPRC-001 §15):**
```
any applicable unresolved hard no-go  ->  Gate7Result(decision="DENY")
```
No "trusted narrow profile" shortcut around Runtime Enforcement no-gos. The positive branch is reached **only** when `posture.execution_available is True` **and** `posture.matched_no_go_ids` (the per-decision subset) is **empty**. The environmental-readiness no-gos (009/013/015/016/017) are enforced separately by the execution-enablement readiness process — Gate 7's per-decision projection deliberately does not carry them, and this is not a shortcut (RE No-Go Registry scoping paragraph; `.1R.13.1` §13 correction).

---

## 24. Runtime Enforcement policy composition (phase prompt §26, §27) — CANONICAL MATRIX #3-adjacent

**Frozen (REPRC-001 §16).** Gate 7's evaluation is a **single fail-closed conjunction**, not a multi-rule composition with precedence:

```
structural input validation (steps 1,3,4,5,6)  — any failure -> (None, reason), no Gate7Result
  AND Gate-6 decision == "ALLOW" (step 2)       — else (None, "gate7_pb_decision_not_allow:...")
  AND runtime target eligible (step 4)          — else (None, "gate7_runtime_target_ineligible")
  AND posture.execution_available is True (step 7)
  AND posture.matched_no_go_ids is empty (step 7)
    -> Gate7Result(decision="ALLOW")            [positive branch — synthetic-only until N-16-5..7]
  otherwise
    -> Gate7Result(decision="DENY", matched_no_go_ids=..., causing_reason_ids=...)
```

- **No advisory-constraint channel that can produce a positive result** — advisory reasons (e.g. PB policy drift) are surfaced for audit only, "never a licence to skip a check and never a basis for a positive decision" (RDGO §8).
- **Structural validation strictly precedes the positive decision** (phase prompt §27): any malformed / missing / unknown trusted fact fails closed at steps 1–6 **before** any `Gate7Result` is constructed. **No partial positive object** — the `Gate7Result` is built in one `__init__` call with all fields, inside the seal.
- **Hard blocks only** — there is no weighting, no specificity tier, no override. This mirrors `_compose`'s `DENY > HUMAN_REVIEW > ALLOW` fail-closed model at Gate 6 (PBNDE-001 §5) but Gate 7's is even simpler (binary, single conjunction).

---

## 25. Synthetic / test-only positive Gate-7 path (phase prompt §37)

**Frozen (REPRC-001 §17).** `.1R.25` MUST define a deterministic synthetic positive path so the positive branch is verifiable without enabling execution. It MUST:

- remain **local / in-memory** — a synthetic fully-satisfied `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile via the existing underscore-private test-boundary seams (`_supply_chain_admission_resolver` on the request builder; a test-trusted `ValidatedAuthorityProjection`; a substituted posture resolver returning `execution_available=True` + empty `matched_no_go_ids`) — **exactly** the pattern Gates 5–10 already use (`.1R.16` §23; `runtime_dispatch_gate9.py` docstring);
- **never call an adapter**, never `adapter.dispatch()`, never a `SupplyChainAdmissionResolver` production resolver;
- **never alter capability** — no `Observed → Approved` transition; the production `resolve_runtime_enforcement_posture()` is untouched;
- **never access network / credential / hardware / FIDO2 / WebAuthn / CTAP**;
- be **clearly test-only** — the substitution seam is underscore-private, documented test-only, with no public production parameter that flips the posture or the profile.

The synthetic path proves only: the positive `Gate7Result` *can* be constructed structurally; its identity / currentness binding is well-formed; the downstream chain (Gate 8 digest bind, Gate 9 `runtime_enforcement_binding` write, Gate 10 lineage checks) accepts it; and every replay / stale / forgery challenge in §34 rejects it.

---

## 26. Production positive path after N-16-4 alone (phase prompt §38) — CANONICAL MATRIX #10-adjacent

**Frozen answer:** **After `.1R.25` (N-16-4 implementation) but before N-16-5 / N-16-6 / N-16-7, production Gate 7 CANNOT emit a positive result.** Two independent, currently-insurmountable walls remain:

1. **N-16-5 wall (authority):** `validate_approval` hard-stops on a NON_REAL lineage. There is no path — production or otherwise — to a trusted `ValidatedAuthorityProjection` for a real request, so `Gate5Result` for a real request cannot carry a revalidating projection, so Gate 7 step 5 fails `gate7_stale_validated_authority_projection`. Also, without a valid `human_authority_binding`, the `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile's `P_human_authority_present` / `P_human_authority_binding_valid` predicates fail → POL-013 `DENY` + POL-005 keeps its match → `Gate6Decision(decision="DENY")` → Gate 7 step 2 `gate7_pb_decision_not_allow:DENY`.
2. **N-16-6 wall (admission):** the sole production `SupplyChainAdmissionResolver` is `_NonAdmittingSupplyChainAdmissionResolver` (admits nothing). `P_supply_chain_admission` always fails → same `DENY` cascade.

**And even if both were hypothetically satisfied:** `resolve_runtime_enforcement_posture()` returns `execution_available == False` and `matched_no_go_ids ⊇ {RE-NOGO-002, RE-NOGO-010, RE-NOGO-011}` (N-16-4 only clears RE-NOGO-001 for the synthetic profile) → Gate 7 step 7 `DENY`.

So the precise frozen statement (matching PBNDE-001's precedent that the profile "is unsatisfiable in production"): **production Gate 7 remains DENY-only after N-16-4 alone; a positive result is structurally reachable only on the clearly-labelled synthetic test path.**

---

## 27. Production effect reachability (phase prompt §39, §62) — hard requirement

**Frozen:** Even after a future `.1R.25` implementation:
```
first external effect  =  still UNREACHABLE
```
because N-16-5, N-16-6, N-16-7, and Slice C all remain open, and:
- no `adapter.dispatch()` call site exists anywhere in `src/pcae` (`.1R.16` §24.2 — *absent*, not merely unreachable);
- `RuntimeRegistry` is empty (no real adapter);
- `execution_availability == "unavailable"`;
- Gate 10's `DispatchEnvelope` "authorizes nothing" and there is no consumer that turns it into an effect.

**AST-level zero-effect evidence obligation for `.1R.25`:** the Gate-7 module (and any new REPRC helper module) MUST import no `subprocess` / `socket` / `ssl` / `os.system`/`popen`/`spawn`/`exec*` / `pty` / provider SDK / HTTP client / credential resolver / FIDO2 / WebAuthn / CTAP, and MUST call no Gate-8 / Gate-9-consumption / Gate-10-adapter primitive — enforced by an AST guard in the `.1R.25` suite, exactly as the current `.1R.13.2` suite enforces for `runtime_dispatch_gate7.py`.

---

## 28. Runtime posture during implementation (phase prompt §40)

**Frozen `.1R.25` acceptance condition:** `pcae runtime inspect` = `not_implemented / Observed / observe / unavailable`; `Execution capability: unavailable`; `Maximum plugin capability: observe`; `Permission Broker status: execution_unavailable`; governance posture `non-executing`; 0 plugins / 0 capabilities — **before and after**, byte-identical `runtime_introspection` `CURRENT_*` / `EXECUTION_AVAILABILITY` constants. Any drift is a blocking `.1R.25` regression.

---

## 29. Contract ownership (phase prompt §41, §43) — CANONICAL MATRIX #12 partial

**Candidates evaluated:**

| Candidate | Verdict | Reason |
|---|---|---|
| RDGO-001 evolution only | **INSUFFICIENT alone** | RDGO-001 is a *gate-ordering* contract; §8 is one paragraph. It should carry a clarifying cross-reference (v3.2 MINOR) but is the wrong home for a result schema, trust model, replay matrix, and lifetime semantics. |
| **New dedicated contract `REPRC-001` v1.0** (Runtime Enforcement Positive-Result Contract) | **SELECTED** | Directly analogous to PBNDE-001 v1.0 for N-16-3: a focused contract that freezes the positive `Gate7Result`'s meaning, non-bearer trust model, identity, currentness/lifetime, replay/duplicate/stale behaviour, synthetic path, and the finite downstream-consumer set. Initial freeze (v1.0), not a MAJOR migration of an existing contract → lower risk than POL-005's amendment was. |
| new companion contract (à la PBNDE companion to PBRD) | folded into REPRC-001 | no separate PBRD-analogue exists for Gate 7 to companion; REPRC-001 is standalone. |
| existing no-go contract + additive section | **REJECTED** | The RE No-Go Registry is a stable-ID registry; positive-result semantics do not belong there. §44 confirms no registry change. |
| Phase-102 `RuntimeEnforcementDecision` schema evolution | **REJECTED** | That is the design-only decision-engine contract, not the RDGO Gate-7 `runtime_dispatch` coordinator. Reusing it would conflate two independent models. |

**Selected architecture:** **`REPRC-001` v1.0 (new, dedicated) + RDGO-001 v3.1 → v3.2 (MINOR cross-reference in §8, pointing at REPRC-001 for positive-result semantics).**

### 29.1 Dedicated result-contract decision (phase prompt §43) — CANONICAL MATRIX #7-adjacent

**A new contract analogous to PBNDE-001 IS cleaner — SELECTED.** `REPRC-001` covers: result schema (§45), trust ownership (§11), binding/identity (§12–§13), non-bearer semantics (§2.1, §5), lifetime/currentness (§15–§16), duplicate/replay behaviour (§32–§34), and downstream consumption (§49). Rejected alternatives: folding into RDGO-001 (wrong altitude), folding into PBNDE-001 (PBNDE is a *Permission Broker* contract; Gate 7 is downstream and independent), a No-Go Registry section (wrong home).

---

## 30. Contract versioning adjudication (phase prompt §42) — CANONICAL MATRIX #12 (§70.12)

**Read first (per the `.1R.21` lesson): each contract's own versioning rules.**
- RDGO-001 §21: `MAJOR.MINOR`. MINOR = "re-states verified behaviour and does not reorder a gate, move the first-effect boundary, merge authority/permission/enforcement/containment, weaken freshness, or widen effect scope". MAJOR = incompatible state-machine change or merging the four concerns.
- PBNDE-001 §10 / PBRD-001 §16 precedent: a new dedicated contract is born at v1.0 (initial freeze).
- RE No-Go Registry: "IDs are stable once frozen … Canonical statements amended only via versioned change … Additive only unless dedicated migration phase."

| Artifact | Current version | Proposed change | PATCH / MINOR / MAJOR | Primary-source rationale | Migration required? | IV required? |
|---|---|---|---|---|---|---|
| **REPRC-001** (new) | — | Initial freeze: positive Gate-7 result meaning, non-bearer trust model, identity, currentness/lifetime, replay/duplicate/stale matrix, synthetic path, finite consumer set, invariants REPRC-INV-001..00N | **v1.0 (initial freeze)** | PBNDE-001 v1.0 / PBRD-001 §16 precedent — a focused new contract for a new load-bearing security property is born at v1.0 | N/A (initial) | **Yes** — `.1R.26` (or `.1R.27` if a separate freeze phase — §31) |
| **RDGO-001** | v3.1 | §8: add one clarifying sentence — "The exact schema, non-bearer trust model, identity, currentness/lifetime, and replay semantics of a positive Gate-7 result are frozen by REPRC-001 v1.0; Gate 7 remains a binary whether-to-invoke gate and a positive result remains single-attempt, expiring, subordinate to Gates 8/9/10, and never a bearer token." Optionally the §16 "RE decision" row cross-refs REPRC-001. | **MINOR → v3.2** | RDGO §21 — restatement of verified/frozen behaviour; no gate reorder, no first-effect-boundary move, no merge of the four concerns, no freshness weakening, no effect-scope widening. Exactly the shape of the v3.0→v3.1 normalization. | No (no conforming prior artifact carries different semantics) | Yes — folded into `.1R.26` |
| **RE No-Go Registry** | schema 1.1 | **No change** (see §44) | — | positive-path semantics do not belong in a no-go registry; RE-NOGO-001's per-decision projection behaviour is already contract-correct | — | — |
| **`V0_2_EXECUTION_READINESS_NO_GO_GATES.md`** (NG-025) | (annotated by PBNDE-001 §9) | **No change** — REPRC-001 references the existing annotation | — | NG-025 already annotated for the `RUNTIME_DISPATCH_LOCAL_CLI_V1` carve-out; N-16-4 adds nothing | — | — |
| **PBRD-001 / PBNDE-001 / PBPA-001** | v3.0 / v1.0 / v1.1 | **No change** — Gate 7 is downstream of and independent from PB policy; PBNDE-001 §7 already says "Gate 7 receives the PB decision as an input and independently re-validates" | — | PBNDE-001 §7 downstream-gate independence | — | — |
| **RPAC-001** | v1.0 | **No change** — RPAC-REQ-029 `DispatchEnvelope` is a Gate-10 artifact; REPRC-001 references it, does not modify it | — | — | — | — |

**No MAJOR contract bump.** The only version movement is REPRC-001 v1.0 (initial) and RDGO-001 v3.1→v3.2 (MINOR restatement). This deliberately avoids the `.1R.21` versioning mistake (planning a MINOR that turned out MAJOR): REPRC-001 v1.0 is an initial freeze (unambiguous), and the RDGO change is a pure restatement pointer (clearly MINOR under §21's own enumerated criteria).

---

## 31. Contract-freeze vs. direct implementation sequence (phase prompt §58) — frozen

**Two options under repository precedent:**
- **Path X (N-16-3 precedent):** planning (`.1R.24`) → implementation *including inline contract authorship* (`.1R.25`) → IV (`.1R.26`). N-16-3 did exactly this: `.1R.21` planned, `.1R.22` authored PBNDE-001 v1.0 + PBRD-001 v3.0 inline, `.1R.23` verified. RDGO v2→v3 and PBRD v1.1→v2.0 also carried their contract MAJOR inline in the implementing phase.
- **Path Y (separate freeze):** planning (`.1R.24`) → contract freeze (`.1R.25` — REPRC-001 v1.0 + RDGO v3.2, no code) → implementation (`.1R.26`) → IV (`.1R.27`).

**Frozen decision: Path X (inline), with a strong recommendation to author the REPRC-001 v1.0 text as the *first commit* of `.1R.25`, before any `src/pcae` change, and to treat it as frozen for the rest of that phase.**

Rationale:
- REPRC-001 v1.0 is an **initial freeze**, not a MAJOR migration of an existing security-critical contract. The `.1R.21`/`.1R.22` risk that triggered "strongly consider a separate freeze phase" was POL-005's *amendment* (a MAJOR-in-substance change to a universally-applied hard-DENY rule). REPRC-001 has no such incumbent.
- The RDGO change is a MINOR pointer, not a state-machine change.
- The positive Gate-7 *scaffolding already exists and is already consumed* by three frozen downstream gates — `.1R.25` is mostly "make the existing branch reachable on a synthetic path + add `currentness_binding` + fix `expires_at`", a bounded change.
- A separate freeze phase would add a full governed phase (task, commit, push, finalize, IV) for ~1 contract document with no incumbent to migrate — disproportionate.

**If `.1R.25`'s primary-source review discovers that REPRC-001 must incompatibly change RDGO-001's state machine or merge authority/permission/enforcement/containment (a MAJOR), `.1R.25` MUST STOP and re-adjudicate to Path Y** — exactly as `.1R.22` STOPPED at primary-source review when POL-005's versioning turned out MAJOR.

---

## 32. Duplicate evaluation (phase prompt §32) — CANONICAL MATRIX #8-adjacent

**Frozen (REPRC-001 §18).** If Gate 7 evaluates the same exact invocation/attempt twice under an unchanged posture:
- **deterministic same *decision***: `ALLOW` → `ALLOW` (or `DENY` → `DENY`);
- **new object identity each call**: `run_gate7_runtime_enforcement` constructs and registers a *new* `Gate7Result` each time (byte-current: `_GATE7_RESULTS.add(result)` on every completed evaluation). The two results are `!=` (identity-only equality) but carry identical field values and identical `evaluated_input_digest` / `runtime_enforcement_result_id`.
- **no durable state, no "attempt consumed"**: Gate 7 stays idempotently repeatable (module docstring: "attempt 1 → reject, attempt 2 → reject, no state mutation"; the positive path is symmetric).
- **alignment with Slice-B single-attempt**: the at-most-once guard is Gate 9's `dispatch_attempted` marker keyed by `attempt_id`, not anything Gate 7 owns. Re-evaluation is *only* meaningful before Gate 9; after Gate 9's durable record exists, a second Gate-7 evaluation for the same `attempt_id` is moot (Gate 10 reads the durable `runtime_enforcement_binding`, not a fresh Gate-7 object). `.1R.25` need not reject a duplicate Gate-7 call — it is harmless and produces a logically-identical result.

---

## 33. Serialization / restart behavior (phase prompt §30, §31) — CANONICAL MATRIX #10 (§70.10)

| Question | Frozen decision (REPRC-001 §19) |
|---|---|
| Do positive Gate-7 results survive **process restart**? | **No.** `Gate7Result.__reduce__` raises; the `_GATE7_RESULTS` registry is process-local. |
| Session restart? | **No.** Same. |
| Machine restart? | **No.** Same. |
| Restart invalidation defined? | **Yes, explicitly.** After any restart, the positive Gate-7 evaluation MUST be **re-run** from a freshly re-resolved `Gate6Decision` and `Gate5Result`. The **durable** truth that survives restart is Gate 9's `consumption.json` `runtime_enforcement_binding` (verdict + expiry + `evaluated_input_digest` + `decision_digest`), which Gate 10 re-reads and re-verifies against a fresh authority-generation re-derivation. A `Gate7Result` reconstructed after restart from any serialized form is inert (`is_gate7_result` → `False`). |

**Persistence-model options (phase prompt §31):**

| Model | Description | Verdict |
|---|---|---|
| **Model A — no durable positive-result persistence; recompute Gate 7 after restart** | The `Gate7Result` is ephemeral; the only durable anchor is Gate 9's `consumption.json` (written *after* Gate 7, at a later gate) | **SELECTED** — matches the byte-current architecture exactly; matches `Gate5Result` / `Gate6Decision` / `Gate8Result` (all ephemeral); the durable RE binding at Gate 9 already provides restart-safe truth for the only consumer that runs post-restart (Gate 10). |
| Model B — append-only durable positive-result store bound to invocation/attempt + currentness generation | A new durable store just for Gate-7 results | **REJECTED** — introduces a new durable authority-ish artifact that a restart could resurrect; duplicates what Gate 9's `consumption.json` already records; no consumer needs it (Gate 8 re-runs Gate 7; Gate 10 reads Gate 9's record). |
| Model C — durable evidence record but trusted runtime result recreated after revalidation | Hybrid | **REJECTED** — this *is* effectively Model A + Gate 9's existing `consumption.json`; naming it a separate model adds nothing. Gate 9 already writes the durable evidence; Gate 7 re-runs on demand. |

**Selected: Model A.** Rejected: B, C.

---

## 34. Replay / stale challenge matrices (phase prompt §33, §34) — feeds CANONICAL MATRIX #14

### 34.1 Stale-positive challenge (phase prompt §33) — which component rejects

```
positive Gate7Result  ->  mutate one authority/currentness dependency  ->  downstream acceptance MUST fail
```

| Mutated dependency | Rejecting component (frozen) | Reason id |
|---|---|---|
| PB decision re-evaluated to a different outcome | Gate 8 re-runs Gate 7 → `pb_decision_digest` mismatch → new evaluation; or Gate 10 `re_binding.verdict != "ALLOW"` | `gate10_re_lineage_not_allow` / fresh Gate-7 `DENY` |
| principal / credential / approval revoked | Gate 7 revalidation (`revalidate_validated_authority_projection`); Gate 9 `S1`/`S2`; Gate 10 authority-generation re-derivation | `gate7_stale_validated_authority_projection` / `gate10_authority_generation_drift:<source>` |
| approval expired (wall-clock) | Gate 7 revalidation; Gate 10 projection revalidation | `gate7_stale_validated_authority_projection` / `gate10_stale_validated_authority_projection` |
| runtime posture changed (e.g. `Observed → Approved`) | Gate 7 re-run → different `runtime_posture_digest`; Gate 10 capability re-read | fresh Gate-7 evaluation / `gate10_runtime_capability_not_unavailable` |
| `inputs` drift (HEAD, task, prompt, target) | Gate 7 construction re-check; Gates 8/9/10 re-check | `gate7_request_currentness_drift:<fact>` / `gate10_request_currentness_drift:<fact>` |
| `currentness_binding` no longer matches fresh re-derivation | Gate 8 re-run Gate 7; Gate 10 authority-generation compare | fresh `DENY` / `gate10_authority_generation_drift` |

### 34.2 Replay challenge (phase prompt §34) — all MUST fail

| Replay attempt | Rejecting layer | Outcome |
|---|---|---|
| same result, different `attempt_id` (2 instead of 1) | Gate 8/9/10 `gate*_invocation_binding_mismatch` (`gate7_result.attempt_id != identity.attempt_id`) | reject |
| same result, different `invocation_id` (B instead of A) | Gate 8/9/10 `gate*_invocation_binding_mismatch` | reject |
| same result, changed runtime target | `evaluated_input_digest` mismatch → `_gate7_result_digest` mismatch → `gate10_gate7_lineage_mismatch`; Gate 8 re-run Gate 7 fails construction re-check | reject |
| same result, changed adapter binding | `evaluated_input_digest` mismatch (`adapter_descriptor_digest` / `adapter_target_config_digest`) | reject |
| same result, changed filesystem scope | `subject_scope_binding_digest` mismatch → `gate7_authority_subject_scope_mismatch` on re-run; `evaluated_input_digest` mismatch | reject |
| same result, changed PB decision | `pb_decision_digest` mismatch; Gate 10 `re_binding` / `pb_binding` verdict checks | reject |
| same result, changed authority generation | `currentness_binding` mismatch; Gate 10 `gate10_authority_generation_drift` | reject |
| copied / `deepcopy` / serialized / reconstructed `Gate7Result` | `is_gate7_result` → `False` (not a `_GATE7_RESULTS` member) at every consumer | reject |
| unsealed / `object.__new__` `Gate7Result` | `is_gate7_result` → `False`; `__init__` without seal raises | reject |
| forged `Gate7Result(decision="ALLOW")` via direct construction | `TypeError` at `__init__` (seal check) | reject |

**Frozen: no replay vector produces a downstream acceptance.** `.1R.26` IV re-derives this matrix from source.

---

## 35. Trusted-input ownership matrix (phase prompt §28) — CANONICAL MATRIX #3 (§70.3)

Every positive-path predicate, its source, trusted producer, whether a caller can control it, its canonical binding, its currentness owner, and its failure behaviour:

| Field / predicate | Gate-7 source | Trusted producer | Caller-controllable? | Canonical binding | Currentness owner | Failure behavior |
|---|---|---|---|---|---|---|
| `gate6_decision` (whole object) | arg | `run_gate6_permission_broker` (`_GATE6_*` registry) | **No** (identity registry) | `pb_decision_digest` | Gate 6 | `gate7_untrusted_gate6_decision` |
| `gate6_decision.decision == "ALLOW"` | arg field | Gate 6 `_compose` | **No** | in `pb_decision_digest` | Gate 6 | `gate7_pb_decision_not_allow:<value>` |
| `gate5_result` (whole object) | kw arg | `run_gate5` (`_GATE5_*` registry) | **No** | via lineage checks | Gate 5 | `gate7_untrusted_gate5_result` |
| `gate5_result.projection` (`ValidatedAuthorityProjection`) | derived | `run_gate5` / `validate_approval` | **No** (`is_trusted_validated_authority_projection`) | `authority_freshness_digest` | Gate 5 create / Gate 7 revalidate | `gate7_stale_validated_authority_projection` |
| `identity` (`RuntimeDispatchIdentity`) | kw arg | Gate 2 coordinator + `type(x) is` check | **No** (exact-type + seal upstream) | `invocation_id`/`attempt_id`/`idempotency_key` in `evaluated_input_digest` | immutable (RDGO §10a) | `gate7_invalid_identity` |
| `inputs` (`RuntimeDispatchRequestConstructionInput`) | kw arg | trusted request builder + `_validate_construction_inputs` | **No** (exact-type + canonical re-check) | fields in `evaluated_input_digest` | Gates 5/8/9 | `gate7_invalid_construction_input` / `gate7_request_currentness_drift:<fact>` |
| `authority_current_time` | kw arg | trusted invocation coordinator | bounded string only; not a trust input | `evaluated_at` / `expires_at` | caller passes; §16 currentness dominates | `gate7_invalid_authority_current_time` |
| `subject_scope_binding_digest` | recomputed | Gate 7 (`_expected_subject_scope_binding_digest`) | **No** (live recompute + compare) | in `evaluated_input_digest` | Gate 7 | `gate7_authority_subject_scope_mismatch` |
| `effect_class == "bounded_local_process_dispatch"` | `inputs` field | construction | **No** (construction validated) | step-4 check | Gate 7 scope fence | `gate7_runtime_target_ineligible` |
| `network_requirement is False` | `inputs` field | construction | **No** | step-4 check | Gates 4/8/10 | `gate7_runtime_target_ineligible` |
| `admission_record_digest` / `admission_class` | `inputs.adapter_descriptor_binding` | trusted builder + N-16-6 resolver | **No** (`_validate_construction_inputs` rejects caller-preset) | (finding N-16-4-2: to be added to `evaluated_input_digest`) | N-16-6 / Gates 8/10 | construction rejection |
| runtime posture (`RuntimeEnforcementPosture`) | internal | `resolve_runtime_enforcement_posture()` (frozen constants + design-only flags) | **No** (no caller parameter; one coherent snapshot) | `runtime_posture_digest` | Gate 7 (+ Gate 10 re-read) | `DENY` (`gate7_runtime_execution_unavailable` / `gate7_safety_no_go:<id>`) |
| `matched_no_go_ids` (per-decision subset) | internal | `_matched_blocking_no_go_ids` over `runtime_enforcement_safety_authorization` | **No** | in `runtime_posture_digest` | Gate 7 | `DENY` |
| `currentness_binding` (NEW, `.1R.25`) | internal | authority-generation vector re-derived at evaluation | **No** | in `runtime_enforcement_result_id` | Gate 9 durable / Gate 10 re-derive | `DENY` / downstream drift reason |

**Every authority-bearing predicate is `Caller-controllable? = No`** — the trust is anchored in exact-object provenance and live recomputation, never a caller-supplied field. This is the `.1R.13` sealed-builder + const-transport discipline, unchanged.

### 35.1 Caller-manufactured Gate-7 result challenge (phase prompt §29) — frozen structural prevention

A caller MUST NOT be able to create `RuntimeEnforcementResult(decision="ALLOW")` (or `Gate7Result(decision="ALLOW")`) and have a downstream gate accept it. **Frozen prevention (three layers, all byte-current):**
1. `Gate7Result.__init__` requires `_seal is _GATE7_RESULT_CONSTRUCTOR_SEAL` — a module-private sentinel — else `TypeError`.
2. `is_gate7_result(x)` requires `x in _GATE7_RESULTS`, populated *only* by `run_gate7_runtime_enforcement`'s completed-evaluation return path.
3. `Gate7Result.__reduce__` raises; `__eq__`/`__hash__` are identity-only; `__init_subclass__` raises — no serialized, copied, or subclassed lookalike is ever a registry member.

REPRC-001 freezes all three as MUST (`REPRC-INV-002`).

---

## 36. PB result binding (phase prompt §35, §36)

**Frozen (REPRC-001 §20).** The Gate-7 input MUST bind (via `_pb_decision_digest`, byte-current): PB `decision`, `decision_reason`, `causing_policy_ids`, `matched_no_go_ids`, `requires_human`, `simulation_only`, `implementation_status`, `request_id`, `invocation_id`, `attempt_id`. **Finding N-16-4-3 (non-blocking, feeds `.1R.25`):** `_pb_decision_digest` does **not** currently bind a PB *request canonical digest* or the PBRD/PBNDE/PBPA contract versions or the policy registry version. `.1R.25` SHOULD add `pb_request_digest` (already available on the durable record's `pb_binding.request_digest`) and `policy_context_versions` to the Gate-7 `pb_decision_digest` composition, so a positive Gate-7 result is invalidated by a PB re-evaluation under a different policy/contract version even if the surface decision fields are unchanged. Additive; no PB behaviour change.

### 36.1 POL-005 / POL-013 relationship (phase prompt §36)

**Frozen (REPRC-001 §21):**
- Gate 7 MUST NOT interpret POL-005 / POL-013 itself beyond consuming the trusted `Gate6Decision`. It reads `causing_policy_ids` / `matched_no_go_ids` from the decision object; it does not import or evaluate `ExecutionDisabledRule` or `NarrowLocalCliDispatchEligibilityRule`.
- **A future PB `ALLOW` does not imply a Runtime Enforcement positive.** Explicitly provable:
  ```
  PB ALLOW  +  Gate-7 constraint violation (e.g. posture no-go, target ineligible, projection stale)
    ->  Gate7Result(decision="DENY")   [Gate 7 step 4 or step 7 — independent of PB]
  ```
  Gate 7 runs its own conjunction (§24) *after* accepting the `ALLOW`; any of its own checks failing yields `DENY` regardless of the PB `ALLOW`. `.1R.26` IV asserts this with a synthetic `Gate6Decision(decision="ALLOW")` + a deliberately-violating request.

---

## 37. Gate-7 result schema (phase prompt §45) — CANONICAL MATRIX #7 (§70.7)

Conceptual schema for REPRC-001 §"result schema" (additive to the byte-current `Gate7Result.__slots__`; **no field removed**):

| Field | Present today? | Purpose | Notes |
|---|---|---|---|
| `reprc_schema_version` | **new** | `"REPRC-001/1.0"` — closed field set; additive-only evolution requires a new MINOR | mirrors `DISPATCH_ENVELOPE_SCHEMA_VERSION` |
| `decision` | yes | `"ALLOW"` \| `"DENY"` (`GATE7_DECISION_VALUES`) | unchanged |
| `runtime_enforcement_result_id` | **new** | the §12 canonical identity digest | additive |
| `invocation_id` | yes | attempt binding | unchanged |
| `attempt_id` | yes | attempt binding | unchanged |
| `request_id` | yes | Gate-6 request lineage | unchanged |
| `idempotency_key` | **new field** (currently only inside `evaluated_input_digest`) | explicit binding | additive; already hashed |
| `runtime_projection_digest` (= `evaluated_input_digest`) | yes (as `evaluated_input_digest`) | the full RDGO §8 projection | keep name `evaluated_input_digest` for downstream compat |
| `pb_decision_digest` (PB binding digest) | yes | Gate-6 decision evidence | + §36 additions in `.1R.25` |
| `authority_freshness_digest` (authority-projection binding) | yes | Gate-5 freshness verdict | unchanged |
| `runtime_posture_digest` | yes | posture + per-decision no-gos | unchanged |
| `currentness_binding` (authority-generation binding) | **new** | §16 currentness token | additive |
| `runtime_target_id` | via digest | scope | keep in digest; optional explicit field |
| `adapter_binding_digest` | via `evaluated_input_digest` | descriptor/config + (N-16-4-2) admission | keep in digest |
| `filesystem/containment binding` | via `subject_scope_binding_digest` | scope | keep in digest; Gate 8 owns actual containment |
| `matched_no_go_ids` | yes | per-decision diagnostic (NOT authority input) | unchanged; empty on `ALLOW` |
| `causing_reason_ids` | yes | positive rationale (§46) / negative reasons | unchanged |
| `evaluated_at` (created) | yes | evaluation instant | unchanged |
| `expires_at` (currentness evidence) | yes — **but semantics fixed per N-16-4-1** | bounded wall-clock backstop | `.1R.25` changes the value, not the field |

**Do not overstuff duplicated authority** (phase prompt §45): the schema carries *digests and identifiers*, never a copy of the approval, the PB decision object, the projection, or the containment evidence — every consumer re-reads the durable / trusted source.

### 37.1 Decision reasons (phase prompt §46)

**Frozen (REPRC-001 §22).** A positive result MUST carry an explicit positive rationale, not an empty tuple. **Finding N-16-4-4 (non-blocking, feeds `.1R.25`):** the current positive branch sets `causing_reason_ids=()`. `.1R.25` MUST set a stable positive reason vocabulary, minimally:
```
gate7_runtime_enforcement_satisfied
gate7_pb_decision_allow_consumed
gate7_authority_projection_revalidated
gate7_runtime_target_within_local_cli_v1_scope
gate7_no_blocking_re_no_go_matched
gate7_synthetic_evaluation_path   (synthetic-only; MUST be present whenever the posture was substituted)
```
Negative reasons remain the current fail-closed set (`gate7_runtime_execution_unavailable`, `gate7_safety_no_go:<id>`, …), unchanged.

### 37.2 Immutability (phase prompt §47)

**Frozen (REPRC-001 §23).** `Gate7Result` is immutable after construction. Byte-current: `__slots__` (no `__dict__`), all fields set once in `__init__` inside the seal, `__eq__`/`__hash__` identity-only. `.1R.25` SHOULD add a `__setattr__` guard mirroring `DispatchEnvelope`'s ("`Gate7Result is immutable`") for defence in depth — additive. Any post-construction mutation attempt MUST raise or be impossible.

### 37.3 Constructor ownership (phase prompt §48)

**Frozen (REPRC-001 §24).** The exact trusted constructor is `run_gate7_runtime_enforcement` in `runtime_dispatch_gate7.py` — the **sole** production owner of the RDGO §8 Gate-7 boundary. No generic public constructor grants authority through structure. `.1R.25` adds no second constructor. A future REPRC helper module (if any) MUST route all `Gate7Result` construction through `run_gate7_runtime_enforcement`.

---

## 38. Consumer ownership (phase prompt §49) — exact finite consumer set — CANONICAL MATRIX #9 partial

**Frozen (REPRC-001 §25) — the exact, finite set of legitimate downstream consumers of a `Gate7Result`:**

| Consumer | Module | How it consumes | What it does with a positive result |
|---|---|---|---|
| Gate 8 | `runtime_dispatch_gate8.run_gate8_process_containment` | `is_gate7_result` + `decision == "ALLOW"` + invocation/attempt lineage | re-runs the Gate-7-relevant checks implicitly, binds `_gate7_result_digest` into `Gate8Result.gate7_result_digest` + `containment_evidence_digest` |
| Gate 9 | `runtime_dispatch_gate9.run_gate9_atomic_authority_consumption` | `is_gate7_result` + `decision == "ALLOW"` + `gate8_result.gate7_result_digest` cross-check | writes `consumption.json` item 7 `runtime_enforcement_binding` (verdict / expiry / `evaluated_input_digest` / `decision_digest`) |
| Gate 10 pre-effect eligibility | `runtime_dispatch_gate10_eligibility.run_gate10_pre_effect_eligibility` | `is_gate7_result` + `decision == "ALLOW"` + `gate8_result.gate7_result_digest == _gate7_result_digest(gate7_result)` + durable `re_binding.verdict == "ALLOW"` + `re_expires_at > now` | mints the `DispatchEnvelope` (only after the full 18-step battery) |

**No other module may import `Gate7Result` / `is_gate7_result` / `run_gate7_runtime_enforcement` as a consumer.** `.1R.25` MUST add a consumer-inventory guard (`AUTHORIZED_CONSUMERS = {the 3 modules above}` + their test files), a subset check, no wildcard, still rejecting any other importer — **authored under the `.1R.25` phase identity** so the later `.1R.24`-recommended IV re-derives it. This pre-empts another scope-fence-reconciliation incident (the `.1R.17`/`.1R.19`/`.1R.22` class).

---

## 39. Predicted guard-impact inventory (phase prompt §50) — CANONICAL MATRIX #13 (§70.13)

**Mandatory due to the `.1R.17` / `.1R.19` / `.1R.22` history.** Predicted guards that a `.1R.25` change to `runtime_dispatch_gate7.py` (+ a new `docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md` + RDGO v3.2) will trip:

| Guard family | Location (predicted) | Why it trips | `.1R.25` reconciliation strategy (§51) |
|---|---|---|---|
| Gate-7 IV byte/AST freeze | `test_gate7_runtime_enforcement_coordinator_independent_verification_3w1r2b1r1_1r13_3.py` | asserts `runtime_dispatch_gate7.py` structure / "always returns DENY on production path" / no-effect AST / `Gate7Result.__slots__` shape / positive branch `pragma: no cover` | **split historical/current**: keep the historical "DENY-only on the *unmodified* production path" assertion as a point-in-time note; add a current assertion that the positive branch is reachable *only* via the synthetic seam and that production posture still yields `DENY`; widen `__slots__` assertion to a subset check over the authorized new fields (no wildcard) |
| Gate-7 integration freeze | `test_gate7_runtime_enforcement_coordinator_integration_3w1r2b1r1_1r13_2.py` | `Gate7Result` field set; decision vocabulary; `_GATE7_RESULTS` registry behaviour; `expires_at == evaluated_at` | widen to subset checks; update the `expires_at` assertion to the N-16-4-1 dual-bound model; keep the "not caller-constructable / not serializable / identity-only" assertions unchanged (they still hold) |
| RE No-Go Registry contract | `test_runtime_enforcement_no_go_registry_contract.py` | RE-NOGO-001..017 IDs / classes / "Gate7Result.matched_no_go_ids projects only the per-decision subset" | **no change expected** — N-16-4 does not touch the registry; if a guard asserts "Gate 7 always matches RE-NOGO-001", split it: historical (unmodified posture) vs current (RE-NOGO-001 not matched for a synthetic fully-satisfied profile) |
| RE shared safety-authorization contract | `test_runtime_enforcement_shared_safety_authorization_contract.py` | `DEFAULT_AUTHORIZATION_FLAGS` / `DEFAULT_SAFETY_FLAGS` values; `AUTH_FLAG_TO_NO_GO` map | **no change** — N-16-4 does not modify the default flag tables; the synthetic path substitutes a *resolver*, not the DEFAULT constants |
| RDGO-001 contract freeze / byte guards | `test_runtime_dispatch_contract_normalization_*` , `test_*cross_contract_freeze*` , the `.1R.15.4` guards | RDGO-001 version pin (`v3.1`), §8 text freeze, "gate count 11", "durable-before-effect items 9" | repin to `v3.2`; rewrite the §8 text-freeze to the v3.2 canonical statement (the REPRC-001 cross-ref sentence added); keep "gate count 11 / items 9 / TOCTOU 7" byte-frozen (unchanged) |
| Gate 8 / Gate 9 / Gate 10 IV suites | `test_*gate8*`, `test_*gate9*serialization*`, `test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py`, `test_dispatch_attempt_durable_lifecycle_*` | consume `_gate7_result_digest` / `runtime_enforcement_binding` shape; may assert the Gate-7 result field set | widen digest-shape assertions to subset checks over the authorized new fields; the `runtime_enforcement_binding` write in Gate 9 gains `currentness_binding` → update the item-7 shape assertion to a subset check |
| meta-guards (`test_meta_guards_*byte_unchanged_since_*`) | `.1R.19R` / `.1R.19R.1` | byte-freeze earlier IV suites | reconcile per the `.1R.22R` §12 precedent — keep truly-untouched suites byte-frozen; replace a byte-freeze of a *modified* suite with a not-weakened check (`def test_` count ≥, no new `xfail`/`skip`, no wildcard) |
| contract-version cross-reference guards | `test_*` that grep for `RDGO-001 v3.1` / `RDGO-001/3.1` across `src/` + `docs/` | the `_RDGO_VERSION = "RDGO-001/3.1"` constant in `runtime_dispatch_gate10_eligibility.py` and any contract cross-ref | `.1R.25` decides: either bump `_RDGO_VERSION` to `3.2` (and every stamped `contract_versions` dict) — a wider blast radius — **or** keep RDGO at v3.1 and put the positive-result clarification *only* in REPRC-001 v1.0 (narrower). **Recommendation: prefer REPRC-001-only; make the RDGO v3.2 bump optional and defer it to a later normalization pass if its cross-ref blast radius is large** (the `.1R.22` PBRD-v2.1→v3.0 sibling-bump cascade lesson — 51 RIHAC/HPAC failures). This keeps `.1R.25` bounded. |

**`.1R.25` MUST run a full-suite / broad deterministic no-xdist fixed-SHA A/B in `git worktree`s at the pre-phase baseline and the phase head** (the `.1R.22R` lesson — the implementing phase's §11 inventory undercounts; grep the whole `tests/` tree for `RDGO-001 v3.1`, `Gate7Result`, `matched_no_go_ids == `, `decision == "DENY"` freezes, `expires_at`, `_GATE7_RESULTS`, `is_gate7_result`, and the Gate-7 test basenames).

---

## 40. Meta-guard strategy (phase prompt §52)

**Frozen (feeds `.1R.25` / `.1R.26`).** Identify every test that executes a Gate-7 guard suite at HEAD (`test_meta_guards_*`, `test_*_guards_pass_at_head`, `test_widened_guard_module_passes_at_head`). Include them in the `.1R.25` implementation A/B plan and the `.1R.26` IV fixed-SHA A/B. Per the `.1R.19R` / `.1R.22R` precedent: keep untouched suites byte-frozen; for a modified suite, replace the byte-freeze with a *not-weakened* check (concatenated needles to avoid self-match; exclude added comment lines; scope the diff to the immutable historical range, not `BASELINE..HEAD`).

---

## 41. Defensive test matrix (phase prompt §53) — CANONICAL MATRIX #14 (§70.14) — ≥ 34 cases for `.1R.25`

| # | Case | Expected |
|---|---|---|
| 1 | valid synthetic positive result (fully-satisfied `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile + substituted posture) | `Gate7Result(decision="ALLOW")`, `is_gate7_result` True, positive `causing_reason_ids` incl. `gate7_synthetic_evaluation_path` |
| 2 | malformed projection (`inputs` fails `_validate_construction_inputs`) | `(None, ("gate7_request_currentness_drift:<fact>",))` |
| 3 | PB `DENY` → Gate-7 | `(None, ("gate7_pb_decision_not_allow:DENY",))`, no `Gate7Result` |
| 4 | PB `HUMAN_REVIEW` → Gate-7 | `(None, ("gate7_pb_decision_not_allow:HUMAN_REVIEW",))` |
| 5 | PB `ALLOW` + Gate-7 posture no-go matched | `Gate7Result(decision="DENY")`, `matched_no_go_ids` non-empty |
| 6 | missing `invocation_id` (empty identity) | `gate7_invalid_identity` |
| 7 | missing `attempt_id` | `gate7_invalid_identity` |
| 8 | wrong `attempt_id` (result for attempt 1, identity attempt 2) — at Gate 8 | `gate8_invocation_binding_mismatch` |
| 9 | wrong `invocation_id` — at Gate 8/9/10 | `gate*_invocation_binding_mismatch` |
| 10 | changed PB binding (different `Gate6Decision` object) between Gate 7 and Gate 8 re-run | fresh Gate-7 evaluation; `pb_decision_digest` differs |
| 11 | changed authority generation (`currentness_binding` drift) | Gate 10 `gate10_authority_generation_drift:<source>` |
| 12 | changed runtime target | `evaluated_input_digest` / `_gate7_result_digest` mismatch → `gate10_gate7_lineage_mismatch` |
| 13 | changed adapter binding | digest mismatch |
| 14 | changed filesystem scope | `gate7_authority_subject_scope_mismatch` on re-run |
| 15 | `network_requirement is True` | `gate7_runtime_target_ineligible` |
| 16 | credential requirement present (effect plan) | Gate 10 `gate10_effect_plan_requires_credentials` |
| 17 | caller-supplied shell string (no field exists) | structurally impossible — assert no such `__slots__` / construction field |
| 18 | fixed-argv mismatch (executable hash drift) | Gate 8/10 `gate10_executable_identity_drift` |
| 19 | fixed-argv mismatch (descriptor pin) | Gate 8 containment re-resolution failure |
| 20 | unsupported effect class (`effect_class != "bounded_local_process_dispatch"`) | `gate7_runtime_target_ineligible` |
| 21 | unresolved no-go (posture returns a blocking `RE-NOGO-*`) | `Gate7Result(decision="DENY")`, `causing_reason_ids` has `gate7_safety_no_go:<id>` |
| 22 | forged positive-result object (`Gate7Result(decision="ALLOW", _seal=object())`) | `TypeError` |
| 23 | unsealed result (`object.__new__(Gate7Result)`) | `is_gate7_result` False at every consumer |
| 24 | serialized/reconstructed result (`pickle.dumps`) | `TypeError` (`__reduce__`) |
| 25 | duplicate evaluation (same inputs twice) | two `!=` objects, identical field values / `evaluated_input_digest` |
| 26 | stale positive (mutate one dependency then feed downstream) | rejecting component per §34.1 |
| 27 | restart behavior (`Gate7Result` from a "previous process") | `is_gate7_result` False; must re-run |
| 28 | downstream Gate-8 still required (positive Gate 7, Gate 8 not run) | Gate 9 `gate9_untrusted_gate8_result` |
| 29 | Gate-9 still required (positive Gate 7 + Gate 8, Gate 9 not run) | Gate 10 `gate10_untrusted_gate9_result` |
| 30 | runtime unavailable despite Gate-7 positive (synthetic ALLOW, real capability re-read) | Gate 10 `gate10_runtime_capability_not_unavailable` |
| 31 | no external effect (AST scan of the Gate-7 + REPRC modules) | no `subprocess`/`socket`/`adapter.dispatch`/provider/credential import or call |
| 32 | no capability change (`pcae runtime inspect` before/after) | `not_implemented / Observed / observe / unavailable`, 0/0 |
| 33 | old negative cases remain negative (every current `.1R.13.2`/`.1R.13.3` DENY/reject case) | unchanged outcomes |
| 34 | exact finite consumer guard (a 4th module importing `is_gate7_result`) | consumer-inventory guard rejects |
| 35 | no caller boolean shortcut (assert no `execution_available` / `pb_allowed` / `re_satisfied` parameter anywhere) | absent |
| 36 | PB `ALLOW` + deliberately-violating request → `DENY` (§36.1 proof) | `Gate7Result(decision="DENY")` |
| 37 | positive result carries non-empty positive `causing_reason_ids` (N-16-4-4) | asserted |
| 38 | `expires_at` dual-bound model (N-16-4-1): fresh positive result is NOT immediately `gate10_re_decision_expired` | Gate 10 accepts within TTL |

Expanded from primary evidence in `.1R.25`; re-derived independently in `.1R.26`.

---

## 42. Positive-path contract wording (phase prompt §54) — conceptual, NOT applied

Conceptual normative text for REPRC-001 §2 (drafted here for `.1R.25` to author; **no contract file is edited by `.1R.24`**):

> **REPRC-001 §2 — Meaning of a positive Gate-7 result.** A `Gate7Result` with `decision == "ALLOW"` and `is_gate7_result(result) == True` asserts that the exact bound `runtime_dispatch` invocation/attempt satisfies Runtime Enforcement's independent conjunction (structural validity, a consumed Gate-6 `ALLOW`, a revalidating Gate-5 authority projection, a target within `bounded_local_process_dispatch` / `RUNTIME_DISPATCH_LOCAL_CLI_V1` scope, an available runtime posture, and no matched per-decision Runtime Enforcement no-go) as of `evaluated_at`, and MAY therefore proceed to Gate 8. It SHALL NOT be construed as, and SHALL NOT be relied upon as: permission to execute or dispatch; runtime capability or adapter availability; effect authorization; human authority (created, consumed, or refreshed); Permission Broker permission; a `DispatchEnvelope`; or a substitute for Gates 8, 9, or the Gate-10 pre-effect read-back. It is ephemeral, non-serializable, non-transferable, invocation/attempt-bound, and invalid across any change to its bound PB decision digest, authority-freshness digest, runtime-posture digest, projection currentness, or authority-generation currentness. The durable record of the Runtime Enforcement verdict is Gate 9's `consumption.json` `runtime_enforcement_binding`; every consumer that runs after Gate 9 SHALL re-read it rather than trust a `Gate7Result` handle.

---

## 43. Negative-path preservation (phase prompt §55)

**Frozen.** `.1R.25` preserves **every** currently-valid negative Gate-7 behaviour: all 12 pre-evaluation fail-closed reason ids; the `DENY` on `not posture.execution_available`; the `DENY` on any matched `RE-NOGO-*`; the `gate7_internal_error_fail_closed` bare-except; the rejection of `DENY`/`HUMAN_REVIEW` Gate-6 decisions before evaluation; the rejection of every non-registry / reconstructed / serialized upstream object. The **only** path that changes is the addition of a reachable positive branch for a synthetic fully-satisfied `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile — and even that stays `DENY` for the production posture. `.1R.26` IV asserts "old negative cases remain negative" via a fixed-SHA A/B.

---

## 44. No-Go contract impact (phase prompt §44)

**Frozen: no change.** The RE No-Go Registry (schema 1.1) requires **no change, no annotation, no new entry, no clarified positive-path rule**. RE-NOGO-001's per-decision projection behaviour is already contract-correct: it is matched when the authorization flag is `False` and not-matched when `True`. N-16-4's synthetic path substitutes a *resolver* that returns `execution_available=True` + empty `matched_no_go_ids` — it does not modify the `DEFAULT_AUTHORIZATION_FLAGS` / `DEFAULT_SAFETY_FLAGS` constants or the `AUTH_FLAG_TO_NO_GO` map. NG-025's existing PBNDE-001 §9 annotation already covers the `RUNTIME_DISPATCH_LOCAL_CLI_V1` carve-out. **No `RE-NOGO-*` entry is created.**

---

## 45. Independent verification design (phase prompt §56) — frozen `.1R.26` IV requirements

The IV (`.1R.26`) MUST independently RE-DERIVE (not trust `.1R.25`'s report or suite) and prove:

1. the positive `Gate7Result` is **attempt-bound** — a result for `(A,1)` is rejected for `(A,2)` / `(B,1)` at every consumer;
2. **non-forgeable** — direct construction raises; `object.__new__` / reconstruction / copy is not a `_GATE7_RESULTS` member;
3. **non-transferable / non-bearer** — `__reduce__` raises; a serialized form is inert; identity-only `==`/`hash`;
4. **stale result rejected** — every §34.1 mutation is caught by the named component;
5. **PB result consumed, not re-run** — Gate 7 imports no `PolicyRegistry` / `_compose` / POL-* rule (AST); a PB `ALLOW` + violating request still `DENY`s;
6. **no-go semantics preserved** — every current `matched_no_go_ids` behaviour; environmental-readiness no-gos still out of per-decision scope by design;
7. **Gate-8/9 still required** — a positive Gate 7 with a missing/negative Gate 8 or Gate 9 fails downstream;
8. **runtime capability independent** — synthetic ALLOW + real capability re-read → `gate10_runtime_capability_not_unavailable`;
9. **no effect reachable** — AST: no `adapter.dispatch()` call site; `RuntimeRegistry` empty; `pcae runtime inspect` unchanged;
10. **guards fully reconciled** — the `.1R.25` guard-impact inventory is complete (independent broad fixed-SHA A/B; do not trust `.1R.25`'s enumeration);
11. **fixed-SHA A/B clean** — 0 attributable functional regressions; every added guard node is a deliberate reconciliation and still rejects an unauthorized change;
12. **contract fidelity** — REPRC-001 v1.0 text matches the implemented behaviour; RDGO v3.2 (if bumped) is a genuine MINOR restatement (§21 criteria); no MAJOR was carried silently.

---

## 46. Implementation-phase decomposition (phase prompt §57) — frozen

**Recommended (IDs above `.1R.20` are recommended, NOT reserved — `.1R.16` §36.2):**

| Phase ID (recommended) | Title | Scope |
|---|---|---|
| `149O.20L.7O.3W.1R.2B.1R.1.1R.25` | **N-16-4 Real Positive Single-Attempt Runtime Enforcement Gate Implementation** | Author `docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md` (**REPRC-001 v1.0**) as the first commit; optionally RDGO-001 v3.1→v3.2 (MINOR §8 cross-ref) *iff* its cross-ref blast radius is small — else defer to a normalization pass; make the `Gate7Result` positive branch reachable **only** via the synthetic test-boundary seam; add `runtime_enforcement_result_id` / `currentness_binding` / `reprc_schema_version` / explicit `idempotency_key` fields (additive `__slots__`); fix `expires_at` to the N-16-4-1 dual-bound model; bind `admission_record_digest` / `admission_class` (N-16-4-2) + `pb_request_digest` / `policy_context_versions` (N-16-4-3) into the Gate-7 digests; set the positive `causing_reason_ids` vocabulary (N-16-4-4); add the `__setattr__` immutability guard; add the consumer-inventory guard (§38); Gate 9 records `currentness_binding` in `runtime_enforcement_binding` (additive to item 7); the ≥ 38-case defensive test matrix (§41); scope-fence guard reconciliation (§39/§40) — subset checks, no wildcard, no test renamed, each still rejecting an unauthorized change. **NO `adapter.dispatch()` call site, NO capability change, NO N-16-5/6/7 work, NO execution enablement.** |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.26` | **Independent Verification of the N-16-4 Runtime Enforcement Gate** | RE-DERIVE the §45 requirements against REPRC-001 v1.0, RDGO §8, and byte-current source; independent broad fixed-SHA A/B in `git worktree`s; the 12-point IV proof; disclose any undisclosed attributable guard regressions as a BLOCKER referred to a `.1R.25R` reconciliation (the `.1R.18` / `.1R.20` / `.1R.23` precedent). |

Treat the IDs as recommended unless project conventions reserve them. **Do not implement `.1R.25` or `.1R.26`.**

---

## 47. Contract-freeze decision (phase prompt §58) — restated

**Frozen: planning (`.1R.24`) → implementation with inline contract authorship (`.1R.25`) → IV (`.1R.26`)** — the N-16-3 precedent (Path X of §31). A separate contract-freeze phase is **not** required because REPRC-001 v1.0 is an initial freeze with no incumbent to migrate and the RDGO change is a MINOR pointer. **Fallback:** if `.1R.25` primary-source review finds REPRC-001 must force a MAJOR RDGO state-machine change or merge the four concerns, `.1R.25` STOPS and re-adjudicates to a separate `.1R.25` freeze + `.1R.26` impl + `.1R.27` IV.

---

## 48. N-16-4 → N-16-5 → N-16-6 → N-16-7 ordering (phase prompt §59, §60, §61) — CANONICAL MATRIX #15-adjacent

### 48.1 N-16-5 ordering (phase prompt §59)

**Question:** Is a synthetic/test-only positive Runtime Enforcement implementation independently useful and safe before real human authentication (N-16-5) exists?

**Frozen answer: YES — preserve N-16-4 before N-16-5.**
- **Useful:** it freezes the positive-result contract (meaning, non-bearer trust, identity, currentness, replay) and makes the downstream chain's positive-path handling (Gate 8 digest bind, Gate 9 `runtime_enforcement_binding`, Gate 10 lineage) *testable* end-to-end on a synthetic path. Without it, every later prerequisite (N-16-5/6/7) would have to guess at the positive Gate-7 shape.
- **Safe:** the synthetic path is local/in-memory, substitutes only via underscore-private test seams, touches no capability / adapter / credential / network, and production Gate 7 stays `DENY`-only (two independent walls — N-16-5 authority, N-16-6 admission — plus RE-NOGO-002/010/011).
- **Precedent:** Gate 8 (`.1R.13.5`), Gate 9 (`.1R.15`), Slice A (`.1R.17`), Slice B (`.1R.19`) were all implemented and verified on exactly this synthetic-substitution pattern before real authority existed. N-16-4 is the same shape.

No STOP / re-adjudication of the ordering.

### 48.2 N-16-6 relationship (phase prompt §60)

**Frozen: N-16-6 remains after N-16-5.** The N-16-4 contract (REPRC-001) **references** the future admission interface without implementing it: §21 of this plan and finding N-16-4-2 say `.1R.25` binds `admission_record_digest` / `admission_class` into the Gate-7 digest (evidence Gate 6 already produced via the trusted builder) — Gate 7 performs **no** admission lookup and calls **no** resolver. REPRC-001 v1.0 §13 will state "Gate 7 evaluates only the admission evidence bound by Gate 6; live admission re-checks are owned by Gates 8/10 and N-16-6."

### 48.3 N-16-7 last (phase prompt §61)

**Frozen: N-16-7 remains strictly last before Slice C.** N-16-4 introduces no capability enablement. `resolve_runtime_enforcement_posture()` stays a pure read of frozen constants. The synthetic path substitutes the posture *resolver* at a test seam; it never flips `EXECUTION_AVAILABILITY` or performs an `Observed → Approved` transition.

### 48.4 Slice C boundary (phase prompt §62)

**Frozen: Slice C keeps NO phase ID.**
```
Slice C cannot begin until N-16-3, N-16-4, N-16-5, N-16-6, N-16-7 all independently close.
```
N-16-3 is CLOSED; N-16-4 is OPEN (this plan); N-16-5/6/7 OPEN. No planning decision in `.1R.24` authorizes an effect.

### 48.5 First external effect (phase prompt §63)

**Frozen: ABSENT.** No `.1R.24` decision authorizes an effect. `.1R.25` adds no `adapter.dispatch()` call site (AST-enforced).

---

## 49. N-23-2 carry-forward (phase prompt §64)

**Carried explicitly:** **N-23-2 — INFO / DEFERRED NORMALIZATION DEBT** (PBNDE-001 §3 / PBRD-001 §12a.1 say the `RUNTIME_DISPATCH_LOCAL_CLI_V1` marker is "committed into the request canonical digest" — it is not *literally* in the digest; PBRD §5's "derived commitments" paragraph describes the real, sound mechanism). **N-16-4 does not create a natural normalization point** — N-16-4 is downstream of PB policy and does not touch PBRD / PBNDE / PBPA. **No PBRD / PBNDE edit in `.1R.24` or (recommended) `.1R.25`.** N-23-2 remains tracked, deferred to a dedicated PB-contract normalization pass. N-23-1 (INV-008 non-executable `ALLOW` for a structurally-complete test-built sealed profile — contract-sanctioned, unreachable in production) is also carried unchanged.

---

## 50. Whole-system authority chain, post-N-16-4 (phase prompt §65) — CANONICAL MATRIX #16 (§70.16)

The conceptual chain, corrected to the byte-current RDGO-001 v3.1 gate numbering (RDGO's Gate 3 = human authority creation, Gate 5 = approval validation, Gate 6 = PB, Gate 7 = Runtime Enforcement, Gate 8 = containment, Gate 9 = durable record + consumption, Gate 10 = pre-effect eligibility then adapter dispatch):

| # | Stage | Artifact passed forward | Trust binding | Authority: created / consumed / evidenced |
|---|---|---|---|---|
| 1 | Real human authentication + approval (N-16-5; today NON_REAL) | `RuntimeInvocationApproval` (RIASC-001 v3.0) + HPAC proof lifecycle | HPAC-001 v2.1 protected-channel presentation + v2 challenge digest binding | **creates** human authority |
| 2 | Gate 5 — approval validation | `Gate5Result` + `ValidatedAuthorityProjection` | `is_gate5_result` registry; `validate_approval` (re-runnable) | **evidences** (projects) authority; consumes nothing |
| 3 | Gate 6 — PB policy decision | `Gate6Decision` (`decision`, `causing_policy_ids`, `matched_no_go_ids`, digests) | `is_gate6_decision` registry; PBRD-001 v3.0 fourteen-fact request digest | **creates** policy permission (`ALLOW`/`DENY`/`HUMAN_REVIEW`); not authority |
| 4 | **Gate 7 — Runtime Enforcement decision** | **`Gate7Result` (`decision`, `runtime_enforcement_result_id`, `evaluated_input_digest`, `pb_decision_digest`, `authority_freshness_digest`, `runtime_posture_digest`, `currentness_binding`)** | **`is_gate7_result` registry; seal; non-serializable; REPRC-001 v1.0** | **evidences** "may proceed to Gate 8"; **creates no authority, consumes none, reusable = no, durable = no** |
| 5 | Gate 8 — process containment + live preflight | `Gate8Result` + `containment_evidence_digest` (binds `_gate7_result_digest`) | `is_gate8_result` registry; three-layer containment model | **evidences** established containment; not authority |
| 6 | Gate 9 — durable pre-dispatch record + atomic authority consumption | `Gate9Result` (`status="consumed"`) + `consumption.json` (`HPAC-AUTHORITY-CONSUMPTION/2.1`, item 7 `runtime_enforcement_binding`) | create-only atomic primitive (`O_EXCL` + `os.link`); `S1`/`S2` re-check | **consumes** human authority (approval + proof + presentation + challenge) atomically, once |
| 7 | Gate 10 — pre-effect eligibility / `DispatchEnvelope` | `DispatchEnvelope` (RPAC-REQ-029) | `is_dispatch_envelope` registry; 18-step read-back battery; capability re-read = `Observed/observe/unavailable` | **evidences** pre-effect readiness; "authorizes nothing" |
| 8 | Slice-B durable attempt lifecycle | `RuntimeInvocationRecord` (`PREPARED → EFFECT_ATTEMPT_STARTED → …`) | non-authoritative mirror; digest-chained append-only | **evidences** attempt state; `GRANTS_NO_EFFECT_AUTHORITY` |
| 9 | Runtime capability (N-16-7) | capability snapshot (`execution_availability`) | frozen `runtime_introspection` constants; governed `Observed → Approved` transition | **enabling condition**, not authority; today `unavailable` |
| 10 | Slice-C adapter dispatch (no phase ID) | one process-spawn / dispatch receipt | established containment + `DispatchEnvelope` re-validated immediately before | **FIRST EXTERNAL EFFECT** — consumes nothing new; the effect itself |

### 50.1 Authority-creation table (phase prompt §66) — CANONICAL MATRIX #16 (§70.16)

| Stage | Input | Output | Creates authority? | Consumes authority? | Reusable? | Durable? | Can cause effect? |
|---|---|---|---|---|---|---|---|
| Gate 3 (human approval) | human act + subject facts | `RuntimeInvocationApproval` | **Yes** (human authority) | No | No (one attempt via `attempt_limit=1`) | Yes (RIASC record) | No |
| Gate 5 | approval ref + current state | `ValidatedAuthorityProjection` | No (projects) | No | Re-runnable (not cached authority) | No (ephemeral) | No |
| Gate 6 | 14-fact request + projection | `Gate6Decision` | No (policy permission) | No | Re-evaluate on drift | No (ephemeral) | No |
| **Gate 7** | **`Gate6Decision` + `Gate5Result` + `identity`/`inputs` + internal posture** | **`Gate7Result`** | **No** | **No** | **No — re-run, never reuse** | **No — ephemeral** | **No** |
| Gate 8 | `Gate7Result` + effect plan + descriptor | `Gate8Result` + containment evidence | No | No | No | Digest bound at Gate 9 | No |
| Gate 9 | `Gate8Result` + all lineage | `Gate9Result("consumed")` + `consumption.json` | No | **Yes — approval + proof + presentation + challenge, atomically, once** | No | **Yes** (`consumption.json`) | No process effect yet |
| Gate 10 pre-effect | `Gate9Result` + durable record + fresh resolvers | `DispatchEnvelope` | No | No | No | No (ephemeral) | No |
| Slice C dispatch | `DispatchEnvelope` + containment | process receipt | No | No | No | mirror record | **YES** |

**Gate 7 never appears as final effect authority.** It creates nothing, consumes nothing, is not reusable, is not durable, and cannot cause an effect. This is the frozen property.

### 50.2 Failure propagation (phase prompt §67)

**Frozen.** A Gate-7 `DENY` (or `(None, reason)`) **stops the flow** — Gate 8 rejects a non-`ALLOW` `Gate7Result` at `gate8_gate7_decision_not_allow` *before* Shell Gate evaluation; Gate 9 rejects at `gate9_gate7_decision_not_allow`; Gate 10 rejects at `gate10_gate7_decision_not_allow`. **No later gate may override a Gate-7 `DENY`** — there is no code path in Gate 8, 9, or 10 that converts a non-`ALLOW` Gate-7 result into forward progress. `.1R.26` IV asserts this by AST + behaviour.

### 50.3 Result observability + audit evidence (phase prompt §68, §69)

**Frozen (REPRC-001 §26).**
- **Observability:** `pcae runtime inspect` / reporting MAY expose, for audit: the Gate-7 `decision`, `causing_reason_ids`, `matched_no_go_ids`, `runtime_enforcement_result_id`. It MUST NOT expose secrets, credential material, or the raw approval/projection, and observability MUST NOT become authority (a displayed `runtime_enforcement_result_id` grants nothing — `is_gate7_result` still requires registry membership).
- **Audit evidence:** `.1R.25` implementation MUST ensure the durable postmortem proof is Gate 9's `consumption.json` `runtime_enforcement_binding` (verdict, expiry, `evaluated_input_digest`, `decision_digest`, + `currentness_binding`). **`audit evidence != authority`** — the record proves *what was decided*, never *permits a redo*.

---

## 51. STOP-condition check (phase prompt §"Valid early STOP conditions", §77) — none apply

| STOP condition | Applies? | Evidence |
|---|---|---|
| RDGO v3.1 semantics fundamentally preclude any bounded positive Gate-7 result | **No** | RDGO §8 *explicitly* provides for one ("Its positive decision is single-attempt, expiring …"); §10 item 7 records the Gate-7 verdict durably; the positive branch is already coded and consumed by three gates |
| A positive Gate-7 result cannot be represented without becoming bearer authority | **No** | It already is non-bearer today — `is_gate7_result` registry + `__reduce__` raises + identity-only equality; §11 freezes the model |
| Gate-7 positivity cannot be made attempt-specific / non-transferable | **No** | Already bound to `invocation_id`/`attempt_id`/`request_id`/`evaluated_input_digest`; three independent enforcement layers (§13) |
| Consuming Gate-6/PB evidence would require rerunning or overriding PB policy | **No** | Gate 7 consumes the `Gate6Decision` object as an input; imports no policy code; PBNDE-001 §7 already frozen this |
| A positive Gate-7 result cannot remain subordinate to Gates 8/9/10 / Slice-B / runtime capability | **No** | Every one already independently re-validates; §14, §17–§21 freeze the subordination |
| Current no-go semantics require a contract evolution broader than N-16-4 | **No** | §23/§44 — no RE No-Go Registry change; only RE-NOGO-001's per-decision projection un-matches for a synthetic fully-satisfied profile |
| N-16-4 cannot be separated cleanly from N-16-5/6/7 | **No** | §26/§48 — production Gate 7 stays `DENY`-only after N-16-4 alone (N-16-5 authority + N-16-6 admission walls); the synthetic path is clean and precedented |
| Implementation necessarily introduces the first external effect | **No** | §27 — no `adapter.dispatch()` call site; AST-enforced; `RuntimeRegistry` empty |
| Repository evidence requires a materially different prerequisite ordering | **No** | §48 — N-16-3→4→5→6→7 (N-16-7 last, N-16-4 before N-16-5) confirmed from `.1R.16` §35 + `.1R.21` §41 |
| A normative-contract versioning question cannot be resolved from current repository conventions | **No** | §30 — REPRC-001 v1.0 (PBNDE-001 precedent, initial freeze) + RDGO v3.1→v3.2 MINOR (§21's own enumerated MINOR criteria); the RDGO bump is even made *optional* to bound blast radius |

**No STOP / BLOCKED condition is reached.** The plan proceeds through governed finalization.

---

## 52. Runtime / no-effect verdict (phase prompt §72)

```
Runtime:               Observed / observe / unavailable   (not_implemented; maximum plugin capability: observe)
First external effect: ABSENT
Execution enabled:     NO
```

`git diff --name-only 1ca1f6ab HEAD -- src/pcae` empty. `git diff --name-only 1ca1f6ab HEAD -- docs/contracts docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` empty. `runtime_dispatch_gate7.py` byte-identical. `pcae runtime inspect`: `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; Permission Broker status `execution_unavailable`; governance posture `non-executing`. The only subprocesses used were read-only `git` history inspection and `pcae` governance CLI checks.

---

## 53. Recommended next phase (phase prompt §73)

**Recommended (requires its own separate explicit human authorization; ID recommended, NOT reserved):**

`149O.20L.7O.3W.1R.2B.1R.1.1R.25` — **N-16-4 Real Positive Single-Attempt Runtime Enforcement Gate Implementation** (scope frozen in §46: author REPRC-001 v1.0 first; make the positive `Gate7Result` branch reachable only via the synthetic test seam; the additive schema fields + `expires_at` fix + digest bindings + positive reason vocabulary + immutability guard + consumer-inventory guard; Gate 9 records `currentness_binding` additively; ≥ 38-case defensive matrix; scope-fence guard reconciliation with a broad fixed-SHA A/B; NO adapter call site, NO capability change, NO N-16-5/6/7 work, NO execution enablement) → then `149O.20L.7O.3W.1R.2B.1R.1.1R.26` — **Independent Verification of the N-16-4 Runtime Enforcement Gate**.

Then N-16-5 → N-16-6 → N-16-7 (N-16-7 strictly last), each its own authorized implementation + IV pair. Slice C / Slice D keep NO phase ID until N-16-3..7 all close. **Do not begin `.1R.25` / `.1R.26`.**

---

## 54. `.3` governance incident (phase prompt §74) — preserved

```
DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
```

Preserved exactly. Only the primary human-authorized operator holds `.1R.24` lifecycle authority. No delegated worker committed, finalized, or pushed. No raw `git commit` / `git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass — governed `pcae` lifecycle only.

---

## 55. Findings summary (all non-blocking; feed `.1R.25` / `.1R.26`)

| ID | Finding | Disposition |
|---|---|---|
| **N-16-4-1** | Current `expires_at = evaluation instant` is unusable for a real positive path (Gate 10 requires `re_expires_at > now` strictly). | `.1R.25` replaces with the §16 dual-bound (generational currentness + bounded wall-clock TTL) model. |
| **N-16-4-2** | The Gate-7 `evaluated_input_digest` does not bind `admission_record_digest` / `admission_class` (bound only at Gate 6). | `.1R.25` adds them as an additive internal digest field (defence in depth; **not** an N-16-6 implementation). |
| **N-16-4-3** | `_pb_decision_digest` does not bind a PB request canonical digest or policy/contract versions. | `.1R.25` adds `pb_request_digest` + `policy_context_versions` to the composition (additive; no PB behaviour change). |
| **N-16-4-4** | The positive branch sets `causing_reason_ids=()` — a positive result must carry an explicit positive rationale. | `.1R.25` sets the §37.1 stable positive reason vocabulary. |
| **N-16-4-5** (observation) | `.1R.16` §35 row 14 labels N-16-4 "PBRD §12 item 5" — the current contract is PBRD-001 **v3.0**; §12 was superseded by §12a; the "item 5" enumeration is `.1R.16`-local. | Non-blocking cross-reference imprecision; `.1R.25` / `.1R.26` should frame N-16-4 as "the positive Gate-7 result over the RDGO-001 v3.1 §8 projection", not "PBRD §12 item 5". |

No new **blocking** finding. N-16-3 is not reopened.

---

## 56. Planning verdict (phase prompt §71)

**N-16-4 ARCHITECTURE / CONTRACT PLAN COMPLETE — IMPLEMENTATION NOT BEGUN.**

**REAL POSITIVE GATE-7 RESULT: ARCHITECTURE FROZEN — NON-BEARER — INVOCATION/ATTEMPT BOUND — DOWNSTREAM GATES STILL REQUIRED.**

- Meaning frozen (§9, §42): "the exact bound invocation/attempt satisfies Runtime Enforcement constraints sufficiently to proceed to Gate 8" — and the explicit negative list (§2.1).
- Vocabulary: Option A (reuse `decision="ALLOW"`); B/C/D rejected (§10).
- Trust model: process-local exact-object identity registry `_GATE7_RESULTS` + constructor seal + non-serializable + identity-only equality (§11); no new trust primitive.
- Identity: `runtime_enforcement_result_id` over the projection + PB + authority-freshness + posture + currentness digests + contract version (§12).
- Currentness/lifetime: generational-first (`currentness_binding` over the authority-generation vector) + bounded wall-clock TTL backstop (§15, §16); N-16-4-1 fix.
- Subordination frozen: Gate 8 still required, Gate 9 owns consumption, Gate 10's 18-step battery unchanged, Slice-B lifecycle untouched, runtime capability (N-16-7) and adapter admission (N-16-6) independent (§17–§22, §48).
- No-go / replay / stale / restart behaviour defined (§23, §32–§34, §33).
- Contract ownership: **new REPRC-001 v1.0** + RDGO-001 v3.1→v3.2 MINOR (optional, blast-radius-gated) (§29, §30).
- Guard-impact / meta-guard / defensive-test / IV plans complete (§39–§41, §45).
- Prerequisite ordering reconfirmed: N-16-3 (CLOSED) → N-16-4 → N-16-5 → N-16-6 → N-16-7 (last); N-16-4 before N-16-5; Slice C / D no phase ID (§48).
- N-23-2 carried; no PBRD/PBNDE edit (§49).
- No production / contract / runtime / effect change by this phase.

Recommended next: `.1R.25` (implementation) → `.1R.26` (IV). **Requires separate explicit human authorization.**

---

## 57. No-go confirmations

- No `src/pcae` file was created, modified, or deleted; `git diff --name-only 1ca1f6ab HEAD -- src/pcae` is empty; `runtime_dispatch_gate7.py` is byte-identical.
- No normative contract file was edited; RDGO-001, PBRD-001, PBNDE-001, PBPA-001, RIHAC-001, RIASC-001, HPAC-001, RPAC-001, the RE No-Go Registry, and `V0_2_EXECUTION_READINESS_NO_GO_GATES.md` are all byte-unchanged.
- No new contract file (`REPRC-001`) was created; it is a conceptual deliverable for `.1R.25`, not authored now.
- No `Gate7Result` schema field, no `run_gate7_runtime_enforcement` change, no `resolve_runtime_enforcement_posture` change, no `_GATE7_RESULTS` behaviour change.
- No positive Gate-7 production path was enabled; production Gate 7 still always returns `Gate7Result(decision="DENY")`; the positive branch remains `pragma: no cover - unreachable in production`.
- No execution was enabled; runtime remains `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities.
- No runtime capability was elevated or promoted; no `Observed -> Approved/Executable` transition; N-16-7 remains untouched and last.
- No Slice C was implemented; no `adapter.dispatch(` call site exists anywhere in `src/pcae`; Slice C / Slice D keep no phase ID.
- No N-16-4 implementation, and no N-16-5 / N-16-6 / N-16-7 work was begun; each remains its own separately authorized implementation + IV pair.
- No adapter (mock or real) was registered, implemented, activated, or called; `RuntimeRegistry` remains empty; no supply-chain admission store or resolver was created or called.
- No credential, secret resolver, FIDO2 / WebAuthn / CTAP, or protected human-approval UI was accessed, created, or referenced; deterministic authentication remains NON_REAL.
- No approval, proof, presentation, challenge, or nonce was consumed on any path; no `consumption.json` was written anywhere.
- No subprocess, process spawn, `os.system`/`popen`/`spawn`/`exec*`, `pty`, provider SDK, HTTP client, socket, or network path was created or invoked; only read-only `git` history inspection and `pcae` governance CLI checks were run.
- No third-party system, unrelated account, provider API, external network, or deployment target was accessed or mutated.
- No test was added, removed, weakened, skipped, xfailed, or renamed; no planning-traceability test was manufactured; no functional-suite evidence was fabricated for a planning-only phase.
- No MAJOR or MINOR contract version was bumped, forced, or overridden; REPRC-001 v1.0 and RDGO-001 v3.2 are conceptual deltas for `.1R.25`, not applied.
- No reopening of a closed gate boundary (Gate 5, 6, 7, 8, 9), the Slice-A / Slice-B verdicts, or the N-16-3 closure.
- No human approval was treated as a policy or enforcement override.
- No raw `git commit` / `git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass; governed `pcae` lifecycle only.
- No delegated worker committed, finalized, or pushed; only the primary human-authorized operator holds `.1R.24` lifecycle authority; `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` is preserved.
- No STOP or BLOCKED condition was reached; every valid early-STOP condition in the phase prompt was checked (§51) and none applies.
- No "Remaining" section is presented; all authorized planning work is complete.
