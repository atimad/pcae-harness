# Phase 143K — Interactive Workflow Session Infrastructure Architecture and Skeleton Implementation

**Status:** Complete
**Mode:** Implementation, of the Interactive Workflow subsystem's
foundational session infrastructure only — session domain model, session
identity, a structural State Machine skeleton, a persistence abstraction
(interfaces only, no storage technology selected), a deterministic
serialization framework, an invariant validation framework, an
infrastructure error model, package layout, and unit tests. No executable
governance workflow, no CHGR creation, no human governance decision is
possible from this code. The implementation is structurally complete but
functionally inert outside explicitly authorized infrastructure.
**Governing authority:** IWC-001 v1.1
(`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md`), CHGR-001
(`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`), Phase
143J implementation plan
(`docs/PHASE_143J_CANONICAL_HUMAN_GOVERNANCE_RECORD_INTERACTIVE_DECISION_WORKFLOW_IMPLEMENTATION_PLANNING.md`),
Phase 143I.1/143I.2 (state-transition table widening and its independent
verification), TAMC-001, TAMPC-001.
**Runtime:** Observed / observe / unavailable (unchanged by this phase)
**Deliverable:** this document, the `pcae.interactive_workflow` package,
unit tests, this phase report.

> **This code exists to give later phases a stable, contract-conformant
> foundation to build on. It does not itself run any part of the
> Interactive Workflow. Nothing in this package can create a CHGR, drive a
> confirmation, or grant authority.**

---

## 0. Method and Scope Reconciliation

Phase 143J's own recommended phase decomposition (§17) scoped **143K** to
the Session Persistence Interface, the Session Coordinator, and the Error
Model, with the **State Machine explicitly assigned to Phase 143L**
("Transition engine: State Machine … depends on 143K"). This phase's
actual governing prompt includes "State Machine Skeleton" in 143K's scope
directly, alongside an explicit instruction: *"Do not implement transition
execution logic beyond the minimum needed to construct valid session
objects. No workflow orchestration."*

This phase reconciles the two by implementing only the **structural**
half of the State Machine in 143K — the ten-state definitions and the
widened transition table as data
(`pcae.interactive_workflow.state_machine.transitions`), plus a pure,
side-effect-free transition-legality predicate. It does **not** implement
the transition *engine*: no persistence-on-transition, no resumability
sequencing, no lazy-timeout evaluation, no requirement that a
Confirmation Engine result be in hand before accepting a transition into
`Confirmed`. Those remain Phase 143L's scope, as 143J planned. This is a
disclosed, narrow, structural-only interpretation of "State Machine
skeleton," consistent with the governing prompt's own explicit
instruction quoted above — the same disclosure discipline Phase 143J used
for its own two adjustments to the governing prompt's suggested phase
split (143J §17).

The governing prompt's Persistence Abstraction section is stricter than
Phase 143J §6.8's plan: 143J allowed 143K to choose a default
file-based implementation; the actual 143K governing prompt states
explicitly *"Do not select: SQLite, JSON, PostgreSQL, filesystem, cloud
storage. Storage technology remains deliberately deferred."* This phase
follows the governing prompt: `SessionRepository`
(`pcae.interactive_workflow.persistence.repository`) is an abstract
interface with **no concrete implementation** anywhere in this package.

---

## 1. Required Initial Actions (performed)

1. Bootstrapped a governed PCAE session (`pcae session bootstrap
   --agent-id claude-local`).
2. Confirmed a clean repository (`git status --short`, no output).
3. Confirmed no active governed phase (prior active task was the idle
   placeholder left by Phase 143J's closure).
4. Read in full: CHGR-001, IWC-001 v1.1 (including its §24 widening
   history), Phase 143J, Phase 143I.2, and the repository's existing
   `pcae.cltr`/`pcae.cltr_prototype` packages as the closest structural
   precedent for a new subsystem's package layout, error hierarchy, and
   test organization convention.
5. Closed the idle task, added a new `interactive_workflow` architecture
   zone to `.pcae/policy.toml` (self-contained; depends on no other
   production zone), and created this phase's task contract before
   `pcae phase start`.

Phase 143J's implementation plan was treated as evidence of the intended
architecture, not as a substitute for reading IWC-001 v1.1 and CHGR-001
directly. The domain model, identity rule, transition table, and
error-model naming below were each independently checked against IWC-001
v1.1's contract text (not merely against 143J's summary of it).

