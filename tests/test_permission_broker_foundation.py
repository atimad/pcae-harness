"""Tests for Phase 108A — Permission Broker Foundation.

Verifies the isolated policy-evaluation-only PermissionBroker: fail-closed
behavior, request/decision models, component registry, NG/INV mapping,
and — critically — that the module has no dependency on shell execution,
backend invocation, or Telegram. No subprocess invocation in this file;
pure in-process, pytest-xdist safe.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from pcae.core import permission_broker_foundation as pbf
from pcae.core.permission_broker_foundation import (
    COMPONENT_IDS,
    COMPONENT_REGISTRY,
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    DECISION_VALUES,
    IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE,
    PermissionBroker,
    PermissionBrokerDecision,
    PermissionBrokerRequest,
    build_permission_broker_request,
    get_component,
)

MODULE_PATH = Path(pbf.__file__)

EXPECTED_COMPONENTS = {
    "COMP-001": "Permission Broker",
    "COMP-002": "Execution Boundary",
    "COMP-003": "Human Approval Gate",
    "COMP-004": "Shell Boundary",
    "COMP-005": "Backend Boundary",
    "COMP-006": "Adapter Boundary",
    "COMP-007": "Audit Boundary",
    "COMP-008": "Rollback Boundary",
    "COMP-009": "Emergency Stop",
    "COMP-010": "Execution Enablement",
}


def _valid_request(**overrides) -> PermissionBrokerRequest:
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


# --- broker / model existence -------------------------------------------------


def test_broker_class_exists():
    assert PermissionBroker is not None


def test_broker_has_evaluate_method():
    broker = PermissionBroker()
    assert hasattr(broker, "evaluate")
    assert callable(broker.evaluate)


def test_request_model_exists():
    assert PermissionBrokerRequest is not None


def test_decision_model_exists():
    assert PermissionBrokerDecision is not None


def test_request_model_has_suggested_fields():
    fields = {f for f in PermissionBrokerRequest.__dataclass_fields__}
    for expected in (
        "request_id", "timestamp", "action_type", "execution_class",
        "task_id", "phase_id", "requested_component", "requested_capability",
        "requested_resource", "evidence_available", "approval_present",
        "simulation_only",
    ):
        assert expected in fields, f"Missing request field: {expected}"


def test_decision_model_has_suggested_fields():
    fields = {f for f in PermissionBrokerDecision.__dataclass_fields__}
    for expected in (
        "decision", "decision_reason", "matched_no_go_ids", "matched_invariants",
        "required_remediation", "requires_human", "simulation_only",
        "implementation_status",
    ):
        assert expected in fields, f"Missing decision field: {expected}"


def test_decision_values_are_allow_deny_human_review():
    assert set(DECISION_VALUES) == {"ALLOW", "DENY", "HUMAN_REVIEW"}


def test_build_request_generates_id_and_timestamp():
    r = _valid_request()
    assert r.request_id
    assert r.timestamp
    assert r.request_id.startswith("pbr-")


def test_request_defaults_to_simulation_only():
    r = _valid_request()
    assert r.simulation_only is True


# --- fail-closed behavior ---------------------------------------------------


def test_invalid_request_object_denied():
    broker = PermissionBroker()
    decision = broker.evaluate("not a request")  # type: ignore[arg-type]
    assert decision.decision == DECISION_DENY


def test_unknown_action_type_denied():
    broker = PermissionBroker()
    request = _valid_request(action_type="delete_everything")
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_DENY
    assert "NG-024" in decision.matched_no_go_ids
    assert "INV-004" in decision.matched_invariants


def test_unsupported_execution_class_denied():
    broker = PermissionBroker()
    request = _valid_request(execution_class="quantum")
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_DENY
    assert "NG-015" in decision.matched_no_go_ids
    assert "INV-001" in decision.matched_invariants


def test_unrecognized_component_denied():
    broker = PermissionBroker()
    request = _valid_request(requested_component="COMP-999")
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_DENY
    assert "NG-025" in decision.matched_no_go_ids
    assert "INV-001" in decision.matched_invariants


def test_missing_task_denied():
    broker = PermissionBroker()
    request = _valid_request(task_id=None)
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_DENY
    assert "NG-001" in decision.matched_no_go_ids
    assert "INV-002" in decision.matched_invariants


def test_missing_evidence_denied():
    broker = PermissionBroker()
    request = _valid_request(evidence_available=False)
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_DENY
    assert "NG-023" in decision.matched_no_go_ids
    assert "INV-009" in decision.matched_invariants


def test_missing_approval_results_in_human_review():
    """Phase 148C.6 (PBPA-001 PBPA-REQ-063): POL-004 is applicable only to
    mediated-execution classes {shell, backend, adapter, rollback} — an
    in-scope class is required for POL-004 to be asked about this request
    at all."""
    broker = PermissionBroker()
    request = _valid_request(execution_class="shell", approval_present=False)
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_HUMAN_REVIEW
    assert decision.requires_human is True
    assert "NG-008" in decision.matched_no_go_ids
    assert "INV-003" in decision.matched_invariants


def test_missing_approval_out_of_scope_class_not_applicable_and_allows():
    """Phase 148C.6 (PBPA-001 PBPA-REQ-016/063): at execution_class="none"
    (outside POL-004's applicable set), POL-004 is NOT_APPLICABLE — never
    treated as ALLOW-by-triggering, but also never forced into
    HUMAN_REVIEW merely because approval is absent. With nothing else
    triggering, the decision is ALLOW."""
    broker = PermissionBroker()
    request = _valid_request(execution_class="none", approval_present=False)
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_ALLOW
    assert "POL-004" in decision.non_applicable_policy_ids
    assert "POL-004" not in decision.applicable_policy_ids
    assert "POL-004" not in decision.triggered_policy_ids


def test_real_execution_attempt_always_denied():
    """simulation_only=False must always deny — no execution boundary exists."""
    broker = PermissionBroker()
    request = _valid_request(simulation_only=False)
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_DENY
    assert "NG-025" in decision.matched_no_go_ids


def test_fully_valid_simulation_request_allowed():
    broker = PermissionBroker()
    request = _valid_request()
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_ALLOW
    assert "INV-008" in decision.matched_invariants


def test_deny_checked_before_human_review():
    """Missing evidence must deny even when approval is also missing —
    fail-closed priority: DENY conditions checked before HUMAN_REVIEW."""
    broker = PermissionBroker()
    request = _valid_request(evidence_available=False, approval_present=False)
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_DENY


# --- current implementation status always execution_unavailable -------------


@pytest.mark.parametrize("overrides", [
    {},
    {"task_id": None},
    {"evidence_available": False},
    {"approval_present": False},
    {"action_type": "unknown_thing"},
    {"simulation_only": False},
])
def test_implementation_status_always_execution_unavailable(overrides):
    broker = PermissionBroker()
    request = _valid_request(**overrides)
    decision = broker.evaluate(request)
    assert decision.implementation_status == IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE


def test_allow_decision_never_marks_execution_available():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request())
    assert decision.decision == DECISION_ALLOW
    assert decision.implementation_status == "execution_unavailable"


# --- no execution / no side effects -----------------------------------------


def test_evaluate_has_no_side_effects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    broker = PermissionBroker()
    broker.evaluate(_valid_request())
    assert list(tmp_path.iterdir()) == []


def test_evaluate_returns_decision_not_none():
    broker = PermissionBroker()
    decision = broker.evaluate(_valid_request())
    assert decision is not None
    assert isinstance(decision, PermissionBrokerDecision)


# --- component registry -----------------------------------------------------


def test_component_registry_has_ten_entries():
    assert len(COMPONENT_REGISTRY) == 10


@pytest.mark.parametrize("comp_id,name", list(EXPECTED_COMPONENTS.items()))
def test_component_id_registered(comp_id, name):
    entry = get_component(comp_id)
    assert entry is not None
    assert entry.name == name


def test_component_ids_match_expected_set():
    assert COMPONENT_IDS == frozenset(EXPECTED_COMPONENTS)


def test_unknown_component_returns_none():
    assert get_component("COMP-999") is None


def test_permission_broker_component_marked_foundation_implemented():
    entry = get_component("COMP-001")
    assert entry.implementation_status == "foundation_implemented"


@pytest.mark.parametrize("comp_id", [c for c in EXPECTED_COMPONENTS if c != "COMP-001"])
def test_other_components_marked_not_implemented(comp_id):
    entry = get_component(comp_id)
    assert entry.implementation_status == "not_implemented"


# --- NG / INV mapping existence ----------------------------------------------


def test_ng_mappings_exist_across_decisions():
    broker = PermissionBroker()
    seen_ng_ids: set[str] = set()
    scenarios = [
        {"task_id": None},
        {"evidence_available": False},
        {"execution_class": "shell", "approval_present": False},
        {"action_type": "nonexistent_action"},
        {"execution_class": "nonexistent_class"},
        {"requested_component": "COMP-999"},
        {"simulation_only": False},
    ]
    for overrides in scenarios:
        decision = broker.evaluate(_valid_request(**overrides))
        seen_ng_ids.update(decision.matched_no_go_ids)
    assert seen_ng_ids == {"NG-001", "NG-023", "NG-008", "NG-024", "NG-015", "NG-025"}


def test_inv_mappings_exist_across_decisions():
    broker = PermissionBroker()
    seen_inv_ids: set[str] = set()
    scenarios = [
        {},
        {"task_id": None},
        {"evidence_available": False},
        {"execution_class": "shell", "approval_present": False},
        {"action_type": "nonexistent_action"},
    ]
    for overrides in scenarios:
        decision = broker.evaluate(_valid_request(**overrides))
        seen_inv_ids.update(decision.matched_invariants)
    assert seen_inv_ids == {"INV-002", "INV-009", "INV-003", "INV-004", "INV-008"}


def test_all_matched_no_go_ids_are_well_formed():
    broker = PermissionBroker()
    for overrides in [{}, {"task_id": None}, {"evidence_available": False}]:
        decision = broker.evaluate(_valid_request(**overrides))
        for ng_id in decision.matched_no_go_ids:
            assert ng_id.startswith("NG-")
            assert len(ng_id) == 6


def test_all_matched_invariants_are_well_formed():
    broker = PermissionBroker()
    for overrides in [{}, {"task_id": None}, {"evidence_available": False}]:
        decision = broker.evaluate(_valid_request(**overrides))
        for inv_id in decision.matched_invariants:
            assert inv_id.startswith("INV-")


# --- isolation: no shell / backend / telegram dependency --------------------


@pytest.fixture(scope="module")
def module_imports() -> list[str]:
    import ast
    tree = ast.parse(MODULE_PATH.read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def test_broker_has_no_shell_dependency(module_imports):
    forbidden = ("shell_gate", "subprocess", "os.system")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_broker_has_no_backend_dependency(module_imports):
    forbidden = ("backend_invocations", "backend_cli", "agent_backends")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_broker_has_no_telegram_dependency(module_imports):
    forbidden = ("notifications", "telegram")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_broker_module_imports_only_stdlib():
    import ast
    tree = ast.parse(MODULE_PATH.read_text())
    stdlib_allowed = {"__future__", "uuid", "dataclasses", "datetime", "typing"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                assert top in stdlib_allowed, f"non-stdlib import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                assert top in stdlib_allowed, f"non-stdlib import: {node.module}"


def test_broker_evaluate_signature_has_no_repo_root_or_subprocess_params():
    sig = inspect.signature(PermissionBroker.evaluate)
    param_names = list(sig.parameters)
    assert "repo_root" not in param_names
    assert "command" not in param_names
    assert "cwd" not in param_names
