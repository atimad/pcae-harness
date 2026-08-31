# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.20 — Independent Verification of the Dispatch-Attempt Durable Lifecycle

**Type:** independent verification of `.1R.19` (Slice B of the `.1R.16` Gate-10 plan).
**Status:** **BLOCKED INDEPENDENT-VERIFICATION RESULT — finalized (Option B).**
The substantive dispatch-attempt durable lifecycle is independently verified /
closed-worthy; **regression / verification-evidence acceptance is BLOCKED** and
referred to a dedicated repair phase (`149O.20L.7O.3W.1R.2B.1R.1.1R.19R`). See §2 and §12.
**Verification-entry SHA:** `738e8209` (`.1R.19` finalize head; `origin/main..HEAD = 0` at entry).
**Immutable pre-`.1R.19` baseline:** `a2b679fe` (independently verified:
`git rev-parse bb646972^` — parent of the `.1R.19` production implementation
commit `bb646972`; also the `.1R.17R.1` finalize head).
**Production source modified by this phase:** none.
**Normative contracts modified by this phase:** none.
**Scope-fence / guard files modified by this phase:** none — the 3 discovered
undisclosed `.1R.19`-attributable guard failures (+ 2 consequential meta-guard
failures) are **NOT repaired inside `.1R.20`**; they are referred to `.1R.19R`.
**Execution:** not enabled. Runtime `not_implemented / Observed / observe / unavailable`;
POL-005 hard DENY unchanged; 0 plugins / 0 capabilities; `pcae runtime inspect`
posture byte-identical.
**Governance:** governed `pcae` lifecycle only. The delegated `.3` finalization /
commit / push incident remains **UNAUTHORIZED**. Only the primary
human-authorized operator holds `.1R.20` lifecycle authority. This phase is
**not self-closed** — the substantive verdicts below are offered as evidence; the
blocker is referred out, not adjudicated away.

## Exact `.1R.19` commit range (independently reconstructed)

| # | SHA | Role |
|---|---|---|
| baseline | `a2b679fe` | immutable pre-`.1R.19` baseline (parent of `bb646972`) |
| 1 | `bb646972` | **production implementation** — new `runtime_dispatch_attempt_lifecycle.py`; 3S.2.1 MUST-FIX #1 (`runtime_adapter.py`); MUST-FIX #2 (`runtime_invocation.py`); item-9 (`runtime_introspection.py` + `commands/runtime_inspect.py`) |
| 2 | `bd6a6982` | test suite (55) + xfail→pass promotion + 9 scope-fence guard widenings |
| 3 | `3375b616` | canonical doc + status + changelog |
| 4 | `44a5c0b4` | 5 further scope-fence / byte-freeze guard widenings |
| 5 | `e58aacf5` | task close → idle |
| 6 | `88e716b1` | staged completion metadata / report |
| 7 | `738e8209` | governed push-state reconciliation (verification-entry head) |

Production scope since baseline — independently confirmed via
`git diff --name-only a2b679fe HEAD -- src/` — is **exactly** the five files
`.1R.16` §36.2 / §38 authorises for Slice B:
`runtime_dispatch_attempt_lifecycle.py` (new), `runtime_adapter.py`,
`runtime_introspection.py`, `runtime_invocation.py`, `commands/runtime_inspect.py`.
No normative contract changed (`git diff --stat a2b679fe HEAD -- docs/contracts/` empty).

---

## Verdict summary

| Component | Verdict |
|---|---|
| Dispatch-attempt durable lifecycle (state machine, transitions, terminals, append-only) | **substantively verified / closed-worthy** |
| Write-before-effect + at-most-once dispatch-attempt guard | **substantively verified / closed-worthy** (see N-20-4) |
| Crash / restart determination (`resolve_disposition`) | **substantively verified / closed-worthy** |
| Deterministic idempotency identity (`derive_dispatch_attempt_record_id`) | **substantively verified / closed-worthy** |
| `RuntimeInvocationRecord` non-authority (semantic wall) | **substantively verified / closed-worthy** |
| 3S.2.1 MUST-FIX #1 — malformed adapter-result fail-closed | **substantively verified / closed-worthy** |
| 3S.2.1 MUST-FIX #2 — `RuntimeInvocationStore` path containment | **substantively verified / closed-worthy** |
| item-9 — runtime-inspect discoverability (human-output only; `--json` byte-unchanged) | **substantively verified / closed-worthy** |
| N-16-2 — dispatch-attempt durable mirror infrastructure | **substantively verified / closed-worthy (Slice-B scope; interpretation A)** — production Gate-10-caller wiring is Slice C |
| First external effect | **ABSENT** (verified — no `adapter.dispatch()` call site; no effect primitive; zero production consumers) |
| **Regression / verification-evidence acceptance** | **BLOCKED** — 3 undisclosed `.1R.19`-attributable HPAC Layer-1/2 consumer-inventory guard regressions + 2 consequential meta-guard failures + an inaccurate `.1R.19` finalized fixed-SHA A/B record. Same defect class that BLOCKED `.1R.18`. Referred to `.1R.19R`. |

