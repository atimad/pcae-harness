from __future__ import annotations

import argparse
import json

from pcae.core.paths import HarnessPath
from pcae.core.review import (
    VALID_DISPOSITIONS,
    create_lifecycle_review,
    list_lifecycle_reviews,
    show_lifecycle_review,
)


def run_lifecycle_review_create(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()

    if args.disposition not in VALID_DISPOSITIONS:
        print(f"Invalid disposition: {args.disposition}")
        print(f"Valid: {', '.join(VALID_DISPOSITIONS)}")
        return 1

    record = create_lifecycle_review(
        root,
        disposition=args.disposition,
        notes=args.notes or "",
        reviewer=args.reviewer or "human",
        task_id=getattr(args, "task", None),
        commit_range=getattr(args, "commit_range", None),
    )

    if args.json:
        print(json.dumps(record.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"Created lifecycle review: {record.lrr_id}")
        print(f"  Task: {record.task_id}")
        print(f"  Disposition: {record.disposition}")
        print(f"  Reviewer: {record.reviewer}")
        if record.commit_range != "unknown":
            print(f"  Commit range: {record.commit_range}")
        if record.notes:
            print(f"  Notes: {record.notes}")

    return 0


def run_lifecycle_review_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    record = show_lifecycle_review(root, args.lrr_id)

    if record is None:
        print(f"Lifecycle review not found: {args.lrr_id}")
        return 1

    if args.json:
        print(json.dumps(record.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"Lifecycle review: {record.lrr_id}")
        print(f"  Task: {record.task_id}")
        print(f"  Disposition: {record.disposition}")
        print(f"  Reviewer: {record.reviewer}")
        print(f"  Commit range: {record.commit_range}")
        if record.reviewed_files:
            print("  Reviewed files:")
            for f in record.reviewed_files:
                print(f"    - {f}")
        if record.notes:
            print(f"  Notes: {record.notes}")
        print(f"  Created: {record.created_at}")

    return 0


def run_lifecycle_review_list(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    task_id = getattr(args, "task", None)
    open_only = getattr(args, "open", False)

    records = list_lifecycle_reviews(root, task_id=task_id, open_only=open_only)

    if args.json:
        print(json.dumps(
            {"reviews": [r.to_dict() for r in records]},
            indent=2, sort_keys=True,
        ))
    else:
        if not records:
            print("No lifecycle reviews found.")
        else:
            print(f"Lifecycle reviews: {len(records)}")
            for record in records:
                print(f"  [{record.disposition}] {record.lrr_id} — {record.task_id}")

    return 0
