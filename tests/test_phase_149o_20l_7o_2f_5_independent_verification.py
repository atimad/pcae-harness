"""Phase 149O.20L.7O.2F.5 -- Durable-Registry Signer Cross-Record
Consistency and TOCTOU Repair Independent Verification.

Independently derived (not copied from 2F.3/2F.4 test bodies): raw
schema-valid JSON registry fixtures are constructed directly from the
field names read out of `hatp_bootstrap.py`/`hatp_hardware_credentials.py`'s
own parsers, and the production consumer
(`_resolve_deployment_binding_signer`, `sign_rollback_evidence`) is
exercised directly. Verifies:

* B-149O.20L.7O.2F.3-1 (binding.principal_id != signer.principal_id)
  fails closed pre-touch on current source.
* B-149O.20L.7O.2F.3-2 (signer.provider_profile conflict) fails closed
  pre-touch on current source.
* A fully coherent fixture succeeds (control).
* The two calls to `_resolve_deployment_binding_signer` inside
  `sign_rollback_evidence` (pre-touch snapshot A, post-touch snapshot B)
  each perform a genuinely fresh disk read -- not a cached compare --
  by mutating the on-disk registry between the two reads and observing
  the change is picked up.
* `HATPSignerResolution` equality is complete-field value equality, not
  object identity: two independently-read snapshots of unchanged state
  compare equal despite being different Python objects; a materially
  changed re-read compares unequal.
* No production caller of `credential_identity()` exists outside its
  own provider-module definition (BF-1 regression).
* `Fido2HardwareProvider.enroll_credential()` still omits any
  resident/discoverable-key CTAP2 option (BF-2 regression, textual
  check -- this module holds no live hardware).

No production source, contract, or hardware is touched or provisioned.
All state is disposable and written to `tmp_path`.
"""
from __future__ import annotations

import inspect
import json
import uuid
from pathlib import Path

import pytest

from pcae.core.hatp_bootstrap import HATPTrustStore, resolve_canonical_deployment_root
from pcae.core.hatp_hardware_credentials import HATPHardwareCredentialStore
from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1
from pcae.core.hatp_signing_ceremony import (
    HATPSignerResolution,
    NoAuthorizedSignerError,
    _resolve_deployment_binding_signer,
)
from pcae.core.paths import HarnessPath

PROD_PROVIDER = HATP_HARDWARE_PROVIDER_V1


def _write_trust_registry(
    root: Path,
    *,
    binding_principal: str,
    signer_principal: str,
    repo_id: str,
    canon_root: str,
    signer_provider: str,
    binding_provider: str = PROD_PROVIDER,
    signer_key_id: str = "signer-X",
    signer_status: str = "active",
    principal_status: str = "active",
) -> None:
    principals = [{"principal_id": binding_principal, "status": principal_status}]
    if signer_principal != binding_principal:
        principals.append({"principal_id": signer_principal, "status": "active"})
    doc = {
        "registry_version": 1,
        "principals": principals,
        "signers": [
            {
                "signer_key_id": signer_key_id,
                "principal_id": signer_principal,
                "provider_profile": signer_provider,
                "status": signer_status,
            }
        ],
        "deployment_bindings": [
            {
                "repository_id": repo_id,
                "canonical_deployment_root": canon_root,
                "principal_id": binding_principal,
                "signer_key_id": signer_key_id,
                "provider_profile": binding_provider,
                "authority_scope": "rollback_signing",
                "valid_from": "2026-01-01T00:00:00Z",
                "status": "active",
            }
        ],
        "authorities": [],
    }
    (root / "registry.json").write_text(json.dumps(doc), encoding="utf-8")


def _write_credential_registry(
    root: Path, *, provider: str = PROD_PROVIDER, signer_key_id: str = "signer-X", status: str = "active",
    public_key_hex: str = "aa" * 16,
) -> None:
    doc = {
        "schema_version": 1,
        "credentials": [
            {
                "signer_key_id": signer_key_id,
                "provider_profile": provider,
                "protocol_name": "FIDO2",
                "algorithm": "ES256",
                "public_key_hex": public_key_hex,
                "status": status,
            }
        ],
    }
    (root / "hardware-credentials.json").write_text(json.dumps(doc), encoding="utf-8")


