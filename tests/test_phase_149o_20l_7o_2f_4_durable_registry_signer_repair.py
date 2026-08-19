"""Defensive repair coverage for Phase 149O.20L.7O.2F.4.

All state is disposable and synthetic.  Hardware interaction is represented
only by the existing test provider boundary.
"""
from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

from pcae.core import hatp_signing_ceremony as ceremony
from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1, HATPProviderUnavailableError
from pcae.core.human_approval_trusted_provenance import RollbackSite
from test_phase_149o_20l_7o_2f_3_independent_verification import (
    _HardwareStore,
    _Provider,
    _Trust,
    _binding,
    _credential,
    _principal,
    _run,
    _setup_ag3,
    _signer,
    _valid_state,
)


def _published(root) -> list[Path]:
    envelope_dir = root.path / ".pcae" / "hatp-evidence" / "envelopes"
    return list(envelope_dir.glob("*.json")) if envelope_dir.exists() else []


def test_valid_coherent_state_returns_complete_immutable_resolution_and_signs(tmp_path):
    root = _setup_ag3(tmp_path)
    trust, hardware = _valid_state()
    provider = _Provider()
    resolution = ceremony._resolve_deployment_binding_signer(
        root,
        trust,
        repository_id="repo-1",
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        hardware_credential_store_factory=lambda: hardware,
    )
    assert resolution.principal_id == "principal-1"
    assert resolution.signer_key_id == "11" * 16
    assert resolution.binding == trust.binding
    assert resolution.signer == trust.signers["11" * 16]
    assert resolution.principal == trust.principals["principal-1"]
    assert resolution.credential == hardware.records["11" * 16]
    result = _run(root, trust, hardware, provider)
    assert result.path.exists()
    assert provider.touch_calls == 1


