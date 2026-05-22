from __future__ import annotations

import argparse

from pcae.core.hooks import install_hooks
from pcae.core.paths import HarnessPath


def run_hooks_install(args: argparse.Namespace) -> int:
    result = install_hooks(HarnessPath.cwd())
    print(result.message)
    return 0 if result.installed else 1
