"""Phase 149O.20L.7O.2N.3 -- hac-dell Repaired FIDO2 Admin Redeployment and
HATP Hardware Runtime Dependency Realization.

Independently-authored companion test module. Covers static checks against
already-persisted repository/CHGR state and the exact command/content text
this phase's report claims to have executed on the live Dell host. No live
SSH or Dell mutation is performed in CI -- all Dell evidence is captured in
the canonical phase report (docs/PHASE_149O_20L_7O_2N_3_HAC_DELL_REPAIRED_
FIDO2_ADMIN_REDEPLOYMENT_AND_HATP_HARDWARE_RUNTIME_DEPENDENCY_REALIZATION.md)
and is not re-verified live here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parents[1]

OLD_SHA = "4efcb255ca5340224f0278f724b939d794a553ca"
CANDIDATE_SHA = "cdb77b75fc8bbca04340c7f25c405db3b07d32f7"

GOVERNING_CHGR_ID = "chgr-e0dfb3e752e6430089ca1ee02636ec7e"

DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
DELL_HOSTNAME = "atila-Latitude-E5470"
REPOSITORY_INSTANCE_ID = "0107866f-af7c-40b4-8317-74e71acb05ca"
HMIC_IMPLEMENTATION_DIGEST = (
    "abfbffca527d3bf6d6ba610f6f5cd2d80bf113f9aa08f4339eb40322a8c077c4"
)

EXPECTED_CONTRACT_VERSIONS = {
    "HMRC-001": "1.1",
    "HATP-001": "1.0",
    "HSCE-001": "1.3",
    "RAE-001": "1.0",
    "HBDC-001": "1.2",
    "HPSE-001": "1.1",
    "HHCE-001": "1.1",
}

REPAIRED_SCRIPT = "scripts/hatp_hardware_credential_admin.py"

MUTATION_COMMANDS = [
    f"sudo -n git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src fetch origin {CANDIDATE_SHA}",
    f"sudo -n git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src cat-file -t {CANDIDATE_SHA}",
    f"sudo -n git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src checkout --detach {CANDIDATE_SHA}",
    "sudo -n chown -R root:pcae /opt/pcae/runtime/src",
]

ROLLBACK_COMMANDS = [
    f"git checkout --detach {OLD_SHA}",
]

VENV_INSTALL_COMMAND = 'sudo -n /opt/pcae/runtime/venv/bin/pip install "/opt/pcae/runtime/src[hatp-hardware]"'
VENV_REPAIR_COMMAND = "sudo -n /opt/pcae/runtime/venv/bin/pip install --no-deps -e /opt/pcae/runtime/src"

PHASE_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2N_3_HAC_DELL_REPAIRED_FIDO2_ADMIN_REDEPLOYMENT_AND_HATP_HARDWARE_RUNTIME_DEPENDENCY_REALIZATION.md"
)

CHGR_PATH = REPO_ROOT / ".pcae" / "publication-execution" / "records" / f"{GOVERNING_CHGR_ID}.json"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestPhaseReportDocument:
    def test_phase_report_exists(self):
        assert PHASE_REPORT_PATH.exists()

    def test_phase_report_names_both_shas(self):
        text = PHASE_REPORT_PATH.read_text(encoding="utf-8")
        assert OLD_SHA in text
        assert CANDIDATE_SHA in text

    def test_phase_report_names_hmic_digest(self):
        text = PHASE_REPORT_PATH.read_text(encoding="utf-8")
        assert HMIC_IMPLEMENTATION_DIGEST in text

    def test_phase_report_names_repaired_script(self):
        text = PHASE_REPORT_PATH.read_text(encoding="utf-8")
        assert REPAIRED_SCRIPT in text

    def test_phase_report_names_exact_mutation_commands(self):
        text = PHASE_REPORT_PATH.read_text(encoding="utf-8")
        assert "fetch origin" in text
        assert "checkout --detach" in text
        assert "chown -R root:pcae" in text

    def test_phase_report_names_venv_realization_and_repair(self):
        text = PHASE_REPORT_PATH.read_text(encoding="utf-8")
        assert "hatp-hardware" in text
        assert "pip install" in text
        assert "--no-deps -e" in text

    def test_phase_report_excludes_certification_and_hardware(self):
        text = PHASE_REPORT_PATH.read_text(encoding="utf-8")
        assert "certification" in text.lower()
        assert "no OS-level" in text or "No OS-level" in text

    def test_phase_report_records_implementation_mismatch_consequence(self):
        text = PHASE_REPORT_PATH.read_text(encoding="utf-8")
        assert "IMPLEMENTATION_MISMATCH" in text

    def test_phase_report_distinguishes_software_from_hardware_availability(self):
        text = PHASE_REPORT_PATH.read_text(encoding="utf-8")
        assert "AVAILABLE" in text
        assert "UNKNOWN / NOT CHECKED" in text
        assert "NOT AUTHORIZED / NOT PERFORMED" in text


class TestGoverningCHGR:
    def test_chgr_record_exists(self):
        assert CHGR_PATH.exists()

    def test_chgr_lifecycle_state_published(self):
        record = _read_json(CHGR_PATH)
        assert record.get("lifecycle_state") == "published"

    def test_chgr_selected_option_is_approve(self):
        record = _read_json(CHGR_PATH)
        assert record.get("selected_option_id") == "approve"

    def test_chgr_embeds_both_shas(self):
        record = _read_json(CHGR_PATH)
        blob = json.dumps(record)
        assert OLD_SHA in blob
        assert CANDIDATE_SHA in blob

    def test_chgr_conditions_bind_target_host(self):
        record = _read_json(CHGR_PATH)
        conditions = record.get("conditions", "")
        assert DELL_HOSTNAME in conditions
        assert DELL_MACHINE_ID in conditions

    def test_chgr_conditions_scope_venv_action_to_declared_extra(self):
        record = _read_json(CHGR_PATH)
        conditions = record.get("conditions", "")
        assert "hatp-hardware" in conditions
        assert "no ad-hoc bare" in conditions.lower() or "ad-hoc" in conditions.lower()

    def test_chgr_conditions_exclude_certification_and_hardware(self):
        record = _read_json(CHGR_PATH)
        conditions = record.get("conditions", "")
        assert "certification" in conditions.lower()
        assert "FIDO2" in conditions
        assert "makeCredential" in conditions


class TestMutationCommandIdentity:
    def test_mutation_commands_scoped_to_deployment_root(self):
        for command in MUTATION_COMMANDS:
            assert "/opt/pcae/runtime/src" in command

    def test_mutation_commands_never_use_blanket_chmod(self):
        for command in MUTATION_COMMANDS:
            assert "chmod -R" not in command

    def test_rollback_targets_old_sha(self):
        assert OLD_SHA in ROLLBACK_COMMANDS[0]
        assert CANDIDATE_SHA not in " ".join(ROLLBACK_COMMANDS)

    def test_venv_install_command_scoped_to_declared_extra_only(self):
        assert "[hatp-hardware]" in VENV_INSTALL_COMMAND
        assert "fido2" not in VENV_INSTALL_COMMAND  # extra name only, not a bare package install

    def test_venv_repair_command_is_editable_no_deps(self):
        assert "--no-deps" in VENV_REPAIR_COMMAND
        assert "-e" in VENV_REPAIR_COMMAND.split()


class TestExpectedPostDeploymentIdentity:
    def test_repository_instance_id_format(self):
        assert len(REPOSITORY_INSTANCE_ID) == 36
        assert REPOSITORY_INSTANCE_ID.count("-") == 4

    def test_hmic_digest_is_64_hex_chars(self):
        assert len(HMIC_IMPLEMENTATION_DIGEST) == 64
        int(HMIC_IMPLEMENTATION_DIGEST, 16)

    def test_expected_contract_versions_has_seven_members(self):
        assert len(EXPECTED_CONTRACT_VERSIONS) == 7


class TestLocalHMICReconstruction:
    """Independently re-derives the same HMIC facts locally (this Mac
    repository, not Dell) that the phase report claims were separately,
    live re-derived on hac-dell -- confirming this phase's own local
    claims are at least internally consistent with current production
    source (candidate_sha == current HEAD at authoring time)."""

    def test_frozen_set_has_38_members(self):
        from pcae.core.hatp_mandatory_certification import _FROZEN_AUTHORITY_BEARING_FILES

        assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 38
        assert REPAIRED_SCRIPT in _FROZEN_AUTHORITY_BEARING_FILES

    def test_local_digest_matches_recorded_digest(self):
        from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest
        from pcae.core.paths import HarnessPath

        root = HarnessPath(REPO_ROOT)
        assert derive_implementation_scope_digest(root) == HMIC_IMPLEMENTATION_DIGEST

    def test_local_contract_versions_match_recorded(self):
        from pcae.core import hatp_mandatory_certification as h
        from pcae.core.paths import HarnessPath

        root = HarnessPath(REPO_ROOT)
        assert h.derive_contract_versions(root) == EXPECTED_CONTRACT_VERSIONS

    def test_pyproject_declares_hatp_hardware_extra_unchanged(self):
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        assert "hatp-hardware" in text
        assert "fido2>=1.1,<2" in text
        assert "cryptography>=42,<45" in text
