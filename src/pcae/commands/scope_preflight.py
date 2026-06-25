from __future__ import annotations

import argparse
import json

from pcae.core.scope_preflight import build_scope_preflight
from pcae.core.paths import HarnessPath


def run_scope_preflight(args: argparse.Namespace) -> int:
    requested_action = getattr(args, "requested_action", None) or "unknown"
    requested_files = getattr(args, "requested_file", None) or []
    data = build_scope_preflight(
        HarnessPath.cwd().path,
        requested_action=requested_action,
        requested_files=requested_files,
    )
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        pf = data["preflight"]
        print("Scope gate preflight evaluation")
        print(f"  Decision:        {pf['decision']}")
        print(f"  Requested action: {pf['requested_action']}")
        print(f"  Requested files:  {pf['requested_files']}")
        print(f"  Reason codes:    {pf['reason_codes']}")
        print(f"  Task contract:   {'detected' if pf['task_contract_detected'] else 'not detected'}")
        print(f"  Allowed matched: {pf['matched_allowed_files']}")
        print(f"  Forbidden matched: {pf['matched_forbidden_files']}")
        print(f"  Unknown files:   {pf['unknown_files']}")
        print(f"  Human review:    {pf['human_review_required']}")
        print(f"  More evidence:   {pf['more_evidence_required']}")
        print(f"  Auth granted:    {pf['authorization_granted']}")
        print(f"  Exec authorized: {pf['execution_authorized']}")
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0