---

## 1. Verification principle

**RE-DERIVE. DO NOT TRUST.** Every claim below was derived independently from:

* **RDGO-001 v3.1** §11 (Gate 10 forward read-back prerequisite), §16 (cross-contract
  identifiers), **§17 (crash and recovery states)**, **§18 (retry contract)**, §19
  (security invariants) — `docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md`;
* **RPAC-REQ-064 … RPAC-REQ-072** — `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md` §13;
* the **`.1R.16` planning document** (§22.3 state model, §25.1 at-most-once, §31 crash
  determination, §36.1 slice decomposition, §35 prerequisite table item 12 = N-16-2);
* current production source read line by line.

Not accepted from the `.1R.19` report, state names, helper names, test names,
comments, or `pcae runtime inspect` output.

Fresh independent suite:
`tests/test_dispatch_attempt_durable_lifecycle_iv_3w1r2b1r1_1r20.py` — **67 passed, 0 failed**
(deterministic, `-p no:randomly`, no xdist). It also encodes the blocker as
executable regression evidence (`finding_n20_*` tests).

---

## 2. The blocker (recorded exactly)

### N-20-1 — three undisclosed `.1R.19`-attributable consumer-inventory guard regressions (BLOCKING)

`.1R.19` added `from pcae.core.hpac_foundation import (...)` to **two** production
modules:

* `src/pcae/core/runtime_dispatch_attempt_lifecycle.py` (new) — imports
  `HPACMalformedError`, `canonical_digest`, `read_canonical_json_document`,
  `reject_symlink`, `require_safe_relative_id_component`;
