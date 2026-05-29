from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from pcae.core.git_status import read_git_branch
from pcae.core.paths import HarnessPath
from pcae.core.policy import DEFAULT_AGENT_STALE_AFTER_SECONDS, load_policy
from pcae.core.tasks import find_latest_active_task


# ---------------------------------------------------------------------------
# Multi-Agent Collaboration registry (Phase 37A)
# ---------------------------------------------------------------------------

MULTI_AGENT_REGISTRY_ADVISORY = (
    "Agent registry is read-only. The human user remains authoritative."
)


@dataclass(frozen=True)
class AgentEntry:
    agent_id: str
    agent_type: str
    role: str
    status: str
    capabilities: tuple[str, ...]
    preferred_workloads: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": list(self.capabilities),
            "preferred_workloads": list(self.preferred_workloads),
            "role": self.role,
            "status": self.status,
        }


MULTI_AGENT_REGISTRY: tuple[AgentEntry, ...] = (
    AgentEntry(
        agent_id="claude-local",
        agent_type="claude",
        role="documentation",
        status="available",
        capabilities=(
            "architecture_review",
            "code_analysis",
            "documentation",
            "decision_making",
        ),
        preferred_workloads=("implementation", "documentation", "analysis"),
    ),
    AgentEntry(
        agent_id="codex-local",
        agent_type="codex",
        role="implementation",
        status="available",
        capabilities=(
            "code_generation",
            "test_writing",
            "runtime_execution",
        ),
        preferred_workloads=("implementation", "tests"),
    ),
    AgentEntry(
        agent_id="pcae-native",
        agent_type="pcae",
        role="governance",
        status="available",
        capabilities=(
            "governance_validation",
            "policy_enforcement",
            "provenance_tracking",
        ),
        preferred_workloads=("validation", "governance"),
    ),
)


def build_multi_agent_registry() -> dict:
    """Return a read-only multi-agent registry summary."""
    agents = [entry.to_dict() for entry in MULTI_AGENT_REGISTRY]
    return {
        "advisory": MULTI_AGENT_REGISTRY_ADVISORY,
        "agent_count": len(agents),
        "agents": agents,
    }


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
class AgentAcquireResult:
    lock: "AgentLock"
    already_held: bool


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


def acquire_agent_lock_idempotent(
    root: HarnessPath,
    agent_id: str,
    acquired_at: datetime | None = None,
) -> AgentAcquireResult:
    existing = read_agent_lock(root)
    if existing is not None:
        if existing.agent_id == agent_id:
            return AgentAcquireResult(lock=existing, already_held=True)
        raise ValueError(f"Agent lock already held by {existing.agent_id}.")
    lock = acquire_agent_lock(root, agent_id, acquired_at)
    return AgentAcquireResult(lock=lock, already_held=False)


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


def build_agent_lock_state(root: HarnessPath) -> dict[str, object]:
    try:
        status = build_agent_status(root)
    except ValueError:
        lock = read_agent_lock(root)
        return compact_agent_lock_state(
            {
                "age_seconds": None,
                "lock": None if lock is None else lock.data,
                "locked": lock is not None,
                "stale": False,
                "stale_after_seconds": AGENT_LOCK_STALE_AFTER_SECONDS,
            }
        )
    return compact_agent_lock_state(status)


def compact_agent_lock_state(status: dict[str, object]) -> dict[str, object]:
    lock = status.get("lock")
    agent_id = None
    if isinstance(lock, dict):
        value = lock.get("agent_id")
        if isinstance(value, str):
            agent_id = value

    return {
        "age_seconds": status.get("age_seconds"),
        "agent_id": agent_id,
        "locked": status["locked"],
        "stale": status["stale"],
        "stale_after_seconds": status["stale_after_seconds"],
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
