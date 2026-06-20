from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

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
        "activation",
        "active_task_id",
        "active_task_title",
        "audit_summary",
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
        "prompt_summary",
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


# Phase 71T — Audit Commit Pair Classification Flexibility
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("verb", ["Implement", "Document", "Design", "Add", "Refine"])
def test_71t_audit_recognizes_implementation_verbs(
    tmp_path: Path, monkeypatch, capsys, verb: str
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    dummy = tmp_path / "dummy.txt"
    dummy.write_text(f"impl {verb}", encoding="utf-8")
    run_git(tmp_path, "add", "dummy.txt")
    run_git(tmp_path, "commit", "-m", f"{verb} Phase 80A test {verb.lower()} phase")
    dummy.write_text(f"comp {verb}", encoding="utf-8")
    run_git(tmp_path, "add", "dummy.txt")
    run_git(tmp_path, "commit", "-m", f"Complete Phase 80A test {verb.lower()} phase")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase = data["phases"][0]
    assert phase["phase_id"] == "80A"
    assert phase["implementation_commit"] is not None
    assert phase["completion_commit"] is not None
    assert phase["commit_pair_complete"] is True
    assert not any("80A" in w for w in data["warnings"])


def test_71t_complete_not_classified_as_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    dummy = tmp_path / "dummy.txt"
    dummy.write_text("comp only", encoding="utf-8")
    run_git(tmp_path, "add", "dummy.txt")
    run_git(tmp_path, "commit", "-m", "Complete Phase 80B closure only phase")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase = data["phases"][0]
    assert phase["phase_id"] == "80B"
    assert phase["implementation_commit"] is None
    assert phase["completion_commit"] is not None
    assert phase["commit_pair_complete"] is False
    assert any("80B" in w and "implementation" in w for w in data["warnings"])


def test_71t_missing_impl_still_warns(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    dummy = tmp_path / "dummy.txt"
    dummy.write_text("comp only", encoding="utf-8")
    run_git(tmp_path, "add", "dummy.txt")
    run_git(tmp_path, "commit", "-m", "Complete Phase 80C genuinely missing impl")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert any("80C" in w and "implementation" in w for w in data["warnings"])


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
# Autonomy audit visibility in handoff (Phase 71I)
# ---------------------------------------------------------------------------


def _write_audit_artifact(root: Path, audit: dict) -> None:
    import json as _json

    audit_dir = root / ".pcae" / "phase-audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "latest.json").write_text(
        _json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8",
    )


def test_71i_handoff_artifact_includes_audit_when_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Audit handoff task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T060000Z",
        "phases_detected": 4,
        "warnings": ["Phase 71X: missing completion commit"],
        "healthy_idle": True,
    })
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["audit_summary"]["present"] is True
    assert data["audit_summary"]["phases_detected"] == 4
    assert data["audit_summary"]["warning_count"] == 1
    assert data["audit_summary"]["healthy_idle"] is True
    assert data["audit_summary"]["created_at"] == "20260619T060000Z"


def test_71i_handoff_artifact_audit_absent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "No audit handoff task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = _json.loads(output)
    assert data["audit_summary"] is None


