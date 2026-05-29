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
