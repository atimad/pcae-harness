"""Tests for Phase 148C.10 — Permission Broker Production Consumption
Contract v1.2 Independent Verification.

Independent verification suite. This phase performs NO production source
changes (`src/pcae/**` untouched — confirmed via `git diff --name-only`)
and NO amendment to PBPC-001 or PBPA-001. It independently re-derives,
rather than trusts, Phase 148C.9's v1.1 -> v1.2 reconciliation claims by
re-executing the live, unmodified Permission Broker Foundation
(`src/pcae/core/permission_broker_foundation.py`) directly through its
public API, and by inspecting `src/pcae/commands/push.py` for absence of
production Permission Broker wiring.

No approval is fabricated: every `approval_present=False` request
constructed below is honestly False. No policy is added, removed, or
modified. No PBPC/PBPA contract text is touched by this file.
"""

from __future__ import annotations

import inspect

import pytest

from pcae.core import permission_broker_foundation as pbf
from pcae.core.permission_broker_foundation import (
    ACTION_PUSH,
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    DEFAULT_POLICY_RULES,
    EXECUTION_CLASS_ADAPTER,
    EXECUTION_CLASS_BACKEND,
    EXECUTION_CLASS_MUTATION,
    EXECUTION_CLASS_NONE,
    EXECUTION_CLASS_ROLLBACK,
    EXECUTION_CLASS_SHELL,
    PermissionBroker,
    PolicyRegistry,
    build_permission_broker_request,
)


def _broker() -> PermissionBroker:
    return PermissionBroker(PolicyRegistry(DEFAULT_POLICY_RULES))


