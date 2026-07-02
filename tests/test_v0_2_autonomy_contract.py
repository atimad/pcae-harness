"""Tests for Phase 107B — v0.2 Autonomy Contract Freeze.

Documentation-focused: verifies the frozen v0.2 autonomy contract and
its accompanying phase document exist and make the required (and only
the required) claims. No live network access. Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = REPO_ROOT / "docs" / "V0_2_AUTONOMY_CONTRACT.md"
PHASE_DOC_PATH = REPO_ROOT / "docs" / "PHASE_107_V0_2_AUTONOMY_CONTRACT_FREEZE.md"

COMPONENTS = [
    "Permission Broker",
    "Execution Boundary",
    "Human Approval Gate",
    "Shell/Subprocess/Network Boundary",
    "Backend Invocation Boundary",
    "Adapter Invocation Boundary",
    "Audit Boundary",
    "Rollback Readiness Boundary",
    "Emergency Stop Boundary",
    "Execution Enablement Model",
    "No-Go Registry",
    "PR / Branch Protection Workflow",
]

INVARIANT_IDS = [f"INV-{n:03d}" for n in range(1, 11)]

LIFECYCLE_STATES = [
    "PLANNED",
    "READY",
    "AWAITING_HUMAN_APPROVAL",
    "AUTHORIZED",
    "EXECUTING",
    "COMPLETED",
    "FAILED",
    "ABORTED",
]


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_PATH.read_text()


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC_PATH.read_text()


# --- existence ---------------------------------------------------------------


def test_contract_doc_exists():
    assert CONTRACT_PATH.is_file()


def test_phase_doc_exists():
    assert PHASE_DOC_PATH.is_file()


# --- v0.2 target / v0.1 boundary -----------------------------------------------


def test_v0_2_target_is_level_3(contract_text):
    assert "Level 3" in contract_text
    normalized = " ".join(contract_text.split())
    assert "Governed Human-Approved Bounded Execution" in normalized


def test_v0_1_remains_non_executing(contract_text):
    lowered = contract_text.lower()
    assert "v0.1 remains non-executing" in lowered


def test_execution_remains_unavailable_now(contract_text):
    lowered = contract_text.lower()
    assert "execution remains unavailable now" in lowered


# --- architectural invariants ---------------------------------------------------


@pytest.mark.parametrize("invariant_id", INVARIANT_IDS)
def test_architectural_invariant_present(contract_text, invariant_id):
    assert invariant_id in contract_text


def test_invariants_section_exists(contract_text):
    assert "Architectural Invariants" in contract_text


# --- execution lifecycle --------------------------------------------------------


@pytest.mark.parametrize("state", LIFECYCLE_STATES)
def test_execution_lifecycle_state_present(contract_text, state):
    assert state in contract_text


def test_execution_lifecycle_section_exists(contract_text):
    assert "Canonical Execution Lifecycle" in contract_text


# --- required conceptual content ------------------------------------------------


def test_permission_broker_role_exists(contract_text):
    assert "Permission Broker" in contract_text
    assert "fail-closed" in contract_text.lower()


def test_human_approval_requirement_exists(contract_text):
    lowered = contract_text.lower()
    assert "human approval" in lowered
    assert "mandatory" in lowered


def test_shell_subprocess_network_boundaries_exist(contract_text):
    assert "Shell/Subprocess/Network" in contract_text


def test_backend_adapter_boundaries_exist(contract_text):
    assert "Backend Invocation Boundary" in contract_text
    assert "Adapter Invocation Boundary" in contract_text


def test_audit_requirements_exist(contract_text):
    lowered = contract_text.lower()
    assert "audit artifact" in lowered
    assert "durable" in lowered


def test_rollback_readiness_exists(contract_text):
    lowered = contract_text.lower()
    assert "rollback readiness" in lowered


def test_emergency_stop_requirement_exists(contract_text):
    lowered = contract_text.lower()
    assert "emergency stop" in lowered


def test_execution_enablement_is_future_default_off(contract_text):
    lowered = contract_text.lower()
    assert "default-off" in lowered or "default off" in lowered
    assert "not implemented" in lowered


def test_no_go_conditions_exist(contract_text):
    assert "Hard No-Go Conditions" in contract_text


def test_branch_protected_main_pr_workflow_implications_exist(contract_text):
    lowered = contract_text.lower()
    assert "branch-protected" in lowered or "branch protection" in lowered
    assert "pull request" in lowered or "pr " in lowered or "pr-" in lowered


# --- component sections: Purpose / Responsibilities / Current Status ----------


@pytest.mark.parametrize("component", COMPONENTS)
def test_component_has_required_subsections(contract_text, component):
    heading = f"### {component}"
    assert heading in contract_text
    idx = contract_text.index(heading)
    # Look at the text following the component heading for its subsections.
    window = contract_text[idx : idx + 1500]
    assert "**Purpose:**" in window
    assert "**Responsibilities:**" in window
    assert "**Current Status:**" in window


# --- no overclaiming -------------------------------------------------------------


@pytest.mark.parametrize("fixture_name", ["contract_text", "phase_doc_text"])
def test_docs_do_not_claim_execution_capabilities_exist(fixture_name, request):
    text = request.getfixturevalue(fixture_name).lower()
    forbidden_phrases = [
        "runtime enforcement is implemented",
        "pcae autonomously executes",
        "autonomous execution is available",
        "telegram inbound is available",
        "telegram inbound exists",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text


# --- recommended next phase -------------------------------------------------------


@pytest.mark.parametrize("fixture_name", ["contract_text", "phase_doc_text"])
def test_docs_recommend_next_phase_107c(fixture_name, request):
    text = request.getfixturevalue(fixture_name)
    assert "107C" in text
