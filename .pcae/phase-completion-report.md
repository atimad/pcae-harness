# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.24 Complete — N-16-4 Real Positive Single-Attempt Runtime Enforcement Gate Architecture and Contract Planning

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.24
**Type:** planning / primary-source analysis / contract-impact analysis / threat-modeling / decision-freezing only
**Status:** N-16-4 ARCHITECTURE / CONTRACT PLAN COMPLETE — IMPLEMENTATION NOT BEGUN — REAL POSITIVE GATE-7 RESULT: ARCHITECTURE FROZEN — NON-BEARER — INVOCATION/ATTEMPT BOUND — DOWNSTREAM GATES STILL REQUIRED
**Phase-entry SHA:** `1ca1f6ab` (`origin/main` synced; `origin/main..HEAD = 0` at entry)
**Production source changed:** none (`git diff --name-only 1ca1f6ab HEAD -- src/pcae` empty; `runtime_dispatch_gate7.py` byte-identical)
**Normative contracts changed:** none (`git diff --name-only 1ca1f6ab HEAD -- docs/contracts docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` empty)
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; FIRST EXTERNAL EFFECT ABSENT; execution NOT enabled

## Summary

Planning / primary-source analysis / contract-impact analysis / threat-modeling / decision-freezing only. Re-derived N-16-4 from primary source (RDGO-001 v3.1 all 21 sections; PBNDE-001 v1.0; the RE No-Go Registry schema 1.1; NG-025; the legacy Phase-102 `RuntimeEnforcementDecision` freeze; `src/pcae/core/runtime_dispatch_gate7.py` **read in full**; `src/pcae/core/runtime_dispatch_gate10_eligibility.py` **read in full**; the Gate-7 consumption paths in `runtime_dispatch_gate8.py` / `gate9.py`; `runtime_enforcement_safety_authorization.py`; `.1R.16` §35 row 14 = the N-16-4 mandate; `.1R.13.1` / `.1R.13.2` / `.1R.13.3` Gate-7 frozen decisions), not from phase summaries.

**Central finding (frozen).** Gate 7's positive `Gate7Result(decision="ALLOW", …)` branch **already exists** — sealed (`_GATE7_RESULT_CONSTRUCTOR_SEAL`), non-serializable (`__reduce__` raises), registry-provenanced (`_GATE7_RESULTS`), identity-only equality, `# pragma: no cover - unreachable in production` — and is **already consumed** by three frozen downstream gates: Gate 8 binds `_gate7_result_digest(gate7_result)` into the containment evidence; Gate 9 writes `consumption.json` item 7 `runtime_enforcement_binding = {verdict, expires_at, evaluated_input_digest, decision_digest}`; Gate-10 pre-effect eligibility requires `is_gate7_result` + `decision == "ALLOW"` + `gate8_result.gate7_result_digest == _gate7_result_digest(gate7_result)` + durable `re_binding.verdict == "ALLOW"` + `re_expires_at` strictly after now. **N-16-4 is therefore fundamentally a contract-freeze**, not a green-field build: what is missing is a frozen contract governing what the positive object *means*, how its trust is anchored, its identity, its currentness/lifetime, and its replay semantics.

## Frozen architecture

