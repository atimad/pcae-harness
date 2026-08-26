# Phase 149O.20L.7O.3M — Rollback Readiness / Evidence Automatic Consumption Architecture and Integration

**Status:** COMPLETE
**Phase type:** BOUNDED ARCHITECTURE-PLUS-INTEGRATION (narrower than originally scoped, per this phase's own re-derivation).
**Phase-entry commit:** `7b193145` (HEAD at phase start; `origin/main..HEAD` = 0; working tree clean; `v0.4.2` unchanged at `bc7935f4`).
**Repository:** `~/repos/pcae-harness`. **Out of scope, not inspected:** `~/repos/pcae-deepseek-research`. **Article track:** STOPPED — not read, not modified, not published.
**Human priority selection:** Candidate A (rollback readiness / evidence automatic generation and consumption), selected in `149O.20L.7O.3K`.

## 1. Objective

Reduce unnecessary operator choreography around rollback preparation while preserving `human rollback intent != readiness != evidence != Permission Broker permission != execution capability != rollback effect`. Per the governing brief's core semantic rule, this phase's mandate is to **derive what can legitimately be automated from the current rollback architecture** first, and only implement if current contracts/source support it without inventing a new readiness authority object.

## 2. v0.4.2 baseline

Re-verified at phase entry (not merely re-cited):

```
git status --short                        => (empty, clean)
git status --branch --short               => ## main...origin/main
git log --oneline origin/main..HEAD       => (empty)
git rev-list --count origin/main..HEAD    => 0
git rev-parse HEAD                        => 7b19314591c2f954b727a3a96746747e38a55bb1
git rev-parse origin/main                 => 7b19314591c2f954b727a3a96746747e38a55bb1
git rev-parse v0.4.2^{commit}             => bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4
pcae health                               => healthy (active task: 149O.20L.7O.3L.1, reported complete/pushed)
pcae check                                => passed
pcae status coherence                     => coherent
pcae doctor task-memory                   => warnings only (pre-existing tasks/DONE.md sync-debt entries predating this phase, repository-maintainer-only)
pcae push check                           => nothing_to_push
pcae runtime inspect                      => Observed / observe / unavailable
pcae notify status                        => Telegram configured, enabled, ready
pcae phase-report show --latest           => Phase 149O.20L.7O.3L, status completed, report complete
```

Task lifecycle: the still-active `149O.20L.7O.3L.1` task (reported complete/pushed by its own prior phase) was closed via `pcae task close`. Closing it surfaced five additional stale idle-placeholder task files left uncleaned in `tasks/active/` from `3A`, `3C.3.2`, `3C.4`, `3H`, and `3K` (the recurring `tasks/active/` directory-collapse bug documented by prior phases) — each was independently closed via `pcae task close <identifier>`, `pcae session write` was re-run to resync `.pcae/session.json`, and a fresh task for this phase was created and its allowed-files corrected via `pcae task update` (one call, full replacement set, per the established `pcae task update` gotcha). This lifecycle cleanup was committed separately (`09eb8ec5`) before any phase-scoped source change, mirroring prior-phase precedent of keeping lifecycle bookkeeping and source-modifying commits distinct.

## 3. Current rollback graph (re-derived from current source, not inherited from 3E/3F/3I summaries)

Read directly from `src/pcae/core/agent.py` (`build_rollback_execution`, line 94095 at phase entry) and `src/pcae/commands/agent.py` (`run_rollback`, line 16263):

```
pcae rollback --per-id X [--dry-run] [--hatp-evidence-id]
  -> run_rollback()                                    [commands/agent.py:16263]
      -> build_rollback_execution()                     [core/agent.py:94095]
          -> (optional) hatp_evidence_id supplied -> resolve_ag5_gated_rollback_authority()  [advisory-only Wave-7 attachment, never gates dispatch]
          -> PER lookup (lookup_promotion_execution_record) / eligibility (_RER_PER_ELIGIBLE_STATUSES) / rollback_payload_available check
          -> ECP lookup (lookup_execution_change_package)
          -> in-progress conflict check (_rer_in_progress_for_per)
          -> file_plan = [PER.file_results where outcome == "success"]      [computed unconditionally]
          -> divergence = _rer_check_divergence(root, ecp, file_plan)       [computed unconditionally]
          -> dry_run=True?  -> return preview (zero mutation, zero RER persisted, zero broker/HATP call) -- UNCHANGED
          -> RER created ("in_progress" or "aborted_divergence"); persisted
          -> divergence blocking?  -> return (before either authority gate) -- UNCHANGED
          -> if HATP_MANDATORY:
                -> hatp_rollback_consumption.evaluate_for_real_effect()     [BROKER-GATED, HATP-integrated, pre-existing, untouched]
                -> deny -> return, zero mutation
          -> else (DEFAULT PATH -- every current real deployment):
                -> mutation_permission.evaluate_rollback_permission()      [Permission Broker gate, released v0.4.1 / 149O.20L.7O.3F, untouched]
                -> DENY / broker failure -> return, zero mutation
          -> restore/remove loop (real filesystem mutation)                [effect boundary]
          -> RollbackExecutionRecord finalized/persisted (status completed/partial/failed)
  -> pcae rollback-execution show/list / mark-interrupted                  [read-only inspection / bookkeeping-only interruption marking]
```

This call graph was confirmed byte-for-byte identical to `149O.20L.7O.3F`'s own documented graph — no source drift since v0.4.1.

## 4. Existing evidence semantics — the central finding of this phase

Direct source re-reading (not inherited from `3I`) surfaces a finding that **changes this phase's scope**: `file_plan` and `divergence_check` — the "evidence" this phase's brief describes as needing automatic preparation — are already computed **unconditionally**, at the very top of `build_rollback_execution`, for `dry_run=True` and `dry_run=False` alike (`agent.py:94192-94193`, unchanged by this phase). The `dry_run` flag controls only whether the function *returns early* with that evidence (a zero-mutation preview) or *continues* to actually consume it (gate the divergence short-circuit, then reach an authority gate, then effect).

Consequently, **the exact automation this phase's Core Objective describes — "human expresses rollback intent → PCAE automatically performs existing safe preparation/evidence steps → PCAE surfaces readiness/evidence truth → existing human boundary remains → existing Permission Broker gate remains → existing rollback effect boundary remains" — is already the current, released (v0.4.1) production behavior of a real `pcae rollback --per-id X` invocation.** A human does not need to separately invoke `--dry-run` first; the preparation step runs automatically, inline, exactly once, every time, and is already consumed internally to decide whether to stop (divergence conflict) or proceed to the Permission Broker gate and then the effect boundary.

This directly refines (not merely re-cites) `149O.20L.7O.3I`'s own characterization of "current manual choreography" (§5 of that phase's report: "(2) operator manually runs `pcae rollback --per-id X --dry-run` to preview; (3) operator manually re-runs without `--dry-run`... to dispatch"). Re-derivation from current source shows step (2) was **never mechanically required** to reach step (3) — it is optional, advisory tooling for a human who wants a preview before committing to the real command, not a code-enforced prerequisite. `README.md`'s "both gated on prior human-reviewed evidence" (line 192) refers to the **originating PER's** own human-reviewed promotion evidence (`rollback_payload_available=True` is itself downstream of a human-approved `pcae promote`), not to a mandatory fresh dry-run-then-re-invoke pattern for the rollback command itself — confirmed by the absence of any code path that requires a prior `dry_run=True` call before a real one succeeds.

