"""Phase 113T: Repository Transition Validator Contract Freeze.

Documentation-completeness tests only. This phase freezes a contract
in writing -- there is no ``validate_transition()`` implementation to
unit-test. These tests verify the contract document is fully and
consistently specified, and that the phase makes no implementation
claims it cannot back up.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_TRANSITION_VALIDATOR_CONTRACT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_113_REPOSITORY_TRANSITION_VALIDATOR_CONTRACT_FREEZE.md"
ARCHITECTURE_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_TRANSITION_VALIDATOR.md"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text)


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def phase_text() -> str:
    return PHASE_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def contract_text_flat(contract_text) -> str:
    return _normalize(contract_text)


@pytest.fixture(scope="module")
def phase_text_flat(phase_text) -> str:
    return _normalize(phase_text)


class TestDocumentsExist:
    def test_contract_document_exists(self):
        assert CONTRACT_DOC.is_file()

    def test_phase_document_exists(self):
        assert PHASE_DOC.is_file()

    def test_113s_architecture_document_still_exists(self):
        # 113T extends 113S; it must not have removed or replaced it.
        assert ARCHITECTURE_DOC.is_file()

    def test_contract_document_not_empty(self, contract_text):
        assert len(contract_text) > 3000

    def test_phase_document_not_empty(self, phase_text):
        assert len(phase_text) > 500


class TestValidatorContractFrozen:
    def test_status_frozen(self, contract_text):
        assert "Contract frozen" in contract_text

    def test_interface_section_present(self, contract_text):
        assert "Transition Validator Interface" in contract_text

    def test_signature_present(self, contract_text_flat):
        assert "validate_transition(" in contract_text_flat
        assert "current_state" in contract_text_flat
        assert "proposed_transition" in contract_text_flat
        assert "expected_target_state" in contract_text_flat
        assert "invariants" in contract_text_flat

    @pytest.mark.parametrize(
        "verdict",
        ["Accept", "Reject", "Quarantine", "Requires Human Review"],
    )
    def test_verdict_frozen(self, contract_text, verdict):
        assert verdict in contract_text

    def test_no_fifth_verdict_claimed(self, contract_text_flat):
        assert "no fifth value" in contract_text_flat


class TestRepositoryStateFrozen:
    def test_repository_state_section_present(self, contract_text):
        assert "## 3. Repository State" in contract_text

    def test_state_table_has_ownership_columns(self, contract_text):
        section = contract_text.split("## 3. Repository State")[1].split("## 4.")[0]
        for column in ["Owner", "Authoritative source", "Lifecycle", "Mutability"]:
            assert column in section

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
    def test_state_component_present(self, contract_text, component):
        section = contract_text.split("## 3. Repository State")[1].split("## 4.")[0]
        assert component in section


class TestTransitionInterfaceFrozen:
    def test_transition_contracts_section_present(self, contract_text):
        assert "## 4. Transition Contracts" in contract_text

    @pytest.mark.parametrize(
        "kind",
        [
            "start_task",
            "modify_files",
            "run_validation",
            "commit",
            "finish_task",
            "complete_phase",
            "report_generation",
            "report_promotion",
            "push",
            "notify",
            "status_update",
            "roadmap_update",
        ],
    )
    def test_transition_kind_frozen(self, contract_text, kind):
        assert kind in contract_text

    def test_no_command_may_bypass_validator(self, contract_text):
        assert "No command may bypass the validator" in contract_text


class TestCanonicalTransitionAuthorityFrozen:
    def test_first_class_requirement_language_present(self, contract_text_flat):
        assert "first-class" in contract_text_flat.lower()

    def test_never_two_independent_promotion_paths(self, contract_text_flat):
        assert "never exist two independent canonical report promotion paths" in contract_text_flat.lower()

    @pytest.mark.parametrize(
        "path",
        [
            "pcae phase complete",
            "pcae task finish --commit",
        ],
    )
    def test_existing_paths_named(self, contract_text, path):
        assert path in contract_text

    def test_future_paths_named(self, contract_text_flat):
        for term in ["future automation", "future scheduler", "future Telegram completion",
                     "future REST completion", "future agent completion", "future execution engine"]:
            assert term in contract_text_flat


class TestCanonicalPromotionContractFrozen:
    def test_promotion_section_present(self, contract_text):
        assert "## 5. Canonical Promotion Contract" in contract_text

    @pytest.mark.parametrize(
        "state",
        ["Draft", "Blocked", "Rejected", "Quarantined", "Certified", "Canonical"],
    )
    def test_promotion_state_frozen(self, contract_text, state):
        section = contract_text.split("## 5. Canonical Promotion Contract")[1].split("## 6.")[0]
        assert state in section

    def test_only_certified_may_become_canonical(self, contract_text):
        assert "Only Certified may become Canonical" in contract_text


class TestIdentityContractFrozen:
    def test_identity_contract_section_present(self, contract_text):
        assert "## 6. Identity Contract" in contract_text

    @pytest.mark.parametrize(
        "authority",
        [
            "Single identity source",
            "Single report promotion source",
            "Single metadata source",
            "Single canonical report source",
        ],
    )
    def test_singular_authority_frozen(self, contract_text, authority):
        assert authority in contract_text

    def test_no_alternate_derivation(self, contract_text):
        assert "No alternate identity derivation" in contract_text
        assert "No alternate promotion pipeline" in contract_text


class TestNotificationContractFrozen:
    def test_notification_section_present(self, contract_text):
        assert "## 7. Notification Contract" in contract_text

    @pytest.mark.parametrize(
        "term",
        [
            "Notification eligibility",
            "Notification idempotency",
            "Single external notification",
            "Notification certification",
        ],
    )
    def test_notification_term_frozen(self, contract_text, term):
        assert term in contract_text

    def test_no_intermediate_external_notification(self, contract_text):
        assert "No intermediate external notification" in contract_text


class TestInvariantContractFrozen:
    def test_invariant_section_present(self, contract_text):
        assert "## 8. Invariant Contract" in contract_text

    @pytest.mark.parametrize(
        "classification",
        ["Mandatory", "Derived", "Optional", "Future", "Blocking", "Warning", "Informational"],
    )
    def test_classification_defined(self, contract_text, classification):
        section = contract_text.split("## 8. Invariant Contract")[1].split("## 9.")[0]
        assert classification in section


class TestFailureContractFrozen:
    def test_failure_section_present(self, contract_text):
        assert "## 9. Failure Contract" in contract_text

    @pytest.mark.parametrize(
        "failure_mode",
        [
            "Identity mismatch",
            "Metadata mismatch",
            "Commit mismatch",
            "Report mismatch",
            "Architecture mismatch",
            "Notification mismatch",
            "Validator unavailable",
            "Missing evidence",
            "Partial validation",
        ],
    )
    def test_failure_mode_mapped(self, contract_text, failure_mode):
        section = contract_text.split("## 9. Failure Contract")[1].split("## 10.")[0]
        assert failure_mode in section

    def test_no_undefined_behavior(self, contract_text_flat):
        assert "Undefined behavior is not a permitted outcome" in contract_text_flat

    def test_every_failure_resolves_to_named_verdict(self, contract_text):
        section = contract_text.split("## 9. Failure Contract")[1].split("## 10.")[0]
        for verdict in ["Reject", "Quarantine", "Requires Human Review"]:
            assert verdict in section


class TestSemanticBoundaryFrozen:
    def test_semantic_boundary_section_present(self, contract_text):
        assert "## 10. Semantic Boundary" in contract_text

    def test_models_never_certify_themselves(self, contract_text):
        assert "Models never certify themselves" in contract_text


class TestFutureIntegrationDocumented:
    def test_future_integration_section_present(self, contract_text):
        assert "## 11. Future Integration" in contract_text

    @pytest.mark.parametrize(
        "integration_point",
        [
            "Task lifecycle",
            "Phase lifecycle",
            "Runtime Snapshot",
            "Runtime Inspect",
            "Advisory Runtime",
            "Permission Broker",
            "Execution runtime",
            "Approval runtime",
            "Future execution",
        ],
    )
    def test_integration_point_named(self, contract_text, integration_point):
        section = contract_text.split("## 11. Future Integration")[1].split("## 12.")[0]
        assert integration_point in section


class Test113SAsymmetryDocumentedAsContractRequirement:
    def test_asymmetry_section_present(self, contract_text):
        assert "## 1. The 113S Asymmetry" in contract_text

    def test_asymmetry_described(self, contract_text_flat):
        assert "pcae phase complete" in contract_text_flat
        assert "pcae task finish --commit" in contract_text_flat
        assert "phase-completion-metadata.json" in contract_text_flat

    def test_not_just_a_bug_framing(self, contract_text):
        assert "not \"just a bug\"" in contract_text or "not just a bug" in contract_text.lower()

    def test_frozen_requirement_stated(self, contract_text_flat):
        section = contract_text_flat.split("## 1. The 113S Asymmetry")[1].split("## 2.")[0]
        assert "There must never exist two independent canonical report promotion paths" in section

    def test_phase_doc_states_not_fixed_by_this_phase(self, phase_text_flat):
        assert "not fixed by this phase" in phase_text_flat.lower()


class TestNoImplementationClaims:
    def test_non_goals_section_present(self, contract_text):
        assert "## 12. Non-Goals" in contract_text

    def test_no_validate_transition_implementation_claimed(self, contract_text):
        section = contract_text.split("## 12. Non-Goals")[1]
        assert "No `validate_transition()` implementation" in section

    def test_no_behavior_change_claimed(self, contract_text_flat):
        assert "no change to `pcae phase complete`" in contract_text_flat.lower()

    def test_phase_doc_states_architecture_only(self, phase_text):
        assert "no implementation" in phase_text.lower()

    def test_no_source_files_touched_claim(self, phase_text_flat):
        assert "No source file under `src/pcae/` was touched" in phase_text_flat


class TestExecutionRemainsUnavailable:
    def test_contract_doc_confirms_execution_unavailable(self, contract_text_flat):
        assert "Execution capability remains unavailable" in contract_text_flat

    def test_phase_doc_confirms_execution_unavailable(self, phase_text_flat):
        assert "Execution capability remains unavailable" in phase_text_flat


class TestRecommendedNextPhase:
    def test_phase_doc_recommends_next_phase(self, phase_text):
        assert "113U" in phase_text
        assert "Repository Transition Validator Prototype" in phase_text
