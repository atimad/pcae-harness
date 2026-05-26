from __future__ import annotations

import argparse
import json

from pcae.core.ci import (
    CiDrift,
    CiRepairPlan,
    CiStatus,
    GITHUB_WORKFLOW_RELATIVE_PATH,
    apply_github_actions_repair,
    detect_github_actions_drift,
    generate_github_actions_workflow,
    inspect_github_actions_workflow,
    plan_github_actions_repair,
    render_github_actions_workflow,
)
from pcae.core.paths import HarnessPath


def run_ci_generate_github(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()

    if args.dry_run:
        print(f"Would write {GITHUB_WORKFLOW_RELATIVE_PATH.as_posix()}:")
        print(render_github_actions_workflow(), end="")
        return 0

    try:
        result = generate_github_actions_workflow(root, force=args.force)
    except FileExistsError as error:
        print(str(error))
        return 1

    if result.overwritten:
        print(f"Overwritten: {result.relative_path.as_posix()}")
    elif result.created:
        print(f"Created: {result.relative_path.as_posix()}")
    else:
        print(f"Already present: {result.relative_path.as_posix()}")
    return 0


def run_ci_status(args: argparse.Namespace) -> int:
    status = inspect_github_actions_workflow(HarnessPath.cwd())
    if args.json:
        print(json.dumps(ci_status_json_data(status), indent=2, sort_keys=True))
    else:
        print_ci_status(status)
    return 0


def run_ci_drift(args: argparse.Namespace) -> int:
    drift = detect_github_actions_drift(HarnessPath.cwd())
    if args.json:
        print(json.dumps(ci_drift_json_data(drift), indent=2, sort_keys=True))
    else:
        print_ci_drift(drift)
    return 0


def run_ci_repair(args: argparse.Namespace) -> int:
    if args.dry_run and args.force:
        print("Use either --dry-run or --force, not both.")
        return 1
    if not args.dry_run and not args.force:
        print("CI repair requires --dry-run or --force.")
        return 1

    plan = (
        plan_github_actions_repair(HarnessPath.cwd())
        if args.dry_run
        else apply_github_actions_repair(HarnessPath.cwd())
    )
    if args.json:
        print(json.dumps(ci_repair_json_data(plan), indent=2, sort_keys=True))
    else:
        if args.dry_run:
            print_ci_repair_plan(plan)
        else:
            print_ci_repair_result(plan)
    return 0


def print_ci_status(status: CiStatus) -> None:
    print("PCAE CI status")
    print(f"Workflow exists: {format_bool(status.workflow_exists)}")
    print(f"Workflow path: {status.workflow_path.as_posix()}")
    print(f"Health step: {format_bool(status.has_health_step)}")
    print(f"Check step: {format_bool(status.has_check_step)}")
    print(f"Risk step: {format_bool(status.has_risk_step)}")
    print(f"Overall status: {status.overall_status}")


def print_ci_drift(drift: CiDrift) -> None:
    print("PCAE CI drift")
    print(f"Drift detected: {format_bool(drift.drift_detected)}")
    print(f"Overall status: {drift.overall_status}")
    if drift.drift_findings:
        print("Drift findings:")
        for finding in drift.drift_findings:
            print(f"  - {finding}")
    else:
        print("No CI governance drift detected.")


def print_ci_repair_plan(plan: CiRepairPlan) -> None:
    print("PCAE CI repair dry run")
    print(f"Workflow path: {plan.workflow_path.as_posix()}")
    print(f"Repair needed: {format_bool(plan.repair_needed)}")
    print(f"Action: {plan.action}")
    print(f"Reason: {plan.reason}")


def print_ci_repair_result(plan: CiRepairPlan) -> None:
    print("PCAE CI repair")
    print(f"Workflow path: {plan.workflow_path.as_posix()}")
    if not plan.repair_needed:
        print("No repair needed.")
        return
    if plan.action == "create":
        print("Created workflow.")
        return
    if plan.action == "overwrite":
        print("Overwritten workflow.")
        print(f"Reason: {plan.reason}")
        return
    print(f"Action: {plan.action}")


def ci_status_json_data(status: CiStatus) -> dict[str, object]:
    return {
        "has_check_step": status.has_check_step,
        "has_health_step": status.has_health_step,
        "has_risk_step": status.has_risk_step,
        "overall_status": status.overall_status,
        "workflow_exists": status.workflow_exists,
        "workflow_path": status.workflow_path.as_posix(),
    }


def ci_drift_json_data(drift: CiDrift) -> dict[str, object]:
    return {
        "drift_detected": drift.drift_detected,
        "drift_findings": list(drift.drift_findings),
        "overall_status": drift.overall_status,
    }


def ci_repair_json_data(plan: CiRepairPlan) -> dict[str, object]:
    return {
        "action": plan.action,
        "reason": plan.reason,
        "repair_needed": plan.repair_needed,
        "workflow_path": plan.workflow_path.as_posix(),
    }


def format_bool(value: bool) -> str:
    return "true" if value else "false"
