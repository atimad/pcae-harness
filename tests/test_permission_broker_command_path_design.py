"""Tests for Phase 109A — Permission Broker Command-Path Integration Design.

Documentation-focused: verifies the frozen command-path integration
design document and its accompanying phase document exist and make the
required (and only the required) claims. No live network access.
Non-executing. Read-only file assertions — no subprocess invocation, no
shared .pcae/ artifact state, safe under pytest-xdist.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DESIGN_DOC_PATH = REPO_ROOT / "docs" / "V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md"
PHASE_DOC_PATH = REPO_ROOT / "docs" / "PHASE_109_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION_DESIGN.md"

PIPELINE_STAGES = [
    "AI Agent",
    "Permission Broker",
    "Command Boundary",
    "Execution Boundary",
    "Human Approval Gate",
    "Shell",
    "Audit Boundary",
    "Rollback Boundary",
]

COMMAND_CATEGORIES = [
    "Read-only",
    "Repository inspection",
    "Documentation mutation",
    "Source mutation",
    "Test execution",
    "Git lifecycle",
    "shell execution",
    "Backend invocation",
    "Adapter invocation",
    "Network",
    "High-risk",
]

INTEGRATION_POINTS = [
    "pcae commit implementation",
    "pcae push",
    "Shell mediation",
    "Subprocess mediation",
    "Backend invocation",
    "Adapter invocation",
    "Future execution API",
]

BROKER_CONTRACT_TERMS = [
    "Broker input",
    "Broker output",
    "Decision lifecycle",
    "Required metadata",
    "Policy evaluation order",
    "Failure behavior",
    "Audit expectations",
]

COMPATIBILITY_AREAS = [
    "Autonomy Contract",
    "No-Go Gates",
    "Local Governance",
    "Branch Protection",
    "Existing lifecycle commands",
]

FORBIDDEN_CLAIMS = [
    "execution is available",
    "execution is enabled",
    "broker is integrated",
    "broker is wired into",
    "pcae commit implementation now calls",
    "pcae push now calls",
    "shell mediation is implemented",
    "backend invocation is implemented",
    "execution capability is implemented",
]


@pytest.fixture(scope="module")
def design_text() -> str:
    return DESIGN_DOC_PATH.read_text()


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC_PATH.read_text()


# --- existence ---------------------------------------------------------------


def test_design_doc_exists():
    assert DESIGN_DOC_PATH.is_file()


def test_phase_doc_exists():
    assert PHASE_DOC_PATH.is_file()


def test_design_doc_not_empty(design_text):
    assert len(design_text.strip()) > 2000


def test_phase_doc_not_empty(phase_doc_text):
    assert len(phase_doc_text.strip()) > 500


# --- 1. canonical architecture / execution pipeline ---------------------------


def test_architecture_section_present(design_text):
    assert "Canonical Command-Path Integration Architecture" in design_text


@pytest.mark.parametrize("stage", PIPELINE_STAGES)
def test_pipeline_stage_present(design_text, stage):
    assert stage in design_text


def test_execution_pipeline_section_present(design_text):
    assert "## 5. Execution Pipeline" in design_text


def test_pipeline_order_preserved_in_architecture_diagram(design_text):
    start = design_text.index("## 1. Canonical Command-Path Integration Architecture")
    end = design_text.index("## 2. Command Categories")
    block = design_text[start:end]
    positions = [block.index(stage) for stage in PIPELINE_STAGES]
    assert positions == sorted(positions), "Pipeline stages are out of order"


def test_command_boundary_explicitly_not_a_component_id(design_text):
    normalized = " ".join(design_text.split())
    assert "not a new frozen component" in normalized or "not a standing component" in normalized.replace("service", "component")


# --- 2. command categories ------------------------------------------------------


def test_command_categories_section_present(design_text):
    assert "## 2. Command Categories" in design_text


@pytest.mark.parametrize("category", COMMAND_CATEGORIES)
def test_command_category_present(design_text, category):
    assert category in design_text


def test_command_categories_have_required_fields(design_text):
    start = design_text.index("## 2. Command Categories")
    end = design_text.index("## 3. Integration Points")
    block = design_text[start:end]
    for field in ("Risk level", "Broker involvement", "Future approval requirement", "Current implementation status"):
        assert field in block


def test_eleven_command_categories_frozen(design_text):
    start = design_text.index("## 2. Command Categories")
    end = design_text.index("## 3. Integration Points")
    block = design_text[start:end]
    assert block.count("Risk level:") == 11


# --- 3. integration points -------------------------------------------------------


def test_integration_points_section_present(design_text):
    assert "## 3. Integration Points" in design_text


@pytest.mark.parametrize("point", INTEGRATION_POINTS)
def test_integration_point_present(design_text, point):
    assert point in design_text


def test_integration_points_not_connected(design_text):
    start = design_text.index("## 3. Integration Points")
    end = design_text.index("## 4. Broker Interaction Contract")
    block = design_text[start:end]
    assert "is implemented, connected, or enabled by" in block


# --- 4. broker interaction contract -----------------------------------------------


def test_broker_contract_section_present(design_text):
    assert "## 4. Broker Interaction Contract" in design_text


@pytest.mark.parametrize("term", BROKER_CONTRACT_TERMS)
def test_broker_contract_term_present(design_text, term):
    assert term in design_text


def test_broker_contract_references_existing_models(design_text):
    assert "PermissionBrokerRequest" in design_text
    assert "PermissionBrokerDecision" in design_text


def test_broker_contract_fail_closed_stated(design_text):
    start = design_text.index("## 4. Broker Interaction Contract")
    end = design_text.index("## 5. Execution Pipeline")
    block = design_text[start:end]
    assert "fail-closed" in block.lower() or "fail closed" in block.lower()


# --- 5. execution pipeline (frozen, boundaries identified) ------------------------


def test_execution_pipeline_status_table_present(design_text):
    assert "foundation_implemented" in design_text
    assert "not_implemented" in design_text


def test_every_component_status_documented(design_text):
    for comp_id in ("COMP-001", "COMP-002", "COMP-003", "COMP-004", "COMP-005", "COMP-006", "COMP-007", "COMP-008"):
        assert comp_id in design_text


# --- 6. design compatibility ----------------------------------------------------------


def test_compatibility_section_present(design_text):
    assert "## 6. Design Compatibility" in design_text


@pytest.mark.parametrize("area", COMPATIBILITY_AREAS)
def test_compatibility_area_addressed(design_text, area):
    start = design_text.index("## 6. Design Compatibility")
    end = design_text.index("## 7. Repository Protection Implications")
    block = design_text[start:end]
    assert area in block


# --- 7. repository protection implications -----------------------------------------


def test_repository_protection_section_present(design_text):
    assert "## 7. Repository Protection Implications" in design_text


def test_repository_protection_addresses_required_questions(design_text):
    start = design_text.index("## 7. Repository Protection Implications")
    end = design_text.index("## Explicit Non-Goals")
    block = design_text[start:end]
    for phrase in (
        "strengthen repository", "differs from hooks", "differs from branch protection",
        "remains fail-closed",
    ):
        assert phrase in block.lower() or phrase.replace("-", " ") in block.lower(), f"missing: {phrase}"


# --- no implementation / execution claims -------------------------------------------


@pytest.mark.parametrize("claim", FORBIDDEN_CLAIMS)
def test_design_doc_does_not_claim_implementation(design_text, claim):
    assert claim not in design_text.lower()


@pytest.mark.parametrize("claim", FORBIDDEN_CLAIMS)
def test_phase_doc_does_not_claim_implementation(phase_doc_text, claim):
    assert claim not in phase_doc_text.lower()


def test_design_doc_states_no_implementation_boundary(design_text):
    normalized = " ".join(design_text.split())
    assert "design only" in normalized.lower() or "architecture/design only" in normalized.lower()


def test_design_doc_v0_1_non_executing_preserved(design_text):
    assert "v0.1.0-rc1" in design_text
    assert "non-executing" in design_text.lower()


def test_explicit_non_goals_section_present(design_text):
    assert "## Explicit Non-Goals" in design_text
    start = design_text.index("## Explicit Non-Goals")
    block = design_text[start:]
    for phrase in (
        "No broker command-path integration", "No runtime execution", "No shell mediation",
        "No subprocess mediation", "No backend invocation", "No adapter invocation",
        "No execution enablement", "No execution capability", "No audit persistence",
        "No rollback execution", "No emergency stop", "No Telegram inbound",
        "No automatic apply", "No command execution", "No Permission Broker enforcement",
        "No shell boundary implementation", "No backend boundary implementation",
    ):
        assert phrase in block


# --- recommends next phase ------------------------------------------------------------


def test_design_doc_recommends_109b(design_text):
    normalized = " ".join(design_text.split())
    assert "109B" in normalized
    assert "First Command-Path Integration Prototype" in normalized


def test_phase_doc_recommends_109b(phase_doc_text):
    normalized = " ".join(phase_doc_text.split())
    assert "109B" in normalized
    assert "First Command-Path Integration Prototype" in normalized


# --- phase doc cross-references ---------------------------------------------------------


def test_phase_doc_references_prior_phases(phase_doc_text):
    for ref in ("107B", "107C", "107E", "108A", "108D", "108E"):
        assert ref in phase_doc_text


def test_phase_doc_references_autonomy_contract(phase_doc_text):
    assert "V0_2_AUTONOMY_CONTRACT.md" in phase_doc_text


def test_phase_doc_references_no_go_gates(phase_doc_text):
    assert "V0_2_EXECUTION_READINESS_NO_GO_GATES.md" in phase_doc_text


def test_phase_doc_states_no_src_changes(phase_doc_text):
    normalized = phase_doc_text.lower()
    assert "no source code" in normalized