@pytest.mark.parametrize(
    "case,mutate,error",
    [
        (
            "binding-signer-principal-conflict",
            lambda trust, _hardware: trust.signers.__setitem__(
                "11" * 16, _signer(principal="principal-other")
            ),
            "SignerRecord principal_id",
        ),
        (
            "signer-provider-conflict",
            lambda trust, _hardware: trust.signers.__setitem__(
                "11" * 16, _signer(profile="PIV")
            ),
            "SignerRecord provider_profile",
        ),
        (
            "credential-provider-conflict",
            lambda _trust, hardware: hardware.records.__setitem__(
                "11" * 16, _credential(profile="PIV")
            ),
            "hardware credential.*provider_profile",
        ),
        (
            "missing-principal",
            lambda trust, _hardware: trust.principals.clear(),
            "principal_id.*not active",
        ),
        (
            "missing-signer",
            lambda trust, _hardware: trust.signers.clear(),
            "not an active authorized signer",
        ),
        (
            "missing-credential",
            lambda _trust, hardware: hardware.records.clear(),
            "no active HardwareCredentialRecord",
        ),
        (
            "revoked-principal",
            lambda trust, _hardware: trust.principals.__setitem__(
                "principal-1", _principal(status="revoked")
            ),
            "principal_id.*not active",
        ),
        (
            "revoked-signer",
            lambda trust, _hardware: trust.signers.__setitem__(
                "11" * 16, _signer(status="revoked")
            ),
            "not an active authorized signer",
        ),
        (
            "revoked-credential",
            lambda _trust, hardware: hardware.records.__setitem__(
                "11" * 16, _credential(status="revoked")
            ),
            "no active HardwareCredentialRecord",
        ),
        (
            "revoked-binding",
            lambda trust, _hardware: setattr(trust, "binding", replace(trust.binding, status="revoked")),
            "no active DeploymentBinding",
        ),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_initial_inconsistent_or_inactive_state_fails_before_touch_and_publication(
    tmp_path, case, mutate, error
):
    root = _setup_ag3(tmp_path)
    trust, hardware = _valid_state()
    mutate(trust, hardware)
    provider = _Provider()
    if case == "revoked-binding":
        trust.binding = None  # production resolution filters non-active bindings
    with pytest.raises(ceremony.NoAuthorizedSignerError, match=error):
        _run(root, trust, hardware, provider)
    assert provider.touch_calls == 0
    assert _published(root) == []


def _write_trust_registry(
    store_root: Path,
    *,
    repository_id: str,
    deployment_root: str,
    binding_principal: str = "principal-1",
    signer_principal: str = "principal-1",
    signer_profile: str = HATP_HARDWARE_PROVIDER_V1,
) -> None:
    store_root.mkdir()
    (store_root / "registry.json").write_text(
        json.dumps(
            {
                "registry_version": 1,
                "principals": [
                    {"principal_id": "principal-1", "status": "active", "revoked_at": None},
                    {"principal_id": "principal-2", "status": "active", "revoked_at": None},
                ],
                "signers": [
                    {
                        "signer_key_id": "11" * 16,
                        "principal_id": signer_principal,
                        "provider_profile": signer_profile,
                        "status": "active",
                        "revoked_at": None,
                    }
                ],
                "authorities": [],
                "deployment_bindings": [
                    {
                        "repository_id": repository_id,
                        "canonical_deployment_root": deployment_root,
                        "principal_id": binding_principal,
                        "signer_key_id": "11" * 16,
                        "provider_profile": HATP_HARDWARE_PROVIDER_V1,
                        "authority_scope": "CLASS_B_DEPLOYMENT",
                        "valid_from": "2026-08-19T00:00:00.000Z",
                        "status": "active",
                        "revoked_at": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "binding_principal,signer_principal,signer_profile,error",
    [
        ("principal-1", "principal-2", HATP_HARDWARE_PROVIDER_V1, "SignerRecord principal_id"),
        ("principal-1", "principal-1", "PIV", "SignerRecord provider_profile"),
    ],
    ids=["historical-principal-conflict", "historical-provider-conflict"],
)
def test_schema_valid_historical_cross_record_conflict_fails_before_touch(
    tmp_path, binding_principal, signer_principal, signer_profile, error
):
    root = _setup_ag3(tmp_path)
    repository_id = ceremony.read_repository_identity(root).repository_instance_id
    trust_root = tmp_path / "historical-trust"
    _write_trust_registry(
        trust_root,
        repository_id=repository_id,
        deployment_root=str(root.path.resolve()),
        binding_principal=binding_principal,
        signer_principal=signer_principal,
        signer_profile=signer_profile,
    )
    provider = _Provider()
    with pytest.raises(ceremony.NoAuthorizedSignerError, match=error):
        ceremony.sign_rollback_evidence(
            root,
            site=RollbackSite.AG3,
            job_id="job-1",
            provider_factory=lambda: provider,
            trust_store_factory=lambda: HATPTrustStore(_test_only_root=trust_root),
            hardware_credential_store_factory=lambda: _HardwareStore(
                {"11" * 16: _credential()}
            ),
            confirm=lambda _preview: True,
        )
    assert provider.touch_calls == 0
    assert _published(root) == []


@pytest.mark.parametrize("mismatch", ["repository", "root"])
def test_repository_or_canonical_root_mismatch_fails_before_touch(tmp_path, mismatch):
    root = _setup_ag3(tmp_path)
    actual_repository_id = ceremony.read_repository_identity(root).repository_instance_id
    registry_repository_id = (
        "22222222-2222-4222-8222-222222222222" if mismatch == "repository" else actual_repository_id
    )
    deployment_root = "/wrong/deployment/root" if mismatch == "root" else str(root.path.resolve())
    trust_root = tmp_path / "trust-mismatch"
    _write_trust_registry(
        trust_root, repository_id=registry_repository_id, deployment_root=deployment_root
    )
    provider = _Provider()
    with pytest.raises(ceremony.NoAuthorizedSignerError, match="no active DeploymentBinding"):
        ceremony.sign_rollback_evidence(
            root,
            site=RollbackSite.AG3,
            job_id="job-1",
            provider_factory=lambda: provider,
            trust_store_factory=lambda: HATPTrustStore(_test_only_root=trust_root),
            hardware_credential_store_factory=lambda: _HardwareStore(
                {"11" * 16: _credential()}
            ),
            confirm=lambda _preview: True,
        )
    assert provider.touch_calls == 0
    assert _published(root) == []


def _change_binding_signer(trust, hardware):
    trust.binding = replace(trust.binding, signer_key_id="22" * 16)
    trust.signers["22" * 16] = _signer(signer="22" * 16)
    hardware.records["22" * 16] = _credential(signer="22" * 16)


def _change_binding_principal(trust, _hardware):
    trust.binding = replace(trust.binding, principal_id="principal-2")
    trust.principals["principal-2"] = _principal("principal-2")
    trust.signers["11" * 16] = _signer(principal="principal-2")


@pytest.mark.parametrize(
    "mutation",
    [
        _change_binding_signer,
        _change_binding_principal,
        lambda trust, _hardware: trust.signers.__setitem__(
            "11" * 16, _signer(principal="principal-2")
        ),
        lambda trust, _hardware: trust.signers.__setitem__("11" * 16, _signer(profile="PIV")),
        lambda trust, _hardware: trust.principals.__setitem__(
            "principal-1", _principal(status="revoked")
        ),
        lambda trust, _hardware: trust.signers.__setitem__(
            "11" * 16, _signer(status="revoked")
        ),
        lambda _trust, hardware: hardware.records.__setitem__(
            "11" * 16, _credential(status="revoked")
        ),
        lambda _trust, hardware: hardware.records.__setitem__(
            "11" * 16, _credential(profile="PIV")
        ),
        lambda trust, _hardware: setattr(
            trust, "binding", replace(trust.binding, provider_profile="PIV")
        ),
        lambda trust, _hardware: setattr(
            trust, "binding", replace(trust.binding, authority_scope="CHANGED_SCOPE")
        ),
        lambda trust, _hardware: setattr(
            trust, "binding", replace(trust.binding, valid_from="2026-08-19T00:00:01.000Z")
        ),
        lambda _trust, hardware: hardware.records.__setitem__(
            "11" * 16, _credential(public_key=b"replacement-key")
        ),
    ],
    ids=[
        "binding-rotates-signer",
        "binding-changes-principal",
        "signer-principal-changes",
        "signer-provider-changes",
        "principal-revoked",
        "signer-revoked",
        "credential-revoked",
        "credential-provider-changes",
        "binding-provider-changes",
        "binding-authority-scope-rewrite",
        "binding-valid-from-rewrite",
        "credential-public-key-rewrite",
    ],
)
def test_material_authority_change_after_touch_discards_candidate(tmp_path, mutation):
    root = _setup_ag3(tmp_path)
    trust, hardware = _valid_state()
    provider = _Provider(on_touch=lambda: mutation(trust, hardware))
    with pytest.raises(ceremony.EvidenceSerializationFailureError):
        _run(root, trust, hardware, provider)
    assert provider.touch_calls == 1
    assert _published(root) == []


def test_registry_only_state_cannot_publish_without_hardware_signature(tmp_path):
    root = _setup_ag3(tmp_path)
    trust, hardware = _valid_state()
    provider = _Provider(fail_touch=HATPProviderUnavailableError("synthetic device absent"))
    with pytest.raises(ceremony.ProviderUnavailableError):
        _run(root, trust, hardware, provider)
    assert provider.touch_calls == 1
    assert _published(root) == []


def test_credential_identity_production_caller_inventory_remains_zero():
    callers = []
    for path in Path("src/pcae").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "credential_identity":
                    callers.append((str(path), node.lineno))
    assert callers == []


def test_nonresident_model_b_regression_uses_explicit_bound_id_without_discovery(tmp_path):
    root = _setup_ag3(tmp_path)
    trust, hardware = _valid_state()
    provider = _Provider()
    result = _run(root, trust, hardware, provider)
    assert result.path.exists()
    assert provider.identity_calls == 0
    assert provider.received_signer == "11" * 16
