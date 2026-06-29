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

# Report completeness states (Phase 92D.5)
COMPLETENESS_COMPLETE = "complete"
COMPLETENESS_PARTIAL = "partial"
COMPLETENESS_INCOMPLETE = "incomplete"

VALID_COMPLETENESS: frozenset[str] = frozenset({
    COMPLETENESS_COMPLETE,
    COMPLETENESS_PARTIAL,
    COMPLETENESS_INCOMPLETE,
})

# Trust-critical fields for a completed phase report
_TRUST_CRITICAL_FIELDS: tuple[str, ...] = (
    "phase_id", "phase_name", "status", "summary",
)
_NON_FATAL_TRUST_FIELDS: tuple[str, ...] = (
    "files_changed", "tests_run", "commits", "pushed_status",
    "test_results", "governance_results",
)
_FATAL_TRUST_FIELDS: tuple[str, ...] = (
    "phase_id", "phase_name", "status",
)

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
    # Phase 92D.5 trust contract fields
    report_completeness: str = ""
    missing_trust_fields: list[str] = field(default_factory=list)
    trust_warnings: list[str] = field(default_factory=list)
    notification_result: dict[str, Any] = field(default_factory=dict)
    # Phase 92D.8 canonical report
    canonical_report_content: str = ""
    canonical_report_used: bool = False

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

    def assess_completeness(self) -> tuple[str, list[str], list[str]]:
        """Assess report completeness and return (state, missing_fields, warnings).

        Phase 92D.5 — trust contract:
        - complete: all trust-critical and non-fatal fields are captured
        - partial: critical fields OK but some non-fatal fields missing
        - incomplete: any critical field is missing, contradictory, or stale
        """
        missing: list[str] = []
        warnings: list[str] = []

        # Check fatal trust fields
        if not self.phase_id:
            missing.append("phase_id")
        if not self.phase_name:
            missing.append("phase_name")
        if not self.status:
            missing.append("status")

        for field in _FATAL_TRUST_FIELDS:
            val = getattr(self, field, None)
            is_empty = val is None or (isinstance(val, str) and not val)
            if is_empty and field not in missing:
                missing.append(field)

        if missing:
            # Any critical field missing → incomplete
            return COMPLETENESS_INCOMPLETE, missing, warnings

        # Check non-fatal trust fields
        if self.files_changed <= 0:
            missing.append("files_changed")
        # tests_run satisfied by structured test_results when present
        if self.tests_run <= 0 and not self.test_results:
            missing.append("tests_run")
        if not self.commits:
            missing.append("commits")
        if not self.pushed_status:
            missing.append("pushed_status")
        if not self.test_results:
            missing.append("test_results")
        if not self.governance_results:
            missing.append("governance_results")

        if missing:
            warnings.append(f"Missing trust fields: {', '.join(missing)}")
            return COMPLETENESS_PARTIAL, missing, warnings

        return COMPLETENESS_COMPLETE, [], []

    def apply_trust_assessment(self) -> None:
        """Run completeness assessment and store results in the report."""
        state, missing, warnings = self.assess_completeness()
        self.report_completeness = state
        self.missing_trust_fields = missing
        self.trust_warnings = warnings

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
            "report_completeness": self.report_completeness,
            "missing_trust_fields": self.missing_trust_fields,
            "trust_warnings": self.trust_warnings,
            "notification_result": self.notification_result,
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

        # Phase 92D.5 — Report completeness
        state = self.report_completeness or self.assess_completeness()[0]
        if state == COMPLETENESS_COMPLETE:
            lines.append(f"- **Report completeness:** complete ✅")
        elif state == COMPLETENESS_PARTIAL:
            lines.append(f"- **Report completeness:** partial ⚠️")
        elif state == COMPLETENESS_INCOMPLETE:
            lines.append(f"- **Report completeness:** incomplete ❌ Manual review required.")
        if self.missing_trust_fields:
            lines.append(f"- **Missing trust fields:** {', '.join(self.missing_trust_fields)}")

        if self.completed_at:
            lines.append(f"- **Completed:** {self.completed_at}")

        # Files changed — show "not captured" instead of misleading 0.
        # Only show a number when files_changed > 0 (positively measured).
        # A zero with commits present is still misleading after push.
        if self.files_changed > 0:
            lines.append(f"- **Files changed:** {self.files_changed}")
        else:
            lines.append(f"- **Files changed:** not captured")

        # Tests run — show "not captured" instead of misleading 0.
        # When structured test_results exist, tests are considered captured.
        if self.tests_run > 0:
            lines.append(f"- **Tests run:** {self.tests_run}")
        elif self.test_results:
            count = len(self.test_results)
            lines.append(f"- **Tests run:** {count} suite(s)")
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

        # Phase 92D.5 — Trust warnings and missing fields
        if self.missing_trust_fields or self.trust_warnings:
            lines.append("## Missing Trust Fields")
            lines.append("")
            if self.missing_trust_fields:
                lines.append(f"- **Fields:** {', '.join(self.missing_trust_fields)}")
            for w in self.trust_warnings:
                lines.append(f"- ⚠️ {w}")
            lines.append("")

        if self.notification_result:
            lines.append("## Notification Dispatch")
            lines.append("")
            nr = self.notification_result
            lines.append(f"- **Dispatched:** {nr.get('dispatched', False)}")
            lines.append(f"- **Sinks:** {', '.join(nr.get('sinks', [])) or 'none'}")
            lines.append(f"- **Success:** {nr.get('success', False)}")
            if nr.get("error"):
                lines.append(f"- **Error:** {nr['error']}")
            lines.append("")

        # Phase 92D.8.1 — Report Consistency section
        consistency_warnings = [w for w in self.trust_warnings
                                if "Mismatch" in w or "canonical report and metadata" in w
                                or "canonical report validation failed" in w
                                or "no canonical report artifact" in w]
        if self.canonical_report_content or consistency_warnings:
            lines.append("## Report Consistency")
            lines.append("")
            lines.append(f"- **Canonical report:** {'present' if self.canonical_report_content else 'absent'}")
            lines.append(f"- **Metadata:** {'present' if self.commits or self.test_results or self.governance_results else 'absent'}")
            if consistency_warnings:
                lines.append(f"- **Status:** mismatch detected")
                lines.append("- **Warnings:**")
                for w in consistency_warnings:
                    lines.append(f"  - {w}")
            else:
                lines.append(f"- **Status:** consistent")
            lines.append("")

        lines.append("---")
        if self.canonical_report_used:
            lines.append(f"*Canonical report artifact. Schema version {self.schema_version}.*")
        else:
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


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 92D.8 — Canonical final report artifact contract
# ═══════════════════════════════════════════════════════════════════════════════

