# Phase 149O.18C — AG3 Mandatory Consumption Integration

**Phase type:** BOUNDED PRODUCTION IMPLEMENTATION (Wave C of the 149O.17
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
`pcae phase-report reconcile --phase-id 149O.18B` confirmed 149O.18B
`status: completed`, report `complete`, pushed, `origin/main..HEAD: 0`,
reconciliation `status: reconciled` (mutation: none), recommended next
phase confirmed as 149O.18C.

149O.18B verdict (restated, unchanged by this phase): **HATP MANDATORY
EVIDENCE CONSUMPTION ADAPTER: IMPLEMENTED — READY FOR 149O.18C.**
HMRC-001 v1.0 byte-unchanged. HATP production **NOT READY**. Runtime
`Observed / observe / unavailable`.

**Phase-entry commit:** `5143bb27` (149O.18B's final commit).

---

## 2. Primary Sources Read

- `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
  (HMRC-001 v1.0, full text, §1-36).
- `docs/PHASE_149O_18A_HATP_MANDATORY_CUTOVER_STATE_FOUNDATION.md`,
  `docs/PHASE_149O_18B_HATP_MANDATORY_EVIDENCE_CONSUMPTION_ADAPTER.md`
  (full text).
- `src/pcae/core/hatp_mandatory_cutover.py` (full file, 149O.18A) —
  confirmed `resolve_production_hatp_cutover_mode(root: HarnessPath) ->
  CutoverModeResolution` as the sole production entrypoint, and
  `CutoverModeResolution.mode: CutoverMode` as the three-value vocabulary.
- `src/pcae/core/hatp_rollback_consumption.py` (full file, 149O.18B) —
  confirmed `evaluate_for_real_effect(request, *, root)` as the
  structurally-truthful `simulation_only=False` real-effect entrypoint,
  `HATPRollbackConsumptionRequest(evidence_id, operation_context)`, and
  `HATPRollbackConsumptionResult(evidence_id, hatp_status, pb_decision,
  reasons)`.
- `src/pcae/core/agent.py::execute_rollback` (read in full, 5234-5460) —
  confirmed the existing structural preconditions (idempotent-return,
  `rollback_approval_state`, `rollback_eligible`,
  `rollback_mode_recommendation`, clean working tree,
  original-commit-is-ancestor), the Wave-7 (149O.6) advisory
  `hatp_authority` block, and the exact `_run_git_revert` call site.
- `src/pcae/core/rollback_approval_evidence.py` — confirmed
  `Ag3RollbackApprovalContext(job_id, original_commit_sha, task_id,
  repository_state)` and `RepositoryStateBinding(head_commit_sha, branch)`.
- Every current production caller of `execute_rollback` was independently
  re-inventoried (not assumed unchanged from 149O.17's own text):
  `grep -rn "execute_rollback(" src/pcae/*.py src/pcae/**/*.py` found
  exactly two textual matches — `src/pcae/commands/agent.py:2238`
  (the real, single production caller of `pcae.core.agent.execute_rollback`)
  and `src/pcae/commands/cltr_migration.py:102`
  (`rehearsal_rollback.execute_rollback`, a same-named but entirely
  different function in `pcae.cltr.migration.rehearsal.rollback`, confirmed
  unrelated by reading both modules directly).

---

## 3. 18C Requirement Subset

Per the 149O.17 plan's traceability table, Wave C ownership (module
`AG3`): HMRC-REQ-036, 052 (AG3 portion), 061, 063, 065, 066, 068, 069
(AG3 portion), 071-072 (AG3 portion), 073-074 (AG3 portion).

**MC subset:** MC-4 (no post-cutover legacy fallback), MC-6 (protected
state determines mode), MC-7 (ordinary runtime cannot downgrade), MC-10
(approval goes through PB), MC-11 (PB ALLOW ≠ capability, AG3 production
effect caller covered), MC-14 (real effect uses truthful PB).

**Attack subset covered by this phase's new test suite**
(`tests/test_ag3_hatp_mandatory_consumption.py`): #20/#23/#63 (legacy
approved + missing HATP, post-cutover), #24/#83 (direct-call bypass),
#30/#31/#84/#85 (raw-hook bypass), #25-28/#87 (no cache/repeat attempt),
#32/#33/#65/#66/#90/#91 (PB DENY/HUMAN_REVIEW), #34/#92/#93 (effect
truthfulness), #36 (current POL-005 consequence), #42/#43 (no
mode/authority override), #64 (legacy-unapproved + HMRC ALLOW reaches
effect), #67 (deterministic ALLOW permits exactly one effect). Attacks
owned by Waves A/B/D/E/F (#1-19, #22, #29, #35, #37-41, #44-45) are
covered by 18A/18B's own suites or are not this phase's to exercise.

---

## 4. Production Diff (Two Files — Classified Exception)

**Expected:** `src/pcae/core/agent.py` only. **Actual:**
`src/pcae/core/agent.py` and `src/pcae/core/hatp_mandatory_cutover.py`.

`git diff --stat 5143bb27 -- src/pcae/`:

```
 src/pcae/core/agent.py                  | 101 +++++++++++++++++++++++++++-----
 src/pcae/core/hatp_mandatory_cutover.py |  32 +++++++++-
```

### 4.1 `agent.py` (expected file)

`execute_rollback` gained:

- Fresh mode resolution before the existing legacy `rollback_approval_state`
  gate (skips that gate entirely in `HATP_MANDATORY`, unchanged in
  `LEGACY_COMPATIBLE`/`PREPARED`).
- A second, independent fresh mode resolution immediately before
  `_run_git_revert` (the Mandatory Consumption Boundary): in
  `HATP_MANDATORY`, requires `hatp_evidence_id`, constructs an
  `Ag3RollbackApprovalContext`, calls `evaluate_for_real_effect`, and
  requires `pb_decision == DECISION_ALLOW` before the effect proceeds.
- Two pre-existing bug fixes, discovered and fixed only because this
  phase's own new test suite exercised the Wave-7 `hatp_authority` block
  and the new gate together for the first time (§5 below):
  `read_git_branch(str(root.path))` → `read_git_branch(root)` at both
  the existing Wave-7 call site (line ~5290, pre-existing since 149O.6)
  and this phase's new call site.

No other function in `agent.py` was touched. `build_rollback_execution`
(AG5) is byte-unchanged (confirmed: `git diff 5143bb27 -- agent.py` does
not contain `def build_rollback_execution`).

### 4.2 `hatp_mandatory_cutover.py` (classified exception, §5)

One narrow, single-hunk correction to `_resolve_cutover_mode_at_root`'s
identity-absent branch. Full classification below.

---

## 5. Classified Defect: Identity-Absent Resolution vs. HMRC-REQ-032

**Discovery.** Wiring `resolve_production_hatp_cutover_mode` into
`execute_rollback` exactly as HMRC-REQ-066/074 specify — the sole,
unmodified production entrypoint, no override — was attempted first.
Running the existing regression suite (`pytest tests/test_agent.py -k
rollback`) against that wiring produced **8 failures**
(`test_43d_approved_rollback_creates_revert_commit`,
`test_43d_rollback_commit_sha_captured`, `test_43d_persists_rollback_metadata`,
`test_43d_rollback_status_is_rolled_back`,
`test_43d1_second_execute_preserves_rollback_sha`,
`test_43e_approved_executed_rollback_can_be_pushed`,
`test_43e_rollback_commit_sha_in_output`,
`test_43e_rollback_commit_not_in_history_blocks_push`) — a direct
`LEGACY_COMPATIBLE` regression, forbidden by this phase's own charter and
by HMRC-REQ-032.

**Root cause.** `_resolve_cutover_mode_at_root` (149O.18A) fails closed to
`HATP_MANDATORY` unconditionally whenever local `repository_instance_id`
resolution (`read_repository_identity`) returns `None` — *before* ever
consulting the protected root's Cutover Record or monotonic marker. This
repository itself has no `.pcae/repository-identity.json` (confirmed
directly: `read_repository_identity(HarnessPath.cwd())` returns `None` on
this real development host), so the unmodified 18A resolver classifies
*this actual, real, un-cutover deployment* as `HATP_MANDATORY` — directly
contradicting HMRC-REQ-032's explicit text: "Default state for every
existing deployment, including the current local development host."

**Why this is a proven, narrow API defect, not a redesign call.**
HMRC-REQ-045's Cutover Record schema itself requires a
`repository_instance_id` field to exist at the moment any record is
written. A repository with **no local identity at all** cannot possibly
have a Cutover Record naming it, by construction — so identity-absence
combined with a protected root that also has **no Cutover Record and no
monotonic marker at all** is unambiguous proof of first-install, exactly
the case HMRC-REQ-050 already resolves to `LEGACY_COMPATIBLE`. 18A's
resolver never reaches that check for the identity-absent case; it
short-circuits first. This exactly matches this phase's own governing
constraint for touching a frozen module: *"a narrowly-proven API defect,"*
classified here rather than guessed at.

**Security property re-verified, not weakened.** The one scenario the
original unconditional fail-closed branch defended against — an agent
deleting its own local, agent-writable `repository-identity.json` to try
to escape a *genuinely* HATP_MANDATORY-activated deployment — is
unaffected: if the protected root carries **any** activation evidence at
all (a valid, corrupt, or symlinked Cutover Record or marker, for *any*
repository), the corrected resolver still fails closed to
`HATP_MANDATORY`, identically to before. Only the doubly-absent case
(no record, no marker) changes outcome. Proven by
`tests/test_hatp_mandatory_cutover.py::
test_no_repository_identity_with_existing_record_fails_closed` and
`::test_no_repository_identity_with_existing_marker_fails_closed` (new
this phase), and by
`tests/test_phase_149o_18c_ag3_mandatory_consumption_integration.py::
TestClassifiedCutoverResolverCorrection` (production-code-path
re-verification, not just the unit fixture).

**Scope of the fix.** Exactly one function, one hunk: the
identity-`None` branch of `_resolve_cutover_mode_at_root`, changed from
an unconditional `return CutoverModeResolution(HATP_MANDATORY, ...)` to a
probe of the existing (unmodified) `_read_cutover_record`/
`_read_cutover_activation_marker` readers — reusing them exactly as-is,
adding no new file-reading logic. Every code path reachable when
`repository_instance_id` is not `None` is byte-for-byte identical to
149O.18A (confirmed:
`TestClassifiedCutoverResolverCorrection::test_identity_present_paths_are_untouched`).
`is_valid_cutover_transition`, the Cutover Record schema/parser, the
protected-storage symlink discipline, and `_write_cutover_transition`
are all untouched.

**Superseded historical assertion.** 18A's own
`test_no_repository_identity_fails_closed` asserted the old (now-corrected)
unconditional behavior for the doubly-absent case. It is replaced by
`test_no_repository_identity_and_no_activation_evidence_is_legacy`
(same doubly-absent scenario, corrected expectation) plus the two new
security-property tests above — an intentional, narrow snapshot-test
update, not a weakening (86/87 of 149O.18A's own suite pass unmodified;
the sole other failure,
`test_accept_strict_timestamp[2026-08-08T12:00:00.0Z]`, is pre-existing
and unrelated, confirmed via `git stash` A/B against the clean baseline).

---

## 6. AG3 Current Call Graph (Reconstructed)

```
pcae remote rollback execute <job_id> [--json]
  → run_remote_rollback_execute (commands/agent.py:2238)
    → execute_rollback(HarnessPath.cwd(), args.job_id)   [no hatp_evidence_id — unchanged]
      → Wave-7 hatp_authority block (advisory only, 149O.6) — inert (hatp_evidence_id is None)
      → build_rollback_review / _load_job_and_artifact
      → idempotent already_rolled_back short-circuit
      → [NEW] fresh cutover-mode resolution (early read)
        → if != HATP_MANDATORY: legacy rollback_approval_state gate (unchanged)
      → rollback_eligible / rollback_mode_recommendation / dirty-tree / ancestor checks (unchanged)
      → [NEW] Mandatory Consumption Boundary: fresh cutover-mode resolution (boundary read)
        → if == HATP_MANDATORY: require hatp_evidence_id
          → HATPRollbackConsumptionRequest(evidence_id, Ag3RollbackApprovalContext(...))
          → evaluate_for_real_effect(request, root=root)   [149O.18B, simulation_only=False, structural]
          → require pb_decision == DECISION_ALLOW
      → _run_git_revert(original_commit_sha, ...)
      → persist job / return result
```

No CLI caller today supplies `hatp_evidence_id` (HMRC-REQ-011's
`--hatp-evidence-id` flag is intentionally not registered until 18E), so
the current, real `pcae remote rollback execute` command is unaffected in
practice — it always resolves `LEGACY_COMPATIBLE` on this deployment
(§5) and behaves exactly as before.

---

## 7. Mode Resolution / Mode-Read Timing

Two independent, freshly-evaluated calls to
`resolve_production_hatp_cutover_mode(root)` exist in `execute_rollback` —
never a shared/cached local variable, never a module-level cache, never a
caller-supplied override:

1. **Early read**, immediately after the idempotent short-circuit: decides
   only whether the *legacy* `rollback_approval_state` gate applies.
   Staleness here has no security consequence — cutover transitions are
   monotonic and one-way, so a mode change mid-call can only move
   *toward* `HATP_MANDATORY`, and the actual authority decision is never
   taken from this read.
2. **Boundary read**, immediately before `_run_git_revert`: the sole
   authoritative gate. Re-resolved fresh rather than reusing the early
   read specifically so a mode transition occurring after the call began
   (attack #51) is still enforced at the actual effect attempt
   (HMRC-REQ-052/074).

No mode value is cached in a module-level variable, instance attribute,
or process-long structure (`TestNoRealActivation` /
`test_no_cutover_record_or_marker_writer_referenced_in_agent_py`, and
direct source inspection: `resolve_production_hatp_cutover_mode` itself
performs a full filesystem read/validate sequence on every call, §4.6 of
149O.18A).

---

## 8. LEGACY_COMPATIBLE / PREPARED Flow (Unchanged)

Both modes take the identical, pre-149O.18C code path: the legacy
`rollback_approval_state` gate applies exactly as before (pending/denied/
unexpected-state all raise `ValueError`, unchanged messages), structural
checks apply unchanged, and the Mandatory Consumption Boundary's `if
mode == HATP_MANDATORY` guard is false, so no evidence requirement, no
149O.18B call, and no behavior change occurs. Confirmed by
`test_legacy_and_prepared_dispatch_unchanged` (parametrized over both
modes) and by the full pre-existing `tests/test_agent.py -k rollback`
suite (78/78 passed, unmodified).

`PREPARED` does not introduce any additional mandatory evaluation
(HMRC-REQ-035) — confirmed by `test_prepared_does_not_require_evidence`.

---

## 9. HATP_MANDATORY Flow

1. Legacy gate skipped entirely (rollback_approval_state never read as an
   authority signal — `test_mandatory_legacy_unapproved_plus_
   deterministic_allow_reaches_effect` proves an *unapproved* job still
   reaches effect given a deterministic HMRC ALLOW, disproving any
   residual `legacy AND hatp` requirement).
2. Structural checks (job existence/eligibility/mode-recommendation/clean
   tree/ancestor) unchanged and still required.
3. Missing `hatp_evidence_id` → `ValueError`, zero effect
   (`test_mandatory_missing_evidence_id_fails_closed`).
4. `evaluate_for_real_effect` called with a fresh
   `HATPRollbackConsumptionRequest`; raw `hatp_proof`/`hatp_evidence`
   arguments are structurally never forwarded into it
   (`test_consumption_call_ignores_raw_proof_even_with_evidence_id`,
   `test_raw_hatp_proof_alone_does_not_authorize_in_mandatory_mode`).
5. `pb_decision != DECISION_ALLOW` (DENY or HUMAN_REVIEW) → `ValueError`,
   zero effect (`test_mandatory_pb_deny_or_human_review_blocks_effect`,
   parametrized).
6. `pb_decision == DECISION_ALLOW` (only reachable via the deterministic
   internal test seam — never a caller parameter) → exactly one
   `_run_git_revert` call
   (`test_mandatory_deterministic_allow_permits_exactly_one_effect`).
7. Against the real, unmodified 149O.18B adapter (no test seam): PB
   deterministically `DENY`s under current POL-005, zero effect
   (`test_mandatory_current_production_pol005_consequence_confirmed`) —
   the accepted, documented consequence (§13).

---

## 10. Legacy Gate Restructuring

The pre-existing unconditional block:

```python
rollback_approval_state = job.get("rollback_approval_state", "pending")
if rollback_approval_state == "pending": raise ValueError(...)
if rollback_approval_state == "denied": raise ValueError(...)
if rollback_approval_state != "approved": raise ValueError(...)
```

is now wrapped in `if resolve_production_hatp_cutover_mode(root).mode !=
CutoverMode.HATP_MANDATORY:` — line-for-line identical inside the guard,
so `LEGACY_COMPATIBLE`/`PREPARED` behavior (including exact error
messages and their precedence relative to the later structural checks) is
byte-identical to before. In `HATP_MANDATORY`, the block is skipped
entirely — `rollback_approval_state` is read nowhere else in the
function, so it supplies zero authority in that mode (HMRC-REQ-061).

---

## 11. Structural Preconditions (Retained, Unaffected by Cutover)

`rollback_eligible`, `rollback_mode_recommendation == "revert_commit"`,
clean working tree, and original-commit-is-ancestor-of-HEAD are
unconditional in every mode — not touched by this phase, still positioned
exactly where they were (HMRC-REQ-063). HATP validity never substitutes
for or overrides any of them (proven end-to-end by
`test_real_git_revert_in_temp_repo_legacy_vs_mandatory`'s HATP_MANDATORY
branch, which never reaches structural failure but does prove no
additional commit is created when the mandatory gate blocks).

---

## 12. Old Wave-7 Hook Disposition

The pre-existing, additive-only `hatp_authority` advisory block (149O.6)
is untouched and remains active in every mode when a caller supplies
`hatp_evidence_id` — it still never gates dispatch (unchanged
`hatp_ag_authority.resolve_ag3_gated_rollback_authority`,
`simulation_only=True`, advisory-only per its own docstring). It is not
consulted by, and does not influence, the new Mandatory Consumption
Boundary — the two never share state, and only the new gate's
`evaluate_for_real_effect` result can permit the effect in
`HATP_MANDATORY` (`test_mandatory_gate_calls_real_effect_entrypoint_not_
advisory` proves the boundary gate's own entrypoint choice;
`test_agent_source_never_calls_evaluate_for_advisory` proves the real
effect path never touches the advisory 18B entrypoint either). No dual
HATP authority evaluation exists on the real effect path.

Two latent bugs in this pre-existing block (`read_git_branch(str(root.path))`
instead of `read_git_branch(root)`, a type mismatch that raises
`AttributeError` whenever `hatp_evidence_id` is supplied — never
previously exercised, since no production caller ever supplies it) were
discovered and fixed as part of building this phase's own test suite
(§4.1) — squarely in-scope, since both call sites are inside
`execute_rollback` itself, the exact function this phase modifies.

---

## 13. Current Production Consequence

Exactly as 149O.18B documented: `evaluate_for_real_effect`'s truthful
`simulation_only=False` request deterministically resolves PB `DENY`
under current POL-005, even with valid HATP evidence. Therefore, on this
real deployment, `HATP_MANDATORY` + otherwise-valid evidence still
produces **zero git effect** — confirmed end-to-end through the real
`execute_rollback` wiring this phase adds
(`test_mandatory_current_production_pol005_consequence_confirmed`), not
merely at the adapter layer. `HATP_MANDATORY` does not, and cannot yet,
guarantee rollback availability (HMRC-REQ-029/037) — unchanged, not
weakened.

---

## 14. Tests

- **`tests/test_ag3_hatp_mandatory_consumption.py`** (20 tests, new) —
  behavioral integration: LEGACY_COMPATIBLE/PREPARED regression, missing/
  invalid evidence fail-closed, no-dual-authority (attack #64), PB
  DENY/HUMAN_REVIEW blocking, real-POL-005 consequence, deterministic
  ALLOW exactly-one-effect, direct-call bypass prevention, raw-hook
  rejection, no-cache repeat-attempt re-evaluation, signature closure
  (no authority-override parameters), effect-truthfulness (real vs.
  advisory entrypoint, both behavioral and AST-static), and a real
  temporary-git-repository effect test (not the project repository)
  proving both a genuine `LEGACY_COMPATIBLE` revert and a blocked
  `HATP_MANDATORY` non-effect (zero new commits) against real `git`.
- **`tests/test_phase_149o_18c_ag3_mandatory_consumption_integration.py`**
  (24 tests, new) — phase-boundary verification: production file
  allowlist (both expected files, git-diff-based), 18B byte-identity,
  full classification re-verification for the 18A correction (single-hunk
  diff, doubly-absent→LEGACY_COMPATIBLE, activation-evidence-present→
  still-fails-closed, identity-present paths untouched), all seven
  contract byte-identities, AG5/CLI/PB non-change, effect-ordering
  (AST-position check: gate text precedes `_run_git_revert` call in
  source), single-production-caller confirmation (live grep, not a static
  list), no-advisory-call static check, no-real-activation check, and a
  live re-confirmation that this actual repository still resolves
  `LEGACY_COMPATIBLE` end-to-end.
- **`tests/test_hatp_mandatory_cutover.py`** (149O.18A's own suite): one
  stale assertion updated (`test_no_repository_identity_fails_closed` →
  `test_no_repository_identity_and_no_activation_evidence_is_legacy`,
  corrected expectation) plus two new security-property tests
  (`test_no_repository_identity_with_existing_record_fails_closed`,
  `test_no_repository_identity_with_existing_marker_fails_closed`).
  86/87 pass; the sole other failure
  (`test_accept_strict_timestamp[2026-08-08T12:00:00.0Z]`) is pre-existing
  and unrelated (confirmed via `git stash` A/B).

Total new tests this phase: **44** (20 + 24), plus 3 updated/added
assertions in 18A's own suite. All passing.

---

## 15. Regressions

- **`tests/test_agent.py -k rollback`**: 78/78 passed (0 failures) —
  confirmed both before the classified correction (8 failures observed,
  attributed and fixed, §5) and after (0 failures).
- **`tests/test_hatp_rollback_consumption.py`** (18B's own suite): 34/34
  passed, unaffected (module byte-unchanged).
- **`tests/test_permission_broker.py`**: 234/234 passed — no Permission
  Broker behavior changed.
- **`tests/test_phase_149o_18a_...py` / `test_phase_149o_18b_...py`**:
  331/332 passed; the sole failure
  (`TestProductionFileAllowlist::test_only_the_new_cutover_module_was_
  added_to_src_pcae`) is a pre-existing snapshot assertion, confirmed
  identical on the clean 149O.18B baseline via `git stash` (149O.18B's
  own diff against its phase-entry commit already includes two files —
  `hatp_mandatory_cutover.py` and `hatp_rollback_consumption.py` — so
  this 18A-era assertion was already stale before this phase began).
- **Full `-k "149o or hatp"` sweep** (2907 collected, `fido2`
  hardware-dependent collection excluded): A/B-diffed against the clean
  149O.18B baseline via `git stash`. 124 failures pre-existing on the
  baseline (unrelated: timestamp-parser quirks, `fido2` hardware
  dependency, and the same "no `src/pcae/` diff since my own phase-entry
  commit" snapshot pattern every historical HATP-lineage phase test
  carries). Exactly **13 newly-invalidated** by this phase's own diff —
  all of the identical, mechanical "no `src/pcae/` file changed since
  my own baseline" snapshot-assertion pattern 18A/18B's own regression
  sections already documented for themselves (any new `src/pcae/` diff
  necessarily invalidates every earlier phase's own zero-diff snapshot
  check) — plus one governance-gate false-positive
  (`test_pcae_cli_health_and_check_work_with_no_device_attached`,
  attributable to this session's own active task still being the
  post-149O.18B idle placeholder rather than a 149O.18C task file; not a
  HATP/AG3 behavioral regression, resolved by the normal phase-completion
  task-lifecycle transition). No AG3/AG5/rollback/Permission-Broker
  *behavioral* regression was found in either sweep.

---

## 16. Fast Green

`pytest -m fast_green -n auto`:

```
5358 passed, 1 skipped, 12 failed (raw, unfiltered)
```

All 12 raw failures attributed:
- **10 pre-existing, unrelated** (confirmed via `git stash` A/B against
  the clean 149O.18B baseline): `test_python39_z_suffix_defect_repaired_by_
  149o_16_1`, `test_accept_strict_timestamp[2026-08-08T12:00:00.0Z]`,
  `test_exactly_one_production_file_changed_by_149o_16_1`,
  `TestScopeBoundaries::test_no_hmrc_cutover_or_mandatory_consumption_
  module_introduced`, `TestScopeBoundaries::test_no_new_production_files_
  added`, `TestOldHookDispositionAgainstCurrentSource::test_no_hatp_
  mandatory_cutover_module_exists_yet`,
  `TestNoProductionOrContractChangeThisPhase::test_no_production_source_
  modified_this_phase`, `TestNoProductionOrContractMutation::test_no_src_
  pcae_files_changed_name_only`, `TestNoProductionOrContractMutation::
  test_no_src_pcae_files_changed_name_status`,
  `TestProductionFileAllowlist::test_only_the_new_cutover_module_was_
  added_to_src_pcae`.
- **2 necessarily-invalidated by this phase's own production diff**
  (the same mechanical "no `src/pcae/` file changed since my own
  phase-entry commit" pattern): `test_only_expected_production_files_
  changed` (149O.1g), `TestNoProductionSourceModified::test_git_diff_
  against_pre_phase_head_touches_no_src_pcae_or_contract_file` (149O.14).

Deselecting these 12: **5358 passed, 1 skipped, 0 unattributed failed**
(up from 149O.18B's 5270 passed — the delta reflects this phase's 44 new
tests plus 3 updated 18A-suite tests, minus the 12 attributed
deselections' own denominator shift).

---

## 17. Report Trust

- `pcae phase-report reconcile --phase-id 149O.18B`: `status: reconciled`,
  `Mutation: none (inspection only)` (confirmed at phase start, §1).
- `git diff --name-only 5143bb27 -- src/pcae/`: exactly
  `src/pcae/core/agent.py`, `src/pcae/core/hatp_mandatory_cutover.py`.
- `git diff --stat 5143bb27 -- docs/contracts/`: empty for all seven
  upstream contracts (HMRC-001, HSCE-001, HATP-001, RAE-001, RWMPC-001,
  PBPA-001, PBPC-001).

---

## 18. Retained Findings (Unchanged, Non-Blocking)

Shared-single-slot protected-state topology (149O.18A §8); RAE
lookup-key design (149O.18B, `binding_id`-derived, not duplicated here);
HMRC N-1 (149O.16); REQ-080 editorial observation (149O.17);
`149O.12B-Obs-PY39-1` (resolved, 149O.16.2); repository-wide double-Z
timestamp-parser hardening debt (149O.16.2 — this phase's
`hatp_mandatory_cutover.py` correction introduces no new timestamp field
and does not touch the existing timestamp parser). `PY39`: this
repository's own `.venv` remains Python 3.14, not 3.9 — pre-existing,
unrelated, confirmed identically on the clean baseline.

---

## 19. Implementation Verdict

```
AG3 MANDATORY HATP CONSUMPTION INTEGRATION: IMPLEMENTED
— READY FOR 149O.18D
```

`execute_rollback`'s real effect boundary (`_run_git_revert`) now
enforces HMRC-001's Mandatory Consumption Boundary: fresh cutover-mode
resolution, mandatory explicit evidence ID, a fresh 149O.18B real-effect
Consumption Attempt, and a truthful PB `ALLOW` requirement, all evaluated
immediately before the effect, with no caller-reachable bypass (direct
function call, raw-hook parameters, or otherwise) and no dual (legacy OR
HATP) authority. `LEGACY_COMPATIBLE`/`PREPARED` dispatch is unchanged.
AG5, the CLI, and Permission Broker are untouched. Whole-HMRC
implementation is **not** claimed complete — AG5 (18D), CLI evidence-ID
plumbing and legacy-command migration (18E), and the assembled attack
matrix/activation guard (18F) remain. HATP production remains **NOT
READY**. Runtime remains `Observed / observe / unavailable`.

---

## 20. Recommended Next Phase

**149O.18D — AG5 Mandatory Consumption Integration.** Wire fresh
cutover-mode resolution (149O.18A) and the 149O.18B real-effect
Consumption Attempt into `build_rollback_execution`'s effect boundary
(before the first `write_text`/`write_bytes`/`unlink` call in the
`file_plan` loop), mirroring this phase's `execute_rollback` pattern:
`Ag5RollbackApprovalContext`, the same fresh-mode/mandatory-evidence/
real-effect-adapter/truthful-PB-ALLOW ordering, the same direct-call and
raw-hook-bypass protections. No CLI/legacy-migration work in 18D. If
18D's own wiring attempt surfaces the identical
`_resolve_cutover_mode_at_root` identity-absent question, it is already
resolved by this phase's classified correction (§5) — no repeat
investigation needed, since the correction lives in the shared
`hatp_mandatory_cutover.py` module both AG3 and AG5 consume identically.

---

## 21. Explicit Confirmations (Restated for the Phase Report)

`src/pcae/core/agent.py` was modified (the AG3 effect-boundary wiring,
plus two pre-existing `read_git_branch` type-mismatch bug fixes
discovered while exercising it, §12). `src/pcae/core/
hatp_mandatory_cutover.py` was modified — a narrow, classified,
single-hunk correction to `_resolve_cutover_mode_at_root`'s
identity-absent branch, fully documented in §5, required to satisfy
HMRC-REQ-032 for the real current deployment; every identity-present code
path is byte-identical to 149O.18A. `src/pcae/core/
hatp_rollback_consumption.py` (149O.18B) remained byte-unchanged.
HMRC-001 v1.0, HSCE-001 v1.1, HATP-001 v1.0, RAE-001 v1.0, RWMPC-001
v1.0, PBPA-001 v1.0, and PBPC-001 v1.2 all remain byte-unchanged. No AG5
mandatory-consumption integration was implemented. No
`--hatp-evidence-id` rollback CLI plumbing was implemented. No legacy
`pcae remote rollback approve` command behavior changed. No Permission
Broker behavior changed. `POL-005` remains unchanged. No `COMP-002`
capability was implemented. No Cutover Record or activation marker was
created or modified in any real production protected store (this
deployment has no provisioned Class-B protected root at all, consistent
with `pcae runtime inspect`'s `Observed`/`observe`/`unavailable` status).
No real `HATP_MANDATORY` activation occurred. Current `LEGACY_COMPATIBLE`
behavior for this real deployment is unchanged end-to-end (§5, §15).
B-149O-1..4 remain **INDEPENDENTLY VERIFIED AT THE HATP-GATED AUTHORITY
BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED**, unchanged by this phase.
HATP production remains **NOT READY**. Runtime remains `Observed /
observe / unavailable`.