- **Meaning (§9, §42):** a positive Gate-7 result asserts **only** "the exact bound `runtime_dispatch` invocation/attempt satisfies Runtime Enforcement constraints sufficiently to proceed to Gate 8". Explicit negative list: **not** permission to execute/dispatch; **not** runtime capability / adapter availability; **not** effect authorization; **not** human authority (created, consumed, or refreshed); **not** PB permission; **not** a `DispatchEnvelope`; **not** a substitute for Gates 8, 9, or the Gate-10 read-back.
- **Vocabulary (§10):** **Option A** — reuse `decision="ALLOW"`. **B / C / D rejected explicitly**: a rename ripples through three frozen gates + their IV suites for a cosmetic gain; a second typed result doubles the provenance surface; a separate "certificate" between Gate 7 and Gate 8 is exactly the extra bearer token the walls forbid.
- **Non-bearer trust model (§11):** the process-local exact-object identity registry `_GATE7_RESULTS` (keyed by `id(self)`), backed by the constructor seal, `__reduce__`-raises non-serializability, identity-only `==` / `hash`, and `__init_subclass__`-raises. **No new trust primitive** — this is byte-identical to how `Gate5Result` / `Gate6Decision` / `Gate8Result` / `Gate9Result` / `DispatchEnvelope` already work. The F7 same-account autonomous-agent boundary is carried verbatim; the threat model is **not** broadened.
- **Result identity (§12):** `runtime_enforcement_result_id` = canonical digest over `invocation_id` / `attempt_id` / `idempotency_key` + `pb_decision_digest` + `evaluated_input_digest` + `authority_freshness_digest` + `runtime_posture_digest` + a **new** `currentness_binding` + the literal `"REPRC-001/1.0"`. Not frozen as the exact formula — derived by the recommended implementation phase from the then-current composition; added as an additive `__slots__` field.
- **Currentness / lifetime (§15, §16):** **generational-first** — a `currentness_binding` digest over the authority-generation vector (principal / credential / approval / lifecycle generation tokens, the same markers Gate 9 captures), invalid the moment any bound digest no longer matches a fresh re-derivation — **plus** a bounded wall-clock TTL backstop (`expires_at` = earlier of the projection's expiry verdict and `evaluated_at + REPRC_MAX_RESULT_TTL`). Wall-clock expiry alone is **insufficient**.
- **Subordination frozen (§17–§22, §48):** Gate-7 ALLOW → **Gate 8 still independently required** (binds `_gate7_result_digest`; rejects a negative `Gate7Result` before Shell Gate evaluation). Gate 9 remains the **sole owner** of authority consumption — `Gate-7 result != authority consumption`. Gate-10's 18-step pre-effect battery is **unchanged** — `Gate-7 ALLOW != DispatchEnvelope != effect authority`. The Slice-B `RuntimeInvocationRecord` is **never** read or written by Gate 7. Runtime capability (N-16-7) and adapter admission (N-16-6) stay **independent** — Gate 7 evaluates only the admission evidence Gate 6 already bound and performs no live admission lookup and calls no `SupplyChainAdmissionResolver`.
- **Positive-path no-go (§23, §25):** any applicable unresolved **per-decision** hard no-go → `DENY`. **No "trusted narrow profile" shortcut** around Runtime Enforcement no-gos.
- **Persistence (§33):** **Model A** — no durable positive-result store; recompute Gate 7 after restart; the durable truth that survives restart is Gate 9's `consumption.json` `runtime_enforcement_binding`. Models B (durable positive-result store) and C (hybrid) **rejected explicitly**.
- **Replay / stale (§32–§34):** every transplant / copy / `deepcopy` / serialized / reconstructed / forged result and every authority-currentness mutation is rejected by a **named component** (three independent layers today: `is_gate7_result` registry membership; per-gate invocation/attempt/request lineage equality against the live `identity`; `_gate7_result_digest` cross-check bound into the containment evidence and `consumption.json`).

## Contract ownership and versioning

**Frozen: a new dedicated contract `REPRC-001` v1.0** (Runtime Enforcement Positive-Result Contract) — directly analogous to how PBNDE-001 v1.0 was born for N-16-3 — **plus an optional RDGO-001 v3.1 → v3.2 MINOR** clarifying cross-reference in §8 (blast-radius-gated: if the `RDGO-001/3.1` cross-ref sprawl across `src/` + `docs/` is large, keep RDGO at v3.1 and put the clarification only in REPRC-001, per the `.1R.22` sibling-bump-cascade lesson). **No MAJOR contract bump.** The versioning matrix reads each contract's own rules first (RDGO §21's enumerated MINOR criteria; PBNDE §10 / PBRD §16 initial-freeze precedent; the RE No-Go Registry additive-only rule) — deliberately avoiding the `.1R.21` versioning mistake.

**RE No-Go Registry: NO CHANGE.** RE-NOGO-001's per-decision projection simply un-matches for a synthetic fully-satisfied `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile, while RE-NOGO-002 / RE-NOGO-010 / RE-NOGO-011 keep every production and end-to-end path blocked. No new `RE-NOGO-*` entry. NG-025's existing PBNDE-001 §9 annotation already covers the carve-out.