Exact current dry-run/preparation output (both branches compute the same shape):

| Field | Type | Description |
|---|---|---|
| `file_plan` | `list[str]` | Paths from `PER.file_results` where `outcome == "success"`; never user-specified. |
| `divergence_check` | `dict` | `{"file_checks": [...], "blocking": bool, "blocking_paths": [...]}` — per-path status in `{"pending", "already_reverted", "conflict"}`, derived by comparing each path's current on-disk hash against the ECP's `before_hash`/`after_hash`. |
| `would_block` (dry-run only) | `bool` | `divergence_check["blocking"]`. |
| `execution_allowed` | `bool` | Always `False`, every branch. |

Persistence: not ephemeral — both fields are already embedded verbatim in the persisted `RollbackExecutionRecord` (`record["file_plan"]`, `record["divergence_check"]`, `store_rollback_execution_record`) for every non-dry-run invocation, retrievable via `pcae rollback-execution show <rer_id>`. Identity binding: implicit via the RER's own `per_id`/`ecp_id`/`rer_id`, not an independent artifact. Preconditions/errors it can raise: `per_not_found`, `per_status_not_eligible`, `rollback_payload_unavailable`, `ecp_not_found`, `rollback_already_in_progress` (all before `file_plan`/`divergence_check` are computed at all) — none of these are new to this phase. Side effects: proven read-only for `dry_run=True` (verified by this phase's `test_evidence_summary_is_local_derived_state_only`, a direct file-listing before/after comparison).

