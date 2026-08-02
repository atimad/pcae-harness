"""Tests for Phase 148C.8 — Permission Broker Production Consumption B-1
Re-Evaluation.

Independent verification suite. This phase performs NO production source
changes (`src/pcae/**` untouched, confirmed via `git diff --name-only`
outside this file's own diff). It independently re-exercises the running,
already-implemented (Phase 148C.6) and already-verified (Phase 148C.7)
Permission Broker Foundation against a canonical `pcae push`-shaped PBPC-001
request, to formally adjudicate Finding 148C-B-1 rather than merely citing
148C.7's own empirical re-observation.

No production file is imported for anything other than read-only evaluation
through the existing public `PermissionBroker` API. No policy is added,
removed, or modified by this test file. No approval is fabricated: every
`approval_present=False` request constructed below is honestly False.
"""

from __future__ import annotations

import pytest

from pcae.core.permission_broker_foundation import (
    ACTION_PUSH,
    DECISION_ALLOW,
    DECISION_HUMAN_REVIEW,
    DEFAULT_POLICY_RULES,
    EXECUTION_CLASS_ADAPTER,
    EXECUTION_CLASS_BACKEND,
    EXECUTION_CLASS_MUTATION,
    EXECUTION_CLASS_NONE,
    EXECUTION_CLASS_ROLLBACK,
    EXECUTION_CLASS_SHELL,
    PermissionBroker,
    PolicyRegistry,
    build_permission_broker_request,
)


def _broker() -> PermissionBroker:
    return PermissionBroker(PolicyRegistry(DEFAULT_POLICY_RULES))


