from __future__ import annotations

from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.agent import acquire_agent_lock, read_agent_lock
from pcae.core.paths import HarnessPath
from pcae.core.provenance import read_provenance_history
from pcae.core.tasks import create_task_contract


# ---------------------------------------------------------------------------
# pcae phase complete
# ---------------------------------------------------------------------------


def test_phase_complete_records_phase_completed_provenance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "Finished Phase 32A"])

    capsys.readouterr()
    assert exit_code == 0
    history = read_provenance_history(root)
    assert any(e.event_type == "phase_completed" for e in history.events)
    phase_event = next(e for e in history.events if e.event_type == "phase_completed")
    assert phase_event.summary == "Finished Phase 32A"


def test_phase_complete_releases_lock_and_records_agent_released(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "Phase done with lock"])

    capsys.readouterr()
    assert exit_code == 0
    assert read_agent_lock(root) is None
    history = read_provenance_history(root)
    event_types = [e.event_type for e in history.events]
    assert "phase_completed" in event_types
    assert "agent_released" in event_types


def test_phase_complete_without_lock_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "No lock held"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Agent lock: none" in output


def test_phase_complete_prints_summary_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "Completed Phase 32B"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase complete." in output
    assert "Summary: Completed Phase 32B" in output
    assert "Provenance events:" in output
    assert "Agent lock: none" in output


def test_phase_complete_with_lock_prints_released(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "Phase done"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Agent lock: released (by claude-local)" in output


def test_phase_complete_shows_independent_challenge_context(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.commands.phase as phase_commands

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.setattr(
        phase_commands,
        "build_irg_challenge_context",
        lambda harness_root: {
            "display_enabled": True,
            "compact_display": {
                "header": "Independent Challenge Context — advisory only",
                "summary": "1 question surfaced across architecture.",
                "questions": [
                    {
                        "domain": "architecture",
                        "attention_level": "medium_attention",
                        "question": "What counterfactual deserves attention?",
                    }
                ],
                "footer": "Displayed for context only. Command outcomes stay unchanged.",
            },
        },
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "Completed Phase 32B"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Independent Challenge Context — advisory only" in output
    assert "What counterfactual deserves attention?" in output


def test_phase_complete_phase_completed_captures_agent_id(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "complete", "--summary", "Lock held at record time"])

    capsys.readouterr()
    history = read_provenance_history(root)
    phase_event = next(e for e in history.events if e.event_type == "phase_completed")
    assert phase_event.agent_id == "claude-local"


# ---------------------------------------------------------------------------
# pcae phase start
# ---------------------------------------------------------------------------


def test_phase_start_acquires_agent_lock(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Phase start task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "start", "--agent-id", "claude-local"])

    capsys.readouterr()
    assert exit_code == 0
    lock = read_agent_lock(root)
    assert lock is not None
    assert lock.agent_id == "claude-local"


def test_phase_start_records_agent_acquired_provenance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Phase start task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "start", "--agent-id", "claude-local"])

    capsys.readouterr()
    history = read_provenance_history(root)
    assert any(e.event_type == "agent_acquired" for e in history.events)
    acquired = next(e for e in history.events if e.event_type == "agent_acquired")
    assert acquired.agent_id == "claude-local"


def test_phase_start_stops_when_check_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "start", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Phase start stopped: pcae check failed." in output
    assert "No active task contract found in tasks/active/." in output
    assert read_agent_lock(root) is None


def test_phase_start_stops_when_lock_already_held(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Phase lock task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "other-agent")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "start", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Agent lock already held by other-agent." in output


