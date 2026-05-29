from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatch
import json
from pathlib import Path
import re

from pcae.core.git_status import GitChange, read_git_branch, read_git_changes
from pcae.core.paths import HarnessPath


ARCHITECTURE_HISTORY_RELATIVE_PATH = Path(".pcae") / "architecture-history.json"


@dataclass(frozen=True)
class ArchitectureDependencyWarning:
    path: Path
    source_zone: str
    target_zone: str

    @property
    def text(self) -> str:
        return (
            f"{self.path.as_posix()}: {self.source_zone} -> {self.target_zone} "
            "is not allowed by policy"
        )


@dataclass(frozen=True)
class ArchitectureParseWarning:
    path: Path
    reason: str

    @property
    def text(self) -> str:
        return f"{self.path.as_posix()}: {self.reason}"


@dataclass(frozen=True)
class ArchitectureAnalysisResult:
    dependency_warnings: tuple[ArchitectureDependencyWarning, ...]
    parse_warnings: tuple[ArchitectureParseWarning, ...]


@dataclass(frozen=True)
class ArchitectureHistorySnapshot:
    relative_path: Path
    entry: dict
    entries: tuple[dict, ...]


@dataclass(frozen=True)
class ArchitectureHistorySummary:
    relative_path: Path
    entries: tuple[dict, ...]
    latest: dict


@dataclass(frozen=True)
class ArchitectureDriftMetrics:
    total_snapshots: int
    latest_dependency_warnings: int
    max_dependency_warnings: int
    average_dependency_warnings: float
    snapshots_with_warnings: int
    most_frequently_touched_zone: str | None
    latest_enforcement_mode: str
    latest_session_continuity: str


def write_architecture_history_snapshot(
    root: HarnessPath,
    check_result,
    created_at: datetime | None = None,
) -> ArchitectureHistorySnapshot:
    timestamp = created_at or datetime.now(timezone.utc)
    entry = build_architecture_history_entry(root, check_result, timestamp)
    entries = read_architecture_history(root) + (entry,)
    target = root.join(ARCHITECTURE_HISTORY_RELATIVE_PATH)

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(list(entries), file, indent=2, sort_keys=True)
        file.write("\n")

    return ArchitectureHistorySnapshot(
        relative_path=ARCHITECTURE_HISTORY_RELATIVE_PATH,
        entry=entry,
        entries=entries,
    )


def build_architecture_history_entry(
    root: HarnessPath,
    check_result,
    timestamp: datetime,
) -> dict:
    changes = read_git_changes(root)
    active_task = None
    if check_result.active_task_id is not None:
        active_task = {
            "id": check_result.active_task_id,
            "title": check_result.active_task_title,
        }

    return {
        "active_task": active_task,
        "architecture_zones_touched": {
            zone.name: zone.file_count
            for zone in check_result.architecture_zones_touched
        },
        "changed_files_count": len(changes),
        "dependency_warnings_count": len(check_result.architecture_dependency_warnings),
        "enforcement_mode": check_result.architecture_enforcement_mode,
        "git_branch": read_git_branch(root),
        "session_continuity": session_continuity_status(check_result),
        "timestamp": timestamp.isoformat(),
    }


def read_architecture_history(root: HarnessPath) -> tuple[dict, ...]:
    target = root.join(ARCHITECTURE_HISTORY_RELATIVE_PATH)
    if not target.is_file():
        return ()

    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return ()
    return tuple(entry for entry in data if isinstance(entry, dict))


def read_architecture_history_summary(root: HarnessPath) -> ArchitectureHistorySummary:
    target = root.join(ARCHITECTURE_HISTORY_RELATIVE_PATH)
    if not target.is_file():
        raise ValueError("No architecture history found at .pcae/architecture-history.json.")

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid architecture history JSON: {error.msg}.") from error

    if not isinstance(data, list):
        raise ValueError("Invalid architecture history: expected a list of entries.")
    entries = tuple(entry for entry in data if isinstance(entry, dict))
    if not entries:
        raise ValueError("Invalid architecture history: no entries found.")

    return ArchitectureHistorySummary(
        relative_path=ARCHITECTURE_HISTORY_RELATIVE_PATH,
        entries=entries,
        latest=entries[-1],
    )


