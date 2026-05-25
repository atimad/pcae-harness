from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcae.core.fleet import (
    add_fleet_repo,
    apply_fleet_governance,
    build_fleet_apply_plan,
    build_fleet_drift,
    build_fleet_health,
    build_fleet_inspection,
    read_fleet_repos,
    remove_fleet_repo,
    write_fleet_export,
)
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


def run_fleet_remove(args: argparse.Namespace) -> int:
    try:
        repo_path, removed = remove_fleet_repo(
            HarnessPath.cwd(),
            Path(args.path),
            missing_only=args.missing_only,
        )
    except ValueError as error:
        print(error)
        return 1

    if removed:
        print(f"Removed fleet repo: {repo_path}")
    else:
        print(f"Fleet repo still exists; not removed: {repo_path}")
    return 0


def run_fleet_health(args: argparse.Namespace) -> int:
    data = build_fleet_health(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_fleet_health(data)
    return 0 if data["overall_status"] == "healthy" else 1


def run_fleet_inspect(args: argparse.Namespace) -> int:
    data = build_fleet_inspection(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_fleet_inspection(data)
    return 0 if data["overall_status"] == "ready" else 1


def run_fleet_drift(args: argparse.Namespace) -> int:
    data = build_fleet_drift(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_fleet_drift(data)
    return 0 if not data["drift_detected"] else 1


def run_fleet_apply(args: argparse.Namespace) -> int:
    if not args.dry_run and not args.force:
        print("Fleet apply requires --dry-run or --force.")
        return 1

    if args.dry_run:
        data = build_fleet_apply_plan(HarnessPath.cwd())
        if args.json:
            print(
                json.dumps(
                    fleet_apply_json_data(data, dry_run=True),
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print_fleet_apply_plan(data)
        return 0 if data["overall_status"] == "ready" else 1

    data = apply_fleet_governance(HarnessPath.cwd())
    if args.json:
        print(
            json.dumps(
                fleet_apply_json_data(data, dry_run=False),
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_fleet_apply_results(data)
    return 0 if data["overall_status"] == "applied" else 1


def run_fleet_export(args: argparse.Namespace) -> int:
    export = write_fleet_export(HarnessPath.cwd())
    print(f"Wrote fleet governance bundle: {export.relative_path.as_posix()}")
    return 0


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


def print_fleet_inspection(data: dict) -> None:
    print("Fleet inspection")
    print(f"Overall status: {data['overall_status']}")
    print(f"Repos: {data['repo_count']}")
    print(f"Ready: {data['ready_count']}")
    print(f"Not ready: {data['not_ready_count']}")
    for repo in data["repos"]:
        print(f"Repo: {repo['path']}")
        print(f"  Status: {repo['status']}")
        if repo["pcae_files_present"] is None:
            print("  PCAE files: unknown")
        else:
            print(
                "  PCAE files: "
                f"{repo['pcae_files_present']} present, "
                f"{repo['pcae_files_missing']} missing"
            )
        print(f"  Policy exists: {yes_no(repo['policy_exists'])}")
        print(f"  Hooks exist: {yes_no(repo['hooks_exist'])}")
        print(f"  Active tasks exist: {yes_no(repo['active_tasks_exist'])}")
        if repo["details"] != "ok":
            print(f"  Details: {repo['details']}")


def print_fleet_drift(data: dict) -> None:
    print("Fleet drift")
    print(f"Overall status: {data['overall_status']}")
    print(f"Repos: {data['repo_count']}")
    if not data["drift_detected"]:
        print("No governance drift detected.")
        return

    print("Drift findings:")
    for finding in data["drift_findings"]:
        print(f"  {finding['type']}: {finding['path']}")
        if "value" in finding:
            print(f"    Value: {finding['value']}")
        print(f"    {finding['message']}")


def print_fleet_apply_plan(data: dict) -> None:
    print("Fleet apply dry run")
    print(f"Overall status: {data['overall_status']}")
    print(f"Repos: {data['repo_count']}")
    for repo in data["repos"]:
        print(f"Repo: {repo['path']}")
        print(f"  Status: {repo['status']}")
        if repo["status"] == "error":
            print(f"  Details: {repo['details']}")
            continue
        print_paths("  Would create:", repo["would_create"])
        print_paths("  Would overwrite:", repo["would_overwrite"])
        print_paths("  Would skip:", repo["would_skip"])


def print_fleet_apply_results(data: dict) -> None:
    print("Fleet apply")
    print(f"Overall status: {data['overall_status']}")
    print(f"Repos: {data['repo_count']}")
    for repo in data["repos"]:
        print(f"Repo: {repo['path']}")
        print(f"  Status: {repo['status']}")
        if repo["status"] == "error":
            print(f"  Details: {repo['details']}")
            continue
        print_paths("  Created:", repo["created"])
        print_paths("  Overwritten:", repo["overwritten"])
        print_paths("  Skipped:", repo["skipped"])


def print_paths(title: str, paths: list[str]) -> None:
    print(title)
    if not paths:
        print("    none")
        return
    for path in paths:
        print(f"    {path}")


def fleet_apply_json_data(data: dict, *, dry_run: bool) -> dict:
    return {
        "overall_status": data["overall_status"],
        "repo_count": data["repo_count"],
        "repos": [
            fleet_apply_repo_json_data(repo, dry_run=dry_run)
            for repo in data["repos"]
        ],
    }


def fleet_apply_repo_json_data(repo: dict, *, dry_run: bool) -> dict:
    if dry_run:
        created = repo["would_create"]
        overwritten = repo["would_overwrite"]
        skipped = repo["would_skip"]
    else:
        created = repo["created"]
        overwritten = repo["overwritten"]
        skipped = repo["skipped"]

    return {
        "created": created,
        "errors": [] if repo["status"] != "error" else [repo["details"]],
        "overwritten": overwritten,
        "path": repo["path"],
        "skipped": skipped,
        "status": repo["status"],
    }


def yes_no(value: bool) -> str:
    return "yes" if value else "no"
