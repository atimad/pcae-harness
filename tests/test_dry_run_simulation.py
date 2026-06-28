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
