# Phase 143L — Interactive Workflow Transition Engine Implementation

**Status:** Complete
**Mode:** Implementation, of the Interactive Workflow subsystem's
Transition Engine only — transition legality determination and in-memory
state evolution. No workflow orchestration, no governance decision, no
confirmation, no publication, no CHGR creation is possible from this
code.
**Governing authority:** IWC-001 v1.1
(`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md`), CHGR-001
(`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`), Phase
143J implementation plan
(`docs/PHASE_143J_CANONICAL_HUMAN_GOVERNANCE_RECORD_INTERACTIVE_DECISION_WORKFLOW_IMPLEMENTATION_PLANNING.md`),
Phase 143K (Session Infrastructure, this phase's direct foundation),
Phase 143I.1/143I.2 (state-transition table widening and its independent
verification), TAMC-001, TAMPC-001.
**Runtime:** Observed / observe / unavailable (unchanged by this phase)
**Deliverable:** this document, the `pcae.interactive_workflow.
state_machine` Transition Engine (registry, validator, policy, engine,
metadata model, extended error hierarchy), unit/regression/adversarial
tests, this phase report.

> **This code determines whether a proposed session-state transition is
> legal and, if so, evolves an in-memory `Session` object accordingly. It
> performs no persistence write, no evidence collection, no
> clarification, no confirmation, no publication, and creates no CHGR.**

---

## 0. Method and Scope Reconciliation

Phase 143K's own report (§0) disclosed a narrow, structural-only reading
of "State Machine skeleton" — the ten-state definitions and the widened
`TRANSITION_TABLE` as data, plus a pure legality predicate
(`is_valid_transition`) with no orchestration, no persistence side
effect, and no workflow reasoning — and explicitly deferred the
transition *engine* to this phase, consistent with Phase 143J §17's own
decomposition. This phase implements exactly that deferred engine, and
nothing beyond it.

This phase's own governing prompt further narrows scope beyond "engine":
it explicitly excludes evidence orchestration, clarification, preview,
confirmation, publication, CHGR creation, persistence writes, and
transport/CLI/Web/API/execution capability — all deferred to 143M
onward (per Phase 143J's plan) or to phases not yet scheduled
(Publication Handoff, per Phase 143J §3's interface-only disposition).
The Transition Engine built here is therefore narrower than "the thing
that drives a session through its lifecycle" — it is the single
component every future orchestrator (Session Coordinator, and later the
Evidence Coordinator / Clarification Controller / Confirmation Engine)
must call to ask "is this transition legal?" and "apply it," and nothing
more.

---

## 1. Required Initial Actions (performed)

Before writing any code:

1. Bootstrapped a governed PCAE session (`pcae session bootstrap
   --agent-id claude-local`) — confirmed healthy, active task none,
   latest completed phase 143K, repo clean.
2. Confirmed the repository was clean (`git status`) before opening the
   task contract.
3. Confirmed no active governed phase (`tasks/active/` empty; `pcae
   check` had no active task until this phase's own task contract was
   created).
4. Read completely, directly from source, not from any phase's own
   summary:
   - IWC-001 v1.1 (`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md`,
     §4.4 in particular, the widened ten-state transition table)
   - CHGR-001 (`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`)
   - Phase 143J's implementation plan
   - Phase 143K's report and its full `pcae.interactive_workflow`
     package source (`models/session.py`, `state_machine/transitions.py`,
     `errors.py`, `session/coordinator.py`, `validation/invariants.py`,
     `serialization/schema.py`, `persistence/repository.py`,
     `session/identity.py`, `persistence/migration.py`)
   - Phase 143I.1 (state-transition table repair) and 143I.2
     (independent verification of that repair)
   - TAMC-001 / TAMPC-001 (grep-confirmed no reference to Interactive
     Workflow session states, as 143I.1 already established and this
     phase re-confirmed by direct grep before writing code)
   - `PROJECT_STATUS.md` (current-phase and prior-phase summaries)

Every prior implementation (143K's package) was treated as evidence of
established conventions (dependency-injection constructors, frozen
dataclasses, fail-closed errors, table-as-data) to reuse, not as a
pre-answered design decision for this phase's own scope.

---

## 2. Implemented Package

```
src/pcae/interactive_workflow/
  __init__.py                      (docstring updated: 143K + 143L scope)
  errors.py                        (extended: TransitionError family)
  state_machine/
    __init__.py                    (extended: re-exports engine surface)
    transitions.py                 (143K, unmodified — TRANSITION_TABLE)
    registry.py                    (NEW — TransitionRegistry)
    validator.py                   (NEW — TransitionValidator)
    policy.py                      (NEW — TransitionPolicy)
    metadata.py                    (NEW — TransitionMetadata)
    engine.py                      (NEW — TransitionEngine, TransitionResult)
tests/
  test_iwc_143l_transition_engine.py  (NEW — 449 tests)
```

No file outside `src/pcae/interactive_workflow/`, `tests/test_iwc_143l_*.py`,
this document, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`, and
`.pcae/*` governance-bookkeeping files was touched.

---

## 3. Dependency Direction

`state_machine.engine` depends on `state_machine.{registry,validator,
policy,metadata}`, `models.session`, and (function-scope, to avoid a
circular import — see §9) `validation.invariants.validate_version`. It
does **not** depend on `session.coordinator`, `persistence.*`, or
`serialization.*` — the Session Coordinator will depend on the Transition
Engine in a future phase, never the reverse, preserving the acyclic
dependency graph Phase 143J §16 required. Nothing in `state_machine`
imports from outside `pcae.interactive_workflow`.

---

## 4. Transition Registry

`TransitionRegistry` (`state_machine/registry.py`) is a stateless,
read-only inspection object wrapping the existing, unmodified
`TRANSITION_TABLE`. It adds no transition data — `all_states`,
`permitted_targets`, `is_registered`, `is_terminal`, and
`all_transitions` are all pure lookups against the same table Phase 143K
built and Phase 143I.1 widened. This satisfies the governing prompt's
"deterministic and inspectable" requirement (`all_transitions()` yields
every `(source, target)` pair in a stable, sorted order) without
duplicating or reinterpreting the canonical data.

---

## 5. Transition Validator

`TransitionValidator` (`state_machine/validator.py`) is the sole
production determination of whether one proposed `source -> target`
transition is legal. Checks run in a fixed order — unknown state,
duplicate/no-op, terminal-state exit, unsupported (untabled) transition —
so a given illegal input always raises the same error type
(determinism). It fails closed: the first violated rule raises
immediately; no check is skipped, no default assumed.

---

## 6. Transition Policy

`TransitionPolicy` (`state_machine/policy.py`) enforces the one invariant
the Validator cannot check from a single `Session` alone: sequence
monotonicity. It has no configuration surface — "fail-closed" is not a
toggle, per the governing prompt's own instruction that "no transition
rules may exist outside the Transition Engine" (interpreted here to
include the sequence-monotonicity rule, which the Engine composes from
Policy + Validator rather than re-implementing).

---

## 7. Transition Engine

`TransitionEngine` (`state_machine/engine.py`) is the sole owner of:

- legal transition determination (`is_legal`, never raises)
- illegal transition rejection (`apply`, raises deterministically)
- terminal-state enforcement (delegated to the Validator, which the
  Engine always consults before mutating anything)
- transition invariant enforcement (version compatibility, identity
  preservation, sequence monotonicity)
- deterministic transition errors (the `TransitionError` family)

`apply()` never mutates its input `Session` (a frozen dataclass); on
success it returns a `TransitionResult` holding a *new* `Session`
(identity and schema version preserved) and a `TransitionMetadata`
record. On failure, it raises before constructing anything — no partial
`TransitionResult`, no partially-applied state.

The Session Coordinator (`session/coordinator.py`, Phase 143K) is
unmodified by this phase and does not yet call the Transition Engine —
wiring the Coordinator's orchestration to this Engine is deferred to
Phase 143M/143N's own scope (evidence/clarification/confirmation
orchestration), consistent with "This phase shall not implement workflow
orchestration."

---

## 8. Transition Metadata

`TransitionMetadata` (`state_machine/metadata.py`) is a frozen dataclass
with exactly six fields: `session_id`, `previous_state`, `new_state`,
`transition_timestamp`, `transition_sequence_number`, and the optional
`transition_reason`. No authority or identity information beyond
`session_id` exists on this type — verified by an explicit test
(`test_transition_metadata_carries_no_authority_field`) that asserts the
dataclass field set exactly.

---

## 9. Error Model

Six new errors, all subclassing a new `TransitionError` base (itself an
`InteractiveWorkflowError`, per the existing 143K hierarchy):
`UnknownStateError`, `DuplicateTransitionError`,
`TerminalStateViolationError`, `UnsupportedTransitionError`,
`InvalidTransitionSequenceError`, `InvalidTransitionError` (the last
serving as both the fallback for malformed-session input and a general
`TransitionError` a caller can catch without enumerating every subtype).

**Disclosed implementation note (circular import):**
`pcae.interactive_workflow.validation.invariants` already imports
`pcae.interactive_workflow.state_machine.transitions` (for
`is_valid_transition`, a 143K dependency). Because
`state_machine/__init__.py` now eagerly re-exports `TransitionEngine`
from `engine.py`, a module-level `from ...validation.invariants import
validate_version` inside `engine.py` would create a circular import
(`validation.invariants` → `state_machine` (package `__init__`) →
`state_machine.engine` → `validation.invariants`, not yet finished
initializing). Resolved by deferring that one import to function scope
inside `TransitionEngine.apply` — `validate_version` is still called on
every `apply()` invocation, before any other check; only the import
timing changed, not the enforcement. This is the same category of
layering concern Phase 143J §16 anticipated ("acyclic dependency graph")
and is disclosed here rather than silently worked around.

---

## 10. Invariant Enforcement

- **Valid state** — `TransitionValidator` rejects any non-`SessionState`
  value for either source or target (`UnknownStateError`).
- **Valid transition** — `TransitionValidator` rejects any pair absent
  from the registry (`UnsupportedTransitionError`) and any terminal-state
  exit (`TerminalStateViolationError`).
- **Terminal integrity** — re-verified structurally: every terminal
  state's registry exit set is asserted empty (inherited from 143K's own
  `TRANSITION_TABLE` assertion, re-checked at the registry layer by a
  dedicated test).
- **Sequence monotonicity** — `TransitionPolicy.validate_sequence`
  requires a non-negative int, strictly greater than any given
  `previous_sequence_number`.
- **Session identity immutability** — `Session.with_state` (143K)
  structurally preserves `session_id`; the Engine additionally asserts
  this post-construction (`InvalidTransitionError` if ever violated) as
  a defense-in-depth check, and a dedicated test confirms it holds.
- **Version compatibility** — `validate_version` (143K, reused) is called
  on every `apply()`, rejecting any `schema_version` this package does
  not explicitly recognize.

Workflow semantics (why a transition is *desirable*, not merely legal)
remain deferred, per the governing prompt.

---

## 11. Test Strategy and Results

`tests/test_iwc_143l_transition_engine.py` — **449 tests, all passing**:

- **Legal transitions**: every `(source, target)` pair present in
  `TRANSITION_TABLE`, generated programmatically (not hand-enumerated),
  checked against both `TransitionValidator` and `TransitionEngine`.
- **Illegal transitions**: every `(source, target)` pair *absent* from
  the table (excluding same-state pairs, covered separately as
  duplicates), generated as the table's complement over the full 10×10
  state product.
- **Terminal behavior**: every terminal state tested against every
  possible target, confirming `TerminalStateViolationError` (or
  `DuplicateTransitionError` for the same-state case) in all cases, and
  confirming the registry's own empty exit set.
- **Identity preservation / Version preservation / Metadata /
  Determinism / Fail-closed behavior**: each its own dedicated test
  group, per the governing prompt's own required categories.
- **Phase 143I.1 (B-1) regression matrix**: the nine specific cells
  Phase 143I.1 added (`Created→{Cancelled,Expired,Abandoned}`,
  `EvidenceReady→Cancelled`,
  `AwaitingClarification→{Cancelled,Expired,Abandoned}`,
  `DecisionSelected→Abandoned`, `AwaitingConfirmation→Abandoned`) are
  each independently re-verified through the live Transition Engine
  (not just read from the table), plus a universal-availability test
  confirming every non-terminal state can reach all three of
  `Cancelled`/`Expired`/`Abandoned` directly — the exact property
  IWC-REQ-045/046/047/160 required and B-1 found violated.
- **Adversarial testing**: unknown source state, unknown destination
  state, transition replay (same sequence number reused),
  terminal replay, reverse transition, skipped transition, duplicate
  transition, invalid metadata, invalid version, malformed session — all
  eleven of the governing prompt's named scenarios (plus two additional
  sequence-number edge cases), each confirmed to fail deterministically
  with a specific `TransitionError` subtype.
- **Structural compatibility**: a `TransitionResult.session` round-trips
  through 143K's `serialization.schema.to_payload`/`from_payload` and
  passes 143K's own `validation.invariants.validate_session`, confirming
  no architectural coupling was broken.

```
$ python -m pytest tests/test_iwc_143k_session_infrastructure.py tests/test_iwc_143l_transition_engine.py -q
510 passed in 0.15s
```

`pcae health`, `pcae check`, `pcae doctor task-memory`, the full `python
-m pytest -n auto` suite, and `python -m pytest -m fast_green -n auto`
results are recorded in the canonical phase-completion report produced by
`pcae phase complete` (§16 below), not duplicated here to avoid the two
ever silently diverging.

**Disclosed test-authoring correction:** the first draft of
`_all_legal_pairs()` iterated a `frozenset` of target states directly
without sorting. `SessionState` is a `str` `Enum`, and Python's per-process
string-hash randomization means `frozenset` iteration order differs across
`pytest-xdist` worker processes — the first full-suite run under `-n auto`
failed with "Different tests were collected between gw0 and gwN" because
each worker parametrized a different test ID order. Fixed by sorting the
target set by `state.value` before generating parametrize IDs (matching
the pattern `TransitionRegistry.all_transitions()` already used).
Re-confirmed clean afterward. Disclosed since it is the kind of
determinism defect this phase's own "Determinism" requirement exists to
catch.

---

## 12. Requirement Traceability

| IWC-001 v1.1 requirement range | Concern | Implemented in |
|---|---|---|
| IWC-REQ-040 (§4.4, ten states) | Reused unmodified from 143K | `models/session.py` |
| IWC-REQ-042 (§4.4, no unlisted transition / terminal finality) | Enforced at runtime by the Transition Engine (143K only enforced it structurally, at import-time table assertion) | `state_machine/validator.py`, `state_machine/engine.py` |
| IWC-REQ-045–046 (§4.7, expiry) | `Expired` reachable from every non-terminal state; enforced and applied through `TransitionEngine.apply`, not just present in the table | `state_machine/engine.py`, regression tests §11 |
| IWC-REQ-047 (§4.8, cancellation) | `Cancelled` reachable and applicable from every non-terminal state | `state_machine/engine.py`, regression tests §11 |
| IWC-REQ-160 (§12, universal cancel/expire/abandon availability) | Explicit universal-availability test over all five non-terminal states | `tests/test_iwc_143l_transition_engine.py::test_every_non_terminal_state_has_universal_cancel_expire_abandon_exit` |
| Phase 143J §5.4 (Transition Engine responsibility) | Sole ownership of legality determination, illegal-transition rejection, terminal enforcement, invariant enforcement, deterministic errors | `state_machine/engine.py`, `state_machine/validator.py` |
| Phase 143J §12 (error model) | Six new named errors + one fallback, all `TransitionError` subclasses | `errors.py` |
| Phase 143J §16 (dependency layering, acyclic graph) | Engine depends on Registry/Validator/Policy/Metadata/models only; Coordinator not modified to depend on Engine yet | `state_machine/engine.py`, §3 above |
| IWC-REQ-043–044 (§4.5, resumability) | Still not implemented — resumability *sequencing* (smart-resume, ownership re-check) is Session Coordinator/orchestration territory, out of this phase's scope | — (disclosed deferral, consistent with 143K) |

IWC-REQ-137–161 (Privacy, Security, Transport Independence) remain
cross-cutting per Phase 143J §18; this phase's contribution is limited to
the same "design only" posture 143K disclosed — no additional guarantee
is claimed.

---

## 13. Compatibility Verification

- **CHGR-001**: not modified; not imported; no `chgr-` identifier
  produced anywhere in this package; no write under
  `.pcae/governance-records/` (verified by a dedicated test).
- **IWC-001 v1.1**: not modified; `TRANSITION_TABLE` (143K/143I.1) is
  reused byte-for-byte, not copied or re-derived — the Registry wraps it
  rather than reimplementing it, eliminating any risk of a fresh
  table/prose divergence (the exact defect class B-1 was).
- **TAMC-001 / TAMPC-001**: not modified; not imported; no Typed
  Authority Model consumption anywhere in this package.
- **Runtime**: `pcae runtime inspect` unchanged — Observed / observe /
  unavailable before and after this phase.
- **143K Session model / persistence / serialization / validation /
  error hierarchy**: `Session`, `SessionRepository`,
  `serialization.schema`, and `validation.invariants` are all reused
  unmodified except for the disclosed circular-import fix (§9); a
  dedicated structural-compatibility test suite exercises all four
  together with the new Engine.

---

## 14. Security

Every check in the Transition Engine fails closed: an unknown state, a
duplicate/no-op target, a terminal-state exit attempt, an untabled
transition, a non-monotonic sequence number, an unrecognized schema
version, or a malformed session object all raise a specific, typed error
before any `Session` mutation is constructed — there is no code path that
silently accepts, coerces, or defaults any of these. `TransitionEngine`
exposes no `confirm`, `publish`, `orchestrate_evidence`,
`perform_confirmation`, `perform_publication`, or `create_chgr` method
(confirmed by a dedicated negative test) — there is nothing on this class
capable of creating authority, a governance decision, or a CHGR.

---

## 15. Exit Criteria (per governing prompt)

1. Transition Engine exists — ✅ (`state_machine/engine.py`)
2. Transition Registry is complete — ✅ (`state_machine/registry.py`, wraps the full, unmodified `TRANSITION_TABLE`)
3. Transition Validator exists — ✅ (`state_machine/validator.py`)
4. Terminal-state enforcement exists — ✅ (`TerminalStateViolationError`, tested from every terminal state against every target)
5. Transition metadata exists — ✅ (`state_machine/metadata.py`)
6. All legal transitions pass — ✅ (every table cell, §11)
7. All illegal transitions fail — ✅ (full 10×10 complement, §11)
8. B-1 regression suite passes — ✅ (§11, §12)
9. Runtime remains unchanged — ✅ (Observed / observe / unavailable)
10. No governance workflow capability exists — ✅ (§14; no confirm/publish/CHGR method, no persistence write, no evidence/clarification/preview code path)

---

## 16. Recommended Next Phase

**143M — Interactive Workflow Evidence Coordination, Clarification, and
Audit Infrastructure Implementation**, per the governing prompt's own
stated expectation and Phase 143J §17's decomposition. This
recommendation does not authorize 143M.

---

## 17. No-Go — Confirmed Not Done By This Phase

Not implemented, per the governing prompt's explicit exclusion list:
Evidence Coordinator, clarification workflow, Preview Builder, Preview
Digest, confirmation workflow, Session orchestration, persistence writes,
publication handoff, CHGR creation, runtime authority, transport
interfaces, CLI commands, Web/API, execution capability. IWC-001,
CHGR-001, TAMC-001, and TAMPC-001 were not modified. Runtime remains
Observed / observe / unavailable throughout. The Session Coordinator
(`session/coordinator.py`) was not modified and does not yet call the
Transition Engine — wiring that orchestration is explicitly out of this
phase's scope.
