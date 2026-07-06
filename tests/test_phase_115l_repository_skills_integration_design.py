"""Phase 115L: Repository Skills Integration Design.

Documentation/architecture verification only. These tests prove that
the Repository Skills integration architecture is documented and
preserves the no-implementation, no-execution boundary. No Repository
Skills integration, no Repository Skill modification, no Evidence
Provider modification, no Decision Evaluation modification, and no
Repository Transition Validator modification is implemented by this
phase.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
INTEGRATION_ARCH_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_SKILLS_INTEGRATION_ARCHITECTURE.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_115L_REPOSITORY_SKILLS_INTEGRATION_DESIGN.md"


def _read(path: Path) -> str:
    assert path.exists(), f"expected document missing: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


def test_integration_architecture_doc_exists():
    assert INTEGRATION_ARCH_DOC.exists()


def test_phase_doc_exists():
    assert PHASE_DOC.exists()


def test_integration_architecture_documented():
    text = _normalized(INTEGRATION_ARCH_DOC)
    assert "Integration Architecture" in text
    assert "sole orchestrators of Evidence Providers" in text
    assert "Decision Evaluation no longer knows" in text or "receives only" in text


def test_integration_boundary_documented():
    text = _read(INTEGRATION_ARCH_DOC)
    assert "Integration Boundary" in text
    for phrase in (
        "construct providers",
        "discover providers",
        "call providers directly",
        "know provider ordering",
    ):
        assert phrase in text


def test_orchestration_model_documented():
    text = _normalized(INTEGRATION_ARCH_DOC)
    assert "Orchestration Model" in text
    for phrase in ("zero providers", "one provider", "multiple providers"):
        assert phrase in text
    assert "merges its" in text or "merge" in text.lower()


def test_skill_composition_documented():
    text = _normalized(INTEGRATION_ARCH_DOC)
    assert "Skill Composition" in text
    assert "sub-skill" in text.lower()
    assert "No recursive cycles" in text or "no recursive cycles" in text.lower()
    assert "deterministic ordering" in text.lower() or "deterministic" in text.lower()


def test_compatibility_guarantees_documented():
    text = _read(INTEGRATION_ARCH_DOC)
    assert "Compatibility Guarantees" in text
    for phrase in (
        "No provider API changes",
        "No Decision Evaluation semantic changes",
        "No Transition Validator behavior changes",
        "No lifecycle command changes",
    ):
        assert phrase in text


def test_migration_strategy_documented():
    text = _read(INTEGRATION_ARCH_DOC)
    assert "Migration Strategy" in text
    for stage in ("Stage 1", "Stage 2", "Stage 3", "Stage 4"):
        assert stage in text


def test_dependency_direction_documented():
    text = _normalized(INTEGRATION_ARCH_DOC)
    assert "Dependency Direction" in text
    assert "No reverse dependency" in text or "no reverse dependency" in text.lower()
    for phrase in (
        "Repository Skills depend on Evidence Providers",
        "Decision Evaluation depends only on Evidence",
    ):
        assert phrase in text


def test_ai_insertion_point_documented():
    text = _read(INTEGRATION_ARCH_DOC)
    assert "Future AI Insertion Point" in text
    for actor in ("DeepSeek", "GLM", "GPT", "Qwen"):
        assert actor in text
    assert "Repository State remains authoritative" in text


def test_mermaid_diagram_present_in_both_docs():
    for doc in (INTEGRATION_ARCH_DOC, PHASE_DOC):
        text = _read(doc)
        assert "```mermaid" in text
        assert "flowchart TD" in text
        diagram = text[text.index("```mermaid"):]
        for node in (
            "Repository State",
            "Evidence Providers",
            "Repository Skills",
            "Deterministic Skills",
            "Advisory Skills",
            "Evidence Collection",
            "Decision Evaluation",
            "Repository Transition Validator",
            "Transition Result",
            "Repository Artifact",
            "Repository Event",
            "Notification Policy",
            "Consumers",
        ):
            assert node in diagram, node


def test_wire_diagram_shows_deterministic_and_advisory_as_parallel():
    text = _read(INTEGRATION_ARCH_DOC)
    diagram = text[text.index("```mermaid"):]
    assert "EP --> DET" in diagram
    assert "EP --> ADV" in diagram
    assert "DET --> EC" in diagram
    assert "ADV --> EC" in diagram


def test_phase_report_covers_requested_sections():
    text = _read(PHASE_DOC)
    for section in (
        "Integration Architecture Summary",
        "Orchestration Summary",
        "Migration Strategy",
        "Dependency Direction",
        "Compatibility Guarantees",
        "AI Insertion Point",
        "Wire Diagram Summary",
    ):
        assert section in text


def test_no_implementation_claims():
    for doc in (INTEGRATION_ARCH_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "class RepositorySkillOrchestrator",
            "def integrate_repository_skills",
            "def orchestrate_providers",
            "src/pcae/core/repository_skills_integration.py",
            "REST endpoint",
            "Telegram inbound implemented",
        ):
            assert forbidden not in text, f"{doc.name} appears to claim implementation: {forbidden}"


def test_no_new_implementation_module_added():
    forbidden_paths = (
        REPO_ROOT / "src" / "pcae" / "core" / "repository_skills_integration.py",
        REPO_ROOT / "src" / "pcae" / "core" / "skill_orchestration.py",
    )
    for path in forbidden_paths:
        assert not path.exists(), f"unexpected implementation module added: {path}"


def test_no_existing_module_modified_to_reference_repository_skills():
    """115L is design-only: repository_transition_validator.py,
    decision_evaluation.py, and repository_transition_integration.py
    must still not reference repository_skills (unchanged since 115K)."""
    for module_path in (
        REPO_ROOT / "src" / "pcae" / "core" / "decision_evaluation.py",
        REPO_ROOT / "src" / "pcae" / "core" / "repository_transition_validator.py",
        REPO_ROOT / "src" / "pcae" / "core" / "repository_transition_integration.py",
    ):
        source = module_path.read_text(encoding="utf-8")
        assert "repository_skills" not in source, module_path


def test_execution_unavailable_confirmed():
    for doc in (INTEGRATION_ARCH_DOC, PHASE_DOC):
        assert "Execution capability remains unavailable" in _read(doc)


def test_no_go_list_present():
    text = _normalized(PHASE_DOC)
    for phrase in (
        "no Repository Skills integration implemented",
        "no Repository Skill modified",
        "no Evidence Provider modified",
        "no Decision Evaluation modified",
    ):
        assert phrase in text