---

## 2. Implemented Package

```
src/pcae/interactive_workflow/
    __init__.py
    errors.py                     # infrastructure error hierarchy
    models/
        __init__.py
        session.py                 # SessionState (10 states), Session, TERMINAL_STATES
    session/
        __init__.py
        identity.py                 # CDS-<uuid4> generation/validation
        coordinator.py               # SessionCoordinator skeleton
    state_machine/
        __init__.py
        transitions.py                # widened 10-state transition table as data
    persistence/
        __init__.py
        repository.py                  # SessionRepository (abstract, no backend)
        migration.py                    # migration-hook registry skeleton
    serialization/
        __init__.py
        schema.py                        # to_payload/from_payload
    validation/
        __init__.py
        invariants.py                     # structural invariant validators
```

Layout deviates from the governing prompt's illustrative example
(`session/`, `persistence/`, `state_machine/`, `validation/`, `errors/`,
`models/`, `interfaces/`) in two independently-justified ways, per the
prompt's own "Alternative layout is acceptable if independently
justified" clause:

- **`errors/` is a single `errors.py` module**, not a package, mirroring
  `src/pcae/cltr/authority/errors.py` (this repo's existing precedent for
  a Layer-3 error hierarchy as one dedicated file) and matching Phase
  143J §3's own characterization of the Error Model as "a shared
  cross-cutting concern … data/contract, not a running piece of
  software" — there is no internal structure large enough to warrant a
  package.
- **No standalone `interfaces/` package.** The one interface this phase
  defines, `SessionRepository`, lives with its persistence contract
  documentation in `persistence/repository.py`; a separate `interfaces/`
  package would hold nothing but a re-export.

## 3. Dependency Direction

`.pcae/policy.toml`'s new `interactive_workflow` zone declares
`interactive_workflow = ["interactive_workflow"]` — it depends on **no**
other production zone (not `core`, `cltr`, `commands`, or `governance`),
matching the governing prompt's dependency rule ("Infrastructure may
depend upon: shared PCAE utilities. Infrastructure shall not depend upon:
CHGR production, publication, runtime authority, transport UI, CLI,
execution engine"). Nothing in this package imports from
`pcae.governance`, `pcae.schema_resources.chgr`, `pcae.cltr`, `pcae.cli`,
or `pcae.commands`. Internal dependency direction (`errors` and `models`
depend on nothing else in the package; `session/identity.py` depends on
`errors`; `state_machine/transitions.py` depends on `models`;
`persistence/repository.py` depends on `models`; `serialization/schema.py`
depends on `models` and `errors`; `validation/invariants.py` depends on
`errors`, `models`, `session/identity.py`, and
`state_machine/transitions.py`; `session/coordinator.py` depends on all of
the above) is acyclic and mirrors Phase 143J §16's layering (foundational:
persistence interface + error model; next layer: state machine; next
layer: coordinator).

## 4. Session Domain Model

`SessionState` enumerates exactly the ten canonical states from IWC-001
v1.1 §4.4 (IWC-REQ-040), no more, no fewer: `Created`, `EvidenceReady`,
`AwaitingDecision`, `AwaitingClarification`, `DecisionSelected`,
`AwaitingConfirmation`, `Confirmed`, `Cancelled`, `Expired`, `Abandoned`.
`TERMINAL_STATES` names the four terminal states (`Confirmed`,
`Cancelled`, `Expired`, `Abandoned`).

`Session` is a frozen dataclass carrying identity, ownership, template and
subject binding, the in-scope Decision Capture fields
(`human_selection_id`, `human_rationale_text`, `human_conditions_text`,
`disclosure_acknowledgements`), current `session_state`, `schema_version`,
timestamps, and a frozen `metadata` mapping as the sanctioned
future-compatible extension point. Evidence snapshots, confirmation
evidence, clarification logs, and Preview Digest content are **not**
fields on this model — the governing prompt's Serialization section
excludes them explicitly, and no component that would populate them
(Evidence Coordinator, Confirmation Engine, Preview Builder, Clarification
Controller) exists yet.

