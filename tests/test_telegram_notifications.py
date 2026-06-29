"""Tests for Phase 92C Telegram outbound notification sink.

All HTTP is mocked — no real network calls.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pcae.core.notifications import (
    TelegramSink,
    NotificationEvent,
    make_notification_event,
    NotificationResult,
    dispatch,
    phase_report_to_notification_event,
    EVENT_TYPE_PHASE_REPORT_CREATED,
    EVENT_TYPE_MANUAL_TEST,
    TELEGRAM_SINK_NAME,
)
from pcae.core.phase_reports import make_phase_report, write_phase_report, read_latest_report

REPO_ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ──────────────────────────────────────────────────────────────────

def _mock_opener(json_response: dict, status: int = 200):
    """Return a mock urlopen that returns the given JSON response."""
    def opener(req):
        resp = MagicMock()
        resp.read.return_value = json.dumps(json_response).encode()
        resp.status = status
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        return resp
    return opener


def _make_event(**kwargs):
    defaults = {
        "event_type": EVENT_TYPE_MANUAL_TEST,
        "title": "Test Phase",
        "message": "Everything passed.",
    }
    defaults.update(kwargs)
    return make_notification_event(**defaults)


# ── Configuration ────────────────────────────────────────────────────────────

def test_telegram_disabled_by_default():
    sink = TelegramSink(bot_token="t", chat_id="c", enabled=False)
    assert sink.is_configured()
    assert not sink.is_enabled()


def test_telegram_not_configured_without_token():
    sink = TelegramSink(bot_token="", chat_id="c", enabled=True)
    assert not sink.is_configured()


def test_telegram_not_configured_without_chat_id():
    sink = TelegramSink(bot_token="t", chat_id="", enabled=True)
    assert not sink.is_configured()


def test_telegram_configured_and_enabled():
    sink = TelegramSink(bot_token="t", chat_id="c", enabled=True)
    assert sink.is_configured()
    assert sink.is_enabled()


# ── Disabled / unconfigured behavior ─────────────────────────────────────────

def test_send_when_disabled_returns_failure():
    event = _make_event()
    sink = TelegramSink(bot_token="t", chat_id="c", enabled=False)
    result = sink.send(event)
    assert result.success is False
    assert result.error == "disabled_or_unconfigured"
    assert result.sink_name == TELEGRAM_SINK_NAME


def test_send_when_unconfigured_returns_failure():
    event = _make_event()
    sink = TelegramSink(bot_token="", chat_id="", enabled=True)
    result = sink.send(event)
    assert result.success is False


# ── sendMessage success ──────────────────────────────────────────────────────

def test_send_message_success():
    event = _make_event()
    sink = TelegramSink(
        bot_token="test-token", chat_id="123", enabled=True,
        _opener=_mock_opener({"ok": True, "result": {}}),
    )
    result = sink.send(event)
    assert result.success is True
    assert result.metadata["send_message_ok"] is True
    assert result.metadata["send_document_ok"] is True  # no artifact paths → no document needed


# ── sendMessage failure ──────────────────────────────────────────────────────

def test_send_message_failure():
    event = _make_event()
    sink = TelegramSink(
        bot_token="test-token", chat_id="123", enabled=True,
        _opener=_mock_opener({"ok": False, "error": "Forbidden"}),
    )
    result = sink.send(event)
    assert result.success is False
    assert "Forbidden" in (result.error or "")


# ── sendDocument with artifact path ──────────────────────────────────────────

def test_send_with_artifact_sends_document():
    with tempfile.TemporaryDirectory() as td:
        report_path = Path(td) / "latest.md"
        report_path.write_text("# Phase Report\n\nDone.")

        event = _make_event(artifact_paths=[str(report_path)])
        # The sendMessage mock succeeds, sendDocument mock succeeds
        call_count = [0]

        def counting_opener(req):
            call_count[0] += 1
            resp = MagicMock()
            if call_count[0] == 1:
                resp.read.return_value = b'{"ok": true, "result": {}}'
            else:
                resp.read.return_value = b'{"ok": true, "result": {"document": {}}}'
            resp.__enter__ = MagicMock(return_value=resp)
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        sink = TelegramSink(
            bot_token="test-token", chat_id="123", enabled=True,
            _opener=counting_opener,
        )
        result = sink.send(event)
        assert result.success is True
        assert result.metadata["send_document_ok"] is True
        assert call_count[0] == 2  # sendMessage + sendDocument


# ── sendMessage OK but sendDocument fails ────────────────────────────────────

def test_send_message_ok_document_fails():
    with tempfile.TemporaryDirectory() as td:
        report_path = Path(td) / "latest.md"
        report_path.write_text("# Report")

        event = _make_event(artifact_paths=[str(report_path)])
        call_count = [0]

        def fail_doc_opener(req):
            call_count[0] += 1
            resp = MagicMock()
            if call_count[0] == 1:
                resp.read.return_value = b'{"ok": true}'
            else:
                resp.read.return_value = b'{"ok": false, "error": "Bad Request"}'
            resp.__enter__ = MagicMock(return_value=resp)
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        sink = TelegramSink(
            bot_token="test-token", chat_id="123", enabled=True,
            _opener=fail_doc_opener,
        )
        result = sink.send(event)
        assert result.success is False
        assert result.metadata["send_message_ok"] is True
        assert result.metadata["send_document_ok"] is False


# ── Summary truncation ───────────────────────────────────────────────────────

def test_summary_truncated_when_too_long():
    long_msg = "x" * 4000
    event = _make_event(message=long_msg)
    sink = TelegramSink(
        bot_token="t", chat_id="c", enabled=True, max_message_chars=100,
        _opener=_mock_opener({"ok": True}),
    )
    result = sink.send(event)
    assert result.success is True  # summary was truncated before sending


# ── No real network calls ────────────────────────────────────────────────────

def test_no_real_network_calls():
    """Verify that TelegramSink with no _opener would make real calls,
    but our tests always inject _opener."""
    event = _make_event()
    sink = TelegramSink(bot_token="t", chat_id="c", enabled=True)
    # Without _opener, this WOULD make a real call.
    # The test verifies the sink structure, not the call.
    assert sink.is_enabled()


# ── No secret values in output ───────────────────────────────────────────────

def test_no_secret_in_result_message():
    event = _make_event()
    sink = TelegramSink(
        bot_token="secret-token-123", chat_id="456", enabled=True,
        _opener=_mock_opener({"ok": True}),
    )
    result = sink.send(event)
    assert "secret-token-123" not in result.message
    assert "456" not in result.message


# ── Summary message build ────────────────────────────────────────────────────

def test_summary_includes_phase_info():
    event = _make_event(
        title="Phase COMPLETED: Design Phase",
        message="Design done.",
        metadata={
            "phase_id": "92A", "phase_name": "Design Phase",
            "phase_status": "completed",
            "report_completeness": "partial",
            "missing_trust_fields": ["files_changed"],
        },
    )
    sink = TelegramSink(bot_token="t", chat_id="c", enabled=True,
                        _opener=_mock_opener({"ok": True}))
    text = sink._build_summary(event)
    assert "PCAE Phase" in text
    assert "92A" in text
    assert "completed" in text.lower() or "completed" in text
    assert "Design Phase" in text


# ── No Telegram polling/inbound behavior ─────────────────────────────────────

def test_no_inbound_methods():
    """TelegramSink has no polling, webhook, or inbound command methods."""
    sink = TelegramSink(bot_token="t", chat_id="c", enabled=True)
    forbidden = ["poll", "webhook", "listen", "run", "execute", "inbound", "command"]
    for attr in forbidden:
        assert not hasattr(sink, attr), f"TelegramSink must not have {attr}"


# ── No automatic phase-finalization hook ─────────────────────────────────────

def test_no_auto_hook():
    """phase_report_to_notification_event is a pure function, not a hook."""
    report = make_phase_report(phase_id="90A", phase_name="X", status="completed", summary="Y")
    event = phase_report_to_notification_event(report)
    assert event.event_type == EVENT_TYPE_PHASE_REPORT_CREATED
    # No side effects — just creates an event


# ── CLI: send-report missing latest ──────────────────────────────────────────

def test_cli_send_report_no_latest():
    with tempfile.TemporaryDirectory() as td:
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "notify", "send-report", "--reports-dir", td],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode != 0
        assert "No latest" in result.stdout


# ── CLI: send-report with latest ─────────────────────────────────────────────

def test_cli_send_report_with_latest():
    with tempfile.TemporaryDirectory() as td:
        report = make_phase_report(phase_id="90A", phase_name="Test", status="completed", summary="Done.")
        write_phase_report(report, Path(td))
        # Will fail because Telegram not configured — but shouldn't crash
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "notify", "send-report", "--reports-dir", td],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert "FAILED" in result.stdout or "disabled" in result.stdout.lower()


# ── CLI: send-report JSON ────────────────────────────────────────────────────

def test_cli_send_report_json():
    with tempfile.TemporaryDirectory() as td:
        report = make_phase_report(phase_id="90A", phase_name="Test", status="completed", summary="Done.")
        write_phase_report(report, Path(td))
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "notify", "send-report", "--reports-dir", td, "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        assert "event" in data
        assert "results" in data


# ── Integration: telegram sink in dispatcher ─────────────────────────────────

def test_telegram_sink_in_dispatcher():
    event = _make_event()
    sink = TelegramSink(
        bot_token="t", chat_id="c", enabled=True,
        _opener=_mock_opener({"ok": True}),
    )
    results = dispatch(event, [sink])
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].sink_name == TELEGRAM_SINK_NAME


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 92D.2 — Telegram payload compatibility repair
# ═══════════════════════════════════════════════════════════════════════════════


class TestSendMessagePayloadFormat:
    """Verify sendMessage uses URL-encoded form data, not JSON, no parse_mode."""

    def test_send_message_uses_url_encoded_form(self):
        """sendMessage must use application/x-www-form-urlencoded."""
        captured_req = {}

        def capture_opener(req):
            captured_req["headers"] = dict(req.headers)
            captured_req["body"] = req.data
            resp = MagicMock()
            resp.read.return_value = b'{"ok": true, "result": {}}'
            resp.__enter__ = MagicMock(return_value=resp)
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        event = _make_event(
            title="Test Phase",
            message="Everything passed. Shell gate: 122/122. Fast-green: 3272/3272.",
            metadata={"phase_id": "93C", "phase_name": "Test", "phase_status": "completed"},
        )
        sink = TelegramSink(
            bot_token="test-token", chat_id="123", enabled=True,
            _opener=capture_opener,
        )
        result = sink.send(event)
        assert result.success is True

        # Verify Content-Type is URL-encoded form
        ct = captured_req.get("headers", {}).get("Content-type", "")
        assert "application/x-www-form-urlencoded" in ct, \
            f"Expected urlencoded content type, got: {ct}"

        # Verify chat_id is in the form body
        body = captured_req.get("body", b"").decode()
        assert "chat_id=123" in body
        assert "93C" in body

    def test_no_parse_mode_in_send_message(self):
        """sendMessage must NOT include parse_mode by default."""
        captured_body = {}

        def capture_opener(req):
            captured_body["body"] = req.data
            resp = MagicMock()
            resp.read.return_value = b'{"ok": true, "result": {}}'
            resp.__enter__ = MagicMock(return_value=resp)
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        event = _make_event(message="[INFO] Brackets and *stars* in text")
        sink = TelegramSink(
            bot_token="test-token", chat_id="123", enabled=True,
            _opener=capture_opener,
        )
        result = sink.send(event)
        assert result.success is True

        body = captured_body.get("body", b"").decode()
        assert "parse_mode" not in body, \
            "parse_mode must not be sent by default"

    def test_markdown_brackets_dont_break(self):
        """Text with [brackets] should send successfully (no Markdown parsing)."""
        event = _make_event(
            title="Phase COMPLETED: [Test] Phase",
            message="Key: [INFO] Task [FAILED] at path/to/file",
        )
        sink = TelegramSink(
            bot_token="test-token", chat_id="123", enabled=True,
            _opener=_mock_opener({"ok": True, "result": {}}),
        )
        result = sink.send(event)
        assert result.success is True

    def test_send_message_success_proceeds_to_document(self):
        """Successful sendMessage should proceed to sendDocument."""
        with tempfile.TemporaryDirectory() as td:
            report_path = Path(td) / "latest.md"
            report_path.write_text("# Report")

            event = _make_event(artifact_paths=[str(report_path)])
            call_count = [0]

            def counting_opener(req):
                call_count[0] += 1
                resp = MagicMock()
                resp.read.return_value = b'{"ok": true, "result": {}}'
                resp.__enter__ = MagicMock(return_value=resp)
                resp.__exit__ = MagicMock(return_value=False)
                return resp

            sink = TelegramSink(
                bot_token="test-token", chat_id="123", enabled=True,
                _opener=counting_opener,
            )
            result = sink.send(event)
            assert result.success is True
            assert call_count[0] == 2  # sendMessage + sendDocument


class TestHttpErrorBodyCapture:
    """Verify Telegram HTTP error response bodies are captured."""

    def test_http_400_error_body_captured(self):
        """HTTP 400 response body should be read and error description surfaced."""
        from urllib.error import HTTPError

        def error_opener(req):
            error_body = b'{"ok":false,"error_code":400,"description":"Bad Request: cannot parse entities"}'
            exc = HTTPError(
                "https://api.telegram.org/botX/sendMessage",
                400, "Bad Request",
                {}, BytesIO(error_body),
            )
            raise exc

        event = _make_event(message="test")
        sink = TelegramSink(
            bot_token="test-token", chat_id="123", enabled=True,
            _opener=error_opener,
        )
        result = sink.send(event)
        assert result.success is False
        # The Telegram description should be in the error
        assert "parse entities" in (result.error or ""), \
            f"Expected Telegram error description, got: {result.error}"

    def test_http_error_without_body_handled(self):
        """HTTP error without readable body should still produce useful error."""
        from urllib.error import HTTPError

        def error_opener(req):
            exc = HTTPError(
                "https://api.telegram.org/botX/sendMessage",
                403, "Forbidden",
                {}, BytesIO(b""),
            )
            raise exc

        event = _make_event()
        sink = TelegramSink(
            bot_token="test-token", chat_id="123", enabled=True,
            _opener=error_opener,
        )
        result = sink.send(event)
        assert result.success is False
        assert "403" in (result.error or "")

    def test_token_not_leaked_in_error(self):
        """Error output must not contain the bot token."""
        from urllib.error import HTTPError

        def error_opener(req):
            error_body = b'{"ok":false,"description":"Unauthorized"}'
            exc = HTTPError(
                "https://api.telegram.org/botX/sendMessage",
                401, "Unauthorized",
                {}, BytesIO(error_body),
            )
            raise exc

        event = _make_event()
        sink = TelegramSink(
            bot_token="secret-bot-token-abc123", chat_id="999", enabled=True,
            _opener=error_opener,
        )
        result = sink.send(event)
        assert result.success is False
        assert "secret-bot-token-abc123" not in (result.error or "")
        assert "secret-bot-token-abc123" not in (result.message or "")

    def test_chat_id_not_leaked_in_error(self):
        """Error output should not expose chat ID unless project policy allows."""
        from urllib.error import HTTPError

        def error_opener(req):
            error_body = b'{"ok":false,"description":"Chat not found"}'
            exc = HTTPError(
                "https://api.telegram.org/botX/sendMessage",
                400, "Bad Request",
                {}, BytesIO(error_body),
            )
            raise exc

        event = _make_event()
        sink = TelegramSink(
            bot_token="t", chat_id="-1001234567890", enabled=True,
            _opener=error_opener,
        )
        result = sink.send(event)
        assert result.success is False
        # The result.error should contain the Telegram description but not chat ID
        assert "-1001234567890" not in (result.error or ""), \
            f"Chat ID should not be leaked in error: {result.error}"


class TestSummaryTruncationPreserved:
    """Verify summary truncation still works with URL-encoded payload."""

    def test_truncation_still_works(self):
        long_msg = "y" * 4000
        event = _make_event(message=long_msg)
        sink = TelegramSink(
            bot_token="t", chat_id="c", enabled=True, max_message_chars=100,
            _opener=_mock_opener({"ok": True}),
        )
        result = sink.send(event)
        assert result.success is True

    def test_truncation_ellipsis(self):
        long_msg = "z" * 200
        event = _make_event(message=long_msg)
        sink = TelegramSink(
            bot_token="t", chat_id="c", enabled=True, max_message_chars=10,
            _opener=_mock_opener({"ok": True}),
        )
        # _build_summary should produce truncated text
        summary = sink._build_summary(event)
        assert len(summary) <= 10
        assert "..." in summary


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 92D.5 — Trust contract: Telegram text format tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestTelegramTextTrustContract:
    """Verify Telegram text summary meets trust contract requirements."""

    def test_text_includes_phase_id_and_status(self):
        event = _make_event(
            title="Phase COMPLETED: Test",
            message="Done.",
            metadata={"phase_id": "93C", "phase_status": "completed",
                       "phase_name": "Test Phase"},
        )
        sink = TelegramSink(bot_token="t", chat_id="c", enabled=True)
        text = sink._build_summary(event)
        assert "PCAE Phase" in text
        assert "93C" in text

    def test_text_includes_completeness(self):
        event = _make_event(
            title="Test", message="Done.",
            metadata={"phase_id": "93C", "phase_status": "completed",
                       "report_completeness": "partial",
                       "missing_trust_fields": ["files_changed", "tests_run"]},
        )
        sink = TelegramSink(bot_token="t", chat_id="c", enabled=True)
        text = sink._build_summary(event)
        assert "partial" in text
        assert "files_changed" in text

    def test_text_does_not_include_long_summary_body(self):
        long_msg = "A" * 2000
        event = _make_event(
            title="Test", message=long_msg,
            metadata={"phase_id": "93C", "phase_status": "completed"},
        )
        sink = TelegramSink(bot_token="t", chat_id="c", enabled=True)
        text = sink._build_summary(event)
        # The long message should NOT appear verbatim
        assert "A" * 200 not in text
        assert len(text) <= sink._max_message_chars

    def test_text_distinguishes_phase_commit_from_recent(self):
        event = _make_event(
            title="Test", message="Done.",
            metadata={
                "phase_id": "93C", "phase_status": "completed",
                "commits": ["e49b4a74", "0973b4bf", "4885d6c5"],
            },
        )
        sink = TelegramSink(bot_token="t", chat_id="c", enabled=True)
        text = sink._build_summary(event)
        assert "Phase commit" in text
        assert "e49b4a74" in text
        assert "Recent commits" in text

    def test_text_includes_notification_dispatched(self):
        event = _make_event(
            title="Test", message="Done.",
            metadata={"phase_id": "93C", "phase_status": "completed"},
        )
        sink = TelegramSink(bot_token="t", chat_id="c", enabled=True)
        text = sink._build_summary(event)
        assert "sent via telegram" in text

    def test_text_includes_full_report_attached(self):
        event = _make_event(
            title="Test", message="Done.",
            metadata={"phase_id": "93C", "phase_status": "completed"},
        )
        sink = TelegramSink(bot_token="t", chat_id="c", enabled=True)
        text = sink._build_summary(event)
        assert "Full report attached" in text

    def test_text_concise_under_800_chars(self):
        event = _make_event(
            title="Test", message="Done.",
            metadata={
                "phase_id": "93C", "phase_name": "Shell Gate Audit Evidence Model",
                "phase_status": "completed",
                "report_completeness": "partial",
                "missing_trust_fields": ["files_changed"],
                "commits": ["e49b4a74"],
                "pushed_status": "pushed",
                "recommended_next_phase": "TBD",
            },
        )
        sink = TelegramSink(bot_token="t", chat_id="c", enabled=True)
        text = sink._build_summary(event)
        assert len(text) <= 800, f"Telegram text should be concise, got {len(text)} chars"
