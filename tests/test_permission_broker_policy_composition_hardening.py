"""Tests for Phase 108C — Permission Broker Policy Composition & Hardening.

Verifies deterministic decision composition, structured reason chains,
policy conflict handling, explainability hardening, modularity/
pluggability safeguards, and backward compatibility with Phase 108A/108B
public behavior. No subprocess invocation in this file; pure in-process,
pytest-xdist safe.

This file does not modify tests/test_permission_broker_foundation.py
(108A) or tests/test_permission_broker_policy_rule_framework.py (108B) —
both are re-run unmodified as the backward-compatibility check.
"""

from __future__ import annotations

import inspect

import pytest

from pcae.core.permission_broker_foundation import (
    COMPONENT_IDS,
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    DEFAULT_POLICY_RULES,
    PermissionBroker,
    PermissionBrokerDecision,
    PolicyRegistry,
    PolicyResult,
    PolicyRule,
    POLICY_STATUS_IMPLEMENTED,
    ReasonChainLink,
    build_permission_broker_request,
)
from pcae.core.permission_broker_foundation import _compose, _dedup_ordered, _sanitize_result


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


class _DenyRule(PolicyRule):
    implementation_status = POLICY_STATUS_IMPLEMENTED

    def __init__(self, policy_id, name="Deny", ng=("NG-900",), inv=("INV-900",), comp=("COMP-900",), remediation=("fix it",)):
        self.policy_id = policy_id
        self.name = name
        self._ng = ng
        self._inv = inv
        self._comp = comp
        self._rem = remediation

    def evaluate(self, request):
        return PolicyResult(
            policy_id=self.policy_id,
            triggered=True,
            decision=DECISION_DENY,
            decision_reason=f"{self.policy_id.lower()}_denied",
            matched_no_go_ids=self._ng,
            matched_invariants=self._inv,
            matched_component_ids=self._comp,
            required_remediation=self._rem,
        )


class _HumanReviewRule(PolicyRule):
    implementation_status = POLICY_STATUS_IMPLEMENTED

    def __init__(self, policy_id, name="Review"):
        self.policy_id = policy_id
        self.name = name

    def evaluate(self, request):
        return PolicyResult(
            policy_id=self.policy_id,
            triggered=True,
            decision=DECISION_HUMAN_REVIEW,
            decision_reason=f"{self.policy_id.lower()}_review",
            matched_no_go_ids=(f"NG-{self.policy_id[-3:]}",),
            matched_invariants=("INV-800",),
            requires_human=True,
        )


class _NeverTriggers(PolicyRule):
    implementation_status = POLICY_STATUS_IMPLEMENTED

    def __init__(self, policy_id="POL-950", name="Never"):
        self.policy_id = policy_id
        self.name = name

    def evaluate(self, request):
        return PolicyResult(policy_id=self.policy_id, triggered=False)


# --- 1. deterministic decision composition ---------------------------------------


def test_deny_overrides_human_review_and_allow():
    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (
        _NeverTriggers("POL-951"), _HumanReviewRule("POL-952"), _DenyRule("POL-953"),
    ))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_DENY
    assert decision.causing_policy_id == "POL-953"


def test_human_review_overrides_allow():
    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (_NeverTriggers(), _HumanReviewRule("POL-960")))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_HUMAN_REVIEW
    assert decision.causing_policy_id == "POL-960"


def test_allow_only_when_no_deny_or_human_review_triggers():
    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (_NeverTriggers("POL-1"), _NeverTriggers("POL-2")))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_ALLOW


@pytest.mark.parametrize("_iteration", range(10))
def test_deterministic_ordering_of_evaluated_and_triggered_policies(_iteration):
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="shell", task_id=None, action_type="bogus"))
    # POL-013 (Phase ...1R.22, N-16-3) is scoped to execution_class=adapter, so
    # it is non-applicable for this shell request and absent from evaluated ids.
    assert decision.evaluated_policy_ids == tuple(
        r.policy_id for r in DEFAULT_POLICY_RULES if r.policy_id != "POL-013"
    )
    assert decision.triggered_policy_ids == ("POL-001", "POL-006")


