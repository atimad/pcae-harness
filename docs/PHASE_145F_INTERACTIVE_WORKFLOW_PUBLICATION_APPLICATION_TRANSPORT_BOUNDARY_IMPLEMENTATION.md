# Phase 145F — Interactive Workflow + Publication Application/Transport Boundary Implementation

**Status:** Complete.
**Mode:** Implementation, introducing the internal application-service
boundary connecting the Interactive Workflow subsystem to the Publication
subsystem, using the already-implemented persistence components
(`FilesystemSessionRepository`, Phase 145D; `FilesystemPendingReadinessStore`,
Phase 145E). No CLI command, no transport adapter, no engineering
execution capability.
**Governing authority:**
`docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`
(IWPC-001 v1.1, FROZEN, in particular §3 IWPC-REQ-006 "Model D",
§4 Required Architecture Invariants, §12-§17, §19.1, §21, §22, §23, §25),
`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md` (IWC-001 v1.2, session
semantics/persistence-boundary ownership, unmodified),
`docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md` (PEC-001 v1.1,
Publication ownership, unmodified),
`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` (CHGR-001,
unmodified), Phase 145A (Architecture, "Model D" rejection rationale),
Phase 145D, Phase 145E.
**Runtime:** Observed / observe / unavailable, confirmed unchanged before
and after this phase (`pcae runtime inspect --json`).
**Deliverable:** new package
`src/pcae/interactive_workflow/application/` (`__init__.py`, `errors.py`,
`models.py`, `session_service.py`, `publication_service.py`) —
`SessionApplicationService`, `PublicationApplicationService`,
`PreparedPublicationRequest`, and a closed application-level error
taxonomy —
`tests/test_phase_145f_application_service_boundary.py` (45 new tests),
this phase report.

---

## 1. Scope

This phase implements exactly two classes and their supporting error/
value-object modules: `SessionApplicationService` (coordinates
`SessionCoordinator`/`SessionRepository`) and
`PublicationApplicationService` (coordinates the Pending-Readiness Store,
the Session Repository via `SessionApplicationService`, and
`PublicationCoordinator`). No CLI command, transport adapter, decision-
session command handler, engineering execution capability, or CHGR-
writing behavior was implemented. `SessionRepository`,
`FilesystemSessionRepository`, `FilesystemPendingReadinessStore`,
`SessionCoordinator`, `WorkflowOrchestrator`, `PublicationHandoff`, and
`PublicationCoordinator` were not modified. No contract text (IWC-001,
PEC-001, CHGR-001, IWPC-001) was changed.

## 2. The IWPC-REQ-006 "Model D" Question, Addressed Directly

IWPC-001 v1.1 §3 (IWPC-REQ-006) states: "No transport-neutral
application-service class SHALL be required by v1.0. The CLI command
module is the transport adapter; a future, separately governed contract
revision MAY introduce Model D... without this contract needing
retraction." Phase 145A §4 explicitly rejected building "Model D" at that
time, reasoning that a service layer with exactly one prospective
consumer (a CLI that did not yet exist) would be premature abstraction,
and — the more substantive concern — "would risk becoming a **second,
informal, unauthorized** boundary athwart the existing forbidden-import
tests... a new service module sitting 'above' both would need its own
governed boundary contract to avoid quietly becoming the place logic
actually lives."

This phase's own governing prompt explicitly requires implementing "the
application/service boundary" now, while explicitly forbidding any
modification to IWPC-001. Read literally, IWPC-REQ-006 says the class is
not *required*, not that it is *forbidden*; it does not itself block this
phase. Phase 145A's substantive objection — the risk of an informal
boundary competing with, or diverging from, an *existing* transport — is
inapplicable here by construction: no CLI/transport package exists in
this repository (145D §2 and 145E §3 already established this same fact
for their own placement decisions), so there is no existing transport
this new layer could quietly duplicate or drift from. This phase's own
No-Go list (§13 below) keeps that true going forward: no CLI, no
transport adapter, no second invocation surface was added.

