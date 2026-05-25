from __future__ import annotations

import argparse
from pathlib import Path

from pcae.core.repo import RepoTrial, build_repo_trial


def run_repo_trial(args: argparse.Namespace) -> int:
    if not args.dry_run:
        print("Repo trial only supports --dry-run.")
        return 1

    try:
        trial = build_repo_trial(Path(args.path))
    except ValueError as error:
        print(error)
        return 1

    print_repo_trial(trial)
    return 0


def print_repo_trial(trial: RepoTrial) -> None:
    print("PCAE repo trial")
    print(f"Target repo: {trial.target_path}")
    print(
        "PCAE files: "
        f"{trial.pcae_files_present} present, {trial.pcae_files_missing} missing"
    )
    print(f"Policy exists: {yes_no(trial.policy_exists)}")
    print(f"Active tasks exist: {yes_no(trial.active_tasks_exist)}")
    print(f"Hooks exist: {yes_no(trial.hooks_exist)}")
    print("pcae init would create:")
    print_plan_paths(
        path
        for path in trial.init_plans
        if path.would_create
    )
    print("pcae init would skip:")
    print_plan_paths(
        path
        for path in trial.init_plans
        if not path.would_create
    )


def print_plan_paths(plans) -> None:
    paths = tuple(plans)
    if not paths:
        print("  none")
        return
    for plan in paths:
        print(f"  {plan.relative_path.as_posix()}")


def yes_no(value: bool) -> str:
    return "yes" if value else "no"
