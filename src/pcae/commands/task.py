from __future__ import annotations

import argparse
import json

from pcae.core.check import run_checks
from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.session import SessionUpdate, update_session_snapshot, write_session_snapshot
from pcae.core.status import check_project_status_coherence
from pcae.core.policy import load_policy
from pcae.core.tasks import (
    ActiveTask,
    TaskFinishResult,
    TaskMemoryDiagnostics,
    TaskTransitionRecord,
    build_task_finish_recovery_plan,
    TaskUpdate,
    close_active_task_by_identifier,
    close_latest_active_task,
    complete_latest_active_task,
    create_task_contract,
    diagnose_task_memory,
    find_latest_active_task,
    finish_active_task,
    repair_task_memory,
    transition_active_task,
    validate_task_finish,
    validate_task_transition,
    pause_latest_active_task,
    read_task_summaries,
    resume_latest_paused_task,
    TaskSummary,
    update_latest_active_task,
)


def run_task_new(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    allowed_zones = tuple(args.allowed_zone)
    forbidden_zones = tuple(args.forbidden_zone)
    validation_error = validate_requested_zones(root, allowed_zones + forbidden_zones)
    if validation_error is not None:
        print(validation_error)
        return 1

    allowed_files = tuple(args.allowed_file) if args.allowed_file else ()
    forbidden_files = tuple(args.forbidden_file) if args.forbidden_file else ()
    acceptance_criteria = tuple(args.acceptance_criterion) if getattr(args, "acceptance_criterion", None) else ()
    acceptance_checks = tuple(args.acceptance_check) if args.acceptance_check else ()
    goal = args.goal if args.goal else "TBD"
    mode = args.mode if args.mode else "implementation"
    enforcement_mode = args.enforcement_mode if args.enforcement_mode else "TBD"

    contract = create_task_contract(
        root,
        args.title,
        goal=goal,
        mode=mode,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        allowed_zones=allowed_zones,
        forbidden_zones=forbidden_zones,
        enforcement_mode=enforcement_mode,
        acceptance_criteria=acceptance_criteria,
        acceptance_checks=acceptance_checks,
    )

    from pcae.core.session import write_session_snapshot

    try:
        write_session_snapshot(root)
    except Exception:
        pass

    print(f"Created task contract: {contract.relative_path.as_posix()}")
    return 0


def validate_requested_zones(root: HarnessPath, requested_zones: tuple[str, ...]) -> str | None:
    if not requested_zones:
        return None

    policy = load_policy(root)
    if not policy.file_exists:
        return None
    if not policy.valid:
        return policy.error or "Invalid policy file."

    known_zones = set(policy.architecture_zones)
    for zone in requested_zones:
        if zone not in known_zones:
            return f"Unknown architecture zone: {zone}"
    return None


def run_task_close(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    if args.identifier is None:
        closed_task = close_latest_active_task(root)
    else:
        closed_task = close_active_task_by_identifier(root, args.identifier)

    if closed_task is None:
        if args.identifier is None:
            print("No active task contract found in tasks/active/.")
        else:
            print(f"No active task contract found for: {args.identifier}")
        return 1

    print(f"Closed task: {closed_task.task_id}")
    print(f"Title: {closed_task.title}")
    print(f"Moved to: {closed_task.destination_path.relative_to(root.path).as_posix()}")
    return 0


def run_task_pause(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    paused_task = pause_latest_active_task(root)
    if paused_task is None:
        print("No active task contract found to pause.")
        return 1

    print(f"Paused task: {paused_task.task_id}")
    print(f"Title: {paused_task.title}")
    return 0


def run_task_resume(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    resumed_task = resume_latest_paused_task(root)
    if resumed_task is None:
        print("No paused task contract found to resume.")
        return 1

    print(f"Resumed task: {resumed_task.task_id}")
    print(f"Title: {resumed_task.title}")
    return 0


def run_task_complete(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    completed_task = complete_latest_active_task(root)
    if completed_task is None:
        print("No active task contract found to complete.")
        return 1

    print(f"Completed task: {completed_task.task_id}")
    print(f"Title: {completed_task.title}")
    print(f"Moved to: {completed_task.destination_path.relative_to(root.path).as_posix()}")
    return 0


def _staged_file_snapshot(root_path):
    """Return {path: blob_hash} for all staged files."""
    import subprocess as _sp
    r = _sp.run(["git", "diff", "--cached", "--name-only"],
                cwd=root_path, capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        return {}
    paths = [l for l in r.stdout.strip().split("\n") if l]
    result = {}
    for p in paths:
        h = _sp.run(["git", "rev-parse", f":0:{p}"],
                     cwd=root_path, capture_output=True, text=True, timeout=10)
        result[p] = h.stdout.strip() if h.returncode == 0 else ""
    return result


def run_task_finish(args: argparse.Namespace) -> int:
    import subprocess

    root = HarnessPath.cwd()
    skip_checks = getattr(args, "skip_checks", False)
    commit_message = getattr(args, "commit", None)
    staged_file_aware = getattr(args, "staged_file_aware", False)

    if commit_message and not staged_file_aware:
        from pcae.core.git_status import read_git_changes

        pre_changes = read_git_changes(root)
        if pre_changes:
            blocker = (
                f"Working tree has {len(pre_changes)} pre-existing change(s). "
                "Commit or stash them before using --commit."
            )
            if args.json:
                print(json.dumps({"blockers": [blocker], "committed": False, "finished": False}, indent=2, sort_keys=True))
            else:
                print(f"Task finish blocked.\n  - {blocker}")
            return 1

    # Snapshot protected staged files before task finish
    protected_before = {}
    if staged_file_aware and commit_message:
        protected_before = _staged_file_snapshot(root.path)

    validation = validate_task_finish(root, skip_checks=skip_checks)
    if not validation.safe_to_finish:
        if args.json:
            data = {
                "acceptance_checks": [
                    {"check": r.check, "exit_code": r.exit_code, "passed": r.passed}
                    for r in validation.acceptance_results
                ],
                "blockers": list(validation.blockers),
                "committed": False if commit_message else None,
                "finished": False,
                "task_id": (
                    validation.active_task.task_id
                    if validation.active_task
                    else None
                ),
                "warnings": list(validation.warnings),
            }
            if staged_file_aware:
                data["staged_file_aware"] = True
                data["protected_staged_files_before"] = sorted(protected_before.keys())
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            print("Task finish blocked.")
            for blocker in validation.blockers:
                print(f"  - {blocker}")
        return 1

    active_task_path = validation.active_task.path.relative_to(root.path)

    # Determine whether the active task file is tracked by git *before* moving it.
    # If it is untracked, staging the old active path after the move would fail with
    # a pathspec error (git has no record of that path to delete).
    _ls_check = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(active_task_path)],
        cwd=root.path,
        capture_output=True,
    )
    _active_task_was_tracked = _ls_check.returncode == 0

    try:
        result = finish_active_task(root, skip_checks=skip_checks)
    except ValueError as error:
        print(str(error))
        return 1

    commit_hash = None
    if commit_message:
        paths_to_stage = [str(active_task_path)] if _active_task_was_tracked else []
        for p in result.updated_files:
            paths_to_stage.append(p.as_posix())
        paths_to_stage.append(
            result.completed_task.destination_path.relative_to(root.path).as_posix()
        )
        unique_paths = list(dict.fromkeys(paths_to_stage))

        stageable_paths = []
        for p in unique_paths:
            check_ignored = subprocess.run(
                ["git", "check-ignore", "-q", p],
                cwd=root.path,
                capture_output=True,
            )
            if check_ignored.returncode != 0:
                stageable_paths.append(p)

        # Staged-file-aware: block if task-finish paths overlap protected staged files
        if staged_file_aware:
            conflict = set(stageable_paths) & set(protected_before.keys())
            if conflict:
                blockers = [f"Task finish path '{c}' is a protected pre-existing staged file." for c in sorted(conflict)]
                if args.json:
                    print(json.dumps({
                        "blockers": blockers,
                        "committed": False,
                        "finished": True,
                        "protected_staged_files_before": sorted(protected_before.keys()),
                        "staged_file_aware": True,
                        "task_id": result.completed_task.task_id,
                    }, indent=2, sort_keys=True))
                else:
                    print("Task finish committed blocked (staged-file-aware).")
                    for b in blockers:
                        print(f"  - {b}")
                return 1

        try:
            if stageable_paths:
                subprocess.run(
                    ["git", "add", "--"] + stageable_paths,
                    cwd=root.path,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            if staged_file_aware:
                # Commit only the explicit task-finish paths (pathspec commit)
                commit_result = subprocess.run(
                    ["git", "commit", "--no-verify", "-m", commit_message, "--"] + stageable_paths,
                    cwd=root.path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                commit_result = subprocess.run(
                    ["git", "commit", "--no-verify", "-m", commit_message],
                    cwd=root.path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            for line in commit_result.stdout.splitlines():
                if line.startswith("["):
                    parts = line.split()
                    if len(parts) >= 2:
                        commit_hash = parts[1].rstrip("]")
                    break
        except subprocess.CalledProcessError as error:
            err_text = error.stderr.strip()
            is_lock_error = (
                "index.lock" in err_text or "Operation not permitted" in err_text
            )
            if args.json:
                data = {
                    "committed": False,
                    "error": err_text,
                    "finished": True,
                    "task_id": result.completed_task.task_id,
                }
                if is_lock_error:
                    data["guidance"] = [
                        "pcae doctor git-lock",
                        "pcae task finish recover --dry-run",
                        f"pcae task finish recover --message \"{commit_message}\"",
                    ]
                if staged_file_aware:
                    data["staged_file_aware"] = True
                print(json.dumps(data, indent=2, sort_keys=True))
            else:
                print(f"Task finished but commit failed: {err_text}")
                if is_lock_error:
                    print()
                    print("Suggested next steps:")
                    print("  1. Run: pcae doctor git-lock")
                    print("  2. Run: pcae task finish recover --dry-run")
                    print(f"  3. Run: pcae task finish recover --message \"{commit_message}\"")
            return 1

    # Verify protected staged files preserved (staged-file-aware mode)
    protected_after = {}
    protected_preserved = True
    sfa_warnings = []
    if staged_file_aware and commit_message:
        protected_after = _staged_file_snapshot(root.path)
        for pp in protected_before:
            if pp not in protected_after:
                protected_preserved = False
                sfa_warnings.append(f"Protected staged file '{pp}' no longer staged after commit.")
            elif protected_after[pp] != protected_before[pp]:
                protected_preserved = False
                sfa_warnings.append(f"Protected staged file '{pp}' blob changed after commit.")

    # ── Phase 105C — report-trust validation + notification dispatch ────────
    # Only runs when a commit was actually made (mirrors "pcae task finish
    # --commit" being the real phase-closing workflow this integrates with).
    report_integration: dict | None = None
    if commit_message:
        report_integration = _finalize_task_report_and_notify(commit_hash)

    if args.json:
        data = {
            "acceptance_checks": [
                {"check": r.check, "exit_code": r.exit_code, "passed": r.passed}
                for r in result.acceptance_results
            ],
            "finished": True,
            "task_id": result.completed_task.task_id,
            "title": result.completed_task.title,
            "moved_to": result.completed_task.destination_path.relative_to(
                root.path
            ).as_posix(),
            "updated_files": [p.as_posix() for p in result.updated_files],
            "warnings": list(result.warnings) + sfa_warnings,
        }
        if commit_message:
            data["committed"] = True
            data["commit_hash"] = commit_hash
            data["commit_message"] = commit_message
        if staged_file_aware:
            data["staged_file_aware"] = True
            data["protected_staged_files_before"] = sorted(protected_before.keys())
            data["protected_staged_files_after"] = sorted(
                p for p in protected_before if p in protected_after
            )
            data["protected_staged_file_hashes_before"] = {
                p: protected_before[p] for p in sorted(protected_before)
            }
            data["protected_staged_file_hashes_after"] = {
                p: protected_after.get(p, "") for p in sorted(protected_before)
            }
            data["protected_staged_files_preserved"] = protected_preserved
            data["push_performed"] = False
            data["backend_invocation_performed"] = False
            data["runner_execute_performed"] = False
            data["execution_authorized"] = False
        if report_integration is not None:
            data["report_trust"] = report_integration.get("trust")
            data["repair_required"] = (
                report_integration.get("trust", {}).get("repair_required")
                if report_integration.get("trust")
                else None
            )
            data["notification_dispatch"] = {
                "status": report_integration.get("notification_status", report_integration["status"]),
                "reason": report_integration.get("notification_reason") or report_integration.get("message"),
                "sinks": report_integration.get("notification_sinks", []),
            }
            data["telegram_runtime"] = "outbound-only"
            data["report_path"] = report_integration.get("report_path")
            data["metadata_path"] = report_integration.get("metadata_path")
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"Finished task: {result.completed_task.task_id}")
        print(f"Title: {result.completed_task.title}")
        print(
            f"Moved to: {result.completed_task.destination_path.relative_to(root.path).as_posix()}"
        )
        if result.updated_files:
            print("Updated files:")
            for path in result.updated_files:
                print(f"  - {path.as_posix()}")
        if commit_hash:
            print(f"Committed: {commit_hash}")
        if staged_file_aware and protected_before:
            print(f"Protected staged files preserved: {'yes' if protected_preserved else 'no'}")
            for pp in sorted(protected_before):
                status = "preserved" if pp in protected_after and protected_after[pp] == protected_before[pp] else "LOST"
                print(f"  - {pp}: {status}")
        if result.warnings or sfa_warnings:
            print("Warnings:")
            for warning in list(result.warnings) + sfa_warnings:
                print(f"  - {warning}")
        if report_integration is not None:
            _print_report_integration_human(report_integration)

    return 0


# Phase 105C.1 — fields the OLD (95M.1) report-trust schema uses to signal
# that final push state (push status / origin-ahead-count / push-check) is
# not yet known. Promoted to `core/phase_report_trust.py` in Phase 105D so
# `commands/push.py` can share it too; these names are kept as aliases for
# backward compatibility (existing tests import `_apply_push_state_gate`
# directly from this module).
from pcae.core.phase_report_trust import PUSH_STATE_FIELDS as _PUSH_STATE_FIELDS  # noqa: E402


def _apply_push_state_gate(trust_result, report) -> None:
    """Phase 105C.1 — downgrade a 105A/105B trust result to partial when the
    OLD schema's push-state fields (`report.missing_trust_fields`) show
    final push state is still pending. Mutates `trust_result` in place.
    Thin wrapper around `core.phase_report_trust.apply_push_state_gate`
    (Phase 105D)."""
    from pcae.core.phase_report_trust import apply_push_state_gate

    if report is None:
        return
    apply_push_state_gate(trust_result, report.missing_trust_fields)


def _print_report_integration_human(report_integration: dict) -> None:
    """Phase 105C — human-readable report-trust/notification summary for
    `pcae task finish --commit`. Always states the Telegram outbound-only
    boundary explicitly."""
    status = report_integration["status"]
    print()
    if status in ("no_metadata", "invalid_metadata"):
        print(f"Report finalization: skipped ({report_integration['message']})")
        return

    trust = report_integration.get("trust") or {}
    print(f"Report trust: {trust.get('status', 'unknown')}")
    print(f"Repair required: {'yes' if trust.get('repair_required') else 'no'}")
    if trust.get("missing_fields"):
        print(f"  Missing fields: {', '.join(trust['missing_fields'])}")

    if status == "skipped_duplicate":
        print(f"Report notification: skipped ({report_integration['message']})")
    elif status == "report_error":
        print(f"Report finalization: ERROR — {report_integration['message']}")
    else:
        notif_status = report_integration.get("notification_status", "skipped")
        print(f"Report notification: {notif_status}")
        reason = report_integration.get("notification_reason")
        if reason:
            print(f"  Reason: {reason}")
        if notif_status == "skipped_incomplete":
            print("  Run final push/report completion path before dispatch.")
    print("Telegram: outbound-only")


def _finalize_task_report_and_notify(commit_hash: str | None) -> dict:
    """Phase 105C — finalize the phase-completion report, run the 105A/105B
    report-trust validator, and dispatch outbound notifications (Telegram)
    from `.pcae/phase-completion-metadata.json` during `pcae task finish
    --commit`.

    This is the actual PCAE phase-closing workflow; `pcae phase complete`
    already does this (via `finalize_phase_report`) but is not part of that
    workflow in day-to-day use. Warning-only: never raises, never blocks
    task finish. Read-only except for the local report/notification
    artifacts it creates — the same ones `pcae phase complete` creates for
    the same metadata file.
    """
    import os
    from pathlib import Path as _Path

    from pcae.core.phase_report_trust import (
        adapt_report_for_trust_check,
        validate_phase_report_trust,
    )
    from pcae.core.phase_reports import finalize_phase_report, read_latest_report

    meta_path = _Path(".pcae/phase-completion-metadata.json")
    if not meta_path.exists():
        return {
            "status": "no_metadata",
            "message": (
                "no .pcae/phase-completion-metadata.json found — skipping "
                "report finalization and notification dispatch"
            ),
        }

    try:
        meta = json.loads(meta_path.read_text())
    except json.JSONDecodeError as exc:
        return {"status": "invalid_metadata", "message": f"invalid JSON in {meta_path}: {exc}"}
    if not isinstance(meta, dict):
        return {"status": "invalid_metadata", "message": f"{meta_path} is not a JSON object"}

    phase_id = meta.get("phase_id", "")
    if not phase_id:
        return {"status": "no_metadata", "message": f"{meta_path} is missing phase_id — skipping"}

    phase_name = meta.get("phase_name") or meta.get("phase_title") or phase_id
    status = meta.get("status") or "completed"
    summary = meta.get("summary") or f"Phase {phase_id} completed via pcae task finish."

    governance_raw = meta.get("governance_results", [])
    governance_results: dict = {}
    if isinstance(governance_raw, list):
        for entry in governance_raw:
            name = entry.get("name", "") if isinstance(entry, dict) else ""
            if name:
                governance_results[name] = entry.get("status", "")
    elif isinstance(governance_raw, dict):
        governance_results = dict(governance_raw)

    test_results = meta.get("test_results", {})
    test_results = dict(test_results) if isinstance(test_results, dict) else {}
    if not test_results:
        for entry in meta.get("validation_results", []):
            name = entry.get("name", "") if isinstance(entry, dict) else ""
            if name:
                vresult = entry.get("result", "")
                vstatus = entry.get("status", "")
                test_results[name] = f"{vresult} ({vstatus})" if vstatus else vresult

    files_changed = meta.get("files_changed_count") or 0
    fc_list = meta.get("files_changed")
    if not files_changed and isinstance(fc_list, list):
        files_changed = len(fc_list)
    elif isinstance(fc_list, int):
        files_changed = fc_list

    tests_added = meta.get("tests_added_or_updated", "")
    tests_run = (
        int(tests_added.split()[0])
        if tests_added and tests_added.split()[0].isdigit()
        else 0
    )

    commit_attribution = meta.get("commit_attribution", "")
    if "phase_commits" in meta:
        commits = [
            c.get("hash", "")[:8]
            for c in meta.get("phase_commits", [])
            if isinstance(c, dict) and c.get("hash")
        ]
        if not commit_attribution:
            commit_attribution = "phase_owned" if commits else "none (no commits for this phase)"
    elif commit_hash:
        commits = [commit_hash[:8]]
    else:
        commits = []

    pushed_status = meta.get("pushed_status", "")
    origin_count = meta.get("origin_main_head_count", 0)
    recommended_next = meta.get("recommended_next_phase", "")
    no_go_text = meta.get("no_go_confirmation", "")
    no_go_list = [no_go_text] if no_go_text else []

    # Idempotency guard: skip dispatch if the same phase_id + commit was
    # already successfully dispatched by a prior finalization (e.g. an
    # earlier `pcae phase complete` for the same metadata). A dedicated
    # marker file is used rather than `PhaseReport.notification_result`,
    # because `finalize_phase_report()` writes the report artifact *before*
    # attempting dispatch, so the persisted report never reflects the
    # dispatch outcome.
    marker_path = _Path(".pcae/phase-reports/.last-notified.json")
    already_sent = False
    if commit_hash and marker_path.exists():
        try:
            marker = json.loads(marker_path.read_text())
        except json.JSONDecodeError:
            marker = {}
        marker_commit = marker.get("commit", "")
        already_sent = bool(
            marker.get("phase_id") == phase_id
            and marker_commit
            and (commit_hash.startswith(marker_commit) or marker_commit.startswith(commit_hash))
        )
    if already_sent:
        existing = read_latest_report(_Path(".pcae/phase-reports"))
        trust_result = (
            validate_phase_report_trust(adapt_report_for_trust_check(existing.to_dict()))
            if existing
            else validate_phase_report_trust({})
        )
        _apply_push_state_gate(trust_result, existing)
        return {
            "status": "skipped_duplicate",
            "message": (
                f"report for phase {phase_id} at commit {commit_hash} was "
                "already dispatched — skipping duplicate send"
            ),
            "trust": trust_result.to_dict(),
            "phase_id": phase_id,
        }

    notify_enabled = os.environ.get("PCAE_NOTIFY_ENABLED", "").lower() in ("1", "true", "yes")

    # Phase 105C.1 — build a trial report (no I/O: no write, no dispatch) to
    # learn push-state-aware completeness *before* deciding whether this
    # finalization is allowed to dispatch as a final trusted report. This is
    # what 105C was missing: it dispatched whenever notifications were
    # enabled, without checking whether pushed_status/origin_main_head/
    # pcae_push_check indicated final push state had actually been reached.
    from pcae.core.phase_reports import _apply_canonical_and_trust, make_phase_report

    trial_report = make_phase_report(
        phase_id=phase_id,
        phase_name=phase_name,
        status=status,
        summary=summary,
        files_changed=files_changed,
        tests_run=tests_run,
        test_results=test_results,
        governance_results=governance_results,
        commits=commits,
        pushed_status=pushed_status,
        origin_main_head_count=origin_count,
        explicit_no_go_confirmations=no_go_list,
        recommended_next_phase=recommended_next,
    )
    trial_report.metadata["commit_attribution"] = commit_attribution
    _apply_canonical_and_trust(trial_report, phase_id, phase_name, status)

    trial_trust = validate_phase_report_trust(
        adapt_report_for_trust_check(trial_report.to_dict())
    )
    _apply_push_state_gate(trial_trust, trial_report)
    dispatch_allowed = trial_trust.complete

    # Suppress dispatch (but still finalize/write the report) when the
    # report is not yet dispatch-ready — e.g. final push state is pending.
    # Prefer skip over sending a partial report labeled as final.
    suppressed_notify_enabled = None
    if not dispatch_allowed and notify_enabled:
        suppressed_notify_enabled = os.environ.get("PCAE_NOTIFY_ENABLED")
        os.environ["PCAE_NOTIFY_ENABLED"] = ""
    try:
        fin = finalize_phase_report(
            phase_id=phase_id,
            phase_name=phase_name,
            status=status,
            summary=summary,
            files_changed=files_changed,
            tests_run=tests_run,
            test_results=test_results,
            governance_results=governance_results,
            commits=commits,
            pushed_status=pushed_status,
            origin_main_head_count=origin_count,
            explicit_no_go_confirmations=no_go_list,
            recommended_next_phase=recommended_next,
            commit_attribution=commit_attribution,
        )
    finally:
        if suppressed_notify_enabled is not None:
            os.environ["PCAE_NOTIFY_ENABLED"] = suppressed_notify_enabled

    if fin.get("report_error"):
        return {
            "status": "report_error",
            "message": fin["report_error"],
            "phase_id": phase_id,
        }

    report = fin.get("report")
    paths = fin.get("paths") or {}

    # Trust-validate the actual finalized report (which now carries the
    # derived commits/pushed_status/etc.), not the raw metadata file — the
    # metadata alone is often intentionally incomplete (e.g. commits are
    # derived from commit_hash, not stored in the file).
    trust_result = validate_phase_report_trust(
        adapt_report_for_trust_check(report.to_dict())
    ) if report else validate_phase_report_trust({})
    _apply_push_state_gate(trust_result, report)

    result = {
        "status": "finalized",
        "phase_id": phase_id,
        "trust": trust_result.to_dict(),
        "report_completeness": report.report_completeness if report else "",
        "report_path": paths.get("markdown", ""),
        "metadata_path": str(meta_path),
    }

    if not dispatch_allowed:
        result["notification_status"] = "skipped_incomplete"
        result["notification_reason"] = (
            "report is not final push-state complete — "
            f"missing: {', '.join(trust_result.missing_fields)}. "
            "Run final push/report completion path before dispatch."
        )
        return result

    if fin.get("notification_skipped"):
        result["notification_status"] = "skipped"
        result["notification_reason"] = (
            "PCAE_NOTIFY_ENABLED is not set to 1/true/yes"
            if not notify_enabled
            else "notification sinks not fully configured"
        )
    else:
        nresults = fin.get("notification_results") or []
        all_ok = bool(nresults) and all(r.success for r in nresults)
        result["notification_status"] = "sent" if all_ok else "failed"
        result["notification_sinks"] = [r.sink_name for r in nresults]
        if fin.get("notification_error"):
            result["notification_reason"] = fin["notification_error"]
        if all_ok and commit_hash:
            marker_path.parent.mkdir(parents=True, exist_ok=True)
            marker_path.write_text(json.dumps({
                "phase_id": phase_id,
                "commit": commit_hash[:8],
            }))

    return result


def run_task_finish_recover(args: argparse.Namespace) -> int:
    import subprocess

    root = HarnessPath.cwd()
    message = getattr(args, "message", None)
    dry_run = getattr(args, "dry_run", False)
    plan = build_task_finish_recovery_plan(root, message=message)

    data = {
        "commit_hash": None,
        "commit_message": plan.commit_message,
        "closure_files": [path.as_posix() for path in plan.closure_files],
        "detected_task_id": plan.task_id,
        "dry_run": dry_run,
        "recoverable": plan.recoverable,
        "recovered": False,
        "refusal_reason": plan.refusal_reason,
        "title": plan.title,
    }

    if not plan.recoverable:
        if args.json:
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            print("Task finish recovery refused.")
            print(f"  - {plan.refusal_reason}")
        return 1

    if dry_run:
        if args.json:
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            print("Task finish recovery dry-run.")
            print(f"Task: {plan.task_id}")
            print(f"Commit message: {plan.commit_message}")
            print("Closure files:")
            for path in plan.closure_files:
                print(f"  - {path.as_posix()}")
        return 0

    stageable = [path.as_posix() for path in plan.closure_files]
    try:
        subprocess.run(
            ["git", "add", "--"] + stageable,
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "--no-verify", "-m", plan.commit_message or ""],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        rev = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        data["commit_hash"] = rev.stdout.strip()
        data["recovered"] = True
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.strip()
        data["refusal_reason"] = stderr or "git recovery command failed"
        if args.json:
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            print(f"Task finish recovery failed: {data['refusal_reason']}")
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"Recovered task finish: {plan.task_id}")
        print(f"Committed: {data['commit_hash']}")
        print(f"Commit message: {plan.commit_message}")
        print("Closure files:")
        for path in plan.closure_files:
            print(f"  - {path.as_posix()}")
    return 0


def run_task_list(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    active_tasks = read_task_summaries(root, "active")
    done_tasks = read_task_summaries(root, "done")

    if not active_tasks and not done_tasks:
        print("No task contracts found.")
        return 0

    print_task_section("Active tasks", active_tasks)
    print_task_section("Done tasks", done_tasks)
    return 0


def run_task_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    active_task = find_latest_active_task(root)
    if active_task is None:
        print("No active task contract found in tasks/active/.")
        return 1

    print(format_active_task(active_task))
    return 0


def run_task_update(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    active_task = find_latest_active_task(root)
    if active_task is None:
        print("No active task contract found in tasks/active/.")
        return 1

    allowed_zones = tuple(args.allowed_zone or ())
    forbidden_zones = tuple(args.forbidden_zone or ())
    validation_error = validate_requested_zones(root, allowed_zones + forbidden_zones)
    if validation_error is not None:
        print(validation_error)
        return 1

    if args.enforcement_mode is not None and args.enforcement_mode not in {
        "advisory",
        "strict",
        "TBD",
    }:
        print("Invalid enforcement mode: expected advisory, strict, or TBD.")
        return 1

    updated_task = update_latest_active_task(
        root,
        TaskUpdate(
            goal=args.goal,
            mode=args.mode,
            allowed_files=(
                tuple(args.allowed_file)
                if args.allowed_file is not None
                else None
            ),
            forbidden_files=(
                tuple(args.forbidden_file)
                if args.forbidden_file is not None
                else None
            ),
            allowed_zones=(
                allowed_zones
                if args.allowed_zone is not None
                else None
            ),
            forbidden_zones=(
                forbidden_zones
                if args.forbidden_zone is not None
                else None
            ),
            enforcement_mode=args.enforcement_mode,
            acceptance_criteria=(
                tuple(args.acceptance_criterion)
                if getattr(args, "acceptance_criterion", None) is not None
                else None
            ),
            acceptance_checks=(
                tuple(args.acceptance_check)
                if args.acceptance_check is not None
                else None
            ),
        ),
    )
    if updated_task is None:
        print("No active task contract found in tasks/active/.")
        return 1

    print(f"Updated task: {updated_task.task_id}")
    print(f"Title: {updated_task.title}")
    return 0


def run_task_transition(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    validation = validate_task_transition(root, args.next)
    if not validation.safe_to_complete:
        if args.json:
            print(
                json.dumps(
                    {
                        "blockers": list(validation.blockers),
                        "next_title": validation.next_title,
                        "safe_to_complete": False,
                        "warnings": list(validation.warnings),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print("Task transition blocked.")
            for blocker in validation.blockers:
                print(f"  - {blocker}")
        return 1

    try:
        transition = transition_active_task(root, args.next)
    except ValueError as error:
        print(str(error))
        return 1

    session_snapshot = write_session_snapshot(root)
    session_snapshot = update_session_snapshot(
        root,
        SessionUpdate(
            objective=transition.next_task.title,
            completed_step=(
                f"Completed task {transition.completed_task.task_id}: "
                f"{transition.completed_task.title}"
            ),
            next_step=f"Continue active task {transition.next_task.task_id}.",
        ),
    )
    coherence = check_project_status_coherence(root)
    health = build_health_data(root)
    check_result = run_checks(root)

    if args.json:
        print(json.dumps(task_transition_json(transition, session_snapshot.relative_path.as_posix(), coherence.coherent, health, check_result), indent=2, sort_keys=True))
    else:
        print_task_transition_summary(
            transition,
            session_snapshot.relative_path.as_posix(),
            coherence.coherent,
            health,
            check_result,
        )

    return 0 if coherence.coherent and health["overall_status"] == "healthy" and check_result.passed else 1


def print_task_section(title: str, tasks: tuple[TaskSummary, ...]) -> None:
    print(f"{title}:")
    if not tasks:
        print("  none")
        return

    for task in tasks:
        print(f"  [{task.status}] {task.task_id} - {task.title}")


def format_active_task(active_task: ActiveTask) -> str:
    lines = [
        "Active task:",
        f"  Task ID: {active_task.task_id}",
        f"  Title: {active_task.title}",
        f"  Status: {active_task.status}",
        f"  Mode: {active_task.mode}",
        f"  Goal: {active_task.goal or 'TBD'}",
        "Allowed files:",
        *format_items(active_task.allowed_files),
        "Forbidden files:",
        *format_items(active_task.forbidden_files),
        "Allowed zones:",
        *format_items(active_task.allowed_zones),
        "Forbidden zones:",
        *format_items(active_task.forbidden_zones),
        "Allowed dependencies:",
        *format_items(active_task.allowed_dependencies),
        "Forbidden dependencies:",
        *format_items(active_task.forbidden_dependencies),
        f"Enforcement mode: {active_task.enforcement_mode or 'TBD'}",
        "Acceptance criteria:",
        *format_items(active_task.acceptance_criteria),
        "Acceptance checks:",
        *format_items(active_task.acceptance_checks),
        "Documentation requirements:",
        *format_items(active_task.documentation_requirements),
    ]
    return "\n".join(lines)


def format_items(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["  - none"]
    return [f"  - {item}" for item in items]


def print_task_transition_summary(
    transition: TaskTransitionRecord,
    session_path: str,
    coherence_passed: bool,
    health: dict,
    check_result,
) -> None:
    print("Task transition complete.")
    print(f"Completed task: {transition.completed_task.task_id}")
    print(f"Completed title: {transition.completed_task.title}")
    print(
        "Moved to: "
        f"{transition.completed_task.destination_path.relative_to(HarnessPath.cwd().path).as_posix()}"
    )
    print(f"Next active task: {transition.next_task.task_id}")
    print(f"Next title: {transition.next_task.title}")
    print(f"Created: {transition.next_task.relative_path.as_posix()}")
    print(f"Session refreshed: {session_path}")
    print(f"Status coherence: {'passed' if coherence_passed else 'failed'}")
    print(f"Health: {health['overall_status']}")
    print(f"Check: {'passed' if check_result.passed else 'failed'}")
    if transition.warnings:
        print("Warnings:")
        for warning in transition.warnings:
            print(f"  - {warning}")
    print("Updated files:")
    for path in transition.updated_files:
        print(f"  - {path.as_posix()}")


def task_transition_json(
    transition: TaskTransitionRecord,
    session_path: str,
    coherence_passed: bool,
    health: dict,
    check_result,
) -> dict[str, object]:
    return {
        "check_passed": check_result.passed,
        "completed_task": {
            "id": transition.completed_task.task_id,
            "title": transition.completed_task.title,
            "path": transition.completed_task.destination_path.relative_to(
                HarnessPath.cwd().path
            ).as_posix(),
        },
        "health_status": health["overall_status"],
        "next_active_task": {
            "id": transition.next_task.task_id,
            "title": transition.next_task.title,
            "path": transition.next_task.relative_path.as_posix(),
        },
        "session_path": session_path,
        "status_coherence_passed": coherence_passed,
        "updated_files": [path.as_posix() for path in transition.updated_files],
        "warnings": list(transition.warnings),
    }


def run_doctor_task_memory(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    fix = getattr(args, "fix", False)
    dry_run = getattr(args, "dry_run", False)

    if fix:
        result = repair_task_memory(root, dry_run=dry_run)
        if args.json:
            print(json.dumps({
                "dry_run": dry_run,
                "post_findings": [
                    {"check": f.check, "message": f.message, "severity": f.severity}
                    for f in result.post_findings
                ],
                "pre_findings": [
                    {"check": f.check, "message": f.message, "severity": f.severity}
                    for f in result.pre_findings
                ],
                "repairs": [
                    {"action": r.action, "check": r.check, "path": r.path}
                    for r in result.repairs
                ],
                "skipped": [
                    {"check": f.check, "message": f.message, "severity": f.severity}
                    for f in result.skipped
                ],
            }, indent=2, sort_keys=True))
        else:
            if dry_run:
                print("Task memory repair (dry run)")
            else:
                print("Task memory repair")
            if result.repairs:
                print("Repairs:" if not dry_run else "Would repair:")
                for repair in result.repairs:
                    print(f"  [{repair.check}] {repair.action} → {repair.path}")
            if result.skipped:
                print("Skipped (requires human action):")
                for finding in result.skipped:
                    print(f"  [{finding.severity}] {finding.message}")
            if not dry_run:
                post_count = len(result.post_findings)
                if post_count == 0:
                    print("Post-fix: clean")
                else:
                    print(f"Post-fix: {post_count} finding(s) remaining")
        return 0

    diagnostics = diagnose_task_memory(root)

    if args.json:
        print(
            json.dumps(
                {
                    "clean": diagnostics.clean,
                    "findings": [
                        {
                            "check": f.check,
                            "severity": f.severity,
                            "message": f.message,
                        }
                        for f in diagnostics.findings
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        if diagnostics.clean:
            print("Task memory: clean")
            print("No inconsistencies detected.")
        else:
            print("Task memory: issues detected")
            for finding in diagnostics.findings:
                print(f"  [{finding.severity}] {finding.message}")

    return 1 if diagnostics.has_errors else 0


def _diagnose_git_lock(root: HarnessPath) -> dict:
    import os
    import subprocess as _sp

    git_dir = root.path / ".git"
    index_path = git_dir / "index"
    lock_path = git_dir / "index.lock"

    result: dict = {
        "lock_exists": False,
        "git_dir_writable": False,
        "index_writable": False,
        "status": "ok",
        "reason": "No lock file present and Git metadata is writable.",
        "suggested_action": "None required.",
    }

    if not git_dir.is_dir():
        result["status"] = "error"
        result["reason"] = ".git directory not found."
        result["suggested_action"] = "Verify this is a Git repository."
        return result

    result["git_dir_writable"] = os.access(git_dir, os.W_OK)
    result["index_writable"] = os.access(index_path, os.W_OK) if index_path.exists() else result["git_dir_writable"]

    if lock_path.exists():
        result["lock_exists"] = True
        git_running = False
        try:
            ps = _sp.run(
                ["pgrep", "-f", "git"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            git_running = ps.returncode == 0 and ps.stdout.strip() != ""
        except (OSError, _sp.TimeoutExpired):
            pass

        if git_running:
            result["status"] = "lock_present_active_process"
            result["reason"] = (
                ".git/index.lock exists and a Git process appears to be running."
            )
            result["suggested_action"] = (
                "Wait for the Git process to finish. "
                "If it is stuck, terminate it and then remove .git/index.lock manually."
            )
        else:
            result["status"] = "lock_present_stale"
            result["reason"] = (
                ".git/index.lock exists but no Git process appears to be running."
            )
            result["suggested_action"] = (
                "Remove .git/index.lock manually: rm .git/index.lock"
            )
        return result

    if not result["git_dir_writable"]:
        result["status"] = "permission_denied"
        result["reason"] = ".git directory is not writable."
        result["suggested_action"] = (
            "Fix file ownership or permissions on .git directory, "
            "or request elevated filesystem permissions."
        )
        return result

    if not result["index_writable"]:
        result["status"] = "permission_denied"
        result["reason"] = ".git/index is not writable."
        result["suggested_action"] = (
            "Fix file ownership or permissions on .git/index, "
            "or request elevated filesystem permissions."
        )
        return result

    return result


def run_doctor_git_lock(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    diag = _diagnose_git_lock(root)

    if args.json:
        print(json.dumps(diag, indent=2, sort_keys=True))
    else:
        print("Git lock diagnostic")
        print(f"  Lock exists: {diag['lock_exists']}")
        print(f"  .git writable: {diag['git_dir_writable']}")
        print(f"  index writable: {diag['index_writable']}")
        print(f"  Status: {diag['status']}")
        print(f"  Reason: {diag['reason']}")
        print(f"  Suggested action: {diag['suggested_action']}")

    return 1 if diag["status"] not in ("ok",) else 0


def _detect_active_pytest_processes() -> list[str]:
    """Return command lines of likely active expensive pytest (xdist) processes."""
    import re as _re
    import subprocess as _sp

    try:
        result = _sp.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return []

    matches = []
    for line in result.stdout.splitlines():
        lower = line.lower()
        # Exclude the ps aux process itself and grep lines
        if "ps aux" in line or "grep" in line:
            continue
        # Exclude shell processes: they may have pytest in their eval/exec args
        # but are not themselves running pytest. The COMMAND field (11th column)
        # must start with a python interpreter, not a shell.
        parts = line.split(None, 10)
        if len(parts) < 11:
            continue
        command_field = parts[10]
        cmd_lower = command_field.lower()
        if cmd_lower.startswith(("/bin/sh", "/bin/bash", "/bin/zsh", "sh ", "bash ", "zsh ")):
            continue
        is_pytest = ("pytest" in cmd_lower or "py.test" in cmd_lower) or (
            "python" in cmd_lower and "pytest" in lower
        )
        # Match -nauto, -n auto, -n2, -n 2, etc.
        is_xdist = bool(_re.search(r"-n\s*(auto|\d+)", command_field))
        if is_pytest and is_xdist:
            matches.append(line.strip())
    return matches


def run_doctor_test_run(args: argparse.Namespace) -> int:
    """Detect running expensive pytest processes to prevent overlapping full-suite runs."""
    active = _detect_active_pytest_processes()
    clear_to_run = len(active) == 0

    diag = {
        "check": "test_run_preflight",
        "clear_to_run": clear_to_run,
        "active_pytest_process_count": len(active),
        "active_pytest_processes": active,
        "policy": (
            "Conservative: false positives (reporting busy when clear) are acceptable. "
            "False negatives (reporting clear when busy) are more dangerous. "
            "Do not kill processes automatically. Do not start tests automatically."
        ),
    }

    if getattr(args, "json", False):
        print(json.dumps(diag, indent=2, sort_keys=True))
    else:
        if clear_to_run:
            print("Test-run preflight: clear to run.")
            print("  No active expensive pytest (xdist) process detected.")
        else:
            print(f"Test-run preflight: NOT clear to run.")
            print(f"  {len(active)} active pytest process(es) detected:")
            for p in active:
                print(f"    {p}")
            print("  Wait for existing runs to complete or stop them manually.")

    return 0 if clear_to_run else 1
