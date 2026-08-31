"""Tests for Phase 148C.6 — Permission Broker Foundation Policy
Applicability Implementation (PBPA-001 v1.0).

Verifies the applicability layer added on top of the Phase 108A-D
Permission Broker Foundation: per-policy `applicable_execution_classes`
metadata, the policy-owned `applies_to()` predicate, registry-side
applicability filtering, `POL-004`'s scoped domain, construction-time
registry validation (missing/duplicate canonical policy ids), predicate-
failure fail-closed handling, and the additive
`applicable_policy_ids`/`non_applicable_policy_ids` explainability
fields. No subprocess invocation in this file; pure in-process,
pytest-xdist safe.

Does not modify any Phase 108A-D test file — those are re-run unmodified
(save for the specific PBPA-driven call-site updates documented in
Phase 148C.6's final report) as the backward-compatibility check.
"""

from __future__ import annotations

import pytest

from pcae.core.permission_broker_foundation import (
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    DEFAULT_POLICY_RULES,
    EXECUTION_CLASS_ADAPTER,
    EXECUTION_CLASS_BACKEND,
    EXECUTION_CLASS_MUTATION,
    EXECUTION_CLASS_NONE,
    EXECUTION_CLASS_ROLLBACK,
    EXECUTION_CLASS_SHELL,
    KNOWN_EXECUTION_CLASSES,
    POLICY_IDS,
    POLICY_IDS_CANONICAL,
    POLICY_STATUS_IMPLEMENTED,
    PermissionBroker,
    PolicyRegistry,
    PolicyResult,
    PolicyRule,
    build_permission_broker_request,
)

POL_004_APPLICABLE_CLASSES = frozenset({
    EXECUTION_CLASS_SHELL, EXECUTION_CLASS_BACKEND, EXECUTION_CLASS_ADAPTER, EXECUTION_CLASS_ROLLBACK,
})
POL_004_NON_APPLICABLE_CLASSES = frozenset(KNOWN_EXECUTION_CLASSES) - POL_004_APPLICABLE_CLASSES
UNIVERSAL_POLICY_IDS = ("POL-001", "POL-002", "POL-003", "POL-005", "POL-006", "POL-007",
                        "POL-008", "POL-009", "POL-010", "POL-011", "POL-012")


def _valid_request(**overrides):
    fields = dict(
        action_type="read",
        execution_class="none",
        requested_component="COMP-001",
        requested_capability="evaluate",
        task_id="task-1",
        evidence_available=True,
        approval_present=True,
    )
    fields.update(overrides)
    return build_permission_broker_request(**fields)


# ═══════════════════════════════════════════════════════════════════════
# 1. Complete POL-001..012 applicability matrix (Section 34)
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("policy_id", UNIVERSAL_POLICY_IDS)
@pytest.mark.parametrize("execution_class", sorted(KNOWN_EXECUTION_CLASSES))
def test_universal_policy_applicable_on_every_execution_class(policy_id, execution_class):
    rule = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == policy_id)
    request = _valid_request(execution_class=execution_class)
    assert rule.applies_to(request) is True


@pytest.mark.parametrize("execution_class", sorted(POL_004_APPLICABLE_CLASSES))
def test_pol_004_applicable_on_mediated_execution_classes(execution_class):
    rule = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == "POL-004")
    request = _valid_request(execution_class=execution_class)
    assert rule.applies_to(request) is True


@pytest.mark.parametrize("execution_class", sorted(POL_004_NON_APPLICABLE_CLASSES))
def test_pol_004_not_applicable_outside_mediated_execution_classes(execution_class):
    rule = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == "POL-004")
    request = _valid_request(execution_class=execution_class)
    assert rule.applies_to(request) is False


def test_pol_004_frozen_applicability_set_matches_contract():
    rule = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == "POL-004")
    assert rule.applicable_execution_classes == POL_004_APPLICABLE_CLASSES


@pytest.mark.parametrize("policy_id", UNIVERSAL_POLICY_IDS)
def test_universal_policy_metadata_is_none(policy_id):
    rule = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == policy_id)
    assert rule.applicable_execution_classes is None


# ═══════════════════════════════════════════════════════════════════════
# 2. POL-004 evaluation-through-broker tests (Section 33)
# ═══════════════════════════════════════════════════════════════════════


def test_pol_004_in_scope_no_approval_human_review():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="shell", approval_present=False))
    assert decision.decision == DECISION_HUMAN_REVIEW
    assert "POL-004" in decision.triggered_policy_ids
    assert "POL-004" in decision.applicable_policy_ids


