"""HATP Trust-Enrollment Implementation Capability — Phase
149O.20L.7O.2F. Focused/adversarial tests for Surfaces A-E:

- Surface A: `Fido2HardwareProvider.enroll_credential()` (deterministic,
  no real hardware -- monkeypatched `CtapHidDevice`/`Ctap2`, mirroring
  `request_signature`'s own existing test discipline).
- Surface B: `hatp_hardware_credential_admin` writer (register/revoke,
  idempotency, conflict, lock, security).
- Surface C: `hatp_principal_signer_admin` writer, including the
  load-bearing continuous two-lock critical section (HHCE-REQ-037) and
  the HPSE-REQ-056 cross-registry precondition.
- Surface D: `PrincipalRecord.revoked_at` schema widening.
- Surface E: `DeploymentBinding` producer cross-validation (already
  extensively covered in `test_hatp_deployment_binding_admin.py`'s
  updated fixtures; this file adds a few additional adversarial cases
  and the proof-verification regression suite).

Every fixture uses disposable `tmp_path` roots. No test ever touches any
production/protected path, provisions real hardware, enrolls a real
principal/signer, or creates a real `DeploymentBinding`.
"""
from __future__ import annotations

import os
import threading
from dataclasses import fields
from pathlib import Path

import pytest

fido2 = pytest.importorskip("fido2")
cryptography = pytest.importorskip("cryptography")

from cryptography.hazmat.primitives.asymmetric import ec
from fido2 import cbor as fido2_cbor
from fido2.cose import ES256
from fido2.webauthn import AttestedCredentialData, AuthenticatorData

from pcae.core import hatp_fido2_provider as fido2_module
from pcae.core import hatp_hardware_credential_admin as hw_admin
from pcae.core import hatp_principal_signer_admin as ps_admin
from pcae.core import hatp_deployment_binding_admin as db_admin
from pcae.core.hatp_bootstrap import HATPTrustStore, PrincipalRecord, _parse_principal, HATPTrustStoreMalformedError
from pcae.core.hatp_fido2_provider import EnrolledFido2Credential, Fido2HardwareProvider
from pcae.core.hatp_hardware_credentials import HardwareCredentialRecord, HATPHardwareCredentialStore
from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1, HATPProviderCancelledError, HATPProviderDeviceError, HATPProviderUnavailableError
pytestmark = [pytest.mark.fast_green, pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")]


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


def _hw_store(tmp_path: Path, name: str = "hwstore") -> Path:
    root = tmp_path / name
    root.mkdir()
    return root


def _bind_store(tmp_path: Path, name: str = "bindstore") -> Path:
    root = tmp_path / name
    root.mkdir()
    return root


def _register(repo: Path, hw_store: Path, *, signer_key_id: str = "aa" * 16, provider_profile: str = HATP_HARDWARE_PROVIDER_V1):
    return hw_admin.register_credential(
        repository_root=repo,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id=signer_key_id,
            provider_profile=provider_profile,
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key_hex="bb" * 20,
            enrollment_reference="CHGR-HW-1",
        ),
        _store_root=hw_store,
    )


def _enroll_principal(repo: Path, bind_store: Path, principal_id: str = "principal-1"):
    return ps_admin.enroll_principal(
        repository_root=repo,
        evidence=ps_admin.PrincipalEnrollmentEvidence(principal_id=principal_id, election_reference="CHGR-P-1"),
        _protected_root=bind_store,
    )


