# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26 — N-16-4 Real Positive Single-Attempt Runtime Enforcement Gate Implementation

**Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.26`
**Type:** governed implementation — one normative contract (new), one production
file, one new test suite, phase-aware guard-fence reconciliation, governed
lifecycle.
**Phase-entry SHA:** `28b8b2b70dcd4642dc45d4a3961a5218402c3c7c` (`.1R.25` finalize
head; `origin/main..HEAD = 0` at entry).
**Verdict:** **N-16-4 IMPLEMENTED — INDEPENDENT VERIFICATION PENDING `.1R.27`.**
REPRC-001 v1.0 **AUTHORED / FROZEN — IV PENDING.** `Gate7Result(decision="ALLOW")`
**SYNTHETIC TEST PATH REACHABLE; PRODUCTION PATH UNREACHABLE.** B-1 = Model B1-B,
B-2 = Model B2-D, B-3 = Currentness B — **IMPLEMENTED EXACTLY.** Runtime
`not_implemented / Observed / observe / unavailable`. First external effect
ABSENT. N-16-4 is **not** CLOSED.

---

## 1. Primary sources inspected

**Phase artifacts (full or to complete relevant scope).** `PROJECT_STATUS.md`;
the `.1R.25` trust-boundary freeze
(`docs/PHASE_…_1R_25_….md`, 832 lines, full — the authoritative freeze);
the accepted BLOCKED first-`.1R.25` implementation report (session transcript +
memory record — STOP at primary-source review, no repo mutation); the `.1R.24`
planning artifact (`docs/PHASE_…_1R_24_….md`, "conceptual REPRC-001 §N" text);
`.1R.22R.1` / `.1R.23` / `.1R.22` / `.1R.21` (STOP-at-primary-source precedent;
RE-DERIVE / fixed-SHA-A/B discipline; guard-fence reconciliation precedent);
`.1R.16` §35 row 14 + §36.2 (IDs above `.1R.20` recommended not reserved);
`.1R.13.1` (frozen Gate-6/Gate-7 file matrix; `runtime_dispatch_permission.py`
"None anticipated"); `.1R.13.2` / `.1R.13.3` Gate-7 frozen decisions;
`.1R.15` / `.1R.15.2` / `.1R.15.3` Gate-9; `.1R.17R.1` / `.1R.19R.1` Slice A /
Slice B; `.1R.18` / `.1R.20` guard-fence precedent.

**Normative / current contracts.** RDGO-001 v3.1 §8 (read verbatim —
`docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md:220-251`: "Its positive
decision is single-attempt, expiring, and invalid across any relevant input or
policy change. A denial, failure, stale input, unavailable target, or unresolved
no-go stops the flow." — **contains no "a future Gate 8 MUST re-run Gate 7"
clause**, see §10 finding N-16-4-IMPL-1); §10 item 7; §21 versioning; §0 walls.
HPAC-001 v2.1 §41; `HPAC-AUTHORITY-CONSUMPTION/2.1`
(`runtime_invocation_authority_consumption.py` — `CONSUMPTION_SCHEMA_VERSION`,
the closed 5-field `runtime_enforcement_binding` set at line 125). PBRD-001 v3.0
§14; PBNDE-001 v1.0 §7. RIASC-001 v3.0 / RIHAC-001 v2.0. RPAC-001 v1.0
(RPAC-REQ-029 `DispatchEnvelope`, `DISPATCH_ENVELOPE_SCHEMA_VERSION`). The RE
No-Go Registry schema 1.1; NG-025.

**Production source (byte-current).** `src/pcae/core/runtime_dispatch_gate7.py`
(699 lines pre-phase, full) — `Gate7Result` (`__slots__`, `__init__` seal,
`__reduce__` raises, `__eq__`/`__hash__` identity-only, `__init_subclass__`
raises), `is_gate7_result`, `run_gate7_runtime_enforcement` (steps 1–8),
`RuntimeEnforcementPosture`, `resolve_runtime_enforcement_posture`,
`_matched_blocking_no_go_ids`, `_pb_decision_digest`, `_GATE7_RESULTS`,
`_GATE7_RESULT_CONSTRUCTOR_SEAL`, `GATE7_DECISION_VALUES`.
`runtime_dispatch_gate8.py` — `_gate7_result_digest` (L418-436: 11 fields incl.
`expires_at`; docstring "**never re-runs Gate 7**"), imports
`is_trusted_validated_authority_projection` +
`revalidate_validated_authority_projection` (L127-128), the
`gate8_stale_validated_authority_projection` reason (L538), the
`gate8_gate7_decision_not_allow` hard stop (L590-591).
`runtime_dispatch_gate9.py` — the item-7 `runtime_enforcement_binding` write
(reference, not a re-run). `runtime_dispatch_gate10_eligibility.py` — the Gate-7
consumption block, step 11 (`re_expires_at` string compare `<= authority_current_time`
→ `gate10_re_decision_expired`, L790-791), step 12 capability re-read
(`gate10_runtime_capability_not_unavailable`), step 13 generation re-derivation
(`authority_generation_resolver()` → `_first_generation_drift` →
`gate10_authority_generation_drift:<source>`), `DISPATCH_ENVELOPE_SCHEMA_VERSION`
+ the `DispatchEnvelope.__setattr__` immutability pattern (L328-331).
`runtime_authority.py` — `compute_canonical_digest`,
`is_trusted_validated_authority_projection`,
`revalidate_validated_authority_projection`.
`runtime_dispatch_permission.py` — `RuntimeDispatchIdentity.idempotency_key`
(L383), `Gate6Decision.__slots__` (no PB-request/admission field), the builder
input validation rejecting caller-preset `admission_record_digest` /
`admission_class`.
`runtime_introspection.py` — `CURRENT_RUNTIME_STATE` /
`CURRENT_MAXIMUM_PLUGIN_CAPABILITY` / `EXECUTION_AVAILABILITY`.

**Guard tree.** Whole-`tests/` grep (`Gate7Result` / `runtime_dispatch_gate7` /
`run_gate7_runtime_enforcement` / `_GATE7_RESULTS` / `is_gate7_result` /
`runtime_enforcement_binding` / `RDGO-001 v3.1` / `matched_no_go_ids ==` /
`expires_at`) — 41 files. The two Gate-7 suites (`.1R.13.2` 705 lines / `.1R.13.3`
680 lines) read to every load-bearing assertion; the Gate-8/9/10 IV suites; the
`.1R.19R` / `.1R.19R.1` / `.1R.22R` meta-guards; `test_hpac_authority_consumption.py`;
`test_narrow_eligibility_policy_iv_3w1r2b1r1_1r23.py`.

**Repository inspection at entry (phase prompt §4).** `git status` clean;
`git log --oneline origin/main..HEAD` empty; `git rev-list --count
origin/main..HEAD` = 0; `pcae health` healthy; `pcae check` passed; `pcae status
coherence` coherent; `pcae doctor task-memory` warning-only historical `DONE.md`
omissions (pre-existing hygiene debt, no current-phase error); `pcae push check`
`nothing_to_push`; `pcae runtime inspect` `not_implemented / Observed / observe /
unavailable`, registry empty, 0 plugins / 0 capabilities, Permission Broker
`execution_unavailable`, governance posture `non-executing`; `pcae notify status`
Telegram configured and outbound-ready; `pcae phase-report show --latest` = the
`.1R.25` completion report. `.1R.25` confirmed as the latest completed phase; no
active governed phase before startup.

---

## 2. `.1R.25` freeze reconstruction (treated as authoritative)

| Freeze | Selection | Consequence for `.1R.26` |
|---|---|---|
| **B-1** | **Model B1-B** | No `HPAC-AUTHORITY-CONSUMPTION/2.1` change; no Gate-9 item-7 field expansion; no HPAC-001 change. Gate-7 currentness anchored by the existing item-7 `evaluated_input_digest` + item-9 `authority_generation_binding` + live re-derivation owners. **No `currentness_binding` slot on `Gate7Result`.** |
| **B-2** | **Model B2-D** | Gate 7 binds **no** adapter-admission evidence; findings N-16-4-2 and N-16-4-3 (as framed) **WITHDRAWN**. No `admission_record_digest` / `admission_class` field; `_pb_decision_digest` composition unchanged. No `runtime_dispatch_permission.py` / `Gate6Decision` change. |
| **B-3** | **Currentness B** | `run_gate7_runtime_enforcement` signature **unchanged**; no `authority_generation_resolver` parameter; no `currentness_binding` slot. Currentness = existing `authority_freshness_digest` + Gate 7 creation-time projection revalidation + Gate 8's independent projection revalidation + Gate 10 step 13's generation re-derivation. |
| **Schema** | 3 additive `__slots__` | `reprc_schema_version`, `runtime_enforcement_result_id`, `idempotency_key`. |
| **TTL** | 300 s, ALLOW branch | `expires_at = evaluated_at + REPRC_MAX_RESULT_TTL_SECONDS`; bounded wall-clock backstop only (finding N-16-4-1). |
| **Vocab** | positive `causing_reason_ids` | finding N-16-4-4. |
| **Immutability** | `__setattr__` guard mirroring `DispatchEnvelope`. |
| **Contracts** | REPRC-001 v1.0 only | new companion; authored first; RDGO/HPAC/PBRD/PBNDE/PBPA/RPAC/RE-No-Go **NO CHANGE**; no MAJOR, no MINOR. |
| **Surface** | `runtime_dispatch_gate7.py` only + REPRC-001 + new tests. |

**B-1 / B-2 / B-3 implementability confirmed against byte-current source
(phase prompt §69.4):** B1-B needs no store change — the existing digests carry
it; B2-D needs no route — admission is not in the RDGO §8 conjunction and is
gated by Gate 6/8/10; Currentness B needs no signature change — the four owners
already exist. **No valid early-STOP condition applies** (phase prompt
"VALID EARLY STOP CONDITIONS" checklist, §31 of `.1R.25`, re-checked item by item
against the implementation — none holds; the one imprecision found in the
`.1R.25` prose is corrected in REPRC-001 itself with disclosure, §10, and needs
no production change outside `runtime_dispatch_gate7.py`).

---

## 3. REPRC-001 v1.0 — first substantive commit and freeze

| Item | Value |
|---|---|
| File | `docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md` |
| First substantive commit | **`fa62717bfb2c84d45126e8cf98a8b540b9c7857a`** |
| SHA-256 at freeze | **`8700c8717d3a822f61f9139cec0fefef48a06b6576a7a1ea4fc4420c14c7c99c`** |
| Disclosed correction | one — finding **N-16-4-IMPL-1** (§10), §8 / §8.1 wording |
| Correction commit | `cde76fd3286852cccbd4348aa3ccc785295d6383` |
| Final SHA-256 | **`c30cb30d81ab2f4080cc592fdc9e71cfb2e0224fdb1ac452d676db0d2b3226d1`** |
| Semantic drift after implementation began | **none** (the single change is the disclosed §8/§8.1 accuracy correction, made before the production commit) |

REPRC-001 v1.0 sections: §1 `reprc_schema_version`; §2 positive-result meaning +
explicit negative list + decision vocabulary; §3 `runtime_enforcement_result_id`
composition + identity challenges (REPRC-INV-001); §4 non-bearer trust model;
§5 serialization / reconstruction; §6 immutability; §7 `evaluated_at` /
`authority_current_time` / `expires_at` TTL; §8 Currentness B + the four
mandatory stale-rejection owners (REPRC-INV-002) + non-bearer proof
(REPRC-INV-003); §9–§12 Gate 8 / Gate 9 / Gate 10 / Slice-B relationships;
§13 B2-D (no admission binding); §14 PB consumed not re-run; §15 duplicate /
restart Model A; §16 observability; §17 the synthetic / test-only positive path;
§18 production positive path unreachable; §19 no-go semantics; §20 positive
rationale vocabulary; §21 sole constructor + finite consumer set; §22
contract-production equivalence obligation; §23 invariants REPRC-INV-001..006;
§24 versioning + freeze verdict.

---

## 4. Production change — `src/pcae/core/runtime_dispatch_gate7.py` (the ONLY production file)

`git diff --name-only 28b8b2b7 HEAD -- src/pcae` = exactly
`src/pcae/core/runtime_dispatch_gate7.py`.

### 4.1 `Gate7Result` schema — old → new

| Field | old | new |
|---|---|---|
| `decision` | ✓ | ✓ unchanged (`"ALLOW"` \| `"DENY"`) |
| `matched_no_go_ids` | ✓ | ✓ unchanged (empty on ALLOW) |
| `causing_reason_ids` | ✓ (empty on ALLOW) | ✓ **non-empty on ALLOW** — `GATE7_POSITIVE_CAUSING_REASON_IDS` |
| `invocation_id` / `attempt_id` / `request_id` | ✓ | ✓ unchanged |
| `pb_decision_digest` | ✓ | ✓ **composition unchanged** (N-16-4-3 withdrawn) |
| `authority_freshness_digest` | ✓ | ✓ unchanged — the currentness anchor (Currentness B) |
| `evaluated_input_digest` | ✓ | ✓ **composition unchanged** (no admission / PB-request / currentness key added) |
| `runtime_posture_digest` | ✓ | ✓ unchanged |
| `expires_at` | ✓ (= `authority_current_time`) | ✓ field kept; **ALLOW branch value → `evaluated_at + 300 s`**; DENY branch → `evaluated_at` (unchanged) |
| `evaluated_at` | ✓ | ✓ unchanged (= `authority_current_time`) |
| `reprc_schema_version` | — | **NEW** — `"REPRC-001/1.0"` (rejected on construction if any other value) |
| `runtime_enforcement_result_id` | — | **NEW** — §4.2 |
| `idempotency_key` | (inside `evaluated_input_digest` only) | **NEW explicit slot** = `identity.idempotency_key` |
| `_seal` | ✓ | ✓ unchanged |

**Net additive slots: exactly three.** No field removed or repurposed. `__slots__`
retained (no `__dict__`).

### 4.2 `runtime_enforcement_result_id` — exact formula

```python
runtime_enforcement_result_id = compute_canonical_digest({
    "invocation_id":              identity.invocation_id,
    "attempt_id":                 identity.attempt_id,
    "idempotency_key":            identity.idempotency_key,
    "pb_decision_digest":         _pb_decision_digest(gate6_decision),
    "evaluated_input_digest":     evaluated_input_digest,   # the frozen 16-key composition
    "authority_freshness_digest": projection.freshness_verdict_digest or projection.evidence_digest(),
    "runtime_posture_digest":     posture.digest(),
    "reprc_schema_version":       "REPRC-001/1.0",
})
```

`compute_canonical_digest` is the repository-standard NFC-normalized
sorted-key-JSON SHA-256 helper (`runtime_authority`). Computed **once**, after
`evaluated_input_digest` and before the ALLOW/DENY branch; both branches carry
it. It is a digest over lower-level canonical digests — **no circular identity**.
It excludes `decision`, `expires_at`, `evaluated_at`. No admission evidence
(B2-D). No `currentness_binding` (Currentness B).

### 4.3 Idempotency-key binding

`idempotency_key` slot = `identity.idempotency_key` (the Gate-2 canonical content
digest). Mutating it changes `evaluated_input_digest` **and**
`runtime_enforcement_result_id`; a downstream re-derivation of either mismatches
and rejects. No caller-selected independent key path.

### 4.4 Immutability

`Gate7Result.__init__` binds every field via `object.__setattr__` (so
construction is not blocked by the guard), then `self._seal = _seal` last.
`Gate7Result.__setattr__` raises `AttributeError("Gate7Result is immutable")`
once `getattr(self, "_seal", None) is _GATE7_RESULT_CONSTRUCTOR_SEAL`;
`Gate7Result.__delattr__` always raises. Mirrors `DispatchEnvelope`
(`runtime_dispatch_gate10_eligibility.py:328-331`). Tested: direct `setattr`,
`del`, slot mutation, `object.__new__`, copy-style reconstruction — all rejected
or not a `_GATE7_RESULTS` member.

### 4.5 TTL / `expires_at`

New module constant `REPRC_MAX_RESULT_TTL_SECONDS: int = 300`. New helper
`_result_expires_at(evaluated_at)` — `datetime.fromisoformat(value.replace("Z",
"+00:00")) + timedelta(seconds=300)`, re-serialized with the trailing `Z`
preserved. No monotonic clock, no `time.time()`, no PID, no nonce —
restart-reconstructible from the two strings. A malformed
`authority_current_time` on the ALLOW branch raises → caught by the module's
`except Exception` → `gate7_internal_error_fail_closed` (no positive result with
an unbounded `expires_at`). DENY branch keeps `expires_at = authority_current_time`
(never consumed forward). For `NOW = "2026-08-29T00:30:00Z"` the ALLOW `expires_at`
is `"2026-08-29T00:35:00Z"` — a bounded, `_bounded_string(…, 64)`-valid,
lexicographically-greater string that Gate 10 step 11's
`re_expires_at <= authority_current_time` comparison accepts within the window
and rejects outside it.

### 4.6 Positive `causing_reason_ids` vocabulary

```python
GATE7_POSITIVE_CAUSING_REASON_IDS = (
    "gate7_runtime_enforcement_satisfied",
    "gate7_pb_decision_allow_consumed",
    "gate7_authority_projection_revalidated",
    "gate7_runtime_target_within_local_cli_v1_scope",
    "gate7_no_blocking_re_no_go_matched",
    "gate7_synthetic_evaluation_path",
)
```

`gate7_synthetic_evaluation_path` is present on every currently reachable
positive result (the posture resolver was substituted). Negative-branch reasons
are the current fail-closed set, unchanged.

### 4.7 Synthetic / test-only positive seam

**No production change for the seam** — `run_gate7_runtime_enforcement` still
calls the module-global `resolve_runtime_enforcement_posture()` at step 7 (no
parameter added — Currentness B / §18 of the phase prompt). Tests substitute it
via `monkeypatch.setattr(runtime_dispatch_gate7,
"resolve_runtime_enforcement_posture", <substitute>)` returning a
`RuntimeEnforcementPosture` with `execution_available is True` and empty
`matched_no_go_ids` — exactly the `.1R.13.2` / `.1R.13.3` accepted boundary
(which already monkeypatches this same attribute). The module docstring
documents this as the test-only seam and points to REPRC-001 §17.

**Isolation proof (`.1R.26` suite, tests 01–04, 18, 27, 43, 49–50):**
`run_gate7_runtime_enforcement`'s AST parameter list is exactly
`{gate6_decision, gate5_result, identity, inputs, authority_current_time}` — no
`resolver`, no `posture`; no production `src/pcae` code assigns
`resolve_runtime_enforcement_posture`; no env var / config path; the real
`resolve_runtime_enforcement_posture()` returns `execution_available is False`
with a non-empty `matched_no_go_ids`; the positive branch stays
`# pragma: no cover - unreachable in production`; the `.1R.26` autouse fixture
`_isolate_gate7_result_registry` restores `_GATE7_RESULTS` after every test so no
other suite observes a positive result it did not create.

