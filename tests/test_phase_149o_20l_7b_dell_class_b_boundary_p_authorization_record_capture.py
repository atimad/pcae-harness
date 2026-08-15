"""Phase 149O.20L.7B -- Dell Class-B Boundary-P Authorization Record
Capture.

This phase presented the Phase 149O.20L.7A Dell-specific Boundary-P
proposition to the human governance authority and captured an explicit
election via `pcae decision-session`. The human elected AMEND, not
APPROVE -- per AMEND semantics, no CHGR was published (a deliberate,
disclosed judgment call; see the phase document Section 9). Boundary P
remains NOT AUTHORIZED. No Dell mutation occurred. The historical Mac
CHGR was neither modified nor reused.

These tests assert the phase document's documentary content and the
persisted decision-session/readiness-package artifacts. They do not
perform live Dell SSH and do not mutate the Dell.
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
    / "PHASE_149O_20L_7B_DELL_CLASS_B_BOUNDARY_P_AUTHORIZATION_RECORD_CAPTURE.md"
)

SESSION_ID = "CDS-cf123bbf-a5d7-4f0f-ac22-0baa257990af"
PACKAGE_ID = "prp-03cfe21aca284d009e71a2581c984dc0"

SESSION_PATH = REPO_ROOT / ".pcae" / "decision-sessions" / f"{SESSION_ID}.json"
READINESS_PACKAGE_PATH = (
    REPO_ROOT / ".pcae" / "decision-sessions" / "pending-packages" / f"{PACKAGE_ID}.json"
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def session_record() -> dict:
    payload = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
    return payload["session"]


class TestHistoricalMacChgrUntouchedAndNoNewChgr:
    def test_mac_chgr_file_still_present(self):
        assert MAC_CHGR_PATH.is_file()

    def test_mac_chgr_still_published_and_approved(self):
        record = json.loads(MAC_CHGR_PATH.read_text(encoding="utf-8"))
        assert record["lifecycle_state"] == "published"
        assert record["selected_option_id"] == "approve"

    def test_mac_chgr_decision_subject_still_names_the_mac(self):
        record = json.loads(MAC_CHGR_PATH.read_text(encoding="utf-8"))
        assert "Atilas-MacBook-Pro.local" in record["decision_subject"]
        assert "Dell" not in record["decision_subject"]

    def test_no_new_chgr_published_this_phase(self):
        chgr_files = sorted(p.name for p in RECORDS_DIR.glob("chgr-*.json"))
        assert chgr_files == ["chgr-d4343fa51b9743f3abaeb87a881a78b1.json"]

    def test_no_dell_named_chgr_exists(self):
        for path in RECORDS_DIR.glob("chgr-*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            subject = record.get("decision_subject", "")
            assert "hac-dell" not in subject
            assert "54ff22ce400b475aa0d55cb68f4a3334" not in subject


class TestDecisionSessionCaptured:
    def test_session_artifact_exists(self):
        assert SESSION_PATH.is_file()

    def test_session_confirmed(self, session_record):
        assert session_record["session_state"] == "Confirmed"

    def test_session_election_is_amend(self, session_record):
        assert session_record["human_selection_id"] == "amend"

    def test_session_options_presented_closed_set(self, session_record):
        assert set(session_record["options_presented"]) == {
            "approve",
            "decline",
            "amend",
        }

    def test_session_subject_names_the_dell_by_machine_id(self, session_record):
        assert "54ff22ce400b475aa0d55cb68f4a3334" in session_record["subject_ref"]
        assert "hac-dell" in session_record["subject_ref"]

    def test_session_subject_does_not_name_the_mac(self, session_record):
        assert "Atilas-MacBook-Pro" not in session_record["subject_ref"]

    def test_session_rationale_contains_first_person_election(self, session_record):
        rationale = session_record["human_rationale_text"]
        assert "I, as the human governance authority, elect to AMEND" in rationale

    def test_session_rationale_covers_all_four_amendment_requirements(
        self, session_record
    ):
        rationale = session_record["human_rationale_text"]
        assert "commit SHA" in rationale
        assert "rollback-verification commands" in rationale
        assert "launch-wrapper content" in rationale
        assert "/opt/pcae/projects/<repo-slug>/repo" in rationale

    def test_session_conditions_state_no_chgr_and_no_authorization(
        self, session_record
    ):
        conditions = session_record["human_conditions_text"]
        assert "not APPROVE" in conditions
        assert "Boundary P remains NOT AUTHORIZED" in conditions
        assert "No CHGR to be published" in conditions

    def test_readiness_package_persisted_pending(self):
        assert READINESS_PACKAGE_PATH.is_file()
        payload = json.loads(READINESS_PACKAGE_PATH.read_text(encoding="utf-8"))
        assert payload["disposition"] == "pending"


class TestPhaseDocumentContent:
    def test_no_unresolved_editorial_placeholder_tokens_remain(self, doc_text):
        # <origin-url>/<pinned-commit-sha> are legitimately quoted -- they
        # are the L.7A Action 6 gaps this phase's AMEND asks a future
        # phase to bind; they are not this phase's own unfilled content.
        for token in ("TBD", "TODO", "FIXME", "XXX"):
            assert token not in doc_text

    def test_verifier_locality_disclosure_present(self, doc_text):
        assert "cannot evaluate the Dell from the Mac" in doc_text

    def test_election_outcome_recorded_as_amend(self, doc_text):
        assert "Election outcome: AMEND." in doc_text

    def test_no_chgr_published_disclosed(self, doc_text):
        assert "No `chgr-*.json` file was created this phase" in doc_text

    def test_boundary_p_not_authorized_after_amend(self, doc_text):
        assert "Boundary P: NOT AUTHORIZED" in doc_text

    def test_boundary_c_and_a_not_authorized(self, doc_text):
        assert doc_text.count("Boundary C: NOT AUTHORIZED") >= 2
        assert doc_text.count("Boundary A: NOT AUTHORIZED") >= 2

    def test_recommended_next_phase_is_narrow_amendment_phase(self, doc_text):
        assert "149O.20L.7B.1" in doc_text
        assert "Materialization" in doc_text

    def test_no_provisioning_claimed(self, doc_text):
        assert "NO DELL MUTATION OCCURRED" in doc_text

    def test_session_and_package_ids_cited(self, doc_text):
        assert SESSION_ID in doc_text
        assert PACKAGE_ID in doc_text

    def test_materiality_assessment_present(self, doc_text):
        assert "Verdict: material." in doc_text


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
        assert "No `src/pcae/**`, `scripts/**`, or `docs/contracts/**` file" in doc_text
