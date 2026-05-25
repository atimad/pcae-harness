from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcae.core.fleet import add_fleet_repo, build_fleet_health, read_fleet_repos
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


def run_fleet_health(args: argparse.Namespace) -> int:
    data = build_fleet_health(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_fleet_health(data)
    return 0 if data["overall_status"] == "healthy" else 1


def print_fleet_health(data: dict) -> None:
    print("Fleet health")
    print(f"Overall status: {data['overall_status']}")
    print(f"Repos: {data['repo_count']}")
    print(f"Healthy: {data['healthy_count']}")
    print(f"Unhealthy: {data['unhealthy_count']}")
    for repo in data["repos"]:
        print(f"Repo: {repo['path']}")
        print(f"  Status: {repo['status']}")
        active_task = repo["active_task"]
        if isinstance(active_task, dict):
            print(f"  Active task: {active_task.get('id', 'unknown')}")
            print(f"  Title: {active_task.get('title', 'Untitled task')}")
        else:
            print("  Active task: none")
        print(f"  Session continuity: {repo['session_continuity'] or 'unknown'}")
        print(f"  Latest enforcement mode: {repo['latest_enforcement_mode'] or 'unknown'}")
        warnings = repo["latest_dependency_warnings"]
        if warnings is None:
            print("  Latest dependency warnings: unknown")
        else:
            print(f"  Latest dependency warnings: {warnings}")
        if repo["details"] != "ok":
            print(f"  Details: {repo['details']}")
