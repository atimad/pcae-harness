from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from pcae.core.git_status import read_git_branch
from pcae.core.paths import HarnessPath
from pcae.core.policy import DEFAULT_AGENT_STALE_AFTER_SECONDS, load_policy
from pcae.core.tasks import find_latest_active_task


AGENT_LOCK_RELATIVE_PATH = Path(".pcae") / "agent-lock.json"
AGENT_LOCK_STALE_AFTER_SECONDS = DEFAULT_AGENT_STALE_AFTER_SECONDS


@dataclass(frozen=True)
class AgentLock:
    relative_path: Path
    data: dict

    @property
    def agent_id(self) -> str:
        value = self.data.get("agent_id")
        return value if isinstance(value, str) else ""


@dataclass(frozen=True)
class AgentReleaseResult:
    released: bool
    message: str


def acquire_agent_lock(
    root: HarnessPath,
    agent_id: str,
    acquired_at: datetime | None = None,
) -> AgentLock:
    target = root.join(AGENT_LOCK_RELATIVE_PATH)
    if target.exists():
        existing = read_agent_lock(root)
        locked_by = existing.agent_id if existing is not None else "unknown"
        raise ValueError(f"Agent lock already held by {locked_by}.")

    timestamp = acquired_at or datetime.now(timezone.utc)
    data = build_agent_lock_data(root, agent_id, timestamp)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")

    return AgentLock(relative_path=AGENT_LOCK_RELATIVE_PATH, data=data)


def release_agent_lock(
    root: HarnessPath,
    agent_id: str,
    force_stale: bool = False,
) -> AgentReleaseResult:
    target = root.join(AGENT_LOCK_RELATIVE_PATH)
    lock = read_agent_lock(root)
    if lock is None:
        return AgentReleaseResult(False, "No agent lock is currently held.")

    if lock.agent_id != agent_id:
        if force_stale:
            status = build_agent_status(root)
            if status["stale"]:
                target.unlink()
                return AgentReleaseResult(
                    True,
                    (
                        "Force-released stale agent lock held by "
                        f"{lock.agent_id}."
                    ),
                )
            return AgentReleaseResult(
                False,
                (
                    "Agent lock is not stale; "
                    f"{agent_id} cannot release lock held by {lock.agent_id}."
                ),
            )
        return AgentReleaseResult(
            False,
            f"Agent lock is held by {lock.agent_id}; {agent_id} cannot release it.",
        )

    target.unlink()
    return AgentReleaseResult(True, f"Released agent lock for {agent_id}.")


def read_agent_lock(root: HarnessPath) -> AgentLock | None:
    target = root.join(AGENT_LOCK_RELATIVE_PATH)
    if not target.is_file():
        return None

    data = json.loads(target.read_text(encoding="utf-8"))
    return AgentLock(relative_path=AGENT_LOCK_RELATIVE_PATH, data=data)


def build_agent_status(
    root: HarnessPath,
    now: datetime | None = None,
) -> dict[str, object]:
    stale_after_seconds = read_agent_stale_after_seconds(root)
    lock = read_agent_lock(root)
    if lock is None:
        return {
            "age_seconds": None,
            "lock": None,
            "locked": False,
            "stale": False,
            "stale_after_seconds": stale_after_seconds,
        }

    age_seconds = calculate_lock_age_seconds(
        lock.data.get("acquired_at"),
        now or datetime.now(timezone.utc),
    )
    return {
        "age_seconds": age_seconds,
        "lock": lock.data,
        "locked": True,
        "stale": age_seconds is not None
        and age_seconds > stale_after_seconds,
        "stale_after_seconds": stale_after_seconds,
    }


def build_agent_lock_data(
    root: HarnessPath,
    agent_id: str,
    timestamp: datetime,
) -> dict[str, object]:
    active_task = find_latest_active_task(root)
    return {
        "active_task": None
        if active_task is None
        else {
            "id": active_task.task_id,
            "title": active_task.title,
        },
        "acquired_at": timestamp.isoformat(),
        "agent_id": agent_id,
        "git_branch": read_git_branch(root),
    }


def calculate_lock_age_seconds(
    acquired_at: object,
    now: datetime,
) -> int | None:
    if not isinstance(acquired_at, str):
        return None

    try:
        acquired = datetime.fromisoformat(acquired_at)
    except ValueError:
        return None

    if acquired.tzinfo is None:
        acquired = acquired.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    return max(0, int((now - acquired).total_seconds()))


def read_agent_stale_after_seconds(root: HarnessPath) -> int:
    policy = load_policy(root)
    if not policy.valid:
        raise ValueError(policy.error or "Invalid policy.")
    return policy.agent_stale_after_seconds
