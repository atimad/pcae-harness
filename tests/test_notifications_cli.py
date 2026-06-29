"""CLI tests for Phase 92B notification commands."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(args: list[str]) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "pcae", "notify"] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)


def _json(args: list[str]) -> dict:
    result = _run(args + ["--json"])
    assert result.returncode == 0, f"Failed: {result.stderr}"
    return json.loads(result.stdout)


# ── status ───────────────────────────────────────────────────────────────────


def test_status_text():
    result = _run(["status"])
    assert result.returncode == 0
    assert "noop" in result.stdout
    assert "filesystem" in result.stdout
    assert "telegram" in result.stdout.lower()
    assert "Telegram sink" in result.stdout


def test_status_json():
    data = _json(["status"])
    assert data["notification_foundation_available"] is True
    assert data["telegram_sink_available"] is True
    assert data["auto_finalization_hook_available"] is True
    assert data["external_network_possible"] is False
    assert data["external_network_active_by_default"] is False


# ── test noop ────────────────────────────────────────────────────────────────


def test_test_noop_text():
    result = _run(["test", "--sink", "noop"])
    assert result.returncode == 0


def test_test_noop_json():
    data = _json(["test", "--sink", "noop"])
    assert "event" in data
    assert "results" in data
    assert data["results"][0]["success"] is True


# ── test stdout ──────────────────────────────────────────────────────────────


def test_test_stdout_text():
    result = _run(["test", "--sink", "stdout"])
    assert result.returncode == 0


def test_test_stdout_json():
    data = _json(["test", "--sink", "stdout"])
    assert data["results"][0]["success"] is True


# ── test filesystem ──────────────────────────────────────────────────────────


def test_test_filesystem_text():
    with tempfile.TemporaryDirectory() as td:
        result = _run(["test", "--sink", "filesystem", "--output-dir", td])
        assert result.returncode == 0
        assert any(Path(td).iterdir())


def test_test_filesystem_json():
    with tempfile.TemporaryDirectory() as td:
        data = _json(["test", "--sink", "filesystem", "--output-dir", td])
        assert data["results"][0]["success"] is True


# ── test unknown sink ────────────────────────────────────────────────────────


def test_test_unknown_sink_fails():
    result = _run(["test", "--sink", "telegram"])
    assert result.returncode != 0


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 92D.4 — Status text context-sensitive behavior
# ═══════════════════════════════════════════════════════════════════════════════


class TestStatusTextContextSensitive:
    """Verify pcae notify status text reflects actual state."""

    def test_status_shows_ready_when_configured_and_enabled(self):
        import os
        old_token = os.environ.get("PCAE_TELEGRAM_BOT_TOKEN")
        old_chat = os.environ.get("PCAE_TELEGRAM_CHAT_ID")
        old_tg_en = os.environ.get("PCAE_TELEGRAM_ENABLED")
        old_notify = os.environ.get("PCAE_NOTIFY_ENABLED")
        os.environ["PCAE_TELEGRAM_BOT_TOKEN"] = "test-token"
        os.environ["PCAE_TELEGRAM_CHAT_ID"] = "123"
        os.environ["PCAE_TELEGRAM_ENABLED"] = "1"
        os.environ["PCAE_NOTIFY_ENABLED"] = "1"
        try:
            result = _run(["status"])
            assert result.returncode == 0
            assert "ready for outbound delivery" in result.stdout
        finally:
            _restore_env("PCAE_TELEGRAM_BOT_TOKEN", old_token)
            _restore_env("PCAE_TELEGRAM_CHAT_ID", old_chat)
            _restore_env("PCAE_TELEGRAM_ENABLED", old_tg_en)
            _restore_env("PCAE_NOTIFY_ENABLED", old_notify)

    def test_status_shows_configured_but_disabled_when_tg_disabled(self):
        import os
        old_token = os.environ.get("PCAE_TELEGRAM_BOT_TOKEN")
        old_chat = os.environ.get("PCAE_TELEGRAM_CHAT_ID")
        old_tg_en = os.environ.get("PCAE_TELEGRAM_ENABLED")
        old_notify = os.environ.get("PCAE_NOTIFY_ENABLED")
        os.environ["PCAE_TELEGRAM_BOT_TOKEN"] = "test-token"
        os.environ["PCAE_TELEGRAM_CHAT_ID"] = "123"
        os.environ["PCAE_TELEGRAM_ENABLED"] = "0"
        os.environ["PCAE_NOTIFY_ENABLED"] = "1"
        try:
            result = _run(["status"])
            assert result.returncode == 0
            assert "configured but disabled" in result.stdout
        finally:
            _restore_env("PCAE_TELEGRAM_BOT_TOKEN", old_token)
            _restore_env("PCAE_TELEGRAM_CHAT_ID", old_chat)
            _restore_env("PCAE_TELEGRAM_ENABLED", old_tg_en)
            _restore_env("PCAE_NOTIFY_ENABLED", old_notify)

    def test_status_shows_unconfigured_when_missing_token(self):
        import os
        old_token = os.environ.get("PCAE_TELEGRAM_BOT_TOKEN")
        old_chat = os.environ.get("PCAE_TELEGRAM_CHAT_ID")
        old_tg_en = os.environ.get("PCAE_TELEGRAM_ENABLED")
        old_notify = os.environ.get("PCAE_NOTIFY_ENABLED")
        os.environ["PCAE_TELEGRAM_BOT_TOKEN"] = ""
        os.environ["PCAE_TELEGRAM_CHAT_ID"] = ""
        os.environ["PCAE_TELEGRAM_ENABLED"] = "0"
        os.environ["PCAE_NOTIFY_ENABLED"] = "0"
        try:
            result = _run(["status"])
            assert result.returncode == 0
            assert "disabled unless configured" in result.stdout
        finally:
            _restore_env("PCAE_TELEGRAM_BOT_TOKEN", old_token)
            _restore_env("PCAE_TELEGRAM_CHAT_ID", old_chat)
            _restore_env("PCAE_TELEGRAM_ENABLED", old_tg_en)
            _restore_env("PCAE_NOTIFY_ENABLED", old_notify)

    def test_status_json_includes_correct_state(self):
        import os
        old_token = os.environ.get("PCAE_TELEGRAM_BOT_TOKEN")
        old_chat = os.environ.get("PCAE_TELEGRAM_CHAT_ID")
        old_tg_en = os.environ.get("PCAE_TELEGRAM_ENABLED")
        os.environ["PCAE_TELEGRAM_BOT_TOKEN"] = "test-token"
        os.environ["PCAE_TELEGRAM_CHAT_ID"] = "123"
        os.environ["PCAE_TELEGRAM_ENABLED"] = "1"
        try:
            data = _json(["status"])
            assert data["telegram_configured"] is True
            assert data["telegram_enabled"] is True
            assert data["telegram_token_present"] is True
            assert data["telegram_chat_id_present"] is True
        finally:
            _restore_env("PCAE_TELEGRAM_BOT_TOKEN", old_token)
            _restore_env("PCAE_TELEGRAM_CHAT_ID", old_chat)
            _restore_env("PCAE_TELEGRAM_ENABLED", old_tg_en)

    def test_no_token_leaked_in_status(self):
        import os
        old_token = os.environ.get("PCAE_TELEGRAM_BOT_TOKEN")
        old_chat = os.environ.get("PCAE_TELEGRAM_CHAT_ID")
        old_tg_en = os.environ.get("PCAE_TELEGRAM_ENABLED")
        os.environ["PCAE_TELEGRAM_BOT_TOKEN"] = "secret-token-abc123xyz"
        os.environ["PCAE_TELEGRAM_CHAT_ID"] = "-100999888777"
        os.environ["PCAE_TELEGRAM_ENABLED"] = "1"
        try:
            result = _run(["status"])
            assert result.returncode == 0
            assert "secret-token-abc123xyz" not in result.stdout
            assert "-100999888777" not in result.stdout
        finally:
            _restore_env("PCAE_TELEGRAM_BOT_TOKEN", old_token)
            _restore_env("PCAE_TELEGRAM_CHAT_ID", old_chat)
            _restore_env("PCAE_TELEGRAM_ENABLED", old_tg_en)


def _restore_env(key: str, old_val: str | None):
    import os
    if old_val is not None:
        os.environ[key] = old_val
    else:
        os.environ.pop(key, None)
