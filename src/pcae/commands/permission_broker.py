"""CLI runner for pcae permission-broker evaluate (Phase 88R prototype)."""
from __future__ import annotations

import argparse
import json

from pcae.core.paths import HarnessPath
from pcae.core.permission_broker import build_permission_broker


def run_permission_broker_evaluate(args: argparse.Namespace) -> int:
    requested_files: list[str] = list(getattr(args, "requested_file", None) or [])
    data = build_permission_broker(
        repo_root=HarnessPath.cwd().path,
        requested_action=args.requested_action,
        requested_files=requested_files,
        requested_command=getattr(args, "requested_command", None),
        source_backend=getattr(args, "source_backend", None),
        commit_message=getattr(args, "commit_message", None),
        push_target=getattr(args, "push_target", None),
        health_passed=_tri(getattr(args, "health_passed", None)),
        check_passed=_tri(getattr(args, "check_passed", None)),
        doctor_passed=_tri(getattr(args, "doctor_passed", None)),
        push_check_passed=_tri(getattr(args, "push_check_passed", None)),
        tests_present=bool(getattr(args, "tests_present", False)),
        tests_passed=_tri(getattr(args, "tests_passed", None)),
        human_review_present=bool(getattr(args, "human_review_present", False)),
        human_approval_present=bool(getattr(args, "human_approval_present", False)),
        accepted_risk_present=bool(getattr(args, "accepted_risk_present", False)),
    )

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        broker = data["broker"]
        decision = broker["decision"]
        action = broker["requested_action"]
        hard = broker["hard_block_present"]
        active = broker["active_task_detected"]
        print("Permission broker evaluate (prototype)")
        print(f"  Action:      {action}")
        if broker["requested_command"]:
            print(f"  Command:     {broker['requested_command']!r}")
        print(f"  Decision:    {decision}")
        print(f"  Hard block:  {hard}")
        print(f"  Active task: {active}")
        if broker["missing_evidence"]:
            print(f"  Missing:     {', '.join(broker['missing_evidence'])}")
        if broker["reason_codes"]:
            print(f"  Reasons:     {', '.join(broker['reason_codes'])}")
        print()
        print("  [broker_does_not_grant_execution_authorization]")

    return 0


def _tri(value: object) -> bool | None:
    """Convert argparse tri-state (None / True) to bool | None."""
    if value is True:
        return True
    if value is False:
        return False
    return None
