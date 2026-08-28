"""Adversarial tests for `human_principal_registry.py` — Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.3."""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path

import pytest

from pcae.core.hpac_foundation import (
    HPACDuplicateError,
    HPACMalformedError,
    HPACSymlinkError,
    ProtectedAdminCapability,
    resolve_hpac_protected_root,
)
from pcae.core.human_principal_registry import (
    CredentialRecord,
    HumanPrincipalRegistryConflictError,
    HumanPrincipalRegistryError,
    HumanPrincipalRegistryNotFoundError,
    HumanPrincipalRegistryStore,
    PrincipalRecord,
    new_credential_id,
    new_principal_id,
)


CAP = ProtectedAdminCapability()


def _store(tmp_path: Path) -> HumanPrincipalRegistryStore:
    return HumanPrincipalRegistryStore(tmp_path / "hpac-root")


def _enroll_principal(store: HumanPrincipalRegistryStore, principal_id: str | None = None) -> PrincipalRecord:
    return store.enroll_principal(
        CAP,
        principal_id=principal_id or new_principal_id(),
        enrollment_provenance_ref="prov-ref-1",
        enrolled_at="2026-08-28T00:00:00Z",
    )


def test_valid_principal_record_enrolls_and_resolves(tmp_path):
    store = _store(tmp_path)
    record = _enroll_principal(store)
    resolved = store.resolve_principal(record.principal_id)
    assert resolved == record
    assert resolved.status == "active"
    assert resolved.revoked_at is None


def test_valid_credential_record_enrolls_and_resolves(tmp_path):
    store = _store(tmp_path)
    principal = _enroll_principal(store)
    credential = store.enroll_credential(
        CAP,
        credential_id=new_credential_id(),
        principal_id=principal.principal_id,
        mechanism_id="hpac.deterministic.test-only.v1",
        public_key="pubkey-bytes",
        assurance_capabilities=("up", "uv"),
        enrollment_provenance_ref="prov-ref-2",
        enrolled_at="2026-08-28T00:00:01Z",
    )
    resolved = store.resolve_credential(credential.credential_id)
    assert resolved == credential
    assert resolved.principal_id == principal.principal_id
    # HPAC-REQ-013: no private key/PIN/biometric/path field exists at all.
    assert not hasattr(credential, "private_key")
    assert not hasattr(credential, "pin")
    assert not hasattr(credential, "repository_path")


def test_malformed_record_unknown_field_rejected(tmp_path):
    store = _store(tmp_path)
    store.path.parent.mkdir(parents=True, exist_ok=True)
    import json

    bad_doc = {
        "schema_version": "HPAC-REGISTRY/2.0",
        "principals": [
            {
                "principal_id": "hp-x",
                "status": "active",
                "enrollment_provenance_ref": "r",
                "enrolled_at": "2026-08-28T00:00:00Z",
                "revoked_at": None,
                "sneaky_extra_field": "trust-me",
            }
        ],
        "credentials": [],
    }
    store.path.write_text(json.dumps(bad_doc), encoding="utf-8")
    with pytest.raises(HPACMalformedError):
        store.resolve_principal("hp-x")


def test_duplicate_principal_id_rejected(tmp_path):
    store = _store(tmp_path)
    pid = new_principal_id()
    _enroll_principal(store, pid)
    with pytest.raises(HumanPrincipalRegistryConflictError):
        _enroll_principal(store, pid)


def test_duplicate_credential_id_in_document_rejected(tmp_path):
    store = _store(tmp_path)
    store.path.parent.mkdir(parents=True, exist_ok=True)
    import json

    doc = {
        "schema_version": "HPAC-REGISTRY/2.0",
        "principals": [
            {
                "principal_id": "hp-a",
                "status": "active",
                "enrollment_provenance_ref": "r",
                "enrolled_at": "2026-08-28T00:00:00Z",
                "revoked_at": None,
            }
        ],
        "credentials": [
            {
                "credential_id": "hpc-dup",
                "principal_id": "hp-a",
                "mechanism_id": "m",
                "public_key": "k",
                "assurance_capabilities": ["up"],
                "status": "active",
                "enrollment_provenance_ref": "r",
                "enrolled_at": "2026-08-28T00:00:00Z",
                "revoked_at": None,
            },
            {
                "credential_id": "hpc-dup",
                "principal_id": "hp-a",
                "mechanism_id": "m",
                "public_key": "k2",
                "assurance_capabilities": ["up"],
                "status": "active",
                "enrollment_provenance_ref": "r",
                "enrolled_at": "2026-08-28T00:00:00Z",
                "revoked_at": None,
            },
        ],
    }
    store.path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(HPACMalformedError):
        store.resolve_credential("hpc-dup")


def test_revoked_principal_is_monotonic_and_idempotent(tmp_path):
    store = _store(tmp_path)
    principal = _enroll_principal(store)
    first = store.revoke_principal(CAP, principal_id=principal.principal_id, revoked_at="2026-08-28T01:00:00Z")
    assert first.status == "revoked"
    # Later revocation of an already-revoked principal is an idempotent no-op.
    second = store.revoke_principal(CAP, principal_id=principal.principal_id, revoked_at="2026-08-28T02:00:00Z")
    assert second == first


