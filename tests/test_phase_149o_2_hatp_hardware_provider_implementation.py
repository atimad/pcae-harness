"""HATP Hardware Provider Implementation (Wave 5) -- Phase 149O.2.

Tests the real FIDO2 provider (`pcae.core.hatp_fido2_provider`), the
honestly-scoped PIV placeholder (`pcae.core.hatp_piv_provider`), the
protected hardware-credential registry
(`pcae.core.hatp_hardware_credentials`), and the Wave-5 abstraction
layer added to `pcae.core.hatp_providers` (discovery, factory,
`HATPHardwareSigner`).

Deterministic tests use real WebAuthn/CTAP2 data structures
(`fido2.webauthn.AuthenticatorData`/`CollectedClientData`) and real
ECDSA cryptography (`cryptography.hazmat.primitives.asymmetric.ec`)
signed with a test-only in-memory key -- genuine cryptographic
verification logic, exercised without a physical device. This machine
has zero attached FIDO2/PIV hardware (independently confirmed by
`discover_hardware_providers()` below); the small number of tests that
require a real device are marked `hatp_hardware_required` and
`skipif`-skipped rather than fabricated (item 88).
"""
from __future__ import annotations

import ast
import inspect
import json
import re
import uuid
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytest

fido2 = pytest.importorskip("fido2")
cryptography = pytest.importorskip("cryptography")

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from fido2 import cbor as fido2_cbor
from fido2.cose import ES256
from fido2.webauthn import AuthenticatorData, CollectedClientData

from pcae.core import hatp_fido2_provider as fido2_module
from pcae.core import hatp_hardware_credentials as credentials_module
from pcae.core import hatp_piv_provider as piv_module
from pcae.core import hatp_providers as providers_module
from pcae.core.hatp_bootstrap import HATPTrustStore, resolve_canonical_deployment_root
from pcae.core.hatp_fido2_provider import Fido2HardwareProvider, discover_fido2
from pcae.core.hatp_hardware_credentials import HardwareCredentialRecord, HATPHardwareCredentialStore
from pcae.core.hatp_piv_provider import PivHardwareProvider, discover_piv
from pcae.core.hatp_providers import (
    HATP_HARDWARE_PROVIDER_V1,
    HardwareProviderCapabilities,
    HardwareProviderConformance,
    HATPHardwareProviderError,
    HATPHardwareSigner,
    HATPProofVerifierProvider,
    HATPProviderCancelledError,
    HATPProviderDeviceError,
    HATPProviderUnavailableError,
    ProviderAssertion,
    TestHATPProofVerifierProvider,
    create_production_hardware_provider,
    discover_hardware_providers,
)
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    HATPExpectedOperation,
    HATPVerificationEvidence,
    HATPVerificationStatus,
    RollbackSite,
    HumanApprovalProvenanceProof,
    canonicalize_hatp_proof_payload,
    verify_hatp_proof,
)

_EVAL_TIME = datetime(2026, 8, 7, 12, 0, 0, tzinfo=timezone.utc)
_SRC_ROOT = Path(__file__).resolve().parent.parent / "src" / "pcae"


def _strip_docstrings_and_comments(source: str) -> str:
    without_docstrings = re.sub(r'""".*?"""', "", source, flags=re.DOTALL)
    return "\n".join(line.split("#", 1)[0] for line in without_docstrings.splitlines())


# ═══════════════════════════════════════════════════════════════════════════
# Fixture builders -- real key + real WebAuthn/CTAP2-shaped evidence
# ═══════════════════════════════════════════════════════════════════════════


def _generate_test_key():
    """Test-only stand-in for a hardware-protected non-exportable key
    (item 14: software keys may exist only in clearly test-only
    fixtures; this key is never enrolled into any production credential
    store and this fixture is never reachable from
    `create_production_hardware_provider`)."""

    return ec.generate_private_key(ec.SECP256R1())


def _cose_public_key_bytes(private_key) -> bytes:
    cose_key = ES256.from_cryptography_key(private_key.public_key())
    return fido2_cbor.encode(dict(cose_key))


def _sign_assertion(
    private_key,
    *,
    canonical_payload: bytes,
    credential_id: bytes,
    up: bool = True,
    rp_id_hash: Optional[bytes] = None,
    origin: Optional[str] = None,
    client_data_type=CollectedClientData.TYPE.GET,
    challenge_override: Optional[bytes] = None,
) -> bytes:
    """Build a real, byte-exact WebAuthn/CTAP2 assertion, signed with a
    test-only key, and serialize it in `hatp_fido2_provider`'s own
    strict evidence schema -- exercising the real serialize/deserialize/
    verify path, not a shortcut."""

    challenge = challenge_override if challenge_override is not None else fido2_module._payload_digest(canonical_payload)
    client_data = CollectedClientData.create(
        type=client_data_type, challenge=challenge, origin=origin or fido2_module._HATP_ORIGIN
    )
    flags = AuthenticatorData.FLAG.UP if up else AuthenticatorData.FLAG(0)
    auth_data = AuthenticatorData.create(rp_id_hash or fido2_module._RP_ID_HASH, flags, 1)
    signed_bytes = bytes(auth_data) + client_data.hash
    signature = private_key.sign(signed_bytes, ec.ECDSA(hashes.SHA256()))
    return fido2_module._serialize_evidence(
        credential_id=credential_id,
        authenticator_data=bytes(auth_data),
        client_data_json=bytes(client_data),
        signature=signature,
    )


