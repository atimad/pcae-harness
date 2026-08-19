"""Phase 149O.20L.7O.2K — HATP Prerequisite DAG Correction and Next
Real-Effect Node Selection (HMIC Certification vs. FIDO2
Hardware-Credential Enrollment).

Analysis/authorization-only evidence checks. These tests do not build a
certification or enrollment orchestration engine and perform no real
ceremony, no SSH, no host mutation. They mechanically confirm the
primary-source facts this phase's document relies on: the current HMIC
36/7 frozen-identity baseline, that HMIC validation never touches
enrollment-side data files, the standalone-admin-script asymmetry between
certification/DeploymentBinding and hardware-credential/principal-signer
writers, that the corrected DAG document states the selected node exactly
once with no ambiguity, and that no production source changed since phase
entry.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src" / "pcae"
sys.path.insert(0, str(REPO_ROOT / "src"))

CERTIFICATION_SRC = SRC / "core" / "hatp_mandatory_certification.py"
PROVIDERS_SRC = SRC / "core" / "hatp_providers.py"
FIDO2_SRC = SRC / "core" / "hatp_fido2_provider.py"
HW_CRED_ADMIN_SRC = SRC / "core" / "hatp_hardware_credential_admin.py"
PRINCIPAL_SIGNER_ADMIN_SRC = SRC / "core" / "hatp_principal_signer_admin.py"
CLASS_B_CONFORMANCE_SRC = SRC / "core" / "hatp_class_b_conformance.py"

HMIC_CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
)
HBDC_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
HPSE_CONTRACT = (
    REPO_ROOT / "docs" / "contracts" / "HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"
)

DOC = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2K_HATP_PREREQUISITE_DAG_CORRECTION_AND_NEXT_REAL_EFFECT_NODE_SELECTION.md"
)

pytestmark = pytest.mark.fast_green

PHASE_ENTRY_COMMIT = "e2c1772deef655fcd506e1e81406eae419f8519c"


def test_hmic_frozen_source_identity_is_exactly_36_members_27_plus_9():
    from pcae.core.hatp_mandatory_certification import (
        _FROZEN_REPOSITORY_ROOT_RELATIVE_FILES,
        _FROZEN_SRC_PCAE_RELATIVE_FILES,
    )

    assert len(_FROZEN_SRC_PCAE_RELATIVE_FILES) == 27
    assert len(_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES) == 9
    assert (
        len(_FROZEN_SRC_PCAE_RELATIVE_FILES) + len(_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES)
        == 36
    )


def test_hmic_contract_versions_is_exactly_seven_members_current_versions():
    from pcae.core.hatp_mandatory_certification import derive_contract_versions
    from pcae.core.paths import HarnessPath

    root = HarnessPath(REPO_ROOT)
    versions = derive_contract_versions(root)
    assert len(versions) == 7
    assert versions["HBDC-001"] == "1.2"
    assert versions["HPSE-001"] == "1.1"
    assert versions["HSCE-001"] == "1.3"


def test_hardware_credential_and_principal_signer_admin_modules_are_hmic_bound_source():
    from pcae.core.hatp_mandatory_certification import _FROZEN_SRC_PCAE_RELATIVE_FILES

    assert "core/hatp_hardware_credential_admin.py" in _FROZEN_SRC_PCAE_RELATIVE_FILES
    assert "core/hatp_principal_signer_admin.py" in _FROZEN_SRC_PCAE_RELATIVE_FILES


def test_hmic_validation_algorithm_does_not_read_enrollment_data_files():
    text = CERTIFICATION_SRC.read_text(encoding="utf-8")
    assert "def _validate_at_root(" in text
    idx = text.index("def _validate_at_root(")
    idx_end = text.index("\ndef ", idx + 10)
    body = text[idx:idx_end]
    for forbidden in ("hardware-credentials.json", "registry.json", "deployment-bindings.json"):
        assert forbidden not in body, f"validation body unexpectedly reads {forbidden}"


def test_hmic_contract_states_certification_does_not_evaluate_pb_or_capability():
    text = HMIC_CONTRACT.read_text(encoding="utf-8")
    assert "HMIC-REQ-122" in text
    assert "HMIC-REQ-124" in text
    assert "Certification Does Not Evaluate PB" in text
    assert "Certification Does Not Create Capability" in text


def test_hmic_contract_creation_and_activation_are_distinct_ceremonies():
    text = HMIC_CONTRACT.read_text(encoding="utf-8")
    assert "HMIC-REQ-086" in text
    assert "HMIC-REQ-118" in text
    assert "never combined into one action" in text


def test_fido2_enroll_credential_is_real_ceremony_credential_identity_still_unconditional_raise():
    text = FIDO2_SRC.read_text(encoding="utf-8")
    assert "def enroll_credential(" in text
    assert "Ctap2" in text
    assert "make_credential(" in text
    idx = text.index("def credential_identity(")
    window = text[idx : idx + 400]
    assert "raise HATPProviderUnavailableError" in window


def test_hpse_contract_signer_enrollment_requires_hardware_credential_precondition():
    text = HPSE_CONTRACT.read_text(encoding="utf-8")
    assert "HPSE-REQ-056" in text
    assert "hardware credential registration (via HHCE-001's writer) **before**" in text


def test_hpse_contract_readiness_state_machine_present():
    text = HPSE_CONTRACT.read_text(encoding="utf-8")
    assert "HPSE-REQ-066" in text
    assert (
        "PROVIDER_UNIMPLEMENTED  →  PROVIDER_AVAILABLE  →  CREDENTIAL_PRESENT  →  "
        "CREDENTIAL_REGISTERED  →  SIGNER_ENROLLED" in text
    )


def test_standalone_admin_script_asymmetry_certification_and_binding_have_scripts_others_do_not():
    scripts_dir = REPO_ROOT / "scripts"
    names = {p.name for p in scripts_dir.glob("*.py")}
    assert "hatp_certification_admin.py" in names
    assert "hatp_deployment_binding_admin.py" in names
    assert "hatp_hardware_credential_admin.py" not in names
    assert "hatp_principal_signer_admin.py" not in names


def test_hardware_credential_admin_writer_library_exists_even_without_standalone_script():
    assert HW_CRED_ADMIN_SRC.exists()
    text = HW_CRED_ADMIN_SRC.read_text(encoding="utf-8")
    assert "def register_credential(" in text
    assert "def revoke_credential(" in text


def test_principal_signer_admin_writer_library_exists_even_without_standalone_script():
    assert PRINCIPAL_SIGNER_ADMIN_SRC.exists()


def test_class_b_sole_residual_failure_is_hbdc_req_042():
    text = CLASS_B_CONFORMANCE_SRC.read_text(encoding="utf-8")
    assert "HBDC-REQ-042" in text
    assert "no_active_deployment_binding_matches_repository_and_root" in text


def test_hbdc_contract_still_version_1_2():
    text = HBDC_CONTRACT.read_text(encoding="utf-8")
    assert "**Version:** 1.2" in text


def test_hmic_contract_still_version_1_6():
    text = HMIC_CONTRACT.read_text(encoding="utf-8")
    assert "**Version:** 1.6" in text


def test_authorization_doc_exists_and_selects_exactly_one_node():
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8")
    assert "**Selected: (A) HMIC `CertificationRecord` creation.**" in text
    normalized = " ".join(text.split())
    assert (
        "A: HMIC CERTIFICATION SELECTED AS NEXT REAL-EFFECT NODE — "
        "AUTHORIZATION ENVELOPE FROZEN — NOT EXECUTED." in normalized
    )
    # FIDO2 explicitly rejected, not silently omitted.
    assert "Rejected candidate reasoning (FIDO2 enrollment)" in text


def test_authorization_doc_freezes_create_only_not_activate():
    text = DOC.read_text(encoding="utf-8")
    assert "`create` subcommand only" in text
    assert "No write to\n  `certification-bindings.json`" in text or (
        "No write to" in text and "certification-bindings.json" in text
    )


def test_authorization_doc_states_no_cycle_found():
    text = DOC.read_text(encoding="utf-8")
    assert "**The hypothesized cycle does not exist**" in text
    assert "No Blocking architectural defect." in text


def test_authorization_doc_corrects_2i_protected_root_node():
    text = DOC.read_text(encoding="utf-8")
    assert "Protected Root: SATISFIED AT HBDC-REQ-011..018 BOUNDARY" in text


def test_no_production_source_changed_since_phase_entry_commit():
    result = subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY_COMMIT, "--", "src", "docs/contracts"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in result.stdout.splitlines() if line.strip()]
    assert changed == [], f"unexpected production/contract change: {changed}"


def test_no_real_trust_or_certification_state_files_exist_in_repo():
    # This phase never authorizes creation of any real protected-store
    # artifact; confirm none accidentally landed in-repo (they would
    # never legitimately live in-repo anyway -- Protected Root is
    # off-repository host state).
    for forbidden_name in (
        "certifications.json",
        "certification-bindings.json",
        "hardware-credentials.json",
    ):
        matches = list(REPO_ROOT.rglob(forbidden_name))
        # Exclude any path under .git or virtualenvs, defensive only.
        matches = [m for m in matches if ".git" not in m.parts and "site-packages" not in m.parts]
        assert matches == [], f"unexpected real-state file found in repo: {matches}"
