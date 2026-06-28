"""Phase report artifact model — Phase 92A.

Creates durable, local phase report artifacts for PCAE Production v1.
Foundation for later outbound notifications, Telegram delivery, and
automatic phase-finalization reporting.

No Telegram, no notification dispatch, no automatic hooks, no enforcement.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"

VALID_STATUSES: frozenset[str] = frozenset({
    "completed",
    "failed",
    "blocked",
    "partial",
    "cancelled",
})

_REQUIRED_FIELDS: frozenset[str] = frozenset({
    "phase_id",
    "phase_name",
    "status",
    "summary",
})

# Safe filename: letters, digits, hyphens, underscores only
_SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9_.-]")


@dataclass(frozen=False)
class PhaseReport:
    """A durable phase report artifact.

    Captures the outcome of a PCAE governed phase for later inspection,
    notification, and audit.  No Telegram, no dispatch, no hooks.
    """

    schema_version: str = SCHEMA_VERSION
    phase_id: str = ""
    phase_name: str = ""
    status: str = ""
    summary: str = ""
    started_at: str | None = None
    completed_at: str = ""
    created_at: str = ""
    files_changed: int = 0
    tests_run: int = 0
    test_results: dict[str, Any] = field(default_factory=dict)
    governance_results: dict[str, Any] = field(default_factory=dict)
    commits: list[str] = field(default_factory=list)
    pushed_status: str = ""
    origin_main_head_count: int = 0
    explicit_no_go_confirmations: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    follow_ups: list[str] = field(default_factory=list)
    recommended_next_phase: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        """Return list of validation issues (empty = valid)."""
        issues: list[str] = []
        if not self.phase_id:
            issues.append("phase_id is required")
        if not self.phase_name:
            issues.append("phase_name is required")
        if not self.status:
            issues.append("status is required")
        elif self.status not in VALID_STATUSES:
            issues.append(
                f"invalid status: {self.status!r}. "
                f"Must be one of: {', '.join(sorted(VALID_STATUSES))}"
            )
        if not self.summary:
            issues.append("summary is required")
        if self.schema_version != SCHEMA_VERSION:
            issues.append(
                f"schema_version {self.schema_version!r} != expected {SCHEMA_VERSION!r}"
            )
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "status": self.status,
            "summary": self.summary,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
            "files_changed": self.files_changed,
            "tests_run": self.tests_run,
            "test_results": self.test_results,
            "governance_results": self.governance_results,
            "commits": self.commits,
            "pushed_status": self.pushed_status,
            "origin_main_head_count": self.origin_main_head_count,
            "explicit_no_go_confirmations": self.explicit_no_go_confirmations,
            "risks": self.risks,
            "follow_ups": self.follow_ups,
            "recommended_next_phase": self.recommended_next_phase,
            "metadata": self.metadata,
        }

    def render_markdown(self) -> str:
        """Render a human-readable Markdown summary.

        Uses "not captured" for unknown fields instead of misleading zeroes.
        """
        lines: list[str] = []
        lines.append(f"# Phase Report: {self.phase_name}")
        lines.append("")
        lines.append(f"- **Phase ID:** `{self.phase_id}`")
        lines.append(f"- **Status:** {self.status}")
        if self.completed_at:
            lines.append(f"- **Completed:** {self.completed_at}")

        # Files changed — show "not captured" instead of misleading 0
        if self.files_changed > 0 or self.commits:
            lines.append(f"- **Files changed:** {self.files_changed}")
        else:
            lines.append(f"- **Files changed:** not captured")

        # Tests run — show "not captured" instead of misleading 0
        if self.tests_run > 0:
            lines.append(f"- **Tests run:** {self.tests_run}")
        else:
            lines.append(f"- **Tests run:** not captured")

        # Commits
        if self.commits:
            lines.append(f"- **Commits:** {', '.join(self.commits)}")
        else:
            lines.append(f"- **Commits:** not captured")

        # Push status
        push_display = self.pushed_status if self.pushed_status else "not captured"
        lines.append(f"- **Pushed:** {push_display}")

        # origin/main..HEAD — only show if pushed
        if self.pushed_status:
            lines.append(f"- **origin/main..HEAD:** {self.origin_main_head_count}")

        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(self.summary)
        lines.append("")

        if self.governance_results:
            lines.append("## Governance Results")
            lines.append("")
            for key, val in self.governance_results.items():
                lines.append(f"- **{key}:** {val}")
            lines.append("")

        if self.test_results:
            lines.append("## Test Results")
            lines.append("")
            for key, val in self.test_results.items():
                lines.append(f"- **{key}:** {val}")
            lines.append("")

        if self.explicit_no_go_confirmations:
            lines.append("## No-Go Confirmations")
            lines.append("")
            for item in self.explicit_no_go_confirmations:
                lines.append(f"- {item}")
            lines.append("")

        if self.risks:
            lines.append("## Risks")
            lines.append("")
            for risk in self.risks:
                lines.append(f"- {risk}")
            lines.append("")

        if self.follow_ups:
            lines.append("## Follow-Ups")
            lines.append("")
            for fu in self.follow_ups:
                lines.append(f"- {fu}")
            lines.append("")

        if self.recommended_next_phase:
            lines.append("## Recommended Next Phase")
            lines.append("")
            lines.append(self.recommended_next_phase)
            lines.append("")

        lines.append("---")
        lines.append(f"*Report generated by PCAE Phase 92A. Schema version {self.schema_version}.*")
        return "\n".join(lines)

    def render_json(self) -> str:
        """Render as JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