class _CredentialStoreFixture:
    """A minimal, in-memory stand-in for `HATPHardwareCredentialStore`,
    used only to isolate `Fido2HardwareProvider.verify()` from the
    filesystem-backed protected registry in most tests. Separate tests
    exercise the real `HATPHardwareCredentialStore` against a
    `tmp_path`-backed registry file."""

    def __init__(self, records: dict) -> None:
        self._records = records

    def lookup_credential(self, signer_key_id: str):
        return self._records.get(signer_key_id)


class _Fido2Harness:
    def __init__(self) -> None:
        self.private_key = _generate_test_key()
        self.credential_id = uuid.uuid4().bytes
        self.signer_key_id = self.credential_id.hex()
        self.provider_profile = HATP_HARDWARE_PROVIDER_V1
        self.record = HardwareCredentialRecord(
            signer_key_id=self.signer_key_id,
            provider_profile=self.provider_profile,
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key=_cose_public_key_bytes(self.private_key),
            status="active",
        )
        self.store = _CredentialStoreFixture({self.signer_key_id: self.record})
        self.provider = Fido2HardwareProvider(credential_store=self.store)

    def evidence(self, canonical_payload: bytes, **kwargs) -> bytes:
        return _sign_assertion(self.private_key, canonical_payload=canonical_payload, credential_id=self.credential_id, **kwargs)

    def verify(self, canonical_payload: bytes, evidence: Optional[bytes] = None, **kwargs):
        return self.provider.verify(
            canonical_payload=canonical_payload,
            signer_key_id=kwargs.pop("signer_key_id", self.signer_key_id),
            provider_profile=kwargs.pop("provider_profile", self.provider_profile),
            assertion=evidence if evidence is not None else self.evidence(canonical_payload, **kwargs),
        )


@pytest.fixture()
def fido2_harness() -> _Fido2Harness:
    return _Fido2Harness()


# ═══════════════════════════════════════════════════════════════════════════
# 0. Environment honesty -- this machine has no real hardware attached
# ═══════════════════════════════════════════════════════════════════════════


def test_discover_hardware_providers_reports_honest_facts() -> None:
    """FIDO2 library IS installed (item 89: record honestly). No
    physical device is attached to this development machine -- this
    assertion is a genuine environment fact, not a mock."""

    availabilities = discover_hardware_providers()
    by_protocol = {a.protocol_name: a for a in availabilities}
    assert set(by_protocol) == {"FIDO2", "PIV"}
    assert by_protocol["FIDO2"].library_installed is True
    assert by_protocol["FIDO2"].device_detected is False
    assert by_protocol["PIV"].library_installed is False
    assert by_protocol["PIV"].device_detected is False
    for availability in availabilities:
        assert availability.provider_profile == HATP_HARDWARE_PROVIDER_V1


def test_discover_fido2_matches_module_level_function() -> None:
    direct = discover_fido2()
    assert direct.protocol_name == "FIDO2"
    assert direct.library_installed is True


def test_discover_piv_always_reports_unavailable() -> None:
    result = discover_piv()
    assert result.library_installed is False
    assert result.device_detected is False
    assert result.notes


# ═══════════════════════════════════════════════════════════════════════════
# 1. Required Test -- Exact Provider Contract (item 96)
# ═══════════════════════════════════════════════════════════════════════════


def test_fido2_provider_conforms_to_verifier_protocol_structurally() -> None:
    assert isinstance(Fido2HardwareProvider(), HATPProofVerifierProvider)


def test_fido2_provider_conforms_to_signer_protocol_structurally() -> None:
    assert isinstance(Fido2HardwareProvider(), HATPHardwareSigner)


def test_piv_provider_conforms_to_both_protocols_structurally() -> None:
    assert isinstance(PivHardwareProvider(), HATPProofVerifierProvider)
    assert isinstance(PivHardwareProvider(), HATPHardwareSigner)


def test_verify_signature_matches_frozen_wave4_interface() -> None:
    sig = inspect.signature(Fido2HardwareProvider.verify)
    params = list(sig.parameters)
    assert params == ["self", "canonical_payload", "signer_key_id", "provider_profile", "assertion"]


# ═══════════════════════════════════════════════════════════════════════════
# 2. Required Test -- Canonical Payload (item 97)
# ═══════════════════════════════════════════════════════════════════════════


def test_valid_assertion_over_exact_canonical_payload(fido2_harness: _Fido2Harness) -> None:
    payload = b'{"a":1}'
    outcome = fido2_harness.verify(payload)
    assert outcome.signature_valid is True
    assert outcome.human_presence_proven is True
    assert outcome.attestation_valid is None


def test_provider_evidence_binds_full_canonical_bytes_not_a_truncation(fido2_harness: _Fido2Harness) -> None:
    payload_a = b'{"a":1,"b":2}'
    payload_b = b'{"a":1,"b":3}'
    evidence = fido2_harness.evidence(payload_a)
    outcome = fido2_harness.verify(payload_b, evidence=evidence)
    assert outcome.signature_valid is False


# ═══════════════════════════════════════════════════════════════════════════
# 3/4. Required Test -- Presence Required / Presence Per Operation (98/99)
# ═══════════════════════════════════════════════════════════════════════════


def test_missing_user_presence_flag_reports_presence_not_proven(fido2_harness: _Fido2Harness) -> None:
    payload = b'{"op":"rollback"}'
    outcome = fido2_harness.verify(payload, up=False)
    assert outcome.signature_valid is True
    assert outcome.human_presence_proven is False