* `src/pcae/core/runtime_invocation.py` (3S.2.1 MUST-FIX #2) — imports
  `HPACMalformedError`, `require_safe_relative_id_component`.

This is a **legitimate reuse** of the repository's canonical path-safety /
digest helpers — the same helpers the canonical HPAC consumption store uses.
**But** the HPAC Layer-1/2 consumer-inventory guard family freezes the exact set
of production modules permitted to import that foundation, and `.1R.19` **never
widened it and never disclosed the change**. Three guards pass at `a2b679fe` and
fail at HEAD:

| Guard node | Baseline `a2b679fe` | HEAD `738e8209` |
|---|:--:|:--:|
| `test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py::test_hpac_repair_has_zero_preexisting_production_consumers` | **pass** | **FAIL** |
| `test_hpac_foundation_independent_verification_3w1r2b1r111r31.py::test_new_hpac_modules_have_zero_preexisting_production_consumers` | **pass** | **FAIL** |
| `test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py::test_foundation_has_no_production_consumers_or_gate_wiring` | **pass** | **FAIL** |

Each failure message is identical in substance:
`unauthorized production consumer(s) of the HPAC Layer-1/2 foundation:
[('runtime_dispatch_attempt_lifecycle.py', 'pcae.core.hpac_foundation'),
('runtime_invocation.py', 'pcae.core.hpac_foundation')]`.

**Classification:** these are legitimate stale consumer-inventory / allowlist
guards — each still rejects *any other* importer; no trust boundary is
weakened; Slice B is an authorized reuser of shared path-safety primitives. The
correct repair is to widen each `AUTHORIZED_CONSUMERS` set by exactly the two
Slice-B entries (no wildcard), keeping the guard tight. This is a **guard-
maintenance and verification-evidence defect, not a production Slice-B
implementation defect.**

### N-20-2 — `.1R.19` finalized fixed-SHA A/B record is inaccurate (BLOCKING)

The `.1R.19` completion metadata / report / changelog assert
**“0 unexplained attributable regressions”** and that *“every widened
scope-fence guard keeps explicit finite enumeration and still rejects an
unauthorized importer.”* Three guards were **never widened at all** and now
fail. The finalized A/B record is materially inaccurate — exactly as `.1R.17`’s
was when it BLOCKED `.1R.18`. A provenance-preserving erratum (original text
preserved verbatim; A/B figure corrected) is required and is deferred to
`.1R.19R`.

### N-20-3 — `.1R.19` shipped a self-contradicting meta-guard (BLOCKING, consequential)

`.1R.19` added
`tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py::test_widened_guard_module_passes_at_head[test_hpac_foundation_trust_root_repair_3w1r2b1r111r32]`
— a meta-guard that runs the `r111r32` guard as a subprocess and asserts it
passes at HEAD. It does not. `.1R.19` committed a test that contradicts its own
disclosed guard set.

Additionally, the pre-existing `.1R.15.3` meta-guard
`tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py::test_v15_2_guards_pass_at_head`
(which runs the same three HPAC consumer-inventory guards and asserts “3 passed”)
also fails at HEAD — the same single root cause (N-20-1).

### Fixed-SHA A/B attribution (independently re-executed)

Deterministic, dedicated git worktree at `a2b679fe`, `-p no:randomly`, **no
xdist**, selection
`-k "gate5 or gate7 or gate8 or gate9 or gate10 or introspection or runtime_dispatch or authority_consumption or hpac or runtime_authority or serialization or runtime_invocation or runtime_adapter or runtime_inspect or dispatch_attempt or 3s2_1"`:

* **A** (baseline `a2b679fe`) = **38** failing nodes.
* **B / C** (HEAD `738e8209`; `origin/main == HEAD`) = **43** failing nodes.
* **ADDED in B = 6; REMOVED = 1.**
* **ADDED, attributable to and explained by `.1R.19` (root cause N-20-1) = 5:**
  the 3 guard nodes above + the 2 consequential meta-guards (N-20-3).
* **ADDED, NOT attributable (pre-existing flake) = 1:**
  `test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py::test_concurrent_conflicting_successors_have_one_canonical_winner`
  — non-deterministic (observed pass/fail/fail on three consecutive HEAD runs;
  also fails intermittently at the baseline). Disclosed, not a regression.
* **REMOVED = 1:**
  `test_gate10_slice_a_scope_fence_reconciliation_3w1r2b1r1_1r17r.py::test_original_r17_immutable_phase_report_artifacts_untouched`
  — environmental (detached worktree vs. the main working copy); not a real fix.
* **`.1R.20`-attributable functional regressions = 0** — this phase changes no
  production source; its new suite is independent and 67/67 green.
* The 38 baseline failures are pre-existing on `main` and unrelated (HATP /
  HPAC contract-freeze text asserts, `.1R.15` contract-verification text
  asserts, HATP proof-model serialization scope), reproduced identically in A
  and B.

**Required for closure (phase prompt §48): UNEXPLAINED ATTRIBUTABLE FUNCTIONAL
REGRESSIONS = 0 — met (0). But: undisclosed attributable guard regressions ≠ 0
and the predecessor A/B record is inaccurate → BLOCKED (§45–§48; `.1R.18`
precedent).**

---

## 3. Substantive verification — RDGO §17 / §18 + RPAC-REQ-064..072 (clean)

### Exact production transition matrix (`DISPATCH_ATTEMPT_TRANSITIONS`, re-derived)

```
None                     -> {PREPARED}
PREPARED                 -> {EFFECT_ATTEMPT_STARTED, DISPATCH_NOT_STARTED}
EFFECT_ATTEMPT_STARTED   -> {RECEIPT_CAPTURED, DISPATCH_UNCERTAIN}
RECEIPT_CAPTURED         -> {}          (terminal)
DISPATCH_UNCERTAIN       -> {}          (terminal)
DISPATCH_NOT_STARTED     -> {}          (terminal)
```

Independently derived from RDGO §17’s minimum conceptual states
(`DISPATCH_ATTEMPTED` → `{DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER |
DISPATCH_UNCERTAIN | RESULT_CAPTURED_UNTRUSTED}`) and confirmed byte-for-byte
against the production map. **No backwards transition** (`EFFECT_ATTEMPT_STARTED
→ PREPARED` rejected), **no terminal mutation**, **no duplicate terminal**, **no
state skip** — each exercised in the fresh suite.

### RDGO §17 crash-state ↔ `DispatchAttemptDisposition` mapping (verified)

| RDGO §17 state | Production disposition | `external_effect_possible` | `automatic_retry_permitted` |
|---|---|:--:|:--:|
| (no record / no transition) | `not_started` | `False` | `False` |
| `DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER` (latest `PREPARED`) | same | `False` | `False` |
| `DISPATCH_UNCERTAIN` (unresolved `EFFECT_ATTEMPT_STARTED`) | `DISPATCH_UNCERTAIN` | `True` | `False` |
| `RESULT_CAPTURED_UNTRUSTED` (`RECEIPT_CAPTURED`) | `RECEIPT_CAPTURED` | `True` | `False` |
| terminal `DISPATCH_NOT_STARTED` / `DISPATCH_UNCERTAIN` | as recorded | derived | `False` |

* **RDGO §18 “There is no automatic retry.”** — `automatic_retry_permitted` is
  hard-`False` for **every** state once a record exists. Verified.
* **RPAC-REQ-068** — “Restart before dispatch SHALL resume validation without
  dispatch. Restart after a dispatch-intent/receipt boundary with unknown
  outcome SHALL record `ambiguous_outcome` and SHALL NOT automatically
  redispatch.” — `resolve_disposition` derives from **durable state only** (a
  fresh `RuntimeInvocationRecordStore` with no shared memory reconstructs the
  identical disposition and transition log). Verified: crash-before-`PREPARED`
  → `not_started`; crash-after-`PREPARED` → not-started-after-marker,
  `external_effect_possible=False`; crash-after-`EFFECT_ATTEMPT_STARTED` →
  `DISPATCH_UNCERTAIN`, `external_effect_possible=True`, no auto-retry path.
* **§21 (ambiguous state never becomes `NOT_STARTED`)** — `record_dispatch_not_started`
  is only reachable from `PREPARED` (`next_dispatch_attempt_transition` rejects
  `EFFECT_ATTEMPT_STARTED → DISPATCH_NOT_STARTED`); an unresolved started
  attempt always resolves to `DISPATCH_UNCERTAIN`. Verified.
* **PREPARED semantics (§7 / §9)** — durable attempt identity exists; no
  effect-start marker; no authority. Verified.
* **EFFECT_ATTEMPT_STARTED semantics (§8 / §10)** — the durable no-auto-retry
  boundary; it does **not** mean an effect occurred, an adapter accepted, or a
  receipt exists. Module docstring, implementation, and the `.1R.19` suite all
  preserve this. Verified.
* **Write-before-effect (§11)** — structurally: the lifecycle module contains
  **no** `.dispatch(` / `subprocess` / `socket` / process-spawn call (AST scan);
  no caller immediately dispatches (zero production consumers, §11 below); the
  durable start marker is architecturally positioned before the future (Slice C)
  effect boundary. Verified.
* **RECEIPT_CAPTURED = evidence ≠ authority (§22)** — terminal; no successor;
  `fresh_human_authority_required=True`; no receipt authorizes a new attempt.
  Verified.

### At-most-once + concurrency (§12 / §14 / §61)

* Second `begin_effect_attempt` on the same attempt → `DispatchAttemptAlreadyStartedError`
  (fail closed). Restart-then-start-again → same. Verified.
* **Concurrent start, 4 / 8 / 16 / 32 contenders, repeated:** exactly **one**
  durable `EFFECT_ATTEMPT_STARTED` transition, exactly **one** winner, every
  loser fails closed. The atomic primitive is `O_CREAT | O_EXCL` on a temp
  sibling + `os.link` into the absent final name (one winner by construction);
  losers hit `FileExistsError` → remapped, or the durability pre-check. Verified.
* **No exactly-once overclaim (§13)** — the module docstring and the `.1R.19`
  report both state the target as *at-most-once dispatch attempt + durable
  uncertainty + no blind retry*, never generic exactly-once external effect.
  Verified.

### Idempotency identity (§15 / §16 / §17)

`derive_dispatch_attempt_record_id(invocation_id, attempt_id) = "dar-" +
sha256_canonical({invocation_id, attempt_id})[:32]`. AST scan of the function
body (docstring stripped) confirms **no** `time` / `now` / `urandom` / `getpid`
/ `uuid` / `monotonic` / `getmtime` / `random` reference — restart derives the
identical id from durable inputs only. `invocation_id` / `attempt_id` /
`idempotency_key` / `record_id` / consumption-record digest / envelope digest
are distinct binding fields with no semantic collision (RDGO §16 /§10a).
Cross-attempt isolation (different `attempt_id` under one `invocation_id`) and
cross-invocation isolation verified. Same `record_id` + identical bound content
→ idempotent resume (RPAC-REQ-066); + different content → hard collision
(`DispatchAttemptIntegrityError`). Verified.

### Corruption battery + append-only (§23 / §24 / §25)

`list_transitions` re-validates on every read and fails closed on: unknown
state, sequence gap, transition digest mismatch, chain (prior) digest mismatch,
transition-after-terminal, unreadable / non-dict document, `record_id`
mismatch, unknown schema version, record integrity-digest mismatch. `record_id`
path traversal (`../x`, `..`, `a/b`, `/abs`, `.`) → `DispatchAttemptIntegrityError`.
Every transition file is create-only (`O_EXCL` + `os.link`); an idempotent
replay writes nothing; no whole-file rewrite path exists. `not_a_tuple`
membership-check formatting at `list_transitions` is a frozenset test (correct,
not a silently-disabled check — exercised by the unknown-state case). Verified.

---

## 4. 3S.2.1 MUST-FIX #1 — malformed adapter-result fail-closed (clean)

**Original defect (re-derived from 3S.2.1 §… / RDGO §12):** a non-conforming
`adapter.collect()` return (a plain `dict`, wrong ids, an exception) reached
`store.write_result()` and raised an uncaught `AttributeError` *inside* the
store, or persisted a `result.json` / `intake-handoff.json` for a malformed
result. RDGO §12: *“Malformed output fails closed and must never be persisted as
a successful result.”*

**Repair (verified):** `simulate_invocation` now wraps `adapter.dispatch()` and
`adapter.collect()` in `try/except Exception` → `FAILURE_MALFORMED_RESULT`
(`dispatch_raised:` / `collect_raised:`), and calls the new strict
`malformed_adapter_result_reasons(result, request)` — which returns a non-empty
tuple (never raises) for a non-`RuntimeInvocationResult`, id/version mismatch,
`simulation_only is not True`, `execution_effect != "none"`, `untrusted is not
True`, unknown terminal outcome, missing digests, non-`Mapping`
`structured_payload`, or non-`tuple` `changed_files` — **before** any state
transition or `store.write_result()`. Source-order check confirms the
`malformed_reasons` gate precedes every `write_result` in the function body.
Acceptance is **not** loosened to preserve an old test — the pre-existing
malformed-result test was adapted to the repaired fail-closed behaviour. The
simulation path remains non-effecting: exactly **one** `adapter.dispatch(` call
site (the pre-existing resolved *simulation* adapter), no new effect primitive.

---

## 5. 3S.2.1 MUST-FIX #2 — `RuntimeInvocationStore` path containment (clean)

**Original defect (re-derived):** `_invocation_dir` / `_attempt_dir` joined a
caller-relayed `invocation_id` / `attempt_id` straight onto the store root with
no grammar check — a crafted `../../../../tmp/x` could select a location outside
`.pcae/runtime-invocations/mock-v1/`.

**Repair (verified):** both directory helpers now pass the component through
`require_safe_relative_id_component` (the canonical HPAC grammar — rejects `.`,
`..`, and any path separator *before* the join) via `_require_safe_store_component`
→ `InvocationIntegrityError`, and `_write_create_only` additionally runs
`_assert_within_root` — a **resolved-path** containment check
(`path.resolve().relative_to(root)`), not a string-prefix comparison. ID grammar
battery (`../../../../tmp/x`, `..`, `.`, `a/b`, `/etc/passwd`, `a\b`) all fail
closed on both helpers. Canonical generated IDs (`att-<32hex>`, `inv-<32hex>`)
still pass unchanged — no compatibility regression. The old
`xfail(strict=True)` traversal demonstrator was **promoted** to a passing
expected-rejection test (not weakened — a real defect closure).

**Symlink escape (§34):** the mirror store’s `_write_create_only` rejects a
symlink at the final name (`reject_symlink`) but deliberately does **not**
reject a symlink in an *ancestor* component (macOS `/var` temp roots are
symlinks) — documented verbatim in the module, consistent with the carried-over
F7 threat model (data-forgery resistance, not arbitrary same-process code, not
ancestor-symlink hardening). Not reachable as a new threat in the current
storage model; not a blocker.

---

## 6. item-9 — runtime-inspect discoverability repair (clean)

**Original requirement (re-derived from 3S.2.1 §44 / §61):** a
`TRUTHFUL_WITH_LIMITATION` discoverability gap — `pcae runtime inspect` reports
the empty long-lived `RuntimeRegistry`, but separate runtime-adapter-shaped
surfaces (the RPAC-001 mock/dry simulation coordinator; the Gate-10 eligibility
coordinator; now the Slice-B mirror) coexist, and “Plugin count: 0 / Registry
status: empty” is easy to over-read as “nothing runtime-adapter-shaped exists.”

**Repair (verified):** additive, observational `RuntimeAdapterSurfaceInfo` +
frozen `RUNTIME_ADAPTER_SURFACES` tuple (3 entries) + `get_adapter_surfaces()`
in `runtime_introspection.py` — **static data, the tuple is the whole
implementation**; the accessor reads no registry (`"RuntimeRegistry" not in`
the function body), instantiates nothing, invokes nothing, mutates nothing.
Every surface is `effecting=False`, `authoritative=False`,
`execution_availability="unavailable"`. `commands/runtime_inspect.py` renders a
one-line human summary + a `--verbose` detail block — added **only** inside
`_format_human` (the diff touches no `_format_json` path).

**JSON contract identity (§38):** `src/pcae/core/runtime_snapshot.py` is
byte-unchanged since `a2b679fe`; the `commands/runtime_inspect.py` diff adds no
line to `_format_json`. The Phase 112F 9-key `--json` contract is untouched —
the repair is human-output only.

**Introspection authority wall (§39):** `RuntimeAdapterSurfaceInfo` is a frozen
inert dataclass — not adapter registration, not capability registration, not
runtime authority, not execution readiness; each entry’s `reachable_via`
truthfully states there is no positive production path. **Non-mutating (§40):**
`pcae runtime inspect` reports `not_implemented / Observed / observe /
unavailable`, empty registry, 0 plugins / 0 capabilities at entry and
finalization — unchanged.

---

## 7. `RuntimeInvocationRecord` non-authority (clean)

`RuntimeInvocationRecord` has **no** `approve` / `authorize` / `permit` /
`grant` / `consume` method and **no** `execution_allowed` / `permission` /
`authorized` field. `GRANTS_NO_EFFECT_AUTHORITY` is a permanent
`init=False` field defaulting `True`; `record_grants_no_effect_authority(...)`
is unconditional — its AST body is a single `return True`, so a genuine,
copied, `deepcopy`-d, dict-round-tripped, or entirely foreign object all “grant
nothing.” **Structurally, nothing in the module consults a durable record for
effect authority** — a reconstructed record planted at a foreign root
authorizes nothing because there is no code path that reads a record and
returns an authorization. The authoritative at-most-once truth stays the
create-only `consumption.json` (`HPAC-AUTHORITY-CONSUMPTION/2.1`), which every
consumer re-reads (RDGO §11). Verified.

---

## 8. N-16-2 — original meaning, consumer inventory, adjudication (§42–§44 / §68)

### Original wording (`.1R.16` §35, prerequisite table item 12)

> *“Dispatch-attempt durable lifecycle / mirror `RuntimeInvocationRecord`
> (RPAC-REQ-067/068/069/070) — the durable place a `DISPATCH_UNCERTAIN` /
> restart outcome lives.”* Evidence column: *“§22.3 — `RuntimeInvocationStore`
> exists for the dry path only; **no Gate 5–11-wired mirror**.”* Blocks Slice
> A/B: *“YES (Slice B scope).”*

### Adjudication: interpretation A

`.1R.16` §36.1 charters **Slice B** as *“Dispatch-attempt durable lifecycle:
mirror `RuntimeInvocationRecord` (RPAC-REQ-067), state machine + crash/restart
determination + `DISPATCH_UNCERTAIN`, idempotency, `EFFECT_ATTEMPT_STARTED`
write-before-effect guard”* — the module itself. It charters **Slice C** as
*“the single `adapter.dispatch()` call site added to the coordinator.”* The
“no Gate 5–11-wired mirror” phrasing describes the **pre-Slice-B deficiency
state**; there is no external effect to mirror until Slice C, so full
Gate-chain wiring necessarily arrives **with** Slice C. **“Wired” meant
interpretation A: build the durable mirror infrastructure, ready for the future
Gate-10/11 lifecycle, with no effect-bearing consumer yet.**

### Production-consumer inventory (§43, independently run)

`git grep -l 'runtime_dispatch_attempt_lifecycle' -- src/` returns exactly:

* `src/pcae/core/runtime_dispatch_attempt_lifecycle.py` (the module itself);
* `src/pcae/core/runtime_introspection.py` — **one descriptive string literal**
  in the surface list. **Not an import. Not a call.**

**Zero** production importers. Nothing creates `PREPARED`. Nothing calls
`begin_effect_attempt`. There is no production dispatch-chain caller. Slice A
(`runtime_dispatch_gate10_eligibility.py`) does not call it. No Gate 5–9 code
calls it. It is **library infrastructure + tests only** — by design.

### N-16-2 — CLOSED (Slice-B scope)

The mirror infrastructure is complete and independently verified correct.
Production Gate-10-caller wiring is **Slice C scope** and remains gated behind
N-16-3 … N-16-7 (no positive production path exists — real Gate 7 DENY, POL-005
hard DENY, execution unavailable). N-16-2 **does not block Slice-B lifecycle
acceptance** (`.1R.16` §35 “Blocks Slice A/B — fold into Slice B”; phase prompt
§44 “need not block … if infrastructure itself is correct”). It is **not** a
Slice-C blocker in its own right beyond what N-16-3..7 already impose.

---

## 9. N-20-4 — concurrent-loser error type is not deterministic (NON-BLOCKING)

`begin_effect_attempt` guarantees the **safety** property (exactly one durable
`EFFECT_ATTEMPT_STARTED`; every losing contender fails closed with a
`DispatchAttemptLifecycleError` subclass) but **not** the deterministic *error
type* its own docstring promises (*“every loser gets the same error”*) and
phase-prompt §14 requires (*“losing contenders map deterministically to
duplicate-start failure”*). Under real thread contention a fraction of losers
escape with a raw `DispatchAttemptTransitionError`
(`invalid_transition:EFFECT_ATTEMPT_STARTED->EFFECT_ATTEMPT_STARTED`) raised by
`_append_transition` in the window between the `_effect_attempt_started_is_durable`
pre-check and the create-only link — the `except DispatchAttemptIntegrityError`
remap in `begin_effect_attempt` only covers `record_already_exists`, not the
transition error. **Fail-closed and at-most-once still hold**; only the error
contract’s determinism does not. A caller catching
`DispatchAttemptAlreadyStartedError` specifically would let the
`DispatchAttemptTransitionError` escape.

**Recommendation (for `.1R.19R`):** wrap the `_append_transition` call in
`begin_effect_attempt` so **every** losing contender is normalised to
`DispatchAttemptAlreadyStartedError`. Encoded as regression evidence in
`test_finding_n20_4_concurrent_losers_do_not_all_map_to_already_started_error`.
Non-blocking on its own; folded into the referred repair.

---

## 10. Static / dynamic no-effect proof (§56–§58)

* No `src/pcae/core/runtime_dispatch_gate10.py`; no `Gate10Result` /
  `_GATE10_RESULTS`; no real (non-mock) `RuntimeAdapter`.
* AST scan of `runtime_dispatch_attempt_lifecycle.py`,
  `runtime_introspection.py`, `commands/runtime_inspect.py`: **no** `.dispatch(`
  call node, **no** `subprocess` / `socket` / `ssl` / `http.client` import,
  **no** process-spawn attr.
* `runtime_adapter.py`: exactly **one** `adapter.dispatch(` call site — the
  pre-existing resolved simulation adapter, contract-bounded, `execution_effect
  = none`.
* Dynamic re-derivation: concurrency / crash / corruption / malformed-result /
  runtime-inspect exercises recorded **zero** real effect-boundary calls.

---

## 11. Test-quality review of the `.1R.19` suite (§60 / §63)

* `tests/test_dispatch_attempt_durable_lifecycle_3w1r2b1r1_1r19.py` — **55/55
  green** at HEAD. Covers the §42 case list. Genuinely contract-derived for the
  state machine, disposition, idempotency, corruption, and non-authority.
* **Gap (feeds N-20-4):** the concurrency test asserts the winner count and
  fail-closed but does not assert the loser error *type* under enough stress to
  surface the `DispatchAttemptTransitionError` leak.
* **Weakening audit:** tests removed = 0; tests skipped-to-pass = 0; tests
  xfailed-to-pass = 0; security wildcarding = 0. The one `xfail(strict=True)`
  store-path-traversal demonstrator was **promoted to a passing expected-
  rejection test** — independently confirmed a real defect closure (the
  traversal is now rejected), not a weakened expectation.
* **The `.1R.19` scope-fence widenings that *were* made** (across `.1R.8` /
  `.1R.11` / `117` / `.1R.15.5` / `.1R.17` / `.1R.17R` / `.1R.17R.1` / `.1R.18`
  / both inspect import-allowlists) were independently reviewed: each adds the
  exact 5-file Slice-B set (no wildcard), keeps `<=` subset assertions, and
  keeps separate `forbidden` sets asserting Gate 5–8 byte-unchanged. Tight.
  **The defect is the *missing* widening of the r111r31 / r111r32 / r111r321
  family (N-20-1), not the quality of the widenings that were done.**

---

## 12. Adjudications

| Item | Adjudication |
|---|---|
| **DISPATCH-ATTEMPT DURABLE LIFECYCLE** | **substantively verified / closed-worthy** — durable / restart-safe transitions; exactly-one start; corruption fail-closed; no authority semantics; no effect call |
| **AT-MOST-ONCE ATTEMPT / FAIL-CLOSED UNCERTAINTY** | **substantively verified / closed-worthy** — no generic exactly-once claim; deterministic *outcome*; see N-20-4 for the non-blocking error-type nuance |
| **MALFORMED ADAPTER-RESULT REPAIR** | **substantively verified / closed-worthy** |
| **PATH-CONTAINMENT REPAIR** | **substantively verified / closed-worthy** |
| **RUNTIME-INSPECT DISCOVERABILITY** | **substantively verified / closed-worthy** |
| **ITEM 9** (A ∧ B ∧ C) | **substantively verified / closed-worthy** (all three sub-repairs) |
| **N-16-2** | **CLOSED (Slice-B scope; interpretation A)** — infrastructure correct; Gate-10-caller wiring is Slice C |
| **FIRST EXTERNAL EFFECT** | **ABSENT** (verified) |
| **SLICE-B LIFECYCLE ACCEPTANCE** | **BLOCKED** — pending `.1R.19R` (N-20-1 / N-20-2 / N-20-3) |
| **Slice-C blockers N-16-3 … N-16-7** | UNCHANGED — all remain hard prerequisites; no evidence in this phase affects them |
| **`.3` governance incident** | **UNAUTHORIZED** — preserved |

**Final verdict:** **BLOCKED INDEPENDENT-VERIFICATION RESULT (Option B).** The
substantive dispatch-attempt durable lifecycle, at-most-once semantics, the two
3S.2.1 repairs, the item-9 repair, and N-16-2 (Slice-B scope) are each
independently verified / closed-worthy and the first external effect is absent.
Slice-B lifecycle acceptance is **BLOCKED** on three undisclosed
`.1R.19`-attributable HPAC Layer-1/2 consumer-inventory guard regressions
(N-20-1), an inaccurate `.1R.19` finalized fixed-SHA A/B record (N-20-2), and a
self-contradicting `.1R.19` meta-guard (N-20-3) — the same defect class that
BLOCKED `.1R.18`. Not self-closed; the blocker is referred out.

---

## 13. Recommended repair phase (requires its own explicit human authorization)

**`149O.20L.7O.3W.1R.2B.1R.1.1R.19R` — Slice-B Scope-Fence and Verification-Evidence Reconciliation.**
Scope:

1. Widen the three HPAC Layer-1/2 consumer-inventory guards — `r111r31`
   (`test_new_hpac_modules_have_zero_preexisting_production_consumers`),
   `r111r32` (`test_hpac_repair_has_zero_preexisting_production_consumers`),
   `r111r321` (`test_foundation_has_no_production_consumers_or_gate_wiring`) —
   by exactly the two authorized Slice-B entries
   `("runtime_dispatch_attempt_lifecycle.py", "pcae.core.hpac_foundation")` and
   `("runtime_invocation.py", "pcae.core.hpac_foundation")` (no wildcard; each
   guard still rejecting any other importer).
2. Confirm the two consequential meta-guards (`.1R.19`’s
   `test_widened_guard_module_passes_at_head[...r111r32]` and `.1R.15.3`’s
   `test_v15_2_guards_pass_at_head`) go green as a result.
3. Issue a **provenance-preserving erratum** to the `.1R.19` canonical doc and,
   as a governed amendment, correct the `.1R.19` completion metadata / report
   fixed-SHA A/B figure to the true *“5 added (all explained by `.1R.19`,
   root cause N-20-1), 0 removed; 1 pre-existing flake disclosed”* — original
   text preserved verbatim.
4. Normalise `begin_effect_attempt` so every concurrent loser raises
   `DispatchAttemptAlreadyStartedError` (N-20-4). *(This is a `src/pcae` change —
   `.1R.19R` is a repair phase, not verification-only.)*
5. Re-run the fixed-SHA A/B to confirm 0 added / 0 removed after the widening.

No normative contract change. No Slice C work. No `adapter.dispatch()` call
site. No execution enablement. Then →
**`149O.20L.7O.3W.1R.2B.1R.1.1R.19R.1` — Independent Verification of the Slice-B
Reconciliation.** After `.1R.19R.1` closes, the Slice-B track is complete and
the next prerequisite work is the **Slice-C prerequisite set** (N-16-3 POL-005
narrow-eligibility rule + IV, N-16-4 real RE gate, N-16-5 real FIDO2/UI, N-16-6
RPAC-REQ-095 adapter, N-16-7 capability enablement) — each its own explicitly
authorized phase. **Slice C / D keep no phase ID** until all of N-16-3 … N-16-7
close.

---

## 14. Fresh `.1R.20` verification suite

`tests/test_dispatch_attempt_durable_lifecycle_iv_3w1r2b1r1_1r20.py` — **67
passed, 0 failed** (deterministic, `-p no:randomly`, no xdist). Sections:
range/scope reconstruction; RDGO §17/§18 + RPAC-REQ-064..072 lifecycle
re-derivation; transition matrix; PREPARED / EFFECT_ATTEMPT_STARTED semantics;
write-before-effect; duplicate-start; concurrent-start one-winner (4/8/16/32);
restart-after-PREPARED / after-start; uncertainty; terminal restart; receipt
non-authority; corruption battery; append-only; restart reconstruction;
idempotency derivation stability; cross-attempt isolation; malformed-result
original defect + repair + ordering + exception handling + no-effect; path
defect + ID grammar battery + resolved containment + valid-ID compatibility;
runtime-inspect human output + JSON identity + non-authority + non-mutation;
N-16-2 production-consumer inventory + adjudication; **N-20-1 / N-20-3
regression evidence**; **N-20-4 concurrency finding evidence**; runtime posture;
POL-005 byte identity; first-effect absence; static/dynamic no-effect.

---

*Independent verification performed by the primary human-authorized operator for
phase 149O.20L.7O.3W.1R.2B.1R.1.1R.20 through the governed `pcae` lifecycle. No
production source or normative contract was modified. The `.1R.19` historical
report is preserved unchanged; the formal erratum is deferred to `.1R.19R`.
DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved.*
