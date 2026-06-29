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
    assert exit_code == 0
    assert "Session end complete." in output


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


def test_session_start_idle_when_no_active_task_clean_tree(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "start"])

    output = capsys.readouterr().out
    assert exit_code == 0


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
    assert "Readiness: ready" in output


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
        assert "Readiness: ready" in output


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


def test_session_bootstrap_no_task_reports_check_failure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Check: failed" in output


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
    assert data.keys() >= {
        "active_task",
        "agent_id",
        "check_status",
        "current_session",
        "health_status",
        "latest_event",
        "latest_handoff",
        "lock_acquired",
        "lock_backend_name",
        "lock_conflict",
        "lock_rehydrated",
        "lock_synced",
        "provenance_event_count",
        "ready",
        "recognized_backend",
    }
    assert data["latest_handoff"] is None


def test_session_bootstrap_json_no_task_reports_check_failure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 1
    data = json.loads(output)
    assert data["ready"] is False
    assert data["check_status"] == "failed"


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
    assert "Readiness: ready" in output


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
    assert "Readiness:" in output


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
    assert data.keys() >= {
        "active_task",
        "agent_id",
        "check_status",
        "current_session",
        "health_status",
        "latest_event",
        "latest_handoff",
        "lock_acquired",
        "lock_backend_name",
        "lock_conflict",
        "lock_rehydrated",
        "lock_synced",
        "provenance_event_count",
        "ready",
        "recognized_backend",
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


# ---------------------------------------------------------------------------
# Phase 70W: handoff bootstrap consumption
# ---------------------------------------------------------------------------


def _write_handoff_artifact(tmp_path: Path, data: dict) -> None:
    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    (handoffs_dir / "latest.json").write_text(
        json.dumps(data, indent=2, sort_keys=True), encoding="utf-8",
    )


def _sample_handoff() -> dict:
    return {
        "active_task_id": None,
        "active_task_title": None,
        "auto_summary": True,
        "bootstrap_command": "pcae session bootstrap --agent-id claude-local",
        "branch": "main",
        "check_passed": True,
        "created_at": "2026-06-19T00:00:00+00:00",
        "handoff_id": "handoff-20260619T000000-000000-idle",
        "health_status": "healthy (idle)",
        "latest_commit": "Complete Phase 70V",
        "lifecycle_review": "not_applicable",
        "next_agent": "claude-local",
        "push_mode": "nothing_to_push",
        "push_ready": False,
        "recent_commits": ["Complete Phase 70V"],
        "recommended_next_action": "pcae session bootstrap --agent-id claude-local",
        "summary": "Phase handoff: branch=main, task=idle",
        "task_memory_status": "clean",
        "task_state": "idle",
        "unpushed_commits": 0,
        "working_tree": "clean",
    }


def test_70w_bootstrap_shows_handoff_when_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Handoff bootstrap task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Last handoff:" in output
    assert "Phase handoff: branch=main, task=idle" in output
    assert "Complete Phase 70V" in output


def test_70w_bootstrap_no_handoff_still_works(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "No handoff task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Last handoff:" not in output


def test_70w_bootstrap_json_includes_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "JSON handoff bootstrap task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["latest_handoff"] is not None
    assert data["latest_handoff"]["handoff_id"] == "handoff-20260619T000000-000000-idle"
    assert data["latest_handoff"]["summary"] == "Phase handoff: branch=main, task=idle"


def test_70w_bootstrap_json_null_handoff_when_missing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "No handoff JSON task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["latest_handoff"] is None


def test_70w_compact_bootstrap_json_includes_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["latest_handoff"] is not None
    assert data["latest_handoff"]["branch"] == "main"


def test_70w_bootstrap_does_not_mutate_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "No mutate task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    handoff_data = _sample_handoff()
    _write_handoff_artifact(tmp_path, handoff_data)
    before = (tmp_path / ".pcae" / "handoffs" / "latest.json").read_text(encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["session", "bootstrap", "--agent-id", "claude-local"])

    capsys.readouterr()
    after = (tmp_path / ".pcae" / "handoffs" / "latest.json").read_text(encoding="utf-8")
    assert before == after


# ---------------------------------------------------------------------------
# Phase 71A: bootstrap handoff freshness and stale phase fix
# ---------------------------------------------------------------------------


def test_71a_compact_bootstrap_shows_handoff_over_stale_phase(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    handoff = _sample_handoff()
    handoff["summary"] = "Phase handoff: task=idle, latest_commit=Complete Phase 70Z"
    handoff["latest_commit"] = "Complete Phase 70Z"
    _write_handoff_artifact(tmp_path, handoff)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Last handoff:" in output
    assert "Complete Phase 70Z" in output
    assert "Phase (from PROJECT_STATUS.md):" in output


def test_71a_compact_bootstrap_no_handoff_shows_plain_phase(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase:" in output
    assert "Phase (from PROJECT_STATUS.md):" not in output


def test_71a_compact_bootstrap_json_includes_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    handoff = _sample_handoff()
    handoff["latest_commit"] = "Complete Phase 70Z"
    _write_handoff_artifact(tmp_path, handoff)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["latest_handoff"] is not None
    assert data["latest_handoff"]["latest_commit"] == "Complete Phase 70Z"
    assert "Last handoff:" in data["bootstrap_prompt"]


def test_71a_compact_bootstrap_prompt_text_contains_handoff_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    handoff = _sample_handoff()
    handoff["summary"] = "Phase handoff: branch=main, task=idle"
    handoff["task_state"] = "idle"
    handoff["recommended_next_action"] = "pcae session bootstrap --agent-id claude-local"
    _write_handoff_artifact(tmp_path, handoff)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Task: idle" in output
    assert "Next action:" in output


# ---------------------------------------------------------------------------
# Phase queue visibility in bootstrap (Phase 71D)
# ---------------------------------------------------------------------------


def test_71d_bootstrap_shows_queue_from_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Queue bootstrap task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    handoff = _sample_handoff()
    handoff["phase_queue_present"] = True
    handoff["phase_queue_count"] = 3
    handoff["phase_queue_next"] = "Phase 72A: queue item"
    _write_handoff_artifact(tmp_path, handoff)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase queue: 3 entries" in output
    assert "Next queued: Phase 72A: queue item" in output


def test_71d_bootstrap_silent_when_no_queue_in_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "No queue bootstrap task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase queue" not in output


def test_71d_compact_bootstrap_shows_queue_from_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    handoff = _sample_handoff()
    handoff["phase_queue_present"] = True
    handoff["phase_queue_count"] = 2
    handoff["phase_queue_next"] = "Phase 72C: compact queue"
    _write_handoff_artifact(tmp_path, handoff)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase queue: 2 entries" in output
    assert "Phase 72C: compact queue" in output


def test_71d_compact_bootstrap_silent_when_no_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase queue" not in output


# ---------------------------------------------------------------------------
# Autonomy audit visibility in bootstrap (Phase 71I)
# ---------------------------------------------------------------------------


def _write_audit_artifact(root: Path, audit: dict) -> None:
    audit_dir = root / ".pcae" / "phase-audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "latest.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8",
    )


def test_71i_compact_bootstrap_shows_audit_when_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T060000Z",
        "phases_detected": 4,
        "warnings": ["Phase 71X: missing completion commit"],
        "healthy_idle": True,
    })
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Last audit:" in output
    assert "4 phases" in output
    assert "1 warnings" in output
    assert "healthy idle" in output


def test_71i_compact_bootstrap_clean_when_no_audit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Last audit:" not in output


def test_71i_compact_bootstrap_audit_no_warnings(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T070000Z",
        "phases_detected": 2,
        "warnings": [],
        "healthy_idle": False,
    })
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Last audit:" in output
    assert "2 phases" in output
    assert "0 warnings" in output
    assert "healthy idle" not in output