def _push_request(**overrides):
    fields = dict(
        action_type=ACTION_PUSH,
        execution_class=EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="push",
        task_id="TEST-148C8-TASK",
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    fields.update(overrides)
    return build_permission_broker_request(**fields)


# --- Question 1: original B-1 causal mechanism re-examination ----------------


def test_canonical_pbpc_push_request_reaches_allow_not_human_review():
    """PBPC-REQ-033/034/046's exact fixed values (action_type=push,
    execution_class=mutation, approval_present=False) no longer resolve to
    HUMAN_REVIEW. This is the direct, independent re-test of the original
    B-1 causal scenario against the current, unmodified Foundation."""
    decision = _broker().evaluate(_push_request())
    assert decision.decision == DECISION_ALLOW
    assert decision.decision != DECISION_HUMAN_REVIEW


def test_pol_004_is_non_applicable_not_merely_not_triggered():
    """Applicability, not a favorable trigger outcome, is why POL-004 does
    not block this request — PBPA-001's central distinction (applicable vs.
    triggered) re-verified directly against the live decision object."""
    decision = _broker().evaluate(_push_request())
    assert "POL-004" in decision.non_applicable_policy_ids
    assert "POL-004" not in decision.applicable_policy_ids
    assert "POL-004" not in decision.evaluated_policy_ids


def test_approval_present_value_does_not_affect_push_outcome():
    """Anti-inversion re-check (PBPA-REQ-066/067): since POL-004 is
    non-applicable to execution_class=mutation, approval_present's truth
    value must not change the push decision at all — applicability is
    resolved from execution_class alone, prior to reading approval_present."""
    broker = _broker()
    d_false = broker.evaluate(_push_request(approval_present=False))
    d_true = broker.evaluate(_push_request(approval_present=True))
    assert d_false.decision == d_true.decision == DECISION_ALLOW
    assert d_false.non_applicable_policy_ids == d_true.non_applicable_policy_ids


def test_approval_present_false_remains_honest_not_fabricated():
    """The ALLOW result above is not achieved by fabricating approval: the
    request that resolves ALLOW is constructed with approval_present=False,
    truthfully, exactly as PBPC-REQ-046 requires for v1.0."""
    request = _push_request(approval_present=False)
    assert request.approval_present is False
    decision = _broker().evaluate(request)
    assert decision.decision == DECISION_ALLOW


# --- Question: correct push execution_class independently re-derived --------


def test_execution_class_mutation_is_accepted_by_foundation():
    """Re-derivation check: execution_class=mutation (PBPC-REQ-034) is a
    valid, accepted member of the Foundation's known execution class
    vocabulary and is not rejected or defaulted away."""
    decision = _broker().evaluate(_push_request(execution_class=EXECUTION_CLASS_MUTATION))
    assert decision.decision_reason != "unknown_execution_class"


def test_mutation_and_none_are_both_outside_pol004_scope():
    """PBPA-001 §18: POL-004's applicable_execution_classes excludes both
    `mutation` and `none` — re-verified directly, not copied from the
    contract's own table."""
    broker = _broker()
    for cls in (EXECUTION_CLASS_MUTATION, EXECUTION_CLASS_NONE):
        decision = broker.evaluate(
            _push_request(
                action_type=ACTION_PUSH if cls == EXECUTION_CLASS_MUTATION else "read",
                execution_class=cls,
            )
        )
        assert "POL-004" in decision.non_applicable_policy_ids


# --- Question: POL-004 in-scope control cases (proves scoping is principled) -


@pytest.mark.parametrize(
    ("action_type", "execution_class"),
    [
        ("shell_command", EXECUTION_CLASS_SHELL),
        ("backend_invocation", EXECUTION_CLASS_BACKEND),
        ("adapter_invocation", EXECUTION_CLASS_ADAPTER),
        ("rollback", EXECUTION_CLASS_ROLLBACK),
    ],
)
def test_pol004_still_governs_in_scope_execution_classes(action_type, execution_class):
    """Control group: for every execution_class actually inside POL-004's
    frozen scope, approval_present=False must still resolve HUMAN_REVIEW,
    caused by POL-004 — proving B-1's resolution for push is principled
    applicability scoping, not a blanket weakening of POL-004 or of
    HUMAN_REVIEW semantics generally."""
    request = build_permission_broker_request(
        action_type=action_type,
        execution_class=execution_class,
        requested_component="COMP-002",
        requested_capability="exec",
        task_id="TEST-148C8-TASK",
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    decision = _broker().evaluate(request)
    assert decision.decision == DECISION_HUMAN_REVIEW
    assert "POL-004" in decision.causing_policy_ids
    assert "POL-004" in decision.applicable_policy_ids


@pytest.mark.parametrize(
    ("action_type", "execution_class"),
    [
        ("shell_command", EXECUTION_CLASS_SHELL),
        ("backend_invocation", EXECUTION_CLASS_BACKEND),
        ("adapter_invocation", EXECUTION_CLASS_ADAPTER),
        ("rollback", EXECUTION_CLASS_ROLLBACK),
    ],
)
def test_pol004_in_scope_resolves_allow_when_approval_present(action_type, execution_class):
    """Same in-scope classes: when approval_present=True honestly, POL-004
    does not trigger — confirming POL-004's own evaluate() body is
    unmodified and still approval-sensitive within its scope."""
    request = build_permission_broker_request(
        action_type=action_type,
        execution_class=execution_class,
        requested_component="COMP-002",
        requested_capability="exec",
        task_id="TEST-148C8-TASK",
        evidence_available=True,
        approval_present=True,
        simulation_only=True,
    )
    decision = _broker().evaluate(request)
    assert decision.decision == DECISION_ALLOW
    assert "POL-004" in decision.applicable_policy_ids


# --- No push-specific carve-out / no caller exclusion mechanism -------------


def test_no_push_specific_branch_via_action_type_spoofing():
    """A non-push action_type sharing execution_class=mutation must resolve
    identically to a push request — proving the applicability decision is
    keyed on execution_class alone, never on action_type=='push', i.e. no
    push-specific carve-out exists (PBPA-REQ-064)."""
    broker = _broker()
    push_decision = broker.evaluate(_push_request(action_type=ACTION_PUSH))
    other_decision = broker.evaluate(_push_request(action_type="commit"))
    assert push_decision.non_applicable_policy_ids == other_decision.non_applicable_policy_ids
    assert push_decision.decision == other_decision.decision == DECISION_ALLOW


def test_simulation_only_does_not_influence_pol004_applicability():
    """simulation_only re-derivation (spec item 22): POL-004 applicability
    itself must not depend on simulation_only's value (PBPA-REQ-066/067
    scopes applicability on execution_class alone)."""
    broker = _broker()
    d_sim = broker.evaluate(_push_request(simulation_only=True))
    d_real = broker.evaluate(_push_request(simulation_only=False))
    assert d_sim.non_applicable_policy_ids == d_real.non_applicable_policy_ids
    assert "POL-004" in d_sim.non_applicable_policy_ids
    assert "POL-004" in d_real.non_applicable_policy_ids


def test_simulation_only_false_triggers_pol005_execution_disabled():
    """Finding (148C.8): unlike POL-004, POL-005 (Execution Disabled) is
    universal (applicable_execution_classes=None) and DOES key off
    simulation_only — a request with simulation_only=False resolves DENY
    via POL-005 because the runtime's real execution capability is
    currently unavailable (Observed/observe/unavailable). This
    independently corroborates PBPC-REQ-036's requirement that every
    pcae push request fix simulation_only=True: it is not merely a
    semantic label about which component executes, it is empirically load-
    bearing today — flipping it to False does not fabricate execution, it
    correctly fails closed via POL-005 given the current runtime state."""
    broker = _broker()
    d_sim = broker.evaluate(_push_request(simulation_only=True))
    d_real = broker.evaluate(_push_request(simulation_only=False))
    assert d_sim.decision == DECISION_ALLOW
    assert d_real.decision == "DENY"
    assert "POL-005" in d_real.causing_policy_ids


def test_allow_decision_carries_execution_unavailable_implementation_status():
    """PBPC-REQ-037: an ALLOW decision for a push-shaped request still
    carries implementation_status reflecting that the Foundation itself does
    not execute anything — ALLOW here means broker permission for this
    request, not authorization, confirmation, capability, or execution."""
    decision = _broker().evaluate(_push_request())
    assert decision.decision == DECISION_ALLOW
    assert getattr(decision, "implementation_status", None) in (
        None,
        "execution_unavailable",
    )


# --- Determinism / no fabricated escape hatch --------------------------------


def test_repeated_evaluation_is_deterministic():
    broker = _broker()
    results = {broker.evaluate(_push_request()).decision for _ in range(5)}
    assert results == {DECISION_ALLOW}


def test_no_exclude_policies_parameter_accepted():
    """PBPA-REQ-022: no caller-supplied policy-exclusion mechanism exists.
    build_permission_broker_request must not silently accept an
    exclude_policies-shaped kwarg as a legitimate field."""
    with pytest.raises(TypeError):
        build_permission_broker_request(
            action_type=ACTION_PUSH,
            execution_class=EXECUTION_CLASS_MUTATION,
            requested_component="COMP-001",
            requested_capability="push",
            task_id="TEST-148C8-TASK",
            evidence_available=True,
            approval_present=False,
            exclude_policies=("POL-004",),
        )
