"""Tests for Phase 149F — Repository-Wide Mutation Permission Coverage
Wave 1: the shared primitive (`pcae.core.mutation_permission`).

Verifies `evaluate_repository_mutation_permission`'s ALLOW-only
consumption rule in isolation from any specific adapter: DENY/
HUMAN_REVIEW/broker-construction-exception/broker-evaluation-exception/
malformed-result all fail closed; POL-001 (missing task) DENY; POL-005
direct-Foundation control case (`simulation_only=False` -> DENY,
Foundation-level only, never reachable via any Wave-1 adapter); no
caller-selectable `action_type`/`execution_class`/policy set exists on
any adapter's public surface.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.core import mutation_permission as mp
from pcae.core import permission_broker_foundation as pbf
from pcae.core.paths import HarnessPath

REPO_ROOT = Path(__file__).resolve().parent.parent


def _real_repo(tmp_path: Path) -> HarnessPath:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True, capture_output=True)
    return HarnessPath(tmp_path)


# ── ALLOW-only consumption ──────────────────────────────────────────────


def test_allow_decision_is_authorized(tmp_path):
    root = _real_repo(tmp_path)
    result = mp.evaluate_repository_mutation_permission(
        root=root,
        action_type=pbf.ACTION_COMMIT,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_remote_commit",
        task_id="task-1",
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    assert result.authorized is True
    assert result.decision.decision == pbf.DECISION_ALLOW
    assert result.broker_failure_reason is None


def test_deny_decision_is_not_authorized(tmp_path):
    root = _real_repo(tmp_path)
    # POL-001 (MissingTaskContextRule) denies when task_id is None for
    # a MUTATION-class request that requires task identity.
    result = mp.evaluate_repository_mutation_permission(
        root=root,
        action_type=pbf.ACTION_COMMIT,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_remote_commit",
        task_id=None,
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    assert result.authorized is False
    assert result.decision is not None
    assert result.decision.decision in (pbf.DECISION_DENY, pbf.DECISION_HUMAN_REVIEW)


def test_human_review_decision_is_not_authorized(tmp_path):
    root = _real_repo(tmp_path)
    calls = {"count": 0}

    def fake_evaluate(self, request):
        calls["count"] += 1
        return pbf.PermissionBrokerDecision(
            decision=pbf.DECISION_HUMAN_REVIEW,
            decision_reason="forced_human_review",
            matched_no_go_ids=(),
            matched_invariants=(),
            required_remediation=(),
            requires_human=True,
            simulation_only=True,
        )

    import pytest as _pytest
    mpatch = _pytest.MonkeyPatch()
    mpatch.setattr(pbf.PermissionBroker, "evaluate", fake_evaluate)
    try:
        result = mp.evaluate_repository_mutation_permission(
            root=root,
            action_type=pbf.ACTION_COMMIT,
            execution_class=pbf.EXECUTION_CLASS_MUTATION,
            requested_component="COMP-001",
            requested_capability="pcae_remote_commit",
            task_id="task-1",
            requested_resource=None,
            evidence_available=True,
            approval_present=False,
            simulation_only=True,
        )
    finally:
        mpatch.undo()
    assert calls["count"] == 1
    assert result.authorized is False
    assert result.decision.decision == pbf.DECISION_HUMAN_REVIEW


def test_broker_construction_exception_fails_closed(tmp_path, monkeypatch):
    root = _real_repo(tmp_path)

    class _ExplodingBroker:
        def __init__(self):
            raise RuntimeError("construction failed")

    monkeypatch.setattr(pbf, "PermissionBroker", _ExplodingBroker)
    result = mp.evaluate_repository_mutation_permission(
        root=root,
        action_type=pbf.ACTION_COMMIT,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_remote_commit",
        task_id="task-1",
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    assert result.authorized is False
    assert result.decision is None
    assert "construction failed" in result.broker_failure_reason


def test_broker_evaluation_exception_fails_closed(tmp_path, monkeypatch):
    root = _real_repo(tmp_path)

    def exploding_evaluate(self, request):
        raise RuntimeError("evaluation failed")

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", exploding_evaluate)
    result = mp.evaluate_repository_mutation_permission(
        root=root,
        action_type=pbf.ACTION_COMMIT,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_remote_commit",
        task_id="task-1",
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    assert result.authorized is False
    assert result.decision is None
    assert "evaluation failed" in result.broker_failure_reason


def test_malformed_broker_result_fails_closed(tmp_path, monkeypatch):
    root = _real_repo(tmp_path)

    def malformed_evaluate(self, request):
        class _FakeAllow:
            decision = pbf.DECISION_ALLOW

        return _FakeAllow()

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", malformed_evaluate)
    result = mp.evaluate_repository_mutation_permission(
        root=root,
        action_type=pbf.ACTION_COMMIT,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_remote_commit",
        task_id="task-1",
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    assert result.authorized is False
    assert result.decision is None
    assert result.broker_failure_reason == "invalid_broker_result"


def test_pol005_simulation_only_false_denies(tmp_path):
    """RWMPC-REQ-015: `simulation_only=False` unconditionally triggers
    POL-005 DENY at the Foundation level. No Wave-1 adapter ever passes
    `simulation_only=False` (verified separately, below) -- this is a
    direct Foundation-level control case only."""
    root = _real_repo(tmp_path)
    result = mp.evaluate_repository_mutation_permission(
        root=root,
        action_type=pbf.ACTION_COMMIT,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_remote_commit",
        task_id="task-1",
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=False,
    )
    assert result.authorized is False
    assert result.decision.decision == pbf.DECISION_DENY


def test_pol004_not_applicable_to_mutation_class():
    """RWMPC-REQ-017: POL-004 is scoped to
    {SHELL, BACKEND, ADAPTER, ROLLBACK}; MUTATION is excluded."""
    from pcae.core.permission_broker_foundation import MissingHumanApprovalRule

    rule = MissingHumanApprovalRule()
    assert pbf.EXECUTION_CLASS_MUTATION not in rule.applicable_execution_classes
    assert pbf.EXECUTION_CLASS_ROLLBACK in rule.applicable_execution_classes


# ── No caller-selectable classification (RWMPC-REQ-016) ────────────────


@pytest.mark.parametrize(
    "adapter",
    [
        mp.evaluate_commit_permission,
        mp.evaluate_alternate_push_permission,
        mp.evaluate_promotion_permission,
        mp.evaluate_repository_mutation_permission,
    ],
)
def test_no_adapter_exposes_execution_class_or_policy_selection_parameter(adapter):
    signature = inspect.signature(adapter)
    forbidden = {
        "execution_class_override",
        "policy_ids",
        "exclude_policy",
        "exclude_policies",
        "skip_policy",
        "selected_policy_ids",
        "policy_profile",
        "registry_override",
    }
    assert forbidden.isdisjoint(signature.parameters), (
        f"{adapter.__name__} exposes a caller-selectable classification/policy parameter"
    )


def test_evaluate_repository_mutation_permission_is_only_request_constructor():
    """RWMPC-REQ-013: this module is the only place in the codebase
    permitted to construct a `PermissionBrokerRequest` for a non-`pcae
    push` mutation site."""
    source = Path(mp.__file__).read_text(encoding="utf-8")
    assert source.count("build_permission_broker_request(") == 1


def test_action_type_and_execution_class_are_hardcoded_literals_not_parameters():
    """Per-class adapters must not thread action_type/execution_class as
    caller-supplied parameters (RWMPC-REQ-016)."""
    for adapter in (
        mp.evaluate_commit_permission,
        mp.evaluate_alternate_push_permission,
    ):
        signature = inspect.signature(adapter)
        assert "action_type" not in signature.parameters
        assert "execution_class" not in signature.parameters
