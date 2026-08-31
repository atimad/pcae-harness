"""Tests for Phase 108B — Permission Broker Policy Rule Framework.

Verifies the extensible policy rule framework introduced on top of the
Phase 108A Permission Broker foundation: the PolicyRule interface, the
PolicyRegistry, decision composition (DENY > HUMAN_REVIEW > ALLOW,
fail-closed), stable POL-NNN identifiers, and explainability (the
decision names exactly which policy caused it). No subprocess
invocation in this file; pure in-process, pytest-xdist safe.

This file intentionally does not modify or duplicate
tests/test_permission_broker_foundation.py (Phase 108A) — that suite is
re-run unmodified against the refactored implementation as the
backward-compatibility check.
"""

from __future__ import annotations

import inspect

import pytest

from pcae.core.permission_broker_foundation import (
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    DEFAULT_POLICY_RULES,
    POLICY_IDS,
    POLICY_STATUS_IMPLEMENTED,
    POLICY_STATUS_NOT_IMPLEMENTED,
    PermissionBroker,
    PolicyRegistry,
    PolicyResult,
    PolicyRule,
    StubPolicyRule,
    build_permission_broker_request,
)

EXPECTED_POLICY_NAMES = {
    "POL-001": "Missing Active Task",
    "POL-002": "Task Outside Scope",
    "POL-003": "Missing Evidence",
    "POL-004": "Missing Human Approval",
    "POL-005": "Execution Disabled",
    "POL-006": "Unknown Capability",
    "POL-007": "Unknown Component",
    "POL-008": "Emergency Stop Active",
    "POL-009": "Audit Unavailable",
    "POL-010": "Rollback Unavailable",
    "POL-011": "Unknown Backend",
    "POL-012": "Unknown Adapter",
}

IMPLEMENTED_POLICY_IDS = {"POL-001", "POL-003", "POL-004", "POL-005", "POL-006", "POL-007"}
STUB_POLICY_IDS = set(EXPECTED_POLICY_NAMES) - IMPLEMENTED_POLICY_IDS


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


# --- policy registry existence -------------------------------------------------


def test_policy_registry_class_exists():
    assert PolicyRegistry is not None


def test_default_registry_constructs_with_no_args():
    registry = PolicyRegistry()
    assert registry.policy_ids == POLICY_IDS


def test_registry_has_twelve_policies():
    # Phase ...1R.22 (N-16-3) added POL-013 (Narrow Local-CLI Dispatch
    # Eligibility, NarrowLocalCliDispatchEligibilityRule) as the thirteenth
    # canonical policy — the conjunctive companion to POL-005's
    # RUNTIME_DISPATCH_LOCAL_CLI_V1 carve-out (PBNDE-001 v1.0 §4, PBPA-001
    # v1.1). No policy was removed or renumbered; POL-001..012 are byte-stable.
    # This is an exact freeze at the current canonical cardinality, not a
    # permissive minimum — see .1R.22R reconciliation.
    assert len(DEFAULT_POLICY_RULES) == 13
    assert len(POLICY_IDS) == 13


@pytest.mark.parametrize("policy_id,name", list(EXPECTED_POLICY_NAMES.items()))
def test_policy_id_registered_with_expected_name(policy_id, name):
    rule = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == policy_id)
    assert rule.name == name


def test_policy_ids_are_stable_and_ordered():
    # Exact canonical identifier set POL-001..POL-013 (POL-013 added by
    # Phase ...1R.22, N-16-3). Range end is 14 == 13 canonical ids + 1.
    assert POLICY_IDS == tuple(f"POL-{n:03d}" for n in range(1, 14))
    # No duplicate, no gap, POL-013 is the last and is the narrow-dispatch
    # eligibility rule.
    assert len(set(POLICY_IDS)) == len(POLICY_IDS)
    assert POLICY_IDS[-1] == "POL-013"
    pol_013 = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == "POL-013")
    assert pol_013.name == "Narrow Local-CLI Dispatch Eligibility"
    assert type(pol_013).__name__ == "NarrowLocalCliDispatchEligibilityRule"


# --- policy interface -----------------------------------------------------------


def test_policy_rule_base_class_exists():
    assert PolicyRule is not None


def test_policy_result_model_exists():
    assert PolicyResult is not None


def test_policy_rule_base_class_evaluate_not_implemented():
    rule = PolicyRule()
    with pytest.raises(NotImplementedError):
        rule.evaluate(_valid_request())


def test_all_default_rules_are_policy_rule_instances():
    for rule in DEFAULT_POLICY_RULES:
        assert isinstance(rule, PolicyRule)


def test_all_default_rules_have_evaluate_method():
    for rule in DEFAULT_POLICY_RULES:
        assert callable(rule.evaluate)


