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
    assert "available=4" in output
    assert "declared=4" in output
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
    assert "kimi-local" not in declared_ids
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
    assert summary["available"] == 4
    assert summary["declared"] == 4
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


def test_agents_show_available_kimi(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "show", "kimi-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "kimi-local" in output
    assert "kimi" in output
    assert "available" in output


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

    for agent_id in ("deepseek-local", "gemini-local", "grok-local", "perplexity-local"):
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
# pcae collaboration handoffs (Phase 37G)
# ---------------------------------------------------------------------------


def _write_provenance_events(root: Path, events: list[dict]) -> None:
    history_path = root / ".pcae" / "provenance-history.json"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(
        json.dumps(events, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _make_provenance_event(
    event_type: str,
    agent_id: str | None = None,
    summary: str = "",
    timestamp: str = "2026-05-01T10:00:00+00:00",
    active_task: dict | None = None,
) -> dict:
    return {
        "active_task": active_task,
        "agent_id": agent_id,
        "event_type": event_type,
        "git_branch": "main",
        "summary": summary,
        "timestamp": timestamp,
    }


def test_collaboration_handoffs_empty_history(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "handoffs"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Handoff history" in output
    assert "Handoff count: 0" in output
    assert "No handoff records found." in output
    assert "advisory" in output.lower()


def test_collaboration_handoffs_empty_history_json(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "handoffs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["handoff_count"] == 0
    assert data["handoffs"] == []
    assert "advisory" in data
    assert "no handoff state is modified" in data["advisory"]


def test_collaboration_handoffs_single_record(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    task = {"id": "task-001", "title": "Test task"}
    _write_provenance_events(tmp_path, [
        _make_provenance_event("phase_completed", "codex-local", "Phase X done",
                               "2026-05-01T09:00:00+00:00", task),
        _make_provenance_event("agent_released", "codex-local", "Released",
                               "2026-05-01T09:01:00+00:00", task),
        _make_provenance_event("agent_acquired", "claude-local", "Acquired",
                               "2026-05-01T09:01:01+00:00", task),
    ])

    exit_code = main(["collaboration", "handoffs"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Handoff count: 1" in output
    assert "codex-local" in output
    assert "claude-local" in output
    assert "Continuity verified: yes" in output


def test_collaboration_handoffs_json_single_record(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    task = {"id": "task-001", "title": "Test task"}
    _write_provenance_events(tmp_path, [
        _make_provenance_event("phase_completed", "codex-local", "Phase X done",
                               "2026-05-01T09:00:00+00:00", task),
        _make_provenance_event("agent_released", "codex-local", "Released",
                               "2026-05-01T09:01:00+00:00", task),
        _make_provenance_event("agent_acquired", "claude-local", "Acquired",
                               "2026-05-01T09:01:01+00:00", task),
    ])

    exit_code = main(["collaboration", "handoffs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["handoff_count"] == 1
    h = data["handoffs"][0]
    assert h["source_agent"] == "codex-local"
    assert h["target_agent"] == "claude-local"
    assert h["continuity_verified"] is True
    assert h["summary"] == "Phase X done"
    assert h["phase"] == "task-001"
    assert h["active_task"] == task


def test_collaboration_handoffs_json_all_fields(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_provenance_events(tmp_path, [
        _make_provenance_event("agent_released", "agent-a", "R", "2026-05-01T09:00:00+00:00"),
        _make_provenance_event("agent_acquired", "agent-b", "A", "2026-05-01T09:00:01+00:00"),
    ])

    exit_code = main(["collaboration", "handoffs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    h = data["handoffs"][0]
    for field in (
        "source_agent", "target_agent", "timestamp", "phase",
        "active_task", "continuity_verified", "architecture_memory_present",
        "summary", "warnings",
    ):
        assert field in h, f"Missing field '{field}' in handoff record"


def test_collaboration_handoffs_most_recent_first(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_provenance_events(tmp_path, [
        _make_provenance_event("agent_released", "agent-a", "R1", "2026-05-01T08:00:00+00:00"),
        _make_provenance_event("agent_acquired", "agent-b", "A1", "2026-05-01T08:00:01+00:00"),
        _make_provenance_event("agent_released", "agent-b", "R2", "2026-05-02T08:00:00+00:00"),
        _make_provenance_event("agent_acquired", "agent-c", "A2", "2026-05-02T08:00:01+00:00"),
    ])

    exit_code = main(["collaboration", "handoffs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["handoff_count"] == 2
    assert data["handoffs"][0]["timestamp"] == "2026-05-02T08:00:00+00:00"
    assert data["handoffs"][1]["timestamp"] == "2026-05-01T08:00:00+00:00"


def test_collaboration_handoffs_continuity_verified_direct(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_provenance_events(tmp_path, [
        _make_provenance_event("agent_released", "a", "R", "2026-05-01T09:00:00+00:00"),
        _make_provenance_event("agent_acquired", "b", "A", "2026-05-01T09:00:01+00:00"),
    ])

    exit_code = main(["collaboration", "handoffs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["handoffs"][0]["continuity_verified"] is True


def test_collaboration_handoffs_continuity_not_verified_with_gap(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_provenance_events(tmp_path, [
        _make_provenance_event("agent_released", "a", "R", "2026-05-01T09:00:00+00:00"),
        _make_provenance_event("some_other_event", None, "X", "2026-05-01T09:00:00+00:00"),
        _make_provenance_event("agent_acquired", "b", "A", "2026-05-01T09:00:01+00:00"),
    ])

    exit_code = main(["collaboration", "handoffs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["handoffs"][0]["continuity_verified"] is False


def test_collaboration_handoffs_architecture_memory_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    arch_path = tmp_path / ".pcae" / "architecture-history.json"
    arch_path.write_text(
        json.dumps([{"id": "ADR-0001", "title": "Test ADR"}]) + "\n",
        encoding="utf-8",
    )
    _write_provenance_events(tmp_path, [
        _make_provenance_event("agent_released", "a", "R", "2026-05-01T09:00:00+00:00"),
        _make_provenance_event("agent_acquired", "b", "A", "2026-05-01T09:00:01+00:00"),
    ])

    exit_code = main(["collaboration", "handoffs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["handoffs"][0]["architecture_memory_present"] is True


def test_collaboration_handoffs_no_architecture_memory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_provenance_events(tmp_path, [
        _make_provenance_event("agent_released", "a", "R", "2026-05-01T09:00:00+00:00"),
        _make_provenance_event("agent_acquired", "b", "A", "2026-05-01T09:00:01+00:00"),
    ])

    exit_code = main(["collaboration", "handoffs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["handoffs"][0]["architecture_memory_present"] is False


def test_collaboration_handoffs_malformed_warns_missing_source(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_provenance_events(tmp_path, [
        _make_provenance_event("agent_released", None, "R", "2026-05-01T09:00:00+00:00"),
        _make_provenance_event("agent_acquired", "b", "A", "2026-05-01T09:00:01+00:00"),
    ])

    exit_code = main(["collaboration", "handoffs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert any("Source agent ID missing" in w for w in data["handoffs"][0]["warnings"])


def test_collaboration_handoffs_release_without_acquire_ignored(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_provenance_events(tmp_path, [
        _make_provenance_event("agent_released", "a", "R", "2026-05-01T09:00:00+00:00"),
    ])

    exit_code = main(["collaboration", "handoffs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["handoff_count"] == 0


def test_collaboration_handoffs_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["collaboration", "handoffs"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_collaboration_handoffs_human_shows_continuity(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_provenance_events(tmp_path, [
        _make_provenance_event("agent_released", "codex-local", "R", "2026-05-01T09:00:00+00:00"),
        _make_provenance_event("agent_acquired", "claude-local", "A", "2026-05-01T09:00:01+00:00"),
    ])

    exit_code = main(["collaboration", "handoffs"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Continuity verified:" in output
    assert "Architecture memory:" in output


def test_collaboration_handoffs_core_build_handoff_history(tmp_path: Path) -> None:
    from pcae.core.provenance import build_handoff_history
    from pcae.core.paths import HarnessPath

    init_agent_repo(tmp_path)
    task = {"id": "task-abc", "title": "Task ABC"}
    _write_provenance_events(tmp_path, [
        _make_provenance_event("phase_completed", "codex-local", "Done",
                               "2026-05-01T09:00:00+00:00", task),
        _make_provenance_event("agent_released", "codex-local", "R",
                               "2026-05-01T09:01:00+00:00", task),
        _make_provenance_event("agent_acquired", "claude-local", "A",
                               "2026-05-01T09:01:01+00:00", task),
    ])

    history = build_handoff_history(HarnessPath(tmp_path))

    assert history.handoff_count == 1
    h = history.handoffs[0]
    assert h.source_agent == "codex-local"
    assert h.target_agent == "claude-local"
    assert h.continuity_verified is True
    assert h.summary == "Done"
    assert h.phase == "task-abc"
    assert "no handoff state is modified" in history.advisory


# ---------------------------------------------------------------------------
# pcae agents runtime-discover (Phase 38A)
# ---------------------------------------------------------------------------


def _mock_none_find(name: str) -> None:
    return None


def _mock_none_probe(cmd: list, timeout: int = 5) -> None:
    return None


def test_agents_runtime_discover_human_output(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "runtime-discover"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Runtime discovery" in output
    assert "codex-local" in output
    assert "claude-local" in output
    assert "kimi-local" in output
    assert "Agents checked: 3" in output
    assert "advisory" in output.lower()


def test_agents_runtime_discover_json_structure(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "agents" in data
    assert "discovery_summary" in data
    assert "advisory" in data


def test_agents_runtime_discover_three_agents(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    agent_ids = [a["agent_id"] for a in data["agents"]]
    assert "codex-local" in agent_ids
    assert "claude-local" in agent_ids
    assert "kimi-local" in agent_ids
    assert len(agent_ids) == 3


def test_agents_runtime_discover_all_not_installed(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for agent in data["agents"]:
        assert agent["capabilities"]["installed"] is False
    summary = data["discovery_summary"]
    assert summary["agents_installed"] == 0
    assert summary["agents_not_installed"] == 3
    assert summary["agents_checked"] == 3


def test_agents_runtime_discover_installed_agent(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "claude" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "claude":
            return "usage: claude [-p prompt] [--json] [--mcp] [--hooks] [remote]"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "1.0.0" if exe == "claude" else None)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    claude = next(a for a in data["agents"] if a["agent_id"] == "claude-local")
    caps = claude["capabilities"]
    assert caps["installed"] is True
    assert caps["executable_path"] == "/usr/bin/claude"
    assert caps["version"] == "1.0.0"
    assert caps["interactive_supported"] == "yes"
    assert data["discovery_summary"]["agents_installed"] == 1


def test_agents_runtime_discover_capabilities_all_fields(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for agent in data["agents"]:
        caps = agent["capabilities"]
        for field in (
            "installed", "executable_path", "version",
            "interactive_supported", "non_interactive_supported",
            "stdin_prompt_supported", "prompt_file_supported",
            "structured_output_supported", "mcp_supported",
            "hooks_supported", "subagents_supported", "remote_supported",
            "known_limitations",
        ):
            assert field in caps, f"Missing '{field}' in '{agent['agent_id']}'"


def test_agents_runtime_discover_not_installed_caps_unknown(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for agent in data["agents"]:
        caps = agent["capabilities"]
        assert caps["installed"] is False
        for cap in (
            "interactive_supported", "non_interactive_supported",
            "stdin_prompt_supported", "prompt_file_supported",
            "structured_output_supported", "mcp_supported",
            "hooks_supported", "subagents_supported", "remote_supported",
        ):
            assert caps[cap] == "unknown", (
                f"Expected 'unknown' for '{cap}' of not-installed '{agent['agent_id']}', "
                f"got '{caps[cap]}'"
            )


def test_agents_runtime_discover_detects_non_interactive(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "claude" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "claude":
            return "usage: claude -p <prompt> run in non-interactive mode"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: None)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    claude = next(a for a in data["agents"] if a["agent_id"] == "claude-local")
    assert claude["capabilities"]["non_interactive_supported"] == "yes"


def test_agents_runtime_discover_detects_mcp(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        return "codex mcp-server start options" if cmd[0] == "codex" else None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: None)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    codex = next(a for a in data["agents"] if a["agent_id"] == "codex-local")
    assert codex["capabilities"]["mcp_supported"] == "yes"


def test_agents_runtime_discover_conservative_unknown_not_no(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "claude" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "claude":
            return "usage: claude [options] basic help with no special features listed"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: None)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    claude = next(a for a in data["agents"] if a["agent_id"] == "claude-local")
    caps = claude["capabilities"]
    for cap in ("mcp_supported", "hooks_supported", "subagents_supported", "remote_supported"):
        assert caps[cap] == "unknown", f"Expected 'unknown' (not 'no') for '{cap}', got '{caps[cap]}'"


def test_agents_runtime_discover_advisory(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "user remains authoritative" in data["advisory"]


def test_agents_runtime_discover_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["agents", "runtime-discover"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_agents_runtime_discover_summary_fields(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    summary = data["discovery_summary"]
    assert summary["agents_checked"] == 3
    assert "agents_installed" in summary
    assert "agents_not_installed" in summary
    assert summary["agents_installed"] + summary["agents_not_installed"] == summary["agents_checked"]


def test_agents_runtime_discover_installed_interactive_yes(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(agent_mod, "_find_executable", lambda name: f"/usr/bin/{name}" if name == "codex" else None)
    monkeypatch.setattr(agent_mod, "_run_probe", lambda cmd, timeout=5: "codex usage" if cmd[0] == "codex" else None)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: None)

    exit_code = main(["agents", "runtime-discover", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    codex = next(a for a in data["agents"] if a["agent_id"] == "codex-local")
    assert codex["capabilities"]["interactive_supported"] == "yes"


def test_agents_runtime_discover_core_build(tmp_path: Path, monkeypatch) -> None:
    import pcae.core.agent as agent_mod
    from pcae.core.agent import build_runtime_discovery

    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    result = build_runtime_discovery()

    assert result.advisory == "Runtime discovery is advisory; the user remains authoritative."
    assert len(result.agents) == 3
    for entry in result.agents:
        assert entry.capabilities.installed is False


# ---------------------------------------------------------------------------
# pcae collaboration reviews (Phase 37H)
# ---------------------------------------------------------------------------


def test_collaboration_reviews_human_output(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Review workflows" in output
    assert "Review workflow count: 3" in output
    assert "implementation_review" in output
    assert "documentation_review" in output
    assert "architecture_review" in output
    assert "Review statuses:" in output
    assert "pending" in output
    assert "reviewed" in output
    assert "validated" in output
    assert "rejected" in output
    assert "advisory" in output.lower()


def test_collaboration_reviews_json_output(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "review_workflows" in data
    assert "review_statuses" in data
    assert "advisory" in data


def test_collaboration_reviews_json_three_workflows(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    names = [w["workflow_name"] for w in data["review_workflows"]]
    assert "implementation_review" in names
    assert "documentation_review" in names
    assert "architecture_review" in names
    assert len(names) == 3


def test_collaboration_reviews_json_four_statuses(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    statuses = data["review_statuses"]
    assert "pending" in statuses
    assert "reviewed" in statuses
    assert "validated" in statuses
    assert "rejected" in statuses
    assert len(statuses) == 4


def test_collaboration_reviews_implementation_steps(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    impl = next(w for w in data["review_workflows"] if w["workflow_name"] == "implementation_review")
    step_names = [s["step_name"] for s in impl["steps"]]
    assert step_names == ["implementer", "reviewer", "validator"]


def test_collaboration_reviews_documentation_steps(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    doc = next(w for w in data["review_workflows"] if w["workflow_name"] == "documentation_review")
    step_names = [s["step_name"] for s in doc["steps"]]
    assert step_names == ["author", "reviewer", "validator"]


def test_collaboration_reviews_architecture_steps(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    arch = next(w for w in data["review_workflows"] if w["workflow_name"] == "architecture_review")
    step_names = [s["step_name"] for s in arch["steps"]]
    assert step_names == ["proposer", "reviewer", "validator"]


def test_collaboration_reviews_step_fields_present(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for workflow in data["review_workflows"]:
        for step in workflow["steps"]:
            for field in (
                "step_name", "recommended_agent_role", "purpose",
                "required_lifecycle_status", "review_status",
            ):
                assert field in step, (
                    f"Missing '{field}' in step '{step.get('step_name')}' "
                    f"of '{workflow['workflow_name']}'"
                )


def test_collaboration_reviews_default_status_is_pending(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for workflow in data["review_workflows"]:
        for step in workflow["steps"]:
            assert step["review_status"] == "pending", (
                f"Expected 'pending' in step '{step['step_name']}' "
                f"of '{workflow['workflow_name']}', got '{step['review_status']}'"
            )


def test_collaboration_reviews_steps_are_ordered(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    impl = next(w for w in data["review_workflows"] if w["workflow_name"] == "implementation_review")
    assert impl["steps"][0]["step_name"] == "implementer"
    assert impl["steps"][-1]["step_name"] == "validator"


def test_collaboration_reviews_advisory_semantics(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no agents are executed" in data["advisory"]
    assert "assigned automatically" in data["advisory"]


def test_collaboration_reviews_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["collaboration", "reviews"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_collaboration_reviews_human_shows_review_status(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "reviews"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "review: pending" in output
    assert "Purpose:" in output
    assert "min status:" in output


def test_collaboration_reviews_core_build(tmp_path: Path, monkeypatch, capsys) -> None:
    from pcae.core.agent import REVIEW_WORKFLOWS, build_review_workflows

    data = build_review_workflows()
    assert len(data["review_workflows"]) == 3
    assert len(data["review_statuses"]) == 4
    assert "no agents are executed" in data["advisory"]
    names = [w["workflow_name"] for w in data["review_workflows"]]
    assert names == ["implementation_review", "documentation_review", "architecture_review"]


def test_collaboration_reviews_each_has_three_steps() -> None:
    from pcae.core.agent import REVIEW_WORKFLOWS

    for workflow in REVIEW_WORKFLOWS:
        assert len(workflow.steps) == 3, (
            f"Workflow '{workflow.workflow_name}' expected 3 steps, got {len(workflow.steps)}"
        )


# ---------------------------------------------------------------------------
# pcae collaboration workflows (Phase 37F)
# ---------------------------------------------------------------------------


def test_collaboration_workflows_human_output(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Collaboration workflows" in output
    assert "Workflow count: 4" in output
    assert "implementation" in output
    assert "documentation" in output
    assert "architecture" in output
    assert "handoff" in output
    assert "advisory" in output.lower()


def test_collaboration_workflows_json_output(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "workflows" in data
    assert "advisory" in data
    assert isinstance(data["workflows"], list)


def test_collaboration_workflows_json_four_workflows(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    names = [w["workflow_name"] for w in data["workflows"]]
    assert "implementation" in names
    assert "documentation" in names
    assert "architecture" in names
    assert "handoff" in names
    assert len(names) == 4


def test_collaboration_workflows_implementation_steps(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    impl = next(w for w in data["workflows"] if w["workflow_name"] == "implementation")
    step_names = [s["step_name"] for s in impl["steps"]]
    assert step_names == ["implementer", "reviewer", "validator"]


def test_collaboration_workflows_documentation_steps(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    doc = next(w for w in data["workflows"] if w["workflow_name"] == "documentation")
    step_names = [s["step_name"] for s in doc["steps"]]
    assert step_names == ["author", "reviewer", "validator"]


def test_collaboration_workflows_architecture_steps(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    arch = next(w for w in data["workflows"] if w["workflow_name"] == "architecture")
    step_names = [s["step_name"] for s in arch["steps"]]
    assert step_names == ["proposer", "reviewer", "validator"]


def test_collaboration_workflows_handoff_steps(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    handoff = next(w for w in data["workflows"] if w["workflow_name"] == "handoff")
    step_names = [s["step_name"] for s in handoff["steps"]]
    assert step_names == ["outgoing_agent", "incoming_agent", "validator"]


def test_collaboration_workflows_step_fields_present(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for workflow in data["workflows"]:
        for step in workflow["steps"]:
            for field in ("step_name", "recommended_agent_role", "purpose", "required_lifecycle_status"):
                assert field in step, (
                    f"Missing field '{field}' in step '{step.get('step_name')}' "
                    f"of workflow '{workflow['workflow_name']}'"
                )


def test_collaboration_workflows_steps_are_ordered(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    impl = next(w for w in data["workflows"] if w["workflow_name"] == "implementation")
    assert impl["steps"][0]["step_name"] == "implementer"
    assert impl["steps"][-1]["step_name"] == "validator"


def test_collaboration_workflows_handoff_outgoing_requires_active(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    handoff = next(w for w in data["workflows"] if w["workflow_name"] == "handoff")
    outgoing = next(s for s in handoff["steps"] if s["step_name"] == "outgoing_agent")
    assert outgoing["required_lifecycle_status"] == "active"


def test_collaboration_workflows_advisory_semantics(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no agents are executed" in data["advisory"]
    assert "assigned automatically" in data["advisory"]


def test_collaboration_workflows_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["collaboration", "workflows"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_collaboration_workflows_human_shows_steps(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["collaboration", "workflows"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "implementer" in output
    assert "proposer" in output
    assert "outgoing_agent" in output
    assert "incoming_agent" in output
    assert "Purpose:" in output
    assert "min status:" in output


def test_collaboration_workflows_core_build() -> None:
    from pcae.core.agent import COLLABORATION_WORKFLOWS, build_collaboration_workflows

    data = build_collaboration_workflows()
    assert len(data["workflows"]) == 4
    assert "no agents are executed" in data["advisory"]
    names = [w["workflow_name"] for w in data["workflows"]]
    assert names == ["implementation", "documentation", "architecture", "handoff"]


def test_collaboration_workflows_each_has_three_steps() -> None:
    from pcae.core.agent import COLLABORATION_WORKFLOWS

    for workflow in COLLABORATION_WORKFLOWS:
        assert len(workflow.steps) == 3, (
            f"Workflow '{workflow.workflow_name}' expected 3 steps, got {len(workflow.steps)}"
        )


# ---------------------------------------------------------------------------
# pcae agents config show / validate (Phase 37E)
# ---------------------------------------------------------------------------


def test_agents_config_show_available_agent(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "config", "show", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "claude-local" in output
    assert "Adapter type: cli" in output
    assert "Configuration status: configured" in output
    assert "Executable hint: claude" in output
    assert "Requires manual setup: no" in output
    assert "Lifecycle status: available" in output
    assert "advisory" in output.lower()


def test_agents_config_show_kimi_local(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "config", "show", "kimi-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "kimi-local" in output
    assert "Adapter type: cli" in output
    assert "Configuration status: configured" in output
    assert "Executable hint: kimi" in output
    assert "Requires manual setup: no" in output
    assert "Lifecycle status: available" in output


def test_agents_config_show_native_agent(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "config", "show", "pcae-native"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "pcae-native" in output
    assert "Adapter type: native" in output
    assert "Configuration status: configured" in output
    assert "Executable hint: pcae" in output
    assert "Requires manual setup: no" in output


def test_agents_config_show_unknown_agent_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "config", "show", "no-such-agent"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Agent not found" in output
    assert "no-such-agent" in output


def test_agents_config_show_json_available(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "config", "show", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_id"] == "claude-local"
    assert data["adapter_type"] == "cli"
    assert data["configuration_status"] == "configured"
    assert data["executable_hint"] == "claude"
    assert data["requires_manual_setup"] is False
    assert data["lifecycle_status"] == "available"
    assert "configuration_notes" in data


def test_agents_config_show_json_declared(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "config", "show", "deepseek-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_id"] == "deepseek-local"
    assert data["adapter_type"] == "undeclared"
    assert data["configuration_status"] == "unconfigured"
    assert data["executable_hint"] is None
    assert data["requires_manual_setup"] is True
    assert data["lifecycle_status"] == "declared"


def test_agents_config_show_json_all_fields(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "config", "show", "codex-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for field in (
        "agent_id", "adapter_type", "configuration_status",
        "executable_hint", "requires_manual_setup",
        "configuration_notes", "lifecycle_status",
    ):
        assert field in data, f"Missing field '{field}' in config show output"


def test_agents_config_show_all_declared_agents(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    for agent_id in ("deepseek-local", "gemini-local", "grok-local", "perplexity-local"):
        exit_code = main(["agents", "config", "show", agent_id, "--json"])
        data = json.loads(capsys.readouterr().out)
        assert exit_code == 0, f"Expected exit 0 for {agent_id}"
        assert data["adapter_type"] == "undeclared"
        assert data["configuration_status"] == "unconfigured"
        assert data["lifecycle_status"] == "declared"


def test_agents_config_show_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["agents", "config", "show", "claude-local"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_agents_config_validate_passes(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "config", "validate"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Agent configuration validation" in output
    assert "Validation status: valid" in output
    assert "Errors: none" in output
    assert "advisory" in output.lower()


def test_agents_config_validate_json_valid(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "config", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["errors"] == []
    assert data["agent_count"] == 8
    assert "advisory" in data
    assert "configuration does not imply execution" in data["advisory"]


def test_agents_config_validate_json_all_fields(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "config", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for field in ("valid", "agent_count", "errors", "warnings", "advisory"):
        assert field in data, f"Missing field '{field}' in config validate output"


def test_agents_config_validate_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["agents", "config", "validate"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_agents_config_available_agents_have_non_undeclared_adapter() -> None:
    from pcae.core.agent import (
        ADAPTER_TYPE_UNDECLARED,
        AGENT_CONFIG_REGISTRY,
        AGENT_STATUS_AVAILABLE,
        MULTI_AGENT_REGISTRY,
    )

    available_ids = {e.agent_id for e in MULTI_AGENT_REGISTRY if e.status == AGENT_STATUS_AVAILABLE}
    for agent_id in available_ids:
        config = AGENT_CONFIG_REGISTRY.get(agent_id)
        assert config is not None, f"No config entry for available agent '{agent_id}'"
        assert config.adapter_type != ADAPTER_TYPE_UNDECLARED, (
            f"Available agent '{agent_id}' must not use undeclared adapter"
        )


def test_agents_config_declared_agents_may_have_undeclared_adapter() -> None:
    from pcae.core.agent import (
        ADAPTER_TYPE_UNDECLARED,
        AGENT_CONFIG_REGISTRY,
        AGENT_STATUS_DECLARED,
        MULTI_AGENT_REGISTRY,
    )

    declared_ids = {e.agent_id for e in MULTI_AGENT_REGISTRY if e.status == AGENT_STATUS_DECLARED}
    for agent_id in declared_ids:
        config = AGENT_CONFIG_REGISTRY.get(agent_id)
        assert config is not None, f"No config entry for declared agent '{agent_id}'"
        assert config.adapter_type == ADAPTER_TYPE_UNDECLARED, (
            f"Declared agent '{agent_id}' expected undeclared adapter in initial mapping"
        )


def test_agents_config_validate_core_detects_available_with_undeclared() -> None:
    from pcae.core.agent import (
        ADAPTER_TYPE_UNDECLARED,
        AGENT_CONFIG_REGISTRY,
        AgentConfigEntry,
        validate_agent_configs,
    )
    import copy

    original = AGENT_CONFIG_REGISTRY.get("claude-local")
    assert original is not None

    bad_entry = AgentConfigEntry(
        agent_id="claude-local",
        adapter_type=ADAPTER_TYPE_UNDECLARED,
        executable_hint=None,
        requires_manual_setup=True,
        configuration_notes="broken",
    )

    original_registry = dict(AGENT_CONFIG_REGISTRY)
    AGENT_CONFIG_REGISTRY["claude-local"] = bad_entry
    try:
        result = validate_agent_configs()
        assert result.valid is False
        assert any("undeclared adapter" in e for e in result.errors)
    finally:
        AGENT_CONFIG_REGISTRY["claude-local"] = original_registry["claude-local"]


def test_agents_config_core_get_agent_config() -> None:
    from pcae.core.agent import get_agent_config

    config = get_agent_config("claude-local")
    assert config is not None
    assert config.agent_id == "claude-local"
    assert config.adapter_type == "cli"
    assert config.configuration_status == "configured"
    assert get_agent_config("no-such-agent") is None


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
    assert "available=4" in output
    assert "configured=0" in output
    assert "declared=4" in output
    assert "Agents by lifecycle state:" in output
    assert "available (4):" in output
    assert "declared (4):" in output
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
    assert summary["available"] == 4
    assert summary["declared"] == 4
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
    assert len(by_state["available"]) == 4
    assert len(by_state["declared"]) == 4
    assert by_state["configured"] == []
    assert by_state["active"] == []
    available_ids = {e["agent_id"] for e in by_state["available"]}
    assert available_ids == {"claude-local", "codex-local", "pcae-native", "kimi-local"}
    declared_ids = {e["agent_id"] for e in by_state["declared"]}
    assert declared_ids == {
        "deepseek-local", "gemini-local", "grok-local", "perplexity-local"
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

    assert report.lifecycle_summary["available"] == 4
    assert report.lifecycle_summary["declared"] == 4
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


# ---------------------------------------------------------------------------
# pcae agents adapters / pcae agents adapter show (Phase 38B)
# ---------------------------------------------------------------------------


def test_agents_adapters_human_output(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapters"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Agent adapters" in output
    assert "Total:" in output
    assert "Adapters:" in output
    assert "Adapter reporting is advisory; no agent runtime is modified." in output


def test_agents_adapters_json_structure(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "adapters" in data
    assert "adapter_summary" in data
    assert "advisory" in data


def test_agents_adapters_json_all_eight_agents(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    ids = {e["agent_id"] for e in data["adapters"]}
    assert len(data["adapters"]) == 8
    assert "claude-local" in ids
    assert "codex-local" in ids
    assert "kimi-local" in ids
    assert "pcae-native" in ids
    assert "deepseek-local" in ids
    assert "gemini-local" in ids
    assert "grok-local" in ids
    assert "perplexity-local" in ids


def test_agents_adapters_json_summary_counts_no_discovery(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    summary = data["adapter_summary"]
    assert summary["total"] == 8
    assert summary["cli"] == 3
    assert summary["native"] == 1
    assert summary["undeclared"] == 4
    assert summary["api"] == 0
    assert summary["desktop_manual"] == 0


def test_agents_adapters_cli_adapter_types(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    by_id = {e["agent_id"]: e for e in data["adapters"]}
    assert by_id["codex-local"]["adapter_type"] == "cli"
    assert by_id["claude-local"]["adapter_type"] == "cli"
    assert by_id["kimi-local"]["adapter_type"] == "cli"
    assert by_id["pcae-native"]["adapter_type"] == "native"
    assert by_id["deepseek-local"]["adapter_type"] == "undeclared"


def test_agents_adapters_installed_agent_shows_runtime_data(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "usage: codex [-p prompt] [--json] [mcp] [hook] [remote]"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "1.2.3" if exe == "codex" else None
    )

    exit_code = main(["agents", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    by_id = {e["agent_id"]: e for e in data["adapters"]}
    codex = by_id["codex-local"]
    assert codex["runtime_installed"] is True
    assert codex["runtime_version"] == "1.2.3"
    assert codex["supports_mcp"] == "yes"
    assert codex["supports_hooks"] == "yes"
    assert codex["supports_remote"] == "yes"


def test_agents_adapters_not_installed_shows_null_runtime(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    by_id = {e["agent_id"]: e for e in data["adapters"]}
    # CLI agents not found → installed=false, version=null
    for agent_id in ("codex-local", "claude-local", "kimi-local"):
        entry = by_id[agent_id]
        assert entry["runtime_installed"] is False
        assert entry["runtime_version"] is None


def test_agents_adapters_declared_agents_not_checked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    by_id = {e["agent_id"]: e for e in data["adapters"]}
    for agent_id in ("deepseek-local", "gemini-local", "grok-local", "perplexity-local"):
        entry = by_id[agent_id]
        assert entry["runtime_installed"] is None
        assert entry["runtime_version"] is None
        for cap_field in (
            "supports_interactive", "supports_non_interactive",
            "supports_mcp", "supports_hooks", "supports_remote",
        ):
            assert entry[cap_field] == "unknown", (
                f"{agent_id}.{cap_field} should be unknown"
            )


def test_agents_adapters_native_installed_no_version(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    by_id = {e["agent_id"]: e for e in data["adapters"]}
    native = by_id["pcae-native"]
    assert native["adapter_type"] == "native"
    assert native["runtime_installed"] is True
    assert native["runtime_version"] is None


def test_agents_adapters_all_entries_have_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    required_fields = {
        "adapter_type", "agent_id", "lifecycle_status", "notes",
        "runtime_installed", "runtime_version",
        "supports_hooks", "supports_interactive", "supports_mcp",
        "supports_non_interactive", "supports_remote",
    }
    for entry in data["adapters"]:
        for field in required_fields:
            assert field in entry, f"Missing field '{field}' in entry for {entry.get('agent_id')}"


def test_agents_adapters_advisory_string(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no agent runtime is modified" in data["advisory"]


def test_agents_adapters_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["agents", "adapters"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_agents_adapter_show_codex_local(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return "/usr/bin/codex" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "usage: codex exec [mcp] [hook] [remote] non-interactive"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "2.0.0" if exe == "codex" else None
    )

    exit_code = main(["agents", "adapter", "show", "codex-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "codex-local" in output
    assert "Adapter type: cli" in output
    assert "Lifecycle status: available" in output
    assert "Installed: yes" in output
    assert "Version: 2.0.0" in output
    assert "Adapter reporting is advisory; no agent runtime is modified." in output


def test_agents_adapter_show_kimi_local(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "kimi" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "kimi":
            return "-p, --prompt <prompt>  run one prompt non-interactively"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "0.6.0" if exe == "kimi" else None
    )

    exit_code = main(["agents", "adapter", "show", "kimi-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "kimi-local" in output
    assert "Adapter type: cli" in output
    assert "Lifecycle status: available" in output
    assert "Installed: yes" in output
    assert "Version: 0.6.0" in output
    assert "Supports non-interactive: yes" in output


def test_agents_adapter_show_unknown_agent_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "show", "no-such-agent"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Agent not found" in output
    assert "no-such-agent" in output


def test_agents_adapter_show_json(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "show", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_id"] == "claude-local"
    assert data["adapter_type"] == "cli"
    assert data["lifecycle_status"] == "available"
    assert "advisory" in data
    assert "runtime_installed" in data
    assert "supports_interactive" in data
    assert "supports_non_interactive" in data
    assert "supports_mcp" in data
    assert "supports_hooks" in data
    assert "supports_remote" in data


def test_agents_adapter_show_declared_agent(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "show", "deepseek-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_id"] == "deepseek-local"
    assert data["adapter_type"] == "undeclared"
    assert data["lifecycle_status"] == "declared"
    assert data["runtime_installed"] is None
    assert data["runtime_version"] is None
    for cap_field in (
        "supports_interactive", "supports_non_interactive",
        "supports_mcp", "supports_hooks", "supports_remote",
    ):
        assert data[cap_field] == "unknown"


def test_agents_adapter_show_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["agents", "adapter", "show", "codex-local"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_agents_adapter_show_unknown_caps_remain_unknown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return "/usr/bin/kimi" if name == "kimi" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "kimi":
            return "usage: kimi [options]"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "0.6.0" if exe == "kimi" else None
    )

    exit_code = main(["agents", "adapter", "show", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["runtime_installed"] is True
    assert data["supports_mcp"] == "unknown"
    assert data["supports_hooks"] == "unknown"
    assert data["supports_remote"] == "unknown"


# ---------------------------------------------------------------------------
# pcae agents adapter inspect (Phase 38C)
# ---------------------------------------------------------------------------


def test_agents_adapter_inspect_codex_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex exec [mcp] [hook] [remote] non-interactive --json stdin"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "1.0.0" if exe == "codex" else None
    )

    exit_code = main(["agents", "adapter", "inspect", "codex-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Adapter inspection" in output
    assert "codex-local" in output
    assert "Adapter type: cli" in output
    assert "Execution modes:" in output
    assert "Discovered capabilities:" in output
    assert "Capabilities are discovered conservatively" in output


def test_agents_adapter_inspect_codex_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "codex-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_id"] == "codex-local"
    assert data["adapter_type"] == "cli"
    assert "capabilities" in data
    assert "execution_modes" in data
    assert "advisory" in data
    assert "executable_path" in data
    assert "runtime_version" in data


def test_agents_adapter_inspect_capability_records_are_modular(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "codex-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    # Every capability record has the required modular fields
    required_fields = {"name", "status", "source", "notes"}
    for cap in data["capabilities"]:
        assert required_fields <= cap.keys(), (
            f"Capability record {cap.get('name')} missing fields"
        )


def test_agents_adapter_inspect_known_capabilities_reported(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return "/usr/bin/codex" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex exec [mcp] [hook] [remote] non-interactive --json stdin pipe"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "2.0.0" if exe == "codex" else None
    )

    exit_code = main(["agents", "adapter", "inspect", "codex-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    caps_by_name = {c["name"]: c for c in data["capabilities"]}
    assert caps_by_name["mcp"]["status"] == "yes"
    assert caps_by_name["hooks"]["status"] == "yes"
    assert caps_by_name["remote"]["status"] == "yes"
    assert caps_by_name["structured_output"]["status"] == "yes"
    assert caps_by_name["stdin_prompt"]["status"] == "yes"
    assert caps_by_name["non_interactive"]["status"] == "yes"
    assert caps_by_name["interactive"]["status"] == "yes"
    assert data["runtime_version"] == "2.0.0"
    assert data["executable_path"] == "/usr/bin/codex"


def test_agents_adapter_inspect_unknown_caps_remain_unknown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return "/usr/bin/codex" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex basic help text only"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "1.0.0" if exe == "codex" else None
    )

    exit_code = main(["agents", "adapter", "inspect", "codex-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    caps_by_name = {c["name"]: c for c in data["capabilities"]}
    assert caps_by_name["mcp"]["status"] == "unknown"
    assert caps_by_name["hooks"]["status"] == "unknown"
    assert caps_by_name["remote"]["status"] == "unknown"
    assert caps_by_name["prompt_file"]["status"] == "unknown"
    assert caps_by_name["subagents"]["status"] == "unknown"


def test_agents_adapter_inspect_execution_modes_from_discovery(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return "/usr/bin/codex" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex non-interactive exec"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "1.0.0" if exe == "codex" else None
    )

    exit_code = main(["agents", "adapter", "inspect", "codex-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "interactive" in data["execution_modes"]
    assert "non-interactive" in data["execution_modes"]


def test_agents_adapter_inspect_not_installed_all_unknown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "codex-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["executable_path"] is None
    assert data["runtime_version"] is None
    assert data["execution_modes"] == []
    for cap in data["capabilities"]:
        assert cap["status"] == "unknown", (
            f"Capability {cap['name']} should be unknown when not installed"
        )


def test_agents_adapter_inspect_unknown_agent_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "no-such-agent"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Agent not found" in output
    assert "no-such-agent" in output


def test_agents_adapter_inspect_advisory_string(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "codex-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "discovered conservatively" in data["advisory"]


def test_agents_adapter_inspect_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["agents", "adapter", "inspect", "codex-local"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_agents_adapter_inspect_cap_source_is_help(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "codex-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for cap in data["capabilities"]:
        assert cap["source"] == "help", f"Source for {cap['name']} should be 'help'"


def test_agents_adapter_inspect_capability_specs_are_extensible() -> None:
    from pcae.core.agent import _CAPABILITY_SPECS, CapabilityRecord

    # All specs have four elements and can instantiate CapabilityRecord
    for field_attr, cap_name, yes_note, unknown_note in _CAPABILITY_SPECS:
        assert isinstance(cap_name, str) and cap_name
        assert isinstance(yes_note, str) and yes_note
        assert isinstance(unknown_note, str) and unknown_note
        record = CapabilityRecord(
            name=cap_name,
            status="unknown",
            source="help",
            notes=unknown_note,
        )
        d = record.to_dict()
        assert d["name"] == cap_name
        assert d["status"] == "unknown"


def test_agents_adapter_inspect_declared_agent_all_unknown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "deepseek-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_id"] == "deepseek-local"
    assert data["executable_path"] is None
    assert data["execution_modes"] == []
    for cap in data["capabilities"]:
        assert cap["status"] == "unknown"


# pcae agents adapter inspect claude-local (Phase 38D)
# ---------------------------------------------------------------------------


def test_agents_adapter_inspect_claude_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "claude" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "claude":
            return "claude --json mcp hook remote non-interactive stdin"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "1.0.0" if exe == "claude" else None
    )

    exit_code = main(["agents", "adapter", "inspect", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Adapter inspection" in output
    assert "claude-local" in output
    assert "Adapter type: cli" in output
    assert "Execution modes:" in output
    assert "Discovered capabilities:" in output
    assert "Capabilities are discovered conservatively" in output
    assert "Claude CLI versions" in output


def test_agents_adapter_inspect_claude_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_id"] == "claude-local"
    assert data["adapter_type"] == "cli"
    assert "capabilities" in data
    assert "execution_modes" in data
    assert "advisory" in data
    assert "executable_path" in data
    assert "runtime_version" in data


def test_agents_adapter_inspect_claude_advisory_says_claude_cli(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "discovered conservatively" in data["advisory"]
    assert "Claude CLI versions" in data["advisory"]


def test_agents_adapter_inspect_claude_capability_schema_matches_codex(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    claude_code = main(["agents", "adapter", "inspect", "claude-local", "--json"])
    claude_data = json.loads(capsys.readouterr().out)

    codex_code = main(["agents", "adapter", "inspect", "codex-local", "--json"])
    codex_data = json.loads(capsys.readouterr().out)

    assert claude_code == 0
    assert codex_code == 0
    required_fields = {"name", "status", "source", "notes"}
    for cap in claude_data["capabilities"]:
        assert required_fields <= cap.keys()
    claude_names = {c["name"] for c in claude_data["capabilities"]}
    codex_names = {c["name"] for c in codex_data["capabilities"]}
    assert claude_names == codex_names


def test_agents_adapter_inspect_claude_known_capabilities_reported(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return "/usr/bin/claude" if name == "claude" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "claude":
            return "claude --json mcp hook remote non-interactive stdin pipe"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "2.0.0" if exe == "claude" else None
    )

    exit_code = main(["agents", "adapter", "inspect", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    caps_by_name = {c["name"]: c for c in data["capabilities"]}
    assert caps_by_name["mcp"]["status"] == "yes"
    assert caps_by_name["hooks"]["status"] == "yes"
    assert caps_by_name["remote"]["status"] == "yes"
    assert caps_by_name["structured_output"]["status"] == "yes"
    assert caps_by_name["stdin_prompt"]["status"] == "yes"
    assert caps_by_name["non_interactive"]["status"] == "yes"
    assert caps_by_name["interactive"]["status"] == "yes"
    assert data["runtime_version"] == "2.0.0"
    assert data["executable_path"] == "/usr/bin/claude"


def test_agents_adapter_inspect_claude_unknown_caps_remain_unknown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return "/usr/bin/claude" if name == "claude" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "claude":
            return "claude basic help text only"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "1.0.0" if exe == "claude" else None
    )

    exit_code = main(["agents", "adapter", "inspect", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    caps_by_name = {c["name"]: c for c in data["capabilities"]}
    assert caps_by_name["mcp"]["status"] == "unknown"
    assert caps_by_name["hooks"]["status"] == "unknown"
    assert caps_by_name["remote"]["status"] == "unknown"
    assert caps_by_name["prompt_file"]["status"] == "unknown"
    assert caps_by_name["subagents"]["status"] == "unknown"


def test_agents_adapter_inspect_claude_not_installed_all_unknown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["executable_path"] is None
    assert data["runtime_version"] is None
    assert data["execution_modes"] == []
    for cap in data["capabilities"]:
        assert cap["status"] == "unknown"


def test_agents_adapter_inspect_claude_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["agents", "adapter", "inspect", "claude-local"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_agents_adapter_inspect_claude_cap_source_is_help(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for cap in data["capabilities"]:
        assert cap["source"] == "help", f"Source for {cap['name']} should be 'help'"


# pcae agents adapter inspect kimi-local (Phase 38E)
# ---------------------------------------------------------------------------


def test_agents_adapter_inspect_kimi_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "kimi" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "kimi":
            return "kimi non-interactively stdin"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "1.0.0" if exe == "kimi" else None
    )

    exit_code = main(["agents", "adapter", "inspect", "kimi-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Adapter inspection" in output
    assert "kimi-local" in output
    assert "Adapter type: cli" in output
    assert "Execution modes:" in output
    assert "Capabilities are discovered conservatively" in output
    assert "Kimi CLI versions" in output


def test_agents_adapter_inspect_kimi_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_id"] == "kimi-local"
    assert data["adapter_type"] == "cli"
    assert "capabilities" in data
    assert "execution_modes" in data
    assert "advisory" in data
    assert "executable_path" in data
    assert "runtime_version" in data


def test_agents_adapter_inspect_kimi_advisory_says_kimi_cli(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "discovered conservatively" in data["advisory"]
    assert "Kimi CLI versions" in data["advisory"]


def test_agents_adapter_inspect_kimi_capability_schema_matches_codex(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    kimi_code = main(["agents", "adapter", "inspect", "kimi-local", "--json"])
    kimi_data = json.loads(capsys.readouterr().out)

    codex_code = main(["agents", "adapter", "inspect", "codex-local", "--json"])
    codex_data = json.loads(capsys.readouterr().out)

    assert kimi_code == 0
    assert codex_code == 0
    required_fields = {"name", "status", "source", "notes"}
    for cap in kimi_data["capabilities"]:
        assert required_fields <= cap.keys()
    assert {c["name"] for c in kimi_data["capabilities"]} == {
        c["name"] for c in codex_data["capabilities"]
    }


def test_agents_adapter_inspect_kimi_known_capabilities_reported(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return "/usr/bin/kimi" if name == "kimi" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "kimi":
            return "kimi non-interactively stdin pipe --json mcp hook remote"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "2.0.0" if exe == "kimi" else None
    )

    exit_code = main(["agents", "adapter", "inspect", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    caps_by_name = {c["name"]: c for c in data["capabilities"]}
    assert caps_by_name["non_interactive"]["status"] == "yes"
    assert caps_by_name["stdin_prompt"]["status"] == "yes"
    assert caps_by_name["structured_output"]["status"] == "yes"
    assert caps_by_name["mcp"]["status"] == "yes"
    assert caps_by_name["hooks"]["status"] == "yes"
    assert caps_by_name["remote"]["status"] == "yes"
    assert caps_by_name["interactive"]["status"] == "yes"
    assert data["runtime_version"] == "2.0.0"
    assert data["executable_path"] == "/usr/bin/kimi"


def test_agents_adapter_inspect_kimi_unknown_caps_remain_unknown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return "/usr/bin/kimi" if name == "kimi" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "kimi":
            return "kimi basic help text only"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "1.0.0" if exe == "kimi" else None
    )

    exit_code = main(["agents", "adapter", "inspect", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    caps_by_name = {c["name"]: c for c in data["capabilities"]}
    assert caps_by_name["mcp"]["status"] == "unknown"
    assert caps_by_name["hooks"]["status"] == "unknown"
    assert caps_by_name["remote"]["status"] == "unknown"
    assert caps_by_name["prompt_file"]["status"] == "unknown"
    assert caps_by_name["subagents"]["status"] == "unknown"
    assert caps_by_name["structured_output"]["status"] == "unknown"


def test_agents_adapter_inspect_kimi_not_installed_all_unknown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["executable_path"] is None
    assert data["runtime_version"] is None
    assert data["execution_modes"] == []
    for cap in data["capabilities"]:
        assert cap["status"] == "unknown"


def test_agents_adapter_inspect_kimi_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["agents", "adapter", "inspect", "kimi-local"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_agents_adapter_inspect_kimi_cap_source_is_help(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["agents", "adapter", "inspect", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for cap in data["capabilities"]:
        assert cap["source"] == "help", f"Source for {cap['name']} should be 'help'"


# pcae remote status (Phase 39A)
# ---------------------------------------------------------------------------


def test_remote_status_human_output_not_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote Autonomous Coding status" in output
    assert "not_ready" in output
    assert "Remote Autonomous Coding readiness is advisory" in output
    assert "no agents are executed" in output


def test_remote_status_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "readiness_status" in data
    assert "available_agents" in data
    assert "supported_adapters" in data
    assert "missing_capabilities" in data
    assert "governance_readiness" in data
    assert "safety_notes" in data
    assert "advisory" in data


def test_remote_status_not_ready_when_no_agents_installed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["readiness_status"] == "not_ready"
    assert data["available_agents"] == []
    assert data["supported_adapters"] == []


def test_remote_status_ready_when_agent_has_non_interactive(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex exec non-interactive full-auto"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "1.0.0" if exe == "codex" else None
    )

    exit_code = main(["remote", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["readiness_status"] == "ready"
    assert len(data["available_agents"]) == 1
    assert data["available_agents"][0]["agent_id"] == "codex-local"
    assert data["available_agents"][0]["non_interactive"] == "yes"


def test_remote_status_partially_ready_when_installed_no_non_interactive(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex basic help only"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(
        agent_mod, "_extract_version_string", lambda exe: "1.0.0" if exe == "codex" else None
    )

    exit_code = main(["remote", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["readiness_status"] == "partially_ready"


def test_remote_status_advisory_string(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no agents are executed" in data["advisory"]


def test_remote_status_safety_notes_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(data["safety_notes"]) >= 1
    notes_text = " ".join(data["safety_notes"]).lower()
    assert "not yet implemented" in notes_text


def test_remote_status_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["remote", "status"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_remote_status_multiple_agents_installed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name in ("codex", "claude") else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] in ("codex", "claude"):
            return f"{cmd[0]} non-interactive"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "1.0.0")

    exit_code = main(["remote", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    agent_ids = [a["agent_id"] for a in data["available_agents"]]
    assert "codex-local" in agent_ids
    assert "claude-local" in agent_ids
    assert data["readiness_status"] == "ready"


def test_remote_status_governance_readiness_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    gov = data["governance_readiness"]
    assert "session_active" in gov
    assert "architecture_memory_present" in gov
    assert "active_task_present" in gov


def test_remote_status_missing_capabilities_for_installed_agent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex basic help"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "1.0.0")

    exit_code = main(["remote", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert any("codex-local" in m for m in data["missing_capabilities"])


def test_remote_status_supported_adapters_reflect_installed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "claude" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "claude":
            return "claude non-interactive"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "1.0.0")

    exit_code = main(["remote", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "cli" in data["supported_adapters"]


# pcae remote policy (Phase 39B)
# ---------------------------------------------------------------------------


def test_remote_policy_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "policy"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote Autonomous Coding execution policy" in output
    assert "Approval required: yes" in output
    assert "codex-local" in output
    assert "claude-local" in output
    assert "kimi-local" in output
    assert "cli" in output
    assert "non_interactive" in output
    assert "Remote execution policy is advisory" in output
    assert "no agents are executed" in output


def test_remote_policy_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "policy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in (
        "advisory",
        "allowed_adapters",
        "allowed_agents",
        "allowed_execution_modes",
        "approval_required",
        "disallowed_operations",
        "max_files_changed",
        "max_runtime_minutes",
        "require_clean_git",
        "require_human_approval_before_commit",
        "require_human_approval_before_push",
        "require_pcae_check",
        "require_tests",
    ):
        assert key in data, f"Missing key: {key}"


def test_remote_policy_default_values(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "policy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["approval_required"] is True
    assert data["require_clean_git"] is True
    assert data["require_pcae_check"] is True
    assert data["require_tests"] is True
    assert data["require_human_approval_before_commit"] is True
    assert data["require_human_approval_before_push"] is True
    assert data["allowed_adapters"] == ["cli"]
    assert data["allowed_execution_modes"] == ["non_interactive"]
    assert data["max_files_changed"] is None
    assert data["max_runtime_minutes"] is None


def test_remote_policy_allowed_agents_include_all_three(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "policy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    agents = data["allowed_agents"]
    assert "codex-local" in agents
    assert "claude-local" in agents
    assert "kimi-local" in agents


def test_remote_policy_disallowed_operations_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "policy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    ops = data["disallowed_operations"]
    assert isinstance(ops, list)
    assert len(ops) > 0
    assert "force_push" in ops
    assert "rm_rf" in ops


def test_remote_policy_advisory_string(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "policy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "advisory" in data["advisory"].lower() or "policy" in data["advisory"].lower()
    assert "no agents are executed" in data["advisory"]


def test_remote_policy_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["remote", "policy"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_remote_policy_human_output_shows_disallowed_operations(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "policy"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Disallowed operations" in output
    assert "force_push" in output
    assert "rm_rf" in output


def test_remote_policy_human_output_max_fields_unlimited(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "policy"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "(unlimited)" in output


# pcae remote plan (Phase 39C)
# ---------------------------------------------------------------------------


def test_remote_plan_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote Autonomous Coding execution plan" in output
    assert "Requested agent: codex-local" in output
    assert "Execution mode: non_interactive" in output
    assert "Remote execution plan is advisory" in output
    assert "no agents are executed" in output


def test_remote_plan_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in (
        "advisory",
        "blockers",
        "execution_mode",
        "governance_readiness",
        "policy_compliance",
        "readiness_status",
        "requested_agent",
        "required_approvals",
        "required_checks",
        "safety_notes",
    ):
        assert key in data, f"Missing key: {key}"


def test_remote_plan_default_agent_is_codex(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["requested_agent"] == "codex-local"


def test_remote_plan_policy_compliance_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    comp = data["policy_compliance"]
    assert "agent_allowed" in comp
    assert "adapter_allowed" in comp
    assert "compliant" in comp
    assert "execution_mode_allowed" in comp


def test_remote_plan_required_approvals_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    approvals = data["required_approvals"]
    assert isinstance(approvals, list)
    assert len(approvals) > 0
    assert any("approval" in a for a in approvals)


def test_remote_plan_required_checks_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    checks = data["required_checks"]
    assert isinstance(checks, list)
    assert any("pcae check" in c for c in checks)
    assert any("git" in c for c in checks)
    assert any("tests" in c for c in checks)


def test_remote_plan_blocked_when_agent_not_installed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["readiness_status"] == "blocked"
    assert any("not installed" in b for b in data["blockers"])


def test_remote_plan_blocked_when_agent_not_in_policy(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan", "--agent", "unknown-agent", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["readiness_status"] == "blocked"
    assert any("not in allowed_agents" in b for b in data["blockers"])
    assert data["policy_compliance"]["agent_allowed"] is False


def test_remote_plan_ready_when_agent_installed_with_non_interactive(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex exec non-interactive full-auto"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "0.135.0")

    exit_code = main(["remote", "plan", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["readiness_status"] == "ready"
    assert data["blockers"] == []
    assert data["policy_compliance"]["agent_allowed"] is True
    assert data["policy_compliance"]["adapter_allowed"] is True


def test_remote_plan_blocked_when_installed_but_no_non_interactive(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex basic help only"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "0.135.0")

    exit_code = main(["remote", "plan", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["readiness_status"] == "blocked"
    assert any("does not support execution mode" in b for b in data["blockers"])


def test_remote_plan_agent_flag_sets_requested_agent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan", "--agent", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["requested_agent"] == "claude-local"


def test_remote_plan_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["remote", "plan"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_remote_plan_governance_readiness_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    gov = data["governance_readiness"]
    assert "session_active" in gov
    assert "architecture_memory_present" in gov
    assert "active_task_present" in gov


def test_remote_plan_safety_notes_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    notes = data["safety_notes"]
    assert isinstance(notes, list)
    assert len(notes) > 0
    assert any("No agents will be executed" in n for n in notes)


def test_remote_plan_human_output_shows_blockers(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "plan"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Blockers" in output
    assert "not installed" in output


def test_remote_plan_human_output_no_blockers_when_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex exec non-interactive full-auto"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "0.135.0")

    exit_code = main(["remote", "plan"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Blockers: none" in output
    assert "ready" in output


# pcae remote jobs (Phase 39D)
# ---------------------------------------------------------------------------


def test_remote_jobs_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote job registry" in output
    assert "Jobs: 0" in output
    assert "Supported statuses" in output
    assert "Remote jobs are advisory definitions" in output
    assert "no agents are executed" in output


def test_remote_jobs_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "advisory" in data
    assert "jobs" in data
    assert "job_schema" in data
    assert "supported_statuses" in data


def test_remote_jobs_empty_by_default(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["jobs"] == []


def test_remote_jobs_all_statuses_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    statuses = data["supported_statuses"]
    for expected in (
        "draft",
        "awaiting_approval",
        "approved",
        "blocked",
        "ready",
        "completed",
        "failed",
    ):
        assert expected in statuses, f"Missing status: {expected}"


def test_remote_jobs_seven_statuses(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(data["supported_statuses"]) == 7


def test_remote_jobs_schema_fields_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    schema = data["job_schema"]
    for field in (
        "approval_state",
        "created_at",
        "execution_mode",
        "job_id",
        "policy_compliance",
        "requested_agent",
        "requested_task",
        "required_approvals",
        "required_checks",
        "safety_notes",
        "status",
    ):
        assert field in schema, f"Missing schema field: {field}"


def test_remote_jobs_schema_field_count(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(data["job_schema"]) == 11


def test_remote_jobs_advisory_string(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no agents are executed" in data["advisory"]


def test_remote_jobs_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["remote", "jobs"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_remote_jobs_human_output_lists_statuses(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs"])

    output = capsys.readouterr().out
    assert exit_code == 0
    for status in ("draft", "awaiting_approval", "approved", "blocked", "ready"):
        assert status in output, f"Missing status in human output: {status}"


def test_remote_job_schema_fields_constant(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import REMOTE_JOB_SCHEMA_FIELDS, REMOTE_JOB_SUPPORTED_STATUSES

    assert "job_id" in REMOTE_JOB_SCHEMA_FIELDS
    assert "status" in REMOTE_JOB_SCHEMA_FIELDS
    assert "requested_agent" in REMOTE_JOB_SCHEMA_FIELDS
    assert "draft" in REMOTE_JOB_SUPPORTED_STATUSES
    assert "failed" in REMOTE_JOB_SUPPORTED_STATUSES


# pcae remote validate (Phase 39E)
# ---------------------------------------------------------------------------


def _make_valid_job(**overrides) -> dict:
    base = {
        "approval_state": "pending",
        "created_at": "2026-05-30T10:00:00+00:00",
        "execution_mode": "non_interactive",
        "job_id": "job-001",
        "policy_compliance": {"compliant": True},
        "requested_agent": "codex-local",
        "requested_task": "Run tests",
        "required_approvals": ["human approval required before execution"],
        "required_checks": ["pcae check must pass"],
        "safety_notes": ["No agents will be executed by this plan."],
        "status": "draft",
    }
    base.update(overrides)
    return base


def test_remote_validate_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "validate"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote job validation" in output
    assert "Status: valid" in output
    assert "Jobs validated: 0" in output
    assert "Remote job validation is advisory" in output
    assert "no agents are executed" in output


def test_remote_validate_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in ("advisory", "blockers", "errors", "job_count", "valid", "warnings"):
        assert key in data, f"Missing key: {key}"


def test_remote_validate_empty_registry_is_valid(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["job_count"] == 0
    assert data["errors"] == []
    assert data["warnings"] == []
    assert data["blockers"] == []


def test_remote_validate_advisory_string(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no agents are executed" in data["advisory"]


def test_remote_validate_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["remote", "validate"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_remote_validate_job_missing_field(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import build_remote_validate

    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job = _make_valid_job()
    del job["execution_mode"]

    data = build_remote_validate(jobs=[job])

    assert data["valid"] is False
    assert any("execution_mode" in e for e in data["errors"])


def test_remote_validate_job_invalid_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import build_remote_validate

    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job = _make_valid_job(status="running")

    data = build_remote_validate(jobs=[job])

    assert data["valid"] is False
    assert any("unsupported status" in e for e in data["errors"])


def test_remote_validate_job_disallowed_agent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import build_remote_validate

    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job = _make_valid_job(requested_agent="forbidden-bot")

    data = build_remote_validate(jobs=[job])

    assert data["valid"] is False
    assert any("not in allowed_agents" in b for b in data["blockers"])


def test_remote_validate_job_disallowed_execution_mode(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import build_remote_validate

    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job = _make_valid_job(execution_mode="interactive")

    data = build_remote_validate(jobs=[job])

    assert data["valid"] is False
    assert any("not allowed" in b for b in data["blockers"])


def test_remote_validate_job_empty_approvals_warning(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import build_remote_validate

    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job = _make_valid_job(required_approvals=[])

    data = build_remote_validate(jobs=[job])

    assert any("required_approvals" in w for w in data["warnings"])


def test_remote_validate_job_empty_checks_warning(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import build_remote_validate

    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job = _make_valid_job(required_checks=[])

    data = build_remote_validate(jobs=[job])

    assert any("required_checks" in w for w in data["warnings"])


def test_remote_validate_job_non_compliant_policy_warning(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import build_remote_validate

    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job = _make_valid_job(policy_compliance={"compliant": False})

    data = build_remote_validate(jobs=[job])

    assert any("policy_compliance.compliant is false" in w for w in data["warnings"])


def test_remote_validate_valid_job_passes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import build_remote_validate

    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job = _make_valid_job()

    data = build_remote_validate(jobs=[job])

    assert data["valid"] is True
    assert data["errors"] == []
    assert data["blockers"] == []
    assert data["job_count"] == 1


def test_remote_validate_multiple_jobs_accumulates_errors(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import build_remote_validate

    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    jobs = [
        _make_valid_job(job_id="job-001", requested_agent="bad-agent"),
        _make_valid_job(job_id="job-002", status="unknown-status"),
    ]

    data = build_remote_validate(jobs=jobs)

    assert data["valid"] is False
    assert data["job_count"] == 2
    assert len(data["blockers"]) >= 1
    assert len(data["errors"]) >= 1


def test_remote_validate_human_output_shows_counts(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "validate"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Errors: 0" in output
    assert "Warnings: 0" in output
    assert "Blockers: 0" in output


# pcae remote approvals (Phase 39F)
# ---------------------------------------------------------------------------


def test_remote_approvals_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approvals"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote approval workflow" in output
    assert "Approval states" in output
    assert "approval gates" in output.lower()
    assert "Pending approvals: 0" in output
    assert "Remote approvals are advisory" in output
    assert "no agents are executed" in output


def test_remote_approvals_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approvals", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in ("advisory", "approval_gates", "approval_states", "pending_approvals"):
        assert key in data, f"Missing key: {key}"


def test_remote_approvals_all_states_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approvals", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    states = data["approval_states"]
    for expected in ("pending", "approved", "denied", "expired"):
        assert expected in states, f"Missing state: {expected}"


def test_remote_approvals_four_states(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approvals", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(data["approval_states"]) == 4


def test_remote_approvals_all_gates_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approvals", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    gate_names = [g["gate"] for g in data["approval_gates"]]
    for expected in ("before_execution", "before_commit", "before_push"):
        assert expected in gate_names, f"Missing gate: {expected}"


def test_remote_approvals_three_gates(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approvals", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(data["approval_gates"]) == 3


def test_remote_approvals_gate_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approvals", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for gate in data["approval_gates"]:
        assert "gate" in gate
        assert "required" in gate
        assert "description" in gate
        assert isinstance(gate["required"], bool)


def test_remote_approvals_gates_required_from_policy(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approvals", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    gates_by_name = {g["gate"]: g for g in data["approval_gates"]}
    assert gates_by_name["before_execution"]["required"] is True
    assert gates_by_name["before_commit"]["required"] is True
    assert gates_by_name["before_push"]["required"] is True


def test_remote_approvals_empty_registry_no_pending(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approvals", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["pending_approvals"] == []


def test_remote_approvals_pending_job_appears(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import build_remote_approvals

    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    jobs = [{"job_id": "job-001", "approval_state": "pending", "requested_agent": "codex-local"}]

    data = build_remote_approvals(jobs=jobs)

    assert len(data["pending_approvals"]) == 1
    p = data["pending_approvals"][0]
    assert p["job_id"] == "job-001"
    assert p["state"] == "pending"
    assert p["gate"] == "before_execution"
    assert p["requested_agent"] == "codex-local"


def test_remote_approvals_approved_job_not_pending(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import build_remote_approvals

    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    jobs = [{"job_id": "job-002", "approval_state": "approved", "requested_agent": "codex-local"}]

    data = build_remote_approvals(jobs=jobs)

    assert data["pending_approvals"] == []


def test_remote_approvals_advisory_string(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approvals", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no agents are executed" in data["advisory"]


def test_remote_approvals_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["remote", "approvals"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_remote_approvals_human_output_shows_gate_names(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approvals"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "before_execution" in output
    assert "before_commit" in output
    assert "before_push" in output


def test_remote_approvals_constants(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import REMOTE_APPROVAL_GATES, REMOTE_APPROVAL_STATES

    assert len(REMOTE_APPROVAL_STATES) == 4
    assert len(REMOTE_APPROVAL_GATES) == 3
    assert "pending" in REMOTE_APPROVAL_STATES
    assert "before_execution" in REMOTE_APPROVAL_GATES


# ---------------------------------------------------------------------------


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
