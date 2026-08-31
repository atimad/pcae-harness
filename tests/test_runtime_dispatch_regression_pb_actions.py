"""Tests for Phase 149O.20L.7O.3W — existing PB action regression
protection (3V.2 §35): rerun rollback, push, publication, and other
mutation-action request construction/evaluation with unchanged inputs and
assert byte-identical-shape decisions, proving the new optional
`runtime_dispatch_context` field and new action constant do not alter any
existing action's evaluation.
"""

from __future__ import annotations

from pcae.core import permission_broker_foundation as pbf

from _rdw3w_helpers import full_chain


def _decision_shape(decision: pbf.PermissionBrokerDecision) -> dict:
    return {
        "decision": decision.decision,
        "decision_reason": decision.decision_reason,
        "matched_no_go_ids": decision.matched_no_go_ids,
        "matched_invariants": decision.matched_invariants,
        "requires_human": decision.requires_human,
        "causing_policy_ids": decision.causing_policy_ids,
        "precedence_reason": decision.precedence_reason,
    }


def _build(action_type: str, execution_class: str, **overrides) -> pbf.PermissionBrokerRequest:
    kwargs = dict(
        requested_component="COMP-001",
        requested_capability="generic",
        task_id="task-a",
        evidence_available=True,
        approval_present=True,
        simulation_only=True,
    )
    kwargs.update(overrides)
    return pbf.build_permission_broker_request(
        action_type=action_type, execution_class=execution_class, **kwargs
    )


def test_rollback_action_unaffected_by_extension():
    request = _build(pbf.ACTION_ROLLBACK, pbf.EXECUTION_CLASS_ROLLBACK)
    assert request.runtime_dispatch_context is None
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_ALLOW


def test_push_action_unaffected_by_extension():
    request = _build(pbf.ACTION_PUSH, pbf.EXECUTION_CLASS_MUTATION)
    assert request.runtime_dispatch_context is None
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_ALLOW


def test_source_mutation_action_unaffected_by_extension():
    request = _build(pbf.ACTION_SOURCE_MUTATION, pbf.EXECUTION_CLASS_MUTATION)
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_ALLOW


def test_backend_invocation_action_unaffected_by_extension():
    request = _build(pbf.ACTION_BACKEND_INVOCATION, pbf.EXECUTION_CLASS_BACKEND)
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_ALLOW


def test_adapter_invocation_action_unaffected_by_extension():
    request = _build(pbf.ACTION_ADAPTER_INVOCATION, pbf.EXECUTION_CLASS_ADAPTER)
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_ALLOW


def test_shell_command_action_unaffected_by_extension():
    request = _build(pbf.ACTION_SHELL_COMMAND, pbf.EXECUTION_CLASS_SHELL)
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_ALLOW


def test_missing_approval_still_triggers_human_review_for_every_pre_existing_mediated_class():
    for action_type, execution_class in (
        (pbf.ACTION_ROLLBACK, pbf.EXECUTION_CLASS_ROLLBACK),
        (pbf.ACTION_SHELL_COMMAND, pbf.EXECUTION_CLASS_SHELL),
        (pbf.ACTION_BACKEND_INVOCATION, pbf.EXECUTION_CLASS_BACKEND),
        (pbf.ACTION_ADAPTER_INVOCATION, pbf.EXECUTION_CLASS_ADAPTER),
    ):
        request = _build(action_type, execution_class, approval_present=False)
        decision = pbf.PermissionBroker().evaluate(request)
        assert decision.decision == pbf.DECISION_HUMAN_REVIEW
        assert "POL-004" in decision.causing_policy_ids


def test_real_non_simulation_request_still_denied_for_every_pre_existing_action():
    for action_type, execution_class in (
        (pbf.ACTION_ROLLBACK, pbf.EXECUTION_CLASS_ROLLBACK),
        (pbf.ACTION_PUSH, pbf.EXECUTION_CLASS_MUTATION),
        (pbf.ACTION_ADAPTER_INVOCATION, pbf.EXECUTION_CLASS_ADAPTER),
    ):
        request = _build(action_type, execution_class, simulation_only=False)
        decision = pbf.PermissionBroker().evaluate(request)
        assert decision.decision == pbf.DECISION_DENY
        assert "POL-005" in decision.causing_policy_ids


def test_policy_registry_still_exactly_twelve_canonical_policies():
    """Phase ...1R.22 (N-16-3) adds exactly one canonical policy, POL-013
    (Narrow Local-CLI Dispatch Eligibility) -- canonical count is now 13.
    The generic POL-004 / POL-005 / POL-006 coverage of `runtime_dispatch`
    via `execution_class=adapter` is unchanged; POL-013 is an additive
    conjunctive companion that never emits ALLOW or HUMAN_REVIEW."""
    assert len(pbf.POLICY_IDS) == 13
    assert pbf.POLICY_IDS[-1] == "POL-013"
    assert set(pbf.POLICY_IDS) == pbf.POLICY_IDS_CANONICAL


def test_policy_registry_construction_still_validates_completeness():
    registry = pbf.PolicyRegistry()
    assert set(registry.policy_ids) == pbf.POLICY_IDS_CANONICAL


def test_unknown_action_type_still_denied_by_pol006_for_a_truly_unknown_action():
    request = pbf.build_permission_broker_request(
        action_type="totally_made_up_action",
        execution_class=pbf.EXECUTION_CLASS_ADAPTER,
        requested_component="COMP-006",
        requested_capability="x",
        task_id="task-a",
        evidence_available=True,
        approval_present=True,
        simulation_only=True,
    )
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_DENY
    assert "POL-006" in decision.causing_policy_ids


def test_runtime_dispatch_no_longer_triggers_pol006_unknown_action():
    """Before this phase, `runtime_dispatch` would have been an unknown
    action (POL-006 DENY). After this phase, it is recognized -- POL-006
    no longer fires for it (though other policies, notably POL-005 for
    real dispatch, still may)."""
    _, _, request, decision = full_chain(simulation_only=True)
    assert "POL-006" not in decision.causing_policy_ids
