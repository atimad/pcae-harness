"""Phase 149O.20L.7O.2Z -- Post-v0.3.1 Release Candidate Final Verification.

Fresh tests for the one bounded repair this phase makes: 2Y's
malformed-agent-lock fail-closed handling covered invalid JSON, but not
well-formed JSON that decodes to a non-dict value (array, string, number,
boolean, null). Independently discovered during this phase's release
verification: such a lock file crashed both `pcae intake from-files`
(via `derive_producer_provenance`) and `pcae session bootstrap` (via
`acquire_agent_lock_idempotent`) with an uncaught `AttributeError`,
because `read_agent_lock` does not raise for valid-but-wrong-type JSON --
the crash occurred one line later, at `AgentLock.agent_id`, outside
2Y's original try/except.

Does not reuse 2Y's own test functions.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.core import agent as agent_module
from pcae.core import intake
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


def _git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "2z@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "2Z"], cwd=path, check=True)
    (path / "seed.txt").write_text("seed\n")
    subprocess.run(["git", "add", "seed.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=path, check=True)


def _root(tmp_path, name="repo") -> HarnessPath:
    d = tmp_path / name
    d.mkdir()
    _git_repo(d)
    return HarnessPath(d)


def _task(root: HarnessPath, allowed=("app/allowed/**",)) -> str:
    contract = create_task_contract(
        root, "2Z release-candidate verification task",
        created_at=datetime(2026, 8, 24, 23, 0, tzinfo=timezone.utc),
        allowed_files=allowed,
    )
    return contract.task_id


WRONG_TYPE_LOCK_PAYLOADS = {
    "json_array": "[1, 2, 3]",
    "json_string": '"just a string"',
    "json_number": "42",
    "json_bool": "true",
    "json_null": "null",
}


# ---------------------------------------------------------------------------
# AgentLock.agent_id property: no longer crashes on non-dict decoded data
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("payload", WRONG_TYPE_LOCK_PAYLOADS.values(), ids=WRONG_TYPE_LOCK_PAYLOADS.keys())
def test_agent_lock_agent_id_property_safe_on_non_dict_data(payload):
    data = json.loads(payload)
    lock = agent_module.AgentLock(relative_path=agent_module.AGENT_LOCK_RELATIVE_PATH, data=data)
    assert lock.agent_id == ""


def test_agent_lock_agent_id_property_unchanged_for_well_formed_dict():
    lock = agent_module.AgentLock(
        relative_path=agent_module.AGENT_LOCK_RELATIVE_PATH,
        data={"agent_id": "claude-local"},
    )
    assert lock.agent_id == "claude-local"


# ---------------------------------------------------------------------------
# derive_producer_provenance: wrong-type lock now rejected cleanly
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("payload", WRONG_TYPE_LOCK_PAYLOADS.values(), ids=WRONG_TYPE_LOCK_PAYLOADS.keys())
def test_derive_producer_provenance_rejects_wrong_type_lock_cleanly(tmp_path, payload):
    root = _root(tmp_path)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(payload)

    producer, errors = intake.derive_producer_provenance(root, None)
    assert producer is None
    assert len(errors) == 1
    assert errors[0].startswith("malformed_agent_lock:")


def test_wrong_type_lock_does_not_silently_accept_explicit_producer(tmp_path):
    """Same non-broadening requirement 2Y established for invalid JSON must
    hold for valid-but-wrong-type JSON too: reject outright, do not fall
    through to the no-lock candidate-sourced path."""
    root = _root(tmp_path)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("[1, 2, 3]")

    producer, errors = intake.derive_producer_provenance(root, "explicit-producer")
    assert producer is None
    assert errors[0].startswith("malformed_agent_lock:")


def test_cli_intake_from_files_no_traceback_on_wrong_type_lock(tmp_path, monkeypatch, capsys):
    """End-to-end CLI-level regression: this used to crash with a raw
    Python AttributeError traceback; it must now print a clean rejection."""
    from pcae.cli import main
    from pcae.commands.init import init_harness

    root_dir = tmp_path / "cliroot"
    root_dir.mkdir()
    _git_repo(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    task_id = _task(root)
    lock_path = root_dir / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("[1, 2, 3]")
    content_file = root_dir / "content.txt"
    content_file.write_text("hi\n")
    monkeypatch.chdir(root_dir)

    exit_code = main([
        "intake", "from-files",
        "--task-id", task_id,
        "--candidate-id", "cli-cand-1",
        "--file", f"app/allowed/x.txt:create:{content_file}",
        "--summary", "s",
        "--json",
    ])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "Traceback" not in out
    result = json.loads(out)
    assert result["accepted"] is False
    assert any(e.startswith("malformed_agent_lock:") for e in result["rejection_reasons"])


# ---------------------------------------------------------------------------
# pcae session bootstrap: wrong-type lock no longer crashes with a traceback
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("payload", WRONG_TYPE_LOCK_PAYLOADS.values(), ids=WRONG_TYPE_LOCK_PAYLOADS.keys())
def test_acquire_agent_lock_idempotent_no_crash_on_wrong_type_lock(tmp_path, payload):
    root = _root(tmp_path)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(payload)

    with pytest.raises(ValueError, match="Agent lock already held"):
        agent_module.acquire_agent_lock_idempotent(root, "claude-local")


def test_cli_session_bootstrap_no_traceback_on_wrong_type_lock(tmp_path, monkeypatch, capsys):
    from pcae.cli import main
    from pcae.commands.init import init_harness

    root_dir = tmp_path / "cliroot2"
    root_dir.mkdir()
    _git_repo(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    lock_path = root_dir / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("null")
    monkeypatch.chdir(root_dir)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "Traceback" not in out
    assert "Agent lock already held" in out


# ---------------------------------------------------------------------------
# Regression guards: well-formed lock and no-lock paths unaffected
# ---------------------------------------------------------------------------

def test_repair_does_not_affect_well_formed_lock_intake_path(tmp_path):
    root = _root(tmp_path)
    agent_module.acquire_agent_lock(
        root, "codex-ox", acquired_at=datetime(2026, 8, 24, 23, 0, tzinfo=timezone.utc),
    )
    producer, errors = intake.derive_producer_provenance(root, None)
    assert errors == []
    assert producer == {"kind": "codex-ox", "source": "agent_lock"}


def test_repair_does_not_affect_no_lock_path(tmp_path):
    root = _root(tmp_path)
    producer, errors = intake.derive_producer_provenance(root, "external-tool-xyz")
    assert errors == []
    assert producer == {"kind": "external-tool-xyz", "source": "candidate"}


def test_repair_does_not_affect_well_formed_lock_bootstrap_idempotent(tmp_path):
    root = _root(tmp_path)
    result1 = agent_module.acquire_agent_lock_idempotent(root, "claude-local")
    assert result1.already_held is False
    result2 = agent_module.acquire_agent_lock_idempotent(root, "claude-local")
    assert result2.already_held is True
