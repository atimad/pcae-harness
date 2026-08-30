"""
Runtime Introspection Prototype — Phase 111B.

The first observation-only implementation of the Runtime Introspection
architecture frozen by 111A (`docs/PCAE_RUNTIME_INTROSPECTION.md`).
This module exposes Runtime, Registry, Plugin, Capability, Health,
Version, Governance, and RuntimeState metadata — in-process only, no
CLI, no REST endpoint, no web UI. It **exposes information; it never
changes behavior**, exactly as 111A §1 defines introspection.

Isolation (by design, verified by tests reading this module's own
source, mirroring 108A's isolation guarantee for
`permission_broker_foundation.py` and 110E/110F's for
`runtime_registry.py`): this module imports only the standard library
plus three already-frozen, already-non-executing internal modules —
`pcae.core.runtime_registry` (110E/110F, the metadata store this module
reads), `pcae.core.permission_broker_foundation` (108A, read only for
its `IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE` constant — no
`PermissionBroker` instance is ever constructed or evaluated here), and
`pcae.core.command_path_observation` (109C, read only for
`INTEGRATION_REGISTRY`'s length — no `observe()` call is ever made
here). It uses no `subprocess`, no shell, no network, no file mutation,
no `importlib`, no `eval`/`exec`, and no dependency on `shell_gate`,
`backend_invocations`, `notifications`, or any other execution-adjacent
module.

Implements, observation-only, eight of the eleven introspection objects
111A froze (`docs/PCAE_RUNTIME_INTROSPECTION.md` §4): `RuntimeInfo`,
`RegistryInfo`, `PluginInfo`, `CapabilityInfo`, `HealthInfo`,
`VersionInfo`, `GovernanceInfo`, `RuntimeStateInfo`. Two of the eight —
`RegistryInfo` and `PluginInfo` — are implemented as direct type
aliases of 110E/110F's own `RegistrySnapshot`/`PluginDescriptor`, not
as new duplicate dataclasses, since 111A §4 already named those exact
existing shapes as what those two objects map onto.

**Deliberately deferred, not implemented this phase:** `SessionInfo`,
`TaskInfo`, `PhaseInfo`. This phase's own goal statement scopes
introspection to "runtime, registry, plugin, capability, health, state,
and governance metadata" — Session/Task/Phase are not named. Each of
those three domains already has a full, working, filesystem-backed
precedent (`pcae session bootstrap --json`, `pcae task show --json`,
`pcae phase report --json`) that reads live `.pcae/` state — wrapping
those is a materially different scope (filesystem I/O, live session/
lock state) from this phase's in-process, `RuntimeRegistry`-backed
model, and is left to a future phase.

Eight functions mirror 111A §7's eight canonical API operation names
(`GetRuntime()` -> `get_runtime()`, `GetRegistry()` -> `get_registry()`,
`GetPlugins()` -> `get_plugins()`, `GetCapabilities()` ->
`get_capabilities()`, `GetHealth()` -> `get_health()`, `GetGovernance()`
-> `get_governance()`, `GetState()` -> `get_state()`, `GetVersion()` ->
`get_version()`) 1:1, in idiomatic Python snake_case rather than the
architecture document's illustrative PascalCase.

Current implementation status: **execution unavailable**. No CLI
command, REST endpoint, or web UI exposes any of this module's
functions — that is explicitly planned for 111C (the `pcae runtime
inspect` command), not implemented here. Current maximum runtime state
remains
`Observed` (110A §8); current maximum plugin capability remains
`observe` (110B §3) — this module reports both as static, frozen facts;
it does not compute, influence, or change either.

See `docs/PHASE_111_RUNTIME_INTROSPECTION_PROTOTYPE.md`,
`docs/PCAE_RUNTIME_INTROSPECTION.md` (111A), and
`docs/PCAE_RUNTIME_ARCHITECTURE.md` (110A).
"""

from __future__ import annotations

from dataclasses import dataclass

from pcae import __version__ as _RELEASE_VERSION
from pcae.core.command_path_observation import INTEGRATION_REGISTRY
from pcae.core.permission_broker_foundation import (
    IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE,
)
from pcae.core.runtime_registry import (
    CAPABILITY_CLASSES,
    UNDECLARABLE_CAPABILITIES,
    PluginDescriptor,
    RegistrySnapshot,
    RuntimeRegistry,
)

# ═══════════════════════════════════════════════════════════════════════
# Frozen architecture-level facts (restated from 110A — not redefined)
# ═══════════════════════════════════════════════════════════════════════

