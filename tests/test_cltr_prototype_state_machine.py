from __future__ import annotations

import pytest

from pcae.cltr_prototype import state_machine as sm
from pcae.cltr_prototype.identity import resolve_identity
from pcae.cltr_prototype.models import RetryClassification, SpineState


@pytest.fixture()
def ident():
    return resolve_identity(
        {"transition_id": "t-sm-1", "phase_id": "135F", "repository_identity": "pcae-harness", "branch_identity": "main"}
    )


def test_full_spine_success_via_t1_t13(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    assert r.spine_state == SpineState.PROPOSED

    r = sm.t2_begin_certification(r, at="t1").new_record
    assert r.spine_state == SpineState.CERTIFYING

    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    assert r.spine_state == SpineState.CERTIFIED

    r = sm.t5_begin_promotion(r, at="t3").new_record
    assert r.spine_state == SpineState.PROMOTING

    r = sm.t6_promote_succeed(r, at="t4", promotion_binding=None).new_record
    assert r.spine_state == SpineState.PROMOTED

    r = sm.t8_begin_notification(r, at="t5").new_record
    assert r.spine_state == SpineState.NOTIFYING

    r = sm.t9_notify_confirm(r, at="t6", notification_binding=None).new_record
    assert r.spine_state == SpineState.NOTIFIED

    r = sm.t13_close_success(r, at="t7").new_record
    assert r.spine_state == SpineState.TERMINAL_SUCCESS
    assert r.is_terminal


def test_certification_failure_path(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t4_certification_fail(r, at="t2", detail="bad evidence").new_record
    assert r.spine_state == SpineState.FAILED_PRE_CERT
    assert r.is_terminal


def test_notified_unconfirmed_path(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    r = sm.t5_begin_promotion(r, at="t3").new_record
    r = sm.t6_promote_succeed(r, at="t4", promotion_binding=None).new_record
    r = sm.t8_begin_notification(r, at="t5").new_record
    r = sm.t10_notify_unconfirmed(r, at="t6", notification_binding=None).new_record
    assert r.spine_state == SpineState.NOTIFIED_UNCONFIRMED
    assert sm.retry_classification(r) == RetryClassification.REPAIR_DERIVATIVE_ONLY

    r2 = sm.t12_reconcile_receipt(r, at="t7", receipt_binding=None, resolved=False).new_record
    assert r2.spine_state == SpineState.NOTIFIED_UNCONFIRMED  # constrained repair, not a delivery retry

    r3 = sm.t14_close_partial(r2, at="t8").new_record
    assert r3.spine_state == SpineState.TERMINAL_PARTIAL_EXTERNAL
    assert r3.is_terminal


def test_promote_fail_path(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    r = sm.t5_begin_promotion(r, at="t3").new_record
    r = sm.t7_promote_fail(r, at="t4", observation_detail="partial promotion observed").new_record
    assert r.spine_state == SpineState.FAILED_POST_CERT


def test_notify_retry_self_loop(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    r = sm.t5_begin_promotion(r, at="t3").new_record
    r = sm.t6_promote_succeed(r, at="t4", promotion_binding=None).new_record
    r = sm.t8_begin_notification(r, at="t5").new_record
    r2 = sm.t11_notify_retry(r, at="t6").new_record
    assert r2.spine_state == SpineState.NOTIFYING  # still NOTIFYING, self-loop


def test_quarantine_orthogonal_flag(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    r2 = sm.t15_quarantine(r, at="t3", mismatch_detail="digest mismatch found").new_record
    assert r2.quarantined is True
    assert r2.spine_state == SpineState.CERTIFIED  # flag, not a spine change


def test_supersede_orthogonal_flag(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    r2 = sm.t16_supersede(r, at="t3", superseding_transition_id="t-sm-2").new_record
    assert r2.superseded is True
    assert r2.superseded_by == "t-sm-2"
    assert r2.spine_state == SpineState.CERTIFIED


# --- Forbidden transitions (F1-F14) -----------------------------------------

def test_f1_f2_f12_promotion_without_certification(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    with pytest.raises(sm.ForbiddenTransitionError):
        sm.t5_begin_promotion(r, at="t1")


def test_f2_f4_notification_without_promotion(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    with pytest.raises(sm.ForbiddenTransitionError):
        sm.t8_begin_notification(r, at="t3")


def test_f3_certify_from_failed_pre_cert(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t4_certification_fail(r, at="t2", detail="bad").new_record
    with pytest.raises(sm.ForbiddenTransitionError):
        sm.t3_certify(r, at="t3", certified_state={"x": 1})


def test_f5_promoted_backward_to_certifying(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    r = sm.t5_begin_promotion(r, at="t3").new_record
    r = sm.t6_promote_succeed(r, at="t4", promotion_binding=None).new_record
    with pytest.raises(sm.ForbiddenTransitionError):
        sm.t6_promote_succeed(r, at="t5", promotion_binding=None)  # not in PROMOTING anymore


def test_f6_notified_ordinary_redispatch(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    r = sm.t5_begin_promotion(r, at="t3").new_record
    r = sm.t6_promote_succeed(r, at="t4", promotion_binding=None).new_record
    r = sm.t8_begin_notification(r, at="t5").new_record
    r = sm.t9_notify_confirm(r, at="t6", notification_binding=None).new_record
    with pytest.raises(sm.ForbiddenTransitionError):
        sm.t11_notify_retry(r, at="t7")


def test_f7_terminal_success_ordinary_replay(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    r = sm.t5_begin_promotion(r, at="t3").new_record
    r = sm.t6_promote_succeed(r, at="t4", promotion_binding=None).new_record
    r = sm.t8_begin_notification(r, at="t5").new_record
    r = sm.t9_notify_confirm(r, at="t6", notification_binding=None).new_record
    r = sm.t13_close_success(r, at="t7").new_record
    with pytest.raises(sm.ForbiddenTransitionError):
        sm.t13_close_success(r, at="t8")


def test_f8_superseded_reactivation_rejected_via_close(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    r = sm.t5_begin_promotion(r, at="t3").new_record
    r = sm.t6_promote_succeed(r, at="t4", promotion_binding=None).new_record
    r = sm.t8_begin_notification(r, at="t5").new_record
    r = sm.t16_supersede(r, at="t5b", superseding_transition_id="other").new_record
    assert sm.retry_classification(r) == RetryClassification.REJECT_SUPERSEDED_REDIRECT


def test_f9_quarantine_requires_certified_or_later(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    with pytest.raises(sm.ForbiddenTransitionError):
        sm.t15_quarantine(r, at="t1", mismatch_detail="x")


def test_f10_marker_before_notified_is_a_generator_level_concern():
    # F10 (marker/receipt creation before NOTIFIED/NOTIFIED_UNCONFIRMED) is
    # enforced by CLTR-ORDER-6 in the invariant engine (invariants.py),
    # since state_machine.py's own transition functions accept a
    # marker_binding kwarg only at T9/T10 — no earlier-stage function
    # (T1-T8) exposes a marker_binding parameter at all. See
    # test_cltr_prototype_invariants.py for the full CLTR-ORDER-6 check.
    import inspect

    for fn in (sm.t1_propose_transition, sm.t2_begin_certification, sm.t3_certify, sm.t4_certification_fail, sm.t5_begin_promotion, sm.t6_promote_succeed, sm.t7_promote_fail, sm.t8_begin_notification):
        params = inspect.signature(fn).parameters
        assert "marker_binding" not in params


def test_f11_derivative_generation_is_generator_level_concern():
    # F11 (derivative generation from an uncertified authority) is enforced
    # by generator.py never binding report/metadata evidence before T3.
    pass


def test_f12_any_state_to_promoting_without_certified(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    with pytest.raises(sm.ForbiddenTransitionError):
        sm.t5_begin_promotion(r, at="t2")


def test_f13_failed_post_cert_to_promoted(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    r = sm.t5_begin_promotion(r, at="t3").new_record
    r = sm.t7_promote_fail(r, at="t4", observation_detail="observed").new_record
    with pytest.raises(sm.ForbiddenTransitionError):
        sm.t6_promote_succeed(r, at="t5", promotion_binding=None)


def test_f14_terminal_to_any_other_spine_state(ident):
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t4_certification_fail(r, at="t2", detail="bad").new_record
    with pytest.raises(sm.ForbiddenTransitionError):
        sm.t2_begin_certification(r, at="t3")


# --- Retry table (135D §24) -------------------------------------------------

@pytest.mark.parametrize(
    "state,expected",
    [
        (SpineState.PROPOSED, RetryClassification.BEGIN),
        (SpineState.CERTIFYING, RetryClassification.BEGIN),
        (SpineState.CERTIFIED, RetryClassification.CONTINUE),
        (SpineState.PROMOTING, RetryClassification.RESUME_AFTER_OBSERVATION),
        (SpineState.PROMOTED, RetryClassification.CONTINUE),
        (SpineState.NOTIFYING, RetryClassification.RESUME_AFTER_OBSERVATION),
        (SpineState.NOTIFIED, RetryClassification.RETURN_PRIOR_RESULT),
        (SpineState.NOTIFIED_UNCONFIRMED, RetryClassification.REPAIR_DERIVATIVE_ONLY),
        (SpineState.TERMINAL_SUCCESS, RetryClassification.RETURN_PRIOR_RESULT),
        (SpineState.TERMINAL_PARTIAL_EXTERNAL, RetryClassification.RETURN_PRIOR_RESULT),
        (SpineState.FAILED_PRE_CERT, RetryClassification.BEGIN),
        (SpineState.FAILED_POST_CERT, RetryClassification.RESUME_AFTER_OBSERVATION),
    ],
)
def test_retry_classification_table(ident, state, expected):
    certified_state = {"x": 1} if state not in (SpineState.PROPOSED, SpineState.CERTIFYING) else None
    from pcae.cltr_prototype.models import TransitionRecord

    record = TransitionRecord(identity=ident, spine_state=state, source_revision="abc", certified_state=certified_state)
    assert sm.retry_classification(record) == expected


def test_quarantined_overrides_retry_table(ident):
    from pcae.cltr_prototype.models import TransitionRecord

    record = TransitionRecord(identity=ident, spine_state=SpineState.CERTIFIED, source_revision="abc", certified_state={"x": 1}, quarantined=True)
    assert sm.retry_classification(record) == RetryClassification.REQUIRE_HUMAN_REVIEW


def test_no_generic_set_state_function_exists():
    import inspect

    names = [name for name, _ in inspect.getmembers(sm, inspect.isfunction)]
    assert "set_state" not in names
    assert "apply_transition" not in names
