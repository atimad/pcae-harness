from __future__ import annotations

import json
import subprocess
import sys

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_GATES = [
    "task_start_gate", "scope_check_gate", "backend_invocation_gate",
    "prompt_send_gate", "capture_acceptance_gate", "intake_review_gate",
    "adoption_approval_gate", "source_mutation_gate", "test_mutation_gate",
    "commit_gate", "push_gate", "rollback_gate", "storage_write_gate",
    "permission_broker_gate", "shell_command_gate",
]

VALID_DECISIONS = {
    "allow", "deny", "requires_human_review", "requires_more_evidence",
    "blocked_by_risk", "blocked_by_scope", "blocked_by_lifecycle_state",
    "blocked_by_missing_artifact", "blocked_by_must_never_repeat_control",
    "unknown",
}

HIGH_RISK_GATES = {
    "backend_invocation_gate", "prompt_send_gate", "adoption_approval_gate",
    "permission_broker_gate", "shell_command_gate",
}

WRITE_CAPABLE_GATES = {
    "source_mutation_gate", "commit_gate", "push_gate", "rollback_gate",
    "storage_write_gate",
}


def _run_gate_dry_run_json() -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "gate-dry-run", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


def test_gate_dry_run_exits_successfully():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "gate-dry-run", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0


def test_gate_dry_run_output_is_valid_json():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "gate-dry-run", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    data = json.loads(result.stdout)
    assert isinstance(data, dict)


def test_gate_dry_run_envelope_fields():
    data = _run_gate_dry_run_json()
    assert "schema_version" in data
    assert "generated_at" in data
    assert "source_command" in data
    assert "repository_root" in data
    assert "dry_run" in data
    assert "taxonomy_version" in data
    assert "gate_count" in data
    assert "gates" in data
    assert "warnings" in data
    assert "errors" in data
    assert "safety_notes" in data


def test_gate_dry_run_is_true():
    data = _run_gate_dry_run_json()
    assert data["dry_run"] is True


def test_gate_dry_run_taxonomy_version():
    data = _run_gate_dry_run_json()
    assert data["taxonomy_version"] == "0.1"


def test_gate_dry_run_gate_count():
    data = _run_gate_dry_run_json()
    assert data["gate_count"] == 15
    assert len(data["gates"]) == 15


def test_gate_dry_run_all_expected_gates_present():
    data = _run_gate_dry_run_json()
    gate_ids = {g["gate_id"] for g in data["gates"]}
    for expected in EXPECTED_GATES:
        assert expected in gate_ids, f"Missing gate: {expected}"


def test_gate_dry_run_gate_required_fields():
    data = _run_gate_dry_run_json()
    required = [
        "gate_id", "gate_name", "gate_category", "protected_action",
        "risk_level", "decision", "reason_codes", "human_review_required",
        "evidence_artifacts", "evidence_events", "evidence_decisions",
        "evidence_risks", "allowed_scope", "denied_scope",
        "requested_action", "requested_actor", "requested_files",
        "dry_run", "enforcement_performed", "authorization_granted",
        "safety_notes", "generated_at", "schema_version",
    ]
    for gate in data["gates"]:
        for field in required:
            assert field in gate, f"Missing {field} in {gate['gate_id']}"


def test_gate_dry_run_valid_decision_values():
    data = _run_gate_dry_run_json()
    for gate in data["gates"]:
        assert gate["decision"] in VALID_DECISIONS, (
            f"Invalid decision {gate['decision']} in {gate['gate_id']}"
        )


def test_gate_dry_run_reason_codes_are_lists():
    data = _run_gate_dry_run_json()
    for gate in data["gates"]:
        assert isinstance(gate["reason_codes"], list)


def test_gate_dry_run_enforcement_false():
    data = _run_gate_dry_run_json()
    for gate in data["gates"]:
        assert gate["enforcement_performed"] is False, (
            f"enforcement_performed should be False in {gate['gate_id']}"
        )


def test_gate_dry_run_authorization_false():
    data = _run_gate_dry_run_json()
    for gate in data["gates"]:
        assert gate["authorization_granted"] is False, (
            f"authorization_granted should be False in {gate['gate_id']}"
        )


def test_gate_dry_run_envelope_no_backend():
    data = _run_gate_dry_run_json()
    assert data["safety_notes"]["backend_invocation_performed"] is False


def test_gate_dry_run_envelope_no_repo_mutation():
    data = _run_gate_dry_run_json()
    assert data["safety_notes"]["repo_mutation_performed"] is False


def test_gate_dry_run_envelope_no_storage():
    data = _run_gate_dry_run_json()
    assert data["safety_notes"]["storage_written"] is False


def test_gate_dry_run_permission_broker_not_implemented():
    data = _run_gate_dry_run_json()
    assert data["safety_notes"]["permission_broker_not_implemented"] is True


def test_gate_dry_run_shell_gate_not_implemented():
    data = _run_gate_dry_run_json()
    assert data["safety_notes"]["shell_gate_not_implemented"] is True


def test_gate_dry_run_storage_not_implemented():
    data = _run_gate_dry_run_json()
    assert data["safety_notes"]["storage_not_implemented"] is True


def test_gate_dry_run_high_risk_no_auto_allow():
    data = _run_gate_dry_run_json()
    for gate in data["gates"]:
        if gate["gate_id"] in HIGH_RISK_GATES:
            assert gate["decision"] != "allow", (
                f"High-risk gate {gate['gate_id']} should not auto-allow"
            )


def test_gate_dry_run_write_capable_no_auto_allow():
    data = _run_gate_dry_run_json()
    for gate in data["gates"]:
        if gate["gate_id"] in WRITE_CAPABLE_GATES:
            assert gate["decision"] != "allow", (
                f"Write-capable gate {gate['gate_id']} should not auto-allow"
            )


def test_gate_dry_run_no_allow_from_recommendation():
    data = _run_gate_dry_run_json()
    for gate in data["gates"]:
        assert gate["decision"] != "allow", (
            f"Gate {gate['gate_id']} should not auto-allow in dry-run"
        )


def test_gate_dry_run_no_cache_files_created():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs_to_check = [
        pcae_dir / "cache", pcae_dir / "gates", pcae_dir / "state",
        pcae_dir / "decisions",
    ]
    before = {d: d.exists() for d in dirs_to_check}
    _run_gate_dry_run_json()
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"


def test_gate_dry_run_no_repository_mutation():
    result1 = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    before = result1.stdout
    _run_gate_dry_run_json()
    result2 = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result2.stdout == before


def test_artifact_index_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "artifact-index", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["record_count"] > 0


def test_memory_snapshot_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "memory-snapshot", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0


def test_governance_timeline_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "governance-timeline", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0


def test_decision_log_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "decision-log", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0


def test_risk_register_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "risk-register", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0


def test_project_state_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "project-state", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
