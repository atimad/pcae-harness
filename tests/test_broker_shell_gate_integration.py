"""
Broker + Shell Gate Integration Tests — Phase 88T.

Tests the integrated broker decision logic consuming shell-gate evidence.
All tests are fast_green (no subprocess calls to classify commands).

Covers:
- Hard-block propagation from shell gate to broker
- Non-hard-block shell gate decision handling
- Read-only command handling
- Contradiction detection via _check_sg_contradiction
- Performed-flag invariant (all 14 flags unconditionally False)
- Secret-access command redaction
- Active-task / no-active-task boundary
- Audit field presence and correctness
- CLI smoke (slow/integration tier)
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
    _SG_SCHEMA_VERSION,
    _check_sg_contradiction,
    build_permission_broker,
)

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent

# All 14 performed/authorization flags
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


# ── TestShellGateHardBlockPropagation ──────────────────────────────────────

class TestShellGateHardBlockPropagation:
    """Shell gate hard blocks propagate to broker hard block decisions."""

    def test_raw_git_push_command(self, no_task_root):
        b = _broker("read", command="git push origin main", root=no_task_root)
        assert b["decision"] == "blocked_by_raw_git_push"
        assert b["hard_block_present"] is True

    def test_force_push_command(self, no_task_root):
        b = _broker("read", command="git push --force origin main", root=no_task_root)
        assert b["decision"] == "blocked_by_force_push"
        assert b["hard_block_present"] is True

    def test_force_with_lease_command(self, no_task_root):
        b = _broker("read", command="git push --force-with-lease", root=no_task_root)
        assert b["decision"] == "blocked_by_force_push"
        assert b["hard_block_present"] is True

    def test_raw_git_commit_command(self, no_task_root):
        b = _broker("read", command="git commit -m 'msg'", root=no_task_root)
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_git_history_rewrite_rebase(self, no_task_root):
        b = _broker("read", command="git rebase -i HEAD~3", root=no_task_root)
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_destructive_filesystem_rm_rf(self, no_task_root):
        b = _broker("read", command="rm -rf .", root=no_task_root)
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_policy_forbidden_file_mutation_maps_to_scope(self, tmp_task_root):
        # blocked_by_policy_forbidden_file → blocked_by_scope (88T change)
        b = _broker("source_mutation", command="cat file.py > README.md",
                    root=tmp_task_root)
        assert b["decision"] == "blocked_by_scope"
        assert b["hard_block_present"] is True

    def test_unknown_command_blocked(self, no_task_root):
        b = _broker("read", command="somecustomtool --do-something", root=no_task_root)
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_blocked_by_missing_task_maps_to_task_contract(self, no_task_root):
        # blocked_by_missing_task from SG (mutating category, no task) →
        # should fire as blocked_by_task_contract via 1d (requires_active_task)
        # OR via _SG_HARD_BLOCK_TO_BROKER["blocked_by_missing_task"]
        b = _broker("source_mutation", command="cp src/a.py src/b.py",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_task_contract"
        assert b["hard_block_present"] is True

    def test_hard_block_overrides_human_review(self, no_task_root):
        b = _broker("read", command="git push --force",
                    human_review_present=True, root=no_task_root)
        assert b["decision"] == "blocked_by_force_push"
        assert b["execution_authorized"] is False

    def test_hard_block_overrides_human_approval(self, no_task_root):
        b = _broker("read", command="git push --force",
                    human_approval_present=True, root=no_task_root)
        # human_approval alongside SG hard block → contradiction
        assert b["hard_block_present"] is True
        assert b["execution_authorized"] is False

    def test_hard_block_with_accepted_risk(self, no_task_root):
        b = _broker("read", command="rm -rf .",
                    accepted_risk_present=True, root=no_task_root)
        # accepted_risk alongside SG hard block → contradiction
        assert b["hard_block_present"] is True
        assert b["execution_authorized"] is False

    def test_hard_block_passes_without_health_evidence(self, no_task_root):
        # Hard block fires before evidence failures check
        b = _broker("source_mutation", command="git push --force",
                    health_passed=None, root=no_task_root)
        assert b["decision"] == "blocked_by_force_push"

    def test_hard_block_before_scope_check(self, tmp_task_root):
        # Hard block fires at priority 1 before scope preflight at priority 6
        b = _broker("source_mutation", command="git push --force",
                    files=["src/x.py"], root=tmp_task_root)
        assert b["decision"] == "blocked_by_force_push"


# ── TestShellGateNonHardBlock ──────────────────────────────────────────────

class TestShellGateNonHardBlock:
    """Non-hard-block shell gate decisions handled correctly."""

    def test_package_install_requires_human_review(self, tmp_task_root):
        # Use action="read" — non-mutating, so missing health/check don't block
        b = _broker("read", command="pip install requests", root=tmp_task_root)
        assert b["decision"] == "requires_human_review"
        assert b["hard_block_present"] is False

    def test_package_install_with_human_review_satisfies_gate(self, tmp_task_root):
        b = _broker("read", command="pip install requests",
                    human_review_present=True, root=tmp_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["execution_authorized"] is False

    def test_network_access_requires_human_review(self, tmp_task_root):
        b = _broker("read", command="curl https://example.com", root=tmp_task_root)
        assert b["decision"] == "requires_human_review"

    def test_backend_invocation_requires_human_review(self, tmp_task_root):
        # Use action="read" — non-mutating avoids missing-evidence block
        b = _broker("read", command="claude --help", root=tmp_task_root)
        assert b["decision"] == "requires_human_review"

    def test_environment_mutation_requires_human_review(self, tmp_task_root):
        b = _broker("read", command="export API_KEY=secret", root=tmp_task_root)
        assert b["decision"] == "requires_human_review"

    def test_requires_preflight_adds_missing_evidence(self, tmp_task_root):
        # source_mutation command without health/check → missing evidence
        b = _broker("source_mutation", command="cp src/a.py src/b.py",
                    root=tmp_task_root)
        assert b["decision"] == "requires_more_evidence"
        assert "health_check" in b["missing_evidence"]

    def test_requires_active_task_with_task_present_satisfies(self, tmp_task_root):
        # pytest command + task present: requires_active_task satisfied → no block from SG
        b = _broker("test_mutation", command="python -m pytest tests -q",
                    health_passed=True, check_passed=True,
                    human_review_present=True, root=tmp_task_root)
        assert b["decision"] == "allow_preflight_only"

    def test_sg_requires_human_review_without_human_review(self, tmp_task_root):
        b = _broker("source_mutation", command="pip install requests",
                    health_passed=True, check_passed=True,
                    root=tmp_task_root)
        assert b["decision"] == "requires_human_review"


# ── TestShellGateReadOnly ──────────────────────────────────────────────────

class TestShellGateReadOnly:
    """Read-only shell gate decisions produce allow_preflight_only, never execution_authorized."""

    def test_cat_file_allow_preflight_only(self, no_task_root):
        b = _broker("read", command="cat src/pcae/cli.py", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["execution_authorized"] is False
        assert b["authorization_granted"] is False

    def test_git_log_allow_preflight_only(self, no_task_root):
        b = _broker("read", command="git log --oneline -10", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["execution_authorized"] is False

    def test_ls_allow_preflight_only(self, no_task_root):
        b = _broker("read", command="ls -la", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["execution_authorized"] is False

    def test_git_status_allow_preflight_only(self, no_task_root):
        b = _broker("read", command="git status", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"

    def test_grep_allow_preflight_only(self, no_task_root):
        b = _broker("read", command="grep -r 'TODO' src/", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"

    def test_pcae_governed_lifecycle_allow_preflight_only(self, tmp_task_root):
        b = _broker("source_mutation", command="pcae health",
                    health_passed=True, check_passed=True,
                    root=tmp_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["execution_authorized"] is False

    def test_read_only_does_not_require_task(self, no_task_root):
        # Read-only command in idle repo (no task) → allow_preflight_only
        b = _broker("read", command="cat README.md", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"


# ── TestShellGateContradictionDetection ───────────────────────────────────

class TestShellGateContradictionDetection:
    """Contradiction detection yields blocked_by_conflicting_evidence."""

    def _make_sg_evidence(self, **overrides: Any) -> dict[str, Any]:
        """Build a minimal valid sg_evidence dict, applying overrides."""
        base: dict[str, Any] = {
            "schema_version": _SG_SCHEMA_VERSION,
            "command_text": "cat file.py",
            "command_text_redacted": False,
            "command_category": "read_only_inspection",
            "decision": "allow_read_only",
            "reason_codes": ["read_only_program"],
            "detected_flags": {
                "read_only_detected": True,
                "force_push_detected": False,
                "raw_git_push_detected": False,
                "secret_access_detected": False,
            },
            "hard_block_present": False,
            "secret_access_detected": False,
        }
        base.update(overrides)
        return base

    def test_schema_version_missing_is_contradiction(self):
        ev = self._make_sg_evidence()
        del ev["schema_version"]
        result = _check_sg_contradiction(ev, "read")
        assert any("schema_version_mismatch" in d for d in result)

    def test_schema_version_wrong_is_contradiction(self):
        ev = self._make_sg_evidence(schema_version="99.0")
        result = _check_sg_contradiction(ev, "read")
        assert any("schema_version_mismatch" in d for d in result)

    def test_performed_flag_true_is_contradiction(self):
        ev = self._make_sg_evidence(command_executed=True)
        result = _check_sg_contradiction(ev, "read")
        assert any("command_executed" in d for d in result)

    def test_authorization_granted_true_is_contradiction(self):
        ev = self._make_sg_evidence(authorization_granted=True)
        result = _check_sg_contradiction(ev, "read")
        assert any("authorization_granted" in d for d in result)

    def test_execution_authorized_true_is_contradiction(self):
        ev = self._make_sg_evidence(execution_authorized=True)
        result = _check_sg_contradiction(ev, "read")
        assert any("execution_authorized" in d for d in result)

    def test_hard_block_with_allow_decision_is_contradiction(self):
        ev = self._make_sg_evidence(hard_block_present=True, decision="allow_read_only")
        result = _check_sg_contradiction(ev, "read")
        assert any("sg_hard_block_with_allow_decision" in d for d in result)

    def test_force_push_flag_with_wrong_decision_is_contradiction(self):
        ev = self._make_sg_evidence(
            detected_flags={
                "force_push_detected": True,
                "raw_git_push_detected": False,
                "secret_access_detected": False,
            },
            decision="allow_read_only",
        )
        result = _check_sg_contradiction(ev, "read")
        assert any("sg_force_push_flag_but_decision" in d for d in result)

    def test_raw_git_push_with_allow_is_contradiction(self):
        ev = self._make_sg_evidence(
            detected_flags={
                "force_push_detected": False,
                "raw_git_push_detected": True,
                "secret_access_detected": False,
            },
            decision="allow_read_only",
        )
        result = _check_sg_contradiction(ev, "read")
        assert any("raw_git_push_flag_with_allow_decision" in d for d in result)

    def test_unknown_category_with_allow_is_contradiction(self):
        ev = self._make_sg_evidence(
            command_category="unknown",
            decision="allow_read_only",
        )
        result = _check_sg_contradiction(ev, "read")
        assert any("sg_unknown_category_with_allow_decision" in d for d in result)

    def test_mutating_action_with_allow_read_only_is_contradiction(self):
        ev = self._make_sg_evidence(decision="allow_read_only")
        result = _check_sg_contradiction(ev, "source_mutation")
        assert any("sg_allow_read_only_for_mutating_action" in d for d in result)

    def test_secret_not_redacted_is_contradiction(self):
        ev = self._make_sg_evidence(
            command_text="cat ~/.ssh/id_rsa",  # not redacted
            secret_access_detected=True,
            detected_flags={
                "secret_access_detected": True,
                "force_push_detected": False,
                "raw_git_push_detected": False,
            },
        )
        result = _check_sg_contradiction(ev, "read")
        assert any("sg_secret_access_command_not_redacted" in d for d in result)

    def test_human_approval_alongside_sg_hard_block_is_contradiction(self):
        ev = self._make_sg_evidence(hard_block_present=True, decision="blocked_by_force_push")
        result = _check_sg_contradiction(ev, "read", human_approval_present=True)
        assert any("human_approval_alongside_sg_hard_block" in d for d in result)

    def test_accepted_risk_alongside_sg_hard_block_is_contradiction(self):
        ev = self._make_sg_evidence(hard_block_present=True, decision="blocked_by_force_push")
        result = _check_sg_contradiction(ev, "read", accepted_risk_present=True)
        assert any("accepted_risk_alongside_sg_hard_block" in d for d in result)

    def test_no_contradiction_for_clean_evidence(self):
        ev = self._make_sg_evidence()
        result = _check_sg_contradiction(ev, "read")
        assert result == []

    def test_contradiction_noted_for_force_push_with_human_approval(self, no_task_root):
        # Human approval + force push: priority 1 (SG hard block) fires first and
        # returns blocked_by_force_push. The contradiction is still recorded in audit.
        b = _broker("read", command="git push --force",
                    human_approval_present=True, root=no_task_root)
        # Priority 1 wins: hard block decision is returned
        assert b["decision"] == "blocked_by_force_push"
        assert b["hard_block_present"] is True
        # Contradiction is flagged in audit fields
        assert b["conflicting_evidence_detected"] is True

    def test_contradiction_details_populated(self, no_task_root):
        b = _broker("read", command="git push --force",
                    human_approval_present=True, root=no_task_root)
        assert len(b["conflicting_evidence_details"]) >= 1

    def test_contradiction_fires_at_priority_2_for_non_hard_block_sg(self):
        # Demonstrate priority 2 contradiction by calling _broker_decide directly
        # with sg_evidence that is contradictory but whose SG decision is NOT in the
        # hard block map (so priority 1 doesn't fire).
        from pcae.core.permission_broker import _broker_decide
        sg = {
            "schema_version": "99.0",  # wrong version → contradiction
            "command_text": "cat file.py",
            "command_text_redacted": False,
            "command_category": "read_only_inspection",
            "decision": "allow_read_only",  # NOT in hard block map → priority 1 doesn't fire
            "reason_codes": [],
            "detected_flags": {"force_push_detected": False, "raw_git_push_detected": False,
                               "secret_access_detected": False},
            "hard_block_present": False,
            "secret_access_detected": False,
        }
        from pcae.core.permission_broker import _check_sg_contradiction
        contradiction_details = _check_sg_contradiction(sg, "read")
        assert contradiction_details  # schema mismatch caught
        decision, reason_codes, missing = _broker_decide(
            requested_action="read",
            task_contract=None,
            sg_evidence=sg,
            scope_decision=None,
            health_passed=None,
            check_passed=None,
            doctor_passed=None,
            push_check_passed=None,
            tests_passed=None,
            test_run_clear=None,
            human_review_present=False,
            contradiction_details=contradiction_details,
        )
        assert decision == "blocked_by_conflicting_evidence"
        assert "contradictory_shell_gate_evidence" in reason_codes

    def test_no_contradiction_for_clean_force_push(self, no_task_root):
        # force push without human_approval_present → hard block but no contradiction
        b = _broker("read", command="git push --force", root=no_task_root)
        assert b["decision"] == "blocked_by_force_push"
        assert b["conflicting_evidence_detected"] is False


# ── TestPerformedFlagInvariant ─────────────────────────────────────────────

class TestShellGatePerformedFlagInvariant:
    """All 14 performed/authorization flags are unconditionally False with shell gate commands."""

    @pytest.mark.parametrize("flag", _PERFORMED_FLAGS)
    def test_flag_false_on_allow_path(self, flag: str, no_task_root):
        b = _broker("read", command="cat README.md", root=no_task_root)
        assert b[flag] is False, f"{flag} must be False on allow path"

    @pytest.mark.parametrize("flag", _PERFORMED_FLAGS)
    def test_flag_false_on_hard_block_path(self, flag: str, no_task_root):
        b = _broker("read", command="git push --force", root=no_task_root)
        assert b[flag] is False, f"{flag} must be False on hard block path"

    @pytest.mark.parametrize("flag", _PERFORMED_FLAGS)
    def test_flag_false_on_requires_human_review_path(self, flag: str, tmp_task_root):
        b = _broker("source_mutation", command="pip install requests",
                    root=tmp_task_root)
        assert b[flag] is False, f"{flag} must be False on human review path"

    @pytest.mark.parametrize("flag", _PERFORMED_FLAGS)
    def test_flag_false_on_contradiction_path(self, flag: str, no_task_root):
        b = _broker("read", command="git push --force",
                    human_approval_present=True, root=no_task_root)
        assert b[flag] is False, f"{flag} must be False on contradiction path"


# ── TestSecretAccessRedaction ──────────────────────────────────────────────

class TestSecretAccessRedaction:
    """Secret-access command text is redacted in broker output."""

    def test_ssh_key_read_is_redacted(self, no_task_root):
        b = _broker("read", command="cat ~/.ssh/id_rsa", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert sg is not None
        assert sg["command_text"] == "<redacted_secret_access_command>"
        assert sg["command_text_redacted"] is True

    def test_security_keychain_is_redacted(self, no_task_root):
        b = _broker("read", command="security find-generic-password -a myaccount",
                    root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert sg is not None
        assert sg["command_text"] == "<redacted_secret_access_command>"
        assert b["shell_gate_command_text_redacted"] is True

    def test_gpg_command_is_redacted(self, no_task_root):
        b = _broker("read", command="gpg --export-secret-keys", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert sg is not None
        assert sg["command_text"] == "<redacted_secret_access_command>"

    def test_non_secret_command_is_not_redacted(self, no_task_root):
        b = _broker("read", command="cat src/pcae/cli.py", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert sg is not None
        assert sg["command_text"] == "cat src/pcae/cli.py"
        assert sg["command_text_redacted"] is False
        assert b["shell_gate_command_text_redacted"] is False

    def test_redacted_command_produces_no_text_hash(self, no_task_root):
        b = _broker("read", command="cat ~/.ssh/id_rsa", root=no_task_root)
        assert b["shell_gate_command_text_hash"] is None

    def test_non_secret_command_has_sha256_hash(self, no_task_root):
        import hashlib
        b = _broker("read", command="cat src/pcae/cli.py", root=no_task_root)
        expected = hashlib.sha256(b"cat src/pcae/cli.py").hexdigest()
        assert b["shell_gate_command_text_hash"] == expected

    def test_secret_access_evidence_not_redacted_is_contradiction(self, no_task_root):
        # If secret detected but not redacted → contradiction (tested via _check_sg_contradiction)
        # In normal broker flow, redaction happens before contradiction check,
        # so this path can only be triggered via direct _check_sg_contradiction call.
        ev = {
            "schema_version": _SG_SCHEMA_VERSION,
            "command_text": "cat ~/.ssh/id_rsa",  # NOT redacted
            "command_text_redacted": False,
            "command_category": "secret_access",
            "decision": "requires_human_review",
            "reason_codes": [],
            "detected_flags": {"secret_access_detected": True, "force_push_detected": False,
                               "raw_git_push_detected": False},
            "hard_block_present": False,
            "secret_access_detected": True,
        }
        result = _check_sg_contradiction(ev, "read")
        assert any("sg_secret_access_command_not_redacted" in d for d in result)


# ── TestActiveTaskBoundary ─────────────────────────────────────────────────

class TestActiveTaskBoundary:
    """Read-only commands unblocked in idle repo; mutating commands blocked without task."""

    def test_read_command_no_task_allowed(self, no_task_root):
        b = _broker("read", command="cat src/pcae/cli.py", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"

    def test_mutating_action_no_task_blocked(self, no_task_root):
        # source_mutation action without command, no task → blocked_by_task_contract
        b = _broker("source_mutation", root=no_task_root)
        assert b["decision"] == "blocked_by_task_contract"

    def test_mutating_shell_command_no_task_blocked(self, no_task_root):
        # Mutating shell command, no task → blocked via shell gate 1d or broker priority 5
        b = _broker("source_mutation", command="cp src/a.py src/b.py", root=no_task_root)
        assert b["decision"] == "blocked_by_task_contract"
        assert b["hard_block_present"] is True

    def test_mutating_shell_command_with_task_proceeds(self, tmp_task_root):
        # Mutating shell command, task present → moves past task check to missing evidence
        b = _broker("source_mutation", command="cp src/a.py src/b.py",
                    root=tmp_task_root)
        # SG decision for cp is requires_preflight; no health/check → requires_more_evidence
        assert b["decision"] == "requires_more_evidence"

    def test_requires_active_task_sg_no_task_hard_block(self, no_task_root):
        # pytest command + no task → SG: requires_active_task → broker 1d hard block
        b = _broker("test_mutation", command="python -m pytest tests -q",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_task_contract"
        assert b["hard_block_present"] is True

    def test_requires_active_task_sg_with_task_no_block(self, tmp_task_root):
        # pytest command + task present → SG constraint satisfied, proceeds
        b = _broker("test_mutation", command="python -m pytest tests -q",
                    health_passed=True, check_passed=True,
                    human_review_present=True, root=tmp_task_root)
        assert b["decision"] == "allow_preflight_only"

    def test_read_only_sg_decision_no_task_allowed(self, no_task_root):
        # git log (read-only) + no task → allow_preflight_only, task not required
        b = _broker("read", command="git log --oneline -5", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"
        assert b["active_task_detected"] is False


# ── TestAuditFields ────────────────────────────────────────────────────────

class TestAuditFields:
    """Audit fields added in 88T are present and correct in broker output."""

    def test_shell_gate_schema_version_present(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert b["shell_gate_schema_version"] == "0.1"

    def test_shell_gate_command_category_present(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert b["shell_gate_command_category"] == "read_only_inspection"

    def test_shell_gate_decision_present(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert b["shell_gate_decision"] == "allow_read_only"

    def test_shell_gate_reason_codes_present(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert isinstance(b["shell_gate_reason_codes"], list)
        assert len(b["shell_gate_reason_codes"]) > 0

    def test_shell_gate_hard_block_present_false_for_allow(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert b["shell_gate_hard_block_present"] is False

    def test_shell_gate_hard_block_present_true_for_force_push(self, no_task_root):
        b = _broker("read", command="git push --force", root=no_task_root)
        assert b["shell_gate_hard_block_present"] is True

    def test_conflicting_evidence_detected_false_for_clean(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert b["conflicting_evidence_detected"] is False
        assert b["conflicting_evidence_details"] == []

    def test_conflicting_evidence_detected_true_for_contradiction(self, no_task_root):
        b = _broker("read", command="git push --force",
                    human_approval_present=True, root=no_task_root)
        assert b["conflicting_evidence_detected"] is True

    def test_hard_block_sources_for_force_push(self, no_task_root):
        b = _broker("read", command="git push --force", root=no_task_root)
        assert "shell_gate" in b["hard_block_sources"]

    def test_hard_block_sources_empty_for_allow(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert b["hard_block_sources"] == []

    def test_accepted_risk_noted_reflects_input(self, no_task_root):
        b = _broker("read", command="cat file.py",
                    accepted_risk_present=True, root=no_task_root)
        assert b["accepted_risk_noted"] is True

    def test_accepted_risk_noted_false_when_absent(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert b["accepted_risk_noted"] is False

    def test_broker_mapping_reason_format(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        reason = b["broker_mapping_reason"]
        assert "sg:" in reason
        assert "->broker:" in reason

    def test_audit_fields_null_when_no_command(self, no_task_root):
        b = _broker("read", root=no_task_root)
        assert b["shell_gate_schema_version"] is None
        assert b["shell_gate_command_category"] is None
        assert b["shell_gate_decision"] is None
        assert b["shell_gate_hard_block_present"] is None
        assert b["shell_gate_command_text_hash"] is None
        assert b["shell_gate_command_text_redacted"] is False

    def test_evidence_source_includes_category_label(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        # Evidence source label should include category
        sources = b["evidence_sources"]
        sg_sources = [s for s in sources if "shell-gate" in s]
        assert any("read_only_inspection" in s for s in sg_sources)


# ── TestDecisionMapping ────────────────────────────────────────────────────

class TestDecisionMapping:
    """Verify key shell gate → broker decision mappings from 88S §6."""

    def test_policy_forbidden_file_maps_to_scope(self, tmp_task_root):
        # 88T change: was blocked_by_shell_gate, now blocked_by_scope
        b = _broker("source_mutation", command="cat file.py > README.md",
                    root=tmp_task_root)
        assert b["decision"] == "blocked_by_scope"

    def test_blocked_by_missing_task_maps_to_task_contract(self, no_task_root):
        b = _broker("source_mutation", command="cp src/a.py src/b.py",
                    root=no_task_root)
        assert b["decision"] == "blocked_by_task_contract"

    def test_raw_git_push_maps_to_raw_git_push(self, no_task_root):
        b = _broker("read", command="git push origin main", root=no_task_root)
        assert b["decision"] == "blocked_by_raw_git_push"

    def test_force_push_maps_to_force_push(self, no_task_root):
        b = _broker("read", command="git push -f", root=no_task_root)
        assert b["decision"] == "blocked_by_force_push"

    def test_allow_read_only_maps_to_allow_preflight_only(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert b["decision"] == "allow_preflight_only"

    def test_allow_governed_maps_to_allow_preflight_only(self, tmp_task_root):
        b = _broker("source_mutation", command="pcae health",
                    health_passed=True, check_passed=True,
                    root=tmp_task_root)
        assert b["decision"] == "allow_preflight_only"

    def test_sg_hard_block_map_contains_blocked_by_missing_task(self):
        assert "blocked_by_missing_task" in _SG_HARD_BLOCK_TO_BROKER

    def test_sg_hard_block_map_policy_forbidden_is_scope(self):
        assert _SG_HARD_BLOCK_TO_BROKER["blocked_by_policy_forbidden_file"] == "blocked_by_scope"

    def test_sg_allow_decisions_set_correct(self):
        assert "allow_read_only" in _SG_ALLOW_DECISIONS
        assert "allow_governed" in _SG_ALLOW_DECISIONS
        assert "allow_test_execution" in _SG_ALLOW_DECISIONS
        assert "blocked_by_force_push" not in _SG_ALLOW_DECISIONS


# ── TestShellGateEvidenceFields ────────────────────────────────────────────

class TestShellGateEvidenceFields:
    """sg_evidence in broker output has the new 88T fields."""

    def test_sg_evidence_has_schema_version(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert sg["schema_version"] == "0.1"

    def test_sg_evidence_has_hard_block_present_false(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert sg["hard_block_present"] is False

    def test_sg_evidence_has_hard_block_present_true(self, no_task_root):
        b = _broker("read", command="git push --force", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert sg["hard_block_present"] is True

    def test_sg_evidence_has_secret_access_detected_false(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert sg["secret_access_detected"] is False

    def test_sg_evidence_has_secret_access_detected_true(self, no_task_root):
        b = _broker("read", command="cat ~/.ssh/id_rsa", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert sg["secret_access_detected"] is True

    def test_sg_evidence_has_command_text_redacted_false(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert sg["command_text_redacted"] is False

    def test_sg_evidence_has_command_text_redacted_true(self, no_task_root):
        b = _broker("read", command="cat ~/.ssh/id_rsa", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert sg["command_text_redacted"] is True

    def test_sg_evidence_none_when_no_command(self, no_task_root):
        b = _broker("read", root=no_task_root)
        assert b["shell_gate_evidence"] is None

    def test_sg_evidence_has_detected_flags(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert "detected_flags" in sg
        assert isinstance(sg["detected_flags"], dict)

    def test_sg_evidence_has_reason_codes(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        sg = b["shell_gate_evidence"]
        assert isinstance(sg["reason_codes"], list)


# ── TestEnvelopeInvariants ─────────────────────────────────────────────────

class TestEnvelopeInvariants:
    """Broker envelope invariants hold when shell gate evidence is present."""

    def test_schema_version_present(self, no_task_root):
        result = _pb("read", command="cat file.py", root=no_task_root)
        assert result["schema_version"] == "0.1"

    def test_broker_decision_in_bpe_decisions(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert b["decision"] in BPE_DECISIONS

    def test_hard_block_decision_in_hard_block_set(self, no_task_root):
        b = _broker("read", command="git push --force", root=no_task_root)
        assert b["decision"] in BPE_HARD_BLOCK_DECISIONS

    def test_hard_block_present_consistent_with_decision(self, no_task_root):
        b = _broker("read", command="git push --force", root=no_task_root)
        assert b["hard_block_present"] is True
        assert b["decision"] in BPE_HARD_BLOCK_DECISIONS

    def test_allow_decision_hard_block_false(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert b["hard_block_present"] is False

    def test_shell_gate_evidence_in_evidence_sources(self, no_task_root):
        b = _broker("read", command="cat file.py", root=no_task_root)
        assert any("shell-gate" in s for s in b["evidence_sources"])

    def test_warnings_list_exists(self, no_task_root):
        result = _pb("read", command="cat file.py", root=no_task_root)
        assert isinstance(result["warnings"], list)

    def test_warnings_has_contradiction_notice(self, no_task_root):
        result = _pb("read", command="git push --force",
                     human_approval_present=True, root=no_task_root)
        assert any("contradictions_detected" in w for w in result["warnings"])


# ── CLI Smoke Tests (slow/integration tier) ────────────────────────────────

class TestCLISmoke:
    """CLI integration: broker command accepts requested command, returns JSON."""

    @pytest.mark.slow
    @pytest.mark.integration
    def test_cli_with_read_only_command(self):
        cmd = [
            sys.executable, "-m", "pcae",
            "permission-broker", "evaluate",
            "--requested-action", "read",
            "--requested-command", "cat README.md",
            "--json",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        broker = data["broker"]
        assert broker["command_executed"] is False
        assert broker["execution_authorized"] is False
        assert broker["shell_gate_evidence"] is not None
        assert "shell_gate_schema_version" in broker

    @pytest.mark.slow
    @pytest.mark.integration
    def test_cli_with_force_push_command(self):
        cmd = [
            sys.executable, "-m", "pcae",
            "permission-broker", "evaluate",
            "--requested-action", "read",
            "--requested-command", "git push --force",
            "--json",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        broker = data["broker"]
        assert broker["decision"] == "blocked_by_force_push"
        assert broker["hard_block_present"] is True
        assert broker["command_executed"] is False
        assert broker["execution_authorized"] is False

    @pytest.mark.slow
    @pytest.mark.integration
    def test_cli_with_secret_access_command(self):
        cmd = [
            sys.executable, "-m", "pcae",
            "permission-broker", "evaluate",
            "--requested-action", "read",
            "--requested-command", "cat ~/.ssh/id_rsa",
            "--json",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        broker = data["broker"]
        assert broker["shell_gate_command_text_redacted"] is True
        sg = broker["shell_gate_evidence"]
        assert sg["command_text"] == "<redacted_secret_access_command>"