_CANONICAL_REPORT_PATH = ".pcae/phase-completion-report.md"


def load_canonical_report() -> str | None:
    """Load the canonical phase completion report if present.

    Returns the full Markdown content, or None if the file is absent.
    """
    from pathlib import Path as _Path
    path = _Path(_CANONICAL_REPORT_PATH)
    if not path.exists():
        return None
    try:
        content = path.read_text()
        if content.strip():
            return content
    except Exception:
        pass
    return None


def validate_canonical_report(
    content: str,
    phase_id: str,
    phase_name: str,
    status: str,
) -> tuple[bool, list[str]]:
    """Validate canonical report against expected metadata.

    Returns (is_valid, warnings).
    Checks: non-empty, phase_id present, phase_name present, status present,
    no obvious stale phase mismatch.
    """
    warnings: list[str] = []
    if not content or not content.strip():
        return False, ["canonical report is empty"]

    # Check for phase ID
    if phase_id and phase_id not in content:
        warnings.append(f"phase_id '{phase_id}' not found in canonical report")

    # Check for phase name
    if phase_name:
        # Check first 50 chars of name
        name_fragment = phase_name[:30]
        if name_fragment and name_fragment not in content:
            warnings.append(f"phase_name fragment not found in canonical report")

    # Check status
    if status and status not in content.lower():
        warnings.append(f"status '{status}' not found in canonical report")

    # Check for stale mismatch: compare title phase ID to expected
    import re
    title_match = re.search(
        r'^#\s+Phase\s+(\d+[A-Z](?:\.\d+)*)\b', content, re.MULTILINE
    )
    if title_match and phase_id:
        title_phase_id = title_match.group(1)
        if title_phase_id != phase_id:
            warnings.append(
                f"canonical report title phase_id={title_phase_id}, "
                f"expected={phase_id}"
            )

    is_valid = len(warnings) == 0
    return is_valid, warnings


def write_canonical_report(content: str) -> bool:
    """Write the canonical phase completion report.

    Returns True on success.
    """
    from pathlib import Path as _Path
    path = _Path(_CANONICAL_REPORT_PATH)
    try:
        path.write_text(content)
        return True
    except Exception:
        return False


def is_valid_status(status: str) -> bool:
    return status in VALID_STATUSES


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 92D — Automatic finalization hook
# ═══════════════════════════════════════════════════════════════════════════════