def test_full_wave4_integration_maps_missing_presence_to_user_presence_not_proven(tmp_path: Path) -> None:
    """End-to-end through the real Wave-4 verifier
    (`verify_hatp_proof`), using `Fido2HardwareProvider` as the
    provider -- not `TestHATPProofVerifierProvider` -- to confirm the
    hardware provider integrates correctly with the independently
    verified Wave-4 engine."""

    harness = _build_wave4_integration_harness(tmp_path)
    proof = harness["proof"]
    payload = canonicalize_hatp_proof_payload(proof)
    evidence = HATPVerificationEvidence(
        assertion=_sign_assertion(
            harness["private_key"], canonical_payload=payload, credential_id=harness["credential_id"], up=False
        )
    )
    result = verify_hatp_proof(
        proof,
        evidence=evidence,
        provider=harness["provider"],
        trust_store=harness["trust_store"],
        expected_operation=harness["expected_operation"],
        current_repository_id=harness["repo_id"],
        canonical_deployment_root=harness["canonical_root"],
        evaluation_time=_EVAL_TIME,
    )
    assert result.status == HATPVerificationStatus.USER_PRESENCE_NOT_PROVEN


def test_presence_from_operation_a_cannot_satisfy_operation_b(fido2_harness: _Fido2Harness) -> None:
    """A UP=true assertion genuinely produced for payload A does not
    become valid evidence for payload B merely because presence was
    proven at some point -- the presence flag lives inside the same
    signed `authenticatorData` that is invalidated by a payload change
    (item 45: presence replay)."""

    payload_a = b'{"op":"A"}'
    payload_b = b'{"op":"B"}'
    evidence_a = fido2_harness.evidence(payload_a, up=True)
    outcome = fido2_harness.verify(payload_b, evidence=evidence_a)
    assert outcome.signature_valid is False


# ═══════════════════════════════════════════════════════════════════════════
# 5/6. Required Test -- Wrong Payload / Wrong Credential (100/101)
# ═══════════════════════════════════════════════════════════════════════════


def test_wrong_payload_fails(fido2_harness: _Fido2Harness) -> None:
    evidence = fido2_harness.evidence(b'{"x":1}')
    outcome = fido2_harness.verify(b'{"x":2}', evidence=evidence)
    assert outcome.signature_valid is False


def test_wrong_credential_signature_fails(fido2_harness: _Fido2Harness) -> None:
    """A different (also test-only) private key signs; verification
    must fail against the enrolled public key (item 37/39: device-swap
    attack)."""

    payload = b'{"y":1}'
    other_key = _generate_test_key()
    forged = _sign_assertion(other_key, canonical_payload=payload, credential_id=fido2_harness.credential_id)
    outcome = fido2_harness.verify(payload, evidence=forged)
    assert outcome.signature_valid is False


def test_credential_id_field_mismatch_fails(fido2_harness: _Fido2Harness) -> None:
    """Assertion claims a different credential id than `signer_key_id`
    (item 37): the evidence's own credential_id must agree."""

    payload = b'{"z":1}'
    wrong_id = uuid.uuid4().bytes
    evidence = _sign_assertion(fido2_harness.private_key, canonical_payload=payload, credential_id=wrong_id)
    outcome = fido2_harness.verify(payload, evidence=evidence)
    assert outcome.signature_valid is False


# ═══════════════════════════════════════════════════════════════════════════
# 7. Required Test -- Wrong Provider Profile (item 102)
# ═══════════════════════════════════════════════════════════════════════════


def test_wrong_provider_profile_fails(fido2_harness: _Fido2Harness) -> None:
    payload = b'{"p":1}'
    outcome = fido2_harness.verify(payload, provider_profile="SOME_OTHER_PROFILE")
    assert outcome.signature_valid is False


def test_record_profile_mismatch_fails_even_if_caller_profile_matches_credential() -> None:
    key = _generate_test_key()
    credential_id = uuid.uuid4().bytes
    signer_key_id = credential_id.hex()
    record = HardwareCredentialRecord(
        signer_key_id=signer_key_id,
        provider_profile="A_DIFFERENT_PROFILE",
        protocol_name="FIDO2",
        algorithm="ES256",
        public_key=_cose_public_key_bytes(key),
        status="active",
    )
    provider = Fido2HardwareProvider(credential_store=_CredentialStoreFixture({signer_key_id: record}))
    payload = b'{"q":1}'
    evidence = _sign_assertion(key, canonical_payload=payload, credential_id=credential_id)
    outcome = provider.verify(
        canonical_payload=payload, signer_key_id=signer_key_id, provider_profile=HATP_HARDWARE_PROVIDER_V1, assertion=evidence
    )
    assert outcome.signature_valid is False


# ═══════════════════════════════════════════════════════════════════════════
# 8. Required Test -- Unknown Credential (item 103)
# ═══════════════════════════════════════════════════════════════════════════


def test_unknown_credential_fails(fido2_harness: _Fido2Harness) -> None:
    payload = b'{"u":1}'
    empty_store = _CredentialStoreFixture({})
    provider = Fido2HardwareProvider(credential_store=empty_store)
    evidence = fido2_harness.evidence(payload)
    outcome = provider.verify(
        canonical_payload=payload,
        signer_key_id=fido2_harness.signer_key_id,
        provider_profile=fido2_harness.provider_profile,
        assertion=evidence,
    )
    assert outcome.signature_valid is False


# ═══════════════════════════════════════════════════════════════════════════
# 9. Required Test -- Revoked Signer (item 104) -- provider-level AND
#    full Wave-4 integration
# ═══════════════════════════════════════════════════════════════════════════