**Sequence: Path X (inline, the N-16-3 precedent)** — planning (`.1R.24`) → implementation with inline REPRC-001 v1.0 authorship as the first commit (`.1R.25`) → IV (`.1R.26`). A separate contract-freeze phase is **not** required (initial freeze, no incumbent to migrate; the RDGO change is a MINOR pointer). Documented fallback: if `.1R.25` primary-source review finds REPRC-001 forces a MAJOR RDGO state-machine change or merges authority/permission/enforcement/containment, `.1R.25` **STOPS** and re-adjudicates to a separate freeze phase + shifted impl/IV IDs — exactly as `.1R.22` STOPPED when POL-005's versioning turned out MAJOR.

## Production positive path after N-16-4 alone: NONE

Two independent, currently-insurmountable walls remain: **(1) the N-16-5 authority wall** — `validate_approval` hard-stops on a NON_REAL lineage, so no valid `human_authority_binding` for a real request exists → `Gate5Result` cannot carry a revalidating projection → Gate 7 step 5 `gate7_stale_validated_authority_projection` (and the profile's human-authority predicates fail → `Gate6Decision(decision="DENY")` → Gate 7 step 2 `gate7_pb_decision_not_allow:DENY`); **(2) the N-16-6 admission wall** — the sole production `SupplyChainAdmissionResolver` is `_NonAdmittingSupplyChainAdmissionResolver` (admits nothing) → `P_supply_chain_admission` always fails → same `DENY` cascade. And even if both were hypothetically satisfied, `resolve_runtime_enforcement_posture()` returns `execution_available == False` and `matched_no_go_ids ⊇ {RE-NOGO-002, RE-NOGO-010, RE-NOGO-011}` → Gate 7 step 7 `DENY`. A positive Gate-7 result is structurally reachable **only** on the clearly-labelled synthetic test path (local/in-memory, underscore-private documented-test-only substitution seams, no adapter / capability / network / credential / hardware / FIDO2 / WebAuthn / CTAP).

**First external effect: still UNREACHABLE** even after a future `.1R.25` — no `adapter.dispatch()` call site exists anywhere in `src/pcae` (*absent*, not merely unreachable); `RuntimeRegistry` empty; `execution_availability` unavailable; Slice C has no phase ID.

## Non-blocking findings (feed the recommended implementation and IV phases)

- **N-16-4-1** — the current `expires_at = evaluation instant` is unusable for a real positive path (Gate 10 requires `re_expires_at` strictly after now) → the recommended implementation phase replaces it with the dual-bound (generational currentness + bounded wall-clock TTL) model.
- **N-16-4-2** — bind `admission_record_digest` / `admission_class` into the Gate-7 `evaluated_input_digest` (defence in depth; **not** an N-16-6 implementation, **not** a new resolver call).
- **N-16-4-3** — bind a PB request canonical digest + policy/contract versions into `_pb_decision_digest`.
- **N-16-4-4** — the positive branch sets `causing_reason_ids=()`; a positive result must carry an explicit positive rationale vocabulary.
- **N-16-4-5** (observation) — `.1R.16` §35 row 14's "PBRD §12 item 5" label predates PBRD-001 v3.0 §12a; frame N-16-4 as "the positive Gate-7 result over the RDGO-001 v3.1 §8 projection".

**No new blocker. N-16-3 is CLOSED and not reopened. N-23-2 carried (INFO / DEFERRED NORMALIZATION DEBT — N-16-4 does not create a natural normalization point; no PBRD/PBNDE edit). N-23-1 carried.**

## Prerequisite ordering (reconfirmed, frozen)

N-16-3 (**CLOSED**) → N-16-4 → N-16-5 (real FIDO2 / WebAuthn / CTAP + protected human-approval UI) → N-16-6 (RPAC-REQ-095 fixed-argv external-executable adapter + supply-chain admission) → N-16-7 (runtime capability enablement `Observed → Approved/Executable` — **strictly last**). **N-16-4 lands before N-16-5**: a synthetic/test-only positive Runtime Enforcement implementation is independently useful (it freezes the positive-result contract and makes the downstream positive-path handling testable end-to-end) and safe (local/in-memory, underscore-private test seams only, no capability/adapter/credential/network, production Gate 7 stays `DENY`-only) — the exact pattern Gates 8 and 9, Slice A, and Slice B were built and verified on before real authority existed. Slice C (first concrete effect adapter integration) and Slice D (independent end-to-end verification of the first external effect) keep **no phase ID** until N-16-3..7 all independently close.

## Canonical planning matrices (16)

Produced in the canonical doc: (1) current Gate-7 behavior; (2) structural-vs-temporary DENY; (3) trusted input ownership; (4) RDGO v3.1 projection; (5) no-go ownership; (6) Gate 6→7 consumption; (7) result schema; (8) result currentness/invalidation; (9) downstream gate relationship; (10) persistence/restart options; (11) option comparison/rejection; (12) contract versioning; (13) predicted guard-impact inventory; (14) defensive test matrix (38 cases); (15) implementation/IV phase decomposition; (16) whole authority chain + authority-creation table.

## Whole-system authority chain (post-N-16-4)

real human authentication/approval (N-16-5; today NON_REAL, **creates** authority) → Gate 5 approval validation (**evidences**) → Gate 6 PB policy decision (**creates** policy permission) → **Gate 7 Runtime Enforcement decision** (`Gate7Result` — **evidences** "may proceed to Gate 8"; creates no authority, consumes none, reusable = no, durable = no, can cause effect = no) → Gate 8 process containment (**evidences** containment) → Gate 9 atomic authority consumption + durable pre-dispatch record (**consumes** approval + proof + presentation + challenge, once, atomically) → Gate-10 pre-effect eligibility / `DispatchEnvelope` (**evidences** pre-effect readiness; "authorizes nothing") → Slice-B durable attempt lifecycle (**evidences** attempt state; grants no effect authority) → runtime capability (N-16-7; enabling condition, not authority; today `unavailable`) → Slice-C adapter dispatch (no phase ID — **FIRST EXTERNAL EFFECT**). **Gate 7 never appears as final effect authority.**

## Governance

- `pcae health` healthy · `pcae check` passed · `pcae status coherence` coherent · `pcae push check` `nothing_to_push` (pre-push) · `pcae doctor task-memory` warning-only historical `DONE.md` omissions (pre-existing hygiene debt; no current-phase error) · `pcae runtime inspect` `not_implemented / Observed / observe / unavailable`, 0/0.
- **DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED** — preserved. Only the primary human-authorized operator holds `.1R.24` lifecycle authority. Governed `pcae` lifecycle only — no raw `git commit`/`git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass.
- No STOP / BLOCKED condition reached — every valid early-STOP condition in the phase prompt was checked (§51) and none applies.

## Verdict

**N-16-4 REAL POSITIVE SINGLE-ATTEMPT RUNTIME ENFORCEMENT GATE ARCHITECTURE AND CONTRACT PLAN COMPLETE — PLANNING ONLY.** N-16-4 NOT implemented; Gate-7 production behaviour unchanged (still always `DENY` on the production path); FIRST EXTERNAL EFFECT still ABSENT; execution NOT enabled. REAL POSITIVE GATE-7 RESULT: ARCHITECTURE FROZEN — NON-BEARER — INVOCATION/ATTEMPT BOUND — DOWNSTREAM GATES STILL REQUIRED.

**Runtime: Observed / observe / unavailable. First external effect: ABSENT. Execution enabled: NO.**

## Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.25` — **N-16-4 Real Positive Single-Attempt Runtime Enforcement Gate Implementation** → then `149O.20L.7O.3W.1R.2B.1R.1.1R.26` — **Independent Verification of the N-16-4 Runtime Enforcement Gate**. Each requires its own separate explicit human authorization; IDs recommended, NOT reserved. **Do not implement `.1R.25` / `.1R.26`.** Do not begin N-16-5..7. Do not begin Slice C. Do not implement or call the first external effect. Do not enable execution.

See `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_24_N_16_4_REAL_POSITIVE_SINGLE_ATTEMPT_RUNTIME_ENFORCEMENT_GATE_ARCHITECTURE_AND_CONTRACT_PLANNING.md`.
