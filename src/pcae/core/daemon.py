from __future__ import annotations

from dataclasses import dataclass


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
    planned_checks: tuple[str, ...]


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


def daemon_status() -> DaemonStatus:
    return DaemonStatus(
        supported=True,
        running=False,
        mode="dry-run-only",
        watch_supported=False,
        dry_run_supported=True,
        planned_checks=DAEMON_DRY_RUN_STEPS,
    )
