from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.agent import acquire_agent_lock, build_agent_status
from pcae.core.paths import HarnessPath
from pcae.core.provenance import read_provenance_history
from pcae.core.tasks import create_task_contract


def test_agent_acquire_creates_lock(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "acquire", "--agent-id", "agent-a"])

    output = capsys.readouterr().out
    lock_path = tmp_path / ".pcae" / "agent-lock.json"
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "Agent lock acquired by agent-a." in output
    assert data["agent_id"] == "agent-a"
    assert data["git_branch"] in {"main", "master"}
    assert data["active_task"] == {
        "id": "20260525-0800-agent-task",
        "title": "Agent task",
    }


def test_agent_duplicate_acquire_fails(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "agent-a")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "acquire", "--agent-id", "agent-b"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Agent lock already held by agent-a." in output


def test_agent_release_wrong_agent_fails(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "agent-a")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "release", "--agent-id", "agent-b"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Agent lock is held by agent-a; agent-b cannot release it." in output
    assert (tmp_path / ".pcae" / "agent-lock.json").exists()


def test_agent_release_correct_agent_succeeds(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "agent-a")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "release", "--agent-id", "agent-a"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Released agent lock for agent-a." in output
    assert not (tmp_path / ".pcae" / "agent-lock.json").exists()


def test_agent_force_stale_releases_stale_different_agent(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    acquire_agent_lock(
        HarnessPath(tmp_path),
        "agent-a",
        acquired_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["agent", "release", "--agent-id", "agent-b", "--force-stale"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Force-released stale agent lock held by agent-a." in output
    assert not (tmp_path / ".pcae" / "agent-lock.json").exists()


def test_agent_force_stale_refuses_fresh_different_agent(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "agent-a")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["agent", "release", "--agent-id", "agent-b", "--force-stale"]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert (
        "Agent lock is not stale; agent-b cannot release lock held by agent-a."
        in output
    )
    assert (tmp_path / ".pcae" / "agent-lock.json").exists()


def test_agent_force_stale_with_no_lock_fails(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["agent", "release", "--agent-id", "agent-b", "--force-stale"]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No agent lock is currently held." in output


def test_agent_status_reports_available(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Agent lock: available" in output


def test_agent_status_reports_held(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "agent-a")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Agent lock: held" in output
    assert "Agent ID: agent-a" in output
    assert "Active task: 20260525-0800-agent-task - Agent task" in output


def test_agent_status_json_parses(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "agent-a")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["locked"] is True
    assert data["stale"] is False
    assert isinstance(data["age_seconds"], int)
    assert data["stale_after_seconds"] == 14400
    assert data["lock"]["agent_id"] == "agent-a"
    assert data["lock"]["active_task"]["title"] == "Agent task"


def test_agent_status_json_reports_available_metadata(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data == {
        "age_seconds": None,
        "lock": None,
        "locked": False,
        "stale": False,
        "stale_after_seconds": 14400,
    }


def test_agent_fresh_lock_is_not_stale(tmp_path: Path) -> None:
    init_agent_repo(tmp_path)
    acquired_at = datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc)
    acquire_agent_lock(HarnessPath(tmp_path), "agent-a", acquired_at=acquired_at)

    status = build_agent_status(
        HarnessPath(tmp_path),
        now=acquired_at + timedelta(hours=3, minutes=59),
    )

    assert status["locked"] is True
    assert status["stale"] is False
    assert status["age_seconds"] == 14340
    assert status["stale_after_seconds"] == 14400


def test_agent_old_lock_is_stale(tmp_path: Path) -> None:
    init_agent_repo(tmp_path)
    acquired_at = datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc)
    acquire_agent_lock(HarnessPath(tmp_path), "agent-a", acquired_at=acquired_at)

    status = build_agent_status(
        HarnessPath(tmp_path),
        now=acquired_at + timedelta(hours=4, seconds=1),
    )

    assert status["locked"] is True
    assert status["stale"] is True
    assert status["age_seconds"] == 14401


def test_agent_policy_threshold_overrides_default(tmp_path: Path) -> None:
    init_agent_repo(tmp_path)
    write_agent_policy_threshold(tmp_path, 60)
    acquired_at = datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc)
    acquire_agent_lock(HarnessPath(tmp_path), "agent-a", acquired_at=acquired_at)

    status = build_agent_status(
        HarnessPath(tmp_path),
        now=acquired_at + timedelta(seconds=61),
    )

    assert status["stale"] is True
    assert status["stale_after_seconds"] == 60


def test_agent_status_json_reports_policy_threshold(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    write_agent_policy_threshold(tmp_path, 60)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["stale_after_seconds"] == 60


def test_agent_status_fails_on_invalid_policy_threshold(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    policy_file = tmp_path / ".pcae" / "policy.toml"
    policy_file.write_text(
        policy_file.read_text(encoding="utf-8").replace(
            "stale_after_seconds = 14400",
            'stale_after_seconds = "soon"',
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "status"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert (
        "Invalid policy: agent.stale_after_seconds must be a positive integer."
        in output
    )


def test_agent_status_reports_stale_lock(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    acquire_agent_lock(
        HarnessPath(tmp_path),
        "agent-a",
        acquired_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Agent lock: stale" in output
    assert "Stale after seconds: 14400" in output


def test_agent_lock_is_ignored_by_git(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agent", "acquire", "--agent-id", "agent-a"])
    capsys.readouterr()

    ignored = subprocess.run(
        ["git", "check-ignore", ".pcae/agent-lock.json"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert exit_code == 0
    assert ignored.returncode == 0


# ---------------------------------------------------------------------------
# provenance recording for agent lifecycle
# ---------------------------------------------------------------------------


def test_agent_acquire_records_provenance_event(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["agent", "acquire", "--agent-id", "test-agent"])
    capsys.readouterr()

    history = read_provenance_history(HarnessPath(tmp_path))
    assert len(history.events) == 1
    event = history.events[0]
    assert event.event_type == "agent_acquired"
    assert "test-agent" in event.summary
    assert event.agent_id == "test-agent"
    assert event.git_branch is not None


def test_agent_acquire_failure_does_not_record_provenance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "first-agent")
    monkeypatch.chdir(tmp_path)

    main(["agent", "acquire", "--agent-id", "second-agent"])
    capsys.readouterr()

    history = read_provenance_history(HarnessPath(tmp_path))
    assert not any(e.event_type == "agent_acquired" for e in history.events)


def test_agent_release_records_provenance_event(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["agent", "acquire", "--agent-id", "test-agent"])
    capsys.readouterr()

    main(["agent", "release", "--agent-id", "test-agent"])
    capsys.readouterr()

    history = read_provenance_history(HarnessPath(tmp_path))
    release_events = [e for e in history.events if e.event_type == "agent_released"]
    assert len(release_events) == 1
    event = release_events[0]
    assert "test-agent" in event.summary
    assert event.agent_id == "test-agent"


def test_agent_release_failure_does_not_record_provenance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "other-agent")
    monkeypatch.chdir(tmp_path)

    main(["agent", "release", "--agent-id", "wrong-agent"])
    capsys.readouterr()

    history = read_provenance_history(HarnessPath(tmp_path))
    assert not any(e.event_type == "agent_released" for e in history.events)


def test_agent_acquire_and_release_both_recorded(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["agent", "acquire", "--agent-id", "lifecycle-agent"])
    main(["agent", "release", "--agent-id", "lifecycle-agent"])
    capsys.readouterr()

    history = read_provenance_history(HarnessPath(tmp_path))
    assert len(history.events) == 2
    assert history.events[0].event_type == "agent_acquired"
    assert history.events[1].event_type == "agent_released"


# ---------------------------------------------------------------------------
# acquire_agent_lock_idempotent
# ---------------------------------------------------------------------------


def test_acquire_idempotent_fresh_acquires_lock(tmp_path: Path) -> None:
    from pcae.core.agent import acquire_agent_lock_idempotent

    init_agent_repo(tmp_path)
    result = acquire_agent_lock_idempotent(HarnessPath(tmp_path), "claude-local")
    assert result.lock.agent_id == "claude-local"
    assert result.already_held is False


def test_acquire_idempotent_same_agent_returns_already_held(tmp_path: Path) -> None:
    from pcae.core.agent import acquire_agent_lock_idempotent

    init_agent_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "claude-local")
    result = acquire_agent_lock_idempotent(HarnessPath(tmp_path), "claude-local")
    assert result.lock.agent_id == "claude-local"
    assert result.already_held is True


def test_acquire_idempotent_different_agent_raises(tmp_path: Path) -> None:
    from pcae.core.agent import acquire_agent_lock_idempotent

    init_agent_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "other-agent")
    with pytest.raises(ValueError, match="Agent lock already held by other-agent"):
        acquire_agent_lock_idempotent(HarnessPath(tmp_path), "claude-local")


# ---------------------------------------------------------------------------
# pcae agents — multi-agent collaboration registry (Phase 37A)
# ---------------------------------------------------------------------------


def test_agents_human_output(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Multi-agent registry" in output
    assert "Agent count: 8" in output
    assert "claude-local" in output
    assert "codex-local" in output
    assert "pcae-native" in output
    assert "kimi-local" in output
    assert "deepseek-local" in output
    assert "gemini-local" in output
    assert "grok-local" in output
    assert "perplexity-local" in output
    assert "status: available" in output
    assert "status: declared" in output
    assert "Lifecycle summary:" in output
    assert "available=3" in output
    assert "declared=5" in output
    assert "Advisory:" in output


def test_agents_json_output(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_count"] == 8
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) == 8
    assert "advisory" in data

    ids = [entry["agent_id"] for entry in data["agents"]]
    assert "claude-local" in ids
    assert "codex-local" in ids
    assert "pcae-native" in ids
    assert "kimi-local" in ids
    assert "deepseek-local" in ids
    assert "gemini-local" in ids
    assert "grok-local" in ids
    assert "perplexity-local" in ids

    claude = next(e for e in data["agents"] if e["agent_id"] == "claude-local")
    assert claude["agent_type"] == "claude"
    assert claude["role"] == "documentation"
    assert claude["status"] == "available"
    assert isinstance(claude["capabilities"], list)
    assert len(claude["capabilities"]) > 0
    assert isinstance(claude["preferred_workloads"], list)
    assert len(claude["preferred_workloads"]) > 0


def test_agents_json_all_required_fields(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for entry in data["agents"]:
        for field in ("agent_id", "agent_type", "role", "status", "capabilities", "preferred_workloads"):
            assert field in entry, f"Missing field '{field}' in agent entry {entry['agent_id']}"


def test_agents_registry_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = list((tmp_path / ".pcae").iterdir()) if (tmp_path / ".pcae").exists() else []
    main(["agents"])
    capsys.readouterr()
    after = list((tmp_path / ".pcae").iterdir()) if (tmp_path / ".pcae").exists() else []

    assert set(p.name for p in before) == set(p.name for p in after)


def test_agents_new_agents_are_declared(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    declared_ids = {
        e["agent_id"] for e in data["agents"] if e["status"] == "declared"
    }
    assert "kimi-local" in declared_ids
    assert "deepseek-local" in declared_ids
    assert "gemini-local" in declared_ids
    assert "grok-local" in declared_ids
    assert "perplexity-local" in declared_ids


def test_agents_existing_agents_remain_available(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    available_ids = {
        e["agent_id"] for e in data["agents"] if e["status"] == "available"
    }
    assert "claude-local" in available_ids
    assert "codex-local" in available_ids
    assert "pcae-native" in available_ids


def test_agents_json_includes_lifecycle_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "lifecycle_summary" in data
    summary = data["lifecycle_summary"]
    assert summary["available"] == 3
    assert summary["declared"] == 5
    assert summary["configured"] == 0
    assert summary["active"] == 0


def test_agents_lifecycle_summary_counts_match_registry(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    summary = data["lifecycle_summary"]
    total = sum(summary.values())
    assert total == data["agent_count"]


def test_agent_entry_invalid_status_raises() -> None:
    from pcae.core.agent import AgentEntry

    with pytest.raises(ValueError, match="Invalid agent status"):
        AgentEntry(
            agent_id="test-agent",
            agent_type="test",
            role="testing",
            status="unknown_status",
            capabilities=(),
            preferred_workloads=(),
        )


def test_agent_entry_valid_statuses_accepted() -> None:
    from pcae.core.agent import VALID_AGENT_STATUSES, AgentEntry

    for status in VALID_AGENT_STATUSES:
        entry = AgentEntry(
            agent_id="test-agent",
            agent_type="test",
            role="testing",
            status=status,
            capabilities=(),
            preferred_workloads=(),
        )
        assert entry.status == status


# ---------------------------------------------------------------------------
# pcae agents show (Phase 37C)
# ---------------------------------------------------------------------------


def test_agents_show_available_agent(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "show", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "claude-local" in output
    assert "claude" in output
    assert "documentation" in output
    assert "available" in output
    assert "Capabilities:" in output
    assert "Preferred workloads:" in output


def test_agents_show_declared_agent(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "show", "kimi-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "kimi-local" in output
    assert "kimi" in output
    assert "declared" in output


def test_agents_show_unknown_agent_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "show", "no-such-agent"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Agent not found" in output
    assert "no-such-agent" in output


def test_agents_show_json(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "show", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_id"] == "claude-local"
    assert data["agent_type"] == "claude"
    assert data["role"] == "documentation"
    assert data["status"] == "available"
    assert isinstance(data["capabilities"], list)
    assert isinstance(data["preferred_workloads"], list)


def test_agents_show_declared_json(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "show", "deepseek-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_id"] == "deepseek-local"
    assert data["status"] == "declared"


def test_agents_show_all_new_declared_agents(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    for agent_id in ("kimi-local", "deepseek-local", "gemini-local", "grok-local", "perplexity-local"):
        exit_code = main(["agents", "show", agent_id])
        output = capsys.readouterr().out
        assert exit_code == 0, f"Expected exit 0 for {agent_id}"
        assert agent_id in output
        assert "declared" in output


# ---------------------------------------------------------------------------
# pcae agents validate (Phase 37C)
# ---------------------------------------------------------------------------


def test_agents_validate_passes_for_built_in_registry(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "validate"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Agent registry validation" in output
    assert "Validation status: valid" in output
    assert "Errors: none" in output
    assert "advisory" in output.lower()


def test_agents_validate_json_valid_registry(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["errors"] == []
    assert isinstance(data["warnings"], list)
    assert data["agent_count"] == 8
    assert "advisory" in data
    assert "Agent configuration validation is advisory" in data["advisory"]


def test_agents_validate_json_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for field in ("valid", "agent_count", "errors", "warnings", "advisory"):
        assert field in data, f"Missing field '{field}' in validate output"


def test_agents_validate_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["agents", "validate"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_validate_agent_registry_core(tmp_path: Path) -> None:
    from pcae.core.agent import validate_agent_registry

    result = validate_agent_registry()

    assert result.valid is True
    assert result.errors == ()
    assert result.agent_count == 8
    assert "advisory" in result.advisory.lower()


def test_validate_agent_registry_detects_invalid_status() -> None:
    from pcae.core.agent import (
        AgentEntry,
        AgentValidationResult,
        MULTI_AGENT_REGISTRY,
        AGENT_VALIDATION_ADVISORY,
    )

    bad = AgentEntry.__new__(AgentEntry)
    object.__setattr__(bad, "agent_id", "bad-agent")
    object.__setattr__(bad, "agent_type", "test")
    object.__setattr__(bad, "role", "testing")
    object.__setattr__(bad, "status", "nonexistent")
    object.__setattr__(bad, "capabilities", ())
    object.__setattr__(bad, "preferred_workloads", ())

    registry = MULTI_AGENT_REGISTRY + (bad,)

    errors: list[str] = []
    seen: set[str] = set()
    from pcae.core.agent import VALID_AGENT_STATUSES, AGENT_STATUS_AVAILABLE, AGENT_STATUS_ACTIVE
    for entry in registry:
        if entry.agent_id in seen:
            errors.append(f"Duplicate agent ID: '{entry.agent_id}'.")
        seen.add(entry.agent_id)
        if entry.status not in VALID_AGENT_STATUSES:
            errors.append(
                f"Agent '{entry.agent_id}' has invalid status '{entry.status}'."
            )
    assert any("nonexistent" in e for e in errors)


# ---------------------------------------------------------------------------
# pcae agents lifecycle (Phase 37D)
# ---------------------------------------------------------------------------


def test_agents_lifecycle_human_output(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "lifecycle"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Lifecycle summary" in output
    assert "Agent count: 8" in output
    assert "State distribution:" in output
    assert "active=0" in output
    assert "available=3" in output
    assert "configured=0" in output
    assert "declared=5" in output
    assert "Agents by lifecycle state:" in output
    assert "available (3):" in output
    assert "declared (5):" in output
    assert "claude-local" in output
    assert "codex-local" in output
    assert "pcae-native" in output
    assert "kimi-local" in output
    assert "Lifecycle progression guidance:" in output
    assert "Lifecycle reporting is advisory; no agent state is modified." in output


def test_agents_lifecycle_json_output(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "lifecycle", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "lifecycle_summary" in data
    assert "agents_by_state" in data
    assert "progression_guidance" in data
    assert "advisory" in data
    assert "validation" in data


def test_agents_lifecycle_json_summary_counts(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "lifecycle", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    summary = data["lifecycle_summary"]
    assert summary["available"] == 3
    assert summary["declared"] == 5
    assert summary["configured"] == 0
    assert summary["active"] == 0
    assert sum(summary.values()) == 8


def test_agents_lifecycle_json_agents_by_state(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "lifecycle", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    by_state = data["agents_by_state"]
    assert len(by_state["available"]) == 3
    assert len(by_state["declared"]) == 5
    assert by_state["configured"] == []
    assert by_state["active"] == []
    available_ids = {e["agent_id"] for e in by_state["available"]}
    assert available_ids == {"claude-local", "codex-local", "pcae-native"}
    declared_ids = {e["agent_id"] for e in by_state["declared"]}
    assert declared_ids == {
        "kimi-local", "deepseek-local", "gemini-local", "grok-local", "perplexity-local"
    }


def test_agents_lifecycle_json_progression_guidance(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "lifecycle", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    guidance = data["progression_guidance"]
    for state in ("declared", "configured", "available", "active"):
        assert state in guidance
        assert isinstance(guidance[state], str)
        assert len(guidance[state]) > 0


def test_agents_lifecycle_json_advisory(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "lifecycle", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no agent state is modified" in data["advisory"]


def test_agents_lifecycle_json_validation_valid(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "lifecycle", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["validation"]["valid"] is True
    assert data["validation"]["errors"] == []


def test_agents_lifecycle_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["agents", "lifecycle"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_agents_lifecycle_human_shows_progression_guidance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "lifecycle"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "declared:" in output
    assert "configured:" in output
    assert "available:" in output
    assert "active:" in output


def test_agents_lifecycle_core_build_lifecycle_report() -> None:
    from pcae.core.agent import build_lifecycle_report

    report = build_lifecycle_report()

    assert report.lifecycle_summary["available"] == 3
    assert report.lifecycle_summary["declared"] == 5
    assert report.lifecycle_summary["configured"] == 0
    assert report.lifecycle_summary["active"] == 0
    assert report.validation.valid is True
    assert report.validation.errors == ()
    assert "no agent state is modified" in report.advisory


def test_agents_lifecycle_validation_detects_duplicate_ids() -> None:
    from pcae.core.agent import (
        AgentEntry,
        AGENT_STATUS_DECLARED,
        _validate_lifecycle,
        MULTI_AGENT_REGISTRY,
    )

    duplicate = AgentEntry(
        agent_id="claude-local",
        agent_type="claude",
        role="documentation",
        status=AGENT_STATUS_DECLARED,
        capabilities=(),
        preferred_workloads=(),
    )
    registry = MULTI_AGENT_REGISTRY + (duplicate,)
    result = _validate_lifecycle(registry)

    assert result.valid is False
    assert any("Duplicate agent ID" in e and "claude-local" in e for e in result.errors)


def test_agents_lifecycle_validation_detects_inconsistent_metadata() -> None:
    from pcae.core.agent import (
        AgentEntry,
        AGENT_STATUS_AVAILABLE,
        _validate_lifecycle,
    )

    bad = AgentEntry(
        agent_id="incomplete-agent",
        agent_type="test",
        role="testing",
        status=AGENT_STATUS_AVAILABLE,
        capabilities=(),
        preferred_workloads=(),
    )
    result = _validate_lifecycle((bad,))

    assert result.valid is False
    assert any("inconsistent lifecycle metadata" in e for e in result.errors)


def test_agents_lifecycle_all_states_present_in_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "lifecycle"])

    output = capsys.readouterr().out
    assert exit_code == 0
    for state in ("active", "available", "configured", "declared"):
        assert state in output


def init_agent_repo(root: Path) -> None:
    init_git_repo(root)
    init_harness(HarnessPath(root))
    write_pcae_runtime_ignore(root)
    create_task_contract(
        HarnessPath(root),
        "Agent task",
        created_at=datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc),
    )


def init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def write_pcae_runtime_ignore(root: Path) -> None:
    target = root / ".pcae" / ".gitignore"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "session.json\narchitecture-history.json\nagent-lock.json\n",
        encoding="utf-8",
    )


def write_agent_policy_threshold(root: Path, threshold: int) -> None:
    policy_file = root / ".pcae" / "policy.toml"
    policy_file.write_text(
        policy_file.read_text(encoding="utf-8").replace(
            "stale_after_seconds = 14400",
            f"stale_after_seconds = {threshold}",
        ),
        encoding="utf-8",
    )
