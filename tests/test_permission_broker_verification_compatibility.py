"""Tests for Phase 108D — Permission Broker Verification & Compatibility.

Verifies, without changing, the Permission Broker's isolation and
compatibility properties established across 108A (foundation), 108B
(policy rule framework), and 108C (composition hardening). This phase
adds no new broker behavior — it strengthens the test surface that
proves the broker remains isolated, contract-traceable, deterministic,
and unwired into any command path.

No subprocess invocation in this file; pure in-process, pytest-xdist
safe. Does not modify tests/test_permission_broker_foundation.py (108A),
tests/test_permission_broker_policy_rule_framework.py (108B), or
tests/test_permission_broker_policy_composition_hardening.py (108C) —
all three are re-run unmodified as the backward-compatibility check.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

import pcae.core.permission_broker_foundation as pbf
from pcae.core.permission_broker_foundation import (
    COMPONENT_IDS,
    COMPONENT_REGISTRY,
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    DEFAULT_POLICY_RULES,
    IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE,
    PermissionBroker,
    PermissionBrokerDecision,
    PolicyRegistry,
    PolicyResult,
    PolicyRule,
    build_permission_broker_request,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
BROKER_MODULE_PATH = Path(pbf.__file__)
AUTONOMY_CONTRACT_PATH = REPO_ROOT / "docs" / "V0_2_AUTONOMY_CONTRACT.md"
NO_GO_GATES_PATH = REPO_ROOT / "docs" / "V0_2_EXECUTION_READINESS_NO_GO_GATES.md"

LIFECYCLE_COMMAND_MODULES = (
    "src/pcae/commands/commit.py",
    "src/pcae/commands/push.py",
    "src/pcae/commands/task.py",
    "src/pcae/commands/phase.py",
)


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


@pytest.fixture(scope="module")
def broker_module_imports() -> list[str]:
    tree = ast.parse(BROKER_MODULE_PATH.read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


@pytest.fixture(scope="module")
def autonomy_contract_text() -> str:
    return AUTONOMY_CONTRACT_PATH.read_text()


@pytest.fixture(scope="module")
def no_go_gates_text() -> str:
    return NO_GO_GATES_PATH.read_text()


@pytest.fixture(scope="module")
def frozen_ng_ids(no_go_gates_text) -> set[str]:
    import re
    return set(re.findall(r"NG-\d{3}", no_go_gates_text))


@pytest.fixture(scope="module")
def frozen_inv_ids(autonomy_contract_text) -> set[str]:
    import re
    return set(re.findall(r"INV-\d{3}", autonomy_contract_text))


# ═══════════════════════════════════════════════════════════════════════
# 1. Broker isolation verification
# ═══════════════════════════════════════════════════════════════════════


def test_broker_imports_only_allowed_stdlib_modules(broker_module_imports):
    allowed = {"__future__", "uuid", "dataclasses", "datetime"}
    for name in broker_module_imports:
        top = name.split(".")[0]
        assert top in allowed, f"unexpected import: {name}"


def test_broker_does_not_import_subprocess(broker_module_imports):
    assert "subprocess" not in broker_module_imports
    assert "os" not in broker_module_imports


def test_broker_does_not_import_shell_gate(broker_module_imports):
    for name in broker_module_imports:
        assert "shell_gate" not in name


def test_broker_does_not_import_backend_modules(broker_module_imports):
    forbidden = ("backend_invocations", "backend_cli", "agent_backends", "agent_invoke")
    for name in broker_module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_broker_does_not_import_adapter_modules(broker_module_imports):
    for name in broker_module_imports:
        assert "adapter" not in name


def test_broker_does_not_import_notification_or_telegram_modules(broker_module_imports):
    for name in broker_module_imports:
        assert "notification" not in name
        assert "telegram" not in name.lower()


LIFECYCLE_COMMAND_MODULES_UNWIRED = tuple(
    m for m in LIFECYCLE_COMMAND_MODULES if m != "src/pcae/commands/push.py"
)


@pytest.mark.parametrize("relative_path", LIFECYCLE_COMMAND_MODULES_UNWIRED)
def test_broker_not_imported_by_lifecycle_command_modules(relative_path):
    """Objective 1: the broker must not be imported *directly* by commit/
    task/phase lifecycle commands unless explicitly documented. As of
    108D, no such documented wiring exists for these three modules — this
    test asserts that fact directly against the real command source.
    `push.py` is excluded from this assertion as of Phase 148E: PBPC-001
    v1.2 (frozen by 148B, Finding B-1 closed by 148C.8/148C.9) explicitly
    authorizes and requires `pcae push` -- and only `pcae push` -- to
    consume the Permission Broker as its mandatory production
    permission-decision boundary (see
    `test_permission_broker_push_production_consumption.py` for the
    dedicated, PBPC-focused test suite covering that wiring). As of Phase
    149F (RWMPC-001 v1.0 Wave 1), `phase.py` is an authorized *indirect*
    consumer via the sole sanctioned adapter module
    `pcae.core.mutation_permission` (PH1/PH2/PH3) -- this test's literal
    assertion (`phase.py` never references the Foundation or constructs
    `PermissionBroker(` *directly*) still holds and remains the correct,
    narrower invariant; `commit.py`/`task.py` remain wholly unwired
    (TK1-3 explicitly deferred, RWMPC-001 Section 14)."""
    path = REPO_ROOT / relative_path
    assert path.is_file(), f"expected lifecycle command module missing: {relative_path}"
    source = path.read_text()
    assert "permission_broker_foundation" not in source
    assert "PermissionBroker(" not in source


def test_broker_wiring_remains_scoped_to_push_only():
    """Phase 148E — the one explicitly authorized exception (`push.py`)
    must not silently expand: no other lifecycle command module may
    import the broker without a corresponding contract amendment."""
    path = REPO_ROOT / "src/pcae/commands/push.py"
    source = path.read_text()
    assert "permission_broker_foundation" in source


def test_broker_not_referenced_in_cli_dispatch():
    cli_source = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text()
    assert "permission_broker_foundation" not in cli_source


def test_broker_decisions_cannot_execute_anything(tmp_path, monkeypatch):
    """No decision path performs file I/O, subprocess invocation, or any
    other side effect, across every default rule and every outcome."""
    monkeypatch.chdir(tmp_path)
    broker = PermissionBroker()
    scenarios = [
        {},
        {"task_id": None},
        {"evidence_available": False},
        {"approval_present": False},
        {"simulation_only": False},
        {"action_type": "nonexistent"},
        {"execution_class": "nonexistent"},
        {"requested_component": "COMP-999"},
    ]
    for overrides in scenarios:
        broker.evaluate(_valid_request(**overrides))
    assert list(tmp_path.iterdir()) == []


def test_allow_decision_still_execution_unavailable():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_ALLOW
    assert decision.implementation_status == IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE


@pytest.mark.parametrize("overrides", [
    {}, {"task_id": None}, {"evidence_available": False}, {"approval_present": False},
    {"simulation_only": False}, {"action_type": "nonexistent"},
])
def test_every_decision_execution_unavailable(overrides):
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(**overrides))
    assert decision.implementation_status == IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE


# ═══════════════════════════════════════════════════════════════════════
# 2. Compatibility with 107B/107C contracts (cross-referenced against docs)
# ═══════════════════════════════════════════════════════════════════════


def test_every_broker_ng_id_exists_in_frozen_no_go_gates_doc(frozen_ng_ids):
    broker = PermissionBroker()
    scenarios = [
        {"task_id": None}, {"evidence_available": False}, {"approval_present": False},
        {"action_type": "nonexistent"}, {"execution_class": "nonexistent"},
        {"requested_component": "COMP-999"}, {"simulation_only": False}, {},
    ]
    used_ng_ids: set[str] = set()
    for overrides in scenarios:
        decision = broker.evaluate(_valid_request(**overrides))
        used_ng_ids.update(decision.matched_no_go_ids)
    assert used_ng_ids, "expected at least one NG id across scenarios"
    assert used_ng_ids <= frozen_ng_ids, f"broker references NG ids not in the frozen doc: {used_ng_ids - frozen_ng_ids}"


def test_every_broker_inv_id_exists_in_frozen_autonomy_contract(frozen_inv_ids):
    broker = PermissionBroker()
    scenarios = [
        {}, {"task_id": None}, {"evidence_available": False}, {"approval_present": False},
        {"action_type": "nonexistent"}, {"execution_class": "nonexistent"},
        {"requested_component": "COMP-999"}, {"simulation_only": False},
    ]
    used_inv_ids: set[str] = set()
    for overrides in scenarios:
        decision = broker.evaluate(_valid_request(**overrides))
        used_inv_ids.update(decision.matched_invariants)
    assert used_inv_ids, "expected at least one INV id across scenarios"
    assert used_inv_ids <= frozen_inv_ids, f"broker references INV ids not in the frozen contract: {used_inv_ids - frozen_inv_ids}"


def test_component_registry_ids_referenced_in_autonomy_contract_doc(autonomy_contract_text):
    """Every canonical COMP-NNN id frozen in 108A must actually appear in
    the autonomy contract doc it was additively cross-referenced into."""
    for entry in COMPONENT_REGISTRY:
        assert entry.component_id in autonomy_contract_text


def test_no_go_gate_index_table_has_component_id_column(no_go_gates_text):
    assert "Component ID" in no_go_gates_text


def test_decisions_always_carry_remediation_when_triggered():
    broker = PermissionBroker()
    for overrides in [
        {"task_id": None},
        {"evidence_available": False},
        {"execution_class": "shell", "approval_present": False},
    ]:
        decision = broker.evaluate(_valid_request(**overrides))
        assert len(decision.required_remediation) >= 1


def test_fail_closed_default_confirmed_for_every_default_rule_trigger():
    """Every default rule that can trigger resolves to DENY or
    HUMAN_REVIEW — never ALLOW — confirming fail-closed is the design,
    not an accident of the specific scenarios tested elsewhere."""
    broker = PermissionBroker()
    triggering_overrides = [
        {"task_id": None},
        {"evidence_available": False},
        {"execution_class": "shell", "approval_present": False},
        {"simulation_only": False},
        {"action_type": "nonexistent"},
        {"execution_class": "nonexistent"},
        {"requested_component": "COMP-999"},
    ]
    for overrides in triggering_overrides:
        decision = broker.evaluate(_valid_request(**overrides))
        assert decision.decision in (DECISION_DENY, DECISION_HUMAN_REVIEW)


def test_stub_policies_have_no_component_mapping_yet():
    """Objective 2 boundary: COMP identifiers are canonical (108A), but
    the six stub policies never trigger and therefore never assert a
    component mapping — no behavior is invented for them here."""
    for rule in DEFAULT_POLICY_RULES:
        if rule.implementation_status == "not_implemented":
            result = rule.evaluate(_valid_request())
            assert result.triggered is False
            assert result.matched_component_ids == ()


# ═══════════════════════════════════════════════════════════════════════
# 3. Decision composition behavior (re-verification, real registry)
# ═══════════════════════════════════════════════════════════════════════


def test_multi_cause_deny_with_real_registry():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(task_id=None, action_type="nonexistent", requested_component="COMP-999"))
    assert decision.decision == DECISION_DENY
    assert set(decision.causing_policy_ids) == {"POL-001", "POL-006", "POL-007"}
    assert len(decision.reason_chain) == 3


def test_multi_cause_human_review_with_custom_rules():
    class ReviewA(PolicyRule):
        policy_id = "POL-701"
        name = "Review A"
        implementation_status = "implemented"

        def evaluate(self, request):
            return PolicyResult(policy_id=self.policy_id, triggered=True, decision=DECISION_HUMAN_REVIEW,
                                 decision_reason="review_a", matched_no_go_ids=("NG-008",), requires_human=True)

    class ReviewB(PolicyRule):
        policy_id = "POL-702"
        name = "Review B"
        implementation_status = "implemented"

        def evaluate(self, request):
            return PolicyResult(policy_id=self.policy_id, triggered=True, decision=DECISION_HUMAN_REVIEW,
                                 decision_reason="review_b", matched_no_go_ids=("NG-008",), requires_human=True)

    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (ReviewA(), ReviewB()))
    broker = PermissionBroker(registry=registry)
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_HUMAN_REVIEW
    assert decision.causing_policy_ids == ("POL-701", "POL-702")
    assert decision.requires_human is True


def test_deny_precedence_over_human_review_with_real_registry():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(execution_class="shell", evidence_available=False, approval_present=False))
    assert decision.decision == DECISION_DENY
    assert decision.causing_policy_id == "POL-003"
    assert "POL-004" in decision.triggered_policy_ids


def test_order_preserving_dedup_across_real_multi_trigger():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(simulation_only=False, requested_component="COMP-999"))
    # POL-005 and POL-007 both map to NG-025/INV-001/COMP-002 — dedup must
    # collapse the duplicate, not just concatenate.
    assert decision.matched_no_go_ids.count("NG-025") == 1
    assert decision.matched_invariants.count("INV-001") == 1
    assert decision.matched_component_ids.count("COMP-002") == 1


def test_causing_policy_ids_field_present_and_ordered():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(task_id=None, action_type="nonexistent"))
    assert decision.causing_policy_ids == ("POL-001", "POL-006")


def test_reason_chain_present_and_matches_causing_ids():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(task_id=None, action_type="nonexistent"))
    assert tuple(link.policy_id for link in decision.reason_chain) == decision.causing_policy_ids


def test_precedence_reason_present_for_every_category():
    broker = PermissionBroker()
    deny = broker.evaluate(_valid_request(task_id=None))
    review = broker.evaluate(_valid_request(execution_class="shell", approval_present=False))
    allow = broker.evaluate(_valid_request())
    assert deny.precedence_reason
    assert review.precedence_reason
    assert allow.precedence_reason
    assert deny.precedence_reason != review.precedence_reason != allow.precedence_reason


def test_remediation_preserved_across_multi_cause():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(task_id=None, action_type="nonexistent"))
    assert len(decision.required_remediation) >= 2


def test_malformed_policy_rule_fails_closed():
    class Malformed(PolicyRule):
        policy_id = "POL-703"
        name = "Malformed"
        implementation_status = "implemented"

        def evaluate(self, request):
            return "not a PolicyResult"

    broker = PermissionBroker(registry=PolicyRegistry(rules=DEFAULT_POLICY_RULES + (Malformed(),)))
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_DENY
    assert decision.decision_reason == "invalid_policy_result"


def test_raising_policy_rule_fails_closed():
    class Raises(PolicyRule):
        policy_id = "POL-704"
        name = "Raises"
        implementation_status = "implemented"

        def evaluate(self, request):
            raise RuntimeError("simulated failure")

    broker = PermissionBroker(registry=PolicyRegistry(rules=DEFAULT_POLICY_RULES + (Raises(),)))
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_DENY
    assert decision.decision_reason == "invalid_policy_result"


def test_empty_registry_fails_closed():
    """Phase 148C.6 (PBPA-001 PBPA-REQ-073): fail-closed for an empty
    registry moves to PolicyRegistry construction time (a missing-policy
    condition for all twelve canonical ids), superseding the pre-PBPA
    behavior where construction succeeded and evaluate() denied."""
    with pytest.raises(ValueError, match="missing canonical policy"):
        PolicyRegistry(rules=())


def test_unknown_action_fails_closed():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(action_type="totally_unknown_action"))
    assert decision.decision == DECISION_DENY


def test_missing_evidence_fails_closed():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(evidence_available=False))
    assert decision.decision == DECISION_DENY


def test_ambiguity_fails_closed_via_unknown_capability_policy():
    """Policy ambiguity (an unrecognized action/execution class) resolves
    to DENY via POL-006 and NG-024 ("Policy Ambiguity")."""
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request(action_type="ambiguous_thing"))
    assert decision.decision == DECISION_DENY
    assert "NG-024" in decision.matched_no_go_ids


# ═══════════════════════════════════════════════════════════════════════
# 4. Backward compatibility
# ═══════════════════════════════════════════════════════════════════════


def test_prior_phase_test_modules_still_collect_and_import_cleanly():
    """108A/108B/108C test modules must still import without error against
    the current broker module — a basic collection-level compatibility
    smoke test, independent of actually running their assertions (which
    the validation suites do separately)."""
    import importlib
    for module_name in (
        "tests.test_permission_broker_foundation",
        "tests.test_permission_broker_policy_rule_framework",
        "tests.test_permission_broker_policy_composition_hardening",
    ):
        importlib.import_module(module_name)


def test_public_decision_shape_is_a_strict_superset_of_108a_fields():
    fields = set(PermissionBrokerDecision.__dataclass_fields__)
    original_108a_fields = {
        "decision", "decision_reason", "matched_no_go_ids", "matched_invariants",
        "required_remediation", "requires_human", "simulation_only",
        "implementation_status", "matched_component_ids", "evaluated_policy_ids",
        "triggered_policy_ids", "causing_policy_id",
    }
    assert original_108a_fields <= fields


def test_zero_arg_broker_and_default_registry_unchanged():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_ALLOW
    # 12 original policies + POL-013 (Phase ...1R.22, N-16-3 — additive
    # conjunctive eligibility policy that never emits ALLOW/HUMAN_REVIEW).
    assert len(DEFAULT_POLICY_RULES) == 13


def test_component_registry_unchanged_since_108a():
    assert COMPONENT_IDS == frozenset({f"COMP-{n:03d}" for n in range(1, 11)})
    assert len(COMPONENT_REGISTRY) == 10
