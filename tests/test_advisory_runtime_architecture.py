"""Tests for Phase 113A — Advisory Runtime Architecture.

This is a pure documentation-verification suite. Phase 113A is an
architecture/design phase: it designs the Advisory Runtime -- the
Runtime subsystem responsible for producing read-only recommendations
from Runtime Snapshot -- without implementing any advisory logic,
runtime execution, or execution capability. There is no runtime code
to unit-test -- these tests verify the documents exist, contain the
required frozen content, make no implementation claims, and that the
pipeline, Advisory Result model, categories, integration rules,
plugin-gap naming, presentation model, and safety rules are present as
specified.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURE_DOC = REPO_ROOT / "docs" / "PCAE_ADVISORY_RUNTIME.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_113_ADVISORY_RUNTIME_ARCHITECTURE.md"


@pytest.fixture(scope="module")
def architecture_text() -> str:
    return ARCHITECTURE_DOC.read_text()


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC.read_text()


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


# ═══════════════════════════════════════════════════════════════════════
# Documents exist
# ═══════════════════════════════════════════════════════════════════════


def test_advisory_runtime_document_exists():
    assert ARCHITECTURE_DOC.exists()
    assert ARCHITECTURE_DOC.stat().st_size > 0


def test_phase_113a_document_exists():
    assert PHASE_DOC.exists()
    assert PHASE_DOC.stat().st_size > 0


# ═══════════════════════════════════════════════════════════════════════
# New principle
# ═══════════════════════════════════════════════════════════════════════


def test_recommendation_precedes_authorization_principle(architecture_text):
    text = _normalized(architecture_text)
    assert "Recommendation precedes authorization." in text


def test_principle_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Recommendation precedes authorization" in text


def test_distinguished_from_irg_challenge(architecture_text):
    text = _normalized(architecture_text)
    assert "IRG Challenge" in text
    assert "strategic" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — Advisory Runtime subsystem defined
# ═══════════════════════════════════════════════════════════════════════


def test_subsystem_definition_section_exists(architecture_text):
    assert "## 1. Advisory Runtime Subsystem Definition" in architecture_text


def test_subsystem_never_executes_never_authorizes(architecture_text):
    text = _normalized(architecture_text)
    assert "never executes" in text.lower()
    assert "never authorizes" in text.lower()


def test_architectural_boundaries_documented(architecture_text):
    text = _normalized(architecture_text)
    assert "what Advisory Runtime is not" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — Advisory pipeline frozen
# ═══════════════════════════════════════════════════════════════════════


def test_pipeline_section_exists(architecture_text):
    assert "## 2. Advisory Pipeline" in architecture_text


PIPELINE_STAGES = ("Runtime Snapshot", "Analysis", "Recommendation", "Advisory Result", "Presentation")


@pytest.mark.parametrize("stage", PIPELINE_STAGES)
def test_pipeline_stage_documented(architecture_text, stage):
    assert stage in architecture_text


def test_five_pipeline_stages(architecture_text):
    assert len(PIPELINE_STAGES) == 5
    for stage in PIPELINE_STAGES:
        assert stage in architecture_text


def test_no_execution_path_documented(architecture_text):
    text = _normalized(architecture_text)
    assert "No execution path" in text


def test_pipeline_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    for stage in PIPELINE_STAGES:
        assert stage in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — Advisory Result contract
# ═══════════════════════════════════════════════════════════════════════


def test_advisory_result_section_exists(architecture_text):
    assert "## 3. Advisory Result" in architecture_text


ADVISORY_RESULT_FIELDS = (
    "advisory_id", "category", "severity", "confidence", "rationale",
    "evidence_references", "recommended_action", "affected_runtime_objects", "timestamp",
)


@pytest.mark.parametrize("field", ADVISORY_RESULT_FIELDS)
def test_advisory_result_field_documented(architecture_text, field):
    assert f"`{field}`" in architecture_text


def test_nine_advisory_result_fields(architecture_text):
    assert len(ADVISORY_RESULT_FIELDS) == 9
    for field in ADVISORY_RESULT_FIELDS:
        assert field in architecture_text


def test_severity_vocabulary_documented(architecture_text):
    text = architecture_text
    for level in ("info", "advisory", "warning", "critical"):
        assert level in text


def test_confidence_vocabulary_reuses_existing_codebase_convention(architecture_text):
    text = architecture_text
    for level in ("unknown", "observed", "validated", "proven"):
        assert level in text
    assert "_CAP_CONF_UNKNOWN" in text or "capability-discovery confidence" in text.lower()


def test_recommended_action_never_executable(architecture_text):
    text = _normalized(architecture_text)
    assert "never an executable command" in text.lower() or "never executable" in text.lower()


def test_advisory_result_is_architecture_only(architecture_text):
    text = _normalized(architecture_text)
    assert "No implementation." in text


def test_advisory_result_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    for field in ("advisory_id", "category", "severity", "confidence"):
        assert field in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 4 — Advisory categories
# ═══════════════════════════════════════════════════════════════════════


def test_categories_section_exists(architecture_text):
    assert "## 4. Advisory Categories" in architecture_text


ADVISORY_CATEGORIES = (
    "Runtime Health", "Governance", "Context Consistency", "Registry",
    "Plugin Compatibility", "Configuration", "Operational Readiness",
)


@pytest.mark.parametrize("category", ADVISORY_CATEGORIES)
def test_advisory_category_documented(architecture_text, category):
    assert category in architecture_text


def test_future_extensibility_named(architecture_text):
    text = _normalized(architecture_text)
    assert "Future extensibility" in text


def test_open_taxonomy_documented_and_contrasted_with_110b(architecture_text):
    text = _normalized(architecture_text)
    assert "open taxonomy" in text.lower()
    assert "110B" in text
    assert "closed" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — Runtime integration / Snapshot dependency
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_integration_section_exists(architecture_text):
    assert "## 5. Runtime Integration" in architecture_text


def test_snapshot_only_dependency_documented(architecture_text):
    text = _normalized(architecture_text)
    assert "consumes Runtime Snapshot, and nothing else" in text or "Runtime Snapshot, and nothing else" in text


def test_no_direct_transport_dependency_documented(architecture_text):
    text = _normalized(architecture_text)
    assert "must not depend directly on the CLI, Telegram, REST" in text or "not depend directly on" in text


def test_runtime_integration_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Runtime Snapshot exclusively" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — Plugin integration
# ═══════════════════════════════════════════════════════════════════════


def test_plugin_integration_section_exists(architecture_text):
    assert "## 6. Plugin Integration" in architecture_text


def test_no_existing_plugin_category_fits_documented(architecture_text):
    text = _normalized(architecture_text)
    assert "no existing plugin category fits" in text.lower()
    assert "ten plugin categories" in text.lower() or "ten frozen plugin categories" in text.lower()


def test_no_eleventh_category_added(architecture_text):
    text = _normalized(architecture_text)
    assert "does not add an eleventh plugin category" in text.lower() or "does not add an eleventh category" in text.lower()


def test_no_plugin_loading_documented(architecture_text):
    text = _normalized(architecture_text)
    assert "No plugin loading." in text


def test_plugin_gap_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Named, not resolved" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 7 — Presentation layer / consumer independence
# ═══════════════════════════════════════════════════════════════════════


def test_presentation_section_exists(architecture_text):
    assert "## 7. Presentation Layer" in architecture_text


FUTURE_CONSUMERS = ("CLI", "Telegram", "REST", "Dashboard", "AI agents")


@pytest.mark.parametrize("consumer", FUTURE_CONSUMERS)
def test_future_consumer_named(architecture_text, consumer):
    assert consumer in architecture_text


def test_no_implementation_for_consumers(architecture_text):
    text = _normalized(architecture_text)
    assert "No implementation is added for any of the five consumers above" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 8 — Safety rules (absolute)
# ═══════════════════════════════════════════════════════════════════════


def test_safety_rules_section_exists(architecture_text):
    assert "## 8. Safety Rules" in architecture_text


SAFETY_RULES = (
    "Never executes",
    "Never authorizes",
    "Never mutates Runtime Context",
    "Never mutates Runtime Snapshot",
    "Never invokes Permission Broker",
    "Never invokes shell",
    "Never invokes adapters",
)


@pytest.mark.parametrize("rule", SAFETY_RULES)
def test_safety_rule_documented(architecture_text, rule):
    assert rule in architecture_text


def test_seven_safety_rules(architecture_text):
    assert len(SAFETY_RULES) == 7
    for rule in SAFETY_RULES:
        assert rule in architecture_text


def test_safety_rules_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Seven absolute rules frozen" in text or "seven absolute" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable / Observed / observe reconfirmation
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("doc_text_fixture", ["architecture_text", "phase_doc_text"])
def test_execution_unavailable_documented(request, doc_text_fixture):
    text = _normalized(request.getfixturevalue(doc_text_fixture))
    assert "Execution unavailable" in text or "execution_unavailable" in text


def test_current_maximum_runtime_state_still_observed(architecture_text, phase_doc_text):
    for text in (architecture_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum runtime state" in normalized
        assert "Observed" in normalized


def test_current_maximum_plugin_capability_still_observe(architecture_text, phase_doc_text):
    for text in (architecture_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum plugin capability" in normalized
        assert "`observe`" in normalized or "observe" in normalized


# ═══════════════════════════════════════════════════════════════════════
# No implementation claims
# ═══════════════════════════════════════════════════════════════════════

FORBIDDEN_IMPLEMENTATION_CLAIMS = (
    "advisory execution implemented",
    "runtime execution enabled",
    "command authorization implemented",
    "command denial implemented",
    "permission broker enforcement implemented",
    "plugin loading implemented",
    "plugin instantiation implemented",
    "plugin invocation implemented",
    "dependency injection implemented",
    "shell mediation implemented",
    "backend invocation implemented",
    "adapter invocation implemented",
    "execution enablement implemented",
    "execution capability implemented",
    "automatic apply implemented",
    "audit persistence implemented",
    "rollback execution implemented",
    "telegram inbound implemented",
    "rest server implemented",
    "web ui implemented",
    "daemon implemented",
    "background workers implemented",
)


@pytest.mark.parametrize("doc_path", [ARCHITECTURE_DOC, PHASE_DOC])
@pytest.mark.parametrize("claim", FORBIDDEN_IMPLEMENTATION_CLAIMS)
def test_no_forbidden_implementation_claims(doc_path, claim):
    text = doc_path.read_text().lower()
    assert claim not in text


@pytest.mark.parametrize("doc_path", [ARCHITECTURE_DOC, PHASE_DOC])
def test_no_go_confirmations_section_present(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No-Go Confirmations" in text
    assert "No runtime execution" in text


# ═══════════════════════════════════════════════════════════════════════
# Next phase recommendation exists
# ═══════════════════════════════════════════════════════════════════════


def test_recommended_next_phase_is_113b(architecture_text, phase_doc_text):
    for text in (architecture_text, phase_doc_text):
        assert "113B" in text
        assert "Advisory Runtime Contract Freeze" in text


# ═══════════════════════════════════════════════════════════════════════
# No runtime implementation added anywhere in the source tree
# ═══════════════════════════════════════════════════════════════════════


def test_no_advisory_runtime_module_added_to_core():
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    forbidden_names = {
        "advisory_runtime.py", "advisory_result.py", "advisory_pipeline.py",
        "advisory_analysis.py", "advisory_recommendation.py",
    }
    existing = {p.name for p in core_dir.glob("*.py")}
    assert not (forbidden_names & existing)


def test_no_new_directory_added_for_advisory():
    assert not (REPO_ROOT / "src" / "pcae" / "advisory").exists()


def test_task_contract_excludes_src_pcae():
    """This phase's task contract must not list any src/pcae/ file as
    allowed -- confirming the design-only boundary was respected at the
    governance layer, not just by convention."""
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-113a-advisory-runtime*"))
    if not matches:
        pytest.skip("113A task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    allowed_files_start = contract_text.index("## Allowed Files")
    allowed_files_end = contract_text.index("##", allowed_files_start + 1)
    allowed_files_section = contract_text[allowed_files_start:allowed_files_end]
    assert "src/pcae/" not in allowed_files_section