# ── Constructors ─────────────────────────────────────────────────────────────


def make_phase_report(
    *,
    phase_id: str,
    phase_name: str,
    status: str,
    summary: str,
    **kwargs: Any,
) -> PhaseReport:
    """Create a validated PhaseReport. Raises ValueError on invalid input."""
    report = PhaseReport(
        phase_id=phase_id,
        phase_name=phase_name,
        status=status,
        summary=summary,
        created_at=kwargs.pop("created_at", _utc_now_iso()),
        **kwargs,
    )
    issues = report.validate()
    if issues:
        raise ValueError(f"Invalid phase report: {'; '.join(issues)}")
    return report


# ── File I/O ────────────────────────────────────────────────────────────────


def _safe_filename(phase_id: str) -> str:
    """Sanitize a phase_id for use in filenames."""
    return _SAFE_FILENAME_RE.sub("-", phase_id)


def _ensure_dir(reports_dir: Path) -> None:
    """Create the phase-reports directory if it doesn't exist."""
    reports_dir.mkdir(parents=True, exist_ok=True)


def write_phase_report(report: PhaseReport, reports_dir: Path) -> dict[str, str]:
    """Write a phase report as timestamped Markdown and JSON artifacts,
    and update latest.md / latest.json.

    Returns a dict with paths written.
    """
    issues = report.validate()
    if issues:
        raise ValueError(f"Cannot write invalid report: {'; '.join(issues)}")

    _ensure_dir(reports_dir)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_id = _safe_filename(report.phase_id)
    base = f"{ts}-{safe_id}"

    md_path = reports_dir / f"{base}.md"
    json_path = reports_dir / f"{base}.json"
    latest_md = reports_dir / "latest.md"
    latest_json = reports_dir / "latest.json"

    md_content = report.render_markdown()
    json_content = report.render_json()

    md_path.write_text(md_content)
    json_path.write_text(json_content)
    latest_md.write_text(md_content)
    latest_json.write_text(json_content)

    return {
        "markdown": str(md_path),
        "json": str(json_path),
        "latest_markdown": str(latest_md),
        "latest_json": str(latest_json),
    }


def read_latest_report(reports_dir: Path) -> PhaseReport | None:
    """Read the latest phase report from latest.json. Returns None if not found."""
    latest_json = reports_dir / "latest.json"
    if not latest_json.exists():
        return None
    try:
        data = json.loads(latest_json.read_text())
        return PhaseReport(**data)
    except (json.JSONDecodeError, TypeError):
        return None


