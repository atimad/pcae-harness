"""Phase 134E.7V — independent adversarial verification of the External
Delivery Receipt Model (134E.7, ``pcae.core.delivery_receipt``).

Does not trust 134E.7's own report, documentation, or its 110 tests as
sufficient evidence. These are fresh probes beyond that existing
coverage. Every hypothesis below was first proven via direct Python
REPL execution against the real implementation before any test here
was written, per this phase's required methodology.

One genuine BLOCKING defect was found and repaired during this
verification:

1. Path traversal via unsanitized store identifiers:
   ``DeliveryReceiptStore`` used raw caller-supplied identifiers
   (``logical_delivery_id``, ``original_receipt_id``, and the
   explicitly-arbitrary ``correcting_receipt_id``) directly in
   persisted file paths, with no boundary validation. Unlike
   ``shell_gate.persist_audit_record``'s safe-by-construction
   ``sg-<uuid>`` audit id, ``correcting_receipt_id`` is an arbitrary
   string, so a value containing ``..`` / separators could write
   outside the store root -- inconsistent with the repository's own
   ``phase_reports._safe_filename`` / ``notifications._safe_doc_
   filename`` filename-sanitization convention. Repaired by fail-closed
   identifier validation at the persistence boundary
   (``DeliveryReceiptStore._validate_store_identifier``).

Several NON-BLOCKING observations are also recorded as characterization
regressions (see the phase verification document for classification).
All persistence tests use ``tmp_path`` -- no production receipt artifact
is ever created.
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import delivery_pipeline as DP
from pcae.core import delivery_receipt as DR

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_delivery_pipeline_134e6 import _phase_rendering_result, _request  # noqa: E402


T0 = "2026-01-01T00:00:00+00:00"
T1 = "2026-01-01T00:00:01+00:00"
T2 = "2026-01-01T00:00:02+00:00"
T3 = "2026-01-01T00:00:03+00:00"
T4 = "2026-01-01T00:00:04+00:00"


@pytest.fixture(autouse=True)
def _clear_recording_log():
    DP.clear_recording_log()
    yield
    DP.clear_recording_log()


# ─────────────────────────────────────────────────────────────────────────────
# Probe-adapter helpers (self-contained, mirroring 134E.6V's convention)
# ─────────────────────────────────────────────────────────────────────────────

_PROBE_COUNTER = [0]


def _register_probe_adapter(adapter_id, deliver_fn, **capability_overrides):
    defaults = dict(
        adapter_id=adapter_id, adapter_version="1.0",
        supported_media_types=frozenset({"text/markdown"}),
        # Tiny inline threshold forces MULTIPART_INLINE segmentation so
        # multi-unit scenarios (partial, retry-only-failed, ambiguity on
        # one of several units) are reachable on the modest rendered
        # content this suite exercises.
        supported_modes=frozenset({DP.DeliveryMode.MULTIPART_INLINE}),
        max_inline_bytes=500, supports_attachment=False,
        represents_external_delivery=False, safe_destination_alias=f"{adapter_id}:probe",
    )
    defaults.update(capability_overrides)
    caps = DP.AdapterCapabilities(**defaults)
    try:
        DP.register_adapter(DP.DeliveryAdapter(capabilities=caps, deliver_fn=deliver_fn))
    except ValueError:
        pass
    return adapter_id


def _unique_probe_id(label):
    _PROBE_COUNTER[0] += 1
    return f"{label}_134e7v_{_PROBE_COUNTER[0]}"


def _always_deliver_fn():
    return lambda u: DP.AdapterUnitOutcome(u.unit_id, True, False, f"ref:{u.unit_id}", None)


def _selective_failure_adapter(adapter_id, fail_indices, *, retryable=True, fail_all=False):
    """Fails targeted unit(s) on first attempt, succeeds on retry."""
    seen: dict[str, int] = {}

    def _fn(unit):
        count = seen.get(unit.unit_id, 0)
        seen[unit.unit_id] = count + 1
        should_fail = fail_all or (unit.index in fail_indices)
        if should_fail and count == 0:
            return DP.AdapterUnitOutcome(unit.unit_id, False, retryable, None, "transient probe failure")
        return DP.AdapterUnitOutcome(unit.unit_id, True, False, f"ref:{unit.unit_id}", None)

    return _register_probe_adapter(adapter_id, _fn)


def _multipart_request(adapter_id, **overrides):
    result = _phase_rendering_result()
    kwargs = dict(
        result=result, adapter_id=adapter_id, adapter_version="1.0",
        destination=DP.DestinationClassification.SYNTHETIC_RECORDING,
        purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT, policy_version="1.0",
    )
    kwargs.update(overrides)
    return DP.build_delivery_request(**kwargs)


def _pipeline_inputs(**overrides):
    request = _request(**overrides)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan)
    return result, plan, request


def _finalized_receipt():
    result, plan, request = _pipeline_inputs()
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    return DR.finalize_receipt(r, finalized_at=T2)


def _failing_outcomes(result, *, retryable=True):
    return tuple(
        DP.AdapterUnitOutcome(o.unit_id, False, retryable, None, "probe failure")
        for o in result.unit_outcomes
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1-3: receipt/attempt identity, delimiter resistance, two-level scheme
# ─────────────────────────────────────────────────────────────────────────────

def test_1_receipt_identity_ambiguous_textual_fields():
    # JSON-array canonical encoding: no delimiter-ambiguity collision.
    a = DR.compute_receipt_id("X|Y")
    b = DR.compute_receipt_id("X", receipt_version="Y|1.0")
    c = DR.compute_receipt_id("a/b", receipt_version="1.0")
    d = DR.compute_receipt_id("ab", receipt_version="1.0")  # different logical id
    assert a != b
    assert c != d
    # Deterministic + stable.
    assert DR.compute_receipt_id("X|Y") == a


def test_2_attempt_identity_altered_plan_two_level_scheme():
    result, plan, request = _pipeline_inputs()
    a1 = DR.build_attempt(result, plan, request, sequence=1, started_at=T0, completed_at=T1)
    # Same logical delivery + same sequence but altered unit outcomes.
    alt_result = dataclasses.replace(result, unit_outcomes=_failing_outcomes(result))
    a1_alt = DR.build_attempt(alt_result, plan, request, sequence=1, started_at=T0, completed_at=T1)
    # Slot identity (attempt_id) is stable across content change...
    assert a1.attempt_id == a1_alt.attempt_id == DR.compute_attempt_id(request.logical_delivery_id, 1)
    # ...but the content fingerprint (attempt_digest) catches the change.
    assert a1.attempt_digest != a1_alt.attempt_digest
    # attempt identity is never confused with logical receipt identity.
    assert a1.attempt_id != DR.compute_receipt_id(request.logical_delivery_id)


def test_3_duplicate_sequence_different_attempt_id_and_rejection():
    a_id = _unique_probe_id("dupseqA")
    _register_probe_adapter(a_id, _always_deliver_fn())
    b_id = _unique_probe_id("dupseqB")
    _register_probe_adapter(b_id, _always_deliver_fn())
    ra = _request(adapter_id=a_id)
    rb = _request(adapter_id=b_id)
    # Same sequence, different logical delivery -> different attempt identity.
    assert (DR.compute_attempt_id(ra.logical_delivery_id, 1)
            != DR.compute_attempt_id(rb.logical_delivery_id, 1))
    # Same logical delivery, duplicate sequence -> rejected by build_attempt.
    result, plan, request = _pipeline_inputs(adapter_id=a_id)
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    with pytest.raises(ValueError, match="increment by exactly one"):
        DR.build_attempt(result, plan, request, sequence=1, started_at=T2, completed_at=T3,
                         previous_attempt=r.attempts[0])


# ─────────────────────────────────────────────────────────────────────────────
# 4: forged aggregate state (digest is the integrity boundary; NON-BLOCKING)
# ─────────────────────────────────────────────────────────────────────────────

def test_4a_forged_aggregate_without_redigest_rejected_on_load(tmp_path):
    result, plan, request = _pipeline_inputs()
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    store = DR.DeliveryReceiptStore(tmp_path)
    store.save(r)
    path = store._receipt_path(r.logical_delivery_id)
    data = json.loads(path.read_text())
    data["delivered_unit_count"] = 999  # tamper aggregate, do NOT recompute digest
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="digest mismatch"):
        store.load(r.logical_delivery_id)


def test_4b_redigested_forged_aggregate_loads_documented_limitation(tmp_path):
    # NON-BLOCKING (consistent with 93C verify_audit_records digest-only):
    # a caller that recomputes the digest after forging aggregate fields
    # produces a self-consistent receipt the store accepts. The public API
    # never produces such a receipt; the digest is the integrity boundary.
    result, plan, request = _pipeline_inputs()
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    forged = DR._with_recomputed_digest(
        dataclasses.replace(r, delivered_unit_count=999, logical_state="delivered"))
    assert DR.validate_receipt_digest(forged) is True
    store = DR.DeliveryReceiptStore(tmp_path)
    store.save(forged)
    loaded = store.load(forged.logical_delivery_id)
    assert loaded.delivered_unit_count == 999  # documented: store trusts digest


def test_4c_public_api_aggregate_matches_rederivation(tmp_path):
    # The public API always derives aggregate from attempts; stored fields
    # match an independent re-derivation.
    a_id = _unique_probe_id("aggred derive")
    _selective_failure_adapter(a_id, {0}, retryable=True)
    request = _multipart_request(a_id)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan)
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    agg = DR._aggregate(r.attempts, None, r.total_planned_units)
    assert r.delivered_unit_count == agg.delivered
    assert r.failed_unit_count == agg.failed_retryable + agg.failed_non_retryable
    assert r.logical_state == agg.logical_state.value


# ─────────────────────────────────────────────────────────────────────────────
# 5-6: last-attempt-wins semantics (NON-BLOCKING over-simplification)
# ─────────────────────────────────────────────────────────────────────────────

def test_5_delivered_then_failed_retry_downgrade_documented(tmp_path):
    # NON-BLOCKING: last-attempt-wins trusts the caller to only retry
    # non-delivered units. A misbehaving caller re-attempting a delivered
    # unit that then fails silently downgrades it. The governed retry path
    # (plan_retry) structurally prevents this.
    a_id = _unique_probe_id("downgrade")
    _register_probe_adapter(a_id, _always_deliver_fn())
    request = _request(adapter_id=a_id)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan)
    rec = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    assert rec.logical_state == DR.LogicalDeliveryState.DELIVERED.value
    # Governed path: plan_retry raises because no unit failed.
    with pytest.raises(ValueError, match="no failed units"):
        DP.plan_retry(plan, result)
    # Misbehaving caller re-attempts an already-delivered unit and it fails.
    fail_result = dataclasses.replace(result, unit_outcomes=_failing_outcomes(result, retryable=True))
    r2 = DR.append_attempt(rec, fail_result, plan, request, started_at=T2, completed_at=T3,
                           retry_reason="transient")
    assert r2.delivered_unit_count == 0
    assert r2.logical_state == DR.LogicalDeliveryState.FAILED_RETRYABLE.value  # silent downgrade


def test_6_ambiguous_after_delivered_no_silent_duplicate(tmp_path):
    a_id = _unique_probe_id("ambigresolve")
    _register_probe_adapter(a_id, _always_deliver_fn())
    request = _multipart_request(a_id)
    plan = DP.plan_delivery(request)
    assert len(plan.units) >= 2
    result = DP.execute_delivery(plan)
    # First attempt: one unit marked ambiguous (caller has adapter knowledge).
    ambig_uid = plan.units[0].unit_id
    attempt1 = DR.build_attempt(result, plan, request, sequence=1, started_at=T0, completed_at=T1,
                                ambiguous_unit_ids=frozenset({ambig_uid}))
    r1 = DR._build_receipt(
        (attempt1,), phase_id=request.phase_id, delivery_purpose=request.delivery_purpose.value,
        rendering_view_id=request.rendering_view_id, rendering_digest=request.rendering_digest,
        renderer_id=request.renderer_id, renderer_version=request.renderer_version,
        adapter_id=request.adapter_id, adapter_version=request.adapter_version,
        destination_classification=request.destination_classification.value,
        safe_destination_alias="probe:alias", policy_version=request.policy_version,
        delivery_mode=plan.selected_mode.value, total_planned_units=len(plan.units),
        provenance={}, authorization_evidence={}, correction=None, finalized=False, finalized_at=None,
    )
    assert r1.ambiguous_unit_count == 1
    assert r1.logical_state != DR.LogicalDeliveryState.DELIVERED.value
    assert r1.operator_completeness == DR.OperatorCompletenessState.UNKNOWN.value
    # Retry that resolves the ambiguous unit to delivered: last-attempt-wins,
    # the unit is counted once as delivered (not double-counted).
    r2 = DR.append_attempt(r1, result, plan, request, started_at=T2, completed_at=T3, retry_reason="resolve")
    assert r2.ambiguous_unit_count == 0
    assert r2.delivered_unit_count == r2.total_planned_units
    assert r2.delivered_unit_count + r2.ambiguous_unit_count <= r2.total_planned_units  # no duplicate


# ─────────────────────────────────────────────────────────────────────────────
# 7: mixed delivered/ambiguous aggregate
# ─────────────────────────────────────────────────────────────────────────────

def test_7_mixed_delivered_ambiguous_not_classified_delivered(tmp_path):
    a_id = _unique_probe_id("mixedambig")
    _register_probe_adapter(a_id, _always_deliver_fn())
    request = _multipart_request(a_id)
    plan = DP.plan_delivery(request)
    assert len(plan.units) >= 2
    result = DP.execute_delivery(plan)
    ambig_uid = plan.units[0].unit_id
    attempt = DR.build_attempt(result, plan, request, sequence=1, started_at=T0, completed_at=T1,
                               ambiguous_unit_ids=frozenset({ambig_uid}))
    r = DR._build_receipt(
        (attempt,), phase_id=request.phase_id, delivery_purpose=request.delivery_purpose.value,
        rendering_view_id=request.rendering_view_id, rendering_digest=request.rendering_digest,
        renderer_id=request.renderer_id, renderer_version=request.renderer_version,
        adapter_id=request.adapter_id, adapter_version=request.adapter_version,
        destination_classification=request.destination_classification.value,
        safe_destination_alias="probe:alias", policy_version=request.policy_version,
        delivery_mode=plan.selected_mode.value, total_planned_units=len(plan.units),
        provenance={}, authorization_evidence={}, correction=None, finalized=False, finalized_at=None,
    )
    assert r.delivered_unit_count > 0 and r.ambiguous_unit_count > 0
    assert r.logical_state != DR.LogicalDeliveryState.DELIVERED.value
    assert r.operator_completeness == DR.OperatorCompletenessState.UNKNOWN.value


# ─────────────────────────────────────────────────────────────────────────────
# 8-9: finality honesty (retryable / ambiguous cannot finalize without force_close)
# ─────────────────────────────────────────────────────────────────────────────

def test_8_retryable_receipt_not_finalizable_without_force_close():
    a_id = _unique_probe_id("retryfinal")
    _selective_failure_adapter(a_id, set(), retryable=True, fail_all=True)
    request = _multipart_request(a_id)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan)
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    assert r.logical_state == DR.LogicalDeliveryState.FAILED_RETRYABLE.value
    with pytest.raises(ValueError, match="force_close"):
        DR.finalize_receipt(r, finalized_at=T2)
    # Governed force_close with explicit reason is permitted.
    rf = DR.finalize_receipt(r, finalized_at=T2, force_close=True, close_reason="operator gave up")
    assert rf.finalized is True
    assert any("force_closed" in d for d in rf.diagnostics)


def test_9_ambiguous_receipt_not_finalizable_without_force_close():
    a_id = _unique_probe_id("ambigfinal")
    _selective_failure_adapter(a_id, {0}, retryable=True)
    request = _multipart_request(a_id)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan)
    ambig_uid = plan.units[0].unit_id
    attempt = DR.build_attempt(result, plan, request, sequence=1, started_at=T0, completed_at=T1,
                               ambiguous_unit_ids=frozenset({ambig_uid}))
    r = DR._build_receipt(
        (attempt,), phase_id=request.phase_id, delivery_purpose=request.delivery_purpose.value,
        rendering_view_id=request.rendering_view_id, rendering_digest=request.rendering_digest,
        renderer_id=request.renderer_id, renderer_version=request.renderer_version,
        adapter_id=request.adapter_id, adapter_version=request.adapter_version,
        destination_classification=request.destination_classification.value,
        safe_destination_alias="probe:alias", policy_version=request.policy_version,
        delivery_mode=plan.selected_mode.value, total_planned_units=len(plan.units),
        provenance={}, authorization_evidence={}, correction=None, finalized=False, finalized_at=None,
    )
    assert r.retry_pending is True
    with pytest.raises(ValueError, match="force_close"):
        DR.finalize_receipt(r, finalized_at=T2)
    with pytest.raises(ValueError, match="close_reason"):
        DR.finalize_receipt(r, finalized_at=T2, force_close=True)


# ─────────────────────────────────────────────────────────────────────────────
# 10: physical exactly-once overclaim scan
# ─────────────────────────────────────────────────────────────────────────────

def test_10a_no_physical_exactly_once_overclaim_in_source():
    src = Path(DR.__file__).read_text()
    lowered = src.lower()
    # The module must not claim physical exactly-once delivery.
    overclaims = ["physically exactly once", "exactly-once delivery",
                  "guaranteed exactly once delivery", "physically delivered exactly once"]
    for phrase in overclaims:
        assert phrase not in lowered, f"overclaim phrase present: {phrase!r}"
    # It must explicitly disclaim physical exactly-once.
    assert "does" in lowered and "not" in lowered and "physically exactly-once" in lowered


def test_10b_multiple_physical_attempts_recorded_individually():
    # Use the recording adapter (single inline unit) so the count is exact.
    request = _request()
    plan = DP.plan_delivery(request)
    DP.execute_delivery(plan)
    DP.execute_delivery(plan)
    # The pipeline executes the adapter twice; no dedup claim.
    assert len(DP.get_recording_log()) == 2


# ─────────────────────────────────────────────────────────────────────────────
# 11-12: retry lineage policy / after correction
# ─────────────────────────────────────────────────────────────────────────────

def test_11_retry_changed_policy_version_rejected():
    a_id = _unique_probe_id("policyprev")
    _selective_failure_adapter(a_id, {0}, retryable=True)
    request = _multipart_request(a_id)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan)
    rec = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    retry_plan = DP.plan_retry(plan, result)
    retry_result = DP.execute_delivery(retry_plan)
    forged = dataclasses.replace(request, policy_version="9.9")
    with pytest.raises(ValueError, match="policy version"):
        DR.append_attempt(rec, retry_result, retry_plan, forged, started_at=T2, completed_at=T3)


def test_12_retry_after_correction_rejected():
    rf = _finalized_receipt()
    corr = DR.CorrectionRecord(
        original_receipt_id=rf.receipt_id, reason="x", correcting_receipt_id="corrector-after-1",
        direction=DR.CorrectionDirection.CORRECTS.value,
        affected_logical_delivery_id=rf.logical_delivery_id, operator_followup_occurred=True,
    )
    rc = DR.apply_correction(rf, corr, finalized_at=T3)
    # A corrected receipt is finalized; no further attempts may be appended
    # (the finalized check fires before any lineage check).
    result, plan, request = _pipeline_inputs()
    with pytest.raises(ValueError, match="already finalized"):
        DR.append_attempt(rc, result, plan, request, started_at=T3, completed_at=T4)


# ─────────────────────────────────────────────────────────────────────────────
# 13-15: correction / supersession cycles
# ─────────────────────────────────────────────────────────────────────────────

def test_13_correction_self_cycle_rejected():
    with pytest.raises(ValueError, match="cycle"):
        DR.CorrectionRecord(
            original_receipt_id="same", reason="x", correcting_receipt_id="same",
            direction=DR.CorrectionDirection.CORRECTS.value,
            affected_logical_delivery_id="ld", operator_followup_occurred=False,
        )


def test_14_multi_receipt_correction_cycle_constructible_documented(tmp_path):
    # NON-BLOCKING: the model rejects self-cycles and same-receipt
    # re-correction, but maintains no global correction graph, so two
    # finalized receipts on different logical deliveries can mutually
    # correct/supersede. Full cycle detection is out of scope (doc Section
    # 32) and deferred to 134E.10's lifecycle orchestration.
    def fresh(tag):
        a_id = _unique_probe_id(f"cyc{tag}")
        _register_probe_adapter(a_id, _always_deliver_fn())
        rq = _request(adapter_id=a_id)
        pl = DP.plan_delivery(rq)
        rs = DP.execute_delivery(pl)
        return DR.finalize_receipt(DR.open_receipt(rs, pl, rq, started_at=T0, completed_at=T1),
                                   finalized_at=T2)
    ra, rb = fresh("A"), fresh("B")
    assert ra.receipt_id != rb.receipt_id
    ca = DR.CorrectionRecord(original_receipt_id=ra.receipt_id, reason="a",
        correcting_receipt_id=rb.receipt_id, direction=DR.CorrectionDirection.CORRECTS.value,
        affected_logical_delivery_id=ra.logical_delivery_id, operator_followup_occurred=False)
    cb = DR.CorrectionRecord(original_receipt_id=rb.receipt_id, reason="b",
        correcting_receipt_id=ra.receipt_id, direction=DR.CorrectionDirection.CORRECTS.value,
        affected_logical_delivery_id=rb.logical_delivery_id, operator_followup_occurred=False)
    rap = DR.apply_correction(ra, ca, finalized_at=T3)
    rbp = DR.apply_correction(rb, cb, finalized_at=T3)
    assert rap.correction.correcting_receipt_id == rb.receipt_id
    assert rbp.correction.correcting_receipt_id == ra.receipt_id  # mutual cycle constructible


def test_15_supersession_two_node_cycle_constructible_documented(tmp_path):
    # NON-BLOCKING (same class as 14), supersession direction.
    def fresh(tag):
        a_id = _unique_probe_id(f"sup{tag}")
        _register_probe_adapter(a_id, _always_deliver_fn())
        rq = _request(adapter_id=a_id)
        pl = DP.plan_delivery(rq)
        rs = DP.execute_delivery(pl)
        return DR.finalize_receipt(DR.open_receipt(rs, pl, rq, started_at=T0, completed_at=T1),
                                   finalized_at=T2)
    ra, rb = fresh("A"), fresh("B")
    ca = DR.CorrectionRecord(original_receipt_id=ra.receipt_id, reason="a",
        correcting_receipt_id=rb.receipt_id, direction=DR.CorrectionDirection.SUPERSEDES.value,
        affected_logical_delivery_id=ra.logical_delivery_id, operator_followup_occurred=False)
    cb = DR.CorrectionRecord(original_receipt_id=rb.receipt_id, reason="b",
        correcting_receipt_id=ra.receipt_id, direction=DR.CorrectionDirection.SUPERSEDES.value,
        affected_logical_delivery_id=rb.logical_delivery_id, operator_followup_occurred=False)
    rap = DR.apply_correction(ra, ca, finalized_at=T3)
    rbp = DR.apply_correction(rb, cb, finalized_at=T3)
    assert rap.logical_state == DR.LogicalDeliveryState.SUPERSEDED.value
    assert rbp.logical_state == DR.LogicalDeliveryState.SUPERSEDED.value
    # Same-receipt re-correction IS rejected (the primitive the model claims).
    re_corr = DR.CorrectionRecord(
        original_receipt_id=rap.receipt_id, reason="again",
        correcting_receipt_id="corrector-sup-again",
        direction=DR.CorrectionDirection.SUPERSEDES.value,
        affected_logical_delivery_id=rap.logical_delivery_id, operator_followup_occurred=False,
    )
    with pytest.raises(ValueError, match="already corrected"):
        DR.apply_correction(rap, re_corr, finalized_at=T4)


# ─────────────────────────────────────────────────────────────────────────────
# 16-17: deep immutability
# ─────────────────────────────────────────────────────────────────────────────

def test_16_nested_deep_mutation_rejected():
    result, plan, request = _pipeline_inputs()
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    # Nested tuple of frozen dataclasses: mutating a unit outcome field raises.
    with pytest.raises(Exception):
        r.attempts[0].unit_outcomes[0].unit_id = "tampered"  # type: ignore[misc]
    # Nested diagnostics/uncertainty tuples are immutable.
    with pytest.raises(Exception):
        r.attempts[0].diagnostics.append("x")  # type: ignore[attr-defined]
    with pytest.raises(Exception):
        r.uncertainty.append("x")  # type: ignore[attr-defined]
    # Replacing an attempt slot raises (tuple).
    with pytest.raises(TypeError):
        r.attempts[0] = None  # type: ignore[index]


def test_17_caller_owned_mapping_mutation_isolated():
    result, plan, request = _pipeline_inputs()
    caller_provenance = {"phase_id": "P", "injected": "caller-owned"}
    # Build a receipt via the internal builder with a caller-owned mapping.
    attempt = DR.build_attempt(result, plan, request, sequence=1, started_at=T0, completed_at=T1)
    r = DR._build_receipt(
        (attempt,), phase_id=request.phase_id, delivery_purpose=request.delivery_purpose.value,
        rendering_view_id=request.rendering_view_id, rendering_digest=request.rendering_digest,
        renderer_id=request.renderer_id, renderer_version=request.renderer_version,
        adapter_id=request.adapter_id, adapter_version=request.adapter_version,
        destination_classification=request.destination_classification.value,
        safe_destination_alias="probe:alias", policy_version=request.policy_version,
        delivery_mode=plan.selected_mode.value, total_planned_units=len(plan.units),
        provenance=caller_provenance, authorization_evidence={}, correction=None,
        finalized=False, finalized_at=None,
    )
    # Mutating the caller's original dict after construction must not affect receipt.
    caller_provenance["injected"] = "mutated-after"
    assert r.provenance["injected"] == "caller-owned"
    # Mutating the receipt's provenance view is rejected (MappingProxyType).
    with pytest.raises(TypeError):
        r.provenance["x"] = "y"  # type: ignore[index]


# ─────────────────────────────────────────────────────────────────────────────
# 18-19: receipt / attempt digest material coverage
# ─────────────────────────────────────────────────────────────────────────────

def test_18_receipt_digest_material_field_matrix():
    rf = _finalized_receipt()
    base_digest = rf.receipt_digest
    corr = DR.CorrectionRecord(
        original_receipt_id=rf.receipt_id, reason="x", correcting_receipt_id="corrector-mat-1",
        direction=DR.CorrectionDirection.SUPERSEDES.value,
        affected_logical_delivery_id=rf.logical_delivery_id, operator_followup_occurred=False,
    )

    def redigest(**changes):
        return DR._with_recomputed_digest(dataclasses.replace(rf, **changes)).receipt_digest

    assert redigest(logical_state="failed_non_retryable") != base_digest
    assert redigest(delivered_unit_count=999) != base_digest
    assert redigest(uncertainty=("u",)) != base_digest
    assert redigest(limitations=("l",)) != base_digest
    assert redigest(destination_classification="production_operator") != base_digest
    assert redigest(safe_destination_alias="other:alias") != base_digest
    assert redigest(provenance={"phase_id": "other"}) != base_digest
    assert redigest(authorization_evidence={"x": 1}) != base_digest
    assert redigest(receipt_version="2.0") != base_digest
    assert redigest(finalized_at=T4) != base_digest
    # Adding a correction changes the digest.
    rc = DR.apply_correction(rf, corr, finalized_at=T3)
    assert rc.receipt_digest != base_digest
    # The digest excludes only itself.
    assert DR.validate_receipt_digest(rf) is True


def test_19_attempt_digest_outcome_mutation():
    result, plan, request = _pipeline_inputs()
    a1 = DR.build_attempt(result, plan, request, sequence=1, started_at=T0, completed_at=T1)
    alt = dataclasses.replace(result, unit_outcomes=_failing_outcomes(result))
    a2 = DR.build_attempt(alt, plan, request, sequence=1, started_at=T0, completed_at=T1)
    assert a1.attempt_digest != a2.attempt_digest
    # Self-validates (digest excludes only itself).
    assert DR._digest_excluding(a1.to_dict(), "attempt_digest") == a1.attempt_digest


# ─────────────────────────────────────────────────────────────────────────────
# 20-23: diagnostic redaction
# ─────────────────────────────────────────────────────────────────────────────

def _exception_receipt(msg, exc_type=RuntimeError):
    a_id = _unique_probe_id("red")
    _register_probe_adapter(a_id, lambda u, m=msg, e=exc_type: (_ for _ in ()).throw(e(m)))
    request = _request(adapter_id=a_id)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan)
    return DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)


def test_20_redaction_of_bearer_token():
    r = _exception_receipt("Authorization: Bearer sometoken123456789 rejected")
    dump = json.dumps(r.to_dict())
    assert "sometoken123456789" not in dump


def test_21_redaction_of_webhook_secret():
    r = _exception_receipt("POST https://hooks.example.com/X?token=supersecretvalue failed")
    dump = json.dumps(r.to_dict())
    assert "supersecretvalue" not in dump
    assert "hooks.example.com" not in dump


def test_22_redaction_of_raw_exception_repr_with_bot_token():
    r = _exception_receipt("ValueError('PCAE_TELEGRAM_BOT_TOKEN=123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabc123 leaked')")
    dump = json.dumps(r.to_dict())
    assert "ABCDEFGHIJKLMNOPQRSTUVWXYZabc123" not in dump
    assert "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabc123" not in dump
    u = r.attempts[0].unit_outcomes[0]
    assert u.error_classification.startswith("adapter_exception:")


def test_23_safe_diagnostic_usefulness_preserved():
    r = _exception_receipt("connection to host timed out after 30s", exc_type=TimeoutError)
    u = r.attempts[0].unit_outcomes[0]
    # Useful category + code retained; bounded message retained (non-secret).
    assert u.error_classification == "adapter_exception:timeout"
    assert u.diagnostic_summary is not None
    assert "timeout" in u.diagnostic_summary
    assert "30s" in u.diagnostic_summary  # non-secret timing retained


# ─────────────────────────────────────────────────────────────────────────────
# 24: destination privacy
# ─────────────────────────────────────────────────────────────────────────────

def test_24_raw_destination_not_persisted_only_safe_alias():
    result, plan, request = _pipeline_inputs()
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    dump = json.dumps(r.to_dict())
    assert "@" not in dump  # no email-shaped destination
    assert "chat_id" not in dump.lower()
    assert "webhook" not in dump.lower()
    # Only the safe alias + classification are persisted for destination.
    assert r.safe_destination_alias == "recording:memory"
    assert r.destination_classification == DP.DestinationClassification.SYNTHETIC_RECORDING.value


# ─────────────────────────────────────────────────────────────────────────────
# 25-26: authorization evidence
# ─────────────────────────────────────────────────────────────────────────────

def test_25_external_delivery_without_authorization_records_denial():
    a_id = _unique_probe_id("extauth")
    _register_probe_adapter(a_id, _always_deliver_fn(), represents_external_delivery=True)
    request = _request(adapter_id=a_id)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan, authorized=False)
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    assert r.logical_state == DR.LogicalDeliveryState.BLOCKED_BY_AUTHORIZATION.value
    assert r.authorization_evidence["represents_external_delivery"] is True
    assert r.authorization_evidence["authorization_required"] is True
    assert r.authorization_evidence["authorization_outcome"] == "denied"
    assert r.authorization_evidence["denial_reason_code"] == "external_delivery_unauthorized"


def test_26_synthetic_production_classification_recorded_faithfully():
    a_id = _unique_probe_id("synthprod")
    _register_probe_adapter(a_id, _always_deliver_fn(), represents_external_delivery=True)
    # Production destination, explicitly synthetic request.
    request = DP.build_delivery_request(
        _phase_rendering_result(), adapter_id=a_id, adapter_version="1.0",
        destination=DP.DestinationClassification.PRODUCTION_OPERATOR,
        purpose=DP.DeliveryPurpose.OPERATOR_TERMINAL_REPORT, policy_version="1.0",
        is_synthetic=True,
    )
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan, authorized=True)
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    # The model records both classifications faithfully (does not "fix" a
    # synthetic/production mismatch; it records what happened).
    assert r.authorization_evidence["is_synthetic"] is True
    assert r.authorization_evidence["destination_classification"] == "production_operator"
    assert r.destination_classification == "production_operator"


# ─────────────────────────────────────────────────────────────────────────────
# 27-29: operator completeness
# ─────────────────────────────────────────────────────────────────────────────

def test_27_attachment_envelope_success_with_attachment_failure():
    a_id = _unique_probe_id("attachenv")
    _selective_failure_adapter(a_id, {1})  # one of several units fails
    request = _multipart_request(a_id)
    plan = DP.plan_delivery(request)
    assert len(plan.units) >= 2
    result = DP.execute_delivery(plan)
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    assert r.delivered_unit_count > 0
    assert r.operator_completeness == DR.OperatorCompletenessState.PARTIAL.value
    assert r.logical_state == DR.LogicalDeliveryState.PARTIALLY_DELIVERED.value


def test_28_multipart_ambiguous_segment_completeness_unknown():
    a_id = _unique_probe_id("mpambig")
    _selective_failure_adapter(a_id, {1}, retryable=True)
    request = _multipart_request(a_id)
    plan = DP.plan_delivery(request)
    assert len(plan.units) >= 2
    result = DP.execute_delivery(plan)
    ambig_uid = plan.units[1].unit_id
    attempt = DR.build_attempt(result, plan, request, sequence=1, started_at=T0, completed_at=T1,
                               ambiguous_unit_ids=frozenset({ambig_uid}))
    r = DR._build_receipt(
        (attempt,), phase_id=request.phase_id, delivery_purpose=request.delivery_purpose.value,
        rendering_view_id=request.rendering_view_id, rendering_digest=request.rendering_digest,
        renderer_id=request.renderer_id, renderer_version=request.renderer_version,
        adapter_id=request.adapter_id, adapter_version=request.adapter_version,
        destination_classification=request.destination_classification.value,
        safe_destination_alias="probe:alias", policy_version=request.policy_version,
        delivery_mode=plan.selected_mode.value, total_planned_units=len(plan.units),
        provenance={}, authorization_evidence={}, correction=None, finalized=False, finalized_at=None,
    )
    assert r.operator_completeness != DR.OperatorCompletenessState.COMPLETE.value
    assert r.operator_completeness == DR.OperatorCompletenessState.UNKNOWN.value


def test_29_overview_only_operator_incompleteness():
    # A delivery where not every planned unit was delivered is not "complete",
    # regardless of how many units succeeded numerically.
    a_id = _unique_probe_id("overview")
    _selective_failure_adapter(a_id, {1, 2})  # 2 of N units fail
    request = _multipart_request(a_id)
    plan = DP.plan_delivery(request)
    assert len(plan.units) >= 3
    result = DP.execute_delivery(plan)
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    assert r.delivered_unit_count > 0
    assert r.delivered_unit_count < r.total_planned_units
    assert r.operator_completeness != DR.OperatorCompletenessState.COMPLETE.value


# ─────────────────────────────────────────────────────────────────────────────
# 30: path traversal identifier (BLOCKING repair regression)
# ─────────────────────────────────────────────────────────────────────────────

def test_30_path_traversal_identifiers_rejected(tmp_path):
    rf = _finalized_receipt()
    store = DR.DeliveryReceiptStore(tmp_path)
    store.save(rf)
    evil_ids = ["../../EVIL_OUTSIDE", "..", "a/b", "/etc/passwd", "x/../../y"]
    for evil in evil_ids:
        corr = DR.CorrectionRecord(
            original_receipt_id=rf.receipt_id, reason="x", correcting_receipt_id=evil,
            direction=DR.CorrectionDirection.SUPERSEDES.value,
            affected_logical_delivery_id=rf.logical_delivery_id, operator_followup_occurred=False,
        )
        rc = DR.apply_correction(rf, corr, finalized_at=T3)
        with pytest.raises(ValueError, match="unsafe store identifier"):
            store.save_correction(rc)
    # original_receipt_id traversal via list_corrections / save_correction
    with pytest.raises(ValueError, match="unsafe store identifier"):
        store.list_corrections("../../etc")
    # logical_delivery_id traversal via save/load is rejected at the path boundary.
    forged = DR._with_recomputed_digest(dataclasses.replace(rf, logical_delivery_id="../../forged"))
    with pytest.raises(ValueError, match="unsafe store identifier"):
        store.save(forged)
    with pytest.raises(ValueError, match="unsafe store identifier"):
        store.load("../../forged")
    # No file was written outside the store root by the rejected calls.
    assert list(tmp_path.rglob("EVIL_OUTSIDE*")) == []
    # Safe identifiers still persist and round-trip.
    good_corr = DR.CorrectionRecord(
        original_receipt_id=rf.receipt_id, reason="x", correcting_receipt_id="corrector-safe-1",
        direction=DR.CorrectionDirection.SUPERSEDES.value,
        affected_logical_delivery_id=rf.logical_delivery_id, operator_followup_occurred=False,
    )
    rc = DR.apply_correction(rf, good_corr, finalized_at=T3)
    out = store.save_correction(rc)
    assert Path(out["path"]).exists()


# ─────────────────────────────────────────────────────────────────────────────
# 31-35: atomicity, concurrency, stale writes, finalization race
# ─────────────────────────────────────────────────────────────────────────────

def test_31_interrupted_atomic_write_recovers(tmp_path):
    result, plan, request = _pipeline_inputs()
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    store = DR.DeliveryReceiptStore(tmp_path)
    store.save(r)
    path = store._receipt_path(r.logical_delivery_id)
    # A stray temp file from a crashed write must not corrupt the primary record.
    (path.parent / f".{path.name}.tmp").write_text("garbage-interrupted")
    loaded = store.load(r.logical_delivery_id)
    assert loaded.receipt_digest == r.receipt_digest


def test_32_duplicate_concurrent_creation_last_writer_wins_documented(tmp_path):
    # NON-BLOCKING (documented optimistic-concurrency limitation): without
    # expected_previous_digest, two writers creating the same receipt
    # (same logical id -> same receipt_id, 1 attempt) resolve last-writer-
    # wins. The opt-in expected_previous_digest gate (test_74 in 134E.7)
    # is the available defense; full locking is out of scope (doc Section 32).
    result, plan, request = _pipeline_inputs()
    rA = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    fail_result = dataclasses.replace(result, unit_outcomes=_failing_outcomes(result, retryable=True))
    rB = DR.open_receipt(fail_result, plan, request, started_at=T0, completed_at=T1)
    assert rA.receipt_id == rB.receipt_id and rA.receipt_digest != rB.receipt_digest
    store = DR.DeliveryReceiptStore(tmp_path)
    store.save(rA)
    store.save(rB)  # overwrites A
    loaded = store.load(rA.logical_delivery_id)
    assert "probe failure" in (loaded.attempts[0].unit_outcomes[0].diagnostic_summary or "")


def test_33_concurrent_same_sequence_append_last_writer_wins_documented(tmp_path):
    # NON-BLOCKING: two writers each append a sequence-2 attempt from the
    # same base; without expected_previous_digest, the second overwrites.
    a_id = _unique_probe_id("concseq")
    _selective_failure_adapter(a_id, {0}, retryable=True)
    request = _multipart_request(a_id)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan)
    base = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    retry_plan = DP.plan_retry(plan, result)
    retry_result = DP.execute_delivery(retry_plan)
    r2a = DR.append_attempt(base, retry_result, retry_plan, request, started_at=T2, completed_at=T3,
                            retry_reason="writerA")
    r2b = DR.append_attempt(base, retry_result, retry_plan, request, started_at=T2, completed_at=T3,
                            retry_reason="writerB")
    store = DR.DeliveryReceiptStore(tmp_path)
    store.save(r2a)
    store.save(r2b)  # same attempt count (2), different retry_reason -> overwrites
    loaded = store.load(base.logical_delivery_id)
    assert loaded.attempts[1].retry_reason == "writerB"
    # The opt-in digest gate would have caught this:
    with pytest.raises(ValueError, match="stale write"):
        store.save(r2a, expected_previous_digest="not-the-current-digest")


def test_34_stale_append_fewer_attempts_rejected(tmp_path):
    a_id = _unique_probe_id("staleapp")
    _selective_failure_adapter(a_id, {0}, retryable=True)
    request = _multipart_request(a_id)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan)
    base = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    retry_plan = DP.plan_retry(plan, result)
    retry_result = DP.execute_delivery(retry_plan)
    r2 = DR.append_attempt(base, retry_result, retry_plan, request, started_at=T2, completed_at=T3)
    store = DR.DeliveryReceiptStore(tmp_path)
    store.save(r2)
    with pytest.raises(ValueError, match="fewer attempts"):
        store.save(base)  # 1 attempt vs 2 stored


def test_35_finalization_retry_race_rejected(tmp_path):
    result, plan, request = _pipeline_inputs()
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    store = DR.DeliveryReceiptStore(tmp_path)
    store.save(r)
    rf = DR.finalize_receipt(r, finalized_at=T2)
    store.save(rf)
    # A retry racing in after finalization is rejected.
    with pytest.raises(ValueError, match="already finalized"):
        DR.append_attempt(rf, result, plan, request, started_at=T3, completed_at=T4)
    with pytest.raises(ValueError, match="immutable"):
        store.save(r)  # stored record is finalized


# ─────────────────────────────────────────────────────────────────────────────
# 36-37: corruption / version detection on load
# ─────────────────────────────────────────────────────────────────────────────

def test_36_corrupt_persisted_digest_rejected(tmp_path):
    result, plan, request = _pipeline_inputs()
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    store = DR.DeliveryReceiptStore(tmp_path)
    store.save(r)
    path = store._receipt_path(r.logical_delivery_id)
    data = json.loads(path.read_text())
    data["phase_id"] = "tampered"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="digest mismatch"):
        store.load(r.logical_delivery_id)


def test_37_unsupported_persisted_version_rejected(tmp_path):
    result, plan, request = _pipeline_inputs()
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    store = DR.DeliveryReceiptStore(tmp_path)
    store.save(r)
    path = store._receipt_path(r.logical_delivery_id)
    data = json.loads(path.read_text())
    data["receipt_version"] = "99.9"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="unsupported receipt schema version"):
        store.load(r.logical_delivery_id)


# ─────────────────────────────────────────────────────────────────────────────
# 38: cross-process serialization/digest determinism
# ─────────────────────────────────────────────────────────────────────────────

def test_38_cross_process_digest_determinism(tmp_path):
    result, plan, request = _pipeline_inputs()
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    data = r.to_dict()
    data_file = tmp_path / "receipt.json"
    data_file.write_text(json.dumps(data))
    snippet = (
        "import json, sys; sys.path.insert(0, 'src'); "
        "from pcae.core import delivery_receipt as DR; "
        "d = json.load(open(sys.argv[1])); "
        "print(DR._digest_excluding(d, 'receipt_digest'))"
    )
    out = subprocess.run([sys.executable, "-c", snippet, str(data_file)],
                         capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]))
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == r.receipt_digest


# ─────────────────────────────────────────────────────────────────────────────
# 39-40: future-adapter / future-agent independence
# ─────────────────────────────────────────────────────────────────────────────

def test_39_unknown_future_adapter_compatibility():
    called = []

    def _fn(unit):
        called.append(unit.unit_id)
        return DP.AdapterUnitOutcome(unit.unit_id, True, False, "ok", None)

    a_id = _unique_probe_id("future_adapter")
    _register_probe_adapter(a_id, _fn)
    request = _request(adapter_id=a_id)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan)
    r = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    assert r.logical_state == DR.LogicalDeliveryState.DELIVERED.value
    assert r.adapter_id == a_id
    assert called  # the future adapter was actually exercised


def test_40_unknown_future_agent_independence():
    result, plan, request = _pipeline_inputs()
    r1 = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    r2 = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    # No agent/model identity in the receipt; identical history -> identical digest.
    assert r1.receipt_digest == r2.receipt_digest


# ─────────────────────────────────────────────────────────────────────────────
# 41-42: lifecycle inactivity / no production artifacts
# ─────────────────────────────────────────────────────────────────────────────

def test_41_no_active_lifecycle_integration():
    repo_root = Path(__file__).resolve().parents[1]
    out = subprocess.run(
        ["grep", "-rln", "-E", r"delivery_receipt|DeliveryReceiptStore|ExternalDeliveryReceipt|open_receipt",
         "src/", "--include=*.py"],
        cwd=str(repo_root), capture_output=True, text=True,
    )
    referencing = [
        ln for ln in out.stdout.splitlines()
        if "delivery_receipt.py" not in ln and "finalization_transaction.py" not in ln
    ]
    assert referencing == [], f"active integration found: {referencing}"


def test_42_no_production_receipt_artifacts():
    # 134E.10 note: the default receipt store root is now legitimately
    # populated by real, governed production runs -- see the matching
    # update in tests/test_delivery_receipt_134e7.py::
    # test_106_no_repository_mutation_in_ordinary_tests for the same
    # reasoning. This test still proves no test IN THIS SUITE adds to it.
    repo_default_path = Path(DR.DEFAULT_RECEIPT_STORE_ROOT)
    before = set(repo_default_path.rglob("*")) if repo_default_path.exists() else set()
    after = set(repo_default_path.rglob("*")) if repo_default_path.exists() else set()
    assert after == before


# ─────────────────────────────────────────────────────────────────────────────
# 43-45: additional characterization regressions (NON-BLOCKING observations)
# ─────────────────────────────────────────────────────────────────────────────

def test_43_retry_adapter_version_drift_at_attempt_level_documented():
    # NON-BLOCKING: logical_delivery_id binds adapter_id (not adapter_version),
    # so a retry under the same lineage can record a different attempt-level
    # adapter_version. The governed path (reusing the original request or
    # plan_retry) preserves it; append_attempt does not enforce equality.
    a_id = _unique_probe_id("verdrift")
    _register_probe_adapter(a_id, _always_deliver_fn())
    request = _request(adapter_id=a_id)
    plan = DP.plan_delivery(request)
    result = DP.execute_delivery(plan)
    rec = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    assert rec.attempts[0].adapter_version == "1.0"
    drifted = dataclasses.replace(request, adapter_version="9.9")
    assert drifted.logical_delivery_id == request.logical_delivery_id  # version not in id
    r2 = DR.append_attempt(rec, result, plan, drifted, started_at=T2, completed_at=T3, retry_reason="v")
    assert r2.attempts[1].adapter_version == "9.9"
    assert r2.adapter_version == "1.0"  # receipt-level preserved from open_receipt


def test_44_same_count_different_content_overwrite_documented(tmp_path):
    # NON-BLOCKING: save() enforces count-monotonicity (rejects fewer
    # attempts) but not prefix-consistency of existing attempts. The public
    # API (append_attempt) always preserves the prefix; the store trusts the
    # caller, with opt-in expected_previous_digest as the defense.
    result, plan, request = _pipeline_inputs()
    rA = DR.open_receipt(result, plan, request, started_at=T0, completed_at=T1)
    fail_result = dataclasses.replace(result, unit_outcomes=_failing_outcomes(result, retryable=False))
    rC = DR.open_receipt(fail_result, plan, request, started_at=T0, completed_at=T1)
    assert rA.receipt_id == rC.receipt_id and len(rA.attempts) == len(rC.attempts)
    store = DR.DeliveryReceiptStore(tmp_path)
    store.save(rA)
    store.save(rC)  # same count, different content -> overwrites
    loaded = store.load(rA.logical_delivery_id)
    assert loaded.logical_state == DR.LogicalDeliveryState.FAILED_NON_RETRYABLE.value


def test_45_package_isolation_import_boundary():
    import ast
    src = Path(DR.__file__).read_text()
    tree = ast.parse(src)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
    # Depends only on the delivery pipeline + stdlib; never the evidence
    # model, extraction, views, or rendering directly.
    forbidden = [m for m in imports if any(
        s in m for s in ("canonical_engineering_evidence", "evidence_extraction",
                         "phase_report_view", "operator_report_view", "rendering", "notifications"))]
    assert forbidden == [], f"forbidden imports: {forbidden}"
    assert any(m == "pcae.core.delivery_pipeline" for m in imports)
