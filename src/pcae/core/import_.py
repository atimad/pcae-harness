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


def restore_governance_bundle(root: Path, path: Path) -> GovernanceBundleRestore:
    preview = read_governance_bundle_preview(path)
    validate_restorable_bundle(preview.data)

    written_paths: list[Path] = []
    root.joinpath(".pcae").mkdir(parents=True, exist_ok=True)

    session_snapshot = preview.data.get("session_snapshot")
    if session_snapshot is not None:
        write_json_file(root / RESTORE_TARGETS[0], session_snapshot)
        written_paths.append(RESTORE_TARGETS[0])

    history_summary = preview.data.get("latest_architecture_history_summary")
    if isinstance(history_summary, dict):
        latest_history = history_summary.get("latest")
        if latest_history is not None:
            write_json_file(root / RESTORE_TARGETS[1], [latest_history])
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
