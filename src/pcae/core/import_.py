from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from pcae.core.export import GOVERNANCE_BUNDLE_REQUIRED_KEYS


FUTURE_IMPORT_TARGETS = (
    ".pcae/session.json",
    ".pcae/architecture-history.json",
    ".pcae/policy.toml",
    "tasks/active/",
)
RESTORE_TARGETS = (
    Path(".pcae") / "session.json",
    Path(".pcae") / "architecture-history.json",
)


@dataclass(frozen=True)
class GovernanceBundlePreview:
    data: dict
    future_import_targets: tuple[str, ...] = FUTURE_IMPORT_TARGETS


@dataclass(frozen=True)
class GovernanceBundleRestore:
    written_paths: tuple[Path, ...]


def read_governance_bundle_preview(path: Path) -> GovernanceBundlePreview:
    if not path.is_file():
        raise ValueError(f"Governance bundle not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid governance bundle JSON: {error.msg}.") from error

    if not isinstance(data, dict):
        raise ValueError("Invalid governance bundle: expected a JSON object.")

    missing_keys = sorted(GOVERNANCE_BUNDLE_REQUIRED_KEYS - set(data))
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ValueError(f"Invalid governance bundle: missing required keys: {missing}.")

    return GovernanceBundlePreview(data=data)


def restore_governance_bundle(
    root: Path,
    path: Path,
    merge_history: bool = False,
) -> GovernanceBundleRestore:
    preview = read_governance_bundle_preview(path)
    validate_restorable_bundle(preview.data)

    written_paths: list[Path] = []
    root.joinpath(".pcae").mkdir(parents=True, exist_ok=True)

    session_snapshot = preview.data.get("session_snapshot")
    if session_snapshot is not None:
        write_json_file(root / RESTORE_TARGETS[0], session_snapshot)
        written_paths.append(RESTORE_TARGETS[0])

    imported_history = imported_history_entries(preview.data)
    if imported_history:
        history_path = root / RESTORE_TARGETS[1]
        if merge_history:
            history = merge_history_entries(
                read_local_history_entries(history_path),
                imported_history,
            )
        else:
            history = imported_history
        write_json_file(history_path, history)
        written_paths.append(RESTORE_TARGETS[1])

    return GovernanceBundleRestore(written_paths=tuple(written_paths))


def validate_restorable_bundle(data: dict) -> None:
    health_summary = data.get("health_summary")
    check_summary = data.get("check_summary")

    health_status = status_value(health_summary, "overall_status")
    check_status = status_value(check_summary, "status")
    if health_status != "healthy" or check_status != "passed":
        raise ValueError(
            "Refusing to restore governance bundle because health/check status "
            f"is not healthy/passed: health={health_status}, check={check_status}."
        )


def imported_history_entries(data: dict) -> list[dict]:
    history_summary = data.get("latest_architecture_history_summary")
    if not isinstance(history_summary, dict):
        return []

    entries = history_summary.get("entries_data")
    if isinstance(entries, list):
        return [entry for entry in entries if isinstance(entry, dict)]

    latest_history = history_summary.get("latest")
    if isinstance(latest_history, dict):
        return [latest_history]
    return []


def read_local_history_entries(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [entry for entry in data if isinstance(entry, dict)]


def merge_history_entries(
    local_entries: list[dict],
    imported_entries: list[dict],
) -> list[dict]:
    by_timestamp: dict[str, dict] = {}
    untimestamped: list[dict] = []
    for entry in local_entries + imported_entries:
        timestamp = entry.get("timestamp")
        if isinstance(timestamp, str) and timestamp:
            by_timestamp.setdefault(timestamp, entry)
        else:
            untimestamped.append(entry)

    return untimestamped + [
        by_timestamp[timestamp]
        for timestamp in sorted(by_timestamp)
    ]


def status_value(value, key: str) -> str:
    if not isinstance(value, dict):
        return "missing"
    status = value.get(key)
    if isinstance(status, str) and status:
        return status
    return "unknown"


def write_json_file(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")
