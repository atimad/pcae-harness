"""Tests for Phase 149O.20L.7O.3W — `RuntimeInvocationApprovalStore`:
atomicity, path confinement, create-only/duplicate-reject, malformed
artifact handling, restart persistence.

Pure filesystem I/O against a temp directory. Zero subprocess/network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.core import runtime_authority as ra
from pcae.core.runtime_invocation_approval_store import (
    ApprovalStoreIntegrityError,
    RuntimeInvocationApprovalStore,
    STORE_ROOT,
)

from _rdw3w_helpers import build_approval


@pytest.fixture
def store(tmp_path: Path) -> RuntimeInvocationApprovalStore:
    return RuntimeInvocationApprovalStore(tmp_path)


def test_create_then_load_round_trips(store: RuntimeInvocationApprovalStore):
    approval = build_approval()
    store.create(approval)
    loaded = store.load(approval.approval_id)
    assert loaded == approval


def test_canonical_storage_location(tmp_path: Path, store: RuntimeInvocationApprovalStore):
    approval = build_approval()
    store.create(approval)
    expected = tmp_path / STORE_ROOT / approval.approval_id / "approval.json"
    assert expected.exists()
    assert expected.is_file()


def test_load_missing_returns_none(store: RuntimeInvocationApprovalStore):
    assert store.load("ria-" + "0" * 32) is None


def test_create_only_second_write_same_id_rejected(store: RuntimeInvocationApprovalStore):
    approval = build_approval()
    store.create(approval)
    with pytest.raises(ApprovalStoreIntegrityError):
        store.create(approval)  # same object, byte-identical content


def test_create_only_second_write_different_content_same_id_also_rejected(
    store: RuntimeInvocationApprovalStore,
):
    """Unlike the dry path's idempotent-resume-on-identical-content
    behavior, an approval is a one-shot human act: duplicate creation is
    ALWAYS an error, never a silent no-op even with identical content
    (RIASC-001 §9, RIHAC-001 §4)."""
    approval = build_approval()
    store.create(approval)
    import dataclasses

    conflicting = dataclasses.replace(approval, expires_at="2026-08-27T23:00:00Z")
    conflicting = dataclasses.replace(
        conflicting, record_digest=ra.compute_record_digest(conflicting)
    )
    # Force the same approval_id (simulating an ID collision).
    conflicting = dataclasses.replace(conflicting, approval_id=approval.approval_id)
    conflicting = dataclasses.replace(
        conflicting, record_digest=ra.compute_record_digest(conflicting)
    )
    with pytest.raises(ApprovalStoreIntegrityError):
        store.create(conflicting)


@pytest.mark.parametrize("malicious_id", [
    "../../../etc/passwd",
    "ria-" + "0" * 31 + "/../../evil",
    "/etc/passwd",
    "ria-" + "G" * 32,  # uppercase not allowed by pattern
    "ria-" + "0" * 31,  # too short
    "ria-" + "0" * 33,  # too long
    "not-even-prefixed",
    "",
    "ria-../../../x",
])
def test_path_confinement_rejects_malicious_approval_ids(
    tmp_path: Path, store: RuntimeInvocationApprovalStore, malicious_id: str
):
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(malicious_id)
    # Also confirm no path escaped the store root as a side effect.
    root = tmp_path / STORE_ROOT
    if root.exists():
        for p in root.rglob("*"):
            assert str(p.resolve()).startswith(str(root.resolve()))


def test_path_confinement_checked_before_any_path_construction(
    tmp_path: Path, store: RuntimeInvocationApprovalStore
):
    """No file/directory is ever created for a rejected ID -- confinement
    happens strictly before any filesystem interaction."""
    root = tmp_path / STORE_ROOT
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load("../../../escape")
    assert not root.exists() or not any(root.iterdir())


def test_malformed_json_fails_closed(tmp_path: Path, store: RuntimeInvocationApprovalStore):
    approval_id = "ria-" + "1" * 32
    approval_dir = tmp_path / STORE_ROOT / approval_id
    approval_dir.mkdir(parents=True)
    (approval_dir / "approval.json").write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(approval_id)


def test_truncated_json_fails_closed(tmp_path: Path, store: RuntimeInvocationApprovalStore):
    approval = build_approval()
    store.create(approval)
    path = tmp_path / STORE_ROOT / approval.approval_id / "approval.json"
    full = path.read_text(encoding="utf-8")
    path.write_text(full[: len(full) // 2], encoding="utf-8")
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(approval.approval_id)


def test_schema_invalid_artifact_fails_closed(tmp_path: Path, store: RuntimeInvocationApprovalStore):
    approval_id = "ria-" + "2" * 32
    approval_dir = tmp_path / STORE_ROOT / approval_id
    approval_dir.mkdir(parents=True)
    (approval_dir / "approval.json").write_text(json.dumps({"approval_id": approval_id}), encoding="utf-8")
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(approval_id)


def test_unknown_fields_fail_closed(tmp_path: Path, store: RuntimeInvocationApprovalStore):
    approval = build_approval()
    store.create(approval)
    path = tmp_path / STORE_ROOT / approval.approval_id / "approval.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["unexpected_extra_field"] = True
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(approval.approval_id)


def test_mismatched_identity_fails_closed(tmp_path: Path, store: RuntimeInvocationApprovalStore):
    """A document whose internal `approval_id` doesn't match the ID it
    was looked up by is rejected, even if otherwise schema-valid --
    catches a directory/content mismatch (e.g. from a corrupted rename)."""
    a1 = build_approval()
    a2 = build_approval()
    store.create(a1)
    store.create(a2)
    # Overwrite a1's stored file (bypassing the store's own create-only
    # guard, simulating filesystem-level corruption) with a2's content.
    path1 = tmp_path / STORE_ROOT / a1.approval_id / "approval.json"
    path2 = tmp_path / STORE_ROOT / a2.approval_id / "approval.json"
    path1.write_text(path2.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(a1.approval_id)


def test_corrupted_provenance_fails_closed(tmp_path: Path, store: RuntimeInvocationApprovalStore):
    approval = build_approval()
    store.create(approval)
    path = tmp_path / STORE_ROOT / approval.approval_id / "approval.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["provenance"]["identity_evidence_kind"] = "not_a_real_kind"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(approval.approval_id)


def test_corrupted_hash_fails_closed(tmp_path: Path, store: RuntimeInvocationApprovalStore):
    approval = build_approval()
    store.create(approval)
    path = tmp_path / STORE_ROOT / approval.approval_id / "approval.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["record_digest"] = "not-hex-not-64-chars"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(approval.approval_id)


# ── Atomicity ─────────────────────────────────────────────────────────


def test_atomic_write_never_leaves_half_written_valid_artifact(
    tmp_path: Path, store: RuntimeInvocationApprovalStore
):
    approval = build_approval()
    store.create(approval)
    approval_dir = tmp_path / STORE_ROOT / approval.approval_id
    files = list(approval_dir.iterdir())
    assert [f.name for f in files] == ["approval.json"]  # no orphaned .tmp file
    assert not any(f.suffix == ".tmp" for f in files)


def test_preexisting_partial_directory_fails_closed(tmp_path: Path, store: RuntimeInvocationApprovalStore):
    """A pre-existing partial container is corruption, never absence."""
    approval = build_approval()
    approval_dir = tmp_path / STORE_ROOT / approval.approval_id
    approval_dir.mkdir(parents=True)
    tmp_file = approval_dir / "approval.json.tmp"
    tmp_file.write_text("partial content that never got replace()d", encoding="utf-8")
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(approval.approval_id)
    with pytest.raises(ApprovalStoreIntegrityError):
        store.exists(approval.approval_id)


# ── Restart / persistence ────────────────────────────────────────────────


def test_approval_persists_across_store_instances(tmp_path: Path):
    approval = build_approval()
    store1 = RuntimeInvocationApprovalStore(tmp_path)
    store1.create(approval)
    store2 = RuntimeInvocationApprovalStore(tmp_path)  # simulates fresh process
    loaded = store2.load(approval.approval_id)
    assert loaded == approval


def test_exists_reflects_persisted_state(store: RuntimeInvocationApprovalStore):
    approval = build_approval()
    assert not store.exists(approval.approval_id)
    store.create(approval)
    assert store.exists(approval.approval_id)


def test_lookup_never_accepts_caller_supplied_arbitrary_path(
    tmp_path: Path, store: RuntimeInvocationApprovalStore
):
    """The store's public API takes only `approval_id` -- there is no
    method accepting a raw path, so this is a structural (not just
    behavioral) guarantee, verified here via introspection."""
    import inspect

    load_sig = inspect.signature(store.load)
    create_sig = inspect.signature(store.create)
    assert list(load_sig.parameters) == ["approval_id"]
    assert list(create_sig.parameters) == ["approval"]
    for param in load_sig.parameters.values():
        assert param.annotation in (str, inspect.Parameter.empty) or "Path" not in str(
            param.annotation
        )
