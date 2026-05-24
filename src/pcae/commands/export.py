from __future__ import annotations

import argparse

from pcae.core.export import write_governance_export_bundle
from pcae.core.paths import HarnessPath


def run_export_bundle(args: argparse.Namespace) -> int:
    bundle = write_governance_export_bundle(HarnessPath.cwd())
    print(f"Wrote governance bundle: {bundle.relative_path.as_posix()}")
    return 0
