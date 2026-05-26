from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.paths import HarnessPath


GITHUB_WORKFLOW_RELATIVE_PATH = Path(".github") / "workflows" / "pcae-governance.yml"


@dataclass(frozen=True)
class CiGenerateResult:
    relative_path: Path
    created: bool
    overwritten: bool


@dataclass(frozen=True)
class CiStatus:
    workflow_exists: bool
    workflow_path: Path
    has_health_step: bool
    has_check_step: bool
    has_risk_step: bool
    overall_status: str


@dataclass(frozen=True)
class CiDrift:
    drift_detected: bool
    drift_findings: tuple[str, ...]
    overall_status: str


def render_github_actions_workflow() -> str:
    return """name: PCAE Governance

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  governance:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Install project
        run: python -m pip install -e .

      - name: PCAE health
        run: pcae health --json

      - name: PCAE check
        run: pcae check --json

      - name: PCAE risk
        run: pcae analytics risk --json
"""


def generate_github_actions_workflow(
    root: HarnessPath,
    force: bool = False,
) -> CiGenerateResult:
    target = root.join(GITHUB_WORKFLOW_RELATIVE_PATH)
    if target.exists() and not force:
        raise FileExistsError(
            f"{GITHUB_WORKFLOW_RELATIVE_PATH.as_posix()} already exists. Use --force to overwrite."
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    existed = target.exists()
    with target.open("w", encoding="utf-8", newline="\n") as file:
        file.write(render_github_actions_workflow())

    return CiGenerateResult(
        relative_path=GITHUB_WORKFLOW_RELATIVE_PATH,
        created=not existed,
        overwritten=existed,
    )


def inspect_github_actions_workflow(root: HarnessPath) -> CiStatus:
    target = root.join(GITHUB_WORKFLOW_RELATIVE_PATH)
    if not target.is_file():
        return CiStatus(
            workflow_exists=False,
            workflow_path=GITHUB_WORKFLOW_RELATIVE_PATH,
            has_health_step=False,
            has_check_step=False,
            has_risk_step=False,
            overall_status="missing",
        )

    content = target.read_text(encoding="utf-8")
    has_health_step = "pcae health --json" in content
    has_check_step = "pcae check --json" in content
    has_risk_step = "pcae analytics risk --json" in content
    configured = has_health_step and has_check_step and has_risk_step

    return CiStatus(
        workflow_exists=True,
        workflow_path=GITHUB_WORKFLOW_RELATIVE_PATH,
        has_health_step=has_health_step,
        has_check_step=has_check_step,
        has_risk_step=has_risk_step,
        overall_status="configured" if configured else "incomplete",
    )


def detect_github_actions_drift(root: HarnessPath) -> CiDrift:
    status = inspect_github_actions_workflow(root)
    if not status.workflow_exists:
        return CiDrift(
            drift_detected=True,
            drift_findings=("workflow file missing",),
            overall_status="missing",
        )

    findings: list[str] = []
    if not status.has_health_step:
        findings.append("missing health step")
    if not status.has_check_step:
        findings.append("missing check step")
    if not status.has_risk_step:
        findings.append("missing analytics risk step")

    return CiDrift(
        drift_detected=bool(findings),
        drift_findings=tuple(findings),
        overall_status="drift" if findings else "no_drift",
    )