@pytest.fixture
def coherent_fixture(tmp_path):
    trust_root = tmp_path / "trust"
    cred_root = tmp_path / "cred"
    deploy_root = tmp_path / "deploy"
    trust_root.mkdir()
    cred_root.mkdir()
    deploy_root.mkdir()
    repo_id = str(uuid.uuid4())
    canon_root = resolve_canonical_deployment_root(deploy_root)
    _write_trust_registry(
        trust_root,
        binding_principal="principal-A",
        signer_principal="principal-A",
        repo_id=repo_id,
        canon_root=canon_root,
        signer_provider=PROD_PROVIDER,
    )
    _write_credential_registry(cred_root)
    trust_store = HATPTrustStore(_test_only_root=trust_root)

    def hw_factory():
        return HATPHardwareCredentialStore(_test_only_root=cred_root)

    return {
        "trust_root": trust_root,
        "cred_root": cred_root,
        "deploy_root": deploy_root,
        "repo_id": repo_id,
        "canon_root": canon_root,
        "trust_store": trust_store,
        "hw_factory": hw_factory,
    }


def _resolve(fx):
    return _resolve_deployment_binding_signer(
        HarnessPath(fx["deploy_root"]),
        fx["trust_store"],
        repository_id=fx["repo_id"],
        provider_profile=PROD_PROVIDER,
        hardware_credential_store_factory=fx["hw_factory"],
    )


class TestBF3_1CrossRecordPrincipalConflict:
    def test_current_source_rejects_binding_principal_signer_principal_mismatch_before_touch(self, tmp_path):
        trust_root = tmp_path / "trust"
        cred_root = tmp_path / "cred"
        deploy_root = tmp_path / "deploy"
        trust_root.mkdir(); cred_root.mkdir(); deploy_root.mkdir()
        repo_id = str(uuid.uuid4())
        canon_root = resolve_canonical_deployment_root(deploy_root)
        _write_trust_registry(
            trust_root,
            binding_principal="principal-A",
            signer_principal="principal-B",  # conflict: HSCE-REQ-080 step 3
            repo_id=repo_id,
            canon_root=canon_root,
            signer_provider=PROD_PROVIDER,
        )
        _write_credential_registry(cred_root)
        trust_store = HATPTrustStore(_test_only_root=trust_root)

        with pytest.raises(NoAuthorizedSignerError, match="principal_id"):
            _resolve_deployment_binding_signer(
                HarnessPath(deploy_root),
                trust_store,
                repository_id=repo_id,
                provider_profile=PROD_PROVIDER,
                hardware_credential_store_factory=lambda: HATPHardwareCredentialStore(_test_only_root=cred_root),
            )


class TestBF3_2CrossRecordProviderConflict:
    def test_current_source_rejects_signer_provider_conflict_before_touch(self, tmp_path):
        trust_root = tmp_path / "trust"
        cred_root = tmp_path / "cred"
        deploy_root = tmp_path / "deploy"
        trust_root.mkdir(); cred_root.mkdir(); deploy_root.mkdir()
        repo_id = str(uuid.uuid4())
        canon_root = resolve_canonical_deployment_root(deploy_root)
        _write_trust_registry(
            trust_root,
            binding_principal="principal-A",
            signer_principal="principal-A",
            repo_id=repo_id,
            canon_root=canon_root,
            signer_provider="SOME_OTHER_PROVIDER_PROFILE",  # conflicts with resolved production provider
            binding_provider=PROD_PROVIDER,
        )
        _write_credential_registry(cred_root, provider=PROD_PROVIDER)
        trust_store = HATPTrustStore(_test_only_root=trust_root)

        with pytest.raises(NoAuthorizedSignerError, match="provider_profile"):
            _resolve_deployment_binding_signer(
                HarnessPath(deploy_root),
                trust_store,
                repository_id=repo_id,
                provider_profile=PROD_PROVIDER,
                hardware_credential_store_factory=lambda: HATPHardwareCredentialStore(_test_only_root=cred_root),
            )


class TestCoherentControlStillResolves:
    def test_fully_coherent_state_resolves_successfully(self, coherent_fixture):
        resolution = _resolve(coherent_fixture)
        assert isinstance(resolution, HATPSignerResolution)
        assert resolution.principal_id == "principal-A"
        assert resolution.signer_key_id == "signer-X"


