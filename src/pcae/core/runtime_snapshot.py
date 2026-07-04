"""
Runtime Snapshot — Phase 112E.

Composes 111B's eight Runtime Introspection objects (unchanged --
`RuntimeInfo`, `RegistryInfo`, `PluginInfo`, `CapabilityInfo`,
`HealthInfo`, `GovernanceInfo`, `RuntimeStateInfo`, `VersionInfo`) with
112C's `RuntimeContext` into one canonical, read-only Runtime Snapshot
— the Runtime's single operational representation, per this phase's
own new principle: **"Runtime Snapshot is the canonical read model."**

`RuntimeSnapshot` composes; it never re-derives. Every field is either
a direct reference to an object 111B already computed (delegated via
its own unchanged `get_*()` functions) or a `RuntimeContext` built by
reading real, already-governed repo state through helpers this
codebase already uses elsewhere for the same purpose (`pcae session
bootstrap` reads the identical `.pcae/session.json` and
`tasks/active/` sources via the identical `pcae.core.session`/
`pcae.core.tasks` functions). No field on `RuntimeSnapshot` is a new,
independently-computed value duplicating something Introspection or
Context already represents (112E objective 2: "Do not duplicate data
already represented elsewhere").

Read-only, observation-only, execution-unavailable: this module never
calls `PermissionBroker.evaluate()`, never loads/instantiates/invokes a
plugin, never mutates `RuntimeRegistry` state, never performs a network
call, and never reads an environment variable, secret, token, or
credential. Its one read-only filesystem access
(`build_runtime_context_from_repo()`) reflects already-governed repo
state into an observation-only `RuntimeContext` — the same class of
read `pcae session bootstrap`/`pcae runtime inspect`'s own prior
phases already perform, not a new I/O capability introduced here.

See `docs/PCAE_RUNTIME_SNAPSHOT.md`,
`docs/PHASE_112_RUNTIME_SNAPSHOT_INTEGRATION.md`,
`src/pcae/core/runtime_introspection.py` (111B), and
`src/pcae/core/runtime_context.py` (112C).
"""

from __future__ import annotations

from dataclasses import dataclass

from pcae.core.command_path_observation import INTEGRATION_REGISTRY
from pcae.core.paths import HarnessPath
from pcae.core.runtime_context import (
    ObservationContext,
    RuntimeContext,
    RuntimeSession,
    TaskContext,
)
from pcae.core.runtime_introspection import (
    CapabilityInfo,
    GovernanceInfo,
    HealthInfo,
    PluginInfo,
    RegistryInfo,
    RuntimeInfo,
    RuntimeStateInfo,
    VersionInfo,
    get_capabilities,
    get_governance,
    get_health,
    get_plugins,
    get_registry,
    get_runtime,
    get_state,
    get_version,
)
from pcae.core.runtime_registry import RuntimeRegistry
from pcae.core.session import read_session_snapshot
from pcae.core.tasks import find_latest_active_task


@dataclass(frozen=True)
class RuntimeSnapshot:
    """The Runtime's single, canonical, read-only operational snapshot
    (112E). Composes 111B's eight Introspection objects, unchanged,
    with 112C's `RuntimeContext` — the observation-only integration
    this phase's objective 4 requires. `context` is `None` only when no
    session state exists at all (`.pcae/session.json` absent), never as
    an error condition."""

    runtime: RuntimeInfo
    registry: RegistryInfo
    plugins: tuple[PluginInfo, ...]
    capabilities: tuple[CapabilityInfo, ...]
    health: HealthInfo
    governance: GovernanceInfo
    state: RuntimeStateInfo
    version: VersionInfo
    context: RuntimeContext | None


def build_runtime_context_from_repo(root: HarnessPath) -> RuntimeContext | None:
    """Best-effort, read-only `RuntimeContext` reflecting real repo
    state: the active task contract (`tasks/active/`) and session
    (`.pcae/session.json`), read via the same already-governed helpers
    `pcae session bootstrap` itself uses
    (`pcae.core.session.read_session_snapshot`,
    `pcae.core.tasks.find_latest_active_task`). Populates only what is
    genuinely observable today: `RuntimeSession`, its active
    `TaskContext` (if any), and `ObservationContext` (the four INT-NNN
    integrations, always consultable per 112B §8's "Observation always
    available" invariant).

    `PhaseContext`/`IntentContext`/`ApprovalContext`/
    `BrokerDecisionContext`/`EvidenceContext` are deliberately never
    populated here — none has a real, governed backing source anywhere
    in this codebase (`COMP-003`/`COMP-007` remain unimplemented, per
    112A/112B/112C/112D), and inventing placeholder values for them
    would misrepresent what this phase actually observes rather than
    honestly reporting nothing exists to show yet.

    Returns `None` only when `.pcae/session.json` does not exist at all
    — an uninitialized repo has no session to report, not an error."""
    session_snapshot = read_session_snapshot(root)
    if session_snapshot is None:
        return None

    session_id = str(session_snapshot.data.get("timestamp") or "unknown-session")

    active_task = find_latest_active_task(root)
    tasks: tuple[TaskContext, ...] = ()
    if active_task is not None:
        tasks = (
            TaskContext(
                task_id=active_task.task_id,
                session_id=session_id,
                title=active_task.title,
                lifecycle_stage="Observed",
            ),
        )

    observation = ObservationContext(
        observation_id=f"{session_id}-observation",
        session_id=session_id,
        consulted_integrations=tuple(entry.integration_id for entry in INTEGRATION_REGISTRY),
        lifecycle_stage="Observed",
    )

    session = RuntimeSession(
        session_id=session_id,
        tasks=tasks,
        observation=observation,
        lifecycle_stage="Observed",
    )
    return RuntimeContext(session=session, lifecycle_stage="Observed")


