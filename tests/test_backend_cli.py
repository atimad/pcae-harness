"""CLI tests for Phase 94E — Backend invocation dry-run CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd_args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pcae", "backend"] + cmd_args,
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=15,
    )

def _json(cmd_args: list[str]) -> dict:
    r = _run(cmd_args + ["--json"])
    assert r.returncode == 0, f"CLI failed: {r.stderr}"
    return json.loads(r.stdout)


class TestBackendList:
    def test_list_shows_backends(self):
        r = _run(["list"])
        assert r.returncode == 0
        assert "claude" in r.stdout

    def test_list_json(self):
        data = _json(["list"])
        assert len(data["backends"]) == 5

    def test_list_json_no_secrets(self):
        data = _json(["list"])
        j = json.dumps(data)
        assert "sk-ant" not in j


class TestBackendStatus:
    def test_status_reports_registry(self):
        r = _run(["status"])
        assert r.returncode == 0
        assert "5 backend" in r.stdout

    def test_status_reports_no_execution(self):
        r = _run(["status"])
        assert "none" in r.stdout.lower()

    def test_status_json(self):
        data = _json(["status"])
        assert data["registry_available"] is True
        assert data["no_execution"] is True


class TestBackendPlan:
    def test_plan_mock_dry_run(self):
        r = _run(["plan", "--backend", "mock", "--phase-id", "94E"])
        assert r.returncode == 0
        assert "mock" in r.stdout

    def test_plan_unknown_backend_fails(self):
        r = _run(["plan", "--backend", "nonexistent"])
        assert r.returncode != 0
        assert "Unknown" in r.stdout

    def test_plan_json(self):
        data = _json(["plan", "--backend", "mock", "--phase-id", "94E"])
        assert data["readiness"]["status"] in ("ready", "missing_evidence")

    def test_plan_does_not_invoke_backend(self):
        r = _run(["plan", "--backend", "mock"])
        assert "dry-run" in r.stdout.lower() or "no backend" in r.stdout.lower()

    def test_plan_no_execution_remains_true(self):
        data = _json(["plan", "--backend", "mock"])
        assert data["request"]["no_execution_by_default"] is True


class TestBackendShow:
    def test_show_missing_artifacts(self):
        r = _run(["show", "--latest"])
        assert r.returncode != 0

    def test_show_no_secrets_in_output(self):
        r = _run(["show", "--latest"])
        assert "sk-" not in r.stdout


class TestNoSubprocess:
    def test_list_no_subprocess(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "subprocess.run" not in source
        assert "Popen(" not in source