def test_policy_result_has_required_fields():
    fields = set(PolicyResult.__dataclass_fields__)
    for expected in (
        "policy_id", "triggered", "decision", "decision_reason",
        "matched_no_go_ids", "matched_invariants", "matched_component_ids",
        "required_remediation", "requires_human", "simulation_only",
    ):
        assert expected in fields


@pytest.mark.parametrize("policy_id", sorted(IMPLEMENTED_POLICY_IDS))
def test_implemented_rules_marked_implemented(policy_id):
    rule = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == policy_id)
    assert rule.implementation_status == POLICY_STATUS_IMPLEMENTED


@pytest.mark.parametrize("policy_id", sorted(STUB_POLICY_IDS))
def test_stub_rules_marked_not_implemented(policy_id):
    rule = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == policy_id)
    assert rule.implementation_status == POLICY_STATUS_NOT_IMPLEMENTED
    assert isinstance(rule, StubPolicyRule)


# --- individual policy evaluation ------------------------------------------------


def test_individual_rule_evaluates_independently():
    from pcae.core.permission_broker_foundation import MissingActiveTaskRule
    rule = MissingActiveTaskRule()
    result = rule.evaluate(_valid_request(task_id=None))
    assert result.triggered is True
    assert result.policy_id == "POL-001"
    assert result.decision == DECISION_DENY


def test_individual_rule_not_triggered_when_condition_absent():
    from pcae.core.permission_broker_foundation import MissingActiveTaskRule
    rule = MissingActiveTaskRule()
    result = rule.evaluate(_valid_request())
    assert result.triggered is False


def test_stub_rule_never_triggers():
    rule = StubPolicyRule("POL-999", "Test Stub")
    for overrides in [{}, {"task_id": None}, {"evidence_available": False}, {"simulation_only": False}]:
        result = rule.evaluate(_valid_request(**overrides))
        assert result.triggered is False


def test_rules_do_not_know_about_one_another():
    """A single rule's evaluate() must not require or reference other
    rules' results — verified structurally: it takes only `request`."""
    for rule in DEFAULT_POLICY_RULES:
        sig = inspect.signature(rule.evaluate)
        assert list(sig.parameters) == ["request"]


# --- multiple policies evaluated -------------------------------------------------


def test_registry_evaluates_all_rules_every_time():
    registry = PolicyRegistry()
    results = registry.evaluate_all(_valid_request())
    # 13 since Phase ...1R.22 (POL-013 added). evaluate_all is unfiltered —
    # it runs every registered rule regardless of applicability.
    assert len(results) == 13
    assert {r.policy_id for r in results} == set(POLICY_IDS)


def test_registry_evaluates_all_rules_even_when_one_triggers():
    """Rules are never short-circuited: even when POL-001 triggers, all
    13 policies still evaluate (POL-013 added by Phase ...1R.22)."""
    registry = PolicyRegistry()
    results = registry.evaluate_all(_valid_request(task_id=None))
    assert len(results) == 13
    triggered = [r for r in results if r.triggered]
    assert len(triggered) == 1
    assert triggered[0].policy_id == "POL-001"


def test_broker_evaluated_policy_ids_equal_applicable_policy_set():
    """Phase 148C.6 (PBPA-001 PBPA-REQ-081): superseded, not merely
    updated. `evaluated_policy_ids` is redefined by this contract to mean
    "every policy actually passed to evaluate()" — i.e. exactly the
    applicable set for this request's execution_class, not
    unconditionally the whole registry.

    Phase ...1R.22 (N-16-3) added POL-013, scoped to
    ``frozenset({EXECUTION_CLASS_ADAPTER})`` (PBPA-001 v1.1), so POL-013 is
    non-applicable for the ``shell`` and ``none`` classes exercised here:
    the expected evaluated set for ``shell`` is POLICY_IDS minus POL-013,
    and for ``none`` it is POLICY_IDS minus {POL-004, POL-013}. The exact
    finite exclusion is asserted (no wildcard) — see .1R.22R."""
    broker = PermissionBroker()
    for overrides in [
        {"execution_class": "shell"},
        {"execution_class": "shell", "task_id": None},
        {"execution_class": "shell", "approval_present": False},
        {"execution_class": "shell", "simulation_only": False},
    ]:
        decision = broker.evaluate(_valid_request(**overrides))
        assert decision.evaluated_policy_ids == tuple(
            p for p in POLICY_IDS if p != "POL-013"
        )
        assert "POL-013" in decision.non_applicable_policy_ids

    for overrides in [{}, {"task_id": None}, {"approval_present": False}, {"simulation_only": False}]:
        decision = broker.evaluate(_valid_request(**overrides))
        assert decision.evaluated_policy_ids == tuple(
            p for p in POLICY_IDS if p not in ("POL-004", "POL-013")
        )
        assert "POL-004" in decision.non_applicable_policy_ids
        assert "POL-013" in decision.non_applicable_policy_ids


