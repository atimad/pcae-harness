from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(extra_args: list[str] | None = None) -> dict:
    cmd = [sys.executable, "-m", "pcae", "preflight", "scope", "--json"]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


def _pf(extra_args: list[str] | None = None) -> dict:
    return _run(extra_args)["preflight"]


# ===== Allowed file exact match =====


def test_allowed_exact_match_project_status():
    pf = _pf(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "allow_preflight"
    assert "PROJECT_STATUS.md" in pf["matched_allowed_files"]


def test_allowed_exact_match_changelog():
    pf = _pf(["--requested-action", "docs_mutation", "--requested-file", "CHANGELOG.md"])
    assert pf["decision"] == "allow_preflight"
    assert "CHANGELOG.md" in pf["matched_allowed_files"]


def test_allowed_exact_match_task_contract():
    pf = _pf(["--requested-action", "read",
              "--requested-file", "tasks/active/88c-scope-preflight-review.md"])
    assert pf["decision"] == "allow_preflight"


# ===== Allowed file glob match =====


def test_allowed_glob_match_test_file():
    pf = _pf(["--requested-action", "test_mutation",
              "--requested-file", "tests/test_scope_preflight_review.py"])
    assert pf["decision"] == "allow_preflight"
    assert "tests/test_scope_preflight_review.py" in pf["matched_allowed_files"]


def test_allowed_glob_match_docs_review():
    pf = _pf(["--requested-action", "docs_mutation",
              "--requested-file", "docs/PHASE_88_SCOPE_GATE_PREFLIGHT_REVIEW.md"])
    assert pf["decision"] == "allow_preflight"


# ===== Forbidden file exact match =====


def test_forbidden_exact_match_readme():
    pf = _pf(["--requested-action", "docs_mutation", "--requested-file", "README.md"])
    assert pf["decision"] in ("blocked_by_scope", "deny_preflight")
    assert "README.md" in pf["matched_forbidden_files"]


def test_forbidden_exact_match_real_captured_tasks():
    pf = _pf(["--requested-action", "docs_mutation",
              "--requested-file", "docs/REAL_CAPTURED_TASKS.md"])
    assert pf["decision"] in ("blocked_by_scope", "deny_preflight")
    assert "docs/REAL_CAPTURED_TASKS.md" in pf["matched_forbidden_files"]


def test_forbidden_exact_match_linkedin():
    pf = _pf(["--requested-action", "docs_mutation",
              "--requested-file", "docs/LINKEDIN_ARTICLE_DRAFT.md"])
    assert pf["decision"] in ("blocked_by_scope", "deny_preflight")
    assert "docs/LINKEDIN_ARTICLE_DRAFT.md" in pf["matched_forbidden_files"]


# ===== Forbidden file glob match =====


def test_forbidden_glob_match_pcae_dir():
    pf = _pf(["--requested-action", "storage_write",
              "--requested-file", ".pcae/preflight_state.json"])
    assert ".pcae/preflight_state.json" in pf["matched_forbidden_files"] or \
        pf["decision"] == "requires_human_review"


def test_forbidden_glob_match_githooks_dir():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", ".githooks/pre-commit"])
    assert ".githooks/pre-commit" in pf["matched_forbidden_files"] or \
        pf["decision"] in ("blocked_by_scope", "deny_preflight", "requires_more_evidence")


# ===== Allowed and forbidden conflict =====


def test_conflict_forbidden_wins_over_allowed():
    pf = _pf(["--requested-action", "docs_mutation",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "README.md"])
    assert pf["decision"] in ("deny_preflight", "blocked_by_scope")
    assert "README.md" in pf["matched_forbidden_files"]
    assert "PROJECT_STATUS.md" in pf["matched_allowed_files"]


def test_conflict_single_forbidden_blocks_all():
    pf = _pf(["--requested-action", "docs_mutation",
              "--requested-file", "CHANGELOG.md",
              "--requested-file", "docs/REAL_CAPTURED_TASKS.md",
              "--requested-file", "docs/PHASE_88_SCOPE_GATE_PREFLIGHT_REVIEW.md"])
    assert pf["decision"] in ("deny_preflight", "blocked_by_scope")
    assert "docs/REAL_CAPTURED_TASKS.md" in pf["matched_forbidden_files"]


# ===== Multiple files all allowed =====


def test_multi_file_all_allowed():
    pf = _pf(["--requested-action", "read",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "CHANGELOG.md"])
    assert pf["decision"] == "allow_preflight"
    assert len(pf["matched_allowed_files"]) == 2
    assert len(pf["matched_forbidden_files"]) == 0
    assert len(pf["unknown_files"]) == 0


def test_multi_file_three_allowed():
    pf = _pf(["--requested-action", "read",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "CHANGELOG.md",
              "--requested-file", "docs/PHASE_88_SCOPE_GATE_PREFLIGHT_REVIEW.md"])
    assert pf["decision"] == "allow_preflight"
    assert len(pf["matched_allowed_files"]) == 3


# ===== Multiple files mixed allowed and forbidden =====


def test_multi_file_mixed_allowed_forbidden():
    pf = _pf(["--requested-action", "docs_mutation",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "README.md"])
    assert pf["decision"] in ("deny_preflight", "blocked_by_scope")
    assert "forbidden_file_requested" in pf["reason_codes"]


def test_multi_file_two_allowed_one_forbidden():
    pf = _pf(["--requested-action", "docs_mutation",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "CHANGELOG.md",
              "--requested-file", "docs/LINKEDIN_ARTICLE_DRAFT.md"])
    assert pf["decision"] in ("deny_preflight", "blocked_by_scope")


# ===== Multiple files mixed allowed and unknown =====


def test_multi_file_mixed_allowed_unknown():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "src/pcae/core/scope_preflight.py",
              "--requested-file", "src/totally_unknown.py"])
    assert pf["decision"] in ("requires_human_review", "requires_more_evidence")
    assert "src/totally_unknown.py" in pf["unknown_files"]
    assert "src/pcae/core/scope_preflight.py" in pf["matched_allowed_files"]


