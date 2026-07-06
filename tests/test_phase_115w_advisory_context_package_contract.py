"""Phase 115W: Advisory Context Package Contract.

Documentation/architecture verification only. These tests prove the
Advisory Context Package contract is frozen and preserves the
no-implementation, no-execution boundary. No AdvisoryContextPackage
runtime, no Advisory Provider runtime change, no Repository Skill, no
Evidence Provider, no Decision Evaluation, no Repository Transition
Validator, and no lifecycle command is implemented or modified by
this phase.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_DOC = REPO_ROOT / "docs" / "PCAE_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_115W_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md"


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
        text = _normalized(doc)
        assert "Advisory models receive bounded, trusted, provenance-preserving context" in text
        assert "They do not receive unrestricted repository access" in text


def test_required_sections_documented():
    text = _normalized(CONTRACT_DOC)
    assert "Required Sections" in text
    for section in (
        "package_id",
        "created_at_utc",
        "objective",
        "advisory_question",
        "trusted_pcae_instructions",
        "repository_summary",
        "deterministic_evidence_summary",
        "transition_context",
        "constraints_and_no_go_rules",
        "artifact_references",
        "untrusted_repository_content",
        "provenance",
        "limitations",
        "size_budget",
        "redaction_summary",
    ):
        assert section in text, section


def test_required_sections_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    for section in (
        "package_id", "created_at_utc", "objective", "advisory_question",
        "trusted_pcae_instructions", "repository_summary",
        "deterministic_evidence_summary", "transition_context",
        "constraints_and_no_go_rules", "artifact_references",
        "untrusted_repository_content", "provenance", "limitations",
        "size_budget", "redaction_summary",
    ):
        assert section in text, section


def test_fifteen_sections_no_optional_language():
    text = _normalized(CONTRACT_DOC)
    assert "15 required sections" in text or "exactly these sections" in text
    assert "No section is optional" in text


def test_trust_boundaries_documented():
    text = _normalized(CONTRACT_DOC)
    assert "Trust Boundaries" in text
    for boundary_class in (
        "Trusted PCAE instructions",
        "Deterministic PCAE evidence",
        "Untrusted repository content",
        "Model-produced advisory output",
    ):
        assert boundary_class in text, boundary_class


def test_trust_boundaries_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    for boundary_class in (
        "trusted pcae instructions", "deterministic pcae evidence",
        "untrusted repository content", "model-produced advisory output",
    ):
        assert boundary_class in text, boundary_class


def test_prompt_injection_boundary_documented():
    text = _normalized(CONTRACT_DOC)
    assert "Prompt-Injection Boundary" in text
    for phrase in (
        "must be treated as untrusted",
        "always its own section",
        "clearly delimited",
        "No instruction found inside",
        "assembled last",
    ):
        assert phrase in text, phrase


def test_prompt_injection_boundary_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    assert "structurally separate" in text
    assert "delimited and labelled" in text
    assert "assembled last" in text


def test_size_limits_documented():
    text = _normalized(CONTRACT_DOC)
    assert "Size Limits" in text
    for phrase in (
        "Total package budget concept",
        "Per-section budget concept",
        "Deterministic summarization requirement",
        "No unbounded repository dumps",
    ):
        assert phrase in text, phrase


def test_size_limits_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    assert "total package budget" in text
    assert "per-section budget" in text
    assert "unbounded" in text


def test_redaction_policy_documented():
    text = _normalized(CONTRACT_DOC)
    assert "Redaction" in text
    for forbidden_content in (
        "secrets", "tokens", "credentials", "private env values",
        "unrestricted logs", "raw config secrets",
    ):
        assert forbidden_content in text.lower(), forbidden_content
    assert "redaction_summary" in text


def test_redaction_policy_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    for forbidden_content in ("secrets", "tokens", "credentials", "private env values"):
        assert forbidden_content in text, forbidden_content


def test_provenance_rules_documented():
    text = _normalized(CONTRACT_DOC)
    assert "## 6. Provenance" in text
    assert "package-level provenance" in text.lower()
    assert "item-level provenance" in text.lower()
    assert "never discarded during summarization" in text.lower() or "never discarded" in text.lower()


def test_provenance_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    assert "package-level" in text
    assert "item-level" in text


def test_artifact_reference_rules_documented():
    text = _normalized(CONTRACT_DOC)
    assert "Artifact References" in text
    for phrase in (
        "referenced by path",
        "referenced by that",
        "referenced by hash",
        "never a default",
    ):
        assert phrase in text, phrase


def test_artifact_reference_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    assert "referenced by path" in text
    assert "referenced by evidence id" in text or "evidence id" in text
    assert "referenced by hash" in text


def test_allowed_advisory_question_documented():
    text = _normalized(CONTRACT_DOC)
    assert "Allowed Advisory Questions" in text
    assert "Is the repository state internally consistent?" in text
    assert "only bounded repository consistency review is supported" in text.lower()


def test_allowed_advisory_question_documented_in_phase_doc():
    text = _normalized(PHASE_DOC)
    assert "Is the repository state internally consistent?" in text


def test_future_extensibility_documented():
    text = _normalized(CONTRACT_DOC)
    assert "Future Extensibility" in text
    for future_area in (
        "documentation consistency",
        "report consistency",
        "architecture consistency",
        "code review",
        "security review",
    ):
        assert future_area in text.lower(), future_area
    assert "Not implemented" in text or "not implemented" in text.lower()


def test_future_extensibility_documented_in_phase_doc():
    text = _normalized(PHASE_DOC).lower()
    for future_area in (
        "documentation", "report", "architecture consistency",
        "code review", "security review",
    ):
        assert future_area in text, future_area


def test_relationship_to_prior_phases_documented():
    text = _read(CONTRACT_DOC)
    for phase in ("115P", "115Q", "115R", "115U", "115V"):
        assert phase in text


def test_phase_report_covers_requested_sections():
    text = _read(PHASE_DOC)
    for section in (
        "Context Package Contract Summary",
        "Required Sections",
        "Trust Boundary Summary",
        "Prompt-Injection Handling",
        "Size / Redaction / Provenance Rules",
        "Artifact Reference Model",
        "Allowed Advisory Question",
    ):
        assert section in text, section


def test_no_implementation_claims():
    for doc in (CONTRACT_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "class AdvisoryContextPackage",
            "def build_advisory_context_package",
            "def assemble_context_package",
            "src/pcae/core/advisory_context_package.py",
            "src/pcae/core/context_package.py",
            "REST endpoint",
            "Telegram inbound implemented",
        ):
            assert forbidden not in text, f"{doc.name} appears to claim implementation: {forbidden}"


def test_no_new_implementation_module_added():
    """As of 115W (this phase), no implementation module existed yet.

    ``advisory_context_package.py`` was subsequently implemented by
    Phase 115X (this contract's own "Recommended Next Phase") -- this
    guard test is intentionally narrowed to the module names that
    remain unimplemented, since 115W's own "no implementation" claim
    is a property of 115W's diff, not a permanent constraint on later
    phases. See ``docs/PHASE_115X_ADVISORY_CONTEXT_PACKAGE_PROTOTYPE.md``.
    """
    forbidden_paths = (
        REPO_ROOT / "src" / "pcae" / "core" / "context_package.py",
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_context.py",
    )
    for path in forbidden_paths:
        assert not path.exists(), f"unexpected implementation module added: {path}"


def test_no_existing_advisory_module_modified_to_reference_context_package():
    for module_path in (
        REPO_ROOT / "src" / "pcae" / "core" / "advisory_repository_skills.py",
        REPO_ROOT / "src" / "pcae" / "core" / "current_acting_model_advisory_provider.py",
        REPO_ROOT / "src" / "pcae" / "core" / "decision_evaluation.py",
        REPO_ROOT / "src" / "pcae" / "core" / "repository_transition_validator.py",
    ):
        source = module_path.read_text(encoding="utf-8")
        for forbidden in ("AdvisoryContextPackage", "advisory_context_package", "context_package"):
            assert forbidden not in source, f"{module_path.name}: {forbidden}"


def test_no_deepseek_or_backend_integration_claimed():
    for doc in (CONTRACT_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "deepseek is integrated", "glm is integrated", "claude is integrated",
            "codex is integrated", "qwen is integrated", "openai is integrated",
            "now integrated",
        ):
            assert forbidden not in text.lower()


def test_execution_unavailable_confirmed():
    for doc in (CONTRACT_DOC, PHASE_DOC):
        assert "Execution capability remains unavailable" in _read(doc)


def test_no_go_list_present():
    text = _normalized(PHASE_DOC)
    assert "AdvisoryContextPackage` runtime implemented" in text
    assert "no Advisory Provider runtime modified" in text
    assert "No execution" in text
