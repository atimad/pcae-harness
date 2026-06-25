from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(extra_args: list[str] | None = None) -> dict:
    cmd = [sys.executable, "-m", "pcae", "preflight", "mutation", "--json"]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


def _pf(extra_args: list[str] | None = None) -> dict:
    return _run(extra_args)["preflight"]


# --- Command exists ---

def test_command_exists():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "mutation", "--json",
         "--requested-action", "source_mutation"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0

def test_valid_json():
    data = _run(["--requested-action", "source_mutation"])
    assert isinstance(data, dict)

# --- Envelope ---

def test_envelope_fields():
    data = _run(["--requested-action", "source_mutation"])
    assert data["schema_version"] == "0.1"
    assert data["source_command"] == "pcae preflight mutation"
    assert "preflight" in data
    assert "safety_notes" in data

# --- Preflight fields ---

def test_preflight_fields():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    required = [
        "preflight_type", "requested_action", "requested_files", "decision",
        "reason_codes", "task_contract_detected", "scope_preflight_required",
        "scope_preflight_decision", "backend_preflight_required",
        "captured_output_required", "captured_output_present",
        "diff_required", "diff_present", "adoption_review_required",
        "adoption_review_present", "adoption_approval_required",
        "adoption_approval_present", "human_review_required",
        "more_evidence_required", "authorization_granted",
        "execution_authorized", "mutation_performed",
        "adoption_review_performed", "adoption_approval_granted",
        "adoption_execution_performed", "backend_invocation_performed",
        "prompt_sent", "capture_performed", "commit_performed",
        "push_performed", "repo_mutation_performed", "storage_written",
    ]
    for f in required:
        assert f in pf, f"Missing: {f}"

def test_preflight_type():
    pf = _pf(["--requested-action", "source_mutation"])
    assert pf["preflight_type"] == "mutation_adoption_preflight"

# --- Docs mutation in scope ---

def test_docs_mutation_in_scope():
    pf = _pf(["--requested-action", "docs_mutation", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"
    assert pf["scope_preflight_decision"] == "allowed"

# --- Source mutation in scope ---

def test_source_mutation_in_scope():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"

# --- Forbidden file ---

def test_forbidden_file_blocked():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "README.md"])
    assert pf["decision"] == "blocked_by_scope"
    assert "scope_preflight_denied" in pf["reason_codes"]

# --- Unknown file ---

def test_unknown_file():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "some_unknown.py"])
    assert pf["decision"] in ("requires_more_evidence", "requires_human_review")

# --- Missing capture ---

def test_adoption_missing_capture():
    pf = _pf(["--requested-action", "captured_output_adoption"])
    assert pf["decision"] == "blocked_by_missing_capture"

# --- Capture present no hash ---

def test_adoption_capture_no_hash():
    pf = _pf(["--requested-action", "captured_output_adoption", "--captured-output-present"])
    assert pf["decision"] == "requires_more_evidence"
    assert pf["captured_output_present"] is True
    assert pf["captured_output_hash_present"] is False

# --- Capture with hash ---

def test_adoption_capture_with_hash():
    pf = _pf(["--requested-action", "captured_output_adoption",
              "--captured-output-present", "--captured-output-hash", "abc123"])
    assert pf["decision"] == "requires_human_review"
    assert pf["captured_output_hash_present"] is True

# --- Adoption approval without review ---

def test_approval_without_review():
    pf = _pf(["--requested-action", "adoption_approval"])
    assert pf["decision"] == "blocked_by_missing_adoption_review"

# --- Adoption approval with review ---

def test_approval_with_review():
    pf = _pf(["--requested-action", "adoption_approval", "--adoption-review-present"])
    assert pf["decision"] == "requires_human_review"

# --- Adoption execution without approval ---

def test_execution_without_approval():
    pf = _pf(["--requested-action", "adoption_execution", "--adoption-review-present"])
    assert pf["decision"] == "blocked_by_missing_adoption_approval"

# --- Adoption execution with review and approval ---

