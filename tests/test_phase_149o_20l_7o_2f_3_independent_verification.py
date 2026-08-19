"""Independent adversarial verification of Phase 149O.20L.7O.2F.2.

This file deliberately does not import the 2F.2 phase test module.  It
reconstructs the old resolver from the fixed pre-repair commit and validates
the current production orchestrator with independently-built fakes.
"""
from __future__ import annotations

import ast
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from fido2.cose import ES256
from fido2.webauthn import AuthenticatorData

from pcae.core import hatp_deployment_binding_admin as binding_admin
from pcae.core import hatp_fido2_provider as fido2_module
from pcae.core import hatp_hardware_credential_admin as credential_admin
from pcae.core import hatp_principal_signer_admin as principal_admin
from pcae.core import hatp_signing_ceremony as ceremony
from pcae.core.hatp_evidence_store import HATPEvidenceStore
from pcae.core.hatp_bootstrap import DeploymentBinding, PrincipalRecord, SignerRecord
from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.hatp_hardware_credentials import HardwareCredentialRecord
from pcae.core.hatp_hardware_credentials import HATPHardwareCredentialStore
from pcae.core.hatp_providers import (
    HATP_HARDWARE_PROVIDER_V1,
    HATPProviderUnavailableError,
    ProviderAssertion,
)
from pcae.core.human_approval_trusted_provenance import RollbackSite
from fido2.webauthn import CollectedClientData

from test_hatp_signing_ceremony import _setup_ag3


PRE_REPAIR_COMMIT = "6e5c258d^"


def _binding(*, principal: str = "principal-1", signer: str = "11" * 16, profile: str = HATP_HARDWARE_PROVIDER_V1, scope: str = "rollback_signing") -> DeploymentBinding:
    return DeploymentBinding(
        repository_id="repo-1",
        canonical_deployment_root="/not-trusted-by-fake",
        principal_id=principal,
        signer_key_id=signer,
        provider_profile=profile,
        authority_scope=scope,
        valid_from="2026-08-19T00:00:00.000Z",
        status="active",
    )


def _signer(*, principal: str = "principal-1", signer: str = "11" * 16, profile: str = HATP_HARDWARE_PROVIDER_V1, status: str = "active") -> SignerRecord:
    return SignerRecord(signer_key_id=signer, principal_id=principal, provider_profile=profile, status=status)


def _principal(principal: str = "principal-1", status: str = "active") -> PrincipalRecord:
    return PrincipalRecord(principal_id=principal, status=status)


def _credential(*, signer: str = "11" * 16, profile: str = HATP_HARDWARE_PROVIDER_V1, status: str = "active", public_key: bytes = b"cose-key") -> HardwareCredentialRecord:
    return HardwareCredentialRecord(
        signer_key_id=signer,
        provider_profile=profile,
        protocol_name="FIDO2",
        algorithm="ES256",
        public_key=public_key,
        status=status,
    )


class _Trust:
    def __init__(self, binding=None, signers=None, principals=None):
        self.binding = binding
        self.signers = signers or {}
        self.principals = principals or {}

    def resolve_deployment_authorization(self, **_kwargs):
        return self.binding

    def lookup_signer(self, signer_key_id):
        return self.signers.get(signer_key_id)

    def lookup_principal(self, principal_id):
        return self.principals.get(principal_id)


class _HardwareStore:
    def __init__(self, records=None):
        self.records = records or {}

    def lookup_credential(self, signer_key_id):
        return self.records.get(signer_key_id)


class _Provider:
    def __init__(self, on_touch=None, fail_touch: Exception | None = None):
        self.identity_calls = 0
        self.touch_calls = 0
        self.received_signer = None
        self.on_touch = on_touch
        self.fail_touch = fail_touch

    def credential_identity(self):
        self.identity_calls += 1
        raise HATPProviderUnavailableError("historical BF-1: unavailable")

    def request_signature(self, payload, *, signer_key_id, provider_profile, presence_timeout_s=30.0):
        self.touch_calls += 1
        self.received_signer = signer_key_id
        if self.on_touch:
            self.on_touch()
        if self.fail_touch:
            raise self.fail_touch
        return ProviderAssertion(
            credential_id=signer_key_id,
            provider_profile=provider_profile,
            algorithm="ES256",
            evidence=b"independent-assertion",
        )


