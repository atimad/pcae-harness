"""
Regression tests for scope file-pattern matching consistency across PCAE preflight callers.

Phase 88O.1 centralised scope matching by having gate_dry_run._evaluate_scope use
_match_file from scope_preflight rather than its own inline logic. These tests verify:

- _match_file semantics (exact, glob, prefix)
- Policy-forbidden files remain blocked across all four callers
- scope_preflight and gate_dry_run classify the same file identically
- No-active-task behaviour remains non-authorising
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from pcae.core.scope_preflight import _match_file, _SPF_POLICY_FORBIDDEN_FILES
from pcae.core.gate_dry_run import _evaluate_scope
from pcae.core.scope_preflight import _evaluate_preflight
from pcae.core.mutation_preflight import _evaluate_scope_for_mutation
from pcae.core.backend_preflight import _evaluate_scope_for_files

REPO_ROOT = Path(__file__).resolve().parent.parent

_MOCK_TC: dict[str, Any] = {
    "path": "tasks/active/mock-task.md",
    "allowed_files": [
        "PROJECT_STATUS.md",
        "CHANGELOG.md",
        "docs/PHASE_88_FOO.md",
        "src/pcae/core/scope_preflight.py",
        "src/pcae/core/gate_dry_run.py",
        "tests/test_scope_matching_consistency.py",
        "tasks/active/**",
    ],
    "forbidden_files": [
        "src/pcae/cli.py",
    ],
}


# ===== _match_file unit tests =====


def test_match_file_exact_path():
    assert _match_file("README.md", ["README.md"])


def test_match_file_prefix_fallback_documented():
    # _match_file includes a startswith fallback for patterns without trailing slash.
    # "README.md" (exact pattern, no *) also matches "README.md.bak" because
    # "README.md.bak".startswith("README.md") is True.
    # This is the documented current behaviour — not changed in 88O.1.
    assert _match_file("README.md.bak", ["README.md"])


def test_match_file_glob_double_star_src():
    assert _match_file("src/pcae/core/scope_preflight.py", ["src/**"])


def test_match_file_glob_double_star_nested():
    assert _match_file("src/pcae/core/deeply/nested/file.py", ["src/**"])


def test_match_file_glob_single_star_docs():
    assert _match_file("docs/PHASE_88_FOO.md", ["docs/*.md"])


def test_match_file_glob_tests_double_star():
    assert _match_file("tests/test_scope_matching_consistency.py", ["tests/**"])


def test_match_file_nonmatching_exact():
    assert not _match_file("pyproject.toml", ["README.md", "CHANGELOG.md"])


def test_match_file_nonmatching_unrelated():
    assert not _match_file("unrelated/deeply/nested.py", ["src/**", "tests/**"])


def test_match_file_prefix_pattern_with_slash():
    # Pattern "tasks/active/" should match "tasks/active/foo.md" (prefix with slash)
    assert _match_file("tasks/active/foo.md", ["tasks/active/"])


def test_match_file_prefix_pattern_glob():
    # Pattern "tasks/active/**" matches via fnmatch
    assert _match_file("tasks/active/foo.md", ["tasks/active/**"])


def test_match_file_empty_patterns_returns_false():
    assert not _match_file("README.md", [])


def test_match_file_star_wildcard_matches_any():
    # "*" in fnmatch matches any string including path separators
    assert _match_file("any/deeply/nested/file.txt", ["*"])


# ===== _SPF_POLICY_FORBIDDEN_FILES tests =====


def test_policy_forbidden_files_tuple_length():
    assert len(_SPF_POLICY_FORBIDDEN_FILES) == 3


def test_policy_forbidden_readme_present():
    assert "README.md" in _SPF_POLICY_FORBIDDEN_FILES


def test_policy_forbidden_real_captured_tasks_present():
    assert "docs/REAL_CAPTURED_TASKS.md" in _SPF_POLICY_FORBIDDEN_FILES


def test_policy_forbidden_linkedin_draft_present():
    assert "docs/LINKEDIN_ARTICLE_DRAFT.md" in _SPF_POLICY_FORBIDDEN_FILES


def test_policy_forbidden_readme_matches():
    assert _match_file("README.md", list(_SPF_POLICY_FORBIDDEN_FILES))


def test_policy_forbidden_real_captured_tasks_matches():
    assert _match_file("docs/REAL_CAPTURED_TASKS.md", list(_SPF_POLICY_FORBIDDEN_FILES))


def test_policy_forbidden_linkedin_matches():
    assert _match_file("docs/LINKEDIN_ARTICLE_DRAFT.md", list(_SPF_POLICY_FORBIDDEN_FILES))


def test_policy_forbidden_non_member_does_not_match():
    assert not _match_file("docs/PHASE_88_FOO.md", list(_SPF_POLICY_FORBIDDEN_FILES))


# ===== Cross-caller consistency: Python-level (fast) =====


def test_scope_preflight_and_gate_dry_run_agree_on_readme_forbidden():
    """Both callers must classify README.md as forbidden when a task contract is active."""
    preflight = _evaluate_preflight("source_mutation", ["README.md"], _MOCK_TC)
    scope = _evaluate_scope(REPO_ROOT, "source_mutation", ["README.md"], _MOCK_TC)
    assert "README.md" in preflight["matched_forbidden_files"]
    assert "README.md" in scope["matched_forbidden_files"]


def test_scope_preflight_and_gate_dry_run_agree_on_real_captured_tasks():
    preflight = _evaluate_preflight("source_mutation", ["docs/REAL_CAPTURED_TASKS.md"], _MOCK_TC)
    scope = _evaluate_scope(REPO_ROOT, "source_mutation", ["docs/REAL_CAPTURED_TASKS.md"], _MOCK_TC)
    assert "docs/REAL_CAPTURED_TASKS.md" in preflight["matched_forbidden_files"]
    assert "docs/REAL_CAPTURED_TASKS.md" in scope["matched_forbidden_files"]


def test_scope_preflight_and_gate_dry_run_agree_on_linkedin_forbidden():
    preflight = _evaluate_preflight("source_mutation", ["docs/LINKEDIN_ARTICLE_DRAFT.md"], _MOCK_TC)
    scope = _evaluate_scope(REPO_ROOT, "source_mutation", ["docs/LINKEDIN_ARTICLE_DRAFT.md"], _MOCK_TC)
    assert "docs/LINKEDIN_ARTICLE_DRAFT.md" in preflight["matched_forbidden_files"]
    assert "docs/LINKEDIN_ARTICLE_DRAFT.md" in scope["matched_forbidden_files"]


def test_scope_preflight_and_gate_dry_run_agree_on_allowed_file():
    """Both must classify an explicitly allowed file as allowed."""
    preflight = _evaluate_preflight("docs_mutation", ["PROJECT_STATUS.md"], _MOCK_TC)
    scope = _evaluate_scope(REPO_ROOT, "docs_mutation", ["PROJECT_STATUS.md"], _MOCK_TC)
    assert "PROJECT_STATUS.md" in preflight["matched_allowed_files"]
    assert "PROJECT_STATUS.md" in scope["matched_allowed_files"]


def test_scope_preflight_and_gate_dry_run_agree_on_task_forbidden_file():
    """Both must classify task-forbidden src/pcae/cli.py as forbidden."""
    preflight = _evaluate_preflight("source_mutation", ["src/pcae/cli.py"], _MOCK_TC)
    scope = _evaluate_scope(REPO_ROOT, "source_mutation", ["src/pcae/cli.py"], _MOCK_TC)
    assert "src/pcae/cli.py" in preflight["matched_forbidden_files"]
    assert "src/pcae/cli.py" in scope["matched_forbidden_files"]


def test_mutation_preflight_agrees_readme_forbidden():
    result = _evaluate_scope_for_mutation(["README.md"], _MOCK_TC)
    assert result == "denied"


def test_backend_preflight_agrees_readme_forbidden():
    result = _evaluate_scope_for_files(["README.md"], _MOCK_TC)
    assert result["scope_decision"] == "denied"
    assert "README.md" in result["matched_forbidden"]


def test_mutation_preflight_agrees_real_captured_tasks_forbidden():
    result = _evaluate_scope_for_mutation(["docs/REAL_CAPTURED_TASKS.md"], _MOCK_TC)
    assert result == "denied"


def test_backend_preflight_agrees_real_captured_tasks_forbidden():
    result = _evaluate_scope_for_files(["docs/REAL_CAPTURED_TASKS.md"], _MOCK_TC)
    assert result["scope_decision"] == "denied"


def test_mutation_preflight_agrees_linkedin_forbidden():
    result = _evaluate_scope_for_mutation(["docs/LINKEDIN_ARTICLE_DRAFT.md"], _MOCK_TC)
    assert result == "denied"


def test_backend_preflight_agrees_linkedin_forbidden():
    result = _evaluate_scope_for_files(["docs/LINKEDIN_ARTICLE_DRAFT.md"], _MOCK_TC)
    assert result["scope_decision"] == "denied"


def test_all_four_callers_agree_on_readme_forbidden():
    """Single test: all four scope evaluation paths classify README.md as forbidden."""
    preflight = _evaluate_preflight("source_mutation", ["README.md"], _MOCK_TC)
    scope = _evaluate_scope(REPO_ROOT, "source_mutation", ["README.md"], _MOCK_TC)
    mutation = _evaluate_scope_for_mutation(["README.md"], _MOCK_TC)
    backend = _evaluate_scope_for_files(["README.md"], _MOCK_TC)

    assert "README.md" in preflight["matched_forbidden_files"]
    assert "README.md" in scope["matched_forbidden_files"]
    assert mutation == "denied"
    assert backend["scope_decision"] == "denied"


def test_all_four_callers_agree_on_allowed_file():
    """All four agree that PROJECT_STATUS.md is in the allowed set."""
    preflight = _evaluate_preflight("docs_mutation", ["PROJECT_STATUS.md"], _MOCK_TC)
    scope = _evaluate_scope(REPO_ROOT, "docs_mutation", ["PROJECT_STATUS.md"], _MOCK_TC)
    mutation = _evaluate_scope_for_mutation(["PROJECT_STATUS.md"], _MOCK_TC)
    backend = _evaluate_scope_for_files(["PROJECT_STATUS.md"], _MOCK_TC)

    assert "PROJECT_STATUS.md" in preflight["matched_allowed_files"]
    assert "PROJECT_STATUS.md" in scope["matched_allowed_files"]
    assert mutation == "allowed"
    assert backend["scope_decision"] == "allowed"


# ===== No-active-task remains non-authorising =====


def test_scope_preflight_no_task_not_authorising():
    result = _evaluate_preflight("source_mutation", ["README.md"], None)
    assert result["decision"] == "blocked_by_missing_task_contract"
    assert result["authorization_granted"] is False
    assert result["execution_authorized"] is False


def test_gate_dry_run_no_task_unknown_scope():
    scope = _evaluate_scope(REPO_ROOT, "source_mutation", ["README.md"], None)
    assert scope["scope_status"] == "unknown"
    assert scope["task_contract_detected"] is False


def test_mutation_preflight_no_task_returns_none():
    result = _evaluate_scope_for_mutation(["README.md"], None)
    assert result is None


def test_backend_preflight_no_task_scope_not_evaluated():
    result = _evaluate_scope_for_files(["README.md"], None)
    assert result["scope_evaluated"] is False


# ===== CLI cross-caller consistency (subprocess) =====


@pytest.mark.slow
@pytest.mark.integration
def test_cli_scope_preflight_blocks_readme():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "scope", "--json",
         "--requested-action", "source_mutation", "--requested-file", "README.md"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    pf = data["preflight"]
    assert "README.md" in pf["matched_forbidden_files"]
    assert pf["decision"] in ("blocked_by_scope", "deny_preflight")


@pytest.mark.slow
@pytest.mark.integration
def test_cli_gate_dry_run_blocks_readme():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "gate-dry-run", "--json",
         "--requested-action", "source_mutation", "--requested-file", "README.md"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    scope_gate = next(g for g in data["gates"] if g["gate_id"] == "scope_check_gate")
    se = scope_gate["scope_evaluation"]
    assert "README.md" in se["matched_forbidden_files"]
    assert se["scope_status"] == "out_of_scope"


@pytest.mark.slow
@pytest.mark.integration
def test_cli_both_agree_readme_is_forbidden():
    """Scope preflight and gate dry-run must classify README.md identically via CLI."""
    spf_result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "scope", "--json",
         "--requested-action", "source_mutation", "--requested-file", "README.md"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    gate_result = subprocess.run(
        [sys.executable, "-m", "pcae", "gate-dry-run", "--json",
         "--requested-action", "source_mutation", "--requested-file", "README.md"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert spf_result.returncode == 0
    assert gate_result.returncode == 0

    spf_pf = json.loads(spf_result.stdout)["preflight"]
    gate_se = next(
        g for g in json.loads(gate_result.stdout)["gates"]
        if g["gate_id"] == "scope_check_gate"
    )["scope_evaluation"]

    assert "README.md" in spf_pf["matched_forbidden_files"]
    assert "README.md" in gate_se["matched_forbidden_files"]


@pytest.mark.slow
@pytest.mark.integration
def test_cli_mutation_preflight_blocks_readme():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "mutation", "--json",
         "--requested-action", "source_mutation", "--requested-file", "README.md"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    pf = data["preflight"]
    assert pf["decision"] == "blocked_by_scope"


@pytest.mark.slow
@pytest.mark.integration
def test_cli_backend_preflight_blocks_readme():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "backend", "--json",
         "--requested-backend", "claude", "--requested-action", "docs_mutation",
         "--requested-file", "README.md", "--prompt-present"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    pf = data["preflight"]
    # Backend preflight decision may be requires_more_evidence (e.g. missing prompt hash)
    # while scope is still denied; check scope outcome directly.
    assert pf["scope_preflight_decision"] == "denied"
    assert not pf["authorization_granted"]
