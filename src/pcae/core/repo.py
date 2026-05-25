from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.inspect import inspect_harness
from pcae.core.paths import HarnessPath
from pcae.core.templates import INIT_TEMPLATES
from pcae.core.writer import WritePlan, plan_missing_files


@dataclass(frozen=True)
class RepoTrial:
    target_path: Path
    is_git_repo: bool
    pcae_files_present: int
    pcae_files_missing: int
    init_plans: tuple[WritePlan, ...]
    policy_exists: bool
    active_tasks_exist: bool
    hooks_exist: bool


def build_repo_trial(target_path: Path) -> RepoTrial:
    if not target_path.exists():
        raise ValueError(f"Target repo path does not exist: {target_path}")
    if not target_path.is_dir():
        raise ValueError(f"Target repo path is not a directory: {target_path}")
    if not target_path.joinpath(".git").exists():
        raise ValueError(f"Target path is not a Git repo: {target_path}")

    root = HarnessPath(target_path)
    inspection = inspect_harness(root)
    active_tasks = target_path / "tasks" / "active"
    return RepoTrial(
        target_path=target_path,
        is_git_repo=True,
        pcae_files_present=len(inspection.present_paths),
        pcae_files_missing=len(inspection.missing_paths),
        init_plans=tuple(plan_missing_files(root, INIT_TEMPLATES)),
        policy_exists=inspection.policy.present,
        active_tasks_exist=active_tasks.is_dir()
        and any(active_tasks.glob("*.md")),
        hooks_exist=target_path.joinpath(".githooks", "pre-commit").is_file(),
    )
