"""Phase 114D.1: Post-Push Canonicalization & Notification Reconciliation.

Phase 114D's own `pcae agent verify-handoff` run against this real
repository found a live defect immediately after 114D's own governed
push: `.pcae/phase-completion-metadata.json` declared phase_id `114D`,
but `.pcae/phase-reports/latest.json` was still `114A` -- canonical
report promotion never reran after the push that made the repository
push-clean. Every finalization attempt *during* `pcae task finish
--commit` is inherently evaluated one commit before that commit is
pushed (the closure commit itself), so the Repository Transition
Validator correctly quarantines it (Phase 113X/114C behavior, unchanged
and still correct) -- but nothing ever re-evaluated finalization
*after* the subsequent push actually landed.

This module provides the two pure, read-only decisions
`pcae push` consults to decide whether to re-trigger finalization:

- `reconciliation_pending(root)` -- does declared metadata describe a
  phase that has not yet been canonically promoted?
- `live_push_is_clean(root)` -- is the working tree clean *and* does
  live git state (Phase 114C's `compute_live_push_state()`) confirm
  `origin/main..HEAD == 0`?

Both are pure queries; neither writes anything. The actual promotion +
notification re-run is triggered by `pcae push` itself
(`src/pcae/commands/push.py`), which calls the existing
`_finalize_report_and_notify(...)` (`src/pcae/commands/phase.py`) --
already carrying Phase 114C's live push-state reconciliation and Phase
114B's notification certification/idempotency. Nothing here duplicates
that logic.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import read_latest_report
from pcae.core.push_state_reconciliation import compute_live_push_state


def load_completion_metadata(root: HarnessPath) -> dict:
    path = root.join(Path(".pcae") / "phase-completion-metadata.json")
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def reconciliation_pending(root: HarnessPath) -> tuple[bool, str, dict]:
    """Whether declared phase-completion metadata names a phase that has
    not yet been canonically promoted.

    Returns ``(pending, reason, metadata)``. Comparing canonical state
    directly (rather than tracking "have we already reconciled this")
    makes repeated calls naturally idempotent: once promotion succeeds,
    the canonical report agrees with metadata and this returns
    ``pending=False`` on every subsequent call for the same metadata.
    """
    metadata = load_completion_metadata(root)
    metadata_phase_id = metadata.get("phase_id") if isinstance(metadata.get("phase_id"), str) else None
    if not metadata_phase_id:
        return False, "no phase-completion metadata declared", metadata
    if metadata.get("status") != "completed":
        return False, "metadata status is not 'completed'", metadata

    reports_dir = root.join(Path(".pcae") / "phase-reports")
    report = read_latest_report(reports_dir)
    if report is None:
        return (
            True,
            f"no canonical report exists yet (metadata declares phase_id {metadata_phase_id!r})",
            metadata,
        )
    if report.phase_id != metadata_phase_id:
        return (
            True,
            f"canonical report phase_id {report.phase_id!r} does not match metadata phase_id {metadata_phase_id!r}",
            metadata,
        )
    return False, "canonical report already matches metadata", metadata


def live_push_is_clean(root: HarnessPath) -> bool:
    """Whether it is safe to promote a canonical report right now.

    Requires both a clean working tree and live-confirmed
    `origin/main..HEAD == 0` (Phase 114C's `compute_live_push_state()`).
    Never returns True on a dirty tree or genuinely unpushed commits --
    canonicalization must never run ahead of what has actually reached
    `origin/main` (Objective 6).
    """
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=root.path, capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return False
    if status.returncode != 0 or status.stdout.strip():
        return False

    live = compute_live_push_state()
    return live.determinable and live.origin_main_head_count == 0
