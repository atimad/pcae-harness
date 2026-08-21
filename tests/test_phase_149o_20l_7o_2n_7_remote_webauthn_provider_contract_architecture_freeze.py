"""Phase 149O.20L.7O.2N.7 -- Remote WebAuthn Provider Contract and Ceremony
Architecture Freeze. Disposable evidence tests: structural completeness of
the frozen HRWP-001 contract document, plus non-regression confirmation
that this documentation-only phase left the existing local FIDO2 provider
and its `provider_profile` constant byte-unchanged. No test touches real
hardware, a protected root, or performs any registry write.
"""
from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md"
_PHASE_REPORT_PATH = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2N_7_REMOTE_WEBAUTHN_PROVIDER_CONTRACT_AND_CEREMONY_ARCHITECTURE_FREEZE.md"
)


@pytest.fixture(scope="module")
def contract_text() -> str:
    assert _CONTRACT_PATH.is_file(), f"contract document missing: {_CONTRACT_PATH}"
    return _CONTRACT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def phase_report_text() -> str:
    assert _PHASE_REPORT_PATH.is_file(), f"phase report missing: {_PHASE_REPORT_PATH}"
    return _PHASE_REPORT_PATH.read_text(encoding="utf-8")


def test_contract_identity_frozen(contract_text: str) -> None:
    assert "**Contract:** HRWP-001" in contract_text
    assert "**Version:** 1.0" in contract_text
    assert "FROZEN" in contract_text


def test_contract_declares_no_implementation(contract_text: str) -> None:
    assert "NOT YET INDEPENDENTLY VERIFIED, NOT IMPLEMENTED" in contract_text
    assert "authorizes no implementation" in contract_text


def test_contract_defines_distinct_provider_profile(contract_text: str) -> None:
    assert "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN" in contract_text
    # Must be explicitly distinguished from the existing production profile,
    # not silently reused.
    assert "HRWP-REQ-007" in contract_text
    assert "distinct `provider_profile` value" in contract_text


def test_contract_covers_required_architecture_sections(contract_text: str) -> None:
    required_topics = [
        "## 3. Provider model",
        "## 4. `provider_profile` vocabulary",
        "## 5. Transport is not governance identity",
        "## 6. Multiple-credential model",
        "## 7. Credential selection policy",
        "## 8. Enrollment ceremony",
        "## 9. Pre-hardware governance ordering",
        "## 10. WebAuthn registration evidence mapping",
        "## 11. Attestation policy",
        "## 12. RP ID",
        "## 13. Origin model",
        "## 14. HTTPS / certificate requirement",
        "## 16. Server verification requirements",
        "## 17. User verification policy",
        "## 20. Session / challenge structure",
        "## 21. Challenge replay protection",
        "## 22. Session binding",
        "## 26. Assertion / signing",
        "## 27. WebAuthn assertion evidence mapping",
        "## 35. HSCE-001 relationship",
        "## 36. Future HMIC-001 consequence",
        "## 43. What this contract does NOT do",
    ]
    for topic in required_topics:
        assert topic in contract_text, f"missing required contract section: {topic!r}"


def test_contract_preserves_model_b_invariant(contract_text: str) -> None:
    assert "Registry resolves governance identity; hardware proves possession and signs" in contract_text
    assert "never governance identity" in contract_text


def test_contract_names_rp_id_as_open_infrastructure_requirement(contract_text: str) -> None:
    # Must not silently invent a literal hostname -- the contract must say
    # explicitly that no hostname has been provisioned/decided.
    assert "no PCAE-controlled domain, LAN name, or reverse-proxy hostname has been provisioned or decided" in contract_text
    assert "hatp.pcae.local" in contract_text  # existing constant discussed, not silently reused


def test_contract_rejects_unsafe_rp_id_forms(contract_text: str) -> None:
    assert "SHALL NOT be: `localhost`" in contract_text or "localhost" in contract_text
    assert "raw IP address" in contract_text
    assert "per-session" in contract_text


