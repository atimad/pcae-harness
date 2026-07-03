"""Tests for Phase 110B — Runtime Plugin Contract Freeze.

This is a pure documentation-verification suite. Phase 110B is a
contract/freeze phase: it turns the ten plugin categories 110A named
into stable contracts (eighteen standard fields, capability taxonomy,
lifecycle states, compatibility/versioning rules, security boundaries)
and adds long-term runtime vision language to the roadmap, without
implementing plugin loading, a plugin registry, dependency injection, or
any runtime execution. There is no runtime code to unit-test -- these
tests verify the documents exist, contain the required frozen content,
make no implementation claims, and that the roadmap vision language is
present as specified.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_PLUGIN_CONTRACTS.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_110_RUNTIME_PLUGIN_CONTRACT_FREEZE.md"
ROADMAP_DOC = REPO_ROOT / "docs" / "ROADMAP.md"
RUNTIME_ARCH_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_ARCHITECTURE.md"


@pytest.fixture(scope="module")
def contracts_text() -> str:
    return CONTRACTS_DOC.read_text()


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC.read_text()


@pytest.fixture(scope="module")
def roadmap_text() -> str:
    return ROADMAP_DOC.read_text()


def _normalized(text: str) -> str:
    """Collapse markdown line-wrap whitespace so a multi-word phrase can
    be matched even when it happens to straddle a hard-wrapped line."""
    return re.sub(r"\s+", " ", text)


# ═══════════════════════════════════════════════════════════════════════
# Documents exist
# ═══════════════════════════════════════════════════════════════════════


def test_plugin_contract_document_exists():
    assert CONTRACTS_DOC.exists()
    assert CONTRACTS_DOC.stat().st_size > 0


def test_phase_110b_document_exists():
    assert PHASE_DOC.exists()
    assert PHASE_DOC.stat().st_size > 0


def test_roadmap_document_exists():
    assert ROADMAP_DOC.exists()
    assert ROADMAP_DOC.stat().st_size > 0


# ═══════════════════════════════════════════════════════════════════════
# All 10 plugin categories are defined
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
def test_plugin_category_contract_defined(contracts_text, category):
    assert category in contracts_text


def test_exactly_ten_category_contract_sections(contracts_text):
    headers = re.findall(r"^### 2\.\d+ (.+)$", contracts_text, re.MULTILINE)
    assert len(headers) == 10


@pytest.mark.parametrize("field", [
    "Allowed responsibilities",
    "Forbidden responsibilities",
    "Input schema description",
    "Output schema description",
    "Lifecycle requirements",
    "Security/no-go constraints",
    "Failure behavior",
    "Current status",
])
def test_every_category_has_required_contract_fields(contracts_text, field):
    count = contracts_text.count(f"**{field}:**")
    assert count >= 10, f"expected '{field}' at least 10 times, found {count}"


def test_plugin_categories_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    for category in PLUGIN_CATEGORIES:
        assert category in text


# ═══════════════════════════════════════════════════════════════════════
# Standard contract fields (18) are defined
# ═══════════════════════════════════════════════════════════════════════

STANDARD_CONTRACT_FIELDS = (
    "Plugin ID",
    "Plugin type",
    "Purpose",
    "Responsibilities",
    "Inputs",
    "Outputs",
    "Lifecycle hooks",
    "Capability declaration",
    "Configuration model",
    "Health reporting",
    "Versioning",
    "Compatibility rules",
    "Security boundaries",
    "Evidence requirements",
    "Failure behavior",
    "Approval requirements",
    "Audit expectations",
    "Current implementation status",
)


@pytest.mark.parametrize("field", STANDARD_CONTRACT_FIELDS)
def test_standard_contract_field_documented(contracts_text, field):
    assert field in contracts_text


def test_exactly_eighteen_standard_fields(contracts_text):
    section_match = re.search(r"## 1\. Canonical Plugin Contract Model\n(.*?)\n## 2\.", contracts_text, re.DOTALL)
    assert section_match is not None
    section = section_match.group(1)
    rows = re.findall(r"^\| \d+ \| \*\*", section, re.MULTILINE)
    assert len(rows) == 18


def test_standard_fields_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    for field in ("Plugin ID", "Plugin type", "Purpose", "Responsibilities", "Inputs", "Outputs",
                  "Lifecycle hooks", "Capability declaration", "Configuration model", "Health reporting",
                  "Versioning", "Compatibility rules", "Security boundaries", "Evidence requirements",
                  "Failure behavior", "Approval requirements", "Audit expectations",
                  "Current implementation status"):
        assert field in text


# ═══════════════════════════════════════════════════════════════════════
# Capability taxonomy exists
# ═══════════════════════════════════════════════════════════════════════

CAPABILITY_CLASSES = (
    "observe",
    "advise",
    "approve",
    "deny",
    "enforce",
    "execute",
    "audit",
    "notify",
    "store",
    "rollback_prepare",
)


def test_capability_taxonomy_section_exists(contracts_text):
    assert "Plugin Capability Taxonomy" in contracts_text


@pytest.mark.parametrize("capability", CAPABILITY_CLASSES)
def test_capability_class_documented(contracts_text, capability):
    assert f"`{capability}`" in contracts_text


def test_capability_taxonomy_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    for capability in CAPABILITY_CLASSES:
        assert f"`{capability}`" in text


# ═══════════════════════════════════════════════════════════════════════
# Lifecycle states exist
# ═══════════════════════════════════════════════════════════════════════

LIFECYCLE_STATES = (
    "defined",
    "registered",
    "configured",
    "healthy",
    "available",
    "disabled",
    "failed",
    "retired",
)


def test_lifecycle_states_section_exists(contracts_text):
    assert "Plugin Lifecycle States" in contracts_text


@pytest.mark.parametrize("state", LIFECYCLE_STATES)
def test_lifecycle_state_documented(contracts_text, state):
    assert f"`{state}`" in contracts_text


def test_lifecycle_state_order_preserved(contracts_text):
    section_match = re.search(r"## 4\. Plugin Lifecycle States\n.*?```\n(.*?)```", contracts_text, re.DOTALL)
    assert section_match is not None
    diagram = section_match.group(1)
    positions = [diagram.index(state) for state in LIFECYCLE_STATES]
    assert positions == sorted(positions)


def test_lifecycle_states_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    for state in LIFECYCLE_STATES:
        assert f"`{state}" in text or state in text


# ═══════════════════════════════════════════════════════════════════════
# Compatibility / versioning rules exist
# ═══════════════════════════════════════════════════════════════════════


def test_compatibility_versioning_section_exists(contracts_text):
    assert "Compatibility and Versioning Rules" in contracts_text


@pytest.mark.parametrize("term", [
    "semantic version",
    "backward compat",
    "contract evolution",
    "deprecat",
    "110A",
])
def test_compatibility_versioning_terms_present(contracts_text, term):
    assert term.lower() in contracts_text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Security boundaries exist
# ═══════════════════════════════════════════════════════════════════════

SECURITY_BOUNDARIES = (
    "fail-closed",
    "least privilege",
    "no implicit execution",
    "no self-authorization",
    "no hidden network access",
    "no secret leakage",
    "no untracked mutation",
    "no bypass of human approval",
    "no bypass of the permission broker",
    "no bypass of audit",
)


def test_security_boundaries_section_exists(contracts_text):
    assert "Security Boundaries" in contracts_text


@pytest.mark.parametrize("boundary", SECURITY_BOUNDARIES)
def test_security_boundary_documented(contracts_text, boundary):
    assert boundary in contracts_text.lower()


def test_security_boundaries_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text).lower()
    for boundary in ("fail-closed", "least privilege", "no implicit execution", "no self-authorization",
                      "no hidden network access", "no secret leakage", "no untracked mutation",
                      "no bypass of human approval", "no bypass of the permission broker",
                      "no bypass of audit"):
        assert boundary in text


# ═══════════════════════════════════════════════════════════════════════
# Long-term runtime vision present in roadmap
# ═══════════════════════════════════════════════════════════════════════


def test_long_term_runtime_vision_section_exists(roadmap_text):
    assert "Long-Term Runtime Vision" in roadmap_text


@pytest.mark.parametrize("phrase", [
    "governed automation runtime",
    "modular",
    "pluggable",
    "connected",
    "observable",
    "automatable",
    "governed",
])
def test_vision_qualities_present(roadmap_text, phrase):
    assert phrase.lower() in roadmap_text.lower()


@pytest.mark.parametrize("intent_source", ["Claude", "Codex", "DeepSeek", "Telegram"])
def test_intent_source_examples_present(roadmap_text, intent_source):
    assert intent_source in roadmap_text


@pytest.mark.parametrize("execution_target", ["shell", "git", "filesystem", "backend agents", "network calls", "cloud runners"])
def test_execution_target_examples_present(roadmap_text, execution_target):
    assert execution_target in roadmap_text.lower()


def test_runtime_does_not_privilege_any_agent(roadmap_text):
    text = _normalized(roadmap_text).lower()
    assert "does not privilege any one agent or execution mechanism" in text


def test_execution_is_not_the_center_statement_present(roadmap_text):
    text = _normalized(roadmap_text)
    assert "Execution is not the center of PCAE" in text
    assert "Execution is one governed plugin capability inside the runtime" in text


def test_pluggable_first_ordering_present(roadmap_text):
    text = _normalized(roadmap_text)
    assert "Pluggable first" in text
    assert "Connected second" in text
    assert "Automated third" in text
    assert "Executable last" in text


def test_pluggable_first_ordering_present_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Pluggable first" in text
    assert "Connected second" in text
    assert "Automated third" in text
    assert "Executable last" in text


# ═══════════════════════════════════════════════════════════════════════
# Current maximum capability is Observed / observe only
# ═══════════════════════════════════════════════════════════════════════


def test_current_maximum_capability_is_observe_only(contracts_text):
    text = _normalized(contracts_text)
    assert "Current maximum capability actually exercised by any real PCAE code path today: `observe`" in text


def test_enforce_and_execute_marked_undeclarable(contracts_text):
    text = contracts_text.lower()
    assert "no plugin, category, or code path may declare `enforce` or `execute` today" in text \
        or "enforce" in text and "execute" in text and "undeclarable" in text


@pytest.mark.parametrize("doc_text_fixture", ["contracts_text", "phase_doc_text"])
def test_execution_unavailable_documented(request, doc_text_fixture):
    text = _normalized(request.getfixturevalue(doc_text_fixture))
    assert "Execution unavailable" in text or "execution_unavailable" in text


def test_current_maximum_runtime_state_still_observed(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Current maximum runtime state" in text
    assert "**Observed**" in text


# ═══════════════════════════════════════════════════════════════════════
# No implementation claims
# ═══════════════════════════════════════════════════════════════════════

FORBIDDEN_IMPLEMENTATION_CLAIMS = (
    "plugin loading implemented",
    "plugin registry implemented",
    "dependency injection framework implemented",
    "runtime execution enabled",
    "execution capability implemented",
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


@pytest.mark.parametrize("doc_path", [CONTRACTS_DOC, PHASE_DOC])
@pytest.mark.parametrize("claim", FORBIDDEN_IMPLEMENTATION_CLAIMS)
def test_no_forbidden_implementation_claims(doc_path, claim):
    text = doc_path.read_text().lower()
    assert claim not in text


@pytest.mark.parametrize("doc_path", [CONTRACTS_DOC, PHASE_DOC])
def test_no_plugin_loading_implementation_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No plugin loading" in text


@pytest.mark.parametrize("doc_path", [CONTRACTS_DOC, PHASE_DOC])
def test_no_execution_capability_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No execution capability" in text


@pytest.mark.parametrize("doc_path", [CONTRACTS_DOC, PHASE_DOC])
def test_no_go_confirmations_section_present(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No-Go Confirmations" in text
    assert "No runtime execution" in text


# ═══════════════════════════════════════════════════════════════════════
# Next phase recommendation exists
# ═══════════════════════════════════════════════════════════════════════


def test_recommended_next_phase_is_110c(contracts_text, phase_doc_text):
    for text in (contracts_text, phase_doc_text):
        assert "110C" in text
        assert "Runtime Plugin Registry Design" in text


# ═══════════════════════════════════════════════════════════════════════
# No runtime implementation added anywhere in the source tree
# ═══════════════════════════════════════════════════════════════════════


def test_no_plugin_directory_added():
    assert not (REPO_ROOT / "src" / "pcae" / "plugins").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "runtime").exists()


def test_no_runtime_module_added_to_core():
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    forbidden_names = {"runtime.py", "pcae_runtime.py", "plugin_registry.py", "plugin_loader.py", "plugin_contract.py"}
    existing = {p.name for p in core_dir.glob("*.py")}
    assert not (forbidden_names & existing)


def test_task_contract_excludes_src_pcae():
    """This phase's task contract must not list any src/pcae/ file as
    allowed -- confirming the contract-only boundary was respected at
    the governance layer, not just by convention."""
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-110b*"))
    if not matches:
        pytest.skip("110B task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    assert "src/pcae/" not in contract_text


def test_integration_registry_still_has_exactly_four_entries():
    """This phase's docs reference the existing 4 observation
    integrations without adding a 5th -- confirmed directly."""
    from pcae.core.command_path_observation import INTEGRATION_REGISTRY
    assert len(INTEGRATION_REGISTRY) == 4


def test_permission_broker_foundation_unchanged_by_this_phase():
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


def test_runtime_architecture_doc_still_present_and_referenced(contracts_text):
    """110A's docs must still exist and this phase's contracts document
    must reference them (compatibility, not replacement)."""
    assert RUNTIME_ARCH_DOC.exists()
    assert "PCAE_RUNTIME_ARCHITECTURE.md" in contracts_text or "110A" in contracts_text
