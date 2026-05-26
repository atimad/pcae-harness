from __future__ import annotations

from dataclasses import dataclass

from pcae.core.paths import HarnessPath
from pcae.core.policy import (
    DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS,
    load_policy,
)

DAEMON_DRY_RUN_STEPS = (
    "pcae health",
    "pcae check",
    "pcae fleet drift",
    "pcae analytics risk",
    "pcae pipeline run --dry-run",
)


@dataclass(frozen=True)
class DaemonDryRunStep:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class DaemonDryRunResult:
    mode: str
    status: str
    cycle_count: int
    steps: tuple[DaemonDryRunStep, ...]


@dataclass(frozen=True)
class DaemonStatus:
    supported: bool
    running: bool
    mode: str
    watch_supported: bool
    dry_run_supported: bool
    default_interval_seconds: int
    planned_checks: tuple[str, ...]


@dataclass(frozen=True)
class DaemonWatchPlan:
    mode: str
    interval_seconds: int
    planned_checks: tuple[str, ...]
    would_repeat_continuously: bool


def run_daemon_dry_run_cycle() -> DaemonDryRunResult:
    return DaemonDryRunResult(
        mode="dry-run",
        status="planned",
        cycle_count=1,
        steps=tuple(
            DaemonDryRunStep(
                name=step,
                status="planned",
                message="would run during daemon monitoring cycle",
            )
            for step in DAEMON_DRY_RUN_STEPS
        ),
    )


def build_daemon_watch_plan(
    root: HarnessPath,
    interval_seconds: int | None = None,
) -> DaemonWatchPlan:
    effective_interval = (
        interval_seconds
        if interval_seconds is not None
        else read_daemon_watch_interval_seconds(root)
    )
    if effective_interval <= 0:
        raise ValueError("Interval seconds must be a positive integer.")

    return DaemonWatchPlan(
        mode="dry-run",
        interval_seconds=effective_interval,
        planned_checks=DAEMON_DRY_RUN_STEPS,
        would_repeat_continuously=True,
    )


def daemon_status(root: HarnessPath) -> DaemonStatus:
    return DaemonStatus(
        supported=True,
        running=False,
        mode="dry-run-only",
        watch_supported=False,
        dry_run_supported=True,
        default_interval_seconds=read_daemon_watch_interval_seconds(root),
        planned_checks=DAEMON_DRY_RUN_STEPS,
    )


def read_daemon_watch_interval_seconds(root: HarnessPath) -> int:
    policy = load_policy(root)
    if not policy.valid:
        raise ValueError(policy.error or "Invalid policy.")
    return policy.daemon_watch_interval_seconds
