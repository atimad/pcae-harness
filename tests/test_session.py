from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.session import (
    SessionUpdate,
    read_session_snapshot,
    update_session_snapshot,
    write_session_snapshot,
)
from pcae.core.tasks import create_task_contract


def test_session_write_creates_readable_snapshot(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Write handoff snapshot",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )
    write_file(tmp_path / "src" / "changed.py", "print('changed')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "changed.py", "print('changed again')\n")

    snapshot = write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )

    session_file = tmp_path / ".pcae" / "session.json"
    assert snapshot.relative_path == Path(".pcae/session.json")
    assert session_file.is_file()

    data = json.loads(session_file.read_text(encoding="utf-8"))
    assert data["timestamp"] == "2026-05-23T08:00:00+00:00"
    assert data["active_task"] == {
        "id": "20260523-0730-write-handoff-snapshot",
        "title": "Write handoff snapshot",
    }
    assert data["git"]["branch"] in {"main", "master"}
    assert data["git"]["status_summary"] == "1 changed file"
    assert data["git"]["changed_files"] == [
        {"path": "src/changed.py", "status": " M"}
    ]
    assert data["current_objective"] == ""
    assert data["last_completed_step"] == ""
    assert data["next_recommended_step"] == ""
    assert data["blockers"] == []
    assert data["warnings"] == []
    assert data["architectural_notes"] == []


def test_session_write_works_without_active_task(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)

    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )

    data = json.loads((tmp_path / ".pcae" / "session.json").read_text(encoding="utf-8"))
    assert data["active_task"] is None


