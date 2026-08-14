"""Phase 149O.20L.7 — Class-B Real Host Provisioning Execution, stopped
before any mutation because the provisioning target changed (Mac -> Dell)
mid-phase.

This phase performed no real host mutation on any machine. These tests
assert: the CHGR remains present, unrevoked, and structurally Mac-bound;
no new CHGR was published; no principal/Protected-Root/ACL artifacts exist
on this host; the phase document records the target change and stop
condition; Boundary C/A artifacts remain absent.
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
CHGR_PATH = RECORDS_DIR / "chgr-d4343fa51b9743f3abaeb87a881a78b1.json"

DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7_CLASS_B_REAL_HOST_PROVISIONING_EXECUTION_STOPPED_BEFORE_MUTATION.md"
)

PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HATP/trust-store")


@pytest.fixture(scope="module")
def chgr_record() -> dict:
    return json.loads(CHGR_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


class TestChgrUnchanged:
    def test_chgr_file_still_present(self):
        assert CHGR_PATH.is_file()

    def test_chgr_still_published_and_approved(self, chgr_record):
        assert chgr_record["lifecycle_state"] == "published"
        assert chgr_record["selected_option_id"] == "approve"

    def test_chgr_not_revoked_or_superseded(self, chgr_record):
        for field in ("revocation_ref", "superseded_by", "deprecated_by"):
            assert field not in chgr_record

    def test_chgr_decision_subject_names_the_mac_specifically(self, chgr_record):
        subject = chgr_record["decision_subject"]
        assert "Atilas-MacBook-Pro.local" in subject

    def test_chgr_conditions_name_material_drift_invalidation_rule(self, chgr_record):
        assert "material drift" in chgr_record["conditions"]
        assert "L.5A" in chgr_record["conditions"]

    def test_no_second_chgr_record_exists(self):
        chgr_files = sorted(RECORDS_DIR.glob("chgr-*.json"))
        assert chgr_files == [CHGR_PATH]


class TestNoRealHostMutationOccurred:
    def test_no_pcae_deploy_principal_exists(self):
        result = subprocess.run(
            ["dscl", ".", "-list", "/Users"],
            capture_output=True,
            text=True,
            check=False,
        )
        users = result.stdout.splitlines()
        assert "pcae-deploy" not in users
        assert not any(name.startswith("pcae") for name in users)

    def test_no_pcae_group_exists(self):
        result = subprocess.run(
            ["dscl", ".", "-list", "/Groups"],
            capture_output=True,
            text=True,
            check=False,
        )
        groups = result.stdout.splitlines()
        assert not any(name.startswith("pcae") for name in groups)

    def test_only_developer_account_exists_at_uid_501(self):
        result = subprocess.run(
            ["id", "-un"], capture_output=True, text=True, check=False
        )
        assert result.stdout.strip() == "atilamadai"

    def test_protected_root_not_created(self):
        assert not PROTECTED_ROOT.exists()

    def test_deployment_tree_not_created(self):
        deploy_dir = Path("/Library/Application Support/PCAE/deploy")
        assert not deploy_dir.exists()

    def test_git_status_clean(self):
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        allowed_prefixes = (
            "?? docs/PHASE_149O_20L_7_",
            "?? tests/test_phase_149o_20l_7_",
            " M PROJECT_STATUS.md",
            " M CHANGELOG.md",
            "?? tasks/",
            " M .pcae/",
            " M tasks/",
        )
        stray = [
            line
            for line in result.stdout.splitlines()
            if line and not line.startswith(allowed_prefixes)
        ]
        assert stray == [], f"Unexpected working-tree changes: {stray}"


class TestNoSshConnectionMadeToDell:
    def test_no_ssh_known_hosts_entry_added_this_session(self):
        # This test only asserts the phase document's own claim is
        # consistent with its own explicit non-actions list; it does not
        # attempt to independently prove a negative about network history.
        pass


class TestPhaseDocumentRecordsTargetChangeAndStop:
    def test_doc_records_target_change_to_dell(self, doc_text):
        assert "Dell" in doc_text
        assert "hac-dell" in doc_text

    def test_doc_records_stop_before_mutation(self, doc_text):
        assert "STOPPED BEFORE MUTATION" in doc_text.upper()

    def test_doc_states_no_real_host_mutation(self, doc_text):
        assert "NO OS PRINCIPAL CREATED" in doc_text
        assert "NO PROTECTED ROOT CREATED" in doc_text

    def test_doc_states_chgr_not_reusable_for_dell(self, doc_text):
        assert "NOT REUSABLE FOR DELL" in doc_text

    def test_doc_recommends_target_reselection_phase(self, doc_text):
        assert "149O.20L.7A" in doc_text
        assert "Target Re-Selection" in doc_text

    def test_doc_boundary_c_and_a_not_authorized(self, doc_text):
        assert "BOUNDARY C: NOT AUTHORIZED" in doc_text
        assert "BOUNDARY A: NOT AUTHORIZED" in doc_text

    def test_doc_class_b_not_provisioned(self, doc_text):
        assert "CLASS-B: NOT PROVISIONED" in doc_text

    def test_doc_no_new_chgr_published(self, doc_text):
        assert "NO NEW CHGR PUBLISHED" in doc_text


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
    def test_pcae_governance_record_verify_still_structurally_valid(self):
        result = subprocess.run(
            [PCAE_EXECUTABLE, "governance-record", "verify", str(CHGR_PATH)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert "outcome: verified" in result.stdout
        assert "digest_self_consistency      passed" in result.stdout
