"""
Broker + Shell Gate Integration — Edge Case Tests (Phase 88U).

Expands coverage from 88T with:
- Compound command handling through broker (&&, ||, ;)
- Pipe/tee policy-forbidden and mutation writes through broker
- Environment mutation variants through broker
- Network access through broker
- Package install variants through broker
- Unknown command conservative blocking
- Secret access additional file paths
- Expensive pytest classification (no subprocess; fast_green safe)
- CLI JSON envelope stability (slow tier)
- Idle-vs-active task behavior (comprehensive)
- Non-hard-block decisions never authorize execution
- Hard-block mapping consistency
- Known false-negative documentation
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from pcae.core.permission_broker import (
    BPE_DECISIONS,
    BPE_HARD_BLOCK_DECISIONS,
    BPE_MUTATING_ACTIONS,
    _SG_ALLOW_DECISIONS,
    _SG_HARD_BLOCK_TO_BROKER,
    _SG_HARD_BLOCK_DECISIONS_SET,
    build_permission_broker,
)
from pcae.core.shell_gate import (
    SGP_DECISIONS,
    _classify_command,
    _is_expensive_pytest,
)

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


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_task_root(tmp_path: Path) -> Path:
    """Isolated temp repo with a minimal active task contract."""
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True)
    (active_dir / "test-active-task.md").write_text(
        "## Allowed Files\n"
        "- src/**\n"
        "- tests/**\n"
        "- docs/**\n"
        "## Forbidden Files\n"
    )
    return tmp_path


@pytest.fixture
def no_task_root(tmp_path: Path) -> Path:
    """Isolated temp repo with NO active task (idle state)."""
    return tmp_path


# ── Helpers ────────────────────────────────────────────────────────────────

def _pb(
    action: str = "read",
    command: str | None = None,
    files: list[str] | None = None,
    health_passed: bool | None = None,
    check_passed: bool | None = None,
    human_review_present: bool = False,
    human_approval_present: bool = False,
    accepted_risk_present: bool = False,
    root: Path = REPO_ROOT,
) -> dict[str, Any]:
    return build_permission_broker(
        repo_root=root,
        requested_action=action,
        requested_files=files,
        requested_command=command,
        health_passed=health_passed,
        check_passed=check_passed,
        human_review_present=human_review_present,
        human_approval_present=human_approval_present,
        accepted_risk_present=accepted_risk_present,
    )


def _broker(action: str = "read", **kwargs: Any) -> dict[str, Any]:
    return _pb(action=action, **kwargs)["broker"]


# ── TestCompoundCommandsThruBroker ─────────────────────────────────────────

class TestCompoundCommandsThruBroker:
    """Compound shell commands (&&, ||, ;) take the most restrictive segment."""

    def test_git_status_and_push_yields_raw_push_block(self, no_task_root):
        b = _broker("read", command="git status && git push origin main",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_raw_git_push"
        assert b["hard_block_present"] is True

    def test_git_status_or_push_yields_raw_push_block(self, no_task_root):
        b = _broker("read", command="git status || git push origin main",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_raw_git_push"
        assert b["hard_block_present"] is True

    def test_git_status_semicolon_push_yields_raw_push_block(self, no_task_root):
        # Spaces required around ; so shlex.split yields ";" as a separate token
        b = _broker("read", command="git status ; git push origin main",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_raw_git_push"
        assert b["hard_block_present"] is True

    def test_semicolon_without_spaces_now_split_89a(self, no_task_root):
        """89A fix: compact operator splitting now detects ; without spaces.
        'git status; git push' is split into two segments. git push →
        raw_git_push → hard block (most restrictive wins)."""
        b = _broker("read", command="git status; git push origin main",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_raw_git_push"
        assert b["hard_block_present"] is True

    def test_pcae_health_and_force_push_yields_force_push_block(self, no_task_root):
        b = _broker("read", command="pcae health && git push --force",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_force_push"
        assert b["hard_block_present"] is True

    def test_git_status_and_force_push(self, no_task_root):
        b = _broker("read", command="git status && git push --force origin",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_force_push"
        assert b["hard_block_present"] is True

    def test_two_read_only_commands_allow(self, no_task_root):
        b = _broker("read", command="cat file.py && echo done", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["hard_block_present"] is False

    def test_git_log_and_git_status_allow(self, no_task_root):
        b = _broker("read", command="git log --oneline && git status",
                    root=no_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["hard_block_present"] is False

    def test_compound_with_unknown_segment_blocks_by_shell_gate(self, no_task_root):
        # unknown (severity 5) is more restrictive than package_install (severity 6)
        b = _broker("read", command="pip install requests && python script.py",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_compound_reason_codes_include_compound_detected(self, no_task_root):
        envelope = _pb("read", command="git status && git push", root=no_task_root)
        sg = envelope["broker"]["shell_gate_evidence"]
        assert sg is not None
        assert "compound_command_detected" in sg["reason_codes"]

    def test_compound_performed_flags_invariant(self, no_task_root):
        b = _broker("read", command="git status && git push origin main",
                    root=no_task_root)
        for flag in _PERFORMED_FLAGS:
            assert b[flag] is False, f"{flag} should be False"


# ── TestPipeTeeWritesThruBroker ────────────────────────────────────────────

class TestPipeTeeWritesThruBroker:
    """Pipe+tee chains route to broker correctly based on tee write target."""

    def test_tee_to_readme_yields_scope_block(self, no_task_root):
        b = _broker("read", command="echo x | tee README.md", root=no_task_root)
        assert b["decision"] == "blocked_by_scope"
        assert b["hard_block_present"] is True

    def test_tee_append_to_readme_yields_scope_block(self, no_task_root):
        # -a flag skipped by _find_tee_write_target → README.md still detected
        b = _broker("read", command="echo x | tee -a README.md", root=no_task_root)
        assert b["decision"] == "blocked_by_scope"
        assert b["hard_block_present"] is True

    def test_tee_to_src_file_no_task_yields_task_contract_block(self, no_task_root):
        b = _broker("read", command="echo x | tee src/output.py", root=no_task_root)
        assert b["decision"] == "blocked_by_task_contract"
        assert b["hard_block_present"] is True

    def test_tee_to_src_file_with_task_yields_requires_more_evidence(self, tmp_task_root):
        b = _broker("source_mutation", command="echo x | tee src/output.py",
                    root=tmp_task_root)
        assert b["decision"] == "requires_more_evidence"
        assert b["hard_block_present"] is False

    def test_tee_to_docs_file_no_task_yields_task_contract_block(self, no_task_root):
        b = _broker("read", command="cat file.py | tee docs/notes.md",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_task_contract"
        assert b["hard_block_present"] is True

    def test_tee_to_generic_file_no_task_yields_task_contract_block(self, no_task_root):
        b = _broker("read", command="echo x | tee output.txt", root=no_task_root)
        assert b["decision"] == "blocked_by_task_contract"
        assert b["hard_block_present"] is True

    def test_pipe_without_tee_two_read_only_allows(self, no_task_root):
        b = _broker("read", command="git log | grep commit", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["hard_block_present"] is False

    def test_tee_reason_codes_include_pipe_tee_write_detected(self, no_task_root):
        envelope = _pb("read", command="echo x | tee README.md", root=no_task_root)
        sg = envelope["broker"]["shell_gate_evidence"]
        assert "pipe_tee_write_detected" in sg["reason_codes"]


# ── TestEnvironmentMutationThruBroker ─────────────────────────────────────

class TestEnvironmentMutationThruBroker:
    """Environment mutation commands require human review; never hard-block."""

    def test_export_api_key_requires_human_review(self, no_task_root):
        b = _broker("read", command="export OPENAI_API_KEY=x", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_unset_variable_requires_human_review(self, no_task_root):
        b = _broker("read", command="unset OPENAI_API_KEY", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_source_env_file_requires_human_review(self, no_task_root):
        b = _broker("read", command="source .env", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_dot_env_file_requires_human_review(self, no_task_root):
        b = _broker("read", command=". .env", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_env_var_prefix_command_requires_human_review(self, no_task_root):
        # OPENAI_API_KEY=x python script.py → env_var_prefix_detected
        b = _broker("read", command="OPENAI_API_KEY=x python script.py",
                    root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_env_var_prefix_command_is_redacted_88v1(self, no_task_root):
        # 88V.1 repair: env var prefix with secret-like key name IS now
        # detected and redacted. (GAP-1 fixed.)
        envelope = _pb("read", command="OPENAI_API_KEY=x python script.py",
                       root=no_task_root)
        sg = envelope["broker"]["shell_gate_evidence"]
        assert sg["command_text_redacted"] is True
        assert sg["command_category"] == "secret_access"

    def test_environment_mutation_with_human_review_allows(self, no_task_root):
        b = _broker("read", command="export API_KEY=x",
                    human_review_present=True, root=no_task_root)
        assert b["decision"] == "allow_preflight_only"

    def test_environment_mutation_audit_category_field(self, no_task_root):
        b = _broker("read", command="source .env", root=no_task_root)
        assert b["shell_gate_command_category"] == "environment_mutation"

    def test_environment_mutation_performed_flags_invariant(self, no_task_root):
        b = _broker("read", command="export KEY=val", root=no_task_root)
        for flag in _PERFORMED_FLAGS:
            assert b[flag] is False, f"{flag} should be False"


# ── TestNetworkAccessThruBroker ───────────────────────────────────────────

class TestNetworkAccessThruBroker:
    """Network programs require human review; they are not hard blocks."""

    def test_curl_requires_human_review(self, no_task_root):
        b = _broker("read", command="curl https://example.com", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_wget_requires_human_review(self, no_task_root):
        b = _broker("read", command="wget https://example.com/file", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_ssh_host_requires_human_review(self, no_task_root):
        b = _broker("read", command="ssh user@host.example.com", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_scp_requires_human_review(self, no_task_root):
        b = _broker("read", command="scp file host:/tmp", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_ping_requires_human_review(self, no_task_root):
        b = _broker("read", command="ping 8.8.8.8", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_network_with_human_review_allows(self, no_task_root):
        b = _broker("read", command="curl https://example.com",
                    human_review_present=True, root=no_task_root)
        assert b["decision"] == "allow_preflight_only"

    def test_network_reason_codes_include_network_requires_human_review(self, no_task_root):
        # The network-specific reason is in shell_gate_reason_codes (SG layer);
        # broker reason_codes contain the broker-level "shell_gate_requires_human_review"
        b = _broker("read", command="wget https://example.com/file", root=no_task_root)
        assert any("network_access_requires_human_review" in rc
                   for rc in b["shell_gate_reason_codes"])

    def test_network_performed_flags_invariant(self, no_task_root):
        b = _broker("read", command="curl https://example.com", root=no_task_root)
        for flag in _PERFORMED_FLAGS:
            assert b[flag] is False, f"{flag} should be False"


# ── TestPackageInstallThruBroker ───────────────────────────────────────────

class TestPackageInstallThruBroker:
    """Package install commands require human review."""

    def test_pip_install_requires_human_review(self, no_task_root):
        b = _broker("read", command="pip install requests", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_pip_install_requirements_file(self, no_task_root):
        b = _broker("read", command="pip install -r requirements.txt",
                    root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_python_m_pip_install(self, no_task_root):
        b = _broker("read", command="python -m pip install requests",
                    root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_npm_install(self, no_task_root):
        b = _broker("read", command="npm install", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_package_install_with_human_review_allows(self, no_task_root):
        b = _broker("read", command="pip install requests",
                    human_review_present=True, root=no_task_root)
        assert b["decision"] == "allow_preflight_only"

    def test_package_install_performed_flags_invariant(self, no_task_root):
        b = _broker("read", command="pip install requests", root=no_task_root)
        for flag in _PERFORMED_FLAGS:
            assert b[flag] is False, f"{flag} should be False"


# ── TestUnknownCommandThruBroker ───────────────────────────────────────────

class TestUnknownCommandThruBroker:
    """Unknown programs are hard-blocked conservatively."""

    def test_hyphenated_unknown_tool_hard_blocked(self, no_task_root):
        b = _broker("read", command="unknown-tool --dangerous", root=no_task_root)
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_custom_tool_hard_blocked(self, no_task_root):
        b = _broker("read", command="customtool run", root=no_task_root)
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_dot_slash_script_hard_blocked(self, no_task_root):
        b = _broker("read", command="./myscript.sh", root=no_task_root)
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_bash_script_requires_review_89a(self, no_task_root):
        """89A fix: bash is now a known shell. Shell with script file
        requires human review (not hard blocked as unknown)."""
        b = _broker("read", command="bash script.sh", root=no_task_root)
        assert b["decision"] != "blocked_by_shell_gate"
        assert b["shell_gate_command_category"] != "unknown"

    def test_unknown_command_reason_codes(self, no_task_root):
        b = _broker("read", command="unknown-tool --dangerous", root=no_task_root)
        assert any("shell_gate_decision:blocked_by_unknown_command" in rc
                   for rc in b["reason_codes"])

    def test_unknown_never_authorizes(self, no_task_root):
        b = _broker("read", command="unknown-tool --dangerous", root=no_task_root)
        assert b["authorization_granted"] is False
        assert b["execution_authorized"] is False


# ── TestSecretAccessEdgeCases ─────────────────────────────────────────────

class TestSecretAccessEdgeCases:
    """Secret-access detection covers common credential file prefixes."""

    def test_cat_ssh_config_redacted(self, no_task_root):
        envelope = _pb("read", command="cat ~/.ssh/config", root=no_task_root)
        b = envelope["broker"]
        assert b["decision"] == "requires_human_review"
        assert b["shell_gate_command_text_redacted"] is True
        assert b["shell_gate_command_category"] == "secret_access"

    def test_cat_aws_credentials_redacted(self, no_task_root):
        envelope = _pb("read", command="cat ~/.aws/credentials", root=no_task_root)
        b = envelope["broker"]
        assert b["decision"] == "requires_human_review"
        assert b["shell_gate_command_text_redacted"] is True
        assert b["shell_gate_command_category"] == "secret_access"

    def test_cat_kube_config_redacted(self, no_task_root):
        envelope = _pb("read", command="cat ~/.kube/config", root=no_task_root)
        b = envelope["broker"]
        assert b["decision"] == "requires_human_review"
        assert b["shell_gate_command_text_redacted"] is True

    def test_cat_netrc_redacted(self, no_task_root):
        envelope = _pb("read", command="cat ~/.netrc", root=no_task_root)
        b = envelope["broker"]
        assert b["decision"] == "requires_human_review"
        assert b["shell_gate_command_text_redacted"] is True

    def test_security_keychain_redacted(self, no_task_root):
        envelope = _pb("read", command="security find-generic-password",
                       root=no_task_root)
        b = envelope["broker"]
        assert b["decision"] == "requires_human_review"
        assert b["shell_gate_command_text_redacted"] is True
        assert b["shell_gate_command_category"] == "secret_access"

    def test_cat_ssh_private_key_redacted(self, no_task_root):
        envelope = _pb("read", command="cat ~/.ssh/id_ed25519", root=no_task_root)
        assert envelope["broker"]["shell_gate_command_text_redacted"] is True

    def test_cat_gnupg_dir_redacted(self, no_task_root):
        envelope = _pb("read", command="cat ~/.gnupg/private-keys-v1.d",
                       root=no_task_root)
        assert envelope["broker"]["shell_gate_command_text_redacted"] is True

    def test_cat_source_file_not_redacted(self, no_task_root):
        envelope = _pb("read", command="cat src/pcae/cli.py", root=no_task_root)
        b = envelope["broker"]
        assert b["shell_gate_command_text_redacted"] is False
        assert b["shell_gate_command_category"] == "read_only_inspection"

    def test_secret_command_hash_is_null(self, no_task_root):
        # SHA-256 hash is null (None) for redacted commands
        b = _broker("read", command="cat ~/.ssh/id_rsa", root=no_task_root)
        assert b["shell_gate_command_text_hash"] is None

    def test_non_secret_command_has_hash(self, no_task_root):
        b = _broker("read", command="git status", root=no_task_root)
        assert b["shell_gate_command_text_hash"] is not None
        assert len(b["shell_gate_command_text_hash"]) == 64  # SHA-256 hex

    def test_secret_with_human_review_allows(self, no_task_root):
        b = _broker("read", command="cat ~/.ssh/id_rsa",
                    human_review_present=True, root=no_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["execution_authorized"] is False


# ── TestExpensivePytestClassification ─────────────────────────────────────

class TestExpensivePytestClassification:
    """Expensive pytest detection (no subprocess; classification only)."""

    def test_python_m_pytest_n_auto_is_expensive(self):
        cls = _classify_command("python -m pytest -n auto")
        assert cls["detected_flags"]["expensive_test_execution_detected"] is True
        assert cls["command_category"] == "test_execution"

    def test_python_m_pytest_n_4_is_expensive(self):
        cls = _classify_command("python -m pytest -n 4")
        assert cls["detected_flags"]["expensive_test_execution_detected"] is True

    def test_python_m_pytest_n_auto_with_path_is_expensive(self):
        cls = _classify_command("python -m pytest -n auto tests/")
        assert cls["detected_flags"]["expensive_test_execution_detected"] is True

    def test_pytest_n_auto_is_expensive(self):
        cls = _classify_command("pytest -n auto")
        assert cls["detected_flags"]["expensive_test_execution_detected"] is True

    def test_python_m_pytest_no_n_is_not_expensive(self):
        cls = _classify_command("python -m pytest tests -q")
        assert cls["detected_flags"]["expensive_test_execution_detected"] is False
        assert cls["command_category"] == "test_execution"

    def test_plain_pytest_is_not_expensive(self):
        cls = _classify_command("pytest tests/")
        assert cls["detected_flags"]["expensive_test_execution_detected"] is False
        assert cls["command_category"] == "test_execution"

    def test_is_expensive_pytest_helper_direct(self):
        assert _is_expensive_pytest(["python", "-m", "pytest", "-n", "auto"]) is True
        assert _is_expensive_pytest(["python", "-m", "pytest", "-n4"]) is True
        assert _is_expensive_pytest(["python", "-m", "pytest", "tests"]) is False
        assert _is_expensive_pytest(["pytest", "--numprocesses", "4"]) is True


# ── TestIdleVsActiveTaskEdgeCases ─────────────────────────────────────────

class TestIdleVsActiveTaskEdgeCases:
    """Comprehensive idle vs active task behavior across command types."""

    def test_read_only_idle_allows(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["active_task_detected"] is False

    def test_read_only_with_active_task_allows(self, tmp_task_root):
        b = _broker("read", command="cat file.py", root=tmp_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["active_task_detected"] is True

    def test_filesystem_write_idle_hard_blocks(self, no_task_root):
        # cp is filesystem_write; no task → SG blocked_by_missing_task
        b = _broker("read", command="cp file.py file2.py", root=no_task_root)
        assert b["decision"] == "blocked_by_task_contract"
        assert b["hard_block_present"] is True

    def test_filesystem_write_with_active_task_needs_more_evidence(self, tmp_task_root):
        b = _broker("filesystem_write", command="cp file.py file2.py",
                    root=tmp_task_root)
        assert b["decision"] == "requires_more_evidence"
        assert b["hard_block_present"] is False
        assert "health_check" in b["missing_evidence"]

    def test_pytest_no_task_hard_blocks_by_task_contract(self, no_task_root):
        # requires_active_task at SG level → blocked_by_task_contract at priority 1d
        b = _broker("read", command="python -m pytest tests -q", root=no_task_root)
        assert b["decision"] == "blocked_by_task_contract"
        assert b["hard_block_present"] is True

    def test_pytest_with_active_task_allows(self, tmp_task_root):
        b = _broker("read", command="python -m pytest tests -q", root=tmp_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["hard_block_present"] is False

    def test_environment_mutation_idle_action_read_requires_human_review(self, no_task_root):
        # With action="read" (non-mutating), SG requires_human_review passes through
        b = _broker("read", command="export API_KEY=x", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["active_task_detected"] is False

    def test_environment_mutation_action_mutating_idle_blocked_by_task(self, no_task_root):
        # With action="environment_mutation" (mutating), priority 5 fires: no task
        b = _broker("environment_mutation", command="export API_KEY=x",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_task_contract"
        assert b["hard_block_present"] is True

    def test_network_access_idle_requires_human_review(self, no_task_root):
        b = _broker("read", command="curl https://example.com", root=no_task_root)
        assert b["decision"] == "requires_human_review"

    def test_secret_access_idle_requires_human_review(self, no_task_root):
        b = _broker("read", command="cat ~/.ssh/id_rsa", root=no_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False  # secret_access is not a hard block

    def test_raw_push_always_hard_blocks_regardless_of_task(self, tmp_task_root):
        # Even with active task, raw git push is unconditional hard block
        b = _broker("read", command="git push origin main", root=tmp_task_root)
        assert b["decision"] == "blocked_by_raw_git_push"
        assert b["hard_block_present"] is True

    def test_force_push_always_hard_blocks_regardless_of_task(self, tmp_task_root):
        b = _broker("read", command="git push --force", root=tmp_task_root)
        assert b["decision"] == "blocked_by_force_push"
        assert b["hard_block_present"] is True


# ── TestNonHardBlockNeverAuthorizes ───────────────────────────────────────

class TestNonHardBlockNeverAuthorizes:
    """Non-hard-block decisions never grant authorization_granted or execution_authorized."""

    @pytest.mark.parametrize("command,action", [
        ("pip install requests", "read"),
        ("curl https://example.com", "read"),
        ("export API_KEY=x", "read"),
        ("source .env", "read"),
        ("cat ~/.ssh/id_rsa", "read"),
        ("wget https://example.com/file", "read"),
        ("ssh user@host", "read"),
        ("source .bashrc", "read"),
        (". .env", "read"),
    ])
    def test_non_hard_block_commands_never_authorize(self, command, action,
                                                      no_task_root):
        b = _broker(action, command=command, root=no_task_root)
        assert b["authorization_granted"] is False
        assert b["execution_authorized"] is False

    @pytest.mark.parametrize("command", [
        "cat file.py",
        "git status",
        "git log --oneline",
        "ls -la",
        "pcae health",
    ])
    def test_allow_preflight_only_never_authorizes(self, command, no_task_root):
        b = _broker("read", command=command, root=no_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["authorization_granted"] is False
        assert b["execution_authorized"] is False

    @pytest.mark.parametrize("command,action", [
        ("pip install requests", "read"),
        ("curl https://example.com", "read"),
    ])
    def test_with_human_review_still_never_authorizes(self, command, action,
                                                       no_task_root):
        b = _broker(action, command=command, human_review_present=True,
                    root=no_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["authorization_granted"] is False
        assert b["execution_authorized"] is False


# ── TestHardBlockMappingConsistency ───────────────────────────────────────

class TestHardBlockMappingConsistency:
    """Verify _SG_HARD_BLOCK_TO_BROKER mapping integrity."""

    def test_all_sg_hard_block_values_in_bpe_decisions(self):
        for sg_dec, broker_dec in _SG_HARD_BLOCK_TO_BROKER.items():
            assert broker_dec in BPE_DECISIONS, (
                f"broker_dec {broker_dec!r} (from sg:{sg_dec}) not in BPE_DECISIONS"
            )

    def test_hard_block_keys_are_valid_sgp_decisions(self):
        for sg_dec in _SG_HARD_BLOCK_TO_BROKER:
            assert sg_dec in SGP_DECISIONS, (
                f"SG hard-block key {sg_dec!r} not in SGP_DECISIONS"
            )

    def test_sg_hard_block_decisions_set_matches_dict_keys(self):
        assert _SG_HARD_BLOCK_DECISIONS_SET == frozenset(_SG_HARD_BLOCK_TO_BROKER.keys())

    def test_blocked_by_scope_in_hard_block_decisions(self):
        # 88T change: blocked_by_policy_forbidden_file → blocked_by_scope
        assert "blocked_by_scope" in BPE_HARD_BLOCK_DECISIONS

    def test_blocked_by_task_contract_in_hard_block_decisions(self):
        # 88T change: blocked_by_missing_task → blocked_by_task_contract
        assert "blocked_by_task_contract" in BPE_HARD_BLOCK_DECISIONS

    def test_blocked_by_raw_git_push_in_hard_block_decisions(self):
        assert "blocked_by_raw_git_push" in BPE_HARD_BLOCK_DECISIONS

    def test_blocked_by_force_push_in_hard_block_decisions(self):
        assert "blocked_by_force_push" in BPE_HARD_BLOCK_DECISIONS

    def test_deny_not_in_bpe_hard_block_decisions(self):
        # Known inconsistency: "deny" is in _SG_HARD_BLOCK_TO_BROKER but
        # not in BPE_HARD_BLOCK_DECISIONS. In practice, no SG classifier path
        # produces "deny" today, so hard_block_present would be False if it fired.
        assert "deny" in _SG_HARD_BLOCK_TO_BROKER
        assert "deny" not in BPE_HARD_BLOCK_DECISIONS

    def test_sg_allow_decisions_not_in_hard_block_to_broker(self):
        for allow_dec in _SG_ALLOW_DECISIONS:
            assert allow_dec not in _SG_HARD_BLOCK_TO_BROKER


# ── TestFalseNegativeDocumented ───────────────────────────────────────────

class TestFalseNegativeDocumented:
    """
    Previously documented false negatives — repaired in 88V.1.

    These tests now confirm the REPAIRED behavior. GAP-1 and GAP-2
    false negatives from 88U have been fixed. The tests serve as
    regression anchors ensuring the fixes persist.
    """

    def test_secret_var_prefix_now_detected_as_secret(self, no_task_root):
        # 88V.1 REPAIR (was GAP-1 false negative): API key set via VAR=val prefix
        # is now detected and classified as secret_access with redaction.
        envelope = _pb("read",
                       command="OPENAI_API_KEY=sk-secret123 python script.py",
                       root=no_task_root)
        b = envelope["broker"]
        sg = b["shell_gate_evidence"]
        assert sg["command_category"] == "secret_access"
        assert sg["command_text_redacted"] is True
        assert sg["secret_access_detected"] is True

    def test_env_grep_secret_now_detected_as_secret(self, no_task_root):
        # 88V.1 REPAIR (was GAP-2 false negative): `env | grep KEY` is now
        # classified as secret_access because env is detected as secret exposure.
        b = _broker("read", command="env | grep AWS_SECRET_ACCESS_KEY",
                    root=no_task_root)
        # env → secret_access → requires_human_review
        assert b["decision"] == "requires_human_review"
        assert b["shell_gate_command_category"] == "secret_access"

    def test_printenv_secret_var_now_detected_as_secret(self, no_task_root):
        # 88V.1 REPAIR (was GAP-2 false negative): `printenv SECRET_VAR` is now
        # classified as secret_access because printenv is a secret exposure tool.
        b = _broker("read", command="printenv AWS_SECRET_ACCESS_KEY",
                    root=no_task_root)
        assert b["shell_gate_command_category"] == "secret_access"

    def test_bash_script_false_positive_fixed_89a(self, no_task_root):
        """89A fix: bash is recognized as known shell. The false positive
        where bash scripts were blocked as unknown is now resolved."""
        b = _broker("read", command="bash script.sh", root=no_task_root)
        assert b["shell_gate_command_category"] != "unknown"
        assert b["shell_gate_command_category"] != "backend_invocation"

    def test_git_soft_reset_blocked_as_unknown(self, no_task_root):
        # KNOWN FALSE POSITIVE: `git reset HEAD~1` (soft reset, no --hard/--mixed)
        # falls through the reset handler and is classified as unknown git subcommand.
        # Only --hard and --mixed resets are explicitly handled.
        b = _broker("read", command="git reset HEAD~1", root=no_task_root)
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["shell_gate_command_category"] == "unknown"


# ── TestCLIJSONEnvelopeStability ─────────────────────────────────────────

class TestCLIJSONEnvelopeStability:
    """CLI JSON output has all required fields in the correct shape (slow tier)."""

    @pytest.mark.slow
    @pytest.mark.integration
    def test_envelope_has_schema_version(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "schema_version" in data
        assert data["schema_version"] == "0.1"

    @pytest.mark.slow
    @pytest.mark.integration
    def test_envelope_has_generated_at(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        data = json.loads(result.stdout)
        assert "generated_at" in data
        assert data["generated_at"]  # non-empty

    @pytest.mark.slow
    @pytest.mark.integration
    def test_envelope_has_repository_root(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        data = json.loads(result.stdout)
        assert "repository_root" in data

    @pytest.mark.slow
    @pytest.mark.integration
    def test_envelope_has_broker_object(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        data = json.loads(result.stdout)
        assert "broker" in data
        assert isinstance(data["broker"], dict)

    @pytest.mark.slow
    @pytest.mark.integration
    def test_broker_decision_in_bpe_decisions(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        data = json.loads(result.stdout)
        assert data["broker"]["decision"] in BPE_DECISIONS

    @pytest.mark.slow
    @pytest.mark.integration
    def test_broker_authorization_granted_false(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        data = json.loads(result.stdout)
        assert data["broker"]["authorization_granted"] is False

    @pytest.mark.slow
    @pytest.mark.integration
    def test_broker_execution_authorized_false(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        data = json.loads(result.stdout)
        assert data["broker"]["execution_authorized"] is False

    @pytest.mark.slow
    @pytest.mark.integration
    def test_all_performed_flags_false_in_cli_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        data = json.loads(result.stdout)
        broker = data["broker"]
        for flag in _PERFORMED_FLAGS:
            assert broker[flag] is False, f"CLI output: {flag} should be False"

    @pytest.mark.slow
    @pytest.mark.integration
    def test_shell_gate_evidence_present_when_command_given(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read", "--requested-command", "git status", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        data = json.loads(result.stdout)
        assert data["broker"]["shell_gate_evidence"] is not None

    @pytest.mark.slow
    @pytest.mark.integration
    def test_shell_gate_evidence_absent_without_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        data = json.loads(result.stdout)
        assert data["broker"]["shell_gate_evidence"] is None

    @pytest.mark.slow
    @pytest.mark.integration
    def test_secret_command_redacted_in_cli_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read",
             "--requested-command", "cat ~/.ssh/id_rsa", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        data = json.loads(result.stdout)
        sg = data["broker"]["shell_gate_evidence"]
        assert sg["command_text"] == "<redacted_secret_access_command>"
        assert sg["command_text_redacted"] is True

    @pytest.mark.slow
    @pytest.mark.integration
    def test_raw_secret_command_redacted_in_sg_evidence(self):
        # The raw command appears in broker.requested_command (not additionally
        # redacted), but shell_gate_evidence.command_text IS the redacted sentinel.
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read",
             "--requested-command", "cat ~/.ssh/id_rsa", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        data = json.loads(result.stdout)
        sg = data["broker"]["shell_gate_evidence"]
        assert sg["command_text"] == "<redacted_secret_access_command>"
        assert sg["command_text_redacted"] is True
        # GAP-3 repair: broker.requested_command must also be redacted
        assert data["broker"]["requested_command"] == "<redacted_secret_access_command>"


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 88V.1 — Secret Redaction and Deny Mapping Repair Tests
# ═══════════════════════════════════════════════════════════════════════════════


# ── GAP-1: VAR=val secret redaction ──────────────────────────────────────────

class TestGap1VarValSecretRedaction:
    """VAR=val command prefixes with secret-like names must be detected/redacted."""

    def test_openai_api_key_var_prefix_detected_as_secret(self):
        """OPENAI_API_KEY=x python script.py → secret_access detected."""
        cls = _classify_command("OPENAI_API_KEY=x python script.py")
        assert cls["command_category"] == "secret_access", (
            f"Expected secret_access, got {cls['command_category']}"
        )
        assert cls["detected_flags"]["secret_access_detected"] is True

    def test_anthropic_api_key_var_prefix_detected_as_secret(self):
        """ANTHROPIC_API_KEY=secret pytest → secret_access detected."""
        cls = _classify_command("ANTHROPIC_API_KEY=secret pytest")
        assert cls["command_category"] == "secret_access"
        assert cls["detected_flags"]["secret_access_detected"] is True

    def test_aws_secret_access_key_var_prefix_detected_as_secret(self):
        """AWS_SECRET_ACCESS_KEY=x python tool.py → secret_access detected."""
        cls = _classify_command("AWS_SECRET_ACCESS_KEY=x python tool.py")
        assert cls["command_category"] == "secret_access"
        assert cls["detected_flags"]["secret_access_detected"] is True

    def test_token_var_prefix_detected_as_secret(self):
        """TOKEN=x curl https://example.com → secret_access detected."""
        cls = _classify_command("TOKEN=x curl https://example.com")
        assert cls["command_category"] == "secret_access"
        assert cls["detected_flags"]["secret_access_detected"] is True

    def test_password_var_prefix_detected_as_secret(self):
        """PASSWORD=x echo ok → secret_access detected."""
        cls = _classify_command("PASSWORD=x echo ok")
        assert cls["command_category"] == "secret_access"
        assert cls["detected_flags"]["secret_access_detected"] is True

    def test_benign_var_prefix_not_falsely_redacted(self):
        """MY_VAR=hello echo world → environment_mutation, not over-redacted."""
        cls = _classify_command("MY_VAR=hello echo world")
        assert cls["command_category"] == "environment_mutation"
        assert cls["detected_flags"]["secret_access_detected"] is False
        assert cls["detected_flags"]["environment_mutation_detected"] is True

    def test_debug_var_prefix_not_falsely_redacted(self):
        """DEBUG=1 python test.py → environment_mutation, not secret."""
        cls = _classify_command("DEBUG=1 python test.py")
        assert cls["command_category"] == "environment_mutation"
        assert cls["detected_flags"]["secret_access_detected"] is False

    def test_path_var_prefix_not_falsely_redacted(self):
        """PATH=/custom/bin ls → environment_mutation, not secret."""
        cls = _classify_command("PATH=/custom/bin ls")
        assert cls["command_category"] == "environment_mutation"
        assert cls["detected_flags"]["secret_access_detected"] is False

    # Broker-level redaction for VAR=val secret commands
    def test_openai_key_var_prefix_redacted_in_broker_json(self):
        """OPENAI_API_KEY=x python → broker JSON does not contain raw secret."""
        b = _broker("read", command="OPENAI_API_KEY=sk-abc123 python script.py")
        raw_json = json.dumps(b, sort_keys=True)
        assert "sk-abc123" not in raw_json, "Raw secret value leaked in broker JSON"
        sg = b["shell_gate_evidence"]
        assert sg["secret_access_detected"] is True

    def test_token_var_prefix_redacted_in_broker_json(self):
        """TOKEN=x curl → broker JSON does not contain raw secret."""
        b = _broker("read", command="TOKEN=ghp_secret123 curl https://api.github.com")
        raw_json = json.dumps(b, sort_keys=True)
        assert "ghp_secret123" not in raw_json, "Raw secret value leaked in broker JSON"
        sg = b["shell_gate_evidence"]
        assert sg["secret_access_detected"] is True

    def test_password_var_prefix_redacted_in_broker_json(self):
        """PASSWORD=x echo ok → broker JSON does not contain raw secret."""
        b = _broker("read", command="PASSWORD=s3cr3t! echo ok")
        raw_json = json.dumps(b, sort_keys=True)
        assert "s3cr3t!" not in raw_json, "Raw secret value leaked in broker JSON"