def test_phase_start_prints_active_task_and_timeline(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Timeline test task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "start", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase start." in output
    assert "Check: passed" in output
    assert "Active task:" in output
    assert "Title: Timeline test task" in output
    assert "Provenance events:" in output
    assert "Latest event:" in output


def test_phase_start_no_provenance_reports_none(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Fresh repo task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "start", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    # After start_phase, at least the agent_acquired event exists
    assert "Provenance events: 1" in output
    assert "Latest event: Agent lock acquired by claude-local" in output


# ---------------------------------------------------------------------------
# round-trip: phase start → phase complete
# ---------------------------------------------------------------------------


def test_phase_start_then_complete_round_trip(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Round trip task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    start_code = main(["phase", "start", "--agent-id", "claude-local"])
    capsys.readouterr()
    complete_code = main(["phase", "complete", "--summary", "Round trip done"])
    capsys.readouterr()

    assert start_code == 0
    assert complete_code == 0
    assert read_agent_lock(root) is None
    history = read_provenance_history(root)
    event_types = [e.event_type for e in history.events]
    assert event_types == ["agent_acquired", "phase_completed", "agent_released"]


# ---------------------------------------------------------------------------
# pcae phase handoff
# ---------------------------------------------------------------------------


def test_phase_handoff_records_phase_completed_provenance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "Phase done", "--next-agent", "claude-next"]
    )

    capsys.readouterr()
    assert exit_code == 0
    history = read_provenance_history(root)
    phase_events = [e for e in history.events if e.event_type == "phase_completed"]
    assert len(phase_events) == 1
    assert phase_events[0].summary == "Phase done"
    assert phase_events[0].agent_id == "claude-local"


def test_phase_handoff_runs_governance_validation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff validation task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "Validate governance", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Health: healthy" in output
    assert "Check: passed" in output


def test_phase_handoff_releases_current_lock(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff release task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--summary", "Release", "--next-agent", "claude-next"])

    capsys.readouterr()
    history = read_provenance_history(root)
    event_types = [e.event_type for e in history.events]
    assert "agent_released" in event_types
    released = next(e for e in history.events if e.event_type == "agent_released")
    assert released.agent_id == "claude-local"


def test_phase_handoff_acquires_next_agent_lock(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff acquire task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--summary", "Acquire next", "--next-agent", "claude-next"])

    capsys.readouterr()
    lock = read_agent_lock(root)
    assert lock is not None
    assert lock.agent_id == "claude-next"
    history = read_provenance_history(root)
    acquired = [e for e in history.events if e.event_type == "agent_acquired"]
    assert any(e.agent_id == "claude-next" for e in acquired)


def test_phase_handoff_prints_human_readable_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff output task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "32C complete", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase handoff." in output
    assert "Summary: 32C complete" in output
    assert "Health:" in output
    assert "Check:" in output
    assert "Provenance events:" in output
    assert "Released agent: claude-local" in output
    assert "Next agent: claude-next" in output
    assert "Agent lock: acquired by claude-next" in output
    assert "Manual handoff steps:" in output
    assert "Close or reset the current AI session if needed." in output
    assert "pcae session bootstrap --agent-id claude-next" in output
    assert "Bootstrap prompt (copy-ready):" in output
    assert "pcae session bootstrap --agent-id claude-next" in output


def test_phase_handoff_shows_independent_challenge_context(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.commands.phase as phase_commands

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff challenge task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.setattr(
        phase_commands,
        "build_irg_challenge_context",
        lambda harness_root: {
            "display_enabled": True,
            "compact_display": {
                "header": "Independent Challenge Context — advisory only",
                "summary": "2 questions surfaced across governance and capability.",
                "questions": [
                    {
                        "domain": "governance",
                        "attention_level": "high_attention",
                        "question": "What assumption might be wrong?",
                    },
                    {
                        "domain": "capability",
                        "attention_level": "medium_attention",
                        "question": "What blind spot exists?",
                    },
                ],
                "footer": "Displayed for context only. Command outcomes stay unchanged.",
            },
        },
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "32C complete", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Independent Challenge Context — advisory only" in output
    assert "What assumption might be wrong?" in output


def test_phase_lifecycle_challenge_independence_validation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import pcae.commands.phase as phase_commands

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Phase lifecycle independence task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    complete_scenarios = [
        None,
        {
            "display_enabled": True,
            "compact_display": {
                "header": "Independent Challenge Context — advisory only",
                "summary": "3 questions surfaced across governance, roadmap, and architecture.",
                "questions": [
                    {"domain": "governance", "attention_level": "high_attention", "question": "What changed?"},
                    {"domain": "roadmap", "attention_level": "medium_attention", "question": "What blind spot exists?"},
                    {"domain": "architecture", "attention_level": "critical_question", "question": "What counterfactual deserves attention?"},
                ],
                "footer": "Displayed for context only. Command outcomes stay unchanged.",
            },
        },
    ]
    for scenario in complete_scenarios:
        monkeypatch.setattr(
            phase_commands,
            "build_irg_challenge_context",
            (lambda harness_root, payload=scenario: payload),
        )
        exit_code = main(["phase", "complete", "--summary", "Phase done"])
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "Phase complete." in output
        assert "Summary: Phase done" in output

    acquire_agent_lock(root, "claude-local")
    handoff_scenarios = [
        None,
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
    for scenario in handoff_scenarios:
        monkeypatch.setattr(
            phase_commands,
            "build_irg_challenge_context",
            (lambda harness_root, payload=scenario: payload),
        )
        exit_code = main(
            ["phase", "handoff", "--summary", "Switch agents", "--next-agent", "claude-next"]
        )
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "Phase handoff." in output
        assert "Summary: Switch agents" in output


def test_phase_handoff_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff JSON task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "phase", "handoff",
            "--summary", "JSON handoff",
            "--next-agent", "claude-next",
            "--json",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["summary"] == "JSON handoff"
    assert data["released_agent"] == "claude-local"
    assert data["next_agent"] == "claude-next"
    assert data["health_status"] in {"healthy", "unhealthy"}
    assert data["check_status"] in {"passed", "failed"}
    assert isinstance(data["provenance_event_count"], int)
    assert isinstance(data["manual_steps"], list)
    assert len(data["manual_steps"]) == 4
    assert any("pcae session bootstrap --agent-id claude-next" in s for s in data["manual_steps"])
    assert isinstance(data["restart_workflows"], list)
    assert len(data["restart_workflows"]) == 3
    assert set(data.keys()) == {
        "check_status",
        "explicit_next_agent",
        "health_status",
        "manual_steps",
        "next_agent",
        "provenance_event_count",
        "recommendation_note",
        "recommendation_reason",
        "recommendation_used",
        "recommended_agent",
        "released_agent",
        "restart_workflows",
        "strategic_continuity",
        "summary",
        "suggested_workflow",
        "workflow",
        "workflow_valid",
        "workflow_warnings",
        "governance_checkpoints",
        "work_type",
    }
    # no --work-type: recommendation fields are null/false
    assert data["work_type"] is None
    assert data["recommended_agent"] is None
    assert data["recommendation_reason"] is None
    assert data["recommendation_used"] is False
    assert "advisory" in data["recommendation_note"]
    assert data["suggested_workflow"] is None
    assert data["workflow"] is None
    assert data["workflow_valid"] is None
    assert data["workflow_warnings"] == []
    assert data["governance_checkpoints"] == []
    assert data["explicit_next_agent"] == "claude-next"


def test_phase_handoff_without_current_lock(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff no lock task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "No lock", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Released agent: none" in output
    assert "Agent lock: acquired by claude-next" in output
    lock = read_agent_lock(root)
    assert lock is not None
    assert lock.agent_id == "claude-next"


def test_phase_handoff_full_event_sequence(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff sequence task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(
        ["phase", "handoff", "--summary", "Full sequence", "--next-agent", "claude-next"]
    )

    capsys.readouterr()
    history = read_provenance_history(root)
    event_types = [e.event_type for e in history.events]
    assert event_types == [
        "phase_completed",
        "agent_released",
        "agent_acquired",
    ]


def test_phase_handoff_check_failure_still_completes_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    # No task contract → check will fail
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "Bad state handoff", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    # Handoff still completes (lock acquired, provenance recorded) despite check failure
    assert exit_code == 0
    assert "Check: failed" in output
    assert "Health: unhealthy" in output
    history = read_provenance_history(root)
    assert any(e.event_type == "phase_completed" for e in history.events)
    assert any(e.event_type == "agent_acquired" for e in history.events)
    lock = read_agent_lock(root)
    assert lock is not None
    assert lock.agent_id == "claude-next"


# ---------------------------------------------------------------------------
# Phase 32E: user-friendly handoff guidance
# ---------------------------------------------------------------------------


def test_phase_handoff_missing_next_agent_prints_guidance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--summary", "Missing next agent"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Please specify the next agent with --next-agent <agent-id>." in output


def test_phase_handoff_human_output_includes_manual_steps(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff steps task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "Steps test", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Manual handoff steps:" in output
    assert "1. Close or reset the current AI session if needed." in output
    assert "2." in output
    assert "pcae session bootstrap --agent-id claude-next" in output
    assert "3." in output
    assert "4." in output


def test_phase_handoff_human_output_includes_bootstrap_prompt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff prompt task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "Prompt test", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Bootstrap prompt (copy-ready):" in output
    assert "pcae session bootstrap --agent-id claude-next" in output
    assert "governed engineering session" in output
    assert "─" in output


def test_phase_handoff_json_includes_manual_steps_with_correct_agent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff manual steps JSON task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "phase", "handoff",
            "--summary", "Manual steps JSON",
            "--next-agent", "claude-next",
            "--json",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    steps = data["manual_steps"]
    assert isinstance(steps, list)
    assert len(steps) == 4
    assert steps[0] == "Close or reset the current AI session if needed."
    assert "pcae session bootstrap --agent-id claude-next" in steps[1]
    assert "bootstrap prompt" in steps[2].lower()
    assert "phase prompt" in steps[3].lower()


# ---------------------------------------------------------------------------
# Phase 32F: multi-agent governed bootstrap guidance
# ---------------------------------------------------------------------------


def test_phase_handoff_output_includes_claude_cli_example(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Restart workflows task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "32F test", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Example restart workflows:" in output
    assert "Claude CLI:" in output
    assert "claude" in output


def test_phase_handoff_output_includes_codex_desktop_example(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Codex restart task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "Codex test", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Codex Desktop:" in output
    assert "pcae session bootstrap --agent-id codex-local" in output


def test_phase_handoff_output_includes_generic_agent_example(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Generic agent task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "Generic test", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Generic governed agent:" in output
    assert "pcae session bootstrap --agent-id <agent-id>" in output


def test_phase_handoff_bootstrap_prompt_remains_generic(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Generic prompt task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "Prompt generic", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Bootstrap prompt (copy-ready):" in output
    assert "governed engineering session" in output
    assert "governed engineering session in the PCAE harness" in output


def test_phase_handoff_json_restart_workflows_structure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Restart workflows JSON task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "phase", "handoff",
            "--summary", "Workflows JSON",
            "--next-agent", "claude-next",
            "--json",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    workflows = data["restart_workflows"]
    assert len(workflows) == 3
    agent_names = [w["agent"] for w in workflows]
    assert "Claude CLI" in agent_names
    assert "Codex Desktop" in agent_names
    assert "Generic governed agent" in agent_names
    for w in workflows:
        assert isinstance(w["steps"], list)
        assert len(w["steps"]) >= 2
    codex = next(w for w in workflows if w["agent"] == "Codex Desktop")
    assert any("codex-local" in s for s in codex["steps"])
    generic = next(w for w in workflows if w["agent"] == "Generic governed agent")
    assert any("<agent-id>" in s for s in generic["steps"])


def test_phase_handoff_missing_next_agent_does_not_mutate_state(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.provenance import read_provenance_history

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--summary", "No mutation"])

    capsys.readouterr()
    # Lock still held, no provenance events recorded
    from pcae.core.agent import read_agent_lock
    assert read_agent_lock(root) is not None
    history = read_provenance_history(root)
    assert len(history.events) == 0


# ---------------------------------------------------------------------------
# pcae phase handoff --work-type (Phase 33D)
# ---------------------------------------------------------------------------


def test_phase_handoff_work_type_documentation_uses_claude_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33D doc task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "doc handoff", "--work-type", "documentation"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Next agent: claude-local" in output
    assert "Recommended agent: claude-local" in output
    assert "Recommendations are advisory; the user may override them." in output
    assert "Suggested next workflow: documentation" in output


def test_phase_handoff_work_type_implementation_uses_codex_local(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33D impl task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "impl handoff", "--work-type", "implementation"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Next agent: codex-local" in output
    assert "Recommended agent: codex-local" in output
    assert "Agent lock: acquired by codex-local" in output


def test_phase_handoff_work_type_shows_reason_in_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33D reason task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--summary", "reason test", "--work-type", "documentation"])

    output = capsys.readouterr().out
    assert "Reason:" in output
    assert "documentation" in output


def test_phase_handoff_explicit_next_agent_overrides_work_type(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33D override task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "phase", "handoff",
            "--summary", "override",
            "--work-type", "documentation",
            "--next-agent", "codex-local",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Next agent: codex-local" in output
    assert "Agent lock: acquired by codex-local" in output


def test_phase_handoff_both_flags_shows_recommendation_and_override_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33D both flags task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(
        [
            "phase", "handoff",
            "--summary", "both flags",
            "--work-type", "documentation",
            "--next-agent", "codex-local",
        ]
    )

    output = capsys.readouterr().out
    assert "Recommended agent: claude-local" in output
    assert "User override: explicit --next-agent is being used" in output
    assert "Next agent: codex-local" in output


def test_phase_handoff_both_flags_matching_shows_matches_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33D match task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(
        [
            "phase", "handoff",
            "--summary", "match",
            "--work-type", "documentation",
            "--next-agent", "claude-local",
        ]
    )

    output = capsys.readouterr().out
    assert "Recommended agent: claude-local" in output
    assert "User override: explicit --next-agent matches recommendation." in output


def test_phase_handoff_work_type_json_includes_recommendation_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33D JSON task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "phase", "handoff",
            "--summary", "JSON rec",
            "--work-type", "documentation",
            "--json",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["work_type"] == "documentation"
    assert data["recommended_agent"] == "claude-local"
    assert data["recommendation_reason"] is not None
    assert "documentation" in data["recommendation_reason"]
    assert data["recommendation_used"] is True
    assert data["suggested_workflow"]["workflow"] == "documentation"
    assert data["suggested_workflow"]["execution_mode"] == "simulation"
    assert data["explicit_next_agent"] is None
    assert data["next_agent"] == "claude-local"


def test_phase_handoff_work_type_json_override_sets_recommendation_used_false(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33D JSON override task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "phase", "handoff",
            "--summary", "JSON override",
            "--work-type", "documentation",
            "--next-agent", "codex-local",
            "--json",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["work_type"] == "documentation"
    assert data["recommended_agent"] == "claude-local"
    assert data["recommendation_used"] is False
    assert data["explicit_next_agent"] == "codex-local"
    assert data["next_agent"] == "codex-local"


def test_phase_handoff_work_type_acquires_recommended_agent_lock(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.agent import read_agent_lock

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33D lock task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(
        ["phase", "handoff", "--summary", "lock check", "--work-type", "implementation"]
    )
    capsys.readouterr()

    lock = read_agent_lock(root)
    assert lock is not None
    assert lock.agent_id == "codex-local"


def test_phase_handoff_work_type_missing_both_still_shows_guidance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--summary", "no agent"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Please specify the next agent with --next-agent <agent-id>." in output


# ---------------------------------------------------------------------------
# pcae phase handoff --workflow (Phase 33I)
# ---------------------------------------------------------------------------


def test_phase_handoff_workflow_implementation_shows_validation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33I workflow task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "phase", "handoff",
            "--summary", "workflow validation",
            "--workflow", "implementation",
            "--next-agent", "codex-local",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Workflow validation:" in output
    assert "Workflow: implementation" in output
    assert "Result: valid" in output
    assert "Governance checkpoints:" in output
    assert "pcae check" in output
    assert "Recommendations remain advisory" in output


def test_phase_handoff_workflow_release_json_includes_validation_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33I release JSON task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "phase", "handoff",
            "--summary", "release workflow json",
            "--workflow", "release",
            "--next-agent", "pcae-native",
            "--json",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["workflow"] == "release"
    assert data["workflow_valid"] is True
    assert data["workflow_warnings"] == []
    assert any(
        entry["checkpoint"] == "pcae provenance session current"
        for entry in data["governance_checkpoints"]
    )


def test_phase_handoff_work_type_and_workflow_both_work(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33I combined task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "phase", "handoff",
            "--summary", "combined",
            "--work-type", "implementation",
            "--workflow", "implementation",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Recommended agent: codex-local" in output
    assert "Workflow validation:" in output
    assert "Workflow: implementation" in output
    assert "Agent lock: acquired by codex-local" in output


def test_phase_handoff_workflow_with_explicit_override_remains_authoritative(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "33I override task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "phase", "handoff",
            "--summary", "override workflow",
            "--work-type", "documentation",
            "--workflow", "documentation",
            "--next-agent", "codex-local",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Recommended agent: claude-local" in output
    assert "User override: explicit --next-agent is being used" in output
    assert "Next agent: codex-local" in output
    assert "Workflow validation:" in output


# ---------------------------------------------------------------------------
# helpers
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
