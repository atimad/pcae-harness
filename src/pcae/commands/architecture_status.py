"""CLI runner for ``pcae architecture-status inspect`` (Phase 134E.8).

Narrow, read-only inspection surface for the corrected Architecture
Status generator -- lets an operator or agent see exactly what would be
embedded in the next generated phase report (completed/current/planned
state, freshness, provenance, conflicts, runtime state) without having
to finalize a phase first. No mutation, no execution capability.
"""

from __future__ import annotations

import argparse
import json

from pcae.core.architecture_status import validate_architecture_status
from pcae.core.phase_reports import build_architecture_status


def run_architecture_status_inspect(args: argparse.Namespace) -> int:
    """pcae architecture-status inspect [--json]"""
    status = build_architecture_status()
    issues = validate_architecture_status(status)

    if getattr(args, "json", False):
        print(json.dumps({"architecture_status": status, "validation_issues": issues}, indent=2))
        return 0

    print(f"Architecture Status (schema {status.get('schema_version', '?')})")
    print(f"State marker: {status.get('state_marker', '')}")
    print(f"Freshness: {status.get('freshness', '')}")
    print()

    if status.get("completed_chapters"):
        print("Completed:")
        for chapter in status["completed_chapters"]:
            print(f"  - [{chapter['chapter']}] {chapter['label']}")
        print()

    current_id = status.get("current_phase_id", "")
    if status.get("in_progress"):
        print("In Progress:")
        for item in status["in_progress"]:
            print(f"  - {item}")
    elif current_id:
        print(f"Current phase: {current_id} (completed)")
    else:
        print("Current phase: none (no active governed phase)")
    print()

    if status.get("planned"):
        print("Planned:")
        for item in status["planned"]:
            print(f"  - {item}")
    else:
        print("Planned: (none disclosed)")
    print()

    print("Runtime:")
    print(f"  State: {status.get('current_runtime_state', '') or 'unknown'}")
    print(f"  Maximum Capability: {status.get('current_maximum_capability', '') or 'unknown'}")
    print(f"  Execution Availability: {status.get('execution_availability', '') or 'unknown'}")
    print()

    if status.get("limitations"):
        print("Limitations:")
        for item in status["limitations"]:
            print(f"  - {item}")
        print()

    if status.get("conflicts"):
        print("Conflicts:")
        for item in status["conflicts"]:
            print(f"  - {item}")
        print()

    print("Source provenance:")
    for name, outcome in status.get("source_provenance", {}).items():
        print(f"  - {name}: {outcome}")
    print()

    if issues:
        print("Validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("Validation: passed")
    return 0
