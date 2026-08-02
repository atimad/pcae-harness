"""Phase 148C.7 — Permission Broker Foundation Policy Applicability
Independent Implementation Verification.

Independent adversarial tests against the PBPA-001 v1.0 applicability
layer implemented by Phase 148C.6. Written fresh against PBPA-001 and
the production source directly, not copied from
`tests/test_permission_broker_policy_applicability.py` (148C.6's own
test suite) — deliberately overlapping in target behavior (an
independent verifier is expected to re-derive and re-attack the same
surface, not avoid it), but exercised through different code paths and
scenario constructions where practical. Adds no production behavior;
modifies no file under `src/pcae/**`.

Does not close Finding B-1. Test 4 below (`test_b1_causal_mechanism_...`)
empirically re-confirms the B-1 causal chain's current state; it is an
observation, not a closure — B-1 formally remains OPEN (Section 38 of
PBPA-001; Section 8.1 of PBPC-001 v1.1) until a dedicated PBPC/B-1
re-evaluation phase (148C.8) independently rules on closure.
"""

from __future__ import annotations

import pytest

from pcae.core.permission_broker_foundation import (
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    DEFAULT_POLICY_RULES,
    EXECUTION_CLASS_MUTATION,
    EXECUTION_CLASS_NONE,
    EXECUTION_CLASS_SHELL,
    MissingHumanApprovalRule,
    PermissionBroker,
    PolicyRegistry,
    PolicyResult,
    PolicyRule,
    build_permission_broker_request,
)


def _req(**overrides):
    fields = dict(
        action_type="read",
        execution_class="none",
        requested_component="COMP-001",
        requested_capability="phase-148c7-verification",
        task_id="task-1",
        evidence_available=True,
        approval_present=True,
    )
    fields.update(overrides)
    return build_permission_broker_request(**fields)


# ── 1. Predicate-failure fail-closed (independent construction) ──────────


def test_applicability_predicate_exception_fails_closed_to_deny():
    class ExplodingPredicateRule(PolicyRule):
        policy_id = "POL-EXPLODE-148C7"

        def applies_to(self, request):
            raise RuntimeError("simulated predicate failure")

        def evaluate(self, request):
            return PolicyResult(policy_id=self.policy_id, triggered=False)

    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (ExplodingPredicateRule(),))
    decision = PermissionBroker(registry=registry).evaluate(_req())
    assert decision.decision == DECISION_DENY
    # Must never silently resolve to NOT_APPLICABLE-and-skip: a predicate
    # failure is sanitized as an applicable-but-failed (fail-closed DENY)
    # result, never as a silently-skipped non-applicable policy.
    assert "POL-EXPLODE-148C7" not in decision.non_applicable_policy_ids
    assert "POL-EXPLODE-148C7" in decision.applicable_policy_ids


# ── 2. Registry construction-time attacks ─────────────────────────────────


def test_missing_required_universal_policy_fails_closed_at_construction():
    incomplete = tuple(r for r in DEFAULT_POLICY_RULES if r.policy_id != "POL-001")
    with pytest.raises(ValueError):
        PolicyRegistry(rules=incomplete)


def test_missing_pol_004_specifically_fails_closed_at_construction():
    incomplete = tuple(r for r in DEFAULT_POLICY_RULES if r.policy_id != "POL-004")
    with pytest.raises(ValueError):
        PolicyRegistry(rules=incomplete)


def test_duplicate_pol_004_different_object_same_id_rejected():
    dup = DEFAULT_POLICY_RULES + (MissingHumanApprovalRule(),)
    with pytest.raises(ValueError):
        PolicyRegistry(rules=dup)


# ── 3. Class spoofing / trust boundary (empirical, direct invocation) ────


def test_shell_operation_mislabeled_as_none_yields_allow_per_contract_trust_model():
    """PBPA-001 explicitly places classification-authenticity responsibility
    at the integration-point contract, not the Foundation (PBPA-REQ-032).
    A caller supplying a false `execution_class` DOES change the applicable
    set -- this is accepted, contract-documented behavior, not a defect:
    the Foundation cannot and does not independently re-derive
    `execution_class` from `action_type`. This test records that boundary
    empirically rather than asserting a stronger (unauthorized) model."""
    spoofed = _req(action_type="shell_command", execution_class=EXECUTION_CLASS_NONE, approval_present=False)
    decision = PermissionBroker().evaluate(spoofed)
    assert decision.decision == DECISION_ALLOW
    assert "POL-004" in decision.non_applicable_policy_ids


