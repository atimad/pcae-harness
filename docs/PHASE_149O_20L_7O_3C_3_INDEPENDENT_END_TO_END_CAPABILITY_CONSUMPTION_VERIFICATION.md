# Phase 149O.20L.7O.3C.3 — Independent End-to-End Capability Consumption Verification

**Status:** VERIFICATION COMPLETE — **ONE BLOCKING FINDING**. Verification-only; no production source modified.
**Phase-entry commit:** `9139a2bb` (HEAD at phase start; `origin/main..HEAD` = 0; working tree clean; `pcae health` healthy, `pcae check` passed, `pcae status coherence` coherent, `pcae push check` nothing_to_push, `pcae runtime inspect` Observed/observe/unavailable).
**3C.2 commits independently inspected:** `f4556d76` (Governed Capability Consumption Integration, the production diff), `280ff8b2` (docs/status), `2b92a6f6` / `90deba98` (task-lifecycle bookkeeping only).
**Repository:** `~/repos/pcae-harness`. **Out of scope, not inspected:** `~/repos/pcae-deepseek-research`. **Article track:** STOPPED — not read, not modified, not published.
**Canonical authority used:** `PROJECT_STATUS.md`; no conflict with `tasks/TODO.md` encountered.

## 1. Methodology

Per the governing brief's "RE-DERIVE, DO NOT TRUST" instruction, 3C.2's own report, tests, and consumer-graph claims were treated as unverified assertions to be independently re-derived from current source, not as evidence. Verification used four independent techniques, each applied directly against the currently-committed source at phase-entry HEAD:

1. **Direct source reading** of every file in the `f4556d76` diff (`git show --stat --summary` + full diffs), not the phase document's prose description of it.
2. **Live execution of real production code** in short, throwaway Python REPL sessions against the actual classes (`SessionCoordinator`, `SessionApplicationService`, `PublicationApplicationService`, `PublicationCoordinator`, `mutation_permission.evaluate_publication_permission`, `PermissionBroker`) — not mocks, not the 3C.2 test suite.
3. **A fresh, independent pytest suite** (`tests/test_phase_149o_20l_7o_3c_3_independent_e2e_verification.py`, 22 tests, all passing) built from scratch with its own fixtures/harness class, importing zero test functions from `tests/test_phase_149o_20l_7o_3c_2_governed_capability_consumption_integration.py`.
4. **Repository-wide static re-derivation**: `git grep`-based full-repo scans for every claimed "single call site" / "no bypass" / "no self-CLI" assertion, and a direct re-run of the actual AST-based architecture-zone dependency scanner (`pcae.core.architecture.analyze_changed_python_dependencies`) against the 3C.2 diff's `.py` files.

This phase did not attempt a full subprocess-level `pcae phase complete` CLI black-box E2E in a disposable git repository (items 26-32 of the governing brief, in their most literal form) — that would require standing up a complete governed repository scaffold (agent lock, task lifecycle, `.pcae/` state) purely to exercise code this phase could exercise directly and more precisely by calling the real production service objects (`auto_publish_confirmed_session`, `publish_with_permission_gate`) with the same inputs `run_phase_complete` supplies them. §4 documents the exact call-site proof this substitutes. This is a disclosed scope reduction, not a silent omission — a follow-up repair/verification phase should still perform a literal subprocess-level E2E once the Blocking finding in §7 is repaired, since that finding is specifically about behavior at the `run_phase_complete` call boundary itself.

## 2. Pre-3C.2 historical behavior (reconstructed from the diff, not from current comments)

Read directly from `git show f4556d76`'s `-` (removed) / context lines against `src/pcae/commands/phase.py`, `governance_record.py`, `decision_session.py`, `interactive_workflow/application/session_service.py`, `interactive_workflow/session/coordinator.py`:

