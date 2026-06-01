from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess

from pcae.core.git_status import read_git_branch, read_git_changes
from pcae.core.paths import HarnessPath
from pcae.core.policy import DEFAULT_AGENT_STALE_AFTER_SECONDS, load_policy
from pcae.core.tasks import find_latest_active_task


# ---------------------------------------------------------------------------
# Multi-Agent Collaboration registry (Phase 37A / 37B / 37C)
# ---------------------------------------------------------------------------

MULTI_AGENT_REGISTRY_ADVISORY = (
    "Agent registry is read-only. The human user remains authoritative."
)
AGENT_VALIDATION_ADVISORY = (
    "Agent configuration validation is advisory; the user remains authoritative."
)

AGENT_STATUS_DECLARED = "declared"
AGENT_STATUS_CONFIGURED = "configured"
AGENT_STATUS_AVAILABLE = "available"
AGENT_STATUS_ACTIVE = "active"

VALID_AGENT_STATUSES: frozenset[str] = frozenset(
    {
        AGENT_STATUS_DECLARED,
        AGENT_STATUS_CONFIGURED,
        AGENT_STATUS_AVAILABLE,
        AGENT_STATUS_ACTIVE,
    }
)


@dataclass(frozen=True)
class AgentEntry:
    agent_id: str
    agent_type: str
    role: str
    status: str
    capabilities: tuple[str, ...]
    preferred_workloads: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in VALID_AGENT_STATUSES:
            raise ValueError(
                f"Invalid agent status {self.status!r}; "
                f"must be one of: {', '.join(sorted(VALID_AGENT_STATUSES))}."
            )

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
    # Available agents (configured and confirmed for local use)
    AgentEntry(
        agent_id="claude-local",
        agent_type="claude",
        role="documentation",
        status=AGENT_STATUS_AVAILABLE,
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
        status=AGENT_STATUS_AVAILABLE,
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
        status=AGENT_STATUS_AVAILABLE,
        capabilities=(
            "governance_validation",
            "policy_enforcement",
            "provenance_tracking",
        ),
        preferred_workloads=("validation", "governance"),
    ),
    # Confirmed available agents (CLI confirmed on PATH)
    AgentEntry(
        agent_id="kimi-local",
        agent_type="kimi",
        role="analysis",
        status=AGENT_STATUS_AVAILABLE,
        capabilities=(
            "code_analysis",
            "documentation",
            "research",
        ),
        preferred_workloads=("analysis", "documentation"),
    ),
    # Declared agents (registered for future use; not yet configured or available)
    AgentEntry(
        agent_id="deepseek-local",
        agent_type="deepseek",
        role="implementation",
        status=AGENT_STATUS_DECLARED,
        capabilities=(
            "code_generation",
            "reasoning",
            "implementation",
        ),
        preferred_workloads=("implementation", "analysis"),
    ),
    AgentEntry(
        agent_id="gemini-local",
        agent_type="gemini",
        role="analysis",
        status=AGENT_STATUS_DECLARED,
        capabilities=(
            "code_analysis",
            "documentation",
            "multimodal",
        ),
        preferred_workloads=("analysis", "documentation"),
    ),
    AgentEntry(
        agent_id="grok-local",
        agent_type="grok",
        role="analysis",
        status=AGENT_STATUS_DECLARED,
        capabilities=(
            "reasoning",
            "code_analysis",
            "research",
        ),
        preferred_workloads=("analysis", "research"),
    ),
    AgentEntry(
        agent_id="perplexity-local",
        agent_type="perplexity",
        role="research",
        status=AGENT_STATUS_DECLARED,
        capabilities=(
            "research",
            "documentation",
            "web_search",
        ),
        preferred_workloads=("research", "documentation"),
    ),
)


def _build_lifecycle_summary() -> dict[str, int]:
    summary = {s: 0 for s in sorted(VALID_AGENT_STATUSES)}
    for entry in MULTI_AGENT_REGISTRY:
        summary[entry.status] += 1
    return summary


def build_multi_agent_registry() -> dict:
    """Return a read-only multi-agent registry summary."""
    agents = [entry.to_dict() for entry in MULTI_AGENT_REGISTRY]
    return {
        "advisory": MULTI_AGENT_REGISTRY_ADVISORY,
        "agent_count": len(agents),
        "agents": agents,
        "lifecycle_summary": _build_lifecycle_summary(),
    }


def get_agent_by_id(agent_id: str) -> AgentEntry | None:
    """Return the AgentEntry for agent_id, or None if not found."""
    for entry in MULTI_AGENT_REGISTRY:
        if entry.agent_id == agent_id:
            return entry
    return None


@dataclass(frozen=True)
class AgentValidationResult:
    valid: bool
    agent_count: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "advisory": self.advisory,
            "agent_count": self.agent_count,
            "errors": list(self.errors),
            "valid": self.valid,
            "warnings": list(self.warnings),
        }


def validate_agent_registry() -> AgentValidationResult:
    """Return a read-only advisory validation of the multi-agent registry."""
    errors: list[str] = []
    warnings: list[str] = []

    seen_ids: set[str] = set()
    for entry in MULTI_AGENT_REGISTRY:
        if entry.agent_id in seen_ids:
            errors.append(f"Duplicate agent ID: '{entry.agent_id}'.")
        seen_ids.add(entry.agent_id)

        if entry.status not in VALID_AGENT_STATUSES:
            errors.append(
                f"Agent '{entry.agent_id}' has invalid status '{entry.status}'."
            )

        if not entry.role or not entry.role.strip():
            errors.append(f"Agent '{entry.agent_id}' has an empty role.")

        if entry.status in (AGENT_STATUS_AVAILABLE, AGENT_STATUS_ACTIVE):
            if not entry.capabilities:
                errors.append(
                    f"Agent '{entry.agent_id}' is '{entry.status}' "
                    "but has no capabilities."
                )
            if not entry.preferred_workloads:
                errors.append(
                    f"Agent '{entry.agent_id}' is '{entry.status}' "
                    "but has no preferred workloads."
                )

    return AgentValidationResult(
        valid=len(errors) == 0,
        agent_count=len(MULTI_AGENT_REGISTRY),
        warnings=tuple(warnings),
        errors=tuple(errors),
        advisory=AGENT_VALIDATION_ADVISORY,
    )


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


# ---------------------------------------------------------------------------
# Agent configuration model (Phase 37E)
# ---------------------------------------------------------------------------

ADAPTER_TYPE_CLI = "cli"
ADAPTER_TYPE_API = "api"
ADAPTER_TYPE_DESKTOP_MANUAL = "desktop_manual"
ADAPTER_TYPE_NATIVE = "native"
ADAPTER_TYPE_UNDECLARED = "undeclared"

VALID_ADAPTER_TYPES: frozenset[str] = frozenset(
    {
        ADAPTER_TYPE_CLI,
        ADAPTER_TYPE_API,
        ADAPTER_TYPE_DESKTOP_MANUAL,
        ADAPTER_TYPE_NATIVE,
        ADAPTER_TYPE_UNDECLARED,
    }
)

CONFIG_ADVISORY = (
    "Agent configuration metadata is advisory; "
    "configuration does not imply execution."
)


@dataclass(frozen=True)
class AgentConfigEntry:
    agent_id: str
    adapter_type: str
    executable_hint: str | None
    requires_manual_setup: bool
    configuration_notes: str

    @property
    def configuration_status(self) -> str:
        return "configured" if self.adapter_type != ADAPTER_TYPE_UNDECLARED else "unconfigured"

    def to_dict(self, lifecycle_status: str = "") -> dict:
        return {
            "adapter_type": self.adapter_type,
            "agent_id": self.agent_id,
            "configuration_notes": self.configuration_notes,
            "configuration_status": self.configuration_status,
            "executable_hint": self.executable_hint,
            "lifecycle_status": lifecycle_status,
            "requires_manual_setup": self.requires_manual_setup,
        }


AGENT_CONFIG_REGISTRY: dict[str, AgentConfigEntry] = {
    "claude-local": AgentConfigEntry(
        agent_id="claude-local",
        adapter_type=ADAPTER_TYPE_CLI,
        executable_hint="claude",
        requires_manual_setup=False,
        configuration_notes="Invoked via the Claude Code CLI.",
    ),
    "codex-local": AgentConfigEntry(
        agent_id="codex-local",
        adapter_type=ADAPTER_TYPE_CLI,
        executable_hint="codex",
        requires_manual_setup=False,
        configuration_notes="Invoked via the Codex CLI.",
    ),
    "pcae-native": AgentConfigEntry(
        agent_id="pcae-native",
        adapter_type=ADAPTER_TYPE_NATIVE,
        executable_hint="pcae",
        requires_manual_setup=False,
        configuration_notes="Built-in PCAE governance agent; no external invocation required.",
    ),
    "kimi-local": AgentConfigEntry(
        agent_id="kimi-local",
        adapter_type=ADAPTER_TYPE_CLI,
        executable_hint="kimi",
        requires_manual_setup=False,
        configuration_notes="CLI adapter; invoked via the kimi executable.",
    ),
    "deepseek-local": AgentConfigEntry(
        agent_id="deepseek-local",
        adapter_type=ADAPTER_TYPE_UNDECLARED,
        executable_hint=None,
        requires_manual_setup=True,
        configuration_notes="Adapter not yet declared. Configure adapter before use.",
    ),
    "gemini-local": AgentConfigEntry(
        agent_id="gemini-local",
        adapter_type=ADAPTER_TYPE_UNDECLARED,
        executable_hint=None,
        requires_manual_setup=True,
        configuration_notes="Adapter not yet declared. Configure adapter before use.",
    ),
    "grok-local": AgentConfigEntry(
        agent_id="grok-local",
        adapter_type=ADAPTER_TYPE_UNDECLARED,
        executable_hint=None,
        requires_manual_setup=True,
        configuration_notes="Adapter not yet declared. Configure adapter before use.",
    ),
    "perplexity-local": AgentConfigEntry(
        agent_id="perplexity-local",
        adapter_type=ADAPTER_TYPE_UNDECLARED,
        executable_hint=None,
        requires_manual_setup=True,
        configuration_notes="Adapter not yet declared. Configure adapter before use.",
    ),
}


def get_agent_config(agent_id: str) -> AgentConfigEntry | None:
    return AGENT_CONFIG_REGISTRY.get(agent_id)


@dataclass(frozen=True)
class AgentConfigValidationResult:
    valid: bool
    agent_count: int
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "advisory": self.advisory,
            "agent_count": self.agent_count,
            "errors": list(self.errors),
            "valid": self.valid,
            "warnings": list(self.warnings),
        }


def validate_agent_configs() -> AgentConfigValidationResult:
    """Return a read-only advisory validation of the agent configuration model."""
    errors: list[str] = []
    warnings: list[str] = []

    seen_ids: set[str] = set()
    for agent_id, config in AGENT_CONFIG_REGISTRY.items():
        if agent_id in seen_ids:
            errors.append(f"Duplicate config entry for agent ID: '{agent_id}'.")
        seen_ids.add(agent_id)

        if config.adapter_type not in VALID_ADAPTER_TYPES:
            errors.append(
                f"Agent '{agent_id}' has invalid adapter type '{config.adapter_type}'."
            )

        registry_entry = get_agent_by_id(agent_id)
        if registry_entry is not None:
            if (
                registry_entry.status in (AGENT_STATUS_AVAILABLE, AGENT_STATUS_ACTIVE)
                and config.adapter_type == ADAPTER_TYPE_UNDECLARED
            ):
                errors.append(
                    f"Agent '{agent_id}' is '{registry_entry.status}' "
                    "but has undeclared adapter type."
                )

    return AgentConfigValidationResult(
        valid=len(errors) == 0,
        agent_count=len(AGENT_CONFIG_REGISTRY),
        errors=tuple(errors),
        warnings=tuple(warnings),
        advisory=CONFIG_ADVISORY,
    )


# ---------------------------------------------------------------------------
# Agent lifecycle reporting (Phase 37D)
# ---------------------------------------------------------------------------

LIFECYCLE_ADVISORY = "Lifecycle reporting is advisory; no agent state is modified."

LIFECYCLE_PROGRESSION_GUIDANCE: dict[str, str] = {
    AGENT_STATUS_DECLARED: (
        "Agent is registered but not yet configured. "
        "Next: add the agent to policy.toml with kind and roles."
    ),
    AGENT_STATUS_CONFIGURED: (
        "Agent is configured in policy.toml but availability is unconfirmed. "
        "Next: verify the agent is reachable and mark it available."
    ),
    AGENT_STATUS_AVAILABLE: (
        "Agent is configured and ready for task assignment. "
        "Next: acquire the session lock to activate."
    ),
    AGENT_STATUS_ACTIVE: (
        "Agent currently holds the session lock and is actively engaged. "
        "No further progression required."
    ),
}


@dataclass(frozen=True)
class LifecycleValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "errors": list(self.errors),
            "valid": self.valid,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class LifecycleReport:
    lifecycle_summary: dict[str, int]
    agents_by_state: dict[str, list[dict]]
    progression_guidance: dict[str, str]
    validation: LifecycleValidationResult
    advisory: str

    def to_dict(self) -> dict:
        return {
            "advisory": self.advisory,
            "agents_by_state": self.agents_by_state,
            "lifecycle_summary": self.lifecycle_summary,
            "progression_guidance": self.progression_guidance,
            "validation": self.validation.to_dict(),
        }


def _validate_lifecycle(registry: tuple[AgentEntry, ...]) -> LifecycleValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()

    for entry in registry:
        if entry.agent_id in seen_ids:
            errors.append(f"Duplicate agent ID: '{entry.agent_id}'.")
        seen_ids.add(entry.agent_id)

        if entry.status not in VALID_AGENT_STATUSES:
            errors.append(
                f"Agent '{entry.agent_id}' has invalid lifecycle state '{entry.status}'."
            )

        if entry.status in (AGENT_STATUS_AVAILABLE, AGENT_STATUS_ACTIVE):
            if not entry.capabilities:
                errors.append(
                    f"Agent '{entry.agent_id}' is '{entry.status}' "
                    "but has no capabilities (inconsistent lifecycle metadata)."
                )
            if not entry.preferred_workloads:
                errors.append(
                    f"Agent '{entry.agent_id}' is '{entry.status}' "
                    "but has no preferred workloads (inconsistent lifecycle metadata)."
                )

    return LifecycleValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def build_lifecycle_report() -> LifecycleReport:
    """Return a read-only lifecycle state distribution report."""
    summary: dict[str, int] = {s: 0 for s in sorted(VALID_AGENT_STATUSES)}
    agents_by_state: dict[str, list[dict]] = {s: [] for s in sorted(VALID_AGENT_STATUSES)}

    for entry in MULTI_AGENT_REGISTRY:
        summary[entry.status] += 1
        agents_by_state[entry.status].append(entry.to_dict())

    return LifecycleReport(
        lifecycle_summary=summary,
        agents_by_state=agents_by_state,
        progression_guidance=dict(LIFECYCLE_PROGRESSION_GUIDANCE),
        validation=_validate_lifecycle(MULTI_AGENT_REGISTRY),
        advisory=LIFECYCLE_ADVISORY,
    )


# ---------------------------------------------------------------------------
# Collaboration workflow templates (Phase 37F)
# ---------------------------------------------------------------------------

COLLABORATION_ADVISORY = (
    "Collaboration workflows are advisory templates; "
    "no agents are executed or assigned automatically."
)


@dataclass(frozen=True)
class WorkflowStep:
    step_name: str
    recommended_agent_role: str
    purpose: str
    required_lifecycle_status: str

    def to_dict(self) -> dict:
        return {
            "purpose": self.purpose,
            "recommended_agent_role": self.recommended_agent_role,
            "required_lifecycle_status": self.required_lifecycle_status,
            "step_name": self.step_name,
        }


@dataclass(frozen=True)
class CollaborationWorkflow:
    workflow_name: str
    steps: tuple[WorkflowStep, ...]

    def to_dict(self) -> dict:
        return {
            "steps": [s.to_dict() for s in self.steps],
            "workflow_name": self.workflow_name,
        }


COLLABORATION_WORKFLOWS: tuple[CollaborationWorkflow, ...] = (
    CollaborationWorkflow(
        workflow_name="implementation",
        steps=(
            WorkflowStep(
                step_name="implementer",
                recommended_agent_role="implementation",
                purpose="Produces the implementation output.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
            ),
            WorkflowStep(
                step_name="reviewer",
                recommended_agent_role="analysis",
                purpose="Reviews implementation for correctness.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
            ),
            WorkflowStep(
                step_name="validator",
                recommended_agent_role="governance",
                purpose="Validates governance and quality gates.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
            ),
        ),
    ),
    CollaborationWorkflow(
        workflow_name="documentation",
        steps=(
            WorkflowStep(
                step_name="author",
                recommended_agent_role="documentation",
                purpose="Authors the documentation content.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
            ),
            WorkflowStep(
                step_name="reviewer",
                recommended_agent_role="analysis",
                purpose="Reviews documentation for accuracy.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
            ),
            WorkflowStep(
                step_name="validator",
                recommended_agent_role="governance",
                purpose="Validates governance and quality gates.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
            ),
        ),
    ),
    CollaborationWorkflow(
        workflow_name="architecture",
        steps=(
            WorkflowStep(
                step_name="proposer",
                recommended_agent_role="architecture",
                purpose="Proposes the architectural design.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
            ),
            WorkflowStep(
                step_name="reviewer",
                recommended_agent_role="analysis",
                purpose="Reviews architecture for soundness.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
            ),
            WorkflowStep(
                step_name="validator",
                recommended_agent_role="governance",
                purpose="Validates governance and policy compliance.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
            ),
        ),
    ),
    CollaborationWorkflow(
        workflow_name="handoff",
        steps=(
            WorkflowStep(
                step_name="outgoing_agent",
                recommended_agent_role="any",
                purpose="Transfers session state and context to the incoming agent.",
                required_lifecycle_status=AGENT_STATUS_ACTIVE,
            ),
            WorkflowStep(
                step_name="incoming_agent",
                recommended_agent_role="any",
                purpose="Receives session state and resumes governed work.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
            ),
            WorkflowStep(
                step_name="validator",
                recommended_agent_role="governance",
                purpose="Validates governance continuity after handoff.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
            ),
        ),
    ),
)


def build_collaboration_workflows() -> dict:
    """Return a read-only collaboration workflow template catalogue."""
    return {
        "advisory": COLLABORATION_ADVISORY,
        "workflows": [w.to_dict() for w in COLLABORATION_WORKFLOWS],
    }


# ---------------------------------------------------------------------------
# Review workflow templates (Phase 37H)
# ---------------------------------------------------------------------------

REVIEW_STATUS_PENDING = "pending"
REVIEW_STATUS_REVIEWED = "reviewed"
REVIEW_STATUS_VALIDATED = "validated"
REVIEW_STATUS_REJECTED = "rejected"

VALID_REVIEW_STATUSES: tuple[str, ...] = (
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_REVIEWED,
    REVIEW_STATUS_VALIDATED,
    REVIEW_STATUS_REJECTED,
)

REVIEW_ADVISORY = (
    "Review workflows are advisory; "
    "no agents are executed or assigned automatically."
)


@dataclass(frozen=True)
class ReviewWorkflowStep:
    step_name: str
    recommended_agent_role: str
    purpose: str
    required_lifecycle_status: str
    review_status: str

    def to_dict(self) -> dict:
        return {
            "purpose": self.purpose,
            "recommended_agent_role": self.recommended_agent_role,
            "required_lifecycle_status": self.required_lifecycle_status,
            "review_status": self.review_status,
            "step_name": self.step_name,
        }


@dataclass(frozen=True)
class ReviewWorkflow:
    workflow_name: str
    steps: tuple[ReviewWorkflowStep, ...]

    def to_dict(self) -> dict:
        return {
            "steps": [s.to_dict() for s in self.steps],
            "workflow_name": self.workflow_name,
        }


REVIEW_WORKFLOWS: tuple[ReviewWorkflow, ...] = (
    ReviewWorkflow(
        workflow_name="implementation_review",
        steps=(
            ReviewWorkflowStep(
                step_name="implementer",
                recommended_agent_role="implementation",
                purpose="Produces the implementation subject to review.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
                review_status=REVIEW_STATUS_PENDING,
            ),
            ReviewWorkflowStep(
                step_name="reviewer",
                recommended_agent_role="analysis",
                purpose="Reviews implementation for correctness and completeness.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
                review_status=REVIEW_STATUS_PENDING,
            ),
            ReviewWorkflowStep(
                step_name="validator",
                recommended_agent_role="governance",
                purpose="Validates governance gates and quality standards.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
                review_status=REVIEW_STATUS_PENDING,
            ),
        ),
    ),
    ReviewWorkflow(
        workflow_name="documentation_review",
        steps=(
            ReviewWorkflowStep(
                step_name="author",
                recommended_agent_role="documentation",
                purpose="Authors the documentation subject to review.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
                review_status=REVIEW_STATUS_PENDING,
            ),
            ReviewWorkflowStep(
                step_name="reviewer",
                recommended_agent_role="analysis",
                purpose="Reviews documentation for accuracy and completeness.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
                review_status=REVIEW_STATUS_PENDING,
            ),
            ReviewWorkflowStep(
                step_name="validator",
                recommended_agent_role="governance",
                purpose="Validates governance and documentation standards.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
                review_status=REVIEW_STATUS_PENDING,
            ),
        ),
    ),
    ReviewWorkflow(
        workflow_name="architecture_review",
        steps=(
            ReviewWorkflowStep(
                step_name="proposer",
                recommended_agent_role="architecture",
                purpose="Proposes the architectural design subject to review.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
                review_status=REVIEW_STATUS_PENDING,
            ),
            ReviewWorkflowStep(
                step_name="reviewer",
                recommended_agent_role="analysis",
                purpose="Reviews architecture for soundness and trade-offs.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
                review_status=REVIEW_STATUS_PENDING,
            ),
            ReviewWorkflowStep(
                step_name="validator",
                recommended_agent_role="governance",
                purpose="Validates governance and policy compliance.",
                required_lifecycle_status=AGENT_STATUS_AVAILABLE,
                review_status=REVIEW_STATUS_PENDING,
            ),
        ),
    ),
)


