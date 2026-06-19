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
                "evolution_summary": "1 new",
                "calibration_state": "diversifying",
                "calibration_detail": "1 new concern(s) detected",
                "questions": [
                    {
                        "finding_id": "IRC-001-arch",
                        "domain": "architecture",
                        "attention_level": "medium_attention",
                        "question": "What counterfactual deserves attention?",
                    }
                ],
                "resolved_questions": [],
                "suppressed_count": 0,
                "footer": "Displayed for context only. Command outcomes stay unchanged.",
            },
            "comparative": {
                "new_concern_ids": ["IRC-001-arch"],
                "persistent_concern_ids": [],
                "resolved_concern_ids": [],
                "persistence_claims": {},
            },
        },
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "Completed Phase 32B"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Independent Challenge Context — advisory only" in output
    assert "1 new" in output


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


def test_phase_start_succeeds_in_idle_state(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "start", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    lock = read_agent_lock(root)
    assert lock is not None
    assert lock.agent_id == "claude-local"


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
                "evolution_summary": "2 new",
                "calibration_state": "diversifying",
                "calibration_detail": "2 new concern(s) across 2 domain(s)",
                "questions": [
                    {
                        "finding_id": "IRC-001-gov",
                        "domain": "governance",
                        "attention_level": "high_attention",
                        "question": "What assumption might be wrong?",
                    },
                    {
                        "finding_id": "IRC-001-cap",
                        "domain": "capability",
                        "attention_level": "medium_attention",
                        "question": "What blind spot exists?",
                    },
                ],
                "resolved_questions": [],
                "suppressed_count": 0,
                "footer": "Displayed for context only. Command outcomes stay unchanged.",
            },
            "comparative": {
                "new_concern_ids": ["IRC-001-gov", "IRC-001-cap"],
                "persistent_concern_ids": [],
                "resolved_concern_ids": [],
                "persistence_claims": {},
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
    expected_keys = {
        "active_task_id",
        "active_task_title",
        "auto_summary",
        "bootstrap_command",
        "branch",
        "check_passed",
        "check_status",
        "created_at",
        "explicit_next_agent",
        "governance_checkpoints",
        "handoff_id",
        "health_status",
        "latest_commit",
        "lifecycle_review",
        "manual_steps",
        "next_agent",
        "phase_queue_count",
        "phase_queue_next",
        "phase_queue_present",
        "provenance_event_count",
        "push_mode",
        "push_ready",
        "recent_commits",
        "recommendation_note",
        "recommendation_reason",
        "recommendation_used",
        "recommended_agent",
        "recommended_next_action",
        "released_agent",
        "restart_workflows",
        "strategic_continuity",
        "summary",
        "suggested_workflow",
        "task_memory_status",
        "task_state",
        "unpushed_commits",
        "workflow",
        "workflow_valid",
        "workflow_warnings",
        "work_type",
        "working_tree",
    }
    assert set(data.keys()) == expected_keys
    assert data["auto_summary"] is False
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
    assert exit_code == 0
    assert "Check: passed" in output
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


def test_phase_handoff_missing_next_agent_with_lock_defaults_to_holder(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--summary", "Self handoff"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Next agent: claude-local" in output
    lock = read_agent_lock(root)
    assert lock is not None
    assert lock.agent_id == "claude-local"


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
# Phase 70U: auto-summary and zero-argument handoff
# ---------------------------------------------------------------------------


def test_70u_handoff_without_summary_generates_auto_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Auto summary task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase handoff." in output
    assert "Summary: Phase handoff:" in output
    assert "branch=" in output
    assert "health=" in output
    assert "task=" in output


def test_70u_handoff_with_summary_uses_verbatim(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Verbatim summary task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "My custom summary", "--next-agent", "claude-next"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Summary: My custom summary" in output
    assert "Phase handoff:" not in output.split("Summary: ")[1].split("\n")[0]


def test_70u_handoff_zero_arguments_uses_current_lock_holder(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Zero args task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Next agent: claude-local" in output
    assert "Agent lock: acquired by claude-local" in output


def test_70u_handoff_no_lock_no_next_agent_prints_guidance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Please specify the next agent with --next-agent <agent-id>." in output


def test_70u_handoff_json_auto_summary_true(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "JSON auto task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["auto_summary"] is True
    assert "Phase handoff:" in data["summary"]
    assert "branch=" in data["summary"]


def test_70u_handoff_json_auto_summary_false_with_manual(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "JSON manual task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "Manual text", "--next-agent", "claude-next", "--json"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["auto_summary"] is False
    assert data["summary"] == "Manual text"


def test_70u_auto_summary_includes_review_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Review summary task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "review=" in output


def test_70u_auto_summary_includes_latest_commit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Commit summary task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "latest_commit=baseline" in output


def test_70u_auto_summary_idle_state(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "task=idle" in output


def test_70u_handoff_zero_arguments_persists_artifact(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Persist artifact task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff"])

    capsys.readouterr()
    assert exit_code == 0
    latest = tmp_path / ".pcae" / "handoffs" / "latest.json"
    assert latest.is_file()


def test_70u_handoff_default_next_agent_does_not_override_work_type(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Work type priority task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--work-type", "implementation"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Next agent: codex-local" in output


# ---------------------------------------------------------------------------
# Phase 70V: handoff artifact persistence
# ---------------------------------------------------------------------------


def test_70v_handoff_writes_latest_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Latest artifact task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next"])

    capsys.readouterr()
    assert exit_code == 0
    latest = tmp_path / ".pcae" / "handoffs" / "latest.json"
    assert latest.is_file()
    data = _json.loads(latest.read_text(encoding="utf-8"))
    assert data["auto_summary"] is True
    assert "handoff_id" in data
    assert data["next_agent"] == "claude-next"


def test_70v_handoff_writes_timestamped_artifact(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Timestamped artifact task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next"])

    capsys.readouterr()
    assert exit_code == 0
    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    timestamped_files = [f for f in handoffs_dir.iterdir() if f.name.startswith("handoff-")]
    assert len(timestamped_files) == 1


def test_70v_handoff_artifact_includes_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Fields artifact task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next"])

    capsys.readouterr()
    assert exit_code == 0
    latest = tmp_path / ".pcae" / "handoffs" / "latest.json"
    data = _json.loads(latest.read_text(encoding="utf-8"))
    required_fields = {
        "handoff_id", "created_at", "branch", "working_tree",
        "unpushed_commits", "task_state", "active_task_id",
        "active_task_title", "health_status", "check_passed",
        "task_memory_status", "push_ready", "push_mode",
        "lifecycle_review", "latest_commit", "recent_commits",
        "summary", "auto_summary", "next_agent",
        "bootstrap_command", "recommended_next_action",
    }
    assert required_fields.issubset(set(data.keys()))


def test_70v_handoff_manual_summary_persists_auto_false(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Manual persist task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--summary", "My manual summary", "--next-agent", "claude-next"]
    )

    capsys.readouterr()
    assert exit_code == 0
    latest = tmp_path / ".pcae" / "handoffs" / "latest.json"
    data = _json.loads(latest.read_text(encoding="utf-8"))
    assert data["auto_summary"] is False
    assert data["summary"] == "My manual summary"


def test_70v_handoff_json_consistent_with_artifact(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "JSON consistent task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["phase", "handoff", "--next-agent", "claude-next", "--json"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    json_output = _json.loads(output)
    latest = tmp_path / ".pcae" / "handoffs" / "latest.json"
    artifact = _json.loads(latest.read_text(encoding="utf-8"))
    assert json_output["handoff_id"] == artifact["handoff_id"]
    assert json_output["summary"] == artifact["summary"]
    assert json_output["auto_summary"] == artifact["auto_summary"]


def test_70v_handoff_show_displays_latest(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Show latest task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--next-agent", "claude-next"])
    capsys.readouterr()

    exit_code = main(["phase", "handoff-show"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Latest handoff artifact" in output
    assert "Handoff ID:" in output
    assert "Branch:" in output
    assert "Health:" in output
    assert "Bootstrap:" in output


def test_70v_handoff_show_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Show JSON task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--next-agent", "claude-next"])
    capsys.readouterr()

    exit_code = main(["phase", "handoff-show", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert "handoff_id" in data
    assert "summary" in data


def test_70v_handoff_show_no_artifact_reports_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff-show"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No handoff artifact found" in output


def test_70v_handoff_show_no_artifact_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff-show", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 1
    data = _json.loads(output)
    assert "error" in data


def test_70v_gitignore_template_includes_handoffs(
    tmp_path: Path,
) -> None:
    from pcae.core.templates import INIT_TEMPLATES

    gitignore_content = INIT_TEMPLATES[Path(".pcae/.gitignore")]
    assert "handoffs/" in gitignore_content


def test_70v_handoff_latest_updates_on_second_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Double handoff task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--summary", "First handoff", "--next-agent", "claude-next"])
    capsys.readouterr()

    main(["phase", "handoff", "--summary", "Second handoff", "--next-agent", "claude-next"])
    capsys.readouterr()

    latest = tmp_path / ".pcae" / "handoffs" / "latest.json"
    data = _json.loads(latest.read_text(encoding="utf-8"))
    assert data["summary"] == "Second handoff"

    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    timestamped_files = [f for f in handoffs_dir.iterdir() if f.name.startswith("handoff-")]
    assert len(timestamped_files) == 2


# ---------------------------------------------------------------------------
# Phase 70Y: phase queue planning command
# ---------------------------------------------------------------------------


def test_70y_queue_add(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "add", "70Z — Governed Multi-Phase Runner Design"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Added to phase queue (position 1)" in output
    assert "70Z" in output


def test_70y_queue_list(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase A"])
    main(["phase", "queue", "add", "Phase B"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase queue (2 entries):" in output
    assert "1. Phase A" in output
    assert "2. Phase B" in output


def test_70y_queue_list_empty(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase queue is empty." in output


def test_70y_queue_show_is_alias_for_list(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase X"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "show"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase queue (1 entries):" in output
    assert "Phase X" in output


def test_70y_queue_clear(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase A"])
    main(["phase", "queue", "add", "Phase B"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "clear"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Cleared 2 entries" in output

    exit_code2 = main(["phase", "queue", "list"])
    output2 = capsys.readouterr().out
    assert "Phase queue is empty." in output2


def test_70y_queue_add_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "add", "Phase J", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["added"] == "Phase J"
    assert data["position"] == 1
    assert data["queue_length"] == 1


def test_70y_queue_list_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase A"])
    main(["phase", "queue", "add", "Phase B"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "list", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["queue_length"] == 2
    assert data["queue"] == ["Phase A", "Phase B"]


def test_70y_queue_clear_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase A"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "clear", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["cleared"] == 1


def test_70y_queue_show_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase S"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "show", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["queue"] == ["Phase S"]


def test_70y_gitignore_template_includes_phase_queue(
    tmp_path: Path,
) -> None:
    from pcae.core.templates import INIT_TEMPLATES

    gitignore_content = INIT_TEMPLATES[Path(".pcae/.gitignore")]
    assert "phase-queue.json" in gitignore_content


# ---------------------------------------------------------------------------
# Phase 70X: handoff artifact hygiene
# ---------------------------------------------------------------------------


def _create_fake_handoff(tmp_path: Path, name: str) -> None:
    import json as _json

    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    data = {"handoff_id": name, "summary": f"fake {name}"}
    (handoffs_dir / f"{name}.json").write_text(
        _json.dumps(data), encoding="utf-8",
    )


def test_70x_prune_dry_run_reports_without_deleting(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    for i in range(5):
        _create_fake_handoff(tmp_path, f"handoff-2026061{i}T000000-000000-idle")

    exit_code = main(["phase", "handoff-prune", "--keep", "2", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Dry run" in output
    assert "would prune 3" in output
    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    assert len(list(handoffs_dir.glob("handoff-*.json"))) == 5


def test_70x_prune_apply_deletes_old_artifacts(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    for i in range(5):
        _create_fake_handoff(tmp_path, f"handoff-2026061{i}T000000-000000-idle")

    exit_code = main(["phase", "handoff-prune", "--keep", "2"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Pruned 3" in output
    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    remaining = sorted(f.name for f in handoffs_dir.glob("handoff-*.json"))
    assert len(remaining) == 2
    assert remaining[0] == "handoff-20260613T000000-000000-idle.json"
    assert remaining[1] == "handoff-20260614T000000-000000-idle.json"


def test_70x_prune_preserves_latest_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    (handoffs_dir / "latest.json").write_text('{"summary":"latest"}', encoding="utf-8")
    for i in range(3):
        _create_fake_handoff(tmp_path, f"handoff-2026061{i}T000000-000000-idle")

    exit_code = main(["phase", "handoff-prune", "--keep", "1"])

    capsys.readouterr()
    assert exit_code == 0
    assert (handoffs_dir / "latest.json").is_file()


def test_70x_prune_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    for i in range(4):
        _create_fake_handoff(tmp_path, f"handoff-2026061{i}T000000-000000-idle")

    exit_code = main(["phase", "handoff-prune", "--keep", "2", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["total"] == 4
    assert data["kept"] == 2
    assert len(data["pruned"]) == 2
    assert data["dry_run"] is False


def test_70x_prune_nothing_to_prune(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    for i in range(2):
        _create_fake_handoff(tmp_path, f"handoff-2026061{i}T000000-000000-idle")

    exit_code = main(["phase", "handoff-prune", "--keep", "5"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No handoff artifacts to prune" in output


def test_70x_prune_no_handoffs_dir(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff-prune"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No handoff artifacts found" in output


def test_70x_prune_dry_run_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    for i in range(3):
        _create_fake_handoff(tmp_path, f"handoff-2026061{i}T000000-000000-idle")

    exit_code = main(["phase", "handoff-prune", "--keep", "1", "--dry-run", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["dry_run"] is True
    assert len(data["pruned"]) == 2
    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    assert len(list(handoffs_dir.glob("handoff-*.json"))) == 3


# ---------------------------------------------------------------------------
# Phase queue readiness check (Phase 71E)
# ---------------------------------------------------------------------------


def test_71e_queue_check_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "add", "Phase 72A: test"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "ready" in output.lower()
    assert "Queue: 1 entries" in output


def test_71e_queue_check_no_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "no queue" in output.lower()


def test_71e_queue_check_empty_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text("[]", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "empty" in output.lower() or "no queue" in output.lower()


def test_71e_queue_check_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Blocking task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "add", "Phase 72A: test"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "active task exists" in output


def test_71e_queue_check_dirty_tree(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "add", "Phase 72A: test"])
    capsys.readouterr()
    (tmp_path / "dirty.txt").write_text("dirty", encoding="utf-8")

    exit_code = main(["phase", "queue", "check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "dirty" in output.lower()


def test_71e_queue_check_json_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "add", "Phase 72A: test"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "check", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["ready"] is True
    assert data["queue_present"] is True
    assert data["queue_length"] == 1
    assert data["next_queued"] == "Phase 72A: test"
    assert data["health_passed"] is True
    assert data["check_passed"] is True
    assert data["active_task"] is None
    assert data["task_memory_clean"] is True
    assert data["reasons"] == []


def test_71e_queue_check_json_not_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Blocking task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "add", "Phase 72A: test"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "check", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 1
    data = _json.loads(output)
    assert data["ready"] is False
    assert len(data["reasons"]) > 0


# ---------------------------------------------------------------------------
# Phase queue visibility in handoff (Phase 71D)
# ---------------------------------------------------------------------------


def test_71d_handoff_artifact_includes_queue_fields_when_queue_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Queue visibility task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "add", "Phase 72A: test phase"])
    capsys.readouterr()

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["phase_queue_present"] is True
    assert data["phase_queue_count"] == 1
    assert data["phase_queue_next"] == "Phase 72A: test phase"


def test_71d_handoff_artifact_queue_absent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "No queue task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["phase_queue_present"] is False
    assert data["phase_queue_count"] == 0
    assert data["phase_queue_next"] is None


def test_71d_handoff_show_displays_queue_when_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff show queue task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "add", "Phase 72B: next step"])
    capsys.readouterr()

    main(["phase", "handoff", "--next-agent", "claude-next"])
    capsys.readouterr()

    exit_code = main(["phase", "handoff-show"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase queue: 1 entries" in output
    assert "Next queued: Phase 72B: next step" in output


def test_71d_handoff_show_silent_when_no_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff show no queue task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--next-agent", "claude-next"])
    capsys.readouterr()

    exit_code = main(["phase", "handoff-show"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase queue" not in output


# ---------------------------------------------------------------------------
# pcae phase audit (Phase 71C)
# ---------------------------------------------------------------------------


def _create_phase_commits(root: Path, phase_id: str, description: str) -> None:
    dummy = root / "dummy.txt"
    dummy.write_text(f"impl {phase_id}", encoding="utf-8")
    run_git(root, "add", "dummy.txt")
    run_git(root, "commit", "-m", f"Implement Phase {phase_id} {description}")
    dummy.write_text(f"comp {phase_id}", encoding="utf-8")
    run_git(root, "add", "dummy.txt")
    run_git(root, "commit", "-m", f"Complete Phase {phase_id} {description}")


def test_71c_audit_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_phase_commits(tmp_path, "70A", "test feature alpha")
    _create_phase_commits(tmp_path, "70B", "test feature beta")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase Audit Report" in output
    assert "70A" in output
    assert "70B" in output
    assert "test feature alpha" in output
    assert "test feature beta" in output
    assert "complete" in output.lower()
    assert "Current State" in output


def test_71c_audit_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_phase_commits(tmp_path, "70A", "test feature alpha")
    _create_phase_commits(tmp_path, "70B", "test feature beta")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["phases_detected"] == 2
    assert isinstance(data["phases"], list)
    assert data["health_status"] in ("healthy", "unhealthy")
    assert "check_passed" in data
    assert "push_mode" in data
    assert "healthy_idle" in data
    assert "warnings" in data


def test_71c_audit_commit_pair_detection(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_phase_commits(tmp_path, "70A", "test feature alpha")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase = data["phases"][0]
    assert phase["phase_id"] == "70A"
    assert phase["implementation_commit"] is not None
    assert phase["completion_commit"] is not None
    assert phase["commit_pair_complete"] is True


def test_71c_audit_missing_pair_warning(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    dummy = tmp_path / "dummy.txt"
    dummy.write_text("impl only", encoding="utf-8")
    run_git(tmp_path, "add", "dummy.txt")
    run_git(tmp_path, "commit", "-m", "Implement Phase 70X test incomplete")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase = data["phases"][0]
    assert phase["phase_id"] == "70X"
    assert phase["implementation_commit"] is not None
    assert phase["completion_commit"] is None
    assert phase["commit_pair_complete"] is False
    assert any("70X" in w and "completion" in w for w in data["warnings"])


def test_71c_audit_missing_pair_human_warning(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    dummy = tmp_path / "dummy.txt"
    dummy.write_text("impl only", encoding="utf-8")
    run_git(tmp_path, "add", "dummy.txt")
    run_git(tmp_path, "commit", "-m", "Implement Phase 70X test incomplete")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "INCOMPLETE" in output
    assert "MISSING" in output
    assert "Warnings" in output


def test_71c_audit_last_flag(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_phase_commits(tmp_path, "70A", "alpha")
    _create_phase_commits(tmp_path, "70B", "beta")
    _create_phase_commits(tmp_path, "70C", "gamma")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--last", "2", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["phases_detected"] == 2


def test_71c_audit_since_flag(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_phase_commits(tmp_path, "70A", "alpha")
    _create_phase_commits(tmp_path, "70B", "beta")
    _create_phase_commits(tmp_path, "70C", "gamma")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--since", "70B", "--last", "100", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase_ids = [p["phase_id"] for p in data["phases"]]
    assert "70A" not in phase_ids
    assert "70B" in phase_ids
    assert "70C" in phase_ids


def test_71c_audit_no_phase_commits(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phases detected: 0" in output
    assert "No phase commits found" in output


def test_71c_audit_handoff_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    (handoffs_dir / "latest.json").write_text(
        _json.dumps({"summary": "test handoff summary"}), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["latest_handoff_summary"] == "test handoff summary"


def test_71c_audit_no_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["latest_handoff_summary"] is None


# ---------------------------------------------------------------------------
# Phase queue residue hygiene (Phase 71G)
# ---------------------------------------------------------------------------


def test_71g_hygiene_empty_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "hygiene"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "clean" in output.lower()
    assert "empty" in output.lower()


def test_71g_hygiene_empty_queue_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "hygiene", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_length"] == 0
    assert data["has_issues"] is False
    assert data["findings"] == []
    assert data["clearable_count"] == 0


def test_71g_hygiene_no_placeholders(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase 72A: implement auth module"])
    main(["phase", "queue", "add", "Phase 72B: add tests for auth"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "hygiene"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "clean" in output.lower()
    assert "no placeholders" in output.lower()


def test_71g_hygiene_detects_placeholders(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase 72A: test phase"])
    main(["phase", "queue", "add", "Phase 72B: real work"])
    main(["phase", "queue", "add", "Phase 72C: next step"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "hygiene"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "2 placeholder(s)" in output
    assert "test phase" in output
    assert "next step" in output


def test_71g_hygiene_detects_placeholders_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase 72A: test phase"])
    main(["phase", "queue", "add", "Phase 72B: real work"])
    main(["phase", "queue", "add", "dummy entry"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "hygiene", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_length"] == 3
    assert data["has_issues"] is True
    assert data["clearable_count"] == 2
    assert len(data["findings"]) == 2


def test_71g_hygiene_clear_requires_confirm(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "test phase"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "hygiene", "--clear-placeholders"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "--confirm" in output


def test_71g_hygiene_clear_requires_confirm_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "test phase"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "hygiene", "--clear-placeholders", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert "error" in data


def test_71g_hygiene_clear_placeholders_confirmed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase 72A: test phase"])
    main(["phase", "queue", "add", "Phase 72B: real work"])
    main(["phase", "queue", "add", "Phase 72C: next step"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "hygiene", "--clear-placeholders", "--confirm"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Cleared 2 placeholder(s)" in output
    assert "1 real entries remain" in output

    capsys.readouterr()
    main(["phase", "queue", "list"])
    list_output = capsys.readouterr().out
    assert "Phase 72B: real work" in list_output
    assert "test phase" not in list_output
    assert "next step" not in list_output


def test_71g_hygiene_clear_placeholders_confirmed_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "placeholder entry"])
    main(["phase", "queue", "add", "real phase work"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "hygiene", "--clear-placeholders", "--confirm", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["cleared"] == 1
    assert data["remaining"] == 1


def test_71g_hygiene_clear_no_placeholders_to_clear(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase 72A: real work"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "hygiene", "--clear-placeholders", "--confirm"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No placeholder entries" in output


def test_71g_hygiene_case_insensitive(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "TEST PHASE entry"])
    main(["phase", "queue", "add", "Placeholder Item"])
    main(["phase", "queue", "add", "DUMMY run"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "hygiene", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["clearable_count"] == 3


def test_71g_hygiene_real_entries_not_cleared(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase 72A: implement auth"])
    main(["phase", "queue", "add", "Phase 72B: test phase"])
    main(["phase", "queue", "add", "Phase 72C: add logging"])
    capsys.readouterr()

    main(["phase", "queue", "hygiene", "--clear-placeholders", "--confirm"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "list", "--json"])

    import json as _json

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_length"] == 2
    assert data["queue"] == ["Phase 72A: implement auth", "Phase 72C: add logging"]


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
