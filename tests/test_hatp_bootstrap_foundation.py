from __future__ import annotations

import inspect
import json
import os
import stat
import uuid
from pathlib import Path

import pytest

from pcae.core import hatp_bootstrap as hb
from pcae.core.hatp_bootstrap import (
    BootstrapEnvironmentStatus,
    HATPTrustStore,
    HATPTrustStoreMalformedError,
    HATPTrustStoreSymlinkError,
    deployment_binding_matches,
    inspect_bootstrap_environment,
    resolve_canonical_deployment_root,
)

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")


def _repo_id() -> str:
    return str(uuid.uuid4())


def _write_registry(root: Path, document: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "registry.json").write_text(json.dumps(document), encoding="utf-8")


def _valid_binding(repository_id: str, canonical_root: str, *, status: str = "active") -> dict:
    return {
        "repository_id": repository_id,
        "canonical_deployment_root": canonical_root,
        "principal_id": "principal-1",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "authority_scope": "rollback",
        "valid_from": "2026-08-05T00:00:00.000Z",
        "status": status,
        "revoked_at": "2026-08-05T01:00:00.000Z" if status == "revoked" else None,
    }


# ── Missing / malformed store ────────────────────────────────────────────


def test_missing_registry_lookups_return_none(tmp_path: Path) -> None:
    store = HATPTrustStore(_test_only_root=tmp_path / "does-not-exist")
    assert store.load_repository_enrollment(_repo_id()) is None
    assert store.lookup_principal("p") is None
    assert store.lookup_signer("s") is None
    assert store.lookup_authority("p", _repo_id()) is None
    assert store.signer_revoked("s") is False
    assert store.environment_status().status == BootstrapEnvironmentStatus.UNAVAILABLE


def test_malformed_json_fails_closed(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "registry.json").write_text("not json", encoding="utf-8")
    store = HATPTrustStore(_test_only_root=store_root)

    with pytest.raises(HATPTrustStoreMalformedError):
        store.load_repository_enrollment(_repo_id())
    assert store.environment_status().status == BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION


