# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19 — Dispatch-Attempt Durable Lifecycle, Idempotency, and 3S.2.1 Prerequisite Repairs

**Type:** implementation (Slice B of the `.1R.16` Gate-10 plan).
**Status:** IMPLEMENTED — INDEPENDENT VERIFICATION PENDING (`.1R.20`).
**Phase-entry SHA:** `a2b679fe` (`origin/main` synced; `origin/main..HEAD = 0` at entry).
**First external effect:** ABSENT. No `adapter.dispatch()` call site, no `runtime_dispatch_gate10.py`, no real adapter, no process/socket/provider/credential path. Execution not enabled.
**Runtime posture:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; POL-005 hard DENY — all unchanged.
**Governance:** governed `pcae` lifecycle only. The delegated `.3` finalization / commit / push incident remains **UNAUTHORIZED**; only the primary human-authorized operator holds `.1R.19` lifecycle authority.

This is the canonical artifact required by the phase prompt §61 step 22 / §63.

---

## 1. Governing planning baseline (phase prompt §1 / §3)

Re-read in full at phase entry: `.1R.16` (Gate-10 architecture — §20, §22, §24, §25, §31, §34, §36.2, §38 in particular), `.1R.17` (Slice-A implementation), `.1R.18` (Slice-A IV — BLOCKED), `.1R.17R` (scope-fence + erratum reconciliation), `.1R.17R.1` (reconciliation IV — CLOSED); `3S.2.1` (§20, §26, §27, §29, §44, §61, §62 — the two MUST-FIX items and item 9); RPAC-001 v1.0 §13 (RPAC-REQ-064–072), RDGO-001 v3.1 (§10a, §11, §17, §18), PBRD-001 v2.1 §12, HPAC-001 v2.1 §41. Current production source read line-by-line: `runtime_invocation.py`, `runtime_adapter.py`, `runtime_introspection.py`, `runtime_snapshot.py`, `runtime_dispatch_gate10_eligibility.py`, `runtime_dry_consumption.py`, `runtime_inspect.py`, `permission_broker_foundation.py` (POL-005).

Treated as frozen unless primary evidence disproves it (none does): Gate 5–9 CLOSED; Gate-10 pre-effect eligibility + `DispatchEnvelope` VERIFIED (`.1R.17` / `.1R.17R.1`); Slice-A lifecycle acceptance CLOSED; first external effect ABSENT; runtime `Observed / observe / unavailable`.

## 2. Initial repository inspection (phase prompt §4)

```
git status --short / --branch --short   -> clean; ## main...origin/main
git log --oneline origin/main..HEAD     -> (empty); rev-list --count = 0
git rev-parse HEAD                       -> a2b679fe
pcae health / check / status coherence   -> healthy / passed / coherent
pcae doctor task-memory                  -> warning-only (pre-existing O4 tasks/DONE.md omissions); no current-phase error
pcae push check                          -> Mode: nothing_to_push; phase-report trust + identity: passed
pcae runtime inspect                     -> not_implemented / Observed / observe / unavailable; 0 plugins / 0 capabilities
pcae notify status                       -> Telegram configured, enabled, outbound-ready
pcae phase-report show --latest          -> .1R.17R.1 — INDEPENDENTLY VERIFIED WITH NON-BLOCKING FINDINGS
```

Confirmed: `.1R.17R.1` is the latest completed phase; repository clean; no active governed phase before this phase's task was opened; `origin/main..HEAD = 0`; runtime remains `Observed / observe / unavailable`.

## 3. Core Slice-B semantic wall (phase prompt §5)

`RuntimeInvocationRecord != permission != human approval != PB ALLOW != runtime capability != authorization to dispatch`. It is a **non-authoritative durable mirror / evidence record**. Possession, reconstruction, copying, or parsing of it grants nothing. This is enforced structurally: `RuntimeInvocationRecord` has no `approve` / `authorize` / `permit` / `grant` / `consume` method and no `execution_allowed` / `permission` / `authorized` field; `RuntimeInvocationRecord.GRANTS_NO_EFFECT_AUTHORITY` is a permanent load-bearing marker; `record_grants_no_effect_authority()` always returns `True`. The authoritative at-most-once authority-consumption truth stays `consumption.json` (`HPAC-AUTHORITY-CONSUMPTION/2.1`), which every consumer re-reads (RDGO-001 v3.1 §11).

## 4. Production files changed (phase prompt §50)