def build_runtime_snapshot(root: HarnessPath, registry: RuntimeRegistry) -> RuntimeSnapshot:
    """Assemble the full `RuntimeSnapshot` in one pass. Delegates
    entirely to 111B's own `get_*()` functions (unchanged) for every
    Introspection field, and to `build_runtime_context_from_repo()` for
    the Context field — pure composition, no new computation."""
    return RuntimeSnapshot(
        runtime=get_runtime(),
        registry=get_registry(registry),
        plugins=get_plugins(registry),
        capabilities=get_capabilities(registry),
        health=get_health(registry),
        governance=get_governance(),
        state=get_state(),
        version=get_version(registry),
        context=build_runtime_context_from_repo(root),
    )


def _context_to_dict(context: RuntimeContext | None) -> dict | None:
    """Serialize a `RuntimeContext` for JSON output. `active_phase`/
    `intent`/`approval`/`broker_decision`/`evidence` are always `None`
    today — named explicitly, per this phase's objective 4, rather than
    omitted, so a consumer can see what Runtime Context will eventually
    report without mistaking today's absence for a missing feature."""
    if context is None or context.session is None:
        return None
    session = context.session
    observation = session.observation
    return {
        "session_id": session.session_id,
        "lifecycle_stage": session.lifecycle_stage,
        "active_tasks": [
            {"task_id": t.task_id, "title": t.title, "lifecycle_stage": t.lifecycle_stage}
            for t in session.tasks
        ],
        "active_phase": None,
        "intent": None,
        "approval": None,
        "broker_decision": None,
        "evidence": None,
        "observation": (
            {
                "observation_id": observation.observation_id,
                "consulted_integrations": list(observation.consulted_integrations),
                "lifecycle_stage": observation.lifecycle_stage,
            }
            if observation is not None
            else None
        ),
    }


def snapshot_to_dict(snapshot: RuntimeSnapshot) -> dict:
    """Serialize a `RuntimeSnapshot` into the CLI's stable JSON shape:
    identical `runtime`/`registry`/`plugins`/`capabilities`/`health`/
    `governance`/`state`/`version` top-level keys to 111C's original
    `_build_snapshot()` dict (backward compatible), plus one new,
    additive `context` key. `manifest` is never included (110E/110F/
    111C's own exclusion rule, inherited unchanged)."""
    return {
        "runtime": {
            "pipeline_stages": list(snapshot.runtime.pipeline_stages),
            "principles": list(snapshot.runtime.principles),
            "runtime_services": list(snapshot.runtime.runtime_services),
        },
        "registry": {
            "registered_plugin_count": snapshot.registry.registered_plugin_count,
            "registered_capability_count": snapshot.registry.registered_capability_count,
            "registry_status": snapshot.registry.registry_status,
            "metadata_validity": snapshot.registry.metadata_validity,
            "plugin_ids": list(snapshot.registry.plugin_ids),
            "capabilities": list(snapshot.registry.capabilities),
        },
        "plugins": [
            {
                "plugin_id": p.plugin_id,
                "plugin_type": p.plugin_type,
                "version": p.version,
                "capabilities": list(p.capabilities),
                "lifecycle_state": p.lifecycle_state,
                "health_state": p.health_state,
                "implementation_status": p.implementation_status,
                # manifest deliberately omitted -- open/untyped field,
                # never surfaced (110E/110F/111C).
            }
            for p in snapshot.plugins
        ],
        "capabilities": [
            {
                "capability": c.capability,
                "declaring_plugin_ids": list(c.declaring_plugin_ids),
                "undeclarable": c.undeclarable,
            }
            for c in snapshot.capabilities
        ],
        "health": {
            "runtime_status": snapshot.health.runtime_status,
            "registry_status": snapshot.health.registry_status,
            "plugin_count": snapshot.health.plugin_count,
            "capability_count": snapshot.health.capability_count,
            "metadata_validity": snapshot.health.metadata_validity,
            "execution_availability": snapshot.health.execution_availability,
            "current_runtime_state": snapshot.health.current_runtime_state,
            "current_maximum_plugin_capability": snapshot.health.current_maximum_plugin_capability,
        },
        "governance": {
            "non_executing_posture": snapshot.governance.non_executing_posture,
            "broker_implementation_status": snapshot.governance.broker_implementation_status,
            "observed_command_paths": snapshot.governance.observed_command_paths,
            "execution_capability": snapshot.governance.execution_capability,
        },
        "state": {
            "current_state": snapshot.state.current_state,
            "state_model": list(snapshot.state.state_model),
        },
        "version": {
            "release_version": snapshot.version.release_version,
            "plugin_versions": [list(pair) for pair in snapshot.version.plugin_versions],
        },
        "context": _context_to_dict(snapshot.context),
    }
