"""Phase 114A: canonical artifact promotion pipeline tests."""
from __future__ import annotations

import json
from pathlib import Path

from pcae.core.canonical_artifact_promotion import (
    ArtifactState,
    can_transition,
    promote_artifact,
    quarantine_artifact,
)
from pcae.core.phase_reports import (
    make_phase_report,
    write_phase_report,
    write_quarantined_report,
)


def _phase_report():
    report = make_phase_report(
        phase_id="114A",
        phase_name="Promotion Fixture",
        status="completed",
        summary="Promotion fixture.",
        files_changed=1,
        tests_run=1,
        test_results={
            "report_notification_tests": "1/1 (passed)",
            "bootstrap_session_reporting_tests": "present (passed)",
            "fast_green": "1/1 (passed)",
        },
        governance_results={
            "pcae_health": "healthy",
            "pcae_check": "passed",
            "pcae_doctor_task_memory": "clean",
            "pcae_push_check": "clean",
            "telegram_runtime": "loaded, configured, enabled",
        },
        commits=["abc12345"],
        pushed_status="pushed",
        origin_main_head_count=0,
        explicit_no_go_confirmations=[
            "No execution. No authorization. No push integration. No notification enforcement. "
            "No Permission Broker enforcement. No plugins. No REST. No Web UI. No Dashboard. "
            "No Telegram inbound. No force push. No package publication."
        ],
        recommended_next_phase="114B - Notification Enforcement & Idempotency",
    )
    report.apply_trust_assessment()
    return report


def test_successful_promotion_writes_versioned_and_latest_artifacts(tmp_path):
    result = promote_artifact(
        artifact_type="phase_report",
        artifact_id="114A",
        source_state=ArtifactState.CERTIFIED,
        versioned_artifacts={tmp_path / "20260705-114A.md": "# Report\n"},
        canonical_artifacts={tmp_path / "latest.md": "# Report\n"},
    )

    assert result.promoted is True
    assert result.target_state == ArtifactState.CANONICAL
    assert (tmp_path / "20260705-114A.md").read_text() == "# Report\n"
    assert (tmp_path / "latest.md").read_text() == "# Report\n"
    assert [d.status for d in result.diagnostics] == ["validated", "certified", "promoted"]


def test_promotion_only_from_certified(tmp_path):
    for state in (ArtifactState.DRAFT, ArtifactState.VALIDATED, ArtifactState.REJECTED, ArtifactState.QUARANTINED):
        result = promote_artifact(
            artifact_type="phase_report",
            artifact_id=state.value,
            source_state=state,
            versioned_artifacts={tmp_path / f"{state.value}.md": "versioned"},
            canonical_artifacts={tmp_path / "latest.md": "latest"},
        )
        assert result.promoted is False
        assert not (tmp_path / f"{state.value}.md").exists()
        assert not (tmp_path / "latest.md").exists()


def test_rejected_cannot_promote_and_latest_unchanged(tmp_path):
    latest = tmp_path / "latest.json"
    latest.write_text('{"phase_id": "old"}')

    result = promote_artifact(
        artifact_type="phase_report",
        artifact_id="rejected",
        source_state=ArtifactState.REJECTED,
        versioned_artifacts={tmp_path / "rejected.json": "{}"},
        canonical_artifacts={latest: '{"phase_id": "new"}'},
    )

    assert result.promoted is False
    assert "not certified" in result.diagnostics[-1].message
    assert latest.read_text() == '{"phase_id": "old"}'
    assert not (tmp_path / "rejected.json").exists()


def test_quarantined_cannot_promote_and_latest_unchanged(tmp_path):
    latest = tmp_path / "latest.md"
    latest.write_text("# Old\n")

    result = promote_artifact(
        artifact_type="phase_report",
        artifact_id="quarantined",
        source_state=ArtifactState.QUARANTINED,
        versioned_artifacts={tmp_path / "blocked.md": "# Blocked\n"},
        canonical_artifacts={latest: "# New\n"},
    )

    assert result.promoted is False
    assert latest.read_text() == "# Old\n"
    assert not (tmp_path / "blocked.md").exists()


def test_quarantined_artifacts_retained_for_forensics(tmp_path):
    result = quarantine_artifact(
        artifact_type="phase_report",
        artifact_id="114A",
        quarantine_artifacts={tmp_path / "quarantine" / "blocked.json": '{"blocked": true}'},
        blockers=("report_completeness",),
    )

    assert result.promoted is False
    assert result.target_state == ArtifactState.QUARANTINED
    assert (tmp_path / "quarantine" / "blocked.json").exists()
    assert [d.status for d in result.diagnostics] == ["quarantined", "rejected"]


def test_phase_report_writer_promotes_only_certified_report(tmp_path):
    report = _phase_report()

    paths = write_phase_report(report, tmp_path)

    assert paths["promotion_status"] == "promoted"
    assert Path(paths["latest_markdown"]).exists()
    assert Path(paths["latest_json"]).exists()
    latest = json.loads(Path(paths["latest_json"]).read_text())
    assert latest["phase_id"] == "114A"
    assert latest["report_completeness"] == "complete"


def test_phase_report_quarantine_never_overwrites_latest(tmp_path):
    old_json = '{"phase_id": "old"}'
    old_md = "# Old\n"
    (tmp_path / "latest.json").write_text(old_json)
    (tmp_path / "latest.md").write_text(old_md)

    paths = write_quarantined_report(_phase_report(), tmp_path, ["blocked"])

    assert paths["promotion_status"] == "quarantined"
    assert Path(paths["quarantine_json"]).exists()
    assert Path(paths["quarantine_markdown"]).exists()
    assert (tmp_path / "latest.json").read_text() == old_json
    assert (tmp_path / "latest.md").read_text() == old_md


def test_state_machine_freezes_expected_transitions():
    assert can_transition(ArtifactState.DRAFT, ArtifactState.VALIDATED)
    assert can_transition(ArtifactState.VALIDATED, ArtifactState.CERTIFIED)
    assert can_transition(ArtifactState.CERTIFIED, ArtifactState.CANONICAL)
    assert not can_transition(ArtifactState.REJECTED, ArtifactState.CANONICAL)
    assert not can_transition(ArtifactState.QUARANTINED, ArtifactState.CANONICAL)


def test_future_artifact_extensibility(tmp_path):
    result = promote_artifact(
        artifact_type="future_artifact",
        artifact_id="future-1",
        source_state=ArtifactState.CERTIFIED,
        versioned_artifacts={tmp_path / "future" / "artifact.json": "{}"},
        canonical_artifacts={tmp_path / "future" / "latest.json": "{}"},
    )

    assert result.artifact_type == "future_artifact"
    assert result.promoted is True
    assert (tmp_path / "future" / "latest.json").exists()


def test_execution_unavailable_not_changed_by_promotion_module():
    source = Path("src/pcae/core/canonical_artifact_promotion.py").read_text()
    assert "subprocess" not in source
    assert "execute" not in source.lower()