- **`pcae phase complete` knew nothing about Interactive Workflow.** No reference to `decision_session`, `SessionApplicationService`, or any session/CHGR concept existed anywhere in `phase.py` before this diff.
- **The human had to invoke `decision-session readiness` and `governance-record publish` manually** to move a `Confirmed` session's readiness package into a published CHGR — `governance_record.py::run_governance_record_publish` called `context.publication_service.resume_publication(package_id, operator_id=operator_id)` directly, with no Permission Broker involvement at all.
- **CHGR publication had zero Permission Broker coverage.** `mutation_permission.py` had three existing adapters (commit, alternate-push, promotion) before this diff; no publication adapter existed.
- **`SessionCoordinator` had no `list_session_ids()`** and `SessionApplicationService` had no `find_session_by_subject_ref()` — there was no way to look up a session by an external subject identity at all; a caller needed the session id itself.
- **Active-task behavior:** `find_latest_active_task(root)` was not called anywhere in `run_phase_complete` before this diff.

## 3. Current production call graph (independently traced)

```
pcae phase complete (CLI)
  -> run_phase_complete(args)                          [src/pcae/commands/phase.py]
       active_task_before_completion = find_latest_active_task(root)   [pcae.core.tasks]
       finalizable = _finalize_report_and_notify(...)   [unchanged pre-existing gate]
       if finalizable and active_task_before_completion is not None:
           agent_lock = read_agent_lock(root)
           outcome = auto_publish_confirmed_session(     [pcae.commands.governance_auto_publication]
               build_application_context(),               [pcae.commands.decision_session — existing composition root]
               subject_ref=active_task_before_completion.task_id,
               operator_id=agent_lock.agent_id or "unknown-agent",
           )
             -> find_confirmed_session(session_service, subject_ref)
                  -> SessionApplicationService.find_session_by_subject_ref(subject_ref)
                       -> SessionCoordinator.list_session_ids() -> FilesystemSessionRepository.list_session_ids()
                       -> SessionCoordinator.load_session(id) [per id] -> FilesystemSessionRepository.load(id)
             -> [state routing; only SessionState.CONFIRMED continues]
             -> PublicationApplicationService.ensure_readiness_package(session_id, caller_identity=operator_id)
                  -> SessionApplicationService.require_bound_identity  (fails closed on identity mismatch)
                  -> find_readiness_package_for_session / construct_readiness_package [existing, unmodified]
             -> publish_with_permission_gate(publication_service, root, package_id, operator_id=operator_id)
                                                          [pcae.commands.publication_permission_gate]
                  -> PublicationApplicationService.prepare_publication_request(package_id)   [existing, unmodified]
                  -> find_latest_active_task(root)         [pcae.core.tasks — reused, not reinvented]
                  -> mutation_permission.evaluate_publication_permission(root, session_id, package_id, task_id)
                       -> mutation_permission.evaluate_repository_mutation_permission(...)   [existing primitive]
                            -> permission_broker_foundation.build_permission_broker_request(...)
                            -> PermissionBroker().evaluate(request)  -> PolicyRegistry (POL-001..012)
                  -> [authorized == False] -> raise PublicationPermissionDeniedApplicationError (no hand_off call)
                  -> [authorized == True]  -> PublicationApplicationService.hand_off(prepared, operator_id)
                                                -> PublicationCoordinator.execute(package, event)  [existing, unmodified]
       if finalizable: complete_phase(root, args.summary)   [unchanged pre-existing lock release / provenance]
```

