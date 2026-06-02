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

    artifact = tmp_path / ".pcae" / "remote" / "results" / f"{job_id}-result.json"
    assert artifact.exists()
    stored = json.loads(artifact.read_text(encoding="utf-8"))
    assert stored["executed"] is True
    assert stored["job_id"] == job_id
    assert data["output_path"].endswith(f"{job_id}-result.json")


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


def test_remote_invoke_kimi_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "create", "--agent", "kimi-local", "--prompt", "report task", "--persist", "--json"])
    job_id = json.loads(capsys.readouterr().out)["job"]["job_id"]
    main(["remote", "approve", job_id, "--json"])
    capsys.readouterr()

    _patch_ready(monkeypatch, "kimi-local")
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "PCAE Kimi execution test successful.\n"))

    exit_code = main(["remote", "execute", job_id, "--invoke", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["executed"] is True
    assert data["command"][:2] == ["kimi", "-p"]


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


# ---------------------------------------------------------------------------
# Phase 41B.3: Claude Adapter Contract Validation
# ---------------------------------------------------------------------------


def test_remote_execute_dry_run_command_preview_claude_uses_dash_p(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")

    _patch_ready(monkeypatch, "claude-local")

    main(["remote", "execute", job_id, "--dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    cmd = data["execution_preview"]["command_preview"]
    assert cmd is not None
    assert "claude" in cmd
    assert "-p" in cmd
    assert "--print" not in cmd
    assert "--prompt" not in cmd


def test_remote_invoke_claude_command_uses_dash_p(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")

    _patch_ready(monkeypatch, "claude-local")
    monkeypatch.setattr(
        _agent_mod,
        "_run_agent_subprocess",
        lambda cmd, timeout: _fake_proc(0, "PCAE Claude execution test successful.\n"),
    )

    main(["remote", "execute", job_id, "--invoke", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["executed"] is True
    assert data["command"][0] == "claude"
    assert data["command"][1] == "-p"
    assert "--print" not in data["command"]


# ---------------------------------------------------------------------------
# Phase 41B.4: Kimi Adapter Contract Correction
# ---------------------------------------------------------------------------


def test_remote_execute_dry_run_command_preview_kimi_uses_dash_p(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="kimi-local")

    _patch_ready(monkeypatch, "kimi-local")

    main(["remote", "execute", job_id, "--dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    cmd = data["execution_preview"]["command_preview"]
    assert cmd is not None
    assert "kimi" in cmd
    assert "-p" in cmd
    assert "--prompt" not in cmd
    assert "--yolo" not in cmd
    assert "--auto" not in cmd


def test_remote_invoke_kimi_command_uses_dash_p(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="kimi-local")

    _patch_ready(monkeypatch, "kimi-local")
    monkeypatch.setattr(
        _agent_mod,
        "_run_agent_subprocess",
        lambda cmd, timeout: _fake_proc(0, "PCAE Kimi execution test successful.\n"),
    )

    main(["remote", "execute", job_id, "--invoke", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["executed"] is True
    assert data["command"][0] == "kimi"
    assert data["command"][1] == "-p"
    assert "--yolo" not in data["command"]
    assert "--auto" not in data["command"]


def test_remote_invoke_codex_adapter_unchanged_after_kimi_fix(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="codex-local")

    _patch_ready(monkeypatch, "codex-local")
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0))

    main(["remote", "execute", job_id, "--invoke", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["command"][:4] == ["codex", "exec", "--sandbox", "read-only"]


def test_remote_invoke_claude_adapter_unchanged_after_kimi_fix(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")

    _patch_ready(monkeypatch, "claude-local")
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0))

    main(["remote", "execute", job_id, "--invoke", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["command"][:2] == ["claude", "-p"]
    assert "--print" not in data["command"]


# ---------------------------------------------------------------------------
# Phase 41C: Governed Execution Reporting
# ---------------------------------------------------------------------------


def test_remote_results_unknown_job_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "results", "job-00000000-000000-000000"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Unknown job" in output


def test_remote_results_no_execution_artifact(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "results", job_id])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "no execution result available" in output
    assert job_id in output


def test_remote_results_no_execution_artifact_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "results", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["result_available"] is False
    assert data["job_id"] == job_id
    assert data["execution_result"] is None
    assert "advisory" in data
    assert "Execution reporting is read-only" in data["advisory"]


def _invoke_job(tmp_path, monkeypatch, capsys, agent="codex-local") -> str:
    """Helper: create, approve, and invoke a job; return job_id."""
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent=agent)
    _patch_ready(monkeypatch, agent)
    monkeypatch.setattr(
        _agent_mod,
        "_run_agent_subprocess",
        lambda cmd, timeout: _fake_proc(0, "Task output.\n"),
    )
    main(["remote", "execute", job_id, "--invoke", "--json"])
    capsys.readouterr()
    return job_id


def test_remote_results_after_invoke_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "results", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["result_available"] is True
    assert data["job_id"] == job_id
    assert data["requested_agent"] == "codex-local"
    assert "advisory" in data
    assert "Execution reporting is read-only" in data["advisory"]
    result = data["execution_result"]
    assert result is not None
    for key in (
        "command_used", "duration_seconds", "execution_finished_at",
        "execution_started_at", "exit_code", "final_status",
        "output_path", "readiness_at_execution",
        "stderr_summary", "stdout_summary",
    ):
        assert key in result, f"missing key: {key}"
    assert result["exit_code"] == 0
    assert result["final_status"] == "completed"
    assert result["command_used"] is not None
    assert result["output_path"].endswith(f"{job_id}-result.json")


def test_remote_results_after_invoke_human(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "results", job_id])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Execution results" in output
    assert job_id in output
    assert "completed" in output
    assert "Execution reporting is read-only" in output


def test_remote_results_failed_job_reports_failed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)
    _patch_ready(monkeypatch)
    monkeypatch.setattr(
        _agent_mod,
        "_run_agent_subprocess",
        lambda cmd, timeout: _fake_proc(1, stderr="execution error\n"),
    )
    main(["remote", "execute", job_id, "--invoke", "--json"])
    capsys.readouterr()

    exit_code = main(["remote", "results", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["result_available"] is True
    assert data["execution_result"]["exit_code"] == 1
    assert data["execution_result"]["final_status"] == "failed"


def test_remote_results_is_readonly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job(tmp_path, monkeypatch, capsys)

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    before = (jobs_dir / f"{job_id}.json").read_text(encoding="utf-8")

    main(["remote", "results", job_id, "--json"])
    capsys.readouterr()

    after = (jobs_dir / f"{job_id}.json").read_text(encoding="utf-8")
    assert before == after


# ---------------------------------------------------------------------------
# Phase 41D: Execution Result Persistence
# ---------------------------------------------------------------------------


def test_remote_invoke_persists_to_results_dir(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    _patch_ready(monkeypatch)
    monkeypatch.setattr(
        _agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "ok\n")
    )

    main(["remote", "execute", job_id, "--invoke", "--json"])
    capsys.readouterr()

    artifact = tmp_path / ".pcae" / "remote" / "results" / f"{job_id}-result.json"
    assert artifact.exists()
    stored = json.loads(artifact.read_text(encoding="utf-8"))
    assert stored["job_id"] == job_id
    assert stored["executed"] is True


def test_remote_invoke_result_has_timing_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    _patch_ready(monkeypatch)
    monkeypatch.setattr(
        _agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "ok\n")
    )

    main(["remote", "execute", job_id, "--invoke", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "started_at" in data
    assert "finished_at" in data
    assert "duration_seconds" in data
    assert data["started_at"] is not None
    assert data["finished_at"] is not None
    assert isinstance(data["duration_seconds"], (int, float))
    assert data["duration_seconds"] >= 0


def test_remote_invoke_job_updated_with_result_path_and_executed_at(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    _patch_ready(monkeypatch)
    monkeypatch.setattr(
        _agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0)
    )

    main(["remote", "execute", job_id, "--invoke", "--json"])
    capsys.readouterr()

    jobs_dir = tmp_path / ".pcae" / "remote" / "jobs"
    stored = json.loads((jobs_dir / f"{job_id}.json").read_text(encoding="utf-8"))
    assert "result_path" in stored
    assert "executed_at" in stored
    assert stored["result_path"].endswith(f"{job_id}-result.json")
    assert stored["executed_at"] is not None


def test_remote_invoke_result_artifact_preserves_full_stdout(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    long_output = "x" * 2000
    _patch_ready(monkeypatch)
    monkeypatch.setattr(
        _agent_mod,
        "_run_agent_subprocess",
        lambda cmd, timeout: _fake_proc(0, long_output),
    )

    main(["remote", "execute", job_id, "--invoke", "--json"])
    capsys.readouterr()

    artifact = tmp_path / ".pcae" / "remote" / "results" / f"{job_id}-result.json"
    stored = json.loads(artifact.read_text(encoding="utf-8"))
    assert stored["stdout"] == long_output


def test_remote_results_timing_fields_populated_after_invoke(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "results", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    result = data["execution_result"]
    assert result["execution_started_at"] is not None
    assert result["execution_finished_at"] is not None
    assert result["duration_seconds"] is not None
    assert isinstance(result["duration_seconds"], (int, float))


def test_remote_invoke_human_output_shows_timing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)

    _patch_ready(monkeypatch)
    monkeypatch.setattr(
        _agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "done\n")
    )

    exit_code = main(["remote", "execute", job_id, "--invoke"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Started at:" in output
    assert "Duration:" in output


# ---------------------------------------------------------------------------
# Phase 41E: Multi-Runtime Execution Validation
# ---------------------------------------------------------------------------

_VALIDATION_PROMPT_TEMPLATE = (
    "Read-only task: reply with exactly:\n"
    "PCAE {runtime} execution validation successful.\n"
    "Do not modify files."
)

_VALIDATION_EXPECTED_OUTPUT_TEMPLATE = (
    "PCAE {runtime} execution validation successful.\n"
)


def _make_validation_proc(runtime_name: str) -> _subprocess_mod.CompletedProcess:
    stdout = _VALIDATION_EXPECTED_OUTPUT_TEMPLATE.format(runtime=runtime_name)
    return _fake_proc(0, stdout)


def _run_validated_lifecycle(
    tmp_path: Path,
    monkeypatch,
    capsys,
    agent_id: str,
    runtime_name: str,
) -> tuple[str, dict, dict]:
    """Full lifecycle helper for validation. Returns (job_id, exec_data, results_data)."""
    prompt = _VALIDATION_PROMPT_TEMPLATE.format(runtime=runtime_name)

    main(["remote", "create", "--agent", agent_id, "--prompt", prompt, "--persist", "--json"])
    job_id = json.loads(capsys.readouterr().out)["job"]["job_id"]

    main(["remote", "approve", job_id, "--json"])
    capsys.readouterr()

    _patch_ready(monkeypatch, agent_id)
    monkeypatch.setattr(
        _agent_mod,
        "_run_agent_subprocess",
        lambda cmd, timeout: _make_validation_proc(runtime_name),
    )

    main(["remote", "execute", job_id, "--invoke", "--json"])
    exec_data = json.loads(capsys.readouterr().out)

    main(["remote", "results", job_id, "--json"])
    results_data = json.loads(capsys.readouterr().out)

    return job_id, exec_data, results_data


# ---- Full lifecycle: claude-local ----------------------------------------

def test_41e_claude_local_job_creation_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    prompt = _VALIDATION_PROMPT_TEMPLATE.format(runtime="claude")

    exit_code = main(["remote", "create", "--agent", "claude-local", "--prompt", prompt, "--persist", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["persisted"] is True
    assert data["job"]["requested_agent"] == "claude-local"


def test_41e_claude_local_approval_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys, agent="claude-local")

    exit_code = main(["remote", "approve", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["new_approval_state"] == "approved"


def test_41e_claude_local_readiness_gate_passes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")

    _patch_ready(monkeypatch, "claude-local")
    exit_code = main(["remote", "ready", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["ready"] is True
    assert data["blockers"] == []


def test_41e_claude_local_full_lifecycle(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    import subprocess as sp
    log_before = sp.run(
        ["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True
    ).stdout

    job_id, exec_data, results_data = _run_validated_lifecycle(
        tmp_path, monkeypatch, capsys, "claude-local", "claude"
    )

    # exit code and final status
    assert exec_data["exit_code"] == 0
    assert exec_data["final_status"] == "completed"

    # artifact persisted
    artifact = tmp_path / ".pcae" / "remote" / "results" / f"{job_id}-result.json"
    assert artifact.exists()

    # results reporting
    assert results_data["result_available"] is True
    assert results_data["execution_result"]["final_status"] == "completed"

    # no commit
    log_after = sp.run(
        ["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True
    ).stdout
    assert log_before == log_after


# ---- Full lifecycle: kimi-local ------------------------------------------

def test_41e_kimi_local_job_creation_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    prompt = _VALIDATION_PROMPT_TEMPLATE.format(runtime="kimi")

    exit_code = main(["remote", "create", "--agent", "kimi-local", "--prompt", prompt, "--persist", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["persisted"] is True
    assert data["job"]["requested_agent"] == "kimi-local"


def test_41e_kimi_local_approval_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_job(tmp_path, monkeypatch, capsys, agent="kimi-local")

    exit_code = main(["remote", "approve", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["new_approval_state"] == "approved"


def test_41e_kimi_local_readiness_gate_passes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="kimi-local")

    _patch_ready(monkeypatch, "kimi-local")
    exit_code = main(["remote", "ready", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["ready"] is True
    assert data["blockers"] == []


def test_41e_kimi_local_full_lifecycle(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    import subprocess as sp
    log_before = sp.run(
        ["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True
    ).stdout

    job_id, exec_data, results_data = _run_validated_lifecycle(
        tmp_path, monkeypatch, capsys, "kimi-local", "kimi"
    )

    assert exec_data["exit_code"] == 0
    assert exec_data["final_status"] == "completed"

    artifact = tmp_path / ".pcae" / "remote" / "results" / f"{job_id}-result.json"
    assert artifact.exists()

    assert results_data["result_available"] is True
    assert results_data["execution_result"]["final_status"] == "completed"

    log_after = sp.run(
        ["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True
    ).stdout
    assert log_before == log_after


# ---- Result persistence --------------------------------------------------

def test_41e_result_persistence_claude_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job_id, exec_data, _ = _run_validated_lifecycle(
        tmp_path, monkeypatch, capsys, "claude-local", "claude"
    )

    artifact = tmp_path / ".pcae" / "remote" / "results" / f"{job_id}-result.json"
    assert artifact.exists()
    stored = json.loads(artifact.read_text(encoding="utf-8"))
    assert stored["job_id"] == job_id
    assert stored["selected_agent"] == "claude-local"
    assert stored["executed"] is True
    assert stored["exit_code"] == 0
    assert stored["final_status"] == "completed"
    assert "started_at" in stored
    assert "finished_at" in stored
    assert "duration_seconds" in stored
    expected = _VALIDATION_EXPECTED_OUTPUT_TEMPLATE.format(runtime="claude")
    assert stored["stdout"] == expected


def test_41e_result_persistence_kimi_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job_id, exec_data, _ = _run_validated_lifecycle(
        tmp_path, monkeypatch, capsys, "kimi-local", "kimi"
    )

    artifact = tmp_path / ".pcae" / "remote" / "results" / f"{job_id}-result.json"
    assert artifact.exists()
    stored = json.loads(artifact.read_text(encoding="utf-8"))
    assert stored["job_id"] == job_id
    assert stored["selected_agent"] == "kimi-local"
    assert stored["executed"] is True
    assert stored["exit_code"] == 0
    assert stored["final_status"] == "completed"
    assert "started_at" in stored
    assert "finished_at" in stored
    assert "duration_seconds" in stored
    expected = _VALIDATION_EXPECTED_OUTPUT_TEMPLATE.format(runtime="kimi")
    assert stored["stdout"] == expected


# ---- Reporting -----------------------------------------------------------

def test_41e_reporting_claude_local_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job_id, _, results_data = _run_validated_lifecycle(
        tmp_path, monkeypatch, capsys, "claude-local", "claude"
    )

    assert results_data["result_available"] is True
    assert results_data["job_id"] == job_id
    assert results_data["requested_agent"] == "claude-local"
    result = results_data["execution_result"]
    assert result["exit_code"] == 0
    assert result["final_status"] == "completed"
    assert result["execution_started_at"] is not None
    assert result["duration_seconds"] is not None
    assert result["output_path"].endswith(f"{job_id}-result.json")


def test_41e_reporting_kimi_local_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job_id, _, results_data = _run_validated_lifecycle(
        tmp_path, monkeypatch, capsys, "kimi-local", "kimi"
    )

    assert results_data["result_available"] is True
    assert results_data["job_id"] == job_id
    assert results_data["requested_agent"] == "kimi-local"
    result = results_data["execution_result"]
    assert result["exit_code"] == 0
    assert result["final_status"] == "completed"
    assert result["execution_started_at"] is not None
    assert result["duration_seconds"] is not None
    assert result["output_path"].endswith(f"{job_id}-result.json")


def test_41e_reporting_human_output_claude(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id, _, _ = _run_validated_lifecycle(
        tmp_path, monkeypatch, capsys, "claude-local", "claude"
    )

    exit_code = main(["remote", "results", job_id])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Execution results" in output
    assert job_id in output
    assert "completed" in output
    assert "Execution reporting is read-only" in output


def test_41e_reporting_human_output_kimi(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id, _, _ = _run_validated_lifecycle(
        tmp_path, monkeypatch, capsys, "kimi-local", "kimi"
    )

    exit_code = main(["remote", "results", job_id])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Execution results" in output
    assert job_id in output
    assert "completed" in output
    assert "Execution reporting is read-only" in output


# ---- Adapter selection ---------------------------------------------------

def test_41e_adapter_command_claude_local_uses_dash_p(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")

    _patch_ready(monkeypatch, "claude-local")
    monkeypatch.setattr(
        _agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "ok\n")
    )

    main(["remote", "execute", job_id, "--invoke", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["command"][0] == "claude"
    assert data["command"][1] == "-p"
    assert "--print" not in data["command"]


def test_41e_adapter_command_kimi_local_uses_dash_p(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="kimi-local")

    _patch_ready(monkeypatch, "kimi-local")
    monkeypatch.setattr(
        _agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "ok\n")
    )

    main(["remote", "execute", job_id, "--invoke", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["command"][0] == "kimi"
    assert data["command"][1] == "-p"
    assert "--yolo" not in data["command"]
    assert "--auto" not in data["command"]


def test_41e_adapters_are_runtime_specific(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Claude and Kimi must use distinct commands; neither may use the other's executable."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    # Execute claude-local and capture command
    job_id_claude = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")
    _patch_ready(monkeypatch, "claude-local")
    monkeypatch.setattr(
        _agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "ok\n")
    )
    main(["remote", "execute", job_id_claude, "--invoke", "--json"])
    claude_data = json.loads(capsys.readouterr().out)

    # Execute kimi-local and capture command
    job_id_kimi = _create_approved_job(tmp_path, monkeypatch, capsys, agent="kimi-local")
    _patch_ready(monkeypatch, "kimi-local")
    main(["remote", "execute", job_id_kimi, "--invoke", "--json"])
    kimi_data = json.loads(capsys.readouterr().out)

    assert claude_data["command"][0] == "claude"
    assert kimi_data["command"][0] == "kimi"
    assert claude_data["command"][0] != kimi_data["command"][0]
    assert claude_data["selected_agent"] != kimi_data["selected_agent"]


# ---------------------------------------------------------------------------
# Phase 41F: Execution Output Normalization
# ---------------------------------------------------------------------------


def _invoke_job_with_output(
    tmp_path: Path,
    monkeypatch,
    capsys,
    agent: str,
    rc: int = 0,
    stdout: str = "ok\n",
    stderr: str = "",
) -> str:
    """Create, approve, and invoke a job for agent with given subprocess output. Returns job_id."""
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent=agent)
    _patch_ready(monkeypatch, agent)
    monkeypatch.setattr(
        _agent_mod,
        "_run_agent_subprocess",
        lambda cmd, timeout: _fake_proc(rc, stdout, stderr),
    )
    main(["remote", "execute", job_id, "--invoke", "--json"])
    capsys.readouterr()
    return job_id


def test_41f_codex_clean_stdout_classification(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path, monkeypatch, capsys, "codex-local", stdout="Codex answer.\n"
    )

    main(["remote", "results", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    result = data["execution_result"]
    assert result["output_classification"] == "clean_stdout"
    assert result["normalized_final_output"] == "Codex answer."
    assert result["stdout_summary"] is not None
    assert result["stderr_summary"] is None


def test_41f_claude_clean_stdout_classification(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path, monkeypatch, capsys, "claude-local", stdout="Claude answer.\n"
    )

    main(["remote", "results", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    result = data["execution_result"]
    assert result["output_classification"] == "clean_stdout"
    assert result["normalized_final_output"] == "Claude answer."


def test_41f_kimi_stderr_status_text_classification(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path,
        monkeypatch,
        capsys,
        "kimi-local",
        stdout="Kimi final answer.\n",
        stderr="Thinking... reasoning step 1\nreasoning step 2\n",
    )

    main(["remote", "results", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    result = data["execution_result"]
    assert result["output_classification"] == "stderr_with_status_text"
    assert result["normalized_final_output"] == "Kimi final answer."
    assert result["stderr_summary"] is not None
    assert "Thinking" in result["stderr_summary"]


def test_41f_empty_output_classification(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path, monkeypatch, capsys, "codex-local", stdout="", stderr=""
    )

    main(["remote", "results", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    result = data["execution_result"]
    assert result["output_classification"] == "empty_output"
    assert result["normalized_final_output"] is None


def test_41f_execution_error_classification(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path,
        monkeypatch,
        capsys,
        "codex-local",
        rc=1,
        stdout="partial output\n",
        stderr="error: something failed\n",
    )

    main(["remote", "results", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    result = data["execution_result"]
    assert result["output_classification"] == "execution_error"
    assert result["normalized_final_output"] is None


def test_41f_json_includes_normalized_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n"
    )

    main(["remote", "results", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    result = data["execution_result"]
    assert "output_classification" in result
    assert "normalized_final_output" in result
    assert "stdout_summary" in result
    assert "stderr_summary" in result


def test_41f_raw_stdout_stderr_preserved_in_artifact(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path,
        monkeypatch,
        capsys,
        "codex-local",
        stdout="raw answer\n",
        stderr="raw status\n",
    )

    results_file = tmp_path / ".pcae" / "remote" / "results" / f"{job_id}-result.json"
    artifact = json.loads(results_file.read_text(encoding="utf-8"))
    assert artifact["stdout"] == "raw answer\n"
    assert artifact["stderr"] == "raw status\n"


def test_41f_human_output_shows_classification_and_normalized(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path, monkeypatch, capsys, "codex-local", stdout="human answer\n"
    )

    main(["remote", "results", job_id])
    output = capsys.readouterr().out

    assert "Output classification:" in output
    assert "clean_stdout" in output
    assert "Normalized final output:" in output
    assert "human answer" in output


def test_41f_kimi_stderr_only_normalized_output_is_none(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """When Kimi emits only stderr and stdout is empty, normalized_final_output is None."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path,
        monkeypatch,
        capsys,
        "kimi-local",
        stdout="",
        stderr="status text only\n",
    )

    main(["remote", "results", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    result = data["execution_result"]
    assert result["output_classification"] == "stderr_with_status_text"
    assert result["normalized_final_output"] is None


# ---------------------------------------------------------------------------
# Phase 41G: Remote Execution Result Registry
# ---------------------------------------------------------------------------


def test_41g_registry_empty_directory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "results"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Execution result registry" in output
    assert "Result count: 0" in output
    assert "Execution result registry is read-only" in output


def test_41g_registry_empty_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "results", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["result_count"] == 0
    assert data["results"] == []
    assert data["warnings"] == []
    assert "Execution result registry is read-only" in data["advisory"]


def test_41g_registry_lists_results(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="answer\n")

    exit_code = main(["remote", "results"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Result count: 1" in output
    assert "codex-local" in output
    assert "completed" in output
    assert "clean_stdout" in output


def test_41g_registry_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path, monkeypatch, capsys, "codex-local", stdout="answer\n"
    )

    exit_code = main(["remote", "results", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["result_count"] == 1
    assert len(data["results"]) == 1
    assert data["warnings"] == []
    assert "advisory" in data
    entry = data["results"][0]
    for key in (
        "job_id", "selected_agent", "final_status", "exit_code",
        "duration_seconds", "output_classification", "output_path", "finished_at",
    ):
        assert key in entry, f"missing key: {key}"
    assert entry["job_id"] == job_id
    assert entry["selected_agent"] == "codex-local"
    assert entry["final_status"] == "completed"
    assert entry["exit_code"] == 0
    assert entry["output_classification"] == "clean_stdout"


def test_41g_registry_sorted_newest_first(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job_id_1 = _invoke_job_with_output(
        tmp_path, monkeypatch, capsys, "codex-local", stdout="first\n"
    )
    job_id_2 = _invoke_job_with_output(
        tmp_path, monkeypatch, capsys, "claude-local", stdout="second\n"
    )

    exit_code = main(["remote", "results", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["result_count"] == 2
    ids = [e["job_id"] for e in data["results"]]
    assert ids.index(job_id_2) < ids.index(job_id_1), "newer job should appear first"


def test_41g_registry_malformed_file_warns(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / ".pcae" / "remote" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "job-bad-result.json").write_text("not valid json", encoding="utf-8")

    exit_code = main(["remote", "results", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["result_count"] == 0
    assert len(data["warnings"]) == 1
    assert "job-bad-result.json" in data["warnings"][0]


def test_41g_registry_includes_output_classification(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(
        tmp_path,
        monkeypatch,
        capsys,
        "kimi-local",
        stdout="kimi answer\n",
        stderr="thinking...\n",
    )

    exit_code = main(["remote", "results", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["results"][0]["output_classification"] == "stderr_with_status_text"


def test_41g_job_id_still_works(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n"
    )

    exit_code = main(["remote", "results", job_id, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["result_available"] is True
    assert data["job_id"] == job_id


def test_41g_registry_readonly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _invoke_job_with_output(
        tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n"
    )

    results_dir = tmp_path / ".pcae" / "remote" / "results"
    before = {f.name: f.read_text() for f in results_dir.glob("*.json")}

    main(["remote", "results", "--json"])
    capsys.readouterr()

    after = {f.name: f.read_text() for f in results_dir.glob("*.json")}
    assert before == after


# ---------------------------------------------------------------------------
# Phase 41H: Execution Analytics
# ---------------------------------------------------------------------------


def test_41h_analytics_empty_registry(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "analytics"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Execution analytics summary" in output
    assert "Total executions:       0" in output
    assert "Execution analytics are computed from persisted result artifacts." in output


def test_41h_analytics_empty_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "analytics", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    a = data["analytics"]
    assert a["total_executions"] == 0
    assert a["successful_executions"] == 0
    assert a["failed_executions"] == 0
    assert a["success_rate"] is None
    assert a["average_duration_seconds"] is None
    assert a["fastest_execution"] is None
    assert a["slowest_execution"] is None
    assert a["latest_execution"] is None
    assert data["runtime_metrics"] == {}
    assert data["warnings"] == []
    assert "advisory" in data


def test_41h_analytics_global_metrics(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "claude-local", rc=1, stdout="", stderr="err\n")

    exit_code = main(["remote", "analytics", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    a = data["analytics"]
    assert a["total_executions"] == 2
    assert a["successful_executions"] == 1
    assert a["failed_executions"] == 1
    assert a["success_rate"] == 0.5
    assert a["average_duration_seconds"] is not None
    assert a["fastest_execution"] is not None
    assert a["slowest_execution"] is not None
    assert a["latest_execution"] is not None


def test_41h_analytics_success_rate_all_pass(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "analytics", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["analytics"]["success_rate"] == 1.0
    assert data["analytics"]["failed_executions"] == 0


def test_41h_analytics_per_runtime_metrics(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "claude-local", stdout="ok\n")
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "kimi-local", stdout="ok\n", stderr="thinking\n")

    exit_code = main(["remote", "analytics", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    rm = data["runtime_metrics"]
    for agent in ("codex-local", "claude-local", "kimi-local"):
        assert agent in rm, f"missing runtime: {agent}"
        m = rm[agent]
        assert m["executions"] == 1
        assert m["successes"] == 1
        assert m["failures"] == 0
        assert "average_duration" in m


def test_41h_analytics_per_runtime_failure_counted(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", rc=1, stderr="fail\n")

    exit_code = main(["remote", "analytics", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    m = data["runtime_metrics"]["codex-local"]
    assert m["failures"] == 1
    assert m["successes"] == 0


def test_41h_analytics_fastest_slowest(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "claude-local", stdout="ok\n")

    exit_code = main(["remote", "analytics", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    a = data["analytics"]
    assert a["fastest_execution"]["duration_seconds"] <= a["slowest_execution"]["duration_seconds"]
    for key in ("job_id", "selected_agent", "duration_seconds", "final_status"):
        assert key in a["fastest_execution"]
        assert key in a["slowest_execution"]


def test_41h_analytics_latest_execution_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "analytics", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    latest = data["analytics"]["latest_execution"]
    assert latest is not None
    for key in ("job_id", "selected_agent", "final_status", "finished_at"):
        assert key in latest


def test_41h_analytics_malformed_file_warns(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / ".pcae" / "remote" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "job-bad-result.json").write_text("not json", encoding="utf-8")

    exit_code = main(["remote", "analytics", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["analytics"]["total_executions"] == 0
    assert len(data["warnings"]) == 1
    assert "job-bad-result.json" in data["warnings"][0]


def test_41h_analytics_human_output_shows_runtime_breakdown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "analytics"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Runtime breakdown" in output
    assert "codex-local" in output
    assert "Successes:" in output
    assert "Execution analytics are computed from persisted result artifacts." in output


def test_41h_analytics_readonly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    results_dir = tmp_path / ".pcae" / "remote" / "results"
    before = {f.name: f.read_text() for f in results_dir.glob("*.json")}

    main(["remote", "analytics", "--json"])
    capsys.readouterr()

    after = {f.name: f.read_text() for f in results_dir.glob("*.json")}
    assert before == after


# ---------------------------------------------------------------------------
# Phase 41I: Execution Report Export
# ---------------------------------------------------------------------------


def test_41i_report_export_creates_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "report", "export"])

    capsys.readouterr()
    assert exit_code == 0
    reports_dir = tmp_path / ".pcae" / "remote" / "reports"
    assert reports_dir.exists()
    report_files = list(reports_dir.glob("remote-execution-report-*.json"))
    assert len(report_files) == 1


def test_41i_report_export_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "report", "export"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Export path:" in output
    assert "Total executions:" in output
    assert "Success rate:" in output
    assert "Execution report export is read-only" in output


def test_41i_report_export_json_metadata(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "report", "export", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in ("export_path", "exported_at", "total_executions", "success_rate", "advisory"):
        assert key in data, f"missing key: {key}"
    assert data["total_executions"] == 1
    assert data["success_rate"] == 1.0
    assert data["export_path"].startswith(".pcae/remote/reports/remote-execution-report-")
    assert data["export_path"].endswith(".json")
    assert "Execution report export is read-only" in data["advisory"]


def test_41i_report_file_content(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    main(["remote", "report", "export", "--json"])
    meta = json.loads(capsys.readouterr().out)

    report_path = tmp_path / meta["export_path"]
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for key in (
        "exported_at", "total_executions", "successful_executions",
        "failed_executions", "success_rate", "runtime_breakdown",
        "latest_execution", "result_registry_summary", "advisory",
    ):
        assert key in report, f"missing key in report: {key}"
    assert report["total_executions"] == 1
    assert report["successful_executions"] == 1
    assert report["failed_executions"] == 0
    assert report["success_rate"] == 1.0
    assert isinstance(report["runtime_breakdown"], dict)
    assert "codex-local" in report["runtime_breakdown"]
    assert isinstance(report["result_registry_summary"], dict)
    assert report["result_registry_summary"]["result_count"] == 1


def test_41i_report_export_empty_registry(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "report", "export", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["total_executions"] == 0
    assert data["success_rate"] is None
    reports_dir = tmp_path / ".pcae" / "remote" / "reports"
    assert reports_dir.exists()
    assert len(list(reports_dir.glob("*.json"))) == 1


def test_41i_report_does_not_mutate_results(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    results_dir = tmp_path / ".pcae" / "remote" / "results"
    before = {f.name: f.read_text() for f in results_dir.glob("*.json")}

    main(["remote", "report", "export", "--json"])
    capsys.readouterr()

    after_results = {f.name: f.read_text() for f in results_dir.glob("*.json")}
    assert before == after_results


def test_41i_report_filename_format(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import re
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "report", "export", "--json"])
    data = json.loads(capsys.readouterr().out)

    filename = Path(data["export_path"]).name
    assert re.match(r"remote-execution-report-\d{8}-\d{6}\.json", filename), (
        f"unexpected filename: {filename}"
    )


# ---------------------------------------------------------------------------
# Phase 41J: Execution Report Inspection
# ---------------------------------------------------------------------------


def _export_report(tmp_path, monkeypatch, capsys) -> str:
    """Helper: export a report and return the export_path string."""
    main(["remote", "report", "export", "--json"])
    return json.loads(capsys.readouterr().out)["export_path"]


def test_41j_inspect_valid_report_human(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")
    report_path = _export_report(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "report", "inspect", report_path])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Report summary" in output
    assert "Validation:       valid" in output
    assert "Total executions: 1" in output
    assert "codex-local" in output
    assert "Report inspection is read-only" in output


def test_41j_inspect_valid_report_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")
    report_path = _export_report(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "report", "inspect", report_path, "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in ("advisory", "report", "report_path", "validation_status", "warnings"):
        assert key in data, f"missing key: {key}"
    assert data["validation_status"] == "valid"
    assert data["warnings"] == []
    assert data["report_path"] == report_path
    assert data["report"] is not None
    assert "Report inspection is read-only" in data["advisory"]


def test_41j_inspect_report_fields_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "claude-local", stdout="ok\n")
    report_path = _export_report(tmp_path, monkeypatch, capsys)

    main(["remote", "report", "inspect", report_path, "--json"])
    data = json.loads(capsys.readouterr().out)

    report = data["report"]
    for key in (
        "exported_at", "total_executions", "successful_executions",
        "failed_executions", "success_rate", "runtime_breakdown",
        "latest_execution", "result_registry_summary",
    ):
        assert key in report, f"missing report field: {key}"
    assert report["total_executions"] == 1
    assert "claude-local" in report["runtime_breakdown"]


def test_41j_inspect_missing_file_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "report", "inspect", ".pcae/remote/reports/nonexistent.json"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "not found" in output.lower() or "nonexistent" in output


def test_41j_inspect_malformed_json_reports_invalid(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    reports_dir = tmp_path / ".pcae" / "remote" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    bad_file = reports_dir / "remote-execution-report-bad.json"
    bad_file.write_text("not json at all", encoding="utf-8")

    exit_code = main(["remote", "report", "inspect", str(bad_file), "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["validation_status"] == "invalid"
    assert data["report"] is None
    assert len(data["warnings"]) >= 1


def test_41j_inspect_partial_report_warns(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    reports_dir = tmp_path / ".pcae" / "remote" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    partial_file = reports_dir / "remote-execution-report-partial.json"
    partial_file.write_text(
        json.dumps({"exported_at": "2026-01-01T00:00:00Z", "total_executions": 0}),
        encoding="utf-8",
    )

    exit_code = main(["remote", "report", "inspect", str(partial_file), "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["validation_status"] == "partial"
    assert data["report"] is not None
    assert len(data["warnings"]) > 0
    assert any("Missing required field" in w for w in data["warnings"])


def test_41j_inspect_readonly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")
    report_path = _export_report(tmp_path, monkeypatch, capsys)

    reports_dir = tmp_path / ".pcae" / "remote" / "reports"
    before = {f.name: f.read_text() for f in reports_dir.glob("*.json")}

    main(["remote", "report", "inspect", report_path, "--json"])
    capsys.readouterr()

    after = {f.name: f.read_text() for f in reports_dir.glob("*.json")}
    assert before == after


# ---------------------------------------------------------------------------
# Phase 41K: Execution Trends
# ---------------------------------------------------------------------------


def test_41k_trends_empty_registry(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "trends"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Execution trends summary" in output
    assert "Total executions:     0" in output
    assert "insufficient_data" in output
    assert "Execution trends are computed from persisted execution history." in output


def test_41k_trends_empty_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "trends", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in ("advisory", "trend_summary", "runtime_trends", "warnings"):
        assert key in data, f"missing key: {key}"
    ts = data["trend_summary"]
    assert ts["total_executions"] == 0
    assert ts["trend_status"] == "insufficient_data"
    assert ts["success_rate_trend"] == "insufficient_data"
    assert ts["average_duration_trend"] == "insufficient_data"
    assert ts["newest_execution"] is None
    assert ts["oldest_execution"] is None
    assert ts["execution_timespan"] is None
    assert data["runtime_trends"] == {}


def test_41k_trends_insufficient_data_with_few_results(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    for _ in range(4):
        _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "trends", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    ts = data["trend_summary"]
    assert ts["total_executions"] == 4
    assert ts["trend_status"] == "insufficient_data"
    assert ts["success_rate_trend"] == "insufficient_data"
    assert ts["average_duration_trend"] == "insufficient_data"


def test_41k_trends_stable_with_five_results(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    for _ in range(5):
        _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "trends", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    ts = data["trend_summary"]
    assert ts["total_executions"] == 5
    assert ts["trend_status"] != "insufficient_data"
    assert ts["success_rate_trend"] in ("stable", "increasing", "decreasing")
    assert ts["average_duration_trend"] in ("stable", "increasing", "decreasing",
                                             "insufficient_data")


def test_41k_trends_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "trends", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    ts = data["trend_summary"]
    for key in (
        "total_executions", "trend_status", "success_rate_trend",
        "average_duration_trend", "execution_timespan",
        "oldest_execution", "newest_execution",
    ):
        assert key in ts, f"missing trend_summary key: {key}"


def test_41k_trends_runtime_breakdown_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "claude-local", stdout="ok\n")

    exit_code = main(["remote", "trends", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    rt = data["runtime_trends"]
    assert "codex-local" in rt
    assert "claude-local" in rt
    for agent in ("codex-local", "claude-local"):
        m = rt[agent]
        for key in ("execution_count", "average_duration", "fastest_execution",
                    "slowest_execution", "success_rate"):
            assert key in m, f"missing key {key!r} for {agent}"
        assert m["execution_count"] == 1
        assert m["success_rate"] == 1.0


def test_41k_trends_oldest_and_newest(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="first\n")
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "claude-local", stdout="second\n")

    exit_code = main(["remote", "trends", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    ts = data["trend_summary"]
    oldest = ts["oldest_execution"]
    newest = ts["newest_execution"]
    assert oldest is not None
    assert newest is not None
    for key in ("job_id", "selected_agent", "final_status", "finished_at"):
        assert key in oldest
        assert key in newest
    if oldest["finished_at"] and newest["finished_at"]:
        assert oldest["finished_at"] <= newest["finished_at"]


def test_41k_trends_malformed_file_warns(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / ".pcae" / "remote" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "job-bad-result.json").write_text("not json", encoding="utf-8")

    exit_code = main(["remote", "trends", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["trend_summary"]["total_executions"] == 0
    assert len(data["warnings"]) >= 1


def test_41k_trends_human_output_format(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "trends"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Execution trends summary" in output
    assert "Trend status:" in output
    assert "Runtime trend breakdown" in output
    assert "codex-local" in output
    assert "Execution trends are computed from persisted execution history." in output


def test_41k_trends_readonly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    results_dir = tmp_path / ".pcae" / "remote" / "results"
    before = {f.name: f.read_text() for f in results_dir.glob("*.json")}

    main(["remote", "trends", "--json"])
    capsys.readouterr()

    after = {f.name: f.read_text() for f in results_dir.glob("*.json")}
    assert before == after


# ---------------------------------------------------------------------------
# Phase 41L: Runtime Benchmarking
# ---------------------------------------------------------------------------


def test_41l_benchmark_empty_registry(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "benchmark"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Runtime benchmark summary" in output
    assert "Total executions: 0" in output
    assert "insufficient_data" in output
    assert "Runtime benchmarks are computed from persisted execution history." in output


def test_41l_benchmark_empty_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "benchmark", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in ("advisory", "benchmark_summary", "runtime_metrics", "rankings", "warnings"):
        assert key in data, f"missing key: {key}"
    bs = data["benchmark_summary"]
    assert bs["total_executions"] == 0
    assert bs["runtime_count"] == 0
    assert bs["benchmark_confidence"] == "insufficient_data"
    assert data["runtime_metrics"] == {}
    r = data["rankings"]
    assert r["fastest_runtime"] is None
    assert r["slowest_runtime"] is None
    assert r["highest_success_rate"] is None


def test_41l_benchmark_json_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "benchmark", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    bs = data["benchmark_summary"]
    for key in ("total_executions", "runtime_count", "benchmark_confidence"):
        assert key in bs
    for key in ("fastest_runtime", "slowest_runtime", "highest_success_rate"):
        assert key in data["rankings"]
    assert "codex-local" in data["runtime_metrics"]


def test_41l_benchmark_per_runtime_metrics(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "benchmark", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    m = data["runtime_metrics"]["codex-local"]
    for key in (
        "execution_count", "success_rate", "average_duration_seconds",
        "fastest_execution_seconds", "slowest_execution_seconds",
        "latest_execution", "output_classification_breakdown",
    ):
        assert key in m, f"missing key: {key}"
    assert m["execution_count"] == 1
    assert m["success_rate"] == 1.0
    assert m["average_duration_seconds"] is not None
    assert m["fastest_execution_seconds"] is not None
    assert m["slowest_execution_seconds"] is not None
    assert m["latest_execution"] is not None


def test_41l_benchmark_output_classification_breakdown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")
    _invoke_job_with_output(
        tmp_path, monkeypatch, capsys, "codex-local", rc=1, stderr="err\n"
    )

    exit_code = main(["remote", "benchmark", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    bd = data["runtime_metrics"]["codex-local"]["output_classification_breakdown"]
    for cls in ("clean_stdout", "stderr_with_status_text", "empty_output", "execution_error"):
        assert cls in bd, f"missing classification: {cls}"
    assert bd["clean_stdout"] == 1
    assert bd["execution_error"] == 1
    assert bd["clean_stdout"] + bd["execution_error"] == 2


def test_41l_benchmark_rankings_computed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "claude-local", stdout="ok\n")

    exit_code = main(["remote", "benchmark", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    r = data["rankings"]
    assert r["fastest_runtime"] is not None
    assert r["slowest_runtime"] is not None
    assert r["highest_success_rate"] is not None
    assert r["fastest_runtime"] in data["runtime_metrics"]
    assert r["slowest_runtime"] in data["runtime_metrics"]
    assert r["highest_success_rate"] in data["runtime_metrics"]
    fastest_avg = data["runtime_metrics"][r["fastest_runtime"]]["average_duration_seconds"]
    slowest_avg = data["runtime_metrics"][r["slowest_runtime"]]["average_duration_seconds"]
    assert fastest_avg <= slowest_avg


def test_41l_benchmark_insufficient_data_confidence(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    for _ in range(4):
        _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "benchmark", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["benchmark_summary"]["benchmark_confidence"] == "insufficient_data"


def test_41l_benchmark_low_confidence_with_five(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    for _ in range(5):
        _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "benchmark", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["benchmark_summary"]["benchmark_confidence"] == "low"


def test_41l_benchmark_human_output_format(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    exit_code = main(["remote", "benchmark"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Runtime benchmark summary" in output
    assert "Runtime metrics" in output
    assert "codex-local" in output
    assert "Runtime benchmarks are computed from persisted execution history." in output


def test_41l_benchmark_malformed_file_warns(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / ".pcae" / "remote" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "job-bad-result.json").write_text("not json", encoding="utf-8")

    exit_code = main(["remote", "benchmark", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["benchmark_summary"]["total_executions"] == 0
    assert len(data["warnings"]) >= 1


def test_41l_benchmark_readonly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _invoke_job_with_output(tmp_path, monkeypatch, capsys, "codex-local", stdout="ok\n")

    results_dir = tmp_path / ".pcae" / "remote" / "results"
    before = {f.name: f.read_text() for f in results_dir.glob("*.json")}

    main(["remote", "benchmark", "--json"])
    capsys.readouterr()

    after_benchmark = {f.name: f.read_text() for f in results_dir.glob("*.json")}
    assert before == after_benchmark


# ---------------------------------------------------------------------------
# Phase 41L.1 — Controlled Runtime Benchmarking (dry-run only)
# ---------------------------------------------------------------------------


def test_411_controlled_benchmark_dry_run_human(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "benchmark", "controlled", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Controlled benchmark plan (dry run)" in output
    assert "claude-local" in output
    assert "codex-local" in output
    assert "kimi-local" in output
    assert "Reply with exactly: PCAE controlled benchmark successful." in output
    assert "Runs per runtime: 3" in output
    assert "Planned metrics" in output
    assert "Limitations" in output
    assert "Controlled benchmarks measure end-to-end runtime execution" in output


def test_411_controlled_benchmark_dry_run_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "benchmark", "controlled", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in ("advisory", "benchmark_plan", "planned_metrics", "limitations", "future_metrics"):
        assert key in data


def test_411_controlled_benchmark_plan_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "benchmark", "controlled", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    plan = data["benchmark_plan"]
    assert plan["runtimes"] == ["claude-local", "codex-local", "kimi-local"]
    assert plan["prompt"] == "Reply with exactly: PCAE controlled benchmark successful."
    assert plan["runs_per_runtime"] == 3
    assert plan["execution_mode"] == "non_interactive"
    assert plan["human_approval_required"] is True
    assert plan["total_planned_runs"] == 9


def test_411_controlled_benchmark_planned_metrics(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "benchmark", "controlled", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    metrics = data["planned_metrics"]
    for m in ("duration_seconds", "exit_code", "stdout_length", "stderr_length",
              "output_classification", "success_or_failure"):
        assert m in metrics


def test_411_controlled_benchmark_limitations_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "benchmark", "controlled", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    limitations = data["limitations"]
    assert len(limitations) >= 1
    combined = " ".join(limitations)
    assert "wall-clock" in combined
    assert "human approval" in combined.lower()
    assert "no agents are executed" in combined


def test_411_controlled_benchmark_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "benchmark", "controlled", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "end-to-end runtime execution" in data["advisory"]
    assert "model performance" in data["advisory"]


def test_411_controlled_benchmark_readonly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before_files = list((tmp_path / ".pcae").rglob("*.json"))

    main(["remote", "benchmark", "controlled", "--dry-run", "--json"])
    capsys.readouterr()

    after_files = list((tmp_path / ".pcae").rglob("*.json"))
    assert set(f.name for f in before_files) == set(f.name for f in after_files)


def test_411_controlled_benchmark_historical_unchanged(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "benchmark", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "benchmark_summary" in data
    assert "runtime_metrics" in data
    assert "rankings" in data


def test_411_controlled_benchmark_dry_run_required(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["remote", "benchmark", "controlled"])

    assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# Phase 41M — File Modification Governance Design
# ---------------------------------------------------------------------------


def test_41m_file_governance_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "file-governance"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "File Modification Governance Design" in output
    assert "Writable Scope Rules" in output
    assert "Approval Workflow" in output
    assert "Rollback Strategy" in output
    assert "Risk Model" in output
    assert "This phase defines governance only; no file modifications are performed." in output


def test_41m_file_governance_json_top_level_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "file-governance", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in ("advisory", "governance_design", "risk_model", "approval_model", "rollback_model"):
        assert key in data


def test_41m_file_governance_design_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "file-governance", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    design = data["governance_design"]
    for section in (
        "writable_scope_rules",
        "change_capture",
        "approval_workflow",
        "commit_governance",
        "push_governance",
        "rollback_strategy",
        "safety_model",
    ):
        assert section in design


def test_41m_file_governance_writable_scope(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "file-governance", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    scope = data["governance_design"]["writable_scope_rules"]
    assert "allowed_paths" in scope
    assert "denied_paths" in scope
    assert "protected_files" in scope
    assert "repository_root_constraint" in scope
    assert len(scope["allowed_paths"]) >= 1
    assert len(scope["denied_paths"]) >= 1


def test_41m_file_governance_approval_workflow(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "file-governance", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    approval = data["governance_design"]["approval_workflow"]
    assert approval["human_review_required"] is True
    assert len(approval["approval_checkpoints"]) >= 1
    assert "rejection_handling" in approval
    assert "re_execution_requirements" in approval


def test_41m_file_governance_risk_model(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "file-governance", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    risk = data["risk_model"]
    assert set(risk["risk_levels"]) == {"low", "medium", "high", "critical"}
    assert "classification_scheme" in risk
    for level in ("low", "medium", "high", "critical"):
        assert level in risk["classification_scheme"]


def test_41m_file_governance_rollback_model(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "file-governance", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    rollback = data["rollback_model"]
    assert "rollback_prerequisites" in rollback
    assert "rollback_artifact_requirements" in rollback
    assert "recovery_workflow" in rollback
    assert len(rollback["recovery_workflow"]) >= 1


def test_41m_file_governance_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "file-governance", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "governance only" in data["advisory"]
    assert "no file modifications" in data["advisory"]


def test_41m_file_governance_readonly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before_files = set(f.name for f in (tmp_path / ".pcae").rglob("*.json"))

    main(["remote", "file-governance", "--json"])
    capsys.readouterr()

    after_files = set(f.name for f in (tmp_path / ".pcae").rglob("*.json"))
    assert before_files == after_files


# ---------------------------------------------------------------------------
# Phase 42A — Controlled File Modification
# ---------------------------------------------------------------------------

# Helpers for the file-change git capture functions.

def _fake_git_head(sha: str = "abc1234"):
    """Return a patcher that makes _capture_git_head return sha."""
    def _capture(root):
        return sha
    return _capture


def _fake_git_changed_files(files: list[str]):
    """Return a patcher that makes _capture_git_changed_files return files."""
    def _capture(root):
        return files
    return _capture


def _fake_diff_summary(summary: str = ""):
    """Return a patcher that makes _capture_diff_summary return summary."""
    def _capture(root):
        return summary
    return _capture


def _patch_file_change_helpers(
    monkeypatch,
    changed_files: list[str] | None = None,
    diff_summary: str = "",
    head_sha: str = "abc1234",
) -> None:
    """Patch all three git-capture helpers for file-change tests."""
    monkeypatch.setattr(_agent_mod, "_capture_git_head", _fake_git_head(head_sha))
    monkeypatch.setattr(
        _agent_mod,
        "_capture_git_changed_files",
        _fake_git_changed_files(changed_files if changed_files is not None else []),
    )
    monkeypatch.setattr(_agent_mod, "_capture_diff_summary", _fake_diff_summary(diff_summary))


def _invoke_job_with_file_changes(
    tmp_path: Path,
    monkeypatch,
    capsys,
    agent: str = "claude-local",
    changed_files: list[str] | None = None,
    diff_summary: str = "",
    rc: int = 0,
    stdout: str = "ok\n",
    stderr: str = "",
) -> tuple[str, dict]:
    """Create, approve, and invoke a job with --allow-file-changes. Returns (job_id, data)."""
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent=agent)
    _patch_ready(monkeypatch, agent)
    _patch_file_change_helpers(monkeypatch, changed_files=changed_files, diff_summary=diff_summary)
    monkeypatch.setattr(
        _agent_mod,
        "_run_agent_subprocess",
        lambda cmd, timeout: _fake_proc(rc, stdout, stderr),
    )
    exit_code = main(["remote", "execute", job_id, "--invoke", "--allow-file-changes", "--json"])
    data = json.loads(capsys.readouterr().out)
    return job_id, data


def test_42a_file_changes_requires_allow_flag(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Without --allow-file-changes, --invoke uses the read-only path."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys)
    _patch_ready(monkeypatch)
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "ok\n"))

    exit_code = main(["remote", "execute", job_id, "--invoke", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    # Read-only invoke does NOT produce file-change fields.
    assert "changed_files" not in data
    assert "scope_validation" not in data
    assert "pre_execution_head" not in data


def test_42a_no_changes_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys, changed_files=[]
    )

    assert data["final_status"] == "completed_with_no_changes"
    assert data["changed_files"] == []
    assert data["scope_validation"]["valid"] is True


def test_42a_docs_modification_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        changed_files=["docs/remote-controlled-modification-test.md"],
        diff_summary=" docs/remote-controlled-modification-test.md | 1 +",
    )

    assert data["final_status"] == "completed"
    assert "docs/remote-controlled-modification-test.md" in data["changed_files"]
    assert data["scope_validation"]["valid"] is True
    assert data["scope_validation"]["violations"] == []


def test_42a_tasks_modification_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        changed_files=["tasks/notes.md"],
    )

    assert data["final_status"] == "completed"
    assert data["scope_validation"]["valid"] is True


def test_42a_src_modification_is_scope_violation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        changed_files=["src/pcae/core/agent.py"],
    )

    assert data["final_status"] == "failed"
    scope = data["scope_validation"]
    assert scope["valid"] is False
    assert len(scope["violations"]) >= 1
    assert any("src/" in v for v in scope["violations"])


def test_42a_tests_modification_is_scope_violation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        changed_files=["tests/test_something.py"],
    )

    assert data["final_status"] == "failed"
    assert data["scope_validation"]["valid"] is False


def test_42a_pcae_dir_is_scope_violation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        changed_files=[".pcae/policy.toml"],
    )

    assert data["final_status"] == "failed"
    assert data["scope_validation"]["valid"] is False


def test_42a_json_output_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        changed_files=["docs/test.md"],
        diff_summary=" docs/test.md | 1 +",
    )

    for key in (
        "executed",
        "job_id",
        "selected_agent",
        "pre_execution_head",
        "changed_files",
        "scope_validation",
        "diff_summary",
        "final_status",
        "advisory",
    ):
        assert key in data, f"missing key: {key}"


def test_42a_pre_execution_head_captured(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        changed_files=[],
    )

    assert data["pre_execution_head"] == "abc1234"


def test_42a_diff_summary_captured(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        changed_files=["docs/note.md"],
        diff_summary=" docs/note.md | 3 +++",
    )

    assert "docs/note.md" in data["diff_summary"]


def test_42a_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys, changed_files=[]
    )

    assert "no commit or push" in data["advisory"].lower()


def test_42a_no_commit_no_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Verify no git commit or push commands are invoked by the handler."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    commits_before = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    ).stdout.strip()

    _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys,
        changed_files=["docs/test.md"],
    )

    commits_after = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert commits_before == commits_after


def test_42a_artifact_persisted(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job_id, data = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys, changed_files=["docs/test.md"]
    )

    results_dir = tmp_path / ".pcae" / "remote" / "results"
    artifact_file = results_dir / f"{job_id}-result.json"
    assert artifact_file.exists()
    artifact = json.loads(artifact_file.read_text())
    assert artifact["file_changes_allowed"] is True
    assert "changed_files" in artifact
    assert "scope_validation" in artifact
    assert "pre_execution_head" in artifact


def test_42a_agent_failure_marks_failed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys,
        changed_files=["docs/test.md"],
        rc=1,
        stderr="Agent error.\n",
    )

    assert data["final_status"] == "failed"
    assert data["exit_code"] == 1


def test_42a_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")
    _patch_ready(monkeypatch, "claude-local")
    _patch_file_change_helpers(
        monkeypatch,
        changed_files=["docs/test.md"],
        diff_summary=" docs/test.md | 1 +",
    )
    monkeypatch.setattr(
        _agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "Done.\n")
    )

    exit_code = main(["remote", "execute", job_id, "--invoke", "--allow-file-changes"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Remote execution result (file changes allowed)" in output
    assert "Pre-execution HEAD" in output
    assert "Changed files" in output
    assert "Scope validation" in output
    assert "no commit or push" in output.lower()


# ---------------------------------------------------------------------------
# Phase 42A.1 — Codex Writable Sandbox Contract
# ---------------------------------------------------------------------------


def test_421_codex_read_only_invoke_uses_read_only_sandbox(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Standard --invoke (no --allow-file-changes) keeps --sandbox read-only for codex."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="codex-local")
    _patch_ready(monkeypatch, "codex-local")

    captured_cmd: list[list[str]] = []

    def _fake_subprocess(cmd, timeout):
        captured_cmd.append(cmd)
        return _fake_proc(0, "ok\n")

    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", _fake_subprocess)

    exit_code = main(["remote", "execute", job_id, "--invoke", "--json"])

    capsys.readouterr()
    assert exit_code == 0
    assert len(captured_cmd) == 1
    cmd = captured_cmd[0]
    assert "--sandbox" in cmd
    sandbox_value = cmd[cmd.index("--sandbox") + 1]
    assert sandbox_value == "read-only"


def test_421_codex_file_changes_uses_workspace_write_sandbox(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """--allow-file-changes switches codex to --sandbox workspace-write."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="codex-local")
    _patch_ready(monkeypatch, "codex-local")
    _patch_file_change_helpers(monkeypatch, changed_files=["docs/test.md"])

    captured_cmd: list[list[str]] = []

    def _fake_subprocess(cmd, timeout):
        captured_cmd.append(cmd)
        return _fake_proc(0, "ok\n")

    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", _fake_subprocess)

    exit_code = main(
        ["remote", "execute", job_id, "--invoke", "--allow-file-changes", "--json"]
    )

    capsys.readouterr()
    assert exit_code == 0
    assert len(captured_cmd) == 1
    cmd = captured_cmd[0]
    assert "--sandbox" in cmd
    sandbox_value = cmd[cmd.index("--sandbox") + 1]
    assert sandbox_value == "workspace-write"


def test_421_sandbox_mode_in_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys,
        agent="codex-local",
        changed_files=["docs/test.md"],
    )

    assert "sandbox_mode" in data
    assert data["sandbox_mode"] == "workspace-write"


def test_421_sandbox_mode_in_artifact(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job_id, _ = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys,
        agent="codex-local",
        changed_files=["docs/test.md"],
    )

    artifact_file = tmp_path / ".pcae" / "remote" / "results" / f"{job_id}-result.json"
    artifact = json.loads(artifact_file.read_text())
    assert artifact["sandbox_mode"] == "workspace-write"


def test_421_claude_uses_permission_mode_acceptedits_with_file_changes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Phase 42A.3.1: --allow-file-changes adds --permission-mode acceptEdits for claude-local."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    captured_cmd: list[list[str]] = []

    def _fake_subprocess(cmd, timeout):
        captured_cmd.append(cmd)
        return _fake_proc(0, "ok\n")

    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")
    _patch_ready(monkeypatch, "claude-local")
    _patch_file_change_helpers(monkeypatch, changed_files=[])
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", _fake_subprocess)

    main(["remote", "execute", job_id, "--invoke", "--allow-file-changes", "--json"])
    capsys.readouterr()

    assert len(captured_cmd) == 1
    cmd = captured_cmd[0]
    assert cmd[0] == "claude"
    assert cmd[1] == "-p"
    assert "--permission-mode" in cmd
    assert cmd[cmd.index("--permission-mode") + 1] == "acceptEdits"
    assert "--sandbox" not in cmd


def test_421_kimi_unaffected_by_file_changes_flag(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Kimi command does not gain --sandbox flag when --allow-file-changes is used."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    captured_cmd: list[list[str]] = []

    def _fake_subprocess(cmd, timeout):
        captured_cmd.append(cmd)
        return _fake_proc(0, "ok\n")

    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="kimi-local")
    _patch_ready(monkeypatch, "kimi-local")
    _patch_file_change_helpers(monkeypatch, changed_files=[])
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", _fake_subprocess)

    main(["remote", "execute", job_id, "--invoke", "--allow-file-changes", "--json"])
    capsys.readouterr()

    assert len(captured_cmd) == 1
    cmd = captured_cmd[0]
    assert "--sandbox" not in cmd
    assert cmd[0] == "kimi"
    assert cmd[1] == "-p"


def test_421_codex_docs_modification_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys,
        agent="codex-local",
        changed_files=["docs/remote-controlled-modification-test.md"],
        diff_summary=" docs/remote-controlled-modification-test.md | 1 +",
    )

    assert data["final_status"] == "completed"
    assert data["scope_validation"]["valid"] is True
    assert data["sandbox_mode"] == "workspace-write"


def test_421_codex_src_violation_still_detected(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    _, data = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys,
        agent="codex-local",
        changed_files=["src/pcae/core/agent.py"],
    )

    assert data["final_status"] == "failed"
    assert data["scope_validation"]["valid"] is False
    assert data["sandbox_mode"] == "workspace-write"


def test_421_sandbox_mode_in_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="codex-local")
    _patch_ready(monkeypatch, "codex-local")
    _patch_file_change_helpers(monkeypatch, changed_files=["docs/test.md"])
    monkeypatch.setattr(
        _agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "Done.\n")
    )

    exit_code = main(["remote", "execute", job_id, "--invoke", "--allow-file-changes"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Sandbox mode" in output
    assert "workspace-write" in output


# ---------------------------------------------------------------------------
# Phase 42A.2 — Git Change Detection After Writable Execution
# ---------------------------------------------------------------------------


def test_422_capture_untracked_file_in_tracked_dir(
    tmp_path: Path,
) -> None:
    """Files added to an already-tracked directory are detected."""
    init_git_repo(tmp_path)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "existing.md").write_text("existing\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env={**__import__("os").environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )

    (docs_dir / "remote-controlled-modification-test.md").write_text("PCAE test\n")

    from pcae.core.agent import _capture_git_changed_files
    files = _capture_git_changed_files(HarnessPath(tmp_path))

    assert any("remote-controlled-modification-test.md" in f for f in files)


def test_422_capture_untracked_file_in_untracked_dir(
    tmp_path: Path,
) -> None:
    """Files inside an entirely-untracked directory are detected individually."""
    init_git_repo(tmp_path)
    # docs/ has never been committed — without --untracked-files=all git
    # would only report 'docs/' not the individual file inside it.
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "remote-controlled-modification-test.md").write_text("PCAE test\n")

    from pcae.core.agent import _capture_git_changed_files
    files = _capture_git_changed_files(HarnessPath(tmp_path))

    # Must see the individual file, not just the directory entry.
    assert any("remote-controlled-modification-test.md" in f for f in files)
    # No trailing-slash directory-only entries.
    assert "docs/" not in files


def test_422_no_changes_returns_empty(
    tmp_path: Path,
) -> None:
    """Clean working tree produces an empty changed-files list."""
    init_git_repo(tmp_path)
    (tmp_path / "init.txt").write_text("x\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env={**__import__("os").environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )

    from pcae.core.agent import _capture_git_changed_files
    files = _capture_git_changed_files(HarnessPath(tmp_path))

    assert files == []


def _make_file_creating_subprocess(tmp_path: Path, rel_path: str, content: str = "PCAE test\n"):
    """
    Return a fake _run_agent_subprocess that creates a real file in tmp_path.

    This lets _capture_git_changed_files run against real git without needing
    to be mocked, verifying the full post-execution detection pipeline.
    """
    def _subprocess(cmd, timeout):
        target = tmp_path / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return _fake_proc(0, "Created file.\n")
    return _subprocess


def _commit_repo_for_file_detection(tmp_path: Path) -> None:
    """
    Prepare a clean git state for file-detection integration tests.

    Extends .pcae/.gitignore to include 'remote/' so job and result artifacts
    are not tracked, then commits every file. After this call git status is
    clean, and only files created by the fake agent subprocess will appear in
    _capture_git_changed_files output.
    """
    pcae_gitignore = tmp_path / ".pcae" / ".gitignore"
    pcae_gitignore.write_text(
        "session.json\narchitecture-history.json\nagent-lock.json\nremote/\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )


def test_422_integration_untracked_docs_file_detected(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """
    End-to-end: agent creates docs/ file → _capture_git_changed_files detects it →
    scope validation passes → final_status == 'completed'.
    """
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _commit_repo_for_file_detection(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="codex-local")
    _patch_ready(monkeypatch, "codex-local")
    # Do NOT patch _capture_git_changed_files — let it run for real.
    monkeypatch.setattr(
        _agent_mod,
        "_run_agent_subprocess",
        _make_file_creating_subprocess(tmp_path, "docs/remote-controlled-modification-test.md"),
    )
    # Patch diff summary (git diff --stat won't show untracked files).
    monkeypatch.setattr(_agent_mod, "_capture_diff_summary", lambda root: "")

    exit_code = main(
        ["remote", "execute", job_id, "--invoke", "--allow-file-changes", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert any(
        "remote-controlled-modification-test.md" in f for f in data["changed_files"]
    ), f"changed_files={data['changed_files']}"
    assert data["scope_validation"]["valid"] is True
    assert data["final_status"] == "completed"


def test_422_integration_completed_with_no_changes_when_clean(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """
    End-to-end: agent creates no files → _capture_git_changed_files returns [] →
    final_status == 'completed_with_no_changes'.
    """
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _commit_repo_for_file_detection(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="codex-local")
    _patch_ready(monkeypatch, "codex-local")
    monkeypatch.setattr(
        _agent_mod, "_run_agent_subprocess", lambda cmd, timeout: _fake_proc(0, "nothing done\n")
    )
    monkeypatch.setattr(_agent_mod, "_capture_diff_summary", lambda root: "")

    exit_code = main(
        ["remote", "execute", job_id, "--invoke", "--allow-file-changes", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["changed_files"] == []
    assert data["final_status"] == "completed_with_no_changes"


def test_422_integration_src_file_is_scope_violation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """
    End-to-end: agent creates src/ file → scope validation fails →
    final_status == 'failed'.
    """
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _commit_repo_for_file_detection(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="codex-local")
    _patch_ready(monkeypatch, "codex-local")
    monkeypatch.setattr(
        _agent_mod,
        "_run_agent_subprocess",
        _make_file_creating_subprocess(tmp_path, "src/unauthorized.py"),
    )
    monkeypatch.setattr(_agent_mod, "_capture_diff_summary", lambda root: "")

    exit_code = main(
        ["remote", "execute", job_id, "--invoke", "--allow-file-changes", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["final_status"] == "failed"
    assert data["scope_validation"]["valid"] is False
    assert any("src/" in v for v in data["scope_validation"]["violations"])


# ---------------------------------------------------------------------------
# Phase 42A.3 — Claude Writable Execution Contract Inspection
# ---------------------------------------------------------------------------


def test_42a3_writable_contract_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Writable Execution Contract" in output
    assert "claude-local" in output
    assert "claude -p" in output
    assert "Writable support:" in output
    assert "unknown" in output
    assert "Safety recommendation:" in output
    assert "advisory" in output.lower()


def test_42a3_writable_contract_json_top_level_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in (
        "agent_id",
        "current_invocation_command",
        "known_read_only_behavior",
        "writable_support_status",
        "required_flags_if_known",
        "unknowns",
        "safety_recommendation",
        "advisory",
    ):
        assert key in data


def test_42a3_writable_support_is_unknown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["writable_support_status"] == "unknown"


def test_42a3_required_flags_empty(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["required_flags_if_known"] == []


def test_42a3_invocation_command_is_claude_p(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "claude" in data["current_invocation_command"]
    assert "-p" in data["current_invocation_command"]


def test_42a3_unknowns_are_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(data["unknowns"]) >= 1


def test_42a3_safety_recommendation_is_conservative(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "claude-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    rec = data["safety_recommendation"].lower()
    assert "do not enable" in rec or "conservative" in rec


def test_42a3_unknown_agent_returns_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "unknown-agent"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Error" in output


def test_42a3_unknown_agent_json_has_error_key(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "unknown-agent", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert "error" in data


def test_42a3_readonly_does_not_execute_claude(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    executed: list[str] = []

    original_run = __import__("subprocess").run

    def patched_run(cmd, **kwargs):  # type: ignore[no-untyped-def]
        if isinstance(cmd, list) and cmd and "claude" in cmd[0]:
            executed.append(str(cmd))
        return original_run(cmd, **kwargs)

    monkeypatch.setattr("subprocess.run", patched_run)
    main(["remote", "writable-contract", "claude-local", "--json"])

    assert executed == [], "claude must not be executed during writable-contract inspection"


# ---------------------------------------------------------------------------
# Phase 42A.4 — Kimi Writable Execution Contract Inspection
# ---------------------------------------------------------------------------


def test_42a4_writable_contract_kimi_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "kimi-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Writable Execution Contract" in output
    assert "kimi-local" in output
    assert "kimi -p" in output
    assert "Writable support:" in output
    assert "unknown" in output
    assert "Dangerous flags" in output
    assert "--yolo" in output
    assert "--auto" in output
    assert "Safety recommendation:" in output
    assert "advisory" in output.lower()


def test_42a4_writable_contract_kimi_json_top_level_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for key in (
        "agent_id",
        "current_invocation_command",
        "known_read_only_behavior",
        "writable_support_status",
        "required_flags_if_known",
        "dangerous_flags",
        "unknowns",
        "safety_recommendation",
        "advisory",
    ):
        assert key in data


def test_42a4_kimi_writable_support_is_unknown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["writable_support_status"] == "unknown"


def test_42a4_kimi_required_flags_empty(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["required_flags_if_known"] == []


def test_42a4_kimi_invocation_command_is_kimi_p(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "kimi" in data["current_invocation_command"]
    assert "-p" in data["current_invocation_command"]


def test_42a4_kimi_dangerous_flags_surfaces_yolo_and_auto(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    dangerous = data["dangerous_flags"]
    assert len(dangerous) >= 2
    combined = " ".join(dangerous)
    assert "--yolo" in combined
    assert "--auto" in combined


def test_42a4_kimi_unknowns_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(data["unknowns"]) >= 1


def test_42a4_kimi_safety_recommendation_is_conservative(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    rec = data["safety_recommendation"].lower()
    assert "do not enable" in rec or "conservative" in rec
    assert "yolo" in rec or "dangerous" in rec or "not allowed" in rec


def test_42a4_kimi_known_read_only_behavior_includes_positional_failure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "writable-contract", "kimi-local", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    combined = " ".join(data["known_read_only_behavior"]).lower()
    assert "too many arguments" in combined


def test_42a4_kimi_does_not_affect_claude_contract(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "writable-contract", "claude-local", "--json"])
    claude_data = json.loads(capsys.readouterr().out)

    main(["remote", "writable-contract", "kimi-local", "--json"])
    kimi_data = json.loads(capsys.readouterr().out)

    assert claude_data["agent_id"] == "claude-local"
    assert kimi_data["agent_id"] == "kimi-local"
    assert "claude" in claude_data["current_invocation_command"]
    assert "kimi" in kimi_data["current_invocation_command"]
    assert claude_data["dangerous_flags"] == []
    assert len(kimi_data["dangerous_flags"]) >= 2


def test_42a4_readonly_does_not_execute_kimi(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    executed: list[str] = []

    original_run = __import__("subprocess").run

    def patched_run(cmd, **kwargs):  # type: ignore[no-untyped-def]
        if isinstance(cmd, list) and cmd and "kimi" in cmd[0]:
            executed.append(str(cmd))
        return original_run(cmd, **kwargs)

    monkeypatch.setattr("subprocess.run", patched_run)
    main(["remote", "writable-contract", "kimi-local", "--json"])

    assert executed == [], "kimi must not be executed during writable-contract inspection"


# ---------------------------------------------------------------------------
# Phase 42A.3.1 — Claude Writable Contract Correction
# ---------------------------------------------------------------------------


def test_42a31_read_only_claude_command_unchanged(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Read-only Claude invocation (no --allow-file-changes) stays as `claude -p <prompt>`."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    captured_cmd: list[list[str]] = []

    def _fake_subprocess(cmd, timeout):
        captured_cmd.append(cmd)
        return _fake_proc(0, "ok\n")

    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")
    _patch_ready(monkeypatch, "claude-local")
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", _fake_subprocess)

    main(["remote", "execute", job_id, "--invoke", "--json"])
    capsys.readouterr()

    assert len(captured_cmd) == 1
    cmd = captured_cmd[0]
    assert cmd[0] == "claude"
    assert cmd[1] == "-p"
    assert "--permission-mode" not in cmd


def test_42a31_writable_claude_uses_accept_edits(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """--allow-file-changes adds --permission-mode acceptEdits to the Claude command."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    captured_cmd: list[list[str]] = []

    def _fake_subprocess(cmd, timeout):
        captured_cmd.append(cmd)
        return _fake_proc(0, "ok\n")

    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")
    _patch_ready(monkeypatch, "claude-local")
    _patch_file_change_helpers(monkeypatch, changed_files=[])
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", _fake_subprocess)

    main(["remote", "execute", job_id, "--invoke", "--allow-file-changes", "--json"])
    capsys.readouterr()

    cmd = captured_cmd[0]
    assert "--permission-mode" in cmd
    assert cmd[cmd.index("--permission-mode") + 1] == "acceptEdits"


def test_42a31_no_dangerous_claude_flags(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Claude writable command must not include auto, bypassPermissions, or dangerously-skip."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    captured_cmd: list[list[str]] = []

    def _fake_subprocess(cmd, timeout):
        captured_cmd.append(cmd)
        return _fake_proc(0, "ok\n")

    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")
    _patch_ready(monkeypatch, "claude-local")
    _patch_file_change_helpers(monkeypatch, changed_files=[])
    monkeypatch.setattr(_agent_mod, "_run_agent_subprocess", _fake_subprocess)

    main(["remote", "execute", job_id, "--invoke", "--allow-file-changes", "--json"])
    capsys.readouterr()

    cmd = captured_cmd[0]
    cmd_str = " ".join(cmd)
    assert "auto" not in cmd_str or "--permission-mode acceptEdits" in cmd_str
    assert "bypassPermissions" not in cmd_str
    assert "dangerously-skip" not in cmd_str
    # Specifically: if --permission-mode is present, its value must be acceptEdits
    if "--permission-mode" in cmd:
        assert cmd[cmd.index("--permission-mode") + 1] == "acceptEdits"


def test_42a31_permission_mode_in_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """JSON output from --allow-file-changes includes permission_mode=acceptEdits for claude."""
    _, data = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys, agent="claude-local", changed_files=[]
    )
    assert "permission_mode" in data
    assert data["permission_mode"] == "acceptEdits"


def test_42a31_permission_mode_in_artifact(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Persisted result artifact includes permission_mode=acceptEdits for claude."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job_id, _ = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys, agent="claude-local", changed_files=[]
    )
    artifact_file = tmp_path / ".pcae" / "remote" / "results" / f"{job_id}-result.json"
    artifact = json.loads(artifact_file.read_text())
    assert artifact["permission_mode"] == "acceptEdits"


def test_42a31_permission_mode_in_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Human output displays 'Permission mode: acceptEdits' for claude writable execution."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")
    _patch_ready(monkeypatch, "claude-local")
    _patch_file_change_helpers(monkeypatch, changed_files=[])
    monkeypatch.setattr(
        _agent_mod,
        "_run_agent_subprocess",
        lambda cmd, timeout: _fake_proc(0, "ok\n"),
    )

    main(["remote", "execute", job_id, "--invoke", "--allow-file-changes"])
    output = capsys.readouterr().out
    assert "Permission mode" in output
    assert "acceptEdits" in output


def test_42a31_docs_modification_succeeds_with_claude(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """docs/ file change passes scope validation for claude-local writable execution."""
    _, data = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        agent="claude-local",
        changed_files=["docs/generated-note.md"],
        diff_summary="1 file changed",
    )
    assert data["scope_validation"]["valid"] is True
    assert data["final_status"] == "completed"
    assert "docs/generated-note.md" in data["changed_files"]


def test_42a31_codex_permission_mode_is_na(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Codex writable execution gets permission_mode=n/a (unchanged from prior behavior)."""
    _, data = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys, agent="codex-local", changed_files=[]
    )
    assert data["permission_mode"] == "n/a"


def test_42a31_kimi_permission_mode_is_na(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Kimi writable execution gets permission_mode=n/a (unchanged from prior behavior)."""
    _, data = _invoke_job_with_file_changes(
        tmp_path, monkeypatch, capsys, agent="kimi-local", changed_files=[]
    )
    assert data["permission_mode"] == "n/a"


# ---------------------------------------------------------------------------
# Phase 42B — Change Review Artifacts
# ---------------------------------------------------------------------------


def _invoke_and_review(
    tmp_path: Path,
    monkeypatch,
    capsys,
    agent: str = "claude-local",
    changed_files: list[str] | None = None,
    diff_summary: str = "",
    rc: int = 0,
) -> tuple[str, dict]:
    """Invoke a job with file changes, then call pcae remote changes <job_id> --json."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id, _ = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        agent=agent,
        changed_files=changed_files,
        diff_summary=diff_summary,
        rc=rc,
    )
    exit_code = main(["remote", "changes", "show", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)
    return job_id, data


def test_42b_changes_json_top_level_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _, data = _invoke_and_review(tmp_path, monkeypatch, capsys, changed_files=[])
    assert "change_review" in data
    assert "advisory" in data


def test_42b_change_review_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _, data = _invoke_and_review(tmp_path, monkeypatch, capsys, changed_files=[])
    review = data["change_review"]
    for key in (
        "job_id",
        "requested_agent",
        "final_status",
        "changed_files",
        "scope_validation",
        "diff_summary",
        "risk_level",
        "approval_required",
        "commit_allowed",
        "push_allowed",
    ):
        assert key in review, f"missing key: {key}"


def test_42b_docs_only_change_is_low_risk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _, data = _invoke_and_review(
        tmp_path, monkeypatch, capsys,
        changed_files=["docs/generated-note.md"],
    )
    assert data["change_review"]["risk_level"] == "low"


def test_42b_tasks_only_change_is_low_risk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _, data = _invoke_and_review(
        tmp_path, monkeypatch, capsys,
        changed_files=["tasks/notes.md"],
    )
    assert data["change_review"]["risk_level"] == "low"


def test_42b_scope_violation_is_critical_risk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _, data = _invoke_and_review(
        tmp_path, monkeypatch, capsys,
        changed_files=["src/pcae/core/agent.py"],
    )
    assert data["change_review"]["risk_level"] == "critical"


def test_42b_no_changes_reports_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _, data = _invoke_and_review(tmp_path, monkeypatch, capsys, changed_files=[])
    review = data["change_review"]
    assert review["changed_files"] == []
    assert review["risk_level"] == "low"


def test_42b_scope_violation_surfaces_in_review(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _, data = _invoke_and_review(
        tmp_path, monkeypatch, capsys,
        changed_files=["src/pcae/core/agent.py"],
    )
    review = data["change_review"]
    assert review["scope_validation"]["valid"] is False
    assert len(review["scope_validation"]["violations"]) >= 1


def test_42b_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _, data = _invoke_and_review(tmp_path, monkeypatch, capsys, changed_files=[])
    assert "Change review is advisory" in data["advisory"]
    assert "no commit or push" in data["advisory"]


def test_42b_push_always_false(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _, data = _invoke_and_review(
        tmp_path, monkeypatch, capsys,
        changed_files=["docs/note.md"],
    )
    assert data["change_review"]["push_allowed"] is False


def test_42b_commit_allowed_for_clean_completion(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _, data = _invoke_and_review(
        tmp_path, monkeypatch, capsys,
        changed_files=["docs/note.md"],
    )
    review = data["change_review"]
    assert review["final_status"] == "completed"
    assert review["commit_allowed"] is True


def test_42b_commit_not_allowed_on_scope_violation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _, data = _invoke_and_review(
        tmp_path, monkeypatch, capsys,
        changed_files=["src/pcae/core/agent.py"],
    )
    assert data["change_review"]["commit_allowed"] is False


def test_42b_missing_job_returns_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "changes", "show", "nonexistent-job-id"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Unknown job" in output or "nonexistent" in output.lower()


def test_42b_missing_artifact_reports_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """A job with no result artifact still returns a review with a clear note."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    # Persist a job manually (no execution artifact written).
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")

    exit_code = main(["remote", "changes", "show", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    review = data["change_review"]
    assert review["risk_level"] == "unknown"
    assert "notes" in review
    assert review["changed_files"] == []


def test_42b_human_output_contains_key_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job_id, _ = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        changed_files=["docs/report.md"],
    )
    main(["remote", "changes", "show", job_id])
    output = capsys.readouterr().out

    assert "Change Review" in output
    assert "Risk level" in output
    assert "Scope validation" in output
    assert "Approval guidance" in output
    assert "advisory" in output.lower()


def test_42b_readonly_does_not_write_files(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """pcae remote changes must not create new files."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    job_id, _ = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        changed_files=["docs/note.md"],
    )

    files_before = set(tmp_path.rglob("*"))
    main(["remote", "changes", "show", job_id, "--json"])
    capsys.readouterr()
    files_after = set(tmp_path.rglob("*"))

    assert files_after == files_before


# ---------------------------------------------------------------------------
# Phase 42C — Human Approval Gate for Changes
# ---------------------------------------------------------------------------


def _setup_executed_job(
    tmp_path: Path,
    monkeypatch,
    capsys,
    agent: str = "claude-local",
    changed_files: list[str] | None = None,
) -> str:
    """Create, execute, and return a job_id with a result artifact on disk."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id, _ = _invoke_job_with_file_changes(
        tmp_path,
        monkeypatch,
        capsys,
        agent=agent,
        changed_files=changed_files if changed_files is not None else ["docs/note.md"],
    )
    return job_id


def test_42c_approve_valid_job_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    exit_code = main(["remote", "changes", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["updated"] is True
    assert data["new_change_approval_state"] == "approved"


def test_42c_approve_json_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "changes", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    for key in (
        "updated",
        "job_id",
        "previous_change_approval_state",
        "new_change_approval_state",
        "commit_allowed",
        "push_allowed",
        "advisory",
    ):
        assert key in data, f"missing key: {key}"


def test_42c_approve_sets_commit_allowed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "changes", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["commit_allowed"] is True
    assert data["push_allowed"] is False


def test_42c_approve_persists_state_in_job_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "changes", "approve", job_id, "--json"])
    capsys.readouterr()

    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    job = json.loads(job_file.read_text())
    assert job["change_approval_state"] == "approved"


def test_42c_deny_valid_job_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    exit_code = main(["remote", "changes", "deny", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["updated"] is True
    assert data["new_change_approval_state"] == "denied"


def test_42c_deny_sets_commit_not_allowed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "changes", "deny", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["commit_allowed"] is False
    assert data["push_allowed"] is False


def test_42c_deny_persists_state_in_job_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "changes", "deny", job_id, "--json"])
    capsys.readouterr()

    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    job = json.loads(job_file.read_text())
    assert job["change_approval_state"] == "denied"


def test_42c_no_change_job_cannot_be_approved(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """A job that produced no file changes cannot be approved."""
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=[])

    exit_code = main(["remote", "changes", "approve", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "no files were changed" in output.lower() or "cannot approve" in output.lower()


def test_42c_scope_violation_job_cannot_be_approved(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """A job with scope violations cannot be approved."""
    job_id = _setup_executed_job(
        tmp_path, monkeypatch, capsys, changed_files=["src/pcae/core/agent.py"]
    )

    exit_code = main(["remote", "changes", "approve", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "scope" in output.lower() or "cannot approve" in output.lower()


def test_42c_deny_allowed_for_scope_violation_job(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Denial is allowed even when scope is violated."""
    job_id = _setup_executed_job(
        tmp_path, monkeypatch, capsys, changed_files=["src/pcae/core/agent.py"]
    )

    exit_code = main(["remote", "changes", "deny", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["new_change_approval_state"] == "denied"


def test_42c_approve_missing_artifact_returns_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Approve fails when no result artifact exists."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")

    exit_code = main(["remote", "changes", "approve", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "no result artifact" in output.lower() or "cannot approve" in output.lower()


def test_42c_deny_missing_artifact_returns_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Deny fails when no result artifact exists."""
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")

    exit_code = main(["remote", "changes", "deny", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "no result artifact" in output.lower() or "cannot deny" in output.lower()


def test_42c_approve_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "changes", "approve", job_id])
    output = capsys.readouterr().out

    assert "approved" in output.lower()
    assert "Commit allowed" in output
    assert "no commit or push" in output.lower()


def test_42c_deny_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "changes", "deny", job_id])
    output = capsys.readouterr().out

    assert "denied" in output.lower()
    assert "no commit or push" in output.lower()


def test_42c_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "changes", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "no commit or push" in data["advisory"].lower()


def test_42c_previous_state_is_pending_initially(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "changes", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["previous_change_approval_state"] == "pending"


# ---------------------------------------------------------------------------
# Phase 42D — Controlled Commit
# ---------------------------------------------------------------------------


def _setup_approved_change(
    tmp_path: Path,
    monkeypatch,
    capsys,
    agent: str = "claude-local",
    changed_files: list[str] | None = None,
) -> str:
    """Create, execute, approve changes, and return job_id. Drains capsys."""
    if changed_files is None:
        changed_files = ["docs/note.md"]
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, agent=agent, changed_files=changed_files)
    main(["remote", "changes", "approve", job_id, "--json"])
    capsys.readouterr()
    return job_id


def _patch_commit_helpers(
    monkeypatch,
    dirty_files: list[str] | None = None,
    commit_sha: str = "def5678",
    git_add_rc: int = 0,
    git_commit_rc: int = 0,
) -> None:
    """Patch git helpers for commit tests."""
    if dirty_files is None:
        dirty_files = ["docs/note.md"]
    monkeypatch.setattr(
        _agent_mod,
        "_capture_git_changed_files",
        _fake_git_changed_files(dirty_files),
    )
    monkeypatch.setattr(_agent_mod, "_capture_git_head", _fake_git_head(commit_sha))
    monkeypatch.setattr(
        _agent_mod,
        "_run_git_add",
        lambda files, cwd: _fake_proc(git_add_rc),
    )
    monkeypatch.setattr(
        _agent_mod,
        "_run_git_commit",
        lambda message, cwd: _fake_proc(git_commit_rc, stdout="[main abc1234] PCAE: ...\n"),
    )


def test_42d_approved_change_can_be_committed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys)
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md"])

    exit_code = main(["remote", "commit", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["committed"] is True


def test_42d_commit_json_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys)
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md"])

    main(["remote", "commit", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    for key in ("committed", "job_id", "commit_sha", "changed_files", "push_allowed", "advisory"):
        assert key in data, f"missing key: {key}"


def test_42d_commit_sha_captured(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys)
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md"], commit_sha="cafe1234")

    main(["remote", "commit", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["commit_sha"] == "cafe1234"


def test_42d_push_always_false(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys)
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md"])

    main(["remote", "commit", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["push_allowed"] is False


def test_42d_commit_persists_sha_in_job_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys)
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md"], commit_sha="abc9999")

    main(["remote", "commit", job_id, "--json"])
    capsys.readouterr()

    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    job = json.loads(job_file.read_text())
    assert job["commit_sha"] == "abc9999"
    assert "committed_at" in job


def test_42d_pending_change_cannot_be_committed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md"])

    exit_code = main(["remote", "commit", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "pending" in output.lower() or "cannot commit" in output.lower()


def test_42d_denied_change_cannot_be_committed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    main(["remote", "changes", "deny", job_id])
    capsys.readouterr()
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md"])

    exit_code = main(["remote", "commit", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "denied" in output.lower() or "cannot commit" in output.lower()


def test_42d_no_changed_files_cannot_be_committed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(
        tmp_path, monkeypatch, capsys, changed_files=[]
    )
    _patch_commit_helpers(monkeypatch, dirty_files=[])

    exit_code = main(["remote", "commit", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "no files were changed" in output.lower() or "cannot commit" in output.lower()


def test_42d_scope_violation_cannot_be_committed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """A scope-violated job cannot be committed (and cannot be approved)."""
    job_id = _setup_executed_job(
        tmp_path, monkeypatch, capsys, changed_files=["src/pcae/core/agent.py"]
    )
    _patch_commit_helpers(monkeypatch, dirty_files=["src/pcae/core/agent.py"])

    exit_code = main(["remote", "commit", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "scope" in output.lower() or "cannot commit" in output.lower()


def test_42d_unexpected_dirty_files_blocks_commit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md", "docs/extra.md"])

    exit_code = main(["remote", "commit", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "unexpected" in output.lower() or "cannot commit" in output.lower()


def test_42d_missing_expected_file_blocks_commit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    _patch_commit_helpers(monkeypatch, dirty_files=[])

    exit_code = main(["remote", "commit", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "not found in working tree" in output.lower() or "cannot commit" in output.lower()


def test_42d_git_add_failure_blocks_commit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys)
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md"], git_add_rc=1)

    exit_code = main(["remote", "commit", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "git add failed" in output.lower() or "cannot commit" in output.lower()


def test_42d_git_commit_failure_blocks_commit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys)
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md"], git_commit_rc=1)

    exit_code = main(["remote", "commit", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "git commit failed" in output.lower() or "cannot commit" in output.lower()


def test_42d_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys)
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md"])

    main(["remote", "commit", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "no push was performed" in data["advisory"].lower()


def test_42d_human_output_key_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys)
    _patch_commit_helpers(monkeypatch, dirty_files=["docs/note.md"], commit_sha="abc1234")

    main(["remote", "commit", job_id])
    output = capsys.readouterr().out

    assert "Commit SHA" in output or "commit" in output.lower()
    assert "abc1234" in output
    assert "no push" in output.lower()


def test_42d_missing_job_returns_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "commit", "nonexistent-job-id"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "unknown job" in output.lower() or "cannot commit" in output.lower()


# ---------------------------------------------------------------------------
# Phase 42E — Controlled Push
# ---------------------------------------------------------------------------


def _setup_committed_change(
    tmp_path: Path,
    monkeypatch,
    capsys,
    agent: str = "claude-local",
    changed_files: list[str] | None = None,
    commit_sha: str = "def5678",
) -> str:
    """Create, execute, approve, and commit changes. Returns job_id."""
    if changed_files is None:
        changed_files = ["docs/note.md"]
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys, agent=agent, changed_files=changed_files)
    _patch_commit_helpers(monkeypatch, dirty_files=changed_files, commit_sha=commit_sha)
    main(["remote", "commit", job_id, "--json"])
    capsys.readouterr()
    return job_id


def _patch_push_helpers(
    monkeypatch,
    dirty_files: list[str] | None = None,
    head_sha: str = "def5678",
    branch: str = "main",
    remote: str = "origin",
    push_rc: int = 0,
) -> None:
    """Patch git helpers for push tests."""
    if dirty_files is None:
        dirty_files = []
    monkeypatch.setattr(
        _agent_mod,
        "_capture_git_changed_files",
        _fake_git_changed_files(dirty_files),
    )
    monkeypatch.setattr(_agent_mod, "_capture_git_head", _fake_git_head(head_sha))
    monkeypatch.setattr(_agent_mod, "_get_current_branch", lambda root: branch)
    monkeypatch.setattr(_agent_mod, "_get_git_remote", lambda root: remote)
    monkeypatch.setattr(
        _agent_mod,
        "_run_git_push",
        lambda rem, br, cwd: _fake_proc(push_rc, stdout="To origin\n" if push_rc == 0 else ""),
    )


def test_42e_approved_committed_change_can_be_pushed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_push_helpers(monkeypatch)

    exit_code = main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["pushed"] is True


def test_42e_push_json_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_push_helpers(monkeypatch)

    main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    for key in ("pushed", "job_id", "commit_sha", "remote_branch", "push_status", "advisory"):
        assert key in data, f"missing key: {key}"


def test_42e_push_status_is_pushed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_push_helpers(monkeypatch)

    main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["push_status"] == "pushed"


def test_42e_commit_sha_in_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, commit_sha="cafe9876")
    _patch_push_helpers(monkeypatch, head_sha="cafe9876")

    main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["commit_sha"] == "cafe9876"


def test_42e_remote_branch_in_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_push_helpers(monkeypatch, branch="main", remote="origin")

    main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["remote_branch"] == "origin/main"


def test_42e_job_updated_with_push_metadata(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_push_helpers(monkeypatch)

    main(["remote", "push", job_id, "--json"])
    capsys.readouterr()

    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    job = json.loads(job_file.read_text())
    assert job["push_status"] == "pushed"
    assert "pushed_at" in job
    assert "remote_branch" in job


def test_42e_pending_change_cannot_be_pushed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    _patch_push_helpers(monkeypatch)

    exit_code = main(["remote", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "pending" in output.lower() or "cannot push" in output.lower()


def test_42e_denied_change_cannot_be_pushed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    main(["remote", "changes", "deny", job_id])
    capsys.readouterr()
    _patch_push_helpers(monkeypatch)

    exit_code = main(["remote", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "denied" in output.lower() or "cannot push" in output.lower()


def test_42e_no_governed_commit_blocks_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Approved job without a commit cannot be pushed."""
    job_id = _setup_approved_change(tmp_path, monkeypatch, capsys)
    _patch_push_helpers(monkeypatch)

    exit_code = main(["remote", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "no governed commit" in output.lower() or "cannot push" in output.lower()


def test_42e_dirty_working_tree_blocks_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_push_helpers(monkeypatch, dirty_files=["docs/unexpected.md"])

    exit_code = main(["remote", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "dirty" in output.lower() or "cannot push" in output.lower()


def test_42e_head_mismatch_blocks_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_push_helpers(monkeypatch, head_sha="aaabbb1")
    monkeypatch.setattr(_agent_mod, "_check_commit_is_ancestor", lambda sha, cwd: False)

    exit_code = main(["remote", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "not in current branch history" in output.lower() or "cannot push" in output.lower()


def test_42e_git_push_failure_blocks_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_push_helpers(monkeypatch, push_rc=1)

    exit_code = main(["remote", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "git push failed" in output.lower() or "cannot push" in output.lower()


def test_42e_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_push_helpers(monkeypatch)

    main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "push completed" in data["advisory"].lower()
    assert "governance" in data["advisory"].lower()


def test_42e_human_output_key_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_push_helpers(monkeypatch, head_sha="def5678", branch="main", remote="origin")

    main(["remote", "push", job_id])
    output = capsys.readouterr().out

    assert "def5678" in output
    assert "origin/main" in output
    assert "pushed" in output.lower()
    assert "governance" in output.lower()


def test_42e_missing_job_returns_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "push", "nonexistent-job-id"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "unknown job" in output.lower() or "cannot push" in output.lower()


# ---------------------------------------------------------------------------
# Phase 43A — Governed Rollback Design
# ---------------------------------------------------------------------------


def test_43a_rollback_governance_json_top_level_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "rollback-governance", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    for key in ("advisory", "rollback_governance", "rollback_modes", "risk_model", "approval_model"):
        assert key in data, f"missing top-level key: {key}"


def test_43a_rollback_governance_inner_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "rollback-governance", "--json"])
    data = json.loads(capsys.readouterr().out)

    gov = data["rollback_governance"]
    for key in ("eligibility_model", "rollback_artifacts", "safety_rules"):
        assert key in gov, f"missing rollback_governance key: {key}"


def test_43a_rollback_modes_defined(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "rollback-governance", "--json"])
    data = json.loads(capsys.readouterr().out)

    modes = {m["mode"] for m in data["rollback_modes"]}
    assert "revert_commit" in modes
    assert "restore_files" in modes
    assert "reset_branch" in modes


def test_43a_reset_branch_not_allowed_by_default(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "rollback-governance", "--json"])
    data = json.loads(capsys.readouterr().out)

    reset = next(m for m in data["rollback_modes"] if m["mode"] == "reset_branch")
    assert reset["allowed_by_default"] is False
    assert reset["risk_level"] == "critical"
    assert "dangerous" in reset["notes"].lower() or "not allowed" in reset["notes"].lower()


def test_43a_revert_commit_is_preferred(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "rollback-governance", "--json"])
    data = json.loads(capsys.readouterr().out)

    revert = next(m for m in data["rollback_modes"] if m["mode"] == "revert_commit")
    assert revert["preferred"] is True
    assert revert["allowed_by_default"] is True


def test_43a_approval_model_defined(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "rollback-governance", "--json"])
    data = json.loads(capsys.readouterr().out)

    am = data["approval_model"]
    assert am["rollback_review_required"] is True
    assert am["rollback_approval_required"] is True
    assert am["rollback_commit_separate"] is True
    assert am["rollback_push_separate"] is True
    assert am["auto_rollback_allowed"] is False


def test_43a_risk_model_four_levels(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "rollback-governance", "--json"])
    data = json.loads(capsys.readouterr().out)

    levels = {lvl["level"] for lvl in data["risk_model"]["levels"]}
    assert levels == {"low", "medium", "high", "critical"}


def test_43a_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["remote", "rollback-governance", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "no rollback is performed" in data["advisory"].lower()


def test_43a_human_output_key_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "rollback-governance"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Rollback Governance Design" in output
    assert "Rollback Modes" in output
    assert "Safety Rules" in output
    assert "Risk Model" in output
    assert "Approval Model" in output
    assert "no rollback is performed" in output.lower()


def test_43a_read_only_no_execution(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before = list((tmp_path / ".pcae").rglob("*"))
    main(["remote", "rollback-governance", "--json"])
    capsys.readouterr()
    after = list((tmp_path / ".pcae").rglob("*"))

    assert before == after


# ---------------------------------------------------------------------------
# Phase 42E.1 — Governed Commit Lineage Validation
# ---------------------------------------------------------------------------


def _patch_push_lineage(monkeypatch, is_ancestor: bool = True) -> None:
    """Patch _check_commit_is_ancestor for push tests where HEAD != commit."""
    monkeypatch.setattr(
        _agent_mod,
        "_check_commit_is_ancestor",
        lambda sha, cwd: is_ancestor,
    )


def test_42e1_push_allowed_when_head_equals_commit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Exact match: HEAD == governed commit → push succeeds, no warning."""
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_push_helpers(monkeypatch, head_sha="def5678")

    exit_code = main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["pushed"] is True


def test_42e1_push_allowed_when_commit_is_ancestor(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Ancestor: governed commit is reachable from HEAD → push succeeds."""
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_push_helpers(monkeypatch, head_sha="advanced1")
    _patch_push_lineage(monkeypatch, is_ancestor=True)

    exit_code = main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["pushed"] is True


def test_42e1_warning_shown_when_head_has_advanced_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """When HEAD advanced beyond governed commit, warning appears in JSON."""
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_push_helpers(monkeypatch, head_sha="advanced1")
    _patch_push_lineage(monkeypatch, is_ancestor=True)

    main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert len(data["warnings"]) > 0
    assert any("additional commits" in w.lower() for w in data["warnings"])


def test_42e1_warning_shown_when_head_has_advanced_human(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """When HEAD advanced beyond governed commit, warning appears in human output."""
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_push_helpers(monkeypatch, head_sha="advanced1")
    _patch_push_lineage(monkeypatch, is_ancestor=True)

    main(["remote", "push", job_id])
    output = capsys.readouterr().out

    assert "warning" in output.lower()
    assert "additional commits" in output.lower()


def test_42e1_push_blocked_when_commit_not_in_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Governed commit is not reachable from HEAD → push blocked."""
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_push_helpers(monkeypatch, head_sha="diverged1")
    _patch_push_lineage(monkeypatch, is_ancestor=False)

    exit_code = main(["remote", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "not in current branch history" in output.lower() or "cannot push" in output.lower()


def test_42e1_json_includes_lineage_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_push_helpers(monkeypatch)

    main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "lineage_status" in data


def test_42e1_json_includes_warnings_field(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_push_helpers(monkeypatch)

    main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "warnings" in data
    assert isinstance(data["warnings"], list)


def test_42e1_lineage_status_exact_match(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_push_helpers(monkeypatch, head_sha="def5678")

    main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["lineage_status"] == "exact_match"


def test_42e1_lineage_status_ancestor(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_push_helpers(monkeypatch, head_sha="advanced1")
    _patch_push_lineage(monkeypatch, is_ancestor=True)

    main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["lineage_status"] == "ancestor"


def test_42e1_exact_match_has_no_warnings(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_push_helpers(monkeypatch, head_sha="def5678")

    main(["remote", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["warnings"] == []


# ---------------------------------------------------------------------------
# Phase 43B — Rollback Review Artifacts
# ---------------------------------------------------------------------------


def test_43b_rollback_review_json_top_level_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)

    exit_code = main(["remote", "rollback-review", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert "rollback_review" in data
    assert "advisory" in data


def test_43b_rollback_review_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)

    main(["remote", "rollback-review", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    review = data["rollback_review"]
    for key in (
        "job_id",
        "original_commit_sha",
        "rollback_mode_recommendation",
        "rollback_eligible",
        "affected_files",
        "rollback_risk_level",
        "rollback_approval_required",
        "rollback_commit_required",
        "rollback_push_required",
    ):
        assert key in review, f"missing field: {key}"


def test_43b_eligible_job_is_eligible(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback-review", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["rollback_review"]["rollback_eligible"] is True


def test_43b_no_artifact_not_eligible(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    job_id = _create_approved_job(tmp_path, monkeypatch, capsys, agent="claude-local")

    exit_code = main(["remote", "rollback-review", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["rollback_review"]["rollback_eligible"] is False
    notes = " ".join(data["rollback_review"]["eligibility_notes"]).lower()
    assert "no result artifact" in notes or "no governed commit" in notes


def test_43b_no_commit_sha_not_eligible(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback-review", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    review = data["rollback_review"]
    assert review["rollback_eligible"] is False
    notes = " ".join(review["eligibility_notes"]).lower()
    assert "no governed commit" in notes


def test_43b_revert_commit_recommended_for_eligible_job(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback-review", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["rollback_review"]["rollback_mode_recommendation"] == "revert_commit"


def test_43b_docs_only_is_low_risk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback-review", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["rollback_review"]["rollback_risk_level"] == "low"


def test_43b_src_change_is_medium_or_higher_risk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(
        tmp_path, monkeypatch, capsys, changed_files=["src/pcae/core/agent.py"]
    )

    main(["remote", "rollback-review", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["rollback_review"]["rollback_risk_level"] in ("medium", "critical")


def test_43b_approval_fields_always_true(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)

    main(["remote", "rollback-review", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    review = data["rollback_review"]
    assert review["rollback_approval_required"] is True
    assert review["rollback_commit_required"] is True
    assert review["rollback_push_required"] is True


def test_43b_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)

    main(["remote", "rollback-review", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "no rollback is performed" in data["advisory"].lower()


def test_43b_human_output_key_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    exit_code = main(["remote", "rollback-review", job_id])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Rollback Review" in output
    assert "revert_commit" in output
    assert "Affected files" in output or "affected" in output.lower()
    assert "no rollback is performed" in output.lower()


def test_43b_read_only_no_file_mutations(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)

    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    before = job_file.read_text()

    main(["remote", "rollback-review", job_id, "--json"])
    capsys.readouterr()

    assert job_file.read_text() == before


def test_43b_missing_job_returns_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "rollback-review", "no-such-job"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "unknown job" in output.lower()


# ---------------------------------------------------------------------------
# Phase 43C — Rollback Approval Gate
# ---------------------------------------------------------------------------


def test_43c_approve_eligible_job_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    exit_code = main(["remote", "rollback", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["updated"] is True
    assert data["new_rollback_approval_state"] == "approved"


def test_43c_approve_json_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    for key in (
        "updated",
        "job_id",
        "previous_rollback_approval_state",
        "new_rollback_approval_state",
        "rollback_eligible",
        "rollback_mode_recommendation",
        "advisory",
    ):
        assert key in data, f"missing key: {key}"


def test_43c_approve_eligible_sets_rollback_eligible_true(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["rollback_eligible"] is True
    assert data["rollback_mode_recommendation"] == "revert_commit"


def test_43c_approve_persists_state_in_job_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback", "approve", job_id, "--json"])
    capsys.readouterr()

    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    job = json.loads(job_file.read_text())
    assert job["rollback_approval_state"] == "approved"


def test_43c_approve_records_previous_state(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["previous_rollback_approval_state"] == "pending"


def test_43c_ineligible_rollback_cannot_be_approved(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    exit_code = main(["remote", "rollback", "approve", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "not eligible" in output.lower()


def test_43c_deny_eligible_job_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    exit_code = main(["remote", "rollback", "deny", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["updated"] is True
    assert data["new_rollback_approval_state"] == "denied"


def test_43c_deny_ineligible_job_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_executed_job(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    exit_code = main(["remote", "rollback", "deny", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["updated"] is True
    assert data["new_rollback_approval_state"] == "denied"
    assert data["rollback_eligible"] is False


def test_43c_deny_json_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback", "deny", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    for key in (
        "updated",
        "job_id",
        "previous_rollback_approval_state",
        "new_rollback_approval_state",
        "rollback_eligible",
        "rollback_mode_recommendation",
        "advisory",
    ):
        assert key in data, f"missing key: {key}"


def test_43c_deny_persists_state_in_job_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback", "deny", job_id, "--json"])
    capsys.readouterr()

    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    job = json.loads(job_file.read_text())
    assert job["rollback_approval_state"] == "denied"


def test_43c_advisory_text_approve(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "no rollback was performed" in data["advisory"].lower()


def test_43c_advisory_text_deny(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    main(["remote", "rollback", "deny", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "no rollback was performed" in data["advisory"].lower()


def test_43c_human_output_approve(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    exit_code = main(["remote", "rollback", "approve", job_id])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Rollback Approval" in output
    assert "approved" in output
    assert "revert_commit" in output
    assert "no rollback was performed" in output.lower()


def test_43c_human_output_deny(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    exit_code = main(["remote", "rollback", "deny", job_id])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Rollback Denial" in output
    assert "denied" in output
    assert "no rollback was performed" in output.lower()


def test_43c_no_rollback_performed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])

    git_calls: list[str] = []

    original_run = __import__("subprocess").run

    def _spy_subprocess_run(cmd, **kwargs):
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "git":
            git_calls.append(str(cmd))
        return original_run(cmd, **kwargs)

    monkeypatch.setattr(__import__("subprocess"), "run", _spy_subprocess_run)

    main(["remote", "rollback", "approve", job_id, "--json"])
    capsys.readouterr()

    revert_or_reset = [c for c in git_calls if "revert" in c or "reset" in c or "commit" in c or "push" in c]
    assert revert_or_reset == [], f"Unexpected git calls: {revert_or_reset}"


def test_43c_missing_job_approve_returns_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "rollback", "approve", "no-such-job"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "unknown job" in output.lower()


def test_43c_missing_job_deny_returns_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "rollback", "deny", "no-such-job"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "unknown job" in output.lower()


# ---------------------------------------------------------------------------
# Phase 43D — Controlled Rollback Execution
# ---------------------------------------------------------------------------


def _setup_approved_rollback(
    tmp_path: Path,
    monkeypatch,
    capsys,
    commit_sha: str = "def5678",
    changed_files: list[str] | None = None,
) -> str:
    """Create, execute, commit, and rollback-approve a job. Returns job_id."""
    job_id = _setup_committed_change(
        tmp_path, monkeypatch, capsys,
        commit_sha=commit_sha,
        changed_files=changed_files or ["docs/note.md"],
    )
    main(["remote", "rollback", "approve", job_id, "--json"])
    capsys.readouterr()
    return job_id


def _patch_rollback_execute_helpers(
    monkeypatch,
    revert_rc: int = 0,
    revert_sha: str = "rev1234",
    dirty_files: list[str] | None = None,
    ancestor: bool = True,
) -> None:
    """Patch git helpers for rollback execute tests."""
    monkeypatch.setattr(
        _agent_mod,
        "_capture_git_changed_files",
        _fake_git_changed_files(dirty_files or []),
    )
    monkeypatch.setattr(_agent_mod, "_capture_git_head", _fake_git_head(revert_sha))
    monkeypatch.setattr(
        _agent_mod,
        "_run_git_revert",
        lambda sha, cwd: _fake_proc(revert_rc, stdout=f"[main {revert_sha}] Revert ...\n"),
    )
    monkeypatch.setattr(
        _agent_mod,
        "_check_commit_is_ancestor",
        lambda sha, cwd: ancestor,
    )


def test_43d_approved_rollback_creates_revert_commit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)

    exit_code = main(["remote", "rollback", "execute", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["rolled_back"] is True


def test_43d_json_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)

    main(["remote", "rollback", "execute", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    for key in (
        "rolled_back",
        "job_id",
        "original_commit_sha",
        "rollback_commit_sha",
        "rollback_status",
        "advisory",
    ):
        assert key in data, f"missing key: {key}"


def test_43d_rollback_commit_sha_captured(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch, revert_sha="cafe9876")

    main(["remote", "rollback", "execute", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["rollback_commit_sha"] == "cafe9876"


def test_43d_original_commit_sha_in_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_rollback_execute_helpers(monkeypatch)

    main(["remote", "rollback", "execute", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["original_commit_sha"] == "def5678"


def test_43d_persists_rollback_metadata(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch, revert_sha="cafe9876")

    main(["remote", "rollback", "execute", job_id, "--json"])
    capsys.readouterr()

    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    job = json.loads(job_file.read_text())
    assert job["rollback_commit_sha"] == "cafe9876"
    assert job["rollback_status"] == "rolled_back"
    assert "rolled_back_at" in job


def test_43d_rollback_status_is_rolled_back(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)

    main(["remote", "rollback", "execute", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["rollback_status"] == "rolled_back"


def test_43d_pending_approval_blocks_execute(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)

    exit_code = main(["remote", "rollback", "execute", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "pending" in output.lower()


def test_43d_denied_approval_blocks_execute(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    main(["remote", "rollback", "deny", job_id, "--json"])
    capsys.readouterr()
    _patch_rollback_execute_helpers(monkeypatch)

    exit_code = main(["remote", "rollback", "execute", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "denied" in output.lower()


def test_43d_dirty_tree_blocks_execute(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch, dirty_files=["docs/unexpected.md"])

    exit_code = main(["remote", "rollback", "execute", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "dirty" in output.lower()


def test_43d_commit_not_in_history_blocks_execute(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch, ancestor=False)

    exit_code = main(["remote", "rollback", "execute", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "not reachable from head" in output.lower()


def test_43d_git_revert_failure_blocks_execute(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch, revert_rc=1)

    exit_code = main(["remote", "rollback", "execute", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "rollback failed" in output.lower()


def test_43d_no_push_performed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)

    push_calls: list = []
    _patch_rollback_execute_helpers(monkeypatch)
    monkeypatch.setattr(
        _agent_mod,
        "_run_git_push",
        lambda remote, branch, cwd: push_calls.append((remote, branch)) or _fake_proc(0),
    )

    main(["remote", "rollback", "execute", job_id, "--json"])
    capsys.readouterr()

    assert push_calls == [], f"Unexpected push calls: {push_calls}"


def test_43d_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)

    main(["remote", "rollback", "execute", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "no push was performed" in data["advisory"].lower()


def test_43d_human_output_key_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys, commit_sha="def5678")
    _patch_rollback_execute_helpers(monkeypatch, revert_sha="rev1234")

    exit_code = main(["remote", "rollback", "execute", job_id])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Rollback Execution" in output
    assert "def5678" in output
    assert "rev1234" in output
    assert "rolled_back" in output
    assert "no push was performed" in output.lower()


def test_43d_missing_job_returns_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_agent_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["remote", "rollback", "execute", "no-such-job"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "unknown job" in output.lower()


# ---------------------------------------------------------------------------
# Phase 43D.1 — Rollback Result Consistency Fix
# ---------------------------------------------------------------------------


def test_43d1_second_execute_returns_already_rolled_back(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)

    # First execute — succeeds
    main(["remote", "rollback", "execute", job_id, "--json"])
    capsys.readouterr()

    # Second execute — must return already_rolled_back, not failure
    exit_code = main(["remote", "rollback", "execute", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["rollback_status"] == "already_rolled_back"
    assert data["rolled_back"] is True


def test_43d1_second_execute_preserves_rollback_sha(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch, revert_sha="cafe9876")

    main(["remote", "rollback", "execute", job_id, "--json"])
    capsys.readouterr()

    main(["remote", "rollback", "execute", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["rollback_commit_sha"] == "cafe9876"


def test_43d1_no_duplicate_revert_on_second_execute(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)

    revert_calls: list[str] = []
    original_revert = _agent_mod._run_git_revert

    def _counting_revert(sha: str, cwd: str):
        revert_calls.append(sha)
        return _fake_proc(0, stdout=f"[main rev1234] Revert\n")

    monkeypatch.setattr(_agent_mod, "_run_git_revert", _counting_revert)
    monkeypatch.setattr(_agent_mod, "_capture_git_changed_files", _fake_git_changed_files([]))
    monkeypatch.setattr(_agent_mod, "_capture_git_head", _fake_git_head("rev1234"))
    monkeypatch.setattr(_agent_mod, "_check_commit_is_ancestor", lambda sha, cwd: True)

    main(["remote", "rollback", "execute", job_id, "--json"])
    capsys.readouterr()
    assert len(revert_calls) == 1

    main(["remote", "rollback", "execute", job_id, "--json"])
    capsys.readouterr()
    assert len(revert_calls) == 1, "git revert must not run a second time"


def test_43d1_already_rolled_back_json_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)

    main(["remote", "rollback", "execute", job_id, "--json"])
    capsys.readouterr()

    main(["remote", "rollback", "execute", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    for key in (
        "rolled_back",
        "job_id",
        "original_commit_sha",
        "rollback_commit_sha",
        "rollback_status",
        "advisory",
    ):
        assert key in data, f"missing key: {key}"


def test_43d1_success_does_not_emit_failure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)

    exit_code = main(["remote", "rollback", "execute", job_id])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "failed" not in output.lower()
    assert "error" not in output.lower()


def test_43d1_human_and_json_agree_on_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)

    # First call — both outputs must say rolled_back
    main(["remote", "rollback", "execute", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["rollback_status"] == "rolled_back"
    assert data["rolled_back"] is True

    # Second call — both outputs must say already_rolled_back
    main(["remote", "rollback", "execute", job_id])
    human = capsys.readouterr().out
    main(["remote", "rollback", "execute", job_id, "--json"])
    data2 = json.loads(capsys.readouterr().out)

    assert data2["rollback_status"] == "already_rolled_back"
    assert "already_rolled_back" in human


# ---------------------------------------------------------------------------
# Phase 43E — Controlled Rollback Push
# ---------------------------------------------------------------------------


def _setup_rolled_back_job(
    tmp_path: Path,
    monkeypatch,
    capsys,
    commit_sha: str = "def5678",
    revert_sha: str = "rev1234",
) -> str:
    """Create, commit, rollback-approve, and execute rollback. Returns job_id."""
    job_id = _setup_approved_rollback(
        tmp_path, monkeypatch, capsys, commit_sha=commit_sha
    )
    _patch_rollback_execute_helpers(monkeypatch, revert_sha=revert_sha)
    main(["remote", "rollback", "execute", job_id, "--json"])
    capsys.readouterr()
    return job_id


def _patch_rollback_push_helpers(
    monkeypatch,
    dirty_files: list[str] | None = None,
    ancestor: bool = True,
    branch: str = "main",
    remote: str = "origin",
    push_rc: int = 0,
) -> None:
    """Patch git helpers for rollback push tests."""
    monkeypatch.setattr(
        _agent_mod,
        "_capture_git_changed_files",
        _fake_git_changed_files(dirty_files or []),
    )
    monkeypatch.setattr(
        _agent_mod,
        "_check_commit_is_ancestor",
        lambda sha, cwd: ancestor,
    )
    monkeypatch.setattr(_agent_mod, "_get_current_branch", lambda root: branch)
    monkeypatch.setattr(_agent_mod, "_get_git_remote", lambda root: remote)
    monkeypatch.setattr(
        _agent_mod,
        "_run_git_push",
        lambda rem, br, cwd: _fake_proc(push_rc, stdout="To origin\n" if push_rc == 0 else ""),
    )


def test_43e_approved_executed_rollback_can_be_pushed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_rolled_back_job(tmp_path, monkeypatch, capsys)
    _patch_rollback_push_helpers(monkeypatch)

    exit_code = main(["remote", "rollback", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["pushed"] is True


def test_43e_push_json_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_rolled_back_job(tmp_path, monkeypatch, capsys)
    _patch_rollback_push_helpers(monkeypatch)

    main(["remote", "rollback", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    for key in ("pushed", "job_id", "rollback_commit_sha", "remote_branch", "push_status", "advisory"):
        assert key in data, f"missing key: {key}"


def test_43e_push_status_is_pushed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_rolled_back_job(tmp_path, monkeypatch, capsys)
    _patch_rollback_push_helpers(monkeypatch)

    main(["remote", "rollback", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["push_status"] == "pushed"


def test_43e_rollback_commit_sha_in_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_rolled_back_job(tmp_path, monkeypatch, capsys, revert_sha="cafe9876")
    _patch_rollback_push_helpers(monkeypatch)

    main(["remote", "rollback", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["rollback_commit_sha"] == "cafe9876"


def test_43e_persists_push_metadata(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_rolled_back_job(tmp_path, monkeypatch, capsys)
    _patch_rollback_push_helpers(monkeypatch, branch="main", remote="origin")

    main(["remote", "rollback", "push", job_id, "--json"])
    capsys.readouterr()

    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    job = json.loads(job_file.read_text())
    assert job["rollback_push_status"] == "pushed"
    assert job["rollback_remote_branch"] == "origin/main"
    assert "rollback_pushed_at" in job


def test_43e_pending_approval_blocks_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_rollback_push_helpers(monkeypatch)

    exit_code = main(["remote", "rollback", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "pending" in output.lower()


def test_43e_denied_approval_blocks_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    main(["remote", "rollback", "deny", job_id, "--json"])
    capsys.readouterr()
    _patch_rollback_push_helpers(monkeypatch)

    exit_code = main(["remote", "rollback", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "denied" in output.lower()


def test_43e_missing_rollback_sha_blocks_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_push_helpers(monkeypatch)

    exit_code = main(["remote", "rollback", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "no rollback commit found" in output.lower()


def test_43e_dirty_tree_blocks_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_rolled_back_job(tmp_path, monkeypatch, capsys)
    _patch_rollback_push_helpers(monkeypatch, dirty_files=["docs/unexpected.md"])

    exit_code = main(["remote", "rollback", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "dirty" in output.lower()


def test_43e_rollback_commit_not_in_history_blocks_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_rolled_back_job(tmp_path, monkeypatch, capsys)
    _patch_rollback_push_helpers(monkeypatch, ancestor=False)

    exit_code = main(["remote", "rollback", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "not reachable from head" in output.lower()


def test_43e_no_rollback_commit_created_during_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_rolled_back_job(tmp_path, monkeypatch, capsys)

    revert_calls: list[str] = []
    _patch_rollback_push_helpers(monkeypatch)
    monkeypatch.setattr(
        _agent_mod,
        "_run_git_revert",
        lambda sha, cwd: revert_calls.append(sha) or _fake_proc(0),
    )

    main(["remote", "rollback", "push", job_id, "--json"])
    capsys.readouterr()

    assert revert_calls == [], f"git revert must not run during push: {revert_calls}"


def test_43e_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_rolled_back_job(tmp_path, monkeypatch, capsys)
    _patch_rollback_push_helpers(monkeypatch)

    main(["remote", "rollback", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "pcae governance" in data["advisory"].lower()


def test_43e_human_output_key_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_rolled_back_job(tmp_path, monkeypatch, capsys, revert_sha="rev1234")
    _patch_rollback_push_helpers(monkeypatch, branch="main", remote="origin")

    exit_code = main(["remote", "rollback", "push", job_id])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Rollback Push" in output
    assert "rev1234" in output
    assert "pushed" in output.lower()
    assert "origin/main" in output
    assert "pcae governance" in output.lower()


def test_43e_already_rolled_back_status_can_be_pushed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_rolled_back_job(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    # second execute → already_rolled_back
    main(["remote", "rollback", "execute", job_id, "--json"])
    capsys.readouterr()

    _patch_rollback_push_helpers(monkeypatch)
    exit_code = main(["remote", "rollback", "push", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["pushed"] is True


# ---------------------------------------------------------------------------
# Phase 44A: Multi-Agent Collaboration Design
# ---------------------------------------------------------------------------


def test_44a_collaboration_design_command_exits_zero(capsys) -> None:
    exit_code = main(["collaboration-design"])
    assert exit_code == 0


def test_44a_collaboration_design_json_exits_zero(capsys) -> None:
    exit_code = main(["collaboration-design", "--json"])
    assert exit_code == 0


def test_44a_collaboration_design_json_has_required_top_level_keys(capsys) -> None:
    main(["collaboration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "collaboration_design" in data
    assert "runtime_mapping" in data
    assert "governance_model" in data
    assert "conflict_model" in data
    assert "advisory" in data


def test_44a_collaboration_design_defines_four_agent_roles(capsys) -> None:
    main(["collaboration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    roles = [r["role"] for r in data["collaboration_design"]["agent_roles"]]
    assert "planner" in roles
    assert "implementer" in roles
    assert "reviewer" in roles
    assert "validator" in roles


def test_44a_collaboration_design_only_implementer_may_modify_files(capsys) -> None:
    main(["collaboration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    for role_def in data["collaboration_design"]["agent_roles"]:
        if role_def["role"] == "implementer":
            assert role_def["may_modify_files"] is True
        else:
            assert role_def["may_modify_files"] is False


def test_44a_collaboration_design_runtime_mapping_includes_all_agents(capsys) -> None:
    main(["collaboration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    agent_ids = [m["agent_id"] for m in data["runtime_mapping"]]
    assert "codex-local" in agent_ids
    assert "claude-local" in agent_ids
    assert "kimi-local" in agent_ids


def test_44a_collaboration_design_all_agents_support_all_four_roles(capsys) -> None:
    main(["collaboration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    for mapping in data["runtime_mapping"]:
        roles = mapping["supported_roles"]
        assert "planner" in roles
        assert "implementer" in roles
        assert "reviewer" in roles
        assert "validator" in roles


def test_44a_collaboration_design_governance_model_has_rules(capsys) -> None:
    main(["collaboration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    rules = data["governance_model"]["rules"]
    assert len(rules) > 0
    assert any("implementer may modify files" in r for r in rules)
    assert any("approval required before commit" in r for r in rules)
    assert any("commit required before push" in r for r in rules)


def test_44a_collaboration_design_conflict_model_covers_halt_conditions(capsys) -> None:
    main(["collaboration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    conditions = [item["condition"] for item in data["conflict_model"]]
    assert any("reviewer rejects" in c for c in conditions)
    assert any("validator fails" in c for c in conditions)
    assert any("scope validation fails" in c for c in conditions)
    for item in data["conflict_model"]:
        assert item["outcome"] == "execution halted"


def test_44a_collaboration_design_advisory_is_correct(capsys) -> None:
    main(["collaboration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data
    assert "advisory" in data["advisory"].lower()
    assert "no orchestration" in data["advisory"].lower()


def test_44a_collaboration_design_human_output_shows_agent_roles(capsys) -> None:
    main(["collaboration-design"])
    output = capsys.readouterr().out
    assert "planner" in output
    assert "implementer" in output
    assert "reviewer" in output
    assert "validator" in output


def test_44a_collaboration_design_human_output_shows_advisory(capsys) -> None:
    main(["collaboration-design"])
    output = capsys.readouterr().out
    assert "advisory" in output.lower()


# ---------------------------------------------------------------------------
# Phase 44B: Multi-Agent Orchestration Design
# ---------------------------------------------------------------------------


def test_44b_orchestration_design_command_exits_zero(capsys) -> None:
    exit_code = main(["orchestration-design"])
    assert exit_code == 0


def test_44b_orchestration_design_json_exits_zero(capsys) -> None:
    exit_code = main(["orchestration-design", "--json"])
    assert exit_code == 0


def test_44b_orchestration_design_json_has_required_top_level_keys(capsys) -> None:
    main(["orchestration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "orchestration_design" in data
    assert "capability_profile_model" in data
    assert "orchestration_patterns" in data
    assert "governance_integration" in data
    assert "conflict_resolution" in data
    assert "future_agent_expansion" in data
    assert "advisory" in data


def test_44b_orchestration_design_coordinator_responsibilities_defined(capsys) -> None:
    main(["orchestration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    responsibilities = data["orchestration_design"]["coordinator_responsibilities"]
    names = [r["name"] for r in responsibilities]
    assert "task_decomposition" in names
    assert "role_assignment" in names
    assert "parallel_execution_planning" in names
    assert "result_collection" in names
    assert "conflict_detection" in names
    assert "consensus_calculation" in names
    assert "governance_handoff" in names


def test_44b_orchestration_design_capability_profile_model_defined(capsys) -> None:
    main(["orchestration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    model = data["capability_profile_model"]
    fields = model["fields"]
    assert "agent_id" in fields
    assert "runtime" in fields
    assert "lifecycle_status" in fields
    assert "capabilities" in fields
    assert "writable_supported" in fields
    assert "subagent_supported" in fields
    assert "evidence_source" in fields
    assert "confidence" in fields
    cats = model["capability_categories"]
    assert "planning" in cats
    assert "implementation" in cats
    assert "review" in cats
    assert "validation" in cats
    assert "research" in cats
    assert "testing" in cats
    assert "architecture" in cats
    assert "documentation" in cats
    assert "security" in cats
    assert "performance" in cats
    assert "dependency-analysis" in cats
    assert "data-science" in cats
    assert "devops" in cats


def test_44b_orchestration_design_patterns_defined(capsys) -> None:
    main(["orchestration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    patterns = [p["pattern"] for p in data["orchestration_patterns"]]
    assert "sequential" in patterns
    assert "parallel_review" in patterns
    assert "parallel_planning" in patterns
    assert "swarm" in patterns
    assert "full_pipeline" in patterns


def test_44b_orchestration_design_governance_rules_defined(capsys) -> None:
    main(["orchestration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    rules = data["governance_integration"]["rules"]
    assert len(rules) > 0
    assert any("only implementer" in r for r in rules)
    assert any("read-only" in r for r in rules)
    assert any("human remains authoritative" in r for r in rules)


def test_44b_orchestration_design_conflict_resolution_model_defined(capsys) -> None:
    main(["orchestration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    cr = data["conflict_resolution"]
    policies = [p["policy"] for p in cr["policies"]]
    assert "unanimous" in policies
    assert "majority" in policies
    assert "weighted" in policies
    assert "human_escalation" in policies
    assert cr["default_policy"] == "human_escalation"
    assert "escalation_rule" in cr


def test_44b_orchestration_design_future_agent_expansion_included(capsys) -> None:
    main(["orchestration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    agents = [a["agent_id"] for a in data["future_agent_expansion"]]
    assert "deepseek-local" in agents
    assert "gemini-local" in agents
    assert "grok-local" in agents
    assert "perplexity-local" in agents


def test_44b_orchestration_design_advisory_is_correct(capsys) -> None:
    main(["orchestration-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data
    assert "advisory" in data["advisory"].lower()
    assert "no orchestration" in data["advisory"].lower()


def test_44b_orchestration_design_human_output_shows_coordinator_responsibilities(
    capsys,
) -> None:
    main(["orchestration-design"])
    output = capsys.readouterr().out
    assert "task_decomposition" in output
    assert "role_assignment" in output
    assert "governance_handoff" in output


def test_44b_orchestration_design_human_output_shows_patterns(capsys) -> None:
    main(["orchestration-design"])
    output = capsys.readouterr().out
    assert "sequential" in output
    assert "parallel_review" in output
    assert "swarm" in output
    assert "full_pipeline" in output


def test_44b_orchestration_design_human_output_shows_advisory(capsys) -> None:
    main(["orchestration-design"])
    output = capsys.readouterr().out
    assert "advisory" in output.lower()


# ---------------------------------------------------------------------------
# Phase 44C: Agent Capability Auto-Discovery
# ---------------------------------------------------------------------------


def test_44c_capability_registry_command_exits_zero(capsys) -> None:
    exit_code = main(["capability-registry"])
    assert exit_code == 0


def test_44c_capability_registry_json_exits_zero(capsys) -> None:
    exit_code = main(["capability-registry", "--json"])
    assert exit_code == 0


def test_44c_capability_registry_json_has_required_top_level_keys(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "capability_registry" in data
    assert "discovery_summary" in data
    assert "advisory" in data


def test_44c_capability_registry_includes_all_agents(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    agent_ids = [p["agent_id"] for p in data["capability_registry"]]
    assert "codex-local" in agent_ids
    assert "claude-local" in agent_ids
    assert "kimi-local" in agent_ids
    assert "deepseek-local" in agent_ids
    assert "gemini-local" in agent_ids
    assert "grok-local" in agent_ids
    assert "perplexity-local" in agent_ids


def test_44c_capability_registry_profile_fields_present(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        assert "agent_id" in profile
        assert "runtime" in profile
        assert "lifecycle_status" in profile
        assert "installed" in profile
        assert "version" in profile
        assert "capabilities" in profile
        assert "subagent_profile" in profile


def test_44c_capability_registry_capability_entry_fields(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        for cap in profile["capabilities"]:
            assert "name" in cap
            assert "confidence" in cap
            assert "evidence_sources" in cap
            assert "notes" in cap


def test_44c_capability_registry_subagent_profile_fields(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        sp = profile["subagent_profile"]
        assert "supported" in sp
        assert "confidence" in sp
        assert "mechanism" in sp
        assert "evidence_sources" in sp
        assert "notes" in sp


def test_44c_capability_registry_declared_future_agents_are_unknown(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    declared_ids = {"deepseek-local", "gemini-local", "grok-local", "perplexity-local"}
    for profile in data["capability_registry"]:
        if profile["agent_id"] in declared_ids:
            assert profile["installed"] is False
            for cap in profile["capabilities"]:
                assert cap["confidence"] == "unknown"
            assert profile["subagent_profile"]["supported"] is False
            assert profile["subagent_profile"]["confidence"] == "unknown"


def test_44c_capability_registry_valid_confidence_values(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    valid = {"unknown", "observed", "validated", "proven"}
    for profile in data["capability_registry"]:
        for cap in profile["capabilities"]:
            assert cap["confidence"] in valid
        assert profile["subagent_profile"]["confidence"] in valid


def test_44c_capability_registry_all_categories_present_per_agent(capsys) -> None:
    from pcae.core.agent import CAPABILITY_CATEGORIES
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        cap_names = {c["name"] for c in profile["capabilities"]}
        for cat in CAPABILITY_CATEGORIES:
            assert cat in cap_names, (
                f"Agent {profile['agent_id']} missing capability category {cat!r}"
            )


def test_44c_capability_registry_subagent_swarm_not_proven(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        for cap in profile["capabilities"]:
            if cap["name"] in ("subagent-coordination", "skill-execution", "swarm-coordination"):
                assert cap["confidence"] != "proven", (
                    f"Agent {profile['agent_id']} has {cap['name']} "
                    f"marked as 'proven' — should be at most 'observed' from CLI help."
                )


def test_44c_capability_registry_advisory_is_correct(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data["advisory"].lower()
    assert "evidence-based" in data["advisory"].lower()
    assert "refreshed" in data["advisory"].lower()


def test_44c_capability_registry_human_output_shows_agent_ids(capsys) -> None:
    main(["capability-registry"])
    output = capsys.readouterr().out
    assert "codex-local" in output
    assert "claude-local" in output
    assert "kimi-local" in output


def test_44c_capability_registry_human_output_shows_advisory(capsys) -> None:
    main(["capability-registry"])
    output = capsys.readouterr().out
    assert "advisory" in output.lower()


def test_44c_capability_discovery_command_exits_zero(capsys) -> None:
    exit_code = main(["capability-discovery"])
    assert exit_code == 0


def test_44c_capability_discovery_json_exits_zero(capsys) -> None:
    exit_code = main(["capability-discovery", "--json"])
    assert exit_code == 0


def test_44c_capability_discovery_json_has_required_top_level_keys(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "capability_registry" in data
    assert "discovery_summary" in data
    assert "advisory" in data


def test_44c_capability_discovery_includes_all_agents(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    agent_ids = [p["agent_id"] for p in data["capability_registry"]]
    assert "codex-local" in agent_ids
    assert "claude-local" in agent_ids
    assert "kimi-local" in agent_ids
    assert "deepseek-local" in agent_ids
    assert "gemini-local" in agent_ids
    assert "grok-local" in agent_ids
    assert "perplexity-local" in agent_ids


def test_44c_capability_discovery_no_proven_subagent_swarm(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        for cap in profile["capabilities"]:
            if cap["name"] in ("subagent-coordination", "skill-execution", "swarm-coordination"):
                assert cap["confidence"] != "proven", (
                    f"Agent {profile['agent_id']} has {cap['name']} "
                    f"marked as 'proven' — CLI help can produce at most 'observed'."
                )


def test_44c_capability_discovery_declared_future_agents_remain_unknown(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    declared_ids = {"deepseek-local", "gemini-local", "grok-local", "perplexity-local"}
    for profile in data["capability_registry"]:
        if profile["agent_id"] in declared_ids:
            assert profile["installed"] is False
            for cap in profile["capabilities"]:
                assert cap["confidence"] == "unknown"


def test_44c_capability_discovery_advisory_is_correct(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data["advisory"].lower()
    assert "no agents are executed" in data["advisory"].lower()


def test_44c_capability_discovery_human_output_shows_agent_ids(capsys) -> None:
    main(["capability-discovery"])
    output = capsys.readouterr().out
    assert "codex-local" in output
    assert "claude-local" in output
    assert "kimi-local" in output


def test_44c_capability_discovery_human_output_shows_advisory(capsys) -> None:
    main(["capability-discovery"])
    output = capsys.readouterr().out
    assert "advisory" in output.lower()


def test_44c_capability_registry_discovery_summary_fields(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    summary = data["discovery_summary"]
    assert "agents_checked" in summary
    assert "agents_installed" in summary
    assert "agents_not_installed" in summary
    assert "proven_capability_entries" in summary
    assert "unknown_capability_entries" in summary
    assert "subagent_capable_agents" in summary
    assert summary["agents_checked"] == 7
    assert summary["agents_not_installed"] == summary["agents_checked"] - summary["agents_installed"]


def test_44c_capability_discovery_subagent_capable_agents_populated_when_supported(
    capsys,
) -> None:
    # Any installed agent whose CLI help contains subagent-related keywords must
    # appear in subagent_capable_agents.  We verify the list is consistent with
    # the per-agent subagent_profile, not that a specific runtime is listed.
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    summary = data["discovery_summary"]
    expected = {
        p["agent_id"]
        for p in data["capability_registry"]
        if p["subagent_profile"]["supported"]
    }
    assert set(summary["subagent_capable_agents"]) == expected


def test_44c_capability_discovery_observed_subagent_uses_approved_evidence_sources(
    capsys,
) -> None:
    # Any capability marked as "observed" must cite only approved evidence sources.
    approved = {
        "runtime_discovery",
        "CLI help inspection",
        "governed_execution_history",
        "writable_execution_history",
        "manual_validation",
        "documentation_reference",
        "adapter_contract",
    }
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        for cap in profile["capabilities"]:
            if cap["name"] in ("subagent-coordination", "skill-execution", "swarm-coordination"):
                if cap["confidence"] == "observed":
                    for src in cap["evidence_sources"]:
                        assert src in approved, (
                            f"Agent {profile['agent_id']} cap {cap['name']} "
                            f"uses unapproved evidence source {src!r}"
                        )


def test_44c_capability_discovery_installed_subagent_support_is_observed_not_unknown(
    capsys,
) -> None:
    # Agents with subagent support detected from CLI help must be "observed", not "unknown".
    # This verifies the mechanism fires for any installed agent that matches keywords —
    # without hardcoding which agent must match.
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        if not profile["installed"]:
            continue
        if profile["subagent_profile"]["supported"]:
            subagent_cap = next(
                (c for c in profile["capabilities"] if c["name"] == "subagent-coordination"),
                None,
            )
            assert subagent_cap is not None
            assert subagent_cap["confidence"] == "observed", (
                f"{profile['agent_id']} subagent_profile.supported=True but "
                f"subagent-coordination confidence={subagent_cap['confidence']!r}"
            )


def test_44c_capability_discovery_subagent_evidence_includes_approved_source(
    capsys,
) -> None:
    # For any agent with observed subagent-coordination, at least one evidence source
    # must be an approved discovery source (CLI, runtime, or documentation).
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    approved = {"CLI help inspection", "runtime_discovery", "documentation_reference"}
    for profile in data["capability_registry"]:
        for cap in profile["capabilities"]:
            if cap["name"] == "subagent-coordination" and cap["confidence"] == "observed":
                assert any(src in approved for src in cap["evidence_sources"]), (
                    f"{profile['agent_id']} subagent-coordination is observed but "
                    f"evidence_sources {cap['evidence_sources']} contains no approved source"
                )


# ---------------------------------------------------------------------------
# Phase 44C.1: Documentation Capability Discovery
# ---------------------------------------------------------------------------


def test_44c1_codex_subagent_coordination_is_observed(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    codex = next(p for p in data["capability_registry"] if p["agent_id"] == "codex-local")
    cap = next(c for c in codex["capabilities"] if c["name"] == "subagent-coordination")
    assert cap["confidence"] == "observed"
    assert "documentation_reference" in cap["evidence_sources"]


def test_44c1_codex_skill_execution_is_observed(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    codex = next(p for p in data["capability_registry"] if p["agent_id"] == "codex-local")
    cap = next(c for c in codex["capabilities"] if c["name"] == "skill-execution")
    assert cap["confidence"] == "observed"
    assert "documentation_reference" in cap["evidence_sources"]


def test_44c1_claude_custom_agent_support_is_observed(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    claude = next(p for p in data["capability_registry"] if p["agent_id"] == "claude-local")
    cap = next(c for c in claude["capabilities"] if c["name"] == "custom-agent-support")
    assert cap["confidence"] == "observed"
    assert "documentation_reference" in cap["evidence_sources"]


def test_44c1_kimi_swarm_coordination_is_observed(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    kimi = next(p for p in data["capability_registry"] if p["agent_id"] == "kimi-local")
    cap = next(c for c in kimi["capabilities"] if c["name"] == "swarm-coordination")
    assert cap["confidence"] == "observed"
    assert "documentation_reference" in cap["evidence_sources"]


def test_44c1_multiple_evidence_sources_supported(capsys) -> None:
    # Claude's subagent-coordination should have both documentation_reference
    # and CLI help inspection (and possibly runtime_discovery).
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    claude = next(p for p in data["capability_registry"] if p["agent_id"] == "claude-local")
    cap = next(c for c in claude["capabilities"] if c["name"] == "subagent-coordination")
    assert cap["confidence"] == "observed"
    assert len(cap["evidence_sources"]) >= 2
    assert "documentation_reference" in cap["evidence_sources"]


def test_44c1_doc_reference_never_produces_proven(capsys) -> None:
    # No capability whose sole evidence is documentation_reference may be proven.
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        for cap in profile["capabilities"]:
            if (
                cap["evidence_sources"] == ["documentation_reference"]
                or cap["evidence_sources"] == ("documentation_reference",)
            ):
                assert cap["confidence"] != "proven", (
                    f"{profile['agent_id']}.{cap['name']} is proven from "
                    f"documentation_reference alone — not allowed"
                )
                assert cap["confidence"] != "validated", (
                    f"{profile['agent_id']}.{cap['name']} is validated from "
                    f"documentation_reference alone — not allowed"
                )


def test_44c1_doc_reference_max_confidence_is_observed(capsys) -> None:
    # Any capability with documentation_reference as an evidence source must
    # be at most observed (documentation cannot validate or prove).
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        for cap in profile["capabilities"]:
            if "documentation_reference" in cap["evidence_sources"]:
                assert cap["confidence"] in ("observed", "unknown"), (
                    f"{profile['agent_id']}.{cap['name']} has documentation_reference "
                    f"but confidence={cap['confidence']!r} — must be at most 'observed'"
                )


def test_44c1_future_agents_remain_unknown_no_doc_entries(capsys) -> None:
    # Declared agents without doc catalog entries must stay unknown for
    # the advanced capabilities.
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    future_ids = {"deepseek-local", "gemini-local", "grok-local", "perplexity-local"}
    for profile in data["capability_registry"]:
        if profile["agent_id"] not in future_ids:
            continue
        for cap in profile["capabilities"]:
            assert "documentation_reference" not in cap["evidence_sources"], (
                f"{profile['agent_id']}.{cap['name']} has documentation_reference "
                f"but no doc catalog entry exists for this agent"
            )


def test_44c1_custom_agent_support_in_all_profiles(capsys) -> None:
    # custom-agent-support must appear in every agent profile (unknown for those
    # without a doc catalog entry, observed for claude).
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        cap_names = {c["name"] for c in profile["capabilities"]}
        assert "custom-agent-support" in cap_names, (
            f"{profile['agent_id']} missing custom-agent-support capability"
        )


def test_44c1_doc_capabilities_from_catalog_not_hardcoded_cli(capsys) -> None:
    # Discovery uses the catalog lookup; an agent not in the catalog gets no
    # documentation_reference evidence — even if installed.
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    no_doc_ids = {"deepseek-local", "gemini-local", "grok-local", "perplexity-local"}
    for profile in data["capability_registry"]:
        if profile["agent_id"] not in no_doc_ids:
            continue
        for cap in profile["capabilities"]:
            assert "documentation_reference" not in cap["evidence_sources"]


# Phase 44D: Capability Validation Framework


def test_44d_capability_validation_json_has_required_top_level_keys(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "validation_framework" in data
    assert "promotion_rules" in data
    assert "validation_candidates" in data
    assert "advisory" in data


def test_44d_capability_validation_lifecycle_has_four_levels(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    lifecycle = data["validation_framework"]["lifecycle"]
    assert lifecycle == ["unknown", "observed", "validated", "proven"]


def test_44d_capability_validation_all_seven_sources_declared(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    sources = data["validation_framework"]["validation_sources"]
    for expected in (
        "documentation_reference",
        "cli_discovery",
        "manual_validation",
        "runtime_validation",
        "governed_execution_history",
        "writable_execution_history",
        "adapter_contract",
    ):
        assert expected in sources, f"Missing validation source: {expected}"


def test_44d_capability_validation_rule_unknown_to_observed(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    rule = next((r for r in data["promotion_rules"] if r["rule_id"] == "unknown_to_observed"), None)
    assert rule is not None
    assert rule["from_confidence"] == "unknown"
    assert rule["to_confidence"] == "observed"
    assert rule["required_validation"] == "evidence_collection"
    assert "documentation_reference" in rule["validation_sources"]
    assert "cli_discovery" in rule["validation_sources"]


def test_44d_capability_validation_rule_observed_to_validated(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    rule = next((r for r in data["promotion_rules"] if r["rule_id"] == "observed_to_validated"), None)
    assert rule is not None
    assert rule["from_confidence"] == "observed"
    assert rule["to_confidence"] == "validated"
    assert rule["required_validation"] == "successful_controlled_experiment"
    assert "runtime_validation" in rule["validation_sources"]


def test_44d_capability_validation_rule_validated_to_proven(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    rule = next((r for r in data["promotion_rules"] if r["rule_id"] == "validated_to_proven"), None)
    assert rule is not None
    assert rule["from_confidence"] == "validated"
    assert rule["to_confidence"] == "proven"
    assert rule["required_validation"] == "successful_governed_production_usage"
    assert "governed_execution_history" in rule["validation_sources"]


def test_44d_capability_validation_rule_proven_no_downgrade(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    rule = next((r for r in data["promotion_rules"] if r["rule_id"] == "proven_no_downgrade"), None)
    assert rule is not None
    assert rule["from_confidence"] == "proven"
    assert rule["to_confidence"] == "proven"
    assert rule["required_validation"] == "not_applicable"
    assert "downgrade" in rule["description"].lower()


def test_44d_capability_validation_four_promotion_rules_defined(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert len(data["promotion_rules"]) == 4


def test_44d_capability_validation_candidates_has_all_agents(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    agent_ids = {a["agent_id"] for a in data["validation_candidates"]}
    for expected in ("codex-local", "claude-local", "kimi-local"):
        assert expected in agent_ids


def test_44d_capability_validation_candidate_agent_fields(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    for agent in data["validation_candidates"]:
        assert "agent_id" in agent
        assert "installed" in agent
        assert "observed_capabilities" in agent
        assert "validated_capabilities" in agent
        assert "proven_capabilities" in agent
        assert "next_validation_candidates" in agent
        assert "recommended_validation_method" in agent


def test_44d_capability_validation_next_candidate_fields(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    for agent in data["validation_candidates"]:
        for c in agent["next_validation_candidates"]:
            assert "capability" in c
            assert "current_confidence" in c
            assert "promotion_path" in c
            assert "recommended_validation_method" in c
            assert "required_validation" in c


def test_44d_capability_validation_codex_subagent_observed_to_validated(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    codex = next(a for a in data["validation_candidates"] if a["agent_id"] == "codex-local")
    assert "subagent-coordination" in codex["observed_capabilities"]
    match = next(
        (c for c in codex["next_validation_candidates"]
         if c["capability"] == "subagent-coordination"),
        None,
    )
    assert match is not None, "subagent-coordination not in codex-local next_validation_candidates"
    assert match["current_confidence"] == "observed"
    assert match["promotion_path"] == "observed → validated"
    assert match["recommended_validation_method"] == "runtime_validation"


def test_44d_capability_validation_claude_subagent_observed_to_validated(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    claude = next(a for a in data["validation_candidates"] if a["agent_id"] == "claude-local")
    assert "subagent-coordination" in claude["observed_capabilities"]
    match = next(
        (c for c in claude["next_validation_candidates"]
         if c["capability"] == "subagent-coordination"),
        None,
    )
    assert match is not None
    assert match["current_confidence"] == "observed"
    assert match["promotion_path"] == "observed → validated"


def test_44d_capability_validation_kimi_swarm_observed_to_validated(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    kimi = next(a for a in data["validation_candidates"] if a["agent_id"] == "kimi-local")
    assert "swarm-coordination" in kimi["observed_capabilities"]
    match = next(
        (c for c in kimi["next_validation_candidates"]
         if c["capability"] == "swarm-coordination"),
        None,
    )
    assert match is not None
    assert match["current_confidence"] == "observed"
    assert match["promotion_path"] == "observed → validated"


def test_44d_capability_validation_advisory_text(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    advisory = data["advisory"].lower()
    assert "advisory" in advisory
    assert "no runtime validation is executed" in advisory


def test_44d_capability_validation_human_output_shows_framework(capsys) -> None:
    main(["capability-validation"])
    output = capsys.readouterr().out
    assert "capability validation framework" in output.lower()
    assert "confidence lifecycle" in output.lower()
    assert "promotion rules" in output.lower()


def test_44d_capability_validation_human_output_shows_all_lifecycle_levels(capsys) -> None:
    main(["capability-validation"])
    output = capsys.readouterr().out
    for level in ("unknown", "observed", "validated", "proven"):
        assert level in output


def test_44d_capability_validation_human_output_shows_per_agent_candidates(capsys) -> None:
    main(["capability-validation"])
    output = capsys.readouterr().out
    assert "codex-local" in output
    assert "claude-local" in output
    assert "kimi-local" in output
    assert "subagent-coordination" in output
    assert "swarm-coordination" in output
    assert "observed → validated" in output


def test_44d_capability_validation_lifecycle_descriptions_present(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    descs = data["validation_framework"]["lifecycle_descriptions"]
    for level in ("unknown", "observed", "validated", "proven"):
        assert level in descs


def test_44d_capability_validation_proven_description_mentions_no_downgrade(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    proven_desc = data["validation_framework"]["lifecycle_descriptions"]["proven"].lower()
    assert "downgrade" in proven_desc or "cannot" in proven_desc


def test_44d_capability_validation_installed_agents_have_nonempty_next_candidates(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    installed = [a for a in data["validation_candidates"] if a["installed"]]
    assert len(installed) > 0
    for agent in installed:
        assert len(agent["next_validation_candidates"]) > 0, (
            f"{agent['agent_id']} is installed but has no next_validation_candidates"
        )


def test_44d_capability_validation_no_execution_performed(capsys) -> None:
    # Verifies the command is strictly read-only: advisory says so.
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "executed" in data["advisory"].lower()


# Phase 44D.1: Capability Classification Normalization


def test_44d1_discovery_summary_has_normalized_group_keys(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    summary = data["discovery_summary"]
    assert "subagent_capable_agents" in summary
    assert "swarm_capable_agents" in summary
    assert "multi_agent_capable_agents" in summary
    assert "extensibility_capable_agents" in summary


def test_44d1_registry_summary_has_normalized_group_keys(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    summary = data["discovery_summary"]
    assert "subagent_capable_agents" in summary
    assert "swarm_capable_agents" in summary
    assert "multi_agent_capable_agents" in summary
    assert "extensibility_capable_agents" in summary


def test_44d1_kimi_swarm_rolls_up_into_multi_agent(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    summary = data["discovery_summary"]
    assert "kimi-local" in summary["swarm_capable_agents"]
    assert "kimi-local" in summary["multi_agent_capable_agents"]


def test_44d1_codex_subagent_rolls_up_into_multi_agent(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    summary = data["discovery_summary"]
    assert "codex-local" in summary["subagent_capable_agents"]
    assert "codex-local" in summary["multi_agent_capable_agents"]


def test_44d1_claude_subagent_rolls_up_into_multi_agent(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    summary = data["discovery_summary"]
    assert "claude-local" in summary["subagent_capable_agents"]
    assert "claude-local" in summary["multi_agent_capable_agents"]


def test_44d1_multi_agent_includes_all_three_installed_runtimes(capsys) -> None:
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    multi = set(data["discovery_summary"]["multi_agent_capable_agents"])
    for agent in ("codex-local", "claude-local", "kimi-local"):
        assert agent in multi, f"{agent} missing from multi_agent_capable_agents"


def test_44d1_original_capability_records_preserved_in_discovery(capsys) -> None:
    # Normalization is summary-level only — individual capability entries must survive unchanged.
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    kimi = next(p for p in data["capability_registry"] if p["agent_id"] == "kimi-local")
    cap_names = {c["name"] for c in kimi["capabilities"]}
    assert "swarm-coordination" in cap_names
    swarm_cap = next(c for c in kimi["capabilities"] if c["name"] == "swarm-coordination")
    assert swarm_cap["confidence"] == "observed"


def test_44d1_normalization_does_not_promote_confidence(capsys) -> None:
    # Grouped agents must not have their individual confidence levels altered.
    main(["capability-discovery", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        for cap in profile["capabilities"]:
            if cap["name"] in ("subagent-coordination", "swarm-coordination",
                               "custom-agent-support", "skill-execution"):
                assert cap["confidence"] in ("unknown", "observed", "validated", "proven"), (
                    f"{profile['agent_id']}.{cap['name']} has unexpected confidence "
                    f"{cap['confidence']!r}"
                )


def test_44d1_validation_normalized_summary_present(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "normalized_summary" in data
    ns = data["normalized_summary"]
    assert "multi_agent_capable_agents" in ns
    assert "extensibility_capable_agents" in ns
    assert "swarm_capable_agents" in ns
    assert "subagent_capable_agents" in ns


def test_44d1_validation_kimi_in_multi_agent_via_swarm(capsys) -> None:
    # Validation uses doc-catalog evidence (no CLI probing):
    # kimi's swarm-coordination is observed → kimi is multi_agent_capable.
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    ns = data["normalized_summary"]
    assert "kimi-local" in ns["swarm_capable_agents"]
    assert "kimi-local" in ns["multi_agent_capable_agents"]


def test_44d1_validation_normalization_rules_exposed(capsys) -> None:
    main(["capability-validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    rules = data["normalized_summary"].get("normalization_rules", {})
    assert rules.get("subagent-coordination") == "multi_agent_capable"
    assert rules.get("swarm-coordination") == "multi_agent_capable"
    assert rules.get("custom-agent-support") == "multi_agent_capable"
    assert rules.get("skill-execution") == "extensibility_capable"


def test_44d1_human_output_shows_normalized_groups_in_registry(capsys) -> None:
    main(["capability-registry"])
    output = capsys.readouterr().out
    assert "multi-agent capable" in output.lower() or "multi_agent" in output.lower()
    assert "swarm" in output.lower()


def test_44d1_human_output_shows_normalized_groups_in_validation(capsys) -> None:
    main(["capability-validation"])
    output = capsys.readouterr().out
    assert "normalized" in output.lower()
    assert "multi_agent" in output.lower() or "multi-agent" in output.lower()


# Phase 44D.2: Registry / Summary Consistency Validation


def test_44d2_registry_kimi_swarm_is_observed_with_doc_evidence(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    kimi = next(p for p in data["capability_registry"] if p["agent_id"] == "kimi-local")
    swarm = next(c for c in kimi["capabilities"] if c["name"] == "swarm-coordination")
    assert swarm["confidence"] == "observed", (
        f"kimi-local swarm-coordination confidence={swarm['confidence']!r}, expected 'observed'"
    )
    assert "documentation_reference" in swarm["evidence_sources"], (
        f"kimi-local swarm-coordination missing documentation_reference evidence"
    )
    assert len(swarm["evidence_sources"]) > 0


def test_44d2_registry_summary_includes_kimi_in_swarm_capable(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "kimi-local" in data["discovery_summary"]["swarm_capable_agents"]


def test_44d2_registry_summary_includes_all_three_in_multi_agent(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    multi = set(data["discovery_summary"]["multi_agent_capable_agents"])
    for agent in ("codex-local", "claude-local", "kimi-local"):
        assert agent in multi, f"{agent} missing from registry multi_agent_capable_agents"


def test_44d2_registry_swarm_capable_derived_from_registry_evidence(capsys) -> None:
    # Each agent in swarm_capable_agents must have swarm-coordination at observed+.
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    registry_by_id = {p["agent_id"]: p for p in data["capability_registry"]}
    for agent_id in data["discovery_summary"]["swarm_capable_agents"]:
        profile = registry_by_id[agent_id]
        swarm = next(
            (c for c in profile["capabilities"] if c["name"] == "swarm-coordination"), None
        )
        assert swarm is not None, f"{agent_id} in swarm_capable but has no swarm-coordination cap"
        assert swarm["confidence"] in ("observed", "validated", "proven"), (
            f"{agent_id} in swarm_capable but swarm-coordination confidence={swarm['confidence']!r}"
        )
        assert len(swarm["evidence_sources"]) > 0, (
            f"{agent_id} swarm-coordination has empty evidence_sources"
        )


def test_44d2_registry_multi_agent_capable_derivable_from_registry(capsys) -> None:
    # Each agent in multi_agent_capable_agents must have at least one qualifying cap at observed+.
    _qualifying = {"subagent-coordination", "swarm-coordination", "custom-agent-support"}
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    registry_by_id = {p["agent_id"]: p for p in data["capability_registry"]}
    for agent_id in data["discovery_summary"]["multi_agent_capable_agents"]:
        profile = registry_by_id[agent_id]
        found = any(
            c["name"] in _qualifying and c["confidence"] in ("observed", "validated", "proven")
            for c in profile["capabilities"]
        )
        assert found, (
            f"{agent_id} in multi_agent_capable_agents but no qualifying capability at observed+"
        )


def test_44d2_registry_extensibility_capable_derivable_from_registry(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    registry_by_id = {p["agent_id"]: p for p in data["capability_registry"]}
    for agent_id in data["discovery_summary"]["extensibility_capable_agents"]:
        profile = registry_by_id[agent_id]
        skill = next(
            (c for c in profile["capabilities"] if c["name"] == "skill-execution"), None
        )
        assert skill is not None
        assert skill["confidence"] in ("observed", "validated", "proven"), (
            f"{agent_id} in extensibility_capable but skill-execution={skill['confidence']!r}"
        )
        assert len(skill["evidence_sources"]) > 0


def test_44d2_registry_doc_evidence_never_exceeds_observed(capsys) -> None:
    # Documentation reference evidence alone must not produce validated or proven confidence.
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    for profile in data["capability_registry"]:
        for cap in profile["capabilities"]:
            if cap["evidence_sources"] == ["documentation_reference"]:
                assert cap["confidence"] in ("unknown", "observed"), (
                    f"{profile['agent_id']}.{cap['name']} has only documentation_reference "
                    f"but confidence={cap['confidence']!r} — must be at most 'observed'"
                )


def test_44d2_discovery_and_registry_swarm_agree(capsys) -> None:
    # kimi must appear in swarm_capable_agents in both commands.
    main(["capability-registry", "--json"])
    reg = json.loads(capsys.readouterr().out)
    main(["capability-discovery", "--json"])
    disc = json.loads(capsys.readouterr().out)
    assert "kimi-local" in reg["discovery_summary"]["swarm_capable_agents"]
    assert "kimi-local" in disc["discovery_summary"]["swarm_capable_agents"]


def test_44d2_discovery_and_registry_multi_agent_agree(capsys) -> None:
    main(["capability-registry", "--json"])
    reg = json.loads(capsys.readouterr().out)
    main(["capability-discovery", "--json"])
    disc = json.loads(capsys.readouterr().out)
    reg_multi = set(reg["discovery_summary"]["multi_agent_capable_agents"])
    disc_multi = set(disc["discovery_summary"]["multi_agent_capable_agents"])
    for agent in ("codex-local", "claude-local", "kimi-local"):
        assert agent in reg_multi, f"{agent} not in registry multi_agent_capable_agents"
        assert agent in disc_multi, f"{agent} not in discovery multi_agent_capable_agents"


def test_44d2_original_capability_names_preserved_in_registry(capsys) -> None:
    main(["capability-registry", "--json"])
    data = json.loads(capsys.readouterr().out)
    kimi = next(p for p in data["capability_registry"] if p["agent_id"] == "kimi-local")
    cap_names = {c["name"] for c in kimi["capabilities"]}
    assert "swarm-coordination" in cap_names
    # Normalization is summary-level only — the original name must survive in the registry.
    assert "multi_agent_capable" not in cap_names


# ---------------------------------------------------------------------------
# Phase 44E — Coordinator Agent Design
# ---------------------------------------------------------------------------


def test_44e_coordinator_design_command_exits_zero(capsys) -> None:
    exit_code = main(["coordinator-design"])
    assert exit_code == 0


def test_44e_coordinator_design_json_exits_zero(capsys) -> None:
    exit_code = main(["coordinator-design", "--json"])
    assert exit_code == 0


def test_44e_coordinator_design_json_has_required_top_level_keys(capsys) -> None:
    main(["coordinator-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "coordinator_design" in data
    assert "task_classification" in data
    assert "selection_model" in data
    assert "orchestration_strategies" in data
    assert "governance_integration" in data
    assert "advisory" in data


def test_44e_coordinator_design_has_eight_responsibilities(capsys) -> None:
    main(["coordinator-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    responsibilities = data["coordinator_design"]["responsibilities"]
    assert len(responsibilities) == 8
    names = [r["name"] for r in responsibilities]
    assert "task_intake" in names
    assert "task_classification" in names
    assert "capability_lookup" in names
    assert "agent_selection" in names
    assert "orchestration_strategy_selection" in names
    assert "result_aggregation" in names
    assert "conflict_escalation" in names
    assert "governance_handoff" in names


def test_44e_coordinator_design_task_classification_has_twelve_classes(capsys) -> None:
    main(["coordinator-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    classes = data["task_classification"]["supported_task_classes"]
    assert len(classes) == 12
    for expected in (
        "planning", "implementation", "review", "validation", "research",
        "testing", "architecture", "documentation", "security", "performance",
        "dependency-analysis", "roadmap-generation",
    ):
        assert expected in classes


def test_44e_coordinator_design_selection_model_prohibits_hardcoding(capsys) -> None:
    main(["coordinator-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    model = data["selection_model"]
    prohibited = model["prohibited_hardcoding"]
    assert any("codex" in p and "implementer" in p for p in prohibited)
    assert any("claude" in p and "reviewer" in p for p in prohibited)
    assert any("kimi" in p and "planner" in p for p in prohibited)


def test_44e_coordinator_design_selection_criteria_defined(capsys) -> None:
    main(["coordinator-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    criteria = [c["criterion"] for c in data["selection_model"]["selection_criteria"]]
    assert "capability_present" in criteria
    assert "confidence_threshold" in criteria
    assert "agent_installed" in criteria
    assert "agent_available" in criteria


def test_44e_coordinator_design_selection_output_fields_defined(capsys) -> None:
    main(["coordinator-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["selection_model"]["selection_output_fields"]
    assert "task_id" in fields
    assert "selected_agents" in fields
    assert "selection_reason" in fields
    assert "capability_used" in fields
    assert "confidence_level" in fields


def test_44e_coordinator_design_has_six_orchestration_strategies(capsys) -> None:
    main(["coordinator-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    strategies = data["orchestration_strategies"]
    assert len(strategies) == 6
    names = [s["strategy"] for s in strategies]
    assert "single_agent" in names
    assert "sequential" in names
    assert "parallel_review" in names
    assert "parallel_planning" in names
    assert "swarm" in names
    assert "consensus" in names


def test_44e_coordinator_design_governance_boundaries_defined(capsys) -> None:
    main(["coordinator-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_integration"]
    assert "coordinator_may" in gov
    assert "coordinator_may_not" in gov
    may = gov["coordinator_may"]
    may_not = gov["coordinator_may_not"]
    assert any("assign work" in item for item in may)
    assert any("aggregate results" in item for item in may)
    for prohibited in ("commit", "push", "rollback"):
        assert any(prohibited in item for item in may_not)
    assert any("bypass governance" in item for item in may_not)


def test_44e_coordinator_design_future_expansion_includes_all_agents(capsys) -> None:
    main(["coordinator-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    agents = data["future_agent_expansion"]
    for expected in (
        "codex-local", "claude-local", "kimi-local",
        "deepseek-local", "gemini-local", "grok-local", "perplexity-local",
    ):
        assert expected in agents


def test_44e_coordinator_design_advisory_is_correct(capsys) -> None:
    main(["coordinator-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data
    assert "no orchestration" in data["advisory"].lower()


def test_44e_coordinator_design_human_output_shows_responsibilities(capsys) -> None:
    main(["coordinator-design"])
    output = capsys.readouterr().out
    assert "task_intake" in output
    assert "capability_lookup" in output
    assert "agent_selection" in output
    assert "governance_handoff" in output


def test_44e_coordinator_design_human_output_shows_advisory(capsys) -> None:
    main(["coordinator-design"])
    output = capsys.readouterr().out
    assert "Coordinator design is advisory" in output
    assert "no orchestration is performed" in output


# ---------------------------------------------------------------------------
# Phase 44F — Consensus Engine Design
# ---------------------------------------------------------------------------


def test_44f_consensus_design_command_exits_zero(capsys) -> None:
    exit_code = main(["consensus-design"])
    assert exit_code == 0


def test_44f_consensus_design_json_exits_zero(capsys) -> None:
    exit_code = main(["consensus-design", "--json"])
    assert exit_code == 0


def test_44f_consensus_design_json_has_required_top_level_keys(capsys) -> None:
    main(["consensus-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "consensus_design" in data
    assert "decision_types" in data
    assert "consensus_policies" in data
    assert "weighting_model" in data
    assert "conflict_handling" in data
    assert "governance_boundaries" in data
    assert "advisory" in data


def test_44f_consensus_design_input_fields_defined(capsys) -> None:
    main(["consensus-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["consensus_design"]["input_fields"]
    for expected in (
        "agent_id", "assigned_role", "task_id", "recommendation",
        "confidence", "rationale", "evidence_artifacts", "execution_result_refs",
    ):
        assert expected in fields


def test_44f_consensus_design_has_five_decision_types(capsys) -> None:
    main(["consensus-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    decisions = [d["decision"] for d in data["decision_types"]]
    assert len(decisions) == 5
    for expected in ("approve", "reject", "request_changes", "inconclusive", "escalate_to_human"):
        assert expected in decisions


def test_44f_consensus_design_has_six_policies(capsys) -> None:
    main(["consensus-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    policies = [p["policy"] for p in data["consensus_policies"]]
    assert len(policies) == 6
    for expected in ("unanimous", "majority", "weighted", "confidence_weighted", "role_priority", "human_escalation"):
        assert expected in policies


def test_44f_consensus_design_default_policy_is_human_escalation(capsys) -> None:
    main(["consensus-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["consensus_design"]["default_policy"] == "human_escalation"
    default_policies = [p for p in data["consensus_policies"] if p["is_default"]]
    assert len(default_policies) == 1
    assert default_policies[0]["policy"] == "human_escalation"


def test_44f_consensus_design_weighting_model_has_five_sources(capsys) -> None:
    main(["consensus-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    sources = [s["source"] for s in data["weighting_model"]["weight_sources"]]
    assert len(sources) == 5
    for expected in (
        "capability_confidence", "runtime_availability",
        "successful_execution_history", "role_fit", "task_class_fit",
    ):
        assert expected in sources


def test_44f_consensus_design_conflict_handling_preserves_recommendations(capsys) -> None:
    main(["consensus-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    steps = data["conflict_handling"]["steps"]
    assert any("preserve all agent recommendations" in s for s in steps)
    assert any("preserve all agent rationales" in s for s in steps)
    assert any("conflict summary" in s for s in steps)
    assert any("escalate to human" in s for s in steps)


def test_44f_consensus_design_governance_boundaries_defined(capsys) -> None:
    main(["consensus-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_boundaries"]
    may = gov["engine_may"]
    may_not = gov["engine_may_not"]
    assert any("aggregate" in item for item in may)
    assert any("advisory" in item for item in may)
    for prohibited in ("commit", "push", "rollback"):
        assert any(prohibited in item for item in may_not)
    assert any("bypass governance" in item for item in may_not)


def test_44f_consensus_design_future_expansions_defined(capsys) -> None:
    main(["consensus-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    expansions = data["future_expansions"]
    assert len(expansions) >= 5
    assert any("quorum" in e for e in expansions)
    assert any("veto" in e for e in expansions)


def test_44f_consensus_design_advisory_is_correct(capsys) -> None:
    main(["consensus-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "no consensus execution" in data["advisory"].lower()


def test_44f_consensus_design_human_output_shows_decision_types(capsys) -> None:
    main(["consensus-design"])
    output = capsys.readouterr().out
    for dt in ("approve", "reject", "request_changes", "inconclusive", "escalate_to_human"):
        assert dt in output


def test_44f_consensus_design_human_output_shows_advisory(capsys) -> None:
    main(["consensus-design"])
    output = capsys.readouterr().out
    assert "Consensus design is advisory" in output
    assert "no consensus execution is performed" in output


# ---------------------------------------------------------------------------
# Phase 44G — Parallel Agent Execution Design
# ---------------------------------------------------------------------------


def test_44g_parallel_execution_design_command_exits_zero(capsys) -> None:
    exit_code = main(["parallel-execution-design"])
    assert exit_code == 0


def test_44g_parallel_execution_design_json_exits_zero(capsys) -> None:
    exit_code = main(["parallel-execution-design", "--json"])
    assert exit_code == 0


def test_44g_parallel_execution_design_json_has_required_top_level_keys(capsys) -> None:
    main(["parallel-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "parallel_execution_design" in data
    assert "execution_topologies" in data
    assert "child_task_model" in data
    assert "safety_rules" in data
    assert "failure_model" in data
    assert "result_aggregation" in data
    assert "governance_integration" in data
    assert "advisory" in data


def test_44g_parallel_execution_design_has_seven_topologies(capsys) -> None:
    main(["parallel-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    topologies = [t["topology"] for t in data["execution_topologies"]]
    assert len(topologies) == 7
    for expected in (
        "fan_out", "fan_in", "map_reduce",
        "parallel_review", "parallel_planning", "parallel_validation", "swarm",
    ):
        assert expected in topologies


def test_44g_parallel_execution_design_all_topologies_are_parallel(capsys) -> None:
    main(["parallel-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    for topo in data["execution_topologies"]:
        assert topo["parallel"] is True


def test_44g_parallel_execution_design_child_task_fields_defined(capsys) -> None:
    main(["parallel-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["child_task_model"]["fields"]
    for expected in (
        "child_task_id", "parent_task_id", "assigned_agent", "assigned_role",
        "capability_required", "execution_mode", "writable_allowed",
        "timeout_seconds", "status", "result_ref", "failure_reason",
    ):
        assert expected in fields


def test_44g_parallel_execution_design_safety_rules_defined(capsys) -> None:
    main(["parallel-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    rules = data["safety_rules"]
    assert any("read-only" in r for r in rules)
    assert any("commit" in r for r in rules)
    assert any("push" in r for r in rules)
    assert any("rollback" in r for r in rules)
    assert any("bypass" in r for r in rules)


def test_44g_parallel_execution_design_failure_model_has_seven_statuses(capsys) -> None:
    main(["parallel-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    statuses = data["failure_model"]["statuses"]
    assert len(statuses) == 7
    for expected in ("pending", "running", "completed", "failed", "timed_out", "cancelled", "blocked"):
        assert expected in statuses


def test_44g_parallel_execution_design_failure_handling_preserves_partial(capsys) -> None:
    main(["parallel-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    handling = data["failure_model"]["failure_handling"]
    assert any("partial" in h for h in handling)
    assert any("human escalation" in h for h in handling)
    assert any("timeout" in h for h in handling)


def test_44g_parallel_execution_design_result_aggregation_fields_defined(capsys) -> None:
    main(["parallel-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["result_aggregation"]["aggregate_fields"]
    for expected in ("recommendations", "confidence", "conflicts", "evidence_artifacts"):
        assert expected in fields


def test_44g_parallel_execution_design_governance_integration_defined(capsys) -> None:
    main(["parallel-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    feeds_into = data["governance_integration"]["feeds_into"]
    assert any("consensus" in f for f in feeds_into)
    assert any("approval" in f for f in feeds_into)
    assert any("commit" in f for f in feeds_into)
    assert any("push" in f for f in feeds_into)


def test_44g_parallel_execution_design_advisory_is_correct(capsys) -> None:
    main(["parallel-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "no parallel execution" in data["advisory"].lower()


def test_44g_parallel_execution_design_human_output_shows_topologies(capsys) -> None:
    main(["parallel-execution-design"])
    output = capsys.readouterr().out
    for topo in ("fan_out", "fan_in", "map_reduce", "swarm"):
        assert topo in output


def test_44g_parallel_execution_design_human_output_shows_advisory(capsys) -> None:
    main(["parallel-execution-design"])
    output = capsys.readouterr().out
    assert "Parallel execution design is advisory" in output
    assert "no parallel execution is performed" in output


# ---------------------------------------------------------------------------
# Phase 44H — Multi-Agent Planning Prototype Design
# ---------------------------------------------------------------------------


def test_44h_planning_prototype_design_command_exits_zero(capsys) -> None:
    exit_code = main(["planning-prototype-design"])
    assert exit_code == 0


def test_44h_planning_prototype_design_json_exits_zero(capsys) -> None:
    exit_code = main(["planning-prototype-design", "--json"])
    assert exit_code == 0


def test_44h_planning_prototype_design_json_has_required_top_level_keys(capsys) -> None:
    main(["planning-prototype-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "planning_prototype_design" in data
    assert "planning_objective_model" in data
    assert "planner_selection" in data
    assert "parallel_planning_flow" in data
    assert "planning_artifact_model" in data
    assert "governance_rules" in data
    assert "conflict_handling" in data
    assert "advisory" in data


def test_44h_planning_prototype_design_objective_model_fields_defined(capsys) -> None:
    main(["planning-prototype-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["planning_objective_model"]["fields"]
    for expected in (
        "objective_id", "objective_text", "planning_scope", "constraints",
        "required_capabilities", "output_format", "human_approval_required",
    ):
        assert expected in fields


def test_44h_planning_prototype_design_planner_selection_capabilities_defined(capsys) -> None:
    main(["planning-prototype-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    caps = data["planner_selection"]["required_capabilities"]
    for expected in ("planning", "architecture", "roadmap-generation", "documentation", "review"):
        assert expected in caps


def test_44h_planning_prototype_design_selection_is_capability_based_and_neutral(capsys) -> None:
    main(["planning-prototype-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    rules = data["planner_selection"]["selection_rules"]
    assert any("capability-based" in r for r in rules)
    assert any("runtime-neutral" in r for r in rules)
    assert any("human-overridable" in r for r in rules)


def test_44h_planning_prototype_design_parallel_flow_has_seven_steps(capsys) -> None:
    main(["planning-prototype-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    flow = data["parallel_planning_flow"]
    assert len(flow) == 7
    assert any("coordinator receives objective" in s for s in flow)
    assert any("planners produce independent plans" in s for s in flow)
    assert any("consensus engine" in s for s in flow)
    assert any("human reviews" in s for s in flow)


def test_44h_planning_prototype_design_artifact_model_fields_defined(capsys) -> None:
    main(["planning-prototype-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["planning_artifact_model"]["fields"]
    for expected in (
        "plan_id", "objective_id", "planner_agents", "proposed_phases",
        "dependencies", "risks", "assumptions", "conflicts",
        "consensus_summary", "human_decision_required",
    ):
        assert expected in fields


def test_44h_planning_prototype_design_governance_rules_defined(capsys) -> None:
    main(["planning-prototype-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    rules = data["governance_rules"]
    assert any("read-only" in r for r in rules)
    assert any("cannot modify files" in r for r in rules)
    assert any("cannot commit" in r for r in rules)
    assert any("cannot push" in r for r in rules)
    assert any("advisory" in r for r in rules)
    assert any("human approves" in r for r in rules)


def test_44h_planning_prototype_design_conflict_handling_preserves_all_plans(capsys) -> None:
    main(["planning-prototype-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    handling = data["conflict_handling"]
    assert any("preserve all proposed plans" in h for h in handling)
    assert any("human decision" in h for h in handling)
    assert any("auto-select" in h for h in handling)


def test_44h_planning_prototype_design_future_path_defined(capsys) -> None:
    main(["planning-prototype-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["planning_prototype_design"]["future_path"]]
    assert "44I" in phases
    assert "44J" in phases
    assert "45A" in phases


def test_44h_planning_prototype_design_advisory_is_correct(capsys) -> None:
    main(["planning-prototype-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "no planning agents are executed" in data["advisory"].lower()


def test_44h_planning_prototype_design_human_output_shows_flow(capsys) -> None:
    main(["planning-prototype-design"])
    output = capsys.readouterr().out
    assert "coordinator receives objective" in output
    assert "consensus engine" in output
    assert "human reviews" in output


def test_44h_planning_prototype_design_human_output_shows_advisory(capsys) -> None:
    main(["planning-prototype-design"])
    output = capsys.readouterr().out
    assert "Planning prototype design is advisory" in output
    assert "no planning agents are executed" in output


# ---------------------------------------------------------------------------
# Phase 44I — Planning Artifact Dry-Run
# ---------------------------------------------------------------------------


def test_44i_planning_dry_run_command_exits_zero(capsys) -> None:
    exit_code = main(["planning-dry-run"])
    assert exit_code == 0


def test_44i_planning_dry_run_json_exits_zero(capsys) -> None:
    exit_code = main(["planning-dry-run", "--json"])
    assert exit_code == 0


def test_44i_planning_dry_run_json_has_required_top_level_keys(capsys) -> None:
    main(["planning-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "objective" in data
    assert "planner_selection" in data
    assert "simulated_plans" in data
    assert "simulated_consensus" in data
    assert "human_review" in data
    assert "advisory" in data


def test_44i_planning_dry_run_objective_is_capability_validation(capsys) -> None:
    main(["planning-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    obj = data["objective"]
    assert "capability validation framework" in obj["objective_text"].lower()
    assert obj["objective_id"] == "plan-dry-run-001"
    assert "planning" in obj["required_capabilities"]
    assert "architecture" in obj["required_capabilities"]
    assert "roadmap-generation" in obj["required_capabilities"]


def test_44i_planning_dry_run_selects_three_planners(capsys) -> None:
    main(["planning-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    sel = data["planner_selection"]
    assert len(sel["selected_agents"]) == 3
    for expected in ("codex-local", "claude-local", "kimi-local"):
        assert expected in sel["selected_agents"]


def test_44i_planning_dry_run_selection_details_have_required_fields(capsys) -> None:
    main(["planning-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    for detail in data["planner_selection"]["selection_details"]:
        assert "agent_id" in detail
        assert "selection_reason" in detail
        assert "capability_used" in detail
        assert "confidence_level" in detail
        assert detail["confidence_level"] in ("observed", "validated", "proven")


def test_44i_planning_dry_run_simulated_plans_one_per_planner(capsys) -> None:
    main(["planning-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    plans = data["simulated_plans"]
    assert len(plans) == 3
    planner_ids = [p["planner_id"] for p in plans]
    for expected in ("codex-local", "claude-local", "kimi-local"):
        assert expected in planner_ids


def test_44i_planning_dry_run_simulated_plans_have_required_fields(capsys) -> None:
    main(["planning-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    for plan in data["simulated_plans"]:
        assert "planner_id" in plan
        assert "proposed_phases" in plan
        assert "assumptions" in plan
        assert "risks" in plan
        assert len(plan["proposed_phases"]) > 0


def test_44i_planning_dry_run_simulated_consensus_has_required_fields(capsys) -> None:
    main(["planning-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    cons = data["simulated_consensus"]
    assert "agreements" in cons
    assert "conflicts" in cons
    assert "consensus_summary" in cons
    assert len(cons["agreements"]) > 0
    assert len(cons["conflicts"]) > 0


def test_44i_planning_dry_run_human_review_required(capsys) -> None:
    main(["planning-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    review = data["human_review"]
    assert review["human_decision_required"] is True
    assert len(review["review_items"]) > 0


def test_44i_planning_dry_run_advisory_is_correct(capsys) -> None:
    main(["planning-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "simulated" in data["advisory"].lower()
    assert "no planning agents were executed" in data["advisory"].lower()


def test_44i_planning_dry_run_human_output_shows_planner_selection(capsys) -> None:
    main(["planning-dry-run"])
    output = capsys.readouterr().out
    assert "codex-local" in output
    assert "claude-local" in output
    assert "kimi-local" in output
    assert "validated" in output


def test_44i_planning_dry_run_human_output_shows_consensus_and_advisory(capsys) -> None:
    main(["planning-dry-run"])
    output = capsys.readouterr().out
    assert "Simulated consensus" in output
    assert "Human review required" in output
    assert "Planning dry-run is simulated" in output
    assert "No planning agents were executed" in output


# ---------------------------------------------------------------------------
# Phase 44J — Multi-Agent Planning Execution Design
# ---------------------------------------------------------------------------


def test_44j_planning_execution_design_command_exits_zero(capsys) -> None:
    exit_code = main(["planning-execution-design"])
    assert exit_code == 0


def test_44j_planning_execution_design_json_exits_zero(capsys) -> None:
    exit_code = main(["planning-execution-design", "--json"])
    assert exit_code == 0


def test_44j_planning_execution_design_json_has_required_top_level_keys(capsys) -> None:
    main(["planning-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "planning_execution_design" in data
    assert "planning_task_model" in data
    assert "planner_runtime_requirements" in data
    assert "execution_modes" in data
    assert "artifact_collection" in data
    assert "consensus_integration" in data
    assert "governance_integration" in data
    assert "future_evolution" in data
    assert "advisory" in data


def test_44j_planning_execution_design_lifecycle_has_eight_stages(capsys) -> None:
    main(["planning-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    lifecycle = data["planning_execution_design"]["lifecycle"]
    assert len(lifecycle) == 8


def test_44j_planning_execution_design_lifecycle_stages_have_required_fields(capsys) -> None:
    main(["planning-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    for stage in data["planning_execution_design"]["lifecycle"]:
        assert "stage" in stage
        assert "name" in stage
        assert "description" in stage
        assert isinstance(stage["stage"], int)


def test_44j_planning_execution_design_task_model_has_required_fields(capsys) -> None:
    main(["planning-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["planning_task_model"]["fields"]
    for expected in (
        "planning_task_id",
        "objective_id",
        "assigned_agent",
        "capability_required",
        "execution_mode",
        "timeout_seconds",
        "status",
        "artifact_ref",
    ):
        assert expected in fields


def test_44j_planning_execution_design_runtime_requirements_defined(capsys) -> None:
    main(["planning-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    reqs = data["planner_runtime_requirements"]
    assert len(reqs) == 4
    combined = " ".join(reqs).lower()
    assert "installed" in combined
    assert "available" in combined
    assert "planning" in combined
    assert "confidence" in combined


def test_44j_planning_execution_design_execution_modes_defined(capsys) -> None:
    main(["planning-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    modes = data["execution_modes"]
    assert len(modes) == 5
    mode_names = [m["mode"] for m in modes]
    for expected in (
        "single_planner",
        "sequential_planners",
        "parallel_planners",
        "swarm_planners",
        "consensus_planners",
    ):
        assert expected in mode_names
    for mode in modes:
        assert "description" in mode


def test_44j_planning_execution_design_artifact_collection_fields_defined(capsys) -> None:
    main(["planning-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["artifact_collection"]["fields"]
    for expected in ("phases", "dependencies", "assumptions", "risks", "recommendations", "confidence"):
        assert expected in fields


def test_44j_planning_execution_design_consensus_integration_defined(capsys) -> None:
    main(["planning-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    targets = data["consensus_integration"]["feeds_into"]
    assert "consensus engine" in targets
    assert "conflict analysis" in targets
    assert "agreement analysis" in targets


def test_44j_planning_execution_design_governance_requires_human_approval(capsys) -> None:
    main(["planning-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_integration"]
    before = gov["human_approval_required_before"]
    assert "task creation" in before
    assert "execution" in before
    assert "implementation" in before
    assert "roadmap_policy" in gov
    assert "advisory" in gov["roadmap_policy"].lower()


def test_44j_planning_execution_design_future_evolution_defined(capsys) -> None:
    main(["planning-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44K" in phases
    assert "44L" in phases
    assert "45A" in phases
    for entry in data["future_evolution"]:
        assert "description" in entry


def test_44j_planning_execution_design_advisory_is_correct(capsys) -> None:
    main(["planning-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data["advisory"].lower()
    assert "no planning agents are executed" in data["advisory"].lower()


def test_44j_planning_execution_design_human_output_shows_lifecycle_and_advisory(capsys) -> None:
    main(["planning-execution-design"])
    output = capsys.readouterr().out
    assert "objective" in output
    assert "approved_roadmap" in output
    assert "human_approval_required_before" in output or "Human approval required before" in output
    assert "Planning execution design is advisory" in output


# ---------------------------------------------------------------------------
# Phase 44K — Agent Execution Framework Design
# ---------------------------------------------------------------------------


def test_44k_execution_framework_design_command_exits_zero(capsys) -> None:
    exit_code = main(["execution-framework-design"])
    assert exit_code == 0


def test_44k_execution_framework_design_json_exits_zero(capsys) -> None:
    exit_code = main(["execution-framework-design", "--json"])
    assert exit_code == 0


def test_44k_execution_framework_design_json_has_required_top_level_keys(capsys) -> None:
    main(["execution-framework-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "execution_framework_design" in data
    assert "execution_lifecycle" in data
    assert "runtime_adapter_contract" in data
    assert "execution_request_model" in data
    assert "result_model" in data
    assert "governance_integration" in data
    assert "failure_model" in data
    assert "advisory" in data


def test_44k_execution_framework_design_lifecycle_has_nine_stages(capsys) -> None:
    main(["execution-framework-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert len(data["execution_lifecycle"]) == 9


def test_44k_execution_framework_design_lifecycle_stages_have_required_fields(capsys) -> None:
    main(["execution-framework-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    for stage in data["execution_lifecycle"]:
        assert "stage" in stage
        assert "name" in stage
        assert "description" in stage
        assert isinstance(stage["stage"], int)
    names = [s["name"] for s in data["execution_lifecycle"]]
    assert "request" in names
    assert "governance" in names


def test_44k_execution_framework_design_adapter_contract_fields_defined(capsys) -> None:
    main(["execution-framework-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["runtime_adapter_contract"]["fields"]
    for expected in (
        "runtime_id",
        "availability",
        "version",
        "capabilities",
        "supports_writable_execution",
        "supports_subagents",
        "supports_parallel_execution",
    ):
        assert expected in fields


def test_44k_execution_framework_design_adapter_required_operations_defined(capsys) -> None:
    main(["execution-framework-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    ops = data["runtime_adapter_contract"]["required_operations"]
    assert len(ops) == 5
    combined = " ".join(ops)
    assert "health" in combined
    assert "execute" in combined
    assert "cancel" in combined
    assert "collect_results" in combined


def test_44k_execution_framework_design_execution_request_model_has_required_fields(capsys) -> None:
    main(["execution-framework-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["execution_request_model"]["fields"]
    for expected in (
        "execution_id",
        "parent_task_id",
        "objective",
        "assigned_agent",
        "required_capabilities",
        "execution_mode",
        "writable_allowed",
        "timeout_seconds",
        "metadata",
    ):
        assert expected in fields


def test_44k_execution_framework_design_result_model_has_required_fields(capsys) -> None:
    main(["execution-framework-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["result_model"]["fields"]
    for expected in (
        "execution_id",
        "agent_id",
        "status",
        "started_at",
        "completed_at",
        "artifacts",
        "recommendations",
        "confidence",
        "errors",
    ):
        assert expected in fields


def test_44k_execution_framework_design_governance_may_and_may_not(capsys) -> None:
    main(["execution-framework-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_integration"]
    assert "invoke runtimes" in gov["framework_may"]
    assert "collect results" in gov["framework_may"]
    for prohibited in ("approve", "commit", "push", "rollback"):
        assert prohibited in gov["framework_may_not"]
    assert "note" in gov


def test_44k_execution_framework_design_failure_model_has_required_types(capsys) -> None:
    main(["execution-framework-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fm = data["failure_model"]
    for expected in (
        "unavailable_runtime",
        "timeout",
        "execution_failure",
        "partial_result",
        "cancelled",
        "capability_mismatch",
    ):
        assert expected in fm["failure_types"]
    assert "human" in fm["escalation"].lower()


def test_44k_execution_framework_design_future_evolution_defined(capsys) -> None:
    main(["execution-framework-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44L" in phases
    assert "44M" in phases
    assert "45A" in phases
    for entry in data["future_evolution"]:
        assert "description" in entry


def test_44k_execution_framework_design_advisory_is_correct(capsys) -> None:
    main(["execution-framework-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data["advisory"].lower()
    assert "no agent execution is performed" in data["advisory"].lower()


def test_44k_execution_framework_design_human_output_shows_lifecycle_and_advisory(capsys) -> None:
    main(["execution-framework-design"])
    output = capsys.readouterr().out
    assert "request" in output
    assert "governance" in output
    assert "framework_may" in output or "Framework may" in output
    assert "Execution framework design is advisory" in output


# ---------------------------------------------------------------------------
# Phase 44L — Runtime Adapter Integration Design
# ---------------------------------------------------------------------------


def test_44l_adapter_design_command_exits_zero(capsys) -> None:
    exit_code = main(["adapter-design"])
    assert exit_code == 0


def test_44l_adapter_design_json_exits_zero(capsys) -> None:
    exit_code = main(["adapter-design", "--json"])
    assert exit_code == 0


def test_44l_adapter_design_json_has_required_top_level_keys(capsys) -> None:
    main(["adapter-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "adapter_design" in data
    assert "adapter_registry" in data
    assert "adapter_contract" in data
    assert "adapter_health_model" in data
    assert "governance_integration" in data
    assert "future_evolution" in data
    assert "advisory" in data


def test_44l_adapter_design_architecture_layers_defined(capsys) -> None:
    main(["adapter-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    layers = data["adapter_design"]["architecture_layers"]
    assert len(layers) == 5
    combined = " ".join(layers).lower()
    assert "coordinator" in combined
    assert "execution framework" in combined
    assert "registry" in combined
    assert "agent runtime" in combined


def test_44l_adapter_design_registry_responsibilities_and_fields(capsys) -> None:
    main(["adapter-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    reg = data["adapter_registry"]
    assert len(reg["responsibilities"]) == 5
    combined_resp = " ".join(reg["responsibilities"]).lower()
    assert "register" in combined_resp
    assert "health" in combined_resp
    for expected in (
        "runtime_id",
        "adapter_class",
        "lifecycle_status",
        "supported_capabilities",
        "writable_supported",
        "subagent_supported",
        "parallel_supported",
    ):
        assert expected in reg["fields"]


def test_44l_adapter_design_contract_required_methods(capsys) -> None:
    main(["adapter-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    required = data["adapter_contract"]["required_methods"]
    assert len(required) == 5
    combined = " ".join(required)
    assert "health()" in combined
    assert "execute()" in combined
    assert "cancel()" in combined
    assert "collect_results()" in combined
    assert "discover_capabilities()" in combined


def test_44l_adapter_design_contract_optional_methods(capsys) -> None:
    main(["adapter-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    optional = data["adapter_contract"]["optional_methods"]
    assert len(optional) == 5
    combined = " ".join(optional)
    assert "discover_subagents()" in combined
    assert "discover_skills()" in combined
    assert "estimate_cost()" in combined


def test_44l_adapter_design_initial_adapters_defined(capsys) -> None:
    main(["adapter-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    adapters = data["adapter_design"]["initial_adapters"]
    assert len(adapters) == 3
    ids = [a["adapter_id"] for a in adapters]
    assert "codex-local-adapter" in ids
    assert "claude-local-adapter" in ids
    assert "kimi-local-adapter" in ids
    for adapter in adapters:
        assert "supports" in adapter
        assert "execution" in adapter["supports"]
        assert "writable execution" in adapter["supports"]


def test_44l_adapter_design_future_adapters_defined(capsys) -> None:
    main(["adapter-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    future = data["adapter_design"]["future_adapters"]
    assert len(future) >= 4
    combined = " ".join(future)
    assert "deepseek" in combined
    assert "gemini" in combined
    assert "cloud" in combined


def test_44l_adapter_design_health_states_defined(capsys) -> None:
    main(["adapter-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    health = data["adapter_health_model"]
    for expected in ("available", "degraded", "unavailable", "unknown"):
        assert expected in health["states"]
    assert len(health["capability_sync"]) == 3
    assert "source of truth" in health["capability_registry_note"].lower()


def test_44l_adapter_design_governance_may_and_may_not(capsys) -> None:
    main(["adapter-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_integration"]
    assert "execute runtime requests" in gov["adapters_may"]
    assert "collect runtime results" in gov["adapters_may"]
    for prohibited in ("approve", "commit", "push", "rollback", "bypass governance"):
        assert prohibited in gov["adapters_may_not"]


def test_44l_adapter_design_future_evolution_defined(capsys) -> None:
    main(["adapter-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44M" in phases
    assert "44N" in phases
    assert "44O" in phases
    assert "45A" in phases
    for entry in data["future_evolution"]:
        assert "description" in entry


def test_44l_adapter_design_advisory_is_correct(capsys) -> None:
    main(["adapter-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data["advisory"].lower()
    assert "no adapters are executed" in data["advisory"].lower()


def test_44l_adapter_design_human_output_shows_architecture_and_advisory(capsys) -> None:
    main(["adapter-design"])
    output = capsys.readouterr().out
    assert "Coordinator" in output
    assert "Agent Runtime" in output
    assert "codex-local-adapter" in output
    assert "Runtime adapter integration design is advisory" in output


# ---------------------------------------------------------------------------
# Phase 44M — Controlled Agent Invocation Design
# ---------------------------------------------------------------------------


def test_44m_invocation_design_command_exits_zero(capsys) -> None:
    exit_code = main(["invocation-design"])
    assert exit_code == 0


def test_44m_invocation_design_json_exits_zero(capsys) -> None:
    exit_code = main(["invocation-design", "--json"])
    assert exit_code == 0


def test_44m_invocation_design_json_has_required_top_level_keys(capsys) -> None:
    main(["invocation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "invocation_design" in data
    assert "invocation_lifecycle" in data
    assert "invocation_request_model" in data
    assert "safety_gates" in data
    assert "writable_rules" in data
    assert "result_capture_model" in data
    assert "governance_integration" in data
    assert "advisory" in data


def test_44m_invocation_design_lifecycle_has_nine_stages(capsys) -> None:
    main(["invocation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    lifecycle = data["invocation_lifecycle"]
    assert len(lifecycle) == 9
    for stage in lifecycle:
        assert "stage" in stage
        assert "name" in stage
        assert "description" in stage
        assert isinstance(stage["stage"], int)
    names = [s["name"] for s in lifecycle]
    assert "request" in names
    assert "governance" in names
    assert "capability_validation" in names
    assert "runtime_invocation" in names


def test_44m_invocation_design_request_model_has_required_fields(capsys) -> None:
    main(["invocation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["invocation_request_model"]["fields"]
    for expected in (
        "invocation_id",
        "execution_id",
        "runtime_id",
        "agent_id",
        "objective",
        "capabilities_required",
        "writable_allowed",
        "timeout_seconds",
        "metadata",
    ):
        assert expected in fields


def test_44m_invocation_design_safety_gates_required_defined(capsys) -> None:
    main(["invocation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    required = data["safety_gates"]["required_before_invocation"]
    assert len(required) == 5
    combined = " ".join(required).lower()
    assert "runtime available" in combined
    assert "capability present" in combined
    assert "confidence threshold" in combined
    assert "objective present" in combined


def test_44m_invocation_design_safety_gates_blocked_defined(capsys) -> None:
    main(["invocation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    blocked = data["safety_gates"]["blocked_if"]
    assert len(blocked) == 4
    combined = " ".join(blocked).lower()
    assert "runtime unavailable" in combined
    assert "capability mismatch" in combined
    assert "governance violation" in combined
    assert "timeout invalid" in combined


def test_44m_invocation_design_writable_rules_default_read_only(capsys) -> None:
    main(["invocation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    wr = data["writable_rules"]
    assert wr["default"] == "read-only"
    requires = wr["writable_requires"]
    assert len(requires) == 3
    combined = " ".join(requires).lower()
    assert "governance approval" in combined
    assert "writable_supported" in combined
    assert "audit trail" in combined


def test_44m_invocation_design_result_capture_model_fields(capsys) -> None:
    main(["invocation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["result_capture_model"]["fields"]
    for expected in (
        "invocation_id",
        "status",
        "artifacts",
        "recommendations",
        "confidence",
        "errors",
        "timestamps",
    ):
        assert expected in fields


def test_44m_invocation_design_governance_may_and_may_not(capsys) -> None:
    main(["invocation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_integration"]
    assert "invoke agents" in gov["system_may"]
    assert "collect results" in gov["system_may"]
    for prohibited in ("approve", "commit", "push", "rollback", "bypass governance"):
        assert prohibited in gov["system_may_not"]


def test_44m_invocation_design_invocation_flow_defined(capsys) -> None:
    main(["invocation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    inv = data["invocation_design"]
    assert "coordinator" in inv["invocation_flow"]
    assert "runtime" in inv["invocation_flow"]
    assert "runtime" in inv["result_flow"]
    assert "coordinator" in inv["result_flow"]


def test_44m_invocation_design_future_evolution_defined(capsys) -> None:
    main(["invocation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44N" in phases
    assert "44O" in phases
    assert "45A" in phases
    for entry in data["future_evolution"]:
        assert "description" in entry


def test_44m_invocation_design_advisory_is_correct(capsys) -> None:
    main(["invocation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data["advisory"].lower()
    assert "no agents are invoked" in data["advisory"].lower()


def test_44m_invocation_design_human_output_shows_lifecycle_and_advisory(capsys) -> None:
    main(["invocation-design"])
    output = capsys.readouterr().out
    assert "request" in output
    assert "governance" in output
    assert "read-only" in output
    assert "Controlled invocation design is advisory" in output


def test_44n_real_planning_design_command_exits_zero(capsys) -> None:
    exit_code = main(["real-planning-design"])
    assert exit_code == 0


def test_44n_real_planning_design_json_exits_zero(capsys) -> None:
    exit_code = main(["real-planning-design", "--json"])
    assert exit_code == 0


def test_44n_real_planning_design_json_has_required_top_level_keys(capsys) -> None:
    main(["real-planning-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "real_planning_design" in data
    assert "planning_lifecycle" in data
    assert "planner_eligibility" in data
    assert "execution_modes" in data
    assert "planning_artifact_model" in data
    assert "consensus_integration" in data
    assert "human_review_model" in data
    assert "governance_integration" in data
    assert "advisory" in data


def test_44n_real_planning_design_lifecycle_has_nine_stages(capsys) -> None:
    main(["real-planning-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    lifecycle = data["planning_lifecycle"]
    assert len(lifecycle) == 9
    for stage in lifecycle:
        assert "stage" in stage
        assert "name" in stage
        assert "description" in stage
        assert isinstance(stage["stage"], int)
    names = [s["name"] for s in lifecycle]
    assert "objective" in names
    assert "planner_selection" in names
    assert "artifact_collection" in names
    assert "human_review" in names
    assert "approved_roadmap" in names


def test_44n_real_planning_design_planner_eligibility_criteria(capsys) -> None:
    main(["real-planning-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    criteria = data["planner_eligibility"]["criteria"]
    assert len(criteria) == 5
    combined = " ".join(criteria).lower()
    assert "installed" in combined
    assert "available" in combined
    assert "planning capability" in combined
    assert "confidence threshold" in combined
    assert "invocation safety gates" in combined


def test_44n_real_planning_design_execution_modes_defined(capsys) -> None:
    main(["real-planning-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    modes = data["execution_modes"]
    assert len(modes) == 5
    mode_names = [m["mode"] for m in modes]
    assert "single_planner" in mode_names
    assert "sequential_planners" in mode_names
    assert "parallel_planners" in mode_names
    assert "swarm_planners" in mode_names
    assert "consensus_planners" in mode_names
    for mode in modes:
        assert "description" in mode


def test_44n_real_planning_design_artifact_model_fields(capsys) -> None:
    main(["real-planning-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["planning_artifact_model"]["fields"]
    for expected in (
        "artifact_id",
        "objective_id",
        "planner_id",
        "proposed_phases",
        "dependencies",
        "assumptions",
        "risks",
        "recommendations",
        "confidence",
    ):
        assert expected in fields


def test_44n_real_planning_design_consensus_integration_defined(capsys) -> None:
    main(["real-planning-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    feeds = data["consensus_integration"]["feeds_into"]
    assert len(feeds) == 3
    combined = " ".join(feeds).lower()
    assert "agreement" in combined
    assert "conflict" in combined
    assert "consensus summary" in combined


def test_44n_real_planning_design_human_review_model_defined(capsys) -> None:
    main(["real-planning-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    review = data["human_review_model"]
    assert review["human_review_required"] is True
    actions = review["actions"]
    assert len(actions) == 4
    combined = " ".join(actions).lower()
    assert "approve roadmap" in combined
    assert "reject roadmap" in combined
    assert "request changes" in combined
    assert "request additional planners" in combined


def test_44n_real_planning_design_governance_may_and_may_not(capsys) -> None:
    main(["real-planning-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_integration"]
    assert "invoke planners" in gov["system_may"]
    assert "collect planning artifacts" in gov["system_may"]
    for prohibited in ("approve implementation", "commit", "push", "rollback", "bypass governance"):
        assert prohibited in gov["system_may_not"]


def test_44n_real_planning_design_future_evolution_defined(capsys) -> None:
    main(["real-planning-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44O" in phases
    assert "44P" in phases
    assert "44Q" in phases
    assert "45A" in phases
    for entry in data["future_evolution"]:
        assert "description" in entry


def test_44n_real_planning_design_advisory_is_correct(capsys) -> None:
    main(["real-planning-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data["advisory"].lower()
    assert "no planners are executed" in data["advisory"].lower()


def test_44n_real_planning_design_human_output_shows_lifecycle_and_advisory(capsys) -> None:
    main(["real-planning-design"])
    output = capsys.readouterr().out
    assert "objective" in output
    assert "human_review" in output
    assert "approved_roadmap" in output
    assert "Real planning design is advisory" in output


def test_44o_consensus_execution_design_command_exits_zero(capsys) -> None:
    exit_code = main(["consensus-execution-design"])
    assert exit_code == 0


def test_44o_consensus_execution_design_json_exits_zero(capsys) -> None:
    exit_code = main(["consensus-execution-design", "--json"])
    assert exit_code == 0


def test_44o_consensus_execution_design_json_has_required_top_level_keys(capsys) -> None:
    main(["consensus-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "consensus_execution_design" in data
    assert "execution_lifecycle" in data
    assert "consensus_input_model" in data
    assert "agreement_analysis" in data
    assert "conflict_analysis" in data
    assert "weighting_model" in data
    assert "recommendation_types" in data
    assert "human_review_requirements" in data
    assert "governance_integration" in data
    assert "advisory" in data


def test_44o_consensus_execution_design_lifecycle_has_eight_stages(capsys) -> None:
    main(["consensus-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    lifecycle = data["execution_lifecycle"]
    assert len(lifecycle) == 8
    for stage in lifecycle:
        assert "stage" in stage
        assert "name" in stage
        assert "description" in stage
        assert isinstance(stage["stage"], int)
    names = [s["name"] for s in lifecycle]
    assert "agent_outputs" in names
    assert "agreement_analysis" in names
    assert "conflict_analysis" in names
    assert "consensus_evaluation" in names
    assert "decision_recommendation" in names
    assert "human_review" in names


def test_44o_consensus_execution_design_input_model_fields(capsys) -> None:
    main(["consensus-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["consensus_input_model"]["fields"]
    for expected in (
        "consensus_id",
        "execution_id",
        "agent_id",
        "role",
        "recommendation",
        "confidence",
        "rationale",
        "artifacts",
    ):
        assert expected in fields


def test_44o_consensus_execution_design_agreement_analysis_defined(capsys) -> None:
    main(["consensus-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    identifies = data["agreement_analysis"]["identifies"]
    assert len(identifies) == 3
    combined = " ".join(identifies).lower()
    assert "matching recommendations" in combined
    assert "compatible recommendations" in combined
    assert "supporting evidence" in combined


def test_44o_consensus_execution_design_conflict_analysis_defined(capsys) -> None:
    main(["consensus-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    identifies = data["conflict_analysis"]["identifies"]
    assert len(identifies) == 4
    combined = " ".join(identifies).lower()
    assert "conflicting recommendations" in combined
    assert "incompatible plans" in combined
    assert "missing evidence" in combined
    assert "confidence discrepancies" in combined


def test_44o_consensus_execution_design_weighting_model_inputs(capsys) -> None:
    main(["consensus-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    inputs = data["weighting_model"]["inputs"]
    assert len(inputs) == 5
    combined = " ".join(inputs).lower()
    assert "capability confidence" in combined
    assert "runtime availability" in combined
    assert "successful execution history" in combined
    assert "task fit" in combined
    assert "role fit" in combined


def test_44o_consensus_execution_design_recommendation_types_defined(capsys) -> None:
    main(["consensus-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    types = data["recommendation_types"]
    assert len(types) == 5
    type_names = [r["type"] for r in types]
    for expected in ("approve", "reject", "request_changes", "inconclusive", "escalate_to_human"):
        assert expected in type_names
    for rec in types:
        assert "description" in rec


def test_44o_consensus_execution_design_human_review_requirements(capsys) -> None:
    main(["consensus-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    conditions = data["human_review_requirements"]["human_required_when"]
    assert len(conditions) == 4
    combined = " ".join(conditions).lower()
    assert "conflicts exceed threshold" in combined
    assert "confidence below threshold" in combined
    assert "recommendation inconclusive" in combined
    assert "governance-sensitive" in combined


def test_44o_consensus_execution_design_governance_may_and_may_not(capsys) -> None:
    main(["consensus-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_integration"]
    assert "evaluate outputs" in gov["system_may"]
    assert "calculate weights" in gov["system_may"]
    assert "generate recommendations" in gov["system_may"]
    for prohibited in ("approve implementation", "commit", "push", "rollback", "bypass governance"):
        assert prohibited in gov["system_may_not"]


def test_44o_consensus_execution_design_future_evolution_defined(capsys) -> None:
    main(["consensus-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44P" in phases
    assert "44Q" in phases
    assert "44R" in phases
    assert "45A" in phases
    for entry in data["future_evolution"]:
        assert "description" in entry


def test_44o_consensus_execution_design_advisory_is_correct(capsys) -> None:
    main(["consensus-execution-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data["advisory"].lower()
    assert "no consensus execution is performed" in data["advisory"].lower()


def test_44o_consensus_execution_design_human_output_shows_lifecycle_and_advisory(capsys) -> None:
    main(["consensus-execution-design"])
    output = capsys.readouterr().out
    assert "agent_outputs" in output
    assert "human_review" in output
    assert "decision_recommendation" in output
    assert "Consensus execution design is advisory" in output


def test_44p_runtime_execution_prototype_command_exits_zero(capsys) -> None:
    exit_code = main(["runtime-execution-prototype"])
    assert exit_code == 0


def test_44p_runtime_execution_prototype_json_exits_zero(capsys) -> None:
    exit_code = main(["runtime-execution-prototype", "--json"])
    assert exit_code == 0


def test_44p_runtime_execution_prototype_json_has_required_top_level_keys(capsys) -> None:
    main(["runtime-execution-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "runtime_execution_prototype" in data
    assert "execution_request_model" in data
    assert "adapter_resolution_model" in data
    assert "runtime_invocation_model" in data
    assert "result_capture_model" in data
    assert "timeout_model" in data
    assert "failure_model" in data
    assert "prototype_restrictions" in data
    assert "governance_integration" in data
    assert "advisory" in data


def test_44p_runtime_execution_prototype_execution_request_model_fields(capsys) -> None:
    main(["runtime-execution-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["execution_request_model"]["fields"]
    for expected in (
        "request_id",
        "runtime_id",
        "objective",
        "capabilities_required",
        "timeout_seconds",
        "read_only",
        "metadata",
    ):
        assert expected in fields


def test_44p_runtime_execution_prototype_adapter_resolution_steps_defined(capsys) -> None:
    main(["runtime-execution-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    steps = data["adapter_resolution_model"]["steps"]
    assert len(steps) == 4
    combined = " ".join(steps).lower()
    assert "runtime_id" in combined
    assert "adapter health" in combined
    assert "capability match" in combined
    assert "resolve adapter instance" in combined


def test_44p_runtime_execution_prototype_invocation_model_single_read_only(capsys) -> None:
    main(["runtime-execution-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    inv = data["runtime_invocation_model"]
    assert inv["execution_mode"] == "non_interactive"
    assert inv["single_runtime"] is True
    assert inv["writable"] is False
    assert "structured" in inv["output_capture"]
    assert "stdin" in inv["delivery_methods"] or "prompt_file" in inv["delivery_methods"]


def test_44p_runtime_execution_prototype_result_capture_model_fields(capsys) -> None:
    main(["runtime-execution-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    rc = data["result_capture_model"]
    for expected in (
        "request_id",
        "status",
        "output",
        "artifacts",
        "errors",
        "started_at",
        "completed_at",
        "duration_seconds",
    ):
        assert expected in rc["fields"]
    statuses = rc["statuses"]
    assert "completed" in statuses
    assert "timed_out" in statuses
    assert "failed" in statuses


def test_44p_runtime_execution_prototype_timeout_model_defined(capsys) -> None:
    main(["runtime-execution-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    rules = data["timeout_model"]["rules"]
    assert len(rules) >= 3
    combined = " ".join(rules).lower()
    assert "timeout_seconds" in combined
    assert "timed_out" in combined
    assert "partial output" in combined


def test_44p_runtime_execution_prototype_failure_model_types_defined(capsys) -> None:
    main(["runtime-execution-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    types = [f["type"] for f in data["failure_model"]["types"]]
    assert len(types) == 5
    for expected in (
        "adapter_unavailable",
        "capability_mismatch",
        "timeout",
        "execution_error",
        "output_parse_failure",
    ):
        assert expected in types
    for ft in data["failure_model"]["types"]:
        assert "description" in ft


def test_44p_runtime_execution_prototype_restrictions_enforce_spec(capsys) -> None:
    main(["runtime-execution-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    restrictions = data["prototype_restrictions"]
    assert len(restrictions) == 9
    for expected in (
        "read_only_only",
        "single_runtime_only",
        "no_writable_execution",
        "no_commit",
        "no_push",
        "no_rollback",
        "no_subagents",
        "no_swarm",
        "no_consensus",
    ):
        assert expected in restrictions


def test_44p_runtime_execution_prototype_governance_may_and_may_not(capsys) -> None:
    main(["runtime-execution-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_integration"]
    assert "create execution requests" in gov["system_may"]
    assert "resolve adapters" in gov["system_may"]
    assert "capture results" in gov["system_may"]
    for prohibited in ("approve implementation", "commit", "push", "rollback", "bypass governance"):
        assert prohibited in gov["system_may_not"]


def test_44p_runtime_execution_prototype_future_evolution_defined(capsys) -> None:
    main(["runtime-execution-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44Q" in phases
    assert "44R" in phases
    assert "45A" in phases
    for entry in data["future_evolution"]:
        assert "description" in entry


def test_44p_runtime_execution_prototype_advisory_is_correct(capsys) -> None:
    main(["runtime-execution-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data["advisory"].lower()
    assert "no agents are executed" in data["advisory"].lower()


def test_44p_runtime_execution_prototype_human_output_shows_sections_and_advisory(capsys) -> None:
    main(["runtime-execution-prototype"])
    output = capsys.readouterr().out
    assert "non_interactive" in output
    assert "timeout" in output
    assert "adapter_unavailable" in output
    assert "Runtime execution prototype is advisory" in output


def test_44q_planner_adapter_prototype_command_exits_zero(capsys) -> None:
    exit_code = main(["planner-adapter-prototype"])
    assert exit_code == 0


def test_44q_planner_adapter_prototype_json_exits_zero(capsys) -> None:
    exit_code = main(["planner-adapter-prototype", "--json"])
    assert exit_code == 0


def test_44q_planner_adapter_prototype_json_has_required_top_level_keys(capsys) -> None:
    main(["planner-adapter-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "planner_adapter_prototype" in data
    assert "adapter_resolution" in data
    assert "invocation_preview" in data
    assert "safety_gates" in data
    assert "blockers" in data
    assert "advisory" in data


def test_44q_planner_adapter_prototype_selects_codex_local_by_default(capsys) -> None:
    main(["planner-adapter-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    proto = data["planner_adapter_prototype"]
    assert proto["selected_runtime"] == "codex-local"
    assert proto["selected_agent"] == "codex"
    assert proto["capability_required"] == "planning"


def test_44q_planner_adapter_prototype_execution_mode_non_interactive(capsys) -> None:
    main(["planner-adapter-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    proto = data["planner_adapter_prototype"]
    assert proto["execution_mode"] == "non_interactive"
    assert isinstance(proto["timeout_seconds"], int)
    assert proto["timeout_seconds"] > 0


def test_44q_planner_adapter_prototype_adapter_resolution_fields(capsys) -> None:
    main(["planner-adapter-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    res = data["adapter_resolution"]
    assert "codex-local" in res["registry_lookup"]
    assert res["adapter_type"] == "cli"
    assert "planning" in res["capability_verified"].lower()
    assert "resolution_status" in res


def test_44q_planner_adapter_prototype_invocation_preview_defined(capsys) -> None:
    main(["planner-adapter-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    inv = data["invocation_preview"]
    assert "invocation_command_preview" in inv
    assert "codex" in inv["invocation_command_preview"].lower()
    assert inv["execution_mode"] == "non_interactive"
    assert isinstance(inv["timeout_seconds"], int)
    assert "result_capture_model" in inv
    for expected in ("planner_request_id", "status", "output", "proposed_phases", "confidence"):
        assert expected in inv["result_capture_model"]


def test_44q_planner_adapter_prototype_safety_gates_defined(capsys) -> None:
    main(["planner-adapter-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    gates = data["safety_gates"]
    assert len(gates) >= 4
    combined = " ".join(gates).lower()
    assert "runtime_id" in combined
    assert "capability_required" in combined
    assert "read_only" in combined
    assert "timeout" in combined


def test_44q_planner_adapter_prototype_blockers_defined(capsys) -> None:
    main(["planner-adapter-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    blockers = data["blockers"]
    assert len(blockers) >= 2
    combined = " ".join(blockers).lower()
    assert "codex-local" in combined
    assert "writable" in combined or "not installed" in combined


def test_44q_planner_adapter_prototype_scope_read_only_single_runtime(capsys) -> None:
    main(["planner-adapter-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    scope = data["planner_adapter_prototype"]["prototype_scope"]
    assert "read_only_only" in scope
    assert "single_runtime_only" in scope
    assert "no_writable_execution" in scope
    assert "no_commit" in scope
    assert "no_push" in scope
    assert "no_consensus_execution" in scope


def test_44q_planner_adapter_prototype_no_actual_execution(capsys) -> None:
    main(["planner-adapter-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    res = data["adapter_resolution"]
    assert "prototype" in res["resolution_status"].lower()
    assert "not probed" in res["health_check"].lower()


def test_44q_planner_adapter_prototype_future_evolution_defined(capsys) -> None:
    main(["planner-adapter-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44R" in phases
    assert "45A" in phases


def test_44q_planner_adapter_prototype_advisory_is_correct(capsys) -> None:
    main(["planner-adapter-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "read-only" in data["advisory"].lower()
    assert "no planner runtime is invoked" in data["advisory"].lower()


def test_44q_planner_adapter_prototype_human_output_shows_summary_and_advisory(capsys) -> None:
    main(["planner-adapter-prototype"])
    output = capsys.readouterr().out
    assert "codex-local" in output
    assert "non_interactive" in output
    assert "Safety gates" in output
    assert "Planner adapter prototype is read-only" in output


# ---------------------------------------------------------------------------
# Phase 44R: Multi-Agent Execution Prototype
# ---------------------------------------------------------------------------


def test_44r_multi_agent_prototype_command_exits_zero(capsys) -> None:
    exit_code = main(["multi-agent-prototype"])
    assert exit_code == 0


def test_44r_multi_agent_prototype_json_exits_zero(capsys) -> None:
    exit_code = main(["multi-agent-prototype", "--json"])
    assert exit_code == 0


def test_44r_multi_agent_prototype_json_has_required_top_level_keys(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "execution_plan" in data
    assert "selected_agents" in data
    assert "invocation_previews" in data
    assert "aggregation_plan" in data
    assert "governance_rules" in data
    assert "advisory" in data


def test_44r_multi_agent_prototype_selects_default_agents(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    agents = data["selected_agents"]
    assert "codex-local" in agents
    assert "claude-local" in agents
    assert "kimi-local" in agents
    assert len(agents) >= 2


def test_44r_multi_agent_prototype_execution_plan_fields(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    plan = data["execution_plan"]
    assert "execution_id" in plan
    assert "selected_agents" in plan
    assert "assigned_roles" in plan
    assert "capabilities_used" in plan
    assert "orchestration_strategy" in plan
    assert len(plan["selected_agents"]) >= 2
    assert len(plan["assigned_roles"]) >= 2
    assert len(plan["capabilities_used"]) >= 1


def test_44r_multi_agent_prototype_orchestration_strategy_supported(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    plan = data["execution_plan"]
    supported = plan["supported_strategies"]
    assert plan["orchestration_strategy"] in supported
    for strategy in ("single_agent", "sequential", "parallel_review", "parallel_planning", "consensus"):
        assert strategy in supported


def test_44r_multi_agent_prototype_invocation_previews_per_agent(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    previews = data["invocation_previews"]
    assert len(previews) >= 2
    for inv in previews:
        assert "runtime_id" in inv
        assert "adapter_id" in inv
        assert "invocation_preview" in inv
        assert "timeout_seconds" in inv
        assert "writable_allowed" in inv
        assert isinstance(inv["timeout_seconds"], int)
        assert inv["timeout_seconds"] > 0
        assert inv["writable_allowed"] is False


def test_44r_multi_agent_prototype_invocation_previews_match_selected_agents(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    selected = set(data["selected_agents"])
    preview_ids = {inv["runtime_id"] for inv in data["invocation_previews"]}
    assert preview_ids == selected


def test_44r_multi_agent_prototype_aggregation_plan_sections(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    agg = data["aggregation_plan"]
    assert "result_collection_plan" in agg
    assert "artifact_collection_plan" in agg
    assert "consensus_input_plan" in agg


def test_44r_multi_agent_prototype_result_collection_plan_fields(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    rc = data["aggregation_plan"]["result_collection_plan"]
    assert rc["collection_mode"] == "structured"
    assert rc["per_agent_results"] is True
    assert rc["partial_results_preserved"] is True
    for field in ("agent_id", "status", "output", "artifacts", "errors"):
        assert field in rc["result_fields"]


def test_44r_multi_agent_prototype_artifact_collection_read_only(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    ac = data["aggregation_plan"]["artifact_collection_plan"]
    assert ac["collection_mode"] == "read_only"
    assert "no artifacts written" in ac["persistence"].lower()


def test_44r_multi_agent_prototype_governance_rules_defined(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_rules"]
    assert "prototype_may" in gov
    assert "prototype_may_not" in gov
    may = " ".join(gov["prototype_may"]).lower()
    may_not = " ".join(gov["prototype_may_not"]).lower()
    assert "select agents" in may
    assert "invoke runtimes" in may_not
    assert "submit prompts" in may_not
    assert "modify files" in may_not
    assert "commit" in may_not
    assert "push" in may_not
    assert "rollback" in may_not


def test_44r_multi_agent_prototype_advisory_is_correct(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "read-only" in data["advisory"].lower()
    assert "no runtimes are invoked" in data["advisory"].lower()


def test_44r_multi_agent_prototype_future_evolution_defined(capsys) -> None:
    main(["multi-agent-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44S" in phases
    assert "44T" in phases
    assert "45A" in phases


def test_44r_multi_agent_prototype_human_output_shows_sections_and_advisory(capsys) -> None:
    main(["multi-agent-prototype"])
    output = capsys.readouterr().out
    assert "Multi-agent execution prototype" in output
    assert "codex-local" in output
    assert "claude-local" in output
    assert "kimi-local" in output
    assert "Invocation previews" in output
    assert "Aggregation plan" in output
    assert "Governance" in output
    assert "Multi-agent execution prototype is read-only" in output


# ---------------------------------------------------------------------------
# Phase 44S: Consensus Prototype
# ---------------------------------------------------------------------------


def test_44s_consensus_prototype_command_exits_zero(capsys) -> None:
    exit_code = main(["consensus-prototype"])
    assert exit_code == 0


def test_44s_consensus_prototype_json_exits_zero(capsys) -> None:
    exit_code = main(["consensus-prototype", "--json"])
    assert exit_code == 0


def test_44s_consensus_prototype_json_has_required_top_level_keys(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "simulated_inputs" in data
    assert "aggregation" in data
    assert "agreement_analysis" in data
    assert "conflict_analysis" in data
    assert "weighting_preview" in data
    assert "recommendation_preview" in data
    assert "governance_rules" in data
    assert "advisory" in data


def test_44s_consensus_prototype_simulated_inputs_generated(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    inputs = data["simulated_inputs"]
    assert len(inputs) == 3
    agent_ids = {inp["agent_id"] for inp in inputs}
    assert "codex-local" in agent_ids
    assert "claude-local" in agent_ids
    assert "kimi-local" in agent_ids


def test_44s_consensus_prototype_simulated_inputs_have_required_fields(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    for inp in data["simulated_inputs"]:
        assert "agent_id" in inp
        assert "recommendation" in inp
        assert "confidence" in inp
        assert "rationale" in inp
        assert isinstance(inp["confidence"], float)
        assert 0.0 < inp["confidence"] <= 1.0


def test_44s_consensus_prototype_aggregation_fields(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    agg = data["aggregation"]
    assert "collected_outputs" in agg
    assert "agreement_candidates" in agg
    assert "conflict_candidates" in agg
    assert len(agg["collected_outputs"]) == 3
    assert len(agg["agreement_candidates"]) >= 1
    assert len(agg["conflict_candidates"]) >= 1


def test_44s_consensus_prototype_agreement_analysis(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    aa = data["agreement_analysis"]
    assert "agreements" in aa
    assert "agreement_count" in aa
    assert aa["agreement_count"] == len(aa["agreements"])
    assert aa["agreement_count"] >= 1
    combined = " ".join(aa["agreements"]).lower()
    assert "approve" in combined


def test_44s_consensus_prototype_conflict_analysis(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    ca = data["conflict_analysis"]
    assert "conflicts" in ca
    assert "conflict_count" in ca
    assert "confidence_differences" in ca
    assert ca["conflict_count"] == len(ca["conflicts"])
    assert ca["conflict_count"] >= 1
    cd = ca["confidence_differences"]
    assert "max" in cd
    assert "min" in cd
    assert "spread" in cd
    assert cd["spread"] == round(cd["max"] - cd["min"], 10)


def test_44s_consensus_prototype_weighting_preview(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    wp = data["weighting_preview"]
    assert "weights" in wp
    assert "note" in wp
    assert len(wp["weights"]) == 3
    for w in wp["weights"]:
        assert "agent_id" in w
        assert "capability_confidence" in w
        assert "task_fit" in w
        assert "role_fit" in w
        assert "preview_weight" in w
        assert isinstance(w["preview_weight"], float)
    total = sum(w["preview_weight"] for w in wp["weights"])
    assert abs(total - 1.0) < 0.01


def test_44s_consensus_prototype_recommendation_preview(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    rp = data["recommendation_preview"]
    assert "recommended_outcome" in rp
    assert "valid_outcomes" in rp
    assert "basis" in rp
    assert rp["recommended_outcome"] in rp["valid_outcomes"]
    for outcome in ("approve", "reject", "request_changes", "inconclusive", "escalate_to_human"):
        assert outcome in rp["valid_outcomes"]


def test_44s_consensus_prototype_human_review_always_required(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    rp = data["recommendation_preview"]
    assert rp["human_review_required"] is True
    assert "human_review_reason" in rp
    assert len(rp["human_review_reason"]) > 0


def test_44s_consensus_prototype_governance_rules(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_rules"]
    assert "prototype_may" in gov
    assert "prototype_may_not" in gov
    may = " ".join(gov["prototype_may"]).lower()
    may_not = " ".join(gov["prototype_may_not"]).lower()
    assert "aggregate" in may
    assert "analyze" in may
    assert "execute consensus" in may_not
    assert "invoke runtimes" in may_not
    assert "modify files" in may_not
    assert "commit" in may_not
    assert "push" in may_not
    assert "rollback" in may_not


def test_44s_consensus_prototype_advisory_is_correct(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "simulated" in data["advisory"].lower()
    assert "no runtimes are invoked" in data["advisory"].lower()


def test_44s_consensus_prototype_future_evolution_defined(capsys) -> None:
    main(["consensus-prototype", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44T" in phases
    assert "44U" in phases
    assert "45A" in phases


def test_44s_consensus_prototype_human_output_shows_sections_and_advisory(capsys) -> None:
    main(["consensus-prototype"])
    output = capsys.readouterr().out
    assert "Consensus prototype" in output
    assert "Simulated inputs" in output
    assert "Agreement analysis" in output
    assert "Conflict analysis" in output
    assert "Weighting preview" in output
    assert "Recommendation preview" in output
    assert "Governance" in output
    assert "Consensus prototype is simulated" in output


# ---------------------------------------------------------------------------
# Phase 44T: Controlled Runtime Invocation Pilot
# ---------------------------------------------------------------------------


def test_44t_invocation_pilot_command_exits_zero(capsys) -> None:
    exit_code = main(["invocation-pilot"])
    assert exit_code == 0


def test_44t_invocation_pilot_json_exits_zero(capsys) -> None:
    exit_code = main(["invocation-pilot", "--json"])
    assert exit_code == 0


def test_44t_invocation_pilot_json_has_required_top_level_keys(capsys) -> None:
    main(["invocation-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "pilot_lifecycle" in data
    assert "pilot_request_model" in data
    assert "safety_gates" in data
    assert "result_capture" in data
    assert "pilot_scope" in data
    assert "governance_rules" in data
    assert "future_evolution" in data
    assert "advisory" in data


def test_44t_invocation_pilot_lifecycle_has_required_stages(capsys) -> None:
    main(["invocation-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    lifecycle = data["pilot_lifecycle"]
    assert len(lifecycle) == 7
    combined = " ".join(lifecycle)
    assert "request" in combined
    assert "safety_validation" in combined
    assert "adapter_resolution" in combined
    assert "invocation_preparation" in combined
    assert "result_capture" in combined
    assert "human_review" in combined


def test_44t_invocation_pilot_lifecycle_ordered_correctly(capsys) -> None:
    main(["invocation-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    lifecycle = data["pilot_lifecycle"]
    assert lifecycle[0] == "request"
    assert lifecycle[-1] == "human_review"
    result_idx = next(i for i, s in enumerate(lifecycle) if "result_capture" in s)
    review_idx = lifecycle.index("human_review")
    assert result_idx < review_idx


def test_44t_invocation_pilot_request_model_fields(capsys) -> None:
    main(["invocation-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    req = data["pilot_request_model"]
    for field in ("pilot_id", "runtime_id", "agent_id", "objective",
                  "timeout_seconds", "writable_allowed", "governance_mode"):
        assert field in req["fields"]
        assert field in req


def test_44t_invocation_pilot_request_model_defaults(capsys) -> None:
    main(["invocation-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    req = data["pilot_request_model"]
    assert req["runtime_id"] == "codex-local"
    assert req["writable_allowed"] is False
    assert req["governance_mode"] == "read_only"
    assert isinstance(req["timeout_seconds"], int)
    assert req["timeout_seconds"] > 0


def test_44t_invocation_pilot_safety_gates_defined(capsys) -> None:
    main(["invocation-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    gates = data["safety_gates"]
    assert len(gates) == 5
    combined = " ".join(gates).lower()
    assert "runtime available" in combined
    assert "read-only" in combined
    assert "capability" in combined
    assert "governance" in combined
    assert "timeout" in combined


def test_44t_invocation_pilot_result_capture_fields(capsys) -> None:
    main(["invocation-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    fields = data["result_capture"]["fields"]
    for expected in ("status", "stdout_summary", "stderr_summary", "artifacts", "timestamps"):
        assert expected in fields


def test_44t_invocation_pilot_scope_enforces_restrictions(capsys) -> None:
    main(["invocation-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    scope = data["pilot_scope"]
    for restriction in (
        "single_runtime_only",
        "read_only_only",
        "no_writable_execution",
        "no_file_modification",
        "no_subagents",
        "no_swarm",
        "no_consensus_execution",
        "no_commit",
        "no_push",
        "no_rollback",
    ):
        assert restriction in scope


def test_44t_invocation_pilot_governance_rules_defined(capsys) -> None:
    main(["invocation-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_rules"]
    assert "pilot_may" in gov
    assert "pilot_may_not" in gov
    may = " ".join(gov["pilot_may"]).lower()
    may_not = " ".join(gov["pilot_may_not"]).lower()
    assert "prepare invocation" in may
    assert "resolve adapter" in may
    assert "capture results" in may
    assert "modify files" in may_not
    assert "commit" in may_not
    assert "push" in may_not
    assert "rollback" in may_not
    assert "bypass governance" in may_not


def test_44t_invocation_pilot_advisory_is_correct(capsys) -> None:
    main(["invocation-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "design only" in data["advisory"].lower()
    assert "no runtime execution" in data["advisory"].lower()


def test_44t_invocation_pilot_future_evolution_defined(capsys) -> None:
    main(["invocation-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44U" in phases
    assert "44V" in phases
    assert "45A" in phases


def test_44t_invocation_pilot_human_output_shows_sections_and_advisory(capsys) -> None:
    main(["invocation-pilot"])
    output = capsys.readouterr().out
    assert "Controlled runtime invocation pilot" in output
    assert "Pilot lifecycle" in output
    assert "Safety gates" in output
    assert "Result capture" in output
    assert "Pilot scope" in output
    assert "Governance" in output
    assert "Invocation pilot is a design only" in output


# ---------------------------------------------------------------------------
# Phase 44U: Multi-Agent Runtime Pilot
# ---------------------------------------------------------------------------


def test_44u_multi_runtime_pilot_command_exits_zero(capsys) -> None:
    exit_code = main(["multi-runtime-pilot"])
    assert exit_code == 0


def test_44u_multi_runtime_pilot_json_exits_zero(capsys) -> None:
    exit_code = main(["multi-runtime-pilot", "--json"])
    assert exit_code == 0


def test_44u_multi_runtime_pilot_json_has_required_top_level_keys(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "runtime_selection" in data
    assert "execution_plan" in data
    assert "invocation_previews" in data
    assert "result_capture_plan" in data
    assert "consensus_preparation" in data
    assert "governance_rules" in data
    assert "advisory" in data


def test_44u_multi_runtime_pilot_selects_default_runtimes(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    rs = data["runtime_selection"]
    selected = rs["selected_runtimes"]
    assert "codex-local" in selected
    assert "claude-local" in selected
    assert "kimi-local" in selected
    assert len(selected) == 3


def test_44u_multi_runtime_pilot_runtime_selection_fields(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    rs = data["runtime_selection"]
    assert "selected_runtimes" in rs
    assert "selected_agents" in rs
    assert "capability_summary" in rs
    for rid in rs["selected_runtimes"]:
        assert rid in rs["selected_agents"]
        assert rid in rs["capability_summary"]
        assert len(rs["capability_summary"][rid]) >= 1


def test_44u_multi_runtime_pilot_execution_plan_fields(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    plan = data["execution_plan"]
    assert "pilot_id" in plan
    assert "orchestration_strategy" in plan
    assert "supported_strategies" in plan
    assert "participating_runtimes" in plan
    assert "participating_agents" in plan
    assert "timeout_seconds" in plan
    assert "writable_allowed" in plan


def test_44u_multi_runtime_pilot_execution_plan_defaults(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    plan = data["execution_plan"]
    assert plan["orchestration_strategy"] == "parallel_review"
    assert plan["orchestration_strategy"] in plan["supported_strategies"]
    assert plan["writable_allowed"] is False
    assert isinstance(plan["timeout_seconds"], int)
    assert plan["timeout_seconds"] > 0


def test_44u_multi_runtime_pilot_supported_strategies(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    strategies = data["execution_plan"]["supported_strategies"]
    for strategy in ("sequential", "parallel_review", "parallel_planning", "consensus_preparation"):
        assert strategy in strategies


def test_44u_multi_runtime_pilot_invocation_previews_per_runtime(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    previews = data["invocation_previews"]
    assert len(previews) == 3
    for inv in previews:
        assert "runtime_id" in inv
        assert "adapter_id" in inv
        assert "invocation_preview" in inv
        assert "timeout_seconds" in inv
        assert "writable_allowed" in inv
        assert inv["writable_allowed"] is False


def test_44u_multi_runtime_pilot_invocation_previews_match_selected(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    selected = set(data["runtime_selection"]["selected_runtimes"])
    preview_ids = {inv["runtime_id"] for inv in data["invocation_previews"]}
    assert preview_ids == selected


def test_44u_multi_runtime_pilot_result_capture_plan_fields(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    rcp = data["result_capture_plan"]
    assert "expected_artifacts" in rcp
    assert "expected_recommendations" in rcp
    assert "expected_confidence" in rcp
    assert "expected_metadata" in rcp
    assert len(rcp["expected_artifacts"]) >= 1
    assert len(rcp["expected_recommendations"]) >= 1
    assert len(rcp["expected_metadata"]) >= 1


def test_44u_multi_runtime_pilot_consensus_preparation(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    cp = data["consensus_preparation"]
    assert "consensus_inputs" in cp
    assert "agreement_candidates" in cp
    assert "conflict_candidates" in cp
    assert len(cp["consensus_inputs"]) >= 1
    combined = " ".join(cp["consensus_inputs"]).lower()
    assert "recommendation" in combined
    assert "confidence" in combined


def test_44u_multi_runtime_pilot_governance_rules(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_rules"]
    assert "pilot_may" in gov
    assert "pilot_may_not" in gov
    may = " ".join(gov["pilot_may"]).lower()
    may_not = " ".join(gov["pilot_may_not"]).lower()
    assert "select runtimes" in may
    assert "invoke runtimes" in may_not
    assert "submit prompts" in may_not
    assert "modify files" in may_not
    assert "commit" in may_not
    assert "push" in may_not
    assert "rollback" in may_not
    assert "bypass governance" in may_not


def test_44u_multi_runtime_pilot_advisory_is_correct(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "read-only" in data["advisory"].lower()
    assert "no runtimes are invoked" in data["advisory"].lower()


def test_44u_multi_runtime_pilot_future_evolution_defined(capsys) -> None:
    main(["multi-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44V" in phases
    assert "44W" in phases
    assert "45A" in phases


def test_44u_multi_runtime_pilot_human_output_shows_sections_and_advisory(capsys) -> None:
    main(["multi-runtime-pilot"])
    output = capsys.readouterr().out
    assert "Multi-runtime pilot" in output
    assert "codex-local" in output
    assert "claude-local" in output
    assert "kimi-local" in output
    assert "Invocation previews" in output
    assert "Result capture plan" in output
    assert "Consensus preparation" in output
    assert "Governance" in output
    assert "Multi-runtime pilot is read-only" in output

# Phase 44V: Consensus Runtime Pilot
# ---------------------------------------------------------------------------


def test_44v_consensus_runtime_pilot_command_exits_zero(capsys) -> None:
    exit_code = main(["consensus-runtime-pilot"])
    assert exit_code == 0


def test_44v_consensus_runtime_pilot_json_exits_zero(capsys) -> None:
    exit_code = main(["consensus-runtime-pilot", "--json"])
    assert exit_code == 0


def test_44v_consensus_runtime_pilot_json_has_required_top_level_keys(capsys) -> None:
    main(["consensus-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "pilot_id" in data
    assert "runtime_outputs" in data
    assert "result_collection" in data
    assert "agreement_analysis" in data
    assert "conflict_analysis" in data
    assert "recommendation_preview" in data
    assert "governance_rules" in data
    assert "advisory" in data


def test_44v_consensus_runtime_pilot_simulated_outputs_present(capsys) -> None:
    main(["consensus-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    outputs = data["runtime_outputs"]
    runtime_ids = [o["runtime_id"] for o in outputs]
    assert "codex-local" in runtime_ids
    assert "claude-local" in runtime_ids
    assert "kimi-local" in runtime_ids
    assert len(outputs) == 3


def test_44v_consensus_runtime_pilot_output_fields(capsys) -> None:
    main(["consensus-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    for out in data["runtime_outputs"]:
        assert "runtime_id" in out
        assert "recommendation" in out
        assert "confidence" in out
        assert "rationale" in out
        assert "artifact_summary" in out
        assert isinstance(out["confidence"], float)
        assert 0.0 <= out["confidence"] <= 1.0


def test_44v_consensus_runtime_pilot_result_collection_fields(capsys) -> None:
    main(["consensus-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    rc = data["result_collection"]
    assert "collected_outputs" in rc
    assert "output_metadata" in rc
    assert "runtime_summary" in rc
    assert rc["output_metadata"]["collection_mode"] == "simulated"
    assert rc["output_metadata"]["writable_allowed"] is False


def test_44v_consensus_runtime_pilot_agreement_analysis(capsys) -> None:
    main(["consensus-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    ag = data["agreement_analysis"]
    assert "matching_recommendations" in ag
    assert "matching_recommendation" in ag
    assert "supporting_evidence" in ag
    assert len(ag["matching_recommendations"]) >= 1
    assert len(ag["supporting_evidence"]) >= 1
    assert ag["matching_recommendation"] == "approve"


def test_44v_consensus_runtime_pilot_conflict_analysis(capsys) -> None:
    main(["consensus-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    cf = data["conflict_analysis"]
    assert "conflicting_recommendations" in cf
    assert "confidence_differences" in cf
    assert "missing_evidence" in cf
    assert len(cf["conflicting_recommendations"]) >= 1
    cdiff = cf["confidence_differences"]
    assert "confidence_spread" in cdiff
    assert cdiff["confidence_spread"] > 0.0


def test_44v_consensus_runtime_pilot_recommendation_preview(capsys) -> None:
    main(["consensus-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    rp = data["recommendation_preview"]
    assert "consensus_recommendation" in rp
    assert "basis" in rp
    assert "valid_outcomes" in rp
    assert "human_review_required" in rp
    assert "human_review_reason" in rp
    assert rp["human_review_required"] is True
    assert rp["consensus_recommendation"] in rp["valid_outcomes"]


def test_44v_consensus_runtime_pilot_valid_outcomes(capsys) -> None:
    main(["consensus-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    outcomes = data["recommendation_preview"]["valid_outcomes"]
    for expected in ("approve", "reject", "request_changes", "inconclusive", "escalate_to_human"):
        assert expected in outcomes


def test_44v_consensus_runtime_pilot_governance_rules(capsys) -> None:
    main(["consensus-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_rules"]
    assert "pilot_may" in gov
    assert "pilot_may_not" in gov
    may = " ".join(gov["pilot_may"]).lower()
    may_not = " ".join(gov["pilot_may_not"]).lower()
    assert "collect outputs" in may
    assert "analyze agreements" in may
    assert "analyze conflicts" in may
    assert "invoke runtimes" in may_not
    assert "submit prompts" in may_not
    assert "modify files" in may_not
    assert "commit" in may_not
    assert "push" in may_not
    assert "rollback" in may_not


def test_44v_consensus_runtime_pilot_advisory_is_correct(capsys) -> None:
    main(["consensus-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "simulated" in data["advisory"].lower()
    assert "no runtimes are invoked" in data["advisory"].lower()


def test_44v_consensus_runtime_pilot_future_evolution_defined(capsys) -> None:
    main(["consensus-runtime-pilot", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44W" in phases
    assert "44X" in phases
    assert "45A" in phases


def test_44v_consensus_runtime_pilot_human_output_shows_sections_and_advisory(capsys) -> None:
    main(["consensus-runtime-pilot"])
    output = capsys.readouterr().out
    assert "Consensus runtime pilot" in output
    assert "codex-local" in output
    assert "claude-local" in output
    assert "kimi-local" in output
    assert "Agreement analysis" in output
    assert "Conflict analysis" in output
    assert "Recommendation preview" in output
    assert "Governance" in output
    assert "Consensus runtime pilot is simulated" in output

# Phase 44W: Governed Execution Dry-Run
# ---------------------------------------------------------------------------


def test_44w_governed_execution_dry_run_command_exits_zero(capsys) -> None:
    exit_code = main(["governed-execution-dry-run"])
    assert exit_code == 0


def test_44w_governed_execution_dry_run_json_exits_zero(capsys) -> None:
    exit_code = main(["governed-execution-dry-run", "--json"])
    assert exit_code == 0


def test_44w_governed_execution_dry_run_json_has_required_top_level_keys(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    for key in (
        "dry_run_id",
        "lifecycle",
        "objective_intake",
        "capability_discovery",
        "runtime_selection",
        "invocation_plan",
        "simulated_result_plan",
        "consensus_handoff",
        "governance_checkpoints",
        "blockers",
        "governance_rules",
        "advisory",
    ):
        assert key in data, f"missing key: {key}"


def test_44w_governed_execution_dry_run_lifecycle_has_eight_stages(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    lifecycle = data["lifecycle"]
    assert len(lifecycle) == 8
    names = [s["name"] for s in lifecycle]
    for expected in (
        "objective_intake",
        "capability_discovery",
        "runtime_selection",
        "invocation_planning",
        "simulated_result_capture",
        "consensus_preparation",
        "governance_decision_point",
        "human_review",
    ):
        assert expected in names


def test_44w_governed_execution_dry_run_objective_intake(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    obj = data["objective_intake"]
    assert "objective_id" in obj
    assert "requested_capabilities" in obj
    assert "governance_mode" in obj
    assert "writable_allowed" in obj
    assert obj["writable_allowed"] is False
    assert obj["governance_mode"] == "read_only"
    assert len(obj["requested_capabilities"]) >= 1


def test_44w_governed_execution_dry_run_capability_discovery(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    cap = data["capability_discovery"]
    assert "requested_capabilities" in cap
    assert "discovered_runtimes" in cap
    assert "coverage" in cap
    assert "unmet_capabilities" in cap
    assert cap["coverage"] == "full"
    assert cap["unmet_capabilities"] == []
    for capability in cap["requested_capabilities"]:
        assert capability in cap["discovered_runtimes"]


def test_44w_governed_execution_dry_run_runtime_selection(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    rs = data["runtime_selection"]
    assert "selected_runtimes" in rs
    assert "selection_basis" in rs
    assert len(rs["selected_runtimes"]) >= 1
    for rid in ("codex-local", "claude-local", "kimi-local"):
        assert rid in rs["selected_runtimes"]


def test_44w_governed_execution_dry_run_invocation_plan_fields(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    plan = data["invocation_plan"]
    assert len(plan) >= 1
    for step in plan:
        assert "step" in step
        assert "runtime_id" in step
        assert "capability" in step
        assert "governance_checkpoint" in step
        assert "writable_allowed" in step
        assert step["writable_allowed"] is False


def test_44w_governed_execution_dry_run_simulated_result_plan(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    srp = data["simulated_result_plan"]
    assert "collection_mode" in srp
    assert "expected_fields" in srp
    assert "simulated_outcomes" in srp
    assert "writable_allowed" in srp
    assert srp["collection_mode"] == "simulated"
    assert srp["writable_allowed"] is False
    assert len(srp["simulated_outcomes"]) >= 1
    for outcome in srp["simulated_outcomes"]:
        assert "runtime_id" in outcome
        assert "status" in outcome
        assert "confidence" in outcome


def test_44w_governed_execution_dry_run_consensus_handoff(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    ch = data["consensus_handoff"]
    assert "inputs_prepared" in ch
    assert "human_review_required" in ch
    assert "conflict_escalation" in ch
    assert ch["human_review_required"] is True
    assert len(ch["inputs_prepared"]) >= 1
    combined = " ".join(ch["inputs_prepared"]).lower()
    assert "recommendation" in combined
    assert "confidence" in combined


def test_44w_governed_execution_dry_run_governance_checkpoints(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    checkpoints = data["governance_checkpoints"]
    assert len(checkpoints) >= 3
    names = [cp["checkpoint"] for cp in checkpoints]
    assert "objective_intake" in names
    assert "pre_invocation_safety_gate" in names
    assert "human_review" in names
    for cp in checkpoints:
        assert "description" in cp
        assert "required" in cp
        assert cp["required"] is True


def test_44w_governed_execution_dry_run_blockers_present(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    blockers = data["blockers"]
    assert len(blockers) >= 1
    combined = " ".join(blockers).lower()
    assert "no_runtime_invocation" in combined
    assert "no_file_modification" in combined


def test_44w_governed_execution_dry_run_governance_rules(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_rules"]
    assert "dry_run_may" in gov
    assert "dry_run_may_not" in gov
    may = " ".join(gov["dry_run_may"]).lower()
    may_not = " ".join(gov["dry_run_may_not"]).lower()
    assert "intake objective" in may
    assert "invoke runtimes" in may_not
    assert "submit prompts" in may_not
    assert "modify files" in may_not
    assert "commit" in may_not
    assert "push" in may_not
    assert "rollback" in may_not


def test_44w_governed_execution_dry_run_advisory(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "simulated" in data["advisory"].lower()
    assert "no runtimes are invoked" in data["advisory"].lower()


def test_44w_governed_execution_dry_run_future_evolution(capsys) -> None:
    main(["governed-execution-dry-run", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "44X" in phases
    assert "45A" in phases


def test_44w_governed_execution_dry_run_human_output_shows_sections(capsys) -> None:
    main(["governed-execution-dry-run"])
    output = capsys.readouterr().out
    assert "Governed execution dry-run" in output
    assert "Lifecycle" in output
    assert "Objective intake" in output
    assert "Capability discovery" in output
    assert "Invocation plan" in output
    assert "Simulated result plan" in output
    assert "Consensus handoff" in output
    assert "Governance checkpoints" in output
    assert "Blockers" in output
    assert "Governance" in output
    assert "Governed execution dry-run is simulated" in output

# Phase 44X: Runtime Invocation Validation
# ---------------------------------------------------------------------------


def test_44x_invocation_contracts_command_exits_zero(capsys) -> None:
    exit_code = main(["invocation-contracts"])
    assert exit_code == 0


def test_44x_invocation_contracts_json_exits_zero(capsys) -> None:
    exit_code = main(["invocation-contracts", "--json"])
    assert exit_code == 0


def test_44x_invocation_contracts_json_has_required_top_level_keys(capsys) -> None:
    main(["invocation-contracts", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "invocation_contracts" in data
    assert "invalid_preview_contracts" in data
    assert "advisory" in data


def test_44x_invocation_contracts_codex_validated(capsys) -> None:
    main(["invocation-contracts", "--json"])
    data = json.loads(capsys.readouterr().out)
    contracts = {c["runtime_id"]: c for c in data["invocation_contracts"]}
    assert "codex-local" in contracts
    codex = contracts["codex-local"]
    assert codex["status"] == "validated"
    assert "read_only" in codex and "writable" in codex
    assert codex["read_only"]["writable_allowed"] is False
    assert codex["writable"]["writable_allowed"] is True
    assert "codex exec" in codex["read_only"]["command"]
    assert "read-only" in codex["read_only"]["command"]
    assert "workspace-write" in codex["writable"]["command"]


def test_44x_invocation_contracts_claude_validated(capsys) -> None:
    main(["invocation-contracts", "--json"])
    data = json.loads(capsys.readouterr().out)
    contracts = {c["runtime_id"]: c for c in data["invocation_contracts"]}
    assert "claude-local" in contracts
    claude = contracts["claude-local"]
    assert claude["status"] == "validated"
    assert claude["read_only"]["writable_allowed"] is False
    assert claude["writable"]["writable_allowed"] is True
    assert "claude -p" in claude["read_only"]["command"]
    assert "acceptEdits" in claude["writable"]["command"]


def test_44x_invocation_contracts_kimi_validated(capsys) -> None:
    main(["invocation-contracts", "--json"])
    data = json.loads(capsys.readouterr().out)
    contracts = {c["runtime_id"]: c for c in data["invocation_contracts"]}
    assert "kimi-local" in contracts
    kimi = contracts["kimi-local"]
    assert kimi["status"] == "validated"
    assert kimi["read_only"]["writable_allowed"] is False
    assert "kimi -p" in kimi["read_only"]["command"]


def test_44x_invocation_contracts_contract_fields(capsys) -> None:
    main(["invocation-contracts", "--json"])
    data = json.loads(capsys.readouterr().out)
    for contract in data["invocation_contracts"]:
        assert "runtime_id" in contract
        assert "status" in contract
        assert "read_only" in contract
        assert "writable" in contract
        for mode_key in ("read_only", "writable"):
            mode = contract[mode_key]
            assert "command" in mode
            assert "mode" in mode
            assert "writable_allowed" in mode


def test_44x_invocation_contracts_invalid_preview_all_three_runtimes(capsys) -> None:
    main(["invocation-contracts", "--json"])
    data = json.loads(capsys.readouterr().out)
    invalid = data["invalid_preview_contracts"]
    runtime_ids = [c["runtime_id"] for c in invalid]
    assert "codex-local" in runtime_ids
    assert "claude-local" in runtime_ids
    assert "kimi-local" in runtime_ids
    assert len(invalid) == 3


def test_44x_invocation_contracts_invalid_preview_fields(capsys) -> None:
    main(["invocation-contracts", "--json"])
    data = json.loads(capsys.readouterr().out)
    for inv in data["invalid_preview_contracts"]:
        assert inv["status"] == "invalid_preview_contract"
        assert inv["should_not_use_for_real_execution"] is True
        assert "reason" in inv
        assert "command" in inv
        assert "--non-interactive" in inv["command"]
        assert "--output-format json" in inv["command"]


def test_44x_invocation_contracts_governance_rules(capsys) -> None:
    main(["invocation-contracts", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_rules"]
    assert "validation_may" in gov
    assert "validation_may_not" in gov
    may = " ".join(gov["validation_may"]).lower()
    may_not = " ".join(gov["validation_may_not"]).lower()
    assert "validated invocation contracts" in may
    assert "invalid preview contracts" in may
    assert "invoke runtimes" in may_not
    assert "submit prompts" in may_not
    assert "modify files" in may_not
    assert "commit" in may_not
    assert "push" in may_not
    assert "rollback" in may_not


def test_44x_invocation_contracts_advisory(capsys) -> None:
    main(["invocation-contracts", "--json"])
    data = json.loads(capsys.readouterr().out)
    advisory = data["advisory"].lower()
    assert "validated references" in advisory
    assert "no runtimes are invoked" in advisory


def test_44x_invocation_contracts_future_evolution(capsys) -> None:
    main(["invocation-contracts", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "45A" in phases


def test_44x_invocation_contracts_human_output_shows_all_sections(capsys) -> None:
    main(["invocation-contracts"])
    output = capsys.readouterr().out
    assert "Invocation contract validation summary" in output
    assert "codex-local" in output
    assert "claude-local" in output
    assert "kimi-local" in output
    assert "read-only" in output
    assert "writable" in output
    assert "Invalid preview contracts" in output
    assert "invalid_preview_contract" in output
    assert "Governance" in output
    assert "Invocation contracts are validated references" in output

# Phase 44Y: Governed Runtime Execution Readiness Assessment
# ---------------------------------------------------------------------------


def test_44y_execution_readiness_command_exits_zero(capsys) -> None:
    exit_code = main(["execution-readiness"])
    assert exit_code == 0


def test_44y_execution_readiness_json_exits_zero(capsys) -> None:
    exit_code = main(["execution-readiness", "--json"])
    assert exit_code == 0


def test_44y_execution_readiness_json_has_required_top_level_keys(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    for key in ("readiness_summary", "subsystem_assessments", "gap_analysis", "recommendations", "advisory"):
        assert key in data, f"missing key: {key}"


def test_44y_execution_readiness_summary_fields(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    s = data["readiness_summary"]
    assert "assessment_id" in s
    assert "overall_status" in s
    assert "total_areas" in s
    assert "ready" in s
    assert "partially_ready" in s
    assert "not_ready" in s
    assert "execution_safe" in s
    assert "execution_safe_reason" in s
    assert s["execution_safe"] is False
    assert s["total_areas"] == s["ready"] + s["partially_ready"] + s["not_ready"]


def test_44y_execution_readiness_six_subsystem_areas(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    assessments = data["subsystem_assessments"]
    assert len(assessments) == 6
    areas = [a["area"] for a in assessments]
    for expected in (
        "capability_registry",
        "coordinator",
        "consensus",
        "runtime_adapters",
        "invocation_layer",
        "governance",
    ):
        assert expected in areas


def test_44y_execution_readiness_subsystem_statuses(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    by_area = {a["area"]: a["status"] for a in data["subsystem_assessments"]}
    assert by_area["capability_registry"] == "ready"
    assert by_area["governance"] == "ready"
    assert by_area["coordinator"] == "partially_ready"
    assert by_area["consensus"] == "partially_ready"
    assert by_area["runtime_adapters"] == "partially_ready"
    assert by_area["invocation_layer"] == "partially_ready"


def test_44y_execution_readiness_subsystem_evaluated_fields(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    for assessment in data["subsystem_assessments"]:
        assert "area" in assessment
        assert "status" in assessment
        assert "evaluated" in assessment
        assert len(assessment["evaluated"]) >= 1
        for ev in assessment["evaluated"]:
            assert "criterion" in ev
            assert "met" in ev
            assert "detail" in ev
            assert isinstance(ev["met"], bool)


def test_44y_execution_readiness_capability_registry_all_met(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    by_area = {a["area"]: a for a in data["subsystem_assessments"]}
    cap = by_area["capability_registry"]
    criteria = [e["criterion"] for e in cap["evaluated"]]
    assert "discovery_support" in criteria
    assert "validation_support" in criteria
    assert "classification_support" in criteria
    assert all(e["met"] for e in cap["evaluated"])


def test_44y_execution_readiness_partially_ready_have_unmet_criteria(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    for assessment in data["subsystem_assessments"]:
        if assessment["status"] == "partially_ready":
            unmet = [e for e in assessment["evaluated"] if not e["met"]]
            assert len(unmet) >= 1, f"{assessment['area']} is partially_ready but has no unmet criteria"


def test_44y_execution_readiness_gap_analysis_fields(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    gap = data["gap_analysis"]
    assert "missing_implementations" in gap
    assert "missing_validations" in gap
    assert "missing_runtime_integrations" in gap
    assert len(gap["missing_implementations"]) >= 1
    assert len(gap["missing_validations"]) >= 1
    assert len(gap["missing_runtime_integrations"]) >= 1


def test_44y_execution_readiness_gap_covers_all_runtimes(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    integrations = " ".join(data["gap_analysis"]["missing_runtime_integrations"]).lower()
    assert "codex-local" in integrations
    assert "claude-local" in integrations
    assert "kimi-local" in integrations


def test_44y_execution_readiness_recommendations_present(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    recs = data["recommendations"]
    assert len(recs) >= 1
    combined = " ".join(recs).lower()
    assert "adapter" in combined


def test_44y_execution_readiness_advisory(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    advisory = data["advisory"].lower()
    assert "informational" in advisory
    assert "no runtimes are invoked" in advisory


def test_44y_execution_readiness_future_evolution(capsys) -> None:
    main(["execution-readiness", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "45A" in phases


def test_44y_execution_readiness_human_output_shows_all_sections(capsys) -> None:
    main(["execution-readiness"])
    output = capsys.readouterr().out
    assert "Execution readiness assessment" in output
    assert "Subsystem readiness" in output
    assert "capability_registry" in output
    assert "coordinator" in output
    assert "consensus" in output
    assert "runtime_adapters" in output
    assert "invocation_layer" in output
    assert "governance" in output
    assert "Gap analysis" in output
    assert "Recommended next steps" in output
    assert "Execution readiness assessment is informational" in output

# Phase 44Z: Runtime Adapter Registry Design
# ---------------------------------------------------------------------------


def test_44z_adapter_registry_design_command_exits_zero(capsys) -> None:
    exit_code = main(["adapter-registry-design"])
    assert exit_code == 0


def test_44z_adapter_registry_design_json_exits_zero(capsys) -> None:
    exit_code = main(["adapter-registry-design", "--json"])
    assert exit_code == 0


def test_44z_adapter_registry_design_json_has_required_top_level_keys(capsys) -> None:
    main(["adapter-registry-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    for key in (
        "registry_responsibilities",
        "adapter_registration_model",
        "adapter_resolution",
        "health_model",
        "capability_synchronization",
        "governance_rules",
        "advisory",
    ):
        assert key in data, f"missing key: {key}"


def test_44z_adapter_registry_design_registry_responsibilities(capsys) -> None:
    main(["adapter-registry-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    responsibilities = data["registry_responsibilities"]
    for expected in (
        "register_adapter",
        "unregister_adapter",
        "discover_adapters",
        "resolve_adapter",
        "report_health",
        "report_capabilities",
    ):
        assert expected in responsibilities


def test_44z_adapter_registry_design_registration_model_fields(capsys) -> None:
    main(["adapter-registry-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    model = data["adapter_registration_model"]
    field_names = [f["field"] for f in model]
    for expected in (
        "runtime_id",
        "adapter_id",
        "version",
        "lifecycle_status",
        "supported_capabilities",
        "writable_supported",
        "subagent_supported",
        "swarm_supported",
    ):
        assert expected in field_names
    for field in model:
        assert "field" in field
        assert "type" in field
        assert "description" in field


def test_44z_adapter_registry_design_adapter_resolution_structure(capsys) -> None:
    main(["adapter-registry-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    res = data["adapter_resolution"]
    assert "input" in res
    assert "output" in res
    assert "resolution_steps" in res
    assert "fallback" in res
    assert "runtime_id" in res["input"]
    assert "adapter_id" in res["output"]
    assert "health_status" in res["output"]
    assert "capabilities" in res["output"]
    assert len(res["resolution_steps"]) >= 1


def test_44z_adapter_registry_design_health_model_states(capsys) -> None:
    main(["adapter-registry-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    hm = data["health_model"]
    assert "states" in hm
    assert "state_descriptions" in hm
    for state in ("available", "degraded", "unavailable", "unknown"):
        assert state in hm["states"]
        assert state in hm["state_descriptions"]


def test_44z_adapter_registry_design_capability_synchronization(capsys) -> None:
    main(["adapter-registry-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    cs = data["capability_synchronization"]
    assert "registry_may_receive" in cs
    assert "source_of_truth" in cs
    assert cs["source_of_truth"] == "capability_registry"
    for item in ("runtime discovery", "capability discovery", "version discovery"):
        assert item in cs["registry_may_receive"]


def test_44z_adapter_registry_design_governance_rules(capsys) -> None:
    main(["adapter-registry-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_rules"]
    assert "registry_may" in gov
    assert "registry_may_not" in gov
    may = " ".join(gov["registry_may"]).lower()
    may_not = " ".join(gov["registry_may_not"]).lower()
    assert "discover adapters" in may
    assert "resolve adapters" in may
    assert "report capabilities" in may
    assert "invoke runtimes" in may_not
    assert "approve actions" in may_not
    assert "commit" in may_not
    assert "push" in may_not
    assert "rollback" in may_not


def test_44z_adapter_registry_design_advisory(capsys) -> None:
    main(["adapter-registry-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    advisory = data["advisory"].lower()
    assert "read-only" in advisory
    assert "no adapters are implemented" in advisory


def test_44z_adapter_registry_design_future_evolution(capsys) -> None:
    main(["adapter-registry-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "45A" in phases
    assert "45B" in phases
    assert "45C" in phases


def test_44z_adapter_registry_design_human_output_shows_all_sections(capsys) -> None:
    main(["adapter-registry-design"])
    output = capsys.readouterr().out
    assert "Runtime adapter registry design" in output
    assert "Registry responsibilities" in output
    assert "register_adapter" in output
    assert "Adapter registration model" in output
    assert "writable_supported" in output
    assert "Adapter resolution" in output
    assert "Health model" in output
    assert "available" in output
    assert "Capability synchronization" in output
    assert "capability_registry" in output
    assert "Governance" in output
    assert "Adapter registry design is read-only" in output


# Phase 45A: Autonomous Roadmap Generation Design
# ---------------------------------------------------------------------------


def test_45a_roadmap_generation_design_command_exits_zero(capsys) -> None:
    exit_code = main(["roadmap-generation-design"])
    assert exit_code == 0


def test_45a_roadmap_generation_design_json_exits_zero(capsys) -> None:
    exit_code = main(["roadmap-generation-design", "--json"])
    assert exit_code == 0


def test_45a_roadmap_generation_design_json_has_required_top_level_keys(capsys) -> None:
    main(["roadmap-generation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    for key in (
        "evidence_sources",
        "agent_roles",
        "lifecycle",
        "proposal_model",
        "governance_rules",
        "future_evolution",
        "advisory",
    ):
        assert key in data, f"missing key: {key}"


def test_45a_roadmap_generation_design_evidence_sources(capsys) -> None:
    main(["roadmap-generation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    sources = data["evidence_sources"]
    for expected in (
        "PROJECT_STATUS.md",
        "CHANGELOG.md",
        "tasks/TODO.md",
        "tasks/DONE.md",
        "tests",
        "capability registry",
        "execution/readiness assessments",
        "governance history",
    ):
        assert expected in sources, f"missing evidence source: {expected}"


def test_45a_roadmap_generation_design_agent_roles(capsys) -> None:
    main(["roadmap-generation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    roles = data["agent_roles"]
    role_names = [r["role"] for r in roles]
    for expected in (
        "repository_analyst",
        "architecture_analyst",
        "test_analyst",
        "governance_analyst",
        "capability_analyst",
        "planning_coordinator",
    ):
        assert expected in role_names, f"missing agent role: {expected}"
    for role in roles:
        assert "role" in role
        assert "responsibility" in role
        assert len(role["responsibility"]) > 0


def test_45a_roadmap_generation_design_lifecycle_steps(capsys) -> None:
    main(["roadmap-generation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    lifecycle = data["lifecycle"]
    for expected in (
        "evidence_collection",
        "gap_analysis",
        "candidate_phase_generation",
        "dependency_ordering",
        "risk_assessment",
        "consensus_review",
        "human_approval",
    ):
        assert expected in lifecycle, f"missing lifecycle step: {expected}"


def test_45a_roadmap_generation_design_proposal_model_fields(capsys) -> None:
    main(["roadmap-generation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    model = data["proposal_model"]
    field_names = [f["field"] for f in model]
    for expected in (
        "proposal_id",
        "generated_at",
        "evidence_sources",
        "candidate_phases",
        "dependencies",
        "risks",
        "assumptions",
        "confidence",
        "human_decision_required",
    ):
        assert expected in field_names, f"missing proposal model field: {expected}"
    for field in model:
        assert "field" in field
        assert "type" in field
        assert "description" in field


def test_45a_roadmap_generation_design_proposal_model_human_decision_required(capsys) -> None:
    main(["roadmap-generation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    model = data["proposal_model"]
    hdr = next(f for f in model if f["field"] == "human_decision_required")
    assert hdr["type"] == "bool"
    assert "always true" in hdr["description"].lower()


def test_45a_roadmap_generation_design_governance_rules_may(capsys) -> None:
    main(["roadmap-generation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_rules"]
    assert "proposal_may" in gov
    may = " ".join(gov["proposal_may"]).lower()
    assert "describe candidate phases" in may
    assert "summarize evidence" in may
    assert "report confidence" in may


def test_45a_roadmap_generation_design_governance_rules_may_not(capsys) -> None:
    main(["roadmap-generation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_rules"]
    assert "proposal_may_not" in gov
    may_not = " ".join(gov["proposal_may_not"]).lower()
    assert "mutate roadmap" in may_not
    assert "create tasks" in may_not
    assert "commit" in may_not
    assert "push" in may_not
    assert "approve itself" in may_not


def test_45a_roadmap_generation_design_governance_human_approval_required(capsys) -> None:
    main(["roadmap-generation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    gov = data["governance_rules"]
    assert gov["human_approval_required"] is True
    assert gov["advisory"] is True


def test_45a_roadmap_generation_design_advisory(capsys) -> None:
    main(["roadmap-generation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    advisory = data["advisory"].lower()
    assert "read-only" in advisory
    assert "no roadmap proposals are generated or mutated" in advisory


def test_45a_roadmap_generation_design_future_evolution(capsys) -> None:
    main(["roadmap-generation-design", "--json"])
    data = json.loads(capsys.readouterr().out)
    phases = [e["phase"] for e in data["future_evolution"]]
    assert "45B" in phases
    assert "45C" in phases
    assert "45D" in phases
    assert "45E" in phases


def test_45a_roadmap_generation_design_human_output_shows_all_sections(capsys) -> None:
    main(["roadmap-generation-design"])
    output = capsys.readouterr().out
    assert "Autonomous roadmap generation design" in output
    assert "Evidence sources" in output
    assert "PROJECT_STATUS.md" in output
    assert "governance history" in output
    assert "Roadmap agent roles" in output
    assert "repository_analyst" in output
    assert "planning_coordinator" in output
    assert "Roadmap generation lifecycle" in output
    assert "evidence_collection" in output
    assert "human_approval" in output
    assert "Roadmap proposal model" in output
    assert "human_decision_required" in output
    assert "Governance rules" in output
    assert "mutate roadmap" in output
    assert "Future evolution" in output
    assert "45B" in output
    assert "Roadmap generation design is read-only" in output
