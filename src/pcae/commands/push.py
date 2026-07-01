from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import subprocess

from pcae.core.check import run_checks
from pcae.core.git_status import read_git_branch, read_git_changes
from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.policy import load_policy
from pcae.core.tasks import diagnose_task_memory


@dataclass(frozen=True)
class PushReadiness:
    branch: str
    clean: bool
    unpushed: int
    health_ok: bool
    check_ok: bool
    doctor_ok: bool
    doctor_warnings: bool
    mode: str
    ready: bool
    change_count: int
    review_status: str
    lifecycle_review_required: bool
    lifecycle_review_passed: bool
    lifecycle_review_reason: str
    phase_report_trust_status: str
    phase_report_trust_repair_required: bool
    phase_report_trust_missing_fields: tuple[str, ...]
    phase_report_trust_placeholder_fields: tuple[str, ...]


def _assess_phase_report_trust(root: HarnessPath) -> dict:
    """Phase 105D — validate the latest phase report's CONTENT completeness
    (105A/105B schema) as a push-check gate.

    Deliberately does NOT apply the 105C.1 push-state fold: task finish
    legitimately writes pushed_status/origin_main_head/pcae_push_check as
    pending before every push, and push-check already gates on live git
    state via its own unpushed-commit-count/clean-tree checks. Requiring
    the report to already claim "pushed" here would make push-check
    permanently unpassable for the normal task-finish-then-push sequence.
    See docs/PHASE_105_PHASE_REPORT_TRUST_HARD_FAIL_PUSH_CHECK_INTEGRATION.md.
    """
    latest_path = root.path / ".pcae" / "phase-reports" / "latest.json"
    if not latest_path.exists():
        return {
            "status": "skipped", "repair_required": False,
            "missing_fields": [], "placeholder_fields": [],
        }
    try:
        data = json.loads(latest_path.read_text())
    except json.JSONDecodeError:
        return {
            "status": "skipped", "repair_required": False,
            "missing_fields": [], "placeholder_fields": [],
        }
    if not isinstance(data, dict):
        return {
            "status": "skipped", "repair_required": False,
            "missing_fields": [], "placeholder_fields": [],
        }

    from pcae.core.phase_report_trust import compute_final_trust

    trust = compute_final_trust(data, push_state_aware=False)
    return {
        "status": "passed" if trust.complete else "failed",
        "repair_required": trust.repair_required,
        "missing_fields": trust.missing_fields,
        "placeholder_fields": trust.placeholder_fields,
    }


def assess_push_readiness(root: HarnessPath) -> PushReadiness:
    changes = read_git_changes(root)
    branch = read_git_branch(root)
    unpushed = _count_unpushed_commits(root)
    health = build_health_data(root)
    check_result = run_checks(root)
    diagnostics = diagnose_task_memory(root)
    phase_report_trust = _assess_phase_report_trust(root)

    clean = not changes
    from pcae.core.health import is_healthy

    health_ok = is_healthy(health)
    idle = health.get("idle", False)
    check_ok = check_result.passed
    doctor_ok = not diagnostics.has_errors

    mode = _determine_mode(
        clean=clean,
        health_ok=health_ok,
        idle=idle,
        check_ok=check_ok,
        doctor_ok=doctor_ok,
        unpushed=unpushed,
        check_result=check_result,
        root=root,
    )

    ready = mode in ("active_task", "post_finish_closure")

    from pcae.core.review import lifecycle_review_status
    from pcae.core.tasks import find_latest_active_task

    active_task = find_latest_active_task(root)
    task_id = active_task.task_id if active_task else None
    review = lifecycle_review_status(root, task_id)

    policy = load_policy(root)
    review_required = policy.lifecycle_review_require_approved
    review_passed, review_reason = _evaluate_lifecycle_review(
        review, review_required,
    )

    if review_required and not review_passed and ready:
        ready = False
        mode = "not_ready"

    # Phase 105D — a partial/placeholder-containing phase report blocks
    # push readiness (content completeness only; see
    # `_assess_phase_report_trust` for why push-state fields are excluded).
    if phase_report_trust["status"] == "failed" and ready:
        ready = False
        mode = "not_ready"

    return PushReadiness(
        branch=branch,
        clean=clean,
        unpushed=unpushed,
        health_ok=health_ok,
        check_ok=check_ok,
        doctor_ok=doctor_ok,
        doctor_warnings=diagnostics.has_warnings,
        mode=mode,
        ready=ready,
        change_count=len(changes),
        review_status=review,
        lifecycle_review_required=review_required,
        lifecycle_review_passed=review_passed,
        lifecycle_review_reason=review_reason,
        phase_report_trust_status=phase_report_trust["status"],
        phase_report_trust_repair_required=phase_report_trust["repair_required"],
        phase_report_trust_missing_fields=tuple(phase_report_trust["missing_fields"]),
        phase_report_trust_placeholder_fields=tuple(phase_report_trust["placeholder_fields"]),
    )