---

## 5. Currentness B — the four named mandatory stale-rejection owners (re-derived from source)

| # | Owner | Exact function / step | Reason id on drift | Classification |
|---|---|---|---|---|
| 1 | Gate 7, creation time | `is_trusted_validated_authority_projection(projection)` + `revalidate_validated_authority_projection(projection, current_time=authority_current_time)` (re-runs `validate_approval`) — `runtime_dispatch_gate7.py` step 5 | `gate7_stale_validated_authority_projection` (returns `(None, …)`, **no `Gate7Result`**) | MANDATORY |
| 2 | Gate 8, consumer | independent projection re-trust + `revalidate_validated_authority_projection` at its own point of use + `_gate7_result_digest` lineage recheck — `runtime_dispatch_gate8.py` (imports both predicates L127-128) | `gate8_stale_validated_authority_projection`; a trusted **negative** `Gate7Result` → `gate8_gate7_decision_not_allow` before Shell Gate | MANDATORY |
| 3 | Gate 10 step 13 | `authority_generation_resolver()` → `_first_generation_drift(durable_snapshot, current_markers)` vs. item-9 `authority_generation_binding` — `runtime_dispatch_gate10_eligibility.py` | `gate10_authority_generation_drift:<source>` (restart-safe) | MANDATORY |
| 4 | Gate 10 step 11 | durable `re_binding.verdict == "ALLOW"` and `re_expires_at > authority_current_time` (string compare) | `gate10_re_decision_expired` | DEFENCE-IN-DEPTH (bounded wall-clock backstop) |