def test_broker_evaluated_policy_ids_partition_matches_applicable_non_applicable():
    """`applicable_policy_ids` and `non_applicable_policy_ids` partition
    the canonical POLICY_IDS exactly, for both an in-scope and an
    out-of-scope execution_class."""
    broker = PermissionBroker()
    for execution_class in ("shell", "none", "mutation", "backend", "adapter", "rollback"):
        decision = broker.evaluate(_valid_request(execution_class=execution_class))
        assert set(decision.applicable_policy_ids) | set(decision.non_applicable_policy_ids) == set(POLICY_IDS)
        assert set(decision.applicable_policy_ids) & set(decision.non_applicable_policy_ids) == set()
        assert decision.evaluated_policy_ids == decision.applicable_policy_ids


# --- decision composition and precedence -----------------------------------------


def test_deny_precedence_over_human_review():
    """When both a DENY-triggering and a HUMAN_REVIEW-triggering policy
    fire simultaneously, DENY wins."""
    broker = PermissionBroker()
    request = _valid_request(execution_class="shell", evidence_available=False, approval_present=False)
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_DENY
    assert decision.causing_policy_id == "POL-003"
    assert "POL-004" in decision.triggered_policy_ids


def test_human_review_precedence_over_allow():
    """When only a HUMAN_REVIEW-triggering policy fires, it wins over the
    implicit ALLOW default."""
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="shell", approval_present=False))
    assert decision.decision == DECISION_HUMAN_REVIEW
    assert decision.causing_policy_id == "POL-004"


def test_allow_precedence_when_nothing_triggers():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_ALLOW
    assert decision.causing_policy_id is None
    assert decision.triggered_policy_ids == ()


def test_composition_picks_first_deny_in_registry_order():
    """Two simultaneously-triggered DENY policies: the one earlier in
    registry (POL-NNN) order determines the outcome."""
    broker = PermissionBroker()
    # task missing (POL-001) AND unknown action type (POL-006) both true.
    request = _valid_request(task_id=None, action_type="nonexistent")
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_DENY
    assert decision.causing_policy_id == "POL-001"
    assert set(decision.triggered_policy_ids) == {"POL-001", "POL-006"}


def test_custom_registry_composition():
    """Decision composition works correctly with an injected, minimal
    custom registry — proving composition is independent of the real
    12-policy set."""

    class AlwaysDeny(PolicyRule):
        policy_id = "POL-900"
        name = "Always Deny"
        implementation_status = POLICY_STATUS_IMPLEMENTED

        def evaluate(self, request):
            return PolicyResult(
                policy_id=self.policy_id, triggered=True,
                decision=DECISION_DENY, decision_reason="test_deny",
            )

    class AlwaysAllow(PolicyRule):
        policy_id = "POL-901"
        name = "Always Allow (never triggers)"
        implementation_status = POLICY_STATUS_IMPLEMENTED

        def evaluate(self, request):
            return PolicyResult(policy_id=self.policy_id, triggered=False)

    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (AlwaysAllow(), AlwaysDeny()))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_DENY
    assert decision.causing_policy_id == "POL-900"


def test_custom_registry_all_allow_results_in_allow():
    class NeverTriggers(PolicyRule):
        policy_id = "POL-950"
        name = "Never Triggers"
        implementation_status = POLICY_STATUS_IMPLEMENTED

        def evaluate(self, request):
            return PolicyResult(policy_id=self.policy_id, triggered=False)

    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (NeverTriggers(),))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_ALLOW


# --- explainability ---------------------------------------------------------------


def test_decision_explanation_identifies_causing_policy():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(task_id=None))
    assert decision.causing_policy_id == "POL-001"
    assert decision.causing_policy_id in decision.triggered_policy_ids


def test_decision_reason_matches_causing_policy_reason():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="shell", approval_present=False))
    assert decision.decision_reason == "missing_human_approval"
    assert decision.causing_policy_id == "POL-004"


def test_allow_decision_has_no_causing_policy():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_ALLOW
    assert decision.causing_policy_id is None


def test_invalid_request_has_no_causing_policy_no_policies_evaluated():
    """Structural validation happens before any policy rule runs."""
    broker = PermissionBroker()
    decision = broker.evaluate("not a request")  # type: ignore[arg-type]
    assert decision.decision == DECISION_DENY
    assert decision.causing_policy_id is None
    assert decision.evaluated_policy_ids == ()


# --- broker no longer contains duplicated policy logic ---------------------------