def calculate_architecture_drift_metrics(
    summary: ArchitectureHistorySummary,
) -> ArchitectureDriftMetrics:
    warning_counts = tuple(
        integer_value(entry.get("dependency_warnings_count"))
        for entry in summary.entries
    )
    zone_counts: dict[str, int] = {}
    for entry in summary.entries:
        zones = entry.get("architecture_zones_touched")
        if not isinstance(zones, dict):
            continue
        for zone_name, count in zones.items():
            if not isinstance(zone_name, str):
                continue
            zone_counts[zone_name] = zone_counts.get(zone_name, 0) + integer_value(count)

    most_frequently_touched_zone = None
    if zone_counts:
        most_frequently_touched_zone = sorted(
            zone_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[0][0]

    latest = summary.latest
    total_snapshots = len(summary.entries)
    latest_dependency_warnings = warning_counts[-1]
    return ArchitectureDriftMetrics(
        total_snapshots=total_snapshots,
        latest_dependency_warnings=latest_dependency_warnings,
        max_dependency_warnings=max(warning_counts),
        average_dependency_warnings=sum(warning_counts) / total_snapshots,
        snapshots_with_warnings=sum(1 for count in warning_counts if count > 0),
        most_frequently_touched_zone=most_frequently_touched_zone,
        latest_enforcement_mode=string_value(latest.get("enforcement_mode")),
        latest_session_continuity=string_value(latest.get("session_continuity")),
    )


def integer_value(value) -> int:
    if isinstance(value, int):
        return value
    return 0


def string_value(value) -> str:
    if isinstance(value, str) and value:
        return value
    return "unknown"


def session_continuity_status(check_result) -> str:
    if any("Session continuity verified." in info.text for info in check_result.infos):
        return "verified"
    if any(
        "Session snapshot missing" in warning.text
        for warning in check_result.warnings
    ):
        return "missing"
    if any(
        "Session active task does not match current active task" in violation.text
        for violation in check_result.violations
    ):
        return "mismatch"
    if any("Invalid session JSON" in violation.text for violation in check_result.violations):
        return "invalid"
    return "unknown"


def analyze_changed_python_dependencies(
    root: HarnessPath,
    changes: tuple[GitChange, ...],
    architecture_zones: dict[str, tuple[str, ...]],
    architecture_rules: dict[str, tuple[str, ...]],
    forbidden_dependencies: tuple[tuple[str, str], ...] = (),
) -> ArchitectureAnalysisResult:
    if not architecture_rules and not forbidden_dependencies:
        return ArchitectureAnalysisResult(dependency_warnings=(), parse_warnings=())

    dependency_warnings: list[ArchitectureDependencyWarning] = []
    parse_warnings: list[ArchitectureParseWarning] = []

    for change in changes:
        if change.path.suffix != ".py":
            continue

        source_zones = zones_for_path(change.path, architecture_zones)
        if not source_zones:
            continue

        source_path = root.join(change.path)
        try:
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            parse_warnings.append(
                ArchitectureParseWarning(
                    path=change.path,
                    reason=f"Could not parse Python imports: {error}",
                )
            )
            continue

        for module_name in imported_modules(tree):
            target_path = local_module_path(root, module_name)
            if target_path is None:
                continue
            target_zones = zones_for_path(target_path, architecture_zones)
            if not target_zones:
                continue
            dependency_warnings.extend(
                disallowed_dependencies(
                    change.path,
                    source_zones,
                    target_zones,
                    architecture_rules,
                    forbidden_dependencies,
                )
            )

    return ArchitectureAnalysisResult(
        dependency_warnings=tuple(deduplicate_dependency_warnings(dependency_warnings)),
        parse_warnings=tuple(parse_warnings),
    )


def imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            if node.module is None:
                continue
            modules.append(node.module)
            modules.extend(
                f"{node.module}.{alias.name}"
                for alias in node.names
                if alias.name != "*"
            )
    return tuple(modules)


def local_module_path(root: HarnessPath, module_name: str) -> Path | None:
    if not module_name.startswith("pcae."):
        return None

    module_parts = module_name.split(".")
    module_path = Path("src").joinpath(*module_parts).with_suffix(".py")
    if root.join(module_path).is_file():
        return module_path

    package_path = Path("src").joinpath(*module_parts) / "__init__.py"
    if root.join(package_path).is_file():
        return package_path

    return None


def zones_for_path(path: Path, zones: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    return tuple(
        zone_name
        for zone_name, patterns in zones.items()
        if path_matches_any(path, patterns)
    )


def disallowed_dependencies(
    path: Path,
    source_zones: tuple[str, ...],
    target_zones: tuple[str, ...],
    architecture_rules: dict[str, tuple[str, ...]],
    forbidden_dependencies: tuple[tuple[str, str], ...] = (),
) -> tuple[ArchitectureDependencyWarning, ...]:
    warnings: list[ArchitectureDependencyWarning] = []
    for source_zone in source_zones:
        allowed_targets = architecture_rules.get(source_zone, ())
        for target_zone in target_zones:
            if dependency_is_forbidden(
                source_zone,
                target_zone,
                forbidden_dependencies,
            ):
                warnings.append(
                    ArchitectureDependencyWarning(
                        path=path,
                        source_zone=source_zone,
                        target_zone=target_zone,
                    )
                )
                continue
            if "*" in allowed_targets:
                continue
            if target_zone in allowed_targets:
                continue
            warnings.append(
                ArchitectureDependencyWarning(
                    path=path,
                    source_zone=source_zone,
                    target_zone=target_zone,
                )
            )
    return tuple(warnings)


def dependency_is_forbidden(
    source_zone: str,
    target_zone: str,
    forbidden_dependencies: tuple[tuple[str, str], ...],
) -> bool:
    return any(
        source_zone == forbidden_source
        and (forbidden_target == "*" or target_zone == forbidden_target)
        for forbidden_source, forbidden_target in forbidden_dependencies
    )


def deduplicate_dependency_warnings(
    warnings: list[ArchitectureDependencyWarning],
) -> tuple[ArchitectureDependencyWarning, ...]:
    deduplicated: list[ArchitectureDependencyWarning] = []
    seen: set[tuple[Path, str, str]] = set()
    for warning in warnings:
        key = (warning.path, warning.source_zone, warning.target_zone)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(warning)
    return tuple(deduplicated)


def path_matches_any(path: Path, patterns: tuple[str, ...]) -> bool:
    path_text = path.as_posix()
    return any(path_matches_pattern(path_text, pattern.strip()) for pattern in patterns)


def path_matches_pattern(path_text: str, pattern: str) -> bool:
    if not pattern:
        return False
    if pattern.endswith("/"):
        return path_text.startswith(pattern)
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path_text == prefix or path_text.startswith(f"{prefix}/")
    if pattern.endswith("/*"):
        prefix = pattern[:-2]
        if not path_text.startswith(f"{prefix}/"):
            return False
        remainder = path_text[len(prefix) + 1 :]
        return "/" not in remainder
    if "/" not in pattern and fnmatch(Path(path_text).name, pattern):
        return True
    return fnmatch(path_text, pattern)


# ---------------------------------------------------------------------------
# Architecture Decision Record model (Phase 36F)
# ---------------------------------------------------------------------------

ADR_VALID_STATUSES: frozenset[str] = frozenset({
    "proposed",
    "accepted",
    "superseded",
    "deprecated",
})

# "accepted" is the human-approved status; all other transitions require
# explicit human action — AI agents may contribute but do not approve.
ADR_HUMAN_APPROVED_STATUS = "accepted"


@dataclass(frozen=True)
class ArchitectureDecisionRecord:
    """A governed Architecture Decision Record (ADR).

    Human author is required and remains authoritative; contributors are
    vendor-neutral and may include AI agents or tooling identifiers.
    """
    decision_id: str
    title: str
    status: str
    rationale: str
    alternatives_considered: tuple[str, ...]
    consequences: tuple[str, ...]
    created_at: datetime
    phase_reference: str | None
    author: str
    contributors: tuple[str, ...]  # vendor-neutral; may include AI agent IDs

    @property
    def is_human_approved(self) -> bool:
        return self.status == ADR_HUMAN_APPROVED_STATUS

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "status": self.status,
            "rationale": self.rationale,
            "alternatives_considered": list(self.alternatives_considered),
            "consequences": list(self.consequences),
            "created_at": self.created_at.isoformat(),
            "phase_reference": self.phase_reference,
            "author": self.author,
            "contributors": list(self.contributors),
            "is_human_approved": self.is_human_approved,
        }


def create_adr(
    decision_id: str,
    title: str,
    status: str,
    rationale: str,
    author: str,
    alternatives_considered: tuple[str, ...] | list[str] = (),
    consequences: tuple[str, ...] | list[str] = (),
    created_at: datetime | None = None,
    phase_reference: str | None = None,
    contributors: tuple[str, ...] | list[str] = (),
) -> ArchitectureDecisionRecord:
    """Return a validated ArchitectureDecisionRecord.

    Raises ValueError for invalid status or empty required fields.
    Human author is required — human remains authoritative.
    Contributors are vendor-neutral and may include AI agent identifiers.
    """
    if not isinstance(decision_id, str) or not decision_id:
        raise ValueError("decision_id must be a non-empty string.")
    if not isinstance(title, str) or not title:
        raise ValueError("title must be a non-empty string.")
    if not isinstance(rationale, str) or not rationale:
        raise ValueError("rationale must be a non-empty string.")
    if not isinstance(author, str) or not author:
        raise ValueError(
            "author must be a non-empty string; human author is required."
        )
    if status not in ADR_VALID_STATUSES:
        valid = ", ".join(sorted(ADR_VALID_STATUSES))
        raise ValueError(
            f"Invalid ADR status: {status!r}. Valid statuses: {valid}."
        )
    return ArchitectureDecisionRecord(
        decision_id=decision_id,
        title=title,
        status=status,
        rationale=rationale,
        alternatives_considered=tuple(alternatives_considered),
        consequences=tuple(consequences),
        created_at=created_at or datetime.now(timezone.utc),
        phase_reference=phase_reference,
        author=author,
        contributors=tuple(contributors),
    )


# ---------------------------------------------------------------------------
# ADR inspection API (Phase 36G)
# ---------------------------------------------------------------------------

ADR_INSPECTION_ADVISORY = (
    "Architecture decision inspection is advisory; the user remains authoritative."
)

# Deterministic in-memory sample registry. Phase 36H will introduce
# human-authored persistence; until then this registry provides stable
# fixture data for the decisions and show commands.
_SAMPLE_ADR_REGISTRY: tuple[ArchitectureDecisionRecord, ...] = (
    create_adr(
        decision_id="ADR-0001",
        title="Use TOML for PCAE policy configuration",
        status="accepted",
        rationale=(
            "TOML is human-readable, widely supported in Python tooling, "
            "and expresses structured configuration without requiring a schema compiler."
        ),
        alternatives_considered=["JSON", "YAML", "INI"],
        consequences=[
            "Policy is editable by humans without dedicated tooling.",
            "Policy parsing errors surface as clear ValueError messages.",
        ],
        created_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        phase_reference="1A",
        author="atila",
        contributors=[],
    ),
    create_adr(
        decision_id="ADR-0002",
        title="Architecture Decision Records as first-class PCAE artifacts",
        status="accepted",
        rationale=(
            "ADRs provide governed, human-approved decision memory that survives "
            "agent context resets and session boundaries."
        ),
        alternatives_considered=["Inline comments", "Wiki pages", "No formal record"],
        consequences=[
            "ADR model is now a PCAE core artifact.",
            "Contributors field preserves vendor-neutral agent attribution.",
        ],
        created_at=datetime(2026, 5, 29, 0, 0, tzinfo=timezone.utc),
        phase_reference="36F",
        author="atila",
        contributors=["claude-local"],
    ),
)


def get_adr_registry(
    root: HarnessPath | None = None,
) -> tuple[ArchitectureDecisionRecord, ...]:
    """Return the sample ADR registry merged with any persisted ADRs.

    When root is None, returns only the deterministic sample registry.
    When root is provided, appends persisted ADRs from .pcae/architecture/.
    """
    if root is None:
        return _SAMPLE_ADR_REGISTRY
    return _SAMPLE_ADR_REGISTRY + load_persisted_adrs(root)


@dataclass(frozen=True)
class ADRListResult:
    decisions: tuple[ArchitectureDecisionRecord, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "decision_count": len(self.decisions),
            "decisions": [d.to_dict() for d in self.decisions],
            "advisory": self.advisory,
        }


def list_architecture_decisions(
    registry: tuple[ArchitectureDecisionRecord, ...],
) -> ADRListResult:
    """Return a read-only listing of all ADRs in the registry."""
    return ADRListResult(decisions=registry, advisory=ADR_INSPECTION_ADVISORY)


def lookup_adr_by_id(
    decision_id: str,
    registry: tuple[ArchitectureDecisionRecord, ...],
) -> ArchitectureDecisionRecord | None:
    """Return the ADR matching decision_id, or None if not found."""
    for adr in registry:
        if adr.decision_id == decision_id:
            return adr
    return None


# ---------------------------------------------------------------------------
# ADR persistence (Phase 36H)
# ---------------------------------------------------------------------------

ADR_PERSISTENCE_RELATIVE_PATH = Path(".pcae") / "architecture"

ADR_ADD_ADVISORY = (
    "Architecture decision records are governed artifacts. "
    "Human author is required; human remains authoritative."
)


def _load_adr_from_file(path: Path) -> ArchitectureDecisionRecord:
    """Parse a persisted ADR JSON file into an ArchitectureDecisionRecord."""
    data = json.loads(path.read_text(encoding="utf-8"))
    created_at_raw = data.get("created_at")
    created_at = (
        datetime.fromisoformat(created_at_raw)
        if isinstance(created_at_raw, str) and created_at_raw
        else datetime.now(timezone.utc)
    )
    return create_adr(
        decision_id=data["decision_id"],
        title=data["title"],
        status=data["status"],
        rationale=data["rationale"],
        alternatives_considered=data.get("alternatives_considered", []),
        consequences=data.get("consequences", []),
        created_at=created_at,
        phase_reference=data.get("phase_reference"),
        author=data["author"],
        contributors=data.get("contributors", []),
    )


def load_persisted_adrs(root: HarnessPath) -> tuple[ArchitectureDecisionRecord, ...]:
    """Return ADRs loaded from .pcae/architecture/, sorted by filename."""
    dir_path = root.join(ADR_PERSISTENCE_RELATIVE_PATH)
    if not dir_path.is_dir():
        return ()
    adrs: list[ArchitectureDecisionRecord] = []
    for path in sorted(p for p in dir_path.iterdir() if p.suffix == ".json"):
        try:
            adrs.append(_load_adr_from_file(path))
        except (OSError, ValueError, KeyError):
            continue
    return tuple(adrs)


def generate_adr_decision_id(root: HarnessPath) -> str:
    """Return the next sequential ADR decision_id (e.g. ADR-0003)."""
    existing = get_adr_registry(root)
    max_num = 0
    for adr in existing:
        m = re.match(r"^ADR-(\d+)$", adr.decision_id)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"ADR-{max_num + 1:04d}"


def persist_adr(root: HarnessPath, adr: ArchitectureDecisionRecord) -> Path:
    """Write adr to .pcae/architecture/ADR-YYYYMMDD-HHMMSS.json and return the relative path."""
    dir_path = root.join(ADR_PERSISTENCE_RELATIVE_PATH)
    dir_path.mkdir(parents=True, exist_ok=True)
    filename = f"ADR-{adr.created_at.strftime('%Y%m%d-%H%M%S')}.json"
    file_path = dir_path / filename
    with file_path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(adr.to_dict(), fh, indent=2, sort_keys=True)
        fh.write("\n")
    return ADR_PERSISTENCE_RELATIVE_PATH / filename


@dataclass(frozen=True)
class ADRAddResult:
    adr: ArchitectureDecisionRecord
    relative_path: Path
    advisory: str

    def to_dict(self) -> dict:
        return {
            "adr": self.adr.to_dict(),
            "relative_path": self.relative_path.as_posix(),
            "advisory": self.advisory,
        }


# ---------------------------------------------------------------------------
# ADR export (Phase 36I)
# ---------------------------------------------------------------------------

ADR_EXPORT_RELATIVE_PATH = Path(".pcae") / "architecture-exports"

ADR_EXPORT_ADVISORY = (
    "Architecture decision exports are read-only portable artifacts. "
    "The user remains authoritative; no ADRs are mutated by export."
)


@dataclass(frozen=True)
class ADRExportResult:
    export_path: Path
    exported_at: str
    decision_count: int
    advisory: str

    def to_dict(self) -> dict:
        return {
            "export_path": self.export_path.as_posix(),
            "exported_at": self.exported_at,
            "decision_count": self.decision_count,
            "advisory": self.advisory,
        }


def export_architecture_decisions(
    root: HarnessPath,
    exported_at: datetime | None = None,
) -> ADRExportResult:
    """Export all ADRs (sample + persisted) to .pcae/architecture-exports/."""
    timestamp = exported_at or datetime.now(timezone.utc)
    exported_at_str = timestamp.isoformat()
    registry = get_adr_registry(root)

    status_summary: dict[str, int] = {s: 0 for s in sorted(ADR_VALID_STATUSES)}
    for adr in registry:
        if adr.status in status_summary:
            status_summary[adr.status] += 1

    export_data = {
        "advisory": ADR_EXPORT_ADVISORY,
        "decision_count": len(registry),
        "decisions": [adr.to_dict() for adr in registry],
        "exported_at": exported_at_str,
        "statuses": status_summary,
    }

    filename = f"architecture-decisions-{timestamp.strftime('%Y%m%d-%H%M%S')}.json"
    relative_path = ADR_EXPORT_RELATIVE_PATH / filename
    target = root.join(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(export_data, fh, indent=2, sort_keys=True)
        fh.write("\n")

    return ADRExportResult(
        export_path=relative_path,
        exported_at=exported_at_str,
        decision_count=len(registry),
        advisory=ADR_EXPORT_ADVISORY,
    )


def add_architecture_decision(
    root: HarnessPath,
    title: str,
    rationale: str,
    author: str,
    status: str = "accepted",
    alternatives_considered: tuple[str, ...] | list[str] = (),
    consequences: tuple[str, ...] | list[str] = (),
    phase_reference: str | None = None,
    contributors: tuple[str, ...] | list[str] = (),
    created_at: datetime | None = None,
) -> ADRAddResult:
    """Create, validate, and persist a new ADR.

    Raises ValueError for invalid status or empty required fields.
    Human author is required — human remains authoritative.
    """
    timestamp = created_at or datetime.now(timezone.utc)
    decision_id = generate_adr_decision_id(root)
    adr = create_adr(
        decision_id=decision_id,
        title=title,
        status=status,
        rationale=rationale,
        alternatives_considered=alternatives_considered,
        consequences=consequences,
        created_at=timestamp,
        phase_reference=phase_reference,
        author=author,
        contributors=contributors,
    )
    relative_path = persist_adr(root, adr)
    return ADRAddResult(adr=adr, relative_path=relative_path, advisory=ADR_ADD_ADVISORY)
