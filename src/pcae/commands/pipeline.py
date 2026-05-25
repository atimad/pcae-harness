from __future__ import annotations

import argparse
import json

from pcae.core.paths import HarnessPath
from pcae.core.pipeline import DEFAULT_PIPELINE_NAME, PipelineResult, run_default_pipeline


def run_pipeline(args: argparse.Namespace) -> int:
    name = args.name or DEFAULT_PIPELINE_NAME
    if name != DEFAULT_PIPELINE_NAME:
        print(f"Unknown pipeline: {name}")
        return 1

    result = run_default_pipeline(HarnessPath.cwd(), dry_run=args.dry_run)
    if args.json:
        print(json.dumps(pipeline_json_data(result), indent=2, sort_keys=True))
    else:
        print_pipeline_result(result)
    return 0 if result.status in {"passed", "planned"} else 1


def print_pipeline_result(result: PipelineResult) -> None:
    print(f"Pipeline: {result.name}")
    if result.status == "planned":
        print("Mode: dry-run")
    for step in result.steps:
        print(f"- {step.name}: {step.status}")
        print(f"  {step.message}")
    print(f"Pipeline result: {result.status}")


def pipeline_json_data(result: PipelineResult) -> dict[str, object]:
    return {
        "generated_timestamp": result.generated_timestamp,
        "overall_status": result.status,
        "pipeline_name": result.name,
        "steps": [
            {
                "artifacts": list(step.artifacts),
                "name": step.name,
                "status": step.status,
                "summary": step.message,
            }
            for step in result.steps
        ],
        "stopped_at": result.stopped_at,
    }
