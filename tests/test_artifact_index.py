from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_artifact_index_json() -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "artifact-index", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


def test_artifact_index_exits_successfully():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "artifact-index", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0


def test_artifact_index_output_is_valid_json():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "artifact-index", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    data = json.loads(result.stdout)
    assert isinstance(data, dict)


def test_artifact_index_envelope_fields():
    data = _run_artifact_index_json()
    assert "schema_version" in data
    assert "generated_at" in data
    assert "source_command" in data
    assert "repository_root" in data
    assert "records" in data
    assert "warnings" in data
    assert "errors" in data
    assert "safety_notes" in data


def test_artifact_index_records_is_list():
    data = _run_artifact_index_json()
    assert isinstance(data["records"], list)
    assert len(data["records"]) > 0


def test_artifact_index_record_fields():
    data = _run_artifact_index_json()
    required_fields = [
        "artifact_id",
        "artifact_type",
        "artifact_path",
        "artifact_title",
        "artifact_status",
        "artifact_version",
        "source_phase",
        "created_phase",
        "last_updated_phase",
        "implementation_status",
        "authoritative_for",
        "supersedes",
        "superseded_by",
        "related_artifacts",
        "evidence_level",
        "freshness_status",
        "hash_or_commit_ref",
        "required_for_memory_queries",
        "safety_notes",
    ]
    for record in data["records"]:
        for field in required_fields:
            assert field in record, f"Missing field {field} in record {record.get('artifact_id')}"


def test_artifact_index_key_artifacts_present():
    data = _run_artifact_index_json()
    ids = {r["artifact_id"] for r in data["records"]}
    expected = {
        "roadmap-reconciliation-phase-85-plan",
        "persistent-lifecycle-memory-model",
        "artifact-index-design",
        "governance-event-timeline-design",
        "decision-log-integration-design",
        "risk-register-design",
        "project-state-snapshot-design",
        "phase-85-implementation-roadmap",
        "phase-85-data-model-storage-design",
        "multi-agent-governance-summary",
        "full-health-baseline-84k3",
        "project-status",
        "changelog",
        "readme",
    }
    for artifact_id in expected:
        assert artifact_id in ids, f"Expected artifact {artifact_id} not found"


def test_artifact_index_type_mapping():
    data = _run_artifact_index_json()
    type_map = {r["artifact_id"]: r["artifact_type"] for r in data["records"]}
    assert type_map["persistent-lifecycle-memory-model"] == "memory_model_artifact"
    assert type_map["artifact-index-design"] == "artifact_index_design_artifact"
    assert type_map["governance-event-timeline-design"] == "timeline_design_artifact"
    assert type_map["risk-register-design"] == "risk_register_design_artifact"
    assert type_map["project-status"] == "status_artifact"
    assert type_map["changelog"] == "changelog_artifact"
    assert type_map["readme"] == "readme_artifact"


def test_artifact_index_unknown_not_encoded_as_false():
    data = _run_artifact_index_json()
    for record in data["records"]:
        if record["artifact_status"] == "missing":
            assert record["freshness_status"] != False
            assert record["evidence_level"] != False


def test_artifact_index_safety_notes_present():
    data = _run_artifact_index_json()
    notes = data["safety_notes"]
    assert notes["artifact_index_is_read_only"] is True
    assert notes["artifact_index_does_not_authorize_execution"] is True
    assert notes["artifact_index_does_not_authorize_adoption"] is True
    assert notes["artifact_index_does_not_authorize_commit_or_push"] is True
    assert notes["generated_cache_created"] is False
    assert notes["pcae_storage_created"] is False


def test_artifact_index_no_cache_files_created():
    repo_root = Path(__file__).resolve().parent.parent
    pcae_dir = repo_root / ".pcae"
    cache_dir = pcae_dir / "cache"
    index_dir = pcae_dir / "index"
    before_cache = cache_dir.exists()
    before_index = index_dir.exists()
    _run_artifact_index_json()
    if not before_cache:
        assert not cache_dir.exists(), ".pcae/cache/ was created by artifact-index command"
    if not before_index:
        assert not index_dir.exists(), ".pcae/index/ was created by artifact-index command"


def test_artifact_index_no_authority_inference():
    data = _run_artifact_index_json()
    notes = data["safety_notes"]
    assert notes["artifact_index_does_not_authorize_execution"] is True
    assert notes["artifact_index_does_not_authorize_adoption"] is True
    assert notes["artifact_index_does_not_authorize_commit_or_push"] is True


def test_artifact_index_present_artifacts_have_commit_ref():
    data = _run_artifact_index_json()
    for record in data["records"]:
        if record["artifact_status"] == "current":
            assert record["hash_or_commit_ref"] is not None, (
                f"Present artifact {record['artifact_id']} missing commit ref"
            )


def test_artifact_index_schema_version():
    data = _run_artifact_index_json()
    assert data["schema_version"] == "0.1"


def test_artifact_index_record_count():
    data = _run_artifact_index_json()
    assert data["record_count"] == len(data["records"])
    assert data["present_count"] + data["missing_count"] == data["record_count"]
