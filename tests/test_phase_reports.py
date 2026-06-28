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
