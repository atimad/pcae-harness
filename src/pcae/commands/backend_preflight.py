from __future__ import annotations

import argparse
import json

from pcae.core.backend_preflight import build_backend_preflight
from pcae.core.paths import HarnessPath


def run_backend_preflight(args: argparse.Namespace) -> int:
    requested_backend = getattr(args, "requested_backend", None) or "unknown_backend"
    requested_action = getattr(args, "requested_action", None) or "unknown"
    requested_files = getattr(args, "requested_file", None) or []
    prompt_present = getattr(args, "prompt_present", False) or False
    prompt_hash = getattr(args, "prompt_hash", None)
    data = build_backend_preflight(
        HarnessPath.cwd().path,
        requested_backend=requested_backend,
        requested_action=requested_action,
        requested_files=requested_files,
        prompt_present=prompt_present,
        prompt_hash=prompt_hash,
    )
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        pf = data["preflight"]
        print("Backend invocation preflight evaluation")
        print(f"  Decision:          {pf['decision']}")
        print(f"  Backend:           {pf['requested_backend']}")
        print(f"  Backend known:     {pf['backend_known']}")
        print(f"  Action:            {pf['requested_action']}")
        print(f"  Prompt present:    {pf['prompt_present']}")
        print(f"  Prompt required:   {pf['prompt_required']}")
        print(f"  Reason codes:      {pf['reason_codes']}")
        print(f"  Task contract:     {'detected' if pf['task_contract_detected'] else 'not detected'}")
        print(f"  Human review:      {pf['human_review_required']}")
        print(f"  More evidence:     {pf['more_evidence_required']}")
        print(f"  Auth granted:      {pf['authorization_granted']}")
        print(f"  Exec authorized:   {pf['execution_authorized']}")
        print(f"  Backend invoked:   {pf['backend_invocation_performed']}")
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0
