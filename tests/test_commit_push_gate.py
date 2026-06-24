from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(extra_args: list[str] | None = None) -> dict:
    cmd = [sys.executable, "-m", "pcae", "gate-dry-run", "--json"]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


def _gate(data: dict, gate_id: str) -> dict:
    for g in data["gates"]:
        if g["gate_id"] == gate_id:
            return g
    raise AssertionError(f"{gate_id} not found")


def test_default_still_works():
    data = _run()
    assert data["gate_count"] == 15
    assert data["dry_run"] is True


def test_commit_gate_present():
    data = _run()
    assert _gate(data, "commit_gate")["gate_id"] == "commit_gate"


def test_push_gate_present():
    data = _run()
    assert _gate(data, "push_gate")["gate_id"] == "push_gate"


def test_commit_gate_has_commit_evaluation():
    data = _run(["--requested-action", "commit"])
    gate = _gate(data, "commit_gate")
    assert "commit_evaluation" in gate


def test_push_gate_has_push_evaluation():
    data = _run(["--requested-action", "push"])
    gate = _gate(data, "push_gate")
    assert "push_evaluation" in gate


def test_commit_evaluation_required_fields():
    data = _run(["--requested-action", "commit"])
    ce = _gate(data, "commit_gate")["commit_evaluation"]
    for field in ["commit_status", "requested_action", "repository_clean",
                  "staged_changes_detected", "unstaged_changes_detected",
                  "commit_message_present", "human_approval_detected",
                  "task_contract_detected", "task_contract_path",
                  "lifecycle_state", "check_status", "health_status",
                  "evidence_sources", "commit_notes"]:
        assert field in ce, f"Missing commit_evaluation field: {field}"


def test_push_evaluation_required_fields():
    data = _run(["--requested-action", "push"])
    pe = _gate(data, "push_gate")["push_evaluation"]
    for field in ["push_status", "requested_action", "branch",
                  "origin_sync_status", "origin_main_head_count",
                  "push_target", "raw_push_detected", "force_push_detected",
                  "human_approval_detected", "task_contract_detected",
                  "task_contract_path", "lifecycle_state",
                  "push_check_status", "evidence_sources", "push_notes"]:
        assert field in pe, f"Missing push_evaluation field: {field}"


def test_commit_does_not_create_commit():
    data = _run(["--requested-action", "commit", "--commit-message-present", "--human-approved"])
    gate = _gate(data, "commit_gate")
    assert gate["authorization_granted"] is False
    assert gate["enforcement_performed"] is False
    assert gate["decision"] != "allow"


def test_push_does_not_push():
    data = _run(["--requested-action", "push", "--push-target", "origin/main", "--human-approved"])
    gate = _gate(data, "push_gate")
    assert gate["authorization_granted"] is False
    assert gate["enforcement_performed"] is False
    assert gate["decision"] != "allow"


def test_commit_does_not_stage():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-action", "commit", "--commit-message-present"])
    r2 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == before


def test_push_does_not_raw_push():
    data = _run(["--requested-action", "push"])
    pe = _gate(data, "push_gate").get("push_evaluation", {})
    assert pe.get("raw_push_detected") is False
    assert pe.get("force_push_detected") is False


def test_human_approved_does_not_authorize_commit():
    data = _run(["--requested-action", "commit", "--human-approved", "--commit-message-present"])
    gate = _gate(data, "commit_gate")
    assert gate["authorization_granted"] is False
    assert gate["decision"] != "allow"


def test_human_approved_does_not_authorize_push():
    data = _run(["--requested-action", "push", "--human-approved", "--push-target", "origin/main"])
    gate = _gate(data, "push_gate")
    assert gate["authorization_granted"] is False
    assert gate["decision"] != "allow"


def test_commit_message_present_does_not_authorize():
    data = _run(["--requested-action", "commit", "--commit-message-present"])
    gate = _gate(data, "commit_gate")
    assert gate["authorization_granted"] is False
    ce = gate["commit_evaluation"]
    assert ce["commit_message_present"] is True


def test_push_target_does_not_authorize():
    data = _run(["--requested-action", "push", "--push-target", "origin/main"])
    gate = _gate(data, "push_gate")
    assert gate["authorization_granted"] is False
    pe = gate["push_evaluation"]
    assert pe["push_target"] == "origin/main"


def test_all_gates_authorization_false():
    data = _run(["--requested-action", "commit", "--human-approved", "--commit-message-present"])
    for g in data["gates"]:
        assert g["authorization_granted"] is False
        assert g["enforcement_performed"] is False


def test_envelope_commit_push_safety_notes():
    data = _run()
    n = data["safety_notes"]
    assert n["commit_gate_dry_run_only"] is True
    assert n["commit_gate_does_not_stage_files"] is True
    assert n["commit_gate_does_not_create_commit"] is True
    assert n["commit_gate_does_not_authorize_commit"] is True
    assert n["push_gate_dry_run_only"] is True
    assert n["push_gate_does_not_push"] is True
    assert n["push_gate_does_not_raw_push"] is True
    assert n["push_gate_does_not_force_push"] is True
    assert n["push_gate_does_not_authorize_push"] is True
    assert n["human_approval_flag_is_not_commit_authorization"] is True
    assert n["human_approval_flag_is_not_push_authorization"] is True
    assert n["clean_repo_is_not_commit_authorization"] is True
    assert n["push_check_pass_is_not_push_authorization"] is True


def test_repo_mutation_performed_false():
    data = _run(["--requested-action", "commit"])
    assert data["safety_notes"]["repo_mutation_performed"] is False


def test_backend_invocation_performed_false():
    data = _run(["--requested-action", "push"])
    assert data["safety_notes"]["backend_invocation_performed"] is False


def test_storage_written_false():
    data = _run(["--requested-action", "commit"])
    assert data["safety_notes"]["storage_written"] is False


def test_scope_gate_still_works():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "src/pcae/core/gate_dry_run.py"])
    scope = _gate(data, "scope_check_gate")
    assert "scope_evaluation" in scope
    assert scope["authorization_granted"] is False


def test_backend_gate_still_works():
    data = _run(["--requested-action", "backend_invocation",
                 "--requested-backend", "claude", "--prompt-present"])
    bg = _gate(data, "backend_invocation_gate")
    assert "backend_evaluation" in bg
    assert bg["authorization_granted"] is False


def test_adoption_gate_still_works():
    data = _run(["--requested-action", "adoption",
                 "--requested-file", "src/example.py",
                 "--adoption-artifact-present"])
    ag = _gate(data, "adoption_approval_gate")
    assert "adoption_evaluation" in ag
    assert ag["authorization_granted"] is False


def test_no_cache_files_created():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs = [pcae_dir / "cache", pcae_dir / "gates", pcae_dir / "commits", pcae_dir / "pushes"]
    before = {d: d.exists() for d in dirs}
    _run(["--requested-action", "commit", "--commit-message-present"])
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"


def test_no_repository_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-action", "push", "--push-target", "origin/main", "--human-approved"])
    r2 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == before


def test_existing_commands_still_work():
    for cmd in ["artifact-index", "memory-snapshot", "governance-timeline",
                "decision-log", "risk-register", "project-state"]:
        result = subprocess.run(
            [sys.executable, "-m", "pcae", cmd, "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"{cmd} failed"
