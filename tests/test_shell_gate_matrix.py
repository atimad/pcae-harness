"""
Shell gate test matrix (Phase 88Q).

Systematic coverage of all 23 command categories, idle-vs-active behavior,
compound command parsing, pipe/tee write detection, redirection chains,
backend/secret/environment detection, and policy-forbidden file handling.

All tests are fast (no subprocess) — they call _classify_command directly or
build_shell_gate with the real repo root.  Included in the fast_green tier
via conftest.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from pcae.core.shell_gate import (
    SGP_CATEGORIES,
    _classify_command,
    _classify_single,
    _find_tee_write_target,
    _is_secret_file_access,
    _most_restrictive_classification,
    _split_on_operators,
    build_shell_gate,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Helpers ────────────────────────────────────────────────────────────────


def _sg(command: str) -> dict[str, Any]:
    """Return shell_gate envelope using the real repo root."""
    return build_shell_gate(REPO_ROOT, command_text=command)["shell_gate"]


def _cat(command: str) -> str:
    return _classify_command(command)["command_category"]


def _dec(command: str) -> str:
    return _sg(command)["decision"]


def _cat_idle(command: str) -> str:
    """Classify without any active task contract."""
    with patch("pcae.core.shell_gate._detect_task_contract", return_value=None):
        return build_shell_gate(REPO_ROOT, command_text=command)["shell_gate"]["decision"]


def _cat_active(command: str) -> str:
    """Classify with a mock active task contract."""
    fake_contract = {"path": "tasks/active/fake-task.md", "id": "fake-task"}
    with patch("pcae.core.shell_gate._detect_task_contract", return_value=fake_contract):
        with patch("pcae.core.shell_gate._call_doctor_test_run", return_value=True):
            return build_shell_gate(REPO_ROOT, command_text=command)["shell_gate"]["decision"]


# ── 1. Category constants coverage ────────────────────────────────────────


class TestCategoryConstants:
    def test_all_23_categories_defined(self):
        assert len(SGP_CATEGORIES) == 24  # 23 named + "unknown"

    def test_unknown_in_categories(self):
        assert "unknown" in SGP_CATEGORIES

    def test_backend_invocation_in_categories(self):
        assert "backend_invocation" in SGP_CATEGORIES

    def test_secret_access_in_categories(self):
        assert "secret_access" in SGP_CATEGORIES

    def test_environment_mutation_in_categories(self):
        assert "environment_mutation" in SGP_CATEGORIES


# ── 2. Category matrix: read_only_inspection ──────────────────────────────


class TestReadOnlyInspection:
    @pytest.mark.parametrize("cmd", [
        "pwd",
        "ls",
        "ls -la",
        "ls -lah /tmp",
        "cat PROJECT_STATUS.md",
        "head -20 PROJECT_STATUS.md",
        "tail -10 CHANGELOG.md",
        "wc -l src/pcae/core/shell_gate.py",
        "diff file1 file2",
        "date",
        "whoami",
        "hostname",
        "id",
        "uname -a",
    ])
    def test_read_only_commands(self, cmd):
        assert _cat(cmd) == "read_only_inspection"

    @pytest.mark.parametrize("cmd", [
        "git status",
        "git log --oneline -5",
        "git log --oneline -20",
        "git diff",
        "git show HEAD",
        "git branch",
        "git remote -v",
        "git rev-parse HEAD",
        "git describe --tags",
        "git ls-files",
    ])
    def test_git_read_only_commands(self, cmd):
        assert _cat(cmd) == "read_only_inspection"

    @pytest.mark.parametrize("cmd", [
        "grep -R 'Phase 88' docs",
        "grep -n 'def test' tests/test_shell_gate.py",
        "find docs -maxdepth 1 -type f",
        "find . -name '*.py' -maxdepth 3",
        "rg 'shell_gate' src",
    ])
    def test_grep_find_read_only(self, cmd):
        assert _cat(cmd) == "read_only_inspection"

    @pytest.mark.parametrize("cmd", [
        "sed -n '1,20p' PROJECT_STATUS.md",
        "sed -n '/Phase/p' CHANGELOG.md",
        "awk '{print $1}' file.txt",
        "awk 'NR<10' PROJECT_STATUS.md",
    ])
    def test_sed_awk_read_only(self, cmd):
        assert _cat(cmd) == "read_only_inspection"

    def test_read_only_decision_is_allow(self):
        assert _dec("ls") == "allow_read_only"

    def test_git_status_decision_is_allow(self):
        assert _dec("git status") == "allow_read_only"


# ── 3. Category matrix: test_execution ────────────────────────────────────


class TestTestExecution:
    @pytest.mark.parametrize("cmd", [
        "python -m pytest tests/test_shell_gate.py -q",
        "python -m pytest tests/test_shell_gate.py",
        "python -m pytest -m 'fast_green'",
        "python -m pytest",
        "pytest tests/",
    ])
    def test_non_expensive_pytest(self, cmd):
        assert _cat(cmd) == "test_execution"

    @pytest.mark.parametrize("cmd", [
        "python -m pytest -n auto",
        "python -m pytest -n auto -ra --durations=50",
        "python -m pytest -m fast_green -n auto",
        "python -m pytest -n 4",
        "python -m pytest -n 8 -m 'not slow'",
    ])
    def test_expensive_pytest(self, cmd):
        result = _classify_command(cmd)
        assert result["command_category"] == "test_execution"
        assert result["detected_flags"]["expensive_test_execution_detected"] is True

    def test_pytest_no_task_idle_decision(self):
        assert _cat_idle("python -m pytest tests/test_shell_gate.py -q") == "requires_active_task"

    def test_pytest_with_task_decision(self):
        assert _cat_active("python -m pytest tests/test_shell_gate.py -q") == "allow_test_execution"

    def test_expensive_pytest_with_task_decision(self):
        assert _cat_active("python -m pytest -n auto") == "allow_test_execution"


# ── 4. Category matrix: pcae governed ─────────────────────────────────────


class TestPcaeGoverned:
    @pytest.mark.parametrize("cmd", [
        "pcae health",
        "pcae check",
        "pcae doctor task-memory",
        "pcae doctor test-run --json",
        "pcae task list",
        "pcae session bootstrap --compact --profile implementation",
        "pcae shell-gate check --command 'ls'",
    ])
    def test_pcae_lifecycle_governed(self, cmd):
        assert _cat(cmd) == "pcae_governed_lifecycle"

    @pytest.mark.parametrize("cmd", [
        "pcae commit implementation --path src/example.py --message 'x'",
    ])
    def test_pcae_commit_governed(self, cmd):
        assert _cat(cmd) == "pcae_governed_commit"

    def test_pcae_task_finish_lifecycle(self):
        # pcae task finish is governed lifecycle (subcommand is 'task', not 'commit')
        assert _cat("pcae task finish --commit 'x'") == "pcae_governed_lifecycle"

    @pytest.mark.parametrize("cmd", [
        "pcae push",
        "pcae push check",
    ])
    def test_pcae_push_governed(self, cmd):
        assert _cat(cmd) == "pcae_governed_push"

    def test_pcae_governed_decision_is_allow(self):
        assert _dec("pcae health") == "allow_governed"

    def test_pcae_commit_decision_is_allow(self):
        assert _dec("pcae commit implementation --path src/x.py --message 'x'") == "allow_governed"

    def test_pcae_push_decision_is_allow(self):
        assert _dec("pcae push") == "allow_governed"

    # pcae lifecycle subcommands that map to specific categories
    def test_pcae_output_capture_governed(self):
        assert _cat("pcae output capture") == "pcae_governed_lifecycle"

    def test_pcae_intake_review_governed(self):
        assert _cat("pcae intake review") == "pcae_governed_lifecycle"

    def test_pcae_adoption_approve_governed(self):
        assert _cat("pcae adoption approve") == "pcae_governed_lifecycle"


# ── 5. Category matrix: raw git ───────────────────────────────────────────


class TestRawGit:
    @pytest.mark.parametrize("cmd", [
        "git commit -m 'x'",
        "git commit --amend",
        "git commit -am 'x'",
    ])
    def test_raw_git_commit_blocked(self, cmd):
        assert _cat(cmd) == "raw_git_commit"
        assert _dec(cmd) == "blocked_by_raw_git_commit"

    @pytest.mark.parametrize("cmd", [
        "git push",
        "git push origin main",
        "git push origin HEAD",
    ])
    def test_raw_git_push_blocked(self, cmd):
        assert _cat(cmd) == "raw_git_push"
        assert _dec(cmd) == "blocked_by_raw_git_push"

    @pytest.mark.parametrize("cmd", [
        "git push --force",
        "git push -f",
        "git push --force-with-lease",
        "git push --force-if-includes",
        "git push origin main --force",
    ])
    def test_force_push_blocked(self, cmd):
        assert _cat(cmd) == "force_push"
        assert _dec(cmd) == "blocked_by_force_push"

    @pytest.mark.parametrize("cmd", [
        "git reset --hard HEAD",
        "git reset --hard HEAD~1",
        "git reset --mixed HEAD",
        "git rebase main",
        "git rebase -i HEAD~3",
        "git cherry-pick abc123",
    ])
    def test_git_history_rewrite_blocked(self, cmd):
        assert _cat(cmd) in ("git_history_rewrite",)
        assert _dec(cmd) == "blocked_by_history_rewrite"

    @pytest.mark.parametrize("cmd", [
        "git clean -fd",
        "git clean -fdx",
    ])
    def test_git_clean_destructive(self, cmd):
        assert _cat(cmd) == "destructive_filesystem"
        assert _dec(cmd) == "blocked_by_destructive_filesystem"


# ── 6. Category matrix: destructive filesystem ────────────────────────────


class TestDestructiveFilesystem:
    @pytest.mark.parametrize("cmd", [
        "rm -rf /tmp/example",
        "rm -rf .",
        "rm -r build/",
        "rm -rf build dist",
    ])
    def test_rm_recursive_destructive(self, cmd):
        assert _cat(cmd) == "destructive_filesystem"
        assert _dec(cmd) == "blocked_by_destructive_filesystem"


# ── 7. Category matrix: filesystem_write ──────────────────────────────────


class TestFilesystemWrite:
    @pytest.mark.parametrize("cmd", [
        "rm file.txt",
        "mv a b",
        "cp a b",
        "mkdir new_dir",
        "touch new_file.txt",
        "chmod +x script.sh",
        "chmod 755 file",
        "chown user:group file",
        "chgrp staff file",
        "ln -s src dst",
        "ln src dst",
    ])
    def test_filesystem_write_commands(self, cmd):
        assert _cat(cmd) == "filesystem_write"

    def test_filesystem_write_no_task_blocked(self):
        assert _cat_idle("rm file.txt") == "blocked_by_missing_task"

    def test_filesystem_write_with_task_requires_preflight(self):
        assert _cat_active("rm file.txt") == "requires_preflight"


# ── 8. Category matrix: source/test/docs mutation ─────────────────────────


class TestMutationCategories:
    def test_echo_redirect_to_source(self):
        assert _cat("echo x > src/example.py") == "source_mutation"

    def test_echo_redirect_to_test(self):
        assert _cat("echo x > tests/test_example.py") == "test_mutation"

    def test_echo_redirect_to_docs(self):
        assert _cat("echo x > docs/example.md") == "docs_mutation"

    def test_cat_redirect_to_source(self):
        assert _cat("cat template > src/new.py") == "source_mutation"

    def test_source_mutation_no_task_blocked(self):
        assert _cat_idle("echo x > src/example.py") == "blocked_by_missing_task"

    def test_source_mutation_with_task_requires_preflight(self):
        assert _cat_active("echo x > src/example.py") == "requires_preflight"

    def test_test_mutation_no_task_blocked(self):
        assert _cat_idle("echo x > tests/test_new.py") == "blocked_by_missing_task"

    def test_docs_mutation_no_task_blocked(self):
        assert _cat_idle("echo x > docs/NEW.md") == "blocked_by_missing_task"


# ── 9. Category matrix: policy_forbidden_file_mutation ────────────────────


class TestPolicyForbiddenFileMutation:
    @pytest.mark.parametrize("cmd", [
        "echo x > README.md",
        "echo x >> README.md",
        "cat template > README.md",
        "python script.py > README.md",
        "echo x > docs/REAL_CAPTURED_TASKS.md",
        "echo x > docs/LINKEDIN_ARTICLE_DRAFT.md",
    ])
    def test_policy_forbidden_file_redirects(self, cmd):
        assert _cat(cmd) == "policy_forbidden_file_mutation"
        assert _dec(cmd) == "blocked_by_policy_forbidden_file"

    def test_policy_forbidden_blocks_regardless_of_task(self):
        assert _cat_idle("echo x > README.md") == "blocked_by_policy_forbidden_file"
        assert _cat_active("echo x > README.md") == "blocked_by_policy_forbidden_file"


# ── 10. Category matrix: backend_invocation ──────────────────────────────


class TestBackendInvocation:
    @pytest.mark.parametrize("cmd", [
        "claude 'modify src/app.py'",
        "claude-deepseek 'edit tests'",
        "codex 'fix bug'",
        "openai 'analyze code'",
        "gemini 'review PR'",
    ])
    def test_backend_programs_classified(self, cmd):
        assert _cat(cmd) == "backend_invocation"

    def test_backend_invocation_flag_set(self):
        result = _classify_command("claude 'do something'")
        assert result["detected_flags"]["backend_invocation_detected"] is True

    def test_backend_invocation_decision(self):
        assert _dec("claude 'modify src/app.py'") == "requires_human_review"


# ── 11. Category matrix: package_install ──────────────────────────────────


class TestPackageInstall:
    @pytest.mark.parametrize("cmd", [
        "pip install requests",
        "pip3 install requests",
        "python -m pip install requests",
        "brew install jq",
        "npm install",
        "npm install lodash",
        "cargo install ripgrep",
        "gem install bundler",
    ])
    def test_package_install_commands(self, cmd):
        assert _cat(cmd) == "package_install"
        assert _dec(cmd) == "requires_human_review"


# ── 12. Category matrix: network_access ──────────────────────────────────


class TestNetworkAccess:
    @pytest.mark.parametrize("cmd", [
        "curl https://example.com",
        "wget https://example.com/file",
        "ssh host",
        "ssh user@host.example.com",
        "scp file.txt user@host:/tmp",
        "aws s3 ls",
        "gcloud compute instances list",
        "gh pr list",
    ])
    def test_network_access_commands(self, cmd):
        assert _cat(cmd) == "network_access"
        assert _dec(cmd) == "requires_human_review"


# ── 13. Category matrix: secret_access ───────────────────────────────────


class TestSecretAccess:
    @pytest.mark.parametrize("cmd", [
        "cat ~/.ssh/id_rsa",
        "cat ~/.ssh/id_ed25519",
        "head ~/.ssh/id_rsa",
        "tail ~/.netrc",
        "cat ~/.aws/credentials",
        "cat ~/.aws/config",
        "cat ~/.kube/config",
        "cat ~/.docker/config.json",
        "cat /etc/shadow",
    ])
    def test_secret_file_reads(self, cmd):
        assert _cat(cmd) == "secret_access"

    @pytest.mark.parametrize("cmd", [
        "security find-generic-password",
        "security find-internet-password",
        "gpg --decrypt secrets.gpg",
        "gpg --export-secret-keys",
        "pass show api/key",
        "op item get 'API Key'",
        "vault kv get secret/api",
    ])
    def test_secret_access_programs(self, cmd):
        assert _cat(cmd) == "secret_access"

    def test_secret_access_flag_set(self):
        result = _classify_command("cat ~/.ssh/id_rsa")
        assert result["detected_flags"]["secret_access_detected"] is True

    def test_secret_access_decision(self):
        assert _dec("cat ~/.ssh/id_rsa") == "requires_human_review"

    def test_cat_normal_file_not_secret(self):
        assert _cat("cat PROJECT_STATUS.md") == "read_only_inspection"

    def test_cat_src_file_not_secret(self):
        assert _cat("cat src/pcae/core/shell_gate.py") == "read_only_inspection"


# ── 14. Category matrix: environment_mutation ────────────────────────────


class TestEnvironmentMutation:
    @pytest.mark.parametrize("cmd", [
        "export API_KEY=secret",
        "export PATH=/usr/local/bin:$PATH",
        "export DEBUG=1",
        "unset API_KEY",
    ])
    def test_export_unset_environment(self, cmd):
        assert _cat(cmd) == "environment_mutation"

    @pytest.mark.parametrize("cmd", [
        "DEBUG=1 python -m pytest",
        "PYTHONPATH=src python script.py",
    ])
    def test_env_var_prefix_benign(self, cmd):
        """Non-secret VAR=val prefixes → environment_mutation."""
        assert _cat(cmd) == "environment_mutation"

    @pytest.mark.parametrize("cmd", [
        "OPENAI_API_KEY=x python script.py",
        "API_KEY=abc123 curl https://api.example.com",
    ])
    def test_env_var_prefix_secret_detected_88v1(self, cmd):
        """Secret-like VAR=val prefixes → secret_access (88V.1 GAP-1 repair)."""
        assert _cat(cmd) == "secret_access"

    @pytest.mark.parametrize("cmd", [
        "source ~/.zshrc",
        "source ~/.bashrc",
        "source .env",
        ". ~/.bashrc",
        ". .env",
    ])
    def test_shell_source(self, cmd):
        assert _cat(cmd) == "environment_mutation"

    def test_environment_mutation_flag_set(self):
        result = _classify_command("export API_KEY=secret")
        assert result["detected_flags"]["environment_mutation_detected"] is True

    def test_environment_mutation_decision(self):
        assert _dec("export API_KEY=secret") == "requires_human_review"

    def test_env_var_prefix_decision(self):
        # 88V.1: secret-like VAR=val prefixes → secret_access → requires_human_review
        assert _dec("OPENAI_API_KEY=x python script.py") == "requires_human_review"

    def test_printenv_is_secret_exposure_88v1(self):
        # 88V.1 GAP-2 repair: printenv dumps all env vars → secret_access
        assert _cat("printenv") == "secret_access"

    def test_env_no_args_is_secret_exposure_88v1(self):
        # 88V.1 GAP-2 repair: env dumps all env vars → secret_access
        assert _cat("env") == "secret_access"


# ── 15. Category matrix: unknown ─────────────────────────────────────────


class TestUnknownCategory:
    @pytest.mark.parametrize("cmd", [
        "some_totally_unknown_program",
        "frobnicator --flag",
        "my_custom_script.sh",
    ])
    def test_unknown_program_blocked(self, cmd):
        assert _cat(cmd) == "unknown"
        assert _dec(cmd) == "blocked_by_unknown_command"


# ── 16. Idle vs active behavior ───────────────────────────────────────────


class TestIdleVsActiveBehavior:
    """Commands where idle vs active state changes the decision."""

    def test_test_execution_idle_requires_active_task(self):
        assert _cat_idle("python -m pytest tests/ -q") == "requires_active_task"

    def test_test_execution_active_allows(self):
        assert _cat_active("python -m pytest tests/ -q") == "allow_test_execution"

    def test_filesystem_write_idle_blocked(self):
        assert _cat_idle("rm file.txt") == "blocked_by_missing_task"

    def test_filesystem_write_active_requires_preflight(self):
        assert _cat_active("rm file.txt") == "requires_preflight"

    def test_source_mutation_idle_blocked(self):
        assert _cat_idle("echo x > src/example.py") == "blocked_by_missing_task"

    def test_source_mutation_active_requires_preflight(self):
        assert _cat_active("echo x > src/example.py") == "requires_preflight"

    def test_docs_mutation_idle_blocked(self):
        assert _cat_idle("echo x > docs/new.md") == "blocked_by_missing_task"

    def test_docs_mutation_active_requires_preflight(self):
        assert _cat_active("echo x > docs/new.md") == "requires_preflight"

    def test_read_only_same_in_idle_and_active(self):
        assert _cat_idle("ls") == "allow_read_only"
        assert _cat_active("ls") == "allow_read_only"

    def test_hard_block_same_in_idle_and_active(self):
        assert _cat_idle("git push --force") == "blocked_by_force_push"
        assert _cat_active("git push --force") == "blocked_by_force_push"

    def test_policy_forbidden_same_in_idle_and_active(self):
        assert _cat_idle("echo x > README.md") == "blocked_by_policy_forbidden_file"
        assert _cat_active("echo x > README.md") == "blocked_by_policy_forbidden_file"


# ── 17. Compound command handling ─────────────────────────────────────────


class TestCompoundCommands:
    def test_both_read_only_allows(self):
        assert _cat("git status && echo ok") == "read_only_inspection"

    def test_dangerous_second_segment_wins(self):
        assert _cat("git status && rm -rf /tmp") == "destructive_filesystem"

    def test_dangerous_first_segment_wins(self):
        assert _cat("rm -rf /tmp && echo done") == "destructive_filesystem"

    def test_git_commit_in_compound(self):
        assert _cat("pcae check ; git commit -m 'x'") == "raw_git_commit"

    def test_force_push_in_compound(self):
        assert _cat("git status && git push --force") == "force_push"

    def test_unknown_second_segment_conservative(self):
        # unknown wins over read_only (conservative)
        result = _classify_command("git status && some_unknown_cmd")
        assert result["command_category"] == "unknown"

    def test_compound_reason_code_present(self):
        result = _classify_command("git status && echo ok")
        assert "compound_command_detected" in result["reason_codes"]

    def test_double_ampersand_operator(self):
        assert _cat("ls && ls") == "read_only_inspection"

    def test_double_pipe_or_operator(self):
        assert _cat("grep x file || echo missing") == "read_only_inspection"

    def test_semicolon_operator(self):
        assert _cat("git status ; git log --oneline -3") == "read_only_inspection"

    def test_policy_forbidden_in_compound_wins(self):
        assert _cat("git status && echo x > README.md") == "policy_forbidden_file_mutation"

    def test_raw_git_push_in_compound_wins(self):
        assert _cat("pcae health && git push") == "raw_git_push"

    def test_source_mutation_in_compound(self):
        assert _cat("cat file && echo x > src/app.py") == "source_mutation"


# ── 18. Pipe chain handling ───────────────────────────────────────────────


class TestPipeChains:
    def test_cat_pipe_grep_read_only(self):
        assert _cat("cat PROJECT_STATUS.md | grep Phase") == "read_only_inspection"

    def test_git_log_pipe_grep_read_only(self):
        assert _cat("git log --oneline | grep Phase") == "read_only_inspection"

    def test_tee_to_tmp_filesystem_write(self):
        assert _cat("python -m pytest -n auto | tee /tmp/pytest.log") == "filesystem_write"

    def test_tee_to_readme_policy_forbidden(self):
        assert _cat("echo x | tee README.md") == "policy_forbidden_file_mutation"

    def test_tee_to_real_captured_tasks_forbidden(self):
        assert _cat("cat a | tee docs/REAL_CAPTURED_TASKS.md") == "policy_forbidden_file_mutation"

    def test_tee_to_linkedin_article_forbidden(self):
        assert _cat("cat a | tee docs/LINKEDIN_ARTICLE_DRAFT.md") == "policy_forbidden_file_mutation"

    def test_tee_to_source_file(self):
        assert _cat("cat template | tee src/new.py") == "source_mutation"

    def test_tee_to_test_file(self):
        assert _cat("cat template | tee tests/test_new.py") == "test_mutation"

    def test_tee_to_docs_file(self):
        assert _cat("cat template | tee docs/new.md") == "docs_mutation"

    def test_tee_append_flag_ignored_for_path(self):
        # tee -a README.md still writes to README.md
        assert _cat("cat file | tee -a README.md") == "policy_forbidden_file_mutation"

    def test_pipe_chain_reason_code_present(self):
        result = _classify_command("cat file | grep pattern")
        assert "pipe_chain_detected" in result["reason_codes"]

    def test_tee_write_reason_code_present(self):
        result = _classify_command("echo x | tee README.md")
        assert "pipe_tee_write_detected" in result["reason_codes"]

    def test_pipe_to_unknown_conservative(self):
        result = _classify_command("cat file | some_unknown_program")
        assert result["command_category"] == "unknown"

    def test_pure_read_pipe_allows(self):
        assert _dec("cat PROJECT_STATUS.md | grep Phase") == "allow_read_only"


# ── 19. Redirection handling ──────────────────────────────────────────────


class TestRedirectionHandling:
    def test_redirect_to_tmp_filesystem_write(self):
        assert _cat("echo x > /tmp/output.txt") == "filesystem_write"

    def test_append_to_changelog(self):
        assert _cat("echo x >> CHANGELOG.md") == "filesystem_write"

    def test_redirect_to_source_file(self):
        assert _cat("echo x > src/new.py") == "source_mutation"

    def test_redirect_to_test_file(self):
        assert _cat("echo x > tests/test_new.py") == "test_mutation"

    def test_redirect_to_docs_file(self):
        assert _cat("echo x > docs/new.md") == "docs_mutation"

    def test_redirect_to_readme_forbidden(self):
        assert _cat("echo x > README.md") == "policy_forbidden_file_mutation"

    def test_redirect_to_real_captured_tasks_forbidden(self):
        assert _cat("echo x > docs/REAL_CAPTURED_TASKS.md") == "policy_forbidden_file_mutation"

    def test_git_log_redirected_to_file(self):
        assert _cat("git log --oneline > /tmp/log.txt") == "filesystem_write"

    def test_git_status_redirected_to_readme(self):
        assert _cat("git status > README.md") == "policy_forbidden_file_mutation"

    def test_python_script_redirect(self):
        assert _cat("python script.py > out.txt") == "filesystem_write"

    def test_python_script_redirect_to_src(self):
        assert _cat("python gen.py > src/generated.py") == "source_mutation"

    def test_sed_inplace_source(self):
        assert _cat("sed -i 's/old/new/g' src/app.py") == "source_mutation"

    def test_sed_inplace_test(self):
        assert _cat("sed -i 's/old/new/g' tests/test_app.py") == "test_mutation"


# ── 20. Performed flags invariant ────────────────────────────────────────


_ALL_PERFORMED_FLAGS = (
    "authorization_granted",
    "execution_authorized",
    "command_executed",
    "repo_mutation_performed",
    "backend_invocation_performed",
    "prompt_sent",
    "capture_performed",
    "intake_performed",
    "adoption_performed",
    "raw_git_push_performed",
    "force_push_performed",
    "storage_written",
)

_REPRESENTATIVE_COMMANDS = [
    "ls",
    "git status",
    "python -m pytest -n auto",
    "pcae health",
    "pcae push",
    "git push --force",
    "rm -rf /tmp",
    "echo x > README.md",
    "cat ~/.ssh/id_rsa",
    "export API_KEY=secret",
    "claude 'do something'",
    "git status && rm -rf /",
    "echo x | tee README.md",
    "chmod +x script.sh",
    "pip install requests",
    "curl https://example.com",
    "some_unknown_program",
]


class TestPerformedFlagsInvariant:
    @pytest.mark.parametrize("cmd", _REPRESENTATIVE_COMMANDS)
    def test_all_performed_flags_false(self, cmd):
        sg = _sg(cmd)
        for flag in _ALL_PERFORMED_FLAGS:
            assert sg[flag] is False, f"{flag}=True for command: {cmd!r}"


# ── 21. Classifier-only boundary ─────────────────────────────────────────


class TestClassifierOnlyBoundary:
    def test_does_not_execute_commands(self):
        sg = _sg("rm -rf /")
        assert sg["safety_notes"]["shell_gate_does_not_execute_commands"] is True

    def test_does_not_intercept_shell(self):
        sg = _sg("ls")
        assert sg["safety_notes"]["shell_gate_does_not_intercept_shell"] is True

    def test_does_not_invoke_backends(self):
        sg = _sg("claude 'do something'")
        assert sg["safety_notes"]["shell_gate_does_not_invoke_backends"] is True

    def test_does_not_install_wrappers(self):
        sg = _sg("ls")
        assert sg["safety_notes"]["shell_gate_does_not_install_wrappers"] is True

    def test_permission_broker_not_implemented(self):
        sg = _sg("ls")
        assert sg["safety_notes"]["permission_broker_not_implemented"] is True

    def test_execution_authorization_not_granted(self):
        sg = _sg("ls")
        assert sg["safety_notes"]["execution_authorization_not_granted"] is True

    def test_gate_type_is_prototype(self):
        sg = _sg("ls")
        assert sg["gate_type"] == "shell_gate_prototype"


# ── 22. False-positive review ────────────────────────────────────────────


class TestFalsePositiveReview:
    """
    Known acceptable false positives (over-blocking).  These classify as
    more restrictive than strictly necessary but preserve safety.
    """

    def test_echo_inside_quotes_may_trigger_redirection(self):
        # 'echo "x > y"' — the > is inside a quoted string but the regex
        # still matches.  This is a known conservative false positive.
        # We document it rather than fix it in 88Q.
        result = _classify_command("echo 'x > y'")
        # Acceptable outcomes: either read_only or filesystem_write
        assert result["command_category"] in ("read_only_inspection", "filesystem_write",
                                               "policy_forbidden_file_mutation")

    def test_env_with_args_is_secret_exposure_88v1(self):
        # 88V.1 GAP-2 repair: 'env python script.py' — env is now classified
        # as secret_access. Previously was read_only (false negative).
        assert _cat("env python script.py") == "secret_access"

    def test_printenv_grep_secret_exposure_88v1(self):
        # 88V.1 GAP-2 repair: printenv | grep KEY — pipe chain picks most
        # restrictive segment; printenv → secret_access wins.
        assert _cat("printenv | grep KEY") == "secret_access"

    def test_git_fetch_read_only(self):
        # git fetch is in the read-only list (doesn't modify working tree).
        assert _cat("git fetch origin") == "read_only_inspection"

    def test_diff_files_read_only(self):
        assert _cat("diff src/a.py src/b.py") == "read_only_inspection"


# ── 23. False-negative review ────────────────────────────────────────────


class TestFalseNegativeReview:
    """
    Previously undetected dangerous commands that 88Q fixes.
    Each test verifies a real false negative from 88P is now caught.
    """

    def test_tee_to_readme_now_blocked(self):
        # 88P: echo x | tee README.md → read_only_inspection (FALSE NEGATIVE)
        # 88Q: → policy_forbidden_file_mutation
        assert _cat("echo x | tee README.md") == "policy_forbidden_file_mutation"

    def test_cat_ssh_key_now_secret(self):
        # 88P: cat ~/.ssh/id_rsa → read_only_inspection (FALSE NEGATIVE)
        # 88Q: → secret_access
        assert _cat("cat ~/.ssh/id_rsa") == "secret_access"

    def test_compound_dangerous_second_segment(self):
        # 88P: git status && rm -rf / → read_only_inspection (FALSE NEGATIVE)
        # 88Q: → destructive_filesystem
        assert _cat("git status && rm -rf /") == "destructive_filesystem"

    def test_export_env_mutation_now_classified(self):
        # 88P: export API_KEY=secret → unknown (correct block, wrong category)
        # 88Q: → environment_mutation (correct category)
        assert _cat("export API_KEY=secret") == "environment_mutation"

    def test_claude_backend_now_classified(self):
        # 88P: claude "do something" → unknown (correct block, wrong category)
        # 88Q: → backend_invocation (correct category)
        assert _cat("claude 'do something'") == "backend_invocation"

    def test_security_program_now_classified(self):
        # 88P: security find-generic-password → unknown (correct block, wrong category)
        # 88Q: → secret_access (correct category)
        assert _cat("security find-generic-password") == "secret_access"

    def test_chmod_now_classified(self):
        # 88P: chmod +x script.sh → unknown
        # 88Q: → filesystem_write
        assert _cat("chmod +x script.sh") == "filesystem_write"

    def test_git_push_in_compound_now_blocked(self):
        # 88P: pcae health && git push → read_only_inspection (FALSE NEGATIVE)
        # 88Q: → raw_git_push
        assert _cat("pcae health && git push") == "raw_git_push"


# ── 24. Helper unit tests ─────────────────────────────────────────────────


class TestHelperFunctions:
    def test_split_on_operators_compound(self):
        from pcae.core.shell_gate import _COMPOUND_OPS
        tokens = ["git", "status", "&&", "echo", "ok"]
        segments = _split_on_operators(tokens, _COMPOUND_OPS)
        assert segments == [["git", "status"], ["echo", "ok"]]

    def test_split_on_operators_pipe(self):
        tokens = ["cat", "file", "|", "grep", "pattern"]
        segments = _split_on_operators(tokens, {"|"})
        assert segments == [["cat", "file"], ["grep", "pattern"]]

    def test_split_on_operators_no_op(self):
        tokens = ["git", "status"]
        segments = _split_on_operators(tokens, {"&&"})
        assert segments == [["git", "status"]]

    def test_find_tee_write_target_simple(self):
        pipe_segs = [["cat", "file"], ["tee", "README.md"]]
        assert _find_tee_write_target(pipe_segs) == "README.md"

    def test_find_tee_write_target_with_flag(self):
        pipe_segs = [["cat", "file"], ["tee", "-a", "output.txt"]]
        assert _find_tee_write_target(pipe_segs) == "output.txt"

    def test_find_tee_write_target_no_tee(self):
        pipe_segs = [["cat", "file"], ["grep", "pattern"]]
        assert _find_tee_write_target(pipe_segs) is None

    def test_most_restrictive_picks_lower_severity(self):
        c1 = {"command_category": "read_only_inspection",
              "reason_codes": ["r"], "detected_flags": {}}
        c2 = {"command_category": "raw_git_push",
              "reason_codes": ["p"], "detected_flags": {}}
        result = _most_restrictive_classification([c1, c2])
        assert result["command_category"] == "raw_git_push"

    def test_most_restrictive_single_item(self):
        c1 = {"command_category": "read_only_inspection",
              "reason_codes": ["r"], "detected_flags": {}}
        result = _most_restrictive_classification([c1])
        assert result["command_category"] == "read_only_inspection"

    def test_most_restrictive_empty_returns_unknown(self):
        result = _most_restrictive_classification([])
        assert result["command_category"] == "unknown"

    def test_is_secret_file_access_ssh(self):
        assert _is_secret_file_access(["~/.ssh/id_rsa"]) is True

    def test_is_secret_file_access_aws(self):
        assert _is_secret_file_access(["~/.aws/credentials"]) is True

    def test_is_secret_file_access_normal_file(self):
        assert _is_secret_file_access(["PROJECT_STATUS.md"]) is False

    def test_is_secret_file_access_empty(self):
        assert _is_secret_file_access([]) is False

    def test_classify_single_same_as_classify_command_for_simple(self):
        # _classify_single and _classify_command should agree for simple commands
        assert (
            _classify_single("ls")["command_category"]
            == _classify_command("ls")["command_category"]
        )
        assert (
            _classify_single("git push --force")["command_category"]
            == _classify_command("git push --force")["command_category"]
        )
