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


# ===== Docs mutation =====

def test_docs_mutation_in_scope():
    pf = _pf(["--requested-action", "docs_mutation", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"
    assert pf["scope_preflight_decision"] == "allowed"

def test_docs_mutation_forbidden():
    pf = _pf(["--requested-action", "docs_mutation", "--requested-file", "README.md"])
    assert pf["decision"] == "blocked_by_scope"

# ===== Source mutation =====

def test_source_mutation_in_scope():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"

def test_source_mutation_forbidden():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "README.md"])
    assert pf["decision"] == "blocked_by_scope"

# ===== Test mutation =====

def test_test_mutation_in_scope():
    pf = _pf(["--requested-action", "test_mutation", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"

# ===== Generated artifact mutation =====

def test_generated_artifact_in_scope():
    pf = _pf(["--requested-action", "generated_artifact_mutation",
              "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"

# ===== Forbidden file =====

def test_forbidden_file_blocks():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "docs/REAL_CAPTURED_TASKS.md"])
    assert pf["decision"] == "blocked_by_scope"

# ===== Unknown file =====

def test_unknown_file():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "some_unknown_file.py"])
    assert pf["decision"] in ("requires_more_evidence", "requires_human_review")

# ===== Multi-file all allowed =====

def test_multi_file_all_allowed():
    pf = _pf(["--requested-action", "docs_mutation",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "CHANGELOG.md"])
    assert pf["decision"] == "requires_human_review"
    assert pf["scope_preflight_decision"] == "allowed"

# ===== Multi-file mixed forbidden =====

def test_multi_file_forbidden():
    pf = _pf(["--requested-action", "docs_mutation",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "README.md"])
    assert pf["decision"] == "blocked_by_scope"

# ===== Multi-file mixed unknown =====

def test_multi_file_unknown():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "some_totally_unknown.py"])
    assert pf["decision"] in ("requires_more_evidence", "requires_human_review")

# ===== Scope allow does not authorize mutation =====

def test_scope_allow_not_mutation_auth():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"
    assert "scope_allow_not_mutation_authorization" in pf["reason_codes"]
    assert pf["authorization_granted"] is False
    assert pf["mutation_performed"] is False

# ===== Source-backend known =====

def test_source_backend_known():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "PROJECT_STATUS.md", "--source-backend", "claude"])
    assert pf["backend_preflight_required"] is True
    assert pf["backend_preflight_decision"] == "known"
    assert pf["decision"] == "requires_human_review"

# ===== Source-backend unknown =====

def test_source_backend_unknown():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "PROJECT_STATUS.md", "--source-backend", "random_ai"])
    assert pf["decision"] == "requires_more_evidence"
    assert pf["backend_preflight_decision"] == "unknown"

# ===== Backend evidence does not authorize adoption =====

def test_backend_evidence_not_adoption_auth():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "PROJECT_STATUS.md", "--source-backend", "claude"])
    assert pf["authorization_granted"] is False
    assert pf["adoption_approval_granted"] is False

# ===== Captured output missing =====

def test_capture_missing_blocks():
    pf = _pf(["--requested-action", "captured_output_adoption"])
    assert pf["decision"] == "blocked_by_missing_capture"

# ===== Captured output present no hash =====

def test_capture_no_hash():
    pf = _pf(["--requested-action", "captured_output_adoption", "--captured-output-present"])
    assert pf["decision"] == "requires_more_evidence"
    assert pf["captured_output_present"] is True
    assert pf["captured_output_hash_present"] is False

# ===== Captured output present with hash =====

def test_capture_with_hash():
    pf = _pf(["--requested-action", "captured_output_adoption",
              "--captured-output-present", "--captured-output-hash", "abc123"])
    assert pf["decision"] == "requires_human_review"
    assert pf["captured_output_hash_present"] is True

# ===== Captured output does not authorize adoption =====