def build_review_workflows() -> dict:
    """Return a read-only review workflow template catalogue."""
    return {
        "advisory": REVIEW_ADVISORY,
        "review_statuses": list(VALID_REVIEW_STATUSES),
        "review_workflows": [w.to_dict() for w in REVIEW_WORKFLOWS],
    }


# ---------------------------------------------------------------------------
# Agent runtime capability discovery (Phase 38A)
# ---------------------------------------------------------------------------

RUNTIME_CAP_YES = "yes"
RUNTIME_CAP_UNKNOWN = "unknown"

RUNTIME_DISCOVERY_ADVISORY = (
    "Runtime discovery is advisory; the user remains authoritative."
)

# Agents to probe: (agent_id, executable_name)
_RUNTIME_PROBE_AGENTS: tuple[tuple[str, str], ...] = (
    ("codex-local", "codex"),
    ("claude-local", "claude"),
    ("kimi-local", "kimi"),
)

# Capability detection keyword sets (all matched against lowercased combined help text).
_KW_NON_INTERACTIVE = (
    "-p ", "--print", " exec ", "exec\n", "full-auto",
    "non-interactive", "noninteractive", "--headless",
)
_KW_STDIN = ("stdin", "from stdin", "pipe", "piped")
_KW_PROMPT_FILE = ("--file", "--prompt-file", "prompt file")
_KW_STRUCTURED_OUTPUT = ("--json", "--output=json", "json output", "output json")
_KW_MCP = ("mcp",)
_KW_HOOKS = ("hook",)
_KW_SUBAGENTS = ("subagent", "sub-agent")
_KW_REMOTE = ("remote",)


@dataclass(frozen=True)
class AgentRuntimeCapabilities:
    installed: bool
    executable_path: str | None
    version: str | None
    interactive_supported: str
    non_interactive_supported: str
    stdin_prompt_supported: str
    prompt_file_supported: str
    structured_output_supported: str
    mcp_supported: str
    hooks_supported: str
    subagents_supported: str
    remote_supported: str
    known_limitations: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "executable_path": self.executable_path,
            "hooks_supported": self.hooks_supported,
            "installed": self.installed,
            "interactive_supported": self.interactive_supported,
            "known_limitations": list(self.known_limitations),
            "mcp_supported": self.mcp_supported,
            "non_interactive_supported": self.non_interactive_supported,
            "prompt_file_supported": self.prompt_file_supported,
            "remote_supported": self.remote_supported,
            "stdin_prompt_supported": self.stdin_prompt_supported,
            "structured_output_supported": self.structured_output_supported,
            "subagents_supported": self.subagents_supported,
            "version": self.version,
        }


@dataclass(frozen=True)
class AgentRuntimeEntry:
    agent_id: str
    executable: str
    capabilities: AgentRuntimeCapabilities

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities.to_dict(),
            "executable": self.executable,
        }


@dataclass(frozen=True)
class RuntimeDiscoveryResult:
    agents: tuple[AgentRuntimeEntry, ...]
    advisory: str

    def to_dict(self) -> dict:
        installed = sum(1 for a in self.agents if a.capabilities.installed)
        return {
            "advisory": self.advisory,
            "agents": [a.to_dict() for a in self.agents],
            "discovery_summary": {
                "agents_checked": len(self.agents),
                "agents_installed": installed,
                "agents_not_installed": len(self.agents) - installed,
            },
        }


def _find_executable(name: str) -> str | None:
    return shutil.which(name)


def _run_probe(cmd: list[str], timeout: int = 5) -> str | None:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
        return (result.stdout + result.stderr).lower()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
        return None


def _extract_version_string(executable: str) -> str | None:
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            stdin=subprocess.DEVNULL,
        )
        output = (result.stdout + result.stderr).strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
        return None
    if not output:
        return None
    match = re.search(r"\bv?(\d+\.\d+[\d.]*)\b", output)
    return match.group(0) if match else output[:80]


def _cap_detect(text: str, keywords: tuple[str, ...]) -> str:
    return RUNTIME_CAP_YES if any(kw in text for kw in keywords) else RUNTIME_CAP_UNKNOWN


def _not_installed_capabilities() -> AgentRuntimeCapabilities:
    return AgentRuntimeCapabilities(
        installed=False,
        executable_path=None,
        version=None,
        interactive_supported=RUNTIME_CAP_UNKNOWN,
        non_interactive_supported=RUNTIME_CAP_UNKNOWN,
        stdin_prompt_supported=RUNTIME_CAP_UNKNOWN,
        prompt_file_supported=RUNTIME_CAP_UNKNOWN,
        structured_output_supported=RUNTIME_CAP_UNKNOWN,
        mcp_supported=RUNTIME_CAP_UNKNOWN,
        hooks_supported=RUNTIME_CAP_UNKNOWN,
        subagents_supported=RUNTIME_CAP_UNKNOWN,
        remote_supported=RUNTIME_CAP_UNKNOWN,
        known_limitations=(),
    )


def _discover_capabilities(agent_id: str, executable: str) -> AgentRuntimeCapabilities:
    path = _find_executable(executable)
    if path is None:
        return _not_installed_capabilities()

    combined: list[str] = []

    main_help = _run_probe([executable, "--help"])
    if main_help:
        combined.append(main_help)

    # Codex-specific: probe subcommands for richer capability signal.
    if executable == "codex":
        for sub in (["codex", "exec", "--help"], ["codex", "mcp", "--help"],
                    ["codex", "mcp-server", "--help"]):
            out = _run_probe(sub)
            if out:
                combined.append(out)

    h = " ".join(combined)

    version = _extract_version_string(executable)

    limitations: list[str] = []
    if not h:
        limitations.append(f"{executable} --help produced no output; capability detection limited.")

    return AgentRuntimeCapabilities(
        installed=True,
        executable_path=path,
        version=version,
        interactive_supported=RUNTIME_CAP_YES,
        non_interactive_supported=_cap_detect(h, _KW_NON_INTERACTIVE),
        stdin_prompt_supported=_cap_detect(h, _KW_STDIN),
        prompt_file_supported=_cap_detect(h, _KW_PROMPT_FILE),
        structured_output_supported=_cap_detect(h, _KW_STRUCTURED_OUTPUT),
        mcp_supported=_cap_detect(h, _KW_MCP),
        hooks_supported=_cap_detect(h, _KW_HOOKS),
        subagents_supported=_cap_detect(h, _KW_SUBAGENTS),
        remote_supported=_cap_detect(h, _KW_REMOTE),
        known_limitations=tuple(limitations),
    )


def build_runtime_discovery() -> RuntimeDiscoveryResult:
    """Return a read-only agent runtime capability discovery report."""
    entries = tuple(
        AgentRuntimeEntry(
            agent_id=agent_id,
            executable=executable,
            capabilities=_discover_capabilities(agent_id, executable),
        )
        for agent_id, executable in _RUNTIME_PROBE_AGENTS
    )
    return RuntimeDiscoveryResult(agents=entries, advisory=RUNTIME_DISCOVERY_ADVISORY)


def read_agent_stale_after_seconds(root: HarnessPath) -> int:
    policy = load_policy(root)
    if not policy.valid:
        raise ValueError(policy.error or "Invalid policy.")
    return policy.agent_stale_after_seconds


# ---------------------------------------------------------------------------
# Agent Adapter Model (Phase 38B)
# ---------------------------------------------------------------------------

ADAPTER_ADVISORY = (
    "Adapter reporting is advisory; no agent runtime is modified."
)


@dataclass(frozen=True)
class AgentAdapterEntry:
    agent_id: str
    adapter_type: str
    lifecycle_status: str
    runtime_installed: bool | None
    runtime_version: str | None
    supports_interactive: str
    supports_non_interactive: str
    supports_mcp: str
    supports_hooks: str
    supports_remote: str
    notes: str

    def to_dict(self) -> dict:
        return {
            "adapter_type": self.adapter_type,
            "agent_id": self.agent_id,
            "lifecycle_status": self.lifecycle_status,
            "notes": self.notes,
            "runtime_installed": self.runtime_installed,
            "runtime_version": self.runtime_version,
            "supports_hooks": self.supports_hooks,
            "supports_interactive": self.supports_interactive,
            "supports_mcp": self.supports_mcp,
            "supports_non_interactive": self.supports_non_interactive,
            "supports_remote": self.supports_remote,
        }


def _build_adapter_entries() -> tuple[AgentAdapterEntry, ...]:
    discovery = build_runtime_discovery()
    runtime_by_id: dict[str, AgentRuntimeCapabilities] = {
        e.agent_id: e.capabilities for e in discovery.agents
    }
    entries: list[AgentAdapterEntry] = []
    for agent in MULTI_AGENT_REGISTRY:
        config = AGENT_CONFIG_REGISTRY.get(agent.agent_id)
        adapter_type = config.adapter_type if config else ADAPTER_TYPE_UNDECLARED
        notes = config.configuration_notes if config else "No configuration entry."

        caps = runtime_by_id.get(agent.agent_id)
        if caps is not None:
            runtime_installed: bool | None = caps.installed
            runtime_version: str | None = caps.version
            supports_interactive = caps.interactive_supported
            supports_non_interactive = caps.non_interactive_supported
            supports_mcp = caps.mcp_supported
            supports_hooks = caps.hooks_supported
            supports_remote = caps.remote_supported
        elif adapter_type == ADAPTER_TYPE_NATIVE:
            runtime_installed = True
            runtime_version = None
            supports_interactive = RUNTIME_CAP_UNKNOWN
            supports_non_interactive = RUNTIME_CAP_UNKNOWN
            supports_mcp = RUNTIME_CAP_UNKNOWN
            supports_hooks = RUNTIME_CAP_UNKNOWN
            supports_remote = RUNTIME_CAP_UNKNOWN
        else:
            runtime_installed = None
            runtime_version = None
            supports_interactive = RUNTIME_CAP_UNKNOWN
            supports_non_interactive = RUNTIME_CAP_UNKNOWN
            supports_mcp = RUNTIME_CAP_UNKNOWN
            supports_hooks = RUNTIME_CAP_UNKNOWN
            supports_remote = RUNTIME_CAP_UNKNOWN

        entries.append(AgentAdapterEntry(
            agent_id=agent.agent_id,
            adapter_type=adapter_type,
            lifecycle_status=agent.status,
            runtime_installed=runtime_installed,
            runtime_version=runtime_version,
            supports_interactive=supports_interactive,
            supports_non_interactive=supports_non_interactive,
            supports_mcp=supports_mcp,
            supports_hooks=supports_hooks,
            supports_remote=supports_remote,
            notes=notes,
        ))
    return tuple(entries)


def build_agent_adapters() -> dict:
    """Return adapter registry combining static config and runtime discovery."""
    adapters = _build_adapter_entries()
    type_counts: dict[str, int] = {}
    for a in adapters:
        type_counts[a.adapter_type] = type_counts.get(a.adapter_type, 0) + 1
    return {
        "adapter_summary": {
            "api": type_counts.get(ADAPTER_TYPE_API, 0),
            "cli": type_counts.get(ADAPTER_TYPE_CLI, 0),
            "desktop_manual": type_counts.get(ADAPTER_TYPE_DESKTOP_MANUAL, 0),
            "native": type_counts.get(ADAPTER_TYPE_NATIVE, 0),
            "total": len(adapters),
            "undeclared": type_counts.get(ADAPTER_TYPE_UNDECLARED, 0),
        },
        "adapters": [a.to_dict() for a in adapters],
        "advisory": ADAPTER_ADVISORY,
    }


def get_agent_adapter(agent_id: str) -> dict | None:
    """Return adapter entry for a single agent, or None if not found."""
    for entry in _build_adapter_entries():
        if entry.agent_id == agent_id:
            data = entry.to_dict()
            data["advisory"] = ADAPTER_ADVISORY
            return data
    return None


# ---------------------------------------------------------------------------
# Capability Record Model (Phase 38C)
# ---------------------------------------------------------------------------

CAP_SOURCE_HELP = "help"
CAP_SOURCE_MANUAL = "manual"

ADAPTER_INSPECT_ADVISORY = (
    "Capabilities are discovered conservatively"
    " and may evolve with Codex CLI versions."
)

CLAUDE_ADAPTER_INSPECT_ADVISORY = (
    "Capabilities are discovered conservatively"
    " and may evolve with Claude CLI versions."
)

KIMI_ADAPTER_INSPECT_ADVISORY = (
    "Capabilities are discovered conservatively"
    " and may evolve with Kimi CLI versions."
)

_ADAPTER_INSPECT_ADVISORY_BY_AGENT_TYPE: dict[str, str] = {
    "claude": CLAUDE_ADAPTER_INSPECT_ADVISORY,
    "kimi": KIMI_ADAPTER_INSPECT_ADVISORY,
}


@dataclass(frozen=True)
class CapabilityRecord:
    name: str
    status: str
    source: str
    notes: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "notes": self.notes,
            "source": self.source,
            "status": self.status,
        }


# Each tuple: (runtime_field_attr, capability_name, yes_note, unknown_note)
# Add new Codex capabilities here without touching any other code.
_CAPABILITY_SPECS: tuple[tuple[str, str, str, str], ...] = (
    (
        "interactive_supported", "interactive",
        "Interactive CLI usage confirmed.",
        "Interactive CLI usage not detected.",
    ),
    (
        "non_interactive_supported", "non_interactive",
        "Non-interactive mode keywords found in help output.",
        "Non-interactive mode keywords not found in help output.",
    ),
    (
        "stdin_prompt_supported", "stdin_prompt",
        "Stdin/pipe prompt keywords found in help output.",
        "Stdin/pipe prompt keywords not found in help output.",
    ),
    (
        "prompt_file_supported", "prompt_file",
        "Prompt file keywords found in help output.",
        "Prompt file keywords not found in help output.",
    ),
    (
        "structured_output_supported", "structured_output",
        "JSON output keywords found in help output.",
        "JSON output keywords not found in help output.",
    ),
    (
        "mcp_supported", "mcp",
        "MCP keywords found in help output.",
        "MCP keywords not found in help output.",
    ),
    (
        "hooks_supported", "hooks",
        "Hook keywords found in help output.",
        "Hook keywords not found in help output.",
    ),
    (
        "subagents_supported", "subagents",
        "Subagent keywords found in help output.",
        "Subagent keywords not found in help output.",
    ),
    (
        "remote_supported", "remote",
        "Remote keywords found in help output.",
        "Remote keywords not found in help output.",
    ),
)


def _build_capability_records(
    caps: AgentRuntimeCapabilities,
) -> tuple[CapabilityRecord, ...]:
    return tuple(
        CapabilityRecord(
            name=cap_name,
            status=getattr(caps, field_attr),
            source=CAP_SOURCE_HELP,
            notes=yes_note if getattr(caps, field_attr) == RUNTIME_CAP_YES else unknown_note,
        )
        for field_attr, cap_name, yes_note, unknown_note in _CAPABILITY_SPECS
    )


def _unknown_capability_records() -> tuple[CapabilityRecord, ...]:
    return tuple(
        CapabilityRecord(
            name=cap_name,
            status=RUNTIME_CAP_UNKNOWN,
            source=CAP_SOURCE_HELP,
            notes=unknown_note,
        )
        for _, cap_name, _, unknown_note in _CAPABILITY_SPECS
    )


def build_adapter_inspection(agent_id: str) -> dict | None:
    """Return deep capability inspection for a single agent, or None if not found."""
    agent = next(
        (a for a in MULTI_AGENT_REGISTRY if a.agent_id == agent_id), None
    )
    if agent is None:
        return None

    config = AGENT_CONFIG_REGISTRY.get(agent_id)
    adapter_type = config.adapter_type if config else ADAPTER_TYPE_UNDECLARED

    discovery = build_runtime_discovery()
    runtime_entry = next(
        (e for e in discovery.agents if e.agent_id == agent_id), None
    )

    if runtime_entry is not None:
        caps = runtime_entry.capabilities
        executable_path = caps.executable_path
        runtime_version = caps.version
        cap_records = (
            _build_capability_records(caps)
            if caps.installed
            else _unknown_capability_records()
        )
        execution_modes: list[str] = []
        if caps.interactive_supported == RUNTIME_CAP_YES:
            execution_modes.append("interactive")
        if caps.non_interactive_supported == RUNTIME_CAP_YES:
            execution_modes.append("non-interactive")
    else:
        executable_path = None
        runtime_version = None
        cap_records = _unknown_capability_records()
        execution_modes = []

    advisory = _ADAPTER_INSPECT_ADVISORY_BY_AGENT_TYPE.get(
        agent.agent_type, ADAPTER_INSPECT_ADVISORY
    )
    return {
        "adapter_type": adapter_type,
        "advisory": advisory,
        "agent_id": agent_id,
        "capabilities": [r.to_dict() for r in cap_records],
        "execution_modes": execution_modes,
        "executable_path": executable_path,
        "runtime_version": runtime_version,
    }


# ---------------------------------------------------------------------------
# Remote Autonomous Coding Foundation (Phase 39A)
# ---------------------------------------------------------------------------

REMOTE_STATUS_ADVISORY = (
    "Remote Autonomous Coding readiness is advisory; no agents are executed."
)

REMOTE_STATUS_READY = "ready"
REMOTE_STATUS_PARTIALLY_READY = "partially_ready"
REMOTE_STATUS_NOT_READY = "not_ready"

REMOTE_SAFETY_NOTES: tuple[str, ...] = (
    "Remote Autonomous Coding is not yet implemented.",
    "No agents will be executed by this command.",
    "Human review and approval required before any remote execution.",
)

_REMOTE_ARCH_HISTORY_PATH = Path(".pcae") / "architecture-history.json"


def _check_architecture_memory_present(root: HarnessPath) -> bool:
    target = root.join(_REMOTE_ARCH_HISTORY_PATH)
    if not target.is_file():
        return False
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return isinstance(data, list) and len(data) > 0


def _build_remote_governance_readiness(root: HarnessPath) -> dict[str, bool]:
    try:
        status = build_agent_status(root)
        session_active = bool(status["locked"]) and not bool(status["stale"])
    except ValueError:
        session_active = False
    return {
        "active_task_present": find_latest_active_task(root) is not None,
        "architecture_memory_present": _check_architecture_memory_present(root),
        "session_active": session_active,
    }


def build_remote_status(root: HarnessPath) -> dict:
    """Return advisory remote autonomous coding readiness status."""
    discovery = build_runtime_discovery()

    available_agents: list[dict] = []
    supported_adapters: set[str] = set()
    missing_caps: list[str] = []

    for entry in discovery.agents:
        caps = entry.capabilities
        if not caps.installed:
            continue
        config = AGENT_CONFIG_REGISTRY.get(entry.agent_id)
        adapter_type = config.adapter_type if config else ADAPTER_TYPE_UNDECLARED
        supported_adapters.add(adapter_type)
        available_agents.append({
            "adapter_type": adapter_type,
            "agent_id": entry.agent_id,
            "hooks": caps.hooks_supported,
            "mcp": caps.mcp_supported,
            "non_interactive": caps.non_interactive_supported,
            "remote": caps.remote_supported,
            "runtime_version": caps.version,
        })
        for cap_name, cap_val in (
            ("non_interactive", caps.non_interactive_supported),
            ("mcp", caps.mcp_supported),
            ("hooks", caps.hooks_supported),
        ):
            if cap_val == RUNTIME_CAP_UNKNOWN:
                missing_caps.append(f"{cap_name} ({entry.agent_id})")

    if not available_agents:
        readiness_status = REMOTE_STATUS_NOT_READY
    elif any(a["non_interactive"] == RUNTIME_CAP_YES for a in available_agents):
        readiness_status = REMOTE_STATUS_READY
    else:
        readiness_status = REMOTE_STATUS_PARTIALLY_READY

    return {
        "advisory": REMOTE_STATUS_ADVISORY,
        "available_agents": available_agents,
        "governance_readiness": _build_remote_governance_readiness(root),
        "missing_capabilities": missing_caps,
        "readiness_status": readiness_status,
        "safety_notes": list(REMOTE_SAFETY_NOTES),
        "supported_adapters": sorted(supported_adapters),
    }


# ---------------------------------------------------------------------------
# Remote Autonomous Coding Execution Policy (Phase 39B)
# ---------------------------------------------------------------------------

REMOTE_POLICY_ADVISORY = (
    "Remote execution policy is advisory; no agents are executed or scheduled."
)

_REMOTE_POLICY_DISALLOWED_OPERATIONS: tuple[str, ...] = (
    "delete_branch",
    "drop_table",
    "force_push",
    "rm_rf",
)


