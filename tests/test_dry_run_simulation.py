"""
Dry-run blocking simulation prototype tests — Phase 89C.

Tests for pcae dry-run check, explain, and status.
All tests are fast_green (no subprocess execution beyond reading
governance state via advisory/broker delegation).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from pcae.core.dry_run import (
    SIMULATION_DECISIONS,
    build_simulation,
    build_simulation_explain,
    build_simulation_status,
)

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Helpers ─────────────────────────────────────────────────────────────────

_INVARIANT_FALSES = [
    "authorization_granted",
    "execution_authorized",
    "command_executed",
    "enforcement_applied",
    "shell_intercepted",
    "wrapper_installed",
    "backend_invoked",
    "prompt_sent",
    "output_captured",
    "intake_performed",
    "adoption_performed",
]


def _sim(command: str) -> dict[str, Any]:
    """Return simulation envelope for a command."""
    return build_simulation(REPO_ROOT, requested_command=command)


# ═══════════════════════════════════════════════════════════════════════════════
# Core Simulation Envelope Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSimulationEnvelope:
    """JSON envelope structure and required fields."""

    REQUIRED_FIELDS = [
        "schema_version", "generated_at", "repository_root",
        "simulation_id", "simulation_mode", "simulation_version",
        "requested_action", "requested_command", "requested_command_redacted",
        "broker_decision", "simulation_decision",
        "simulation_severity", "simulation_severity_label",
        "would_block", "would_allow_read_only",
        "would_require_human_review", "would_require_preflight",
        "hard_block_present", "redaction_applied", "safe_to_display",
        "operator_message", "next_required_action",
        "safety_invariants", "known_limitations",
    ]

    def test_envelope_has_required_fields(self):
        data = _sim("git status")
        for field in self.REQUIRED_FIELDS:
            assert field in data, f"Missing required field: {field}"

    def test_simulation_mode_is_true(self):
        data = _sim("git status")
        assert data["simulation_mode"] is True

    def test_schema_version(self):
        data = _sim("git status")
        assert data["schema_version"] == "0.1"


class TestSimulationInvariantFalseFields:
    """All authorization/enforcement/interception fields always false."""

    @pytest.mark.parametrize("field", _INVARIANT_FALSES)
    def test_invariant_field_false(self, field):
        data = _sim("git status")
        assert data[field] is False, f"{field} must be False"

    @pytest.mark.parametrize("field", _INVARIANT_FALSES)
    def test_blocked_command_invariants_still_false(self, field):
        data = _sim("git push --force origin main")
        assert data[field] is False, f"{field} must be False"

    @pytest.mark.parametrize("field", _INVARIANT_FALSES)
    def test_secret_command_invariants_still_false(self, field):
        data = _sim("OPENAI_API_KEY=x python script.py")
        assert data[field] is False, f"{field} must be False"


class TestSimulationSafetyInvariants:
    """safety_invariants object correctness."""

    def test_safety_invariants_present(self):
        data = _sim("git status")
        si = data["safety_invariants"]
        assert si["simulation_only"] is True
        assert si["no_execution"] is True
        assert si["no_authorization"] is True
        assert si["no_enforcement"] is True
        assert si["no_interception"] is True
        assert si["no_wrappers"] is True
        assert si["no_backend"] is True
        assert si["no_persistent_state"] is True
        assert si["hard_blocks_preserved"] is True
        assert si["secrets_redacted"] is True

    def test_known_limitations_present(self):
        data = _sim("git status")
        lims = data["known_limitations"]
        assert len(lims) >= 3
        assert any("no enforcement" in l.lower() for l in lims)


class TestSimulationId:
    """Simulation ID uniqueness."""

    def test_simulation_id_is_present(self):
        data = _sim("git status")
        assert "simulation_id" in data
        assert data["simulation_id"].startswith("sim-")

    def test_simulation_ids_are_unique(self):
        ids = {_sim("git status")["simulation_id"] for _ in range(10)}
        assert len(ids) == 10


# ═══════════════════════════════════════════════════════════════════════════════
# Decision Mapping Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSimulationDecisionMapping:
    """Simulation decisions match advisory decisions."""

    def test_read_only_maps_to_governed_preflight(self):
        data = _sim("git status")
        # Broker maps allow_preflight_only → would_allow_governed_preflight_only
        assert data["simulation_decision"] == "would_allow_governed_preflight_only"
        assert data["simulation_severity"] == "info"
        assert data["would_block"] is False
        assert data["would_allow_read_only"] is False  # advisory uses governed preflight for this path
        assert data["would_allow_governed_preflight_only"] is True

    def test_raw_git_push_maps_to_would_block(self):
        data = _sim("git push origin main")
        assert data["simulation_decision"] == "would_block_by_raw_git_push"
        assert data["simulation_severity"] == "blocked"
        assert data["would_block"] is True
        assert data["hard_block_present"] is True
        assert data["governed_alternative"] == "pcae push"

    def test_force_push_maps_to_would_block(self):
        data = _sim("git push --force origin main")
        assert data["simulation_decision"] == "would_block_by_force_push"
        assert data["simulation_severity"] == "blocked"
        assert data["would_block"] is True
        assert data["governed_alternative"] is None  # permanently blocked

    def test_shell_embedded_git_push_blocks(self):
        data = _sim("sh -c 'git push'")
        assert data["would_block"] is True
        assert data["simulation_severity"] == "blocked"

    def test_env_python_not_secret(self):
        data = _sim("env python")
        assert data["simulation_decision"] != "would_require_human_review"

    def test_compact_pipe_env_grep_now_redacted(self):
        data = _sim("env|grep TOKEN")
        assert data["redaction_applied"] is True

    def test_compact_tee_readme_blocked(self):
        data = _sim("echo x|tee README.md")
        assert data["would_block"] is True


class TestSimulationSeverity:
    """Severity model mapping."""

    def test_info_for_governed_pcae(self):
        data = _sim("pcae health")
        assert data["simulation_severity"] == "info"

    def test_caution_for_missing_evidence(self):
        data = _sim("echo x > src/test.py")
        # filesystem_write + no active task = missing task → caution
        assert data["simulation_severity"] in ("caution", "blocked")

    def test_blocked_for_force_push(self):
        data = _sim("git push --force origin main")
        assert data["simulation_severity"] == "blocked"

    def test_review_required_for_secret(self):
        data = _sim("OPENAI_API_KEY=x python script.py")
        assert data["simulation_severity"] == "review_required"


class TestSimulationEnforcementReadiness:
    """Enforcement readiness field present and non-empty."""

    def test_enforcement_readiness_present(self):
        data = _sim("git status")
        assert "enforcement_readiness" in data
        assert len(data["enforcement_readiness"]) > 0

    def test_blocked_command_has_readiness(self):
        data = _sim("git push --force origin main")
        assert "enforcement read" in data["enforcement_readiness"].lower() or \
               "force push" in data["enforcement_readiness"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Hard-Block Preservation
# ═══════════════════════════════════════════════════════════════════════════════

class TestHardBlockPreservation:
    """Hard blocks preserved in simulation output."""

    def test_human_approval_cannot_override_hard_block(self):
        data = build_simulation(
            REPO_ROOT, requested_command="git push --force origin main",
            human_review_present=True, human_approval_present=True,
        )
        assert data["would_block"] is True
        assert data["hard_block_present"] is True
        assert data["human_approval_cannot_override_hard_block"] is True

    def test_accepted_risk_cannot_override_hard_block(self):
        data = build_simulation(
            REPO_ROOT, requested_command="git push --force origin main",
            accepted_risk_present=True,
        )
        assert data["would_block"] is True
        assert data["hard_block_present"] is True

    def test_all_hard_blocks_stay_blocking(self):
        for cmd in [
            "git push --force origin main",
            "rm -rf /",
            "echo x > README.md",
            "git push origin main",
        ]:
            data = _sim(cmd)
            assert data["would_block"] is True, f"{cmd}: hard block not preserved"


# ═══════════════════════════════════════════════════════════════════════════════
# Secret-Redaction Preservation
# ═══════════════════════════════════════════════════════════════════════════════

class TestSecretRedaction:
    """Secrets are redacted in simulation output."""

    def test_secret_env_var_redacted(self):
        data = _sim("OPENAI_API_KEY=x python script.py")
        assert data["redaction_applied"] is True

    def test_env_bare_redacted(self):
        data = _sim("env")
        assert data["redaction_applied"] is True

    def test_cat_ssh_key_redacted(self):
        data = _sim("cat ~/.ssh/id_rsa")
        assert data["redaction_applied"] is True

    def test_redaction_sentinel_not_raw(self):
        data = _sim("OPENAI_API_KEY=x python script.py")
        assert "OPENAI_API_KEY" not in data["requested_command"]


# ═══════════════════════════════════════════════════════════════════════════════
# Explain and Status
# ═══════════════════════════════════════════════════════════════════════════════

class TestSimulationExplain:
    """Simulation explain returns valid data."""

    def test_explain_known_decision(self):
        data = build_simulation_explain("would_block_by_raw_git_push")
        assert data["valid_decision"] is True
        assert "explanation" in data
        assert data["severity"] == "blocked"
        assert data["governed_alternative"] == "pcae push"

    def test_explain_unknown_decision(self):
        data = build_simulation_explain("not_a_decision")
        assert data["valid_decision"] is False
        assert "explanation" in data

    @pytest.mark.parametrize("decision", [
        "would_allow_read_only",
        "would_block_by_force_push",
        "would_require_human_review",
        "would_deny",
    ])
    def test_all_key_decisions_explainable(self, decision):
        data = build_simulation_explain(decision)
        assert data["valid_decision"] is True
        assert len(data["explanation"]["summary"]) > 0


class TestSimulationStatus:
    """Simulation status returns correct invariants."""

    def test_status_available(self):
        data = build_simulation_status()
        assert data["simulation_mode_available"] is True
        assert data["simulation_mode_version"] == "0.1"
        assert data["phase"] == "89C"
        assert data["enforcement_stage"] == "dry_run_simulation"

    def test_status_invariants(self):
        data = build_simulation_status()
        inv = data["invariants"]
        assert inv["simulation_only"] is True
        assert inv["no_command_execution"] is True
        assert inv["no_enforcement"] is True

    def test_status_limitations(self):
        data = build_simulation_status()
        assert len(data["known_limitations"]) >= 3


# ═══════════════════════════════════════════════════════════════════════════════
# Decision Vocabulary Coverage
# ═══════════════════════════════════════════════════════════════════════════════

class TestSimulationDecisionVocabulary:
    """All 19 decisions are present in the vocabulary."""

    def test_19_decisions_defined(self):
        assert len(SIMULATION_DECISIONS) == 19

    def test_key_decisions_in_vocabulary(self):
        for d in [
            "would_allow_read_only",
            "would_block_by_raw_git_push",
            "would_block_by_force_push",
            "would_deny",
            "unknown",
        ]:
            assert d in SIMULATION_DECISIONS


# ═══════════════════════════════════════════════════════════════════════════════
# Compound and Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestSimulationCompoundCommands:
    """Compound commands use most-restrictive classification."""

    def test_compound_blocks_on_dangerous_segment(self):
        data = _sim("git status && git push --force")
        assert data["would_block"] is True
        assert data["simulation_severity"] == "blocked"

    def test_compound_allows_on_read_only(self):
        data = _sim("git status && echo hello")
        assert data["would_block"] is False

    def test_compact_compound_blocks(self):
        data = _sim("git status&&git push")
        assert data["would_block"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# 89D Test Matrix — A. Read-Only Allow / Safe Paths
# ═══════════════════════════════════════════════════════════════════════════════

class Test89dMatrixReadOnly:
    """Read-only and governed PCAE commands should not be blocked."""

    @pytest.mark.parametrize("cmd", [
        "git status",
        "git diff",
        "git log --oneline -5",
        "pcae health",
        "pcae check",
        "pcae doctor task-memory",
        "ls",
        "pwd",
        "echo hello",
        "whoami",
        "date",
        "head README.md",
        "wc README.md",
    ])
    def test_read_only_not_blocked(self, cmd):
        data = _sim(cmd)
        assert data["would_block"] is False, f"{cmd}: read-only should not be blocked"
        assert data["simulation_severity"] in ("info", "caution"), \
            f"{cmd}: severity should be info or caution, got {data['simulation_severity']}"

    def test_pytest_dry_run_not_blocked(self):
        data = _sim("python -m pytest tests/test_dry_run_simulation.py -q")
        # pytest without -n auto is test execution → may require task
        assert data["would_block"] is False or data["would_require_active_task"], \
            "pytest should require task or be allowed, not hard blocked"


# ═══════════════════════════════════════════════════════════════════════════════
# 89D Test Matrix — B. Hard-Block Paths
# ═══════════════════════════════════════════════════════════════════════════════

class Test89dMatrixHardBlocks:
    """Hard-block commands must produce blocked severity."""

    @pytest.mark.parametrize("cmd,expected_block", [
        ("git push", "would_block_by_raw_git_push"),
        ("git push --force", "would_block_by_force_push"),
        ("git push -f", "would_block_by_force_push"),
        ("git commit -m x", "would_block_by_shell_gate"),
        ("rm -rf .", "would_block_by_shell_gate"),
        ("echo x > README.md", "would_block_by_shell_gate"),
    ])
    def test_hard_block_commands_blocked(self, cmd, expected_block):
        data = _sim(cmd)
        assert data["would_block"] is True, f"{cmd}: should be blocked"
        assert data["simulation_severity"] == "blocked", \
            f"{cmd}: severity should be blocked"
        assert data["hard_block_present"] is True

    def test_git_reset_hard_blocked(self):
        data = _sim("git reset --hard HEAD")
        assert data["would_block"] is True

    def test_force_push_has_no_governed_alternative(self):
        data = _sim("git push --force origin main")
        assert data["governed_alternative"] is None  # permanently blocked

    def test_raw_push_has_governed_alternative(self):
        data = _sim("git push origin main")
        assert data["governed_alternative"] == "pcae push"


# ═══════════════════════════════════════════════════════════════════════════════
# 89D Test Matrix — C. Shell Embedded-Command Paths
# ═══════════════════════════════════════════════════════════════════════════════

class Test89dMatrixShellEmbedded:
    """Shell -c/-lc commands classify embedded commands."""

    def test_bash_bare_requires_review(self):
        data = _sim("bash")
        assert data["shell_gate_category"] != "unknown"
        assert data["would_block"] is False  # requires review, not blocked

    def test_sh_bare_requires_review(self):
        data = _sim("sh")
        assert data["shell_gate_category"] != "unknown"

    def test_zsh_bare_requires_review(self):
        data = _sim("zsh")
        assert data["shell_gate_category"] != "unknown"

    def test_bash_lc_git_status_not_blocked(self):
        data = _sim('bash -lc "git status"')
        # Embedded git status → read_only_inspection → not blocked
        assert data["would_block"] is False

    def test_sh_c_git_status_not_blocked(self):
        data = _sim("sh -c 'git status'")
        assert data["would_block"] is False

    def test_bash_lc_git_push_blocked(self):
        data = _sim('bash -lc "git push"')
        assert data["would_block"] is True
        assert data["simulation_severity"] == "blocked"

    def test_sh_c_git_push_blocked(self):
        data = _sim("sh -c 'git push'")
        assert data["would_block"] is True

    def test_zsh_lc_git_push_force_blocked(self):
        data = _sim("zsh -lc 'git push --force'")
        assert data["would_block"] is True
        assert data["hard_block_present"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# 89D Test Matrix — D. Env-Prefix Paths
# ═══════════════════════════════════════════════════════════════════════════════

class Test89dMatrixEnvPrefix:
    """env and VAR=val prefix behavior from 89A."""

    def test_env_python_not_secret_access(self):
        data = _sim("env python script.py")
        assert data["shell_gate_category"] != "secret_access"

    def test_var_x_python_environment_mutation(self):
        data = _sim("VAR=x python script.py")
        # VAR=x is non-secret env mutation
        assert data["would_block"] is False  # requires review, not blocked

    def test_openai_key_env_triggers_secret(self):
        data = _sim("OPENAI_API_KEY=x python script.py")
        assert data["redaction_applied"] is True
        assert data["simulation_severity"] == "review_required"

    def test_env_openai_key_triggers_secret(self):
        data = _sim("env OPENAI_API_KEY=x python script.py")
        assert data["redaction_applied"] is True

    def test_env_token_x_curl_secret(self):
        data = _sim("env TOKEN=x curl https://example.com")
        assert data["redaction_applied"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# 89D Test Matrix — E. Compact Operator Paths
# ═══════════════════════════════════════════════════════════════════════════════

class Test89dMatrixCompactOperators:
    """Compact operators (|, &&, ||, ; without spaces) from 89A."""

    def test_env_pipe_grep_token_redacted(self):
        data = _sim("env|grep TOKEN")
        assert data["redaction_applied"] is True

    def test_env_pipe_grep_secret_redacted(self):
        data = _sim("env|grep SECRET")
        assert data["redaction_applied"] is True

    def test_env_pipe_grep_openai_key_redacted(self):
        data = _sim("env|grep OPENAI_API_KEY")
        assert data["redaction_applied"] is True

    def test_git_status_andand_git_push_blocked(self):
        data = _sim("git status&&git push")
        assert data["would_block"] is True

    def test_pcae_health_andand_git_push_blocked(self):
        data = _sim("pcae health&&git push")
        assert data["would_block"] is True
        assert data["simulation_severity"] == "blocked"

    def test_echo_pipe_tee_readme_blocked(self):
        data = _sim("echo x|tee README.md")
        assert data["would_block"] is True

    def test_git_status_semicolon_git_push_blocked(self):
        data = _sim("git status;git push")
        assert data["would_block"] is True

    def test_git_status_oror_git_push_blocked(self):
        data = _sim("git status||git push")
        assert data["would_block"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# 89D Test Matrix — F. Redaction Paths
# ═══════════════════════════════════════════════════════════════════════════════

class Test89dMatrixRedaction:
    """Secret redaction across env, files, and programs."""

    @pytest.mark.parametrize("cmd", [
        "printenv",
        "env",
        "env|grep TOKEN",
        "OPENAI_API_KEY=abc python script.py",
        "cat ~/.ssh/id_rsa",
        "security find-generic-password",
    ])
    def test_redaction_paths_redacted(self, cmd):
        data = _sim(cmd)
        assert data["redaction_applied"] is True, f"{cmd}: should be redacted"

    def test_echo_dollar_variable_not_currently_redacted(self):
        """echo $VAR references are shell-expanded, not classified as secret access.
        This is a known limitation — shell expansion detection is deferred."""
        data = _sim("echo $OPENAI_API_KEY")
        # echo is read-only; $VAR is not detected as secret pattern
        assert data["would_block"] is False

    def test_cat_dotenv_not_currently_redacted(self):
        """cat .env is not in _SECRET_FILE_PREFIXES. Known limitation."""
        data = _sim("cat .env")
        # cat is read-only unless redirected; .env not in secret file prefixes
        assert data["would_block"] is False

    def test_redacted_commands_use_sentinel(self):
        for cmd in [
            "OPENAI_API_KEY=x python script.py",
            "cat ~/.ssh/id_rsa",
        ]:
            data = _sim(cmd)
            assert "OPENAI_API_KEY" not in data["requested_command"]
            assert "id_rsa" not in data.get("requested_command", "")


# ═══════════════════════════════════════════════════════════════════════════════
# 89D Test Matrix — G. Explain/Status Coverage
# ═══════════════════════════════════════════════════════════════════════════════

class Test89dMatrixExplainCoverage:
    """All 19 decisions are explainable with complete information."""

    @pytest.mark.parametrize("decision", [
        "would_allow_read_only",
        "would_allow_governed_preflight_only",
        "would_require_active_task",
        "would_require_preflight",
        "would_require_human_review",
        "would_require_more_evidence",
        "would_block_by_scope",
        "would_block_by_task_contract",
        "would_block_by_raw_git_push",
        "would_block_by_force_push",
        "would_block_by_shell_gate",
        "would_block_by_test_run_lock",
        "would_block_by_failed_health",
        "would_block_by_failed_check",
        "would_block_by_failed_doctor",
        "would_block_by_push_check",
        "would_block_by_conflicting_evidence",
        "would_deny",
        "unknown",
    ])
    def test_every_decision_explainable(self, decision):
        data = build_simulation_explain(decision)
        assert data["valid_decision"] is True, f"{decision}: should be valid"
        assert "explanation" in data
        assert "summary" in data["explanation"]
        assert "meaning" in data["explanation"]

    def test_explain_includes_severity(self):
        data = build_simulation_explain("would_block_by_raw_git_push")
        assert data["severity"] == "blocked"

    def test_explain_includes_enforcement_readiness(self):
        data = build_simulation_explain("would_block_by_force_push")
        assert len(data["enforcement_readiness"]) > 0


class Test89dMatrixStatusCoverage:
    """Status reports all invariants and limitations."""

    def test_status_all_invariants_true(self):
        data = build_simulation_status()
        for key, val in data["invariants"].items():
            assert val is True, f"invariant {key} should be True"

    def test_status_limitations_complete(self):
        data = build_simulation_status()
        lims = data["known_limitations"]
        assert any("simulation only" in l.lower() or "no enforcement" in l.lower()
                   for l in lims)
        assert any("shell" in l.lower() for l in lims)


# ═══════════════════════════════════════════════════════════════════════════════
# 89D Test Matrix — H. JSON Schema Stability
# ═══════════════════════════════════════════════════════════════════════════════

class Test89dMatrixJsonStability:
    """JSON output has all required fields with stable types."""

    REQUIRED_CHECK_FIELDS = [
        "schema_version", "generated_at", "simulation_mode",
        "requested_command", "requested_command_redacted",
        "simulation_decision", "simulation_severity",
        "simulation_recommendation", "would_block",
        "would_allow_read_only", "would_allow_governed_preflight_only",
        "would_require_human_review", "would_require_preflight",
        "would_require_more_evidence", "hard_block_present",
        "hard_block_reason", "human_approval_relevant",
        "accepted_risk_relevant", "redaction_applied",
        "operator_message", "next_required_action",
        "safety_invariants", "warnings", "errors",
        "known_limitations",
    ]

    @pytest.mark.parametrize("field", REQUIRED_CHECK_FIELDS)
    def test_check_json_field_present(self, field):
        data = _sim("git status")
        assert field in data, f"check JSON missing: {field}"

    @pytest.mark.parametrize("cmd", [
        "git status", "git push", "git push --force",
        "OPENAI_API_KEY=x python script.py", "bash",
        "sh -c 'git status'", "env|grep TOKEN",
    ])
    def test_all_cmd_types_have_complete_envelope(self, cmd):
        data = _sim(cmd)
        for field in self.REQUIRED_CHECK_FIELDS:
            assert field in data, f"{cmd}: missing {field}"

    def test_simulation_id_format(self):
        for _ in range(5):
            data = _sim("git status")
            sid = data["simulation_id"]
            assert sid.startswith("sim-")
            assert len(sid) == 16  # "sim-" + 12 hex chars

    def test_enforcement_stage_consistent(self):
        for cmd in ["git status", "git push", "bash"]:
            data = _sim(cmd)
            assert data["enforcement_stage"] == "dry_run_simulation"


# ═══════════════════════════════════════════════════════════════════════════════
# 89D — Safety Invariant Cross-Check (All Commands)
# ═══════════════════════════════════════════════════════════════════════════════

class Test89dSafetyInvariantCrossCheck:
    """Every command type preserves all invariants."""

    ALL_COMMANDS = [
        "git status",
        "git push",
        "git push --force",
        "bash",
        "sh -c 'git status'",
        "sh -c 'git push'",
        "env python",
        "OPENAI_API_KEY=x python script.py",
        "env|grep TOKEN",
        "git status&&git push",
        "echo x|tee README.md",
        "pcae health",
    ]

    @pytest.mark.parametrize("cmd", ALL_COMMANDS)
    def test_no_execution_invariant(self, cmd):
        data = _sim(cmd)
        assert data["command_executed"] is False
        assert data["authorization_granted"] is False
        assert data["execution_authorized"] is False

    @pytest.mark.parametrize("cmd", ALL_COMMANDS)
    def test_no_enforcement_invariant(self, cmd):
        data = _sim(cmd)
        assert data["enforcement_applied"] is False
        assert data["shell_intercepted"] is False
        assert data["wrapper_installed"] is False

    @pytest.mark.parametrize("cmd", ALL_COMMANDS)
    def test_no_backend_invariant(self, cmd):
        data = _sim(cmd)
        assert data["backend_invoked"] is False
        assert data["prompt_sent"] is False
        assert data["output_captured"] is False
        assert data["intake_performed"] is False
        assert data["adoption_performed"] is False
