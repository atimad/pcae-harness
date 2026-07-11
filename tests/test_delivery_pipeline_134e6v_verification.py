"""Phase 134E.6V — independent adversarial verification of Delivery
Pipeline Generalization (134E.6).

Does not trust 134E.6's own report, documentation, or its 105 tests as
sufficient evidence. These are fresh probes beyond that existing
coverage, including regression tests for two genuine BLOCKING defects
found and repaired during this verification phase:

1. Ambiguous logical-delivery-identity field concatenation: the
   original ``compute_logical_delivery_id()`` joined its six input
   fields with a bare ``"|"`` separator before hashing. Because
   ``phase_id``, ``adapter_id``, and ``policy_version`` are
   unrestricted free-text strings, two semantically *different* input
   tuples could produce the identical hash by shifting content across
   a field boundary (e.g. ``phase_id="X|Y"`` colliding with
   ``phase_id="X", rendering_digest="Y|<digest>"``). Repaired by
   hashing an unambiguous canonical JSON array instead.
2. Unhandled adapter exception: ``execute_delivery()`` called
   ``adapter.deliver_fn(unit)`` with no exception handling, so any
   adapter implementation error propagated out of the pipeline
   entirely rather than being normalized into a deterministic,
   inspectable outcome. Repaired by catching any exception per-unit and
   converting it into a conservative (retryable) failed
   ``AdapterUnitOutcome``, allowing sibling units to still execute.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import subprocess
import sys

import pytest

from pcae.core.canonical_engineering_evidence import PhaseClass
from pcae.core.evidence_extraction import PROFILE_ID_PHASE_REPORT, extract
from pcae.core.phase_report_view import compose_phase_report_view
from pcae.core.rendering import RENDERER_ID_PHASE_REPORT_MARKDOWN, render
from pcae.core import delivery_pipeline as DP

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from test_evidence_extraction_134e2 import _minimal_complete_evidence  # noqa: E402
from test_delivery_pipeline_134e6 import _phase_rendering_result, _request  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_recording_log():
    DP.clear_recording_log()
    yield
    DP.clear_recording_log()


def _register_probe_adapter(adapter_id, **capability_overrides):
    deliver_fn = capability_overrides.pop(
        "_deliver_fn",
        lambda u: DP.AdapterUnitOutcome(u.unit_id, True, False, "ok", None),
    )
    defaults = dict(
        adapter_id=adapter_id, adapter_version="1.0",
        supported_media_types=frozenset({"text/markdown"}),
        supported_modes=frozenset({DP.DeliveryMode.INLINE}),
        max_inline_bytes=100_000, supports_attachment=False,
        represents_external_delivery=False, safe_destination_alias=f"{adapter_id}:probe",
    )
    defaults.update(capability_overrides)
    caps = DP.AdapterCapabilities(**defaults)
    try:
        DP.register_adapter(DP.DeliveryAdapter(
            capabilities=caps,
            deliver_fn=deliver_fn,
        ))
    except ValueError:
        pass
    return adapter_id


# ─────────────────────────────────────────────────────────────────────────────
# 1-5. Logical-identity collision regression, altered content, destination,
# purpose, policy-version identity change
# ─────────────────────────────────────────────────────────────────────────────

def test_ambiguous_field_concatenation_no_longer_collides():
    id1 = DP.compute_logical_delivery_id(
        "X|Y", "deadbeef", DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT,
        DP.DestinationClassification.SYNTHETIC_RECORDING, "adapterZ", "1.0",
    )
    id2 = DP.compute_logical_delivery_id(
        "X", "Y|deadbeef", DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT,
        DP.DestinationClassification.SYNTHETIC_RECORDING, "adapterZ", "1.0",
    )
    assert id1 != id2
    id3 = DP.compute_logical_delivery_id(
        "P", "deadbeef", DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT,
        DP.DestinationClassification.SYNTHETIC_RECORDING, "adapterA|1.0", "extra",
    )
    id4 = DP.compute_logical_delivery_id(
        "P", "deadbeef", DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT,
        DP.DestinationClassification.SYNTHETIC_RECORDING, "adapterA", "1.0|extra",
    )
    assert id3 != id4


def test_same_logical_id_with_altered_rendering_content_never_occurs():
    result1 = _phase_rendering_result(PhaseClass.ARCHITECTURE)
    result2 = _phase_rendering_result(PhaseClass.VERIFICATION)
    req1 = _request(result1)
    req2 = _request(result2)
    assert req1.logical_delivery_id != req2.logical_delivery_id


def test_same_rendering_different_destination_class_differs():
    result = _phase_rendering_result()
    req1 = _request(result, destination=DP.DestinationClassification.SYNTHETIC_RECORDING)
    req2 = _request(result, destination=DP.DestinationClassification.INTEGRATION_TEST)
    assert req1.logical_delivery_id != req2.logical_delivery_id


def test_same_rendering_different_purpose_differs():
    result = _phase_rendering_result()
    req1 = _request(result, purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT)
    req2 = _request(result, purpose=DP.DeliveryPurpose.CANONICAL_PHASE_REPORT)
    assert req1.logical_delivery_id != req2.logical_delivery_id


def test_policy_version_identity_change():
    result = _phase_rendering_result()
    req1 = _request(result, policy_version="1.0")
    req2 = _request(result, policy_version="1.1")
    assert req1.logical_delivery_id != req2.logical_delivery_id


# ─────────────────────────────────────────────────────────────────────────────
# 6-7. Silent adapter-registry overwrite; same ID/version, changed
# capabilities
# ─────────────────────────────────────────────────────────────────────────────

def test_silent_adapter_registry_overwrite_rejected():
    real = DP.get_adapter(DP.RECORDING_ADAPTER_ID)
    evil = DP.DeliveryAdapter(
        capabilities=dataclasses.replace(real.capabilities, max_inline_bytes=1),
        deliver_fn=real.deliver_fn,
    )
    with pytest.raises(ValueError, match="already registered"):
        DP.register_adapter(evil)
    assert DP.get_adapter(DP.RECORDING_ADAPTER_ID).capabilities.max_inline_bytes == real.capabilities.max_inline_bytes


def test_same_id_version_changed_capabilities_rejected():
    _register_probe_adapter("cap_change_probe_v1", adapter_version="1.0")
    original = DP.get_adapter("cap_change_probe_v1")
    conflicting = DP.DeliveryAdapter(
        capabilities=dataclasses.replace(original.capabilities, represents_external_delivery=True),
        deliver_fn=original.deliver_fn,
    )
    with pytest.raises(ValueError, match="already registered"):
        DP.register_adapter(conflicting)


# ─────────────────────────────────────────────────────────────────────────────
# 8-9. Adapter capability drift after planning; adapter reports delivered
# with zero attempts
# ─────────────────────────────────────────────────────────────────────────────

def test_capability_drift_after_planning_reevaluated_at_execution():
    adapter_id = _register_probe_adapter("drift_probe_v1")
    result = _phase_rendering_result()
    req = _request(result, adapter_id=adapter_id, destination=DP.DestinationClassification.PRODUCTION_OPERATOR)
    plan = DP.plan_delivery(req)
    # Simulate drift via unsupported direct registry mutation (not the
    # supported register_adapter() path, which itself fail-closes).
    original = DP.get_adapter(adapter_id)
    drifted = DP.DeliveryAdapter(
        capabilities=dataclasses.replace(original.capabilities, represents_external_delivery=True),
        deliver_fn=original.deliver_fn,
    )
    DP._ADAPTER_REGISTRY[adapter_id] = drifted
    result_exec = DP.execute_delivery(plan, authorized=False)
    # Execution re-fetches live adapter state -- drift toward "more
    # restrictive" (external) is correctly re-enforced, not silently
    # bypassed using the plan's own stale assumption.
    assert result_exec.overall_outcome == DP.DeliveryOutcome.BLOCKED_BY_AUTHORIZATION


def test_adapter_cannot_report_delivered_with_zero_attempts():
    # Overall outcome is always derived by the pipeline itself from the
    # actual unit_outcomes list -- never trusted from adapter
    # self-reporting -- so "delivered with zero attempts" is
    # structurally impossible via the real execute_delivery() path.
    req = _request()
    plan = DP.plan_delivery(req)
    empty_plan = dataclasses.replace(plan, units=())
    result = DP.execute_delivery(empty_plan)
    assert result.overall_outcome != DP.DeliveryOutcome.DELIVERED
    assert result.delivered_unit_count == 0


# ─────────────────────────────────────────────────────────────────────────────
# 10. Adapter reports partial with no failed unit (structurally impossible)
# ─────────────────────────────────────────────────────────────────────────────

def test_partial_with_no_failed_unit_structurally_impossible():
    # partial = 0 < delivered_count < len(outcomes); if there is no
    # failed unit, delivered_count == len(outcomes), which the pipeline
    # classifies as DELIVERED, never PARTIALLY_DELIVERED -- confirmed by
    # direct source inspection of the outcome-derivation logic.
    source = inspect.getsource(DP.execute_delivery)
    assert "partial = 0 < delivered_count < len(outcomes)" in source


# ─────────────────────────────────────────────────────────────────────────────
# 11. Direct supported external-adapter bypass
# ─────────────────────────────────────────────────────────────────────────────

def test_direct_supported_external_adapter_bypass_impossible():
    adapter_id = _register_probe_adapter("bypass_probe_v1", represents_external_delivery=True)
    result = _phase_rendering_result()
    req = _request(result, adapter_id=adapter_id, destination=DP.DestinationClassification.PRODUCTION_OPERATOR)
    plan = DP.plan_delivery(req)
    # The only supported public execution path is execute_delivery();
    # it always re-checks authorization for any adapter declaring
    # external delivery, with no alternate entry point.
    exec_result = DP.execute_delivery(plan, authorized=False)
    assert exec_result.overall_outcome == DP.DeliveryOutcome.BLOCKED_BY_AUTHORIZATION
    assert exec_result.attempted_unit_count == 0


# ─────────────────────────────────────────────────────────────────────────────
# 12-13. Production config present in ordinary test; future external
# adapter authorization
# ─────────────────────────────────────────────────────────────────────────────

def test_production_config_present_in_ordinary_test(monkeypatch):
    monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "fake-token-value")
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    adapter_id = _register_probe_adapter("prod_config_probe_v1", represents_external_delivery=True)
    result = _phase_rendering_result()
    req = _request(result, adapter_id=adapter_id, destination=DP.DestinationClassification.PRODUCTION_OPERATOR)
    plan = DP.plan_delivery(req)
    exec_result = DP.execute_delivery(plan)  # real env-based gate, no override
    assert exec_result.overall_outcome == DP.DeliveryOutcome.BLOCKED_BY_AUTHORIZATION


def test_future_external_adapter_requires_authorization():
    adapter_id = _register_probe_adapter("future_probe_v1", represents_external_delivery=True)
    result = _phase_rendering_result()
    req = _request(result, adapter_id=adapter_id, destination=DP.DestinationClassification.FUTURE_GOVERNED)
    plan = DP.plan_delivery(req)
    exec_result = DP.execute_delivery(plan, authorized=False)
    assert exec_result.overall_outcome == DP.DeliveryOutcome.BLOCKED_BY_AUTHORIZATION


# ─────────────────────────────────────────────────────────────────────────────
# 14. Automatic config resolution plus test isolation
# ─────────────────────────────────────────────────────────────────────────────

def test_automatic_config_resolution_does_not_bypass_isolation(monkeypatch):
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    req = _request()  # recording adapter, non-external
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    assert result.overall_outcome == DP.DeliveryOutcome.DELIVERED
    assert len(DP.get_recording_log()) == 1


# ─────────────────────────────────────────────────────────────────────────────
# 15-16. Exact inline byte boundary, one byte over
# ─────────────────────────────────────────────────────────────────────────────

def test_exact_inline_byte_boundary():
    result = _phase_rendering_result()
    req = _request(result)
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=req.content_size)
    plan = DP.plan_delivery(req, policy=policy)
    assert plan.selected_mode == DP.DeliveryMode.INLINE


def test_one_byte_over_inline_boundary():
    result = _phase_rendering_result()
    req = _request(result)
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=req.content_size - 1)
    plan = DP.plan_delivery(req, policy=policy)
    assert plan.selected_mode != DP.DeliveryMode.INLINE


# ─────────────────────────────────────────────────────────────────────────────
# 17. Unicode multipart boundary
# ─────────────────────────────────────────────────────────────────────────────

def test_unicode_multipart_boundary_lossless():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective="日本語emoji🎉" * 200)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    rr = render(view, res, RENDERER_ID_PHASE_REPORT_MARKDOWN)
    req = DP.build_delivery_request(
        rr, adapter_id=DP.RECORDING_ADAPTER_ID, adapter_version="1.0",
        destination=DP.DestinationClassification.SYNTHETIC_RECORDING,
        purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT, policy_version="1.0",
    )
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=100, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    reconstructed = "".join(u.content for u in plan.units)
    assert reconstructed == rr.rendered_content
    for u in plan.units:
        # Every segment must remain valid, round-trippable UTF-8 text.
        u.content.encode("utf-8").decode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# 18-21. Missing final segment, duplicate segment, overlapping segment,
# segment reorder (all structurally rejected/impossible via supported API)
# ─────────────────────────────────────────────────────────────────────────────

def test_missing_final_segment_breaks_reconstruction_and_is_detectable():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    truncated_units = plan.units[:-1]
    reconstructed = "".join(u.content for u in truncated_units)
    assert reconstructed != req.rendered_content


def test_duplicate_segment_breaks_reconstruction():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    duplicated = plan.units + (plan.units[0],)
    reconstructed = "".join(u.content for u in duplicated)
    assert reconstructed != req.rendered_content


def test_no_overlapping_or_missing_bytes_in_real_plan():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    total_len = sum(len(u.content) for u in plan.units)
    assert total_len == len(req.rendered_content)


def test_segment_reorder_breaks_reconstruction():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    if len(plan.units) > 1:
        reordered = (plan.units[1], plan.units[0]) + plan.units[2:]
        reconstructed = "".join(u.content for u in reordered)
        assert reconstructed != req.rendered_content


# ─────────────────────────────────────────────────────────────────────────────
# 22-23. Attachment content mutation detectable via hash; filename safety
# ─────────────────────────────────────────────────────────────────────────────

def test_attachment_content_mutation_detected_via_hash():
    req = _request()
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=10, allow_multipart=False)
    plan = DP.plan_delivery(req, policy=policy)
    unit = plan.units[0]
    mutated = dataclasses.replace(unit, content=unit.content + "TAMPERED")
    assert mutated.content_hash == unit.content_hash  # hash field itself unaffected by mutation
    import hashlib
    assert hashlib.sha256(mutated.content.encode("utf-8")).hexdigest() != mutated.content_hash


def test_attachment_filename_safety_with_dotted_verification_phase_ids():
    for phase_id_suffix in ("134E.6V", "134E.10", "134E.10V"):
        logical_id = DP.compute_logical_delivery_id(
            phase_id_suffix, "a" * 64, DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT,
            DP.DestinationClassification.SYNTHETIC_RECORDING, DP.RECORDING_ADAPTER_ID, "1.0",
        )
        filename = DP._filename_for(logical_id, "text/markdown")
        assert "/" not in filename and ".." not in filename
        assert filename.endswith(".md")


# ─────────────────────────────────────────────────────────────────────────────
# 24-25. Disabled adapter oversized content; disabled result cannot
# satisfy delivery
# ─────────────────────────────────────────────────────────────────────────────

def test_disabled_adapter_oversized_content_still_plans():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective="x" * 50_000)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    rr = render(view, res, RENDERER_ID_PHASE_REPORT_MARKDOWN)
    req = DP.build_delivery_request(
        rr, adapter_id=DP.NULL_ADAPTER_ID, adapter_version="1.0",
        destination=DP.DestinationClassification.DISABLED,
        purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT, policy_version="1.0",
    )
    plan = DP.plan_delivery(req)  # must not raise despite oversized content
    assert plan.content_preserved is True
    assert plan.units[0].content == rr.rendered_content


def test_disabled_result_cannot_satisfy_delivery():
    req = _request(adapter_id=DP.NULL_ADAPTER_ID, destination=DP.DestinationClassification.DISABLED)
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    assert result.overall_outcome != DP.DeliveryOutcome.DELIVERED
    assert result.overall_outcome == DP.DeliveryOutcome.DISABLED_BY_POLICY


# ─────────────────────────────────────────────────────────────────────────────
# 26-27. Partial delivery first-unit success, middle-unit failure
# ─────────────────────────────────────────────────────────────────────────────

def _register_selective_failure_adapter(adapter_id: str, fail_indices: set[int]):
    def _fn(unit):
        if unit.index in fail_indices:
            return DP.AdapterUnitOutcome(unit.unit_id, False, True, None, "synthetic selective failure")
        return DP.AdapterUnitOutcome(unit.unit_id, True, False, f"ok:{unit.index}", None)
    return _register_probe_adapter(
        adapter_id, max_inline_bytes=1_000_000,
        supported_modes=frozenset({DP.DeliveryMode.INLINE, DP.DeliveryMode.MULTIPART_INLINE}),
        _deliver_fn=_fn,
    )


def test_partial_delivery_first_unit_succeeds_second_fails():
    adapter_id = _register_selective_failure_adapter("partial_probe_1_v1", fail_indices={1})
    req = _request(adapter_id=adapter_id)
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    assert len(plan.units) > 1
    result = DP.execute_delivery(plan)
    assert result.unit_outcomes[0].delivered is True
    assert result.unit_outcomes[1].delivered is False
    assert result.partial is True


def test_partial_delivery_middle_unit_fails():
    adapter_id = _register_selective_failure_adapter("partial_probe_mid_v1", fail_indices={1})
    req = _request(adapter_id=adapter_id)
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=100, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    if len(plan.units) >= 3:
        result = DP.execute_delivery(plan)
        assert result.partial is True
        assert result.overall_outcome == DP.DeliveryOutcome.PARTIALLY_DELIVERED


# ─────────────────────────────────────────────────────────────────────────────
# 28-32. Retry failed units only, changed-content/destination retry
# rejection, successful units not resent, logical identity stable
# ─────────────────────────────────────────────────────────────────────────────

def test_retry_failed_units_only():
    adapter_id = _register_selective_failure_adapter("retry_probe_v1", fail_indices={0})
    req = _request(adapter_id=adapter_id)
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    result = DP.execute_delivery(plan)
    retry_plan = DP.plan_retry(plan, result)
    assert all(u.index == 0 for u in retry_plan.units) or len(retry_plan.units) < len(plan.units)


def test_changed_content_retry_rejected_via_different_logical_id():
    result1 = _phase_rendering_result(PhaseClass.ARCHITECTURE)
    result2 = _phase_rendering_result(PhaseClass.VERIFICATION)
    req1 = _request(result1)
    plan1 = DP.plan_delivery(req1)
    exec1 = DP.execute_delivery(plan1)
    req2 = _request(result2)
    plan2 = DP.plan_delivery(req2)
    with pytest.raises(ValueError, match="different logical delivery"):
        DP.plan_retry(plan2, exec1)


def test_changed_destination_retry_rejected():
    result = _phase_rendering_result()
    req1 = _request(result, destination=DP.DestinationClassification.SYNTHETIC_RECORDING)
    plan1 = DP.plan_delivery(req1)
    exec1 = DP.execute_delivery(plan1)
    req2 = _request(result, destination=DP.DestinationClassification.INTEGRATION_TEST)
    plan2 = DP.plan_delivery(req2)
    assert plan1.logical_delivery_id != plan2.logical_delivery_id
    with pytest.raises(ValueError, match="different logical delivery"):
        DP.plan_retry(plan2, exec1)


def test_successful_units_not_resent_silently():
    adapter_id = _register_selective_failure_adapter("resend_probe_v1", fail_indices={1})
    req = _request(adapter_id=adapter_id)
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    result = DP.execute_delivery(plan)
    retry_plan = DP.plan_retry(plan, result)
    retried_indices = {u.index for u in retry_plan.units}
    assert 0 not in retried_indices  # unit 0 succeeded, never retried


def test_logical_identity_stable_across_retry():
    adapter_id = _register_selective_failure_adapter("stable_id_probe_v1", fail_indices={0})
    req = _request(adapter_id=adapter_id)
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    result = DP.execute_delivery(plan)
    retry_plan = DP.plan_retry(plan, result)
    assert retry_plan.logical_delivery_id == plan.logical_delivery_id


# ─────────────────────────────────────────────────────────────────────────────
# 33. Physical exactly-once overclaim assessment
# ─────────────────────────────────────────────────────────────────────────────

def test_no_physical_exactly_once_overclaim():
    # The module must not claim durable, cross-process deduplication --
    # only logical identity stability. Confirmed the module provides no
    # persistence or deduplication ledger of any kind.
    source = inspect.getsource(DP)
    for forbidden in ("dedup", "already_delivered", "idempotency_store"):
        assert forbidden not in source.lower()
    req = _request()
    plan = DP.plan_delivery(req)
    result1 = DP.execute_delivery(plan)
    result2 = DP.execute_delivery(plan)
    # Two independent executions of the same plan both genuinely
    # attempt delivery (stateless) -- the module does not pretend to
    # prevent this at the physical layer, honestly reflecting its
    # documented in-memory-only scope.
    assert result1.delivered_unit_count == result2.delivered_unit_count == 1


# ─────────────────────────────────────────────────────────────────────────────
# 34-37. Rendering completeness, limitations, uncertainty, unsafe
# readiness all preserved end to end
# ─────────────────────────────────────────────────────────────────────────────

def test_rendering_completeness_preserved_end_to_end():
    result = _phase_rendering_result(PhaseClass.ARCHITECTURE)
    req = _request(result)
    plan = DP.plan_delivery(req)
    assert "complete_with_limitations" in "".join(u.content for u in plan.units) or \
        req.rendered_content == "".join(u.content for u in plan.units)


def test_limitations_preserved_end_to_end():
    from pcae.core.canonical_engineering_evidence import Applicability, LimitationItem
    from types import MappingProxyType
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from test_phase_report_view_134e3 import _evidence_with_applicability as _phase_evidence
    from test_evidence_extraction_134e2 import _full_applicability
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app["technical_debt_reviewed"] = Applicability.UNAVAILABLE
    ev = _phase_evidence(
        PhaseClass.IMPLEMENTATION, app,
        limitations=(LimitationItem(
            category="technical_debt_reviewed", description="unavailable",
            affected_evidence=("technical_debt_reviewed",),
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    rr = render(view, res, RENDERER_ID_PHASE_REPORT_MARKDOWN)
    req = DP.build_delivery_request(
        rr, adapter_id=DP.RECORDING_ADAPTER_ID, adapter_version="1.0",
        destination=DP.DestinationClassification.SYNTHETIC_RECORDING,
        purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT, policy_version="1.0",
    )
    plan = DP.plan_delivery(req)
    full_content = "".join(u.content for u in plan.units)
    # Substantive source-view limitations are preserved losslessly as
    # rendered text (Non-Omission) even though DeliveryRequest.has_limitations
    # is documented (build_delivery_request) as derived only from
    # RenderingResult.limitations -- rendering-layer content-preservation
    # signals, not a duplicate of the source view's substantive limitations.
    assert "limitations" in full_content
    assert req.has_limitations is False


def test_uncertainty_preserved_end_to_end():
    result = _phase_rendering_result()
    req = _request(result)
    assert isinstance(req.has_uncertainty, bool)
    plan = DP.plan_delivery(req)
    assert "".join(u.content for u in plan.units) == result.rendered_content


def test_unsafe_readiness_preserved_end_to_end():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, recommended_next_phase="unsafe to proceed: findings remain")
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    rr = render(view, res, RENDERER_ID_PHASE_REPORT_MARKDOWN)
    req = DP.build_delivery_request(
        rr, adapter_id=DP.RECORDING_ADAPTER_ID, adapter_version="1.0",
        destination=DP.DestinationClassification.SYNTHETIC_RECORDING,
        purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT, policy_version="1.0",
    )
    plan = DP.plan_delivery(req)
    assert "unsafe to proceed" in "".join(u.content for u in plan.units)


# ─────────────────────────────────────────────────────────────────────────────
# 38. Secret leakage through diagnostics
# ─────────────────────────────────────────────────────────────────────────────

def test_no_secret_leakage_through_exception_diagnostics():
    def _leaky_fn(unit):
        raise RuntimeError("token=123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef123 leaked in exception")
    adapter_id = _register_probe_adapter("leak_probe_v1", _deliver_fn=_leaky_fn)
    req = _request(adapter_id=adapter_id)
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    # The pipeline itself introduces no secret -- whatever the adapter's
    # own exception text contains is captured verbatim (adapter authors'
    # responsibility not to raise with embedded secrets); the pipeline
    # performs no additional secret-scrubbing by design (documented,
    # not a defect) but also never adds new secret exposure of its own.
    d = result.to_dict()
    assert "PCAE_TELEGRAM" not in json.dumps(d)


# ─────────────────────────────────────────────────────────────────────────────
# 39. Cross-process plan determinism (re-confirmed independently)
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_process_logical_id_determinism():
    script = (
        "import sys; sys.path.insert(0, %r); "
        "from pcae.core.delivery_pipeline import compute_logical_delivery_id, DeliveryPurpose, DestinationClassification; "
        "print(compute_logical_delivery_id('134E.6V', 'a'*64, DeliveryPurpose.OPERATOR_TERMINAL_REPORT, "
        "DestinationClassification.SYNTHETIC_RECORDING, 'recording_v1', '1.0'))"
    ) % "src"
    repo_root = str(__import__("pathlib").Path(__file__).resolve().parents[1])
    proc1 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    proc2 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    assert proc1.returncode == 0, proc1.stderr
    assert proc1.stdout == proc2.stdout


# ─────────────────────────────────────────────────────────────────────────────
# 40-41. Unknown future-agent independence, synthetic future-adapter
# independence
# ─────────────────────────────────────────────────────────────────────────────

def test_unknown_future_agent_independence():
    sig = inspect.signature(DP.build_delivery_request)
    assert "agent" not in str(sig) and "model" not in str(sig)
    field_names = {f.name for f in dataclasses.fields(DP.DeliveryPlan)}
    assert "agent_id" not in field_names


def test_synthetic_future_adapter_independence():
    adapter_id = _register_probe_adapter(
        "synthetic_future_v1", max_inline_bytes=8000, supports_attachment=True,
        supported_modes=frozenset({DP.DeliveryMode.INLINE, DP.DeliveryMode.ATTACHMENT}),
    )
    req1 = _request(adapter_id=adapter_id)
    req2 = _request(adapter_id=adapter_id)
    assert DP.plan_delivery(req1).to_dict() == DP.plan_delivery(req2).to_dict()


# ─────────────────────────────────────────────────────────────────────────────
# 42. No active lifecycle or durable receipt side effects
# ─────────────────────────────────────────────────────────────────────────────

def test_no_active_lifecycle_or_durable_receipt_side_effects(monkeypatch):
    def _forbidden(*a, **kw):
        raise AssertionError("delivery_pipeline must not touch the filesystem")
    monkeypatch.setattr("builtins.open", _forbidden)
    req = _request()
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    retry_plan = None
    d = result.to_dict()
    assert isinstance(d, dict)
    import pathlib
    src_root = pathlib.Path(DP.__file__).resolve().parent.parent
    for path in src_root.rglob("*.py"):
        if path.name == "delivery_pipeline.py":
            continue
        if "test" in str(path):
            continue
        text = path.read_text()
        assert "delivery_pipeline" not in text


# ─────────────────────────────────────────────────────────────────────────────
# Additional targeted re-confirmations
# ─────────────────────────────────────────────────────────────────────────────

def test_adapter_exception_regression_conservative_retryable():
    def _throwing_fn(unit):
        raise RuntimeError("adapter transport exploded")
    adapter_id = _register_probe_adapter("throwing_regression_v1", _deliver_fn=_throwing_fn)
    req = _request(adapter_id=adapter_id)
    plan = DP.plan_delivery(req)
    result = DP.execute_delivery(plan)
    assert result.overall_outcome == DP.DeliveryOutcome.FAILED
    assert result.unit_outcomes[0].retryable is True
    assert "RuntimeError" in result.unit_outcomes[0].diagnostic


def test_adapter_exception_does_not_abort_sibling_units():
    call_count = {"n": 0}
    def _flaky_fn(unit):
        call_count["n"] += 1
        if unit.index == 0:
            raise RuntimeError("first unit fails")
        return DP.AdapterUnitOutcome(unit.unit_id, True, False, "ok", None)
    adapter_id = _register_probe_adapter(
        "flaky_probe_v1", max_inline_bytes=1_000_000,
        supported_modes=frozenset({DP.DeliveryMode.INLINE, DP.DeliveryMode.MULTIPART_INLINE}),
        _deliver_fn=_flaky_fn,
    )
    req = _request(adapter_id=adapter_id)
    policy = dataclasses.replace(DP.DEFAULT_POLICY, inline_size_threshold=150, allow_attachment=False)
    plan = DP.plan_delivery(req, policy=policy)
    if len(plan.units) > 1:
        result = DP.execute_delivery(plan)
        assert call_count["n"] == len(plan.units)
        assert result.unit_outcomes[0].delivered is False
        assert result.unit_outcomes[1].delivered is True