| File | Change | Effect sensitivity |
|---|---|---|
| `src/pcae/core/runtime_dispatch_attempt_lifecycle.py` *(new, 690 lines)* | The dispatch-attempt durable lifecycle mirror: `RuntimeInvocationRecord` header + append-only chained transition log + write-before-effect at-most-once guard + crash/restart determination + deterministic idempotency identity. Non-authoritative, non-effecting. | none — records only; imports only `json`, `os`, stdlib, `pcae.core.hpac_foundation` |
| `src/pcae/core/runtime_invocation.py` | 3S.2.1 MUST-FIX #2: `RuntimeInvocationStore` sanitizes `invocation_id` / `attempt_id` (`require_safe_relative_id_component` grammar) + a resolved-path `_assert_within_root` containment check on every create. | low — path confinement only |
| `src/pcae/core/runtime_adapter.py` | 3S.2.1 MUST-FIX #1: `simulate_invocation` validates the `adapter.dispatch()` receipt and the `adapter.collect()` return (`malformed_adapter_result_reasons`) and fails closed with `FAILURE_MALFORMED_RESULT` before any state write / `store.write_result()` — never an uncaught `AttributeError`, never a persisted `result.json`. `dispatch()` / `collect()` exceptions are also caught → fail closed. | low — still exactly one `resolved.adapter.dispatch(` call site; still simulation-only |
| `src/pcae/core/runtime_introspection.py` | 3S.2.1 item-9 runtime-inspect discoverability repair: additive observational `RuntimeAdapterSurfaceInfo` + frozen `RUNTIME_ADAPTER_SURFACES` tuple + `get_adapter_surfaces()` — static data only, reads no registry, instantiates nothing, mutates nothing. | none |
| `src/pcae/commands/runtime_inspect.py` | Renders the observational surface list: a one-line summary in the default view + a detail section in `--verbose`, sourced from `get_adapter_surfaces()`. **`--json` output is byte-unchanged** — the 112F 9-key JSON contract is untouched. | none |

`runtime_dispatch_gate10_eligibility.py` (the Slice-A coordinator) is **byte-unchanged** (`git diff a2b679fe HEAD -- src/pcae/core/runtime_dispatch_gate10_eligibility.py` empty). Gate 5–9 + `runtime_invocation_authority_consumption.py` are **byte-unchanged**. `runtime_snapshot.py` is **byte-unchanged**. No `docs/contracts/**` change.

## 5. RPAC / RDGO lifecycle derivation (phase prompt §6–§19)

Re-derived from RPAC-REQ-067 (persistent append-only `RuntimeInvocationRecord`), RPAC-REQ-064/065/066 (identity + idempotency key + resume/collision), RPAC-REQ-068 (restart before dispatch resumes validation; restart after an intent/receipt boundary with unknown outcome records `ambiguous_outcome` and SHALL NOT auto-redispatch), RPAC-REQ-069/070 (duplicate-completion idempotent replay vs conflicting-completion quarantine; deterministic candidate identity), RPAC-REQ-071/072 (retry classes; every retry needs a new `attempt_id` + fresh gates + human authorization), RDGO-001 v3.1 §17 (crash-state table) and §18 (no automatic retry).

### 5.1 State machine

```
none ──▶ PREPARED ──▶ EFFECT_ATTEMPT_STARTED ──▶ RECEIPT_CAPTURED   (terminal)
              │                    └──────────▶ DISPATCH_UNCERTAIN  (terminal)
              └───────────────────────────────▶ DISPATCH_NOT_STARTED (terminal)
```

The `.1R.16` §22.3 state names are used verbatim (RPAC does not define alternate names for this mirror). RDGO-001 v3.1 §17's crash-state vocabulary (`DISPATCH_ATTEMPTED`, `DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER`, `DISPATCH_UNCERTAIN`, `RESULT_CAPTURED_UNTRUSTED`) is the *disposition* vocabulary `resolve_disposition()` returns.

### 5.2 Transition matrix

| source \ dest | PREPARED | EFFECT_ATTEMPT_STARTED | RECEIPT_CAPTURED | DISPATCH_UNCERTAIN | DISPATCH_NOT_STARTED |
|---|---|---|---|---|---|
| *(none)* | **ALLOW** | DENY (skip) | DENY (skip) | DENY (skip) | DENY (skip) |
| PREPARED | NO-OP / idempotent | **ALLOW** | DENY (skip) | DENY (skip) | **ALLOW** |
| EFFECT_ATTEMPT_STARTED | DENY (backwards) | DENY (duplicate; → `DispatchAttemptAlreadyStartedError`) | **ALLOW** | **ALLOW** | DENY (skip) |
| RECEIPT_CAPTURED | DENY | DENY | NO-OP if same detail digest / DENY conflicting | DENY | DENY |
| DISPATCH_UNCERTAIN | DENY | DENY | DENY | NO-OP / DENY conflicting | DENY |
| DISPATCH_NOT_STARTED | DENY | DENY | DENY | DENY | NO-OP / DENY conflicting |

Exactly **5 ALLOW edges** in the whole matrix (asserted by `test_transition_matrix_full_classification`). Every other requested edge is DENY. `next_dispatch_attempt_transition()` enforces `DISPATCH_ATTEMPT_TRANSITIONS` exactly; a duplicate terminal with an identical `detail` digest is an idempotent replay (RPAC-REQ-069), a conflicting `detail` is a `DispatchAttemptIntegrityError`.

### 5.3 State semantics

* **PREPARED** — all pre-effect material needed to identify the future attempt is durably recorded; **no external effect attempted**; retry may still be governed per the lifecycle. It is not by itself an authorization to dispatch.
* **EFFECT_ATTEMPT_STARTED** (decisive) — PCAE has durably crossed the point after which automatic retry of this exact attempt is prohibited. It does **not** mean an external effect occurred, the adapter accepted the request, a result exists, or the effect succeeded.
* **RECEIPT_CAPTURED** (terminal) — a future effect-bearing component produced a receipt/evidence object and the mirror captured it. `receipt != authority` (RPAC-REQ-036; RDGO-001 v3.1 §19). A synthetic receipt shape may be modelled; no real receipt is created (no adapter is called).
* **DISPATCH_UNCERTAIN** (terminal) — PCAE cannot establish whether a future external effect occurred after the attempt-start boundary. Automatic retry prohibited; manual/governed resolution required. Uncertainty is never downgraded to "not started".
* **DISPATCH_NOT_STARTED** (terminal) — used **only** where the durable lifecycle can prove no external effect was started (reachable only from `PREPARED`); never for an ambiguous failure.

