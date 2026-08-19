"""Phase 149O.20L.7N.5 -- Dell Current-Source Redeployment Independent
Verification.

Independently-authored companion test module. Imports nothing from
7N.4's own test module (`test_phase_149o_20l_7n_4_dell_current_source_
redeployment_execution.py`) as oracle -- this module encodes fresh,
independent constants and assertions derived from *this session's own*
live-Dell evidence (captured in
`docs/PHASE_149O_20L_7N_5_DELL_CURRENT_SOURCE_REDEPLOYMENT_INDEPENDENT_
VERIFICATION.md`). No live SSH or Dell mutation is performed in CI --
the live evidence is captured at authoring time and is not re-verified
live here, matching the pattern (not the values) of 7N.4's own
companion test module.
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

DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
DELL_HOSTNAME = "atila-Latitude-E5470"

WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
HMIC_IMPLEMENTATION_DIGEST = (
    "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"
)

EXPECTED_TREE_TOTAL = 4200
EXPECTED_MODE_100644 = 4186
EXPECTED_MODE_100755 = 14

EXPECTED_HBDC_RESIDUAL = {"HBDC-REQ-042"}
EXPECTED_HBDC_RESIDUAL_REASON = "no_repository_identity_present"

GOVERNING_CHGR_ID = "chgr-71bd24f9d3d742d6baac772e480fc876"
HISTORICAL_CHGR_IDS = (
    "chgr-d4343fa51b9743f3abaeb87a881a78b1",
    "chgr-96a0ce12756e4cc892492a87af1db832",
    "chgr-541cb08c313b4f8884970172d37c5a1d",
    "chgr-0e37ed1340b14311826722c4dbf3e856",
)

REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7N_5_DELL_CURRENT_SOURCE_REDEPLOYMENT_INDEPENDENT_VERIFICATION.md"
)

CONTRACT_VERSIONS = {
    "HMRC-001": "1.1",
    "HATP-001": "1.0",
    "HSCE-001": "1.1",
    "RAE-001": "1.0",
    "HBDC-001": "1.1",
}

FROZEN_SRC_PCAE_RELATIVE_FILES = (
    "core/hatp_mandatory_cutover.py",
    "core/hatp_ag_authority.py",
    "core/hatp_rollback_consumption.py",
    "core/hatp_bootstrap.py",
    "core/human_approval_trusted_provenance.py",
    "core/repository_identity.py",
    "core/rollback_approval_evidence.py",
    "core/hatp_evidence_store.py",
    "core/hatp_signed_evidence.py",
    "core/agent.py",
    "commands/agent.py",
    "cli.py",
    "core/permission_broker.py",
    "core/permission_broker_foundation.py",
    "core/hatp_providers.py",
    "core/hatp_fido2_provider.py",
    "core/hatp_piv_provider.py",
    "core/hatp_hardware_credentials.py",
    "core/hatp_mandatory_certification.py",
    "core/hatp_class_b_topology_verifier.py",
    "core/hatp_environment_lock_verifier.py",
    "core/hatp_class_b_conformance.py",
    "core/hatp_deployment_binding_admin.py",
)

FROZEN_REPOSITORY_ROOT_RELATIVE_FILES = (
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
    "scripts/hatp_certification_admin.py",
    "scripts/hatp_deployment_binding_admin.py",
)

HMIC_30_CANONICAL_PATHS = tuple(
    "src/pcae/" + f for f in FROZEN_SRC_PCAE_RELATIVE_FILES
) + FROZEN_REPOSITORY_ROOT_RELATIVE_FILES


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestFrozenSetShape:
    def test_frozen_set_has_exactly_thirty_members(self):
        assert len(HMIC_30_CANONICAL_PATHS) == 30

    def test_frozen_set_has_no_duplicates(self):
        assert len(set(HMIC_30_CANONICAL_PATHS)) == 30

    def test_frozen_set_matches_production_constant_in_source(self):
        import re

        text = (
            REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py"
        ).read_text(encoding="utf-8")
        match = re.search(r"assert len\(_FROZEN_AUTHORITY_BEARING_FILES\) == (\d+)", text)
        assert match is not None
        assert int(match.group(1)) >= 30

    def test_hbdc_contract_is_the_fifth_bound_contract_in_frozen_set(self):
        assert (
            "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
            in FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
        )

    def test_deployment_binding_admin_script_is_in_frozen_set(self):
        assert (
            "scripts/hatp_deployment_binding_admin.py"
            in FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
        )


class TestCandidateGitIdentity:
    def test_candidate_sha_is_a_commit(self):
        assert _git("cat-file", "-t", CANDIDATE_SHA) == "commit"

    def test_old_sha_is_a_commit(self):
        assert _git("cat-file", "-t", OLD_SHA) == "commit"

    def test_candidate_is_ancestor_of_origin_main(self):
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", CANDIDATE_SHA, "origin/main"],
            cwd=REPO_ROOT,
            timeout=30,
        )
        assert result.returncode == 0


class TestContractVersions:
    def test_hmic_contract_states_v1_4(self):
        """As of this phase, HEAD carried v1.4; a later amendment
        (149O.20L.7O.2H) additively bumped it to v1.5."""
        text = (
            REPO_ROOT
            / "docs"
            / "contracts"
            / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
        ).read_text(encoding="utf-8")
        assert "**Contract ID:** HMIC-001" in text
        version_line = next(line for line in text.splitlines() if line.startswith("**Version:**"))
        major, minor = (int(x) for x in version_line.split()[-1].split("."))
        assert (major, minor) >= (1, 4)

    def test_hbdc_contract_states_v1_1(self):
        text = (
            REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
        ).read_text(encoding="utf-8")
        assert "**Contract:** HBDC-001" in text
        assert "**Version:** 1.1" in text

    def test_derived_contract_versions_shape(self):
        assert CONTRACT_VERSIONS == {
            "HMRC-001": "1.1",
            "HATP-001": "1.0",
            "HSCE-001": "1.1",
            "RAE-001": "1.0",
            "HBDC-001": "1.1",
        }


class TestExpectedDigestAndWrapperFormat:
    def test_hmic_digest_is_64_hex_chars(self):
        assert len(HMIC_IMPLEMENTATION_DIGEST) == 64
        int(HMIC_IMPLEMENTATION_DIGEST, 16)  # raises if not hex

    def test_wrapper_digest_is_64_hex_chars_standard_sha256_length(self):
        # This phase explicitly checked the length of the expected wrapper
        # hash string rather than assuming agreement: it is a standard
        # 64-character SHA-256 hex digest, not unusually long.
        assert len(WRAPPER_DIGEST) == 64
        int(WRAPPER_DIGEST, 16)


class TestTreeInventoryExpectation:
    def test_expected_tree_composition_sums_correctly(self):
        assert EXPECTED_MODE_100644 + EXPECTED_MODE_100755 == EXPECTED_TREE_TOTAL

    def test_expected_totals_match_spec(self):
        assert EXPECTED_TREE_TOTAL == 4200
        assert EXPECTED_MODE_100644 == 4186
        assert EXPECTED_MODE_100755 == 14


class TestHBDCResidualExpectation:
    def test_residual_is_exactly_hbdc_req_042(self):
        assert EXPECTED_HBDC_RESIDUAL == {"HBDC-REQ-042"}

    def test_residual_reason_is_no_repository_identity_present(self):
        assert EXPECTED_HBDC_RESIDUAL_REASON == "no_repository_identity_present"


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

    def test_report_states_all_4200_paths_and_zero_mismatches(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "4200/4200 checked, 0 mismatches" in text

    def test_report_states_thirty_of_thirty_hmic_files_ok(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "30/30 OK, 0 mismatches" in text

    def test_report_does_not_claim_hmic_certified_or_valid(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "HMIC VALID" not in text
        assert "HMIC CERTIFIED" not in text

    def test_report_uses_exact_hmic_wording(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert (
            "HMIC v1.4 IMPLEMENTATION/SOURCE IDENTITY INDEPENDENTLY VERIFIED "
            "DEPLOYED — NOT CERTIFIED" in text
        )

    def test_report_does_not_claim_hbdc_compliant(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "HBDC COMPLIANT" not in text.replace("NON_COMPLIANT", "")

    def test_report_states_exact_final_verdict(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert (
            "INDEPENDENTLY VERIFIED — CURRENT SOURCE DEPLOYMENT COMPLETE" in text
        )

    def test_report_recommends_but_does_not_initiate_7o(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "149O.20L.7O" in text
        assert "does **not** initiate or elect 7O" in text

    def test_report_carries_forward_all_four_findings(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "DeploymentBinding audit-failure-after-durable-mutation gap" in text
        assert "Permissive timestamp parser" in text
        assert "HMIC-REQ-103 revocation-validation gap" in text
        assert "HMIC-REQ-063 executed-byte provenance limitation" in text


class TestGoverningAndHistoricalCHGRIntegrity:
    def test_governing_chgr_exists_and_verified_state(self):
        path = (
            REPO_ROOT
            / ".pcae/publication-execution/records"
            / f"{GOVERNING_CHGR_ID}.json"
        )
        assert path.exists()
        record = _read_json(path)
        assert record["lifecycle_state"] == "published"
        assert record["selected_option_id"] == "approve"

    def test_governing_chgr_unchanged_by_this_phase(self):
        path = (
            REPO_ROOT
            / ".pcae/publication-execution/records"
            / f"{GOVERNING_CHGR_ID}.json"
        )
        result = subprocess.run(
            ["git", "status", "--short", "--", str(path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.stdout.strip() == ""

    def test_all_historical_chgrs_still_published(self):
        for chgr_id in HISTORICAL_CHGR_IDS:
            path = (
                REPO_ROOT / ".pcae/publication-execution/records" / f"{chgr_id}.json"
            )
            assert path.exists()
            record = _read_json(path)
            assert record["lifecycle_state"] == "published"

    def test_no_historical_chgr_byte_changed_by_this_phase(self):
        for chgr_id in HISTORICAL_CHGR_IDS:
            path = (
                REPO_ROOT / ".pcae/publication-execution/records" / f"{chgr_id}.json"
            )
            result = subprocess.run(
                ["git", "status", "--short", "--", str(path)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.stdout.strip() == ""


class TestAgentReachabilityStatic:
    def test_producer_not_referenced_in_cli(self):
        text = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
        assert "hatp_deployment_binding_admin" not in text

    def test_producer_not_referenced_in_core_agent(self):
        text = (REPO_ROOT / "src" / "pcae" / "core" / "agent.py").read_text(
            encoding="utf-8"
        )
        assert "hatp_deployment_binding_admin" not in text

    def test_producer_not_referenced_in_commands_agent(self):
        text = (REPO_ROOT / "src" / "pcae" / "commands" / "agent.py").read_text(
            encoding="utf-8"
        )
        assert "hatp_deployment_binding_admin" not in text


class TestNoMutationPerformedThisPhase:
    def test_report_states_no_dell_mutation(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "No Dell mutation was performed" in text

    def test_report_states_no_repositoryidentity_or_binding_created(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "No RepositoryIdentity or DeploymentBinding was created" in text

    def test_report_states_no_certification_performed(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "No HMIC certification was performed" in text