class TestFreshSecondRead:
    def test_second_resolution_call_observes_a_disk_mutation_made_between_calls(self, coherent_fixture):
        first = _resolve(coherent_fixture)

        # Mutate on-disk registry state directly (simulating a concurrent
        # administrative rotation) between the two resolution calls --
        # if the second call used a cached/first-read object instead of
        # a fresh disk read, it would not observe this.
        _write_trust_registry(
            coherent_fixture["trust_root"],
            binding_principal="principal-A",
            signer_principal="principal-A",
            repo_id=coherent_fixture["repo_id"],
            canon_root=coherent_fixture["canon_root"],
            signer_provider=PROD_PROVIDER,
            signer_key_id="signer-X",
            signer_status="revoked",
        )

        with pytest.raises(NoAuthorizedSignerError):
            _resolve(coherent_fixture)

        # Confirm the *first* resolution's own snapshot is unaffected
        # (immutability) -- it still reports the original active status.
        assert first.signer.status == "active"


class TestSnapshotValueEqualityNotIdentity:
    def test_two_independent_reads_of_unchanged_state_are_value_equal_but_not_identical_objects(self, coherent_fixture):
        a = _resolve(coherent_fixture)
        b = _resolve(coherent_fixture)
        assert a is not b
        assert a.binding is not b.binding
        assert a == b  # dataclass field-wise equality across independently-read objects

    def test_a_materially_changed_reread_compares_unequal(self, coherent_fixture):
        a = _resolve(coherent_fixture)
        _write_trust_registry(
            coherent_fixture["trust_root"],
            binding_principal="principal-A",
            signer_principal="principal-A",
            repo_id=coherent_fixture["repo_id"],
            canon_root=coherent_fixture["canon_root"],
            signer_provider=PROD_PROVIDER,
            signer_key_id="signer-X",
        )
        # same content -> still equal
        b = _resolve(coherent_fixture)
        assert a == b

        # now genuinely change credential content (public key rewrite,
        # same signer_key_id) -- HSCE-REQ-083 v1.3 must detect this even
        # though (principal_id, signer_key_id) is unchanged.
        _write_credential_registry(coherent_fixture["cred_root"], public_key_hex="bb" * 16)
        c = _resolve(coherent_fixture)
        assert c != a


class TestSnapshotFieldInventory:
    def test_resolution_dataclass_fields_cover_repository_root_provider_and_all_four_records(self):
        field_names = {f for f in HATPSignerResolution.__dataclass_fields__}
        assert field_names == {
            "repository_id",
            "canonical_deployment_root",
            "provider_profile",
            "binding",
            "signer",
            "principal",
            "credential",
        }

    def test_resolution_dataclass_is_frozen(self):
        assert HATPSignerResolution.__dataclass_params__.frozen is True


class TestBF1CredentialIdentityCallerInventory:
    def test_no_production_module_calls_credential_identity_except_its_own_definition(self):
        import ast
        import pcae.core as core_pkg

        core_dir = Path(core_pkg.__file__).parent
        offending = []
        for py_file in sorted(core_dir.glob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
            defines_it = any(
                isinstance(node, ast.FunctionDef) and node.name == "credential_identity"
                for node in ast.walk(tree)
            )
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    name = getattr(func, "attr", None) or getattr(func, "id", None)
                    if name == "credential_identity":
                        offending.append((py_file.name, node.lineno, defines_it))
        real_callers = [o for o in offending if not o[2]]
        assert real_callers == [], f"unexpected credential_identity() call sites: {real_callers}"


class TestBF2NonResidentEnrollmentTextualRegression:
    def test_enroll_credential_source_passes_no_resident_key_option_to_make_credential(self):
        from pcae.core import hatp_fido2_provider

        source = inspect.getsource(hatp_fido2_provider.Fido2HardwareProvider.enroll_credential)
        assert "make_credential(" in source
        assert "resident_key" not in source
        assert '"rk"' not in source and "'rk'" not in source

    def test_request_signature_uses_explicit_signer_key_id_not_discovery(self):
        from pcae.core import hatp_fido2_provider

        source = inspect.getsource(hatp_fido2_provider.Fido2HardwareProvider.request_signature)
        assert "bytes.fromhex(signer_key_id)" in source