def test_pol_004_in_scope_with_approval_not_triggered_but_applicable():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="shell", approval_present=True))
    assert decision.decision == DECISION_ALLOW
    assert "POL-004" in decision.applicable_policy_ids
    assert "POL-004" not in decision.triggered_policy_ids


@pytest.mark.parametrize("execution_class", ["none", "mutation"])
def test_pol_004_out_of_scope_never_triggers_never_allow_by_itself(execution_class):
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class=execution_class, approval_present=False))
    assert decision.decision == DECISION_ALLOW
    assert "POL-004" in decision.non_applicable_policy_ids
    assert "POL-004" not in decision.applicable_policy_ids
    assert "POL-004" not in decision.evaluated_policy_ids
    assert "POL-004" not in decision.triggered_policy_ids


@pytest.mark.parametrize("execution_class", ["none", "mutation"])
def test_pol_004_evidence_independence_out_of_scope(execution_class):
    """Toggling approval_present must not change POL-004's applicability
    for an out-of-scope class — applicability is resolved from
    execution_class alone, strictly before approval_present is read
    (PBPA-REQ-066/012)."""
    broker = PermissionBroker()
    for approval_present in (True, False):
        decision = broker.evaluate(
            _valid_request(execution_class=execution_class, approval_present=approval_present)
        )
        assert "POL-004" in decision.non_applicable_policy_ids


def test_pol_004_evidence_independence_in_scope():
    """Applicability for an in-scope class is identical regardless of
    approval_present — only the evaluation outcome (triggered or not)
    differs, never the applicability."""
    broker = PermissionBroker()
    for approval_present in (True, False):
        decision = broker.evaluate(
            _valid_request(execution_class="shell", approval_present=approval_present)
        )
        assert "POL-004" in decision.applicable_policy_ids
        assert "POL-004" not in decision.non_applicable_policy_ids


# ═══════════════════════════════════════════════════════════════════════
# 3. execution_class validation / anti-spoofing (Section 32/35)
# ═══════════════════════════════════════════════════════════════════════


def test_unknown_execution_class_denied_via_pol_006_regardless_of_applicability():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="quantum"))
    assert decision.decision == DECISION_DENY
    assert "POL-006" in decision.triggered_policy_ids


def test_unknown_execution_class_cannot_produce_weaker_decision_via_pol_004():
    """An unknown class cannot smuggle a weaker decision through POL-004
    applicability -- POL-006's universal DENY always wins regardless of
    what any scoped rule's predicate resolves to for that class."""
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="quantum", approval_present=False))
    assert decision.decision == DECISION_DENY


def test_simulation_only_cannot_weaken_pol_004_applicability():
    """Toggling simulation_only must have zero effect on which policies
    are applicable -- PBPA-REQ-068/069."""
    broker = PermissionBroker()
    for simulation_only in (True, False):
        decision = broker.evaluate(
            _valid_request(execution_class="shell", approval_present=False, simulation_only=simulation_only)
        )
        assert "POL-004" in decision.applicable_policy_ids


def test_simulation_only_cannot_weaken_applicability_for_mutation_class():
    broker = PermissionBroker()
    for simulation_only in (True, False):
        decision = broker.evaluate(
            _valid_request(execution_class="mutation", approval_present=False, simulation_only=simulation_only)
        )
        assert "POL-004" in decision.non_applicable_policy_ids


def test_future_unsupported_execution_class_leaves_pol_004_non_applicable_by_default():
    """A hypothetical future execution_class value, not yet a member of
    KNOWN_EXECUTION_CLASSES, is unknown to POL-006 (DENY) and, if that
    check were somehow bypassed, would also not be a member of POL-004's
    frozen applicability set -- two independent fail-closed layers."""
    rule = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == "POL-004")
    request = _valid_request(execution_class="future_class_not_yet_defined")
    assert rule.applies_to(request) is False


def test_direct_foundation_invocation_with_weak_claimed_class_still_scoped_by_frozen_metadata():
    """A caller invoking the Foundation directly (bypassing any adapter)
    and simply asserting a weaker execution_class gets exactly the
    applicability that class implies -- there is no separate, stronger
    'real' classification the broker could fall back to (Section 9's
    documented, inherited trust-boundary limitation); this test proves
    the mechanism is at least internally consistent, not a new gap."""
    broker = PermissionBroker()
    weak_claim = broker.evaluate(_valid_request(execution_class="none", approval_present=False))
    honest_claim = broker.evaluate(_valid_request(execution_class="shell", approval_present=False))
    assert weak_claim.decision == DECISION_ALLOW
    assert honest_claim.decision == DECISION_HUMAN_REVIEW


