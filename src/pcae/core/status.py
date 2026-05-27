from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.paths import HarnessPath
from pcae.core.policy import load_policy
from pcae.core.provenance import PROVENANCE_HISTORY_RELATIVE_PATH
from pcae.core.session import read_session_snapshot
from pcae.core.tasks import find_latest_active_task


PROJECT_STATUS_RELATIVE_PATH = Path("PROJECT_STATUS.md")
ROADMAP_RELATIVE_PATHS = (
    PROJECT_STATUS_RELATIVE_PATH,
    Path("tasks") / "TODO.md",
)

# Phrases known to be stale because the features they describe are already
# implemented. Stale roadmap references in governance documents create
# orchestration risk: agents read them as forward-looking guidance and
# attempt to implement work that has already been done.
KNOWN_STALE_PHRASES: tuple[str, ...] = (
    "Implement `pcae end`",
    "Implement `pcae session end`",
    "Full governance audit: `pcae governance audit` command",
)


@dataclass(frozen=True)
class CoherenceWarning:
    document: str
    message: str

    def to_dict(self) -> dict:
        return {"document": self.document, "message": self.message}


@dataclass(frozen=True)
class CoherenceResult:
    warnings: tuple[CoherenceWarning, ...]

    @property
    def coherent(self) -> bool:
        return len(self.warnings) == 0

    def to_dict(self) -> dict:
        return {
            "coherent": self.coherent,
            "warning_count": len(self.warnings),
            "warnings": [w.to_dict() for w in self.warnings],
        }


@dataclass(frozen=True)
class GovernanceAuditCheck:
    name: str
    passed: bool
    message: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass(frozen=True)
class GovernanceAuditSummary:
    check_count: int
    passed_count: int
    failed_count: int
    warning_count: int
    status: str

    def to_dict(self) -> dict:
        return {
            "check_count": self.check_count,
            "failed_count": self.failed_count,
            "passed_count": self.passed_count,
            "status": self.status,
            "warning_count": self.warning_count,
        }


@dataclass(frozen=True)
class GovernanceAuditResult:
    checks: tuple[GovernanceAuditCheck, ...]
    warnings: tuple[CoherenceWarning, ...]
    summary: GovernanceAuditSummary

    @property
    def valid(self) -> bool:
        return self.summary.status == "valid"

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "checks": [check.to_dict() for check in self.checks],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "summary": self.summary.to_dict(),
        }


def check_project_status_coherence(root: HarnessPath) -> CoherenceResult:
    """Return coherence warnings for PROJECT_STATUS.md stale roadmap references."""
    path = root.join(PROJECT_STATUS_RELATIVE_PATH)
    if not path.is_file():
        return CoherenceResult(
            warnings=(
                CoherenceWarning(
                    document=str(PROJECT_STATUS_RELATIVE_PATH),
                    message="PROJECT_STATUS.md not found",
                ),
            )
        )
    text = path.read_text(encoding="utf-8")
    warnings = []
    for phrase in KNOWN_STALE_PHRASES:
        if phrase in text:
            warnings.append(
                CoherenceWarning(
                    document=str(PROJECT_STATUS_RELATIVE_PATH),
                    message=f"Stale roadmap reference: {phrase!r} — feature already implemented.",
                )
            )
    return CoherenceResult(warnings=tuple(warnings))


def audit_governance_coherence(root: HarnessPath) -> GovernanceAuditResult:
    """Return a lightweight read-only governance coherence audit."""
    checks = [
        check_project_status_current_phase(root),
        check_project_status_next_section(root),
        check_active_task_readable(root),
        check_session_continuity_available(root),
        check_provenance_history_exists(root),
        check_policy_parses(root),
        check_agent_registry_non_empty(root),
    ]
    warnings = find_stale_roadmap_references(root)
    passed_count = sum(1 for check in checks if check.passed)
    failed_count = len(checks) - passed_count
    status = "valid" if failed_count == 0 and len(warnings) == 0 else "warnings"
    if failed_count > 0:
        status = "invalid"
    return GovernanceAuditResult(
        checks=tuple(checks),
        warnings=warnings,
        summary=GovernanceAuditSummary(
            check_count=len(checks),
            passed_count=passed_count,
            failed_count=failed_count,
            warning_count=len(warnings),
            status=status,
        ),
    )


def check_project_status_current_phase(root: HarnessPath) -> GovernanceAuditCheck:
    text = read_project_status_text(root)
    if text is None:
        return GovernanceAuditCheck(
            name="project_status_current_phase",
            passed=False,
            message="PROJECT_STATUS.md not found.",
        )
    phase = read_markdown_section_text(text, "Current Phase")
    if phase is None:
        return GovernanceAuditCheck(
            name="project_status_current_phase",
            passed=False,
            message="PROJECT_STATUS.md Current Phase section is missing or empty.",
        )
    return GovernanceAuditCheck(
        name="project_status_current_phase",
        passed=True,
        message=f"Current phase: {first_line(phase)}",
    )