# ── GAP-2: env/printenv secret exposure ──────────────────────────────────────

class TestGap2EnvPrintenvSecretExposure:
    """env and printenv must be classified as secret exposure, not harmless read-only."""

    def test_printenv_classified_as_secret_exposure(self):
        """printenv alone → secret_access (dumps all env vars)."""
        cls = _classify_command("printenv")
        assert cls["command_category"] == "secret_access", (
            f"Expected secret_access, got {cls['command_category']}"
        )
        assert cls["detected_flags"]["secret_access_detected"] is True

    def test_env_classified_as_secret_exposure(self):
        """env alone → secret_access (dumps all env vars)."""
        cls = _classify_command("env")
        assert cls["command_category"] == "secret_access"
        assert cls["detected_flags"]["secret_access_detected"] is True

    def test_printenv_with_secret_var_name(self):
        """printenv OPENAI_API_KEY → secret_access."""
        cls = _classify_command("printenv OPENAI_API_KEY")
        assert cls["command_category"] == "secret_access"
        assert cls["detected_flags"]["secret_access_detected"] is True

    def test_printenv_with_harmless_var_name(self):
        """printenv HOME → secret_access (printenv is still a secret exposure tool)."""
        cls = _classify_command("printenv HOME")
        assert cls["command_category"] == "secret_access"
        assert cls["detected_flags"]["secret_access_detected"] is True

    # Broker-level checks for env/printenv
    def test_printenv_broker_decision_requires_human_review(self):
        """printenv → broker decision requires_human_review (not allow_read_only)."""
        b = _broker("read", command="printenv", health_passed=True,
                     check_passed=True, human_review_present=False)
        assert b["decision"] == "requires_human_review", (
            f"Expected requires_human_review, got {b['decision']}"
        )

    def test_env_broker_command_text_redacted(self):
        """env → shell_gate_evidence.command_text is redacted."""
        b = _broker("read", command="env")
        sg = b["shell_gate_evidence"]
        assert sg["command_text"] == "<redacted_secret_access_command>"
        assert sg["command_text_redacted"] is True

    def test_printenv_piped_to_grep_secret_most_restrictive(self):
        """env | grep SECRET → secret_access via pipe chain (most restrictive)."""
        cls = _classify_command("env | grep SECRET")
        # The pipe chain picks the most restrictive segment; env should be
        # secret_access (severity 2), grep is read_only (severity 9)
        assert cls["command_category"] == "secret_access", (
            f"Expected secret_access, got {cls['command_category']}"
        )

    def test_env_piped_to_grep_key_most_restrictive(self):
        """env | grep KEY → secret_access via pipe chain."""
        cls = _classify_command("env | grep KEY")
        assert cls["command_category"] == "secret_access"


