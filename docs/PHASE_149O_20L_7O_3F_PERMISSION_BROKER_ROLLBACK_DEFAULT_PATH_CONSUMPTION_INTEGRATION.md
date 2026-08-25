# Phase 149O.20L.7O.3F — Permission Broker Rollback Default-Path Consumption Integration

**Status:** COMPLETE
**Phase type:** BOUNDED SOURCE-MODIFYING INTEGRATION.
**Phase-entry commit:** `97bb9cda` (HEAD at phase start; `origin/main..HEAD` = 0; working tree clean).
**Repository:** `~/repos/pcae-harness`. **Out of scope, not inspected:** `~/repos/pcae-deepseek-research`. **Article track:** STOPPED — not read, not modified, not published.
**Human priority selection:** Plan B (Permission Broker rollback-gap closure), selected from `149O.20L.7O.3E`'s three candidates.

## 1. Objective

Close the sole remaining Permission Broker production-coverage gap identified by `149O.20L.7O.3E` Section 7: the `pcae rollback` default (non-`HATP_MANDATORY`) dispatch path had zero Permission Broker evaluation at all, unlike every other root-mutating production command (push, commit, promotion, publication).

## 2. 3E finding (re-derived, not trusted)

`149O.20L.7O.3E` Section 7's mutation matrix cited: `build_rollback_execution` (`src/pcae/core/agent.py`), sole production caller `commands/agent.py:16264` (`run_rollback`), had zero `mutation_permission`/`permission_broker` references in its default dispatch branch. This phase independently re-read `build_rollback_execution` at current HEAD and confirmed the finding is exact and unchanged: the function's `HATP_MANDATORY`-branch gate (`hatp_rollback_consumption.evaluate_for_real_effect`, Phase 149O.18D) is the *only* Permission Broker evaluation in the function, and it only runs when `resolve_production_hatp_cutover_mode(root).mode == CutoverMode.HATP_MANDATORY` — which this deployment does not currently resolve to (`LEGACY_COMPATIBLE`). The `else` branch (the actual default path on this and every current deployment) proceeds directly into the file restore/remove loop with no permission evaluation whatsoever.

## 3. Pre-integration rollback call graph

```
pcae rollback --per-id X [--dry-run] [--hatp-evidence-id]
  → run_rollback()                         [commands/agent.py:16263]
      → build_rollback_execution()          [core/agent.py:94095]
          → PER lookup / eligibility / rollback_payload_available checks
          → ECP lookup
          → in-progress conflict check
          → divergence check
          → dry_run? → return (zero mutation, zero broker call) — UNCHANGED
          → RER created/persisted (status="in_progress" or "aborted_divergence")
          → divergence blocking? → return — UNCHANGED
          → if HATP_MANDATORY:
                → hatp_rollback_consumption.evaluate_for_real_effect()  [BROKER-GATED, HATP-integrated, pre-existing]
                → deny → return, zero mutation
          → else (DEFAULT PATH — every current real deployment):
                → **[GAP: no Permission Broker call at all]**
          → restore/remove loop (real filesystem mutation)          [effect boundary]
```

A separate, structurally distinct AG3 mechanism (`execute_rollback`, job-based `git revert`) has the identical shape (its own `HATP_MANDATORY`-only broker gate, zero coverage on its default path) but is out of this phase's scope — 3E's finding and this phase's mandate are both scoped to AG5 (`build_rollback_execution`, PER-based), the entry point `pcae rollback --per-id X` actually invokes.

## 4. Effect boundary

The effect boundary is the restore/remove loop beginning at the line following the (pre-existing, untouched) `HATP_MANDATORY` gate block: `full_path.write_text(...)` / `full_path.write_bytes(...)` / `full_path.unlink()`. Everything before it (PER/ECP lookup, eligibility checks, divergence check, RER creation) is preparation/readiness, not effect, and is unchanged.

## 5. Existing policy applicability

