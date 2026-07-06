"""Phase 115U: Advisory Provider Strategy & Extension Point Review.

Documentation/architecture verification only. These tests prove the
Advisory Provider strategy review is documented and preserves the
no-implementation, no-second-provider, no-model-configuration,
no-execution boundary. No second Advisory Provider, no provider
selection, no model configuration, and no DeepSeek/GLM/Qwen/Codex-
specific/OpenAI-specific/Claude-specific/local-SLM integration is
implemented by this phase.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
STRATEGY_DOC = REPO_ROOT / "docs" / "PCAE_ADVISORY_PROVIDER_STRATEGY.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_115U_ADVISORY_PROVIDER_STRATEGY_REVIEW.md"


def _read(path: Path) -> str:
    assert path.exists(), f"expected document missing: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


def test_strategy_doc_exists():
    assert STRATEGY_DOC.exists()


def test_phase_doc_exists():
    assert PHASE_DOC.exists()


def test_core_principle_documented():
    for doc in (STRATEGY_DOC, PHASE_DOC):
        text = _normalized(doc)
        assert "The advisory provider may produce evidence" in text
        assert "PCAE remains the authority" in text


def test_core_question_documented():
    for doc in (STRATEGY_DOC, PHASE_DOC):
        text = _normalized(doc)
        assert "Do we need a second advisory provider now" in text


def test_same_model_default_documented():
    text = _normalized(STRATEGY_DOC)
    assert "Same-model default" in text
    assert "current acting model" in text.lower()


def test_same_model_default_reviewed_and_retained():
    text = _normalized(STRATEGY_DOC)
    for phrase in ("Sound", "current acting model remains"):
        assert phrase in text


def test_second_provider_decision_documented():
    text = _normalized(STRATEGY_DOC)
    assert "## 3. Decision" in text or "Decision" in text
    for phrase in (
        "Implement a second provider now? No.",
        "Defer the second provider? Yes.",
        "Keep the extension point open? Yes.",
    ):
        assert phrase in text, phrase


def test_second_provider_decision_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    assert "Defer." in text
    assert "Do not implement a second provider now" in text


def test_extension_point_documented():
    text = _normalized(STRATEGY_DOC)
    assert "Extension Point Preservation" in text
    assert "AdvisoryProvider" in text
    for concept in (
        "Evidence",
        "EvidenceCollection",
        "Repository Skills",
        "Decision Evaluation",
        "Repository Transition Validator",
        "lifecycle commands",
        "Notification Policy",
    ):
        assert concept in text, concept


def test_extension_point_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    for concept in (
        "evidence", "repository skills", "decision evaluation",
        "repository transition validator", "lifecycle commands", "notification policy",
    ):
        assert concept in text.lower(), concept


def test_future_provider_criteria_documented():
    text = _normalized(STRATEGY_DOC)
    assert "Future Provider Criteria" in text
    for criterion in (
        "Independent review",
        "Better domain expertise",
        "Local/offline advisory",
        "Lower cost",
        "Privacy constraint",
        "Stronger consistency checking",
        "Comparative evidence",
    ):
        assert criterion in text, criterion


def test_future_provider_criteria_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    for criterion in (
        "independent review", "domain expertise", "local/offline advisory",
        "lower cost", "privacy constraint", "consistency checking", "comparative evidence",
    ):
        assert criterion in text, criterion


def test_multi_provider_risks_documented():
    text = _normalized(STRATEGY_DOC)
    assert "Multi-Provider Risks" in text
    for risk in (
        "Conflicting advisory evidence",
        "Provider disagreement",
        "Nondeterministic outputs",
        "Cost/latency",
        "Prompt drift",
        "Provider-specific quirks",
        "Hidden vendor coupling",
        "Operator confusion",
    ):
        assert risk in text, risk


def test_multi_provider_risks_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    for risk in (
        "conflicting advisory evidence", "provider disagreement", "nondeterminism",
        "cost/latency", "prompt drift", "provider-specific quirks",
        "hidden vendor coupling", "operator confusion",
    ):
        assert risk in text, risk


def test_disagreement_handling_documented():
    text = _normalized(STRATEGY_DOC)
    assert "Disagreement Handling" in text
    for phrase in (
        "Preserve all evidence",
        "Mark conflicts",
        "Never average or vote blindly",
        "Deterministic Decision Evaluation handles conflicts",
        "No provider becomes authority",
    ):
        assert phrase in text, phrase


def test_disagreement_handling_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    for phrase in (
        "preserve all evidence", "mark conflicts", "never average or vote blindly",
        "no provider ever becomes authority",
    ):
        assert phrase in text, phrase


def test_configuration_posture_documented():
    text = _normalized(STRATEGY_DOC)
    assert "Configuration Posture" in text
    for phrase in (
        "No provider configuration is needed",
        "current acting model remains the default",
        "Optional",
        "Explicit",
        "Isolated to the provider-selection layer",
        "Never leaks into Decision Evaluation or the Validator",
    ):
        assert phrase in text, phrase


def test_configuration_posture_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    assert "no provider configuration needed" in text
    assert "isolated entirely to the provider-selection layer" in text


def test_roadmap_outcome_documented():
    text = _normalized(STRATEGY_DOC)
    assert "Roadmap Outcome" in text
    assert "higher-quality evidence" in text.lower() or "advisory skill hardening" in text.lower()
    assert "not provider proliferation" in text.lower()


def test_roadmap_outcome_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    assert "higher-quality evidence" in text
    assert "not provider proliferation" in text


def test_multi_provider_evaluation_considerations_documented():
    text = _normalized(STRATEGY_DOC)
    for consideration in (
        "Benefit", "Complexity", "Latency", "Cost", "Reproducibility",
        "Disagreement handling", "Reliability", "Configuration burden",
        "Vendor coupling", "Governance risk",
    ):
        assert consideration in text, consideration


def test_no_implementation_claims():
    for doc in (STRATEGY_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "class SecondAdvisoryProvider",
            "class DeepSeekAdvisoryProvider",
            "class ClaudeAdvisoryProvider",
            "def select_provider",
            "src/pcae/core/second_advisory_provider.py",
            "src/pcae/core/provider_registry.py",
            "REST endpoint",
            "Telegram inbound implemented",
            "PCAE_ADVISORY_PROVIDER=",
        ):
            assert forbidden not in text, f"{doc.name} appears to claim implementation: {forbidden}"


def test_no_new_implementation_module_added():
    forbidden_paths = (
        REPO_ROOT / "src" / "pcae" / "core" / "second_advisory_provider.py",
        REPO_ROOT / "src" / "pcae" / "core" / "provider_registry.py",
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_provider_selection.py",
        REPO_ROOT / "src" / "pcae" / "core" / "deepseek_advisory_provider.py",
        REPO_ROOT / "src" / "pcae" / "core" / "glm_advisory_provider.py",
    )
    for path in forbidden_paths:
        assert not path.exists(), f"unexpected implementation module added: {path}"


def test_no_existing_advisory_module_modified_to_add_provider_selection():
    for module_path in (
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_repository_skills.py",
        REPO_ROOT / "src" / "pcae" / "core" / "current_acting_model_advisory_provider.py",
    ):
        source = module_path.read_text(encoding="utf-8")
        for forbidden in ("provider_registry", "select_provider", "ProviderSelector"):
            assert forbidden not in source, f"{module_path.name}: {forbidden}"


def test_no_deepseek_or_backend_integration_claimed():
    for doc in (STRATEGY_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "deepseek is integrated", "glm is integrated", "claude is integrated",
            "codex is integrated", "qwen is integrated", "openai is integrated",
            "now integrated",
        ):
            assert forbidden not in text.lower()


def test_execution_unavailable_confirmed():
    for doc in (STRATEGY_DOC, PHASE_DOC):
        assert "Execution capability remains unavailable" in _read(doc)


def test_no_go_list_present():
    text = _normalized(PHASE_DOC)
    for phrase in (
        "no second Advisory Provider implemented",
        "no provider selection added",
        "no model configuration added",
        "No execution",
    ):
        assert phrase in text