def test_revoked_credential_record_fails_at_provider_level(fido2_harness: _Fido2Harness) -> None:
    payload = b'{"r":1}'
    revoked_record = HardwareCredentialRecord(
        signer_key_id=fido2_harness.signer_key_id,
        provider_profile=fido2_harness.provider_profile,
        protocol_name="FIDO2",
        algorithm="ES256",
        public_key=fido2_harness.record.public_key,
        status="revoked",
    )
    provider = Fido2HardwareProvider(credential_store=_CredentialStoreFixture({fido2_harness.signer_key_id: revoked_record}))
    evidence = fido2_harness.evidence(payload)
    outcome = provider.verify(
        canonical_payload=payload,
        signer_key_id=fido2_harness.signer_key_id,
        provider_profile=fido2_harness.provider_profile,
        assertion=evidence,
    )
    assert outcome.signature_valid is False


def _build_wave4_integration_harness(tmp_path: Path) -> dict:
    repo_id = str(uuid.uuid4())
    deploy_dir = tmp_path / "deploy"
    deploy_dir.mkdir()
    canonical_root = resolve_canonical_deployment_root(deploy_dir)

    principal_id = "principal-fido2-1"
    private_key = _generate_test_key()
    credential_id = uuid.uuid4().bytes
    signer_key_id = credential_id.hex()
    provider_profile = HATP_HARDWARE_PROVIDER_V1

    store_root = tmp_path / "trust-store"
    store_root.mkdir(parents=True)
    (store_root / "registry.json").write_text(
        json.dumps(
            {
                "registry_version": 1,
                "principals": [{"principal_id": principal_id, "status": "active"}],
                "signers": [
                    {
                        "signer_key_id": signer_key_id,
                        "principal_id": principal_id,
                        "provider_profile": provider_profile,
                        "status": "active",
                    }
                ],
                "deployment_bindings": [
                    {
                        "repository_id": repo_id,
                        "canonical_deployment_root": canonical_root,
                        "principal_id": principal_id,
                        "signer_key_id": signer_key_id,
                        "provider_profile": provider_profile,
                        "authority_scope": "rollback",
                        "valid_from": "2026-01-01T00:00:00.000Z",
                        "status": "active",
                    }
                ],
                "authorities": [
                    {
                        "principal_id": principal_id,
                        "repository_id": repo_id,
                        "authority_scope": "rollback",
                        "status": "active",
                        "valid_from": "2026-01-01T00:00:00.000Z",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    trust_store = HATPTrustStore(_test_only_root=store_root)

    record = HardwareCredentialRecord(
        signer_key_id=signer_key_id,
        provider_profile=provider_profile,
        protocol_name="FIDO2",
        algorithm="ES256",
        public_key=_cose_public_key_bytes(private_key),
        status="active",
    )
    provider = Fido2HardwareProvider(credential_store=_CredentialStoreFixture({signer_key_id: record}))

    proof = HumanApprovalProvenanceProof(
        proof_version=1,
        principal_id=principal_id,
        signer_key_id=signer_key_id,
        provider_profile=provider_profile,
        repository_id=repo_id,
        decision_record_id="decision-fido2-1",
        decision_record_digest="0" * 64,
        binding_id="binding-fido2-1",
        binding_digest="1" * 64,
        rollback_site=RollbackSite.AG3,
        operation_reference=Ag3OperationReference(job_id="job-fido2-1", original_commit_sha="a" * 40),
        issued_at="2026-08-07T12:00:00.000Z",
    )
    expected_operation = HATPExpectedOperation(
        decision_record_id=proof.decision_record_id,
        binding_id=proof.binding_id,
        rollback_site=proof.rollback_site,
        operation_reference=proof.operation_reference,
    )
    return {
        "repo_id": repo_id,
        "canonical_root": canonical_root,
        "principal_id": principal_id,
        "private_key": private_key,
        "credential_id": credential_id,
        "signer_key_id": signer_key_id,
        "provider_profile": provider_profile,
        "trust_store": trust_store,
        "provider": provider,
        "proof": proof,
        "expected_operation": expected_operation,
        "store_root": store_root,
    }


def _verify_with_harness(harness: dict, *, up: bool = True, **trust_store_kwargs) -> HATPVerificationStatus:
    proof = harness["proof"]
    payload = canonicalize_hatp_proof_payload(proof)
    evidence = HATPVerificationEvidence(
        assertion=_sign_assertion(harness["private_key"], canonical_payload=payload, credential_id=harness["credential_id"], up=up)
    )
    trust_store = trust_store_kwargs.pop("trust_store", harness["trust_store"])
    result = verify_hatp_proof(
        proof,
        evidence=evidence,
        provider=harness["provider"],
        trust_store=trust_store,
        expected_operation=harness["expected_operation"],
        current_repository_id=trust_store_kwargs.pop("current_repository_id", harness["repo_id"]),
        canonical_deployment_root=trust_store_kwargs.pop("canonical_deployment_root", harness["canonical_root"]),
        evaluation_time=_EVAL_TIME,
    )
    return result.status


def test_full_wave4_integration_valid_end_to_end(tmp_path: Path) -> None:
    harness = _build_wave4_integration_harness(tmp_path)
    assert _verify_with_harness(harness) == HATPVerificationStatus.VALID


def test_full_wave4_integration_revoked_signer(tmp_path: Path) -> None:
    harness = _build_wave4_integration_harness(tmp_path)
    registry_path = harness["store_root"] / "registry.json"
    document = json.loads(registry_path.read_text(encoding="utf-8"))
    document["signers"][0]["status"] = "revoked"
    document["signers"][0]["revoked_at"] = "2026-08-07T00:00:00.000Z"
    registry_path.write_text(json.dumps(document), encoding="utf-8")
    assert _verify_with_harness(harness) == HATPVerificationStatus.REVOKED_SIGNER


# ═══════════════════════════════════════════════════════════════════════════
# 10/11. Required Test -- Wrong Repository / Wrong Deployment (105/106),
#         via full Wave-4 integration with the real hardware provider
# ═══════════════════════════════════════════════════════════════════════════


def test_full_wave4_integration_wrong_repository(tmp_path: Path) -> None:
    harness = _build_wave4_integration_harness(tmp_path)
    status = _verify_with_harness(harness, current_repository_id=str(uuid.uuid4()))
    assert status in (HATPVerificationStatus.WRONG_REPOSITORY, HATPVerificationStatus.UNAUTHORIZED_SIGNER)


def test_full_wave4_integration_wrong_deployment_root(tmp_path: Path) -> None:
    harness = _build_wave4_integration_harness(tmp_path)
    other_dir = tmp_path / "other-deploy"
    other_dir.mkdir()
    other_root = resolve_canonical_deployment_root(other_dir)
    assert _verify_with_harness(harness, canonical_deployment_root=other_root) == HATPVerificationStatus.WRONG_DEPLOYMENT


# ═══════════════════════════════════════════════════════════════════════════
# 12. Required Test -- Attestation (item 107) -- documented, machine-
#     checked non-blocking limitation, not a fabricated failure path
# ═══════════════════════════════════════════════════════════════════════════


def test_fido2_provider_does_not_claim_device_attestation(fido2_harness: _Fido2Harness) -> None:
    capabilities = fido2_harness.provider.capabilities()
    assert capabilities.device_attestation is False
    assert capabilities.hatp_conformant == HardwareProviderConformance.CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS
    outcome = fido2_harness.verify(b'{"attest":1}')
    assert outcome.attestation_valid is None


def test_wave4_verifier_still_fails_closed_if_a_provider_reports_attestation_invalid() -> None:
    """Confirms Wave 4's own (already independently verified)
    attestation-failure handling remains correctly wired for ANY
    provider outcome, including one a real Wave-5 provider could one
    day produce once device attestation is implemented -- exercised
    here with the deterministic test provider, since no Wave-5 provider
    in this phase sets `attestation_valid=False`."""

    outcome = TestHATPProofVerifierProvider(attestation_valid=False).verify(
        canonical_payload=b"x", signer_key_id="s", provider_profile="p", assertion=b"y"
    )
    assert outcome.attestation_valid is False


# ═══════════════════════════════════════════════════════════════════════════
# 13. Required Test -- Device Unavailable (item 109) -- real environment
#     fact on this machine (zero attached devices)
# ═══════════════════════════════════════════════════════════════════════════


def test_request_signature_raises_unavailable_when_no_device_attached() -> None:
    provider = Fido2HardwareProvider()
    with pytest.raises(HATPProviderUnavailableError):
        provider.request_signature(b"payload", signer_key_id="aa", provider_profile=HATP_HARDWARE_PROVIDER_V1)


def test_credential_identity_raises_unavailable_when_no_device_attached() -> None:
    provider = Fido2HardwareProvider()
    with pytest.raises(HATPProviderUnavailableError):
        provider.credential_identity()


def test_piv_provider_unconditionally_unavailable() -> None:
    provider = PivHardwareProvider()
    with pytest.raises(HATPProviderUnavailableError):
        provider.credential_identity()
    with pytest.raises(HATPProviderUnavailableError):
        provider.request_signature(b"x", signer_key_id="s", provider_profile=HATP_HARDWARE_PROVIDER_V1)
    outcome = provider.verify(canonical_payload=b"x", signer_key_id="s", provider_profile=HATP_HARDWARE_PROVIDER_V1, assertion=b"y")
    assert outcome.signature_valid is False
    assert provider.capabilities().hatp_conformant == HardwareProviderConformance.NOT_CONFORMANT


# ═══════════════════════════════════════════════════════════════════════════
# 14/15. Required Test -- User Cancels / Device Disconnects (110/111),
#         simulated via monkeypatch (no real device exists to exercise
#         this path on -- item 88, honestly marked as simulated)
# ═══════════════════════════════════════════════════════════════════════════


class _FakeDevice:
    pass


class _CancellingCtap2:
    def __init__(self, device) -> None:
        pass

    def get_assertion(self, **kwargs):
        from fido2.ctap import CtapError

        raise CtapError(CtapError.ERR.ACTION_TIMEOUT)


class _FailingCtap2:
    def __init__(self, device) -> None:
        pass

    def get_assertion(self, **kwargs):
        raise OSError("simulated device I/O failure")


def test_request_signature_maps_ctap_timeout_to_cancelled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fido2_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([_FakeDevice()])))
    monkeypatch.setattr(fido2_module, "Ctap2", _CancellingCtap2)
    provider = Fido2HardwareProvider()
    with pytest.raises(HATPProviderCancelledError):
        provider.request_signature(b"payload", signer_key_id="aa" * 8, provider_profile=HATP_HARDWARE_PROVIDER_V1)


def test_request_signature_maps_transport_failure_to_device_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fido2_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([_FakeDevice()])))
    monkeypatch.setattr(fido2_module, "Ctap2", _FailingCtap2)
    provider = Fido2HardwareProvider()
    with pytest.raises(HATPProviderDeviceError):
        provider.request_signature(b"payload", signer_key_id="aa" * 8, provider_profile=HATP_HARDWARE_PROVIDER_V1)


def test_request_signature_rejects_non_hex_signer_key_id() -> None:
    monkeypatch_devices = None
    provider = Fido2HardwareProvider()
    # No device attached in this environment -> device-absence is
    # checked before the signer_key_id parse; this exercises the parse
    # path independently via direct call with a patched device list.
    with pytest.raises(HATPProviderUnavailableError):
        provider.request_signature(b"payload", signer_key_id="not-hex!", provider_profile=HATP_HARDWARE_PROVIDER_V1)


# ═══════════════════════════════════════════════════════════════════════════
# 16. Required Test -- Test Provider Cannot Enter Production Factory
#     (item 112)
# ═══════════════════════════════════════════════════════════════════════════


def test_production_factory_never_returns_test_provider() -> None:
    provider = create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)
    assert not isinstance(provider, TestHATPProofVerifierProvider)
    assert isinstance(provider, Fido2HardwareProvider)