#: The seven-stage Runtime Pipeline frozen by 110A §2.
PIPELINE_STAGES: tuple[str, ...] = (
    "Intent Source",
    "Runtime",
    "Intent Pipeline",
    "Decision Pipeline",
    "Execution Adapter",
    "Evidence Pipeline",
    "Notification Pipeline",
)

#: The eleven Runtime Principles frozen by 110A §6.
RUNTIME_PRINCIPLES: tuple[str, ...] = (
    "Modular",
    "Pluggable",
    "Connected",
    "Observable",
    "Automatable",
    "Governed",
    "Fail-closed",
    "Least privilege",
    "Human-controlled",
    "Deterministic",
    "Testable",
)

#: The nine Runtime Services frozen by 110A §4.
RUNTIME_SERVICES: tuple[str, ...] = (
    "Session",
    "Task",
    "Phase",
    "Identity",
    "Configuration",
    "Plugin Registry",
    "Policy Registry",
    "Integration Registry",
    "Audit Registry",
)

#: The eight-state Runtime State Model frozen by 110A §8, restated
#: verbatim by 111A §6 (not a new vocabulary).
RUNTIME_STATE_MODEL: tuple[str, ...] = (
    "Intent",
    "Observed",
    "Advisory",
    "Approved",
    "Executable",
    "Executed",
    "Audited",
    "Rollback Ready",
)

#: Current maximum state reachable by any real PCAE command path today
#: (110A §8, unchanged). This module reports this as a static fact; it
#: does not compute or influence it.
CURRENT_RUNTIME_STATE: str = "Observed"

#: Current maximum plugin capability actually exercised by any real
#: PCAE code path today (110B §3, unchanged).
CURRENT_MAXIMUM_PLUGIN_CAPABILITY: str = "observe"

#: Execution capability availability (108A/107B/107C, unchanged).
#: `implementation_status` is unconditionally `"execution_unavailable"`
#: on every Permission Broker decision; this module restates that fact
#: for the introspection domain rather than re-deriving it.
EXECUTION_AVAILABILITY: str = "unavailable"


# ═══════════════════════════════════════════════════════════════════════
# Runtime-adapter surface discoverability (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19,
# Slice B — 3S.2.1 item-9 runtime-inspect repair)
# ═══════════════════════════════════════════════════════════════════════
#
# 3S.2.1 §44/§61 recorded a TRUTHFUL_WITH_LIMITATION discoverability gap:
# the RegistryInfo `pcae runtime inspect` reports is the long-lived
# `RuntimeRegistry` (empty), but a *separate*, transient, per-call RPAC-001
# mock/dry runtime-adapter surface exists in production (reachable via
# `pcae session bootstrap --dry-runtime`) and a plain "Plugin count: 0 /
# Capability count: 0 / Registry status: empty" is easy for an operator to
# over-read as "nothing runtime-adapter-shaped exists in this repo".
#
# This repair adds an OBSERVATIONAL, NON-MUTATING surface list: static,
# frozen facts, no registry read, no adapter instantiation, no `simulate_*`
# call, no capability enablement. Every entry is truthful about being
# simulation-only / non-authoritative and about execution remaining
# `unavailable`. It implies NO adapter readiness and NO execution
# enablement (phase prompt §35 / §37).


@dataclass(frozen=True)
class RuntimeAdapterSurfaceInfo:
    """One coexisting runtime-adapter-shaped surface in this repository,
    described by static frozen facts. `effecting` is `False` for every
    surface today; `execution_availability` restates the global
    `unavailable` posture so no entry can be over-read as a readiness
    claim."""

    surface_id: str
    kind: str
    description: str
    reachable_via: str
    effecting: bool
    authoritative: bool
    execution_availability: str


