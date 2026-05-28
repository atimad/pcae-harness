from __future__ import annotations

import argparse
import json

from pcae.core.orchestration import (
    ORCHESTRATION_SELECTION_ADVISORY,
    build_agent_registry_data,
    build_orchestration_data,
    build_workflow_plan,
    build_workflow_readiness,
    build_workflow_simulation,
    build_workflow_validation,
    recommend_agent,
    select_agent,
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


def run_orchestration_select(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        data = select_agent(root, args.task_type)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        matched_role = data["matched_role"] or "fallback"
        print(f"Task type: {data['task_type']}")
        print(f"Recommended agent: {data['recommended_agent']}")
        print(f"Matched role: {matched_role}")
        print(f"Fallback used: {'yes' if data['fallback_used'] else 'no'}")
        print(f"Reason: {data['reason']}")
        print(ORCHESTRATION_SELECTION_ADVISORY)
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
        print(f"Suggested workflow plan: {data['workflow']}")
        print(data["recommendation_note"])
        for step in data["steps"]:
            print(
                f"  {step['step']}. Recommended agent: "
                f"{step['recommended_agent']} -> {step['work_type']}"
            )
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
        print(f"Suggested workflow simulation: {data['workflow']}")
        print(f"Simulation mode: {data['execution_mode']}")
        print(data["recommendation_note"])
        print("Ordered steps:")
        for step in data["steps"]:
            print(
                f"  {step['step']}. Recommended agent: "
                f"{step['recommended_agent']} -> {step['work_type']}"
            )
            print(f"     Reason: {step['reason']}")
            checkpoint = step["governance_checkpoint"]
            if checkpoint:
                print(f"     Governance checkpoint: {checkpoint}")
        print(f"Final result: {data['status']}")
    return 0


def run_orchestration_validate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        data = build_workflow_validation(root, args.workflow)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"Orchestration workflow validation: {data['workflow']}")
        print("Recommendations remain advisory; validation checks coherence, not mandatory routing.")
        print(f"Validation result: {'valid' if data['valid'] else 'invalid'}")
        print("Warnings:")
        if data["warnings"]:
            for warning in data["warnings"]:
                print(f"  - {warning}")
        else:
            print("  - none")
        print("Validated steps:")
        for step in data["validated_steps"]:
            role = step["recommended_role"] or "fallback"
            print(
                f"  {step['step']}. Recommended agent: "
                f"{step['recommended_agent']} -> {step['work_type']} "
                f"(role: {role})"
            )
        print("Governance checkpoints:")
        if data["governance_checkpoints"]:
            for checkpoint in data["governance_checkpoints"]:
                print(
                    f"  {checkpoint['step']}. {checkpoint['work_type']}: "
                    f"{checkpoint['checkpoint']}"
                )
        else:
            print("  - none")
    return 0 if data["valid"] else 1


def run_orchestration_readiness(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        data = build_workflow_readiness(root, args.workflow)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"Orchestration execution readiness: {data['workflow']}")
        print(data["advisory"])
        print(f"Readiness status: {'ready' if data['ready'] else 'not ready'}")
        print("Readiness checks:")
        for check in data["readiness_checks"]:
            status = "passed" if check["passed"] else "failed"
            print(f"  - {check['name']}: {status} ({check['detail']})")
        print("Governance checkpoints:")
        if data["governance_checkpoints"]:
            for checkpoint in data["governance_checkpoints"]:
                print(
                    f"  {checkpoint['step']}. {checkpoint['work_type']}: "
                    f"{checkpoint['checkpoint']}"
                )
        else:
            print("  - none")
        print("Warnings:")
        if data["warnings"]:
            for warning in data["warnings"]:
                print(f"  - {warning}")
        else:
            print("  - none")
    return 0 if data["ready"] else 1
