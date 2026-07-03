from __future__ import annotations

import argparse
import json

from pcae.core.hooks import diagnose_hooks, install_hooks
from pcae.core.paths import HarnessPath


def run_hooks_install(args: argparse.Namespace) -> int:
    result = install_hooks(HarnessPath.cwd())
    print(result.message)
    return 0 if result.installed else 1


def run_hooks_status(args: argparse.Namespace) -> int:
    status = diagnose_hooks(HarnessPath.cwd())

    if getattr(args, "json", False):
        print(json.dumps({
            "status": status.status,
            "git_repo": status.git_repo,
            "hooks_path_configured": status.hooks_path_configured,
            "hooks_path_expected": status.hooks_path_expected,
            "missing_hook_files": list(status.missing_hook_files),
            "non_executable_hook_files": list(status.non_executable_hook_files),
            "healthy": status.healthy,
            "recommended_remediation": list(status.recommended_remediation),
        }, indent=2, sort_keys=True))
    else:
        print("PCAE Git hook status")
        print(f"  Status: {status.status}")
        print(f"  Git repository: {status.git_repo}")
        print(f"  core.hooksPath configured: {status.hooks_path_configured!r}")
        print(f"  core.hooksPath expected: {status.hooks_path_expected!r}")
        if status.missing_hook_files:
            print(f"  Missing hook files: {', '.join(status.missing_hook_files)}")
        if status.non_executable_hook_files:
            print(f"  Non-executable hook files: {', '.join(status.non_executable_hook_files)}")
        print(f"  Healthy: {status.healthy}")
        if status.recommended_remediation:
            print("  Recommended remediation:")
            for step in status.recommended_remediation:
                print(f"    {step}")

    return 0 if status.healthy else 1
