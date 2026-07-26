# Phase 145G.1 — Interactive Workflow CLI Command-Surface Completion and Readiness Construction Repair

**Status:** Completed (bounded repair/completion phase).
**Repairs:** Phase 145G's disclosed Blocking finding F-145G-1.
**Runtime:** Observed / observe / unavailable, unchanged before and after
this phase (confirmed via `pcae runtime inspect --json`).
**Governing contracts (read, not modified):** IWPC-001 v1.1, IWC-001
v1.2, PEC-001 v1.1, CHGR-001.

This report intentionally follows a leaner format than Phase 145D–145G's
own exhaustive reports (a scoping decision made explicit with the user at
the start of this phase, given the enormous surface area the original
governing prompt specified). It states what was built, why, what was
verified, and what remains open — the essential content, not the full
ceremonial traceability-matrix apparatus.

## 1. What Phase 145G disclosed, and what this phase closes

Phase 145G implemented `decision-session create`/`status`/`readiness`
(read-only) and `governance-record publish`, and disclosed Blocking
finding **F-145G-1**: `evidence`/`clarify`/`preview`/`confirm`/`cancel`
could not be implemented because `WorkflowOrchestrator` and its six
collaborators (Evidence Coordinator, Clarification Controller, Audit
Recorder, Preview Builder, Confirmation Controller, Transition Engine)
are in-memory-only — no store anywhere in the repository persisted
orchestration-stage progress, registered evidence, clarification
exchanges, or confirmation artifacts across separate CLI process
invocations. `readiness`'s construction path (IWPC-REQ-024) was blocked
for the identical reason: `PublicationHandoff.build_package` requires a
completed `OrchestrationState`, a live `Preview`, a `ConfirmationRequest`,
and an accepted `ConfirmationResponse`, none of which the CLI had any way
to obtain.

This phase closes F-145G-1 by implementing all five missing commands and
repairing `readiness` construction, without redesigning Interactive
Workflow architecture, without modifying frozen contract text, and
without touching `SessionRepository`, `FilesystemSessionRepository`,
`FilesystemPendingReadinessStore`, `PublicationHandoff`,
`PublicationCoordinator`, or any orchestration/evidence/clarification/
preview/confirmation domain-model file.

## 2. Blocking-finding re-derivation (required first step)

Re-derived directly from source, not from Phase 145G's own report text:

1. **Missing commands confirmed:** `evidence`/`clarify`/`preview`/
   `confirm`/`cancel` absent from `decision_session.py` and `cli.py`
   (confirmed by reading both files before any change).
2. **Unreachable domain operations confirmed:** `SessionCoordinator.
   orchestrate_evidence`/`perform_confirmation` exist but have no caller
   outside test files; `SessionCoordinator` has no `cancel` method at
   all.
3. **In-memory-only artifacts confirmed:** `WorkflowOrchestrator.__init__`
   always constructed a fresh `OrchestrationState()`; `EvidenceCoordinator`/
   `ClarificationController`/`ConfirmationController` hold plain `Dict`
   instance attributes with no `persist`/`load` method anywhere in their
   class bodies.
4. **Why `PublicationHandoff.build_package` cannot be called after a
   restart, confirmed:** its signature requires `orchestration_state`,
   `preview`, `confirmation_request`, `confirmation_response` as live
   objects; nothing persisted any of them.
5. **Required persisted artifacts, determined:** completed orchestration
   stages; registered evidence items; clarification request/response
   pairs; confirmation request/response pairs; one cached rendered
   Preview (needed so `confirm`/readiness-construction can bind to the
   *exact* Preview a caller last saw); cancellation reason/timestamp
   (`Session` itself carries no cancellation-reason field).
6. **Whether IWPC-001 already freezes persistence semantics for this:**
   No. §13 (`SessionRepository`) is frozen to exactly `create`/`load`/
   `persist`/`exists`/`list_session_ids` (IWPC-REQ-066) and explicitly
   forbids adding a sixth method. §14 (Pending-Readiness Store) governs a
   different artifact (the already-immutable `PublicationReadinessPackage`
   post-construction), not pre-construction orchestration bookkeeping.
   No section names a store for orchestration-stage/evidence/
   clarification/confirmation bookkeeping — this is the exact gap Phase
   145G itself recommended a future phase ("145H") design.
7. **Minimal application-layer extension required:** Yes — six new
   `SessionApplicationService` methods and one new
   `PublicationApplicationService` method (§4 below).
8. **Requirement conflict found between 145G's original scope, IWPC-001,
   and current source interfaces:** Yes — see §3 below (F-145G.1-1), a
   new finding this phase discovered and could not close within its own
   authorized scope.

## 3. New finding: F-145G.1-1 (disclosed, not closed by this phase)

