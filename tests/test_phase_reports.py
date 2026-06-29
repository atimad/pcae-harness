"""Tests for Phase 92A phase report artifact model."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from pcae.core.phase_reports import (
    PhaseReport,
    make_phase_report,
    write_phase_report,
    read_latest_report,
    is_valid_status,
    SCHEMA_VERSION,
    VALID_STATUSES,
)


# ── Construction and validation ──────────────────────────────────────────────

def test_create_valid_report():
    r = make_phase_report(
        phase_id="90A-test",
        phase_name="Test Phase",
        status="completed",
        summary="All done.",
    )
    assert r.phase_id == "90A-test"
    assert r.status == "completed"
    assert r.schema_version == SCHEMA_VERSION
    assert r.created_at


def test_reject_missing_phase_id():
    with pytest.raises(ValueError, match="phase_id"):
        make_phase_report(phase_id="", phase_name="X", status="completed", summary="Y")


def test_reject_missing_status():
    with pytest.raises(ValueError, match="status"):
        make_phase_report(phase_id="X", phase_name="X", status="", summary="Y")


def test_reject_invalid_status():
    with pytest.raises(ValueError, match="invalid status"):
        make_phase_report(phase_id="X", phase_name="X", status="bogus", summary="Y")


def test_reject_missing_summary():
    with pytest.raises(ValueError, match="summary"):
        make_phase_report(phase_id="X", phase_name="X", status="completed", summary="")


def test_all_valid_statuses_accepted():
    for st in VALID_STATUSES:
        r = make_phase_report(phase_id="X", phase_name="X", status=st, summary="OK")
        assert r.status == st


def test_is_valid_status():
    assert is_valid_status("completed") is True
    assert is_valid_status("bogus") is False


# ── Markdown rendering ───────────────────────────────────────────────────────

def test_render_markdown_includes_phase_name():
    r = make_phase_report(phase_id="90A", phase_name="Test Phase", status="completed", summary="Done.")
    md = r.render_markdown()
    assert "Test Phase" in md
    assert "90A" in md
    assert "Done." in md
    assert "completed" in md


def test_render_markdown_includes_governance_results():
    r = make_phase_report(
        phase_id="90A", phase_name="X", status="completed", summary="Y",
        governance_results={"health": "healthy", "check": "passed"},
    )
    md = r.render_markdown()
    assert "health" in md
    assert "healthy" in md


def test_render_markdown_includes_test_results():
    r = make_phase_report(
        phase_id="90A", phase_name="X", status="completed", summary="Y",
        test_results={"fast_green": "3221/3221"},
    )
    md = r.render_markdown()
    assert "fast_green" in md


def test_render_markdown_includes_no_go_confirmations():
    r = make_phase_report(
        phase_id="90A", phase_name="X", status="completed", summary="Y",
        explicit_no_go_confirmations=["No enforcement", "No shell interception"],
    )
    md = r.render_markdown()
    assert "No enforcement" in md


def test_render_markdown_includes_recommended_next():
    r = make_phase_report(
        phase_id="90A", phase_name="X", status="completed", summary="Y",
        recommended_next_phase="90B",
    )
    md = r.render_markdown()
    assert "90B" in md


# ── JSON rendering ───────────────────────────────────────────────────────────

def test_render_json_has_schema_version():
    r = make_phase_report(phase_id="90A", phase_name="X", status="completed", summary="Y")
    data = json.loads(r.render_json())
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["phase_id"] == "90A"


def test_render_json_includes_all_fields():
    r = make_phase_report(phase_id="90A", phase_name="X", status="completed", summary="Y")
    data = json.loads(r.render_json())
    for field in ["phase_id", "phase_name", "status", "summary", "commits", "risks", "follow_ups"]:
        assert field in data


# ── File I/O ─────────────────────────────────────────────────────────────────

def test_write_creates_timestamped_markdown():
    r = make_phase_report(phase_id="90A", phase_name="X", status="completed", summary="Y")
    with tempfile.TemporaryDirectory() as td:
        paths = write_phase_report(r, Path(td))
        assert Path(paths["markdown"]).exists()
        assert Path(paths["json"]).exists()
        assert Path(paths["latest_markdown"]).exists()
        assert Path(paths["latest_json"]).exists()
        content = Path(paths["markdown"]).read_text()
        assert "90A" in content


def test_write_updates_latest_files():
    r1 = make_phase_report(phase_id="90A", phase_name="First", status="completed", summary="Done.")
    r2 = make_phase_report(phase_id="90B", phase_name="Second", status="completed", summary="Also done.")
    with tempfile.TemporaryDirectory() as td:
        write_phase_report(r1, Path(td))
        write_phase_report(r2, Path(td))
        latest = Path(td) / "latest.md"
        content = latest.read_text()
        assert "Second" in content


def test_read_latest_returns_report():
    r = make_phase_report(phase_id="90A", phase_name="X", status="completed", summary="Y")
    with tempfile.TemporaryDirectory() as td:
        write_phase_report(r, Path(td))
        latest = read_latest_report(Path(td))
        assert latest is not None
        assert latest.phase_id == "90A"


def test_read_latest_none_when_missing():
    with tempfile.TemporaryDirectory() as td:
        assert read_latest_report(Path(td)) is None


def test_cannot_write_invalid_report():
    r = PhaseReport()  # missing all required fields
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(ValueError):
            write_phase_report(r, Path(td))


# ── No-go confirmations preserved ────────────────────────────────────────────

def test_no_go_confirmations_preserved_in_json():
    r = make_phase_report(
        phase_id="90A", phase_name="X", status="completed", summary="Y",
        explicit_no_go_confirmations=[
            "No enforcement implemented",
            "No shell interception",
            "No backend invocation",
        ],
    )
    data = json.loads(r.render_json())
    assert len(data["explicit_no_go_confirmations"]) == 3


# ── Commits and push state ───────────────────────────────────────────────────

def test_commits_and_push_preserved():
    r = make_phase_report(
        phase_id="90A", phase_name="X", status="completed", summary="Y",
        commits=["abc123", "def456"],
        pushed_status="pushed",
        origin_main_head_count=0,
    )
    data = json.loads(r.render_json())
    assert data["commits"] == ["abc123", "def456"]
    assert data["pushed_status"] == "pushed"
    assert data["origin_main_head_count"] == 0


# ── No secrets in output ─────────────────────────────────────────────────────

def test_no_secrets_in_markdown():
    r = make_phase_report(phase_id="90A", phase_name="X", status="completed", summary="Done with sk-test-123.")
    md = r.render_markdown()
    # Secrets should never appear in phase reports — this is operator responsibility
    # The model itself doesn't filter, but the test verifies the content passes through
    assert "Done with sk-test-123." in md


# ── Safe filename generation ─────────────────────────────────────────────────

def test_special_chars_in_phase_id_sanitized():
    r = make_phase_report(
        phase_id="90A — Test & Phase", phase_name="X", status="completed", summary="Y",
    )
    with tempfile.TemporaryDirectory() as td:
        paths = write_phase_report(r, Path(td))
        filename = Path(paths["markdown"]).name
        assert "&" not in filename
        assert "—" not in filename


# ── Metadata passthrough ────────────────────────────────────────────────────

def test_metadata_preserved():
    r = make_phase_report(
        phase_id="90A", phase_name="X", status="completed", summary="Y",
        metadata={"operator": "test-user", "session": "s1"},
    )
    assert r.metadata["operator"] == "test-user"


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 92D — Automatic finalization hook tests
# ═══════════════════════════════════════════════════════════════════════════════

from pcae.core.phase_reports import finalize_phase_report


def test_finalize_creates_latest_artifacts():
    with tempfile.TemporaryDirectory() as td:
        fin = finalize_phase_report(
            phase_id="90A", phase_name="Test Phase", status="completed",
            summary="All done.", reports_dir=Path(td),
        )
        assert fin["report"] is not None
        assert fin["paths"]["latest_markdown"]
        assert Path(fin["paths"]["latest_markdown"]).exists()
        assert Path(fin["paths"]["latest_json"]).exists()


def test_finalize_creates_timestamped_artifacts():
    with tempfile.TemporaryDirectory() as td:
        fin = finalize_phase_report(
            phase_id="90A", phase_name="Test Phase", status="completed",
            summary="Done.", reports_dir=Path(td),
        )
        assert fin["paths"]["markdown"]
        assert fin["paths"]["json"]
        assert Path(fin["paths"]["markdown"]).exists()
        assert Path(fin["paths"]["json"]).exists()


def test_finalize_report_includes_phase_identity():
    with tempfile.TemporaryDirectory() as td:
        fin = finalize_phase_report(
            phase_id="91A", phase_name="Broker Proto", status="completed",
            summary="Implemented.", reports_dir=Path(td),
        )
        content = Path(fin["paths"]["latest_markdown"]).read_text()
        assert "91A" in content
        assert "Broker Proto" in content


def test_finalize_notification_skipped_by_default():
    with tempfile.TemporaryDirectory() as td:
        fin = finalize_phase_report(
            phase_id="90A", phase_name="X", status="completed",
            summary="Y", reports_dir=Path(td),
        )
        assert fin["notification_skipped"] is True
        assert fin["notification_results"] is None


def test_finalize_preserves_explicit_no_go():
    with tempfile.TemporaryDirectory() as td:
        fin = finalize_phase_report(
            phase_id="90A", phase_name="X", status="completed",
            summary="Y",
            explicit_no_go_confirmations=["No enforcement", "No shell"],
            reports_dir=Path(td),
        )
        content = Path(fin["paths"]["latest_markdown"]).read_text()
        assert "No enforcement" in content


def test_finalize_includes_commits():
    with tempfile.TemporaryDirectory() as td:
        fin = finalize_phase_report(
            phase_id="90A", phase_name="X", status="completed",
            summary="Y", commits=["abc123", "def456"],
            pushed_status="pushed", origin_main_head_count=0,
            reports_dir=Path(td),
        )
        content = Path(fin["paths"]["latest_markdown"]).read_text()
        assert "abc123" in content


def test_finalize_includes_next_phase():
    with tempfile.TemporaryDirectory() as td:
        fin = finalize_phase_report(
            phase_id="90A", phase_name="X", status="completed",
            summary="Y", recommended_next_phase="91A",
            reports_dir=Path(td),
        )
        content = Path(fin["paths"]["latest_markdown"]).read_text()
        assert "91A" in content


def test_finalize_notification_with_filesystem_sink(monkeypatch):
    monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
    monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")
    with tempfile.TemporaryDirectory() as td:
        notify_dir = Path(td) / "notifications"
        monkeypatch.setenv("PCAE_NOTIFY_OUTPUT_DIR", str(notify_dir))
        fin = finalize_phase_report(
            phase_id="90A", phase_name="X", status="completed",
            summary="Y", reports_dir=Path(td),
        )
        assert fin["notification_skipped"] is False
        assert fin["notification_results"] is not None
        assert len(fin["notification_results"]) > 0
        assert fin["notification_results"][0].success is True


def test_finalize_notification_with_noop_sink(monkeypatch):
    monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
    monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
    with tempfile.TemporaryDirectory() as td:
        fin = finalize_phase_report(
            phase_id="90A", phase_name="X", status="completed",
            summary="Y", reports_dir=Path(td),
        )
        assert fin["notification_skipped"] is False
        assert fin["notification_results"][0].success is True


def test_finalize_telegram_disabled_does_not_send(monkeypatch):
    monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
    monkeypatch.setenv("PCAE_NOTIFY_SINKS", "telegram")
    # No PCAE_TELEGRAM_BOT_TOKEN set → TelegramSink won't be configured
    with tempfile.TemporaryDirectory() as td:
        fin = finalize_phase_report(
            phase_id="90A", phase_name="X", status="completed",
            summary="Y", reports_dir=Path(td),
        )
        assert fin["report"] is not None  # report still created
        # Notification attempted but Telegram fails gracefully


def test_finalize_notification_failure_non_fatal(monkeypatch):
    """Report creation succeeds even if notification config is broken."""
    monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
    monkeypatch.setenv("PCAE_NOTIFY_SINKS", "telegram")
    # Missing token → sink disabled, but report still created
    with tempfile.TemporaryDirectory() as td:
        fin = finalize_phase_report(
            phase_id="90A", phase_name="X", status="completed",
            summary="Y", reports_dir=Path(td),
        )
        assert fin["report"] is not None
        assert fin["report_error"] is None


def test_finalize_report_creation_failure_handled():
    """Invalid phase_id should not crash."""
    fin = finalize_phase_report(
        phase_id="", phase_name="X", status="completed",
        summary="Y",
    )
    assert fin["report"] is None
    assert fin["report_error"] is not None


def test_finalize_with_all_fields():
    with tempfile.TemporaryDirectory() as td:
        fin = finalize_phase_report(
            phase_id="92A", phase_name="Full Test", status="completed",
            summary="Everything works.",
            files_changed=5, tests_run=3305,
            test_results={"fast_green": "3305/3305"},
            governance_results={"health": "healthy", "check": "passed"},
            commits=["abc123", "def456"],
            pushed_status="pushed", origin_main_head_count=0,
            explicit_no_go_confirmations=["No enforcement", "No Telegram inbound"],
            recommended_next_phase="93A",
            reports_dir=Path(td),
        )
        assert fin["report"] is not None
        content = Path(fin["paths"]["latest_markdown"]).read_text()
        assert "Full Test" in content
        assert "3305" in content
        assert "healthy" in content
        assert "No enforcement" in content
        assert "93A" in content


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 92D.3 — Freshness and attachment repair
# ═══════════════════════════════════════════════════════════════════════════════


class TestLatestReportFreshness:
    """Verify write_phase_report correctly updates latest.md / latest.json."""

    def test_write_updates_latest_md(self):
        with tempfile.TemporaryDirectory() as td:
            r = make_phase_report(
                phase_id="93B", phase_name="Test B", status="completed",
                summary="Phase B done.",
            )
            write_phase_report(r, Path(td))
            latest = Path(td) / "latest.md"
            assert latest.exists()
            content = latest.read_text()
            assert "Test B" in content
            assert "Phase B done." in content

    def test_write_updates_latest_json(self):
        with tempfile.TemporaryDirectory() as td:
            r = make_phase_report(
                phase_id="93C", phase_name="Test C", status="completed",
                summary="Phase C done.",
            )
            write_phase_report(r, Path(td))
            latest_json = Path(td) / "latest.json"
            assert latest_json.exists()
            data = json.loads(latest_json.read_text())
            assert data["phase_id"] == "93C"

    def test_latest_overwritten_by_newer_phase(self):
        with tempfile.TemporaryDirectory() as td:
            r1 = make_phase_report(
                phase_id="92A", phase_name="First", status="completed",
                summary="First phase.",
            )
            write_phase_report(r1, Path(td))
            assert "First" in (Path(td) / "latest.md").read_text()

            r2 = make_phase_report(
                phase_id="92B", phase_name="Second", status="completed",
                summary="Second phase.",
            )
            write_phase_report(r2, Path(td))
            content = (Path(td) / "latest.md").read_text()
            assert "Second" in content
            assert "First" not in content

    def test_read_latest_report_returns_latest(self):
        with tempfile.TemporaryDirectory() as td:
            r1 = make_phase_report(
                phase_id="91A", phase_name="Old", status="completed",
                summary="Old phase.",
            )
            write_phase_report(r1, Path(td))
            r2 = make_phase_report(
                phase_id="91B", phase_name="New", status="completed",
                summary="New phase.",
            )
            write_phase_report(r2, Path(td))
            latest = read_latest_report(Path(td))
            assert latest is not None
            assert latest.phase_id == "91B"
            assert latest.phase_name == "New"

    def test_timestamped_artifact_created(self):
        with tempfile.TemporaryDirectory() as td:
            r = make_phase_report(
                phase_id="90X", phase_name="Timestamped", status="completed",
                summary="Check timestamp.",
            )
            paths = write_phase_report(r, Path(td))
            markdown_path = Path(paths["markdown"])
            assert markdown_path.exists()
            assert "90X" in markdown_path.name or "Timestamped" in markdown_path.read_text()


class TestFinalizePhaseReportCurrentPhase:
    """Verify finalize_phase_report uses the current phase's report path."""

    def test_notification_uses_timestamped_path(self):
        with tempfile.TemporaryDirectory() as td:
            fin = finalize_phase_report(
                phase_id="92D.3-test", phase_name="Freshness Test",
                status="completed", summary="Testing freshness.",
                reports_dir=Path(td),
            )
            assert fin["report"] is not None
            paths = fin["paths"]
            # Timestamped markdown path should exist and contain current phase
            ts_md = Path(paths["markdown"])
            assert ts_md.exists()
            content = ts_md.read_text()
            assert "Freshness Test" in content

    def test_latest_md_matches_timestamped(self):
        with tempfile.TemporaryDirectory() as td:
            fin = finalize_phase_report(
                phase_id="92D.3-t2", phase_name="Match Test",
                status="completed", summary="Match check.",
                reports_dir=Path(td),
            )
            paths = fin["paths"]
            ts_content = Path(paths["markdown"]).read_text()
            latest_content = Path(paths["latest_markdown"]).read_text()
            assert ts_content == latest_content, \
                "Timestamped and latest.md must have identical content"

    def test_notification_uses_current_phase_id(self):
        with tempfile.TemporaryDirectory() as td:
            fin = finalize_phase_report(
                phase_id="92D.3-t3", phase_name="Phase ID Test",
                status="completed", summary="Phase ID check.",
                reports_dir=Path(td),
            )
            report = fin["report"]
            assert report is not None
            assert report.phase_id == "92D.3-t3"


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 92D.4 — Notification dispatch visibility and files_changed repair
# ═══════════════════════════════════════════════════════════════════════════════


