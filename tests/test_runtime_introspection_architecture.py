"""Tests for Phase 111A — Runtime Introspection Architecture.

This is a pure documentation-verification suite. Phase 111A is an
architecture/design phase: it designs how PCAE exposes Runtime,
Registry, Plugin, Capability, Session, and Health information through a
safe, read-only introspection model -- without implementing any
introspection module, CLI command, REST endpoint, or web UI. There is
no runtime code to unit-test -- these tests verify the documents exist,
contain the required frozen content, make no implementation claims, and
that the domain/health/status/visibility/object/API models are present
as specified.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INTROSPECTION_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_INTROSPECTION.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_111_RUNTIME_INTROSPECTION_ARCHITECTURE.md"


@pytest.fixture(scope="module")
def introspection_text() -> str:
    return INTROSPECTION_DOC.read_text()


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


def test_runtime_introspection_document_exists():
    assert INTROSPECTION_DOC.exists()
    assert INTROSPECTION_DOC.stat().st_size > 0


def test_phase_111a_document_exists():
    assert PHASE_DOC.exists()
    assert PHASE_DOC.stat().st_size > 0


# ═══════════════════════════════════════════════════════════════════════
# Core architectural principle
# ═══════════════════════════════════════════════════════════════════════


def test_preserved_principles_present(introspection_text):
    text = _normalized(introspection_text)
    assert "Runtime orchestrates." in text
    assert "Registry resolves." in text
    assert "Plugins implement." in text
    assert "Metadata precedes behavior." in text


def test_visibility_precedes_authority_principle_documented(introspection_text):
    text = _normalized(introspection_text)
    assert "Visibility precedes authority." in text


def test_visibility_precedes_authority_summarized_in_phase_doc(phase_doc_text):
    assert "Visibility precedes authority" in _normalized(phase_doc_text)


# ═══════════════════════════════════════════════════════════════════════
# Introspection defined as read-only, never behavior-changing
# ═══════════════════════════════════════════════════════════════════════


def test_introspection_defined_as_read_only_visibility_layer(introspection_text):
    text = _normalized(introspection_text)
    assert "read-only visibility layer" in text


def test_introspection_never_changes_behavior(introspection_text):
    text = _normalized(introspection_text)
    assert "it never changes behavior." in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Introspection domains documented (15 canonical domains)
# ═══════════════════════════════════════════════════════════════════════

INTROSPECTION_DOMAINS = (
    "Runtime",
    "Registry",
    "Plugins",
    "Capabilities",
    "Policy",
    "Observation",
    "Session",
    "Task",
    "Phase",
    "Identity",
    "Configuration",
    "Health",
    "Version",
    "Governance",
    "Future Execution",
)


def test_introspection_domains_section_exists(introspection_text):
    assert "## 2. Introspection Domains" in introspection_text


@pytest.mark.parametrize("domain", INTROSPECTION_DOMAINS)
def test_introspection_domain_documented(introspection_text, domain):
    assert f"**{domain}**" in introspection_text


def test_fifteen_domains_documented(introspection_text):
    assert len(INTROSPECTION_DOMAINS) == 15
    for domain in INTROSPECTION_DOMAINS:
        assert domain in introspection_text


def test_domains_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    for domain in INTROSPECTION_DOMAINS:
        assert domain in text


def test_future_execution_marked_least_visible(introspection_text):
    text = _normalized(introspection_text)
    assert "permanently the least-visible domain" in text


# ═══════════════════════════════════════════════════════════════════════
# Introspection model — four visibility tiers
# ═══════════════════════════════════════════════════════════════════════

VISIBILITY_TIERS = (
    "Visible",
    "Hidden",
    "Requires future authorization",
    "Permanently unavailable",
)


def test_introspection_model_section_exists(introspection_text):
    assert "## 3. Introspection Model" in introspection_text


@pytest.mark.parametrize("tier", VISIBILITY_TIERS)
def test_visibility_tier_documented(introspection_text, tier):
    assert tier in introspection_text


def test_four_tiers_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    for tier in VISIBILITY_TIERS:
        assert tier in text


# ═══════════════════════════════════════════════════════════════════════
# Introspection objects documented (design only)
# ═══════════════════════════════════════════════════════════════════════

INTROSPECTION_OBJECTS = (
    "RuntimeInfo",
    "RegistryInfo",
    "PluginInfo",
    "CapabilityInfo",
    "HealthInfo",
    "VersionInfo",
    "GovernanceInfo",
    "RuntimeStateInfo",
    "SessionInfo",
    "TaskInfo",
    "PhaseInfo",
)


def test_introspection_objects_section_exists(introspection_text):
    assert "## 4. Introspection Objects" in introspection_text


@pytest.mark.parametrize("obj", INTROSPECTION_OBJECTS)
def test_introspection_object_documented(introspection_text, obj):
    assert f"`{obj}`" in introspection_text


def test_eleven_introspection_objects_documented(introspection_text):
    assert len(INTROSPECTION_OBJECTS) == 11
    for obj in INTROSPECTION_OBJECTS:
        assert obj in introspection_text


def test_introspection_objects_summarized_in_phase_doc(phase_doc_text):
    for obj in ("RuntimeInfo", "RegistryInfo", "PluginInfo", "HealthInfo"):
        assert obj in phase_doc_text


def test_introspection_objects_are_design_only(introspection_text):
    text = _normalized(introspection_text)
    assert "No implementation." in text


def test_introspection_objects_map_to_existing_precedents(introspection_text):
    text = _normalized(introspection_text)
    assert "RegistrySnapshot" in text
    assert "PluginDescriptor" in text


# ═══════════════════════════════════════════════════════════════════════
# Runtime Health Model documented
# ═══════════════════════════════════════════════════════════════════════

HEALTH_FACETS = (
    "Runtime health",
    "Registry health",
    "Plugin metadata health",
    "Manifest validity",
    "Contract compatibility",
    "Observation coverage",
    "Execution availability",
    "Approval availability",
)


def test_health_model_section_exists(introspection_text):
    assert "## 5. Runtime Health Model" in introspection_text


@pytest.mark.parametrize("facet", HEALTH_FACETS)
def test_health_facet_documented(introspection_text, facet):
    assert facet in introspection_text


def test_eight_health_facets_documented(introspection_text):
    assert len(HEALTH_FACETS) == 8
    for facet in HEALTH_FACETS:
        assert facet in introspection_text


def test_health_model_current_expected_state_documented(introspection_text):
    text = _normalized(introspection_text)
    assert "Healthy" in text
    assert "Execution unavailable" in text


def test_health_model_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "health model" in text
    assert "eight" in text or "8" in text


# ═══════════════════════════════════════════════════════════════════════
# Runtime Status Model documented (restates 110A §8)
# ═══════════════════════════════════════════════════════════════════════

RUNTIME_STATES = (
    "Intent",
    "Observed",
    "Advisory",
    "Approved",
    "Executable",
    "Executed",
    "Audited",
    "Rollback Ready",
)


def test_status_model_section_exists(introspection_text):
    assert "## 6. Runtime Status Model" in introspection_text


@pytest.mark.parametrize("state", RUNTIME_STATES)
def test_runtime_state_documented(introspection_text, state):
    assert state in introspection_text


def test_status_model_restates_110a_not_a_new_model(introspection_text):
    text = _normalized(introspection_text)
    assert "not a new" in text.lower() or "not a second" in text.lower()


def test_current_state_is_observed(introspection_text, phase_doc_text):
    for text in (introspection_text, phase_doc_text):
        normalized = _normalized(text)
        assert "`Observed`" in normalized


def test_status_model_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "status model" in text


# ═══════════════════════════════════════════════════════════════════════
# Introspection API documented (design only)
# ═══════════════════════════════════════════════════════════════════════

API_OPERATIONS = (
    "GetRuntime()",
    "GetRegistry()",
    "GetPlugins()",
    "GetCapabilities()",
    "GetHealth()",
    "GetGovernance()",
    "GetState()",
    "GetVersion()",
)


def test_introspection_api_section_exists(introspection_text):
    assert "## 7. Introspection API" in introspection_text


@pytest.mark.parametrize("operation", API_OPERATIONS)
def test_api_operation_documented(introspection_text, operation):
    assert operation in introspection_text


def test_eight_api_operations_documented(introspection_text):
    assert len(API_OPERATIONS) == 8
    for operation in API_OPERATIONS:
        assert operation in introspection_text


def test_api_operations_summarized_in_phase_doc(phase_doc_text):
    for operation in API_OPERATIONS:
        assert operation in phase_doc_text


def test_api_is_design_only(introspection_text):
    text = _normalized(introspection_text)
    assert "Design-only." in text


# ═══════════════════════════════════════════════════════════════════════
# Visibility rules documented
# ═══════════════════════════════════════════════════════════════════════

MAY_EXPOSE = ("Metadata", "Contracts", "Health", "Status", "Capabilities", "Version", "Compatibility")

MUST_NEVER_EXPOSE = (
    "Execution handles",
    "Plugin instances",
    "Internal mutable state",
    "Secret material",
    "Credentials",
    "Approval bypasses",
    "Execution control",
)


def test_visibility_rules_section_exists(introspection_text):
    assert "## 8. Visibility Rules" in introspection_text
    assert "**The Runtime may expose:**" in introspection_text
    assert "**The Runtime must never expose:**" in introspection_text


@pytest.mark.parametrize("item", MAY_EXPOSE)
def test_may_expose_item_documented(introspection_text, item):
    assert item in introspection_text


@pytest.mark.parametrize("item", MUST_NEVER_EXPOSE)
def test_must_never_expose_item_documented(introspection_text, item):
    assert item in introspection_text


def test_visibility_rules_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "visibility rules" in text.lower()
    assert "must never expose" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable / Observed / observe reconfirmation
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("doc_text_fixture", ["introspection_text", "phase_doc_text"])
def test_execution_unavailable_documented(request, doc_text_fixture):
    text = _normalized(request.getfixturevalue(doc_text_fixture))
    assert "Execution unavailable" in text or "execution_unavailable" in text


def test_current_maximum_runtime_state_still_observed(introspection_text, phase_doc_text):
    for text in (introspection_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum runtime state" in normalized
        assert "Observed" in normalized


def test_current_maximum_plugin_capability_still_observe(introspection_text, phase_doc_text):
    for text in (introspection_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum plugin capability" in normalized
        assert "`observe`" in normalized or "observe" in normalized


# ═══════════════════════════════════════════════════════════════════════
# No implementation claims
# ═══════════════════════════════════════════════════════════════════════

FORBIDDEN_IMPLEMENTATION_CLAIMS = (
    "runtime introspection implemented",
    "cli introspection command implemented",
    "rest endpoint implemented",
    "web ui implemented",
    "plugin loading implemented",
    "plugin instantiation implemented",
    "plugin invocation implemented",
    "dependency injection implemented",
    "runtime execution enabled",
    "command authorization implemented",
    "command denial implemented",
    "shell mediation implemented",
    "backend invocation implemented",
    "adapter invocation implemented",
    "execution enablement implemented",
    "execution capability implemented",
    "permission broker enforcement implemented",
    "audit persistence implemented",
    "rollback execution implemented",
    "emergency stop implemented",
    "telegram inbound implemented",
    "daemon implemented",
    "background workers implemented",
    "automatic apply implemented",
)


@pytest.mark.parametrize("doc_path", [INTROSPECTION_DOC, PHASE_DOC])
@pytest.mark.parametrize("claim", FORBIDDEN_IMPLEMENTATION_CLAIMS)
def test_no_forbidden_implementation_claims(doc_path, claim):
    text = doc_path.read_text().lower()
    assert claim not in text


@pytest.mark.parametrize("doc_path", [INTROSPECTION_DOC, PHASE_DOC])
def test_no_introspection_implementation_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No runtime introspection implementation" in text


@pytest.mark.parametrize("doc_path", [INTROSPECTION_DOC, PHASE_DOC])
def test_no_cli_command_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No CLI introspection command" in text


@pytest.mark.parametrize("doc_path", [INTROSPECTION_DOC, PHASE_DOC])
def test_no_rest_or_web_ui_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No REST endpoint" in text
    assert "No web UI" in text


@pytest.mark.parametrize("doc_path", [INTROSPECTION_DOC, PHASE_DOC])
def test_no_go_confirmations_section_present(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No-Go Confirmations" in text
    assert "No runtime execution" in text


# ═══════════════════════════════════════════════════════════════════════
# Next phase recommendation exists
# ═══════════════════════════════════════════════════════════════════════


def test_recommended_next_phase_is_111b(introspection_text, phase_doc_text):
    for text in (introspection_text, phase_doc_text):
        assert "111B" in text
        assert "Runtime Introspection Prototype" in text
        assert "Observation-Only" in text


# ═══════════════════════════════════════════════════════════════════════
# No runtime implementation added anywhere in the source tree
# ═══════════════════════════════════════════════════════════════════════


def test_no_introspection_module_added_to_core():
    """As of 111A (architecture/design only), no implementation module
    existed. `runtime_introspection.py` itself was intentionally,
    legitimately added by the very next phase, 111B (Runtime
    Introspection Prototype) -- excluded here rather than left to
    perpetually fail once that phase landed, mirroring how 110D/110C's
    equivalent guards never collided with 110E's later
    `runtime_registry.py` by design. The remaining forbidden names
    (a hypothetical one-object-per-file split this design never called
    for) remain valid: 111B implemented every object in one module."""
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    forbidden_names = {
        "introspection.py", "runtime_info.py",
        "registry_info.py", "plugin_info.py", "health_info.py",
        "governance_info.py", "runtime_state_info.py",
    }
    existing = {p.name for p in core_dir.glob("*.py")}
    assert not (forbidden_names & existing)


def test_no_introspection_cli_wiring_added():
    cli_text = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text()
    assert "GetRuntime" not in cli_text
    assert "GetRegistry" not in cli_text
    assert "runtime-introspection" not in cli_text


def test_no_new_directory_added_for_introspection():
    assert not (REPO_ROOT / "src" / "pcae" / "introspection").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "plugins").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "runtime").exists()


def test_task_contract_excludes_src_pcae():
    """This phase's task contract must not list any src/pcae/ file as
    allowed -- confirming the design-only boundary was respected at the
    governance layer, not just by convention."""
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-111a*"))
    if not matches:
        pytest.skip("111A task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    assert "src/pcae/" not in contract_text