def test_unknown_registry_version_rejected(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    _write_registry(store_root, {"registry_version": 999})
    store = HATPTrustStore(_test_only_root=store_root)

    with pytest.raises(HATPTrustStoreMalformedError):
        store.load_repository_enrollment(_repo_id())


def test_unrecognized_top_level_field_rejected(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    _write_registry(store_root, {"registry_version": 1, "trusted": True})
    store = HATPTrustStore(_test_only_root=store_root)

    with pytest.raises(HATPTrustStoreMalformedError):
        store.load_repository_enrollment(_repo_id())


def test_duplicate_deployment_binding_rejected(tmp_path: Path) -> None:
    repo_id = _repo_id()
    store_root = tmp_path / "store"
    _write_registry(
        store_root,
        {
            "registry_version": 1,
            "deployment_bindings": [
                _valid_binding(repo_id, "/A"),
                _valid_binding(repo_id, "/B"),
            ],
        },
    )
    store = HATPTrustStore(_test_only_root=store_root)

    with pytest.raises(HATPTrustStoreMalformedError):
        store.load_repository_enrollment(repo_id)


def test_authority_record_bad_repository_id_rejected(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    _write_registry(
        store_root,
        {
            "registry_version": 1,
            "authorities": [
                {
                    "principal_id": "p1",
                    "repository_id": "not-a-uuid",
                    "authority_scope": "rollback",
                    "status": "active",
                    "valid_from": "2026-08-05T00:00:00.000Z",
                    "revoked_at": None,
                }
            ],
        },
    )
    store = HATPTrustStore(_test_only_root=store_root)

    with pytest.raises(HATPTrustStoreMalformedError):
        store.lookup_authority("p1", _repo_id())


def test_revoked_without_revoked_at_rejected(tmp_path: Path) -> None:
    repo_id = _repo_id()
    binding = _valid_binding(repo_id, "/A", status="revoked")
    binding["revoked_at"] = None
    store_root = tmp_path / "store"
    _write_registry(store_root, {"registry_version": 1, "deployment_bindings": [binding]})
    store = HATPTrustStore(_test_only_root=store_root)

    with pytest.raises(HATPTrustStoreMalformedError):
        store.load_repository_enrollment(repo_id)


# ── Lookups on a valid registry ──────────────────────────────────────────


def test_unknown_repository_returns_none(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    _write_registry(store_root, {"registry_version": 1, "deployment_bindings": [_valid_binding(_repo_id(), "/A")]})
    store = HATPTrustStore(_test_only_root=store_root)

    assert store.load_repository_enrollment(_repo_id()) is None


def test_unknown_signer_returns_none(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    _write_registry(store_root, {"registry_version": 1})
    store = HATPTrustStore(_test_only_root=store_root)

    assert store.lookup_signer("nonexistent") is None
    assert store.signer_revoked("nonexistent") is False


def test_revoked_signer_detected(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    _write_registry(
        store_root,
        {
            "registry_version": 1,
            "signers": [
                {
                    "signer_key_id": "signer-1",
                    "principal_id": "p1",
                    "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                    "status": "revoked",
                    "revoked_at": "2026-08-05T00:00:00.000Z",
                }
            ],
        },
    )
    store = HATPTrustStore(_test_only_root=store_root)

    assert store.signer_revoked("signer-1") is True
    assert store.lookup_signer("signer-1").status == "revoked"


def test_authority_scope_and_repository_scope_lookup(tmp_path: Path) -> None:
    repo_id = _repo_id()
    store_root = tmp_path / "store"
    _write_registry(
        store_root,
        {
            "registry_version": 1,
            "authorities": [
                {
                    "principal_id": "p1",
                    "repository_id": repo_id,
                    "authority_scope": "rollback",
                    "status": "active",
                    "valid_from": "2026-08-05T00:00:00.000Z",
                    "revoked_at": None,
                }
            ],
        },
    )
    store = HATPTrustStore(_test_only_root=store_root)

    assert store.lookup_authority("p1", repo_id) is not None
    assert store.lookup_authority("p1", _repo_id()) is None  # repository-scope mismatch
    assert store.lookup_authority("someone-else", repo_id) is None  # principal-scope mismatch


# ── Copy / clone / same-ID-wrong-root attacks (HATP-REQ-057-063) ────────


def test_same_id_wrong_root_is_unauthorized(tmp_path: Path) -> None:
    repo_id = _repo_id()
    store_root = tmp_path / "store"
    _write_registry(store_root, {"registry_version": 1, "deployment_bindings": [_valid_binding(repo_id, "/authorized/A")]})
    store = HATPTrustStore(_test_only_root=store_root)

    authorized = store.resolve_deployment_authorization(
        repository_id=repo_id, canonical_deployment_root="/authorized/A"
    )
    assert authorized is not None

    stolen = store.resolve_deployment_authorization(
        repository_id=repo_id, canonical_deployment_root="/unauthorized/B"
    )
    assert stolen is None


def test_full_copy_attack_no_matching_deployment(tmp_path: Path) -> None:
    """Repo A: ID X, enrolled at root A. Repo B copies ID X, has root B.
    Lookup for B's root must find no authorized deployment."""

    repo_id = _repo_id()
    store_root = tmp_path / "store"
    _write_registry(store_root, {"registry_version": 1, "deployment_bindings": [_valid_binding(repo_id, "/deploy/A")]})
    store = HATPTrustStore(_test_only_root=store_root)

    repo_b_result = store.resolve_deployment_authorization(repository_id=repo_id, canonical_deployment_root="/deploy/B")
    assert repo_b_result is None


def test_revoked_binding_never_matches(tmp_path: Path) -> None:
    repo_id = _repo_id()
    store_root = tmp_path / "store"
    _write_registry(
        store_root, {"registry_version": 1, "deployment_bindings": [_valid_binding(repo_id, "/A", status="revoked")]}
    )
    store = HATPTrustStore(_test_only_root=store_root)

    assert store.resolve_deployment_authorization(repository_id=repo_id, canonical_deployment_root="/A") is None


def test_deployment_binding_matches_helper() -> None:
    repo_id = _repo_id()
    binding = hb._parse_deployment_binding(_valid_binding(repo_id, "/A"))
    assert deployment_binding_matches(binding, repository_id=repo_id, canonical_deployment_root="/A") is True
    assert deployment_binding_matches(binding, repository_id=repo_id, canonical_deployment_root="/B") is False
    assert deployment_binding_matches(None, repository_id=repo_id, canonical_deployment_root="/A") is False


# ── Canonical root resolution ────────────────────────────────────────────


def test_canonical_root_resolves_symlink(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link_dir = tmp_path / "link"
    link_dir.symlink_to(real_dir)

    assert resolve_canonical_deployment_root(link_dir) == resolve_canonical_deployment_root(real_dir)


# ── Permission / ownership / symlink environment checks ─────────────────


def test_current_deployment_is_not_ready_same_user(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    store_root.chmod(0o700)

    result = inspect_bootstrap_environment(store_root)
    assert result.status == BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION
    assert "agent_and_admin_share_os_principal" in result.reasons


def test_group_writable_store_is_unsafe(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    store_root.chmod(0o770)

    result = inspect_bootstrap_environment(store_root)
    assert result.status == BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION
    assert "trust_store_group_or_other_writable" in result.reasons


def test_world_writable_parent_is_unsafe(tmp_path: Path) -> None:
    store_root = tmp_path / "parent" / "store"
    store_root.mkdir(parents=True)
    store_root.chmod(0o700)
    store_root.parent.chmod(0o777)

    result = inspect_bootstrap_environment(store_root)
    assert result.status == BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION
    assert "trust_store_parent_world_writable" in result.reasons

    store_root.parent.chmod(0o755)  # restore for tmp_path cleanup


def test_symlinked_store_root_is_unsafe(tmp_path: Path) -> None:
    real_dir = tmp_path / "real-store"
    real_dir.mkdir()
    link_dir = tmp_path / "link-store"
    link_dir.symlink_to(real_dir)

    result = inspect_bootstrap_environment(link_dir)
    assert result.status == BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION
    assert "trust_store_root_is_symlink" in result.reasons


def test_missing_store_is_unavailable_not_unsafe(tmp_path: Path) -> None:
    result = inspect_bootstrap_environment(tmp_path / "nowhere")
    assert result.status == BootstrapEnvironmentStatus.UNAVAILABLE
    assert result.reasons == ("trust_store_missing",)


def test_registry_file_symlink_substitution_rejected(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    decoy = tmp_path / "decoy-registry.json"
    decoy.write_text(json.dumps({"registry_version": 1}), encoding="utf-8")
    (store_root / "registry.json").symlink_to(decoy)

    store = HATPTrustStore(_test_only_root=store_root)
    with pytest.raises(HATPTrustStoreSymlinkError):
        store.load_repository_enrollment(_repo_id())


# ── No caller-controlled production override ─────────────────────────────


def test_production_constructor_accepts_no_path_argument() -> None:
    sig = inspect.signature(HATPTrustStore.production)
    assert list(sig.parameters.keys()) == []


def test_production_ignores_environment_overrides(monkeypatch) -> None:
    for var in ("PCAE_HATP_TRUST_STORE", "HATP_TRUST_STORE", "HATP_TRUSTED_KEY", "PCAE_HATP_TRUSTED_KEY"):
        monkeypatch.setenv(var, "/tmp/attacker-controlled")

    if os.name == "posix":
        store = HATPTrustStore.production()
        assert store.root == Path.home() / ".pcae-hatp" / "trust-store"


def test_no_agent_facing_mutation_methods_exist() -> None:
    public_methods = {name for name in dir(HATPTrustStore) if not name.startswith("_")}
    forbidden = {"enroll", "grant", "revoke", "rotate", "mutate", "write", "save", "update"}
    assert public_methods.isdisjoint(forbidden)


def test_no_hatp_rae_permission_broker_or_agent_imports() -> None:
    import_lines = [
        line.strip()
        for line in inspect.getsource(hb).splitlines()
        if line.strip().startswith("import ") or line.strip().startswith("from ")
    ]
    for forbidden_module in (
        "rollback_approval_evidence",
        "permission_broker",
        "pcae.core.agent",
        "commands.agent",
    ):
        assert not any(forbidden_module in line for line in import_lines), import_lines