def test_capture_not_adoption_auth():
    pf = _pf(["--requested-action", "captured_output_adoption",
              "--captured-output-present", "--captured-output-hash", "abc123"])
    assert "captured_output_not_adoption_authorization" in pf["reason_codes"]
    assert pf["adoption_execution_performed"] is False

# ===== Diff present =====

def test_diff_present():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md",
              "--diff-present", "--diff-hash", "d1"])
    assert pf["diff_present"] is True
    assert pf["diff_hash_present"] is True

# ===== Adoption approval without review =====

def test_approval_without_review():
    pf = _pf(["--requested-action", "adoption_approval"])
    assert pf["decision"] == "blocked_by_missing_adoption_review"

# ===== Adoption approval with review =====

def test_approval_with_review_not_granting():
    pf = _pf(["--requested-action", "adoption_approval", "--adoption-review-present"])
    assert pf["decision"] == "requires_human_review"
    assert pf["adoption_approval_granted"] is False
    assert "adoption_review_not_approval" in pf["reason_codes"]

# ===== Adoption execution without approval =====

def test_execution_without_approval():
    pf = _pf(["--requested-action", "adoption_execution", "--adoption-review-present"])
    assert pf["decision"] == "blocked_by_missing_adoption_approval"

# ===== Adoption execution with approval =====

def test_execution_with_approval_not_executing():
    pf = _pf(["--requested-action", "adoption_execution",
              "--adoption-review-present", "--adoption-approval-present"])
    assert pf["decision"] == "requires_human_review"
    assert pf["adoption_execution_performed"] is False
    assert "adoption_approval_not_execution" in pf["reason_codes"]

# ===== Unknown mutation action =====

def test_unknown_mutation_action():
    pf = _pf(["--requested-action", "unknown_mutation_action"])
    assert pf["decision"] == "requires_human_review"
    assert "unknown_action" in pf["reason_codes"]

def test_unknown_action():
    pf = _pf(["--requested-action", "unknown"])
    assert pf["decision"] == "requires_human_review"

# ===== All safety flags false =====

def test_all_flags_false_on_review():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False
    assert pf["mutation_performed"] is False
    assert pf["adoption_review_performed"] is False
    assert pf["adoption_approval_granted"] is False
    assert pf["adoption_execution_performed"] is False
    assert pf["backend_invocation_performed"] is False
    assert pf["prompt_sent"] is False
    assert pf["capture_performed"] is False
    assert pf["commit_performed"] is False
    assert pf["push_performed"] is False
    assert pf["repo_mutation_performed"] is False
    assert pf["storage_written"] is False

def test_all_flags_false_on_block():
    pf = _pf(["--requested-action", "captured_output_adoption"])
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False
    assert pf["mutation_performed"] is False
    assert pf["adoption_execution_performed"] is False
    assert pf["commit_performed"] is False
    assert pf["push_performed"] is False
    assert pf["storage_written"] is False

# ===== No artifacts =====

def test_no_pcae_artifacts():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs = [pcae_dir / "mutation", pcae_dir / "adoption", pcae_dir / "cache",
            pcae_dir / "mutation_preflight"]
    before = {d: d.exists() for d in dirs}
    _run(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    _run(["--requested-action", "captured_output_adoption", "--captured-output-present",
          "--captured-output-hash", "h1"])
    _run(["--requested-action", "adoption_execution", "--adoption-review-present",
          "--adoption-approval-present"])
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"

def test_no_repo_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    _run(["--requested-action", "captured_output_adoption"])
    r2 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == before

# ===== Existing commands =====

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

# ===== Disclaimer =====

def test_disclaimer():
    pf = _pf(["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"])
    assert "mutation_preflight_only_not_execution_authorization" in pf["reason_codes"]

# ===== Determinism =====

def test_deterministic():
    args = ["--requested-action", "source_mutation", "--requested-file", "PROJECT_STATUS.md"]
    pf1 = _pf(args)
    pf2 = _pf(args)
    assert pf1["decision"] == pf2["decision"]
    assert pf1["reason_codes"] == pf2["reason_codes"]