# ═══════════════════════════════════════════════════════════════════════
# 4. Registry validation: missing / duplicate canonical policy (Section 18)
# ═══════════════════════════════════════════════════════════════════════


def test_registry_construction_succeeds_with_default_rules():
    registry = PolicyRegistry()
    assert set(registry.policy_ids) == POLICY_IDS_CANONICAL


def test_registry_rejects_missing_canonical_policy():
    incomplete = tuple(r for r in DEFAULT_POLICY_RULES if r.policy_id != "POL-004")
    with pytest.raises(ValueError, match="missing canonical policy"):
        PolicyRegistry(rules=incomplete)


def test_registry_rejects_missing_canonical_policy_message_names_the_id():
    incomplete = tuple(r for r in DEFAULT_POLICY_RULES if r.policy_id != "POL-004")
    with pytest.raises(ValueError, match=r"POL-004"):
        PolicyRegistry(rules=incomplete)


def test_registry_rejects_duplicate_policy_id():
    from pcae.core.permission_broker_foundation import MissingActiveTaskRule
    duplicated = DEFAULT_POLICY_RULES + (MissingActiveTaskRule(),)
    with pytest.raises(ValueError, match="duplicate policy_id"):
        PolicyRegistry(rules=duplicated)


def test_registry_accepts_superset_with_extra_non_canonical_rule():
    """A registry containing every canonical id plus one extra,
    non-canonical rule remains valid — completeness is a subset
    requirement, not an exact-match requirement."""

    class ExtraRule(PolicyRule):
        policy_id = "POL-014"  # POL-013 is now canonical (Phase ...1R.22)
        name = "Extra"
        implementation_status = POLICY_STATUS_IMPLEMENTED

        def evaluate(self, request):
            return PolicyResult(policy_id=self.policy_id, triggered=False)

    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (ExtraRule(),))
    assert len(registry.policy_ids) == 14


def test_no_valid_allow_when_required_policy_missing():
    """Missing policy is a construction-time defect, not a request-time
    NOT_APPLICABLE -- confirmed by construction itself never succeeding,
    so no request can ever be evaluated against an incomplete registry."""
    incomplete = tuple(r for r in DEFAULT_POLICY_RULES if r.policy_id != "POL-001")
    with pytest.raises(ValueError):
        PolicyRegistry(rules=incomplete)


# ═══════════════════════════════════════════════════════════════════════
# 5. Predicate failure fails closed (Section 34/38)
# ═══════════════════════════════════════════════════════════════════════


def test_applicability_predicate_failure_fails_closed_to_deny():
    class RaisesOnApplicability(PolicyRule):
        policy_id = "POL-705"
        name = "Raises On Applicability"
        implementation_status = POLICY_STATUS_IMPLEMENTED

        def applies_to(self, request):
            raise RuntimeError("cannot resolve applicability")

        def evaluate(self, request):
            return PolicyResult(policy_id=self.policy_id, triggered=False)

    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (RaisesOnApplicability(),))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_DENY
    assert decision.decision_reason == "invalid_policy_result"
    assert decision.causing_policy_id == "POL-705"


def test_applicability_predicate_failure_never_produces_not_applicable():
    """A predicate failure must not be silently converted into
    NOT_APPLICABLE -- it is sanitized as a triggered, fail-closed DENY,
    the same as an evaluate() exception."""
    class RaisesOnApplicability(PolicyRule):
        policy_id = "POL-706"
        name = "Raises On Applicability"
        implementation_status = POLICY_STATUS_IMPLEMENTED

        def applies_to(self, request):
            raise RuntimeError("boom")

        def evaluate(self, request):
            return PolicyResult(policy_id=self.policy_id, triggered=False)

    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (RaisesOnApplicability(),))
    results = registry.evaluate_all(_valid_request())
    result = next(r for r in results if r.policy_id == "POL-706")
    assert result.applicable is True
    assert result.triggered is True
    assert result.decision == DECISION_DENY


# ═══════════════════════════════════════════════════════════════════════
# 6. Empty applicable set (Section 21/30) — defense in depth
# ═══════════════════════════════════════════════════════════════════════