def check_project_status_next_section(root: HarnessPath) -> GovernanceAuditCheck:
    text = read_project_status_text(root)
    if text is None:
        return GovernanceAuditCheck(
            name="project_status_next",
            passed=False,
            message="PROJECT_STATUS.md not found.",
        )
    next_text = read_markdown_section_text(text, "Next")
    if next_text is None:
        return GovernanceAuditCheck(
            name="project_status_next",
            passed=False,
            message="PROJECT_STATUS.md Next section is missing or empty.",
        )
    return GovernanceAuditCheck(
        name="project_status_next",
        passed=True,
        message=f"Next: {first_line(next_text)}",
    )


def check_active_task_readable(root: HarnessPath) -> GovernanceAuditCheck:
    try:
        active_task = find_latest_active_task(root)
    except OSError as error:
        return GovernanceAuditCheck(
            name="active_task",
            passed=False,
            message=f"Active task could not be read: {error}",
        )
    if active_task is None:
        return GovernanceAuditCheck(
            name="active_task",
            passed=False,
            message="No active task contract found in tasks/active/.",
        )
    return GovernanceAuditCheck(
        name="active_task",
        passed=True,
        message=f"Active task: {active_task.task_id}",
    )


def check_session_continuity_available(root: HarnessPath) -> GovernanceAuditCheck:
    try:
        snapshot = read_session_snapshot(root)
    except (OSError, ValueError) as error:
        return GovernanceAuditCheck(
            name="session_continuity",
            passed=False,
            message=f"Session continuity status is unavailable: {error}",
        )
    if snapshot is None:
        return GovernanceAuditCheck(
            name="session_continuity",
            passed=False,
            message="Session snapshot missing at .pcae/session.json.",
        )
    return GovernanceAuditCheck(
        name="session_continuity",
        passed=True,
        message="Session continuity status is available.",
    )


def check_provenance_history_exists(root: HarnessPath) -> GovernanceAuditCheck:
    if root.join(PROVENANCE_HISTORY_RELATIVE_PATH).is_file():
        return GovernanceAuditCheck(
            name="provenance_history",
            passed=True,
            message=".pcae/provenance-history.json exists.",
        )
    return GovernanceAuditCheck(
        name="provenance_history",
        passed=False,
        message=".pcae/provenance-history.json is missing.",
    )


def check_policy_parses(root: HarnessPath) -> GovernanceAuditCheck:
    policy = load_policy(root)
    if policy.valid:
        return GovernanceAuditCheck(
            name="policy_configuration",
            passed=True,
            message=f"Policy parses successfully ({policy.source}).",
        )
    return GovernanceAuditCheck(
        name="policy_configuration",
        passed=False,
        message=policy.error or "Policy configuration is invalid.",
    )


def check_agent_registry_non_empty(root: HarnessPath) -> GovernanceAuditCheck:
    policy = load_policy(root)
    if not policy.valid:
        return GovernanceAuditCheck(
            name="agent_registry",
            passed=False,
            message=policy.error or "Agent registry unavailable because policy is invalid.",
        )
    if not policy.agent_registry:
        return GovernanceAuditCheck(
            name="agent_registry",
            passed=False,
            message="Agent registry is empty.",
        )
    return GovernanceAuditCheck(
        name="agent_registry",
        passed=True,
        message=f"Agent registry contains {len(policy.agent_registry)} agent(s).",
    )


def find_stale_roadmap_references(root: HarnessPath) -> tuple[CoherenceWarning, ...]:
    warnings: list[CoherenceWarning] = []
    for relative_path in ROADMAP_RELATIVE_PATHS:
        path = root.join(relative_path)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in KNOWN_STALE_PHRASES:
            if phrase in text:
                warnings.append(
                    CoherenceWarning(
                        document=relative_path.as_posix(),
                        message=(
                            f"Stale roadmap reference: {phrase!r} "
                            "— feature already implemented."
                        ),
                    )
                )
    return tuple(warnings)


def read_project_status_text(root: HarnessPath) -> str | None:
    path = root.join(PROJECT_STATUS_RELATIVE_PATH)
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def read_markdown_section_text(content: str, section_name: str) -> str | None:
    lines = content.splitlines()
    values: list[str] = []
    in_section = False
    target = f"## {section_name}"

    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line.strip() == target
            continue
        if in_section and line.strip():
            values.append(line.strip())

    if not values:
        return None
    return "\n".join(values)


def first_line(text: str) -> str:
    return text.splitlines()[0]