## 5. Session Identity

`pcae.interactive_workflow.session.identity` implements `CDS-<uuid4>`
generation and validation (IWC-001 v1.1 §4.1, IWC-REQ-033–035):
immutable, uuid4-collision-resistant (no central counter), carries no
lifecycle or authority information. `test_session_identity_carries_no_authority_information`
and `test_session_id_rejects_chgr_prefix` (both in the test suite below)
check the identifier is structurally distinct in prefix from CHGR's
`chgr-<uuid4>` and carries nothing beyond the bare uuid4 body.

## 6. State Machine Skeleton (structural only)

`pcae.interactive_workflow.state_machine.transitions.TRANSITION_TABLE` is
the widened ten-state table (post-143I.1, independently verified by
143I.2) as an immutable mapping — table-as-data, not an `if`/`elif`
chain, so the same structure a future test suite enumerates from is the
structure the code itself checks against (Phase 143J §5.2/§15's stated
design principle for the *full* engine, applied here to the skeleton).
`is_valid_transition(current, target)` is a pure lookup with no I/O and no
orchestration. Terminal states carry an explicitly empty exit set,
asserted at import time (`assert TRANSITION_TABLE[state] == frozenset()
for state in TERMINAL_STATES`) so a future edit that accidentally gives a
terminal state an exit fails immediately and loudly, not silently at
first use.

