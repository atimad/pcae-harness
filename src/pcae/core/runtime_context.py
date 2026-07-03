"""
Runtime Context Prototype — Phase 112C.

The first observation-only implementation of the Runtime Context
contracts frozen by 112B (`docs/PCAE_RUNTIME_CONTEXT_CONTRACT.md`),
built on the architecture 112A designed
(`docs/PCAE_RUNTIME_CONTEXT_ARCHITECTURE.md`). This module implements
all twelve Runtime Context objects as inert, immutable data records —
it **describes the Runtime's dynamic operational state; it never
executes**, exactly as 112A §1 defines Context and exactly as
`runtime_introspection.py` (111B) and `runtime_registry.py` (110E)
already established the same "surfaces facts, never decides/executes"
discipline for their own layers.

Isolation (by design, verified by tests reading this module's own
source, mirroring 108A/110E/111B's isolation guarantees): this module
imports only the standard library (`dataclasses`, `typing`). It does
not import `permission_broker_foundation`, `runtime_registry`,
`command_path_observation`, or any execution-adjacent module — a
`BrokerDecisionContext` *wraps* the shape of a decision the Broker
would produce elsewhere; it never calls `PermissionBroker.evaluate()`
itself. It uses no `subprocess`, no shell, no network, no file
mutation, no `importlib`, and no `eval`/`exec`.

Implements all twelve objects 112A §3 froze and 112B §1-§7 gave
contracts for: `RuntimeContext`, `RuntimeSession`, `TaskContext`,
`PhaseContext`, `IntentContext`, `BrokerDecisionContext`,
`ApprovalContext`, `EvidenceContext`, `ObservationContext`, and three
explicitly future/stub objects — `ExecutionContext`, `AuditContext`,
`RollbackContext`.

**Relationship chain ordering.** This module implements the chain in
112B's own *resolved* order — `Intent -> Broker Decision -> Approval ->
Evidence` — not 112A's original presentation order (`Intent -> Approval
-> Broker Decision`), because 112B §8.2 explicitly resolved that
ordering tension in favor of Broker Decision preceding Approval, citing
110A §5's frozen "Decision Pipeline -> Approval" interface and 110A
§8's frozen state sequence. Objective 1 of this phase's own brief asks
for an implementation "exactly matching the contracts frozen in 112B"
— this module honors that resolved contract, not the pre-resolution
diagram, and documents the difference explicitly
(`docs/PHASE_112_RUNTIME_CONTEXT_PROTOTYPE.md`) rather than silently
reverting a phase that already did the work of resolving it.

**Identity precedes state** (112B's own principle addition, §2 of the
contract): every object below requires a non-empty identity string at
construction -- there is no default, auto-generated, or optional
identity for any of the eight objects with a real identity concept
(`session_id` through `observation_id`) or the three future stubs
(`execution_id`/`audit_id`/`rollback_id`). Construction with an empty
identity raises `ValueError` immediately (fail-closed), exactly as
112B §7's "Identity is immutable and precedes state" invariant
requires: `Created` *is* the act of identity assignment, not a step
that may be deferred past it. `RuntimeContext` itself has no
independent identity (112B §2), matching its role as the root
aggregate scoped to whichever `RuntimeSession` it currently
references.

**Lifecycle representation, not lifecycle execution.** Every object
carries a `lifecycle_stage` field drawn from `CONTEXT_LIFECYCLE_STAGES`
(112A §4's six-stage vocabulary, restated verbatim, not reinvented).
The only transition this module implements is `observe()`, moving an
object from `Created`/`Initialized` to `Observed` -- returning a *new*
frozen instance (`dataclasses.replace`), never mutating the original,
since these objects are immutable. No `Updated`, `Completed`, or
`Archived` transition is implemented; no `Executing`/`Executed`/
`RolledBack` state exists anywhere in this module, consistent with
112B §3's frozen invalid-transition rule.

**Ownership and persistence are represented, never enforced.** Every
class below carries a class-level `OWNERSHIP` (who creates/owns/
updates/archives/observes, 112B §4) and `PERSISTENCE_BUCKET` (which of
112B §5's four buckets -- Persistent/Session-only/Future persistence/
Never persist -- this object belongs to) constant. Nothing in this
module reads, checks, or acts on either value; they are metadata for a
human or a future Introspection layer to read, exactly as 112A §5
already established for the architecture and 112B §4/§5 froze per
object.

Current implementation status: **execution unavailable**. No CLI
command, persistence mechanism, or serialization format exists for any
object in this module -- that remains out of scope for a future phase
(112D, verification & compatibility, is the recommended next phase).
Current maximum runtime state remains `Observed` (110A §8); current
maximum plugin capability remains `observe` (110B §3) -- this module
restates both as static facts; it does not compute, influence, or
change either.

See `docs/PHASE_112_RUNTIME_CONTEXT_PROTOTYPE.md`,
`docs/PCAE_RUNTIME_CONTEXT_CONTRACT.md` (112B), and
`docs/PCAE_RUNTIME_CONTEXT_ARCHITECTURE.md` (112A).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import ClassVar

# ═══════════════════════════════════════════════════════════════════════
# Frozen architecture-level facts (restated -- not redefined)
# ═══════════════════════════════════════════════════════════════════════

#: The six-stage Context Lifecycle frozen by 112A §4, restated verbatim
#: -- a distinct vocabulary from 110A §8's Runtime State Model and 110B
#: §4's Plugin Lifecycle, not a competitor to either.
CONTEXT_LIFECYCLE_STAGES: tuple[str, ...] = (
    "Created",
    "Initialized",
    "Observed",
    "Updated",
    "Completed",
    "Archived",
)

#: The four persistence buckets frozen by 112B §5, restated verbatim.
CONTEXT_PERSISTENCE_BUCKETS: tuple[str, ...] = (
    "Persistent",
    "Session-only",
    "Future persistence",
    "Never persist",
)

#: The resolved Context relationship chain (112B §6 / §8.2) -- Broker
#: Decision precedes Approval, per 112B's explicit resolution, not
#: 112A's original presentation order. Execution, Audit, and Rollback
#: remain conceptual only (no field beyond a not-implemented marker,
#: 112A §3), named here as the eventual next links in the chain.
CONTEXT_RELATIONSHIP_CHAIN: tuple[str, ...] = (
    "RuntimeSession",
    "TaskContext",
    "PhaseContext",
    "IntentContext",
    "BrokerDecisionContext",
    "ApprovalContext",
    "EvidenceContext",
    "ExecutionContext (future)",
    "AuditContext (future)",
    "RollbackContext (future)",
)

#: Current maximum state reachable by any real PCAE command path today
#: (110A §8, unchanged). This module reports this as a static fact; it
#: does not compute or influence it.
CURRENT_RUNTIME_STATE: str = "Observed"

#: Current maximum plugin capability actually exercised by any real
#: PCAE code path today (110B §3, unchanged).
CURRENT_MAXIMUM_PLUGIN_CAPABILITY: str = "observe"

#: Execution capability availability (108A/107B/107C, unchanged).
EXECUTION_AVAILABILITY: str = "unavailable"


def _require_identity(value: str, field_name: str) -> None:
    """Fail-closed identity validation (112B §7, invariant 9: 'Identity
    is immutable and precedes state'). Raising here, at construction,
    is the enforcement point for that invariant -- there is no path to
    a Context object existing without one."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required and must be a non-empty string")