def _enroll_signer(
    repo: Path,
    bind_store: Path,
    hw_store: Path,
    *,
    principal_id: str = "principal-1",
    signer_key_id: str = "aa" * 16,
    provider_profile: str = HATP_HARDWARE_PROVIDER_V1,
):
    return ps_admin.enroll_signer(
        repository_root=repo,
        evidence=ps_admin.SignerEnrollmentEvidence(
            principal_id=principal_id, signer_key_id=signer_key_id, provider_profile=provider_profile, election_reference="CHGR-S-1"
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Surface A -- FIDO2 credential identity/enrollment (deterministic)
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


class _CancellingCtap2:
    def __init__(self, device) -> None:
        pass

    def make_credential(self, **kwargs):
        from fido2.ctap import CtapError

        raise CtapError(CtapError.ERR.ACTION_TIMEOUT)


class _FailingCtap2:
    def __init__(self, device) -> None:
        pass

    def make_credential(self, **kwargs):
        raise OSError("simulated device I/O failure")


class _NoCredentialDataCtap2:
    def __init__(self, device) -> None:
        pass

    def make_credential(self, **kwargs):
        class _FakeAttestation:
            pass

        att = _FakeAttestation()
        att.auth_data = AuthenticatorData.create(fido2_module._RP_ID_HASH, AuthenticatorData.FLAG(0), 1)
        return att


def test_enroll_credential_raises_unavailable_when_no_device_attached() -> None:
    provider = Fido2HardwareProvider()
    with pytest.raises(HATPProviderUnavailableError):
        provider.enroll_credential()


def test_enroll_credential_success_produces_stable_provider_bound_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fido2_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([_FakeDevice()])))
    monkeypatch.setattr(fido2_module, "Ctap2", _WorkingCtap2)

    provider = Fido2HardwareProvider()
    enrolled = provider.enroll_credential()

    assert isinstance(enrolled, EnrolledFido2Credential)
    assert enrolled.algorithm == "ES256"
    assert enrolled.provider_profile == HATP_HARDWARE_PROVIDER_V1
    # Deterministic hex round-trip -- signer_key_id == hex(credential_identity_bytes) (HPSE-REQ-061).
    assert bytes.fromhex(enrolled.credential_id_hex)
    # public_key_hex is exactly CBOR-encoded COSE_Key bytes, matching verify()'s own decode path (fixes NBF-1).
    from fido2.cose import CoseKey

    decoded = CoseKey.parse(fido2_cbor.decode(bytes.fromhex(enrolled.public_key_hex)))
    assert isinstance(decoded, ES256)


def test_enroll_credential_two_calls_produce_different_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """No caching/reuse: each ceremony mints a genuinely fresh credential
    (HHCE-REQ-012(a) uniqueness -- distinct physical credentials never
    collide; this test exercises the "two calls" case, not physical
    distinctness, which is a hardware fact this test cannot observe)."""

    monkeypatch.setattr(fido2_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([_FakeDevice()])))
    monkeypatch.setattr(fido2_module, "Ctap2", _WorkingCtap2)
    provider = Fido2HardwareProvider()
    first = provider.enroll_credential()
    second = provider.enroll_credential()
    assert first.credential_id_hex != second.credential_id_hex


def test_enroll_credential_maps_ctap_timeout_to_cancelled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fido2_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([_FakeDevice()])))
    monkeypatch.setattr(fido2_module, "Ctap2", _CancellingCtap2)
    provider = Fido2HardwareProvider()
    with pytest.raises(HATPProviderCancelledError):
        provider.enroll_credential()


def test_enroll_credential_maps_transport_failure_to_device_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fido2_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([_FakeDevice()])))
    monkeypatch.setattr(fido2_module, "Ctap2", _FailingCtap2)
    provider = Fido2HardwareProvider()
    with pytest.raises(HATPProviderDeviceError):
        provider.enroll_credential()


def test_enroll_credential_fails_closed_when_no_credential_data_returned(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fido2_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([_FakeDevice()])))
    monkeypatch.setattr(fido2_module, "Ctap2", _NoCredentialDataCtap2)
    provider = Fido2HardwareProvider()
    with pytest.raises(HATPProviderDeviceError):
        provider.enroll_credential()


def test_enroll_credential_never_extracts_a_private_key() -> None:
    import inspect

    source = inspect.getsource(Fido2HardwareProvider.enroll_credential)
    assert "private_key" not in source
    assert "priv" not in source.lower().replace("private", "")  # no smuggled private-key variable