def test_multi_file_one_allowed_one_unknown_requires_review():
    pf = _pf(["--requested-action", "read",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "some_random_file.txt"])
    assert pf["decision"] in ("requires_human_review", "requires_more_evidence")
    assert "some_random_file.txt" in pf["unknown_files"]


# ===== Unknown file with known action =====


def test_unknown_file_known_action_read():
    pf = _pf(["--requested-action", "read",
              "--requested-file", "nonexistent/path/foo.py"])
    assert pf["decision"] in ("requires_more_evidence", "requires_human_review")
    assert "nonexistent/path/foo.py" in pf["unknown_files"]


def test_unknown_file_known_action_source_mutation():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "src/unknown_module.py"])
    assert pf["decision"] in ("requires_more_evidence", "requires_human_review")
    assert "src/unknown_module.py" in pf["unknown_files"]


# ===== Known file with unknown action =====


def test_known_allowed_file_unknown_action():
    pf = _pf(["--requested-action", "unknown",
              "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"
    assert "unknown_action" in pf["reason_codes"]
    assert pf["human_review_required"] is True


def test_known_forbidden_file_unknown_action():
    pf = _pf(["--requested-action", "unknown",
              "--requested-file", "README.md"])
    assert pf["decision"] == "requires_human_review"
    assert "unknown_action" in pf["reason_codes"]


# ===== Unknown action with unknown file =====


def test_unknown_action_unknown_file():
    pf = _pf(["--requested-action", "destroy_everything",
              "--requested-file", "nonexistent.py"])
    assert pf["decision"] in ("requires_human_review", "unknown")
    assert "unknown_action" in pf["reason_codes"]
    assert pf["human_review_required"] is True


def test_completely_novel_action():
    pf = _pf(["--requested-action", "teleport_files",
              "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] in ("requires_human_review", "unknown")
    assert "unknown_action" in pf["reason_codes"]


# ===== Read action on docs file =====


def test_read_on_docs_file_allowed():
    pf = _pf(["--requested-action", "read",
              "--requested-file", "docs/PHASE_88_SCOPE_GATE_PREFLIGHT_REVIEW.md"])
    assert pf["decision"] == "allow_preflight"


def test_read_on_forbidden_docs_file():
    pf = _pf(["--requested-action", "read",
              "--requested-file", "docs/REAL_CAPTURED_TASKS.md"])
    assert pf["decision"] in ("blocked_by_scope", "deny_preflight")


# ===== docs_mutation on allowed docs file =====


def test_docs_mutation_allowed_docs_file():
    pf = _pf(["--requested-action", "docs_mutation",
              "--requested-file", "docs/PHASE_88_SCOPE_GATE_PREFLIGHT_REVIEW.md"])
    assert pf["decision"] == "allow_preflight"


# ===== docs_mutation on docs/REAL_CAPTURED_TASKS.md =====


def test_docs_mutation_real_captured_tasks_blocked():
    pf = _pf(["--requested-action", "docs_mutation",
              "--requested-file", "docs/REAL_CAPTURED_TASKS.md"])
    assert pf["decision"] in ("blocked_by_scope", "deny_preflight")
    assert "docs/REAL_CAPTURED_TASKS.md" in pf["matched_forbidden_files"]


# ===== source_mutation on src file =====


def test_source_mutation_allowed_src():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "src/pcae/core/scope_preflight.py"])
    assert pf["decision"] == "allow_preflight"


def test_source_mutation_unknown_src():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "src/pcae/core/nonexistent.py"])
    assert pf["decision"] in ("requires_more_evidence", "requires_human_review")
    assert "src/pcae/core/nonexistent.py" in pf["unknown_files"]


