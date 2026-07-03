"""Tests for Phase 110A — PCAE Runtime Architecture & Plugin Model.

This is a pure documentation-verification suite. Phase 110A is an
architecture/freeze phase: it defines the canonical PCAE Runtime,
pipeline, plugin model, services, interfaces, principles, capability
matrix, and state model in three new documents, and touches no file
under `src/pcae/`. There is no runtime code to unit-test -- these tests
verify the documents exist, contain the required frozen content, make
no implementation claims, and that no runtime implementation was
introduced anywhere in the source tree.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_ARCH_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_ARCHITECTURE.md"
PLUGIN_MODEL_DOC = REPO_ROOT / "docs" / "PCAE_PLUGIN_MODEL.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_110_RUNTIME_ARCHITECTURE.md"


@pytest.fixture(scope="module")
def runtime_arch_text() -> str:
    return RUNTIME_ARCH_DOC.read_text()


@pytest.fixture(scope="module")
def plugin_model_text() -> str:
    return PLUGIN_MODEL_DOC.read_text()


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC.read_text()


def _normalized(text: str) -> str:
    """Collapse markdown line-wrap whitespace so a multi-word phrase can
    be matched even when it happens to straddle a hard-wrapped line."""
    return re.sub(r"\s+", " ", text)


# ═══════════════════════════════════════════════════════════════════════
# Documents exist
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_architecture_document_exists():
    assert RUNTIME_ARCH_DOC.exists()
    assert RUNTIME_ARCH_DOC.stat().st_size > 0


def test_plugin_model_document_exists():
    assert PLUGIN_MODEL_DOC.exists()
    assert PLUGIN_MODEL_DOC.stat().st_size > 0


def test_phase_110_document_exists():
    assert PHASE_DOC.exists()
    assert PHASE_DOC.stat().st_size > 0


# ═══════════════════════════════════════════════════════════════════════
# Runtime pipeline documented
# ═══════════════════════════════════════════════════════════════════════

PIPELINE_STAGES = (
    "Intent Source",
    "Runtime",
    "Intent Pipeline",
    "Decision Pipeline",
    "Execution Adapter",
    "Evidence Pipeline",
    "Notification Pipeline",
)


@pytest.mark.parametrize("stage", PIPELINE_STAGES)
def test_runtime_pipeline_stage_documented(runtime_arch_text, stage):
    assert stage in runtime_arch_text


def test_runtime_pipeline_order_preserved(runtime_arch_text):
    """The seven stages must appear in the frozen order, within the
    pipeline diagram itself (the stage names also appear individually
    elsewhere in the document, e.g. in the section header, so the
    search is scoped to the diagram's own fenced code block)."""
    section_match = re.search(r"## 2\. The Runtime Pipeline\n.*?```\n(.*?)```", runtime_arch_text, re.DOTALL)
    assert section_match is not None
    diagram = section_match.group(1)
    positions = [diagram.index(stage) for stage in PIPELINE_STAGES]
    assert positions == sorted(positions)


def test_runtime_pipeline_summarized_in_phase_doc(phase_doc_text):
    for stage in PIPELINE_STAGES:
        assert stage in phase_doc_text


# ═══════════════════════════════════════════════════════════════════════
# Plugin categories documented
# ═══════════════════════════════════════════════════════════════════════

PLUGIN_CATEGORIES = (
    "Intent Source Plugin",
    "Policy Plugin",
    "Decision Plugin",
    "Approval Plugin",
    "Execution Adapter Plugin",
    "Audit Plugin",
    "Notification Plugin",
    "Storage Plugin",
    "Identity Plugin",
    "Context Plugin",
)


@pytest.mark.parametrize("category", PLUGIN_CATEGORIES)
def test_plugin_category_documented(plugin_model_text, category):
    assert category in plugin_model_text


def test_exactly_ten_plugin_categories(plugin_model_text):
    headers = re.findall(r"^## \d+\. (.+)$", plugin_model_text, re.MULTILINE)
    assert len(headers) == 10


@pytest.mark.parametrize("field", ["Purpose", "Responsibilities", "Lifecycle", "Inputs", "Outputs", "Current Status", "Future Implementation Phase"])
def test_every_plugin_category_has_required_fields(plugin_model_text, field):
    """Each of the 7 required fields must appear at least 10 times (once
    per category)."""
    count = plugin_model_text.count(f"**{field}:**")
    assert count >= 10, f"expected field '{field}' at least 10 times, found {count}"


def test_plugin_categories_referenced_in_runtime_architecture(runtime_arch_text):
    for category in PLUGIN_CATEGORIES:
        assert category in runtime_arch_text


def test_plugin_categories_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    for category in PLUGIN_CATEGORIES:
        assert category in text


# ═══════════════════════════════════════════════════════════════════════
# Runtime services documented
# ═══════════════════════════════════════════════════════════════════════

RUNTIME_SERVICES = (
    "Session",
    "Task",
    "Phase",
    "Identity",
    "Configuration",
    "Plugin Registry",
    "Policy Registry",
    "Integration Registry",
    "Audit Registry",
)


@pytest.mark.parametrize("service", RUNTIME_SERVICES)
def test_runtime_service_documented(runtime_arch_text, service):
    assert service in runtime_arch_text


# ═══════════════════════════════════════════════════════════════════════
# Runtime principles documented
# ═══════════════════════════════════════════════════════════════════════

RUNTIME_PRINCIPLES = (
    "Modular",
    "Pluggable",
    "Connected",
    "Observable",
    "Automatable",
    "Governed",
    "Fail-closed",
    "Least privilege",
    "Human-controlled",
    "Deterministic",
    "Testable",
)


@pytest.mark.parametrize("principle", RUNTIME_PRINCIPLES)
def test_runtime_principle_documented(runtime_arch_text, principle):
    assert principle in runtime_arch_text


def test_exactly_eleven_principles(runtime_arch_text):
    section_match = re.search(r"## 6\. Runtime Principles\n(.*?)\n## 7\.", runtime_arch_text, re.DOTALL)
    assert section_match is not None
    section = section_match.group(1)
    numbered = re.findall(r"^\d+\.\s+\*\*", section, re.MULTILINE)
    assert len(numbered) == 11


def test_runtime_principles_summarized_in_phase_doc(phase_doc_text):
    for principle in RUNTIME_PRINCIPLES:
        assert principle in phase_doc_text


# ═══════════════════════════════════════════════════════════════════════
# Capability matrix exists
# ═══════════════════════════════════════════════════════════════════════


def test_capability_matrix_exists(runtime_arch_text):
    assert "Runtime Capability Matrix" in runtime_arch_text


@pytest.mark.parametrize("column", ["Current capability", "Future capability", "Implementation phase", "Current implementation status", "Expected maturity"])
def test_capability_matrix_has_required_columns(runtime_arch_text, column):
    assert column in runtime_arch_text


def test_capability_matrix_summarized_in_phase_doc(phase_doc_text):
    assert "Capability Matrix" in phase_doc_text


# ═══════════════════════════════════════════════════════════════════════
# Runtime state model documented
# ═══════════════════════════════════════════════════════════════════════

STATE_MODEL_STATES = (
    "Intent",
    "Observed",
    "Advisory",
    "Approved",
    "Executable",
    "Executed",
    "Audited",
    "Rollback Ready",
)


@pytest.mark.parametrize("state", STATE_MODEL_STATES)
def test_state_model_state_documented(runtime_arch_text, state):
    assert state in runtime_arch_text


def test_state_model_order_preserved(runtime_arch_text):
    section_match = re.search(r"## 8\. Runtime State Model\n(.*?)```\n(.*?)```", runtime_arch_text, re.DOTALL)
    assert section_match is not None
    diagram = section_match.group(2)
    positions = [diagram.index(state) for state in STATE_MODEL_STATES]
    assert positions == sorted(positions)


def test_state_model_summarized_in_phase_doc(phase_doc_text):
    for state in STATE_MODEL_STATES:
        assert state in phase_doc_text


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable explicitly documented
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("doc_text_fixture", ["runtime_arch_text", "plugin_model_text", "phase_doc_text"])
def test_execution_unavailable_documented(request, doc_text_fixture):
    text = _normalized(request.getfixturevalue(doc_text_fixture))
    assert "Execution unavailable" in text or "execution_unavailable" in text


def test_current_maximum_state_is_observed(runtime_arch_text):
    text = _normalized(runtime_arch_text)
    assert "Current maximum state reachable by any real PCAE command path today: `Observed`" in text


def test_execution_integration_status_present_in_phase_doc(phase_doc_text):
    for field in ["Observed command paths", "Behavior-changing paths", "Authorized paths", "Execution-capable paths", "Current execution capability"]:
        assert field in phase_doc_text
    assert "**4**" in phase_doc_text
    assert "**0**" in phase_doc_text


# ═══════════════════════════════════════════════════════════════════════
# No implementation claims
# ═══════════════════════════════════════════════════════════════════════

FORBIDDEN_IMPLEMENTATION_CLAIMS = (
    "runtime execution enabled",
    "execution capability implemented",
    "plugin loading implemented",
    "dependency injection framework implemented",
    "permission broker enforcement implemented",
    "audit persistence implemented",
    "rollback execution implemented",
    "emergency stop implemented",
    "telegram inbound implemented",
    "rest server implemented",
    "web server implemented",
    "daemon implemented",
    "background workers implemented",
    "automatic apply implemented",
    "command execution implemented",
)


@pytest.mark.parametrize("doc_path", [RUNTIME_ARCH_DOC, PLUGIN_MODEL_DOC, PHASE_DOC])
@pytest.mark.parametrize("claim", FORBIDDEN_IMPLEMENTATION_CLAIMS)
def test_no_forbidden_implementation_claims(doc_path, claim):
    text = doc_path.read_text().lower()
    assert claim not in text


@pytest.mark.parametrize("doc_path", [RUNTIME_ARCH_DOC, PLUGIN_MODEL_DOC, PHASE_DOC])
def test_no_go_confirmations_section_present(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No-Go Confirmations" in text
    assert "No runtime execution" in text


@pytest.mark.parametrize("doc_path", [RUNTIME_ARCH_DOC, PLUGIN_MODEL_DOC])
def test_no_go_confirmations_include_plugin_loading(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No plugin loading implementation" in text
    assert "No dependency injection framework" in text


def test_recommended_next_phase_is_110b(runtime_arch_text, plugin_model_text, phase_doc_text):
    for text in (runtime_arch_text, plugin_model_text, phase_doc_text):
        assert "110B" in text
        assert "Runtime Plugin Contract Freeze" in text


# ═══════════════════════════════════════════════════════════════════════
# No runtime implementation added anywhere in the source tree
# ═══════════════════════════════════════════════════════════════════════


def test_no_runtime_module_added_to_core():
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    forbidden_names = {"runtime.py", "pcae_runtime.py", "runtime_pipeline.py", "plugin_registry.py", "plugin_loader.py"}
    existing = {p.name for p in core_dir.glob("*.py")}
    assert not (forbidden_names & existing)


def test_no_plugin_directory_added():
    assert not (REPO_ROOT / "src" / "pcae" / "plugins").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "runtime").exists()


def test_no_new_cli_subcommand_for_runtime():
    cli_source = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text()
    assert '"runtime-architecture"' not in cli_source
    assert '"plugin-registry"' not in cli_source


def test_task_contract_excludes_src_pcae():
    """This phase's task contract must not list any src/pcae/ file as
    allowed -- confirming the architecture-only boundary was respected
    at the governance layer, not just by convention."""
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-110a*"))
    if not matches:
        pytest.skip("110A task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    assert "src/pcae/" not in contract_text


def test_permission_broker_foundation_unchanged_by_this_phase():
    """108A-108D's broker isolation guarantee must still hold -- this
    phase's docs describe it but must not have touched it."""
    import ast
    pbf_path = REPO_ROOT / "src" / "pcae" / "core" / "permission_broker_foundation.py"
    tree = ast.parse(pbf_path.read_text())
    allowed = {"__future__", "uuid", "dataclasses", "datetime"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] in allowed
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] in allowed


def test_integration_registry_still_has_exactly_four_entries():
    """This phase's docs reference the existing 4 observation
    integrations without adding a 5th -- confirmed directly."""
    from pcae.core.command_path_observation import INTEGRATION_REGISTRY
    assert len(INTEGRATION_REGISTRY) == 4