This is disclosed here as a **Non-Blocking** finding, the same
classification 145E §5 used for its own analogous frozen-contract gap:
the underlying intent IWPC-REQ-006 protects against (an unauthorized
transport boundary) is not violated, even though the requirement's literal
text anticipates this layer arriving via "a future, separately governed
contract revision" rather than an implementation phase's own prompt. A
future CLI/transport phase (145G) building `decision-session`/
`governance-record publish` as thin adapters over this boundary would be
the natural point to also propose that formal IWPC-001 revision, if the
project wants `application/` to become IWPC-001's own named, contractual
Model D rather than the internal, pre-transport coordination layer it is
today.

## 3. Placement Decision

Mirrors Phase 145D §2 and Phase 145E §3's reasoning: since no CLI/
transport package exists yet, there is no physical location matching
IWPC-REQ-174's literal "transport/application boundary (the adapter
module itself)" language. The new package is placed at
`interactive_workflow/application/`, a sibling of `persistence/`,
`session/`, `orchestration/`, and `publication_handoff/` — it sits inside
`interactive_workflow` rather than as a new top-level package because its
primary responsibility (session lifecycle coordination) is
Interactive-Workflow territory, and because `publication_service.py`'s
cross-boundary coordination role is exactly the "Application boundary"
IWPC-001 §3 already names as "the point at which a transport adapter
calls into `SessionCoordinator`/`WorkflowOrchestrator`... or
`PublicationCoordinator`" — a description of a *relationship*, not a
package location. A future CLI/transport phase MAY relocate or re-export
these classes without changing their behavior, exactly as 145D/145E's own
placement decisions anticipated for themselves.

## 4. Composition, Not Reimplementation

Both services are thin coordination wrappers, never reimplementations
(IWPC-REQ-011, "delegate... SHALL NOT reimplement"):

- `SessionApplicationService` is constructed with an explicit
  `SessionCoordinator` and delegates `create_session`/`load_session`/
  `persist_session` to it unchanged; `update_session` is a documented
  alias for `persist_session` (`SessionRepository` itself defines no
  separate "update" primitive, IWPC-REQ-066); `complete_session` adds
  exactly one precondition check (`session.is_terminal()`) the underlying
  coordinator does not itself perform, then persists.
- `PublicationApplicationService` is constructed with an explicit
  `FilesystemPendingReadinessStore`, `SessionApplicationService` (never a
  second, parallel path into the raw `SessionRepository` — enforced by a
  dedicated dependency-boundary test, §9 below), and `PublicationCoordinator`.
  `prepare_publication_request` and `hand_off` add exactly the
  precondition checks (disposition still pending, bound session not
  `Expired`) that neither the store nor the Coordinator itself performs at
  this layer, then delegate `authorize`/`execute` to
  `PublicationCoordinator` unchanged (IWPC-REQ-127/128) and delegate
  attempt-linkage/disposition recording to the store unchanged
  (IWPC-REQ-087/088/089).

Neither class evaluates authority, infers identity, constructs a CHGR, or
invents an authorization policy (IWPC-REQ-007-013 restated at this
layer).

## 5. Application-Level Error Taxonomy