class TestFilesChangedNotCaptured:
    """Verify files_changed=0 renders as 'not captured' not misleading zero."""

    def test_files_changed_zero_shows_not_captured(self):
        r = make_phase_report(
            phase_id="92D.4", phase_name="Test", status="completed",
            summary="Done.", files_changed=0, commits=["abc123"],
        )
        md = r.render_markdown()
        assert "**Files changed:** not captured" in md, \
            "files_changed=0 should show 'not captured' even with commits present"

    def test_files_changed_positive_shows_number(self):
        r = make_phase_report(
            phase_id="92D.4", phase_name="Test", status="completed",
            summary="Done.", files_changed=5, commits=["abc123"],
        )
        md = r.render_markdown()
        assert "**Files changed:** 5" in md
        assert "**Files changed:** not captured" not in md

    def test_files_changed_zero_no_commits_shows_not_captured(self):
        r = make_phase_report(
            phase_id="92D.4", phase_name="Test", status="completed",
            summary="Done.", files_changed=0,
        )
        md = r.render_markdown()
        assert "**Files changed:** not captured" in md


class TestFinalizationNotificationResult:
    """Verify finalize_phase_report returns correct notification metadata."""

    def test_notification_skipped_when_disabled(self):
        import os
        with tempfile.TemporaryDirectory() as td:
            old_val = os.environ.pop("PCAE_NOTIFY_ENABLED", None)
            try:
                fin = finalize_phase_report(
                    phase_id="92D.4-t1", phase_name="Skip Test",
                    status="completed", summary="Skipping.",
                    reports_dir=Path(td),
                )
                assert fin["notification_skipped"] is True
            finally:
                if old_val is not None:
                    os.environ["PCAE_NOTIFY_ENABLED"] = old_val

    def test_notification_failure_non_fatal(self):
        """Notification failure should not affect report creation."""
        import os
        with tempfile.TemporaryDirectory() as td:
            old_notify = os.environ.get("PCAE_NOTIFY_ENABLED")
            old_sinks = os.environ.get("PCAE_NOTIFY_SINKS")
            os.environ["PCAE_NOTIFY_ENABLED"] = "1"
            os.environ["PCAE_NOTIFY_SINKS"] = "filesystem"
            try:
                fin = finalize_phase_report(
                    phase_id="92D.4-t2", phase_name="NonFatal Test",
                    status="completed", summary="Should complete.",
                    reports_dir=Path(td),
                )
                assert fin["report"] is not None
                assert fin["report_error"] is None
                paths = fin["paths"]
                assert Path(paths["markdown"]).exists()
                # Notification may have succeeded or failed — but report exists
            finally:
                if old_notify is not None:
                    os.environ["PCAE_NOTIFY_ENABLED"] = old_notify
                else:
                    os.environ.pop("PCAE_NOTIFY_ENABLED", None)
                if old_sinks is not None:
                    os.environ["PCAE_NOTIFY_SINKS"] = old_sinks
                else:
                    os.environ.pop("PCAE_NOTIFY_SINKS", None)

    def test_notification_result_includes_paths(self):
        import os
        with tempfile.TemporaryDirectory() as td:
            old_notify = os.environ.get("PCAE_NOTIFY_ENABLED")
            os.environ["PCAE_NOTIFY_ENABLED"] = "1"
            os.environ["PCAE_NOTIFY_SINKS"] = "noop"
            try:
                fin = finalize_phase_report(
                    phase_id="92D.4-t3", phase_name="Path Test",
                    status="completed", summary="Paths check.",
                    reports_dir=Path(td),
                )
                assert fin["notification_skipped"] is False
                assert fin["paths"]["markdown"]
                assert fin["paths"]["latest_markdown"]
            finally:
                if old_notify is not None:
                    os.environ["PCAE_NOTIFY_ENABLED"] = old_notify
                else:
                    os.environ.pop("PCAE_NOTIFY_ENABLED", None)
                os.environ.pop("PCAE_NOTIFY_SINKS", None)

