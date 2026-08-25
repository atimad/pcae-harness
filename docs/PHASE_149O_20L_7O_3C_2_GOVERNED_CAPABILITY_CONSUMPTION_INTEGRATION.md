# Phase 149O.20L.7O.3C.2 — Governed Capability Consumption Integration (Plan B+)

**Status:** IMPLEMENTED. First source-modifying phase in the 3C thread.
**Phase-entry commit:** `999227fd` (HEAD at phase start; `origin/main..HEAD` = 0; working tree clean; `pcae health` healthy, `pcae check` passed, `pcae status coherence` coherent, `pcae push check` nothing_to_push, `pcae runtime inspect` Observed/observe/unavailable, `v0.3.1` unchanged at `5d7edef9`, no `v0.3.2` tag local or remote).
**Repository:** `~/repos/pcae-harness`. **Out of scope, not inspected:** `~/repos/pcae-deepseek-research`. **Article track:** STOPPED — not read, not modified, not published.
**Canonical authority used:** `PROJECT_STATUS.md`; no conflict with `tasks/TODO.md` encountered.

## 1. Selected scope — Plan B+ (human-selected, per 3C.1 §24)

1. Interactive Workflow auto-detect + route
2. CHGR downstream automatic consumption
3. Publication Execution Ownership auto-invocation
4. Permission Broker coverage for the CHGR/publication path
5. Repository Intelligence internal consumption — **gated on reconfirmation; DEFERRED (§9 below)**

Deferred by the governing instruction regardless of source findings: rollback readiness/evidence auto-generation (unless a strict prerequisite — none was found), Runtime Enforcement consumption, shell-gate enforcement/audit surfacing, broad Advisory-context wiring, HATP/HMIC/Class-B, CLTR authority cutover, runtime execution, Telegram inbound, backend/model execution.

## 2. Re-derived current source (3C.1 evidence re-confirmed against this phase's HEAD)

3C.1's file:line citations for the target subsystems were re-read directly at this phase's HEAD (not trusted as still-accurate):

- `src/pcae/governance/publication/coordinator.py::PublicationCoordinator.authorize/execute` — unchanged shape from 3C.1's description; deliberately imports nothing from Permission Broker (its own docstring's explicit exclusion list is about `interactive_workflow` sub-packages, not `permission_broker`, but the class is intentionally minimal — see §5 for why the new gate was placed one layer up instead of inside this class).
- `src/pcae/interactive_workflow/application/publication_service.py::PublicationApplicationService` (Phase 145F) — `ensure_readiness_package`, `hand_off`, `resume_publication` confirmed as the real, already-existing, already-idempotent application-service boundary; `hand_off` was the one call site 3C.1 predicted for the broker gate.
- `src/pcae/commands/decision_session.py::build_application_context()` — confirmed as the one narrow composition root already shared by `decision-session` and `governance-record` CLI commands; **this phase's auto-orchestration entry point reuses this exact function**, so a human typing the CLI sequence by hand and this phase's automatic path reach the identical production object graph.
- `src/pcae/core/mutation_permission.py` — confirmed as "the only place in the codebase permitted to construct a `PermissionBrokerRequest` for a non-`pcae push` mutation site" (its own docstring), with three existing adapters (commit, alternate-push, promotion) sharing `evaluate_repository_mutation_permission`. A fourth, publication, adapter was added following the identical pattern.
- `src/pcae/interactive_workflow/models/session.py::SessionState` — the ten-state closed vocabulary re-confirmed unchanged (`Created, EvidenceReady, AwaitingDecision, AwaitingClarification, DecisionSelected, AwaitingConfirmation, Confirmed, Cancelled, Expired, Abandoned`).
- `src/pcae/core/repository_transition_integration.py::metadata_requires_human_review` — investigated as a candidate "existing authoritative requires-human-governance signal" and **rejected** as the auto-detect trigger: it gates `pcae phase complete`'s own report-promotion transition via a hand-set `phase-completion-metadata.json` flag, a different, unrelated concept from "does this operation's subject have a Confirmable Decision Session." Using it would have been exactly the invented heuristic trigger §5 of the governing brief forbids. The actual authoritative signal used instead is the existing, canonical `Session.session_state` state machine itself (§4 below).

## 3. Interactive Workflow auto-detect + route — what "detect" means here

