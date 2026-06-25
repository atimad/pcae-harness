from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]
REPO_ROOT = Path(__file__).resolve().parent.parent

def _commit(extra=None):
    cmd = [sys.executable, "-m", "pcae", "preflight", "commit", "--json"] + (extra or [])
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0, f"Failed: {r.stderr}"
    return json.loads(r.stdout)

def _push(extra=None):
    cmd = [sys.executable, "-m", "pcae", "preflight", "push", "--json"] + (extra or [])
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0, f"Failed: {r.stderr}"
    return json.loads(r.stdout)

def _cpf(extra=None): return _commit(extra)["preflight"]
def _ppf(extra=None): return _push(extra)["preflight"]

# ===== Commit: missing message =====
def test_commit_missing_message():
    assert _cpf()["decision"] == "blocked_by_missing_commit_message"

# ===== Commit: message alone =====
def test_commit_message_alone_non_auth():
    pf = _cpf(["--commit-message", "test"])
    assert pf["decision"] != "allow_preflight"
    assert pf["authorization_granted"] is False
    assert pf["commit_performed"] is False

# ===== Commit: message + diff =====
def test_commit_message_diff_non_auth():
    pf = _cpf(["--commit-message", "t", "--diff-present"])
    assert pf["decision"] != "allow_preflight"
    assert pf["authorization_granted"] is False

# ===== Commit: message + diff + tests =====
def test_commit_message_diff_tests_non_auth():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present", "--tests-passed"])
    assert pf["decision"] != "allow_preflight"
    assert pf["authorization_granted"] is False

# ===== Commit: all pass still review =====
def test_commit_all_pass_review():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present", "--tests-passed",
               "--pcae-check-passed", "--pcae-health-passed", "--doctor-passed"])
    assert pf["decision"] == "requires_human_review"
    assert pf["human_review_required"] is True
    assert pf["authorization_granted"] is False
    assert pf["commit_performed"] is False

# ===== Commit: tests missing =====
def test_commit_tests_missing():
    pf = _cpf(["--commit-message", "t", "--diff-present"])
    assert pf["decision"] == "blocked_by_missing_tests"

# ===== Commit: tests failed =====
def test_commit_tests_failed():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present"])
    assert pf["decision"] == "blocked_by_failed_tests"

# ===== Commit: check failed =====
def test_commit_check_failed():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present", "--tests-passed"])
    assert pf["decision"] == "blocked_by_failed_check"

# ===== Commit: health failed =====
def test_commit_health_failed():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present", "--tests-passed",
               "--pcae-check-passed"])
    assert pf["decision"] == "blocked_by_failed_health"

# ===== Commit: doctor failed =====
def test_commit_doctor_failed():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present", "--tests-passed",
               "--pcae-check-passed", "--pcae-health-passed"])
    assert pf["decision"] == "blocked_by_failed_doctor"

# ===== Push: missing target =====
def test_push_missing_target():
    pf = _ppf(["--push-check-passed", "--tests-present", "--tests-passed",
               "--pcae-check-passed", "--pcae-health-passed", "--doctor-passed"])
    assert pf["decision"] == "blocked_by_branch_state"

# ===== Push: target alone =====
def test_push_target_alone_non_auth():
    pf = _ppf(["--push-target", "origin/main"])
    assert pf["decision"] != "allow_preflight"
    assert pf["authorization_granted"] is False

# ===== Push: push-check missing =====
def test_push_check_missing():
    pf = _ppf(["--push-target", "origin/main"])
    assert pf["decision"] == "blocked_by_push_check"

# ===== Push: push-check passed alone =====
def test_push_check_passed_alone():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed"])
    assert pf["decision"] != "allow_preflight"
    assert pf["authorization_granted"] is False

# ===== Push: all pass still review =====
def test_push_all_pass_review():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed",
               "--tests-present", "--tests-passed",
               "--pcae-check-passed", "--pcae-health-passed", "--doctor-passed"])
    assert pf["decision"] == "requires_human_review"
    assert pf["human_review_required"] is True
    assert pf["push_performed"] is False

# ===== Push: tests missing =====
def test_push_tests_missing():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed"])
    assert pf["decision"] == "blocked_by_missing_tests"

# ===== Push: tests failed =====
def test_push_tests_failed():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed", "--tests-present"])
    assert pf["decision"] == "blocked_by_failed_tests"

# ===== Push: check failed =====
def test_push_check_failed():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed",
               "--tests-present", "--tests-passed"])
    assert pf["decision"] == "blocked_by_failed_check"

# ===== Push: health failed =====
def test_push_health_failed():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed",
               "--tests-present", "--tests-passed", "--pcae-check-passed"])
    assert pf["decision"] == "blocked_by_failed_health"

# ===== Push: doctor failed =====
def test_push_doctor_failed():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed",
               "--tests-present", "--tests-passed", "--pcae-check-passed",
               "--pcae-health-passed"])
    assert pf["decision"] == "blocked_by_failed_doctor"