### 5.4 Write-before-effect ordering

```
PREPARED persisted
   ▶ EFFECT_ATTEMPT_STARTED persisted        ← this phase
   ▶ [future first external effect — NOT PRESENT IN THIS PHASE — Slice C]
```

Model A (write-before-effect) + Model C (two-state lifecycle), per `.1R.16` §22.2: Model A's failure mode (a false "attempted" after a crash) is fail-closed (`DISPATCH_UNCERTAIN` + fresh human authority, one one-shot authority wasted at worst); Model B's (a duplicate external effect) is fail-open and is rejected. No effect primitive is added — `runtime_dispatch_attempt_lifecycle.py` imports only `json`, `os`, `dataclasses`, `pathlib`, `typing`, and `pcae.core.hpac_foundation`.

### 5.5 At-most-once dispatch-attempt guarantee

Once `EFFECT_ATTEMPT_STARTED` is durable for an attempt identity: a second `begin_effect_attempt()` raises `DispatchAttemptAlreadyStartedError`; a restart (fresh store object, durable state only) observes the marker and refuses; an unresolved started attempt resolves to `DISPATCH_UNCERTAIN` and fails closed. This is **at-most-once attempt**, not generic exactly-once external effect — the future external system may provide neither atomicity nor idempotency, so `DISPATCH_UNCERTAIN` + durable uncertainty + no blind retry is the guarantee (RDGO-001 v3.1 §17 last ¶).

### 5.6 Attempt identity / idempotency key

`derive_dispatch_attempt_record_id(invocation_id, attempt_id)` = `"dar-" + sha256_canonical({invocation_id, attempt_id})[:32]` — a deterministic, restart-stable function of exactly the `(invocation_id, attempt_id)` pair that keys the consumed attempt at Gate 9 (RDGO-001 v3.1 §10a; `.1R.16` §25.3). No wall clock, mtime, nonce, PID, or random input enters it (AST-asserted). The `idempotency_key` (RPAC-REQ-065 SHA-256 of canonical versioned request content) is carried on the record binding from the `DispatchEnvelope`; it never by itself authorizes redispatch. Relationship: `invocation_id` (logical), `attempt_id` (one concrete try, `att-<32hex>`), `idempotency_key` (logical content), `proof_id` / `approval_id` (durable-record binding keys), `consumption_record_digest` / `envelope_digest` (the exact consumed authority + minted envelope this attempt describes).

### 5.7 Append-only discipline

Each transition is an immutable, `sha256`-chained observation (`sequence`, `state`, `observed_at`, `prior_digest`, `detail`, `digest`) written through an `O_CREAT | O_EXCL` primitive + `os.link` into an absent final name + `fsync`. `list_transitions()` re-verifies the sequence, the chain digest, and each transition digest on every read, and rejects a truncated / malformed / unknown-state / duplicate-sequence / post-terminal transition. The record header is create-only and integrity-digested. A concurrent race to create a record or start an attempt has exactly one winner; every loser fails closed.

## 6. Crash / restart determination (phase prompt §20–§25 / §45)

`resolve_disposition(record_id)` derives the outcome from **durable state only**:

| Durable latest state | disposition | terminal | automatic_retry_permitted | fresh_human_authority_required | external_effect_possible |
|---|---|---|---|---|---|
| no record | `not_started` | no | no | no | no |
| PREPARED | `DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER` | no | **no** | yes | **no** |
| EFFECT_ATTEMPT_STARTED (unresolved) | `DISPATCH_UNCERTAIN` | no | **no** | yes | **yes** |
| RECEIPT_CAPTURED | `RECEIPT_CAPTURED` | yes | no | yes | yes |
| DISPATCH_UNCERTAIN | `DISPATCH_UNCERTAIN` | yes | no | yes | yes |
| DISPATCH_NOT_STARTED | `DISPATCH_NOT_STARTED` | yes | no | yes | no |

* **Crash before EFFECT_ATTEMPT_STARTED** — no effect can have been attempted by this phase; the effect boundary was never crossed; `external_effect_possible = False`; a fresh `invocation_id` / `attempt_id` / approval / proof is required for any new attempt.
* **Crash after EFFECT_ATTEMPT_STARTED** — the future effect boundary may have been crossed; `DISPATCH_UNCERTAIN`; no blind retry; a human decision is required. A restarted process may not re-start the same attempt.
* **Crash after receipt before the mirror's terminal write** — indistinguishable from crash-during at the mirror; the safe posture is `DISPATCH_UNCERTAIN`. (Modelled; the actual receipt path is Slice C.)
* Restart uses `derive_dispatch_attempt_record_id` (pure function of durable identity) and `list_transitions` (durable file scan) — no registry / object-identity dependency.

## 7. 3S.2.1 MUST-FIX #1 — malformed adapter result (phase prompt §32–§34)

`3S.2.1` §62 item 1: `simulate_invocation` called `store.write_result()` on an unvalidated `adapter.collect()` return; a non-`RuntimeInvocationResult` raised an uncaught `AttributeError` inside `RuntimeInvocationStore.write_result`.

