from __future__ import annotations

import argparse
import json

from pcae.core.orchestration import (
    build_agent_registry_data,
    build_orchestration_data,
    build_workflow_plan,
    build_workflow_simulation,
    recommend_agent,
)
from pcae.core.paths import HarnessPath


def run_orchestration_policy(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        data = build_orchestration_data(root)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Orchestration policy")
        print(f"Default agent: {data['default_agent']}")
        print(f"Documentation agent: {data['documentation_agent']}")
        print(f"Runtime agent: {data['runtime_agent']}")
        print(f"Validation agent: {data['validation_agent']}")
    return 0


def run_orchestration_agents(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        data = build_agent_registry_data(root)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Agent registry")
        for entry in data:
            roles = ", ".join(entry["roles"])
            print(f"{entry['agent_id']} ({entry['kind']}): {roles}")
    return 0


def run_orchestration_recommend(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        data = recommend_agent(root, args.work_type)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"Work type: {data['work_type']}")
        print(f"Recommended agent: {data['recommended_agent']}")
        print(f"Reason: {data['reason']}")
    return 0


def run_orchestration_plan(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        data = build_workflow_plan(root, args.workflow)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"Workflow plan: {data['workflow']}")
        for step in data["steps"]:
            print(f"  {step['step']}. {step['assigned_agent']} -> {step['work_type']}")
            print(f"     Reason: {step['reason']}")
    return 0


def run_orchestration_simulate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        data = build_workflow_simulation(root, args.workflow)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"Workflow simulation: {data['workflow']}")
        print(f"Simulation mode: {data['execution_mode']}")
        print("Ordered steps:")
        for step in data["steps"]:
            print(f"  {step['step']}. {step['assigned_agent']} -> {step['work_type']}")
            print(f"     Reason: {step['reason']}")
            checkpoint = step["governance_checkpoint"]
            if checkpoint:
                print(f"     Governance checkpoint: {checkpoint}")
        print(f"Final result: {data['status']}")
    return 0
