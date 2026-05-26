from __future__ import annotations

import argparse
import json

from pcae.core.orchestration import build_orchestration_data
from pcae.core.paths import HarnessPath


def run_orchestration_policy(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        data = build_orchestration_data(root)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Orchestration policy")
        print(f"Default agent: {data['default_agent']}")
        print(f"Documentation agent: {data['documentation_agent']}")
        print(f"Runtime agent: {data['runtime_agent']}")
        print(f"Validation agent: {data['validation_agent']}")
    return 0
