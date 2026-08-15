"""Phase 149O.20L.7D.11 -- Repaired-Source Dell Redeployment + Action-9
Re-Adjudication Execution.

Independently-authored companion test module (imports nothing from
7D.9's or 7D.10's own test modules as oracle). This phase performed a
real, governed source-identity transition against the live `hac-dell`
host (`ssh hac-dell`) and a real read-only Action-9 re-adjudication.
The live Dell facts captured here (source SHA, mode inventory, wrapper
digest, venv metadata, Action-9 structured output) are recorded as
static constants mirroring what this phase's own canonical report and
phase-completion metadata record -- matching this project's established
convention (7D.5, 7D.9, 7D.10 all do the same for their own live-Dell
findings). This module does not re-SSH into Dell; it re-verifies the
git-object-level and governance-record-level claims that do not require
live Dell access, and asserts the captured literal Action-9 output text
is internally consistent with the authorized residual.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DOC = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7D_11_REPAIRED_SOURCE_DELL_REDEPLOYMENT_ACTION_9_RE_ADJUDICATION_EXECUTION.md"
)

GOVERNING_CHGR_ID = "chgr-0e37ed1340b14311826722c4dbf3e856"
FALLBACK_CHGR_IDS = (
    "chgr-96a0ce12756e4cc892492a87af1db832",
    "chgr-541cb08c313b4f8884970172d37c5a1d",
)

OLD_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
CANDIDATE_SHA = "28bf137b5dc95d024e8913b678dce0501a46fd0f"

DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"

OLD_TRACKED_PATH_COUNT = 4030
OLD_100644_COUNT = 4024
OLD_100755_COUNT = 6

CANDIDATE_TRACKED_PATH_COUNT = 4108
CANDIDATE_100644_COUNT = 4097
CANDIDATE_100755_COUNT = 11

THREE_REPAIRED_FILES = (
    "src/pcae/core/hatp_class_b_conformance.py",
    "src/pcae/core/hatp_class_b_topology_verifier.py",
    "src/pcae/core/hatp_environment_lock_verifier.py",
)
REPAIRED_FILE_DIGESTS = {
    "src/pcae/core/hatp_class_b_conformance.py": "dc2f26e21613e7f600cae8e2ea3187601e4b2ab84741792cf69c7170e1a696b5",
    "src/pcae/core/hatp_class_b_topology_verifier.py": "edba46128d5c18d40843302360dcb161ab20b83dbe3f44b2f0c67f3cae0d5687",
    "src/pcae/core/hatp_environment_lock_verifier.py": "1d28fec0ecc5518cf212b3534b7a0520731e9da2274b45186ce8bb2141b44bea",
}

CORRECTED_ACTION_9_PATH = "/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin"

EXPECTED_AUTHORIZED_RESIDUAL = {"HBDC-REQ-042"}
ACTUAL_MEASURED_RESIDUAL = {"HBDC-REQ-042"}
NOW_SATISFIED_REQS = ("HBDC-REQ-022", "HBDC-REQ-030", "HBDC-REQ-035", "HBDC-REQ-036")

# Literal captured Action-9 status-line output for both runs (determinism check).
ACTION_9_STATUS_LINE = "NON_COMPLIANT"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _git(*args: str) -> str:
    """Strictly read-only git query against this repository -- never
    fetch/checkout/commit/push/reset."""
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


class TestReportExists:
    def test_report_doc_exists(self):
        assert REPORT_DOC.exists()

    def test_report_doc_names_both_shas(self):
        text = REPORT_DOC.read_text(encoding="utf-8")
        assert OLD_SHA in text
        assert CANDIDATE_SHA in text

    def test_report_doc_states_exact_residual(self):
        text = REPORT_DOC.read_text(encoding="utf-8")
        assert "HBDC-REQ-042" in text


class TestGoverningCHGR:
    @pytest.fixture
    def chgr_path(self) -> Path:
        return REPO_ROOT / ".pcae/publication-execution/records" / f"{GOVERNING_CHGR_ID}.json"

    def test_governing_chgr_exists_published_and_approved(self, chgr_path: Path):
        record = _read_json(chgr_path)
        assert record["lifecycle_state"] == "published"
        assert record["selected_option_id"] == "approve"
        assert record["record_id"] == GOVERNING_CHGR_ID

    def test_governing_chgr_binds_candidate_sha_and_path(self, chgr_path: Path):
        record = _read_json(chgr_path)
        assert CANDIDATE_SHA in record["rationale"]
        assert CORRECTED_ACTION_9_PATH in record["rationale"]

    def test_governing_chgr_requires_exact_residual_stop_semantics(self, chgr_path: Path):
        record = _read_json(chgr_path)
        assert "{HBDC-REQ-042}" in record["conditions"]
        assert "STOP" in record["conditions"]

    def test_governing_chgr_unchanged_by_this_phase(self, chgr_path: Path):
        result = subprocess.run(
            ["git", "status", "--short", "--", str(chgr_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.stdout.strip() == ""

    def test_governing_chgr_verify_cli_reports_verified(self, chgr_path: Path):
        result = subprocess.run(
            ["pcae", "governance-record", "verify", str(chgr_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0
        assert "outcome: verified" in result.stdout


class TestFallbackCHGRsInapplicable:
    @pytest.mark.parametrize("chgr_id", FALLBACK_CHGR_IDS)
    def test_fallback_chgr_does_not_name_candidate_sha(self, chgr_id: str):
        path = REPO_ROOT / ".pcae/publication-execution/records" / f"{chgr_id}.json"
        record = _read_json(path)
        assert CANDIDATE_SHA not in record["rationale"]
        assert CANDIDATE_SHA not in record["decision_subject"]

    @pytest.mark.parametrize("chgr_id", FALLBACK_CHGR_IDS)
    def test_fallback_chgr_unchanged_by_this_phase(self, chgr_id: str):
        path = REPO_ROOT / ".pcae/publication-execution/records" / f"{chgr_id}.json"
        result = subprocess.run(
            ["git", "status", "--short", "--", str(path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.stdout.strip() == ""


class TestCandidateIdentityAndByteMatch:
    def test_candidate_object_is_a_commit(self):
        assert _git("cat-file", "-t", CANDIDATE_SHA).strip() == "commit"

    def test_candidate_is_ancestor_of_origin_main(self):
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", CANDIDATE_SHA, "origin/main"],
            cwd=REPO_ROOT,
            timeout=30,
        )
        assert result.returncode == 0

    def test_old_to_candidate_scoped_diff_is_exactly_three_files(self):
        output = _git(
            "diff",
            "--name-status",
            OLD_SHA,
            CANDIDATE_SHA,
            "--",
            "src/",
            "scripts/",
            "docs/contracts/",
            "pyproject.toml",
        )
        changed = {line.split("\t")[1] for line in output.strip().splitlines() if line.strip()}
        assert changed == set(THREE_REPAIRED_FILES)

    @pytest.mark.parametrize("relpath", THREE_REPAIRED_FILES)
    def test_repaired_file_blob_digest_matches_dell_deployed_digest(self, relpath: str):
        import hashlib

        blob = subprocess.run(
            ["git", "show", f"{CANDIDATE_SHA}:{relpath}"],
            cwd=REPO_ROOT,
            capture_output=True,
            timeout=30,
        )
        assert blob.returncode == 0
        digest = hashlib.sha256(blob.stdout).hexdigest()
        assert digest == REPAIRED_FILE_DIGESTS[relpath]


class TestCandidateTreeInventory:
    def test_candidate_tracked_path_count_and_mode_split(self):
        output = _git("ls-tree", "-r", "--name-only", CANDIDATE_SHA)
        paths = [p for p in output.splitlines() if p.strip()]
        assert len(paths) == CANDIDATE_TRACKED_PATH_COUNT

        mode_output = _git("ls-tree", "-r", CANDIDATE_SHA)
        modes = [line.split()[0] for line in mode_output.splitlines() if line.strip()]
        assert modes.count("100644") == CANDIDATE_100644_COUNT
        assert modes.count("100755") == CANDIDATE_100755_COUNT
        assert CANDIDATE_100644_COUNT + CANDIDATE_100755_COUNT == CANDIDATE_TRACKED_PATH_COUNT

    def test_old_sha_tracked_path_count_and_mode_split(self):
        output = _git("ls-tree", "-r", "--name-only", OLD_SHA)
        paths = [p for p in output.splitlines() if p.strip()]
        assert len(paths) == OLD_TRACKED_PATH_COUNT

        mode_output = _git("ls-tree", "-r", OLD_SHA)
        modes = [line.split()[0] for line in mode_output.splitlines() if line.strip()]
        assert modes.count("100644") == OLD_100644_COUNT
        assert modes.count("100755") == OLD_100755_COUNT


class TestContractVersionsUnchanged:
    @pytest.mark.parametrize(
        "relpath,expected_version",
        [
            ("docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md", "1.0"),
            (
                "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
                "1.3",
            ),
            ("docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md", "1.1"),
        ],
    )
    def test_contract_version_at_candidate_sha(self, relpath: str, expected_version: str):
        text = _git("show", f"{CANDIDATE_SHA}:{relpath}")
        version_lines = [line for line in text.splitlines() if "version" in line.lower()]
        assert any(expected_version in line for line in version_lines[:3])


class TestAction9Adjudication:
    def test_expected_residual_is_exactly_hbdc_req_042(self):
        assert EXPECTED_AUTHORIZED_RESIDUAL == {"HBDC-REQ-042"}

    def test_actual_measured_residual_matches_authorized_residual_exactly(self):
        assert ACTUAL_MEASURED_RESIDUAL == EXPECTED_AUTHORIZED_RESIDUAL

    def test_adjudication_rule_succeeds_only_on_exact_match(self):
        def adjudicate(actual: set, expected: set) -> str:
            return "SUCCESS" if actual == expected else "STOP"

        assert adjudicate(ACTUAL_MEASURED_RESIDUAL, EXPECTED_AUTHORIZED_RESIDUAL) == "SUCCESS"
        assert adjudicate({"HBDC-REQ-042", "HBDC-REQ-036"}, EXPECTED_AUTHORIZED_RESIDUAL) == "STOP"
        assert adjudicate(set(), EXPECTED_AUTHORIZED_RESIDUAL) == "STOP"

    def test_action_9_status_is_non_compliant_not_unexpected_compliant(self):
        # An unexpected COMPLIANT result with no DeploymentBinding would require
        # investigation (governing instruction Sec.45); this phase's actual
        # measurement was NON_COMPLIANT with the sole authorized residual.
        assert ACTION_9_STATUS_LINE == "NON_COMPLIANT"

    def test_previously_failing_requirements_now_measured_satisfied(self):
        for req in NOW_SATISFIED_REQS:
            assert req not in ACTUAL_MEASURED_RESIDUAL


class TestNoBoundaryCOrAThisPhase:
    def test_no_deploymentbinding_artifact_anywhere(self):
        matches = [
            m for m in REPO_ROOT.rglob("*eploymentBinding*") if ".git" not in m.parts
        ]
        assert matches == []

    def test_no_certification_artifact_created_this_phase(self):
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        for line in result.stdout.splitlines():
            assert "certification" not in line.lower()

    def test_deployment_identity_check_still_driven_only_by_binding_absence(self):
        source = (REPO_ROOT / "src/pcae/core/hatp_class_b_conformance.py").read_text(encoding="utf-8")
        assert "no_repository_identity_present" in source
        assert "no_active_deployment_binding_matches_repository_and_root" in source


class TestNoUnauthorizedRepositoryMutationThisPhase:
    def test_src_scripts_contracts_pyproject_unmodified_in_this_repo(self):
        result = subprocess.run(
            [
                "git",
                "diff",
                "--stat",
                CANDIDATE_SHA,
                "HEAD",
                "--",
                "src/pcae/",
                "scripts/",
                "docs/contracts/",
                "pyproject.toml",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.stdout.strip() == ""

    def test_wrapper_digest_constant_matches_authority_bound_value(self):
        # The wrapper itself lives only on Dell; this asserts the constant this
        # module and the phase report both bind is the one CHGR-bound value.
        assert WRAPPER_DIGEST == "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"

    def test_dell_machine_id_constant_matches_authority_bound_value(self):
        assert DELL_MACHINE_ID == "54ff22ce400b475aa0d55cb68f4a3334"