| Module | Function | Input | Output | Side effect | Authority role | Failure behavior |
|---|---|---|---|---|---|---|
| `pcae.core.tasks` | `find_latest_active_task` | repo root | `Task \| None` | none (read) | none | returns `None`, never raises for "no task" |
| `pcae.commands.governance_auto_publication` | `auto_publish_confirmed_session` | context, subject_ref, operator_id | `AutoPublicationOutcome` (closed vocabulary) | may publish a CHGR | orchestration only — never confirms/authorizes | **catches `ApplicationServiceError` subclasses only** — see §7 |
| `pcae.interactive_workflow.application.session_service` | `find_session_by_subject_ref` | subject_ref | `Session \| None` | none (read, full scan) | none | raises `SessionStoreCorruptError`/`PersistenceUnavailableError` (uncaught by caller — §7) on any corrupt/unreadable session file encountered during the scan, even one unrelated to `subject_ref` |
| `pcae.interactive_workflow.application.publication_service` | `ensure_readiness_package` | session_id, caller_identity | `PendingReadinessRecord` | may persist a new readiness package | verifies identity binding (fails closed) | raises typed `ApplicationServiceError` subclasses, all caught by the caller |
| `pcae.commands.publication_permission_gate` | `publish_with_permission_gate` | publication_service, root, package_id, operator_id | `PublicationExecutionResult` | may publish a CHGR | **the** non-bypassable gate | raises `PublicationPermissionDeniedApplicationError` on any non-`ALLOW` decision or broker failure — fail-closed, no fallback |
| `pcae.core.mutation_permission` | `evaluate_publication_permission` / `evaluate_repository_mutation_permission` | root, session_id, package_id, task_id | `MutationPermissionResult` | none (simulation_only=True) | Decision Consumption Point | catches all `Exception` from broker construction/evaluation, returns `authorized=False` |
| `pcae.core.permission_broker_foundation` | `PermissionBroker.evaluate` | request | `PermissionBrokerDecision` | none | policy composition (DENY > HUMAN_REVIEW > ALLOW) | fails closed on malformed request/decision |
| `pcae.governance.publication.coordinator` | `PublicationCoordinator.execute` | package, event | `PublicationExecutionResult` | writes the CHGR record | terminal effect boundary | unchanged from pre-3C.2 |

## 4. Highest-level entry point proof

`git grep -n "auto_publish_confirmed_session(" -- src/pcae` returns exactly two lines: the `def` in `governance_auto_publication.py` and one call in `commands/phase.py::run_phase_complete`. There is no test-only helper standing in for this — `run_phase_complete` is the argparse handler bound to the `phase complete` subcommand (confirmed via `pcae phase complete --help`/CLI dispatch table), i.e. the actual command a human or the governed lifecycle runs. No manual internal CLI choreography is required to reach it: calling `pcae phase complete` alone reaches `auto_publish_confirmed_session` unconditionally whenever an active task exists, with no additional flag or hidden opt-in. **`pcae phase complete` is confirmed to be the real, sole, unconditionally-reached production entry point** for this integration.

## 5. Commands-zone architecture-policy repair — independently reconstructed and re-verified

3C.2's report (§5a) describes an initial draft that placed the Permission Broker call inside `PublicationApplicationService.hand_off()` (`interactive_workflow` zone), rejected by the repository's pre-commit `pcae check` hook because `.pcae/policy.toml`'s frozen `interactive_workflow` zone rule (`interactive_workflow = ["interactive_workflow", "governance", "aesic"]`, Phase 143K) excludes `core`. This rejected draft is not independently re-derivable from git history (it was never committed — a single squashed production commit, `f4556d76`, is all that exists), so this phase verifies the *outcome*, not the rejected intermediate state, by two independent means:

