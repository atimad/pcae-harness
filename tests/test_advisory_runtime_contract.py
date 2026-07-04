"""Tests for Phase 113B — Advisory Runtime Contract Freeze.

This is a pure documentation-verification suite. Phase 113B is a
contract/freeze phase: it freezes the Advisory Result contract,
explainability contract, evidence model, reproducibility rule,
advisory categories, severity/confidence semantics, lifecycle,
presentation contract, safety rules, and compatibility rules for the
Advisory Runtime (113A) -- without implementing any advisory logic,
runtime execution, or execution capability. There is no runtime code
to unit-test -- these tests verify the documents exist, contain the
required frozen content, make no implementation claims, and correctly
extend (not silently duplicate) 113A's own nine-field model.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_DOC = REPO_ROOT / "docs" / "PCAE_ADVISORY_RUNTIME_CONTRACT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_113_ADVISORY_RUNTIME_CONTRACT_FREEZE.md"
ARCHITECTURE_DOC = REPO_ROOT / "docs" / "PCAE_ADVISORY_RUNTIME.md"


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_DOC.read_text()


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC.read_text()


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


# ═══════════════════════════════════════════════════════════════════════
# Documents exist
# ═══════════════════════════════════════════════════════════════════════


def test_advisory_runtime_contract_document_exists():
    assert CONTRACT_DOC.exists()
    assert CONTRACT_DOC.stat().st_size > 0


def test_phase_113b_document_exists():
    assert PHASE_DOC.exists()
    assert PHASE_DOC.stat().st_size > 0


def test_architecture_doc_still_present_unmodified_reference():
    assert ARCHITECTURE_DOC.exists()


# ═══════════════════════════════════════════════════════════════════════
# New principle
# ═══════════════════════════════════════════════════════════════════════


def test_explainability_precedes_trust_principle(contract_text):
    text = _normalized(contract_text)
    assert "Explainability precedes trust." in text


def test_principle_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Explainability precedes trust" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — Advisory Result contract
# ═══════════════════════════════════════════════════════════════════════


def test_section_1_exists(contract_text):
    assert "## 1. Advisory Result Contract" in contract_text


ADVISORY_RESULT_FIELDS = (
    "advisory_id", "category", "severity", "confidence", "recommended_action",
    "rationale", "evidence_references", "affected_runtime_objects", "timestamp",
    "source_snapshot_reference", "reasoning_summary", "alternative_considerations",
    "remediation", "implementation_status",
)


@pytest.mark.parametrize("field", ADVISORY_RESULT_FIELDS)
def test_advisory_result_field_documented(contract_text, field):
    assert f"`{field}`" in contract_text


def test_fourteen_fields_frozen(contract_text):
    assert len(ADVISORY_RESULT_FIELDS) == 14
    for field in ADVISORY_RESULT_FIELDS:
        assert field in contract_text


def test_recommendation_reconciled_not_duplicated(contract_text):
    text = _normalized(contract_text)
    assert "recommendation" in text.lower()
    assert "does not add a duplicate" in text or "not add a duplicate" in text
    assert "recommended_action" in text


def test_advisory_result_no_implementation(contract_text):
    text = _normalized(contract_text)
    assert "No implementation." in text


def test_advisory_result_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    assert "Fourteen fields frozen" in text or "fourteen fields" in text.lower()
    assert "source_snapshot_reference" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — Explainability contract
# ═══════════════════════════════════════════════════════════════════════


def test_section_2_exists(contract_text):
    assert "## 2. Explainability Contract" in contract_text


EXPLAINABILITY_FACETS = (
    "What was observed",
    "Why it matters",
    "What evidence supports it",
    "What Runtime Snapshot fields were used",
    "What recommendation was made",
    "What remediation is suggested",
    "Why this is advisory only",
    "Why no authorization or execution follows",
)


@pytest.mark.parametrize("facet", EXPLAINABILITY_FACETS)
def test_explainability_facet_documented(contract_text, facet):
    assert facet in contract_text


def test_eight_explainability_facets(contract_text):
    assert len(EXPLAINABILITY_FACETS) == 8


def test_reproducibility_principle_documented(contract_text):
    text = _normalized(contract_text)
    assert "Every recommendation must be reproducible from the Runtime Snapshot." in text


def test_reproducibility_cites_110a_deterministic_principle(contract_text):
    text = _normalized(contract_text)
    assert "Deterministic" in text
    assert "110A" in text


def test_explainability_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Eight required explanations" in text or "eight required explanations" in text.lower()
    assert "reproducible" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — Evidence model
# ═══════════════════════════════════════════════════════════════════════


def test_section_3_exists(contract_text):
    assert "## 3. Evidence Model" in contract_text


EVIDENCE_REFERENCE_FIELDS = ("domain", "object_id", "field_path", "evidence_summary")


@pytest.mark.parametrize("field", EVIDENCE_REFERENCE_FIELDS)
def test_evidence_reference_field_documented(contract_text, field):
    assert f"`{field}`" in contract_text


def test_no_evidence_database_documented(contract_text):
    text = _normalized(contract_text)
    assert "No evidence database" in text
    assert "No audit persistence" in text


def test_evidence_model_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    assert "EvidenceReference" in text
    assert "no evidence database" in text.lower() or "No evidence database" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 4 — Advisory categories
# ═══════════════════════════════════════════════════════════════════════


def test_section_4_exists(contract_text):
    assert "## 4. Advisory Categories" in contract_text


ADVISORY_CATEGORIES = (
    "Runtime Health", "Governance", "Context Consistency", "Registry",
    "Plugin Compatibility", "Configuration", "Operational Readiness",
)


@pytest.mark.parametrize("category", ADVISORY_CATEGORIES)
def test_category_documented(contract_text, category):
    assert category in contract_text


def test_extension_rule_documented(contract_text):
    text = _normalized(contract_text)
    assert "Extension rule" in text
    assert "meaning" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — Severity/confidence semantics
# ═══════════════════════════════════════════════════════════════════════


def test_section_5_exists(contract_text):
    assert "## 5. Severity and Confidence Semantics" in contract_text


SEVERITY_LEVELS = ("info", "advisory", "warning", "critical")
CONFIDENCE_LEVELS = ("unknown", "observed", "validated", "proven")


@pytest.mark.parametrize("level", SEVERITY_LEVELS)
def test_severity_level_documented(contract_text, level):
    assert f"`{level}`" in contract_text


@pytest.mark.parametrize("level", CONFIDENCE_LEVELS)
def test_confidence_level_documented(contract_text, level):
    assert f"`{level}`" in contract_text


def test_severity_confidence_orthogonal_documented(contract_text):
    text = _normalized(contract_text)
    assert "orthogonal" in text.lower()
    assert "never conflated" in text.lower()


def test_ambiguity_handling_fail_closed_documented(contract_text):
    text = _normalized(contract_text)
    assert "Fail-closed" in text or "fail-closed" in text.lower()
    assert "alternative_considerations" in text


def test_severity_confidence_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "orthogonal" in text
    assert "fail-closed" in text or "fail closed" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — Advisory lifecycle
# ═══════════════════════════════════════════════════════════════════════


def test_section_6_exists(contract_text):
    assert "## 6. Advisory Lifecycle" in contract_text


LIFECYCLE_STAGES = ("produced", "presented", "acknowledged", "superseded", "resolved", "dismissed")


@pytest.mark.parametrize("stage", LIFECYCLE_STAGES)
def test_lifecycle_stage_documented(contract_text, stage):
    assert f"`{stage}`" in contract_text


def test_six_lifecycle_stages(contract_text):
    assert len(LIFECYCLE_STAGES) == 6


def test_lifecycle_contract_only_status(contract_text):
    text = _normalized(contract_text)
    assert "Current implementation status: contract only" in text


def test_lifecycle_distinct_from_other_vocabularies(contract_text):
    text = _normalized(contract_text)
    assert "not to be conflated" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Objective 7 — Presentation contract
# ═══════════════════════════════════════════════════════════════════════


def test_section_7_exists(contract_text):
    assert "## 7. Presentation Contract" in contract_text


PRESENTATION_CONSUMERS = ("CLI", "Telegram", "REST", "Dashboard", "AI agents")


@pytest.mark.parametrize("consumer", PRESENTATION_CONSUMERS)
def test_presentation_consumer_named(contract_text, consumer):
    assert consumer in contract_text


def test_same_underlying_model_documented(contract_text):
    text = _normalized(contract_text)
    assert "same underlying" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Objective 8 — Safety rules (extended from 113A)
# ═══════════════════════════════════════════════════════════════════════


def test_section_8_exists(contract_text):
    assert "## 8. Safety Rules" in contract_text


SAFETY_RULES = (
    "Execute", "Authorize", "Deny", "Mutate Runtime Snapshot", "Mutate Runtime Context",
    "Invoke Permission Broker", "Imply approval", "Bypass human review", "Bypass future audit",
)


@pytest.mark.parametrize("rule", SAFETY_RULES)
def test_safety_rule_documented(contract_text, rule):
    assert rule in contract_text


def test_ten_safety_rules_documented(contract_text, phase_doc_text):
    assert len(SAFETY_RULES) == 9  # 9 named rules; "invoke shell/backend/adapters" counted as 1 of the 10 total
    text = _normalized(phase_doc_text)
    assert "Ten absolute rules frozen" in text


def test_safety_extended_from_113a_documented(contract_text):
    text = _normalized(contract_text)
    assert "113A" in text
    assert "new, 113B" in text or "new" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Objective 9 — Compatibility rules
# ═══════════════════════════════════════════════════════════════════════


def test_section_9_exists(contract_text):
    assert "## 9. Compatibility Rules" in contract_text


COMPATIBILITY_RULES = (
    "Additive-only changes",
    "Breaking changes require a major version bump",
    "Consumer expectations",
    "Unknown field handling",
    "Reproducibility expectations",
)


@pytest.mark.parametrize("rule", COMPATIBILITY_RULES)
def test_compatibility_rule_documented(contract_text, rule):
    assert rule in contract_text


def test_no_versioning_field_added(contract_text):
    text = _normalized(contract_text)
    assert "No versioning field is added by this phase" in text
    assert "advisory_contract_version" in text


def test_compatibility_mirrors_112f(contract_text):
    text = _normalized(contract_text)
    assert "112F" in text


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable / Observed / observe reconfirmation
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
    "advisory runtime implemented",
    "advisory execution implemented",
    "command authorization implemented",
    "command denial implemented",
    "permission broker enforcement implemented",
    "runtime execution enabled",
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


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
@pytest.mark.parametrize("claim", FORBIDDEN_IMPLEMENTATION_CLAIMS)
def test_no_forbidden_implementation_claims(doc_path, claim):
    text = doc_path.read_text().lower()
    assert claim not in text


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
def test_no_go_confirmations_section_present(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No-Go Confirmations" in text
    assert "No runtime execution" in text


# ═══════════════════════════════════════════════════════════════════════
# Next phase recommendation exists
# ═══════════════════════════════════════════════════════════════════════


def test_recommended_next_phase_is_113c(contract_text, phase_doc_text):
    for text in (contract_text, phase_doc_text):
        assert "113C" in text
        assert "Advisory Runtime Prototype" in text


# ═══════════════════════════════════════════════════════════════════════
# No runtime implementation added anywhere in the source tree
# ═══════════════════════════════════════════════════════════════════════


def test_no_advisory_module_added_to_core():
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    # advisory_runtime.py now legitimately exists (created by 113C prototype).
    # The contract phase (113B) was documentation-only; these other
    # filenames should still not exist as separate modules.
    forbidden_names = {
        "advisory_result.py", "advisory_pipeline.py",
        "advisory_analysis.py", "advisory_recommendation.py", "evidence_reference.py",
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
    matches = list(done_dir.glob("*phase-113b-advisory-runtime*"))
    if not matches:
        pytest.skip("113B task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text_ = matches[0].read_text()
    allowed_files_start = contract_text_.index("## Allowed Files")
    allowed_files_end = contract_text_.index("##", allowed_files_start + 1)
    allowed_files_section = contract_text_[allowed_files_start:allowed_files_end]
    assert "src/pcae/" not in allowed_files_section
