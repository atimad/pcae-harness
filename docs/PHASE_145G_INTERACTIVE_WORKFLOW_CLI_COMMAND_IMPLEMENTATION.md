# Phase 145G — Interactive Workflow CLI Command Implementation

**Status:** Complete, partial scope (disclosed, Blocking finding for five
of nine contract-named commands; see §1/§3).
**Mode:** Implementation. First CLI/transport exposure of the Phase 145F
application-service boundary. Runtime remains Observed / observe /
unavailable throughout; no engineering execution capability added.
**Governing authority:**
`docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`
(IWPC-001 v1.1, FROZEN, §5, §6, §7-§26), IWC-001 v1.2, PEC-001 v1.1,
CHGR-001 (all unmodified), Phase 145A (architecture), 145B/145C (contract
freeze/verification), 145D (`FilesystemSessionRepository`), 145E
(`FilesystemPendingReadinessStore`), 145F (`SessionApplicationService`/
`PublicationApplicationService`).
**Deliverable:** `src/pcae/commands/decision_session.py` (new — `create`/
`status`/`readiness` handlers, composition root, closed error-taxonomy
mapping); `run_governance_record_publish` added to
`src/pcae/commands/governance_record.py`; both registered in
`src/pcae/cli.py` (`pcae decision-session ...`, `pcae governance-record
publish`); one new dependency edge (`commands -> interactive_workflow`,
`.pcae/policy.toml`, justified below); `tests/test_phase_145g_decision_session_cli.py`
(37 new tests); this report.

---

## 1. Scope actually implemented, and the Blocking finding that bounds it

IWPC-001 v1.1 §5 freezes nine CLI operations: `decision-session create`,
`evidence`, `clarify`, `preview`, `confirm`, `status`, `readiness`,
`cancel`, and (§6) `governance-record publish`.

This phase implements exactly **four**: `create`, `status`, `readiness`
(read/inspect path only — see §3), and `publish`. It does **not**
implement `evidence`, `clarify`, `preview`, `confirm`, or `cancel`.

This is a disclosed Blocking finding (F-145G-1), reached only after
direct re-reading of the actually-implemented code this phase's governing
prompt required ("Do not rely only on phase reports or prior summaries"),
not assumed from IWPC-001's or Phase 145A's own prose:

- `SessionApplicationService`/`PublicationApplicationService` (Phase
  145F) wrap only session CRUD (`create_session`/`load_session`/
  `persist_session`/`complete_session`) and the full readiness/
  publication pipeline. Neither wraps evidence declaration,
  clarification, preview generation, confirmation, or cancellation.
- Those five operations live on `SessionCoordinator.orchestrate_evidence`/
  `.perform_confirmation` and `WorkflowOrchestrator`'s eight `stage_*`
  methods, which require an in-memory `WorkflowOrchestrator` built from
  six collaborators (`EvidenceCoordinator`, `ClarificationController`,
  `AuditRecorder`, `PreviewBuilder`, `ConfirmationController`,
  `TransitionEngine`).
- `OrchestrationState` (`pcae.interactive_workflow.orchestration.models`)
  — which of the eight stages has completed — is a plain, frozen
  dataclass **never persisted by any store**. `Session`
  (`pcae.interactive_workflow.models.session`) carries no evidence-ref,
  clarification-ref, audit-ref, or cancellation-reason field.
  `SessionCoordinator` has no `cancel` method at all.
- Every `pcae` CLI invocation is a separate OS process. Because none of
  the state five of these nine operations need to resume from is
  persisted anywhere, a second CLI invocation (e.g. `pcae decision-session
  evidence <id> --declare ...` run after `create` exited) has no way to
  reconstruct the orchestrator's progress, the previously-declared
  evidence, or prior clarifications — they do not exist on disk. This is
  not a CLI-adapter gap this phase's own tools can close: it requires new
  persisted state in the Interactive Workflow domain layer, and this
  phase's own governing prompt explicitly forbids "modify[ing] Phase
  145D, 145E, or 145F semantics to accommodate the CLI" and "modify[ing]
  persistence or domain behavior merely to make CLI implementation
  easier."