def test_deterministic_ordering_repeated_calls_identical():
    broker = PermissionBroker()
    request = _valid_request(evidence_available=False, approval_present=False)
    results = [broker.evaluate(request) for _ in range(25)]
    assert all(r == results[0] for r in results)


def test_deterministic_ordering_of_no_go_invariant_component_remediation_ids():
    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (
        _DenyRule("POL-970", ng=("NG-A", "NG-B"), inv=("INV-A",), comp=("COMP-A",), remediation=("step one",)),
        _DenyRule("POL-971", ng=("NG-B", "NG-C"), inv=("INV-A", "INV-B"), comp=("COMP-B",), remediation=("step two",)),
    ))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    # Order-preserving, deduplicated: NG-B appears once, in first-seen order.
    assert decision.matched_no_go_ids == ("NG-A", "NG-B", "NG-C")
    assert decision.matched_invariants == ("INV-A", "INV-B")
    assert decision.matched_component_ids == ("COMP-A", "COMP-B")
    assert decision.required_remediation == ("step one", "step two")


def test_dedup_ordered_helper_directly():
    assert _dedup_ordered(("a", "b"), ("b", "c"), ("a",)) == ("a", "b", "c")
    assert _dedup_ordered() == ()
    assert _dedup_ordered((), ("x",)) == ("x",)


# --- 2. structured reason chain --------------------------------------------------


def test_reason_chain_model_exists():
    assert ReasonChainLink is not None


def test_reason_chain_single_cause_matches_brief_example():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(evidence_available=False))
    assert len(decision.reason_chain) == 1
    link = decision.reason_chain[0]
    assert link.policy_id == "POL-003"
    assert link.no_go_ids == ("NG-023",)
    assert link.invariant_ids == ("INV-009",)
    assert link.component_ids == ("COMP-001",)


def test_reason_chain_has_one_link_per_contributing_policy():
    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (_DenyRule("POL-980"), _DenyRule("POL-981")))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert len(decision.reason_chain) == 2
    assert [link.policy_id for link in decision.reason_chain] == ["POL-980", "POL-981"]


def test_reason_chain_empty_on_allow():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request())
    assert decision.reason_chain == ()


def test_reason_chain_fields_are_tuples_machine_readable():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(task_id=None))
    link = decision.reason_chain[0]
    assert isinstance(link.no_go_ids, tuple)
    assert isinstance(link.invariant_ids, tuple)
    assert isinstance(link.component_ids, tuple)


# --- 3. policy conflict handling -------------------------------------------------


def test_conflict_deny_plus_human_review_resolves_deny():
    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (_HumanReviewRule("POL-990"), _DenyRule("POL-991")))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_DENY
    assert "POL-990" in decision.triggered_policy_ids
    assert "POL-991" in decision.triggered_policy_ids
    assert decision.causing_policy_id == "POL-990" or decision.causing_policy_id == "POL-991"
    # DENY-category causing id must actually be the DENY rule, not the review rule.
    assert decision.causing_policy_id == "POL-991"


def test_conflict_allow_plus_deny_resolves_deny():
    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (_NeverTriggers(), _DenyRule("POL-992")))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_DENY


def test_conflict_allow_plus_human_review_resolves_human_review():
    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (_NeverTriggers(), _HumanReviewRule("POL-993")))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_HUMAN_REVIEW


def test_multiple_deny_rules_all_causes_preserved():
    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (_DenyRule("POL-994"), _DenyRule("POL-995"), _DenyRule("POL-996")))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_DENY
    assert decision.causing_policy_ids == ("POL-994", "POL-995", "POL-996")
    assert len(decision.reason_chain) == 3


