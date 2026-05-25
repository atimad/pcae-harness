from __future__ import annotations

import argparse
from pathlib import Path

from pcae.core.fleet import add_fleet_repo, read_fleet_repos
from pcae.core.paths import HarnessPath


def run_fleet_add(args: argparse.Namespace) -> int:
    try:
        repo_path, added = add_fleet_repo(HarnessPath.cwd(), Path(args.path))
    except ValueError as error:
        print(error)
        return 1

    if added:
        print(f"Added fleet repo: {repo_path}")
    else:
        print(f"Fleet repo already registered: {repo_path}")
    return 0


def run_fleet_list(args: argparse.Namespace) -> int:
    repos = read_fleet_repos(HarnessPath.cwd())
    print("Fleet repos:")
    if not repos:
        print("  none")
        return 0
    for repo in repos:
        print(f"  {repo}")
    return 0