def _require_valid_stage(stage: str) -> None:
    if stage not in CONTEXT_LIFECYCLE_STAGES:
        raise ValueError(
            f"lifecycle_stage {stage!r} is not one of the frozen 112A stages: "
            f"{CONTEXT_LIFECYCLE_STAGES}"
        )


# ═══════════════════════════════════════════════════════════════════════
# Ownership metadata (112B §4) -- represented, never enforced
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class OwnershipMetadata:
    """Who creates/owns/updates/archives/observes one Context object
    (112B §4). A plain data record -- reading it never changes what
    anything is permitted to do; it exists so a human or a future
    Introspection layer can answer "who is responsible for this
    object" without inferring it from convention."""

    creates: str
    owns: str
    updates: str
    archives: str
    observes: str


# ═══════════════════════════════════════════════════════════════════════
# Context objects (112A §3 / 112B §1-§7)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ObservationContext:
    """Aggregate observation-integration state for one session (112A
    §3, object 9). `session_id` is the owning `RuntimeSession`'s
    identity, not an independent foreign key concept -- this object is
    one per session, per 112B §2."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime (first INT-NNN consultation of the session)",
        owns="Runtime",
        updates="Runtime (each subsequent INT-NNN consultation)",
        archives="N/A -- never persisted, discarded at session end",
        observes="Introspection (future)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Session-only"

    observation_id: str
    session_id: str
    consulted_integrations: tuple[str, ...] = ()
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_identity(self.observation_id, "observation_id")
        _require_identity(self.session_id, "session_id")
        _require_valid_stage(self.lifecycle_stage)


@dataclass(frozen=True)
class EvidenceContext:
    """One evidence record (112A §3, object 8) -- not implemented
    anywhere today, since `COMP-007` (Audit Boundary) does not exist.
    `approval_id` is the owning `ApprovalContext`'s identity, per 112B
    §6's resolved chain (Approval -> Evidence)."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime -- wrapping COMP-007's eventual output",
        owns="Runtime",
        updates="N/A -- append-only once created",
        archives="Runtime",
        observes="Introspection (future)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Future persistence"

    evidence_id: str
    approval_id: str
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_identity(self.evidence_id, "evidence_id")
        _require_identity(self.approval_id, "approval_id")
        _require_valid_stage(self.lifecycle_stage)


