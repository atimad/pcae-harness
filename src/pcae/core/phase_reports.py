"""Phase report artifact model — Phase 92A.

Creates durable, local phase report artifacts for PCAE Production v1.
Foundation for later outbound notifications, Telegram delivery, and
automatic phase-finalization reporting.

No Telegram, no notification dispatch, no automatic hooks, no enforcement.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Mapping
from typing import Any

from pcae.core import phase_id as canonical_phase_id
from pcae.core.canonical_artifact_promotion import (
    ArtifactState as PromotionArtifactState,
    promote_artifact,
    quarantine_artifact,
)

SCHEMA_VERSION = "1.0"

# Phase 134E.1V-repair — shared canonical-report-title phase-ID extraction.
#
# Previously duplicated independently in validate_canonical_report() and
# _check_canonical_metadata_consistency() as the literal pattern
# ``r'^#\s+Phase\s+(\d+[A-Z](?:\.\d+)*)\b'``. That pattern's trailing
# ``\b`` cannot be satisfied when a dotted sub-phase number is immediately
# followed by a bare verification-suffix letter (e.g. "134E.1V",
# "134E.10V"): after the optional ``(?:\.\d+)*`` group consumes ".1", the
# next character "V" is a word character too, so no word boundary exists
# there and the regex engine backtracks the *entire* dotted group away,
# landing on the bare family prefix ("134E") instead of failing outright.
# That silently collapsed a sub-phase's identity into its parent's,
# exactly the "canonical title parsing collapses a sub-phase into its
# parent" failure mode -- confirmed as the root cause of the 134E.1V
# report/metadata mismatch this repair closes.
#
# Fixed by allowing one optional bare letter inside each dotted segment
# (``\.\d+[A-Za-z]?``) so the suffix is consumed as part of the
# identifier instead of trailing it. 134E, 134E.1, 134E.2, 134E.10,
# 134B.3 (no trailing letter) are unaffected; 134E.1V, 134E.10V (and any
# future dotted sub-phase with a verification suffix) now extract in
# full, matching the identifier as declared everywhere else (CLI
# argument, metadata, task title) rather than a truncated parent.
# Phase 136AX: the mainline branch letter is one-or-more (``[A-Z]+``), not
# exactly one. A phase series that exhausts single letters A-Z rolls over
# into two-letter mainline suffixes (136Z -> 136AA -> ... -> 136AW ->
# 136AX). The single-letter grammar silently failed to parse every such
# two-letter phase ID's canonical title -- reproduced directly against
# this repository's own live PROJECT_STATUS.md ("Phase 136AW -- ...")
# once Track 136 passed "136Z". Matches the grammar already used
# Phase 137R — the phase-ID *grammar* itself is now owned exclusively by
# the canonical parser (``pcae.core.phase_id``, CPIPC-001 §6). Only the
# title-heading shape ("a line starting with '# Phase '") remains here,
# since recognizing a canonical report's title heading is lifecycle
# business logic, not Phase ID grammar (CPIPC-001 §7). The candidate
# substring after the heading prefix is handed to the canonical parser's
# anchored token match, never re-parsed locally.
_CANONICAL_TITLE_PREFIX_RE = re.compile(r'^#\s+Phase\s+', re.MULTILINE)


def _extract_canonical_title_phase_id(content: str) -> str | None:
    """Extract the phase ID from a canonical report's title (first ``#
    Phase <id> ...`` heading), or ``None`` if the title does not match.
    The single shared extraction path for both ``validate_canonical_
    report()`` and ``_check_canonical_metadata_consistency()`` -- fixes
    the divergent-normalization risk of two independently maintained
    copies of the same pattern by construction.
    """
    prefix_match = _CANONICAL_TITLE_PREFIX_RE.search(content)
    if prefix_match is None:
        return None
    token = canonical_phase_id.match_leading_token(content[prefix_match.end():])
    return token.normalized_text if token is not None else None


_OPTIONAL_PHASE_PREFIX_RE = re.compile(r"^\s*Phase\s+", re.IGNORECASE)


def _leading_phase_token(text: str | None) -> str | None:
    """Best-effort leading Phase ID token, with an optional literal
    "Phase " prefix skipped first (137T: a single shared extraction path
    replacing several independently-drifting copies of the same
    ``\\d+[A-Za-z]*(?:\\.[\\d]+[A-Za-z]*)*`` grammar fragment that had
    accumulated across this module's own recommended-next-phase and
    current-phase-identity checks; recognition itself delegates to the
    canonical parser, CPIPC-001, CPIPC-REQ-018). Returns ``None`` if no
    leading token parses.
    """
    stripped = (text or "").strip()
    prefix_match = _OPTIONAL_PHASE_PREFIX_RE.match(stripped)
    candidate_text = stripped[prefix_match.end():] if prefix_match else stripped
    token = canonical_phase_id.match_leading_token(candidate_text)
    return token.normalized_text if token is not None else None


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

# Phase 137I.1 — a fourth, explicitly NON-AUTHORITATIVE canonical state.
# A "pending_push" report is one whose ONLY remaining blocker is that its
# phase has not been pushed yet (see `blockers_are_push_state_only`). It is
# written to the canonical latest.* slot so push readiness's phase-report-
# identity gate (137F.1) can be satisfied and the governed push can proceed,
# but it is never trust-complete, never authoritative, and never notified.
# A normal re-finalization after the push promotes it to COMPLETE and
# dispatches exactly one notification. This is deliberately NOT a member of
# any "authoritative"/"complete" set: every `== COMPLETENESS_COMPLETE`
# authority check correctly treats it as not-yet-complete.
COMPLETENESS_PENDING_PUSH = "pending_push"

VALID_COMPLETENESS: frozenset[str] = frozenset({
    COMPLETENESS_COMPLETE,
    COMPLETENESS_PARTIAL,
    COMPLETENESS_INCOMPLETE,
    COMPLETENESS_PENDING_PUSH,
})


def blockers_are_push_state_only(blockers, missing_trust_fields=None) -> bool:
    """Phase 137I.1 — True iff EVERY finalization-gate blocker is a pure
    consequence of the phase not having been pushed yet, and no non-push
    trust field is missing.

    The closed set of push-derived blocker messages emitted by
    ``validate_finalization_gate`` / report completeness assessment is:

      - ``"pushed_status is ..., not pushed/clean"``
      - ``"origin/main..HEAD is N, not 0"``
      - ``"pcae_push_check is ..., not clean"``
      - ``"report completeness is 'partial', not complete"`` (accepted only
        because the report's own missing trust fields are checked to be
        exclusively push-state below)
      - ``"missing trust fields: ..."`` (accepted only when every listed
        field is a push-state field)

    Any other blocker (phase identity, internal/derived coherence,
    governance, no-go confirmations, stale/cross-phase commits, ...) means
    the report has a genuine integrity defect and must be quarantined --
    never staged as a pending canonical report. This function is what keeps
    the 137I.1 pending-report escape from ever weakening a real trust gate:
    it only ever fires when the sole obstacle is "not pushed yet."
    """
    from pcae.core.phase_report_trust import PUSH_STATE_FIELDS

    if not blockers:
        return False
    push_fields = set(PUSH_STATE_FIELDS)
    missing = {str(f).strip() for f in (missing_trust_fields or [])}
    if missing - push_fields:
        return False
    for raw in blockers:
        b = str(raw).strip()
        if b.startswith("pushed_status is "):
            continue
        if b.startswith("origin/main..HEAD is "):
            continue
        if b.startswith("pcae_push_check is "):
            continue
        if b == "report completeness is 'partial', not complete":
            continue
        if b.startswith("missing trust fields:"):
            listed = [
                f.strip()
                for f in b[len("missing trust fields:"):].split(",")
                if f.strip()
            ]
            if listed and all(f in push_fields for f in listed):
                continue
            return False
        return False
    return True

# Notification outcome model (Phase 113X.3) — explicit, recorded result of a
# finalization's attempt to notify the mobile/Telegram channel. Distinct from
# NotificationResult.success (per-sink), this is the single overall outcome
# threaded through finalize_phase_report()'s return value and persisted on
# PhaseReport.notification_result, so "was the operator told, and if not, why"
# is always answerable from the report/status output alone.
NOTIFICATION_OUTCOME_ATTEMPTED = "attempted"
NOTIFICATION_OUTCOME_SENT = "sent"
NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON = "skipped_with_reason"
NOTIFICATION_OUTCOME_FAILED_WITH_REASON = "failed_with_reason"

VALID_NOTIFICATION_OUTCOMES: frozenset[str] = frozenset({
    NOTIFICATION_OUTCOME_ATTEMPTED,
    NOTIFICATION_OUTCOME_SENT,
    NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON,
    NOTIFICATION_OUTCOME_FAILED_WITH_REASON,
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

# ── Phase 95F.2: required governance and test result keys ──────────────

_REQUIRED_GOVERNANCE_KEYS: tuple[str, ...] = (
    "pcae_health",
    "pcae_check",
    "pcae_doctor_task_memory",
    "pcae_push_check",
    "telegram_runtime",
)

_REQUIRED_BASE_TEST_RESULT_KEYS: tuple[str, ...] = (
    "report_notification_tests",
    "bootstrap_session_reporting_tests",
    "fast_green",
)

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
    # Phase 113C — PCAE Architecture Status (auto-derived from canonical state)
    architecture_status: dict[str, Any] = field(default_factory=dict)

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
        # Phase 95I.1 — commit ownership validation.
        # If commits are present but metadata doesn't declare phase_commits
        # or commit_attribution, warn that commit ownership is unverified.
        # This is a trust warning, not a blocking missing field — it does
        # not downgrade the report to partial on its own.
        elif self.files_changed > 0:
            md = self.metadata or {}
            if not md.get("phase_commits") and not md.get("commit_attribution"):
                if "commits.phase_owned not verified — no phase_commits in metadata" not in warnings:
                    warnings.append("commits.phase_owned not verified — no phase_commits in metadata")
        if not self.pushed_status:
            missing.append("pushed_status")
        # Phase 95I.1 — push-state completeness hardening.
        # A final report must not claim "complete" when unpushed or dirty.
        if self.pushed_status and self.pushed_status not in ("pushed", "clean", "nothing_to_push"):
            if "pushed_status" not in missing:
                missing.append("pushed_status")
        if self.origin_main_head_count > 0:
            missing.append("origin_main_head")
        # governance_results.pcae_push_check must indicate clean state
        if self.governance_results:
            push_check = self.governance_results.get("pcae_push_check", "")
            if push_check and push_check not in ("clean", "nothing_to_push", "clean (nothing_to_push)"):
                if "governance_results.pcae_push_check" not in missing:
                    missing.append("governance_results.pcae_push_check")
        if not self.test_results:
            missing.append("test_results")
        if not self.governance_results:
            for key in _REQUIRED_GOVERNANCE_KEYS:
                missing.append(f"governance_results.{key}")
        else:
            for key in _REQUIRED_GOVERNANCE_KEYS:
                if key not in self.governance_results:
                    missing.append(f"governance_results.{key}")

        if not self.test_results:
            for key in _REQUIRED_BASE_TEST_RESULT_KEYS:
                missing.append(f"test_results.{key}")
        else:
            for key in _REQUIRED_BASE_TEST_RESULT_KEYS:
                if key not in self.test_results:
                    missing.append(f"test_results.{key}")

        if missing:
            warnings.append(f"Missing trust fields: {', '.join(missing)}")
            return COMPLETENESS_PARTIAL, missing, warnings

        return COMPLETENESS_COMPLETE, [], warnings

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
            "canonical_report_used": self.canonical_report_used,
            "architecture_status": self.architecture_status,
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

        if self.architecture_status:
            lines.append("## PCAE Architecture Status")
            lines.append("")
            arch = self.architecture_status
            # Phase 134E.8 — the "Never manually maintained" authority
            # claim is now conditioned on the generator's own disclosed
            # freshness rather than stated unconditionally: an
            # automatically-derived block can still be incomplete or
            # conflicted, and asserting "canonical" over that is exactly
            # the over-claim this phase repairs.
            freshness = arch.get("freshness", "")
            if freshness == "fresh":
                lines.append(
                    "*Generated automatically from canonical project state. "
                    "Never manually maintained.*"
                )
            elif freshness:
                lines.append(
                    f"*Generated automatically from canonical project state "
                    f"(freshness: {freshness}). Never manually maintained; "
                    f"see Limitations/Conflicts below.*"
                )
            else:
                lines.append(
                    "*Generated automatically from canonical project state. "
                    "Never manually maintained.*"
                )
            lines.append("")

            if arch.get("completed"):
                lines.append("### Completed")
                lines.append("")
                for item in arch["completed"]:
                    lines.append(f"- ✓ {item}")
                lines.append("")

            if arch.get("in_progress"):
                lines.append("### In Progress")
                lines.append("")
                for item in arch["in_progress"]:
                    lines.append(f"- ◐ {item}")
                lines.append("")
            elif not arch.get("current_phase_id"):
                lines.append("### In Progress")
                lines.append("")
                lines.append("- (none — no active governed phase)")
                lines.append("")

            if arch.get("planned"):
                lines.append("### Planned")
                lines.append("")
                for item in arch["planned"]:
                    lines.append(f"- ○ {item}")
                lines.append("")

            runtime_state = arch.get("current_runtime_state", "")
            max_capability = arch.get("current_maximum_capability", "")
            exec_availability = arch.get("execution_availability", "")
            if runtime_state or max_capability or exec_availability:
                lines.append("### Current Runtime State")
                lines.append("")
                if runtime_state:
                    lines.append(f"- **State:** {runtime_state}")
                if max_capability:
                    lines.append(f"- **Maximum Capability:** {max_capability}")
                if exec_availability:
                    lines.append(f"- **Execution Availability:** {exec_availability}")
                lines.append("")

            if arch.get("limitations"):
                lines.append("### Limitations")
                lines.append("")
                for item in arch["limitations"]:
                    lines.append(f"- {item}")
                lines.append("")

            if arch.get("conflicts"):
                lines.append("### Conflicts")
                lines.append("")
                for item in arch["conflicts"]:
                    lines.append(f"- {item}")
                lines.append("")

        if self.governance_results:
            lines.append("## Governance Results")
            lines.append("")
            for key in sorted(self.governance_results):
                val = self.governance_results[key]
                lines.append(f"- **{key}:** {val}")
            lines.append("")

        if self.test_results:
            lines.append("## Test Results")
            lines.append("")
            for key in sorted(self.test_results):
                val = self.test_results[key]
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
        canon_present = bool(self.canonical_report_content) or self.canonical_report_used
        if canon_present or consistency_warnings:
            lines.append("## Report Consistency")
            lines.append("")
            lines.append(f"- **Canonical report:** {'present' if canon_present else 'absent'}")
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
    and promote certified content to latest.md / latest.json.

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

    promotion = promote_artifact(
        artifact_type="phase_report",
        artifact_id=report.phase_id,
        source_state=PromotionArtifactState.CERTIFIED,
        versioned_artifacts={
            md_path: md_content,
            json_path: json_content,
        },
        canonical_artifacts={
            latest_md: md_content,
            latest_json: json_content,
        },
    )
    if not promotion.promoted:
        reasons = "; ".join(d.message for d in promotion.diagnostics)
        raise ValueError(f"Cannot promote phase report: {reasons}")
    report.metadata["promotion_diagnostics"] = [
        {"status": d.status, "message": d.message}
        for d in promotion.diagnostics
    ]

    return {
        "markdown": str(md_path),
        "json": str(json_path),
        "latest_markdown": str(latest_md),
        "latest_json": str(latest_json),
        "promotion_status": "promoted",
    }


def _persist_notification_result(paths: dict[str, str], notification_result: dict[str, Any]) -> None:
    """Patch the already-written report JSON artifact(s) with the final
    ``notification_result``, after the fact.

    Phase 136AY: ``finalize_phase_report()`` must call ``write_phase_
    report()`` *before* dispatching notifications (the dispatched
    Telegram message attaches the just-written report file -- a report
    cannot describe the outcome of its own delivery before it exists on
    disk to be delivered). ``report.notification_result`` is then
    computed afterward and set on the in-memory ``report`` object only,
    which is never written back to ``latest.json``/the timestamped JSON
    -- both persisted artifacts kept whatever placeholder value (usually
    ``{}``) was present at write time, regardless of whether dispatch
    actually succeeded or failed. This left `pcae session bootstrap`'s
    own "surface the last completed phase's own notification dispatch
    outcome" feature unable to ever report anything but "not attempted"
    for a real completed phase, live-reproduced against this
    repository's own 136AY finalization.

    A full re-``write_phase_report()`` call is not safe here: it would
    mint a second, differently-timestamped report artifact and attempt
    to re-promote an artifact ID whose CERTIFIED state has already been
    consumed. Instead this patches only the ``notification_result`` key
    directly on disk. This is safe precisely because
    ``compute_report_digest()`` already explicitly excludes
    ``notification_result`` from the certified content hash (see its own
    docstring: "that post-send diagnostic is intentionally excluded so
    marker bytes equal delivered bytes") -- patching it after the fact
    changes no digested, certified, or delivered content.
    """
    import json as _json

    for key in ("json", "latest_json"):
        path_str = paths.get(key)
        if not path_str:
            continue
        p = Path(path_str)
        if not p.exists():
            continue
        try:
            data = _json.loads(p.read_text(encoding="utf-8"))
        except (OSError, _json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        data["notification_result"] = notification_result
        p.write_text(_json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_quarantined_report(
    report: "PhaseReport", reports_dir: Path, blockers: list[str],
) -> dict[str, str]:
    """Write a BLOCKED phase report to a quarantine path.

    Phase 113X.1 — never touches ``latest.md``/``latest.json`` or the
    normal timestamped filename. Used exactly when
    ``validate_finalization_gate()`` returns blockers, so a report that
    failed phase-identity/trust validation can never silently become the
    canonical "latest" artifact (113X Finding 1). The blocker list is
    persisted inside the quarantined artifact itself, so it remains
    self-describing even without the console output that accompanied it.
    """
    quarantine_dir = reports_dir / "quarantine"
    quarantine_dir.mkdir(parents=True, exist_ok=True)

    # Microseconds plus the candidate digest make every rejected attempt a
    # distinct, immutable audit artifact even under rapid retries.
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    safe_id = _safe_filename(report.phase_id)
    attempt_digest = compute_report_digest(report)[:12]
    base = f"{ts}-{safe_id}-{attempt_digest}.blocked"

    md_path = quarantine_dir / f"{base}.md"
    json_path = quarantine_dir / f"{base}.json"

    data = report.to_dict()
    data["finalization_blockers"] = list(blockers)
    data["report_completeness"] = "blocked"
    json_content = json.dumps(data, indent=2, sort_keys=True)

    md_lines = [
        "# BLOCKED Phase Report",
        "",
        "*This report was refused by the finalization gate and was never*",
        "*written as `latest.md`/`latest.json`. It is not canonical and*",
        "*must not be treated as trusted.*",
        "",
        f"- **Phase ID:** `{report.phase_id}`",
        f"- **Phase Name:** {report.phase_name}",
        f"- **Blocker count:** {len(blockers)}",
        "",
        "## Finalization Blockers",
        "",
    ]
    md_lines.extend(f"- {b}" for b in blockers)
    md_lines.append("")
    md_lines.append("## Report Content (as generated -- not trusted, not canonical)")
    md_lines.append("")
    md_lines.append(report.render_markdown())
    md_content = "\n".join(md_lines)

    quarantine_result = quarantine_artifact(
        artifact_type="phase_report",
        artifact_id=report.phase_id,
        quarantine_artifacts={
            md_path: md_content,
            json_path: json_content,
        },
        blockers=tuple(blockers),
    )

    return {
        "quarantine_markdown": str(md_path),
        "quarantine_json": str(json_path),
        "promotion_status": "quarantined" if not quarantine_result.promoted else "promoted",
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


# ── Notification dispatch idempotency (Phase 113V.N) ─────────────────────────
#
# `finalize_phase_report()` writes the report artifact *before* attempting
# dispatch (see its own docstring), so the persisted report's
# `notification_result` cannot itself serve as an "already sent" marker at
# the moment dispatch is being decided. `pcae task finish --commit` already
# carried a private marker-file workaround for this; the same workaround is
# generalized here into one shared implementation so every finalization path
# (`pcae phase complete`, `pcae task finish --commit`) answers "was this
# phase+commit already dispatched" identically, instead of each caller
# keeping (or, previously, only one caller keeping) its own notion of it.

_NOTIFICATION_MARKER_PATH = Path(".pcae/phase-reports/.last-notified.json")


def read_notification_dispatch_marker(marker_path: Path | None = None) -> dict[str, Any]:
    """Read the shared notification-dispatch idempotency marker.

    Returns ``{}`` if the marker file is absent or unreadable.
    """
    path = marker_path or _NOTIFICATION_MARKER_PATH
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def phase_already_notified(
    phase_id: str,
    commit_hash: str = "",
    marker_path: Path | None = None,
    *,
    report_digest: str = "",
    finalization_snapshot_id: str = "",
    delivery_purpose: str = "ordinary_completion",
) -> bool:
    """True if ``phase_id`` already had a final report dispatched.

    Ordinary terminal completion is a phase-level logical outcome. A later
    bookkeeping/report-repair commit must not manufacture a second ordinary
    completion for the same phase. Corrections and supersessions require a
    distinct, explicitly governed delivery purpose.
    """
    return notification_dispatch_state(
        phase_id,
        marker_path=marker_path,
        report_digest=report_digest,
        finalization_snapshot_id=finalization_snapshot_id,
        delivery_purpose=delivery_purpose,
    ) == "already_dispatched"


def notification_dispatch_state(
    phase_id: str,
    *,
    marker_path: Path | None = None,
    report_digest: str = "",
    finalization_snapshot_id: str = "",
    delivery_purpose: str = "ordinary_completion",
) -> str:
    """Classify one logical delivery against the durable marker.

    Returns ``not_dispatched``, ``already_dispatched``, or
    ``payload_conflict``.  Digest/snapshot comparison is fail-closed whenever
    both the stored and proposed identities are available.  Legacy unbound
    markers remain duplicates (their historical payload cannot be recovered
    safely).  Non-ordinary purposes are distinct identities and never consume
    or overwrite the ordinary-completion identity implicitly.
    """
    marker = read_notification_dispatch_marker(marker_path)
    deliveries = marker.get("deliveries", {})
    purpose_marker = deliveries.get(delivery_purpose) if isinstance(deliveries, dict) else None
    if isinstance(purpose_marker, dict):
        candidate = purpose_marker
    elif delivery_purpose == "ordinary_completion":
        candidate = marker
    else:
        return "not_dispatched"
    if candidate.get("phase_id") != phase_id:
        return "not_dispatched"
    marker_purpose = candidate.get("delivery_purpose", "ordinary_completion")
    if marker_purpose != delivery_purpose:
        return "not_dispatched"
    stored_report_digest = str(candidate.get("report_digest", ""))
    stored_snapshot_id = str(candidate.get("finalization_snapshot_id", ""))
    if stored_report_digest and report_digest and stored_report_digest != report_digest:
        return "payload_conflict"
    if stored_snapshot_id and finalization_snapshot_id and stored_snapshot_id != finalization_snapshot_id:
        return "payload_conflict"
    return "already_dispatched"


def write_notification_dispatch_marker(
    phase_id: str,
    commit_hash: str = "",
    marker_path: Path | None = None,
    *,
    report_digest: str = "",
    finalization_snapshot_id: str = "",
    delivery_purpose: str = "ordinary_completion",
) -> None:
    """Persist the shared notification-dispatch idempotency marker.

    Call only after a dispatch attempt actually succeeded.
    """
    path = marker_path or _NOTIFICATION_MARKER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "phase_id": phase_id,
        "commit": commit_hash[:8] if commit_hash else "",
        "report_digest": report_digest,
        "finalization_snapshot_id": finalization_snapshot_id,
        "delivery_purpose": delivery_purpose,
    }
    existing = read_notification_dispatch_marker(path)
    deliveries = existing.get("deliveries", {})
    if not isinstance(deliveries, dict):
        deliveries = {}
    # Upgrade a legacy ordinary record into the purpose map before adding a
    # correction/supersession, preserving historical ordinary identity.
    if existing.get("phase_id") and "ordinary_completion" not in deliveries:
        legacy = {key: existing.get(key, "") for key in entry}
        legacy["delivery_purpose"] = existing.get(
            "delivery_purpose", "ordinary_completion"
        )
        deliveries[legacy["delivery_purpose"]] = legacy
    deliveries[delivery_purpose] = entry
    payload = dict(existing)
    payload["deliveries"] = deliveries
    if delivery_purpose == "ordinary_completion" or not payload.get("phase_id"):
        payload.update(entry)
    path.write_text(json.dumps(payload))


def compute_report_digest(report: "PhaseReport") -> str:
    """Digest the exact certified Markdown payload used for delivery.

    ``finalize_phase_report`` records physical attempt outcome on the mutable
    in-memory report *after* constructing the event. That post-send diagnostic
    is intentionally excluded so marker bytes equal delivered bytes and an
    unchanged retry remains the same logical payload.
    """
    import copy
    certified = copy.deepcopy(report)
    certified.notification_result = {}
    return hashlib.sha256(certified.render_markdown().encode("utf-8")).hexdigest()


def compute_finalization_snapshot_id(report: "PhaseReport") -> str:
    """Return a stable identity for the sealed semantic finalization facts."""
    data = report.to_dict()
    for key in (
        "created_at", "notification_result", "report_completeness",
        "missing_trust_fields", "trust_warnings", "canonical_report_used",
    ):
        data.pop(key, None)
    metadata = data.get("metadata")
    if isinstance(metadata, dict):
        metadata.pop("promotion_diagnostics", None)
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
    title_phase_id = _extract_canonical_title_phase_id(content)
    if title_phase_id and phase_id:
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
    title_phase_id = _extract_canonical_title_phase_id(content)
    if current_phase_id and title_phase_id:
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

    # ── 5. Phase 94T.1: Summary-to-structured next-phase mismatch ────────
    summary = report.summary
    if summary and report.recommended_next_phase:
        # Extract next phase from summary text (same pattern as _derive_next_phase)
        summary_next = None
        # Phase 137I.1V — these two patterns were missed by the 137I.1
        # regex-truncation repair applied to the sibling patterns at
        # lines ~1234/1249/1313/1626/2101 (and push.py). `(?:\.[\d]+)*`
        # dropped a trailing letter after a dotted digit segment, so a
        # summary mentioning "Recommended next phase: 137I.1V — ..." parsed
        # as "137I.1" while the structured field correctly parsed as
        # "137I.1V" — a false mismatch that downgrades a fully legitimate
        # report to `partial` and adds the non-push-state
        # `metadata_consistency` field to `missing_trust_fields`, which
        # also defeats the 137I.1 pending-report escape (`blockers_are_
        # push_state_only` correctly refuses to treat it as push-only).
        # 137T: label location stays local; ID recognition delegates to
        # the canonical parser (CPIPC-001, CPIPC-REQ-018) via
        # ``_leading_phase_token`` -- a single shared helper replacing
        # this file's own several independently-drifting copies of the
        # same grammar fragment.
        for label_pat in [r'Next(?:\s+phase)?[:\s]+', r'Recommended\s+next\s+phase[:\s]+']:
            lm = re.search(label_pat, summary, re.IGNORECASE)
            if lm is None:
                continue
            token = _leading_phase_token(summary[lm.end():])
            if token is not None:
                summary_next = token
                break
        if summary_next:
            structured_phase = _leading_phase_token(report.recommended_next_phase)
            if structured_phase:
                if summary_next != structured_phase:
                    mismatches.append(
                        f"next_phase: summary={summary_next} structured={structured_phase}"
                    )

    # ── 6. Phase 94T.1: Backward-pointing recommended next phase ────────
    if report.phase_id and report.recommended_next_phase:
        current = report.phase_id
        # 137T: ID recognition delegates to the canonical parser
        # (CPIPC-001), which handles arbitrary subphase depth and
        # trailing letters (e.g. "137I.1V") correctly by construction.
        next_num = _leading_phase_token(report.recommended_next_phase)
        if next_num is not None:
            # If next phase number equals current or points backward.
            # Phase 113X.3 — is_phase_id_backward() is branch-aware:
            # naive lexicographic comparison ("113D" < "113X.2") wrongly
            # flagged a valid transition off the "X" exceptional branch
            # back to the lettered mainline as "backward."
            if next_num == current:
                mismatches.append(
                    f"recommended_next_phase={next_num} points to itself (current={current})"
                )
            elif is_phase_id_backward(next_num, current):
                mismatches.append(
                    f"recommended_next_phase={next_num} points backward from {current}"
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


# Phase 149O.1R (B-149O.1R-1 repair) — boundary-safe candidate span for
# evidence-phase-ID extraction. Unlike `phase_id._TOKEN_CANDIDATE_RE`
# (which deliberately has no boundary anchors, appropriate for its own
# "locate a span, let `parse` judge it" contract at call sites that
# already operate on a single known field), this extractor scans
# arbitrary free prose where an unanchored candidate could be pulled out
# of the middle of an unrelated alphanumeric run (e.g. a hex digest) --
# so both boundaries are required here specifically. The dotted-segment
# group is unbounded (`*`, not a single `?`), so multi-component IDs
# (`149O.1H.1`, `149O.1H.1R`) are captured whole rather than truncated
# to their first two components. Acceptance is never decided here --
# every candidate is still handed to `phase_id.parse` (the sole grammar
# authority, CPIPC-REQ-018), exactly as `phase_id.scan_tokens` does.
_EVIDENCE_PHASE_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])[0-9]+[A-Za-z]+(?:\.[0-9A-Za-z]+)*(?![A-Za-z0-9])"
)


def _extract_evidence_phase_ids(text: str) -> list[canonical_phase_id.PhaseId]:
    """Boundary-safe, arbitrary-depth phase-ID tokens found in free
    ``text``, each independently accepted by the canonical grammar
    (`phase_id.parse`) -- never a second, competing acceptance rule."""
    tokens: list[canonical_phase_id.PhaseId] = []
    for candidate in _EVIDENCE_PHASE_TOKEN_RE.findall(text or ""):
        try:
            tokens.append(canonical_phase_id.parse(candidate))
        except canonical_phase_id.PhaseIdError:
            continue
    return tokens


def validate_internal_report_coherence(report: PhaseReport) -> list[str]:
    """Return deterministic cross-section contradictions in a terminal report."""
    issues: list[str] = []
    phase_id = report.phase_id.strip()
    no_go = "\n".join(str(item) for item in report.explicit_no_go_confirmations)

    if report.status == "completed" and phase_id:
        denied = re.search(
            rf"\bNo\s+(?:Phase\s+)?{re.escape(phase_id)}\s+(?:work\s+)?"
            rf"(?:began|occurred|was\s+implemented)\b",
            no_go,
            re.IGNORECASE,
        )
        if denied:
            issues.append(f"No-Go evidence denies that completed phase {phase_id} began")

    # Incident-bounded deterministic legacy-prose check: when a No-Go item
    # explicitly says a named capability/work item did not occur or was not
    # implemented, the summary cannot claim that same normalized phrase.
    summary_lower = re.sub(r"\s+", " ", report.summary.lower())
    for denied_work in re.findall(
        r"\bNo\s+(.+?)\s+(?:occurred|was\s+implemented)\b",
        no_go,
        re.IGNORECASE,
    ):
        phrase = re.sub(r"\s+", " ", denied_work.strip().lower())
        if len(phrase) >= 4 and phrase in summary_lower:
            issues.append(
                f"summary claims work explicitly denied by No-Go evidence: {denied_work.strip()}"
            )

    # 137T: ID recognition delegates to the canonical parser (CPIPC-001,
    # CPIPC-REQ-018), which normalizes to uppercase by construction
    # (CPIPC-REQ-014/033) -- the 134E.9V case-normalization this check
    # needed to hand-apply is now automatic.
    next_token = _leading_phase_token(report.recommended_next_phase)
    if (
        report.status == "completed"
        and next_token is not None
        and next_token == phase_id.upper()
    ):
        issues.append(f"completed phase recommends itself ({phase_id})")

    # Phase 149O.1R (B-149O.1R-1 repair) — evidence-phase-ID extraction now
    # uses the single canonical parser (`phase_id.parse`, CPIPC-REQ-018)
    # for both extraction boundaries and acceptance, and compares by
    # structural identity (`phase_id.equals`/`same_series`) instead of a
    # dot-stripped string. The previous hand-rolled regex's dotted-segment
    # group could match at most once, so a three-or-more-component phase
    # ID (e.g. `149O.1H.1`, `149O.1H.1R`) could never be recognized as its
    # own evidence -- it was silently truncated to its first two
    # components before comparison, producing a false coherence failure
    # for every such phase regardless of how its evidence was worded.
    test_text = "\n".join(f"{key}: {value}" for key, value in report.test_results.items())
    evidence_tokens = _extract_evidence_phase_ids(test_text)
    # 137T: "same series" is a first-class canonical predicate
    # (CPIPC-REQ-043) -- delegates to it instead of an ad hoc
    # string-prefix comparison.
    current_pid = canonical_phase_id.match_leading_token(phase_id)
    # Phase 134E.9 — a verification/regression phase legitimately re-runs
    # another phase's tests as inherited baseline evidence; an explicit
    # governed classification (never inferred from prose) is the only way
    # to suppress this check, so silent omission still fails closed.
    test_evidence_classification = str(
        (report.metadata or {}).get("test_evidence_classification", "")
    ).strip()
    if (
        evidence_tokens
        and current_pid is not None
        and not any(canonical_phase_id.equals(token, current_pid) for token in evidence_tokens)
        and test_evidence_classification != "inherited_regression"
    ):
        same_series = sorted(
            {
                token.normalized_text
                for token in evidence_tokens
                if canonical_phase_id.same_series(token, current_pid)
            }
        )
        if same_series:
            issues.append(
                "test evidence is linked only to other phase identities: "
                + ", ".join(same_series)
            )

    metadata_phase = str((report.metadata or {}).get("phase_id", "")).strip()
    if metadata_phase and metadata_phase != phase_id:
        issues.append(
            f"report identity {phase_id} disagrees with snapshot metadata {metadata_phase}"
        )
    source_revision = str((report.metadata or {}).get("source_revision", "")).strip()
    architecture_revision = str(report.architecture_status.get("repository_revision", "")).strip()
    if source_revision and architecture_revision and source_revision != architecture_revision:
        issues.append(
            "report source revision disagrees with Architecture Status repository revision: "
            f"{source_revision} vs {architecture_revision}"
        )
    return issues


def _apply_internal_report_coherence(report: PhaseReport) -> None:
    issues = validate_internal_report_coherence(report)
    if not issues:
        return
    report.trust_warnings.append("internal report evidence is contradictory")
    report.trust_warnings.extend(f"  Coherence: {issue}" for issue in issues)
    report.report_completeness = COMPLETENESS_INCOMPLETE
    if "internal_evidence_coherence" not in report.missing_trust_fields:
        report.missing_trust_fields.append("internal_evidence_coherence")


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 134E.9 — Report Consistency / Derived Correctness Validation
# ═══════════════════════════════════════════════════════════════════════════════
#
# The 134D implementation plan's authoritative scope for 134E.9 is "a
# reusable validation manifest comparing any derived view/rendering back
# to its source canonical record, checking for invented content, silent
# omission, or unauthorized strengthening of uncertainty/classification"
# (134B §17), wired fail-closed into the existing finalization gate --
# not a second competing gate, not a new evidence pipeline. In this
# repository's currently *active* production lifecycle (the new
# Canonical Engineering Evidence / Evidence Extraction / Derived Views
# chain from 134E.1-134E.7 remains disconnected — confirmed inactive by
# every 134E.xV so far), the one "source canonical record" that is
# actually live is the sealed finalization snapshot 134E.8.1/134E.8V
# already established: ``report.architecture_status`` is the certified,
# immutable Architecture Status snapshot bound into the report at
# construction time (``finalize_phase_report()``), never re-read after.
#
# ``validate_derived_correctness()`` is the reusable manifest that checks
# the *rest* of the report's derived claims against that one sealed
# snapshot -- gaps confirmed absent from both ``validate_internal_report_
# coherence()`` and ``validate_finalization_gate()`` by direct source
# inspection before this phase began: neither function ever read
# ``architecture_status["freshness"]`` or ``["conflicts"]``, so a report
# could be promoted and dispatched even while carrying a `stale`/
# `invalid` or conflicted Architecture Status snapshot; and only
# self-recommendation (`recommended_next_phase == phase_id`) was
# rejected, not a recommendation pointing at a *different* already-
# completed phase (e.g. a stale-132F-style regression).

# The one runtime tuple every governed phase in this repository has ever
# certified (Phase 110A's Runtime State Model — Observed is the
# non-executing ceiling). Not a general-purpose runtime-state registry;
# extending this set is itself a governed decision, never an inferred one.
ALLOWED_RUNTIME_TUPLES: frozenset[tuple[str, str, str]] = frozenset({
    ("Observed", "observe", "unavailable"),
})

# Phase 134E.9.1 — confirmed by direct inspection that `fast_green` (a
# _REQUIRED_BASE_TEST_RESULT_KEYS mandatory key) was checked only for
# *presence*, never for whether its free-text value actually reports a
# failure: a report could declare
# ``test_results["fast_green"] = "0 passed, 4391 failed"`` and still be
# marked complete. Root-caused by the 134E.9 report's own "4389/4390,
# one pre-existing unrelated failure" claim, which -- while textually
# true of that run -- was accepted as complete without this codebase
# ever verifying the claimed failure was actually non-blocking. No
# escape hatch is provided: unlike the recommended-next-phase or
# test-evidence-linkage checks above, a governed classification cannot
# make a real fast_green failure retroactively not have happened.
#
# Phase 134E.9V — independent verification found the original
# proximity-based regex (``(\d+)[^\d]{0,40}?fail``, applied to
# ``str(value)`` for *any* type) unsound against non-natural-language
# representations, proven by direct adversarial probing before any test
# was written: ``{"passed": 0, "failed": 5}`` (a real 5-failure result)
# matched on the unrelated leading ``0`` from ``"passed": 0`` and
# reported **zero** failures -- a false negative that would have let a
# genuinely failing suite reach `complete`. Conversely
# ``{"passed": 4390, "failed": 0}`` (a clean pass) matched forward onto
# ``"failed"`` and reported 4390 failures -- a false positive. Bare
# ``True``/``False``/``None``/negative/bare-int values passed through
# with no finding at all, silently. ``_fast_green_failure_signal()``
# replaces the single regex with type-aware, structural interpretation:
# a ``Mapping`` is read by its own ``failed``/``failures`` key (never by
# textual proximity); a ``bool`` (checked before ``int`` -- ``bool`` is
# an ``int`` subclass in Python) or any other non-``str``/``Mapping``/
# ``int`` type is malformed; a bare ``int`` is ambiguous (no unit) and
# also malformed; only a ``str`` is interpreted by natural-language
# pattern (failure count, or an explicit "N passed" clean-pass signal).
# Anything that cannot be confidently interpreted fails closed as
# malformed -- "unknown or unresolved values fail closed" is now a
# structural property, not a byproduct of what the regex happened to miss.
_FAST_GREEN_FAILURE_RE = re.compile(r'(\d+)[^\d]{0,40}?fail', re.IGNORECASE)
_FAST_GREEN_PASSED_RE = re.compile(r'\d+\s*passed', re.IGNORECASE)
# This repository's other well-established convention alongside "N
# passed"/"N failed" prose: a bare "<passed>/<total>" fraction (e.g.
# "4390/4390", used throughout PROJECT_STATUS.md and every phase report
# preceding this one). Recognized only when no explicit failure-count
# language matched first; failures are the implied ``total - passed``.
_FAST_GREEN_FRACTION_RE = re.compile(r'(\d+)\s*/\s*(\d+)')
_FAST_GREEN_FAILURE_KEYS: tuple[str, ...] = ("failed", "failures", "fail_count", "num_failed")


def _fast_green_failure_signal(value: Any) -> tuple[int | None, bool]:
    """Interpret one ``test_results["fast_green"]`` value.

    Returns ``(failure_count, malformed)``. ``malformed=True`` means the
    value could not be confidently interpreted as either a clean pass or
    an explicit failure count, and must be treated as a failure (fail
    closed) by the caller regardless of ``failure_count`` (always
    ``None`` when malformed). ``failure_count`` is the confidently
    resolved nonzero-or-zero failure count when ``malformed=False``.
    """
    if isinstance(value, bool):
        # bool is an int subclass -- checked first so True/False are
        # never silently treated as 1/0.
        return None, True
    if isinstance(value, Mapping):
        for key in _FAST_GREEN_FAILURE_KEYS:
            if key in value:
                raw = value[key]
                if isinstance(raw, bool) or not isinstance(raw, int):
                    return None, True
                return raw, False
        return None, True
    if isinstance(value, int):
        # A bare int has no unit -- could mean "N passed" or "N failed"
        # with equal plausibility; never guess.
        return None, True
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None, False
        fail_match = _FAST_GREEN_FAILURE_RE.search(text)
        if fail_match:
            return int(fail_match.group(1)), False
        if _FAST_GREEN_PASSED_RE.search(text):
            return 0, False
        frac_match = _FAST_GREEN_FRACTION_RE.search(text)
        if frac_match:
            passed_n, total_n = int(frac_match.group(1)), int(frac_match.group(2))
            if total_n >= passed_n:
                return total_n - passed_n, False
            return None, True  # nonsensical fraction (passed > total)
        return None, True
    return None, True


def validate_derived_correctness(report: PhaseReport) -> list[str]:
    """Validate a terminal report's derived claims against its own sealed
    Architecture Status snapshot (``report.architecture_status``) --
    never against a freshly re-read/regenerated snapshot, so a
    post-certification change can never silently "fix" a report that
    already failed. Returns a list of human-readable issues; empty means
    the derived claims checked here are internally correct. Never raises
    on a malformed/absent snapshot -- an empty snapshot simply yields no
    findings from checks that require it (already-caught elsewhere as a
    missing-trust-field condition).
    """
    issues: list[str] = []
    arch = report.architecture_status or {}
    if not isinstance(arch, dict):
        return issues
    phase_id = report.phase_id.strip()
    md = report.metadata or {}
    from pcae.core.architecture_status import parse_phase_id as _parse_arch_phase_id
    canonical_phase_identity = _parse_arch_phase_id(phase_id) is not None
    completed_ids_upper = {
        str(pid).upper() for pid in (arch.get("completed_phase_ids") or [])
    }
    planned_ids_upper = {
        str(pid).upper() for pid in (arch.get("planned_phase_ids") or [])
    }
    current_id = str(arch.get("current_phase_id", "")).strip().upper()
    in_progress = [str(item) for item in (arch.get("in_progress") or [])]
    own_in_progress = current_id == phase_id.upper() or any(
        re.search(rf"\({re.escape(phase_id)}\)\s*$", item, re.IGNORECASE)
        for item in in_progress
    )

    if canonical_phase_identity and report.status == "completed":
        if own_in_progress:
            issues.append(
                f"completed report phase {phase_id!r} remains current/in-progress "
                "in the sealed Architecture Status snapshot"
            )
        projected_transition = str(
            (arch.get("source_provenance") or {}).get("lifecycle_projection", "")
        ).lower() == f"completed:{phase_id}".lower()
        if projected_transition and phase_id.upper() not in completed_ids_upper:
            issues.append(
                f"completed report phase {phase_id!r} is absent from sealed "
                "Architecture Status completed_phase_ids"
            )
    elif canonical_phase_identity and phase_id.upper() in completed_ids_upper:
        issues.append(
            f"non-completed report phase {phase_id!r} is claimed completed by "
            "the sealed Architecture Status snapshot"
        )
    if canonical_phase_identity and phase_id.upper() in completed_ids_upper and own_in_progress:
        issues.append(f"phase {phase_id!r} appears under both Completed and In Progress")
    if canonical_phase_identity and phase_id.upper() in planned_ids_upper and own_in_progress:
        issues.append(f"phase {phase_id!r} appears under both In Progress and Planned")
    for item in in_progress:
        if re.search(r"\(completed\)", item, re.IGNORECASE):
            issues.append(f"In Progress entry claims completed state: {item!r}")

    # ── Mandatory test evidence value, not just presence: a nonzero
    # failure count reported in test_results["fast_green"] must block,
    # regardless of how the failure is narrated (e.g. "pre-existing",
    # "unrelated") -- that narration is not itself verified evidence.
    # Absence of the key is a separate, pre-existing trust-completeness
    # concern (_REQUIRED_BASE_TEST_RESULT_KEYS) -- this check only
    # interprets a key that is actually present.
    if isinstance(report.test_results, dict) and "fast_green" in report.test_results:
        raw_fast_green = report.test_results["fast_green"]
        # Phase 149O.20L.7O.2R -- structured attribution-aware path,
        # additive to (never replacing) the scalar path below. Selected
        # only when the value is a dict carrying the structured schema
        # marker; any other dict shape (including today's scalar mapping
        # forms) falls through to _fast_green_failure_signal() exactly as
        # before -- byte-for-byte unchanged scalar behavior (2Q Section 8,
        # 2Q.1 Section 16).
        from pcae.core.fast_green_attribution import (
            is_structured_fast_green,
            resolve_repo_root,
            validate_structured_fast_green,
        )
        if is_structured_fast_green(raw_fast_green):
            repo_root = resolve_repo_root(str(Path.cwd()))
            structured_issues = validate_structured_fast_green(
                raw_fast_green,
                repo_root=repo_root,
                phase_id=phase_id,
                pushed_status=report.pushed_status,
            )
            issues.extend(structured_issues)
        else:
            fail_count, malformed = _fast_green_failure_signal(raw_fast_green)
            if malformed:
                issues.append(
                    f"test_results['fast_green'] value {raw_fast_green!r} is "
                    f"malformed or unresolved -- cannot certify complete"
                )
            elif fail_count:
                issues.append(
                    f"test_results['fast_green'] reports {fail_count} "
                    f"failure(s) ({raw_fast_green!r}) -- a failing fast_green "
                    f"result cannot be certified complete"
                )

    # ── Architecture Status freshness/conflicts must not be silently
    # ignored: a "fresh" classification is not a substitute for internal
    # coherence, and a "stale"/"invalid" classification must itself
    # block -- neither was checked by any existing gate before 134E.9.
    freshness = arch.get("freshness", "")
    if freshness in ("stale", "invalid"):
        issues.append(
            f"Architecture Status snapshot is {freshness!r} -- cannot "
            f"certify a report on unresolved/conflicted project state"
        )
    conflicts = arch.get("conflicts") or []
    if conflicts:
        issues.append(
            "Architecture Status snapshot carries unresolved conflicts: "
            + "; ".join(str(c) for c in conflicts)
        )

    # ── Recommended next phase must not already be completed (general
    # case -- self-recommendation is covered separately by
    # validate_internal_report_coherence; this covers recommending a
    # *different* already-completed phase, the exact stale-132F defect
    # shape). An explicit governed classification is the only escape.
    # 137T: ID recognition delegates to the canonical parser (CPIPC-001,
    # CPIPC-REQ-018); comparison is case-insensitive by construction
    # while the disclosed message quotes the report's original text
    # verbatim (never silently rewritten).
    next_pid = canonical_phase_id.match_leading_token(report.recommended_next_phase)
    next_classification = str(md.get("next_phase_classification", "")).strip()
    if (
        next_pid is not None
        and next_pid.normalized_text in completed_ids_upper
        and next_classification != "corrective_recovery_transition"
    ):
        issues.append(
            f"recommended_next_phase {next_pid.source_text!r} is already "
            f"completed per the sealed Architecture Status snapshot"
        )

    # ── Regression guard: the exact defect 134E.8 repaired must never
    # resurface as a planned claim in any certified report.
    if "132F" in (arch.get("planned_phase_ids") or []):
        issues.append(
            "Architecture Status snapshot plans already-completed phase "
            "'132F' -- the stale-132F defect has resurfaced"
        )

    # ── Runtime tuple validity: the three runtime fields, when all
    # present, must form one of this repository's governed-allowed
    # tuples -- never an ungoverned combination.
    runtime_state = arch.get("current_runtime_state", "")
    max_capability = arch.get("current_maximum_capability", "")
    exec_availability = arch.get("execution_availability", "")
    if runtime_state and max_capability and exec_availability:
        tup = (runtime_state, max_capability, exec_availability)
        if tup not in ALLOWED_RUNTIME_TUPLES:
            issues.append(
                f"runtime tuple {tup!r} is not a governed-allowed "
                f"(state, capability, execution_availability) combination"
            )

    # ── Current-phase coherence: the sealed snapshot's own current phase
    # identity, when present, must not name a *different* phase family
    # than this report -- sub-phases of the same report are allowed to
    # complete independently (matches validate_phase_identity's existing
    # sub-phase allowance).
    snapshot_current = str(arch.get("current_phase_id", "")).strip()
    if snapshot_current and phase_id and not phase_id.startswith("."):
        # 137T: "same series+branch family" is the first-class canonical
        # ``same_branch`` predicate (CPIPC-REQ-043), delegating ID
        # recognition to the canonical parser (CPIPC-001, CPIPC-REQ-018)
        # instead of a locally hand-rolled regex + ad hoc string compare.
        report_pid = canonical_phase_id.match_leading_token(phase_id)
        snapshot_pid = canonical_phase_id.match_leading_token(snapshot_current)
        is_sub_phase = "." in phase_id
        if (
            not is_sub_phase
            and report_pid is not None
            and snapshot_pid is not None
            and not canonical_phase_id.same_branch(report_pid, snapshot_pid)
            and snapshot_current != phase_id
        ):
            issues.append(
                f"sealed Architecture Status current_phase_id "
                f"{snapshot_current!r} disagrees with report phase_id "
                f"{phase_id!r}"
            )

    return issues


def _apply_derived_correctness(report: PhaseReport) -> None:
    issues = validate_derived_correctness(report)
    if not issues:
        return
    report.trust_warnings.append("derived correctness validation failed")
    report.trust_warnings.extend(f"  DerivedCorrectness: {issue}" for issue in issues)
    report.report_completeness = COMPLETENESS_INCOMPLETE
    if "derived_correctness" not in report.missing_trust_fields:
        report.missing_trust_fields.append("derived_correctness")


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
    _apply_internal_report_coherence(report)
    _apply_derived_correctness(report)


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 95M.1 — Finalization gate
# ═══════════════════════════════════════════════════════════════════════════════

_MIN_NO_GO_COUNT = 11
_MIN_NO_GO_PREFIX = "No "

# Phase 137R — branch-aware parsing and comparison are now owned
# exclusively by the canonical parser (``pcae.core.phase_id``,
# CPIPC-001 §6, §10). This module no longer defines its own phase-ID
# grammar or comparison tuple.


def is_phase_id_backward(next_id: str, current_id: str) -> bool:
    """Branch-aware replacement for naive lexicographic phase-ID
    ordering (Phase 113X.3, repairing a bug 113X.2 exposed).

    Two phase IDs are only meaningfully orderable when they share the
    same series *and* are on the same kind of branch. The plain
    lettered mainline (``113A``, ``113B``, ``113C``, ``113D``, ...) is
    one real, ordered sequence -- ``"113B"`` genuinely precedes
    ``"113D"``. The ``"X"`` exceptional branch (``113X.1``, ``113X.2``,
    ...) is a separate, self-contained governance-repair excursion with
    its own sub-numbering, not a point in that lettered sequence.

    Naive string/lexicographic comparison (``"113D" < "113X.2"``, since
    ``'D' < 'X'``) wrongly treats a transition *between* these two
    kinds of branch (e.g. returning from the ``113X.N`` excursion back
    to the ``113D`` mainline) as "pointing backward" -- when the two
    IDs simply aren't comparable at all.

    Returns ``True`` only when both IDs share the same series, are
    both on the mainline or both on the ``"X"`` branch, and ``next_id``
    is a genuinely earlier (branch letter, subphase) position than
    ``current_id``. Returns ``False`` (never "backward") whenever the
    two IDs are not comparable -- different series, different kind of
    branch, or either fails to parse -- rather than guessing.
    """
    try:
        next_parsed = canonical_phase_id.parse(next_id)
        current_parsed = canonical_phase_id.parse(current_id)
    except canonical_phase_id.PhaseIdError:
        return False
    return canonical_phase_id.compare(next_parsed, current_parsed) == "less"


@dataclass(frozen=True)
class CanonicalPhaseIdentity:
    """The resolved, single-source phase identity for a finalization
    (Phase 113X.4). ``phase_id``/``phase_name`` always originate from
    the same ``source`` -- never mixed across sources."""

    phase_id: str
    phase_name: str
    source: str  # one of _CANONICAL_IDENTITY_SOURCES


_CANONICAL_IDENTITY_SOURCE_CLI = "cli_argument"
_CANONICAL_IDENTITY_SOURCE_TASK = "active_task_contract"
_CANONICAL_IDENTITY_SOURCE_METADATA = "phase_completion_metadata"
_CANONICAL_IDENTITY_SOURCE_LIFECYCLE = "active_lifecycle_context"

_CANONICAL_IDENTITY_SOURCES: frozenset[str] = frozenset({
    _CANONICAL_IDENTITY_SOURCE_TASK,
    _CANONICAL_IDENTITY_SOURCE_METADATA,
    _CANONICAL_IDENTITY_SOURCE_LIFECYCLE,
    _CANONICAL_IDENTITY_SOURCE_CLI,
})

_LEADING_PHASE_PREFIX_RE = re.compile(r'^\s*Phase\s+')
_LEADING_PHASE_SEPARATOR_RE = re.compile(r'^\s*[:—–-]\s*(.+)$')


def _parse_leading_phase_reference(text: str) -> tuple[str, str] | None:
    """Extract ``(phase_id, phase_name)`` from a string that *starts*
    with ``"Phase <id>: <name>"`` or ``"Phase <id> — <name>"`` (Phase
    113X.4). Anchored at the beginning of the string on purpose: this
    is what makes it structurally safe against the exact forensic
    defect free-text ``--summary`` had (a phase reference anywhere in
    a sentence, e.g. "extends Phase 113B", being mistaken for the
    report's own identity) -- a phase mentioned mid-prose never matches
    here, only a leading, structured "Phase X: ..." declaration does.

    137T: the "Phase " prefix and the ":"/"—" separator locations stay
    local; the Phase ID grammar itself delegates to the canonical
    parser (CPIPC-001, CPIPC-REQ-018).

    Returns ``None`` if ``text`` doesn't start with such a reference.
    """
    stripped = text.strip()
    prefix_m = _LEADING_PHASE_PREFIX_RE.match(stripped)
    if not prefix_m:
        return None
    after_prefix = stripped[prefix_m.end():]
    leading = canonical_phase_id.match_leading_token(after_prefix)
    if leading is None:
        return None
    remainder = after_prefix.strip()[len(leading.source_text):]
    sep_m = _LEADING_PHASE_SEPARATOR_RE.match(remainder)
    if not sep_m:
        return None
    phase_id = leading.normalized_text
    name = sep_m.group(1).strip()
    # Strip a trailing "(completed)."/"(not started)." style status marker.
    name = re.sub(r'\s*\([^()]*\)\.?\s*$', '', name).strip()
    name = name.rstrip('.').strip()
    if not name:
        return None
    return phase_id, name


def resolve_canonical_phase_identity(
    *,
    active_task_title: str | None = None,
    metadata: dict[str, Any] | None = None,
    lifecycle_current_phase_line: str | None = None,
    cli_phase_id: str | None = None,
    cli_phase_name: str | None = None,
) -> CanonicalPhaseIdentity | None:
    """Single canonical phase-identity resolution point for the
    ``pcae phase complete`` finalization path (Phase 113X.4).

    Repairs 113X audit Finding 3 in full: the forensic review proved
    that deriving phase identity by regex over free-text ``--summary``
    is fundamentally unsound -- a summary mentioning a previous phase
    for context (e.g. "extends Phase 113B") could become the report's
    own identity. 113X.2 only detected a *disagreement* between that
    regex-derived value and metadata; this repairs the derivation
    itself. Free-text summary is never consulted here at all -- it is
    not one of the parameters.

    Tries each authoritative source in a fixed precedence order,
    returning the first that resolves. Never mixes fields across
    sources -- ``phase_id`` and ``phase_name`` always come from the
    same winning source:

    1. ``active_task_title`` -- the active task contract's own
       ``Title`` field (e.g. ``"Phase 113X.4: Canonical Phase Identity
       Repair"``), when it starts with a leading "Phase X: ..."
       reference. The task contract is the governed record of what is
       actively being worked on.
    2. ``metadata`` -- ``.pcae/phase-completion-metadata.json``'s own
       structured ``phase_id``/``phase_name`` fields. Never parsed by
       regex; read directly as declared.
    3. ``lifecycle_current_phase_line`` -- PROJECT_STATUS.md's
       "## Current Phase" section text, but *only* when it is not
       already marked ``(completed)`` -- i.e. only when it genuinely
       describes an in-progress phase, not the previously-finalized one.
    4. ``cli_phase_id``/``cli_phase_name`` -- an explicit CLI argument,
       the last-resort override for bootstrapping or when no other
       governed source exists yet.

    Returns ``None`` if no source resolves -- callers must fail closed
    (refuse finalization; never fabricate ``"unknown"`` or fall back to
    regex-derived values).
    """
    if active_task_title:
        parsed = _parse_leading_phase_reference(active_task_title)
        if parsed:
            phase_id, phase_name = parsed
            return CanonicalPhaseIdentity(phase_id, phase_name, _CANONICAL_IDENTITY_SOURCE_TASK)

    meta = metadata or {}
    meta_phase_id = str(meta.get("phase_id", "")).strip()
    if meta_phase_id:
        meta_phase_name = str(meta.get("phase_name") or meta.get("phase_title") or meta_phase_id).strip()
        return CanonicalPhaseIdentity(meta_phase_id, meta_phase_name, _CANONICAL_IDENTITY_SOURCE_METADATA)

    if lifecycle_current_phase_line and "(completed)" not in lifecycle_current_phase_line.lower():
        parsed = _parse_leading_phase_reference(lifecycle_current_phase_line)
        if parsed:
            phase_id, phase_name = parsed
            return CanonicalPhaseIdentity(phase_id, phase_name, _CANONICAL_IDENTITY_SOURCE_LIFECYCLE)

    if cli_phase_id:
        return CanonicalPhaseIdentity(
            cli_phase_id, cli_phase_name or cli_phase_id, _CANONICAL_IDENTITY_SOURCE_CLI,
        )

    return None


# Phase 137R — the phase-ID grammar itself is owned exclusively by the
# canonical parser (``pcae.core.phase_id``, CPIPC-001 §6). Only the
# "Phase " textual prefix locating a candidate remains here; the
# candidate substring is handed to the canonical parser's anchored
# token match, never re-parsed locally.
_COMMIT_SUBJECT_PHASE_PREFIX_RE = re.compile(r"Phase\s+", re.IGNORECASE)


def _find_commit_subject_phase_token(subject: str) -> "canonical_phase_id.PhaseId | None":
    prefix_match = _COMMIT_SUBJECT_PHASE_PREFIX_RE.search(subject)
    if prefix_match is None:
        return None
    return canonical_phase_id.match_leading_token(subject[prefix_match.end():])


def detect_cross_phase_commit_contamination(
    commits: list[str], phase_id: str,
) -> list[str]:
    """Phase 134E.10.1.1 — cross-phase commit rejection (defense in depth).

    This repository's own governed commit messages reliably name their
    owning phase in their subject line (e.g. "Phase 134E.10V: ..."/"Finish
    Phase 134E.10V ..."/"Sync Phase 134E.10V ..."), a convention already
    established and unmodified by this phase. For each commit hash, read
    its subject via ``git log -1 --format=%s`` (read-only) and, if the
    subject names a *different* phase identity than ``phase_id``, return a
    human-readable contamination warning. This directly generalizes the
    defect this phase repairs: a prior-phase commit incorrectly attributed
    to the current phase's own ``commits`` field, found via 134E.10.1's own
    governed report citing "1844b05b" (subject: "Finish Phase 134E.10V
    test-evidence-key correction task") as one of ITS commits.

    Deliberately conservative: unresolvable hashes (a synthetic/test hash,
    a git failure, a commit whose subject cites no phase at all) are
    silently skipped, never treated as contamination -- this is an
    additive safety net on top of, never a replacement for, explicit
    ``phase_commits`` declaration, and must never make an ordinary,
    correctly-attributed governed commit (whose subject may legitimately
    omit an explicit "Phase <ID>" token) fail closed by accident.
    """
    import subprocess

    warnings: list[str] = []
    current = phase_id.strip().upper()
    for commit_hash in commits:
        if not commit_hash:
            continue
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%s", commit_hash],
                capture_output=True, text=True, timeout=5,
            )
        except Exception:
            continue
        if result.returncode != 0:
            continue
        subject = result.stdout.strip()
        token = _find_commit_subject_phase_token(subject)
        if token is None:
            continue
        cited = token.normalized_text
        if cited and cited != current:
            warnings.append(
                f"commit {commit_hash} subject names phase {cited!r}, not "
                f"the current phase {phase_id!r}: {subject!r}"
            )
    return warnings


def validate_finalization_gate(
    *,
    phase_id: str,
    report: "PhaseReport",
    metadata: dict[str, Any] | None = None,
    pushed_status: str = "",
    origin_main_head_count: int = 0,
    governance_results: dict[str, Any] | None = None,
    test_results: dict[str, Any] | None = None,
    no_go_confirmations: list[str] | None = None,
    recommended_next_phase: str = "",
    commit_attribution: str = "",
    identity_conflict: str | None = None,
) -> dict[str, Any]:
    """Authoritative finalization gate for phase completion and Telegram send.

    Must pass before:
    - pcae phase complete marks report as complete
    - Telegram send-report sends final report
    - Next phase recommendation is accepted

    Returns a dict with finalizable, blockers, warnings, diagnostics.
    Fail-closed: if any blocker is present, finalizable=False.

    ``identity_conflict`` is an optional pre-computed identity-conflict
    string, appended to ``blockers`` alongside ``validate_phase_
    identity()``'s own findings. 113X.2 originally populated this from
    a comparison between a regex-derived ``--summary`` phase_id and
    metadata's declared one; 113X.4 replaced that derivation with
    ``resolve_canonical_phase_identity()`` (a single deterministic
    source, never summary text), so ``pcae phase complete`` no longer
    has a competing value to conflict with and passes ``None`` here.
    The parameter remains as a general hook for any other caller that
    detects an identity conflict by its own means.
    """
    blockers: list[str] = []
    warnings: list[str] = []
    md = metadata or {}
    gov = governance_results or {}
    tests = test_results or {}
    no_go = no_go_confirmations or []

    # ── Top-level trust ──────────────────────────────────────────────────
    if report.files_changed <= 0:
        blockers.append("files_changed missing or zero")
    if report.tests_run <= 0 and not tests:
        blockers.append("tests_run missing or zero")
    if not gov:
        blockers.append("governance_results missing")
    else:
        for key in _REQUIRED_GOVERNANCE_KEYS:
            if key not in gov:
                blockers.append(f"governance_results.{key} missing")
    if not tests:
        blockers.append("test_results missing")
    else:
        for key in _REQUIRED_BASE_TEST_RESULT_KEYS:
            if key not in tests:
                blockers.append(f"test_results.{key} missing")

    # ── No-go confirmations ──────────────────────────────────────────────
    no_go_text = md.get("no_go_confirmation", "")
    if not no_go_text and not no_go:
        blockers.append("no_go_confirmations missing")
    else:
        # Count from metadata text, or from explicit list
        no_count = 0
        if isinstance(no_go_text, str) and no_go_text:
            no_count = no_go_text.count(_MIN_NO_GO_PREFIX)
        if no_count == 0 and no_go:
            # Count items from the explicit list parameter
            no_count = len([item for item in no_go if str(item).startswith(_MIN_NO_GO_PREFIX)])
        if no_count < _MIN_NO_GO_COUNT:
            blockers.append(
                f"no_go_confirmations too short ({no_count} items, "
                f"require {_MIN_NO_GO_COUNT}+ separate items each starting with 'No ')"
            )

    # ── Recommended next phase ───────────────────────────────────────────
    if not recommended_next_phase:
        blockers.append("recommended_next_phase missing as structured metadata")
    else:
        # 137T: ID recognition delegates to the canonical parser
        # (CPIPC-001, CPIPC-REQ-018), which handles arbitrary subphase
        # depth and trailing letters (e.g. "137I.1V") correctly by
        # construction.
        rn_num = _leading_phase_token(recommended_next_phase)
        if rn_num is not None:
            if rn_num == phase_id:
                blockers.append(
                    f"recommended_next_phase points to current phase ({rn_num}) — must point forward"
                )

    # ── Push state ───────────────────────────────────────────────────────
    if pushed_status and pushed_status not in ("pushed", "clean", "nothing_to_push"):
        blockers.append(f"pushed_status is {pushed_status!r}, not pushed/clean")
    if origin_main_head_count > 0:
        blockers.append(f"origin/main..HEAD is {origin_main_head_count}, not 0")

    # ── Governance push check ────────────────────────────────────────────
    push_check = gov.get("pcae_push_check", "")
    if push_check and "clean" not in push_check and "nothing_to_push" not in push_check:
        blockers.append(f"pcae_push_check is {push_check!r}, not clean")

    # ── Phase-owned commits ──────────────────────────────────────────────
    if report.files_changed > 0:
        if "phase_commits" in md:
            pc = md.get("phase_commits", [])
            if not pc and (not commit_attribution or "none" not in str(commit_attribution).lower()):
                blockers.append("phase_commits declared but empty while files_changed>0")
        elif not commit_attribution:
            blockers.append("commits.phase_owned missing — no phase_commits or commit_attribution in metadata")

    # ── Stale commit detection ───────────────────────────────────────────
    if report.commits and report.files_changed > 0:
        if "phase_commits" not in md and not commit_attribution:
            blockers.append(
                "commits may be stale prior-phase commits — no phase_commits in metadata "
                "and no commit_attribution"
            )
    # Check commit count vs summary
    summary_commit_count = _extract_commit_count_from_summary(report.summary)
    if summary_commit_count is not None and len(report.commits) != summary_commit_count:
        blockers.append(
            f"commit count mismatch: summary says {summary_commit_count}, "
            f"structured list has {len(report.commits)}"
        )

    # ── Report consistency ───────────────────────────────────────────────
    for issue in validate_internal_report_coherence(report):
        blockers.append(f"internal report coherence: {issue}")
    # Phase 134E.9 — derived-correctness manifest, checked independently
    # of report_completeness below so a caller that bypasses
    # _apply_canonical_and_trust (never happens today, but the gate must
    # not rely on that) still fails closed here.
    for issue in validate_derived_correctness(report):
        blockers.append(f"derived correctness: {issue}")
    if report.report_completeness != COMPLETENESS_COMPLETE:
        blockers.append(
            f"report completeness is {report.report_completeness!r}, not complete"
        )
    missing_fields = getattr(report, "missing_trust_fields", []) or []
    if missing_fields:
        blockers.append(f"missing trust fields: {', '.join(missing_fields)}")

    # ── Phase 113B.2 — Phase identity validation ─────────────────────────
    identity_issues = validate_phase_identity(report, phase_id, md)
    for issue in identity_issues:
        blockers.append(f"phase identity: {issue}")

    # ── Phase 113X.2 — Canonical phase-identity source conflict ──────────
    if identity_conflict:
        blockers.append(f"phase identity: {identity_conflict}")

    # ── Determine outcome ────────────────────────────────────────────────
    finalizable = len(blockers) == 0

    return {
        "finalizable": finalizable,
        "blockers": blockers,
        "warnings": warnings,
        "phase_id": phase_id,
        "recommended_next_phase": recommended_next_phase,
        "pushed_status": pushed_status,
        "origin_main_head_count": origin_main_head_count,
        "phase_owned_commits": bool(md.get("phase_commits")),
        "commit_attribution": commit_attribution,
        "missing_trust_fields": missing_fields,
        "report_completeness": report.report_completeness,
    }


def validate_phase_identity(
    report: PhaseReport,
    phase_id: str,
    md: dict[str, Any],
) -> list[str]:
    """Validate that phase identity is consistent across canonical sources.

    Cross-references the report's ``phase_id`` against PROJECT_STATUS.md,
    architecture status, metadata, and RuntimeSnapshot. Returns a list
    of issue strings (empty = valid). Each returned issue is a hard
    blocker — phase identity mismatches are never advisory.

    Sub-phases (like 113B.2) are legitimate governance hardening phases
    that may not match the current parent phase in PROJECT_STATUS.md.
    They are not flagged as identity mismatches.

    Phase 113B.2 — fail-closed: summary/commit/architecture mismatches
    block finalization.
    """
    issues: list[str] = []
    import re as _re

    # ── 1. PROJECT_STATUS.md current phase vs report phase_id ───────────
    # Sub-phases (e.g. 113B.2) run independently of the current parent
    # phase (e.g. 113C).  Only flag if the report claims to be a parent
    # phase that PROJECT_STATUS.md says is different.
    #
    # Phase 136AX: this used to be a third, independently-maintained
    # regex pair for "find the Current Phase declaration line"
    # (``\d{3}[A-Z](?:\.\d+)?`` -- exactly three digits, exactly one
    # branch letter, no DOTALL), diverging from the module-level
    # ``_CURRENT_PHASE_SECTION_RE``/``_CURRENT_PHASE_LINE_RE`` used by
    # ``build_architecture_status`` below. A three-digit-only phase-ID
    # grammar cannot match this repository's own two- or four-digit
    # families, and the single-branch-letter grammar cannot match a
    # two-letter mainline suffix ("136AW") -- reusing the shared regexes
    # here closes both gaps and removes the duplicate-parser divergence
    # risk (a fix to one no longer silently misses the other).
    ps_path = Path("PROJECT_STATUS.md")
    if ps_path.exists():
        ps_text = ps_path.read_text(encoding="utf-8")
        current_section = _CURRENT_PHASE_SECTION_RE.search(ps_text)
        if current_section:
            section_text = current_section.group(1)
            declaration = _match_current_phase_declaration(section_text)
            if declaration:
                current_id = declaration.phase_id
                # Sub-phases (113B.2) are allowed to complete independently
                is_sub_phase = "." in phase_id
                if not is_sub_phase and current_id != phase_id:
                    # 137T: "same series+branch family" delegates to the
                    # canonical ``same_branch`` predicate (CPIPC-REQ-043)
                    # instead of an ad hoc regex + string compare.
                    report_pid = canonical_phase_id.match_leading_token(phase_id)
                    current_pid = canonical_phase_id.match_leading_token(current_id)
                    if report_pid is not None and current_pid is not None:
                        if not canonical_phase_id.same_branch(report_pid, current_pid):
                            issues.append(
                                f"Report phase_id={phase_id!r} does not match "
                                f"PROJECT_STATUS.md current phase "
                                f"{current_id!r}"
                            )

    # ── 2. Architecture Status consistency ──────────────────────────────
    # Phase 113X.5 — uses the structured `completed_phase_ids` field
    # (113X audit Finding 4) rather than regex-sniffing the human-
    # readable `completed` display strings: the retired hardcoded
    # SERIES_MAP label ("Advisory Runtime (Architecture, Contract,
    # Prototype)") contained no digits at all, so the old substring
    # check ("series in comp") could never actually fire -- the exact
    # reason Finding 4's impossible combination went undetected.
    arch_status = getattr(report, "architecture_status", None) or {}
    if arch_status:
        in_progress = arch_status.get("in_progress", [])
        planned = arch_status.get("planned", [])
        completed_ids = set(arch_status.get("completed_phase_ids", []))

        # 137T: Phase ID recognition delegates to the canonical parser
        # (CPIPC-001, CPIPC-REQ-018) instead of a locally hand-rolled
        # regex -- this also directly fixes the historical Phase
        # 134E.10.1.1 dropped-trailing-letter defect the previous regex
        # needed its own special-cased fix for, since the canonical
        # grammar already handles arbitrary subphase depth and trailing
        # letters correctly by construction.
        def _leading_phase_id(text: str) -> str | None:
            leading = canonical_phase_id.match_leading_token(text)
            return leading.normalized_text if leading is not None else None

        def _parenthetical_phase_id(text: str) -> str | None:
            m = _re.search(r"\(([^()]+)\)", text)
            if m is None:
                return None
            err = canonical_phase_id.validate(m.group(1))
            if err is not None:
                return None
            return canonical_phase_id.normalize(m.group(1))

        planned_ids = [pid for p in planned if (pid := _leading_phase_id(p))]

        # Detect impossible combination: phase is in "in_progress" AND
        # in "planned" at the same time.
        for item in in_progress:
            ip_id = _parenthetical_phase_id(item)
            if ip_id and ip_id in planned_ids:
                issues.append(
                    f"Architecture Status inconsistency: phase "
                    f"{ip_id!r} is both in-progress and planned"
                )

        # "X complete" while "X recommended next" is impossible -- now a
        # direct set-membership check against the structured evidence,
        # not a substring match on a label that may not even contain
        # the phase ID as text.
        for planned_id in planned_ids:
            if planned_id in completed_ids:
                issues.append(
                    f"Architecture Status inconsistency: {planned_id!r} "
                    f"is both completed and still recommended as the "
                    f"planned next phase"
                )

        # "Contract missing while Prototype completed" is structurally
        # prevented rather than validated after the fact:
        # _render_series_milestone_label() only ever includes phases with
        # actual "## Phase X Complete" evidence, so a milestone can never
        # be displayed as completed without its own header existing. A
        # "consecutive letters" gap check was considered here (e.g. A,
        # C present but B absent) and rejected -- this codebase's own
        # convention legitimately uses non-consecutive mnemonic letters
        # for sub-phases (e.g. "111R" for a Review phase after "111D"),
        # so that heuristic produces false positives against real
        # history. Flagging it would itself be a form of inferring a
        # problem from an assumption, the exact thing this phase removes.

        # "Execution available while Runtime state is Observed" is
        # impossible -- Observed is this codebase's non-executing
        # ceiling (see Runtime State Model, 110A); execution can only
        # ever be reported unavailable while it holds. This validates
        # Architecture Status's own two fields for internal agreement;
        # it does not read or modify Runtime Snapshot itself.
        runtime_state = arch_status.get("current_runtime_state", "")
        execution_availability = arch_status.get("execution_availability", "")
        if (
            runtime_state == "Observed"
            and execution_availability
            and execution_availability.lower() != "unavailable"
        ):
            issues.append(
                f"Architecture Status inconsistency: current_runtime_state "
                f"is 'Observed' but execution_availability is "
                f"{execution_availability!r}, not 'unavailable'"
            )

    # ── 3. Recommended next phase vs Architecture Status planned ────────
    # 137T: Phase ID recognition delegates to the canonical parser
    # (CPIPC-001, CPIPC-REQ-018) instead of a locally hand-rolled regex.
    if report.recommended_next_phase and arch_status.get("planned"):
        rec_id_pid = canonical_phase_id.match_leading_token(report.recommended_next_phase)
        if rec_id_pid is not None:
            rec_id = rec_id_pid.normalized_text
            planned_items = arch_status["planned"]
            planned_ids2: list[str] = []
            for p in planned_items:
                pm = canonical_phase_id.match_leading_token(p)
                if pm is not None:
                    planned_ids2.append(pm.normalized_text)
            if planned_ids2 and rec_id not in planned_ids2:
                # Only an issue if the report's recommendation differs from
                # what PROJECT_STATUS.md derived as planned
                pass  # Informational only — not a hard blocker
                # Different sources may legitimately differ on recommendation

    # ── 4. Metadata execution integration vs Architecture Status ────────
    ei_status = md.get("execution_integration_status", {})
    if ei_status and arch_status:
        meta_state = ei_status.get("current_maximum_runtime_state", "")
        arch_state = arch_status.get("current_runtime_state", "")
        if meta_state and arch_state and meta_state != arch_state:
            issues.append(
                f"Runtime state mismatch: metadata says {meta_state!r}, "
                f"Architecture Status says {arch_state!r}"
            )

        meta_cap = ei_status.get("current_maximum_plugin_capability", "")
        arch_cap = arch_status.get("current_maximum_capability", "")
        if meta_cap and arch_cap and meta_cap != arch_cap:
            issues.append(
                f"Plugin capability mismatch: metadata says {meta_cap!r}, "
                f"Architecture Status says {arch_cap!r}"
            )

    # ── 5. (retired — see Phase 113X.4) ──────────────────────────────────
    # Previously compared a regex-extracted "Phase X: ..." reference in
    # report.summary against phase_id, blocking on disagreement. Phase
    # 113X.4 removed --summary as a phase-identity source entirely (113X
    # audit Finding 3: regex-derived identity from free text is
    # fundamentally unsound) -- keeping this check would still let
    # summary prose block a canonically-correct finalization whenever it
    # happened to open with "Phase X: ..." referencing anything else,
    # directly contradicting "free-text summaries must never determine
    # phase id" (now true of validation too, not just derivation).

    # ── 6. Commits reference other phases ───────────────────────────────
    for commit in report.commits:
        commit_msg = commit if isinstance(commit, str) else (
            commit.get("message", "") if isinstance(commit, dict) else ""
        )
        # 137T: "Phase " prefix location stays local; ID recognition
        # delegates to the canonical parser (CPIPC-001, CPIPC-REQ-018).
        commit_prefix_match = _re.search(r"Phase\s+", commit_msg, _re.IGNORECASE)
        commit_phase_pid = (
            canonical_phase_id.match_leading_token(commit_msg[commit_prefix_match.end():])
            if commit_prefix_match is not None else None
        )
        if commit_phase_pid is not None:
            commit_phase = commit_phase_pid.normalized_text
            if commit_phase != phase_id.upper():
                # Sub-phases may reference their parent phase (113B.2 → 113B)
                is_sub = "." in phase_id
                parent = phase_id.split(".")[0] if is_sub else ""
                if not (is_sub and commit_phase == parent):
                    issues.append(
                        f"Commit message references Phase {commit_phase!r} "
                        f"but report is for Phase {phase_id!r}: "
                        f"{commit_msg[:80]}"
                    )

    return issues


#
# Phase 134E.8: the phase-ID capture group below uses the same grammar as
# ``_CANONICAL_TITLE_PHASE_ID_RE`` (134B.3's canonical identity
# resolution) -- ``\d+[A-Z](?:\.\d+[A-Za-z]?)*`` -- instead of the
# previous ``\d{3}[A-Z](?:\.\d+)?``, which could not parse a dotted
# sub-phase with a trailing verification letter (e.g. "134E.7V") at all.
# That silent parse failure was the direct cause of the *current* phase
# vanishing from "In Progress" once Track 134 reached its first ".<N>V"
# verification phase.
# Status-marker alternation shared by every declaration-line grammar
# below (both the "## Current Phase" line and the "## Phase X Complete"
# header's own label line use the same "Phase <id> — <title> (<status>
# ...)." shape). Defined once here so both consumers stay in sync.
_PHASE_STATUS_MARKER_ALTERNATION = (
    r"completed|not started|in progress|blocked|partial|cancelled"
)

# Phase 136AX: branch letter is one-or-more (see _CANONICAL_TITLE_PHASE_ID_RE
# above) -- fixes the same two-letter-suffix parse failure for the
# "## Phase X Complete" header grammar.
_COMPLETED_PHASE_HEADER_RE = re.compile(
    r"^##\s+Phase\s+(\d+[A-Z]+(?:\.\d+[A-Za-z]?)*)\s*(?:Complete|—.*?Complete)",
    re.MULTILINE,
)
_PHASE_LABEL_LINE_RE = re.compile(
    r"^Phase\s+\d+[A-Z]+(?:\.\d+[A-Za-z]?)*\s*[—–-]\s*(.+)$", re.MULTILINE,
)
# Phase 144J: mirrors _CURRENT_PHASE_LINE_WITH_STATUS_RE's DOTALL,
# marker-bounded repair for the sibling "## Phase X Complete" header's
# own label line. Reproduced live: 144A's header snippet is "Phase 144A
# — Publication Execution Ownership Architecture (completed,\narchitecture
# only). ...", and the un-bounded, non-DOTALL _PHASE_LABEL_LINE_RE above
# truncated at the first physical newline, producing the literal,
# unclosed fragment "Publication Execution Ownership Architecture
# (completed," as the milestone label -- the trailing-parenthetical
# stripper below never fires because that fragment has no closing ")"
# to strip. Tried first; falls back to the single-line regex above when
# no status-marker-bounded parenthetical is present at all.
_PHASE_LABEL_LINE_WITH_STATUS_RE = re.compile(
    r"^Phase\s+\d+[A-Z]+(?:\.\d+[A-Za-z]?)*\s*[—–-]\s*"
    r"(.+?)\s*\((" + _PHASE_STATUS_MARKER_ALTERNATION + r")\b[^)]*\)\.?",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
_CURRENT_PHASE_SECTION_RE = re.compile(
    r"^##\s+Current\s+Phase\s*$\n\n(.*?)(?=\n##\s|\Z)",
    re.MULTILINE | re.DOTALL,
)
# Phase 136AX: two repairs to the "Phase <id> — <title> (<status>)."
# declaration-line grammar, both reproduced directly against this
# repository's own live PROJECT_STATUS.md:
#
# 1. Branch letter is one-or-more, not exactly one (see
#    _CANONICAL_TITLE_PHASE_ID_RE above) -- "Phase 136AW — ..." (a
#    two-letter mainline suffix) previously could not match at all,
#    which is the direct, reproduced cause of "## Current Phase section
#    present but its phase-ID/title line did not parse -- current phase
#    could not be identified".
# 2. The title capture now spans to the declaration's own
#    "(completed)"/"(not started)"/etc. status marker with DOTALL,
#    instead of stopping at the first physical newline (``(.+)$`` with
#    only MULTILINE). This repository hand-wraps the declaration
#    sentence across multiple physical lines ("Phase 136AW — Stage 3
#    ...\nReadiness Assessment (completed)."), and the previous grammar
#    silently truncated the title at the wrap point. The match is
#    bounded to the nearest recognized status marker (never open-ended)
#    so it cannot run away into the rest of the section's prose.
#
# Not every declaration line carries an explicit status marker at all
# (e.g. a historical convention: "Phase 134E.10.1V.1 — Completed-Phase
# Architecture Status Transition Repair." with no trailing "(...)").
# Two regexes, tried in order, keep both shapes working: the primary,
# DOTALL, marker-bounded pattern handles the common convention (and the
# wrap-truncation repair); the fallback single-line pattern (the
# original, pre-136AX grammar, letter-count-fixed) handles a
# marker-less declaration exactly as before. ``_match_current_phase_
# declaration()`` is the single call site every consumer uses instead of
# matching either regex directly, so this two-tier fallback is never
# duplicated.
#
# Phase 144J: the marker-bounded pattern required the parenthetical to
# contain *only* the bare marker word (e.g. "(completed)"). This
# repository's actual phase-close convention always qualifies the
# marker with trailing detail -- "(completed, documentation/governance/
# consistency only; no implementation ... change)" -- so that exact
# shape never matched, silently falling through to the marker-less
# fallback below, which truncates the title at the first physical line
# break and leaves ``status_marker`` unset (never guessed as
# completed). Reproduced live against 144H and 144I: both were
# misclassified as "In Progress" in generated Architecture Status
# despite each declaration's own text saying "(completed, ...)". Fixed
# by requiring only that the marker word start the parenthetical
# (``\b[^)]*`` consumes any trailing qualifier up to the close paren)
# rather than requiring it to be the parenthetical's entire content.
# (``_PHASE_STATUS_MARKER_ALTERNATION`` itself is defined once, above,
# next to its first consumer, ``_PHASE_LABEL_LINE_WITH_STATUS_RE``.)
_CURRENT_PHASE_LINE_WITH_STATUS_RE = re.compile(
    r"^Phase\s+(\d+[A-Z]+(?:\.\d+[A-Za-z]?)*)\s*[—–-]\s*"
    r"(.+?)\s*\((" + _PHASE_STATUS_MARKER_ALTERNATION + r")\b[^)]*\)\.?",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
_CURRENT_PHASE_LINE_NO_STATUS_RE = re.compile(
    r"^Phase\s+(\d+[A-Z]+(?:\.\d+[A-Za-z]?)*)\s*[—–-]\s*(.+)$",
    re.MULTILINE,
)


class CurrentPhaseDeclaration:
    """(phase_id, title, status_marker) for a parsed "## Current Phase"
    declaration line. ``status_marker`` is ``None`` when the declaration
    carries no explicit status marker at all (never guessed)."""

    __slots__ = ("phase_id", "title", "status_marker")

    def __init__(self, phase_id: str, title: str, status_marker: str | None) -> None:
        self.phase_id = phase_id
        self.title = title
        self.status_marker = status_marker

    @property
    def is_completed(self) -> bool:
        return self.status_marker == "completed"


def _match_current_phase_declaration(text: str) -> CurrentPhaseDeclaration | None:
    """Parse a "Phase <id> — <title> [(<status>).]" declaration line
    from the start of ``text``. Tries the status-marker-bounded,
    wrap-safe grammar first; falls back to the original single-physical-
    line grammar only when no status marker is present at all. Returns
    ``None`` if neither matches -- callers must not guess."""
    with_status = _CURRENT_PHASE_LINE_WITH_STATUS_RE.match(text)
    if with_status:
        title = re.sub(r"\s+", " ", with_status.group(2)).strip()
        return CurrentPhaseDeclaration(
            with_status.group(1), title, with_status.group(3).lower()
        )
    no_status = _CURRENT_PHASE_LINE_NO_STATUS_RE.match(text)
    if no_status:
        return CurrentPhaseDeclaration(
            no_status.group(1), no_status.group(2).strip(), None
        )
    return None
# Phase 134E.8: "repo " is now optional. Current phase reports write
# "Recommended next phase: ..."; only historical reports (pre-134-series
# wording) wrote "Recommended next repo phase: ...". The previous
# regex matched the old wording only, so the *current* phase's own
# recommendation sentence never matched it -- this was the direct cause
# of falling through to the stale whole-file fallback that produced
# "Planned: 132F" long after Track 132 completed. The fallback itself is
# removed below (see build_architecture_status): a recommendation is
# now read only from the current phase's own bounded section text, never
# reached-back-into-history.
#
# Phase 136AX: dropped the ``^...$`` line-start/line-end anchoring (was
# ``re.MULTILINE`` with no ``re.DOTALL``). In this repository's actual
# prose the sentence is routinely embedded mid-paragraph -- e.g. "...the
# re-derived contract exactly. Recommended next phase: **136AV — Stage
# 3\nTyped Authority Model Whole-Model Integration Verification**." --
# so requiring "Recommended" at the start of a physical line meant the
# regex essentially never matched real content, and the title (when it
# did match by coincidence) was truncated at the first physical newline.
# ``_RECOMMENDED_NEXT_PHASE_LABEL_RE`` below only locates the label; the
# value itself is extracted by ``_extract_recommended_next_phase_values``
# using this repository's two actual authoring conventions (a
# ``**bold**`` span, or a plain sentence terminated by ``". "``), so a
# wrapped title is preserved in full and an incidental period inside a
# bold span's own text never truncates the capture early.
_RECOMMENDED_NEXT_PHASE_LABEL_RE = re.compile(
    r"Recommended\s+next\s*\n?\s*(?:repo\s+)?phase:\s*",
    re.IGNORECASE,
)
_BOLD_SPAN_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_PLAIN_SENTENCE_RE = re.compile(r"(.+?)\.(?:\s|$)", re.DOTALL)


def _extract_recommended_next_phase_values(section_text: str) -> list[str]:
    """Extract every "Recommended next [repo ]phase: ..." value from
    ``section_text``, preserving the full (possibly wrapped) title and
    normalizing internal whitespace. Never reaches outside the given
    bounded text. Returns values in order of appearance; callers that
    want only the current phase's own recommendation must pass only that
    phase's own bounded section text (see ``build_architecture_status``).
    """
    values: list[str] = []
    for label_match in _RECOMMENDED_NEXT_PHASE_LABEL_RE.finditer(section_text):
        rest = section_text[label_match.end():]
        bold_match = _BOLD_SPAN_RE.match(rest)
        if bold_match:
            raw = bold_match.group(1)
        else:
            plain_match = _PLAIN_SENTENCE_RE.match(rest)
            raw = plain_match.group(1) if plain_match else None
        if raw is None:
            continue
        normalized = re.sub(r"\s+", " ", raw).strip()
        normalized = re.sub(
            r"\s*\(not\s+started\)\s*\.?\s*$", "", normalized
        ).rstrip(".").strip()
        if normalized:
            values.append(normalized)
    return values


def _is_milestone_phase_id(phase_id: str) -> bool:
    """True for a phase ID that represents architectural milestone
    progress within its series -- a plain lettered mainline phase
    (e.g. ``"113A"``, ``"113B"``), never a sub-phase (``"113B.2"``) or
    the ``"X"`` exceptional/corrective-governance branch (``"113X.1"``).

    Phase 113X.5: sub-phases and the X-branch are corrective governance
    work, not architecture-track progress -- including them in
    Architecture Status would misrepresent what actually advanced the
    architecture (e.g. 113X.1-.5's own governance repairs are not
    "Advisory Runtime" milestones).
    """
    try:
        parsed = canonical_phase_id.parse(phase_id)
    except canonical_phase_id.PhaseIdError:
        return False
    return not parsed.subphase and parsed.branch != "X"


def _longest_common_prefix(strings: list[str]) -> str:
    """Deterministic longest-common *word* prefix across a list of
    strings. Returns ``""`` for an empty list or when there is no common
    prefix.

    Phase 134E.8: compares whole words, not characters. A character-level
    prefix (the pre-134E.8 behavior) can stop mid-word when two titles
    share a stem but diverge inside it -- e.g. "...Advisory Consumption
    Architecture" vs "...Advisory Context Prototype" share only "Con" at
    the character level, producing a garbled "Con: sumption ... text
    Prototype" label once chapters wider than the narrow 110-113 series
    (each hand-verified to have clean short common prefixes) were
    included. Comparing whole words instead means the prefix always ends
    on a real word boundary, so the remainder is always readable prose,
    never a split fragment.
    """
    if not strings:
        return ""
    word_lists = [s.split() for s in strings]
    shortest = min(len(w) for w in word_lists)
    common: list[str] = []
    for i in range(shortest):
        candidate = word_lists[0][i]
        if all(w[i] == candidate for w in word_lists):
            common.append(candidate)
        else:
            break
    return " ".join(common)


# Phase 134E.8: guardrails on the "prefix + remainders" milestone label
# format -- correct for a handful of short, cleanly-related titles (the
# 110-113 series this format was designed against), but unreadable once
# applied unconditionally to a series with many phases or with duplicate/
# degenerate remainders (observed directly against real repository state
# for series 119, 122, and 124 once the 110-113 scope restriction was
# lifted). Beyond these guardrails, ``_render_series_milestone_label()``
# falls back to a compact, always-readable, always-deterministic form
# instead of an ever-growing concatenated line.
_MILESTONE_LABEL_MAX_PHASES = 8
_MILESTONE_LABEL_MAX_LENGTH = 200


def _render_series_milestone_label(phases: list[tuple[str, str]]) -> str:
    """Render a concise, evidence-derived label for one series' completed
    milestone phases (Phase 113X.5 -- replaces the hardcoded ``SERIES_MAP``
    Finding 4 identified).

    ``phases`` must already be the *actually completed* milestone phases
    for one series, sorted by phase letter (never inferred, never
    including a phase whose own "## Phase X Complete" header wasn't
    found). A single completed phase renders as its own full title
    (there's nothing to abbreviate against). A small series of related
    titles renders as their titles' longest common *word* prefix (the
    shared "track name", e.g. "Advisory Runtime"), followed by each
    phase's own distinguishing remainder joined with " + ", in phase
    order -- so the label always grows exactly in step with which phases
    have actually completed, and never shows a milestone whose own phase
    never completed. A larger or degenerate series (many phases, no
    common prefix, an empty/duplicate remainder, or an excessively long
    rendered line) falls back to a compact ``"<first phase's title>
    (<first id>-<last id>, N phases)"`` form -- full traceability to the
    underlying phase IDs remains available via ``completed_phase_ids``/
    ``completed_chapters`` regardless of which form is used here.
    """
    if not phases:
        return ""
    if len(phases) == 1:
        return phases[0][1]

    ids = [pid for pid, _name in phases]
    names = [name for _pid, name in phases]
    id_range = f"{ids[0]}-{ids[-1]}"
    compact_fallback = f"{names[0]} ({id_range}, {len(phases)} phases)"

    if len(phases) > _MILESTONE_LABEL_MAX_PHASES:
        return compact_fallback

    prefix = _longest_common_prefix(names)
    if not prefix:
        return compact_fallback
    remainders = [name[len(prefix):].strip() for name in names]
    if not all(remainders) or len(set(remainders)) != len(remainders):
        # Empty remainder (a title equals the prefix exactly) or a
        # duplicate remainder (two titles collapse to the same
        # distinguishing text) -- neither is a safe "+"-joined summary.
        return compact_fallback

    label = f"{prefix}: {' + '.join(remainders)}"
    if len(label) > _MILESTONE_LABEL_MAX_LENGTH:
        return compact_fallback
    return label


def build_architecture_status(
    *,
    completing_phase_id: str = "",
    completing_phase_name: str = "",
    report_status: str = "",
    recommended_next_phase: str = "",
) -> dict[str, Any]:
    """Derive a PCAE Architecture Status snapshot from canonical project state.

    Reads PROJECT_STATUS.md to discover completed architectural phases,
    the current phase, and the most recent recommended next phase.
    Reads RuntimeSnapshot for current runtime state, maximum capability,
    and execution availability.
    Returns a dict suitable for the ``architecture_status`` field of a
    PhaseReport.  Never manually maintained — always derived from the
    canonical sources at report-generation time.

    Phase 113X.5 — canonicalized (113X Finding 4): milestone labels are
    no longer a static per-series lookup table describing a series'
    *eventual, full* scope regardless of actual progress. Each series'
    label is now rendered from exactly the phases whose own "## Phase X
    Complete" header actually exists, sorted deterministically by
    phase-ID shape (independent of the section's physical position in
    the file -- 113X audit Finding 6's "out-of-order documentation"
    risk), via ``_render_series_milestone_label()``.

    Phase 134E.8 — repaired three compounding defects that together
    produced a stale "Planned: 132F" claim long after Track 132
    completed, discovered by direct source and state inspection (see
    ``docs/PHASE_134_ARCHITECTURE_STATUS_GENERATION_REPAIR.md``):
    (1) the "planned" regex only matched the retired "Recommended next
    repo phase:" wording, so the current phase's own "Recommended next
    phase:" sentence never matched and generation silently fell back to
    a whole-file search that returned the *first* (most historically
    distant) match of the old wording; the fallback is removed entirely
    -- a recommendation is now read only from the current phase's own
    bounded section text, and its absence is disclosed rather than
    papered over with historical text. (2) "completed" derivation was
    hard-scoped to the 110-113 series only, so Tracks 125-134 could
    never appear even after (1) was fixed; the scope restriction is
    removed -- every series with at least one genuine "## Phase X
    Complete" mainline header now gets its own chapter entry. (3) the
    phase-ID grammar used throughout could not parse a dotted sub-phase
    with a trailing verification letter (e.g. "134E.7V"), so the actual
    current phase silently disappeared from "In Progress"; the grammar
    now matches ``pcae.core.architecture_status.PHASE_ID_RE`` (134B.3's
    canonical identity resolution) exactly. ``completed``,
    ``in_progress``, and ``planned`` remain derived independently from
    disjoint evidence (completed-phase headers; the "## Current Phase"
    section, only if not marked completed; that same section's own
    recommendation sentence) -- none is inferred from another, and any
    resulting overlap (a completed phase still appearing planned) is
    treated as a conflict: dropped from ``planned`` and recorded in
    ``conflicts`` rather than silently displayed.

    Returns a dict with keys:
        schema_version: str — architecture_status.ARCHITECTURE_STATUS_SCHEMA_VERSION
        state_marker: str — short deterministic digest of the
            PROJECT_STATUS.md content this status was derived from (no
            wall-clock time; equal content always yields the same marker)
        completed: list[str] — completed architectural milestones (display)
        completed_phase_ids: list[str] — the exact phase IDs behind
            ``completed``, sorted deterministically -- structured
            evidence for consistency validation, so checks never need
            to regex-parse the human-readable ``completed`` strings
            (the fragility that let Finding 4's impossible-combination
            check silently never fire).
        completed_chapters: list[dict] — one entry per series with keys
            ``chapter`` (series id), ``label`` (display string), and
            ``phase_ids`` (the mainline phase IDs behind that label) --
            structured chapter membership for validation/traceability.
        in_progress: list[str] — current work in progress
        current_phase_id: str — exact current phase ID, or "" if none
        planned: list[str] — planned next milestones (display)
        planned_phase_ids: list[str] — exact phase IDs behind ``planned``
        current_runtime_state: str
        current_maximum_capability: str
        execution_availability: str
        freshness: str — one of architecture_status.VALID_FRESHNESS_STATES
        limitations: list[str] — disclosed gaps (e.g. no explicit plan)
        conflicts: list[str] — disclosed conflicts (fail-closed detections)
        source_provenance: dict[str, str] — per-source read outcome
    """
    from pathlib import Path as _Path
    from pcae.core.architecture_status import (
        ARCHITECTURE_STATUS_SCHEMA_VERSION,
        FRESHNESS_FRESH,
        FRESHNESS_FRESH_WITH_LIMITATIONS,
        FRESHNESS_INVALID,
        parse_phase_id,
        phase_sort_key,
    )

    result: dict[str, Any] = {
        "schema_version": ARCHITECTURE_STATUS_SCHEMA_VERSION,
        "state_marker": "",
        "repository_revision": "",
        "completed": [],
        "completed_phase_ids": [],
        "completed_chapters": [],
        "in_progress": [],
        "current_phase_id": "",
        "planned": [],
        "planned_phase_ids": [],
        "current_runtime_state": "",
        "current_maximum_capability": "",
        "execution_availability": "",
        "freshness": FRESHNESS_INVALID,
        "limitations": [],
        "conflicts": [],
        "source_provenance": {
            "project_status_md": "missing",
            "current_phase_section": "not_found",
            "runtime_snapshot": "not_attempted",
            "repository_revision": "not_attempted",
        },
    }

    limitations: list[str] = []
    conflicts: list[str] = []

    # ── Derive from PROJECT_STATUS.md ──────────────────────────────────
    ps_path = _Path("PROJECT_STATUS.md")
    if not ps_path.exists():
        # Phase 134E.9 — an absent source is a disclosed limitation, not
        # a detected contradiction. "invalid" is now reserved exclusively
        # for genuine conflicts (completed/planned overlap, disagreeing
        # duplicate-header titles) so that validate_derived_correctness()
        # can safely fail closed on "invalid" without also rejecting the
        # legitimate bootstrap/explicit-identity scenario where no
        # PROJECT_STATUS.md exists yet (e.g. a fresh repository, or a
        # caller supplying phase identity entirely via --phase-id).
        result["limitations"] = ["PROJECT_STATUS.md not found -- no canonical state source available"]
        result["freshness"] = FRESHNESS_FRESH_WITH_LIMITATIONS
        return result

    ps_text = ps_path.read_text(encoding="utf-8")
    result["source_provenance"]["project_status_md"] = "read"
    import hashlib as _hashlib
    result["state_marker"] = _hashlib.sha256(ps_text.encode("utf-8")).hexdigest()[:16]
    try:
        import subprocess as _subprocess
        revision = _subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if revision.returncode == 0 and revision.stdout.strip():
            result["repository_revision"] = revision.stdout.strip()
            result["source_provenance"]["repository_revision"] = "read"
        else:
            result["source_provenance"]["repository_revision"] = "unavailable"
            limitations.append("repository revision unavailable -- status cannot be bound to a commit")
    except Exception as exc:
        result["source_provenance"]["repository_revision"] = f"unavailable: {exc}"
        limitations.append("repository revision unavailable -- status cannot be bound to a commit")

    # ── Completed: independently derived from "## Phase X Complete"
    # headers only. Never inferred, never extrapolated to phases whose
    # own header is absent. This repository's convention gives most
    # phases *two* such headers -- one "(historical — full text)" section
    # with the full "Phase X — Title (completed)." declaration line, and
    # one short recap section that often has no such line at all -- so
    # duplicate headers are expected, not evidence of a documentation
    # error, and are deduplicated by first occurrence. A conflict is
    # disclosed only when *both* occurrences yield an actual parsed
    # title (never when one occurrence merely fell back to the bare
    # phase ID for lack of a title line) and those titles disagree --
    # that is a genuine title disagreement, not this repo's normal
    # dual-header shape.
    completed_phases: list[tuple[str, str]] = []
    seen_ids: dict[str, tuple[str, bool]] = {}
    for m in _COMPLETED_PHASE_HEADER_RE.finditer(ps_text):
        phase_id = m.group(1)
        # Phase 144J: bounded to this header's own section (up to the
        # next "## " line), not a fixed 200-char window. The fixed
        # window cut off mid-declaration for any title + status-marker
        # qualifier longer than 200 chars (reproduced live: 144H's own
        # wrapped declaration needs ~230 chars to reach its closing
        # status parenthetical), silently truncating or -- when the
        # opening "(" fell inside the truncated window but its ")"
        # didn't -- leaving a dangling, unclosed fragment as the
        # "name" (reproduced live: 144A rendered as "...Architecture
        # (completed,"). Bounding to the next header instead of a fixed
        # length was verified against every one of this repository's
        # 532 "## Phase X Complete" headers to introduce no
        # cross-section contamination (no header's resolved name grew
        # anomalously long by spilling into a later section).
        next_header = ps_text.find("\n##", m.end())
        section_end = next_header if next_header != -1 else len(ps_text)
        snippet = ps_text[m.end():section_end]
        name_m = _PHASE_LABEL_LINE_WITH_STATUS_RE.search(snippet)
        if name_m is None:
            name_m = _PHASE_LABEL_LINE_RE.search(snippet)
        has_real_name = name_m is not None
        phase_name = re.sub(r"\s+", " ", name_m.group(1)).strip() if name_m else phase_id
        # Strip a trailing "(completed)."/"(not started)." style status
        # marker -- part of the phase declaration line's own formatting,
        # never part of the milestone's actual name. Defense in depth:
        # normally already excluded by the marker-bounded regex above,
        # this also cleans up the marker-less fallback's output should
        # it still end on a parenthetical.
        phase_name = re.sub(r"\s*\([^()]*\)\.?\s*$", "", phase_name).rstrip(".").strip()
        if not phase_name:
            phase_name = phase_id
            has_real_name = False
        if phase_id in seen_ids:
            prev_name, prev_has_real = seen_ids[phase_id]
            if has_real_name and prev_has_real and prev_name != phase_name:
                conflicts.append(
                    f"conflicting titles for phase {phase_id!r}: "
                    f"{prev_name!r} vs {phase_name!r}"
                )
            continue
        seen_ids[phase_id] = (phase_name, has_real_name)
        completed_phases.append((phase_id, phase_name))

    # Group by series, each group sorted by phase-ID shape (series,
    # branch, subphase) -- deterministic regardless of the order
    # headers physically appear in the file.
    by_series: dict[str, list[tuple[str, str]]] = {}
    for pid, pname in completed_phases:
        parsed = parse_phase_id(pid)
        if parsed is None:
            continue
        series = str(parsed[0])
        by_series.setdefault(series, []).append((pid, pname))
    for series in by_series:
        by_series[series].sort(key=lambda pn: phase_sort_key(pn[0]))

    completed_labels: list[str] = []
    completed_phase_ids: list[str] = []
    completed_chapters: list[dict[str, Any]] = []
    for series in sorted(by_series, key=lambda s: int(s) if s.isdigit() else s):
        phases = by_series[series]
        milestone_phases = [phase for phase in phases if _is_milestone_phase_id(phase[0])]
        label = _render_series_milestone_label(milestone_phases or phases)
        completed_labels.append(label)
        ids_for_series = [pid for pid, _name in phases]
        completed_phase_ids.extend(ids_for_series)
        completed_chapters.append({
            "chapter": series,
            "label": label,
            "phase_ids": ids_for_series,
        })

    result["completed"] = completed_labels
    result["completed_phase_ids"] = completed_phase_ids
    result["completed_chapters"] = completed_chapters
    completed_id_set = set(completed_phase_ids)

    # ── In progress / current: independently derived from the "## Current
    # Phase" section only -- never inferred from the completed list above.
    current_section = _CURRENT_PHASE_SECTION_RE.search(ps_text)
    current_section_text = current_section.group(1) if current_section else ""
    if current_section_text:
        result["source_provenance"]["current_phase_section"] = "found"
        declaration = _match_current_phase_declaration(current_section_text)
        if declaration:
            result["current_phase_id"] = declaration.phase_id
            # If the current phase is marked as "(completed)", it is
            # not in-progress — it is already captured in completed
            # above. A declaration with no status marker at all is
            # treated as not-completed (never guessed as completed).
            if not declaration.is_completed:
                result["in_progress"].append(f"{declaration.title} ({declaration.phase_id})")
        else:
            limitations.append(
                "## Current Phase section present but its phase-ID/title "
                "line did not parse -- current phase could not be identified"
            )
    else:
        limitations.append("no ## Current Phase section found -- no active phase state")

    # ── Planned: independently derived from the "Recommended next
    # [repo ]phase:" sentence, read *only* from within the "## Current
    # Phase" section's own bounded text (the actual latest phase's own
    # recommendation). Phase 134E.8: the whole-file fallback that used
    # to run when this sentence wasn't found in-section is removed --
    # that fallback (searching the entire, newest-first history for the
    # first matching sentence) is exactly what surfaced a Track-132-era
    # recommendation as "current" long after Track 132 completed. Its
    # absence is now disclosed via ``limitations`` instead.
    recommended: list[str] = []
    if current_section_text:
        for rec in _extract_recommended_next_phase_values(current_section_text):
            if rec not in recommended:
                recommended.append(rec)
        if not recommended:
            limitations.append(
                "current phase section has no explicit 'Recommended next "
                "phase' sentence -- no planned phase disclosed"
            )

    planned_display: list[str] = []
    planned_ids: list[str] = []
    for rec in recommended[:1]:
        # 137T: ID recognition delegates to the canonical parser
        # (CPIPC-001, CPIPC-REQ-018).
        rec_id = _leading_phase_token(rec)
        if rec_id and rec_id in completed_id_set:
            # Fail closed: never display a completed phase as planned,
            # even defensively, after the primary regex/fallback repair
            # above -- disclose the conflict instead of the stale claim.
            conflicts.append(
                f"recommended next phase {rec_id!r} is already completed -- "
                f"dropped from planned"
            )
            continue
        planned_display.append(rec)
        if rec_id:
            planned_ids.append(rec_id)

    result["planned"] = planned_display
    result["planned_phase_ids"] = sorted(set(planned_ids), key=phase_sort_key)

    # Phase 134E.10.1V.1 -- a completion report is certified before the
    # mutable lifecycle files are advanced.  Seal the intended
    # post-completion transition into the same snapshot instead of either
    # preserving the pre-transition state or regenerating after
    # certification.  This projection is a pure function of the already
    # resolved report identity/status/recommendation and the source snapshot.
    if completing_phase_id and report_status == "completed":
        parsed_completing = parse_phase_id(completing_phase_id)
        if parsed_completing is not None:
            if completing_phase_id not in completed_id_set:
                completed_phase_ids.append(completing_phase_id)
                completed_phase_ids.sort(key=phase_sort_key)
                completed_id_set.add(completing_phase_id)
                result["completed_phase_ids"] = completed_phase_ids

                chapter_id = str(parsed_completing[0])
                chapter = next(
                    (c for c in completed_chapters if c.get("chapter") == chapter_id),
                    None,
                )
                if chapter is None:
                    chapter = {
                        "chapter": chapter_id,
                        "label": completing_phase_name or completing_phase_id,
                        "phase_ids": [],
                    }
                    completed_chapters.append(chapter)
                    completed_chapters.sort(key=lambda c: int(c["chapter"]))
                    completed_labels.append(chapter["label"])
                chapter_ids = list(chapter.get("phase_ids") or [])
                chapter_ids.append(completing_phase_id)
                chapter["phase_ids"] = sorted(set(chapter_ids), key=phase_sort_key)

            if result.get("current_phase_id") == completing_phase_id:
                result["current_phase_id"] = ""
            result["in_progress"] = [
                item for item in result["in_progress"]
                if completing_phase_id.upper() not in str(item).upper()
            ]

            # The structured report recommendation is part of the frozen
            # transition input and therefore outranks pre-transition prose
            # for this projection.  It is never read from mutable state after
            # certification.
            projected_planned: list[str] = []
            projected_planned_ids: list[str] = []
            rec = recommended_next_phase.strip()
            if rec:
                # 137T: ID recognition delegates to the canonical parser
                # (CPIPC-001, CPIPC-REQ-018).
                rec_id = _leading_phase_token(rec) or ""
                if rec_id and rec_id in {pid.upper() for pid in completed_id_set}:
                    conflicts.append(
                        f"projected recommended next phase {rec_id!r} is already "
                        "completed -- dropped from planned"
                    )
                else:
                    projected_planned = [re.sub(r"^Phase\s+", "", rec, flags=re.I)]
                    if rec_id:
                        projected_planned_ids = [rec_id]
            result["planned"] = projected_planned
            result["planned_phase_ids"] = sorted(
                set(projected_planned_ids), key=phase_sort_key
            )
            result["source_provenance"]["lifecycle_projection"] = (
                f"completed:{completing_phase_id}"
            )

    # ── Derive from Runtime Snapshot ───────────────────────────────────
    try:
        from pcae.core.runtime_snapshot import build_runtime_snapshot
        from pcae.core.runtime_registry import RuntimeRegistry
        from pcae.core.paths import HarnessPath

        registry = RuntimeRegistry()
        snapshot = build_runtime_snapshot(HarnessPath.cwd(), registry)
        result["current_runtime_state"] = snapshot.health.current_runtime_state
        result["current_maximum_capability"] = snapshot.health.current_maximum_plugin_capability
        result["execution_availability"] = snapshot.health.execution_availability
        result["source_provenance"]["runtime_snapshot"] = "read"
    except Exception as exc:
        # Best-effort — if snapshot can't be built, leave fields empty
        # and disclose why rather than silently reusing stale values.
        result["source_provenance"]["runtime_snapshot"] = f"unavailable: {exc}"
        limitations.append("runtime snapshot unavailable -- runtime fields not derived")

    result["limitations"] = limitations
    result["conflicts"] = conflicts

    # ── Freshness ────────────────────────────────────────────────────
    if conflicts:
        result["freshness"] = FRESHNESS_INVALID
    elif limitations:
        result["freshness"] = FRESHNESS_FRESH_WITH_LIMITATIONS
    else:
        result["freshness"] = FRESHNESS_FRESH

    return result


def _extract_commit_count_from_summary(summary: str) -> int | None:
    """Extract governed commit count from summary text. Returns None if ambiguous."""
    import re as _re
    # Match patterns like "2 governed commits" or "3 governed commits"
    m = _re.search(r'(\d+)\s+governed\s+commit', summary)
    if m:
        return int(m.group(1))
    return None


def _classify_notification_outcome(
    *,
    notify_enabled: bool,
    sinks: list[Any],
    notification_results: list[Any] | None,
    notification_error: str | None,
) -> tuple[str, str]:
    """Classify a notification dispatch attempt into the Phase 113X.3
    outcome model. Returns ``(outcome, reason)`` -- ``reason`` is ``""``
    exactly when ``outcome == NOTIFICATION_OUTCOME_SENT``.

    Called only once sinks are known to exist and dispatch has been
    attempted (or raised); the "not enabled" / "no sinks configured"
    cases are handled by their own early returns in
    ``finalize_phase_report()`` before this is reached.
    """
    if not notify_enabled:
        return NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON, "PCAE_NOTIFY_ENABLED is not set to 1/true/yes"
    if not sinks:
        return NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON, "no notification sinks configured (PCAE_NOTIFY_SINKS)"
    if notification_error:
        return NOTIFICATION_OUTCOME_FAILED_WITH_REASON, notification_error
    if notification_results is None:
        return NOTIFICATION_OUTCOME_ATTEMPTED, "dispatch attempted but produced no results"
    if all(r.success for r in notification_results):
        return NOTIFICATION_OUTCOME_SENT, ""
    failed = [r for r in notification_results if not r.success]
    reason = "; ".join(f"{r.sink_name}: {r.message}" for r in failed)
    return NOTIFICATION_OUTCOME_FAILED_WITH_REASON, reason


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
    gate: dict[str, Any] | None = None,
    report_is_complete: bool | None = None,
    report_incomplete_reason: str = "",
    allow_pending_push: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a phase report artifact and optionally dispatch notifications.

    Called automatically on pcae phase complete.  Notification failure
    is non-fatal — phase finalization always completes.

    Returns a dict with:
      report: PhaseReport (the created report)
      paths: dict (written artifact paths)
      blocked: bool (Phase 113X.1 -- True if the finalization gate refused
        this report; ``paths`` then holds quarantine paths, never latest.*)
      blockers: list[str] (present when blocked)
      notification_results: list[NotificationResult] or None
      notification_skipped: bool
      notification_error: str or None
      notification_outcome: str (Phase 113X.3 -- one of
        NOTIFICATION_OUTCOME_ATTEMPTED/SENT/SKIPPED_WITH_REASON/
        FAILED_WITH_REASON; always present, so "was the operator told,
        and if not, why" is always answerable)
      notification_kind: str (Phase 113X.3 -- "complete", "partial_warning",
        or "none")

    Notifications are disabled by default.  Enable with:
      PCAE_NOTIFY_ENABLED=1
      PCAE_NOTIFY_SINKS=telegram,filesystem  (optional, default: filesystem)
      PCAE_NOTIFY_OUTPUT_DIR=.pcae/notifications  (default)

    Phase 113X.1 — finalization gate enforcement: when the caller passes
    the already-computed ``gate`` (from ``validate_finalization_gate()``)
    and it has blockers, the report is written to a quarantine path
    instead of ``latest.md``/``latest.json`` (113X Finding 1: previously
    the gate result was advisory-only for the write path -- a blocked
    report could still overwrite the canonical "latest" artifact with no
    persisted record of why it was blocked). ``gate=None`` (the default,
    used by existing callers/tests that don't pass it) preserves the
    prior unconditional-write behavior exactly. Blocked/quarantined
    reports remain fully silent (113X.1 semantics; not weakened here) --
    the notification guarantee below applies only when canonical
    latest.* artifacts are actually written.

    Phase 113X.3 — finalization notification guarantee: ``report_is_
    complete`` (default ``None``, preserving prior behavior exactly for
    callers that don't pass it -- notably ``pcae task finish --commit``,
    which remains a separate, unchanged, warning-only visibility path)
    lets the caller state whether this finalization is fully trust-
    complete. When ``False`` (finalized but partial -- canonical
    latest.* were still written, just not via the "blocked" branch
    above), a clearly-labeled WARNING notification is sent instead of
    the normal "Phase COMPLETED" one, carrying ``report_incomplete_
    reason`` -- closing the silent-Telegram gap 113X.2's own completion
    exposed. A finalized phase that updates canonical report artifacts
    is never simply silent: normal notification, warning notification,
    or an explicit recorded skip/failure reason are the only outcomes.
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
        # Phase 95I.1 — commit attribution tracking
        if kwargs.get("commit_attribution"):
            report.metadata["commit_attribution"] = kwargs["commit_attribution"]
        # Phase 149O.1R (B-149O.1R-2 repair) — carry the governed
        # `test_evidence_classification` metadata field through to the
        # object `validate_internal_report_coherence` actually reads.
        # Previously this field existed in
        # `.pcae/phase-completion-metadata.json` and was documented (Phase
        # 134E.9) as the only way to suppress a legitimate same-series
        # evidence citation, but neither this function nor its only
        # caller (`commands/phase.py`'s `_finalize_report_and_notify`)
        # ever read it from metadata or forwarded it here, so it was
        # always dropped before reaching the validator -- dead metadata.
        if kwargs.get("test_evidence_classification"):
            report.metadata["test_evidence_classification"] = kwargs["test_evidence_classification"]
        # Architecture Status is sealed by the caller before certification
        # whenever available. Reuse those exact bytes/facts through promotion
        # and delivery; never re-read mutable lifecycle sources after the
        # finalization snapshot has been certified.
        sealed_architecture_status = kwargs.get("architecture_status_snapshot")
        if isinstance(sealed_architecture_status, dict):
            report.architecture_status = json.loads(json.dumps(sealed_architecture_status))
        else:
            try:
                report.architecture_status = build_architecture_status(
                    completing_phase_id=phase_id,
                    completing_phase_name=phase_name,
                    report_status=status,
                    recommended_next_phase=recommended_next_phase,
                )
            except Exception:
                # Best-effort for legacy callers that do not seal a snapshot.
                pass
        report.metadata["phase_id"] = phase_id
        report.metadata["source_revision"] = report.architecture_status.get(
            "repository_revision", ""
        )

        # Phase 92D.5/92D.8 — Apply trust assessment with canonical report
        _apply_canonical_and_trust(report, phase_id, phase_name, status)

        # Phase 113X.1 — finalization gate enforcement: a blocked gate
        # quarantines the report instead of writing latest.md/latest.json.
        if gate is not None and not gate.get("finalizable", True):
            blockers = [str(b) for b in gate.get("blockers", [])]
            # Phase 137I.1 — finalization-ordering deadlock escape. When the
            # ONLY blockers are that this phase has not been pushed yet, and
            # the report is otherwise fully complete (identity, coherence,
            # governance, no-go, and every non-push trust field), write it to
            # the canonical latest.* slot in an explicitly NON-AUTHORITATIVE
            # "pending_push" state instead of quarantining it. This lets push
            # readiness's phase-report-identity gate (137F.1) be satisfied so
            # the governed push can proceed; a normal re-finalization after
            # the push promotes the report to COMPLETE and dispatches exactly
            # one notification. No trust gate is weakened: a pending report is
            # never trust-complete, never authoritative, and never notified
            # (see `blockers_are_push_state_only` for the closed blocker set),
            # and any genuine integrity blocker still quarantines below.
            if allow_pending_push and blockers_are_push_state_only(
                blockers, getattr(report, "missing_trust_fields", None)
            ):
                report.report_completeness = COMPLETENESS_PENDING_PUSH
                paths = write_phase_report(report, reports_dir)
                pending_reason = (
                    "report staged as PENDING push -- canonical latest.* "
                    "written for the phase-report-identity gate, but NOT "
                    "authoritative and NOT notified until pushed and "
                    "re-finalized"
                )
                report.notification_result = {
                    "dispatched": False, "sinks": [], "success": False,
                    "error": None,
                    "outcome": NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON,
                    "reason": pending_reason,
                    "kind": "pending",
                }
                _persist_notification_result(paths, report.notification_result)
                return {
                    "report": report,
                    "paths": paths,
                    "blocked": False,
                    "pending_push": True,
                    "blockers": blockers,
                    "notification_results": None,
                    "notification_skipped": True,
                    "notification_error": None,
                    "notification_outcome": NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON,
                    "notification_reason": pending_reason,
                    "notification_kind": "pending",
                    "report_error": None,
                }
            report.report_completeness = "blocked"
            paths = write_quarantined_report(report, reports_dir, blockers)
            return {
                "report": report,
                "paths": paths,
                "blocked": True,
                "blockers": blockers,
                "notification_results": None,
                "notification_skipped": True,
                "notification_error": None,
                # Phase 113X.3 — additive visibility only: quarantine
                # semantics (113X.1) are unchanged, still fully silent by
                # design (do not weaken quarantine semantics).
                "notification_outcome": NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON,
                "notification_reason": (
                    "report was quarantined by the finalization gate "
                    "(phase-identity/trust blocker) -- not eligible for "
                    "any notification"
                ),
                "notification_kind": "none",
                "report_error": None,
            }

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
    # Phase 113X.3 — is this finalization fully trust-complete? Callers
    # that don't state it explicitly (report_is_complete=None -- notably
    # `pcae task finish --commit`, and any bare pre-113X.3 caller) get
    # exactly the prior, unconditional "complete" event -- this function
    # never used to look at report.report_completeness to decide the
    # event kind at all, so deriving it from that field here would be a
    # silent behavior change for those callers, not a preservation of it.
    is_complete = True if report_is_complete is None else report_is_complete
    if not notify_enabled:
        skip_reason = "PCAE_NOTIFY_ENABLED is not set to 1/true/yes"
        report.notification_result = {
            "dispatched": False, "sinks": [], "success": False, "error": None,
            "outcome": NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON,
            "reason": skip_reason,
            "kind": "complete" if is_complete else "partial_warning",
        }
        _persist_notification_result(paths, report.notification_result)
        return {
            "report": report,
            "paths": paths,
            "notification_results": None,
            "notification_skipped": True,
            "notification_error": None,
            "notification_outcome": NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON,
            "notification_reason": skip_reason,
            "notification_kind": "complete" if is_complete else "partial_warning",
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
        phase_report_to_partial_warning_notification_event,
        NotificationSink,
    )

    # Use timestamped markdown path for attachment — guarantees the current
    # phase report is attached (not a stale latest.md if write order changed).
    report_path = paths.get("markdown", paths.get("latest_markdown", ""))
    artifact_paths = [str(report_path)] if report_path else []

    # Phase 113X.3 — a finalized-but-partial report (canonical latest.*
    # were written; not the blocked/quarantined branch above) gets a
    # clearly-labeled WARNING event, never the normal "Phase COMPLETED"
    # one -- 105D's rule that partial reports are never sent as normal
    # final reports is preserved by construction (different event, not
    # a suppressed one).
    notification_kind = "complete" if is_complete else "partial_warning"
    if is_complete:
        event = phase_report_to_notification_event(report, artifact_paths=artifact_paths)
    else:
        event = phase_report_to_partial_warning_notification_event(
            report,
            reason=report_incomplete_reason or "report trust is incomplete",
            artifact_paths=artifact_paths,
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
    if not sinks:
        skip_reason = "no notification sinks configured (PCAE_NOTIFY_SINKS)"
        report.notification_result = {
            "dispatched": False, "sinks": [], "success": False, "error": None,
            "outcome": NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON,
            "reason": skip_reason, "kind": notification_kind,
        }
        _persist_notification_result(paths, report.notification_result)
        return {
            "report": report,
            "paths": paths,
            "notification_results": None,
            "notification_skipped": True,
            "notification_error": None,
            "notification_outcome": NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON,
            "notification_reason": skip_reason,
            "notification_kind": notification_kind,
            "report_error": None,
        }

    try:
        notification_results = dispatch(event, sinks)
    except Exception as exc:
        notification_error = str(exc)

    # Phase 113X.3 — single canonical outcome classification, one of
    # NOTIFICATION_OUTCOME_{ATTEMPTED,SENT,SKIPPED_WITH_REASON,
    # FAILED_WITH_REASON}. Always recorded, so "was the operator told,
    # and if not, why" never depends on reading console output alone.
    outcome, outcome_reason = _classify_notification_outcome(
        notify_enabled=True, sinks=sinks,
        notification_results=notification_results, notification_error=notification_error,
    )

    # Phase 92D.5 — Store notification result in report
    report_sinks = [r.sink_name for r in notification_results] if notification_results else []
    report_ok = all(r.success for r in notification_results) if notification_results else False
    report.notification_result = {
        "dispatched": notification_results is not None,
        "sinks": report_sinks,
        "success": report_ok,
        "error": notification_error,
        "outcome": outcome,
        "reason": outcome_reason,
        "kind": notification_kind,
    }
    _persist_notification_result(paths, report.notification_result)

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
        "notification_outcome": outcome,
        "notification_reason": outcome_reason if outcome != NOTIFICATION_OUTCOME_SENT else "",
        "notification_kind": notification_kind,
        "report_error": None,
    }
