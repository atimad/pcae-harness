"""Phase 105A — Phase Report Trust Gate Implementation.

Non-executing, non-authorizing. Pure validation logic for phase completion
report trust. Detects missing required fields, disallowed placeholders,
and classifies reports as complete/partial/invalid.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

# ═══════════════════════════════════════════════════════════════════════════
# Required Field Definitions
# ═══════════════════════════════════════════════════════════════════════════

REQUIRED_REPORT_FIELDS: tuple[str, ...] = (
    "phase_id",
    "status",
    "files_changed",
    "tests_run",
    "commits",
    "pushed",
    "summary",
    "recommended_next_phase",
)

REQUIRED_GOVERNANCE_FIELDS: tuple[str, ...] = (
    "pcae_health",
    "pcae_check",
    "pcae_doctor_task_memory",
    "pcae_push_check",
    "telegram_runtime",
)

REQUIRED_TEST_FIELDS: tuple[str, ...] = (
    "report_notification_tests",
    "bootstrap_session_reporting_tests",
    "fast_green",
)

DISALLOWED_PLACEHOLDER_VALUES: tuple[str, ...] = (
    "TBD",
    "pending",
    "not captured",
    "unknown",
)

COMPLETENESS_COMPLETE = "complete"
COMPLETENESS_PARTIAL = "partial"
COMPLETENESS_INVALID = "invalid"

ISSUE_TYPE_MISSING = "missing_field"
ISSUE_TYPE_PLACEHOLDER = "placeholder"
ISSUE_TYPE_EMPTY = "empty_value"


@dataclass(frozen=False)
class PhaseReportTrustIssue:
    field: str
    issue_type: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "issue_type": self.issue_type, "detail": self.detail}


@dataclass(frozen=False)
class PhaseReportTrustResult:
    complete: bool = False
    status: str = COMPLETENESS_INVALID
    missing_fields: list[str] = field(default_factory=list)
    placeholder_fields: list[str] = field(default_factory=list)
    empty_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    all_issues: list[PhaseReportTrustIssue] = field(default_factory=list)
    repair_required: bool = True
    can_be_active_latest: bool = False
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "complete": self.complete,
            "status": self.status,
            "missing_fields": sorted(self.missing_fields),
            "placeholder_fields": sorted(self.placeholder_fields),
            "empty_fields": sorted(self.empty_fields),
            "warnings": list(self.warnings),
            "repair_required": self.repair_required,
            "can_be_active_latest": self.can_be_active_latest,
            "summary": self.summary,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Validation Logic
# ═══════════════════════════════════════════════════════════════════════════

def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return True
        if stripped in DISALLOWED_PLACEHOLDER_VALUES:
            return True
    return False


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return True
    return False


def validate_phase_report_trust(report: Mapping[str, Any]) -> PhaseReportTrustResult:
    """Validate a candidate phase report for trust completeness.

    Non-executing. Non-authorizing. Pure validation.
    """
    issues: list[PhaseReportTrustIssue] = []

    # ── Required top-level fields ──
    for field in REQUIRED_REPORT_FIELDS:
        value = report.get(field)
        if _is_empty(value):
            issues.append(PhaseReportTrustIssue(field, ISSUE_TYPE_MISSING, f"{field} is missing or empty"))
        elif _is_placeholder(value):
            issues.append(PhaseReportTrustIssue(field, ISSUE_TYPE_PLACEHOLDER, f"{field} has disallowed placeholder: {value!r}"))

    # ── Required governance fields ──
    gov = report.get("governance_results")
    if isinstance(gov, Mapping):
        for field in REQUIRED_GOVERNANCE_FIELDS:
            value = gov.get(field)
            if _is_empty(value):
                issues.append(PhaseReportTrustIssue(f"governance_results.{field}", ISSUE_TYPE_MISSING, f"governance_results.{field} is missing or empty"))
            elif _is_placeholder(value):
                issues.append(PhaseReportTrustIssue(f"governance_results.{field}", ISSUE_TYPE_PLACEHOLDER, f"governance_results.{field} has disallowed placeholder: {value!r}"))
    else:
        for field in REQUIRED_GOVERNANCE_FIELDS:
            issues.append(PhaseReportTrustIssue(f"governance_results.{field}", ISSUE_TYPE_MISSING, "governance_results is missing (not a Mapping)"))

    # ── Required test fields ──
    tests = report.get("test_results")
    if isinstance(tests, Mapping):
        for field in REQUIRED_TEST_FIELDS:
            value = tests.get(field)
            if _is_empty(value):
                issues.append(PhaseReportTrustIssue(f"test_results.{field}", ISSUE_TYPE_MISSING, f"test_results.{field} is missing or empty"))
            elif _is_placeholder(value):
                issues.append(PhaseReportTrustIssue(f"test_results.{field}", ISSUE_TYPE_PLACEHOLDER, f"test_results.{field} has disallowed placeholder: {value!r}"))
    else:
        for field in REQUIRED_TEST_FIELDS:
            issues.append(PhaseReportTrustIssue(f"test_results.{field}", ISSUE_TYPE_MISSING, "test_results is missing (not a Mapping)"))

    # ── Stale recommendation check ──
    rec = str(report.get("recommended_next_phase", ""))
    if rec and "Recommends 102D" in rec:
        issues.append(PhaseReportTrustIssue("recommended_next_phase", ISSUE_TYPE_PLACEHOLDER, "stale recommendation wording detected"))

    # ── Commits TBD check ──
    commits = report.get("commits")
    if isinstance(commits, str) and commits.strip() == "TBD":
        issues.append(PhaseReportTrustIssue("commits", ISSUE_TYPE_PLACEHOLDER, "commits is TBD"))
    elif isinstance(commits, (list, tuple)) and len(commits) == 0:
        issues.append(PhaseReportTrustIssue("commits", ISSUE_TYPE_EMPTY, "commits is empty list"))

    # ── Compose result ──
    missing = [i.field for i in issues if i.issue_type == ISSUE_TYPE_MISSING]
    placeholders = [i.field for i in issues if i.issue_type == ISSUE_TYPE_PLACEHOLDER]
    empties = [i.field for i in issues if i.issue_type == ISSUE_TYPE_EMPTY]

    has_critical = len(missing) > 0
    has_placeholder = len(placeholders) > 0

    if has_critical:
        status = COMPLETENESS_INVALID
    elif has_placeholder:
        status = COMPLETENESS_PARTIAL
    else:
        status = COMPLETENESS_COMPLETE

    result = PhaseReportTrustResult(
        complete=(status == COMPLETENESS_COMPLETE),
        status=status,
        missing_fields=missing,
        placeholder_fields=placeholders,
        empty_fields=empties,
        all_issues=issues,
        repair_required=has_critical or has_placeholder,
        can_be_active_latest=(status == COMPLETENESS_COMPLETE),
    )

    if has_critical:
        result.summary = f"Report is INVALID: {len(missing)} missing field(s). Repair required."
    elif has_placeholder:
        result.summary = f"Report is PARTIAL: {len(placeholders)} placeholder(s). Repair required."
    else:
        result.summary = "Report is COMPLETE. All trust fields present."

    if not has_critical and not has_placeholder:
        result.warnings.append("No missing or placeholder fields detected.")

    return result


def adapt_report_for_trust_check(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a raw report/metadata JSON mapping into the shape expected
    by :func:`validate_phase_report_trust`.

    Phase 105B — bridges two report schemas that evolved independently in
    this codebase: the durable ``PhaseReport`` artifact
    (``core/phase_reports.py``, e.g. ``.pcae/phase-reports/latest.json``)
    and the pre-completion ``.pcae/phase-completion-metadata.json`` draft.
    Field name differences (``pushed_status`` vs ``pushed``,
    ``files_changed_count`` vs ``files_changed``, ``phase_commits`` vs
    ``commits``) and shape differences (``governance_results``/
    ``test_results`` as a list of ``{"name", "status"}`` records vs a
    mapping) are reconciled here. Read-only, pure, no I/O.
    """
    out: dict[str, Any] = dict(raw)

    if not out.get("pushed") and out.get("pushed_status"):
        out["pushed"] = out["pushed_status"]

    if not out.get("files_changed") and out.get("files_changed_count"):
        out["files_changed"] = out["files_changed_count"]

    if not out.get("commits") and out.get("phase_commits"):
        out["commits"] = [
            c.get("hash", "")[:8]
            for c in out["phase_commits"]
            if isinstance(c, Mapping) and c.get("hash")
        ]

    if not out.get("tests_run") and out.get("tests_added_or_updated"):
        match = re.match(r"\s*(\d+)", str(out["tests_added_or_updated"]))
        if match:
            out["tests_run"] = int(match.group(1))

    for key in ("governance_results", "test_results"):
        value = out.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            out[key] = {
                item.get("name", ""): item.get("status", item.get("result", ""))
                for item in value
                if isinstance(item, Mapping) and item.get("name")
            }

    return out