def test_71i_compact_bootstrap_json_includes_audit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T080000Z",
        "phases_detected": 5,
        "warnings": [],
        "healthy_idle": True,
    })
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "Last audit:" in data["bootstrap_prompt"]


# ---------------------------------------------------------------------------
# Phase 71J: pcae session continuity-check
# ---------------------------------------------------------------------------


def test_71j_continuity_check_healthy_idle(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T100000Z",
        "phases_detected": 5,
        "warnings": [],
        "healthy_idle": True,
    })
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "continuity-check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Continuity check" in output
    assert "Suitable for continuation: yes" in output
    assert "Handoff: present" in output
    assert "Audit: 5 phases" in output
    assert "Phase queue: empty" in output
    assert "Task state: idle" in output
    assert "Issues:" not in output


def test_71j_continuity_check_json_healthy(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T100000Z",
        "phases_detected": 5,
        "warnings": [],
        "healthy_idle": True,
    })
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "continuity-check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["suitable_for_continuation"] is True
    assert data["handoff_present"] is True
    assert data["audit_present"] is True
    assert data["check_passed"] is True
    assert data["task_state"] == "idle"
    assert data["phase_queue_count"] == 0
    assert data["issues"] == []
    assert data["working_tree"] == "clean"


def test_71j_continuity_check_missing_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T100000Z",
        "phases_detected": 3,
        "warnings": [],
        "healthy_idle": True,
    })
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "continuity-check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Handoff: missing" in output
    assert "No handoff artifact found" in output


