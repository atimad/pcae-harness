"""Tests for Phase 110C — Runtime Service Registry & Plugin Discovery
Architecture.

This is a pure documentation-verification suite. Phase 110C is an
architecture/design phase: it designs how the Runtime discovers,
resolves, validates, and reasons about plugins without directly
coupling to concrete implementations -- without implementing a
registry, plugin loading, discovery execution, or any runtime
execution. There is no runtime code to unit-test -- these tests verify
the documents exist, contain the required frozen content, make no
implementation claims, and that the static/dynamic runtime distinction
is present as specified.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_SERVICE_REGISTRY.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_110_RUNTIME_SERVICE_REGISTRY_ARCHITECTURE.md"


@pytest.fixture(scope="module")
def registry_text() -> str:
    return REGISTRY_DOC.read_text()


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


def test_service_registry_document_exists():
    assert REGISTRY_DOC.exists()
    assert REGISTRY_DOC.stat().st_size > 0


def test_phase_110c_document_exists():
    assert PHASE_DOC.exists()
    assert PHASE_DOC.stat().st_size > 0


# ═══════════════════════════════════════════════════════════════════════
# Core architectural principle
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_orchestrates_registry_resolves_plugins_implement(registry_text):
    text = _normalized(registry_text)
    assert "Runtime orchestrates." in text
    assert "Registry resolves." in text
    assert "Plugins implement." in text


def test_discoverable_always_principle_present(registry_text):
    text = _normalized(registry_text)
    assert "Pluggable first." in text
    assert "Connected second." in text
    assert "Automated third." in text
    assert "Executable last." in text
    assert "Discoverable always." in text


def test_core_principle_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Runtime orchestrates" in text
    assert "Registry resolves" in text
    assert "Plugins implement" in text
    assert "Discoverable always" in text


# ═══════════════════════════════════════════════════════════════════════
# Service discovery model exists
# ═══════════════════════════════════════════════════════════════════════

DISCOVERY_FACETS = (
    "Plugin identity",
    "Plugin type",
    "Capability declarations",
    "Version compatibility",
    "Health status",
    "Lifecycle state",
    "Security posture",
    "Current implementation status",
)


def test_service_discovery_section_exists(registry_text):
    assert "## 2. Service Discovery" in registry_text


@pytest.mark.parametrize("facet", DISCOVERY_FACETS)
def test_discovery_facet_documented(registry_text, facet):
    assert facet in registry_text


def test_discovery_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    for facet in ("plugin identity", "plugin type", "capability declarations",
                  "version compatibility", "health status", "lifecycle state",
                  "security posture", "current implementation status"):
        assert facet in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Plugin manifest concept exists
# ═══════════════════════════════════════════════════════════════════════

MANIFEST_FIELDS = (
    "Plugin ID",
    "Plugin name",
    "Plugin type",
    "Version",
    "Compatible runtime version",
    "Capabilities provided",
    "Capabilities required",
    "Dependencies",
    "Lifecycle hooks",
    "Configuration schema",
    "Security boundaries",
    "Evidence requirements",
    "Approval requirements",
    "Audit expectations",
    "Current status",
)


def test_plugin_manifest_section_exists(registry_text):
    assert "Plugin Manifest Concept" in registry_text


@pytest.mark.parametrize("field", MANIFEST_FIELDS)
def test_manifest_field_documented(registry_text, field):
    assert field in registry_text


def test_manifest_is_future_no_implementation(registry_text):
    text = _normalized(registry_text)
    assert "No manifest schema, file format, parser, or loader is implemented" in text


def test_manifest_summarized_in_phase_doc(phase_doc_text):
    assert "manifest" in phase_doc_text.lower()
    assert "fifteen fields" in phase_doc_text.lower() or "15 fields" in phase_doc_text


# ═══════════════════════════════════════════════════════════════════════
# Capability resolution model exists
# ═══════════════════════════════════════════════════════════════════════


def test_capability_resolution_section_exists(registry_text):
    assert "## 4. Capability Resolution" in registry_text


@pytest.mark.parametrize("step", ["Intent:", "Runtime:", "Registry:", "Plugin:"])
def test_capability_resolution_flow_step_present(registry_text, step):
    assert step in registry_text


def test_capability_resolution_example_present(registry_text):
    text = _normalized(registry_text)
    assert "Run tests" in text
    assert "resolves compatible plugin candidates" in text


def test_capability_resolution_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "capability resolution" in text
    assert "five-step" in text or "5-step" in text or "five step" in text


# ═══════════════════════════════════════════════════════════════════════
# Registry responsibilities / non-responsibilities defined
# ═══════════════════════════════════════════════════════════════════════

REGISTRY_OWNS = (
    "Registration metadata",
    "Discovery",
    "Compatibility checks",
    "Capability lookup",
    "Plugin health visibility",
    "Lifecycle visibility",
    "Dependency metadata",
    "Current availability",
)

REGISTRY_DOES_NOT_OWN = (
    "Orchestration",
    "Policy decisions",
    "Approval decisions",
    "Execution",
    "Audit persistence",
    "Rollback execution",
)


def test_registry_responsibilities_section_exists(registry_text):
    assert "The Registry owns:" in registry_text
    assert "The Registry does not own:" in registry_text


@pytest.mark.parametrize("item", REGISTRY_OWNS)
def test_registry_owns_item_documented(registry_text, item):
    assert item in registry_text


@pytest.mark.parametrize("item", REGISTRY_DOES_NOT_OWN)
def test_registry_does_not_own_item_documented(registry_text, item):
    assert item in registry_text


def test_registry_responsibilities_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Registry owns:" in text
    assert "Registry does not own:" in text


# ═══════════════════════════════════════════════════════════════════════
# Plugin responsibility boundaries defined
# ═══════════════════════════════════════════════════════════════════════

PLUGINS_OWN = (
    "Declared capability implementation",
    "Local health signal",
    "Lifecycle hooks",
    "Bounded inputs/outputs",
    "Evidence emission",
)

PLUGINS_DO_NOT_OWN = (
    "Global orchestration",
    "Self-authorization",
    "Bypassing the Permission Broker",
    "Bypassing approval",
    "Bypassing audit",
    "Discovering or calling each other directly",
)


def test_plugin_boundaries_section_exists(registry_text):
    assert "**Plugins own:**" in registry_text
    assert "**Plugins do not own:**" in registry_text


@pytest.mark.parametrize("item", PLUGINS_OWN)
def test_plugins_own_item_documented(registry_text, item):
    assert item in registry_text


@pytest.mark.parametrize("item", PLUGINS_DO_NOT_OWN)
def test_plugins_do_not_own_item_documented(registry_text, item):
    assert item in registry_text


def test_plugin_boundaries_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Plugins own:" in text
    assert "Plugins do not own:" in text


# ═══════════════════════════════════════════════════════════════════════
# Infrastructure / capability plugin classes distinguished
# ═══════════════════════════════════════════════════════════════════════

INFRASTRUCTURE_PLUGINS = ("Identity Plugin", "Storage Plugin", "Notification Plugin", "Audit Plugin", "Context Plugin")
CAPABILITY_PLUGINS = ("Intent Source Plugin", "Policy Plugin", "Decision Plugin", "Approval Plugin", "Execution Adapter Plugin")


def test_infrastructure_plugin_class_defined(registry_text):
    assert "Infrastructure plugins" in registry_text
    for plugin in INFRASTRUCTURE_PLUGINS:
        assert plugin in registry_text


def test_capability_plugin_class_defined(registry_text):
    assert "Capability plugins" in registry_text
    for plugin in CAPABILITY_PLUGINS:
        assert plugin in registry_text


def test_plugin_classes_explained(registry_text):
    text = _normalized(registry_text)
    assert "Why the distinction matters" in text


def test_plugin_classes_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    assert "Infrastructure plugins" in text
    assert "Capability plugins" in text


# ═══════════════════════════════════════════════════════════════════════
# Static / dynamic runtime model defined
# ═══════════════════════════════════════════════════════════════════════

STATIC_RUNTIME_ITEMS = ("Architecture", "Contracts", "Registry", "Plugin metadata", "Compatibility")
DYNAMIC_RUNTIME_ITEMS = ("Session", "Task", "Phase", "Intent", "Approval", "Broker decision", "Execution state")


def test_static_runtime_model_defined(registry_text):
    assert "**Static runtime**" in registry_text
    for item in STATIC_RUNTIME_ITEMS:
        assert item in registry_text


def test_dynamic_runtime_model_defined(registry_text):
    assert "**Dynamic runtime**" in registry_text
    for item in DYNAMIC_RUNTIME_ITEMS:
        assert item in registry_text


def test_dynamic_runtime_marked_as_future_phase(registry_text):
    text = _normalized(registry_text)
    assert "a future phase, not implemented here" in text.lower() \
        or "future phase, not implemented here" in text


def test_static_dynamic_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    assert "Static runtime" in text
    assert "Dynamic runtime" in text


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable explicitly stated
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("doc_text_fixture", ["registry_text", "phase_doc_text"])
def test_execution_unavailable_documented(request, doc_text_fixture):
    text = _normalized(request.getfixturevalue(doc_text_fixture))
    assert "Execution unavailable" in text or "execution_unavailable" in text


def test_current_maximum_runtime_state_still_observed(registry_text, phase_doc_text):
    for text in (registry_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum runtime state" in normalized
        assert "Observed" in normalized


def test_current_maximum_plugin_capability_still_observe(registry_text, phase_doc_text):
    for text in (registry_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum plugin capability" in normalized
        assert "`observe`" in normalized or "observe" in normalized


# ═══════════════════════════════════════════════════════════════════════
# No implementation claims
# ═══════════════════════════════════════════════════════════════════════

FORBIDDEN_IMPLEMENTATION_CLAIMS = (
    "plugin registry implemented",
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


@pytest.mark.parametrize("doc_path", [REGISTRY_DOC, PHASE_DOC])
@pytest.mark.parametrize("claim", FORBIDDEN_IMPLEMENTATION_CLAIMS)
def test_no_forbidden_implementation_claims(doc_path, claim):
    text = doc_path.read_text().lower()
    assert claim not in text


@pytest.mark.parametrize("doc_path", [REGISTRY_DOC, PHASE_DOC])
def test_no_plugin_loading_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No plugin loading" in text


@pytest.mark.parametrize("doc_path", [REGISTRY_DOC, PHASE_DOC])
def test_no_registry_implementation_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No plugin registry implementation" in text


@pytest.mark.parametrize("doc_path", [REGISTRY_DOC, PHASE_DOC])
def test_no_go_confirmations_section_present(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No-Go Confirmations" in text
    assert "No runtime execution" in text


# ═══════════════════════════════════════════════════════════════════════
# Next phase recommendation exists
# ═══════════════════════════════════════════════════════════════════════


def test_recommended_next_phase_is_110d(registry_text, phase_doc_text):
    for text in (registry_text, phase_doc_text):
        assert "110D" in text
        assert "Runtime Registry Contract Freeze" in text


# ═══════════════════════════════════════════════════════════════════════
# No runtime implementation added anywhere in the source tree
# ═══════════════════════════════════════════════════════════════════════


def test_no_registry_module_added_to_core():
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    forbidden_names = {
        "runtime.py", "pcae_runtime.py", "plugin_registry.py", "plugin_loader.py",
        "plugin_contract.py", "service_registry.py", "plugin_manifest.py",
        "plugin_discovery.py", "capability_resolution.py",
    }
    existing = {p.name for p in core_dir.glob("*.py")}
    assert not (forbidden_names & existing)


def test_no_plugin_or_runtime_directory_added():
    assert not (REPO_ROOT / "src" / "pcae" / "plugins").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "runtime").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "registry").exists()


def test_task_contract_excludes_src_pcae():
    """This phase's task contract must not list any src/pcae/ file as
    allowed -- confirming the design-only boundary was respected at the
    governance layer, not just by convention."""
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-110c*"))
    if not matches:
        pytest.skip("110C task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    assert "src/pcae/" not in contract_text


def test_integration_registry_still_has_exactly_four_entries():
    """This phase's docs reference the existing INTEGRATION_REGISTRY
    (109C) as a precedent without modifying it -- confirmed directly."""
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


def test_prior_110_series_docs_still_present():
    for doc_name in (
        "PCAE_RUNTIME_ARCHITECTURE.md",
        "PCAE_PLUGIN_MODEL.md",
        "PCAE_RUNTIME_PLUGIN_CONTRACTS.md",
        "PHASE_110_RUNTIME_ARCHITECTURE.md",
        "PHASE_110_RUNTIME_PLUGIN_CONTRACT_FREEZE.md",
    ):
        assert (REPO_ROOT / "docs" / doc_name).exists()