def select_active_phase_report(
    reports: Sequence[Mapping[str, Any]],
    phase_id: str | None = None,
) -> tuple[Mapping[str, Any] | None, PhaseReportTrustResult | None]:
    """Select the active/latest complete report for a given phase.

    Returns (selected_report, validation_result).
    selected_report is None if no suitable report found.
    """
    # Filter by phase_id if provided
    candidates = list(reports)
    if phase_id:
        candidates = [r for r in candidates if str(r.get("phase_id", "")) == phase_id]

    if not candidates:
        return None, None

    # Score each candidate
    scored: list[tuple[Mapping[str, Any], PhaseReportTrustResult]] = []
    for r in candidates:
        v = validate_phase_report_trust(r)
        scored.append((r, v))

    # Prefer complete reports
    completes = [(r, v) for r, v in scored if v.complete]
    if completes:
        return completes[-1]  # last complete in input order (stable)

    # Fall back to latest partial with repair guidance
    partials = [(r, v) for r, v in scored if v.status == COMPLETENESS_PARTIAL]
    if partials:
        latest = partials[-1]
        latest[1].can_be_active_latest = False
        latest[1].repair_required = True
        return latest

    # Nothing usable
    return None, scored[-1][1] if scored else None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 105D — Push-state gate (originally 105C.1, promoted to shared core)