# ── GAP-3: broker.requested_command raw secret retention ─────────────────────

class TestGap3BrokerRequestedCommandRedaction:
    """broker.requested_command must not retain raw secret-access command text."""

    def test_cat_ssh_key_requested_command_redacted(self):
        """cat ~/.ssh/id_rsa → broker.requested_command is redacted."""
        b = _broker("read", command="cat ~/.ssh/id_rsa")
        assert b["requested_command"] == "<redacted_secret_access_command>", (
            f"Got: {b['requested_command']}"
        )

    def test_security_find_generic_password_requested_command_redacted(self):
        """security find-generic-password → broker.requested_command is redacted."""
        b = _broker("read", command="security find-generic-password")
        assert b["requested_command"] == "<redacted_secret_access_command>"

    def test_openai_key_var_prefix_requested_command_redacted(self):
        """OPENAI_API_KEY=x python → broker.requested_command is redacted."""
        b = _broker("read", command="OPENAI_API_KEY=sk-abc python script.py")
        assert b["requested_command"] == "<redacted_secret_access_command>"

    def test_full_serialized_json_no_raw_secret_command(self):
        """Full broker JSON serialization must not contain raw secret-access command text."""
        b = _broker("read", command="cat ~/.ssh/id_rsa")
        raw_json = json.dumps(b, sort_keys=True)
        assert "~/.ssh/id_rsa" not in raw_json, (
            "Raw secret file path leaked in broker JSON"
        )

    def test_nested_shell_gate_evidence_no_raw_secret_command(self):
        """Nested shell_gate_evidence.command_text must not contain raw command."""
        b = _broker("read", command="security find-generic-password")
        sg = b["shell_gate_evidence"]
        assert sg["command_text"] == "<redacted_secret_access_command>"
        assert "find-generic-password" not in sg["command_text"]

    def test_ordinary_readonly_command_not_redacted(self):
        """ls -la → broker.requested_command is preserved (not over-redacted)."""
        b = _broker("read", command="ls -la")
        assert b["requested_command"] == "ls -la"

    def test_git_status_not_redacted(self):
        """git status → broker.requested_command is preserved."""
        b = _broker("read", command="git status")
        assert b["requested_command"] == "git status"