# ── Helpers ──────────────────────────────────────────────────────────────────


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_valid_status(status: str) -> bool:
    return status in VALID_STATUSES


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 92D — Automatic finalization hook
# ═══════════════════════════════════════════════════════════════════════════════


def finalize_phase_report(
    phase_id: str,
    phase_name: str,
    status: str,
    summary: str,
    *,
    reports_dir: Path | None = None,
    files_changed: int = 0,
    tests_run: int = 0,
    test_results: dict[str, Any] | None = None,
    governance_results: dict[str, Any] | None = None,
    commits: list[str] | None = None,
    pushed_status: str = "",
    origin_main_head_count: int = 0,
    explicit_no_go_confirmations: list[str] | None = None,
    recommended_next_phase: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a phase report artifact and optionally dispatch notifications.

    Called automatically on pcae phase complete.  Notification failure
    is non-fatal — phase finalization always completes.

    Returns a dict with:
      report: PhaseReport (the created report)
      paths: dict (written artifact paths)
      notification_results: list[NotificationResult] or None
      notification_skipped: bool
      notification_error: str or None

    Notifications are disabled by default.  Enable with:
      PCAE_NOTIFY_ENABLED=1
      PCAE_NOTIFY_SINKS=telegram,filesystem  (optional, default: filesystem)
      PCAE_NOTIFY_OUTPUT_DIR=.pcae/notifications  (default)
    """
    import os
    from pathlib import Path as _Path

    if reports_dir is None:
        reports_dir = _Path(".pcae/phase-reports")

    # 1. Create and write the phase report
    try:
        report = make_phase_report(
            phase_id=phase_id,
            phase_name=phase_name,
            status=status,
            summary=summary,
            files_changed=files_changed,
            tests_run=tests_run,
            test_results=test_results or {},
            governance_results=governance_results or {},
            commits=commits or [],
            pushed_status=pushed_status,
            origin_main_head_count=origin_main_head_count,
            explicit_no_go_confirmations=explicit_no_go_confirmations or [],
            recommended_next_phase=recommended_next_phase,
        )
        paths = write_phase_report(report, reports_dir)
    except Exception as exc:
        return {
            "report": None,
            "paths": {},
            "notification_results": None,
            "notification_skipped": True,
            "notification_error": None,
            "report_error": str(exc),
        }

    # 2. Optionally dispatch notifications
    notify_enabled = os.environ.get("PCAE_NOTIFY_ENABLED", "").lower() in ("1", "true", "yes")
    if not notify_enabled:
        return {
            "report": report,
            "paths": paths,
            "notification_results": None,
            "notification_skipped": True,
            "notification_error": None,
            "report_error": None,
        }

    # 3. Build sinks from env config
    sink_names_raw = os.environ.get("PCAE_NOTIFY_SINKS", "filesystem")
    sink_names = [s.strip() for s in sink_names_raw.split(",") if s.strip()]
    output_dir = _Path(os.environ.get("PCAE_NOTIFY_OUTPUT_DIR", ".pcae/notifications"))

    from pcae.core.notifications import (
        NoopSink,
        FilesystemSink,
        TelegramSink,
        dispatch,
        phase_report_to_notification_event,
        NotificationSink,
    )

    event = phase_report_to_notification_event(
        report,
        artifact_paths=[str(paths.get("latest_markdown", ""))],
    )

    sinks: list[NotificationSink] = []
    for name in sink_names:
        if name == "noop":
            sinks.append(NoopSink())
        elif name == "filesystem":
            sinks.append(FilesystemSink(output_dir))
        elif name == "telegram":
            sinks.append(TelegramSink())

    notification_error: str | None = None
    notification_results = None
    if sinks:
        try:
            notification_results = dispatch(event, sinks)
        except Exception as exc:
            notification_error = str(exc)

    return {
        "report": report,
        "paths": paths,
        "notification_results": notification_results,
        "notification_skipped": False,
        "notification_error": notification_error,
        "report_error": None,
    }