def _check_canonical_metadata_consistency(report: PhaseReport) -> None:
    """Check consistency between canonical report and structured metadata.

    Phase 92D.8.2 — refreshed: phase_id freshness, commit timing tolerance,
    check-name-aware validation comparison.
    """
    import re
    content = report.canonical_report_content
    if not content:
        return

    mismatches: list[str] = []

    # ── 1. Phase ID freshness ──────────────────────────────────────────
    # Extract current phase ID from the canonical report TITLE only.
    # Ignore recommended next phase, historical context, and prose mentions.
    current_phase_id = report.phase_id
    # Match the first H1 heading: "# Phase 92D.8.3 Complete — ..."
    title_match = re.search(
        r'^#\s+Phase\s+(\d+[A-Z](?:\.\d+)*)\b', content, re.MULTILINE
    )
    if current_phase_id and title_match:
        title_phase_id = title_match.group(1)
        if title_phase_id != current_phase_id:
            mismatches.append(
                f"canonical report title phase_id={title_phase_id}, "
                f"current phase_id={current_phase_id}"
            )

    # ── 2. Check-name-aware validation comparison ──────────────────────
    # Only compare check names that appear in BOTH canonical content and metadata
    if report.test_results:
        for name, result in report.test_results.items():
            meta_match = re.search(r'(\d+/\d+)', str(result))
            if not meta_match:
                continue
            meta_total = meta_match.group(1)

            # Require the check NAME to appear near the total in canonical content
            name_pattern = re.escape(name)
            found = re.search(
                rf'{name_pattern}[:\s]*(\d+/\d+)', content, re.IGNORECASE
            )
            if not found:
                # Check name not found in canonical — not a mismatch, just not present
                continue

            canon_total = found.group(1)
            if canon_total != meta_total:
                mismatches.append(
                    f"{name} result: canonical={canon_total} metadata={meta_total}"
                )

    # ── 3. Pushed status ───────────────────────────────────────────────
    if report.pushed_status:
        pat = re.search(r'(?:Pushed|Push)[:\s]+(pushed|not_pushed|nothing_to_push)',
                        content, re.IGNORECASE)
        if pat:
            canon_push = pat.group(1).lower()
            meta_push = report.pushed_status.lower()
            if canon_push != meta_push and canon_push != "nothing_to_push":
                mismatches.append(
                    f"pushed_status: canonical={canon_push} metadata={meta_push}"
                )

    # ── 4. Commit presence (tolerant of pre-completion timing) ─────────
    # The canonical report is written BEFORE pcae phase complete, so it
    # may not contain the final completion commit hash. Only warn if the
    # commit is present in metadata AND the content clearly references
    # a different commit as the phase commit (stale reference).
    if report.commits and len(report.commits) > 1:
        # We have multiple commits — check if any appear to be phase commits in content
        phase_commit = report.commits[0][:8]
        # Look for explicit phase commit mention in content
        commit_pattern = re.search(
            r'(?:Phase commit|commit)[:\s]+([a-f0-9]{7,40})', content, re.IGNORECASE
        )
        if commit_pattern:
            canon_commit = commit_pattern.group(1)[:8]
            if phase_commit != canon_commit:
                # Different commit — stale reference
                mismatches.append(
                    f"phase commit: canonical={canon_commit} metadata={phase_commit}"
                )

    # Apply mismatches to trust
    if mismatches:
        report.trust_warnings.append(
            "canonical report and metadata disagree"
        )
        for m in mismatches:
            report.trust_warnings.append(f"  Mismatch: {m}")
        report.trust_warnings.append("Manual review recommended.")
        if report.report_completeness == COMPLETENESS_COMPLETE:
            report.report_completeness = COMPLETENESS_PARTIAL
        if "metadata_consistency" not in report.missing_trust_fields:
            report.missing_trust_fields.append("metadata_consistency")


def _apply_canonical_and_trust(
    report: PhaseReport,
    phase_id: str,
    phase_name: str,
    status: str,
) -> None:
    """Load canonical report, validate, apply trust assessment.

    Phase 92D.8 — canonical final report artifact contract.
    """
    canonical = load_canonical_report()
    if canonical is not None:
        is_valid, cwarnings = validate_canonical_report(
            canonical, phase_id, phase_name, status,
        )
        report.canonical_report_content = canonical
        report.canonical_report_used = is_valid
        if not is_valid:
            report.trust_warnings.extend(cwarnings)
            report.trust_warnings.append(
                "canonical report validation failed — trust downgraded"
            )
    else:
        # No canonical report — warn about missing canonical artifact
        report.trust_warnings.append(
            "no canonical report artifact (.pcae/phase-completion-report.md) — "
            "future phases must use canonical report flow"
        )

    report.apply_trust_assessment()

    # Phase 92D.8.1 — Consistency guard: run AFTER trust assessment
    # so mismatches can downgrade a complete report to partial/incomplete.
    if report.canonical_report_content:
        _check_canonical_metadata_consistency(report)


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
        # Phase 92D.5/92D.8 — Apply trust assessment with canonical report
        _apply_canonical_and_trust(report, phase_id, phase_name, status)
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

    # Use timestamped markdown path for attachment — guarantees the current
    # phase report is attached (not a stale latest.md if write order changed).
    report_path = paths.get("markdown", paths.get("latest_markdown", ""))
    event = phase_report_to_notification_event(
        report,
        artifact_paths=[str(report_path)] if report_path else [],
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

    # Phase 92D.5 — Store notification result in report
    report_sinks = [r.sink_name for r in notification_results] if notification_results else []
    report_ok = all(r.success for r in notification_results) if notification_results else False
    report.notification_result = {
        "dispatched": notification_results is not None,
        "sinks": report_sinks,
        "success": report_ok,
        "error": notification_error,
    }

    # Stale-report check: verify report phase_id matches event
    if notification_results:
        for r in notification_results:
            r.metadata["report_phase_id"] = phase_id
            r.metadata["report_phase_name"] = phase_name

    return {
        "report": report,
        "paths": paths,
        "notification_results": notification_results,
        "notification_skipped": False,
        "notification_error": notification_error,
        "report_error": None,
    }
