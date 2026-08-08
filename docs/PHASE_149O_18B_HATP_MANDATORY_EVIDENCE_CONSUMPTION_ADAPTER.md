# Phase 149O.18B — HATP Mandatory Evidence Consumption Adapter

**Phase type:** BOUNDED PRODUCTION IMPLEMENTATION (Wave B of the 149O.17
implementation plan).

**Subject:** `HMRC-001 v1.0` —
`docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`, status
`VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS` (149O.16), unchanged.

---

## 1. Baseline

Confirmed at phase start by direct command execution: repository clean;
`origin/main..HEAD: 0`; `pcae health` healthy; `pcae check` passed;
`pcae status coherence` coherent; `pcae doctor task-memory` warnings
(7 pre-existing `tasks/done/` vs `tasks/DONE.md` entries, predating this
phase, unrelated); `pcae push check` clean (`nothing_to_push`);
`pcae runtime inspect` `Observed / observe / unavailable`, Permission
Broker `execution_unavailable`; `pcae notify status` Telegram
configured/enabled/ready; `pcae phase-report show --latest` /
`pcae phase-report reconcile --phase-id 149O.18A` confirmed 149O.18A
`status: completed`, report `complete`, pushed,
`origin/main..HEAD: 0`, reconciliation `status: reconciled` (mutation:
none), recommended next phase confirmed as 149O.18B.

149O.18A verdict (restated, unchanged by this phase): **HATP MANDATORY
CUTOVER STATE FOUNDATION: IMPLEMENTED — READY FOR 149O.18B.** HMRC-001
v1.0 byte-unchanged. HATP production **NOT READY**. Runtime `Observed /
observe / unavailable`.

---

## 2. 18B Requirement Subset (from the 149O.17 traceability table)

Primary owner `CONS` (`src/pcae/core/hatp_rollback_consumption.py`):
HMRC-REQ-006 (partial, vocabulary discipline), 007 (partial, semantic
walls), 010, 013–030 (adapter portion), 073 (partial, no caller-supplied
authority), 075–079.

| Req | Normative meaning (compressed) | Failure/behavior | Test owner |
|---|---|---|---|
| 010 | `evidence_id` domain = HSCE-REQ-056, rejected pre-path-construction | Fail closed (`ValueError` before any I/O) | `HATPRollbackConsumptionRequest.__post_init__` + `test_invalid_evidence_id_domain_rejected_before_any_store_access` |
| 013 | Evidence ID has no authority meaning alone | Structural | `test_missing_evidence_fails_closed` et al. |
| 014 | No implicit evidence selection | No such lookup exists | `test_no_latest_or_glob_lookup_method_exists`, `test_two_valid_evidence_ids_each_consumes_only_its_own` |
| 015 | Sole loader `HATPEvidenceStore.load`; no arbitrary path/parse/caller envelope | Structural | `_load_envelope_proof_and_assertion` — no alternate loader exists |
| 016 | Canonical loaded object exactly `HATPSignedEvidenceEnvelope` | Structural | same |
| 017 | Full 7-step consumption chain, evaluated fresh every attempt | Fail closed at any step | `_internal_consume_hatp_rollback_evidence` |
| 018 | 13-member fail-closed load/verification-status enumeration | Fail closed, every member | reused unmodified `HATPVerificationStatus`; load failures collapse to `MISSING` via `hatp_proof=None`, never a new parallel enum |
| 020 | Unknown/future verification status always fails | Fail closed | reused unmodified `verify_hatp_proof` |
| 021 | `approval_present` derived exclusively by existing RAE+HATP+substrate 3-term AND | Fail closed on any internal error | `resolve_rollback_approval_evidence_with_hatp` reused unmodified |
| 022 | No duplication of RAE/digest/operation/freshness/revocation logic | Structural | no local reimplementation anywhere in the new module |
| 023 | `approval_present` stays local to adapter/PB construction | Structural | never exposed on `HATPRollbackConsumptionResult` |
| 024 | PB remains sole permission-decision owner | Structural | `PermissionBroker().evaluate()` is the only decision source |
| 025 | PB request reuses existing shape | n/a — shape reuse | `build_permission_broker_request(action_type=ACTION_ROLLBACK, execution_class=EXECUTION_CLASS_ROLLBACK, requested_component="COMP-008", ...)` |
| 029 (MC-14) | Effect-truthful PB requirement | Fail closed (current POL-005 denies) | `evaluate_for_real_effect`/`evaluate_for_advisory`, `TestSimulationOnlyTruthfulness` |
| 073 (partial) | No caller-supplied approval boolean/PB decision/provider override on the adapter | Structurally absent from signatures | `TestProductionDependencyClosure`, `TestNoRawHookPublicInputs` |
| 075 | Result shape: `evidence_id`, `hatp_status`, `pb_decision`, `reasons`; `approval_present` not generically exposed | n/a — type design | `HATPRollbackConsumptionResult`, `test_result_has_exactly_hmrc_req_075_fields` |
| 076 | No Consumption Attempt result persisted/reused | Fail closed on repeat if state changed | `test_repeat_call_reevaluates_after_evidence_deleted`/`_after_binding_revoked` |
| 077 | Evidence deleted/modified/revoked after prior success ⇒ later attempt fails/re-verifies | Fail closed on retry | same |
| 078 | Two valid evidence IDs ⇒ caller must explicitly choose | Rejected (no selection) | `test_two_valid_evidence_ids_each_consumes_only_its_own` |
| 079 | Pre-cutover evidence usable post-cutover if still fresh/valid | n/a — allowed if fresh | adapter is mode-agnostic by construction (no cutover import) |