`ACTION_ROLLBACK` and `EXECUTION_CLASS_ROLLBACK` already exist in `permission_broker_foundation.py`'s known vocabulary (`KNOWN_ACTION_TYPES`/`KNOWN_EXECUTION_CLASSES`), previously consumed only by the separate HATP-gated AG3/AG5 advisory evaluation in `hatp_ag_authority.py`. No new action-type or execution-class vocabulary was invented.

Critically, `EXECUTION_CLASS_ROLLBACK` is one of the four execution classes `MissingHumanApprovalRule` (POL-004) applies to; `EXECUTION_CLASS_MUTATION` — the class every pre-existing Wave-1 adapter (commit/promotion/publication) uses — is explicitly excluded from POL-004. Using `EXECUTION_CLASS_ROLLBACK` for this new adapter would have caused POL-004 to trigger `HUMAN_REVIEW` unconditionally (since no `approval_present` evidence concept exists for the default path), permanently blocking every default-path rollback and inventing a new human-approval requirement this phase's brief explicitly forbids ("do not invent Permission Broker policy," "do not change human authority"). The new adapter therefore reuses `EXECUTION_CLASS_MUTATION` (identical to every existing Wave-1 adapter) paired with the existing `ACTION_ROLLBACK` literal — a combination `UnknownCapabilityRule` (POL-006) already accepts (it checks `action_type` and `execution_class` membership independently), and which resolves purely on POL-001 (active task)/POL-003 (evidence)/POL-006/POL-007 — matching the "Result: ALLOW/DENY" (no HUMAN_REVIEW) shape 3E's own E2E design (§15) specified for this candidate.

## 6. Permission Broker integration seam

New adapter `evaluate_rollback_permission()` added to `src/pcae/core/mutation_permission.py`, mirroring `evaluate_publication_permission()`'s shape exactly: constructs one request via the shared `evaluate_repository_mutation_permission()` primitive, `action_type=ACTION_ROLLBACK`, `execution_class=EXECUTION_CLASS_MUTATION`, `requested_component="COMP-008"` ("Rollback Boundary" — the same component id `hatp_ag_authority.py` already registered for AG5), `requested_capability="build_rollback_execution"` (the same literal `hatp_ag_authority.resolve_ag5_gated_rollback_authority` already uses), `evidence_available=True`, `approval_present=False`, `simulation_only=True`. No new decision state, no new policy vocabulary, no rollback-specific shadow broker — one centralized `PermissionBroker` remains authoritative.