def test_contract_addresses_raw_ctap_vs_webauthn_semantic_gap_honestly(contract_text: str) -> None:
    # The core finding: the existing local provider already speaks the
    # WebAuthn assertion wire format; only origin/RP-ID enforcement differs.
    assert "authenticatorData || SHA-256(clientDataJSON)" in contract_text
    assert "origin/RP-ID enforcement" in contract_text
    assert "SUPPORTED VIA A NEW, PROVIDER-SPECIFIC ASSERTION PROFILE" in contract_text


def test_contract_does_not_claim_hsce_amended(contract_text: str) -> None:
    assert "This contract does NOT amend HSCE-001" in contract_text


def test_contract_requirement_count_matches_stated_total(contract_text: str) -> None:
    import re

    req_ids = re.findall(r"HRWP-REQ-(\d{3})", contract_text)
    assert req_ids, "no HRWP-REQ-### identifiers found"
    numbers = sorted(int(n) for n in set(req_ids))
    assert numbers[0] == 1
    assert numbers == list(range(1, numbers[-1] + 1)), "HRWP-REQ-### numbering has a gap"
    assert "68 normative requirements" in contract_text
    assert numbers[-1] == 68


def test_contract_no_go_list_matches_governing_no_go(contract_text: str) -> None:
    no_go_terms = [
        "creates no real WebAuthn credential",
        "invokes no `makeCredential`/`getAssertion` against real hardware",
        "modifies no HMIC-001 record",
        "performs no redeployment",
        "activates no HATP production state",
    ]
    for term in no_go_terms:
        assert term in contract_text, f"missing No-Go statement: {term!r}"


def test_phase_report_states_expected_verdict(phase_report_text: str) -> None:
    assert "REMOTE WEBAUTHN PROVIDER CONTRACT FROZEN" in phase_report_text
    assert "NO REAL CREDENTIAL CREATED" in phase_report_text
    assert "SUPPORTED VIA NEW PROVIDER-SPECIFIC ASSERTION PROFILE" in phase_report_text


def test_phase_report_confirms_no_production_source_touched(phase_report_text: str) -> None:
    assert "no path under `src/pcae/` or `scripts/` is modified" in phase_report_text


def test_phase_report_names_next_phase_as_independent_verification(phase_report_text: str) -> None:
    assert "independent verification of HRWP-001 before any implementation" in phase_report_text


def test_existing_local_fido2_provider_unchanged_by_this_phase() -> None:
    """Non-regression: this documentation-only phase must not have touched
    the production HATP FIDO2 provider module or its RP-ID/origin
    constants -- the exact source this phase's contract analysis depends
    on reading accurately."""

    from pcae.core import hatp_fido2_provider

    assert hatp_fido2_provider._HATP_RP_ID == "hatp.pcae.local"
    assert hatp_fido2_provider._HATP_ORIGIN == "pcae-hatp://hatp.pcae.local"
    assert hatp_fido2_provider.PROTOCOL_NAME == "FIDO2"


def test_existing_production_provider_profile_constant_unchanged_by_this_phase() -> None:
    """Non-regression: the shared `HATP_HARDWARE_PROVIDER_V1` constant this
    contract deliberately does NOT overload must remain exactly what it
    was before this phase."""

    from pcae.core import hatp_providers

    assert hatp_providers.HATP_HARDWARE_PROVIDER_V1 == "HATP_HARDWARE_PROVIDER_V1"
    assert hatp_providers._PRODUCTION_HARDWARE_PROVIDER_PROFILES == (hatp_providers.HATP_HARDWARE_PROVIDER_V1,)


def test_hardware_credential_record_schema_unchanged_by_this_phase() -> None:
    """Non-regression: HHCE-001's HardwareCredentialRecord field set must
    remain exactly what this contract claims it read and did not widen."""

    from pcae.core.hatp_hardware_credentials import HardwareCredentialRecord

    field_names = set(HardwareCredentialRecord.__dataclass_fields__.keys())
    assert field_names == {
        "signer_key_id",
        "provider_profile",
        "protocol_name",
        "algorithm",
        "public_key",
        "status",
        "revoked_at",
    }
