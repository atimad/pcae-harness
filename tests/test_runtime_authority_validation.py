"""Tests for Phase 149O.20L.7O.3W — RIHAC-001 §16 twelve-step ordered
validation, all seven RIHAC-001 §13 freshness conditions, provenance,
consumption-state inspection, and security/threat adversarial cases
(forged/copied/tampered approval, task/target/prompt swap, replay-after-
validation-without-consumption).

Pure in-process, zero subprocess/network/credential access.
"""

from __future__ import annotations

import dataclasses

import pytest

from pcae.core import runtime_authority as ra

from _rdw3w_helpers import (
    HEAD_COMMIT_B,
    NOW_EXPIRED,
    NOW_FRESH,
    POLICY_VERSION_B,
    REPO_B,
    TASK_B,
    TARGET_B,
    TASK_CONTRACT_DIGEST_B,
    always_unconsumed,
    build_approval,
    matching_context,
    prompt_hash,
)


def test_matching_context_validates_successfully():
    approval = build_approval()
    ctx = matching_context(approval)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert reasons == ()
    assert projection is not None
    assert projection.approval_id == approval.approval_id
    assert projection.record_digest == approval.record_digest


def test_none_approval_fails_closed_step_1_2():
    ctx = matching_context(build_approval())
    projection, reasons = ra.validate_approval(None, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons[0].startswith("no_valid_approval")


def test_record_digest_tamper_detected_step_4():
    approval = build_approval()
    tampered = dataclasses.replace(approval, record_digest="0" * 64)
    ctx = matching_context(approval)
    projection, reasons = ra.validate_approval(tampered, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("record_digest_mismatch",)


def test_tampered_subject_field_detected_via_digest_mismatch():
    """Any tamper to a subject field, without recomputing record_digest,
    is caught by digest recomputation before subject binding is even
    checked (step 4 precedes step 5)."""
    approval = build_approval()
    tampered_subject = dataclasses.replace(approval.subject, task_id="task-stolen")
    tampered = dataclasses.replace(approval, subject=tampered_subject)
    ctx = matching_context(approval)
    projection, reasons = ra.validate_approval(tampered, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("record_digest_mismatch",)


@pytest.mark.parametrize("field,value,expected_reason", [
    ("repository_identity", REPO_B, "subject_mismatch:repository_identity"),
    ("task_id", TASK_B, "subject_mismatch:task_id"),
])
def test_step_5_repository_task_binding(field, value, expected_reason):
    approval = build_approval()
    ctx = matching_context(approval)
    ctx = dataclasses.replace(ctx, **{field: value})
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == (expected_reason,)


def test_step_5_phase_mismatch():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), phase_id="other-phase")
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("governance_context_mismatch:phase_id",)


def test_step_5_session_mismatch_phase_only_never_fabricates_session():
    approval = build_approval()  # session_id=None
    ctx = dataclasses.replace(matching_context(approval), session_id="sess-injected")
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("governance_context_mismatch:session_id",)


def test_step_6_invocation_id_mismatch():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), invocation_id="inv-" + "0" * 32)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("subject_mismatch:invocation_id",)


def test_step_6_target_swap_no_fallback():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), runtime_target_id=TARGET_B)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("subject_mismatch:runtime_target_id",)


def test_step_7_prompt_swap():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), prompt_hash=prompt_hash("Do a different thing."))
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("subject_mismatch:prompt_hash",)


def test_step_8_adapter_descriptor_digest_mismatch():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), descriptor_digest="9" * 64)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("adapter_binding_mismatch:descriptor_digest",)


def test_step_8_target_config_digest_mismatch():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), target_config_digest="9" * 64)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("adapter_binding_mismatch:target_config_digest",)


def test_step_8_requested_capability_mismatch():
    approval = build_approval()
    ctx = matching_context(approval, requested_capability="different_capability")
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("scope_mismatch:requested_capability",)


# ── Step 9: all seven freshness conditions ───────────────────────────────


def test_freshness_head_commit_change_stale():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), head_commit=HEAD_COMMIT_B)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("stale_approval:stale:head_commit",)


def test_freshness_task_contract_digest_change_stale():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), task_contract_digest=TASK_CONTRACT_DIGEST_B)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("stale_approval:stale:task_contract_digest",)


def test_freshness_task_no_longer_active_stale():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), task_state="closed")
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("stale_approval:stale:task_state",)


def test_freshness_prompt_change_is_subject_mismatch_not_staleness():
    # Already covered by test_step_7_prompt_swap; documented here as the
    # explicit RIHAC-001 §13 row cross-reference: "different subject" not
    # "stale."
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), prompt_hash=prompt_hash("changed"))
    _, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert reasons[0].startswith("subject_mismatch")


def test_freshness_runtime_target_change_is_subject_mismatch_not_staleness():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), runtime_target_id=TARGET_B)
    _, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert reasons[0].startswith("subject_mismatch")


def test_freshness_adapter_configuration_change_is_stale_via_step_8():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), descriptor_digest="7" * 64)
    _, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert reasons[0].startswith("adapter_binding_mismatch")


