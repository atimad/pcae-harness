# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.2 Complete — Gate-9 Atomic-Consumption Serialization-Semantics Repair

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.15.2
**Type:** narrow production repair (V-15-1) + bundled test-hygiene (V-15-2, V-15-3)
**Status:** IMPLEMENTED — INDEPENDENT VERIFICATION PENDING — V-15-1 NOT YET CLOSED
**Production source changed:** `src/pcae/core/runtime_dispatch_gate9.py` only (`git diff --name-only d78d9676 HEAD -- src/pcae`)
**Normative contracts changed:** none (`git diff --name-only d78d9676 HEAD -- docs/contracts` empty)
**Consumption-record schema:** unchanged (`runtime_invocation_authority_consumption.py` byte-unchanged; `authority_binding` remains the closed 12-field set)
**Runtime:** `not_implemented / Observed / observe / unavailable`; POL-005 unchanged; real execution UNAVAILABLE
**Phase-entry SHA:** `d78d9676` · **.1R.15.1 planning baseline:** `a56bd253`

## Summary

Narrow V-15-1 Gate-9 serialization-semantics repair frozen by `.1R.15.1`
§14 (Option B), **in-memory only**. `run_gate9_atomic_authority_consumption`
captures a monotonic `AuthorityGenerationSnapshot` **S1** the instant the
full HPAC-REQ-099 in-boundary revalidation battery (steps 9–14) succeeds
(step 14a), re-reads it as **S2** immediately before the create-only
linearization with **zero intervening effectful I/O** (step 15a), and fails
closed on any change — no `consumption.json`, no Gate 10.

**Tokens** (all whole-record / full-chain digests over canonical durable
state, restart-reconstructible; no wall-clock / mtime / nonce /
selected-field digest): `principal_generation` / `credential_generation` /
`approval_generation` via a new trusted `authority_generation_resolver` DI
parameter (same pattern as `descriptor_resolver` /
`capability_snapshot_resolver`); `lifecycle_generation` = digest over every
`(sequence, state, event_digest)` of `resolve_canonical_chain(proof_id)`
(**subsumes** the proof-state token — dedup proven); `consumption_generation`
= `("absent",)` / `("present", digest)` / durability-uncertain → fail
closed. The per-`proof_id` create-only atomic primitive remains the **sole**
linearization point — no second lock, no transaction system, no bearer
object.

**Contract-embedding decision (surfaced to and adjudicated by the primary
operator per §6/§24).** HPAC-REQ-098 defines `authority_binding` as a
closed 12-field set with no extensibility clause; `registry_state_digest`
normatively denotes the registry/configuration digest (HPAC-REQ-095/099),
**not** the full mutable-authority-generation vector — that semantic
permission is **not provable** from the frozen contracts. Therefore the
persisted consumption record is **left unchanged** and **durable /
re-readable generation-state commitment for Gate 10's second line of
defense is DEFERRED TO `.1R.15.4` contract normalization** — explicitly,
not silently satisfied.

Final disposition distinguishes:
- **V-15-1 production race window: REPAIRED — INDEPENDENT VERIFICATION PENDING**
- **durable Gate-10 generation-snapshot representation: DEFERRED TO `.1R.15.4` CONTRACT NORMALIZATION**
- **V-15-2 REPAIRED — VERIFICATION PENDING** (three `_3w1r2b1r111r31/32/321` HPAC-foundation zero-consumer guards → phase-aware subset invariants; FAIL@`d78d9676` → PASS@HEAD)
- **V-15-3 REPAIRED — VERIFICATION PENDING** (three raw `is_gate5_result` assignments → `monkeypatch.setattr`)

## Threat model — drift injected in the S1→S2 window (real canonical stores)

Principal revocation, credential revocation, lifecycle-head change,
approval-state change, and multi-drift each → `gate9_authority_generation_drift:*`,
fail closed, **0** consumption records. A valid consumption record
appearing between S1 and S2 → deterministic `already_consumed`, **no second
create**. Stable tokens → exactly one `consumed`. Crash-before-S2 /
crash-after-S2-pre-create → unconsumed; crash-after-create → durable record
+ deterministic `already_consumed` on retry. Concurrency (4 barrier-synced
contenders): exactly one `consumed`, exactly one durable canonical record —
RDGO-001 §18 unchanged. Every drift outcome is fail-safe (the one-shot
authority is burned, never escalated) and produces no external effect.

