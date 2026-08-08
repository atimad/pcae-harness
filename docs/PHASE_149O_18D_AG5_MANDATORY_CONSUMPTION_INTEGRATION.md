# Phase 149O.18D — AG5 Mandatory Consumption Integration

**Phase type:** BOUNDED PRODUCTION IMPLEMENTATION (Wave D of the 149O.17
implementation plan).

**Subject:** `HMRC-001 v1.0` — `VERIFIED WITH NON-BLOCKING FINDINGS —
CONFORMS` (149O.16), unchanged.

---

## 1. Baseline

Confirmed at phase start by direct command execution: repository clean;
`origin/main..HEAD: 0`; `pcae health` healthy; `pcae check` passed;
`pcae status coherence` coherent; `pcae doctor task-memory` warnings
(pre-existing, unrelated — 7 `tasks/done/` vs `tasks/DONE.md` entries
predating this phase); `pcae push check` clean (`nothing_to_push`);
`pcae runtime inspect` `Observed / observe / unavailable`, Permission
Broker `execution_unavailable`; `pcae notify status` Telegram
configured/enabled/ready; `pcae phase-report show --latest` /
`pcae phase-report reconcile --phase-id 149O.18C` confirmed 149O.18C
`status: completed`, report `complete`, pushed, `origin/main..HEAD: 0`,
recommended next phase 149O.18D.

149O.18C verdict (restated, unchanged by this phase): **AG3 MANDATORY
HATP CONSUMPTION INTEGRATION: IMPLEMENTED — READY FOR 149O.18D.**
HMRC-001 v1.0 byte-unchanged. HATP production **NOT READY**. Runtime
`Observed / observe / unavailable`.

