from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcae.core.repo import RepoTrial, apply_repo_onboarding, build_repo_trial
from pcae.core.writer import WriteResult


def run_repo_trial(args: argparse.Namespace) -> int:
    if not args.dry_run:
        print("Repo trial only supports --dry-run.")
        return 1

    try:
        trial = build_repo_trial(Path(args.path))
    except ValueError as error:
        print(error)
        return 1

    if args.json:
        print(json.dumps(repo_trial_json_data(trial), indent=2, sort_keys=True))
    else:
        print_repo_trial(trial)
    return 0


def run_repo_apply(args: argparse.Namespace) -> int:
    if not args.dry_run and not args.force:
        print("Real repo apply is not implemented yet. Use --dry-run or --force.")
        return 1

    try:
        if args.dry_run:
            trial = build_repo_trial(Path(args.path))
            print_repo_apply_plan(trial)
            return 0
        results = apply_repo_onboarding(Path(args.path))
    except ValueError as error:
        print(error)
        return 1

    print("PCAE repo apply completed.")
    print_write_results("Created:", (result for result in results if result.created))
    print_write_results(
        "Overwritten:",
        (result for result in results if result.overwritten),
    )
    print_write_results(
        "Skipped:",
        (
            result
            for result in results
            if not result.created and not result.overwritten
        ),
    )
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


def print_repo_apply_plan(trial: RepoTrial) -> None:
    print("PCAE repo apply dry run")
    print(f"Target repo: {trial.target_path}")
    print("Would create:")
    print_plan_paths(
        path
        for path in trial.init_plans
        if path.would_create
    )
    print("Would skip:")
    print_plan_paths(
        path
        for path in trial.init_plans
        if not path.would_create and not path.would_overwrite
    )
    print("Would overwrite:")
    print_plan_paths(
        path
        for path in trial.init_plans
        if path.would_overwrite
    )


def print_plan_paths(plans) -> None:
    paths = tuple(plans)
    if not paths:
        print("  none")
        return
    for plan in paths:
        print(f"  {plan.relative_path.as_posix()}")


def print_write_results(title: str, results) -> None:
    items: tuple[WriteResult, ...] = tuple(results)
    print(title)
    if not items:
        print("  none")
        return
    for result in items:
        print(f"  {result.relative_path.as_posix()}")


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def repo_trial_json_data(trial: RepoTrial) -> dict[str, object]:
    return {
        "active_tasks_exist": trial.active_tasks_exist,
        "hooks_exist": trial.hooks_exist,
        "init_would_create": [
            plan.relative_path.as_posix()
            for plan in trial.init_plans
            if plan.would_create
        ],
        "init_would_skip": [
            plan.relative_path.as_posix()
            for plan in trial.init_plans
            if not plan.would_create
        ],
        "is_git_repo": trial.is_git_repo,
        "pcae_files_missing": trial.pcae_files_missing,
        "pcae_files_present": trial.pcae_files_present,
        "policy_exists": trial.policy_exists,
        "target_repo": trial.target_path.as_posix(),
    }
