"""Phase 149O.20L.7O.2N.12 -- Independent Verification of Phase 149O.20L.7O.2N.11's
HRWP-001 v1.1 protocol_name Closed-Vocabulary Contract Clarification.

Independently re-derives NBF-149O.20L.7O.2N.8-1's disposition from primary
source and the fixed pre-2N.11 historical checkpoint (commit e7451333),
rather than trusting 2N.11's report/tests/comments. Fresh test suite, not
copied from 2N.11's own test file.

VERIFICATION ONLY. No production change. No implementation.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HRWP_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md"
_HRAC_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md"
_HHCE_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"
_HSCE_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"
_CREDENTIALS_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credentials.py"
_ADMIN_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credential_admin.py"
_PROVIDERS_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_providers.py"

_PHASE_ENTRY_COMMIT = "e7451333"  # 149O.20L.7O.2N.10's canonical-sync commit, immediately pre-2N.11


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _git_show(rev: str, path: str) -> str:
    out = subprocess.run(
        ["git", "show", f"{rev}:{path}"], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    )
    return out.stdout


# ---------------------------------------------------------------------------
# 1. Fixed historical checkpoint (pre-2N.11): reproduce the original
#    contradiction independently.
# ---------------------------------------------------------------------------


def test_pre_2n11_checkpoint_hrwp_was_v1_0_with_inaccurate_no_schema_widening_claim():
    old_text = _git_show(_PHASE_ENTRY_COMMIT, "docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md")
    assert "**Version:** 1.0" in old_text
    match = re.search(r"\*\*HRWP-REQ-019\.\*\*(.*?)(?=\n\n\*\*HRWP-REQ-020)", old_text, re.DOTALL)
    assert match is not None
    assert "requiring no schema widening" in match.group(1)


def test_pre_2n11_checkpoint_production_protocol_values_already_closed():
    old_src = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_hardware_credentials.py")
    assert 'frozenset({"FIDO2", "PIV"})' in old_src
    assert "not in _PROTOCOL_VALUES" in old_src
    assert "WEBAUTHN" not in old_src


# ---------------------------------------------------------------------------
# 2. Current contract checkpoint: version, requirement identity/numbering.
# ---------------------------------------------------------------------------


def test_current_hrwp_version_is_1_1_and_status_reflects_repair():
    text = _text(_HRWP_PATH)
    assert "**Version:** 1.1" in text
    assert "CONTRACT REPAIRED" in text


def test_current_hrwp_requirement_numbering_sequential_no_gap_no_duplicate():
    text = _text(_HRWP_PATH)
    numbers = [int(n) for n in re.findall(r"\*\*HRWP-REQ-(\d+)", text)]
    assert sorted(numbers) == list(range(1, 69))
    assert len(numbers) == len(set(numbers))
    assert "**HRWP-REQ-019 (revised, v1.1" in text


# ---------------------------------------------------------------------------
# 3. Primary production source: exact current _PROTOCOL_VALUES.
# ---------------------------------------------------------------------------


def test_current_protocol_values_exact_set():
    from pcae.core.hatp_hardware_credentials import _PROTOCOL_VALUES

    assert _PROTOCOL_VALUES == frozenset({"FIDO2", "PIV"})
    assert "WEBAUTHN" not in _PROTOCOL_VALUES


# ---------------------------------------------------------------------------
# 4. Mechanical fail-closed proof: unknown protocol_name rejected.
# ---------------------------------------------------------------------------


def test_unknown_protocol_name_mechanically_rejected_by_registry_parser():
    from pcae.core.hatp_hardware_credentials import (
        HATPHardwareCredentialStoreMalformedError,
        _parse_credential_registry_document,
    )

    doc = {
        "credentials": [
            {
                "signer_key_id": "ab" * 16,
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN",
                "protocol_name": "WEBAUTHN",
                "algorithm": "ES256",
                "public_key_hex": "aa" * 8,
                "status": "active",
                "revoked_at": None,
            }
        ]
    }
    with pytest.raises(HATPHardwareCredentialStoreMalformedError):
        _parse_credential_registry_document(doc)


def test_known_protocol_names_still_accepted_by_registry_parser():
    from pcae.core.hatp_hardware_credentials import _parse_credential_registry_document

    for known in ("FIDO2", "PIV"):
        doc = {
            "credentials": [
                {
                    "signer_key_id": "ab" * 16,
                    "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                    "protocol_name": known,
                    "algorithm": "ES256",
                    "public_key_hex": "aa" * 8,
                    "status": "active",
                    "revoked_at": None,
                }
            ]
        }
        result = _parse_credential_registry_document(doc)
        assert result.credentials["ab" * 16].protocol_name == known


# ---------------------------------------------------------------------------
# 5. Structural schema re-derivation: no new field required.
# ---------------------------------------------------------------------------


def test_hardware_credential_record_structural_fields_unchanged():
    from pcae.core.hatp_hardware_credentials import HardwareCredentialRecord
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(HardwareCredentialRecord)}
    assert field_names == {
        "signer_key_id",
        "provider_profile",
        "protocol_name",
        "algorithm",
        "public_key",
        "status",
        "revoked_at",
    }


# ---------------------------------------------------------------------------
# 6. HRWP-REQ-019 text distinguishes structural schema vs closed vocabulary.
# ---------------------------------------------------------------------------


def test_hrwp_req_019_distinguishes_structural_schema_from_closed_vocabulary():
    text = _text(_HRWP_PATH)
    match = re.search(r"\*\*HRWP-REQ-019 \(revised.*?\*\*(.*?)(?=\n\n\*\*HRWP-REQ-020)", text, re.DOTALL)
    assert match is not None
    body = match.group(1)
    assert "structural schema widening" in body
    assert "closed-vocabulary widening" in body
    assert "_PROTOCOL_VALUES" in body
    assert "fail-closed" not in body.lower() or "rejected" in body  # rejection semantics present


def test_hrwp_req_019_names_exact_future_value_webauthn_uppercase():
    text = _text(_HRWP_PATH)
    match = re.search(r"\*\*HRWP-REQ-019 \(revised.*?\*\*(.*?)(?=\n\n\*\*HRWP-REQ-020)", text, re.DOTALL)
    assert match is not None
    assert '`"WEBAUTHN"`' in match.group(1)


# ---------------------------------------------------------------------------
# 7. Fail-closed requirement not weakened to open string.
# ---------------------------------------------------------------------------


def test_hrwp_req_019_does_not_recommend_open_string_relaxation():
    text = _text(_HRWP_PATH)
    match = re.search(r"\*\*HRWP-REQ-019 \(revised.*?\*\*(.*?)(?=\n\n\*\*HRWP-REQ-020)", text, re.DOTALL)
    assert match is not None
    assert "SHALL NOT be relaxed to an open string" in match.group(1)


# ---------------------------------------------------------------------------
# 8. protocol_name vs provider_profile semantics not conflated.
# ---------------------------------------------------------------------------


def test_protocol_name_and_provider_profile_are_distinct_fields_in_source():
    import dataclasses
    from pcae.core.hatp_hardware_credentials import HardwareCredentialRecord

    names = {f.name for f in dataclasses.fields(HardwareCredentialRecord)}
    assert {"protocol_name", "provider_profile"} <= names
    # distinct requirement text in contract
    text = _text(_HRWP_PATH)
    assert "HRWP-REQ-007" in text and "HRWP-REQ-019" in text


# ---------------------------------------------------------------------------
# 9. provider_profile production vocabulary -- also closed, separately gated.
#    (New finding candidate: §45's implementation-prerequisite list only
#    names _PROTOCOL_VALUES, not this factory-level closed allowlist.)
# ---------------------------------------------------------------------------


def test_provider_profile_factory_allowlist_is_also_closed_and_excludes_remote_webauthn():
    from pcae.core.hatp_providers import (
        _PRODUCTION_HARDWARE_PROVIDER_PROFILES,
        HATP_HARDWARE_PROVIDER_V1,
    )

    assert _PRODUCTION_HARDWARE_PROVIDER_PROFILES == (HATP_HARDWARE_PROVIDER_V1,)
    assert "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN" not in _PRODUCTION_HARDWARE_PROVIDER_PROFILES


def test_create_production_hardware_provider_rejects_remote_webauthn_profile_today():
    from pcae.core.hatp_providers import (
        create_production_hardware_provider,
        HATPProviderUnavailableError,
    )

    with pytest.raises(HATPProviderUnavailableError):
        create_production_hardware_provider("HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN")


def test_hardware_credential_record_own_provider_profile_field_is_not_closed_at_parse_time():
    # provider_profile at the registry-parser level is only validated as a
    # non-empty string -- the closed check lives in the factory, not the
    # record parser. This confirms the closed-vocabulary gate for
    # provider_profile is enforced at a *different* layer than protocol_name's.
    from pcae.core.hatp_hardware_credentials import _parse_credential_registry_document

    doc = {
        "credentials": [
            {
                "signer_key_id": "cd" * 16,
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN",
                "protocol_name": "FIDO2",
                "algorithm": "ES256",
                "public_key_hex": "bb" * 8,
                "status": "active",
                "revoked_at": None,
            }
        ]
    }
    result = _parse_credential_registry_document(doc)
    assert result.credentials["cd" * 16].provider_profile == "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN"


# ---------------------------------------------------------------------------
# 10. Duplicated-vocabulary search: a second, independent closed check.
#     (New finding candidate: hatp_hardware_credential_admin.py has its own
#     hardcoded ("FIDO2", "PIV") tuple, not named by §45's repair scope.)
# ---------------------------------------------------------------------------


def test_duplicated_closed_protocol_vocabulary_exists_in_admin_enrollment_path():
    admin_src = _text(_ADMIN_SRC)
    assert 'protocol_name not in ("FIDO2", "PIV")' in admin_src


def test_admin_enrollment_validator_rejects_webauthn_protocol_name_today():
    from pcae.core.hatp_hardware_credential_admin import (
        CredentialEnrollmentEvidence,
        _validate_enrollment_evidence,
        CredentialEvidenceMalformedError,
    )

    evidence = CredentialEnrollmentEvidence(
        signer_key_id="ef" * 16,
        provider_profile="HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN",
        protocol_name="WEBAUTHN",
        algorithm="ES256",
        public_key_hex="cc" * 8,
        enrollment_reference="ref-1",
    )
    with pytest.raises(CredentialEvidenceMalformedError):
        _validate_enrollment_evidence(evidence)


# ---------------------------------------------------------------------------
# 11. No production change since phase entry (raw git diff, not report).
# ---------------------------------------------------------------------------


def test_no_production_source_change_since_phase_entry():
    diff = subprocess.run(
        ["git", "diff", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", "src/pcae", "scripts"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert diff == ""


def test_downstream_contracts_unchanged_since_phase_entry():
    diff = subprocess.run(
        [
            "git",
            "diff",
            f"{_PHASE_ENTRY_COMMIT}..HEAD",
            "--",
            "docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md",
            "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
            "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert diff == ""


# ---------------------------------------------------------------------------
# 12. Historical record compatibility: existing values remain valid.
# ---------------------------------------------------------------------------


def test_existing_protocol_values_remain_valid_conceptually_pre_widening():
    from pcae.core.hatp_hardware_credentials import _PROTOCOL_VALUES

    assert {"FIDO2", "PIV"} <= _PROTOCOL_VALUES


# ---------------------------------------------------------------------------
# 13. Mixed local/remote representability at the schema level (no field
#     collision, no singleton assumption) -- exercised via the registry
#     parser accepting two distinct records under one document.
# ---------------------------------------------------------------------------


def test_registry_parser_supports_multiple_simultaneous_records_no_collision():
    from pcae.core.hatp_hardware_credentials import _parse_credential_registry_document

    doc = {
        "credentials": [
            {
                "signer_key_id": "11" * 16,
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                "protocol_name": "FIDO2",
                "algorithm": "ES256",
                "public_key_hex": "aa" * 8,
                "status": "active",
                "revoked_at": None,
            },
            {
                "signer_key_id": "22" * 16,
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN",
                "protocol_name": "PIV",  # placeholder known value; WEBAUTHN not yet acceptable
                "algorithm": "ES256",
                "public_key_hex": "bb" * 8,
                "status": "active",
                "revoked_at": None,
            },
        ]
    }
    result = _parse_credential_registry_document(doc)
    assert len(result.credentials) == 2
    assert result.credentials["11" * 16].signer_key_id != result.credentials["22" * 16].signer_key_id


# ---------------------------------------------------------------------------
# 14. Stale-current-text sweep: no current normative "no schema/vocabulary
#     change" claim outside the historical §45 narrative.
# ---------------------------------------------------------------------------


def test_no_stale_current_normative_no_vocabulary_change_claim():
    text = _text(_HRWP_PATH)
    # Split off §45's historical narrative (explicitly describing the v1.0
    # error) -- everything before it must not contain the retracted claim.
    pre_repair_text = text.split("## 45. v1.1 Repair")[0]
    assert "requiring no schema widening" not in pre_repair_text


def test_hrac_001_protocol_name_reference_remains_accurate_and_carried_forward():
    text = _text(_HRAC_PATH)
    assert "carried forward" in text.lower() or "not resolved" in text.lower() or "does not depend on that finding" in text


# ---------------------------------------------------------------------------
# 15. HRWP version-history distinguishes v1.0 historical vs v1.1 corrected.
# ---------------------------------------------------------------------------


def test_version_history_distinguishes_v1_0_from_v1_1():
    text = _text(_HRWP_PATH)
    section_45 = text.split("## 45. v1.1 Repair")[1].split("## 44. Requirement count")[0]
    assert "v1.0 text asserted" in section_45 or "v1.0's text" in section_45
    assert "Version consequence" in section_45