#: The frozen, non-executing runtime-adapter surface inventory. Static
#: data — this tuple is the whole implementation; nothing is computed,
#: instantiated, or invoked to produce it.
RUNTIME_ADAPTER_SURFACES: tuple[RuntimeAdapterSurfaceInfo, ...] = (
    RuntimeAdapterSurfaceInfo(
        surface_id="rpac-mock-v1-dry-consumption",
        kind="simulation",
        description=(
            "RPAC-001 v1.0 mock/dry runtime-adapter simulation coordinator "
            "(runtime_adapter.simulate_invocation) — fixed local fixtures, "
            "no process spawn, no network, execution_effect=none. Not "
            "wired to the RDGO Gate 5-11 chain."
        ),
        reachable_via="pcae session bootstrap --dry-runtime --runtime-target <fixture-id>",
        effecting=False,
        authoritative=False,
        execution_availability=EXECUTION_AVAILABILITY,
    ),
    RuntimeAdapterSurfaceInfo(
        surface_id="gate10-pre-effect-eligibility",
        kind="pre_effect_eligibility",
        description=(
            "Gate-10 pre-effect eligibility + DispatchEnvelope coordinator "
            "(runtime_dispatch_gate10_eligibility, Slice A) — control-plane "
            "read-back battery only, contains no adapter.dispatch() call site."
        ),
        reachable_via="no production-reachable positive path (RDGO gate chain: real Gate 7 DENY, POL-005 hard DENY, execution unavailable)",
        effecting=False,
        authoritative=False,
        execution_availability=EXECUTION_AVAILABILITY,
    ),
    RuntimeAdapterSurfaceInfo(
        surface_id="dispatch-attempt-durable-lifecycle",
        kind="durable_mirror",
        description=(
            "Non-authoritative append-only dispatch-attempt mirror record "
            "(runtime_dispatch_attempt_lifecycle, Slice B) — PREPARED / "
            "EFFECT_ATTEMPT_STARTED / RECEIPT_CAPTURED / DISPATCH_UNCERTAIN / "
            "DISPATCH_NOT_STARTED. Evidence/coordination state only; "
            "authorizes no effect."
        ),
        reachable_via="written only by a trusted Gate-10 caller; no positive production path exists",
        effecting=False,
        authoritative=False,
        execution_availability=EXECUTION_AVAILABILITY,
    ),
)


# ═══════════════════════════════════════════════════════════════════════
# Introspection objects — inert data records, mirroring 111A §4
# ═══════════════════════════════════════════════════════════════════════

#: `RegistryInfo` (111A §4) is realized as 110E/110F's own
#: `RegistrySnapshot` — no new, duplicate dataclass is introduced, since
#: `RuntimeRegistry.registry_health()` already returns exactly the
#: shape 111A's design specified.
RegistryInfo = RegistrySnapshot

#: `PluginInfo` (111A §4) is realized as 110E/110F's own
#: `PluginDescriptor` — for the same reason as `RegistryInfo` above.
PluginInfo = PluginDescriptor


@dataclass(frozen=True)
class RuntimeInfo:
    """Architecture-level facts about the Runtime itself (111A §4,
    object 1). No live Runtime instance exists to query (110A: "Runtime
    ... Not implemented") — every field here is a static, frozen fact
    about the Runtime's *design*, not a live measurement."""

    pipeline_stages: tuple[str, ...]
    principles: tuple[str, ...]
    runtime_services: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityInfo:
    """One capability class's current declaration state (111A §4,
    object 4). Enumerates the full ten-class frozen taxonomy (110B §3),
    not only currently-declared capabilities, so `undeclarable` is a
    meaningful signal (`True` for exactly `execute`/`enforce`) rather
    than trivially always `False`."""

    capability: str
    declaring_plugin_ids: tuple[str, ...]
    undeclarable: bool


@dataclass(frozen=True)
class HealthInfo:
    """Metadata-only Runtime Health snapshot (111A §5, eight facets --
    this prototype implements the subset groundable without a live
    Runtime instance: registry health, plugin count, capability count,
    metadata validity, execution availability, current runtime state,
    and current maximum plugin capability; `runtime_status` reports the
    Runtime's own implementation status, honestly `not_implemented`,
    rather than a fabricated 'healthy' claim about something that does
    not exist to be healthy or unhealthy)."""

    runtime_status: str
    registry_status: str
    plugin_count: int
    capability_count: int
    metadata_validity: str
    execution_availability: str
    current_runtime_state: str
    current_maximum_plugin_capability: str


@dataclass(frozen=True)
class VersionInfo:
    """Version state across the release and every registered plugin
    (111A §4, object 6). Only grounds fields with a real source: the
    release version (`pcae.__version__`) and each registered plugin's
    own declared version (110B §1 field 11). No fabricated "contract
    model version" field is included -- 110B §5 freezes versioning
    *rules*, not a single version number for the contract model
    itself."""

    release_version: str
    plugin_versions: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class GovernanceInfo:
    """Read-only governance snapshot (111A §4, object 7 / this phase's
    objective 4): non-executing posture, broker implementation status,
    command-path observation status, and execution capability -- all
    read from already-frozen constants/registries, never computed."""

    non_executing_posture: bool
    broker_implementation_status: str
    observed_command_paths: int
    execution_capability: str


@dataclass(frozen=True)
class RuntimeStateInfo:
    """Current position in the Runtime State Model (111A §4, object 8 /
    111A §6). `current_state` is always `Observed` today; `state_model`
    is 110A §8's eight states, restated verbatim, never a competing
    vocabulary."""

    current_state: str
    state_model: tuple[str, ...]