`.1R.27` can independently locate each by name. Gate 9 additionally re-derives
the Gate-7 lineage and captures its own S1/S2 authority-generation snapshot; it
records item 7 as a **reference**, not a re-run.

---

## 6. Non-bearer / serialization / restart (REPRC §4, §5, §15)

- `is_gate7_result` still requires `isinstance(candidate, Gate7Result) and
  candidate in _GATE7_RESULTS`; the only insertion point is
  `run_gate7_runtime_enforcement`'s completed-evaluation return path.
- `__reduce__` raises `TypeError` → `pickle.dumps` fails; `copy.copy` /
  `copy.deepcopy` raise or produce a non-member.
- `object.__new__(Gate7Result)` and manual field reconstruction (including
  copying `_seal`) → not a `_GATE7_RESULTS` member → `is_gate7_result` False.
- A known `runtime_enforcement_result_id` alone grants nothing.
- `__init_subclass__` raises → not subclassable.
- Process restart: `_GATE7_RESULTS` is process-local; a prior result is gone;
  Gate 7 must be re-run. No durable Gate-7 store. Model A preserved.
- Duplicate evaluation: deterministic same `decision` /
  `runtime_enforcement_result_id` / `evaluated_input_digest`; a new `!=` object
  each call; no durable "attempt consumed" state.

---

## 7. B1-B / B2-D / Currentness B fidelity (phase prompt §62 / §63 / §64)

**B1-B IMPLEMENTED EXACTLY.**
`git diff 28b8b2b7 HEAD -- src/pcae/core/runtime_invocation_authority_consumption.py`
= empty; `HPAC-AUTHORITY-CONSUMPTION` stays `/2.1`; no `currentness_binding`
durable field; no Gate-9 production change
(`git diff 28b8b2b7 HEAD -- src/pcae/core/runtime_dispatch_gate9.py` = empty);
HPAC-001 stays v2.1.

