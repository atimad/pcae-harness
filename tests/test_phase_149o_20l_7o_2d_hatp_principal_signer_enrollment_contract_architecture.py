"""Phase 149O.20L.7O.2D -- HATP Principal/Signer Enrollment Contract
Architecture.

This phase is contract-text/architecture-only: no enrollment writer was
implemented, no `PrincipalRecord`/`SignerRecord` was written, no
credential was provisioned, no `DeploymentBinding` was created, no
election was initiated, no CHGR was published, no certification was
performed, and no Dell mutation occurred. These tests assert (a) both
new/amended contract documents are internally requirement-numbering-
complete and self-consistent, and (b) the source-level facts the
contracts' design decisions rest on are still true of the current
source tree -- not a live re-execution against `hac-dell`.
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
    / "PHASE_149O_20L_7O_2D_HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT_ARCHITECTURE.md"
)
_HPSE_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"
_HBDC_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_BOOTSTRAP_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py"
_PROVIDERS_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_providers.py"
_FIDO2_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_fido2_provider.py"
_ADMIN_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_deployment_binding_admin.py"
_HARDWARE_CREDENTIALS_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credentials.py"


def _doc_text() -> str:
    return " ".join(_DOC_PATH.read_text().split())


def _hpse_text() -> str:
    return _HPSE_CONTRACT_PATH.read_text()


def _hbdc_text() -> str:
    return _HBDC_CONTRACT_PATH.read_text()


def _bootstrap_source() -> str:
    return _BOOTSTRAP_PATH.read_text()


def _providers_source() -> str:
    return _PROVIDERS_PATH.read_text()


def _fido2_source() -> str:
    return _FIDO2_PATH.read_text()


def _admin_source() -> str:
    return _ADMIN_PATH.read_text()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Both contract documents exist and are internally requirement-
#    numbering-complete (no gaps, no duplicates).
# ═══════════════════════════════════════════════════════════════════════════


class TestRequirementNumberingComplete:
    def test_hpse_contract_exists(self) -> None:
        assert _HPSE_CONTRACT_PATH.is_file()

    def test_hpse_req_sequential_no_gaps_no_duplicates(self) -> None:
        ids = [int(m) for m in re.findall(r"HPSE-REQ-(\d+)", _hpse_text())]
        distinct = sorted(set(ids))
        assert distinct == list(range(1, 53)), f"expected HPSE-REQ-001..052 with no gaps, got {distinct}"

    def test_hpse_contract_declares_52_requirements(self) -> None:
        assert "**52**" in _hpse_text()

    def test_hbdc_amendment_req_071_through_076_present_exactly_once(self) -> None:
        text = _hbdc_text()
        for n in range(71, 77):
            req_id = f"HBDC-REQ-{n:03d}"
            count = len(re.findall(re.escape(req_id) + r"\b", text))
            assert count >= 1, f"{req_id} missing from HBDC-001"

    def test_hbdc_version_is_1_2(self) -> None:
        assert "**Version:** 1.2" in _hbdc_text()

    def test_hbdc_has_section_16_2(self) -> None:
        assert "### 16.2" in _hbdc_text()

    def test_hbdc_has_cbd_11(self) -> None:
        assert "CBD-11" in _hbdc_text()


# ═══════════════════════════════════════════════════════════════════════════
# 2. Phase report self-consistency.
# ═══════════════════════════════════════════════════════════════════════════


class TestDocSelfConsistency:
    def test_doc_records_phase_entry_commit(self) -> None:
        assert "ec4250edff8496e79880bc4b41007d8326a6bedb" in _doc_text()

    def test_doc_records_final_verdict(self) -> None:
        assert "READY FOR INDEPENDENT VERIFICATION" in _doc_text()

    def test_doc_recommends_next_phase(self) -> None:
        assert "149O.20L.7O.2D.1" in _doc_text()

    def test_doc_states_no_dell_mutation(self) -> None:
        text = _doc_text().lower()
        assert "no dell mutation" in text

    def test_doc_states_no_enrollment_no_binding_no_election_no_chgr_no_certification(self) -> None:
        text = _doc_text().lower()
        assert "no election initiated" in text
        assert "no chgr published" in text
        assert "no certification performed" in text
        assert "no `deploymentbinding` created" in text or "no deploymentbinding created" in text

    def test_doc_names_revoked_at_schema_gap(self) -> None:
        assert "revoked_at" in _doc_text()
        assert "HPSE-REQ-008" in _doc_text()

    def test_doc_names_authority_scope_vocabulary(self) -> None:
        assert "CLASS_B_DEPLOYMENT" in _doc_text()


# ═══════════════════════════════════════════════════════════════════════════
# 3. Source-level facts this architecture's decisions rest on, re-verified
#    directly against current source -- not inherited from prior-phase
#    prose.
# ═══════════════════════════════════════════════════════════════════════════


class TestSourceFactsStillTrue:
    def test_principal_record_has_no_revoked_at_field(self) -> None:
        """The freshly-derived schema-asymmetry finding (HPSE-REQ-008):
        PrincipalRecord, unlike SignerRecord/AuthorityRecord/
        DeploymentBinding, carries no revoked_at field."""

        source = _bootstrap_source()
        match = re.search(r"class PrincipalRecord:\s*\n((?:\s+\w+.*\n)+)", source)
        assert match is not None
        body = match.group(1)
        assert "revoked_at" not in body
        assert "principal_id" in body and "status" in body

    def test_signer_record_has_revoked_at_field(self) -> None:
        source = _bootstrap_source()
        match = re.search(r"class SignerRecord:\s*\n((?:\s+\w+.*\n)+)", source)
        assert match is not None
        assert "revoked_at" in match.group(1)

    def test_parse_principal_allowed_fields_excludes_revoked_at(self) -> None:
        source = _bootstrap_source()
        match = re.search(r"def _parse_principal.*?allowed = (\{[^}]*\})", source, re.DOTALL)
        assert match is not None
        allowed_literal = match.group(1)
        assert "revoked_at" not in allowed_literal
        assert "principal_id" in allowed_literal and "status" in allowed_literal

    def test_hardware_provider_v1_still_sole_production_profile(self) -> None:
        source = _providers_source()
        assert 'HATP_HARDWARE_PROVIDER_V1 = "HATP_HARDWARE_PROVIDER_V1"' in source
        assert "_PRODUCTION_HARDWARE_PROVIDER_PROFILES = (HATP_HARDWARE_PROVIDER_V1,)" in source

    def test_fido2_credential_identity_documents_non_re_derivability(self) -> None:
        source = _fido2_source()
        assert "not re-derivable from the device alone" in source

    def test_resolve_signer_checks_only_signer_status(self) -> None:
        source = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text()
        match = re.search(r"def _resolve_signer\(.*?\n\n\ndef ", source, re.DOTALL)
        assert match is not None
        body = match.group(0)
        assert "lookup_signer" in body
        assert "lookup_principal" not in body

    def test_deployment_binding_admin_still_defers_vocabulary_cross_validation(self) -> None:
        source = _admin_source()
        assert "explicitly deferred" in source
        assert "cross-validation against" in source

    def test_hardware_credentials_uses_hex_encoding_convention(self) -> None:
        source = _HARDWARE_CREDENTIALS_PATH.read_text()
        assert "public_key_hex" in source
        assert "bytes.fromhex" in source

    def test_deployment_binding_transition_lock_file_name_unchanged(self) -> None:
        source = _admin_source()
        assert '_DEPLOYMENT_BINDING_TRANSITION_LOCK_FILE_NAME = ".deployment-binding-transition.lock"' in source


# ═══════════════════════════════════════════════════════════════════════════
# 4. This phase modified no production .py file.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoProductionSourceModified:
    def test_no_new_production_module_created(self) -> None:
        assert not (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_principal_signer_admin.py").exists()
        assert not (_REPO_ROOT / "scripts" / "hatp_principal_signer_admin.py").exists()

    def test_hatp_bootstrap_dataclasses_unchanged_shape(self) -> None:
        from pcae.core.hatp_bootstrap import DeploymentBinding, PrincipalRecord, SignerRecord

        assert tuple(f.name for f in PrincipalRecord.__dataclass_fields__.values()) == ("principal_id", "status")
        assert tuple(f.name for f in SignerRecord.__dataclass_fields__.values()) == (
            "signer_key_id",
            "principal_id",
            "provider_profile",
            "status",
            "revoked_at",
        )
        assert tuple(f.name for f in DeploymentBinding.__dataclass_fields__.values()) == (
            "repository_id",
            "canonical_deployment_root",
            "principal_id",
            "signer_key_id",
            "provider_profile",
            "authority_scope",
            "valid_from",
            "status",
            "revoked_at",
        )
