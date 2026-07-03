# Phase 112C — Runtime Context Prototype (Observation-Only)

## Purpose

Implement the first observation-only Runtime Context prototype using
the contracts frozen in 112A and 112B, introducing the first live
Runtime Context object model while preserving every non-executing
guarantee established through 112B.1. Runtime Context represents the
Runtime's current operational state; it does not execute anything.

## Scope

- `src/pcae/core/runtime_context.py` — the implementation: twelve
  frozen dataclasses (all objects 112A §3 named, all contracts 112B
  §2–§7 froze), a six-stage lifecycle vocabulary restated verbatim, a
  resolved relationship-chain constant, ownership/persistence metadata
  per class, fail-closed identity validation, and one implemented
  lifecycle transition (`observe_context()`).
- `docs/PHASE_112_RUNTIME_CONTEXT_PROTOTYPE.md` — this document.
- `tests/test_runtime_context.py` — 105 new tests covering existence,
  identity, composition, lifecycle, ownership, persistence,
  relationships, and module isolation.
- Three stale forward-looking guard tests, in
  `tests/test_runtime_context_architecture.py`,
  `tests/test_runtime_context_contract.py`, and
  `tests/test_runtime_architecture_review.py`, updated to stop
  forbidding the exact module this phase was always going to create
  (see §6).

## 1. Runtime Context Implementation Summary

All twelve objects 112A §3 froze are implemented as inert,
observation-only data records: `RuntimeContext`, `RuntimeSession`,
`TaskContext`, `PhaseContext`, `IntentContext`, `BrokerDecisionContext`,
`ApprovalContext`, `EvidenceContext`, `ObservationContext`, and three
explicitly future/stub objects — `ExecutionContext`, `AuditContext`,
`RollbackContext`. Every class is a frozen `dataclasses.dataclass`
(immutable — the same discipline `runtime_registry.py`, 110E, and
`runtime_introspection.py`, 111B, already established for their own
layers). The module imports only the standard library
(`dataclasses`, `typing`) — no `permission_broker_foundation`, no
`runtime_registry`, no `command_path_observation`, no shell, no
subprocess, no network. `BrokerDecisionContext` *wraps the shape* of a
Broker decision; it never calls `PermissionBroker.evaluate()`.

**Deliberate deviation from this phase's own brief, documented
honestly.** The brief's objective 7 diagram lists the chain as
`Session → Task → Phase → Intent → Approval → Broker Decision →
Evidence` — 112A's original, pre-resolution presentation order. 112B
§8.2 explicitly resolved the Approval/Broker-Decision ordering tension
in favor of **Broker Decision preceding Approval**, citing 110A §5's
frozen "Decision Pipeline → Approval" interface and 110A §8's frozen
state sequence (`Observed` precedes `Approved`). Since this phase's own
objective 1 asks for an implementation "exactly matching the contracts
frozen in 112B," this module implements the **112B-resolved order**,
not the brief's diagram — reverting to the pre-resolution ordering
would silently discard 112B's own resolution work. This is named here
explicitly, the same discipline 111R/112A/112B already established for
naming a tension rather than picking a side silently — except here the
tension was already resolved, and the discipline is refusing to
un-resolve it by accident.

## 2. Object Model Summary

Twelve classes, one module. No per-object file — `runtime_context.py`
combines all twelve, since 112B's own contract froze the *shape* each
object should have without mandating one file per object (mirroring
110C→110E's single-file `runtime_registry.py` and 111A→111B's single-
file `runtime_introspection.py`, not a new convention). Each class
docstring cites the specific 112A/112B section it implements.

## 3. Immutable Identity Summary

Every object with a real identity concept (`session_id` through
`observation_id`) and every future stub (`execution_id`/`audit_id`/
`rollback_id`) requires a non-empty identity string at construction —
enforced in `__post_init__`, raising `ValueError` immediately
(fail-closed) for an empty or missing identity. There is no default,
no auto-generation: 112B §7's "Identity is immutable and precedes
state" invariant is enforced at the one point it can be — construction
itself, since `Created` *is* the act of identity assignment.
`RuntimeContext` has no independent identity field at all (112B §2) —
it is scoped entirely to whichever `RuntimeSession` it references.
Identity fields cannot be reassigned after construction
(`dataclasses.FrozenInstanceError` on attempted mutation).

