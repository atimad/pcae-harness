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


def _scope_gate(data: dict) -> dict:
    for g in data["gates"]:
        if g["gate_id"] == "scope_check_gate":
            return g
    raise AssertionError("scope_check_gate not found")


def test_default_still_works():
    data = _run()
    assert data["gate_count"] == 15
    assert data["dry_run"] is True


def test_scope_check_gate_present():
    data = _run()
    gate = _scope_gate(data)
    assert gate["gate_id"] == "scope_check_gate"


def test_scope_check_gate_has_scope_evaluation():
    data = _run()
    gate = _scope_gate(data)
    assert "scope_evaluation" in gate


def test_scope_evaluation_required_fields():
    data = _run()
    gate = _scope_gate(data)
    se = gate["scope_evaluation"]
    required = [
        "scope_status", "requested_files", "allowed_files", "forbidden_files",
        "matched_allowed_files", "matched_forbidden_files", "unknown_files",
        "task_contract_detected", "task_contract_path", "evidence_sources",
        "scope_notes",
    ]
    for field in required:
        assert field in se, f"Missing scope_evaluation field: {field}"


def test_default_scope_evaluation_valid():
    data = _run()
    se = _scope_gate(data)["scope_evaluation"]
    assert se["scope_status"] in (
        "in_scope", "out_of_scope", "partially_in_scope", "unknown", "requires_human_review",
    )


def test_read_allowed_file():
    data = _run(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    gate = _scope_gate(data)
    se = gate["scope_evaluation"]
    assert "PROJECT_STATUS.md" in se["matched_allowed_files"] or "PROJECT_STATUS.md" in se["unknown_files"]
    assert gate["authorization_granted"] is False


def test_source_mutation_allowed_file():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "src/pcae/core/gate_dry_run.py"])
    gate = _scope_gate(data)
    se = gate["scope_evaluation"]
    assert se["scope_status"] == "in_scope"
    assert gate["decision"] != "allow"
    assert gate["authorization_granted"] is False


def test_source_mutation_forbidden_file():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "README.md"])
    gate = _scope_gate(data)
    se = gate["scope_evaluation"]
    assert se["scope_status"] == "out_of_scope"
    assert "README.md" in se["matched_forbidden_files"]
    assert gate["decision"] in ("blocked_by_scope", "deny")
    assert gate["authorization_granted"] is False


def test_test_mutation_does_not_authorize():
    data = _run(["--requested-action", "test_mutation",
                 "--requested-file", "tests/test_scope_gate.py"])
    gate = _scope_gate(data)
    assert gate["authorization_granted"] is False


def test_docs_mutation_does_not_authorize():
    data = _run(["--requested-action", "docs_mutation",
                 "--requested-file", "docs/PHASE_87_SCOPE_GATE_PROTOTYPE.md"])
    gate = _scope_gate(data)
    assert gate["authorization_granted"] is False


def test_commit_does_not_authorize():
    data = _run(["--requested-action", "commit"])
    gate = _scope_gate(data)
    assert gate["authorization_granted"] is False


def test_push_does_not_authorize():
    data = _run(["--requested-action", "push"])
    gate = _scope_gate(data)
    assert gate["authorization_granted"] is False


def test_backend_invocation_does_not_authorize():
    data = _run(["--requested-action", "backend_invocation"])
    gate = _scope_gate(data)
    assert gate["authorization_granted"] is False


def test_shell_command_does_not_authorize():
    data = _run(["--requested-action", "shell_command"])
    gate = _scope_gate(data)
    assert gate["authorization_granted"] is False


def test_storage_write_does_not_authorize():
    data = _run(["--requested-action", "storage_write"])
    gate = _scope_gate(data)
    assert gate["authorization_granted"] is False


def test_unknown_action_requires_evidence():
    data = _run(["--requested-action", "unknown"])
    gate = _scope_gate(data)
    assert gate["decision"] in ("requires_more_evidence", "requires_human_review", "unknown")
    assert gate["authorization_granted"] is False


def test_out_of_scope_produces_blocked():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "docs/REAL_CAPTURED_TASKS.md"])
    gate = _scope_gate(data)
    se = gate["scope_evaluation"]
    assert se["scope_status"] in ("out_of_scope", "unknown")
    assert gate["decision"] != "allow"


def test_all_gates_authorization_false():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "src/pcae/core/gate_dry_run.py"])
    for g in data["gates"]:
        assert g["authorization_granted"] is False, f"{g['gate_id']} auth should be False"
        assert g["enforcement_performed"] is False, f"{g['gate_id']} enforce should be False"


def test_envelope_safety_flags():
    data = _run()
    n = data["safety_notes"]
    assert n["scope_gate_dry_run_only"] is True
    assert n["scope_gate_does_not_authorize_mutation"] is True
    assert n["scope_gate_does_not_authorize_commit"] is True
    assert n["scope_gate_does_not_authorize_push"] is True
    assert n["scope_gate_does_not_authorize_backend_invocation"] is True
    assert n["scope_gate_does_not_authorize_shell_execution"] is True
    assert n["scope_in_scope_is_not_overall_authorization"] is True


def test_no_cache_files_created():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs = [pcae_dir / "cache", pcae_dir / "gates", pcae_dir / "scope"]
    before = {d: d.exists() for d in dirs}
    _run(["--requested-action", "source_mutation", "--requested-file", "src/example.py"])
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"


def test_no_repository_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-action", "source_mutation", "--requested-file", "src/example.py"])
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
