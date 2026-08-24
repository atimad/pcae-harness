#!/usr/bin/env python3
"""Deprecated thin compatibility wrapper: Claude Code -> `pcae intake from-files`.

Phase 149O.20L.7O.2U.1 froze the intake contract as generic; Phase
149O.20L.7O.2U.2 implemented this script as a Claude-labelled reference
adapter against it. Phase 149O.20L.7O.2W consolidated that generic logic
(repo/base binding, content hashing, candidate assembly, producer
provenance derivation) into `pcae.core.intake` and the producer-neutral
`pcae intake from-files` CLI command, so it is no longer duplicated here.

This script now does nothing but translate its own CLI arguments into an
equivalent `pcae intake from-files` invocation and shell out to it -- it
contains no intake-contract logic, no repo-fingerprint logic, and no
content-hashing logic of its own. It exists only for callers that already
invoke this exact path/argument shape; new callers should invoke
`pcae intake from-files` directly.

No Claude-specific behavior remains beyond this file's name and the
absence of a hardcoded producer: producer.kind is derived from the active
PCAE governance agent lock the same way it would be for Codex, a custom
agent, or any other bootstrapped identity (see `pcae session bootstrap`).
If no governance lock is active, pass `--producer` explicitly to preserve
the old always-"claude-code" behavior, or bootstrap a session first
(recommended): `pcae session bootstrap --agent-id claude-local`.

This script cannot bypass hash verification, repo/base-commit binding, or
the task-scope check: it still only talks to `pcae intake from-files`
(itself only `pcae intake create` internally) over the same CLI boundary
any external caller uses. It also cannot set promotion_authorized,
execution_allowed, or any other authority-bearing field -- those fields
do not exist in this script's input or output at all.

Usage (unchanged from the prior reference-adapter version):
    python3 scripts/claude_code_intake_adapter.py \\
        --task-id <task_id> \\
        --candidate-id <stable-id-for-this-proposed-change> \\
        --file <repo-relative-path>:<operation>:<path-to-new-content-file> \\
        [--file ... repeatable] \\
        --summary "what Claude Code says it did" \\
        [--self-reported-complete] \\
        [--producer <explicit-producer-id>] \\
        [--dry-run]

`--file` accepts operation in {create, modify, delete}. For "delete", the
third component is omitted: `--file path/to/removed.py:delete`.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--file", dest="files", action="append", default=[], required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--self-reported-complete", action="store_true")
    parser.add_argument(
        "--producer", default=None,
        help="Explicit producer identity; only used when no PCAE governance agent lock is active.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the candidate document, do not submit it.")
    args = parser.parse_args(argv)

    cmd = [
        "pcae", "intake", "from-files",
        "--task-id", args.task_id,
        "--candidate-id", args.candidate_id,
    ]
    for f in args.files:
        cmd += ["--file", f]
    if args.summary:
        cmd += ["--summary", args.summary]
    if args.self_reported_complete:
        cmd += ["--self-reported-complete"]
    if args.producer:
        cmd += ["--producer", args.producer]
    if args.dry_run:
        cmd += ["--dry-run"]
    cmd += ["--json"]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