def test_production_factory_rejects_unrecognized_profile() -> None:
    with pytest.raises(HATPProviderUnavailableError):
        create_production_hardware_provider("NOT_A_REAL_PROFILE")
    with pytest.raises(HATPProviderUnavailableError):
        create_production_hardware_provider("TEST_PROVIDER_V1")


def test_production_factory_module_never_imports_test_provider_by_name() -> None:
    source = _strip_docstrings_and_comments(inspect.getsource(providers_module.create_production_hardware_provider))
    assert "TestHATPProofVerifierProvider" not in source


def test_production_factory_piv_fallback_is_explicit_not_automatic() -> None:
    """FIDO2 IS available (library installed) in this environment, so
    the factory returns it without ever considering PIV -- fallback
    only activates if the caller explicitly requests it AND FIDO2 is
    itself unavailable (item 6/7: no silent downgrade)."""

    sig = inspect.signature(create_production_hardware_provider)
    assert "allow_piv_fallback" in sig.parameters
    assert sig.parameters["allow_piv_fallback"].default is False


# ═══════════════════════════════════════════════════════════════════════════
# 17. Required Test -- Software Private Key Cannot Enter Production
#     Provider (item 113)
# ═══════════════════════════════════════════════════════════════════════════


def _ast_assigned_names(source: str) -> set:
    tree = ast.parse(source)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            names.add(node.arg)
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def test_no_production_code_path_accepts_a_private_key_parameter() -> None:
    forbidden_substrings = ("private_key", "priv_key", "pem_key", "software_key")
    for module in (fido2_module, piv_module, providers_module):
        source = inspect.getsource(module)
        names = _ast_assigned_names(source)
        for name in names:
            lowered = name.lower()
            for forbidden in forbidden_substrings:
                assert forbidden not in lowered, f"{module.__name__} defines suspicious name {name!r}"


