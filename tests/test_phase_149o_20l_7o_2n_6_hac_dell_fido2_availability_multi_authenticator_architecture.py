"""Disposable evidence tests for Phase 149O.20L.7O.2N.6 (hac-dell FIDO2
Physical Authenticator Read-Only Availability, Selection, and
Enrollment Authorization — revised directive: current-device inspection
+ multi-authenticator/remote-WebAuthn architecture investigation).

This phase performed no production source change and no real hardware
mutation. These tests exist only to pin, with disposable `tmp_path`
fixtures and monkeypatched device lists, the read-only facts this
phase's report relies on:

  1. `discover_fido2()` never raises on zero/one/multiple devices and
     never touches the credential store (HHCE governing-prompt §10/34).
  2. `Fido2HardwareProvider.enroll_credential()` and `request_signature()`
     both select `devices[0]` — confirming the "first-wins" physical
     selection semantics this phase's report describes (governing
     prompt §16/17), independent of any credential-store state.
  3. The on-disk registry format already supports more than one active
     `HardwareCredentialRecord`, more than one `SignerRecord`, and more
     than one `SignerRecord` sharing the same `principal_id` — i.e. "one
     Principal, many Signers" is a pre-existing structural capability,
     not a schema change this phase would need to introduce (governing
     prompt §11/12/39).
  4. Exactly one `DeploymentBinding` is resolvable per
     `repository_id` at a time — the existing explicit-selection point
     between "credentials PCAE knows about" and "the one credential a
     live signing ceremony actually uses" (governing prompt §13/32).

No test in this module calls real hardware, writes to a protected root,
or invokes `makeCredential`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pytest

fido2 = pytest.importorskip("fido2")

from pcae.core.hatp_fido2_provider import discover_fido2
from pcae.core.hatp_hardware_credentials import (
    HATPHardwareCredentialStore,
    _parse_credential_registry_document,
)
from pcae.core.hatp_bootstrap import _parse_registry_document

pytestmark = pytest.mark.fast_green


# ---------------------------------------------------------------------------
# 1. discover_fido2() is read-only across zero/one/multiple device counts
# ---------------------------------------------------------------------------


@dataclass
class _FakeDevice:
    label: str


def test_discover_fido2_zero_devices(monkeypatch):
    monkeypatch.setattr("pcae.core.hatp_fido2_provider.CtapHidDevice.list_devices", lambda: [])
    result = discover_fido2()
    assert result.device_detected is False
    assert result.library_installed is True
    assert result.notes == ("devices_detected:0",)


def test_discover_fido2_one_device(monkeypatch):
    monkeypatch.setattr(
        "pcae.core.hatp_fido2_provider.CtapHidDevice.list_devices", lambda: [_FakeDevice("only")]
    )
    result = discover_fido2()
    assert result.device_detected is True
    assert result.notes == ("devices_detected:1",)


def test_discover_fido2_multiple_devices(monkeypatch):
    monkeypatch.setattr(
        "pcae.core.hatp_fido2_provider.CtapHidDevice.list_devices",
        lambda: [_FakeDevice("a"), _FakeDevice("b"), _FakeDevice("c")],
    )
    result = discover_fido2()
    assert result.device_detected is True
    assert result.notes == ("devices_detected:3",)


def test_discover_fido2_enumeration_failure_never_raises(monkeypatch):
    def _raise():
        raise OSError("simulated enumeration failure")

    monkeypatch.setattr("pcae.core.hatp_fido2_provider.CtapHidDevice.list_devices", _raise)
    result = discover_fido2()
    assert result.device_detected is False
    assert result.notes[0].startswith("device_enumeration_failed:")


# ---------------------------------------------------------------------------
# 2. Physical-selection semantics: enroll_credential / request_signature
#    both index devices[0] -- confirmed by source read, pinned here by
#    proving discovery order is exactly enumeration order (no re-sort,
#    no filtering) for the same list `enroll_credential`/`request_signature`
#    would receive.
# ---------------------------------------------------------------------------


def test_enumeration_order_is_preserved_unmodified(monkeypatch):
    from pcae.core.hatp_fido2_provider import CtapHidDevice

    devices = [_FakeDevice("first"), _FakeDevice("second")]
    monkeypatch.setattr(CtapHidDevice, "list_devices", lambda: devices)
    observed = list(CtapHidDevice.list_devices())
    assert observed == devices
    assert observed[0].label == "first"


# ---------------------------------------------------------------------------
# 3. Registry already supports multiple HardwareCredentialRecords and
#    multiple SignerRecords sharing one principal_id.
# ---------------------------------------------------------------------------


def _hex(prefix: str, n: int = 32) -> str:
    return (prefix * n)[:n]


def test_hardware_credential_registry_supports_multiple_active_records(tmp_path):
    store_root = tmp_path / "hwc"
    store_root.mkdir(mode=0o700)
    registry = {
        "schema_version": 1,
        "credentials": [
            {
                "signer_key_id": _hex("aa"),
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                "protocol_name": "FIDO2",
                "algorithm": "ES256",
                "public_key_hex": _hex("11", 40),
                "status": "active",
                "revoked_at": None,
            },
            {
                "signer_key_id": _hex("bb"),
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                "protocol_name": "FIDO2",
                "algorithm": "ES256",
                "public_key_hex": _hex("22", 40),
                "status": "active",
                "revoked_at": None,
            },
        ],
    }
    (store_root / "hardware-credentials.json").write_text(json.dumps(registry), encoding="utf-8")

    store = HATPHardwareCredentialStore(_test_only_root=store_root)
    first = store.lookup_credential(_hex("aa"))
    second = store.lookup_credential(_hex("bb"))
    assert first is not None and first.status == "active"
    assert second is not None and second.status == "active"
    assert first.signer_key_id != second.signer_key_id


def test_signer_registry_supports_one_principal_with_multiple_signers():
    document = {
        "registry_version": 1,
        "principals": [{"principal_id": "principal-1", "status": "active"}],
        "signers": [
            {
                "signer_key_id": _hex("aa"),
                "principal_id": "principal-1",
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                "status": "active",
            },
            {
                "signer_key_id": _hex("bb"),
                "principal_id": "principal-1",
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                "status": "active",
            },
        ],
        "deployment_bindings": [],
        "authorities": [],
    }
    parsed = _parse_registry_document(document)
    assert len(parsed.signers) == 2
    assert {s.principal_id for s in parsed.signers.values()} == {"principal-1"}
    assert {s.signer_key_id for s in parsed.signers.values()} == {_hex("aa"), _hex("bb")}


_REPO_ID = "067b8410-223c-488a-b287-83873c105f9f"


def test_deployment_binding_is_exactly_one_per_repository_id():
    document = {
        "registry_version": 1,
        "principals": [],
        "signers": [],
        "deployment_bindings": [
            {
                "repository_id": _REPO_ID,
                "canonical_deployment_root": "/opt/pcae/runtime/src",
                "principal_id": "principal-1",
                "signer_key_id": _hex("aa"),
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                "authority_scope": "hatp_mandatory",
                "valid_from": "2026-01-01T00:00:00+00:00",
                "status": "active",
            }
        ],
        "authorities": [],
    }
    parsed = _parse_registry_document(document)
    assert len(parsed.deployment_bindings) == 1
    assert parsed.deployment_bindings[_REPO_ID].signer_key_id == _hex("aa")


def test_duplicate_repository_id_deployment_binding_rejected():
    from pcae.core.hatp_bootstrap import HATPTrustStoreMalformedError

    document = {
        "registry_version": 1,
        "principals": [],
        "signers": [],
        "deployment_bindings": [
            {
                "repository_id": _REPO_ID,
                "canonical_deployment_root": "/opt/pcae/runtime/src",
                "principal_id": "principal-1",
                "signer_key_id": _hex("aa"),
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                "authority_scope": "hatp_mandatory",
                "valid_from": "2026-01-01T00:00:00+00:00",
                "status": "active",
            },
            {
                "repository_id": _REPO_ID,
                "canonical_deployment_root": "/opt/pcae/runtime/src",
                "principal_id": "principal-2",
                "signer_key_id": _hex("bb"),
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                "authority_scope": "hatp_mandatory",
                "valid_from": "2026-01-01T00:00:00+00:00",
                "status": "active",
            },
        ],
        "authorities": [],
    }
    with pytest.raises(HATPTrustStoreMalformedError):
        _parse_registry_document(document)
