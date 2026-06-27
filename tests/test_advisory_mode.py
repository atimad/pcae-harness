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
