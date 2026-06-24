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


def _backend_gate(data: dict) -> dict:
    for g in data["gates"]:
        if g["gate_id"] == "backend_invocation_gate":
            return g
    raise AssertionError("backend_invocation_gate not found")


def test_default_still_works():
    data = _run()
    assert data["gate_count"] == 15
    assert data["dry_run"] is True


def test_backend_invocation_gate_present():
    data = _run()
    gate = _backend_gate(data)
    assert gate["gate_id"] == "backend_invocation_gate"


def test_backend_gate_has_backend_evaluation():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "claude"])
    gate = _backend_gate(data)
    assert "backend_evaluation" in gate


def test_backend_evaluation_required_fields():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "claude"])
    be = _backend_gate(data)["backend_evaluation"]
    required = [
        "backend_status", "requested_backend", "requested_action",
        "prompt_present", "backend_allowed_by_scope", "backend_approval_detected",
        "human_approval_detected", "task_contract_detected", "task_contract_path",
        "evidence_sources", "backend_notes",
    ]
    for field in required:
        assert field in be, f"Missing backend_evaluation field: {field}"


def test_default_backend_evaluation():
    data = _run()
    gate = _backend_gate(data)
    assert "backend_evaluation" in gate
    be = gate["backend_evaluation"]
    assert be["backend_status"] in (
        "not_requested", "requested_requires_human_review",
        "requested_requires_more_evidence", "requested_blocked", "requested_unknown",
    )


def test_claude_does_not_invoke():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "claude"])
    gate = _backend_gate(data)
    assert gate["authorization_granted"] is False
    assert gate["enforcement_performed"] is False
    assert gate["decision"] != "allow"


def test_claude_deepseek_does_not_invoke():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "claude-deepseek"])
    gate = _backend_gate(data)
    assert gate["authorization_granted"] is False
    assert gate["decision"] != "allow"


def test_claude_kimi_does_not_invoke():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "claude-kimi"])
    gate = _backend_gate(data)
    assert gate["authorization_granted"] is False
    assert gate["decision"] != "allow"


def test_codex_does_not_invoke():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "codex"])
    gate = _backend_gate(data)
    assert gate["authorization_granted"] is False
    assert gate["decision"] != "allow"


def test_subagent_does_not_invoke():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "subagent"])
    gate = _backend_gate(data)
    assert gate["authorization_granted"] is False
    assert gate["decision"] != "allow"


def test_unknown_backend_requires_evidence():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "unknown"])
    gate = _backend_gate(data)
    assert gate["decision"] in ("requires_more_evidence", "requires_human_review", "deny")
    assert gate["authorization_granted"] is False


def test_prompt_present_does_not_authorize():
    data = _run(["--requested-action", "backend_invocation",
                 "--requested-backend", "claude", "--prompt-present"])
    gate = _backend_gate(data)
    assert gate["authorization_granted"] is False
    assert gate["decision"] != "allow"
    be = gate["backend_evaluation"]
    assert be["prompt_present"] is True
    assert be["backend_approval_detected"] is False


def test_backend_invocation_does_not_send_prompts():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "claude"])
    assert data["safety_notes"]["backend_gate_does_not_send_prompt"] is True


def test_backend_invocation_does_not_capture():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "claude"])
    assert data["safety_notes"]["backend_gate_does_not_capture_output"] is True


def test_backend_invocation_performed_false():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "claude"])
    assert data["safety_notes"]["backend_invocation_performed"] is False


def test_all_gates_authorization_false():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "claude"])
    for g in data["gates"]:
        assert g["authorization_granted"] is False, f"{g['gate_id']} auth should be False"
        assert g["enforcement_performed"] is False, f"{g['gate_id']} enforce should be False"


def test_envelope_backend_safety_notes():
    data = _run()
    n = data["safety_notes"]
    assert n["backend_gate_dry_run_only"] is True
    assert n["backend_gate_does_not_invoke_backend"] is True
    assert n["backend_gate_does_not_send_prompt"] is True
    assert n["backend_gate_does_not_capture_output"] is True
    assert n["backend_gate_does_not_authorize_backend_invocation"] is True
    assert n["backend_gate_requires_human_review_for_invocation"] is True
    assert n["requested_backend_is_not_approval"] is True
    assert n["prompt_presence_is_not_approval"] is True
    assert n["scope_match_is_not_backend_approval"] is True


def test_repo_mutation_performed_false():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "claude"])
    assert data["safety_notes"]["repo_mutation_performed"] is False


def test_storage_written_false():
    data = _run(["--requested-action", "backend_invocation", "--requested-backend", "claude"])
    assert data["safety_notes"]["storage_written"] is False


def test_scope_gate_still_works():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "src/pcae/core/gate_dry_run.py"])
    scope = [g for g in data["gates"] if g["gate_id"] == "scope_check_gate"][0]
    assert "scope_evaluation" in scope
    assert scope["authorization_granted"] is False


def test_no_cache_files_created():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs = [pcae_dir / "cache", pcae_dir / "gates", pcae_dir / "backend"]
    before = {d: d.exists() for d in dirs}
    _run(["--requested-action", "backend_invocation", "--requested-backend", "claude"])
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"


def test_no_repository_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-action", "backend_invocation", "--requested-backend", "claude"])
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