## 4. Composition Summary

`RuntimeContext` contains a `RuntimeSession`, which contains
`TaskContext` and `ObservationContext` objects; `PhaseContext` contains
`IntentContext` objects; `IntentContext` contains a
`BrokerDecisionContext`; `BrokerDecisionContext` contains an
`ApprovalContext`; `ApprovalContext` contains `EvidenceContext` objects
— composition all the way down, never one flattened mutable structure.
The one deliberate exception is `TaskContext ↔ PhaseContext`: since
Task:Phase cardinality is many-to-one over a phase's lifetime (112B
§6/§8.1), `TaskContext` carries a `phase_id: str | None` *reference*,
not a nested `PhaseContext` copy — multiple tasks can reference the
same phase without duplicating it. All collection fields are tuples,
never lists, guarding against the exact mutable-default hardening gap
110F's verification pass caught in `PluginDescriptor` (110E).

## 5. Relationship Summary

`CONTEXT_RELATIONSHIP_CHAIN` names the resolved chain declaratively:
`RuntimeSession → TaskContext → PhaseContext → IntentContext →
BrokerDecisionContext → ApprovalContext → EvidenceContext →
ExecutionContext (future) → AuditContext (future) → RollbackContext
(future)`. The first seven links are live object composition (§4); the
three future links remain conceptual-only, named in the chain constant
but never wired into any real object's field, since none has real data
to carry yet.

## 6. Ownership Summary

Every class carries a class-level `OWNERSHIP: ClassVar[OwnershipMetadata]`
constant (creates/owns/updates/archives/observes), directly transcribing
112B §4's per-object table — never an instance field, since ownership is
fixed per type, not per object. Every class's `creates`/`owns` names
`"Runtime"` — no Plugin, Broker, or Registry ever creates or owns a
Context object, matching 112B §4's stated invariant. Nothing in this
module reads or acts on `OWNERSHIP`; it exists to be read, not enforced.

## 7. Persistence Metadata Summary

Every class carries a class-level `PERSISTENCE_BUCKET: ClassVar[str]`,
one of 112B §5's four buckets (`"Persistent"`, `"Session-only"`,
`"Future persistence"`, `"Never persist"`), transcribed exactly —
`RuntimeSession`/`TaskContext`/`PhaseContext` → `Persistent`;
`IntentContext`/`ObservationContext` → `Session-only`;
`ApprovalContext`/`EvidenceContext`/`AuditContext`/`RollbackContext` →
`Future persistence`; `BrokerDecisionContext`/`ExecutionContext` (today)
→ `Never persist`; `RuntimeContext` (the root aggregate) →
`Session-only`. No storage mechanism, no serialization, no database —
constructing every one of the twelve objects touches no filesystem path
(verified directly, `tests/test_runtime_context.py`).

## 8. Guard-Test Repair (Stale Forward-Looking Assertions)

Three pre-existing tests, written in 110-111-series phases before
`runtime_context.py` existed, asserted it must *not* exist — a
forward-looking guard against premature implementation, exactly as
each phase's own convention intended, and exactly as my own working
notes flagged as worth re-checking once 112B/112C landed:

- `tests/test_runtime_context_architecture.py::test_no_context_module_added_to_core`
  (112A)
- `tests/test_runtime_context_contract.py::test_no_context_module_added_to_core`
  (112B)
- `tests/test_runtime_architecture_review.py::test_no_runtime_context_module_added_to_core`
  (111R)

All three removed `runtime_context.py` from their forbidden-module set
with an explanatory docstring addition, while keeping every other
still-nonexistent per-object filename (`task_context.py`,
`session_info.py`, etc.) forbidden — this phase created one combined
module, not twelve separate files, so those guards remain accurate.
This is the intended outcome those guards were written to eventually
allow, not a regression being silently worked around.