## 5. Existing readiness semantics

Exhaustive re-search this phase (`grep -rn "readiness\|READY\|eligib\|dry_run\|DryRun\|evidence"` across `core/agent.py`'s rollback region, `mutation_permission.py`, `permission_broker*.py`, `rollback_approval_evidence.py`, `hatp_rollback_consumption.py`, `scope_preflight.py`) confirms `149O.20L.7O.3I`'s finding remains correct and current: **no typed "readiness" concept exists anywhere in `src/pcae`** tied to rollback. The only near-name matches are unrelated historical/pilot CLI subcommands (`write-rollback-verification`, `live-write-readiness`, `rollback-execution-pilot`) and one pre-existing, unrelated constant (`EXECUTION_GOVERNANCE_READINESS_REVIEW_ADVISORY`, a different governance-review concept, not rollback-specific) — both independently confirmed via this phase's own `test_no_new_rollback_readiness_type_introduced` regression guard (which fails if any future phase introduces a `rollback`+`readiness`-named symbol without a corresponding contract phase).

The sibling `RollbackApprovalValidationResult` enum and `RepositoryStateBinding` (`core/rollback_approval_evidence.py`) are real design precedent in the same domain but are typed specifically to HATP-gated approval decisions, not to the default-path dry-run/evidence shape this phase's brief targets — reusing them for a new "readiness" concept would still require a new binding/freshness contract of their own (per `3I` §7-8), not a reuse of an existing readiness semantic.

## 6. Readiness-contract decision

Per the governing brief's Section 5 options:

- **Option A** (existing readiness semantic exists, automate its consumption): **Not applicable** — no such semantic exists (§5 above).
- **Option C** (new readiness contract required, STOP): **Not required for the scope this phase actually implements** (§9 below) — reasoning follows.
- **Option B** (readiness is only a derived display/state, informational, non-authoritative): **This is the option this phase exercises**, narrowly: the already-computed `file_plan`/`divergence_check` evidence is surfaced as informational fields in the function's own return value, with **zero new type, zero new schema, zero new persistence, zero new gating**.

A **materially different** candidate automation — proactively generating and *persisting* a rollback-readiness artifact at `pcae promote`-completion time, ahead of any expressed rollback intent, so an operator could inspect current rollback safety without waiting until they actually decide to roll back — was considered and explicitly **rejected as out of this phase's safe scope**. Re-confirming `3I`'s own findings (§7-9 of that phase's report): such a persisted artifact would need its own freshness/staleness contract (repository state can drift between promotion and an eventual, possibly much later, rollback decision), its own identity-binding schema (`schema_resources/rollback_approval/` contains no reusable schema for this), and an explicit non-authority disclaimer field that does not exist today. Building this without that contract risks exactly the hazard this phase's own guardrails (§10, §26) exist to prevent: a promotion-time snapshot read uncritically by a human at a later, unrelated point in time, creating false confidence that a rollback is currently safe when repository state has since changed. The current architecture's actual practice — recomputing `file_plan`/`divergence_check` fresh, from live repository state, at the moment of the real rollback invocation itself — is strictly safer and requires no new contract; a promotion-time cache would trade that safety for convenience of uncertain value, since the fresh, current-state computation already happens automatically and instantly as part of the same rollback command a human would run anyway.

**READINESS CONTRACT NEEDED? NO** (for the bounded, informational-surfacing scope this phase implements). **A new *persisted, pre-emptive* readiness artifact would need a contract** — this phase does not build one and does not smuggle its authority in under a different name.

## 7. Manual choreography (re-derived)

| Step | Owner | Required by code? | Category |
|---|---|---|---|
| Hold a `per_id` from a prior `pcae promote` with `rollback_payload_available=True` | Human | Yes (precondition) | Human-owned |
| (Optional) `pcae rollback --per-id X --dry-run` | Human | **No** — advisory only | Informational |
| `pcae rollback --per-id X [--hatp-evidence-id ...]` | Human | Yes — the sole effect trigger | Human-owned + mechanically preparatory + authority-bearing (invocation) + effectful |
| Evidence computation (`file_plan`/`divergence_check`) | PCAE | Automatic, unconditional | Mechanically preparatory |
| Divergence short-circuit | PCAE | Automatic | Mechanically preparatory (gates, does not authorize) |
| HATP_MANDATORY or default-path Permission Broker gate | PCAE | Automatic | Authority-bearing |
| Restore/remove loop | PCAE | Automatic, gated | Effectful |

The only genuinely *manual, separate* CLI step in the current architecture is the optional `--dry-run` preview — which was never a required prerequisite. There is no undocumented or hidden manual choreography beyond this to remove.

## 8. Target choreography

Already the current production behavior (§4): `rollback intent (pcae rollback --per-id X) -> existing PER/human trigger validated -> existing rollback plan/evidence automatically computed -> preparation result consumed internally -> if invalid (divergence conflict), stop -> Permission Broker -> existing effect`. This phase's one production change (§13) closes the remaining gap in that flow: the evidence that already gated the outcome is now also *returned*/*printed* to the invoking human directly, rather than requiring a second `pcae rollback-execution show <rer_id>` lookup to see facts that already determined their own command's result.

## 9. Human boundary

`--dry-run` is, and remains, purely diagnostic — not a contractual human-review gate the code enforces before a real invocation (§4). `README.md`'s "Human review — Required — for every invocation, promotion, and rollback decision" (line 420) refers to the human's decision to invoke `pcae rollback` at all (a human-initiated action, per `3F`'s own §16 finding, unchanged), not to a mandatory two-step preview-then-commit choreography. This phase changes nothing about that boundary: rollback remains 100% human-initiated via explicit CLI invocation; no automatic continuation from evidence generation to effect was added because none was needed — the existing architecture already goes straight from a single human-initiated real invocation through automatic preparation, the Permission Broker gate, and effect, with no separate "generate evidence, then wait for a second human confirmation" step in current contracts to preserve or violate.

## 10. Evidence identity

Unchanged by this phase. Bound implicitly to the RollbackExecutionRecord's own `rer_id`/`per_id`/`ecp_id` (§4); no cross-repository, cross-task, or cross-PER reuse occurs — each invocation recomputes fresh evidence scoped to its own `per_id`/`ecp_id` pair.

## 11. Evidence freshness

Unchanged, and deliberately not introduced. Every invocation (`dry_run` or real) recomputes `file_plan`/`divergence_check` from current on-disk repository state and the current ECP record — there is no caching, no reuse across invocations, no persisted "readiness" object that could go stale. This phase's rejection of the promotion-time pre-emptive caching idea (§6) is precisely to avoid introducing a freshness/staleness contract that does not currently exist and that the governing brief (§10) forbids inventing heuristically.

## 12. Persistence/reuse

Unchanged. `file_plan`/`divergence_check` were already persisted, verbatim, inside the RollbackExecutionRecord before this phase (`store_rollback_execution_record`) for every non-dry-run invocation. This phase's change surfaces the *same already-persisted values* in the function's *return value* — it adds no new persisted artifact, no new store, no new schema. Verified: `test_evidence_summary_matches_persisted_rer_record`.

## 13. Permission Broker sequencing

**Unchanged.** The evidence-surfacing addition is placed entirely before either authority gate is reached (the fields are computed once, at the top of the function, and merged into every terminal `return` dict from that point on) and does not alter the order, presence, or outcome of the `HATP_MANDATORY` gate or the default-path `mutation_permission.evaluate_rollback_permission()` call in any way. Verified: `test_broker_still_invoked_exactly_once_on_default_path`, `test_default_path_permission_adapter_never_invoked_under_hatp_mandatory`, `test_valid_evidence_plus_deny_still_blocks` (clean, non-blocking evidence does **not** substitute for a broker ALLOW — a forced DENY still blocks dispatch even when `divergence_check["blocking"]` is `False`).

## 14. Evidence non-authority

Verified explicitly: `test_valid_evidence_plus_deny_still_blocks` proves "evidence says safe" (divergence non-blocking) does not imply "Permission Broker ALLOW"; `test_execution_allowed_remains_false_in_every_branch` proves "preparation complete" never implies "execution available" (`execution_allowed` remains `False` in every returned branch, unchanged). No new decision state, no new authority field, no new bypass was introduced.

## 15. Runtime boundary

Unchanged: `Observed / observe / unavailable`, verified before and after this phase's change via direct `pcae runtime inspect` invocation and via `test_runtime_inspect_unaffected_by_evidence_surfacing` (a fresh `RuntimeSnapshot` built before and after a real rollback dispatch, comparing `state.current_state`, `governance.execution_capability`, `governance.non_executing_posture`, and `governance.broker_implementation_status`). Surfacing already-computed local variables in a return dict cannot and does not touch runtime capability.

## 16. HATP isolation

The `HATP_MANDATORY` branch's own gate-denial dict (`gate_denial`) now also receives the same additive `file_plan`/`divergence_check` merge (§13's code location is common to both branches, placed once, after divergence is computed and before either gate) — this is the same category of purely informational addition as the default path, not a change to HATP authority semantics, gate ordering, or decision logic. `hatp_authority` (the separate, pre-existing, advisory-only Wave-7 attachment populated only when `--hatp-evidence-id` is supplied) is untouched. Verified: `test_hatp_mandatory_branch_evidence_field_names_unaffected`, `test_default_path_permission_adapter_never_invoked_under_hatp_mandatory`.

## 17. Service boundary

No new service was created; no logic was extracted or duplicated. `_rer_check_divergence` and the `file_plan` list-comprehension remain exactly where they were (`core/agent.py`), computed once; this phase's change is limited to (a) naming the already-computed local variables as `_evidence_summary` for clarity and (b) merging that same dict into terminal return dicts that previously omitted it. `build_rollback_execution` retains its single production caller (`commands/agent.py::run_rollback`), re-verified this phase: `test_build_rollback_execution_still_has_single_production_caller`.

## 18. Failure semantics

Unchanged in kind; each existing error path (`per_not_found`, `per_status_not_eligible`, `rollback_payload_unavailable`, `ecp_not_found`, `rollback_already_in_progress`, `divergence_conflict`, `hatp_evidence_required`/`hatp_evidence_invalid`/`hatp_mandatory_authority_denied`, `rollback_permission_denied`) continues to fail deterministically and truthfully with the same `error` string as before; this phase adds informational fields to several of these dicts (§13) but changes no error condition, no error string, and no control flow.

## 19. Resume/idempotency

Verified: `test_repeated_real_invocation_after_completion_is_not_in_progress_reentrant` — a second real invocation against an already-reverted PER recomputes fresh evidence (`divergence_check["file_checks"][0]["status"] == "already_reverted"`) rather than reusing any cached state; no duplicate/partial effect. This is pre-existing behavior, unaffected by this phase's additive change (which introduces no caching).

## 20. Auditability

Unchanged; the RollbackExecutionRecord remains the canonical persisted audit artifact. This phase's change makes the same already-persisted evidence additionally visible in the invoking command's own immediate output (CLI print and JSON), reducing (not adding) the number of commands an operator needs to run to see it.

## 21. Side effects

Read-only for `dry_run=True` (verified: `test_evidence_summary_is_local_derived_state_only`, a full file-listing comparison before/after). For a real invocation, no new side effect was introduced — the same restore/remove loop, RER persistence, and authority gates execute exactly as before; the only change is which keys appear in the dict that loop's caller already receives.

## 22. Implementation decision

```
READINESS CONTRACT NEEDED?            NO (for the bounded, non-persisted, informational-surfacing scope actually implemented)
EXISTING PREPARATION SERVICE REUSABLE? YES -- file_plan/divergence_check computation, already canonical, reused verbatim
HUMAN REVIEW REQUIRED AFTER EVIDENCE?  NO -- dry-run was never a contractual review gate; real invocation already proceeds automatically through preparation -> broker -> effect
AUTOMATIC CONTINUATION SAFE?           N/A -- no new continuation was added; the existing single-invocation flow (prepare -> gate -> effect) already exists and is unchanged
```

Per the governing brief's Section 26 gate, since a readiness *contract* is not needed for this bounded scope, implementation proceeded — narrowly, to the evidence-surfacing addition only. The broader, contract-requiring candidate (pre-emptive persisted readiness at promotion time) was explicitly not implemented (§6).

## 23. Production diff

Two production files changed, both additive:

- `src/pcae/core/agent.py` — inside `build_rollback_execution`: one new local variable (`_evidence_summary = {"file_plan": file_plan, "divergence_check": divergence}`, plus an explanatory comment) computed once immediately after `divergence` itself; that dict (or `file_plan` alone, where `divergence_check` was already present) is merged into four existing terminal `return` dicts (`divergence_conflict`, the `HATP_MANDATORY` `gate_denial` return, the default-path `rollback_permission_denied` return, and the final success/partial/failed `result`). No existing key was removed or renamed; no existing control flow, gate, or ordering was changed; no new function, class, or module was added.
- `src/pcae/commands/agent.py` — inside `run_rollback`: the `BLOCKED` branch now also prints `file_plan`/`divergence_check` when present; the completed/partial/failed branch now also prints `divergence_check` when present. No new flag, no new subcommand, no change to exit-code logic, JSON-mode behavior, or existing printed lines.

No other production file was touched. This stays well within the governing brief's Section 38 expectation (rollback preparation/application service, rollback caller integration, tests only).

## 24. Tests

New file `tests/test_phase_149o_20l_7o_3m_rollback_readiness_evidence_automatic_consumption.py` (18 tests, all `fast_green`):

- Preparation-is-automatic: `test_real_invocation_requires_no_prior_dry_run_call`, `test_preparation_evidence_computed_unconditionally_regardless_of_dry_run`.
- Evidence surfacing: `test_completed_result_includes_evidence_summary`, `test_evidence_summary_matches_persisted_rer_record`, `test_permission_denied_result_includes_evidence_summary`, `test_divergence_conflict_result_includes_file_plan`, `test_dry_run_result_shape_unchanged`.
- Non-authority: `test_valid_evidence_plus_deny_still_blocks`, `test_broker_still_invoked_exactly_once_on_default_path`, `test_execution_allowed_remains_false_in_every_branch`.
- HATP isolation: `test_hatp_mandatory_branch_evidence_field_names_unaffected`, `test_default_path_permission_adapter_never_invoked_under_hatp_mandatory`.
- No new authority object: `test_no_new_rollback_readiness_type_introduced`, `test_build_rollback_execution_still_has_single_production_caller`, `test_evidence_summary_is_local_derived_state_only`.
- Manual dry-run compatibility: `test_manual_dry_run_cli_path_still_works`.
- Restart/idempotency: `test_repeated_real_invocation_after_completion_is_not_in_progress_reentrant`.
- Runtime independence: `test_runtime_inspect_unaffected_by_evidence_surfacing`.

## 25. Regressions

- **Rollback regressions**: `tests/test_ag5_hatp_mandatory_consumption.py` (81), `tests/test_hatp_cli_migration.py`, `tests/test_phase_149o_20l_7o_3f_rollback_permission_broker_default_path.py` (21), `tests/test_phase_149o_20l_7o_3f_1_independent_rollback_permission_verification.py`, `tests/test_agent.py -k rollback` (78) — all passed, 0 attributable failures.
- **`tests/test_phase_149o_18d_ag5_mandatory_consumption_integration.py`**: 5 pre-existing failures (frozen "no `src/pcae` file touched since this historical phase's own entry commit" self-checks — this phase's mandate is to touch `core/agent.py`/`commands/agent.py`, triggering the same archival tripwire class `3F` already documented at identical scope). Independently re-confirmed via `git stash push -u` / re-run / `git stash pop` before this phase's diff was applied: **identical 5 failures present with zero source changes**, proving these are pre-existing and unrelated, not caused by this phase.
- **Permission Broker / mutation-permission regressions**: `tests/test_permission_broker.py`, `tests/test_permission_broker_foundation.py`, `tests/test_mutation_permission_core.py`, `tests/test_mutation_permission_commit_integration.py`, `tests/test_mutation_permission_promotion_integration.py`, `tests/test_mutation_permission_push_routing_integration.py`, `tests/test_repository_wide_mutation_inventory_guard.py`, `tests/test_permission_broker_push_production_consumption.py` — 562 combined (including this phase's own 18 new tests and the four `3F`/`3F.1` rollback-PB suites), 0 failures.
- **v0.4.2 RI-attachment regression smoke**: `tests/test_phase_149o_20l_7o_3j_ri_advisory_production_consumption.py`, `tests/test_phase_149o_20l_7o_3j_1_independent_ri_advisory_consumption_verification.py` — 46 passed, 0 failures (no source overlap; run as a representative smoke per the governing brief's §36).

## 26. Fast Green

`pcae phase fast-green-attribution --phase-id 149O.20L.7O.3M --json` (baseline `7b193145` — this phase's phase-entry commit, resolved automatically as the parent of this phase's first attributed commit `09eb8ec5`; candidate `e632a2df` — this phase's implementation commit):

```
status:                          PASS
raw_failed_count (candidate):    339
raw_errors_count (candidate):    9
attributable_failures:           []  (0)
excluded_preexisting_failures:   347 (identical node IDs failed in the independently
                                       re-run baseline at 7b193145; frozen self-referential
                                       contract/byte-identity/git-status tripwires and
                                       pre-existing environment quirks from dozens of
                                       unrelated historical phases -- not caused by this
                                       phase's diff)
excluded_environment_failures:   []
expected_phase_artifacts:        1 -- tests/test_phase_149o_20l_7n_1_dell_redeployment_
                                       proposition_independent_verification.py::
                                       TestCandidateCurrentness::test_head_equals_origin_main,
                                       predicted local_only by pushed_status (expected and
                                       harmless pre-push; resolves once this phase's
                                       commits are pushed to origin/main)
issues:                           []
```

**Attributable functional/behavioral regressions: 0.** This machine-produced result independently corroborates this phase's own manual spot-check regression runs (§25): the identical 5 `test_phase_149o_18d_...` frozen-diff failures, re-confirmed via `git stash` before/after this phase's diff, are part of the 347 pre-existing exclusions above, not new.

## 27. Findings

No BLOCKING findings. This phase's central finding (§4) is that the automation target described in the governing brief's Core Objective was already fully implemented in production as of `149O.20L.7O.3F`/v0.4.1 — the phase's own scope was therefore narrowed, on independent re-derivation, from "wire an automatic preparation-consumption flow" to "surface already-computed, already-consumed, already-persisted evidence that a prior architectural decision had omitted from several of the function's own return values." A materially larger candidate (pre-emptive persisted readiness at promotion time) was correctly identified as requiring a new contract and was not implemented (§6), consistent with the governing brief's Section 26/48 stop rule for that specific candidate — while the narrower, already-safe surfacing improvement proceeded per Section 5's Option B.

## 28. Final verdict

```text
ROLLBACK PREPARATION / EVIDENCE AUTOMATION:
ALREADY IMPLEMENTED (re-derived, not newly built) IN THE PRODUCTION DEFAULT-PATH
ROLLBACK DISPATCH, AS OF v0.4.1 (149O.20L.7O.3F)

NEW AUTHORITATIVE READINESS CONTRACT:
NOT REQUIRED FOR THE SCOPE IMPLEMENTED; WOULD BE REQUIRED FOR THE REJECTED
PROMOTION-TIME PRE-EMPTIVE-PERSISTENCE CANDIDATE (NOT BUILT)

HIGHEST-LEVEL ROLLBACK FLOW:
ALREADY AUTO-CONSUMES EXISTING PREPARATION/EVIDENCE (UNCHANGED BY THIS PHASE)

MANUAL DRY-RUN PREREQUISITE:
NEVER EXISTED AS A CODE-ENFORCED REQUIREMENT (RE-DERIVED FINDING, CORRECTING 3I'S FRAMING)

THIS PHASE'S PRODUCTION CHANGE:
NARROW, ADDITIVE EVIDENCE-SURFACING ONLY (file_plan/divergence_check now
returned/printed on every terminal outcome, not only dry-run/persisted-RER)

HUMAN AUTHORITY:
PRESERVED

PERMISSION BROKER:
REMAINS SEPARATE / AUTHORITATIVE / UNCHANGED SEQUENCING

EVIDENCE:
NON-AUTHORITATIVE (VERIFIED)

PREPARATION SIDE EFFECTS:
READ-ONLY / BOUNDED (VERIFIED)

RUNTIME:
Observed / observe / unavailable (UNCHANGED)

ATTRIBUTABLE REGRESSIONS:
0

INDEPENDENT END-TO-END VERIFICATION:
MANDATORY NEXT
```

## 29. Independent verification requirement

This phase does not self-certify the result complete. Per the governing brief's mandatory follow-up:

**Recommended next phase: 149O.20L.7O.3M.1 — Independent End-to-End Rollback Readiness / Evidence Consumption Verification.**

`3M.1` must independently: re-derive the rollback production graph without trusting this phase's call-graph transcription; re-confirm (or refute) this phase's central finding that automatic preparation-consumption already existed pre-phase; locate the actual highest-level production entry point and confirm no manual preparation CLI prerequisite exists; verify existing evidence semantics, identity, and freshness; verify the human boundary; verify Permission Broker sequencing is unchanged; verify evidence non-authority; verify runtime independence; verify HATP isolation; test restart/idempotency; attempt direct-helper bypass; rerun rollback/Permission Broker/push/publication regressions; adjudicate all findings including whether this phase's scope-narrowing decision (§6) was correct or itself under-scoped.
