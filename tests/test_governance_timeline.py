from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_timeline_json() -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "governance-timeline", "--json"],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def _timeline_data() -> dict:
    """Run governance-timeline once per worker; all field-checking tests share the result."""
    return _run_timeline_json()


@pytest.fixture(scope="module")
def _timeline_data2() -> dict:
    """Second independent run for determinism tests."""
    return _run_timeline_json()


def test_governance_timeline_exits_successfully(_timeline_data) -> None:
    assert _timeline_data is not None


def test_governance_timeline_output_is_valid_json(_timeline_data) -> None:
    assert isinstance(_timeline_data, dict)


def test_governance_timeline_envelope_fields(_timeline_data) -> None:
    data = _timeline_data
    assert "schema_version" in data
    assert "generated_at" in data
    assert "source_command" in data
    assert "repository_root" in data
    assert "events" in data
    assert "event_count" in data
    assert "warnings" in data
    assert "errors" in data
    assert "safety_notes" in data


def test_governance_timeline_events_is_list(_timeline_data) -> None:
    assert isinstance(_timeline_data["events"], list)


def test_governance_timeline_event_count_matches(_timeline_data) -> None:
    assert _timeline_data["event_count"] == len(_timeline_data["events"])


def test_governance_timeline_required_event_fields(_timeline_data) -> None:
    data = _timeline_data
    required = [
        "event_id",
        "event_type",
        "event_status",
        "event_timestamp",
        "source_phase",
        "source_artifact",
        "source_commit",
        "actor",
        "agent_id",
        "human_required",
        "authorization_required",
        "authorization_status",
        "affected_files",
        "related_artifacts",
        "related_events",
        "causal_parent_events",
        "evidence_level",
        "freshness_status",
        "safety_notes",
    ]
    assert len(data["events"]) > 0
    for evt in data["events"][:5]:
        for field in required:
            assert field in evt, f"Missing field: {field} in event {evt.get('event_id')}"


def test_governance_timeline_events_are_deterministic(_timeline_data, _timeline_data2) -> None:
    ids1 = [e["event_id"] for e in _timeline_data["events"]]
    ids2 = [e["event_id"] for e in _timeline_data2["events"]]
    assert ids1 == ids2


def test_governance_timeline_event_ids_stable(_timeline_data, _timeline_data2) -> None:
    for e1, e2 in zip(_timeline_data["events"], _timeline_data2["events"]):
        assert e1["event_id"] == e2["event_id"]


def test_governance_timeline_events_ordered_deterministically(_timeline_data, _timeline_data2) -> None:
    order1 = [(e["source_phase"], e["event_type"], e["event_id"]) for e in _timeline_data["events"]]
    order2 = [(e["source_phase"], e["event_type"], e["event_id"]) for e in _timeline_data2["events"]]
    assert order1 == order2


def test_governance_timeline_86c_evidence(_timeline_data) -> None:
    phase_86c_events = [e for e in _timeline_data["events"] if e["source_phase"] == "86C"]
    assert len(phase_86c_events) > 0
    types = {e["event_type"] for e in phase_86c_events}
    assert "artifact_documented" in types or "prototype_implemented" in types


def test_governance_timeline_86d_evidence(_timeline_data) -> None:
    phase_86d_events = [e for e in _timeline_data["events"] if e["source_phase"] == "86D"]
    assert len(phase_86d_events) > 0
    types = {e["event_type"] for e in phase_86d_events}
    assert "artifact_documented" in types or "prototype_implemented" in types


def test_governance_timeline_artifact_index_used(_timeline_data) -> None:
    assert _timeline_data["safety_notes"]["artifact_index_used"] is True


def test_governance_timeline_memory_snapshot_used(_timeline_data) -> None:
    assert _timeline_data["safety_notes"]["memory_snapshot_used"] is True


def test_governance_timeline_unknown_not_encoded_as_false(_timeline_data) -> None:
    for evt in _timeline_data["events"]:
        if evt["event_timestamp"] is not None:
            assert evt["event_timestamp"] is not False, (
                f"event_timestamp should not be False for {evt['event_id']}"
            )
        if evt["source_artifact"] is not None:
            assert evt["source_artifact"] is not False
        if evt["source_commit"] is not None:
            assert evt["source_commit"] is not False


def test_governance_timeline_no_cache_files_created() -> None:
    pcae_dir = _REPO_ROOT / ".pcae"
    cache_dir = pcae_dir / "cache"
    timeline_dir = pcae_dir / "timelines"
    before_cache = cache_dir.exists()
    before_timeline = timeline_dir.exists()
    _run_timeline_json()
    if not before_cache:
        assert not cache_dir.exists(), ".pcae/cache/ was created"
    if not before_timeline:
        assert not timeline_dir.exists(), ".pcae/timelines/ was created"


def test_governance_timeline_no_repository_files_created() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=_REPO_ROOT,
    )
    before = result.stdout
    _run_timeline_json()
    result2 = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=_REPO_ROOT,
    )
    assert result2.stdout == before, "governance-timeline modified repository files"


def test_governance_timeline_no_authority_inference(_timeline_data) -> None:
    notes = _timeline_data["safety_notes"]
    assert notes["governance_timeline_is_read_only"] is True
    assert notes["governance_timeline_does_not_authorize_execution"] is True
    assert notes["governance_timeline_does_not_authorize_backend_invocation"] is True
    assert notes["governance_timeline_does_not_authorize_adoption"] is True
    assert notes["governance_timeline_does_not_authorize_commit_or_push"] is True


def test_governance_timeline_no_generated_cache(_timeline_data) -> None:
    assert _timeline_data["safety_notes"]["generated_cache_created"] is False
    assert _timeline_data["safety_notes"]["pcae_storage_created"] is False


def test_governance_timeline_schema_version(_timeline_data) -> None:
    assert _timeline_data["schema_version"] == "0.1"


def test_governance_timeline_source_command(_timeline_data) -> None:
    assert _timeline_data["source_command"] == "pcae governance-timeline"


def test_artifact_index_still_works() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "artifact-index", "--json"],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["record_count"] > 0


def test_memory_snapshot_still_works() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "memory-snapshot", "--json"],
        capture_output=True, text=True,
        cwd=_REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "snapshot" in data