def test_no_applicable_policy_fails_closed():
    """Phase 148C.6 (PBPA-001 PBPA-REQ-073): an empty registry is a
    missing-policy condition (all twelve canonical ids absent), and
    PBPA-REQ-073 moves that fail-closed behavior to PolicyRegistry
    construction time — a registry with zero rules can no longer be
    constructed at all, superseding the pre-PBPA behavior where
    construction succeeded and only evaluate() denied."""
    with pytest.raises(ValueError, match="missing canonical policy"):
        PolicyRegistry(rules=())


def test_unknown_policy_result_decision_value_fails_closed():
    class BadDecision(PolicyRule):
        policy_id = "POL-997"
        name = "Bad Decision"
        implementation_status = POLICY_STATUS_IMPLEMENTED

        def evaluate(self, request):
            return PolicyResult(policy_id=self.policy_id, triggered=True, decision="MAYBE_ALLOW")

    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (BadDecision(),))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_DENY
    assert decision.decision_reason == "invalid_policy_result"
    assert decision.causing_policy_id == "POL-997"


def test_unknown_policy_result_non_policy_result_object_fails_closed():
    class BadReturn(PolicyRule):
        policy_id = "POL-998"
        name = "Bad Return"
        implementation_status = POLICY_STATUS_IMPLEMENTED

        def evaluate(self, request):
            return {"decision": "ALLOW"}  # not a PolicyResult

    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (BadReturn(),))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_DENY
    assert decision.decision_reason == "invalid_policy_result"


def test_policy_rule_that_raises_fails_closed():
    class Raises(PolicyRule):
        policy_id = "POL-999"
        name = "Raises"
        implementation_status = POLICY_STATUS_IMPLEMENTED

        def evaluate(self, request):
            raise ValueError("boom")

    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (Raises(),))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_DENY
    assert decision.decision_reason == "invalid_policy_result"
    assert decision.causing_policy_id == "POL-999"


def test_sanitize_result_passes_through_well_formed_results():
    rule = _DenyRule("POL-800")
    result = rule.evaluate(_valid_request())
    assert _sanitize_result(rule, result) is result


def test_sanitize_result_passes_through_not_triggered():
    rule = _NeverTriggers("POL-801")
    result = rule.evaluate(_valid_request())
    assert _sanitize_result(rule, result) is result


# --- 4. explainability hardening --------------------------------------------------


def test_decision_exposes_all_evaluated_triggered_causing_ids():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="shell", task_id=None))
    assert len(decision.evaluated_policy_ids) == 12
    assert decision.triggered_policy_ids == ("POL-001",)
    assert decision.causing_policy_id == "POL-001"
    assert decision.causing_policy_ids == ("POL-001",)


def test_decision_exposes_matched_ng_inv_comp_remediation():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(task_id=None))
    assert decision.matched_no_go_ids == ("NG-001",)
    assert decision.matched_invariants == ("INV-002",)
    assert decision.matched_component_ids == ("COMP-002",)
    assert len(decision.required_remediation) >= 1


def test_decision_exposes_precedence_reason():
    broker = PermissionBroker()
    deny_decision = broker.evaluate(_valid_request(task_id=None))
    assert "deny_precedence" in deny_decision.precedence_reason

    review_decision = broker.evaluate(_valid_request(execution_class="shell", approval_present=False))
    assert "human_review_precedence" in review_decision.precedence_reason

    allow_decision = broker.evaluate(_valid_request())
    assert "allow_default" in allow_decision.precedence_reason


def test_implementation_status_always_execution_unavailable_after_hardening():
    broker = PermissionBroker()
    for overrides in [{}, {"task_id": None}, {"approval_present": False}, {"simulation_only": False}]:
        decision = broker.evaluate(_valid_request(**overrides))
        assert decision.implementation_status == "execution_unavailable"


def test_decision_model_has_hardening_fields():
    fields = set(PermissionBrokerDecision.__dataclass_fields__)
    for expected in ("causing_policy_ids", "reason_chain", "precedence_reason"):
        assert expected in fields