**B2-D IMPLEMENTED EXACTLY.**
`git diff 28b8b2b7 HEAD -- src/pcae/core/runtime_dispatch_permission.py` = empty;
`Gate6Decision` byte/schema unchanged; no `admission_record_digest` /
`admission_class` field on `Gate7Result` or in any digest; `SupplyChainAdmissionResolver`
not imported by `runtime_dispatch_gate7.py`; no PB-request object exposed to
Gate 7; `_pb_decision_digest` composition byte-unchanged.

**Currentness B IMPLEMENTED EXACTLY.**
`run_gate7_runtime_enforcement` signature byte-unchanged (AST — 5 params, no
`resolver`, no `posture`); no `currentness_binding` slot;
`authority_freshness_digest` retained as the currentness anchor; the four §5
owners each present and named; TTL is a backstop only (does not replace live
revalidation — `.1R.26` suite test 17: within-TTL + stale projection →
`gate7_stale_validated_authority_projection`).

---

## 8. PB consumed, not re-run (REPRC §14)

`runtime_dispatch_gate7.py` imports no `PolicyRegistry`, `_compose`, `POL-*`
rule class, `NarrowLocalCliDispatchEligibilityRule`, `ExecutionDisabledRule`,
`PermissionBroker`, `permission_broker_foundation`, or `pcae.core.policy` (AST +
string scan — `.1R.26` suite test 34, test 61). A trusted Gate-6 `ALLOW` + a
Runtime Enforcement violation (real posture) → `Gate7Result(decision="DENY")`
with a non-empty `matched_no_go_ids` (test 33). Gate 7 consumes the
already-trusted `Gate6Decision` only, via `is_gate6_decision`.

---

## 9. Downstream consumer inventory (REPRC §21; phase prompt §30, §31)

`git grep -lE "Gate7Result|is_gate7_result" -- src/pcae` (independently
re-derived, not trusting the count of three) → `runtime_dispatch_gate7.py`
(defines) + exactly:

```
src/pcae/core/runtime_dispatch_gate8.py             (Gate 8)
src/pcae/core/runtime_dispatch_gate9.py             (Gate 9)
src/pcae/core/runtime_dispatch_gate10_eligibility.py   (Gate 10 pre-effect eligibility)
```

`runtime_dispatch_gate8._gate7_result_digest` imported by
`runtime_dispatch_gate10_eligibility` is an intra-family helper import, not a
fourth consumer.

**Consumer-inventory guard (`.1R.26` suite tests 51–54).**
`AUTHORIZED_GATE7_CONSUMERS` = the exact three production modules; the check is
`hits == AUTHORIZED_GATE7_CONSUMERS` (exact set equality, **no wildcard, no
`fnmatch`, no package prefix, no "contains-at-least"**). A separate exact
9-file test-import allowlist (`AUTHORIZED_GATE7_TEST_IMPORTERS`, matched by a
real-`import`-statement regex, not a path-string grep) with a
`missing == set()` completeness check. An unauthorized production importer → the
exact-equality check fails (test 52 re-derives the orientation).

| Consumer | Reads result? | Validates (`is_gate7_result` + `decision == "ALLOW"`)? | Treats as authority? | Persists / serializes it? | Consumes human authority? | Causes effect? |
|---|---|---|---|---|---|---|
| Gate 8 | yes | yes | **no** — permits Gate 8 evaluation only | no / no (`__reduce__` raises) | no | no |
| Gate 9 | yes | yes | **no** — records the verdict as a reference | only the digest/verdict into `consumption.json` | **yes** — approval + proof + presentation + challenge, atomically, once (its own job) | no |
| Gate 10 | yes | yes | **no** — re-reads the durable binding, re-derives generations | no | no | no |

---

## 10. New findings

### N-16-4-IMPL-1 — non-blocking — disclosed precision correction to REPRC-001 §8 / §8.1

`.1R.25` §8.2 quotes 'RDGO §8 "a future Gate 8 MUST re-run Gate 7"' and §8.4
owner 2 says "Re-runs `run_gate7_runtime_enforcement` over freshly re-resolved
`Gate6Decision` / `Gate5Result`". Primary-source review found: (a) RDGO-001 v3.1
§8 (read verbatim) contains no such clause; (b) `runtime_dispatch_gate8.py`'s
`_gate7_result_digest` docstring explicitly states Gate 8 **never re-runs
Gate 7**. Gate 8 *is* the mandatory stale-rejection owner, but via its own
independent projection re-trust + `revalidate_validated_authority_projection`
(fresh `validate_approval`) → `gate8_stale_validated_authority_projection`, plus
the `_gate7_result_digest` lineage recheck — the accurate reading of the `.1R.25`
mechanism clause "a projection stale at Gate 8 fails the re-run → Gate 8
rejects". REPRC-001 §8 item 3 and §8.1 owner 2 were written to describe this
accurately **before** the production implementation commit; the correction is
disclosed here, in `tasks/DECISIONS.md`, and reflected in the two REPRC SHA-256
values (§3). **Not a BLOCKED condition:** the security property — a projection
stale after Gate 7 is caught before Gate 8 proceeds — is unchanged and needs no
production change outside `runtime_dispatch_gate7.py`.

### N-16-4-1, N-16-4-4 — resolved

The dual-model `expires_at` (N-16-4-1) is implemented as the 300 s ALLOW-branch
backstop (§4.5); the positive `causing_reason_ids` vocabulary (N-16-4-4) is
`GATE7_POSITIVE_CAUSING_REASON_IDS` (§4.6). N-16-4-2 and N-16-4-3 remain
**withdrawn** (B2-D). N-16-4-5 (observational) unchanged.

### N-16-4-IMPL-2 — non-blocking — network-drift fail-closed reason

`.1R.25` §19 case 22 predicts `network_requirement is True` →
`gate7_runtime_target_ineligible`. In byte-current source
`_validate_construction_inputs` is called first (step 4) and itself rejects a
non-`False` `network_requirement` as `gate7_request_currentness_drift:invalid_construction_input_facts`
— an *earlier* fail-closed reason, the correct conservative outcome. The `.1R.26`
suite (test 40) accepts either. No production change.

---

## 11. Whole-tree guard search + exact guard-impact table (phase prompt §42, §43)

**Mandatory whole-`tests/` grep** (`Gate7Result` / `runtime_dispatch_gate7.py` /
`run_gate7_runtime_enforcement` / `_GATE7_RESULTS` / `is_gate7_result` /
`runtime_enforcement_binding` / `RDGO-001 v3.1` / `matched_no_go_ids ==` /
`expires_at`) → 41 files. Impact **re-derived against byte-current source, not
trusting `.1R.25`'s 37-file prediction.**

### 11.1 Guards that pass unchanged

