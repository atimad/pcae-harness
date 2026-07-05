"""Phase 113X: Repository Transition Validator Integration Contract.

Documentation-completeness tests only. This phase freezes the future
integration contract and must not claim implementation.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_TRANSITION_VALIDATOR_INTEGRATION_CONTRACT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_113_REPOSITORY_TRANSITION_VALIDATOR_INTEGRATION_CONTRACT.md"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text)


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def phase_text() -> str:
    return PHASE_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def contract_text_flat(contract_text: str) -> str:
    return _normalize(contract_text)


class TestDocumentsExist:
    def test_contract_doc_exists(self):
        assert CONTRACT_DOC.is_file()

    def test_phase_doc_exists(self):
        assert PHASE_DOC.is_file()

    def test_contract_doc_not_empty(self, contract_text):
        assert len(contract_text) > 7000

    def test_phase_doc_not_empty(self, phase_text):
        assert len(phase_text) > 1200


class TestMandatoryEntryPoints:
    @pytest.mark.parametrize(
        "entry_point",
        [
            "pcae phase complete",
            "pcae task finish --commit",
            "Report generation",
            "Report promotion",
            "Phase metadata",
            "Notification dispatch",
            "pcae push check",
            "Future automation",
        ],
    )
    def test_entry_point_documented(self, contract_text, entry_point):
        assert entry_point in contract_text

    @pytest.mark.parametrize(
        "phrase",
        [
            "Before validator",
            "Validator",
            "After validator",
            "Allowed state changes",
            "Forbidden state changes",
        ],
    )
    def test_entry_point_contract_fields_documented(self, contract_text, phrase):
        assert phrase in contract_text


class TestCanonicalAuthority:
    def test_canonical_authority_frozen(self, contract_text):
        section = contract_text.split("## 3. Canonical Authority")[1].split("## 4.")[0]
        for phrase in [
            "No lifecycle command owns canonical state",
            "Commands request transitions",
            "The Repository Transition Validator certifies transitions",
            "Only Certified artifacts may become Canonical/latest",
            "one canonical promotion path",
        ]:
            assert phrase in section


class TestModelContainmentLayer:
    def test_mcl_documented(self, contract_text):
        section = contract_text.split("## 4. Model Containment Layer Contract")[1].split("## 5.")[0]
        for phrase in [
            "Models never modify canonical state",
            "Models propose transitions",
            "The validator certifies transitions",
            "Repository changes only after certification",
            "Agent identity never influences certification",
        ]:
            assert phrase in section

    @pytest.mark.parametrize("actor", ["Claude", "DeepSeek", "Codex", "GLM", "Qwen", "Gemini", "human"])
    def test_mcl_actor_agnostic(self, contract_text, actor):
        assert actor in contract_text


class TestPipeline:
    @pytest.mark.parametrize(
        "stage",
        [
            "Proposal",
            "Validation",
            "Certification",
            "Promotion",
            "Notification",
            "Completion",
            "Rollback eligibility",
        ],
    )
    def test_pipeline_stage_documented(self, contract_text, stage):
        section = contract_text.split("## 5. Transition Pipeline")[1].split("## 6.")[0]
        assert stage in section


class TestIntegrationInvariants:
    def test_invariants_table_present(self, contract_text):
        assert "## 6. Integration Invariants" in contract_text
        for heading in [
            "Required RepositoryState",
            "Required ProposedTransition",
            "Required ExpectedTargetState",
            "Required invariants",
            "Verdict mapping",
        ]:
            assert heading in contract_text

    @pytest.mark.parametrize(
        "command",
        [
            "`pcae phase complete`",
            "`pcae task finish --commit`",
            "report generation",
            "report promotion / `latest.*`",
            "phase metadata",
            "notification dispatch",
            "`pcae push check`",
            "future automation/REST/scheduler/runtime",
        ],
    )
    def test_lifecycle_command_in_invariants_table(self, contract_text, command):
        section = contract_text.split("## 6. Integration Invariants")[1].split("## 7.")[0]
        assert command in section


class TestNotificationDownstream:
    def test_notification_downstream_of_certification(self, contract_text):
        section = contract_text.split("## 8. Notification Integration")[1].split("## 9.")[0]
        for phrase in [
            "Notification is downstream of certification",
            "No certification means no notification",
            "Certification occurs once",
            "Final notification occurs once",
            "Certified/Canonical report",
        ]:
            assert phrase in section


class TestImplementationOrder:
    def test_future_enforcement_order_frozen(self, contract_text_flat):
        for item in [
            "113Y — Repository Transition Validator Integration: Phase Completion",
            "113Z — Repository Transition Validator Integration: Task Finish",
            "114A — Report Promotion / Quarantine Hardening",
            "114B — Notification Enforcement",
            "114C — Push/Check Integration",
            "114D — Cross-Agent Verification",
            "114E — Model Containment Drill",
        ]:
            assert item in contract_text_flat


class TestNoImplementationClaims:
    def test_no_implementation_claims(self, contract_text, phase_text):
        for phrase in [
            "no implementation",
            "No validator integration implemented",
            "No lifecycle command behavior changed",
            "Execution capability remains unavailable",
        ]:
            assert phrase in contract_text or phrase in phase_text

    def test_next_phase_documented(self, contract_text, phase_text):
        expected = "113Y — Repository Transition Validator Integration: Phase Completion"
        assert expected in contract_text
        assert expected in phase_text
