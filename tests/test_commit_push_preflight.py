from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]
REPO_ROOT = Path(__file__).resolve().parent.parent

def _commit(extra_args=None):
    cmd = [sys.executable, "-m", "pcae", "preflight", "commit", "--json"] + (extra_args or [])
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0, f"Failed: {r.stderr}"
    return json.loads(r.stdout)

def _push(extra_args=None):
    cmd = [sys.executable, "-m", "pcae", "preflight", "push", "--json"] + (extra_args or [])
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0, f"Failed: {r.stderr}"
    return json.loads(r.stdout)

def _cpf(extra_args=None): return _commit(extra_args)["preflight"]
def _ppf(extra_args=None): return _push(extra_args)["preflight"]

# --- Commit command ---
def test_commit_exists():
    r = subprocess.run([sys.executable, "-m", "pcae", "preflight", "commit", "--json"],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0

def test_commit_envelope():
    d = _commit()
    assert d["schema_version"] == "0.1"
    assert d["source_command"] == "pcae preflight commit"
    assert "preflight" in d and "safety_notes" in d

def test_commit_missing_message():
    assert _cpf()["decision"] == "blocked_by_missing_commit_message"

def test_commit_missing_diff():
    assert _cpf(["--commit-message", "test"])["decision"] == "blocked_by_missing_diff"

def test_commit_missing_tests():
    assert _cpf(["--commit-message", "t", "--diff-present"])["decision"] == "blocked_by_missing_tests"

def test_commit_failed_tests():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present"])
    assert pf["decision"] == "blocked_by_failed_tests"

def test_commit_failed_check():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present", "--tests-passed"])
    assert pf["decision"] == "blocked_by_failed_check"

def test_commit_failed_health():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present", "--tests-passed",
               "--pcae-check-passed"])
    assert pf["decision"] == "blocked_by_failed_health"

def test_commit_failed_doctor():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present", "--tests-passed",
               "--pcae-check-passed", "--pcae-health-passed"])
    assert pf["decision"] == "blocked_by_failed_doctor"

def test_commit_all_pass_still_review():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present", "--tests-passed",
               "--pcae-check-passed", "--pcae-health-passed", "--doctor-passed"])
    assert pf["decision"] == "requires_human_review"
    assert pf["authorization_granted"] is False
    assert pf["commit_performed"] is False

# --- Push command ---
def test_push_exists():
    r = subprocess.run([sys.executable, "-m", "pcae", "preflight", "push", "--json"],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0

def test_push_envelope():
    d = _push()
    assert d["schema_version"] == "0.1"
    assert d["source_command"] == "pcae preflight push"

def test_push_missing_check():
    assert _ppf()["decision"] == "blocked_by_push_check"

def test_push_raw_git_push():
    assert _ppf(["--raw-git-push-requested"])["decision"] == "blocked_by_raw_git_push"

def test_push_force_push():
    assert _ppf(["--force-push-requested"])["decision"] == "blocked_by_force_push"

def test_push_missing_tests():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed"])
    assert pf["decision"] == "blocked_by_missing_tests"

def test_push_failed_tests():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed", "--tests-present"])
    assert pf["decision"] == "blocked_by_failed_tests"

def test_push_failed_check():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed",
               "--tests-present", "--tests-passed"])
    assert pf["decision"] == "blocked_by_failed_check"

def test_push_all_pass_still_review():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed",
               "--tests-present", "--tests-passed",
               "--pcae-check-passed", "--pcae-health-passed", "--doctor-passed"])
    assert pf["decision"] == "requires_human_review"
    assert pf["push_performed"] is False
    assert pf["raw_git_push_performed"] is False
    assert pf["force_push_performed"] is False

# --- Safety flags ---
def test_commit_safety_flags():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present", "--tests-passed",
               "--pcae-check-passed", "--pcae-health-passed", "--doctor-passed"])
    for k in ("authorization_granted", "execution_authorized", "commit_performed",
              "push_performed", "raw_git_push_performed", "force_push_performed",
              "repo_mutation_performed", "storage_written"):
        assert pf[k] is False, f"{k} should be False"

def test_push_safety_flags():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed",
               "--tests-present", "--tests-passed",
               "--pcae-check-passed", "--pcae-health-passed", "--doctor-passed"])
    for k in ("authorization_granted", "execution_authorized", "commit_performed",
              "push_performed", "raw_git_push_performed", "force_push_performed",
              "repo_mutation_performed", "storage_written"):
        assert pf[k] is False, f"{k} should be False"

# --- No artifacts ---
def test_no_pcae_artifacts():
    d = REPO_ROOT / ".pcae"
    dirs = [d / "commit_preflight", d / "push_preflight", d / "cache"]
    before = {x: x.exists() for x in dirs}
    _commit(["--commit-message", "t", "--diff-present"])
    _push(["--push-target", "origin/main"])
    for x, existed in before.items():
        if not existed:
            assert not x.exists(), f"{x} was created"

def test_no_repo_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=REPO_ROOT)
    _commit()
    _push()
    r2 = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == r1.stdout

# --- Existing commands ---
def test_scope_works():
    r = subprocess.run([sys.executable, "-m", "pcae", "preflight", "scope", "--json",
                        "--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0

def test_backend_works():
    r = subprocess.run([sys.executable, "-m", "pcae", "preflight", "backend", "--json",
                        "--requested-backend", "claude", "--requested-action", "backend_invocation",
                        "--prompt-present", "--prompt-hash", "h"],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0

def test_mutation_works():
    r = subprocess.run([sys.executable, "-m", "pcae", "preflight", "mutation", "--json",
                        "--requested-action", "source_mutation"],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0

def test_gate_dry_run_works():
    r = subprocess.run([sys.executable, "-m", "pcae", "gate-dry-run", "--json"],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0
    assert json.loads(r.stdout)["gate_count"] == 15

def test_intelligence_commands():
    for cmd in ["artifact-index", "memory-snapshot", "governance-timeline",
                "decision-log", "risk-register", "project-state"]:
        r = subprocess.run([sys.executable, "-m", "pcae", cmd, "--json"],
                           capture_output=True, text=True, cwd=REPO_ROOT)
        assert r.returncode == 0, f"{cmd} failed"

# --- Safety notes ---
def test_safety_notes():
    sn = _commit()["safety_notes"]
    assert sn["commit_push_preflight_only"] is True
    assert sn["commit_preflight_does_not_create_commits"] is True
    assert sn["push_preflight_does_not_push"] is True
    assert sn["raw_git_push_forbidden"] is True
    assert sn["force_push_forbidden"] is True
    assert sn["pcae_push_remains_governed_push_path"] is True

# --- Disclaimer ---
def test_commit_disclaimer():
    pf = _cpf()
    assert "commit_preflight_only_not_execution_authorization" in pf["reason_codes"]

def test_push_disclaimer():
    pf = _ppf()
    assert "push_preflight_only_not_execution_authorization" in pf["reason_codes"]
    assert "pcae_push_required_for_governed_push" in pf["reason_codes"]

# --- Plain text ---
def test_commit_plain_text():
    r = subprocess.run([sys.executable, "-m", "pcae", "preflight", "commit"],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0
    assert "Commit preflight evaluation" in r.stdout

def test_push_plain_text():
    r = subprocess.run([sys.executable, "-m", "pcae", "preflight", "push"],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0
    assert "Push preflight evaluation" in r.stdout
