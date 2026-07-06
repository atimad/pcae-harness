"""Phase 115Q: Advisory Repository Skills Contract Freeze.

Documentation/architecture verification only. These tests prove that
the Advisory Repository Skills contract is frozen and preserves the
no-implementation, no-model-call, no-backend-integration,
no-execution boundary. No Advisory Repository Skill, no Advisory
Provider, no model call, no DeepSeek/GLM/Claude/Codex/Qwen/OpenAI/
local-SLM/any-backend integration, no model configuration, and no
change to Repository Skills, Evidence Providers, Decision Evaluation,
the Repository Transition Validator, or lifecycle commands is
implemented by this phase.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_DOC = REPO_ROOT / "docs" / "PCAE_ADVISORY_REPOSITORY_SKILLS_CONTRACT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_115Q_ADVISORY_REPOSITORY_SKILLS_CONTRACT_FREEZE.md"


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
        assert "Advisory Repository Skills produce evidence" in text
        assert "They never decide" in text


def test_backend_agnostic_principle_documented():
    text = _normalized(CONTRACT_DOC)
    assert "Backend-Agnostic Principle" in text
    assert "must not depend directly on a specific model backend" in text
    assert "AdvisoryProvider" in text


def test_advisory_repository_skill_contract_frozen():
    text = _normalized(CONTRACT_DOC)
    assert "Advisory Repository Skill Contract" in text
    for declaration in (
        "Advisory capability",
        "Evidence categories produced",
        "Probabilistic determinism by default",
        "Model-produced evidence boundary",
    ):
        assert declaration in text, declaration
    for responsibility in (
        "build a prompt/request",
        "consume a normalized advisory response",
        "produce",
    ):
        assert responsibility in text, responsibility
    for forbidden in (
        "decision making",
        "repository mutation",
        "lifecycle authority",
        "commit",
        "push",
        "finalize",
        "notification dispatch",
        "artifact promotion",
        "execution",
        "authorization",
        "validator bypass",
    ):
        assert forbidden in text, forbidden


def test_advisory_provider_abstraction_frozen():
    text = _read(CONTRACT_DOC)
    assert "Advisory Provider Abstraction" in text
    for type_name in (
        "AdvisoryProvider",
        "AdvisoryRequest",
        "RawAdvisoryResponse",
        "NormalizedAdvisoryResponse",
    ):
        assert type_name in text, type_name


def test_advisory_provider_fields_frozen():
    text = _normalized(CONTRACT_DOC)
    for field in ("provider_id", "backend_kind", "determinism", "invoke("):
        assert field in text, field


def test_advisory_request_fields_frozen():
    text = _normalized(CONTRACT_DOC)
    for field in ("bounded_context", "question", "response_schema_hint", "timeout_seconds"):
        assert field in text, field


def test_raw_advisory_response_fields_frozen():
    text = _normalized(CONTRACT_DOC)
    for field in ("raw_content", "succeeded"):
        assert field in text, field


def test_normalized_advisory_response_fields_frozen():
    text = _normalized(CONTRACT_DOC)
    for field in ("findings", "confidence_signal", "references", "limitations", "normalization_status"):
        assert field in text, field


def test_no_provider_implemented_but_future_providers_named():
    text = _normalized(CONTRACT_DOC)
    assert "No provider is implemented in this phase" in text
    for provider in (
        "DeepSeek", "Claude", "Codex", "GLM", "Qwen", "OpenAI",
        "local SLM", "external review service", "deterministic mock",
    ):
        assert provider in text, provider


def test_same_model_default_documented():
    text = _normalized(CONTRACT_DOC)
    assert "Default Same-Model Mode" in text
    for phrase in (
        "current acting model",
        "architecture rule, not an implementation",
        "no separate",
        "configuration is required for default mode",
    ):
        assert phrase in text, phrase


def test_same_model_default_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    assert "current acting model" in text.lower()
    assert "no separate configuration is required for default mode" in text.lower()


def test_split_model_future_mode_documented_not_implemented():
    text = _normalized(CONTRACT_DOC)
    assert "Split-Model Future Mode" in text
    for phrase in (
        "writer model",
        "advisory model",
        "Configuration is only needed for this split-model mode",
        "never for default same-model mode",
    ):
        assert phrase in text, phrase


def test_split_model_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    assert "writer model" in text.lower()
    assert "advisory model" in text.lower()
    assert "not implemented" in text.lower()


def test_prompt_boundary_frozen():
    text = _normalized(CONTRACT_DOC)
    assert "Prompt Boundary" in text
    for phrase in (
        "receive bounded repository context",
        "receive an explicit task/question",
        "include no secrets",
        "include no unrestricted command capability",
        "include no execution request",
        "produce an advisory request only",
    ):
        assert phrase in text, phrase


def test_response_boundary_frozen():
    text = _normalized(CONTRACT_DOC)
    assert "Response Boundary" in text
    assert "Raw model output is never trusted directly" in text
    assert "Normalizer" in text
    assert "Evidence Builder" in text
    assert "Only canonical" in text
    assert "Evidence` enters PCAE" in text or "Evidence enters PCAE" in text


def test_response_boundary_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    assert "never trusted directly" in text.lower()
    assert "only canonical" in text.lower()


def test_evidence_builder_contract_frozen():
    text = _normalized(CONTRACT_DOC)
    assert "Evidence Builder Contract" in text
    for phrase in (
        "probabilistic by default",
        "model-produced if applicable",
        "advisory only",
        "confidence-labelled",
        "limitation-labelled",
        "provenance-preserving",
        "never sole authority for Accept",
    ):
        assert phrase in text, phrase


def test_failure_contract_frozen():
    text = _normalized(CONTRACT_DOC)
    assert "Failure Contract" in text
    for phrase in (
        "UNKNOWN",
        "Explicit advisory failure result",
        "Never silent success",
        "Never hidden partial output",
    ):
        assert phrase in text, phrase


def test_failure_behavior_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    assert "unknown" in text.lower()
    assert "never silently succeed" in text.lower() or "never silent success" in text.lower()


def test_safety_rules_frozen():
    text = _normalized(CONTRACT_DOC)
    assert "Safety Rules" in text
    for rule in (
        "execute commands",
        "request shell access",
        "mutate the repository",
        "authorize transitions",
        "override deterministic evidence",
        "override the validator",
        "produce final lifecycle decisions",
        "send notifications",
        "access secrets",
    ):
        assert rule in text, rule


def test_safety_rules_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    for rule in ("execute commands", "shell access", "mutate the repository", "access secrets"):
        assert rule in text.lower(), rule


def test_first_pilot_scope_frozen():
    text = _normalized(CONTRACT_DOC)
    assert "First Future Pilot Scope" in text
    for in_scope in (
        "repository consistency review",
        "documentation consistency review",
        "report consistency review",
    ):
        assert in_scope in text, in_scope
    for out_of_scope in (
        "code execution",
        "security authorization",
        "lifecycle control",
        "autonomous repair",
    ):
        assert out_of_scope in text, out_of_scope


def test_first_pilot_scope_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    for phrase in (
        "repository consistency review",
        "documentation consistency review",
        "report consistency review",
        "security authorization",
        "autonomous repair",
    ):
        assert phrase in text.lower(), phrase


def test_mermaid_diagrams_present_in_contract_doc():
    text = _read(CONTRACT_DOC)
    assert text.count("```mermaid") >= 2
    first_diagram = text[text.index("```mermaid"):]
    for node in (
        "Repository State",
        "Advisory Repository Skill",
        "Prompt Builder",
        "Advisory Provider",
        "Raw Advisory Response",
        "Normalizer",
        "Normalized Advisory Response",
        "Evidence Builder",
        "Evidence Collection",
        "Decision Evaluation",
        "Repository Transition Validator",
    ):
        assert node in first_diagram, node


def test_second_diagram_shows_swappable_providers():
    text = _read(CONTRACT_DOC)
    second_start = text.index("```mermaid", text.index("```mermaid") + 1)
    second_diagram = text[second_start:]
    for node in (
        "AdvisoryProvider interface",
        "current_acting_model",
        "deepseek",
        "claude",
        "deterministic_mock",
    ):
        assert node in second_diagram, node


def test_mermaid_mentioned_in_phase_doc():
    assert "Mermaid" in _read(PHASE_DOC)


def test_relationship_to_prior_phases_documented():
    text = _read(CONTRACT_DOC)
    for phase in ("115H", "115I", "115P", "115J", "115K"):
        assert phase in text


def test_no_new_manifest_field_required():
    text = _normalized(CONTRACT_DOC).lower()
    assert "no manifest schema change is required" in text or "no schema change" in text or "no new field" in text


def test_phase_report_covers_requested_sections():
    text = _read(PHASE_DOC)
    for section in (
        "Advisory Contract Summary",
        "Advisory Provider Abstraction",
        "Prompt Boundary",
        "Response Normalization Boundary",
        "Evidence Builder Contract",
        "Same-Model Default",
        "Split-Model Future Mode",
        "Safety Rules",
        "First Pilot Scope",
        "Wire Diagram Summary",
    ):
        assert section in text, section


def test_no_implementation_claims():
    for doc in (CONTRACT_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "class AdvisoryProvider",
            "class AdvisoryRepositorySkill",
            "def invoke_advisory_provider",
            "def call_deepseek",
            "def call_claude",
            "src/pcae/core/advisory_provider.py",
            "src/pcae/core/advisory_repository_skill.py",
            "REST endpoint",
            "Telegram inbound implemented",
            "PCAE_ADVISORY_MODEL=",
        ):
            assert forbidden not in text, f"{doc.name} appears to claim implementation: {forbidden}"


def test_no_deepseek_or_backend_integration_claimed():
    for doc in (CONTRACT_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "deepseek is integrated", "glm is integrated", "claude is integrated",
            "codex is integrated", "qwen is integrated", "openai is integrated",
            "now integrated",
        ):
            assert forbidden not in text.lower()


def test_no_new_implementation_module_added():
    forbidden_paths = (
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_provider.py",
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_repository_skill.py",
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_normalizer.py",
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_evidence_builder.py",
    )
    for path in forbidden_paths:
        assert not path.exists(), f"unexpected implementation module added: {path}"


def test_no_existing_module_modified_to_reference_advisory_provider():
    for module_path in (
        REPO_ROOT / "src" / "pcae" / "core" / "repository_skills.py",
        REPO_ROOT / "src" / "pcae" / "core" / "decision_evaluation.py",
        REPO_ROOT / "src" / "pcae" / "core" / "repository_transition_validator.py",
        REPO_ROOT / "src" / "pcae" / "core" / "repository_skills_integration.py",
    ):
        source = module_path.read_text(encoding="utf-8")
        for forbidden in ("AdvisoryProvider", "advisory_provider", "NormalizedAdvisoryResponse"):
            assert forbidden not in source, f"{module_path.name}: {forbidden}"


def test_execution_unavailable_confirmed():
    for doc in (CONTRACT_DOC, PHASE_DOC):
        assert "Execution capability remains unavailable" in _read(doc)


def test_no_go_list_present():
    text = _normalized(PHASE_DOC)
    for phrase in (
        "no Advisory Repository Skill implemented",
        "no Advisory Provider implemented",
        "no model call implemented",
        "No execution",
    ):
        assert phrase in text
