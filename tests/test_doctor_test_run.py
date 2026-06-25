"""Tests for pcae doctor test-run (Phase 88N.2).

Verifies that the test-run preflight correctly detects (or does not detect)
running expensive pytest processes, and that the command is read-only and
does not start, kill, or mutate anything.
"""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from pcae.cli import main
from pcae.commands.task import _detect_active_pytest_processes, run_doctor_test_run


# ── Unit tests for _detect_active_pytest_processes ──


def _fake_ps(*patterns: str) -> str:
    """Build a fake ps aux output containing the given process lines."""
    header = "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\n"
    return header + "\n".join(patterns) + "\n"


def _run_detect(fake_output: str) -> list[str]:
    with patch(
        "pcae.commands.task._sp.run" if False else "subprocess.run",
        side_effect=lambda *a, **kw: type(
            "R", (), {"stdout": fake_output, "returncode": 0}
        )(),
    ):
        # Call the real implementation patching the subprocess inside the function
        pass
    return []  # placeholder; real test below uses direct patching


class _FakeProcess:
    def __init__(self, stdout: str = "", returncode: int = 0):
        self.stdout = stdout
        self.returncode = returncode


def _patch_ps(fake_output: str):
    """Context manager that patches subprocess.run inside _detect_active_pytest_processes."""
    import subprocess as _sp_mod

    return patch.object(
        _sp_mod,
        "run",
        return_value=_FakeProcess(stdout=fake_output),
    )


def test_detect_no_active_pytest():
    """No pytest in ps output → empty list (clear_to_run=true)."""
    fake = _fake_ps(
        "user   1234  0.0  0.1  12345  1234 ?  S  10:00  0:00 bash",
        "user   5678  0.0  0.2  23456  2345 ?  S  10:01  0:00 python my_script.py",
    )
    with _patch_ps(fake):
        result = _detect_active_pytest_processes()
    assert result == []


def test_detect_xdist_pytest_found():
    """pytest -n auto in ps output → process detected (clear_to_run=false)."""
    fake = _fake_ps(
        "user   9999  99.0  5.0  999999  99999 ?  R  10:05  5:00 python -m pytest -n auto",
    )
    with _patch_ps(fake):
        result = _detect_active_pytest_processes()
    assert len(result) == 1
    assert "pytest" in result[0]


def test_detect_xdist_with_n4():
    """pytest -n 4 is also flagged as an expensive xdist run."""
    fake = _fake_ps(
        "user   1111  80.0  4.0  888888  88888 ?  R  10:06  3:00 python -m pytest -n 4 tests/",
    )
    with _patch_ps(fake):
        result = _detect_active_pytest_processes()
    assert len(result) == 1


def test_detect_ignores_ps_aux_itself():
    """grep and ps lines are filtered out and not counted as active runs."""
    fake = _fake_ps(
        "user   2222  0.0  0.0  11111  1111 ?  S  10:07  0:00 grep pytest ps aux",
        "user   3333  0.0  0.0  22222  2222 ?  S  10:08  0:00 ps aux",
    )
    with _patch_ps(fake):
        result = _detect_active_pytest_processes()
    assert result == []


def test_detect_ignores_collect_only():
    """A pytest --collect-only run (no -n) should not be flagged."""
    fake = _fake_ps(
        "user   4444  1.0  0.5  33333  3333 ?  S  10:09  0:01 python -m pytest --collect-only -q",
    )
    with _patch_ps(fake):
        result = _detect_active_pytest_processes()
    assert result == []


def test_detect_multiple_xdist_runs():
    """Multiple concurrent xdist runs → all detected."""
    fake = _fake_ps(
        "user   5555  90.0  5.0  999999  99999 ?  R  10:10  4:00 python -m pytest -n auto tests/",
        "user   6666  85.0  4.5  888888  88888 ?  R  10:11  3:30 python -m pytest -n auto",
    )
    with _patch_ps(fake):
        result = _detect_active_pytest_processes()
    assert len(result) == 2


