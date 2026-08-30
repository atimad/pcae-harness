# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.3 Complete — Independent Verification of the Gate-9 Atomic-Consumption Serialization-Semantics Repair

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.15.3
**Type:** independent verification (RE-DERIVE, DO NOT TRUST) — one new test file, no production or contract change
**Status:** INDEPENDENTLY VERIFIED — GATE-9 SERIALIZATION-SEMANTICS REPAIR COMPLETE (durable Gate-10 generation-snapshot representation DEFERRED to `.1R.15.4`)
**Production source changed:** none (`git diff --name-only 735674f7 HEAD -- src/pcae` empty)
**Normative contracts changed:** none (`git diff --name-only d78d9676 HEAD -- docs/contracts schemas` empty)
**Runtime:** `not_implemented / Observed / observe / unavailable`; POL-005 unchanged; real execution UNAVAILABLE; deterministic authentication NON_REAL
**Verification-entry SHA:** `735674f7` · **Immutable pre-repair baseline:** `d78d9676` (`.1R.15.2` functional commit `b32619e5` only)

## Summary

Independent verification of the `.1R.15.2` Gate-9 atomic-consumption
serialization-semantics repair (V-15-1) and the bundled V-15-2 guard
conversion and V-15-3 monkeypatch-hygiene fix. No `.1R.15.2` claim was
accepted from its report, 44 tests, helper names,
`AuthorityGenerationSnapshot`, `_GATE9_RESULTS` membership, or pass counts;
every conclusion re-derived from RDGO-001 v3.0 §10/§15/§17,
HPAC-REQ-095/098/099/100/101, `.1R.9` §12/§18, `.1R.15.1` §14/§17/§19/§20,
and current production source.

**Independently established.** `ast`: exactly one `consumption_store.create`
call site; no `threading` / `fcntl` / `filelock` / `multiprocessing` import
and no `Lock(` / `flock(` / `FileLock(` token — the repair added **no** lock
primitive (`.1R.9` §18 honoured). S1 is captured **only after** the full
HPAC-REQ-099 battery (steps 9–14) — proven by source order **and** by
call-order instrumentation (`_Recorder` shows the first
`authority_generation_resolver` call preceded by `capability_snapshot_resolver`
and `store.resolve`). S2 is re-read **immediately before** the create-only
linearization; an independent source slice from
`_first_authority_generation_drift(s1, s2)` to
`consumption_store.create(...)` contains **exactly one `return`** and none
of `resolve(` / `resolver(` / `run_gate8` / `descriptor_resolver` /
`subprocess` / `open(` / `revalidate_` / `_capture_authority_generation_snapshot`
/ `compute_canonical_digest` / `_build_consumption_record` — **zero
effectful I/O**.

**Token inventory re-derived** — 5 tokens over 4 mutable authority sources:
`principal_generation` / `credential_generation` are whole-record canonical
digests and move on **real** `registry.revoke_principal` /
`registry.revoke_credential`; `lifecycle_generation` digests every
`(sequence, state, event_digest)` of the hash-chained lifecycle and
**subsumes the proof-state token** — proven from HPAC-REQ-094/095 (the proof
lifecycle *is* the immutable event chain; every proof-authority-relevant
mutation is an event in it); `approval_generation` is
**resolver-delegated** (finding N-15-3-2 — see below); `consumption_generation`
is `("absent",)` / `("present", digest)` and a `…DurabilityUncertainError`
propagates → `gate9_consumption_state_durability_uncertain`. All tokens are
pure functions of durable state (restart-reconstructible; no mtime / wall
clock / nonce / process identity — `ast`-verified).

**Drift injection** (real-store mutation and resolver-flip, fired from
inside `_build_consumption_record` — step 15, strictly after S1 and before
S2): principal / credential / lifecycle / approval / multi-drift each →
`gate9_authority_generation_drift:*`, fail closed, **0** `consumption.json`;
a valid consumption record appearing → deterministic `already_consumed`
(**not** a drift rejection), no second create; stable tokens → exactly one
`consumed`. Concurrency: 6 barrier-synced contenders → exactly one winner,
one durable record (8/8 stress loop); a real `revoke_principal` straddling
a contender's S1→S2 window → that contender rejects, 0 records. Crash before
S1 / after S1 / after S2-pre-create → unconsumed; crash after create →
deterministic `already_consumed` (durable record controls restart, incl.
fresh-store retry).

**Practical-limit characterization (honest).** The repair narrows the
window from "one racer's step-9→step-16 duration" to the pure
S2-reads→`create` span. A residual instruction-level micro-window remains —
no lock spans S2→`create` (`.1R.9` §18 forbids a second lock). It is the
practical limit without extending the create primitive into a
conditional-create (Option D, out of scope), produces **no external
effect** (Gate 10 is absent; its `.1R.15.1` §22 forward invariant mandates
full re-read + re-validation + containment re-establishment before any
effect), and is fully closed for the consumption race itself (`O_EXCL` →
`HPACDuplicateError` → `already_consumed`). `.1R.15.4` must normalize
RDGO-001 §10 / `.1R.13.1` §16.2-inv-4 / `.1R.9` §12/§18 to the single
create-only-linearization + zero-I/O-token-recheck model.

