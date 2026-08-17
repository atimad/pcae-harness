"""Phase 149O.20L.7N.4 -- Dell Current-Source Redeployment Execution.

Independently-authored companion test module (imports nothing from
7N/7N.1/7N.2/7N.3's own test modules as oracle). Covers static checks
against already-persisted repository/CHGR state and the exact
command/content text this phase's report claims to have executed on the
live Dell host. No live SSH or Dell mutation is performed in CI -- all
Dell evidence is captured in the canonical phase report
(docs/PHASE_149O_20L_7N_4_DELL_CURRENT_SOURCE_REDEPLOYMENT_EXECUTION.md)
and is not re-verified live here.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parents[1]

OLD_SHA = "28bf137b5dc95d024e8913b678dce0501a46fd0f"
CANDIDATE_SHA = "b0840e96a7ffb12308e95828aa5927c3e7c770c0"

GOVERNING_CHGR_ID = "chgr-71bd24f9d3d742d6baac772e480fc876"
HISTORICAL_CHGR_IDS = (
    "chgr-d4343fa51b9743f3abaeb87a881a78b1",
    "chgr-96a0ce12756e4cc892492a87af1db832",
    "chgr-541cb08c313b4f8884970172d37c5a1d",
    "chgr-0e37ed1340b14311826722c4dbf3e856",
)

DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
DELL_HOSTNAME = "atila-Latitude-E5470"
WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
HMIC_IMPLEMENTATION_DIGEST = (
    "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"
)

EXPECTED_HBDC_RESIDUAL = {"HBDC-REQ-042"}

MUTATION_COMMANDS = [
    f"sudo git -C /opt/pcae/runtime/src fetch origin {CANDIDATE_SHA}",
    f"sudo git -C /opt/pcae/runtime/src cat-file -t {CANDIDATE_SHA}",
    f"sudo git -C /opt/pcae/runtime/src checkout --detach {CANDIDATE_SHA}",
    "sudo chown -R root:pcae /opt/pcae/runtime/src",
    "sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \\;",
    "sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \\;",
    "sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \\;",
]

ROLLBACK_COMMANDS = [
    f"sudo git -C /opt/pcae/runtime/src checkout --detach {OLD_SHA}",
    "sudo chown -R root:pcae /opt/pcae/runtime/src",
    "sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \\;",
    "sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \\;",
    "sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \\;",
]

REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7N_4_DELL_CURRENT_SOURCE_REDEPLOYMENT_EXECUTION.md"
)

PROPOSITION_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7N_DELL_CURRENT_SOURCE_REDEPLOYMENT_PROPOSITION_AUTHORITY_PREPARATION.md"
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestMutationCommandIdentity:
    def test_mutation_sequence_has_seven_steps(self):
        assert len(MUTATION_COMMANDS) == 7

    def test_fetch_uses_full_candidate_sha_no_branch(self):
        fetch_cmd = MUTATION_COMMANDS[0]
        assert CANDIDATE_SHA in fetch_cmd
        assert "origin main" not in fetch_cmd
        assert "pull" not in fetch_cmd

    def test_checkout_is_detached_full_sha_no_branch(self):
        checkout_cmd = MUTATION_COMMANDS[2]
        assert "--detach" in checkout_cmd
        assert CANDIDATE_SHA in checkout_cmd

    def test_ownership_scoped_exactly_to_runtime_src(self):
        chown_cmd = MUTATION_COMMANDS[3]
        assert chown_cmd == "sudo chown -R root:pcae /opt/pcae/runtime/src"

    def test_mode_normalization_uses_two_branch_exec_bit_split(self):
        joined = "\n".join(MUTATION_COMMANDS)
        assert "-perm -u+x -exec chmod 0750" in joined
        assert "! -perm -u+x -exec chmod 0640" in joined
        # No blanket unconditional chmod that would erase the executable split.
        assert "-type f -exec chmod 0640" not in joined

    def test_no_command_touches_venv_or_wrapper(self):
        joined = "\n".join(MUTATION_COMMANDS)
        assert "/opt/pcae/runtime/venv" not in joined
        assert "/opt/pcae/runtime/bin" not in joined

    def test_no_pip_or_reinstall_command_present(self):
        joined = "\n".join(MUTATION_COMMANDS)
        assert "pip" not in joined


class TestRollbackCommandIdentity:
    def test_rollback_targets_old_sha_exactly(self):
        assert ROLLBACK_COMMANDS[0] == (
            f"sudo git -C /opt/pcae/runtime/src checkout --detach {OLD_SHA}"
        )

    def test_rollback_is_network_independent(self):
        joined = "\n".join(ROLLBACK_COMMANDS)
        assert "fetch" not in joined
        assert "pull" not in joined
        assert "clone" not in joined

    def test_rollback_reuses_identical_mode_mapping_as_forward(self):
        assert ROLLBACK_COMMANDS[1:] == MUTATION_COMMANDS[3:]


class TestGoverningCHGR:
    @pytest.fixture
    def chgr_path(self) -> Path:
        return REPO_ROOT / ".pcae/publication-execution/records" / f"{GOVERNING_CHGR_ID}.json"

    def test_governing_chgr_artifact_exists(self, chgr_path: Path):
        assert chgr_path.exists()

    def test_governing_chgr_is_published_and_approved(self, chgr_path: Path):
        record = _read_json(chgr_path)
        assert record["lifecycle_state"] == "published"
        assert record["selected_option_id"] == "approve"
        assert record["record_id"] == GOVERNING_CHGR_ID

    def test_governing_chgr_names_correct_target_and_shas(self, chgr_path: Path):
        record = _read_json(chgr_path)
        subject = record["decision_subject"]
        assert OLD_SHA in subject
        assert CANDIDATE_SHA in subject

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


class TestHistoricalCHGRsUnchangedAndUnused:
    def test_all_four_historical_chgrs_still_published_unrevoked(self):
        for chgr_id in HISTORICAL_CHGR_IDS:
            path = REPO_ROOT / ".pcae/publication-execution/records" / f"{chgr_id}.json"
            assert path.exists()
            record = _read_json(path)
            assert record["lifecycle_state"] == "published"

    def test_no_historical_chgr_byte_changed_by_this_phase(self):
        for chgr_id in HISTORICAL_CHGR_IDS:
            path = REPO_ROOT / ".pcae/publication-execution/records" / f"{chgr_id}.json"
            result = subprocess.run(
                ["git", "status", "--short", "--", str(path)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.stdout.strip() == ""


class TestReportContent:
    def test_report_exists(self):
        assert REPORT_PATH.exists()

    def test_report_states_correct_shas(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert OLD_SHA in text
        assert CANDIDATE_SHA in text

    def test_report_states_correct_dell_identity(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert DELL_MACHINE_ID in text
        assert DELL_HOSTNAME in text

    def test_report_states_correct_implementation_digest(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert HMIC_IMPLEMENTATION_DIGEST in text

    def test_report_states_correct_wrapper_digest(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert WRAPPER_DIGEST in text

    def test_report_states_expected_verdict(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "REDEPLOYMENT EXECUTED SUCCESSFULLY" in text
        assert "INDEPENDENT VERIFICATION PENDING" in text

    def test_report_does_not_claim_hmic_certified_or_valid(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "HMIC VALID" not in text
        assert "HMIC CERTIFIED" not in text

    def test_report_does_not_claim_repositoryidentity_or_binding_created(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "RepositoryIdentity | absent" in text
        assert "DeploymentBinding | absent" in text

    def test_report_recommends_7n5_as_next_phase(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "149O.20L.7N.5" in text

    def test_report_references_canonical_proposition_as_command_source(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "PHASE_149O_20L_7N_DELL_CURRENT_SOURCE_REDEPLOYMENT_PROPOSITION" in text


class TestHBDCResidual:
    def test_expected_residual_is_exactly_hbdc_req_042(self):
        assert EXPECTED_HBDC_RESIDUAL == {"HBDC-REQ-042"}

    def test_report_names_exact_residual_reason(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "no_repository_identity_present" in text


class TestPropositionIsCanonicalSource:
    def test_proposition_artifact_exists(self):
        assert PROPOSITION_PATH.exists()

    def test_proposition_contains_the_exact_mutation_commands(self):
        text = PROPOSITION_PATH.read_text(encoding="utf-8")
        for cmd in MUTATION_COMMANDS:
            assert cmd in text, f"command not found verbatim in proposition: {cmd!r}"

    def test_proposition_contains_the_exact_rollback_commands(self):
        text = PROPOSITION_PATH.read_text(encoding="utf-8")
        for cmd in ROLLBACK_COMMANDS:
            assert cmd in text, f"rollback command not found verbatim in proposition: {cmd!r}"
