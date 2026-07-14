"""Phase 135O — ``transition_id`` design B tests (135M §8.3, resolved 135N)."""

from __future__ import annotations

import uuid

from pcae.cltr.migration.transition_identity import resolve_transition_id


def test_stable_for_same_logical_transition(tmp_path):
    root = tmp_path / "migration"
    first = resolve_transition_id(
        phase_id="135O-T1", entry_point="phase_complete", migration_epoch="e1",
        source_revision="rev-a", migration_root=root,
    )
    second = resolve_transition_id(
        phase_id="135O-T1", entry_point="phase_complete", migration_epoch="e1",
        source_revision="rev-a", migration_root=root,
    )
    assert first.transition_id == second.transition_id
    assert second.replay is True
    assert first.replay is False


def test_distinct_phase_ids_yield_distinct_ids(tmp_path):
    root = tmp_path / "migration"
    a = resolve_transition_id(phase_id="P1", entry_point="phase_complete", migration_epoch="e1", source_revision="r", migration_root=root)
    b = resolve_transition_id(phase_id="P2", entry_point="phase_complete", migration_epoch="e1", source_revision="r", migration_root=root)
    assert a.transition_id != b.transition_id


def test_distinct_entry_points_yield_distinct_ids(tmp_path):
    root = tmp_path / "migration"
    a = resolve_transition_id(phase_id="P1", entry_point="phase_complete", migration_epoch="e1", source_revision="r", migration_root=root)
    b = resolve_transition_id(phase_id="P1", entry_point="task_finish", migration_epoch="e1", source_revision="r", migration_root=root)
    assert a.transition_id != b.transition_id


def test_changed_source_revision_is_a_new_transition_with_predecessor_link(tmp_path):
    root = tmp_path / "migration"
    first = resolve_transition_id(phase_id="P1", entry_point="phase_complete", migration_epoch="e1", source_revision="rev-a", migration_root=root)
    second = resolve_transition_id(phase_id="P1", entry_point="phase_complete", migration_epoch="e1", source_revision="rev-b", migration_root=root)
    assert second.transition_id != first.transition_id
    assert second.predecessor_transition_id == first.transition_id
    assert second.replay is False


def test_no_collision_between_two_distinct_attempts_for_same_phase_id(tmp_path):
    root = tmp_path / "migration"
    ids = set()
    for i in range(5):
        result = resolve_transition_id(phase_id="P-collision", entry_point="phase_complete", migration_epoch="e1", source_revision=f"rev-{i}", migration_root=root)
        ids.add(result.transition_id)
    assert len(ids) == 5


def test_transition_id_is_a_valid_uuid(tmp_path):
    root = tmp_path / "migration"
    result = resolve_transition_id(phase_id="P1", entry_point="phase_complete", migration_epoch="e1", source_revision="r", migration_root=root)
    uuid.UUID(result.transition_id)  # raises ValueError if malformed


def test_no_title_dependency(tmp_path):
    root = tmp_path / "migration"
    a = resolve_transition_id(phase_id="P1", entry_point="phase_complete", migration_epoch="e1", source_revision="r", migration_root=root)
    # Resolving again with the identical logical key never consults any
    # "title" parameter -- the function signature has none.
    b = resolve_transition_id(phase_id="P1", entry_point="phase_complete", migration_epoch="e1", source_revision="r", migration_root=root)
    assert a.transition_id == b.transition_id


def test_no_git_or_subprocess_dependency(tmp_path, monkeypatch):
    import subprocess

    def _boom(*args, **kwargs):
        raise AssertionError("resolve_transition_id must never invoke subprocess")

    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(subprocess, "Popen", _boom)
    root = tmp_path / "migration"
    resolve_transition_id(phase_id="P1", entry_point="phase_complete", migration_epoch="e1", source_revision="r", migration_root=root)


def test_missing_required_field_raises(tmp_path):
    import pytest

    root = tmp_path / "migration"
    with pytest.raises(ValueError):
        resolve_transition_id(phase_id="", entry_point="phase_complete", migration_epoch="e1", source_revision="r", migration_root=root)


def test_replay_after_persistence_is_stable(tmp_path):
    root = tmp_path / "migration"
    first = resolve_transition_id(phase_id="P1", entry_point="task_finish", migration_epoch="e1", source_revision="r", migration_root=root)
    for _ in range(3):
        replay = resolve_transition_id(phase_id="P1", entry_point="task_finish", migration_epoch="e1", source_revision="r", migration_root=root)
        assert replay.transition_id == first.transition_id
        assert replay.replay is True