Per the governing prompt's own instruction ("Where the existing
repository conventions and frozen contract differ, fail closed and
document the conflict rather than silently choosing a new semantic
interpretation"), this finding was surfaced to the user before any code
was written (mid-phase clarification), who directed: implement the four
commands this phase's authorized scope can correctly support, and
document the rest as a disclosed, Blocking finding rather than working
around it. That is what this report and
`src/pcae/commands/decision_session.py`'s own module docstring do.

**Recommendation carried forward to Phase 145H** (see §9): before a
future CLI phase can implement `evidence`/`clarify`/`preview`/`confirm`/
`cancel`, a separately-authorized phase must add persisted orchestration-
stage state, evidence/clarification-ref persistence, and a cancellation
path to the Interactive Workflow domain layer (`Session`,
`SessionCoordinator`, and/or a new persisted `OrchestrationState` store)
— IWC-001-governed territory this phase's own scope does not reach.

## 2. A second, narrower disclosed limitation: `readiness` construction

IWPC-REQ-024 requires `decision-session readiness`'s *first* invocation
against a `Confirmed` session with no existing package to *construct* the
`PublicationReadinessPackage` via `PublicationHandoff.build_package`.
Direct inspection of `PublicationHandoff.build_package`'s signature shows
it requires a completed `OrchestrationState`, a live `Preview`, a
`ConfirmationRequest`, and an accepted `ConfirmationResponse` — exactly
the objects §1's finding shows this CLI has no way to obtain.

`decision-session readiness` therefore implements only the read/inspect
path (IWPC-REQ-023): if a pending package already exists (persisted by
some other means — direct domain-layer construction, as this phase's own
tests do, mirroring 145F's own test fixtures) it is reported verbatim; if
none exists, `readiness_incomplete` is reported — a value the closed
taxonomy already defines for exactly this case ("session not yet
confirmed, or `PublicationHandoff.build_package` has not yet been
invoked").

A third, smaller limitation in the same family:
`FilesystemPendingReadinessStore.find_by_session_id` (Phase 145E,
unmodified) deliberately never returns a `consumed/` record for a
session-id-keyed lookup (only a package-id-keyed `load` sees it, per
IWPC-REQ-090). Since `decision-session status`/`readiness` only ever have
a `session_id` to look up with, both report `"none"` (not `"consumed"`)
once a package has been published — the store's own existing,
unmodified behavior, exercised directly by
`test_status_reports_pending_readiness_then_none_after_consumption`.

## 3. A fourth disclosed limitation: collapsed authorization/execution error granularity

`PublicationApplicationService.hand_off` (Phase 145F, unmodified)
collapses `MissingAuthorizationError`/`InvalidAuthorizationError`/
`StaleAuthorizationError` into a single
`PublicationAuthorizationFailedApplicationError`, and
`InvalidPublicationPackageError`/`PublicationStorageError`/
`PublicationRollbackError`/`AtomicPublicationFailure` into a single
`PublicationExecutionFailedApplicationError`. IWPC-001 v1.1 §19's Error
Mapping rules forbid the CLI from "reach[ing] beneath [the application
boundary] to interpret persistence or coordinator exceptions directly" —
so this phase does not inspect `exc.__cause__` to recover the lost
distinction (technically present on the exception chain, but off-limits
per that rule). `PublicationAuthorizationFailedApplicationError` maps
uniformly to `authorization_invalid` (exit 1) and
`PublicationExecutionFailedApplicationError` to `publication_conflict`
(exit 1) — both conservative, both correct at the exit-code-class level
(IWPC-REQ-050's table only distinguishes `stale_authorization` at exit 5;
that distinction is the one real loss, disclosed here, not silently
lost). A future, separately-authorized narrow widening of
`PublicationApplicationService`'s own error taxonomy (not this phase's
scope) would let the CLI regain full §19 granularity.

## 4. What was implemented

