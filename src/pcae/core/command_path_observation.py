"""
Command-Path Observation — Phase 109B.

The first, observation-only integration between a governed CLI command
and the Permission Broker (`src/pcae/core/permission_broker_foundation.py`,
frozen and hardened across 108A-108D). A command may call `observe()` to
ask the broker for a decision, purely so a future phase can eventually
build real telemetry or testing on top of it. The decision returned here
must never be used to change command behavior, authorize anything, deny
anything, or execute anything.

This module enforces that boundary by construction:

- `observe()` cannot raise. Every internal failure (a malformed request,
  an unexpected exception from the broker, anything) degrades to
  returning `None` — it never propagates an exception to the caller.
- `observe()` performs no I/O, no file access, no subprocess invocation,
  and no state mutation of any kind. It only builds a request and calls
  `PermissionBroker.evaluate()`, which is itself already proven (108A
  AST-import isolation tests, still unmodified by this phase) to have no
  execution capability.
- Nothing in this module prints, logs, persists, or otherwise surfaces
  the decision anywhere a caller could accidentally start depending on
  it for control flow. Callers that want to inspect what `observe()`
  returned must do so explicitly and knowingly (e.g. in a test) — normal
  command control flow discards it immediately.

See `docs/PHASE_109_FIRST_COMMAND_PATH_INTEGRATION_PROTOTYPE.md` for the
full observation contract and safety case, and
`docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` (107A/109A) for
the frozen architecture this integration follows.
"""

from __future__ import annotations

from pcae.core.permission_broker_foundation import (
    PermissionBroker,
    PermissionBrokerDecision,
    build_permission_broker_request,
)


def observe(
    *,
    action_type: str,
    execution_class: str,
    requested_component: str,
    requested_capability: str,
    task_id: str | None = None,
    phase_id: str | None = None,
    evidence_available: bool = False,
    approval_present: bool = False,
) -> PermissionBrokerDecision | None:
    """Consult the Permission Broker for observation purposes only.

    Returns the broker's decision, or `None` if observation itself could
    not complete for any reason. The return value carries no authority:
    it must never be used to change caller behavior, block an action, or
    grant an action. Callers that call this function and then act on
    every branch of the result identically (i.e. ignore it) are using it
    correctly; callers that branch on `decision.decision` to change what
    they do are integrating the broker for real, which is out of scope
    for this observation-only prototype (Phase 109B) and requires the
    hardening design a later phase (109C+) would need to freeze first.
    """
    try:
        request = build_permission_broker_request(
            action_type=action_type,
            execution_class=execution_class,
            requested_component=requested_component,
            requested_capability=requested_capability,
            task_id=task_id,
            phase_id=phase_id,
            evidence_available=evidence_available,
            approval_present=approval_present,
            simulation_only=True,
        )
        return PermissionBroker().evaluate(request)
    except Exception:
        return None