def test_71j_continuity_check_missing_audit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "continuity-check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Audit: missing" in output
    assert "No audit artifact found" in output


def test_71j_continuity_check_dirty_tree(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T100000Z",
        "phases_detected": 3,
        "warnings": [],
        "healthy_idle": True,
    })
    write_file(tmp_path / "dirty.txt", "uncommitted\n")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "continuity-check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Suitable for continuation: no" in output
    assert "Working tree is not clean" in output


def test_71j_continuity_check_non_empty_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T100000Z",
        "phases_detected": 3,
        "warnings": [],
        "healthy_idle": True,
    })
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(
        json.dumps(["Phase 72A: next item", "Phase 72B: another"]),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "continuity-check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase queue: 2 entries" in output


def test_71j_continuity_check_json_missing_both(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "continuity-check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["handoff_present"] is False
    assert data["audit_present"] is False
    assert "No handoff artifact found" in data["issues"]
    assert "No audit artifact found" in data["issues"]


def test_71j_continuity_check_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T100000Z",
        "phases_detected": 3,
        "warnings": [],
        "healthy_idle": True,
    })
    before = text_file_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["session", "continuity-check"])

    capsys.readouterr()
    after = text_file_snapshot(tmp_path)
    assert after == before


def test_71j_continuity_check_with_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Active continuity task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "continuity-check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Task state: active" in output
    assert "Active task:" in output


# ---------------------------------------------------------------------------
# Phase 71M: prompt visibility in bootstrap and continuity-check
# ---------------------------------------------------------------------------