def _valid_state():
    signer_id = "11" * 16
    trust = _Trust(
        _binding(signer=signer_id),
        {signer_id: _signer(signer=signer_id)},
        {"principal-1": _principal()},
    )
    hardware = _HardwareStore({signer_id: _credential(signer=signer_id)})
    return trust, hardware


def _run(root, trust, hardware, provider, *, confirm=lambda _preview: True):
    return ceremony.sign_rollback_evidence(
        root,
        site=RollbackSite.AG3,
        job_id="job-1",
        provider_factory=lambda: provider,
        trust_store_factory=lambda: trust,
        hardware_credential_store_factory=lambda: hardware,
        confirm=confirm,
    )


def test_bf1_historical_resolver_executes_unavailable_identity_call():
    """Execute the actual old function body, rather than merely grepping it."""
    source = subprocess.run(
        ["git", "show", f"{PRE_REPAIR_COMMIT}:src/pcae/core/hatp_signing_ceremony.py"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_resolve_signer")
    node.decorator_list = []
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "Tuple": tuple,
        "HATPTrustStore": object,
        "HATPHardwareSigner": object,
        "ProviderUnavailableError": ceremony.ProviderUnavailableError,
        "NoAuthorizedSignerError": ceremony.NoAuthorizedSignerError,
        "HATPTrustStoreError": Exception,
    }
    exec(compile(module, "<pre-2f2-resolver>", "exec"), namespace)
    provider = _Provider()
    with pytest.raises(ceremony.ProviderUnavailableError, match="credential identity unavailable"):
        namespace["_resolve_signer"](_Trust(), provider)
    assert provider.identity_calls == 1
    assert provider.touch_calls == 0


def test_current_signing_resolves_explicit_nonresident_credential_without_identity(tmp_path):
    """The current path uses the bound ID and reaches the one hardware touch."""
    root = _setup_ag3(tmp_path)
    trust, hardware = _valid_state()
    provider = _Provider()
    result = _run(root, trust, hardware, provider)
    assert result.path.exists()
    assert provider.identity_calls == 0
    assert provider.touch_calls == 1
    assert provider.received_signer == "11" * 16


def test_multiple_active_signers_do_not_affect_bound_signer_selection(tmp_path):
    root = _setup_ag3(tmp_path)
    trust, hardware = _valid_state()
    trust.signers["22" * 16] = _signer(principal="principal-2", signer="22" * 16)
    trust.principals["principal-2"] = _principal("principal-2")
    hardware.records["22" * 16] = _credential(signer="22" * 16)
    assert ceremony._resolve_deployment_binding_signer(
        root,
        trust,
        repository_id="repo-1",
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        hardware_credential_store_factory=lambda: hardware,
    ) == ("principal-1", "11" * 16)


def test_duplicate_deployment_bindings_fail_closed_before_hardware(tmp_path):
    root = _setup_ag3(tmp_path)
    repo_id = "11111111-1111-4111-8111-111111111111"
    binding = {
        "repository_id": repo_id,
        "canonical_deployment_root": str(root.path.resolve()),
        "principal_id": "principal-1",
        "signer_key_id": "11" * 16,
        "provider_profile": HATP_HARDWARE_PROVIDER_V1,
        "authority_scope": "rollback_signing",
        "valid_from": "2026-08-19T00:00:00.000Z",
        "status": "active",
        "revoked_at": None,
    }
    registry_root = tmp_path / "duplicate-registry"
    registry_root.mkdir()
    (registry_root / "registry.json").write_text(
        json.dumps({"registry_version": 1, "principals": [], "signers": [], "authorities": [], "deployment_bindings": [binding, binding]}),
        encoding="utf-8",
    )
    with pytest.raises(ceremony.NoAuthorizedSignerError, match="protected trust store unavailable"):
        ceremony._resolve_deployment_binding_signer(
            root,
            HATPTrustStore(_test_only_root=registry_root),
            repository_id=repo_id,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            hardware_credential_store_factory=lambda: _HardwareStore(),
        )


def test_bf2_makecredential_is_nonresident_but_getassertion_uses_explicit_allow_list(monkeypatch):
    """Prove both halves: enrollment omits rk and signing supplies the ID."""
    enrollment_kwargs = {}
    assertion_kwargs = {}

    class Device: pass

    class CredentialData:
        credential_id = bytes.fromhex("11" * 16)
        public_key = fido2_module.ES256.from_cryptography_key(ec.generate_private_key(ec.SECP256R1()).public_key())

    class Attestation:
        auth_data = type("AuthData", (), {"credential_data": CredentialData()})()

    class Assertion:
        auth_data = b"\x00" * 37
        signature = b"signature"

    class Ctap:
        def __init__(self, _device): pass
        def make_credential(self, **kwargs):
            enrollment_kwargs.update(kwargs)
            return Attestation()
        def get_assertion(self, **kwargs):
            assertion_kwargs.update(kwargs)
            return Assertion()

    monkeypatch.setattr(fido2_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([Device()])))
    monkeypatch.setattr(fido2_module, "Ctap2", Ctap)
    provider = fido2_module.Fido2HardwareProvider()
    enrolled = provider.enroll_credential()
    provider.request_signature(
        b"payload", signer_key_id=enrolled.credential_id_hex, provider_profile=HATP_HARDWARE_PROVIDER_V1
    )
    assert "options" not in enrollment_kwargs  # CTAP2 default rk=false: non-resident
    assert assertion_kwargs["allow_list"] == [
        {"type": "public-key", "id": bytes.fromhex(enrolled.credential_id_hex)}
    ]


