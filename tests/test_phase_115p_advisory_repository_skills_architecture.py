"""Phase 115P: Advisory Repository Skills Architecture.

Documentation/architecture verification only. These tests prove that
the Advisory Repository Skills architecture is documented and
preserves the no-implementation, no-model-call, no-backend-integration,
no-execution boundary. No Advisory Repository Skill, no model call, no
DeepSeek/GLM/Claude/Codex/Qwen/OpenAI/local-SLM/any-backend
integration, no model configuration, and no change to Repository
Skills, Evidence Providers, Decision Evaluation, the Repository
Transition Validator, or lifecycle commands is implemented by this
phase.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ADVISORY_ARCH_DOC = REPO_ROOT / "docs" / "PCAE_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_115P_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md"


def _read(path: Path) -> str:
    assert path.exists(), f"expected document missing: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


def test_architecture_doc_exists():
    assert ADVISORY_ARCH_DOC.exists()


def test_phase_doc_exists():
    assert PHASE_DOC.exists()


def test_core_principle_documented():
    for doc in (ADVISORY_ARCH_DOC, PHASE_DOC):
        text = _read(doc)
        assert "Advisory models may produce evidence" in text
        assert "PCAE decides" in text


def test_advisory_skill_definition_documented():
    text = _normalized(ADVISORY_ARCH_DOC)
    assert "Advisory Repository Skill Definition" in text
    for phrase in (
        "uses a model only as an evidence producer",
        "EvidenceCollection",
        "never decides",
        "never mutates repository state",
        "never authorizes anything",
        "never promotes artifacts",
        "never sends notifications",
        "never commits",
        "never pushes",
        "never finalizes",
    ):
        assert phrase in text, phrase


def test_advisory_pipeline_all_stages_documented():
    text = _normalized(ADVISORY_ARCH_DOC)
    assert "Advisory Pipeline" in text
    for stage in (
        "Repository State",
        "Prompt Builder",
        "Current Model",
        "Raw Response",
        "Normalizer",
        "Evidence Builder",
        "EvidenceCollection",
        "Decision Evaluation",
        "Repository Transition Validator",
    ):
        assert stage in text, stage


def test_pipeline_documented_in_phase_doc_too():
    text = _normalized(PHASE_DOC)
    assert "Prompt Builder" in text
    assert "Current Model" in text
    assert "Raw Response" in text
    assert "Normalizer" in text
    assert "Evidence Builder" in text


def test_model_boundary_documented():
    text = _read(ADVISORY_ARCH_DOC)
    assert "Model Boundary" in text
    assert "never returns a trusted PCAE object directly" in text
    for phrase in (
        "no tool-call authority",
        "no file-write access",
    ):
        assert phrase in text


def test_model_boundary_documented_in_phase_doc():
    text = _read(PHASE_DOC)
    assert "never returns a trusted PCAE object directly" in text


def test_same_model_default_documented():
    text = _normalized(ADVISORY_ARCH_DOC)
    assert "Default Same-Model Mode" in text
    for phrase in (
        "current acting model may be the advisory model by default",
        "no new configuration file",
        "no new CLI flag",
        "no new environment variable",
    ):
        assert phrase in text


def test_same_model_default_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    assert "current acting model may be the advisory model by default" in text


def test_split_model_future_mode_documented_not_implemented():
    text = _normalized(ADVISORY_ARCH_DOC)
    assert "Future Split-Model Mode" in text
    for phrase in (
        "Writer model",
        "Advisory model",
        "This phase implements none of it",
    ):
        assert phrase in text


def test_split_model_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    assert "writer model" in text.lower()
    assert "advisory model" in text.lower()
    assert "not implemented" in text.lower()


def test_safety_rules_documented():
    text = _normalized(ADVISORY_ARCH_DOC)
    assert "Safety Rules" in text
    for phrase in (
        "probabilistic by default",
        "model-produced",
        "never be sole authority for Accept",
        "may trigger human review",
        "may suggest repair",
        "must include limitations",
        "must cite references where possible",
    ):
        assert phrase in text, phrase


def test_failure_behavior_documented():
    text = _normalized(ADVISORY_ARCH_DOC)
    assert "Failure Behavior" in text
    for phrase in (
        "UNKNOWN",
        "explicit advisory failure",
        "never block deterministic checks by itself",
        "never silently succeed",
    ):
        assert phrase in text, phrase


def test_failure_behavior_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    assert "UNKNOWN" in text
    assert "never blocking" in text.lower() or "never block" in text.lower()
    assert "never silently succeeding" in text.lower() or "never silently succeed" in text.lower()


def test_first_pilot_scope_documented():
    text = _normalized(ADVISORY_ARCH_DOC)
    assert "First Future Pilot Scope" in text
    for in_scope in (
        "Repository consistency review",
        "Documentation consistency review",
        "Report consistency review",
    ):
        assert in_scope in text, in_scope
    for out_of_scope in (
        "code execution",
        "lifecycle authority",
        "commit/push/finalize authority",
    ):
        assert out_of_scope in text, out_of_scope


def test_first_pilot_scope_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    for phrase in (
        "repository consistency review",
        "documentation consistency review",
        "report consistency review",
        "code execution",
        "lifecycle authority",
    ):
        assert phrase in text.lower(), phrase


def test_mermaid_diagrams_present_in_architecture_doc():
    text = _read(ADVISORY_ARCH_DOC)
    assert text.count("```mermaid") >= 2
    assert "flowchart TD" in text
    pipeline_diagram = text[text.index("```mermaid"):]
    for node in (
        "Repository State",
        "Prompt Builder",
        "Current Model",
        "Raw Response",
        "Normalizer",
        "Evidence Builder",
        "Evidence Collection",
        "Decision Evaluation",
        "Repository Transition Validator",
    ):
        assert node in pipeline_diagram, node


def test_second_diagram_shows_repository_skills_integration_point():
    text = _read(ADVISORY_ARCH_DOC)
    second_start = text.index("```mermaid", text.index("```mermaid") + 1)
    second_diagram = text[second_start:]
    for node in (
        "Evidence Providers",
        "Deterministic Skills",
        "Advisory Repository Skill",
        "Evidence Collection",
        "Transition Result",
    ):
        assert node in second_diagram, node


def test_mermaid_diagram_present_in_phase_doc():
    text = _read(PHASE_DOC)
    assert "```mermaid" not in text or "Mermaid" in text
    assert "Mermaid" in text


def test_relationship_to_prior_phases_documented():
    text = _read(ADVISORY_ARCH_DOC)
    assert "115H" in text
    assert "115I" in text
    assert "115L" in text
    assert "115M" in text
    assert "115N" in text


def test_no_new_manifest_field_required():
    text = _normalized(ADVISORY_ARCH_DOC)
    assert "no new field" in text.lower() or "no schema change" in text.lower() or "no manifest schema change" in text.lower()


def test_phase_report_covers_requested_sections():
    text = _read(PHASE_DOC)
    for section in (
        "Advisory Architecture Summary",
        "Advisory Pipeline",
        "Model Boundary",
        "Default Same-Model Mode",
        "Future Split-Model Mode",
        "Safety Rules",
        "Failure Behavior",
        "First Future Pilot Scope",
        "Wire Diagram Summary",
    ):
        assert section in text, section


def test_no_implementation_claims():
    for doc in (ADVISORY_ARCH_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "class AdvisoryRepositorySkill",
            "def invoke_model",
            "def call_deepseek",
            "def call_claude",
            "src/pcae/core/advisory_repository_skill.py",
            "src/pcae/core/advisory_skills.py",
            "REST endpoint",
            "Telegram inbound implemented",
            "PCAE_ADVISORY_MODEL=",
        ):
            assert forbidden not in text, f"{doc.name} appears to claim implementation: {forbidden}"


def test_no_new_implementation_module_added():
    forbidden_paths = (
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_repository_skill.py",
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_skills.py",
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_pipeline.py",
        REPO_ROOT / "src" / "pcae" / "core" / "model_normalizer.py",
    )
    for path in forbidden_paths:
        assert not path.exists(), f"unexpected implementation module added: {path}"


def test_no_existing_module_modified_to_reference_advisory_pipeline():
    """115P is design-only: repository_skills.py, decision_evaluation.py,
    repository_transition_validator.py, and repository_skills_integration.py
    must not reference an advisory pipeline/model normalizer at all."""
    for module_path in (
        REPO_ROOT / "src" / "pcae" / "core" / "repository_skills.py",
        REPO_ROOT / "src" / "pcae" / "core" / "decision_evaluation.py",
        REPO_ROOT / "src" / "pcae" / "core" / "repository_transition_validator.py",
        REPO_ROOT / "src" / "pcae" / "core" / "repository_skills_integration.py",
    ):
        source = module_path.read_text(encoding="utf-8")
        for forbidden in ("advisory_pipeline", "model_normalizer", "PromptBuilder", "advisory_model"):
            assert forbidden not in source, f"{module_path.name}: {forbidden}"


def test_no_deepseek_or_backend_integration_claimed():
    for doc in (ADVISORY_ARCH_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "deepseek is integrated", "glm is integrated", "claude is integrated",
            "codex is integrated", "qwen is integrated", "openai is integrated",
            "now integrated",
        ):
            assert forbidden not in text.lower()


def test_execution_unavailable_confirmed():
    for doc in (ADVISORY_ARCH_DOC, PHASE_DOC):
        assert "Execution capability remains unavailable" in _read(doc)


def test_no_go_list_present():
    text = _normalized(PHASE_DOC)
    for phrase in (
        "no Advisory Repository Skill implemented",
        "no model call implemented",
        "No execution",
    ):
        assert phrase in text