# ═══════════════════════════════════════════════════════════════════════════

# Fields the OLD (95M.1, `core/phase_reports.py`) report-trust schema uses to
# signal that final push state (push status / origin-ahead-count / push
# check) is not yet known. This (105A/105B) schema does not check these
# semantically on its own — a `pushed_status` of "not_pushed" is a valid
# non-placeholder string, so it alone reports "complete". Folding these into
# a trust result via `apply_push_state_gate` is what prevents a pre-push
# report from being treated as a final, dispatch-ready trusted handoff.
PUSH_STATE_FIELDS: tuple[str, ...] = (
    "pushed_status",
    "origin_main_head",
    "governance_results.pcae_push_check",
)


def apply_push_state_gate(
    trust_result: PhaseReportTrustResult,
    missing_trust_fields: Sequence[str] | None,
) -> None:
    """Downgrade a trust result to partial when the OLD schema's push-state
    fields (e.g. `PhaseReport.missing_trust_fields`) show final push state is
    still pending. Mutates `trust_result` in place. No-op if
    `missing_trust_fields` is empty/None or contains no push-state fields.
    """
    if not missing_trust_fields:
        return
    pending = [f for f in missing_trust_fields if f in PUSH_STATE_FIELDS]
    if not pending:
        return
    trust_result.missing_fields = sorted(set(trust_result.missing_fields) | set(pending))
    trust_result.complete = False
    trust_result.can_be_active_latest = False
    trust_result.repair_required = True
    if trust_result.status == COMPLETENESS_COMPLETE:
        trust_result.status = COMPLETENESS_PARTIAL
    trust_result.summary = (
        f"Report is PARTIAL: final push state pending ({', '.join(pending)}). "
        "Repair required."
    )


def apply_old_schema_gate(
    trust_result: PhaseReportTrustResult,
    gate: Mapping[str, Any] | None,
) -> None:
    """Downgrade a trust result to incomplete when the OLD (95M.1)
    finalization gate (`core.phase_reports.validate_finalization_gate`)
    found blockers the 105A/105B schema alone does not catch — e.g.
    `files_changed<=0`, an insufficient no-go confirmation count.

    Phase 106H: closes the `pcae task finish --commit` /
    `pcae phase complete` trust-gate asymmetry found in Phase 106G's
    audit, by giving both call sites a single shared function to fold the
    OLD schema's full completeness check into the 105A/105B result, the
    same way `apply_push_state_gate` already folds in push-state fields.
    Mutates `trust_result` in place. No-op if `gate` is None or the gate
    is already finalizable.
    """
    if not gate or gate.get("finalizable", True):
        return
    blockers = [str(b) for b in gate.get("blockers", [])]
    trust_result.missing_fields = sorted(
        set(trust_result.missing_fields) | {f"old_schema_gate: {b}" for b in blockers}
    )
    trust_result.complete = False
    trust_result.can_be_active_latest = False
    trust_result.repair_required = True
    if trust_result.status == COMPLETENESS_COMPLETE:
        trust_result.status = COMPLETENESS_PARTIAL
    trust_result.summary = (
        f"Report is PARTIAL: OLD (95M.1) finalization gate found "
        f"{len(blockers)} blocker(s). Repair required."
    )


def compute_final_trust(
    report: Mapping[str, Any],
    *,
    push_state_aware: bool = True,
    old_schema_missing_fields: Sequence[str] | None = None,
) -> PhaseReportTrustResult:
    """Compute the combined trust result used for dispatch/hard-fail
    decisions (Phase 105D). Adapts and validates `report` with the 105A/105B
    validator, then optionally folds in the OLD schema's push-state fields.

    `old_schema_missing_fields` should be the OLD (95M.1) schema's
    `missing_trust_fields` list when available (e.g. `PhaseReport.
    missing_trust_fields`, or a loaded report dict's `"missing_trust_fields"`
    key) — the 105A/105B schema alone cannot detect push-state pendingness.
    """
    trust_result = validate_phase_report_trust(adapt_report_for_trust_check(report))
    if push_state_aware:
        fields = old_schema_missing_fields
        if fields is None and isinstance(report, Mapping):
            fields = report.get("missing_trust_fields")
        apply_push_state_gate(trust_result, fields)
    return trust_result
