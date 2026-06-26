"""
Shell gate prototype tests (Phase 88P).

All tests are fast (no subprocess) — they call build_shell_gate or _classify_command
directly.  These tests are included in the fast_green tier via conftest.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from pcae.core.shell_gate import (
    SGP_CATEGORIES,
    SGP_DECISIONS,
    _classify_command,
    build_shell_gate,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ────────────────────────────────────────────────────────────────

def _sg(command: str) -> dict[str, Any]:
    """Return shell_gate envelope for a command using the real repo root."""
    return build_shell_gate(REPO_ROOT, command_text=command)["shell_gate"]


def _cat(command: str) -> str:
    return _classify_command(command)["command_category"]


# ── JSON envelope invariants ───────────────────────────────────────────────

class TestEnvelopeInvariants:
    def test_schema_version_present(self):
        data = build_shell_gate(REPO_ROOT, "ls")
        assert data["schema_version"] == "0.1"

    def test_source_command_present(self):
        data = build_shell_gate(REPO_ROOT, "ls")
        assert data["source_command"] == "pcae shell-gate check"

    def test_generated_at_present(self):
        data = build_shell_gate(REPO_ROOT, "ls")
        assert "generated_at" in data and data["generated_at"]

    def test_repository_root_present(self):
        data = build_shell_gate(REPO_ROOT, "ls")
        assert "repository_root" in data

    def test_shell_gate_key_present(self):
        data = build_shell_gate(REPO_ROOT, "ls")
        assert "shell_gate" in data

    def test_warnings_and_errors_present(self):
        data = build_shell_gate(REPO_ROOT, "ls")
        assert "warnings" in data
        assert "errors" in data

    def test_gate_type_is_prototype(self):
        sg = _sg("ls")
        assert sg["gate_type"] == "shell_gate_prototype"

    def test_command_text_preserved(self):
        cmd = "git status --short"
        sg = _sg(cmd)
        assert sg["command_text"] == cmd

    def test_decision_is_known_value(self):
        sg = _sg("ls")
        assert sg["decision"] in SGP_DECISIONS

    def test_command_category_is_known_value(self):
        sg = _sg("ls")
        assert sg["command_category"] in SGP_CATEGORIES


# ── Performed flags always false ───────────────────────────────────────────

class TestPerformedFlagsAlwaysFalse:
    _COMMANDS = [
        "ls",
        "git push --force",
        "git commit -m 'x'",
        "rm -rf /tmp/foo",
        "python -m pytest -n auto",
        "pip install requests",
        "curl https://example.com",
        "unknowncmd --flag",
    ]

    @pytest.mark.parametrize("cmd", _COMMANDS)
    def test_authorization_granted_false(self, cmd):
        assert _sg(cmd)["authorization_granted"] is False

    @pytest.mark.parametrize("cmd", _COMMANDS)
    def test_execution_authorized_false(self, cmd):
        assert _sg(cmd)["execution_authorized"] is False

    @pytest.mark.parametrize("cmd", _COMMANDS)
    def test_command_executed_false(self, cmd):
        assert _sg(cmd)["command_executed"] is False

    @pytest.mark.parametrize("cmd", _COMMANDS)
    def test_repo_mutation_performed_false(self, cmd):
        assert _sg(cmd)["repo_mutation_performed"] is False

    @pytest.mark.parametrize("cmd", _COMMANDS)
    def test_backend_invocation_performed_false(self, cmd):
        assert _sg(cmd)["backend_invocation_performed"] is False

    @pytest.mark.parametrize("cmd", _COMMANDS)
    def test_prompt_sent_false(self, cmd):
        assert _sg(cmd)["prompt_sent"] is False

    @pytest.mark.parametrize("cmd", _COMMANDS)
    def test_capture_performed_false(self, cmd):
        assert _sg(cmd)["capture_performed"] is False

    @pytest.mark.parametrize("cmd", _COMMANDS)
    def test_raw_git_push_performed_false(self, cmd):
        assert _sg(cmd)["raw_git_push_performed"] is False

    @pytest.mark.parametrize("cmd", _COMMANDS)
    def test_force_push_performed_false(self, cmd):
        assert _sg(cmd)["force_push_performed"] is False

    @pytest.mark.parametrize("cmd", _COMMANDS)
    def test_storage_written_false(self, cmd):
        assert _sg(cmd)["storage_written"] is False


# ── Read-only commands ─────────────────────────────────────────────────────

class TestReadOnlyCommands:
    def test_ls_allowed(self):
        sg = _sg("ls -la")
        assert sg["decision"] == "allow_read_only"
        assert sg["command_category"] == "read_only_inspection"

    def test_ls_read_only_detected(self):
        assert _sg("ls")["read_only_detected"] is True

    def test_pwd_allowed(self):
        sg = _sg("pwd")
        assert sg["decision"] == "allow_read_only"

    def test_git_status_allowed(self):
        sg = _sg("git status --short")
        assert sg["decision"] == "allow_read_only"
        assert sg["command_category"] == "read_only_inspection"

    def test_git_log_allowed(self):
        sg = _sg("git log --oneline -10")
        assert sg["decision"] == "allow_read_only"

    def test_git_diff_allowed(self):
        sg = _sg("git diff HEAD")
        assert sg["decision"] == "allow_read_only"

    def test_cat_allowed(self):
        sg = _sg("cat pyproject.toml")
        assert sg["decision"] == "allow_read_only"

    def test_grep_allowed(self):
        sg = _sg("grep -r 'shell_gate' src/")
        assert sg["decision"] == "allow_read_only"

    def test_find_allowed(self):
        sg = _sg("find . -name '*.py'")
        assert sg["decision"] == "allow_read_only"

    def test_sed_n_allowed(self):
        sg = _sg("sed -n '1,10p' CHANGELOG.md")
        assert sg["decision"] == "allow_read_only"

    def test_hard_block_absent_for_read_only(self):
        assert _sg("ls")["hard_block_present"] is False


# ── Raw git commit blocked ─────────────────────────────────────────────────

class TestRawGitCommitBlocked:
    def test_git_commit_blocked(self):
        sg = _sg("git commit -m 'test'")
        assert sg["decision"] == "blocked_by_raw_git_commit"
        assert sg["command_category"] == "raw_git_commit"

    def test_git_commit_raw_detected(self):
        assert _sg("git commit --amend")["raw_git_commit_detected"] is True

    def test_git_commit_hard_block(self):
        assert _sg("git commit -m 'x'")["hard_block_present"] is True

    def test_git_commit_not_executed(self):
        assert _sg("git commit -m 'x'")["command_executed"] is False


# ── Raw git push blocked ───────────────────────────────────────────────────

class TestRawGitPushBlocked:
    def test_git_push_blocked(self):
        sg = _sg("git push")
        assert sg["decision"] == "blocked_by_raw_git_push"
        assert sg["command_category"] == "raw_git_push"

    def test_git_push_origin_blocked(self):
        sg = _sg("git push origin main")
        assert sg["decision"] == "blocked_by_raw_git_push"

    def test_git_push_raw_detected(self):
        assert _sg("git push origin main")["raw_git_push_detected"] is True

    def test_git_push_hard_block(self):
        assert _sg("git push")["hard_block_present"] is True


# ── Force push blocked ─────────────────────────────────────────────────────

class TestForcePushBlocked:
    def test_git_push_force_blocked(self):
        sg = _sg("git push --force")
        assert sg["decision"] == "blocked_by_force_push"
        assert sg["command_category"] == "force_push"

    def test_git_push_f_blocked(self):
        sg = _sg("git push -f")
        assert sg["decision"] == "blocked_by_force_push"

    def test_git_push_force_with_lease_blocked(self):
        sg = _sg("git push --force-with-lease")
        assert sg["decision"] == "blocked_by_force_push"

    def test_force_push_detected_flag(self):
        assert _sg("git push --force")["force_push_detected"] is True

    def test_force_push_hard_block(self):
        assert _sg("git push --force")["hard_block_present"] is True


# ── Git history rewrite blocked ────────────────────────────────────────────

class TestHistoryRewriteBlocked:
    def test_git_reset_hard_blocked(self):
        sg = _sg("git reset --hard HEAD~1")
        assert sg["decision"] == "blocked_by_history_rewrite"

    def test_git_rebase_blocked(self):
        sg = _sg("git rebase main")
        assert sg["decision"] == "blocked_by_history_rewrite"

    def test_git_cherry_pick_blocked(self):
        sg = _sg("git cherry-pick abc123")
        assert sg["decision"] == "blocked_by_history_rewrite"


# ── Destructive filesystem blocked ────────────────────────────────────────

class TestDestructiveFilesystemBlocked:
    def test_rm_rf_blocked(self):
        sg = _sg("rm -rf /tmp/test")
        assert sg["decision"] == "blocked_by_destructive_filesystem"
        assert sg["command_category"] == "destructive_filesystem"

    def test_rm_rf_hard_block(self):
        assert _sg("rm -rf /tmp/test")["hard_block_present"] is True

    def test_destructive_detected_flag(self):
        assert _sg("rm -rf /tmp/test")["destructive_filesystem_detected"] is True

    def test_git_clean_fd_blocked(self):
        sg = _sg("git clean -fd")
        assert sg["decision"] == "blocked_by_destructive_filesystem"


# ── Shell redirection / file write detected ────────────────────────────────

class TestFileWriteRedirectionDetected:
    def test_redirect_to_tmpfile(self):
        sg = _sg("cat foo.txt > /tmp/out.txt")
        assert sg["command_category"] == "filesystem_write"
        assert sg["filesystem_write_detected"] is True

    def test_redirect_append(self):
        sg = _sg("echo hello >> /tmp/log.txt")
        assert sg["filesystem_write_detected"] is True

    def test_redirect_to_source_file(self):
        sg = _sg("echo 'x' > src/pcae/core/new.py")
        assert sg["command_category"] == "source_mutation"
        assert sg["source_mutation_detected"] is True

    def test_redirect_to_test_file(self):
        sg = _sg("echo 'x' > tests/test_new.py")
        assert sg["command_category"] == "test_mutation"
        assert sg["test_mutation_detected"] is True

    def test_redirect_to_docs_file(self):
        sg = _sg("echo 'x' > docs/PHASE_99_FOO.md")
        assert sg["command_category"] == "docs_mutation"
        assert sg["docs_mutation_detected"] is True


# ── Policy-forbidden file blocked ─────────────────────────────────────────

class TestPolicyForbiddenFileBlocked:
    def test_readme_write_blocked(self):
        sg = _sg("echo 'x' > README.md")
        assert sg["decision"] == "blocked_by_policy_forbidden_file"
        assert sg["policy_forbidden_file_detected"] is True

    def test_real_captured_tasks_blocked(self):
        sg = _sg("echo 'x' > docs/REAL_CAPTURED_TASKS.md")
        assert sg["decision"] == "blocked_by_policy_forbidden_file"

    def test_linkedin_article_blocked(self):
        sg = _sg("echo 'x' > docs/LINKEDIN_ARTICLE_DRAFT.md")
        assert sg["decision"] == "blocked_by_policy_forbidden_file"

    def test_policy_forbidden_hard_block(self):
        assert _sg("echo 'x' > README.md")["hard_block_present"] is True

    def test_readme_sed_inplace_blocked(self):
        sg = _sg("sed -i 's/old/new/g' README.md")
        assert sg["decision"] == "blocked_by_policy_forbidden_file"


# ── Test execution classified ─────────────────────────────────────────────

class TestTestExecutionClassified:
    def test_pytest_classified(self):
        sg = _sg("python -m pytest tests/test_shell_gate.py")
        assert sg["command_category"] == "test_execution"
        assert sg["test_execution_detected"] is True

    def test_pytest_n_auto_expensive(self):
        sg = _sg("python -m pytest -n auto")
        assert sg["expensive_test_execution_detected"] is True
        assert sg["test_run_preflight_required"] is True

    def test_pytest_n_4_expensive(self):
        sg = _sg("python -m pytest -n 4 tests/")
        assert sg["expensive_test_execution_detected"] is True

    def test_pytest_no_n_not_expensive(self):
        sg = _sg("python -m pytest tests/test_shell_gate.py -q")
        assert sg["expensive_test_execution_detected"] is False
        assert sg["test_run_preflight_required"] is False

    def test_pcae_commit_classified(self):
        sg = _sg("pcae commit --message 'x'")
        assert sg["command_category"] == "pcae_governed_commit"
        assert sg["decision"] == "allow_governed"

    def test_pcae_push_classified(self):
        sg = _sg("pcae push")
        assert sg["command_category"] == "pcae_governed_push"
        assert sg["decision"] == "allow_governed"


# ── Package install / network review ─────────────────────────────────────

class TestPackageAndNetworkReview:
    def test_pip_install_requires_review(self):
        sg = _sg("pip install requests")
        assert sg["decision"] == "requires_human_review"
        assert sg["command_category"] == "package_install"
        assert sg["package_install_detected"] is True

    def test_brew_install_requires_review(self):
        sg = _sg("brew install ripgrep")
        assert sg["decision"] == "requires_human_review"
        assert sg["command_category"] == "package_install"

    def test_npm_install_requires_review(self):
        sg = _sg("npm install lodash")
        assert sg["decision"] == "requires_human_review"

    def test_curl_requires_review(self):
        sg = _sg("curl https://example.com/script.sh")
        assert sg["decision"] == "requires_human_review"
        assert sg["command_category"] == "network_access"
        assert sg["network_access_detected"] is True

    def test_wget_requires_review(self):
        sg = _sg("wget https://example.com/file.tar.gz")
        assert sg["decision"] == "requires_human_review"


# ── Unknown command blocked ───────────────────────────────────────────────

class TestUnknownCommandBlocked:
    def test_unknown_program_blocked(self):
        sg = _sg("totally_unknown_cmd --flag value")
        assert sg["decision"] == "blocked_by_unknown_command"
        assert sg["command_category"] == "unknown"

    def test_unknown_hard_block(self):
        assert _sg("xyzzy --foo")["hard_block_present"] is True

    def test_empty_command_unknown(self):
        sg = _sg("")
        assert sg["command_category"] == "unknown"

    def test_unknown_not_executed(self):
        assert _sg("xyzzy --foo")["command_executed"] is False


# ── pcae governed commands ────────────────────────────────────────────────

class TestPcaeGoverned:
    def test_pcae_health_governed(self):
        sg = _sg("pcae health")
        assert sg["decision"] == "allow_governed"
        assert sg["command_category"] == "pcae_governed_lifecycle"

    def test_pcae_check_governed(self):
        sg = _sg("pcae check")
        assert sg["decision"] == "allow_governed"

    def test_pcae_task_governed(self):
        sg = _sg("pcae task new 'Test task'")
        assert sg["decision"] == "allow_governed"

    def test_pcae_gate_dry_run_governed(self):
        sg = _sg("pcae gate-dry-run --json")
        assert sg["decision"] == "allow_governed"


# ── Safety notes ──────────────────────────────────────────────────────────

class TestSafetyNotes:
    def test_does_not_execute_commands_note(self):
        sg = _sg("ls")
        assert sg["safety_notes"]["shell_gate_does_not_execute_commands"] is True

    def test_does_not_intercept_shell_note(self):
        sg = _sg("ls")
        assert sg["safety_notes"]["shell_gate_does_not_intercept_shell"] is True

    def test_does_not_invoke_backends_note(self):
        sg = _sg("ls")
        assert sg["safety_notes"]["shell_gate_does_not_invoke_backends"] is True

    def test_permission_broker_not_implemented(self):
        sg = _sg("ls")
        assert sg["safety_notes"]["permission_broker_not_implemented"] is True

    def test_execution_authorization_not_granted(self):
        sg = _sg("ls")
        assert sg["safety_notes"]["execution_authorization_not_granted"] is True
