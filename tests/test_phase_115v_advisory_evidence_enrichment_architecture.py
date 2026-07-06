"""Phase 115V: Advisory Evidence Enrichment Architecture.

Documentation/architecture verification only. These tests prove the
Advisory Evidence Enrichment architecture is documented and preserves
the no-implementation, no-new-provider, no-new-skill,
no-execution boundary. No new Evidence Provider, no new Repository
Skill, no Advisory Provider runtime change, no second advisory
provider, no model configuration, and no DeepSeek/GLM/Qwen/Codex/
OpenAI/Claude-specific/local-SLM integration is implemented by this
phase.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ENRICHMENT_DOC = REPO_ROOT / "docs" / "PCAE_ADVISORY_EVIDENCE_ENRICHMENT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_115V_ADVISORY_EVIDENCE_ENRICHMENT_ARCHITECTURE.md"


def _read(path: Path) -> str:
    assert path.exists(), f"expected document missing: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


def test_enrichment_doc_exists():
    assert ENRICHMENT_DOC.exists()


def test_phase_doc_exists():
    assert PHASE_DOC.exists()


def test_core_principle_documented():
    for doc in (ENRICHMENT_DOC, PHASE_DOC):
        text = _normalized(doc)
        assert "Models improve by receiving better evidence" in text
        assert "not by receiving more authority" in text


def test_enrichment_definition_documented():
    text = _normalized(ENRICHMENT_DOC)
    assert "Advisory Evidence Enrichment Definition" in text
    for phrase in (
        "containment is preserved",
        "evidence, not capability, grows",
        "the model still only produces evidence",
    ):
        assert phrase in text, phrase


def test_all_eleven_evidence_categories_documented():
    text = _normalized(ENRICHMENT_DOC)
    assert "Evidence Enrichment Categories" in text
    for category in (
        "Repository state evidence",
        "Git/history evidence",
        "Changed-files evidence",
        "Test evidence",
        "Architecture evidence",
        "Dependency/module evidence",
        "Documentation evidence",
        "Governance evidence",
        "Runtime capability evidence",
        "Report/metadata consistency evidence",
        "Future semantic/code graph evidence",
    ):
        assert category in text, category


def test_evidence_categories_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    for category in (
        "repository state", "git/history", "changed-files", "test evidence",
        "architecture evidence", "dependency/module", "documentation evidence",
        "governance evidence", "runtime capability", "report/metadata consistency",
        "semantic/code graph",
    ):
        assert category in text, category


def test_priority_matrix_documented():
    text = _normalized(ENRICHMENT_DOC)
    assert "Enrichment Priority Matrix" in text
    for dimension in ("Value", "Difficulty", "Determinism", "Risk", "Expected Advisory Benefit"):
        assert dimension in text, dimension
    assert "Recommended tiering" in text
    assert "Tier 1" in text
    assert "Tier 2" in text
    assert "Tier 3" in text


def test_priority_matrix_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    assert "Priority Matrix" in text
    assert "Tier 1" in text
    assert "Tier 2" in text
    assert "Tier 3" in text


def test_advisory_context_package_documented():
    text = _normalized(ENRICHMENT_DOC)
    assert "Advisory Context Package" in text
    for component in (
        "Bounded repository summary",
        "Deterministic evidence",
        "Current transition/question",
        "Constraints/no-go rules",
        "Relevant artifacts",
        "Known limitations",
    ):
        assert component in text, component


def test_advisory_context_package_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    for component in (
        "bounded repository summary", "deterministic evidence",
        "current transition/question", "constraints/no-go rules",
        "relevant artifacts", "known limitations",
    ):
        assert component in text, component


def test_safety_boundaries_documented():
    text = _normalized(ENRICHMENT_DOC)
    assert "Safety Boundaries" in text
    for boundary in (
        "grant execution capability",
        "expose secrets",
        "include unbounded repository dumps",
        "allow prompt injection from repository files",
        "allow model output to bypass normalization",
        "change Decision Evaluation authority",
    ):
        assert boundary in text, boundary


def test_safety_boundaries_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    for boundary in (
        "execution capability", "expose secrets", "unbounded repository dumps",
        "prompt injection", "bypass normalization", "decision evaluation authority",
    ):
        assert boundary in text, boundary


def test_prompt_injection_handling_documented():
    text = _normalized(ENRICHMENT_DOC)
    assert "Prompt-Injection Handling" in text
    for phrase in (
        "always be treated as untrusted input",
        "Trusted PCAE instructions",
        "Deterministic evidence",
        "Untrusted repository content",
    ):
        assert phrase in text, phrase


def test_prompt_injection_handling_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    assert "untrusted input" in text
    assert "trusted pcae instructions" in text
    assert "untrusted repository content" in text


def test_summarization_rules_documented():
    text = _normalized(ENRICHMENT_DOC)
    assert "Evidence Summarization" in text
    for rule in (
        "deterministic summaries preferred",
        "bounded length",
        "provenance preserved",
        "references retained",
        "raw evidence not blindly pasted",
    ):
        assert rule in text, rule


def test_summarization_rules_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    for rule in (
        "deterministic summaries preferred", "bounded length",
        "provenance preserved", "references retained",
        "never blindly pasted",
    ):
        assert rule in text, rule


def test_future_roadmap_documented():
    text = _normalized(ENRICHMENT_DOC)
    assert "Future Implementation Roadmap" in text
    for phase in (
        "115W — Advisory Context Package Contract",
        "115X — Advisory Context Package Prototype",
        "115Y — Advisory Evidence Enrichment Verification",
        "115Z — Advisory Skill Pilot Hardening",
    ):
        assert phase in text, phase


def test_future_roadmap_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    for phase in ("115W", "115X", "115Y", "115Z"):
        assert phase in text, phase


def test_relationship_to_prior_phases_documented():
    text = _read(ENRICHMENT_DOC)
    for phase in ("115U", "115H", "115Q", "115R", "115T"):
        assert phase in text


def test_no_implementation_claims():
    for doc in (ENRICHMENT_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "class AdvisoryContextPackage",
            "class EvidenceEnrichmentProvider",
            "def enrich_evidence",
            "def build_context_package",
            "src/pcae/core/advisory_evidence_enrichment.py",
            "src/pcae/core/advisory_context_package.py",
            "REST endpoint",
            "Telegram inbound implemented",
        ):
            assert forbidden not in text, f"{doc.name} appears to claim implementation: {forbidden}"


def test_no_new_implementation_module_added():
    forbidden_paths = (
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_evidence_enrichment.py",
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_context_package.py",
        REPO_ROOT / "src" / "pcae" / "core" / "evidence_enrichment.py",
    )
    for path in forbidden_paths:
        assert not path.exists(), f"unexpected implementation module added: {path}"


def test_no_existing_advisory_module_modified_to_reference_enrichment():
    for module_path in (
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_repository_skills.py",
        REPO_ROOT / "src" / "pcae" / "core" / "current_acting_model_advisory_provider.py",
        REPO_ROOT / "src" / "pcae" / "core" / "decision_evaluation.py",
        REPO_ROOT / "src" / "pcae" / "core" / "repository_transition_validator.py",
    ):
        source = module_path.read_text(encoding="utf-8")
        for forbidden in ("AdvisoryContextPackage", "advisory_context_package", "advisory_evidence_enrichment"):
            assert forbidden not in source, f"{module_path.name}: {forbidden}"


def test_no_deepseek_or_backend_integration_claimed():
    for doc in (ENRICHMENT_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "deepseek is integrated", "glm is integrated", "claude is integrated",
            "codex is integrated", "qwen is integrated", "openai is integrated",
            "now integrated",
        ):
            assert forbidden not in text.lower()


def test_execution_unavailable_confirmed():
    for doc in (ENRICHMENT_DOC, PHASE_DOC):
        assert "Execution capability remains unavailable" in _read(doc)


def test_no_go_list_present():
    text = _normalized(PHASE_DOC)
    for phrase in (
        "no new Evidence Provider implemented",
        "no new Repository Skill implemented",
        "no second advisory provider added",
        "No execution",
    ):
        assert phrase in text
