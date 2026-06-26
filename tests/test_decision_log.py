from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_decision_log_json() -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "decision-log", "--json"],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def _decision_data() -> dict:
    """Run decision-log once per worker; all field-checking tests share the result."""
    return _run_decision_log_json()


@pytest.fixture(scope="module")
def _decision_data2() -> dict:
    """Second independent run for determinism tests."""
    return _run_decision_log_json()


def test_decision_log_exits_successfully(_decision_data) -> None:
    assert _decision_data is not None


def test_decision_log_output_is_valid_json(_decision_data) -> None:
    assert isinstance(_decision_data, dict)


def test_decision_log_envelope_fields(_decision_data) -> None:
    data = _decision_data
    assert "schema_version" in data
    assert "generated_at" in data
    assert "source_command" in data
    assert "repository_root" in data
    assert "decisions" in data
    assert "decision_count" in data
    assert "warnings" in data
    assert "errors" in data
    assert "safety_notes" in data


def test_decision_log_decisions_is_list(_decision_data) -> None:
    assert isinstance(_decision_data["decisions"], list)


def test_decision_log_decision_count_matches(_decision_data) -> None:
    assert _decision_data["decision_count"] == len(_decision_data["decisions"])


def test_decision_log_required_fields(_decision_data) -> None:
    data = _decision_data
    required = [
        "decision_id",
        "decision_type",
        "decision_status",
        "decision_timestamp",
        "source_phase",
        "source_artifact",
        "source_event",
        "source_commit",
        "decision_maker",
        "human_required",
        "approved_scope",
        "denied_scope",
        "deferred_scope",
        "rejected_scope",
        "affected_files",
        "affected_agents",
        "authorization_flags",
        "risk_level",
        "supersedes",
        "superseded_by",
        "related_decisions",
        "related_artifacts",
        "related_events",
        "evidence_level",
        "safety_notes",
    ]
    assert len(data["decisions"]) > 0
    for dec in data["decisions"][:5]:
        for field in required:
            assert field in dec, f"Missing field: {field} in decision {dec.get('decision_id')}"


def test_decision_log_decisions_are_deterministic(_decision_data, _decision_data2) -> None:
    ids1 = [d["decision_id"] for d in _decision_data["decisions"]]
    ids2 = [d["decision_id"] for d in _decision_data2["decisions"]]
    assert ids1 == ids2


def test_decision_log_decisions_ordered_deterministically(_decision_data, _decision_data2) -> None:
    order1 = [(d["source_phase"], d["decision_type"], d["decision_id"]) for d in _decision_data["decisions"]]
    order2 = [(d["source_phase"], d["decision_type"], d["decision_id"]) for d in _decision_data2["decisions"]]
    assert order1 == order2


def test_decision_log_decision_ids_stable(_decision_data, _decision_data2) -> None:
    for d1, d2 in zip(_decision_data["decisions"], _decision_data2["decisions"]):
        assert d1["decision_id"] == d2["decision_id"]


def test_decision_log_86c_evidence(_decision_data) -> None:
    phase_86c = [d for d in _decision_data["decisions"] if d["source_phase"] == "86C"]
    assert len(phase_86c) > 0
    types = {d["decision_type"] for d in phase_86c}
    assert "phase_completion_decision" in types


def test_decision_log_86d_evidence(_decision_data) -> None:
    phase_86d = [d for d in _decision_data["decisions"] if d["source_phase"] == "86D"]
    assert len(phase_86d) > 0


def test_decision_log_86e_evidence(_decision_data) -> None:
    phase_86e = [d for d in _decision_data["decisions"] if d["source_phase"] == "86E"]
    assert len(phase_86e) > 0


def test_decision_log_authorization_flags_explicit(_decision_data) -> None:
    for dec in _decision_data["decisions"]:
        flags = dec["authorization_flags"]
        assert isinstance(flags, dict), f"authorization_flags not dict in {dec['decision_id']}"
        assert "execution_authorized" in flags
        assert "backend_invocation_authorized" in flags
        assert "commit_authorized" in flags
        assert "push_authorized" in flags


def test_decision_log_high_risk_auth_flags_false(_decision_data) -> None:
    high_risk = [
        "execution_authorized",
        "backend_invocation_authorized",
        "prompt_sending_authorized",
        "capture_authorized",
        "intake_authorized",
        "adoption_authorized",
        "commit_authorized",
        "push_authorized",
        "storage_authorized",
    ]
    for dec in _decision_data["decisions"]:
        flags = dec["authorization_flags"]
        for flag in high_risk:
            assert flags.get(flag) is False, (
                f"{flag} should be False in {dec['decision_id']}, got {flags.get(flag)}"
            )


def test_decision_log_denied_deferred_rejected_fields_exist(_decision_data) -> None:
    for dec in _decision_data["decisions"][:5]:
        assert "denied_scope" in dec
        assert "deferred_scope" in dec
        assert "rejected_scope" in dec


def test_decision_log_artifact_index_used(_decision_data) -> None:
    assert _decision_data["safety_notes"]["artifact_index_used"] is True


def test_decision_log_memory_snapshot_used(_decision_data) -> None:
    assert _decision_data["safety_notes"]["memory_snapshot_used"] is True


def test_decision_log_governance_timeline_used(_decision_data) -> None:
    assert _decision_data["safety_notes"]["governance_timeline_used"] is True


def test_decision_log_unknown_not_encoded_as_false(_decision_data) -> None:
    for dec in _decision_data["decisions"]:
        if dec["decision_timestamp"] is not None:
            assert dec["decision_timestamp"] is not False
        if dec["source_artifact"] is not None:
            assert dec["source_artifact"] is not False
        if dec["source_event"] is not None:
            assert dec["source_event"] is not False
        if dec["source_commit"] is not None:
            assert dec["source_commit"] is not False


def test_decision_log_no_cache_files_created() -> None:
    pcae_dir = _REPO_ROOT / ".pcae"
    cache_dir = pcae_dir / "cache"
    decision_dir = pcae_dir / "decisions"
    before_cache = cache_dir.exists()
    before_decision = decision_dir.exists()
    _run_decision_log_json()
    if not before_cache:
        assert not cache_dir.exists(), ".pcae/cache/ was created"
    if not before_decision:
        assert not decision_dir.exists(), ".pcae/decisions/ was created"


def test_decision_log_no_repository_files_created() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=_REPO_ROOT,
    )
    before = result.stdout
    _run_decision_log_json()
    result2 = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=_REPO_ROOT,
    )
    assert result2.stdout == before, "decision-log modified repository files"


def test_decision_log_no_authority_inference(_decision_data) -> None:
    notes = _decision_data["safety_notes"]
    assert notes["decision_log_is_read_only"] is True
    assert notes["decision_log_does_not_authorize_execution"] is True
    assert notes["decision_log_does_not_authorize_backend_invocation"] is True
    assert notes["decision_log_does_not_authorize_adoption"] is True
    assert notes["decision_log_does_not_authorize_commit_or_push"] is True


def test_decision_log_no_generated_cache(_decision_data) -> None:
    assert _decision_data["safety_notes"]["generated_cache_created"] is False
    assert _decision_data["safety_notes"]["pcae_storage_created"] is False


def test_decision_log_schema_version(_decision_data) -> None:
    assert _decision_data["schema_version"] == "0.1"


def test_decision_log_source_command(_decision_data) -> None:
    assert _decision_data["source_command"] == "pcae decision-log"


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


def test_governance_timeline_still_works() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "governance-timeline", "--json"],
        capture_output=True, text=True,
        cwd=_REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["event_count"] > 0
