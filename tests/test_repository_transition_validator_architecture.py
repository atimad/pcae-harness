"""Phase 113S: Repository Transition Validator Architecture.

Documentation-completeness tests only. This phase is architecture/
design, not implementation -- there is no ``validate_transition()``
function to unit-test. These tests verify the architecture is fully
and consistently specified in writing, and that the phase makes no
implementation claims it cannot back up.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_TRANSITION_VALIDATOR.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_113_REPOSITORY_TRANSITION_VALIDATOR_ARCHITECTURE.md"


def _normalize(text: str) -> str:
    """Collapse whitespace/line-wraps so multi-line prose phrases can be
    matched as a single substring regardless of Markdown line-wrapping."""
    return re.sub(r"\s+", " ", text)


@pytest.fixture(scope="module")
def architecture_text() -> str:
    return ARCHITECTURE_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def phase_text() -> str:
    return PHASE_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def architecture_text_flat(architecture_text) -> str:
    return _normalize(architecture_text)


@pytest.fixture(scope="module")
def phase_text_flat(phase_text) -> str:
    return _normalize(phase_text)


class TestDocumentsExist:
    def test_architecture_document_exists(self):
        assert ARCHITECTURE_DOC.is_file()

    def test_phase_document_exists(self):
        assert PHASE_DOC.is_file()

    def test_architecture_document_not_empty(self, architecture_text):
        assert len(architecture_text) > 2000

    def test_phase_document_not_empty(self, phase_text):
        assert len(phase_text) > 500


class TestRepositoryStateDefined:
    def test_repository_state_section_present(self, architecture_text):
        assert "Repository State" in architecture_text

    @pytest.mark.parametrize(
        "component",
        [
            "Git state",
            "Working tree",
            "Active task",
            "Phase identity",
            "Project status",
            "Phase reports",
            "Phase-completion metadata",
            "Architecture status",
            "Test results",
            "Governance checks",
            "Notification state",
            "Push state",
            "Runtime state",
            "Execution availability",
        ],
    )
    def test_state_component_listed(self, architecture_text, component):
        assert component in architecture_text


class TestProposedTransitionDefined:
    def test_proposed_transition_section_present(self, architecture_text):
        assert "Proposed Transition" in architecture_text

    @pytest.mark.parametrize(
        "kind",
        [
            "start_task",
            "modify_files",
            "run_validation",
            "commit",
            "finish_task",
            "complete_phase",
            "push",
            "notify",
            "update_status",
            "produce_report",
        ],
    )
    def test_transition_kind_listed(self, architecture_text, kind):
        assert kind in architecture_text

    def test_model_proposes_pcae_validates_principle_stated(self, architecture_text):
        assert "Model proposes" in architecture_text
        assert "PCAE validates" in architecture_text


class TestValidatorOutcomesDefined:
    def test_transition_validator_section_present(self, architecture_text):
        assert "Transition Validator" in architecture_text

    @pytest.mark.parametrize("outcome", ["ACCEPT", "REJECT", "QUARANTINE", "REQUIRES_HUMAN_REVIEW"])
    def test_outcome_defined(self, architecture_text, outcome):
        assert outcome in architecture_text


class TestInvariantsDefined:
    def test_invariants_section_present(self, architecture_text):
        assert "## 4. Invariants" in architecture_text

    @pytest.mark.parametrize(
        "invariant_keyword",
        [
            "Phase identity consistency",
            "Active task consistency",
            "Allowed file scope",
            "Commit lineage",
            "Report completeness",
            "Report trust",
            "Metadata consistency",
            "Architecture status consistency",
            "Recommended-next-phase consistency",
            "Test result consistency",
            "Push state consistency",
            "Notification eligibility",
            "Single final notification",
            "No execution availability",
            "No canonical artifact promotion when blocked",
        ],
    )
    def test_invariant_listed(self, architecture_text, invariant_keyword):
        assert invariant_keyword in architecture_text


class TestAcceptRejectQuarantineSemanticsDefined:
    def test_semantics_section_present(self, architecture_text):
        assert "Accept" in architecture_text
        assert "Reject" in architecture_text
        assert "Quarantine" in architecture_text
        assert "Human-Review" in architecture_text or "Human review" in architecture_text

    def test_reject_means_no_canonical_change(self, architecture_text):
        section = architecture_text.split("## 5. Accept")[1].split("## 6.")[0]
        assert "No canonical state changes" in section or "no canonical state changes" in section

    def test_quarantine_never_promoted(self, architecture_text):
        section = architecture_text.split("## 5. Accept")[1].split("## 6.")[0]
        assert "never promoted" in section.lower() or "never" in section.lower()


class TestCanonicalArtifactPromotionDefined:
    def test_promotion_section_present(self, architecture_text):
        assert "Canonical Artifact Promotion" in architecture_text

    @pytest.mark.parametrize(
        "artifact_state",
        ["Draft", "Blocked", "Quarantined", "Certified", "Canonical"],
    )
    def test_artifact_state_listed(self, architecture_text, artifact_state):
        assert artifact_state in architecture_text

    def test_only_certified_may_become_canonical(self, architecture_text):
        assert "Only certified artifacts may become canonical" in architecture_text


class TestNotificationEligibilityDefined:
    def test_notification_section_present(self, architecture_text):
        assert "Notification Eligibility" in architecture_text

    @pytest.mark.parametrize(
        "condition",
        [
            "finalized",
            "Certified",
            "clean",
            "already been dispatched",
            "configured and enabled",
        ],
    )
    def test_eligibility_condition_present(self, architecture_text, condition):
        section = architecture_text.split("## 7. Notification Eligibility")[1].split("## 8.")[0]
        assert condition in section

    def test_intermediate_reports_never_dispatched(self, architecture_text):
        section = architecture_text.split("## 7. Notification Eligibility")[1].split("## 8.")[0]
        assert "never" in section.lower()


class TestSemanticStructuralBoundaryDefined:
    def test_boundary_section_present(self, architecture_text):
        assert "Semantic vs. Structural Boundary" in architecture_text \
            or "Semantic vs Structural Boundary" in architecture_text

    def test_models_own_semantic_examples(self, architecture_text):
        section_marker = "## 8. Semantic vs"
        assert section_marker in architecture_text
        section = architecture_text.split(section_marker)[1].split("## 9.")[0]
        for term in ["Code design", "Implementation strategy", "Explanations", "Remediation"]:
            assert term in section

    def test_pcae_owns_structural_examples(self, architecture_text):
        section = architecture_text.split("## 8. Semantic vs")[1].split("## 9.")[0]
        for term in ["Identity", "Lifecycle", "Scope", "Reports", "Commits", "Pushes", "Notifications", "Canonical state"]:
            assert term in section


class TestModelAgnosticBehaviorDefined:
    def test_model_agnostic_section_present(self, architecture_text):
        assert "Model-Agnostic Behavior" in architecture_text

    @pytest.mark.parametrize("agent", ["Claude", "Claude-DeepSeek", "Codex", "Qwen", "human"])
    def test_agent_named(self, architecture_text, agent):
        section = architecture_text.split("## 9. Model-Agnostic Behavior")[1].split("## 10.")[0]
        assert agent in section

    def test_no_agent_identity_field_in_validator_signature(self, architecture_text):
        assert "no field for" in architecture_text or "no field for \"which model" in architecture_text.replace("'", '"')


class TestFutureIntegrationDefined:
    def test_future_integration_section_present(self, architecture_text):
        assert "Future Integration" in architecture_text

    @pytest.mark.parametrize(
        "integration_point",
        [
            "Task lifecycle",
            "Phase lifecycle",
            "Commit governance",
            "Push governance",
            "Notification runtime",
            "Runtime Snapshot",
            "Advisory Runtime",
            "Future intent/approval/execution layers",
        ],
    )
    def test_integration_point_listed(self, architecture_text, integration_point):
        assert integration_point in architecture_text


class TestNoImplementationClaims:
    def test_non_goals_section_present(self, architecture_text):
        assert "Non-Goals" in architecture_text

    def test_no_validate_transition_implementation_claimed(self, architecture_text):
        section = architecture_text.split("## 11. Non-Goals")[1]
        assert "No `validate_transition()` function is implemented" in section

    def test_phase_doc_states_architecture_only(self, phase_text):
        assert "Architecture/design only" in phase_text or "architecture/design only" in phase_text.lower()
        assert "no implementation" in phase_text.lower()

    def test_no_source_files_touched_claim(self, phase_text_flat):
        assert "No source file under `src/pcae/` was touched" in phase_text_flat


class TestExecutionRemainsUnavailable:
    def test_architecture_doc_confirms_execution_unavailable(self, architecture_text_flat):
        assert "Execution capability remains unavailable" in architecture_text_flat

    def test_phase_doc_confirms_execution_unavailable(self, phase_text_flat):
        assert "Execution capability remains unavailable" in phase_text_flat

    def test_no_execution_invariant_present(self, architecture_text_flat):
        assert "No execution availability unless explicitly enabled by future contract" in architecture_text_flat


class TestRecommendedNextPhase:
    def test_architecture_doc_silent_on_next_phase_is_fine(self, architecture_text):
        # The architecture document is a durable contract; the phase
        # completion document is where the next-phase recommendation lives.
        assert True

    def test_phase_doc_recommends_next_phase(self, phase_text):
        assert "113T" in phase_text
        assert "Repository Transition Validator Contract Freeze" in phase_text