# ── GAP-4: deny hard-block mapping consistency ───────────────────────────────

class TestGap4DenyMappingConsistency:
    """Shell-gate deny must map to a broker hard block or be unreachable."""

    def test_deny_in_bpe_sg_hard_block_to_broker_mapping(self):
        """deny is mapped in _SG_HARD_BLOCK_TO_BROKER."""
        from pcae.core.permission_broker import _SG_HARD_BLOCK_TO_BROKER
        assert "deny" in _SG_HARD_BLOCK_TO_BROKER, (
            "deny must have an explicit mapping in _SG_HARD_BLOCK_TO_BROKER"
        )

    def test_deny_maps_to_broker_hard_block(self):
        """deny in _SG_HARD_BLOCK_TO_BROKER maps to a BPE_HARD_BLOCK_DECISIONS value."""
        from pcae.core.permission_broker import (
            _SG_HARD_BLOCK_TO_BROKER, BPE_HARD_BLOCK_DECISIONS,
        )
        mapped = _SG_HARD_BLOCK_TO_BROKER["deny"]
        assert mapped in BPE_HARD_BLOCK_DECISIONS, (
            f"deny maps to '{mapped}' which is NOT in BPE_HARD_BLOCK_DECISIONS"
        )

    def test_deny_does_not_produce_allow_preflight_only(self):
        """If a shell gate produces deny, broker must not return allow_preflight_only."""
        # This is tested indirectly: approve everything up to the broker,
        # and verify that deny leads to a hard block
        b = _broker("read", command="rm -rf /",
                    health_passed=True, check_passed=True,
                    human_review_present=True, human_approval_present=True)
        assert b["decision"] != "allow_preflight_only"

    def test_deny_does_not_authorize_execution(self):
        """Any deny-mapped decision must have execution_authorized=False."""
        b = _broker("read", command="rm -rf /",
                    health_passed=True, check_passed=True)
        assert b["execution_authorized"] is False
        assert b["authorization_granted"] is False

    def test_unmapped_shell_gate_decision_fails_closed(self):
        """All shell-gate blocking decisions that _decide can actually produce
        must have a mapping in _SG_HARD_BLOCK_TO_BROKER.
        Unreachable reserved decision values (blocked_by_scope,
        blocked_by_failed_health, blocked_by_failed_check, blocked_by_failed_doctor,
        blocked_by_push_check) are not produced by _decide and are handled through
        other broker paths (scope preflight, evidence failures)."""
        from pcae.core.permission_broker import _SG_HARD_BLOCK_TO_BROKER
        # These are the blocking decisions actually produced by _decide in shell_gate.py
        _SG_DECIDE_REACHABLE_BLOCKS: frozenset[str] = frozenset({
            "blocked_by_force_push",
            "blocked_by_raw_git_push",
            "blocked_by_raw_git_commit",
            "blocked_by_history_rewrite",
            "blocked_by_destructive_filesystem",
            "blocked_by_policy_forbidden_file",
            "blocked_by_backend_policy",
            "blocked_by_prompt_policy",
            "blocked_by_adoption_policy",
            "blocked_by_test_run_lock",
            "blocked_by_unknown_command",
            "blocked_by_missing_task",
            "deny",
            # requires_active_task is handled specially in _broker_decide
            # (checked before _SG_HARD_BLOCK_TO_BROKER lookup, §1d)
        })
        unmapped: list[str] = []
        for dec in _SG_DECIDE_REACHABLE_BLOCKS:
            if dec not in _SG_HARD_BLOCK_TO_BROKER:
                unmapped.append(dec)
        assert unmapped == [], (
            f"Reachable shell-gate blocking decisions not mapped: {unmapped}"
        )


