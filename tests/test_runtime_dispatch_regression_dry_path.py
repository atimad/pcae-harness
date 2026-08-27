"""Tests for Phase 149O.20L.7O.3W — dry-path protection regression (3V.2
§34, PBRD-001 §13): the existing mock-v1
`adapter_invocation`/`simulation_only=true` path MUST remain byte/
behavior-identical after this phase's additive changes.

This file does not re-implement the existing dry-path suites
(`test_runtime_dry_consumption_3s2.py`,
`test_session_bootstrap_dry_runtime_3s2.py`) -- those are re-run
unmodified as part of Fast Green. This file adds the specific new
assertions this phase's own governing instructions require: the dry
path's `InvocationRequest` is not required to carry
`runtime_dispatch`-specific facts beyond what it already had, and its
action/execution-class shape is unchanged.
"""

from __future__ import annotations

import dataclasses

from pcae.core import permission_broker_foundation as pbf
from pcae.core.runtime_invocation import InvocationRequest, compute_idempotency_key


def test_dry_path_action_type_unchanged():
    assert pbf.ACTION_ADAPTER_INVOCATION == "adapter_invocation"
    assert pbf.ACTION_ADAPTER_INVOCATION != pbf.ACTION_TYPE_RUNTIME_DISPATCH


def test_dry_path_invocation_request_shape_unchanged():
    """The dry path's `InvocationRequest` already has `attempt_id`/
    `idempotency_key` (RPAC-001, pre-existing) -- this phase does not add
    any new required field to it (PBRD-001 §13 explicit prohibition)."""
    field_names = {f.name for f in dataclasses.fields(InvocationRequest)}
    # Confirm none of the new real-dispatch-only concepts leaked in.
    forbidden_new_fields = {
        "human_authority_binding", "runtime_dispatch_context",
        "adapter_descriptor_binding", "filesystem_scope_ref",
    }
    assert field_names.isdisjoint(forbidden_new_fields)


def test_existing_compute_idempotency_key_untouched():
    """The pre-existing dry-path hashing function is not migrated or
    widened -- the new `compute_runtime_dispatch_idempotency_key` is a
    separate sibling function (3V.2 §20/§27 explicit)."""
    projection = {"a": 1, "b": 2}
    assert compute_idempotency_key(projection) == compute_idempotency_key(projection)
    import inspect

    sig = inspect.signature(compute_idempotency_key)
    assert list(sig.parameters) == ["projection"]


def test_dry_and_real_dispatch_action_types_are_distinct_and_both_recognized():
    assert pbf.ACTION_ADAPTER_INVOCATION in pbf.KNOWN_ACTION_TYPES
    assert pbf.ACTION_TYPE_RUNTIME_DISPATCH in pbf.KNOWN_ACTION_TYPES
    assert pbf.ACTION_ADAPTER_INVOCATION != pbf.ACTION_TYPE_RUNTIME_DISPATCH


def test_dry_path_permission_broker_request_construction_unaffected():
    """A dry-path-shaped request (adapter_invocation, simulation_only=True,
    no runtime_dispatch_context) still evaluates exactly as before --
    `runtime_dispatch_context` defaults to `None` and is never required."""
    request = pbf.build_permission_broker_request(
        action_type=pbf.ACTION_ADAPTER_INVOCATION,
        execution_class=pbf.EXECUTION_CLASS_ADAPTER,
        requested_component="COMP-006",
        requested_capability="mock_dry_invocation",
        task_id="task-a",
        evidence_available=True,
        approval_present=True,
        simulation_only=True,
    )
    assert request.runtime_dispatch_context is None
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_ALLOW