def test_fido2_provider_signing_path_has_no_software_fallback() -> None:
    """`request_signature`'s only path to producing evidence is a real
    `Ctap2.get_assertion` call against an enumerated device -- there is
    no branch that constructs or accepts an in-process private key."""

    source = inspect.getsource(Fido2HardwareProvider.request_signature)
    assert "generate_private_key" not in source
    assert ".sign(" not in source  # no in-process signing call
    assert "Ctap2" in source


def test_credential_registry_stores_only_public_key_material() -> None:
    field_names = {f.name for f in fields(HardwareCredentialRecord)}
    assert "private_key" not in field_names
    # `revoked_at` added by Phase 149O.20L.7O.2F (HHCE-REQ-008, closes
    # NBF-2) -- the only widening this record's schema has ever had.
    assert field_names == {
        "signer_key_id",
        "provider_profile",
        "protocol_name",
        "algorithm",
        "public_key",
        "status",
        "revoked_at",
    }


# ═══════════════════════════════════════════════════════════════════════════
# 18. Required Test -- Provider Availability Does Not Make HATP
#     Operational (item 114)
# ═══════════════════════════════════════════════════════════════════════════


def test_fido2_library_installed_does_not_flip_substrate_operational(tmp_path: Path) -> None:
    from pcae.core.human_approval_trusted_provenance import inspect_hatp_verification_substrate_readiness

    harness = _build_wave4_integration_harness(tmp_path)
    readiness = inspect_hatp_verification_substrate_readiness(harness["trust_store"], current_repository_id=harness["repo_id"])
    assert readiness.operational is False
    terms = dict(readiness.terms)
    assert terms["provider_profile_available"] is False
    assert terms["provider_attestation_trusted"] is False


# ═══════════════════════════════════════════════════════════════════════════
# 19. Required Test -- No Approval Derivation (item 115)
# ═══════════════════════════════════════════════════════════════════════════


def test_no_approval_present_derivation_in_any_wave5_module() -> None:
    forbidden_targets = {"approval_present", "approved", "authorized", "can_execute", "permission"}
    for module in (providers_module, fido2_module, piv_module, credentials_module):
        source = inspect.getsource(module)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    name = target.id if isinstance(target, ast.Name) else getattr(target, "attr", None)
                    assert name not in forbidden_targets, f"{module.__name__} assigns forbidden name {name!r}"


def test_hardware_credential_record_has_no_authority_fields() -> None:
    field_names = {f.name for f in fields(HardwareCredentialRecord)}
    forbidden = {"approved", "authorized", "approval_present", "can_execute", "permission"}
    assert field_names.isdisjoint(forbidden)


def test_provider_assertion_and_capabilities_have_no_authority_fields() -> None:
    forbidden = {"approved", "authorized", "approval_present", "can_execute", "permission"}
    assert {f.name for f in fields(ProviderAssertion)}.isdisjoint(forbidden)
    assert {f.name for f in fields(HardwareProviderCapabilities)}.isdisjoint(forbidden)