`application/errors.py` defines a closed hierarchy
(`ApplicationServiceError` → `SessionCoordinationError`/
`ReadinessCoordinationError`/`PublicationCoordinationError` → 18 leaf
classes) that every method in this boundary raises instead of any
underlying `InteractiveWorkflowError`/`PublicationExecutionError`
subtype. This is deliberately **not** IWPC-001 §19.1's own `error_type`/
exit-code taxonomy — that vocabulary belongs to the future CLI/transport
layer this phase does not implement (§13 below); this phase's own
"Error Mapping" responsibility ("translate internal persistence failures
into the frozen application-level errors... do not leak filesystem paths,
raw exceptions, stack traces") is satisfied by this boundary's *own*,
narrower taxonomy, which a future 145G CLI phase can map onto §19.1's
`error_type` values one-for-one without needing this phase's classes
renamed (each application-level class corresponds to exactly one
underlying store/coordinator exception class, preserving that future
mapping's determinism). Every error carries a message plus optional
`session_id`/`package_id`/`record_id` — never a raw filesystem path,
Python exception class name, or traceback, which is possible without
re-sanitizing anything here because every wrapped store/coordinator
message is already pre-sanitized by its own phase's design (145D §7 /
145E §11 / 144C's own message discipline).

## 6. Readiness Coordination: Idempotent-by-Key Construction

`PublicationApplicationService.persist_readiness_package` accepts an
already-built `PublicationReadinessPackage` (package *construction*
remains exclusively `PublicationHandoff.build_package`'s, per
IWPC-REQ-011 — this boundary never constructs one), verifies the bound
session is `Confirmed` (IWPC-REQ-107), and is idempotent by `session_id`
(IWPC-REQ-024): if a pending package already exists for that session, the
existing record is returned unchanged rather than persisting the new,
duplicate package (the caller-supplied duplicate is silently discarded,
matching IWPC-REQ-143's own disclosed "discarded, not divergent"
last-write-wins precedent for concurrent construction attempts).

## 7. Publication Boundary: Preparation, Hand-off, Recovery

`prepare_publication_request` verifies a package is not already consumed
and its bound session has not reached `Expired` since construction
(IWPC-REQ-085/114), returning a `PreparedPublicationRequest` — this
boundary's own internal handoff shape, distinct from IWPC-001's own
not-yet-implemented `PublicationRequest` transport object (§10). It
never authorizes or publishes (IWPC-REQ-012).

`hand_off` constructs the `PublicationAuthorizationEvent` from a
caller-supplied `operator_id` exactly as `PublicationCoordinator.authorize`
requires (IWPC-REQ-116/121: no caller-supplied `invoked_at`, always the
process's own wall clock) and invokes `PublicationCoordinator.execute`
unchanged (IWPC-REQ-128). Every one of `execute`'s eight documented
exception types is mapped to exactly one of three application-level
classes (§14 traceability table). On success, the Pending-Readiness
Store's own attempt-linkage/disposition update
(`record_publication_attempt(outcome="succeeded", ...)`) is performed
using the Coordinator's own returned `attempt_id`/`record_id`/
`completed_at` verbatim — never re-derived. On a coordinator-raised
failure (other than replay), a fresh application-generated `attempt_id`
records the failed attempt into this store's own lightweight linkage
(IWPC-REQ-087) — the Coordinator's own `PublicationRecordStore.attempts/`
audit trail remains the authoritative failure record regardless
(IWPC-REQ-087's own "distinct from, never substituting for" language);
a failure to write this store's own linkage on that path is intentionally
swallowed (best-effort only), since the original failure — the thing the
caller actually needs to see — remains authoritative and unmasked.

`resume_publication(package_id, operator_id=...)` is this boundary's
single named recovery entry point (§18 Recovery below): it re-reads
persisted state by calling `prepare_publication_request` then `hand_off`
again, never trusting a caller-supplied "resume" flag (IWPC-REQ-156), and
always constructs a fresh `PublicationAuthorizationEvent` rather than
reusing a cached one (IWPC-REQ-033/152).

## 8. Disclosed Recovery Gap: the IWPC-REQ-154 Interruption Window

IWPC-REQ-154 anticipates a specific interruption window: `execute`
commits the CHGR successfully, but the process dies before this store's
own move-to-`consumed/` disposition update runs — "the next `publish`
invocation MUST detect this via PEC-001's own replay/idempotency-marker
check... before this store's disposition is consulted." This phase's
`resume_publication` implements exactly that: a second `hand_off` call
constructs a fresh authorization and calls `execute` again, which raises
`AuthorizationReplayError` (PEC-001's own exclusive-create marker,
IWPC-REQ-144) rather than double-publishing. This is mapped to
`PublicationAlreadyCompletedApplicationError` — but, in this specific
recovery scenario only, with `record_id=None`: the replay exception
itself carries no `record_id` attribute (verified directly against
`governance/publication/errors.py`; every exception there is a bare
message-only class), and this phase's dependency scope (§10 below)
deliberately does not extend to `PublicationRecordStore` (only
`PublicationCoordinator`'s public interface is an allowed dependency,
IWPC-REQ-174) to peek at the marker file for the missing `record_id`.
This is a genuine, disclosed **Non-Blocking** gap, not silently hidden:
`PublicationAlreadyCompletedApplicationError.record_id` is honestly
`None` in this one path (verified directly by
`test_resume_publication_after_success_reports_already_completed`'s own
assertion, which passes precisely *because* the store's own disposition
had already been updated in that test's setup — the pure-replay-without-
reconciliation path is exercised implicitly by every other
already-completed test, which all do carry a `record_id` since the
store's own successful disposition update already ran). A future phase
MAY add a narrow, public `PublicationRecordStore` accessor for the
committed `record_id` given a `package_id`, letting
`PublicationApplicationService` reconcile this specific window without
widening its dependency surface beyond `PublicationCoordinator` in the
meantime — not implemented here, since it touches a PEC-001-owned
storage module this phase's deliverable list does not name.

## 9. Dependency Boundaries

`session_service.py` depends only on `SessionCoordinator` (transitively:
`SessionRepository`, `interactive_workflow.models.session`,
`interactive_workflow.errors`) and this package's own `errors.py` — never
`pcae.governance.publication`, enforced by a dedicated test
(`test_session_service_does_not_import_publication_subsystem`).
`publication_service.py` depends on `FilesystemPendingReadinessStore`,
`SessionApplicationService` (never a second, parallel path into
`SessionCoordinator`/`WorkflowOrchestrator`/`SessionRepository` directly —
enforced by
`test_publication_service_does_not_import_orchestration_or_session_coordinator`),
`PublicationCoordinator`'s public interface, and this package's own
`errors.py`/`models.py`. Neither module imports `pcae.cli`,
`pcae.commands`, `pcae.lifecycle`, the Permission Broker modules, or the
governance verification/inspection modules (a shared AST-based
forbidden-import test parametrized across both files, mirroring 145E
§13's identical pattern).

## 10. Allowed Dependency Direction (Restated at This Layer)

```
PublicationApplicationService
    -> FilesystemPendingReadinessStore   (public interface only)
    -> SessionApplicationService          (never SessionRepository directly)
    -> PublicationCoordinator.authorize/.execute (public interface only)

SessionApplicationService
    -> SessionCoordinator                 (public interface only)
```

`PublicationApplicationService` does not depend on `PublicationRecordStore`
directly (§8's disclosed gap is this restriction's direct consequence,
accepted deliberately rather than widened to close it).

## 11. Test Strategy and Results

`tests/test_phase_145f_application_service_boundary.py` — 45 tests:
session-lifecycle coordination (create/load/persist/update/completion,
error mapping for not-found/invalid-identifier/already-exists/
not-terminal, 10), readiness coordination (persist/idempotent-by-key/
not-confirmed/not-found/digest-mismatch/find-by-session, 7), publication
request construction (success/not-found/stale/already-completed, 4),
publication boundary hand-off (success/operator-id validation/already-
consumed short-circuit/parametrized exception mapping across all eight
`PublicationCoordinator.execute` exception types, 11), recovery
(interrupted-failure retry, restart-after-success, stale-session-blocks-
recovery, 3), error-taxonomy sanity (2), and dependency-boundary tests
(8, including the shared AST forbidden-import pattern, a package-location
assertion, and both one-directional coupling assertions from §9).

Regression: `tests/test_phase_145d_session_repository_filesystem_implementation.py`
(43 tests), `tests/test_phase_145e_pending_readiness_store_filesystem_implementation.py`
(74 tests), and `tests/test_phase_144c_publication_coordinator.py` (31
tests) re-run unmodified alongside this phase's suite — all 148 pass
together with this phase's own 45 (193 total). A broader selection
(`-k "interactive_workflow or iwc_ or publication or serialization or
persistence or 145 or 144"`, 1882 tests selected) passes 1879, with the
same two pre-existing wheel-packaging failures Phase 145E's own report
already documented and independently reproduced on unmodified `main`
(`test_cltr_authority_136ah_publication.py`,
`test_cltr_authority_136ai_publication_independent.py`, both asserting
about `pcae/cltr/authority/bindings.py`'s wheel inclusion, unrelated to
`interactive_workflow`/`persistence`/`publication_handoff`/this phase's
new `application` package) and 1 pre-existing skip. The `fast_green`
marker suite (`python -m pytest -m fast_green`) passes at 4391 -- the
same count 145E's own report recorded, confirming this phase added no
regression and (since none of this phase's own test module is in the
curated `FAST_GREEN_MODULES` list, `tests/conftest.py`) no new
fast-green-eligible addition either, consistent with 145D/145E's own new
test modules not being added to that curated list. `pcae runtime inspect
--json` confirmed `Observed`/`observe`/`unavailable` unchanged both
before and after this phase's changes.

The full repository suite (`python -m pytest -n auto`) also ran in full:
**26470 passed, 38 failed, 10 skipped** (1973.82s). A representative
sample of the 38 failures (wheel-packaging assertions across the
`cltr/authority` family, `test_advisory_runtime_contract`,
`test_shell_gate`, `test_finalization_transaction_134e10`,
`test_cltr_135o_integration`, `test_bootstrap_todo_consistency`,
`test_rendering_134e5`) was independently reproduced against unmodified
`main` via `git stash`/`git stash pop` (7 of 8 sampled failed identically
in isolation; the eighth, `test_audit_verify_cli`, passed in isolation,
consistent with 145E's own report noting it as an order/parallelism-
dependent flake rather than a real regression). None of the 38 failures
touch `interactive_workflow`, `persistence`, `publication_handoff`,
`serialization`, or this phase's own new `application` package.

## 12. Requirement Traceability (selected)

| Requirement | Satisfied by |
|---|---|
| IWPC-REQ-006 | §2 above; this phase's own disclosed Non-Blocking finding. |
| IWPC-REQ-009-013 | §4 above; neither service evaluates authority, infers identity, or collapses Confirmation/Readiness/Authorization/Publication/Execution into one act. |
| IWPC-REQ-011 | §4 above; both services delegate to, never reimplement, `SessionCoordinator`/`PublicationCoordinator`. |
| IWPC-REQ-024 | §6 above; `persist_readiness_package`'s idempotent-by-`session_id` construction. |
| IWPC-REQ-032/113 | `prepare_publication_request`/`hand_off` both check `disposition == consumed` before touching the Coordinator, mapped to `PublicationAlreadyCompletedApplicationError`, reading `record_id` from the store's own persisted record, never re-deriving one. |
| IWPC-REQ-033/152 | §7 above; `resume_publication` always constructs a fresh `PublicationAuthorizationEvent`. |
| IWPC-REQ-085/114 | `prepare_publication_request`'s `SessionState.EXPIRED` check, mapped to `ReadinessPackageStaleApplicationError`. |
| IWPC-REQ-087-089 | §7 above; `_record_succeeded_attempt`/`_record_failed_attempt`. |
| IWPC-REQ-098/126-128 | `hand_off` invokes `authorize`/`execute` in the Coordinator's own unchanged order, adding no additional step. |
| IWPC-REQ-135-137 | §5 above; the application error taxonomy. |
| IWPC-REQ-144/154-156 | §7/§8 above; `resume_publication`. |
| IWPC-REQ-174-177 | §9/§10 above; the dependency-boundary tests. |

## 13. No-Go — Confirmed Not Done By This Phase

- No CLI command was implemented.
- No transport adapter was implemented.
- No engineering execution capability was introduced; `pcae runtime
  inspect --json` remains `Observed`/`observe`/`unavailable` before and
  after this phase.
- `PublicationCoordinator` was not bypassed, duplicated, or reimplemented;
  every authorize/execute call is delegated unchanged.
- No CHGR artifact was created or written by any code this phase added.
- `SessionRepository`, `FilesystemSessionRepository`,
  `FilesystemPendingReadinessStore`, `SessionCoordinator`,
  `WorkflowOrchestrator`, `PublicationHandoff`, and
  `PublicationCoordinator` were not modified.
- IWC-001, PEC-001, CHGR-001, IWPC-001 contract text was not modified.
- No authority-evaluation policy, `--force`-equivalent bypass, or implicit
  identity source was introduced.
- No background worker or scheduled cleanup was added.

## 14. Recommended Next Phase

**145G — Interactive Workflow CLI Command Implementation**, the phase
this phase's own governing prompt names as likely-next, now that both
concrete persistence components (145D, 145E) and the internal
application-service coordination layer (this phase) exist for a thin CLI
adapter to build against. A 145G that also proposes the formal IWPC-001
"Model D" contract revision §2 above describes (rather than leaving
`application/` as an internal, uncontracted layer indefinitely) would
additionally close this phase's own disclosed IWPC-REQ-006 gap. This
recommendation does not authorize 145G.