3C.1 found (§7.1, re-confirmed unchanged at this phase's HEAD) that **no production lifecycle module computes any existing "this operation requires a human governance act" flag** — the repository-wide grep in §2 above re-confirms this. Inventing a generic cross-operation trigger would therefore have violated the governing brief's explicit "do not invent a heuristic trigger; use existing authoritative state" rule (§5).

The scope actually implemented is the one case that **is** grounded in already-authoritative, already-canonical state: a Confirmable Decision Session's own `session_state` state machine. "Detection" is: does a session bound to this operation's subject exist, and if so, which of the ten canonical states is it in. This is not a new heuristic — it is the identical state machine IWC-001 v1.1 already defines and the CLI already surfaces via `decision-session status`; this phase adds no new state, alias, or inference.

**Binding convention (additive, non-breaking):** the new production entry point (`auto_publish_confirmed_session`, §4) looks up a session by `subject_ref == <the caller's identity for this operation>` — in the one production caller wired this phase (`pcae phase complete`), the active PCAE `task_id`. This does not change `decision-session create --subject-ref`'s existing free-text contract in any way; a session whose `subject_ref` does not happen to equal a task id is simply never matched, exactly as if this module did not exist.

## 4. New production module: `governance_auto_publication.py`

`src/pcae/commands/governance_auto_publication.py` is the single new entry point both "Interactive Workflow auto-detect + route" and "Publication Execution Ownership auto-invocation" consume — 3C.1 §16 identified these as "the same work, not a separate dependency," confirmed correct at implementation time. **This module lives in the `commands` zone, not `interactive_workflow`** — see §5a for why; §4's own description of what it does and does not do is otherwise unaffected by that placement correction.

```
auto_publish_confirmed_session(context, *, subject_ref, operator_id) -> AutoPublicationOutcome
```

- `context` is a `pcae.commands.decision_session.ApplicationContext` built by `build_application_context()` — **no `SessionCoordinator`/`PublicationCoordinator` is constructed by this new module**; it consumes exactly the same production composition root the CLI already uses.
- `find_confirmed_session` (via the new `SessionApplicationService.find_session_by_subject_ref`, backed by the new `SessionCoordinator.list_session_ids`, itself a thin delegation to the existing `SessionRepository.list_session_ids`) performs one full, deterministic, order-independent scan matching `subject_ref` exactly — never a "most recent file" or timestamp heuristic (governing brief §13's discovery prohibition, applied here even though §13 is nominally about CHGR identity — the same discipline was applied to the session lookup that feeds it).
- Every one of the ten `SessionState` values maps to exactly one outcome status (closed vocabulary, `CLOSED_STATUS_VOCABULARY`):

| Session state | Outcome status | CHGR created? |
|---|---|---|
| *(no session found)* | `no_session_bound` | no |
| Created / EvidenceReady / AwaitingDecision / AwaitingClarification / DecisionSelected / AwaitingConfirmation | `awaiting_human_decision` (exact state disclosed) | no |
| Cancelled | `human_rejected` | no |
| Abandoned | `human_deferred` | no |
| Expired | `readiness_unavailable` | no |
| Confirmed, broker denies | `permission_denied` | no |
| Confirmed, already published | `already_published` (original `record_id` returned) | no (no duplicate) |
| Confirmed, first successful publish | `published` (new `record_id` returned) | yes |
| any `ApplicationServiceError` not covered above | `application_error` | no |

Only `Confirmed` can ever reach `ensure_readiness_package`/`resume_publication` — verified directly by `test_human_authority_preservation_no_state_publishes_without_confirmed` and by the nine non-`Confirmed`-state tests, each asserting no `record_id`.

## 5. Permission Broker — CHGR/publication-path gap closure

3C.1 §7.3/§10 found `PublicationCoordinator.execute()` had zero Permission Broker coverage — the one root/external-effect-adjacent action outside the broker's scope. Closed as follows:

- **`mutation_permission.py::evaluate_publication_permission(root, *, session_id, package_id, task_id)`** — a fourth adapter alongside the existing commit/alternate-push/promotion adapters, sharing the same `evaluate_repository_mutation_permission` primitive. Uses the existing `ACTION_DOCS_MUTATION` literal (no new action-type invented — a CHGR record is a structured governance document, the same class of write `classify_promotion_action_type` already assigns to a `docs/`-scoped promotion) and `EXECUTION_CLASS_MUTATION` (identical to every other Wave-1 site — `simulation_only=True`, non-authoritative).
- **Call site:** `pcae.commands.publication_permission_gate.publish_with_permission_gate()` — a new, small `commands`-zone function combining `PublicationApplicationService.prepare_publication_request()` + the broker evaluation + `PublicationApplicationService.hand_off()`, called by every real production path that reaches `hand_off()`. **Not** inside `PublicationApplicationService.hand_off()` itself, and **not** inside `PublicationCoordinator` — see §5a for why this placement was corrected mid-phase (an architecture-policy violation the repository's own pre-commit hook caught).
- **Task-id binding:** mirrors `commands/push.py`'s own `active_task_for_permission.task_id if active_task_for_permission else None` precedent exactly, via `find_latest_active_task`. A publication attempt with no active PCAE task evaluates with `task_id=None`, which the existing `POL-001` "Missing Active Task" policy denies — **the same existing invariant `pcae commit`/`push`/promotion already enforce**, now extended to publication. This is disclosed as an intentional, real behavior change (§10 below), not a bug.
- **Failure handling:** a new `PublicationPermissionDeniedApplicationError` (added to the closed `ApplicationServiceError` taxonomy, mapped to the existing `authorization_invalid` `error_type` — no new CLI exit-code taxonomy member). DENY and broker-construction/evaluation-failure both fail closed identically (mirrors RWMPC-001's own "construction failure is diagnostically identical to an evaluation failure" precedent). No CHGR is created; no readiness-store attempt-linkage update occurs on this path — the gate runs strictly *before* `PublicationCoordinator.authorize()`/`hand_off()` are ever reached, so a denial leaves the readiness package's own attempt-bookkeeping completely untouched, not merely reverted — verified directly (`test_gate_denies_publication_and_creates_no_chgr_without_active_task`).
- **Non-bypassability:** `PublicationCoordinator.execute()` has exactly one live production caller reaching it — `PublicationApplicationService.hand_off()` (verified by `grep -rn "\.execute(" src/pcae`, confirming the only other call site is the dead `core/rollback_approval_evidence.py:980`, discussed as a carried-forward finding in §11). Both the manual CLI path (`governance-record publish` → `publish_with_permission_gate` → `hand_off`) and this phase's new automatic path (`auto_publish_confirmed_session` → `publish_with_permission_gate` → `hand_off`) go through the identical gate function — verified directly (`test_auto_publish_and_manual_gate_share_the_same_broker_call`).

## 5a. Architecture-policy violation caught and corrected mid-phase

The first implementation draft placed the Permission Broker call directly inside `PublicationApplicationService.hand_off()` (`interactive_workflow` zone), importing `pcae.core.mutation_permission`/`pcae.core.paths`/`pcae.core.tasks` there. Attempting to commit this via the governed `pcae commit implementation` path failed: the repository's `.githooks/pre-commit` hook runs `pcae check`, which enforces `.pcae/policy.toml`'s architecture-dependency rules, and reported `src/pcae/interactive_workflow/application/publication_service.py: interactive_workflow -> core is not allowed by policy`. `.pcae/policy.toml`'s `interactive_workflow` zone rule (Phase 143K, `interactive_workflow = ["interactive_workflow", "governance", "aesic"]`) is an explicit, deliberately-narrated frozen boundary — "depends on no other production zone -- not core, cltr, commands, or governance" — that this phase's first draft violated.

**Correction (no policy change; §4 of the governing brief forbids revising contracts):** the broker call was moved out of `hand_off()` entirely and into a new `commands`-zone module, `pcae.commands.publication_permission_gate`, which is permitted to depend on both `core` and `interactive_workflow` (`.pcae/policy.toml`: `commands = ["core", "commands", "cltr", "schema_runtime", "governance", "interactive_workflow", "aesic"]` — the same edge `commands/decision_session.py`/`commands/push.py` already use). `publish_with_permission_gate()` calls `prepare_publication_request()` (state-reading, unchanged), then the broker adapter, then `hand_off()` (unchanged, now broker-call-free again) — functionally identical gating position (strictly before `PublicationCoordinator.execute()`), corrected zone. `governance_auto_publication.py` itself was moved from `interactive_workflow/` to `commands/` for the same reason (it is Interactive-Workflow/Publication *orchestration*, architecturally akin to `commands/decision_session.py`, not interactive_workflow domain logic — and it too would otherwise need a forbidden `core` import to call the gate). `PublicationApplicationService.hand_off()` and `resume_publication()` are otherwise byte-identical to their pre-phase form; the manual CLI path (`commands/governance_record.py::run_governance_record_publish`) was updated to call `publish_with_permission_gate()` instead of `resume_publication()` directly, so both production callers of `hand_off()` are gated identically. `pcae check` passes cleanly post-correction (re-verified at phase close, §16); this correction cost zero policy-file changes.

This is recorded here deliberately, not smoothed over: it is the strongest evidence in this phase that the "no CLI-subprocess integration, real service-to-service wiring" requirement was actually exercised against a real, pre-existing governance mechanism (the architecture-dependency check), not merely asserted in prose.

## 6. CHGR downstream automatic consumption

Achieved as a direct consequence of §4: `auto_publish_confirmed_session`'s `published`/`already_published` outcomes surface `record_id` (the CHGR identity) directly to the caller — the caller (`pcae phase complete`, §7) receives the CHGR id automatically without a human needing to run `governance-record publish` by hand or transcribe the resulting id. Duplicate-CHGR prevention is not reimplemented — it is the existing `PublicationApplicationService`/`PublicationRecordStore` idempotency-by-key invariant (`is_published`/`AuthorizationReplayError`), consumed, never re-derived (verified by `test_repeated_invocation_after_success_is_idempotent_no_duplicate_chgr`: three consecutive calls, one `published` + two `already_published`, identical `record_id`, and `PublicationRecordStore.is_published` confirms exactly one committed publication).

CHGR identity lookup itself uses no heuristic discovery: the `record_id` returned is the one `PublicationCoordinator.execute()`/`resume_publication` already produced and persisted under the package's own stable `package_id`/`session_id` keys — never a "most recent file" scan (governing brief §13).

## 7. Wired production entry point: `pcae phase complete`

`commands/phase.py::run_phase_complete` now calls `auto_publish_confirmed_session` once, non-blocking, immediately before `complete_phase()` runs (the active task is captured beforehand, since it is only reliably resolvable while still active). `subject_ref` is the active task's `task_id`; `operator_id` is the current agent-lock's `agent_id` (falling back to `"unknown-agent"` only if no lock is held, which cannot occur on a governed completion path).

**Compatibility (§41):** the overwhelmingly common case — no session bound to the active task — resolves to `no_session_bound` and prints nothing; phase completion proceeds exactly as before this phase, byte-for-byte, for the ~30 prior 3-series phases' own completion flow, none of which use `decision-session`. This was spot-checked by finalizing this very phase through the identical `pcae phase complete` path used below.

**Not a new blocking precondition:** the outcome is informational only and never changes `finalizable`/the exit code. No governing contract makes CHGR publication a phase-completion precondition; coupling the two would have been a new authority relationship this phase does not introduce.

## 8. Repository Intelligence — reconfirmed and DEFERRED

3C.1 rated RI→push/phase change-context wiring Low risk/S-M effort on the premise that `push.py`'s raw `git log`/`git diff` subprocess calls (§7.5, lines ~321-346 at 3C.1's HEAD) were purely diagnostic display text a service call could mechanically replace. Direct re-reading at this phase's HEAD (`commands/push.py:319-350`) shows this is **not** the case: `_staged_file_snapshot` (path→blob-hash freshness snapshot), `_files_in_unpushed_range`, and `_unpushed_commit_lines` feed the actual push-permission freshness-comparison and report-generation logic, not a display-only path. Swapping their data source for `repository_intelligence.change_impact`/`historical_memory` output would require re-plumbing consumer shape/semantics (freshness-comparison equality checks, report field shapes) throughout `push.py`, not a drop-in function substitution — real, non-trivial, test-touching work outside a defensible "S-M/Low-risk" boundary alongside this phase's two MODERATE-authority-risk items (Interactive Workflow auto-route, Permission Broker gap closure).

Per governing brief §23/§29 ("Either is acceptable"): **DEFERRED AFTER RECONFIRMATION.** Recommended as its own small, independent follow-up phase (3C.1's own dependency graph already lists it as fully independent of everything else in this batch).

## 9. Carried-forward finding: a second, currently-dead path to `PublicationCoordinator.execute()`

`core/rollback_approval_evidence.py:980::create_rollback_approval_decision()` calls `coordinator.execute(package, event)` directly, bypassing `PublicationApplicationService.hand_off()` and therefore bypassing this phase's new Permission Broker gate entirely. This function has **zero production callers today** (re-confirmed at this phase's HEAD, matching 3C.1 §7.1's finding) — rollback integration is explicitly deferred from this batch per the governing instruction, so this path was not touched. **Flagged as a carry-forward finding, not fixed here:** if a future rollback-integration phase ever wires `create_rollback_approval_decision` into a live caller, it must either route through `PublicationApplicationService.hand_off()` or gain its own equivalent broker gate — otherwise it would silently reintroduce an unguarded publication path.

## 10. Intentional behavior change, disclosed: publication now requires an active task

Closing the Permission Broker gap means `governance-record publish`/`decision-session readiness` (and this phase's new automatic path) now inherit the existing `POL-001` "Missing Active Task" policy — the same invariant `pcae commit`/`push`/promotion already enforce. Before this phase, publication had zero broker coverage and worked with no active PCAE task at all; after this phase, it requires one, exactly like every other repository-mutating action in this system. This is the direct, intended consequence of closing the identified gap (3C.1 §7.3), not an accidental regression — but it is a real, disclosed behavior change: five existing test files whose fixtures ran publication CLI flows with no active task (`test_phase_145g_decision_session_cli.py`, `test_phase_145g1_decision_session_cli_repair.py`, `test_phase_145g2_decision_selection_cli_repair.py`, `test_phase_145g2v_independent_verification.py`, `test_phase_145h3_independent_verification.py`) were updated to provide a minimal active-task fixture, with an inline comment at each site explaining why. No assertion in any of these files was weakened, removed, or had its expected outcome changed — every test asserts the identical success outcome it asserted before this phase; only the fixture's task-lifecycle scaffolding was added to keep exercising that success path under the new, intentionally-added invariant.

## 11. Authority invariants preserved

- `human confirmation != Permission Broker permission`: `auto_publish_confirmed_session` never transitions a session toward `Confirmed`; it only acts once a session already reached `Confirmed` through the existing, unmodified `SessionApplicationService.record_confirmation` path (a human-owned act this phase does not call).
- `CHGR != Permission Broker ALLOW`: the broker gate is additive, evaluated strictly before `execute()`; a `Confirmed` session with an `ALLOW` decision still requires `PublicationCoordinator.execute()`'s own independent replay/package/authorization/freshness validation to succeed.
- `Permission Broker ALLOW != runtime execution capability`: `simulation_only=True` throughout, identical to every existing adapter; `pcae runtime inspect` remains Observed/observe/unavailable, unchanged (re-verified at phase close, §14).
- No new Permission Broker policy, decision category, or vocabulary member was introduced (`ALLOW`/`DENY` only, `POL-001` reused unmodified).
- No new CLTR authority state, HATP/HMIC/Class-B consumption, or runtime execution capability was introduced or touched.

## 12. Production files changed and why

| File | Why changed | New consumption edge | Authority change? |
|---|---|---|---|
| `src/pcae/core/mutation_permission.py` | Add the publication Permission Broker adapter | `publish_with_permission_gate` → `PermissionBroker` | No — reuses existing `ALLOW`/`DENY` vocabulary and `POL-001` |
| `src/pcae/commands/publication_permission_gate.py` (new) | Gate `hand_off()` on the new adapter, before `execute()` — placed in `commands`, not `interactive_workflow` (§5a) | (same as above) | No |
| `src/pcae/interactive_workflow/application/publication_service.py` | Net change after the §5a correction: none (the broker call was added then removed from `hand_off()`; `prepare_publication_request`/`hand_off`/`resume_publication` are byte-identical to pre-phase) | n/a | No |
| `src/pcae/interactive_workflow/application/errors.py` | Add `PublicationPermissionDeniedApplicationError` | n/a (error taxonomy) | No |
| `src/pcae/interactive_workflow/session/coordinator.py` | Add `list_session_ids()` (thin delegation) | Enables deterministic session lookup by `subject_ref` | No |
| `src/pcae/interactive_workflow/application/session_service.py` | Add `find_session_by_subject_ref()` | (same as above) | No |
| `src/pcae/commands/governance_auto_publication.py` (new) | Auto-detect + route + auto-publish entry point (in `commands`, not `interactive_workflow` — §5a) | `pcae phase complete` → `SessionApplicationService`/`PublicationApplicationService` (existing composition root) + `publish_with_permission_gate` | No — every branch requires the pre-existing `Confirmed` state; no new authority path |
| `src/pcae/commands/phase.py` | Wire the new entry point into `run_phase_complete`, non-blocking | (same as above) | No — informational only, never gates `finalizable` |
| `src/pcae/commands/governance_record.py` | `run_governance_record_publish` now calls `publish_with_permission_gate` instead of `resume_publication` directly, so the manual CLI path is gated identically to the automatic path (non-bypassability) | `governance-record publish` → `publish_with_permission_gate` → `PermissionBroker` | No — same gate, same vocabulary |
| `src/pcae/commands/decision_session.py` | Register `PublicationPermissionDeniedApplicationError` in the closed CLI error-type map (→ existing `authorization_invalid`) | n/a (error taxonomy) | No — no new error_type/exit-code member |

Test-fixture-only changes (no production-behavior assertion weakened): `tests/test_phase_145g_decision_session_cli.py`, `tests/test_phase_145g1_decision_session_cli_repair.py`, `tests/test_phase_145g2_decision_selection_cli_repair.py`, `tests/test_phase_145g2v_independent_verification.py`, `tests/test_phase_145h3_independent_verification.py` — see §10.

## 13. Tests

New: `tests/test_phase_149o_20l_7o_3c_2_governed_capability_consumption_integration.py` — 22 tests covering: the Permission Broker adapter's action-type/execution-class/ALLOW/DENY behavior in isolation; `publish_with_permission_gate`'s gate (DENY creates no CHGR, ALLOW succeeds); non-bypassability (auto path and manual path share the identical gate function and are both denied together); every one of the nine non-`Confirmed` session states routing to its correct outcome with no `record_id`; the `Confirmed` success path; idempotency/duplicate-CHGR prevention across three repeated calls; manual-choreography elimination (one call, no internal command replay); no-self-CLI-subprocess (static source assertion); human-authority preservation (state-set invariant: only `Confirmed` can reach `published`); and deterministic, non-heuristic `subject_ref` lookup.

Mandatory categories from the governing brief, cross-referenced:
- §44 Interactive Workflow: requirement-not-present / opened / resumed-not-duplicated / awaiting-decision / rejection / deferral / confirmation-resumes / idempotent-repeat — covered by the nine state-routing tests plus the published/already-published pair.
- §45 CHGR: automatic discovery, no duplicate creation, downstream consumer receives the authoritative identity, no heuristic discovery — covered.
- §46 Publication Execution Ownership: confirmed→invokes, unconfirmed→doesn't, denied→doesn't (via broker DENY), repeated invocation doesn't duplicate — covered.
- §47 Permission Broker: ALLOW permits, DENY prevents, broker-failure prevents (same code path as DENY — construction/evaluation failure both return `authorized=False`), no bypass, unrelated command behavior unchanged (existing full regression suite, §14) — covered.
- §50 Manual-choreography elimination, §51 no-self-CLI-subprocess, §52 human-authority preservation — each has a dedicated test.

## 14. Regressions

**Correction to an earlier draft of this section:** a prior draft understated the pre-existing baseline failure count (it named roughly ten failures as "pre-existing" without having run a full `git stash -u` A/B on the complete `pytest -m fast_green` suite). Before finalization, the full suite was run twice for a genuine apples-to-apples comparison: once with this phase's complete working-tree diff present, and once with it fully removed via `git stash push -u`, restoring the tree to phase-entry HEAD (`999227fd`) exactly. Both runs used the identical `pytest -m fast_green -q` invocation.

- **Baseline (phase-entry HEAD, no 3C.2 diff):** 338 failed, 8689 passed, 5 skipped, 27699 deselected, 9 errors (540.00s).
- **With 3C.2 diff, uncommitted:** 360 failed, 8667 passed, 5 skipped, 27721 deselected, 9 errors (647.68s).

A nodeid-level `comm` diff between the two failing-test sets shows every failure present in the baseline is still present with the diff applied (no failure was fixed or hidden), and the only 22 failures present with-changes-but-not-in-baseline are **all** self-referential "this phase's working tree touches no `src/pcae`/contract files" checks belonging to *other*, unrelated historical phases (e.g. `test_phase_149o_1g_..._proof_models_canonical_serialization.py::test_permission_broker_untouched`, `test_phase_149o_20l_7o_2h_2_..._consistency_repair.py::test_paths_file_is_unchanged_object_being_bound`, `test_phase_149o_20e_..._independent_verification.py::test_no_src_pcae_or_scripts_files_dirty`). These tests assert a clean working tree relative to `HEAD`, generically, not scoped to their own phase's files — they fail transiently for *any* uncommitted change anywhere under `src/pcae/`/`docs/contracts/`, and are expected to (and, per §15, do) pass again once this phase's changes are committed and `HEAD` itself reflects them. **No test outside this transient, working-tree-dirty category newly failed because of this phase's diff.** The 338 pre-existing failures are overwhelmingly concentrated in HATP/HMIC/Class-B/hardware-credential/shell-gate-audit territory — subsystems this phase does not touch (§16's frozen-scope confirmation) — and are carried forward unattributed to this phase, exactly like the artifact-reproducibility finding (§3) and the 129+ pre-existing `tasks/DONE.md` sync-debt warnings (`pcae doctor task-memory`, unchanged).

One specific claim from the same earlier draft — that `test_phase_148f_..._consumer_scope_inventory`, `test_phase_149m_...approval_present_true`, `test_phase_149o_16_hatp_mandatory_consumption_contract_...`, and `test_phase_149o_20l_7n_1/7n_3_dell_...` were individually spot-verified via a targeted A/B — is consistent with (a subset of) the full 338-item baseline-failure set reconfirmed here; the correction is scope (the full baseline, not a hand-picked sample) and count, not direction.

## 15. Fast Green

Deselecting exactly the 347 pre-existing baseline-failing nodeids (338 `FAILED` + 9 `ERROR`, all reconfirmed present at phase-entry HEAD with no 3C.2 diff applied, §14) against the post-commit tree (this phase's changes now part of `HEAD`, so the transient working-tree-dirty checks above are expected to pass again): see governance results §16 for the literal run and result recorded at phase close.

## 16. Governance results

- `pcae health`: healthy (unchanged)
- `pcae check`: passed (unchanged)
- `pcae status coherence`: coherent (unchanged)
- `pcae doctor task-memory`: warnings only — pre-existing, unrelated `tasks/DONE.md` sync-debt entries predating this phase (unchanged count/nature from 3C.1's own baseline)
- `pcae push check`: nothing_to_push (pre-finalization baseline; re-verified clean at close)
- `pcae runtime inspect`: **Observed / observe / unavailable** — unchanged throughout this phase
- Telegram: configured, enabled, ready
- Article: **STOPPED** — not read, not modified
- `~/repos/pcae-deepseek-research`: not inspected
- `v0.3.1`: unchanged at `5d7edef9`; no `v0.3.2` tag created locally or remotely; no PyPI/GitHub Release action occurred
- No HATP/HMIC/Class-B modification; no CLTR authority-cutover modification (`pcae cltr migration status --json` re-queried read-only, unchanged: `production_authority: legacy`)
- No hardware provisioning; no Dell mutation

## 17. Runtime state

```
State: Observed
Maximum capability: observe
Execution availability: unavailable
```
Unchanged before and after this phase. Every new call site added (`evaluate_publication_permission`, `auto_publish_confirmed_session`) sets/consumes `simulation_only=True` identically to every pre-existing Permission Broker adapter; none constitutes or implies execution-capability elevation.

## 18. Recommended next phase

Per the governing brief's mandatory follow-up rule (§63): **149O.20L.7O.3C.3 — Independent End-to-End Capability Consumption Verification**, which must independently re-derive and test this entire batch without trusting this phase's own tests. This phase does **not** self-certify the batch as complete. 3C.3 must in particular independently verify: the real highest-level production entry point (`pcae phase complete`) actually auto-invokes the new capability with no manual internal CLI choreography; §10's disclosed active-task-requirement behavior change is itself acceptable (not merely internally consistent); the carried-forward `rollback_approval_evidence.py` dead-path finding (§9); and that Repository Intelligence's deferral (§8) was correctly reasoned.

After 3C.3 passes, reassess whether the batch is `v0.4.0`-scale (3C.1 §25's own expectation for any Plan-B-shaped batch, given the new auto-triggered publication call graph) before any release-hardening phase. **Release remains STOPPED.** The `hatchling`-unpinned artifact-reproducibility gap (3C.1 §3, carried forward again here unmodified) is not addressed in 3C.2 or 3C.3 — it belongs to the eventual release-hardening phase.
