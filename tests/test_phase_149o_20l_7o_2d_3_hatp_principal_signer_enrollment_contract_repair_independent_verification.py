"""Phase 149O.20L.7O.2D.3 -- HATP Principal/Signer Enrollment Contract
Repair Independent Verification.

This phase is read-only independent contract verification of HPSE-001
v1.1 (the 149O.20L.7O.2D.2 repair amendment): no enrollment writer was
implemented, no HHCE-001 writer was implemented, no hardware-provider
implementation change was made, no `PrincipalRecord`/`SignerRecord`/
`HardwareCredentialRecord` was written, no credential was provisioned,
no `DeploymentBinding` was created, no election was initiated, no CHGR
was published, no certification was performed, and no Dell mutation
occurred. These tests mechanically re-verify this phase's own
load-bearing factual claims (the phase report,
`docs/PHASE_149O_20L_7O_2D_3_...md`) directly against live source and the
frozen contract text -- never against 7O.2D.2's own report/tests/prose.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOC_PATH = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2D_3_HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT_REPAIR_INDEPENDENT_VERIFICATION.md"
)
_HPSE_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"
_HBDC_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_BOOTSTRAP_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py"
_FIDO2_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_fido2_provider.py"
_PIV_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_piv_provider.py"
_ADMIN_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_deployment_binding_admin.py"
_HARDWARE_CREDENTIALS_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credentials.py"
_MANDATORY_CERT_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py"


def _read(path: Path) -> str:
    return path.read_text()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Requirement numbering, mechanically re-verified for v1.1 (not taken
#    from 7O.2D.2's own claim).
# ═══════════════════════════════════════════════════════════════════════════


class TestRequirementNumberingIndependentlyReverified:
    def test_hpse_req_range_is_exactly_001_through_074_no_gaps_no_duplicates(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        defined = sorted(int(n) for n in re.findall(r"\*\*HPSE-REQ-(\d{3})\b", text))
        assert defined == list(range(1, 75))

    def test_contract_declares_version_1_1(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        assert "**Version:** 1.1" in text

    def test_exactly_three_requirements_marked_revised_in_place(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        revised = re.findall(r"\*\*HPSE-REQ-(\d{3}) \(revised", text)
        assert sorted(revised) == ["011", "045", "046"]

    def test_hbdc_dependency_line_still_reads_v1_0_disclosed_stale(self) -> None:
        # NB-5: HBDC-001's own "Depends on" line was deliberately left
        # unbumped (HBDC-001's substantive text does not change) -- this
        # is disclosed staleness, not an oversight this phase must repair.
        text = _read(_HBDC_CONTRACT_PATH)
        assert "HPSE-001 v1.0" in text


# ═══════════════════════════════════════════════════════════════════════════
# 2. B-149O.20L.7O.2D.1-2 re-derivation: credential_identity() has zero
#    working implementation for FIDO2 or PIV -- unconditional raise,
#    independent of device presence.
# ═══════════════════════════════════════════════════════════════════════════


class TestCredentialIdentityUnconditionalRaise:
    def test_fido2_credential_identity_body_is_pure_raise(self) -> None:
        source = _read(_FIDO2_PATH)
        match = re.search(r"def credential_identity\(self\) -> str:\n(.*?)\n\n    def ", source, re.DOTALL)
        assert match is not None
        body = match.group(1)
        assert "raise HATPProviderUnavailableError" in body
        assert "if " not in body

    def test_piv_credential_identity_body_is_pure_raise(self) -> None:
        source = _read(_PIV_PATH)
        match = re.search(r"def credential_identity\(self\) -> str:\n(.*?)\n\n    def ", source, re.DOTALL)
        assert match is not None
        body = match.group(1)
        assert "raise HATPProviderUnavailableError" in body
        assert "if " not in body


# ═══════════════════════════════════════════════════════════════════════════
# 3. B-149O.20L.7O.2D.1-1 re-derivation: no hardware-credentials.json
#    writer exists in production source.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoHardwareCredentialWriterExists:
    def test_hardware_credentials_module_exposes_no_mutating_api(self) -> None:
        source = _read(_HARDWARE_CREDENTIALS_PATH)
        for forbidden in ("def enroll", "def register_credential", "def revoke_credential", "def deactivate_credential"):
            assert forbidden not in source

    def test_hardware_credentials_module_is_read_only_lookup_only(self) -> None:
        source = _read(_HARDWARE_CREDENTIALS_PATH)
        assert "class HATPHardwareCredentialStore" in source
        assert "def lookup_credential" in source

    def test_no_hhce_writer_module_exists_anywhere_in_src_or_scripts(self) -> None:
        for base in (_REPO_ROOT / "src", _REPO_ROOT / "scripts"):
            for path in base.rglob("*.py"):
                if ".claude/worktrees" in str(path):
                    continue
                text = path.read_text(errors="ignore")
                assert "def register_credential" not in text
                assert "def enroll_signer" not in text
                assert "def enroll_principal" not in text


# ═══════════════════════════════════════════════════════════════════════════
# 4. Cross-registry structural closure (HPSE-REQ-056/HPI-7) -- the text
#    exists and names the precondition precisely.
# ═══════════════════════════════════════════════════════════════════════════


class TestCrossRegistryPreconditionText:
    def test_hpse_req_056_exists_and_names_active_hardware_credential_precondition(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        assert "HPSE-REQ-056" in text
        match = re.search(r"\*\*HPSE-REQ-056\.\*\*(.*?)(?=\n\n|\Z)", text, re.DOTALL)
        assert match is not None
        body = match.group(1)
        assert "active" in body
        assert "HardwareCredentialRecord" in body

    def test_hpi_7_names_structural_not_disclosed_only_closure(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        assert "HPI-7" in text
        assert "structurally" in text

    def test_lock_ordering_requirement_hpse_req_057_states_fixed_global_order(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        match = re.search(r"\*\*HPSE-REQ-057\.\*\*(.*?)(?=\n\n|\Z)", text, re.DOTALL)
        assert match is not None
        body = match.group(1)
        assert "outer" in body
        assert "inner" in body


# ═══════════════════════════════════════════════════════════════════════════
# 5. No implementation was added by this phase or 7O.2D.2 -- production
#    src/pcae Python is unmodified relative to the pre-7O.2D.2 baseline.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoProductionImplementationExists:
    def test_hardware_credentials_module_docstring_still_defers_enrollment(self) -> None:
        source = _read(_HARDWARE_CREDENTIALS_PATH)
        assert "Enrollment (writing a new credential into this registry) is explicitly" in source
        assert "OUT of Wave-5 scope" in source

    def test_mandatory_cert_frozen_file_set_already_includes_provider_and_credential_files(self) -> None:
        source = _read(_MANDATORY_CERT_PATH)
        for relative in (
            "core/hatp_hardware_credentials.py",
            "core/hatp_fido2_provider.py",
            "core/hatp_piv_provider.py",
        ):
            assert f'"{relative}"' in source


# ═══════════════════════════════════════════════════════════════════════════
# 6. Runtime neutrality: agent-runtime terms appear only in the two
#    dedicated neutrality-disclaiming requirements, nowhere else.
# ═══════════════════════════════════════════════════════════════════════════


class TestRuntimeNeutrality:
    def test_runtime_terms_confined_to_req_051_and_req_074(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        lines_with_terms = [
            i
            for i, line in enumerate(text.splitlines())
            if re.search(r"\bClaude\b|\bCodex\b|\bDeepSeek\b", line)
        ]
        for idx in lines_with_terms:
            line = text.splitlines()[idx]
            assert "HPSE-REQ-051" in line or "HPSE-REQ-074" in line


# ═══════════════════════════════════════════════════════════════════════════
# 7. Phase report internal consistency (this phase's own claims,
#    mechanically checked, not merely narrated).
# ═══════════════════════════════════════════════════════════════════════════


class TestPhaseReportSelfConsistency:
    def test_report_exists(self) -> None:
        assert _DOC_PATH.exists()

    def test_report_names_own_phase_id(self) -> None:
        text = _read(_DOC_PATH)
        assert "149O.20L.7O.2D.3" in text

    def test_report_states_no_implementation_performed(self) -> None:
        text = _read(_DOC_PATH)
        assert "no implementation" in text.lower() or "No implementation" in text

    def test_report_cites_a_final_verdict(self) -> None:
        text = _read(_DOC_PATH)
        assert "VERIFIED" in text