# ═══════════════════════════════════════════════════════════════════════
# Introspection API — mirrors 111A §7's eight operations 1:1
# ═══════════════════════════════════════════════════════════════════════


def get_runtime() -> RuntimeInfo:
    """`GetRuntime()` (111A §7). Static architecture-level facts --
    reads no registry, no plugin, and no live state."""
    return RuntimeInfo(
        pipeline_stages=PIPELINE_STAGES,
        principles=RUNTIME_PRINCIPLES,
        runtime_services=RUNTIME_SERVICES,
    )


def get_registry(registry: RuntimeRegistry) -> RegistryInfo:
    """`GetRegistry()` (111A §7). Delegates entirely to
    `RuntimeRegistry.registry_health()` (110E/110F) -- this function
    adds no new computation, only names the existing call with 111A's
    frozen operation name."""
    return registry.registry_health()


def get_plugins(registry: RuntimeRegistry) -> tuple[PluginInfo, ...]:
    """`GetPlugins()` (111A §7). Delegates entirely to
    `RuntimeRegistry.list_plugins()` (110E/110F)."""
    return registry.list_plugins()


def get_capabilities(registry: RuntimeRegistry) -> tuple[CapabilityInfo, ...]:
    """`GetCapabilities()` (111A §7). One `CapabilityInfo` per frozen
    capability class (110B §3), reporting which currently-registered
    plugins declare it via `RuntimeRegistry.find_capability()`
    (110E) -- read-only, no mutation, no plugin invocation."""
    return tuple(
        CapabilityInfo(
            capability=capability,
            declaring_plugin_ids=tuple(p.plugin_id for p in registry.find_capability(capability)),
            undeclarable=capability in UNDECLARABLE_CAPABILITIES,
        )
        for capability in CAPABILITY_CLASSES
    )


def get_health(registry: RuntimeRegistry) -> HealthInfo:
    """`GetHealth()` (111A §7). Composes `RuntimeRegistry.registry_health()`
    (110E/110F, live) with static architecture-level facts (this
    module's own frozen constants) -- never computes anything not
    already available from an existing, already-verified source."""
    snapshot = registry.registry_health()
    return HealthInfo(
        runtime_status="not_implemented",
        registry_status=snapshot.registry_status,
        plugin_count=snapshot.registered_plugin_count,
        capability_count=snapshot.registered_capability_count,
        metadata_validity=snapshot.metadata_validity,
        execution_availability=EXECUTION_AVAILABILITY,
        current_runtime_state=CURRENT_RUNTIME_STATE,
        current_maximum_plugin_capability=CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
    )


def get_governance() -> GovernanceInfo:
    """`GetGovernance()` (111A §7). Reads two already-frozen, already-
    non-executing sources: `permission_broker_foundation`'s
    `IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE` constant (108A, never
    a live `PermissionBroker` evaluation) and
    `command_path_observation.INTEGRATION_REGISTRY`'s length (109C,
    never an `observe()` call)."""
    return GovernanceInfo(
        non_executing_posture=True,
        broker_implementation_status=IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE,
        observed_command_paths=len(INTEGRATION_REGISTRY),
        execution_capability=EXECUTION_AVAILABILITY,
    )


def get_adapter_surfaces() -> tuple[RuntimeAdapterSurfaceInfo, ...]:
    """The coexisting non-executing runtime-adapter surfaces (Slice B
    3S.2.1 item-9 runtime-inspect repair). Returns the frozen static
    :data:`RUNTIME_ADAPTER_SURFACES` tuple verbatim — reads no registry,
    instantiates no adapter, invokes nothing, mutates nothing, and never
    changes execution availability."""
    return RUNTIME_ADAPTER_SURFACES


def get_state() -> RuntimeStateInfo:
    """`GetState()` (111A §7). Static facts only -- restates 110A §8
    verbatim, never a live computation."""
    return RuntimeStateInfo(
        current_state=CURRENT_RUNTIME_STATE,
        state_model=RUNTIME_STATE_MODEL,
    )


def get_version(registry: RuntimeRegistry) -> VersionInfo:
    """`GetVersion()` (111A §7). Release version is imported directly
    from `pcae.__version__`; per-plugin versions are read from
    currently-registered `PluginDescriptor.version` fields (110B §1
    field 11) via `RuntimeRegistry.list_plugins()`."""
    return VersionInfo(
        release_version=_RELEASE_VERSION,
        plugin_versions=tuple((p.plugin_id, p.version) for p in registry.list_plugins()),
    )