def test_real_writers_nonresident_fido2_chain_signs_and_verifies_cryptographically(tmp_path, monkeypatch):
    """Independent BF-2 closure through every production trust writer.

    Only HID/CTAP transport is synthetic.  The real enrollment method,
    credential/principal/signer/binding writers, signing orchestrator,
    FIDO request method, evidence store, and FIDO verifier all run.
    """
    root = _setup_ag3(tmp_path)
    credential_root = tmp_path / "credentials"
    trust_root = tmp_path / "trust"
    credential_root.mkdir()
    trust_root.mkdir()
    private_key = ec.generate_private_key(ec.SECP256R1())
    cose_key = ES256.from_cryptography_key(private_key.public_key())
    credential_id = bytes.fromhex("ab" * 16)
    calls = {"make": None, "get": None}

    class Device:
        pass

    class Ctap:
        def __init__(self, _device):
            pass

        def make_credential(self, **kwargs):
            calls["make"] = kwargs
            credential_data = type(
                "CredentialData", (), {"credential_id": credential_id, "public_key": cose_key}
            )()
            return type(
                "Attestation", (), {"auth_data": type("AuthData", (), {"credential_data": credential_data})()}
            )()

        def get_assertion(self, **kwargs):
            calls["get"] = kwargs
            auth_data = AuthenticatorData.create(
                fido2_module._RP_ID_HASH, AuthenticatorData.FLAG.UP, 1
            )
            signature = private_key.sign(
                bytes(auth_data) + kwargs["client_data_hash"], ec.ECDSA(hashes.SHA256())
            )
            return type("Assertion", (), {"auth_data": auth_data, "signature": signature})()

    monkeypatch.setattr(fido2_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([Device()])))
    monkeypatch.setattr(fido2_module, "Ctap2", Ctap)
    enrolled = fido2_module.Fido2HardwareProvider().enroll_credential()
    assert calls["make"] is not None and "options" not in calls["make"]

    credential_admin.register_credential(
        repository_root=root.path,
        evidence=credential_admin.CredentialEnrollmentEvidence(
            signer_key_id=enrolled.credential_id_hex,
            provider_profile=enrolled.provider_profile,
            protocol_name="FIDO2",
            algorithm=enrolled.algorithm,
            public_key_hex=enrolled.public_key_hex,
            enrollment_reference="CHGR-IV-CREDENTIAL",
        ),
        _store_root=credential_root,
    )
    principal_admin.enroll_principal(
        repository_root=root.path,
        evidence=principal_admin.PrincipalEnrollmentEvidence(
            principal_id="principal-iv", election_reference="CHGR-IV-PRINCIPAL"
        ),
        _protected_root=trust_root,
    )
    principal_admin.enroll_signer(
        repository_root=root.path,
        evidence=principal_admin.SignerEnrollmentEvidence(
            principal_id="principal-iv",
            signer_key_id=enrolled.credential_id_hex,
            provider_profile=enrolled.provider_profile,
            election_reference="CHGR-IV-SIGNER",
        ),
        _protected_root=trust_root,
        _hardware_store_root=credential_root,
    )
    binding_admin.create_deployment_binding(
        repository_root=root.path,
        authority=binding_admin.AuthorityEvidence(
            principal_id="principal-iv",
            signer_key_id=enrolled.credential_id_hex,
            authority_scope=binding_admin.CLASS_B_DEPLOYMENT_AUTHORITY_SCOPE,
            election_reference="CHGR-IV-BINDING",
        ),
        _protected_root=trust_root,
        _hardware_store_root=credential_root,
    )

    credential_store = HATPHardwareCredentialStore(_test_only_root=credential_root)
    provider = fido2_module.Fido2HardwareProvider(credential_store=credential_store)
    result = ceremony.sign_rollback_evidence(
        root,
        site=RollbackSite.AG3,
        job_id="job-1",
        provider_factory=lambda: provider,
        trust_store_factory=lambda: HATPTrustStore(_test_only_root=trust_root),
        hardware_credential_store_factory=lambda: credential_store,
        confirm=lambda _preview: True,
    )
    envelope = HATPEvidenceStore(root).load(result.evidence_id)
    verification = provider.verify(
        canonical_payload=ceremony.canonicalize_hatp_proof_payload(envelope.proof),
        signer_key_id=envelope.proof.signer_key_id,
        provider_profile=envelope.proof.provider_profile,
        assertion=envelope.provider_assertion,
    )
    assert calls["get"]["allow_list"] == [{"type": "public-key", "id": credential_id}]
    assert verification.signature_valid is True
    assert verification.human_presence_proven is True


