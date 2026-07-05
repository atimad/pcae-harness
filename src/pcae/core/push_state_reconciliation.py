"""Phase 114C: Push Authorization & Post-Push Reconciliation.

Phase 114B's forensic verification found the root cause this module fixes:
``_finalize_report_and_notify``/``_finalize_task_report_and_notify`` read
``pushed_status``/``origin_main_head_count`` from the declared, static
``.pcae/phase-completion-metadata.json`` -- never re-deriving them from
live git state. A genuinely pushed repository (confirmed by ``pcae push
check``: ``origin/main..HEAD`` = 0) was quarantined by ``pcae phase
complete`` because the metadata file still held pre-push values nobody
had refreshed.

This module makes live git state authoritative for current push state
whenever it can be determined, while preserving exact prior behavior
(trusting declared metadata) whenever it cannot be -- notably, isolated
test repositories with no real ``origin`` remote, where live derivation is
fundamentally inconclusive rather than "confirmed unpushed."
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class LivePushState:
    """What git itself reports about the current push state, with an
    explicit ``determinable`` flag distinguishing "confirmed" from
    "couldn't be checked" -- collapsing those into a bare ``0``/``""``
    would make an indeterminate repo (no ``origin/main`` ref, as in an
    isolated test fixture) indistinguishable from a genuinely clean one.
    """

    determinable: bool
    origin_main_head_count: int | None
    pushed_status: str  # "pushed" | "not_pushed" | ""


def compute_live_push_state(timeout: int = 10) -> LivePushState:
    """Derive push state directly from git.

    Returns ``determinable=False`` whenever ``origin/main`` cannot be
    resolved (no such remote-tracking ref) or any git invocation fails --
    the caller must fall back to declared metadata in that case, exactly
    as every finalization path did before this phase.
    """
    try:
        ref_check = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", "origin/main"],
            capture_output=True, text=True, timeout=timeout,
        )
    except Exception:
        return LivePushState(determinable=False, origin_main_head_count=None, pushed_status="")
    if ref_check.returncode != 0:
        return LivePushState(determinable=False, origin_main_head_count=None, pushed_status="")

    try:
        count_result = subprocess.run(
            ["git", "rev-list", "--count", "origin/main..HEAD"],
            capture_output=True, text=True, timeout=timeout,
        )
    except Exception:
        return LivePushState(determinable=False, origin_main_head_count=None, pushed_status="")
    if count_result.returncode != 0 or not count_result.stdout.strip().isdigit():
        return LivePushState(determinable=False, origin_main_head_count=None, pushed_status="")

    count = int(count_result.stdout.strip())
    return LivePushState(
        determinable=True,
        origin_main_head_count=count,
        pushed_status="pushed" if count == 0 else "not_pushed",
    )


@dataclass(frozen=True)
class ReconciledPushState:
    """The single, authoritative push-state view finalization consumes.

    ``pushed_status``/``origin_main_head_count`` are what callers should
    use everywhere they previously read those two fields straight from
    metadata. The remaining fields are diagnostics only -- present so a
    stale-metadata discrepancy is always visible (Objective 8), never
    silently reconciled away without a trace.
    """

    pushed_status: str
    origin_main_head_count: int
    source: str  # "live" | "metadata"
    live_determinable: bool
    live_origin_main_head_count: int | None
    metadata_pushed_status: str
    metadata_origin_main_head_count: int | None
    metadata_push_state_stale: bool

    def to_diagnostics(self) -> dict:
        """Objective 8 shape: always visible, never hidden."""
        return {
            "reconciled_push_state": self.pushed_status,
            "reconciled_origin_main_head_count": self.origin_main_head_count,
            "push_state_source": self.source,
            "metadata_push_state_stale": self.metadata_push_state_stale,
            "metadata_pushed_status": self.metadata_pushed_status,
            "metadata_origin_main_head_count": self.metadata_origin_main_head_count,
            "live_origin_main_head_count": self.live_origin_main_head_count,
        }


def reconcile_push_state(metadata: dict, live: LivePushState | None = None) -> ReconciledPushState:
    """Reconcile declared metadata against live git state.

    Live state wins whenever it is determinable (Objective 2: live git /
    ``pcae push check`` is the authoritative source). When live state is
    not determinable -- no resolvable ``origin/main`` ref, as in an
    isolated test repository with no real remote -- declared metadata is
    used exactly as every finalization path used it before this phase, so
    existing fixtures and callers that never configured a real origin are
    unaffected.
    """
    if live is None:
        live = compute_live_push_state()

    metadata_pushed_status = str(metadata.get("pushed_status") or "")
    metadata_origin_count = metadata.get("origin_main_head_count")
    if not isinstance(metadata_origin_count, int):
        metadata_origin_count = None

    if live.determinable:
        stale = (
            (metadata_pushed_status != "" and metadata_pushed_status != live.pushed_status)
            or (metadata_origin_count is not None and metadata_origin_count != live.origin_main_head_count)
        )
        return ReconciledPushState(
            pushed_status=live.pushed_status,
            origin_main_head_count=live.origin_main_head_count,
            source="live",
            live_determinable=True,
            live_origin_main_head_count=live.origin_main_head_count,
            metadata_pushed_status=metadata_pushed_status,
            metadata_origin_main_head_count=metadata_origin_count,
            metadata_push_state_stale=stale,
        )

    return ReconciledPushState(
        pushed_status=metadata_pushed_status,
        origin_main_head_count=metadata_origin_count if metadata_origin_count is not None else 0,
        source="metadata",
        live_determinable=False,
        live_origin_main_head_count=None,
        metadata_pushed_status=metadata_pushed_status,
        metadata_origin_main_head_count=metadata_origin_count,
        metadata_push_state_stale=False,
    )