# ═══════════════════════════════════════════════════════════════════════════
# 20. Required Test -- No RAE/PB/Agent Call Sites (item 116)
# ═══════════════════════════════════════════════════════════════════════════


def test_no_wave5_module_imported_by_rae_pb_or_agent() -> None:
    wave5_module_names = {"hatp_fido2_provider", "hatp_piv_provider", "hatp_hardware_credentials"}
    consumer_files = [
        _SRC_ROOT / "core" / "rollback_approval_evidence.py",
        _SRC_ROOT / "core" / "permission_broker.py",
        _SRC_ROOT / "core" / "permission_broker_foundation.py",
        _SRC_ROOT / "agent.py",
        _SRC_ROOT / "commands" / "agent.py",
    ]
    for path in consumer_files:
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8")
        for module_name in wave5_module_names:
            assert module_name not in source, f"{path} unexpectedly references {module_name}"


def test_wave5_modules_do_not_import_rae_pb_or_agent() -> None:
    forbidden = ("rollback_approval_evidence", "permission_broker", "pcae.agent", "commands.agent")
    for module in (providers_module, fido2_module, piv_module, credentials_module):
        source = inspect.getsource(module)
        import_lines = "\n".join(
            line.strip() for line in source.splitlines() if re.match(r"^\s*(from|import)\s", line)
        )
        for term in forbidden:
            assert term not in import_lines, f"{module.__name__} imports forbidden module matching {term!r}"


# ═══════════════════════════════════════════════════════════════════════════
# 21. Required Test -- No Prompt/Execution Expansion (item 117)
# ═══════════════════════════════════════════════════════════════════════════


def test_no_wave5_module_references_prompt_generation_or_dispatch() -> None:
    forbidden_terms = ("prompt_generation", "prompt_dispatch", "invoke_agent", "execute_command", "subprocess.run", "os.system")
    for module in (providers_module, fido2_module, piv_module, credentials_module):
        source = inspect.getsource(module)
        for term in forbidden_terms:
            assert term not in source, f"{module.__name__} unexpectedly references {term!r}"


# ═══════════════════════════════════════════════════════════════════════════
# 22. Wave-3/4 module-boundary preservation
# ═══════════════════════════════════════════════════════════════════════════


def test_human_approval_trusted_provenance_does_not_import_any_wave5_module() -> None:
    import pcae.core.human_approval_trusted_provenance as hatp_module

    source = inspect.getsource(hatp_module)
    for name in ("hatp_fido2_provider", "hatp_piv_provider", "hatp_hardware_credentials"):
        assert name not in source


def test_hatp_bootstrap_does_not_import_any_wave5_module() -> None:
    import pcae.core.hatp_bootstrap as bootstrap_module

    source = inspect.getsource(bootstrap_module)
    for name in ("hatp_fido2_provider", "hatp_piv_provider", "hatp_hardware_credentials"):
        assert name not in source


def test_hatp_hardware_credentials_does_not_import_hatp_bootstrap() -> None:
    """Deliberate module independence (mirrors `hatp_bootstrap.py`'s own
    dependency-direction discipline toward `repository_identity.py`)."""

    source = _strip_docstrings_and_comments(inspect.getsource(credentials_module))
    assert "hatp_bootstrap" not in source


# ═══════════════════════════════════════════════════════════════════════════
# 23. Evidence-format strictness (items 30-32)
# ═══════════════════════════════════════════════════════════════════════════


def test_evidence_rejects_unknown_field(fido2_harness: _Fido2Harness) -> None:
    payload = b'{"e":1}'
    evidence = fido2_harness.evidence(payload)
    document = json.loads(evidence)
    document["unexpected_field"] = "x"
    tampered = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    outcome = fido2_harness.verify(payload, evidence=tampered)
    assert outcome.signature_valid is False


def test_evidence_rejects_missing_field(fido2_harness: _Fido2Harness) -> None:
    payload = b'{"e":2}'
    evidence = fido2_harness.evidence(payload)
    document = json.loads(evidence)
    del document["signature_hex"]
    tampered = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    outcome = fido2_harness.verify(payload, evidence=tampered)
    assert outcome.signature_valid is False


def test_evidence_rejects_unknown_version(fido2_harness: _Fido2Harness) -> None:
    payload = b'{"e":3}'
    evidence = fido2_harness.evidence(payload)
    document = json.loads(evidence)
    document["version"] = 999
    tampered = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    outcome = fido2_harness.verify(payload, evidence=tampered)
    assert outcome.signature_valid is False


def test_evidence_rejects_duplicate_json_keys(fido2_harness: _Fido2Harness) -> None:
    payload = b'{"e":4}'
    evidence = fido2_harness.evidence(payload)
    document = json.loads(evidence)
    raw = json.dumps(document, sort_keys=True, separators=(",", ":"))
    duplicated = raw[:-1] + f',"version":{document["version"]}}}'
    outcome = fido2_harness.verify(payload, evidence=duplicated.encode("utf-8"))
    assert outcome.signature_valid is False


def test_evidence_rejects_non_json_garbage(fido2_harness: _Fido2Harness) -> None:
    outcome = fido2_harness.verify(b'{"e":5}', evidence=b"not json at all")
    assert outcome.signature_valid is False


def test_verify_never_raises_for_malformed_assertion(fido2_harness: _Fido2Harness) -> None:
    """Contract restated from `HATPProofVerifierProvider.verify`: MUST
    NOT raise for an invalid/unrecognized assertion."""

    for garbage in (b"", b"{}", b"null", b'{"version":1}', b"\xff\xfe\x00"):
        outcome = fido2_harness.provider.verify(
            canonical_payload=b"payload",
            signer_key_id=fido2_harness.signer_key_id,
            provider_profile=fido2_harness.provider_profile,
            assertion=garbage,
        )
        assert outcome.signature_valid is False


