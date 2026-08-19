"""Phase 149O.19.5C -- HMIC Protected Certification State Store.

Phase-boundary verification and behavioral test suite for Wave C (`docs/
PHASE_149O_19_4_..._IMPLEMENTATION_PLAN.md` §9.3): the protected
storage/locking layer extending `src/pcae/core/hatp_mandatory_
certification.py` -- `_certification_transition_lock`,
`_read_certifications`, `_read_certification_bindings`,
`_load_certification_record`, `_load_active_binding`,
`_append_certification_record`, `_write_active_binding`,
`_write_revocation`, and the production-readable `load_certification`/
`load_active_binding` wrappers.

Scope discipline (restated from the 149O.19.5A/B suites, extended to
storage): this phase answers "does artifact ID X exist / what bytes are
stored / which ID is bound / is ID X recorded as revoked?" -- never "is X
a VALID certification?" No test here asserts, exercises, or would be
satisfied by a `CertificationStatus.VALID` outcome, a validation-algorithm
call, an admin-ceremony call, a `pcae` CLI change, or a
`hatp_mandatory_cutover.py` readiness-wiring change. All tests use
isolated, private temporary protected roots -- never `HATPTrustStore.
production().root` for a write.
"""
from __future__ import annotations

import concurrent.futures
import os
import re
import stat
import subprocess
import threading
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core import hatp_mandatory_cutover as hmrc

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_NEW_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"

_REPO_A = "11111111-1111-4111-8111-111111111111"
_REPO_B = "22222222-2222-4222-8222-222222222222"
_REPO_C = "33333333-3333-4333-8333-333333333333"


def _fields(
    *,
    repository_instance_id: str = _REPO_A,
    canonical_deployment_root: str = "/deploy/A",
    implementation_commit: str = "a" * 40,
    implementation_scope_digest: str = "b" * 64,
    verification_record_digest: str = "c" * 64,
    certified_at: str = "2026-08-10T00:00:00Z",
    certified_by: str = "protected-admin",
) -> dict:
    return dict(
        repository_instance_id=repository_instance_id,
        canonical_deployment_root=canonical_deployment_root,
        implementation_commit=implementation_commit,
        implementation_scope_digest=implementation_scope_digest,
        contract_versions={
            "HMRC-001": "1.0",
            "HATP-001": "1.0",
            "HSCE-001": "1.1",
            "RAE-001": "1.0",
            "HBDC-001": "1.0",
            "HPSE-001": "1.1",
            "HHCE-001": "1.1",
        },
        verification_record_digest=verification_record_digest,
        certified_at=certified_at,
        certified_by=certified_by,
    )


def _make_record(fields: dict) -> hmic.CertificationRecord:
    certification_id = hmic.derive_certification_id(fields)
    return hmic.CertificationRecord(certification_id=certification_id, status="active", revoked_at=None, **fields)


# ═══════════════════════════════════════════════════════════════════════════
# HMIC-REQ item-9: no auto-provisioning on ordinary read.
# ═══════════════════════════════════════════════════════════════════════════


def test_read_on_empty_root_is_absent_and_never_creates_anything(tmp_path):
    root = tmp_path / "protected-root"
    result = hmic._read_certifications(root)
    assert result.status == hmic._ReadStatus.ABSENT
    binding_result = hmic._read_certification_bindings(root)
    assert binding_result.status == hmic._ReadStatus.ABSENT
    assert not root.exists(), "a read-only call must never provision the protected root"