def build_remote_policy() -> dict:
    """Return the advisory remote autonomous coding execution policy."""
    return {
        "advisory": REMOTE_POLICY_ADVISORY,
        "allowed_adapters": ["cli"],
        "allowed_agents": ["claude-local", "codex-local", "kimi-local"],
        "allowed_execution_modes": ["non_interactive"],
        "approval_required": True,
        "disallowed_operations": list(_REMOTE_POLICY_DISALLOWED_OPERATIONS),
        "max_files_changed": None,
        "max_runtime_minutes": None,
        "require_clean_git": True,
        "require_human_approval_before_commit": True,
        "require_human_approval_before_push": True,
        "require_pcae_check": True,
        "require_tests": True,
    }


# ---------------------------------------------------------------------------
# Remote Execution Plan Model (Phase 39C)
# ---------------------------------------------------------------------------

REMOTE_PLAN_ADVISORY = (
    "Remote execution plan is advisory; no agents are executed or scheduled."
)

REMOTE_PLAN_DEFAULT_AGENT = "codex-local"

_REMOTE_PLAN_SAFETY_NOTES: tuple[str, ...] = (
    "No agents will be executed by this plan.",
    "Human review and approval required before any remote execution.",
    "This plan is advisory only.",
)


def build_remote_plan(
    root: HarnessPath,
    requested_agent: str = REMOTE_PLAN_DEFAULT_AGENT,
) -> dict:
    """Return an advisory remote autonomous coding execution plan."""
    policy = build_remote_policy()
    discovery = build_runtime_discovery()
    governance = _build_remote_governance_readiness(root)

    execution_mode = (
        policy["allowed_execution_modes"][0]
        if policy["allowed_execution_modes"]
        else "unknown"
    )

    agent_allowed = requested_agent in policy["allowed_agents"]

    installed_ids = {e.agent_id for e in discovery.agents if e.capabilities.installed}
    agent_installed = requested_agent in installed_ids

    config = AGENT_CONFIG_REGISTRY.get(requested_agent)
    adapter_type = config.adapter_type if config else ADAPTER_TYPE_UNDECLARED
    adapter_allowed = adapter_type in policy["allowed_adapters"]

    agent_entry = next(
        (e for e in discovery.agents if e.agent_id == requested_agent), None
    )
    if agent_entry and agent_entry.capabilities.installed:
        execution_mode_supported = (
            agent_entry.capabilities.non_interactive_supported == RUNTIME_CAP_YES
        )
    else:
        execution_mode_supported = False

    policy_compliance = {
        "adapter_allowed": adapter_allowed,
        "agent_allowed": agent_allowed,
        "compliant": agent_allowed and adapter_allowed,
        "execution_mode_allowed": execution_mode in policy["allowed_execution_modes"],
    }

    required_approvals: list[str] = []
    if policy["approval_required"]:
        required_approvals.append("human approval required before execution")
    if policy["require_human_approval_before_commit"]:
        required_approvals.append("human approval required before commit")
    if policy["require_human_approval_before_push"]:
        required_approvals.append("human approval required before push")

    required_checks: list[str] = []
    if policy["require_clean_git"]:
        required_checks.append("clean git working tree")
    if policy["require_pcae_check"]:
        required_checks.append("pcae check must pass")
    if policy["require_tests"]:
        required_checks.append("tests must pass")

    blockers: list[str] = []
    if not agent_allowed:
        blockers.append(f"agent '{requested_agent}' is not in allowed_agents")
    if not agent_installed:
        blockers.append(f"agent '{requested_agent}' is not installed")
    if not adapter_allowed:
        blockers.append(f"adapter '{adapter_type}' is not in allowed_adapters")
    if agent_installed and not execution_mode_supported:
        blockers.append(
            f"agent '{requested_agent}' does not support execution mode '{execution_mode}'"
        )

    readiness_status = "ready" if not blockers else "blocked"

    return {
        "advisory": REMOTE_PLAN_ADVISORY,
        "blockers": blockers,
        "execution_mode": execution_mode,
        "governance_readiness": governance,
        "policy_compliance": policy_compliance,
        "readiness_status": readiness_status,
        "requested_agent": requested_agent,
        "required_approvals": required_approvals,
        "required_checks": required_checks,
        "safety_notes": list(_REMOTE_PLAN_SAFETY_NOTES),
    }


# ---------------------------------------------------------------------------
# Remote Job Definition Model (Phase 39D)
# ---------------------------------------------------------------------------

REMOTE_JOBS_ADVISORY = (
    "Remote jobs are advisory definitions; no agents are executed."
)

REMOTE_JOB_SUPPORTED_STATUSES: tuple[str, ...] = (
    "draft",
    "awaiting_approval",
    "approved",
    "blocked",
    "ready",
    "completed",
    "failed",
)

REMOTE_JOB_SCHEMA_FIELDS: tuple[str, ...] = (
    "approval_state",
    "created_at",
    "execution_mode",
    "job_id",
    "policy_compliance",
    "requested_agent",
    "requested_task",
    "required_approvals",
    "required_checks",
    "safety_notes",
    "status",
)


def build_remote_jobs() -> dict:
    """Return the advisory remote job registry (empty; no jobs created yet)."""
    return {
        "advisory": REMOTE_JOBS_ADVISORY,
        "job_schema": list(REMOTE_JOB_SCHEMA_FIELDS),
        "jobs": [],
        "supported_statuses": list(REMOTE_JOB_SUPPORTED_STATUSES),
    }


# ---------------------------------------------------------------------------
# Remote Job Validation (Phase 39E)
# ---------------------------------------------------------------------------

REMOTE_VALIDATE_ADVISORY = (
    "Remote job validation is advisory; no agents are executed."
)


def validate_remote_job(job: dict, policy: dict) -> dict:
    """Validate a single remote job definition against policy. Read-only."""
    errors: list[str] = []
    warnings: list[str] = []
    blockers: list[str] = []

    for field in REMOTE_JOB_SCHEMA_FIELDS:
        if field not in job:
            errors.append(f"missing required field: '{field}'")

    status = job.get("status")
    if status is not None and status not in REMOTE_JOB_SUPPORTED_STATUSES:
        errors.append(f"unsupported status: '{status}'")

    requested_agent = job.get("requested_agent")
    if requested_agent is not None:
        if requested_agent not in policy["allowed_agents"]:
            blockers.append(f"agent '{requested_agent}' is not in allowed_agents")

    execution_mode = job.get("execution_mode")
    if execution_mode is not None:
        if execution_mode not in policy["allowed_execution_modes"]:
            blockers.append(f"execution_mode '{execution_mode}' is not allowed")

    required_approvals = job.get("required_approvals")
    if isinstance(required_approvals, list) and len(required_approvals) == 0:
        if policy.get("approval_required"):
            warnings.append("required_approvals is empty but policy requires approval")

    required_checks = job.get("required_checks")
    if isinstance(required_checks, list) and len(required_checks) == 0:
        warnings.append("required_checks is empty")

    compliance = job.get("policy_compliance")
    if isinstance(compliance, dict) and compliance.get("compliant") is False:
        warnings.append("policy_compliance.compliant is false")

    return {
        "blockers": blockers,
        "errors": errors,
        "job_id": job.get("job_id", "(unknown)"),
        "valid": not errors and not blockers,
        "warnings": warnings,
    }


def build_remote_validate(jobs: list | None = None) -> dict:
    """Validate the remote job registry (or a provided list) against policy."""
    policy = build_remote_policy()
    jobs_to_validate: list[dict] = (
        build_remote_jobs()["jobs"] if jobs is None else jobs
    )

    all_errors: list[str] = []
    all_warnings: list[str] = []
    all_blockers: list[str] = []

    for job in jobs_to_validate:
        result = validate_remote_job(job, policy)
        all_errors.extend(result["errors"])
        all_warnings.extend(result["warnings"])
        all_blockers.extend(result["blockers"])

    return {
        "advisory": REMOTE_VALIDATE_ADVISORY,
        "blockers": all_blockers,
        "errors": all_errors,
        "job_count": len(jobs_to_validate),
        "valid": not all_errors and not all_blockers,
        "warnings": all_warnings,
    }


# ---------------------------------------------------------------------------
# Remote Execution Approval Workflow (Phase 39F)
# ---------------------------------------------------------------------------

REMOTE_APPROVALS_ADVISORY = (
    "Remote approvals are advisory; no agents are executed."
)

REMOTE_APPROVAL_STATES: tuple[str, ...] = (
    "pending",
    "approved",
    "denied",
    "expired",
)

REMOTE_APPROVAL_GATES: tuple[str, ...] = (
    "before_execution",
    "before_commit",
    "before_push",
)

_REMOTE_APPROVAL_GATE_DESCRIPTIONS: dict[str, str] = {
    "before_execution": "Human approval required before agent execution begins",
    "before_commit": "Human approval required before committing changes",
    "before_push": "Human approval required before pushing to remote",
}

_REMOTE_APPROVAL_GATE_POLICY_KEYS: dict[str, str] = {
    "before_execution": "approval_required",
    "before_commit": "require_human_approval_before_commit",
    "before_push": "require_human_approval_before_push",
}


def build_remote_approvals(jobs: list | None = None) -> dict:
    """Return the advisory remote execution approval workflow model."""
    policy = build_remote_policy()
    jobs_to_check: list[dict] = (
        build_remote_jobs()["jobs"] if jobs is None else jobs
    )

    approval_gates = [
        {
            "description": _REMOTE_APPROVAL_GATE_DESCRIPTIONS[gate],
            "gate": gate,
            "required": bool(policy[_REMOTE_APPROVAL_GATE_POLICY_KEYS[gate]]),
        }
        for gate in REMOTE_APPROVAL_GATES
    ]

    pending_approvals: list[dict] = []
    for job in jobs_to_check:
        if job.get("approval_state") == "pending":
            pending_approvals.append({
                "gate": "before_execution",
                "job_id": job.get("job_id", "(unknown)"),
                "requested_agent": job.get("requested_agent", "(unknown)"),
                "state": "pending",
            })

    return {
        "advisory": REMOTE_APPROVALS_ADVISORY,
        "approval_gates": approval_gates,
        "approval_states": list(REMOTE_APPROVAL_STATES),
        "pending_approvals": pending_approvals,
    }


# ---------------------------------------------------------------------------
# Remote Execution Adapter Selection (Phase 39G)
# ---------------------------------------------------------------------------

REMOTE_ADAPTERS_ADVISORY = (
    "Remote adapter selection is advisory; no agents are executed."
)


def _score_remote_agent(agent: dict) -> int:
    if not agent["eligible"]:
        return 0
    score = 10
    if agent["remote"] == RUNTIME_CAP_YES:
        score += 2
    elif agent["remote"] == RUNTIME_CAP_UNKNOWN:
        score += 1
    return score


def build_remote_adapters() -> dict:
    """Return an advisory remote adapter selection report."""
    policy = build_remote_policy()
    discovery = build_runtime_discovery()

    discovery_by_id = {e.agent_id: e for e in discovery.agents}

    eligible_agents: list[dict] = []
    selection_notes: list[str] = []

    for agent_id in policy["allowed_agents"]:
        config = AGENT_CONFIG_REGISTRY.get(agent_id)
        adapter_type = config.adapter_type if config else ADAPTER_TYPE_UNDECLARED
        policy_allowed = adapter_type in policy["allowed_adapters"]

        entry = discovery_by_id.get(agent_id)
        if entry:
            caps = entry.capabilities
            runtime_installed = caps.installed
            non_interactive = caps.non_interactive_supported
            remote = caps.remote_supported
            mcp = caps.mcp_supported
            hooks = caps.hooks_supported
            runtime_version = caps.version
        else:
            runtime_installed = False
            non_interactive = RUNTIME_CAP_UNKNOWN
            remote = RUNTIME_CAP_UNKNOWN
            mcp = RUNTIME_CAP_UNKNOWN
            hooks = RUNTIME_CAP_UNKNOWN
            runtime_version = None

        if not policy_allowed:
            eligible = False
            eligibility_reason = (
                f"adapter type '{adapter_type}' not in allowed_adapters"
            )
        elif not runtime_installed:
            eligible = False
            eligibility_reason = "not installed"
        elif non_interactive != RUNTIME_CAP_YES:
            eligible = False
            eligibility_reason = "non-interactive support not confirmed"
        else:
            eligible = True
            if remote == RUNTIME_CAP_YES:
                eligibility_reason = (
                    "installed, non-interactive confirmed, remote confirmed"
                )
            elif remote == RUNTIME_CAP_UNKNOWN:
                eligibility_reason = (
                    "installed, non-interactive confirmed, remote unknown"
                )
                selection_notes.append(
                    f"{agent_id} has unknown remote capability"
                )
            else:
                eligibility_reason = (
                    "installed, non-interactive confirmed, remote not detected"
                )

        missing_capabilities: list[str] = []
        if eligible:
            for cap_name, cap_val in (
                ("mcp", mcp),
                ("hooks", hooks),
                ("remote", remote),
            ):
                if cap_val == RUNTIME_CAP_UNKNOWN:
                    missing_capabilities.append(f"{cap_name} unknown")

        eligible_agents.append({
            "adapter_type": adapter_type,
            "agent_id": agent_id,
            "eligible": eligible,
            "eligibility_reason": eligibility_reason,
            "hooks": hooks,
            "mcp": mcp,
            "missing_capabilities": missing_capabilities,
            "non_interactive": non_interactive,
            "policy_allowed": policy_allowed,
            "remote": remote,
            "runtime_installed": runtime_installed,
            "runtime_version": runtime_version,
        })

    eligible_list = [a for a in eligible_agents if a["eligible"]]
    if eligible_list:
        best = max(eligible_list, key=_score_remote_agent)
        recommended = best["agent_id"]
        rationale = f"{recommended} is {best['eligibility_reason']}."
    else:
        recommended = None
        rationale = "No eligible remote runtime found."

    return {
        "advisory": REMOTE_ADAPTERS_ADVISORY,
        "eligible_agents": eligible_agents,
        "rationale": rationale,
        "recommended_remote_runtime": recommended,
        "selection_notes": selection_notes,
    }


# ---------------------------------------------------------------------------
# Remote Execution Strategy (Phase 39H)
# ---------------------------------------------------------------------------

REMOTE_STRATEGY_ADVISORY = "Runtime selection remains under human control."

REMOTE_SELECTION_STRATEGIES: tuple[str, ...] = (
    "capability_based",
    "human_selected",
    "policy_based",
    "registry_order",
)

_REMOTE_STRATEGY_ADVISORY_NOTES: tuple[str, ...] = (
    "Human selection always takes precedence.",
    "PCAE may recommend runtimes but must not silently choose when human selection is required.",
    "Recommendations remain advisory.",
    "Runtime neutrality is preserved.",
)


def build_remote_strategy() -> dict:
    """Return the advisory remote execution strategy model."""
    return {
        "advisory": REMOTE_STRATEGY_ADVISORY,
        "advisory_notes": list(_REMOTE_STRATEGY_ADVISORY_NOTES),
        "fallback_runtimes": [],
        "human_override_enabled": True,
        "preferred_runtime": None,
        "selection_strategy": "human_selected",
        "supported_strategies": list(REMOTE_SELECTION_STRATEGIES),
        "tie_break_rule": None,
    }


# ---------------------------------------------------------------------------
# Remote Autonomous Coding Dry Run (Phase 40A)
# ---------------------------------------------------------------------------

REMOTE_DRY_RUN_ADVISORY = (
    "Remote dry run is advisory; no agent was executed and no prompt was submitted."
)

_REMOTE_DRY_RUN_SAFETY_NOTES: tuple[str, ...] = (
    "No agent was executed.",
    "The prompt was not submitted to any agent.",
    "This is a preview only.",
)

_REMOTE_DRY_RUN_PROMPT_PREVIEW_MAX = 200


def build_remote_dry_run(
    root: HarnessPath,
    agent_id: str,
    prompt: str,
) -> dict:
    """Return advisory dry-run preview. Raises ValueError for unknown agents."""
    policy = build_remote_policy()
    discovery = build_runtime_discovery()

    known_ids = set(policy["allowed_agents"]) | set(AGENT_CONFIG_REGISTRY.keys())
    if agent_id not in known_ids:
        raise ValueError(
            f"Unknown agent '{agent_id}'. "
            f"Run 'pcae agents show' to list known agents."
        )

    config = AGENT_CONFIG_REGISTRY.get(agent_id)
    adapter_type = config.adapter_type if config else ADAPTER_TYPE_UNDECLARED

    agent_allowed = agent_id in policy["allowed_agents"]
    adapter_allowed = adapter_type in policy["allowed_adapters"]
    execution_mode = (
        policy["allowed_execution_modes"][0]
        if policy["allowed_execution_modes"]
        else "unknown"
    )

    discovery_by_id = {e.agent_id: e for e in discovery.agents}
    entry = discovery_by_id.get(agent_id)
    if entry and entry.capabilities.installed:
        caps = entry.capabilities
        adapter_capabilities = {
            "hooks": caps.hooks_supported,
            "installed": True,
            "mcp": caps.mcp_supported,
            "non_interactive": caps.non_interactive_supported,
            "remote": caps.remote_supported,
            "runtime_version": caps.version,
        }
        agent_installed = True
        non_interactive_ok = caps.non_interactive_supported == RUNTIME_CAP_YES
    else:
        adapter_capabilities = {
            "hooks": RUNTIME_CAP_UNKNOWN,
            "installed": False,
            "mcp": RUNTIME_CAP_UNKNOWN,
            "non_interactive": RUNTIME_CAP_UNKNOWN,
            "remote": RUNTIME_CAP_UNKNOWN,
            "runtime_version": None,
        }
        agent_installed = False
        non_interactive_ok = False

    policy_compliance = {
        "adapter_allowed": adapter_allowed,
        "agent_allowed": agent_allowed,
        "compliant": agent_allowed and adapter_allowed,
        "execution_mode_allowed": execution_mode in policy["allowed_execution_modes"],
    }

    required_approvals: list[str] = []
    if policy["approval_required"]:
        required_approvals.append("human approval required before execution")
    if policy["require_human_approval_before_commit"]:
        required_approvals.append("human approval required before commit")
    if policy["require_human_approval_before_push"]:
        required_approvals.append("human approval required before push")

    required_checks: list[str] = []
    if policy["require_clean_git"]:
        required_checks.append("clean git working tree")
    if policy["require_pcae_check"]:
        required_checks.append("pcae check must pass")
    if policy["require_tests"]:
        required_checks.append("tests must pass")

    blockers: list[str] = []
    if not agent_allowed:
        blockers.append(f"agent '{agent_id}' is not in allowed_agents")
    if not agent_installed:
        blockers.append(f"agent '{agent_id}' is not installed")
    if not adapter_allowed:
        blockers.append(f"adapter type '{adapter_type}' is not in allowed_adapters")
    if agent_installed and not non_interactive_ok:
        blockers.append(
            f"agent '{agent_id}' does not support non-interactive execution"
        )

    prompt_preview = prompt[:_REMOTE_DRY_RUN_PROMPT_PREVIEW_MAX]

    return {
        "adapter_capabilities": adapter_capabilities,
        "advisory": REMOTE_DRY_RUN_ADVISORY,
        "blockers": blockers,
        "dry_run_result": "would_execute" if not blockers else "blocked",
        "execution_mode": execution_mode,
        "policy_compliance": policy_compliance,
        "prompt_preview": prompt_preview,
        "required_approvals": required_approvals,
        "required_checks": required_checks,
        "safety_notes": list(_REMOTE_DRY_RUN_SAFETY_NOTES),
        "selected_agent": agent_id,
    }


# ---------------------------------------------------------------------------
# Remote Job Creation Dry Run (Phase 40B)
# ---------------------------------------------------------------------------

REMOTE_CREATE_DRY_RUN_ADVISORY = (
    "Remote job creation preview is advisory; "
    "no job is persisted and no agent is executed."
)

_REMOTE_CREATE_SAFETY_NOTES: tuple[str, ...] = (
    "No job is persisted.",
    "No agent will be executed.",
    "This preview is for planning purposes only.",
)


