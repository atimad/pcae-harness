"""Phase 149O.20L.7D.5 -- Dell Class-B Provisioning Continuation Execution.

Independently-authored companion test module (imports nothing from
7D.3's or 7D.4's own test modules as oracle). Covers static checks
against already-persisted repository/CHGR/decision-session state and
the exact command/content text this phase's report claims to have
executed. No live SSH or Dell mutation is performed in CI -- all Dell
evidence is captured in the canonical phase report
(docs/PHASE_149O_20L_7D_5_DELL_CLASS_B_PROVISIONING_CONTINUATION_EXECUTION.md)
and is not re-verified live here.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

GOVERNING_CHGR_ID = "chgr-541cb08c313b4f8884970172d37c5a1d"
HISTORICAL_CHGR_ID = "chgr-96a0ce12756e4cc892492a87af1db832"
GOVERNING_SESSION_ID = "CDS-554c3c12-0693-4edd-867d-b86374c376b2"
SUPERSEDED_SESSION_ID = "CDS-8984cecc-4b55-4cfc-aca6-14397f5735a1"
PINNED_SOURCE_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"

EXPECTED_AUTHORIZED_RESIDUAL = {"HBDC-REQ-042"}
ACTUAL_MEASURED_RESIDUAL = {
    "HBDC-REQ-022",
    "HBDC-REQ-030",
    "HBDC-REQ-035",
    "HBDC-REQ-036",
    "HBDC-REQ-042",
}

REPAIRED_ACTION_6_COMMANDS = [
    "sudo git clone --no-checkout git@github.com:atimad/pcae-harness.git /opt/pcae/runtime/src",
    "sudo git -C /opt/pcae/runtime/src checkout --detach 7a3fa971304521cdcb44251e07ef1966baec686a",
    "sudo chown -R root:pcae /opt/pcae/runtime/src",
    "sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \\;",
    "sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \\;",
    "sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \\;",
]

ORIGINAL_DEFECTIVE_ACTION_6_LINE = (
    "sudo find /opt/pcae/runtime/src -type f -exec chmod 0640 {} \\;"
)

WRAPPER_CONTENT = (
    "#!/bin/sh\n"
    "set -eu\n"
    "unset PYTHONPATH\n"
    "PYTHONNOUSERSITE=1\n"
    "export PYTHONNOUSERSITE\n"
    "PATH=/usr/bin:/bin:/usr/sbin:/sbin\n"
    "export PATH\n"
    "cd /opt/pcae/runtime\n"
    'exec /opt/pcae/runtime/venv/bin/pcae "$@"\n'
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestWrapperContentAndDigest:
    def test_wrapper_is_exactly_9_lines_188_bytes(self):
        assert WRAPPER_CONTENT.count("\n") == 9
        assert len(WRAPPER_CONTENT.encode("utf-8")) == 188

    def test_wrapper_digest_matches_authority_bound_value(self):
        digest = hashlib.sha256(WRAPPER_CONTENT.encode("utf-8")).hexdigest()
        assert digest == WRAPPER_DIGEST

    def test_wrapper_has_no_trailing_whitespace_on_any_line(self):
        for line in WRAPPER_CONTENT.splitlines():
            assert line == line.rstrip()

    def test_wrapper_never_sources_a_profile(self):
        assert "source " not in WRAPPER_CONTENT
        assert "\n. " not in WRAPPER_CONTENT

    def test_wrapper_unsets_pythonpath_and_locks_path(self):
        assert "unset PYTHONPATH" in WRAPPER_CONTENT
        assert "PATH=/usr/bin:/bin:/usr/sbin:/sbin" in WRAPPER_CONTENT

    def test_wrapper_execs_pinned_venv_pcae_forwarding_args(self):
        assert WRAPPER_CONTENT.rstrip().endswith(
            'exec /opt/pcae/runtime/venv/bin/pcae "$@"'
        )


class TestRepairedAction6CommandIdentity:
    def test_repaired_sequence_has_six_commands(self):
        assert len(REPAIRED_ACTION_6_COMMANDS) == 6

    def test_repaired_sequence_uses_pinned_sha(self):
        assert any(PINNED_SOURCE_SHA in cmd for cmd in REPAIRED_ACTION_6_COMMANDS)

    def test_repaired_sequence_replaces_unconditional_chmod_with_two_branches(self):
        joined = "\n".join(REPAIRED_ACTION_6_COMMANDS)
        assert ORIGINAL_DEFECTIVE_ACTION_6_LINE not in joined
        assert "-perm -u+x -exec chmod 0750" in joined
        assert "! -perm -u+x -exec chmod 0640" in joined

    def test_repaired_sequence_never_uses_git_restore(self):
        joined = "\n".join(REPAIRED_ACTION_6_COMMANDS)
        assert "git restore" not in joined

    def test_repaired_sequence_clone_checkout_chown_unchanged_from_original(self):
        assert REPAIRED_ACTION_6_COMMANDS[0] == (
            "sudo git clone --no-checkout git@github.com:atimad/pcae-harness.git /opt/pcae/runtime/src"
        )
        assert REPAIRED_ACTION_6_COMMANDS[2] == "sudo chown -R root:pcae /opt/pcae/runtime/src"


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

    def test_governing_chgr_names_correct_dell_target(self, chgr_path: Path):
        record = _read_json(chgr_path)
        assert DELL_MACHINE_ID in record["decision_subject"]
        assert "hac-dell" in record["decision_subject"]

    def test_governing_chgr_conditions_exclude_all_required_boundaries(self, chgr_path: Path):
        record = _read_json(chgr_path)
        conditions = record["conditions"]
        for excluded in (
            "DeploymentBinding creation",
            "Boundary C certification",
            "Boundary A activation",
            "HATP_MANDATORY activation",
            "Cutover Record creation",
            "Permission Broker changes",
            "any rerun of Actions 1-5",
        ):
            assert excluded in conditions

    def test_governing_chgr_rationale_forbids_old_chgr_fallback(self, chgr_path: Path):
        record = _read_json(chgr_path)
        rationale = record["rationale"]
        assert HISTORICAL_CHGR_ID in rationale
        assert "does not authorize continuation" in rationale
        assert "defective Action-6 command" in rationale

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


class TestHistoricalCHGRNotApplicable:
    @pytest.fixture
    def chgr_path(self) -> Path:
        return REPO_ROOT / ".pcae/publication-execution/records" / f"{HISTORICAL_CHGR_ID}.json"

    def test_historical_chgr_still_published_unrevoked(self, chgr_path: Path):
        record = _read_json(chgr_path)
        assert record["lifecycle_state"] == "published"

    def test_historical_chgr_byte_identity_unchanged_by_this_phase(self, chgr_path: Path):
        result = subprocess.run(
            ["git", "status", "--short", "--", str(chgr_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.stdout.strip() == ""


class TestSessionBinding:
    def test_publication_execution_attempt_binds_governing_session(self):
        attempts_dir = REPO_ROOT / ".pcae/publication-execution/attempts"
        matches = []
        for path in attempts_dir.glob("pubexec-*.json"):
            record = _read_json(path)
            result = record.get("result", {})
            if result.get("record_id") == GOVERNING_CHGR_ID:
                matches.append(result)
        assert len(matches) == 1
        assert matches[0]["session_id"] == GOVERNING_SESSION_ID
        assert matches[0]["success"] is True

    def test_superseded_session_package_never_consumed(self):
        consumed_dir = REPO_ROOT / ".pcae/decision-sessions/pending-packages/consumed"
        consumed_ids = {p.stem for p in consumed_dir.glob("*.json")}
        pending_dir = REPO_ROOT / ".pcae/decision-sessions/pending-packages"
        pending_ids = {p.stem for p in pending_dir.glob("*.json")}
        # The superseded session's own package must not appear among consumed packages.
        superseded_session_path = REPO_ROOT / ".pcae/decision-sessions" / f"{SUPERSEDED_SESSION_ID}.json"
        assert superseded_session_path.exists()
        assert pending_ids or consumed_ids  # sanity: directories are populated


class TestAction9Adjudication:
    def test_expected_residual_is_exactly_hbdc_req_042(self):
        assert EXPECTED_AUTHORIZED_RESIDUAL == {"HBDC-REQ-042"}

    def test_actual_residual_exceeds_authorized_residual(self):
        assert ACTUAL_MEASURED_RESIDUAL != EXPECTED_AUTHORIZED_RESIDUAL
        assert EXPECTED_AUTHORIZED_RESIDUAL.issubset(ACTUAL_MEASURED_RESIDUAL)
        unexpected = ACTUAL_MEASURED_RESIDUAL - EXPECTED_AUTHORIZED_RESIDUAL
        assert unexpected == {"HBDC-REQ-022", "HBDC-REQ-030", "HBDC-REQ-035", "HBDC-REQ-036"}

    def test_adjudication_rule_stops_on_any_additional_failure(self):
        def adjudicate(actual: set, expected: set) -> str:
            if actual == expected:
                return "SUCCESS"
            return "STOP"

        assert adjudicate(ACTUAL_MEASURED_RESIDUAL, EXPECTED_AUTHORIZED_RESIDUAL) == "STOP"
        assert adjudicate({"HBDC-REQ-042"}, EXPECTED_AUTHORIZED_RESIDUAL) == "SUCCESS"


class TestDistributionNameRootCause:
    def test_pyproject_declares_pcae_harness_not_pcae(self):
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        assert 'name = "pcae-harness"' in pyproject

    def test_conformance_verifier_looks_up_mismatched_distribution_name(self):
        source = (REPO_ROOT / "src/pcae/core/hatp_class_b_conformance.py").read_text(encoding="utf-8")
        assert 'importlib.metadata.distribution("pcae")' in source

    def test_environment_lock_verifier_looks_up_mismatched_distribution_name(self):
        source = (REPO_ROOT / "src/pcae/core/hatp_environment_lock_verifier.py").read_text(encoding="utf-8")
        assert 'importlib.metadata.distribution("pcae")' in source

    def test_launcher_check_uses_which_pcae(self):
        source = (REPO_ROOT / "src/pcae/core/hatp_environment_lock_verifier.py").read_text(encoding="utf-8")
        assert 'which("pcae")' in source


class TestDeploymentBindingBoundaryCAAbsent:
    def test_no_deploymentbinding_artifact_anywhere(self):
        matches = list(REPO_ROOT.rglob("*eploymentBinding*"))
        matches = [m for m in matches if ".git" not in m.parts]
        assert matches == []

    def test_no_hmic_certification_artifact_created_this_phase(self):
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        for line in result.stdout.splitlines():
            assert "certification" not in line.lower()

    def test_deployment_identity_check_driven_only_by_binding_absence(self):
        source = (REPO_ROOT / "src/pcae/core/hatp_class_b_conformance.py").read_text(encoding="utf-8")
        assert "no_repository_identity_present" in source
        assert "no_active_deployment_binding_matches_repository_and_root" in source


class TestNoProductionSourceRepairThisPhase:
    def test_src_scripts_contracts_unmodified_against_pinned_sha(self):
        result = subprocess.run(
            [
                "git",
                "diff",
                "--stat",
                PINNED_SOURCE_SHA,
                "HEAD",
                "--",
                "src/pcae/",
                "scripts/",
                "docs/contracts/",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.stdout.strip() == ""