| Guard | File | Why unchanged |
|---|---|---|
| `test_posture_resolved_internally_not_from_caller` / `test_posture_resolved_internally_no_caller_parameter` | `.1R.13.2:475` / `.1R.13.3:362` | Currentness B — signature byte-unchanged; params still the exact 5 |
| `test_negative_result_carries_bound_digests` (`assert r.expires_at == NOW`) | `.1R.13.2:472` | DENY branch keeps `expires_at = authority_current_time` |
| `test_positive_branch_is_pragma_no_cover_and_guarded_by_posture` | `.1R.13.3:424` | the ALLOW-branch `Gate7Result(` line keeps its `# pragma: no cover - unreachable in production`; production stays unreachable |
| `test_gate7result_field_reconstruction_is_not_a_member` (`__slots__` iteration) | `.1R.13.3:500` | tolerant iteration; the 3 new slots don't make a reconstruction a registry member |
| `test_gate7_result_not_caller_constructable` / `test_gate7result_not_caller_constructable` | `.1R.13.2:508` / `.1R.13.3:470` | 3 new required kwonly params → `TypeError` before the seal check (still `pytest.raises(TypeError)`) |
| `test_re_nogo_vocabulary_is_consumed_not_redefined` | `.1R.13.2:490` / `.1R.13.3:389` | no quote-prefixed `RE-NOGO-` literal introduced; `_compose(` absent |
| Gate-7 single-file scope-fence (`assert hits == {"…gate7.py"}`) + all `PHASE_ENTRY_BASELINE .. _1R15_4_SCOPE_END` byte-freezes in `.1R.13.2` / `.1R.13.3` | throughout | fixed historical SHAs — unaffected by HEAD |
| `test_no_downstream_production_consumer_of_gate7_result` / `test_gate7_is_sole_production_owner_…` | `.1R.13.3:157` / `.1R.13.3:149` | no consumer added; changes stay in `runtime_dispatch_gate7.py` |
| `_gate7_result_digest` shape guards in `.1R.13.5` / `.1R.15` / `.1R.15.3` / `.1R.18` / `.1R.20` | throughout | `_gate7_result_digest` composition byte-unchanged; the 3 new slots are not hashed by it |
| RDGO header / §8 text-freeze / `_RDGO_VERSION` / `runtime_enforcement_binding` field-list / `test_hpac_authority_consumption` closed-set | `.1R.15.4` / `.1R.15.5` / `test_hpac_authority_consumption.py` | no RDGO / HPAC / consumption-record change |
| `test_narrow_eligibility_policy_iv` `runtime_dispatch_permission.py` / `Gate6Decision` byte-freezes | `.1R.23` | B2-D — no `runtime_dispatch_permission.py` change |

**Result: the two Gate-7 suites (`.1R.13.2` + `.1R.13.3`, 98 tests) pass
byte-unchanged.** No `def test_` renamed or removed anywhere.

### 11.2 Attributable point-in-time guards reconciled (phase-aware, not weakened)

40 nodes across 13 IV / reconciliation suites — each a "since `<fixed baseline>`
nothing but `X` changed in `src/pcae` / `docs/contracts`" scope fence or byte
freeze that the authorized single-file production change + single new companion
contract legitimately trips. Every reconciliation: (a) widens the authorized set
by **exactly** `{runtime_dispatch_gate7.py}` and/or
`{RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md}` with an explicit `.1R.26`
citation; (b) keeps the subset / exact-equality orientation so any **other**
unauthorized file still fails; (c) adds no wildcard, no `fnmatch`, no package
prefix; (d) renames or removes **no** `def test_`.

| Suite | Guard nodes reconciled | Mechanism |
|---|---|---|
| `.1R.15.2` | `test_earlier_gate_modules_unchanged[runtime_dispatch_gate7.py]` | `runtime_dispatch_gate7.py` removed from the parametrize list (Gate 6 precedent); Gate 5 / 8 stay frozen |
| `.1R.15.5` | `test_gate_5_6_7_8_production_modules_byte_unchanged_since_baseline`, `test_no_unplanned_contract_file_changed_since_task_open` | `_G7` moved from `forbidden` to `allowed`; new `_r126_authorized_contract_delta = {REPRC}` subtracted |
| `.1R.17` | `test_earlier_gates_and_contracts_bytes_unchanged_since_baseline`, `test_production_scope_since_baseline_is_the_single_new_file` | `_SLICE_B_AUTHORIZED_SINCE_BASELINE` += `gate7.py`; `_R122_AUTHORIZED_CONTRACT_CHANGES` += REPRC |
| `.1R.17R` | `test_gate5_permission_gate7_gate8_still_byte_unchanged_since_r153`, `test_no_production_source_changed_since_baseline_except_the_one_r17_file`, `test_no_contract_file_changed_since_baseline` | new `_R126 = {_G7}` unioned into every `allowed`; `_R122_CONTRACTS` += REPRC; `_G7` removed from `forbidden` (Gate 5 / 8 stay) |
| `.1R.17R.1` | 5 nodes (`test_gate_5_perm_7_8_are_byte_unchanged_since_r153_baseline`, `test_gate_5_to_9_and_neighbour_modules_byte_identical_since_baseline`, `test_no_normative_contract_changed_since_baseline`, `test_no_production_source_changed_since_the_r17_head_except_authorized_slice_b`, `test_production_scope_since_baseline_is_the_one_r17_file_plus_authorized_slice_b`) | new `_R126 = {_G7}`; `_R122_CONTRACTS` += REPRC; `runtime_dispatch_gate7.py` removed from the byte-freeze loop |
| `.1R.18` | `test_file_byte_unchanged_since_phase_entry_baseline[runtime_dispatch_gate7.py]`, `test_production_scope_since_baseline_is_exactly_one_new_file`, `test_no_unpushed_divergence_at_verification_entry`, `test_widened_guard_module_passes_at_head[…15_2]` (cascade) | `runtime_dispatch_gate7.py` removed from `_UNCHANGED_SINCE_BASELINE`; `_SLICE_A_PLUS_B_SCOPE` renamed → `_SLICE_A_PLUS_B_PLUS_C_SCOPE` (alias kept) += `gate7.py`; `_authorized` in the divergence check += `gate7.py` + REPRC. **The two `.1R.19R` / `.1R.19R.1` `.1R.18`-not-weakened meta-guards still pass** — `r18_new.count('"*"')`, `count("fnmatch")`, `count("def test_")` all hold, `"runtime_dispatch_gate10_eligibility" in r18_new` holds |
| `.1R.19` | `test_gate5_through_gate9_byte_unchanged`, `test_no_contract_file_changed` | `_POST_1R19_AUTHORIZED_SURFACE` += `gate7.py`; `_r122_contracts` += REPRC |
| `.1R.19R` | `test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap`, `test_no_contract_change_since_r20_head` | `_POST_1R19R_AUTHORIZED` += `gate7.py`; `_r122_contracts` += REPRC |
| `.1R.19R.1` | `test_n20_4_lifecycle_diff_since_r20_head_is_only_the_remap`, `test_no_normative_contract_change_since_baseline`, `test_no_slice_a_gate_or_item9_drift_since_r19_head[gate7]`, `test_production_diff_since_r19_head_is_exactly_the_n20_4_remap` | new `_R126 = {gate7.py}` unioned into the `:(exclude)` list and the `changed - _R122 - _R126` checks; `_R122_CONTRACTS` += REPRC; `runtime_dispatch_gate7.py` removed from the drift parametrize list |
| `.1R.20` | `test_slice_b_production_scope_since_baseline_is_exactly_the_authorized_set`, `test_slice_a_and_closed_gate_modules_are_byte_unchanged_since_baseline`, `test_no_normative_contract_changed_since_baseline` | `_R122_AUTHORIZED` += `gate7.py`; `runtime_dispatch_gate7.py` removed from the byte-freeze loop; `_r122_contracts` += REPRC |
| `.1R.22R` | `test_first_external_effect_absent`, `test_n23_2_deferred_no_contract_change_by_this_phase`, `test_no_normative_contract_diff_since_baseline_beyond_the_authorized_set`, `test_no_production_source_diff_by_this_phase`, `test_production_scope_since_baseline_is_exactly_the_two_authorized_files` + (would-be) `test_untouched_meta_and_iv_guards_…` | `R22R_ENTRY..HEAD` checks carve `{gate7.py}` / `{REPRC}`; `test_first_external_effect_absent` re-scoped to "no effect-primitive token in any added `src/pcae` line" (stronger intent-preserving check); `.1R.18` / `.1R.19R` / `.1R.19R.1` moved from `_UNTOUCHED_META_AND_IV_SUITES` into a new `_R126_RECONCILED_META_AND_IV_SUITES` with a dedicated `test_r126_reconciled_meta_and_iv_suites_are_widened_not_weakened` not-weakened guard |
| `.1R.22R.1` | `test_3_production_scope_since_baseline_is_exactly_the_two_authorized_files`, `test_38_n23_2_contract_wording_left_untouched_since_r23_head`, `test_39_no_production_or_contract_diff_since_r22r1_entry`, `test_29_meta_guard_inventory_independently_discovered_and_run` (cascade) | `BASELINE..HEAD` / `R23_HEAD..HEAD` checks carve `{gate7.py}` / `{REPRC}`; test_29's sub-pytest (`.1R.20` / `.1R.18` / `.1R.19R` / `.1R.15.3`) recovers transitively once those are reconciled |
| `.1R.23` | `test_only_two_production_files_changed_since_baseline`, `test_only_authorized_contract_files_changed_since_baseline`, `test_gate7_and_gate9_and_gate10_modules_byte_unchanged` | `changed -= {gate7.py}` / `changed -= {REPRC}` before the exact-equality assert; `runtime_dispatch_gate7.py` removed from the byte-freeze loop (Gate 5 / 8 / 9 / 10 stay) |

