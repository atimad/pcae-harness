"""Phase 115A: Repository Decision & Explainability Framework.

Documentation/architecture verification only. These tests prove that the
architecture contracts exist and preserve the no-runtime boundary.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DECISION_DOC = REPO_ROOT / "docs" / "PCAE_DECISION_FRAMEWORK.md"
SKILLS_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_SKILLS.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_115A_DECISION_EXPLAINABILITY_FRAMEWORK.md"


def _read(path: Path) -> str:
    assert path.exists(), f"expected document missing: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


def test_decision_framework_documented():
    text = _read(DECISION_DOC)
    assert "Repository Decision Framework" in text
    for stage in (
        "Repository State",
        "Repository Transition",
        "Evidence Collection",
        "Decision Evaluation",
        "Transition Result",
        "Repository Artifact",
        "Repository Event",
    ):
        assert stage in text


def test_concept_boundaries_are_distinct():
    text = _read(DECISION_DOC)
    for concept in ("Repository State", "Evidence", "Decision", "Repository Artifact", "Repository Event"):
        assert concept in text
    assert "not a kernel primitive" in text
    assert "evaluation-scoped" in text


def test_evidence_architecture_documented():
    text = _read(DECISION_DOC)
    for term in (
        "Evidence Source",
        "Evidence Category",
        "Evidence Confidence",
        "Evidence Freshness",
        "deterministic",
        "model-independent",
    ):
        assert term in text
    for example in ("Git", "Reports", "Metadata", "Tasks", "Architecture", "Runtime", "Push State", "Notification", "Governance", "Tests"):
        assert example in text


def test_evidence_providers_documented():
    text = _read(DECISION_DOC)
    for provider in (
        "Git Provider",
        "Task Provider",
        "Report Provider",
        "Architecture Provider",
        "Runtime Provider",
        "Notification Provider",
        "Governance Provider",
    ):
        assert provider in text
    assert "They do not decide" in text


def test_decision_pipeline_documented():
    text = _normalized(DECISION_DOC)
    for stage in ("Evidence", "Invariant Evaluation", "Decision", "Explanation", "Transition Result"):
        assert stage in text
    assert "same repository state" in text
    assert "same verdict and explanation" in text


def test_explanation_structure_documented():
    text = _read(DECISION_DOC)
    for field in ("Decision", "Reason", "Evidence Used", "Invariant(s)", "Severity", "Suggested Repair", "Confidence"):
        assert field in text
    assert "No AI-generated prose" in text
    assert "reproducible" in text


def test_four_verdicts_explained():
    text = _read(DECISION_DOC)
    for verdict in ("Accept", "Reject", "Quarantine", "Requires Human Review"):
        assert f"### {verdict}" in text


def test_repository_skills_contract_documented():
    text = _read(SKILLS_DOC)
    assert "Repository Skills" in text
    for phrase in (
        "collects evidence",
        "never mutates repository state",
        "never authorizes transitions",
        "never promotes artifacts",
        "never sends notifications",
        "never bypasses the Repository Transition Validator",
    ):
        assert phrase in text


def test_future_skills_listed():
    text = _read(SKILLS_DOC)
    for skill in (
        "Static Analysis Skill",
        "Security Skill",
        "Performance Skill",
        "Documentation Skill",
        "Dependency Skill",
        "AI Review Skill",
        "Model Review Skill",
    ):
        assert skill in text


def test_decision_composition_prevents_voting_or_override():
    for doc in (DECISION_DOC, SKILLS_DOC):
        text = _read(doc)
        assert "never vote" in text or "never:" in text
        assert "override" in text
        assert "centralized" in text


def test_canonical_mermaid_diagram_present():
    text = _read(DECISION_DOC)
    assert "```mermaid" in text
    assert "flowchart TD" in text
    diagram = text[text.index("```mermaid") :]
    for node in (
        "Repository State",
        "Evidence Providers",
        "Evidence",
        "Decision Framework",
        "Transition Validator",
        "Transition Result",
        "Repository Artifact",
        "Repository Event",
        "Notification Policy",
        "Consumers",
    ):
        assert node in diagram


def test_model_independence_documented():
    for doc in (DECISION_DOC, SKILLS_DOC, PHASE_DOC):
        text = _read(doc).lower()
        for actor in ("deepseek", "claude", "codex", "glm", "humans"):
            assert actor in text
        assert "without architectural change" in text


def test_phase_report_covers_requested_sections():
    text = _read(PHASE_DOC)
    for section in (
        "Decision Framework Summary",
        "Evidence Architecture",
        "Evidence Providers",
        "Decision Evaluation",
        "Explainability Model",
        "Verdict Review",
        "Repository Skills Architecture",
        "Canonical Wire Diagram",
        "Future Architecture",
    ):
        assert section in text


def test_no_runtime_implementation_claims():
    for doc in (DECISION_DOC, SKILLS_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "class Evidence",
            "def collect_evidence",
            "def evaluate_decision",
            "def invoke_skill",
            "EventBus",
            "REST endpoint",
            "Telegram inbound implemented",
        ):
            assert forbidden not in text, f"{doc.name} appears to claim implementation: {forbidden}"


def test_execution_unavailable_confirmed():
    for doc in (DECISION_DOC, SKILLS_DOC, PHASE_DOC):
        assert "Execution capability remains unavailable" in _read(doc)
