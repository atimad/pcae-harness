"""Tests for Phase 107E — PR-Compatible Governed Development Workflow Design.

Documentation-focused: verifies the frozen PR-compatible governed
development workflow document and its accompanying phase document exist
and make the required (and only the required) claims. No live network
access. Non-executing. Read-only file assertions — no subprocess
invocation, no shared .pcae/ artifact state, safe under pytest-xdist.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_DOC_PATH = REPO_ROOT / "docs" / "V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md"
PHASE_DOC_PATH = REPO_ROOT / "docs" / "PHASE_107_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md"

REPOSITORY_ROLES = [
    "Repository Owner",
    "Maintainer",
    "Contributor",
    "Human Reviewer",
    "PCAE",
    "AI Coding Agent",
    "Permission Broker (future)",
]

DEVELOPMENT_FLOW_STAGES = [
    "Task",
    "Feature Branch",
    "Implementation",
    "Validation",
    "Review",
    "Approval",
    "Merge",
    "Main",
]

AI_MAY = [
    "plan",
    "generate code",
    "prepare commits",
    "prepare documentation",
    "recommend PR text",
    "recommend reviewers",
]

AI_MAY_NOT = [
    "merge",
    "self-approve",
    "bypass branch protection",
    "bypass PCAE governance",
    "bypass the Permission Broker",
    "authorize execution",
    "authorize itself",
]

FUTURE_COMPONENTS = [
    "Permission Broker",
    "Human Approval Gate",
    "Execution Boundary",
    "Audit Boundary",
    "Rollback Readiness Boundary",
]

GOVERNANCE_COMMANDS = [
    "pcae health",
    "pcae check",
    "pcae doctor task-memory",
    "pcae push check",
    "pcae task new",
    "pcae commit implementation",
    "pcae task finish",
    "pcae phase complete",
]

NON_GOAL_PHRASES = [
    "No runtime enforcement",
    "No execution capability",
    "No permission broker enforcement",
    "No shell mediation",
    "No backend invocation",
    "No adapter execution",
    "No Telegram inbound",
    "No audit storage implementation",
    "No rollback execution",
    "No emergency stop implementation",
    "No execution enablement",
    "No PR automation",
    "No GitHub Actions changes",
    "No GitHub API integration",
    "No automatic PR creation",
    "No automatic merge",
    "No automatic approval",
    "No merge queues",
    "No branch creation automation",
]

FORBIDDEN_CLAIMS = [
    "execution is available",
    "execution is enabled",
    "pcae can merge",
    "pcae automatically merges",
    "pcae automatically approves",
    "prs are created automatically",
    "prs are merged automatically",
    "merge automation is implemented",
    "pr automation is implemented",
]


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return WORKFLOW_DOC_PATH.read_text()


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC_PATH.read_text()


# --- existence ---------------------------------------------------------------


def test_workflow_doc_exists():
    assert WORKFLOW_DOC_PATH.is_file()


def test_phase_doc_exists():
    assert PHASE_DOC_PATH.is_file()


def test_workflow_doc_not_empty(workflow_text):
    assert len(workflow_text.strip()) > 1000


def test_phase_doc_not_empty(phase_doc_text):
    assert len(phase_doc_text.strip()) > 500


# --- 1. repository roles -------------------------------------------------------


@pytest.mark.parametrize("role", REPOSITORY_ROLES)
def test_repository_role_defined(workflow_text, role):
    assert role in workflow_text


def test_repository_roles_section_present(workflow_text):
    assert "Repository Roles" in workflow_text


def test_roles_have_responsibilities_authority_limitations(workflow_text):
    normalized = " ".join(workflow_text.split())
    assert "Responsibilities:" in normalized
    assert "Authority:" in normalized or "Authority (future" in normalized
    assert "Limitations:" in normalized


# --- 2. development flow --------------------------------------------------------


def test_development_flow_section_present(workflow_text):
    assert "Development Flow" in workflow_text


def test_development_flow_stages_defined(workflow_text):
    for stage in DEVELOPMENT_FLOW_STAGES:
        assert stage in workflow_text, f"Missing development flow stage: {stage}"


def test_development_flow_order_preserved(workflow_text):
    start = workflow_text.index("## 2. Development Flow")
    end = workflow_text.index("## 3. Branch Policy")
    diagram = workflow_text[start:end]
    positions = [diagram.index(stage) for stage in DEVELOPMENT_FLOW_STAGES]
    assert positions == sorted(positions), "Development flow stages are out of order"


def test_development_flow_states_no_implementation(workflow_text):
    normalized = " ".join(workflow_text.split())
    assert "No implementation of PR automation" in normalized \
        or "no implementation of PR automation" in normalized.lower()


# --- 3. branch policy ------------------------------------------------------------


def test_branch_policy_section_present(workflow_text):
    assert "Branch Policy" in workflow_text


@pytest.mark.parametrize("term", [
    "Protected", "main",
    "Feature Branches",
    "Release Branches",
    "Owner Workflow",
    "Maintainer Workflow",
    "Contributor Workflow",
])
def test_branch_policy_covers_required_topics(workflow_text, term):
    assert term in workflow_text


@pytest.mark.parametrize("posture_term", [
    "enforce_admins",
    "Force push",
    "Branch deletion",
    "Conversation resolution",
    "Required PR review",
])
def test_transitional_posture_documented(workflow_text, posture_term):
    assert posture_term in workflow_text


def test_branch_policy_does_not_claim_settings_changed(workflow_text):
    normalized = workflow_text.lower()
    assert "this phase does not change any of these settings" in normalized


# --- 4. AI participation model ---------------------------------------------------


def test_ai_participation_section_present(workflow_text):
    assert "AI Participation Model" in workflow_text


@pytest.mark.parametrize("allowed", AI_MAY)
def test_ai_may_list_item_present(workflow_text, allowed):
    assert allowed.lower() in workflow_text.lower()


@pytest.mark.parametrize("forbidden", AI_MAY_NOT)
def test_ai_may_not_list_item_present(workflow_text, forbidden):
    assert forbidden.lower() in workflow_text.lower()


def test_ai_participation_marked_not_implemented(workflow_text):
    assert "Current implementation status: Not implemented" in workflow_text


# --- 5. approval model: git approval vs execution approval -----------------------


def test_approval_model_section_present(workflow_text):
    assert "Approval Model" in workflow_text


def test_git_approval_defined(workflow_text):
    assert "Git Approval" in workflow_text


def test_execution_approval_defined(workflow_text):
    assert "Execution Approval" in workflow_text


def test_approval_model_distinguishes_git_and_execution(workflow_text):
    normalized = " ".join(workflow_text.split())
    assert "never interchangeable" in normalized or "distinct" in normalized
    assert "A merged PR is not an authorized execution" in normalized


def test_execution_approval_marked_not_implemented(workflow_text):
    idx = workflow_text.index("Execution Approval")
    following = workflow_text[idx:idx + 2000]
    assert "Not implemented" in following


# --- 6. PR requirements -----------------------------------------------------------


def test_pr_requirements_section_present(workflow_text):
    assert "PR Requirements" in workflow_text


@pytest.mark.parametrize("requirement", [
    "passing validation",
    "healthy governance",
    "clean task memory",
    "push readiness",
    "Review complete",
    "Conversations resolved",
    "Branch protection satisfied",
])
def test_pr_requirement_listed(workflow_text, requirement):
    assert requirement.lower() in workflow_text.lower()


# --- 7. governance mapping ---------------------------------------------------------


def test_governance_mapping_section_present(workflow_text):
    assert "Governance Mapping" in workflow_text


@pytest.mark.parametrize("command", GOVERNANCE_COMMANDS)
def test_governance_command_mapped(workflow_text, command):
    assert command in workflow_text


# --- 8. future integration ----------------------------------------------------------


def test_future_integration_section_present(workflow_text):
    assert "Future Integration" in workflow_text


@pytest.mark.parametrize("component", FUTURE_COMPONENTS)
def test_future_component_covered(workflow_text, component):
    assert component in workflow_text


def test_future_integration_is_design_only(workflow_text):
    idx = workflow_text.index("Future Integration")
    following = workflow_text[idx:idx + 400]
    assert "design only" in following.lower()


# --- 9. current status: everything future marked not implemented -----------------


def test_current_status_section_present(workflow_text):
    assert "Current Status" in workflow_text


def test_current_status_table_marks_capabilities_not_implemented(workflow_text):
    idx = workflow_text.index("## 9. Current Status")
    following = workflow_text[idx:idx + 3000]
    assert following.count("Not implemented") >= 10


# --- no execution / automation claims ------------------------------------------------


@pytest.mark.parametrize("phrase", NON_GOAL_PHRASES)
def test_non_goal_phrase_present(workflow_text, phrase):
    assert phrase in workflow_text


@pytest.mark.parametrize("claim", FORBIDDEN_CLAIMS)
def test_workflow_doc_does_not_make_forbidden_claim(workflow_text, claim):
    assert claim not in workflow_text.lower()


@pytest.mark.parametrize("claim", FORBIDDEN_CLAIMS)
def test_phase_doc_does_not_make_forbidden_claim(phase_doc_text, claim):
    assert claim not in phase_doc_text.lower()


def test_workflow_doc_v0_1_non_executing_preserved(workflow_text):
    assert "v0.1.0-rc1" in workflow_text
    assert "non-executing" in workflow_text.lower()


# --- recommends next phase ------------------------------------------------------------


def test_workflow_doc_recommends_108a(workflow_text):
    normalized = " ".join(workflow_text.split())
    assert "108A" in normalized
    assert "Permission Broker Enforcement Implementation" in normalized


def test_phase_doc_recommends_108a(phase_doc_text):
    normalized = " ".join(phase_doc_text.split())
    assert "108A" in normalized
    assert "Permission Broker Enforcement Implementation" in normalized


# --- phase doc cross-references ---------------------------------------------------------


def test_phase_doc_references_107b_107c_107d(phase_doc_text):
    for ref in ("107B", "107C", "107D"):
        assert ref in phase_doc_text


def test_phase_doc_references_autonomy_contract(phase_doc_text):
    assert "V0_2_AUTONOMY_CONTRACT.md" in phase_doc_text


def test_phase_doc_references_no_go_gates(phase_doc_text):
    assert "V0_2_EXECUTION_READINESS_NO_GO_GATES.md" in phase_doc_text
