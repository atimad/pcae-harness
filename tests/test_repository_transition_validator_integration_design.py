"""Phase 113W: Repository Transition Validator Integration Design.

Documentation-completeness tests only. This phase designs future lifecycle
integration and must not claim implementation.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DESIGN_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_TRANSITION_VALIDATOR_INTEGRATION.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_113_REPOSITORY_TRANSITION_VALIDATOR_INTEGRATION_DESIGN.md"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text)


@pytest.fixture(scope="module")
def design_text() -> str:
    return DESIGN_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def phase_text() -> str:
    return PHASE_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def design_text_flat(design_text: str) -> str:
    return _normalize(design_text)


@pytest.fixture(scope="module")
def phase_text_flat(phase_text: str) -> str:
    return _normalize(phase_text)


class TestDocumentsExist:
    def test_integration_design_doc_exists(self):
        assert DESIGN_DOC.is_file()

    def test_phase_doc_exists(self):
        assert PHASE_DOC.is_file()

    def test_design_doc_not_empty(self, design_text):
        assert len(design_text) > 6000

    def test_phase_doc_not_empty(self, phase_text):
        assert len(phase_text) > 1200


class TestContainmentTarget:
    def test_containment_target_documented(self, design_text_flat):
        for phrase in [
            "model, human operator, scheduler, or future automation proposes",
            "PCAE constructs the authoritative `RepositoryState`",
            "Valid transitions proceed",
            "No invalid repository state becomes canonical",
        ]:
            assert phrase in design_text_flat

    def test_deepseek_named_as_containment_subject(self, design_text):
        assert "DeepSeek" in design_text


class TestIntegrationPoints:
    @pytest.mark.parametrize(
        "point",
        [
            "pcae phase complete",
            "pcae task finish --commit",
            "report generation",
            "report promotion",
            "phase-completion metadata",
            "pcae push check",
            "pcae notify send-report",
            "phase-finalization skill",
            "future automation",
            "future agent-driven workflows",
        ],
    )
    def test_integration_point_documented(self, design_text, point):
        assert point in design_text


class TestTransitionFlow:
    @pytest.mark.parametrize(
        "heading",
        [
            "pcae phase complete",
            "pcae task finish --commit",
            "Report Generation",
            "Report Promotion",
            "Phase-Completion Metadata",
            "pcae push check",
            "pcae notify send-report",
            "Phase-Finalization Skill",
            "Future Automation",
        ],
    )
    def test_transition_flow_section_exists(self, design_text, heading):
        assert heading in design_text

    @pytest.mark.parametrize(
        "phrase",
        [
            "Current behavior",
            "Proposed validated behavior",
            "Required inputs",
            "Expected target",
            "Invariants",
            "Accepted outcome",
            "Reject outcome",
            "Quarantine outcome",
            "Human-review outcome",
        ],
    )
    def test_transition_flow_required_fields_present(self, design_text, phrase):
        assert phrase in design_text

    def test_repository_state_and_transition_types_named(self, design_text):
        assert "RepositoryState" in design_text
        assert "ProposedTransition" in design_text
        assert "ExpectedTargetState" in design_text


class TestImplementationOrder:
    def test_implementation_order_documented(self, design_text_flat):
        expected = [
            "1. `pcae phase complete`",
            "2. report promotion/latest artifacts",
            "3. `pcae task finish --commit`",
            "4. notification dispatch",
            "5. `pcae push check`",
            "6. cross-agent verification",
        ]
        for item in expected:
            assert item in design_text_flat

    def test_order_supported_by_evidence(self, design_text):
        assert "Evidence:" in design_text
        assert "113S and" in design_text and "113T identified" in design_text


class TestCanonicalPromotionPath:
    def test_canonical_promotion_path_documented(self, design_text):
        section = design_text.split("## 6. Single Canonical Promotion Path")[1].split("## 7.")[0]
        for artifact in [
            ".pcae/phase-reports/latest.json",
            ".pcae/phase-reports/latest.md",
            ".pcae/phase-completion-metadata.json",
            "notification event eligibility",
        ]:
            assert artifact in section

    def test_no_alternate_promotion_path(self, design_text):
        assert "No command may write `latest.*`" in design_text
        assert "separate path" in design_text


class TestFailureBehavior:
    @pytest.mark.parametrize(
        "verdict",
        ["Reject", "Quarantine", "Requires human review", "Accept"],
    )
    def test_failure_behavior_documented(self, design_text, verdict):
        assert verdict in design_text

    def test_exit_code_behavior_documented(self, design_text):
        assert "Exit-code behavior must be stable" in design_text
        assert "return failure" in design_text


class TestDeepSeekContainmentScenarios:
    @pytest.mark.parametrize(
        "scenario",
        [
            "stale commits in a report",
            "wrong phase ID",
            "missing `recommended_next_phase`",
            "malformed or unstructured test results",
            "duplicate Telegram reports",
            "silent missing Telegram report",
            "stale phase-completion metadata",
            "report from the wrong phase",
            "Architecture Status overclaim",
            "push with an untrusted report",
        ],
    )
    def test_scenario_documented(self, design_text, scenario):
        assert scenario in design_text


class TestNoImplementationClaims:
    def test_design_only_stated(self, design_text, phase_text):
        assert "Design only" in design_text
        assert "No lifecycle integration is implemented" in design_text
        assert "No validator integration implemented" in phase_text
        assert "No lifecycle command behavior changed" in phase_text

    def test_execution_unavailable_documented(self, design_text, phase_text):
        assert "Execution capability remains unavailable" in design_text
        assert "Execution capability remains unavailable" in phase_text

    def test_next_phase_documented(self, design_text_flat, phase_text):
        expected = "113X — Repository Transition Validator Integration Contract"
        assert expected in design_text_flat
        assert expected in phase_text