def test_broker_evaluate_delegates_to_registry():
    """The broker's evaluate() must not contain its own copy of policy
    conditions — verified by injecting a registry whose POL-001
    implementation disagrees with what the real MissingActiveTaskRule
    would have said, and confirming the broker follows the registry, not
    any internal logic. (Phase 148C.6: the substitute keeps policy_id
    "POL-001" rather than omitting it, since PBPA-REQ-073 now requires
    every canonical policy id to be present in a constructed registry —
    the test's intent, "the broker follows whichever POL-001
    implementation the registry holds," is unaffected by that.)"""

    class AlwaysAllowEverything(PolicyRule):
        policy_id = "POL-001"
        name = "Always Allow Everything"
        implementation_status = POLICY_STATUS_IMPLEMENTED

        def evaluate(self, request):
            return PolicyResult(policy_id=self.policy_id, triggered=False)

    registry = PolicyRegistry(rules=tuple(
        AlwaysAllowEverything() if rule.policy_id == "POL-001" else rule
        for rule in DEFAULT_POLICY_RULES
    ))
    broker = PermissionBroker(registry=registry)
    # This request would have hit POL-001 (missing task) under the real
    # MissingActiveTaskRule, but the injected implementation never
    # triggers.
    decision = broker.evaluate(_valid_request(task_id=None))
    assert decision.decision == DECISION_ALLOW


def test_broker_source_has_no_hardcoded_ng_checks_outside_rules():
    """The PermissionBroker.evaluate method body itself should contain
    none of the policy-specific NG-/INV- IDs that now live exclusively
    in PolicyRule subclasses. Only the structural-validation guard
    (NG-023/INV-009) and the ALLOW composition default's own INV-008
    (about the meaning of ALLOW itself, not a duplicated per-policy
    condition) are legitimate exceptions."""
    import pcae.core.permission_broker_foundation as pbf
    source = inspect.getsource(pbf.PermissionBroker.evaluate)
    rule_only_ids = ("NG-001", "NG-008", "NG-015", "NG-024", "NG-025",
                      "INV-001", "INV-002", "INV-003", "INV-004")
    for rule_id in rule_only_ids:
        assert rule_id not in source, f"{rule_id} should only appear in a PolicyRule"


# --- INV / NG / COMP mapping preserved --------------------------------------------


def test_ng_mapping_preserved_across_all_implemented_rules():
    expected = {
        "POL-001": "NG-001",
        "POL-003": "NG-023",
        "POL-004": "NG-008",
        "POL-005": "NG-025",
        "POL-007": "NG-025",
    }
    for policy_id, ng_id in expected.items():
        rule = next(r for r in DEFAULT_POLICY_RULES if r.policy_id == policy_id)
        if policy_id == "POL-001":
            result = rule.evaluate(_valid_request(task_id=None))
        elif policy_id == "POL-003":
            result = rule.evaluate(_valid_request(evidence_available=False))
        elif policy_id == "POL-004":
            result = rule.evaluate(_valid_request(approval_present=False))
        elif policy_id == "POL-005":
            result = rule.evaluate(_valid_request(simulation_only=False))
        elif policy_id == "POL-007":
            result = rule.evaluate(_valid_request(requested_component="COMP-999"))
        assert ng_id in result.matched_no_go_ids


def test_inv_mapping_preserved_across_all_implemented_rules():
    broker = PermissionBroker()
    scenarios_to_inv = {
        (): "INV-008",
        ("task_id", None): "INV-002",
        ("evidence_available", False): "INV-009",
        ("approval_present", False): "INV-003",
    }
    for key, inv_id in scenarios_to_inv.items():
        overrides = {} if not key else {key[0]: key[1]}
        if key == ("approval_present", False):
            overrides["execution_class"] = "shell"
        decision = broker.evaluate(_valid_request(**overrides))
        assert inv_id in decision.matched_invariants


def test_comp_mapping_present_on_triggered_decisions():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(task_id=None))
    assert "COMP-002" in decision.matched_component_ids


def test_comp_mapping_empty_on_allow():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request())
    assert decision.matched_component_ids == ()


# --- execution remains unavailable -------------------------------------------------


@pytest.mark.parametrize("overrides", [
    {},
    {"task_id": None},
    {"evidence_available": False},
    {"approval_present": False},
    {"simulation_only": False},
])
def test_execution_remains_unavailable(overrides):
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(**overrides))
    assert decision.implementation_status == "execution_unavailable"


def test_no_execution_side_effects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    broker = PermissionBroker()
    for overrides in [{}, {"task_id": None}, {"simulation_only": False}]:
        broker.evaluate(_valid_request(**overrides))
    assert list(tmp_path.iterdir()) == []