def test_session_write_command_reports_output(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "write"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Wrote session snapshot: .pcae/session.json" in output
    assert (tmp_path / ".pcae" / "session.json").is_file()


def test_session_write_does_not_overwrite_policy_config(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    policy_file = tmp_path / ".pcae" / "policy.toml"
    before = policy_file.read_text(encoding="utf-8")

    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )

    assert policy_file.read_text(encoding="utf-8") == before


def test_session_update_replaces_and_appends_fields(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )

    snapshot = update_session_snapshot(
        HarnessPath(tmp_path),
        SessionUpdate(
            objective="Implement session update",
            completed_step="Added core updater",
            next_step="Run checks",
            blocker="None",
            warning="Keep policy untouched",
            note="Preserve git fields",
        ),
    )

    assert snapshot.data["current_objective"] == "Implement session update"
    assert snapshot.data["last_completed_step"] == "Added core updater"
    assert snapshot.data["next_recommended_step"] == "Run checks"
    assert snapshot.data["blockers"] == ["None"]
    assert snapshot.data["warnings"] == ["Keep policy untouched"]
    assert snapshot.data["architectural_notes"] == ["Preserve git fields"]
    assert snapshot.data["git"]["branch"] in {"main", "master"}


def test_session_update_creates_snapshot_when_missing(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Update handoff",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )

    snapshot = update_session_snapshot(
        HarnessPath(tmp_path),
        SessionUpdate(objective="Create on update"),
    )

    assert (tmp_path / ".pcae" / "session.json").is_file()
    assert snapshot.data["current_objective"] == "Create on update"
    assert snapshot.data["active_task"] == {
        "id": "20260523-0730-update-handoff",
        "title": "Update handoff",
    }


def test_session_update_does_not_overwrite_policy_config(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    policy_file = tmp_path / ".pcae" / "policy.toml"
    before = policy_file.read_text(encoding="utf-8")

    update_session_snapshot(
        HarnessPath(tmp_path),
        SessionUpdate(objective="Keep policy stable"),
    )

    assert policy_file.read_text(encoding="utf-8") == before


def test_session_read_loads_snapshot(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )

    snapshot = read_session_snapshot(HarnessPath(tmp_path))

    assert snapshot is not None
    assert snapshot.relative_path == Path(".pcae/session.json")
    assert snapshot.data["timestamp"] == "2026-05-23T08:00:00+00:00"


def test_session_read_returns_none_when_missing(tmp_path: Path) -> None:
    assert read_session_snapshot(HarnessPath(tmp_path)) is None


def test_session_read_command_prints_resume_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Resume work",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "read"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Session snapshot:" in output
    assert "Active task: 20260523-0730-resume-work" in output
    assert "Title: Resume work" in output
    assert "Git branch:" in output
    assert "Git status:" in output
    assert "Current objective:" in output
    assert "Last completed step:" in output
    assert "Next recommended step:" in output
    assert "Blockers:\n  none" in output
    assert "Warnings:\n  none" in output
    assert "Architectural notes:\n  none" in output


def test_session_read_command_prints_blockers_and_warnings(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    session_file = tmp_path / ".pcae" / "session.json"
    session_file.write_text(
        json.dumps(
            {
                "active_task": None,
                "architectural_notes": ["Keep parser simple"],
                "blockers": ["Need review"],
                "current_objective": "Finish session read",
                "git": {"status_summary": "clean"},
                "last_completed_step": "Added tests",
                "next_recommended_step": "Run checks",
                "warnings": ["Pending docs"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "read"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Active task: none" in output
    assert "Git branch: unknown" in output
    assert "Git status: clean" in output
    assert "Current objective: Finish session read" in output
    assert "Last completed step: Added tests" in output
    assert "Next recommended step: Run checks" in output
    assert "  - Need review" in output
    assert "  - Pending docs" in output
    assert "  - Keep parser simple" in output


def test_session_read_command_reports_missing_snapshot(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "read"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No session snapshot found at .pcae/session.json." in output


def test_session_update_command_updates_read_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    update_exit_code = main(
        [
            "session",
            "update",
            "--objective",
            "Finish Phase 8A",
            "--completed-step",
            "Added update command",
            "--next-step",
            "Run validation",
            "--blocker",
            "None",
            "--warning",
            "Watch docs",
            "--note",
            "Session JSON stays readable",
        ]
    )
    update_output = capsys.readouterr().out

    read_exit_code = main(["session", "read"])
    read_output = capsys.readouterr().out

    assert update_exit_code == 0
    assert "Updated session snapshot: .pcae/session.json" in update_output
    assert read_exit_code == 0
    assert "Current objective: Finish Phase 8A" in read_output
    assert "Last completed step: Added update command" in read_output
    assert "Next recommended step: Run validation" in read_output
    assert "  - None" in read_output
    assert "  - Watch docs" in read_output
    assert "  - Session JSON stays readable" in read_output


def test_session_end_stops_when_check_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "end"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Session end stopped: pcae check failed." in output
    assert "No active task contract found in tasks/active/." in output
    assert not (tmp_path / ".pcae" / "session.json").exists()
    assert not (tmp_path / ".pcae" / "architecture-history.json").exists()


def test_session_end_writes_snapshot_and_architecture_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "End session",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )
    task_file = tmp_path / "tasks" / "active" / "20260523-0730-end-session.md"
    task_file.write_text(
        task_file.read_text(encoding="utf-8").replace(
            "## Allowed Files\n\n- TBD",
            "## Allowed Files\n\n- .pcae/**",
        ),
        encoding="utf-8",
    )
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "end"])

    output = capsys.readouterr().out
    session_file = tmp_path / ".pcae" / "session.json"
    history_file = tmp_path / ".pcae" / "architecture-history.json"
    session_data = json.loads(session_file.read_text(encoding="utf-8"))
    history_data = json.loads(history_file.read_text(encoding="utf-8"))
    task_file = tmp_path / "tasks" / "active" / "20260523-0730-end-session.md"
    assert exit_code == 0
    assert "Session end complete." in output
    assert "Active task: 20260523-0730-end-session" in output
    assert "Title: End session" in output
    assert "Git status: clean" in output
    assert "Architecture history entries: 1" in output
    assert "Next recommended step: none" in output
    assert session_data["active_task"] == {
        "id": "20260523-0730-end-session",
        "title": "End session",
    }
    assert len(history_data) == 1
    assert history_data[0]["active_task"] == {
        "id": "20260523-0730-end-session",
        "title": "End session",
    }
    assert "## Status\n\nactive" in task_file.read_text(encoding="utf-8")


def test_session_end_appends_architecture_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "End session",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )
    task_file = tmp_path / "tasks" / "active" / "20260523-0730-end-session.md"
    task_file.write_text(
        task_file.read_text(encoding="utf-8").replace(
            "## Allowed Files\n\n- TBD",
            "## Allowed Files\n\n- .pcae/**",
        ),
        encoding="utf-8",
    )
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    first_exit_code = main(["session", "end"])
    capsys.readouterr()
    second_exit_code = main(["session", "end"])

    output = capsys.readouterr().out
    history_data = json.loads(
        (tmp_path / ".pcae" / "architecture-history.json").read_text(
            encoding="utf-8"
        )
    )
    assert first_exit_code == 0
    assert second_exit_code == 0
    assert len(history_data) == 2
    assert "Architecture history entries: 2" in output


def test_session_start_stops_when_check_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "start"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Session start stopped: pcae check failed." in output
    assert "No active task contract found in tasks/active/." in output


def test_session_start_reports_missing_session_and_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Start session",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "start"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Session start summary." in output
    assert "No session snapshot found at .pcae/session.json." in output


def test_session_start_prints_resume_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Start session",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )
    update_session_snapshot(
        HarnessPath(tmp_path),
        SessionUpdate(
            objective="Resume governed work",
            completed_step="Finished previous phase",
            next_step="Run implementation",
            blocker="Need review",
            warning="Watch scope",
        ),
    )
    write_file(
        tmp_path / ".pcae" / "architecture-history.json",
        json.dumps(
            [
                {
                    "active_task": {
                        "id": "20260523-0730-start-session",
                        "title": "Start session",
                    },
                    "architecture_zones_touched": {},
                    "changed_files_count": 0,
                    "dependency_warnings_count": 0,
                    "enforcement_mode": "advisory",
                    "git_branch": "main",
                    "session_continuity": "verified",
                    "timestamp": "2026-05-23T08:00:00+00:00",
                }
            ]
        ),
    )
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "start"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Session start summary." in output
    assert "Active task: 20260523-0730-start-session" in output
    assert "Title: Start session" in output
    assert "Git branch:" in output
    assert "Git status:" in output
    assert "Current objective: Resume governed work" in output
    assert "Last completed step: Finished previous phase" in output
    assert "Next recommended step: Run implementation" in output
    assert "Blockers:\n  - Need review" in output
    assert "Warnings:\n  - Watch scope" in output
    assert "Architecture history entries: 1" in output
    assert "Latest enforcement mode: advisory" in output
    assert "Latest session continuity: verified" in output


def test_session_start_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Start session",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )
    write_file(
        tmp_path / ".pcae" / "architecture-history.json",
        "[]\n",
    )
    commit_baseline(tmp_path)
    before = text_file_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "start"])

    after = text_file_snapshot(tmp_path)
    capsys.readouterr()
    assert exit_code == 0
    assert after == before


# ---------------------------------------------------------------------------
# pcae session bootstrap
# ---------------------------------------------------------------------------


def test_session_bootstrap_acquires_agent_lock(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import read_agent_lock

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Bootstrap task",
    )
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    capsys.readouterr()
    assert exit_code == 0
    lock = read_agent_lock(HarnessPath(tmp_path))
    assert lock is not None
    assert lock.agent_id == "claude-local"


def test_session_bootstrap_records_agent_acquired_provenance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.provenance import read_provenance_history

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Bootstrap provenance task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--agent-id", "claude-local"])

    capsys.readouterr()
    history = read_provenance_history(HarnessPath(tmp_path))
    assert any(e.event_type == "agent_acquired" for e in history.events)
    acquired = next(e for e in history.events if e.event_type == "agent_acquired")
    assert acquired.agent_id == "claude-local"


def test_session_bootstrap_runs_governance_validation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Bootstrap validation task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Health: healthy" in output
    assert "Check: passed" in output


def test_session_bootstrap_shows_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Bootstrap active task test")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Active task:" in output
    assert "Title: Bootstrap active task test" in output


def test_session_bootstrap_shows_current_session(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Bootstrap session task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Current session:" in output
    assert "(active)" in output


def test_session_bootstrap_shows_provenance_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Bootstrap provenance summary task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Provenance events: 1" in output
    assert "Latest event: Agent lock acquired by claude-local" in output


def test_session_bootstrap_prints_ready_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Bootstrap ready task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Ready: yes" in output


def test_session_bootstrap_shows_independent_challenge_context(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.commands.session as session_commands

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Bootstrap challenge task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.setattr(
        session_commands,
        "build_irg_challenge_context",
        lambda root: {
            "display_enabled": True,
            "compact_display": {
                "header": "Independent Challenge Context — advisory only",
                "summary": "2 questions surfaced across governance and roadmap.",
                "questions": [
                    {
                        "domain": "governance",
                        "attention_level": "high_attention",
                        "question": "What assumption might be wrong?",
                    },
                    {
                        "domain": "roadmap",
                        "attention_level": "medium_attention",
                        "question": "What changed since this reasoning was established?",
                    },
                ],
                "footer": "Displayed for context only. Command outcomes stay unchanged.",
            },
        },
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Independent Challenge Context — advisory only" in output
    assert "What assumption might be wrong?" in output
    assert "Displayed for context only. Command outcomes stay unchanged." in output


def test_session_bootstrap_challenge_independence_validation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.commands.session as session_commands

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Bootstrap independence task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    scenarios = [
        None,
        {
            "display_enabled": True,
            "compact_display": {
                "header": "Independent Challenge Context — advisory only",
                "summary": "No material challenge questions surfaced.",
                "questions": [],
                "footer": "",
            },
        },
        {
            "display_enabled": True,
            "compact_display": {
                "header": "Independent Challenge Context — advisory only",
                "summary": "3 questions surfaced across governance, roadmap, and architecture.",
                "questions": [
                    {"domain": "governance", "attention_level": "high_attention", "question": "What changed?"},
                    {"domain": "roadmap", "attention_level": "medium_attention", "question": "What blind spot exists?"},
                    {"domain": "architecture", "attention_level": "low_attention", "question": "What counterfactual deserves attention?"},
                ],
                "footer": "Displayed for context only. Command outcomes stay unchanged.",
            },
        },
        {
            "display_enabled": True,
            "compact_display": {
                "header": "Independent Challenge Context — advisory only",
                "summary": "1 question surfaced across historical_drift.",
                "questions": [
                    {
                        "domain": "historical_drift",
                        "attention_level": "critical_question",
                        "question": "What reasoning may have aged?",
                    }
                ],
                "footer": "Displayed for context only. Command outcomes stay unchanged.",
            },
        },
    ]

    for scenario in scenarios:
        monkeypatch.setattr(
            session_commands,
            "build_irg_challenge_context",
            (lambda root, payload=scenario: payload),
        )
        exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "Health: healthy" in output
        assert "Check: passed" in output
        assert "Ready: yes" in output


def test_session_bootstrap_fails_when_lock_already_held(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import acquire_agent_lock

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "other-agent")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Agent lock already held by other-agent." in output


def test_session_bootstrap_ready_false_when_check_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    # No active task contract → check fails
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Health: unhealthy" in output
    assert "Check: failed" in output
    assert "Ready: no" in output


def test_session_bootstrap_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Bootstrap JSON task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["agent_id"] == "claude-local"
    assert data["health_status"] in {"healthy", "unhealthy"}
    assert data["check_status"] in {"passed", "failed"}
    assert data["ready"] is True
    assert isinstance(data["provenance_event_count"], int)
    assert data["current_session"] is not None
    assert data["current_session"]["active"] is True
    assert data["latest_event"] is not None
    assert data["latest_event"]["event_type"] == "agent_acquired"
    assert data["lock_acquired"] is True
    assert set(data.keys()) == {
        "active_task",
        "agent_id",
        "check_status",
        "current_session",
        "health_status",
        "latest_event",
        "lock_acquired",
        "provenance_event_count",
        "ready",
    }


def test_session_bootstrap_json_ready_false_when_check_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    # No task → check fails
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 1
    data = json.loads(output)
    assert data["ready"] is False
    assert data["check_status"] == "failed"
    assert data["health_status"] == "unhealthy"


# same-agent idempotent bootstrap
# ---------------------------------------------------------------------------


def test_session_bootstrap_same_agent_already_held_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import acquire_agent_lock

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Idempotent bootstrap task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Ready: yes" in output


def test_session_bootstrap_same_agent_shows_already_held_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import acquire_agent_lock

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Already held note task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert "lock already held" in output


def test_session_bootstrap_same_agent_shows_full_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import acquire_agent_lock

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Full summary task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert "Health:" in output
    assert "Check:" in output
    assert "Active task:" in output
    assert "Ready:" in output


def test_session_bootstrap_same_agent_uses_refreshed_session_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import acquire_agent_lock

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Bootstrap stale lock task",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "claude-local")

    stale_task = (
        tmp_path
        / "tasks"
        / "active"
        / "20260523-0730-bootstrap-stale-lock-task.md"
    )
    done_task = (
        tmp_path
        / "tasks"
        / "done"
        / "20260523-0730-bootstrap-stale-lock-task.md"
    )
    done_task.parent.mkdir(parents=True, exist_ok=True)
    stale_task.rename(done_task)
    create_task_contract(
        HarnessPath(tmp_path),
        "Bootstrap current task",
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Active task: 20260523-0800-bootstrap-current-task" in output
    assert "Title: Bootstrap current task" in output
    assert "20260523-0730-bootstrap-stale-lock-task" not in output


def test_session_bootstrap_same_agent_does_not_append_provenance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import acquire_agent_lock
    from pcae.core.provenance import read_provenance_history

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "No duplicate provenance task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "claude-local")
    before = read_provenance_history(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--agent-id", "claude-local"])

    capsys.readouterr()
    after = read_provenance_history(HarnessPath(tmp_path))
    assert len(after.events) == len(before.events)


def test_session_bootstrap_same_agent_json_lock_acquired_false(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import acquire_agent_lock

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Idempotent JSON task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["lock_acquired"] is False
    assert data["agent_id"] == "claude-local"
    assert data["ready"] is True
    assert set(data.keys()) == {
        "active_task",
        "agent_id",
        "check_status",
        "current_session",
        "health_status",
        "latest_event",
        "lock_acquired",
        "provenance_event_count",
        "ready",
    }


def test_session_bootstrap_different_agent_still_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import acquire_agent_lock

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    acquire_agent_lock(HarnessPath(tmp_path), "other-agent")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Agent lock already held by other-agent." in output


# ---------------------------------------------------------------------------
# pcae session bootstrap --compact
# ---------------------------------------------------------------------------


def test_session_bootstrap_compact_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Compact bootstrap task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    capsys.readouterr()
    assert exit_code == 0


def test_session_bootstrap_compact_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.provenance import read_provenance_history

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Read-only compact task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    before_files = text_file_snapshot(tmp_path)
    before_events = len(read_provenance_history(HarnessPath(tmp_path)).events)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact"])

    capsys.readouterr()
    assert text_file_snapshot(tmp_path) == before_files
    assert len(read_provenance_history(HarnessPath(tmp_path)).events) == before_events


def test_session_bootstrap_compact_shows_profile(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Compact profile task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert "Profile: universal" in output


def test_session_bootstrap_compact_shows_bootstrap_prompt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Compact prompt task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert "[PCAE Bootstrap" in output
    assert "Governance:" in output
    assert "Rules:" in output
    assert "Validate:" in output


def test_session_bootstrap_compact_shows_stale_context_suppression(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Stale-context task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert "Stale-context:" in output
    assert "PROJECT_STATUS.md is background" in output
    assert "stale work" in output


def test_session_bootstrap_compact_shows_token_optimization_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Token note task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert "Token optimization note:" in output


def test_session_bootstrap_compact_shows_vendor_neutral_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Vendor-neutral task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert "Vendor-neutral note:" in output
    assert "not tailored to any specific AI agent" in output


def test_session_bootstrap_compact_shows_quality_preservation_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Quality note task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert "Quality preservation note:" in output


def test_session_bootstrap_compact_shows_independent_challenge_context(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.commands.session as session_commands

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Compact challenge task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.setattr(
        session_commands,
        "build_irg_challenge_context",
        lambda root: {
            "display_enabled": True,
            "compact_display": {
                "header": "Independent Challenge Context — advisory only",
                "summary": "1 question surfaced across strategic_review.",
                "questions": [
                    {
                        "domain": "strategic_review",
                        "attention_level": "high_attention",
                        "question": "What blind spot exists?",
                    }
                ],
                "footer": "Displayed for context only. Command outcomes stay unchanged.",
            },
        },
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Independent Challenge Context — advisory only" in output
    assert "What blind spot exists?" in output
    assert "Bootstrap compression" in output
    assert "relaxing governance constraints" in output


def test_session_bootstrap_compact_preserves_operational_rules(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Rules preservation task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert "Phase prompt is authoritative" in output
    assert "active task scope" in output


def test_session_bootstrap_compact_profile_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Implementation profile task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact", "--profile", "implementation"])

    output = capsys.readouterr().out
    assert "Profile: implementation" in output
    assert "implementation profile" in output
    assert "scope_boundaries" in output


def test_session_bootstrap_compact_profile_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Handoff profile task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact", "--profile", "handoff"])

    output = capsys.readouterr().out
    assert "Profile: handoff" in output
    assert "handoff profile" in output
    assert "bootstrap_handoff_notes" in output


def test_session_bootstrap_compact_unknown_profile_falls_back(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Unknown profile task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact", "--profile", "no-such-profile"])

    output = capsys.readouterr().out
    assert "Warning:" in output
    assert "no-such-profile" in output
    assert "Profile: universal" in output


def test_session_bootstrap_compact_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Compact JSON task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact", "--json"])

    capsys.readouterr()
    assert exit_code == 0


def test_session_bootstrap_compact_json_is_valid_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Compact JSON valid task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, dict)


def test_session_bootstrap_compact_json_required_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Compact JSON keys task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact", "--json"])

    data = json.loads(capsys.readouterr().out)
    for key in (
        "advisory",
        "bootstrap_prompt",
        "governance_state",
        "operational_rules",
        "orchestration_state",
        "profile_type",
        "validation_commands",
    ):
        assert key in data, key


def test_session_bootstrap_compact_json_profile_type(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Compact JSON profile task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact", "--profile", "implementation", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert data["profile_type"] == "implementation"


def test_session_bootstrap_compact_json_bootstrap_prompt_is_string(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Compact JSON prompt string task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert isinstance(data["bootstrap_prompt"], str)
    assert "[PCAE Bootstrap" in data["bootstrap_prompt"]


def test_session_bootstrap_compact_json_advisory_is_governance_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Compact JSON advisory task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--compact", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert "Bootstrap compression" in data["advisory"]
    assert "relaxing governance constraints" in data["advisory"]


# ---------------------------------------------------------------------------
# bootstrap helpers
# ---------------------------------------------------------------------------


def patch_task_allowed_files(root: Path) -> None:
    task_dir = root / "tasks" / "active"
    for task_file in task_dir.glob("*.md"):
        content = task_file.read_text(encoding="utf-8")
        task_file.write_text(
            content.replace(
                "## Allowed Files\n\n- TBD",
                "## Allowed Files\n\n- .pcae/**",
            ),
            encoding="utf-8",
        )


def init_git_repo(root: Path) -> None:
    run_git(root, "init")
    run_git(root, "config", "user.email", "test@example.com")
    run_git(root, "config", "user.name", "Test User")


def commit_baseline(root: Path) -> None:
    run_git(root, "add", ".")
    run_git(root, "commit", "-m", "baseline")


def run_git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def text_file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


# --- Phase 70C: session_continuity_status deduplication ---


def test_70c_session_continuity_status_is_canonical() -> None:
    import importlib
    import pcae.core.session
    import pcae.core.health
    import pcae.core.export
    import pcae.core.architecture
    import pcae.commands.check

    canonical = pcae.core.session.session_continuity_status
    assert pcae.core.health.session_continuity_status is canonical
    assert pcae.commands.check.session_continuity_status is canonical
    assert pcae.core.architecture.session_continuity_status is canonical
    assert pcae.core.export.session_continuity_status is canonical


def test_70c_session_continuity_status_returns_verified() -> None:
    from pcae.core.session import session_continuity_status
    from dataclasses import dataclass

    @dataclass
    class FakeResult:
        infos: tuple
        violations: tuple
        warnings: tuple

    result = FakeResult(
        infos=(type("M", (), {"text": "Session continuity verified."})(),),
        violations=(),
        warnings=(),
    )
    assert session_continuity_status(result) == "verified"


def test_70c_session_continuity_status_returns_missing_from_warning() -> None:
    from pcae.core.session import session_continuity_status
    from dataclasses import dataclass

    @dataclass
    class FakeResult:
        infos: tuple
        violations: tuple
        warnings: tuple

    result = FakeResult(
        infos=(),
        violations=(),
        warnings=(type("M", (), {"text": "Session snapshot missing at .pcae/session.json."})(),),
    )
    assert session_continuity_status(result) == "missing"


def test_70c_session_continuity_status_returns_mismatch() -> None:
    from pcae.core.session import session_continuity_status
    from dataclasses import dataclass

    @dataclass
    class FakeResult:
        infos: tuple
        violations: tuple
        warnings: tuple

    result = FakeResult(
        infos=(),
        violations=(type("M", (), {"text": "Session active task does not match current active task."})(),),
        warnings=(),
    )
    assert session_continuity_status(result) == "mismatch"


def test_70c_session_continuity_status_returns_invalid() -> None:
    from pcae.core.session import session_continuity_status
    from dataclasses import dataclass

    @dataclass
    class FakeResult:
        infos: tuple
        violations: tuple
        warnings: tuple

    result = FakeResult(
        infos=(),
        violations=(type("M", (), {"text": "Invalid session JSON: expecting value."})(),),
        warnings=(),
    )
    assert session_continuity_status(result) == "invalid"


def test_70c_session_continuity_status_returns_unknown() -> None:
    from pcae.core.session import session_continuity_status
    from dataclasses import dataclass

    @dataclass
    class FakeResult:
        infos: tuple
        violations: tuple
        warnings: tuple

    result = FakeResult(infos=(), violations=(), warnings=())
    assert session_continuity_status(result) == "unknown"


def test_70c_no_duplicate_definitions_remain() -> None:
    import ast
    from pathlib import Path

    src = Path("src/pcae")
    definitions = []
    for py_file in src.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "session_continuity_status":
                definitions.append(str(py_file))

    assert definitions == ["src/pcae/core/session.py"], (
        f"Expected exactly 1 definition in session.py, found: {definitions}"
    )
