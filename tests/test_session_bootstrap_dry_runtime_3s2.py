"""
Phase 149O.20L.7O.3S.2 — CLI-surface tests for
`pcae session bootstrap --compact --dry-runtime --runtime-target <id>`.

Proves the CLI/command layer is thin (parsing + rendering only, no adapter
business logic -- RPAC construction lives in
`pcae.core.runtime_dry_consumption`), that failure modes are explicit and
non-fallback, and that the ordinary `--compact` prompt-only flow is
unchanged when `--dry-runtime` is absent (Section 33/36/37).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pcae.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]
_STORE_ROOT = REPO_ROOT / ".pcae" / "runtime-invocations"


@pytest.fixture(autouse=True)
def _clean_store():
    """Every test in this file runs against the real repo cwd (the CLI has
    no root-injection seam); this fixture guarantees no test leaves an
    evidence artifact behind in the tracked working tree."""
    yield
    if _STORE_ROOT.exists():
        shutil.rmtree(_STORE_ROOT)


def test_missing_runtime_target_fails_closed(capsys):
    exit_code = main(["session", "bootstrap", "--compact", "--dry-runtime"])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "--runtime-target" in out
    assert "No default or fallback target exists" in out


def test_missing_runtime_target_json_mode(capsys):
    exit_code = main(["session", "bootstrap", "--compact", "--dry-runtime", "--json"])
    out = capsys.readouterr().out
    assert exit_code == 1
    payload = json.loads(out)
    assert payload["dry_runtime_error"] == "missing_runtime_target"


def test_unknown_runtime_target_fails_closed_no_fallback(capsys):
    exit_code = main([
        "session", "bootstrap", "--compact", "--dry-runtime",
        "--runtime-target", "not-a-real-target",
    ])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "No fallback was taken" in out
    # Never silently fell back into ordinary prompt-only output.
    assert "PCAE RPAC-001 mock/dry" not in out


def test_successful_dry_runtime_json_output_is_unambiguous(capsys):
    exit_code = main([
        "session", "bootstrap", "--compact", "--agent-id", "codex-ox",
        "--dry-runtime", "--runtime-target", "mock-dry.no-change.v1", "--json",
    ])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert exit_code == 0
    assert payload["dry_runtime"] is True
    assert payload["simulation_only"] is True
    assert payload["external_runtime_invoked"] is False
    assert payload["execution_availability"] == "unavailable"
    assert payload["agent_id"] == "codex-ox"
    assert payload["requested_runtime_target"] == "mock-dry.no-change.v1"
    assert "openrouter" not in json.dumps(payload).lower()


def test_successful_dry_runtime_text_output_states_simulation_only(capsys):
    exit_code = main([
        "session", "bootstrap", "--compact", "--dry-runtime",
        "--runtime-target", "mock-dry.no-change.v1",
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "SIMULATION ONLY" in out
    assert "External runtime invoked: no" in out
    assert "Execution availability: unavailable" in out
    assert "executed" not in out.lower().replace("execution availability", "")
    assert "ran agent" not in out.lower()


def test_ordinary_compact_bootstrap_unchanged_without_dry_flag(capsys):
    """The normal, pre-existing `--compact` path (no --dry-runtime) must
    produce exactly its historical prompt-only output shape -- no RPAC
    fields, no dispatch, no store artifact."""
    exit_code = main(["session", "bootstrap", "--compact", "--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert exit_code == 0
    assert "dry_runtime" not in payload
    assert "bootstrap_prompt" in payload
    assert not _STORE_ROOT.exists()


def test_dry_runtime_flag_alone_without_compact_is_a_no_op_lock_bootstrap(capsys):
    """--dry-runtime is only consulted inside the --compact branch
    (Section 33/36): without --compact, ordinary lock-acquiring bootstrap
    runs, requiring --agent-id, completely unaffected by --dry-runtime."""
    exit_code = main(["session", "bootstrap", "--dry-runtime"])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "--agent-id is required" in out