def test_unknown_execution_class_always_denies_regardless_of_pol_004_applicability():
    unknown = _req(execution_class="not_a_real_execution_class", approval_present=True)
    decision = PermissionBroker().evaluate(unknown)
    assert decision.decision == DECISION_DENY
    assert decision.causing_policy_ids == ("POL-006",)


# ── 4. B-1 causal-mechanism re-observation (does not close B-1) ──────────


def test_b1_causal_mechanism_reobservation_push_shaped_request():
    """Empirically re-observes whether the original B-1 cause (POL-004
    evaluating unconditionally on every request, including a `pcae push`
    -shaped one with `execution_class=mutation`) still occurs after the
    PBPA-001 applicability implementation. It no longer occurs: POL-004
    is NOT_APPLICABLE to `execution_class=mutation`
    (PBPA-REQ-063/PBPC-REQ-034). This does NOT close B-1 -- B-1 closure
    requires a dedicated PBPC-001 v1.2 re-evaluation (148C.8), per
    PBPA-001 Section 38 and PBPC-001 Section 8.1."""
    push_shaped = build_permission_broker_request(
        action_type="push",
        execution_class=EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_push",
        task_id="task-1",
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    decision = PermissionBroker().evaluate(push_shaped)
    assert "POL-004" in decision.non_applicable_policy_ids
    assert "POL-004" not in decision.applicable_policy_ids
    assert decision.decision == DECISION_ALLOW


# ── 5. Determinism and decision vocabulary ────────────────────────────────


def test_determinism_across_repeated_evaluation_of_identical_request():
    request = _req(execution_class=EXECUTION_CLASS_SHELL, approval_present=False)
    signatures = {
        (
            d.decision,
            d.applicable_policy_ids,
            d.non_applicable_policy_ids,
            d.causing_policy_ids,
        )
        for d in (PermissionBroker().evaluate(request) for _ in range(5))
    }
    assert len(signatures) == 1


def test_decision_vocabulary_still_exactly_three_values():
    from pcae.core.permission_broker_foundation import DECISION_VALUES
    assert set(DECISION_VALUES) == {DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW}


def test_mixed_deny_and_human_review_precedence_deny_wins():
    request = _req(
        action_type="shell_command",
        execution_class=EXECUTION_CLASS_SHELL,
        requested_component="COMP-999-UNKNOWN",  # POL-007 DENY
        approval_present=False,  # POL-004 HUMAN_REVIEW, in-scope for shell
    )
    decision = PermissionBroker().evaluate(request)
    assert decision.decision == DECISION_DENY
    assert "POL-007" in decision.causing_policy_ids
    assert "POL-004" not in decision.causing_policy_ids


# ── 6. simulation_only cannot influence applicability ─────────────────────


def test_simulation_only_does_not_change_applicable_set():
    common = dict(
        action_type="push",
        execution_class=EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="x",
        task_id="t",
        evidence_available=True,
        approval_present=False,
    )
    d_sim = PermissionBroker().evaluate(build_permission_broker_request(simulation_only=True, **common))
    d_real = PermissionBroker().evaluate(build_permission_broker_request(simulation_only=False, **common))
    assert d_sim.applicable_policy_ids == d_real.applicable_policy_ids
    assert d_sim.non_applicable_policy_ids == d_real.non_applicable_policy_ids
    # Evaluation outcome legitimately differs (POL-005), applicability does not.
    assert d_sim.decision == DECISION_ALLOW
    assert d_real.decision == DECISION_DENY


# ── 7. Applicability metadata mutability (observation, not a caller-facing gap) ──


def test_applicable_execution_classes_value_is_a_true_frozenset():
    pol004 = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == "POL-004")
    with pytest.raises(AttributeError):
        pol004.applicable_execution_classes.add(EXECUTION_CLASS_MUTATION)  # type: ignore[union-attr]


def test_no_caller_exclusion_parameter_exists_on_broker_or_registry():
    import inspect

    broker_evaluate_params = inspect.signature(PermissionBroker.evaluate).parameters
    registry_init_params = inspect.signature(PolicyRegistry.__init__).parameters
    for params in (broker_evaluate_params, registry_init_params):
        assert not any("exclude" in p.lower() or "skip" in p.lower() for p in params)
