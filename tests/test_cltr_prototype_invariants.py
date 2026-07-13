from __future__ import annotations

from pcae.cltr_prototype import digest as digest_mod
from pcae.cltr_prototype import invariants as inv
from pcae.cltr_prototype import state_machine as sm
from pcae.cltr_prototype.identity import resolve_identity
from pcae.cltr_prototype.models import EvidenceRef, EvidenceType, EvidenceVerificationStatus, InvariantResultOutcome


def _ident(transition_id="t-inv-1"):
    return resolve_identity(
        {"transition_id": transition_id, "phase_id": "135F", "repository_identity": "pcae-harness", "branch_identity": "main"}
    )


def _certified_record(transition_id="t-inv-1"):
    ident = _ident(transition_id)
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    return digest_mod.seal(r)


def test_evaluate_invariants_returns_37_results_always():
    r = _certified_record()
    results = inv.evaluate_invariants(r)
    assert len(results) == inv.INVARIANT_COUNT
    assert len(results) == 37


def test_no_applicable_invariant_silently_skipped_proposed_state():
    ident = _ident()
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    results = inv.evaluate_invariants(r)
    assert len(results) == 37
    for result in results:
        assert result.outcome in (
            InvariantResultOutcome.PASS,
            InvariantResultOutcome.FAIL,
            InvariantResultOutcome.INAPPLICABLE,
        )


def test_cltr_id_1_fails_on_mismatched_evidence_transition_id():
    r = _certified_record()
    bad_ref = EvidenceRef(
        evidence_id="bad-1",
        evidence_type=EvidenceType.REPORT,
        transition_id="some-other-transition",
        phase_id="135F",
        verification_status=EvidenceVerificationStatus.BOUND,
    )
    r2 = r.with_updates(report_binding=bad_ref)
    result = inv.evaluate_cltr_id_1(r2)
    assert result.outcome == InvariantResultOutcome.FAIL


def test_cltr_id_2_fails_on_mismatched_evidence_phase_id():
    r = _certified_record()
    bad_ref = EvidenceRef(
        evidence_id="bad-2",
        evidence_type=EvidenceType.REPORT,
        transition_id="t-inv-1",
        phase_id="134E",
        verification_status=EvidenceVerificationStatus.BOUND,
    )
    r2 = r.with_updates(report_binding=bad_ref)
    result = inv.evaluate_cltr_id_2(r2)
    assert result.outcome == InvariantResultOutcome.FAIL


def test_cltr_order_6_fails_on_early_marker():
    ident = _ident()
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record  # PROPOSED
    fake_marker = EvidenceRef(
        evidence_id="marker-early",
        evidence_type=EvidenceType.RUNTIME_SNAPSHOT,
        transition_id="t-inv-1",
        phase_id="135F",
        verification_status=EvidenceVerificationStatus.BOUND,
    )
    r2 = r.with_updates(marker_binding=fake_marker)
    result = inv.evaluate_cltr_order_6(r2)
    assert result.outcome == InvariantResultOutcome.FAIL
    assert result.quarantine_recommendation is True


def test_cltr_order_6_passes_when_marker_bound_at_notified():
    ident = _ident()
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    r = sm.t5_begin_promotion(r, at="t3").new_record
    r = sm.t6_promote_succeed(r, at="t4", promotion_binding=None).new_record
    r = sm.t8_begin_notification(r, at="t5").new_record
    marker = EvidenceRef(
        evidence_id="marker-ok",
        evidence_type=EvidenceType.RUNTIME_SNAPSHOT,
        transition_id="t-inv-1",
        phase_id="135F",
        verification_status=EvidenceVerificationStatus.BOUND,
    )
    r = sm.t9_notify_confirm(r, at="t6", notification_binding=None, marker_binding=marker).new_record
    result = inv.evaluate_cltr_order_6(r)
    assert result.outcome == InvariantResultOutcome.PASS


