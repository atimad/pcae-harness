from __future__ import annotations

import json
import subprocess
import sys

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]
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


def test_adoption_approval_gate_present():
    data = _run()
    gate = _gate(data, "adoption_approval_gate")
    assert gate["gate_id"] == "adoption_approval_gate"


def test_source_mutation_gate_present():
    data = _run()
    gate = _gate(data, "source_mutation_gate")
    assert gate["gate_id"] == "source_mutation_gate"


def test_test_mutation_gate_present():
    data = _run()
    gate = _gate(data, "test_mutation_gate")
    assert gate["gate_id"] == "test_mutation_gate"


def test_adoption_gate_has_adoption_evaluation():
    data = _run(["--requested-action", "adoption", "--requested-file", "src/example.py"])
    gate = _gate(data, "adoption_approval_gate")
    assert "adoption_evaluation" in gate


def test_source_mutation_gate_has_mutation_evaluation():
    data = _run(["--requested-action", "source_mutation", "--requested-file", "src/pcae/core/gate_dry_run.py"])
    gate = _gate(data, "source_mutation_gate")
    assert "mutation_evaluation" in gate


def test_test_mutation_gate_has_mutation_evaluation():
    data = _run(["--requested-action", "test_mutation", "--requested-file", "tests/test_example.py"])
    gate = _gate(data, "test_mutation_gate")
    assert "mutation_evaluation" in gate


def test_adoption_evaluation_required_fields():
    data = _run(["--requested-action", "adoption", "--requested-file", "src/example.py"])
    ae = _gate(data, "adoption_approval_gate")["adoption_evaluation"]
    for field in ["adoption_status", "requested_action", "requested_files",
                  "adoption_artifact_present", "adoption_review_detected",
                  "adoption_approval_detected", "human_approval_detected",
                  "task_contract_detected", "task_contract_path",
                  "scope_status", "evidence_sources", "adoption_notes"]:
        assert field in ae, f"Missing adoption_evaluation field: {field}"


def test_mutation_evaluation_required_fields():
    data = _run(["--requested-action", "source_mutation", "--requested-file", "src/pcae/core/gate_dry_run.py"])
    me = _gate(data, "source_mutation_gate")["mutation_evaluation"]
    for field in ["mutation_status", "requested_action", "requested_files",
                  "mutation_type", "scope_status", "matched_allowed_files",
                  "matched_forbidden_files", "unknown_files",
                  "human_approval_detected", "task_contract_detected",
                  "task_contract_path", "evidence_sources", "mutation_notes"]:
        assert field in me, f"Missing mutation_evaluation field: {field}"


def test_adoption_does_not_approve():
    data = _run(["--requested-action", "adoption", "--requested-file", "src/example.py",
                 "--adoption-artifact-present"])
    gate = _gate(data, "adoption_approval_gate")
    assert gate["authorization_granted"] is False
    assert gate["decision"] != "allow"
    ae = gate["adoption_evaluation"]
    assert ae["adoption_approval_detected"] is False


def test_adoption_does_not_execute():
    data = _run(["--requested-action", "adoption", "--requested-file", "src/example.py",
                 "--adoption-artifact-present", "--human-approved"])
    gate = _gate(data, "adoption_approval_gate")
    assert gate["authorization_granted"] is False
    assert gate["enforcement_performed"] is False
    assert gate["decision"] != "allow"


def test_source_mutation_does_not_mutate():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "src/pcae/core/gate_dry_run.py"])
    gate = _gate(data, "source_mutation_gate")
    assert gate["authorization_granted"] is False
    assert gate["decision"] != "allow"


def test_test_mutation_does_not_mutate():
    data = _run(["--requested-action", "test_mutation",
                 "--requested-file", "tests/test_example.py"])
    gate = _gate(data, "test_mutation_gate")
    assert gate["authorization_granted"] is False
    assert gate["decision"] != "allow"


def test_docs_mutation_does_not_mutate():
    data = _run(["--requested-action", "docs_mutation",
                 "--requested-file", "docs/example.md"])
    for g in data["gates"]:
        assert g["authorization_granted"] is False


def test_real_captured_tasks_blocked():
    data = _run(["--requested-action", "docs_mutation",
                 "--requested-file", "docs/REAL_CAPTURED_TASKS.md"])
    scope = _gate(data, "scope_check_gate")
    assert scope["decision"] != "allow"
    se = scope.get("scope_evaluation", {})
    if se.get("matched_forbidden_files"):
        assert "docs/REAL_CAPTURED_TASKS.md" in se["matched_forbidden_files"]


def test_human_approved_does_not_execute():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "src/pcae/core/gate_dry_run.py",
                 "--human-approved"])
    gate = _gate(data, "source_mutation_gate")
    assert gate["authorization_granted"] is False
    assert gate["enforcement_performed"] is False
    assert gate["decision"] != "allow"


def test_adoption_artifact_does_not_approve():
    data = _run(["--requested-action", "adoption",
                 "--requested-file", "src/example.py",
                 "--adoption-artifact-present"])
    gate = _gate(data, "adoption_approval_gate")
    ae = gate["adoption_evaluation"]
    assert ae["adoption_artifact_present"] is True
    assert ae["adoption_approval_detected"] is False
    assert gate["authorization_granted"] is False


def test_all_gates_authorization_false():
    data = _run(["--requested-action", "adoption",
                 "--requested-file", "src/example.py",
                 "--adoption-artifact-present", "--human-approved"])
    for g in data["gates"]:
        assert g["authorization_granted"] is False
        assert g["enforcement_performed"] is False


def test_envelope_adoption_mutation_safety_notes():
    data = _run()
    n = data["safety_notes"]
    assert n["adoption_gate_dry_run_only"] is True
    assert n["adoption_gate_does_not_review_output"] is True
    assert n["adoption_gate_does_not_approve_output"] is True
    assert n["adoption_gate_does_not_apply_output"] is True
    assert n["adoption_gate_does_not_authorize_adoption"] is True
    assert n["mutation_gate_dry_run_only"] is True
    assert n["mutation_gate_does_not_mutate_source"] is True
    assert n["mutation_gate_does_not_mutate_tests"] is True
    assert n["mutation_gate_does_not_mutate_docs"] is True
    assert n["mutation_gate_does_not_authorize_mutation"] is True
    assert n["scope_match_is_not_mutation_approval"] is True
    assert n["human_approval_flag_is_not_execution"] is True
    assert n["adoption_artifact_presence_is_not_approval"] is True


def test_repo_mutation_performed_false():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "src/example.py", "--human-approved"])
    assert data["safety_notes"]["repo_mutation_performed"] is False


def test_backend_invocation_performed_false():
    data = _run(["--requested-action", "adoption"])
    assert data["safety_notes"]["backend_invocation_performed"] is False


def test_storage_written_false():
    data = _run(["--requested-action", "adoption"])
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


def test_no_cache_files_created():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs = [pcae_dir / "cache", pcae_dir / "gates", pcae_dir / "adoption",
            pcae_dir / "mutation"]
    before = {d: d.exists() for d in dirs}
    _run(["--requested-action", "adoption", "--requested-file", "src/example.py"])
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"


def test_no_repository_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-action", "source_mutation",
          "--requested-file", "src/example.py", "--human-approved"])
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