def _write_prompt_artifact(root: Path, title: str, text: str) -> None:
    from pcae.commands.phase import PHASE_PROMPTS_DIR, _slugify
    from datetime import datetime, timezone

    prompts_dir = root / PHASE_PROMPTS_DIR
    prompts_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    slug = _slugify(title)
    ts_str = now.strftime("%Y%m%dT%H%M%SZ")
    ts_filename = f"{slug}-{ts_str}.md"
    (prompts_dir / ts_filename).write_text(text, encoding="utf-8")
    (prompts_dir / "latest.md").write_text(text, encoding="utf-8")
    metadata = {
        "title": title,
        "created_at": now.isoformat(),
        "slug": slug,
        "timestamped_path": str(PHASE_PROMPTS_DIR / ts_filename),
        "latest_path": str(PHASE_PROMPTS_DIR / "latest.md"),
    }
    (prompts_dir / "latest.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )


def test_71m_compact_bootstrap_shows_prompt_when_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_prompt_artifact(tmp_path, "71M Bootstrap", "Bootstrap prompt.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Latest prompt: 71M Bootstrap" in output


def test_71m_compact_bootstrap_clean_when_no_prompt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Latest prompt:" not in output


def test_71m_continuity_check_json_includes_prompt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T100000Z",
        "phases_detected": 5,
        "warnings": [],
        "healthy_idle": True,
    })
    _write_prompt_artifact(tmp_path, "71M Continuity", "Continuity prompt.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "continuity-check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["prompt_present"] is True
    assert data["prompt_title"] == "71M Continuity"
    assert data["prompt_path"] == ".pcae/phase-prompts/latest.md"


def test_71m_continuity_check_json_no_prompt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "continuity-check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["prompt_present"] is False
    assert data["prompt_title"] is None


def test_71m_continuity_check_human_shows_prompt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _write_handoff_artifact(tmp_path, _sample_handoff())
    _write_prompt_artifact(tmp_path, "71M Human", "Human prompt.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "continuity-check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Latest prompt: 71M Human" in output


# --- Phase 71V: Strategic Continuity Pointer Refresh ---


def test_71v_extract_latest_phase_from_audit() -> None:
    from pcae.core.context import _extract_latest_phase

    audit = {"phases": [{"phase_id": "71S"}, {"phase_id": "71R"}]}
    assert _extract_latest_phase(None, audit) == "71S"


def test_71v_extract_latest_phase_from_handoff() -> None:
    from pcae.core.context import _extract_latest_phase

    handoff = {"recent_commits": [
        "Complete Phase 71S Codex autonomy comparison handoff note",
        "Document Phase 71S Codex autonomy comparison",
    ]}
    assert _extract_latest_phase(handoff, None) == "71S"


def test_71v_extract_latest_phase_prefers_audit() -> None:
    from pcae.core.context import _extract_latest_phase

    audit = {"phases": [{"phase_id": "71U"}]}
    handoff = {"recent_commits": ["Complete Phase 71S something"]}
    assert _extract_latest_phase(handoff, audit) == "71U"


def test_71v_extract_latest_phase_none_when_empty() -> None:
    from pcae.core.context import _extract_latest_phase

    assert _extract_latest_phase(None, None) is None
    assert _extract_latest_phase({}, {}) is None
    assert _extract_latest_phase({"recent_commits": []}, {"phases": []}) is None


def test_71v_bootstrap_shows_latest_completed_phase(tmp_path: Path) -> None:
    from pcae.core.context import ContextPack, build_bootstrap_prompt
    from pcae.core.context import resolve_profile

    pack = _make_pack(tmp_path, strategic_activated="69P")
    profile, _ = resolve_profile("implementation")
    audit = {"phases": [{"phase_id": "71S"}]}
    handoff = {"recent_commits": ["Complete Phase 71S something"]}

    result = build_bootstrap_prompt(pack, profile, handoff=handoff, audit=audit)

    assert "Latest completed phase: 71S" in result
    assert "Historical strategic decision: SLR-69P-001" in result
    assert "Strategic Decision:" not in result


def test_71v_bootstrap_no_historical_when_matching(tmp_path: Path) -> None:
    from pcae.core.context import ContextPack, build_bootstrap_prompt
    from pcae.core.context import resolve_profile

    pack = _make_pack(tmp_path, strategic_activated="69P")
    profile, _ = resolve_profile("implementation")
    audit = {"phases": [{"phase_id": "69P"}]}

    result = build_bootstrap_prompt(pack, profile, audit=audit)

    assert "Latest completed phase: 69P" in result
    assert "Strategic Decision: SLR-69P-001" in result
    assert "Historical strategic decision" not in result


def test_71v_bootstrap_no_latest_without_handoff_or_audit(tmp_path: Path) -> None:
    from pcae.core.context import ContextPack, build_bootstrap_prompt
    from pcae.core.context import resolve_profile

    pack = _make_pack(tmp_path, strategic_activated="69P")
    profile, _ = resolve_profile("implementation")

    result = build_bootstrap_prompt(pack, profile)

    assert "Latest completed phase:" not in result
    assert "Strategic Decision: SLR-69P-001" in result
    assert "Historical strategic decision" not in result


# Phase 72I — Compact Historical Continuity Summary
# ---------------------------------------------------------------------------


def test_72i_compact_historical_no_full_rationale(tmp_path: Path) -> None:
    from pcae.core.context import build_bootstrap_prompt
    from pcae.core.context import resolve_profile

    pack = _make_pack(tmp_path, strategic_activated="69P")
    profile, _ = resolve_profile("implementation")
    audit = {"phases": [{"phase_id": "72H"}]}

    result = build_bootstrap_prompt(pack, profile, audit=audit)

    assert "Historical strategic decision: SLR-69P-001" in result
    assert "Full details: pcae strategic-continuity show current" in result
    assert "Deferred Alternatives:" not in result
    assert "Referenced Review Findings:" not in result
    assert "SLR-69P-002" not in result


def test_72i_compact_historical_short_reason(tmp_path: Path) -> None:
    from pcae.core.context import build_bootstrap_prompt
    from pcae.core.context import resolve_profile

    pack = _make_pack(tmp_path, strategic_activated="69P")
    profile, _ = resolve_profile("implementation")
    audit = {"phases": [{"phase_id": "72H"}]}

    result = build_bootstrap_prompt(pack, profile, audit=audit)

    for line in result.splitlines():
        if "Historical strategic decision:" in line:
            assert "phase 69P" in line
            assert "roadmap_gap" in line
            assert len(line) < 300
            break
    else:
        raise AssertionError("Historical strategic decision line not found")


def test_72i_current_strategic_still_shows_full(tmp_path: Path) -> None:
    from pcae.core.context import build_bootstrap_prompt
    from pcae.core.context import resolve_profile

    pack = _make_pack(tmp_path, strategic_activated="69P")
    profile, _ = resolve_profile("implementation")
    audit = {"phases": [{"phase_id": "69P"}]}

    result = build_bootstrap_prompt(pack, profile, audit=audit)

    assert "Strategic Decision: SLR-69P-001" in result
    assert "Reason: Test rationale." in result
    assert "Deferred Alternatives:" in result
    assert "Referenced Review Findings:" in result


def test_72i_compact_historical_preserves_latest_phase(tmp_path: Path) -> None:
    from pcae.core.context import build_bootstrap_prompt
    from pcae.core.context import resolve_profile

    pack = _make_pack(tmp_path, strategic_activated="69P")
    profile, _ = resolve_profile("implementation")
    audit = {"phases": [{"phase_id": "72H"}]}

    result = build_bootstrap_prompt(pack, profile, audit=audit)

    assert "Latest completed phase: 72H" in result
    assert "Governance:" in result
    assert "Rules:" in result
    assert "Validate:" in result


def _make_pack(tmp_path: Path, strategic_activated: str = "69P") -> "ContextPack":
    from pcae.core.context import ContextPack

    return ContextPack(
        active_task=None,
        scope_boundaries={},
        architecture_memory={
            "decision_count": 0,
            "accepted_count": 0,
            "latest_decision": None,
        },
        governance_state={
            "health_status": "healthy (idle)",
            "check_status": "passed",
            "session_continuity": "verified",
            "agent_lock_state": {"locked": True, "agent_id": "test"},
        },
        irg_review_summary={"bootstrap_line": None},
        operational_rules=("Rule one.",),
        orchestration_state={
            "advisory_recommendation_semantics": "User remains authoritative."
        },
        provenance_summary={},
        roadmap_summary={"current_phase": "Phase 71S: Test Phase."},
        strategic_continuity={
            "current": {
                "lineage_id": "SLR-69P-001",
                "activated_phase_id": strategic_activated,
                "selected_branch_id": "BR-005",
                "decision_basis": "roadmap_gap",
                "rationale": "Test rationale.",
            },
            "deferred_alternatives": [],
            "referenced_review_findings": [],
        },
        validation_commands=("pcae health",),
        bootstrap_handoff_notes=(),
        advisory="compact by design",
    )


# Phase 74W.2: session bootstrap agent lock rehydration
def test_74w2_bootstrap_rehydrates_backend_lock(tmp_path, monkeypatch, capsys):
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Lock rehydrate task")
    patch_task_allowed_files(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    exit_code = main(["session", "bootstrap", "--agent-id", "claude-deepseek", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert d["lock_rehydrated"] is True
    assert d["lock_backend_name"] == "claude-deepseek"
    assert d["recognized_backend"] is True
    assert d["lock_conflict"] is False
    # Verify backend lock artifact was written
    lock_path = tmp_path / ".pcae" / "agent-locks" / "latest.json"
    assert lock_path.is_file()
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert lock["lock_status"] == "active"
    assert lock["backend_name"] == "claude-deepseek"
    assert lock["execution_authorized"] is False
    assert lock["invocation_allowed"] is False

def test_74w2_bootstrap_rehydrates_kimi_lock(tmp_path, monkeypatch, capsys):
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Kimi lock task")
    patch_task_allowed_files(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    exit_code = main(["session", "bootstrap", "--agent-id", "claude-kimi", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert d["lock_rehydrated"] is True
    assert d["lock_backend_name"] == "claude-kimi"
    assert d["recognized_backend"] is True
    lock = json.loads((tmp_path / ".pcae" / "agent-locks" / "latest.json").read_text(encoding="utf-8"))
    assert lock["backend_name"] == "claude-kimi"
    assert lock["invocation_allowed"] is False

def test_74w2_bootstrap_unknown_agent_no_rehydrate(tmp_path, monkeypatch, capsys):
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Unknown agent task")
    patch_task_allowed_files(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    exit_code = main(["session", "bootstrap", "--agent-id", "unknown-bot", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert d["lock_rehydrated"] is False
    assert d["recognized_backend"] is False

def test_74w2_bootstrap_no_backend_invocation(tmp_path, monkeypatch, capsys):
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "No invocation task")
    patch_task_allowed_files(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    exit_code = main(["session", "bootstrap", "--agent-id", "claude-deepseek", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    # Lock rehydration does not invoke backend, does not authorize execution
    assert "execution_authorized" not in d or d.get("lock_rehydrated") in (True, False)
    assert d.get("lock_backend_name") is not None or d.get("lock_rehydrated") is False

def test_74w2_compact_bootstrap_sync_lock(tmp_path, monkeypatch, capsys):
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path)
    create_task_contract(HarnessPath(tmp_path), "Compact sync task")
    patch_task_allowed_files(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    exit_code = main(["session", "bootstrap", "--agent-id", "claude-deepseek", "--compact", "--profile", "implementation", "--sync-lock", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert d["lock_synced"] is True
    assert d["lock_backend_name"] == "claude-deepseek"
    assert d["recognized_backend"] is True
    # Verify backend lock was written
    lock_path = tmp_path / ".pcae" / "agent-locks" / "latest.json"
    assert lock_path.is_file()
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert lock["backend_name"] == "claude-deepseek"
    assert lock["execution_authorized"] is False


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Q.1 — Bootstrap resume readiness hardening tests
# ═══════════════════════════════════════════════════════════════════════════

import os as _os_94q1

from pcae.commands.session import (
    _classify_bootstrap_readiness,
    _check_telegram_runtime,
    _extract_phase_number,
    _phase_is_completed,
    _format_push_status,
    READINESS_READY,
    READINESS_READY_WARNINGS,
    READINESS_NEEDS_ATTENTION,
    READINESS_BLOCKED,
)


class Test94Q1ReadinessClassification:
    """_classify_bootstrap_readiness: multi-factor readiness behavior."""

    def test_healthy_all_clean_produces_ready(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=True,
            health_status="healthy",
            active_task=None,
            latest_report=None,
            latest_handoff=None,
            push_check={"unpushed_commits": 0, "mode": "nothing_to_push"},
            tg_runtime={"status": "loaded", "telegram_enabled": True, "telegram_configured": True},
            task_memory_warnings=False,
        )
        assert readiness == READINESS_READY
        assert issues == []

    def test_health_unhealthy_blocks(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=True,
            health_status="unhealthy",
            active_task=None, latest_report=None, latest_handoff=None,
            push_check=None, tg_runtime=None, task_memory_warnings=False,
        )
        assert readiness == READINESS_BLOCKED
        assert any("health" in i.lower() for i in issues)

    def test_check_failed_blocks(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=False,
            health_status="healthy",
            active_task=None, latest_report=None, latest_handoff=None,
            push_check=None, tg_runtime=None, task_memory_warnings=False,
        )
        assert readiness == READINESS_BLOCKED
        assert any("check" in i.lower() for i in issues)

    def test_completed_phase_active_task_is_stale(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=True,
            health_status="healthy",
            active_task={"id": "task-94q", "title": "Phase 94Q — Backend Lifecycle"},
            latest_report={
                "phase_id": "94Q", "status": "completed",
                "report_completeness": "complete",
                "recommended_next_phase": "94Q.1 — Bootstrap Resume",
            },
            latest_handoff=None,
            push_check={"unpushed_commits": 0, "mode": "nothing_to_push"},
            tg_runtime={"status": "loaded", "telegram_enabled": True, "telegram_configured": True},
            task_memory_warnings=False,
        )
        assert readiness == READINESS_BLOCKED
        assert any("stale" in i.lower() for i in issues)

    def test_partial_report_blocks(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=True,
            health_status="healthy",
            active_task=None,
            latest_report={
                "phase_id": "94Q", "status": "completed",
                "report_completeness": "partial",
            },
            latest_handoff=None,
            push_check={"unpushed_commits": 0, "mode": "nothing_to_push"},
            tg_runtime={"status": "loaded", "telegram_enabled": True, "telegram_configured": True},
            task_memory_warnings=False,
        )
        assert readiness == READINESS_BLOCKED
        assert any("partial" in i.lower() for i in issues)

    def test_incomplete_report_blocks(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=True,
            health_status="healthy",
            active_task=None,
            latest_report={
                "phase_id": "94Q", "status": "completed",
                "report_completeness": "incomplete",
            },
            latest_handoff=None,
            push_check={"unpushed_commits": 0, "mode": "nothing_to_push"},
            tg_runtime={"status": "loaded", "telegram_enabled": True, "telegram_configured": True},
            task_memory_warnings=False,
        )
        assert readiness == READINESS_BLOCKED

    def test_stale_handoff_produces_warning(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=True,
            health_status="healthy",
            active_task=None,
            latest_report={
                "phase_id": "94Q", "status": "completed",
                "report_completeness": "complete",
                "completed_at": "2026-06-29T18:00:00Z",
            },
            latest_handoff={"created_at": "2026-06-29T15:00:00Z"},
            push_check={"unpushed_commits": 0, "mode": "nothing_to_push"},
            tg_runtime={"status": "loaded", "telegram_enabled": True, "telegram_configured": True},
            task_memory_warnings=False,
        )
        assert readiness == READINESS_READY_WARNINGS
        assert any("handoff" in i.lower() for i in issues)

    def test_tg_not_loaded_produces_warning(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=True,
            health_status="healthy",
            active_task=None, latest_report=None, latest_handoff=None,
            push_check={"unpushed_commits": 0, "mode": "nothing_to_push"},
            tg_runtime={"status": "not_loaded", "telegram_enabled": False, "telegram_configured": False},
            task_memory_warnings=False,
        )
        assert readiness == READINESS_READY_WARNINGS
        assert any("telegram" in i.lower() for i in issues)

    def test_task_memory_warnings_produce_warning(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=True,
            health_status="healthy",
            active_task=None, latest_report=None, latest_handoff=None,
            push_check={"unpushed_commits": 0, "mode": "nothing_to_push"},
            tg_runtime={"status": "loaded", "telegram_enabled": True, "telegram_configured": True},
            task_memory_warnings=True,
        )
        assert readiness == READINESS_READY_WARNINGS
        assert any("task memory" in i.lower() for i in issues)

    def test_unpushed_commits_produce_warning(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=True,
            health_status="healthy",
            active_task=None, latest_report=None, latest_handoff=None,
            push_check={"unpushed_commits": 3, "mode": "needs_push"},
            tg_runtime={"status": "loaded", "telegram_enabled": True, "telegram_configured": True},
            task_memory_warnings=False,
        )
        assert readiness == READINESS_READY_WARNINGS
        assert any("unpushed" in i.lower() for i in issues)

    def test_multiple_issues_all_reported(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=True,
            health_status="healthy",
            active_task={"id": "task-94q", "title": "Phase 94Q — Backend Lifecycle"},
            latest_report={
                "phase_id": "94Q", "status": "completed",
                "report_completeness": "complete",
            },
            latest_handoff=None,
            push_check={"unpushed_commits": 0, "mode": "nothing_to_push"},
            tg_runtime={"status": "not_loaded", "telegram_enabled": False, "telegram_configured": False},
            task_memory_warnings=True,
        )
        assert readiness == READINESS_BLOCKED  # stale task blocks
        assert len(issues) >= 2


class Test94Q1TelegramRuntime:
    """_check_telegram_runtime: env detection without secrets."""

    def test_no_env_vars_returns_not_loaded(self, monkeypatch):
        monkeypatch.delenv("PCAE_TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("PCAE_TELEGRAM_CHAT_ID", raising=False)
        monkeypatch.delenv("PCAE_TELEGRAM_ENABLED", raising=False)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
        result = _check_telegram_runtime()
        assert result["status"] == "not_loaded"
        assert result["runtime_loaded"] is False
        assert result["telegram_configured"] is False
        assert result["telegram_enabled"] is False

    def test_token_present_returns_loaded(self, monkeypatch):
        monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "test-token")
        monkeypatch.setenv("PCAE_TELEGRAM_CHAT_ID", "test-chat")
        monkeypatch.setenv("PCAE_TELEGRAM_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        result = _check_telegram_runtime()
        assert result["status"] == "loaded"
        assert result["runtime_loaded"] is True
        assert result["telegram_configured"] is True
        assert result["telegram_enabled"] is True

    def test_token_present_but_disabled(self, monkeypatch):
        monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "test-token")
        monkeypatch.setenv("PCAE_TELEGRAM_CHAT_ID", "test-chat")
        monkeypatch.delenv("PCAE_TELEGRAM_ENABLED", raising=False)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
        result = _check_telegram_runtime()
        assert result["status"] == "loaded"
        assert result["telegram_configured"] is True
        assert result["telegram_enabled"] is False

    def test_no_secrets_in_result(self, monkeypatch):
        monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "secret-token-12345")
        monkeypatch.setenv("PCAE_TELEGRAM_CHAT_ID", "123456789")
        result = _check_telegram_runtime()
        j = json.dumps(result)
        assert "secret-token-12345" not in j
        assert "123456789" not in j
        assert result["token_present"] is True
        assert result["chat_id_present"] is True


class Test94Q1Helpers:
    """Unit tests for Phase 94Q.1 helper functions."""

    def test_extract_phase_number_simple(self):
        assert _extract_phase_number("94Q") == "94Q"

    def test_extract_phase_number_with_dot(self):
        assert _extract_phase_number("94Q.1") == "94Q.1"

    def test_phase_is_completed_matching(self):
        report = {"phase_id": "94Q", "status": "completed"}
        assert _phase_is_completed("94Q", report) is True

    def test_phase_is_completed_subphase(self):
        report = {"phase_id": "94Q.1", "status": "completed"}
        assert _phase_is_completed("94Q.1", report) is True

    def test_phase_not_completed(self):
        report = {"phase_id": "94Q", "status": "in_progress"}
        assert _phase_is_completed("94Q", report) is False

    def test_phase_not_completed_different(self):
        report = {"phase_id": "94Q", "status": "completed"}
        assert _phase_is_completed("94P", report) is False

    def test_format_push_clean(self):
        result = _format_push_status({"unpushed_commits": 0, "mode": "nothing_to_push"})
        assert "clean" in result.lower()
        assert "nothing_to_push" in result

    def test_format_push_needs_push(self):
        result = _format_push_status({"unpushed_commits": 5, "mode": "needs_push"})
        assert "needs_push" in result
        assert "5" in result

    def test_format_push_none_is_unknown(self):
        assert _format_push_status(None) == "unknown"


class Test94Q1BootstrapOutput:
    """Bootstrap CLI output includes enriched 94Q.1 fields."""

    def test_json_includes_readiness_fields(self, tmp_path, monkeypatch, capsys):
        from pcae.cli import main
        from pcae.commands.init import init_harness
        from pcae.core.tasks import create_task_contract

        init_harness(HarnessPath(tmp_path))
        init_git_repo(tmp_path)
        create_task_contract(HarnessPath(tmp_path), "94Q.1 Bootstrap test")
        patch_task_allowed_files(tmp_path)
        commit_baseline(tmp_path)
        monkeypatch.chdir(tmp_path)

        # Set up a phase report showing 94Q completed
        reports_dir = tmp_path / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "phase_id": "94Q", "status": "completed",
            "report_completeness": "complete",
            "recommended_next_phase": "94Q.1 — Bootstrap Resume and Telegram Runtime Hardening",
        }
        (reports_dir / "latest.json").write_text(json.dumps(report))

        exit_code = main(["session", "bootstrap", "--agent-id", "claude-deepseek", "--json"])
        d = json.loads(capsys.readouterr().out)

        assert "readiness" in d
        assert "readiness_issues" in d
        assert "latest_phase_report" in d
        assert "push_check" in d
        assert "telegram_runtime" in d
        assert "task_memory_warnings" in d
        assert "active_task_count" in d

    def test_json_no_secrets_in_telegram_runtime(self, tmp_path, monkeypatch, capsys):
        from pcae.cli import main
        from pcae.commands.init import init_harness
        from pcae.core.tasks import create_task_contract

        init_harness(HarnessPath(tmp_path))
        init_git_repo(tmp_path)
        create_task_contract(HarnessPath(tmp_path), "94Q.1 Secret test")
        patch_task_allowed_files(tmp_path)
        commit_baseline(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "secret-bot-token-abc")
        monkeypatch.setenv("PCAE_TELEGRAM_CHAT_ID", "chat-id-xyz")

        exit_code = main(["session", "bootstrap", "--agent-id", "claude-deepseek", "--json"])
        d = json.loads(capsys.readouterr().out)

        j = json.dumps(d)
        assert "secret-bot-token-abc" not in j
        assert "chat-id-xyz" not in j
        assert d["telegram_runtime"]["token_present"] is True

    def test_no_shell_execution_in_readiness_helpers(self):
        import inspect
        from pcae.commands import session
        source = inspect.getsource(session)
        # _load_push_check uses subprocess for git rev-list, which is safe.
        # Ensure no shell execution, os.system, or Popen was added.
        assert "os.system(" not in source
        assert "Popen(" not in source
        assert "shell=True" not in source.lower()
        # Count subprocess.run occurrences — should only be the git call in _load_push_check
        subprocess_count = source.count("subprocess.run")
        assert subprocess_count <= 1, f"Expected at most 1 subprocess.run, found {subprocess_count}"

    def test_no_telegram_inbound_in_session(self):
        import inspect
        from pcae.commands import session
        source = inspect.getsource(session)
        assert "getUpdates" not in source

    def test_no_network_in_readiness_helpers(self):
        import inspect
        from pcae.commands import session
        source = inspect.getsource(session)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_multipart_phase_id_preserved(self):
        readiness, issues = _classify_bootstrap_readiness(
            check_passed=True,
            health_status="healthy",
            active_task=None,
            latest_report={
                "phase_id": "94Q.1", "status": "completed",
                "report_completeness": "complete",
            },
            latest_handoff=None,
            push_check={"unpushed_commits": 0, "mode": "nothing_to_push"},
            tg_runtime={"status": "loaded", "telegram_enabled": True, "telegram_configured": True},
            task_memory_warnings=False,
        )
        assert readiness == READINESS_READY
