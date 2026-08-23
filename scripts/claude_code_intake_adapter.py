#!/usr/bin/env python3
"""Thin reference adapter: Claude Code -> the generic PCAE intake contract.

Phase 149O.20L.7O.2U.1 froze the intake contract as generic (not
Claude-Code-specific); Phase 149O.20L.7O.2U.2 implements this script as the
first concrete producer against it. No Claude-Code-specific field or
semantic is added here that PCAE's core intake contract (pcae.core.intake)
depends on -- this script only *translates* a simple description of files
Claude Code touched into the generic Intake Candidate document, then calls
`pcae intake create` exactly as any other producer would.

This adapter cannot bypass hash verification, repo/base-commit binding, or
the task-scope check: it does not talk to any PCAE internals directly, only
to `pcae intake create` over the same CLI/JSON boundary any external caller
uses. It also cannot set promotion_authorized, execution_allowed, or any
other authority-bearing field -- those fields do not exist in this script's
input or output at all.

Usage:
    python3 scripts/claude_code_intake_adapter.py \\
        --task-id <task_id> \\
        --candidate-id <stable-id-for-this-proposed-change> \\
        --file <repo-relative-path>:<operation>:<path-to-new-content-file> \\
        [--file ... repeatable] \\
        --summary "what Claude Code says it did" \\
        [--self-reported-complete] \\
        [--dry-run]

`--file` accepts operation in {create, modify, delete}. For "delete", the
third component is omitted: `--file path/to/removed.py:delete`.

The adapter computes repo_binding (repo_fingerprint, base_commit=current
HEAD) itself from the real repository state -- it never trusts a caller
to supply these, since they are exactly the fields PCAE's intake contract
uses to reject a stale or foreign diff.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _git(*args: str) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def _repo_fingerprint() -> str:
    roots = sorted(
        line.strip() for line in _git("rev-list", "--max-parents=0", "HEAD").splitlines() if line.strip()
    )
    return hashlib.sha256("|".join(roots).encode("utf-8")).hexdigest()


def _parse_file_arg(raw: str) -> dict:
    parts = raw.split(":", 2)
    if len(parts) < 2:
        raise ValueError(f"invalid --file value (need path:operation[:content_file]): {raw!r}")
    path, operation = parts[0], parts[1]
    if operation == "delete":
        return {"path": path, "operation": "delete"}
    if len(parts) != 3:
        raise ValueError(f"--file for operation {operation!r} needs a content file: {raw!r}")
    content_path = parts[2]
    content = Path(content_path).read_text(encoding="utf-8")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return {
        "path": path,
        "operation": operation,
        "content_after": content,
        "content_hash_after": content_hash,
    }


def build_intake_candidate(
    task_id: str,
    candidate_id: str,
    files: list[str],
    summary: str,
    self_reported_complete: bool,
) -> dict:
    return {
        "intake_contract_version": "1.0",
        "candidate_id": candidate_id,
        "producer": {
            "kind": "claude-code",
            "adapter_version": "2U.2-reference-1",
        },
        "task_context": {
            "task_id": task_id,
            "declared_goal": summary,
        },
        "repo_binding": {
            "repo_fingerprint": _repo_fingerprint(),
            "base_commit": _git("rev-parse", "HEAD"),
        },
        "proposed_changes": [_parse_file_arg(f) for f in files],
        "producer_claims": {
            "summary": summary,
            "self_reported_complete": bool(self_reported_complete),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--file", dest="files", action="append", default=[], required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--self-reported-complete", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print the candidate document, do not submit it.")
    args = parser.parse_args(argv)

    try:
        candidate = build_intake_candidate(
            args.task_id, args.candidate_id, args.files, args.summary, args.self_reported_complete,
        )
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"adapter_error: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(json.dumps(candidate, indent=2, sort_keys=True))
        return 0

    candidate_path = Path(f"/tmp/claude-code-intake-{args.candidate_id}.json")
    candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True))
    proc = subprocess.run(
        ["pcae", "intake", "create", "--candidate-file", str(candidate_path), "--json"],
        capture_output=True, text=True,
    )
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
