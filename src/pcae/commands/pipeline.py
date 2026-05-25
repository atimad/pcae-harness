from __future__ import annotations

import argparse

from pcae.core.paths import HarnessPath
from pcae.core.pipeline import DEFAULT_PIPELINE_NAME, PipelineResult, run_default_pipeline


def run_pipeline(args: argparse.Namespace) -> int:
    name = args.name or DEFAULT_PIPELINE_NAME
    if name != DEFAULT_PIPELINE_NAME:
        print(f"Unknown pipeline: {name}")
        return 1

    result = run_default_pipeline(HarnessPath.cwd())
    print_pipeline_result(result)
    return 0 if result.status == "passed" else 1


def print_pipeline_result(result: PipelineResult) -> None:
    print(f"Pipeline: {result.name}")
    for step in result.steps:
        print(f"- {step.name}: {step.status}")
        print(f"  {step.message}")
    print(f"Pipeline result: {result.status}")
