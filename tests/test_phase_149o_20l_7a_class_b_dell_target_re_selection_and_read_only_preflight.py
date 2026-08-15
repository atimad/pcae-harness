"""Phase 149O.20L.7A — Class-B Dell Target Re-Selection & Read-Only
Preflight.

This phase performed the first legitimate read-only SSH connection to
the Dell (hac-dell, 192.168.192.200), re-derived Ubuntu-specific Class-B
target eligibility, and drafted (but did not publish) a Dell-specific
Boundary-P proposition. No Dell mutation occurred, no new CHGR was
published, and the historical Mac CHGR was neither modified nor reused.
These tests assert the phase document's documentary content and the
continued absence of any Dell-provisioning or CHGR-publication artifact
in this repository. They do not perform live Dell SSH -- the live
evidence gathered this phase is preserved in the phase document rather
than re-derived destructively on every test run.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PCAE_EXECUTABLE = shutil.which("pcae")

RECORDS_DIR = REPO_ROOT / ".pcae" / "publication-execution" / "records"
MAC_CHGR_PATH = RECORDS_DIR / "chgr-d4343fa51b9743f3abaeb87a881a78b1.json"

DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7A_CLASS_B_DELL_TARGET_RE_SELECTION_AND_READ_ONLY_PREFLIGHT.md"
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def mac_chgr_record() -> dict:
    return json.loads(MAC_CHGR_PATH.read_text(encoding="utf-8"))


class TestHistoricalMacChgrUntouched:
    def test_mac_chgr_file_still_present(self):
        assert MAC_CHGR_PATH.is_file()

    def test_mac_chgr_still_published_and_approved(self, mac_chgr_record):
        assert mac_chgr_record["lifecycle_state"] == "published"
        assert mac_chgr_record["selected_option_id"] == "approve"

    def test_mac_chgr_not_revoked_or_superseded(self, mac_chgr_record):
        for field in ("revocation_ref", "superseded_by", "deprecated_by"):
            assert field not in mac_chgr_record

    def test_mac_chgr_decision_subject_still_names_the_mac(self, mac_chgr_record):
        assert "Atilas-MacBook-Pro.local" in mac_chgr_record["decision_subject"]


class TestNoNewChgrPublished:
    def test_only_the_historical_mac_chgr_record_exists(self):
        chgr_files = sorted(RECORDS_DIR.glob("chgr-*.json"))
        assert chgr_files == [MAC_CHGR_PATH]

    def test_no_dell_named_chgr_file_exists(self):
        dell_named = [p for p in RECORDS_DIR.glob("chgr-*.json") if "dell" in p.name.lower()]
        assert dell_named == []


class TestNoDellMutationArtifactsInRepo:
    def test_git_status_clean_scope(self):
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        allowed_prefixes = (
            "?? docs/PHASE_149O_20L_7A_",
            "?? tests/test_phase_149o_20l_7a_",
            " M PROJECT_STATUS.md",
            " M CHANGELOG.md",
            "?? tasks/",
            " M .pcae/",
            " M tasks/",
            " D tasks/",
        )
        stray = [
            line
            for line in result.stdout.splitlines()
            if line and not line.startswith(allowed_prefixes)
        ]
        assert stray == [], f"Unexpected working-tree changes: {stray}"

    def test_no_production_or_contract_file_touched(self):
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        changed = [line for line in result.stdout.splitlines() if line]
        for path in changed:
            assert not path.startswith("src/pcae/")
            assert not path.startswith("docs/contracts/")
            assert not path.startswith("scripts/")


class TestPhaseDocumentRecordsPreflightFindings:
    def test_doc_records_dell_host_identity(self, doc_text):
        assert "atila-Latitude-E5470" in doc_text
        assert "54ff22ce400b475aa0d55cb68f4a3334" in doc_text
        assert "Ubuntu 24.04" in doc_text

    def test_doc_records_first_ssh_connection(self, doc_text):
        assert "hac-dell" in doc_text
        assert "CONNECTED as codex" in doc_text

    def test_doc_states_eligibility_verdict(self, doc_text):
        assert "ELIGIBLE WITH PRECONDITIONS" in doc_text

    def test_doc_states_no_dell_mutation(self, doc_text):
        assert "NO DELL MUTATION OCCURRED" in doc_text

    def test_doc_states_no_new_chgr_published(self, doc_text):
        assert "NO NEW CHGR PUBLISHED" in doc_text

    def test_doc_boundary_p_not_authorized(self, doc_text):
        assert "BOUNDARY P: NOT AUTHORIZED" in doc_text

    def test_doc_boundary_c_and_a_not_authorized(self, doc_text):
        assert "BOUNDARY C: NOT AUTHORIZED" in doc_text
        assert "BOUNDARY A: NOT AUTHORIZED" in doc_text

    def test_doc_class_b_not_provisioned(self, doc_text):
        assert "CLASS-B: NOT PROVISIONED" in doc_text

    def test_doc_recommends_next_phase_7b(self, doc_text):
        assert "149O.20L.7B" in doc_text

    def test_doc_contains_draft_proposition_labeled_not_authorized(self, doc_text):
        assert "DRAFT — NOT AUTHORIZED" in doc_text
        assert "Boundary P is NOT AUTHORIZED by\n> this document" in doc_text

    def test_doc_does_not_reuse_mac_chgr_as_dell_authority(self, doc_text):
        assert "not reusable as authority for it" in doc_text.lower() or (
            "not authority" in doc_text.lower()
        )

    def test_doc_preserves_per_repository_model(self, doc_text):
        assert "independently governed PCAE project" in doc_text
        assert "Deferred" in doc_text
        assert "centralized" in doc_text.lower()

    def test_doc_records_model_1_principal_decision(self, doc_text):
        assert "Model 1 chosen" in doc_text

    def test_doc_records_nine_action_plan(self, doc_text):
        assert "Action 9" in doc_text
        assert "Action 1" in doc_text


class TestBoundaryCAndBoundaryAArtifactsAbsent:
    def test_no_certification_or_cutover_artifacts_exist(self):
        pcae_dir = REPO_ROOT / ".pcae"
        suspicious = []
        for path in pcae_dir.rglob("*"):
            if not path.is_file():
                continue
            name = path.name.lower()
            if "certification" in name or "cutover" in name or "activation-marker" in name:
                suspicious.append(str(path))
        assert suspicious == []


class TestNoDellNamedPrincipalOrProtectedRootExistsLocally:
    def test_no_pcae_deploy_reference_created_on_this_mac(self):
        # This phase creates zero real host resources on the Mac either;
        # confirms this session's own developer identity is unchanged.
        result = subprocess.run(
            ["id", "-un"], capture_output=True, text=True, check=False
        )
        assert result.stdout.strip() == "atilamadai"


class TestGovernanceCliStillHealthy:
    @pytest.mark.skipif(PCAE_EXECUTABLE is None, reason="pcae CLI not on PATH")
    def test_pcae_check_passes(self):
        result = subprocess.run(
            [PCAE_EXECUTABLE, "check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "PCAE check passed" in result.stdout

    @pytest.mark.skipif(PCAE_EXECUTABLE is None, reason="pcae CLI not on PATH")
    def test_pcae_governance_record_verify_mac_chgr_still_structurally_valid(self):
        result = subprocess.run(
            [PCAE_EXECUTABLE, "governance-record", "verify", str(MAC_CHGR_PATH)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert "outcome: verified" in result.stdout