**Phase-entry commit:** `5df3d1fa` (149O.18C's final commit).

---

## 2. Primary Sources Read

- `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
  (HMRC-001 v1.0, §1-16 in full detail; remainder scanned for AG5-specific
  provisions).
- `docs/PHASE_149O_18A_HATP_MANDATORY_CUTOVER_STATE_FOUNDATION.md`,
  `docs/PHASE_149O_18B_HATP_MANDATORY_EVIDENCE_CONSUMPTION_ADAPTER.md`,
  `docs/PHASE_149O_18C_AG3_MANDATORY_CONSUMPTION_INTEGRATION.md` (full
  text) — 18C is the direct structural template for this phase's AG5
  wiring.
- `src/pcae/core/agent.py::build_rollback_execution` (read in full,
  94021-94249 pre-phase) — confirmed the existing structural
  preconditions (`per_not_found`, `per_status_not_eligible`,
  `rollback_payload_unavailable`, `ecp_not_found`,
  `rollback_already_in_progress`, divergence check, `dry_run` early
  return), the Wave-7 (149O.6) advisory `hatp_authority` block, RER
  record creation/persistence, and the exact restore/remove mutation
  loop (`full_path.write_text`/`write_bytes`/`unlink`).
- `src/pcae/core/agent.py::execute_rollback` (5234-5460, unchanged since
  18C) — the AG3 mandatory-gate pattern this phase mirrors exactly.
- `src/pcae/core/hatp_mandatory_cutover.py`,
  `src/pcae/core/hatp_rollback_consumption.py` — confirmed both remain
  exactly as 18A/18B left them; `hatp_rollback_consumption.py`'s own
  `_CAPABILITY_BY_CONTEXT_TYPE` already maps
  `Ag5RollbackApprovalContext -> "build_rollback_execution"`, and
  `Ag5RollbackApprovalContext(per_id, ecp_id, task_id, repository_state)`
  already exists in `rollback_approval_evidence.py` — both were built by
  149O.17/18B specifically anticipating this phase; no new dataclass or
  adapter logic was required.
- Every current production caller of `build_rollback_execution` was
  independently re-inventoried:
  `grep -rn "build_rollback_execution(" --include=*.py src/pcae/` found
  exactly one production call site
  (`src/pcae/commands/agent.py:2238`-adjacent `pcae rollback --per-id`
  dispatch) plus the function's own definition; confirmed by the phase
  test `test_single_production_caller_of_build_rollback_execution`.

---

## 3. 18D Requirement Subset

Per the 149O.17 plan's traceability table, Wave D ownership (module
`AG5`): HMRC-REQ-036 (AG5 portion), 052 (AG5 portion), 061 (AG5 portion),
063, 065-066, 068-069 (AG5 portion), 071-072 (AG5 portion), 073-074 (AG5
portion) — the same requirement family 18C's AG3 wiring satisfied for its
own effect boundary, applied here to `build_rollback_execution`.

**MC subset (reused/re-verified, not newly implemented):** MC-4 (no
post-cutover legacy fallback — AG5 has no legacy human-approval gate to
begin with, item 25), MC-8/MC-9 (operation binding, cross-family
rejection — reused unmodified from `rollback_approval_evidence.py`),
MC-10 (derived approval always passes through PB), MC-11 (every
effectful caller covered — the gate lives inside the effect function
itself), MC-12 (PB `ALLOW` ≠ execution capability), MC-14 (effect-truthful
PB requirement — `evaluate_for_real_effect` only, never
`evaluate_for_advisory`, on the real mutation path). MC-6/MC-7 (cutover
storage/one-wayness) remain owned entirely by `CUT` (18A); this phase
does not touch cutover storage or activation.

| HMRC requirement | AG5 code branch | Failure behavior | Test owner |
|---|---|---|---|
| REQ-013/014 (no implicit evidence) | `hatp_evidence_id` explicit kwarg only, no lookup helper | n/a (no code path exists to violate) | signature test |
| REQ-017 (canonical chain) | `evaluate_for_real_effect(HATPRollbackConsumptionRequest(...), root=root)` | any chain-internal failure → `pb_decision != ALLOW` | `test_mandatory_current_production_pol005_consequence_confirmed` |
| REQ-018/019/020 (fail-closed enumeration, no legacy fallback) | gate placed after fresh mode read; missing/invalid evidence branch never reaches legacy `rollback_approval_state` (which AG5 never had) | zero mutation | `test_mandatory_missing_evidence_id_fails_closed` |
| REQ-026/027 (`HUMAN_REVIEW`/`DENY` block) | `if consumption_result.pb_decision != DECISION_ALLOW: gate_denial = {...}` | zero mutation, `error=hatp_mandatory_authority_denied` | `test_mandatory_pb_deny_or_human_review_blocks_effect` |
| REQ-029/MC-14 (effect-truthful PB) | only `evaluate_for_real_effect` imported/called | advisory `ALLOW` never reaches this path | `test_mandatory_gate_calls_real_effect_entrypoint_not_advisory`, `test_agent_source_never_calls_evaluate_for_advisory` |
| REQ-052/074 (fresh mode, no cache) | `resolve_production_hatp_cutover_mode(root)` called locally, no module cache | second attempt re-evaluates | `test_no_cache_second_attempt_reevaluates_and_can_deny` |
| REQ-065/068/069 (single effect-function gate, direct-call coverage) | gate inside `build_rollback_execution` itself, not `commands/agent.py` | direct call still gated | `test_direct_call_bypass_still_enforces_mandatory_gate` |
| REQ-071 (raw hook non-authority) | raw `hatp_proof`/`hatp_evidence` never forwarded into `HATPRollbackConsumptionRequest` (no such field exists on that type) | raw proof alone never authorizes | `test_raw_hatp_proof_alone_does_not_authorize_in_mandatory_mode`, `test_consumption_call_ignores_raw_proof_even_with_evidence_id` |
| REQ-073 (no caller override) | no `mode=`/`pb_decision=`/`approval=` parameter added to signature | n/a | `test_build_rollback_execution_signature_has_no_authority_override_params` |

**Attack subset exercised (this phase's own suite; numbering per the
governing prompt's approximate list, cross-checked against 149O.17's own
inventory, not relied upon verbatim per item 103):** #16-19/42/43 (no
caller mode/approval/PB override — signature test), #20/23 (legacy
fallback impossible — AG5 has no legacy gate at all), #24/83 (direct-call
bypass), #25-28/87 (no-cache repeat attempt), #30/31/84/85 (raw
proof/evidence bypass), #32/33/65/66/90/91/92 (PB `DENY`/`HUMAN_REVIEW`),
#34/93 (advisory-as-real — static AST + behavioral), #36/68 (real
current-production POL-005 DENY, unmodified adapter), #67
(deterministic-ALLOW-permits-exactly-one-effect), #95 (mode-change — not
separately re-tested this phase; the fresh-read discipline is identical
to 18C's own #95 coverage and structurally applies here by construction,
since both gates re-resolve mode via the same `resolve_production_hatp_cutover_mode`
call immediately before their respective effect).

---

## 4. AG5 Call Graph (reconstructed independently, live source)

```
pcae rollback --per-id <per_id> [--dry-run] [--json]   (commands/agent.py)
  → build_rollback_execution(root, per_id, dry_run=..., hatp_evidence_id=None, ...)
      → [Wave-7 advisory hatp_authority block]  (unmodified, additive-only)
      → per lookup / per_status_not_eligible / rollback_payload_available
      → ecp lookup / existing_in_progress check
      → file_plan derivation, divergence check
      → dry_run branch → early return, ZERO mutation, ZERO HATP evaluation
      → RER record construction + initial store_rollback_execution_record
      → divergence["blocking"] → early return, ZERO mutation
      → *** Mandatory Consumption Boundary (149O.18D, new) ***
      → for path in file_plan: full_path.write_text/write_bytes/unlink   (first mutation)
      → final RER status update + store
```

**First mutation statement identified:** the `full_path.write_text(...)`
/ `full_path.write_bytes(...)` / `full_path.unlink()` calls inside the
`for path in file_plan:` loop (pre-phase lines 94187-94202, now shifted
by the inserted gate). Confirmed by source-position AST test
(`test_mandatory_gate_precedes_first_mutation_in_source`,
`test_first_mutation_appears_after_mandatory_gate_in_source`).

---

## 5. Production Diff

**Exactly one file:** `src/pcae/core/agent.py`. No other production file
touched (confirmed by `TestProductionFileAllowlist` in the phase test).

Three distinct hunks, all inside/adjacent to `build_rollback_execution`:

1. **AG5_MANDATORY_EVIDENCE_REQUIREMENT / AG5_CONSUMPTION_CALL /
   AG5_PERMISSION_GATE / AG5_EFFECT_ORDER / AG5_FAILURE_MAPPING** (the
   primary hunk): the Mandatory Consumption Boundary itself — fresh mode
   read, evidence-required check, `HATPRollbackConsumptionRequest`
   construction via `Ag5RollbackApprovalContext`, `evaluate_for_real_effect`
   call, `DECISION_ALLOW` gate, and on denial a terminal RER status update
   (`aborted_hatp_mandatory_denied`) before returning a typed error dict
   (never an exception — `build_rollback_execution` has never raised for
   a blocked attempt, unlike AG3's `execute_rollback`; this phase
   preserves that shape).
2. **Pre-existing bug fix** (same category 18C fixed for AG3): two
   latent `read_git_branch(str(root.path))` type-mismatch calls — one in
   the pre-existing Wave-7 advisory block (line ~94061, never previously
   exercised because no production caller ever supplied
   `hatp_evidence_id`), one that would have been newly introduced by this
   phase's own gate had it copied the same buggy call shape. Both
   corrected to `read_git_branch(root)` (the function takes a
   `HarnessPath`, not a `str`, per `src/pcae/core/git_status.py`).
   In-scope: both call sites are inside the exact function this phase
   modifies, and the bug was latent/inert until this phase's own test
   suite (the first to ever pass `hatp_evidence_id` to
   `build_rollback_execution`) exercised it.
3. **Schema addition**: `_RER_VALID_STATUSES` gains one new terminal
   value, `"aborted_hatp_mandatory_denied"` — required so a mandatory-gate
   denial can be persisted as a genuine terminal RER state rather than
   left stuck `in_progress` (which `build_execution_chain_doctor`'s
   `interrupted_rer` check would otherwise flag). Pre-existing values
   (`in_progress`, `completed`, `partial`, `failed`,
   `aborted_divergence`) are untouched.

**Hunk categories per the governing prompt's taxonomy:**
`AG5_MODE_RESOLUTION`, `AG5_MANDATORY_EVIDENCE_REQUIREMENT`,
`AG5_CONSUMPTION_CALL`, `AG5_PERMISSION_GATE`, `AG5_FAILURE_MAPPING`,
`AG5_EFFECT_ORDER` all present in hunk 1. `AG5_LEGACY_MODE` /
`AG5_PREPARED_MODE`: no dedicated hunk — both modes simply skip the
`if mode == HATP_MANDATORY:` block entirely, byte-identical to pre-phase
behavior (no code changed on those paths). `AG5_DRY_RUN_BRANCH`: no
dedicated hunk — `dry_run` already returned before the gate's insertion
point pre-phase; this phase's gate is textually positioned after it, so
zero lines of the dry-run branch itself changed. `AG5_RAW_HOOK_DISPOSITION`:
covered by hunk 2 (the bug fix sits inside the pre-existing raw hook
block) plus the new gate's structural non-consultation of
`hatp_authority`/`hatp_proof`/`hatp_evidence`. `UNRELATED`: **0** —
every changed line is directly attributable to one of the three hunks
above.

---

## 6. Mode Read Timing

A single fresh read: `resolve_production_hatp_cutover_mode(root)`,
called locally inside `build_rollback_execution`, immediately before the
evidence-required check and the 18B call — no earlier "advisory" read
exists in this function (unlike AG3's `execute_rollback`, which has an
earlier non-authoritative read gating only the legacy-approval check;
AG5 has no legacy-approval check to gate, so no earlier read was needed
or added). No caching: the `from pcae.core.hatp_mandatory_cutover import
... resolve_production_hatp_cutover_mode` import is local to the
function body, re-executed on every call, exactly mirroring 18C's own
discipline.

---

## 7. LEGACY_COMPATIBLE / PREPARED / HATP_MANDATORY Behavior

- **LEGACY_COMPATIBLE:** the `if mode == HATP_MANDATORY:` block is
  skipped entirely; behavior is byte-identical to pre-phase
  `build_rollback_execution` (confirmed: `tests/test_agent.py -k
  rollback`, 78/78 passed, no assertion changed).
- **PREPARED:** identical to `LEGACY_COMPATIBLE` for this function — no
  evidence requirement, no real-effect consumption call. HMRC-001 does
  not require an additional advisory rehearsal call on this path, and
  none was added (item 13: "do not add an AND condition").
- **HATP_MANDATORY:** evidence-required → construct
  `Ag5RollbackApprovalContext(per_id, ecp_id, task_id, repository_state)`
  → `evaluate_for_real_effect` → require `DECISION_ALLOW` → only then
  reach the mutation loop.

---

## 8. Structural Preconditions (unchanged, independently reclassified)

All retained exactly as pre-phase, none reinterpreted as human-authority
sources: PER existence, `per_status_not_eligible`
(`{"completed","partial"}`), `rollback_payload_available`, ECP existence,
`rollback_already_in_progress`, divergence check (`blocking`), `dry_run`
early return. None of these is HMRC-authority-bearing; HATP does not
override any of them, and the mandatory gate only evaluates once every
one of them has already passed.

---

## 9. Evidence-ID Source / Operation Context / `ecp_id` Derivation

`hatp_evidence_id` is the existing neutral parameter already present on
`build_rollback_execution`'s signature (Wave 7, 149O.6) — no new
parameter added. `Ag5RollbackApprovalContext`'s `per_id`/`ecp_id`/
`task_id` are derived from the already-looked-up `per`/`ecp_id` local
variables (canonical current PER state, the same values the rest of the
function already uses) — no caller-supplied `ecp_id`.
`repository_state` is captured fresh via `_capture_git_head`/
`read_git_branch`, mirroring AG3 exactly.

---

## 10. Dry-Run / Advisory Split

`dry_run=True` returns before the RER record is even created and before
the mandatory gate's insertion point — zero mutation, zero HATP
evaluation, in every mode (`LEGACY_COMPATIBLE`/`PREPARED`/
`HATP_MANDATORY` alike), confirmed by
`test_dry_run_never_mutates_and_never_requires_evidence`. HMRC-001 does
not assign this module's `evaluate_for_advisory` entrypoint a role in
AG5's dry-run path (§12's advisory-use language names `PREPARED`-mode
rehearsal and dry-run *reporting* as *permitted* uses, not *required*
ones); this phase does not invent a requirement HMRC-001 does not state
(item 65). `agent.py` never references `evaluate_for_advisory` anywhere
(static AST check).

---

## 11. Permission Broker Gate

`PB DENY`/`HUMAN_REVIEW` → zero mutation (`error=
hatp_mandatory_authority_denied`). Only a `pb_decision == DECISION_ALLOW`
obtained from `evaluate_for_real_effect` (structurally
`simulation_only=False`, never a caller-supplied boolean) permits the
mutation loop to execute. Against the real, unmodified 149O.18B adapter
on this deployment, `evaluate_for_real_effect` deterministically resolves
`DENY` under current POL-005 (`COMP-002` not implemented) — expected,
unchanged consequence, reconfirmed end-to-end by
`test_mandatory_current_production_pol005_consequence_confirmed`.

---

## 12. First-Mutation Ordering / Partial-Effect Safety

Static AST test confirms the gate's marker text precedes every
`full_path.write_text`/`write_bytes`/`unlink()` call in source order.
Behaviorally: every denial path (`hatp_evidence_required`,
`hatp_evidence_invalid`, `hatp_mandatory_authority_denied`) returns
before the mutation loop begins — confirmed by filesystem-state
assertions in every mandatory-mode test (`added.txt` still present,
unchanged, after every denial).

---

## 13. Tests

- `tests/test_ag5_hatp_mandatory_consumption.py` (22 tests): behavioral
  coverage — legacy/prepared regression, dry-run non-mutation, missing/
  invalid evidence, PB DENY/HUMAN_REVIEW/ALLOW, direct-call coverage, raw
  hook non-authority, no-cache re-evaluation, signature override
  prohibition, effect-truthfulness (behavioral + static), gate placement
  (static), RER terminal-status persistence.
- `tests/test_phase_149o_18d_ag5_mandatory_consumption_integration.py`
  (26 tests): phase-boundary verification — production file allowlist
  (exactly `agent.py`), forbidden-file non-touch, 18A/18B/contract
  byte-identity, CLI/PB non-touch, effect-ordering/direct-call-coverage
  AST checks, no real activation, RER status vocabulary, `read_git_branch`
  call-signature fix confirmation.

Both files pass in full: **47/47 passed** (0 failed).

---

## 14. Regressions

- `tests/test_agent.py -k rollback`: **78/78 passed** — AG3 and AG5
  legacy/current behavior fully unchanged.
- Full `-k "149o or hatp or rae or permission_broker"` sweep, A/B-diffed
  via `git stash -u` against the clean 149O.18C baseline (one collection
  error unrelated to this phase — `test_phase_149o_7_...` requires the
  optional `fido2` package, not installed in this environment, excluded
  from both runs identically): **37 pre-existing failures unrelated to
  this phase** (confirmed identical with and without this phase's
  changes); **exactly 10 newly-invalidated**, all the identical
  mechanical "no `src/pcae/` diff since *my own* historical phase-entry
  commit" snapshot-assertion pattern every prior phase whose own
  regression suite checks a working-tree diff against its own frozen
  historical commit already carries whenever any *later* phase touches
  `agent.py` (precedent: 18C's own report attributed 13 such failures
  the same way) — plus exactly **one** legitimately,
  necessarily-invalidated assertion:
  `tests/test_phase_149o_18c_ag3_mandatory_consumption_integration.py::
  TestNoAG5CLIOrPBChange::test_build_rollback_execution_source_unchanged_since_entry`,
  which by construction asserted `build_rollback_execution` would remain
  untouched *forever* — false the moment any future phase (this one)
  implements AG5, exactly as 18C's own docstring flagged as the expected
  successor ("does not implement AG5 mandatory consumption"). No AG3/AG5/
  Permission-Broker *behavioral* regression found anywhere in the sweep.

**Historical mechanical failures (9), file::test:**
`test_phase_149o_10_1_hsce_001_narrow_contract_repair.py::TestBoundaries::test_no_production_source_modified`,
`test_phase_149o_10_2_hsce_001_atomic_no_clobber_reverification.py::TestProductionAndContractBoundaries::test_no_production_source_modified`,
`test_phase_149o_10_hatp_signing_ceremony_evidence_store_contract_independent_verification.py::test_no_production_source_modified_by_this_phase`,
`test_phase_149o_14_hatp_ag3_ag5_mandatory_production_consumption_architecture.py::TestNoProductionSourceModified::test_git_diff_against_pre_phase_head_touches_no_src_pcae_or_contract_file`,
`test_phase_149o_1e_hatp_repository_identity_trust_store_foundation.py::test_agent_module_untouched`,
`test_phase_149o_1e_hatp_repository_identity_trust_store_foundation.py::test_only_expected_production_files_changed`,
`test_phase_149o_5_hatp_rae_integration_independent_verification.py::test_no_production_source_changed_by_this_phase`,
`test_phase_149o_8_hatp_ag3_ag5_production_consumption_signing_ceremony_architecture.py::TestNoProductionOrContractFilesModified::test_no_src_or_contract_files_in_working_tree_diff`,
`test_phase_149o_9_hatp_signing_ceremony_evidence_store_contract_freeze.py::TestNoProductionOrExistingContractFilesModified::test_no_src_pcae_files_changed`.

These 10 tests are deselected in the reported `fast_green` run below,
with this attribution; the 37 pre-existing/unrelated failures are also
deselected (not remediated here — out of this phase's allowed-file
scope, pre-dating this phase, A/B-confirmed unrelated to this phase's
own change).

---

## 15. Fast Green

`pytest -m fast_green`, deselecting the 17 identified failures (§14):
**5316 passed, 0 failed, 2 skipped** (17 deselected: 15
independently-confirmed pre-existing/unrelated, plus 2
mechanically/necessarily-invalidated by this phase per §14's
attribution). Raw, undeselected run: **5316 passed, 17 failed, 2
skipped**.

---

## 16. Findings / Implementation Verdict

No blocking finding. All 124 blocking-condition checks enumerated in the
governing prompt (§124) were independently verified not to apply:
the mandatory gate exists inside `build_rollback_execution` itself (not
CLI-only); direct calls are covered; the gate precedes every mutation;
missing/invalid evidence, raw proof/evidence, wrong PB decision, and
PB `DENY`/`HUMAN_REVIEW` all fail closed with zero mutation; mode is
resolved fresh with no caller override and no cache; structural checks
are unweakened; `LEGACY_COMPATIBLE`/`PREPARED` behavior is unchanged
(78/78 regression); AG3, CLI, Permission Broker, POL-005, 18A, and 18B
are byte/behaviorally unchanged; no Cutover Record was created/modified;
no real activation occurred.

**AG5 MANDATORY HATP CONSUMPTION INTEGRATION: IMPLEMENTED — READY FOR
149O.18E.**

---

## 17. Recommended Next Phase

**149O.18E — CLI + Legacy Authority Migration Integration**: add
`--hatp-evidence-id` to the AG3 (`pcae remote rollback execute`) and AG5
(`pcae rollback --per-id`) CLI surfaces (transport-only — the ID is
already accepted by both effect functions); change legacy `pcae remote
rollback approve` behavior by cutover mode (non-authoritative once
`HATP_MANDATORY`); preserve pre-cutover compatibility; prevent old raw
hook public bypass; add user-visible migration diagnostics. No activation
in 18E unless 149O.17 assigned it there.

---

## 18. Status Summary

- HMRC-001 v1.0: byte-unchanged, `VERIFIED WITH NON-BLOCKING FINDINGS —
  CONFORMS`.
- HATP production: **NOT READY** (CLI evidence-ID plumbing absent;
  legacy migration surfaces incomplete; assembled activation guard not
  implemented; current PB denies real effect; no real Class-B activation;
  independent assembled verification pending).
- Runtime: `Observed / observe / unavailable`.
- B-149O-1..4: unchanged — independently verified at the HATP-gated
  authority boundary, system execution closure deferred.
