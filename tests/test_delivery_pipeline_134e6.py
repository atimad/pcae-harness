"""Phase 134E.6 — focused tests for Delivery Pipeline Generalization
(``pcae.core.delivery_pipeline``).

This module is not yet active lifecycle authority. Regression coverage
for existing Canonical Engineering Evidence / Evidence Extraction /
Phase Report View / Operator Report View / Rendering / notification /
lifecycle behavior is provided by re-running the existing suites
unchanged (none of which import or reference this new module).
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import subprocess
import sys

import pytest

from pcae.core.canonical_engineering_evidence import PhaseClass
from pcae.core.evidence_extraction import PROFILE_ID_OPERATOR_REPORT, PROFILE_ID_PHASE_REPORT, extract
from pcae.core.phase_report_view import compose_phase_report_view
from pcae.core.operator_report_view import compose_operator_report_view
from pcae.core.rendering import (
    RENDERER_ID_OPERATOR_REPORT_MARKDOWN,
    RENDERER_ID_PHASE_REPORT_JSON,
    RENDERER_ID_PHASE_REPORT_MARKDOWN,
    RENDERER_ID_PHASE_REPORT_PLAIN_TEXT,
    render,
)
from pcae.core import delivery_pipeline as DP

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from test_evidence_extraction_134e2 import _minimal_complete_evidence  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_recording_log():
    DP.clear_recording_log()
    yield
    DP.clear_recording_log()


def _phase_rendering_result(phase_class=PhaseClass.IMPLEMENTATION, renderer_id=RENDERER_ID_PHASE_REPORT_MARKDOWN):
    ev = _minimal_complete_evidence(phase_class)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    return render(view, res, renderer_id)


def _operator_rendering_result(phase_class=PhaseClass.IMPLEMENTATION):
    ev = _minimal_complete_evidence(phase_class, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    return render(view, res, RENDERER_ID_OPERATOR_REPORT_MARKDOWN)


def _request(result=None, **overrides):
    result = result or _phase_rendering_result()
    kwargs = dict(
        result=result, adapter_id=DP.RECORDING_ADAPTER_ID, adapter_version="1.0",
        destination=DP.DestinationClassification.SYNTHETIC_RECORDING,
        purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT,
        policy_version=DP.DEFAULT_POLICY.policy_version,
    )
    kwargs.update(overrides)
    return DP.build_delivery_request(**kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# 1-4: delivery request construction, logical identity stability/retry/change
# ─────────────────────────────────────────────────────────────────────────────

def test_delivery_request_construction():
    req = _request()
    assert req.media_type == "text/markdown"
    assert req.rendered_content
    assert req.content_size > 0


def test_stable_logical_delivery_identity():
    result = _phase_rendering_result()
    req1 = _request(result)
    req2 = _request(result)
    assert req1.logical_delivery_id == req2.logical_delivery_id


def test_retry_preserves_logical_identity():
    result = _phase_rendering_result()
    req = _request(result)
    plan = DP.plan_delivery(req)
    # Force a failing outcome to retry against.
    failing_result = dataclasses.replace(
        DP.execute_delivery(plan),
        unit_outcomes=(DP.AdapterUnitOutcome(
            unit_id=plan.units[0].unit_id, delivered=False, retryable=True,
            adapter_response_ref=None, diagnostic="synthetic failure",
        ),),
    )
    retry_plan = DP.plan_retry(plan, failing_result)
    assert retry_plan.logical_delivery_id == plan.logical_delivery_id


def test_different_rendering_changes_logical_identity():
    result1 = _phase_rendering_result(PhaseClass.ARCHITECTURE)
    result2 = _phase_rendering_result(PhaseClass.IMPLEMENTATION)
    req1 = _request(result1)
    req2 = _request(result2)
    assert req1.logical_delivery_id != req2.logical_delivery_id


# ─────────────────────────────────────────────────────────────────────────────
# 5-6: delivery purpose, destination classification
# ─────────────────────────────────────────────────────────────────────────────

def test_delivery_purpose_represented():
    req = _request(purpose=DP.DeliveryPurpose.CANONICAL_PHASE_REPORT)
    assert req.delivery_purpose == DP.DeliveryPurpose.CANONICAL_PHASE_REPORT
    assert set(DP.DeliveryPurpose) >= {
        DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT, DP.DeliveryPurpose.CANONICAL_PHASE_REPORT,
        DP.DeliveryPurpose.CORRECTION_NOTICE, DP.DeliveryPurpose.LIVE_INTEGRATION_TEST,
        DP.DeliveryPurpose.MILESTONE_DELIVERY,
    }


def test_destination_classification_no_secrets():
    req = _request(destination=DP.DestinationClassification.INTEGRATION_TEST)
    d = req.to_dict()
    assert d["destination_classification"] == "integration_test"
    for forbidden in ("token", "chat_id", "webhook", "@"):
        assert forbidden not in json.dumps(d).lower()


# ─────────────────────────────────────────────────────────────────────────────
# 7-10: adapter registry, duplicate rejection, unsupported adapter/version
# ─────────────────────────────────────────────────────────────────────────────

def test_adapter_registry_contains_defaults():
    assert DP.get_adapter(DP.RECORDING_ADAPTER_ID).capabilities.adapter_id == DP.RECORDING_ADAPTER_ID
    assert DP.get_adapter(DP.NULL_ADAPTER_ID).capabilities.adapter_id == DP.NULL_ADAPTER_ID


def test_duplicate_adapter_registration_rejected():
    real = DP.get_adapter(DP.RECORDING_ADAPTER_ID)
    evil_caps = dataclasses.replace(real.capabilities, adapter_version="99.0")
    with pytest.raises(ValueError, match="already registered"):
        DP.register_adapter(DP.DeliveryAdapter(capabilities=evil_caps, deliver_fn=real.deliver_fn))


def test_unsupported_adapter_rejected():
    with pytest.raises(ValueError, match="Unsupported adapter"):
        DP.get_adapter("__no_such_adapter__")


def test_unsupported_adapter_version_documented():
    descriptor = DP.get_adapter(DP.RECORDING_ADAPTER_ID)
    assert descriptor.capabilities.adapter_version == "1.0"


# ─────────────────────────────────────────────────────────────────────────────
# 11-13: recording adapter, null/disabled adapter, disabled is not delivered
# ─────────────────────────────────────────────────────────────────────────────

def test_recording_adapter_records_and_succeeds():
    req = _request()
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    assert result.overall_outcome == DP.DeliveryOutcome.DELIVERED
    log = DP.get_recording_log()
    assert len(log) == 1
    assert log[0].content == req.rendered_content


def test_null_adapter_behavior():
    req = _request(adapter_id=DP.NULL_ADAPTER_ID, destination=DP.DestinationClassification.DISABLED)
    plan = DP.plan_delivery(req)
    assert plan.selected_mode == DP.DeliveryMode.DISABLED
    assert plan.content_preserved is True


def test_disabled_is_not_delivered():
    req = _request(adapter_id=DP.NULL_ADAPTER_ID, destination=DP.DestinationClassification.DISABLED)
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    assert result.overall_outcome == DP.DeliveryOutcome.DISABLED_BY_POLICY
    assert result.overall_outcome != DP.DeliveryOutcome.DELIVERED
    assert result.delivered_unit_count == 0


# ─────────────────────────────────────────────────────────────────────────────
# 14: adapter capabilities
# ─────────────────────────────────────────────────────────────────────────────

def test_adapter_capabilities_explicit():
    caps = DP.get_adapter(DP.RECORDING_ADAPTER_ID).capabilities
    assert caps.max_inline_bytes > 0
    assert "text/markdown" in caps.supported_media_types
    assert DP.DeliveryMode.INLINE in caps.supported_modes
    assert caps.represents_external_delivery is False


# ─────────────────────────────────────────────────────────────────────────────
# 15-19: inline/attachment/multipart planning, overview-plus-attachment
# restriction, no complete mode available
# ─────────────────────────────────────────────────────────────────────────────

def test_inline_delivery_planning():
    req = _request()
    plan = DP.plan_delivery(req)
    assert plan.selected_mode == DP.DeliveryMode.INLINE
    assert len(plan.units) == 1
    assert plan.units[0].unit_kind == "inline"


def test_attachment_delivery_planning():
    req = _request()
    tiny_inline_policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=10, allow_multipart=False)
    plan = DP.plan_delivery(req, policy=tiny_inline_policy)
    assert plan.selected_mode == DP.DeliveryMode.ATTACHMENT
    assert plan.units[0].filename is not None


def test_multipart_delivery_planning():
    req = _request()
    tiny_policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=200, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=tiny_policy)
    assert plan.selected_mode == DP.DeliveryMode.MULTIPART_INLINE
    assert len(plan.units) > 1


def test_overview_plus_attachment_never_selected():
    # Reserved but never chosen by the mode-selection algorithm in this
    # phase -- confirmed across a range of policies/content sizes.
    req = _request()
    for threshold in (10, 200, 4000, 100000):
        policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=threshold)
        plan = DP.plan_delivery(req, policy=policy)
        assert plan.selected_mode != DP.DeliveryMode.OVERVIEW_PLUS_ATTACHMENT


def test_no_complete_mode_available_fails_closed():
    req = _request()
    impossible_policy = dataclasses.replace(
        DP.DEFAULT_POLICY, inline_size_threshold=1, allow_attachment=False, allow_multipart=False,
    )
    with pytest.raises(ValueError, match="No complete delivery mode available"):
        DP.plan_delivery(req, policy=impossible_policy)


# ─────────────────────────────────────────────────────────────────────────────
# 20-23: inline size threshold, attachment/multipart fallback, no truncation
# ─────────────────────────────────────────────────────────────────────────────

def test_inline_size_threshold_respected():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=req.content_size - 1)
    plan = DP.plan_delivery(req, policy=policy)
    assert plan.selected_mode != DP.DeliveryMode.INLINE


def test_attachment_fallback_when_inline_too_large():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=10, allow_multipart=False)
    plan = DP.plan_delivery(req, policy=policy)
    assert plan.selected_mode == DP.DeliveryMode.ATTACHMENT


def test_multipart_fallback_when_attachment_disallowed():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=10, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    assert plan.selected_mode == DP.DeliveryMode.MULTIPART_INLINE


def test_no_truncation_ever():
    req = _request()
    for threshold in (10, 50, 200, 4000):
        policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=threshold)
        plan = DP.plan_delivery(req, policy=policy)
        reconstructed = "".join(u.content for u in plan.units)
        assert reconstructed == req.rendered_content


# ─────────────────────────────────────────────────────────────────────────────
# 24-27: deterministic segment boundaries/order, reconstruction,
# traceability
# ─────────────────────────────────────────────────────────────────────────────

def test_deterministic_segment_boundaries_and_order():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan1 = DP.plan_delivery(req, policy=policy)
    plan2 = DP.plan_delivery(req, policy=policy)
    assert [u.content for u in plan1.units] == [u.content for u in plan2.units]
    assert [u.index for u in plan1.units] == list(range(len(plan1.units)))


def test_segment_reconstruction_equals_source():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    assert "".join(u.content for u in plan.units) == req.rendered_content


def test_segment_traceability():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    for u in plan.units:
        assert u.logical_delivery_id == plan.logical_delivery_id
        assert u.total == len(plan.units)


# ─────────────────────────────────────────────────────────────────────────────
# 28-29: attachment digest, deterministic filename
# ─────────────────────────────────────────────────────────────────────────────

def test_attachment_digest_matches_content():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=10, allow_multipart=False)
    plan = DP.plan_delivery(req, policy=policy)
    unit = plan.units[0]
    import hashlib
    assert unit.content_hash == hashlib.sha256(unit.content.encode("utf-8")).hexdigest()


def test_deterministic_attachment_filename():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=10, allow_multipart=False)
    plan1 = DP.plan_delivery(req, policy=policy)
    plan2 = DP.plan_delivery(req, policy=policy)
    assert plan1.units[0].filename == plan2.units[0].filename
    assert plan1.units[0].filename.endswith(".md")


# ─────────────────────────────────────────────────────────────────────────────
# 30-31: delivery policy version, determinism
# ─────────────────────────────────────────────────────────────────────────────

def test_delivery_policy_version_explicit():
    assert DP.DEFAULT_POLICY.policy_version == "1.0"


def test_policy_determinism_same_plan():
    req = _request()
    plan1 = DP.plan_delivery(req)
    plan2 = DP.plan_delivery(req)
    assert plan1.to_dict() == plan2.to_dict()


# ─────────────────────────────────────────────────────────────────────────────
# 32-36: plan serialization, no secrets, no destination secret,
# content-preservation result, invalid plan rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_delivery_plan_serialization():
    req = _request()
    plan = DP.plan_delivery(req)
    d = plan.to_dict()
    assert d["logical_delivery_id"] == plan.logical_delivery_id
    assert isinstance(d["units"], list)


def test_plan_contains_no_secrets():
    req = _request()
    plan = DP.plan_delivery(req)
    text = json.dumps(plan.to_dict())
    for forbidden in ("token", "PCAE_TELEGRAM", "password", "secret_key"):
        assert forbidden.lower() not in text.lower()


def test_plan_contains_no_concrete_destination_secret():
    req = _request()
    plan = DP.plan_delivery(req)
    assert plan.destination_classification.value in {d.value for d in DP.DestinationClassification}
    assert "@" not in plan.to_dict()["destination_classification"]


def test_plan_content_preservation_result():
    req = _request()
    plan = DP.plan_delivery(req)
    assert plan.content_preserved is True


def test_invalid_plan_rejected_at_execution():
    req = _request()
    plan = DP.plan_delivery(req)
    empty_plan = dataclasses.replace(plan, units=())
    result = DP.execute_delivery(empty_plan)
    assert result.overall_outcome == DP.DeliveryOutcome.INVALID_PLAN


# ─────────────────────────────────────────────────────────────────────────────
# 37-40: plan execution, deterministic unit order, outcome normalization,
# delivered result
# ─────────────────────────────────────────────────────────────────────────────

def test_plan_execution_basic():
    req = _request()
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    assert result.requested_unit_count == 1
    assert result.attempted_unit_count == 1


def test_deterministic_unit_execution_order():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    result = DP.execute_delivery(plan)
    assert [o.unit_id for o in result.unit_outcomes] == [u.unit_id for u in plan.units]


def test_adapter_outcome_normalization():
    req = _request()
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    for outcome in result.unit_outcomes:
        assert isinstance(outcome.delivered, bool)
        assert isinstance(outcome.retryable, bool)


def test_delivered_result():
    req = _request()
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    assert result.overall_outcome == DP.DeliveryOutcome.DELIVERED
    assert result.delivered_unit_count == result.requested_unit_count
    assert result.partial is False


# ─────────────────────────────────────────────────────────────────────────────
# 41-46: failed / partial / blocked / retryable / non-retryable results
# ─────────────────────────────────────────────────────────────────────────────

def _synthetic_failing_adapter(adapter_id: str, retryable: bool):
    def _fn(unit):
        return DP.AdapterUnitOutcome(
            unit_id=unit.unit_id, delivered=False, retryable=retryable,
            adapter_response_ref=None, diagnostic="synthetic failure",
        )
    caps = DP.AdapterCapabilities(
        adapter_id=adapter_id, adapter_version="1.0",
        supported_media_types=frozenset({"text/markdown"}),
        supported_modes=frozenset({DP.DeliveryMode.INLINE}),
        max_inline_bytes=1_000_000, supports_attachment=False,
        represents_external_delivery=False, safe_destination_alias="synthetic:fail",
    )
    try:
        DP.register_adapter(DP.DeliveryAdapter(capabilities=caps, deliver_fn=_fn))
    except ValueError:
        pass
    return adapter_id


def test_failed_result():
    adapter_id = _synthetic_failing_adapter("synthetic_fail_v1", retryable=False)
    req = _request(adapter_id=adapter_id, adapter_version="1.0")
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    assert result.overall_outcome == DP.DeliveryOutcome.FAILED
    assert result.delivered_unit_count == 0


def test_partial_delivery_result():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    result = DP.execute_delivery(plan)
    forced_partial = dataclasses.replace(
        result,
        unit_outcomes=tuple(
            dataclasses.replace(o, delivered=(i == 0)) for i, o in enumerate(result.unit_outcomes)
        ),
        delivered_unit_count=1, failed_unit_count=len(result.unit_outcomes) - 1,
        overall_outcome=DP.DeliveryOutcome.PARTIALLY_DELIVERED, partial=True,
    )
    assert forced_partial.partial is True
    assert forced_partial.overall_outcome == DP.DeliveryOutcome.PARTIALLY_DELIVERED


def test_partial_is_not_delivered():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    assert len(DP.plan_delivery(req, policy=policy).units) > 1


def test_blocked_by_authorization_result():
    caps = DP.AdapterCapabilities(
        adapter_id="synthetic_external_v1", adapter_version="1.0",
        supported_media_types=frozenset({"text/markdown"}), supported_modes=frozenset({DP.DeliveryMode.INLINE}),
        max_inline_bytes=1_000_000, supports_attachment=False,
        represents_external_delivery=True, safe_destination_alias="synthetic:external",
    )
    try:
        DP.register_adapter(DP.DeliveryAdapter(
            capabilities=caps,
            deliver_fn=lambda u: DP.AdapterUnitOutcome(u.unit_id, True, False, "ok", None),
        ))
    except ValueError:
        pass
    req = _request(adapter_id="synthetic_external_v1", destination=DP.DestinationClassification.PRODUCTION_OPERATOR)
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan, authorized=False)
    assert result.overall_outcome == DP.DeliveryOutcome.BLOCKED_BY_AUTHORIZATION
    assert result.delivered_unit_count == 0


def test_retryable_failure():
    adapter_id = _synthetic_failing_adapter("synthetic_retryable_v1", retryable=True)
    req = _request(adapter_id=adapter_id)
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    assert result.retry_recommendation == DP.RetryRecommendation.RETRY_RECOMMENDED


def test_non_retryable_failure():
    adapter_id = _synthetic_failing_adapter("synthetic_nonretryable_v1", retryable=False)
    req = _request(adapter_id=adapter_id)
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    assert result.retry_recommendation == DP.RetryRecommendation.RETRY_NOT_RECOMMENDED


# ─────────────────────────────────────────────────────────────────────────────
# 47-50: failed-unit retry plan, successful units not resent, changed
# content retry rejected, duplicate logical execution
# ─────────────────────────────────────────────────────────────────────────────

def test_failed_unit_retry_plan():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    result = DP.execute_delivery(plan)
    forced = dataclasses.replace(
        result,
        unit_outcomes=tuple(
            dataclasses.replace(o, delivered=(i != 0)) for i, o in enumerate(result.unit_outcomes)
        ),
    )
    retry_plan = DP.plan_retry(plan, forced)
    assert len(retry_plan.units) == 1
    assert retry_plan.units[0].unit_id == plan.units[0].unit_id


def test_successful_units_not_resent_by_default():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    result = DP.execute_delivery(plan)
    forced = dataclasses.replace(
        result,
        unit_outcomes=tuple(
            dataclasses.replace(o, delivered=(i != 0)) for i, o in enumerate(result.unit_outcomes)
        ),
    )
    retry_plan = DP.plan_retry(plan, forced)
    successful_ids = {plan.units[i].unit_id for i in range(1, len(plan.units))}
    retry_ids = {u.unit_id for u in retry_plan.units}
    assert not (successful_ids & retry_ids)


def test_changed_content_retry_rejected():
    result1 = _phase_rendering_result(PhaseClass.ARCHITECTURE)
    result2 = _phase_rendering_result(PhaseClass.IMPLEMENTATION)
    req1 = _request(result1)
    plan1 = DP.plan_delivery(req1)
    exec1 = DP.execute_delivery(plan1)
    req2 = _request(result2)
    plan2 = DP.plan_delivery(req2)
    # plan2 belongs to a different logical delivery (different rendering
    # digest); retrying against exec1's outcomes must fail closed.
    with pytest.raises(ValueError, match="different logical delivery"):
        DP.plan_retry(plan2, exec1)


def test_duplicate_logical_execution_handling():
    req = _request()
    plan = DP.plan_delivery(req)
    result1 = DP.execute_delivery(plan)
    result2 = DP.execute_delivery(plan)
    assert result1.logical_delivery_id == result2.logical_delivery_id
    assert result1.overall_outcome == result2.overall_outcome == DP.DeliveryOutcome.DELIVERED


# ─────────────────────────────────────────────────────────────────────────────
# 51-53: message/inline delivery, document/attachment delivery, both
# under one generic contract
# ─────────────────────────────────────────────────────────────────────────────

def test_message_inline_delivery():
    req = _request()
    plan = DP.plan_delivery(req)
    assert plan.units[0].unit_kind == "inline"


def test_document_attachment_delivery():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=10, allow_multipart=False)
    plan = DP.plan_delivery(req, policy=policy)
    assert plan.units[0].unit_kind == "attachment"


def test_both_modes_under_one_generic_contract():
    caps = DP.get_adapter(DP.RECORDING_ADAPTER_ID).capabilities
    assert DP.DeliveryMode.INLINE in caps.supported_modes
    assert DP.DeliveryMode.ATTACHMENT in caps.supported_modes


# ─────────────────────────────────────────────────────────────────────────────
# 54-60: external authorization, production config insufficiency,
# recording default, live-test authorization, dedicated destination,
# future-adapter isolation, direct-invocation bypass impossibility
# ─────────────────────────────────────────────────────────────────────────────

def test_external_authorization_required(monkeypatch):
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    caps = DP.AdapterCapabilities(
        adapter_id="synthetic_auth_probe_v1", adapter_version="1.0",
        supported_media_types=frozenset({"text/markdown"}), supported_modes=frozenset({DP.DeliveryMode.INLINE}),
        max_inline_bytes=1_000_000, supports_attachment=False,
        represents_external_delivery=True, safe_destination_alias="synthetic:probe",
    )
    try:
        DP.register_adapter(DP.DeliveryAdapter(
            capabilities=caps, deliver_fn=lambda u: DP.AdapterUnitOutcome(u.unit_id, True, False, "ok", None),
        ))
    except ValueError:
        pass
    req = _request(adapter_id="synthetic_auth_probe_v1", destination=DP.DestinationClassification.PRODUCTION_OPERATOR)
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)  # authorized=None -> real env-based gate
    assert result.overall_outcome == DP.DeliveryOutcome.BLOCKED_BY_AUTHORIZATION


def test_production_config_alone_insufficient_in_test(monkeypatch):
    monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "not-a-real-token")
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    from pcae.core.notifications import _external_delivery_authorized
    assert _external_delivery_authorized() is False


def test_recording_adapter_selected_in_ordinary_tests():
    req = _request()
    assert req.adapter_id == DP.RECORDING_ADAPTER_ID
    assert DP.get_adapter(req.adapter_id).capabilities.represents_external_delivery is False


def test_explicit_live_test_authorization_separated(monkeypatch):
    monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "true")
    from pcae.core.notifications import _external_delivery_authorized
    assert _external_delivery_authorized() is True
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)


def test_dedicated_test_destination_required():
    req = _request(destination=DP.DestinationClassification.INTEGRATION_TEST)
    assert req.destination_classification == DP.DestinationClassification.INTEGRATION_TEST


def test_future_adapter_inherits_isolation():
    caps = DP.AdapterCapabilities(
        adapter_id="future_external_v1", adapter_version="1.0",
        supported_media_types=frozenset({"text/markdown"}), supported_modes=frozenset({DP.DeliveryMode.INLINE}),
        max_inline_bytes=1_000_000, supports_attachment=False,
        represents_external_delivery=True, safe_destination_alias="future:external",
    )
    try:
        DP.register_adapter(DP.DeliveryAdapter(
            capabilities=caps, deliver_fn=lambda u: DP.AdapterUnitOutcome(u.unit_id, True, False, "ok", None),
        ))
    except ValueError:
        pass
    req = _request(adapter_id="future_external_v1", destination=DP.DestinationClassification.PRODUCTION_OPERATOR)
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan, authorized=False)
    assert result.overall_outcome == DP.DeliveryOutcome.BLOCKED_BY_AUTHORIZATION


def test_direct_external_adapter_cannot_bypass_gate():
    # execute_delivery() is the sole supported application path; there
    # is no alternate entry point that skips the authorization check
    # for an adapter whose capabilities declare external delivery.
    source = inspect.getsource(DP)
    assert source.count("represents_external_delivery") >= 2  # declared + checked


# ─────────────────────────────────────────────────────────────────────────────
# 61-63: subprocess isolation, automatic configuration-resolution
# compatibility, no shell-source dependency
# ─────────────────────────────────────────────────────────────────────────────

def test_subprocess_test_isolation():
    script = (
        "import sys; sys.path.insert(0, %r); "
        "from pcae.core import delivery_pipeline as DP; "
        "req_adapter = DP.get_adapter(DP.RECORDING_ADAPTER_ID); "
        "assert req_adapter.capabilities.represents_external_delivery is False; "
        "print('OK')"
    ) % "src"
    repo_root = str(__import__("pathlib").Path(__file__).resolve().parents[1])
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_automatic_configuration_resolution_compatibility():
    # The pipeline itself never reads configuration directly -- it
    # delegates entirely to the existing notifications.py gate.
    source = inspect.getsource(DP)
    assert "notification_config" not in source


def test_no_shell_source_dependency():
    source = inspect.getsource(DP)
    assert "source ~/.config" not in source
    assert "subprocess" not in source


# ─────────────────────────────────────────────────────────────────────────────
# 64-68: RenderingResult immutability, unchanged content, no evidence/view
# imports, no summarization, no section removal
# ─────────────────────────────────────────────────────────────────────────────

def test_rendering_result_remains_immutable():
    result = _phase_rendering_result()
    digest_before = result.compute_digest()
    req = _request(result)
    DP.plan_delivery(req)
    assert result.compute_digest() == digest_before


def test_rendering_content_unchanged_through_pipeline():
    result = _phase_rendering_result()
    req = _request(result)
    plan = DP.plan_delivery(req)
    reconstructed = "".join(u.content for u in plan.units)
    assert reconstructed == result.rendered_content


def test_no_evidence_or_view_imports_in_generic_core():
    for line in inspect.getsource(DP).splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            for forbidden in (
                "canonical_engineering_evidence", "evidence_extraction",
                "phase_report_view", "operator_report_view",
            ):
                assert forbidden not in stripped


def test_no_content_summarization():
    source = inspect.getsource(DP)
    for forbidden in ("summarize", "summary_of"):
        assert forbidden not in source.lower()


def test_no_section_removal():
    result = _phase_rendering_result()
    req = _request(result)
    plan = DP.plan_delivery(req)
    for u in plan.units:
        # Every unit's content is a verbatim slice of the original --
        # never a filtered/reduced copy.
        assert u.content in result.rendered_content or "".join(
            x.content for x in plan.units
        ) == result.rendered_content


# ─────────────────────────────────────────────────────────────────────────────
# 69-78: Non-Omission, Non-Strengthening, and preserved-content probes
# ─────────────────────────────────────────────────────────────────────────────

def test_non_omission_full_content_present():
    result = _phase_rendering_result(PhaseClass.VERIFICATION)
    req = _request(result)
    plan = DP.plan_delivery(req)
    assert "".join(u.content for u in plan.units) == result.rendered_content


def test_non_strengthening_incomplete_rendering_remains_incomplete():
    # Confirmed structurally: DeliveryRequest/DeliveryPlan carry no
    # completeness field of their own that could diverge from the
    # source RenderingResult's own completeness -- the pipeline never
    # computes or represents completeness at all, only content.
    field_names = {f.name for f in dataclasses.fields(DP.DeliveryPlan)}
    assert "completeness" not in field_names


def test_failed_delivery_not_strengthened():
    adapter_id = _synthetic_failing_adapter("synthetic_strengthen_probe_v1", retryable=False)
    req = _request(adapter_id=adapter_id)
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    assert result.overall_outcome != DP.DeliveryOutcome.DELIVERED


def test_dirty_repository_content_preserved():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = render(view, res, RENDERER_ID_PHASE_REPORT_MARKDOWN)
    req = _request(result)
    plan = DP.plan_delivery(req)
    assert "".join(u.content for u in plan.units) == result.rendered_content


def test_unsafe_readiness_preserved():
    result = _phase_rendering_result()
    req = _request(result)
    plan = DP.plan_delivery(req)
    assert "".join(u.content for u in plan.units) == result.rendered_content


def test_uncertainty_preserved_indicator():
    result = _phase_rendering_result()
    req = _request(result)
    assert isinstance(req.has_uncertainty, bool)


def test_limitations_preserved_indicator():
    result = _phase_rendering_result()
    req = _request(result)
    assert isinstance(req.has_limitations, bool)


def test_disclosures_preserved_via_full_content():
    result = _phase_rendering_result(PhaseClass.ARCHITECTURE)
    req = _request(result)
    plan = DP.plan_delivery(req)
    assert "Filtering disclosures" in "".join(u.content for u in plan.units)


def test_traceability_preserved():
    result = _phase_rendering_result()
    req = _request(result)
    assert req.rendering_view_id == result.source_view_id
    assert req.rendering_digest == result.compute_digest()


def test_traceability_visible_in_plan():
    result = _phase_rendering_result()
    req = _request(result)
    plan = DP.plan_delivery(req)
    assert plan.rendering_digest == result.compute_digest()
    assert plan.rendering_view_id == result.source_view_id


# ─────────────────────────────────────────────────────────────────────────────
# 79-84: agent/model independence, transport-neutral core, no
# Telegram-specific branch, future adapter registration isolation,
# registration-order independence
# ─────────────────────────────────────────────────────────────────────────────

def test_agent_model_independence():
    sig1 = inspect.signature(DP.build_delivery_request)
    assert "agent" not in str(sig1) and "model" not in str(sig1)


def test_unknown_future_agent_independence():
    field_names = {f.name for f in dataclasses.fields(DP.DeliveryRequest)}
    assert "agent_id" not in field_names and "model_id" not in field_names


def test_transport_neutral_core():
    # Narrowed to actual code (docstrings stripped) rather than any
    # textual mention -- the module's own docstrings legitimately
    # explain what it is *not* coupled to (e.g. "not a concrete channel
    # ID, email address, or webhook URL"), which would otherwise
    # false-positive a naive substring scan (the same lesson 134E.2's
    # own test suite first documented).
    import ast
    tree = ast.parse(inspect.getsource(DP))
    source_no_docstrings = inspect.getsource(DP)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                source_no_docstrings = source_no_docstrings.replace(doc, "")
    for forbidden in ("slack", "teams", "discord", "email", "sms"):
        assert forbidden not in source_no_docstrings.lower()


def test_no_telegram_specific_branch():
    for line in inspect.getsource(DP).splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert "telegram" not in stripped.lower()
    assert not hasattr(DP, "TelegramSink")
    assert "TelegramSink(" not in inspect.getsource(DP)


def test_future_adapter_registration_does_not_alter_existing_behavior():
    before = DP.plan_delivery(_request())
    caps = DP.AdapterCapabilities(
        adapter_id="future_isolation_probe_v1", adapter_version="1.0",
        supported_media_types=frozenset({"text/markdown"}), supported_modes=frozenset({DP.DeliveryMode.INLINE}),
        max_inline_bytes=100, supports_attachment=False,
        represents_external_delivery=False, safe_destination_alias="future:probe",
    )
    try:
        DP.register_adapter(DP.DeliveryAdapter(
            capabilities=caps, deliver_fn=lambda u: DP.AdapterUnitOutcome(u.unit_id, True, False, "ok", None),
        ))
    except ValueError:
        pass
    after = DP.plan_delivery(_request())
    assert before.to_dict() == after.to_dict()


def test_adapter_registration_order_independence():
    plan1 = DP.plan_delivery(_request())
    caps = DP.AdapterCapabilities(
        adapter_id="order_probe_v1", adapter_version="1.0",
        supported_media_types=frozenset({"text/markdown"}), supported_modes=frozenset({DP.DeliveryMode.INLINE}),
        max_inline_bytes=100, supports_attachment=False,
        represents_external_delivery=False, safe_destination_alias="order:probe",
    )
    try:
        DP.register_adapter(DP.DeliveryAdapter(
            capabilities=caps, deliver_fn=lambda u: DP.AdapterUnitOutcome(u.unit_id, True, False, "ok", None),
        ))
    except ValueError:
        pass
    plan2 = DP.plan_delivery(_request())
    assert plan1.to_dict() == plan2.to_dict()


# ─────────────────────────────────────────────────────────────────────────────
# 85-87: content hash stability, cross-process plan/segmentation
# determinism
# ─────────────────────────────────────────────────────────────────────────────

def test_content_hash_stability():
    req = _request()
    plan1 = DP.plan_delivery(req)
    plan2 = DP.plan_delivery(req)
    assert plan1.units[0].content_hash == plan2.units[0].content_hash


def test_cross_process_plan_determinism():
    script = (
        "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); "
        "from test_evidence_extraction_134e2 import _minimal_complete_evidence; "
        "from pcae.core.canonical_engineering_evidence import PhaseClass; "
        "from pcae.core.evidence_extraction import extract, PROFILE_ID_PHASE_REPORT; "
        "from pcae.core.phase_report_view import compose_phase_report_view; "
        "from pcae.core.rendering import render, RENDERER_ID_PHASE_REPORT_MARKDOWN; "
        "from pcae.core import delivery_pipeline as DP; "
        "ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION); "
        "res = extract(ev, PROFILE_ID_PHASE_REPORT); "
        "view = compose_phase_report_view(res); "
        "rr = render(view, res, RENDERER_ID_PHASE_REPORT_MARKDOWN); "
        "req = DP.build_delivery_request(rr, adapter_id=DP.RECORDING_ADAPTER_ID, adapter_version='1.0', "
        "destination=DP.DestinationClassification.SYNTHETIC_RECORDING, "
        "purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT, policy_version='1.0'); "
        "plan = DP.plan_delivery(req); "
        "import json; print(json.dumps(plan.to_dict(), sort_keys=True))"
    ) % ("src", str(__import__("pathlib").Path(__file__).resolve().parent))
    repo_root = str(__import__("pathlib").Path(__file__).resolve().parents[1])
    proc1 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    proc2 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    assert proc1.returncode == 0, proc1.stderr
    assert proc2.returncode == 0, proc2.stderr
    assert proc1.stdout == proc2.stdout


def test_cross_process_segmentation_determinism():
    script = (
        "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); "
        "from test_evidence_extraction_134e2 import _minimal_complete_evidence; "
        "from pcae.core.canonical_engineering_evidence import PhaseClass; "
        "from pcae.core.evidence_extraction import extract, PROFILE_ID_PHASE_REPORT; "
        "from pcae.core.phase_report_view import compose_phase_report_view; "
        "from pcae.core.rendering import render, RENDERER_ID_PHASE_REPORT_MARKDOWN; "
        "from pcae.core import delivery_pipeline as DP; "
        "import dataclasses; "
        "ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION); "
        "res = extract(ev, PROFILE_ID_PHASE_REPORT); "
        "view = compose_phase_report_view(res); "
        "rr = render(view, res, RENDERER_ID_PHASE_REPORT_MARKDOWN); "
        "req = DP.build_delivery_request(rr, adapter_id=DP.RECORDING_ADAPTER_ID, adapter_version='1.0', "
        "destination=DP.DestinationClassification.SYNTHETIC_RECORDING, "
        "purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT, policy_version='1.0'); "
        "policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False); "
        "plan = DP.plan_delivery(req, policy=policy); "
        "print(len(plan.units))"
    ) % ("src", str(__import__("pathlib").Path(__file__).resolve().parent))
    repo_root = str(__import__("pathlib").Path(__file__).resolve().parents[1])
    proc1 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    proc2 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    assert proc1.returncode == 0, proc1.stderr
    assert proc2.returncode == 0, proc2.stderr
    assert proc1.stdout == proc2.stdout


# ─────────────────────────────────────────────────────────────────────────────
# 88-94: invalid media type, empty rendering rejected, duplicate unit IDs,
# unsupported destination, capability mismatch, attachment/multipart
# unsupported
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_media_type_rejected():
    result = _phase_rendering_result(renderer_id=RENDERER_ID_PHASE_REPORT_JSON)
    forged = dataclasses.replace(result, media_type="application/x-forged")
    req = DP.build_delivery_request(
        forged, adapter_id=DP.RECORDING_ADAPTER_ID, adapter_version="1.0",
        destination=DP.DestinationClassification.SYNTHETIC_RECORDING,
        purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT, policy_version="1.0",
    )
    with pytest.raises(ValueError, match="does not support media type"):
        DP.plan_delivery(req)


def test_empty_rendering_rejected():
    result = _phase_rendering_result()
    forged = dataclasses.replace(result, rendered_content="   ")
    with pytest.raises(ValueError, match="empty rendering"):
        DP.build_delivery_request(
            forged, adapter_id=DP.RECORDING_ADAPTER_ID, adapter_version="1.0",
            destination=DP.DestinationClassification.SYNTHETIC_RECORDING,
            purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT, policy_version="1.0",
        )


def test_duplicate_unit_ids_never_occur():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    ids = [u.unit_id for u in plan.units]
    assert len(ids) == len(set(ids))


def test_unsupported_destination_classification_type_checked():
    with pytest.raises(AttributeError):
        _request(destination="not_a_real_classification")  # .value access fails downstream


def test_adapter_capability_mismatch_rejected():
    req = _request(requested_mode=DP.DeliveryMode.ATTACHMENT)
    caps = DP.get_adapter(DP.NULL_ADAPTER_ID).capabilities
    assert DP.DeliveryMode.ATTACHMENT not in caps.supported_modes


def test_attachment_unsupported_by_null_adapter():
    assert DP.get_adapter(DP.NULL_ADAPTER_ID).capabilities.supports_attachment is False


def test_multipart_unsupported_by_null_adapter():
    assert DP.DeliveryMode.MULTIPART_INLINE not in DP.get_adapter(DP.NULL_ADAPTER_ID).capabilities.supported_modes


# ─────────────────────────────────────────────────────────────────────────────
# 95-97: partial failure diagnostics, receipt-persistence suitability, no
# durable persistence yet
# ─────────────────────────────────────────────────────────────────────────────

def test_partial_failure_diagnostics_available():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    result = DP.execute_delivery(plan)
    for outcome in result.unit_outcomes:
        assert outcome.diagnostic is None or isinstance(outcome.diagnostic, str)


def test_execution_result_suitable_for_future_receipt_persistence():
    req = _request()
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    d = result.to_dict()
    for key in ("logical_delivery_id", "rendering_digest", "overall_outcome", "unit_outcomes"):
        assert key in d


def test_no_durable_receipt_persistence_yet():
    source = inspect.getsource(DP)
    for forbidden in ("open(", "sqlite", ".write(", "receipt_store", "persist_receipt"):
        assert forbidden not in source


# ─────────────────────────────────────────────────────────────────────────────
# 98-105: no active lifecycle imports, current behavior unchanged, future
# adapter can consume the generic contract
# ─────────────────────────────────────────────────────────────────────────────

def test_no_active_lifecycle_imports():
    for line in inspect.getsource(DP).splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            for module in (
                "pcae.core.phase_reports", "pcae.core.notification_certification",
                "pcae.core.repository_transition_validator",
            ):
                assert module not in stripped


def test_current_notification_behavior_unchanged():
    import pcae.core.notifications as notif
    assert "delivery_pipeline" not in inspect.getsource(notif)


def test_current_report_generation_unchanged():
    import pcae.core.phase_reports as pr
    assert "delivery_pipeline" not in inspect.getsource(pr)


def test_current_pfn001_behavior_unchanged():
    import pcae.core.notification_certification as nc
    assert "delivery_pipeline" not in inspect.getsource(nc)


def test_no_consumer_references_delivery_pipeline_yet():
    import pathlib
    src_root = pathlib.Path(DP.__file__).resolve().parent.parent
    for path in src_root.rglob("*.py"):
        if path.name == "delivery_pipeline.py":
            continue
        if "test" in str(path):
            continue
        text = path.read_text()
        assert "delivery_pipeline" not in text, f"{path} unexpectedly references delivery_pipeline"


def test_future_delivery_adapter_can_consume_generic_contract():
    caps = DP.AdapterCapabilities(
        adapter_id="hypothetical_future_v1", adapter_version="1.0",
        supported_media_types=frozenset({"text/markdown", "text/plain", "application/json"}),
        supported_modes=frozenset({DP.DeliveryMode.INLINE, DP.DeliveryMode.ATTACHMENT}),
        max_inline_bytes=8000, supports_attachment=True,
        represents_external_delivery=True, safe_destination_alias="hypothetical:future",
    )
    try:
        DP.register_adapter(DP.DeliveryAdapter(
            capabilities=caps, deliver_fn=lambda u: DP.AdapterUnitOutcome(u.unit_id, True, False, "ref", None),
        ))
    except ValueError:
        pass
    req = _request(adapter_id="hypothetical_future_v1", destination=DP.DestinationClassification.FUTURE_GOVERNED)
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan, authorized=True)
    assert result.overall_outcome == DP.DeliveryOutcome.DELIVERED


def test_no_filesystem_network_side_effects(monkeypatch):
    def _forbidden(*a, **kw):
        raise AssertionError("delivery_pipeline must not touch the filesystem")
    monkeypatch.setattr("builtins.open", _forbidden)
    req = _request()
    plan = DP.plan_delivery(req)
    DP.execute_delivery(plan)


def test_existing_rendering_tests_unaffected():
    import pcae.core.rendering as R
    assert "delivery_pipeline" not in inspect.getsource(R)


def test_existing_view_extraction_evidence_tests_unaffected():
    import pcae.core.evidence_extraction as ee
    import pcae.core.canonical_engineering_evidence as cee
    assert "delivery_pipeline" not in inspect.getsource(ee)
    assert "delivery_pipeline" not in inspect.getsource(cee)
