from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.repo import build_repo_trial, validate_target_repo


FLEET_RELATIVE_PATH = Path(".pcae") / "fleet.json"
FLEET_EXPORTS_RELATIVE_PATH = Path(".pcae") / "fleet-exports"


@dataclass(frozen=True)
class FleetExport:
    relative_path: Path
    data: dict


def add_fleet_repo(root: HarnessPath, repo_path: Path) -> tuple[str, bool]:
    validate_target_repo(repo_path)
    absolute_path = repo_path.resolve().as_posix()
    entries = list(read_fleet_repos(root))
    added = absolute_path not in entries
    if added:
        entries.append(absolute_path)
        write_fleet_repos(root, tuple(sorted(entries)))
    return absolute_path, added


def remove_fleet_repo(
    root: HarnessPath,
    repo_path: Path,
    *,
    missing_only: bool = False,
) -> tuple[str, bool]:
    absolute_path = repo_path.resolve().as_posix()
    entries = list(read_fleet_repos(root))
    if absolute_path not in entries:
        raise ValueError(f"Fleet repo is not registered: {absolute_path}")

    if missing_only and repo_path.exists():
        return absolute_path, False

    entries.remove(absolute_path)
    write_fleet_repos(root, tuple(entries))
    return absolute_path, True


def read_fleet_repos(root: HarnessPath) -> tuple[str, ...]:
    target = root.join(FLEET_RELATIVE_PATH)
    if not target.is_file():
        return ()

    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return ()
    repos = data.get("repos")
    if not isinstance(repos, list):
        return ()
    return tuple(repo for repo in repos if isinstance(repo, str) and repo)


