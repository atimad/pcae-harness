"""Phase 145H.3R.2 — Phase Completion Metadata Sequencing and Finalization
Independent Verification.

Fresh, independently authored adversarial coverage for the Phase 145H.3R.1
repair to ``run_phase_complete()`` (``src/pcae/commands/phase.py``). Does
not reuse fixtures or assertions from
``tests/test_phase_145h3r1_lock_sequencing_repair.py`` -- distinct fixture
shapes, distinct phase identities, and distinct scenarios (sequential
multi-phase lifecycle, other completion entry points, and the
``--stage-pending-report``/``--allow-partial-report`` quarantine-still-
completes behavior this phase's manual disposable-repository reproduction
surfaced as a pre-existing, out-of-scope design point, not a regression of
the repair).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.agent import acquire_agent_lock, read_agent_lock
from pcae.core.paths import HarnessPath
from pcae.core.provenance import read_provenance_history


def _git(tmp_path: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)


def _init(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "verify@example.com")
    _git(tmp_path, "config", "user.name", "Verify")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "baseline")


def _full_metadata(phase_id: str, commit_hash: str, next_phase: str) -> dict:
    return {
        "phase_id": phase_id,
        "phase_name": f"Independent Verification Fixture {phase_id}",
        "files_changed_count": 1,
        "tests_added_or_updated": "0 tests",
        "validation_results": [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": "passed"},
            {"name": "fast_green", "result": "1/1", "status": "passed"},
        ],
        "governance_results": [
            {"name": "pcae_health", "status": "healthy"},
            {"name": "pcae_check", "status": "passed"},
            {"name": "pcae_doctor_task_memory", "status": "clean"},
            {"name": "pcae_push_check", "status": "clean"},
            {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
        ],
        "no_go_confirmation": (
            "No validator bypass. No task finish integration. No notification "
            "enforcement. No push integration. No Permission Broker change. "
            "No execution. No REST. No Telegram inbound. No runtime invocation. "
            "No adapter execution. No automatic apply."
        ),
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "recommended_next_phase": next_phase,
        "phase_commits": [{"hash": commit_hash}],
        "commit_attribution": "phase_owned",
        "execution_availability": "unavailable",
    }


def _write_metadata(tmp_path: Path, data: dict) -> None:
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def _head(tmp_path: Path) -> str:
    out = subprocess.run(
        ["git", "log", "-1", "--format=%H"], cwd=tmp_path, capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _complete(tmp_path: Path, monkeypatch, phase_id: str, extra: list[str] | None = None) -> tuple[int, str]:
    monkeypatch.chdir(tmp_path)
    argv = [
        "phase", "complete", "--summary", f"{phase_id} complete.",
        "--phase-id", phase_id, "--phase-name", f"Independent Verification Fixture {phase_id}",
    ]
    if extra:
        argv.extend(extra)
    code = main(argv)
    return code, ""


def _event_types(root: HarnessPath) -> list[str]:
    return [e.event_type for e in read_provenance_history(root).events]


# ---------------------------------------------------------------------------
# 5.14 — Sequential phases each get an independent baseline: no lock
# leakage, no stale attribution, exactly one phase_completed/agent_released
# pair per phase, predecessor artifacts untouched.
# ---------------------------------------------------------------------------


def test_three_sequential_phases_independent_baselines(tmp_path, monkeypatch, capsys):
    root = HarnessPath(tmp_path)
    _init(tmp_path)

    for phase_id, next_id in (("V1", "V2"), ("V2", "V3"), ("V3", "done")):
        acquire_agent_lock(root, "claude-local")
        (tmp_path / f"{phase_id}.txt").write_text(phase_id, encoding="utf-8")
        _git(tmp_path, "add", ".")
        _git(tmp_path, "commit", "-m", f"Phase {phase_id}: work")
        _write_metadata(tmp_path, _full_metadata(phase_id, _head(tmp_path), next_id))

        code, _ = _complete(tmp_path, monkeypatch, phase_id)
        output = capsys.readouterr().out

        assert code == 0, f"phase {phase_id} unexpectedly failed to complete:\n{output}"
        assert read_agent_lock(root) is None, f"lock leaked past phase {phase_id}"

    events = _event_types(root)
    assert events.count("phase_completed") == 3
    assert events.count("agent_released") == 3


def test_stale_predecessor_metadata_does_not_misattribute_new_phase(tmp_path, monkeypatch, capsys):
    """The historical failure shape, reproduced with fresh fixture data:
    phase N-1's own completion metadata is still on disk (its *natural*
    post-completion state, not artificially stale-by-construction) when
    phase N's completion is attempted. Verify phase N's rejection is a
    clean REJECT that never records phase N's identity anywhere, and never
    silently substitutes phase N-1's identity for phase N's report.
    """
    root = HarnessPath(tmp_path)
    _init(tmp_path)

    acquire_agent_lock(root, "claude-local")
    (tmp_path / "predecessor.txt").write_text("p", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Phase PRED: predecessor work")
    _write_metadata(tmp_path, _full_metadata("PRED", _head(tmp_path), "NEXT"))
    code0, _ = _complete(tmp_path, monkeypatch, "PRED")
    capsys.readouterr()
    assert code0 == 0
    assert read_agent_lock(root) is None

    # Start the next phase without ever refreshing the completion metadata
    # -- exactly the historical precondition at 145G.3/145H.1/145H.2/145H.3.
    acquire_agent_lock(root, "claude-local")
    (tmp_path / "next.txt").write_text("n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Phase NEXT: new phase work")

    events_before = len(read_provenance_history(root).events)
    code1, _ = _complete(tmp_path, monkeypatch, "NEXT")
    output1 = capsys.readouterr().out

    assert code1 == 1
    assert "Transition rejected" in output1
    lock = read_agent_lock(root)
    assert lock is not None and lock.agent_id == "claude-local"
    assert len(read_provenance_history(root).events) == events_before

    # Correct the metadata (ordinary operator remediation) and retry with
    # no manual lock or metadata-recovery workaround beyond the correction
    # the operator was always going to have to make anyway.
    _write_metadata(tmp_path, _full_metadata("NEXT", _head(tmp_path), "done"))
    code2, _ = _complete(tmp_path, monkeypatch, "NEXT")
    output2 = capsys.readouterr().out
    assert code2 == 0
    assert read_agent_lock(root) is None
    events = _event_types(root)
    assert events.count("phase_completed") == 2
    assert events.count("agent_released") == 2


# ---------------------------------------------------------------------------
# Entry-point review — pcae task finish/complete never touch the agent lock
# at all, so they cannot share the repaired defect. Verified by direct
# behavioral test (not just grep), independent of the report's own claim.
# ---------------------------------------------------------------------------


def test_task_complete_does_not_touch_agent_lock(tmp_path, monkeypatch, capsys):
    root = HarnessPath(tmp_path)
    _init(tmp_path)
    monkeypatch.chdir(tmp_path)

    code_new = main(["task", "new", "some-task", "--goal", "g", "--allowed-file", "*"])
    capsys.readouterr()
    assert code_new == 0

    acquire_agent_lock(root, "claude-local")
    lock_before = read_agent_lock(root)
    assert lock_before is not None

    code_complete = main(["task", "complete"])
    capsys.readouterr()

    lock_after = read_agent_lock(root)
    assert lock_after is not None, "pcae task complete must never mutate the agent lock"
    assert lock_after.agent_id == lock_before.agent_id
    assert lock_after.data == lock_before.data


# ---------------------------------------------------------------------------
# --stage-pending-report / --allow-partial-report observation: these flags
# are a pre-existing, explicit opt-in ("I know this report cannot be
# trust-complete right now") that predates and is untouched by the
# 145H.3R.1 diff (the OR-logic computing `finalizable` from
# `dispatch_allowed or allow_partial_report or stage_pending_report` is
# unchanged code, not part of the reordering repair). This is NOT the
# recurring defect: the recurring defect was an *unrequested* lock release
# on an outright REJECT verdict with no override flag present, which
# remains fixed (see the tests above). This test documents, rather than
# asserts a bug, so any future removal of this behavior fails loudly here.
# ---------------------------------------------------------------------------


def test_stage_pending_report_flag_completes_despite_quarantine(tmp_path, monkeypatch, capsys):
    root = HarnessPath(tmp_path)
    _init(tmp_path)
    acquire_agent_lock(root, "claude-local")
    (tmp_path / "w.txt").write_text("w", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Phase QP: work")
    # Deliberately incomplete metadata -- not merely push-state-incomplete.
    _write_metadata(
        tmp_path,
        {
            "phase_id": "QP",
            "phase_name": "Quarantine-plus-flag fixture",
            "phase_commits": [{"hash": _head(tmp_path)}],
            "recommended_next_phase": "done",
        },
    )

    code, _ = _complete(tmp_path, monkeypatch, "QP", extra=["--stage-pending-report"])
    output = capsys.readouterr().out

    assert code == 0
    assert "quarantined" in output.lower()
    assert "Phase complete." in output
    assert read_agent_lock(root) is None
    events = _event_types(root)
    assert events.count("phase_completed") == 1
    assert events.count("agent_released") == 1


# ---------------------------------------------------------------------------
# Notification must not fire on a rejected completion; a rejected
# completion must not write any canonical latest.* artifact either.
# ---------------------------------------------------------------------------


def test_rejected_completion_writes_no_canonical_report_and_no_notification(tmp_path, monkeypatch, capsys):
    root = HarnessPath(tmp_path)
    _init(tmp_path)
    acquire_agent_lock(root, "claude-local")
    (tmp_path / "w.txt").write_text("w", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Phase RJ: work")
    _write_metadata(tmp_path, _full_metadata("WRONG_ID", _head(tmp_path), "done"))

    code, _ = _complete(tmp_path, monkeypatch, "RJ")
    output = capsys.readouterr().out

    assert code == 1
    assert "Transition rejected" in output
    assert "sent" not in output.lower()
    assert "[telegram]: OK" not in output
    latest_json = tmp_path / ".pcae" / "phase-reports" / "latest.json"
    if latest_json.exists():
        data = json.loads(latest_json.read_text(encoding="utf-8"))
        assert data.get("phase_id") != "RJ"