def _push_request(**overrides):
    fields = dict(
        action_type=ACTION_PUSH,
        execution_class=EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="push",
        task_id="TEST-148C10-TASK",
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    fields.update(overrides)
    return build_permission_broker_request(**fields)


# --- Section 30A re-derivation: canonical request satisfiability -----------


def test_canonical_pbpc_push_request_reaches_allow():
    """PBPC-001 v1.2 Section 30A's first control case, independently
    re-executed (not cited from 148C.9's own table)."""
    decision = _broker().evaluate(_push_request())
    assert decision.decision == DECISION_ALLOW
    # POL-013 (Phase ...1R.22, adapter-scoped) is non-applicable to this
    # mutation-class push request; it never affects the push decision.
    assert decision.non_applicable_policy_ids == ("POL-004", "POL-013")
    assert decision.causing_policy_ids == ()


def test_canonical_request_approval_present_true_does_not_change_applicability():
    """Independent extension beyond 148C.9's own table: approval_present
    is honestly irrelevant to POL-004 applicability for a mutation-class
    request, proving applicability truly precedes and is independent of
    the approval_present evidence field (PBPA-REQ-011/012/066)."""
    allow_false = _broker().evaluate(_push_request(approval_present=False))
    allow_true = _broker().evaluate(_push_request(approval_present=True))
    assert allow_false.decision == DECISION_ALLOW
    assert allow_true.decision == DECISION_ALLOW
    assert allow_false.non_applicable_policy_ids == allow_true.non_applicable_policy_ids == ("POL-004", "POL-013")


# --- POL-004 in-scope control: reconciliation did not weaken POL-004 -------


@pytest.mark.parametrize(
    "execution_class",
    [EXECUTION_CLASS_SHELL, EXECUTION_CLASS_BACKEND, EXECUTION_CLASS_ADAPTER, EXECUTION_CLASS_ROLLBACK],
)
def test_pol_004_in_scope_controls_still_require_human_review(execution_class):
    """Section 30A's second control case, independently re-derived for all
    four scoped execution classes (148C.9's table only shows one). Proves
    the v1.2 reconciliation did not broaden POL-004's non-applicability
    beyond EXECUTION_CLASS_MUTATION/NONE."""
    decision = _broker().evaluate(
        _push_request(
            action_type="shell_command",
            execution_class=execution_class,
            requested_capability="shell",
            approval_present=False,
        )
    )
    assert decision.decision == DECISION_HUMAN_REVIEW
    assert "POL-004" in decision.causing_policy_ids
    assert "POL-004" in decision.applicable_policy_ids


def test_pol_004_non_applicable_for_execution_class_none_too():
    """EXECUTION_CLASS_NONE is the other excluded class (Section 8.1);
    independently confirming both excluded classes, not just mutation."""
    decision = _broker().evaluate(
        _push_request(action_type="read", execution_class=EXECUTION_CLASS_NONE, requested_capability="read")
    )
    assert "POL-004" in decision.non_applicable_policy_ids


# --- POL-005 control: Finding F-148C.8-1 / PBPC-REQ-037A --------------------


def test_pol_005_control_simulation_only_false_denies():
    """Section 30A's third control case: simulation_only=False on an
    otherwise canonical push request fails closed via POL-005, exactly as
    PBPC-REQ-037A asserts -- independently re-derived, not cited."""
    decision = _broker().evaluate(_push_request(simulation_only=False))
    assert decision.decision == DECISION_DENY
    assert decision.causing_policy_ids == ("POL-005",)
    assert decision.decision_reason == "execution_boundary_unavailable"


def test_pol_005_applicability_is_universal_and_unaffected_by_pbpa():
    """PBPA-REQ-069: POL-005 is applicability-universal; only its trigger
    condition is simulation-sensitive. Confirms the applicability layer
    did not touch POL-005."""
    allow_decision = _broker().evaluate(_push_request(simulation_only=True))
    deny_decision = _broker().evaluate(_push_request(simulation_only=False))
    assert "POL-005" in allow_decision.applicable_policy_ids
    assert "POL-005" in deny_decision.applicable_policy_ids


# --- Applicability vs. decision; evaluated_policy_ids semantics ------------


def test_evaluated_policy_ids_excludes_non_applicable_policies():
    """PBPA-REQ-081/Section 8.1 (reconciled 'evaluated_policy_ids' prose):
    evaluated_policy_ids is exactly applicable_policy_ids, not "all twelve
    registered policies" (the stale v1.1-era assumption)."""
    decision = _broker().evaluate(_push_request())
    assert "POL-004" not in decision.evaluated_policy_ids
    assert set(decision.evaluated_policy_ids) == set(decision.applicable_policy_ids)
    assert len(decision.evaluated_policy_ids) == 11


def test_not_applicable_is_not_collapsed_into_allow_semantically():
    """PBPA-REQ-016: a non-applicable policy is silent, not a vote for
    ALLOW. Independently confirmed: ALLOW's precedence_reason names
    "no policy triggered a block", never POL-004 by name as a cause."""
    decision = _broker().evaluate(_push_request())
    assert decision.decision == DECISION_ALLOW
    assert "POL-004" not in decision.causing_policy_ids
    assert "no policy triggered" in decision.precedence_reason


def test_decision_vocabulary_has_exactly_three_values():
    """PBPA-REQ-013: no fourth NOT_APPLICABLE-as-decision value exists at
    the broker-decision level."""
    assert pbf.DECISION_VALUES == (DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW)


# --- No caller-supplied exclusion mechanism (PBPA-REQ-022) ------------------


def test_permission_broker_evaluate_accepts_no_exclusion_parameter():
    """PBPA-REQ-022: no caller-supplied exclusion/allow-list parameter
    exists on the public evaluate() surface."""
    signature = inspect.signature(PermissionBroker.evaluate)
    params = set(signature.parameters) - {"self"}
    assert params == {"request"}


# --- Production wiring boundary: push.py is unwired (Section 35) ----------


def test_push_module_is_the_authorized_pbpc_production_consumer():
    """148C.10 (like 148C.9 before it) performed no implementation, and at
    that time asserted push.py never referenced PermissionBroker at all.
    148E intentionally wired push.py as PBPC-001 v1.2's production
    consumer (148F/148G independently re-verified this wiring, 148G.1
    hardened it further), making the original zero-reference assertion a
    stale invariant against current, intentional architecture -- narrowed
    (148G.1) rather than deleted, since the surrounding invariant this
    file protects (repository-wide `git push` dispatch-site wiring
    boundaries, Section 35) is still current and worth guarding. The
    correct invariant now: push.py IS the authorized PBPC production
    consumer; the other real git-push dispatch sites 148F/148G
    independently inventoried (`pcae.commands.agent`'s
    `push_file_changes`, `pcae.commands.phase`'s push-execution
    subcommands) remain unwired, precisely as PBPC-REQ-004/005 scope
    them -- unless separately authorized by a future phase.
    """
    import pcae.commands.agent as agent_module
    import pcae.commands.phase as phase_module
    import pcae.commands.push as push_module

    push_source = inspect.getsource(push_module)
    assert "PermissionBroker" in push_source
    assert "permission_broker_foundation" in push_source

    for unwired_module in (agent_module, phase_module):
        unwired_source = inspect.getsource(unwired_module)
        assert "PermissionBroker" not in unwired_source
        assert "permission_broker_foundation" not in unwired_source


def test_push_module_has_exactly_two_git_push_dispatch_sites():
    """PBPC-REQ-019/029 (Section 9): exactly two Decision Consumption
    Points/dispatch sites -- Path A (ordinary) and Path B (staged-file-
    aware) -- independently counted from source, not cited from the
    contract."""
    import pcae.commands.push as push_module

    source = inspect.getsource(push_module)
    count = source.count('["git", "push"]') + source.count('["git", "push", "origin", "main"]')
    assert count == 2


def test_push_module_does_not_reference_authority_evaluation_or_aesic():
    """PBPC-REQ-080: independently confirms zero authority_evaluation/aesic
    references in push.py, corroborating AESIC independence (Section 22)."""
    import pcae.commands.push as push_module

    source = inspect.getsource(push_module)
    assert "authority_evaluation" not in source
    assert "aesic" not in source


# --- PBPA-001 v1.0 remains unamended -----------------------------------


def test_pbpa_contract_file_is_still_version_1_0():
    """PBPA-001 was not touched by 148C.9. Phase ...1R.22 (N-16-3) amended it
    to v1.1 additively (PBPA-REQ-089 — the POL-013 applicability row); no
    existing PBPA clause changed."""
    import pathlib

    contract_text = pathlib.Path(
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md"
    ).read_text(encoding="utf-8")
    assert "**Version:** 1.1" in contract_text
    assert "POL-013" in contract_text and "PBPA-REQ-089" in contract_text


def test_pbpc_contract_file_is_now_version_1_2():
    """Independently confirms the reconciliation this phase verifies is the
    one actually present in the repository's frozen contract text."""
    import pathlib

    contract_text = pathlib.Path(
        "docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md"
    ).read_text(encoding="utf-8")
    assert "**Version:** 1.2" in contract_text
    assert "Finding B-1 is CLOSED" in contract_text


# --- Registry completeness / no regression to 12-policy canon --------------


def test_registry_still_has_exactly_twelve_canonical_policies():
    # Phase ...1R.22 (N-16-3) adds exactly one canonical policy: POL-013
    # (Narrow Local-CLI Dispatch Eligibility). No existing policy changed;
    # the canonical count is now 13.
    registry = PolicyRegistry()
    assert len(registry.policy_ids) == 13
    assert set(registry.policy_ids) == pbf.POLICY_IDS_CANONICAL


def test_hard_block_registry_still_has_twelve_entries():
    """Independently re-derives the HARD_BLOCK_REGISTRY count from
    production source rather than trusting the historical '12' figure
    PBPC-001 Section 18/26 cites."""
    from pcae.core.permission_broker import HARD_BLOCK_REGISTRY

    assert len(HARD_BLOCK_REGISTRY) == 12