def test_load_active_binding_on_empty_root_returns_none_not_error(tmp_path):
    root = tmp_path / "protected-root"
    result = hmic._load_active_binding(root, repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A")
    assert result is None
    assert not root.exists()


def test_load_certification_record_missing_raises_not_found(tmp_path):
    root = tmp_path / "protected-root"
    with pytest.raises(hmic.CertificationRecordNotFoundError):
        hmic._load_certification_record(root, "f" * 64)


# ═══════════════════════════════════════════════════════════════════════════
# HMIC-REQ-025/026: exactly two frozen file names, single shared file,
# keyed entries -- no per-repository directory, no per-certification path.
# ═══════════════════════════════════════════════════════════════════════════


def test_storage_topology_exactly_two_files_no_per_repo_directories(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    hmic._write_active_binding(
        root,
        hmic.CertificationBinding(
            repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A", active_certification_id=record.certification_id
        ),
    )
    entries = sorted(p.name for p in root.iterdir())
    # certifications.json, certification-bindings.json, and the lock file --
    # no directory, no per-certification-ID file.
    assert set(entries) == {"certifications.json", "certification-bindings.json", ".certification-transition.lock"}
    for entry in entries:
        assert (root / entry).is_file()


def test_certification_id_never_appears_as_a_filename_or_path_component(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    for path in root.rglob("*"):
        assert record.certification_id not in path.name


# ═══════════════════════════════════════════════════════════════════════════
# HMIC-REQ-084/098: create-once, idempotent replay, conflict rejection.
# ═══════════════════════════════════════════════════════════════════════════


def test_create_once_first_write_succeeds(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    result = hmic._append_certification_record(root, record)
    assert result.idempotent is False
    assert result.record == record


def test_create_once_identical_replay_is_idempotent_no_op(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    before = (root / "certifications.json").read_bytes()
    result = hmic._append_certification_record(root, record)
    after = (root / "certifications.json").read_bytes()
    assert result.idempotent is True
    assert before == after, "idempotent replay must not rewrite the file"


def test_create_once_different_bytes_same_id_is_rejected_via_self_consistency(tmp_path):
    """A forged record sharing an existing record's `certification_id` but
    differing in an authority-sensitive field will, by construction, no
    longer satisfy the self-consistency check (HMIC-REQ item-16) -- caught
    before the create-once precondition is even consulted, structurally
    eliminating the "different bytes, same ID" case except via genuine
    hash collision."""

    root = tmp_path / "protected-root"
    fields = _fields()
    record = _make_record(fields)
    hmic._append_certification_record(root, record)

    import dataclasses

    forged = dataclasses.replace(record, certified_by="a-different-operator")
    with pytest.raises(hmic.CertificationIdentityMismatchError):
        hmic._append_certification_record(root, forged)

    # The original stored record is untouched.
    reloaded = hmic._load_certification_record(root, record.certification_id)
    assert reloaded == record


def test_append_rejects_pre_revoked_record():
    fields = _fields()
    certification_id = hmic.derive_certification_id(fields)
    pre_revoked = hmic.CertificationRecord(
        certification_id=certification_id, status="revoked", revoked_at="2026-08-10T00:00:01Z", **fields
    )
    with pytest.raises(ValueError):
        hmic._append_certification_record(Path("/nonexistent"), pre_revoked)


def test_append_self_inconsistent_record_rejected_without_touching_disk(tmp_path):
    root = tmp_path / "protected-root"
    fields = _fields()
    real_id = hmic.derive_certification_id(fields)
    bogus = hmic.CertificationRecord(certification_id="0" * 64, status="active", revoked_at=None, **fields)
    assert bogus.certification_id != real_id
    with pytest.raises(hmic.CertificationIdentityMismatchError):
        hmic._append_certification_record(root, bogus)
    assert not root.exists()


# ═══════════════════════════════════════════════════════════════════════════
# HMIC-REQ-083: atomic mkstemp+fsync+os.replace publication.
# ═══════════════════════════════════════════════════════════════════════════


def test_atomic_write_leaves_no_temp_residue_on_success(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    leftovers = [p for p in root.iterdir() if p.name.startswith(".tmp-hmic-")]
    assert leftovers == []


def test_atomic_write_cleans_up_temp_file_on_write_failure(tmp_path, monkeypatch):
    root = tmp_path / "protected-root"
    root.mkdir(parents=True)

    real_fsync = os.fsync

    def failing_fsync(fd):
        raise OSError("simulated fsync failure")

    monkeypatch.setattr(os, "fsync", failing_fsync)
    with pytest.raises(OSError):
        hmic._atomic_write_protected_json(root, root / "certifications.json", {"schema_version": 1, "certifications": []})
    monkeypatch.setattr(os, "fsync", real_fsync)

    leftovers = [p for p in root.iterdir() if p.name.startswith(".tmp-hmic-")]
    assert leftovers == [], "a failed write must not leave temp residue authoritative or lingering forever as a real risk"
    assert not (root / "certifications.json").exists(), "final file must not exist after a failed write"


# ═══════════════════════════════════════════════════════════════════════════
# HMIC-REQ-085/086/090: active-certification binding -- no implicit latest.
# ═══════════════════════════════════════════════════════════════════════════


def test_creating_a_record_does_not_auto_activate_it(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    binding = hmic._load_active_binding(root, repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A")
    assert binding is None, "appending a record must never itself create an active binding"


def test_no_implicit_latest_multiple_records_no_binding_selects_none(tmp_path):
    root = tmp_path / "protected-root"
    record_1 = _make_record(_fields(certified_at="2026-08-10T00:00:00Z", certified_by="op-1"))
    record_2 = _make_record(_fields(certified_at="2026-08-10T01:00:00Z", certified_by="op-2"))
    hmic._append_certification_record(root, record_1)
    hmic._append_certification_record(root, record_2)
    binding = hmic._load_active_binding(root, repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A")
    assert binding is None


def test_explicit_binding_returns_named_record_even_if_another_is_newer(tmp_path):
    root = tmp_path / "protected-root"
    older = _make_record(_fields(certified_at="2026-08-10T00:00:00Z", certified_by="op-1"))
    newer = _make_record(_fields(certified_at="2026-08-10T05:00:00Z", certified_by="op-2"))
    hmic._append_certification_record(root, older)
    hmic._append_certification_record(root, newer)
    hmic._write_active_binding(
        root,
        hmic.CertificationBinding(
            repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A", active_certification_id=older.certification_id
        ),
    )
    binding = hmic._load_active_binding(root, repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A")
    assert binding.active_certification_id == older.certification_id
    assert binding.active_certification_id != newer.certification_id


def test_active_binding_update_replaces_previous_pointer_same_key(tmp_path):
    root = tmp_path / "protected-root"
    record_1 = _make_record(_fields(certified_at="2026-08-10T00:00:00Z", certified_by="op-1"))
    record_2 = _make_record(_fields(certified_at="2026-08-10T01:00:00Z", certified_by="op-2"))
    hmic._append_certification_record(root, record_1)
    hmic._append_certification_record(root, record_2)
    key_kwargs = dict(repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A")
    hmic._write_active_binding(
        root, hmic.CertificationBinding(active_certification_id=record_1.certification_id, **key_kwargs)
    )
    hmic._write_active_binding(
        root, hmic.CertificationBinding(active_certification_id=record_2.certification_id, **key_kwargs)
    )
    binding = hmic._load_active_binding(root, **key_kwargs)
    assert binding.active_certification_id == record_2.certification_id
    # exactly one entry persisted for this key
    doc = hmic._read_certification_bindings(root).document
    matches = [b for b in doc.bindings if (b.repository_instance_id, b.canonical_deployment_root) == (_REPO_A, "/deploy/A")]
    assert len(matches) == 1


def test_revoked_binding_storage_is_not_rewritten_or_cleared(tmp_path):
    """HMIC-REQ item-109: a binding may still point at a revoked ID at the
    storage layer; Wave C never rewrites or clears it."""

    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    key_kwargs = dict(repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A")
    hmic._write_active_binding(root, hmic.CertificationBinding(active_certification_id=record.certification_id, **key_kwargs))
    hmic._write_revocation(root, certification_id=record.certification_id, revoked_at="2026-08-10T02:00:00Z")
    binding = hmic._load_active_binding(root, **key_kwargs)
    assert binding.active_certification_id == record.certification_id


def test_missing_active_certification_id_binding_explicit_none(tmp_path):
    root = tmp_path / "protected-root"
    key_kwargs = dict(repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A")
    hmic._write_active_binding(root, hmic.CertificationBinding(active_certification_id=None, **key_kwargs))
    binding = hmic._load_active_binding(root, **key_kwargs)
    assert binding is not None
    assert binding.active_certification_id is None


# ═══════════════════════════════════════════════════════════════════════════
# HMIC-REQ-091-094/100: revocation.
# ═══════════════════════════════════════════════════════════════════════════


def test_revocation_is_field_mutation_not_deletion(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    hmic._write_revocation(root, certification_id=record.certification_id, revoked_at="2026-08-10T02:00:00Z")
    doc = hmic._read_certifications(root).document
    assert len(doc.certifications) == 1
    revoked = doc.certifications[0]
    assert revoked.certification_id == record.certification_id
    assert revoked.status == "revoked"
    assert revoked.revoked_at == "2026-08-10T02:00:00Z"
    # every other field byte-identical
    assert revoked.implementation_commit == record.implementation_commit
    assert revoked.implementation_scope_digest == record.implementation_scope_digest


def test_revoke_missing_certification_id_raises_not_found(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    with pytest.raises(hmic.CertificationRecordNotFoundError):
        hmic._write_revocation(root, certification_id="f" * 64, revoked_at="2026-08-10T02:00:00Z")


def test_revoke_on_absent_certifications_file_raises_not_found(tmp_path):
    root = tmp_path / "protected-root"
    with pytest.raises(hmic.CertificationRecordNotFoundError):
        hmic._write_revocation(root, certification_id="f" * 64, revoked_at="2026-08-10T02:00:00Z")


def test_revocation_idempotent_identical_replay(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    hmic._write_revocation(root, certification_id=record.certification_id, revoked_at="2026-08-10T02:00:00Z")
    before = (root / "certifications.json").read_bytes()
    hmic._write_revocation(root, certification_id=record.certification_id, revoked_at="2026-08-10T02:00:00Z")
    after = (root / "certifications.json").read_bytes()
    assert before == after


def test_revocation_conflicting_timestamp_rejected_no_un_revoke(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    hmic._write_revocation(root, certification_id=record.certification_id, revoked_at="2026-08-10T02:00:00Z")
    with pytest.raises(hmic.CertificationConflictError):
        hmic._write_revocation(root, certification_id=record.certification_id, revoked_at="2026-08-10T03:00:00Z")
    # still revoked at the original timestamp -- no un-revoke, no silent update.
    doc = hmic._read_certifications(root).document
    assert doc.certifications[0].revoked_at == "2026-08-10T02:00:00Z"


def test_no_un_revoke_api_exists():
    assert not hasattr(hmic, "unrevoke_certification")
    assert not hasattr(hmic, "_unrevoke_certification")
    assert not any("unrevoke" in name.lower() for name in dir(hmic))


def test_revocation_of_non_active_record_has_no_binding_effect(tmp_path):
    root = tmp_path / "protected-root"
    record_1 = _make_record(_fields(certified_at="2026-08-10T00:00:00Z", certified_by="op-1"))
    record_2 = _make_record(_fields(certified_at="2026-08-10T01:00:00Z", certified_by="op-2"))
    hmic._append_certification_record(root, record_1)
    hmic._append_certification_record(root, record_2)
    key_kwargs = dict(repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A")
    hmic._write_active_binding(root, hmic.CertificationBinding(active_certification_id=record_2.certification_id, **key_kwargs))
    # revoke the non-active record
    hmic._write_revocation(root, certification_id=record_1.certification_id, revoked_at="2026-08-10T02:00:00Z")
    binding = hmic._load_active_binding(root, **key_kwargs)
    assert binding.active_certification_id == record_2.certification_id


# ═══════════════════════════════════════════════════════════════════════════
# HMIC-REQ-128: symlink rejection -- root, parent, both files, lock file.
# ═══════════════════════════════════════════════════════════════════════════


def test_symlinked_protected_root_rejected_on_read(tmp_path):
    real_target = tmp_path / "real-elsewhere"
    real_target.mkdir()
    symlinked_root = tmp_path / "symlinked-root"
    symlinked_root.symlink_to(real_target)
    result = hmic._read_certifications(symlinked_root)
    assert result.status == hmic._ReadStatus.MALFORMED


def test_symlinked_protected_root_rejected_on_write(tmp_path):
    real_target = tmp_path / "real-elsewhere"
    real_target.mkdir()
    symlinked_root = tmp_path / "symlinked-root"
    symlinked_root.symlink_to(real_target)
    record = _make_record(_fields())
    with pytest.raises(hmic.CertificationStorageSymlinkError):
        hmic._append_certification_record(symlinked_root, record)


def test_symlinked_certifications_file_rejected(tmp_path):
    root = tmp_path / "protected-root"
    root.mkdir()
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text("{}")
    (root / "certifications.json").symlink_to(elsewhere)
    result = hmic._read_certifications(root)
    assert result.status == hmic._ReadStatus.MALFORMED


def test_symlinked_bindings_file_rejected(tmp_path):
    root = tmp_path / "protected-root"
    root.mkdir()
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text("{}")
    (root / "certification-bindings.json").symlink_to(elsewhere)
    result = hmic._read_certification_bindings(root)
    assert result.status == hmic._ReadStatus.MALFORMED


def test_symlinked_parent_directory_rejected(tmp_path):
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    root = real_parent / "protected-root"
    root.mkdir()
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)

    symlinked_parent = tmp_path / "symlinked-parent"
    symlinked_parent.symlink_to(real_parent)
    aliased_root = symlinked_parent / "protected-root"
    result = hmic._read_certifications(aliased_root)
    assert result.status == hmic._ReadStatus.MALFORMED


def test_write_never_follows_a_symlinked_final_path(tmp_path):
    """A symlink swapped in at the exact final destination path must never
    be written through -- the write fails closed rather than silently
    following the symlink to an attacker-chosen target."""

    root = tmp_path / "protected-root"
    root.mkdir()
    attacker_target = tmp_path / "attacker-owned.json"
    (root / "certifications.json").symlink_to(attacker_target)
    record = _make_record(_fields())
    with pytest.raises((hmic.CertificationStorageSymlinkError, hmic.CertificationMalformedError)):
        hmic._append_certification_record(root, record)
    assert not attacker_target.exists()


# ═══════════════════════════════════════════════════════════════════════════
# Non-regular file rejection (directory/FIFO in place of a certification
# file) -- rejected identically to a symlink.
# ═══════════════════════════════════════════════════════════════════════════


def test_directory_in_place_of_certifications_file_rejected(tmp_path):
    root = tmp_path / "protected-root"
    root.mkdir()
    (root / "certifications.json").mkdir()
    result = hmic._read_certifications(root)
    assert result.status == hmic._ReadStatus.MALFORMED


def test_fifo_in_place_of_certifications_file_rejected(tmp_path):
    root = tmp_path / "protected-root"
    root.mkdir()
    fifo_path = root / "certifications.json"
    os.mkfifo(fifo_path)
    try:
        result = hmic._read_certifications(root)
        assert result.status == hmic._ReadStatus.MALFORMED
    finally:
        fifo_path.unlink()


# ═══════════════════════════════════════════════════════════════════════════
# Malformed vs missing vs absent -- preserved distinctly, never downgraded.
# ═══════════════════════════════════════════════════════════════════════════


def test_malformed_json_is_malformed_not_absent(tmp_path):
    root = tmp_path / "protected-root"
    root.mkdir()
    (root / "certifications.json").write_text("{not valid json")
    result = hmic._read_certifications(root)
    assert result.status == hmic._ReadStatus.MALFORMED


def test_duplicate_json_keys_rejected_as_malformed(tmp_path):
    root = tmp_path / "protected-root"
    root.mkdir()
    (root / "certifications.json").write_text('{"schema_version": 1, "schema_version": 1, "certifications": []}')
    result = hmic._read_certifications(root)
    assert result.status == hmic._ReadStatus.MALFORMED


def test_unknown_schema_version_rejected_as_malformed(tmp_path):
    root = tmp_path / "protected-root"
    root.mkdir()
    (root / "certifications.json").write_text('{"schema_version": 99, "certifications": []}')
    result = hmic._read_certifications(root)
    assert result.status == hmic._ReadStatus.MALFORMED


def test_load_certification_record_on_malformed_document_raises_malformed_not_not_found(tmp_path):
    root = tmp_path / "protected-root"
    root.mkdir()
    (root / "certifications.json").write_text("{not valid json")
    with pytest.raises(hmic.CertificationMalformedError):
        hmic._load_certification_record(root, "f" * 64)


# ═══════════════════════════════════════════════════════════════════════════
# HMIC-REQ-026/027: multi-repository and multi-deployment isolation.
# ═══════════════════════════════════════════════════════════════════════════


def test_multi_repository_isolation(tmp_path):
    root = tmp_path / "protected-root"
    record_a = _make_record(_fields(repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/shared"))
    record_b = _make_record(_fields(repository_instance_id=_REPO_B, canonical_deployment_root="/deploy/shared"))
    hmic._append_certification_record(root, record_a)
    hmic._append_certification_record(root, record_b)
    hmic._write_active_binding(
        root,
        hmic.CertificationBinding(
            repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/shared", active_certification_id=record_a.certification_id
        ),
    )
    hmic._write_active_binding(
        root,
        hmic.CertificationBinding(
            repository_instance_id=_REPO_B, canonical_deployment_root="/deploy/shared", active_certification_id=record_b.certification_id
        ),
    )
    binding_a = hmic._load_active_binding(root, repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/shared")
    binding_b = hmic._load_active_binding(root, repository_instance_id=_REPO_B, canonical_deployment_root="/deploy/shared")
    assert binding_a.active_certification_id == record_a.certification_id
    assert binding_b.active_certification_id == record_b.certification_id
    assert binding_a.active_certification_id != binding_b.active_certification_id


def test_multi_deployment_isolation_same_repository(tmp_path):
    root = tmp_path / "protected-root"
    record_1 = _make_record(_fields(repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/one"))
    record_2 = _make_record(_fields(repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/two"))
    hmic._append_certification_record(root, record_1)
    hmic._append_certification_record(root, record_2)
    hmic._write_active_binding(
        root,
        hmic.CertificationBinding(
            repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/one", active_certification_id=record_1.certification_id
        ),
    )
    binding_one = hmic._load_active_binding(root, repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/one")
    binding_two = hmic._load_active_binding(root, repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/two")
    assert binding_one.active_certification_id == record_1.certification_id
    assert binding_two is None, "deployment /deploy/two must not observe /deploy/one's binding"


def test_revocation_of_one_repository_certification_does_not_affect_another(tmp_path):
    root = tmp_path / "protected-root"
    record_a = _make_record(_fields(repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A"))
    record_b = _make_record(_fields(repository_instance_id=_REPO_B, canonical_deployment_root="/deploy/B"))
    hmic._append_certification_record(root, record_a)
    hmic._append_certification_record(root, record_b)
    hmic._write_revocation(root, certification_id=record_a.certification_id, revoked_at="2026-08-10T02:00:00Z")
    loaded_b = hmic._load_certification_record(root, record_b.certification_id)
    assert loaded_b.status == "active"


def test_copy_attack_does_not_establish_binding_in_new_root(tmp_path):
    """HMIC-REQ item-56/28/30: copying a repo-A-keyed record's *bytes* into
    a separate protected root does not, by itself, create a binding to it
    there; storage never infers validity from mere placement."""

    root_1 = tmp_path / "root-1"
    root_2 = tmp_path / "root-2"
    record = _make_record(_fields())
    hmic._append_certification_record(root_1, record)
    hmic._append_certification_record(root_2, record)  # same bytes, different root -- allowed to exist physically
    binding_root_2 = hmic._load_active_binding(root_2, repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A")
    assert binding_root_2 is None, "existence in root_2 must not itself establish an active binding there"


# ═══════════════════════════════════════════════════════════════════════════
# HMIC-REQ-097/101/102: dedicated lock, distinct from the cutover lock.
# ═══════════════════════════════════════════════════════════════════════════


def test_lock_file_name_is_dedicated_and_distinct_from_cutover_lock():
    assert hmic._CERTIFICATION_TRANSITION_LOCK_FILE_NAME == ".certification-transition.lock"
    assert hmic._CERTIFICATION_TRANSITION_LOCK_FILE_NAME != hmrc._CUTOVER_TRANSITION_LOCK_FILE_NAME


def test_lock_file_created_only_by_write_not_by_read(tmp_path):
    root = tmp_path / "protected-root"
    hmic._read_certifications(root)
    assert not root.exists(), "a read must never create the lock file or the root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    assert (root / hmic._CERTIFICATION_TRANSITION_LOCK_FILE_NAME).exists()


def test_certification_writes_do_not_touch_cutover_lock_or_cutover_record(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    hmic._write_active_binding(
        root,
        hmic.CertificationBinding(
            repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A", active_certification_id=record.certification_id
        ),
    )
    hmic._write_revocation(root, certification_id=record.certification_id, revoked_at="2026-08-10T02:00:00Z")
    assert not (root / hmrc._CUTOVER_TRANSITION_LOCK_FILE_NAME).exists()
    assert not (root / "cutover-record.json").exists()
    assert not (root / "cutover-activation-marker.json").exists()


# ═══════════════════════════════════════════════════════════════════════════
# HMIC-REQ-097-100: concurrency -- real threads, real filesystem, no mocks.
# ═══════════════════════════════════════════════════════════════════════════


def test_concurrent_identical_creation_race_is_deterministic_one_idempotent(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    barrier = threading.Barrier(8)

    def worker():
        barrier.wait()
        return hmic._append_certification_record(root, record)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: worker(), range(8)))

    winners = [r for r in results if not r.idempotent]
    losers = [r for r in results if r.idempotent]
    assert len(winners) == 1
    assert len(losers) == 7
    doc = hmic._read_certifications(root).document
    assert len(doc.certifications) == 1


def test_concurrent_different_certifications_race_no_corruption(tmp_path):
    root = tmp_path / "protected-root"
    records = [
        _make_record(_fields(certified_at=f"2026-08-10T{hour:02d}:00:00Z", certified_by=f"op-{hour}"))
        for hour in range(10, 18)
    ]
    barrier = threading.Barrier(len(records))

    def worker(record):
        barrier.wait()
        return hmic._append_certification_record(root, record)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(records)) as pool:
        results = list(pool.map(worker, records))

    assert all(not r.idempotent for r in results)
    doc = hmic._read_certifications(root).document
    assert len(doc.certifications) == len(records)
    assert len({r.certification_id for r in doc.certifications}) == len(records)


def test_concurrent_active_binding_race_deterministic_final_pointer(tmp_path):
    root = tmp_path / "protected-root"
    records = [
        _make_record(_fields(certified_at=f"2026-08-10T{hour:02d}:00:00Z", certified_by=f"op-{hour}"))
        for hour in range(10, 15)
    ]
    for record in records:
        hmic._append_certification_record(root, record)
    key_kwargs = dict(repository_instance_id=_REPO_A, canonical_deployment_root="/deploy/A")
    barrier = threading.Barrier(len(records))

    def worker(record):
        barrier.wait()
        hmic._write_active_binding(root, hmic.CertificationBinding(active_certification_id=record.certification_id, **key_kwargs))

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(records)) as pool:
        list(pool.map(worker, records))

    binding = hmic._load_active_binding(root, **key_kwargs)
    assert binding is not None
    assert binding.active_certification_id in {r.certification_id for r in records}
    doc = hmic._read_certification_bindings(root).document
    matches = [b for b in doc.bindings if (b.repository_instance_id, b.canonical_deployment_root) == (_REPO_A, "/deploy/A")]
    assert len(matches) == 1, "no torn/duplicate binding entries after a concurrent race"


def test_concurrent_revoke_replay_race_deterministic_no_corruption(tmp_path):
    root = tmp_path / "protected-root"
    record = _make_record(_fields())
    hmic._append_certification_record(root, record)
    barrier = threading.Barrier(8)

    def worker():
        barrier.wait()
        return hmic._write_revocation(root, certification_id=record.certification_id, revoked_at="2026-08-10T02:00:00Z")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: worker(), range(8)))

    for result in results:
        assert result.status == "revoked"
        assert result.revoked_at == "2026-08-10T02:00:00Z"
    doc = hmic._read_certifications(root).document
    assert len(doc.certifications) == 1
    assert doc.certifications[0].status == "revoked"


def test_concurrent_revoke_vs_recertify_race_no_half_applied_state(tmp_path):
    root = tmp_path / "protected-root"
    record_1 = _make_record(_fields(certified_at="2026-08-10T00:00:00Z", certified_by="op-1"))
    record_2 = _make_record(_fields(certified_at="2026-08-10T01:00:00Z", certified_by="op-2"))
    hmic._append_certification_record(root, record_1)
    barrier = threading.Barrier(2)

    def revoke():
        barrier.wait()
        try:
            hmic._write_revocation(root, certification_id=record_1.certification_id, revoked_at="2026-08-10T02:00:00Z")
        except hmic.HATPMandatoryCertificationError:
            pass

    def append_new():
        barrier.wait()
        hmic._append_certification_record(root, record_2)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(revoke), pool.submit(append_new)]
        for future in futures:
            future.result()

    doc = hmic._read_certifications(root).document
    assert len(doc.certifications) == 2
    by_id = {r.certification_id: r for r in doc.certifications}
    assert by_id[record_1.certification_id].status == "revoked"
    assert by_id[record_2.certification_id].status == "active"


# ═══════════════════════════════════════════════════════════════════════════
# Production load entrypoints -- resolve HATPTrustStore.production().root
# internally; never construct/mutate real production state in tests.
# ═══════════════════════════════════════════════════════════════════════════


def test_load_certification_and_load_active_binding_are_read_only_no_write_api_exposed():
    assert not hasattr(hmic, "create_certification")
    assert not hasattr(hmic, "activate_certification")
    assert not hasattr(hmic, "revoke_certification")
    assert not hasattr(hmic, "certify_current_implementation")
    assert not hasattr(hmic, "mark_independently_verified")
    assert not hasattr(hmic, "set_certified")
    for public_name in ("load_certification", "load_active_binding"):
        assert hasattr(hmic, public_name)
        assert not public_name.startswith("_")
    for private_writer in ("_append_certification_record", "_write_active_binding", "_write_revocation"):
        assert hasattr(hmic, private_writer)
        assert private_writer.startswith("_")


def test_import_has_no_side_effect_no_root_resolution_no_directory_creation(tmp_path, monkeypatch):
    """HMIC-REQ item-96: importing the module performs no filesystem
    mutation, no root resolution, no Git/hardware/PB access. Since the
    module is already imported at collection time, this test instead
    re-imports it in a fresh subprocess and confirms the real production
    trust-store path is never touched by import alone."""

    script = (
        "import sys; sys.path.insert(0, %r)\n"
        "import pcae.core.hatp_mandatory_certification\n"
        "print('import ok')\n"
    ) % str(_SRC.parent)
    result = subprocess.run(["python3", "-c", script], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "import ok" in result.stdout


# ═══════════════════════════════════════════════════════════════════════════
# Phase-boundary / production-allowlist / contract byte-identity checks
# (mirroring the 149O.19.5A/B suites' own final section exactly).
# ═══════════════════════════════════════════════════════════════════════════


def _git(*args: str, cwd: Path = _REPO_ROOT) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout


#: Wave A/B symbols that legitimately contain a forbidden substring below
#: (`is_valid_repository_instance_id` is a pure format check re-exported
#: from `repository_identity.py`; `certification_status_satisfies_
#: readiness` is Wave A's closed binary *mapping* function, HMIC-REQ-107 --
#: neither is a Wave D validation-algorithm or readiness-boolean function).
#: `validate_active_hatp_mandatory_independent_verification_certification`
#: and `_validate_at_root` are Wave D's own validation-algorithm entrypoint
#: and test seam (Phase 149O.19.5D, `docs/PHASE_149O_19_5D_HMIC_ACTIVE_
#: CERTIFICATION_VALIDATION_ENGINE.md`) -- a later, separately-scoped,
#: independently-authorized wave of this same module, not something Wave C
#: itself ever implemented. This test's own purpose (Wave C's storage
#: layer never answers "is X VALID?") is unchanged and still enforced by
#: every other assertion in this suite (e.g. Wave C's writers/readers
#: never compute a `CertificationStatus`); only the module-wide symbol
#: inventory legitimately grew once Wave D shipped.
_WAVE_AB_ALLOWED_EXCEPTIONS = frozenset(
    {
        "is_valid_repository_instance_id",
        "certification_status_satisfies_readiness",
        "validate_active_hatp_mandatory_independent_verification_certification",
        "_validate_at_root",
    }
)


def test_no_validation_function_exists_in_module():
    forbidden_substrings = ("is_valid", "is_certified", "validate_active", "get_current_valid")
    names = [name for name in dir(hmic) if not name.startswith("__") and name not in _WAVE_AB_ALLOWED_EXCEPTIONS]
    for name in names:
        lowered = name.lower()
        for forbidden in forbidden_substrings:
            assert forbidden not in lowered, f"unexpected Wave-D-shaped symbol found in Wave C module: {name}"


def test_no_readiness_boolean_function_exists():
    names = [name for name in dir(hmic) if not name.startswith("__") and name not in _WAVE_AB_ALLOWED_EXCEPTIONS]
    for name in names:
        assert "readiness" not in name.lower(), f"unexpected readiness-shaped symbol in Wave C module: {name}"


def test_module_never_imports_cutover_agent_cli_or_permission_broker():
    text = _NEW_MODULE_PATH.read_text(encoding="utf-8")
    forbidden_imports = (
        "hatp_mandatory_cutover",
        "permission_broker",
        "rollback_approval_evidence",
        "commands.agent",
        "pcae.cli",
        "pcae.core.agent",
    )
    import_lines = [line for line in text.splitlines() if line.strip().startswith(("import ", "from "))]
    for forbidden in forbidden_imports:
        for line in import_lines:
            assert forbidden not in line, f"forbidden import found: {line!r}"


# Phase 149O.19.5F (Wave F, gated by Stop Condition W-1 -- independently
# confirmed closed at 149O.19.5E.4) intentionally wires the fresh HMIC
# validator into this readiness ceiling. The two tests below pin to this
# file's own pre-Wave-F phase-entry commit so their original evidentiary
# claims (unwired as of 149O.19.5C) are preserved, not weakened.
_PRE_WAVE_F_COMMIT = "dd6492717ea27a43e16bce3e9c2077a884ed366f"


def _cutover_source_pre_wave_f() -> str:
    return subprocess.run(
        ["git", "show", f"{_PRE_WAVE_F_COMMIT}:src/pcae/core/hatp_mandatory_cutover.py"],
        cwd=str(Path(hmrc.__file__).resolve().parents[3]),
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_hardcoded_false_readiness_ceiling_unchanged():
    text = _cutover_source_pre_wave_f()
    assert '"mandatory_consumption_implementation_independently_verified",' in text
    marker_index = text.index('"mandatory_consumption_implementation_independently_verified",')
    following = text[marker_index:marker_index + 200]
    assert re.search(r'"mandatory_consumption_implementation_independently_verified",\s*\n\s*False,', following)


def test_certification_module_not_imported_by_cutover_module():
    text = _cutover_source_pre_wave_f()
    assert "hatp_mandatory_certification" not in text
