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


# pcae remote adapters (Phase 39G)
# ---------------------------------------------------------------------------


def test_remote_adapters_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "adapters"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote adapter selection" in output
    assert "Recommended runtime:" in output
    assert "Remote adapter selection is advisory" in output
    assert "no agents are executed" in output


def test_remote_adapters_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in (
        "advisory",
        "eligible_agents",
        "rationale",
        "recommended_remote_runtime",
        "selection_notes",
    ):
        assert key in data, f"Missing key: {key}"


def test_remote_adapters_all_three_agents_represented(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    agent_ids = [a["agent_id"] for a in data["eligible_agents"]]
    assert "codex-local" in agent_ids
    assert "claude-local" in agent_ids
    assert "kimi-local" in agent_ids


def test_remote_adapters_no_recommendation_when_none_installed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["recommended_remote_runtime"] is None
    assert "No eligible" in data["rationale"]
    for a in data["eligible_agents"]:
        assert a["eligible"] is False
        assert a["runtime_installed"] is False


def test_remote_adapters_codex_eligible_with_non_interactive_and_remote(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex exec non-interactive full-auto remote"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "0.135.0")

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    codex = next(a for a in data["eligible_agents"] if a["agent_id"] == "codex-local")
    assert codex["eligible"] is True
    assert codex["non_interactive"] == "yes"
    assert codex["remote"] == "yes"
    assert codex["policy_allowed"] is True


def test_remote_adapters_recommends_codex_when_installed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex exec non-interactive full-auto remote"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "0.135.0")

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["recommended_remote_runtime"] == "codex-local"
    assert "codex-local" in data["rationale"]


def test_remote_adapters_claude_eligible_when_installed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "claude" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "claude":
            return "claude --print non-interactive remote"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "2.1.0")

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    claude = next(a for a in data["eligible_agents"] if a["agent_id"] == "claude-local")
    assert claude["eligible"] is True
    assert claude["policy_allowed"] is True


def test_remote_adapters_kimi_eligible_with_unknown_remote(
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
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "0.6.0")

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    kimi = next(a for a in data["eligible_agents"] if a["agent_id"] == "kimi-local")
    assert kimi["eligible"] is True
    assert kimi["remote"] == "unknown"
    assert any("remote" in m for m in kimi["missing_capabilities"])


def test_remote_adapters_kimi_selection_note_for_unknown_remote(
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
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "0.6.0")

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert any("kimi-local" in n and "unknown remote" in n for n in data["selection_notes"])


def test_remote_adapters_codex_preferred_over_kimi_unknown_remote(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name in ("codex", "kimi") else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex exec non-interactive full-auto remote"
        if cmd[0] == "kimi":
            return "kimi non-interactively stdin"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "1.0.0")

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["recommended_remote_runtime"] == "codex-local"


def test_remote_adapters_agent_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for agent in data["eligible_agents"]:
        for field in (
            "adapter_type",
            "agent_id",
            "eligible",
            "eligibility_reason",
            "missing_capabilities",
            "non_interactive",
            "policy_allowed",
            "remote",
            "runtime_installed",
            "runtime_version",
        ):
            assert field in agent, f"Missing field '{field}' in agent {agent.get('agent_id')}"


def test_remote_adapters_advisory_string(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no agents are executed" in data["advisory"]


def test_remote_adapters_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["remote", "adapters"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_remote_adapters_ineligible_reason_not_installed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "adapters", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for a in data["eligible_agents"]:
        assert "not installed" in a["eligibility_reason"]


# pcae remote strategy (Phase 39H)
# ---------------------------------------------------------------------------


def test_remote_strategy_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "strategy"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote execution strategy" in output
    assert "Selection strategy: human_selected" in output
    assert "Human override: enabled" in output
    assert "Runtime selection remains under human control." in output


def test_remote_strategy_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "strategy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in (
        "advisory",
        "advisory_notes",
        "fallback_runtimes",
        "human_override_enabled",
        "preferred_runtime",
        "selection_strategy",
        "supported_strategies",
        "tie_break_rule",
    ):
        assert key in data, f"Missing key: {key}"


def test_remote_strategy_default_is_human_selected(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "strategy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["selection_strategy"] == "human_selected"


def test_remote_strategy_human_override_enabled(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "strategy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["human_override_enabled"] is True


def test_remote_strategy_no_preferred_runtime(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "strategy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["preferred_runtime"] is None


def test_remote_strategy_empty_fallback_runtimes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "strategy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["fallback_runtimes"] == []


def test_remote_strategy_no_tie_break_rule(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "strategy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["tie_break_rule"] is None


def test_remote_strategy_advisory_notes_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "strategy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    notes = data["advisory_notes"]
    assert isinstance(notes, list)
    assert len(notes) > 0
    assert any("Human selection" in n for n in notes)
    assert any("advisory" in n.lower() for n in notes)
    assert any("neutrality" in n.lower() for n in notes)


def test_remote_strategy_advisory_string(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "strategy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "human control" in data["advisory"].lower()


def test_remote_strategy_supported_strategies(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "strategy", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    strategies = data["supported_strategies"]
    for expected in (
        "human_selected",
        "capability_based",
        "policy_based",
        "registry_order",
    ):
        assert expected in strategies, f"Missing strategy: {expected}"


def test_remote_strategy_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["remote", "strategy"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_remote_strategy_human_output_shows_none_for_defaults(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "strategy"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Preferred runtime: (none)" in output
    assert "Fallback runtimes: (none)" in output
    assert "Tie-break rule: (none)" in output


def test_remote_strategy_constants(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import REMOTE_SELECTION_STRATEGIES

    assert "human_selected" in REMOTE_SELECTION_STRATEGIES
    assert "capability_based" in REMOTE_SELECTION_STRATEGIES
    assert "policy_based" in REMOTE_SELECTION_STRATEGIES
    assert "registry_order" in REMOTE_SELECTION_STRATEGIES
    assert len(REMOTE_SELECTION_STRATEGIES) == 4


# pcae remote dry-run (Phase 40A)
# ---------------------------------------------------------------------------


def _mock_codex_non_interactive_remote(find_fn=None, probe_fn=None):
    """Return (mock_find, mock_probe) for a codex with full remote support."""
    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex exec non-interactive full-auto remote mcp hook"
        return None

    return find_fn or mock_find, probe_fn or mock_probe


def test_remote_dry_run_human_output_codex(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    mock_find, mock_probe = _mock_codex_non_interactive_remote()
    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "0.135.0")

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "run tests"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote Autonomous Coding dry run" in output
    assert "Selected agent: codex-local" in output
    assert "Dry-run result: would_execute" in output
    assert "run tests" in output
    assert "No agent was executed." in output
    assert "Remote dry run is advisory" in output


def test_remote_dry_run_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "test", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in (
        "adapter_capabilities",
        "advisory",
        "blockers",
        "dry_run_result",
        "execution_mode",
        "policy_compliance",
        "prompt_preview",
        "required_approvals",
        "required_checks",
        "safety_notes",
        "selected_agent",
    ):
        assert key in data, f"Missing key: {key}"


def test_remote_dry_run_would_execute_when_installed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    mock_find, mock_probe = _mock_codex_non_interactive_remote()
    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "0.135.0")

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "run tests", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["dry_run_result"] == "would_execute"
    assert data["blockers"] == []
    assert data["selected_agent"] == "codex-local"


def test_remote_dry_run_blocked_when_not_installed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "test", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["dry_run_result"] == "blocked"
    assert any("not installed" in b for b in data["blockers"])


def test_remote_dry_run_unknown_agent_exits_1(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "dry-run", "--agent", "totally-unknown-bot", "--prompt", "test"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Unknown agent" in output or "unknown" in output.lower()
    assert "totally-unknown-bot" in output


def test_remote_dry_run_agent_not_in_policy_is_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    # pcae-native is in the registry but not in policy allowed_agents
    exit_code = main(["remote", "dry-run", "--agent", "pcae-native", "--prompt", "test", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["dry_run_result"] == "blocked"
    assert any("not in allowed_agents" in b for b in data["blockers"])
    assert data["policy_compliance"]["agent_allowed"] is False


def test_remote_dry_run_claude_local_works(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "claude" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "claude":
            return "claude --print non-interactive remote mcp hook"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "2.1.0")

    exit_code = main(["remote", "dry-run", "--agent", "claude-local", "--prompt", "review code", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["selected_agent"] == "claude-local"
    assert data["dry_run_result"] == "would_execute"
    assert data["policy_compliance"]["agent_allowed"] is True


def test_remote_dry_run_kimi_local_policy_compliant(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "kimi" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "kimi":
            return "kimi non-interactively stdin pipe"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "0.6.0")

    exit_code = main(["remote", "dry-run", "--agent", "kimi-local", "--prompt", "fix bug", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["selected_agent"] == "kimi-local"
    assert data["policy_compliance"]["agent_allowed"] is True
    assert data["dry_run_result"] == "would_execute"


def test_remote_dry_run_safety_notes_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "test", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    notes = data["safety_notes"]
    assert any("No agent was executed" in n for n in notes)
    assert any("not submitted" in n for n in notes)
    assert any("preview" in n.lower() for n in notes)


def test_remote_dry_run_prompt_preview_in_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "run all unit tests", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["prompt_preview"] == "run all unit tests"


def test_remote_dry_run_prompt_truncated_at_200(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    long_prompt = "x" * 300

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", long_prompt, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(data["prompt_preview"]) == 200


def test_remote_dry_run_no_execution_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "test", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no agent was executed" in data["advisory"].lower()
    assert "no prompt was submitted" in data["advisory"].lower()


def test_remote_dry_run_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "test"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_remote_dry_run_required_approvals_listed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "test", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(data["required_approvals"]) > 0
    assert any("approval" in a for a in data["required_approvals"])


def test_remote_dry_run_required_checks_listed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "test", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    checks = data["required_checks"]
    assert any("pcae check" in c for c in checks)
    assert any("tests" in c for c in checks)
    assert any("git" in c for c in checks)


def test_remote_dry_run_adapter_capabilities_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "test", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    caps = data["adapter_capabilities"]
    for field in ("hooks", "installed", "mcp", "non_interactive", "remote", "runtime_version"):
        assert field in caps, f"Missing capability field: {field}"


def test_remote_dry_run_policy_compliance_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_mod, "_find_executable", _mock_none_find)
    monkeypatch.setattr(agent_mod, "_run_probe", _mock_none_probe)

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "test", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    comp = data["policy_compliance"]
    for field in ("adapter_allowed", "agent_allowed", "compliant", "execution_mode_allowed"):
        assert field in comp, f"Missing compliance field: {field}"


def test_remote_dry_run_blocked_no_non_interactive(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.core.agent as agent_mod
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mock_find(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "codex" else None

    def mock_probe(cmd: list, timeout: int = 5) -> str | None:
        if cmd[0] == "codex":
            return "codex help only basic"
        return None

    monkeypatch.setattr(agent_mod, "_find_executable", mock_find)
    monkeypatch.setattr(agent_mod, "_run_probe", mock_probe)
    monkeypatch.setattr(agent_mod, "_extract_version_string", lambda exe: "0.135.0")

    exit_code = main(["remote", "dry-run", "--agent", "codex-local", "--prompt", "test", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["dry_run_result"] == "blocked"
    assert any("non-interactive" in b for b in data["blockers"])


# pcae remote create --dry-run (Phase 40B)
# ---------------------------------------------------------------------------


def test_remote_create_dry_run_human_output_codex(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "run tests", "--dry-run"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote job creation preview" in output
    assert "codex-local" in output
    assert "draft" in output
    assert "pending" in output
    assert "No job is persisted." in output
    assert "Remote job creation preview is advisory" in output


def test_remote_create_dry_run_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "advisory" in data
    assert "job_preview" in data
    assert "validation" in data


def test_remote_create_dry_run_job_schema_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job = data["job_preview"]
    for field in (
        "approval_state",
        "created_at",
        "dry_run",
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
        assert field in job, f"Missing job field: {field}"


def test_remote_create_dry_run_codex_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "run tests", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job = data["job_preview"]
    assert job["requested_agent"] == "codex-local"
    assert job["policy_compliance"]["agent_allowed"] is True
    assert job["dry_run"] is True


def test_remote_create_dry_run_claude_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "claude-local", "--prompt", "review code", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job = data["job_preview"]
    assert job["requested_agent"] == "claude-local"
    assert job["policy_compliance"]["agent_allowed"] is True


def test_remote_create_dry_run_kimi_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "kimi-local", "--prompt", "fix bug", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job = data["job_preview"]
    assert job["requested_agent"] == "kimi-local"
    assert job["policy_compliance"]["agent_allowed"] is True


def test_remote_create_dry_run_missing_dry_run_flag_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["remote", "create", "--agent", "codex-local", "--prompt", "test"])

    assert exc_info.value.code != 0


def test_remote_create_dry_run_unknown_agent_exits_1(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "totally-unknown-bot", "--prompt", "test", "--dry-run"]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "totally-unknown-bot" in output


def test_remote_create_dry_run_status_is_draft(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_preview"]["status"] == "draft"


def test_remote_create_dry_run_approval_state_pending(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_preview"]["approval_state"] == "pending"


def test_remote_create_dry_run_flag_is_true(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_preview"]["dry_run"] is True


def test_remote_create_dry_run_validation_valid_for_allowed_agent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    val = data["validation"]
    assert val["valid"] is True
    assert val["errors"] == []
    assert val["blockers"] == []


def test_remote_create_dry_run_validation_blocked_for_disallowed_agent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "pcae-native", "--prompt", "test", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    val = data["validation"]
    assert val["valid"] is False
    assert any("not in allowed_agents" in b for b in val["blockers"])


def test_remote_create_dry_run_job_id_starts_with_preview(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_preview"]["job_id"].startswith("preview-")


def test_remote_create_dry_run_advisory_confirmed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no job is persisted" in data["advisory"].lower()
    assert "no agent is executed" in data["advisory"].lower()


def test_remote_create_dry_run_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["remote", "create", "--agent", "codex-local", "--prompt", "test", "--dry-run"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_remote_create_dry_run_prompt_stored_as_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "fix the login bug", "--dry-run", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_preview"]["requested_task"] == "fix the login bug"


# pcae remote create --preview-persist (Phase 40C)
# ---------------------------------------------------------------------------


def test_remote_persist_preview_human_output_codex(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "run tests", "--preview-persist"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote job persistence preview" in output
    assert "codex-local" in output
    assert "draft" in output
    assert "pending" in output
    assert ".pcae/remote/jobs/" in output
    assert "No job file is written." in output
    assert "no files are written" in output.lower()


def test_remote_persist_preview_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "advisory" in data
    assert "job_file_path" in data
    assert "job_preview" in data
    assert "output_directory" in data
    assert "validation" in data


def test_remote_persist_preview_job_schema_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job = data["job_preview"]
    for field in (
        "approval_state",
        "created_at",
        "execution_mode",
        "job_id",
        "persist_preview",
        "policy_compliance",
        "requested_agent",
        "requested_task",
        "required_approvals",
        "required_checks",
        "safety_notes",
        "status",
    ):
        assert field in job, f"Missing job field: {field}"


def test_remote_persist_preview_codex_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "run tests", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job = data["job_preview"]
    assert job["requested_agent"] == "codex-local"
    assert job["policy_compliance"]["agent_allowed"] is True
    assert job["persist_preview"] is True


def test_remote_persist_preview_claude_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "claude-local", "--prompt", "review code", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job = data["job_preview"]
    assert job["requested_agent"] == "claude-local"
    assert job["policy_compliance"]["agent_allowed"] is True
    assert job["persist_preview"] is True


def test_remote_persist_preview_kimi_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "kimi-local", "--prompt", "fix bug", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job = data["job_preview"]
    assert job["requested_agent"] == "kimi-local"
    assert job["policy_compliance"]["agent_allowed"] is True
    assert job["persist_preview"] is True


def test_remote_persist_preview_job_file_path_format(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    path = data["job_file_path"]
    assert ".pcae/remote/jobs/" in path
    assert path.endswith(".json")
    assert data["output_directory"] == ".pcae/remote/jobs"


def test_remote_persist_preview_job_id_starts_with_job(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_preview"]["job_id"].startswith("job-")


def test_remote_persist_preview_status_is_draft(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_preview"]["status"] == "draft"


def test_remote_persist_preview_approval_state_pending(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_preview"]["approval_state"] == "pending"


def test_remote_persist_preview_validation_valid_for_allowed_agent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    val = data["validation"]
    assert val["valid"] is True
    assert val["errors"] == []
    assert val["blockers"] == []


def test_remote_persist_preview_validation_blocked_for_disallowed_agent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "pcae-native", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    val = data["validation"]
    assert val["valid"] is False
    assert any("not in allowed_agents" in b for b in val["blockers"])


def test_remote_persist_preview_unknown_agent_exits_1(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "totally-unknown-bot", "--prompt", "test", "--preview-persist"]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "totally-unknown-bot" in output


def test_remote_persist_preview_advisory_confirmed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "no files are written" in data["advisory"].lower()
    assert "no agent is executed" in data["advisory"].lower()


def test_remote_persist_preview_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = set(p.name for p in (tmp_path / ".pcae").iterdir())
    main(["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist"])
    capsys.readouterr()
    after = set(p.name for p in (tmp_path / ".pcae").iterdir())

    assert before == after


def test_remote_persist_preview_no_files_created(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    remote_dir = tmp_path / ".pcae" / "remote"
    main(["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist"])
    capsys.readouterr()

    assert not remote_dir.exists()


def test_remote_persist_preview_required_approvals_listed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    approvals = data["job_preview"]["required_approvals"]
    assert isinstance(approvals, list)
    assert len(approvals) > 0


def test_remote_persist_preview_required_checks_listed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    checks = data["job_preview"]["required_checks"]
    assert isinstance(checks, list)
    assert len(checks) > 0


def test_remote_persist_preview_safety_notes_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    notes = data["job_preview"]["safety_notes"]
    assert isinstance(notes, list)
    assert len(notes) == 3
    assert any("No job file is written" in n for n in notes)
    assert any("No agent will be executed" in n for n in notes)


def test_remote_persist_preview_prompt_stored_as_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "fix the login bug", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_preview"]["requested_task"] == "fix the login bug"


def test_remote_persist_preview_and_dry_run_mutually_exclusive(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main([
            "remote", "create", "--agent", "codex-local", "--prompt", "test",
            "--dry-run", "--preview-persist",
        ])

    assert exc_info.value.code != 0


# pcae remote create --persist (Phase 40D)
# ---------------------------------------------------------------------------


def test_remote_persist_human_output_codex(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "run tests", "--persist"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Job created" in output
    assert "codex-local" in output
    assert "draft" in output
    assert "pending" in output
    assert ".pcae/remote/jobs/" in output
    assert "Job persisted. No agent execution has occurred." in output


def test_remote_persist_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "advisory" in data
    assert "job" in data
    assert "job_path" in data
    assert "persisted" in data


def test_remote_persist_job_schema_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job = data["job"]
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
        assert field in job, f"Missing job field: {field}"


def test_remote_persist_no_extra_fields_in_job(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job = data["job"]
    assert "dry_run" not in job
    assert "persist_preview" not in job


def test_remote_persist_codex_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "run tests", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["persisted"] is True
    assert data["job"]["requested_agent"] == "codex-local"
    assert data["job"]["policy_compliance"]["agent_allowed"] is True


def test_remote_persist_claude_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "claude-local", "--prompt", "review code", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["persisted"] is True
    assert data["job"]["requested_agent"] == "claude-local"


def test_remote_persist_kimi_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "kimi-local", "--prompt", "fix bug", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["persisted"] is True
    assert data["job"]["requested_agent"] == "kimi-local"


def test_remote_persist_file_is_created(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job_path = tmp_path / data["job_path"]
    assert job_path.exists(), f"Expected job file at {job_path}"


def test_remote_persist_file_path_format(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_path"].startswith(".pcae/remote/jobs/")
    assert data["job_path"].endswith(".json")


def test_remote_persist_file_content_matches_job(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test task", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job_path = tmp_path / data["job_path"]
    persisted = json.loads(job_path.read_text(encoding="utf-8"))
    assert persisted == data["job"]


def test_remote_persist_status_is_draft(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job"]["status"] == "draft"


def test_remote_persist_approval_state_pending(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job"]["approval_state"] == "pending"


def test_remote_persist_unknown_agent_exits_1(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "totally-unknown-bot", "--prompt", "test", "--persist"]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "totally-unknown-bot" in output


def test_remote_persist_disallowed_agent_exits_1(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "pcae-native", "--prompt", "test", "--persist"]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "pcae-native" in output
    assert "not allowed" in output.lower()


def test_remote_persist_disallowed_agent_no_file_created(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "pcae-native", "--prompt", "test", "--persist"])
    capsys.readouterr()

    remote_dir = tmp_path / ".pcae" / "remote"
    assert not remote_dir.exists()


def test_remote_persist_advisory_confirmed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "job persisted" in data["advisory"].lower()
    assert "no agent execution" in data["advisory"].lower()


def test_remote_persist_required_approvals_listed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    approvals = data["job"]["required_approvals"]
    assert isinstance(approvals, list)
    assert len(approvals) > 0


def test_remote_persist_required_checks_listed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    checks = data["job"]["required_checks"]
    assert isinstance(checks, list)
    assert len(checks) > 0


def test_remote_persist_prompt_stored_as_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "implement the login flow", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job"]["requested_task"] == "implement the login flow"


def test_remote_persist_directory_created(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    assert not jobs_dir.exists()

    main(["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist"])
    capsys.readouterr()

    assert jobs_dir.exists()
    assert jobs_dir.is_dir()


def test_remote_persist_missing_persist_flag_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["remote", "create", "--agent", "codex-local", "--prompt", "test"])

    assert exc_info.value.code != 0


def test_remote_persist_mutually_exclusive_with_dry_run(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main([
            "remote", "create", "--agent", "codex-local", "--prompt", "test",
            "--dry-run", "--persist",
        ])

    assert exc_info.value.code != 0


def test_remote_persist_job_id_starts_with_job(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job"]["job_id"].startswith("job-")


def test_remote_persist_safety_notes_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    notes = data["job"]["safety_notes"]
    assert isinstance(notes, list)
    assert len(notes) == 3
    assert any("No agent has been executed" in n for n in notes)
    assert any("No prompt has been submitted" in n for n in notes)
    assert any("Human approval is required" in n for n in notes)


# pcae remote create --persist identity hardening (Phase 40D.1)
# ---------------------------------------------------------------------------


def test_remote_persist_job_id_includes_microseconds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job_id = data["job"]["job_id"]
    # Format: job-YYYYMMDD-HHMMSS-FFFFFF
    parts = job_id.split("-")
    assert len(parts) == 4, f"Expected 4 dash-separated parts, got: {job_id}"
    assert parts[0] == "job"
    assert len(parts[1]) == 8   # YYYYMMDD
    assert len(parts[2]) == 6   # HHMMSS
    assert len(parts[3]) == 6   # microseconds (FFFFFF)
    assert parts[3].isdigit()


def test_remote_persist_filename_matches_job_id(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job_id = data["job"]["job_id"]
    job_path = data["job_path"]
    assert job_path == f".pcae/remote/jobs/{job_id}.json"


def test_remote_persist_rapid_jobs_all_unique(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    count = 5
    ids_seen: list[str] = []
    paths_seen: list[str] = []
    for i in range(count):
        exit_code = main(
            ["remote", "create", "--agent", "codex-local", "--prompt", f"task {i}", "--persist", "--json"]
        )
        data = json.loads(capsys.readouterr().out)
        assert exit_code == 0
        ids_seen.append(data["job"]["job_id"])
        paths_seen.append(data["job_path"])

    assert len(set(ids_seen)) == count, f"Duplicate job IDs detected: {ids_seen}"
    assert len(set(paths_seen)) == count, f"Duplicate job paths detected: {paths_seen}"
    for path in paths_seen:
        assert (tmp_path / path).exists(), f"Missing job file: {path}"


def test_remote_persist_first_job_not_overwritten_by_second(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "first task", "--persist", "--json"]
    )
    first_data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    first_path = tmp_path / first_data["job_path"]
    first_content = first_path.read_text(encoding="utf-8")

    exit_code = main(
        ["remote", "create", "--agent", "claude-local", "--prompt", "second task", "--persist", "--json"]
    )
    second_data = json.loads(capsys.readouterr().out)
    assert exit_code == 0

    assert first_data["job"]["job_id"] != second_data["job"]["job_id"]
    assert first_path.read_text(encoding="utf-8") == first_content


def test_generate_unique_job_id_skips_existing_file(tmp_path: Path) -> None:
    from pcae.core.agent import _generate_unique_job_id

    jobs_dir = tmp_path / "jobs"
    jobs_dir.mkdir()

    # First call: returns a path that does not yet exist
    job_id_1, path_1 = _generate_unique_job_id(jobs_dir)
    assert not path_1.exists()
    assert path_1 == jobs_dir / f"{job_id_1}.json"

    # Pre-create that file to simulate a collision
    path_1.write_text("{}", encoding="utf-8")

    # Second call: must return a different path that does not exist
    job_id_2, path_2 = _generate_unique_job_id(jobs_dir)
    assert not path_2.exists()
    assert job_id_2 != job_id_1
    assert path_2 != path_1


def test_generate_unique_job_id_path_matches_id(tmp_path: Path) -> None:
    from pcae.core.agent import _generate_unique_job_id

    jobs_dir = tmp_path / "jobs"
    jobs_dir.mkdir()

    job_id, path = _generate_unique_job_id(jobs_dir)
    assert path == jobs_dir / f"{job_id}.json"


def test_remote_persist_preview_job_id_includes_microseconds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["remote", "create", "--agent", "codex-local", "--prompt", "test", "--preview-persist", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job_id = data["job_preview"]["job_id"]
    parts = job_id.split("-")
    assert len(parts) == 4, f"Expected 4 dash-separated parts, got: {job_id}"
    assert parts[3].isdigit() and len(parts[3]) == 6


# pcae remote jobs list (Phase 40E)
# ---------------------------------------------------------------------------


def test_remote_jobs_list_empty_directory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote job listing" in output
    assert "Job count: 0" in output
    assert "Job listing is read-only" in output


def test_remote_jobs_list_empty_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_count"] == 0
    assert data["jobs"] == []
    assert data["warnings"] == []
    assert "advisory" in data


def test_remote_jobs_list_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in ("advisory", "job_count", "jobs", "warnings"):
        assert key in data, f"Missing key: {key}"


def test_remote_jobs_list_shows_persisted_jobs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "task A", "--persist"])
    capsys.readouterr()
    main(["remote", "create", "--agent", "claude-local", "--prompt", "task B", "--persist"])
    capsys.readouterr()

    exit_code = main(["remote", "jobs", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_count"] == 2
    assert len(data["jobs"]) == 2


def test_remote_jobs_list_sorted_newest_first(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "first", "--persist", "--json"])
    first_data = json.loads(capsys.readouterr().out)

    main(["remote", "create", "--agent", "claude-local", "--prompt", "second", "--persist", "--json"])
    second_data = json.loads(capsys.readouterr().out)

    exit_code = main(["remote", "jobs", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    ids = [j["job_id"] for j in data["jobs"]]
    # Second job was created later — should appear first
    assert ids[0] == second_data["job"]["job_id"]
    assert ids[1] == first_data["job"]["job_id"]


def test_remote_jobs_list_job_fields_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist"])
    capsys.readouterr()

    exit_code = main(["remote", "jobs", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    job = data["jobs"][0]
    for field in ("job_id", "requested_agent", "status", "approval_state", "created_at"):
        assert field in job, f"Missing field: {field}"


def test_remote_jobs_list_human_output_with_jobs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "test task", "--persist"])
    capsys.readouterr()

    exit_code = main(["remote", "jobs", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Job count: 1" in output
    assert "codex-local" in output
    assert "draft" in output
    assert "pending" in output
    assert "Job listing is read-only" in output


def test_remote_jobs_list_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "read-only" in data["advisory"].lower()
    assert "no agents are executed" in data["advisory"].lower()


def test_remote_jobs_list_malformed_file_warning(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    (jobs_dir / "job-bad.json").write_text("not valid json{{", encoding="utf-8")

    exit_code = main(["remote", "jobs", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_count"] == 0
    assert len(data["warnings"]) == 1
    assert "job-bad.json" in data["warnings"][0]


def test_remote_jobs_list_malformed_file_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    (jobs_dir / "job-bad.json").write_text("null", encoding="utf-8")

    exit_code = main(["remote", "jobs", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Warning" in output
    assert "job-bad.json" in output


def test_remote_jobs_list_malformed_and_valid_mixed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "good job", "--persist"])
    capsys.readouterr()

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    (jobs_dir / "job-broken.json").write_text("{bad json", encoding="utf-8")

    exit_code = main(["remote", "jobs", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_count"] == 1
    assert len(data["warnings"]) == 1


def test_remote_jobs_list_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "test", "--persist"])
    capsys.readouterr()
    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    files_before = set(p.name for p in jobs_dir.iterdir())

    main(["remote", "jobs", "list"])
    capsys.readouterr()

    files_after = set(p.name for p in jobs_dir.iterdir())
    assert files_before == files_after


def test_remote_jobs_list_no_jobs_dir(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    remote_dir = tmp_path / ".pcae" / "remote"
    assert not remote_dir.exists()

    exit_code = main(["remote", "jobs", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_count"] == 0
    assert data["jobs"] == []


def test_remote_jobs_list_three_agents(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    for agent in ("codex-local", "claude-local", "kimi-local"):
        main(["remote", "create", "--agent", agent, "--prompt", f"task for {agent}", "--persist"])
        capsys.readouterr()

    exit_code = main(["remote", "jobs", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_count"] == 3
    agents_in_list = {j["requested_agent"] for j in data["jobs"]}
    assert agents_in_list == {"codex-local", "claude-local", "kimi-local"}


def test_remote_jobs_list_job_count_matches_jobs_length(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    for i in range(3):
        main(["remote", "create", "--agent", "codex-local", "--prompt", f"task {i}", "--persist"])
        capsys.readouterr()

    exit_code = main(["remote", "jobs", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job_count"] == len(data["jobs"])


# ---------------------------------------------------------------------------
# pcae remote jobs show (Phase 40F)
# ---------------------------------------------------------------------------


def test_remote_jobs_show_existing_job_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "do the thing", "--persist", "--json"])
    data_create = json.loads(capsys.readouterr().out)
    job_id = data_create["job"]["job_id"]

    exit_code = main(["remote", "jobs", "show", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["job"]["job_id"] == job_id
    assert "advisory" in data


def test_remote_jobs_show_existing_job_human(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "human task", "--persist", "--json"])
    data_create = json.loads(capsys.readouterr().out)
    job_id = data_create["job"]["job_id"]

    exit_code = main(["remote", "jobs", "show", job_id])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote job details" in output
    assert job_id in output


def test_remote_jobs_show_unknown_job_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "jobs", "show", "job-99999999-000000-000000"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Unknown job" in output or "No file found" in output


def test_remote_jobs_show_malformed_json_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_id = "job-20260101-120000-000000"
    (jobs_dir / f"{job_id}.json").write_text("{bad json", encoding="utf-8")

    exit_code = main(["remote", "jobs", "show", job_id])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Malformed" in output or "malformed" in output


def test_remote_jobs_show_malformed_not_dict_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_id = "job-20260101-120000-000001"
    (jobs_dir / f"{job_id}.json").write_text("[1, 2, 3]", encoding="utf-8")

    exit_code = main(["remote", "jobs", "show", job_id])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Malformed" in output or "malformed" in output


def test_remote_jobs_show_all_fields_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "inspect me", "--persist", "--json"])
    data_create = json.loads(capsys.readouterr().out)
    job_id = data_create["job"]["job_id"]

    main(["remote", "jobs", "show", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    job = data["job"]
    for field in (
        "job_id",
        "requested_agent",
        "requested_task",
        "execution_mode",
        "approval_state",
        "policy_compliance",
        "status",
        "created_at",
        "required_checks",
        "required_approvals",
        "safety_notes",
    ):
        assert field in job, f"missing field: {field}"


def test_remote_jobs_show_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "advisory check", "--persist", "--json"])
    data_create = json.loads(capsys.readouterr().out)
    job_id = data_create["job"]["job_id"]

    main(["remote", "jobs", "show", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert data["advisory"] == "Job inspection is read-only; no agents are executed."


def test_remote_jobs_show_advisory_in_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "human advisory", "--persist", "--json"])
    data_create = json.loads(capsys.readouterr().out)
    job_id = data_create["job"]["job_id"]

    main(["remote", "jobs", "show", job_id])

    output = capsys.readouterr().out
    assert "read-only" in output
    assert "no agents are executed" in output


def test_remote_jobs_show_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "readonly check", "--persist", "--json"])
    data_create = json.loads(capsys.readouterr().out)
    job_id = data_create["job"]["job_id"]
    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    files_before = set(p.name for p in jobs_dir.iterdir())

    main(["remote", "jobs", "show", job_id])
    capsys.readouterr()

    files_after = set(p.name for p in jobs_dir.iterdir())
    assert files_before == files_after


def test_remote_jobs_show_human_output_all_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "codex-local", "--prompt", "section check", "--persist", "--json"])
    data_create = json.loads(capsys.readouterr().out)
    job_id = data_create["job"]["job_id"]

    main(["remote", "jobs", "show", job_id])

    output = capsys.readouterr().out
    assert "Required checks" in output
    assert "Required approvals" in output
    assert "Safety notes" in output


# ---------------------------------------------------------------------------
# pcae remote approve / deny (Phase 40G)
# ---------------------------------------------------------------------------


def _create_job(tmp_path, monkeypatch, capsys, agent="codex-local", prompt="task") -> str:
    """Helper: persist a job and return its job_id. Drains capsys."""
    main(["remote", "create", "--agent", agent, "--prompt", prompt, "--persist", "--json"])
    data = json.loads(capsys.readouterr().out)
    return data["job"]["job_id"]


def test_remote_approve_pending_job_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "approve", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["updated"] is True
    assert data["new_approval_state"] == "approved"
    assert data["previous_approval_state"] == "pending"
    assert data["job"]["approval_state"] == "approved"
    assert "advisory" in data


def test_remote_deny_pending_job_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "deny", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["updated"] is True
    assert data["new_approval_state"] == "denied"
    assert data["previous_approval_state"] == "pending"
    assert data["job"]["approval_state"] == "denied"


def test_remote_approve_sets_status_ready_when_compliant(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    main(["remote", "jobs", "show", job_id, "--json"])
    job_before = json.loads(capsys.readouterr().out)["job"]
    compliant = job_before.get("policy_compliance", {}).get("compliant", False)

    main(["remote", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)
    expected_status = "ready" if compliant else "draft"
    assert data["job"]["status"] == expected_status


def test_remote_deny_sets_status_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    main(["remote", "deny", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["job"]["status"] == "blocked"


def test_remote_approve_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "approve", job_id])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert job_id in output
    assert "approved" in output
    assert "no agent execution has occurred" in output


def test_remote_deny_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "deny", job_id])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert job_id in output
    assert "denied" in output
    assert "no agent execution has occurred" in output


def test_remote_approve_unknown_job_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "approve", "job-00000000-000000-000000"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Unknown job" in output


def test_remote_deny_unknown_job_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "deny", "job-00000000-000000-000000"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Unknown job" in output


def test_remote_approve_malformed_job_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_id = "job-20260101-120000-000000"
    (jobs_dir / f"{job_id}.json").write_text("{bad", encoding="utf-8")

    exit_code = main(["remote", "approve", job_id])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Malformed" in output or "malformed" in output


def test_remote_approve_mutates_file_on_disk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    main(["remote", "approve", job_id, "--json"])
    capsys.readouterr()

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    stored = json.loads((jobs_dir / f"{job_id}.json").read_text(encoding="utf-8"))
    assert stored["approval_state"] == "approved"


def test_remote_deny_mutates_file_on_disk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    main(["remote", "deny", job_id, "--json"])
    capsys.readouterr()

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    stored = json.loads((jobs_dir / f"{job_id}.json").read_text(encoding="utf-8"))
    assert stored["approval_state"] == "denied"
    assert stored["status"] == "blocked"


def test_remote_approve_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    main(["remote", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["advisory"] == "Approval state updated; no agent execution has occurred."


# ---------------------------------------------------------------------------
# pcae remote ready (Phase 40H)
# ---------------------------------------------------------------------------


def _create_approved_job(tmp_path, monkeypatch, capsys, agent="codex-local") -> str:
    """Helper: persist and approve a job; return job_id. Drains capsys."""
    main(["remote", "create", "--agent", agent, "--prompt", "ready check task", "--persist", "--json"])
    job_id = json.loads(capsys.readouterr().out)["job"]["job_id"]
    main(["remote", "approve", job_id, "--json"])
    capsys.readouterr()
    return job_id


def test_remote_ready_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "ready", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in ("ready", "job_id", "requested_agent", "checks", "blockers", "warnings", "advisory"):
        assert key in data, f"missing key: {key}"


def test_remote_ready_approved_job_status_checks_pass(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    main(["remote", "ready", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["checks"]["approval_state_approved"] is True
    assert data["checks"]["status_ready"] is True
    assert data["checks"]["policy_compliance"] is True


def test_remote_ready_denied_job_is_not_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    main(["remote", "deny", job_id, "--json"])
    capsys.readouterr()

    main(["remote", "ready", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["ready"] is False
    assert data["checks"]["approval_state_approved"] is False
    assert data["checks"]["status_ready"] is False


def test_remote_ready_pending_job_is_not_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    main(["remote", "ready", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["ready"] is False
    assert any("approval_state" in b or "status" in b for b in data["blockers"])


def test_remote_ready_unknown_job_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "ready", "job-00000000-000000-000000"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Unknown job" in output


def test_remote_ready_malformed_job_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_id = "job-20260101-120000-000000"
    (jobs_dir / f"{job_id}.json").write_text("{bad json", encoding="utf-8")

    exit_code = main(["remote", "ready", job_id])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Malformed" in output or "malformed" in output


def test_remote_ready_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "ready", job_id])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert job_id in output
    assert "Execution readiness" in output
    assert "no agent is executed" in output


def test_remote_ready_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    main(["remote", "ready", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["advisory"] == "Execution readiness is advisory; no agent is executed."


def test_remote_ready_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)
    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    job_file = jobs_dir / f"{job_id}.json"
    content_before = job_file.read_text(encoding="utf-8")

    main(["remote", "ready", job_id, "--json"])
    capsys.readouterr()

    assert job_file.read_text(encoding="utf-8") == content_before


def test_remote_ready_checks_contains_expected_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    main(["remote", "ready", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)
    checks = data["checks"]
    for key in (
        "agent_allowed",
        "adapter_allowed",
        "approval_state_approved",
        "execution_mode_allowed",
        "git_working_tree_clean",
        "job_schema_valid",
        "non_interactive_supported",
        "pcae_check_required",
        "policy_compliance",
        "required_approvals_listed",
        "runtime_installed",
        "status_ready",
        "tests_required",
    ):
        assert key in checks, f"missing check: {key}"


def test_remote_ready_job_id_in_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    main(["remote", "ready", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["job_id"] == job_id
    assert data["requested_agent"] == "codex-local"


def test_remote_ready_schema_invalid_job_has_blocker(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_id = "job-20260101-120000-000002"
    (jobs_dir / f"{job_id}.json").write_text(
        json.dumps({"job_id": job_id, "approval_state": "approved", "status": "ready"}),
        encoding="utf-8",
    )

    main(["remote", "ready", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["ready"] is False
    assert data["checks"]["job_schema_valid"] is False
    assert any("missing schema fields" in b for b in data["blockers"])


# ---------------------------------------------------------------------------
# pcae remote execute --dry-run (Phase 41A)
# ---------------------------------------------------------------------------


def test_remote_execute_dry_run_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "execute", job_id, "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "advisory" in data
    assert "execution_preview" in data
    preview = data["execution_preview"]
    for key in (
        "job_id",
        "selected_agent",
        "execution_mode",
        "readiness_status",
        "prompt_preview",
        "command_preview",
        "required_checks",
        "required_approvals",
        "blockers",
        "safety_notes",
        "dry_run_result",
    ):
        assert key in preview, f"missing key in execution_preview: {key}"


def test_remote_execute_dry_run_approved_job_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    main(["remote", "execute", job_id, "--dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    preview = data["execution_preview"]

    assert preview["job_id"] == job_id
    assert preview["selected_agent"] == "codex-local"
    assert preview["prompt_preview"] != ""
    assert isinstance(preview["blockers"], list)
    assert isinstance(preview["safety_notes"], list)
    assert len(preview["safety_notes"]) > 0


def test_remote_execute_dry_run_denied_job_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)
    main(["remote", "deny", job_id, "--json"])
    capsys.readouterr()

    exit_code = main(["remote", "execute", job_id, "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    preview = data["execution_preview"]
    assert preview["readiness_status"] == "blocked"
    assert preview["dry_run_result"] == "blocked"
    assert len(preview["blockers"]) > 0


def test_remote_execute_dry_run_pending_job_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    main(["remote", "execute", job_id, "--dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    preview = data["execution_preview"]
    assert preview["dry_run_result"] == "blocked"
    assert any("approval_state" in b or "status" in b for b in preview["blockers"])


def test_remote_execute_missing_dry_run_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "execute", job_id])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "--dry-run" in output


def test_remote_execute_unknown_job_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "execute", "job-00000000-000000-000000", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Unknown job" in output


def test_remote_execute_dry_run_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "execute", job_id, "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote execution dry run" in output
    assert job_id in output
    assert "no agent was invoked" in output


def test_remote_execute_dry_run_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    main(["remote", "execute", job_id, "--dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["advisory"] == "Execution preview only; no agent was invoked."


def test_remote_execute_dry_run_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)
    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    job_file = jobs_dir / f"{job_id}.json"
    content_before = job_file.read_text(encoding="utf-8")

    main(["remote", "execute", job_id, "--dry-run", "--json"])
    capsys.readouterr()

    assert job_file.read_text(encoding="utf-8") == content_before


def test_remote_execute_dry_run_prompt_preview_truncated(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    long_prompt = "x" * 300
    main(["remote", "create", "--agent", "codex-local", "--prompt", long_prompt, "--persist", "--json"])
    job_id = json.loads(capsys.readouterr().out)["job"]["job_id"]
    main(["remote", "approve", job_id, "--json"])
    capsys.readouterr()

    main(["remote", "execute", job_id, "--dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert len(data["execution_preview"]["prompt_preview"]) <= 200


def test_remote_execute_dry_run_command_preview_for_cli_agent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    main(["remote", "execute", job_id, "--dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    cmd = data["execution_preview"]["command_preview"]
    assert cmd is not None
    assert "codex" in cmd
    assert "exec" in cmd
    assert "sandbox" in cmd
    assert "--quiet" not in cmd


def test_remote_execute_dry_run_safety_notes_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    main(["remote", "execute", job_id, "--dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    notes = data["execution_preview"]["safety_notes"]
    assert any("No agent was executed" in n for n in notes)
    assert any("preview only" in n for n in notes)


# ---------------------------------------------------------------------------
# pcae remote execute --invoke (Phase 41B)
# ---------------------------------------------------------------------------

import subprocess as _subprocess_mod
from pcae.core import agent as _agent_mod
from pcae.core.agent import (
    AgentRuntimeCapabilities,
    AgentRuntimeEntry,
    RuntimeDiscoveryResult,
    RUNTIME_CAP_YES,
    RUNTIME_CAP_UNKNOWN,
    RUNTIME_DISCOVERY_ADVISORY,
)


def _make_installed_discovery(agent_id: str) -> RuntimeDiscoveryResult:
    caps = AgentRuntimeCapabilities(
        installed=True,
        executable_path=f"/usr/local/bin/{agent_id.split('-')[0]}",
        version="test-1.0.0",
        interactive_supported=RUNTIME_CAP_YES,
        non_interactive_supported=RUNTIME_CAP_YES,
        stdin_prompt_supported=RUNTIME_CAP_YES,
        prompt_file_supported=RUNTIME_CAP_YES,
        structured_output_supported=RUNTIME_CAP_YES,
        mcp_supported=RUNTIME_CAP_YES,
        hooks_supported=RUNTIME_CAP_YES,
        subagents_supported=RUNTIME_CAP_YES,
        remote_supported=RUNTIME_CAP_YES,
        known_limitations=(),
    )
    entry = AgentRuntimeEntry(
        agent_id=agent_id,
        executable=f"/usr/local/bin/{agent_id.split('-')[0]}",
        capabilities=caps,
    )
    return RuntimeDiscoveryResult(agents=(entry,), advisory=RUNTIME_DISCOVERY_ADVISORY)


def _fake_proc(rc: int = 0, stdout: str = "ok\n", stderr: str = "") -> _subprocess_mod.CompletedProcess:
    return _subprocess_mod.CompletedProcess(args=[], returncode=rc, stdout=stdout, stderr=stderr)


def test_remote_invoke_missing_flags_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "execute", job_id])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "--dry-run" in output or "--invoke" in output


def test_remote_invoke_unknown_job_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "execute", "job-00000000-000000-000000", "--invoke"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Unknown job" in output


def test_remote_invoke_pending_job_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "execute", job_id, "--invoke"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "not ready" in output.lower() or "Blockers" in output or "approval_state" in output


def test_remote_invoke_denied_job_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)
    main(["remote", "deny", job_id, "--json"])
    capsys.readouterr()

    exit_code = main(["remote", "execute", job_id, "--invoke"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "not ready" in output.lower() or "Blockers" in output or "approval_state" in output


def test_remote_invoke_runtime_not_installed_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "execute", job_id, "--invoke"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "not ready" in output.lower() or "runtime" in output.lower()


def _patch_ready(monkeypatch, agent_id: str = "codex-local") -> None:
    """Patch discovery and git to make the readiness gate pass in tests."""
    monkeypatch.setattr(_agent_mod, "build_runtime_discovery", lambda: _make_installed_discovery(agent_id))
    monkeypatch.setattr(_agent_mod, "read_git_changes", lambda root: ())


def test_remote_invoke_success_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    _patch_ready(monkeypatch)
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "Agent output\n"))

    exit_code = main(["remote", "execute", job_id, "--invoke", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in ("executed", "job_id", "selected_agent", "command", "exit_code", "stdout", "stderr", "output_path", "final_status", "advisory"):
        assert key in data, f"missing key: {key}"
    assert data["executed"] is True
    assert data["exit_code"] == 0
    assert data["final_status"] == "completed"
    assert data["job_id"] == job_id
    assert data["command"][:4] == ["codex", "exec", "--sandbox", "read-only"]
    assert "--quiet" not in data["command"]


def test_remote_invoke_success_status_completed_on_disk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    _patch_ready(monkeypatch)
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0))

    main(["remote", "execute", job_id, "--invoke", "--json"])
    capsys.readouterr()

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    stored = json.loads((jobs_dir / f"{job_id}.json").read_text(encoding="utf-8"))
    assert stored["status"] == "completed"


def test_remote_invoke_failure_status_failed_on_disk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    _patch_ready(monkeypatch)
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(1, stderr="error\n"))

    main(["remote", "execute", job_id, "--invoke", "--json"])
    capsys.readouterr()

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    stored = json.loads((jobs_dir / f"{job_id}.json").read_text(encoding="utf-8"))
    assert stored["status"] == "failed"


def test_remote_invoke_artifact_written(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    _patch_ready(monkeypatch)
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "done\n"))

    main(["remote", "execute", job_id, "--invoke", "--json"])
    data = json.loads(capsys.readouterr().out)

    artifact = tmp_path / ".pcae" / "remote" / "executions" / f"{job_id}_result.json"
    assert artifact.exists()
    stored = json.loads(artifact.read_text(encoding="utf-8"))
    assert stored["executed"] is True
    assert stored["job_id"] == job_id
    assert data["output_path"].endswith(f"{job_id}_result.json")


def test_remote_invoke_no_commit_no_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    import subprocess as sp
    log_before = sp.run(["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True).stdout

    _patch_ready(monkeypatch)
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0))

    main(["remote", "execute", job_id, "--invoke", "--json"])
    capsys.readouterr()

    log_after = sp.run(["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True).stdout
    assert log_before == log_after


def test_remote_invoke_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    _patch_ready(monkeypatch)
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0))

    main(["remote", "execute", job_id, "--invoke", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "no commit or push was performed" in data["advisory"]


def test_remote_invoke_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    _patch_ready(monkeypatch)
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "Task done.\n"))

    exit_code = main(["remote", "execute", job_id, "--invoke"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote execution result" in output
    assert job_id in output
    assert "no commit or push was performed" in output


def test_remote_invoke_kimi_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "kimi-local", "--prompt", "report task", "--persist", "--json"])
    job_id = json.loads(capsys.readouterr().out)["job"]["job_id"]
    main(["remote", "approve", job_id, "--json"])
    capsys.readouterr()

    _patch_ready(monkeypatch, "kimi-local")
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0))

    exit_code = main(["remote", "execute", job_id, "--invoke"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "kimi-local" in output or "syntax" in output.lower() or "safely derivable" in output.lower()


def test_remote_invoke_dry_run_still_works(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "execute", job_id, "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "execution_preview" in data


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
