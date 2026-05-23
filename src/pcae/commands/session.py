from __future__ import annotations

import argparse

from pcae.core.paths import HarnessPath
from pcae.core.session import write_session_snapshot


def run_session_write(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    snapshot = write_session_snapshot(root)

    print(f"Wrote session snapshot: {snapshot.relative_path.as_posix()}")
    return 0