`.1R.13.3` / `.1R.15.3` remain **byte-unchanged** by this phase.

### 11.3 Meta-guard results

- `.1R.19R::test_meta_guards_are_byte_unchanged_since_r20_head` — PASS (`.1R.15.3`
  byte-frozen; `.1R.18` not weakened: `"*"` / `fnmatch` / `def test_` counts hold,
  eligibility module still named).
- `.1R.19R.1::test_meta_guards_byte_unchanged_since_r20_head` — PASS (same checks).
- `.1R.19R.1::test_meta_guard_passes_at_head[*]` — PASS.
- `.1R.22R::test_untouched_meta_and_iv_guards_are_byte_unchanged_by_this_reconciliation`
  — PASS (its `_UNTOUCHED_META_AND_IV_SUITES` now lists only genuinely untouched
  suites; the three `.1R.26`-reconciled meta/IV suites are in the new
  `_R126_RECONCILED_META_AND_IV_SUITES` with the new not-weakened guard).
- `.1R.22R.1::test_28_all_22_nodes_pass_at_head` / `::test_29_meta_guard_inventory…`
  — PASS (transitive recovery).

---

## 12. Defensive test matrix — `tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py`

**78 tests, all green** (standalone `pytest -q`). Groups A–O map the `.1R.25` §19
matrix (≥ 48 cases) plus the REPRC-001 §22 contract-production equivalence
obligation:

- **A (01–04)** — synthetic ALLOW reachable + trusted; production positive
  unreachable (real posture → DENY); real `resolve_runtime_enforcement_posture()`
  reports `unavailable` + the four base no-gos; positive branch still
  `# pragma: no cover` in source.
- **B (05–09)** — `reprc_schema_version` on every result; result-id determinism;
  id changes on any security field; id binds `reprc_schema_version`; id excludes
  `expires_at` / `evaluated_at`.
- **C (10–11)** — `idempotency_key` promoted to an explicit slot; a changed
  idempotency key changes `evaluated_input_digest` and the result id.
- **D (12–17)** — ALLOW `expires_at` = `evaluated_at + 300 s`; DENY `expires_at`
  = `evaluated_at`; TTL constant frozen at 300; fresh positive not expired at
  Gate 10 within the window / expired past it; malformed
  `authority_current_time` → `gate7_internal_error_fail_closed`; TTL never
  rescues a stale projection.
- **E (18–21)** — signature unchanged (AST, no `resolver` / `posture` param);
  no `currentness_binding` slot / key / assignment; exactly three additive slots
  since `28b8b2b7` (via `git show 28b8b2b7:…` + `ast`); the four named
  stale-rejection owners locatable in source.
- **F (22–28)** — immutability (`setattr` / `delattr` raise); not
  caller-constructable even with all new kwargs; `object.__new__` /
  reconstruction not a member; not serializable (`pickle` / `deepcopy` / `copy`);
  a known result id grants nothing; not subclassable; sealed constructor rejects
  an unknown `reprc_schema_version`.
- **G (29–31)** — result from a previous process not a member; duplicate
  evaluation idempotent (same id, `!=` objects); no `consumption.json` written.
- **H (32–35)** — non-`ALLOW` PB decision rejected before the posture resolver is
  consulted (`AssertionError` if consulted); PB `ALLOW` + RE violation → DENY;
  Gate 7 imports no PB-policy symbol (AST); forged `Gate6Decision` rejected.
- **I (36–41)** — changed invocation / attempt / subject-scope binding rejected;
  changed runtime target changes `evaluated_input_digest`; `network_requirement
  is True` fails closed (either reason — N-16-4-IMPL-2); changed PB decision
  digest changes the result id.
- **J (42–46)** — Gate 8 hard-stops a negative result; Gate 9 sole consumption
  owner (Gate 7 writes nothing — AST); Gate 10 capability re-read independent;
  N-16-5 wall (real `validate_approval` → `proj is None`); runtime state
  unchanged after a positive eval.
- **K (47–48)** — positive result carries the non-empty vocabulary incl.
  `gate7_synthetic_evaluation_path`; negative reason set unchanged.
- **L (49–50)** — no effect-primitive call syntax; module imports nothing
  effectful (AST).
- **M (51–54)** — exact production consumer inventory (`==`, no wildcard);
  unauthorized extra consumer would fail; exact finite test-import allowlist
  with a completeness check; allowlists are literal paths, no glob.
- **N (55–59)** — production diff since `28b8b2b7` is exactly `gate7.py`;
  contract diff is exactly REPRC; 8 downstream / sibling modules byte-unchanged;
  6 frozen contracts byte-unchanged; `pcae runtime inspect` constants unchanged.
- **O (60–62)** — REPRC-001 frozen at v1.0; the equivalence map (10 clause →
  source checks); no RDGO / HPAC / PB contract **file** in the diff.

---

## 13. Static proofs (phase prompt §48, §49)

- **PB-rerun AST proof** — `runtime_dispatch_gate7.py` imports/uses no
  `PolicyRegistry`, `_compose`, `POL-*` rule class,
  `NarrowLocalCliDispatchEligibilityRule`, `ExecutionDisabledRule`,
  `PermissionBroker`, `permission_broker_foundation`, `pcae.core.policy`.
- **No-effect static proof** — no `adapter.dispatch(`, `.dispatch(`, `Popen(`,
  `subprocess.`, `os.system(`, `os.execv`, `os.spawn`, `socket.socket(`,
  `pty.spawn`, `.connect(`, `webauthn`, `ctap2`; no import of `subprocess`,
  `socket`, `requests`, `httpx`, `urllib`, `http`, `asyncio`, `multiprocessing`,
  `ctypes`, `pty`, `fcntl`, `signal`, `ssl`, `selectors`, `runtime_dispatch_gate8/9/10`,
  `shell_gate`, `runtime_invocation_authority_consumption`, `runtime_adapter`.
  The only new import is `from datetime import datetime, timedelta`.

---

## 14. Targeted suites + broad guard sweep + fixed-SHA A/B (phase prompt §55, §56, §57)

