"""Phase 149O.20L.7O.2U.2 -- CLI handlers for `pcae intake`.

Thin argument/JSON plumbing only; all validation and ECP construction
logic lives in pcae.core.intake so it can be unit-tested directly.
"""

from __future__ import annotations

import argparse
import json

from pcae.core.intake import (
    INTAKE_ADVISORY,
    build_intake_candidate_from_files,
    list_intake_records,
    lookup_intake_record,
    validate_and_ingest_intake_candidate,
)
from pcae.core.paths import HarnessPath


def run_intake_create(args: argparse.Namespace) -> int:
    try:
        raw = open(args.candidate_file, "r", encoding="utf-8").read()
    except OSError as exc:
        result = {"accepted": False, "rejection_reasons": [f"candidate_file_unreadable:{exc}"]}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("Intake Candidate: REJECTED")
            print(f"  reasons: {result['rejection_reasons']}")
        return 1

    try:
        candidate = json.loads(raw)
    except json.JSONDecodeError as exc:
        result = {"accepted": False, "rejection_reasons": [f"malformed_json:{exc}"]}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("Intake Candidate: REJECTED")
            print(f"  reasons: {result['rejection_reasons']}")
        return 1

    result = validate_and_ingest_intake_candidate(HarnessPath.cwd(), candidate)
    return _print_ingest_result(result, args.json)


def _print_ingest_result(result: dict, json_mode: bool) -> int:
    if json_mode:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("accepted") else 1

    if not result.get("accepted"):
        print("Intake Candidate: REJECTED")
        print(f"  intake_id: {result.get('intake_id')}")
        print(f"  reasons:   {result.get('rejection_reasons')}")
        print()
        print(INTAKE_ADVISORY)
        return 1

    print("Intake Candidate: ACCEPTED")
    print(f"  intake_id:                {result['intake_id']}")
    print(f"  ecp_id:                   {result['ecp_id']}")
    print(f"  idempotent_replay:        {result.get('idempotent_replay', False)}")
    print(f"  execution_allowed:        {result['execution_allowed']}")
    print(f"  promotion_executed:       {result['promotion_executed']}")
    print()
    print(INTAKE_ADVISORY)
    return 0


def run_intake_from_files(args: argparse.Namespace) -> int:
    """Build and submit a generic Intake Candidate from local file changes,
    without a tool-specific adapter.

    Producer provenance is derived from the active PCAE governance agent
    lock when one exists; `--producer` is only needed (and only accepted)
    when no lock is active, or to confirm the value the active lock
    already implies. Producer identity here is descriptive only -- it
    does not invoke any agent/tool, and it does not affect whether this
    candidate is accepted, promoted, or authorized (see INTAKE_ADVISORY).
    """
    root = HarnessPath.cwd()
    build_result = build_intake_candidate_from_files(
        root,
        task_id=args.task_id,
        candidate_id=args.candidate_id,
        file_specs=args.files,
        summary=args.summary,
        self_reported_complete=args.self_reported_complete,
        explicit_producer_kind=args.producer,
    )
    if build_result["errors"]:
        result = {"accepted": False, "rejection_reasons": build_result["errors"]}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("Intake Candidate: NOT SUBMITTED")
            print(f"  reasons: {result['rejection_reasons']}")
        return 1

    candidate = build_result["candidate"]
    if args.dry_run:
        print(json.dumps(candidate, indent=2, sort_keys=True))
        return 0

    result = validate_and_ingest_intake_candidate(root, candidate)
    return _print_ingest_result(result, args.json)


def run_intake_show(args: argparse.Namespace) -> int:
    record = lookup_intake_record(HarnessPath.cwd(), args.intake_id)
    if args.json:
        if record is None:
            print(json.dumps({"error": "intake_not_found", "intake_id": args.intake_id}, indent=2))
            return 1
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0

    if record is None:
        print(f"Intake Candidate: NOT FOUND — {args.intake_id}")
        return 1

    print("Intake Candidate")
    print(f"  intake_id:          {record['intake_id']}")
    print(f"  candidate_id:       {record.get('candidate_id')}")
    print(f"  task_id:            {record.get('task_id')}")
    print(f"  validation_outcome: {record['validation_outcome']}")
    if record.get("rejection_reasons"):
        print(f"  rejection_reasons:  {record['rejection_reasons']}")
    print(f"  ecp_id:             {record.get('ecp_id')}")
    print(f"  integrity_verified: {record.get('integrity_verified')}")
    print(f"  execution_allowed:  {record['execution_allowed']}")
    print(f"  promotion_executed: {record['promotion_executed']}")
    print()
    print(INTAKE_ADVISORY)
    return 0


def run_intake_list(args: argparse.Namespace) -> int:
    task_id = getattr(args, "task_id", None)
    records = list_intake_records(HarnessPath.cwd(), task_id=task_id)
    if args.json:
        print(json.dumps(
            {"task_id": task_id, "records": records, "count": len(records)},
            indent=2, sort_keys=True,
        ))
        return 0

    label = f" for task={task_id}" if task_id else ""
    print(f"Intake Candidates{label}: {len(records)}")
    if not records:
        print("  (none)")
        return 0
    for r in records:
        integrity_flag = "" if r.get("integrity_verified") else " [INTEGRITY MISMATCH]"
        print(f"  {r['intake_id']}  outcome={r['validation_outcome']}  ecp={r.get('ecp_id')}{integrity_flag}")
    return 0