# ===== Raw git push blocked =====
def test_raw_git_push_blocked():
    pf = _ppf(["--push-target", "origin/main", "--raw-git-push-requested"])
    assert pf["decision"] == "blocked_by_raw_git_push"
    assert "raw_git_push_blocked" in pf["reason_codes"]
    assert pf["raw_git_push_performed"] is False

# ===== Force push blocked =====
def test_force_push_blocked():
    pf = _ppf(["--push-target", "origin/main", "--force-push-requested"])
    assert pf["decision"] == "blocked_by_force_push"
    assert "force_push_blocked" in pf["reason_codes"]
    assert pf["force_push_performed"] is False

# ===== Raw + force flags non-executing =====
def test_raw_force_non_executing():
    pf = _ppf(["--push-target", "origin/main", "--raw-git-push-requested",
               "--force-push-requested"])
    assert pf["raw_git_push_performed"] is False
    assert pf["force_push_performed"] is False
    assert pf["push_performed"] is False

# ===== pcae push preservation =====
def test_pcae_push_preservation():
    sn = _push()["safety_notes"]
    assert sn["pcae_push_remains_governed_push_path"] is True
    assert sn["raw_git_push_forbidden"] is True
    assert sn["force_push_forbidden"] is True

# ===== Branch/head fields =====
def test_commit_branch_head():
    pf = _cpf(["--commit-message", "t", "--diff-present"])
    assert pf["branch_name"] is not None
    assert pf["head_commit"] is not None

def test_push_branch_head():
    pf = _ppf(["--push-target", "origin/main"])
    assert pf["branch_name"] is not None
    assert pf["head_commit"] is not None

# ===== Ahead/behind =====
def test_push_ahead_behind():
    pf = _ppf(["--push-target", "origin/main"])
    assert "ahead_count" in pf
    assert "behind_count" in pf

# ===== All safety flags false =====
def test_commit_all_flags_false():
    pf = _cpf(["--commit-message", "t", "--diff-present", "--tests-present", "--tests-passed",
               "--pcae-check-passed", "--pcae-health-passed", "--doctor-passed"])
    for k in ("authorization_granted", "execution_authorized", "commit_performed",
              "push_performed", "raw_git_push_performed", "force_push_performed",
              "repo_mutation_performed", "storage_written"):
        assert pf[k] is False, f"{k}"

def test_push_all_flags_false():
    pf = _ppf(["--push-target", "origin/main", "--push-check-passed",
               "--tests-present", "--tests-passed",
               "--pcae-check-passed", "--pcae-health-passed", "--doctor-passed"])
    for k in ("authorization_granted", "execution_authorized", "commit_performed",
              "push_performed", "raw_git_push_performed", "force_push_performed",
              "repo_mutation_performed", "storage_written"):
        assert pf[k] is False, f"{k}"

def test_blocked_flags_false():
    pf = _ppf(["--raw-git-push-requested"])
    for k in ("authorization_granted", "execution_authorized", "push_performed",
              "raw_git_push_performed", "force_push_performed", "storage_written"):
        assert pf[k] is False, f"{k}"

# ===== No artifacts =====
def test_no_pcae_artifacts():
    d = REPO_ROOT / ".pcae"
    dirs = [d / "commit_preflight", d / "push_preflight", d / "cache"]
    before = {x: x.exists() for x in dirs}
    _commit(["--commit-message", "t", "--diff-present"])
    _push(["--push-target", "origin/main", "--push-check-passed"])
    _push(["--raw-git-push-requested"])
    _push(["--force-push-requested"])
    for x, existed in before.items():
        if not existed:
            assert not x.exists(), f"{x} was created"

def test_no_repo_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=REPO_ROOT)
    _commit()
    _push()
    _push(["--raw-git-push-requested"])
    r2 = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == r1.stdout

# ===== Existing commands =====
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

# ===== Disclaimers =====
def test_commit_disclaimer():
    pf = _cpf()
    assert "commit_preflight_only_not_execution_authorization" in pf["reason_codes"]

def test_push_disclaimer():
    pf = _ppf()
    assert "push_preflight_only_not_execution_authorization" in pf["reason_codes"]
    assert "pcae_push_required_for_governed_push" in pf["reason_codes"]

# ===== Determinism =====
def test_deterministic_commit():
    a = _cpf(["--commit-message", "t", "--diff-present"])
    b = _cpf(["--commit-message", "t", "--diff-present"])
    assert a["decision"] == b["decision"]
    assert a["reason_codes"] == b["reason_codes"]

def test_deterministic_push():
    a = _ppf(["--push-target", "origin/main"])
    b = _ppf(["--push-target", "origin/main"])
    assert a["decision"] == b["decision"]
    assert a["reason_codes"] == b["reason_codes"]