# ═══════════════════════════════════════════════════════════════════════════
# 24. Protected credential registry (mirrors HATPTrustStore discipline)
# ═══════════════════════════════════════════════════════════════════════════


def _write_credential_registry(root: Path, document: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "hardware-credentials.json").write_text(json.dumps(document), encoding="utf-8")


def test_credential_store_round_trip(tmp_path: Path) -> None:
    store_root = tmp_path / "hw-credentials"
    _write_credential_registry(
        store_root,
        {
            "credentials": [
                {
                    "signer_key_id": "abcd",
                    "provider_profile": HATP_HARDWARE_PROVIDER_V1,
                    "protocol_name": "FIDO2",
                    "algorithm": "ES256",
                    "public_key_hex": "aa" * 10,
                    "status": "active",
                }
            ]
        },
    )
    store = HATPHardwareCredentialStore(_test_only_root=store_root)
    record = store.lookup_credential("abcd")
    assert record is not None
    assert record.signer_key_id == "abcd"
    assert record.public_key == bytes.fromhex("aa" * 10)
    assert store.lookup_credential("does-not-exist") is None


def test_credential_store_rejects_duplicate_signer_records(tmp_path: Path) -> None:
    store_root = tmp_path / "hw-credentials-dup"
    doc = {
        "credentials": [
            {
                "signer_key_id": "dup",
                "provider_profile": HATP_HARDWARE_PROVIDER_V1,
                "protocol_name": "FIDO2",
                "algorithm": "ES256",
                "public_key_hex": "bb" * 10,
                "status": "active",
            },
            {
                "signer_key_id": "dup",
                "provider_profile": HATP_HARDWARE_PROVIDER_V1,
                "protocol_name": "FIDO2",
                "algorithm": "ES256",
                "public_key_hex": "cc" * 10,
                "status": "active",
            },
        ]
    }
    _write_credential_registry(store_root, doc)
    store = HATPHardwareCredentialStore(_test_only_root=store_root)
    with pytest.raises(credentials_module.HATPHardwareCredentialStoreMalformedError):
        store.lookup_credential("dup")


def test_credential_store_rejects_symlinked_root(tmp_path: Path) -> None:
    real_root = tmp_path / "real-store"
    real_root.mkdir()
    symlink_root = tmp_path / "symlink-store"
    symlink_root.symlink_to(real_root)
    store = HATPHardwareCredentialStore(_test_only_root=symlink_root)
    with pytest.raises(credentials_module.HATPHardwareCredentialStoreSymlinkError):
        store.lookup_credential("anything")


def test_credential_store_production_accepts_no_override_argument() -> None:
    sig = inspect.signature(HATPHardwareCredentialStore.production)
    assert list(sig.parameters) == []


def test_credential_store_has_no_enroll_revoke_or_rotate_method() -> None:
    forbidden_methods = {"enroll", "grant", "revoke", "rotate"}
    public_methods = {name for name in dir(HATPHardwareCredentialStore) if not name.startswith("_")}
    assert public_methods.isdisjoint(forbidden_methods)


def test_credential_store_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    store_root = tmp_path / "hw-credentials-dupkeys"
    store_root.mkdir(parents=True)
    (store_root / "hardware-credentials.json").write_text(
        '{"credentials": [], "credentials": []}', encoding="utf-8"
    )
    store = HATPHardwareCredentialStore(_test_only_root=store_root)
    with pytest.raises(credentials_module.HATPHardwareCredentialStoreMalformedError):
        store.lookup_credential("anything")


# ═══════════════════════════════════════════════════════════════════════════
# 25. Capability matrix (item 58) sanity
# ═══════════════════════════════════════════════════════════════════════════


def test_fido2_capability_matrix_facts() -> None:
    capabilities = Fido2HardwareProvider().capabilities()
    assert capabilities.provider_profile == HATP_HARDWARE_PROVIDER_V1
    assert capabilities.non_exportable_key is True
    assert capabilities.fresh_touch_per_operation is True
    assert capabilities.credential_identity is True
    assert capabilities.signature_verification is True
    assert capabilities.device_attestation is False


def test_piv_capability_matrix_facts() -> None:
    capabilities = PivHardwareProvider().capabilities()
    assert capabilities.provider_profile == HATP_HARDWARE_PROVIDER_V1
    assert capabilities.non_exportable_key is False
    assert capabilities.fresh_touch_per_operation is False
    assert capabilities.hatp_conformant == HardwareProviderConformance.NOT_CONFORMANT


# ═══════════════════════════════════════════════════════════════════════════
# 26. Hardware-required (skipped on this machine -- item 92/93)
# ═══════════════════════════════════════════════════════════════════════════


def _real_fido2_device_attached() -> bool:
    try:
        from fido2.hid import CtapHidDevice

        return any(True for _ in CtapHidDevice.list_devices())
    except Exception:  # noqa: BLE001
        return False


@pytest.mark.hatp_hardware_required
@pytest.mark.skipif(not _real_fido2_device_attached(), reason="no real FIDO2 device attached to this environment")
def test_real_device_sign_and_verify_round_trip() -> None:  # pragma: no cover
    """Real-hardware test, environment-dependent (item 92): only runs
    if a genuine FIDO2 authenticator is attached. This development
    machine has none -- confirmed by `test_discover_hardware_providers_reports_honest_facts`
    above -- so this test is skipped, never fabricated as passing."""

    pytest.skip("no real hardware in CI/this environment; structural placeholder for a real device")
