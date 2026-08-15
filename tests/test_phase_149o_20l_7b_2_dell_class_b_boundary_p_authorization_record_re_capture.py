"""Phase 149O.20L.7B.2 -- Dell Class-B Boundary-P Authorization Record
Re-Capture.

This phase presented the fully materialized, amended Dell Boundary-P
proposition from Phase 149O.20L.7B.1 to the human governance authority
and captured a fresh, explicit election via `pcae decision-session`.
The human elected APPROVE. A new Dell-specific CHGR
(`chgr-96a0ce12756e4cc892492a87af1db832`) was published, inspected, and
verified. No provisioning occurred. The prior AMEND session and the
historical Mac CHGR were neither modified nor reused.

These tests assert the phase document's documentary content and the
persisted decision-session/readiness-package/CHGR artifacts. They do
not perform live Dell SSH and do not mutate the Dell.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

RECORDS_DIR = REPO_ROOT / ".pcae" / "publication-execution" / "records"
MAC_CHGR_PATH = RECORDS_DIR / "chgr-d4343fa51b9743f3abaeb87a881a78b1.json"

DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7B_2_DELL_CLASS_B_BOUNDARY_P_AUTHORIZATION_RECORD_RE_CAPTURE.md"
)

PRIOR_AMEND_SESSION_ID = "CDS-cf123bbf-a5d7-4f0f-ac22-0baa257990af"
SESSION_ID = "CDS-adb67041-3a30-4b4e-a188-e6284e7743be"
PACKAGE_ID = "prp-66418889a03e42379213a2f50340d362"
NEW_CHGR_ID = "chgr-96a0ce12756e4cc892492a87af1db832"

PINNED_SOURCE_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"

PRIOR_AMEND_SESSION_PATH = (
    REPO_ROOT / ".pcae" / "decision-sessions" / f"{PRIOR_AMEND_SESSION_ID}.json"
)
SESSION_PATH = REPO_ROOT / ".pcae" / "decision-sessions" / f"{SESSION_ID}.json"
READINESS_PACKAGE_PATH = (
    REPO_ROOT
    / ".pcae"
    / "decision-sessions"
    / "pending-packages"
    / "consumed"
    / f"{PACKAGE_ID}.json"
)
NEW_CHGR_PATH = RECORDS_DIR / f"{NEW_CHGR_ID}.json"


@pytest.fixture(scope="module")
def doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def session_record() -> dict:
    payload = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
    return payload["session"]


@pytest.fixture(scope="module")
def prior_amend_session_record() -> dict:
    payload = json.loads(PRIOR_AMEND_SESSION_PATH.read_text(encoding="utf-8"))
    return payload["session"]


@pytest.fixture(scope="module")
def readiness_package() -> dict:
    return json.loads(READINESS_PACKAGE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def new_chgr_record() -> dict:
    return json.loads(NEW_CHGR_PATH.read_text(encoding="utf-8"))


class TestPriorAmendSessionUnchanged:
    def test_prior_amend_session_still_confirmed_amend(self, prior_amend_session_record):
        assert prior_amend_session_record["session_state"] == "Confirmed"
        assert prior_amend_session_record["human_selection_id"] == "amend"

    def test_prior_amend_session_id_distinct_from_new_session(self, prior_amend_session_record):
        assert prior_amend_session_record["session_id"] == PRIOR_AMEND_SESSION_ID
        assert PRIOR_AMEND_SESSION_ID != SESSION_ID


class TestHistoricalMacChgrUnchanged:
    def test_mac_chgr_file_still_present(self):
        assert MAC_CHGR_PATH.is_file()

    def test_mac_chgr_still_published_and_approved(self):
        record = json.loads(MAC_CHGR_PATH.read_text(encoding="utf-8"))
        assert record["lifecycle_state"] == "published"
        assert record["selected_option_id"] == "approve"

    def test_mac_chgr_decision_subject_still_names_the_mac_not_dell(self):
        record = json.loads(MAC_CHGR_PATH.read_text(encoding="utf-8"))
        assert "Atilas-MacBook-Pro.local" in record["decision_subject"]
        assert "hac-dell" not in record["decision_subject"]

    def test_mac_chgr_id_distinct_from_new_dell_chgr(self):
        assert "chgr-d4343fa51b9743f3abaeb87a881a78b1" != NEW_CHGR_ID


class TestNewDecisionSessionCaptured:
    def test_session_artifact_exists(self):
        assert SESSION_PATH.is_file()

    def test_session_confirmed(self, session_record):
        assert session_record["session_state"] == "Confirmed"

    def test_session_election_is_approve(self, session_record):
        assert session_record["human_selection_id"] == "approve"

    def test_session_options_presented_closed_set(self, session_record):
        assert set(session_record["options_presented"]) == {
            "approve",
            "decline",
            "amend",
        }

    def test_session_subject_names_the_dell_by_machine_id(self, session_record):
        assert DELL_MACHINE_ID in session_record["subject_ref"]
        assert "hac-dell" in session_record["subject_ref"]

    def test_session_subject_cites_7b1_proposition(self, session_record):
        assert "149O.20L.7B.1" in session_record["subject_ref"]

    def test_session_subject_does_not_name_the_mac(self, session_record):
        assert "Atilas-MacBook-Pro" not in session_record["subject_ref"]

    def test_session_rationale_contains_first_person_approve_election(self, session_record):
        rationale = session_record["human_rationale_text"]
        assert "I, as the human governance authority, elect to APPROVE" in rationale

    def test_session_rationale_cites_pinned_source_sha(self, session_record):
        assert PINNED_SOURCE_SHA in session_record["human_rationale_text"]

    def test_session_rationale_discloses_action_9_finding(self, session_record):
        rationale = session_record["human_rationale_text"]
        assert "HBDC-REQ-042" in rationale
        assert "DeploymentBinding" in rationale

    def test_session_conditions_exclude_deploymentbinding_and_boundary_c_a(self, session_record):
        conditions = session_record["human_conditions_text"]
        assert "does not authorize DeploymentBinding creation" in conditions
        assert "Boundary C certification" in conditions
        assert "Boundary A activation" in conditions

    def test_session_conditions_exclude_centralized_governance(self, session_record):
        assert "centralized multi-repository governance" in session_record["human_conditions_text"]


class TestReadinessAndPublication:
    def test_readiness_package_persisted_and_consumed(self, readiness_package):
        assert readiness_package["disposition"] == "consumed"
        assert readiness_package["session_id"] == SESSION_ID

    def test_readiness_package_evidence_refs_bind_source_and_wrapper(self, readiness_package):
        evidence_refs = readiness_package["package"]["evidence_refs"]
        assert PINNED_SOURCE_SHA in evidence_refs
        assert WRAPPER_DIGEST in evidence_refs

    def test_readiness_package_record_id_matches_published_chgr(self, readiness_package):
        assert readiness_package["record_id"] == NEW_CHGR_ID

    def test_readiness_package_selected_option_is_approve(self, readiness_package):
        assert readiness_package["package"]["selected_option_id"] == "approve"


class TestNewChgrPublishedInspectedVerified:
    def test_new_chgr_file_exists(self):
        assert NEW_CHGR_PATH.is_file()

    def test_new_chgr_published_and_approved(self, new_chgr_record):
        assert new_chgr_record["lifecycle_state"] == "published"
        assert new_chgr_record["selected_option_id"] == "approve"

    def test_new_chgr_names_the_dell_by_machine_id(self, new_chgr_record):
        assert DELL_MACHINE_ID in new_chgr_record["decision_subject"]

    def test_new_chgr_rationale_preserves_action_9_disclosure(self, new_chgr_record):
        rationale = new_chgr_record["rationale"]
        assert "HBDC-REQ-042" in rationale
        assert "DeploymentBinding" in rationale

    def test_new_chgr_conditions_exclude_deploymentbinding(self, new_chgr_record):
        assert "does not authorize DeploymentBinding creation" in new_chgr_record["conditions"]

    def test_new_chgr_has_related_artifact_refs(self, new_chgr_record):
        assert "confirmation_evidence_ref" in new_chgr_record
        assert "provenance_ref" in new_chgr_record
        assert "integrity_ref" in new_chgr_record

    def test_related_artifact_files_exist(self, new_chgr_record):
        for ref_field in ("confirmation_evidence_ref", "provenance_ref", "integrity_ref"):
            record_id = new_chgr_record[ref_field]["record_id"]
            assert (RECORDS_DIR / f"{record_id}.json").is_file()


class TestNoDeploymentBindingOrHigherBoundaryAuthorized:
    def test_no_deploymentbinding_language_authorizes_creation(self, session_record):
        rationale = session_record["human_rationale_text"]
        conditions = session_record["human_conditions_text"]
        assert "does not authorize DeploymentBinding creation" in conditions
        assert "create a DeploymentBinding" not in rationale
        assert "create a DeploymentBinding" not in conditions

    def test_no_boundary_c_or_a_authorization_language(self, doc_text):
        assert "Boundary C: NOT AUTHORIZED" in doc_text
        assert "Boundary A: NOT AUTHORIZED" in doc_text
        assert "Boundary C: AUTHORIZED" not in doc_text
        assert "Boundary A: AUTHORIZED" not in doc_text


class TestPhaseDocumentContent:
    def test_no_unresolved_editorial_placeholder_tokens_remain(self, doc_text):
        for token in ("TBD", "TODO", "FIXME", "XXX"):
            assert token not in doc_text

    def test_election_outcome_recorded_as_approve(self, doc_text):
        assert "Election outcome: APPROVE." in doc_text

    def test_new_chgr_id_cited(self, doc_text):
        assert NEW_CHGR_ID in doc_text

    def test_session_and_package_ids_cited(self, doc_text):
        assert SESSION_ID in doc_text
        assert PACKAGE_ID in doc_text

    def test_prior_amend_session_id_cited_as_unchanged(self, doc_text):
        assert PRIOR_AMEND_SESSION_ID in doc_text

    def test_boundary_p_authorized_by_chgr_language(self, doc_text):
        assert "Boundary P: AUTHORIZED BY PUBLISHED DELL-SPECIFIC CHGR" in doc_text

    def test_boundary_p_no_execution_yet(self, doc_text):
        assert "INDEPENDENT AUTHORIZATION VERIFICATION PENDING" in doc_text

    def test_class_b_not_provisioned(self, doc_text):
        assert "CLASS-B: NOT PROVISIONED" in doc_text

    def test_recommended_next_phase_is_independent_verification(self, doc_text):
        assert "149O.20L.7C" in doc_text
        assert "Independent Verification" in doc_text

    def test_operator_errors_disclosed_not_hidden(self, doc_text):
        assert "fabricated" in doc_text
        assert "Cancelled" in doc_text or "cancelled" in doc_text.lower()

    def test_no_provisioning_claimed(self, doc_text):
        assert "NO DELL MUTATION OCCURRED" in doc_text

    def test_no_deploymentbinding_created_claimed(self, doc_text):
        assert "NO DEPLOYMENTBINDING AUTHORIZED OR CREATED" in doc_text


class TestNoDellMutation:
    def test_no_provisioning_language_in_doc(self, doc_text):
        forbidden = [
            "useradd pcae",
            "groupadd pcae",
            "sudo mkdir -p /opt/pcae",
        ]
        for phrase in forbidden:
            assert phrase not in doc_text, f"unexpected literal provisioning command: {phrase}"

    def test_no_production_or_contract_files_referenced_as_changed(self, doc_text):
        assert (
            "Zero `src/pcae/**`, `docs/contracts/**`, or `scripts/**` paths touched."
            in doc_text
        )