def run_push_check(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    readiness = assess_push_readiness(root)
    _print_readiness(readiness, args.json)
    return 0 if readiness.ready or readiness.mode == "nothing_to_push" else 1


def _staged_file_snapshot(root_path) -> dict[str, str]:
    """Return {path: blob_hash} for all staged files."""
    r = subprocess.run(["git", "diff", "--cached", "--name-only"],
                       cwd=root_path, capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        return {}
    paths = [l for l in r.stdout.strip().split("\n") if l]
    result = {}
    for p in paths:
        h = subprocess.run(["git", "rev-parse", f":0:{p}"],
                           cwd=root_path, capture_output=True, text=True, timeout=10)
        result[p] = h.stdout.strip() if h.returncode == 0 else ""
    return result


def _files_in_unpushed_range(root_path) -> list[str]:
    """Return file paths changed in origin/main..HEAD."""
    try:
        r = subprocess.run(["git", "diff", "--name-only", "origin/main..HEAD"],
                           cwd=root_path, capture_output=True, text=True, timeout=15)
        return [l for l in r.stdout.strip().split("\n") if l] if r.returncode == 0 else []
    except Exception:
        return []


def _unpushed_commit_lines(root_path) -> list[str]:
    try:
        r = subprocess.run(["git", "log", "--oneline", "origin/main..HEAD"],
                           cwd=root_path, capture_output=True, text=True, timeout=15)
        return [l for l in r.stdout.strip().split("\n") if l] if r.returncode == 0 else []
    except Exception:
        return []


def run_push(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    staged_file_aware = getattr(args, "staged_file_aware", False)
    dry_run = getattr(args, "dry_run", False)

    if staged_file_aware:
        return _run_push_staged_file_aware(root, args, dry_run)

    readiness = assess_push_readiness(root)

    if not readiness.ready:
        if args.json:
            print(json.dumps({
                **_readiness_dict(readiness),
                "pushed": False,
            }, indent=2, sort_keys=True))
        else:
            _print_readiness(readiness, json_mode=False)
        return 0 if readiness.mode == "nothing_to_push" else 1

    if dry_run:
        if args.json:
            print(json.dumps({
                **_readiness_dict(readiness),
                "dry_run": True,
                "pushed": False,
            }, indent=2, sort_keys=True))
        else:
            _print_readiness(readiness, json_mode=False)
            print("Dry run: push skipped.")
        return 0

    try:
        push_result = subprocess.run(
            ["git", "push"],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        push_output = (push_result.stdout + push_result.stderr).strip()
    except subprocess.CalledProcessError as error:
        if args.json:
            print(json.dumps({
                **_readiness_dict(readiness),
                "error": error.stderr.strip(),
                "pushed": False,
            }, indent=2, sort_keys=True))
        else:
            print(f"Push failed: {error.stderr.strip()}")
        return 1

    if args.json:
        print(json.dumps({
            **_readiness_dict(readiness),
            "push_output": push_output,
            "pushed": True,
        }, indent=2, sort_keys=True))
    else:
        _print_readiness(readiness, json_mode=False)
        print(f"Pushed: {push_output}")

    return 0


def _run_push_staged_file_aware(root: HarnessPath, args: argparse.Namespace, dry_run: bool) -> int:
    bl: list[str] = []
    wl: list[str] = []

    # Snapshot protected staged files
    protected_before = _staged_file_snapshot(root.path)

    # Get unpushed commits
    unpushed_lines = _unpushed_commit_lines(root.path)
    unpushed_count = len(unpushed_lines)
    unpushed_hashes = [l.split()[0] for l in unpushed_lines] if unpushed_lines else []

    if unpushed_count == 0:
        r = _sfa_push_result("nothing_to_push", "nothing_to_push", bl, wl,
                             protected_before=protected_before)
        if args.json:
            print(json.dumps(r, indent=2, sort_keys=True))
        else:
            print("Staged-file-aware push: nothing to push.")
        return 0

    # Check which files are in the unpushed range
    files_in_range = _files_in_unpushed_range(root.path)

    # Block if any protected staged file appears in unpushed commit contents
    protected_in_commits = [p for p in protected_before if p in files_in_range]
    if protected_in_commits:
        for p in protected_in_commits:
            bl.append(f"Protected staged file '{p}' appears in unpushed commit range.")
        r = _sfa_push_result("protected_file_in_unpushed_commits", "blocked", bl, wl,
                             protected_before=protected_before,
                             unpushed_lines=unpushed_lines,
                             files_in_range=files_in_range,
                             protected_in_commits=protected_in_commits)
        if args.json:
            print(json.dumps(r, indent=2, sort_keys=True))
        else:
            print("Staged-file-aware push blocked.")
            for b in bl:
                print(f"  - {b}")
        return 1

    # Check for force push requirement (origin/main must be ancestor of HEAD)
    try:
        anc = subprocess.run(["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"],
                             cwd=root.path, capture_output=True, timeout=10)
        if anc.returncode != 0:
            bl.append("origin/main is not ancestor of HEAD; force push would be required.")
            r = _sfa_push_result("force_push_required", "blocked", bl, wl,
                                 protected_before=protected_before,
                                 unpushed_lines=unpushed_lines,
                                 files_in_range=files_in_range)
            if args.json:
                print(json.dumps(r, indent=2, sort_keys=True))
            else:
                print("Staged-file-aware push blocked: force push required.")
            return 1
    except Exception:
        pass

    if dry_run:
        r = _sfa_push_result("ready", "dry_run", bl, wl,
                             protected_before=protected_before,
                             unpushed_lines=unpushed_lines,
                             files_in_range=files_in_range)
        if args.json:
            print(json.dumps(r, indent=2, sort_keys=True))
        else:
            print("Staged-file-aware push: ready (dry run, not pushing).")
            print(f"  Unpushed commits: {unpushed_count}")
            print(f"  Protected staged files: {len(protected_before)}")
        return 0

    # Execute governed push
    try:
        push_result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        push_output = (push_result.stdout + push_result.stderr).strip()
    except subprocess.CalledProcessError as error:
        bl.append(f"Push failed: {error.stderr.strip()[:200]}")
        r = _sfa_push_result("git_error", "blocked", bl, wl,
                             protected_before=protected_before,
                             unpushed_lines=unpushed_lines,
                             files_in_range=files_in_range)
        if args.json:
            print(json.dumps(r, indent=2, sort_keys=True))
        else:
            print(f"Staged-file-aware push failed: {error.stderr.strip()}")
        return 1

    # Post-push: verify protected staged files preserved
    protected_after = _staged_file_snapshot(root.path)
    protected_preserved = True
    for pp in protected_before:
        if pp not in protected_after:
            protected_preserved = False
            wl.append(f"Protected staged file '{pp}' no longer staged after push.")
        elif protected_after[pp] != protected_before[pp]:
            protected_preserved = False
            wl.append(f"Protected staged file '{pp}' blob changed after push.")

    unpushed_after = _unpushed_commit_lines(root.path)
    status = "pushed" if protected_preserved else "protected_staged_file_lost"

    r = _sfa_push_result(status, "pushed", bl, wl,
                         protected_before=protected_before,
                         protected_after=protected_after,
                         protected_preserved=protected_preserved,
                         unpushed_lines=unpushed_lines,
                         unpushed_after=unpushed_after,
                         files_in_range=files_in_range,
                         pushed_hashes=unpushed_hashes)
    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
    else:
        print(f"Staged-file-aware push: {push_output}")
        if protected_before:
            print(f"  Protected staged files preserved: {'yes' if protected_preserved else 'no'}")
    return 0


def _sfa_push_result(
    status: str, outcome: str, bl: list, wl: list,
    protected_before: dict | None = None,
    protected_after: dict | None = None,
    protected_preserved: bool = True,
    unpushed_lines: list | None = None,
    unpushed_after: list | None = None,
    files_in_range: list | None = None,
    protected_in_commits: list | None = None,
    pushed_hashes: list | None = None,
) -> dict:
    pb = protected_before or {}
    pa = protected_after or {}
    ul = unpushed_lines or []
    ua = unpushed_after or []
    fr = files_in_range or []
    return {
        "backend_invocation_performed": False,
        "blockers": bl,
        "branch": "main",
        "execution_authorized": False,
        "files_in_unpushed_commits": sorted(fr),
        "force_push_performed": False,
        "protected_file_in_unpushed_commits": sorted(protected_in_commits or []),
        "protected_staged_file_hashes_after": {p: pa.get(p, "") for p in sorted(pb)},
        "protected_staged_file_hashes_before": {p: pb[p] for p in sorted(pb)},
        "protected_staged_files_after": sorted(p for p in pb if p in pa),
        "protected_staged_files_before": sorted(pb.keys()),
        "protected_staged_files_preserved": protected_preserved,
        "push_outcome": outcome,
        "push_staged_file_aware_status": status,
        "pushed_commit_hashes": pushed_hashes or [],
        "raw_git_push_performed": False,
        "remote": "origin",
        "runner_execute_performed": False,
        "unexpected_staged_files": [],
        "unpushed_commit_hashes_before": [l.split()[0] for l in ul] if ul else [],
        "unpushed_commits_after": ua,
        "unpushed_commits_before": ul,
        "warnings": wl,
    }


def _readiness_dict(readiness: PushReadiness) -> dict:
    noop = readiness.mode == "nothing_to_push"
    blocked = readiness.mode == "not_ready"

    if readiness.ready:
        reason = "push can proceed"
    elif noop:
        reason = "no unpushed commits"
    else:
        reason = "push blocked by validation failure"

    return {
        "branch": readiness.branch,
        "check_passed": readiness.check_ok,
        "doctor_errors": not readiness.doctor_ok,
        "doctor_warnings": readiness.doctor_warnings,
        "health_status": "healthy" if readiness.health_ok else "unhealthy",
        "lifecycle_review": readiness.review_status,
        "lifecycle_review_passed": readiness.lifecycle_review_passed,
        "lifecycle_review_reason": readiness.lifecycle_review_reason,
        "lifecycle_review_required": readiness.lifecycle_review_required,
        "mode": readiness.mode,
        "phase_report_trust": readiness.phase_report_trust_status,
        "phase_report_trust_repair_required": readiness.phase_report_trust_repair_required,
        "phase_report_trust_missing_fields": list(readiness.phase_report_trust_missing_fields),
        "phase_report_trust_placeholder_fields": list(readiness.phase_report_trust_placeholder_fields),
        "push_action_required": blocked,
        "push_blocked": blocked,
        "push_noop": noop,
        "push_reason": reason,
        "ready": readiness.ready,
        "unpushed_commits": readiness.unpushed,
        "working_tree_clean": readiness.clean,
    }


def _print_readiness(readiness: PushReadiness, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(_readiness_dict(readiness), indent=2, sort_keys=True))
        return

    print("Push readiness check")
    print(f"  Branch: {readiness.branch}")
    print(f"  Working tree: {'clean' if readiness.clean else f'{readiness.change_count} changed file(s)'}")
    print(f"  Unpushed commits: {readiness.unpushed}")
    print(f"  Health: {'healthy' if readiness.health_ok else 'unhealthy'}")
    print(f"  Check: {'passed' if readiness.check_ok else 'failed'}")
    doctor_status = "clean" if readiness.doctor_ok and not readiness.doctor_warnings else "errors" if not readiness.doctor_ok else "warnings"
    print(f"  Task memory: {doctor_status}")
    review_line = f"  Lifecycle review: {readiness.review_status}"
    if readiness.lifecycle_review_required:
        enforcement = "passed" if readiness.lifecycle_review_passed else "failed"
        review_line += f" (required, {enforcement})"
    print(review_line)
    print(f"  Phase report trust: {readiness.phase_report_trust_status}")
    if readiness.phase_report_trust_status == "failed":
        print(f"    Repair required: {'yes' if readiness.phase_report_trust_repair_required else 'no'}")
        if readiness.phase_report_trust_missing_fields:
            print(f"    Missing fields: {', '.join(readiness.phase_report_trust_missing_fields)}")
        if readiness.phase_report_trust_placeholder_fields:
            print(f"    Placeholder fields: {', '.join(readiness.phase_report_trust_placeholder_fields)}")
    print(f"  Mode: {readiness.mode}")
    print()
    if readiness.ready:
        print("Ready to push.")
    elif readiness.mode == "nothing_to_push":
        print("Nothing to push.")
    else:
        reasons = []
        if not readiness.clean:
            reasons.append("working tree is dirty")
        if not readiness.health_ok and readiness.mode != "post_finish_closure":
            reasons.append("health is unhealthy")
        elif not readiness.health_ok:
            reasons.append("no active task (not a valid closure state)")
        if not readiness.check_ok and readiness.mode != "post_finish_closure":
            reasons.append("check has violations")
        if not readiness.doctor_ok:
            reasons.append("task memory has errors")
        if readiness.lifecycle_review_required and not readiness.lifecycle_review_passed:
            reasons.append(readiness.lifecycle_review_reason)
        if readiness.phase_report_trust_status == "failed":
            reasons.append("latest phase report trust is incomplete (partial/placeholder content)")
        print("Not ready to push:")
        for reason in reasons:
            print(f"  - {reason}")


def _evaluate_lifecycle_review(
    review_status: str,
    required: bool,
) -> tuple[bool, str]:
    if not required:
        return True, "lifecycle review is advisory (not required by policy)"

    passing = {"approved", "not_applicable"}
    if review_status in passing:
        return True, f"lifecycle review {review_status}"

    reasons = {
        "missing": "lifecycle review is missing (required by policy)",
        "changes_requested": "lifecycle review has changes requested",
        "informational_only": "lifecycle review is informational only (approval required by policy)",
        "mixed": "lifecycle review has conflicting dispositions (changes requested)",
        "unknown": "lifecycle review status is unknown",
    }
    return False, reasons.get(review_status, f"lifecycle review status: {review_status}")


def _determine_mode(
    *,
    clean: bool,
    health_ok: bool,
    idle: bool,
    check_ok: bool,
    doctor_ok: bool,
    unpushed: int,
    check_result,
    root: HarnessPath,
) -> str:
    if unpushed == 0:
        return "nothing_to_push"

    if clean and health_ok and check_ok and doctor_ok and not idle:
        return "active_task"

    if clean and idle and check_ok and doctor_ok:
        return "post_finish_closure"

    if (
        clean
        and not health_ok
        and not check_ok
        and _only_missing_active_task(check_result)
        and doctor_ok
        and _latest_unpushed_is_closure(root)
    ):
        return "post_finish_closure"

    return "not_ready"


def _only_missing_active_task(check_result) -> bool:
    if not check_result.violations:
        return False
    return all(
        "No active task contract found" in v.text
        or "Session active task does not match current active task" in v.text
        for v in check_result.violations
    )


def _latest_unpushed_is_closure(root: HarnessPath) -> bool:
    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        paths = result.stdout.strip().splitlines()
        return any(p.startswith("tasks/done/") for p in paths)
    except subprocess.CalledProcessError:
        return False


def _count_unpushed_commits(root: HarnessPath) -> int:
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "@{u}..HEAD"],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=root.path,
                check=True,
                capture_output=True,
                text=True,
            )
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return 0
