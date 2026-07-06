"""Phase 115H: Repository Skills Architecture.

Documentation/architecture verification only. These tests prove that
the Repository Skills architecture is documented and preserves the
no-implementation, no-execution boundary. No Repository Skill, no
AI/SLM/LLM-backed skill, no DeepSeek integration, and no change to
Evidence Providers, Decision Evaluation, the Repository Transition
Validator, or lifecycle commands is implemented by this phase.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ARCH_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_SKILLS_ARCHITECTURE.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_115H_REPOSITORY_SKILLS_ARCHITECTURE.md"


def _read(path: Path) -> str:
    assert path.exists(), f"expected document missing: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


def test_architecture_doc_exists():
    assert SKILLS_ARCH_DOC.exists()


def test_phase_doc_exists():
    assert PHASE_DOC.exists()


def test_repository_skill_definition_documented():
    text = _normalized(SKILLS_ARCH_DOC)
    assert "Repository Skill Definition" in text
    assert "A Repository Skill **never**:" in text
    for phrase in (
        "observes repository state",
        "collects or derives evidence",
        "may enrich existing evidence",
        "EvidenceCollection",
        "mutates repository state",
        "decides (produces no `TransitionVerdict`",
        "votes (has no weighted or unweighted say",
        "authorizes anything",
        "promotes artifacts",
        "sends notifications",
        "bypasses the Repository Transition Validator",
        "invokes execution",
    ):
        assert phrase in text, phrase


def test_core_principle_documented():
    for doc in (SKILLS_ARCH_DOC, PHASE_DOC):
        text = _read(doc)
        assert "Repository Skills produce evidence" in text
        assert "Repository Skills do not" in text


def test_skill_classes_defined():
    text = _read(SKILLS_ARCH_DOC)
    assert "Skill Classes" in text
    for skill_class in (
        "Deterministic",
        "Reproducible External",
        "Advisory",
        "Human-Assisted",
        "Experimental",
    ):
        assert skill_class in text


def test_deterministic_skill_examples_defined():
    text = _read(SKILLS_ARCH_DOC)
    for skill in (
        "Git Topology Skill",
        "Report Consistency Skill",
        "Metadata Consistency Skill",
        "Architecture Status Skill",
        "Documentation Completeness Skill",
        "Test-Result Consistency Skill",
    ):
        assert skill in text


def test_advisory_skill_boundary_defined():
    text = _read(SKILLS_ARCH_DOC)
    assert "Advisory Skills" in text
    for phrase in (
        "advisory only",
        "probabilistic by default",
        "labelled model-produced",
        "never sole authority for Accept",
        "never allowed to mutate repository state",
        "never allowed to finalize, push, or notify",
        "allowed only to produce evidence",
    ):
        assert phrase in text
    for actor in ("deepseek", "glm", "qwen", "claude", "codex"):
        assert actor in text.lower()


def test_deepseek_future_pilot_boundary_defined():
    for doc in (SKILLS_ARCH_DOC, PHASE_DOC):
        text = _read(doc)
        assert "DeepSeek Future Pilot Boundary" in text or "DeepSeek must not be reintroduced as lifecycle authority" in text
        assert "must not be reintroduced as lifecycle authority" in text
        assert "bounded Advisory" in text


def test_skill_lifecycle_defined():
    text = _normalized(SKILLS_ARCH_DOC)
    assert "Repository Skill Lifecycle" in text
    for stage in (
        "registered",
        "configured",
        "invoked",
        "evidence produced",
        "evidence validated",
        "evidence consumed by Decision Evaluation",
        "result referenced in explanation",
    ):
        assert stage in text


def test_skill_manifest_concept_defined():
    text = _read(SKILLS_ARCH_DOC)
    assert "Skill Manifest Concept" in text
    for field in (
        "skill_id",
        "name",
        "version",
        "class",
        "determinism",
        "categories produced",
        "required inputs",
        "allowed outputs",
        "side-effect policy",
        "timeout policy",
        "failure behavior",
        "confidence defaults",
        "model-produced flag",
    ):
        assert field in text


def test_safety_boundary_defined():
    text = _read(SKILLS_ARCH_DOC)
    assert "Skill Safety Boundary" in text
    for owned_concept in (
        "Repository State",
        "Repository Transition",
        "Repository Artifact promotion",
        "Repository Event emission",
        "Notification Policy",
        "lifecycle authority",
        "execution authority",
    ):
        assert owned_concept in text


def test_mermaid_diagram_present_in_both_docs():
    for doc in (SKILLS_ARCH_DOC, PHASE_DOC):
        text = _read(doc)
        assert "```mermaid" in text
        assert "flowchart TD" in text
        diagram = text[text.index("```mermaid"):]
        for node in (
            "Repository State",
            "Evidence Providers",
            "Repository Skills",
            "Evidence Collection",
            "Decision Evaluation",
            "Repository Transition Validator",
            "Transition Result",
            "Repository Artifact",
            "Repository Event",
            "Notification Policy",
            "Consumers",
        ):
            assert node in diagram


def test_wire_diagram_orders_skills_between_providers_and_evidence():
    text = _read(SKILLS_ARCH_DOC)
    diagram = text[text.index("```mermaid"):]
    assert "EP --> RSK" in diagram
    assert "RSK --> EC" in diagram


def test_phase_report_covers_requested_sections():
    text = _read(PHASE_DOC)
    for section in (
        "Repository Skills Architecture Summary",
        "Skill Class Summary",
        "Evidence-Only Boundary",
        "Advisory / AI Skill Boundary",
        "DeepSeek Future Pilot Boundary",
        "Skill Lifecycle Summary",
        "Skill Manifest Concept",
        "Skill Safety Boundary",
        "Wire Diagram Summary",
    ):
        assert section in text


def test_no_implementation_claims():
    for doc in (SKILLS_ARCH_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "class RepositorySkill",
            "def invoke_skill",
            "def register_skill",
            "src/pcae/core/repository_skills.py",
            "src/pcae/core/skills.py",
            "REST endpoint",
            "Telegram inbound implemented",
        ):
            assert forbidden not in text, f"{doc.name} appears to claim implementation: {forbidden}"


def test_no_new_implementation_module_added():
    forbidden_paths = (
        REPO_ROOT / "src" / "pcae" / "core" / "repository_skills.py",
        REPO_ROOT / "src" / "pcae" / "core" / "skills.py",
        REPO_ROOT / "src" / "pcae" / "core" / "skill_registry.py",
    )
    for path in forbidden_paths:
        assert not path.exists(), f"unexpected implementation module added: {path}"


def test_execution_unavailable_confirmed():
    for doc in (SKILLS_ARCH_DOC, PHASE_DOC):
        assert "Execution capability remains unavailable" in _read(doc)


def test_no_go_list_present():
    text = _normalized(PHASE_DOC)
    for phrase in (
        "no Repository Skill implemented",
        "no AI/SLM/LLM-backed skill implemented",
        "No execution",
        "Permission Broker enforcement",
    ):
        assert phrase in text