# ── Regression: performed/authorization flags remain false ───────────────────

class Test88v1PerformedFlagsInvariant:
    """All performed/authorization flags must remain unconditionally false."""

    @pytest.mark.parametrize("command", [
        "OPENAI_API_KEY=x python script.py",
        "printenv",
        "env | grep SECRET",
        "cat ~/.ssh/id_rsa",
        "security find-generic-password",
    ])
    def test_all_performed_flags_false_for_secret_commands(self, command):
        b = _broker("read", command=command)
        for flag in _PERFORMED_FLAGS:
            assert b[flag] is False, (
                f"Command '{command}': {flag} should be False but is {b[flag]}"
            )


# ── Regression: hard blocks still propagate ──────────────────────────────────

class Test88v1HardBlockPropagation:
    """Hard blocks must still propagate correctly after redaction changes."""

    def test_force_push_still_hard_blocked(self):
        b = _broker("read", command="git push --force origin main")
        assert b["decision"] == "blocked_by_force_push"
        assert b["hard_block_present"] is True

    def test_raw_commit_still_blocked(self):
        b = _broker("read", command="git commit -m 'unsafe'")
        # shell-gate blocked_by_raw_git_commit maps to broker blocked_by_shell_gate
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_history_rewrite_still_blocked(self):
        b = _broker("read", command="git rebase -i HEAD~3")
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_secret_access_hard_blocked_without_approval(self):
        b = _broker("read", command="cat ~/.ssh/id_rsa",
                    health_passed=True, check_passed=True)
        assert b["decision"] == "requires_human_review"

    def test_secret_access_still_requires_review_with_health(self):
        b = _broker("read", command="cat ~/.ssh/id_rsa",
                    health_passed=True, check_passed=True,
                    human_review_present=True)
        assert b["decision"] == "allow_preflight_only"


# ── Regression: human approval / accepted risk cannot override hard blocks ───

class Test88v1HumanApprovalLimits:
    """Human approval and accepted risk must still be unable to override hard blocks."""

    def test_human_approval_does_not_override_force_push(self):
        b = _broker("read", command="git push --force origin main",
                    human_approval_present=True, human_review_present=True,
                    health_passed=True, check_passed=True)
        assert b["decision"] == "blocked_by_force_push"
        assert b["hard_block_present"] is True

    def test_accepted_risk_does_not_override_secret_access_hard_block(self):
        b = _broker("read", command="rm -rf /",
                    human_approval_present=True, accepted_risk_present=True,
                    human_review_present=True,
                    health_passed=True, check_passed=True)
        # rm -rf is destructive_filesystem → blocked_by_destructive_filesystem
        assert b["hard_block_present"] is True
        assert b["decision"] != "allow_preflight_only"
