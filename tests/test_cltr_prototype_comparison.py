from __future__ import annotations

import json
from pathlib import Path

from pcae.cltr_prototype import comparison, digest as digest_mod, state_machine as sm
from pcae.cltr_prototype.identity import resolve_identity

FIXTURES = Path(__file__).parent / "fixtures" / "cltr_prototype"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def _certified_record(transition_id="t-cmp-1"):
    ident = resolve_identity({"transition_id": transition_id, "phase_id": "135F", "repository_identity": "pcae-harness", "branch_identity": "main"})
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    return digest_mod.seal(r)


def test_exact_match_no_mixed_generation():
    r = _certified_record()
    report = comparison.compare(r, {"canonical_report": {"transition_id": "t-cmp-1", "phase_id": "135F"}})
    assert report.mixed_generation_detected is False
    assert report.target_results[0].classification == "conformant"


def test_mixed_derivative_generation_detected():
    fixture = _load("mixed_derivative_generations.json")
    r = _certified_record(fixture["record_transition_id"])
    report = comparison.compare(r, fixture["targets"])
    assert report.mixed_generation_detected is True
    assert "txn-fixture-mixed-gen-OLD" in (report.mixed_generation_detail or "")


def test_conflicting_target_transition_id_flagged():
    r = _certified_record()
    report = comparison.compare(r, {"notification_result": {"transition_id": "some-other-transition"}})
    assert report.target_results[0].classification == "conflicting"
    assert report.target_results[0].quarantine_recommended is True


def test_inline_phase_mismatch_is_conflicting():
    r = _certified_record()
    report = comparison.compare(
        r,
        {"architecture_status": {"transition_id": r.identity.transition_id, "phase_id": "999Z"}},
    )
    assert report.target_results[0].classification == "conflicting"
    assert report.target_results[0].quarantine_recommended is True


def test_inline_digest_mismatch_is_conflicting():
    r = _certified_record()
    report = comparison.compare(r, {"mutable_latest_pointer": {"record_digest": "0" * 64}})
    assert report.target_results[0].classification == "conflicting"


def test_unknown_inline_semantics_fail_closed_as_unverifiable():
    r = _certified_record()
    report = comparison.compare(
        r,
        {"notification_result": {"transition_id": r.identity.transition_id, "notification_outcome": "confirmed"}},
    )
    assert report.target_results[0].classification == "unverifiable"
    assert "not implemented" in (report.target_results[0].limitation or "")


def test_legacy_missing_field_target():
    fixture = _load("legacy_artifact_no_transition_id.json")
    # The legacy metadata's own phase_id (134E.10) must match the record's
    # declared phase_id for this to be a pure "missing field" case rather
    # than a genuine identity conflict (covered separately by
    # test_stale_report_target_flagged_as_conflict).
    ident = resolve_identity({"transition_id": "t-legacy-match", "phase_id": "134E.10", "repository_identity": "pcae-harness", "branch_identity": "main"})
    r_raw = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r_raw = sm.t2_begin_certification(r_raw, at="t1").new_record
    r_raw = sm.t3_certify(r_raw, at="t2", certified_state={"x": 1}).new_record
    r = digest_mod.seal(r_raw)
    full_path = FIXTURES.parent.parent.parent / fixture["artifact_path"]
    report = comparison.compare(r, {"completion_metadata": full_path})
    assert report.target_results[0].classification == "conformant_with_legacy_adapter"
    assert "transition_id" in report.target_results[0].missing_fields


def test_stale_report_target_flagged_as_conflict():
    fixture = _load("stale_report.json")
    r = _certified_record(fixture["declared_identity"]["transition_id"])
    full_path = FIXTURES.parent.parent.parent / fixture["narrative_artifact_path"]
    report = comparison.compare(r, {"canonical_report": full_path})
    assert report.target_results[0].classification == "conflicting"


def test_unrecognized_target_type_marked_unverifiable():
    r = _certified_record()
    report = comparison.compare(r, {"architecture_status": 12345})
    assert report.target_results[0].classification == "unverifiable"


def test_comparison_never_writes_to_targets(tmp_path):
    target_path = tmp_path / "metadata.json"
    original_content = json.dumps({"phase_id": "134E"})
    target_path.write_text(original_content)
    r = _certified_record()
    comparison.compare(r, {"completion_metadata": target_path})
    assert target_path.read_text() == original_content
