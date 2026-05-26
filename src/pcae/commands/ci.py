from __future__ import annotations

import argparse
import json

from pcae.core.ci import (
    CiStatus,
    GITHUB_WORKFLOW_RELATIVE_PATH,
    generate_github_actions_workflow,
    inspect_github_actions_workflow,
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


def print_ci_status(status: CiStatus) -> None:
    print("PCAE CI status")
    print(f"Workflow exists: {format_bool(status.workflow_exists)}")
    print(f"Workflow path: {status.workflow_path.as_posix()}")
    print(f"Health step: {format_bool(status.has_health_step)}")
    print(f"Check step: {format_bool(status.has_check_step)}")
    print(f"Risk step: {format_bool(status.has_risk_step)}")
    print(f"Overall status: {status.overall_status}")


def ci_status_json_data(status: CiStatus) -> dict[str, object]:
    return {
        "has_check_step": status.has_check_step,
        "has_health_step": status.has_health_step,
        "has_risk_step": status.has_risk_step,
        "overall_status": status.overall_status,
        "workflow_exists": status.workflow_exists,
        "workflow_path": status.workflow_path.as_posix(),
    }


def format_bool(value: bool) -> str:
    return "true" if value else "false"
