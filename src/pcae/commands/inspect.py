from __future__ import annotations

import argparse

from pcae.core.inspect import inspect_harness
from pcae.core.paths import HarnessPath
from pcae.core.reporting import format_inspection, format_inspection_json


def run_inspect(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = inspect_harness(root)
    if args.json:
        print(format_inspection_json(result))
        return 0

    print(format_inspection(result))
    return 0
