"""Phase 88M: Preflight Integration Verification.

Verifies the full explicit preflight layer (scope, backend, mutation, commit,
push) as a coherent read-only, non-authorizing governance surface.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core.scope_preflight import build_scope_preflight
from pcae.core.backend_preflight import build_backend_preflight
from pcae.core.mutation_preflight import build_mutation_preflight
from pcae.core.commit_push_preflight import build_commit_preflight, build_push_preflight

pytestmark = [pytest.mark.slow, pytest.mark.integration]

REPO_ROOT = Path(__file__).resolve().parent.parent

_PCAE = [sys.executable, "-m", "pcae"]

# ---------------------------------------------------------------------------
# CLI helper (subprocess — used only for smoke, no-cache, and regression tests)
# ---------------------------------------------------------------------------

def _run(subcmd: list[str]) -> dict:
    cmd = _PCAE + subcmd
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0, f"Command failed ({cmd}): {r.stderr}"
    return json.loads(r.stdout)

# ---------------------------------------------------------------------------
# CLI arg lists (used for smoke + no-cache tests)
# ---------------------------------------------------------------------------

_SCOPE_ALLOW_ARGS = [
    "--requested-action", "source_mutation",
    "--requested-file", "tests/test_preflight_integration_verification.py",
]
_BACKEND_REVIEW_ARGS = [
    "--requested-backend", "claude",
    "--requested-action", "source_mutation",
    "--requested-file", "tests/test_preflight_integration_verification.py",
    "--prompt-present", "--prompt-hash", "abc123",
]
_MUTATION_REVIEW_ARGS = [
    "--requested-action", "source_mutation",
    "--requested-file", "tests/test_preflight_integration_verification.py",
    "--source-backend", "claude",
]
_COMMIT_REVIEW_ARGS = [
    "--commit-message", "integration test",
    "--diff-present", "--tests-present", "--tests-passed",
    "--pcae-check-passed", "--pcae-health-passed", "--doctor-passed",
]
_PUSH_REVIEW_ARGS = [
    "--push-target", "origin/main",
    "--push-check-passed", "--tests-present", "--tests-passed",
    "--pcae-check-passed", "--pcae-health-passed", "--doctor-passed",
]

# ---------------------------------------------------------------------------
# Module-level Python evaluations (no subprocess; shared by all assertion tests)
# ---------------------------------------------------------------------------

_S = build_scope_preflight(
    REPO_ROOT, "source_mutation",
    ["tests/test_preflight_integration_verification.py"],
)["preflight"]

_B = build_backend_preflight(
    REPO_ROOT, "claude", "source_mutation",
    ["tests/test_preflight_integration_verification.py"],
    prompt_present=True, prompt_hash="abc123",
)["preflight"]

_M = build_mutation_preflight(
    REPO_ROOT, "source_mutation",
    ["tests/test_preflight_integration_verification.py"],
    source_backend="claude",
)["preflight"]

_C = build_commit_preflight(
    REPO_ROOT,
    commit_message="integration test",
    diff_present=True, tests_present=True, tests_passed=True,
    pcae_check_passed=True, pcae_health_passed=True, doctor_passed=True,
)["preflight"]

_P = build_push_preflight(
    REPO_ROOT,
    push_target="origin/main",
    push_check_passed=True, tests_present=True, tests_passed=True,
    pcae_check_passed=True, pcae_health_passed=True, doctor_passed=True,
)["preflight"]

_all_pf = pytest.mark.parametrize("pf", [
    pytest.param(_S, id="scope"),
    pytest.param(_B, id="backend"),
    pytest.param(_M, id="mutation"),
    pytest.param(_C, id="commit"),
    pytest.param(_P, id="push"),
])

# ---------------------------------------------------------------------------
# 1. CLI smoke tests — routing + JSON envelope (5 subprocess calls)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cmd,cli_args,source_cmd,pf_type", [
    ("scope", _SCOPE_ALLOW_ARGS, "pcae preflight scope", "scope_gate_preflight"),
    ("backend", _BACKEND_REVIEW_ARGS, "pcae preflight backend", "backend_invocation_preflight"),
    ("mutation", _MUTATION_REVIEW_ARGS, "pcae preflight mutation", "mutation_adoption_preflight"),
    ("commit", _COMMIT_REVIEW_ARGS, "pcae preflight commit", "commit_preflight"),
    ("push", _PUSH_REVIEW_ARGS, "pcae preflight push", "push_preflight"),
])
def test_88m_cli_smoke(cmd, cli_args, source_cmd, pf_type):
    d = _run(["preflight", cmd, "--json"] + list(cli_args))
    assert d.get("schema_version") == "0.1"
    assert "generated_at" in d
    assert d.get("source_command") == source_cmd
    assert "repository_root" in d
    assert d["preflight"]["preflight_type"] == pf_type

# ---------------------------------------------------------------------------
# 2. Notes fields present (Python-level)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pf,notes_key", [
    pytest.param(_S, "scope_notes", id="scope"),
    pytest.param(_B, "backend_notes", id="backend"),
    pytest.param(_M, "mutation_notes", id="mutation"),
    pytest.param(_C, "commit_notes", id="commit"),
    pytest.param(_P, "push_notes", id="push"),
])
def test_88m_has_notes(pf, notes_key):
    assert notes_key in pf
    assert pf[notes_key]

# ---------------------------------------------------------------------------
# 3. Universal non-authorization invariants (Python-level)
# ---------------------------------------------------------------------------

@_all_pf
def test_88m_not_authorizing(pf):
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False


@_all_pf
def test_88m_no_repo_mutation(pf):
    assert pf["repo_mutation_performed"] is False


@_all_pf
def test_88m_no_storage_written(pf):
    assert pf["storage_written"] is False


@_all_pf
def test_88m_detects_lifecycle_state(pf):
    assert pf.get("lifecycle_state") == "active"

# ---------------------------------------------------------------------------
# 4. Command-specific no-write fields (Python-level)
# ---------------------------------------------------------------------------

def test_88m_scope_no_write():
    assert _S["backend_invocation_performed"] is False
    assert _S.get("task_contract_detected") is True


def test_88m_backend_no_write():
    assert _B["backend_invocation_performed"] is False
    assert _B["capture_performed"] is False


def test_88m_mutation_no_write():
    assert _M["mutation_performed"] is False
    assert _M["adoption_execution_performed"] is False
    assert _M["adoption_review_performed"] is False
    assert _M["commit_performed"] is False
    assert _M["push_performed"] is False


def test_88m_commit_no_write():
    assert _C["commit_performed"] is False
    assert _C["push_performed"] is False
    assert _C["force_push_performed"] is False
    assert _C["raw_git_push_performed"] is False


def test_88m_push_no_write():
    assert _P["push_performed"] is False
    assert _P["raw_git_push_performed"] is False
    assert _P["force_push_performed"] is False

# ---------------------------------------------------------------------------
# 5. Review decisions (Python-level)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pf", [
    pytest.param(_B, id="backend"),
    pytest.param(_M, id="mutation"),
    pytest.param(_C, id="commit"),
    pytest.param(_P, id="push"),
])
def test_88m_requires_human_review(pf):
    assert pf["decision"] == "requires_human_review"
    assert pf["human_review_required"] is True

# ---------------------------------------------------------------------------
# 6. Authorization isolation across layers (Python-level)
# ---------------------------------------------------------------------------

def test_88m_authorization_isolation():
    """Each preflight layer has independent authorization; review at one layer does not grant the next."""
    assert _B["authorization_granted"] is False
    assert _B["backend_invocation_performed"] is False
    assert _B.get("backend_allowed_by_policy") is False
    assert _M["authorization_granted"] is False
    assert _M["mutation_performed"] is False
    assert _C["authorization_granted"] is False
    assert _C["commit_performed"] is False
    assert _P["authorization_granted"] is False
    assert _P["push_performed"] is False
    assert _P["raw_git_push_performed"] is False
    assert _P["force_push_performed"] is False

# ---------------------------------------------------------------------------
# 7. Negative scope paths (Python-level)
# ---------------------------------------------------------------------------

def test_88m_scope_blocked_files():
    readme = build_scope_preflight(REPO_ROOT, "source_mutation", ["README.md"])["preflight"]
    assert readme["authorization_granted"] is False
    assert readme["execution_authorized"] is False
    pcae_pf = build_scope_preflight(REPO_ROOT, "source_mutation", [".pcae/policy.toml"])["preflight"]
    assert pcae_pf["authorization_granted"] is False
    pyproject = build_scope_preflight(REPO_ROOT, "source_mutation", ["pyproject.toml"])["preflight"]
    assert pyproject["authorization_granted"] is False
    assert pyproject["execution_authorized"] is False

# ---------------------------------------------------------------------------
# 8. Unknown backend (Python-level)
# ---------------------------------------------------------------------------

def test_88m_unknown_backend_denied():
    pf = build_backend_preflight(
        REPO_ROOT, "unknown_backend", "backend_invocation",
        ["src/example.py"], prompt_present=True, prompt_hash="abc123",
    )["preflight"]
    assert pf["authorization_granted"] is False
    assert pf["decision"] == "deny_preflight"
    assert pf["backend_invocation_performed"] is False
    assert pf["capture_performed"] is False

# ---------------------------------------------------------------------------
# 9. Mutation: missing capture (Python-level)
# ---------------------------------------------------------------------------

def test_88m_mutation_missing_capture():
    pf = build_mutation_preflight(REPO_ROOT, "captured_output_adoption", [])["preflight"]
    assert pf["authorization_granted"] is False
    assert pf["decision"] == "blocked_by_missing_capture"
    assert pf["adoption_execution_performed"] is False
    assert pf["adoption_approval_granted"] is False

# ---------------------------------------------------------------------------
# 10. Commit: missing / incomplete message (Python-level)
# ---------------------------------------------------------------------------

def test_88m_commit_missing_message():
    pf_no_msg = build_commit_preflight(REPO_ROOT)["preflight"]
    assert pf_no_msg["authorization_granted"] is False
    assert pf_no_msg["decision"] == "blocked_by_missing_commit_message"
    assert pf_no_msg["commit_performed"] is False
    pf_msg_only = build_commit_preflight(REPO_ROOT, commit_message="standalone message")["preflight"]
    assert pf_msg_only["authorization_granted"] is False
    assert pf_msg_only["commit_performed"] is False

# ---------------------------------------------------------------------------
# 11. Push: raw git push and force push remain blocked (Python-level)
# ---------------------------------------------------------------------------

def test_88m_push_raw_git_blocked():
    pf = build_push_preflight(REPO_ROOT, push_target="origin/main", raw_git_push_requested=True)["preflight"]
    assert pf["authorization_granted"] is False
    assert pf["decision"] == "blocked_by_raw_git_push"
    assert pf["push_performed"] is False
    assert pf["raw_git_push_performed"] is False
    assert pf["execution_authorized"] is False


def test_88m_push_force_blocked():
    pf = build_push_preflight(REPO_ROOT, push_target="origin/main", force_push_requested=True)["preflight"]
    assert pf["authorization_granted"] is False
    assert pf["decision"] == "blocked_by_force_push"
    assert pf["push_performed"] is False
    assert pf["force_push_performed"] is False
    assert pf["execution_authorized"] is False

# ---------------------------------------------------------------------------
# 12. No .pcae/cache or .pcae/state artifacts after CLI runs (CLI, subprocess)
# ---------------------------------------------------------------------------

def test_88m_no_pcae_cache_after_cli_preflight():
    pcae_cache = REPO_ROOT / ".pcae" / "cache"
    pcae_state = REPO_ROOT / ".pcae" / "state"
    # Positive paths
    _run(["preflight", "scope", "--json"] + _SCOPE_ALLOW_ARGS)
    _run(["preflight", "backend", "--json"] + _BACKEND_REVIEW_ARGS)
    _run(["preflight", "mutation", "--json"] + _MUTATION_REVIEW_ARGS)
    _run(["preflight", "commit", "--json"] + _COMMIT_REVIEW_ARGS)
    _run(["preflight", "push", "--json"] + _PUSH_REVIEW_ARGS)
    # Blocked paths
    _run(["preflight", "scope", "--json", "--requested-action", "source_mutation",
          "--requested-file", "README.md"])
    _run(["preflight", "backend", "--json", "--requested-backend", "unknown_backend",
          "--requested-action", "backend_invocation", "--prompt-present", "--prompt-hash", "h"])
    _run(["preflight", "mutation", "--json", "--requested-action", "captured_output_adoption"])
    _run(["preflight", "commit", "--json"])
    _run(["preflight", "push", "--json", "--push-target", "origin/main", "--raw-git-push-requested"])
    _run(["preflight", "push", "--json", "--push-target", "origin/main", "--force-push-requested"])
    assert not pcae_cache.exists()
    assert not pcae_state.exists()

# ---------------------------------------------------------------------------
# 13. Gate-dry-run regression (CLI)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("args", [
    pytest.param(["gate-dry-run", "--json"], id="default"),
    pytest.param(["gate-dry-run", "--json", "--requested-action", "commit", "--commit-message-present"], id="commit"),
    pytest.param(["gate-dry-run", "--json", "--requested-action", "push", "--push-target", "origin/main"], id="push"),
])
def test_88m_gate_dry_run_still_works(args):
    d = _run(args)
    assert isinstance(d, dict) and len(d) > 0

# ---------------------------------------------------------------------------
# 14. Read-only intelligence commands regression (CLI)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cmd", [
    pytest.param(["artifact-index", "--json"], id="artifact-index"),
    pytest.param(["memory-snapshot", "--json"], id="memory-snapshot"),
    pytest.param(["governance-timeline", "--json"], id="governance-timeline"),
    pytest.param(["decision-log", "--json"], id="decision-log"),
    pytest.param(["risk-register", "--json"], id="risk-register"),
    pytest.param(["project-state", "--json"], id="project-state"),
    pytest.param(["lifecycle", "backend-output-adoption", "summary", "--json"], id="lifecycle-summary"),
])
def test_88m_intelligence_cmd_still_works(cmd):
    d = _run(cmd)
    assert isinstance(d, dict)