def test_revoke_unknown_principal_not_found(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(HumanPrincipalRegistryNotFoundError):
        store.revoke_principal(CAP, principal_id="hp-nonexistent", revoked_at="2026-08-28T00:00:00Z")


def test_enroll_credential_against_missing_principal_fails_closed(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(HumanPrincipalRegistryConflictError):
        store.enroll_credential(
            CAP,
            credential_id=new_credential_id(),
            principal_id="hp-does-not-exist",
            mechanism_id="m",
            public_key="k",
            assurance_capabilities=("up",),
            enrollment_provenance_ref="r",
            enrolled_at="2026-08-28T00:00:00Z",
        )


def test_enroll_credential_against_revoked_principal_fails_closed(tmp_path):
    store = _store(tmp_path)
    principal = _enroll_principal(store)
    store.revoke_principal(CAP, principal_id=principal.principal_id, revoked_at="2026-08-28T01:00:00Z")
    with pytest.raises(HumanPrincipalRegistryConflictError):
        store.enroll_credential(
            CAP,
            credential_id=new_credential_id(),
            principal_id=principal.principal_id,
            mechanism_id="m",
            public_key="k",
            assurance_capabilities=("up",),
            enrollment_provenance_ref="r",
            enrolled_at="2026-08-28T02:00:00Z",
        )


def test_credential_mapping_one_principal_many_credentials(tmp_path):
    store = _store(tmp_path)
    principal = _enroll_principal(store)
    c1 = store.enroll_credential(
        CAP, credential_id=new_credential_id(), principal_id=principal.principal_id,
        mechanism_id="m1", public_key="k1", assurance_capabilities=("up",),
        enrollment_provenance_ref="r", enrolled_at="2026-08-28T00:00:00Z",
    )
    c2 = store.enroll_credential(
        CAP, credential_id=new_credential_id(), principal_id=principal.principal_id,
        mechanism_id="m2", public_key="k2", assurance_capabilities=("up", "uv"),
        enrollment_provenance_ref="r", enrolled_at="2026-08-28T00:00:01Z",
    )
    creds = store.list_credentials()
    assert {c.credential_id for c in creds} == {c1.credential_id, c2.credential_id}
    assert all(c.principal_id == principal.principal_id for c in creds)


def test_repository_path_substitution_is_structurally_impossible(tmp_path):
    """Repository-controlled state cannot select the registry: the store
    only ever reads the `root` its constructor was given; nothing in its
    API accepts a repository/cwd/env override, so pointing two stores at
    two different roots yields two independent registries no matter what
    a caller (agent, repo config, env var) claims."""

    store_a = HumanPrincipalRegistryStore(tmp_path / "root-a")
    store_b = HumanPrincipalRegistryStore(tmp_path / "root-b")
    principal = _enroll_principal(store_a)
    assert store_b.resolve_principal(principal.principal_id) is None


def test_registry_path_resolution_ignores_env_and_cwd(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    monkeypatch.setenv("PCAE_HPAC_ROOT", str(tmp_path / "attacker-controlled"))
    monkeypatch.chdir(tmp_path)
    root_1 = resolve_hpac_protected_root()
    monkeypatch.setenv("HOME", str(tmp_path / "different-fake-home"))
    root_2 = resolve_hpac_protected_root()
    assert root_1 == root_2  # zero-argument, environment-independent resolution


def test_symlinked_registry_path_rejected(tmp_path):
    real_root = tmp_path / "real-root"
    real_root.mkdir()
    link_root = tmp_path / "link-root"
    os.symlink(real_root, link_root)
    store = HumanPrincipalRegistryStore(link_root)
    with pytest.raises(HPACSymlinkError):
        store.resolve_principal("hp-anything")


def test_dataclass_replace_forgery_never_becomes_canonical(tmp_path):
    """Trust-forgery regression: `dataclasses.replace()` on a resolved
    PrincipalRecord produces a Python object, not canonical registry
    state -- resolving the *same* principal_id from the store must still
    reflect only what the store itself wrote, never a caller's in-memory
    mutation."""

    store = _store(tmp_path)
    principal = _enroll_principal(store)
    forged = dataclasses.replace(principal, status="active", enrollment_provenance_ref="attacker-forged")
    assert forged.enrollment_provenance_ref == "attacker-forged"
    resolved_again = store.resolve_principal(principal.principal_id)
    assert resolved_again.enrollment_provenance_ref == "prov-ref-1"
    assert resolved_again != forged


def test_caller_constructed_equivalent_object_is_not_canonical(tmp_path):
    """A hand-constructed `PrincipalRecord` with plausible-looking fields
    is never accepted as canonically enrolled merely because it is
    schema-valid: the store's read path only ever returns what mutation
    APIs actually wrote."""

    store = _store(tmp_path)
    lookalike = PrincipalRecord(
        principal_id="hp-" + "a" * 32,
        status="active",
        enrollment_provenance_ref="forged",
        enrolled_at="2026-08-28T00:00:00Z",
        revoked_at=None,
    )
    resolved = store.resolve_principal(lookalike.principal_id)
    assert resolved is None  # never enrolled through the store, never resolves


def test_no_admin_capability_no_mutation(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(HumanPrincipalRegistryError):
        store.enroll_principal(
            "not-a-capability",  # type: ignore[arg-type]
            principal_id=new_principal_id(),
            enrollment_provenance_ref="r",
            enrolled_at="2026-08-28T00:00:00Z",
        )