def test_71i_handoff_show_displays_audit_when_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff show audit task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    _write_audit_artifact(tmp_path, {
        "created_at": "20260619T070000Z",
        "phases_detected": 3,
        "warnings": [],
        "healthy_idle": True,
    })
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--next-agent", "claude-next"])
    capsys.readouterr()

    exit_code = main(["phase", "handoff-show"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Audit:" in output
    assert "3 phases" in output
    assert "0 warnings" in output


def test_71i_handoff_show_no_audit_line_when_absent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff show no audit task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--next-agent", "claude-next"])
    capsys.readouterr()

    exit_code = main(["phase", "handoff-show"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Audit:" not in output


# ---------------------------------------------------------------------------
# Autonomy audit artifact persistence (Phase 71H)
# ---------------------------------------------------------------------------


def test_71h_audit_save_creates_artifacts(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--last", "4", "--save"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Audit saved:" in output
    assert "Timestamped:" in output

    latest = tmp_path / ".pcae" / "phase-audits" / "latest.json"
    assert latest.is_file()

    import json as _json

    data = _json.loads(latest.read_text(encoding="utf-8"))
    assert "created_at" in data
    assert "phases_detected" in data

    audit_files = list((tmp_path / ".pcae" / "phase-audits").glob("audit-*.json"))
    assert len(audit_files) == 1


def test_71h_audit_save_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--last", "4", "--save", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["saved"] is True
    assert "latest_path" in data
    assert "timestamped_path" in data


def test_71h_audit_save_timestamped_artifact(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "audit", "--last", "2", "--save"])
    capsys.readouterr()

    audit_dir = tmp_path / ".pcae" / "phase-audits"
    ts_files = sorted(audit_dir.glob("audit-*.json"))
    assert len(ts_files) == 1

    data = _json.loads(ts_files[0].read_text(encoding="utf-8"))
    assert "created_at" in data
    assert data["created_at"] in ts_files[0].name


def test_71h_audit_show_human(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "audit", "--last", "4", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "audit-show"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Saved Phase Audit" in output
    assert "Created:" in output
    assert "Phases detected:" in output


def test_71h_audit_show_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "audit", "--last", "4", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "audit-show", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "created_at" in data
    assert "phases_detected" in data


def test_71h_audit_show_missing_artifact(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit-show"])

    output = capsys.readouterr().err
    assert exit_code == 1
    assert "No saved audit artifact found" in output


def test_71h_audit_without_save_does_not_persist(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "audit", "--last", "4"])
    capsys.readouterr()

    audit_dir = tmp_path / ".pcae" / "phase-audits"
    assert not audit_dir.exists() or not (audit_dir / "latest.json").exists()


def test_71h_gitignore_includes_phase_audits(
    tmp_path: Path, monkeypatch,
) -> None:
    init_harness(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    gitignore_content = (tmp_path / ".pcae" / ".gitignore").read_text(encoding="utf-8")
    assert "phase-audits/" in gitignore_content


def test_71h_gitignore_template_includes_phase_audits() -> None:
    from pcae.core.templates import INIT_TEMPLATES

    gitignore_template = INIT_TEMPLATES[Path(".pcae/.gitignore")]
    assert "phase-audits/" in gitignore_template


def test_71h_audit_show_missing_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit-show", "--json"])

    output = capsys.readouterr().err
    assert exit_code == 1
    assert "No saved audit artifact found" in output


# Phase 71W — Audit Handoff Summary Freshness
# ---------------------------------------------------------------------------


def test_71w_audit_show_json_includes_freshness_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "audit", "--last", "4", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "audit-show", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "current_handoff_summary" in data
    assert "current_handoff_created_at" in data
    assert "handoff_summary_stale" in data


def test_71w_audit_show_detects_stale_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)

    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    old_handoff = {"summary": "Old handoff", "created_at": "2026-01-01T00:00:00Z"}
    (handoffs_dir / "latest.json").write_text(
        _json.dumps(old_handoff), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    main(["phase", "audit", "--last", "4", "--save"])
    capsys.readouterr()

    new_handoff = {"summary": "New handoff", "created_at": "2026-06-19T00:00:00Z"}
    (handoffs_dir / "latest.json").write_text(
        _json.dumps(new_handoff), encoding="utf-8"
    )

    exit_code = main(["phase", "audit-show", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["latest_handoff_summary"] == "Old handoff"
    assert data["current_handoff_summary"] == "New handoff"
    assert data["handoff_summary_stale"] is True


def test_71w_audit_show_not_stale_when_matching(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)

    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    handoff = {"summary": "Same handoff", "created_at": "2026-06-19T00:00:00Z"}
    (handoffs_dir / "latest.json").write_text(
        _json.dumps(handoff), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    main(["phase", "audit", "--last", "4", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "audit-show", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["latest_handoff_summary"] == "Same handoff"
    assert data["current_handoff_summary"] == "Same handoff"
    assert data["handoff_summary_stale"] is False


def test_71w_audit_show_human_stale_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)

    handoffs_dir = tmp_path / ".pcae" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    old_handoff = {"summary": "Old summary", "created_at": "2026-01-01T00:00:00Z"}
    (handoffs_dir / "latest.json").write_text(
        _json.dumps(old_handoff), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    main(["phase", "audit", "--last", "4", "--save"])
    capsys.readouterr()

    new_handoff = {"summary": "New summary", "created_at": "2026-06-19T00:00:00Z"}
    (handoffs_dir / "latest.json").write_text(
        _json.dumps(new_handoff), encoding="utf-8"
    )

    exit_code = main(["phase", "audit-show"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "at audit" in output
    assert "current" in output
    assert "Old summary" in output
    assert "New summary" in output


# Phase 71Y — Autonomy Comparison Run Summary Artifact
# ---------------------------------------------------------------------------


def test_71y_autonomy_summary_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "autonomy-summary"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Autonomy Run Summary" in output
    assert "Phases detected:" in output
    assert "agent" in output.lower() or "Note:" in output


def test_71y_autonomy_summary_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "autonomy-summary", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "phases_detected" in data
    assert "warning_count" in data
    assert "health_status" in data
    assert "push_status" in data
    assert "agent_neutral_note" in data
    assert "recovery_commands_observed" in data
    assert "working_tree" in data


def test_71y_autonomy_summary_save(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "autonomy-summary", "--save"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "saved" in output.lower()

    latest_path = tmp_path / ".pcae" / "autonomy-summaries" / "latest.json"
    assert latest_path.exists()
    data = _json.loads(latest_path.read_text(encoding="utf-8"))
    assert "created_at" in data
    assert "phases_detected" in data

    gitignore = tmp_path / ".pcae" / "autonomy-summaries" / ".gitignore"
    assert gitignore.exists()


def test_71y_autonomy_summary_missing_artifacts(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "autonomy-summary", "--json"])

    import json as _json
    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["phases_detected"] == 0
    assert data["latest_completed_phase"] is None
    assert data["latest_handoff_summary"] is None


def test_71y_autonomy_summary_with_audit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_phase_commits(tmp_path, "80A", "test feature alpha")
    monkeypatch.chdir(tmp_path)

    main(["phase", "audit", "--last", "4", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "autonomy-summary", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["phases_detected"] >= 1
    assert data["latest_completed_phase"] == "80A"


# Phase 71Z — Phase Queue Runner Readiness Contract
# ---------------------------------------------------------------------------


def test_71z_runner_readiness_clean_idle(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-readiness", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["environment_ready"] is True
    assert data["queue_ready"] is False
    assert data["runner_ready"] is False
    assert data["blocking_reasons"] == []
    assert data["working_tree"] == "clean"
    assert data["health_status"] == "healthy"
    assert data["check_passed"] is True
    assert data["task_memory_status"] == "clean"
    assert data["active_task"] is None


def test_71z_runner_readiness_with_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Test phase item"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-readiness", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["environment_ready"] is True
    assert data["queue_ready"] is True
    assert data["runner_ready"] is True
    assert data["queue_length"] >= 1


def test_71z_runner_readiness_dirty_tree(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-readiness", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["environment_ready"] is False
    assert data["runner_ready"] is False
    assert any("dirty" in r for r in data["blocking_reasons"])


def test_71z_runner_readiness_active_task_blocks(
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

    exit_code = main(["phase", "runner-readiness", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["environment_ready"] is False
    assert data["active_task"] is not None
    assert any("active task" in r for r in data["blocking_reasons"])


def test_71z_runner_readiness_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-readiness"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Environment ready:" in output
    assert "Queue ready:" in output
    assert "Runner ready:" in output


# Phase 72A — Bounded Phase Runner Dry-Run Planner
# ---------------------------------------------------------------------------


def test_72a_runner_plan_empty_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-plan", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["executable"] is False
    assert data["planned_phases"] == []
    assert data["max_phases"] == 1
    assert "stop_conditions" in data
    assert "validation_sequence" in data
    assert "recovery_path" in data
    assert "No execution" in data["note"]


def test_72a_runner_plan_with_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase alpha"])
    main(["phase", "queue", "add", "Phase beta"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-plan", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["executable"] is True
    assert len(data["planned_phases"]) == 1
    assert data["planned_phases"][0]["title"] == "Phase alpha"


def test_72a_runner_plan_max_phases(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase A"])
    main(["phase", "queue", "add", "Phase B"])
    main(["phase", "queue", "add", "Phase C"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-plan", "--max-phases", "2", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["max_phases"] == 2
    assert len(data["planned_phases"]) == 2


def test_72a_runner_plan_max_clamped(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    for i in range(5):
        main(["phase", "queue", "add", f"Phase {i}"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-plan", "--max-phases", "10", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["max_phases"] == 3
    assert len(data["planned_phases"]) <= 3


def test_72a_runner_plan_not_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Phase blocked"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-plan", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["executable"] is False
    assert len(data["blockers"]) > 0
    assert data["planned_phases"] == []


def test_72a_runner_plan_does_not_mutate_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Immutable phase"])
    capsys.readouterr()

    main(["phase", "runner-plan", "--json"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "list", "--json"])
    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_length"] == 1


def test_72a_runner_plan_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-plan"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "dry-run" in output.lower()
    assert "No execution performed" in output
    assert "Stop conditions:" in output
    assert "Recovery path:" in output


# Phase 72B — Runner Stop-Condition Policy Matrix
# ---------------------------------------------------------------------------


def test_72b_runner_policy_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-policy"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Hard Stop" in output
    assert "Recoverable Stop" in output
    assert "Advisory Warning" in output
    assert "Continue Allowed" in output
    assert "Human authority is absolute" in output


def test_72b_runner_policy_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-policy", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "policy_matrix" in data
    assert "categories" in data
    assert "human_authority_note" in data
    assert len(data["policy_matrix"]) >= 16

    categories = {e["category"] for e in data["policy_matrix"]}
    assert "hard_stop" in categories
    assert "recoverable_stop" in categories
    assert "advisory_warning" in categories
    assert "continue_allowed" in categories


def test_72b_runner_policy_contains_recovery_guidance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-policy", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0

    recoverable = [e for e in data["policy_matrix"] if e["category"] == "recoverable_stop"]
    assert any("task finish recover" in e["guidance"] for e in recoverable)
    assert any("doctor git-lock" in e["guidance"] for e in recoverable)


def test_72b_runner_policy_matrix_entries_have_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-policy", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0

    for entry in data["policy_matrix"]:
        assert "condition" in entry
        assert "category" in entry
        assert "guidance" in entry
        assert entry["category"] in data["categories"]


# Phase 72C — Runner Simulation Fixture Queue
# ---------------------------------------------------------------------------


def test_72c_sim_fixture_default_count(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-sim-fixture", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["count"] == 3
    assert len(data["entries"]) == 3
    assert data["real_queue_mutated"] is False
    assert data["entries"][0]["phase_id"] == "SIM-001"
    assert data["entries"][0]["simulated"] is True


def test_72c_sim_fixture_custom_count(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-sim-fixture", "--count", "5", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["count"] == 5
    assert data["entries"][-1]["phase_id"] == "SIM-005"


def test_72c_sim_fixture_clamped(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-sim-fixture", "--count", "50", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["count"] == 10


def test_72c_sim_fixture_does_not_mutate_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-sim-fixture", "--json"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "list", "--json"])
    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_length"] == 0


def test_72c_sim_fixture_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-sim-fixture"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "SIM-001" in output
    assert "Real queue mutated: no" in output


# Phase 72D — Runner Simulation Trace Artifact
# ---------------------------------------------------------------------------


def test_72d_runner_simulate_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-simulate", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["would_execute"] is False
    assert data["mutation_performed"] is False
    assert len(data["simulated_entries"]) == 3
    assert "readiness" in data
    assert "policy_summary" in data
    assert "stop_conditions_considered" in data
    assert data["readiness"]["environment_ready"] is True
    assert len(data["planned_phases"]) == 3


def test_72d_runner_simulate_save(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-simulate", "--save"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "saved" in output.lower()

    latest = tmp_path / ".pcae" / "runner-simulations" / "latest.json"
    assert latest.exists()
    data = _json.loads(latest.read_text(encoding="utf-8"))
    assert "created_at" in data
    assert data["would_execute"] is False


def test_72d_runner_simulate_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-simulate", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["readiness"]["environment_ready"] is False
    assert data["planned_phases"] == []
    assert data["first_planned_phase"] is None


def test_72d_runner_simulate_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-simulate"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "dry-run" in output.lower()
    assert "Would execute: no" in output
    assert "Mutation performed: no" in output


def test_72d_runner_simulate_does_not_mutate_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-simulate", "--json"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "list", "--json"])
    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_length"] == 0


# Phase 72E — Runner Simulation Failure Cases
# ---------------------------------------------------------------------------


def test_72e_scenario_dirty_tree(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-simulate", "--scenario", "dirty-tree", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["scenario"] == "dirty-tree"
    assert data["policy_category"] == "hard_stop"
    assert data["runner_would_continue"] is False


def test_72e_scenario_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-simulate", "--scenario", "active-task", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["policy_category"] == "hard_stop"
    assert data["runner_would_continue"] is False


def test_72e_scenario_git_lock(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-simulate", "--scenario", "git-lock", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["policy_category"] == "recoverable_stop"
    assert data["runner_would_continue"] is False
    assert "doctor git-lock" in data["suggested_action"]


def test_72e_scenario_audit_warning(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-simulate", "--scenario", "audit-warning", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["policy_category"] == "advisory_warning"
    assert data["runner_would_continue"] is True


def test_72e_scenario_queue_empty(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-simulate", "--scenario", "queue-empty", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["policy_category"] == "continue_allowed"
    assert data["runner_would_continue"] is True


def test_72e_scenario_unknown(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-simulate", "--scenario", "nonexistent"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Unknown scenario" in output


def test_72e_scenario_does_not_mutate_repo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    for scenario in ["dirty-tree", "active-task", "git-lock", "audit-warning", "queue-empty"]:
        main(["phase", "runner-simulate", "--scenario", scenario, "--json"])
        capsys.readouterr()

    exit_code = main(["phase", "queue", "list", "--json"])
    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_length"] == 0

    lock_path = tmp_path / ".git" / "index.lock"
    assert not lock_path.exists()


def test_72e_scenario_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-simulate", "--scenario", "dirty-tree"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Failure Scenario" in output
    assert "hard_stop" in output
    assert "Runner would continue: NO" in output
    assert "Simulated failure only" in output


# Phase 72F — Runner Simulation Review Artifact
# ---------------------------------------------------------------------------


def test_72f_sim_review_missing_simulation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-sim-review", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["review_status"] == "missing_simulation"
    assert data["simulation_present"] is False
    assert any("runner-simulate --save" in r for r in data["review_reasons"])


def test_72f_sim_review_with_simulation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-simulate", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-sim-review", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["review_status"] == "ready_for_approval"
    assert data["simulation_present"] is True
    assert data["would_execute"] is False
    assert data["mutation_performed"] is False


def test_72f_sim_review_save(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-simulate", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-sim-review", "--save"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "saved" in output.lower()

    latest = tmp_path / ".pcae" / "runner-simulation-reviews" / "latest.json"
    assert latest.exists()
    data = _json.loads(latest.read_text(encoding="utf-8"))
    assert "reviewed_at" in data


def test_72f_sim_review_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-sim-review"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Review status:" in output
    assert "missing_simulation" in output


# Phase 72G — Runner Simulation Approval Gate
# ---------------------------------------------------------------------------


def test_72g_sim_approve_missing_review(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-sim-approve", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["approved"] is False
    assert "review" in data["refusal_reason"].lower()


def test_72g_sim_approve_blocked_review(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    review_dir = tmp_path / ".pcae" / "runner-simulation-reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "latest.json").write_text(
        _json.dumps({"review_status": "blocked"}), encoding="utf-8"
    )

    exit_code = main(["phase", "runner-sim-approve", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["approved"] is False
    assert "blocked" in data["refusal_reason"]


def test_72g_sim_approve_success(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-simulate", "--save"])
    capsys.readouterr()
    main(["phase", "runner-sim-review", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-sim-approve", "--message", "Test approval", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["approved"] is True
    assert data["execution_authorized"] is False
    assert data["message"] == "Test approval"
    assert data["approver_source"] == "local_cli"

    latest = tmp_path / ".pcae" / "runner-simulation-approvals" / "latest.json"
    assert latest.exists()


def test_72g_sim_approve_dry_run(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-simulate", "--save"])
    capsys.readouterr()
    main(["phase", "runner-sim-review", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-sim-approve", "--dry-run", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["approved"] is True
    assert data["dry_run"] is True
    assert data["execution_authorized"] is False

    latest = tmp_path / ".pcae" / "runner-simulation-approvals" / "latest.json"
    assert not latest.exists()


def test_72g_sim_approve_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-simulate", "--save"])
    capsys.readouterr()
    main(["phase", "runner-sim-review", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-sim-approve", "--message", "Human OK"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Approved: yes" in output
    assert "Execution authorized: no" in output


# Phase 72H — Runner Execution Preflight Design
# ---------------------------------------------------------------------------


def test_72h_preflight_design_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["preflight_status"] == "design_only"
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False
    assert data["requirements_total"] == 32
    assert "requirements" in data
    assert "unmet_requirements" in data
    assert "human_authority_note" in data


def test_72h_preflight_execution_authorized_always_false(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Test phase"])
    main(["phase", "runner-simulate", "--save"])
    main(["phase", "runner-sim-review", "--save"])
    main(["phase", "runner-sim-approve", "--message", "test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["execution_authorized"] is False
    assert "execution_authorized true" in str(data["unmet_requirements"])


def test_72h_preflight_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "design only" in output.lower()
    assert "Execution available: no" in output
    assert "Execution authorized: no" in output
    assert "Human authority is absolute" in output


def test_72h_preflight_requirements_have_met_field(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    for req in data["requirements"]:
        assert "requirement" in req
        assert "check" in req
        assert "met" in req
        assert isinstance(req["met"], bool)


# Phase 72J — Runner Simulation Approval Persistence Check
# ---------------------------------------------------------------------------


def test_72j_approval_show_missing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-sim-approval-show", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["present"] is False


def test_72j_approval_show_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-simulate", "--save"])
    capsys.readouterr()
    main(["phase", "runner-sim-review", "--save"])
    capsys.readouterr()
    main(["phase", "runner-sim-approve", "--message", "Persist test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-sim-approval-show", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["present"] is True
    assert data["approved"] is True
    assert data["execution_authorized"] is False
    assert data["message"] == "Persist test"


def test_72j_preflight_recognizes_persisted_approval(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Test phase"])
    main(["phase", "runner-simulate", "--save"])
    capsys.readouterr()
    main(["phase", "runner-sim-review", "--save"])
    capsys.readouterr()
    main(["phase", "runner-sim-approve", "--message", "Approved"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    reqs = {r["check"]: r["met"] for r in data["requirements"]}
    assert reqs["approval_present"] is True
    assert reqs["approval_matches"] is True
    assert reqs["execution_authorized"] is False
    assert data["execution_authorized"] is False


def test_72j_preflight_approval_mismatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-simulate", "--save"])
    capsys.readouterr()
    main(["phase", "runner-sim-review", "--save"])
    capsys.readouterr()
    main(["phase", "runner-sim-approve", "--message", "Old approval"])
    capsys.readouterr()

    sim_path = tmp_path / ".pcae" / "runner-simulations" / "latest.json"
    sim_data = _json.loads(sim_path.read_text(encoding="utf-8"))
    sim_data["created_at"] = "20990101T000000Z"
    sim_path.write_text(_json.dumps(sim_data, indent=2), encoding="utf-8")

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    reqs = {r["check"]: r["met"] for r in data["requirements"]}
    assert reqs["approval_present"] is True
    assert reqs["approval_matches"] is False


def test_72j_approval_show_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-sim-approval-show"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No approval artifact found" in output


# Phase 72K — Execution Authorization Negative Gate
# ---------------------------------------------------------------------------


def test_72k_execution_authorize_always_refuses(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-authorize", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["authorization_available"] is False
    assert data["authorized"] is False
    assert data["mutation_performed"] is False
    assert "not implemented" in data["refusal_reason"]


def test_72k_execution_authorize_dry_run_still_refuses(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-authorize", "--dry-run", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["authorized"] is False
    assert data["dry_run"] is True


def test_72k_execution_authorize_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-authorize"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Authorization available: no" in output
    assert "Authorized: no" in output
    assert "not implemented" in output


def test_72k_no_path_produces_execution_authorized_true(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "add", "Test phase"])
    main(["phase", "runner-simulate", "--save"])
    capsys.readouterr()
    main(["phase", "runner-sim-review", "--save"])
    capsys.readouterr()
    main(["phase", "runner-sim-approve", "--message", "Full approval"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-sim-approval-show", "--json"])
    approval = _json.loads(capsys.readouterr().out)
    assert approval["execution_authorized"] is False

    exit_code = main(["phase", "runner-execution-preflight", "--json"])
    preflight = _json.loads(capsys.readouterr().out)
    assert preflight["execution_authorized"] is False
    assert preflight["execution_available"] is False

    exit_code = main(["phase", "runner-execution-authorize", "--json"])
    auth = _json.loads(capsys.readouterr().out)
    assert auth["authorized"] is False
    assert auth["authorization_available"] is False


def test_72k_preflight_still_design_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import json as _json

    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = _json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["preflight_status"] == "design_only"
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False


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


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Phase 71K: pcae phase prompt-capture
# ---------------------------------------------------------------------------


def test_71k_prompt_capture_text(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "phase", "prompt-capture",
        "--title", "71L — Phase Prompt Show",
        "--text", "Implement prompt show command.",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Captured phase prompt: 71L — Phase Prompt Show" in output
    assert (tmp_path / ".pcae" / "phase-prompts" / "latest.md").is_file()
    assert (tmp_path / ".pcae" / "phase-prompts" / "latest.md").read_text(
        encoding="utf-8"
    ) == "Implement prompt show command."


def test_71k_prompt_capture_file(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    prompt_file = tmp_path / "my-prompt.md"
    prompt_file.write_text("File-based prompt content.\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "phase", "prompt-capture",
        "--title", "71K File Test",
        "--file", str(prompt_file),
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Captured phase prompt: 71K File Test" in output
    assert (tmp_path / ".pcae" / "phase-prompts" / "latest.md").read_text(
        encoding="utf-8"
    ) == "File-based prompt content.\n"


def test_71k_prompt_capture_stdin(tmp_path: Path, monkeypatch, capsys) -> None:
    import io

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("Stdin prompt content."))

    exit_code = main([
        "phase", "prompt-capture",
        "--title", "71K Stdin Test",
        "--stdin",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Captured phase prompt: 71K Stdin Test" in output
    assert (tmp_path / ".pcae" / "phase-prompts" / "latest.md").read_text(
        encoding="utf-8"
    ) == "Stdin prompt content."


def test_71k_prompt_capture_creates_timestamped_artifact(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main([
        "phase", "prompt-capture",
        "--title", "Timestamped Test",
        "--text", "Timestamped content.",
    ])

    capsys.readouterr()
    prompts_dir = tmp_path / ".pcae" / "phase-prompts"
    ts_files = [f for f in prompts_dir.iterdir() if f.name.startswith("timestamped-test-")]
    assert len(ts_files) == 1
    assert ts_files[0].read_text(encoding="utf-8") == "Timestamped content."


def test_71k_prompt_capture_updates_latest(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "prompt-capture", "--title", "First", "--text", "First prompt."])
    capsys.readouterr()
    main(["phase", "prompt-capture", "--title", "Second", "--text", "Second prompt."])
    capsys.readouterr()

    latest = (tmp_path / ".pcae" / "phase-prompts" / "latest.md").read_text(encoding="utf-8")
    assert latest == "Second prompt."
    metadata = json.loads(
        (tmp_path / ".pcae" / "phase-prompts" / "latest.json").read_text(encoding="utf-8")
    )
    assert metadata["title"] == "Second"


def test_71k_prompt_capture_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "phase", "prompt-capture",
        "--title", "JSON Output Test",
        "--text", "JSON prompt.",
        "--json",
    ])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["title"] == "JSON Output Test"
    assert "created_at" in data
    assert data["latest_path"] == ".pcae/phase-prompts/latest.md"
    assert "timestamped_path" in data


def test_71k_prompt_capture_gitignored(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "prompt-capture", "--title", "Git Test", "--text", "git test."])
    capsys.readouterr()

    result = subprocess.run(
        ["git", "status", "--porcelain", ".pcae/phase-prompts/"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.stdout.strip() == ""


def test_71k_prompt_capture_no_source_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "phase", "prompt-capture",
        "--title", "No Source",
    ])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "one of --text, --file, or --stdin is required" in output


def test_71k_prompt_capture_file_not_found(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "phase", "prompt-capture",
        "--title", "Missing File",
        "--file", "/nonexistent/file.md",
    ])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "file not found" in output


def test_71k_prompt_capture_template_includes_phase_prompts(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    gitignore = (tmp_path / ".pcae" / ".gitignore").read_text(encoding="utf-8")
    assert "phase-prompts/" in gitignore


# ---------------------------------------------------------------------------
# Phase 71L: pcae phase prompt-show / prompt-list
# ---------------------------------------------------------------------------


def _capture_prompt(tmp_path: Path, title: str, text: str) -> None:
    from pcae.commands.phase import PHASE_PROMPTS_DIR, _slugify
    from datetime import datetime, timezone

    prompts_dir = tmp_path / PHASE_PROMPTS_DIR
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


def test_71l_prompt_show_displays_latest(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "71L Test", "Show me this prompt.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-show"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase prompt: 71L Test" in output
    assert "Show me this prompt." in output
    assert "Created:" in output


def test_71l_prompt_show_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "71L JSON", "JSON prompt content.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-show", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["title"] == "71L JSON"
    assert data["content"] == "JSON prompt content."
    assert "created_at" in data
    assert "latest_path" in data


def test_71l_prompt_show_missing_returns_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-show"])

    output = capsys.readouterr().err
    assert exit_code == 1
    assert "No captured phase prompt found" in output


def test_71l_prompt_list_with_prompts(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "First", "First prompt.")
    prompts_dir = tmp_path / ".pcae" / "phase-prompts"
    (prompts_dir / "second-20260619T120000Z.md").write_text(
        "Second prompt.", encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Captured phase prompts (2):" in output


def test_71l_prompt_list_empty(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No captured phase prompts found" in output


def test_71l_prompt_list_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "Listed", "Listed prompt.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["count"] >= 1
    assert isinstance(data["prompts"], list)
    assert all("filename" in p and "path" in p for p in data["prompts"])


def test_71l_prompt_list_json_empty(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["count"] == 0
    assert data["prompts"] == []


def test_71l_prompt_show_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "ReadOnly", "Read-only test.")
    commit_baseline(tmp_path)

    def text_snapshot(root: Path) -> dict[str, str]:
        return {
            p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
            for p in root.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(root).parts
        }

    before = text_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "prompt-show"])
    main(["phase", "prompt-list"])

    capsys.readouterr()
    after = text_snapshot(tmp_path)
    assert after == before


# ---------------------------------------------------------------------------
# Phase 71M: prompt visibility in handoff and handoff-show
# ---------------------------------------------------------------------------


def test_71m_handoff_artifact_includes_prompt_when_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Prompt handoff task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    _capture_prompt(tmp_path, "71M Handoff", "Prompt for handoff.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["prompt_summary"]["present"] is True
    assert data["prompt_summary"]["title"] == "71M Handoff"
    assert data["prompt_summary"]["path"] == ".pcae/phase-prompts/latest.md"


def test_71m_handoff_artifact_prompt_absent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "No prompt handoff task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "handoff", "--next-agent", "claude-next", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["prompt_summary"] is None


def test_71m_handoff_show_displays_prompt_when_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff show prompt task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    _capture_prompt(tmp_path, "71M Show", "Show prompt in handoff.")
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--next-agent", "claude-next"])
    capsys.readouterr()

    exit_code = main(["phase", "handoff-show"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Latest prompt: 71M Show" in output


def test_71m_handoff_show_silent_when_no_prompt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Handoff show no prompt task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "handoff", "--next-agent", "claude-next"])
    capsys.readouterr()

    exit_code = main(["phase", "handoff-show"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Latest prompt:" not in output


# ---------------------------------------------------------------------------
# Phase 71N: prompt-hygiene and prompt-prune
# ---------------------------------------------------------------------------


def test_71n_prompt_hygiene_empty(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-hygiene"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "clean (no prompts)" in output


def test_71n_prompt_hygiene_no_placeholders(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "Real Phase 72A", "Implement feature X.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-hygiene"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "clean" in output
    assert "no placeholders" in output


def test_71n_prompt_hygiene_detects_placeholder(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "Test Prompt", "This is a test prompt only.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-hygiene"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "1 placeholder(s) found" in output


def test_71n_prompt_hygiene_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "Placeholder Prompt", "placeholder content")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-hygiene", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["has_issues"] is True
    assert data["clearable_count"] >= 1


def test_71n_prompt_hygiene_clear_requires_confirm(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "Test Prompt", "test prompt content")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-hygiene", "--clear-placeholders"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "--confirm" in output


def test_71n_prompt_hygiene_clear_with_confirm(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "Test Prompt Dummy", "dummy test prompt")
    _capture_prompt(tmp_path, "Real Phase 72B", "Implement real work.")
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "phase", "prompt-hygiene", "--clear-placeholders", "--confirm",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Cleared" in output
    prompts_dir = tmp_path / ".pcae" / "phase-prompts"
    remaining = [
        f for f in prompts_dir.iterdir()
        if f.is_file() and f.suffix == ".md" and f.name != "latest.md"
    ]
    assert len(remaining) >= 1
    assert all("dummy" not in f.name for f in remaining)


def test_71n_prompt_prune_nothing_to_prune(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "One", "First.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-prune", "--keep", "5", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Nothing to prune" in output


def test_71n_prompt_prune_dry_run(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    prompts_dir = tmp_path / ".pcae" / "phase-prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for i in range(5):
        (prompts_dir / f"phase-{i}-20260619T10000{i}Z.md").write_text(
            f"Prompt {i}", encoding="utf-8",
        )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-prune", "--keep", "2", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "3 of 5 would be pruned" in output
    assert len(list(prompts_dir.glob("phase-*.md"))) == 5


def test_71n_prompt_prune_confirm(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    prompts_dir = tmp_path / ".pcae" / "phase-prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for i in range(5):
        (prompts_dir / f"phase-{i}-20260619T10000{i}Z.md").write_text(
            f"Prompt {i}", encoding="utf-8",
        )
    (prompts_dir / "latest.md").write_text("Latest", encoding="utf-8")
    (prompts_dir / "latest.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-prune", "--keep", "2"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Pruned 3 of 5" in output
    assert len(list(prompts_dir.glob("phase-*.md"))) == 2
    assert (prompts_dir / "latest.md").is_file()
    assert (prompts_dir / "latest.json").is_file()


def test_71n_prompt_prune_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    prompts_dir = tmp_path / ".pcae" / "phase-prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for i in range(4):
        (prompts_dir / f"phase-{i}-20260619T10000{i}Z.md").write_text(
            f"Prompt {i}", encoding="utf-8",
        )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-prune", "--keep", "2", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["pruned"] == 2
    assert data["keep"] == 2


# ---------------------------------------------------------------------------
# Phase 71P: pcae phase prompt-enqueue
# ---------------------------------------------------------------------------


def test_71p_prompt_enqueue_latest(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "72A — Feature X", "Implement feature X.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-enqueue"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Enqueued from prompt: 72A — Feature X" in output
    queue = json.loads(
        (tmp_path / ".pcae" / "phase-queue.json").read_text(encoding="utf-8")
    )
    assert queue[0]["title"] == "72A — Feature X"
    assert queue[0]["source_type"] == "captured_prompt"
    assert queue[0]["source_prompt_path"] == ".pcae/phase-prompts/latest.md"
    assert queue[0]["source_prompt_created_at"] is not None
    assert queue[0]["created_at"] is not None


def test_71p_prompt_enqueue_dry_run(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "72B — Dry Run", "Dry run test.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-enqueue", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Dry run: would enqueue: 72B — Dry Run" in output
    assert not (tmp_path / ".pcae" / "phase-queue.json").exists()


def test_71p_prompt_enqueue_json(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "72C — JSON", "JSON test.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-enqueue", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["title"] == "72C — JSON"
    assert data["mutated"] is True
    assert data["queue_length"] == 1
    assert "source_prompt_path" in data
    assert "source_prompt_created_at" in data


def test_71p_prompt_enqueue_duplicate_detection(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "72D — Duplicate", "Dup test.")
    monkeypatch.chdir(tmp_path)

    main(["phase", "prompt-enqueue"])
    capsys.readouterr()

    exit_code = main(["phase", "prompt-enqueue"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "already contains" in output


def test_71p_prompt_enqueue_missing_prompt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-enqueue"])

    output = capsys.readouterr().err
    assert exit_code == 1
    assert "no captured phase prompt found" in output


def test_71p_prompt_enqueue_title_override(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "72E — Original", "Original.")
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "phase", "prompt-enqueue", "--title", "Custom Queue Title",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Custom Queue Title" in output
    queue = json.loads(
        (tmp_path / ".pcae" / "phase-queue.json").read_text(encoding="utf-8")
    )
    assert queue[0]["title"] == "Custom Queue Title"


def test_71p_prompt_enqueue_by_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    prompts_dir = tmp_path / ".pcae" / "phase-prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / "specific-20260619T120000Z.md").write_text(
        "Specific prompt.", encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "phase", "prompt-enqueue",
        "--file", "specific-20260619T120000Z.md",
        "--title", "Specific Phase",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Specific Phase" in output


def test_71p_prompt_enqueue_file_not_found(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "phase", "prompt-enqueue",
        "--file", "nonexistent-20260619T000000Z.md",
    ])

    output = capsys.readouterr().err
    assert exit_code == 1
    assert "not found" in output


def test_71p_prompt_enqueue_dry_run_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "72F — DryJSON", "Dry JSON.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-enqueue", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["dry_run"] is True
    assert data["mutated"] is False
    assert data["title"] == "72F — DryJSON"


def test_71p_prompt_enqueue_does_not_execute(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "72G — No Execute", "Do not execute me.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-enqueue"])

    capsys.readouterr()
    assert exit_code == 0
    assert not list((tmp_path / "tasks" / "active").glob("*72g*"))
    assert (tmp_path / ".pcae" / "phase-prompts" / "latest.md").read_text(
        encoding="utf-8"
    ) == "Do not execute me."


# ---------------------------------------------------------------------------
# Phase 71Q: phase prompt queue metadata preservation
# ---------------------------------------------------------------------------


def test_71q_queue_list_json_supports_mixed_entries(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(
        json.dumps([
            "Phase 72A: manual",
            {
                "title": "Phase 72B: captured",
                "source_type": "captured_prompt",
                "source_prompt_path": ".pcae/phase-prompts/latest.md",
                "source_prompt_created_at": "2026-06-19T12:00:00+00:00",
                "created_at": "2026-06-19T12:01:00+00:00",
            },
        ], indent=2) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_length"] == 2
    assert data["queue"][0] == "Phase 72A: manual"
    assert data["entries"][0]["title"] == "Phase 72A: manual"
    assert data["entries"][0]["source_type"] == "manual"
    assert data["entries"][0]["structured"] is False
    assert data["entries"][1]["title"] == "Phase 72B: captured"
    assert data["entries"][1]["source_type"] == "captured_prompt"
    assert data["entries"][1]["source_prompt_path"] == ".pcae/phase-prompts/latest.md"


def test_71q_queue_list_human_supports_structured_entries(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(
        json.dumps([{
            "title": "Phase 72C: structured",
            "source_type": "captured_prompt",
            "source_prompt_path": ".pcae/phase-prompts/latest.md",
            "source_prompt_created_at": "2026-06-19T12:00:00+00:00",
            "created_at": "2026-06-19T12:01:00+00:00",
        }]) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "1. Phase 72C: structured" in output
    assert "source: .pcae/phase-prompts/latest.md" in output


def test_71q_queue_check_json_reports_structured_next_metadata(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(
        json.dumps([{
            "title": "Phase 72D: ready",
            "source_type": "captured_prompt",
            "source_prompt_path": ".pcae/phase-prompts/latest.md",
            "source_prompt_created_at": "2026-06-19T12:00:00+00:00",
            "created_at": "2026-06-19T12:01:00+00:00",
        }]) + "\n",
        encoding="utf-8",
    )
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["next_queued"] == "Phase 72D: ready"
    assert data["next_queued_entry"]["source_type"] == "captured_prompt"
    assert data["entries"][0]["source_prompt_created_at"] == "2026-06-19T12:00:00+00:00"


def test_71q_queue_hygiene_detects_structured_placeholder(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(
        json.dumps([
            {
                "title": "Phase 72E: placeholder",
                "source_type": "captured_prompt",
                "source_prompt_path": ".pcae/phase-prompts/latest.md",
                "source_prompt_created_at": "2026-06-19T12:00:00+00:00",
                "created_at": "2026-06-19T12:01:00+00:00",
            },
            "Phase 72F: real work",
        ]) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "hygiene", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["has_issues"] is True
    assert data["findings"][0]["entry"] == "Phase 72E: placeholder"


def test_71q_prompt_enqueue_duplicate_detection_matches_structured_title(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "72G — Structured Duplicate", "Dup test.")
    monkeypatch.chdir(tmp_path)

    main(["phase", "prompt-enqueue"])
    capsys.readouterr()
    exit_code = main(["phase", "prompt-enqueue"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "already contains" in output


# ---------------------------------------------------------------------------
# Phase 71R: pcae phase prompt-roundtrip-check
# ---------------------------------------------------------------------------


def test_71r_prompt_roundtrip_check_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "72H — Round Trip", "Round-trip prompt.")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-roundtrip-check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase prompt round-trip check: ready" in output
    assert "Dry-run title: 72H — Round Trip" in output
    assert "Mutated: no" in output
    assert not (tmp_path / ".pcae" / "phase-queue.json").exists()


def test_71r_prompt_roundtrip_check_missing_prompt_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-roundtrip-check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["ready"] is False
    assert data["prompt_present"] is False
    assert data["queue_present"] is False
    assert data["dry_run_title"] is None
    assert data["reasons"]


def test_71r_prompt_roundtrip_check_existing_queue_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "72I — Existing Queue", "Prompt with queue.")
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(
        json.dumps([
            "Phase 72J: manual",
            {
                "title": "Phase 72K: captured",
                "source_type": "captured_prompt",
                "source_prompt_path": ".pcae/phase-prompts/latest.md",
                "source_prompt_created_at": "2026-06-19T12:00:00+00:00",
                "created_at": "2026-06-19T12:01:00+00:00",
            },
        ], indent=2) + "\n",
        encoding="utf-8",
    )
    before = queue_path.read_text(encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-roundtrip-check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["ready"] is True
    assert data["prompt_present"] is True
    assert data["queue_present"] is True
    assert data["queue_length"] == 2
    assert data["dry_run_title"] == "72I — Existing Queue"
    assert data["queue_entries"][0]["title"] == "Phase 72J: manual"
    assert queue_path.read_text(encoding="utf-8") == before


def test_71r_prompt_roundtrip_check_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    _capture_prompt(tmp_path, "72L — Read Only", "Do not mutate.")
    prompts_dir = tmp_path / ".pcae" / "phase-prompts"
    before_prompt_files = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(prompts_dir.iterdir())
        if path.is_file()
    }
    before_tasks = list((tmp_path / "tasks" / "active").glob("*.md"))
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "prompt-roundtrip-check", "--json"])

    data = json.loads(capsys.readouterr().out)
    after_prompt_files = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(prompts_dir.iterdir())
        if path.is_file()
    }
    assert exit_code == 0
    assert data["mutated"] is False
    assert data["dry_run_mutated"] is False
    assert before_prompt_files == after_prompt_files
    assert not (tmp_path / ".pcae" / "phase-queue.json").exists()
    assert list((tmp_path / "tasks" / "active").glob("*.md")) == before_tasks


# ---------------------------------------------------------------------------
# Phase 72L: queue validation
# ---------------------------------------------------------------------------


def test_72l_queue_validate_empty_queue(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text("[]", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Valid: yes" in output
    assert "Queue ready: no" in output
    assert "Entry count: 0" in output


def test_72l_queue_validate_empty_queue_json(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text("[]", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["queue_ready"] is False
    assert data["queue_entry_count"] == 0
    assert data["mutated"] is False


def test_72l_queue_validate_no_file(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["queue_file_present"] is False
    assert data["queue_readable"] is False
    assert data["queue_ready"] is False
    assert data["issues"] == []  # absent queue file is valid, not an issue


def test_72l_queue_validate_legacy_string_entries(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps([
        "Phase 72A: First phase",
        "Phase 72B: Second phase",
    ], indent=2) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["queue_entry_count"] == 2
    assert data["queue_ready"] is True
    assert len(data["entries"]) == 2
    assert data["entries"][0]["title"] == "Phase 72A: First phase"
    assert data["entries"][1]["title"] == "Phase 72B: Second phase"
    for e in data["entries"]:
        assert e.get("status") == "ok"


def test_72l_queue_validate_structured_entries(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps([
        {
            "title": "Phase 72C: captured",
            "source_type": "captured_prompt",
            "source_prompt_path": ".pcae/phase-prompts/latest.md",
            "source_prompt_created_at": "2026-06-19T12:00:00+00:00",
            "created_at": "2026-06-19T12:01:00+00:00",
        },
    ], indent=2) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["queue_entry_count"] == 1
    assert data["entries"][0]["status"] == "ok"


def test_72l_queue_validate_placeholder_detected(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps([
        "Phase 72A: real phase",
        "test phase for something",
    ], indent=2) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["valid"] is False
    assert "matches placeholder pattern" in str(data["issues"])


def test_72l_queue_validate_duplicate_detected(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps([
        "Phase 72A: same title",
        "Phase 72A: same title",
    ], indent=2) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["valid"] is False
    assert "duplicate title" in str(data["issues"])


def test_72l_queue_validate_unsupported_source_type(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps([
        {
            "title": "Bad source",
            "source_type": "unknown_type",
        },
    ], indent=2) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["valid"] is False
    assert "unsupported source_type" in str(data["issues"])


def test_72l_queue_validate_captured_prompt_missing_path(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps([
        {
            "title": "Missing path",
            "source_type": "captured_prompt",
        },
    ], indent=2) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["valid"] is False
    assert "missing source_prompt_path" in str(data["issues"])


def test_72l_queue_validate_forbidden_execution_field(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps([
        {
            "title": "Authorized entry",
            "source_type": "manual",
            "execution_authorized": True,
        },
    ], indent=2) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["valid"] is False
    assert "forbidden field" in str(data["issues"])


def test_72l_queue_validate_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps([
        "Phase 72A: real phase title",
        {"title": "Phase 72B: structured", "source_type": "manual"},
    ], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    before_stat = queue_path.stat()
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["mutated"] is False
    assert queue_path.read_text(encoding="utf-8") == before
    assert queue_path.stat().st_mtime == before_stat.st_mtime


def test_72l_queue_validate_invalid_phase_id(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps([
        {
            "title": "Bad phase id",
            "source_type": "manual",
            "phase_id": "not-a-valid-phase",
        },
    ], indent=2) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["valid"] is False
    assert "invalid phase_id" in str(data["issues"])


def test_72l_queue_validate_human_output_no_execution_note(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps(["Phase 72A: test"]), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No execution performed" in output
    assert "read-only" in output.lower()


def test_72l_queue_validate_unreadable_queue(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text("not valid json {{{", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["valid"] is False
    assert data["queue_readable"] is False
    assert "not readable" in str(data["issues"])


def test_72l_queue_validate_not_array(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps({"not": "an array"}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["valid"] is False
    assert "not a JSON array" in str(data["issues"])


# ---------------------------------------------------------------------------
# Phase 72M: queue approval artifact
# ---------------------------------------------------------------------------


def test_72m_queue_approve_dry_run_with_valid_queue(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps([
        "Phase 72A: valid entry",
    ], indent=2) + "\n", encoding="utf-8")
    before = queue_path.read_text(encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "approve", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["approved"] is True
    assert data["dry_run"] is True
    assert data["execution_authorized"] is False
    assert data["approver_source"] == "local_cli"
    assert data["queue_entry_count"] == 1
    assert queue_path.read_text(encoding="utf-8") == before
    assert not (tmp_path / ".pcae" / "phase-queue-approvals" / "latest.json").exists()


def test_72m_queue_approve_success_and_persist(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps([
        "Phase 72A: valid entry",
    ], indent=2) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "approve", "--message", "Test approval", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["approved"] is True
    assert data["execution_authorized"] is False
    assert data["queue_entry_count"] == 1
    assert len(data["queue_digest"]) == 64  # SHA-256 hex digest

    approval_path = tmp_path / ".pcae" / "phase-queue-approvals" / "latest.json"
    assert approval_path.is_file()
    saved = json.loads(approval_path.read_text(encoding="utf-8"))
    assert saved["approved"] is True
    assert saved["execution_authorized"] is False
    assert saved["approved_at"] is not None
    assert saved["approver_source"] == "local_cli"


def test_72m_queue_approve_refuses_empty_queue(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text("[]", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "approve", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["approved"] is False
    assert "empty" in data["refusal_reason"].lower()


def test_72m_queue_approve_refuses_invalid_queue(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps(["dummy placeholder entry"]), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "approve", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["approved"] is False
    assert "validation failed" in data["refusal_reason"].lower()


def test_72m_queue_approve_no_mutation_on_refusal(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text("[]", encoding="utf-8")
    before = queue_path.read_text(encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "approve"])

    capsys.readouterr()
    assert exit_code == 1
    assert queue_path.read_text(encoding="utf-8") == before
    assert not (tmp_path / ".pcae" / "phase-queue-approvals" / "latest.json").exists()


def test_72m_queue_approval_show_when_present(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps(["Phase 72A: test"]), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "approve", "--message", "Show test"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "approval-show", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["present"] is True
    assert data["approved"] is True
    assert data["queue_entry_count"] == 1
    assert data["queue_digest_matches"] is True
    assert data["execution_authorized"] is False
    assert data["approval_message"] == "Show test"


def test_72m_queue_approval_show_mismatch(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps(["Phase 72A: original"]), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "approve", "--message", "First approval"])
    capsys.readouterr()

    queue_path.write_text(json.dumps(["Phase 72B: modified"]), encoding="utf-8")

    exit_code = main(["phase", "queue", "approval-show", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["present"] is True
    assert data["queue_digest_matches"] is False


def test_72m_queue_approval_show_none(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "approval-show", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["present"] is False


def test_72m_queue_approve_human_output_shows_no_execution(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps(["Phase 72A: test"]), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "approve", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Execution authorized: no" in output


def test_72m_queue_approve_does_not_mutate_queue(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 72A: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "queue", "approve", "--message", "Queue stays same"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# Phase 72N: queue-to-runner preflight bridge
# ---------------------------------------------------------------------------


def _make_queue_file(tmp_path: Path, entries: list) -> None:
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def _make_queue_approval(tmp_path: Path, digest: str) -> None:
    approval_dir = tmp_path / ".pcae" / "phase-queue-approvals"
    approval_dir.mkdir(parents=True, exist_ok=True)
    approval = {
        "approved": True,
        "execution_authorized": False,
        "queue_entry_count": 1,
        "queue_digest": digest,
        "approval_message": "test",
        "approver_source": "local_cli",
        "approved_at": "20260619T000000Z",
    }
    (approval_dir / "latest.json").write_text(
        json.dumps(approval, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_72n_preflight_empty_queue_reports_queue_issues(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _make_queue_file(tmp_path, [])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_valid"] is True
    assert data["queue_approval_present"] is False
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False
    assert "queue non-empty" in data["unmet_requirements"]


def test_72n_preflight_valid_approved_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import hashlib as _hashlib

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    entries = ["Phase 72A: valid entry"]
    _make_queue_file(tmp_path, entries)
    digest = _hashlib.sha256(
        (json.dumps(entries, indent=2) + "\n").encode("utf-8")
    ).hexdigest()
    _make_queue_approval(tmp_path, digest)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_valid"] is True
    assert data["queue_validation_status"] == "valid"
    assert data["queue_approval_present"] is True
    assert data["queue_approval_matches_current_queue"] is True
    assert data["queue_approval_execution_authorized"] is False
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False


def test_72n_preflight_approval_mismatch_when_queue_changed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import hashlib as _hashlib

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    # Create approval based on original queue
    original = ["Phase 72A: original"]
    original_digest = _hashlib.sha256(
        (json.dumps(original, indent=2) + "\n").encode("utf-8")
    ).hexdigest()
    _make_queue_approval(tmp_path, original_digest)
    # Now queue has different content
    _make_queue_file(tmp_path, ["Phase 72B: modified"])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_valid"] is True
    assert data["queue_approval_present"] is True
    assert data["queue_approval_matches_current_queue"] is False
    assert "queue approval matches current queue" in data["unmet_requirements"]


def test_72n_preflight_invalid_queue_reports_issues(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _make_queue_file(tmp_path, ["dummy placeholder"])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_valid"] is False
    assert "queue valid" in data["unmet_requirements"]


def test_72n_preflight_execution_always_unavailable(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import hashlib as _hashlib

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    entries = ["Phase 72A: perfectly valid"]
    _make_queue_file(tmp_path, entries)
    digest = _hashlib.sha256(
        (json.dumps(entries, indent=2) + "\n").encode("utf-8")
    ).hexdigest()
    _make_queue_approval(tmp_path, digest)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False
    assert data["preflight_status"] == "design_only"
    assert "execution_authorized true (future phase)" in data["unmet_requirements"]


def test_72n_preflight_queue_approval_execution_authorized_is_false(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    import hashlib as _hashlib

    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    entries = ["Phase 72A: test"]
    _make_queue_file(tmp_path, entries)
    digest = _hashlib.sha256(
        (json.dumps(entries, indent=2) + "\n").encode("utf-8")
    ).hexdigest()
    _make_queue_approval(tmp_path, digest)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_approval_execution_authorized"] is False


def test_72n_preflight_human_output_states_no_execution(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Execution available: no" in output
    assert "Execution authorized: no" in output
    assert "design only" in output.lower()


# ---------------------------------------------------------------------------
# Phase 72O: safe queue fixture lifecycle
# ---------------------------------------------------------------------------


def test_72o_fixture_add_creates_entries(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "fixture-add", "--count", "2", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["added"] == 2
    assert len(data["entries"]) == 2
    assert data["entries"][0]["title"] == "QUEUE-FIXTURE-001"
    assert data["entries"][0]["fixture"] is True
    assert data["entries"][0]["execution_authorized"] is False
    assert data["entries"][0]["source_type"] == "fixture"
    assert data["entries"][1]["title"] == "QUEUE-FIXTURE-002"
    assert data["queue_length"] == 2
    assert "No execution performed" in data["note"]


def test_72o_fixture_add_default_count(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "fixture-add", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["added"] == 1
    assert data["count"] == 1
    assert data["entries"][0]["title"] == "QUEUE-FIXTURE-001"


def test_72o_fixture_validation_reports_valid_and_fixture_count(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "2"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["queue_ready"] is True
    assert data["fixture_count"] == 2
    assert data["queue_entry_count"] == 2


def test_72o_fixture_clear_removes_only_fixtures(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(json.dumps([
        "Phase 72A: real entry",
        {
            "title": "QUEUE-FIXTURE-001",
            "source_type": "fixture",
            "fixture": True,
            "execution_authorized": False,
        },
        "Phase 72B: another real entry",
        {
            "title": "QUEUE-FIXTURE-002",
            "source_type": "fixture",
            "fixture": True,
            "execution_authorized": False,
        },
    ], indent=2) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "fixture-clear", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["cleared"] == 2
    assert data["remaining"] == 2

    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    assert queue == ["Phase 72A: real entry", "Phase 72B: another real entry"]


def test_72o_fixture_clear_on_empty_queue(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text("[]", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "fixture-clear", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["cleared"] == 0
    assert data["remaining"] == 0


def test_72o_fixture_clear_no_fixtures(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text(
        json.dumps(["Phase 72A: real", "Phase 72B: also real"]), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "fixture-clear", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["cleared"] == 0
    assert data["remaining"] == 2


def test_72o_fixture_no_task_created(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    before_tasks = list((tmp_path / "tasks" / "active").glob("*.md"))

    main(["phase", "queue", "fixture-add", "--count", "2"])
    capsys.readouterr()

    after_tasks = list((tmp_path / "tasks" / "active").glob("*.md"))
    assert after_tasks == before_tasks


def test_72o_fixture_human_output_no_execution(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "fixture-add", "--count", "1"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No execution performed" in output


# ---------------------------------------------------------------------------
# Phase 72P: queue approval matching with non-empty queue
# ---------------------------------------------------------------------------


def test_72p_approval_check_match_with_fixture_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "Fixture approval"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "approval-check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["ready"] is True
    assert data["approval_present"] is True
    assert data["approval_matches"] is True
    assert data["queue_valid"] is True
    assert data["execution_authorized"] is False


def test_72p_approval_check_mismatch_when_queue_changes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "Original"])
    capsys.readouterr()
    # Add another fixture → queue digest changes
    main(["phase", "queue", "fixture-add", "--count", "1"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "approval-check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["ready"] is False
    assert data["approval_present"] is True
    assert data["approval_matches"] is False
    assert "does not match" in str(data["reasons"])


def test_72p_approval_check_empty_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    queue_path.write_text("[]", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "queue", "approval-check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["ready"] is False
    assert "empty" in str(data["reasons"])


def test_72p_approval_check_execution_authorized_false(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "Check exec auth"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "approval-check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["execution_authorized"] is False
    assert data["ready"] is True


def test_72p_approval_show_reports_match_and_mismatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "Show test"])
    capsys.readouterr()

    # Approval matches
    exit_code = main(["phase", "queue", "approval-show", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_digest_matches"] is True

    # Modify queue → mismatch
    main(["phase", "queue", "fixture-add", "--count", "1"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "approval-show", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_digest_matches"] is False


def test_72p_approval_check_no_execution(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "No exec"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "approval-check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No execution performed" in output
    assert "read-only" in output.lower()


# ---------------------------------------------------------------------------
# Phase 72Q: queue preflight positive non-execution path
# ---------------------------------------------------------------------------


def test_72q_preflight_queue_requirements_met_with_fixture(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "72Q test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_validation_present"] is True
    assert data["queue_valid"] is True
    assert data["queue_approval_present"] is True
    assert data["queue_approval_matches_current_queue"] is True
    assert data["queue_approval_execution_authorized"] is False
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False


def test_72q_preflight_stays_design_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "72Q status test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["preflight_status"] == "design_only"
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False


def test_72q_preflight_queue_unmet_when_cleared(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "72Q revert test"])
    capsys.readouterr()
    main(["phase", "queue", "clear"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_approval_present"] is True
    assert data["queue_approval_matches_current_queue"] is False
    assert "queue non-empty" in data["unmet_requirements"]
    assert "queue approval matches current queue" in data["unmet_requirements"]


def test_72q_preflight_requirements_list_includes_queue_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "72Q req test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    req_keys = {r["check"] for r in data["requirements"]}
    assert "queue_validation_present" in req_keys
    assert "queue_valid" in req_keys
    assert "queue_approval_present" in req_keys
    assert "queue_approval_matches" in req_keys
    assert "queue_approval_not_authorized" in req_keys


def test_72q_preflight_human_output_states_no_execution(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "72Q human test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Execution available: no" in output
    assert "Execution authorized: no" in output
    assert "design only" in output.lower()
    assert "not implemented and not authorized" in output.lower()


def test_72q_preflight_no_fixture_leftovers(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "72Q cleanup test"])
    capsys.readouterr()

    main(["phase", "queue", "fixture-clear"])
    capsys.readouterr()

    exit_code = main(["phase", "queue", "validate", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["queue_entry_count"] == 0
    assert data["fixture_count"] == 0


# ---------------------------------------------------------------------------
# Phase 72S: execution authorization artifact schema dry run
# ---------------------------------------------------------------------------


def test_72s_schema_json_output(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-authorization-schema", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["schema_only"] is True
    assert data["artifact_written"] is False
    assert data["execution_authorized"] is False
    assert data["authorization_available"] is False
    assert isinstance(data["proposed_fields"], dict)
    assert len(data["proposed_fields"]) > 10
    assert isinstance(data["minimum_requirements"], list)
    assert isinstance(data["forbidden_implied_authorization"], list)


def test_72s_schema_no_artifact_written(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-execution-authorization-schema"])
    capsys.readouterr()

    assert not (tmp_path / ".pcae" / "execution-authorizations").exists()
    assert not (tmp_path / ".pcae" / "execution-auth").exists()


def test_72s_schema_no_queue_mutation(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 72A: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-execution-authorization-schema"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


def test_72s_schema_no_task_created(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    before_tasks = list((tmp_path / "tasks" / "active").glob("*.md"))

    main(["phase", "runner-execution-authorization-schema", "--json"])
    capsys.readouterr()

    assert list((tmp_path / "tasks" / "active").glob("*.md")) == before_tasks


def test_72s_schema_human_output_states_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-authorization-schema"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "schema only" in output.lower()
    assert "read-only" in output.lower()
    assert "not implemented" in output.lower()
    assert "execution authorized: no" in output.lower()


# ---------------------------------------------------------------------------
# Phase 72T: runner execution command stub refusal
# ---------------------------------------------------------------------------


def test_72t_runner_execute_always_refuses(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False
    assert data["mutation_performed"] is False
    assert data["tasks_created"] == 0
    assert data["queue_mutated"] is False


def test_72t_runner_execute_dry_run_still_refuses(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["dry_run"] is True
    assert data["execution_authorized"] is False


def test_72t_runner_execute_no_queue_mutation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 72A: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-execute"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


def test_72t_runner_execute_no_task_created(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    before_tasks = list((tmp_path / "tasks" / "active").glob("*.md"))

    main(["phase", "runner-execute"])
    capsys.readouterr()

    assert list((tmp_path / "tasks" / "active").glob("*.md")) == before_tasks


def test_72t_runner_execute_no_artifact_written(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-execute"])
    capsys.readouterr()

    assert not (tmp_path / ".pcae" / "execution-authorizations").exists()


def test_72t_runner_execute_human_output_unmistakable(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "not implemented" in output.lower()
    assert "not authorized" in output.lower()
    assert "mutation performed: no" in output.lower()
    assert "tasks created: 0" in output.lower()
    assert "queue mutated: no" in output.lower()


# ---------------------------------------------------------------------------
# Phase 72U: execution authorization request artifact
# ---------------------------------------------------------------------------


def test_72u_execution_request_dry_run_writes_nothing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-request", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["dry_run"] is True
    assert data["artifact_written"] is False
    assert data["execution_authorized"] is False
    assert not (tmp_path / ".pcae" / "runner-execution-requests" / "latest.json").exists()


def test_72u_execution_request_persists_with_correct_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-request", "--message", "Test request", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["requested"] is True
    assert data["approved"] is False
    assert data["denied"] is False
    assert data["revoked"] is False
    assert data["execution_authorized"] is False
    assert data["requester_source"] == "local_cli"
    assert data["artifact_written"] is True

    approval_path = tmp_path / ".pcae" / "runner-execution-requests" / "latest.json"
    assert approval_path.is_file()
    saved = json.loads(approval_path.read_text(encoding="utf-8"))
    assert saved["execution_authorized"] is False


def test_72u_execution_request_show_when_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Show test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-request-show", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["present"] is True
    assert data["execution_authorized"] is False
    assert data["requested"] is True


def test_72u_execution_request_show_none(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-request-show", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["present"] is False


def test_72u_execution_request_no_queue_mutation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 72A: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-execution-request", "--message", "No mutation"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


def test_72u_execution_request_no_task_created(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    before_tasks = list((tmp_path / "tasks" / "active").glob("*.md"))

    main(["phase", "runner-execution-request", "--message", "No tasks"])
    capsys.readouterr()

    assert list((tmp_path / "tasks" / "active").glob("*.md")) == before_tasks


# ---------------------------------------------------------------------------
# Phase 72V: execution authorization request review
# ---------------------------------------------------------------------------


def test_72v_request_review_missing_request(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-request-review", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["review_status"] == "missing_request"
    assert data["request_present"] is False
    assert data["approval_granted"] is False
    assert data["execution_authorized"] is False


def test_72v_request_review_with_request(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Review me"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-request-review", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["request_present"] is True
    assert data["approval_granted"] is False
    assert data["execution_authorized"] is False


def test_72v_request_review_save(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Save review test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-request-review", "--save", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["approval_granted"] is False
    assert data["execution_authorized"] is False
    review_path = tmp_path / ".pcae" / "runner-execution-request-reviews" / "latest.json"
    assert review_path.is_file()
    saved = json.loads(review_path.read_text(encoding="utf-8"))
    assert saved["execution_authorized"] is False


def test_72v_request_review_no_approval(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "No approval test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-request-review", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["approval_granted"] is False
    assert data["execution_authorized"] is False
    assert data["note"] is not None


# ---------------------------------------------------------------------------
# Phase 72W: execution authorization request denial and revocation
# ---------------------------------------------------------------------------


def test_72w_deny_missing_request(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-request-deny", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["denied"] is False
    assert data["execution_authorized"] is False


def test_72w_deny_with_request(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Deny me"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-request-deny", "--message", "Denied", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["denied"] is True
    assert data["execution_authorized"] is False
    denial_path = tmp_path / ".pcae" / "runner-execution-request-denials" / "latest.json"
    assert denial_path.is_file()
    saved = json.loads(denial_path.read_text(encoding="utf-8"))
    assert saved["execution_authorized"] is False


def test_72w_revoke_missing_request(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-request-revoke", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["revoked"] is False
    assert data["execution_authorized"] is False


def test_72w_revoke_with_request(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Revoke me"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-request-revoke", "--message", "Revoked", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["revoked"] is True
    assert data["execution_authorized"] is False
    revoke_path = tmp_path / ".pcae" / "runner-execution-request-revocations" / "latest.json"
    assert revoke_path.is_file()
    saved = json.loads(revoke_path.read_text(encoding="utf-8"))
    assert saved["execution_authorized"] is False


def test_72w_deny_does_not_mutate_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Queue check"])
    capsys.readouterr()
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 72A: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")

    main(["phase", "runner-execution-request-deny", "--message", "Denied"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


def test_72w_no_execution_authorized_true(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Auth check"])
    capsys.readouterr()

    deny = main(["phase", "runner-execution-request-deny", "--json"])
    deny_data = json.loads(capsys.readouterr().out)
    assert deny_data["execution_authorized"] is False

    main(["phase", "runner-execution-request", "--message", "Revoke check"])
    capsys.readouterr()
    revoke = main(["phase", "runner-execution-request-revoke", "--json"])
    revoke_data = json.loads(capsys.readouterr().out)
    assert revoke_data["execution_authorized"] is False


# ---------------------------------------------------------------------------
# Phase 72X: execution request preflight integration
# ---------------------------------------------------------------------------


def test_72x_preflight_missing_request(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["execution_request_present"] is False
    assert data["execution_request_status"] == "missing"
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False


def test_72x_preflight_with_request(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Preflight test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["execution_request_present"] is True
    assert data["execution_request_status"] == "present"
    assert data["request_blocks_authorization"] is False


def test_72x_preflight_denied_request_blocks(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Block me"])
    main(["phase", "runner-execution-request-deny", "--message", "Denied"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["execution_request_present"] is True
    assert data["execution_request_status"] == "denied"
    assert data["execution_request_denied"] is True
    assert data["request_blocks_authorization"] is True
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False


def test_72x_preflight_revoked_request_blocks(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Revoke me"])
    main(["phase", "runner-execution-request-revoke", "--message", "Revoked"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["execution_request_status"] == "revoked"
    assert data["execution_request_revoked"] is True
    assert data["request_blocks_authorization"] is True
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False


def test_72x_preflight_with_request_review(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Review me"])
    main(["phase", "runner-execution-request-review", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["execution_request_review_present"] is True
    assert data["execution_request_review_status"] is not None
    assert data["execution_authorized"] is False


# ---------------------------------------------------------------------------
# Phase 72Y: denied request authorization block
# ---------------------------------------------------------------------------


def test_72y_auth_refusal_missing_request(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-authorize", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["authorized"] is False
    assert data["authorization_available"] is False
    assert data["request_present"] is False
    assert data["request_denied"] is False
    assert data["request_revoked"] is False
    assert data["authorization_blocked_by_request_state"] is False


def test_72y_auth_refusal_with_request(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Auth test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-authorize", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["request_present"] is True
    assert data["request_denied"] is False
    assert data["authorization_blocked_by_request_state"] is False
    assert data["authorized"] is False


def test_72y_auth_refusal_denied_blocks(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Block auth"])
    main(["phase", "runner-execution-request-deny", "--message", "Denied"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-authorize", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["request_present"] is True
    assert data["request_denied"] is True
    assert data["authorization_blocked_by_request_state"] is True
    assert "denied" in data["refusal_reason"].lower()
    assert data["authorized"] is False


def test_72y_auth_refusal_revoked_blocks(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Revoke auth"])
    main(["phase", "runner-execution-request-revoke", "--message", "Revoked"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-authorize", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["request_revoked"] is True
    assert data["authorization_blocked_by_request_state"] is True
    assert "revoked" in data["refusal_reason"].lower()
    assert data["authorized"] is False


# ---------------------------------------------------------------------------
# Phase 72Z: authorization lifecycle summary artifact
# ---------------------------------------------------------------------------


def test_72z_summary_missing_artifacts(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-authorization-summary", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["overall_status"] == "incomplete"
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False
    assert data["execution_request"]["present"] is False
    assert data["execution_request"]["status"] == "missing"


def test_72z_summary_with_request(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Summary test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-authorization-summary", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["execution_request"]["present"] is True
    assert data["execution_request"]["status"] == "present"
    assert data["execution_request"]["blocks_authorization"] is False
    assert data["execution_authorized"] is False


def test_72z_summary_denied_request_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Block summary"])
    main(["phase", "runner-execution-request-deny", "--message", "Denied"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-authorization-summary", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["overall_status"] == "blocked"
    assert data["execution_request"]["blocks_authorization"] is True
    assert data["execution_request"]["status"] == "denied"
    assert data["execution_authorized"] is False


def test_72z_summary_revoked_request_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Rev summary"])
    main(["phase", "runner-execution-request-revoke", "--message", "Revoked"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-authorization-summary", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["overall_status"] == "blocked"
    assert data["execution_request"]["status"] == "revoked"
    assert data["execution_authorized"] is False


def test_72z_summary_save(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-authorization-summary", "--save", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["execution_authorized"] is False
    summary_path = tmp_path / ".pcae" / "runner-authorization-summaries" / "latest.json"
    assert summary_path.is_file()
    saved = json.loads(summary_path.read_text(encoding="utf-8"))
    assert saved["execution_authorized"] is False


def test_72z_summary_no_mutation(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 72A: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-authorization-summary"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# Phase 73A: runner no-op execution trace
# ---------------------------------------------------------------------------


def test_73a_noop_trace_json(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute", "--noop", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["noop"] is True
    assert data["execution_authorized"] is False
    assert data["execution_available"] is False
    assert data["would_execute"] is False
    assert data["mutation_performed"] is False
    assert data["tasks_created"] == 0
    assert data["queue_mutated"] is False
    assert "trace_id" in data
    assert "binding" in data


def test_73a_noop_trace_save(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute", "--noop", "--save", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    trace_path = tmp_path / ".pcae" / "runner-execution-traces" / "latest.json"
    assert trace_path.is_file()
    saved = json.loads(trace_path.read_text(encoding="utf-8"))
    assert saved["execution_authorized"] is False
    assert saved["noop"] is True


def test_73a_noop_no_mutation(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 72A: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-execute", "--noop"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


def test_73a_noop_preserves_refusal_without_noop(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["execution_authorized"] is False
    assert data["execution_available"] is False


# ---------------------------------------------------------------------------
# Phase 73B: runner no-op execution approval binding
# ---------------------------------------------------------------------------


def test_73b_noop_binding_empty_queue(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute", "--noop", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["binding"]["binding_complete"] is False
    assert "empty" in str(data["binding"]["binding_reasons"]).lower()


def test_73b_noop_binding_blocked_denied(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execution-request", "--message", "Block bind"])
    main(["phase", "runner-execution-request-deny", "--message", "Denied"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execute", "--noop", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["binding"]["execution_request_denied"] is True
    assert data["binding"]["binding_complete"] is False
    assert "denied" in str(data["binding"]["binding_reasons"]).lower()


def test_73b_noop_binding_with_fixture_and_approval(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"])
    main(["phase", "queue", "approve", "--message", "Bind test"])
    main(["phase", "runner-execution-request", "--message", "Bind req"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execute", "--noop", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["binding"]["queue_approval_present"] is True
    assert data["binding"]["queue_approval_matches_current_queue"] is True
    assert data["binding"]["execution_request_present"] is True
    assert data["binding"]["binding_complete"] is True
    assert data["execution_authorized"] is False


# ---------------------------------------------------------------------------
# Phase 73C: runner no-op execution abort scenarios
# ---------------------------------------------------------------------------


def test_73c_noop_scenario_dirty_tree(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute", "--noop", "--scenario", "dirty-tree", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["scenario"] == "dirty-tree"
    assert data["policy_category"] == "hard_stop"
    assert data["abort"] is True
    assert data["execution_authorized"] is False
    assert data["mutation_performed"] is False


def test_73c_noop_scenario_denied_request(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute", "--noop", "--scenario", "denied-request", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["scenario"] == "denied-request"
    assert data["abort"] is True
    assert data["execution_authorized"] is False


def test_73c_noop_scenario_queue_empty(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute", "--noop", "--scenario", "queue-empty", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["scenario"] == "queue-empty"
    assert data["policy_category"] == "continue_allowed"
    assert data["execution_authorized"] is False


def test_73c_noop_scenario_authorization_unavailable(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute", "--noop", "--scenario", "authorization-unavailable", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["scenario"] == "authorization-unavailable"
    assert data["abort"] is True
    assert data["execution_authorized"] is False


def test_73c_noop_scenario_no_mutation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 72A: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "runner-execute", "--noop", "--scenario", "active-task"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


def test_73c_noop_scenario_requires_noop(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execute", "--scenario", "dirty-tree", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert "error" in data


# ---------------------------------------------------------------------------
# Phase 73C.1: multi-phase implementation commit audit handling
# ---------------------------------------------------------------------------


def _create_phase_impl_only(root: Path, phase_id: str, description: str) -> None:
    dummy = root / "dummy.txt"
    dummy.write_text(f"impl {phase_id}", encoding="utf-8")
    run_git(root, "add", "dummy.txt")
    run_git(root, "commit", "-m", f"Implement Phase {phase_id} {description}")


def _create_phase_comp_only(root: Path, phase_id: str, description: str) -> None:
    dummy = root / "dummy.txt"
    dummy.write_text(f"comp {phase_id}", encoding="utf-8")
    run_git(root, "add", "dummy.txt")
    run_git(root, "commit", "-m", f"Complete Phase {phase_id} {description}")


def _create_shared_impl_commit(root: Path, subject: str) -> None:
    dummy = root / "dummy.txt"
    dummy.write_text("shared impl", encoding="utf-8")
    run_git(root, "add", "dummy.txt")
    run_git(root, "commit", "-m", subject)


def test_73c1_audit_dedicated_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_phase_commits(tmp_path, "73D", "dedicated test")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--last", "5", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase = next(p for p in data["phases"] if p["phase_id"] == "73D")
    assert phase["implementation_commit"] is not None
    assert phase.get("implementation_commit_shared") is False
    assert phase["commit_pair_complete"] is True
    assert len(data["warnings"]) == 0


def test_73c1_audit_missing_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_phase_comp_only(tmp_path, "73D", "comp only")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--last", "5", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase = next(p for p in data["phases"] if p["phase_id"] == "73D")
    assert phase["implementation_commit"] is None
    assert phase["commit_pair_complete"] is False
    assert any("missing implementation" in w for w in data["warnings"])


def test_73c1_audit_shared_range_commit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_shared_impl_commit(
        tmp_path, "Implement Phases 73D-73F shared range implementation"
    )
    _create_phase_comp_only(tmp_path, "73D", "comp D")
    _create_phase_comp_only(tmp_path, "73E", "comp E")
    _create_phase_comp_only(tmp_path, "73F", "comp F")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--last", "5", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase_d = next(p for p in data["phases"] if p["phase_id"] == "73D")
    assert phase_d.get("implementation_commit_shared") is True
    assert phase_d["implementation_commit"] is not None
    assert phase_d["commit_pair_complete"] is False
    assert any("shared multi-phase" in w for w in data["warnings"])
    assert any("73D" in w for w in data["warnings"])


def test_73c1_audit_shared_list_commit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_shared_impl_commit(
        tmp_path, "Implement Phases 73D, 73E, 73F shared list implementation"
    )
    _create_phase_comp_only(tmp_path, "73D", "comp D")
    _create_phase_comp_only(tmp_path, "73E", "comp E")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--last", "5", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase_d = next(p for p in data["phases"] if p["phase_id"] == "73D")
    assert phase_d.get("implementation_commit_shared") is True
    assert "shared multi-phase" in str(data["warnings"])


def test_73c1_audit_shared_and_commit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_shared_impl_commit(
        tmp_path, "Implement Phase 73D and 73E shared and implementation"
    )
    _create_phase_comp_only(tmp_path, "73D", "comp D")
    _create_phase_comp_only(tmp_path, "73E", "comp E")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--last", "5", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase_d = next(p for p in data["phases"] if p["phase_id"] == "73D")
    assert phase_d.get("implementation_commit_shared") is True
    assert "shared multi-phase" in str(data["warnings"])


def test_73c1_audit_dedicated_overrides_shared(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_shared_impl_commit(
        tmp_path, "Implement Phases 73D-73F shared range"
    )
    _create_phase_impl_only(tmp_path, "73D", "dedicated override")
    _create_phase_comp_only(tmp_path, "73D", "comp D")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--last", "5", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase_d = next(p for p in data["phases"] if p["phase_id"] == "73D")
    assert phase_d.get("implementation_commit_shared") is False
    assert phase_d["commit_pair_complete"] is True
    # Other phases from the shared commit may still warn about 73E/73F.
    # 73D itself must not have a shared-implementation warning.
    assert not any(w.startswith("Phase 73D:") and "shared multi-phase" in w for w in data["warnings"])


def test_73c1_audit_json_fields_for_shared(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    _create_shared_impl_commit(
        tmp_path, "Implement Phases 73D-73F shared range"
    )
    _create_phase_comp_only(tmp_path, "73D", "comp D")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "audit", "--last", "5", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    phase = next(p for p in data["phases"] if p["phase_id"] == "73D")
    assert "implementation_commit_shared" in phase
    assert phase["implementation_commit_shared"] is True
    assert "shared_commit_phase_ids" in phase
    assert isinstance(phase["shared_commit_phase_ids"], list)
    assert len(phase["shared_commit_phase_ids"]) > 1


# ---------------------------------------------------------------------------
# Phase 73D: runner no-op trace review artifact
# ---------------------------------------------------------------------------


def test_73d_trace_review_missing_trace(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-trace-review", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["trace_present"] is False
    assert data["review_status"] == "missing_trace"
    assert data["execution_authorized"] is False


def test_73d_trace_review_safe_trace(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execute", "--noop", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-trace-review", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["trace_present"] is True
    assert data["noop"] is True
    assert data["review_status"] == "ready_for_approval"
    assert data["execution_authorized"] is False


def test_73d_trace_review_save(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execute", "--noop", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-trace-review", "--save", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    review_path = tmp_path / ".pcae" / "runner-execution-trace-reviews" / "latest.json"
    assert review_path.is_file()
    saved = json.loads(review_path.read_text(encoding="utf-8"))
    assert saved["execution_authorized"] is False


def test_73d_trace_review_no_mutation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execute", "--noop", "--save"])
    capsys.readouterr()
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 73D: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")

    main(["phase", "runner-execution-trace-review"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# Phase 73E: runner no-op trace approval artifact
# ---------------------------------------------------------------------------


def test_73e_trace_approve_missing_review(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-trace-approve", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["approved"] is False
    assert data["execution_authorized"] is False


def test_73e_trace_approve_success(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execute", "--noop", "--save"])
    main(["phase", "runner-execution-trace-review", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-trace-approve", "--message", "Approved", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["approved"] is True
    assert data["noop_approved"] is True
    assert data["execution_authorized"] is False
    assert data["execution_available"] is False
    approval_path = tmp_path / ".pcae" / "runner-execution-trace-approvals" / "latest.json"
    assert approval_path.is_file()
    saved = json.loads(approval_path.read_text(encoding="utf-8"))
    assert saved["execution_authorized"] is False


def test_73e_trace_approve_dry_run(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execute", "--noop", "--save"])
    main(["phase", "runner-execution-trace-review", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-trace-approve", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["dry_run"] is True
    assert not (tmp_path / ".pcae" / "runner-execution-trace-approvals" / "latest.json").exists()


def test_73e_trace_approval_show(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execute", "--noop", "--save"])
    main(["phase", "runner-execution-trace-review", "--save"])
    main(["phase", "runner-execution-trace-approve", "--message", "Show test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-trace-approval-show", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["present"] is True
    assert data["execution_authorized"] is False


# ---------------------------------------------------------------------------
# Phase 73F: runner no-op execution preflight integration
# ---------------------------------------------------------------------------


def test_73f_preflight_missing_noop_trace(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["noop_trace_present"] is False
    assert data["noop_trace_safe"] is False
    assert data["noop_trace_review_present"] is False
    assert data["noop_trace_approval_present"] is False
    assert data["execution_authorized"] is False


def test_73f_preflight_safe_reviewed_approved_trace(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execute", "--noop", "--save"])
    main(["phase", "runner-execution-trace-review", "--save"])
    main(["phase", "runner-execution-trace-approve", "--message", "Preflight test"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["noop_trace_present"] is True
    assert data["noop_trace_safe"] is True
    assert data["noop_trace_review_present"] is True
    assert data["noop_trace_approval_present"] is True
    assert data["noop_trace_approval_matches_trace_or_review"] is True
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False


def test_73f_preflight_noop_approval_mismatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["phase", "runner-execute", "--noop", "--save"])
    main(["phase", "runner-execution-trace-review", "--save"])
    main(["phase", "runner-execution-trace-approve", "--message", "First"])
    capsys.readouterr()
    # Create a new trace — approval now references old trace
    main(["phase", "runner-execute", "--noop", "--save"])
    capsys.readouterr()

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["noop_trace_approval_matches_trace_or_review"] is False


def test_73f_preflight_still_design_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "runner-execution-preflight", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["preflight_status"] == "design_only"
    assert data["execution_available"] is False
    assert data["execution_authorized"] is False


# ---------------------------------------------------------------------------
# Phase 73G: single-phase runner contract design
# ---------------------------------------------------------------------------


def test_73g_contract_json(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "single-runner-contract", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["design_only"] is True
    assert data["execution_enabled"] is False
    assert data["execution_authorized"] is False
    assert len(data["minimum_requirements"]) > 10
    assert len(data["explicitly_forbidden"]) > 5


def test_73g_contract_save(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "single-runner-contract", "--save", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    contract_path = tmp_path / ".pcae" / "single-runner-contracts" / "latest.json"
    assert contract_path.is_file()
    saved = json.loads(contract_path.read_text(encoding="utf-8"))
    assert saved["design_only"] is True
    assert saved["execution_authorized"] is False


def test_73g_contract_no_mutation(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 73G: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "single-runner-contract"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


def test_73g_contract_human_output_states_design_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "single-runner-contract"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "design only" in output.lower()
    assert "does not enable" in output.lower()


# ---------------------------------------------------------------------------
# Phase 73H: single-phase runner readiness check
# ---------------------------------------------------------------------------


def test_73h_readiness_json(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "single-runner-readiness", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["ready_for_real_execution"] is False
    assert data["execution_authorized"] is False
    assert data["readiness_status"] in ("blocked", "incomplete", "design_ready")


def test_73h_readiness_save(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "single-runner-readiness", "--save", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    rd_path = tmp_path / ".pcae" / "single-runner-readiness" / "latest.json"
    assert rd_path.is_file()
    saved = json.loads(rd_path.read_text(encoding="utf-8"))
    assert saved["execution_authorized"] is False


def test_73h_readiness_no_mutation(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 73H: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "single-runner-readiness"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# Phase 73I: single-phase runner refusal matrix
# ---------------------------------------------------------------------------


def test_73i_refusal_matrix_json(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "single-runner-refusal-matrix", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["design_only"] is True
    assert data["execution_enabled"] is False
    assert len(data["refusal_matrix"]) > 15
    assert "categories" in data


def test_73i_refusal_matrix_save(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "single-runner-refusal-matrix", "--save", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    matrix_path = tmp_path / ".pcae" / "single-runner-refusal-matrices" / "latest.json"
    assert matrix_path.is_file()
    saved = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert saved["design_only"] is True
    assert len(saved["refusal_matrix"]) > 15


def test_73i_refusal_matrix_no_mutation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 73I: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "single-runner-refusal-matrix"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# Phase 73J: execution authorization artifact design
# ---------------------------------------------------------------------------


def test_73j_contract_json(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "execution-authorization-contract", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["design_only"] is True
    assert data["execution_enabled"] is False
    assert data["authorization_available"] is False
    assert data["execution_authorized"] is False
    assert len(data["required_fields"]) > 10
    assert len(data["required_invariants"]) > 5


def test_73j_contract_save(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "execution-authorization-contract", "--save", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    cpath = tmp_path / ".pcae" / "execution-authorization-contracts" / "latest.json"
    assert cpath.is_file()
    saved = json.loads(cpath.read_text(encoding="utf-8"))
    assert saved["execution_authorized"] is False


def test_73j_contract_no_mutation(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 73J: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "execution-authorization-contract"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# Phase 73K: execution authorization artifact schema and dry run
# ---------------------------------------------------------------------------


def test_73k_schema_json(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "execution-authorization-schema", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["schema_only"] is True
    assert data["authorization_available"] is False
    assert data["authorized"] is False
    assert data["execution_authorized"] is False


def test_73k_schema_save(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "execution-authorization-schema", "--save", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    spath = tmp_path / ".pcae" / "execution-authorization-schemas" / "latest.json"
    assert spath.is_file()
    saved = json.loads(spath.read_text(encoding="utf-8"))
    assert saved["execution_authorized"] is False


def test_73k_schema_dry_run_no_mutation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    queue_path = tmp_path / ".pcae" / "phase-queue.json"
    before = json.dumps(["Phase 73K: test"], indent=2) + "\n"
    queue_path.write_text(before, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["phase", "execution-authorization-schema", "--dry-run"])
    capsys.readouterr()

    assert queue_path.read_text(encoding="utf-8") == before

# ---------------------------------------------------------------------------
# Phase 73L: execution authorization matching rules
# ---------------------------------------------------------------------------
def test_73l_rules_json(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    d = json.loads(capsys.readouterr().out) if main(["phase", "execution-authorization-matching-rules", "--json"]) is not None else json.loads(capsys.readouterr().out)
    assert d["rules_only"]; assert not d["authorization_available"]; assert not d["execution_authorized"]; assert len(d["invalidation_rules"]) > 10

def test_73l_rules_save(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "execution-authorization-matching-rules", "--save", "--json"]); capsys.readouterr()
    assert (tmp_path / ".pcae" / "execution-authorization-matching-rules" / "latest.json").is_file()

def test_73l_rules_no_mutation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path)
    q = tmp_path / ".pcae" / "phase-queue.json"; b = json.dumps(["73L test"]) + "\n"; q.write_text(b); monkeypatch.chdir(tmp_path)
    main(["phase", "execution-authorization-matching-rules"]); capsys.readouterr()
    assert q.read_text() == b

# ---------------------------------------------------------------------------
# Phase 73M: negative gate integration
# ---------------------------------------------------------------------------
def test_73m_auth_gate_includes_contract_schema_rules(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "execution-authorization-contract", "--save"]); capsys.readouterr()
    main(["phase", "execution-authorization-schema", "--save"]); capsys.readouterr()
    main(["phase", "execution-authorization-matching-rules", "--save"]); capsys.readouterr()
    exit_code = main(["phase", "runner-execution-authorize", "--dry-run", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 1; assert d["authorized"] is False
    assert d["execution_authorization_contract_present"] is True
    assert d["execution_authorization_schema_present"] is True
    assert d["execution_authorization_matching_rules_present"] is True

def test_73m_auth_gate_missing_prereqs(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    exit_code = main(["phase", "runner-execution-authorize", "--dry-run", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 1; assert d["authorized"] is False
    assert d["execution_authorization_contract_present"] is False

def test_73m_auth_gate_no_positive_auth(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "execution-authorization-contract", "--save"]); capsys.readouterr()
    exit_code = main(["phase", "runner-execution-authorize", "--dry-run", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 1; assert d["authorized"] is False; assert d["execution_authorized"] not in d or d.get("execution_authorized") is not True

# ---------------------------------------------------------------------------
# Phase 73N: single-runner authorization readiness bridge
# ---------------------------------------------------------------------------
def test_73n_readiness_missing_layer(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-readiness", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["ready_for_real_execution"] is False; assert d["execution_authorized"] is False
    assert d["authorization_design_layer_complete"] is False

def test_73n_readiness_complete_layer(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "execution-authorization-contract", "--save"]); capsys.readouterr()
    main(["phase", "execution-authorization-schema", "--save"]); capsys.readouterr()
    main(["phase", "execution-authorization-matching-rules", "--save"]); capsys.readouterr()
    main(["phase", "single-runner-readiness", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["execution_authorization_contract_present"] is True
    assert d["authorization_design_layer_complete"] is True
    assert d["ready_for_real_execution"] is False; assert d["execution_authorized"] is False

def test_73n_readiness_still_blocks(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "execution-authorization-contract", "--save"]); capsys.readouterr()
    main(["phase", "single-runner-readiness", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["ready_for_real_execution"] is False; assert d["readiness_status"] != "design_ready"

# ---------------------------------------------------------------------------
# Phase 73O: real execution still-disabled proof
# ---------------------------------------------------------------------------
def test_73o_proof_passes(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    exit_code = main(["phase", "real-execution-disabled-proof", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 0; assert d["proof_status"] == "passed"
    assert d["real_execution_disabled"] is True; assert d["execution_authorized"] is False

def test_73o_proof_save(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "real-execution-disabled-proof", "--save", "--json"]); capsys.readouterr()
    assert (tmp_path / ".pcae" / "real-execution-disabled-proofs" / "latest.json").is_file()

def test_73o_proof_no_mutation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path)
    q = tmp_path / ".pcae" / "phase-queue.json"; b = json.dumps(["73O test"]) + "\n"; q.write_text(b); monkeypatch.chdir(tmp_path)
    main(["phase", "real-execution-disabled-proof"]); capsys.readouterr()
    assert q.read_text() == b

# ---------------------------------------------------------------------------
# Phase 73P: single queue item activation dry run
# ---------------------------------------------------------------------------
def test_73p_activate_dry_run_empty_queue(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-activate", "--dry-run", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["activation_allowed"] is False; assert d["task_created"] is False; assert d["execution_authorized"] is False

def test_73p_activate_dry_run_no_mutation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path)
    q = tmp_path / ".pcae" / "phase-queue.json"; b = json.dumps(["Phase 73P: test"]) + "\n"; q.write_text(b); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-activate", "--dry-run"]); capsys.readouterr()
    assert q.read_text() == b; assert not (tmp_path / "tasks" / "active" / "test").exists()

def test_73p_activate_dry_run_with_approved_queue(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "test"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--dry-run", "--allow-fixture", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["activation_allowed"] is True; assert d["would_create_task"] is True; assert d["task_created"] is False

def test_73p_activate_dry_run_blocked_by_active_task(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness; from pcae.core.tasks import create_task_contract
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); create_task_contract(HarnessPath(tmp_path), "blocking"); patch_task_allowed_files(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-activate", "--dry-run", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["activation_allowed"] is False

# ---------------------------------------------------------------------------
# Phase 73Q: single queue item activation execution
# ---------------------------------------------------------------------------
def test_73q_activate_execute_creates_task(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "test"]); capsys.readouterr()
    exit_code = main(["phase", "single-runner-activate", "--execute", "--allow-fixture", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 0; assert d["activated"] is True
    assert d["task_created"] is True; assert d["prompt_executed"] is False
    assert d["execution_authorized"] is False
    assert (tmp_path / ".pcae" / "single-runner-activations" / "latest.json").is_file()

def test_73q_activate_refuses_dirty_tree(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    (tmp_path / "dirty.txt").write_text("x")
    main(["phase", "single-runner-activate", "--execute", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["activated"] is False; assert "dirty" in str(d["blockers"]).lower()

def test_73q_activate_refuses_empty_queue(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-activate", "--execute", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["activated"] is False

def test_73q_activation_show(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "test"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    exit_code = main(["phase", "single-runner-activation-show", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 0; assert d["present"] is True; assert d["execution_authorized"] is False

# ---------------------------------------------------------------------------
# Phase 73R: activation recovery and rollback guard
# ---------------------------------------------------------------------------
def test_73r_activation_status_no_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-activation-status", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["activation_present"] is False; assert d["rollback_available"] is False

def test_73r_rollback_dry_run_no_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-activation-rollback", "--dry-run", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["rollback_available"] is False; assert d["execution_authorized"] is False

def test_73r_rollback_execute_safe(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "test"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    exit_code = main(["phase", "single-runner-activation-rollback", "--execute", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 0; assert d["rollback_performed"] is True; assert d["active_task_removed"] is True
    assert d["execution_authorized"] is False

def test_73r_rollback_refuses_manual_task(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness; from pcae.core.tasks import create_task_contract
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); create_task_contract(HarnessPath(tmp_path), "manual"); patch_task_allowed_files(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-activation-rollback", "--execute", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["rollback_performed"] is False

# ---------------------------------------------------------------------------
# Phase 73S: activation end-to-end fixture scenario
# ---------------------------------------------------------------------------
def test_73s_scenario_passes(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    exit_code = main(["phase", "single-runner-activation-scenario", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code == 0; assert d["scenario_status"] == "passed"
    assert d["prompt_executed"] is False; assert d["execution_authorized"] is False

def test_73s_scenario_save(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-activation-scenario", "--save", "--json"]); capsys.readouterr()
    assert (tmp_path / ".pcae" / "single-runner-activation-scenarios" / "latest.json").is_file()

def test_73s_scenario_cleanup(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-activation-scenario"]); capsys.readouterr()
    assert not any((tmp_path / "tasks" / "active").glob("*.md")) if (tmp_path / "tasks" / "active").is_dir() else True

# ---------------------------------------------------------------------------
# Phase 73T: activation handoff and bootstrap visibility
# ---------------------------------------------------------------------------
def test_73t_handoff_includes_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness; from pcae.core.agent import acquire_agent_lock
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "test"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    acquire_agent_lock(HarnessPath(tmp_path), "claude-local")
    main(["phase", "handoff", "--next-agent", "claude-next", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["activation"] is not None; assert d["activation"]["activation_present"] is True
    assert d["activation"]["execution_authorized"] is False

def test_73t_handoff_no_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "handoff", "--next-agent", "claude-next", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["activation"] is None

# ---------------------------------------------------------------------------
# Phase 73U: activation boundary enforcement
# ---------------------------------------------------------------------------
def test_73u_boundary_no_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-activation-boundary", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["boundary_status"] == "no_activation"; assert d["execution_authorized"] is False

def test_73u_boundary_clean_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "test"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "single-runner-activation-boundary", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["boundary_status"] == "clean_activation_boundary"; assert d["implementation_detected"] is False

def test_73u_boundary_save(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "single-runner-activation-boundary", "--save", "--json"]); capsys.readouterr()
    assert (tmp_path / ".pcae" / "single-runner-activation-boundaries" / "latest.json").is_file()

# Phase 73V: activated task implementation handoff
def test_73v_handoff_no_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-implementation-handoff", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["handoff_status"] == "no_activated_task"; assert d["execution_authorized"] is False

def test_73v_handoff_ready(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "test"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "activated-task-implementation-handoff", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["handoff_status"] == "ready"; assert d["execution_authorized"] is False; assert d["prompt_executed"] is False

# Phase 73W: activated task implementation readiness
def test_73w_readiness_no_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-implementation-readiness", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["ready_for_manual_implementation"] is False; assert d["ready_for_automatic_implementation"] is False
    assert d["execution_authorized"] is False
def test_73w_readiness_ready(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "test"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "activated-task-implementation-readiness", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["ready_for_manual_implementation"] is True; assert d["execution_authorized"] is False

# Phase 73X: activated task implementation start gate
def test_73x_start_gate_no_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-implementation-start", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["start_gate_status"] == "blocked"; assert d["manual_implementation_allowed"] is False
    assert d["automatic_implementation_allowed"] is False; assert d["execution_authorized"] is False
def test_73x_start_gate_allowed(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "test"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "activated-task-implementation-start", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["manual_implementation_allowed"] is True; assert d["runner_execution_allowed"] is False
    assert d["execution_authorized"] is False

# Phase 73Y: activated task manual implementation scenario
def test_73y_scenario_passes(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    exit_code = main(["phase", "activated-task-manual-implementation-scenario", "--json"]); d = json.loads(capsys.readouterr().out)
    assert exit_code == 0; assert d["scenario_status"] == "passed"; assert d["execution_authorized"] is False
    assert d["automatic_implementation_allowed"] is False
def test_73y_scenario_save(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-manual-implementation-scenario", "--save", "--json"]); capsys.readouterr()
    assert (tmp_path / ".pcae" / "activated-task-manual-implementation-scenarios" / "latest.json").is_file()

# Phase 73Z: activated task completion flow
def test_73z_flow_no_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-completion-flow", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["flow_status"] == "no_activated_task"; assert d["execution_authorized"] is False
def test_73z_flow_save(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-completion-flow", "--save", "--json"]); capsys.readouterr()
    assert (tmp_path / ".pcae" / "activated-task-completion-flows" / "latest.json").is_file()

# Phase 74A: activated task lifecycle summary
def test_74a_summary_no_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-lifecycle-summary", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["lifecycle_status"] == "no_activation"; assert d["execution_authorized"] is False
def test_74a_summary_ready(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "test"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "activated-task-lifecycle-summary", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["lifecycle_status"] == "implementation_ready"; assert d["execution_authorized"] is False

# Phase 74B: agent implementation package
def test_74b_package_no_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-agent-package", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["package_status"] == "no_activated_task"; assert d["execution_authorized"] is False
def test_74b_package_ready(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "t"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "activated-task-agent-package", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["package_status"] == "ready"; assert d["automatic_invocation_allowed"] is False
# Phase 74C: agent start dry run
def test_74c_agent_start_dry_run_blocked(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-agent-start", "--dry-run", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["agent_start_allowed"] is False; assert d["execution_authorized"] is False
def test_74c_agent_start_dry_run_allowed(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "t"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "activated-task-agent-start", "--dry-run", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["agent_start_allowed"] is True; assert d["agent_invocation_performed"] is False
# Phase 74D: agent assistance start artifact
def test_74d_agent_start_execute_creates_artifact(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "t"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "activated-task-agent-start", "--execute", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["agent_assistance_started"] is True; assert d["agent_invocation_performed"] is False
    assert d["execution_authorized"] is False; assert (tmp_path/".pcae"/"activated-task-agent-starts"/"latest.json").is_file()
def test_74d_agent_start_show(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "t"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "activated-task-agent-start", "--execute"]); capsys.readouterr()
    main(["phase", "activated-task-agent-start-show", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["present"] is True; assert d["execution_authorized"] is False

# Phase 74E: agent output intake
def test_74e_intake_no_activation(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-agent-output-intake", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["intake_status"] == "no_activated_task"; assert d["execution_authorized"] is False
def test_74e_intake_from_file(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "t"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "activated-task-agent-start", "--execute"]); capsys.readouterr()
    (tmp_path / "output.txt").write_text("diff --git a/src/cli.py b/src/cli.py\n--- a/src/cli.py\n+++ b/src/cli.py\n@@ -1 +1 @@\n-old\n+new")
    main(["phase", "activated-task-agent-output-intake", "--from-file", "output.txt", "--save", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["intake_status"] == "recorded"; assert d["patch_detected"] is True; assert d["apply_performed"] is False
# Phase 74F: agent output review
def test_74f_review_missing_intake(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-agent-output-review", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["review_status"] == "missing_intake"; assert d["execution_authorized"] is False
def test_74f_review_ready(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "t"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "activated-task-agent-start", "--execute"]); capsys.readouterr()
    (tmp_path / "out.txt").write_text("test output")
    main(["phase", "activated-task-agent-output-intake", "--from-file", "out.txt", "--save"]); capsys.readouterr()
    main(["phase", "activated-task-agent-output-review", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["review_status"] == "ready_for_apply_dry_run"; assert d["apply_performed"] is False
# Phase 74G: agent output apply dry run
def test_74g_apply_dry_run_blocked(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "activated-task-agent-output-apply", "--dry-run", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["apply_allowed"] is False; assert d["execution_authorized"] is False
def test_74g_apply_dry_run_ready(tmp_path, monkeypatch, capsys):
    from pcae.commands.init import init_harness
    init_harness(HarnessPath(tmp_path)); init_git_repo(tmp_path); commit_baseline(tmp_path); monkeypatch.chdir(tmp_path)
    main(["phase", "queue", "fixture-add", "--count", "1"]); capsys.readouterr()
    main(["phase", "queue", "approve", "--message", "t"]); capsys.readouterr()
    main(["phase", "single-runner-activate", "--execute", "--allow-fixture"]); capsys.readouterr()
    main(["phase", "activated-task-agent-start", "--execute"]); capsys.readouterr()
    (tmp_path / "o.txt").write_text("output")
    main(["phase", "activated-task-agent-output-intake", "--from-file", "o.txt", "--save"]); capsys.readouterr()
    main(["phase", "activated-task-agent-output-review", "--save"]); capsys.readouterr()
    main(["phase", "activated-task-agent-output-apply", "--dry-run", "--json"]); d = json.loads(capsys.readouterr().out)
    assert d["apply_allowed"] is True; assert d["apply_performed"] is False
