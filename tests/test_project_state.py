from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_project_state_json() -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "project-state", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


def test_project_state_exits_successfully():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "project-state", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0


def test_project_state_output_is_valid_json():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "project-state", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    data = json.loads(result.stdout)
    assert isinstance(data, dict)


def test_project_state_envelope_fields():
    data = _run_project_state_json()
    assert "schema_version" in data
    assert "generated_at" in data
    assert "source_command" in data
    assert "repository_root" in data
    assert "snapshot" in data
    assert "warnings" in data
    assert "errors" in data
    assert "safety_notes" in data


def test_project_state_snapshot_is_dict():
    data = _run_project_state_json()
    assert isinstance(data["snapshot"], dict)


def test_project_state_required_fields():
    data = _run_project_state_json()
    snap = data["snapshot"]
    required = [
        "snapshot_id",
        "snapshot_version",
        "snapshot_status",
        "snapshot_created_at",
        "source_phase",
        "latest_completed_phase",
        "current_active_phase",
        "current_lifecycle_state",
        "roadmap_position",
        "recommended_next_phase",
        "repository_clean",
        "branch",
        "origin_sync_status",
        "origin_main_head_count",
        "health_status",
        "check_status",
        "doctor_status",
        "push_check_status",
        "execution_authorized",
        "backend_invocation_authorized",
        "prompt_sending_authorized",
        "capture_authorized",
        "intake_authorized",
        "adoption_authorized",
        "source_mutation_authorized",
        "test_mutation_authorized",
        "readme_mutation_authorized",
        "docs_real_captured_tasks_mutation_authorized",
        "active_blockers",
        "active_deferred_items",
        "active_rejected_items",
        "active_risks",
        "accepted_risks",
        "must_never_repeat_controls",
        "stale_signals",
        "evidence_artifacts",
        "evidence_commits",
        "next_safe_actions",
        "forbidden_actions",
        "human_review_required",
        "confidence",
        "safety_notes",
    ]
    for field in required:
        assert field in snap, f"Missing field: {field}"


def test_project_state_latest_completed_phase():
    data = _run_project_state_json()
    snap = data["snapshot"]
    assert snap["latest_completed_phase"] is not None
    assert snap["latest_completed_phase"] != "unknown"


def test_project_state_recommended_next_phase():
    data = _run_project_state_json()
    snap = data["snapshot"]
    assert snap["recommended_next_phase"] is not None


def test_project_state_active_risks_populated():
    data = _run_project_state_json()
    snap = data["snapshot"]
    assert isinstance(snap["active_risks"], list)
    assert len(snap["active_risks"]) > 0


def test_project_state_accepted_risks_separate():
    data = _run_project_state_json()
    snap = data["snapshot"]
    assert isinstance(snap["accepted_risks"], list)
    assert len(snap["accepted_risks"]) > 0
    active_ids = {r["risk_id"] for r in snap["active_risks"]}
    for ar in snap["accepted_risks"]:
        assert ar["risk_id"] not in active_ids, (
            f"Accepted risk {ar['risk_id']} should not be in active_risks"
        )


def test_project_state_stale_signals_visible():
    data = _run_project_state_json()
    snap = data["snapshot"]
    assert isinstance(snap["stale_signals"], list)
    assert len(snap["stale_signals"]) > 0


def test_project_state_must_never_repeat_visible():
    data = _run_project_state_json()
    snap = data["snapshot"]
    assert isinstance(snap["must_never_repeat_controls"], list)
    assert len(snap["must_never_repeat_controls"]) > 0


def test_project_state_next_safe_actions_present():
    data = _run_project_state_json()
    snap = data["snapshot"]
    assert isinstance(snap["next_safe_actions"], list)
    assert len(snap["next_safe_actions"]) > 0


def test_project_state_next_safe_actions_are_recommendations():
    data = _run_project_state_json()
    snap = data["snapshot"]
    for action in snap["next_safe_actions"]:
        assert "recommendation" in action.lower() or "not authorization" in action.lower(), (
            f"next_safe_action should indicate it is a recommendation: {action}"
        )
    assert data["safety_notes"]["next_safe_actions_are_recommendations_not_authorizations"] is True


def test_project_state_forbidden_actions_present():
    data = _run_project_state_json()
    snap = data["snapshot"]
    assert isinstance(snap["forbidden_actions"], list)
    assert len(snap["forbidden_actions"]) > 0


