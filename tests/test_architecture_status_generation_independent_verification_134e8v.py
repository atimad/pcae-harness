"""Fresh adversarial verification for Phase 134E.8V.

These probes were derived from source inspection and direct REPL experiments,
not copied from the 134E.8/134E.8.1 assertions. No external sink is used.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core.architecture_status import (
    FRESHNESS_FRESH,
    FRESHNESS_FRESH_WITH_LIMITATIONS,
    FRESHNESS_INVALID,
    is_valid_phase_id,
    parse_phase_id,
    phase_sort_key,
    validate_architecture_status,
)
from pcae.core.phase_reports import (
    COMPLETENESS_COMPLETE,
    _apply_internal_report_coherence,
    build_architecture_status,
    compute_finalization_snapshot_id,
    compute_report_digest,
    make_phase_report,
    notification_dispatch_state,
    read_notification_dispatch_marker,
    validate_internal_report_coherence,
    write_notification_dispatch_marker,
    write_phase_report,
)


@pytest.fixture(autouse=True)
def _no_external_delivery(monkeypatch):
    monkeypatch.setenv("PCAE_NOTIFY_CONFIG_DISABLE", "1")
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    monkeypatch.delenv("PCAE_TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("PCAE_TELEGRAM_CHAT_ID", raising=False)


def _status_text(current="134E.8V", recommendation="134E.9", extra=""):
    return f"""# Project Status

## Current Phase

Phase {current} — Verification Phase.

Recommended next phase: {recommendation} — Next governed phase.

## Phase 132F Complete

Phase 132F — Repository Intelligence Service Independent Verification.

## Phase 133C Complete

Phase 133C — PFR-001 Contract Verification Lifecycle Recovery.

## Phase 134B Complete

Phase 134B — Canonical Finalization Contract Freeze.

## Phase 134B.1 Complete

Phase 134B.1 — Corrective phase excluded from milestone chapters.

## Phase 134E.8 Complete

Phase 134E.8 — Architecture Status Generation Repair.

