# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.18 — Independent Verification of the Gate-10 Pre-Effect Eligibility Coordinator

**Type:** independent verification of `.1R.17` (Slice A of the `.1R.16` Gate-10 plan).
**Status:** **BLOCKED — human decision required.** See §2.
**Verification-entry SHA:** `c618134a` (`.1R.17` finalize head; `origin/main..HEAD = 0` at entry).
**Immutable pre-`.1R.17` baseline:** `1f8b9c76` (verified: parent of the `.1R.17`
production implementation commit `302f5aba`).
**Production source modified by this phase:** none.
**Normative contracts modified by this phase:** none.
**Execution:** not enabled. Runtime `not_implemented / Observed / observe / unavailable`;
POL-005 hard DENY unchanged; 0 plugins / 0 capabilities; `pcae runtime inspect`
byte-identical.
**Governance:** governed `pcae` lifecycle only. The delegated `.3` finalization /
commit / push incident remains **UNAUTHORIZED**. Only the primary
human-authorized operator holds `.1R.18` lifecycle authority. This phase is
**not finalized** and **not self-closed**.

---

## 1. Verification work completed before the blocker

All of the following was RE-DERIVED from the primary contracts (RDGO-001 v3.1
§10 / §11 items 1–6 / §15 / §16 / §17 / §19; RPAC-001 v1.0 §7 RPAC-REQ-029;
HPAC-001 v2.1 §41; PBRD-001 v2.1 / POL-005; RE No-Go Registry 1.1), the
`.1R.16` planning document (F-G10-1 … F-G10-18), and current production
source read line-by-line — **not** from the `.1R.17` report, its test names,
or its helper names.

**A fresh, independent verification suite was authored and is green:**
`tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py`
— **111 tests, all passing** (deterministic, `-p no:randomly`, no xdist).

### 1.1 Substantive properties — ALL INDEPENDENTLY VERIFIED CLEAN

