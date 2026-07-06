"""Phase 115I: Repository Skills Contract Freeze.

Documentation/architecture verification only. These tests prove that
the Repository Skills contract is frozen and preserves the
no-implementation, no-execution boundary. No Repository Skill, no
deterministic skill, no AI/SLM/LLM-backed skill, and no DeepSeek
integration is implemented by this phase.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_SKILLS_CONTRACT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_115I_REPOSITORY_SKILLS_CONTRACT_FREEZE.md"


def _read(path: Path) -> str:
    assert path.exists(), f"expected document missing: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


def test_contract_doc_exists():
    assert CONTRACT_DOC.exists()


def test_phase_doc_exists():
    assert PHASE_DOC.exists()


def test_core_principle_documented():
    for doc in (CONTRACT_DOC, PHASE_DOC):
        text = _read(doc)
        assert "Repository Skills never decide" in text
        assert "Repository Skills produce Evidence" in text
        assert "Repository Skills are model-agnostic" in text


def test_repository_skill_contract_frozen():
    text = _normalized(CONTRACT_DOC)
    assert "Repository Skill Contract" in text
    for declaration in (
        "Capabilities",
        "Evidence categories produced",
        "Determinism class",
        "Confidence defaults",
        "Required repository inputs",
        "Produces `EvidenceCollection`",
    ):
        assert declaration in text
    for forbidden in (
        "repository mutation",
        "decision making",
        "validator bypass",
        "lifecycle authority",
        "artifact promotion",
        "notification dispatch",
        "execution",
        "authorization",
        "commit",
        "push",
        "finalize",
    ):
        assert forbidden in text


def test_capability_model_frozen():
    text = _read(CONTRACT_DOC)
    assert "Repository Skill Capability Model" in text
    assert "RepositorySkillCapability" in text
    for capability in (
        "git_analysis",
        "runtime_analysis",
        "architecture_analysis",
        "documentation_analysis",
        "report_analysis",
        "metadata_analysis",
        "dependency_analysis",
        "ai_review",
    ):
        assert capability in text
    assert "outputs" in text.lower()


def test_manifest_frozen():
    text = _read(CONTRACT_DOC)
    assert "Repository Skill Manifest" in text
    for field in (
        "skill_id",
        "name",
        "version",
        "capability list",
        "determinism",
        "confidence policy",
        "evidence categories",
        "required inputs",
        "optional inputs",
        "timeout",
        "failure policy",
        "side-effect policy",
        "model-produced flag",
        "experimental flag",
    ):
        assert field in text


def test_determinism_classes_frozen():
    for doc in (CONTRACT_DOC, PHASE_DOC):
        text = _read(doc)
        for cls in (
            "deterministic",
            "reproducible_external",
            "probabilistic",
            "human_assisted",
            "experimental",
        ):
            assert cls in text


def test_failure_contract_frozen():
    text = _normalized(CONTRACT_DOC)
    assert "Failure Contract" in text
    assert "UNKNOWN" in text
    assert "explicit failure outcome" in text or "explicit, structured failure" in text
    assert "Never partial hidden failure" in text or "never partial hidden failure" in text.lower()
    assert "Never silent success" in text or "never silent success" in text.lower()


def test_execution_boundary_frozen():
    text = _read(CONTRACT_DOC)
    assert "Execution Boundary" in text
    for phrase in (
        "invoke runtime execution",
        "authorize execution",
        "approve transitions",
        "override evidence",
        "override other skills",
        "override the validator",
    ):
        assert phrase in text


def test_advisory_boundary_frozen():
    text = _normalized(CONTRACT_DOC)
    assert "Advisory Skill Boundary" in text
    for actor in ("DeepSeek", "GLM", "GPT", "Qwen"):
        assert actor in text
    for phrase in (
        "advisory evidence only",
        "probabilistic",
        "labelled model-produced",
        "never become sole authority",
        "never bypass Decision Evaluation",
    ):
        assert phrase in text


def test_composition_model_frozen():
    text = _read(CONTRACT_DOC)
    assert "Composition Model" in text
    assert "multiple" in text
    assert "Evidence Providers" in text
    assert "EvidenceCollection" in text
    assert "never sees" in text.lower() or "never see" in text.lower()


def test_explainability_requirements_frozen():
    text = _normalized(CONTRACT_DOC)
    assert "Explainability Requirements" in text
    assert "provenance" in text.lower()
    assert "Evidence IDs" in text
    assert "regardless of which Repository Skill produced" in text


def test_mermaid_diagram_present_in_both_docs():
    for doc in (CONTRACT_DOC, PHASE_DOC):
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
    text = _read(CONTRACT_DOC)
    diagram = text[text.index("```mermaid"):]
    assert "EP --> RSK" in diagram
    assert "RSK --> EC" in diagram


def test_phase_report_covers_requested_sections():
    text = _read(PHASE_DOC)
    for section in (
        "Repository Skill Contract Summary",
        "Capability Model",
        "Manifest Summary",
        "Determinism Classes",
        "Failure Contract",
        "Advisory Boundary",
        "Composition Model",
        "Explainability Summary",
        "Wire Diagram",
    ):
        assert section in text


def test_no_implementation_claims():
    for doc in (CONTRACT_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "class RepositorySkill:",
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
        REPO_ROOT / "src" / "pcae" / "core" / "skill_manifest.py",
    )
    for path in forbidden_paths:
        assert not path.exists(), f"unexpected implementation module added: {path}"


def test_execution_unavailable_confirmed():
    for doc in (CONTRACT_DOC, PHASE_DOC):
        assert "Execution capability remains unavailable" in _read(doc)


def test_no_go_list_present():
    text = _normalized(PHASE_DOC)
    for phrase in (
        "no Repository Skill implemented",
        "no deterministic skill implemented",
        "no AI/SLM/LLM-backed skill implemented",
        "no DeepSeek integration",
    ):
        assert phrase in text
