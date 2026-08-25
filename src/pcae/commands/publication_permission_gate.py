"""Permission Broker gate for CHGR publication (Phase 149O.20L.7O.3C.2).

``PublicationApplicationService`` (``interactive_workflow`` zone) may not
import ``pcae.core`` -- that dependency direction is explicitly excluded
by ``.pcae/policy.toml``'s frozen ``interactive_workflow`` zone rule
("depends on no other production zone -- not core, cltr, commands, or
governance", Phase 143K). The Permission Broker adapter
(``pcae.core.mutation_permission.evaluate_publication_permission``) must
therefore be consulted one layer up, from the ``commands`` zone, which is
already permitted to depend on both ``core`` and ``interactive_workflow``
(the same edge ``commands/decision_session.py``/``commands/push.py``
already use).

This module is the single place that combines
``PublicationApplicationService.prepare_publication_request`` +
``evaluate_publication_permission`` + ``PublicationApplicationService.
hand_off`` -- both real production callers (the manual
``governance-record publish`` CLI handler and the automatic
``commands.governance_auto_publication`` entry point) call
``publish_with_permission_gate`` instead of ``hand_off``/
``resume_publication`` directly, so neither can reach
``PublicationCoordinator.execute()`` without first passing this gate.
"""
from __future__ import annotations

from pcae.core import mutation_permission
from pcae.core.paths import HarnessPath
from pcae.core.tasks import find_latest_active_task
from pcae.governance.publication.models import PublicationExecutionResult
from pcae.interactive_workflow.application.errors import PublicationPermissionDeniedApplicationError
from pcae.interactive_workflow.application.publication_service import PublicationApplicationService


def publish_with_permission_gate(
    publication_service: PublicationApplicationService,
    root: HarnessPath,
    package_id: str,
    *,
    operator_id: str,
) -> PublicationExecutionResult:
    """Prepare, permission-gate, and hand off one publication attempt.

    Mirrors ``PublicationApplicationService.resume_publication``'s own
    "determine the correct action solely by re-reading persisted state"
    contract exactly (``prepare_publication_request`` still raises
    ``PublicationAlreadyCompletedApplicationError``/
    ``ReadinessPackageStaleApplicationError`` first, unchanged) -- the
    only difference is the Permission Broker evaluation inserted strictly
    between preparation and ``hand_off()``, i.e. strictly before
    ``PublicationCoordinator.execute()`` runs.
    """

    prepared = publication_service.prepare_publication_request(package_id)

    # Mirrors `commands/push.py`'s own `active_task_for_permission.task_id
    # if active_task_for_permission else None` precedent exactly: the
    # currently active PCAE task, if any -- never invented, never
    # required (a human running `governance-record publish` with no
    # active task evaluates with `task_id=None`, identical to every other
    # Wave-1 adapter's behavior with no active task bound).
    active_task = find_latest_active_task(root)
    permission_result = mutation_permission.evaluate_publication_permission(
        root,
        session_id=prepared.session_id,
        package_id=prepared.package_id,
        task_id=active_task.task_id if active_task is not None else None,
    )
    if not permission_result.authorized:
        reason = (
            permission_result.broker_failure_reason
            if permission_result.broker_failure_reason is not None
            else (
                permission_result.decision.decision_reason
                if permission_result.decision is not None
                else "Permission Broker denied publication."
            )
        )
        raise PublicationPermissionDeniedApplicationError(
            f"Permission Broker denied publication of package {prepared.package_id!r}: {reason}",
            package_id=prepared.package_id,
            session_id=prepared.session_id,
        )

    return publication_service.hand_off(prepared, operator_id=operator_id)


__all__ = ["publish_with_permission_gate"]
