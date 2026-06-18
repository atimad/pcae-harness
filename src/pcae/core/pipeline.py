from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess

from pcae.core.analytics import calculate_governance_risk, calculate_governance_trends
from pcae.core.architecture import (
    ARCHITECTURE_HISTORY_RELATIVE_PATH,
    calculate_architecture_drift_metrics,
    read_architecture_history_summary,
    write_architecture_history_snapshot,
)
from pcae.core.check import run_checks
from pcae.core.export import write_governance_export_bundle
from pcae.core.fleet import write_fleet_export
from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.session import SESSION_RELATIVE_PATH, write_session_snapshot


DEFAULT_PIPELINE_NAME = "default"
DEFAULT_PIPELINE_DESCRIPTION = "Run the standard PCAE governance workflow."
DEFAULT_PIPELINE_STEPS = (
    "pcae health",
    "pcae check",
    "pcae analytics risk",
    "pcae analytics trends",
    "pcae architecture metrics",
    "pcae export bundle",
    "pcae fleet export",
    "pcae session end",
)


@dataclass(frozen=True)
class PipelineDefinition:
    name: str
    description: str
    steps: tuple[str, ...]
    supports_dry_run: bool
    supports_json: bool


@dataclass(frozen=True)
class PipelineStepResult:
    name: str
    status: str
    message: str
    artifacts: tuple[str, ...] = ()


@dataclass(frozen=True)
class PipelineResult:
    name: str
    status: str
    steps: tuple[PipelineStepResult, ...]
    generated_timestamp: str

    @property
    def stopped_at(self) -> str | None:
        for step in self.steps:
            if step.status == "failed":
                return step.name
        return None


@dataclass(frozen=True)
class TrackedFileSnapshot:
    relative_path: Path
    existed: bool
    content: str | None


def available_pipelines() -> tuple[PipelineDefinition, ...]:
    return (
        PipelineDefinition(
            name=DEFAULT_PIPELINE_NAME,
            description=DEFAULT_PIPELINE_DESCRIPTION,
            steps=DEFAULT_PIPELINE_STEPS,
            supports_dry_run=True,
            supports_json=True,
        ),
    )


def run_default_pipeline(
    root: HarnessPath,
    generated_at: datetime | None = None,
    dry_run: bool = False,
) -> PipelineResult:
    timestamp = generated_at or datetime.now(timezone.utc)
    steps: list[PipelineStepResult] = []

    from pcae.core.health import is_healthy

    health = build_health_data(root)
    if not is_healthy(health):
        steps.append(
            PipelineStepResult(
                name="pcae health",
                status="failed",
                message="governance health is unhealthy",
            )
        )
        return build_pipeline_result("failed", steps, timestamp)
    steps.append(
        PipelineStepResult(
            name="pcae health",
            status="passed",
            message="healthy",
        )
    )

    check_result = run_checks(root)
    if not check_result.passed:
        steps.append(
            PipelineStepResult(
                name="pcae check",
                status="failed",
                message="governance check failed",
            )
        )
        return build_pipeline_result("failed", steps, timestamp)
    steps.append(
        PipelineStepResult(
            name="pcae check",
            status="passed",
            message="passed",
        )
    )

    if dry_run:
        steps.extend(planned_pipeline_steps())
        return build_pipeline_result("planned", steps, timestamp)

    risk = calculate_governance_risk(root)
    steps.append(
        PipelineStepResult(
            name="pcae analytics risk",
            status="passed",
            message=f"{risk.risk_level} risk ({risk.risk_score})",
        )
    )

    trends = calculate_governance_trends(root)
    steps.append(
        PipelineStepResult(
            name="pcae analytics trends",
            status="passed",
            message=f"{trends.total_snapshots} snapshots",
        )
    )

    architecture_summary = read_architecture_history_summary(root)
    metrics = calculate_architecture_drift_metrics(architecture_summary)
    steps.append(
        PipelineStepResult(
            name="pcae architecture metrics",
            status="passed",
            message=f"{metrics.total_snapshots} snapshots",
        )
    )

    governance_bundle = write_governance_export_bundle(root)
    governance_artifact = governance_bundle.relative_path.as_posix()
    steps.append(
        PipelineStepResult(
            name="pcae export bundle",
            status="passed",
            message=governance_artifact,
            artifacts=(governance_artifact,),
        )
    )

    fleet_bundle = write_fleet_export(root)
    fleet_artifact = fleet_bundle.relative_path.as_posix()
    steps.append(
        PipelineStepResult(
            name="pcae fleet export",
            status="passed",
            message=fleet_artifact,
            artifacts=(fleet_artifact,),
        )
    )

    operational_snapshots = capture_tracked_operational_snapshots(root)
    session_snapshot = write_session_snapshot(root)
    architecture_snapshot = write_architecture_history_snapshot(root, check_result)
    restore_tracked_operational_snapshots(root, operational_snapshots)
    session_artifact = session_snapshot.relative_path.as_posix()
    architecture_artifact = architecture_snapshot.relative_path.as_posix()
    steps.append(
        PipelineStepResult(
            name="pcae session end",
            status="passed",
            message=(
                f"{session_artifact}, "
                f"{architecture_artifact}"
            ),
            artifacts=(session_artifact, architecture_artifact),
        )
    )

    return build_pipeline_result("passed", steps, timestamp)


def planned_pipeline_steps() -> tuple[PipelineStepResult, ...]:
    return (
        PipelineStepResult(
            name="pcae analytics risk",
            status="planned",
            message="would compute governance risk",
        ),
        PipelineStepResult(
            name="pcae analytics trends",
            status="planned",
            message="would summarize governance trends",
        ),
        PipelineStepResult(
            name="pcae architecture metrics",
            status="planned",
            message="would summarize architecture metrics",
        ),
        PipelineStepResult(
            name="pcae export bundle",
            status="planned",
            message="would write governance export bundle",
        ),
        PipelineStepResult(
            name="pcae fleet export",
            status="planned",
            message="would write fleet governance export bundle",
        ),
        PipelineStepResult(
            name="pcae session end",
            status="planned",
            message="would write session snapshot and architecture history",
        ),
    )


def build_pipeline_result(
    status: str,
    steps: list[PipelineStepResult],
    timestamp: datetime,
) -> PipelineResult:
    return PipelineResult(
        name=DEFAULT_PIPELINE_NAME,
        status=status,
        steps=tuple(steps),
        generated_timestamp=timestamp.isoformat(),
    )


def capture_tracked_operational_snapshots(
    root: HarnessPath,
) -> tuple[TrackedFileSnapshot, ...]:
    snapshots: list[TrackedFileSnapshot] = []
    for relative_path in operational_state_paths():
        if not git_tracks_path(root, relative_path):
            continue
        target = root.join(relative_path)
        snapshots.append(
            TrackedFileSnapshot(
                relative_path=relative_path,
                existed=target.exists(),
                content=target.read_text(encoding="utf-8")
                if target.exists()
                else None,
            )
        )
    return tuple(snapshots)


def restore_tracked_operational_snapshots(
    root: HarnessPath,
    snapshots: tuple[TrackedFileSnapshot, ...],
) -> None:
    for snapshot in snapshots:
        target = root.join(snapshot.relative_path)
        if not snapshot.existed:
            if target.exists():
                target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as file:
            file.write(snapshot.content or "")


def operational_state_paths() -> tuple[Path, ...]:
    return (
        SESSION_RELATIVE_PATH,
        ARCHITECTURE_HISTORY_RELATIVE_PATH,
    )


def git_tracks_path(root: HarnessPath, relative_path: Path) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path.as_posix()],
        cwd=root.path,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0