def test_no_currently_known_execution_class_reaches_empty_applicable_set():
    """For every currently-known execution_class, at least the six
    universal implemented/stub policies remain applicable -- an empty
    applicable set is not reachable under this implementation for any
    currently-known class."""
    broker = PermissionBroker()
    for execution_class in sorted(KNOWN_EXECUTION_CLASSES):
        decision = broker.evaluate(_valid_request(execution_class=execution_class))
        assert len(decision.applicable_policy_ids) >= len(UNIVERSAL_POLICY_IDS)


def test_compose_empty_results_still_fails_closed_defense_in_depth():
    """_compose's pre-existing empty-results branch remains the
    defense-in-depth fallback if a hypothetical future rule set ever
    produced zero results for a request -- exercised directly since no
    currently-constructible registry can reach it (registry construction
    itself would already have rejected an incomplete rule set)."""
    from pcae.core.permission_broker_foundation import _compose
    decision = _compose(())
    assert decision.decision == DECISION_DENY
    assert decision.decision_reason == "no_applicable_policy"


# ═══════════════════════════════════════════════════════════════════════
# 7. Explainability (Section 39)
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("execution_class", sorted(KNOWN_EXECUTION_CLASSES))
def test_applicable_and_non_applicable_partition_canonical_policy_ids(execution_class):
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class=execution_class))
    applicable = set(decision.applicable_policy_ids)
    non_applicable = set(decision.non_applicable_policy_ids)
    assert applicable | non_applicable == set(POLICY_IDS)
    assert applicable & non_applicable == set()


@pytest.mark.parametrize("execution_class", sorted(KNOWN_EXECUTION_CLASSES))
def test_evaluated_policy_ids_equals_applicable_policy_ids(execution_class):
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class=execution_class))
    assert decision.evaluated_policy_ids == decision.applicable_policy_ids


def test_explainability_deterministic_across_repeated_identical_requests():
    broker = PermissionBroker()
    request = _valid_request(execution_class="shell", approval_present=False)
    results = [broker.evaluate(request) for _ in range(10)]
    first = results[0]
    for r in results[1:]:
        assert r.applicable_policy_ids == first.applicable_policy_ids
        assert r.non_applicable_policy_ids == first.non_applicable_policy_ids
        assert r.evaluated_policy_ids == first.evaluated_policy_ids


def test_applicable_non_applicable_preserve_registry_order():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="none"))
    # POL-004 and POL-013 are both scoped away from execution_class=none
    # (POL-013 added Phase ...1R.22, N-16-3 — adapter-scoped).
    assert decision.applicable_policy_ids == tuple(
        p for p in POLICY_IDS if p not in ("POL-004", "POL-013")
    )
    assert decision.non_applicable_policy_ids == ("POL-004", "POL-013")


def test_not_applicable_never_treated_as_allow():
    """A non-applicable POL-004 must never itself contribute an ALLOW
    signal -- ALLOW here comes only from the composition default (nothing
    triggered), never from a synthesized "applicable and passed" state."""
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="none", approval_present=False))
    assert decision.decision == DECISION_ALLOW
    assert decision.decision_reason == "policy_would_allow_if_execution_existed"
    assert decision.causing_policy_id is None


# ═══════════════════════════════════════════════════════════════════════
# 8. Backward compatibility: real production consumer shapes (Section 3)
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("requested_capability", [
    "pcae_health", "pcae_doctor_task_memory", "pcae_check", "pcae_push_check",
])
def test_real_production_consumer_shapes_unaffected(requested_capability):
    """The four real production call sites (health.py:23, task.py:1406,
    check.py:23, push.py:304) all use action_type="read",
    execution_class="none", approval_present=True, evidence_available=True
    -- every one of the twelve policy results for these shapes is
    unchanged by this implementation."""
    broker = PermissionBroker()
    decision = broker.evaluate(build_permission_broker_request(
        action_type="read",
        execution_class="none",
        requested_component="COMP-001",
        requested_capability=requested_capability,
        task_id="task-1",
        evidence_available=True,
        approval_present=True,
        simulation_only=True,
    ))
    assert decision.decision == DECISION_ALLOW
    assert "POL-004" in decision.non_applicable_policy_ids


def test_legacy_call_site_without_execution_class_awareness_gets_no_weaker_policy_set():
    """A caller supplying the pre-PBPA-typical execution_class="none"
    combined with approval_present=False (a value no real production
    caller sets, but a plausible future/legacy caller) is not silently
    forced through POL-004 -- it correctly reflects non_applicable, and
    every universal policy remains applicable exactly as before this
    phase."""
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="none", approval_present=False))
    for policy_id in UNIVERSAL_POLICY_IDS:
        assert policy_id in decision.applicable_policy_ids