def build_remote_create_dry_run(
    root: HarnessPath,
    agent_id: str,
    prompt: str,
) -> dict:
    """Return advisory job creation preview. Raises ValueError for unknown agents."""
    policy = build_remote_policy()

    known_ids = set(policy["allowed_agents"]) | set(AGENT_CONFIG_REGISTRY.keys())
    if agent_id not in known_ids:
        raise ValueError(
            f"Unknown agent '{agent_id}'. "
            f"Run 'pcae agents show' to list known agents."
        )

    config = AGENT_CONFIG_REGISTRY.get(agent_id)
    adapter_type = config.adapter_type if config else ADAPTER_TYPE_UNDECLARED

    agent_allowed = agent_id in policy["allowed_agents"]
    adapter_allowed = adapter_type in policy["allowed_adapters"]
    execution_mode = (
        policy["allowed_execution_modes"][0]
        if policy["allowed_execution_modes"]
        else "unknown"
    )

    policy_compliance = {
        "adapter_allowed": adapter_allowed,
        "agent_allowed": agent_allowed,
        "compliant": agent_allowed and adapter_allowed,
        "execution_mode_allowed": execution_mode in policy["allowed_execution_modes"],
    }

    required_approvals: list[str] = []
    if policy["approval_required"]:
        required_approvals.append("human approval required before execution")
    if policy["require_human_approval_before_commit"]:
        required_approvals.append("human approval required before commit")
    if policy["require_human_approval_before_push"]:
        required_approvals.append("human approval required before push")

    required_checks: list[str] = []
    if policy["require_clean_git"]:
        required_checks.append("clean git working tree")
    if policy["require_pcae_check"]:
        required_checks.append("pcae check must pass")
    if policy["require_tests"]:
        required_checks.append("tests must pass")

    now = datetime.now(timezone.utc)
    job_preview = {
        "approval_state": "pending",
        "created_at": now.isoformat(),
        "dry_run": True,
        "execution_mode": execution_mode,
        "job_id": f"preview-{now.strftime('%Y%m%d-%H%M%S')}",
        "policy_compliance": policy_compliance,
        "requested_agent": agent_id,
        "requested_task": prompt,
        "required_approvals": required_approvals,
        "required_checks": required_checks,
        "safety_notes": list(_REMOTE_CREATE_SAFETY_NOTES),
        "status": "draft",
    }

    result = validate_remote_job(job_preview, policy)
    validation = {
        "blockers": result["blockers"],
        "errors": result["errors"],
        "valid": result["valid"],
        "warnings": result["warnings"],
    }

    return {
        "advisory": REMOTE_CREATE_DRY_RUN_ADVISORY,
        "job_preview": job_preview,
        "validation": validation,
    }


# ---------------------------------------------------------------------------
# Remote Job Persistence Preview (Phase 40C)
# ---------------------------------------------------------------------------

REMOTE_PERSIST_PREVIEW_ADVISORY = (
    "Remote job persistence preview is advisory; "
    "no files are written and no agent is executed."
)

_REMOTE_PERSIST_PREVIEW_SAFETY_NOTES: tuple[str, ...] = (
    "No job file is written.",
    "No agent will be executed.",
    "This preview is for planning purposes only.",
)

_REMOTE_JOBS_OUTPUT_DIR = Path(".pcae") / "remote" / "jobs"


def _generate_unique_job_id(jobs_dir: Path) -> tuple[str, Path]:
    """Return a job_id and its file path that does not collide with any existing file."""
    while True:
        now = datetime.now(timezone.utc)
        job_id = f"job-{now.strftime('%Y%m%d-%H%M%S')}-{now.strftime('%f')}"
        candidate = jobs_dir / f"{job_id}.json"
        if not candidate.exists():
            return job_id, candidate


def build_remote_create_persist_preview(
    root: HarnessPath,
    agent_id: str,
    prompt: str,
) -> dict:
    """Return advisory job persistence preview. Raises ValueError for unknown agents."""
    policy = build_remote_policy()

    known_ids = set(policy["allowed_agents"]) | set(AGENT_CONFIG_REGISTRY.keys())
    if agent_id not in known_ids:
        raise ValueError(
            f"Unknown agent '{agent_id}'. "
            f"Run 'pcae agents show' to list known agents."
        )

    config = AGENT_CONFIG_REGISTRY.get(agent_id)
    adapter_type = config.adapter_type if config else ADAPTER_TYPE_UNDECLARED

    agent_allowed = agent_id in policy["allowed_agents"]
    adapter_allowed = adapter_type in policy["allowed_adapters"]
    execution_mode = (
        policy["allowed_execution_modes"][0]
        if policy["allowed_execution_modes"]
        else "unknown"
    )

    policy_compliance = {
        "adapter_allowed": adapter_allowed,
        "agent_allowed": agent_allowed,
        "compliant": agent_allowed and adapter_allowed,
        "execution_mode_allowed": execution_mode in policy["allowed_execution_modes"],
    }

    required_approvals: list[str] = []
    if policy["approval_required"]:
        required_approvals.append("human approval required before execution")
    if policy["require_human_approval_before_commit"]:
        required_approvals.append("human approval required before commit")
    if policy["require_human_approval_before_push"]:
        required_approvals.append("human approval required before push")

    required_checks: list[str] = []
    if policy["require_clean_git"]:
        required_checks.append("clean git working tree")
    if policy["require_pcae_check"]:
        required_checks.append("pcae check must pass")
    if policy["require_tests"]:
        required_checks.append("tests must pass")

    now = datetime.now(timezone.utc)
    job_id = f"job-{now.strftime('%Y%m%d-%H%M%S')}-{now.strftime('%f')}"
    job_file_path = str(_REMOTE_JOBS_OUTPUT_DIR / f"{job_id}.json")

    job_preview = {
        "approval_state": "pending",
        "created_at": now.isoformat(),
        "execution_mode": execution_mode,
        "job_id": job_id,
        "persist_preview": True,
        "policy_compliance": policy_compliance,
        "requested_agent": agent_id,
        "requested_task": prompt,
        "required_approvals": required_approvals,
        "required_checks": required_checks,
        "safety_notes": list(_REMOTE_PERSIST_PREVIEW_SAFETY_NOTES),
        "status": "draft",
    }

    result = validate_remote_job(job_preview, policy)
    validation = {
        "blockers": result["blockers"],
        "errors": result["errors"],
        "valid": result["valid"],
        "warnings": result["warnings"],
    }

    return {
        "advisory": REMOTE_PERSIST_PREVIEW_ADVISORY,
        "job_file_path": job_file_path,
        "job_preview": job_preview,
        "output_directory": str(_REMOTE_JOBS_OUTPUT_DIR),
        "validation": validation,
    }


# ---------------------------------------------------------------------------
# Real Remote Job Persistence (Phase 40D)
# ---------------------------------------------------------------------------

REMOTE_PERSIST_ADVISORY = "Job persisted. No agent execution has occurred."

_REMOTE_PERSIST_SAFETY_NOTES: tuple[str, ...] = (
    "No agent has been executed.",
    "No prompt has been submitted.",
    "Human approval is required before any execution.",
)


def persist_remote_job(
    root: HarnessPath,
    agent_id: str,
    prompt: str,
) -> dict:
    """Write a remote job definition to disk. Raises ValueError for unknown or disallowed agents."""
    policy = build_remote_policy()

    known_ids = set(policy["allowed_agents"]) | set(AGENT_CONFIG_REGISTRY.keys())
    if agent_id not in known_ids:
        raise ValueError(
            f"Unknown agent '{agent_id}'. "
            f"Run 'pcae agents show' to list known agents."
        )

    if agent_id not in policy["allowed_agents"]:
        raise ValueError(
            f"Agent '{agent_id}' is not allowed by remote execution policy. "
            f"Allowed agents: {', '.join(policy['allowed_agents'])}."
        )

    config = AGENT_CONFIG_REGISTRY.get(agent_id)
    adapter_type = config.adapter_type if config else ADAPTER_TYPE_UNDECLARED

    adapter_allowed = adapter_type in policy["allowed_adapters"]
    execution_mode = (
        policy["allowed_execution_modes"][0]
        if policy["allowed_execution_modes"]
        else "unknown"
    )

    policy_compliance = {
        "adapter_allowed": adapter_allowed,
        "agent_allowed": True,
        "compliant": adapter_allowed,
        "execution_mode_allowed": execution_mode in policy["allowed_execution_modes"],
    }

    required_approvals: list[str] = []
    if policy["approval_required"]:
        required_approvals.append("human approval required before execution")
    if policy["require_human_approval_before_commit"]:
        required_approvals.append("human approval required before commit")
    if policy["require_human_approval_before_push"]:
        required_approvals.append("human approval required before push")

    required_checks: list[str] = []
    if policy["require_clean_git"]:
        required_checks.append("clean git working tree")
    if policy["require_pcae_check"]:
        required_checks.append("pcae check must pass")
    if policy["require_tests"]:
        required_checks.append("tests must pass")

    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_id, job_file = _generate_unique_job_id(jobs_dir)

    now = datetime.now(timezone.utc)
    job: dict = {
        "approval_state": "pending",
        "created_at": now.isoformat(),
        "execution_mode": execution_mode,
        "job_id": job_id,
        "policy_compliance": policy_compliance,
        "requested_agent": agent_id,
        "requested_task": prompt,
        "required_approvals": required_approvals,
        "required_checks": required_checks,
        "safety_notes": list(_REMOTE_PERSIST_SAFETY_NOTES),
        "status": "draft",
    }

    with job_file.open("x", encoding="utf-8", newline="\n") as fh:
        json.dump(job, fh, indent=2, sort_keys=True)
        fh.write("\n")

    return {
        "advisory": REMOTE_PERSIST_ADVISORY,
        "job": job,
        "job_path": str(_REMOTE_JOBS_OUTPUT_DIR / job_file.name),
        "persisted": True,
    }


# ---------------------------------------------------------------------------
# Remote Job Listing (Phase 40E)
# ---------------------------------------------------------------------------

REMOTE_JOBS_LIST_ADVISORY = "Job listing is read-only; no agents are executed."


