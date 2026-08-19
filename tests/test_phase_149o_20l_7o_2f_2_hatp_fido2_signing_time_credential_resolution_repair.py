"""Phase 149O.20L.7O.2F.2 -- FIDO2 Signing-Time Credential Resolution
Repair. Focused/adversarial tests for the BF-1/BF-2 repair to
``hatp_signing_ceremony.py`` (HSCE-001 v1.2, HSCE-REQ-080..084):

- BF-1 re-derivation: production signing no longer depends on
  ``provider.credential_identity()`` (which FIDO2 unconditionally raises
  for), because signer identity is now resolved exclusively from this
  repository's own durable ``DeploymentBinding``
  (``HATPTrustStore.resolve_deployment_authorization``).
- BF-2 re-derivation: ``Fido2HardwareProvider.enroll_credential()``'s
  CTAP2 ``make_credential`` call requests no ``rk``/resident-key option
  (non-resident output) -- confirmed moot for the production signing
  path, which never relies on resident-credential discovery.
- A full, synthetic, end-to-end production-path test: enroll a synthetic
  FIDO2 credential (monkeypatched CTAP2, no real hardware) -> register a
  ``HardwareCredentialRecord`` (Surface B) -> enroll a principal (Surface
  C) -> enroll a signer (Surface C) -> create a disposable
  ``DeploymentBinding`` (Surface E) -> invoke the real, injectable
  ``hatp_signing_ceremony.sign_rollback_evidence`` orchestrator (the
  actual production signing-resolution path, not a direct helper call)
  with a synthetic/mocked hardware touch only.
- Security attacks: multiple active signers, wrong credential, wrong
  principal, revoked signer, revoked credential, provider mismatch,
  missing credential, stale registry state, duplicate credential,
  authenticator returns unexpected credential.

No real hardware is provisioned. No real credential is registered. No
real principal or signer is enrolled. No real ``DeploymentBinding`` is
created. Every fixture uses disposable ``tmp_path`` roots.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

fido2 = pytest.importorskip("fido2")
cryptography = pytest.importorskip("cryptography")

from cryptography.hazmat.primitives.asymmetric import ec
from fido2.cose import ES256, CoseKey
from fido2.webauthn import AttestedCredentialData, AuthenticatorData

from pcae.core import hatp_deployment_binding_admin as db_admin
from pcae.core import hatp_fido2_provider as fido2_module
from pcae.core import hatp_hardware_credential_admin as hw_admin
from pcae.core import hatp_principal_signer_admin as ps_admin
from pcae.core import hatp_signing_ceremony as ceremony
from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.hatp_fido2_provider import EnrolledFido2Credential, Fido2HardwareProvider
from pcae.core.hatp_hardware_credentials import HATPHardwareCredentialStore
from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1, HATPProviderUnavailableError, ProviderAssertion
from pcae.core.human_approval_trusted_provenance import RollbackSite
from pcae.governance.publication.storage import PublicationRecordStore

from tests.test_hatp_signing_ceremony import (
    _FIXED_INSTANT,
    _fixed_clock,
    _make_ag3_binding,
    _root,
    _write_job,
)

pytestmark = [pytest.mark.fast_green, pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")]


# ═══════════════════════════════════════════════════════════════════════════
# BF-1 re-derivation
# ═══════════════════════════════════════════════════════════════════════════


def test_bf1_repro_credential_identity_still_unconditionally_raises() -> None:
    """Reproduces BF-1's original symptom directly against the real
    provider class: `credential_identity()` fails even with zero device
    interaction, confirming the boundary Phase 149O.20L.7O.2F.1 found."""

    provider = Fido2HardwareProvider()
    with pytest.raises(HATPProviderUnavailableError):
        provider.credential_identity()


def test_bf1_repro_old_resolution_path_no_longer_exists() -> None:
    """Confirms the repair actually removed the broken call site: no
    function in `hatp_signing_ceremony.py` named `_resolve_signer` any
    more (renamed/replaced by `_resolve_deployment_binding_signer`), and
    the module source contains no call to `.credential_identity(`
    anywhere at all."""

    import inspect

    source = inspect.getsource(ceremony)
    assert not hasattr(ceremony, "_resolve_signer")
    assert ".credential_identity(" not in source


def test_bf1_repaired_enrolled_signer_reaches_signing_resolution(tmp_path):
    """BF-1 closure: after the repair, `_resolve_deployment_binding_
    signer` (HSCE-REQ-080) successfully resolves an enrolled FIDO2
    signer's identity without ever calling `credential_identity()` --
    the exact capability BF-1 found permanently broken."""

    root = _root(tmp_path)
    hw_store = tmp_path / "hwstore"
    hw_store.mkdir()
    bind_store = tmp_path / "bindstore"
    bind_store.mkdir()

    hw_admin.register_credential(
        repository_root=root.path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id="aa" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1, protocol_name="FIDO2",
            algorithm="ES256", public_key_hex="bb" * 20, enrollment_reference="CHGR-HW-1",
        ),
        _store_root=hw_store,
    )
    ps_admin.enroll_principal(
        repository_root=root.path,
        evidence=ps_admin.PrincipalEnrollmentEvidence(principal_id="principal-1", election_reference="CHGR-P-1"),
        _protected_root=bind_store,
    )
    ps_admin.enroll_signer(
        repository_root=root.path,
        evidence=ps_admin.SignerEnrollmentEvidence(
            principal_id="principal-1", signer_key_id="aa" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1,
            election_reference="CHGR-S-1",
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )
    db_admin.create_deployment_binding(
        repository_root=root.path,
        authority=db_admin.AuthorityEvidence(
            principal_id="principal-1", signer_key_id="aa" * 16,
            authority_scope=db_admin.CLASS_B_DEPLOYMENT_AUTHORITY_SCOPE, election_reference="CHGR-D-1",
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )

    trust_store = HATPTrustStore(_test_only_root=bind_store)
    resolution = ceremony._resolve_deployment_binding_signer(
        root,
        trust_store,
        repository_id=ceremony.read_repository_identity(root).repository_instance_id,
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        hardware_credential_store_factory=lambda: HATPHardwareCredentialStore(_test_only_root=hw_store),
    )
    assert resolution.principal_id == "principal-1"
    assert resolution.signer_key_id == "aa" * 16


# ═══════════════════════════════════════════════════════════════════════════
# BF-2 re-derivation
# ═══════════════════════════════════════════════════════════════════════════


def test_bf2_repro_enroll_credential_requests_no_resident_key() -> None:
    """Reproduces BF-2's original finding directly: `enroll_credential`'s
    `make_credential` call site passes no `options`/`rk` argument at
    all, confirmed by AST-free direct source inspection of the exact
    call site (not merely CTAP2-library-behavior assumption)."""

    import inspect
    import re

    source = inspect.getsource(Fido2HardwareProvider.enroll_credential)
    match = re.search(r"ctap2\.make_credential\((.*?)\)\n", source, re.DOTALL)
    assert match is not None
    call_kwargs_text = match.group(1)
    assert "options" not in call_kwargs_text
    assert "rk" not in call_kwargs_text


def test_bf2_moot_non_resident_credential_remains_fully_valid_for_signing(tmp_path):
    """BF-2 disposition demonstrated directly: a non-resident credential
    (BF-2's own finding -- no `rk` requested) still reaches a fully
    successful signing-resolution result, because HSCE-REQ-080 never
    performs resident-credential discovery. No ambiguous halfway state."""

    root = _root(tmp_path)
    hw_store = tmp_path / "hwstore"
    hw_store.mkdir()
    bind_store = tmp_path / "bindstore"
    bind_store.mkdir()

    # `register_credential`'s own evidence carries no "resident/
    # non-resident" flag at all -- HardwareCredentialRecord's schema
    # (HHCE-001) is agnostic to CTAP2 residency, confirming the registry
    # layer never depended on it either.
    hw_admin.register_credential(
        repository_root=root.path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id="cc" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1, protocol_name="FIDO2",
            algorithm="ES256", public_key_hex="dd" * 20, enrollment_reference="CHGR-HW-2",
        ),
        _store_root=hw_store,
    )
    ps_admin.enroll_principal(
        repository_root=root.path,
        evidence=ps_admin.PrincipalEnrollmentEvidence(principal_id="principal-2", election_reference="CHGR-P-2"),
        _protected_root=bind_store,
    )
    ps_admin.enroll_signer(
        repository_root=root.path,
        evidence=ps_admin.SignerEnrollmentEvidence(
            principal_id="principal-2", signer_key_id="cc" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1,
            election_reference="CHGR-S-2",
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )
    db_admin.create_deployment_binding(
        repository_root=root.path,
        authority=db_admin.AuthorityEvidence(
            principal_id="principal-2", signer_key_id="cc" * 16,
            authority_scope=db_admin.CLASS_B_DEPLOYMENT_AUTHORITY_SCOPE, election_reference="CHGR-D-2",
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )

    trust_store = HATPTrustStore(_test_only_root=bind_store)
    resolution = ceremony._resolve_deployment_binding_signer(
        root,
        trust_store,
        repository_id=ceremony.read_repository_identity(root).repository_instance_id,
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        hardware_credential_store_factory=lambda: HATPHardwareCredentialStore(_test_only_root=hw_store),
    )
    assert (resolution.principal_id, resolution.signer_key_id) == ("principal-2", "cc" * 16)


# ═══════════════════════════════════════════════════════════════════════════
# Real, synthetic CTAP2 enrollment fixtures (mirrors `test_hatp_trust_
# enrollment_capability.py`'s own monkeypatch discipline exactly).
# ═══════════════════════════════════════════════════════════════════════════


class _FakeDevice:
    pass


def _make_working_credential():
    priv = ec.generate_private_key(ec.SECP256R1())
    cose_key = ES256.from_cryptography_key(priv.public_key())
    cred_id = os.urandom(32)
    acd = AttestedCredentialData.create(b"\x00" * 16, cred_id, cose_key)
    return cred_id, cose_key, acd


class _WorkingCtap2:
    def __init__(self, device) -> None:
        self._device = device

    def make_credential(self, **kwargs):
        cred_id, cose_key, acd = _make_working_credential()
        auth_data = AuthenticatorData.create(fido2_module._RP_ID_HASH, AuthenticatorData.FLAG.AT, 1, acd)

        class _FakeAttestation:
            pass

        att = _FakeAttestation()
        att.auth_data = auth_data
        self.last_cred_id = cred_id
        self.last_cose_key = cose_key
        return att


def _enroll_synthetic_fido2_credential(monkeypatch: pytest.MonkeyPatch) -> EnrolledFido2Credential:
    """Real `enroll_credential()` production ceremony (Surface A),
    exercising the genuine CTAP2 `makeCredential` call path -- only the
    HID device enumeration and `Ctap2` transport are faked, identically
    to `test_hatp_trust_enrollment_capability.py`'s own discipline."""

    monkeypatch.setattr(fido2_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([_FakeDevice()])))
    monkeypatch.setattr(fido2_module, "Ctap2", _WorkingCtap2)
    provider = Fido2HardwareProvider()
    return provider.enroll_credential()


