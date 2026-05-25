from __future__ import annotations

import json
from pathlib import Path

from pcae.core.paths import HarnessPath
from pcae.core.repo import validate_target_repo


FLEET_RELATIVE_PATH = Path(".pcae") / "fleet.json"


def add_fleet_repo(root: HarnessPath, repo_path: Path) -> tuple[str, bool]:
    validate_target_repo(repo_path)
    absolute_path = repo_path.resolve().as_posix()
    entries = list(read_fleet_repos(root))
    added = absolute_path not in entries
    if added:
        entries.append(absolute_path)
        write_fleet_repos(root, tuple(sorted(entries)))
    return absolute_path, added


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