def write_fleet_repos(root: HarnessPath, repos: tuple[str, ...]) -> None:
    target = root.join(FLEET_RELATIVE_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as file:
        json.dump({"repos": sorted(repos)}, file, indent=2, sort_keys=True)
        file.write("\n")


def build_fleet_health(root: HarnessPath) -> dict:
    repos = [fleet_repo_health(repo) for repo in read_fleet_repos(root)]
    healthy_count = sum(1 for repo in repos if repo["status"] == "healthy")
    unhealthy_count = len(repos) - healthy_count
    return {
        "healthy_count": healthy_count,
        "overall_status": "healthy" if unhealthy_count == 0 else "unhealthy",
        "repo_count": len(repos),
        "repos": repos,
        "unhealthy_count": unhealthy_count,
    }


def build_fleet_inspection(root: HarnessPath) -> dict:
    repos = [fleet_repo_inspection(repo) for repo in read_fleet_repos(root)]
    ready_count = sum(1 for repo in repos if repo["status"] == "ready")
    not_ready_count = len(repos) - ready_count
    return {
        "not_ready_count": not_ready_count,
        "overall_status": "ready" if not_ready_count == 0 else "not_ready",
        "ready_count": ready_count,
        "repo_count": len(repos),
        "repos": repos,
    }


def build_fleet_drift(root: HarnessPath) -> dict:
    repos = read_fleet_repos(root)
    inspections = [fleet_repo_inspection(repo) for repo in repos]
    health = [fleet_repo_health(repo) for repo in repos]
    findings = fleet_drift_findings(inspections, health)
    drift_detected = bool(findings)
    return {
        "drift_detected": drift_detected,
        "drift_findings": findings,
        "overall_status": "drift" if drift_detected else "no_drift",
        "repo_count": len(repos),
    }


def fleet_drift_findings(inspections: list[dict], health: list[dict]) -> list[dict]:
    findings: list[dict] = []
    for repo in inspections:
        if repo["pcae_files_missing"] is None:
            findings.append(
                {
                    "path": repo["path"],
                    "type": "repo_unavailable",
                    "message": repo["details"],
                }
            )
        elif repo["pcae_files_missing"] > 0:
            findings.append(
                {
                    "path": repo["path"],
                    "type": "missing_pcae_files",
                    "message": (
                        f"{repo['pcae_files_missing']} required PCAE files missing"
                    ),
                }
            )

    valid_inspections = [
        repo for repo in inspections if repo["pcae_files_missing"] is not None
    ]
    valid_paths = {repo["path"] for repo in valid_inspections}
    valid_health = [repo for repo in health if repo["path"] in valid_paths]
    findings.extend(
        mismatch_findings(
            valid_inspections,
            "policy_exists",
            "policy_existence_mismatch",
            "Policy existence differs across fleet repos.",
        )
    )
    findings.extend(
        mismatch_findings(
            valid_inspections,
            "hooks_exist",
            "hook_existence_mismatch",
            "Hook existence differs across fleet repos.",
        )
    )
    findings.extend(
        mismatch_findings(
            valid_health,
            "latest_enforcement_mode",
            "enforcement_mode_mismatch",
            "Architecture enforcement mode differs across fleet repos.",
        )
    )
    return findings


def mismatch_findings(
    repos: list[dict],
    key: str,
    finding_type: str,
    message: str,
) -> list[dict]:
    values = {repo[key] for repo in repos}
    if len(values) <= 1:
        return []
    return [
        {
            "path": repo["path"],
            "type": finding_type,
            "value": repo[key],
            "message": message,
        }
        for repo in repos
    ]


def write_fleet_export(
    root: HarnessPath,
    generated_at: datetime | None = None,
) -> FleetExport:
    timestamp = generated_at or datetime.now(timezone.utc)
    data = build_fleet_export_data(root, timestamp)
    relative_path = FLEET_EXPORTS_RELATIVE_PATH / (
        f"fleet-governance-bundle-{timestamp.strftime('%Y%m%d-%H%M%S')}.json"
    )
    target = root.join(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")
    return FleetExport(relative_path=relative_path, data=data)


def build_fleet_export_data(root: HarnessPath, timestamp: datetime) -> dict:
    health = build_fleet_health(root)
    return {
        "generated_timestamp": timestamp.isoformat(),
        "healthy_count": health["healthy_count"],
        "overall_status": health["overall_status"],
        "repo_count": health["repo_count"],
        "repos": [
            {
                "active_task": repo["active_task"],
                "latest_dependency_warnings": repo["latest_dependency_warnings"],
                "latest_enforcement_mode": repo["latest_enforcement_mode"],
                "path": repo["path"],
                "session_continuity": repo["session_continuity"],
                "status": repo["status"],
            }
            for repo in health["repos"]
        ],
        "unhealthy_count": health["unhealthy_count"],
    }


def fleet_repo_health(repo: str) -> dict:
    path = Path(repo)
    try:
        validate_target_repo(path)
    except ValueError as error:
        return {
            "active_task": None,
            "details": str(error),
            "latest_dependency_warnings": None,
            "latest_enforcement_mode": None,
            "path": repo,
            "session_continuity": None,
            "status": "unhealthy",
        }

    health = build_health_data(HarnessPath(path))
    return {
        "active_task": health["active_task"],
        "details": "ok" if health["overall_status"] == "healthy" else "check failed",
        "latest_dependency_warnings": health["latest_dependency_warnings"],
        "latest_enforcement_mode": health["latest_enforcement_mode"],
        "path": repo,
        "session_continuity": health["session_continuity"],
        "status": health["overall_status"],
    }


def fleet_repo_inspection(repo: str) -> dict:
    path = Path(repo)
    try:
        trial = build_repo_trial(path)
    except ValueError as error:
        return {
            "active_tasks_exist": False,
            "details": str(error),
            "hooks_exist": False,
            "path": repo,
            "pcae_files_missing": None,
            "pcae_files_present": None,
            "policy_exists": False,
            "status": "not_ready",
        }

    status = "ready" if trial.pcae_files_missing == 0 else "not_ready"
    return {
        "active_tasks_exist": trial.active_tasks_exist,
        "details": "ok" if status == "ready" else "missing PCAE files",
        "hooks_exist": trial.hooks_exist,
        "path": repo,
        "pcae_files_missing": trial.pcae_files_missing,
        "pcae_files_present": trial.pcae_files_present,
        "policy_exists": trial.policy_exists,
        "status": status,
    }