**MC subset:** MC-1, MC-2, MC-3, MC-8, MC-9, MC-10, MC-14 (`evaluate_for_
real_effect` always `simulation_only=False`, structurally, never
caller-supplied).

**Attack subset covered by this phase's test suite** (`tests/
test_hatp_rollback_consumption.py`): 1–3 (load errors), 4–8 (wrong
operation/cross-family/wrong repo/deployment), 12–13/25–28 (no
cache/repeat-attempt), 16–19 (raw-hook/override rejection), 29/45 (no
implicit selection), 34 (partial — simulation-only truthfulness), 35
(mode-agnostic), 36–38 (wrong job/PER/ecp), 43 (wrong repository/
deployment). Attacks 20–24, 30–33, 39–42, 44 belong to Waves A/C/D/E/F
and are not owned by this phase.

---

## 3. Production Module / API Design

**New module (only one, as planned):** `src/pcae/core/hatp_rollback_
consumption.py`.

- **Request type:** `HATPRollbackConsumptionRequest(evidence_id: str,
  operation_context: RollbackApprovalContext)` — `operation_context` is
  exactly one of the two existing, unmodified RAE context types
  (`Ag3RollbackApprovalContext`/`Ag5RollbackApprovalContext`); the site
  (AG3/AG5) is structurally determined by which type is supplied — an
  unrecognized type is rejected in `__post_init__`, before any I/O.
  `evidence_id` is domain-checked (HSCE-REQ-056) in the same
  `__post_init__`, also before any I/O.
- **Result type:** `HATPRollbackConsumptionResult(evidence_id: str,
  hatp_status: HATPVerificationStatus, pb_decision: str, reasons:
  Tuple[str, ...])` — exactly HMRC-REQ-075's four fields. No
  `approval_present`, `executed`, `rollback_succeeded`, or
  `capability_available` field.
- **Canonical load and consumption chain** (`_internal_consume_hatp_
  rollback_evidence`, the fully-parameterized private test seam):
  1. `HATPEvidenceStore.load(evidence_id)` (unmodified) — a load/parse
     failure is represented internally as `hatp_proof=None` rather than
     a second, parallel failure branch; `verify_hatp_proof` (unmodified)
     already maps `None` to `HATPVerificationStatus.MISSING`
     ("no_proof_supplied") by construction.
  2. **RAE lookup key derivation (an explicit design decision, not in
     the plan's own prose, resolved here for the first time):**
     `HATPEvidenceStore` (keyed by the caller's HSCE `evidence_id`, a
     64-hex digest of the proof's own canonical payload) and
     `RollbackApprovalEvidenceStore` (keyed by the RAE Binding's own,
     independently-generated `rae-<uuid>`-shaped `evidence_id`) are two
     separately-keyed stores (HSCE-REQ-007) — the caller's single HSCE
     `evidence_id` cannot itself double as the RAE lookup key (this
     would be circular: the HSCE `evidence_id` is a digest that already
     depends on the proof's `binding_id` field, and the RAE key would
     need to equal that not-yet-computed digest). Instead, the *loaded
     proof's own* `binding_id` field — which already points at the RAE
     Binding it self-asserts to attest to (HATP-001's own field) — is
     used as the RAE lookup key. `verify_hatp_proof`'s existing,
     unmodified `_operation_matches` check independently re-derives the
     *expected* `binding_id` from whichever RAE Binding is actually
     resolved at that key and compares it back against this same proof
     field, so this is never a caller-controllable or self-certifying
     pointer — a forged/mismatched `binding_id` still fails closed via
     the existing engine. On a load failure (no proof), the caller's own
     `evidence_id` is reused as a harmless placeholder RAE lookup key,
     since `hatp_proof=None` already forces `MISSING` regardless of
     whatever that placeholder resolves to.
  3. `resolve_rollback_approval_evidence_with_hatp(operation_context,
     rae_evidence_id, hatp_proof=..., hatp_evidence=..., hatp_provider=...,
     hatp_trust_store=..., ...)` (RAE-001/HATP-001, existing, unmodified)
     — reuses the exact three-term conjunction
     (`_derive_hatp_gated_approval_present`).
  4. `build_permission_broker_request(action_type=ACTION_ROLLBACK,
     execution_class=EXECUTION_CLASS_ROLLBACK,
     requested_component="COMP-008", evidence_available=True,
     approval_present=<derived>, simulation_only=<caller-selected via
     which named function was called>)`.
  5. `PermissionBroker().evaluate(request)` → `ALLOW | DENY |
     HUMAN_REVIEW`.
  6. `reasons` assembled from every distinct diagnostic layer (load
     error / RAE result / RAE diagnostic / HATP reasons / substrate
     readiness reasons / PB decision reason) — HMRC-001 §10's 5-layer
     diagnostic-separation discipline, preserved even though the closed-
     vocabulary `hatp_status`/`pb_decision` fields alone cannot carry all
     of it (e.g. a caller-context/RAE-Binding mismatch surfaces only in
     `reasons`, since it does not change `hatp_status`, which is a
     per-proof, not per-attempt, verdict).
  7. return the typed result — no effect performed here.
- **Two production entrypoints, differing only in a hardcoded
  `simulation_only`:**
  - `evaluate_for_real_effect(request, *, root)` — always
    `simulation_only=False`. Not called by any real production caller
    yet (149O.18C/D wire AG3/AG5 to it).
  - `evaluate_for_advisory(request, *, root)` — always
    `simulation_only=True`. Exists so this module's own test suite (and
    a possible future AG5 `--dry-run` role) has a truthful entrypoint;
    the existing pre-cutover advisory path continues to use `hatp_ag_
    authority.py` unchanged, not this module.
  - Neither entrypoint accepts `simulation_only`, `hatp_proof`,
    `hatp_evidence`, `provider`, `trust_store`, `approval_present`, or
    any other authority-bearing parameter — signature is exactly
    `(request, root)` on both (F-2 closure pattern, mirrors `hatp_ag_
    authority.py:124-125`).
- **Production dependency closure:** both entrypoints resolve
  `HATPTrustStore.production()`, the production hardware provider, and
  repository/deployment identity internally
  (`_resolve_production_dependencies`) — the only call site of
  `HATPTrustStore.production()` in the module, confirmed by an AST-based
  test. The private `_internal_consume_hatp_rollback_evidence` seam
  accepts every dependency explicitly for deterministic unit tests.

---

## 4. No-Go Confirmations

- **Only `src/pcae/core/hatp_rollback_consumption.py` was added to
  `src/pcae/`** this phase — `git diff --name-only b0a71e36..HEAD --
  src/pcae/` shows exactly that one file.
- `hatp_mandatory_cutover.py` (149O.18A) remains **byte-unchanged**
  (`git diff --stat` empty) and is **not imported** by the new module
  (confirmed by AST import inspection) — the adapter is mode-agnostic by
  construction; 149O.18C/D will decide when to invoke it based on fresh
  cutover-mode resolution.
- `hatp_evidence_store.py`, `hatp_signed_evidence.py`, `hatp_ag_
  authority.py`, `human_approval_trusted_provenance.py`, `rollback_
  approval_evidence.py`, `permission_broker.py`/`permission_broker_
  foundation.py`, `hatp_bootstrap.py`, `agent.py`, `commands/agent.py`,
  `cli.py` all remain **byte-unchanged** this phase.
- No HMRC-001, HSCE-001, HATP-001, RAE-001, RWMPC-001, PBPA-001, or
  PBPC-001 contract was modified — all seven remain byte-unchanged
  (`git diff --stat` empty for each).
- No AG3/AG5 effect-boundary integration was implemented; no
  `--hatp-evidence-id` CLI plumbing was implemented; no legacy rollback
  authority behavior changed; no Permission Broker behavior changed; no
  POL-005 change was made; no COMP-002 capability was implemented.
- No rollback effect was performed by this module — `_run_git_revert`,
  `execute_rollback`, `build_rollback_execution`, and any filesystem
  write/unlink identifier are structurally absent from the module
  (AST-confirmed).
- No Cutover Record or activation marker was created or changed by this
  module — no reference to either filename, `activate_hatp_mandatory`,
  or `_write_cutover_transition` exists anywhere in the module.
- No `rollback_approval_state`/legacy approval mutation and no PER-status
  mutation call exists in this module (`create_rollback_approval_
  binding`/`revoke_rollback_approval_binding`/`write_binding` identifiers
  absent, AST-confirmed) — this module only *reads* existing RAE/HATP
  state via the unmodified engine.
- No real HATP_MANDATORY activation occurred; the production protected
  root (if it existed on this host, which it does not) shows no new
  cutover state.
- No governance bypass, `--no-verify` flag, or force push was used this
  phase. No test was skipped or weakened to force a pass.

---

## 5. Tests

- `tests/test_hatp_rollback_consumption.py` (34 tests) — deterministic,
  hardware-independent unit suite. Fixture harness hand-constructs a
  genuine `HATPSignedEvidenceEnvelope` (real `build_hatp_signed_evidence_
  envelope`) plus a hand-authored `RollbackApprovalBinding` under its own
  RAE key, with a proof whose `binding_id` points at that key — mirrors
  149O.4's own "no imported fixtures across phase boundaries" harness
  convention. Covers: request-shape validation; load errors (missing/
  corrupt/invalid-signature); the full valid chain (HATP `VALID`, PB
  denies because substrate readiness is never operational on this
  deployment — the same finding 149O.4/149O.5 established one layer
  down, now proven one layer up through this adapter); wrong operation/
  cross-family/wrong repository/wrong deployment; no implicit selection;
  no cache/repeat-attempt re-evaluation after deletion/revocation; no
  raw-hook/override inputs on either production entrypoint; MC-14
  simulation-only truthfulness and the current POL-005 consequence; a
  deterministic ALLOW-path wiring proof via an internal RAE/HATP engine
  substitution (never a production `allow=True` parameter); mode-
  agnosticism; production dependency-closure fail-closed behavior.
- `tests/test_phase_149o_18b_hatp_mandatory_evidence_consumption_
  adapter.py` (35 tests) — phase-boundary verification: production file
  allowlist, contract byte-identity (all seven), 18A module byte-
  identity, dependency closure (no cutover/agent/CLI import), MC-14
  structural checks, no-raw-hook checks, no-cache/no-persistence checks,
  no-effect/no-cutover-write/no-legacy-mutation checks (AST-based), and
  a fail-closed proof against a throwaway repository root.
- Total new tests this phase: **69**, all passing.

---

## 6. Regressions

- `test_hatp_mandatory_cutover.py` (149O.18A's own suite): green,
  unmodified, unaffected.
- HSCE/signed-evidence/store suites: green, unaffected (module never
  modified).
- HATP authority (`hatp_ag_authority.py`) / RAE / PB suites: green,
  unaffected (all three modules byte-unchanged).
- Rollback (AG3/AG5) behavior: unchanged (no wiring exists yet).
- **Fast Green:** 5270 passed, 0 unattributed failed, 2 skipped, with 12
  deselected: 11 are pre-existing "zero `src/pcae/` diff since phase X"
  snapshot assertions from 149O.14, 149O.16, 149O.16.2 (×5), 149O.17
  (×2), 149O.1g, and this phase's own pre-commit-state test in `test_
  phase_149o_18b_...py` — every one of these is mechanically invalidated
  purely by a new `src/pcae/` file now existing (the same expected
  consequence 149O.18A documented for itself; independently re-confirmed
  via `git stash -u` A/B baseline that all pass again once this phase's
  new files are removed). The 12th is `test_this_venv_interpreter_is_
  actually_python_39`, a pre-existing environment check unrelated to
  this phase (this repository's own `.venv` is currently Python 3.14,
  not 3.9 — independently confirmed to fail identically on the clean
  pre-phase baseline via the same A/B check). Raw undeselected run: 5270
  passed, 12 failed, 2 skipped.
- **Report trust:** `pcae phase-report show --latest` / `pcae push
  check` both pass locally ahead of staging (see §8).

---

## 7. Findings

None new this phase. Retained from prior phases, unchanged: the shared-
single-slot topology observation (149O.18A), HMRC N-1 (149O.16), the
REQ-080 editorial observation (149O.17), `149O.12B-Obs-PY39-1` (resolved,
149O.16.2), the repository-wide double-Z timestamp-parser hardening debt
(149O.16.2, explicitly not inherited by this phase's module — this
module introduces no new authority-bearing timestamp field of its own).

---

## 8. Implementation Verdict

**HATP MANDATORY EVIDENCE CONSUMPTION ADAPTER: IMPLEMENTED — READY FOR
149O.18C.**

HMRC-001 v1.0 remains `VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS`
(byte-unchanged). This phase does **not** claim mandatory AG3/AG5
enforcement — no effect-boundary wiring exists yet. HATP production
remains **NOT READY**. Runtime remains `Observed / observe /
unavailable`. `B-149O-1..4` remain **INDEPENDENTLY VERIFIED AT
HATP-GATED AUTHORITY BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED**,
unchanged by this phase.

## 9. Recommended Next Phase

**149O.18C — AG3 Mandatory Consumption Integration.** Per the 149O.17
plan (§10.3): wire fresh cutover-mode resolution (149O.18A) and this
phase's `evaluate_for_real_effect` into `execute_rollback`, immediately
before `_run_git_revert`, proven first via direct function calls (no CLI
flag registered yet), while preserving `LEGACY_COMPATIBLE`/`PREPARED`
semantics and preventing direct function-call bypass. No AG5 wiring in
18C.
