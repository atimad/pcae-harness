"""Phase 149O.20L.7O.2A.4 -- RepositoryIdentity Write-Path Remediation
Execution.

This phase's live mutation (`chmod 1770 /opt/pcae/runtime/src/.pcae` on
`hac-dell`) is not reproducible in CI -- no route to `hac-dell` exists
here. These tests instead assert the local invariants that must hold
around a chmod-only execution phase: the governing CHGR still verifies
unchanged, no new CHGR was published, no RepositoryIdentity or
DeploymentBinding artifact exists locally, no production source path
was touched, and this phase's own doc records the exact values this
phase's live findings must match (self-consistency, not re-execution).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RECORDS_DIR = _REPO_ROOT / ".pcae" / "publication-execution" / "records"
_DOC_PATH = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2A_4_REPOSITORYIDENTITY_WRITE_PATH_REMEDIATION_EXECUTION.md"
)

_CHGR_ID = "chgr-86aeb5cfa7c44020ad002bc9f80c5856"
_CHGR_PATH = _RECORDS_DIR / f"{_CHGR_ID}.json"
_CONF_ID = "chgrconf-698eefcec95841ef8350e94fa7a59ea8"
_PROV_ID = "chgrprov-5a681f551c3646af81d7ecdb1a3ccff1"
_INTG_ID = "chgrintg-2fa93bd13e7e440f8c98a283cff99872"

_ALL_CHGR_IDS = {
    "chgr-0e37ed1340b14311826722c4dbf3e856",
    "chgr-96a0ce12756e4cc892492a87af1db832",
    "chgr-d4343fa51b9743f3abaeb87a881a78b1",
    "chgr-541cb08c313b4f8884970172d37c5a1d",
    "chgr-71bd24f9d3d742d6baac772e480fc876",
    _CHGR_ID,
}

_TARGET_PATH = "/opt/pcae/runtime/src/.pcae"
_ELECTION_TIME_SHA = "b0840e96a7ffb12308e95828aa5927c3e7c770c0"
_EXPECTED_HMIC_DIGEST = (
    "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"
)
_EXPECTED_WRAPPER_DIGEST = (
    "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _doc_text() -> str:
    return _DOC_PATH.read_text()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Governing CHGR is unchanged, still verifies, and remains the sole
#    record naming this exact target path.
# ═══════════════════════════════════════════════════════════════════════════


class TestGoverningChgrUnchanged:
    def test_chgr_still_names_exact_target_and_mutation(self) -> None:
        chgr = _load(_CHGR_PATH)
        subject = chgr["decision_subject"]
        assert _TARGET_PATH in subject
        assert "0750" in subject
        assert "1770" in subject
        assert "chmod" in subject.lower()

    def test_chgr_excludes_repositoryidentity_and_deploymentbinding(self) -> None:
        chgr = _load(_CHGR_PATH)
        subject = chgr["decision_subject"]
        assert "RepositoryIdentity" in subject
        assert "Deploym" in subject  # "Deployment" wraps across the field

    def test_chgr_lifecycle_state_still_published_not_revoked(self) -> None:
        chgr = _load(_CHGR_PATH)
        assert chgr["lifecycle_state"] == "published"

    def test_decision_maker_identity_unchanged(self) -> None:
        chgr = _load(_CHGR_PATH)
        assert chgr["decision_maker_identity_evidence"]["identifier"] == "Atila Madai"

    def test_only_this_chgr_names_the_target_path(self) -> None:
        matches = [
            chgr_id
            for chgr_id in _ALL_CHGR_IDS
            if _TARGET_PATH in _load(_RECORDS_DIR / f"{chgr_id}.json").get(
                "decision_subject", ""
            )
        ]
        assert matches == [_CHGR_ID]

    def test_no_new_chgr_published_by_this_phase(self) -> None:
        chgr_ids = {p.stem for p in _RECORDS_DIR.glob("chgr-*.json")}
        assert chgr_ids == _ALL_CHGR_IDS

    def test_integrity_chain_still_binds(self) -> None:
        chgr = _load(_CHGR_PATH)
        integrity = _load(_RECORDS_DIR / f"{_INTG_ID}.json")
        conf = _load(_RECORDS_DIR / f"{_CONF_ID}.json")
        prov = _load(_RECORDS_DIR / f"{_PROV_ID}.json")
        assert integrity["payload_digest"] == chgr["record_digest"]
        assert chgr["confirmation_evidence_ref"]["record_digest"] == conf["record_digest"]
        assert chgr["provenance_ref"]["record_digest"] == prov["record_digest"]


# ═══════════════════════════════════════════════════════════════════════════
# 2. Zero local mutation artifacts: this is a real-host execution phase,
#    but it must leave zero RepositoryIdentity/DeploymentBinding trace
#    anywhere in the local tree (git-tracked or not).
# ═══════════════════════════════════════════════════════════════════════════


class TestZeroLocalMutationArtifacts:
    def test_no_repository_identity_artifact_exists_locally(self) -> None:
        matches = [
            m for m in _REPO_ROOT.rglob("*repository-identity*.json") if ".git" not in m.parts
        ]
        assert matches == []

    def test_no_deploymentbinding_artifact_exists_locally(self) -> None:
        matches = [
            m for m in _REPO_ROOT.rglob("*deploymentbinding*.json") if ".git" not in m.parts
        ]
        assert matches == []


# ═══════════════════════════════════════════════════════════════════════════
# 3. No production source changed since the CHGR's election-time SHA.
# ═══════════════════════════════════════════════════════════════════════════


class TestSourceUnchangedSinceElection:
    def test_election_time_source_sha_is_ancestor_of_head(self) -> None:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", _ELECTION_TIME_SHA, "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
        )
        assert result.returncode == 0

    def test_no_src_contracts_or_scripts_changes_since_election(self) -> None:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                _ELECTION_TIME_SHA,
                "HEAD",
                "--",
                "src/",
                "docs/contracts/",
                "scripts/",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════════
# 4. Doc self-consistency: the exact live values this phase's execution
#    log claims must be present, verbatim, in the phase doc.
# ═══════════════════════════════════════════════════════════════════════════


class TestDocRecordsExactExpectedValues:
    def test_doc_exists(self) -> None:
        assert _DOC_PATH.is_file()

    def test_doc_records_exact_mutation_command(self) -> None:
        text = _doc_text()
        assert "chmod 1770 /opt/pcae/runtime/src/.pcae" in text
        assert "chmod -R" not in text
        assert re.search(r"\bchown\b", text.split("## 3.")[0]) is None

    def test_doc_records_exit_status_zero(self) -> None:
        assert "Exit status: `0`" in _doc_text()

    def test_doc_records_pre_and_post_mode(self) -> None:
        text = _doc_text()
        assert "0750" in text
        assert "mode=1770" in text or "1770`" in text

    def test_doc_records_unchanged_source_sha(self) -> None:
        assert _ELECTION_TIME_SHA in _doc_text()

    def test_doc_records_unchanged_hmic_digest(self) -> None:
        assert _EXPECTED_HMIC_DIGEST in _doc_text()

    def test_doc_records_unchanged_wrapper_digest(self) -> None:
        assert _EXPECTED_WRAPPER_DIGEST in _doc_text()

    def test_doc_records_hbdc_non_compliant_sole_residual(self) -> None:
        text = _doc_text()
        assert "NON_COMPLIANT" in text
        assert "HBDC-REQ-042" in text
        assert "HBDC-REQ-036" in text

    def test_doc_records_repositoryidentity_and_deploymentbinding_absent(self) -> None:
        text = _doc_text()
        assert "RepositoryIdentity" in text
        assert "absent" in text.lower()

    def test_doc_records_no_rollback_triggered(self) -> None:
        assert "**Not triggered.**" in _doc_text()

    def test_doc_records_architecture_history_json_carve_out(self) -> None:
        assert "architecture-history.json" in _doc_text()

    def test_doc_records_sticky_bit_reference_verified_qualification(self) -> None:
        text = _doc_text()
        assert "REFERENCE-VERIFIED FROM PRIMARY LINUX/POSIX SOURCES" in text
        assert "not** empirically tested" in text or "not empirically tested" in text

    def test_doc_final_verdict_is_pending_not_verified(self) -> None:
        text = _doc_text()
        assert "INDEPENDENT\nVERIFICATION PENDING" in text
        verdict_section = text.split("## 18.")[1].split("## 19.")[0]
        assert "not* claimed as independently verified" in verdict_section

    def test_doc_recommends_exact_next_phase(self) -> None:
        assert "149O.20L.7O.2A.5" in _doc_text()

    def test_doc_does_not_claim_repositoryidentity_creation(self) -> None:
        text = _doc_text()
        assert "does **not** create RepositoryIdentity" in text

    def test_doc_does_not_begin_strategic_breakpoint_work(self) -> None:
        text = _doc_text()
        assert "not begun this phase" in text