**Targeted deterministic no-xdist run** (24-file affected set + the new suite):
the two Gate-7 suites; the Gate-8/9/10 coordinator + IV suites; the Slice-B
suites; the RDGO / HPAC contract-normalization suites;
`test_hpac_authority_consumption.py`; `test_narrow_eligibility_policy_iv`; the
`.1R.19R` / `.1R.19R.1` / `.1R.22R` / `.1R.22R.1` meta-guards; the Gate-5 / Gate-6
coordinator suites.

**Broad whole-`tests/` grep sweep** — 41 files match the needles; the 17 beyond
the targeted set (HPAC / Gate-5 / Gate-6 / contract-verification suites) run
green at HEAD.

**Fixed-SHA A/B** — baseline `git worktree` at `28b8b2b70dcd4642dc45d4a3961a5218402c3c7c`,
candidate at HEAD, deterministic `-p no:randomly`, no xdist, identical file set:

| | Baseline (`28b8b2b7`) | Candidate (HEAD) |
|---|---|---|
| failed | 8 | 5 |
| passed | 1330 | 1409 |

- **CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0.**
- **UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.**
- Candidate-only nodes during iteration: 1 — this phase's own new-suite
  assertion `test_53_test_importers_of_gate7_symbols_are_a_known_finite_set`
  (its `git grep` initially matched scope-fence *comment* strings; fixed to a
  real-`import`-statement regex) — resolved before finalization.
- Baseline-common (pre-existing, reproduced at `28b8b2b7`, **left unrepaired —
  out of scope**): `.1R.19R.1::test_no_test_weakening_in_the_r19r_diff`
  (self-trips on a `.1R.23`-era `@pytest.mark.skipif` — the disclosed N-22R1-1
  finding), `.1R.22R::test_no_test_weakening_in_the_r22r_diff`,
  `.1R.22R::test_n16_4_to_7_untouched`,
  `.1R.22R::test_no_older_phase_doc_or_contract_was_rewritten_to_imply_v3_0_existed_earlier`,
  `.1R.22R.1::test_27_no_wildcard_introduced_in_tests_diff_since_r23_head`. Three
  further baseline flakies (`.1R.17R::test_original_r17_immutable_phase_report_artifacts_untouched`,
  `.1R.22R::test_historical_22_node_set_reproduces_at_the_fixed_shas`,
  `.1R.22R::test_original_r22_completion_artifacts_preserved_unrewritten`) do not
  reproduce in the candidate environment.

**`fast_green` for finalization metadata:** the targeted affected suites run
green (0 failed) after reconciliation; the 5 remaining failures are
baseline-common and reported deselected.

---

## 15. Byte-scope verification (phase prompt §59, §60, §61)

- `git diff --name-only 28b8b2b7 HEAD -- src/pcae` → **exactly**
  `src/pcae/core/runtime_dispatch_gate7.py`.
- `git diff --name-only 28b8b2b7 HEAD -- docs/contracts` → **exactly**
  `docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md`.
- Byte-unchanged (`git diff 28b8b2b7 HEAD -- <path>` empty):
  `runtime_dispatch_permission.py`, `runtime_dispatch_gate8.py`,
  `runtime_dispatch_gate9.py`, `runtime_dispatch_gate10_eligibility.py`,
  `runtime_invocation_authority_consumption.py`, `runtime_authority.py`,
  `runtime_enforcement_safety_authorization.py`, `runtime_introspection.py`;
  RDGO-001, HPAC-001, PBRD / PBNDE / PBPA / RPAC / RIHAC / RIASC contracts, the
  RE No-Go Registry, `V0_2_EXECUTION_READINESS_NO_GO_GATES.md`.

---

## 16. Runtime / first-effect verdict (phase prompt §50, §54)

```
Runtime status:            not_implemented
Runtime state:             Observed
Execution capability:      unavailable
Maximum plugin capability: observe
Registry status:           empty
Plugin count:              0
Capability count:          0
First external effect:     ABSENT
Execution enabled:         NO
```

`pcae runtime inspect` byte-identical before and after. No `adapter.dispatch()`
call site anywhere in `src/pcae`. `RuntimeRegistry` empty. No `runtime_inspect`
JSON contract change.

---

## 17. Disposition

| Item | State |
|---|---|
| N-16-4 | **IMPLEMENTED — INDEPENDENT VERIFICATION PENDING `.1R.27`.** NOT CLOSED. |
| REPRC-001 v1.0 | **AUTHORED / FROZEN — IV PENDING.** |
| `Gate7Result(decision="ALLOW")` | **SYNTHETIC TEST PATH REACHABLE; PRODUCTION PATH UNREACHABLE.** |
| B-1 / B-2 / B-3 | **B1-B / B2-D / Currentness B — IMPLEMENTED EXACTLY.** |
| N-16-5 / N-16-6 / N-16-7 | OPEN — not begun. N-16-4 before N-16-5. |
| Slice C / Slice D | no phase ID. |
| First external effect | ABSENT. |
| Runtime | Observed / observe / unavailable. |
| N-23-2 | INFO / DEFERRED NORMALIZATION DEBT — carried, not dropped. |
| N-23-1 | INFO — carried. |
| N-16-4-IMPL-1 / IMPL-2 | non-blocking findings, disclosed (§10). |
| `.3` delegated finalization / commit / push | **UNAUTHORIZED** — preserved. |

---

## 18. Recommended next phase (phase prompt §66)

`149O.20L.7O.3W.1R.2B.1R.1.1R.27` — **Independent Verification of the N-16-4
Runtime Enforcement Gate.** RE-DERIVE (do not trust this phase's report or
suite) the 14-point proof of `.1R.25` §20: Currentness B implemented exactly
(signature unchanged by AST, no `currentness_binding` slot, the four named
owners present); stale `Gate7Result` rejected by the named owner; non-bearer /
non-transferable; Gate6→7 route non-forgeable; durable-consumption compatibility
(`HPAC-AUTHORITY-CONSUMPTION/2.1` byte-unchanged); contract versions correct
(REPRC-001 v1.0 text ↔ implemented behaviour, no RDGO/HPAC bump); PB consumed
not re-run; no-go semantics preserved; Gate 8/9/10 still required; runtime
capability independent; no effect reachable; **guards fully reconciled via an
independent broad fixed-SHA A/B — do not trust `.1R.26`'s enumeration; disclose
any undisclosed attributable guard regression as a BLOCKER referred to a
`.1R.26R` reconciliation (the `.1R.18` / `.1R.20` / `.1R.23` precedent)**;
REPRC-001 v1.0 contract-production equivalence map; `.1R.25` freeze fidelity.

Then N-16-5 → N-16-6 → N-16-7 (strictly last), each its own authorized
implementation + IV pair. **Do not begin `.1R.27`, N-16-5/6/7, Slice C, the
first external effect, or execution enablement.**

---

## 19. `.3` governance incident — preserved

```
DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
```