A fourth, unrelated latent bug was found and fixed in the same pass:
`tests/test_runtime_context_contract.py::test_task_contract_excludes_src_pcae`
used the glob `*phase-112b*`, which also matched 112B.1's task contract
(`*phase-112b-1-planning*` contains `"112b"` as a substring) — the same
class of over-broad-substring-match bug already fixed once in this
file (112B.1 itself), here surfacing in the glob instead of a text
check. Narrowed to `*phase-112b-runtime*`.

## 9. Current Limitations

- No persistence, serialization, or storage mechanism exists for any
  object — deliberately, per this phase's hard boundary.
- No CLI command, REST endpoint, or web UI exposes any object in this
  module. `pcae runtime inspect` (111C) does not read this module.
  Wiring Runtime Context into Introspection remains a materially
  different, future phase's scope (112A §1 already named this as the
  eventual direction, not this phase's job).
- The "exactly one active Runtime Context" and "at most one active Task
  per Phase" invariants (112B §7) are represented structurally
  (composition permits multiple `TaskContext`s per session) but not
  enforced — enforcing either would require live runtime state this
  observation-only prototype does not introduce.
- `ApprovalContext.status` and the future stubs' `status` fields are
  conceptual placeholders only — `COMP-003` (Human Approval Gate) and
  `COMP-007` (Audit Boundary) remain unimplemented; nothing in this
  module decides an approval outcome or produces real evidence.

## 10. Recommendation for Verification

**112D — Runtime Context Verification & Compatibility** is recommended
next, mirroring the 110E→110F and 111B→111C/111D "prototype then
verification" pattern this arc has already followed twice: verify this
prototype's shape against 112B's contract field-by-field, confirm
compatibility with 111A/111B's Introspection layer as a future read
path, and re-confirm every non-executing guarantee under `-n auto`.

## Execution Integration Status

Unchanged — this phase introduces no new command-path integration and
no execution capability:

| Field | Value |
|---|---|
| Observed command paths | **4** (unchanged) |
| Behavior-changing paths | **0** |
| Authorized paths | **0** |
| Execution-capable paths | **0** |
| Current execution capability | **Execution unavailable** |
| Current maximum runtime state | **Observed** (unchanged) |
| Current maximum plugin capability | **`observe`** (unchanged) |

## Safety Case

- **Why this phase cannot introduce execution capability:** the new
  module imports nothing beyond `dataclasses`/`typing`; it cannot call
  a shell, a broker, a plugin, or a backend because it has no reference
  to any of them.
- **Why "observation-only" survives real object construction:**
  constructing all twelve objects, fully composed end-to-end, touches
  no filesystem path (`tests/test_runtime_context.py`'s
  `test_no_file_written_by_constructing_any_context_object`) and
  triggers no broker evaluation, plugin load, or subprocess call
  (module-import allowlist test).
- **Why the one implemented transition (`observe_context()`) cannot
  become a lifecycle-execution mechanism:** it only ever moves an
  object from `Created`/`Initialized` to `Observed`, returns a *new*
  instance (never mutates), and raises for every other requested
  transition — there is no `complete()`, `archive()`, or `update()`
  method on any class.

## No-Go Confirmations

No persistence. No serialization. No database. No runtime execution.
No plugin loading. No plugin instantiation. No plugin invocation. No
dependency injection. No shell mediation. No backend invocation. No
adapter invocation. No execution enablement. No execution capability.
No Permission Broker enforcement. No audit persistence. No rollback
execution. No emergency stop. No Telegram inbound. No REST endpoint.
No web UI. No daemon. No background worker. No automatic apply.
`implementation_status` remains unconditionally
`"execution_unavailable"` on every Permission Broker decision. Current
maximum runtime state remains `Observed`. Current maximum plugin
capability remains `observe`. `v0.1.0-rc1` remains non-executing by
design. v0.2 remains the autonomy target (Level 3, not Level 4/5).
GitHub Release for `v0.1.0-rc1` and branch protection on `main` are
unchanged. No new tag. No new GitHub Release. No PyPI/GitHub Packages
publication.

## Recommended Next Phase

**112D — Runtime Context Verification & Compatibility.**