{extra}
"""


def _git_init(path: Path):
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "verify@example.test"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Verifier"], cwd=path, check=True)
    subprocess.run(["git", "add", "PROJECT_STATUS.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=path, check=True)


def _build(tmp_path: Path, monkeypatch, text: str):
    (tmp_path / "PROJECT_STATUS.md").write_text(text)
    _git_init(tmp_path)
    monkeypatch.chdir(tmp_path)
    return build_architecture_status()


def _report(**changes):
    data = dict(
        phase_id="134E.8V",
        phase_name="Architecture Status Generation Independent Verification",
        status="completed",
        summary="Independently verified Architecture Status generation.",
        files_changed=4,
        tests_run=40,
        test_results={"architecture_status_generation_independent_verification_134e8v": "40 passed"},
        governance_results={"pcae_check": "passed"},
        commits=["abc12345"],
        pushed_status="pushed",
        explicit_no_go_confirmations=["No 134E.9 work began."],
        recommended_next_phase="134E.9 - Derived Correctness",
        created_at="one",
    )
    data.update(changes)
    report = make_phase_report(**data)
    report.report_completeness = COMPLETENESS_COMPLETE
    return report


@pytest.mark.parametrize("phase_id", [
    "132F", "133C", "134B.1", "134B.2", "134B.3", "134E", "134E.1",
    "134E.1V", "134E.7V", "134E.8", "134E.8.1", "134E.8V", "134E.10", "134E.10V",
])
def test_exact_phase_grammar_accepts_governed_identities(phase_id):
    assert is_valid_phase_id(phase_id)
    assert parse_phase_id(phase_id) is not None


@pytest.mark.parametrize("phase_id", ["134", "134E8", "134E.", "x134E.8"])
def test_phase_grammar_rejects_malformed_or_truncated_identity(phase_id):
    assert parse_phase_id(phase_id) is None


def test_multi_letter_verification_suffix_now_accepted_per_cpipc_001():
    # Phase 137R / CPIPC-001 §4: the canonical grammar's numeric-segment
    # allows a trailing run of one-or-more letters, not a single letter
    # -- a deliberate widening (this repository's own historical
    # branch-letter rollover already established that letter runs are
    # not capped at one character). "134E.8VV" is therefore valid under
    # the frozen contract, not rejected as it was under this file's
    # pre-137R, single-letter-only local regex.
    assert is_valid_phase_id("134E.8VV")
    assert parse_phase_id("134E.8VV") is not None


def test_ordering_preserves_parent_corrective_verification_and_multidigit():
    values = ["134E.10V", "134B.3", "134E.8V", "134B", "134E.8.1", "134E", "134E.10", "134B.1"]
    ordered = sorted(values, key=phase_sort_key)
    assert ordered.index("134B") < ordered.index("134B.1") < ordered.index("134B.3")
    assert ordered.index("134E.8.1") < ordered.index("134E.8V") < ordered.index("134E.10")


def test_current_recommendation_wins_over_multiple_retired_recommendations(tmp_path, monkeypatch):
    extra = "Recommended next repo phase: 132F — stale.\n\nRecommended next repo phase: 133G — stale."
    status = _build(tmp_path, monkeypatch, _status_text(extra=extra))
    assert status["planned_phase_ids"] == ["134E.9"]
    assert "132F" not in status["planned_phase_ids"]


def test_completed_132f_is_never_planned(tmp_path, monkeypatch):
    status = _build(tmp_path, monkeypatch, _status_text())
    assert "132F" in status["completed_phase_ids"]
    assert "132F" not in status["planned_phase_ids"]


def test_recovered_133c_is_exactly_once_and_ordered(tmp_path, monkeypatch):
    text = _status_text(extra="## Phase 133C Complete\n\nPhase 133C — PFR-001 Contract Verification Lifecycle Recovery.\n")
    status = _build(tmp_path, monkeypatch, text)
    assert status["completed_phase_ids"].count("133C") == 1


def test_corrective_subphases_remain_distinct_from_parent(tmp_path, monkeypatch):
    status = _build(tmp_path, monkeypatch, _status_text())
    assert "134B" in status["completed_phase_ids"]
    assert "134B.1" in status["completed_phase_ids"]
    assert status["completed_phase_ids"].count("134B.1") == 1


def test_completed_planned_overlap_is_invalid_and_disclosed(tmp_path, monkeypatch):
    status = _build(tmp_path, monkeypatch, _status_text(recommendation="132F"))
    assert status["freshness"] == FRESHNESS_INVALID
    assert status["planned_phase_ids"] == []
    assert status["conflicts"]


def test_duplicate_title_conflict_is_invalid(tmp_path, monkeypatch):
    extra = "## Phase 133C Complete\n\nPhase 133C — Different Title.\n"
    status = _build(tmp_path, monkeypatch, _status_text(extra=extra))
    assert status["freshness"] == FRESHNESS_INVALID
    assert any("conflicting titles" in item for item in status["conflicts"])


def test_missing_runtime_is_disclosed_without_hardcoded_fallback(tmp_path, monkeypatch):
    import pcae.core.runtime_snapshot as runtime_snapshot

    monkeypatch.setattr(runtime_snapshot, "build_runtime_snapshot", lambda *_: (_ for _ in ()).throw(RuntimeError("probe")))
    status = _build(tmp_path, monkeypatch, _status_text())
    assert status["current_runtime_state"] == ""
    assert status["current_maximum_capability"] == ""
    assert status["execution_availability"] == ""
    assert status["freshness"] == FRESHNESS_FRESH_WITH_LIMITATIONS


def test_repository_revision_is_bound_to_git_head(tmp_path, monkeypatch):
    status = _build(tmp_path, monkeypatch, _status_text())
    expected = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    assert status["repository_revision"] == expected
    assert status["source_provenance"]["repository_revision"] == "read"


def test_state_marker_changes_when_project_state_changes(tmp_path, monkeypatch):
    first = _build(tmp_path, monkeypatch, _status_text())
    (tmp_path / "PROJECT_STATUS.md").write_text(_status_text(recommendation="134E.10"))
    second = build_architecture_status()
    assert first["state_marker"] != second["state_marker"]


def test_architecture_cli_is_side_effect_free(tmp_path, monkeypatch):
    (tmp_path / "PROJECT_STATUS.md").write_text(_status_text())
    _git_init(tmp_path)
    monkeypatch.chdir(tmp_path)
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if p.is_file())
    from pcae.commands.architecture_status import run_architecture_status_inspect

    class Args:
        json = True

    assert run_architecture_status_inspect(Args()) == 0
    after = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if p.is_file())
    assert before == after


def test_snapshot_binds_every_material_report_family():
    base = _report()
    base.architecture_status = {"repository_revision": "rev1", "planned_phase_ids": ["134E.9"]}
    base.metadata.update({"phase_id": "134E.8V", "source_revision": "rev1"})
    baseline = compute_finalization_snapshot_id(base)
    variants = [
        _report(summary="changed"), _report(files_changed=5), _report(tests_run=41),
        _report(test_results={"generic": "passed"}), _report(governance_results={"pcae_check": "failed"}),
        _report(commits=["different"]), _report(explicit_no_go_confirmations=["No execution capability."]),
        _report(recommended_next_phase="134E.10"),
    ]
    for variant in variants:
        assert compute_finalization_snapshot_id(variant) != baseline


def test_snapshot_excludes_only_intentional_volatile_fields():
    one = _report(created_at="one")
    two = _report(created_at="two")
    two.notification_result = {"attempt": 2}
    assert compute_finalization_snapshot_id(one) == compute_finalization_snapshot_id(two)


def test_report_digest_is_exact_rendered_byte_digest():
    report = _report()
    assert compute_report_digest(report) == hashlib.sha256(report.render_markdown().encode()).hexdigest()


def test_report_digest_is_independent_of_structured_mapping_insertion_order():
    one = _report(
        governance_results={"z_check": "passed", "a_check": "passed"},
        test_results={"z_suite": "passed", "a_suite": "passed"},
    )
    two = _report(
        governance_results={"a_check": "passed", "z_check": "passed"},
        test_results={"a_suite": "passed", "z_suite": "passed"},
    )
    assert compute_report_digest(one) == compute_report_digest(two)


def test_bound_ordinary_payload_repeats_as_duplicate(tmp_path):
    report = _report()
    marker = tmp_path / "marker.json"
    write_notification_dispatch_marker(
        report.phase_id, "abc", marker,
        report_digest=compute_report_digest(report),
        finalization_snapshot_id=compute_finalization_snapshot_id(report),
    )
    assert notification_dispatch_state(
        report.phase_id, marker_path=marker,
        report_digest=compute_report_digest(report),
        finalization_snapshot_id=compute_finalization_snapshot_id(report),
    ) == "already_dispatched"


def test_changed_payload_under_same_ordinary_identity_conflicts(tmp_path):
    original = _report()
    changed = _report(summary="different payload")
    marker = tmp_path / "marker.json"
    write_notification_dispatch_marker(
        original.phase_id, marker_path=marker,
        report_digest=compute_report_digest(original),
        finalization_snapshot_id=compute_finalization_snapshot_id(original),
    )
    assert notification_dispatch_state(
        changed.phase_id, marker_path=marker,
        report_digest=compute_report_digest(changed),
        finalization_snapshot_id=compute_finalization_snapshot_id(changed),
    ) == "payload_conflict"


@pytest.mark.parametrize("purpose", ["correction", "supersession"])
def test_explicit_nonordinary_purpose_is_distinct(tmp_path, purpose):
    report = _report()
    marker = tmp_path / "marker.json"
    write_notification_dispatch_marker(report.phase_id, marker_path=marker)
    assert notification_dispatch_state(
        report.phase_id, marker_path=marker, delivery_purpose=purpose,
        report_digest=compute_report_digest(report),
        finalization_snapshot_id=compute_finalization_snapshot_id(report),
    ) == "not_dispatched"


def test_correction_record_does_not_erase_ordinary_identity(tmp_path):
    report = _report()
    marker = tmp_path / "marker.json"
    digest = compute_report_digest(report)
    snapshot = compute_finalization_snapshot_id(report)
    write_notification_dispatch_marker(
        report.phase_id, marker_path=marker,
        report_digest=digest, finalization_snapshot_id=snapshot,
    )
    write_notification_dispatch_marker(
        report.phase_id, "correction1", marker,
        report_digest="correction-digest",
        finalization_snapshot_id="correction-snapshot",
        delivery_purpose="correction",
    )
    assert notification_dispatch_state(
        report.phase_id, marker_path=marker,
        report_digest=digest, finalization_snapshot_id=snapshot,
    ) == "already_dispatched"
    assert notification_dispatch_state(
        report.phase_id, marker_path=marker,
        report_digest="correction-digest",
        finalization_snapshot_id="correction-snapshot",
        delivery_purpose="correction",
    ) == "already_dispatched"


def test_summary_no_go_work_contradiction_is_rejected():
    report = _report(
        summary="Implemented Architecture Status repair.",
        explicit_no_go_confirmations=["No Architecture Status repair occurred."],
    )
    assert any("summary claims" in item for item in validate_internal_report_coherence(report))


def test_generic_test_names_do_not_false_positive():
    assert validate_internal_report_coherence(_report(test_results={"fast_green": "4390 passed"})) == []


def test_verification_tests_may_reference_implementation_when_verification_identity_present():
    report = _report(test_results={"134e8_implementation": "51 passed", "134e8v_verification": "40 passed"})
    assert not any("other phase identities" in item for item in validate_internal_report_coherence(report))


def test_coherence_failure_cannot_remain_complete():
    report = _report(explicit_no_go_confirmations=["No 134E.8V work began."])
    _apply_internal_report_coherence(report)
    assert report.report_completeness != COMPLETENESS_COMPLETE
    assert "internal_evidence_coherence" in report.missing_trust_fields


def test_source_revision_mismatch_is_rejected():
    report = _report()
    report.metadata.update({"phase_id": report.phase_id, "source_revision": "rev-a"})
    report.architecture_status = {"repository_revision": "rev-b"}
    assert any("source revision" in item for item in validate_internal_report_coherence(report))


def test_stored_markdown_equals_certified_rendered_bytes(tmp_path):
    report = _report()
    paths = write_phase_report(report, tmp_path / "reports")
    assert Path(paths["markdown"]).read_bytes() == report.render_markdown().encode()


def test_marker_digest_equals_stored_payload_digest(tmp_path):
    report = _report()
    paths = write_phase_report(report, tmp_path / "reports")
    marker = tmp_path / "marker.json"
    write_notification_dispatch_marker(
        report.phase_id, marker_path=marker,
        report_digest=compute_report_digest(report),
        finalization_snapshot_id=compute_finalization_snapshot_id(report),
    )
    assert read_notification_dispatch_marker(marker)["report_digest"] == hashlib.sha256(
        Path(paths["markdown"]).read_bytes()
    ).hexdigest()


def test_cross_process_phase_order_is_deterministic():
    code = "from pcae.core.architecture_status import phase_sort_key; import json; print(json.dumps(sorted(['134E.10V','134E.8.1','134E.8V','134B.1'], key=phase_sort_key)))"
    env = dict(os.environ, PYTHONPATH=str(Path.cwd() / "src"))
    one = subprocess.check_output([sys.executable, "-c", code], text=True, env=env)
    two = subprocess.check_output([sys.executable, "-c", code], text=True, env=env)
    assert one == two


def test_no_repository_intelligence_authority_imports():
    source = Path("src/pcae/core/phase_reports.py").read_text()
    build_source = source[source.index("def build_architecture_status"):source.index("def _extract_commit_count_from_summary")]
    assert "repository_intelligence" not in build_source


def test_inactive_track_134_pipeline_has_no_lifecycle_imports():
    for name in ("canonical_engineering_evidence.py", "evidence_extraction.py", "phase_report_view.py", "operator_report_view.py", "rendering.py", "delivery_pipeline.py", "delivery_receipt.py"):
        text = (Path("src/pcae/core") / name).read_text()
        assert "pcae.commands.phase" not in text
        assert "pcae.commands.task" not in text


def test_historical_incident_reports_are_preserved():
    trusted = Path(".pcae/phase-reports/20260711-143817-134E.8.md")
    invalid = Path(".pcae/phase-reports/20260711-144017-134E.8.md")
    assert trusted.exists() and invalid.exists()
    assert hashlib.sha256(trusted.read_bytes()).hexdigest() == "e247d3a30ef0f106b218b00dbf6486f30e5c5636bb410c91f410018ef7419f10"
    assert hashlib.sha256(invalid.read_bytes()).hexdigest() == "a282ece862bca3b9565b45baebc8d0b3600e439d5fa20fd383370ce79fe27775"


def test_real_repository_status_has_no_stale_132f_plan_and_discloses_no_conflicts():
    """Phase 134E.9.1 — ``current_phase_id``/``planned_phase_ids`` are
    intentionally *not* pinned to the literal values true when 134E.8V
    was authored: those fields necessarily change every time a later
    phase completes (134E.9, then this corrective 134E.9.1), which is
    correct evolution, not a regression. Pinning a literal here would
    make this test fail at the next phase transition regardless of any
    actual code defect -- the same live-repository-state coupling this
    corrective phase found and repaired in ``test_dry_run_simulation.py``.
    The genuinely durable invariants (132F completed and never planned,
    Tracks 132-134 represented, 134E.8/134E.8.1 completed, no conflicts,
    fresh) remain pinned exactly as 134E.8V asserted them."""
    status = build_architecture_status()
    assert "132F" in status["completed_phase_ids"]
    assert "132F" not in status["planned_phase_ids"]
    assert {"132", "133", "134"}.issubset({item["chapter"] for item in status["completed_chapters"]})
    assert "134E.8" in status["completed_phase_ids"]
    assert "134E.8.1" in status["completed_phase_ids"]
    assert status["current_phase_id"]
    assert "134E.8V" in status["completed_phase_ids"]
    assert status["conflicts"] == []
    assert status["freshness"] == FRESHNESS_FRESH
    assert validate_architecture_status(status) == []
