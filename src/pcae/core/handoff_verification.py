"""Phase 114D: Cross-Agent Verification Command.

Read-only repository handoff verification: "is it safe for another
model, agent, automation, or human to continue here?" Aggregates
existing read-only signals -- git state, task state, phase/report state,
114C live push-state reconciliation, notification state, architecture
status, and runtime invariants -- into a single pass/warning/fail
verdict.

This module performs no mutation: no commit, no push, no notification,
no finalization, no task/report writes. It only reads git, the
filesystem, and calls other read-only core functions.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import phase_already_notified, read_latest_report
from pcae.core.push_state_reconciliation import compute_live_push_state, reconcile_push_state
from pcae.core.runtime_context import (
    CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
    CURRENT_RUNTIME_STATE,
    EXECUTION_AVAILABILITY,
)
from pcae.core.tasks import diagnose_task_memory, find_latest_active_task

STATUS_PASS = "pass"
STATUS_WARNING = "warning"
STATUS_FAIL = "fail"

_SEVERITY = {STATUS_PASS: 0, STATUS_WARNING: 1, STATUS_FAIL: 2}


@dataclass(frozen=True)
class HandoffCheck:
    name: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class HandoffVerificationResult:
    status: str
    checks: tuple[HandoffCheck, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    failures: tuple[str, ...] = field(default_factory=tuple)
    recommended_next_action: str = ""
    latest_completed_phase: str = ""
    recommended_next_phase: str = ""
    pushed_status: str = ""
    execution_availability: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "checks": [c.to_dict() for c in self.checks],
            "warnings": list(self.warnings),
            "failures": list(self.failures),
            "recommended_next_action": self.recommended_next_action,
            "latest_completed_phase": self.latest_completed_phase,
            "recommended_next_phase": self.recommended_next_phase,
            "pushed_status": self.pushed_status,
            "execution_availability": self.execution_availability,
        }


def _run_git(args: list[str], cwd: Path, timeout: int = 10) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None


def _overall_status(checks: list[HandoffCheck]) -> str:
    worst = STATUS_PASS
    for check in checks:
        if _SEVERITY[check.status] > _SEVERITY[worst]:
            worst = check.status
    return worst


# ── Git state (Objective 2) ─────────────────────────────────────────────────


def _check_git_state(root: HarnessPath) -> list[HandoffCheck]:
    checks: list[HandoffCheck] = []
    cwd = root.path

    status_result = _run_git(["status", "--porcelain=v1"], cwd)
    if status_result is None or status_result.returncode != 0:
        checks.append(HandoffCheck("git_working_tree", STATUS_WARNING, "could not determine working tree state"))
    else:
        lines = [l for l in status_result.stdout.splitlines() if l]
        if lines:
            untracked = [l for l in lines if l.startswith("??")]
            checks.append(HandoffCheck(
                "git_working_tree", STATUS_FAIL,
                f"working tree is dirty ({len(lines)} changed path(s), {len(untracked)} untracked)",
            ))
        else:
            checks.append(HandoffCheck("git_working_tree", STATUS_PASS, "working tree is clean"))

    branch_result = _run_git(["branch", "--show-current"], cwd)
    branch = branch_result.stdout.strip() if branch_result and branch_result.returncode == 0 else ""
    checks.append(HandoffCheck("git_branch", STATUS_PASS if branch else STATUS_WARNING, branch or "could not determine branch"))

    live = compute_live_push_state()
    if not live.determinable:
        checks.append(HandoffCheck(
            "git_origin_resolvable", STATUS_WARNING,
            "origin/main is not resolvable -- push state cannot be verified live",
        ))
    else:
        checks.append(HandoffCheck("git_origin_resolvable", STATUS_PASS, "origin/main resolves"))

        ahead = live.origin_main_head_count or 0
        if ahead == 0:
            checks.append(HandoffCheck("git_origin_main_head_count", STATUS_PASS, "origin/main..HEAD = 0"))
        else:
            checks.append(HandoffCheck(
                "git_origin_main_head_count", STATUS_FAIL,
                f"origin/main..HEAD = {ahead} (unpushed commits)",
            ))

        behind_result = _run_git(["rev-list", "--count", "HEAD..origin/main"], cwd)
        behind = None
        if behind_result and behind_result.returncode == 0 and behind_result.stdout.strip().isdigit():
            behind = int(behind_result.stdout.strip())
        if behind is None:
            checks.append(HandoffCheck("git_head_behind_origin", STATUS_WARNING, "could not determine HEAD..origin/main"))
        elif behind == 0:
            checks.append(HandoffCheck("git_head_behind_origin", STATUS_PASS, "HEAD..origin/main = 0"))
        else:
            checks.append(HandoffCheck(
                "git_head_behind_origin", STATUS_WARNING,
                f"HEAD..origin/main = {behind} (local branch is behind origin/main)",
            ))

        checks.append(HandoffCheck(
            "git_pushed_status", STATUS_PASS if live.pushed_status == "pushed" else STATUS_FAIL,
            f"live pushed_status = {live.pushed_status!r}",
        ))

    return checks


# ── Task state (Objective 3) ────────────────────────────────────────────────


def _check_task_state(root: HarnessPath) -> list[HandoffCheck]:
    checks: list[HandoffCheck] = []

    active_task = find_latest_active_task(root)
    if active_task is None:
        checks.append(HandoffCheck("task_active_task", STATUS_PASS, "no active task (idle) -- valid handoff state"))
    else:
        checks.append(HandoffCheck("task_active_task", STATUS_WARNING, f"active task present: {active_task.title!r}"))

    done_path = root.join(Path("tasks") / "DONE.md")
    if not done_path.exists():
        checks.append(HandoffCheck("task_done_log", STATUS_WARNING, "tasks/DONE.md is missing"))
    else:
        checks.append(HandoffCheck("task_done_log", STATUS_PASS, "tasks/DONE.md present"))

    todo_path = root.join(Path("tasks") / "TODO.md")
    if not todo_path.exists():
        checks.append(HandoffCheck("task_todo_freshness", STATUS_WARNING, "tasks/TODO.md is missing"))
    else:
        checks.append(HandoffCheck("task_todo_freshness", STATUS_PASS, "tasks/TODO.md present"))

    try:
        diagnostics = diagnose_task_memory(root)
        if diagnostics.clean:
            checks.append(HandoffCheck("task_memory_doctor", STATUS_PASS, "task memory clean"))
        elif diagnostics.has_errors:
            checks.append(HandoffCheck("task_memory_doctor", STATUS_FAIL, "task memory has error-severity inconsistencies"))
        else:
            checks.append(HandoffCheck("task_memory_doctor", STATUS_WARNING, "task memory has warning-severity inconsistencies"))
    except Exception:
        checks.append(HandoffCheck("task_memory_doctor", STATUS_WARNING, "pcae doctor task-memory not accessible"))

    return checks


# ── Phase/report state (Objective 4) ────────────────────────────────────────


def _load_metadata(root: HarnessPath) -> dict:
    path = root.join(Path(".pcae") / "phase-completion-metadata.json")
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_project_status_summary(root: HarnessPath) -> tuple[str, str]:
    """Returns (latest_completed_phase, recommended_next_phase), best-effort."""
    try:
        from pcae.core.context import build_context_pack

        pack = build_context_pack(root)
        rs = pack.roadmap_summary
        return str(rs.get("current_phase") or ""), str(rs.get("recommended_next_phase") or "")
    except Exception:
        return "", ""


def _check_phase_report_state(root: HarnessPath, metadata: dict) -> tuple[list[HandoffCheck], str, str]:
    checks: list[HandoffCheck] = []
    reports_dir = root.join(Path(".pcae") / "phase-reports")
    latest_json = reports_dir / "latest.json"
    latest_md = reports_dir / "latest.md"

    latest_completed_phase, recommended_next_phase = _read_project_status_summary(root)

    if not latest_json.exists():
        checks.append(HandoffCheck("report_exists", STATUS_FAIL, "no canonical phase report found (.pcae/phase-reports/latest.json missing)"))
        return checks, latest_completed_phase, recommended_next_phase

    report = read_latest_report(reports_dir)
    if report is None:
        checks.append(HandoffCheck("report_exists", STATUS_FAIL, "latest.json exists but could not be parsed"))
        return checks, latest_completed_phase, recommended_next_phase

    checks.append(HandoffCheck("report_exists", STATUS_PASS, f"canonical report present (phase_id={report.phase_id!r})"))

    metadata_phase_id = metadata.get("phase_id") if isinstance(metadata.get("phase_id"), str) else None
    if metadata_phase_id and metadata_phase_id != report.phase_id:
        checks.append(HandoffCheck(
            "report_metadata_phase_match", STATUS_FAIL,
            f"metadata phase_id {metadata_phase_id!r} does not match canonical report phase_id {report.phase_id!r}",
        ))
    else:
        checks.append(HandoffCheck("report_metadata_phase_match", STATUS_PASS, "metadata phase_id agrees with canonical report (or absent)"))

    completeness = getattr(report, "report_completeness", "")
    if completeness == "complete":
        checks.append(HandoffCheck("report_trust_completeness", STATUS_PASS, "report_completeness = complete"))
    elif completeness == "partial":
        checks.append(HandoffCheck("report_trust_completeness", STATUS_WARNING, "report_completeness = partial"))
    else:
        checks.append(HandoffCheck("report_trust_completeness", STATUS_FAIL, f"report_completeness = {completeness!r}"))

    if latest_md.exists():
        try:
            md_text = latest_md.read_text(encoding="utf-8")
        except Exception:
            md_text = ""
        if report.phase_id and report.phase_id in md_text:
            checks.append(HandoffCheck("report_md_json_agree", STATUS_PASS, "latest.md references the same phase_id as latest.json"))
        else:
            checks.append(HandoffCheck("report_md_json_agree", STATUS_FAIL, "latest.md does not reference latest.json's phase_id"))
    else:
        checks.append(HandoffCheck("report_md_json_agree", STATUS_WARNING, "latest.md is missing"))

    report_commits = list(getattr(report, "commits", []) or [])
    if report_commits:
        log_result = _run_git(["log", "--format=%h", "-100"], root.path)
        recent_hashes = set(log_result.stdout.split()) if log_result and log_result.returncode == 0 else set()
        matched = any(
            any(h.startswith(rc) or rc.startswith(h) for h in recent_hashes)
            for rc in report_commits
        )
        if matched:
            checks.append(HandoffCheck("report_commits_match_git", STATUS_PASS, "at least one reported commit found in recent git log"))
        else:
            checks.append(HandoffCheck(
                "report_commits_match_git", STATUS_WARNING,
                "none of the report's recorded commits were found in the last 100 git log entries",
            ))
    else:
        checks.append(HandoffCheck("report_commits_match_git", STATUS_WARNING, "report declares no commits"))

    return checks, latest_completed_phase, recommended_next_phase


# ── Push-state reconciliation (Objective 5, reuses 114C) ───────────────────


def _check_push_reconciliation(metadata: dict) -> tuple[list[HandoffCheck], str]:
    checks: list[HandoffCheck] = []
    reconciled = reconcile_push_state(metadata)

    if reconciled.metadata_push_state_stale:
        checks.append(HandoffCheck(
            "push_reconciliation", STATUS_WARNING,
            (
                f"declared metadata push state is stale (metadata_pushed_status="
                f"{reconciled.metadata_pushed_status!r}, metadata_origin_main_head_count="
                f"{reconciled.metadata_origin_main_head_count}, live_origin_main_head_count="
                f"{reconciled.live_origin_main_head_count})"
            ),
        ))
    else:
        checks.append(HandoffCheck("push_reconciliation", STATUS_PASS, "declared metadata agrees with live push state (or live state indeterminate)"))

    return checks, reconciled.pushed_status


# ── Notification state (Objective 6) ────────────────────────────────────────


def _check_notification_state(root: HarnessPath, latest_completed_phase: str) -> list[HandoffCheck]:
    checks: list[HandoffCheck] = []

    try:
        from pcae.core.notifications import TelegramSink

        sink = TelegramSink()
        if sink.is_enabled():
            checks.append(HandoffCheck("notification_transport", STATUS_PASS, "Telegram configured and enabled"))
        elif sink.is_configured():
            checks.append(HandoffCheck("notification_transport", STATUS_WARNING, "Telegram configured but not enabled"))
        else:
            checks.append(HandoffCheck("notification_transport", STATUS_WARNING, "Telegram not configured"))
    except Exception:
        checks.append(HandoffCheck("notification_transport", STATUS_WARNING, "notification transport state not determinable"))

    marker_path = root.join(Path(".pcae") / "phase-reports" / ".last-notified.json")
    phase_id_for_marker_check = None
    import re as _re
    match = _re.search(r"\b(\d{3}[A-Za-z](?:\.[A-Za-z0-9]+)?)\b", latest_completed_phase) if latest_completed_phase else None
    if match:
        phase_id_for_marker_check = match.group(1)

    if phase_id_for_marker_check:
        notified = phase_already_notified(phase_id_for_marker_check, marker_path=marker_path)
        if notified:
            checks.append(HandoffCheck("notification_marker", STATUS_PASS, f"latest completed phase {phase_id_for_marker_check!r} has a dispatch marker"))
        else:
            checks.append(HandoffCheck(
                "notification_marker", STATUS_WARNING,
                f"latest completed phase {phase_id_for_marker_check!r} has no notification dispatch marker -- "
                "acceptable (dispatch is opt-in and push-state gated), but visibility-reducing",
            ))
    else:
        checks.append(HandoffCheck("notification_marker", STATUS_WARNING, "could not determine latest completed phase for marker check"))

    return checks


# ── Architecture status (Objective 7) ───────────────────────────────────────


def _check_architecture_status(root: HarnessPath) -> list[HandoffCheck]:
    checks: list[HandoffCheck] = []
    reports_dir = root.join(Path(".pcae") / "phase-reports")
    report = read_latest_report(reports_dir)

    if report is None:
        checks.append(HandoffCheck("architecture_status_present", STATUS_WARNING, "no canonical report to check architecture status against"))
        return checks

    arch = getattr(report, "architecture_status", None) or {}
    if not isinstance(arch, dict) or not arch:
        checks.append(HandoffCheck("architecture_status_present", STATUS_WARNING, "architecture_status is absent or empty on the canonical report"))
        return checks

    checks.append(HandoffCheck("architecture_status_present", STATUS_PASS, "architecture_status present on canonical report"))

    completed_ids = arch.get("completed_phase_ids")
    if isinstance(completed_ids, list) and completed_ids:
        checks.append(HandoffCheck("architecture_completed_ids", STATUS_PASS, f"{len(completed_ids)} completed_phase_ids recorded"))
    else:
        checks.append(HandoffCheck("architecture_completed_ids", STATUS_WARNING, "no completed_phase_ids structured evidence found"))

    planned = arch.get("planned")
    if isinstance(planned, list) and isinstance(completed_ids, list):
        overlap = [p for p in planned if any(str(p).startswith(str(c)) for c in completed_ids)]
        if overlap:
            checks.append(HandoffCheck("architecture_no_duplicate_claim", STATUS_WARNING, f"planned phase(s) overlap with completed_phase_ids: {overlap}"))
        else:
            checks.append(HandoffCheck("architecture_no_duplicate_claim", STATUS_PASS, "no obvious planned/completed overlap detected"))
    else:
        checks.append(HandoffCheck("architecture_no_duplicate_claim", STATUS_WARNING, "insufficient structured data to check for duplicate claims"))

    return checks


# ── Runtime invariants (Objective 8) ────────────────────────────────────────


def _check_runtime_invariants() -> list[HandoffCheck]:
    checks: list[HandoffCheck] = []

    if EXECUTION_AVAILABILITY == "unavailable":
        checks.append(HandoffCheck("runtime_execution_availability", STATUS_PASS, "execution_availability = unavailable"))
    else:
        checks.append(HandoffCheck("runtime_execution_availability", STATUS_FAIL, f"execution_availability = {EXECUTION_AVAILABILITY!r} (expected 'unavailable')"))

    if CURRENT_RUNTIME_STATE == "Observed":
        checks.append(HandoffCheck("runtime_state", STATUS_PASS, "runtime state = Observed"))
    else:
        checks.append(HandoffCheck("runtime_state", STATUS_FAIL, f"runtime state = {CURRENT_RUNTIME_STATE!r} (expected 'Observed')"))

    if CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe":
        checks.append(HandoffCheck("runtime_max_plugin_capability", STATUS_PASS, "maximum plugin capability = observe"))
    else:
        checks.append(HandoffCheck(
            "runtime_max_plugin_capability", STATUS_FAIL,
            f"maximum plugin capability = {CURRENT_MAXIMUM_PLUGIN_CAPABILITY!r} (expected 'observe')",
        ))

    return checks


# ── Top-level entry point ───────────────────────────────────────────────────


def verify_handoff(root: HarnessPath | None = None) -> HandoffVerificationResult:
    """Read-only cross-agent handoff verification.

    Performs no mutation of any kind: no commit, no push, no notify, no
    finalize, no file write. Aggregates every check above into a single
    pass/warning/fail verdict.
    """
    root = root or HarnessPath.cwd()
    metadata = _load_metadata(root)

    all_checks: list[HandoffCheck] = []
    all_checks.extend(_check_git_state(root))
    all_checks.extend(_check_task_state(root))

    report_checks, latest_completed_phase, recommended_next_phase = _check_phase_report_state(root, metadata)
    all_checks.extend(report_checks)

    push_checks, reconciled_pushed_status = _check_push_reconciliation(metadata)
    all_checks.extend(push_checks)

    all_checks.extend(_check_notification_state(root, latest_completed_phase))
    all_checks.extend(_check_architecture_status(root))
    all_checks.extend(_check_runtime_invariants())

    status = _overall_status(all_checks)
    warnings = tuple(c.detail for c in all_checks if c.status == STATUS_WARNING)
    failures = tuple(c.detail for c in all_checks if c.status == STATUS_FAIL)

    if status == STATUS_PASS:
        recommended_next_action = "proceed"
    elif status == STATUS_WARNING:
        recommended_next_action = "review warnings before proceeding"
    else:
        recommended_next_action = "resolve failures before continuing"

    # Prefer the live-derived pushed_status (git state) for the top-level
    # summary field; fall back to the reconciled value when live state is
    # indeterminate (e.g. no origin/main configured).
    live = compute_live_push_state()
    pushed_status = live.pushed_status if live.determinable else reconciled_pushed_status

    return HandoffVerificationResult(
        status=status,
        checks=tuple(all_checks),
        warnings=warnings,
        failures=failures,
        recommended_next_action=recommended_next_action,
        latest_completed_phase=latest_completed_phase,
        recommended_next_phase=recommended_next_phase,
        pushed_status=pushed_status,
        execution_availability=EXECUTION_AVAILABILITY,
    )