def _rotate_binding(trust, _hardware):
    trust.binding = replace(trust.binding, signer_key_id="22" * 16)


def _revoke_signer(trust, _hardware):
    trust.signers["11" * 16] = replace(trust.signers["11" * 16], status="revoked")


def _revoke_principal(trust, _hardware):
    trust.principals["principal-1"] = replace(trust.principals["principal-1"], status="revoked")


def _revoke_credential(_trust, hardware):
    hardware.records["11" * 16] = replace(hardware.records["11" * 16], status="revoked")


def _change_credential_profile(_trust, hardware):
    hardware.records["11" * 16] = replace(hardware.records["11" * 16], provider_profile="PIV")


@pytest.mark.parametrize(
    "mutation",
    [_rotate_binding, _revoke_signer, _revoke_principal, _revoke_credential, _change_credential_profile],
    ids=["binding-rotation", "signer-revocation", "principal-revocation", "credential-revocation", "credential-profile-change"],
)
def test_toctou_authority_changes_discard_candidate_before_publication(tmp_path, mutation):
    root = _setup_ag3(tmp_path)
    trust, hardware = _valid_state()
    provider = _Provider(on_touch=lambda: mutation(trust, hardware))
    with pytest.raises(ceremony.EvidenceSerializationFailureError):
        _run(root, trust, hardware, provider)
    assert provider.touch_calls == 1
    envelope_dir = root.path / ".pcae" / "hatp-evidence" / "envelopes"
    assert not envelope_dir.exists() or not list(envelope_dir.glob("*.json"))


def test_blind_touch_invalid_or_missing_registry_state_never_touches_hardware(tmp_path):
    root = _setup_ag3(tmp_path)
    provider = _Provider()
    trust, hardware = _valid_state()
    trust.binding = None
    with pytest.raises(ceremony.NoAuthorizedSignerError):
        _run(root, trust, hardware, provider)
    assert provider.identity_calls == provider.touch_calls == 0


def test_registry_records_alone_cannot_publish_without_provider_signature(tmp_path):
    root = _setup_ag3(tmp_path)
    trust, hardware = _valid_state()
    provider = _Provider(fail_touch=HATPProviderUnavailableError("no authenticator"))
    with pytest.raises(ceremony.ProviderUnavailableError):
        _run(root, trust, hardware, provider)
    envelope_dir = root.path / ".pcae" / "hatp-evidence" / "envelopes"
    assert provider.touch_calls == 1
    assert not envelope_dir.exists() or not list(envelope_dir.glob("*.json"))


