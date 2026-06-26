"""
Permission broker prototype tests (Phase 88R).

Fast tests call build_permission_broker directly and are in the fast_green
tier.  CLI integration tests are marked slow/integration.
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
    build_permission_broker,
)

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ────────────────────────────────────────────────────────────────

def _pb(
    action: str = "read",
    files: list[str] | None = None,
    command: str | None = None,
    health_passed: bool | None = None,
    check_passed: bool | None = None,
    doctor_passed: bool | None = None,
    push_check_passed: bool | None = None,
    tests_present: bool = False,
    tests_passed: bool | None = None,
    human_review_present: bool = False,
    human_approval_present: bool = False,
    accepted_risk_present: bool = False,
    source_backend: str | None = None,
    commit_message: str | None = None,
    push_target: str | None = None,
) -> dict[str, Any]:
    return build_permission_broker(
        repo_root=REPO_ROOT,
        requested_action=action,
        requested_files=files,
        requested_command=command,
        source_backend=source_backend,
        commit_message=commit_message,
        push_target=push_target,
        health_passed=health_passed,
        check_passed=check_passed,
        doctor_passed=doctor_passed,
        push_check_passed=push_check_passed,
        tests_present=tests_present,
        tests_passed=tests_passed,
        human_review_present=human_review_present,
        human_approval_present=human_approval_present,
        accepted_risk_present=accepted_risk_present,
    )


def _broker(action: str = "read", **kwargs: Any) -> dict[str, Any]:
    return _pb(action=action, **kwargs)["broker"]


# ── Envelope invariants ────────────────────────────────────────────────────

class TestEnvelopeInvariants:
    def test_schema_version_present(self):
        data = _pb()
        assert data["schema_version"] == "0.1"

    def test_generated_at_present(self):
        data = _pb()
        assert data["generated_at"]

    def test_source_command_present(self):
        data = _pb()
        assert data["source_command"] == "pcae permission-broker evaluate"

    def test_repository_root_present(self):
        data = _pb()
        assert "repository_root" in data

    def test_broker_key_present(self):
        data = _pb()
        assert "broker" in data

    def test_warnings_and_errors_present(self):
        data = _pb()
        assert "warnings" in data
        assert "errors" in data


# ── Broker-key invariants ──────────────────────────────────────────────────

class TestBrokerKeyInvariants:
    def test_broker_type_is_prototype(self):
        b = _broker()
        assert b["broker_type"] == "permission_broker_prototype"

    def test_decision_is_known_value(self):
        b = _broker()
        assert b["decision"] in BPE_DECISIONS

    def test_hard_block_present_is_bool(self):
        b = _broker()
        assert isinstance(b["hard_block_present"], bool)

    def test_active_task_detected_is_bool(self):
        b = _broker()
        assert isinstance(b["active_task_detected"], bool)

    def test_evidence_provided_key_present(self):
        b = _broker()
        assert "evidence_provided" in b

    def test_evidence_sources_is_list(self):
        b = _broker()
        assert isinstance(b["evidence_sources"], list)

    def test_missing_evidence_is_list(self):
        b = _broker()
        assert isinstance(b["missing_evidence"], list)

    def test_reason_codes_is_list(self):
        b = _broker()
        assert isinstance(b["reason_codes"], list)

    def test_shell_gate_evidence_is_none_without_command(self):
        b = _broker()
        assert b["shell_gate_evidence"] is None

    def test_shell_gate_evidence_present_with_command(self):
        b = _broker(command="ls -la")
        assert b["shell_gate_evidence"] is not None

    def test_requested_files_preserved(self):
        b = _broker(action="source_mutation", files=["src/foo.py"])
        assert b["requested_files"] == ["src/foo.py"]

    def test_requested_command_preserved(self):
        b = _broker(command="git status")
        assert b["requested_command"] == "git status"

    def test_source_backend_preserved(self):
        b = _broker(source_backend="claude")
        assert b["source_backend"] == "claude"

    def test_commit_message_preserved(self):
        b = _broker(commit_message="Add feature")
        assert b["commit_message"] == "Add feature"

    def test_push_target_preserved(self):
        b = _broker(push_target="origin/main")
        assert b["push_target"] == "origin/main"


# ── Performed / authorization flag invariants ──────────────────────────────

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


class TestPerformedFlagInvariants:
    @pytest.mark.parametrize("flag", _PERFORMED_FLAGS)
    def test_flag_always_false_for_read(self, flag: str):
        b = _broker("read")
        assert b[flag] is False, f"{flag} must always be False"

    @pytest.mark.parametrize("flag", _PERFORMED_FLAGS)
    def test_flag_always_false_for_mutation(self, flag: str):
        b = _broker("source_mutation", files=["src/x.py"],
                    health_passed=True, check_passed=True)
        assert b[flag] is False, f"{flag} must always be False"

    @pytest.mark.parametrize("flag", _PERFORMED_FLAGS)
    def test_flag_always_false_even_with_all_evidence(self, flag: str):
        b = _broker(
            "push",
            health_passed=True, check_passed=True, doctor_passed=True,
            push_check_passed=True, tests_present=True, tests_passed=True,
            human_review_present=True, human_approval_present=True,
        )
        assert b[flag] is False, f"{flag} must always be False"

    @pytest.mark.parametrize("flag", _PERFORMED_FLAGS)
    def test_flag_always_false_for_force_push_command(self, flag: str):
        b = _broker(command="git push --force")
        assert b[flag] is False, f"{flag} must always be False"


# ── Safety notes invariants ────────────────────────────────────────────────

class TestSafetyNotes:
    def test_safety_notes_present(self):
        b = _broker()
        assert "safety_notes" in b

    def test_prototype_only_flag(self):
        b = _broker()
        assert b["safety_notes"]["permission_broker_prototype_only"] is True

    def test_does_not_execute_commands(self):
        b = _broker()
        assert b["safety_notes"]["broker_does_not_execute_commands"] is True

    def test_does_not_invoke_backends(self):
        b = _broker()
        assert b["safety_notes"]["broker_does_not_invoke_backends"] is True

    def test_does_not_replace_human_review(self):
        b = _broker()
        assert b["safety_notes"]["broker_does_not_replace_human_review"] is True

    def test_execution_authorization_not_granted(self):
        b = _broker()
        assert b["safety_notes"]["execution_authorization_not_granted"] is True

    def test_does_not_override_hard_blocks(self):
        b = _broker()
        assert b["safety_notes"]["broker_does_not_override_hard_blocks"] is True


# ── Decision: allow_preflight_only ────────────────────────────────────────

class TestAllowPreflightOnly:
    def test_read_action_no_evidence_needed(self):
        b = _broker("read")
        assert b["decision"] == "allow_preflight_only"

    def test_source_mutation_with_health_check(self):
        b = _broker("source_mutation", files=["src/x.py"],
                    health_passed=True, check_passed=True)
        assert b["decision"] == "allow_preflight_only"

    def test_test_mutation_with_health_check(self):
        b = _broker("test_mutation", files=["tests/test_x.py"],
                    health_passed=True, check_passed=True)
        assert b["decision"] == "allow_preflight_only"

    def test_docs_mutation_with_health_check(self):
        b = _broker("docs_mutation", files=["docs/HOWTO.md"],
                    health_passed=True, check_passed=True)
        assert b["decision"] == "allow_preflight_only"

    def test_push_with_full_evidence_and_human_review(self):
        b = _broker(
            "push",
            health_passed=True, check_passed=True, push_check_passed=True,
            human_review_present=True,
        )
        assert b["decision"] == "allow_preflight_only"

    def test_commit_with_evidence_and_human_review(self):
        b = _broker(
            "commit", commit_message="Add feature",
            health_passed=True, check_passed=True, human_review_present=True,
        )
        assert b["decision"] == "allow_preflight_only"

    def test_hard_block_present_is_false_when_allowed(self):
        b = _broker("read")
        assert b["hard_block_present"] is False

    def test_allow_does_not_grant_authorization(self):
        b = _broker("read")
        assert b["authorization_granted"] is False
        assert b["execution_authorized"] is False


# ── Decision: requires_more_evidence ──────────────────────────────────────

class TestRequiresMoreEvidence:
    def test_source_mutation_missing_health(self):
        b = _broker("source_mutation", files=["src/x.py"])
        assert b["decision"] == "requires_more_evidence"

    def test_source_mutation_missing_check(self):
        b = _broker("source_mutation", files=["src/x.py"], health_passed=True)
        assert b["decision"] == "requires_more_evidence"

    def test_push_missing_push_check(self):
        b = _broker("push", health_passed=True, check_passed=True)
        assert b["decision"] == "requires_more_evidence"
        assert "push_check" in b["missing_evidence"]

    def test_missing_evidence_list_populated(self):
        b = _broker("source_mutation", files=["src/x.py"])
        assert len(b["missing_evidence"]) > 0

    def test_health_missing_in_evidence_list(self):
        b = _broker("source_mutation", files=["src/x.py"])
        assert "health_check" in b["missing_evidence"]

    def test_check_missing_in_evidence_list(self):
        b = _broker("source_mutation", files=["src/x.py"], health_passed=True)
        assert "governance_check" in b["missing_evidence"]

    def test_hard_block_present_is_false(self):
        b = _broker("source_mutation", files=["src/x.py"])
        assert b["hard_block_present"] is False


# ── Decision: requires_human_review ───────────────────────────────────────

class TestRequiresHumanReview:
    def test_push_without_human_review(self):
        b = _broker("push", health_passed=True, check_passed=True,
                    push_check_passed=True)
        assert b["decision"] == "requires_human_review"

    def test_commit_without_human_review(self):
        b = _broker("commit", health_passed=True, check_passed=True)
        assert b["decision"] == "requires_human_review"

    def test_adoption_without_human_review(self):
        b = _broker("adoption", health_passed=True, check_passed=True)
        assert b["decision"] == "requires_human_review"

    def test_rollback_without_human_review(self):
        b = _broker("rollback", health_passed=True, check_passed=True)
        assert b["decision"] == "requires_human_review"

    def test_storage_write_without_human_review(self):
        b = _broker("storage_write", health_passed=True, check_passed=True)
        assert b["decision"] == "requires_human_review"

    def test_push_with_human_review_does_not_require_review(self):
        b = _broker("push", health_passed=True, check_passed=True,
                    push_check_passed=True, human_review_present=True)
        assert b["decision"] != "requires_human_review"

    def test_hard_block_present_is_false(self):
        b = _broker("push", health_passed=True, check_passed=True,
                    push_check_passed=True)
        assert b["hard_block_present"] is False


# ── Decision: blocked_by_task_contract ────────────────────────────────────

class TestBlockedByTaskContract:
    def test_mutating_action_no_task_uses_real_repo(self):
        # With repo root pointing to a tmp dir with no task contract
        tmp_root = Path("/tmp/pcae-88r-test-no-task")
        tmp_root.mkdir(exist_ok=True)
        data = build_permission_broker(
            repo_root=tmp_root,
            requested_action="source_mutation",
            requested_files=["src/x.py"],
            health_passed=True,
            check_passed=True,
        )
        b = data["broker"]
        assert b["decision"] == "blocked_by_task_contract"
        assert b["active_task_detected"] is False
        assert b["hard_block_present"] is True

    def test_read_action_no_task_is_not_blocked(self):
        tmp_root = Path("/tmp/pcae-88r-test-no-task")
        tmp_root.mkdir(exist_ok=True)
        data = build_permission_broker(
            repo_root=tmp_root,
            requested_action="read",
        )
        b = data["broker"]
        assert b["decision"] != "blocked_by_task_contract"

    def test_all_mutating_actions_require_task(self):
        tmp_root = Path("/tmp/pcae-88r-test-no-task")
        tmp_root.mkdir(exist_ok=True)
        for action in BPE_MUTATING_ACTIONS:
            data = build_permission_broker(
                repo_root=tmp_root,
                requested_action=action,
                health_passed=True,
                check_passed=True,
                push_check_passed=True,
            )
            b = data["broker"]
            assert b["decision"] == "blocked_by_task_contract", (
                f"action {action!r} should be blocked_by_task_contract without task"
            )


# ── Decision: shell gate hard blocks ──────────────────────────────────────

class TestShellGateHardBlocks:
    def test_force_push_command_blocked(self):
        b = _broker(command="git push --force")
        assert b["decision"] == "blocked_by_force_push"
        assert b["hard_block_present"] is True

    def test_force_push_short_flag(self):
        b = _broker(command="git push -f origin main")
        assert b["decision"] == "blocked_by_force_push"

    def test_raw_git_push_blocked(self):
        b = _broker(command="git push origin main")
        assert b["decision"] == "blocked_by_raw_git_push"
        assert b["hard_block_present"] is True

    def test_raw_git_commit_blocked(self):
        b = _broker(command="git commit -m 'message'")
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_history_rewrite_blocked(self):
        b = _broker(command="git rebase -i HEAD~3")
        assert b["decision"] == "blocked_by_shell_gate"
        assert b["hard_block_present"] is True

    def test_shell_gate_evidence_present_when_command_given(self):
        b = _broker(command="git push --force")
        assert b["shell_gate_evidence"] is not None
        assert b["shell_gate_evidence"]["command_text"] == "git push --force"

    def test_hard_block_takes_priority_over_missing_evidence(self):
        b = _broker("source_mutation", command="git push --force")
        assert b["decision"] == "blocked_by_force_push"

    def test_hard_block_takes_priority_over_no_task(self):
        tmp_root = Path("/tmp/pcae-88r-test-no-task")
        tmp_root.mkdir(exist_ok=True)
        data = build_permission_broker(
            repo_root=tmp_root,
            requested_action="source_mutation",
            requested_command="git push --force",
        )
        b = data["broker"]
        assert b["decision"] == "blocked_by_force_push"


# ── Decision: evidence failures ───────────────────────────────────────────

class TestEvidenceFailures:
    def test_health_failed_blocks(self):
        b = _broker("read", health_passed=False)
        assert b["decision"] == "blocked_by_failed_health"
        assert b["hard_block_present"] is True

    def test_check_failed_blocks(self):
        b = _broker("read", check_passed=False)
        assert b["decision"] == "blocked_by_failed_check"
        assert b["hard_block_present"] is True

    def test_doctor_failed_blocks(self):
        b = _broker("read", doctor_passed=False)
        assert b["decision"] == "blocked_by_failed_doctor"
        assert b["hard_block_present"] is True

    def test_tests_failed_blocks(self):
        b = _broker("read", tests_passed=False)
        assert b["decision"] == "blocked_by_failed_tests"
        assert b["hard_block_present"] is True

    def test_push_check_failed_blocks_push(self):
        b = _broker("push", health_passed=True, check_passed=True,
                    push_check_passed=False)
        assert b["decision"] == "blocked_by_push_check"
        assert b["hard_block_present"] is True

    def test_push_check_failed_does_not_block_non_push(self):
        b = _broker("source_mutation", files=["src/x.py"],
                    health_passed=True, check_passed=True,
                    push_check_passed=False)
        assert b["decision"] != "blocked_by_push_check"

    def test_health_failure_priority_over_missing_evidence(self):
        b = _broker("source_mutation", health_passed=False)
        assert b["decision"] == "blocked_by_failed_health"

    def test_health_failure_priority_over_task_contract(self):
        tmp_root = Path("/tmp/pcae-88r-test-no-task")
        tmp_root.mkdir(exist_ok=True)
        data = build_permission_broker(
            repo_root=tmp_root,
            requested_action="source_mutation",
            health_passed=False,
        )
        b = data["broker"]
        assert b["decision"] == "blocked_by_failed_health"


# ── Decision: scope preflight integration ─────────────────────────────────

class TestScopePreflight:
    def test_scope_decision_present_when_files_given(self):
        b = _broker("source_mutation", files=["src/x.py"],
                    health_passed=True, check_passed=True)
        # scope_preflight_decision is set (may be allow or blocked depending on contract)
        assert "scope_preflight_decision" in b

    def test_scope_decision_none_when_no_files(self):
        b = _broker("source_mutation", health_passed=True, check_passed=True)
        assert b["scope_preflight_decision"] is None

    def test_policy_forbidden_file_blocked_by_scope(self):
        b = _broker("source_mutation", files=["README.md"],
                    health_passed=True, check_passed=True)
        assert b["decision"] == "blocked_by_scope"
        assert b["hard_block_present"] is True

    def test_scope_evidence_source_recorded(self):
        b = _broker("source_mutation", files=["src/x.py"],
                    health_passed=True, check_passed=True)
        sources = b["evidence_sources"]
        assert any("scope" in s.lower() for s in sources)


# ── BPE constants ─────────────────────────────────────────────────────────

class TestBPEConstants:
    def test_decisions_tuple_has_24_values(self):
        assert len(BPE_DECISIONS) == 24

    def test_allow_preflight_only_in_decisions(self):
        assert "allow_preflight_only" in BPE_DECISIONS

    def test_hard_block_decisions_are_subset_of_decisions(self):
        assert BPE_HARD_BLOCK_DECISIONS.issubset(set(BPE_DECISIONS))

    def test_mutating_actions_non_empty(self):
        assert len(BPE_MUTATING_ACTIONS) > 0

    def test_read_not_in_mutating_actions(self):
        assert "read" not in BPE_MUTATING_ACTIONS


# ── Evidence provided passthrough ─────────────────────────────────────────

class TestEvidenceProvided:
    def test_health_passed_true_recorded(self):
        b = _broker(health_passed=True)
        assert b["evidence_provided"]["health_passed"] is True

    def test_health_passed_false_recorded(self):
        b = _broker(health_passed=False)
        assert b["evidence_provided"]["health_passed"] is False

    def test_health_passed_none_when_not_provided(self):
        b = _broker()
        assert b["evidence_provided"]["health_passed"] is None

    def test_human_review_present_recorded(self):
        b = _broker(human_review_present=True)
        assert b["evidence_provided"]["human_review_present"] is True

    def test_tests_present_recorded(self):
        b = _broker(tests_present=True)
        assert b["evidence_provided"]["tests_present"] is True

    def test_accepted_risk_present_recorded(self):
        b = _broker(accepted_risk_present=True)
        assert b["evidence_provided"]["accepted_risk_present"] is True


# ── CLI integration tests (subprocess) ────────────────────────────────────

@pytest.mark.slow
@pytest.mark.integration
class TestPermissionBrokerCLI:
    def _run(self, args: list[str]) -> dict[str, Any]:
        cmd = [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
               "--json"] + args
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        return json.loads(result.stdout)

    def test_cli_exits_successfully(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read", "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0

    def test_cli_output_is_valid_json(self):
        data = self._run(["--requested-action", "read"])
        assert isinstance(data, dict)

    def test_cli_schema_version(self):
        data = self._run(["--requested-action", "read"])
        assert data["schema_version"] == "0.1"

    def test_cli_source_command(self):
        data = self._run(["--requested-action", "read"])
        assert data["source_command"] == "pcae permission-broker evaluate"

    def test_cli_broker_key(self):
        data = self._run(["--requested-action", "read"])
        assert "broker" in data

    def test_cli_force_push_hard_block(self):
        data = self._run([
            "--requested-action", "read",
            "--requested-command", "git push --force",
        ])
        assert data["broker"]["decision"] == "blocked_by_force_push"
        assert data["broker"]["hard_block_present"] is True

    def test_cli_all_performed_flags_false(self):
        data = self._run(["--requested-action", "read"])
        b = data["broker"]
        for flag in _PERFORMED_FLAGS:
            assert b[flag] is False, f"{flag} must be False in CLI output"

    def test_cli_human_text_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "permission-broker", "evaluate",
             "--requested-action", "read"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        assert "permission broker" in result.stdout.lower()
        assert "decision" in result.stdout.lower()

    def test_cli_requested_file_passthrough(self):
        data = self._run([
            "--requested-action", "source_mutation",
            "--requested-file", "src/pcae/core/permission_broker.py",
            "--health-passed", "--check-passed",
        ])
        b = data["broker"]
        assert "src/pcae/core/permission_broker.py" in b["requested_files"]

    def test_cli_source_backend_passthrough(self):
        data = self._run([
            "--requested-action", "read",
            "--source-backend", "claude",
        ])
        assert data["broker"]["source_backend"] == "claude"