**Repair:** after `result = resolved.adapter.collect(...)` (wrapped in try/except → `FAILURE_MALFORMED_RESULT` on any exception), `malformed_adapter_result_reasons(result, request)` runs a strict, non-raising, fail-closed check **before** any state transition or `store.write_result()`: `isinstance(result, RuntimeInvocationResult)`, exact `invocation_id` / `attempt_id` / `idempotency_key` / `contract_version` / `runtime_target_id` match, `simulation_only is True`, `execution_effect == "none"`, `untrusted is True`, `terminal_outcome in {"success", "failure"}`, non-empty `result_digest` / `payload_digest`, `structured_payload` is a `Mapping`, `changed_files` is a `tuple`. Any failure → `_fail(..., FAILURE_MALFORMED_RESULT, reasons, ...)` — a clean `SimulationOutcome`, no persisted `result.json` / `intake-handoff.json`. The `dispatch()` receipt is likewise guarded (`isinstance(receipt, DispatchReceipt)` + `accepted`). Acceptance was **not** loosened: `simulate_invocation` still contains exactly one `resolved.adapter.dispatch(` call site, still `simulation_only`, no new effect primitive. `test_malformed_adapter_result_never_persists_a_result_document` (3S.2.1 suite) was updated from "asserts an uncaught exception" to "asserts a clean `FAILURE_MALFORMED_RESULT` outcome" — the repaired behaviour.

## 8. 3S.2.1 MUST-FIX #2 — RuntimeInvocationStore path containment (phase prompt §29–§31)

`3S.2.1` §62 item 2: `RuntimeInvocationStore._invocation_dir` / `_write_create_only` joined the raw `invocation_id` onto the store root with no normalization; a crafted `../../..` id resolved outside `.pcae/runtime-invocations/mock-v1/`.