def test_wrong_authenticator_credential_is_rejected_by_real_verifier():
    intended = "11" * 16
    wrong = bytes.fromhex("22" * 16)
    client_data = CollectedClientData.create(
        type=CollectedClientData.TYPE.GET,
        challenge=fido2_module._payload_digest(b"payload"),
        origin=fido2_module._HATP_ORIGIN,
    )
    assertion = fido2_module._serialize_evidence(
        credential_id=wrong,
        authenticator_data=b"\x00" * 37,
        client_data_json=bytes(client_data),
        signature=b"unrelated-signature",
    )
    provider = fido2_module.Fido2HardwareProvider(
        credential_store=_HardwareStore({intended: _credential(signer=intended)})
    )
    outcome = provider.verify(
        canonical_payload=b"payload",
        signer_key_id=intended,
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        assertion=assertion,
    )
    assert outcome.signature_valid is False
    assert outcome.human_presence_proven is False


def test_blocking_finding_malformed_binding_signer_principal_conflict_is_accepted_and_published(tmp_path):
    """Reproduce the new defect as current behavior, keeping IV green.

    Both principals are active, but the binding authorizes one while its
    signer record names the other.  The resolver returns the signer's
    principal and the full path touches hardware and publishes evidence.
    """
    root = _setup_ag3(tmp_path)
    signer_id = "11" * 16
    trust = _Trust(
        _binding(principal="principal-binding", signer=signer_id),
        {signer_id: _signer(principal="principal-signer", signer=signer_id)},
        {"principal-binding": _principal("principal-binding"), "principal-signer": _principal("principal-signer")},
    )
    provider = _Provider()
    result = _run(root, trust, _HardwareStore({signer_id: _credential(signer=signer_id)}), provider)
    assert result.path.exists()
    assert provider.touch_calls == 1
    assert ceremony._resolve_deployment_binding_signer(
        root,
        trust,
        repository_id="repo-1",
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        hardware_credential_store_factory=lambda: _HardwareStore({signer_id: _credential(signer=signer_id)}),
    ) == ("principal-signer", signer_id)


def test_blocking_finding_signer_provider_profile_mismatch_is_accepted_and_published(tmp_path):
    """HSCE-REQ-024 requires this mismatch to fail; current code accepts it."""
    root = _setup_ag3(tmp_path)
    signer_id = "11" * 16
    trust = _Trust(
        _binding(signer=signer_id),
        {signer_id: _signer(signer=signer_id, profile="PIV")},
        {"principal-1": _principal()},
    )
    provider = _Provider()
    result = _run(root, trust, _HardwareStore({signer_id: _credential(signer=signer_id)}), provider)
    assert result.path.exists()
    assert provider.touch_calls == 1


def test_same_signer_binding_authority_rewrite_is_accepted_by_tuple_only_toctou_rule(tmp_path):
    """Characterize HSCE-REQ-083 exactly: only the identity tuple matters.

    This is contract-conforming under v1.2's literal text, but records the
    requested authority-field rewrite scenario for contract-gap assessment.
    """
    root = _setup_ag3(tmp_path)
    trust, hardware = _valid_state()
    provider = _Provider(on_touch=lambda: setattr(trust, "binding", replace(trust.binding, authority_scope="changed-scope")))
    result = _run(root, trust, hardware, provider)
    assert result.path.exists()
    assert provider.touch_calls == 1


def test_same_identity_credential_public_key_rewrite_is_not_detected_by_toctou_recheck(tmp_path):
    """Characterize another v1.2 tuple-only gap requested by the IV."""
    root = _setup_ag3(tmp_path)
    trust, hardware = _valid_state()
    provider = _Provider(
        on_touch=lambda: hardware.records.__setitem__(
            "11" * 16, replace(hardware.records["11" * 16], public_key=b"different-cose-key")
        )
    )
    result = _run(root, trust, hardware, provider)
    assert result.path.exists()
    assert provider.touch_calls == 1
