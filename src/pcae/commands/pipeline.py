from __future__ import annotations

import argparse
import json

from pcae.core.paths import HarnessPath
from pcae.core.pipeline import (
    DEFAULT_PIPELINE_NAME,
    PipelineDefinition,
    PipelineResult,
    available_pipelines,
    run_default_pipeline,
)


def run_pipeline_list(args: argparse.Namespace) -> int:
    pipelines = available_pipelines()
    if args.json:
        print(json.dumps(pipeline_list_json_data(pipelines), indent=2, sort_keys=True))
    else:
        print_pipeline_list(pipelines)
    return 0


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


def print_pipeline_list(pipelines: tuple[PipelineDefinition, ...]) -> None:
    print("Available pipelines:")
    for pipeline in pipelines:
        print(f"- {pipeline.name}")
        print(f"  Description: {pipeline.description}")
        print(f"  Dry-run supported: {format_bool(pipeline.supports_dry_run)}")
        print(f"  JSON output supported: {format_bool(pipeline.supports_json)}")
        print("  Steps:")
        for index, step in enumerate(pipeline.steps, start=1):
            print(f"    {index}. {step}")


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


def pipeline_list_json_data(
    pipelines: tuple[PipelineDefinition, ...],
) -> dict[str, object]:
    return {
        "pipelines": [
            {
                "description": pipeline.description,
                "name": pipeline.name,
                "steps": list(pipeline.steps),
                "supports_dry_run": pipeline.supports_dry_run,
                "supports_json": pipeline.supports_json,
            }
            for pipeline in pipelines
        ]
    }


def format_bool(value: bool) -> str:
    return "yes" if value else "no"