**Durable-snapshot deferral — re-derived and CONFIRMED CORRECT.**
HPAC-REQ-098 `authority_binding` is a closed 12-field set with no extension
clause (a 13th field → `HPACMalformedError`, exercised).
`registry_state_digest` is a flat registry/configuration digest
(HPAC-REQ-095 state table; HPAC-REQ-099 "the exact current
registry/configuration state digest") enumerated **separately** from
principal / credential / proof / approval currentness — folding the
generation vector into its preimage broadens its contractual meaning, a
permission **not provable** from the frozen contracts; its production
computation is byte-unchanged from `.1R.14`. **No schema-safe
representation that `.1R.15.2` missed.** The Gate-9 window closes **without**
the durable snapshot; **Gate 10 still must not be planned/implemented**
until `.1R.15.4`/`.1R.15.5` normalize and verify the durable semantics and
the 10-item `.1R.15.1` §20 prerequisite list holds.

## Adjudications

- **V-15-1 — CLOSED FOR THE GATE-9 SERIALIZATION WINDOW.** Durable Gate-10
  generation-snapshot representation DEFERRED TO `.1R.15.4` CONTRACT
  NORMALIZATION (not conflated with the window closure).
- **V-15-2 — CLOSED.** The three `_3w1r2b1r111r31/32/321` guards are
  phase-aware SUBSET invariants (`set(consumers) - AUTHORIZED_CONSUMERS ==
  set()`, explicit 4-tuple enumeration matching the actual production
  imports, no `startswith`/wildcard; a synthetic unauthorized
  `runtime_dispatch_gate10.py` consumer still trips the guard; verifier
  trust-root + `_GATE9_RESULTS` owner + Gate-10 exact-empty asserts kept
  EXACT). Fixed-SHA A/B `-n0`: FAIL@`d78d9676` (16 failed / 110 passed) →
  PASS@`735674f7` (13 failed / 113 passed), the 13 a strict subset of the 16.
- **V-15-3 — CLOSED.** All three raw `_g5mod.is_gate5_result = lambda …`
  assignments replaced with scoped `monkeypatch.setattr`; `is_gate5_result`
  is the original callable after the file; no cross-test pollution across
  the `.1R.14` / `.1R.15` / `.1R.15.2` / `.1R.15.3` suites (239 passed in
  one process).
- **Overall:** INDEPENDENTLY VERIFIED — GATE-9 SERIALIZATION-SEMANTICS
  REPAIR COMPLETE, with the explicit qualification DURABLE GATE-10
  GENERATION-SNAPSHOT REPRESENTATION: DEFERRED TO `.1R.15.4`.

## Regression preservation

V-13-5-1 containment recomputation + read-back runs at step 8 **before** S1
(source-index asserted). `Gate9Result` discipline (identity-only,
`__reduce__` raises, provenance ≠ success, no new downstream consumer)
unchanged. No Gate-10 / adapter / subprocess / socket / provider /
credential / hardware symbol (`ast` + code-only scan). Runtime `Observed /
observe / unavailable` unchanged. Gate 5/6/7/8 + consumption-store +
`runtime_authority` + `hpac_*` production modules **byte-identical**
`d78d9676→735674f7`; the Gate 5/6/7/8 + consumption suites (430 passed) are
identical at both SHAs by construction (modules **and** test files
unchanged). Gate 5 CLOSED / Gate 6 CLOSED / Gate 7 CLOSED / Gate 8 CLOSED —
reconfirmed. All 8 normative contracts byte-unchanged. Consumption-record
schema (exact 12-key `authority_binding` frozenset) unchanged.

## Tests / regression attribution

- Fresh independent suite
  `tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py`
  — **56 passed** (own `_Recorder` call-order instrumentation, own
  source-slice analyzer, own real-store mutators). Stable individually, in
  random order, and interleaved with the `.1R.14` + `.1R.15` + `.1R.15.2`
  suites (**239 passed** in one process).
- **Fixed-SHA A/B** (baseline `d78d9676`, deterministic `-p no:randomly
  -n0`, dedicated `git worktree`, no xdist for primary attribution):
  Gate 5/6/7/8 + consumption-store modules **and** test files byte-identical
  → 430 passed identical at both SHAs; `.1R.14` 63/63, `.1R.15` 76/76
  unchanged; the only functional delta is **+3 intended V-15-2 guard
  passes** plus **+100 new passing tests** (`.1R.15.2` 44 + `.1R.15.3` 56).
  Aggregate `-n0` targeted set: 12 failed / 783 passed at HEAD, the 12 a
  strict subset of the 16 at baseline (pre-existing
  `test_blocking_reproduction_*` / deterministic-fixture guards).
- One wide `-n auto` candidate
  (`test_gate6…::test_gate5_results_registry_stays_empty_on_every_reject`)
  investigated and dismissed: passes deterministically `-n0` isolated / in
  its full file / after this suite; the Gate-6 module + test file are
  byte-identical since baseline; a known `_GATE5_RESULTS`/`_GATE6_DECISIONS`
  xdist cross-file-pollution flake (`.1R.15` §26).
- Concurrency stress: 8 consecutive loop runs — exactly one `consumed` and
  exactly one durable record every run.
- **CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0; UNEXPLAINED
  ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.**

## New findings

- **N-15-3-1 (INFO / test-quality):** `.1R.15.2`'s
  `test_snapshot_has_exactly_the_six_generation_tokens` body asserts
  **five** tokens; the name says "six". Harmless overstatement (same class
  as `.1R.15` §25 notes). Body correct. Not a Gate-10 prerequisite.
- **N-15-3-2 (INFO / carried to `.1R.15.4`):** `approval_generation` is
  fully resolver-delegated; the coordinator holds no approval-store
  reference. An `approval_generation` computed as the immutable RIASC
  `record_digest` alone would **not** move on an approval revocation
  (HPAC-REQ-102 keeps revocation in a separate store) — so approval
  revocation **in the S1→S2 window** depends entirely on the (not-yet-written)
  production resolver. Non-blocking now (no production caller; approval
  revocation **before** S1 is caught by the step-9 `validate_approval`
  re-run). **`.1R.15.4` requirement:** the production
  `authority_generation_resolver` wiring MUST fold approval-revocation-store
  currentness into `approval_generation`.
- **N-15-2-1 / N-15-2-2** carried from `.1R.15.2` and confirmed correct.
- No new blocking findings. No finding reopens a closed gate boundary. No
  finding is class E.

## No-Go Confirmations

- No production source changed in this phase; verification only — one new test file (`git diff --name-only 735674f7 HEAD -- src/pcae` empty).
- No normative contract file changed; RDGO-001, PBRD-001, RIHAC-001, RIASC-001, HPAC-001, RPAC-001, PBPA-001, POL-005 all byte-unchanged.
- No production defect repaired in this phase; the `.1R.15.2` repair was independently verified, not re-implemented.
- No consumption-record schema change; `runtime_invocation_authority_consumption.py` byte-unchanged; `authority_binding` remains the closed 12-field set.
- No durable generation-snapshot representation added; the deferral to `.1R.15.4` is CONFIRMED CORRECT, not overridden.
- No second global lock, transaction system, advisory-lock object, or bearer object introduced or recommended for `.1R.15.3`.
- No Gate-10 design, module, symbol, phase ID, adapter, subprocess, provider, network, credential, or hardware path.
- No `.1R.15.4` work begun; no contract edited, no phase-document erratum applied, no durable-snapshot representation designed.
- No execution enabled; runtime remains `not_implemented / Observed / observe / unavailable`; no capability registration.
- No real FIDO2 / WebAuthn / CTAP / protected approval UI / physical authenticator access.
- No approval / proof / presentation / challenge / nonce consumed on any production path; no `consumption.json` created outside disposable `tmp_path` test stores.
- No Gate 5 / 6 / 7 / 8 production-module change; their modules are byte-unchanged.
- No third-party system, unrelated account, external credential, provider API, external network, or deployment target accessed.
- No test weakened; the concurrency-loser tests retain the RDGO-001 §18 one-winner / one-record guarantee.
- No raw git commit / git push, no --no-verify, no force push, no history rewrite, no hook bypass; the baseline git worktree was read-only and removed.
- No delegated worker committed, finalized, or pushed; only the primary human-authorized operator holds .1R.15.3 lifecycle authority.
- No begin of .1R.15.4 / .1R.15.5; each needs its own separate explicit human authorization.
- No reopening of a closed gate boundary (Gate 5 / 6 / 7 / 8).
- No self-authored closure without evidence; V-15-1 (window) / V-15-2 / V-15-3 closures rest on independently re-derived primary-source analysis, a fresh 56-test suite, and fixed-SHA A/B.
- No Gate-10 phase ID invented; Gate 10 keeps no ID until .1R.15.5 closes VERIFIED and the section 20 prerequisites hold.
- No authorization of the historical delegated .3 finalization, commit, or push; DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED preserved.

## Recommended Next Phase

**149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 — Runtime-Dispatch Contract
Normalization Implementation.** Not begun; requires its own separate
explicit human authorization. Scope (from `.1R.15.1` §24): the §7–§18
proposed deltas — RDGO-001 → v3.1, PBRD-001 → v2.1, RIASC-001 errata, RE
No-Go Registry → schema 1.1, phase-document errata — **plus** the durable
generation-snapshot representation deferred from `.1R.15.2` **plus** the
N-15-3-2 production `authority_generation_resolver` completeness
requirement. Do not begin it. Do not plan or implement Gate 10; it keeps no
phase ID.

---
*Canonical report artifact. Schema version 1.0.*