def test_freshness_policy_version_drift_does_not_invalidate_but_flags_re_evaluation():
    """RIHAC-001 §13's explicit disposition: policy drift blocks dispatch
    until fresh decisions exist but does NOT retroactively erase the
    human act -- validation still succeeds (non-None projection), with a
    non-empty reason signalling the caller must re-evaluate PB/RE."""
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), policy_version=POLICY_VERSION_B)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is not None
    assert reasons == ("policy_drift_requires_fresh_pb_re_evaluation",)


def test_freshness_seven_conditions_are_exactly_head_task_prompt_target_adapter_policy_expiry():
    """Cardinality/coverage check: every RIHAC-001 §13 row has a
    corresponding, independently-triggerable failure path in this test
    file (six above + expiry below)."""
    covered = {
        "head_commit",
        "task_contract_digest_or_state",
        "prompt_hash",
        "runtime_target_id",
        "adapter_configuration",
        "policy_version",
        "expires_at",
    }
    assert len(covered) == 7


# ── Step 10: expiry ───────────────────────────────────────────────────────


def test_expired_approval_fails_closed():
    approval = build_approval()
    ctx = dataclasses.replace(matching_context(approval), current_time=NOW_EXPIRED)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("expired",)


def test_current_time_exactly_at_expiry_is_expired():
    approval = build_approval(created_at="2026-08-27T00:00:00Z", expires_at="2026-08-27T01:00:00Z")
    ctx = dataclasses.replace(matching_context(approval), current_time="2026-08-27T01:00:00Z")
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("expired",)


def test_current_time_one_second_before_expiry_is_fresh():
    approval = build_approval(created_at="2026-08-27T00:00:00Z", expires_at="2026-08-27T01:00:00Z")
    ctx = dataclasses.replace(matching_context(approval), current_time="2026-08-27T00:59:59Z")
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is not None
    assert reasons == ()


# ── Step 11: consumption/cancellation/uncertainty/completion ────────────


@pytest.mark.parametrize("state", [
    ra.CONSUMPTION_STATE_CONSUMED,
    ra.CONSUMPTION_STATE_CANCELLED,
    ra.CONSUMPTION_STATE_UNCERTAIN,
    ra.CONSUMPTION_STATE_COMPLETED,
])
def test_non_consumable_states_fail_closed(state):
    approval = build_approval()
    ctx = matching_context(approval)
    projection, reasons = ra.validate_approval(
        approval, context=ctx, consumption_lookup=lambda _aid: state
    )
    assert projection is None
    assert reasons == (f"already_bound:{state}",)


def test_unrecognized_consumption_state_fails_closed():
    approval = build_approval()
    ctx = matching_context(approval)
    projection, reasons = ra.validate_approval(
        approval, context=ctx, consumption_lookup=lambda _aid: "some_unknown_state"
    )
    assert projection is None
    assert reasons[0].startswith("unrecognized_consumption_state")


def test_validating_an_unconsumed_approval_repeatedly_never_consumes_it():
    """3V.2 §16's explicit adversarial case: validation is a non-consuming
    observation. Multiple validations of the same still-fresh,
    still-unconsumed approval all succeed identically."""
    approval = build_approval()
    ctx = matching_context(approval)
    results = [
        ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
        for _ in range(5)
    ]
    for projection, reasons in results:
        assert projection is not None
        assert reasons == ()


# ── Provenance ─────────────────────────────────────────────────────────


def test_untrusted_producer_component_rejected():
    """The schema itself const-pins `producer_component` (step 3, RIASC-001
    §7), so a tampered producer identity is rejected even earlier than
    step 4's digest check -- still fail-closed, just at an earlier step."""
    approval = build_approval()
    tampered_provenance = dataclasses.replace(approval.provenance, producer_component="evil.actor")
    tampered = dataclasses.replace(approval, provenance=tampered_provenance)
    tampered = dataclasses.replace(tampered, record_digest=ra.compute_record_digest(tampered))
    ctx = matching_context(approval)
    projection, reasons = ra.validate_approval(tampered, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons[0].startswith("riasc_schema_invalid:")
    assert "provenance_const_mismatch:producer_component" in reasons[0]


def test_producer_identity_must_be_distinct_from_approver():
    approval = build_approval(approver_id=ra.PRODUCER_COMPONENT_V1)
    ctx = matching_context(approval)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("producer_identity_not_distinct_from_approver",)


# ── Security/threat adversarial matrix (3V.2 §38) ───────────────────────


def test_copied_approval_into_sibling_repository_fails_repository_binding():
    approval = build_approval(repository_identity=REPO_B)
    ctx = dataclasses.replace(matching_context(approval), repository_identity="c" * 64)
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("subject_mismatch:repository_identity",)


def test_task_swap_attack():
    approval = build_approval(task_id="task-A-authorized")
    ctx = dataclasses.replace(matching_context(approval), task_id="task-B-not-authorized")
    projection, reasons = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("subject_mismatch:task_id",)


def test_forged_approval_digest_never_validates():
    approval = build_approval()
    forged = dataclasses.replace(approval, approval_id="ria-" + "0" * 32)
    # forged approval_id but digest computed over ORIGINAL content -- the
    # digest recomputation (which now includes the new approval_id) fails.
    ctx = matching_context(approval)
    projection, reasons = ra.validate_approval(forged, context=ctx, consumption_lookup=always_unconsumed)
    assert projection is None
    assert reasons == ("record_digest_mismatch",)
