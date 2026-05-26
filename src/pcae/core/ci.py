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