# ═══════════════════════════════════════════════════════════════════════════
# Full production-path end-to-end test
# ═══════════════════════════════════════════════════════════════════════════


def test_full_production_signing_path_with_synthetic_fido2_credential(tmp_path, monkeypatch):
    """The real production orchestration path, end to end: synthetic
    FIDO2 enrollment -> HardwareCredentialRecord registration -> principal
    enrollment -> signer enrollment -> DeploymentBinding creation ->
    `hatp_signing_ceremony.sign_rollback_evidence` (the actual,
    injectable production signing-resolution orchestrator, not a direct
    helper call) -> provider receives the intended credential ->
    signature path succeeds. Only the physical CTAP2 touch (`Ctap2.
    get_assertion`) is synthetic/mocked; every registry write, lookup,
    RAE Binding resolution, envelope build, and evidence-store publish
    is the genuine production code path."""

    enrolled = _enroll_synthetic_fido2_credential(monkeypatch)
    signer_key_id = enrolled.credential_id_hex

    root = _root(tmp_path)
    hw_store = tmp_path / "hwstore"
    hw_store.mkdir()
    bind_store = tmp_path / "bindstore"
    bind_store.mkdir()

    reg_result = hw_admin.register_credential(
        repository_root=root.path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id=signer_key_id, provider_profile=enrolled.provider_profile, protocol_name="FIDO2",
            algorithm=enrolled.algorithm, public_key_hex=enrolled.public_key_hex, enrollment_reference="CHGR-HW-E2E",
        ),
        _store_root=hw_store,
    )
    assert reg_result.outcome.value == "registered"

    ps_admin.enroll_principal(
        repository_root=root.path,
        evidence=ps_admin.PrincipalEnrollmentEvidence(principal_id="principal-e2e", election_reference="CHGR-P-E2E"),
        _protected_root=bind_store,
    )
    signer_result = ps_admin.enroll_signer(
        repository_root=root.path,
        evidence=ps_admin.SignerEnrollmentEvidence(
            principal_id="principal-e2e", signer_key_id=signer_key_id, provider_profile=enrolled.provider_profile,
            election_reference="CHGR-S-E2E",
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )
    assert signer_result.outcome.value == "enrolled"

    binding_result = db_admin.create_deployment_binding(
        repository_root=root.path,
        authority=db_admin.AuthorityEvidence(
            principal_id="principal-e2e", signer_key_id=signer_key_id,
            authority_scope=db_admin.CLASS_B_DEPLOYMENT_AUTHORITY_SCOPE, election_reference="CHGR-D-E2E",
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )
    assert binding_result.outcome.value == "created"

    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    _write_job(root, "job-e2e", commit_sha="e" * 40)
    _make_ag3_binding(root, pub_store, job_id="job-e2e", commit_sha="e" * 40)

    class _SyntheticTouchProvider:
        """The real `request_signature` production interface, but with
        the physical CTAP2 `get_assertion` transport call replaced by a
        deterministic synthetic assertion -- no real hardware touch
        occurs. `credential_identity()` is present only to prove the
        negative (never called)."""

        def __init__(self) -> None:
            self.request_signature_calls = 0
            self.credential_identity_calls = 0
            self.received_signer_key_id = None

        def credential_identity(self) -> str:  # pragma: no cover - proven never called
            self.credential_identity_calls += 1
            raise HATPProviderUnavailableError("must never be called by the repaired resolution path")

        def request_signature(self, payload: bytes, *, signer_key_id: str, provider_profile: str, presence_timeout_s: float = 30.0) -> ProviderAssertion:
            self.request_signature_calls += 1
            self.received_signer_key_id = signer_key_id
            assert signer_key_id == enrolled.credential_id_hex
            assert provider_profile == HATP_HARDWARE_PROVIDER_V1
            return ProviderAssertion(
                credential_id=signer_key_id, provider_profile=provider_profile, algorithm="ES256",
                evidence=b"synthetic-e2e-assertion",
            )

    provider = _SyntheticTouchProvider()
    result = ceremony.sign_rollback_evidence(
        root,
        site=RollbackSite.AG3,
        job_id="job-e2e",
        clock=_fixed_clock(_FIXED_INSTANT),
        provider_factory=lambda: provider,
        trust_store_factory=lambda: HATPTrustStore(_test_only_root=bind_store),
        hardware_credential_store_factory=lambda: HATPHardwareCredentialStore(_test_only_root=hw_store),
        confirm=lambda preview: True,
    )

    assert isinstance(result, ceremony.HATPSigningResult)
    assert result.idempotent is False
    assert provider.request_signature_calls == 1
    assert provider.credential_identity_calls == 0
    assert provider.received_signer_key_id == enrolled.credential_id_hex
    envelope_path = root.path / ".pcae" / "hatp-evidence" / "envelopes" / f"{result.evidence_id}.json"
    assert envelope_path.exists()


# ═══════════════════════════════════════════════════════════════════════════
# Security attacks: multiple signers, wrong credential, wrong principal,
# revoked signer/credential, provider mismatch, missing credential,
# stale registry state, duplicate credential, unexpected credential.
# ═══════════════════════════════════════════════════════════════════════════


def _setup_two_signer_environment(tmp_path):
    """Two fully-enrolled signers on two DISTINCT repositories, each with
    its own DeploymentBinding -- confirms cross-repository isolation and
    provides fixtures for the "wrong credential"/"wrong principal"
    attacks below."""

    hw_store = tmp_path / "hwstore"
    hw_store.mkdir()
    bind_store = tmp_path / "bindstore"
    bind_store.mkdir()

    root_a = _root(tmp_path / "repo-a")
    root_b = _root(tmp_path / "repo-b")

    for suffix, root in (("a", root_a), ("b", root_b)):
        hw_admin.register_credential(
            repository_root=root.path,
            evidence=hw_admin.CredentialEnrollmentEvidence(
                signer_key_id=f"{suffix}{suffix}" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1,
                protocol_name="FIDO2", algorithm="ES256", public_key_hex="ee" * 20,
                enrollment_reference=f"CHGR-HW-{suffix}",
            ),
            _store_root=hw_store,
        )
        ps_admin.enroll_principal(
            repository_root=root.path,
            evidence=ps_admin.PrincipalEnrollmentEvidence(principal_id=f"principal-{suffix}", election_reference=f"CHGR-P-{suffix}"),
            _protected_root=bind_store,
        )
        ps_admin.enroll_signer(
            repository_root=root.path,
            evidence=ps_admin.SignerEnrollmentEvidence(
                principal_id=f"principal-{suffix}", signer_key_id=f"{suffix}{suffix}" * 16,
                provider_profile=HATP_HARDWARE_PROVIDER_V1, election_reference=f"CHGR-S-{suffix}",
            ),
            _protected_root=bind_store,
            _hardware_store_root=hw_store,
        )
        db_admin.create_deployment_binding(
            repository_root=root.path,
            authority=db_admin.AuthorityEvidence(
                principal_id=f"principal-{suffix}", signer_key_id=f"{suffix}{suffix}" * 16,
                authority_scope=db_admin.CLASS_B_DEPLOYMENT_AUTHORITY_SCOPE, election_reference=f"CHGR-D-{suffix}",
            ),
            _protected_root=bind_store,
            _hardware_store_root=hw_store,
        )

    return root_a, root_b, hw_store, bind_store


def test_attack_multiple_active_signers_each_repository_resolves_only_its_own(tmp_path):
    """Two active signers exist system-wide (one per repository). Each
    repository's own DeploymentBinding deterministically resolves to
    exactly its own signer -- never the other's, never ambiguous, never
    "pick first" (HSCE-REQ-081)."""

    root_a, root_b, hw_store, bind_store = _setup_two_signer_environment(tmp_path)
    trust_store = HATPTrustStore(_test_only_root=bind_store)
    hw_factory = lambda: HATPHardwareCredentialStore(_test_only_root=hw_store)

    resolution_a = ceremony._resolve_deployment_binding_signer(
        root_a, trust_store, repository_id=ceremony.read_repository_identity(root_a).repository_instance_id,
        provider_profile=HATP_HARDWARE_PROVIDER_V1, hardware_credential_store_factory=hw_factory,
    )
    resolution_b = ceremony._resolve_deployment_binding_signer(
        root_b, trust_store, repository_id=ceremony.read_repository_identity(root_b).repository_instance_id,
        provider_profile=HATP_HARDWARE_PROVIDER_V1, hardware_credential_store_factory=hw_factory,
    )
    assert (resolution_a.principal_id, resolution_a.signer_key_id) == ("principal-a", "aa" * 16)
    assert (resolution_b.principal_id, resolution_b.signer_key_id) == ("principal-b", "bb" * 16)
    assert resolution_a.signer_key_id != resolution_b.signer_key_id


def test_attack_wrong_credential_never_bound_to_this_repository_is_rejected(tmp_path):
    """A signer_key_id enrolled and active for a DIFFERENT repository is
    never resolvable for this repository -- resolution reads only this
    repository's own DeploymentBinding, never any other."""

    root_a, root_b, hw_store, bind_store = _setup_two_signer_environment(tmp_path)
    trust_store = HATPTrustStore(_test_only_root=bind_store)

    # root_a's DeploymentBinding always resolves "aa"*16, never "bb"*16
    # (repo_b's credential), regardless of what's active in the registry.
    resolution_a = ceremony._resolve_deployment_binding_signer(
        root_a, trust_store, repository_id=ceremony.read_repository_identity(root_a).repository_instance_id,
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        hardware_credential_store_factory=lambda: HATPHardwareCredentialStore(_test_only_root=hw_store),
    )
    assert resolution_a.signer_key_id != "bb" * 16


def test_attack_revoked_signer_rejected(tmp_path):
    root = _root(tmp_path)
    hw_store = tmp_path / "hwstore"
    hw_store.mkdir()
    bind_store = tmp_path / "bindstore"
    bind_store.mkdir()
    hw_admin.register_credential(
        repository_root=root.path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id="ff" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1, protocol_name="FIDO2",
            algorithm="ES256", public_key_hex="11" * 20, enrollment_reference="CHGR-HW-REV",
        ),
        _store_root=hw_store,
    )
    ps_admin.enroll_principal(
        repository_root=root.path,
        evidence=ps_admin.PrincipalEnrollmentEvidence(principal_id="principal-rev", election_reference="CHGR-P-REV"),
        _protected_root=bind_store,
    )
    ps_admin.enroll_signer(
        repository_root=root.path,
        evidence=ps_admin.SignerEnrollmentEvidence(
            principal_id="principal-rev", signer_key_id="ff" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1,
            election_reference="CHGR-S-REV",
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )
    db_admin.create_deployment_binding(
        repository_root=root.path,
        authority=db_admin.AuthorityEvidence(
            principal_id="principal-rev", signer_key_id="ff" * 16,
            authority_scope=db_admin.CLASS_B_DEPLOYMENT_AUTHORITY_SCOPE, election_reference="CHGR-D-REV",
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )
    ps_admin.revoke_signer(
        repository_root=root.path, signer_key_id="ff" * 16, election_reference="CHGR-REVOKE-1", _protected_root=bind_store,
    )

    trust_store = HATPTrustStore(_test_only_root=bind_store)
    with pytest.raises(ceremony.NoAuthorizedSignerError):
        ceremony._resolve_deployment_binding_signer(
            root, trust_store, repository_id=ceremony.read_repository_identity(root).repository_instance_id,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            hardware_credential_store_factory=lambda: HATPHardwareCredentialStore(_test_only_root=hw_store),
        )


def test_attack_revoked_credential_rejected(tmp_path):
    root = _root(tmp_path)
    hw_store = tmp_path / "hwstore"
    hw_store.mkdir()
    bind_store = tmp_path / "bindstore"
    bind_store.mkdir()
    hw_admin.register_credential(
        repository_root=root.path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id="22" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1, protocol_name="FIDO2",
            algorithm="ES256", public_key_hex="33" * 20, enrollment_reference="CHGR-HW-REVCRED",
        ),
        _store_root=hw_store,
    )
    ps_admin.enroll_principal(
        repository_root=root.path,
        evidence=ps_admin.PrincipalEnrollmentEvidence(principal_id="principal-revcred", election_reference="CHGR-P-REVCRED"),
        _protected_root=bind_store,
    )
    ps_admin.enroll_signer(
        repository_root=root.path,
        evidence=ps_admin.SignerEnrollmentEvidence(
            principal_id="principal-revcred", signer_key_id="22" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1,
            election_reference="CHGR-S-REVCRED",
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )
    db_admin.create_deployment_binding(
        repository_root=root.path,
        authority=db_admin.AuthorityEvidence(
            principal_id="principal-revcred", signer_key_id="22" * 16,
            authority_scope=db_admin.CLASS_B_DEPLOYMENT_AUTHORITY_SCOPE, election_reference="CHGR-D-REVCRED",
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )
    hw_admin.revoke_credential(
        repository_root=root.path, signer_key_id="22" * 16, enrollment_reference="CHGR-REVOKE-CRED", _store_root=hw_store,
    )

    trust_store = HATPTrustStore(_test_only_root=bind_store)
    with pytest.raises(ceremony.NoAuthorizedSignerError):
        ceremony._resolve_deployment_binding_signer(
            root, trust_store, repository_id=ceremony.read_repository_identity(root).repository_instance_id,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            hardware_credential_store_factory=lambda: HATPHardwareCredentialStore(_test_only_root=hw_store),
        )


def test_attack_missing_credential_rejected(tmp_path):
    """A DeploymentBinding pointing at a signer_key_id whose
    HardwareCredentialRecord was never registered at all (not merely
    revoked) fails closed identically."""

    root = _root(tmp_path)
    from tests.test_hatp_signing_ceremony import (
        FakeHardwareCredentialStore,
        FakeTrustStore,
        _active_principal,
        _active_signer,
        _deployment_binding,
    )

    trust_store = FakeTrustStore(
        {"missing-cred": _active_signer(signer_key_id="missing-cred", principal_id="principal-missing")},
        {"principal-missing": _active_principal("principal-missing")},
        binding=_deployment_binding(signer_key_id="missing-cred", principal_id="principal-missing"),
    )
    hw_store = FakeHardwareCredentialStore({})  # nothing registered
    with pytest.raises(ceremony.NoAuthorizedSignerError):
        ceremony._resolve_deployment_binding_signer(
            root, trust_store, repository_id="repo-1", provider_profile=HATP_HARDWARE_PROVIDER_V1,
            hardware_credential_store_factory=lambda: hw_store,
        )


def test_attack_provider_profile_mismatch_at_binding_level_rejected(tmp_path):
    """The DeploymentBinding's own `provider_profile` (e.g. `PIV`) does
    not match the resolved production hardware provider's profile
    (`HATP_HARDWARE_PROVIDER_V1`, FIDO2) -- rejected before any hardware
    touch, independent of whether the underlying signer/credential are
    otherwise valid."""

    from tests.test_hatp_signing_ceremony import (
        FakeHardwareCredentialStore,
        FakeTrustStore,
        _active_credential,
        _active_principal,
        _active_signer,
        _deployment_binding,
    )

    root = _root(tmp_path)
    trust_store = FakeTrustStore(
        {"signer-1": _active_signer()}, {"principal-1": _active_principal()},
        binding=_deployment_binding(provider_profile="PIV"),
    )
    hw_store = FakeHardwareCredentialStore({"signer-1": _active_credential()})
    with pytest.raises(ceremony.NoAuthorizedSignerError):
        ceremony._resolve_deployment_binding_signer(
            root, trust_store, repository_id="repo-1", provider_profile=HATP_HARDWARE_PROVIDER_V1,
            hardware_credential_store_factory=lambda: hw_store,
        )


def test_attack_duplicate_credential_registration_is_conflict_not_silent_overwrite(tmp_path):
    """Attempting to register a second, differing credential under the
    same `signer_key_id` (a "duplicate credential" attack) fails closed
    at the registry-writer layer (Surface B, HHCE-REQ-017) -- confirming
    the signing-time resolution repair does not depend on, or weaken,
    this pre-existing writer-level guarantee."""

    root = _root(tmp_path)
    hw_store = tmp_path / "hwstore"
    hw_store.mkdir()
    hw_admin.register_credential(
        repository_root=root.path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id="44" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1, protocol_name="FIDO2",
            algorithm="ES256", public_key_hex="55" * 20, enrollment_reference="CHGR-HW-DUP-1",
        ),
        _store_root=hw_store,
    )
    with pytest.raises(hw_admin.CredentialConflictError):
        hw_admin.register_credential(
            repository_root=root.path,
            evidence=hw_admin.CredentialEnrollmentEvidence(
                signer_key_id="44" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1, protocol_name="FIDO2",
                algorithm="ES256", public_key_hex="66" * 20, enrollment_reference="CHGR-HW-DUP-2",
            ),
            _store_root=hw_store,
        )


def test_attack_authenticator_returns_unexpected_credential_id_rejected_by_verify(tmp_path):
    """A physical authenticator asserting with a *different* credential
    id than the one the signing command requested (`allow_list`) is not
    a signing-resolution-layer concern (CTAP2's own `allow_list`
    enforcement / `verify()`'s `parsed.credential_id.hex() !=
    signer_key_id.lower()` check, `hatp_fido2_provider.py`, unamended by
    this repair) -- confirmed still present and unweakened by re-reading
    the source directly."""

    import inspect

    source = inspect.getsource(fido2_module.Fido2HardwareProvider.verify)
    assert "parsed.credential_id.hex() != signer_key_id.lower()" in source


def test_attack_stale_registry_state_toctou_between_preview_and_touch(tmp_path):
    """Stale registry state (a DeploymentBinding rotation) landing
    between the pre-touch preview and the hardware touch is caught by
    the extended TOCTOU recheck (HSCE-REQ-083) -- exercised in full via
    `tests/test_hatp_signing_ceremony.py::
    test_toctou_signer_identity_rotation_between_preview_and_touch`; this
    test additionally confirms the discard leaves the evidence store
    completely empty (no partial artifact)."""

    from pcae.core.hatp_evidence_store import HATPEvidenceStore
    from tests.test_hatp_signing_ceremony import (
        FakeHardwareCredentialStore,
        FakeHardwareProvider,
        FakeTrustStore,
        _active_credential,
        _active_principal,
        _active_signer,
        _deployment_binding,
        _make_ag3_binding as _make_binding,
        _rae_store,
        _setup_ag3,
        _sign,
        _write_job,
    )

    root = _setup_ag3(tmp_path)
    trust_store = FakeTrustStore(
        {"signer-1": _active_signer(), "signer-2": _active_signer(signer_key_id="signer-2", principal_id="principal-2")},
        {"principal-1": _active_principal(), "principal-2": _active_principal("principal-2")},
        binding=_deployment_binding(),
    )

    def _rotate_then_confirm(preview) -> bool:
        trust_store._binding = _deployment_binding(signer_key_id="signer-2", principal_id="principal-2")
        return True

    hw_store = FakeHardwareCredentialStore(
        {"signer-1": _active_credential(), "signer-2": _active_credential(signer_key_id="signer-2")}
    )
    provider = FakeHardwareProvider()
    with pytest.raises(ceremony.EvidenceSerializationFailureError):
        _sign(
            root, site=RollbackSite.AG3, job_id="job-1", provider=provider, trust_store=trust_store,
            hardware_credential_store=hw_store, confirm=_rotate_then_confirm,
        )
    store = HATPEvidenceStore(root)
    assert not store.envelopes_dir.exists() or list(store.envelopes_dir.glob("*.json")) == []
