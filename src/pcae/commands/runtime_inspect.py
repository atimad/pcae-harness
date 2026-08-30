"""
Runtime Inspect CLI — Phase 111C, integrated with Runtime Snapshot in 112E.

`pcae runtime inspect` / `pcae runtime inspect --json` / `pcae runtime
inspect --verbose`: renders the Runtime Snapshot (112E,
`pcae.core.runtime_snapshot`) — the Runtime's single, canonical,
read-only operational representation, composing 111B's Runtime
Introspection objects with 112C's Runtime Context. This command
exposes information; it never changes behavior (111A §1, "Visibility
precedes authority").

As of 112E, this module no longer assembles the snapshot itself
(112E objective 3: "Avoid bespoke assembly logic inside the CLI") —
`_build_snapshot()` is now a thin, backward-compatible wrapper around
`pcae.core.runtime_snapshot.build_runtime_snapshot()`, kept under its
original name and single-argument signature so every call site written
against 111C/111D's own `_build_snapshot(registry)` continues to work
unchanged.

Read-only end to end: it constructs one fresh, empty `RuntimeRegistry()`
per invocation and delegates to Runtime Snapshot, which calls every
`pcae.core.runtime_introspection.get_*()` function against it, then
formats the result. There is no persisted or process-shared registry
anywhere in this codebase today (110E's own documented limitation:
"in-memory only for this phase") — an empty snapshot (zero registered
plugins, zero declared capabilities) is therefore the honest, correct
report every invocation produces, not a bug or a placeholder.

Never calls `PermissionBroker.evaluate()` (it reads one already-frozen
status constant, via `runtime_introspection.get_governance()`, exactly
as 111B does), never loads/instantiates/invokes a plugin, never mutates
`RuntimeRegistry` state, never performs a network call, and never reads
an environment variable, secret, token, or credential. Runtime
Snapshot's own Runtime Context integration reads real repo state
(`.pcae/session.json`, `tasks/active/`) through the same already-
governed helpers `pcae session bootstrap` uses — read-only, not a new
I/O capability this command introduces.

`PluginDescriptor.manifest` (an open, untyped field, per 110E/110F) is
deliberately excluded from both the human-readable and JSON output —
110E's own manifest could contain arbitrary caller-supplied data
(including, per a 110F/111B adversarial test, a callable), which this
command must never surface or attempt to serialize.

See `docs/PHASE_111_RUNTIME_INSPECT_CLI.md`,
`docs/PCAE_RUNTIME_INTROSPECTION.md` (111A),
`docs/PCAE_RUNTIME_SNAPSHOT.md` (112E),
`src/pcae/core/runtime_introspection.py` (111B), and
`src/pcae/core/runtime_snapshot.py` (112E).
"""

from __future__ import annotations

import argparse
import json

from pcae.core.command_path_observation import INTEGRATION_REGISTRY
from pcae.core.paths import HarnessPath
from pcae.core.runtime_introspection import get_adapter_surfaces
from pcae.core.runtime_registry import RuntimeRegistry
from pcae.core.runtime_snapshot import build_runtime_snapshot, snapshot_to_dict


def _build_snapshot(registry: RuntimeRegistry) -> dict:
    """Assemble the full operational snapshot. Kept under its original
    111C name and single-argument signature for backward compatibility
    -- delegates entirely to Runtime Snapshot (112E) for assembly; this
    function itself contains no loop, no bespoke composition logic, and
    no side effect."""
    root = HarnessPath.cwd()
    snapshot = build_runtime_snapshot(root, registry)
    return snapshot_to_dict(snapshot)


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

    # 3S.2.1 item-9 runtime-inspect discoverability repair (Slice B): an
    # observational, non-mutating one-line pointer that other,
    # RuntimeRegistry-independent runtime-adapter-shaped surfaces coexist
    # in this repository, so "Plugin count: 0 / Registry status: empty"
    # above is not over-read as "nothing runtime-adapter-shaped exists".
    # Every surface is non-effecting and execution remains unavailable;
    # this implies NO adapter readiness. Full detail in `--verbose`.
    adapter_surfaces = get_adapter_surfaces()
    if adapter_surfaces:
        lines.append(
            f"Runtime-adapter surfaces:  {len(adapter_surfaces)} coexisting, "
            f"all non-effecting, execution {health['execution_availability']} "
            f"(observational; use --verbose)"
        )

    if verbose:
        lines.append("")
        lines.append(
            "Runtime-adapter surfaces (observational — no adapter enabled, execution unavailable):"
        )
        for s in adapter_surfaces:
            lines.append(
                f"  - {s.surface_id} ({s.kind}): effecting={s.effecting} "
                f"authoritative={s.authoritative} execution={s.execution_availability}"
            )
            lines.append(f"      {s.description}")
            lines.append(f"      reachable via: {s.reachable_via}")

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
        lines.append("Runtime Context (112E):")
        context = snapshot.get("context")
        if context is None:
            lines.append("  (no session state observed)")
        else:
            lines.append(f"  Session:         {context['session_id']} ({context['lifecycle_stage']})")
            if context["active_tasks"]:
                for t in context["active_tasks"]:
                    lines.append(f"  Active task:     {t['task_id']} — {t['title']} ({t['lifecycle_stage']})")
            else:
                lines.append("  Active task:     none")
            lines.append("  Active phase:    not implemented anywhere (COMP-003/COMP-007 unimplemented)")
            lines.append("  Intent:          not implemented anywhere")
            lines.append("  Approval:        not implemented anywhere (COMP-003)")
            lines.append("  Broker decision: not implemented anywhere")
            lines.append("  Evidence:        not implemented anywhere (COMP-007)")
            observation = context["observation"]
            if observation is not None:
                lines.append(
                    f"  Observation:     {len(observation['consulted_integrations'])} integrations consulted "
                    f"({', '.join(observation['consulted_integrations'])})"
                )

        lines.append("")
        lines.append("Current limitations:")
        lines.append("  - Registry is in-memory only; no persistence exists (110E).")
        lines.append("  - SessionInfo/TaskInfo/PhaseInfo not yet exposed (111B, deferred).")
        lines.append("  - No plugin loading, instantiation, or invocation exists anywhere.")
        lines.append("  - This command cannot see plugins registered by another process.")
        lines.append("  - Active phase/intent/approval/broker decision/evidence remain unimplemented (112E).")

    return "\n".join(lines)


def run_runtime_inspect(args: argparse.Namespace) -> int:
    """Handler for `pcae runtime inspect`. Never mutates, never loads/
    instantiates/invokes a plugin, never calls
    `PermissionBroker.evaluate()`, never performs I/O beyond stdout and
    the read-only Runtime Context reads Runtime Snapshot itself
    performs."""
    registry = RuntimeRegistry()
    snapshot = _build_snapshot(registry)

    if getattr(args, "json", False):
        print(json.dumps(snapshot, indent=2, sort_keys=False))
    else:
        print(_format_human(snapshot, verbose=getattr(args, "verbose", False)))

    return 0
