"""Tests for Phase 149O.20L.7O.3W — PBRD-001 v1.1 `runtime_dispatch`
request construction (Option B nested context), the fourteen-fact
binding, `approval_present` projection (PBRD-001 §7/§22), POL-004/POL-005
interaction, and DENY > HUMAN_REVIEW > ALLOW precedence.

This is the load-bearing proof that POL-005 remains an unconditional hard
deny for every non-simulation `runtime_dispatch` request after the new
action vocabulary is added -- Fundamental Phase Invariant #5.
"""

from __future__ import annotations

import dataclasses

import pytest

from pcae.core import permission_broker_foundation as pbf
from pcae.core import runtime_authority as ra
from pcae.core import runtime_dispatch_permission as rdp

from _rdw3w_helpers import (
    always_unconsumed,
    build_approval,
    dispatch_inputs,
    full_chain,
    matching_context,
    new_dispatch_identity,
)


def test_runtime_dispatch_action_registered_in_known_action_types():
    assert pbf.ACTION_TYPE_RUNTIME_DISPATCH in pbf.KNOWN_ACTION_TYPES
    assert pbf.ACTION_TYPE_RUNTIME_DISPATCH == "runtime_dispatch"


def test_runtime_dispatch_reuses_existing_adapter_execution_class():
    approval, projection, request, decision = full_chain()
    assert request.execution_class == pbf.EXECUTION_CLASS_ADAPTER


def test_runtime_dispatch_context_is_none_for_existing_actions():
    """Every existing action type leaves `runtime_dispatch_context=None`
    -- backward compatibility (Option B)."""
    request = pbf.build_permission_broker_request(
        action_type=pbf.ACTION_PUSH,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="push",
        task_id="task-a",
        evidence_available=True,
    )
    assert request.runtime_dispatch_context is None


def test_runtime_dispatch_request_carries_fourteen_facts():
    _, _, request, _ = full_chain()
    facts = request.runtime_dispatch_context
    assert facts is not None
    field_names = {f.name for f in dataclasses.fields(facts)}
    # The fourteen logical PBRD-001 binding facts, plus `profile_classification`
    # — a DERIVED, non-caller commitment added by PBRD-001 v3.0 §12a (Phase
    # ...1R.22, N-16-3). It is not a fifteenth logical fact: it is a trusted-
    # builder-computed marker over the other facts (`""` on every legacy /
    # non-narrow-profile request).
    assert field_names == {
        "invocation_id", "attempt_id", "idempotency_key", "repository_identity",
        "task_id", "lifecycle_context", "runtime_target_id",
        "adapter_descriptor_binding", "prompt_hash", "requested_capability",
        "transport_type", "network_requirement", "filesystem_scope_ref",
        "human_authority_binding", "profile_classification",
    }
    assert len(field_names) == 15
    # The fourteen logical facts (excluding the derived marker).
    assert len(field_names - {"profile_classification"}) == 14


def test_transport_type_fixed_local_cli():
    _, _, request, _ = full_chain()
    assert request.runtime_dispatch_context.transport_type == "local_cli"


def test_network_requirement_fixed_false():
    _, _, request, _ = full_chain()
    assert request.runtime_dispatch_context.network_requirement is False


# ── approval_present projection (PBRD-001 §7/§22) ────────────────────────


def test_noncanonical_non_real_fixture_never_projects_approval_present_true():
    _, _, request, _ = full_chain()
    assert request.approval_present is False


def test_missing_approval_projects_approval_present_false():
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None, simulation_only=True,
    )
    assert request.approval_present is False


def test_only_gate_5_projection_can_produce_approval_present_true():
    """There is no code path by which a caller can directly pass
    `approval_present=True` -- the builder function signature does not
    even accept that parameter."""
    import inspect

    sig = inspect.signature(rdp.build_runtime_dispatch_permission_broker_request)
    assert "approval_present" not in sig.parameters
    assert "validated_authority" in sig.parameters


def test_stale_approval_never_reaches_pb_as_approval_present_true():
    """Gate 5 rejects a stale approval before request construction even
    completes; PB never sees `approval_present=true` for it."""
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), head_commit="9" * 40)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs, invocation_id=approval.subject.invocation_id)
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=projection, simulation_only=True,
    )
    assert request.approval_present is False


def test_mismatched_subject_approval_never_reaches_pb_as_present():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), task_id="different-task")
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs, invocation_id=approval.subject.invocation_id)
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=projection, simulation_only=True,
    )
    assert request.approval_present is False


# ── POL-004 / POL-005 interaction ────────────────────────────────────────


def test_structural_request_without_real_authority_requires_human_review():
    _, _, _, decision = full_chain(simulation_only=True)
    assert decision.decision == pbf.DECISION_HUMAN_REVIEW


def test_missing_approval_triggers_pol004_human_review():
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None, simulation_only=True,
    )
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_HUMAN_REVIEW
    assert "POL-004" in decision.causing_policy_ids


