"""Phase 135K — immutable shadow generation storage, atomic pointer,
crash-recovery, and adversarial path-containment tests."""

from __future__ import annotations

import json

import pytest

from pcae.cltr import schema
from pcae.cltr.digest import compute_record_digest
from pcae.cltr.enums import LifecycleState, TransitionType
from pcae.cltr.models import ProductionCltrRecord
from pcae.cltr.persistence import (
    ConflictingGenerationError,
    PathContainmentError,
    list_generations,
    publish_generation,
    read_current_generation,
    read_current_pointer,
    read_generation,
)


def _record(transition_id="135K-PERSIST", **overrides) -> ProductionCltrRecord:
    fields = dict(
        schema_id=schema.SCHEMA_ID,
        schema_version=schema.SCHEMA_VERSION,
        contract_version=schema.CONTRACT_VERSION,
        compatibility_id=schema.COMPATIBILITY_ID,
        transition_id=transition_id,
        phase_id=transition_id,
        repository_identity="repo",
        branch_identity="main",
        transition_type=TransitionType.PROPOSE_TRANSITION,
        lifecycle_state=LifecycleState.PROPOSED,
        source_revision="abc123",
    )
    fields.update(overrides)
    return ProductionCltrRecord(**fields)


def _digested(record: ProductionCltrRecord) -> ProductionCltrRecord:
    return record.with_digest(compute_record_digest(record))


def test_publish_creates_generation_and_pointer(tmp_path):
    root = tmp_path / "cltr-shadow"
    record = _digested(_record())
    handle = publish_generation(record, entry_point="phase_complete", shadow_root=root)
    assert handle.record_path.exists()
    assert handle.manifest_path.exists()
    pointer = read_current_pointer(root)
    assert pointer["transition_id"] == record.transition_id
    assert pointer["record_digest"] == record.record_digest
    assert pointer["shadow_mode"] is True
    assert pointer["authoritative"] is False


def test_generation_is_immutable_no_in_place_rewrite(tmp_path):
    root = tmp_path / "cltr-shadow"
    record = _digested(_record())
    publish_generation(record, entry_point="phase_complete", shadow_root=root)
    different = _digested(_record(final_revision="different"))
    with pytest.raises(ConflictingGenerationError):
        publish_generation(different, entry_point="phase_complete", shadow_root=root)


def test_duplicate_invocation_same_content_is_idempotent(tmp_path):
    root = tmp_path / "cltr-shadow"
    record = _digested(_record())
    h1 = publish_generation(record, entry_point="phase_complete", shadow_root=root)
    h2 = publish_generation(record, entry_point="phase_complete", shadow_root=root)
    assert h1.record_digest == h2.record_digest
    assert len(list_generations(root)) == 1


def test_read_generation_verifies_digest_chain(tmp_path):
    root = tmp_path / "cltr-shadow"
    record = _digested(_record())
    publish_generation(record, entry_point="phase_complete", shadow_root=root)
    generation = read_generation(root, record.transition_id)
    assert generation["manifest"]["record_digest"] == record.record_digest


def test_missing_pointer_returns_none(tmp_path):
    root = tmp_path / "cltr-shadow"
    assert read_current_pointer(root) is None
    assert read_current_generation(root) is None


def test_dangling_pointer_target_returns_none(tmp_path):
    root = tmp_path / "cltr-shadow"
    root.mkdir(parents=True)
    (root / "current").write_text(
        json.dumps({"transition_id": "does-not-exist", "generation_id": "x", "record_digest": "d" * 64, "manifest_digest": "e" * 64}),
        encoding="utf-8",
    )
    assert read_current_generation(root) is None


def test_stale_pointer_digest_mismatch_returns_none(tmp_path):
    root = tmp_path / "cltr-shadow"
    record = _digested(_record())
    publish_generation(record, entry_point="phase_complete", shadow_root=root)
    (root / "current").write_text(
        json.dumps(
            {
                "transition_id": record.transition_id,
                "generation_id": record.transition_id,
                "record_digest": "0" * 64,
                "manifest_digest": "0" * 64,
            }
        ),
        encoding="utf-8",
    )
    assert read_current_generation(root) is None


def test_path_traversal_transition_id_rejected(tmp_path):
    root = tmp_path / "cltr-shadow"
    record = _digested(_record(transition_id="../../etc/passwd"))
    with pytest.raises(PathContainmentError):
        publish_generation(record, entry_point="phase_complete", shadow_root=root)


def test_symlink_generation_directory_rejected(tmp_path):
    root = tmp_path / "cltr-shadow"
    (root / "generations").mkdir(parents=True)
    target = tmp_path / "outside"
    target.mkdir()
    (root / "generations" / "135K-SYMLINK").symlink_to(target)
    record = _digested(_record(transition_id="135K-SYMLINK"))
    with pytest.raises(PathContainmentError):
        publish_generation(record, entry_point="phase_complete", shadow_root=root)


def test_crash_before_finalize_leaves_no_visible_generation(tmp_path, monkeypatch):
    import pcae.cltr.persistence as persistence_module

    root = tmp_path / "cltr-shadow"
    record = _digested(_record())

    original_replace = persistence_module.os.replace
    call_count = {"n": 0}

    def _boom(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise OSError("simulated crash before finalize rename")
        return original_replace(*args, **kwargs)

    monkeypatch.setattr(persistence_module.os, "replace", _boom)
    with pytest.raises(OSError):
        publish_generation(record, entry_point="phase_complete", shadow_root=root)
    assert read_current_pointer(root) is None
    assert list_generations(root) == []
    # The partial candidate must be quarantined, not left dangling in
    # generations/ and never silently promoted.
    quarantine_dir = root / "quarantine"
    assert quarantine_dir.exists()
    assert any(quarantine_dir.iterdir())


def test_crash_after_finalize_before_pointer_is_recoverable(tmp_path, monkeypatch):
    import pcae.cltr.persistence as persistence_module

    root = tmp_path / "cltr-shadow"
    record = _digested(_record())

    original_publish_pointer = persistence_module._publish_current_pointer

    def _boom(*args, **kwargs):
        raise OSError("simulated crash during pointer publication")

    monkeypatch.setattr(persistence_module, "_publish_current_pointer", _boom)
    with pytest.raises(OSError):
        publish_generation(record, entry_point="phase_complete", shadow_root=root)

    # The generation itself is already finalized (immutable) even though
    # the pointer switch failed -- it is safe, complete, and recoverable by
    # a later corrected pointer switch; it must not have been quarantined.
    assert (root / "generations" / record.transition_id / "record.json").exists()
    assert read_current_pointer(root) is None

    # Recovery: republishing the same content is idempotent and completes
    # the pointer switch without rewriting the immutable generation.
    monkeypatch.setattr(persistence_module, "_publish_current_pointer", original_publish_pointer)
    publish_generation(record, entry_point="phase_complete", shadow_root=root)
    assert read_current_pointer(root)["transition_id"] == record.transition_id


def test_list_generations_limit(tmp_path):
    root = tmp_path / "cltr-shadow"
    for i in range(3):
        publish_generation(_digested(_record(transition_id=f"135K-{i}")), entry_point="phase_complete", shadow_root=root)
    assert len(list_generations(root)) == 3
    assert len(list_generations(root, limit=2)) == 2
