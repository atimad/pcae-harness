from __future__ import annotations

import argparse
import json

from pcae.core.commit_push_preflight import build_commit_preflight, build_push_preflight
from pcae.core.paths import HarnessPath


def run_commit_preflight(args: argparse.Namespace) -> int:
    data = build_commit_preflight(
        HarnessPath.cwd().path,
        commit_message=getattr(args, "commit_message", None),
        diff_present=getattr(args, "diff_present", False) or False,
        tests_present=getattr(args, "tests_present", False) or False,
        tests_passed=getattr(args, "tests_passed", False) or False,
        pcae_check_passed=getattr(args, "pcae_check_passed", False) or False,
        pcae_health_passed=getattr(args, "pcae_health_passed", False) or False,
        doctor_passed=getattr(args, "doctor_passed", False) or False,
        requested_files=getattr(args, "requested_file", None) or [],
    )
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        pf = data["preflight"]
        print("Commit preflight evaluation")
        print(f"  Decision:       {pf['decision']}")
        print(f"  Action:         {pf['requested_action']}")
        print(f"  Message:        {'present' if pf['commit_message_present'] else 'missing'}")
        print(f"  Diff:           {'present' if pf['diff_present'] else 'missing'}")
        print(f"  Tests:          {'passed' if pf['tests_passed'] else ('present' if pf['tests_present'] else 'missing')}")
        print(f"  Check:          {'passed' if pf['pcae_check_passed'] else 'not passed'}")
        print(f"  Health:         {'passed' if pf['pcae_health_passed'] else 'not passed'}")
        print(f"  Doctor:         {'passed' if pf['doctor_passed'] else 'not passed'}")
        print(f"  Branch:         {pf['branch_name']}")
        print(f"  Human review:   {pf['human_review_required']}")
        print(f"  Auth granted:   {pf['authorization_granted']}")
        print(f"  Commit done:    {pf['commit_performed']}")
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0


def run_push_preflight(args: argparse.Namespace) -> int:
    data = build_push_preflight(
        HarnessPath.cwd().path,
        push_target=getattr(args, "push_target", None),
        push_check_passed=getattr(args, "push_check_passed", False) or False,
        pcae_check_passed=getattr(args, "pcae_check_passed", False) or False,
        pcae_health_passed=getattr(args, "pcae_health_passed", False) or False,
        doctor_passed=getattr(args, "doctor_passed", False) or False,
        tests_present=getattr(args, "tests_present", False) or False,
        tests_passed=getattr(args, "tests_passed", False) or False,
        raw_git_push_requested=getattr(args, "raw_git_push_requested", False) or False,
        force_push_requested=getattr(args, "force_push_requested", False) or False,
    )
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        pf = data["preflight"]
        print("Push preflight evaluation")
        print(f"  Decision:       {pf['decision']}")
        print(f"  Action:         {pf['requested_action']}")
        print(f"  Push target:    {pf['push_target']}")
        print(f"  Push check:     {'passed' if pf['push_check_passed'] else 'not passed'}")
        print(f"  Tests:          {'passed' if pf['tests_passed'] else ('present' if pf['tests_present'] else 'missing')}")
        print(f"  Branch:         {pf['branch_name']}")
        print(f"  Ahead:          {pf['ahead_count']}")
        print(f"  Behind:         {pf['behind_count']}")
        print(f"  Raw git push:   {pf['raw_git_push_requested']}")
        print(f"  Force push:     {pf['force_push_requested']}")
        print(f"  Human review:   {pf['human_review_required']}")
        print(f"  Auth granted:   {pf['authorization_granted']}")
        print(f"  Push done:      {pf['push_performed']}")
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0