# ===== source_mutation on docs file =====


def test_source_mutation_on_docs_file():
    pf = _pf(["--requested-action", "source_mutation",
              "--requested-file", "docs/PHASE_88_SCOPE_GATE_PREFLIGHT_REVIEW.md"])
    assert pf["decision"] == "allow_preflight"


# ===== test_mutation on tests file =====


def test_test_mutation_allowed_test_file():
    pf = _pf(["--requested-action", "test_mutation",
              "--requested-file", "tests/test_scope_preflight_review.py"])
    assert pf["decision"] == "allow_preflight"


# ===== test_mutation on src file =====


def test_test_mutation_on_src_file():
    pf = _pf(["--requested-action", "test_mutation",
              "--requested-file", "src/pcae/core/scope_preflight.py"])
    assert pf["decision"] == "allow_preflight"


# ===== adoption action =====


def test_adoption_action_requires_human_review():
    pf = _pf(["--requested-action", "adoption",
              "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"
    assert pf["human_review_required"] is True
    assert "adoption_not_scope_decidable" in pf["reason_codes"]


# ===== backend_invocation not broadly authorized =====


def test_backend_invocation_not_broadly_authorized():
    pf = _pf(["--requested-action", "backend_invocation",
              "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False
    assert "backend_invocation_not_scope_decidable" in pf["reason_codes"]


# ===== commit not broadly authorized =====


def test_commit_not_broadly_authorized():
    pf = _pf(["--requested-action", "commit",
              "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False
    assert "commit_not_scope_decidable" in pf["reason_codes"]


# ===== push not broadly authorized =====


def test_push_not_broadly_authorized():
    pf = _pf(["--requested-action", "push",
              "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False
    assert "push_not_scope_decidable" in pf["reason_codes"]


# ===== rollback not broadly authorized =====


def test_rollback_not_broadly_authorized():
    pf = _pf(["--requested-action", "rollback",
              "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"
    assert pf["authorization_granted"] is False
    assert "rollback_not_scope_decidable" in pf["reason_codes"]


# ===== storage_write not broadly authorized =====


def test_storage_write_not_broadly_authorized():
    pf = _pf(["--requested-action", "storage_write",
              "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "requires_human_review"
    assert pf["authorization_granted"] is False
    assert "storage_write_not_scope_decidable" in pf["reason_codes"]


# ===== allow_preflight never sets execution_authorized =====


def test_allow_preflight_execution_authorized_false():
    pf = _pf(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "allow_preflight"
    assert pf["execution_authorized"] is False


def test_allow_preflight_authorization_granted_false():
    pf = _pf(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] == "allow_preflight"
    assert pf["authorization_granted"] is False


def test_allow_preflight_multi_file_authorization_false():
    pf = _pf(["--requested-action", "read",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "CHANGELOG.md"])
    assert pf["decision"] == "allow_preflight"
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False


# ===== All negative decisions preserve safety flags =====


def test_deny_preserves_repo_mutation_false():
    pf = _pf(["--requested-action", "docs_mutation", "--requested-file", "README.md"])
    assert pf["decision"] in ("blocked_by_scope", "deny_preflight")
    assert pf["repo_mutation_performed"] is False


def test_deny_preserves_storage_written_false():
    pf = _pf(["--requested-action", "docs_mutation", "--requested-file", "README.md"])
    assert pf["storage_written"] is False


def test_deny_preserves_backend_invocation_false():
    pf = _pf(["--requested-action", "docs_mutation", "--requested-file", "README.md"])
    assert pf["backend_invocation_performed"] is False


def test_review_preserves_repo_mutation_false():
    pf = _pf(["--requested-action", "unknown", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["repo_mutation_performed"] is False


def test_review_preserves_storage_written_false():
    pf = _pf(["--requested-action", "unknown", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["storage_written"] is False


def test_review_preserves_backend_invocation_false():
    pf = _pf(["--requested-action", "unknown", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["backend_invocation_performed"] is False


def test_evidence_preserves_repo_mutation_false():
    pf = _pf(["--requested-action", "read", "--requested-file", "nonexistent.py"])
    assert pf["repo_mutation_performed"] is False


def test_evidence_preserves_storage_written_false():
    pf = _pf(["--requested-action", "read", "--requested-file", "nonexistent.py"])
    assert pf["storage_written"] is False


def test_evidence_preserves_backend_invocation_false():
    pf = _pf(["--requested-action", "read", "--requested-file", "nonexistent.py"])
    assert pf["backend_invocation_performed"] is False


# ===== No state/cache/.pcae files created =====


def test_no_pcae_cache_created():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs = [
        pcae_dir / "cache", pcae_dir / "gates", pcae_dir / "scope",
        pcae_dir / "preflight", pcae_dir / "broker", pcae_dir / "shell_gate",
        pcae_dir / "preflight_state",
    ]
    before = {d: d.exists() for d in dirs}
    _run(["--requested-action", "source_mutation", "--requested-file", "src/example.py"])
    _run(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    _run(["--requested-action", "unknown", "--requested-file", "README.md"])
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"


def test_no_pcae_state_files():
    pcae_dir = REPO_ROOT / ".pcae"
    candidates = [
        pcae_dir / "preflight_state.json",
        pcae_dir / "scope_preflight.json",
        pcae_dir / "gate_state.json",
        pcae_dir / "scope_decisions.json",
        pcae_dir / "preflight_log.json",
    ]
    _run(["--requested-action", "source_mutation", "--requested-file", "src/example.py"])
    for f in candidates:
        assert not f.exists(), f"{f} was created"


# ===== No requested file mutation =====


def test_no_repository_mutation_after_multiple_runs():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-action", "source_mutation", "--requested-file", "src/example.py"])
    _run(["--requested-action", "docs_mutation", "--requested-file", "README.md"])
    _run(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    _run(["--requested-action", "unknown", "--requested-file", "nonexistent.py"])
    r2 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == before


# ===== Existing commands still work =====


def test_gate_dry_run_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "gate-dry-run", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["gate_count"] == 15
    assert data["dry_run"] is True


def test_existing_intelligence_commands_still_work():
    for cmd in ["artifact-index", "memory-snapshot", "governance-timeline",
                "decision-log", "risk-register", "project-state"]:
        result = subprocess.run(
            [sys.executable, "-m", "pcae", cmd, "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"{cmd} failed: {result.stderr}"


# ===== Reason code completeness =====


def test_preflight_disclaimer_always_present_allow():
    pf = _pf(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    assert "preflight_only_not_execution_authorization" in pf["reason_codes"]


def test_preflight_disclaimer_always_present_deny():
    pf = _pf(["--requested-action", "docs_mutation", "--requested-file", "README.md"])
    assert "preflight_only_not_execution_authorization" in pf["reason_codes"]


def test_preflight_disclaimer_always_present_review():
    pf = _pf(["--requested-action", "unknown", "--requested-file", "PROJECT_STATUS.md"])
    assert "preflight_only_not_execution_authorization" in pf["reason_codes"]


def test_preflight_disclaimer_always_present_evidence():
    pf = _pf(["--requested-action", "read", "--requested-file", "nonexistent.py"])
    assert "preflight_only_not_execution_authorization" in pf["reason_codes"]


# ===== Determinism =====


def test_deterministic_output():
    pf1 = _pf(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    pf2 = _pf(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    assert pf1["decision"] == pf2["decision"]
    assert pf1["reason_codes"] == pf2["reason_codes"]
    assert pf1["matched_allowed_files"] == pf2["matched_allowed_files"]
    assert pf1["matched_forbidden_files"] == pf2["matched_forbidden_files"]
    assert pf1["unknown_files"] == pf2["unknown_files"]


def test_deterministic_deny():
    pf1 = _pf(["--requested-action", "docs_mutation", "--requested-file", "README.md"])
    pf2 = _pf(["--requested-action", "docs_mutation", "--requested-file", "README.md"])
    assert pf1["decision"] == pf2["decision"]
    assert pf1["reason_codes"] == pf2["reason_codes"]


# ===== Edge: empty-string action =====


def test_empty_string_action_handled():
    pf = _pf(["--requested-action", "", "--requested-file", "PROJECT_STATUS.md"])
    assert pf["decision"] in ("requires_human_review", "unknown")
    assert "unknown_action" in pf["reason_codes"]