| Verification target | Result | Evidence (this phase's suite + source re-read) |
|---|---|---|
| **F-G10-1 trusted `Gate9Result` + `status == "consumed"`** | **VERIFIED** | `is_gate9_result` = `isinstance` **and** exact-object `_GATE9_RESULTS` membership (re-read `runtime_dispatch_gate9.py:374`). `None` / `object()` / `object.__new__` / copy / pickle → `gate10_untrusted_gate9_result`. A trusted-but-`already_consumed` result → `gate10_gate9_status_not_consumed`. Provenance ≠ consumed success. |
| **F-G10-2 / F-G10-3 durable `/2.1` re-read; `/2.0` hard rejection** | **VERIFIED** | The coordinator re-reads `consumption_store.resolve(proof_id)` from disk and trusts the durable record, using the in-memory `Gate9Result` only as a comparison key. `DurabilityUncertain` / absent → `gate10_consumption_record_read_back_failed`. Schema ≠ `HPAC-AUTHORITY-CONSUMPTION/2.1` **or** `authority_generation_binding is None` → `gate10_consumption_record_generation_snapshot_absent` (covers `/2.0`) with **no fallback**. |
| **F-G10-4 / F-G10-5 durable generation binding + current re-derivation** | **VERIFIED** | `_validate_authority_generation_binding` re-run; `snapshot_schema_version` exact; durable `consumption_generation == "absent"` required; malformed → `gate10_consumption_snapshot_malformed`. Current 5-marker vector re-derived from canonical durable stores; `principal` / `credential` / `approval` / `lifecycle` drift → `gate10_authority_generation_drift:<source>`; `consumption_generation` must be exactly `present:<this record's digest>` else `gate10_consumption_state_inconsistent`. |
| **Post-consumption drift (principal / credential / approval / lifecycle)** | **VERIFIED** | Each marker independently drift-tested → fail closed, `consumption.json` byte-unchanged (create-only; no un-consume path). Optional trusted-projection `revalidate_validated_authority_projection` re-run at Gate-10 entry; stale/untrusted → `gate10_stale_validated_authority_projection`. |
| **N-16-1 `build_gate10_authority_generation_resolver`** | **VERIFIED** | Composed from (calls) the **frozen** Gate-9 factory `build_production_authority_generation_resolver` (`runtime_dispatch_gate9.py` **byte-identical** to `1f8b9c76` — `git diff` empty) + reused `_lifecycle_generation_token` / `_consumption_generation_token`. Five markers, canonical durable state only, restart-reconstructible (independent A==B rebuild over a fresh store), no wall clock / mtime / nonce / `uuid` / `getpid` / `os.urandom` in the factory body. Unreadable principal/credential/approval → resolver raises → `gate10_internal_error_fail_closed`. |
| **N-16-1 `build_gate10_capability_snapshot_resolver`** | **VERIFIED** | Reads the canonical `runtime_introspection` constants only — `{Observed, observe, unavailable}`; creates no new capability source; registers / activates / promotes / elevates nothing; mutates no runtime constant (AST-checked); `pcae runtime inspect` byte-identical before/after. |
| **F-G10-7 runtime-capability check + §24 semantic wall** | **VERIFIED** | Step 12 requires the fresh snapshot to be **exactly** `Observed / observe / unavailable` via the same `_runtime_execution_unavailable` predicate Gate 9 uses. Any drift (`available`, partial dict, non-dict, `None`, `True`) → `gate10_runtime_capability_not_unavailable`. A caller cannot manufacture execution availability: the only snapshot that passes asserts the runtime **cannot** act. **`consumed human authority != runtime capability`** — no `Gate9Result` / `/2.1` record / generation binding / envelope state overrides `execution_availability`. |
| **F-G10-12 POL-005 / Gate-6 lineage** | **VERIFIED** | Trusts the durable `pb_binding.decision == "ALLOW"`; **no** PB policy re-run (`evaluate_pb_policy` / `evaluate_policy` / `run_gate6` / `PermissionBroker(` absent from source). POL-005 remains hard DENY (`permission_broker_foundation.py` byte-unchanged). |
| **F-G10-13 Gate-7 / RE lineage** | **VERIFIED** | Durable `runtime_enforcement_binding.verdict == "ALLOW"` **and** `expires_at > authority_current_time` required; else `gate10_re_lineage_not_allow` / `gate10_re_decision_expired`. `matched_no_go_ids` **not** referenced in code (per-decision diagnostic, not authority). Prior Gate-7 state is **not** a permanent substitute for current capability (step 12 re-reads). |
| **F-G10-10 / F-G10-11 containment + executable read-back** | **VERIFIED** | `run_gate8_process_containment` re-run over freshly re-resolved inputs + four-digest equality vs the handed `Gate8Result` **and** the durable `dispatch_binding.containment_evidence_ref`; executable re-`stat` + re-`sha256`. Independent drift tests — executable hash, absent/symlink, argv, cwd, env allowlist, `time_limit_ref`, `credentials_required` — each → fail closed, no envelope. |
| **F-G10-13 envelope mint ordering** | **VERIFIED** | Source order proven: `envelope = DispatchEnvelope(_seal=…)` occurs strictly after every authoritative check (capability, generation drift, Gate-8 re-run, executable re-hash, PB lineage). On **every** negative path `_DISPATCH_ENVELOPES` is unchanged — no leaked mint. |
| **§39 RPAC-REQ-029 field equivalence** | **VERIFIED** | All 30 envelope slots present and bound to the durable record / recomputed digests; `envelope_schema_version == "RPAC-DISPATCH-ENVELOPE/1.0"`; `expires_at == re_expires_at`; `contract_versions` names RDGO-001/3.1, HPAC-001/2.1, RPAC-001/1.0 + schema versions; 64-hex `envelope_digest`. No extra authority semantics. |
| **§40–§42 `DispatchEnvelope` non-bearer** | **VERIFIED** | `_seal` guard rejects caller construction; `__init_subclass__` raises; `__setattr__` immutable; `__reduce__` raises (pickle **and** `deepcopy` **and** direct `__reduce__()` all `TypeError`); `__eq__` / `__hash__` are identity; `is_dispatch_envelope` is **exact-object registry membership** — a copy, `object.__new__`, `to_reference_document()` dict, or reconstruction is **not** a member. `is_dispatch_envelope` is documented and named as **process-local provenance only**, explicitly **not** effect authority. |
| **§43 effect-bearing consumer inventory** | **VERIFIED — 0** | `git grep` for `is_dispatch_envelope` / `run_gate10_pre_effect_eligibility` / `_DISPATCH_ENVELOPES` / `build_gate10_` under `src/pcae` returns exactly `{runtime_dispatch_gate10_eligibility.py}`. The pre-existing `SimulationDispatchEnvelope` (mock-v1 `simulate_invocation` path) is a **distinct type**, not wired into the RDGO Gate 5–11 chain. |
| **§44 / §45 no adapter call site / no effect primitive** | **VERIFIED** | AST walk: **no** `.dispatch()` `Call` node; `posix_spawn` absent from the AST dump. After stripping every string literal (so docstring prose that names the forbidden concepts is ignored), the remaining **code** contains no `subprocess` / `Popen` / `os.system` / `os.popen` / `exec*` / `spawn*` / `socket` / `ssl.` / `pty` / `ctypes` / `fcntl` / `urlopen` / `http.client` / `requests.` / `httpx.` / `fido2` / `webauthn` / `ctap` / `RuntimeAdapter` / `DispatchReceipt` / `getpass` reference. The module imports nothing effectful. |
| **§46 dynamic zero-effect boundary trap** | **VERIFIED** | `os.system` / `os.posix_spawn` / `os.popen` / `os.fork` / `os.execv` / `os.execve` / `subprocess.{Popen,run,call,check_output}` / `socket.socket` all monkeypatched to fail; the positive path **and** every negative branch were run — **zero** effect-boundary calls. |
| **§47 no positive production path** | **VERIFIED** | With **no** provenance substitution a hand-built `Gate9Result` is not a registry member → fail closed at step 1. Independent blockers re-confirmed: deterministic HPAC NON_REAL; real Gate-7 DENY; runtime `unavailable`; no registered real adapter; POL-005 hard DENY; no protected UI / real FIDO2. Gate-7 DENY blocks **independently** of the capability stop. |
| **§48 test-boundary substitution isolation** | **VERIFIED** | After the fixture's `monkeypatch` teardown the real `is_gate{5,7,9}_result` predicates reject a hand-built object. `g10.__all__` exposes no `mint_*` / `register_*` / `force_eligible` symbol. The substitution cannot mutate the canonical runtime posture (asserted before/after). |
| **§51–§57 Gate 9 byte identity + Gate 5–8 + introspection + registry + POL-005 + contracts unchanged** | **VERIFIED** | `git diff 1f8b9c76 HEAD` empty for `runtime_dispatch_gate{5,7,8,9}.py`, `runtime_dispatch_permission.py`, `runtime_invocation_authority_consumption.py`, `runtime_introspection.py`, `runtime_authority.py`, `runtime_adapter.py`, `runtime_registry.py`, `mock_runtime_adapter.py`, `permission_broker_foundation.py`, `shell_gate.py`, and every named `docs/contracts/**` file + the RE No-Go Registry. Production scope since baseline = **exactly one new file**. `RuntimeRegistry` still empty. |
| **F7 threat model** | **VERIFIED — not broadened** | Stated verbatim in the module docstring ("same-account autonomous-agent assumption", "same-process Python code execution", "threat model NOT broadened"). |

### 1.2 Non-blocking observations recorded

* **N-18-2 (INFO).** The `.1R.17` phase report / canonical doc prose says the
  fail-closed reason taxonomy has "**38** stems"; the actual
  `GATE10_ELIGIBILITY_REASON_IDS` `frozenset` carries **39** members. The
  taxonomy is closed and correctly a `frozenset`; only the prose count is
  off by one. Non-blocking.
* **N-18-3 (INFO).** Phase prompt §23 expects "with the current production
  capability resolver: **NO `DispatchEnvelope`** because execution remains
  unavailable." The verified Slice-A design (`.1R.16` §13 F-G10-7) is the
  **opposite polarity**: step 12 requires the snapshot to attest
  `unavailable` **to proceed** (mirroring `runtime_dispatch_gate9`'s own
  "never consume authority into a runtime that could act"), so an envelope
  **is** minted under the canonical non-executing posture. The decisive
  no-effect guarantee is **structural** — the module has no
  `adapter.dispatch()` call site (§44) and zero effect-boundary calls on any
  path (§46) — not envelope suppression. The §24 semantic wall
  (`consumed human authority != runtime capability`) holds. This is a
  designed, `.1R.16`-documented choice; Slice C is where the polarity for a
  genuinely-available runtime is (re)decided. Non-blocking.

---

## 2. THE BLOCKER

### 2.1 Statement

**`.1R.17` shipped 17 test regressions in pre-existing scope-fence /
consumer-inventory guards that it did not widen and did not disclose, and
`.1R.17`'s finalized, pushed, Telegram-notified phase-completion report
records a fixed-SHA A/B result — "ADDED failures in B = 0; REMOVED = 0" —
that is contradicted by primary evidence.**

### 2.2 Primary-source evidence

Fixed-SHA A/B, immutable baseline `1f8b9c76` (dedicated `git worktree`),
deterministic `-p no:randomly`, **no xdist**, selection
`-k "gate5 or gate7 or gate8 or gate9 or introspection or runtime_dispatch or
authority_consumption or gate10 or hpac or runtime_authority or serialization"`:

| Run | Failing nodes |
|---|---|
| **A** — baseline `1f8b9c76` | **29** |
| **B** — verification-entry `c618134a` (+ this phase's 3 non-production commits) | **46** |
| **ADDED in B (not in A):** | **17** |
| **REMOVED (in A, not B):** | **0** |
| candidate-only (`.1R.17` + `.1R.18` suites) among the 17 | **0** |

The 29 A-run failures reproduce identically in B (the pre-existing `main`
class: HATP / HPAC contract-freeze text asserts, HATP proof-model
serialization scope, `test_runtime_authority_pb_verification` registry text
assert). The **17 added** are **not** in that class and each was verified to
**pass at `1f8b9c76` and fail at `c618134a`**:

```
test_gate7_runtime_enforcement_coordinator_independent_verification_3w1r2b1r1_1r13_3.py
  ::test_no_downstream_production_consumer_of_gate7_result
  ::test_gate7_is_the_only_new_gate6_decision_consumer
test_gate7_runtime_enforcement_coordinator_integration_3w1r2b1r1_1r13_2.py
  ::test_gate7_is_sole_production_consumer_of_is_gate6_decision
test_gate8_process_containment_coordinator_independent_verification_3w1r2b1r1_1r13_5.py
  ::test_gate7_result_consumer_grep_is_exactly_gate7_and_gate8_today
  ::test_no_gate9_consumer_of_gate8result_exists_yet
  ::test_sole_production_owner_of_gate8_boundary
test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py
  ::test_gate8_is_sole_production_owner_of_containment_boundary
  ::test_gate8_is_the_only_new_gate7_result_consumer
  ::test_gate8result_has_zero_downstream_production_consumers
test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py
  ::test_gate8result_new_consumer_is_only_gate9
  ::test_gate9result_has_zero_downstream_production_consumers_and_no_gate10
  ::test_no_alternate_consumption_store_create_caller_in_production
  ::test_sole_semantic_owner_of_gate9_consumption_boundary
test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py
  ::test_gate9_is_sole_production_owner_of_consumption_boundary
  ::test_gate9_is_the_only_new_gate8_result_consumer
  ::test_gate9result_has_zero_downstream_production_consumers
test_runtime_dispatch_contract_normalization_independent_verification_3w1r2b1r1_1r15_5.py
  ::test_gate_5_6_7_8_production_modules_byte_unchanged_since_baseline
```

Representative failure:

```
tests/test_gate7_..._1r13_3.py::test_no_downstream_production_consumer_of_gate7_result
  assert hits <= {gate7.py, gate8.py, gate9.py}
  AssertionError: unexpected Gate7Result consumer:
    ['.../runtime_dispatch_gate10_eligibility.py', '.../runtime_dispatch_gate7.py',
     '.../runtime_dispatch_gate8.py', '.../runtime_dispatch_gate9.py']
```

### 2.3 Attribution

**16 of 17** are *genuine* new-authorized-consumer facts: the `.1R.17`
non-effecting eligibility coordinator legitimately references, **in code**,
`Gate7Result` / `is_gate7_result` (6×), `Gate8Result` / `is_gate8_result`
(8×/2×), `Gate9Result` / `is_gate9_result` (7×/4×), `Gate6Decision` /
`is_gate6_decision` (3×/2×), `run_gate8_process_containment` (3×), and
`RuntimeInvocationAuthorityConsumptionStore` (2×) — exactly the lineage /
containment re-run RDGO-001 v3.1 §11 item 4 + `.1R.16` §16 **mandate**. This
is the identical situation `.1R.17` handled for **8 other** guards by the
established "allowlist widening" precedent; it simply **missed these**.

**1 of 17** (`test_sole_semantic_owner_of_gate9_consumption_boundary`) is a
docstring-grep false positive: the module docstring names
`run_gate9_atomic_authority_consumption` once when explaining why the
coordinator is structurally unreachable.

**The `.1R.15.5` byte-scope guard** (`test_gate_5_6_7_8_production_modules_byte_unchanged_since_baseline`)
asserts `git diff 4d480553..HEAD -- src/pcae/core` is a subset of
`{gate9.py, runtime_invocation_authority_consumption.py}`; it now also sees
`runtime_dispatch_gate10_eligibility.py`. Gate 5–8 remain byte-unchanged —
only the guard's `allowed` set is stale.

**None of the 17 indicates a substantive trust-boundary violation** — Gate 10
is an authorized consumer per RDGO §11 / `.1R.16`. The 8 guards `.1R.17` DID
widen each still fail for any *other* importer (independently reviewed and
confirmed in this phase's suite, §49/§50). The defect is **incomplete
scope-fence coverage plus an inaccurate governance-record A/B figure**.

### 2.4 Why this exceeds `.1R.18` verification-only authority

1. **The `.1R.17` phase-completion report is finalized, pushed to
   `origin/main`, and a Telegram notification was dispatched** stating "0
   added failures" and "eight prior scope-fence guards widened … each still
   fails for any other importer". Primary evidence contradicts the first
   claim and shows the second was incomplete. Correcting a completed,
   published governance record is not a delegated-IV action
   (phase prompt §70 / §71: "Only the primary human-authorized operator
   holds `.1R.18` lifecycle authority"; cf. the still-`UNAUTHORIZED` `.3`
   incident).
2. **Remediation touches prior independent-verification phases.** Widening
   these guards means editing assertions and rationale inside the `.1R.13.2`,
   `.1R.13.4`, `.1R.13.5`, `.1R.14`, `.1R.15`, and `.1R.15.5` suites —
   including an exact-equality assertion and a comment that literally reads
   `# Gate 10 does not exist.` (`.1R.14`). Whether `.1R.18` may re-author
   other IV phases' guards, or whether that belongs to a dedicated
   `.1R.17R` reconciliation phase, is a scope decision for the operator.
3. **The repository's standard acceptance gate does not pass.** This phase's
   own task contract lists `python -m pytest -n auto passes` as an
   acceptance check; it currently fails, attributable to `.1R.17`. A
   governed `pcae phase complete` for `.1R.18` would have to record a
   non-clean test state or a scope expansion that was never authorized.

### 2.5 What was NOT modified

* **No production source** changed (`git diff 1f8b9c76 HEAD -- src/pcae` =
  the single `.1R.17` file only).
* **No normative contract** changed.
* **No scope-fence guard** was widened by this phase.
* **No `pcae phase complete`** was run; `.1R.18` is not finalized, not
  self-closed, and the recommended-next-phase pointer is unchanged.

---

## 3. Repository / governance state at BLOCK

| Fact | Value |
|---|---|
| Working tree | clean |
| `pcae health` / `check` / `status coherence` | healthy / passed / coherent |
| `pcae doctor task-memory` | warning-only (pre-existing O4 `tasks/DONE.md` omissions) |
| `pcae runtime inspect` | `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; PB `execution_unavailable` |
| Active task | `Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.18: Independent Verification …` (open, not closed) |
| `origin/main..HEAD` | **3** (all `.1R.18` governed infrastructure; no production / contract change) |
| Unpushed commits | `e6c1b7cd` open governed phase task · `8ab50a8c` independent-verification suite (111 tests, green in isolation) · `5860dabd` remove superseded idle active-task file |
| Pushed | **no** (`pcae push` not run) |
| Telegram | not dispatched (no `pcae phase complete`) |
| `.3` governance incident | `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved |

---

## 4. Exact human decision required

Choose the remediation path for the 17 `.1R.17`-attributable guard
regressions and the inaccurate `.1R.17` A/B record, and authorize the
corresponding scope:

**Option A — fold the fix into `.1R.18`.** Authorize `.1R.18` to (i) widen
the 16 genuine consumer-inventory guards with the established allowlist
precedent (each still rejecting any other importer), (ii) repair the 1
docstring-grep guard, (iii) extend the `.1R.15.5` byte-scope `allowed` set,
(iv) add a preserved-original erratum to the `.1R.17` canonical doc noting
the true count was **17 added (all explained)**, and (v) then complete
`.1R.18` finalization with the corrected fixed-SHA A/B. Fastest; expands
`.1R.18` scope to re-authoring six earlier IV suites.

**Option B — dedicated `.1R.17R` reconciliation phase.** Close `.1R.18` now
as **INDEPENDENTLY VERIFIED WITH A BLOCKING FINDING** (substantive properties
all clean per §1; the guard/A-B finding referred out), then run a separate
governed `.1R.17R` to complete the scope-fence widening and correct the
`.1R.17` record, followed by its own IV. Cleanest governance separation;
one extra phase.

**Option C — re-issue `.1R.17`'s completion record.** Treat the inaccurate
A/B figure as a governance-record defect and correct `.1R.17`'s
`phase-completion-report.md` / metadata under a governed amendment before
`.1R.18` proceeds.

`.1R.18` will resume on your instruction. No `.1R.19` / Slice B / Slice C
work is begun. Execution is not enabled.

---

## 5. Recommended next phase (unchanged; not begun)

`149O.20L.7O.3W.1R.2B.1R.1.1R.19` — Dispatch-Attempt Durable Lifecycle,
Idempotency, and 3S.2.1 Prerequisite Repairs (Slice B) — remains the
recommendation **after** `.1R.18` closes. Slice C / D keep no phase ID.

---
*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.18 (BLOCKED).*