Deliberately **not** implemented here (Phase 143L's scope per §0 above):
transition execution, state persistence-on-transition, resumability
sequencing, lazy timeout evaluation, or the Confirmation Engine
precondition on entry to `Confirmed`.

## 7. Persistence Abstraction

`pcae.interactive_workflow.persistence.repository.SessionRepository` is an
`abc.ABC` with five abstract methods (`create`, `load`, `persist`,
`exists`, `list_session_ids`) and no concrete subclass anywhere in this
package — `SessionRepository()` cannot be instantiated
(`test_session_repository_cannot_be_instantiated_directly`). The module
documents the persistence contract (fail-closed on read/write failure, no
partial mutation, no semantic interpretation of session state) and names
`CHGR_STORAGE_PREFIX = ".pcae/governance-records/"` as a path no
implementation may write under (IWC-001 v1.1 §4.10, IWC-REQ-049).
`pcae.interactive_workflow.persistence.migration.MigrationRegistry` is the
migration-hook extension point: a registry from source `schema_version` to
migration callable, with nothing registered yet (there is exactly one
schema version so far).

## 8. Serialization Framework

`pcae.interactive_workflow.serialization.schema.to_payload`/`from_payload`
convert a `Session` to and from a plain, JSON-compatible `dict` carrying
`schema_version`, identity, state, timestamps, Decision Capture fields,
and the metadata container. `from_payload` raises
`UnsupportedVersionError` for any `schema_version` not in
`_KNOWN_SCHEMA_VERSIONS` — never falls back to "assume latest." Preview
Digest, evidence, confirmation, publication, and CHGR fields are absent
from the payload because they are absent from `Session` itself (§4 above);
`test_serialization_excludes_out_of_scope_fields` checks this directly.

## 9. Invariant Validation Framework

`pcae.interactive_workflow.validation.invariants` provides
`validate_identifier`, `validate_known_state`,
`validate_terminal_integrity`, `validate_required_metadata`,
`validate_version`, and a `validate_session` composition. Each validates
exactly one structural concern and raises rather than repairs.
`validate_terminal_integrity` is the one function that reasons about two
states at once (current, proposed) — it checks both terminal-exit
prohibition and table membership, but never *why* a transition might be
desirable, matching the governing prompt's "Do not validate workflow
semantics."

## 10. Error Model

`pcae.interactive_workflow.errors` defines `InteractiveWorkflowError` and
six leaf errors named directly from the governing prompt's own examples:
`SessionNotFoundError`, `InvalidSessionStateError`,
`InvalidIdentifierError`, `UnsupportedVersionError`,
`PersistenceUnavailableError`, `SerializationFailureError`. One addition
beyond the prompt's list, `InvariantViolationError`, covers structural
invariant failures not specific to state or identity (currently: missing
required metadata) — a minimal, disclosed extension of the named set, not
a replacement for it. No workflow-semantic error (invalid transition
*attempted mid-workflow*, ownership mismatch on resume, confirmation
digest mismatch) is defined here; those are deferred to the phase that
implements the behavior they guard.

## 11. Session Coordinator Skeleton

`pcae.interactive_workflow.session.coordinator.SessionCoordinator` is
constructed with an injected `SessionRepository` (constructor-only
dependency injection — no global singleton, no module-level registry). It
implements `create_session`, `load_session`, `persist_session`,
`validate_state`, and `register_lifecycle_hook`. `orchestrate_evidence`,
`perform_confirmation`, and `perform_publication` exist as named methods
that unconditionally raise `NotImplementedError` with an explanatory
message — a deliberate choice over simply omitting the methods, so a
caller reaching for out-of-scope behavior gets a typed, deterministic
refusal instead of an `AttributeError`. The class has **no** `publish` or
`confirm` method at all (`test_session_coordinator_has_no_publish_or_confirm_that_succeeds`)
— those aren't even stubbed, since nothing in 143K plans to ever host them
on this class per Phase 143J §4's Responsibility Matrix ("Prohibited"
column for Session Coordinator: "Selecting on human's behalf; inferring
consent; computing 'is this authoritative'"). `register_lifecycle_hook`
only appends to a list; there is no code path in 143K that invokes a
registered hook, since driving a transition is Phase 143L's transition
engine, not this skeleton
(`test_coordinator_registers_lifecycle_hooks_without_invoking_them`).

---

## 12. Requirement Traceability

| IWC-001 v1.1 requirement range | Concern | Implemented in |
|---|---|---|
| IWC-REQ-033–035 (§4.1, identity) | `CDS-<uuid4>` generation/validation, authority-neutral | `session/identity.py` |
| IWC-REQ-036–037 (§4.2, identity binding) | `owner_identity` field carried on `Session`; re-check on resume deferred to 143L | `models/session.py` (field); resume logic explicitly out of scope |
| IWC-REQ-038–039 (§4.3, template/subject binding) | `template_ref`/`subject_ref` immutable fields | `models/session.py` |
| IWC-REQ-040 (§4.4, ten states) | `SessionState` enum, exactly ten members | `models/session.py` |
| IWC-REQ-042 (§4.4, no unlisted transition / terminal finality) | `TRANSITION_TABLE` as data, terminal states with empty exit sets, asserted at import | `state_machine/transitions.py` |
| IWC-REQ-043–044 (§4.5, resumability) | Not implemented — resumability sequencing is transition-engine behavior, deferred to 143L | — (disclosed deferral) |
| IWC-REQ-045–046 (§4.7, expiry) | `Expired` is a reachable terminal state from every active state in the table; lazy evaluation itself deferred to 143L | `state_machine/transitions.py` (table only) |
| IWC-REQ-047–048 (§4.8, cancellation) | `Cancelled` is a reachable terminal state from every active state; cancellation *execution* deferred to 143L | `state_machine/transitions.py` (table only) |
| IWC-REQ-049 (§4.10, persistence boundary) | `SessionRepository` interface; `CHGR_STORAGE_PREFIX` named as forbidden write target | `persistence/repository.py` |
| Phase 143J §6.5 (schema versioning) | `schema_version` field, independent version-compatibility check | `models/session.py`, `serialization/schema.py`, `validation/invariants.py` |
| Phase 143J §12 (error model) | Six named errors + one disclosed addition | `errors.py` |
| Phase 143J §16 (dependency layering) | `.pcae/policy.toml` `interactive_workflow` zone, self-contained | `.pcae/policy.toml` |

IWC-REQ-137–142 (Privacy) and IWC-REQ-143–161 (Security, Transport
Independence) are cross-cutting and, per Phase 143J §18, span 143K
through later phases with a compatibility check at 143P — this phase's
contribution is limited to "design only; policy deferred," i.e. the
persistence interface names the forbidden storage location and nothing
else claims a privacy/security guarantee it does not implement.

---

## 13. Validation Evidence

```
$ python -m pytest tests/test_iwc_143k_session_infrastructure.py -v
============================== 61 passed in 0.05s ==============================
```

`pcae health`, `pcae check`, `pcae doctor task-memory`, the full
`python -m pytest -n auto` suite, and `python -m pytest -m fast_green -n
auto` results are recorded in the canonical phase-completion report
produced by `pcae phase complete` (§16 below), not duplicated here to
avoid the two ever silently diverging.

---

## 14. Compatibility Verification

- **CHGR-001**: not modified; not imported; no `chgr-` identifier
  produced anywhere in this package; no write under
  `.pcae/governance-records/`.
- **IWC-001 v1.1**: not modified; the ten-state model and the widened
  §4.4 transition table are reproduced exactly, cross-checked against the
  contract text directly (not only against Phase 143J's summary).
- **TAMC-001 / TAMPC-001**: not modified; not imported; no Typed
  Authority Model consumption occurs anywhere in this package.
- **Runtime**: `pcae runtime inspect` unchanged — Observed / observe /
  unavailable before and after this phase.

---

## 15. Security

Every unimplemented path in this package fails closed: `SessionRepository`
cannot be instantiated without a concrete subclass implementing all five
methods; `SessionCoordinator.orchestrate_evidence` /
`perform_confirmation` / `perform_publication` raise
`NotImplementedError` unconditionally; there is no `publish` or `confirm`
method to accidentally call; `from_payload` refuses any unrecognized
`schema_version` rather than guessing; `validate_terminal_integrity`
refuses any exit attempt from a terminal state. Nothing in this package
can create authority, create a governance decision, create a CHGR,
publish a record, or bypass confirmation, because none of the code paths
that would do any of those things exist yet.

---

## 16. Exit Criteria (per governing prompt)

1. Session infrastructure exists — ✅ (`models/`, `session/`)
2. State model exists — ✅ (`models/session.py`, ten states, no more/fewer)
3. Repository abstraction exists — ✅ (`persistence/repository.py`, interface only)
4. Serialization framework exists — ✅ (`serialization/schema.py`)
5. Validation framework exists — ✅ (`validation/invariants.py`)
6. Error model exists — ✅ (`errors.py`)
7. Infrastructure tests pass — ✅ (61/61, see §13)
8. No workflow behavior exists — ✅ (no evidence orchestration, clarification, preview, confirmation, cancellation/expiry/abandonment execution, or publication code path exists)
9. No authority capability exists — ✅ (identity is authority-neutral; no authority field, no consent inference)
10. Runtime remains unchanged — ✅ (Observed / observe / unavailable)

---

## 17. Recommended Next Phase

**143L — Interactive Workflow Transition Engine Implementation**, per the
governing prompt's own stated expectation and Phase 143J §17's
decomposition: implement transition *execution* (persistence-on-transition,
resumability sequencing per IWC-001 v1.1 §4.5, lazy timeout evaluation per
§4.7, the Confirmation Engine precondition on entry to `Confirmed`) on top
of the structural table this phase built. This recommendation does not
authorize 143L.

---

## 18. No-Go — Confirmed Not Done By This Phase

Not implemented, per the governing prompt's explicit deferral list:
evidence orchestration, clarification, preview generation, Preview
Digest, confirmation, cancellation workflow execution, expiry workflow
execution, abandonment workflow execution, publication handoff, CHGR
creation, runtime consumption, transport UI, CLI workflow, Web/API
workflow, execution capability. No concrete `SessionRepository`
implementation (SQLite/JSON/PostgreSQL/filesystem/cloud) was selected or
built. No transition *execution* logic beyond the minimum needed to
represent and structurally validate a `Session` object was implemented.