## Regression preservation

V-13-5-1 containment recomputation + read-back runs at step 8 **before**
S1 (source-order asserted). Gate9Result discipline (identity-only,
`__reduce__` raises, provenance ≠ success, no new downstream consumer)
unchanged. No Gate-10 / adapter / subprocess / socket / provider /
credential / hardware symbol. Runtime `Observed / observe / unavailable`
unchanged. **Gate 5/6/7/8 production modules byte-unchanged.** All 8
normative contracts byte-unchanged.

## Tests / regression attribution

- New focused suite `tests/test_gate9_serialization_semantics_repair_3w1r2b1r1_1r15_2.py` — **44 passed**.
- `.1R.14` 63/63, `.1R.15` 76/76 (resolver DI wired; 0 functional change).
- Adjacent Gate 5–8 + B1/B7/N1/N2 + runtime-authority 383/383; consumption store + `.1R.13.5` 127/127.
- **Fixed-SHA A/B** (baseline `d78d9676`, `git stash`): the 3 V-15-2 guards FAIL@baseline → PASS@HEAD; the ~13 remaining HPAC-foundation-reproduction / HATP-contract-byte failures are pre-existing and identical at baseline.
- **CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0; UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.**

## New findings

- **N-15-2-1 (INFO):** `revoke_credential` rewrites the shared principal/credential registry document, so `principal_generation` also moves on a pure credential revocation. Fail-safe (either token moving blocks the create); first/aggregate-mismatch reporting per RDGO-001 §15. Not a prerequisite for anything.
- **N-15-2-2 (carried to `.1R.15.4`):** the durable Gate-10 generation-snapshot representation requires a normative schema change.
- No new **blocking** findings. No self-close of V-15-1 / V-15-2 / V-15-3.

## No-Go Confirmations

- No normative contract file changed; RDGO-001, PBRD-001, RIHAC-001, RIASC-001, HPAC-001, RPAC-001, PBPA-001, POL-005 all byte-unchanged.
- No consumption-record schema change; `runtime_invocation_authority_consumption.py` byte-unchanged; `authority_binding` remains the closed 12-field set.
- No 13th `authority_binding` field; no structured value smuggled into an existing digest field; durable representation DEFERRED to `.1R.15.4`, not silently satisfied.
- No second global lock, transaction system, or bearer object; the per-`proof_id` create-only primitive remains the sole linearization point.
- No Gate-10 design, module, symbol, phase ID, adapter, subprocess, provider, network, credential, or hardware path.
- No execution enabled; runtime remains `not_implemented / Observed / observe / unavailable`; no capability registration.
- No real FIDO2 / WebAuthn / CTAP / protected approval UI / physical authenticator access.
- No approval / proof / presentation / challenge / nonce consumed on any production path; no `consumption.json` outside disposable `tmp_path` test stores.
- No Gate 5 / 6 / 7 / 8 production-module change.
- No third-party system, unrelated account, external credential, provider API, external network, or Dell deployment target accessed.
- No test weakened; concurrency-loser tests retain the RDGO-001 §18 one-winner / one-record guarantee.
- No raw git commit / git push, no --no-verify, no force push, no history rewrite, no hook bypass.
- No delegated worker committed, finalized, or pushed; only the primary human-authorized operator holds .1R.15.2 lifecycle authority.
- No begin of .1R.15.3 / .1R.15.4 / .1R.15.5; each needs its own explicit human authorization.
- No reopening of a closed gate boundary (Gate 5 / 6 / 7 / 8).
- No self-close of V-15-1 / V-15-2 / V-15-3.
- No authorization of the historical delegated .3 finalization, commit, or push; DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED preserved.

## Recommended Next Phase

**149O.20L.7O.3W.1R.2B.1R.1.1R.15.3 — Independent Verification of the
Gate-9 Serialization-Semantics Repair.** Not begun; requires its own
separate explicit human authorization. The verification must additionally
re-derive the contract-embedding analysis and confirm the durable-snapshot
deferral is correct. Do not begin `.1R.15.4`. Do not plan or implement
Gate 10; it keeps no phase ID.

---
*Canonical report artifact. Schema version 1.0.*
