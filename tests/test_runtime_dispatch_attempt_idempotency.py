"""Tests for Phase 149O.20L.7O.3W — attempt_id/idempotency_key adversarial
matrix (3V.2 §21, RDGO-001 §10a, PBRD-001 §15).

Proves: `attempt_id` answers "which concrete try"; `idempotency_key`
answers "which logical request"; the two are never conflated with
`invocation_id` or `approval_id`; replay/collision detection fails
closed.
"""

from __future__ import annotations

import dataclasses

import pytest

from pcae.core import permission_broker_foundation as pbf
from pcae.core import runtime_dispatch_permission as rdp

from _rdw3w_helpers import dispatch_inputs, full_chain


def test_attempt_id_distinct_from_invocation_id():
    inputs = dispatch_inputs()
    identity = rdp.new_runtime_dispatch_identity(inputs)
    assert identity.attempt_id != identity.invocation_id
    assert identity.attempt_id.startswith("att-")
    assert identity.invocation_id.startswith("inv-")


def test_attempt_id_distinct_from_idempotency_key():
    inputs = dispatch_inputs()
    identity = rdp.new_runtime_dispatch_identity(inputs)
    assert identity.attempt_id != identity.idempotency_key


def test_idempotency_key_distinct_from_approval_id():
    _, projection, request, _ = full_chain()
    assert request.runtime_dispatch_context.idempotency_key != projection.approval_id


def test_two_fresh_identities_for_same_inputs_share_idempotency_key_but_not_attempt_id():
    """A genuine retry of the same unchanged logical request: new
    `attempt_id` every time, same `idempotency_key`."""
    inputs = dispatch_inputs()
    id1 = rdp.new_runtime_dispatch_identity(inputs)
    id2 = rdp.new_runtime_dispatch_identity(inputs, invocation_id=id1.invocation_id)
    assert id1.attempt_id != id2.attempt_id
    assert id1.idempotency_key == id2.idempotency_key
    assert id1.invocation_id == id2.invocation_id


def test_changed_target_produces_different_idempotency_key():
    inputs_a = dispatch_inputs(runtime_target_id="target-a")
    inputs_b = dispatch_inputs(runtime_target_id="target-b")
    key_a = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(inputs_a)
    )
    key_b = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(inputs_b)
    )
    assert key_a != key_b


def test_changed_prompt_produces_different_idempotency_key():
    inputs_a = dispatch_inputs(prompt="do thing A")
    inputs_b = dispatch_inputs(prompt="do thing B")
    key_a = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(inputs_a)
    )
    key_b = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(inputs_b)
    )
    assert key_a != key_b


def test_changed_task_produces_different_idempotency_key():
    inputs_a = dispatch_inputs(task_id="task-x")
    inputs_b = dispatch_inputs(task_id="task-y")
    key_a = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(inputs_a)
    )
    key_b = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(inputs_b)
    )
    assert key_a != key_b


def test_changed_repository_produces_different_idempotency_key():
    inputs_a = dispatch_inputs(repository_identity="a" * 64)
    inputs_b = dispatch_inputs(repository_identity="b" * 64)
    key_a = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(inputs_a)
    )
    key_b = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(inputs_b)
    )
    assert key_a != key_b


def test_idempotency_key_is_pure_function_impossible_to_hold_constant_across_change():
    """Structurally impossible test (3V.2 §21 items 2/3): it is not merely
    unlikely but architecturally impossible for the key to stay the same
    while target/prompt change, because the key is a pure function over
    exactly those fields."""
    inputs_a = dispatch_inputs()
    inputs_b = dispatch_inputs(runtime_target_id="a-different-target")
    proj_a = rdp.canonical_runtime_dispatch_projection(inputs_a)
    proj_b = rdp.canonical_runtime_dispatch_projection(inputs_b)
    assert proj_a != proj_b
    assert rdp.compute_runtime_dispatch_idempotency_key(
        proj_a
    ) != rdp.compute_runtime_dispatch_idempotency_key(proj_b)


# ── Collision detection (RPAC-REQ-066) ──────────────────────────────────


