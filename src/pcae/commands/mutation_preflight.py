from __future__ import annotations

import argparse
import json

from pcae.core.mutation_preflight import build_mutation_preflight
from pcae.core.paths import HarnessPath


def run_mutation_preflight(args: argparse.Namespace) -> int:
    requested_action = getattr(args, "requested_action", None) or "unknown"
    requested_files = getattr(args, "requested_file", None) or []
    captured_output_present = getattr(args, "captured_output_present", False) or False
    captured_output_hash = getattr(args, "captured_output_hash", None)
    diff_present = getattr(args, "diff_present", False) or False
    diff_hash = getattr(args, "diff_hash", None)
    adoption_review_present = getattr(args, "adoption_review_present", False) or False
    adoption_approval_present = getattr(args, "adoption_approval_present", False) or False
    source_backend = getattr(args, "source_backend", None)
    data = build_mutation_preflight(
        HarnessPath.cwd().path,
        requested_action=requested_action,
        requested_files=requested_files,
        captured_output_present=captured_output_present,
        captured_output_hash=captured_output_hash,
        diff_present=diff_present,
        diff_hash=diff_hash,
        adoption_review_present=adoption_review_present,
        adoption_approval_present=adoption_approval_present,
        source_backend=source_backend,
    )
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        pf = data["preflight"]
        print("Mutation/adoption preflight evaluation")
        print(f"  Decision:           {pf['decision']}")
        print(f"  Action:             {pf['requested_action']}")
        print(f"  Files:              {pf['requested_files']}")
        print(f"  Reason codes:       {pf['reason_codes']}")
        print(f"  Task contract:      {'detected' if pf['task_contract_detected'] else 'not detected'}")
        print(f"  Scope required:     {pf['scope_preflight_required']}")
        print(f"  Scope decision:     {pf['scope_preflight_decision']}")
        print(f"  Capture present:    {pf['captured_output_present']}")
        print(f"  Review present:     {pf['adoption_review_present']}")
        print(f"  Approval present:   {pf['adoption_approval_present']}")
        print(f"  Human review:       {pf['human_review_required']}")
        print(f"  Auth granted:       {pf['authorization_granted']}")
        print(f"  Exec authorized:    {pf['execution_authorized']}")
        print(f"  Mutation performed: {pf['mutation_performed']}")
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0
