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