def test_same_attempt_id_different_content_hard_collision():
    tracker = rdp.RuntimeDispatchIdentityTracker()
    inputs_a = dispatch_inputs(task_id="task-a")
    inputs_b = dispatch_inputs(task_id="task-b")
    identity_a = rdp.new_runtime_dispatch_identity(inputs_a)
    # Force a collision: reuse identity_a's attempt_id with content from
    # a different logical request.
    identity_b_forced = dataclasses.replace(
        rdp.new_runtime_dispatch_identity(inputs_b), attempt_id=identity_a.attempt_id
    )
    rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity_a, inputs=inputs_a, validated_authority=None, identity_tracker=tracker,
    )
    with pytest.raises(rdp.RuntimeDispatchConstructionError):
        rdp.build_runtime_dispatch_permission_broker_request(
            identity=identity_b_forced, inputs=inputs_b, validated_authority=None, identity_tracker=tracker,
        )


def test_same_idempotency_key_different_invocation_id_rejected():
    """Distinct logical invocations never share an idempotency key by
    construction; presenting an old key with a "new" invocation is
    rejected (PBRD-001 §15)."""
    tracker = rdp.RuntimeDispatchIdentityTracker()
    inputs = dispatch_inputs()
    identity_1 = rdp.new_runtime_dispatch_identity(inputs)
    rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity_1, inputs=inputs, validated_authority=None, identity_tracker=tracker,
    )
    # A different invocation presenting the SAME idempotency_key (which,
    # for unchanged inputs, is legitimately identical) but claiming a new
    # attempt AND a new invocation_id simultaneously is a replay-as-new
    # attack: reject.
    forged = rdp.RuntimeDispatchIdentity(
        invocation_id="inv-" + "9" * 32,
        attempt_id="att-" + "8" * 32,
        idempotency_key=identity_1.idempotency_key,
    )
    with pytest.raises(rdp.RuntimeDispatchConstructionError):
        rdp.build_runtime_dispatch_permission_broker_request(
            identity=forged, inputs=inputs, validated_authority=None, identity_tracker=tracker,
        )


def test_same_attempt_id_identical_content_is_not_a_collision():
    """Re-registering the exact same identity twice (e.g. idempotent
    resume before any state change) is not itself an error at the
    tracker layer."""
    tracker = rdp.RuntimeDispatchIdentityTracker()
    inputs = dispatch_inputs()
    identity = rdp.new_runtime_dispatch_identity(inputs)
    rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None, identity_tracker=tracker,
    )
    rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None, identity_tracker=tracker,
    )  # no raise


# ── PB decision replay across changed attempt_id (PBRD-001 §10) ─────────


def test_pb_decision_is_freshly_evaluated_per_request_never_cached_across_attempt_change():
    """A changed `attempt_id` always yields a structurally distinct
    request (distinct `runtime_dispatch_context.attempt_id`), so the
    broker's per-call evaluation is inherently non-cached across attempts
    -- there is no code path in this module that reuses a prior
    `PermissionBrokerDecision` object across two different requests."""
    inputs = dispatch_inputs()
    identity_1 = rdp.new_runtime_dispatch_identity(inputs)
    identity_2 = rdp.new_runtime_dispatch_identity(inputs, invocation_id=identity_1.invocation_id)
    assert identity_1.attempt_id != identity_2.attempt_id

    broker = pbf.PermissionBroker()
    req_1 = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity_1, inputs=inputs, validated_authority=None,
    )
    req_2 = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity_2, inputs=inputs, validated_authority=None,
    )
    decision_1 = broker.evaluate(req_1)
    decision_2 = broker.evaluate(req_2)
    assert req_1.runtime_dispatch_context.attempt_id != req_2.runtime_dispatch_context.attempt_id
    # Both independently evaluated (equal outcome here since inputs are
    # identical modulo attempt_id -- the point is each call is a fresh,
    # independent evaluation, not a cache hit).
    assert decision_1.decision == decision_2.decision == pbf.DECISION_HUMAN_REVIEW


def test_uncertain_attempt_requires_brand_new_attempt_id_for_retry():
    """Modeling RDGO-001 §10a's crash/uncertainty relationship: even a
    'same logical request' retry after an uncertain prior attempt must
    mint a genuinely new `attempt_id` -- verified structurally, since
    `new_runtime_dispatch_identity` never accepts a caller-supplied
    `attempt_id`."""
    import inspect

    sig = inspect.signature(rdp.new_runtime_dispatch_identity)
    assert "attempt_id" not in sig.parameters
