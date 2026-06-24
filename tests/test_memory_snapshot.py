from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_memory_snapshot_json() -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "memory-snapshot", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


def test_memory_snapshot_exits_successfully():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "memory-snapshot", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0


def test_memory_snapshot_output_is_valid_json():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "memory-snapshot", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    data = json.loads(result.stdout)
    assert isinstance(data, dict)


def test_memory_snapshot_envelope_fields():
    data = _run_memory_snapshot_json()
    assert "schema_version" in data
    assert "generated_at" in data
    assert "source_command" in data
    assert "repository_root" in data
    assert "snapshot" in data
    assert "warnings" in data
    assert "errors" in data
    assert "safety_notes" in data


def test_memory_snapshot_snapshot_is_dict():
    data = _run_memory_snapshot_json()
    assert isinstance(data["snapshot"], dict)


def test_memory_snapshot_required_fields():
    data = _run_memory_snapshot_json()
    snapshot = data["snapshot"]
    required = [
        "memory_snapshot_id",
        "memory_model_version",
        "project_id",
        "repository_path",
        "current_phase",
        "latest_completed_phase",
        "current_lifecycle_state",
        "roadmap_position",
        "phase_sequence_position",
        "last_verified_commit",
        "origin_sync_status",
        "health_status",
        "governance_status",
        "artifact_index_status",
        "timeline_status",
        "decision_log_status",
        "risk_status",
        "next_safe_actions",
        "forbidden_actions",
        "provenance",
        "safety_notes",
    ]
    for field in required:
        assert field in snapshot, f"Missing field: {field}"


def test_memory_snapshot_latest_completed_phase_populated():
    data = _run_memory_snapshot_json()
    snapshot = data["snapshot"]
    assert snapshot["latest_completed_phase"] is not None


def test_memory_snapshot_artifact_index_available():
    data = _run_memory_snapshot_json()
    snapshot = data["snapshot"]
    assert snapshot["artifact_index_status"] in ("available", "partial")


def test_memory_snapshot_provenance_has_artifacts():
    data = _run_memory_snapshot_json()
    provenance = data["snapshot"]["provenance"]
    assert "source_artifacts" in provenance
    assert isinstance(provenance["source_artifacts"], list)
    assert len(provenance["source_artifacts"]) > 0


def test_memory_snapshot_provenance_has_commit():
    data = _run_memory_snapshot_json()
    provenance = data["snapshot"]["provenance"]
    assert "head_commit" in provenance
    assert provenance["head_commit"] is not None


def test_memory_snapshot_unknown_not_encoded_as_false():
    data = _run_memory_snapshot_json()
    snapshot = data["snapshot"]
    for field in ["timeline_status", "decision_log_status", "risk_status"]:
        assert snapshot[field] is not False, f"{field} should not be False"


def test_memory_snapshot_safety_notes_present():
    data = _run_memory_snapshot_json()
    notes = data["safety_notes"]
    assert notes["memory_snapshot_is_read_only"] is True
    assert notes["memory_snapshot_does_not_authorize_execution"] is True
    assert notes["memory_snapshot_does_not_authorize_backend_invocation"] is True
    assert notes["memory_snapshot_does_not_authorize_adoption"] is True
    assert notes["memory_snapshot_does_not_authorize_commit_or_push"] is True
    assert notes["generated_cache_created"] is False
    assert notes["pcae_storage_created"] is False
    assert notes["artifact_index_used"] is True


def test_memory_snapshot_no_cache_files_created():
    repo_root = Path(__file__).resolve().parent.parent
    pcae_dir = repo_root / ".pcae"
    cache_dir = pcae_dir / "cache"
    snapshot_dir = pcae_dir / "snapshots"
    before_cache = cache_dir.exists()
    before_snapshot = snapshot_dir.exists()
    _run_memory_snapshot_json()
    if not before_cache:
        assert not cache_dir.exists(), ".pcae/cache/ was created"
    if not before_snapshot:
        assert not snapshot_dir.exists(), ".pcae/snapshots/ was created"


def test_memory_snapshot_no_authority_inference():
    data = _run_memory_snapshot_json()
    notes = data["safety_notes"]
    assert notes["memory_snapshot_does_not_authorize_execution"] is True
    assert notes["memory_snapshot_does_not_authorize_backend_invocation"] is True
    assert notes["memory_snapshot_does_not_authorize_adoption"] is True
    assert notes["memory_snapshot_does_not_authorize_commit_or_push"] is True


def test_memory_snapshot_forbidden_actions_populated():
    data = _run_memory_snapshot_json()
    snapshot = data["snapshot"]
    assert isinstance(snapshot["forbidden_actions"], list)
    assert len(snapshot["forbidden_actions"]) > 0


def test_memory_snapshot_schema_version():
    data = _run_memory_snapshot_json()
    assert data["schema_version"] == "0.1"


def test_artifact_index_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "artifact-index", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["record_count"] > 0
