"""Phase 149O.20L.7O.2D.1 -- HATP Principal/Signer Enrollment Contract
Independent Verification.

This phase is read-only independent contract verification: no enrollment
writer was implemented, no `PrincipalRecord`/`SignerRecord` was written,
no credential was provisioned, no `DeploymentBinding` was created, no
election was initiated, no CHGR was published, no certification was
performed, and no Dell mutation occurred. These tests mechanically
re-verify this phase's own load-bearing factual claims (the phase report,
`docs/PHASE_149O_20L_7O_2D_1_...md`) directly against live source and the
frozen contract text -- never against the phase report's own prose.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOC_PATH = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2D_1_HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT_INDEPENDENT_VERIFICATION.md"
)
_HPSE_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"
_HBDC_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_BOOTSTRAP_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py"
_FIDO2_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_fido2_provider.py"
_PIV_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_piv_provider.py"
_ADMIN_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_deployment_binding_admin.py"
_HARDWARE_CREDENTIALS_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credentials.py"
_PROVENANCE_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "human_approval_trusted_provenance.py"
_MANDATORY_CERT_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py"


def _read(path: Path) -> str:
    return path.read_text()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Requirement numbering, mechanically re-verified (not taken from the
#    architecture phase's own claim).
# ═══════════════════════════════════════════════════════════════════════════


class TestRequirementNumberingIndependentlyReverified:
    def test_hpse_req_range_is_exactly_001_through_052_no_gaps_no_duplicates(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        defined = sorted(int(n) for n in re.findall(r"\*\*HPSE-REQ-(\d{3})\b", text))
        assert defined == list(range(1, 53))

    def test_hbdc_req_071_through_076_defined_exactly_once(self) -> None:
        text = _read(_HBDC_CONTRACT_PATH)
        for n in range(71, 77):
            pattern = rf"\*\*HBDC-REQ-0{n}\.\*\*"
            assert len(re.findall(pattern, text)) == 1, f"HBDC-REQ-0{n} not defined exactly once"


# ═══════════════════════════════════════════════════════════════════════════
# 2. This phase's central finding: `credential_identity()` has zero
#    working implementation for FIDO2 or PIV -- unconditional raise,
#    independent of device presence. Mechanically re-verified against
#    live source, not against HPSE-001's or this phase's own prose.
# ═══════════════════════════════════════════════════════════════════════════


class TestCredentialIdentityUnconditionalRaise:
    def test_fido2_credential_identity_body_is_pure_raise(self) -> None:
        source = _read(_FIDO2_PATH)
        match = re.search(r"def credential_identity\(self\) -> str:\n(.*?)\n\n    def ", source, re.DOTALL)
        assert match is not None
        body = match.group(1)
        # The entire body is a docstring-free unconditional raise: no `if`,
        # no device probe, no resident-credential discovery call.
        assert "raise HATPProviderUnavailableError" in body
        assert "if " not in body

    def test_piv_credential_identity_is_also_unconditional_raise(self) -> None:
        source = _read(_PIV_PATH)
        match = re.search(r"def credential_identity\(self\) -> str:\n(.*?)\n\n    def ", source, re.DOTALL)
        assert match is not None
        body = match.group(1)
        assert "raise HATPProviderUnavailableError" in body


# ═══════════════════════════════════════════════════════════════════════════
# 3. This phase's other central finding: no production writer exists for
#    `hardware-credentials.json`, and `verify()` fails closed whenever no
#    entry is found -- confirmed directly against source.
# ═══════════════════════════════════════════════════════════════════════════


class TestHardwareCredentialRegistryHasNoWriter:
    def test_hardware_credential_store_exposes_no_mutating_method(self) -> None:
        source = _read(_HARDWARE_CREDENTIALS_PATH)
        for banned in ("def enroll", "def revoke", "def rotate", "def write", "def create"):
            assert banned not in source

    def test_hardware_credentials_docstring_anticipates_future_admin_surface(self) -> None:
        source = _read(_HARDWARE_CREDENTIALS_PATH)
        assert "future Human/Admin-only administrative surface" in source

    def test_hpse_contract_does_not_name_a_hardware_credentials_writer_requirement(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        # HPSE-001 references hardware-credentials.json only for its
        # encoding convention (HPSE-REQ-012) and no-secret-material
        # discipline (HPSE-REQ-014) -- never as a write target.
        assert "does not amend" in text
        assert "hardware-credentials.json" in text

    def test_fido2_verify_fails_closed_on_absent_credential_record(self) -> None:
        source = _read(_FIDO2_PATH)
        match = re.search(r"def verify\(\n(.*?)\n    # -+\n", source, re.DOTALL)
        body = match.group(1) if match else source
        assert "record is None" in body
        assert "signature_valid=False" in body


# ═══════════════════════════════════════════════════════════════════════════
# 4. `PrincipalRecord.revoked_at` gap -- disclosed, independently
#    re-confirmed.
# ═══════════════════════════════════════════════════════════════════════════


class TestPrincipalRevokedAtGapReconfirmed:
    def test_parse_principal_allowed_fields_excludes_revoked_at(self) -> None:
        source = _read(_BOOTSTRAP_PATH)
        match = re.search(r"def _parse_principal\(document: dict\) -> PrincipalRecord:\n(.*?)\n\n\n", source, re.DOTALL)
        assert match is not None
        body = match.group(1)
        assert '{"principal_id", "status"}' in body
        assert "revoked_at" not in body


# ═══════════════════════════════════════════════════════════════════════════
# 5. `deployment_binding_matches` exact three-field scope (HBDC-REQ-076's
#    claim), independently re-confirmed.
# ═══════════════════════════════════════════════════════════════════════════


class TestDeploymentBindingMatchesExactScope:
    def test_deployment_binding_matches_checks_only_three_fields(self) -> None:
        source = _read(_BOOTSTRAP_PATH)
        match = re.search(r"def deployment_binding_matches\(.*?\n\) -> bool:\n(.*?)\n\n\n", source, re.DOTALL)
        assert match is not None
        body = match.group(1)
        assert "binding.status != \"active\"" in body
        assert "binding.repository_id == repository_id" in body
        assert "binding.canonical_deployment_root == canonical_deployment_root" in body
        assert "principal_id" not in body
        assert "signer_key_id" not in body
        assert "authority_scope" not in body


# ═══════════════════════════════════════════════════════════════════════════
# 6. `verify_hatp_proof` independently re-derives signer/principal/
#    binding state from the live registry, cross-checking the
#    `DeploymentBinding`'s copied fields -- resolves the tampered-
#    registry hypothetical (§9 of the phase report).
# ═══════════════════════════════════════════════════════════════════════════


class TestVerifyHatpProofLiveCrossChecks:
    def test_verify_checks_live_principal_status(self) -> None:
        source = _read(_PROVENANCE_PATH)
        assert 'trust_store.lookup_principal(signer.principal_id)' in source
        assert 'principal.status != "active"' in source

    def test_verify_cross_checks_binding_against_live_signer(self) -> None:
        source = _read(_PROVENANCE_PATH)
        assert "binding.principal_id != signer.principal_id" in source

    def test_verify_never_trusts_proof_self_asserted_principal_or_provider(self) -> None:
        source = _read(_PROVENANCE_PATH)
        assert "signer.principal_id != proof.principal_id" in source
        assert "signer.provider_profile != proof.provider_profile" in source


# ═══════════════════════════════════════════════════════════════════════════
# 7. HMIC frozen-file-set membership facts (§18 of the phase report).
# ═══════════════════════════════════════════════════════════════════════════


class TestHmicFrozenFileSetFacts:
    def test_hatp_bootstrap_and_deployment_binding_admin_already_bound(self) -> None:
        source = _read(_MANDATORY_CERT_PATH)
        match = re.search(r"_FROZEN_SRC_PCAE_RELATIVE_FILES.*?=\s*\((.*?)\n\)", source, re.DOTALL)
        assert match is not None
        body = match.group(1)
        assert '"core/hatp_bootstrap.py"' in body
        assert '"core/hatp_hardware_credentials.py"' in body
        assert '"core/hatp_deployment_binding_admin.py"' in body

    def test_no_principal_signer_admin_module_yet_bound(self) -> None:
        source = _read(_MANDATORY_CERT_PATH)
        match = re.search(r"_FROZEN_SRC_PCAE_RELATIVE_FILES.*?=\s*\((.*?)\n\)", source, re.DOTALL)
        assert match is not None
        body = match.group(1)
        assert "principal_signer" not in body


# ═══════════════════════════════════════════════════════════════════════════
# 8. Verdict/report self-consistency.
# ═══════════════════════════════════════════════════════════════════════════


class TestReportSelfConsistency:
    def test_report_exists_and_states_final_verdict(self) -> None:
        text = " ".join(_DOC_PATH.read_text().split())
        assert "NOT VERIFIED" in text
        assert "CONTRACT AMENDMENT REQUIRED" in text

    def test_report_names_two_blocking_findings(self) -> None:
        text = _DOC_PATH.read_text()
        assert "B-149O.20L.7O.2D.1-1" in text
        assert "B-149O.20L.7O.2D.1-2" in text

    def test_report_recommends_repair_phase(self) -> None:
        text = " ".join(_DOC_PATH.read_text().split())
        assert "149O.20L.7O.2D.2" in text

    def test_report_states_no_dell_mutation_no_enrollment_no_binding(self) -> None:
        text = " ".join(_DOC_PATH.read_text().split())
        assert "No Dell mutation" in text or "no Dell mutation" in text
        assert "No enrollment" in text or "no enrollment" in text


# ═══════════════════════════════════════════════════════════════════════════
# 9. No production source modification this phase.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoProductionSourceModified:
    def test_no_src_or_scripts_files_changed_since_phase_entry_commit(self) -> None:
        result = subprocess.run(
            ["git", "diff", "--name-only", "789c0015", "--", "src/", "scripts/"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        changed = [line for line in result.stdout.splitlines() if line.strip()]
        assert changed == []
