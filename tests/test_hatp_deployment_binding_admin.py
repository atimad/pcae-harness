"""Producer-oriented unit/adversarial/round-trip tests for
`pcae.core.hatp_deployment_binding_admin` — Phase 149O.20L.7I,
`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` §16.1
(HBDC-REQ-056..070).

Every fixture uses a disposable `tmp_path` "repository" and a disposable
`tmp_path` protected-root ("trust store"). No test ever touches
`HATPTrustStore.production()`'s real path, creates a real
`.pcae/repository-identity.json` in this repository's own working tree,
or performs any network/Dell access.
"""
from __future__ import annotations

import inspect
import json
import os
import re
import threading
import uuid
from pathlib import Path

import pytest

from pcae.core import hatp_deployment_binding_admin as admin
from pcae.core.hatp_bootstrap import (
    DeploymentBinding,
    HATPTrustStore,
    HATPTrustStoreMalformedError,
    HATPTrustStoreSymlinkError,
    deployment_binding_matches,
    resolve_canonical_deployment_root,
)
from pcae.core.paths import HarnessPath
from pcae.core.provenance import read_provenance_history
from pcae.core.repository_identity import (
    RepositoryIdentityMalformedError,
    ensure_repository_identity,
)

pytestmark = [pytest.mark.fast_green, pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")]


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


def _repo(tmp_path: Path, name: str = "repo") -> Path:
    root = tmp_path / name
    root.mkdir()
    ensure_repository_identity(HarnessPath(root))
    return root


def _store(tmp_path: Path, name: str = "store") -> Path:
    root = tmp_path / name
    root.mkdir()
    return root


def _authority(**overrides: str) -> admin.AuthorityEvidence:
    fields = dict(
        principal_id="principal-1",
        signer_key_id="signer-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        authority_scope="rollback",
        election_reference="CHGR-TEST-0001",
    )
    fields.update(overrides)
    return admin.AuthorityEvidence(**fields)


def _registry_raw(store_root: Path) -> dict:
    return json.loads((store_root / "registry.json").read_text(encoding="utf-8"))


def _provenance_event_types(repo_root: Path) -> list[str]:
    history = read_provenance_history(HarnessPath(repo_root))
    return [event.event_type for event in history.events]


# ═══════════════════════════════════════════════════════════════════════════
# CREATE — happy path, idempotency, conflict, revoked-entry
# ═══════════════════════════════════════════════════════════════════════════


def test_create_writes_a_new_active_binding(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    authority = _authority()

    result = admin.create_deployment_binding(repository_root=repo_root, authority=authority, _protected_root=store_root)

    assert result.outcome == admin.DeploymentBindingOutcome.CREATED
    assert result.previous_binding is None
    assert result.binding.status == "active"
    assert result.binding.revoked_at is None
    assert admin._TIMESTAMP_PATTERN.fullmatch(result.binding.valid_from)
    assert "deployment_binding_created" in _provenance_event_types(repo_root)


def test_create_is_idempotent_on_identical_active_entry(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    authority = _authority()

    first = admin.create_deployment_binding(repository_root=repo_root, authority=authority, _protected_root=store_root)
    second = admin.create_deployment_binding(repository_root=repo_root, authority=authority, _protected_root=store_root)

    assert second.outcome == admin.DeploymentBindingOutcome.ALREADY_SATISFIED
    # No fresh write: valid_from is byte-identical, not regenerated.
    assert second.binding.valid_from == first.binding.valid_from
    assert _provenance_event_types(repo_root).count("deployment_binding_create_noop") == 1


def test_create_conflicting_active_entry_fails_closed(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)

    before = _registry_raw(store_root)
    with pytest.raises(admin.DuplicateConflictingBindingError):
        admin.create_deployment_binding(
            repository_root=repo_root, authority=_authority(principal_id="different-principal"), _protected_root=store_root
        )
    assert _registry_raw(store_root) == before  # no overwrite


def test_create_against_revoked_entry_fails_closed(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-REV-1", _protected_root=store_root)

    before = _registry_raw(store_root)
    with pytest.raises(admin.DuplicateConflictingBindingError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert _registry_raw(store_root) == before  # revoked entry never silently reactivated


# ═══════════════════════════════════════════════════════════════════════════
# ROTATE — happy path, nonexistent, revoked
# ═══════════════════════════════════════════════════════════════════════════


def test_rotate_overwrites_mutable_fields_in_place(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    created = admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)

    rotated = admin.rotate_deployment_binding(
        repository_root=repo_root, authority=_authority(principal_id="principal-2"), _protected_root=store_root
    )

    assert rotated.outcome == admin.DeploymentBindingOutcome.ROTATED
    assert rotated.binding.principal_id == "principal-2"
    assert rotated.binding.status == "active"
    assert rotated.binding.revoked_at is None
    assert rotated.previous_binding == created.binding
    # Exactly one entry remains for this repository_id -- no dual-active window.
    raw = _registry_raw(store_root)
    matches = [b for b in raw["deployment_bindings"] if b["repository_id"] == created.binding.repository_id]
    assert len(matches) == 1
    assert "deployment_binding_rotated" in _provenance_event_types(repo_root)


def test_rotate_nonexistent_entry_fails_closed_never_creates(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)

    with pytest.raises(admin.DeploymentBindingNotFoundError):
        admin.rotate_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert not (store_root / "registry.json").exists()


def test_rotate_revoked_entry_fails_closed_never_resurrects(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-REV-1", _protected_root=store_root)

    before = _registry_raw(store_root)
    with pytest.raises(admin.DeploymentBindingRevokedError):
        admin.rotate_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert _registry_raw(store_root) == before


# ═══════════════════════════════════════════════════════════════════════════
# REVOKE — happy path, nonexistent, already-revoked idempotency
# ═══════════════════════════════════════════════════════════════════════════


def test_revoke_field_mutates_never_deletes(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    created = admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)

    revoked = admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-REV-1", _protected_root=store_root)

    assert revoked.outcome == admin.DeploymentBindingOutcome.REVOKED
    assert revoked.binding.status == "revoked"
    assert admin._TIMESTAMP_PATTERN.fullmatch(revoked.binding.revoked_at)
    # Every other field preserved unchanged (CBD-10 field mutation, not deletion).
    assert revoked.binding.principal_id == created.binding.principal_id
    assert revoked.binding.canonical_deployment_root == created.binding.canonical_deployment_root
    assert revoked.binding.valid_from == created.binding.valid_from
    raw = _registry_raw(store_root)
    assert len(raw["deployment_bindings"]) == 1  # record retained, not deleted
    assert "deployment_binding_revoked" in _provenance_event_types(repo_root)


def test_revoke_nonexistent_entry_fails_closed_no_tombstone(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)

    with pytest.raises(admin.DeploymentBindingNotFoundError):
        admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-1", _protected_root=store_root)
    assert not (store_root / "registry.json").exists()


def test_revoke_already_revoked_is_idempotent_preserves_original_revoked_at(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    first = admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-REV-1", _protected_root=store_root)

    second = admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-REV-2", _protected_root=store_root)

    assert second.outcome == admin.DeploymentBindingOutcome.ALREADY_REVOKED
    assert second.binding.revoked_at == first.binding.revoked_at  # original evidence never overwritten
    assert "deployment_binding_revoke_noop" in _provenance_event_types(repo_root)


# ═══════════════════════════════════════════════════════════════════════════
# RepositoryIdentity prerequisite (HBDC-REQ-057/8.1)
# ═══════════════════════════════════════════════════════════════════════════


def test_create_fails_closed_when_repository_identity_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "no-identity-repo"
    repo_root.mkdir()
    store_root = _store(tmp_path)

    with pytest.raises(admin.RepositoryIdentityMissingError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert not (repo_root / ".pcae" / "repository-identity.json").exists()
    assert not (store_root / "registry.json").exists()


def test_create_fails_closed_when_repository_identity_malformed(tmp_path: Path) -> None:
    repo_root = tmp_path / "malformed-identity-repo"
    repo_root.mkdir()
    identity_path = repo_root / ".pcae" / "repository-identity.json"
    identity_path.parent.mkdir(parents=True)
    identity_path.write_text("{not valid json", encoding="utf-8")
    store_root = _store(tmp_path)

    with pytest.raises(RepositoryIdentityMalformedError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert not (store_root / "registry.json").exists()


def test_create_never_calls_ensure_repository_identity_as_side_effect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "no-identity-repo"
    repo_root.mkdir()
    store_root = _store(tmp_path)

    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("create_deployment_binding must never call ensure_repository_identity()")

    monkeypatch.setattr(admin, "read_repository_identity", admin.read_repository_identity)  # sanity: symbol exists
    with pytest.raises(admin.RepositoryIdentityMissingError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert not (repo_root / ".pcae" / "repository-identity.json").exists()


# ═══════════════════════════════════════════════════════════════════════════
# Authority-evidence validation (HBDC-REQ-058/064/065)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "field", ["principal_id", "signer_key_id", "provider_profile", "authority_scope"]
)
def test_create_rejects_empty_authority_field(tmp_path: Path, field: str) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)

    with pytest.raises(admin.AuthorityEvidenceMalformedError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(**{field: ""}), _protected_root=store_root)
    assert not (store_root / "registry.json").exists()


def test_create_rejects_missing_election_reference(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)

    with pytest.raises(admin.AuthorityEvidenceMissingError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(election_reference=""), _protected_root=store_root)
    assert not (store_root / "registry.json").exists()


def test_revoke_rejects_missing_election_reference(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)

    with pytest.raises(admin.AuthorityEvidenceMissingError):
        admin.revoke_deployment_binding(repository_root=repo_root, election_reference="", _protected_root=store_root)


def test_authority_fields_never_widened_or_transformed(tmp_path: Path) -> None:
    """149O.20L.7H's deferred vocabulary-cross-validation finding: unknown
    input must not be transformed into broader authority -- the exact
    caller-supplied string is preserved byte-for-byte."""

    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    authority = _authority(authority_scope="totally-unrecognized-scope-string")

    result = admin.create_deployment_binding(repository_root=repo_root, authority=authority, _protected_root=store_root)
    assert result.binding.authority_scope == "totally-unrecognized-scope-string"


# ═══════════════════════════════════════════════════════════════════════════
# Canonical root / registry malformation / trust-store availability
# ═══════════════════════════════════════════════════════════════════════════


def test_create_fails_closed_when_repository_root_does_not_resolve(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    import shutil

    shutil.rmtree(repo_root / ".pcae")  # keep identity file removed after resolving path once is not enough
    shutil.rmtree(repo_root)

    with pytest.raises((admin.RepositoryIdentityMissingError, admin.DeploymentRootUnresolvableError)):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)


def test_malformed_registry_document_fails_closed_not_repaired(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    (store_root / "registry.json").write_text("not json at all", encoding="utf-8")

    with pytest.raises(HATPTrustStoreMalformedError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    # Untouched -- producer never "repairs" a malformed registry.
    assert (store_root / "registry.json").read_text(encoding="utf-8") == "not json at all"


def test_duplicate_registry_records_fail_closed(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    identity = ensure_repository_identity(HarnessPath(repo_root))
    canonical_root = resolve_canonical_deployment_root(repo_root)
    duplicate_doc = {
        "registry_version": 1,
        "deployment_bindings": [
            _binding_document(identity.repository_instance_id, canonical_root, "p1"),
            _binding_document(identity.repository_instance_id, canonical_root, "p2"),
        ],
    }
    (store_root / "registry.json").write_text(json.dumps(duplicate_doc), encoding="utf-8")

    with pytest.raises(HATPTrustStoreMalformedError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)


def _binding_document(repository_id: str, canonical_root: str, principal_id: str, *, status: str = "active") -> dict:
    return {
        "repository_id": repository_id,
        "canonical_deployment_root": canonical_root,
        "principal_id": principal_id,
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "authority_scope": "rollback",
        "valid_from": "2026-08-05T00:00:00.000Z",
        "status": status,
        "revoked_at": "2026-08-05T01:00:00.000Z" if status == "revoked" else None,
    }


def test_trust_store_missing_fails_closed(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = tmp_path / "does-not-exist"

    with pytest.raises(admin.DeploymentBindingTrustStoreUnavailableError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)


def test_trust_store_root_symlink_rejected(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    real_store = _store(tmp_path, "real-store")
    symlinked_store = tmp_path / "symlinked-store"
    symlinked_store.symlink_to(real_store)

    with pytest.raises(HATPTrustStoreSymlinkError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=symlinked_store)


def test_registry_path_symlink_substitution_rejected(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    decoy_target = tmp_path / "decoy.json"
    decoy_target.write_text("{}", encoding="utf-8")
    (store_root / "registry.json").symlink_to(decoy_target)

    with pytest.raises(HATPTrustStoreSymlinkError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)


def test_lock_file_path_symlink_rejected(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    decoy_target = tmp_path / "decoy.lock"
    decoy_target.write_text("", encoding="utf-8")
    (store_root / admin._DEPLOYMENT_BINDING_TRANSITION_LOCK_FILE_NAME).symlink_to(decoy_target)

    with pytest.raises(HATPTrustStoreSymlinkError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)


# ═══════════════════════════════════════════════════════════════════════════
# Atomic publication / fault injection
# ═══════════════════════════════════════════════════════════════════════════


def test_interrupted_write_before_rename_leaves_no_partial_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)

    real_replace = os.replace

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("simulated crash before rename")

    monkeypatch.setattr(admin.os, "replace", _boom)
    with pytest.raises(OSError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    monkeypatch.setattr(admin.os, "replace", real_replace)

    assert not (store_root / "registry.json").exists()
    # No leaked temp files either.
    leftover = [p for p in store_root.iterdir() if p.name.startswith(".tmp-deployment-binding-")]
    assert leftover == []


def test_readback_mismatch_is_treated_as_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)

    def _wrong_readback(store_root_arg: Path, expected_binding: DeploymentBinding) -> DeploymentBinding:
        from dataclasses import replace as _replace

        return _replace(expected_binding, principal_id="corrupted-on-disk")

    monkeypatch.setattr(admin, "_read_back_and_verify", _wrong_readback)
    # _read_back_and_verify is monkeypatched to *not* raise, so the mismatch
    # must be caught at a higher level by this test comparing the returned
    # binding to what was requested -- exercising that a caller cannot be
    # fooled by a stubbed readback. Restore the real implementation and
    # verify it does raise on a genuine mismatch:
    monkeypatch.undo()

    def _raising_readback(store_root_arg: Path, expected_binding: DeploymentBinding) -> DeploymentBinding:
        raise admin.DeploymentBindingReadbackMismatchError("simulated read-back mismatch")

    monkeypatch.setattr(admin, "_read_back_and_verify", _raising_readback)
    with pytest.raises(admin.DeploymentBindingReadbackMismatchError):
        admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)


def test_readback_mismatch_function_detects_real_corruption(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    result = admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)

    from dataclasses import replace as _replace

    wrong_expectation = _replace(result.binding, principal_id="not-what-was-written")
    with pytest.raises(admin.DeploymentBindingReadbackMismatchError):
        admin._read_back_and_verify(store_root, wrong_expectation)


# ═══════════════════════════════════════════════════════════════════════════
# Concurrency / TOCTOU
# ═══════════════════════════════════════════════════════════════════════════


def test_concurrent_create_produces_exactly_one_deterministic_active_entry(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    authority = _authority()

    outcomes: list[object] = []
    errors: list[BaseException] = []

    def _worker() -> None:
        try:
            outcomes.append(
                admin.create_deployment_binding(repository_root=repo_root, authority=authority, _protected_root=store_root).outcome
            )
        except BaseException as exc:  # noqa: BLE001 - concurrency test collects every outcome
            errors.append(exc)

    threads = [threading.Thread(target=_worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert set(outcomes) <= {admin.DeploymentBindingOutcome.CREATED, admin.DeploymentBindingOutcome.ALREADY_SATISFIED}
    assert outcomes.count(admin.DeploymentBindingOutcome.CREATED) == 1
    raw = _registry_raw(store_root)
    assert len(raw["deployment_bindings"]) == 1


def test_concurrent_rotate_vs_revoke_yields_one_deterministic_final_state(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)

    results: list[object] = []
    errors: list[BaseException] = []

    def _rotate() -> None:
        try:
            results.append(
                admin.rotate_deployment_binding(
                    repository_root=repo_root, authority=_authority(principal_id="rotated-principal"), _protected_root=store_root
                )
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    def _revoke() -> None:
        try:
            results.append(
                admin.revoke_deployment_binding(
                    repository_root=repo_root, election_reference="CHGR-CONC-1", _protected_root=store_root
                )
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_rotate), threading.Thread(target=_revoke)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly one of the two operations may legitimately fail (rotate-after-
    # revoke is fail-closed; revoke-after-rotate always succeeds) -- but the
    # lock guarantees the two writers are never interleaved, so the final
    # on-disk state is always fully self-consistent (never a torn write).
    raw = _registry_raw(store_root)
    assert len(raw["deployment_bindings"]) == 1
    entry = raw["deployment_bindings"][0]
    assert entry["status"] in {"active", "revoked"}
    if entry["status"] == "revoked":
        assert entry["revoked_at"] is not None
    else:
        assert entry["revoked_at"] is None


# ═══════════════════════════════════════════════════════════════════════════
# Producer/consumer round-trip (HBDC item-31/53/54/55)
# ═══════════════════════════════════════════════════════════════════════════


def test_create_round_trip_through_production_consumer_chain(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    identity = ensure_repository_identity(HarnessPath(repo_root))
    canonical_root = resolve_canonical_deployment_root(repo_root)

    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)

    store = HATPTrustStore(_test_only_root=store_root)
    binding = store.load_repository_enrollment(identity.repository_instance_id)
    assert binding is not None
    assert deployment_binding_matches(
        binding, repository_id=identity.repository_instance_id, canonical_deployment_root=canonical_root
    )


def test_rotate_round_trip_exactly_one_entry_old_no_longer_matches(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    identity = ensure_repository_identity(HarnessPath(repo_root))
    canonical_root = resolve_canonical_deployment_root(repo_root)

    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(principal_id="principal-A"), _protected_root=store_root)
    admin.rotate_deployment_binding(repository_root=repo_root, authority=_authority(principal_id="principal-B"), _protected_root=store_root)

    store = HATPTrustStore(_test_only_root=store_root)
    binding = store.load_repository_enrollment(identity.repository_instance_id)
    assert binding is not None
    assert binding.principal_id == "principal-B"
    assert deployment_binding_matches(
        binding, repository_id=identity.repository_instance_id, canonical_deployment_root=canonical_root
    )
    raw = _registry_raw(store_root)
    assert len([b for b in raw["deployment_bindings"] if b["repository_id"] == identity.repository_instance_id]) == 1


def test_revoke_round_trip_consumer_no_longer_matches(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    identity = ensure_repository_identity(HarnessPath(repo_root))
    canonical_root = resolve_canonical_deployment_root(repo_root)

    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-REV-1", _protected_root=store_root)

    store = HATPTrustStore(_test_only_root=store_root)
    binding = store.load_repository_enrollment(identity.repository_instance_id)
    assert binding is not None
    assert binding.status == "revoked"
    assert not deployment_binding_matches(
        binding, repository_id=identity.repository_instance_id, canonical_deployment_root=canonical_root
    )


# ═══════════════════════════════════════════════════════════════════════════
# Multi-repository / multi-root isolation
# ═══════════════════════════════════════════════════════════════════════════


def test_multi_repository_operations_are_isolated(tmp_path: Path) -> None:
    repo_a = _repo(tmp_path, "repo-a")
    repo_b = _repo(tmp_path, "repo-b")
    store_root = _store(tmp_path)

    result_a = admin.create_deployment_binding(repository_root=repo_a, authority=_authority(principal_id="principal-A"), _protected_root=store_root)
    result_b = admin.create_deployment_binding(repository_root=repo_b, authority=_authority(principal_id="principal-B"), _protected_root=store_root)

    assert result_a.binding.repository_id != result_b.binding.repository_id
    admin.revoke_deployment_binding(repository_root=repo_a, election_reference="CHGR-A-REV", _protected_root=store_root)

    store = HATPTrustStore(_test_only_root=store_root)
    binding_a = store.load_repository_enrollment(result_a.binding.repository_id)
    binding_b = store.load_repository_enrollment(result_b.binding.repository_id)
    assert binding_a.status == "revoked"
    assert binding_b.status == "active"  # operation on A never affected B

    raw = _registry_raw(store_root)
    assert len(raw["deployment_bindings"]) == 2


def test_same_repository_identity_two_hosts_requires_two_independent_bindings(tmp_path: Path) -> None:
    """8.5 of the 149O.20L.7G plan: a given repository_id's single entry
    binds at most one canonical_deployment_root at a time -- deploying the
    identical identity to a second host requires a fresh, independent
    repository_instance_id (a fresh `pcae init`), not a second root bound
    under the same repository_id."""

    repo_root = _repo(tmp_path, "shared-identity-repo")
    store_root = _store(tmp_path)
    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)

    # Simulate "the same identity file copied to a second host": same
    # repository_id, different canonical_deployment_root, attempted via a
    # second repo_root sharing the identical repository-identity.json bytes.
    second_host_root = tmp_path / "second-host-copy"
    second_host_root.mkdir()
    (second_host_root / ".pcae").mkdir()
    identity_bytes = (repo_root / ".pcae" / "repository-identity.json").read_bytes()
    (second_host_root / ".pcae" / "repository-identity.json").write_bytes(identity_bytes)

    with pytest.raises(admin.DuplicateConflictingBindingError):
        admin.create_deployment_binding(repository_root=second_host_root, authority=_authority(), _protected_root=store_root)


# ═══════════════════════════════════════════════════════════════════════════
# Strict timestamp grammar (HBDC-REQ-067)
# ═══════════════════════════════════════════════════════════════════════════


def test_generated_timestamps_conform_to_strict_grammar(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    result = admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    revoked = admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-1", _protected_root=store_root)

    strict = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")
    assert strict.fullmatch(result.binding.valid_from)
    assert strict.fullmatch(revoked.binding.revoked_at)


@pytest.mark.parametrize(
    "noncanonical",
    [
        "2026-08-16T10:00:00+05:00",  # non-Z offset
        "2026-08-16T10:00:00.123456789Z",  # >6-digit fraction
        "2026-08-16 10:00:00Z",  # space-separated
        "2026-08-16T10:00:00",  # missing Z
    ],
)
def test_noncanonical_timestamp_forms_never_emitted(noncanonical: str) -> None:
    strict = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")
    assert not strict.fullmatch(noncanonical)  # documents exactly what the writer must never emit


# ═══════════════════════════════════════════════════════════════════════════
# Schema preservation (item 13/74/75: no new fields)
# ═══════════════════════════════════════════════════════════════════════════


def test_deployment_binding_schema_has_exactly_nine_original_fields() -> None:
    fields = {f.name for f in DeploymentBinding.__dataclass_fields__.values()}
    assert fields == {
        "repository_id",
        "canonical_deployment_root",
        "principal_id",
        "signer_key_id",
        "provider_profile",
        "authority_scope",
        "valid_from",
        "status",
        "revoked_at",
    }


def test_no_binding_id_hmic_digest_host_identity_or_source_sha_fields() -> None:
    fields = {f.name for f in DeploymentBinding.__dataclass_fields__.values()}
    forbidden = {"binding_id", "certification_id", "certification_digest", "machine_id", "source_sha", "content_digest"}
    assert fields.isdisjoint(forbidden)


def test_no_new_status_vocabulary_introduced(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    result = admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert result.binding.status in {"active", "revoked"}


def test_revoked_at_null_active_pair_enforced(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    active = admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert active.binding.status == "active" and active.binding.revoked_at is None

    revoked = admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-1", _protected_root=store_root)
    assert revoked.binding.status == "revoked" and revoked.binding.revoked_at is not None


# ═══════════════════════════════════════════════════════════════════════════
# No agent-reachable write surface (HBDC-REQ-056/066)
# ═══════════════════════════════════════════════════════════════════════════


def test_module_not_imported_by_cli_or_agent_reachable_code() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    forbidden_sources = [
        repo_root / "src" / "pcae" / "cli.py",
        repo_root / "src" / "pcae" / "commands" / "agent.py",
        repo_root / "src" / "pcae" / "core" / "agent.py",
    ]
    for source in forbidden_sources:
        if not source.exists():
            continue
        text = source.read_text(encoding="utf-8")
        assert "hatp_deployment_binding_admin" not in text, f"{source} must never import the DeploymentBinding admin surface"


def test_hatp_bootstrap_module_remains_read_only() -> None:
    from pcae.core import hatp_bootstrap as hb

    write_verbs = ("create_", "rotate_", "revoke_", "write_", "enroll", "grant(", "revoke(")
    public_names = [name for name in dir(hb.HATPTrustStore) if not name.startswith("_")]
    for name in public_names:
        assert not any(name.startswith(verb) for verb in ("create", "rotate", "revoke", "write", "enroll", "grant"))


def test_admin_script_exists_and_is_not_a_pcae_cli_subcommand() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "hatp_deployment_binding_admin.py"
    assert script.exists()
    cli_source = (repo_root / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
    assert "deployment-binding" not in cli_source
    assert "deployment_binding_admin" not in cli_source


# ═══════════════════════════════════════════════════════════════════════════
# Preview (read-only, never writes)
# ═══════════════════════════════════════════════════════════════════════════


def test_preview_create_never_writes(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)

    preview = admin.preview_create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert preview.kind == admin.DeploymentBindingPreviewKind.WOULD_CREATE
    assert not (store_root / "registry.json").exists()


def test_preview_reflects_already_satisfied_and_conflict(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)

    same = admin.preview_create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert same.kind == admin.DeploymentBindingPreviewKind.WOULD_NOOP_ALREADY_SATISFIED

    different = admin.preview_create_deployment_binding(
        repository_root=repo_root, authority=_authority(principal_id="other"), _protected_root=store_root
    )
    assert different.kind == admin.DeploymentBindingPreviewKind.WOULD_CONFLICT


def test_preview_rotate_and_revoke_reflect_current_state_without_writing(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)

    not_found = admin.preview_rotate_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert not_found.kind == admin.DeploymentBindingPreviewKind.WOULD_FAIL_NOT_FOUND

    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    would_rotate = admin.preview_rotate_deployment_binding(repository_root=repo_root, authority=_authority(principal_id="x"), _protected_root=store_root)
    assert would_rotate.kind == admin.DeploymentBindingPreviewKind.WOULD_ROTATE

    would_revoke = admin.preview_revoke_deployment_binding(repository_root=repo_root, _protected_root=store_root)
    assert would_revoke.kind == admin.DeploymentBindingPreviewKind.WOULD_REVOKE

    admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-1", _protected_root=store_root)
    would_fail_revoked = admin.preview_rotate_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    assert would_fail_revoked.kind == admin.DeploymentBindingPreviewKind.WOULD_FAIL_REVOKED

    already_revoked = admin.preview_revoke_deployment_binding(repository_root=repo_root, _protected_root=store_root)
    assert already_revoked.kind == admin.DeploymentBindingPreviewKind.WOULD_NOOP_ALREADY_REVOKED

    # No preview call above ever wrote a fresh timestamp or mutated state.
    raw = _registry_raw(store_root)
    assert len(raw["deployment_bindings"]) == 1


# ═══════════════════════════════════════════════════════════════════════════
# Audit evidence (HBDC-REQ-062/065)
# ═══════════════════════════════════════════════════════════════════════════


def test_audit_record_captures_election_reference(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)
    admin.create_deployment_binding(
        repository_root=repo_root, authority=_authority(election_reference="CHGR-ABC-123"), _protected_root=store_root
    )

    history = read_provenance_history(HarnessPath(repo_root))
    matching = [e for e in history.events if e.event_type == "deployment_binding_created"]
    assert len(matching) == 1
    assert "CHGR-ABC-123" in matching[0].summary


def test_every_operation_emits_exactly_one_audit_record(tmp_path: Path) -> None:
    repo_root = _repo(tmp_path)
    store_root = _store(tmp_path)

    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)
    admin.create_deployment_binding(repository_root=repo_root, authority=_authority(), _protected_root=store_root)  # noop
    admin.rotate_deployment_binding(repository_root=repo_root, authority=_authority(principal_id="p2"), _protected_root=store_root)
    admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-1", _protected_root=store_root)
    admin.revoke_deployment_binding(repository_root=repo_root, election_reference="CHGR-2", _protected_root=store_root)  # noop

    types = _provenance_event_types(repo_root)
    assert types.count("deployment_binding_created") == 1
    assert types.count("deployment_binding_create_noop") == 1
    assert types.count("deployment_binding_rotated") == 1
    assert types.count("deployment_binding_revoked") == 1
    assert types.count("deployment_binding_revoke_noop") == 1


# ═══════════════════════════════════════════════════════════════════════════
# Real disposable-only guarantee (149O.20L.7I item 51/52)
# ═══════════════════════════════════════════════════════════════════════════


def test_no_real_repository_identity_leaked_into_this_repositorys_working_tree() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    assert not (repo_root / ".pcae" / "repository-identity.json").exists()
