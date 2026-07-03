"""Tests for Phase 110D — Runtime Registry Contract Freeze & Resolution
Semantics.

This is a pure documentation-verification suite. Phase 110D is a
contract/freeze phase: it freezes the canonical Runtime Registry API,
capability resolution semantics, plugin selection rules, lifecycle
expectations, compatibility guarantees, and failure behavior -- without
implementing a registry, plugin loading, discovery execution, or any
runtime execution. There is no runtime code to unit-test -- these tests
verify the documents exist, contain the required frozen content, make
no implementation claims, and that the resolution/selection/
compatibility/failure vocabularies are present as specified.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_REGISTRY_CONTRACT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_110_RUNTIME_REGISTRY_CONTRACT_FREEZE.md"


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_DOC.read_text()


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


def test_registry_contract_document_exists():
    assert CONTRACT_DOC.exists()
    assert CONTRACT_DOC.stat().st_size > 0


def test_phase_110d_document_exists():
    assert PHASE_DOC.exists()
    assert PHASE_DOC.stat().st_size > 0


# ═══════════════════════════════════════════════════════════════════════
# Core architectural principle (unchanged, restated)
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_orchestrates_registry_resolves_plugins_implement(contract_text):
    text = _normalized(contract_text)
    assert "Runtime orchestrates." in text
    assert "Registry resolves." in text
    assert "Plugins implement." in text


def test_discoverable_always_principle_present(contract_text):
    text = _normalized(contract_text)
    assert "Pluggable first." in text
    assert "Connected second." in text
    assert "Automated third." in text
    assert "Executable last." in text
    assert "Discoverable always." in text


def test_single_authoritative_interface_documented(contract_text):
    text = _normalized(contract_text)
    assert "single authoritative service-resolution interface" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Canonical Registry API frozen
# ═══════════════════════════════════════════════════════════════════════

REGISTRY_API_OPERATIONS = (
    "RegisterPlugin()",
    "UnregisterPlugin()",
    "DiscoverCapabilities()",
    "ResolveCapability()",
    "ListPlugins()",
    "GetPluginMetadata()",
    "GetPluginHealth()",
    "ValidateCompatibility()",
    "ListCapabilityProviders()",
)


def test_canonical_registry_api_section_exists(contract_text):
    assert "## 2. Canonical Registry API" in contract_text


@pytest.mark.parametrize("operation", REGISTRY_API_OPERATIONS)
def test_registry_api_operation_documented(contract_text, operation):
    assert operation in contract_text


def test_registry_api_summarized_in_phase_doc(phase_doc_text):
    for operation in REGISTRY_API_OPERATIONS:
        assert operation in phase_doc_text


def test_registry_api_is_design_only(contract_text):
    text = _normalized(contract_text)
    assert "Design-only." in text


# ═══════════════════════════════════════════════════════════════════════
# Capability namespace conventions frozen
# ═══════════════════════════════════════════════════════════════════════

CAPABILITY_NAMESPACES = (
    "intent.receive",
    "intent.plan",
    "policy.evaluate",
    "decision.observe",
    "decision.advise",
    "approval.request",
    "approval.record",
    "execution.shell",
    "execution.git",
    "execution.backend",
    "execution.filesystem",
    "audit.write",
    "audit.verify",
    "notification.send",
    "storage.read",
    "storage.write",
    "identity.resolve",
    "context.session",
    "context.phase",
)


def test_capability_namespace_section_exists(contract_text):
    assert "## 3. Capability Namespace Conventions" in contract_text


@pytest.mark.parametrize("namespace", CAPABILITY_NAMESPACES)
def test_capability_namespace_documented(contract_text, namespace):
    assert namespace in contract_text


def test_capability_namespace_summarized_in_phase_doc(phase_doc_text):
    for namespace in CAPABILITY_NAMESPACES:
        assert namespace in phase_doc_text


# ═══════════════════════════════════════════════════════════════════════
# Resolution semantics frozen
# ═══════════════════════════════════════════════════════════════════════

RESOLUTION_OUTCOMES = (
    "Resolved",
    "MultipleCandidates",
    "NoProvider",
    "Incompatible",
    "Disabled",
    "Unavailable",
    "HealthRejected",
    "VersionRejected",
    "PolicyRejected",
)


def test_resolution_semantics_section_exists(contract_text):
    assert "## 4. Resolution Semantics" in contract_text


@pytest.mark.parametrize("outcome", RESOLUTION_OUTCOMES)
def test_resolution_outcome_documented(contract_text, outcome):
    assert outcome in contract_text


def test_resolution_semantics_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "resolution semantics" in text
    assert "nine resolution outcomes" in text or "9 resolution outcomes" in text


# ═══════════════════════════════════════════════════════════════════════
# Plugin selection semantics frozen
# ═══════════════════════════════════════════════════════════════════════

SELECTION_STRATEGIES = (
    "HighestPriority",
    "HighestVersion",
    "Healthiest",
    "PolicyPreferred",
    "UserPreferred",
    "ManualSelection",
    "FirstCompatible",
)


def test_selection_semantics_section_exists(contract_text):
    assert "## 5. Plugin Selection Semantics" in contract_text


@pytest.mark.parametrize("strategy", SELECTION_STRATEGIES)
def test_selection_strategy_documented(contract_text, strategy):
    assert strategy in contract_text


def test_selection_strategies_summarized_in_phase_doc(phase_doc_text):
    for strategy in SELECTION_STRATEGIES:
        assert strategy in phase_doc_text


def test_registry_never_selects_among_candidates(contract_text):
    text = _normalized(contract_text)
    assert "the Runtime — never the Registry" in text or "never the Registry" in text


# ═══════════════════════════════════════════════════════════════════════
# Compatibility rules frozen
# ═══════════════════════════════════════════════════════════════════════

COMPATIBILITY_DIMENSIONS = (
    "Runtime version",
    "Plugin version",
    "Manifest version",
    "Contract version",
    "Capability version",
)


def test_compatibility_rules_section_exists(contract_text):
    assert "## 6. Compatibility Rules" in contract_text


@pytest.mark.parametrize("dimension", COMPATIBILITY_DIMENSIONS)
def test_compatibility_dimension_documented(contract_text, dimension):
    assert dimension in contract_text


def test_future_migration_policy_named_as_open_question(contract_text):
    text = _normalized(contract_text)
    assert "Future migration policy" in text
    assert "not defined by this document" in text.lower() or "not defined here" in text.lower()


def test_compatibility_rules_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "compatibility rules" in text
    assert "migration policy" in text


# ═══════════════════════════════════════════════════════════════════════
# Plugin lifecycle interaction frozen (observation only)
# ═══════════════════════════════════════════════════════════════════════

LIFECYCLE_STATES_OBSERVED = (
    "Registered",
    "Available",
    "Unavailable",
    "Disabled",
    "Deprecated",
    "Removed",
)


def test_lifecycle_interaction_section_exists(contract_text):
    assert "## 7. Plugin Lifecycle Interaction" in contract_text


@pytest.mark.parametrize("state", LIFECYCLE_STATES_OBSERVED)
def test_lifecycle_state_documented(contract_text, state):
    assert state in contract_text


def test_registry_never_executes_lifecycle(contract_text):
    text = _normalized(contract_text)
    assert "Registry never executes lifecycle" in text


# ═══════════════════════════════════════════════════════════════════════
# Registry / Runtime / Plugin responsibilities restated as contract
# ═══════════════════════════════════════════════════════════════════════

REGISTRY_OWNS = (
    "Registration metadata",
    "Discovery",
    "Capability lookup",
    "Compatibility evaluation",
    "Plugin metadata",
    "Plugin health visibility",
    "Availability visibility",
)

REGISTRY_DOES_NOT_OWN = (
    "Execution",
    "Orchestration",
    "Approval",
    "Policy",
    "Audit persistence",
    "Rollback",
)

RUNTIME_OWNS = (
    "Orchestration",
    "Workflow progression",
    "Policy invocation",
    "Approval invocation",
    "Plugin invocation",
    "State transitions",
    "Registry interaction",
)

RUNTIME_DOES_NOT_OWN = (
    "Plugin metadata",
    "Capability storage",
    "Plugin discovery",
)

PLUGINS_OWN = (
    "Declared capabilities",
    "Bounded implementation",
    "Health reporting",
    "Manifest",
    "Version",
    "Local lifecycle",
)

PLUGINS_DO_NOT_OWN = (
    "Global orchestration",
    "Global discovery",
    "Authorization",
    "Approval bypass",
    "Registry modification",
)


def test_registry_responsibilities_section_exists(contract_text):
    assert "## 8. Registry Responsibilities" in contract_text
    assert "**The Registry owns:**" in contract_text
    assert "**The Registry does not own:**" in contract_text


@pytest.mark.parametrize("item", REGISTRY_OWNS)
def test_registry_owns_item_documented(contract_text, item):
    assert item in contract_text


@pytest.mark.parametrize("item", REGISTRY_DOES_NOT_OWN)
def test_registry_does_not_own_item_documented(contract_text, item):
    assert item in contract_text


def test_runtime_responsibilities_section_exists(contract_text):
    assert "## 9. Runtime Responsibilities" in contract_text
    assert "**The Runtime owns:**" in contract_text
    assert "**The Runtime never owns:**" in contract_text


@pytest.mark.parametrize("item", RUNTIME_OWNS)
def test_runtime_owns_item_documented(contract_text, item):
    assert item in contract_text


@pytest.mark.parametrize("item", RUNTIME_DOES_NOT_OWN)
def test_runtime_does_not_own_item_documented(contract_text, item):
    assert item in contract_text


def test_plugin_responsibilities_section_exists(contract_text):
    assert "## 10. Plugin Responsibilities" in contract_text
    assert "**Plugins own:**" in contract_text
    assert "**Plugins never own:**" in contract_text


@pytest.mark.parametrize("item", PLUGINS_OWN)
def test_plugins_own_item_documented(contract_text, item):
    assert item in contract_text


@pytest.mark.parametrize("item", PLUGINS_DO_NOT_OWN)
def test_plugins_do_not_own_item_documented(contract_text, item):
    assert item in contract_text


def test_responsibilities_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Registry, Runtime, and Plugin responsibilities" in text


# ═══════════════════════════════════════════════════════════════════════
# Failure behavior frozen
# ═══════════════════════════════════════════════════════════════════════

FAILURE_SCENARIOS = (
    "No provider",
    "Multiple providers",
    "Registry unavailable",
    "Manifest invalid",
    "Compatibility failure",
)

FAILURE_CONSEQUENCES = (
    "No execution.",
    "No automatic execution.",
    "Execution unavailable.",
    "Plugin unavailable.",
)


def test_failure_behavior_section_exists(contract_text):
    assert "## 11. Failure Behavior" in contract_text


@pytest.mark.parametrize("scenario", FAILURE_SCENARIOS)
def test_failure_scenario_documented(contract_text, scenario):
    assert scenario in contract_text


@pytest.mark.parametrize("consequence", FAILURE_CONSEQUENCES)
def test_failure_consequence_documented(contract_text, consequence):
    text = _normalized(contract_text)
    assert consequence in text


def test_failure_behavior_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "failure behavior" in text
    assert "less" in text and "execution capability" in text


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable explicitly stated
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("doc_text_fixture", ["contract_text", "phase_doc_text"])
def test_execution_unavailable_documented(request, doc_text_fixture):
    text = _normalized(request.getfixturevalue(doc_text_fixture))
    assert "Execution unavailable" in text or "execution_unavailable" in text


def test_current_maximum_runtime_state_still_observed(contract_text, phase_doc_text):
    for text in (contract_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum runtime state" in normalized
        assert "Observed" in normalized


def test_current_maximum_plugin_capability_still_observe(contract_text, phase_doc_text):
    for text in (contract_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum plugin capability" in normalized
        assert "`observe`" in normalized or "observe" in normalized


# ═══════════════════════════════════════════════════════════════════════
# No implementation claims
# ═══════════════════════════════════════════════════════════════════════

FORBIDDEN_IMPLEMENTATION_CLAIMS = (
    "registry implemented",
    "plugin loading implemented",
    "plugin discovery execution implemented",
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


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
@pytest.mark.parametrize("claim", FORBIDDEN_IMPLEMENTATION_CLAIMS)
def test_no_forbidden_implementation_claims(doc_path, claim):
    text = doc_path.read_text().lower()
    assert claim not in text


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
def test_no_plugin_loading_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No plugin loading" in text


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
def test_no_registry_implementation_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No registry implementation" in text


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
def test_no_dependency_injection_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No dependency injection framework" in text


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
def test_no_go_confirmations_section_present(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No-Go Confirmations" in text
    assert "No runtime execution" in text


# ═══════════════════════════════════════════════════════════════════════
# Next phase recommendation exists
# ═══════════════════════════════════════════════════════════════════════


def test_recommended_next_phase_is_110e(contract_text, phase_doc_text):
    for text in (contract_text, phase_doc_text):
        assert "110E" in text
        assert "Runtime Registry Prototype" in text
        assert "Observation-Only" in text


# ═══════════════════════════════════════════════════════════════════════
# No runtime implementation added anywhere in the source tree
# ═══════════════════════════════════════════════════════════════════════


def test_no_registry_module_added_to_core():
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    forbidden_names = {
        "runtime.py", "pcae_runtime.py", "plugin_registry.py", "plugin_loader.py",
        "plugin_contract.py", "service_registry.py", "plugin_manifest.py",
        "plugin_discovery.py", "capability_resolution.py", "registry_contract.py",
        "capability_registry_resolver.py",
    }
    existing = {p.name for p in core_dir.glob("*.py")}
    assert not (forbidden_names & existing)


def test_no_plugin_or_runtime_directory_added():
    assert not (REPO_ROOT / "src" / "pcae" / "plugins").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "runtime").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "registry").exists()


def test_task_contract_excludes_src_pcae():
    """This phase's task contract must not list any src/pcae/ file as
    allowed -- confirming the contract-only boundary was respected at
    the governance layer, not just by convention."""
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-110d*"))
    if not matches:
        pytest.skip("110D task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text_on_disk = matches[0].read_text()
    assert "src/pcae/" not in contract_text_on_disk
