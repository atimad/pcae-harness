"""
Runtime Inspect CLI — Phase 111C.

`pcae runtime inspect` / `pcae runtime inspect --json` / `pcae runtime
inspect --verbose`: the first CLI command exposing 111B's
observation-only Runtime Introspection prototype
(`pcae.core.runtime_introspection`) as a safe, read-only operational
snapshot. This command exposes information; it never changes behavior
(111A §1, "Visibility precedes authority").

Read-only end to end: it constructs one fresh, empty `RuntimeRegistry()`
per invocation and calls every `pcae.core.runtime_introspection.get_*()`
function against it, then formats the result. There is no persisted or
process-shared registry anywhere in this codebase today (110E's own
documented limitation: "in-memory only for this phase") — an empty
snapshot (zero registered plugins, zero declared capabilities) is
therefore the honest, correct report every invocation produces, not a
bug or a placeholder.

Never calls `PermissionBroker.evaluate()` (it reads one already-frozen
status constant, via `runtime_introspection.get_governance()`, exactly
as 111B does), never loads/instantiates/invokes a plugin, never mutates
`RuntimeRegistry` state, never performs a network call, and never reads
an environment variable, secret, token, or credential.

`PluginDescriptor.manifest` (an open, untyped field, per 110E/110F) is
deliberately excluded from both the human-readable and JSON output —
110E's own manifest could contain arbitrary caller-supplied data
(including, per a 110F/111B adversarial test, a callable), which this
command must never surface or attempt to serialize.

See `docs/PHASE_111_RUNTIME_INSPECT_CLI.md`,
`docs/PCAE_RUNTIME_INTROSPECTION.md` (111A), and
`src/pcae/core/runtime_introspection.py` (111B).
"""

from __future__ import annotations

import argparse
import json

from pcae.core.command_path_observation import INTEGRATION_REGISTRY
from pcae.core.runtime_introspection import (
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


def _build_snapshot(registry: RuntimeRegistry) -> dict:
    """Assemble the full operational snapshot from every 111B
    introspection function, in one pass. Pure read: no argument is
    mutated, no function call has a side effect."""
    runtime = get_runtime()
    registry_info = get_registry(registry)
    plugins = get_plugins(registry)
    capabilities = get_capabilities(registry)
    health = get_health(registry)
    governance = get_governance()
    state = get_state()
    version = get_version(registry)

    return {
        "runtime": {
            "pipeline_stages": list(runtime.pipeline_stages),
            "principles": list(runtime.principles),
            "runtime_services": list(runtime.runtime_services),
        },
        "registry": {
            "registered_plugin_count": registry_info.registered_plugin_count,
            "registered_capability_count": registry_info.registered_capability_count,
            "registry_status": registry_info.registry_status,
            "metadata_validity": registry_info.metadata_validity,
            "plugin_ids": list(registry_info.plugin_ids),
            "capabilities": list(registry_info.capabilities),
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
                # never surfaced by this command (see module docstring).
            }
            for p in plugins
        ],
        "capabilities": [
            {
                "capability": c.capability,
                "declaring_plugin_ids": list(c.declaring_plugin_ids),
                "undeclarable": c.undeclarable,
            }
            for c in capabilities
        ],
        "health": {
            "runtime_status": health.runtime_status,
            "registry_status": health.registry_status,
            "plugin_count": health.plugin_count,
            "capability_count": health.capability_count,
            "metadata_validity": health.metadata_validity,
            "execution_availability": health.execution_availability,
            "current_runtime_state": health.current_runtime_state,
            "current_maximum_plugin_capability": health.current_maximum_plugin_capability,
        },
        "governance": {
            "non_executing_posture": governance.non_executing_posture,
            "broker_implementation_status": governance.broker_implementation_status,
            "observed_command_paths": governance.observed_command_paths,
            "execution_capability": governance.execution_capability,
        },
        "state": {
            "current_state": state.current_state,
            "state_model": list(state.state_model),
        },
        "version": {
            "release_version": version.release_version,
            "plugin_versions": [list(pair) for pair in version.plugin_versions],
        },
    }


def _format_human(snapshot: dict, verbose: bool) -> str:
    health = snapshot["health"]
    registry = snapshot["registry"]
    governance = snapshot["governance"]
    principles = snapshot["runtime"]["principles"]

    governance_posture = "non-executing" if governance["non_executing_posture"] else "unknown"
    lines = [
        "PCAE Runtime Inspect",
        "",
        f"Runtime status:            {health['runtime_status']}",
        f"Runtime state:             {health['current_runtime_state']}",
        f"Execution capability:      {health['execution_availability']}",
        f"Maximum plugin capability: {health['current_maximum_plugin_capability']}",
        f"Registry status:           {registry['registry_status']}",
        f"Plugin count:              {registry['registered_plugin_count']}",
        f"Capability count:          {registry['registered_capability_count']}",
        f"Observation integrations:  {governance['observed_command_paths']}",
        f"Permission Broker status:  {governance['broker_implementation_status']}",
        f"Governance posture:        {governance_posture}",
        f"Runtime principles:        {len(principles)} frozen ({', '.join(principles)})",
    ]

    if verbose:
        lines.append("")
        lines.append("Plugin metadata:")
        if snapshot["plugins"]:
            for p in snapshot["plugins"]:
                lines.append(
                    f"  - {p['plugin_id']} ({p['plugin_type']}, v{p['version']}) "
                    f"capabilities={p['capabilities']} lifecycle={p['lifecycle_state']} "
                    f"health={p['health_state']} status={p['implementation_status']}"
                )
        else:
            lines.append("  (none registered)")

        lines.append("")
        lines.append("Capability declarations:")
        for c in snapshot["capabilities"]:
            marker = " [undeclarable]" if c["undeclarable"] else ""
            declaring = ", ".join(c["declaring_plugin_ids"]) or "(none)"
            lines.append(f"  - {c['capability']}: {declaring}{marker}")

        lines.append("")
        lines.append("Observation integrations:")
        for entry in INTEGRATION_REGISTRY:
            lines.append(f"  - {entry.integration_id}: {entry.command} ({entry.observation_status})")

        lines.append("")
        lines.append("Current limitations:")
        lines.append("  - Registry is in-memory only; no persistence exists (110E).")
        lines.append("  - SessionInfo/TaskInfo/PhaseInfo not yet exposed (111B, deferred).")
        lines.append("  - No plugin loading, instantiation, or invocation exists anywhere.")
        lines.append("  - This command cannot see plugins registered by another process.")

    return "\n".join(lines)


def run_runtime_inspect(args: argparse.Namespace) -> int:
    """Handler for `pcae runtime inspect`. Never mutates, never loads/
    instantiates/invokes a plugin, never calls
    `PermissionBroker.evaluate()`, never performs I/O beyond stdout."""
    registry = RuntimeRegistry()
    snapshot = _build_snapshot(registry)

    if getattr(args, "json", False):
        print(json.dumps(snapshot, indent=2, sort_keys=False))
    else:
        print(_format_human(snapshot, verbose=getattr(args, "verbose", False)))

    return 0
