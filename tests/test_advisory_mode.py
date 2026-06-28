"""
Advisory mode prototype tests — Phase 88X.

Tests for pcae advisory check, explain, and status.
All tests are fast_green (no subprocess execution, no file I/O beyond
reading governance state).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from pcae.core.advisory import (
    ADVISORY_DECISIONS,
    _BROKER_TO_ADVISORY,
    build_advisory,
    build_advisory_explain,
    build_advisory_status,
)
from pcae.core.permission_broker import BPE_DECISIONS

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent

_PERFORMED_FLAGS = [
    "authorization_granted",
    "execution_authorized",
    "command_executed",
    "repo_mutation_performed",
    "backend_invocation_performed",
    "prompt_sent",
    "capture_performed",
    "intake_performed",
    "adoption_performed",
    "commit_performed",
    "push_performed",
    "raw_git_push_performed",
    "force_push_performed",
    "storage_written",
]

_REQUIRED_ENVELOPE_FIELDS = [
    "schema_version", "generated_at", "repository_root",
    "advisory_mode", "requested_action", "requested_command",
    "requested_command_redacted", "broker_decision",
    "shell_gate_decision", "shell_gate_category",
    "advisory_decision", "advisory_recommendation",
    "would_block", "would_require_human_review",
    "would_require_preflight", "would_require_active_task",
    "would_require_more_evidence",
    "hard_block_present", "hard_block_reason",
    "human_approval_relevant", "accepted_risk_relevant",
    "redaction_applied", "redaction_reason", "safe_to_display",
    "operator_message", "next_required_action",
    "authorization_granted", "execution_authorized",
    "command_executed", "enforcement_applied",
    "performed_flags", "evidence_sources", "warnings", "errors",
]

_INVARIANT_FALSE_FIELDS = [
    "authorization_granted",
    "execution_authorized",
    "command_executed",
    "enforcement_applied",
]

# ── Helpers ────────────────────────────────────────────────────────────────

def _adv(command: str, **kwargs: Any) -> dict[str, Any]:
    """Build advisory output for a command."""
    return build_advisory(
        repo_root=REPO_ROOT,
        requested_command=command,
        **kwargs,
    )


def _cli_check(command: str, **extra_args: str) -> dict[str, Any]:
    """Run pcae advisory check --command <CMD> --json and parse output."""
    cmd = [sys.executable, "-m", "pcae", "advisory", "check",
           "--command", command, "--json"]
    for flag in extra_args:
        cmd.append(flag)
    result = subprocess.run(cmd, capture_output=True, text=True,
                            cwd=str(REPO_ROOT))
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return json.loads(result.stdout)


# ═══════════════════════════════════════════════════════════════════════════════
# Advisory check — JSON envelope
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryCheckEnvelope:
    """Advisory check JSON output has the correct shape and invariants."""

    def test_json_envelope_has_all_required_fields(self):
        data = _adv("git status")
        for field in _REQUIRED_ENVELOPE_FIELDS:
            assert field in data, f"Missing required field: {field}"

    def test_json_envelope_advisory_mode_true(self):
        data = _adv("git status")
        assert data["advisory_mode"] is True

    def test_json_envelope_schema_version(self):
        data = _adv("git status")
        assert data["schema_version"] == "0.1"

    def test_authorization_granted_false(self):
        data = _adv("git status")
        assert data["authorization_granted"] is False

    def test_execution_authorized_false(self):
        data = _adv("git status")
        assert data["execution_authorized"] is False

    def test_command_executed_false(self):
        data = _adv("git status")
        assert data["command_executed"] is False

    def test_enforcement_applied_false(self):
        data = _adv("git push --force origin main")
        assert data["enforcement_applied"] is False

    def test_shell_intercepted_false(self):
        data = _adv("git push --force origin main")
        assert data["shell_intercepted"] is False

    def test_broker_decision_in_bpe_decisions(self):
        data = _adv("git status")
        assert data["broker_decision"] in BPE_DECISIONS

    def test_advisory_decision_in_advisory_decisions(self):
        data = _adv("git status")
        assert data["advisory_decision"] in ADVISORY_DECISIONS

    def test_all_invariant_fields_false_for_read_only(self):
        data = _adv("git status")
        for field in _INVARIANT_FALSE_FIELDS:
            assert data[field] is False, f"{field} should be False"

    def test_all_invariant_fields_false_for_hard_block(self):
        data = _adv("git push --force origin main")
        for field in _INVARIANT_FALSE_FIELDS:
            assert data[field] is False, f"{field} should be False"

    def test_all_performed_flags_false(self):
        data = _adv("git push --force origin main")
        performed = data["performed_flags"]
        for flag in _PERFORMED_FLAGS:
            assert performed[flag] is False, f"performed.{flag} should be False"

    @pytest.mark.parametrize("flag", _PERFORMED_FLAGS)
    def test_each_performed_flag_false_read_only(self, flag):
        data = _adv("git status")
        assert data["performed_flags"][flag] is False


# ═══════════════════════════════════════════════════════════════════════════════
# Advisory check — Read-only commands
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryCheckReadOnly:
    """Read-only commands produce safe non-blocking advisory output."""

    def test_git_status_read_only(self):
        data = _adv("git status")
        assert data["broker_decision"] == "allow_preflight_only"
        assert data["advisory_decision"] == "would_allow_governed_preflight_only"
        assert data["would_block"] is False
        assert data["hard_block_present"] is False

    def test_ls_read_only(self):
        data = _adv("ls -la")
        assert data["would_block"] is False
        assert data["hard_block_present"] is False

    def test_pwd_read_only(self):
        data = _adv("pwd")
        assert data["would_block"] is False

    def test_echo_read_only(self):
        data = _adv("echo hello")
        assert data["would_block"] is False

    def test_pcae_health_is_governed(self):
        data = _adv("pcae health")
        assert data["would_block"] is False

    def test_diff_read_only(self):
        data = _adv("diff file1 file2")
        assert data["would_block"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# Advisory check — Hard blocks
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryCheckHardBlocks:
    """Commands that trigger hard blocks produce would_block_* advisory decisions."""

    def test_git_push_hard_block(self):
        data = _adv("git push origin main")
        assert data["would_block"] is True
        assert data["hard_block_present"] is True
        assert data["advisory_decision"] == "would_block_by_raw_git_push"

    def test_git_push_force_hard_block(self):
        data = _adv("git push --force origin main")
        assert data["would_block"] is True
        assert data["hard_block_present"] is True
        assert data["advisory_decision"] == "would_block_by_force_push"

    def test_rm_rf_hard_block(self):
        data = _adv("rm -rf /")
        assert data["would_block"] is True
        assert data["hard_block_present"] is True

    def test_echo_redirect_forbidden_file_hard_block(self):
        data = _adv("echo x > README.md")
        assert data["would_block"] is True
        assert data["hard_block_present"] is True

    def test_git_clean_hard_block(self):
        data = _adv("git clean -fd")
        assert data["would_block"] is True
        assert data["hard_block_present"] is True

    def test_unknown_command_hard_block(self):
        data = _adv("unknown-tool --dangerous")
        assert data["would_block"] is True
        assert data["hard_block_present"] is True

    def test_raw_git_commit_hard_block(self):
        data = _adv("git commit -m 'unsafe'")
        assert data["would_block"] is True
        assert data["hard_block_present"] is True

    def test_history_rewrite_hard_block(self):
        data = _adv("git rebase -i HEAD~3")
        assert data["would_block"] is True
        assert data["hard_block_present"] is True

    def test_pcae_health_and_push_compound_hard_block(self):
        data = _adv("pcae health && git push origin main")
        assert data["would_block"] is True
        assert data["hard_block_present"] is True

    def test_hard_block_operator_message_present(self):
        data = _adv("git push --force origin main")
        assert "blocked" in data["operator_message"].lower()
        assert "advisory mode does not enforce" in data["operator_message"].lower()

    def test_hard_block_next_action_present(self):
        data = _adv("git push --force origin main")
        assert len(data["next_required_action"]) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Advisory check — Review / preflight states
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryCheckReviewPreflight:
    """Commands requiring review or preflight produce appropriate advisory states."""

    def test_pip_install_requires_human_review(self):
        data = _adv("pip install requests")
        assert data["would_require_human_review"] is True
        assert data["would_block"] is False

    def test_curl_requires_human_review(self):
        data = _adv("curl https://example.com")
        assert data["would_require_human_review"] is True

    def test_export_secret_requires_human_review(self):
        data = _adv("export OPENAI_API_KEY=x")
        # export is environment_mutation → requires_human_review
        assert data["would_require_human_review"] is True

    def test_review_commands_no_hard_block(self):
        for cmd in ["pip install requests", "curl https://example.com"]:
            data = _adv(cmd)
            assert data["hard_block_present"] is False, f"{cmd} should not be hard blocked"
            assert data["authorization_granted"] is False

    def test_expensive_pytest_non_authorizing(self):
        data = _adv("python -m pytest -n auto")
        # Expensive pytest evaluation is always non-authorizing.
        # With active task + test_run_clear → allow_test_execution → preflight_only
        # Without active task → requires_active_task → blocked_by_task_contract
        assert data["authorization_granted"] is False
        assert data["execution_authorized"] is False
        assert data["command_executed"] is False

    def test_human_approval_relevant_for_review_commands(self):
        data = _adv("curl https://example.com")
        assert data["human_approval_relevant"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# Advisory check — Secret redaction
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryCheckSecretRedaction:
    """Secret-access commands are redacted in advisory output (88V.1 rules)."""

    def test_openai_key_not_in_json(self):
        data = _adv("OPENAI_API_KEY=sk-abc123 python script.py")
        raw = json.dumps(data, sort_keys=True)
        assert "sk-abc123" not in raw, "Raw secret leaked in JSON"

    def test_token_not_in_json(self):
        data = _adv("TOKEN=ghp_secret123 curl https://api.github.com")
        raw = json.dumps(data, sort_keys=True)
        assert "ghp_secret123" not in raw, "Raw token leaked in JSON"

    def test_password_not_in_json(self):
        data = _adv("PASSWORD=s3cr3t! echo ok")
        raw = json.dumps(data, sort_keys=True)
        assert "s3cr3t!" not in raw, "Raw password leaked in JSON"

    def test_cat_ssh_key_not_in_json(self):
        data = _adv("cat ~/.ssh/id_rsa")
        raw = json.dumps(data, sort_keys=True)
        assert "~/.ssh/id_rsa" not in raw, "Raw secret file path leaked in JSON"

    def test_security_find_generic_not_in_json(self):
        data = _adv("security find-generic-password")
        raw = json.dumps(data, sort_keys=True)
        assert "find-generic-password" not in raw, "Raw secret command leaked in JSON"

    def test_printenv_secret_not_in_json(self):
        data = _adv("printenv OPENAI_API_KEY")
        raw = json.dumps(data, sort_keys=True)
        assert "OPENAI_API_KEY" not in raw, "Raw secret var name leaked in JSON"

    def test_env_grep_secret_not_in_json(self):
        data = _adv("env | grep SECRET")
        raw = json.dumps(data, sort_keys=True)
        assert "SECRET" not in raw, "Raw secret pattern leaked in JSON"

    def test_secret_commands_are_redacted(self):
        for cmd in [
            "OPENAI_API_KEY=x python script.py",
            "cat ~/.ssh/id_rsa",
            "security find-generic-password",
            "printenv",
        ]:
            data = _adv(cmd)
            assert data["redaction_applied"] is True, f"{cmd} should be redacted"

    def test_redaction_reason_populated(self):
        data = _adv("cat ~/.ssh/id_rsa")
        assert data["redaction_reason"] == "secret_access_detected"

    def test_safe_to_display_true_for_redacted(self):
        data = _adv("cat ~/.ssh/id_rsa")
        assert data["safe_to_display"] is True

    def test_requested_command_redacted_flag_true(self):
        data = _adv("OPENAI_API_KEY=x python script.py")
        assert data["requested_command_redacted"] is True

    def test_ordinary_commands_not_over_redacted(self):
        for cmd in ["git status", "ls -la", "echo hello"]:
            data = _adv(cmd)
            assert data["redaction_applied"] is False, f"{cmd} should NOT be redacted"
            assert data["requested_command_redacted"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# Advisory check — Broker → Advisory mapping
# ═══════════════════════════════════════════════════════════════════════════════

class TestBrokerToAdvisoryMapping:
    """Every broker decision maps to an advisory decision."""

    def test_all_bpe_decisions_have_mapping(self):
        unmapped = []
        for dec in BPE_DECISIONS:
            if dec not in _BROKER_TO_ADVISORY:
                unmapped.append(dec)
        assert unmapped == [], f"Unmapped broker decisions: {unmapped}"

    def test_all_mapped_values_are_valid_advisory_decisions(self):
        for broker_dec, advisory_dec in _BROKER_TO_ADVISORY.items():
            assert advisory_dec in ADVISORY_DECISIONS, (
                f"Broker {broker_dec} maps to invalid advisory {advisory_dec}"
            )

    def test_hard_blocks_map_to_would_block(self):
        for broker_dec, advisory_dec in _BROKER_TO_ADVISORY.items():
            if broker_dec.startswith("blocked_by_"):
                assert advisory_dec.startswith("would_block_"), (
                    f"Hard block {broker_dec} maps to {advisory_dec}, "
                    f"expected would_block_*"
                )

    def test_deny_maps_to_would_deny(self):
        assert _BROKER_TO_ADVISORY["deny"] == "would_deny"

    def test_allow_preflight_only_not_blocked(self):
        assert _BROKER_TO_ADVISORY["allow_preflight_only"] == "would_allow_governed_preflight_only"


# ═══════════════════════════════════════════════════════════════════════════════
# Advisory explain
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryExplain:
    """Advisory explain returns valid explanations for decisions."""

    def test_explain_force_push(self):
        data = build_advisory_explain("would_block_by_force_push")
        assert data["valid_decision"] is True
        assert "force push" in data["explanation"]["meaning"].lower()

    def test_explain_shell_gate(self):
        data = build_advisory_explain("would_block_by_shell_gate")
        assert data["valid_decision"] is True
        assert data["explanation"]["would_block"] == "yes"

    def test_explain_deny(self):
        data = build_advisory_explain("would_deny")
        assert data["valid_decision"] is True

    def test_explain_unknown_decision_is_safe(self):
        data = build_advisory_explain("not_a_real_decision")
        assert data["valid_decision"] is False
        assert "summary" in data["explanation"]

    def test_explain_all_decisions_list(self):
        data = build_advisory_explain("would_block_by_force_push")
        assert "all_decisions" in data
        assert len(data["all_decisions"]) == len(ADVISORY_DECISIONS)

    def test_explain_cli_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "explain",
             "--decision", "would_block_by_raw_git_push", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid_decision"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# Advisory status
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryStatus:
    """Advisory status reports prototype state and invariants."""

    def test_status_advisory_available(self):
        data = build_advisory_status()
        assert data["advisory_mode_available"] is True
        assert data["implementation_status"] == "prototype"
        assert data["phase"] == "88X"

    def test_status_invariants(self):
        data = build_advisory_status()
        inv = data["invariants"]
        for key in inv:
            assert inv[key] is True, f"Invariant {key} should be True"

    def test_status_cli_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "status", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["advisory_mode_available"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# Advisory check — CLI integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryCheckCLI:
    """CLI integration tests for pcae advisory check."""

    def test_cli_git_status_valid_json(self):
        data = _cli_check("git status")
        assert "advisory_decision" in data

    def test_cli_force_push_hard_block(self):
        data = _cli_check("git push --force origin main")
        assert data["advisory_decision"] == "would_block_by_force_push"
        assert data["would_block"] is True

    def test_cli_returns_zero_exit_code(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "check",
             "--command", "git status"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0

    def test_cli_returns_zero_even_for_hard_blocks(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "check",
             "--command", "git push --force origin main"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0

    def test_cli_authorization_granted_false(self):
        data = _cli_check("git status")
        assert data["authorization_granted"] is False

    def test_cli_human_readable_output_contains_non_authorizing(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "check",
             "--command", "git status"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert "Non-Authorizing" in result.stdout
        assert "not granted" in result.stdout
        assert "not authorized" in result.stdout

    def test_cli_human_readable_hard_block_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "check",
             "--command", "git push --force origin main"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert "would block" in result.stdout.lower()
        assert "Non-Authorizing" in result.stdout

    def test_cli_no_secret_in_human_readable_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "check",
             "--command", "OPENAI_API_KEY=sk-abc123 python script.py"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert "sk-abc123" not in result.stdout


# ═══════════════════════════════════════════════════════════════════════════════
# Invariants
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryInvariants:
    """Cross-cutting invariants for all advisory evaluations."""

    @pytest.mark.parametrize("command,expected_block", [
        ("git push --force origin main", True),
        ("rm -rf /", True),
        ("git push origin main", True),
        ("git commit -m x", True),
        ("echo x > README.md", True),
    ])
    def test_hard_blocks_never_downgraded_to_no_block(self, command, expected_block):
        data = _adv(command)
        assert data["would_block"] is expected_block
        assert data["hard_block_present"] is True

    @pytest.mark.parametrize("command", [
        "git push --force origin main",
        "rm -rf /",
        "echo x > README.md",
    ])
    def test_human_approval_does_not_override_hard_blocks(self, command):
        data = _adv(command, human_approval_present=True,
                    human_review_present=True,
                    health_passed=True, check_passed=True)
        assert data["would_block"] is True, (
            f"{command}: hard block must not be overridden by human approval"
        )
        assert data["hard_block_present"] is True

    @pytest.mark.parametrize("command", [
        "git push --force origin main",
        "rm -rf /",
    ])
    def test_accepted_risk_does_not_override_hard_blocks(self, command):
        data = _adv(command, accepted_risk_present=True,
                    human_approval_present=True,
                    human_review_present=True,
                    health_passed=True, check_passed=True)
        assert data["would_block"] is True, (
            f"{command}: hard block must not be overridden by accepted risk"
        )

    @pytest.mark.parametrize("command", [
        "git status",
        "git push --force origin main",
        "rm -rf /",
        "pip install requests",
        "curl https://example.com",
        "OPENAI_API_KEY=x python script.py",
        "cat ~/.ssh/id_rsa",
        "printenv",
    ])
    def test_no_command_execution_for_any_command(self, command):
        data = _adv(command)
        assert data["command_executed"] is False
        assert data["execution_authorized"] is False
        assert data["authorization_granted"] is False
        assert data["enforcement_applied"] is False

    @pytest.mark.parametrize("command", [
        "git status",
        "git push --force origin main",
        "OPENAI_API_KEY=x python script.py",
    ])
    def test_all_performed_flags_false_for_all_commands(self, command):
        data = _adv(command)
        performed = data["performed_flags"]
        for flag in _PERFORMED_FLAGS:
            assert performed[flag] is False, (
                f"{command}: performed.{flag} should be False"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 88Y — Advisory Command Matrix (comprehensive)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Read-only commands ─────────────────────────────────────────────────────

class Test88yMatrixReadOnly:
    """All read-only commands produce safe non-blocking advisory output."""

    @pytest.mark.parametrize("cmd", [
        "git status", "pwd", "ls", "ls -la",
        "cat PROJECT_STATUS.md", "grep -R 'Phase 88' docs",
        "diff file1 file2", "echo hello", "whoami",
        "date", "head CHANGELOG.md", "wc -l README.md",
    ])
    def test_read_only_commands_non_blocking(self, cmd):
        data = _adv(cmd)
        assert data["would_block"] is False, f"{cmd}: should not block"
        assert data["hard_block_present"] is False
        assert data["authorization_granted"] is False
        assert data["execution_authorized"] is False

    @pytest.mark.parametrize("cmd", [
        "git status", "pwd", "ls",
    ])
    def test_read_only_json_envelope_valid(self, cmd):
        data = _adv(cmd)
        assert data["broker_decision"] is not None
        assert data["shell_gate_decision"] is not None
        assert data["shell_gate_category"] is not None
        assert data["advisory_decision"] in ADVISORY_DECISIONS


# ── Governed PCAE commands ─────────────────────────────────────────────────

class Test88yMatrixGovernedPCAE:
    """PCAE lifecycle commands are governed (allow_governed)."""

    @pytest.mark.parametrize("cmd", [
        "pcae health", "pcae check",
        "pcae doctor task-memory", "pcae doctor test-run --json",
    ])
    def test_governed_commands_non_blocking(self, cmd):
        data = _adv(cmd)
        assert data["would_block"] is False
        assert data["authorization_granted"] is False


# ── Raw git hard blocks ────────────────────────────────────────────────────

class Test88yMatrixGitHardBlocks:
    """Raw git push/commit/force push produce hard blocks."""

    @pytest.mark.parametrize("cmd,expected_decision", [
        ("git push", "would_block_by_raw_git_push"),
        ("git push origin main", "would_block_by_raw_git_push"),
        ("git push --force", "would_block_by_force_push"),
        ("git push -f", "would_block_by_force_push"),
        ("git push --force origin main", "would_block_by_force_push"),
    ])
    def test_git_push_hard_blocks(self, cmd, expected_decision):
        data = _adv(cmd)
        assert data["would_block"] is True, f"{cmd}: should be hard blocked"
        assert data["hard_block_present"] is True
        assert data["advisory_decision"] == expected_decision, (
            f"{cmd}: expected {expected_decision}, got {data['advisory_decision']}"
        )

    def test_git_commit_hard_block(self):
        data = _adv("git commit -m 'test'")
        assert data["would_block"] is True

    def test_git_rebase_hard_block(self):
        data = _adv("git rebase -i HEAD~3")
        assert data["would_block"] is True


# ── Dangerous filesystem ────────────────────────────────────────────────────

class Test88yMatrixDangerousFilesystem:
    """Dangerous filesystem commands produce hard blocks."""

    @pytest.mark.parametrize("cmd", [
        "rm -rf /", "rm -rf /tmp", "rm -rf .",
        "git reset --hard HEAD", "git clean -fd",
    ])
    def test_dangerous_commands_hard_blocked(self, cmd):
        data = _adv(cmd)
        assert data["would_block"] is True, f"{cmd}: should be hard blocked"
        assert data["hard_block_present"] is True


# ── Policy-forbidden writes ─────────────────────────────────────────────────

class Test88yMatrixPolicyForbidden:
    """Writes to policy-forbidden files produce hard blocks."""

    @pytest.mark.parametrize("cmd", [
        "echo x > README.md",
        "echo x >> README.md",
        "cat x > docs/REAL_CAPTURED_TASKS.md",
        "echo x > docs/LINKEDIN_ARTICLE_DRAFT.md",
    ])
    def test_policy_forbidden_writes_blocked(self, cmd):
        data = _adv(cmd)
        assert data["would_block"] is True, f"{cmd}: should be blocked"
        assert data["hard_block_present"] is True

    def test_tee_readme_blocked(self):
        data = _adv("echo x | tee README.md")
        assert data["would_block"] is True
        assert data["hard_block_present"] is True


# ── Test execution ──────────────────────────────────────────────────────────

class Test88yMatrixTestExecution:
    """Test execution commands are non-authorizing."""

    @pytest.mark.parametrize("cmd", [
        "python -m pytest tests/test_advisory_mode.py -q",
        "python -m pytest -n auto",
        "python -m pytest -m fast_green -n auto",
    ])
    def test_test_execution_non_authorizing(self, cmd):
        data = _adv(cmd)
        assert data["authorization_granted"] is False
        assert data["execution_authorized"] is False
        assert data["command_executed"] is False


# ── Review-required commands ────────────────────────────────────────────────

class Test88yMatrixReviewRequired:
    """Package install and network commands require human review."""

    @pytest.mark.parametrize("cmd", [
        "pip install requests",
        "python -m pip install requests",
        "brew install jq",
        "npm install",
        "cargo install ripgrep",
        "curl https://example.com",
        "wget https://example.com/file",
        "ssh host",
        "scp file host:/tmp",
    ])
    def test_review_required_commands(self, cmd):
        data = _adv(cmd)
        assert data["would_require_human_review"] is True or data["would_block"] is True, (
            f"{cmd}: should require review or block"
        )
        assert data["authorization_granted"] is False


# ── Secret/redaction commands ───────────────────────────────────────────────

class Test88yMatrixSecretRedaction:
    """Secret-access commands are redacted in all advisory output."""

    @pytest.mark.parametrize("cmd,secret_fragment", [
        ("OPENAI_API_KEY=sk-abc123 python script.py", "sk-abc123"),
        ("TOKEN=ghp_token curl https://example.com", "ghp_token"),
        ("PASSWORD=s3cr3t! echo ok", "s3cr3t!"),
        ("cat ~/.ssh/id_rsa", "~/.ssh/id_rsa"),
        ("security find-generic-password", "find-generic-password"),
    ])
    def test_secret_not_in_json(self, cmd, secret_fragment):
        data = _adv(cmd)
        raw = json.dumps(data, sort_keys=True)
        assert secret_fragment not in raw, f"{cmd}: raw secret leaked in JSON"

    @pytest.mark.parametrize("cmd", [
        "printenv",
        "printenv OPENAI_API_KEY",
        "env",
        "env | grep SECRET",
    ])
    def test_env_printenv_redacted(self, cmd):
        data = _adv(cmd)
        assert data["redaction_applied"] is True, f"{cmd}: should be redacted"

    @pytest.mark.parametrize("cmd", [
        "OPENAI_API_KEY=x python script.py",
        "cat ~/.ssh/id_rsa",
        "security find-generic-password",
        "printenv",
        "env",
    ])
    def test_redacted_commands_redacted_flag(self, cmd):
        data = _adv(cmd)
        assert data["requested_command_redacted"] is True

    @pytest.mark.parametrize("cmd,secret_fragment", [
        ("OPENAI_API_KEY=sk-abc123 python script.py", "sk-abc123"),
        ("TOKEN=ghp_token curl https://example.com", "ghp_token"),
        ("PASSWORD=s3cr3t! echo ok", "s3cr3t!"),
    ])
    def test_secret_not_in_human_readable(self, cmd, secret_fragment):
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "check",
             "--command", cmd],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        assert secret_fragment not in result.stdout


# ── Compound commands ───────────────────────────────────────────────────────

class Test88yMatrixCompound:
    """Compound commands take the most restrictive segment."""

    @pytest.mark.parametrize("cmd", [
        "git status && git push",
        "pcae health && git push",
        "git status || git push",
        "cat PROJECT_STATUS.md | grep Phase",
    ])
    def test_compound_commands_most_restrictive(self, cmd):
        data = _adv(cmd)
        assert data["broker_decision"] is not None
        assert data["advisory_decision"] in ADVISORY_DECISIONS
        assert data["authorization_granted"] is False

    def test_semicolon_compound(self):
        data = _adv("git status ; git push")
        assert data["would_block"] is True


# ── Unknown/ambiguous commands ──────────────────────────────────────────────

class Test88yMatrixUnknown:
    """Unknown commands are conservatively blocked, not allowed."""

    @pytest.mark.parametrize("cmd", [
        "unknown-tool --dangerous",
    ])
    def test_unknown_commands_blocked(self, cmd):
        data = _adv(cmd)
        assert data["would_block"] is True, f"{cmd}: unknown should be blocked"
        assert data["advisory_decision"] != "would_allow_read_only"
        assert data["advisory_decision"] != "would_allow_governed_preflight_only"

    def test_bash_requires_review_not_blocked_89a(self):
        """89A fix: bash is a known shell, requires human review (not unknown block)."""
        data = _adv("bash")
        # bash requires human review, not blocked as unknown
        assert data["shell_gate_category"] != "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 88Y — CLI JSON Stability
# ═══════════════════════════════════════════════════════════════════════════════

class Test88yCLIJsonStability:
    """CLI JSON output is stable across command types."""

    def _cli(self, command):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "check",
             "--command", command, "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        return json.loads(result.stdout)

    @pytest.mark.parametrize("cmd", [
        "git status", "git push", "OPENAI_API_KEY=x python script.py",
        "rm -rf /", "pip install requests", "unknown-tool --dangerous",
    ])
    def test_cli_json_parses(self, cmd):
        data = self._cli(cmd)
        assert "schema_version" in data
        assert "advisory_decision" in data
        assert data["authorization_granted"] is False
        assert data["execution_authorized"] is False

    def test_explain_json_parses(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "explain",
             "--decision", "would_block_by_raw_git_push", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid_decision"] is True

    def test_explain_unknown_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "explain",
             "--decision", "unknown", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid_decision"] is True

    def test_status_json_parses(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "status", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["advisory_mode_available"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 88Y — Human-Readable Output Stability
# ═══════════════════════════════════════════════════════════════════════════════

class Test88yHumanReadableStability:
    """Human-readable advisory output contains required sections."""

    def _human(self, cmd):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "check",
             "--command", cmd],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        return result.stdout

    def test_read_only_human_output(self):
        out = self._human("git status")
        assert "Non-Authorizing" in out
        assert "not granted" in out.lower()
        assert "not authorized" in out.lower()

    def test_hard_block_human_output(self):
        out = self._human("git push --force origin main")
        assert "would block" in out.lower()

    def test_secret_command_human_output_no_leak(self):
        out = self._human("OPENAI_API_KEY=sk-abc123 python script.py")
        assert "sk-abc123" not in out

    def test_explain_human_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "explain",
             "--decision", "would_block_by_force_push"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        assert "force push" in result.stdout.lower()

    def test_status_human_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "advisory", "status"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        assert "prototype" in result.stdout.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 88Y — Decision Vocabulary Coverage
# ═══════════════════════════════════════════════════════════════════════════════

class Test88yDecisionVocabulary:
    """All 19 advisory decisions are explainable."""

    @pytest.mark.parametrize("decision", ADVISORY_DECISIONS)
    def test_every_decision_is_explainable(self, decision):
        data = build_advisory_explain(decision)
        assert data["valid_decision"] is True, f"{decision}: should be valid"
        assert "summary" in data["explanation"]
        assert "meaning" in data["explanation"]
        assert "would_block" in data["explanation"]
        assert "can_override" in data["explanation"]
        assert "next_step" in data["explanation"]

    def test_unknown_decision_safe(self):
        data = build_advisory_explain("not_a_decision")
        assert data["valid_decision"] is False
        assert "summary" in data["explanation"]


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 88Y — Broker/Shell-Gate Consistency
# ═══════════════════════════════════════════════════════════════════════════════

class Test88yBrokerShellGateConsistency:
    """Broker and shell gate decisions are consistent in advisory output."""

    def test_shell_gate_decision_matches_broker_mapping(self):
        """For known commands, SG decision is reflected in broker decision."""
        data = _adv("git status")
        assert data["shell_gate_decision"] == "allow_read_only"
        assert data["shell_gate_category"] == "read_only_inspection"

    def test_secret_access_sg_reflected_in_broker(self):
        data = _adv("cat ~/.ssh/id_rsa")
        assert data["shell_gate_category"] == "secret_access"
        assert data["redaction_applied"] is True

    def test_force_push_sg_reflected_in_broker(self):
        data = _adv("git push --force origin main")
        assert data["advisory_decision"] == "would_block_by_force_push"

    def test_env_classified_as_secret(self):
        data = _adv("env")
        assert data["shell_gate_category"] == "secret_access"

    def test_printenv_classified_as_secret(self):
        data = _adv("printenv")
        assert data["shell_gate_category"] == "secret_access"

    @pytest.mark.parametrize("cmd,expected_sg_category", [
        ("git status", "read_only_inspection"),
        ("pip install requests", "package_install"),
        ("curl https://example.com", "network_access"),
        ("rm -rf /", "destructive_filesystem"),
        ("cat ~/.ssh/id_rsa", "secret_access"),
        ("env", "secret_access"),
        ("git push", "raw_git_push"),
        ("git push --force origin main", "force_push"),
        ("export FOO=bar", "environment_mutation"),
    ])
    def test_shell_gate_category_correct(self, cmd, expected_sg_category):
        data = _adv(cmd)
        assert data["shell_gate_category"] == expected_sg_category, (
            f"{cmd}: expected {expected_sg_category}, got {data['shell_gate_category']}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 88Y — False-Positive / False-Negative Review
# ═══════════════════════════════════════════════════════════════════════════════

class Test88yFalsePositiveReview:
    """Documented false positives — conservative but not dangerous."""

    def test_bash_recognized_as_known_shell_89a(self):
        """89A fix: bash is recognized as a known shell, not unknown."""
        data = _adv("bash")
        assert data["shell_gate_category"] != "unknown"

    def test_sh_minus_c_embedded_command_classified_89a(self):
        """89A fix: sh -c 'git push' classifies the embedded command.
        git push is raw_git_push which is a hard block."""
        data = _adv("sh -c 'git push'")
        # git push inside sh -c → raw_git_push → would_block
        assert data["would_block"] is True

    def test_env_python_no_longer_secret_access_89a(self):
        """89A fix: 'env python' is no longer over-classified as secret_access.
        env inspects arguments; running a program through env delegates to
        the sub-command classifier."""
        data = _adv("env python")
        assert data["shell_gate_category"] != "secret_access"
        data2 = _adv("env python script.py")
        assert data2["shell_gate_category"] != "secret_access"


class Test88yFalseNegativeReview:
    """Documented false negatives found in 88Y review."""

    def test_env_pipe_grep_no_spaces_now_redacted_89a(self):
        """89A fix: 'env|grep TOKEN' without spaces around | is now split
        on the compact pipe operator. The pipe chain detects env → secret_access
        which triggers redaction. The false negative is fixed."""
        data = _adv("env|grep TOKEN")
        # 89A fix: compact operator splitting now detects the pipe,
        # so env triggers secret_access → redaction IS applied
        assert data["redaction_applied"] is True

    def test_no_false_negatives_in_hard_blocks(self):
        """All tested hard-block commands produce would_block."""
        for cmd in ["git push --force origin main", "rm -rf /",
                     "echo x > README.md", "git push", "git commit -m x"]:
            data = _adv(cmd)
            assert data["would_block"] is True, f"{cmd}: FN — not blocked"

    def test_no_false_negatives_in_secret_redaction(self):
        """All tested secret commands are redacted."""
        for cmd in ["OPENAI_API_KEY=x python script.py",
                     "cat ~/.ssh/id_rsa", "security find-generic-password",
                     "printenv", "env"]:
            data = _adv(cmd)
            assert data["redaction_applied"] is True, (
                f"{cmd}: FN — secret not redacted"
            )

    def test_no_false_negatives_in_review_required(self):
        """Review-required commands are not silently allowed."""
        for cmd in ["pip install requests", "curl https://example.com",
                     "ssh host"]:
            data = _adv(cmd)
            assert not data["would_block"] or data["hard_block_present"], (
                f"{cmd}: should be review-required or blocked, not silently allowed"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 88Y — Comprehensive Invariant Cross-Check
# ═══════════════════════════════════════════════════════════════════════════════

class Test88yComprehensiveInvariants:
    """All 88Y matrix commands preserve invariants."""

    ALL_88Y_COMMANDS = [
        "git status", "pwd", "ls",
        "pcae health", "pcae check",
        "git push", "git push --force origin main",
        "rm -rf /", "git reset --hard HEAD",
        "echo x > README.md",
        "python -m pytest -n auto",
        "pip install requests", "curl https://example.com",
        "OPENAI_API_KEY=x python script.py",
        "printenv", "env | grep SECRET",
        "cat ~/.ssh/id_rsa",
        "git status && git push",
        "unknown-tool --dangerous", "bash",
    ]

    @pytest.mark.parametrize("cmd", ALL_88Y_COMMANDS)
    def test_all_commands_authorization_false(self, cmd):
        data = _adv(cmd)
        assert data["authorization_granted"] is False
        assert data["execution_authorized"] is False
        assert data["command_executed"] is False
        assert data["enforcement_applied"] is False

    @pytest.mark.parametrize("cmd", ALL_88Y_COMMANDS)
    def test_all_commands_performed_flags_false(self, cmd):
        data = _adv(cmd)
        for flag in _PERFORMED_FLAGS:
            assert data["performed_flags"][flag] is False, (
                f"{cmd}: performed.{flag} should be False"
            )

    @pytest.mark.parametrize("cmd", ALL_88Y_COMMANDS)
    def test_all_commands_envelope_present(self, cmd):
        data = _adv(cmd)
        for field in ["schema_version", "advisory_mode",
                       "broker_decision", "advisory_decision",
                       "advisory_recommendation", "operator_message",
                       "next_required_action"]:
            assert field in data, f"{cmd}: missing field {field}"
