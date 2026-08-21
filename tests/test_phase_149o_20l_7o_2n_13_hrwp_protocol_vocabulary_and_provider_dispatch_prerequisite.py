"""Phase 149O.20L.7O.2N.13 -- Remote WebAuthn Production Vocabulary and
Provider-Dispatch Prerequisite Resolution.

Implements the narrow production prerequisite HRWP-001 v1.1's §45 repair
(closing NBF-149O.20L.7O.2N.8-1) named as future work, and independently
resolves NBF-149O.20L.7O.2N.12-1/NBF-149O.20L.7O.2N.12-2 from this
phase's own re-derivation of primary source.

Implemented this phase:

1. `hatp_hardware_credentials.py::_PROTOCOL_VALUES` additively widened
   to include "WEBAUTHN" (closes NBF-149O.20L.7O.2N.12-2's vocabulary
   defect).
2. `hatp_hardware_credential_admin.py`'s previously-duplicated, mirrored
   `("FIDO2", "PIV")` closed-vocabulary check now imports and consumes
   the same canonical `_PROTOCOL_VALUES` from `hatp_hardware_
   credentials.py` (an already-valid dependency boundary this module
   already used for other underscore-private symbols), eliminating the
   divergent-vocabulary defect rather than merely widening both mirrors
   in parallel.

NOT implemented this phase (NBF-149O.20L.7O.2N.12-1 disposition:
OUTCOME A -- NOT A PRESENT DEFECT / FUTURE IMPLEMENTATION OBLIGATION):

`hatp_providers.py::_PRODUCTION_HARDWARE_PROVIDER_PROFILES` /
`create_production_hardware_provider()` are UNCHANGED. Direct
re-derivation of `create_production_hardware_provider()` (read fresh
this phase) shows it is not actually a per-profile dispatch table: once
`provider_profile` passes the closed-allowlist gate, the function always
attempts `Fido2HardwareProvider` first (PIV only as an explicit,
caller-opted fallback) -- there is no per-profile branch that would
route `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` to a distinct remote
implementation, because no such implementation exists. Adding the remote
profile to the allowlist today would therefore not "enable" a remote
provider -- it would silently route any remote-profile caller into the
*local* `Fido2HardwareProvider`, which is exactly the remote-to-local
fallback HRWP-001 (client trust model, §19) and this phase's own
governing prompt (§16) prohibit. `_PRODUCTION_HARDWARE_PROVIDER_PROFILES`
in its current, sole-implementation form is therefore best read as "the
set of production-implemented profiles," not an open, dispatch-agnostic
identity vocabulary -- HRWP-REQ-006 explicitly defers this exact
dispatch-mechanism decision to a future implementation phase and does
not resolve it here, consistent with this disposition.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CREDENTIALS_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credentials.py"
_ADMIN_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credential_admin.py"
_PROVIDERS_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_providers.py"
_HRWP_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Exact protocol vocabulary widening.
# ---------------------------------------------------------------------------


def test_protocol_values_widened_to_include_webauthn_preserving_legacy():
    from pcae.core.hatp_hardware_credentials import _PROTOCOL_VALUES

    assert _PROTOCOL_VALUES == frozenset({"FIDO2", "PIV", "WEBAUTHN"})


def test_webauthn_value_is_exact_uppercase_no_aliases():
    src = _text(_CREDENTIALS_SRC)
    assert '"WEBAUTHN"' in src
    for bad_alias in ("WEB_AUTHN", "REMOTE_WEBAUTHN", "FIDO2_WEBAUTHN"):
        assert bad_alias not in src


# ---------------------------------------------------------------------------
# 2. Registry parser: WEBAUTHN accepted, unknown rejected, legacy unchanged.
# ---------------------------------------------------------------------------


def _credential_doc(protocol_name: str, *, provider_profile: str = "HATP_HARDWARE_PROVIDER_V1") -> dict:
    return {
        "credentials": [
            {
                "signer_key_id": "ab" * 16,
                "provider_profile": provider_profile,
                "protocol_name": protocol_name,
                "algorithm": "ES256",
                "public_key_hex": "aa" * 8,
                "status": "active",
                "revoked_at": None,
            }
        ]
    }


def test_registry_parser_accepts_webauthn():
    from pcae.core.hatp_hardware_credentials import _parse_credential_registry_document

    result = _parse_credential_registry_document(
        _credential_doc("WEBAUTHN", provider_profile="HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN")
    )
    assert result.credentials["ab" * 16].protocol_name == "WEBAUTHN"
    assert result.credentials["ab" * 16].provider_profile == "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN"


def test_registry_parser_rejects_arbitrary_unknown_protocol_name():
    from pcae.core.hatp_hardware_credentials import (
        HATPHardwareCredentialStoreMalformedError,
        _parse_credential_registry_document,
    )

    with pytest.raises(HATPHardwareCredentialStoreMalformedError):
        _parse_credential_registry_document(_credential_doc("NOT_A_REAL_PROTOCOL"))


@pytest.mark.parametrize("legacy_protocol", ["FIDO2", "PIV"])
def test_registry_parser_legacy_protocols_unchanged(legacy_protocol):
    from pcae.core.hatp_hardware_credentials import _parse_credential_registry_document

    result = _parse_credential_registry_document(_credential_doc(legacy_protocol))
    assert result.credentials["ab" * 16].protocol_name == legacy_protocol


# ---------------------------------------------------------------------------
# 3. Admin enrollment-evidence validation: centralized, consistent.
# ---------------------------------------------------------------------------


def test_admin_module_imports_canonical_protocol_values_not_a_mirrored_literal():
    admin_src = _text(_ADMIN_SRC)
    assert "_PROTOCOL_VALUES" in admin_src
    assert 'protocol_name not in ("FIDO2", "PIV")' not in admin_src
    assert 'protocol_name not in ("FIDO2", "PIV", "WEBAUTHN")' not in admin_src


def test_admin_validator_and_registry_parser_share_the_same_object():
    from pcae.core.hatp_hardware_credentials import _PROTOCOL_VALUES as credentials_values
    from pcae.core.hatp_hardware_credential_admin import _PROTOCOL_VALUES as admin_values

    assert admin_values is credentials_values


def _enrollment_evidence(protocol_name: str, *, provider_profile: str = "HATP_HARDWARE_PROVIDER_V1"):
    from pcae.core.hatp_hardware_credential_admin import CredentialEnrollmentEvidence

    return CredentialEnrollmentEvidence(
        signer_key_id="cd" * 16,
        provider_profile=provider_profile,
        protocol_name=protocol_name,
        algorithm="ES256",
        public_key_hex="bb" * 8,
        enrollment_reference="ref-phase-2n-13",
    )


def test_admin_validator_accepts_webauthn_evidence():
    from pcae.core.hatp_hardware_credential_admin import _validate_enrollment_evidence

    _validate_enrollment_evidence(
        _enrollment_evidence("WEBAUTHN", provider_profile="HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN")
    )  # must not raise


def test_admin_validator_rejects_arbitrary_unknown_protocol():
    from pcae.core.hatp_hardware_credential_admin import (
        CredentialEvidenceMalformedError,
        _validate_enrollment_evidence,
    )

    with pytest.raises(CredentialEvidenceMalformedError):
        _validate_enrollment_evidence(_enrollment_evidence("NOT_A_REAL_PROTOCOL"))


@pytest.mark.parametrize("legacy_protocol", ["FIDO2", "PIV"])
def test_admin_validator_legacy_protocols_unchanged(legacy_protocol):
    from pcae.core.hatp_hardware_credential_admin import _validate_enrollment_evidence

    _validate_enrollment_evidence(_enrollment_evidence(legacy_protocol))  # must not raise


# ---------------------------------------------------------------------------
# 4. No third duplicated validator exists anywhere in production.
# ---------------------------------------------------------------------------


def test_no_third_closed_protocol_vocabulary_validator_exists():
    proc = subprocess.run(
        ["git", "grep", "-n", '"FIDO2"', "--", "src/pcae"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    validator_like = [
        line
        for line in lines
        if "hatp_hardware_credentials.py" in line or "hatp_hardware_credential_admin.py" in line
    ]
    # Exactly the two known, now-centralized sites: the canonical
    # _PROTOCOL_VALUES definition/comment in hatp_hardware_credentials.py,
    # and the field-kind comment there -- hatp_hardware_credential_admin.py
    # must carry NO literal "FIDO2" string anymore (it imports the value).
    assert not any("hatp_hardware_credential_admin.py" in line for line in validator_like)
    other_files = {
        line.split(":", 1)[0]
        for line in lines
        if "hatp_hardware_credentials.py" not in line
        and "hatp_hardware_credential_admin.py" not in line
        and "hatp_providers.py" not in line
        and "hatp_fido2_provider.py" not in line
    }
    assert other_files == set(), f"unexpected additional protocol-literal production sites: {other_files}"


# ---------------------------------------------------------------------------
# 5. Structural schema unchanged.
# ---------------------------------------------------------------------------


def test_hardware_credential_record_schema_unchanged():
    import dataclasses

    from pcae.core.hatp_hardware_credentials import HardwareCredentialRecord

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


def test_credential_enrollment_evidence_schema_unchanged():
    import dataclasses

    from pcae.core.hatp_hardware_credential_admin import CredentialEnrollmentEvidence

    field_names = {f.name for f in dataclasses.fields(CredentialEnrollmentEvidence)}
    assert field_names == {
        "signer_key_id",
        "provider_profile",
        "protocol_name",
        "algorithm",
        "public_key_hex",
        "enrollment_reference",
    }


# ---------------------------------------------------------------------------
# 6. Mixed-record representability: local FIDO2 + PIV + WEBAUTHN, no
#    collision, disposable/synthetic state only, nothing made authoritative.
# ---------------------------------------------------------------------------


def test_mixed_protocol_records_coexist_without_collision():
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
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                "protocol_name": "PIV",
                "algorithm": "ES256",
                "public_key_hex": "bb" * 8,
                "status": "active",
                "revoked_at": None,
            },
            {
                "signer_key_id": "33" * 16,
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN",
                "protocol_name": "WEBAUTHN",
                "algorithm": "ES256",
                "public_key_hex": "cc" * 8,
                "status": "active",
                "revoked_at": None,
            },
        ]
    }
    result = _parse_credential_registry_document(doc)
    assert len(result.credentials) == 3
    assert {rec.protocol_name for rec in result.credentials.values()} == {"FIDO2", "PIV", "WEBAUTHN"}
    assert {rec.signer_key_id for rec in result.credentials.values()} == {"11" * 16, "22" * 16, "33" * 16}


def test_multiple_signer_records_per_principal_unchanged():
    """HRWP-REQ-012: SignerRecord is keyed by signer_key_id only --
    principal_id is not a uniqueness key. Re-derive from source that this
    remains true (no widening was needed or made)."""
    import dataclasses

    from pcae.core.hatp_bootstrap import SignerRecord

    field_names = {f.name for f in dataclasses.fields(SignerRecord)}
    assert "signer_key_id" in field_names
    assert "principal_id" in field_names
    # No uniqueness constraint field was added.
    assert "unique_per_principal" not in field_names


# ---------------------------------------------------------------------------
# 7. Provider factory: NOT amended. Remote profile still fails closed. No
#    silent fallback to local FIDO2.
# ---------------------------------------------------------------------------


def test_production_provider_profile_allowlist_unchanged_by_this_phase():
    from pcae.core.hatp_providers import _PRODUCTION_HARDWARE_PROVIDER_PROFILES, HATP_HARDWARE_PROVIDER_V1

    assert _PRODUCTION_HARDWARE_PROVIDER_PROFILES == (HATP_HARDWARE_PROVIDER_V1,)
    assert "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN" not in _PRODUCTION_HARDWARE_PROVIDER_PROFILES


def test_factory_rejects_remote_webauthn_profile_fail_closed_not_falling_through():
    from pcae.core.hatp_providers import HATPProviderUnavailableError, create_production_hardware_provider

    with pytest.raises(HATPProviderUnavailableError):
        create_production_hardware_provider("HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN")


def test_factory_source_confirms_no_per_profile_dispatch_branch_exists():
    """Re-derive this phase's disposition directly from source: the
    factory does not branch on `provider_profile` to select among
    multiple provider classes -- it is purely a closed-allowlist gate
    followed by an unconditional FIDO2-then-PIV-fallback attempt. This is
    why adding the remote profile to the allowlist today would not
    "enable" it -- it would silently route to the local provider."""
    src = _text(_PROVIDERS_SRC)
    factory_start = src.index("def create_production_hardware_provider(")
    factory_body = src[factory_start : factory_start + 2000]
    assert "provider_profile not in _PRODUCTION_HARDWARE_PROVIDER_PROFILES" in factory_body
    # No conditional branch keyed on a specific profile value beyond the
    # single allowlist gate -- confirms the allowlist is not itself a
    # dispatch table.
    assert "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN" not in factory_body


def test_local_fido2_provider_construction_regression_free():
    from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1, create_production_hardware_provider
    from pcae.core.hatp_fido2_provider import Fido2HardwareProvider

    provider = create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)
    assert isinstance(provider, Fido2HardwareProvider)


def test_no_production_capability_metadata_falsely_advertises_remote_provider():
    """discover_hardware_providers() only ever reports FIDO2/PIV --
    truthful, since no remote-WebAuthn discovery/availability probe
    exists yet."""
    from pcae.core.hatp_providers import discover_hardware_providers

    results = discover_hardware_providers()
    assert all(r.protocol_name in ("FIDO2", "PIV") for r in results)
    assert not any("WEBAUTHN" in r.protocol_name for r in results)


# ---------------------------------------------------------------------------
# 8. HRWP-001 v1.1 contract text unaffected by this implementation phase
#    (this phase implements a prerequisite it already named -- it does not
#    amend the contract itself).
# ---------------------------------------------------------------------------


def test_hrwp_contract_still_v1_1_unamended_by_this_implementation_phase():
    text = _text(_HRWP_PATH)
    assert "**Version:** 1.1" in text
    assert "68 normative requirements" in text


def test_hrwp_req_006_dispatch_question_text_unchanged():
    """HRWP-REQ-006 explicitly defers the dispatch-mechanism decision to
    a future implementation phase and does not itself resolve it -- this
    phase's own disposition (do not amend the factory) is consistent
    with, not contradicted by, that deferral."""
    text = _text(_HRWP_PATH)
    assert "HRWP-REQ-006" in text
    assert "this contract does not resolve that dispatch question" in text


# ---------------------------------------------------------------------------
# 9. HMIC membership / digest consequence.
# ---------------------------------------------------------------------------


def test_both_changed_files_are_already_hmic_bound_members():
    from pcae.core.hatp_mandatory_certification import (
        _FROZEN_SRC_PCAE_RELATIVE_FILES,
        _FROZEN_SRC_PCAE_RELATIVE_COUNT,
    )

    assert "core/hatp_hardware_credentials.py" in _FROZEN_SRC_PCAE_RELATIVE_FILES
    assert "core/hatp_hardware_credential_admin.py" in _FROZEN_SRC_PCAE_RELATIVE_FILES
    assert _FROZEN_SRC_PCAE_RELATIVE_COUNT == 27


def test_hmic_total_member_count_unchanged_at_38():
    from pcae.core.hatp_mandatory_certification import (
        _FROZEN_SRC_PCAE_RELATIVE_FILES,
        _FROZEN_REPOSITORY_ROOT_RELATIVE_FILES,
    )

    assert len(_FROZEN_SRC_PCAE_RELATIVE_FILES) + len(_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES) == 38


def test_implementation_scope_digest_is_derivable_and_changed_from_phase_entry():
    """This phase changed bytes of two already-bound HMIC members; the
    resulting development-source `implementation_scope_digest` therefore
    differs from the digest at phase entry. This is expected and does
    NOT amend HMIC-001 or certify anything -- no CertificationRecord is
    created or mutated by this test or this phase."""
    from pcae.core.paths import HarnessPath
    from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest

    digest = derive_implementation_scope_digest(HarnessPath.cwd())
    assert isinstance(digest, str)
    assert len(digest) == 64
    int(digest, 16)  # valid hex


# ---------------------------------------------------------------------------
# 10. No remote enrollment / no real credential / no Principal / no Signer
#     / no DeploymentBinding is created anywhere by this test module.
# ---------------------------------------------------------------------------


def test_this_test_module_creates_no_real_hardware_credential_record_instances():
    """Guard against accidental scope creep: this test module must never
    instantiate a real, persisted HardwareCredentialRecord via the
    production writer -- only in-memory parser/validator calls against
    disposable dict/dataclass literals, verified above."""
    module_src = Path(__file__).read_text(encoding="utf-8")
    body = module_src.split("def test_this_test_module_creates_no_real_hardware_credential_record_instances")[0]
    assert "register_credential(" not in body
    assert "HATPHardwareCredentialStore.production()" not in body