The call site is in `build_rollback_execution` (`src/pcae/core/agent.py`), placed immediately after the pre-existing (untouched) `HATP_MANDATORY` gate block and immediately before the restore/remove loop, guarded by `if resolve_production_hatp_cutover_mode(root).mode != CutoverMode.HATP_MANDATORY:` — so it governs only the previously-unguarded default (legacy/prepared) path and never runs inside the `HATP_MANDATORY` branch, which keeps its own separate, stricter, HATP-integrated gate completely untouched (HATP is trust-blocked in this phase's No-Go list).

## 7. Post-integration call graph

```
pcae rollback --per-id X [--dry-run]
  → run_rollback() → build_rollback_execution()
      → ... unchanged preconditions ...
      → dry_run? → return (zero mutation, zero broker call) — UNCHANGED
      → RER created; divergence blocking? → return — UNCHANGED
      → if HATP_MANDATORY:
            → evaluate_for_real_effect()  [UNCHANGED, untouched]
      → else (DEFAULT PATH):
            → mutation_permission.evaluate_rollback_permission()   [NEW]
                → PermissionBroker().evaluate(request)
                → ALLOW  → continue to restore/remove loop (unchanged behavior)
                → DENY / broker failure / malformed result
                    → record["status"] = "aborted_permission_denied"
                    → RER persisted (terminal, rollback_executed=False)
                    → return {"error": "rollback_permission_denied", ...denial details...}
      → restore/remove loop                                        [effect boundary, ALLOW-gated on default path]
```

## 8. Operation identity

Bound to the existing canonical PER/ECP identifiers already resolved inside `build_rollback_execution` (`per_id`, `ecp_id` from the already-looked-up ECP record) plus the currently active task (`find_latest_active_task(root)`, the same source every pre-existing commit/promotion adapter uses) — never CLI text, filename, timestamp, or git-history heuristics. `requested_resource` is `f"per:{per_id};ecp:{ecp_id}"`.

## 9. ALLOW

Verified (`test_real_allow_permits_default_path_rollback`, `test_real_allow_permits_both_default_modes`): with an active task present (the only precondition POL-001/POL-003/POL-006/POL-007 impose here), the broker returns `ALLOW` and dispatch proceeds exactly as before this phase — file restored/removed, RER completed, `reverted=True`. ALLOW is a permission gate passed, not an execution-capability activation: runtime remains `Observed`/`observe`/`unavailable` throughout (§16).

## 10. DENY

Verified (`test_deny_blocks_default_path_rollback`, `test_missing_active_task_denies_default_path_rollback`, `test_repeated_denied_attempts_stay_zero_mutation`): a forced `DENY` (or a real `DENY` from a missing active task, POL-001) returns `{"error": "rollback_permission_denied", "permission_decision": "DENY", ...}`, zero file mutation, a terminal `aborted_permission_denied` RER persisted. Repeated denied attempts remain zero-mutation and idempotent (no duplicate effects, no partial dispatch).

## 11. HUMAN_REVIEW

`EXECUTION_CLASS_MUTATION` structurally cannot trigger POL-004 (§5), so a real `HUMAN_REVIEW` cannot occur on this path in current production code — this phase does not invent one. `test_human_review_does_not_auto_confirm_default_path_rollback` and `test_execution_class_mutation_never_triggers_pol004_for_rollback` verify both the structural guarantee and that the caller-side handling would still correctly treat a (forced, non-production) `HUMAN_REVIEW` as non-authorized rather than translating it into a completed dispatch, if the policy registry were ever amended in a future phase.

## 12. Broker failure

Verified (`test_broker_failure_blocks_default_path_rollback`, `test_malformed_broker_result_blocks_default_path_rollback`): a raised exception from `PermissionBroker.evaluate` or a malformed (`None`) result both produce `permission_decision == "BROKER_FAILURE"`, zero mutation — fail-closed, matching the shared `evaluate_repository_mutation_permission` primitive's existing exception-boundary discipline (no new handling was written; the existing Wave-1 primitive is reused as-is).

## 13. No fallback

There is no code path from a denied/failed broker evaluation back into the restore/remove loop — the `if not rollback_permission_result.authorized:` branch returns unconditionally. Verified indirectly by every DENY/broker-failure test asserting `added.txt` still exists with its original content.

## 14. No-bypass

- Top-level entry point: `pcae rollback --per-id X` → `run_rollback` → `build_rollback_execution` — the only CLI surface for this mutation.
- `test_single_production_caller_of_build_rollback_execution` (re-run in this phase's own suite): `build_rollback_execution` has exactly one production caller anywhere in `src/pcae` (`commands/agent.py:16264`).
- No other production code duplicates the restore/write logic (`grep -rn "store_rollback_execution_record\|_rer_check_divergence\|_pxr_hash_file"` outside `core/agent.py` returns nothing).
- The carried-forward dead-code path 3E flagged (`core/rollback_approval_evidence.py::create_rollback_approval_decision`, which calls `PublicationCoordinator.execute()` directly) was re-confirmed still dead this phase (definition + `__all__` export only, zero production callers) — unrelated to AG5's rollback effect boundary in any case (it is a governance-document-publication helper, not a file-restore path).
- `test_no_self_cli_subprocess_in_new_adapter_or_gate`: AST-level check that neither the new adapter nor `build_rollback_execution` invokes `subprocess.run`/`Popen` with `"pcae"` as the first argument.

## 15. Rollback readiness/evidence compatibility

`dry_run=True` returns before reaching the `HATP_MANDATORY` check entirely (unchanged code path, unchanged line position) and therefore never reaches the new gate — verified explicitly (`test_dry_run_bypasses_broker_entirely_even_under_forced_deny`, `test_dry_run_readiness_unaffected_by_missing_task`): dry-run rollback preview/evidence generation remains available with **zero** broker/task precondition, exactly as before this phase, even when the broker would deny or no task is active.

## 16. Human authority

Rollback remains 100% human-initiated via the explicit `pcae rollback --per-id X` CLI invocation — the broker adds a machine-checked authorization gate on an already-human-initiated action, not a new human step, and does not replace it. The pre-existing, separate HATP-gated advisory evaluation (`hatp_authority`, populated only when `--hatp-evidence-id` is supplied) is untouched and remains additive-only/non-gating on the default path, exactly as before.

## 17. Runtime result

`pcae runtime inspect` before and after this phase: `Observed / observe / unavailable`, byte-identical. A broker `ALLOW` on the default path permits only the already-existing, already-narrow rollback dispatch behavior that existed before this phase (restoring/removing exactly the files `PER.file_results` recorded) — it activates no new execution capability, expands no rollback scope, and does not touch the `Permission Broker status: execution_unavailable` / `Governance posture: non-executing` runtime facts.

## 18. Audit/evidence

The broker decision's outcome is reflected in the existing RollbackExecutionRecord (RER) mechanism: a denial persists a genuine terminal RER (`status="aborted_permission_denied"`, `rollback_executed=False`) via the existing `store_rollback_execution_record`/`_rer_validate` machinery — no new canonical artifact was added. `"aborted_permission_denied"` was added to the existing closed `_RER_VALID_STATUSES` vocabulary (mirroring the precedent `"aborted_hatp_mandatory_denied"` set in Phase 149O.18D) so the record is genuinely persisted (`_rer_validate` rejects storage of a record with an unregistered status) rather than silently failing to store. Verified: `test_denial_persists_terminal_rer_record`.

## 19. Restart/idempotency

Repeated denied attempts against the same PER remain zero-mutation and produce no duplicate/partial effect (`test_repeated_denied_attempts_stay_zero_mutation`) — each attempt creates its own fresh RER (existing per-attempt `rer_id` generation, unmodified) and the underlying file is never touched. The mechanical divergence-conflict gate (pre-existing) still runs, and still short-circuits, before the new permission gate (`test_divergence_conflict_still_blocks_before_permission`) — the broker is never reached for an already-blocked-by-divergence attempt, matching the existing `evaluate_promotion_permission` precedent's identical gate ordering.

## 20. Production diff scope

Exactly two production files changed:

- `src/pcae/core/mutation_permission.py` — one new adapter function (`evaluate_rollback_permission`) plus its two supporting module-level constants (`_ROLLBACK_COMPONENT`, `_ROLLBACK_CAPABILITY`) and a docstring update to the file's header noting the one narrow Wave-1-style exception this phase adds; appended after the existing publication adapter, no existing function modified.
- `src/pcae/core/agent.py` — one new `if` block inside `build_rollback_execution`, inserted after the (untouched) `HATP_MANDATORY` gate block and before the restore/remove loop; one new entry added to the existing closed `_RER_VALID_STATUSES` frozenset. No existing line inside the `HATP_MANDATORY` branch, the PER/ECP/divergence preconditions, or the restore/remove loop itself was modified.

One test file was updated for compatibility (`tests/test_ag5_hatp_mandatory_consumption.py`, comment-only — its shared fixture already created an active task as a pre-existing Phase 149F side effect of `_init_git_root`, so no functional change was needed there once traced). One new test file was added (`tests/test_phase_149o_20l_7o_3f_rollback_permission_broker_default_path.py`, 21 tests). No unrelated cleanup was performed.

## 21. Tests

New file `tests/test_phase_149o_20l_7o_3f_rollback_permission_broker_default_path.py` (21 tests, all `fast_green`): real-ALLOW positive control (both `LEGACY_COMPATIBLE`/`PREPARED`), broker-invocation identity spy (action/execution-class/component/capability/resource/task), DENY, broker-exception failure, malformed-result failure, missing-active-task DENY, forced-HUMAN_REVIEW non-auto-confirm, POL-004/`EXECUTION_CLASS_MUTATION` structural exclusion, no-partial-file-results-on-deny, dry-run-bypasses-broker-entirely (even under forced DENY / missing task), `HATP_MANDATORY`-path-never-invokes-new-adapter, terminal-RER-persistence-on-denial, repeated-denial idempotency, divergence-conflict-precedes-permission ordering, sole-production-caller re-confirmation, no-self-CLI-subprocess AST check, gate-source-position check, dry-run-readiness-unaffected-by-missing-task, and rollback/promotion/publication operation-identity distinctness.

## 22. Regressions

- **Rollback regressions** (`tests/test_ag5_hatp_mandatory_consumption.py`, `tests/test_hatp_cli_migration.py`, `tests/test_phase_149o_18d_ag5_mandatory_consumption_integration.py`): 22 + 120 = 142 passed unmodified in behavior (the `test_phase_149o_18d_...` file has 5 pre-existing failures, confirmed present identically on the phase-entry commit via `git stash` before/after comparison — unrelated frozen-diff/contract-byte-identity tripwires from that historical phase, not caused by this phase).
- **Permission Broker Foundation / push / publication / policy / hard-block regressions** (21 files, 983 non-new tests): 983 passed, 2 pre-existing failures (`test_permission_broker_consumer_scope_inventory`, `test_actual_git_push_dispatch_site_in_core_agent_remains_unwired`), both confirmed present identically before this phase via `git stash` comparison — unrelated to rollback, caused by a pre-existing `permission_broker_foundation` import string already present in `core/agent.py`'s HATP module before this phase touched anything.
- **Full Fast Green baseline-vs-current node-ID delta** (§23): 19 newly-failing node IDs, all independently confirmed non-functional (frozen source-diff/git-status tripwires from unrelated historical phases, or `-n auto` parallel-execution flakiness on shared real-host-state fixtures, confirmed by serial re-run passing 3/3). Zero functional/behavioral regressions.
- **Cross-consumer distinctness**: `ACTION_ROLLBACK` remains distinct from `ACTION_SOURCE_MUTATION`/`ACTION_DOCS_MUTATION`; `_ROLLBACK_CAPABILITY` ("build_rollback_execution") is distinct from `_PROMOTION_CAPABILITY`/`_PUBLICATION_CAPABILITY` — push/promotion/publication/rollback remain four separate operation identities, no leakage (`test_rollback_operation_identity_distinct_from_promotion_and_publication`).
- **Architecture-policy**: the new adapter lives in `core/mutation_permission.py` (the canonical zone for non-`push` mutation-permission construction, per RWMPC-001), not in the `commands` layer; the gate call site in `core/agent.py` is a thin call into that adapter, not inline policy logic.

## 23. Fast Green

Baseline (phase-entry commit `97bb9cda`, via `git stash`): `337 failed, 8690 passed, 5 skipped, 9 errors` (`-m fast_green -n auto`).
Current (this phase's diff applied, working tree, uncommitted at measurement time): `354 failed, 8694 passed, 5 skipped, 9 errors`.

Exact failed/error node-ID delta (`comm` on sorted `FAILED`/`ERROR` lines from two full untruncated runs):

- **19 newly failing**, all in one of two independently-confirmed non-functional categories:
  1. Frozen "no `src/pcae` file touched/changed/dirty since this historical phase's own entry commit" self-checks in 12 unrelated older phases' own test suites (e.g. `test_phase_149o_1g_hatp_proof_models_canonical_serialization.py::test_permission_broker_untouched`, `test_phase_149o_17_hmrc_implementation_plan_completeness.py::...test_no_src_pcae_files_changed_name_only`, several `test_git_status_touches_no_src_pcae...`/`test_no_src_pcae_files_dirty_in_working_tree` variants). These are archival tripwires asserting "no phase after mine will ever touch this file again" — necessarily triggered because this phase's entire mandate is to modify `core/agent.py` and `core/mutation_permission.py`. The `git-status`-based variants are additionally uncommitted-working-tree artifacts that clear once this phase's commits land. This is the same pre-existing category already responsible for the baseline's 337 failures (confirmed identical mechanism via direct inspection of each new failure's assertion).
  2. 3 `-n auto` parallel-execution flakes on shared real-host-state HMIC/hac-dell fixtures (`test_activate_on_unknown_id_fails_closed` / `test_unknown_certification_id_rejected` in three unrelated Class-B phase files) — confirmed flaky, not caused by this phase's diff, by re-running all three serially: `3 passed in 0.06s`.
- **2 newly passing** (baseline-only failures not reproduced in the current run) — confirmed to be the same class of `-n auto` flakiness (parametrized `test_hatp_mandatory_certification_models.py` cases), not attributable to this phase.

**Attributable functional/behavioral regressions: 0.**

## 24. Public v0.4.0 isolation

`v0.4.0` tag (`ea3f731e`), GitHub Release, and PyPI artifacts were not touched. No new release, no version change, no tag operation occurred in this phase.

## 25. Deferred candidates

Unchanged from `149O.20L.7O.3E`, not implemented in this phase: runtime preflight disclosure (Plan A), rollback readiness/evidence auto-generation (Plan A), Repository Intelligence → push/phase wiring (Plan C), Advisory-Context → Advisory core wiring (Plan C), Runtime Enforcement consumption (trust-blocked).

## 26. Trust-blocked / No-Go areas untouched

HATP (`hatp_mandatory_cutover.py`, `hatp_ag_authority.py`, `hatp_rollback_consumption.py`, and the entire `HATP_MANDATORY` branch of `build_rollback_execution`) — byte-unchanged, confirmed via `git diff` scoped to those files/branch. HMIC, Class-B authority, CLTR cutover, runtime execution activation, Telegram inbound, backend/model execution — not touched, not investigated. Dell host — not mutated. `~/repos/pcae-deepseek-research` — not inspected. Article — remains STOPPED, not read, not modified, not published. No new Permission Broker decision state, policy vocabulary, or rollback-specific shadow broker was invented; no rollback capability was expanded beyond the pre-existing dry-run-safe/PER-eligible scope; no human authority was changed; no version was changed.

## 27. Independent verification requirement

This phase does not self-certify the integration complete. Per the governing brief's mandatory follow-up:

**Recommended next phase: 149O.20L.7O.3F.1 — Independent End-to-End Rollback Permission-Boundary Verification.**

3F.1 must independently: re-derive the rollback production graph; locate the actual effect boundary; prove the broker is reached from the highest-level rollback path (`pcae rollback --per-id X`); attempt direct-helper bypass; verify ALLOW; verify DENY; verify broker failure; verify human-gate independence; verify runtime-capability independence; verify readiness/evidence remain usable; test restart/idempotency; rerun existing push/publication Permission Broker consumers; adjudicate all findings. This phase's own test suite (§21) is a first-party verification pass, not a substitute for 3F.1's independent one.

## 28. Verdict

```text
PERMISSION BROKER ROLLBACK DEFAULT-PATH CONSUMPTION:
IMPLEMENTED

DEFAULT ROLLBACK EFFECT PATH:
BROKER-GOVERNED

ALLOW:
VERIFIED

DENY:
VERIFIED

BROKER FAILURE:
FAIL-CLOSED

NO-BYPASS:
IMPLEMENTATION TESTED

ROLLBACK READINESS/EVIDENCE:
PRESERVED

HUMAN AUTHORITY:
PRESERVED

RUNTIME:
Observed / observe / unavailable

ATTRIBUTABLE REGRESSIONS:
0

INDEPENDENT VERIFICATION:
MANDATORY NEXT
```

Recommended next phase: **149O.20L.7O.3F.1 — Independent End-to-End Rollback Permission-Boundary Verification.** Not begun in this phase.
