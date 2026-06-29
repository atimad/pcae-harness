"""Tests for Phase 93B Narrow Shell Gate Prototype — core check_shell_gate().

Tests the broker-integrated shell gate check function. All checks are
simulation-only — no command execution, no shell interception, no enforcement.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pcae.core.shell_gate import check_shell_gate

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent


def _check(command_text: str) -> dict:
    """Run check_shell_gate() and return the result dict."""
    return check_shell_gate(REPO_ROOT, command_text)


# ═══════════════════════════════════════════════════════════════════════════════
# Classification tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifierCategories:
    """Verify the shell gate classifies commands into correct categories."""

    @pytest.mark.parametrize("cmd,expected_category", [
        ("pcae health", "pcae_governed_lifecycle"),
        ("pcae check", "pcae_governed_lifecycle"),
        ("pcae commit", "pcae_governed_commit"),
        ("pcae push", "pcae_governed_push"),
        ("git status", "read_only_inspection"),
        ("git log", "read_only_inspection"),
        ("git diff", "read_only_inspection"),
        ("git branch", "read_only_inspection"),
        ("ls", "read_only_inspection"),
        ("cat README.md", "read_only_inspection"),
        ("echo hello", "read_only_inspection"),
        ("git commit -m x", "raw_git_commit"),
        ("git push", "raw_git_push"),
        ("git push --force", "force_push"),
        ("git push -f", "force_push"),
        ("git push --force-with-lease", "force_push"),
        ("git rebase main", "git_history_rewrite"),
        ("rm -rf /tmp/test", "destructive_filesystem"),
        ("rm -rf /", "destructive_filesystem"),
        ("git clean -fdx", "destructive_filesystem"),
        ("python -m pytest tests/", "test_execution"),
        ("pytest tests/", "test_execution"),
    ])
    def test_classification(self, cmd, expected_category):
        result = _check(cmd)
        assert result["command_category"] == expected_category, \
            f"Expected {expected_category} for {cmd!r}, got {result['command_category']}"


class TestClassifierCommandClass:
    """Verify command class mapping for broker."""

    @pytest.mark.parametrize("cmd,expected_class", [
        ("pcae health", "governed"),
        ("pcae check", "governed"),
        ("git status", "read_only"),
        ("git log", "read_only"),
        ("git commit -m x", "raw_git_commit"),
        ("git push", "raw_git_push"),
        ("git push --force", "force_push"),
        ("git push -f", "force_push"),
        ("git push --force-with-lease", "force_push"),
        ("rm -rf /tmp/x", "destructive_filesystem"),
        ("git clean -fdx", "destructive_filesystem"),
        ("python -m pytest tests/", "read_only"),
        ("pytest tests/", "read_only"),
        ("xyzzy123_nonexistent_cmd", "unknown"),
    ])
    def test_command_class(self, cmd, expected_class):
        result = _check(cmd)
        assert result["command_class"] == expected_class, \
            f"Expected class {expected_class} for {cmd!r}, got {result['command_class']}"


class TestNoVerifyDetection:
    """Verify --no-verify flag detection and precedence."""

    def test_git_commit_no_verify_long(self):
        result = _check("git commit --no-verify -m x")
        assert result["command_class"] == "no_verify"
        assert result["decision"] == "deny"
        assert result["hard_block"] is True

    def test_git_commit_no_verify_short(self):
        result = _check("git commit -n -m x")
        assert result["command_class"] == "no_verify"
        assert result["decision"] == "deny"
        assert result["hard_block"] is True

    def test_git_push_no_verify(self):
        result = _check("git push --no-verify")
        assert result["command_class"] == "no_verify"
        assert result["decision"] == "deny"
        assert result["hard_block"] is True

    def test_no_verify_takes_precedence(self):
        result = _check("git commit --no-verify -m test")
        assert result["command_class"] == "no_verify"
        assert result["command_category"] == "raw_git_commit"


# ═══════════════════════════════════════════════════════════════════════════════
# Decision behavior tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestHardBlockDecisions:
    """Verify hard-block command classes return deny with hard_block=true."""

    def test_raw_git_commit_is_hard_blocked(self):
        result = _check("git commit -m x")
        assert result["decision"] == "deny"
        assert result["hard_block"] is True
        assert result["reason_code"] == "blocked_by_raw_git_commit"

    def test_raw_git_push_is_hard_blocked(self):
        result = _check("git push")
        assert result["decision"] == "deny"
        assert result["hard_block"] is True
        assert result["reason_code"] == "blocked_by_raw_git_push"

    def test_force_push_is_hard_blocked(self):
        result = _check("git push --force")
        assert result["decision"] == "deny"
        assert result["hard_block"] is True
        assert result["reason_code"] == "blocked_by_force_push"

    def test_force_push_short_flag_is_hard_blocked(self):
        result = _check("git push -f")
        assert result["decision"] == "deny"
        assert result["hard_block"] is True

    def test_no_verify_is_hard_blocked(self):
        result = _check("git commit --no-verify -m x")
        assert result["decision"] == "deny"
        assert result["hard_block"] is True
        assert result["reason_code"] == "blocked_by_no_verify"

    def test_destructive_filesystem_is_hard_blocked(self):
        result = _check("rm -rf /tmp/x")
        assert result["decision"] == "deny"
        assert result["hard_block"] is True
        assert result["reason_code"] == "blocked_by_destructive_filesystem"

    def test_unknown_command_fails_closed(self):
        result = _check("xyzzy_not_a_command")
        assert result["decision"] == "deny"
        assert result["hard_block"] is True


class TestAllowDecisions:
    """Verify read-only and governed commands are allowed."""

    def test_read_only_inspection_allowed(self):
        result = _check("git status")
        assert result["decision"] == "allow"
        assert result["hard_block"] is False

    def test_ls_is_allowed(self):
        result = _check("ls")
        assert result["decision"] == "allow"
        assert result["hard_block"] is False

    def test_governed_pcae_allowed(self):
        result = _check("pcae health")
        assert result["decision"] == "allow"
        assert result["hard_block"] is False


class TestTestExecution:
    """Verify test execution is not hard-blocked."""

    def test_pytest_not_hard_blocked(self):
        result = _check("pytest tests/ -q")
        assert result["hard_block"] is False, \
            f"pytest should not be hard-blocked, got {result['reason_code']}"

    def test_python_pytest_not_hard_blocked(self):
        result = _check("python -m pytest tests/ -q")
        assert result["hard_block"] is False, \
            f"python -m pytest should not be hard-blocked, got {result['reason_code']}"


class TestBackendInvocation:
    """Verify backend invocation is safely gated."""

    def test_backend_invocation_safe_denial(self):
        result = _check("claude 'write code'")
        assert result["decision"] in ("deny", "human_review"), \
            f"Backend invocation should be deny or human_review, got {result['decision']}"

    def test_backend_invocation_not_allowed(self):
        result = _check("deepseek chat")
        assert result["decision"] != "allow", \
            "Backend invocation must not be allowed without review"


# ═══════════════════════════════════════════════════════════════════════════════
# Hard-block invariant tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestHardBlockNonOverridable:
    """Verify hard blocks cannot be overridden (88V §16)."""

    def test_force_push_hard_block_present(self):
        result = _check("git push --force origin main")
        assert result["hard_block"] is True
        assert result["decision"] == "deny"
        assert result["safety_notes"]["hard_blocks_non_overridable"] is True

    def test_raw_git_commit_hard_block_present(self):
        result = _check("git commit -m 'test'")
        assert result["hard_block"] is True
        assert result["decision"] == "deny"

    def test_destructive_fs_hard_block_present(self):
        result = _check("rm -rf important_dir")
        assert result["hard_block"] is True
        assert result["decision"] == "deny"


# ═══════════════════════════════════════════════════════════════════════════════
# Output model tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestOutputModel:
    """Verify the output includes all required fields."""

    REQUIRED_KEYS = [
        "schema_version", "generated_at", "command_text",
        "command_category", "command_class", "action_type",
        "decision", "hard_block", "reason_code", "reason_codes",
        "message", "required_evidence", "audit_payload",
        "simulation_only", "no_execution", "no_enforcement",
        "authorization_granted", "execution_authorized",
        "event_id", "safety_notes",
    ]

    def test_output_has_all_required_keys(self):
        result = _check("git status")
        for key in self.REQUIRED_KEYS:
            assert key in result, f"Missing required key: {key}"

    def test_simulation_only_is_true(self):
        result = _check("git push")
        assert result["simulation_only"] is True

    def test_no_execution_is_true(self):
        result = _check("rm -rf /")
        assert result["no_execution"] is True

    def test_no_enforcement_is_true(self):
        result = _check("git commit -m x")
        assert result["no_enforcement"] is True

    def test_authorization_granted_is_false(self):
        result = _check("git status")
        assert result["authorization_granted"] is False

    def test_audit_payload_present(self):
        result = _check("git push --force")
        audit = result["audit_payload"]
        assert "event_id" in audit
        assert "event_type" in audit
        assert "timestamp" in audit
        assert "decision" in audit
        assert "hard_block" in audit

    def test_schema_version_is_1_0(self):
        result = _check("ls")
        assert result["schema_version"] == "1.0"


# ═══════════════════════════════════════════════════════════════════════════════
# Non-execution guarantee tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestNoExecutionGuarantee:
    """Verify no code path executes the command."""

    def test_command_executed_always_false(self):
        result = _check("rm -rf /")
        assert result["command_executed"] is False

    def test_shell_intercepted_always_false(self):
        result = _check("git push --force")
        assert result["shell_intercepted"] is False

    def test_backend_invoked_always_false(self):
        result = _check("claude 'hello'")
        assert result["backend_invoked"] is False

    def test_safety_notes_confirm_no_execution(self):
        result = _check("git commit -m x")
        notes = result["safety_notes"]
        assert notes["shell_gate_does_not_execute_commands"] is True
        assert notes["shell_gate_does_not_intercept_shell"] is True
        assert notes["shell_gate_does_not_install_wrappers"] is True
        assert notes["shell_gate_does_not_invoke_backends"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# Edge case tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_empty_command_fails_closed(self):
        result = _check("")
        assert result["command_category"] == "unknown"
        assert result["hard_block"] is True

    def test_whitespace_only_command(self):
        result = _check("   ")
        assert result["command_category"] == "unknown"
        assert result["hard_block"] is True

    def test_compound_command_with_hard_block(self):
        result = _check("git status && git push --force")
        assert result["decision"] == "deny"
        assert result["hard_block"] is True

    def test_git_commit_message_with_special_chars(self):
        result = _check('git commit -m "fix: update README"')
        assert result["command_class"] == "raw_git_commit"
        assert result["hard_block"] is True

    def test_command_with_env_vars(self):
        # DEBUG=1 ... is classified as environment_mutation by the existing
        # shell gate classifier, which maps to a mutating action.
        result = _check("DEBUG=1 pytest tests/")
        # The exact outcome depends on whether the classifier sees env var
        # prefix or pytest invocation first. Both safe behaviors are valid.
        assert result["command_category"] in (
            "environment_mutation", "test_execution",
        ), f"Unexpected category: {result['command_category']}"