def load_persisted_jobs(root: HarnessPath) -> dict:
    """Read persisted job files from .pcae/remote/jobs/, newest first. Read-only."""
    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    jobs: list[dict] = []
    warnings: list[str] = []

    if jobs_dir.exists():
        for path in sorted(jobs_dir.glob("*.json"), reverse=True):
            try:
                parsed = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                warnings.append(f"Skipping malformed file {path.name}: {exc}")
                continue
            if not isinstance(parsed, dict):
                warnings.append(f"Skipping malformed file (not a dict): {path.name}")
                continue
            jobs.append(parsed)

    return {
        "advisory": REMOTE_JOBS_LIST_ADVISORY,
        "job_count": len(jobs),
        "jobs": jobs,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Remote Job Inspection (Phase 40F)
# ---------------------------------------------------------------------------

REMOTE_JOB_INSPECT_ADVISORY = "Job inspection is read-only; no agents are executed."


def inspect_persisted_job(root: HarnessPath, job_id: str) -> dict:
    """Read a single persisted job by ID. Raises ValueError on unknown or malformed."""
    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    job_file = jobs_dir / f"{job_id}.json"

    if not job_file.exists():
        raise ValueError(f"Unknown job: {job_id!r}. No file found at {job_file}.")

    try:
        parsed = json.loads(job_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Malformed job file {job_file.name}: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"Malformed job file {job_file.name}: content is not a JSON object.")

    return {
        "advisory": REMOTE_JOB_INSPECT_ADVISORY,
        "job": parsed,
    }


# ---------------------------------------------------------------------------
# Remote Job Approval Mutation (Phase 40G)
# ---------------------------------------------------------------------------

REMOTE_JOB_APPROVAL_ADVISORY = "Approval state updated; no agent execution has occurred."


def _mutate_job_approval(root: HarnessPath, job_id: str, new_approval_state: str) -> dict:
    """Read, mutate approval_state/status, write back. Raises ValueError on bad input."""
    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    job_file = jobs_dir / f"{job_id}.json"

    if not job_file.exists():
        raise ValueError(f"Unknown job: {job_id!r}. No file found at {job_file}.")

    try:
        job = json.loads(job_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Malformed job file {job_file.name}: {exc}") from exc

    if not isinstance(job, dict):
        raise ValueError(f"Malformed job file {job_file.name}: content is not a JSON object.")

    previous_approval_state = job.get("approval_state", "unknown")

    job["approval_state"] = new_approval_state
    if new_approval_state == "approved":
        compliance = job.get("policy_compliance", {})
        compliant = isinstance(compliance, dict) and compliance.get("compliant", False)
        job["status"] = "ready" if compliant else "draft"
    else:
        job["status"] = "blocked"

    with job_file.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(job, fh, indent=2, sort_keys=True)
        fh.write("\n")

    return {
        "advisory": REMOTE_JOB_APPROVAL_ADVISORY,
        "job": job,
        "new_approval_state": new_approval_state,
        "previous_approval_state": previous_approval_state,
        "updated": True,
    }


def approve_remote_job(root: HarnessPath, job_id: str) -> dict:
    """Approve a persisted job. Raises ValueError on unknown or malformed job."""
    return _mutate_job_approval(root, job_id, "approved")


def deny_remote_job(root: HarnessPath, job_id: str) -> dict:
    """Deny a persisted job. Raises ValueError on unknown or malformed job."""
    return _mutate_job_approval(root, job_id, "denied")


# ---------------------------------------------------------------------------
# Remote Execution Readiness Gate (Phase 40H)
# ---------------------------------------------------------------------------

REMOTE_JOB_READINESS_ADVISORY = "Execution readiness is advisory; no agent is executed."


def check_remote_job_readiness(root: HarnessPath, job_id: str) -> dict:
    """Check execution readiness for a persisted job. Read-only, never mutates."""
    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    job_file = jobs_dir / f"{job_id}.json"

    if not job_file.exists():
        raise ValueError(f"Unknown job: {job_id!r}. No file found at {job_file}.")

    try:
        job = json.loads(job_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Malformed job file {job_file.name}: {exc}") from exc

    if not isinstance(job, dict):
        raise ValueError(f"Malformed job file {job_file.name}: content is not a JSON object.")

    policy = build_remote_policy()
    discovery = build_runtime_discovery()

    requested_agent: str = job.get("requested_agent", "")
    execution_mode: str = job.get("execution_mode", "")

    config = AGENT_CONFIG_REGISTRY.get(requested_agent)
    adapter_type = config.adapter_type if config else ADAPTER_TYPE_UNDECLARED

    installed_ids = {e.agent_id for e in discovery.agents if e.capabilities.installed}
    agent_installed = requested_agent in installed_ids

    agent_entry = next(
        (e for e in discovery.agents if e.agent_id == requested_agent), None
    )
    non_interactive_ok = (
        agent_entry is not None
        and agent_entry.capabilities.installed
        and agent_entry.capabilities.non_interactive_supported == RUNTIME_CAP_YES
    )

    missing_fields = [f for f in REMOTE_JOB_SCHEMA_FIELDS if f not in job]
    job_schema_valid = not missing_fields

    compliance = job.get("policy_compliance", {})
    policy_compliance_ok = isinstance(compliance, dict) and bool(compliance.get("compliant"))

    required_checks: list = job.get("required_checks") or []
    required_approvals: list = job.get("required_approvals") or []

    pcae_check_required = "pcae check must pass" in required_checks
    tests_required = "tests must pass" in required_checks
    required_approvals_listed = len(required_approvals) > 0

    checks: dict[str, bool] = {
        "agent_allowed": requested_agent in policy["allowed_agents"],
        "adapter_allowed": adapter_type in policy["allowed_adapters"],
        "approval_state_approved": job.get("approval_state") == "approved",
        "execution_mode_allowed": execution_mode in policy["allowed_execution_modes"],
        "job_schema_valid": job_schema_valid,
        "non_interactive_supported": non_interactive_ok,
        "pcae_check_required": pcae_check_required,
        "policy_compliance": policy_compliance_ok,
        "required_approvals_listed": required_approvals_listed,
        "runtime_installed": agent_installed,
        "status_ready": job.get("status") == "ready",
        "tests_required": tests_required,
    }

    blockers: list[str] = []
    warnings: list[str] = []

    if not job_schema_valid:
        blockers.append(f"missing schema fields: {missing_fields}")
    if not checks["status_ready"]:
        blockers.append(f"job status is '{job.get('status')}', expected 'ready'")
    if not checks["approval_state_approved"]:
        blockers.append(
            f"approval_state is '{job.get('approval_state')}', expected 'approved'"
        )
    if not checks["policy_compliance"]:
        blockers.append("policy_compliance.compliant is not true")
    if not checks["agent_allowed"]:
        blockers.append(f"agent '{requested_agent}' is not in allowed_agents")
    if not checks["adapter_allowed"]:
        blockers.append(f"adapter '{adapter_type}' is not in allowed_adapters")
    if not checks["execution_mode_allowed"]:
        blockers.append(
            f"execution_mode '{execution_mode}' is not in allowed_execution_modes"
        )
    if not checks["runtime_installed"]:
        blockers.append(f"runtime for agent '{requested_agent}' is not installed")
    if not checks["non_interactive_supported"]:
        blockers.append(
            f"agent '{requested_agent}' does not support non-interactive execution"
        )

    try:
        git_changes = read_git_changes(root)
        git_clean = len(git_changes) == 0
    except Exception:
        git_clean = None
        warnings.append("could not determine git working tree status")

    if git_clean is None:
        checks["git_working_tree_clean"] = False
    elif git_clean:
        checks["git_working_tree_clean"] = True
    else:
        checks["git_working_tree_clean"] = False
        blockers.append("git working tree is not clean")

    if not required_approvals_listed:
        warnings.append("required_approvals is empty — ensure approval requirements are captured")
    if not pcae_check_required:
        warnings.append("pcae check requirement not found in required_checks")
    if not tests_required:
        warnings.append("tests requirement not found in required_checks")

    return {
        "advisory": REMOTE_JOB_READINESS_ADVISORY,
        "blockers": blockers,
        "checks": checks,
        "job_id": job.get("job_id", job_id),
        "ready": not blockers,
        "requested_agent": requested_agent,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# First Controlled Agent Execution Preview (Phase 41A)
# ---------------------------------------------------------------------------

REMOTE_EXECUTE_DRY_RUN_ADVISORY = "Execution preview only; no agent was invoked."

_REMOTE_EXECUTE_SAFETY_NOTES: tuple[str, ...] = (
    "No agent was executed.",
    "The prompt was not submitted to any agent.",
    "No files were modified.",
    "This is a preview only; human authorisation is required before execution.",
)

_REMOTE_EXECUTE_PROMPT_PREVIEW_MAX = 200


def _derive_command_preview(agent_id: str, prompt_preview: str) -> str | None:
    """Return a plausible CLI invocation preview, or None if not safely derivable."""
    config = AGENT_CONFIG_REGISTRY.get(agent_id)
    if config is None or config.adapter_type != ADAPTER_TYPE_CLI:
        return None
    hint = config.executable_hint
    if hint is None:
        return None
    safe_prompt = prompt_preview.replace("'", "\\'")
    if agent_id == "codex-local":
        return f"[preview] {hint} exec --sandbox read-only '{safe_prompt}'"
    if agent_id in ("claude-local", "kimi-local"):
        return f"[preview] {hint} -p '{safe_prompt}'"
    return f"[preview] {hint} --prompt '{safe_prompt}'"


def build_remote_execute_dry_run(root: HarnessPath, job_id: str) -> dict:
    """Return advisory execution preview for a persisted job. Never executes an agent."""
    readiness = check_remote_job_readiness(root, job_id)

    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    job_file = jobs_dir / f"{job_id}.json"
    job = json.loads(job_file.read_text(encoding="utf-8"))

    requested_agent: str = job.get("requested_agent", "")
    prompt: str = job.get("requested_task", "")
    prompt_preview = prompt[:_REMOTE_EXECUTE_PROMPT_PREVIEW_MAX]

    readiness_status = "ready" if readiness["ready"] else "blocked"
    dry_run_result = "would_execute" if readiness["ready"] else "blocked"

    execution_preview = {
        "blockers": readiness["blockers"],
        "command_preview": _derive_command_preview(requested_agent, prompt_preview),
        "dry_run_result": dry_run_result,
        "execution_mode": job.get("execution_mode", ""),
        "job_id": readiness["job_id"],
        "prompt_preview": prompt_preview,
        "readiness_status": readiness_status,
        "required_approvals": job.get("required_approvals", []),
        "required_checks": job.get("required_checks", []),
        "safety_notes": list(_REMOTE_EXECUTE_SAFETY_NOTES),
        "selected_agent": requested_agent,
    }

    return {
        "advisory": REMOTE_EXECUTE_DRY_RUN_ADVISORY,
        "execution_preview": execution_preview,
    }


# ---------------------------------------------------------------------------
# First Real Controlled Agent Invocation (Phase 41B)
# ---------------------------------------------------------------------------

REMOTE_INVOKE_ADVISORY = (
    "Agent execution completed under PCAE governance; "
    "no commit or push was performed."
)

_REMOTE_EXECUTIONS_DIR = Path(".pcae") / "remote" / "executions"
_REMOTE_RESULTS_DIR = Path(".pcae") / "remote" / "results"
_INVOKE_TIMEOUT_SECONDS = 300

_INVOKE_UNSUPPORTED_REASON = (
    "non-interactive command syntax is not safely derivable for this agent"
)


_CLAUDE_PERMISSION_MODE_WRITABLE = "acceptEdits"

def _build_invoke_command(
    agent_id: str,
    prompt: str,
    allow_file_changes: bool = False,
) -> list[str] | None:
    """Return the argv for non-interactive agent invocation, or None if unsafe/unknown."""
    if agent_id == "claude-local":
        if allow_file_changes:
            return ["claude", "-p", "--permission-mode", _CLAUDE_PERMISSION_MODE_WRITABLE, prompt]
        return ["claude", "-p", prompt]
    if agent_id == "codex-local":
        sandbox = "workspace-write" if allow_file_changes else "read-only"
        return ["codex", "exec", "--sandbox", sandbox, prompt]
    if agent_id == "kimi-local":
        return ["kimi", "-p", prompt]
    return None


def _run_agent_subprocess(
    command: list[str],
    timeout: int,
) -> subprocess.CompletedProcess:
    """Execute the agent subprocess. Extracted for testability."""
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def invoke_remote_job(root: HarnessPath, job_id: str) -> dict:
    """Invoke the agent for a persisted, approved, ready job under PCAE governance."""
    readiness = check_remote_job_readiness(root, job_id)

    if not readiness["ready"]:
        blocker_lines = "; ".join(readiness["blockers"])
        raise ValueError(
            f"Job '{job_id}' is not ready for execution. Blockers: {blocker_lines}"
        )

    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    job_file = jobs_dir / f"{job_id}.json"
    job = json.loads(job_file.read_text(encoding="utf-8"))

    requested_agent: str = job.get("requested_agent", "")
    prompt: str = job.get("requested_task", "")

    command = _build_invoke_command(requested_agent, prompt)
    if command is None:
        raise ValueError(
            f"Agent '{requested_agent}' cannot be invoked: {_INVOKE_UNSUPPORTED_REASON}."
        )

    started_at = datetime.now(timezone.utc)
    try:
        proc = _run_agent_subprocess(command, _INVOKE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        raise ValueError(
            f"Agent '{requested_agent}' timed out after {_INVOKE_TIMEOUT_SECONDS}s."
        ) from None
    except (FileNotFoundError, OSError) as exc:
        raise ValueError(f"Failed to invoke agent '{requested_agent}': {exc}") from exc
    finished_at = datetime.now(timezone.utc)

    exit_code: int = proc.returncode
    stdout: str = proc.stdout or ""
    stderr: str = proc.stderr or ""
    final_status = "completed" if exit_code == 0 else "failed"
    duration_seconds = round((finished_at - started_at).total_seconds(), 3)
    result_path = str(_REMOTE_RESULTS_DIR / f"{job_id}-result.json")

    results_dir = root.join(_REMOTE_RESULTS_DIR)
    results_dir.mkdir(parents=True, exist_ok=True)
    result_file = results_dir / f"{job_id}-result.json"
    artifact = {
        "advisory": REMOTE_INVOKE_ADVISORY,
        "command": command,
        "duration_seconds": duration_seconds,
        "executed": True,
        "exit_code": exit_code,
        "final_status": final_status,
        "finished_at": finished_at.isoformat(),
        "job_id": job_id,
        "selected_agent": requested_agent,
        "started_at": started_at.isoformat(),
        "stderr": stderr,
        "stdout": stdout,
    }
    with result_file.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(artifact, fh, indent=2, sort_keys=True)
        fh.write("\n")

    job["executed_at"] = started_at.isoformat()
    job["result_path"] = result_path
    job["status"] = final_status
    with job_file.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(job, fh, indent=2, sort_keys=True)
        fh.write("\n")

    return {
        "advisory": REMOTE_INVOKE_ADVISORY,
        "command": command,
        "duration_seconds": duration_seconds,
        "executed": True,
        "exit_code": exit_code,
        "final_status": final_status,
        "finished_at": finished_at.isoformat(),
        "job_id": job_id,
        "output_path": result_path,
        "selected_agent": requested_agent,
        "started_at": started_at.isoformat(),
        "stderr": stderr,
        "stdout": stdout,
    }


# ---------------------------------------------------------------------------
# Controlled File Modification (Phase 42A)
# ---------------------------------------------------------------------------

FILE_MODIFY_ADVISORY = (
    "Files may have been modified, but no commit or push was performed."
)

_FILE_MODIFY_STATUS_NO_CHANGES = "completed_with_no_changes"

# Paths allowed for modification in Phase 42A (prefix match on posix path).
_PHASE_42A_ALLOWED_PREFIXES: tuple[str, ...] = ("docs/", "tasks/")

# Paths unconditionally denied regardless of scope.
_PHASE_42A_DENIED_PREFIXES: tuple[str, ...] = (
    "src/",
    "tests/",
    ".pcae/",
    ".git/",
    ".github/",
)
_PHASE_42A_DENIED_EXACT: frozenset[str] = frozenset(
    {"pyproject.toml", ".pcae/policy.toml"}
)


def _capture_git_head(root: HarnessPath) -> str:
    """Return the short HEAD commit SHA, or 'unknown' if git fails."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(root.path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.stdout.strip() if proc.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _capture_git_changed_files(root: HarnessPath) -> list[str]:
    """
    Return all changed paths after writable execution.

    Uses --untracked-files=all so new files inside untracked directories are
    listed individually rather than collapsed to a directory entry (e.g.
    'docs/new.md' not 'docs/'). Handles renamed files by taking the destination
    path only.
    """
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=str(root.path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            return []
        files = []
        for line in proc.stdout.splitlines():
            if len(line) > 3:
                path_part = line[3:].strip()
                # Renamed files: "old-name -> new-name" — keep destination only.
                if " -> " in path_part:
                    path_part = path_part.split(" -> ", 1)[-1]
                files.append(path_part)
        return files
    except Exception:
        return []


def _capture_diff_summary(root: HarnessPath) -> str:
    """Return a compact diff summary (stat lines). Empty string if none."""
    try:
        proc = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=str(root.path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.stdout.strip() if proc.returncode == 0 else ""
    except Exception:
        return ""


def _validate_file_change_scope(changed_files: list[str]) -> dict:
    """
    Validate changed files against Phase 42A scope rules.

    Returns a dict with 'valid' (bool), 'violations' (list[str]), and 'notes'.
    """
    violations: list[str] = []
    for path in changed_files:
        posix = path.replace("\\", "/").lstrip("/")
        if posix in _PHASE_42A_DENIED_EXACT:
            violations.append(f"scope violation: protected file modified: {path}")
            continue
        denied = any(posix.startswith(prefix) for prefix in _PHASE_42A_DENIED_PREFIXES)
        if denied:
            violations.append(f"scope violation: denied path modified: {path}")
            continue
        allowed = any(posix.startswith(prefix) for prefix in _PHASE_42A_ALLOWED_PREFIXES)
        if not allowed:
            violations.append(
                f"scope violation: path not in allowed scope (docs/, tasks/): {path}"
            )
    return {
        "allowed_prefixes": list(_PHASE_42A_ALLOWED_PREFIXES),
        "denied_prefixes": list(_PHASE_42A_DENIED_PREFIXES),
        "notes": "Phase 42A allows modifications only under docs/ and tasks/.",
        "valid": len(violations) == 0,
        "violations": violations,
    }


def invoke_remote_job_with_file_changes(root: HarnessPath, job_id: str) -> dict:
    """
    Invoke a governed job and allow workspace writes.

    Captures pre/post git state, validates changed files against Phase 42A
    scope rules, and persists change metadata with the execution artifact.
    No commit or push is performed.
    """
    readiness = check_remote_job_readiness(root, job_id)
    if not readiness["ready"]:
        blocker_lines = "; ".join(readiness["blockers"])
        raise ValueError(
            f"Job '{job_id}' is not ready for execution. Blockers: {blocker_lines}"
        )

    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    job_file = jobs_dir / f"{job_id}.json"
    job = json.loads(job_file.read_text(encoding="utf-8"))

    requested_agent: str = job.get("requested_agent", "")
    prompt: str = job.get("requested_task", "")

    command = _build_invoke_command(requested_agent, prompt, allow_file_changes=True)
    if command is None:
        raise ValueError(
            f"Agent '{requested_agent}' cannot be invoked: {_INVOKE_UNSUPPORTED_REASON}."
        )

    pre_execution_head = _capture_git_head(root)

    started_at = datetime.now(timezone.utc)
    try:
        proc = _run_agent_subprocess(command, _INVOKE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        raise ValueError(
            f"Agent '{requested_agent}' timed out after {_INVOKE_TIMEOUT_SECONDS}s."
        ) from None
    except (FileNotFoundError, OSError) as exc:
        raise ValueError(f"Failed to invoke agent '{requested_agent}': {exc}") from exc
    finished_at = datetime.now(timezone.utc)

    exit_code: int = proc.returncode
    stdout: str = proc.stdout or ""
    stderr: str = proc.stderr or ""
    agent_succeeded = exit_code == 0
    duration_seconds = round((finished_at - started_at).total_seconds(), 3)

    # Derive sandbox_mode from command for codex; n/a for other adapters.
    sandbox_mode = "workspace-write" if requested_agent == "codex-local" else "n/a"
    # Derive permission_mode for claude; n/a for other adapters.
    permission_mode = _CLAUDE_PERMISSION_MODE_WRITABLE if requested_agent == "claude-local" else "n/a"

    changed_files = _capture_git_changed_files(root)
    diff_summary = _capture_diff_summary(root)
    scope_validation = _validate_file_change_scope(changed_files)

    if not agent_succeeded:
        final_status = "failed"
    elif scope_validation["violations"]:
        final_status = "failed"
    elif not changed_files:
        final_status = _FILE_MODIFY_STATUS_NO_CHANGES
    else:
        final_status = "completed"

    result_path = str(_REMOTE_RESULTS_DIR / f"{job_id}-result.json")
    results_dir = root.join(_REMOTE_RESULTS_DIR)
    results_dir.mkdir(parents=True, exist_ok=True)
    result_file = results_dir / f"{job_id}-result.json"

    artifact = {
        "advisory": FILE_MODIFY_ADVISORY,
        "changed_files": changed_files,
        "command": command,
        "diff_summary": diff_summary,
        "duration_seconds": duration_seconds,
        "executed": True,
        "exit_code": exit_code,
        "file_changes_allowed": True,
        "final_status": final_status,
        "finished_at": finished_at.isoformat(),
        "job_id": job_id,
        "permission_mode": permission_mode,
        "pre_execution_head": pre_execution_head,
        "sandbox_mode": sandbox_mode,
        "scope_validation": scope_validation,
        "selected_agent": requested_agent,
        "started_at": started_at.isoformat(),
        "stderr": stderr,
        "stdout": stdout,
    }
    with result_file.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(artifact, fh, indent=2, sort_keys=True)
        fh.write("\n")

    job["executed_at"] = started_at.isoformat()
    job["result_path"] = result_path
    job["status"] = final_status
    with job_file.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(job, fh, indent=2, sort_keys=True)
        fh.write("\n")

    return {
        "advisory": FILE_MODIFY_ADVISORY,
        "changed_files": changed_files,
        "command": command,
        "diff_summary": diff_summary,
        "duration_seconds": duration_seconds,
        "executed": True,
        "exit_code": exit_code,
        "final_status": final_status,
        "finished_at": finished_at.isoformat(),
        "job_id": job_id,
        "output_path": result_path,
        "permission_mode": permission_mode,
        "pre_execution_head": pre_execution_head,
        "sandbox_mode": sandbox_mode,
        "scope_validation": scope_validation,
        "selected_agent": requested_agent,
        "started_at": started_at.isoformat(),
        "stderr": stderr,
        "stdout": stdout,
    }


# ---------------------------------------------------------------------------
# Governed Execution Reporting (Phase 41C)
# ---------------------------------------------------------------------------

REMOTE_RESULTS_ADVISORY = (
    "Execution reporting is read-only; no agents are executed."
)

_REMOTE_STDOUT_SUMMARY_MAX = 500
_REMOTE_STDERR_SUMMARY_MAX = 200

OUTPUT_CLASS_CLEAN_STDOUT = "clean_stdout"
OUTPUT_CLASS_STDERR_STATUS = "stderr_with_status_text"
OUTPUT_CLASS_EMPTY = "empty_output"
OUTPUT_CLASS_ERROR = "execution_error"


def _classify_execution_output(stdout: str, stderr: str, exit_code: object) -> str:
    """Classify execution output into one of four normalized categories."""
    if exit_code is not None and exit_code != 0:
        return OUTPUT_CLASS_ERROR
    if not stdout.strip() and not stderr.strip():
        return OUTPUT_CLASS_EMPTY
    if stderr.strip():
        return OUTPUT_CLASS_STDERR_STATUS
    return OUTPUT_CLASS_CLEAN_STDOUT


def _normalize_final_output(stdout: str, classification: str) -> "str | None":
    """Return the normalized final answer text, or None when not applicable."""
    if classification in (OUTPUT_CLASS_ERROR, OUTPUT_CLASS_EMPTY):
        return None
    stripped = stdout.strip()
    return stripped if stripped else None


def build_remote_results(root: HarnessPath, job_id: str) -> dict:
    """Return execution results for a persisted job. Raises ValueError for unknown jobs."""
    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    job_file = jobs_dir / f"{job_id}.json"

    if not job_file.exists():
        raise ValueError(f"Unknown job: {job_id!r}. No file found at {job_file}.")

    try:
        job = json.loads(job_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Malformed job file {job_file.name}: {exc}") from exc

    if not isinstance(job, dict):
        raise ValueError(
            f"Malformed job file {job_file.name}: content is not a JSON object."
        )

    requested_agent: str = job.get("requested_agent", "")

    # Phase 41D: primary location is results/; fall back to executions/ for pre-41D artifacts.
    results_artifact = root.join(_REMOTE_RESULTS_DIR) / f"{job_id}-result.json"
    legacy_artifact = root.join(_REMOTE_EXECUTIONS_DIR) / f"{job_id}_result.json"

    if results_artifact.exists():
        artifact_file = results_artifact
        output_path = str(_REMOTE_RESULTS_DIR / f"{job_id}-result.json")
    elif legacy_artifact.exists():
        artifact_file = legacy_artifact
        output_path = str(_REMOTE_EXECUTIONS_DIR / f"{job_id}_result.json")
    else:
        artifact_file = results_artifact  # canonical path for "not found" message
        output_path = str(_REMOTE_RESULTS_DIR / f"{job_id}-result.json")

    if not artifact_file.exists():
        return {
            "advisory": REMOTE_RESULTS_ADVISORY,
            "execution_result": None,
            "job_id": job_id,
            "requested_agent": requested_agent,
            "result_available": False,
        }

    try:
        artifact = json.loads(artifact_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(
            f"Malformed execution artifact for job {job_id!r}: {exc}"
        ) from exc

    if not isinstance(artifact, dict):
        raise ValueError(
            f"Malformed execution artifact for job {job_id!r}: "
            "content is not a JSON object."
        )

    stdout_full: str = artifact.get("stdout") or ""
    stderr_full: str = artifact.get("stderr") or ""
    exit_code = artifact.get("exit_code")

    classification = _classify_execution_output(stdout_full, stderr_full, exit_code)
    normalized_out = _normalize_final_output(stdout_full, classification)

    execution_result = {
        "command_used": artifact.get("command"),
        "duration_seconds": artifact.get("duration_seconds"),
        "execution_finished_at": (
            artifact.get("finished_at") or artifact.get("execution_finished_at")
        ),
        "execution_started_at": (
            artifact.get("started_at") or artifact.get("execution_started_at")
        ),
        "exit_code": exit_code,
        "final_status": artifact.get("final_status"),
        "normalized_final_output": normalized_out,
        "output_classification": classification,
        "output_path": output_path,
        "readiness_at_execution": artifact.get("readiness_at_execution"),
        "stderr_summary": stderr_full[:_REMOTE_STDERR_SUMMARY_MAX] or None,
        "stdout_summary": stdout_full[:_REMOTE_STDOUT_SUMMARY_MAX] or None,
    }

    return {
        "advisory": REMOTE_RESULTS_ADVISORY,
        "execution_result": execution_result,
        "job_id": job_id,
        "requested_agent": requested_agent,
        "result_available": True,
    }


REMOTE_REGISTRY_ADVISORY = (
    "Execution result registry is read-only; no agents are executed."
)


def build_remote_results_registry(root: HarnessPath) -> dict:
    """List all persisted execution result artifacts, newest first. Read-only."""
    results_dir = root.join(_REMOTE_RESULTS_DIR)
    warnings: list[str] = []
    entries: list[dict] = []

    if results_dir.exists():
        artifact_files = sorted(
            results_dir.glob("*-result.json"), key=lambda p: p.name, reverse=True
        )
        for artifact_file in artifact_files:
            try:
                artifact = json.loads(artifact_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                warnings.append(f"Skipped malformed result file {artifact_file.name}: {exc}")
                continue
            if not isinstance(artifact, dict):
                warnings.append(
                    f"Skipped result file {artifact_file.name}: content is not a JSON object."
                )
                continue
            stdout_val: str = artifact.get("stdout") or ""
            stderr_val: str = artifact.get("stderr") or ""
            exit_code = artifact.get("exit_code")
            classification = _classify_execution_output(stdout_val, stderr_val, exit_code)
            entries.append({
                "duration_seconds": artifact.get("duration_seconds"),
                "exit_code": exit_code,
                "final_status": artifact.get("final_status"),
                "finished_at": artifact.get("finished_at"),
                "job_id": artifact.get("job_id", artifact_file.stem.replace("-result", "")),
                "output_classification": classification,
                "output_path": str(_REMOTE_RESULTS_DIR / artifact_file.name),
                "selected_agent": artifact.get("selected_agent"),
            })

    return {
        "advisory": REMOTE_REGISTRY_ADVISORY,
        "result_count": len(entries),
        "results": entries,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Execution Analytics (Phase 41H)
# ---------------------------------------------------------------------------

REMOTE_ANALYTICS_ADVISORY = (
    "Execution analytics are computed from persisted result artifacts."
)


def _compute_runtime_metrics(entries: list[dict]) -> dict[str, dict]:
    """Aggregate per-agent execution metrics from registry entries."""
    buckets: dict[str, dict] = {}
    for entry in entries:
        agent = entry.get("selected_agent") or "unknown"
        if agent not in buckets:
            buckets[agent] = {"executions": 0, "successes": 0, "failures": 0, "_durs": []}
        buckets[agent]["executions"] += 1
        if entry.get("final_status") == "completed":
            buckets[agent]["successes"] += 1
        else:
            buckets[agent]["failures"] += 1
        dur = entry.get("duration_seconds")
        if dur is not None:
            buckets[agent]["_durs"].append(dur)

    result: dict[str, dict] = {}
    for agent, m in buckets.items():
        durs = m.pop("_durs")
        m["average_duration"] = round(sum(durs) / len(durs), 3) if durs else None
        result[agent] = m
    return result


def build_remote_execution_analytics(root: HarnessPath) -> dict:
    """Compute analytics over persisted execution result artifacts. Read-only."""
    registry = build_remote_results_registry(root)
    entries: list[dict] = registry["results"]
    warnings: list[str] = list(registry["warnings"])

    total = len(entries)
    successful = sum(1 for e in entries if e.get("final_status") == "completed")
    failed = total - successful
    success_rate = round(successful / total, 4) if total > 0 else None

    timed = [e for e in entries if e.get("duration_seconds") is not None]
    durs = [e["duration_seconds"] for e in timed]
    avg_dur = round(sum(durs) / len(durs), 3) if durs else None
    fastest_entry = min(timed, key=lambda e: e["duration_seconds"]) if timed else None
    slowest_entry = max(timed, key=lambda e: e["duration_seconds"]) if timed else None

    dated = [e for e in entries if e.get("finished_at")]
    latest_entry = max(dated, key=lambda e: e["finished_at"]) if dated else None

    def _timing_summary(e: dict | None) -> "dict | None":
        if e is None:
            return None
        return {
            "duration_seconds": e.get("duration_seconds"),
            "final_status": e.get("final_status"),
            "job_id": e.get("job_id"),
            "selected_agent": e.get("selected_agent"),
        }

    def _latest_summary(e: dict | None) -> "dict | None":
        if e is None:
            return None
        return {
            "final_status": e.get("final_status"),
            "finished_at": e.get("finished_at"),
            "job_id": e.get("job_id"),
            "selected_agent": e.get("selected_agent"),
        }

    return {
        "advisory": REMOTE_ANALYTICS_ADVISORY,
        "analytics": {
            "average_duration_seconds": avg_dur,
            "failed_executions": failed,
            "fastest_execution": _timing_summary(fastest_entry),
            "latest_execution": _latest_summary(latest_entry),
            "slowest_execution": _timing_summary(slowest_entry),
            "success_rate": success_rate,
            "successful_executions": successful,
            "total_executions": total,
        },
        "runtime_metrics": _compute_runtime_metrics(entries),
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Execution Report Export (Phase 41I)
# ---------------------------------------------------------------------------

REMOTE_REPORTS_DIR = Path(".pcae") / "remote" / "reports"
REMOTE_REPORT_EXPORT_ADVISORY = (
    "Execution report export is read-only; no agents are executed."
)


def export_remote_execution_report(root: HarnessPath) -> dict:
    """Export an execution report artifact to .pcae/remote/reports/. Returns export metadata."""
    analytics_data = build_remote_execution_analytics(root)
    a = analytics_data["analytics"]
    registry = build_remote_results_registry(root)

    from datetime import datetime, timezone  # noqa: PLC0415
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    exported_at = now.isoformat()

    report = {
        "advisory": REMOTE_REPORT_EXPORT_ADVISORY,
        "exported_at": exported_at,
        "failed_executions": a["failed_executions"],
        "latest_execution": a["latest_execution"],
        "result_registry_summary": {
            "result_count": registry["result_count"],
            "warnings": registry["warnings"],
        },
        "runtime_breakdown": analytics_data["runtime_metrics"],
        "success_rate": a["success_rate"],
        "successful_executions": a["successful_executions"],
        "total_executions": a["total_executions"],
        "warnings": analytics_data["warnings"],
    }

    reports_dir = root.join(REMOTE_REPORTS_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"remote-execution-report-{timestamp}.json"
    report_path = reports_dir / filename
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )

    return {
        "advisory": REMOTE_REPORT_EXPORT_ADVISORY,
        "export_path": str(REMOTE_REPORTS_DIR / filename),
        "exported_at": exported_at,
        "success_rate": a["success_rate"],
        "total_executions": a["total_executions"],
    }


# ---------------------------------------------------------------------------
# Execution Report Inspection (Phase 41J)
# ---------------------------------------------------------------------------

REMOTE_REPORT_INSPECT_ADVISORY = (
    "Report inspection is read-only; no agents are executed."
)

_REQUIRED_REPORT_FIELDS = (
    "advisory",
    "exported_at",
    "failed_executions",
    "latest_execution",
    "result_registry_summary",
    "runtime_breakdown",
    "success_rate",
    "successful_executions",
    "total_executions",
)


def inspect_remote_execution_report(root: HarnessPath, report_path_str: str) -> dict:
    """Inspect an exported execution report file. Read-only; raises ValueError if unreadable."""
    p = Path(report_path_str)
    if not p.is_absolute():
        p = root.join(p)

    if not p.exists():
        raise ValueError(f"Report file not found: {report_path_str!r}")

    try:
        raw = p.read_text(encoding="utf-8")
        report = json.loads(raw)
    except (json.JSONDecodeError, OSError) as exc:
        return {
            "advisory": REMOTE_REPORT_INSPECT_ADVISORY,
            "report": None,
            "report_path": report_path_str,
            "validation_status": "invalid",
            "warnings": [f"Malformed report file: {exc}"],
        }

    if not isinstance(report, dict):
        return {
            "advisory": REMOTE_REPORT_INSPECT_ADVISORY,
            "report": None,
            "report_path": report_path_str,
            "validation_status": "invalid",
            "warnings": ["Report content is not a JSON object."],
        }

    missing = [f for f in _REQUIRED_REPORT_FIELDS if f not in report]
    warnings = [f"Missing required field: {f!r}" for f in missing]
    validation_status = "valid" if not missing else "partial"

    return {
        "advisory": REMOTE_REPORT_INSPECT_ADVISORY,
        "report": report,
        "report_path": report_path_str,
        "validation_status": validation_status,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Execution Trends (Phase 41K)
# ---------------------------------------------------------------------------

REMOTE_TRENDS_ADVISORY = (
    "Execution trends are computed from persisted execution history."
)

_TREND_INSUFFICIENT_DATA = "insufficient_data"
_TREND_INCREASING = "increasing"
_TREND_DECREASING = "decreasing"
_TREND_STABLE = "stable"
_TREND_MIN_EXECUTIONS = 5
_TREND_CHANGE_THRESHOLD = 0.1


def _compute_trend_indicator(ordered_values: list[float]) -> str:
    """Return a trend direction from an ordered (oldest-first) list of numeric values."""
    if len(ordered_values) < _TREND_MIN_EXECUTIONS:
        return _TREND_INSUFFICIENT_DATA
    half = len(ordered_values) // 2
    tail = len(ordered_values) - half
    first_avg = sum(ordered_values[:half]) / half
    second_avg = sum(ordered_values[half:]) / tail
    if first_avg == 0:
        return _TREND_STABLE
    change = (second_avg - first_avg) / abs(first_avg)
    if change > _TREND_CHANGE_THRESHOLD:
        return _TREND_INCREASING
    if change < -_TREND_CHANGE_THRESHOLD:
        return _TREND_DECREASING
    return _TREND_STABLE


def build_remote_execution_trends(root: HarnessPath) -> dict:
    """Compute execution trends over persisted result artifacts. Read-only."""
    from datetime import datetime  # noqa: PLC0415

    registry = build_remote_results_registry(root)
    entries: list[dict] = registry["results"]
    warnings: list[str] = list(registry["warnings"])

    total = len(entries)

    # Sort oldest-first by finished_at; undated entries appended last.
    dated = sorted(
        [e for e in entries if e.get("finished_at")],
        key=lambda e: e["finished_at"],
    )
    undated = [e for e in entries if not e.get("finished_at")]
    sorted_entries = dated + undated

    # Global trend indicators
    if total < _TREND_MIN_EXECUTIONS:
        trend_status = success_rate_trend = average_duration_trend = _TREND_INSUFFICIENT_DATA
    else:
        success_values = [
            1.0 if e.get("final_status") == "completed" else 0.0
            for e in sorted_entries
        ]
        dur_values = [
            e["duration_seconds"]
            for e in sorted_entries
            if e.get("duration_seconds") is not None
        ]
        success_rate_trend = _compute_trend_indicator(success_values)
        average_duration_trend = _compute_trend_indicator(dur_values)
        trend_status = success_rate_trend

    # Execution timespan in seconds
    execution_timespan: "float | None" = None
    if len(dated) >= 2:
        try:
            oldest_ts = datetime.fromisoformat(dated[0]["finished_at"])
            newest_ts = datetime.fromisoformat(dated[-1]["finished_at"])
            execution_timespan = round((newest_ts - oldest_ts).total_seconds(), 1)
        except (ValueError, TypeError):
            pass

    def _summary(e: "dict | None") -> "dict | None":
        if e is None:
            return None
        return {
            "final_status": e.get("final_status"),
            "finished_at": e.get("finished_at"),
            "job_id": e.get("job_id"),
            "selected_agent": e.get("selected_agent"),
        }

    # Per-runtime trends
    runtime_buckets: dict[str, list[dict]] = {}
    for entry in sorted_entries:
        agent = entry.get("selected_agent") or "unknown"
        runtime_buckets.setdefault(agent, []).append(entry)

    runtime_trends: dict[str, dict] = {}
    for agent, bucket in runtime_buckets.items():
        timed = [e for e in bucket if e.get("duration_seconds") is not None]
        durs = [e["duration_seconds"] for e in timed]
        successes = sum(1 for e in bucket if e.get("final_status") == "completed")
        avg_dur = round(sum(durs) / len(durs), 3) if durs else None
        fastest = min(timed, key=lambda e: e["duration_seconds"]) if timed else None
        slowest = max(timed, key=lambda e: e["duration_seconds"]) if timed else None
        runtime_trends[agent] = {
            "average_duration": avg_dur,
            "execution_count": len(bucket),
            "fastest_execution": (
                {"duration_seconds": fastest["duration_seconds"], "job_id": fastest.get("job_id")}
                if fastest else None
            ),
            "slowest_execution": (
                {"duration_seconds": slowest["duration_seconds"], "job_id": slowest.get("job_id")}
                if slowest else None
            ),
            "success_rate": round(successes / len(bucket), 4) if bucket else None,
        }

    return {
        "advisory": REMOTE_TRENDS_ADVISORY,
        "runtime_trends": runtime_trends,
        "trend_summary": {
            "average_duration_trend": average_duration_trend,
            "execution_timespan": execution_timespan,
            "newest_execution": _summary(dated[-1] if dated else None),
            "oldest_execution": _summary(dated[0] if dated else None),
            "success_rate_trend": success_rate_trend,
            "total_executions": total,
            "trend_status": trend_status,
        },
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Runtime Benchmarking (Phase 41L)
# ---------------------------------------------------------------------------

REMOTE_BENCHMARK_ADVISORY = (
    "Runtime benchmarks are computed from persisted execution history."
)

_BENCHMARK_CONFIDENCE_THRESHOLDS = (
    (20, "high"),
    (10, "medium"),
    (5, "low"),
    (0, "insufficient_data"),
)


def _compute_benchmark_confidence(min_executions_per_runtime: int) -> str:
    """Return benchmark confidence level from the minimum per-runtime execution count."""
    for threshold, level in _BENCHMARK_CONFIDENCE_THRESHOLDS:
        if min_executions_per_runtime >= threshold:
            return level
    return "insufficient_data"


def build_remote_runtime_benchmark(root: HarnessPath) -> dict:
    """Compute per-runtime benchmark metrics from persisted result artifacts. Read-only."""
    registry = build_remote_results_registry(root)
    entries: list[dict] = registry["results"]
    warnings: list[str] = list(registry["warnings"])

    total = len(entries)

    # Group by runtime, sorted alphabetically for deterministic rankings.
    runtime_buckets: dict[str, list[dict]] = {}
    for entry in entries:
        agent = entry.get("selected_agent") or "unknown"
        runtime_buckets.setdefault(agent, []).append(entry)

    min_count = min((len(v) for v in runtime_buckets.values()), default=0)
    confidence = _compute_benchmark_confidence(min_count)

    # Per-runtime metrics
    runtime_metrics: dict[str, dict] = {}
    for agent in sorted(runtime_buckets):
        bucket = runtime_buckets[agent]
        timed = [e for e in bucket if e.get("duration_seconds") is not None]
        durs = [e["duration_seconds"] for e in timed]
        successes = sum(1 for e in bucket if e.get("final_status") == "completed")
        avg_dur = round(sum(durs) / len(durs), 3) if durs else None
        fastest_s = round(min(durs), 3) if durs else None
        slowest_s = round(max(durs), 3) if durs else None

        dated = [e for e in bucket if e.get("finished_at")]
        latest = max(dated, key=lambda e: e["finished_at"]) if dated else None

        breakdown: dict[str, int] = {
            OUTPUT_CLASS_CLEAN_STDOUT: 0,
            OUTPUT_CLASS_STDERR_STATUS: 0,
            OUTPUT_CLASS_EMPTY: 0,
            OUTPUT_CLASS_ERROR: 0,
        }
        for e in bucket:
            cls = e.get("output_classification")
            if cls in breakdown:
                breakdown[cls] += 1

        runtime_metrics[agent] = {
            "average_duration_seconds": avg_dur,
            "execution_count": len(bucket),
            "fastest_execution_seconds": fastest_s,
            "latest_execution": (
                {
                    "final_status": latest.get("final_status"),
                    "finished_at": latest.get("finished_at"),
                    "job_id": latest.get("job_id"),
                }
                if latest else None
            ),
            "output_classification_breakdown": breakdown,
            "slowest_execution_seconds": slowest_s,
            "success_rate": round(successes / len(bucket), 4),
        }

    # Rankings — deterministic: alphabetical tie-break via sorted dict order.
    timed_runtimes = {
        a: m for a, m in runtime_metrics.items()
        if m["average_duration_seconds"] is not None
    }
    fastest_runtime = (
        min(timed_runtimes, key=lambda a: timed_runtimes[a]["average_duration_seconds"])
        if timed_runtimes else None
    )
    slowest_runtime = (
        max(timed_runtimes, key=lambda a: timed_runtimes[a]["average_duration_seconds"])
        if timed_runtimes else None
    )
    highest_success_rate = (
        max(runtime_metrics, key=lambda a: runtime_metrics[a]["success_rate"])
        if runtime_metrics else None
    )

    return {
        "advisory": REMOTE_BENCHMARK_ADVISORY,
        "benchmark_summary": {
            "benchmark_confidence": confidence,
            "runtime_count": len(runtime_buckets),
            "total_executions": total,
        },
        "rankings": {
            "fastest_runtime": fastest_runtime,
            "highest_success_rate": highest_success_rate,
            "slowest_runtime": slowest_runtime,
        },
        "runtime_metrics": runtime_metrics,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Controlled Runtime Benchmarking (Phase 41L.1)
# ---------------------------------------------------------------------------

CONTROLLED_BENCHMARK_ADVISORY = (
    "Controlled benchmarks measure end-to-end runtime execution, not pure model performance."
)

_CONTROLLED_BENCHMARK_RUNTIMES: tuple[str, ...] = (
    "claude-local",
    "codex-local",
    "kimi-local",
)
_CONTROLLED_BENCHMARK_PROMPT = "Reply with exactly: PCAE controlled benchmark successful."
_CONTROLLED_BENCHMARK_RUNS_PER_RUNTIME = 3
_CONTROLLED_BENCHMARK_EXECUTION_MODE = "non_interactive"

_CONTROLLED_BENCHMARK_PLANNED_METRICS: tuple[str, ...] = (
    "duration_seconds",
    "exit_code",
    "stdout_length",
    "stderr_length",
    "output_classification",
    "success_or_failure",
)

_CONTROLLED_BENCHMARK_FUTURE_METRICS: tuple[str, ...] = (
    "mean_duration",
    "median_duration",
    "p95_duration",
    "stddev_duration",
    "success_rate",
)

_CONTROLLED_BENCHMARK_LIMITATIONS: tuple[str, ...] = (
    "Duration is end-to-end wall-clock time, not model inference time.",
    "Network latency, system load, and process startup are included in duration.",
    "Rankings are not valid with fewer than the planned runs per runtime.",
    "Human approval is required before any real execution occurs.",
    "This dry-run previews the plan only; no agents are executed.",
)


def build_controlled_benchmark_plan() -> dict:
    """Return the controlled benchmark plan. Read-only; no agents executed."""
    return {
        "advisory": CONTROLLED_BENCHMARK_ADVISORY,
        "benchmark_plan": {
            "execution_mode": _CONTROLLED_BENCHMARK_EXECUTION_MODE,
            "human_approval_required": True,
            "prompt": _CONTROLLED_BENCHMARK_PROMPT,
            "runs_per_runtime": _CONTROLLED_BENCHMARK_RUNS_PER_RUNTIME,
            "runtimes": list(_CONTROLLED_BENCHMARK_RUNTIMES),
            "sandbox_behavior": (
                "sandbox/read-only preserved where supported by the runtime adapter"
            ),
            "total_planned_runs": (
                len(_CONTROLLED_BENCHMARK_RUNTIMES) * _CONTROLLED_BENCHMARK_RUNS_PER_RUNTIME
            ),
        },
        "future_metrics": list(_CONTROLLED_BENCHMARK_FUTURE_METRICS),
        "limitations": list(_CONTROLLED_BENCHMARK_LIMITATIONS),
        "planned_metrics": list(_CONTROLLED_BENCHMARK_PLANNED_METRICS),
    }


# ---------------------------------------------------------------------------
# File Modification Governance Design (Phase 41M)
# ---------------------------------------------------------------------------

FILE_GOVERNANCE_ADVISORY = (
    "This phase defines governance only; no file modifications are performed."
)

_FILE_GOVERNANCE_RISK_LEVELS: tuple[str, ...] = ("low", "medium", "high", "critical")

_FILE_GOVERNANCE_WRITABLE_SCOPE: dict = {
    "allowed_paths": [
        "src/",
        "tests/",
        "docs/",
        "tasks/",
        "CHANGELOG.md",
        "PROJECT_STATUS.md",
    ],
    "denied_paths": [
        ".pcae/agent-lock.json",
        ".pcae/provenance-history.json",
        ".pcae/session.json",
        ".github/",
        ".git/",
    ],
    "generated_artifact_paths": [
        ".pcae/remote/",
        ".pcae/runtime-snapshots/",
        ".pcae/context-packs/",
        ".pcae/continuity-packs/",
        ".pcae/architecture-exports/",
        ".pcae/provenance-exports/",
    ],
    "protected_files": [
        ".pcae/policy.toml",
        "pyproject.toml",
        ".githooks/pre-commit",
    ],
    "repository_root_constraint": (
        "All modifications must remain within the governed repository root. "
        "Paths outside the repository root are unconditionally denied."
    ),
}

_FILE_GOVERNANCE_CHANGE_CAPTURE: dict = {
    "changed_files": "Full list of paths written or deleted during execution.",
    "diff_collection": "Unified diff of every modified file captured before commit.",
    "modification_summary": (
        "Human-readable summary: files added, modified, deleted, and total lines changed."
    ),
    "risk_classification": (
        "Each change is classified low/medium/high/critical based on path sensitivity "
        "and operation type (create < modify < delete)."
    ),
}

_FILE_GOVERNANCE_APPROVAL_WORKFLOW: dict = {
    "approval_checkpoints": [
        "before_execution: human approves the prompt and planned scope.",
        "after_execution: human reviews captured diff before any commit.",
        "before_commit: human approves the commit message and changed files.",
        "before_push: human approves the target branch and remote.",
    ],
    "human_review_required": True,
    "rejection_handling": (
        "Any denied checkpoint aborts the workflow. No partial commits are created. "
        "The working tree is restored to pre-execution state."
    ),
    "re_execution_requirements": (
        "Re-execution requires a new human approval cycle from the "
        "before_execution checkpoint."
    ),
}

_FILE_GOVERNANCE_COMMIT_GOVERNANCE: dict = {
    "commit_approval_requirements": [
        "Human must approve the diff at the after_execution checkpoint.",
        "Human must confirm the commit message before commit is created.",
        "pcae check must pass on the post-execution working tree.",
        "python -m pytest must pass on the post-execution working tree.",
    ],
    "commit_metadata_requirements": [
        "Commit message must identify the governed job ID.",
        "Commit message must identify the agent that produced the changes.",
        "Co-authored-by attribution must be present.",
    ],
    "commit_separated_from_modification": (
        "Execution and commit are separate governed steps. "
        "Agent execution never triggers an automatic commit."
    ),
}

_FILE_GOVERNANCE_PUSH_GOVERNANCE: dict = {
    "branch_restrictions": [
        "Force-push to any branch is unconditionally disallowed.",
        "Direct push to the default branch requires explicit human override.",
        "Push to protected branches requires a pull-request workflow.",
    ],
    "push_approval_requirements": [
        "Human must approve the target branch at the before_push checkpoint.",
        "Human must confirm no protected branch rules are violated.",
    ],
    "push_separated_from_commit": (
        "Commit and push are separate governed steps. "
        "A committed change is never automatically pushed."
    ),
}

_FILE_GOVERNANCE_ROLLBACK_STRATEGY: dict = {
    "recovery_workflow": [
        "Identify the pre-execution commit SHA from the job record.",
        "Human reviews the rollback scope and confirms the target SHA.",
        "git reset --hard <pre-execution SHA> restores the working tree.",
        "pcae check is run to confirm governance health after rollback.",
    ],
    "rollback_artifact_requirements": [
        "Job record must contain the pre-execution git HEAD SHA.",
        "Captured diff must be retained in the execution artifact.",
        "Rollback must be initiated by the human user, not the agent.",
    ],
    "rollback_prerequisites": [
        "Pre-execution HEAD SHA recorded in the job artifact.",
        "Working tree must be clean before rollback is initiated.",
        "No subsequent governed commits may have been pushed to shared remotes.",
    ],
}

_FILE_GOVERNANCE_SAFETY_MODEL: dict = {
    "file_modifying_opt_in": (
        "File-modifying execution is an explicit opt-in flag. "
        "Omitting the flag keeps execution read-only by default."
    ),
    "protected_operation_handling": (
        "Operations matching protected patterns (delete_branch, drop_table, "
        "force_push, rm_rf) are unconditionally blocked regardless of approval state."
    ),
    "read_only_default": (
        "All governed remote executions are read-only by default. "
        "No file is written, committed, or pushed without explicit human approval."
    ),
}

_FILE_GOVERNANCE_RISK_MODEL: dict = {
    "classification_scheme": {
        "critical": "Deletion of protected governance files or irreversible operations.",
        "high": "Modification of policy, CI, hooks, or dependency configuration.",
        "low": "Addition of new source files or documentation with no deletions.",
        "medium": "Modification of existing source or test files.",
    },
    "risk_levels": list(_FILE_GOVERNANCE_RISK_LEVELS),
    "risk_note": (
        "Risk level is advisory. Human review is required at every approval checkpoint "
        "regardless of the computed risk level."
    ),
}


def build_file_governance_design() -> dict:
    """Return the file modification governance design. Read-only; no files modified."""
    return {
        "advisory": FILE_GOVERNANCE_ADVISORY,
        "approval_model": _FILE_GOVERNANCE_APPROVAL_WORKFLOW,
        "governance_design": {
            "approval_workflow": _FILE_GOVERNANCE_APPROVAL_WORKFLOW,
            "change_capture": _FILE_GOVERNANCE_CHANGE_CAPTURE,
            "commit_governance": _FILE_GOVERNANCE_COMMIT_GOVERNANCE,
            "push_governance": _FILE_GOVERNANCE_PUSH_GOVERNANCE,
            "rollback_strategy": _FILE_GOVERNANCE_ROLLBACK_STRATEGY,
            "safety_model": _FILE_GOVERNANCE_SAFETY_MODEL,
            "writable_scope_rules": _FILE_GOVERNANCE_WRITABLE_SCOPE,
        },
        "risk_model": _FILE_GOVERNANCE_RISK_MODEL,
        "rollback_model": _FILE_GOVERNANCE_ROLLBACK_STRATEGY,
    }


# ---------------------------------------------------------------------------
# Phase 42A.3 — Claude Writable Execution Contract Inspection
# Phase 42A.4 — Kimi Writable Execution Contract Inspection
# ---------------------------------------------------------------------------

CLAUDE_WRITABLE_CONTRACT_ADVISORY = (
    "Claude writable contract inspection is advisory and read-only. "
    "No agents are executed, no files are modified, and Claude writable "
    "mode is not enabled by this command."
)

KIMI_WRITABLE_CONTRACT_ADVISORY = (
    "Kimi writable contract inspection is advisory and read-only. "
    "No agents are executed, no files are modified, and Kimi writable "
    "mode is not enabled by this command."
)

WRITABLE_CONTRACT_ADVISORY = (
    "Writable contract inspection is advisory and read-only. "
    "No agents are executed, no files are modified, and writable "
    "mode is not enabled by this command."
)

_CLAUDE_READ_ONLY_INVOCATION = ["claude", "-p", "<prompt>"]

_CLAUDE_KNOWN_READ_ONLY_BEHAVIORS = [
    "claude -p '<prompt>' runs non-interactively and returns output to stdout.",
    "Read-only execution is confirmed: no --sandbox flag is required.",
    "Exit code 0 on success; non-zero on failure.",
    "stdout contains the agent response; stderr may contain status or reasoning text.",
]

_CLAUDE_WRITABLE_UNKNOWNS = [
    "Whether claude -p supports a writable sandbox flag is not yet confirmed.",
    "No --sandbox or equivalent writable flag has been identified in claude --help output.",
    "Writable execution behavior has not been tested under PCAE governance.",
    "Side effects of file modification (scope, extent) are not documented.",
]

_KIMI_READ_ONLY_INVOCATION = ["kimi", "-p", "<prompt>"]

_KIMI_KNOWN_READ_ONLY_BEHAVIORS = [
    "kimi -p '<prompt>' runs non-interactively and returns output to stdout.",
    "Positional prompt invocation ('kimi <prompt>') fails with: too many arguments.",
    "Exit code 0 on success; non-zero on failure.",
    "stdout contains the agent response; stderr may contain status or reasoning text.",
    "Known options: -p/--prompt, --output-format text, --output-format stream-json, "
    "--plan, -S/--session, -C/--continue.",
]

_KIMI_DANGEROUS_FLAGS = [
    "--yolo (-y): bypasses safety checks — not allowed under PCAE governance.",
    "--auto: enables autonomous behavior without explicit per-step approval — "
    "not allowed under PCAE governance.",
]

_KIMI_WRITABLE_UNKNOWNS = [
    "Whether kimi -p supports governed file-write without --yolo or --auto is not confirmed.",
    "Writable execution scope and side effects have not been tested under PCAE governance.",
    "Whether --plan or --session affect file write behavior is not documented.",
    "Interaction between kimi writable mode and PCAE scope validation is not established.",
]


def build_writable_contract(agent_id: str) -> dict:
    """Return the writable execution contract inspection for the given agent.

    Supports claude-local (Phase 42A.3) and kimi-local (Phase 42A.4).
    Returns an error dict for unsupported agents.
    Read-only; no agents are executed and no files are modified.
    """
    if agent_id == "claude-local":
        return {
            "agent_id": agent_id,
            "current_invocation_command": " ".join(_CLAUDE_READ_ONLY_INVOCATION),
            "known_read_only_behavior": _CLAUDE_KNOWN_READ_ONLY_BEHAVIORS,
            "writable_support_status": "unknown",
            "required_flags_if_known": [],
            "dangerous_flags": [],
            "unknowns": _CLAUDE_WRITABLE_UNKNOWNS,
            "safety_recommendation": (
                "Do not enable Claude writable mode until writable flags and sandbox "
                "behavior are confirmed. Conservative default: treat claude-local as "
                "read-only until explicit writable contract is established and approved."
            ),
            "advisory": CLAUDE_WRITABLE_CONTRACT_ADVISORY,
        }

    if agent_id == "kimi-local":
        return {
            "agent_id": agent_id,
            "current_invocation_command": " ".join(_KIMI_READ_ONLY_INVOCATION),
            "known_read_only_behavior": _KIMI_KNOWN_READ_ONLY_BEHAVIORS,
            "writable_support_status": "unknown",
            "required_flags_if_known": [],
            "dangerous_flags": _KIMI_DANGEROUS_FLAGS,
            "unknowns": _KIMI_WRITABLE_UNKNOWNS,
            "safety_recommendation": (
                "Do not enable Kimi writable mode. --yolo and --auto are dangerous "
                "and are not allowed under PCAE governance. Writable behavior without "
                "these flags is unconfirmed. Conservative default: treat kimi-local as "
                "read-only until an explicit writable contract is established and approved."
            ),
            "advisory": KIMI_WRITABLE_CONTRACT_ADVISORY,
        }

    return {
        "agent_id": agent_id,
        "error": f"Writable contract inspection is not available for '{agent_id}'.",
        "advisory": WRITABLE_CONTRACT_ADVISORY,
    }


def build_claude_writable_contract(agent_id: str) -> dict:
    """Compatibility shim — delegates to build_writable_contract."""
    return build_writable_contract(agent_id)


# ---------------------------------------------------------------------------
# Phase 42B — Change Review Artifacts
# ---------------------------------------------------------------------------

CHANGE_REVIEW_ADVISORY = (
    "Change review is advisory; no commit or push is performed."
)

# High-risk path prefixes (config, policy, CI, dependencies).
_CHANGE_REVIEW_HIGH_RISK_PREFIXES: tuple[str, ...] = (
    ".github/",
    ".pcae/",
    "pyproject.toml",
    ".pcae/policy.toml",
)
# Medium-risk path prefixes (source code, tests).
_CHANGE_REVIEW_MEDIUM_RISK_PREFIXES: tuple[str, ...] = ("src/", "tests/")
# Low-risk path prefixes (docs, tasks).
_CHANGE_REVIEW_LOW_RISK_PREFIXES: tuple[str, ...] = ("docs/", "tasks/")


def _classify_change_risk(changed_files: list[str], scope_validation: dict) -> str:
    """
    Classify overall risk level for a set of changed files.

    critical — scope violation present, or destructive/protected paths touched.
    high     — config, policy, CI, or dependency files changed.
    medium   — src/ or tests/ changed.
    low      — docs/ or tasks/ only.

    Returns one of: 'critical', 'high', 'medium', 'low'.
    Read-only; does not modify any files or state.
    """
    if not scope_validation.get("valid", True) or scope_validation.get("violations"):
        return "critical"

    risk = "low"
    for path in changed_files:
        posix = path.replace("\\", "/").lstrip("/")
        if any(
            posix == prefix or posix.startswith(prefix)
            for prefix in _CHANGE_REVIEW_HIGH_RISK_PREFIXES
        ):
            return "high"
        if any(posix.startswith(prefix) for prefix in _CHANGE_REVIEW_MEDIUM_RISK_PREFIXES):
            risk = "medium"
    return risk


def build_change_review(root: HarnessPath, job_id: str) -> dict:
    """
    Build a governed change review artifact for a file-modifying remote execution.

    Reads the persisted job definition and execution result artifact.
    Returns a review dict including changed_files, risk_level, scope_validation,
    approval guidance, and advisory. Read-only; no files are modified.
    Raises ValueError for unknown or malformed job IDs.
    """
    # Load job definition.
    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    job_file = jobs_dir / f"{job_id}.json"

    if not job_file.exists():
        raise ValueError(f"Unknown job: {job_id!r}. No file found at {job_file}.")

    try:
        job = json.loads(job_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Malformed job file for {job_id!r}: {exc}") from exc

    if not isinstance(job, dict):
        raise ValueError(f"Malformed job file for {job_id!r}: content is not a JSON object.")

    requested_agent: str = job.get("requested_agent", "")
    job_final_status: str = job.get("status", "unknown")

    # Load execution result artifact (primary path, then legacy path).
    results_artifact = root.join(_REMOTE_RESULTS_DIR) / f"{job_id}-result.json"
    legacy_artifact = root.join(_REMOTE_EXECUTIONS_DIR) / f"{job_id}_result.json"

    artifact: dict | None = None
    if results_artifact.exists():
        try:
            parsed = json.loads(results_artifact.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                artifact = parsed
        except (json.JSONDecodeError, OSError):
            artifact = None
    elif legacy_artifact.exists():
        try:
            parsed = json.loads(legacy_artifact.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                artifact = parsed
        except (json.JSONDecodeError, OSError):
            artifact = None

    if artifact is None:
        return {
            "advisory": CHANGE_REVIEW_ADVISORY,
            "change_review": {
                "approval_required": True,
                "changed_files": [],
                "commit_allowed": False,
                "diff_summary": "",
                "final_status": job_final_status,
                "job_id": job_id,
                "notes": "No execution result artifact found for this job.",
                "push_allowed": False,
                "requested_agent": requested_agent,
                "risk_level": "unknown",
                "scope_validation": {"valid": False, "violations": [], "notes": "No artifact."},
            },
        }

    changed_files: list[str] = artifact.get("changed_files") or []
    scope_validation: dict = artifact.get("scope_validation") or {
        "valid": True, "violations": [], "notes": ""
    }
    diff_summary: str = artifact.get("diff_summary") or ""
    final_status: str = artifact.get("final_status") or job_final_status

    risk_level = _classify_change_risk(changed_files, scope_validation)

    scope_ok = scope_validation.get("valid", True)
    approval_required = True
    commit_allowed = scope_ok and final_status == "completed"
    push_allowed = False  # push always requires separate human approval

    return {
        "advisory": CHANGE_REVIEW_ADVISORY,
        "change_review": {
            "approval_required": approval_required,
            "changed_files": changed_files,
            "commit_allowed": commit_allowed,
            "diff_summary": diff_summary,
            "final_status": final_status,
            "job_id": job_id,
            "push_allowed": push_allowed,
            "requested_agent": requested_agent,
            "risk_level": risk_level,
            "scope_validation": scope_validation,
        },
    }


# ---------------------------------------------------------------------------
# Phase 42C — Human Approval Gate for Changes
# ---------------------------------------------------------------------------

CHANGE_APPROVAL_ADVISORY = (
    "Change approval updated; no commit or push was performed."
)

_CHANGE_APPROVAL_STATES: tuple[str, ...] = ("pending", "approved", "denied")


def _load_job_and_artifact(
    root: HarnessPath, job_id: str
) -> tuple[dict, dict | None, str]:
    """
    Load the persisted job dict and its result artifact (or None).

    Returns (job, artifact, job_file_path_str).
    Raises ValueError for unknown or malformed jobs.
    """
    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    job_file = jobs_dir / f"{job_id}.json"

    if not job_file.exists():
        raise ValueError(f"Unknown job: {job_id!r}. No file found at {job_file}.")

    try:
        job = json.loads(job_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Malformed job file for {job_id!r}: {exc}") from exc

    if not isinstance(job, dict):
        raise ValueError(f"Malformed job file for {job_id!r}: content is not a JSON object.")

    artifact: dict | None = None
    for candidate in (
        root.join(_REMOTE_RESULTS_DIR) / f"{job_id}-result.json",
        root.join(_REMOTE_EXECUTIONS_DIR) / f"{job_id}_result.json",
    ):
        if candidate.exists():
            try:
                parsed = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    artifact = parsed
                    break
            except (json.JSONDecodeError, OSError):
                pass

    return job, artifact, str(job_file)


def _write_job(job_file_path: str, job: dict) -> None:
    """Write the mutated job dict back to disk."""
    path = Path(job_file_path)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(job, fh, indent=2, sort_keys=True)
        fh.write("\n")


def approve_file_changes(root: HarnessPath, job_id: str) -> dict:
    """
    Approve the file changes produced by a remote execution.

    Rules:
    - Result artifact must exist.
    - changed_files must be non-empty.
    - scope_validation must be valid (no violations).
    - Does not commit or push.

    Returns result dict with updated change_approval_state.
    Raises ValueError on unknown jobs or failed preconditions.
    """
    job, artifact, job_file_path = _load_job_and_artifact(root, job_id)

    if artifact is None:
        raise ValueError(
            f"Cannot approve changes for job {job_id!r}: no result artifact found."
        )

    changed_files: list[str] = artifact.get("changed_files") or []
    if not changed_files:
        raise ValueError(
            f"Cannot approve changes for job {job_id!r}: no files were changed."
        )

    scope_validation: dict = artifact.get("scope_validation") or {}
    if not scope_validation.get("valid", False):
        violations = scope_validation.get("violations", [])
        raise ValueError(
            f"Cannot approve changes for job {job_id!r}: scope validation failed. "
            f"Violations: {violations}"
        )

    previous_state: str = job.get("change_approval_state", "pending")
    job["change_approval_state"] = "approved"
    _write_job(job_file_path, job)

    return {
        "advisory": CHANGE_APPROVAL_ADVISORY,
        "commit_allowed": True,
        "job_id": job_id,
        "new_change_approval_state": "approved",
        "previous_change_approval_state": previous_state,
        "push_allowed": False,
        "updated": True,
    }


def deny_file_changes(root: HarnessPath, job_id: str) -> dict:
    """
    Deny the file changes produced by a remote execution.

    Rules:
    - Result artifact must exist.
    - Denial is allowed regardless of changed_files or scope_validation.
    - Does not commit or push.

    Returns result dict with updated change_approval_state.
    Raises ValueError on unknown jobs or missing artifact.
    """
    job, artifact, job_file_path = _load_job_and_artifact(root, job_id)

    if artifact is None:
        raise ValueError(
            f"Cannot deny changes for job {job_id!r}: no result artifact found."
        )

    previous_state: str = job.get("change_approval_state", "pending")
    job["change_approval_state"] = "denied"
    _write_job(job_file_path, job)

    return {
        "advisory": CHANGE_APPROVAL_ADVISORY,
        "commit_allowed": False,
        "job_id": job_id,
        "new_change_approval_state": "denied",
        "previous_change_approval_state": previous_state,
        "push_allowed": False,
        "updated": True,
    }


# ---------------------------------------------------------------------------
# Phase 42D — Controlled Commit
# ---------------------------------------------------------------------------

CONTROLLED_COMMIT_ADVISORY = "Commit created; no push was performed."


def _run_git_add(
    files: list[str], cwd: str
) -> subprocess.CompletedProcess:
    """Run 'git add -- <files>'. Extracted for testability."""
    return subprocess.run(
        ["git", "add", "--"] + files,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _run_git_commit(
    message: str, cwd: str
) -> subprocess.CompletedProcess:
    """Run 'git commit -m <message>'. Extracted for testability."""
    return subprocess.run(
        ["git", "commit", "-m", message],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def commit_file_changes(root: HarnessPath, job_id: str) -> dict:
    """
    Create a governed git commit for approved file changes.

    Pre-conditions:
    - Result artifact exists.
    - changed_files is non-empty.
    - scope_validation passed.
    - change_approval_state == "approved".
    - Working tree contains all expected changed files.
    - No dirty files beyond the approved changed_files.

    Never pushes. Never approves automatically. Never modifies files.
    Raises ValueError on any blocking condition.
    """
    job, artifact, job_file_path = _load_job_and_artifact(root, job_id)

    if artifact is None:
        raise ValueError(
            f"Cannot commit job {job_id!r}: no result artifact found."
        )

    changed_files: list[str] = artifact.get("changed_files") or []
    if not changed_files:
        raise ValueError(
            f"Cannot commit job {job_id!r}: no files were changed."
        )

    scope_validation: dict = artifact.get("scope_validation") or {}
    if not scope_validation.get("valid", False):
        violations = scope_validation.get("violations", [])
        raise ValueError(
            f"Cannot commit job {job_id!r}: scope validation failed. "
            f"Violations: {violations}"
        )

    approval_state: str = job.get("change_approval_state", "pending")
    if approval_state == "pending":
        raise ValueError(
            f"Cannot commit job {job_id!r}: change approval is pending. "
            "Approve changes first with 'pcae remote changes approve'."
        )
    if approval_state == "denied":
        raise ValueError(
            f"Cannot commit job {job_id!r}: changes were denied."
        )
    if approval_state != "approved":
        raise ValueError(
            f"Cannot commit job {job_id!r}: unexpected approval state {approval_state!r}."
        )

    current_dirty = set(_capture_git_changed_files(root))
    expected = set(changed_files)

    missing_from_tree = expected - current_dirty
    if missing_from_tree:
        raise ValueError(
            f"Cannot commit job {job_id!r}: expected changed files not found in working tree: "
            f"{sorted(missing_from_tree)}"
        )

    unexpected = current_dirty - expected
    if unexpected:
        raise ValueError(
            f"Cannot commit job {job_id!r}: unexpected uncommitted changes found: "
            f"{sorted(unexpected)}. Working tree must only contain the approved changes."
        )

    requested_agent: str = job.get("requested_agent", "unknown")
    commit_message = (
        f"PCAE: {job_id}\n"
        f"\n"
        f"Agent: {requested_agent}\n"
        f"Files: {len(changed_files)}\n"
    )

    try:
        stage_proc = _run_git_add(changed_files, str(root.path))
        if stage_proc.returncode != 0:
            raise ValueError(
                f"Cannot commit job {job_id!r}: git add failed. {stage_proc.stderr.strip()}"
            )

        commit_proc = _run_git_commit(commit_message, str(root.path))
        if commit_proc.returncode != 0:
            raise ValueError(
                f"Cannot commit job {job_id!r}: git commit failed. {commit_proc.stderr.strip()}"
            )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(
            f"Cannot commit job {job_id!r}: git operation timed out."
        ) from exc

    commit_sha = _capture_git_head(root)

    job["commit_sha"] = commit_sha
    job["committed_at"] = datetime.now(timezone.utc).isoformat()
    _write_job(job_file_path, job)

    return {
        "advisory": CONTROLLED_COMMIT_ADVISORY,
        "changed_files": changed_files,
        "commit_sha": commit_sha,
        "committed": True,
        "job_id": job_id,
        "push_allowed": False,
    }


# ---------------------------------------------------------------------------
# Phase 42E — Controlled Push
# ---------------------------------------------------------------------------

CONTROLLED_PUSH_ADVISORY = "Push completed through PCAE governance."


def _get_current_branch(root: HarnessPath) -> str:
    """Return current git branch name, or 'unknown'."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(root.path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.stdout.strip() if proc.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _get_git_remote(root: HarnessPath) -> str:
    """Return first configured remote name, or 'origin' when none found."""
    try:
        proc = subprocess.run(
            ["git", "remote"],
            cwd=str(root.path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        remotes = proc.stdout.strip().splitlines()
        return remotes[0] if remotes else "origin"
    except Exception:
        return "origin"


def _run_git_push(
    remote: str, branch: str, cwd: str
) -> subprocess.CompletedProcess:
    """Run 'git push <remote> HEAD:<branch>'. Extracted for testability."""
    return subprocess.run(
        ["git", "push", remote, f"HEAD:{branch}"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _check_commit_is_ancestor(commit_sha: str, cwd: str) -> bool:
    """Return True if commit_sha is an ancestor of (or equal to) HEAD."""
    try:
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit_sha, "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.returncode == 0
    except Exception:
        return False


def push_file_changes(root: HarnessPath, job_id: str) -> dict:
    """
    Execute a governed git push for an approved and committed job.

    Pre-conditions:
    - Result artifact exists.
    - change_approval_state == "approved".
    - commit_sha recorded on the job (governed commit was created).
    - Working tree is clean.
    - Current HEAD matches the governed commit SHA.

    Never creates commits. Never approves changes. Never modifies files.
    Raises ValueError on any blocking condition.
    """
    job, artifact, job_file_path = _load_job_and_artifact(root, job_id)

    if artifact is None:
        raise ValueError(
            f"Cannot push job {job_id!r}: no result artifact found."
        )

    approval_state: str = job.get("change_approval_state", "pending")
    if approval_state == "pending":
        raise ValueError(
            f"Cannot push job {job_id!r}: change approval is pending. "
            "Approve and commit first."
        )
    if approval_state == "denied":
        raise ValueError(
            f"Cannot push job {job_id!r}: changes were denied."
        )
    if approval_state != "approved":
        raise ValueError(
            f"Cannot push job {job_id!r}: unexpected approval state {approval_state!r}."
        )

    commit_sha: str = job.get("commit_sha") or ""
    if not commit_sha:
        raise ValueError(
            f"Cannot push job {job_id!r}: no governed commit found. "
            "Run 'pcae remote commit' first."
        )

    dirty = _capture_git_changed_files(root)
    if dirty:
        raise ValueError(
            f"Cannot push job {job_id!r}: working tree is dirty. "
            f"Unexpected changes: {dirty}"
        )

    current_head = _capture_git_head(root)
    if current_head == "unknown":
        raise ValueError(
            f"Cannot push job {job_id!r}: could not determine current HEAD."
        )

    warnings: list[str] = []
    if current_head == commit_sha:
        lineage_status = "exact_match"
    else:
        if not _check_commit_is_ancestor(commit_sha, str(root.path)):
            raise ValueError(
                f"Cannot push job {job_id!r}: governed commit ({commit_sha!r}) "
                f"is not in current branch history (HEAD: {current_head!r})."
            )
        lineage_status = "ancestor"
        warnings.append("Additional commits exist after the governed commit.")

    branch = _get_current_branch(root)
    remote = _get_git_remote(root)
    remote_branch = f"{remote}/{branch}"

    try:
        push_proc = _run_git_push(remote, branch, str(root.path))
    except subprocess.TimeoutExpired as exc:
        raise ValueError(
            f"Cannot push job {job_id!r}: git push timed out."
        ) from exc

    if push_proc.returncode != 0:
        raise ValueError(
            f"Cannot push job {job_id!r}: git push failed. {push_proc.stderr.strip()}"
        )

    push_status = "pushed"

    job["pushed_at"] = datetime.now(timezone.utc).isoformat()
    job["push_status"] = push_status
    job["remote_branch"] = remote_branch
    _write_job(job_file_path, job)

    return {
        "advisory": CONTROLLED_PUSH_ADVISORY,
        "commit_sha": commit_sha,
        "job_id": job_id,
        "lineage_status": lineage_status,
        "push_status": push_status,
        "pushed": True,
        "remote_branch": remote_branch,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Phase 43A — Governed Rollback Design
# ---------------------------------------------------------------------------

ROLLBACK_GOVERNANCE_ADVISORY = (
    "Rollback governance is advisory; no rollback is performed."
)

_ROLLBACK_ELIGIBILITY_MODEL: dict = {
    "required_conditions": [
        "Governed job exists in .pcae/remote/jobs/.",
        "Result artifact exists in .pcae/remote/results/.",
        "commit_sha is recorded on the job (governed commit was created).",
        "Governed commit is reachable from the current branch.",
        "Working tree is clean.",
        "Rollback target (pre-execution HEAD SHA) is identified.",
    ],
    "blocking_conditions": [
        "No governed job record.",
        "No result artifact.",
        "No commit_sha on job (commit was never created).",
        "Governed commit not reachable from current branch.",
        "Working tree is dirty.",
        "Rollback target SHA unknown or unavailable.",
    ],
}

_ROLLBACK_MODES: list = [
    {
        "mode": "revert_commit",
        "description": (
            "Create a new git revert commit that undoes the governed commit. "
            "Preserves full commit history."
        ),
        "preferred": True,
        "allowed_by_default": True,
        "risk_level": "medium",
        "notes": "Preferred rollback mode. Non-destructive; history is preserved.",
    },
    {
        "mode": "restore_files",
        "description": (
            "Restore changed files to their pre-execution state without "
            "creating a revert commit."
        ),
        "preferred": False,
        "allowed_by_default": True,
        "risk_level": "medium",
        "notes": (
            "Available when a revert commit is not suitable. "
            "Requires a separate governed commit and approval."
        ),
    },
    {
        "mode": "reset_branch",
        "description": (
            "Reset the branch pointer to a prior SHA. "
            "Destructive; rewrites history."
        ),
        "preferred": False,
        "allowed_by_default": False,
        "risk_level": "critical",
        "notes": (
            "Dangerous. Not allowed by default. "
            "Requires explicit future policy override and human approval."
        ),
    },
]

_ROLLBACK_SAFETY_RULES: list = [
    "revert_commit is preferred over reset_branch.",
    "No destructive reset without explicit future policy override.",
    "No automatic rollback; human approval is required.",
    "No push after rollback unless separately approved.",
    "Rollback review required before rollback approval.",
    "Rollback commit is separate from rollback push.",
    "Human remains authoritative at every rollback checkpoint.",
]

_ROLLBACK_ARTIFACT_FIELDS: dict = {
    "rollback_plan": "Description of the rollback approach and scope.",
    "affected_files": "List of files that would be restored or reverted.",
    "original_commit": "The governed commit SHA being rolled back.",
    "rollback_commit": "The SHA of the revert commit, if created.",
    "risk_level": "Risk classification of the rollback operation.",
    "approval_state": "Human approval state: pending, approved, or denied.",
}

_ROLLBACK_RISK_MODEL: dict = {
    "levels": [
        {
            "level": "low",
            "description": "Rollback of docs/ or tasks/ only changes.",
        },
        {
            "level": "medium",
            "description": "Rollback of src/ or tests/ changes.",
        },
        {
            "level": "high",
            "description": "Rollback of config, policy, CI, or dependency files.",
        },
        {
            "level": "critical",
            "description": "Branch reset or other destructive rollback operation.",
        },
    ],
    "risk_note": (
        "Risk level is advisory. Human review is required at every rollback "
        "checkpoint regardless of the computed risk level."
    ),
}

_ROLLBACK_APPROVAL_MODEL: dict = {
    "approval_gates": [
        "before_rollback_execution",
        "before_rollback_commit",
        "before_rollback_push",
    ],
    "auto_rollback_allowed": False,
    "notes": (
        "Rollback review and approval are separate governance steps. "
        "No rollback is executed, committed, or pushed without explicit human approval."
    ),
    "rollback_approval_required": True,
    "rollback_commit_separate": True,
    "rollback_push_separate": True,
    "rollback_review_required": True,
}


def build_rollback_governance() -> dict:
    """Return the rollback governance design. Read-only; no files modified, no rollback performed."""
    return {
        "advisory": ROLLBACK_GOVERNANCE_ADVISORY,
        "approval_model": _ROLLBACK_APPROVAL_MODEL,
        "risk_model": _ROLLBACK_RISK_MODEL,
        "rollback_governance": {
            "eligibility_model": _ROLLBACK_ELIGIBILITY_MODEL,
            "rollback_artifacts": _ROLLBACK_ARTIFACT_FIELDS,
            "safety_rules": _ROLLBACK_SAFETY_RULES,
        },
        "rollback_modes": _ROLLBACK_MODES,
    }


# ---------------------------------------------------------------------------
# Phase 43B — Rollback Review Artifacts
# ---------------------------------------------------------------------------

ROLLBACK_REVIEW_ADVISORY = "Rollback review is advisory; no rollback is performed."

# ---------------------------------------------------------------------------
# Phase 43C — Rollback Approval Gate
# ---------------------------------------------------------------------------

ROLLBACK_APPROVAL_ADVISORY = "Rollback approval updated; no rollback was performed."

_ROLLBACK_APPROVAL_STATES: tuple[str, ...] = ("pending", "approved", "denied")


def approve_rollback(root: HarnessPath, job_id: str) -> dict:
    """
    Approve a rollback plan for a specific job.

    Rules:
    - Rollback review must indicate eligible (result artifact, commit_sha,
      and changed_files are all present).
    - Does not execute rollback, git revert, git reset, commit, or push.

    Returns result dict with updated rollback_approval_state.
    Raises ValueError on unknown jobs or ineligible rollback.
    """
    review_data = build_rollback_review(root, job_id)
    review = review_data["rollback_review"]

    if not review["rollback_eligible"]:
        notes = review.get("eligibility_notes", [])
        raise ValueError(
            f"Cannot approve rollback for job {job_id!r}: rollback is not eligible. "
            f"Notes: {notes}"
        )

    job, _artifact, job_file_path = _load_job_and_artifact(root, job_id)

    previous_state: str = job.get("rollback_approval_state", "pending")
    job["rollback_approval_state"] = "approved"
    _write_job(job_file_path, job)

    return {
        "advisory": ROLLBACK_APPROVAL_ADVISORY,
        "job_id": job_id,
        "new_rollback_approval_state": "approved",
        "previous_rollback_approval_state": previous_state,
        "rollback_eligible": True,
        "rollback_mode_recommendation": review["rollback_mode_recommendation"],
        "updated": True,
    }


def deny_rollback(root: HarnessPath, job_id: str) -> dict:
    """
    Deny a rollback plan for a specific job.

    Rules:
    - Denial is allowed for any rollback-reviewed job, eligible or not.
    - Does not execute rollback, git revert, git reset, commit, or push.

    Returns result dict with updated rollback_approval_state.
    Raises ValueError on unknown or malformed jobs.
    """
    review_data = build_rollback_review(root, job_id)
    review = review_data["rollback_review"]

    job, _artifact, job_file_path = _load_job_and_artifact(root, job_id)

    previous_state: str = job.get("rollback_approval_state", "pending")
    job["rollback_approval_state"] = "denied"
    _write_job(job_file_path, job)

    return {
        "advisory": ROLLBACK_APPROVAL_ADVISORY,
        "job_id": job_id,
        "new_rollback_approval_state": "denied",
        "previous_rollback_approval_state": previous_state,
        "rollback_eligible": review["rollback_eligible"],
        "rollback_mode_recommendation": review["rollback_mode_recommendation"],
        "updated": True,
    }


# ---------------------------------------------------------------------------
# Phase 43D — Controlled Rollback Execution
# ---------------------------------------------------------------------------

CONTROLLED_ROLLBACK_ADVISORY = "Rollback commit created; no push was performed."


def _run_git_revert(commit_sha: str, cwd: str) -> subprocess.CompletedProcess:
    """Run 'git revert --no-edit <commit_sha>'. Extracted for testability."""
    return subprocess.run(
        ["git", "revert", "--no-edit", commit_sha],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )


def execute_rollback(root: HarnessPath, job_id: str) -> dict:
    """
    Execute a governed rollback using git revert for an approved rollback plan.

    Pre-conditions:
    - rollback_approval_state == "approved".
    - Rollback review is eligible (original commit SHA + changed_files present).
    - rollback_mode_recommendation == "revert_commit".
    - Working tree is clean.
    - Original governed commit is reachable from HEAD.

    Idempotent: if rollback_commit_sha is already recorded on the job,
    returns already_rolled_back without running git revert again.

    Runs: git revert --no-edit <original_commit_sha>
    Captures rollback commit SHA. Persists rollback metadata on the job file.
    Never pushes. Never resets. Never modifies files beyond the revert commit.
    Raises ValueError on any blocking condition.
    """
    review_data = build_rollback_review(root, job_id)
    review = review_data["rollback_review"]

    job, _artifact, job_file_path = _load_job_and_artifact(root, job_id)

    existing_rollback_sha: str = job.get("rollback_commit_sha") or ""
    if existing_rollback_sha:
        return {
            "advisory": CONTROLLED_ROLLBACK_ADVISORY,
            "job_id": job_id,
            "original_commit_sha": review["original_commit_sha"],
            "rollback_commit_sha": existing_rollback_sha,
            "rollback_status": "already_rolled_back",
            "rolled_back": True,
        }

    rollback_approval_state: str = job.get("rollback_approval_state", "pending")
    if rollback_approval_state == "pending":
        raise ValueError(
            f"Cannot execute rollback for job {job_id!r}: rollback approval is pending. "
            "Approve the rollback first with 'pcae remote rollback approve'."
        )
    if rollback_approval_state == "denied":
        raise ValueError(
            f"Cannot execute rollback for job {job_id!r}: rollback was denied."
        )
    if rollback_approval_state != "approved":
        raise ValueError(
            f"Cannot execute rollback for job {job_id!r}: unexpected rollback approval state "
            f"{rollback_approval_state!r}."
        )

    if not review["rollback_eligible"]:
        notes = review.get("eligibility_notes", [])
        raise ValueError(
            f"Cannot execute rollback for job {job_id!r}: rollback is not eligible. "
            f"Notes: {notes}"
        )

    if review["rollback_mode_recommendation"] != "revert_commit":
        raise ValueError(
            f"Cannot execute rollback for job {job_id!r}: mode is "
            f"{review['rollback_mode_recommendation']!r}; only 'revert_commit' is supported."
        )

    original_commit_sha: str = review["original_commit_sha"]

    dirty = _capture_git_changed_files(root)
    if dirty:
        raise ValueError(
            f"Cannot execute rollback for job {job_id!r}: working tree is dirty. "
            f"Unexpected changes: {dirty}"
        )

    if not _check_commit_is_ancestor(original_commit_sha, str(root.path)):
        raise ValueError(
            f"Cannot execute rollback for job {job_id!r}: original governed commit "
            f"({original_commit_sha!r}) is not reachable from HEAD."
        )

    revert_proc = _run_git_revert(original_commit_sha, str(root.path))
    if revert_proc.returncode != 0:
        raise ValueError(
            f"Rollback failed for job {job_id!r}: git revert exited "
            f"{revert_proc.returncode}. stderr: {revert_proc.stderr.strip()!r}"
        )

    rollback_commit_sha = _capture_git_head(root)

    job["rollback_commit_sha"] = rollback_commit_sha
    job["rollback_status"] = "rolled_back"
    job["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
    _write_job(job_file_path, job)

    return {
        "advisory": CONTROLLED_ROLLBACK_ADVISORY,
        "job_id": job_id,
        "original_commit_sha": original_commit_sha,
        "rollback_commit_sha": rollback_commit_sha,
        "rollback_status": "rolled_back",
        "rolled_back": True,
    }


# ---------------------------------------------------------------------------
# Phase 43E — Controlled Rollback Push
# ---------------------------------------------------------------------------

ROLLBACK_PUSH_ADVISORY = "Rollback push completed through PCAE governance."

_ROLLBACK_EXECUTED_STATUSES: tuple[str, ...] = ("rolled_back", "already_rolled_back")


def push_rollback(root: HarnessPath, job_id: str) -> dict:
    """
    Push the rollback commit for an approved and executed rollback.

    Pre-conditions:
    - rollback_approval_state == "approved".
    - rollback_commit_sha is recorded on the job.
    - rollback_status is "rolled_back" or "already_rolled_back".
    - Working tree is clean.
    - Rollback commit is reachable from HEAD.

    Never creates commits. Never approves automatically. Never modifies files.
    Raises ValueError on any blocking condition.
    """
    job, _artifact, job_file_path = _load_job_and_artifact(root, job_id)

    rollback_approval_state: str = job.get("rollback_approval_state", "pending")
    if rollback_approval_state == "pending":
        raise ValueError(
            f"Cannot push rollback for job {job_id!r}: rollback approval is pending. "
            "Approve the rollback first with 'pcae remote rollback approve'."
        )
    if rollback_approval_state == "denied":
        raise ValueError(
            f"Cannot push rollback for job {job_id!r}: rollback was denied."
        )
    if rollback_approval_state != "approved":
        raise ValueError(
            f"Cannot push rollback for job {job_id!r}: unexpected rollback approval state "
            f"{rollback_approval_state!r}."
        )

    rollback_commit_sha: str = job.get("rollback_commit_sha") or ""
    if not rollback_commit_sha:
        raise ValueError(
            f"Cannot push rollback for job {job_id!r}: no rollback commit found. "
            "Run 'pcae remote rollback execute' first."
        )

    rollback_status: str = job.get("rollback_status") or ""
    if rollback_status not in _ROLLBACK_EXECUTED_STATUSES:
        raise ValueError(
            f"Cannot push rollback for job {job_id!r}: rollback was not successfully executed "
            f"(status: {rollback_status!r})."
        )

    dirty = _capture_git_changed_files(root)
    if dirty:
        raise ValueError(
            f"Cannot push rollback for job {job_id!r}: working tree is dirty. "
            f"Unexpected changes: {dirty}"
        )

    if not _check_commit_is_ancestor(rollback_commit_sha, str(root.path)):
        raise ValueError(
            f"Cannot push rollback for job {job_id!r}: rollback commit "
            f"({rollback_commit_sha!r}) is not reachable from HEAD."
        )

    branch = _get_current_branch(root)
    remote = _get_git_remote(root)
    remote_branch = f"{remote}/{branch}"

    try:
        push_proc = _run_git_push(remote, branch, str(root.path))
    except subprocess.TimeoutExpired as exc:
        raise ValueError(
            f"Cannot push rollback for job {job_id!r}: git push timed out."
        ) from exc

    if push_proc.returncode != 0:
        raise ValueError(
            f"Cannot push rollback for job {job_id!r}: git push failed. "
            f"{push_proc.stderr.strip()}"
        )

    job["rollback_pushed_at"] = datetime.now(timezone.utc).isoformat()
    job["rollback_push_status"] = "pushed"
    job["rollback_remote_branch"] = remote_branch
    _write_job(job_file_path, job)

    return {
        "advisory": ROLLBACK_PUSH_ADVISORY,
        "job_id": job_id,
        "push_status": "pushed",
        "pushed": True,
        "remote_branch": remote_branch,
        "rollback_commit_sha": rollback_commit_sha,
    }


def build_rollback_review(root: HarnessPath, job_id: str) -> dict:
    """
    Generate a governed rollback review artifact for a specific job.

    Reads the persisted job and execution result artifact.
    Returns a review dict with rollback eligibility, recommendation,
    risk level, and approval guidance. Read-only; no files modified,
    no rollback performed.
    Raises ValueError for unknown or malformed job IDs.
    """
    jobs_dir = root.join(_REMOTE_JOBS_OUTPUT_DIR)
    job_file = jobs_dir / f"{job_id}.json"

    if not job_file.exists():
        raise ValueError(f"Unknown job: {job_id!r}. No file found at {job_file}.")

    try:
        job = json.loads(job_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Malformed job file for {job_id!r}: {exc}") from exc

    if not isinstance(job, dict):
        raise ValueError(f"Malformed job file for {job_id!r}: content is not a JSON object.")

    requested_agent: str = job.get("requested_agent", "")
    original_commit_sha: str = job.get("commit_sha") or ""

    artifact: dict | None = None
    for candidate in (
        root.join(_REMOTE_RESULTS_DIR) / f"{job_id}-result.json",
        root.join(_REMOTE_EXECUTIONS_DIR) / f"{job_id}_result.json",
    ):
        if candidate.exists():
            try:
                parsed = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    artifact = parsed
                    break
            except (json.JSONDecodeError, OSError):
                pass

    eligibility_notes: list[str] = []
    if artifact is None:
        eligibility_notes.append("No result artifact found.")
    if not original_commit_sha:
        eligibility_notes.append("No governed commit recorded on job.")

    changed_files: list[str] = []
    scope_validation: dict = {}

    if artifact is not None:
        changed_files = artifact.get("changed_files") or []
        scope_validation = artifact.get("scope_validation") or {}
        if not changed_files:
            eligibility_notes.append("No files were changed in this execution.")

    rollback_eligible = len(eligibility_notes) == 0

    rollback_risk_level: str
    if changed_files:
        rollback_risk_level = _classify_change_risk(changed_files, scope_validation)
    else:
        rollback_risk_level = "unknown"

    rollback_mode_recommendation = "revert_commit" if rollback_eligible else "not_applicable"

    return {
        "advisory": ROLLBACK_REVIEW_ADVISORY,
        "rollback_review": {
            "affected_files": changed_files,
            "eligibility_notes": eligibility_notes,
            "job_id": job_id,
            "original_commit_sha": original_commit_sha,
            "requested_agent": requested_agent,
            "rollback_approval_required": True,
            "rollback_commit_required": True,
            "rollback_eligible": rollback_eligible,
            "rollback_mode_recommendation": rollback_mode_recommendation,
            "rollback_push_required": True,
            "rollback_risk_level": rollback_risk_level,
        },
    }


# ---------------------------------------------------------------------------
# Multi-Agent Collaboration Design (Phase 44A)
# ---------------------------------------------------------------------------

COLLABORATION_DESIGN_ADVISORY = (
    "Multi-agent collaboration design is advisory; no orchestration is performed."
)

_COLLABORATION_AGENT_ROLES: tuple[dict, ...] = (
    {
        "role": "planner",
        "description": "Decomposes work and produces an execution plan.",
        "may_modify_files": False,
    },
    {
        "role": "implementer",
        "description": "Modifies files and creates governed execution results.",
        "may_modify_files": True,
    },
    {
        "role": "reviewer",
        "description": "Reviews changes and produces review artifacts.",
        "may_modify_files": False,
    },
    {
        "role": "validator",
        "description": "Runs checks/tests and validates outcomes.",
        "may_modify_files": False,
    },
)

_COLLABORATION_RUNTIME_MAPPING: tuple[dict, ...] = (
    {
        "agent_id": "codex-local",
        "supported_roles": ["planner", "implementer", "reviewer", "validator"],
    },
    {
        "agent_id": "claude-local",
        "supported_roles": ["planner", "implementer", "reviewer", "validator"],
    },
    {
        "agent_id": "kimi-local",
        "supported_roles": ["planner", "implementer", "reviewer", "validator"],
    },
)

_COLLABORATION_PATTERNS: tuple[dict, ...] = (
    {
        "pattern": "single-agent",
        "description": "One agent acts as planner, implementer, and reviewer.",
        "steps": ["planner == implementer == reviewer"],
    },
    {
        "pattern": "dual-agent",
        "description": "One agent plans, another implements.",
        "steps": ["planner", "implementer"],
    },
    {
        "pattern": "review",
        "description": "Implementer hands off to a separate reviewer.",
        "steps": ["implementer", "reviewer"],
    },
    {
        "pattern": "validation",
        "description": "Implementer hands off to a separate validator.",
        "steps": ["implementer", "validator"],
    },
    {
        "pattern": "full-pipeline",
        "description": "Full four-stage pipeline: plan → implement → review → validate.",
        "steps": ["planner", "implementer", "reviewer", "validator"],
    },
)

_COLLABORATION_GOVERNANCE_RULES: tuple[str, ...] = (
    "implementer may modify files",
    "planner may not modify files",
    "reviewer may not modify files",
    "validator may not modify files",
    "review required before approval",
    "approval required before commit",
    "commit required before push",
)

_COLLABORATION_CONFLICT_MODEL: tuple[dict, ...] = (
    {
        "condition": "reviewer rejects",
        "outcome": "execution halted",
    },
    {
        "condition": "validator fails",
        "outcome": "execution halted",
    },
    {
        "condition": "scope validation fails",
        "outcome": "execution halted",
    },
)

_COLLABORATION_FUTURE_EXTENSIONS: tuple[str, ...] = (
    "agent voting",
    "multiple reviewers",
    "consensus thresholds",
    "agent specialization",
    "remote/cloud agents",
)


def build_collaboration_design() -> dict:
    """Return a read-only multi-agent collaboration architecture design."""
    return {
        "collaboration_design": {
            "agent_roles": list(_COLLABORATION_AGENT_ROLES),
            "collaboration_patterns": list(_COLLABORATION_PATTERNS),
        },
        "runtime_mapping": list(_COLLABORATION_RUNTIME_MAPPING),
        "governance_model": {
            "rules": list(_COLLABORATION_GOVERNANCE_RULES),
        },
        "conflict_model": list(_COLLABORATION_CONFLICT_MODEL),
        "future_extensions": list(_COLLABORATION_FUTURE_EXTENSIONS),
        "advisory": COLLABORATION_DESIGN_ADVISORY,
    }