**Repair:** `_invocation_dir` / `_attempt_dir` route `invocation_id` / `attempt_id` through `require_safe_relative_id_component` (the repository's canonical "exactly one safe path component" grammar — rejects `.`, `..`, `/`, `\` **before** the join, since `Path.__truediv__` discards a root prefix on an absolute string). `HPACMalformedError` is re-raised as `InvocationIntegrityError` (fail closed). `_write_create_only` additionally runs `_assert_within_root(path)` — a resolved-path check (`path.resolve().relative_to(root.resolve())`), not a string prefix — so every persisted document lives strictly beneath the store root even against a symlink or a bypassed component check. Production callers always pass `new_invocation_id()` / `new_attempt_id()` values, which satisfy the grammar unchanged; the existing 3S.2.1 `xfail(strict=True)` gap demonstrator (`test_store_invocation_id_lacks_path_confinement_defense_in_depth`) was **promoted** to a real expected-rejection test (`test_store_invocation_id_path_confinement_defense_in_depth`), exactly as its own comment anticipated ("promoted out of xfail"). The dedicated `.1R.19` suite also exercises `../`, absolute, `/`-separator, `\`-separator, `..`, `.`, symlink-escape, and a normal id.

## 9. 3S.2.1 item-9 — runtime-inspect discoverability repair (phase prompt §35–§38)

`3S.2.1` §44/§61 recorded a TRUTHFUL_WITH_LIMITATION discoverability gap: `pcae runtime inspect` reports the long-lived (empty) `RuntimeRegistry` and gives no pointer that a separate, transient, per-call RPAC-001 mock/dry runtime-adapter surface exists (reachable via `pcae session bootstrap --dry-runtime`), so a plain "Plugin count: 0 / Registry status: empty" is easy to over-read as "nothing runtime-adapter-shaped exists".

**Repair:** `runtime_introspection.py` gains an additive, observational `RuntimeAdapterSurfaceInfo` dataclass + a frozen `RUNTIME_ADAPTER_SURFACES` tuple (three entries: the RPAC mock-v1 dry-consumption simulation coordinator; the Gate-10 pre-effect eligibility coordinator; this phase's dispatch-attempt durable lifecycle mirror) + `get_adapter_surfaces()`. Every entry is static data — no registry read, no adapter instantiation, no `simulate_*` call, no mutation — and is explicitly `effecting=False`, `authoritative=False`, `execution_availability="unavailable"`. `runtime_inspect.py` renders a one-line summary in the default view and a detail section in `--verbose`. **The `--json` output is byte-unchanged** (the Phase 112F 9-key JSON contract and `runtime_snapshot.py` are untouched — the repair is deliberately human-output only, so it cannot be over-read as a machine-consumable readiness signal). `pcae runtime inspect` still reports `not_implemented / Observed / observe / unavailable`, `Registry status: empty`, `Plugin count: 0`, `Capability count: 0` — verified byte-identical for the JSON mode at entry and finalization.

### Item-9 disposition (phase prompt §36 / §52)

All three prerequisite repairs are IMPLEMENTED:
1. malformed adapter result fails closed — done (§7);
2. `RuntimeInvocationStore` `invocation_id` / `attempt_id` containment — done (§8);
3. runtime-inspect discoverability — done (§9).

**ITEM 9: IMPLEMENTED — INDEPENDENT VERIFICATION PENDING `.1R.20`.** Not CLOSED before `.1R.20`.

## 10. N-16-2 disposition (phase prompt §53)

`.1R.16` §35 item 12 (N-16-2): "Dispatch-attempt durable lifecycle / mirror `RuntimeInvocationRecord` — the durable place a `DISPATCH_UNCERTAIN` / restart outcome lives." This is now implemented as the non-authoritative append-only `RuntimeInvocationRecord` mirror with the full `PREPARED → EFFECT_ATTEMPT_STARTED → {RECEIPT_CAPTURED | DISPATCH_UNCERTAIN | DISPATCH_NOT_STARTED}` state machine, crash/restart determination, and at-most-once guard.

**N-16-2: IMPLEMENTED — INDEPENDENT VERIFICATION PENDING.** "Wired" here means: the mirror exists, is durable, is restart-readable, is bounded to one `(invocation_id, attempt_id)` identity, and is consumed by nothing that could turn it into effect authority. It does **not** mean effect dispatch — there is no `adapter.dispatch()` call site and no Gate-5→11 caller of this module. The trusted Gate-10 caller that would open a record and write transitions around a future `adapter.dispatch()` is Slice C (no phase ID).

## 11. Verdicts (phase prompt §54)

```
DISPATCH-ATTEMPT DURABLE LIFECYCLE:                        IMPLEMENTED — INDEPENDENT VERIFICATION PENDING (.1R.20)
AT-MOST-ONCE ATTEMPT / FAIL-CLOSED UNCERTAINTY:            IMPLEMENTED — INDEPENDENT VERIFICATION PENDING
3S.2.1 PREREQUISITE REPAIRS (MUST-FIX #1, #2, runtime-inspect):  IMPLEMENTED — INDEPENDENT VERIFICATION PENDING
FIRST EXTERNAL EFFECT:                                    ABSENT
```

Not self-closed. Recommended next: exactly `149O.20L.7O.3W.1R.2B.1R.1.1R.20` — Independent Verification of the Dispatch-Attempt Durable Lifecycle. Not begun. Slice C / D keep no phase ID.

## 12. Slice-C blockers (phase prompt §55)

`N-16-3` (PBRD-001 §12 POL-005 narrow-eligibility rule + IV), `N-16-4` (real positive single-attempt Runtime Enforcement gate), `N-16-5` (real FIDO2 / WebAuthn / CTAP + protected human-approval UI), `N-16-6` (RPAC-REQ-095 generic fixed-argv external-executable adapter + supply-chain admission), `N-16-7` (runtime capability enablement `Observed → Approved/Executable`) — **status unchanged; all remain hard prerequisites for the first external effect.** No direct evidence in this phase affects any of them.

## 13. Consumer inventory (phase prompt §46)

Production consumers of `RuntimeInvocationRecord` / `runtime_dispatch_attempt_lifecycle`: **none** in the Gate-5→11 chain. `grep -rn "runtime_dispatch_attempt_lifecycle\|RuntimeInvocationRecord" src/pcae/` outside the module itself → only `runtime_introspection.RUNTIME_ADAPTER_SURFACES` (a descriptive string, not a call). No new effect-bearing consumer appears. The mirror remains evidence/coordination state only.

## 14. Static / dynamic no-effect proof (phase prompt §47 / §48)

* **Static (AST + code-only token scan)** of `runtime_dispatch_attempt_lifecycle.py`: imports are `json`, `os`, `dataclasses`, `pathlib`, `typing`, `pcae.core.hpac_foundation` only — no `subprocess` / `socket` / `ssl` / `pty` / `ctypes` / provider SDK / HTTP client / credential resolver / FIDO2 / WebAuthn / `multiprocessing` / `asyncio`. No `Call` to `.dispatch` / `.Popen` / `.spawn` / `.system` / `.posix_spawn` / `.check_output`. The string/comment-stripped code contains no `.dispatch(` / `subprocess.` / `socket.socket` / `os.system(`. The `os.*` calls used are `open` (`O_CREAT|O_EXCL`), `write`, `fsync`, `close`, `link`, `unlink`, `urandom`, `getpid` — file persistence only.
* **Dynamic effect trap** (`test_no_dynamic_effect_when_lifecycle_and_repairs_exercised`): `subprocess.Popen`, `subprocess.run`, `os.posix_spawn`, `os.system` monkeypatched to raise; lifecycle transitions + `record_dispatch_uncertain` + `get_adapter_surfaces` exercised → zero effect calls.

## 15. Fixed-SHA A/B (phase prompt §49)

Immutable pre-`.1R.19` baseline: `a2b679fe` (== HEAD at phase entry). Deterministic run (`-p no:randomly`, xdist for speed with `--dist=loadfile`; the attribution nodes below re-confirmed single-process) across the new Slice-B suite, the runtime invocation store / record suites, the simulation suites, the runtime-inspect / introspection / snapshot suites, the Slice-A `.1R.17` / `.1R.18` / `.1R.17R` / `.1R.17R.1` suites, the Gate 5–9 suites, and the relevant RPAC / RDGO contract tests (59 test files).

```
BASELINE (a2b679fe, clean)          : 62 pre-existing failing nodes
AFTER   (a2b679fe + .1R.19 changes) : 64 failing nodes

NEW attributable failing nodes                         : 2
FIXED (previously failing, now pass)                   : 0
UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS        : 0
CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES : 0
```

The 62 baseline failures are pre-existing and unrelated (HATP wave suites, `.3V.1` / `.3V.1R.1` contract-verification cardinality assertions, deploymentbinding contract, class-B ACL, `.1R.18` `[...r111r32]` / `[...1g]` cascade nodes that already fail at clean HEAD, etc.) — reproduced identically with the phase's changes stashed.

The **2 NEW failing nodes are both non-functional working-tree / unpushed-state artifacts** that pass once the phase is committed and pushed:
* `test_gate10_slice_a_scope_fence_reconciliation_3w1r2b1r1_1r17r.py::test_no_working_tree_production_or_contract_diff` — asserts `git diff -- src/pcae` (working tree) is empty; clean after `pcae commit`.
* `test_phase_149o_20l_7d_4_action_6_continuation_baseline_amendment_independent_verification.py::test_no_production_source_modified_this_phase` — asserts `git diff origin/main -- src/pcae/**` is empty; clean after `pcae push` (origin/main advances).

Post-push re-run of both: **PASS** (recorded in §17).

### 15.1 Scope-fence guard reconciliation (phase prompt §21 classification)

The authorized Slice-B production changes trip a set of earlier-phase point-in-time "only files X changed since my fixed baseline" / consumer-inventory / import-allowlist guards. `.1R.16` §36.2 / §38 authorizes exactly this production-file set; the `.1R.13.2` / `.1R.17` / `.1R.17R` precedent is to widen each guard minimally and keep it explicit and finite (no wildcard). Reconciled this phase, each still rejecting any unauthorized importer / production-file expansion:

| Guard | File | Widening |
|---|---|---|
| `test_isolation_only_three_production_files_changed_since_baseline` | `test_b1_b7_n1_n2_..._1r8.py` | `_authorized` += the 4 Slice-B files (exact filenames) |
| `test_production_file_allowlist_matches_frozen_phase_matrix` | `test_runtime_authority_production_repair_3w1r2b1r1117.py` | `_authorized_surface` += the 4 Slice-B files |
| `test_earlier_gates_and_contracts_bytes_unchanged_since_baseline` | `test_gate10_..._1r17.py` | `runtime_adapter.py` / `runtime_introspection.py` removed from the byte-unchanged loop; `runtime_dispatch_gate9.py` **added** (strengthening); Slice-A coordinator byte-unchanged assertion kept |
| `test_production_scope_since_baseline_is_the_single_new_file` | `test_gate10_..._1r17.py` | now a subset check against the exact `_SLICE_B_AUTHORIZED_SINCE_BASELINE` set |
| `test_production_dry_source_is_byte_unchanged_from_verification_baseline` | `test_phase_149o_20l_7o_3v_1_contract_verification.py` | converted to a phase-aware invariant: when the diff is non-empty, it must be the authorized 3S.2.1 MUST-FIX #1 repair only (exactly one `adapter.dispatch(` call site; no effect primitive; `malformed_adapter_result_reasons` / `FAILURE_MALFORMED_RESULT` present; no added line grants authority / enables execution / registers an adapter) |
| `test_module_imports_are_allowlisted` | `test_runtime_inspect_cli.py` | `pcae.core.runtime_introspection` re-added (already transitive via `runtime_snapshot`) |
| `test_module_import_allowlist_unchanged_from_111c` | `test_runtime_inspect_verification.py` | same |
| `test_no_slice_b_lifecycle_artifact_in_the_gate10_module` | `test_gate10_..._1r17r_1.py` | still asserts the Slice-A *coordinator* module carries no Slice-B token (true — Slice B is a separate module); the `doc19 == []` assertion replaced by a Slice-A-coordinator byte-unchanged assertion |
| `test_r18_and_r17_suites_are_byte_unchanged_since_their_own_finalization` | `test_gate10_..._1r17r_1.py` | renamed to `..._are_unchanged_except_slice_b_scope_fence_widening`: allows only Slice-B scope-fence widening in the two suites, no wildcard, and requires a Slice-B filename to appear |

**Test-weakening audit:** 0 tests removed, 0 skipped/`xfail`ed (the one existing `xfail(strict=True)` was *promoted* to a passing assertion), 0 allowlists wildcarded, every widened set keeps explicit finite enumeration.

## 16. No-drift confirmations (phase prompt §38–§41, §56, §57)

* Slice-A coordinator `runtime_dispatch_gate10_eligibility.py` — **byte-unchanged** (`git diff a2b679fe HEAD` empty).
* Gate 5 / 6 / 7 / 8 / 9 + `runtime_invocation_authority_consumption.py` — **byte-unchanged**.
* `docs/contracts/**` + `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` — **byte-unchanged**. No normative contract change; the state machine is fully expressible under current RPAC-001 v1.0 / RDGO-001 v3.1 (no STOP condition triggered — phase prompt §51).
* `runtime_snapshot.py` + the `--json` runtime-inspect contract — **byte-unchanged**.
* `RuntimeRegistry` — empty; no adapter registered / activated / implemented (phase prompt §41).
* No `runtime_dispatch_gate10.py` / effect coordinator / adapter dispatch module / external receipt path created (phase prompt §40).
* Runtime posture: `State: Observed`, `Maximum Capability: observe`, `Execution Availability: unavailable` — unchanged (phase prompt §56). No capability elevation / `Observed → Approved/Executable` transition.
* POL-005 (`ExecutionDisabledRule`) — byte-unchanged; still universal hard DENY for every truthful non-simulation `runtime_dispatch` (re-verified live: `PermissionBroker().evaluate(simulation_only=False)` → `DENY`) (phase prompt §57).
* `.3` governance incident — `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved verbatim (phase prompt §59). No delegated worker committed, finalized, or pushed.

## 17. Governed finalization (phase prompt §61 steps 26–33)

Recorded after the governed `pcae` commit / push / `pcae phase complete`:

* **Commits:** listed in `.pcae/phase-completion-metadata.json` `phase_commits`.
* **Pushed status:** `pushed`; `origin/main..HEAD = 0` confirmed post-push.
* **Post-push re-run** of `test_no_working_tree_production_or_contract_diff` and `test_no_production_source_modified_this_phase`: **PASS** (the 2 A/B artifacts resolved).
* **Final `pcae health` / `check` / `status coherence` / `doctor task-memory` / `push check` / `runtime inspect`:** healthy / passed / coherent / warning-only (pre-existing) / nothing_to_push / `Observed / observe / unavailable` (byte-identical JSON to entry).
* **Telegram notification:** dispatched by `pcae phase complete` (one notification, carrying this report).

## 18. Recommended next phase (phase prompt §58)

`149O.20L.7O.3W.1R.2B.1R.1.1R.20` — Independent Verification of the Dispatch-Attempt Durable Lifecycle. RE-DERIVE the crash/restart/idempotency model against RDGO-001 v3.1 §17/§18 and RPAC-REQ-064–072; independently confirm the two 3S.2.1 repairs and the runtime-inspect repair; re-run the fixed-SHA A/B; re-derive the scope-fence guard widenings. **Not begun.** Do not implement the Gate-10 effect. Do not enable execution. Slice C / D keep no phase ID.

---

## No-Go Confirmations

- No first external effect: no `adapter.dispatch()` call site anywhere in this phase's code; no `runtime_dispatch_gate10.py`; no real (non-mock) `RuntimeAdapter`; `runtime_dispatch_attempt_lifecycle.py` imports and calls no `subprocess` / process spawn / `os.system` / `os.popen` / `exec*` / `spawn*` / `posix_spawn` / `socket` / `ssl` / provider SDK / HTTP client / credential resolver / FIDO2 / WebAuthn / CTAP / smartcard / USB path.
- No adapter (mock or real) was registered, activated, implemented, or called; `RuntimeRegistry` remains empty; `RuntimeAdapterResolver` has no callable instance for a real target.
- No execution was enabled; runtime remains `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; POL-005 unchanged and still hard DENY.
- No runtime capability was elevated or promoted; no `Observed → Approved/Executable` transition was performed or planned to occur automatically.
- No normative contract file was edited (RDGO / PBRD / HPAC / RIHAC / RIASC / RPAC / PBPA / POL-005 / RE registry all byte-unchanged); no MAJOR or MINOR contract version bumped, forced, or overridden.
- No Slice-A semantic change: `runtime_dispatch_gate10_eligibility.py` is byte-unchanged since `a2b679fe`.
- No closed gate boundary (Gate 5 / 6 / 7 / 8 / 9) was reopened; their production modules and `runtime_invocation_authority_consumption.py` remain byte-unchanged since `a2b679fe`.
- No credential was accessed, resolved, embedded, or referenced; no secret resolver was created.
- No `consumption.json` was written anywhere by this phase; the mirror `RuntimeInvocationRecord` is a distinct, non-authoritative, repository-side store under `.pcae/runtime-dispatch-attempts/` and authorizes no effect.
- No approval / proof / presentation / challenge / nonce was consumed on any path.
- The dispatch-attempt mirror record never authorizes an effect: no `approve` / `authorize` / `permit` / `grant` / `consume` method, no `execution_allowed` / `permission` / `authorized` field, `GRANTS_NO_EFFECT_AUTHORITY` permanent, `record_grants_no_effect_authority()` always `True`; a copied / reconstructed record grants nothing.
- No third-party system, unrelated account, external credential, provider API, external network, or deployment target was accessed or mutated; no other machine was contacted.
- No test was removed, weakened, skipped, or `xfail`ed; the one pre-existing `xfail(strict=True)` gap demonstrator was promoted to a passing expected-rejection test; every widened scope-fence guard keeps explicit finite enumeration and still rejects an unauthorized importer / production-file expansion.
- The `--json` `pcae runtime inspect` contract (Phase 112F, 9 top-level keys) and `runtime_snapshot.py` are byte-unchanged; the item-9 repair is human-output only.
- No raw `git commit` / `git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass — governed `pcae` lifecycle only.
- No delegated worker committed, finalized, or pushed; only the primary human-authorized operator holds `.1R.19` lifecycle authority; the historical delegated `.3` finalization / commit / push remains UNAUTHORIZED.
- No `.1R.20` (Slice B IV) work was begun; no Slice C / D artifact or phase ID was created; the first external effect keeps no phase ID.
- No STOP / BLOCKED condition was reached — RPAC-001 v1.0 / RDGO-001 v3.1 support the append-only dispatch-attempt lifecycle with no normative contract change; the write-before-effect model is expressed without an effect call site; crash/restart is represented with append-only immutable state; each 3S.2.1 repair is within Slice-B scope; the runtime-inspect repair is observational only and needs no capability enablement; the repository is coherent.

---
*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19.*

---

## ERRATUM — issued by Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19R (Slice-B Scope-Fence and Verification-Evidence Reconciliation)

**Append-only. Every section above this line, including §15 (Fixed-SHA A/B) and
the No-Go Confirmations, is preserved verbatim as the original historical
record. This erratum corrects the verification-evidence claim; it does not
rewrite it.** The original immutable `.1R.19` phase-report / completion-metadata
artifacts (commits `88e716b1` / `738e8209`) are preserved unchanged.

### What was wrong

* **§15 (Fixed-SHA A/B)** recorded *"NEW attributable failing nodes : 2"* and
  *"UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS : 0"*, and **§15.1** stated
  *"every widened scope-fence guard keeps explicit finite enumeration and still
  rejects an unauthorized importer."* The **No-Go Confirmations** repeated
  *"every widened scope-fence guard … still rejects an unauthorized importer."*
* `.1R.19` added `from pcae.core.hpac_foundation import (…)` to **two** production
  modules — `src/pcae/core/runtime_dispatch_attempt_lifecycle.py` (new) and
  `src/pcae/core/runtime_invocation.py` (3S.2.1 MUST-FIX #2) — a legitimate
  reuse of the canonical Layer-1 path-safety / digest **utilities**
  (`require_safe_relative_id_component`, `canonical_digest`, `reject_symlink`,
  `read_canonical_json_document`, `HPACMalformedError`). Neither module writes
  an HPAC principal, presentation, proof, lifecycle event, or consumption
  record; the non-authoritative `RuntimeInvocationRecord` grants no effect
  authority.
* **But `.1R.19` never widened and never disclosed** the HPAC Layer-1/2
  consumer-inventory guard family. `.1R.20` (Independent Verification, BLOCKED
  result) found it.

### Correct historical result

Independently re-executed by `.1R.19R` in dedicated detached worktrees
(`a2b679fe` → `738e8209`), `-p no:randomly`, no xdist, the effective `.1R.20`
selection:

```
pre-.1R.19 baseline a2b679fe   : 30 failing nodes
original .1R.19 head 738e8209  : 35 failing nodes

ADDED, attributable to and explained by .1R.19 (root cause N-20-1) : 5
REMOVED                                                            : 0
```

The 5 added nodes:

| # | Node | Class |
|---|---|---|
| 1 | `test_hpac_foundation_independent_verification_3w1r2b1r111r31.py::test_new_hpac_modules_have_zero_preexisting_production_consumers` | direct HPAC consumer-inventory guard |
| 2 | `test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py::test_hpac_repair_has_zero_preexisting_production_consumers` | direct HPAC consumer-inventory guard |
| 3 | `test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py::test_foundation_has_no_production_consumers_or_gate_wiring` | direct HPAC consumer-inventory guard |
| 4 | `test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py::test_widened_guard_module_passes_at_head[test_hpac_foundation_trust_root_repair_3w1r2b1r111r32]` | consequential meta-guard (runs #2) |
| 5 | `test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py::test_v15_2_guards_pass_at_head` | consequential meta-guard (runs #1–#3) |

**Additional disclosed noise (not a regression):** `.1R.20` §2 disclosed one
non-deterministic pre-existing flake,
`test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py::test_concurrent_conflicting_successors_have_one_canonical_winner`
(observed pass/fail/fail on consecutive HEAD runs; also fails intermittently at
the baseline). It did not surface in the `.1R.19R` deterministic single-process
re-run. Disclosed, not attributable, not counted.

The **original §15 count of "2"** referred only to the two working-tree /
unpushed-state artifact nodes that `.1R.19` did resolve post-push; it did not
capture the five undisclosed guard/meta-guard nodes above.

### Production impact

**None.** `.1R.20` independently RE-DERIVED the dispatch-attempt durable
lifecycle, at-most-once semantics, crash/restart determination, idempotency
identity, `RuntimeInvocationRecord` non-authority, both 3S.2.1 repairs, item-9,
and N-16-2 (Slice-B scope, interpretation A) as **substantively verified /
closed-worthy**, and confirmed the first external effect is **absent**. No
substantive Slice-B lifecycle defect was identified.

### Governance / evidence impact

A **material completeness defect** in the `.1R.19` fixed-SHA A/B evidence — the
same defect class that BLOCKED `.1R.18`.

### Repair

**`.1R.19R`** widened the three `AUTHORIZED_CONSUMERS` sets by **exactly** the
two authorized Slice-B importer tuples
`("runtime_dispatch_attempt_lifecycle.py", "pcae.core.hpac_foundation")` and
`("runtime_invocation.py", "pcae.core.hpac_foundation")` — no wildcard; each
guard still rejects any other importer. The two consequential meta-guards
recover transitively (no meta-guard weakened). After the widening the repaired
tree records **0 attributable added / 0 attributable removed** vs `a2b679fe`.
See `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_19R_SLICE_B_SCOPE_FENCE_AND_VERIFICATION_EVIDENCE_RECONCILIATION.md`.

### N-20-4 (separate, non-blocking production-quality repair)

`.1R.20` §9 also recorded a non-blocking finding: concurrent losing contenders
of `begin_effect_attempt` did not all map to the same error type (a fraction
leaked `DispatchAttemptTransitionError`). `.1R.19R` normalised this — the
`EFFECT_ATTEMPT_STARTED → EFFECT_ATTEMPT_STARTED` edge (only that edge) is
remapped to `DispatchAttemptAlreadyStartedError`; the winner-selection
primitive, the state machine, and every other fail-closed error path are
unchanged. This is a production-quality repair, not a lifecycle or normative
contract change.

*Erratum — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19R.*