def test_project_state_authorization_booleans_explicit():
    data = _run_project_state_json()
    snap = data["snapshot"]
    auth_fields = [
        "execution_authorized",
        "backend_invocation_authorized",
        "prompt_sending_authorized",
        "capture_authorized",
        "intake_authorized",
        "adoption_authorized",
        "source_mutation_authorized",
        "test_mutation_authorized",
        "readme_mutation_authorized",
        "docs_real_captured_tasks_mutation_authorized",
    ]
    for field in auth_fields:
        assert isinstance(snap[field], bool), f"{field} should be bool"


def test_project_state_high_risk_auth_false():
    data = _run_project_state_json()
    snap = data["snapshot"]
    assert snap["execution_authorized"] is False
    assert snap["backend_invocation_authorized"] is False
    assert snap["prompt_sending_authorized"] is False
    assert snap["capture_authorized"] is False
    assert snap["intake_authorized"] is False
    assert snap["adoption_authorized"] is False
    assert snap["readme_mutation_authorized"] is False
    assert snap["docs_real_captured_tasks_mutation_authorized"] is False


def test_project_state_artifact_index_used():
    data = _run_project_state_json()
    assert data["safety_notes"]["artifact_index_used"] is True


def test_project_state_memory_snapshot_used():
    data = _run_project_state_json()
    assert data["safety_notes"]["memory_snapshot_used"] is True


def test_project_state_governance_timeline_used():
    data = _run_project_state_json()
    assert data["safety_notes"]["governance_timeline_used"] is True


def test_project_state_decision_log_used():
    data = _run_project_state_json()
    assert data["safety_notes"]["decision_log_used"] is True


def test_project_state_risk_register_used():
    data = _run_project_state_json()
    assert data["safety_notes"]["risk_register_used"] is True


def test_project_state_unknown_not_encoded_as_false():
    data = _run_project_state_json()
    snap = data["snapshot"]
    for field in ["health_status", "check_status", "doctor_status", "push_check_status"]:
        assert snap[field] is not False, f"{field} should not be False"


def test_project_state_no_cache_files_created():
    repo_root = Path(__file__).resolve().parent.parent
    pcae_dir = repo_root / ".pcae"
    cache_dir = pcae_dir / "cache"
    state_dir = pcae_dir / "state"
    before_cache = cache_dir.exists()
    before_state = state_dir.exists()
    _run_project_state_json()
    if not before_cache:
        assert not cache_dir.exists(), ".pcae/cache/ was created"
    if not before_state:
        assert not state_dir.exists(), ".pcae/state/ was created"


def test_project_state_no_repository_files_created():
    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=repo_root,
    )
    before = result.stdout
    _run_project_state_json()
    result2 = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=repo_root,
    )
    assert result2.stdout == before, "project-state modified repository files"


def test_project_state_no_authority_inference():
    data = _run_project_state_json()
    notes = data["safety_notes"]
    assert notes["project_state_is_read_only"] is True
    assert notes["project_state_does_not_authorize_execution"] is True
    assert notes["project_state_does_not_authorize_backend_invocation"] is True
    assert notes["project_state_does_not_authorize_adoption"] is True
    assert notes["project_state_does_not_authorize_commit_or_push"] is True


def test_project_state_no_generated_cache():
    data = _run_project_state_json()
    assert data["safety_notes"]["generated_cache_created"] is False
    assert data["safety_notes"]["pcae_storage_created"] is False


def test_project_state_schema_version():
    data = _run_project_state_json()
    assert data["schema_version"] == "0.1"


def test_project_state_source_command():
    data = _run_project_state_json()
    assert data["source_command"] == "pcae project-state"


def test_project_state_layer_summary():
    data = _run_project_state_json()
    assert "layer_summary" in data
    layers = data["layer_summary"]
    assert layers["artifact_index"]["record_count"] > 0
    assert layers["governance_timeline"]["event_count"] > 0
    assert layers["decision_log"]["decision_count"] > 0
    assert layers["risk_register"]["risk_count"] > 0


def test_artifact_index_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "artifact-index", "--json"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["record_count"] > 0


def test_memory_snapshot_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "memory-snapshot", "--json"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "snapshot" in data


def test_governance_timeline_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "governance-timeline", "--json"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["event_count"] > 0


def test_decision_log_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "decision-log", "--json"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["decision_count"] > 0


def test_risk_register_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "risk-register", "--json"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["risk_count"] > 0