Only the primary human-authorized operator holds `.1R.26` lifecycle authority.
No delegated worker committed, finalized, or pushed. No raw `git commit` /
`git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass
— governed `pcae` lifecycle only.

---

## 20. No-go confirmations

- No `src/pcae` file other than `runtime_dispatch_gate7.py` was created,
  modified, or deleted; `runtime_dispatch_permission.py`,
  `runtime_dispatch_gate8.py`, `runtime_dispatch_gate9.py`,
  `runtime_dispatch_gate10_eligibility.py`,
  `runtime_invocation_authority_consumption.py`, `runtime_authority.py` are
  byte-identical to `28b8b2b7`.
- No normative contract other than the NEW
  `docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md` was created
  or edited; RDGO-001, HPAC-001, `HPAC-AUTHORITY-CONSUMPTION`, PBRD-001,
  PBNDE-001, PBPA-001, RPAC-001, RIHAC-001, RIASC-001, the RE No-Go Registry,
  `V0_2_EXECUTION_READINESS_NO_GO_GATES.md` are all byte-unchanged.
- No `run_gate7_runtime_enforcement` signature change; no `currentness_binding`
  slot; no `authority_generation_resolver` parameter; no admission binding at
  Gate 7; no PB-request object exposed to Gate 7.
- No RDGO / HPAC / PBRD / PBNDE / PBPA / RPAC / RE-No-Go / NG-025 version bump,
  forced or overridden; the only version movement is REPRC-001 v1.0 (initial
  freeze). No MAJOR. No MINOR.
- The positive Gate-7 production path was NOT enabled; production
  `run_gate7_runtime_enforcement(...)` still returns `Gate7Result(decision="DENY")`
  or `(None, reasons)` for every currently constructible real request; the
  positive branch remains `# pragma: no cover - unreachable in production`.
- No execution was enabled; runtime remains `not_implemented / Observed /
  observe / unavailable`; 0 plugins / 0 capabilities; `pcae runtime inspect`
  byte-unchanged.
- No runtime capability was elevated or promoted; no `Observed → Approved /
  Executable` transition; N-16-7 untouched and last.
- No Slice C was implemented; no `adapter.dispatch(` call site exists anywhere
  in `src/pcae`; Slice C / Slice D keep no phase ID.
- No N-16-5 / N-16-6 / N-16-7 work was begun.
- No adapter (mock or real) was registered, implemented, activated, or called;
  `RuntimeRegistry` remains empty; no supply-chain admission store or resolver
  was created or called.
- No credential, secret resolver, FIDO2 / WebAuthn / CTAP, or protected
  human-approval UI was accessed, created, or referenced; deterministic
  authentication remains NON_REAL.
- No approval, proof, presentation, challenge, or nonce was consumed on any
  path; no `consumption.json` was written anywhere.
- No subprocess, process spawn, `os.system` / `popen` / `spawn` / `exec*`,
  `pty`, provider SDK, HTTP client, socket, or network path was created or
  invoked by the touched module; the only subprocesses used in this phase were
  read-only `git` history inspection, `pytest` runs, and `pcae` governance CLI
  checks.
- No third-party system, unrelated account, provider API, external network, or
  deployment target was accessed or mutated.
- No test was weakened: no `def test_` renamed or removed in any suite; no
  `@pytest.mark.skip` / `xfail` / `skipif` decorator added; no wildcard,
  `fnmatch`, or package prefix introduced into any consumer / scope-fence
  allowlist; every reconciled guard still rejects any other unauthorized file.
- No reopening of a closed gate boundary (Gate 5, 6, 7, 8, 9, 10 pre-effect),
  the Slice-A / Slice-B verdicts, or the N-16-3 closure.
- No human approval was treated as a policy or enforcement override.
- No raw `git commit` / `git push`, no `--no-verify`, no force push, no history
  rewrite, no hook bypass; governed `pcae` lifecycle only.
- No delegated worker committed, finalized, or pushed; `DELEGATED .3
  FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` is preserved.
- No STOP or BLOCKED condition was reached; every valid early-STOP condition in
  the phase prompt was checked against the implementation and none applies.
- No "Remaining" section is presented; all authorized `.1R.26` work is complete.

---

## 21. Erratum — `149O.20L.7O.3W.1R.2B.1R.1.1R.26R` (provenance-preserving, additive)

*This section is appended after the fact. Nothing above this line has been
edited or rewritten; the original `.1R.26` claims and evidence stand exactly
as authored.*

**Original claim (§11.2 / §17 above, as authored):** "40 attributable
point-in-time guard nodes across 13 IV / reconciliation suites... 0 unexplained
attributable functional regressions."

**`.1R.27` discovery.** `149O.20L.7O.3W.1R.2B.1R.1.1R.27`'s independent
verification (RE-DERIVE discipline) reproduced its own broad fixed-SHA A/B
independently and found **one additional undisclosed `.1R.26`-attributable
stale point-in-time scope-fence guard** that the 40-node table above did not
include:

`tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py::test_runtime_posture_unchanged_and_no_new_first_effect_call_site`

— PASSES at pre-`.1R.26` baseline `28b8b2b7`; FAILS at `.1R.26` finalized
head `9d28f7ef`; fails only because its `.1R.22`-baseline-rooted (`8603fe6a`)
exact `src/pcae` current-state file-set assertion,
`{permission_broker_foundation.py, runtime_dispatch_permission.py}`, was
never widened to include `.1R.26`'s authorized single-file addition
`runtime_dispatch_gate7.py`. `.1R.27` classified this as an explicit BLOCKED
condition ("an undisclosed `.1R.26`-attributable guard regression is found")
and referred it to a `.1R.26R` reconciliation per this document's own §18
precedent guidance, rather than repairing it itself (out of IV-only scope).

**Corrected historical count.** `149O.20L.7O.3W.1R.2B.1R.1.1R.26R` freshly
re-derived the true attributable count for this guard class via an
independent fixed-SHA A/B (`28b8b2b7` baseline vs. `9d28f7ef` candidate,
deterministic, no xdist, over every test file in the repo matching an exact
`src/pcae` name-only-diff / current-state-freeze pattern), then via a direct
primary-operator run of the full Gate-7-referencing suite family: the true count is
**42** (the 40 originally disclosed and reconciled in `.1R.26`,
plus 2 more — this node, and
`tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py::test_53_test_importers_of_gate7_symbols_are_a_known_finite_set`,
whose finite `AUTHORIZED_GATE7_TEST_IMPORTERS` allowlist did not admit the
later-authorized `.1R.27` independent-verification suite — same mechanical
class, both missed at `.1R.26` time and reconciled in `.1R.26R`). No further
same-class stale guard was found. One unrelated pre-existing finding was
also surfaced and independently confirmed present at the unmodified
`9d28f7ef` head (zero `.1R.26R` changes applied):
`tests/test_gate6_permission_broker_production_consumption_integration_independent_verification_3w1r2b1r1_1r13.py::test_no_downstream_production_consumer_of_gate6_symbols`
fails because `runtime_dispatch_gate10_eligibility.py` references Gate-6
symbols outside that guard's frozen allowlist — this is **not**
`.1R.26`-attributable (unrelated to `runtime_dispatch_gate7.py`, pre-dates
`.1R.26`) and was left unrepaired, out of `.1R.26R`'s scope.

**Classification.** Non-behavioural verification-evidence defect only. No
production defect. No contract defect. The guard's other two assertions
(runtime posture unchanged; no new `adapter.dispatch(` call site) were never
false and remained intact throughout — the missed widening never permitted
an actual regression to go undetected; it only caused this one guard's own
scope-fence to trip on legitimate, already-disclosed `.1R.26` change.

**Repair.** `149O.20L.7O.3W.1R.2B.1R.1.1R.26R` — widened the guard's
exact-equality set by exactly `{runtime_dispatch_gate7.py}`, preserving
exact-set semantics (no wildcard, no `fnmatch`, no prefix, no
subset/superset tolerance) and every other assertion in the function,
unchanged. See
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_N_16_4_SCOPE_FENCE_AND_VERIFICATION_EVIDENCE_RECONCILIATION.md`
for the full reconciliation record.

**N-16-4 implementation semantics: UNCHANGED.** This erratum does not alter
any verdict in §17 above other than the guard-count correction stated here;
N-16-4 remains **not** CLOSED pending a fresh/restarted `.1R.27`.