@dataclass(frozen=True)
class ApprovalContext:
    """One intent's human-approval status (112A §3, object 6) -- not
    implemented anywhere, since `COMP-003` (Human Approval Gate) does
    not exist. `status` is a conceptual placeholder only -- this object
    records that an approval outcome exists once one does; it is never
    itself the mechanism that decides one (112A §5)."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime -- wrapping COMP-003's eventual outcome; never self-created",
        owns="Runtime",
        updates="Runtime, recording an outcome COMP-003 would produce -- never itself",
        archives="Runtime",
        observes="Introspection (future)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Future persistence"

    approval_id: str
    decision_id: str
    status: str = "not_implemented"
    evidence: tuple[EvidenceContext, ...] = ()
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_identity(self.approval_id, "approval_id")
        _require_identity(self.decision_id, "decision_id")
        _require_valid_stage(self.lifecycle_stage)


@dataclass(frozen=True)
class BrokerDecisionContext:
    """One Permission Broker decision, contextualized (112A §3, object
    7). This class *wraps the shape* a `PermissionBrokerDecision`
    (108A) would take -- it never imports `permission_broker_foundation`
    and never calls `PermissionBroker.evaluate()`. Per 112B §6/§8.2,
    this object precedes `ApprovalContext` in the resolved chain."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime -- wrapping a decision the Broker (COMP-001) already produced",
        owns="Runtime",
        updates="N/A -- immutable once wrapped",
        archives="N/A -- never persisted, discarded at end of consultation",
        observes="Introspection (future, for the single consultation's duration only)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Never persist"

    decision_id: str
    intent_id: str
    approval: ApprovalContext | None = None
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_identity(self.decision_id, "decision_id")
        _require_identity(self.intent_id, "intent_id")
        _require_valid_stage(self.lifecycle_stage)


@dataclass(frozen=True)
class IntentContext:
    """One proposed action (112A §3, object 5; 110A §8's `Intent` state,
    given a concrete shape). `phase_id` is the owning `PhaseContext`'s
    identity -- each Intent belongs to exactly one Phase (112B §7,
    invariant 4)."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime (on receiving a well-formed intent, 110A §5)",
        owns="Runtime",
        updates="Runtime (as the intent moves through the pipeline)",
        archives="Runtime",
        observes="Introspection (future)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Session-only"

    intent_id: str
    phase_id: str
    description: str = ""
    source: str = ""
    broker_decision: BrokerDecisionContext | None = None
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_identity(self.intent_id, "intent_id")
        _require_identity(self.phase_id, "phase_id")
        _require_valid_stage(self.lifecycle_stage)


@dataclass(frozen=True)
class PhaseContext:
    """One governed phase (112A §3, object 4). Composed of one-or-more
    `IntentContext` objects (112B §6). `intents` is a tuple, never a
    list, so this object's own immutability cannot be defeated by
    mutating a mutable field in place -- the same hardening lesson
    110F's verification pass caught for `PluginDescriptor` (110E)."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime",
        owns="Runtime",
        updates="Runtime",
        archives="Runtime (pcae phase complete)",
        observes="Introspection (future PhaseInfo)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Persistent"

    phase_id: str
    title: str = ""
    intents: tuple[IntentContext, ...] = ()
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_identity(self.phase_id, "phase_id")
        _require_valid_stage(self.lifecycle_stage)


@dataclass(frozen=True)
class TaskContext:
    """One active or historical task (112A §3, object 3). `session_id`
    is the owning `RuntimeSession`'s identity; `phase_id` is an
    optional reference to the phase this task's work belongs to --
    a reference, not a nested copy, since Task:Phase cardinality is
    many-to-one over a phase's lifetime (112B §6/§8.1): many tasks may
    reference the same phase without duplicating it."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime (pcae task new)",
        owns="Runtime",
        updates="Runtime (pcae task update/pause/resume)",
        archives="Runtime (pcae task complete/finish)",
        observes="Introspection (future TaskInfo)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Persistent"

    task_id: str
    session_id: str
    phase_id: str | None = None
    title: str = ""
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_identity(self.task_id, "task_id")
        _require_identity(self.session_id, "session_id")
        _require_valid_stage(self.lifecycle_stage)


@dataclass(frozen=True)
class RuntimeSession:
    """One working session (112A §3, object 2). Composed of zero-or-
    more `TaskContext` objects and, at most, one `ObservationContext`
    (one per session, 112B §2). At most one Task is *active* at any
    given moment (112B §6, unchanged from 112A) -- this prototype
    represents the collection; it does not enforce that invariant,
    since doing so would require live runtime state this phase does
    not introduce."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime (pcae session bootstrap)",
        owns="Runtime",
        updates="Runtime",
        archives="Runtime (session end)",
        observes="Introspection (future SessionInfo)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Persistent"

    session_id: str
    tasks: tuple[TaskContext, ...] = ()
    observation: ObservationContext | None = None
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_identity(self.session_id, "session_id")
        _require_valid_stage(self.lifecycle_stage)


