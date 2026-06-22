"""Staged-file-aware implementation commit (Phase 79A).

Commits only explicitly requested paths while preserving unrelated
pre-existing staged files in the index.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pcae.core.paths import HarnessPath


def _git(root: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _staged_files(root: Path) -> dict[str, str]:
    """Return {path: blob_hash} for all staged files."""
    r = _git(root, "diff", "--cached", "--name-only")
    if r.returncode != 0:
        return {}
    paths = [l for l in r.stdout.strip().split("\n") if l]
    result = {}
    for p in paths:
        h = _git(root, "rev-parse", f":0:{p}")
        result[p] = h.stdout.strip() if h.returncode == 0 else ""
    return result


def _new_untracked(root: Path) -> list[str]:
    r = _git(root, "ls-files", "--others", "--exclude-standard")
    return [l for l in r.stdout.strip().split("\n") if l] if r.returncode == 0 else []


def build_implementation_commit(
    root: HarnessPath,
    message: str,
    paths: list[str],
    dry_run: bool = False,
) -> dict:
    ts = datetime.now(timezone.utc).isoformat()
    bl: list[str] = []
    wl: list[str] = []

    if not paths:
        return _blocked("no_paths_provided", ["No paths provided."], [], ts)

    if not message and not dry_run:
        return _blocked("blocked", ["No commit message provided."], [], ts)

    root_path = root.path

    # Snapshot pre-existing staged files
    staged_before = _staged_files(root_path)
    staged_before_paths = set(staged_before.keys())

    # All pre-existing staged files are protected
    requested = set(paths)
    protected = set(staged_before_paths)

    # Block if any requested path overlaps with pre-existing staged files
    conflict = requested & staged_before_paths
    if conflict:
        for c in sorted(conflict):
            bl.append(f"Requested path '{c}' is a protected pre-existing staged file.")
        return _blocked("protected_staged_file_conflict", bl, wl, ts,
                        protected_before=staged_before, requested=paths)

    # Stage only the explicit implementation paths
    stage_errors = []
    for p in paths:
        full = root_path / p
        if full.is_file() or full.exists():
            r = _git(root_path, "add", "--", p)
            if r.returncode != 0:
                stage_errors.append(f"Failed to stage '{p}': {r.stderr.strip()[:200]}")
        else:
            # Could be a deleted file
            r = _git(root_path, "add", "--", p)
            if r.returncode != 0:
                stage_errors.append(f"Path '{p}' does not exist and cannot be staged: {r.stderr.strip()[:200]}")

    if stage_errors:
        # Restore index to pre-state
        for p in paths:
            if p not in staged_before:
                _git(root_path, "reset", "HEAD", "--", p)
            else:
                _git(root_path, "checkout", "--", p)
        return _blocked("git_error", stage_errors, wl, ts,
                        protected_before=staged_before, requested=paths)

    # Verify no protected staged file blobs changed from staging
    staged_after_stage = _staged_files(root_path)
    for pp in protected:
        if pp not in staged_after_stage:
            bl.append(f"Protected staged file '{pp}' disappeared from index after staging.")
        elif staged_after_stage[pp] != staged_before[pp]:
            bl.append(f"Protected staged file '{pp}' blob changed after staging.")

    if bl:
        # Restore
        for p in paths:
            if p not in staged_before:
                _git(root_path, "reset", "HEAD", "--", p)
        return _blocked("protected_staged_file_modified", bl, wl, ts,
                        protected_before=staged_before, requested=paths)

    if dry_run:
        # Unstage what we staged (restore to pre-state)
        for p in paths:
            if p not in staged_before:
                _git(root_path, "reset", "HEAD", "--", p)
        return {
            "backend_invocation_performed": False,
            "blockers": [],
            "commit_created": False,
            "commit_hash": None,
            "commit_outcome": "dry_run",
            "committed_files": sorted(paths),
            "execution_authorized": False,
            "generated_at": ts,
            "implementation_paths_staged": sorted(paths),
            "message": message,
            "protected_files_committed": [],
            "protected_staged_file_hashes_after": {p: staged_before[p] for p in sorted(protected)},
            "protected_staged_file_hashes_before": {p: staged_before[p] for p in sorted(protected)},
            "protected_staged_files_after": sorted(protected),
            "protected_staged_files_before": sorted(protected),
            "protected_staged_files_preserved": True,
            "push_performed": False,
            "requested_paths": sorted(paths),
            "runner_execute_performed": False,
            "staged_file_aware_commit_status": "ready",
            "unexpected_committed_files": [],
            "warnings": wl,
        }

    # Commit using explicit pathspec to commit only the requested paths
    # git commit <path>... commits only those paths from the index
    commit_args = ["commit", "-m", message, "--"] + sorted(paths)
    cr = _git(root_path, *commit_args, timeout=60)
    if cr.returncode != 0:
        # Restore
        for p in paths:
            if p not in staged_before:
                _git(root_path, "reset", "HEAD", "--", p)
        return _blocked("git_error", [f"Commit failed: {cr.stderr.strip()[:300]}"], wl, ts,
                        protected_before=staged_before, requested=paths)

    # Get commit hash
    ch = _git(root_path, "rev-parse", "HEAD")
    commit_hash = ch.stdout.strip() if ch.returncode == 0 else ""

    # Verify committed files
    cf = _git(root_path, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")
    committed_files = sorted(l for l in cf.stdout.strip().split("\n") if l)

    unexpected = [f for f in committed_files if f not in requested]
    protected_committed = [f for f in committed_files if f in protected]

    # Verify protected staged files preserved
    staged_after = _staged_files(root_path)
    protected_preserved = True
    for pp in protected:
        if pp not in staged_after:
            protected_preserved = False
            wl.append(f"Protected staged file '{pp}' no longer staged after commit.")
        elif staged_after[pp] != staged_before[pp]:
            protected_preserved = False
            wl.append(f"Protected staged file '{pp}' blob changed after commit.")

    status = "committed"
    if unexpected:
        status = "unexpected_commit_files"
    if protected_committed:
        status = "protected_staged_file_conflict"
    if not protected_preserved:
        status = "protected_staged_file_lost"

    return {
        "backend_invocation_performed": False,
        "blockers": bl,
        "commit_created": True,
        "commit_hash": commit_hash,
        "commit_outcome": "committed",
        "committed_files": committed_files,
        "execution_authorized": False,
        "generated_at": ts,
        "implementation_paths_staged": sorted(paths),
        "message": message,
        "protected_files_committed": protected_committed,
        "protected_staged_file_hashes_after": {p: staged_after.get(p, "") for p in sorted(protected)},
        "protected_staged_file_hashes_before": {p: staged_before[p] for p in sorted(protected)},
        "protected_staged_files_after": sorted(p for p in protected if p in staged_after),
        "protected_staged_files_before": sorted(protected),
        "protected_staged_files_preserved": protected_preserved,
        "push_performed": False,
        "requested_paths": sorted(paths),
        "runner_execute_performed": False,
        "staged_file_aware_commit_status": status,
        "unexpected_committed_files": unexpected,
        "warnings": wl,
    }


def _blocked(status: str, bl: list[str], wl: list[str], ts: str,
             protected_before: dict | None = None,
             requested: list[str] | None = None) -> dict:
    pb = protected_before or {}
    rq = requested or []
    return {
        "backend_invocation_performed": False,
        "blockers": bl,
        "commit_created": False,
        "commit_hash": None,
        "commit_outcome": "blocked",
        "committed_files": [],
        "execution_authorized": False,
        "generated_at": ts,
        "implementation_paths_staged": [],
        "message": "",
        "protected_files_committed": [],
        "protected_staged_file_hashes_after": {},
        "protected_staged_file_hashes_before": {p: pb[p] for p in sorted(pb)},
        "protected_staged_files_after": sorted(pb.keys()),
        "protected_staged_files_before": sorted(pb.keys()),
        "protected_staged_files_preserved": True,
        "push_performed": False,
        "requested_paths": sorted(rq),
        "runner_execute_performed": False,
        "staged_file_aware_commit_status": status,
        "unexpected_committed_files": [],
        "warnings": wl,
    }


def run_commit_implementation(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    message = getattr(args, "message", "") or ""
    paths = list(getattr(args, "path", None) or [])
    dry_run = getattr(args, "dry_run", False)

    r = build_implementation_commit(root, message, paths, dry_run=dry_run)

    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
        return 0 if r["staged_file_aware_commit_status"] in ("ready", "committed") else 1

    print("Staged-File-Aware Implementation Commit")
    print("=" * 42)
    print(f"  Status: {r['staged_file_aware_commit_status']}")
    print(f"  Outcome: {r['commit_outcome']}")
    print(f"  Commit: {r['commit_hash'] or 'none'}")
    print(f"  Committed files: {len(r['committed_files'])}")
    print(f"  Protected preserved: {'yes' if r['protected_staged_files_preserved'] else 'no'}")
    if r["blockers"]:
        for b in r["blockers"]:
            print(f"  BLOCKED: {b}")
    if r["warnings"]:
        for w in r["warnings"]:
            print(f"  WARNING: {w}")
    return 0 if r["staged_file_aware_commit_status"] in ("ready", "committed") else 1