1. **Policy re-read:** `load_policy(root).architecture_rules["interactive_workflow"]` at current HEAD is `("interactive_workflow", "governance", "aesic")` — no `"core"`. `architecture_rules["commands"]` includes both `"core"` and `"interactive_workflow"` — confirming the described target zone can legally hold the dependency the source zone could not.
2. **Direct re-execution of the actual AST-based scanner** (`pcae.core.architecture.analyze_changed_python_dependencies`, the same function `pcae check`'s pre-commit hook calls) against every `.py` file in the `f4556d76` diff, at current HEAD: **zero dependency warnings, zero parse warnings.** This is not "the hook passed" taken on faith — this phase re-ran the identical static-analysis function directly and inspected its structured result.

Final placement verified command-layer/service-layer separation: `governance_auto_publication.py` and `publication_permission_gate.py` (both `commands` zone) contain only orchestration — session lookup, state routing, and delegation to `core.mutation_permission`/`interactive_workflow.application.*` — no governance/business logic is duplicated from those layers (confirmed by reading both files in full; see §3's call graph). No forbidden import direction: `interactive_workflow/application/publication_service.py`, `interactive_workflow/application/session_service.py`, and `interactive_workflow/session/coordinator.py` (all touched by the diff) import nothing from `pcae.core` (re-confirmed by the same AST scan — zero warnings covers these files too, since they were part of the scanned diff). No hidden circular dependency: `commands` -> `core` and `commands` -> `interactive_workflow` are both pre-existing, one-directional, already-frozen edges; nothing in the diff adds a reverse edge. No CLI parsing used as an internal integration API (§6).

## 6. Static self-CLI check

`git grep`/AST-import scan of `governance_auto_publication.py`, `publication_permission_gate.py`, `interactive_workflow/application/session_service.py`, `interactive_workflow/session/coordinator.py`: no `subprocess` import, no `os.system`, no `shell=True`, no construction of a `["pcae", ...]` argv list. `phase.py` and `mutation_permission.py` do use `subprocess` extensively, but exclusively for `git` invocations (ahead-count, log, diff) — all pre-existing, none touched by this diff, none self-invoking `pcae`. **Confirmed via `test_no_self_cli_subprocess_in_integration_modules`.**

## 7. BLOCKING finding — uncaught exception crashes unrelated `pcae phase complete` runs

**This is the phase's central result and was not disclosed anywhere in 3C.2's own report.**

`auto_publish_confirmed_session` catches exactly four exception types, all from the `ApplicationServiceError` hierarchy (`interactive_workflow/application/errors.py`): `PublicationAlreadyCompletedApplicationError`, `PublicationPermissionDeniedApplicationError`, `ReadinessSessionNotConfirmedApplicationError`, and the base `ApplicationServiceError`. Its very first call, `find_confirmed_session` → `SessionApplicationService.find_session_by_subject_ref`, performs a **full scan of every persisted session** (`list_session_ids()` then `load_session(id)` for each), and `load_session`/`FilesystemSessionRepository.load` raise `SessionStoreCorruptError` (on invalid JSON) or `PersistenceUnavailableError` (on an `OSError`) — both members of a **separate, sibling exception hierarchy**, `InteractiveWorkflowError` (`interactive_workflow/errors.py`), that shares no base class with `ApplicationServiceError` other than `Exception` itself. `find_session_by_subject_ref` only catches `SessionNotFoundError` (also `InteractiveWorkflowError`) around the per-id load — a corrupt file's actual exception is not that one, so it propagates.

The call site in `run_phase_complete` wraps the entire auto-publish block in **no try/except at all**. The result: **one corrupted or unreadable file anywhere in the Interactive Workflow session store causes every future `pcae phase complete` invocation to crash**, for any phase, regardless of whether that phase's active task has any relationship to Interactive Workflow, as long as an active task exists (the overwhelmingly common case).

**Independently reproduced twice:**
- A standalone REPL run: create one unrelated session (`subject_ref="unrelated-task-999"`), corrupt its on-disk JSON file, then call `find_session_by_subject_ref` with a *different*, unrelated subject_ref — raises `SessionStoreCorruptError`.
- `tests/test_phase_149o_20l_7o_3c_3_independent_e2e_verification.py::test_corrupted_unrelated_session_file_crashes_auto_publish` (passing — i.e., the exception is confirmed raised, not swallowed) and `::test_run_phase_complete_call_site_has_no_exception_guard_around_auto_publish_block` (statically confirms no `try:` wraps the call in `run_phase_complete`'s current source).

**Why this is Blocking, not Non-Blocking:** the governing brief's own finding-classification examples (item 49) list "phase completion becomes incorrectly blocked for unrelated workflows" as a canonical Blocking example. This finding is strictly worse than "blocked" — it is an unhandled crash — and it is triggered by state (a corrupt file anywhere in the store) that this phase's own scope explicitly contemplates as a required test category ("corrupt-state E2E," items 31/44) and requires to "fail closed," not crash the unrelated production entry point.

**Why the existing regression suite did not catch this:** every existing test exercising `run_phase_complete` (39 tests across 3 files, all still passing — see §17) runs in a fixture environment with either no session store at all or only well-formed session files; none introduces an unrelated corrupted file. This is precisely the "re-derive, do not trust" gap this phase exists to find.

**Recommended narrow repair (not applied in this phase, per the governing brief's "prefer to stop with a narrow repair recommendation" instruction):** wrap the `auto_publish_confirmed_session(...)` call in `run_phase_complete` in a `try/except InteractiveWorkflowError` (or more narrowly, `except (SessionStoreCorruptError, PersistenceUnavailableError)`), printing the same kind of informational diagnostic the `application_error` branch already prints, without raising — mirroring the existing "must not silently continue, but must never gate `finalizable`" contract this module already applies to every other failure mode. This is a small, bounded, single-call-site fix; it does not require touching the Permission Broker, session, or publication logic.

## 8. NON-BLOCKING finding — duplicate `subject_ref` sessions resolved by latest-timestamp, not fail-closed

Independently reproduced (`test_duplicate_subject_ref_sessions_resolved_by_latest_timestamp_not_fail_closed`, and a standalone REPL run creating two sessions with the same `subject_ref` a few milliseconds apart): `find_session_by_subject_ref` sorts matching candidates by `created_at` and returns the last one — a "latest timestamp" resolution, which is exactly the class of heuristic the governing brief's item 14 instructs rejecting, in the one case (duplicate `subject_ref`) where more than one candidate exists. The module's own docstring already discloses this as a known limitation ("a disclosed limitation, not a silently-assumed impossibility"), so this is not an undisclosed defect, but a disclosed heuristic is still a heuristic, and it has a real consequence worth recording: if a session for a given task is already `Confirmed` and published, and a second, later session is later created with the same `subject_ref` (e.g. a mistaken duplicate `decision-session create`) in a non-terminal state, `auto_publish_confirmed_session` will report `awaiting_human_decision` for that task going forward — the earlier, already-published CHGR's identity becomes unreachable through this lookup path (though it remains present and discoverable directly by `package_id`/`session_id` in the record store; nothing is lost, only this specific automatic lookup's view of "the" session for that subject becomes stale). Classified **NON-BLOCKING**: it only manifests under an operator-created duplicate-subject_ref condition the system does not otherwise produce on its own, it never causes a duplicate CHGR or an incorrect publish, and it degrades to "reports the wrong pending state" rather than "publishes incorrectly." Recommended follow-up: `find_session_by_subject_ref` should raise on ambiguity (more than one live/non-terminal candidate) rather than silently picking one, consistent with item 14/15's fail-closed instruction.

## 9. NON-BLOCKING / informational — carried-forward dead path to `PublicationCoordinator.execute()`

`core/rollback_approval_evidence.py::create_rollback_approval_decision` constructs its own `PublicationCoordinator` and calls `.execute()` directly, bypassing `publish_with_permission_gate` and therefore the Permission Broker entirely. This predates 3C.2 (not introduced by it) and was already disclosed in 3C.2's own report §9 as a carried-forward finding. Independently re-confirmed at this phase's HEAD via `git grep -ln "create_rollback_approval_decision(" -- src/pcae`: **the only match is the function's own definition — zero production callers.** `test_rollback_approval_evidence_publication_coordinator_is_currently_unreachable_dead_code` pins this as a regression guard: if this function ever gains a real caller in a future rollback-integration phase, that test will fail, flagging the need to re-verify Permission Broker no-bypass before that phase can be considered clean. Item 21's "critical stop condition" (no production-reachable ungoverned path) is satisfied today because "production-reachable" requires an actual live caller, which does not exist.

## 10. Permission Broker: ALLOW / DENY / failure — verified against real production code, not mocks

- **DENY (natural trigger, not synthetic):** `evaluate_publication_permission(root, session_id, package_id, task_id=None)` against the real `PermissionBroker`/`PolicyRegistry` returns `authorized=False`, `decision_reason="missing_active_task_contract"` (POL-001) — reproduced directly in a REPL and in `test_broker_deny_via_missing_active_task_blocks_publication_and_creates_no_chgr`. With `task_id` set to a real active task, the identical call returns `authorized=True`, `decision="ALLOW"`.
- **Broker internal failure fails closed:** a broker whose `.evaluate()` raises `RuntimeError` produces `authorized=False`, `broker_failure_reason="simulated broker internal failure"` — no fallback to an unbrokered publish path exists (`publish_with_permission_gate` only ever calls `hand_off()` after a `authorized is True` check).
- **No-bypass:** `git grep -n "\.hand_off("` across the entire `src/pcae` tree returns exactly one external call site (`publish_with_permission_gate`) plus `resume_publication`'s own internal `self.hand_off(...)`; `git grep -n "\.resume_publication("` returns **zero** production callers (only its own `def`). Both the manual CLI path (`governance-record publish`) and the automatic path (`pcae phase complete`) reach `hand_off()` exclusively through `publish_with_permission_gate` — confirmed by direct source grep, not by trusting the phase document's claim.

## 11. Human authority preservation — critical stop condition, verified for all nine non-`Confirmed` states

Fresh negative tests (`test_no_automatic_positive_decision_for_any_non_confirmed_state`, parametrized over all nine non-`Confirmed` `SessionState` values) confirm: for every one of `Created`, `EvidenceReady`, `AwaitingDecision`, `AwaitingClarification`, `DecisionSelected`, `AwaitingConfirmation` (→ `awaiting_human_decision`), `Cancelled` (→ `human_rejected`), `Abandoned` (→ `human_deferred`), and `Expired` (→ `readiness_unavailable`), `auto_publish_confirmed_session` returns a `record_id=None` outcome — never fabricates a positive decision, never constructs a readiness package, never reaches the broker or `PublicationCoordinator`. Additionally confirmed (incidentally, while debugging a test fixture): `ensure_readiness_package`'s identity-binding check (`require_bound_identity`, IWC-REQ-022/151, pre-existing and unmodified) genuinely rejects an `operator_id` that does not match the session's bound owner identity — a second, independent layer of human-authority preservation this phase did not need to add, and confirmed still enforced.

## 12. Active-task behavior change

**Before 3C.2:** `find_latest_active_task` was not called in `run_phase_complete` at all.
**After 3C.2:** it is called once, unconditionally, before `_finalize_report_and_notify`/`complete_phase` run, purely to capture `subject_ref` for the (also unconditional, but internally no-op-safe) auto-publish attempt. This value is never used to gate `finalizable` or the exit code — confirmed by reading the full function body: the `if finalizable and active_task_before_completion is not None:` block only ever *prints* and computes `outcome`; `complete_phase()` is called afterward based solely on the pre-existing `finalizable` value, unchanged.

Tested/confirmed via the existing (unmodified, still-passing) regression suite — 39 tests across `test_phase_complete_completion_metadata_shape_136aw.py`, `test_repository_transition_validator_phase_complete_integration.py`, and one other file exercising `run_phase_complete` directly, none of which bind a decision session to their active task, all still pass (§17), confirming ordinary phase completion (no session bound) is unaffected. Compatible with lifecycle contracts and additive **except** for §7's Blocking finding, which is a real, unexpectedly broad consequence of this change (it introduces a new unrelated-failure mode into every phase completion with an active task) despite not being a regression in the *tested* scenarios.

## 13-16. Readiness identity / CHGR discovery / uniqueness / downstream semantics

- **Readiness identity:** `ensure_readiness_package` is idempotent-by-key (existing, unmodified `PublicationApplicationService` behavior) — a second call for the same session returns the existing package, never mints a second one. Confirmed via `test_broker_allow_via_active_task_permits_exactly_the_existing_continuation`'s second-call assertion (`already_published`, identical `record_id`).
- **CHGR automatic discovery:** the `record_id` surfaced by `auto_publish_confirmed_session` is exactly the one `PublicationCoordinator.execute()`/`hand_off()` already produced and persisted under the package's own `package_id`/`session_id` keys (existing `PublicationRecordStore` idempotency-by-key, not re-derived) — no "newest file"/timestamp/title-based discovery of the CHGR itself. (§8's finding is about *session* lookup, one layer upstream of CHGR identity, not CHGR discovery itself.)
- **CHGR uniqueness:** confirmed via the same idempotent-repeat test — one `published` + N `already_published`, one committed record, `PublicationRecordStore` state unchanged across repeats.
- **CHGR downstream semantic use:** classified as **disclosure/orchestration-convenience**, not authority — `auto_publish_confirmed_session` only ever *surfaces* the `record_id` to the caller (`pcae phase complete`'s printed output); it assigns the CHGR no additional authority, does not gate `finalizable`, and does not feed any further automatic action. This matches the governing contract (no governing contract makes CHGR publication a phase-completion precondition, confirmed by reading the full `run_phase_complete` body — the auto-publish outcome is never consulted after the print statements).

## 17. Regressions actually run

- `tests/test_phase_149o_20l_7o_3c_2_governed_capability_consumption_integration.py`, `tests/test_iwc_143o_session_coordination_publication_handoff.py`, `tests/test_phase_145g_decision_session_cli.py`: **117 passed.**
- `tests/test_phase_145g2v_independent_verification.py`, `tests/test_phase_145g1_decision_session_cli_repair.py`, `tests/test_phase_145g2_decision_selection_cli_repair.py`, `tests/test_phase_145h3_independent_verification.py`: **104 passed** — includes `test_genuine_subprocess_e2e_create_through_publish`, a real subprocess-level `pcae decision-session create` → ... → `pcae governance-record publish` CLI E2E (not this phase's addition, but independently re-run here, passing, under the new POL-001-gated publish path). This substantially narrows this phase's §1-disclosed scope reduction: the *manual* publish path now has genuine subprocess-CLI E2E coverage through the Permission Broker gate; only the *automatic* `pcae phase complete`-triggered path lacks an equivalent literal subprocess E2E, which is the follow-up repair phase's recommended addition (§21).
- All 3 files in the repository that call `run_phase_complete` directly (`grep -rl "run_phase_complete\b" tests/`): **39 passed** — confirms ordinary, session-less phase completion is unaffected by 3C.2's change, consistent with §12.
- `tests/test_phase_149o_20l_7o_3c_3_independent_e2e_verification.py` (this phase's fresh suite): **22 passed.**
- Fast Green (`pytest -m fast_green -q`, full suite): run in background against unmodified production source (this phase added only test/doc files); result recorded in the canonical phase-completion report once the run completes.

## 18. Repository Intelligence deferral — independently re-verified

`grep -rn "repository_intelligence\|RepositoryIntelligence" src/pcae/commands/push.py`: **zero matches** — RI is not consumed by `push.py` at current HEAD, consistent with the deferral. The 3C.2 diff itself (`git show f4556d76 --name-only`) touches no file under `src/pcae/repository_intelligence/` or `src/pcae/commands/repository_intelligence.py`, and no file in the diff imports either module (re-confirmed by the same AST scan used in §5, which covers every changed file). **Verdict: DEFERRAL CORRECT — no hidden RI integration occurred, and the underlying re-plumbing-cost argument in 3C.2 §8 (that `push.py`'s freshness-comparison logic is not display-only) is independently corroborated by this phase not finding any drop-in substitution point either.** No new Advisory/RI follow-up candidate is recorded — this phase did not find a genuinely small/low-risk seam that 3C.2 missed.

## 19. Runtime / CLTR / HATP boundary

`pcae runtime inspect`: `Observed / observe / unavailable`, identical before and after this phase's work (no production source changed). No file under `src/pcae/cltr/`, HATP/HMIC/Class-B trust surfaces, shell-gate, or rollback-execution paths appears in the 3C.2 diff or in this phase's own (test/doc-only) changes.

## 20. Findings summary

| # | Finding | Classification |
|---|---|---|
| 1 | Uncaught `SessionStoreCorruptError`/`PersistenceUnavailableError` (an `InteractiveWorkflowError`, not caught by `auto_publish_confirmed_session`'s `ApplicationServiceError`-only except clauses) crashes `pcae phase complete` for any active task whenever any unrelated session file in the store is corrupt/unreadable | **BLOCKING** |
| 2 | `find_session_by_subject_ref` resolves duplicate-`subject_ref` sessions by latest-`created_at`, not fail-closed | NON-BLOCKING (disclosed limitation, independently reproduced, real but narrow consequence) |
| 3 | `rollback_approval_evidence.create_rollback_approval_decision` remains an ungated path to `PublicationCoordinator.execute()`, but is currently dead code | NON-BLOCKING / informational, carried forward (pinned by regression test) |
| 4 | All other re-derived claims in 3C.2's report (entry-point wiring, architecture-zone correction, no-bypass, no-self-CLI, human-authority preservation, active-task-requirement disclosure, RI deferral) | CONFIRMED |

**Blocking finding count: 1.**

## 21. Final verdict

**PLAN B+ CAPABILITY CONSUMPTION: PARTIALLY INDEPENDENTLY VERIFIED — ONE BLOCKING DEFECT FOUND, NOT REPAIRED IN THIS PHASE.**

- Interactive Workflow auto-detect + route: production-consumed, auto-routed, human authority preserved for all nine non-`Confirmed` states — confirmed. Reachable via the unconditional `pcae phase complete` call — confirmed, but that same unconditional call is exactly what makes Finding 1 reachable on every phase completion with an active task.
- CHGR: automatically discovered/consumed at the CHGR-identity layer; uniqueness verified for the normal (non-duplicate-subject_ref) case; §8's narrow duplicate-subject_ref gap is real but non-blocking.
- Publication Execution Ownership: automatically invoked at the governed boundary — confirmed.
- Permission Broker: CHGR/publication-path coverage confirmed non-bypassable for every currently-live production caller — confirmed.
- Repository Intelligence: deferral independently verified correct.
- Manual internal choreography: removed for the connected path (one call reaches the full chain) — confirmed.
- Runtime: unchanged, Observed/observe/unavailable — confirmed.

Per the governing brief's mandatory decision gate (item 57): **one unresolved Blocking finding remains. Do NOT proceed to release-scope/release-hardening work.** Recommend the smallest repair phase: **149O.20L.7O.3C.3.1 — Auto-Publish Corrupt-Store Fail-Closed Repair**, scoped narrowly to wrapping the `auto_publish_confirmed_session(...)` call site in `run_phase_complete` (or the exception handling inside `auto_publish_confirmed_session`/`find_confirmed_session` itself) so a corrupt/unreadable, unrelated session file degrades to a non-fatal, disclosed `application_error`-class outcome instead of crashing phase completion — plus a literal subprocess-level `pcae phase complete` E2E test exercising this exact scenario, and reconfirmation of the duplicate-`subject_ref` fail-closed behavior (§8) as a secondary, optional scope item for the same phase or a follow-up. Only after that repair phase passes should 149O.20L.7O.3C.4 (release scope/version reassessment) be considered.

## 22. Release / reproducible-build carry-forward

v0.3.2 remains NOT RELEASED; no tag, GitHub Release, artifact upload, or PyPI publication occurred this phase. No version was changed. The unpinned-`hatchling` reproducible-build issue remains open and unaddressed, unmodified by this phase, carried forward again to whichever release-hardening phase eventually follows a clean 3C.3.x verification result.