def test_execution_with_review_and_approval():
    pf = _pf(["--requested-action", "adoption_execution",
              "--adoption-review-present", "--adoption-approval-present"])
    assert pf["decision"] == "requires_human_review"

# --- Source backend ---

def test_source_backend_known():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "PROJECT_STATUS.md", "--source-backend", "claude"])
    assert pf["backend_preflight_required"] is True
    assert pf["backend_preflight_decision"] == "known"

def test_source_backend_unknown():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "PROJECT_STATUS.md", "--source-backend", "random_ai"])
    assert pf["decision"] == "requires_more_evidence"
    assert pf["backend_preflight_decision"] == "unknown"

# --- Unknown action ---

def test_unknown_action():
    pf = _pf(["--requested-action", "unknown_mutation_action"])
    assert pf["decision"] == "requires_human_review"
    assert "unknown_action" in pf["reason_codes"]

def test_unknown():
    pf = _pf(["--requested-action", "unknown"])
    assert pf["decision"] == "requires_human_review"

# --- Diff flags ---

def test_diff_present_reflected():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md",
              "--diff-present", "--diff-hash", "d1"])
    assert pf["diff_present"] is True
    assert pf["diff_hash_present"] is True

# --- Safety flags always false ---

def test_authorization_false():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False

def test_mutation_not_performed():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["mutation_performed"] is False
    assert pf["adoption_review_performed"] is False
    assert pf["adoption_approval_granted"] is False
    assert pf["adoption_execution_performed"] is False

def test_no_backend_prompt_capture():
    pf = _pf(["--requested-action", "source_mutation"])
    assert pf["backend_invocation_performed"] is False
    assert pf["prompt_sent"] is False
    assert pf["capture_performed"] is False

def test_no_commit_push_storage():
    pf = _pf(["--requested-action", "source_mutation"])
    assert pf["commit_performed"] is False
    assert pf["push_performed"] is False
    assert pf["repo_mutation_performed"] is False
    assert pf["storage_written"] is False

# --- No artifacts ---

def test_no_pcae_artifacts():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs = [pcae_dir / "mutation", pcae_dir / "adoption", pcae_dir / "cache",
            pcae_dir / "preflight", pcae_dir / "mutation_preflight"]
    before = {d: d.exists() for d in dirs}
    _run(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    _run(["--requested-action", "captured_output_adoption", "--captured-output-present"])
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"

def test_no_repo_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    r2 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == before

# --- Existing commands ---

def test_scope_preflight_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "scope", "--json",
         "--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0

def test_backend_preflight_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "backend", "--json",
         "--requested-backend", "claude", "--requested-action", "backend_invocation",
         "--prompt-present", "--prompt-hash", "h1"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0

def test_gate_dry_run_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "gate-dry-run", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["gate_count"] == 15

def test_intelligence_commands_work():
    for cmd in ["artifact-index", "memory-snapshot", "governance-timeline",
                "decision-log", "risk-register", "project-state"]:
        result = subprocess.run(
            [sys.executable, "-m", "pcae", cmd, "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"{cmd} failed"

# --- Safety notes ---

def test_safety_notes():
    data = _run(["--requested-action", "source_mutation"])
    sn = data["safety_notes"]
    assert sn["mutation_preflight_only"] is True
    assert sn["mutation_preflight_does_not_mutate_files"] is True
    assert sn["mutation_preflight_does_not_apply_output"] is True
    assert sn["mutation_preflight_does_not_invoke_backends"] is True
    assert sn["mutation_preflight_does_not_commit"] is True
    assert sn["mutation_preflight_does_not_push"] is True
    assert sn["scope_preflight_is_separate"] is True
    assert sn["backend_preflight_is_separate"] is True
    assert sn["permission_broker_not_implemented"] is True

# --- Disclaimer ---

def test_disclaimer():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    assert "mutation_preflight_only_not_execution_authorization" in pf["reason_codes"]
    assert "scope_allow_not_mutation_authorization" in pf["reason_codes"]

# --- Plain text ---

def test_plain_text():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "mutation",
         "--requested-action", "source_mutation"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "Mutation/adoption preflight evaluation" in result.stdout