def test_non_real_fixture_does_not_satisfy_pol004():
    _, _, request, decision = full_chain(simulation_only=True)
    assert request.approval_present is False
    assert "POL-004" in decision.causing_policy_ids


def test_real_dispatch_always_denied_by_pol005_after_non_real_rejection():
    _, _, request, decision = full_chain(simulation_only=False)
    assert request.simulation_only is False
    assert decision.decision == pbf.DECISION_DENY
    assert "POL-005" in decision.causing_policy_ids


def test_pol005_deny_precedes_pol004_human_review_when_both_would_fire():
    """DENY > HUMAN_REVIEW precedence: a real (non-simulation) request
    with NO approval triggers both POL-004 (would-be HUMAN_REVIEW) and
    POL-005 (DENY); DENY wins."""
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None, simulation_only=False,
    )
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_DENY
    assert "POL-005" in decision.causing_policy_ids


def test_structural_non_real_path_remains_distinct_from_pol005_deny():
    approval, projection, sim_request, sim_decision = full_chain(simulation_only=True)
    assert sim_request.approval_present is False
    assert "POL-004" in sim_decision.causing_policy_ids
    assert sim_decision.decision == pbf.DECISION_HUMAN_REVIEW

    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs, invocation_id=approval.subject.invocation_id)
    real_request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=projection, simulation_only=False,
    )
    real_decision = pbf.PermissionBroker().evaluate(real_request)
    assert real_request.approval_present is False
    assert real_decision.decision == pbf.DECISION_DENY
    # PBRD-001 v3.0 §12a (Phase ...1R.22): POL-013 also DENYs every non-simulation
    # runtime_dispatch request that is not the fully bound narrow profile,
    # reinforcing POL-005's hard DENY.
    assert real_decision.causing_policy_ids == ("POL-005", "POL-013")


def test_pb_precedence_deny_beats_human_review_beats_allow():
    assert pbf.DECISION_DENY == "DENY"
    assert pbf.DECISION_HUMAN_REVIEW == "HUMAN_REVIEW"
    assert pbf.DECISION_ALLOW == "ALLOW"


# ── Adversarial: caller-supplied authority shortcuts ─────────────────────


def test_caller_cannot_inject_approval_present_via_runtime_dispatch_context():
    """Even if a caller constructs `RuntimeDispatchRequestFacts` directly
    (bypassing the trusted builder), `PermissionBrokerRequest.approval_present`
    is a separate top-level field the facts object cannot influence --
    POL-004 only reads `request.approval_present`, never anything inside
    `runtime_dispatch_context`."""
    _, _, request, _ = full_chain()
    facts_field_names = {f.name for f in dataclasses.fields(request.runtime_dispatch_context)}
    assert "approval_present" not in facts_field_names


def test_human_authority_binding_is_reference_plus_digest_not_raw_authority():
    _, _, request, _ = full_chain()
    binding = request.runtime_dispatch_context.human_authority_binding
    field_names = {f.name for f in dataclasses.fields(binding)}
    assert field_names == {"approval_id", "approval_record_digest", "validation_evidence_digest"}
    assert binding.approval_id == ""
    assert binding.approval_record_digest == ""
    assert binding.validation_evidence_digest == ""


# ── Construction-time identity validation ────────────────────────────────


def test_invalid_invocation_id_rejected_at_construction():
    inputs = dispatch_inputs()
    bad_identity = rdp.RuntimeDispatchIdentity(
        invocation_id="not-valid",
        attempt_id="att-" + "0" * 32,
        idempotency_key=rdp.compute_runtime_dispatch_idempotency_key(
            rdp.canonical_runtime_dispatch_projection(inputs, invocation_id="inv-" + "0" * 32)
        ),
    )
    with pytest.raises(rdp.RuntimeDispatchConstructionError):
        rdp.build_runtime_dispatch_permission_broker_request(
            identity=bad_identity, inputs=inputs, validated_authority=None,
        )


def test_invalid_attempt_id_rejected_at_construction():
    inputs = dispatch_inputs()
    bad_identity = rdp.RuntimeDispatchIdentity(
        invocation_id="inv-" + "0" * 32,
        attempt_id="not-valid",
        idempotency_key=rdp.compute_runtime_dispatch_idempotency_key(
            rdp.canonical_runtime_dispatch_projection(inputs, invocation_id="inv-" + "0" * 32)
        ),
    )
    with pytest.raises(rdp.RuntimeDispatchConstructionError):
        rdp.build_runtime_dispatch_permission_broker_request(
            identity=bad_identity, inputs=inputs, validated_authority=None,
        )


def test_tampered_idempotency_key_rejected_at_construction():
    """A caller cannot present an `idempotency_key` that doesn't match the
    canonical content projection -- structurally impossible to smuggle a
    stale/forged key through the trusted builder."""
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    forged = dataclasses.replace(identity, idempotency_key="0" * 64)
    with pytest.raises(rdp.RuntimeDispatchConstructionError):
        rdp.build_runtime_dispatch_permission_broker_request(
            identity=forged, inputs=inputs, validated_authority=None,
        )