def test_cltr_persist_2_fails_on_digest_tamper():
    r = _certified_record()
    tampered = r.with_updates(source_revision="tampered")
    result = inv.evaluate_cltr_persist_2(tampered)
    assert result.outcome == InvariantResultOutcome.FAIL
    assert result.quarantine_recommendation is True


def test_cltr_persist_2_passes_on_valid_digest():
    r = _certified_record()
    result = inv.evaluate_cltr_persist_2(r)
    assert result.outcome == InvariantResultOutcome.PASS


def test_cltr_commit_2_fails_on_unclassified_declared_commit():
    from pcae.cltr_prototype.models import CommitDeclaration, CommitRole

    r = _certified_record().with_updates(declared_commits=(CommitDeclaration(commit_hash="abc", declared_role=CommitRole.SOURCE_CHANGE),))
    result = inv.evaluate_cltr_commit_2(r)
    assert result.outcome == InvariantResultOutcome.FAIL


def test_cltr_commit_3_fails_when_unresolvable_hash_classified_verified():
    from pcae.cltr_prototype.models import CommitClassificationResult, CommitOwnershipClassification

    r = _certified_record().with_updates(
        commit_classifications=(CommitClassificationResult(commit_hash="fake", classification=CommitOwnershipClassification.VERIFIED, reason=""),)
    )
    result = inv.evaluate_cltr_commit_3(r, comparison_bundle={"known_unresolvable_hashes": ["fake"]})
    assert result.outcome == InvariantResultOutcome.FAIL


def test_cltr_marker_1_fails_on_marker_receipt_identity_mismatch():
    r = _certified_record()
    marker = EvidenceRef(evidence_id="m1", evidence_type=EvidenceType.RUNTIME_SNAPSHOT, transition_id="t-inv-1", phase_id="135F", verification_status=EvidenceVerificationStatus.BOUND)
    receipt = EvidenceRef(evidence_id="r1", evidence_type=EvidenceType.RUNTIME_SNAPSHOT, transition_id="different-transition", phase_id="135F", verification_status=EvidenceVerificationStatus.BOUND)
    r2 = r.with_updates(marker_binding=marker, receipt_binding=receipt)
    result = inv.evaluate_cltr_marker_1(r2)
    assert result.outcome == InvariantResultOutcome.FAIL


def test_invariant_engine_never_returns_pass_for_unavailable_evidence():
    # An invariant that requires an external comparison bundle, when none is
    # supplied, must report inapplicable (disclosed), never a silent pass.
    r = _certified_record()
    result = inv.evaluate_cltr_state_1(r)  # not terminal yet -> inapplicable
    assert result.outcome == InvariantResultOutcome.INAPPLICABLE

    terminal_ident = _ident("t-inv-terminal")
    tr = sm.t1_propose_transition(terminal_ident, "rev1", at="t0").new_record
    tr = sm.t2_begin_certification(tr, at="t1").new_record
    tr = sm.t3_certify(tr, at="t2", certified_state={"x": 1}).new_record
    tr = sm.t5_begin_promotion(tr, at="t3").new_record
    tr = sm.t6_promote_succeed(tr, at="t4", promotion_binding=None).new_record
    tr = sm.t8_begin_notification(tr, at="t5").new_record
    tr = sm.t9_notify_confirm(tr, at="t6", notification_binding=None).new_record
    tr = sm.t13_close_success(tr, at="t7").new_record
    result2 = inv.evaluate_cltr_state_1(tr)  # terminal but no bundle supplied
    assert result2.outcome == InvariantResultOutcome.INAPPLICABLE  # never auto-pass


def test_all_invariant_ids_are_unique():
    r = _certified_record()
    results = inv.evaluate_invariants(r)
    ids = [res.invariant_id for res in results]
    assert len(ids) == len(set(ids))


def test_all_invariants_are_blocking_severity_by_default():
    r = _certified_record()
    results = inv.evaluate_invariants(r)
    assert all(res.severity == "Blocking" for res in results)
