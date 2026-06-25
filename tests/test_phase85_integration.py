"""Phase 85 read-only stack integration tests.

Validates the six read-only commands together: artifact-index, memory-snapshot,
governance-timeline, decision-log, risk-register, project-state. Checks
cross-layer consistency, read-only behavior, no authority inference, and
no storage creation.
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration, pytest.mark.phase_closure]
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

COMMANDS = [
    ("artifact-index", "--json"),
    ("memory-snapshot", "--json"),
    ("governance-timeline", "--json"),
    ("decision-log", "--json"),
    ("risk-register", "--json"),
    ("project-state", "--json"),
]


def _run_cmd(cmd: str, flag: str) -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", cmd, flag],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, f"{cmd} failed: {result.stderr}"
    return json.loads(result.stdout)


# --- All six commands exit successfully ---

def test_all_commands_exit_successfully():
    for cmd, flag in COMMANDS:
        result = subprocess.run(
            [sys.executable, "-m", "pcae", cmd, flag],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"{cmd} exited with {result.returncode}"


def test_all_commands_emit_valid_json():
    for cmd, flag in COMMANDS:
        result = subprocess.run(
            [sys.executable, "-m", "pcae", cmd, flag],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        assert isinstance(data, dict), f"{cmd} did not emit dict"


# --- Common envelope fields ---

def test_all_commands_have_schema_version():
    for cmd, flag in COMMANDS:
        data = _run_cmd(cmd, flag)
        assert "schema_version" in data, f"{cmd} missing schema_version"
        assert data["schema_version"] == "0.1"


def test_all_commands_have_source_command():
    for cmd, flag in COMMANDS:
        data = _run_cmd(cmd, flag)
        assert "source_command" in data, f"{cmd} missing source_command"


def test_all_commands_have_repository_root():
    for cmd, flag in COMMANDS:
        data = _run_cmd(cmd, flag)
        assert "repository_root" in data, f"{cmd} missing repository_root"


def test_all_commands_have_warnings_errors_safety_notes():
    for cmd, flag in COMMANDS:
        data = _run_cmd(cmd, flag)
        assert "warnings" in data, f"{cmd} missing warnings"
        assert "errors" in data, f"{cmd} missing errors"
        assert "safety_notes" in data, f"{cmd} missing safety_notes"


# --- Layer-specific content ---

def test_artifact_index_has_records():
    data = _run_cmd("artifact-index", "--json")
    assert "records" in data
    assert isinstance(data["records"], list)
    assert len(data["records"]) > 0


def test_memory_snapshot_has_snapshot():
    data = _run_cmd("memory-snapshot", "--json")
    assert "snapshot" in data
    assert isinstance(data["snapshot"], dict)


def test_governance_timeline_has_events():
    data = _run_cmd("governance-timeline", "--json")
    assert "events" in data
    assert isinstance(data["events"], list)
    assert len(data["events"]) > 0


def test_decision_log_has_decisions():
    data = _run_cmd("decision-log", "--json")
    assert "decisions" in data
    assert isinstance(data["decisions"], list)
    assert len(data["decisions"]) > 0


def test_risk_register_has_risks():
    data = _run_cmd("risk-register", "--json")
    assert "risks" in data
    assert isinstance(data["risks"], list)
    assert len(data["risks"]) > 0


def test_project_state_has_snapshot():
    data = _run_cmd("project-state", "--json")
    assert "snapshot" in data
    assert isinstance(data["snapshot"], dict)


# --- Cross-layer consistency: project-state uses lower layers ---

def test_project_state_layer_summary_reflects_artifact_index():
    ai = _run_cmd("artifact-index", "--json")
    ps = _run_cmd("project-state", "--json")
    layers = ps.get("layer_summary", {})
    assert layers["artifact_index"]["record_count"] == ai["record_count"]


def test_project_state_layer_summary_reflects_timeline():
    tl = _run_cmd("governance-timeline", "--json")
    ps = _run_cmd("project-state", "--json")
    layers = ps.get("layer_summary", {})
    assert layers["governance_timeline"]["event_count"] == tl["event_count"]


def test_project_state_layer_summary_reflects_decision_log():
    dl = _run_cmd("decision-log", "--json")
    ps = _run_cmd("project-state", "--json")
    layers = ps.get("layer_summary", {})
    assert layers["decision_log"]["decision_count"] == dl["decision_count"]


def test_project_state_layer_summary_reflects_risk_register():
    rr = _run_cmd("risk-register", "--json")
    ps = _run_cmd("project-state", "--json")
    layers = ps.get("layer_summary", {})
    assert layers["risk_register"]["risk_count"] == rr["risk_count"]


def test_project_state_latest_completed_phase_populated():
    ps = _run_cmd("project-state", "--json")
    snap = ps["snapshot"]
    assert snap["latest_completed_phase"] is not None
    assert snap["latest_completed_phase"] != "unknown"


def test_project_state_recommended_next_phase_populated():
    ps = _run_cmd("project-state", "--json")
    snap = ps["snapshot"]
    assert snap["recommended_next_phase"] is not None


def test_project_state_active_risks_from_risk_register():
    rr = _run_cmd("risk-register", "--json")
    ps = _run_cmd("project-state", "--json")
    rr_active_ids = {r["risk_id"] for r in rr["risks"] if r["risk_status"] == "active"}
    ps_active_ids = {r["risk_id"] for r in ps["snapshot"]["active_risks"]}
    assert ps_active_ids == rr_active_ids


def test_project_state_accepted_risks_from_risk_register():
    rr = _run_cmd("risk-register", "--json")
    ps = _run_cmd("project-state", "--json")
    rr_accepted_ids = {r["risk_id"] for r in rr["risks"] if r["risk_status"] == "accepted"}
    ps_accepted_ids = {r["risk_id"] for r in ps["snapshot"]["accepted_risks"]}
    assert ps_accepted_ids == rr_accepted_ids


def test_project_state_stale_signals_from_risk_register():
    rr = _run_cmd("risk-register", "--json")
    ps = _run_cmd("project-state", "--json")
    rr_stale_ids = {r["risk_id"] for r in rr["risks"] if r["risk_status"] == "stale_signal"}
    ps_stale_ids = {r["risk_id"] for r in ps["snapshot"]["stale_signals"]}
    assert ps_stale_ids == rr_stale_ids


def test_project_state_evidence_from_artifact_index():
    ai = _run_cmd("artifact-index", "--json")
    ps = _run_cmd("project-state", "--json")
    ai_paths = {r["artifact_path"] for r in ai["records"] if r["artifact_status"] == "current"}
    ps_paths = set(ps["snapshot"]["evidence_artifacts"])
    assert ps_paths == ai_paths


# --- Accepted risk separation ---

def test_accepted_risk_separate_from_active():
    ps = _run_cmd("project-state", "--json")
    snap = ps["snapshot"]
    active_ids = {r["risk_id"] for r in snap["active_risks"]}
    accepted_ids = {r["risk_id"] for r in snap["accepted_risks"]}
    assert active_ids.isdisjoint(accepted_ids), "Accepted risks overlap with active risks"


def test_accepted_risk_not_treated_as_mitigated():
    rr = _run_cmd("risk-register", "--json")
    assert rr["safety_notes"]["accepted_risk_is_not_mitigation"] is True
    for risk in rr["risks"]:
        if risk["risk_status"] == "accepted":
            assert risk["mitigation"] is None, (
                f"Accepted risk {risk['risk_id']} should not have mitigation"
            )


# --- Stale signal and must-never-repeat visibility ---

def test_stale_signals_visible_in_project_state():
    ps = _run_cmd("project-state", "--json")
    assert len(ps["snapshot"]["stale_signals"]) > 0


def test_must_never_repeat_visible_in_project_state():
    ps = _run_cmd("project-state", "--json")
    assert len(ps["snapshot"]["must_never_repeat_controls"]) > 0


def test_must_never_repeat_visible_in_risk_register():
    rr = _run_cmd("risk-register", "--json")
    mnr_types = {r["risk_type"] for r in rr["risks"]
                 if r["risk_type"] in ("must_never_repeat_risk",
                                       "raw_push_exception_risk",
                                       "hook_bypass_exception_risk")}
    assert len(mnr_types) >= 2


# --- Forbidden actions and next safe actions ---

def test_project_state_forbidden_actions():
    ps = _run_cmd("project-state", "--json")
    snap = ps["snapshot"]
    assert isinstance(snap["forbidden_actions"], list)
    assert len(snap["forbidden_actions"]) > 0


def test_project_state_next_safe_actions_are_recommendations():
    ps = _run_cmd("project-state", "--json")
    snap = ps["snapshot"]
    assert isinstance(snap["next_safe_actions"], list)
    assert len(snap["next_safe_actions"]) > 0
    for action in snap["next_safe_actions"]:
        assert "recommendation" in action.lower() or "not authorization" in action.lower()
    assert ps["safety_notes"]["next_safe_actions_are_recommendations_not_authorizations"] is True


# --- High-risk authorization booleans ---

def test_project_state_high_risk_auth_false():
    ps = _run_cmd("project-state", "--json")
    snap = ps["snapshot"]
    assert snap["execution_authorized"] is False
    assert snap["backend_invocation_authorized"] is False
    assert snap["prompt_sending_authorized"] is False
    assert snap["capture_authorized"] is False
    assert snap["intake_authorized"] is False
    assert snap["adoption_authorized"] is False
    assert snap["readme_mutation_authorized"] is False
    assert snap["docs_real_captured_tasks_mutation_authorized"] is False


def test_decision_log_auth_flags_all_false():
    dl = _run_cmd("decision-log", "--json")
    for dec in dl["decisions"]:
        flags = dec["authorization_flags"]
        for key in ["execution_authorized", "backend_invocation_authorized",
                     "adoption_authorized", "commit_authorized", "push_authorized"]:
            assert flags.get(key) is False, (
                f"{key} should be False in {dec['decision_id']}"
            )


# --- Safety notes across all commands ---

def test_all_commands_no_execution_authorization():
    checks = {
        "artifact-index": "artifact_index_does_not_authorize_execution",
        "memory-snapshot": "memory_snapshot_does_not_authorize_execution",
        "governance-timeline": "governance_timeline_does_not_authorize_execution",
        "decision-log": "decision_log_does_not_authorize_execution",
        "risk-register": "risk_register_does_not_authorize_execution",
        "project-state": "project_state_does_not_authorize_execution",
    }
    for cmd, key in checks.items():
        data = _run_cmd(cmd, "--json")
        assert data["safety_notes"][key] is True, f"{cmd} missing {key}"


def test_all_commands_no_backend_invocation_authorization():
    checks = {
        "memory-snapshot": "memory_snapshot_does_not_authorize_backend_invocation",
        "governance-timeline": "governance_timeline_does_not_authorize_backend_invocation",
        "decision-log": "decision_log_does_not_authorize_backend_invocation",
        "risk-register": "risk_register_does_not_authorize_backend_invocation",
        "project-state": "project_state_does_not_authorize_backend_invocation",
    }
    for cmd, key in checks.items():
        data = _run_cmd(cmd, "--json")
        assert data["safety_notes"][key] is True, f"{cmd} missing {key}"


def test_all_commands_no_adoption_authorization():
    checks = {
        "artifact-index": "artifact_index_does_not_authorize_adoption",
        "memory-snapshot": "memory_snapshot_does_not_authorize_adoption",
        "governance-timeline": "governance_timeline_does_not_authorize_adoption",
        "decision-log": "decision_log_does_not_authorize_adoption",
        "risk-register": "risk_register_does_not_authorize_adoption",
        "project-state": "project_state_does_not_authorize_adoption",
    }
    for cmd, key in checks.items():
        data = _run_cmd(cmd, "--json")
        assert data["safety_notes"][key] is True, f"{cmd} missing {key}"


def test_all_commands_no_commit_push_authorization():
    checks = {
        "artifact-index": "artifact_index_does_not_authorize_commit_or_push",
        "memory-snapshot": "memory_snapshot_does_not_authorize_commit_or_push",
        "governance-timeline": "governance_timeline_does_not_authorize_commit_or_push",
        "decision-log": "decision_log_does_not_authorize_commit_or_push",
        "risk-register": "risk_register_does_not_authorize_commit_or_push",
        "project-state": "project_state_does_not_authorize_commit_or_push",
    }
    for cmd, key in checks.items():
        data = _run_cmd(cmd, "--json")
        assert data["safety_notes"][key] is True, f"{cmd} missing {key}"


# --- No cache/state/.pcae creation ---

def test_no_cache_or_state_created_by_stack():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs_to_check = [
        pcae_dir / "cache",
        pcae_dir / "state",
        pcae_dir / "snapshots",
        pcae_dir / "timelines",
        pcae_dir / "decisions",
        pcae_dir / "risks",
        pcae_dir / "memory",
        pcae_dir / "index",
    ]
    before = {d: d.exists() for d in dirs_to_check}
    for cmd, flag in COMMANDS:
        _run_cmd(cmd, flag)
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created by running commands"


def test_no_repository_mutation_by_stack():
    result1 = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    before = result1.stdout
    for cmd, flag in COMMANDS:
        _run_cmd(cmd, flag)
    result2 = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result2.stdout == before, "Running commands mutated repository files"


# --- Determinism ---

def test_commands_deterministic_counts():
    counts1 = {}
    counts2 = {}
    count_keys = {
        "artifact-index": "record_count",
        "governance-timeline": "event_count",
        "decision-log": "decision_count",
        "risk-register": "risk_count",
    }
    for cmd, key in count_keys.items():
        d1 = _run_cmd(cmd, "--json")
        d2 = _run_cmd(cmd, "--json")
        counts1[cmd] = d1[key]
        counts2[cmd] = d2[key]
    assert counts1 == counts2