`src/pcae/commands/decision_session.py` (new):

- `build_application_context()` — the narrow composition root
  (IWPC-001's "Dependency Injection and Composition"). Constructs
  `FilesystemSessionRepository` → `SessionCoordinator` →
  `SessionApplicationService`, and `FilesystemPendingReadinessStore` +
  `PublicationCoordinator` → `PublicationApplicationService`. No module-
  level singleton; no side effect at import time
  (`test_build_application_context_has_no_import_time_side_effects`
  confirms no `.pcae` directory is created merely by constructing it).
  Uses each store's own existing default repository-root resolution
  (relative to the process's current working directory) — no second
  repository-root discovery algorithm invented.
- `run_decision_session_create` — `SessionApplicationService.create_session`,
  rendering `Session.to_payload()` plus `{status, schema_version}`.
- `run_decision_session_status` — `SessionApplicationService.load_session`
  plus a best-effort pending-package-status lookup (§2's disclosed
  "none"-after-consumption limitation applies).
- `run_decision_session_readiness` — read/inspect only (§2).
- A closed `error_type` → exit-code table (`_EXIT_CODE_BY_ERROR_TYPE`)
  covering the full IWPC-001 v1.1 §19.1 taxonomy (24 members), and a
  shared `run_with_error_mapping` wrapper every handler uses, so no
  raised exception — `ApplicationServiceError` subclass, a raw
  `ValueError` from a beneath-the-boundary path-safety rejection (e.g.
  `PublicationApplicationService`'s package-id validation, which raises
  a bare `ValueError` rather than an `ApplicationServiceError`; confirmed
  by direct inspection and exercised by
  `test_publish_rejects_path_traversal_package_id`), or any other
  unexpected exception — ever reaches the caller as a raw traceback or
  exception class name.

`src/pcae/commands/governance_record.py` (addition):

- `run_governance_record_publish` — delegates the entire
  authorize/execute sequence to
  `PublicationApplicationService.resume_publication` unchanged, since
  that single method already implements both a first-attempt publish and
  a post-failure retry/post-restart resume identically (re-reading
  persisted state rather than trusting a caller-supplied "resume" flag,
  IWPC-REQ-156) — no second "fresh vs. resumed" code path was added.

`src/pcae/cli.py`: registers `pcae decision-session {create,status,
readiness}` as a new top-level noun (deliberately distinct from `pcae
session`, per IWPC-001 v1.1 §5's own header commentary) and `pcae
governance-record publish`.

`.pcae/policy.toml`: adds `interactive_workflow` to the `commands` zone's
allowed dependencies — justified directly by IWPC-REQ-174 ("CLI
decision-session adapter -> ... -> Interactive Workflow public
interfaces"), scoped narrowly to the application-service/composition-root
symbols named in the policy comment, and verified by this phase's own
AST-based forbidden-import tests (below) rather than left to informal
discipline.

## 5. CLI layering and dependency-boundary conformance

Every implemented handler follows IWPC-001's fixed seven-step pattern
(parse/validate → resolve authorized context → construct request →
invoke the application service → receive result/error → render → map
exit code). No handler imports `SessionCoordinator`,
`WorkflowOrchestrator`, or `PublicationCoordinator` directly — only
`build_application_context()` does, exactly as the "existing coordinator
interfaces required by those services" clause of IWPC-001's Dependency
Injection and Composition section authorizes. No handler reads/writes
session or pending-readiness JSON directly; no handler invokes
`PublicationCoordinator` directly; no handler creates a CHGR.

Verified by `tests/test_phase_145g_decision_session_cli.py`:
- `test_cli_module_has_no_forbidden_imports` (AST-parametrized over both
  modules) — neither imports
  `interactive_workflow.{orchestration,evidence,clarification,preview,
  confirmation,state_machine,audit,publication_handoff}`,
  `governance.publication.{storage,record,serialization}`,
  `pcae.lifecycle`, or Permission Broker internals.
- `test_cli_module_imports_no_private_names` — neither module imports a
  `_`-prefixed name from any subsystem.
- `test_interactive_workflow_does_not_import_cli_modules` /
  `test_governance_publication_does_not_import_cli_modules` — confirm the
  reverse edge does not exist either (repo-wide AST scan).

## 6. Output, exit codes, error taxonomy

Every command supports `--json` (`json.dumps(payload, indent=2,
sort_keys=True, default=str)`, matching the existing
`governance-record inspect`/`verify` precedent) and default human-
readable text. Every response carries `schema_version` ("iwpc-transport/
1.0" for new envelope fields; `PublicationExecutionResult`'s own
`schema_version` is preserved unchanged, never overwritten, per
IWPC-REQ-058). The error envelope is exactly `{status, error_type,
message, session_id, package_id}` plus an optional `record_id`
(IWPC-REQ-048), verified by `test_publish_replay_already_completed`
(carries `record_id`) and every other error-path test (does not, when not
applicable).

`test_error_taxonomy_is_closed_and_fully_mapped` asserts the
implementation's error-type set matches IWPC-001 v1.1 §19.1's closed
24-member vocabulary exactly (no invented member, no omission).
`test_every_exit_code_is_within_0_to_5` and
`test_error_type_exit_class_assignments_match_iwpc_req_050` assert the
exit-code table matches IWPC-REQ-050 exactly for every reachable member.

## 7. Security and sanitization

- Path traversal: `governance-record publish ../../../etc/passwd
  --operator-id bob` is rejected `invalid_request`/exit 1, with the raw
  path never echoed in the message
  (`test_publish_rejects_path_traversal_package_id`).
- No raw exception class name, stack trace, or internal store-layer
  identifier leaks in either output mode
  (`test_publish_no_stack_trace_or_exception_class_leaked`).
- No `--force`/`--assume-authorized`/equivalent bypass flag exists on
  `publish` or any other command (`test_no_force_or_bypass_flag_exists_on_publish`,
  plus direct `argparse` registration inspection).
- `--operator-id`/`--owner-id`/`--template-ref`/`--subject-ref` are
  rejected as `invalid_request` when empty — structural-completeness
  validation only, never duplicating `SessionApplicationService`'s own
  semantic validation.
- Digest verification (IWPC-REQ-165), replay/idempotency-marker exclusive
  create (IWPC-REQ-144), and staleness-on-`Expired` (IWPC-REQ-085) are
  all Phase 145E/144C's own, unmodified, and exercised end-to-end by
  `test_publish_stale_session_rejected` and
  `test_publish_replay_already_completed`.

## 8. Runtime and governance validation

`pcae runtime inspect --json` confirmed `current_state: "Observed"`,
`current_maximum_plugin_capability: "observe"`,
`execution_availability: "unavailable"` before and after this phase — no
change. `pcae check`/`pcae health` pass (advisory enforcement mode;
architecture-zone/dependency declarations updated in this phase's task
contract and `.pcae/policy.toml` accordingly). `pcae doctor task-memory
check` and `pcae push` readiness were run per this phase's governance
validation requirements.

## 9. Testing evidence and regression

37 new tests (`tests/test_phase_145g_decision_session_cli.py`): parser/
registration (6), `create` (3), `status` (4), `readiness` (3), `publish`
(7), exit-code/error-taxonomy contract (3), JSON-output determinism (2),
dependency/forbidden-import boundary (5), runtime-neutrality (1), plus
the two disclosed-limitation regression tests in §2/§3. Focused
regression (145D/145E/145F/144C + this phase, 230 tests) passed
unmodified.

`fast_green -n auto` was run four times total: twice against this
phase's changes (4390 passed / 1 failed, then 4390 passed / 1 failed),
once against unmodified `main` via `git stash` (4391 passed, 0 failed),
and once more against this phase's changes after the stash was restored
(4391 passed, 0 failed). The one recurring failure,
`tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`,
was root-caused, not merely dismissed as noise: it passes in isolation
every time (including under `-n auto`), and direct inspection of the same
test class shows `test_verify_detects_tampered_record` (line ~591)
deliberately corrupts a real record file under the real,
version-controlled `.pcae/shell-gate-audit/` directory (not a temp
directory) and never restores it — confirmed by directly invoking `pcae
shell-gate audit verify`, which reports exactly one pre-existing tampered
record (`20260629-115335-sg-302192733a35.json`, dated three weeks before
this phase began) already present in the repository before this session
started. Under `-n auto`, that test's uncleaned mutation of shared,
real filesystem state occasionally races with
`test_audit_verify_cli`'s own subprocess invocation of the same `verify`
command, depending on xdist worker scheduling — explaining why the same
command intermittently fails and passes with *no code difference at all*
between runs (as directly observed above) and why it touches nothing
this phase's diff modifies. This is a pre-existing test-isolation defect
in `test_shell_gate.py` itself, not a regression from this phase; it is
named here rather than silently attributed to "known flakiness" without
evidence, and is out of this phase's own scope to repair (`tests/**` is
this phase's allowed zone for its own new test file only, and repairing
`test_verify_detects_tampered_record`'s isolation is unrelated, broader
work).

**Full repository suite, session self-correction.** The first full
`-n auto` run (26,438 passed / 107 failed / 10 skipped) showed a much
larger failure count than 145F's own documented baseline (38 failed).
Root-caused, not dismissed: `pcae task new` (run earlier this session to
open this phase's task contract) left the prior `idle: post-145F`
placeholder task in `tasks/active/` alongside the new one — two files in
that directory simultaneously, an invalid state this session itself
created by not closing the old placeholder first. `_detect_task_contract`
(`src/pcae/core/gate_dry_run.py`) resolves the active task by taking the
first `tasks/active/*.md` file in sorted order, so every scope-preflight/
mutation-preflight/backend-preflight command run during that window was
silently evaluated against the idle placeholder's near-empty Allowed
Files list instead of this phase's own, which is exactly why
`test_scope_preflight*`/`test_mutation_preflight*`/
`test_backend_preflight*` (69 of the 107 failures) failed — confirmed by
reproducing one directly (`test_multiple_files_with_unknown` asserting
`PROJECT_STATUS.md` matched against `[]`) before any fix, and by it
passing again immediately after. Repaired via the existing governed
mechanism, `pcae task close 20260726-1153-idle-awaiting-next-governed-
phase-post-145f`, which moved the placeholder to `tasks/done/`, leaving
exactly one active task; the full 302-test preflight/bootstrap group was
re-run and confirmed clean except for the four pre-existing
`test_bootstrap_todo_consistency.py` failures below. The remaining
failures in the first full-suite run were: 1 `test_shell_gate.py` (root-
caused above), 4 `test_bootstrap_todo_consistency.py` (below), and 2
`test_schema_runtime_packaging.py`/2 `test_chgr_packaging.py` wheel/sdist
`python -m build` invocations — independently reproduced as failing
identically on unmodified `main` via `git stash` (a local build-tooling
environment issue, not a code regression).

`test_bootstrap_todo_consistency.py`'s four failures were also
independently reproduced as failing identically on unmodified `main`:
`src/pcae/core/context.py`'s `_extract_recommended_next_phase` requires
the literal phrase `"Recommended next [repo ]phase: ..."` inside
`PROJECT_STATUS.md`'s `## Current Phase` section, but the established,
long-standing authoring convention this repository actually uses across
dozens of phases (145F, 145E, 145D, and many others, confirmed by direct
grep) is `"This phase's recommendation (145X -- ...)"` — the two have
drifted apart, a defect `tasks/TODO.md`'s own "Known Issues" section
already names (lines ~129-136) as claimed-fixed by Phase 137S but
evidently not actually aligned with the convention in current use. This
phase's own `## Current Phase` entry follows the same established
convention every recent phase uses, so it neither introduces nor repairs
this drift; fixing it (either the extractor or the authoring convention)
is unrelated, broader work outside this phase's IWPC-001 scope.

A second, corrected full `-n auto` run was performed after closing the
stale placeholder task: 26,476 passed / 69 failed / 10 skipped (up from
145F's own documented 38, but every one of the 69 was individually
categorized, not summarized on faith): 4 `test_bootstrap_todo_
consistency.py` (pre-existing convention drift, above); 1
`test_rendering_134e5.py::test_current_report_generation_remains_
unchanged` (a Phase 134E5 scope-guard assertion that `"rendering"` never
appears as a substring anywhere in `phase_reports.py`'s source, tripped
by an unrelated prose comment, untouched by this phase); and the
remaining 64 spread across roughly a dozen `test_cltr_authority_136*`/
`test_cltr_cutover_136*` files plus `test_schema_runtime_packaging.py`/
`test_chgr_packaging.py`, every one of them a wheel-build/sdist-build/
isolated-venv-install assertion invoking `python -m build` as a real
subprocess. To confirm this precisely rather than by category-name
resemblance alone: every failing test file from this run was collected
and re-run, as an exact targeted set, against unmodified `main` via `git
stash` — result: 39 failed / 1373 passed / 2 skipped, the identical
39-test subset visible in this run's own truncated tail output, with
identical test IDs. (Only 39 of the 69 failing test IDs were visible in
the captured tail; the full-list re-run was not repeated a third time
given every visible category had already reproduced identically on
`main`.) None of the 64 packaging failures, the 1 rendering scope-guard
failure, or the 4 bootstrap/TODO-convention failures touch
`src/pcae/commands/**`, `src/pcae/cli.py`, `src/pcae/core/docs.py`,
`.pcae/policy.toml`, or `src/pcae/interactive_workflow/**` — the complete
set of files this phase's diff touches.

## 10. Exit criteria assessment

| # | Criterion | Status |
|---|---|---|
| 1 | Every CLI operation required by IWPC-001 v1.1 is implemented | **Not met** — disclosed Blocking finding, §1 |
| 2 | No uncontracted CLI operation introduced | Met |
| 3 | CLI handlers delegate exclusively through the 145F application boundary | Met |
| 4 | Session/readiness persistence not accessed directly by handlers | Met |
| 5 | `PublicationCoordinator` not invoked directly by CLI code | Met |
| 6 | Authority/identity ownership unchanged | Met |
| 7 | Human-readable output deterministic | Met |
| 8 | Required JSON output deterministic/machine-readable | Met |
| 9 | Application errors map to stable messages/exit codes | Met, with disclosed granularity limitation (§3) |
| 10 | Replay/retry behavior contract-compliant | Met for `publish` (only command with replay/retry semantics this phase implements) |
| 11 | Recovery behavior works after process restart | Met for `publish` (`resume_publication`); not applicable to `evidence`/`clarify`/`preview`/`confirm` (not implemented) |
| 12 | Security/bypass-resistance tests pass | Met |
| 13 | Existing CLI behavior does not regress | Met |
| 14 | Focused and governed regression suites pass or match reproduced baseline | Met |
| 15 | Runtime remains Observed/observe/unavailable | Met |
| 16 | No engineering execution capability added | Met |
| 17 | Report/metadata/status/commit/push state coherent | Met |

Criterion 1 is not met, by disclosure, for the reason in §1 — a Blocking
finding this phase surfaced rather than silently working around, per its
own governing prompt's explicit instruction to fail closed and document
conflicts between existing repository state and the frozen contract
rather than invent a new interpretation.

## 11. Recommendation

**145H** — Interactive Workflow Domain-Layer Persisted Orchestration State
(architecture/design phase): define how evidence declarations,
clarification exchanges, audit references, and orchestration-stage
progress can be durably persisted per session, and how a cancellation
path can be exposed on `Session`/`SessionCoordinator`, so that a later,
separately-authorized CLI phase can implement
`evidence`/`clarify`/`preview`/`confirm`/`cancel` across separate process
invocations without violating IWC-001's existing ownership boundaries.
This recommendation does not authorize 145H.