def test_detect_ignores_shell_with_pytest_in_eval():
    """Shell processes with pytest in their eval args are NOT flagged.

    Regression test for the 88N.2 false-positive: pcae doctor test-run itself
    is invoked by a shell like:
        /bin/zsh -c ... eval 'pcae doctor test-run && python -m pytest -n auto ...'
    The COMMAND field starts with /bin/zsh, not python. Must not be detected.
    """
    fake = _fake_ps(
        (
            "user   18901  0.9  0.0  435308624  2656  ??  Ss  11:49PM  0:00.00"
            " /bin/zsh -c source /path/snapshot.sh && eval"
            " 'pcae doctor test-run && python -m pytest -n auto -q 2>&1'"
        )
    )
    with _patch_ps(fake):
        result = _detect_active_pytest_processes()
    assert result == [], "shell process wrapping pytest invocation must not be detected"


# ── Integration tests via CLI main() ──


def test_doctor_test_run_clear_json(capsys):
    """When no active xdist run, JSON output has clear_to_run=true."""
    fake = _fake_ps("user 9 0.0 0.0 999 99 ? S 00:00 0:00 bash")
    with _patch_ps(fake):
        exit_code = main(["doctor", "test-run", "--json"])

    out = json.loads(capsys.readouterr().out)
    assert out["clear_to_run"] is True
    assert out["active_pytest_process_count"] == 0
    assert out["check"] == "test_run_preflight"
    assert exit_code == 0


def test_doctor_test_run_busy_json(capsys):
    """When xdist run active, JSON output has clear_to_run=false."""
    fake = _fake_ps(
        "user 1234 99.0 5.0 999999 99999 ? R 10:00 5:00 python -m pytest -n auto"
    )
    with _patch_ps(fake):
        exit_code = main(["doctor", "test-run", "--json"])

    out = json.loads(capsys.readouterr().out)
    assert out["clear_to_run"] is False
    assert out["active_pytest_process_count"] >= 1
    assert exit_code == 1


def test_doctor_test_run_clear_text(capsys):
    """Human-readable output when clear."""
    fake = _fake_ps("user 9 0.0 0.0 999 99 ? S 00:00 0:00 bash")
    with _patch_ps(fake):
        main(["doctor", "test-run"])

    out = capsys.readouterr().out
    assert "clear to run" in out.lower()


def test_doctor_test_run_busy_text(capsys):
    """Human-readable output when busy warns the operator."""
    fake = _fake_ps(
        "user 1234 99.0 5.0 999999 99999 ? R 10:00 5:00 python -m pytest -n auto"
    )
    with _patch_ps(fake):
        main(["doctor", "test-run"])

    out = capsys.readouterr().out
    assert "not clear" in out.lower() or "not_clear" in out.lower() or "NOT clear" in out


def test_doctor_test_run_does_not_mutate(tmp_path, monkeypatch, capsys):
    """The command must not write files, stage, commit, or push."""
    import os

    monkeypatch.chdir(tmp_path)
    fake = _fake_ps("user 9 0.0 0.0 999 99 ? S 00:00 0:00 bash")
    files_before = set(str(p) for p in tmp_path.rglob("*"))

    with _patch_ps(fake):
        main(["doctor", "test-run", "--json"])

    files_after = set(str(p) for p in tmp_path.rglob("*"))
    capsys.readouterr()
    assert files_after == files_before, "doctor test-run must not write any files"


def test_doctor_test_run_no_backend_invocation(capsys):
    """JSON output must confirm no backend invocation, execution, or mutation."""
    fake = _fake_ps("user 9 0.0 0.0 999 99 ? S 00:00 0:00 bash")
    with _patch_ps(fake):
        main(["doctor", "test-run", "--json"])

    out = json.loads(capsys.readouterr().out)
    # These fields must NOT appear as true
    assert out.get("backend_invocation_performed", False) is False
    assert out.get("execution_authorized", False) is False
    assert out.get("repo_mutation_performed", False) is False


def test_doctor_test_run_stale_ps_error_handled(capsys):
    """If ps raises an exception, the command handles it gracefully (conservative: reports clear)."""
    import subprocess as _sp_mod

    with patch.object(_sp_mod, "run", side_effect=Exception("ps unavailable")):
        exit_code = main(["doctor", "test-run", "--json"])

    out = json.loads(capsys.readouterr().out)
    # Conservative: when ps fails, assume clear (can't detect active processes)
    assert "clear_to_run" in out
    assert exit_code == 0