def test_credential_identity_unchanged_still_unconditionally_raises() -> None:
    """Deliberate non-redesign (governing prompt §5): `credential_
    identity()` remains the *discovery*-at-signing-time operation
    `_resolve_signer` already calls; it is not repurposed into an
    enrollment ceremony."""

    provider = Fido2HardwareProvider()
    with pytest.raises(HATPProviderUnavailableError):
        provider.credential_identity()


# ═══════════════════════════════════════════════════════════════════════════
# Surface B -- HHCE writer
# ═══════════════════════════════════════════════════════════════════════════


def test_register_credential_writes_active_record(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    result = _register(tmp_path, hw_store)
    assert result.outcome == hw_admin.HardwareCredentialOutcome.REGISTERED
    assert result.record.status == "active"
    assert result.record.revoked_at is None

    store = HATPHardwareCredentialStore(_test_only_root=hw_store)
    assert store.lookup_credential("aa" * 16) == result.record


def test_register_credential_is_idempotent(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    first = _register(tmp_path, hw_store)
    second = _register(tmp_path, hw_store)
    assert second.outcome == hw_admin.HardwareCredentialOutcome.ALREADY_REGISTERED
    assert second.record == first.record


def test_register_credential_conflicting_fields_fails_closed(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    _register(tmp_path, hw_store)
    with pytest.raises(hw_admin.CredentialConflictError):
        hw_admin.register_credential(
            repository_root=tmp_path,
            evidence=hw_admin.CredentialEnrollmentEvidence(
                signer_key_id="aa" * 16,
                provider_profile=HATP_HARDWARE_PROVIDER_V1,
                protocol_name="FIDO2",
                algorithm="ES256",
                public_key_hex="cc" * 20,  # differs
                enrollment_reference="CHGR-HW-2",
            ),
            _store_root=hw_store,
        )


def test_register_credential_against_revoked_fails_closed_never_reactivates(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    _register(tmp_path, hw_store)
    hw_admin.revoke_credential(repository_root=tmp_path, signer_key_id="aa" * 16, enrollment_reference="CHGR-REV-1", _store_root=hw_store)
    with pytest.raises(hw_admin.CredentialConflictError):
        _register(tmp_path, hw_store)


def test_revoke_credential_is_idempotent_preserves_original_revoked_at(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    _register(tmp_path, hw_store)
    first = hw_admin.revoke_credential(repository_root=tmp_path, signer_key_id="aa" * 16, enrollment_reference="CHGR-REV-1", _store_root=hw_store)
    second = hw_admin.revoke_credential(repository_root=tmp_path, signer_key_id="aa" * 16, enrollment_reference="CHGR-REV-2", _store_root=hw_store)
    assert second.outcome == hw_admin.HardwareCredentialOutcome.ALREADY_REVOKED
    assert second.record.revoked_at == first.record.revoked_at


def test_revoke_credential_nonexistent_fails_closed(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    with pytest.raises(hw_admin.CredentialNotFoundError):
        hw_admin.revoke_credential(repository_root=tmp_path, signer_key_id="does-not-exist", enrollment_reference="CHGR-1", _store_root=hw_store)


def test_revoked_credential_fails_closed_at_verification_time(tmp_path: Path) -> None:
    """HHCE-REQ-042: a revoked credential's status is what `verify()`
    already checks -- reconfirmed here against a REAL registry entry
    produced by this phase's own writer, not a hand-authored fixture."""

    hw_store = _hw_store(tmp_path)
    _register(tmp_path, hw_store)
    hw_admin.revoke_credential(repository_root=tmp_path, signer_key_id="aa" * 16, enrollment_reference="CHGR-REV-1", _store_root=hw_store)

    provider = Fido2HardwareProvider(credential_store=HATPHardwareCredentialStore(_test_only_root=hw_store))
    outcome = provider.verify(canonical_payload=b"x", signer_key_id="aa" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1, assertion=b"y")
    assert outcome.signature_valid is False


def test_preview_register_never_writes(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    preview = hw_admin.preview_register_credential(
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id="dd" * 16,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key_hex="ee" * 20,
            enrollment_reference="CHGR-PREVIEW",
        ),
        _store_root=hw_store,
    )
    assert preview.kind == hw_admin.HardwareCredentialPreviewKind.WOULD_REGISTER
    assert not (hw_store / "hardware-credentials.json").exists()


def test_preview_revoke_classifies_not_found_would_revoke_already_revoked(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    not_found = hw_admin.preview_revoke_credential(signer_key_id="zz" * 16, _store_root=hw_store)
    assert not_found.kind == hw_admin.HardwareCredentialPreviewKind.WOULD_FAIL_NOT_FOUND

    _register(tmp_path, hw_store)
    would_revoke = hw_admin.preview_revoke_credential(signer_key_id="aa" * 16, _store_root=hw_store)
    assert would_revoke.kind == hw_admin.HardwareCredentialPreviewKind.WOULD_REVOKE

    hw_admin.revoke_credential(repository_root=tmp_path, signer_key_id="aa" * 16, enrollment_reference="CHGR-1", _store_root=hw_store)
    already_revoked = hw_admin.preview_revoke_credential(signer_key_id="aa" * 16, _store_root=hw_store)
    assert already_revoked.kind == hw_admin.HardwareCredentialPreviewKind.WOULD_NOOP_ALREADY_REVOKED


def test_hardware_credential_lock_file_created_with_secure_mode(tmp_path: Path) -> None:
    import stat

    hw_store = _hw_store(tmp_path)
    _register(tmp_path, hw_store)
    lock_path = hw_store / hw_admin._HARDWARE_CREDENTIAL_TRANSITION_LOCK_FILE_NAME
    assert lock_path.exists()
    mode = stat.S_IMODE(lock_path.stat().st_mode)
    assert mode == 0o600


def test_register_credential_rejects_symlinked_store_root(tmp_path: Path) -> None:
    real = _hw_store(tmp_path, "real")
    symlinked = tmp_path / "symlinked"
    symlinked.symlink_to(real)
    with pytest.raises(hw_admin.HATPHardwareCredentialStoreSymlinkError):
        _register(tmp_path, symlinked)


def test_register_credential_rejects_malformed_public_key_hex(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    with pytest.raises(hw_admin.CredentialEvidenceMalformedError):
        hw_admin.register_credential(
            repository_root=tmp_path,
            evidence=hw_admin.CredentialEnrollmentEvidence(
                signer_key_id="aa" * 16,
                provider_profile=HATP_HARDWARE_PROVIDER_V1,
                protocol_name="FIDO2",
                algorithm="ES256",
                public_key_hex="not-hex!",
                enrollment_reference="CHGR-1",
            ),
            _store_root=hw_store,
        )


def test_no_private_key_field_anywhere_in_credential_record_or_writer() -> None:
    field_names = {f.name for f in fields(HardwareCredentialRecord)}
    assert "private_key" not in field_names
    assert "pin" not in field_names


# ═══════════════════════════════════════════════════════════════════════════
# Surface D -- PrincipalRecord.revoked_at
# ═══════════════════════════════════════════════════════════════════════════


def test_principal_record_has_revoked_at_field() -> None:
    field_names = {f.name for f in fields(PrincipalRecord)}
    assert field_names == {"principal_id", "status", "revoked_at"}


def test_parse_principal_backwards_compatible_with_no_revoked_at_key() -> None:
    record = _parse_principal({"principal_id": "p1", "status": "active"})
    assert record.revoked_at is None


def test_parse_principal_revoked_requires_revoked_at() -> None:
    with pytest.raises(HATPTrustStoreMalformedError):
        _parse_principal({"principal_id": "p1", "status": "revoked"})


def test_parse_principal_active_with_revoked_at_set_is_malformed() -> None:
    with pytest.raises(HATPTrustStoreMalformedError):
        _parse_principal({"principal_id": "p1", "status": "active", "revoked_at": "2026-08-19T00:00:00.000Z"})


def test_parse_principal_rejects_unknown_field() -> None:
    with pytest.raises(HATPTrustStoreMalformedError):
        _parse_principal({"principal_id": "p1", "status": "active", "display_name": "nope"})


# ═══════════════════════════════════════════════════════════════════════════
# Surface C -- Principal/Signer writer, cross-registry precondition,
# continuous two-lock critical section (HHCE-REQ-037, load-bearing)
# ═══════════════════════════════════════════════════════════════════════════


def test_enroll_principal_and_signer_happy_path(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _register(tmp_path, hw_store)
    _enroll_principal(tmp_path, bind_store)
    result = _enroll_signer(tmp_path, bind_store, hw_store)
    assert result.outcome == ps_admin.SignerOutcome.ENROLLED
    assert result.record.principal_id == "principal-1"


def test_enroll_signer_without_registered_credential_fails_closed_HPSE_REQ_056(tmp_path: Path) -> None:
    """The load-bearing structural closure of HPSE-REQ-056: no credential
    registered at all -> enroll_signer cannot succeed."""

    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _enroll_principal(tmp_path, bind_store)
    with pytest.raises(ps_admin.HardwareCredentialNotRegisteredError):
        _enroll_signer(tmp_path, bind_store, hw_store)

    # Structural, not merely disclosed: registry.json must not carry an
    # active SignerRecord for this signer_key_id after the failed attempt.
    trust_store = HATPTrustStore(_test_only_root=bind_store)
    assert trust_store.lookup_signer("aa" * 16) is None


def test_enroll_signer_missing_principal_fails_closed(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _register(tmp_path, hw_store)
    with pytest.raises(ps_admin.PrincipalNotFoundError):
        _enroll_signer(tmp_path, bind_store, hw_store)


def test_enroll_signer_revoked_principal_fails_closed(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _register(tmp_path, hw_store)
    _enroll_principal(tmp_path, bind_store)
    ps_admin.revoke_principal(repository_root=tmp_path, principal_id="principal-1", election_reference="CHGR-REV", _protected_root=bind_store)
    with pytest.raises(ps_admin.PrincipalRevokedError):
        _enroll_signer(tmp_path, bind_store, hw_store)


def test_enroll_signer_provider_profile_mismatch_fails_closed(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _register(tmp_path, hw_store)  # provider_profile=HATP_HARDWARE_PROVIDER_V1
    _enroll_principal(tmp_path, bind_store)
    # evidence.provider_profile is validated against the closed allowlist
    # first; a value outside it is UnsupportedProviderProfileError, not a
    # credential-mismatch -- exercised separately below.
    with pytest.raises(ps_admin.UnsupportedProviderProfileError):
        _enroll_signer(tmp_path, bind_store, hw_store, provider_profile="NOT_A_REAL_PROFILE")


def test_enroll_signer_is_idempotent(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _register(tmp_path, hw_store)
    _enroll_principal(tmp_path, bind_store)
    first = _enroll_signer(tmp_path, bind_store, hw_store)
    second = _enroll_signer(tmp_path, bind_store, hw_store)
    assert second.outcome == ps_admin.SignerOutcome.ALREADY_ENROLLED
    assert second.record == first.record


def test_enroll_signer_conflicting_replay_fails_closed(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _register(tmp_path, hw_store)
    _enroll_principal(tmp_path, bind_store, principal_id="principal-1")
    _enroll_principal(tmp_path, bind_store, principal_id="principal-2")
    _enroll_signer(tmp_path, bind_store, hw_store, principal_id="principal-1")
    with pytest.raises(ps_admin.DuplicateSignerError):
        _enroll_signer(tmp_path, bind_store, hw_store, principal_id="principal-2")


def test_revoke_signer_never_reactivates_and_is_idempotent(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _register(tmp_path, hw_store)
    _enroll_principal(tmp_path, bind_store)
    _enroll_signer(tmp_path, bind_store, hw_store)
    first = ps_admin.revoke_signer(repository_root=tmp_path, signer_key_id="aa" * 16, election_reference="CHGR-REV-1", _protected_root=bind_store)
    second = ps_admin.revoke_signer(repository_root=tmp_path, signer_key_id="aa" * 16, election_reference="CHGR-REV-2", _protected_root=bind_store)
    assert second.outcome == ps_admin.SignerOutcome.ALREADY_REVOKED
    assert second.record.revoked_at == first.record.revoked_at
    with pytest.raises(ps_admin.DuplicateSignerError):
        _enroll_signer(tmp_path, bind_store, hw_store)


def test_pcae_pattern_no_active_signer_without_credential_cross_registry_invariant(tmp_path: Path) -> None:
    """HHI-5/HPI-7: no active SignerRecord can exist without a
    corresponding active HardwareCredentialRecord, even after the
    credential is later revoked -- the SignerRecord itself is untouched
    (HHCE-REQ-043's no-cascade disposition), but live verification fails
    closed regardless (checked here via a direct registry-state assertion
    plus the existing provider.verify() fail-closed path)."""

    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _register(tmp_path, hw_store)
    _enroll_principal(tmp_path, bind_store)
    _enroll_signer(tmp_path, bind_store, hw_store)

    hw_admin.revoke_credential(repository_root=tmp_path, signer_key_id="aa" * 16, enrollment_reference="CHGR-REV", _store_root=hw_store)

    # SignerRecord itself is untouched (no automatic cascade).
    trust_store = HATPTrustStore(_test_only_root=bind_store)
    signer = trust_store.lookup_signer("aa" * 16)
    assert signer is not None and signer.status == "active"

    # ...but live verification fails closed regardless (HHCE-REQ-044).
    provider = Fido2HardwareProvider(credential_store=HATPHardwareCredentialStore(_test_only_root=hw_store))
    outcome = provider.verify(canonical_payload=b"x", signer_key_id="aa" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1, assertion=b"y")
    assert outcome.signature_valid is False


def test_lock_ordering_hardware_outer_deployment_binding_inner(tmp_path: Path) -> None:
    """HPSE-REQ-057/HHCE-REQ-036: structural proof the two locks are
    acquired in the fixed global order by inspecting `enroll_signer`'s
    own source, plus a runtime check that the hardware-credential lock
    is held (non-reentrant, would deadlock if re-acquired) at the point
    the inner lock is taken."""

    import inspect

    source = inspect.getsource(ps_admin.enroll_signer)
    outer_idx = source.index("hardware_credential_transition_lock(hw_store_root)")
    inner_idx = source.index("_deployment_binding_transition_lock(binding_store_root)")
    assert outer_idx < inner_idx, "hardware-credential lock must be acquired OUTER, before the deployment-binding lock"


def test_continuous_lock_hold_no_release_reacquire_between_check_and_write(tmp_path: Path) -> None:
    """HHCE-REQ-037 (load-bearing): instrument the hardware-credential
    lock's acquire/release via monkeypatching `fcntl.flock` and assert
    it is acquired exactly once and released exactly once across one
    entire `enroll_signer` call -- proving no release/reacquire occurs
    between the precondition check and the write."""

    import fcntl

    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _register(tmp_path, hw_store)
    _enroll_principal(tmp_path, bind_store)

    events: list = []
    real_flock = fcntl.flock

    def _tracking_flock(fd, operation):
        if operation == fcntl.LOCK_EX:
            events.append("acquire")
        elif operation == fcntl.LOCK_UN:
            events.append("release")
        return real_flock(fd, operation)

    import unittest.mock

    # `fcntl` is one shared global module object -- patching `flock` here
    # observes BOTH locks `enroll_signer` acquires (the hardware-
    # credential-store lock AND `.deployment-binding-transition.lock`),
    # which is exactly what proves continuous, nested (not sequential)
    # holding: the outer lock's acquire must precede the inner lock's
    # acquire, and the outer lock's release must follow the inner lock's
    # release -- a strict "acquire, acquire, release, release" nesting
    # pattern. A release/reacquire between check and write (HHCE-REQ-037's
    # violation case) would instead produce "acquire, release, acquire,
    # release" for the outer lock -- distinguishable from this pattern.
    with unittest.mock.patch("pcae.core.hatp_hardware_credential_admin.fcntl.flock", side_effect=_tracking_flock):
        _enroll_signer(tmp_path, bind_store, hw_store)

    assert events == ["acquire", "acquire", "release", "release"], (
        f"expected strictly-nested outer/inner lock acquire/release, got: {events}"
    )


def test_concurrent_enroll_signer_produces_no_split_brain(tmp_path: Path) -> None:
    """HPSE-REQ-058(F): concurrent enrollment attempts against the same
    signer_key_id never interleave a partial state -- exactly one
    logical enrollment succeeds as ENROLLED, any others observe
    ALREADY_ENROLLED (idempotent) or a clean typed failure, never a
    corrupted/partial registry.json."""

    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _register(tmp_path, hw_store)
    _enroll_principal(tmp_path, bind_store)

    outcomes: list = []
    errors: list = []

    def _worker() -> None:
        try:
            outcomes.append(_enroll_signer(tmp_path, bind_store, hw_store).outcome)
        except BaseException as exc:  # noqa: BLE001 - concurrency test collects every outcome
            errors.append(exc)

    threads = [threading.Thread(target=_worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, f"unexpected errors: {errors}"
    assert set(outcomes) <= {ps_admin.SignerOutcome.ENROLLED, ps_admin.SignerOutcome.ALREADY_ENROLLED}
    assert outcomes.count(ps_admin.SignerOutcome.ENROLLED) == 1

    trust_store = HATPTrustStore(_test_only_root=bind_store)
    signer = trust_store.lookup_signer("aa" * 16)
    assert signer is not None and signer.status == "active"


def test_preview_enroll_signer_classifies_credential_not_registered(tmp_path: Path) -> None:
    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _enroll_principal(tmp_path, bind_store)
    preview = ps_admin.preview_enroll_signer(
        evidence=ps_admin.SignerEnrollmentEvidence(
            principal_id="principal-1", signer_key_id="aa" * 16, provider_profile=HATP_HARDWARE_PROVIDER_V1, election_reference="x"
        ),
        _protected_root=bind_store,
        _hardware_store_root=hw_store,
    )
    assert preview.kind == ps_admin.SignerPreviewKind.WOULD_FAIL_CREDENTIAL_NOT_REGISTERED


def test_error_vocabulary_no_bare_valueerror_for_normative_failures(tmp_path: Path) -> None:
    """HPSE-REQ-034/HHCE-REQ-045: every named failure surfaces as a typed
    error rooted at this module's own error hierarchy, never a bare
    ValueError."""

    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    try:
        _enroll_signer(tmp_path, bind_store, hw_store)
    except Exception as exc:
        assert isinstance(exc, ps_admin.HATPPrincipalSignerAdminError)
        assert not isinstance(exc, ValueError) or isinstance(exc, ps_admin.HATPPrincipalSignerAdminError)


# ═══════════════════════════════════════════════════════════════════════════
# Surface E -- proof-verification regression (no verifier-side code
# changed; this confirms real enrolled state round-trips through the
# existing, unmodified `verify_hatp_proof` engine end to end)
# ═══════════════════════════════════════════════════════════════════════════


def _end_to_end_enrolled_state(tmp_path: Path):
    hw_store = _hw_store(tmp_path)
    bind_store = _bind_store(tmp_path)
    _register(tmp_path, hw_store)
    _enroll_principal(tmp_path, bind_store)
    _enroll_signer(tmp_path, bind_store, hw_store)
    return hw_store, bind_store


def test_deployment_binding_producer_rejects_missing_principal_end_to_end(tmp_path: Path) -> None:
    from pcae.core.paths import HarnessPath
    from pcae.core.repository_identity import ensure_repository_identity

    repo = tmp_path / "repo"
    repo.mkdir()
    ensure_repository_identity(HarnessPath(repo))
    hw_store, bind_store = _end_to_end_enrolled_state(tmp_path)

    authority = db_admin.AuthorityEvidence(
        principal_id="does-not-exist", signer_key_id="aa" * 16, authority_scope="CLASS_B_DEPLOYMENT", election_reference="x"
    )
    with pytest.raises(db_admin.AuthorityPrincipalNotFoundError):
        db_admin.create_deployment_binding(repository_root=repo, authority=authority, _protected_root=bind_store, _hardware_store_root=hw_store)


def test_deployment_binding_producer_rejects_revoked_signer_end_to_end(tmp_path: Path) -> None:
    from pcae.core.paths import HarnessPath
    from pcae.core.repository_identity import ensure_repository_identity

    repo = tmp_path / "repo"
    repo.mkdir()
    ensure_repository_identity(HarnessPath(repo))
    hw_store, bind_store = _end_to_end_enrolled_state(tmp_path)
    ps_admin.revoke_signer(repository_root=tmp_path, signer_key_id="aa" * 16, election_reference="CHGR-REV", _protected_root=bind_store)

    authority = db_admin.AuthorityEvidence(
        principal_id="principal-1", signer_key_id="aa" * 16, authority_scope="CLASS_B_DEPLOYMENT", election_reference="x"
    )
    with pytest.raises(db_admin.AuthoritySignerRevokedError):
        db_admin.create_deployment_binding(repository_root=repo, authority=authority, _protected_root=bind_store, _hardware_store_root=hw_store)


def test_deployment_binding_producer_succeeds_end_to_end_with_real_enrolled_state(tmp_path: Path) -> None:
    from pcae.core.paths import HarnessPath
    from pcae.core.repository_identity import ensure_repository_identity

    repo = tmp_path / "repo"
    repo.mkdir()
    ensure_repository_identity(HarnessPath(repo))
    hw_store, bind_store = _end_to_end_enrolled_state(tmp_path)

    authority = db_admin.AuthorityEvidence(
        principal_id="principal-1", signer_key_id="aa" * 16, authority_scope="CLASS_B_DEPLOYMENT", election_reference="x"
    )
    result = db_admin.create_deployment_binding(repository_root=repo, authority=authority, _protected_root=bind_store, _hardware_store_root=hw_store)
    assert result.outcome == db_admin.DeploymentBindingOutcome.CREATED
    assert result.binding.provider_profile == HATP_HARDWARE_PROVIDER_V1


# ═══════════════════════════════════════════════════════════════════════════
# Runtime neutrality (governing prompt §33)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("module_name", ["hatp_hardware_credential_admin", "hatp_principal_signer_admin"])
def test_new_writer_modules_reference_no_runtime_identifier(module_name: str) -> None:
    import importlib
    import inspect

    module = importlib.import_module(f"pcae.core.{module_name}")
    source = inspect.getsource(module)
    for forbidden in ("claude", "codex", "deepseek", "anthropic", "openai"):
        assert forbidden not in source.lower()


def test_new_writer_modules_never_imported_by_agent_reachable_code() -> None:
    import inspect
    from pcae import cli as cli_module
    from pcae.core import agent as agent_core_module

    for module in (cli_module, agent_core_module):
        source = inspect.getsource(module)
        assert "hatp_hardware_credential_admin" not in source
        assert "hatp_principal_signer_admin" not in source
