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
    assert "Telegram" in result.stdout


def test_status_json():
    data = _json(["status"])
    assert data["notification_foundation_available"] is True
    assert data["telegram_implemented"] is False
    assert data["automatic_hooks"] is False
    assert data["external_network"] is False


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