No command in IWPC-001 v1.1's frozen §5 command surface (IWPC-REQ-014)
transitions a session out of `AwaitingDecision`. Confirmed by direct
source grep: `Session.human_selection_id`/`human_rationale_text`/
`human_conditions_text`/`options_presented` — the Decision Capture fields
IWC-001 v1.1 §5.3/§6 requires a human to author — have no production
setter anywhere in `interactive_workflow/session/coordinator.py`,
`.../state_machine/**`, or any prior phase's own source (`grep -rln
"human_selection_id=" tests/` finds only test fixtures; the same search
against `src/pcae/commands` and `src/pcae/interactive_workflow/application`
finds nothing). `EvidenceReady` -> `AwaitingDecision` and
`AwaitingDecision` -> `DecisionSelected` are both legal transitions per
the frozen `TRANSITION_TABLE`
(`interactive_workflow/state_machine/transitions.py`), but no command
this phase is authorized to add (its own governing prompt forbids
inventing an uncontracted command, and forbids changing frozen contract
text) drives either one.

**Consequence:** `clarify` (requires `AwaitingClarification`, itself only
reachable from `AwaitingDecision`), `preview` (requires
`DecisionSelected` or later), and `confirm` (requires
`AwaitingConfirmation`) are each implemented completely and correctly in
this phase — every one works whenever a session genuinely is in its
required precondition state — but that state is not reachable through
any real, CLI-only invocation sequence starting from `create`. Only
`evidence` (`Created` -> `EvidenceReady`) and `cancel` (any non-terminal
-> `Cancelled`) are genuinely reachable end-to-end via the CLI alone.

**Disposition:** Not closable within this phase's authorized scope.
Closing it requires either a future, separately-authorized IWPC-001
contract revision adding a decision-selection command, or a
determination (not this phase's to make) that IWC-001 intends selection
capture to happen outside a `decision-session` sub-command entirely.
Recorded here, in `PROJECT_STATUS.md`, `CHANGELOG.md`, and
`tasks/DECISIONS.md`, per this phase's own "disclose, don't invent"
discipline — mirroring exactly how Phase 145G disclosed F-145G-1 rather
than working around it.

## 4. What was built

### 4.1 Persisted orchestration state

`src/pcae/interactive_workflow/persistence/filesystem_orchestration_store.py`
(new): `FilesystemOrchestrationStore` + `OrchestrationRecord`. Storage
layout mirrors `FilesystemSessionRepository` (Phase 145D) exactly: single
flat directory (`.pcae/decision-sessions/orchestration/`), one file per
session, atomic `tempfile.mkstemp` → write → `flush` → `fsync` →
`os.replace` writes with `finally`-block temp-file cleanup, a dedicated
store-level `schema_version` (`decision-session-orchestration/1.0`),
path-safety validation via the existing `validate_session_id`, and
symlink refusal. Owned by the CLI/transport layer (extending IWPC-REQ-067's
own precedent), not by `SessionCoordinator` — no file under
`interactive_workflow/session/**`, `.../orchestration/**`, `.../evidence/**`,
etc. was modified to accommodate this store; it depends only on stdlib
and `session.identity.validate_session_id`.

What is persisted, and why: completed orchestration stages (so
`WorkflowOrchestrator` can resume); a running transition-sequence
counter (for `TransitionEngine.apply`'s monotonicity policy and
`Preview`'s staleness check); every registered evidence item,
clarification exchange, confirmation request, and confirmation response
(plain JSON dicts, translated to/from live domain objects exclusively at
the application-service boundary — this store has no dependency on
`interactive_workflow.orchestration`/`.evidence`/`.clarification`/
`.confirmation`/`.preview`); one cached rendered `Preview` (so `confirm`
and readiness construction can bind to the exact Preview a caller last
saw — Preview Builder's own determinism, IWPC-REQ-019, is what makes
re-deriving that exact content from live evidence/clarification refs
safe); and cancellation metadata.

`interactive_workflow/errors.py` gained one narrow addition:
`OrchestrationStoreCorruptError` (mirrors `SessionStoreCorruptError`'s
existing precedent exactly).

### 4.2 `WorkflowOrchestrator` — one additive constructor parameter

`orchestration/coordinator.py`: `WorkflowOrchestrator.__init__` gained
`initial_state: Optional[OrchestrationState] = None` (default `None`,
fully backward compatible — every existing caller and every Phase
143O/144C test is unaffected). When supplied, the orchestrator resumes
from that state instead of always starting fresh at
`SessionInitialization`. This does not change stage-sequencing rules,
does not skip a legality check, and does not let a caller fabricate
progress: `OrchestrationState.__post_init__` (unmodified) still enforces
that `completed_stages` is a valid, gapless, ordered prefix of
`STAGE_ORDER`.

### 4.3 `SessionApplicationService` — six new methods

`application/session_service.py`: `submit_evidence`,
`submit_clarification`, `generate_preview`, `record_confirmation`,
`cancel_session`, `construct_readiness_package`. Each: loads the
persisted `Session`; loads (or creates) the session's
`OrchestrationRecord`; rehydrates the six `WorkflowOrchestrator`
collaborators *exclusively through their own public registration
methods* (`register`, `register_request`, `register_response` — never by
writing to a private attribute, verified by the module's own
`_rehydrate_collaborators` helper); delegates every transition-legality
and workflow-semantic decision to the unmodified `SessionCoordinator`/
`WorkflowOrchestrator`/`TransitionEngine`; persists the resulting
`Session` and `OrchestrationRecord` atomically; and maps every
domain-layer exception into six new, narrowly-scoped application errors
(`application/errors.py`:
`SessionInvalidTransitionApplicationError`,
`SessionConfirmationConflictApplicationError`,
`SessionOrchestrationCorruptApplicationError`,
`SessionOrchestrationPersistenceUnavailableApplicationError`, plus reuse
of the existing `ReadinessSessionNotConfirmedApplicationError` for
`readiness_incomplete`).

Key interpretation decisions (see `tasks/DECISIONS.md` for the full
list): `evidence` is single-invocation, since no template-declared
"required evidence" list exists anywhere in this codebase for
completeness to check against — every declared identifier is registered
immediately, so a session's evidence is always "complete" the instant
it's declared. `preview` auto-advances the orchestrator's
`ClarificationLifecycle` bookkeeping stage when a session skipped
`clarify` (pure sequencing, no domain decision — that stage method
performs no validation of its own). `confirm` recomputes the live
Preview digest via `PreviewBuilder.build` immediately before comparing
against `--preview-digest` (IWPC-REQ-095), never trusting a stale cache.

### 4.4 `PublicationApplicationService` — one new method

`ensure_readiness_package(session_id)`: returns the existing pending
package if one exists (idempotent-by-key, IWPC-REQ-024); otherwise calls
`SessionApplicationService.construct_readiness_package` (which delegates
construction itself to the unmodified `PublicationHandoff.build_package`)
and persists the result via the existing, unmodified
`persist_readiness_package`. `decision-session readiness` now calls this
instead of read-only inspection alone.

### 4.5 CLI (`commands/decision_session.py`, `cli.py`)

Five new thin handlers (`run_decision_session_evidence`/`_clarify`/
`_preview`/`_confirm`/`_cancel`) following the existing
parse → validate → invoke application service → render → map-exit-code
pattern exactly. No CLI handler imports
`WorkflowOrchestrator`/`SessionCoordinator` internals,
`interactive_workflow.orchestration`/`.evidence`/`.clarification`/
`.preview`/`.confirmation`/`.state_machine`/`.audit`/`.publication_handoff`,
or any private (`_`-prefixed) name — verified by an extension of Phase
145G's own AST-based forbidden-import test
(`tests/test_phase_145g1_decision_session_cli_repair.py`). No new
dependency edge was needed in `.pcae/policy.toml` (the existing
`commands -> interactive_workflow` edge, declared and scope-justified by
Phase 145G, already covers this).

## 5. Architectural flow preserved

```
CLI handler
    -> SessionApplicationService / PublicationApplicationService
    -> SessionCoordinator / WorkflowOrchestrator (unmodified)
    -> SessionRepository (unmodified) + FilesystemOrchestrationStore (new)
    -> PublicationHandoff (unmodified)
    -> Pending-Readiness Store (unmodified)
    -> PublicationApplicationService
    -> PublicationCoordinator (unmodified)
```

No CLI handler calls `WorkflowOrchestrator`/`SessionCoordinator`/
`PublicationHandoff`/`PublicationCoordinator` directly, reads/writes
persistence directly, evaluates authority, fabricates confirmation,
infers identity, or synthesizes readiness without the required persisted
artifacts.

## 6. End-to-end verification

A real end-to-end scenario was exercised directly (both via the
application-service layer in an ad hoc script and via actual `pcae`
subprocess CLI invocations in a scratch directory) and is pinned by
`test_end_to_end_create_through_publish_with_restart_boundaries`: create
→ evidence → **[documented bridge — see §3]** → clarify → preview →
confirm → readiness (construct, then re-inspect after a fresh
process/service instantiation) → publish → replay rejected
(`publication_already_completed`), with a fresh `SessionApplicationService`/
`PublicationApplicationService`/`FilesystemOrchestrationStore` instance
constructed between every step to prove state is genuinely file-persisted,
not held in a shared Python object.

## 7. Regression validation

- `pcae check` / `pcae health` / `pcae doctor task-memory`: passed/
  healthy/clean, both before and after this phase's edits (task contract
  `20260726-1747-phase-145g-1-...` scoped to exactly the files this phase
  touches).
- `pcae runtime inspect --json`: `Observed`/`observe`/`unavailable`,
  unchanged before and after.
- All 37 pre-existing Phase 145G tests
  (`tests/test_phase_145g_decision_session_cli.py`) pass unmodified.
- 44 new tests
  (`tests/test_phase_145g1_decision_session_cli_repair.py`): parser
  registration; `evidence`/`cancel` end-to-end-reachable success/failure/
  restart-safety paths; `clarify`/`preview`/`confirm`/readiness-
  construction bridged-precondition success/failure/idempotency/restart-
  safety paths; the full end-to-end scenario (§6); orchestration-store
  atomic-write/corruption/path-traversal/missing-record tests; forbidden-
  import boundary extension (both directions).
- Focused regression: `tests/test_phase_145d_session_repository_filesystem_implementation.py`
  + `tests/test_phase_145e_pending_readiness_store_filesystem_implementation.py`
  + `tests/test_phase_145f_application_service_boundary.py`
  + `tests/test_phase_144c_publication_coordinator.py`
  + both 145G/145G.1 CLI test files: **274 passed, 0 failed.**
- Broad selection (`-k "iwc or interactive_workflow or 143"`, 842
  collected): **817 passed, 2 failed** — both failures
  (`test_chgr_packaging.py`'s `python -m build` wheel-packaging
  assertions) independently reproduced against unmodified `main` via
  `git stash` (identical failure both before and after this phase's
  diff), confirming pre-existing, unrelated environment issues.
- `fast_green` marker (single-worker, no `-n auto`): **4391 passed, 0
  failed** — matches the exact count Phase 145F/145G's own reports
  recorded as the clean baseline.
- Full repository suite (`pytest -n auto`): run; see this phase's
  `phase-completion-metadata.json` for the final count and the
  pre-existing-failure comparison against unmodified `main`.

## 8. No-Go confirmation

No HTTP/RPC/socket/web/message-bus/remote transport was added. No TUI or
interactive terminal prompt was added. No automatic confirmation,
authorization, or publication was added — `confirm` requires an explicit
`--statement`; `publish` requires an explicit `--operator-id`; neither
command infers or defaults either. No `--force`/`--assume-authorized`
bypass exists on any command (verified directly,
`test_no_force_or_bypass_flag_on_any_new_command`). No CLI handler
bypasses `SessionApplicationService`/`PublicationApplicationService`. No
CLI handler accesses `SessionRepository`, the orchestration store, or the
Pending-Readiness Store directly. No CHGR artifact is created by CLI or
application-service code. IWC-001/PEC-001/CHGR-001/IWPC-001 contract text
was not changed. No file under `src/pcae/governance/publication/**` was
modified. `Session`, `SessionRepository`,
`FilesystemSessionRepository`, `FilesystemPendingReadinessStore`,
`PublicationHandoff`, `PublicationCoordinator`, and every orchestration
collaborator's own domain logic (evidence/clarification/preview/
confirmation validation rules) are unmodified — the sole domain-layer
change is `WorkflowOrchestrator`'s one additive constructor parameter
(§4.2). No runtime capability change was made; `pcae runtime inspect`
remains `Observed`/`observe`/`unavailable` before and after. Phase 145H
was not begun.

## 9. Residual findings

- **F-145G.1-1 (unresolved, disclosed):** see §3. Recommended
  disposition: a future, separately-authorized contract revision (or
  ruling) defining how a session reaches `DecisionSelected` through the
  CLI/transport layer.
- **Non-Blocking (inherited from 145G, unchanged by this phase):**
  `status`/`readiness` report `"none"` rather than `"consumed"` once a
  package is published, since `FilesystemPendingReadinessStore.
  find_by_session_id` (145E, unmodified) never returns a `consumed/`
  record via session-id-keyed lookup. `PublicationApplicationService`
  (145F, unmodified) still collapses several PEC-001 exception classes
  into two application-error classes each.
- **Non-Blocking (new, disclosed):** the `cancel_session`
  application-service method stores cancellation reason/timestamp in the
  orchestration record rather than on `Session` itself (which carries no
  cancellation-reason field) — a deliberate choice to avoid widening the
  frozen `Session` dataclass merely to carry one optional string.

## 10. Recommendation

A likely next phase is **145G.1V — Interactive Workflow CLI
Command-Surface Repair Independent Verification**, or a phase directly
addressing F-145G.1-1 via a governed IWPC-001 contract revision. This
recommendation does not authorize either.