# --- 5. modularity / pluggability safeguards --------------------------------------


def test_policy_rule_implementations_remain_independent():
    for rule in DEFAULT_POLICY_RULES:
        sig = inspect.signature(rule.evaluate)
        assert list(sig.parameters) == ["request"]


def test_registry_accepts_additional_rules_without_modifying_broker():
    # POL-013 is now a canonical policy (Phase ...1R.22); use POL-014 for the
    # synthetic extra rule this test injects.
    extra = DEFAULT_POLICY_RULES + (_DenyRule("POL-014", name="Extra Rule"),)
    registry = PolicyRegistry(rules=extra)
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request(execution_class="shell"))
    assert decision.decision == DECISION_DENY
    assert decision.causing_policy_id == "POL-014"
    # execution_class=shell: 12 canonical (POL-013 is adapter-scoped, non-
    # applicable) + the universal synthetic POL-014 = 13 evaluated.
    assert len(decision.evaluated_policy_ids) == 13


def test_broker_class_source_unchanged_in_size_class_stays_thin():
    """The broker's evaluate() should remain a thin orchestrator: guard +
    delegate, nothing more, even after this phase's hardening."""
    source = inspect.getsource(PermissionBroker.evaluate)
    assert "_compose(" in source
    assert source.count("return") <= 2


def test_broker_module_has_no_shell_backend_adapter_telegram_dependency():
    import ast
    from pathlib import Path
    import pcae.core.permission_broker_foundation as pbf
    tree = ast.parse(Path(pbf.__file__).read_text())
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    forbidden = ("shell_gate", "backend_invocations", "notifications", "adapter", "telegram", "subprocess")
    for name in names:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_policy_rules_return_policy_result_only():
    for rule in DEFAULT_POLICY_RULES:
        result = rule.evaluate(_valid_request())
        assert isinstance(result, PolicyResult)


def test_policy_rules_do_not_execute_commands():
    import inspect as _inspect
    for rule in DEFAULT_POLICY_RULES:
        source = _inspect.getsource(type(rule).evaluate)
        assert "subprocess" not in source
        assert "os.system" not in source
        assert "eval(" not in source
        assert "exec(" not in source


def test_decision_composition_is_centralized():
    """Every code path that produces a PermissionBrokerDecision from
    PolicyResults goes through the single _compose function."""
    broker = PermissionBroker()
    results = broker._registry.evaluate_all(_valid_request(task_id=None))
    direct = _compose(results)
    via_broker = broker.evaluate(_valid_request(task_id=None))
    assert direct == via_broker


def test_no_dynamic_plugin_loading_present():
    import pcae.core.permission_broker_foundation as pbf
    source = inspect.getsource(pbf)
    for forbidden in ("importlib", "__import__", "pkg_resources", "entry_points"):
        assert forbidden not in source


# --- 6. backward compatibility -----------------------------------------------------


def test_108a_public_symbols_still_present():
    import pcae.core.permission_broker_foundation as pbf
    for symbol in (
        "PermissionBroker", "PermissionBrokerRequest", "PermissionBrokerDecision",
        "build_permission_broker_request", "COMPONENT_REGISTRY", "COMPONENT_IDS",
        "get_component", "DECISION_ALLOW", "DECISION_DENY", "DECISION_HUMAN_REVIEW",
    ):
        assert hasattr(pbf, symbol)


def test_108b_public_symbols_still_present():
    import pcae.core.permission_broker_foundation as pbf
    for symbol in (
        "PolicyRule", "PolicyResult", "PolicyRegistry", "DEFAULT_POLICY_RULES",
        "POLICY_IDS", "StubPolicyRule",
    ):
        assert hasattr(pbf, symbol)


def test_zero_arg_broker_construction_still_works():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_ALLOW


def test_component_registry_unaffected_by_hardening():
    assert COMPONENT_IDS == frozenset({f"COMP-{n:03d}" for n in range(1, 11)})