@dataclass(frozen=True)
class ExecutionContext:
    """What would eventually model `Executed` (110A §8) -- today,
    frozen with exactly one meaningful field: `status =
    "execution_unavailable"` (112A §3, object 10). Naming this object
    now gives a future phase a vocabulary to design against; it grants
    no execution capability whatsoever."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime (stub only, today)",
        owns="Runtime",
        updates="N/A today -- frozen at execution_unavailable",
        archives="N/A",
        observes="Introspection (future)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Never persist"

    execution_id: str
    status: str = "execution_unavailable"
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_identity(self.execution_id, "execution_id")
        _require_valid_stage(self.lifecycle_stage)


@dataclass(frozen=True)
class AuditContext:
    """What would eventually model `Audited` (110A §8) -- today, frozen
    as a stub with no field beyond a not-implemented marker (112A §3,
    object 11)."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime (stub only, today)",
        owns="Runtime",
        updates="N/A today",
        archives="N/A",
        observes="Introspection (future)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Future persistence"

    audit_id: str
    status: str = "not_implemented"
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_identity(self.audit_id, "audit_id")
        _require_valid_stage(self.lifecycle_stage)


@dataclass(frozen=True)
class RollbackContext:
    """What would eventually model `Rollback Ready` (110A §8) -- today,
    frozen as a stub with no field beyond a not-implemented marker
    (112A §3, object 12)."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime (stub only, today)",
        owns="Runtime",
        updates="N/A today",
        archives="N/A",
        observes="Introspection (future)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Future persistence"

    rollback_id: str
    status: str = "not_implemented"
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_identity(self.rollback_id, "rollback_id")
        _require_valid_stage(self.lifecycle_stage)


@dataclass(frozen=True)
class RuntimeContext:
    """The top-level aggregate a Runtime instance would hold (112A §3,
    object 1). No independent identity (112B §2) -- scoped entirely to
    whichever `RuntimeSession` it currently references. Composition
    over a single mutable structure: this object *contains* a
    `RuntimeSession` (which itself contains `TaskContext`/
    `ObservationContext`, which contain further objects down the
    resolved chain, `CONTEXT_RELATIONSHIP_CHAIN`) rather than flattening
    every field from every object into one giant record."""

    OWNERSHIP: ClassVar[OwnershipMetadata] = OwnershipMetadata(
        creates="Runtime (at Runtime startup)",
        owns="Runtime",
        updates="Runtime",
        archives="N/A -- lives with the process, never independently archived",
        observes="Introspection (future)",
    )
    PERSISTENCE_BUCKET: ClassVar[str] = "Session-only"

    session: RuntimeSession | None = None
    lifecycle_stage: str = "Created"

    def __post_init__(self) -> None:
        _require_valid_stage(self.lifecycle_stage)


# ═══════════════════════════════════════════════════════════════════════
# The one implemented lifecycle transition -- observation (112A §4)
# ═══════════════════════════════════════════════════════════════════════


def observe_context(context_object):
    """Return a *new* copy of `context_object` with `lifecycle_stage`
    advanced to `"Observed"` -- the only transition this module
    implements (112C objective 4: "No transitions beyond observation").
    Never mutates the original (all Context objects are frozen).
    Raises `ValueError` (fail-closed) if the object is not currently in
    `Created` or `Initialized` -- exactly 112B §3's frozen valid-
    transition table: `Observed` -> `Observed` is not a listed
    transition, and no object may skip backward to be re-observed from
    `Updated`/`Completed`/`Archived`."""
    stage = getattr(context_object, "lifecycle_stage", None)
    if stage not in ("Created", "Initialized"):
        raise ValueError(
            f"Cannot observe from lifecycle stage {stage!r}; only 'Created' or "
            "'Initialized' may transition to 'Observed' (112B §3)."
        )
    return replace(context_object, lifecycle_stage="Observed")
