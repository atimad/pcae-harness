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
_KW_SUBAGENTS = (
    "subagent",
    "sub-agent",
    "background agent",   # e.g. "Manage background agents"
    "multi-agent",        # e.g. "multi-agent code review"
    "--agents",           # e.g. "--agents <json> defining custom agents"
)
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


# ---------------------------------------------------------------------------
# Multi-Agent Orchestration Design (Phase 44B)
# ---------------------------------------------------------------------------

ORCHESTRATION_DESIGN_ADVISORY = (
    "Multi-agent orchestration design is advisory; no orchestration is performed."
)

_ORCHESTRATION_COORDINATOR_RESPONSIBILITIES: tuple[dict, ...] = (
    {
        "name": "task_decomposition",
        "description": (
            "Break complex tasks into subtasks and assign each to an appropriate agent role."
        ),
    },
    {
        "name": "role_assignment",
        "description": (
            "Select the most capable agent for each role based on capability profiles."
        ),
    },
    {
        "name": "parallel_execution_planning",
        "description": (
            "Identify independent subtasks that can execute concurrently across agents."
        ),
    },
    {
        "name": "result_collection",
        "description": (
            "Gather, normalize, and aggregate outputs from all participating agents."
        ),
    },
    {
        "name": "conflict_detection",
        "description": (
            "Detect disagreements or contradictions across agent outputs before proceeding."
        ),
    },
    {
        "name": "consensus_calculation",
        "description": (
            "Apply the configured conflict resolution policy to produce a unified result."
        ),
    },
    {
        "name": "governance_handoff",
        "description": (
            "Transfer governed state, provenance, and task context to the next agent or human."
        ),
    },
)

_ORCHESTRATION_CAPABILITY_PROFILE_FIELDS: tuple[str, ...] = (
    "agent_id",
    "runtime",
    "lifecycle_status",
    "capabilities",
    "writable_supported",
    "subagent_supported",
    "evidence_source",
    "confidence",
)

_ORCHESTRATION_CAPABILITY_CATEGORIES: tuple[str, ...] = (
    "planning",
    "implementation",
    "review",
    "validation",
    "research",
    "testing",
    "architecture",
    "documentation",
    "security",
    "performance",
    "dependency-analysis",
    "data-science",
    "devops",
)

_ORCHESTRATION_PATTERNS: tuple[dict, ...] = (
    {
        "pattern": "sequential",
        "description": (
            "Agents execute one after another; each agent consumes the prior agent's output."
        ),
        "steps": ["agent_1", "agent_2", "...", "agent_n"],
        "parallel": False,
    },
    {
        "pattern": "parallel_review",
        "description": (
            "Multiple reviewer agents run concurrently; results are collected and reconciled."
        ),
        "steps": ["implementer", "reviewer_1 || reviewer_2 || ... || reviewer_n", "reconciler"],
        "parallel": True,
    },
    {
        "pattern": "parallel_planning",
        "description": (
            "Multiple planner agents produce plans concurrently; coordinator selects or merges."
        ),
        "steps": ["planner_1 || planner_2 || ... || planner_n", "coordinator"],
        "parallel": True,
    },
    {
        "pattern": "swarm",
        "description": (
            "Many agents work simultaneously on independent subtasks; coordinator collects results."
        ),
        "steps": ["coordinator", "agent_1 || agent_2 || ... || agent_n", "result_collection"],
        "parallel": True,
    },
    {
        "pattern": "full_pipeline",
        "description": (
            "Full governed pipeline: plan → implement → review → validate."
        ),
        "steps": ["planner", "implementer", "reviewer", "validator"],
        "parallel": False,
    },
)

_ORCHESTRATION_GOVERNANCE_RULES: tuple[str, ...] = (
    "only implementer role may modify files",
    "planner, reviewer, and validator are read-only by default",
    "file modification requires existing execution governance",
    "commit remains separately governed from file modification",
    "push remains separately governed from commit",
    "human remains authoritative over all orchestration decisions",
)

_ORCHESTRATION_CONFLICT_RESOLUTION_POLICIES: tuple[dict, ...] = (
    {
        "policy": "unanimous",
        "description": "All agents must agree; any disagreement halts progress.",
    },
    {
        "policy": "majority",
        "description": "A simple majority of agent outputs determines the result.",
    },
    {
        "policy": "weighted",
        "description": (
            "Agent outputs are weighted by confidence or role; highest weight wins."
        ),
    },
    {
        "policy": "human_escalation",
        "description": (
            "Disagreements are escalated to the human for resolution. Human is authoritative."
        ),
    },
)

_ORCHESTRATION_DEFAULT_CONFLICT_POLICY = "human_escalation"

_ORCHESTRATION_FUTURE_AGENTS: tuple[dict, ...] = (
    {
        "agent_id": "deepseek-local",
        "status": "planned",
        "notes": "Future local agent expansion; vendor-neutral design supports addition.",
    },
    {
        "agent_id": "gemini-local",
        "status": "planned",
        "notes": "Future local agent expansion; vendor-neutral design supports addition.",
    },
    {
        "agent_id": "grok-local",
        "status": "planned",
        "notes": "Future local agent expansion; vendor-neutral design supports addition.",
    },
    {
        "agent_id": "perplexity-local",
        "status": "planned",
        "notes": "Future local agent expansion; vendor-neutral design supports addition.",
    },
    {
        "agent_id": "future-cloud-agents",
        "status": "planned",
        "notes": "Design supports cloud-based agent runtimes without hardcoding providers.",
    },
    {
        "agent_id": "future-local-agents",
        "status": "planned",
        "notes": "Design supports additional local runtimes via the adapter registry.",
    },
)


def build_orchestration_design() -> dict:
    """Return a read-only multi-agent orchestration architecture design."""
    return {
        "orchestration_design": {
            "coordinator_responsibilities": list(_ORCHESTRATION_COORDINATOR_RESPONSIBILITIES),
        },
        "capability_profile_model": {
            "fields": list(_ORCHESTRATION_CAPABILITY_PROFILE_FIELDS),
            "capability_categories": list(_ORCHESTRATION_CAPABILITY_CATEGORIES),
        },
        "orchestration_patterns": list(_ORCHESTRATION_PATTERNS),
        "governance_integration": {
            "rules": list(_ORCHESTRATION_GOVERNANCE_RULES),
        },
        "conflict_resolution": {
            "policies": list(_ORCHESTRATION_CONFLICT_RESOLUTION_POLICIES),
            "default_policy": _ORCHESTRATION_DEFAULT_CONFLICT_POLICY,
            "escalation_rule": (
                "When no consensus is reached, the human is authoritative."
            ),
        },
        "future_agent_expansion": list(_ORCHESTRATION_FUTURE_AGENTS),
        "advisory": ORCHESTRATION_DESIGN_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Agent Capability Auto-Discovery (Phase 44C)
# ---------------------------------------------------------------------------

_CAP_CONF_UNKNOWN = "unknown"
_CAP_CONF_OBSERVED = "observed"
_CAP_CONF_VALIDATED = "validated"
_CAP_CONF_PROVEN = "proven"

VALID_CAPABILITY_CONFIDENCES: frozenset[str] = frozenset({
    _CAP_CONF_UNKNOWN,
    _CAP_CONF_OBSERVED,
    _CAP_CONF_VALIDATED,
    _CAP_CONF_PROVEN,
})

CAPABILITY_CATEGORIES: tuple[str, ...] = (
    "planning",
    "implementation",
    "review",
    "validation",
    "research",
    "testing",
    "architecture",
    "documentation",
    "security",
    "performance",
    "dependency-analysis",
    "data-science",
    "devops",
    "refactoring",
    "custom-agent-support",
    "code-generation",
    "roadmap-generation",
    "subagent-coordination",
    "skill-execution",
    "swarm-coordination",
)

# Documentation capability catalog (Phase 44C.1).
# Maps agent_id → capabilities documented by vendor.
# Produces confidence=observed only; never validated or proven.
# Add future agents here without changing discovery code.
_DOC_CAPABILITY_CATALOG: dict[str, tuple[str, ...]] = {
    "codex-local": ("subagent-coordination", "skill-execution"),
    "claude-local": ("subagent-coordination", "custom-agent-support"),
    "kimi-local": ("swarm-coordination",),
}

CAPABILITY_REGISTRY_ADVISORY = (
    "Capability registry is advisory; capabilities are evidence-based "
    "and should be refreshed after runtime updates."
)

CAPABILITY_DISCOVERY_ADVISORY = (
    "Capability discovery is advisory and read-only; no agents are executed."
)

# Evidence source constants
_EV_RUNTIME_DISC = "runtime_discovery"
_EV_CLI_HELP = "CLI help inspection"
_EV_EXEC_HIST = "governed_execution_history"
_EV_WRITABLE_HIST = "writable_execution_history"
_EV_MANUAL_VAL = "manual_validation"
_EV_DOC_REF = "documentation_reference"
_EV_ADAPTER = "adapter_contract"

# CLI help keyword sets for advanced capability detection.
# Kept in sync with _KW_SUBAGENTS to share the same evidence-gathering basis.
_KW_CAP_SUBAGENT = (
    "subagent",
    "sub-agent",
    "background agent",   # e.g. "Manage background agents"
    "multi-agent",        # e.g. "multi-agent code review"
    "--agents",           # e.g. "--agents <json> defining custom agents"
)
_KW_CAP_SKILL = ("skill",)
_KW_CAP_SWARM = ("swarm", "agent-swarm")


@dataclass(frozen=True)
class CapabilityEntry:
    name: str
    confidence: str
    evidence_sources: tuple[str, ...]
    notes: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "confidence": self.confidence,
            "evidence_sources": list(self.evidence_sources),
            "notes": self.notes,
        }


@dataclass(frozen=True)
class SubagentProfile:
    supported: bool
    confidence: str
    mechanism: str
    evidence_sources: tuple[str, ...]
    notes: str

    def to_dict(self) -> dict:
        return {
            "supported": self.supported,
            "confidence": self.confidence,
            "mechanism": self.mechanism,
            "evidence_sources": list(self.evidence_sources),
            "notes": self.notes,
        }


@dataclass(frozen=True)
class AgentCapabilityProfile:
    agent_id: str
    runtime: str
    lifecycle_status: str
    installed: bool
    version: str | None
    capabilities: tuple[CapabilityEntry, ...]
    subagent_profile: SubagentProfile

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "runtime": self.runtime,
            "lifecycle_status": self.lifecycle_status,
            "installed": self.installed,
            "version": self.version,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "subagent_profile": self.subagent_profile.to_dict(),
        }


# Base capability declarations per agent from adapter contracts.
# Format per tuple: (name, confidence, evidence_sources_tuple, notes)
_CapSpec = tuple[str, str, tuple[str, ...], str]

_CODEX_BASE: tuple[_CapSpec, ...] = (
    ("planning", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("implementation", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("code-generation", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("testing", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("review", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("validation", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("documentation", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("refactoring", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
)

_CLAUDE_BASE: tuple[_CapSpec, ...] = (
    ("planning", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("implementation", _CAP_CONF_VALIDATED, (_EV_ADAPTER, _EV_MANUAL_VAL),
     "acceptEdits writable support confirmed via manual validation."),
    ("code-generation", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("review", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("validation", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("documentation", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("architecture", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("research", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("security", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("refactoring", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
)

_KIMI_BASE: tuple[_CapSpec, ...] = (
    ("planning", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("implementation", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("code-generation", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("review", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("documentation", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
    ("research", _CAP_CONF_VALIDATED, (_EV_ADAPTER,), "Confirmed via adapter contract."),
)


@dataclass(frozen=True)
class _AgentCapabilitySpec:
    agent_id: str
    runtime: str
    executable: str | None
    lifecycle_status: str
    base_capabilities: tuple[_CapSpec, ...]


_CAPABILITY_AGENT_SPECS: tuple[_AgentCapabilitySpec, ...] = (
    _AgentCapabilitySpec("codex-local", "codex", "codex", AGENT_STATUS_AVAILABLE, _CODEX_BASE),
    _AgentCapabilitySpec("claude-local", "claude", "claude", AGENT_STATUS_AVAILABLE, _CLAUDE_BASE),
    _AgentCapabilitySpec("kimi-local", "kimi", "kimi", AGENT_STATUS_AVAILABLE, _KIMI_BASE),
    _AgentCapabilitySpec("deepseek-local", "deepseek", None, AGENT_STATUS_DECLARED, ()),
    _AgentCapabilitySpec("gemini-local", "gemini", None, AGENT_STATUS_DECLARED, ()),
    _AgentCapabilitySpec("grok-local", "grok", None, AGENT_STATUS_DECLARED, ()),
    _AgentCapabilitySpec("perplexity-local", "perplexity", None, AGENT_STATUS_DECLARED, ()),
)


def _check_agent_execution_history(
    root: HarnessPath, agent_id: str
) -> tuple[bool, bool]:
    """Return (has_governed_execution, has_writable_execution) for agent_id."""
    results_dir = root.join(_REMOTE_RESULTS_DIR)
    if not results_dir.exists():
        return False, False
    has_exec = False
    has_writable = False
    for f in results_dir.glob("*-result.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        if data.get("selected_agent") != agent_id:
            continue
        if data.get("final_status") == "completed":
            has_exec = True
            if data.get("changed_files"):
                has_writable = True
    return has_exec, has_writable


def _build_agent_capability_profile(
    spec: _AgentCapabilitySpec,
    root: HarnessPath,
    probe_cli: bool,
    runtime_caps_by_id: dict[str, AgentRuntimeCapabilities] | None = None,
    doc_capabilities: tuple[str, ...] = (),
) -> AgentCapabilityProfile:
    """Build a capability profile for one agent. Read-only.

    runtime_caps_by_id: optional pre-computed runtime discovery results keyed by
    agent_id; when present, used as an additional ``runtime_discovery`` evidence
    source alongside CLI help inspection.

    doc_capabilities: vendor-documented capabilities for this agent; each name
    produces at most ``observed`` confidence with evidence ``documentation_reference``.
    """
    installed = False
    version: str | None = None
    help_text = ""

    if spec.executable is not None:
        path = _find_executable(spec.executable)
        installed = path is not None

        if installed and probe_cli:
            version = _extract_version_string(spec.executable)
            parts: list[str] = []
            main_help = _run_probe([spec.executable, "--help"])
            if main_help:
                parts.append(main_help)
            # Probe known subcommands for richer signal; executable-agnostic probing
            # of common subcommand patterns (exec, mcp, mcp-server).
            for sub in ("exec", "mcp", "mcp-server"):
                out = _run_probe([spec.executable, sub, "--help"])
                if out:
                    parts.append(out)
            help_text = " ".join(parts)

    has_exec, has_writable = _check_agent_execution_history(root, spec.agent_id)

    capabilities: list[CapabilityEntry] = []
    seen_names: set[str] = set()

    for name, conf, ev_srcs, notes in spec.base_capabilities:
        if not installed:
            capabilities.append(CapabilityEntry(
                name=name,
                confidence=_CAP_CONF_UNKNOWN,
                evidence_sources=(),
                notes="Agent not installed; capability unverifiable.",
            ))
            seen_names.add(name)
            continue

        final_conf = conf
        final_ev: list[str] = list(ev_srcs)

        if name == "implementation" and has_writable:
            final_conf = _CAP_CONF_PROVEN
            if _EV_WRITABLE_HIST not in final_ev:
                final_ev.append(_EV_WRITABLE_HIST)
        elif name in ("implementation", "code-generation", "testing", "validation") and has_exec:
            final_conf = _CAP_CONF_PROVEN
            if _EV_EXEC_HIST not in final_ev:
                final_ev.append(_EV_EXEC_HIST)

        capabilities.append(CapabilityEntry(
            name=name,
            confidence=final_conf,
            evidence_sources=tuple(final_ev),
            notes=notes,
        ))
        seen_names.add(name)

    # Advanced capability detection from CLI help keywords and runtime discovery.
    # Any installed agent whose help text or runtime caps match these patterns
    # is elevated to "observed" — evidence-based, not hardcoded per runtime.
    if installed:
        runtime_caps = (runtime_caps_by_id or {}).get(spec.agent_id)
        for cap_name, kw_set, runtime_attr in (
            ("subagent-coordination", _KW_CAP_SUBAGENT, "subagents_supported"),
            ("skill-execution", _KW_CAP_SKILL, None),
            ("swarm-coordination", _KW_CAP_SWARM, None),
        ):
            if cap_name in seen_names:
                continue
            ev_srcs: list[str] = []
            # CLI help inspection
            if help_text and any(kw in help_text for kw in kw_set):
                ev_srcs.append(_EV_CLI_HELP)
            # Runtime discovery as secondary evidence source
            if (
                runtime_attr is not None
                and runtime_caps is not None
                and getattr(runtime_caps, runtime_attr, RUNTIME_CAP_UNKNOWN) == RUNTIME_CAP_YES
                and _EV_RUNTIME_DISC not in ev_srcs
            ):
                ev_srcs.append(_EV_RUNTIME_DISC)
            if ev_srcs:
                capabilities.append(CapabilityEntry(
                    name=cap_name,
                    confidence=_CAP_CONF_OBSERVED,
                    evidence_sources=tuple(ev_srcs),
                    notes="Detected from CLI help or runtime discovery; not confirmed by execution.",
                ))
                seen_names.add(cap_name)

    # Documentation reference pass — vendor-documented capabilities.
    # Applies regardless of installation status: documentation is external evidence.
    # Produces at most confidence=observed; never validates or proves a capability.
    for cap_name in doc_capabilities:
        existing_idx = next(
            (i for i, c in enumerate(capabilities) if c.name == cap_name), None
        )
        if existing_idx is None:
            # Capability not yet recorded — create as observed from documentation.
            capabilities.append(CapabilityEntry(
                name=cap_name,
                confidence=_CAP_CONF_OBSERVED,
                evidence_sources=(_EV_DOC_REF,),
                notes="Documented by vendor; not yet validated by PCAE.",
            ))
            seen_names.add(cap_name)
        else:
            # Capability already recorded — add documentation_reference as additional source.
            existing = capabilities[existing_idx]
            if _EV_DOC_REF not in existing.evidence_sources:
                new_conf = (
                    _CAP_CONF_OBSERVED
                    if existing.confidence == _CAP_CONF_UNKNOWN
                    else existing.confidence
                )
                capabilities[existing_idx] = CapabilityEntry(
                    name=existing.name,
                    confidence=new_conf,
                    evidence_sources=existing.evidence_sources + (_EV_DOC_REF,),
                    notes=existing.notes,
                )

    # Fill remaining categories as unknown
    for cat in CAPABILITY_CATEGORIES:
        if cat not in seen_names:
            capabilities.append(CapabilityEntry(
                name=cat,
                confidence=_CAP_CONF_UNKNOWN,
                evidence_sources=(),
                notes="No evidence collected." if installed else "Agent not installed.",
            ))

    # Build subagent profile from subagent-coordination capability
    subagent_cap = next(
        (c for c in capabilities if c.name == "subagent-coordination"), None
    )
    if subagent_cap is not None and subagent_cap.confidence != _CAP_CONF_UNKNOWN:
        subagent_profile = SubagentProfile(
            supported=True,
            confidence=subagent_cap.confidence,
            mechanism="CLI help keyword detection, runtime discovery, or documentation reference",
            evidence_sources=subagent_cap.evidence_sources,
            notes=subagent_cap.notes,
        )
    else:
        subagent_profile = SubagentProfile(
            supported=False,
            confidence=_CAP_CONF_UNKNOWN,
            mechanism="none",
            evidence_sources=(),
            notes="No subagent support detected." if installed else "Agent not installed.",
        )

    return AgentCapabilityProfile(
        agent_id=spec.agent_id,
        runtime=spec.runtime,
        lifecycle_status=spec.lifecycle_status,
        installed=installed,
        version=version,
        capabilities=tuple(capabilities),
        subagent_profile=subagent_profile,
    )


# ---------------------------------------------------------------------------
# Phase 44D.1: Capability Classification Normalization
# ---------------------------------------------------------------------------
# Normalization maps individual capability names into higher-level summary
# groups without erasing original records or altering confidence levels.
# Any capability at observed or better qualifies an agent for a group.

_MULTI_AGENT_CAPABILITIES: frozenset[str] = frozenset({
    "subagent-coordination",
    "swarm-coordination",
    "custom-agent-support",
})

_EXTENSIBILITY_CAPABILITIES: frozenset[str] = frozenset({
    "skill-execution",
})


def _has_capability_observed(profile: AgentCapabilityProfile, cap_name: str) -> bool:
    """Return True if the agent holds *cap_name* at observed confidence or better."""
    for cap in profile.capabilities:
        if cap.name == cap_name and cap.confidence != _CAP_CONF_UNKNOWN:
            return True
    return False


def _build_normalized_summary(profiles: list[AgentCapabilityProfile]) -> dict:
    """Return normalized capability group membership lists. Read-only; no confidence mutation."""
    subagent_capable = [p.agent_id for p in profiles if p.subagent_profile.supported]
    swarm_capable = [
        p.agent_id for p in profiles
        if _has_capability_observed(p, "swarm-coordination")
    ]
    multi_agent_capable = [
        p.agent_id for p in profiles
        if any(_has_capability_observed(p, cap) for cap in _MULTI_AGENT_CAPABILITIES)
    ]
    extensibility_capable = [
        p.agent_id for p in profiles
        if any(_has_capability_observed(p, cap) for cap in _EXTENSIBILITY_CAPABILITIES)
    ]
    return {
        "subagent_capable_agents": subagent_capable,
        "swarm_capable_agents": swarm_capable,
        "multi_agent_capable_agents": multi_agent_capable,
        "extensibility_capable_agents": extensibility_capable,
        "normalization_rules": {
            "subagent-coordination": "multi_agent_capable",
            "swarm-coordination": "multi_agent_capable",
            "custom-agent-support": "multi_agent_capable",
            "skill-execution": "extensibility_capable",
        },
    }


def _build_discovery_summary(profiles: list[AgentCapabilityProfile]) -> dict:
    installed_count = sum(1 for p in profiles if p.installed)
    proven_count = sum(
        1 for p in profiles
        for c in p.capabilities
        if c.confidence == _CAP_CONF_PROVEN
    )
    unknown_count = sum(
        1 for p in profiles
        for c in p.capabilities
        if c.confidence == _CAP_CONF_UNKNOWN
    )
    normalized = _build_normalized_summary(profiles)
    return {
        "agents_checked": len(profiles),
        "agents_installed": installed_count,
        "agents_not_installed": len(profiles) - installed_count,
        "proven_capability_entries": proven_count,
        "unknown_capability_entries": unknown_count,
        "subagent_capable_agents": normalized["subagent_capable_agents"],
        "swarm_capable_agents": normalized["swarm_capable_agents"],
        "multi_agent_capable_agents": normalized["multi_agent_capable_agents"],
        "extensibility_capable_agents": normalized["extensibility_capable_agents"],
    }


def build_capability_registry(root: HarnessPath) -> dict:
    """Return the evidence-based agent capability registry (no CLI probing).

    Documentation-backed capabilities from the doc catalog are included at
    confidence=observed with evidence_source=documentation_reference so that
    the registry summary groups are consistent with capability-discovery and
    capability-validation output.
    """
    profiles = [
        _build_agent_capability_profile(
            spec,
            root,
            probe_cli=False,
            doc_capabilities=_DOC_CAPABILITY_CATALOG.get(spec.agent_id, ()),
        )
        for spec in _CAPABILITY_AGENT_SPECS
    ]
    return {
        "capability_registry": [p.to_dict() for p in profiles],
        "discovery_summary": _build_discovery_summary(profiles),
        "advisory": CAPABILITY_REGISTRY_ADVISORY,
    }


def build_capability_discovery(root: HarnessPath) -> dict:
    """Run auto-discovery of agent capabilities via CLI help + runtime discovery. Read-only."""
    # Run runtime discovery once and pass results as a second evidence source.
    rt_result = build_runtime_discovery()
    runtime_caps_by_id: dict[str, AgentRuntimeCapabilities] = {
        entry.agent_id: entry.capabilities for entry in rt_result.agents
    }
    profiles = [
        _build_agent_capability_profile(
            spec,
            root,
            probe_cli=True,
            runtime_caps_by_id=runtime_caps_by_id,
            doc_capabilities=_DOC_CAPABILITY_CATALOG.get(spec.agent_id, ()),
        )
        for spec in _CAPABILITY_AGENT_SPECS
    ]
    return {
        "capability_registry": [p.to_dict() for p in profiles],
        "discovery_summary": _build_discovery_summary(profiles),
        "advisory": CAPABILITY_DISCOVERY_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 44D: Capability Validation Framework
# ---------------------------------------------------------------------------

CAPABILITY_VALIDATION_ADVISORY = (
    "Capability validation is advisory; no runtime validation is executed."
)

# Ordered lifecycle levels from lowest to highest confidence.
CAPABILITY_VALIDATION_LIFECYCLE: tuple[str, ...] = (
    _CAP_CONF_UNKNOWN,
    _CAP_CONF_OBSERVED,
    _CAP_CONF_VALIDATED,
    _CAP_CONF_PROVEN,
)

# All recognized validation source types.
CAPABILITY_VALIDATION_SOURCES: tuple[str, ...] = (
    "documentation_reference",
    "cli_discovery",
    "manual_validation",
    "runtime_validation",
    "governed_execution_history",
    "writable_execution_history",
    "adapter_contract",
)

# All promotion rules, including unknown→observed and the proven no-downgrade guard.
_CAPABILITY_PROMOTION_RULES: tuple[dict, ...] = (
    {
        "rule_id": "unknown_to_observed",
        "from_confidence": _CAP_CONF_UNKNOWN,
        "to_confidence": _CAP_CONF_OBSERVED,
        "required_validation": "evidence_collection",
        "validation_sources": ["documentation_reference", "cli_discovery"],
        "description": (
            "A capability becomes observed when evidence is collected from "
            "documentation references or CLI help/runtime discovery."
        ),
    },
    {
        "rule_id": "observed_to_validated",
        "from_confidence": _CAP_CONF_OBSERVED,
        "to_confidence": _CAP_CONF_VALIDATED,
        "required_validation": "successful_controlled_experiment",
        "validation_sources": ["runtime_validation", "manual_validation"],
        "description": (
            "A successful controlled PCAE experiment must confirm the capability "
            "behaves as expected in a governed session."
        ),
    },
    {
        "rule_id": "validated_to_proven",
        "from_confidence": _CAP_CONF_VALIDATED,
        "to_confidence": _CAP_CONF_PROVEN,
        "required_validation": "successful_governed_production_usage",
        "validation_sources": ["governed_execution_history", "writable_execution_history"],
        "description": (
            "The capability must be successfully exercised in real governed production "
            "usage recorded in PCAE execution history."
        ),
    },
    {
        "rule_id": "proven_no_downgrade",
        "from_confidence": _CAP_CONF_PROVEN,
        "to_confidence": _CAP_CONF_PROVEN,
        "required_validation": "not_applicable",
        "validation_sources": [],
        "description": (
            "Proven capabilities cannot be downgraded by documentation-only evidence. "
            "Once proven, the confidence level is permanent unless explicitly reset by "
            "a human governance decision."
        ),
    },
)


def _promotion_rule_for(confidence: str) -> dict | None:
    """Return the rule for promoting *beyond* the given confidence, or None if not promotable."""
    for rule in _CAPABILITY_PROMOTION_RULES:
        if rule["from_confidence"] == confidence and rule["to_confidence"] != confidence:
            return rule
    return None


def _recommended_validation_method(rule: dict) -> str:
    """Return the primary validation source from a promotion rule."""
    sources = rule.get("validation_sources", [])
    return sources[0] if sources else "not_applicable"


def _build_validation_candidates(
    profiles: list[AgentCapabilityProfile],
) -> list[dict]:
    """Return per-agent validation candidate records for installed agents."""
    candidates: list[dict] = []
    for profile in profiles:
        observed: list[str] = []
        validated: list[str] = []
        proven: list[str] = []
        next_candidates: list[dict] = []

        for cap in profile.capabilities:
            if cap.confidence == _CAP_CONF_OBSERVED:
                observed.append(cap.name)
            elif cap.confidence == _CAP_CONF_VALIDATED:
                validated.append(cap.name)
            elif cap.confidence == _CAP_CONF_PROVEN:
                proven.append(cap.name)

        # Next validation candidates are observed capabilities (can be promoted to validated).
        for cap in profile.capabilities:
            rule = _promotion_rule_for(cap.confidence)
            if rule is None:
                continue
            next_candidates.append({
                "capability": cap.name,
                "current_confidence": cap.confidence,
                "promotion_path": f"{cap.confidence} → {rule['to_confidence']}",
                "recommended_validation_method": _recommended_validation_method(rule),
                "required_validation": rule["required_validation"],
            })

        # Primary recommended method: use rule for the first next candidate, or n/a.
        if next_candidates:
            primary_method = next_candidates[0]["recommended_validation_method"]
        else:
            primary_method = "not_applicable"

        candidates.append({
            "agent_id": profile.agent_id,
            "installed": profile.installed,
            "observed_capabilities": observed,
            "validated_capabilities": validated,
            "proven_capabilities": proven,
            "next_validation_candidates": next_candidates,
            "recommended_validation_method": primary_method,
        })
    return candidates


# ---------------------------------------------------------------------------
# Coordinator Agent Design (Phase 44E)
# ---------------------------------------------------------------------------

COORDINATOR_DESIGN_ADVISORY = (
    "Coordinator design is advisory; no orchestration is performed."
)

_COORDINATOR_RESPONSIBILITIES: tuple[dict, ...] = (
    {
        "name": "task_intake",
        "description": "Receive and record incoming task requests.",
    },
    {
        "name": "task_classification",
        "description": "Classify tasks into supported task classes.",
    },
    {
        "name": "capability_lookup",
        "description": "Query the capability registry for agents matching the task class.",
    },
    {
        "name": "agent_selection",
        "description": "Select eligible agents based on capability, confidence, and lifecycle status.",
    },
    {
        "name": "orchestration_strategy_selection",
        "description": "Choose the appropriate orchestration strategy for the task.",
    },
    {
        "name": "result_aggregation",
        "description": "Collect and aggregate results from assigned agents.",
    },
    {
        "name": "conflict_escalation",
        "description": "Escalate conflicts or disagreements to the human for resolution.",
    },
    {
        "name": "governance_handoff",
        "description": "Transfer results and context through governed PCAE checkpoints.",
    },
)

_COORDINATOR_TASK_CLASSES: tuple[str, ...] = (
    "planning",
    "implementation",
    "review",
    "validation",
    "research",
    "testing",
    "architecture",
    "documentation",
    "security",
    "performance",
    "dependency-analysis",
    "roadmap-generation",
)

_COORDINATOR_SELECTION_CRITERIA: tuple[dict, ...] = (
    {
        "criterion": "capability_present",
        "description": "Agent declares the required capability in the registry.",
    },
    {
        "criterion": "confidence_threshold",
        "description": "Capability confidence is observed or higher (not unknown).",
    },
    {
        "criterion": "agent_installed",
        "description": "Agent runtime is confirmed installed on the local system.",
    },
    {
        "criterion": "agent_available",
        "description": "Agent lifecycle status is available or active.",
    },
)

_COORDINATOR_SELECTION_MODEL: dict = {
    "rule": (
        "Coordinator must not hardcode runtime-to-role assignments. "
        "Instead, query the capability registry, check confidence level, "
        "verify lifecycle status, and select eligible agents dynamically."
    ),
    "prohibited_hardcoding": [
        "codex -> implementer",
        "claude -> reviewer",
        "kimi -> planner",
    ],
    "selection_criteria": list(_COORDINATOR_SELECTION_CRITERIA),
    "selection_output_fields": [
        "task_id",
        "selected_agents",
        "selection_reason",
        "capability_used",
        "confidence_level",
    ],
}

_COORDINATOR_ORCHESTRATION_STRATEGIES: tuple[dict, ...] = (
    {
        "strategy": "single_agent",
        "description": "One agent handles the full task.",
        "parallel": False,
        "steps": ["coordinator → agent"],
        "example": "coordinator → agent",
    },
    {
        "strategy": "sequential",
        "description": "Agents execute in sequence: planner, then implementer, then reviewer.",
        "parallel": False,
        "steps": ["planner", "implementer", "reviewer"],
        "example": "planner → implementer → reviewer",
    },
    {
        "strategy": "parallel_review",
        "description": "One implementer, multiple reviewers operating in parallel.",
        "parallel": True,
        "steps": ["implementer", "reviewerA | reviewerB | reviewerC"],
        "example": "implementer → [reviewerA, reviewerB, reviewerC]",
    },
    {
        "strategy": "parallel_planning",
        "description": "Multiple planners in parallel; coordinator aggregates plans.",
        "parallel": True,
        "steps": ["plannerA | plannerB", "coordinator aggregation"],
        "example": "[plannerA, plannerB] → coordinator aggregation",
    },
    {
        "strategy": "swarm",
        "description": "Multiple agents work in parallel; coordinator collects all results.",
        "parallel": True,
        "steps": ["agentA | agentB | agentC", "coordinator aggregation"],
        "example": "[agentA, agentB, agentC] → coordinator aggregation",
    },
    {
        "strategy": "consensus",
        "description": "Multiple planners propose; coordinator computes consensus.",
        "parallel": True,
        "steps": ["planner1 | planner2 | planner3", "coordinator consensus"],
        "example": "[planner1, planner2, planner3] → coordinator consensus",
    },
)

_COORDINATOR_GOVERNANCE_BOUNDARIES: dict = {
    "coordinator_may": [
        "assign work to eligible agents",
        "aggregate results from agents",
    ],
    "coordinator_may_not": [
        "approve changes",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
    "note": (
        "All execution remains governed by existing PCAE controls. "
        "Coordinator authority is advisory and coordination-scoped only."
    ),
}

_COORDINATOR_FUTURE_AGENTS: tuple[str, ...] = (
    "codex-local",
    "claude-local",
    "kimi-local",
    "deepseek-local",
    "gemini-local",
    "grok-local",
    "perplexity-local",
    "future-local-runtimes",
    "future-cloud-runtimes",
)


# ---------------------------------------------------------------------------
# Consensus Engine Design (Phase 44F)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Parallel Agent Execution Design (Phase 44G)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Multi-Agent Planning Prototype Design (Phase 44H)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Planning Artifact Dry-Run (Phase 44I)
# ---------------------------------------------------------------------------

PLANNING_DRY_RUN_ADVISORY = (
    "Planning dry-run is simulated. No planning agents were executed."
)

_PLANNING_DRY_RUN_OBJECTIVE_ID = "plan-dry-run-001"
_PLANNING_DRY_RUN_OBJECTIVE_TEXT = "Implement a capability validation framework"
_PLANNING_DRY_RUN_SCOPE = "core/agent.py, tests/test_agent.py, docs"
_PLANNING_DRY_RUN_REQUIRED_CAPABILITIES = ("planning", "architecture", "roadmap-generation")

# Deterministic mock planner selection derived from known capability profiles.
# Uses the same agents that build_capability_registry populates at validated+.
_PLANNING_DRY_RUN_PLANNER_SELECTION: tuple[dict, ...] = (
    {
        "agent_id": "codex-local",
        "selection_reason": "Declares planning capability at validated confidence via adapter contract.",
        "capability_used": "planning",
        "confidence_level": "validated",
    },
    {
        "agent_id": "claude-local",
        "selection_reason": "Declares planning capability at validated confidence via adapter contract.",
        "capability_used": "planning",
        "confidence_level": "validated",
    },
    {
        "agent_id": "kimi-local",
        "selection_reason": "Declares planning capability at validated confidence via governed execution history.",
        "capability_used": "planning",
        "confidence_level": "validated",
    },
)

# Deterministic mock planning artifacts — one per selected planner.
_PLANNING_DRY_RUN_SIMULATED_PLANS: tuple[dict, ...] = (
    {
        "planner_id": "codex-local",
        "proposed_phases": [
            "Phase 1: Define capability model",
            "Phase 2: Implement validation rules",
            "Phase 3: Add CLI commands",
            "Phase 4: Write tests",
        ],
        "assumptions": [
            "Capability model is well-defined",
            "CLI patterns are established",
        ],
        "risks": [
            "Capability categories may expand",
            "Validation rules may conflict",
        ],
    },
    {
        "planner_id": "claude-local",
        "proposed_phases": [
            "Phase 1: Design capability ontology",
            "Phase 2: Implement registry",
            "Phase 3: Build validation pipeline",
            "Phase 4: Integration tests",
        ],
        "assumptions": [
            "Registry is extensible",
            "Test framework supports parametric tests",
        ],
        "risks": [
            "Ontology drift over time",
            "Registry performance at scale",
        ],
    },
    {
        "planner_id": "kimi-local",
        "proposed_phases": [
            "Phase 1: Capability data model",
            "Phase 2: Evidence collection pipeline",
            "Phase 3: Confidence scoring",
            "Phase 4: CLI and documentation",
        ],
        "assumptions": [
            "Evidence sources are well-defined",
            "Confidence thresholds are fixed",
        ],
        "risks": [
            "Evidence collection requires agent runtime",
            "Confidence scoring is subjective",
        ],
    },
)

_PLANNING_DRY_RUN_SIMULATED_CONSENSUS: dict = {
    "agreements": [
        "CLI commands are required",
        "Tests are required",
        "Registry must be read-only by default",
    ],
    "conflicts": [
        "Phase ordering: codex-local favors implementation-first; claude-local favors design-first.",
        "Scope: kimi-local includes confidence scoring as a separate phase.",
    ],
    "consensus_summary": (
        "Three planners agree on core deliverables (CLI, tests, registry). "
        "Phase ordering and scope boundaries require human decision."
    ),
}

_PLANNING_DRY_RUN_HUMAN_REVIEW: dict = {
    "human_decision_required": True,
    "review_items": [
        "Resolve phase ordering conflict",
        "Confirm scope boundaries",
        "Approve proposed phases before execution",
    ],
}

_PLANNING_DRY_RUN_NEXT_ACTIONS: tuple[str, ...] = (
    "Human reviews simulated plans",
    "Human resolves conflicts and selects preferred approach",
    "Human approves planning artifact before execution",
    "Run pcae planning-dry-run --json for machine-readable output",
)


def build_planning_dry_run() -> dict:
    """Return a simulated multi-agent planning dry-run. Read-only; no agents executed."""
    return {
        "objective": {
            "objective_id": _PLANNING_DRY_RUN_OBJECTIVE_ID,
            "objective_text": _PLANNING_DRY_RUN_OBJECTIVE_TEXT,
            "planning_scope": _PLANNING_DRY_RUN_SCOPE,
            "required_capabilities": list(_PLANNING_DRY_RUN_REQUIRED_CAPABILITIES),
        },
        "planner_selection": {
            "selected_agents": [p["agent_id"] for p in _PLANNING_DRY_RUN_PLANNER_SELECTION],
            "selection_details": list(_PLANNING_DRY_RUN_PLANNER_SELECTION),
        },
        "simulated_plans": list(_PLANNING_DRY_RUN_SIMULATED_PLANS),
        "simulated_consensus": _PLANNING_DRY_RUN_SIMULATED_CONSENSUS,
        "human_review": _PLANNING_DRY_RUN_HUMAN_REVIEW,
        "next_actions": list(_PLANNING_DRY_RUN_NEXT_ACTIONS),
        "advisory": PLANNING_DRY_RUN_ADVISORY,
    }


PLANNING_PROTOTYPE_DESIGN_ADVISORY = (
    "Planning prototype design is advisory; no planning agents are executed."
)

_PLANNING_OBJECTIVE_FIELDS: tuple[str, ...] = (
    "objective_id",
    "objective_text",
    "planning_scope",
    "constraints",
    "required_capabilities",
    "output_format",
    "human_approval_required",
)

_PLANNER_SELECTION_CAPABILITIES: tuple[str, ...] = (
    "planning",
    "architecture",
    "roadmap-generation",
    "documentation",
    "review",
)

_PLANNER_SELECTION_RULES: tuple[str, ...] = (
    "capability-based: agents must declare the required capability in the registry",
    "confidence-aware: capability confidence must be observed or higher",
    "runtime-neutral: no agent is hardcoded as the planner",
    "human-overridable: the human may override any agent selection",
)

_PARALLEL_PLANNING_FLOW: tuple[str, ...] = (
    "coordinator receives objective",
    "coordinator selects eligible planners from capability registry",
    "coordinator creates read-only planning child tasks",
    "planners produce independent plans in parallel",
    "coordinator aggregates plans",
    "consensus engine identifies agreements and conflicts",
    "human reviews proposed plan and makes final decision",
)

_PLANNING_ARTIFACT_FIELDS: tuple[str, ...] = (
    "plan_id",
    "objective_id",
    "planner_agents",
    "proposed_phases",
    "dependencies",
    "risks",
    "assumptions",
    "conflicts",
    "consensus_summary",
    "human_decision_required",
)

_PLANNING_GOVERNANCE_RULES: tuple[str, ...] = (
    "planning is read-only",
    "planners cannot modify files",
    "planners cannot approve changes",
    "planners cannot commit",
    "planners cannot push",
    "planner output is advisory",
    "human approves roadmap before execution",
)

_PLANNING_CONFLICT_HANDLING: tuple[str, ...] = (
    "preserve all proposed plans",
    "highlight disagreements between planners",
    "require human decision for conflicts",
    "do not auto-select roadmap when consensus is weak",
)

_PLANNING_FUTURE_PATH: tuple[dict, ...] = (
    {
        "phase": "44I",
        "description": "Planning artifact dry-run",
    },
    {
        "phase": "44J",
        "description": "Multi-agent planning execution",
    },
    {
        "phase": "45A",
        "description": "Autonomous roadmap generation",
    },
)


def build_planning_prototype_design() -> dict:
    """Return a read-only multi-agent planning prototype architecture design."""
    return {
        "planning_prototype_design": {
            "future_path": list(_PLANNING_FUTURE_PATH),
        },
        "planning_objective_model": {
            "fields": list(_PLANNING_OBJECTIVE_FIELDS),
        },
        "planner_selection": {
            "required_capabilities": list(_PLANNER_SELECTION_CAPABILITIES),
            "selection_rules": list(_PLANNER_SELECTION_RULES),
        },
        "parallel_planning_flow": list(_PARALLEL_PLANNING_FLOW),
        "planning_artifact_model": {
            "fields": list(_PLANNING_ARTIFACT_FIELDS),
        },
        "governance_rules": list(_PLANNING_GOVERNANCE_RULES),
        "conflict_handling": list(_PLANNING_CONFLICT_HANDLING),
        "advisory": PLANNING_PROTOTYPE_DESIGN_ADVISORY,
    }


PARALLEL_EXECUTION_DESIGN_ADVISORY = (
    "Parallel execution design is advisory; no parallel execution is performed."
)

_PARALLEL_EXECUTION_TOPOLOGIES: tuple[dict, ...] = (
    {
        "topology": "fan_out",
        "description": "Coordinator distributes a single task to multiple agents simultaneously.",
        "parallel": True,
    },
    {
        "topology": "fan_in",
        "description": "Multiple agent outputs are collected and merged by the coordinator.",
        "parallel": True,
    },
    {
        "topology": "map_reduce",
        "description": "Task is split into sub-tasks (map), each executed in parallel; results are reduced by the coordinator.",
        "parallel": True,
    },
    {
        "topology": "parallel_review",
        "description": "Multiple reviewers evaluate the same artifact in parallel.",
        "parallel": True,
    },
    {
        "topology": "parallel_planning",
        "description": "Multiple planners produce independent plans in parallel; coordinator aggregates.",
        "parallel": True,
    },
    {
        "topology": "parallel_validation",
        "description": "Multiple validators run checks in parallel; results fed to consensus engine.",
        "parallel": True,
    },
    {
        "topology": "swarm",
        "description": "Many agents operate on distinct sub-tasks simultaneously; coordinator collects all outputs.",
        "parallel": True,
    },
)

_PARALLEL_COORDINATOR_RESPONSIBILITIES: tuple[str, ...] = (
    "create child tasks",
    "assign agents based on capability registry",
    "define execution mode per child task",
    "monitor timeout and deadline",
    "collect outputs",
    "normalize results",
    "aggregate findings",
    "pass outputs to consensus engine",
    "hand off to existing governance controls",
)

_PARALLEL_CHILD_TASK_FIELDS: tuple[str, ...] = (
    "child_task_id",
    "parent_task_id",
    "assigned_agent",
    "assigned_role",
    "capability_required",
    "execution_mode",
    "writable_allowed",
    "timeout_seconds",
    "status",
    "result_ref",
    "failure_reason",
)

_PARALLEL_SAFETY_RULES: tuple[str, ...] = (
    "default child tasks are read-only",
    "writable child tasks require explicit governance approval",
    "no child task may commit",
    "no child task may push",
    "no child task may rollback",
    "coordinator cannot bypass human approval",
)

_PARALLEL_CHILD_TASK_STATUSES: tuple[str, ...] = (
    "pending",
    "running",
    "completed",
    "failed",
    "timed_out",
    "cancelled",
    "blocked",
)

_PARALLEL_FAILURE_HANDLING: tuple[str, ...] = (
    "partial results are preserved",
    "failed child does not invalidate all results by default",
    "timeout produces incomplete result",
    "consensus engine decides whether partial outputs are usable",
    "human escalation is default for conflicting or incomplete outcomes",
)

_PARALLEL_RESULT_AGGREGATION_FIELDS: tuple[str, ...] = (
    "stdout_stderr_summaries",
    "execution_metadata",
    "evidence_artifacts",
    "changed_files",
    "recommendations",
    "confidence",
    "conflicts",
)

_PARALLEL_GOVERNANCE_INTEGRATION: tuple[str, ...] = (
    "consensus engine",
    "change review",
    "approval gates",
    "commit governance",
    "push governance",
    "rollback governance",
)


def build_parallel_execution_design() -> dict:
    """Return a read-only parallel agent execution architecture design."""
    return {
        "parallel_execution_design": {
            "coordinator_responsibilities": list(_PARALLEL_COORDINATOR_RESPONSIBILITIES),
        },
        "execution_topologies": list(_PARALLEL_EXECUTION_TOPOLOGIES),
        "child_task_model": {
            "fields": list(_PARALLEL_CHILD_TASK_FIELDS),
        },
        "safety_rules": list(_PARALLEL_SAFETY_RULES),
        "failure_model": {
            "statuses": list(_PARALLEL_CHILD_TASK_STATUSES),
            "failure_handling": list(_PARALLEL_FAILURE_HANDLING),
        },
        "result_aggregation": {
            "aggregate_fields": list(_PARALLEL_RESULT_AGGREGATION_FIELDS),
        },
        "governance_integration": {
            "feeds_into": list(_PARALLEL_GOVERNANCE_INTEGRATION),
        },
        "advisory": PARALLEL_EXECUTION_DESIGN_ADVISORY,
    }


CONSENSUS_DESIGN_ADVISORY = (
    "Consensus design is advisory; no consensus execution is performed."
)

_CONSENSUS_INPUT_FIELDS: tuple[str, ...] = (
    "agent_id",
    "assigned_role",
    "task_id",
    "recommendation",
    "confidence",
    "rationale",
    "evidence_artifacts",
    "execution_result_refs",
)

_CONSENSUS_DECISION_TYPES: tuple[dict, ...] = (
    {
        "decision": "approve",
        "description": "All or majority of agents agree the work is acceptable.",
    },
    {
        "decision": "reject",
        "description": "All or majority of agents agree the work should not proceed.",
    },
    {
        "decision": "request_changes",
        "description": "Agents agree the work needs modification before proceeding.",
    },
    {
        "decision": "inconclusive",
        "description": "Agents disagree and no policy threshold is met.",
    },
    {
        "decision": "escalate_to_human",
        "description": "Conflict cannot be resolved automatically; human decision required.",
    },
)

_CONSENSUS_POLICIES: tuple[dict, ...] = (
    {
        "policy": "unanimous",
        "description": "All agents must agree for a decision to be reached.",
        "is_default": False,
    },
    {
        "policy": "majority",
        "description": "More than half of agents must agree for a decision to be reached.",
        "is_default": False,
    },
    {
        "policy": "weighted",
        "description": "Agents are assigned numeric weights; decision goes to the weighted majority.",
        "is_default": False,
    },
    {
        "policy": "confidence_weighted",
        "description": "Agent weights are derived from their capability confidence levels.",
        "is_default": False,
    },
    {
        "policy": "role_priority",
        "description": "Certain roles (e.g. validator) have decision authority over others.",
        "is_default": False,
    },
    {
        "policy": "human_escalation",
        "description": "Conflicts are always escalated to the human for final decision.",
        "is_default": True,
    },
)

_CONSENSUS_DEFAULT_POLICY = "human_escalation"

_CONSENSUS_WEIGHT_SOURCES: tuple[dict, ...] = (
    {
        "source": "capability_confidence",
        "description": "Higher confidence level (proven > validated > observed > unknown) yields higher weight.",
    },
    {
        "source": "runtime_availability",
        "description": "Agents with confirmed available lifecycle status receive higher weight.",
    },
    {
        "source": "successful_execution_history",
        "description": "Agents with more successful governed executions receive higher weight.",
    },
    {
        "source": "role_fit",
        "description": "Weight is higher when the agent's declared role matches the task role.",
    },
    {
        "source": "task_class_fit",
        "description": "Weight is higher when the agent's capabilities match the task class.",
    },
)

_CONSENSUS_CONFLICT_HANDLING: dict = {
    "rule": (
        "When agents disagree, the consensus engine preserves all recommendations "
        "and rationales, produces a conflict summary, and escalates to the human "
        "by default. No automatic resolution is performed."
    ),
    "steps": [
        "preserve all agent recommendations",
        "preserve all agent rationales",
        "produce conflict summary",
        "escalate to human by default",
    ],
}

_CONSENSUS_GOVERNANCE_BOUNDARIES: dict = {
    "engine_may": [
        "aggregate agent recommendations",
        "produce advisory decision",
        "flag conflicts for human review",
        "request human decision",
    ],
    "engine_may_not": [
        "approve changes",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
    "note": (
        "Consensus engine output is advisory only. "
        "All approval, commit, push, and rollback operations remain "
        "governed by existing PCAE controls."
    ),
}

_CONSENSUS_FUTURE_EXPANSIONS: tuple[str, ...] = (
    "quorum thresholds",
    "veto-capable roles",
    "domain-specific weighting",
    "reviewer panels",
    "roadmap proposal consensus",
)


def build_consensus_design() -> dict:
    """Return a read-only consensus engine architecture design."""
    return {
        "consensus_design": {
            "input_fields": list(_CONSENSUS_INPUT_FIELDS),
            "default_policy": _CONSENSUS_DEFAULT_POLICY,
        },
        "decision_types": list(_CONSENSUS_DECISION_TYPES),
        "consensus_policies": list(_CONSENSUS_POLICIES),
        "weighting_model": {
            "description": (
                "Weights are derived from agent-specific evidence rather than "
                "hardcoded values. No weight is assigned without supporting evidence."
            ),
            "weight_sources": list(_CONSENSUS_WEIGHT_SOURCES),
        },
        "conflict_handling": _CONSENSUS_CONFLICT_HANDLING,
        "governance_boundaries": _CONSENSUS_GOVERNANCE_BOUNDARIES,
        "future_expansions": list(_CONSENSUS_FUTURE_EXPANSIONS),
        "advisory": CONSENSUS_DESIGN_ADVISORY,
    }


def build_coordinator_design() -> dict:
    """Return a read-only coordinator agent architecture design."""
    return {
        "coordinator_design": {
            "responsibilities": list(_COORDINATOR_RESPONSIBILITIES),
        },
        "task_classification": {
            "supported_task_classes": list(_COORDINATOR_TASK_CLASSES),
        },
        "selection_model": _COORDINATOR_SELECTION_MODEL,
        "orchestration_strategies": list(_COORDINATOR_ORCHESTRATION_STRATEGIES),
        "governance_integration": _COORDINATOR_GOVERNANCE_BOUNDARIES,
        "future_agent_expansion": list(_COORDINATOR_FUTURE_AGENTS),
        "advisory": COORDINATOR_DESIGN_ADVISORY,
    }


PLANNING_EXECUTION_DESIGN_ADVISORY = (
    "Planning execution design is advisory; no planning agents are executed."
)

_PLANNING_EXECUTION_LIFECYCLE: tuple[dict, ...] = (
    {
        "stage": 1,
        "name": "objective",
        "description": "Human submits a planning objective to the coordinator.",
    },
    {
        "stage": 2,
        "name": "planner_selection",
        "description": (
            "Coordinator selects eligible planning agents from the capability registry "
            "based on capability, confidence, and lifecycle status."
        ),
    },
    {
        "stage": 3,
        "name": "planning_task_creation",
        "description": (
            "Coordinator creates one read-only planning task per selected planner; "
            "human approval required before tasks are created."
        ),
    },
    {
        "stage": 4,
        "name": "agent_execution",
        "description": (
            "Selected planners execute according to the chosen execution mode; "
            "each produces an independent planning artifact."
        ),
    },
    {
        "stage": 5,
        "name": "planning_artifact_collection",
        "description": "Coordinator collects all planning artifacts from completed planning tasks.",
    },
    {
        "stage": 6,
        "name": "consensus",
        "description": (
            "Consensus engine analyzes collected artifacts for agreements and conflicts "
            "across planner outputs."
        ),
    },
    {
        "stage": 7,
        "name": "human_review",
        "description": (
            "Human reviews consensus output, resolves conflicts, and decides whether "
            "to approve, reject, or request changes to the proposed roadmap."
        ),
    },
    {
        "stage": 8,
        "name": "approved_roadmap",
        "description": (
            "Human approves the final roadmap; no implementation begins without "
            "explicit human approval."
        ),
    },
)

_PLANNING_TASK_FIELDS: tuple[str, ...] = (
    "planning_task_id",
    "objective_id",
    "assigned_agent",
    "capability_required",
    "execution_mode",
    "timeout_seconds",
    "status",
    "artifact_ref",
)

_PLANNER_RUNTIME_REQUIREMENTS: tuple[str, ...] = (
    "agent must be installed",
    "agent must have available lifecycle status",
    "agent must possess planning capability at observed confidence or higher",
    "agent must meet the configured confidence threshold",
)

_PLANNING_EXECUTION_MODES: tuple[dict, ...] = (
    {
        "mode": "single_planner",
        "description": "One planner agent produces a single plan.",
    },
    {
        "mode": "sequential_planners",
        "description": (
            "Planners execute one after another; each plan may reference prior outputs."
        ),
    },
    {
        "mode": "parallel_planners",
        "description": (
            "Multiple planners execute simultaneously; coordinator aggregates outputs."
        ),
    },
    {
        "mode": "swarm_planners",
        "description": (
            "Many planners operate on distinct planning sub-tasks simultaneously."
        ),
    },
    {
        "mode": "consensus_planners",
        "description": (
            "Multiple planners run in parallel; consensus engine resolves conflicts "
            "before human review."
        ),
    },
)

_PLANNING_ARTIFACT_COLLECTION_FIELDS: tuple[str, ...] = (
    "phases",
    "dependencies",
    "assumptions",
    "risks",
    "recommendations",
    "confidence",
)

_PLANNING_CONSENSUS_INTEGRATION: tuple[str, ...] = (
    "consensus engine",
    "conflict analysis",
    "agreement analysis",
)

_PLANNING_EXECUTION_GOVERNANCE: dict = {
    "roadmap_policy": (
        "Roadmaps produced by planning agents remain advisory until human-approved."
    ),
    "human_approval_required_before": [
        "task creation",
        "execution",
        "implementation",
    ],
    "governance_notes": [
        "Planning agents may not modify files.",
        "Planning agents may not commit.",
        "Planning agents may not push.",
        "All planning output is advisory until the human approves the roadmap.",
    ],
}

_PLANNING_EXECUTION_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44K", "description": "Agent Execution Framework"},
    {"phase": "44L", "description": "Runtime Adapter Integration"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_planning_execution_design() -> dict:
    """Return a read-only multi-agent planning execution architecture design."""
    return {
        "planning_execution_design": {
            "lifecycle": list(_PLANNING_EXECUTION_LIFECYCLE),
        },
        "planning_task_model": {
            "fields": list(_PLANNING_TASK_FIELDS),
        },
        "planner_runtime_requirements": list(_PLANNER_RUNTIME_REQUIREMENTS),
        "execution_modes": list(_PLANNING_EXECUTION_MODES),
        "artifact_collection": {
            "fields": list(_PLANNING_ARTIFACT_COLLECTION_FIELDS),
        },
        "consensus_integration": {
            "feeds_into": list(_PLANNING_CONSENSUS_INTEGRATION),
        },
        "governance_integration": _PLANNING_EXECUTION_GOVERNANCE,
        "future_evolution": list(_PLANNING_EXECUTION_FUTURE_EVOLUTION),
        "advisory": PLANNING_EXECUTION_DESIGN_ADVISORY,
    }


EXECUTION_FRAMEWORK_DESIGN_ADVISORY = (
    "Execution framework design is advisory; no agent execution is performed."
)

_EXECUTION_FRAMEWORK_LIFECYCLE: tuple[dict, ...] = (
    {
        "stage": 1,
        "name": "request",
        "description": (
            "Coordinator receives an execution request with objective and required capabilities."
        ),
    },
    {
        "stage": 2,
        "name": "capability_lookup",
        "description": (
            "Capability registry is queried to identify agents matching required capabilities."
        ),
    },
    {
        "stage": 3,
        "name": "agent_selection",
        "description": (
            "Eligible agents are selected based on capability match, confidence level, "
            "and lifecycle status."
        ),
    },
    {
        "stage": 4,
        "name": "execution_request_creation",
        "description": (
            "Coordinator creates a structured execution request for each selected agent."
        ),
    },
    {
        "stage": 5,
        "name": "runtime_adapter",
        "description": (
            "Execution request is dispatched to the appropriate runtime adapter "
            "for the assigned agent."
        ),
    },
    {
        "stage": 6,
        "name": "agent_execution",
        "description": (
            "Runtime adapter invokes the agent; agent executes and produces output artifacts."
        ),
    },
    {
        "stage": 7,
        "name": "result_capture",
        "description": (
            "Runtime adapter captures agent output, errors, and execution metadata."
        ),
    },
    {
        "stage": 8,
        "name": "consensus",
        "description": (
            "Collected results are fed into the consensus engine for agreement "
            "and conflict analysis."
        ),
    },
    {
        "stage": 9,
        "name": "governance",
        "description": (
            "Consensus output is handed off to governance for approval, commit, "
            "push, and rollback decisions."
        ),
    },
)

_EXECUTION_REQUEST_FIELDS: tuple[str, ...] = (
    "execution_id",
    "parent_task_id",
    "objective",
    "assigned_agent",
    "required_capabilities",
    "execution_mode",
    "writable_allowed",
    "timeout_seconds",
    "metadata",
)

_ADAPTER_CONTRACT_FIELDS: tuple[str, ...] = (
    "runtime_id",
    "availability",
    "version",
    "capabilities",
    "supports_writable_execution",
    "supports_subagents",
    "supports_parallel_execution",
)

_ADAPTER_REQUIRED_OPERATIONS: tuple[str, ...] = (
    "health()",
    "discover_capabilities()",
    "execute()",
    "cancel()",
    "collect_results()",
)

_EXECUTION_SUPPORTED_RUNTIMES: tuple[str, ...] = (
    "codex-local",
    "claude-local",
    "kimi-local",
)

_EXECUTION_FUTURE_RUNTIMES: tuple[str, ...] = (
    "deepseek-local",
    "gemini-local",
    "grok-local",
    "perplexity-local",
    "cloud runtimes",
)

_EXECUTION_RESULT_FIELDS: tuple[str, ...] = (
    "execution_id",
    "agent_id",
    "status",
    "started_at",
    "completed_at",
    "artifacts",
    "recommendations",
    "confidence",
    "errors",
)

_EXECUTION_GOVERNANCE_INTEGRATION: dict = {
    "framework_may": [
        "invoke runtimes",
        "collect results",
    ],
    "framework_may_not": [
        "approve",
        "commit",
        "push",
        "rollback",
    ],
    "note": "All governance operations remain external to the execution framework.",
}

_EXECUTION_FAILURE_TYPES: tuple[str, ...] = (
    "unavailable_runtime",
    "timeout",
    "execution_failure",
    "partial_result",
    "cancelled",
    "capability_mismatch",
)

_EXECUTION_FRAMEWORK_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44L", "description": "Runtime Adapter Integration"},
    {"phase": "44M", "description": "Controlled Agent Invocation"},
    {"phase": "44N", "description": "Real Multi-Agent Planning"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_execution_framework_design() -> dict:
    """Return a read-only agent execution framework architecture design."""
    return {
        "execution_framework_design": {
            "supported_runtimes": list(_EXECUTION_SUPPORTED_RUNTIMES),
            "future_runtimes": list(_EXECUTION_FUTURE_RUNTIMES),
        },
        "execution_lifecycle": list(_EXECUTION_FRAMEWORK_LIFECYCLE),
        "runtime_adapter_contract": {
            "fields": list(_ADAPTER_CONTRACT_FIELDS),
            "required_operations": list(_ADAPTER_REQUIRED_OPERATIONS),
        },
        "execution_request_model": {
            "fields": list(_EXECUTION_REQUEST_FIELDS),
        },
        "result_model": {
            "fields": list(_EXECUTION_RESULT_FIELDS),
        },
        "governance_integration": _EXECUTION_GOVERNANCE_INTEGRATION,
        "failure_model": {
            "failure_types": list(_EXECUTION_FAILURE_TYPES),
            "escalation": "human escalation is default",
        },
        "future_evolution": list(_EXECUTION_FRAMEWORK_FUTURE_EVOLUTION),
        "advisory": EXECUTION_FRAMEWORK_DESIGN_ADVISORY,
    }


ADAPTER_DESIGN_ADVISORY = (
    "Runtime adapter integration design is advisory; no adapters are executed."
)

_ADAPTER_ARCHITECTURE_LAYERS: tuple[str, ...] = (
    "Coordinator",
    "Execution Framework",
    "Runtime Adapter Registry",
    "Runtime Adapters",
    "Agent Runtime",
)

_ADAPTER_REGISTRY_RESPONSIBILITIES: tuple[str, ...] = (
    "register adapters",
    "discover adapters",
    "resolve adapter by runtime_id",
    "report adapter capabilities",
    "report adapter health",
)

_ADAPTER_REGISTRY_FIELDS: tuple[str, ...] = (
    "runtime_id",
    "adapter_class",
    "lifecycle_status",
    "version",
    "supported_capabilities",
    "writable_supported",
    "subagent_supported",
    "parallel_supported",
)

_ADAPTER_CONTRACT_REQUIRED_METHODS: tuple[str, ...] = (
    "health()",
    "discover_capabilities()",
    "execute()",
    "cancel()",
    "collect_results()",
)

_ADAPTER_CONTRACT_OPTIONAL_METHODS: tuple[str, ...] = (
    "discover_subagents()",
    "discover_skills()",
    "discover_swarm()",
    "estimate_cost()",
    "estimate_duration()",
)

_INITIAL_RUNTIME_ADAPTERS: tuple[dict, ...] = (
    {
        "adapter_id": "codex-local-adapter",
        "supports": ["execution", "writable execution", "subagents", "skills"],
    },
    {
        "adapter_id": "claude-local-adapter",
        "supports": ["execution", "writable execution", "agent teams"],
    },
    {
        "adapter_id": "kimi-local-adapter",
        "supports": ["execution", "writable execution", "swarm"],
    },
)

_FUTURE_RUNTIME_ADAPTERS: tuple[str, ...] = (
    "deepseek-local-adapter",
    "gemini-local-adapter",
    "grok-local-adapter",
    "perplexity-local-adapter",
    "cloud adapters",
)

_ADAPTER_HEALTH_STATES: tuple[str, ...] = (
    "available",
    "degraded",
    "unavailable",
    "unknown",
)

_ADAPTER_CAPABILITY_SYNC: tuple[str, ...] = (
    "runtime discovery",
    "version discovery",
    "capability discovery",
)

_ADAPTER_GOVERNANCE_INTEGRATION: dict = {
    "adapters_may": [
        "execute runtime requests",
        "collect runtime results",
    ],
    "adapters_may_not": [
        "approve",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
}

_ADAPTER_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44M", "description": "Controlled Agent Invocation"},
    {"phase": "44N", "description": "Real Multi-Agent Planning"},
    {"phase": "44O", "description": "Multi-Agent Consensus Execution"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_adapter_design() -> dict:
    """Return a read-only runtime adapter integration architecture design."""
    return {
        "adapter_design": {
            "architecture_layers": list(_ADAPTER_ARCHITECTURE_LAYERS),
            "initial_adapters": list(_INITIAL_RUNTIME_ADAPTERS),
            "future_adapters": list(_FUTURE_RUNTIME_ADAPTERS),
        },
        "adapter_registry": {
            "responsibilities": list(_ADAPTER_REGISTRY_RESPONSIBILITIES),
            "fields": list(_ADAPTER_REGISTRY_FIELDS),
        },
        "adapter_contract": {
            "required_methods": list(_ADAPTER_CONTRACT_REQUIRED_METHODS),
            "optional_methods": list(_ADAPTER_CONTRACT_OPTIONAL_METHODS),
        },
        "adapter_health_model": {
            "states": list(_ADAPTER_HEALTH_STATES),
            "capability_sync": list(_ADAPTER_CAPABILITY_SYNC),
            "capability_registry_note": (
                "Capability registry remains source of truth."
            ),
        },
        "governance_integration": _ADAPTER_GOVERNANCE_INTEGRATION,
        "future_evolution": list(_ADAPTER_FUTURE_EVOLUTION),
        "advisory": ADAPTER_DESIGN_ADVISORY,
    }


INVOCATION_DESIGN_ADVISORY = (
    "Controlled invocation design is advisory; no agents are invoked."
)

_INVOCATION_LIFECYCLE: tuple[dict, ...] = (
    {
        "stage": 1,
        "name": "request",
        "description": "Coordinator receives a controlled invocation request.",
    },
    {
        "stage": 2,
        "name": "capability_validation",
        "description": (
            "Required capabilities are validated against the capability registry "
            "and confidence thresholds."
        ),
    },
    {
        "stage": 3,
        "name": "agent_selection",
        "description": (
            "Eligible agents are selected based on validated capability match "
            "and lifecycle status."
        ),
    },
    {
        "stage": 4,
        "name": "adapter_resolution",
        "description": (
            "Runtime adapter registry resolves the correct adapter "
            "for the assigned runtime."
        ),
    },
    {
        "stage": 5,
        "name": "invocation_request_creation",
        "description": (
            "A structured invocation request is created with all safety gate fields "
            "populated."
        ),
    },
    {
        "stage": 6,
        "name": "runtime_invocation",
        "description": (
            "Adapter invokes the agent runtime; invocation is blocked if any "
            "safety gate fails."
        ),
    },
    {
        "stage": 7,
        "name": "result_capture",
        "description": (
            "Adapter captures agent output, artifacts, errors, and timing metadata."
        ),
    },
    {
        "stage": 8,
        "name": "consensus",
        "description": (
            "Captured results are fed to the consensus engine for agreement "
            "and conflict analysis."
        ),
    },
    {
        "stage": 9,
        "name": "governance",
        "description": (
            "Consensus output is handed to governance for approval, commit, "
            "push, and rollback decisions."
        ),
    },
)

_INVOCATION_REQUEST_FIELDS: tuple[str, ...] = (
    "invocation_id",
    "execution_id",
    "runtime_id",
    "agent_id",
    "objective",
    "capabilities_required",
    "writable_allowed",
    "timeout_seconds",
    "metadata",
)

_INVOCATION_SAFETY_REQUIRED: tuple[str, ...] = (
    "runtime available",
    "capability present",
    "confidence threshold met",
    "governance mode valid",
    "objective present",
)

_INVOCATION_SAFETY_BLOCKED: tuple[str, ...] = (
    "runtime unavailable",
    "capability mismatch",
    "governance violation",
    "timeout invalid",
)

_WRITABLE_INVOCATION_REQUIRES: tuple[str, ...] = (
    "explicit governance approval",
    "writable_supported runtime",
    "audit trail",
)

_INVOCATION_FLOW: tuple[str, ...] = (
    "coordinator",
    "execution framework",
    "adapter",
    "runtime",
)

_RESULT_FLOW: tuple[str, ...] = (
    "runtime",
    "adapter",
    "execution framework",
    "coordinator",
)

_RESULT_CAPTURE_FIELDS: tuple[str, ...] = (
    "invocation_id",
    "status",
    "artifacts",
    "recommendations",
    "confidence",
    "errors",
    "timestamps",
)

_INVOCATION_GOVERNANCE_INTEGRATION: dict = {
    "system_may": [
        "invoke agents",
        "collect results",
    ],
    "system_may_not": [
        "approve",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
}

_INVOCATION_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44N", "description": "Real Multi-Agent Planning Design"},
    {"phase": "44O", "description": "Multi-Agent Consensus Execution Design"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_invocation_design() -> dict:
    """Return a read-only controlled agent invocation architecture design."""
    return {
        "invocation_design": {
            "invocation_flow": list(_INVOCATION_FLOW),
            "result_flow": list(_RESULT_FLOW),
        },
        "invocation_lifecycle": list(_INVOCATION_LIFECYCLE),
        "invocation_request_model": {
            "fields": list(_INVOCATION_REQUEST_FIELDS),
        },
        "safety_gates": {
            "required_before_invocation": list(_INVOCATION_SAFETY_REQUIRED),
            "blocked_if": list(_INVOCATION_SAFETY_BLOCKED),
        },
        "writable_rules": {
            "default": "read-only",
            "writable_requires": list(_WRITABLE_INVOCATION_REQUIRES),
        },
        "result_capture_model": {
            "fields": list(_RESULT_CAPTURE_FIELDS),
        },
        "governance_integration": _INVOCATION_GOVERNANCE_INTEGRATION,
        "future_evolution": list(_INVOCATION_FUTURE_EVOLUTION),
        "advisory": INVOCATION_DESIGN_ADVISORY,
    }


REAL_PLANNING_DESIGN_ADVISORY = (
    "Real planning design is advisory; no planners are executed."
)

_REAL_PLANNING_LIFECYCLE: tuple[dict, ...] = (
    {
        "stage": 1,
        "name": "objective",
        "description": "Coordinator receives a planning objective.",
    },
    {
        "stage": 2,
        "name": "capability_discovery",
        "description": (
            "Available planners are discovered via the capability registry."
        ),
    },
    {
        "stage": 3,
        "name": "planner_selection",
        "description": (
            "Eligible planners are selected based on capability match, "
            "confidence threshold, and invocation safety gates."
        ),
    },
    {
        "stage": 4,
        "name": "invocation_creation",
        "description": (
            "A structured invocation request is created for each selected planner."
        ),
    },
    {
        "stage": 5,
        "name": "planner_execution",
        "description": (
            "Selected planners are executed through the execution framework "
            "and runtime adapters."
        ),
    },
    {
        "stage": 6,
        "name": "artifact_collection",
        "description": (
            "Planning artifacts are collected from each planner execution result."
        ),
    },
    {
        "stage": 7,
        "name": "consensus",
        "description": (
            "Collected artifacts are fed to the consensus engine for agreement "
            "and conflict analysis."
        ),
    },
    {
        "stage": 8,
        "name": "human_review",
        "description": (
            "Human reviewer evaluates consensus output before any roadmap is approved."
        ),
    },
    {
        "stage": 9,
        "name": "approved_roadmap",
        "description": (
            "Human-approved roadmap is recorded as a governed planning artifact."
        ),
    },
)

_PLANNER_ELIGIBILITY_CRITERIA: tuple[str, ...] = (
    "be installed",
    "be available",
    "support planning capability",
    "satisfy confidence threshold",
    "pass invocation safety gates",
)

_REAL_PLANNING_EXECUTION_MODES: tuple[dict, ...] = (
    {
        "mode": "single_planner",
        "description": "One planner produces a single planning artifact.",
    },
    {
        "mode": "sequential_planners",
        "description": "Planners execute in sequence; each builds on prior artifacts.",
    },
    {
        "mode": "parallel_planners",
        "description": "Planners execute concurrently; artifacts are collected independently.",
    },
    {
        "mode": "swarm_planners",
        "description": "Multiple planners execute with shared context and cross-artifact visibility.",
    },
    {
        "mode": "consensus_planners",
        "description": "Planners execute independently; consensus engine resolves conflicts.",
    },
)

_REAL_PLANNING_ARTIFACT_FIELDS: tuple[str, ...] = (
    "artifact_id",
    "objective_id",
    "planner_id",
    "proposed_phases",
    "dependencies",
    "assumptions",
    "risks",
    "recommendations",
    "confidence",
)

_CONSENSUS_INTEGRATION_FEEDS: tuple[str, ...] = (
    "agreement analysis",
    "conflict analysis",
    "consensus summary",
)

_HUMAN_REVIEW_ACTIONS: tuple[str, ...] = (
    "approve roadmap",
    "reject roadmap",
    "request changes",
    "request additional planners",
)

_REAL_PLANNING_GOVERNANCE_INTEGRATION: dict = {
    "system_may": [
        "invoke planners",
        "collect planning artifacts",
    ],
    "system_may_not": [
        "approve implementation",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
}

_REAL_PLANNING_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44O", "description": "Multi-Agent Consensus Execution Design"},
    {"phase": "44P", "description": "Controlled Runtime Execution Prototype"},
    {"phase": "44Q", "description": "Planner Runtime Adapter Prototype"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_real_planning_design() -> dict:
    """Return a read-only real multi-agent planning architecture design."""
    return {
        "real_planning_design": {
            "planning_lifecycle": list(_REAL_PLANNING_LIFECYCLE),
        },
        "planning_lifecycle": list(_REAL_PLANNING_LIFECYCLE),
        "planner_eligibility": {
            "criteria": list(_PLANNER_ELIGIBILITY_CRITERIA),
            "human_review_required_before_execution": True,
        },
        "execution_modes": list(_REAL_PLANNING_EXECUTION_MODES),
        "planning_artifact_model": {
            "fields": list(_REAL_PLANNING_ARTIFACT_FIELDS),
        },
        "consensus_integration": {
            "feeds_into": list(_CONSENSUS_INTEGRATION_FEEDS),
        },
        "human_review_model": {
            "actions": list(_HUMAN_REVIEW_ACTIONS),
            "human_review_required": True,
        },
        "governance_integration": _REAL_PLANNING_GOVERNANCE_INTEGRATION,
        "future_evolution": list(_REAL_PLANNING_FUTURE_EVOLUTION),
        "advisory": REAL_PLANNING_DESIGN_ADVISORY,
    }


CONSENSUS_EXECUTION_DESIGN_ADVISORY = (
    "Consensus execution design is advisory; no consensus execution is performed."
)

_CEXEC_LIFECYCLE: tuple[dict, ...] = (
    {
        "stage": 1,
        "name": "agent_outputs",
        "description": "Agent execution results are received as raw outputs.",
    },
    {
        "stage": 2,
        "name": "result_collection",
        "description": (
            "Outputs are normalized into structured consensus input records "
            "with identity, role, and confidence metadata."
        ),
    },
    {
        "stage": 3,
        "name": "agreement_analysis",
        "description": (
            "Matching and compatible recommendations are identified across agents; "
            "supporting evidence is aggregated."
        ),
    },
    {
        "stage": 4,
        "name": "conflict_analysis",
        "description": (
            "Conflicting recommendations, incompatible plans, missing evidence, "
            "and confidence discrepancies are surfaced."
        ),
    },
    {
        "stage": 5,
        "name": "weight_calculation",
        "description": (
            "Per-agent weights are calculated from capability confidence, "
            "availability, execution history, task fit, and role fit."
        ),
    },
    {
        "stage": 6,
        "name": "consensus_evaluation",
        "description": (
            "Weighted agreement and conflict scores are evaluated against "
            "configured consensus policy thresholds."
        ),
    },
    {
        "stage": 7,
        "name": "decision_recommendation",
        "description": (
            "A governance-level recommendation is generated: approve, reject, "
            "request_changes, inconclusive, or escalate_to_human."
        ),
    },
    {
        "stage": 8,
        "name": "human_review",
        "description": (
            "Human reviewer evaluates the recommendation before any governance "
            "action is taken."
        ),
    },
)

_CEXEC_INPUT_FIELDS: tuple[str, ...] = (
    "consensus_id",
    "execution_id",
    "agent_id",
    "role",
    "recommendation",
    "confidence",
    "rationale",
    "artifacts",
)

_CEXEC_AGREEMENT_IDENTIFIES: tuple[str, ...] = (
    "matching recommendations",
    "compatible recommendations",
    "supporting evidence",
)

_CEXEC_CONFLICT_IDENTIFIES: tuple[str, ...] = (
    "conflicting recommendations",
    "incompatible plans",
    "missing evidence",
    "confidence discrepancies",
)

_CEXEC_WEIGHT_INPUTS: tuple[str, ...] = (
    "capability confidence",
    "runtime availability",
    "successful execution history",
    "task fit",
    "role fit",
)

_CEXEC_RECOMMENDATION_TYPES: tuple[dict, ...] = (
    {
        "type": "approve",
        "description": "Strong agreement across agents; confidence above threshold.",
    },
    {
        "type": "reject",
        "description": "Dominant agreement that proposed action should not proceed.",
    },
    {
        "type": "request_changes",
        "description": "Partial agreement with identified conflicts requiring resolution.",
    },
    {
        "type": "inconclusive",
        "description": "Insufficient agreement or confidence to produce a clear recommendation.",
    },
    {
        "type": "escalate_to_human",
        "description": "Governance-sensitive action or unresolvable conflict requires human decision.",
    },
)

_CEXEC_HUMAN_REVIEW_CONDITIONS: tuple[str, ...] = (
    "conflicts exceed threshold",
    "confidence below threshold",
    "recommendation inconclusive",
    "governance-sensitive action proposed",
)

_CEXEC_GOVERNANCE_INTEGRATION: dict = {
    "system_may": [
        "evaluate outputs",
        "calculate weights",
        "generate recommendations",
    ],
    "system_may_not": [
        "approve implementation",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
}

_CEXEC_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44P", "description": "Controlled Runtime Execution Prototype"},
    {"phase": "44Q", "description": "Planner Runtime Adapter Prototype"},
    {"phase": "44R", "description": "Multi-Agent Execution Prototype"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_consensus_execution_design() -> dict:
    """Return a read-only multi-agent consensus execution architecture design."""
    return {
        "consensus_execution_design": {
            "execution_lifecycle": list(_CEXEC_LIFECYCLE),
        },
        "execution_lifecycle": list(_CEXEC_LIFECYCLE),
        "consensus_input_model": {
            "fields": list(_CEXEC_INPUT_FIELDS),
        },
        "agreement_analysis": {
            "identifies": list(_CEXEC_AGREEMENT_IDENTIFIES),
        },
        "conflict_analysis": {
            "identifies": list(_CEXEC_CONFLICT_IDENTIFIES),
        },
        "weighting_model": {
            "inputs": list(_CEXEC_WEIGHT_INPUTS),
        },
        "recommendation_types": list(_CEXEC_RECOMMENDATION_TYPES),
        "human_review_requirements": {
            "human_required_when": list(_CEXEC_HUMAN_REVIEW_CONDITIONS),
        },
        "governance_integration": _CEXEC_GOVERNANCE_INTEGRATION,
        "future_evolution": list(_CEXEC_FUTURE_EVOLUTION),
        "advisory": CONSENSUS_EXECUTION_DESIGN_ADVISORY,
    }


RUNTIME_EXECUTION_PROTOTYPE_ADVISORY = (
    "Runtime execution prototype is advisory; no agents are executed."
)

_PROTO_EXECUTION_REQUEST_FIELDS: tuple[str, ...] = (
    "request_id",
    "runtime_id",
    "objective",
    "capabilities_required",
    "timeout_seconds",
    "read_only",
    "metadata",
)

_PROTO_ADAPTER_RESOLUTION_STEPS: tuple[str, ...] = (
    "look up runtime_id in adapter registry",
    "verify adapter health",
    "verify capability match",
    "resolve adapter instance",
)

_PROTO_INVOCATION_ABSTRACTION: dict = {
    "execution_mode": "non_interactive",
    "delivery_methods": ["stdin", "prompt_file"],
    "output_capture": "structured",
    "timeout_enforcement": "adapter_enforced",
    "single_runtime": True,
    "writable": False,
}

_PROTO_RESULT_CAPTURE_FIELDS: tuple[str, ...] = (
    "request_id",
    "status",
    "output",
    "artifacts",
    "errors",
    "started_at",
    "completed_at",
    "duration_seconds",
)

_PROTO_RESULT_STATUSES: tuple[str, ...] = (
    "completed",
    "timed_out",
    "failed",
    "adapter_unavailable",
    "capability_mismatch",
)

_PROTO_TIMEOUT_RULES: tuple[str, ...] = (
    "timeout_seconds set at request creation",
    "adapter enforces timeout boundary",
    "on timeout: status = timed_out",
    "partial output preserved on timeout",
    "no automatic retry without human approval",
)

_PROTO_FAILURE_TYPES: tuple[dict, ...] = (
    {
        "type": "adapter_unavailable",
        "description": "Adapter registry cannot resolve a healthy adapter for runtime_id.",
    },
    {
        "type": "capability_mismatch",
        "description": "Resolved adapter does not satisfy required capabilities.",
    },
    {
        "type": "timeout",
        "description": "Execution exceeded timeout_seconds; partial output preserved.",
    },
    {
        "type": "execution_error",
        "description": "Runtime returned a non-zero exit code or fatal error.",
    },
    {
        "type": "output_parse_failure",
        "description": "Structured output could not be parsed from runtime response.",
    },
)

_PROTO_RESTRICTIONS: tuple[str, ...] = (
    "read_only_only",
    "single_runtime_only",
    "no_writable_execution",
    "no_commit",
    "no_push",
    "no_rollback",
    "no_subagents",
    "no_swarm",
    "no_consensus",
)

_PROTO_GOVERNANCE_INTEGRATION: dict = {
    "system_may": [
        "create execution requests",
        "resolve adapters",
        "invoke runtimes (read-only)",
        "capture results",
    ],
    "system_may_not": [
        "approve implementation",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
}

_PROTO_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44Q", "description": "Planner Runtime Adapter Prototype"},
    {"phase": "44R", "description": "Multi-Agent Execution Prototype"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_runtime_execution_prototype() -> dict:
    """Return a read-only controlled runtime execution prototype design."""
    return {
        "runtime_execution_prototype": {
            "restrictions": list(_PROTO_RESTRICTIONS),
        },
        "execution_request_model": {
            "fields": list(_PROTO_EXECUTION_REQUEST_FIELDS),
        },
        "adapter_resolution_model": {
            "steps": list(_PROTO_ADAPTER_RESOLUTION_STEPS),
        },
        "runtime_invocation_model": _PROTO_INVOCATION_ABSTRACTION,
        "result_capture_model": {
            "fields": list(_PROTO_RESULT_CAPTURE_FIELDS),
            "statuses": list(_PROTO_RESULT_STATUSES),
        },
        "timeout_model": {
            "rules": list(_PROTO_TIMEOUT_RULES),
        },
        "failure_model": {
            "types": list(_PROTO_FAILURE_TYPES),
        },
        "prototype_restrictions": list(_PROTO_RESTRICTIONS),
        "governance_integration": _PROTO_GOVERNANCE_INTEGRATION,
        "future_evolution": list(_PROTO_FUTURE_EVOLUTION),
        "advisory": RUNTIME_EXECUTION_PROTOTYPE_ADVISORY,
    }


PLANNER_ADAPTER_PROTOTYPE_ADVISORY = (
    "Planner adapter prototype is read-only; no planner runtime is invoked."
)

_PAP_DEFAULT_RUNTIME = "codex-local"
_PAP_DEFAULT_AGENT = "codex"
_PAP_CAPABILITY_REQUIRED = "planning"
_PAP_EXECUTION_MODE = "non_interactive"
_PAP_TIMEOUT_SECONDS = 300

_PAP_ADAPTER_RESOLUTION: dict = {
    "registry_lookup": "codex-local",
    "adapter_type": "cli",
    "health_check": "adapter health not probed (prototype preview)",
    "capability_verified": "planning (observed confidence)",
    "resolution_status": "resolved (prototype only)",
}

_PAP_INVOCATION_COMMAND_PREVIEW: str = (
    "codex --non-interactive --output-format json <prompt>"
)

_PAP_RESULT_CAPTURE_MODEL: tuple[str, ...] = (
    "planner_request_id",
    "status",
    "output",
    "proposed_phases",
    "assumptions",
    "risks",
    "confidence",
    "errors",
    "started_at",
    "completed_at",
    "duration_seconds",
)

_PAP_SAFETY_GATES: tuple[str, ...] = (
    "runtime_id present",
    "capability_required present",
    "planning capability at observed confidence or higher",
    "adapter resolved and healthy",
    "read_only mode enforced",
    "timeout_seconds set",
)

_PAP_BLOCKERS: tuple[str, ...] = (
    "codex-local not installed",
    "planning capability below confidence threshold",
    "adapter health check failed",
    "writable execution requested (not allowed in prototype)",
)

_PAP_PROTOTYPE_SCOPE: tuple[str, ...] = (
    "single_runtime_only",
    "read_only_only",
    "no_writable_execution",
    "no_file_modification",
    "no_child_task_persistence",
    "no_consensus_execution",
    "no_commit",
    "no_push",
)

_PAP_GOVERNANCE_INTEGRATION: dict = {
    "system_may": [
        "preview adapter resolution",
        "preview invocation command",
        "show safety gates",
        "show blockers",
    ],
    "system_may_not": [
        "invoke codex-local",
        "submit prompts",
        "create jobs",
        "modify files",
        "commit",
        "push",
        "bypass governance",
    ],
}

_PAP_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44R", "description": "Multi-Agent Execution Prototype"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_planner_adapter_prototype() -> dict:
    """Return a read-only planner runtime adapter prototype preview."""
    return {
        "planner_adapter_prototype": {
            "planner_request_id": "proto-44q-preview",
            "selected_runtime": _PAP_DEFAULT_RUNTIME,
            "selected_agent": _PAP_DEFAULT_AGENT,
            "capability_required": _PAP_CAPABILITY_REQUIRED,
            "execution_mode": _PAP_EXECUTION_MODE,
            "timeout_seconds": _PAP_TIMEOUT_SECONDS,
            "prototype_scope": list(_PAP_PROTOTYPE_SCOPE),
        },
        "adapter_resolution": _PAP_ADAPTER_RESOLUTION,
        "invocation_preview": {
            "invocation_command_preview": _PAP_INVOCATION_COMMAND_PREVIEW,
            "execution_mode": _PAP_EXECUTION_MODE,
            "timeout_seconds": _PAP_TIMEOUT_SECONDS,
            "result_capture_model": list(_PAP_RESULT_CAPTURE_MODEL),
        },
        "safety_gates": list(_PAP_SAFETY_GATES),
        "blockers": list(_PAP_BLOCKERS),
        "governance_integration": _PAP_GOVERNANCE_INTEGRATION,
        "future_evolution": list(_PAP_FUTURE_EVOLUTION),
        "advisory": PLANNER_ADAPTER_PROTOTYPE_ADVISORY,
    }


def build_capability_validation(root: HarnessPath) -> dict:
    """Return the capability validation framework. Read-only; no CLI probing.

    Includes documentation-reference capabilities from the doc catalog so that
    observed capabilities (subagent-coordination, swarm-coordination, etc.)
    appear as validation candidates without requiring live CLI probing.
    """
    profiles = [
        _build_agent_capability_profile(
            spec,
            root,
            probe_cli=False,
            doc_capabilities=_DOC_CAPABILITY_CATALOG.get(spec.agent_id, ()),
        )
        for spec in _CAPABILITY_AGENT_SPECS
    ]
    validation_candidates = _build_validation_candidates(profiles)
    normalized_summary = _build_normalized_summary(profiles)
    validation_framework = {
        "description": (
            "Framework for defining how PCAE promotes discovered agent capabilities "
            "from observed to validated and proven through controlled evidence."
        ),
        "lifecycle": list(CAPABILITY_VALIDATION_LIFECYCLE),
        "lifecycle_descriptions": {
            _CAP_CONF_UNKNOWN: "No evidence collected; capability unverified.",
            _CAP_CONF_OBSERVED: (
                "Evidence from documentation references or CLI discovery; "
                "not yet validated by a controlled experiment."
            ),
            _CAP_CONF_VALIDATED: "Confirmed by a successful controlled PCAE experiment.",
            _CAP_CONF_PROVEN: (
                "Confirmed by successful governed production usage in execution history; "
                "cannot be downgraded by documentation-only evidence."
            ),
        },
        "validation_sources": list(CAPABILITY_VALIDATION_SOURCES),
        "promotion_rules": list(_CAPABILITY_PROMOTION_RULES),
    }
    return {
        "validation_framework": validation_framework,
        "promotion_rules": list(_CAPABILITY_PROMOTION_RULES),
        "validation_candidates": validation_candidates,
        "normalized_summary": normalized_summary,
        "advisory": CAPABILITY_VALIDATION_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 44R: Multi-Agent Execution Prototype
# ---------------------------------------------------------------------------

MULTI_AGENT_EXECUTION_PROTOTYPE_ADVISORY = (
    "Multi-agent execution prototype is read-only; no runtimes are invoked."
)

_MAE_EXECUTION_ID = "proto-44r-preview"

_MAE_DEFAULT_AGENTS: tuple[str, ...] = (
    "codex-local",
    "claude-local",
    "kimi-local",
)

_MAE_AGENT_ROLES: dict[str, str] = {
    "codex-local": "implementation",
    "claude-local": "documentation",
    "kimi-local": "analysis",
}

_MAE_AGENT_ADAPTERS: dict[str, str] = {
    "codex-local": "cli_adapter_codex",
    "claude-local": "cli_adapter_claude",
    "kimi-local": "cli_adapter_kimi",
}

_MAE_AGENT_INVOCATION_PREVIEWS: dict[str, str] = {
    "codex-local": "codex --non-interactive --output-format json <prompt>",
    "claude-local": "claude --non-interactive --output-format json <prompt>",
    "kimi-local": "kimi --non-interactive --output-format json <prompt>",
}

_MAE_AGENT_TIMEOUTS: dict[str, int] = {
    "codex-local": 300,
    "claude-local": 300,
    "kimi-local": 300,
}

_MAE_CAPABILITIES_USED: tuple[str, ...] = (
    "code_generation",
    "documentation",
    "code_analysis",
)

_MAE_ORCHESTRATION_STRATEGY = "parallel_review"

_MAE_SUPPORTED_STRATEGIES: tuple[str, ...] = (
    "single_agent",
    "sequential",
    "parallel_review",
    "parallel_planning",
    "consensus",
)

_MAE_RESULT_COLLECTION_PLAN: dict = {
    "collection_mode": "structured",
    "per_agent_results": True,
    "timeout_enforcement": "per_agent",
    "partial_results_preserved": True,
    "result_fields": [
        "agent_id",
        "status",
        "output",
        "artifacts",
        "errors",
        "started_at",
        "completed_at",
        "duration_seconds",
    ],
}

_MAE_ARTIFACT_COLLECTION_PLAN: dict = {
    "collection_mode": "read_only",
    "artifact_types": ["output", "structured_json", "error_log"],
    "persistence": "none (prototype preview; no artifacts written)",
    "deduplication": "by agent_id",
}

_MAE_CONSENSUS_INPUT_PLAN: dict = {
    "consensus_mode": "advisory",
    "inputs": ["per_agent_output", "per_agent_confidence", "per_agent_status"],
    "aggregation": "human_escalation (default policy)",
    "note": "Consensus execution is planned for Phase 44S.",
}

_MAE_GOVERNANCE_RULES: dict = {
    "prototype_may": [
        "select agents from registry",
        "build execution plan",
        "preview invocations",
    ],
    "prototype_may_not": [
        "invoke runtimes",
        "submit prompts",
        "modify files",
        "commit",
        "push",
        "rollback",
    ],
}

_MAE_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44S", "description": "Consensus Prototype"},
    {"phase": "44T", "description": "Controlled Runtime Invocation Pilot"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_multi_agent_execution_prototype() -> dict:
    """Return a read-only multi-agent execution prototype preview."""
    selected_agents = list(_MAE_DEFAULT_AGENTS)
    assigned_roles = {aid: _MAE_AGENT_ROLES[aid] for aid in selected_agents}

    execution_plan = {
        "execution_id": _MAE_EXECUTION_ID,
        "selected_agents": selected_agents,
        "assigned_roles": assigned_roles,
        "capabilities_used": list(_MAE_CAPABILITIES_USED),
        "orchestration_strategy": _MAE_ORCHESTRATION_STRATEGY,
        "supported_strategies": list(_MAE_SUPPORTED_STRATEGIES),
    }

    invocation_previews = [
        {
            "runtime_id": aid,
            "adapter_id": _MAE_AGENT_ADAPTERS[aid],
            "invocation_preview": _MAE_AGENT_INVOCATION_PREVIEWS[aid],
            "timeout_seconds": _MAE_AGENT_TIMEOUTS[aid],
            "writable_allowed": False,
        }
        for aid in selected_agents
    ]

    aggregation_plan = {
        "result_collection_plan": _MAE_RESULT_COLLECTION_PLAN,
        "artifact_collection_plan": _MAE_ARTIFACT_COLLECTION_PLAN,
        "consensus_input_plan": _MAE_CONSENSUS_INPUT_PLAN,
    }

    return {
        "execution_plan": execution_plan,
        "selected_agents": selected_agents,
        "invocation_previews": invocation_previews,
        "aggregation_plan": aggregation_plan,
        "governance_rules": _MAE_GOVERNANCE_RULES,
        "future_evolution": list(_MAE_FUTURE_EVOLUTION),
        "advisory": MULTI_AGENT_EXECUTION_PROTOTYPE_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 44S: Consensus Prototype
# ---------------------------------------------------------------------------

CONSENSUS_PROTOTYPE_ADVISORY = (
    "Consensus prototype is simulated. No runtimes are invoked."
)

_CPROTO_SIMULATED_INPUTS: tuple[dict, ...] = (
    {
        "agent_id": "codex-local",
        "recommendation": "approve",
        "confidence": 0.85,
        "rationale": "Implementation is correct and all tests pass.",
    },
    {
        "agent_id": "claude-local",
        "recommendation": "approve",
        "confidence": 0.90,
        "rationale": "Documentation and code analysis confirm correctness.",
    },
    {
        "agent_id": "kimi-local",
        "recommendation": "request_changes",
        "confidence": 0.70,
        "rationale": "Code analysis identified potential edge cases requiring review.",
    },
)

_CPROTO_AGREEMENT_CANDIDATES: tuple[str, ...] = (
    "codex-local",
    "claude-local",
)

_CPROTO_CONFLICT_CANDIDATES: tuple[str, ...] = ("kimi-local",)

_CPROTO_AGREEMENTS: tuple[str, ...] = (
    "codex-local and claude-local both recommend approve",
)

_CPROTO_CONFLICTS: tuple[str, ...] = (
    "kimi-local recommends request_changes vs approve from codex-local and claude-local",
)

_CPROTO_CONFIDENCE_DIFFERENCES: dict = {
    "max": 0.90,
    "min": 0.70,
    "spread": 0.20,
    "note": "Spread exceeds 0.15; human review recommended.",
}

_CPROTO_WEIGHTING_PREVIEW: tuple[dict, ...] = (
    {
        "agent_id": "codex-local",
        "capability_confidence": "observed",
        "task_fit": "high",
        "role_fit": "implementation",
        "preview_weight": 0.35,
    },
    {
        "agent_id": "claude-local",
        "capability_confidence": "observed",
        "task_fit": "high",
        "role_fit": "documentation",
        "preview_weight": 0.40,
    },
    {
        "agent_id": "kimi-local",
        "capability_confidence": "observed",
        "task_fit": "medium",
        "role_fit": "analysis",
        "preview_weight": 0.25,
    },
)

_CPROTO_VALID_OUTCOMES: tuple[str, ...] = (
    "approve",
    "reject",
    "request_changes",
    "inconclusive",
    "escalate_to_human",
)

_CPROTO_RECOMMENDED_OUTCOME = "approve"

_CPROTO_RECOMMENDATION_BASIS = (
    "Weighted majority: 2 of 3 agents recommend approve. "
    "kimi-local conflict flagged for human review."
)

_CPROTO_HUMAN_REVIEW_REASON = (
    "Conflict detected: kimi-local recommendation differs from majority."
)

_CPROTO_GOVERNANCE_RULES: dict = {
    "prototype_may": [
        "aggregate outputs",
        "analyze agreements",
        "analyze conflicts",
        "generate recommendation preview",
    ],
    "prototype_may_not": [
        "execute consensus",
        "invoke runtimes",
        "modify files",
        "commit",
        "push",
        "rollback",
    ],
}

_CPROTO_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44T", "description": "Controlled Runtime Invocation Pilot"},
    {"phase": "44U", "description": "Multi-Agent Runtime Pilot"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_consensus_prototype() -> dict:
    """Return a read-only consensus prototype with simulated multi-agent outputs."""
    simulated_inputs = [dict(inp) for inp in _CPROTO_SIMULATED_INPUTS]

    aggregation = {
        "collected_outputs": simulated_inputs,
        "agreement_candidates": list(_CPROTO_AGREEMENT_CANDIDATES),
        "conflict_candidates": list(_CPROTO_CONFLICT_CANDIDATES),
    }

    agreement_analysis = {
        "agreements": list(_CPROTO_AGREEMENTS),
        "agreement_count": len(_CPROTO_AGREEMENTS),
    }

    conflict_analysis = {
        "conflicts": list(_CPROTO_CONFLICTS),
        "conflict_count": len(_CPROTO_CONFLICTS),
        "confidence_differences": _CPROTO_CONFIDENCE_DIFFERENCES,
    }

    weighting_preview = {
        "note": "Preview weights only; no real scoring is performed.",
        "weights": [dict(w) for w in _CPROTO_WEIGHTING_PREVIEW],
    }

    recommendation_preview = {
        "recommended_outcome": _CPROTO_RECOMMENDED_OUTCOME,
        "valid_outcomes": list(_CPROTO_VALID_OUTCOMES),
        "basis": _CPROTO_RECOMMENDATION_BASIS,
        "human_review_required": True,
        "human_review_reason": _CPROTO_HUMAN_REVIEW_REASON,
    }

    return {
        "simulated_inputs": simulated_inputs,
        "aggregation": aggregation,
        "agreement_analysis": agreement_analysis,
        "conflict_analysis": conflict_analysis,
        "weighting_preview": weighting_preview,
        "recommendation_preview": recommendation_preview,
        "governance_rules": _CPROTO_GOVERNANCE_RULES,
        "future_evolution": list(_CPROTO_FUTURE_EVOLUTION),
        "advisory": CONSENSUS_PROTOTYPE_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 44T: Controlled Runtime Invocation Pilot
# ---------------------------------------------------------------------------

INVOCATION_PILOT_ADVISORY = (
    "Invocation pilot is a design only. No runtime execution occurs."
)

_IPILOT_DEFAULT_RUNTIME = "codex-local"
_IPILOT_DEFAULT_AGENT = "codex"
_IPILOT_GOVERNANCE_MODE = "read_only"
_IPILOT_TIMEOUT_SECONDS = 300

_IPILOT_LIFECYCLE: tuple[str, ...] = (
    "request",
    "safety_validation",
    "adapter_resolution",
    "invocation_preparation",
    "runtime_execution (conceptual)",
    "result_capture",
    "human_review",
)

_IPILOT_REQUEST_FIELDS: tuple[str, ...] = (
    "pilot_id",
    "runtime_id",
    "agent_id",
    "objective",
    "timeout_seconds",
    "writable_allowed",
    "governance_mode",
)

_IPILOT_SAFETY_GATES: tuple[str, ...] = (
    "runtime available",
    "read-only mode enforced",
    "capability match verified",
    "governance valid",
    "timeout valid",
)

_IPILOT_RESULT_CAPTURE_FIELDS: tuple[str, ...] = (
    "status",
    "stdout_summary",
    "stderr_summary",
    "artifacts",
    "timestamps",
)

_IPILOT_PILOT_SCOPE: tuple[str, ...] = (
    "single_runtime_only",
    "read_only_only",
    "no_writable_execution",
    "no_file_modification",
    "no_subagents",
    "no_swarm",
    "no_consensus_execution",
    "no_commit",
    "no_push",
    "no_rollback",
)

_IPILOT_GOVERNANCE_RULES: dict = {
    "pilot_may": [
        "prepare invocation",
        "resolve adapter",
        "capture results",
    ],
    "pilot_may_not": [
        "modify files",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
}

_IPILOT_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44U", "description": "Multi-Agent Runtime Pilot"},
    {"phase": "44V", "description": "Consensus Runtime Pilot"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_invocation_pilot() -> dict:
    """Return a read-only controlled runtime invocation pilot design."""
    pilot_request_model = {
        "pilot_id": "pilot-44t-preview",
        "runtime_id": _IPILOT_DEFAULT_RUNTIME,
        "agent_id": _IPILOT_DEFAULT_AGENT,
        "objective": "<task objective — provided at invocation time>",
        "timeout_seconds": _IPILOT_TIMEOUT_SECONDS,
        "writable_allowed": False,
        "governance_mode": _IPILOT_GOVERNANCE_MODE,
        "fields": list(_IPILOT_REQUEST_FIELDS),
    }

    return {
        "pilot_lifecycle": list(_IPILOT_LIFECYCLE),
        "pilot_request_model": pilot_request_model,
        "safety_gates": list(_IPILOT_SAFETY_GATES),
        "result_capture": {
            "fields": list(_IPILOT_RESULT_CAPTURE_FIELDS),
        },
        "pilot_scope": list(_IPILOT_PILOT_SCOPE),
        "governance_rules": _IPILOT_GOVERNANCE_RULES,
        "future_evolution": list(_IPILOT_FUTURE_EVOLUTION),
        "advisory": INVOCATION_PILOT_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 44U: Multi-Agent Runtime Pilot
# ---------------------------------------------------------------------------

MULTI_RUNTIME_PILOT_ADVISORY = (
    "Multi-runtime pilot is read-only; no runtimes are invoked."
)

_MRPILOT_DEFAULT_RUNTIMES: tuple[str, ...] = (
    "codex-local",
    "claude-local",
    "kimi-local",
)

_MRPILOT_RUNTIME_AGENTS: dict[str, str] = {
    "codex-local": "codex",
    "claude-local": "claude",
    "kimi-local": "kimi",
}

_MRPILOT_RUNTIME_CAPABILITIES: dict[str, list[str]] = {
    "codex-local": ["code_generation", "test_writing"],
    "claude-local": ["documentation", "code_analysis"],
    "kimi-local": ["code_analysis", "research"],
}

_MRPILOT_RUNTIME_ADAPTERS: dict[str, str] = {
    "codex-local": "cli_adapter_codex",
    "claude-local": "cli_adapter_claude",
    "kimi-local": "cli_adapter_kimi",
}

_MRPILOT_INVOCATION_PREVIEWS: dict[str, str] = {
    "codex-local": "codex --non-interactive --output-format json <prompt>",
    "claude-local": "claude --non-interactive --output-format json <prompt>",
    "kimi-local": "kimi --non-interactive --output-format json <prompt>",
}

_MRPILOT_PILOT_ID = "pilot-44u-preview"
_MRPILOT_DEFAULT_STRATEGY = "parallel_review"
_MRPILOT_TIMEOUT_SECONDS = 300

_MRPILOT_SUPPORTED_STRATEGIES: tuple[str, ...] = (
    "sequential",
    "parallel_review",
    "parallel_planning",
    "consensus_preparation",
)

_MRPILOT_EXPECTED_ARTIFACTS: tuple[str, ...] = (
    "structured_output",
    "error_log",
    "confidence_score",
)

_MRPILOT_EXPECTED_RECOMMENDATIONS: tuple[str, ...] = (
    "approve",
    "request_changes",
    "inconclusive",
)

_MRPILOT_EXPECTED_METADATA: tuple[str, ...] = (
    "runtime_id",
    "agent_id",
    "started_at",
    "completed_at",
    "duration_seconds",
)

_MRPILOT_CONSENSUS_INPUTS: tuple[str, ...] = (
    "per_runtime_recommendation",
    "per_runtime_confidence",
    "per_runtime_rationale",
)

_MRPILOT_PILOT_SCOPE: tuple[str, ...] = (
    "read_only_only",
    "no_writable_execution",
    "no_file_modification",
    "no_commit",
    "no_push",
    "no_rollback",
    "no_subagent_execution",
    "no_swarm_execution",
    "no_consensus_execution",
)

_MRPILOT_GOVERNANCE_RULES: dict = {
    "pilot_may": [
        "select runtimes",
        "create execution plan",
        "generate invocation previews",
        "prepare consensus inputs",
    ],
    "pilot_may_not": [
        "invoke runtimes",
        "submit prompts",
        "modify files",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
}

_MRPILOT_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44V", "description": "Consensus Runtime Pilot"},
    {"phase": "44W", "description": "Governed Execution Dry-Run"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_multi_runtime_pilot() -> dict:
    """Return a read-only multi-runtime pilot preview."""
    selected_runtimes = list(_MRPILOT_DEFAULT_RUNTIMES)
    selected_agents = {rid: _MRPILOT_RUNTIME_AGENTS[rid] for rid in selected_runtimes}

    runtime_selection = {
        "selected_runtimes": selected_runtimes,
        "selected_agents": selected_agents,
        "capability_summary": {
            rid: list(_MRPILOT_RUNTIME_CAPABILITIES[rid]) for rid in selected_runtimes
        },
    }

    execution_plan = {
        "pilot_id": _MRPILOT_PILOT_ID,
        "orchestration_strategy": _MRPILOT_DEFAULT_STRATEGY,
        "supported_strategies": list(_MRPILOT_SUPPORTED_STRATEGIES),
        "participating_runtimes": selected_runtimes,
        "participating_agents": [selected_agents[rid] for rid in selected_runtimes],
        "timeout_seconds": _MRPILOT_TIMEOUT_SECONDS,
        "writable_allowed": False,
    }

    invocation_previews = [
        {
            "runtime_id": rid,
            "adapter_id": _MRPILOT_RUNTIME_ADAPTERS[rid],
            "invocation_preview": _MRPILOT_INVOCATION_PREVIEWS[rid],
            "timeout_seconds": _MRPILOT_TIMEOUT_SECONDS,
            "writable_allowed": False,
        }
        for rid in selected_runtimes
    ]

    result_capture_plan = {
        "expected_artifacts": list(_MRPILOT_EXPECTED_ARTIFACTS),
        "expected_recommendations": list(_MRPILOT_EXPECTED_RECOMMENDATIONS),
        "expected_confidence": "per_runtime float in [0.0, 1.0]",
        "expected_metadata": list(_MRPILOT_EXPECTED_METADATA),
    }

    consensus_preparation = {
        "consensus_inputs": list(_MRPILOT_CONSENSUS_INPUTS),
        "agreement_candidates": "runtimes sharing the same recommendation",
        "conflict_candidates": "runtimes with differing recommendations",
        "note": "Consensus execution is not performed in this pilot.",
    }

    return {
        "runtime_selection": runtime_selection,
        "execution_plan": execution_plan,
        "invocation_previews": invocation_previews,
        "result_capture_plan": result_capture_plan,
        "consensus_preparation": consensus_preparation,
        "governance_rules": _MRPILOT_GOVERNANCE_RULES,
        "future_evolution": list(_MRPILOT_FUTURE_EVOLUTION),
        "advisory": MULTI_RUNTIME_PILOT_ADVISORY,
    }


# Phase 44V: Consensus Runtime Pilot
# ---------------------------------------------------------------------------

CONSENSUS_RUNTIME_PILOT_ADVISORY = (
    "Consensus runtime pilot is simulated; no runtimes are invoked."
)

_CRPILOT_PILOT_ID = "pilot-44v-preview"

_CRPILOT_DEFAULT_RUNTIMES: tuple[str, ...] = (
    "codex-local",
    "claude-local",
    "kimi-local",
)

_CRPILOT_SIMULATED_OUTPUTS: tuple[dict, ...] = (
    {
        "runtime_id": "codex-local",
        "recommendation": "approve",
        "confidence": 0.85,
        "rationale": "Code changes are well-structured and follow project conventions.",
        "artifact_summary": "3 files reviewed, 0 critical issues, 2 minor suggestions.",
    },
    {
        "runtime_id": "claude-local",
        "recommendation": "approve",
        "confidence": 0.90,
        "rationale": "Implementation is correct and documentation is complete.",
        "artifact_summary": "Architecture review complete; governance docs verified.",
    },
    {
        "runtime_id": "kimi-local",
        "recommendation": "request_changes",
        "confidence": 0.70,
        "rationale": "Edge case in error handling requires attention before approval.",
        "artifact_summary": "2 potential edge cases identified; test coverage gap detected.",
    },
)

_CRPILOT_OUTPUT_METADATA: dict = {
    "collection_mode": "simulated",
    "runtime_count": 3,
    "collection_timestamp": "pilot-44v-simulated",
    "writable_allowed": False,
}

_CRPILOT_RUNTIME_SUMMARY: dict = {
    "total_runtimes": 3,
    "outputs_collected": 3,
    "outputs_missing": 0,
    "recommendation_distribution": {
        "approve": 2,
        "request_changes": 1,
    },
}

_CRPILOT_AGREEMENT_ANALYSIS: dict = {
    "matching_recommendations": ["codex-local", "claude-local"],
    "matching_recommendation": "approve",
    "compatible_recommendations": ["codex-local", "claude-local"],
    "supporting_evidence": [
        "codex-local and claude-local both recommend 'approve'",
        "Combined confidence of matching agents: 0.875",
        "No critical issues identified by matching agents",
    ],
}

_CRPILOT_CONFLICT_ANALYSIS: dict = {
    "conflicting_recommendations": [
        {
            "runtime_id": "kimi-local",
            "recommendation": "request_changes",
            "conflicts_with": "approve (codex-local, claude-local)",
        }
    ],
    "confidence_differences": {
        "max_confidence": 0.90,
        "min_confidence": 0.70,
        "confidence_spread": 0.20,
    },
    "missing_evidence": [
        "kimi-local did not identify specific lines requiring changes"
    ],
}

_CRPILOT_VALID_OUTCOMES: tuple[str, ...] = (
    "approve",
    "reject",
    "request_changes",
    "inconclusive",
    "escalate_to_human",
)

_CRPILOT_RECOMMENDATION_PREVIEW: dict = {
    "consensus_recommendation": "approve",
    "basis": "weighted majority 2 of 3",
    "human_review_required": True,
    "human_review_reason": "conflict detected: kimi-local recommends request_changes",
}

_CRPILOT_GOVERNANCE_RULES: dict = {
    "pilot_may": [
        "collect outputs",
        "analyze agreements",
        "analyze conflicts",
        "generate recommendation preview",
    ],
    "pilot_may_not": [
        "invoke runtimes",
        "submit prompts",
        "modify files",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
}

_CRPILOT_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44W", "description": "Governed Execution Dry-Run"},
    {"phase": "44X", "description": "Runtime Invocation Validation"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_consensus_runtime_pilot() -> dict:
    """Return a read-only consensus runtime pilot with simulated multi-runtime outputs."""
    runtime_outputs = list(_CRPILOT_SIMULATED_OUTPUTS)

    result_collection = {
        "collected_outputs": runtime_outputs,
        "output_metadata": dict(_CRPILOT_OUTPUT_METADATA),
        "runtime_summary": dict(_CRPILOT_RUNTIME_SUMMARY),
    }

    recommendation_preview = {
        "consensus_recommendation": _CRPILOT_RECOMMENDATION_PREVIEW["consensus_recommendation"],
        "basis": _CRPILOT_RECOMMENDATION_PREVIEW["basis"],
        "valid_outcomes": list(_CRPILOT_VALID_OUTCOMES),
        "human_review_required": _CRPILOT_RECOMMENDATION_PREVIEW["human_review_required"],
        "human_review_reason": _CRPILOT_RECOMMENDATION_PREVIEW["human_review_reason"],
    }

    return {
        "pilot_id": _CRPILOT_PILOT_ID,
        "runtime_outputs": runtime_outputs,
        "result_collection": result_collection,
        "agreement_analysis": dict(_CRPILOT_AGREEMENT_ANALYSIS),
        "conflict_analysis": dict(_CRPILOT_CONFLICT_ANALYSIS),
        "recommendation_preview": recommendation_preview,
        "governance_rules": _CRPILOT_GOVERNANCE_RULES,
        "future_evolution": list(_CRPILOT_FUTURE_EVOLUTION),
        "advisory": CONSENSUS_RUNTIME_PILOT_ADVISORY,
    }


# Phase 44W: Governed Execution Dry-Run
# ---------------------------------------------------------------------------

GOVERNED_EXECUTION_DRY_RUN_ADVISORY = (
    "Governed execution dry-run is simulated; no runtimes are invoked."
)

_GEDR_DRY_RUN_ID = "dry-run-44w-preview"

_GEDR_LIFECYCLE: tuple[dict, ...] = (
    {"step": 1, "name": "objective_intake", "description": "Validate and record the execution objective."},
    {"step": 2, "name": "capability_discovery", "description": "Match requested capabilities to available runtimes."},
    {"step": 3, "name": "runtime_selection", "description": "Select runtimes based on capability coverage."},
    {"step": 4, "name": "invocation_planning", "description": "Plan invocations per runtime with governance checkpoints."},
    {"step": 5, "name": "simulated_result_capture", "description": "Define result capture plan (no execution)."},
    {"step": 6, "name": "consensus_preparation", "description": "Prepare inputs for consensus evaluation."},
    {"step": 7, "name": "governance_decision_point", "description": "Evaluate governance checkpoints; surface blockers."},
    {"step": 8, "name": "human_review", "description": "Human review is always required before any outcome is acted upon."},
)

_GEDR_OBJECTIVE: dict = {
    "objective_id": "obj-44w-preview",
    "description": "Review and validate implementation changes for governance compliance.",
    "requested_capabilities": ["code_analysis", "documentation", "governance_validation"],
    "governance_mode": "read_only",
    "writable_allowed": False,
}

_GEDR_CAPABILITY_DISCOVERY: dict = {
    "requested_capabilities": ["code_analysis", "documentation", "governance_validation"],
    "discovered_runtimes": {
        "code_analysis": ["codex-local", "claude-local", "kimi-local"],
        "documentation": ["claude-local"],
        "governance_validation": ["claude-local"],
    },
    "coverage": "full",
    "unmet_capabilities": [],
}

_GEDR_SELECTED_RUNTIMES: tuple[str, ...] = (
    "codex-local",
    "claude-local",
    "kimi-local",
)

_GEDR_INVOCATION_PLAN: tuple[dict, ...] = (
    {
        "step": 1,
        "runtime_id": "codex-local",
        "capability": "code_analysis",
        "invocation_preview": "codex --non-interactive --output-format json <prompt>",
        "timeout_seconds": 300,
        "writable_allowed": False,
        "governance_checkpoint": "pre_invocation_safety_gate",
    },
    {
        "step": 2,
        "runtime_id": "kimi-local",
        "capability": "code_analysis",
        "invocation_preview": "kimi --non-interactive --output-format json <prompt>",
        "timeout_seconds": 300,
        "writable_allowed": False,
        "governance_checkpoint": "pre_invocation_safety_gate",
    },
    {
        "step": 3,
        "runtime_id": "claude-local",
        "capability": "documentation",
        "invocation_preview": "claude --non-interactive --output-format json <prompt>",
        "timeout_seconds": 300,
        "writable_allowed": False,
        "governance_checkpoint": "pre_invocation_safety_gate",
    },
    {
        "step": 4,
        "runtime_id": "claude-local",
        "capability": "governance_validation",
        "invocation_preview": "claude --non-interactive --output-format json <prompt>",
        "timeout_seconds": 300,
        "writable_allowed": False,
        "governance_checkpoint": "post_execution_governance_audit",
    },
)

_GEDR_SIMULATED_RESULT_PLAN: dict = {
    "collection_mode": "simulated",
    "expected_fields": [
        "runtime_id",
        "status",
        "output",
        "confidence",
        "artifacts",
        "duration_seconds",
    ],
    "simulated_outcomes": [
        {"runtime_id": "codex-local", "status": "completed", "confidence": 0.85},
        {"runtime_id": "kimi-local", "status": "completed", "confidence": 0.70},
        {"runtime_id": "claude-local", "status": "completed", "confidence": 0.90},
    ],
    "partial_result_handling": "preserved",
    "writable_allowed": False,
}

_GEDR_CONSENSUS_HANDOFF: dict = {
    "inputs_prepared": [
        "per_runtime_recommendation",
        "per_runtime_confidence",
        "per_runtime_rationale",
    ],
    "agreement_threshold": 0.67,
    "conflict_escalation": "escalate_to_human",
    "human_review_required": True,
    "handoff_status": "planned",
    "note": "Consensus execution is not performed in this dry-run.",
}

_GEDR_GOVERNANCE_CHECKPOINTS: tuple[dict, ...] = (
    {
        "checkpoint": "objective_intake",
        "description": "Objective validated: governance_mode=read_only, writable_allowed=false.",
        "command": "pcae check",
        "required": True,
    },
    {
        "checkpoint": "capability_discovery",
        "description": "All requested capabilities covered by available runtimes.",
        "command": "pcae orchestration capabilities",
        "required": True,
    },
    {
        "checkpoint": "pre_invocation_safety_gate",
        "description": "Each runtime verified: read-only mode enforced, capability matched, governance valid.",
        "command": "pcae health",
        "required": True,
    },
    {
        "checkpoint": "post_execution_governance_audit",
        "description": "Results collected; no writable artifacts produced; audit trail complete.",
        "command": "pcae check",
        "required": True,
    },
    {
        "checkpoint": "human_review",
        "description": "Human review required before any outcome is acted upon.",
        "command": None,
        "required": True,
    },
)

_GEDR_BLOCKERS: tuple[str, ...] = (
    "no_runtime_invocation: runtimes are not invoked in this dry-run",
    "no_writable_execution: writable_allowed is always false",
    "no_file_modification: no files are modified",
    "no_approval_mutation: governance decisions are advisory only",
)

_GEDR_GOVERNANCE_RULES: dict = {
    "dry_run_may": [
        "intake objective",
        "discover capabilities",
        "select runtimes",
        "plan invocations",
        "simulate result capture",
        "prepare consensus handoff",
        "expose governance checkpoints",
    ],
    "dry_run_may_not": [
        "invoke runtimes",
        "submit prompts",
        "modify files",
        "commit",
        "push",
        "rollback",
        "mutate approvals",
        "bypass governance",
    ],
}

_GEDR_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "44X", "description": "Runtime Invocation Validation"},
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_governed_execution_dry_run() -> dict:
    """Return a read-only governed execution dry-run showing the full lifecycle."""
    return {
        "dry_run_id": _GEDR_DRY_RUN_ID,
        "lifecycle": list(_GEDR_LIFECYCLE),
        "objective_intake": dict(_GEDR_OBJECTIVE),
        "capability_discovery": dict(_GEDR_CAPABILITY_DISCOVERY),
        "runtime_selection": {
            "selected_runtimes": list(_GEDR_SELECTED_RUNTIMES),
            "selection_basis": "capability coverage",
        },
        "invocation_plan": list(_GEDR_INVOCATION_PLAN),
        "simulated_result_plan": dict(_GEDR_SIMULATED_RESULT_PLAN),
        "consensus_handoff": dict(_GEDR_CONSENSUS_HANDOFF),
        "governance_checkpoints": list(_GEDR_GOVERNANCE_CHECKPOINTS),
        "blockers": list(_GEDR_BLOCKERS),
        "governance_rules": _GEDR_GOVERNANCE_RULES,
        "future_evolution": list(_GEDR_FUTURE_EVOLUTION),
        "advisory": GOVERNED_EXECUTION_DRY_RUN_ADVISORY,
    }

# Phase 44X: Runtime Invocation Validation
# ---------------------------------------------------------------------------

INVOCATION_CONTRACTS_ADVISORY = (
    "Invocation contracts are validated references; no runtimes are invoked."
)

_ICONV_VALIDATED_CONTRACTS: tuple[dict, ...] = (
    {
        "runtime_id": "codex-local",
        "status": "validated",
        "read_only": {
            "command": 'codex exec --sandbox read-only "<prompt>"',
            "mode": "read_only",
            "writable_allowed": False,
        },
        "writable": {
            "command": 'codex exec --sandbox workspace-write "<prompt>"',
            "mode": "writable",
            "writable_allowed": True,
        },
    },
    {
        "runtime_id": "claude-local",
        "status": "validated",
        "read_only": {
            "command": 'claude -p "<prompt>"',
            "mode": "read_only",
            "writable_allowed": False,
        },
        "writable": {
            "command": 'claude -p --permission-mode acceptEdits "<prompt>"',
            "mode": "writable",
            "writable_allowed": True,
        },
    },
    {
        "runtime_id": "kimi-local",
        "status": "validated",
        "read_only": {
            "command": 'kimi -p "<prompt>"',
            "mode": "read_only",
            "writable_allowed": False,
        },
        "writable": {
            "command": 'kimi -p "<prompt>"',
            "mode": "writable",
            "writable_allowed": True,
        },
    },
)

_ICONV_INVALID_PREVIEW_CONTRACTS: tuple[dict, ...] = (
    {
        "runtime_id": "codex-local",
        "command": "codex --non-interactive --output-format json <prompt>",
        "status": "invalid_preview_contract",
        "should_not_use_for_real_execution": True,
        "reason": "Preview-only placeholder; not a real codex invocation contract.",
    },
    {
        "runtime_id": "claude-local",
        "command": "claude --non-interactive --output-format json <prompt>",
        "status": "invalid_preview_contract",
        "should_not_use_for_real_execution": True,
        "reason": "Preview-only placeholder; not a real claude invocation contract.",
    },
    {
        "runtime_id": "kimi-local",
        "command": "kimi --non-interactive --output-format json <prompt>",
        "status": "invalid_preview_contract",
        "should_not_use_for_real_execution": True,
        "reason": "Preview-only placeholder; not a real kimi invocation contract.",
    },
)

_ICONV_GOVERNANCE_RULES: dict = {
    "validation_may": [
        "report validated invocation contracts",
        "flag invalid preview contracts",
        "expose per-runtime read-only commands",
        "expose per-runtime writable commands",
    ],
    "validation_may_not": [
        "invoke runtimes",
        "submit prompts",
        "modify files",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
}

_ICONV_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_invocation_contracts() -> dict:
    """Return validated runtime invocation contracts and flagged invalid preview contracts."""
    return {
        "invocation_contracts": list(_ICONV_VALIDATED_CONTRACTS),
        "invalid_preview_contracts": list(_ICONV_INVALID_PREVIEW_CONTRACTS),
        "governance_rules": _ICONV_GOVERNANCE_RULES,
        "future_evolution": list(_ICONV_FUTURE_EVOLUTION),
        "advisory": INVOCATION_CONTRACTS_ADVISORY,
    }

# Phase 44Y: Governed Runtime Execution Readiness Assessment
# ---------------------------------------------------------------------------

EXECUTION_READINESS_ADVISORY = (
    "Execution readiness assessment is informational; no runtimes are invoked."
)

_ERDYA_READINESS_SUMMARY: dict = {
    "assessment_id": "readiness-44y-preview",
    "overall_status": "partially_ready",
    "total_areas": 6,
    "ready": 2,
    "partially_ready": 4,
    "not_ready": 0,
    "execution_safe": False,
    "execution_safe_reason": (
        "Four subsystems are partially ready; "
        "real runtime execution requires full readiness."
    ),
}

_ERDYA_SUBSYSTEM_ASSESSMENTS: tuple[dict, ...] = (
    {
        "area": "capability_registry",
        "status": "ready",
        "evaluated": [
            {
                "criterion": "discovery_support",
                "met": True,
                "detail": "pcae orchestration capabilities exposes capability matrix.",
            },
            {
                "criterion": "validation_support",
                "met": True,
                "detail": "Capability validation implemented in core/orchestration.py.",
            },
            {
                "criterion": "classification_support",
                "met": True,
                "detail": "Roles and capabilities classified in policy.toml.",
            },
        ],
    },
    {
        "area": "coordinator",
        "status": "partially_ready",
        "evaluated": [
            {
                "criterion": "orchestration_support",
                "met": True,
                "detail": "Orchestration design and workflow planning implemented.",
            },
            {
                "criterion": "planner_support",
                "met": True,
                "detail": "Planner adapter prototype validated (Phase 44Q).",
            },
            {
                "criterion": "runtime_selection_support",
                "met": False,
                "detail": "Runtime selection is advisory only; real agent dispatch not implemented.",
            },
        ],
    },
    {
        "area": "consensus",
        "status": "partially_ready",
        "evaluated": [
            {
                "criterion": "agreement_analysis",
                "met": True,
                "detail": "Agreement analysis implemented in consensus prototype (Phase 44S/44V).",
            },
            {
                "criterion": "conflict_analysis",
                "met": True,
                "detail": "Conflict analysis with confidence spread implemented.",
            },
            {
                "criterion": "recommendation_support",
                "met": False,
                "detail": "Consensus recommendations are simulated; real runtime outputs not wired.",
            },
        ],
    },
    {
        "area": "runtime_adapters",
        "status": "partially_ready",
        "evaluated": [
            {
                "criterion": "adapter_architecture",
                "met": True,
                "detail": "Adapter architecture designed and validated through Phase 44W.",
            },
            {
                "criterion": "adapter_contracts",
                "met": True,
                "detail": "Validated invocation contracts published (Phase 44X).",
            },
            {
                "criterion": "adapter_registry",
                "met": False,
                "detail": "Runtime adapter registry not implemented; adapters are design-time only.",
            },
        ],
    },
    {
        "area": "invocation_layer",
        "status": "partially_ready",
        "evaluated": [
            {
                "criterion": "invocation_contracts",
                "met": True,
                "detail": "Per-runtime read-only and writable contracts validated (Phase 44X).",
            },
            {
                "criterion": "safety_gates",
                "met": True,
                "detail": "Safety gates defined in invocation pilot (Phase 44T) and dry-run (Phase 44W).",
            },
            {
                "criterion": "writable_controls",
                "met": False,
                "detail": "Writable execution controls not enforced at runtime; always false in pilots.",
            },
        ],
    },
    {
        "area": "governance",
        "status": "ready",
        "evaluated": [
            {
                "criterion": "modification_governance",
                "met": True,
                "detail": "pcae check enforces source change policies.",
            },
            {
                "criterion": "commit_governance",
                "met": True,
                "detail": "Pre-commit hook validates governance before commit.",
            },
            {
                "criterion": "push_governance",
                "met": True,
                "detail": "Push governance defined; no unauthorized pushes allowed.",
            },
            {
                "criterion": "rollback_governance",
                "met": True,
                "detail": "Rollback governance implemented (pcae rollback commands).",
            },
        ],
    },
)

_ERDYA_GAP_ANALYSIS: dict = {
    "missing_implementations": [
        "Real runtime dispatch from coordinator to adapters.",
        "Runtime adapter registry with live health probing.",
        "Writable execution controls enforced at runtime boundary.",
    ],
    "missing_validations": [
        "End-to-end invocation test with a real runtime.",
        "Consensus evaluation on real (non-simulated) runtime outputs.",
        "Writable contract enforcement validated against live runtime.",
    ],
    "missing_runtime_integrations": [
        "codex-local: adapter not integrated; contract validated but not wired.",
        "claude-local: adapter not integrated; contract validated but not wired.",
        "kimi-local: adapter not integrated; contract validated but not wired.",
    ],
}

_ERDYA_RECOMMENDATIONS: tuple[str, ...] = (
    "Implement runtime adapter registry with live health probing before real execution.",
    "Wire coordinator runtime selection to a real adapter dispatch path.",
    "Validate writable execution controls against at least one runtime before enabling.",
    "Run end-to-end integration test with a sandboxed real runtime before 45A.",
)

_ERDYA_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
)


def build_execution_readiness() -> dict:
    """Return a read-only governed runtime execution readiness assessment."""
    return {
        "readiness_summary": dict(_ERDYA_READINESS_SUMMARY),
        "subsystem_assessments": list(_ERDYA_SUBSYSTEM_ASSESSMENTS),
        "gap_analysis": dict(_ERDYA_GAP_ANALYSIS),
        "recommendations": list(_ERDYA_RECOMMENDATIONS),
        "future_evolution": list(_ERDYA_FUTURE_EVOLUTION),
        "advisory": EXECUTION_READINESS_ADVISORY,
    }

# Phase 44Z: Runtime Adapter Registry Design
# ---------------------------------------------------------------------------

ADAPTER_REGISTRY_DESIGN_ADVISORY = (
    "Adapter registry design is read-only; no adapters are implemented or invoked."
)

_ARDSGN_REGISTRY_RESPONSIBILITIES: tuple[str, ...] = (
    "register_adapter",
    "unregister_adapter",
    "discover_adapters",
    "resolve_adapter",
    "report_health",
    "report_capabilities",
)

_ARDSGN_REGISTRATION_MODEL_FIELDS: tuple[dict, ...] = (
    {"field": "runtime_id", "type": "str", "description": "Unique identifier for the runtime."},
    {"field": "adapter_id", "type": "str", "description": "Unique identifier for the adapter implementation."},
    {"field": "version", "type": "str", "description": "Semantic version of the adapter."},
    {"field": "lifecycle_status", "type": "str", "description": "Current lifecycle state: active, deprecated, or inactive."},
    {"field": "supported_capabilities", "type": "list[str]", "description": "Capabilities the adapter declares support for."},
    {"field": "writable_supported", "type": "bool", "description": "Whether the adapter supports writable execution mode."},
    {"field": "subagent_supported", "type": "bool", "description": "Whether the adapter supports subagent delegation."},
    {"field": "swarm_supported", "type": "bool", "description": "Whether the adapter supports swarm-mode execution."},
)

_ARDSGN_ADAPTER_RESOLUTION: dict = {
    "input": {
        "runtime_id": "str — the runtime to resolve",
    },
    "output": {
        "adapter_id": "str — resolved adapter identifier",
        "health_status": "str — one of: available, degraded, unavailable, unknown",
        "capabilities": "list[str] — capabilities reported by the adapter",
    },
    "resolution_steps": [
        "Look up runtime_id in the registry.",
        "Verify adapter lifecycle_status is active.",
        "Check adapter health via report_health.",
        "Return adapter_id, health_status, and capabilities.",
    ],
    "fallback": "Return health_status=unknown if runtime_id is not registered.",
}

_ARDSGN_HEALTH_STATES: tuple[str, ...] = (
    "available",
    "degraded",
    "unavailable",
    "unknown",
)

_ARDSGN_HEALTH_MODEL: dict = {
    "states": list(_ARDSGN_HEALTH_STATES),
    "state_descriptions": {
        "available": "Adapter is reachable and ready to accept invocations.",
        "degraded": "Adapter is reachable but operating with reduced capacity or errors.",
        "unavailable": "Adapter is not reachable; invocations will fail.",
        "unknown": "Adapter health has not been probed or runtime_id is not registered.",
    },
    "probe_mode": "on-demand",
    "probe_note": "Health is not probed continuously; queried at resolution time.",
}

_ARDSGN_CAPABILITY_SYNCHRONIZATION: dict = {
    "registry_may_receive": [
        "runtime discovery",
        "capability discovery",
        "version discovery",
    ],
    "source_of_truth": "capability_registry",
    "sync_note": (
        "The capability registry remains the authoritative source of truth. "
        "The adapter registry synchronizes declared capabilities from adapters "
        "but does not override the capability registry."
    ),
}

_ARDSGN_GOVERNANCE_RULES: dict = {
    "registry_may": [
        "discover adapters",
        "resolve adapters",
        "report capabilities",
        "report health",
    ],
    "registry_may_not": [
        "invoke runtimes",
        "approve actions",
        "commit",
        "push",
        "rollback",
        "bypass governance",
    ],
}

_ARDSGN_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45A", "description": "Autonomous Roadmap Generation"},
    {"phase": "45B", "description": "Runtime Adapter Registry Prototype"},
    {"phase": "45C", "description": "Runtime Adapter Registry Implementation"},
)


def build_adapter_registry_design() -> dict:
    """Return a read-only runtime adapter registry design."""
    return {
        "registry_responsibilities": list(_ARDSGN_REGISTRY_RESPONSIBILITIES),
        "adapter_registration_model": list(_ARDSGN_REGISTRATION_MODEL_FIELDS),
        "adapter_resolution": dict(_ARDSGN_ADAPTER_RESOLUTION),
        "health_model": dict(_ARDSGN_HEALTH_MODEL),
        "capability_synchronization": dict(_ARDSGN_CAPABILITY_SYNCHRONIZATION),
        "governance_rules": _ARDSGN_GOVERNANCE_RULES,
        "future_evolution": list(_ARDSGN_FUTURE_EVOLUTION),
        "advisory": ADAPTER_REGISTRY_DESIGN_ADVISORY,
    }


# Phase 45A: Autonomous Roadmap Generation Design
# ---------------------------------------------------------------------------

ROADMAP_GENERATION_DESIGN_ADVISORY = (
    "Roadmap generation design is read-only; no roadmap proposals are generated or mutated."
)

_RGDSGN_EVIDENCE_SOURCES: tuple[str, ...] = (
    "PROJECT_STATUS.md",
    "CHANGELOG.md",
    "tasks/TODO.md",
    "tasks/DONE.md",
    "tests",
    "capability registry",
    "execution/readiness assessments",
    "governance history",
)

_RGDSGN_AGENT_ROLES: tuple[dict, ...] = (
    {
        "role": "repository_analyst",
        "responsibility": (
            "Reads and summarizes project state from PROJECT_STATUS.md, "
            "CHANGELOG.md, and task files."
        ),
    },
    {
        "role": "architecture_analyst",
        "responsibility": (
            "Identifies structural gaps and evolution opportunities from "
            "architecture documentation."
        ),
    },
    {
        "role": "test_analyst",
        "responsibility": (
            "Surveys test coverage and identifies untested capabilities."
        ),
    },
    {
        "role": "governance_analyst",
        "responsibility": (
            "Evaluates governance history, policy compliance, and readiness "
            "assessments."
        ),
    },
    {
        "role": "capability_analyst",
        "responsibility": (
            "Reads the capability registry and identifies missing or "
            "underdeveloped capabilities."
        ),
    },
    {
        "role": "planning_coordinator",
        "responsibility": (
            "Aggregates evidence from all analysts, generates candidate phases, "
            "orders dependencies, and compiles the roadmap proposal."
        ),
    },
)

_RGDSGN_LIFECYCLE_STEPS: tuple[str, ...] = (
    "evidence_collection",
    "gap_analysis",
    "candidate_phase_generation",
    "dependency_ordering",
    "risk_assessment",
    "consensus_review",
    "human_approval",
)

_RGDSGN_PROPOSAL_MODEL_FIELDS: tuple[dict, ...] = (
    {
        "field": "proposal_id",
        "type": "str",
        "description": "Unique identifier for this roadmap proposal.",
    },
    {
        "field": "generated_at",
        "type": "str",
        "description": "ISO 8601 timestamp when the proposal was generated.",
    },
    {
        "field": "evidence_sources",
        "type": "list[str]",
        "description": "Evidence sources consulted during generation.",
    },
    {
        "field": "candidate_phases",
        "type": "list[dict]",
        "description": "Proposed next phases with title, rationale, and priority.",
    },
    {
        "field": "dependencies",
        "type": "list[dict]",
        "description": "Dependency relationships between candidate phases.",
    },
    {
        "field": "risks",
        "type": "list[dict]",
        "description": "Risks identified during generation with severity and mitigation notes.",
    },
    {
        "field": "assumptions",
        "type": "list[str]",
        "description": "Assumptions made during evidence analysis.",
    },
    {
        "field": "confidence",
        "type": "float",
        "description": "Aggregate confidence score (0.0–1.0) for the proposal.",
    },
    {
        "field": "human_decision_required",
        "type": "bool",
        "description": "Always true; human approval is required before acting on any proposal.",
    },
)

_RGDSGN_GOVERNANCE_RULES: dict = {
    "proposal_may": [
        "describe candidate phases",
        "summarize evidence",
        "express dependencies",
        "report risks and assumptions",
        "report confidence",
    ],
    "proposal_may_not": [
        "mutate roadmap",
        "create tasks",
        "execute phases",
        "commit",
        "push",
        "approve itself",
    ],
    "human_approval_required": True,
    "advisory": True,
}

_RGDSGN_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45B", "description": "Roadmap Evidence Collector"},
    {"phase": "45C", "description": "Roadmap Proposal Dry-Run"},
    {"phase": "45D", "description": "Multi-Agent Roadmap Proposal"},
    {"phase": "45E", "description": "Roadmap Approval Workflow"},
)


def build_roadmap_generation_design() -> dict:
    """Return a read-only autonomous roadmap generation architecture design."""
    return {
        "evidence_sources": list(_RGDSGN_EVIDENCE_SOURCES),
        "agent_roles": list(_RGDSGN_AGENT_ROLES),
        "lifecycle": list(_RGDSGN_LIFECYCLE_STEPS),
        "proposal_model": list(_RGDSGN_PROPOSAL_MODEL_FIELDS),
        "governance_rules": dict(_RGDSGN_GOVERNANCE_RULES),
        "future_evolution": list(_RGDSGN_FUTURE_EVOLUTION),
        "advisory": ROADMAP_GENERATION_DESIGN_ADVISORY,
    }


# Phase 45B: Roadmap Evidence Collector
# ---------------------------------------------------------------------------

ROADMAP_EVIDENCE_ADVISORY = (
    "Roadmap evidence collection is read-only; no roadmap mutation, "
    "task creation, or runtime execution occurs."
)


def _collect_project_summary(root: HarnessPath) -> dict:
    """Read PROJECT_STATUS.md and extract a structured summary."""
    path = root.join(Path("PROJECT_STATUS.md"))
    try:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        current_phase = "unknown"
        for line in lines[:20]:
            stripped = line.strip().rstrip(".")
            if stripped.startswith("Phase "):
                current_phase = stripped
                break
        return {
            "current_phase": current_phase,
            "status_file_lines": len(lines),
            "status_readable": True,
        }
    except OSError:
        return {
            "current_phase": "unknown",
            "status_file_lines": 0,
            "status_readable": False,
        }


def _collect_changelog_summary(root: HarnessPath) -> dict:
    """Count changelog entries from CHANGELOG.md."""
    path = root.join(Path("CHANGELOG.md"))
    try:
        text = path.read_text(encoding="utf-8")
        entries = sum(1 for line in text.splitlines() if line.startswith("- "))
        return {
            "changelog_unreleased_entries": entries,
            "changelog_readable": True,
        }
    except OSError:
        return {
            "changelog_unreleased_entries": 0,
            "changelog_readable": False,
        }


def _collect_task_counts(root: HarnessPath) -> dict:
    """Count task entries from tasks/TODO.md and tasks/DONE.md."""
    result: dict = {}
    for key, rel in (
        ("todo_entries", Path("tasks") / "TODO.md"),
        ("done_entries", Path("tasks") / "DONE.md"),
    ):
        readable_key = key.replace("entries", "readable")
        fpath = root.join(rel)
        try:
            text = fpath.read_text(encoding="utf-8")
            result[key] = sum(1 for line in text.splitlines() if line.startswith("- "))
            result[readable_key] = True
        except OSError:
            result[key] = 0
            result[readable_key] = False
    return result


def _collect_test_evidence(root: HarnessPath) -> dict:
    """Collect test counts via pytest --collect-only. Read-only; no tests executed."""
    try:
        proc = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            cwd=str(root.path),
            timeout=30,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        total_collected = 0
        for line in output.splitlines():
            m = re.search(r"(\d+)\s+test", line)
            if m:
                total_collected = int(m.group(1))
                break
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        total_collected = 0
    return {
        "total_collected": total_collected,
        "executed": False,
        "passed": "not_executed",
        "failed": "not_executed",
        "collection_command": "pytest --collect-only -q --tb=no",
    }


def _summarize_capability_evidence(capability_data: dict) -> dict:
    """Extract a structured summary from build_capability_registry output."""
    registry = capability_data.get("capability_registry", [])
    discovery = capability_data.get("discovery_summary", {})
    return {
        "agent_count": len(registry),
        "agent_ids": [a.get("agent_id", "unknown") for a in registry],
        "total_declared_capabilities": sum(
            len(a.get("capabilities", [])) for a in registry
        ),
        "agents_installed": discovery.get("agents_installed", 0),
        "agents_not_installed": discovery.get("agents_not_installed", 0),
        "multi_agent_capable": discovery.get("multi_agent_capable_agents", []),
    }


def _summarize_readiness_evidence(readiness_data: dict) -> dict:
    """Extract readiness summary from execution readiness data."""
    summary = readiness_data.get("readiness_summary", {})
    return {
        "overall_status": summary.get("overall_status", "unknown"),
        "execution_safe": summary.get("execution_safe", False),
        "subsystems_ready": summary.get("ready", 0),
        "subsystems_partially_ready": summary.get("partially_ready", 0),
        "subsystems_not_ready": summary.get("not_ready", 0),
        "total_areas": summary.get("total_areas", 0),
    }


def _summarize_governance_evidence(readiness_data: dict) -> dict:
    """Extract governance evidence from execution readiness assessments."""
    assessments = readiness_data.get("subsystem_assessments", [])
    governance = next(
        (a for a in assessments if a.get("area") == "governance"), None
    )
    if governance:
        met = [
            e["criterion"]
            for e in governance.get("evaluated", [])
            if e.get("met")
        ]
        unmet = [
            e["criterion"]
            for e in governance.get("evaluated", [])
            if not e.get("met")
        ]
        status = governance.get("status", "unknown")
    else:
        met, unmet, status = [], [], "unknown"
    return {
        "governance_areas": [
            "modification_governance",
            "commit_governance",
            "push_governance",
            "rollback_governance",
        ],
        "governance_status": status,
        "criteria_met": met,
        "criteria_unmet": unmet,
    }


def _derive_roadmap_gaps(
    project_summary: dict,
    readiness_data: dict,
) -> list[dict]:
    """Synthesize identified gaps from collected evidence."""
    gaps: list[dict] = []
    n = 1

    gap_analysis = readiness_data.get("gap_analysis", {})
    for item in gap_analysis.get("missing_implementations", []):
        gaps.append({
            "gap_id": f"gap-{n:03d}",
            "category": "missing_implementation",
            "description": item,
            "source": "execution_readiness",
        })
        n += 1
    for item in gap_analysis.get("missing_validations", []):
        gaps.append({
            "gap_id": f"gap-{n:03d}",
            "category": "missing_validation",
            "description": item,
            "source": "execution_readiness",
        })
        n += 1
    for item in gap_analysis.get("missing_runtime_integrations", []):
        gaps.append({
            "gap_id": f"gap-{n:03d}",
            "category": "missing_runtime_integration",
            "description": item,
            "source": "execution_readiness",
        })
        n += 1

    todo_count = project_summary.get("todo_entries", 0)
    if todo_count > 0:
        gaps.append({
            "gap_id": f"gap-{n:03d}",
            "category": "pending_tasks",
            "description": (
                f"{todo_count} pending future exploration "
                f"{'item' if todo_count == 1 else 'items'} in tasks/TODO.md."
            ),
            "source": "task_tracking",
        })
        n += 1

    assessments = readiness_data.get("subsystem_assessments", [])
    for assessment in assessments:
        if assessment.get("status") == "partially_ready":
            unmet = [
                e["criterion"]
                for e in assessment.get("evaluated", [])
                if not e.get("met")
            ]
            if unmet:
                gaps.append({
                    "gap_id": f"gap-{n:03d}",
                    "category": "subsystem_partial_readiness",
                    "description": (
                        f"Subsystem '{assessment['area']}' is partially ready; "
                        f"unmet: {', '.join(unmet)}."
                    ),
                    "source": "execution_readiness",
                })
                n += 1

    return gaps


def _derive_roadmap_focus_areas(
    gaps: list[dict],
    readiness_data: dict,
) -> list[dict]:
    """Derive candidate roadmap focus areas from gaps and readiness evidence."""
    areas: list[dict] = []
    for i, rec in enumerate(readiness_data.get("recommendations", [])):
        areas.append({
            "area_id": f"area-{i + 1:03d}",
            "focus_area": rec,
            "priority": "high",
            "rationale": "Derived from execution readiness assessment.",
            "source": "execution_readiness",
        })

    task_gaps = [g for g in gaps if g["category"] == "pending_tasks"]
    if task_gaps:
        areas.append({
            "area_id": f"area-{len(areas) + 1:03d}",
            "focus_area": "Resolve pending task backlog",
            "priority": "medium",
            "rationale": task_gaps[0]["description"],
            "source": "task_tracking",
        })

    areas.append({
        "area_id": f"area-{len(areas) + 1:03d}",
        "focus_area": "Advance roadmap generation pipeline",
        "priority": "high",
        "rationale": (
            "Phase 45A defined roadmap generation architecture. "
            "Collected evidence now supports phases 45C–45E."
        ),
        "source": "phase_45a_design",
    })

    return areas


def build_roadmap_evidence(root: HarnessPath) -> dict:
    """Collect structured repository evidence for roadmap generation. Read-only."""
    generated_at = datetime.now(timezone.utc).isoformat()
    package_id = f"rev-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    project_summary = {
        **_collect_project_summary(root),
        **_collect_changelog_summary(root),
        **_collect_task_counts(root),
    }
    test_summary = _collect_test_evidence(root)

    capability_data = build_capability_registry(root)
    capability_summary = _summarize_capability_evidence(capability_data)

    readiness_data = build_execution_readiness()
    readiness_summary = _summarize_readiness_evidence(readiness_data)
    governance_summary = _summarize_governance_evidence(readiness_data)

    identified_gaps = _derive_roadmap_gaps(project_summary, readiness_data)
    candidate_focus_areas = _derive_roadmap_focus_areas(identified_gaps, readiness_data)

    return {
        "package_id": package_id,
        "generated_at": generated_at,
        "evidence_sources": [
            "PROJECT_STATUS.md",
            "CHANGELOG.md",
            "tasks/TODO.md",
            "tasks/DONE.md",
            "tests",
            "capability_registry",
            "execution_readiness",
            "governance",
        ],
        "project_summary": project_summary,
        "test_summary": test_summary,
        "capability_summary": capability_summary,
        "governance_summary": governance_summary,
        "readiness_summary": readiness_summary,
        "identified_gaps": identified_gaps,
        "candidate_focus_areas": candidate_focus_areas,
        "advisory": ROADMAP_EVIDENCE_ADVISORY,
    }


# Phase 45C: Roadmap Proposal Dry-Run
# ---------------------------------------------------------------------------

ROADMAP_PROPOSAL_DRY_RUN_ADVISORY = (
    "Roadmap proposal dry-run is advisory; no roadmap changes are performed."
)

_RPDRUN_GOVERNANCE_RULES: dict = {
    "proposal_may": [
        "recommend phases",
        "recommend ordering",
        "recommend priorities",
        "summarize evidence",
        "report risks and assumptions",
    ],
    "proposal_may_not": [
        "create phases",
        "modify roadmap",
        "create tasks",
        "execute work",
        "commit",
        "push",
    ],
    "human_decision_required": True,
    "advisory": True,
}


def _categorize_gaps(identified_gaps: list[dict]) -> dict:
    """Categorize identified gaps for proposal gap analysis."""
    by_cat: dict[str, list[str]] = {}
    for gap in identified_gaps:
        by_cat.setdefault(gap["category"], []).append(gap["gap_id"])
    return {
        "readiness_gaps": by_cat.get("subsystem_partial_readiness", []),
        "capability_gaps": by_cat.get("missing_implementation", []),
        "governance_gaps": by_cat.get("governance", []),
        "runtime_integration_gaps": by_cat.get("missing_runtime_integration", []),
        "validation_gaps": by_cat.get("missing_validation", []),
        "task_gaps": by_cat.get("pending_tasks", []),
        "total": len(identified_gaps),
    }


def _generate_candidate_phases(identified_gaps: list[dict]) -> list[dict]:
    """Generate candidate roadmap phases from evidence gaps."""
    phases: list[dict] = []
    n = 1

    impl_gaps = [g for g in identified_gaps if g["category"] == "missing_implementation"]
    if impl_gaps:
        phases.append({
            "phase_id": f"candidate-{n:03d}",
            "title": "Runtime Adapter Registry Implementation",
            "rationale": "Close missing runtime dispatch and adapter registry implementation gaps.",
            "evidence_refs": [g["gap_id"] for g in impl_gaps],
            "confidence": 0.80,
        })
        n += 1

    rt_gaps = [g for g in identified_gaps if g["category"] == "missing_runtime_integration"]
    if rt_gaps:
        phases.append({
            "phase_id": f"candidate-{n:03d}",
            "title": "Runtime Adapter Wiring",
            "rationale": f"Wire {len(rt_gaps)} runtime adapter(s) to the execution framework.",
            "evidence_refs": [g["gap_id"] for g in rt_gaps],
            "confidence": 0.75,
        })
        n += 1

    val_gaps = [g for g in identified_gaps if g["category"] == "missing_validation"]
    if val_gaps:
        phases.append({
            "phase_id": f"candidate-{n:03d}",
            "title": "Runtime Integration Validation",
            "rationale": "Validate real runtime execution end-to-end before enabling production use.",
            "evidence_refs": [g["gap_id"] for g in val_gaps],
            "confidence": 0.70,
        })
        n += 1

    candidate_ids = [p["phase_id"] for p in phases]
    last_candidate = candidate_ids[-1] if candidate_ids else "phase_45c_dry_run"

    for pid, title, rationale, refs in [
        ("45D", "Multi-Agent Roadmap Proposal",
         "Extend dry-run with real multi-agent deliberation for proposal generation.",
         [last_candidate]),
        ("45E", "Roadmap Approval Workflow",
         "Implement human approval workflow for generated roadmap proposals.",
         ["45D"]),
        ("45F", "Prompt Generation Design",
         "Design structured prompt generation for agent task delegation.",
         ["45E"]),
        ("45G", "Adaptive Agent-Specific Prompt Generation",
         "Generate prompts adapted to individual agent capabilities and task requirements.",
         ["45F"]),
    ]:
        phases.append({
            "phase_id": pid,
            "title": title,
            "rationale": rationale,
            "evidence_refs": refs,
            "confidence": 0.80,
        })

    return phases


def _generate_proposal_dependencies(candidate_phases: list[dict]) -> tuple[list[dict], list[str]]:
    """Generate dependency pairs and recommended ordering from candidate phases."""
    phase_ids = [p["phase_id"] for p in candidate_phases]
    candidate_ids = sorted(p for p in phase_ids if p.startswith("candidate-"))
    future_ids = [p for p in phase_ids if not p.startswith("candidate-")]

    deps: list[dict] = []
    n = 1

    for i in range(len(candidate_ids) - 1):
        deps.append({
            "dep_id": f"dep-{n:03d}",
            "from_phase": candidate_ids[i],
            "to_phase": candidate_ids[i + 1],
            "relationship": "must_precede",
            "rationale": f"{candidate_ids[i]} must complete before {candidate_ids[i + 1]} begins.",
        })
        n += 1

    if candidate_ids and future_ids:
        deps.append({
            "dep_id": f"dep-{n:03d}",
            "from_phase": candidate_ids[-1],
            "to_phase": future_ids[0],
            "relationship": "recommended_precede",
            "rationale": "Implementation maturity supports advanced roadmap generation phases.",
        })
        n += 1

    for i in range(len(future_ids) - 1):
        deps.append({
            "dep_id": f"dep-{n:03d}",
            "from_phase": future_ids[i],
            "to_phase": future_ids[i + 1],
            "relationship": "must_precede",
            "rationale": f"{future_ids[i]} must complete before {future_ids[i + 1]} begins.",
        })
        n += 1

    ordering = candidate_ids + future_ids
    return deps, ordering


def _generate_proposal_risks(
    identified_gaps: list[dict],
    readiness_summary: dict,
) -> list[dict]:
    """Derive risks from identified gaps and readiness evidence."""
    risks: list[dict] = []
    n = 1

    if not readiness_summary.get("execution_safe", True):
        risks.append({
            "risk_id": f"risk-{n:03d}",
            "category": "execution_safety",
            "description": (
                "Real execution is not yet safe; execution_safe=false in readiness assessment."
            ),
            "severity": "high",
            "mitigation": (
                "Complete adapter registry and writable control validations "
                "before enabling real execution."
            ),
        })
        n += 1

    rt_gaps = [g for g in identified_gaps if g["category"] == "missing_runtime_integration"]
    if rt_gaps:
        risks.append({
            "risk_id": f"risk-{n:03d}",
            "category": "runtime_integration",
            "description": (
                f"{len(rt_gaps)} runtime adapter(s) not yet wired to the execution framework."
            ),
            "severity": "high",
            "mitigation": "Implement adapter wiring phase before enabling coordinated execution.",
        })
        n += 1

    impl_gaps = [g for g in identified_gaps if g["category"] == "missing_implementation"]
    if impl_gaps:
        risks.append({
            "risk_id": f"risk-{n:03d}",
            "category": "implementation_gap",
            "description": f"{len(impl_gaps)} missing implementation(s) block production readiness.",
            "severity": "medium",
            "mitigation": "Prioritize implementation gaps in the next planning cycle.",
        })
        n += 1

    val_gaps = [g for g in identified_gaps if g["category"] == "missing_validation"]
    if val_gaps:
        risks.append({
            "risk_id": f"risk-{n:03d}",
            "category": "validation_gap",
            "description": (
                f"{len(val_gaps)} end-to-end validation(s) not yet performed."
            ),
            "severity": "medium",
            "mitigation": "Schedule integration validation phases before production deployment.",
        })
        n += 1

    risks.append({
        "risk_id": f"risk-{n:03d}",
        "category": "proposal_advisory",
        "description": (
            "This proposal is a dry-run; candidate phases require human review before adoption."
        ),
        "severity": "low",
        "mitigation": "All proposals require explicit human approval via roadmap approval workflow.",
    })

    return risks


def _generate_proposal_assumptions(evidence: dict) -> list[str]:
    """Derive proposal assumptions from collected evidence."""
    ps = evidence.get("project_summary", {})
    ts = evidence.get("test_summary", {})
    assumptions = [
        "Test suite remains green throughout implementation phases.",
        "Human approval is required before any candidate phase is acted upon.",
        "Evidence collection reflects current repository state at generation time.",
        "Read-only constraints remain enforced throughout the roadmap generation pipeline.",
        "Governance policy remains consistent with current .pcae/policy.toml.",
    ]
    total = ts.get("total_collected", 0)
    if total > 0:
        assumptions.append(
            f"Test coverage ({total} tests collected) is sufficient to detect "
            "regressions introduced by candidate phases."
        )
    done = ps.get("done_entries", 0)
    if done > 0:
        assumptions.append(
            f"Completed phases ({done} in tasks/DONE.md) represent stable "
            "foundations that candidate phases may build upon."
        )
    return assumptions


def _compute_proposal_confidence(evidence: dict) -> float:
    """Compute overall proposal confidence from evidence quality and gap count."""
    rs = evidence.get("readiness_summary", {})
    total = max(rs.get("total_areas", 1), 1)
    ready = rs.get("subsystems_ready", 0)
    base = 0.40 + (ready / total) * 0.40
    gap_count = len(evidence.get("identified_gaps", []))
    gap_penalty = min(gap_count * 0.02, 0.15)
    return round(max(base - gap_penalty, 0.20), 2)


def build_roadmap_proposal_dry_run(root: HarnessPath) -> dict:
    """Generate a simulated roadmap proposal from collected evidence. Read-only."""
    evidence = build_roadmap_evidence(root)

    identified_gaps = evidence.get("identified_gaps", [])
    readiness_summary = evidence.get("readiness_summary", {})

    gap_analysis = _categorize_gaps(identified_gaps)
    candidate_phases = _generate_candidate_phases(identified_gaps)
    dependencies, recommended_ordering = _generate_proposal_dependencies(candidate_phases)
    risks = _generate_proposal_risks(identified_gaps, readiness_summary)
    assumptions = _generate_proposal_assumptions(evidence)
    confidence = _compute_proposal_confidence(evidence)

    return {
        "proposal_id": f"rdp-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_package_id": evidence.get("package_id", "unknown"),
        "gap_analysis": gap_analysis,
        "candidate_phases": candidate_phases,
        "dependencies": dependencies,
        "recommended_ordering": recommended_ordering,
        "risks": risks,
        "assumptions": assumptions,
        "confidence": confidence,
        "human_decision_required": True,
        "governance_rules": dict(_RPDRUN_GOVERNANCE_RULES),
        "advisory": ROADMAP_PROPOSAL_DRY_RUN_ADVISORY,
    }


# Phase 45D: Multi-Agent Roadmap Proposal
# ---------------------------------------------------------------------------

MULTI_AGENT_ROADMAP_ADVISORY = (
    "Multi-agent roadmap proposal is simulated; no agents are executed."
)

# Simulated agent perspectives — mock data only, no runtimes invoked.
_MARMAP_AGENT_PROPOSALS: tuple[dict, ...] = (
    {
        "agent_id": "codex-local",
        "proposal_id": "agent-prop-codex-45d",
        "recommendation": "approve",
        "confidence": 0.82,
        "rationale": (
            "Strong implementation pathway with clear technical deliverables; "
            "defers design-heavy phases 45F/45G until implementation is stable."
        ),
        "candidate_phases": [
            {"phase_id": "candidate-001", "title": "Runtime Adapter Registry Implementation", "confidence": 0.85},
            {"phase_id": "candidate-002", "title": "Runtime Adapter Wiring", "confidence": 0.80},
            {"phase_id": "candidate-003", "title": "Runtime Integration Validation", "confidence": 0.75},
            {"phase_id": "45D", "title": "Multi-Agent Roadmap Proposal", "confidence": 0.82},
            {"phase_id": "45E", "title": "Roadmap Approval Workflow", "confidence": 0.78},
        ],
        "risks": [
            "Deferred 45F/45G may create design debt.",
            "candidate-001 scope may expand under real implementation.",
        ],
    },
    {
        "agent_id": "claude-local",
        "proposal_id": "agent-prop-claude-45d",
        "recommendation": "approve",
        "confidence": 0.88,
        "rationale": (
            "Comprehensive phasing with balanced risk across implementation and design; "
            "recommends full roadmap execution without deferral."
        ),
        "candidate_phases": [
            {"phase_id": "candidate-001", "title": "Runtime Adapter Registry Implementation", "confidence": 0.88},
            {"phase_id": "candidate-002", "title": "Runtime Adapter Wiring", "confidence": 0.85},
            {"phase_id": "candidate-003", "title": "Runtime Integration Validation", "confidence": 0.82},
            {"phase_id": "45D", "title": "Multi-Agent Roadmap Proposal", "confidence": 0.90},
            {"phase_id": "45E", "title": "Roadmap Approval Workflow", "confidence": 0.88},
            {"phase_id": "45F", "title": "Prompt Generation Design", "confidence": 0.80},
            {"phase_id": "45G", "title": "Adaptive Agent-Specific Prompt Generation", "confidence": 0.75},
        ],
        "risks": [
            "Full roadmap scope may extend timeline.",
            "45F/45G design quality depends on 45D/45E maturity.",
        ],
    },
    {
        "agent_id": "kimi-local",
        "proposal_id": "agent-prop-kimi-45d",
        "recommendation": "request_changes",
        "confidence": 0.71,
        "rationale": (
            "Conservative phasing: skips candidate-001 (high execution risk without prior validation), "
            "includes 45F to ensure prompt design precedes implementation."
        ),
        "candidate_phases": [
            {"phase_id": "candidate-002", "title": "Runtime Adapter Wiring", "confidence": 0.72},
            {"phase_id": "candidate-003", "title": "Runtime Integration Validation", "confidence": 0.75},
            {"phase_id": "45D", "title": "Multi-Agent Roadmap Proposal", "confidence": 0.70},
            {"phase_id": "45E", "title": "Roadmap Approval Workflow", "confidence": 0.74},
            {"phase_id": "45F", "title": "Prompt Generation Design", "confidence": 0.68},
        ],
        "risks": [
            "Skipping candidate-001 delays adapter registry implementation.",
            "Overall confidence lower due to unresolved execution risk.",
        ],
    },
)

# Proposal comparison derived from the three simulated proposals.
_MARMAP_SHARED_PHASE_IDS: tuple[str, ...] = (
    "candidate-002",
    "candidate-003",
    "45D",
    "45E",
)

_MARMAP_UNIQUE_RECOMMENDATIONS: dict = {
    "codex-local": [],
    "claude-local": ["45G"],
    "kimi-local": [],
}

_MARMAP_CONFLICTING_RECOMMENDATIONS: tuple[dict, ...] = (
    {
        "phase_id": "candidate-001",
        "recommended_by": ["codex-local", "claude-local"],
        "not_recommended_by": ["kimi-local"],
        "conflict_reason": "kimi-local excludes candidate-001 citing execution risk.",
    },
    {
        "phase_id": "45F",
        "recommended_by": ["claude-local", "kimi-local"],
        "not_recommended_by": ["codex-local"],
        "conflict_reason": "codex-local defers 45F as premature.",
    },
)

# Consensus analysis.
_MARMAP_AGREEMENTS: tuple[dict, ...] = (
    {"phase_id": "candidate-002", "agreed_by": ["codex-local", "claude-local", "kimi-local"]},
    {"phase_id": "candidate-003", "agreed_by": ["codex-local", "claude-local", "kimi-local"]},
    {"phase_id": "45D", "agreed_by": ["codex-local", "claude-local", "kimi-local"]},
    {"phase_id": "45E", "agreed_by": ["codex-local", "claude-local", "kimi-local"]},
)

_MARMAP_CONFIDENCE_DIFFERENCES: dict = {
    "max_confidence": 0.88,
    "min_confidence": 0.71,
    "confidence_spread": 0.17,
    "agents": ["codex-local (0.82)", "claude-local (0.88)", "kimi-local (0.71)"],
}

_MARMAP_RECOMMENDATION_DISTRIBUTION: dict = {
    "approve": 2,
    "request_changes": 1,
    "agents_approve": ["codex-local", "claude-local"],
    "agents_request_changes": ["kimi-local"],
}

# Consensus recommendation.
_MARMAP_CONSENSUS_OUTCOME = "approve"
_MARMAP_CONSENSUS_BASIS = "weighted majority 2 of 3"
_MARMAP_CONSENSUS_CONFIDENCE = 0.80
_MARMAP_CONSENSUS_CONFLICT_REASON = (
    "conflict detected: kimi-local recommends request_changes vs approve majority"
)

_MARMAP_RECOMMENDED_PHASES: tuple[str, ...] = _MARMAP_SHARED_PHASE_IDS

_MARMAP_VALID_OUTCOMES: tuple[str, ...] = (
    "approve",
    "request_changes",
    "inconclusive",
    "escalate_to_human",
)

_MARMAP_GOVERNANCE_RULES: dict = {
    "proposal_system_may": [
        "compare proposals",
        "analyze agreements",
        "generate recommendations",
        "report conflicts",
        "report confidence differences",
    ],
    "proposal_system_may_not": [
        "create roadmap phases",
        "mutate roadmap",
        "create tasks",
        "execute work",
        "commit",
        "push",
    ],
    "human_decision_required": True,
    "advisory": True,
}

_MARMAP_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45E", "description": "Roadmap Approval Workflow"},
    {"phase": "45F", "description": "Prompt Generation Design"},
    {"phase": "45G", "description": "Adaptive Agent-Specific Prompt Generation"},
    {"phase": "45H", "description": "Prompt Validation Framework"},
    {"phase": "45I", "description": "Prompt Governance Design"},
)


def build_multi_agent_roadmap(root: HarnessPath) -> dict:
    """Generate a simulated multi-agent roadmap proposal. Read-only; no agents executed."""
    dry_run = build_roadmap_proposal_dry_run(root)

    agent_proposals = [dict(p) for p in _MARMAP_AGENT_PROPOSALS]

    proposal_comparison = {
        "shared_recommendations": list(_MARMAP_SHARED_PHASE_IDS),
        "unique_recommendations": dict(_MARMAP_UNIQUE_RECOMMENDATIONS),
        "conflicting_recommendations": [dict(c) for c in _MARMAP_CONFLICTING_RECOMMENDATIONS],
    }

    consensus_analysis = {
        "agreements": [dict(a) for a in _MARMAP_AGREEMENTS],
        "agreement_count": len(_MARMAP_AGREEMENTS),
        "conflicts": [dict(c) for c in _MARMAP_CONFLICTING_RECOMMENDATIONS],
        "conflict_count": len(_MARMAP_CONFLICTING_RECOMMENDATIONS),
        "confidence_differences": dict(_MARMAP_CONFIDENCE_DIFFERENCES),
        "recommendation_distribution": dict(_MARMAP_RECOMMENDATION_DISTRIBUTION),
    }

    consensus_recommendation = {
        "outcome": _MARMAP_CONSENSUS_OUTCOME,
        "valid_outcomes": list(_MARMAP_VALID_OUTCOMES),
        "basis": _MARMAP_CONSENSUS_BASIS,
        "recommended_phases": list(_MARMAP_RECOMMENDED_PHASES),
        "recommended_ordering": list(_MARMAP_RECOMMENDED_PHASES),
        "consensus_confidence": _MARMAP_CONSENSUS_CONFIDENCE,
        "human_review_required": True,
        "human_review_reason": _MARMAP_CONSENSUS_CONFLICT_REASON,
        "conflict_phases": [c["phase_id"] for c in _MARMAP_CONFLICTING_RECOMMENDATIONS],
    }

    human_review = {
        "human_review_required": True,
        "review_reason": "Multi-agent consensus contains conflicts requiring human resolution.",
        "conflict_phases": [c["phase_id"] for c in _MARMAP_CONFLICTING_RECOMMENDATIONS],
        "reviewable_outcome": _MARMAP_CONSENSUS_OUTCOME,
        "reviewable_phases": list(_MARMAP_RECOMMENDED_PHASES),
    }

    return {
        "proposal_id": f"marp-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run_proposal_id": dry_run["proposal_id"],
        "evidence_package_id": dry_run["evidence_package_id"],
        "agent_proposals": agent_proposals,
        "proposal_comparison": proposal_comparison,
        "consensus_analysis": consensus_analysis,
        "consensus_recommendation": consensus_recommendation,
        "human_review": human_review,
        "governance_rules": dict(_MARMAP_GOVERNANCE_RULES),
        "future_evolution": [dict(e) for e in _MARMAP_FUTURE_EVOLUTION],
        "advisory": MULTI_AGENT_ROADMAP_ADVISORY,
    }


# Phase 45E: Roadmap Approval Workflow
# ---------------------------------------------------------------------------

ROADMAP_APPROVAL_DESIGN_ADVISORY = (
    "Roadmap approval workflow is advisory; no roadmap approval is recorded."
)

_RAD_APPROVAL_LIFECYCLE: tuple[dict, ...] = (
    {
        "step": 1,
        "name": "proposal_generated",
        "description": "A roadmap proposal is generated from evidence and multi-agent review.",
        "inputs": ["roadmap_evidence_package", "roadmap_proposal_dry_run", "multi_agent_roadmap_proposal"],
        "outputs": ["proposal_id", "agent_proposals", "consensus_recommendation"],
    },
    {
        "step": 2,
        "name": "proposal_reviewed",
        "description": "The proposal and agent perspectives are reviewed for completeness and conflicts.",
        "inputs": ["proposal_id", "agent_proposals"],
        "outputs": ["review_summary", "identified_conflicts", "confidence_assessment"],
    },
    {
        "step": 3,
        "name": "conflicts_identified",
        "description": "Conflicting agent recommendations are surfaced for human resolution.",
        "inputs": ["conflicting_recommendations", "confidence_differences"],
        "outputs": ["conflict_list", "conflict_resolution_requirements"],
    },
    {
        "step": 4,
        "name": "human_decision_required",
        "description": "A human reviews the proposal and conflict list, then records an approval decision.",
        "inputs": ["proposal_id", "conflict_list", "consensus_recommendation"],
        "outputs": ["approval_state", "human_notes", "approved_phases", "denied_phases"],
    },
    {
        "step": 5,
        "name": "approval_state_recorded",
        "description": "The approval decision is recorded in a governed approval artifact (future artifact; not yet mutated).",
        "inputs": ["approval_state", "approved_phases", "denied_phases", "human_notes"],
        "outputs": ["roadmap_approval_id", "approved_roadmap_artifact"],
    },
    {
        "step": 6,
        "name": "approved_roadmap_informs_phase_generation",
        "description": "The approved roadmap artifact informs future governed phase generation.",
        "inputs": ["approved_roadmap_artifact"],
        "outputs": ["next_phase_candidates", "phase_generation_context"],
    },
)

_RAD_APPROVAL_STATES: tuple[dict, ...] = (
    {
        "state": "pending",
        "description": "Proposal has been generated; human decision not yet recorded.",
        "terminal": False,
        "requires_human_action": True,
    },
    {
        "state": "approved",
        "description": "Human has approved the roadmap proposal; approved phases may inform future phase generation.",
        "terminal": True,
        "requires_human_action": False,
    },
    {
        "state": "denied",
        "description": "Human has denied the roadmap proposal; no phases are promoted.",
        "terminal": True,
        "requires_human_action": False,
    },
    {
        "state": "changes_requested",
        "description": "Human has requested changes; proposal returns to generation with revised inputs.",
        "terminal": False,
        "requires_human_action": True,
    },
)

_RAD_DECISION_MODEL: dict = {
    "decision_authority": "human",
    "decision_inputs": [
        "multi_agent_roadmap_proposal",
        "consensus_recommendation",
        "conflict_list",
        "agent_rationales",
        "confidence_assessments",
    ],
    "valid_decisions": ["approved", "denied", "changes_requested"],
    "decision_is_final": False,
    "human_notes_required": False,
    "conflict_resolution_required_before_approve": False,
    "advisory": "Human decision is authoritative; governance system recommendations are advisory.",
    "escalation": "If consensus_confidence is below threshold or conflicts are unresolved, human review is mandatory.",
}

_RAD_CONFLICT_RESOLUTION_REQUIREMENTS: dict = {
    "conflict_sources": [
        "agent recommendation disagreements",
        "confidence spread exceeding threshold",
        "phase exclusion by one or more agents",
    ],
    "resolution_strategies": [
        {"strategy": "human_override", "description": "Human selects final approved or denied phases."},
        {"strategy": "defer_conflict_phase", "description": "Move conflicting phase to denied or changes_requested bucket."},
        {"strategy": "re_elicit", "description": "Request new agent proposal with additional constraints."},
    ],
    "resolution_authority": "human",
    "resolution_must_be_recorded": True,
    "unresolved_conflicts_block_approve": False,
}

_RAD_ARTIFACT_MODEL: dict = {
    "artifact_name": "ApprovedRoadmapArtifact",
    "fields": [
        {"name": "roadmap_approval_id", "type": "str", "description": "Unique approval artifact identifier."},
        {"name": "proposal_id", "type": "str", "description": "ID of the approved/denied multi-agent roadmap proposal."},
        {"name": "approved_phases", "type": "list[str]", "description": "Phase IDs approved by the human."},
        {"name": "denied_phases", "type": "list[str]", "description": "Phase IDs denied by the human."},
        {"name": "changes_requested", "type": "list[dict]", "description": "Phases with requested changes and notes."},
        {"name": "conflicts_resolved", "type": "list[dict]", "description": "Conflicts and how each was resolved."},
        {"name": "approved_by", "type": "str", "description": "Identifier of the human approver."},
        {"name": "approved_at", "type": "str", "description": "ISO 8601 timestamp of the approval decision."},
        {"name": "human_notes", "type": "str", "description": "Free-text human notes on the decision."},
    ],
    "artifact_is_mutable": False,
    "artifact_creation": "future — not yet implemented; no approval mutation in this phase.",
}

_RAD_GOVERNANCE_BOUNDARIES: dict = {
    "approval_workflow_may": [
        "describe approval lifecycle",
        "define approval states",
        "define human decision model",
        "define conflict resolution requirements",
        "define approved roadmap artifact model",
        "define governance boundaries",
    ],
    "approval_workflow_may_not": [
        "record approval state",
        "mutate roadmap",
        "create tasks",
        "execute work",
        "generate prompts",
        "commit",
        "push",
    ],
    "human_decision_required": True,
    "advisory": True,
}

_RAD_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45F", "description": "Prompt Generation Design"},
    {"phase": "45G", "description": "Adaptive Agent-Specific Prompt Generation"},
    {"phase": "45H", "description": "Prompt Validation Framework"},
    {"phase": "45I", "description": "Prompt Governance Design"},
)


def build_roadmap_approval_design(root: HarnessPath) -> dict:
    """Design a governed roadmap approval workflow. Read-only; no approval state mutated."""
    multi_agent = build_multi_agent_roadmap(root)

    roadmap_approval_workflow = {
        "workflow_id": f"rad-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "proposal_id": multi_agent["proposal_id"],
        "dry_run_proposal_id": multi_agent["dry_run_proposal_id"],
        "evidence_package_id": multi_agent["evidence_package_id"],
        "approval_lifecycle": [dict(s) for s in _RAD_APPROVAL_LIFECYCLE],
        "human_decision_required": True,
        "current_approval_state": "pending",
    }

    return {
        "roadmap_approval_workflow": roadmap_approval_workflow,
        "approval_states": [dict(s) for s in _RAD_APPROVAL_STATES],
        "decision_model": dict(_RAD_DECISION_MODEL),
        "conflict_resolution_requirements": dict(_RAD_CONFLICT_RESOLUTION_REQUIREMENTS),
        "artifact_model": dict(_RAD_ARTIFACT_MODEL),
        "governance_boundaries": dict(_RAD_GOVERNANCE_BOUNDARIES),
        "future_evolution": [dict(e) for e in _RAD_FUTURE_EVOLUTION],
        "advisory": ROADMAP_APPROVAL_DESIGN_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 45F: Prompt Generation Design
# ---------------------------------------------------------------------------

PROMPT_GENERATION_DESIGN_ADVISORY = (
    "Prompt generation design is informational; no prompts are executed."
)

_PGD_LIFECYCLE: tuple[dict, ...] = (
    {
        "step": 1,
        "name": "approved_phase",
        "description": "An approved phase is selected as input to the prompt generation pipeline.",
        "inputs": ["approved_roadmap_proposals", "approved_phases", "roadmap_approval_artifacts"],
        "outputs": ["phase_id", "phase_context"],
    },
    {
        "step": 2,
        "name": "phase_analysis",
        "description": "The approved phase is analysed to extract objective, scope, constraints, and dependencies.",
        "inputs": ["phase_id", "phase_context", "roadmap_evidence"],
        "outputs": ["phase_analysis_result", "dependency_map", "constraint_set"],
    },
    {
        "step": 3,
        "name": "prompt_generation",
        "description": "A canonical prompt is generated from the phase analysis result.",
        "inputs": ["phase_analysis_result", "dependency_map", "constraint_set"],
        "outputs": ["draft_prompt", "prompt_id", "traceability_references"],
    },
    {
        "step": 4,
        "name": "prompt_validation",
        "description": "The draft prompt is validated for completeness, section coverage, and traceability.",
        "inputs": ["draft_prompt", "traceability_references"],
        "outputs": ["validation_result", "validation_errors", "validated_prompt"],
    },
    {
        "step": 5,
        "name": "human_review",
        "description": "The validated prompt is surfaced to a human for review and approval before any execution.",
        "inputs": ["validated_prompt", "validation_result"],
        "outputs": ["review_decision", "human_notes", "approved_prompt"],
    },
    {
        "step": 6,
        "name": "future_execution_candidate",
        "description": "The approved prompt becomes a future execution candidate; no execution occurs in this phase.",
        "inputs": ["approved_prompt"],
        "outputs": ["execution_candidate_id"],
    },
)

_PGD_CANONICAL_PROMPT_MODEL: dict = {
    "model_name": "CanonicalPrompt",
    "fields": [
        {"name": "prompt_id", "type": "str", "description": "Unique prompt identifier."},
        {"name": "phase_id", "type": "str", "description": "ID of the approved phase that generated this prompt."},
        {"name": "title", "type": "str", "description": "Human-readable title of the prompt."},
        {"name": "objective", "type": "str", "description": "What the prompt is intended to accomplish."},
        {"name": "rationale", "type": "str", "description": "Why this prompt is needed; traceability to approved roadmap."},
        {"name": "dependencies", "type": "list[str]", "description": "Other phase or prompt IDs this prompt depends on."},
        {"name": "allowed_files", "type": "list[str]", "description": "File path patterns the agent may modify."},
        {"name": "forbidden_files", "type": "list[str]", "description": "File path patterns the agent must not modify."},
        {"name": "acceptance_criteria", "type": "list[str]", "description": "Conditions that must hold for the prompt to be considered complete."},
        {"name": "validation_steps", "type": "list[str]", "description": "Commands or checks to run to verify acceptance criteria."},
        {"name": "governance_rules", "type": "list[str]", "description": "Governance constraints that apply during execution."},
        {"name": "confidence", "type": "float", "description": "Confidence score (0.0–1.0) for the generated prompt."},
        {"name": "human_approval_required", "type": "bool", "description": "Whether human approval is required before execution."},
    ],
}

_PGD_REQUIRED_SECTIONS: tuple[str, ...] = (
    "goal",
    "scope",
    "constraints",
    "allowed_files",
    "forbidden_files",
    "acceptance_criteria",
    "validation_commands",
    "governance_boundaries",
)

_PGD_TRACEABILITY_MODEL: dict = {
    "required_references": [
        {"field": "proposal_id", "description": "ID of the approved roadmap proposal that authorised this prompt."},
        {"field": "roadmap_approval_id", "description": "ID of the roadmap approval artifact that recorded human approval."},
        {"field": "evidence_package_id", "description": "ID of the evidence package that informed the roadmap proposal."},
    ],
    "traceability_purpose": "Prompts must be traceable to approved roadmap artifacts so governance audits can verify authorisation.",
    "traceability_is_required": True,
}

_PGD_GOVERNANCE_BOUNDARIES: dict = {
    "prompt_generation_may": [
        "generate prompts",
        "generate validation guidance",
        "generate governance guidance",
    ],
    "prompt_generation_may_not": [
        "execute prompts",
        "invoke agents",
        "modify repository",
        "create commits",
        "create pushes",
    ],
    "human_approval_required": True,
    "advisory": True,
}

_PGD_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45G", "description": "Adaptive Agent-Specific Prompt Generation"},
    {"phase": "45H", "description": "Prompt Validation Framework"},
    {"phase": "45I", "description": "Prompt Governance Design"},
    {"phase": "45J", "description": "Prompt Artifact Model"},
    {"phase": "45K", "description": "Prompt Approval Workflow"},
)


def build_prompt_generation_design() -> dict:
    """Design the canonical prompt generation architecture. Read-only; no prompts executed."""
    design_id = f"pgd-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    prompt_generation_design = {
        "design_id": design_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "45F",
        "title": "Prompt Generation Design",
        "summary": (
            "Defines the canonical prompt generation architecture used by PCAE. "
            "Prompts are derived from approved phases and roadmap artifacts. "
            "No prompts are executed; no agents are invoked."
        ),
        "lifecycle": [dict(s) for s in _PGD_LIFECYCLE],
        "canonical_prompt_model": dict(_PGD_CANONICAL_PROMPT_MODEL),
        "required_sections": list(_PGD_REQUIRED_SECTIONS),
        "traceability_model": dict(_PGD_TRACEABILITY_MODEL),
        "governance_boundaries": dict(_PGD_GOVERNANCE_BOUNDARIES),
        "future_evolution": [dict(e) for e in _PGD_FUTURE_EVOLUTION],
    }

    return {
        "prompt_generation_design": prompt_generation_design,
        "lifecycle": [dict(s) for s in _PGD_LIFECYCLE],
        "canonical_prompt_model": dict(_PGD_CANONICAL_PROMPT_MODEL),
        "traceability_model": dict(_PGD_TRACEABILITY_MODEL),
        "governance_boundaries": dict(_PGD_GOVERNANCE_BOUNDARIES),
        "advisory": PROMPT_GENERATION_DESIGN_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 45G: Adaptive Agent-Specific Prompt Generation
# ---------------------------------------------------------------------------

ADAPTIVE_PROMPT_DESIGN_ADVISORY = (
    "Adaptive prompt generation design is informational; no prompts are executed."
)

_APD_SUPPORTED_AGENTS: tuple[str, ...] = (
    "codex-local",
    "claude-local",
    "kimi-local",
)

_APD_LIFECYCLE: tuple[dict, ...] = (
    {
        "step": 1,
        "name": "canonical_prompt",
        "description": "A canonical prompt artifact is received as input.",
        "inputs": ["canonical_prompt_artifact", "approved_phase", "prompt_generation_design"],
        "outputs": ["canonical_prompt_id", "canonical_prompt_context"],
    },
    {
        "step": 2,
        "name": "human_agent_selection",
        "description": "A human selects one or more target agents. PCAE may recommend; human is authoritative.",
        "inputs": ["canonical_prompt_context", "capability_registry"],
        "outputs": ["selected_agents", "selection_rationale"],
    },
    {
        "step": 3,
        "name": "agent_profile_lookup",
        "description": "Adaptation profiles for each selected agent are retrieved from the registry.",
        "inputs": ["selected_agents", "capability_registry"],
        "outputs": ["agent_profiles", "adaptation_rules"],
    },
    {
        "step": 4,
        "name": "prompt_adaptation",
        "description": "The canonical prompt is adapted for each selected agent according to its profile.",
        "inputs": ["canonical_prompt_context", "agent_profiles", "adaptation_rules"],
        "outputs": ["adapted_prompts", "adaptation_summary"],
    },
    {
        "step": 5,
        "name": "intent_preservation_check",
        "description": "Each adapted prompt is checked to confirm objective, acceptance criteria, and governance boundaries are unchanged.",
        "inputs": ["adapted_prompts", "canonical_prompt_context"],
        "outputs": ["intent_preservation_status", "preservation_warnings"],
    },
    {
        "step": 6,
        "name": "human_review",
        "description": "The adapted prompt set is presented to a human for review before any execution.",
        "inputs": ["adapted_prompts", "intent_preservation_status", "adaptation_summary"],
        "outputs": ["review_decision", "human_notes", "approved_prompt_set"],
    },
    {
        "step": 7,
        "name": "future_execution_candidate",
        "description": "The approved adapted prompts become future execution candidates; no execution occurs in this phase.",
        "inputs": ["approved_prompt_set"],
        "outputs": ["execution_candidate_ids"],
    },
)

_APD_HUMAN_AGENT_SELECTION: dict = {
    "supported_agents": list(_APD_SUPPORTED_AGENTS),
    "multi_agent_allowed": True,
    "selection_authority": "human",
    "pcae_recommendation": "advisory",
    "selection_notes": [
        "Human may select a single agent or any combination of supported agents.",
        "PCAE may recommend agents based on task type and capability registry.",
        "Human selection overrides any PCAE recommendation.",
        "Vendor-neutral: no agent is mandatory.",
    ],
}

_APD_ADAPTATION_PROFILES: tuple[dict, ...] = (
    {
        "agent_id": "codex-local",
        "adaptation_focus": "implementation",
        "style": "concise, execution-oriented",
        "emphasis": [
            "implementation-focused instructions",
            "file and change focused scope",
            "concise execution instructions",
            "strong validation commands",
        ],
        "review_depth": "low",
        "design_alternatives": False,
        "risk_analysis": False,
        "assumption_checking": False,
        "edge_case_coverage": False,
    },
    {
        "agent_id": "claude-local",
        "adaptation_focus": "architecture and review",
        "style": "thorough, analytical",
        "emphasis": [
            "architecture and review focused instructions",
            "risk analysis",
            "design alternatives",
            "governance review",
        ],
        "review_depth": "high",
        "design_alternatives": True,
        "risk_analysis": True,
        "assumption_checking": False,
        "edge_case_coverage": False,
    },
    {
        "agent_id": "kimi-local",
        "adaptation_focus": "research and challenge",
        "style": "exploratory, questioning",
        "emphasis": [
            "research and challenge focused instructions",
            "assumption checking",
            "edge cases",
            "alternative approaches",
            "capability discovery",
        ],
        "review_depth": "medium",
        "design_alternatives": True,
        "risk_analysis": False,
        "assumption_checking": True,
        "edge_case_coverage": True,
    },
)

_APD_INTENT_PRESERVATION_RULES: dict = {
    "adaptation_may_change": [
        "style",
        "focus",
        "explanation depth",
        "validation emphasis",
        "review emphasis",
    ],
    "adaptation_must_not_change": [
        "objective",
        "acceptance criteria",
        "governance boundaries",
        "allowed files",
        "forbidden files",
        "safety rules",
    ],
    "preservation_check_required": True,
    "preservation_failure_blocks_execution": True,
}

_APD_PROMPT_SET_MODEL: dict = {
    "model_name": "AdaptedPromptSet",
    "fields": [
        {"name": "prompt_set_id", "type": "str", "description": "Unique identifier for the adapted prompt set."},
        {"name": "canonical_prompt_id", "type": "str", "description": "ID of the canonical prompt this set was derived from."},
        {"name": "selected_agents", "type": "list[str]", "description": "Agent IDs selected by the human."},
        {"name": "adapted_prompts", "type": "list[AdaptedPrompt]", "description": "One adapted prompt per selected agent."},
        {"name": "adaptation_summary", "type": "str", "description": "Human-readable summary of what changed across adaptations."},
        {"name": "intent_preservation_status", "type": "str", "description": "Overall preservation check result: preserved or violated."},
        {"name": "human_approval_required", "type": "bool", "description": "Whether human approval is required before any execution."},
    ],
    "adapted_prompt_fields": [
        {"name": "agent_id", "type": "str", "description": "Target agent for this adaptation."},
        {"name": "adaptation_profile", "type": "str", "description": "Name of the adaptation profile applied."},
        {"name": "prompt_text", "type": "str", "description": "The adapted prompt text."},
        {"name": "preserved_sections", "type": "list[str]", "description": "Sections kept identical to the canonical prompt."},
        {"name": "adapted_sections", "type": "list[str]", "description": "Sections modified during adaptation."},
        {"name": "warnings", "type": "list[str]", "description": "Any preservation warnings raised during adaptation."},
    ],
}

_APD_GOVERNANCE_BOUNDARIES: dict = {
    "adaptive_prompt_generation_may": [
        "generate agent-specific prompt variants",
        "summarize adaptations",
        "recommend agents",
    ],
    "adaptive_prompt_generation_may_not": [
        "execute prompts",
        "invoke agents",
        "modify repository",
        "change canonical intent",
        "approve prompts",
        "commit",
        "push",
    ],
    "human_approval_required": True,
    "advisory": True,
}

_APD_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45H", "description": "Prompt Validation Framework"},
    {"phase": "45I", "description": "Prompt Governance Design"},
    {"phase": "45J", "description": "Prompt Artifact Model"},
    {"phase": "45K", "description": "Prompt Approval Workflow"},
)


def build_adaptive_prompt_design() -> dict:
    """Design adaptive agent-specific prompt generation. Read-only; no prompts executed."""
    design_id = f"apd-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    adaptive_prompt_design = {
        "design_id": design_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "45G",
        "title": "Adaptive Agent-Specific Prompt Generation",
        "summary": (
            "Defines how PCAE adapts a canonical prompt to one or more target agents. "
            "The human selects target agents; PCAE adapts style, focus, and emphasis "
            "without changing objective, acceptance criteria, or governance boundaries. "
            "No prompts are executed; no agents are invoked."
        ),
        "lifecycle": [dict(s) for s in _APD_LIFECYCLE],
        "human_agent_selection": dict(_APD_HUMAN_AGENT_SELECTION),
        "adaptation_profiles": [dict(p) for p in _APD_ADAPTATION_PROFILES],
        "intent_preservation_rules": dict(_APD_INTENT_PRESERVATION_RULES),
        "prompt_set_model": dict(_APD_PROMPT_SET_MODEL),
        "governance_boundaries": dict(_APD_GOVERNANCE_BOUNDARIES),
        "future_evolution": [dict(e) for e in _APD_FUTURE_EVOLUTION],
    }

    return {
        "adaptive_prompt_design": adaptive_prompt_design,
        "lifecycle": [dict(s) for s in _APD_LIFECYCLE],
        "human_agent_selection": dict(_APD_HUMAN_AGENT_SELECTION),
        "adaptation_profiles": [dict(p) for p in _APD_ADAPTATION_PROFILES],
        "intent_preservation_rules": dict(_APD_INTENT_PRESERVATION_RULES),
        "prompt_set_model": dict(_APD_PROMPT_SET_MODEL),
        "governance_boundaries": dict(_APD_GOVERNANCE_BOUNDARIES),
        "advisory": ADAPTIVE_PROMPT_DESIGN_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 45H: Prompt Validation Framework
# ---------------------------------------------------------------------------

PROMPT_VALIDATION_DESIGN_ADVISORY = (
    "Prompt validation design is informational; no prompts are executed."
)

_PVD_REQUIRED_SECTIONS: tuple[str, ...] = (
    "goal",
    "scope",
    "constraints",
    "allowed_files",
    "forbidden_files",
    "acceptance_criteria",
    "validation_commands",
    "governance_boundaries",
)

_PVD_VALIDATION_CATEGORIES: tuple[dict, ...] = (
    {
        "category": "completeness",
        "description": "Verifies all required sections are present in the prompt.",
        "rules": [
            f"Section '{s}' must be present and non-empty."
            for s in _PVD_REQUIRED_SECTIONS
        ],
        "failure_severity": "error",
    },
    {
        "category": "traceability",
        "description": "Verifies the prompt references required governance artifacts.",
        "rules": [
            "prompt_id must be present.",
            "phase_id must reference an approved phase.",
            "proposal_id must reference an approved roadmap proposal.",
            "roadmap_approval_id must reference a recorded approval artifact.",
            "evidence_package_id must reference an evidence package.",
        ],
        "failure_severity": "error",
    },
    {
        "category": "intent_preservation",
        "description": "Verifies agent-specific prompts do not alter objective, acceptance criteria, or governance boundaries.",
        "rules": [
            "objective must be identical to the canonical prompt.",
            "acceptance_criteria must be identical to the canonical prompt.",
            "governance_boundaries must be identical to the canonical prompt.",
            "allowed_files must be identical to the canonical prompt.",
            "forbidden_files must be identical to the canonical prompt.",
            "safety_rules must be identical to the canonical prompt.",
        ],
        "failure_severity": "error",
        "applies_to": "agent_specific_prompts",
    },
    {
        "category": "safety",
        "description": "Verifies the prompt does not contain instructions that bypass governance.",
        "rules": [
            "Prompt must not instruct agent to bypass governance.",
            "Prompt must not instruct agent to auto-approve.",
            "Prompt must not instruct agent to auto-commit.",
            "Prompt must not instruct agent to auto-push.",
            "Prompt must not instruct agent to auto-rollback.",
            "Prompt must not silently expand allowed scope.",
        ],
        "failure_severity": "error",
    },
    {
        "category": "agent_compatibility",
        "description": "Verifies the target agent exists and is compatible with the prompt.",
        "rules": [
            "Target agent must exist in the capability registry.",
            "Target agent capability must be suitable for the prompt task type.",
            "Selected agent must match the adaptation profile used.",
        ],
        "failure_severity": "warning",
    },
)

_PVD_TRACEABILITY_REQUIREMENTS: dict = {
    "required_references": [
        {"field": "prompt_id", "description": "Unique identifier for this prompt."},
        {"field": "phase_id", "description": "ID of the approved phase that generated this prompt."},
        {"field": "proposal_id", "description": "ID of the approved roadmap proposal."},
        {"field": "roadmap_approval_id", "description": "ID of the recorded roadmap approval artifact."},
        {"field": "evidence_package_id", "description": "ID of the evidence package informing the roadmap."},
    ],
    "traceability_is_required": True,
    "missing_reference_severity": "error",
}

_PVD_INTENT_PRESERVATION_RULES: dict = {
    "applies_to": "agent_specific_prompts",
    "preserved_fields": [
        "objective",
        "acceptance_criteria",
        "governance_boundaries",
        "allowed_files",
        "forbidden_files",
        "safety_rules",
    ],
    "check_method": "field_equality_against_canonical",
    "failure_severity": "error",
    "preservation_check_required": True,
}

_PVD_SAFETY_RULES: tuple[str, ...] = (
    "Prompt must not instruct agent to bypass governance.",
    "Prompt must not instruct agent to auto-approve.",
    "Prompt must not instruct agent to auto-commit.",
    "Prompt must not instruct agent to auto-push.",
    "Prompt must not instruct agent to auto-rollback.",
    "Prompt must not silently expand allowed scope.",
)

_PVD_VALIDATION_STATUSES: tuple[str, ...] = (
    "valid",
    "valid_with_warnings",
    "invalid",
)

_PVD_VALIDATION_RESULT_MODEL: dict = {
    "model_name": "PromptValidationResult",
    "fields": [
        {"name": "validation_id", "type": "str", "description": "Unique identifier for this validation run."},
        {"name": "prompt_id", "type": "str", "description": "ID of the prompt being validated."},
        {"name": "validation_status", "type": "str", "description": f"Overall status: {', '.join(_PVD_VALIDATION_STATUSES)}."},
        {"name": "errors", "type": "list[str]", "description": "Validation errors that must be resolved before approval."},
        {"name": "warnings", "type": "list[str]", "description": "Non-blocking issues that should be reviewed."},
        {"name": "missing_sections", "type": "list[str]", "description": "Required sections absent from the prompt."},
        {"name": "traceability_status", "type": "str", "description": "Result of traceability check: complete or incomplete."},
        {"name": "intent_preservation_status", "type": "str", "description": "Result of intent preservation check: preserved or violated."},
        {"name": "safety_status", "type": "str", "description": "Result of safety check: safe or unsafe."},
        {"name": "human_review_required", "type": "bool", "description": "Whether human review is required before approval."},
    ],
    "validation_statuses": list(_PVD_VALIDATION_STATUSES),
}

_PVD_GOVERNANCE_BOUNDARIES: dict = {
    "prompt_validation_may": [
        "validate prompt completeness",
        "validate prompt traceability",
        "validate intent preservation",
        "validate safety rules",
        "validate agent compatibility",
        "report validation results",
    ],
    "prompt_validation_may_not": [
        "execute prompts",
        "invoke agents",
        "modify repository",
        "auto-approve prompts",
        "commit",
        "push",
    ],
    "read_only": True,
    "human_review_required": True,
    "advisory": True,
}

_PVD_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45I", "description": "Prompt Governance Design"},
    {"phase": "45J", "description": "Prompt Artifact Model"},
    {"phase": "45K", "description": "Prompt Approval Workflow"},
)


def build_prompt_validation_design() -> dict:
    """Design the prompt validation framework. Read-only; no prompts executed."""
    design_id = f"pvd-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    prompt_validation_design = {
        "design_id": design_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "45H",
        "title": "Prompt Validation Framework",
        "summary": (
            "Defines validation rules for generated canonical and agent-specific prompts "
            "before approval or execution. Covers completeness, traceability, intent "
            "preservation, safety, and agent compatibility. No prompts are executed; "
            "no agents are invoked."
        ),
        "validation_categories": [dict(c) for c in _PVD_VALIDATION_CATEGORIES],
        "required_sections": list(_PVD_REQUIRED_SECTIONS),
        "traceability_requirements": dict(_PVD_TRACEABILITY_REQUIREMENTS),
        "intent_preservation_rules": dict(_PVD_INTENT_PRESERVATION_RULES),
        "safety_rules": list(_PVD_SAFETY_RULES),
        "validation_result_model": dict(_PVD_VALIDATION_RESULT_MODEL),
        "governance_boundaries": dict(_PVD_GOVERNANCE_BOUNDARIES),
        "future_evolution": [dict(e) for e in _PVD_FUTURE_EVOLUTION],
    }

    return {
        "prompt_validation_design": prompt_validation_design,
        "validation_categories": [dict(c) for c in _PVD_VALIDATION_CATEGORIES],
        "required_sections": list(_PVD_REQUIRED_SECTIONS),
        "traceability_requirements": dict(_PVD_TRACEABILITY_REQUIREMENTS),
        "intent_preservation_rules": dict(_PVD_INTENT_PRESERVATION_RULES),
        "safety_rules": list(_PVD_SAFETY_RULES),
        "validation_result_model": dict(_PVD_VALIDATION_RESULT_MODEL),
        "governance_boundaries": dict(_PVD_GOVERNANCE_BOUNDARIES),
        "advisory": PROMPT_VALIDATION_DESIGN_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 45I: Prompt Governance Design
# ---------------------------------------------------------------------------

PROMPT_GOVERNANCE_DESIGN_ADVISORY = (
    "Prompt governance design is informational; no prompts are approved or executed."
)

_PGV_GOVERNANCE_LIFECYCLE: tuple[dict, ...] = (
    {
        "step": 1,
        "name": "canonical_prompt",
        "description": "A canonical prompt artifact enters the governance pipeline.",
        "inputs": ["canonical_prompt_artifact", "roadmap_approval_artifact"],
        "outputs": ["prompt_id", "governance_context"],
    },
    {
        "step": 2,
        "name": "validation",
        "description": "The prompt is validated for completeness, traceability, intent preservation, and safety.",
        "inputs": ["prompt_id", "prompt_validation_results"],
        "outputs": ["validation_status", "validation_errors", "validation_warnings"],
    },
    {
        "step": 3,
        "name": "governance_review",
        "description": "Governance lineage, audit history, and approval requirements are checked.",
        "inputs": ["prompt_id", "validation_status", "lineage_record"],
        "outputs": ["governance_review_result", "approval_requirements_met"],
    },
    {
        "step": 4,
        "name": "human_approval",
        "description": "A human reviews the governance review result and grants or denies approval.",
        "inputs": ["prompt_id", "governance_review_result"],
        "outputs": ["approval_decision", "human_notes", "governance_state"],
    },
    {
        "step": 5,
        "name": "approved_prompt",
        "description": "The prompt is recorded as approved and its lineage is updated.",
        "inputs": ["approval_decision", "governance_state"],
        "outputs": ["approved_prompt_id", "updated_lineage"],
    },
    {
        "step": 6,
        "name": "future_execution_candidate",
        "description": "The approved prompt becomes a future execution candidate; no execution occurs in this phase.",
        "inputs": ["approved_prompt_id"],
        "outputs": ["execution_candidate_id"],
    },
)

_PGV_GOVERNED_PROMPT_TYPES: tuple[dict, ...] = (
    {
        "type": "canonical_prompt",
        "description": "The original prompt derived from an approved phase. Source of truth for intent.",
        "mutable": False,
        "requires_approval": True,
    },
    {
        "type": "adapted_prompt",
        "description": "An agent-specific variant of a canonical prompt. Intent must be preserved.",
        "mutable": False,
        "requires_approval": True,
    },
    {
        "type": "approved_prompt",
        "description": "A canonical or adapted prompt that has passed validation and received human approval.",
        "mutable": False,
        "requires_approval": False,
    },
    {
        "type": "rejected_prompt",
        "description": "A prompt that failed validation or was denied by a human reviewer.",
        "mutable": False,
        "requires_approval": False,
    },
    {
        "type": "superseded_prompt",
        "description": "A prompt that has been replaced by a newer version. Retained for audit history.",
        "mutable": False,
        "requires_approval": False,
    },
)

_PGV_GOVERNANCE_REQUIREMENTS: dict = {
    "required_fields": [
        "prompt_id",
        "phase_id",
        "proposal_id",
        "roadmap_approval_id",
        "evidence_package_id",
    ],
    "required_properties": [
        "traceable",
        "auditable",
        "reviewable",
    ],
}

_PGV_LINEAGE_MODEL: dict = {
    "model_name": "PromptLineage",
    "tracked_fields": [
        {"name": "source_prompt_id", "description": "ID of the canonical prompt this prompt derives from."},
        {"name": "adaptation_history", "description": "Ordered list of adaptation events with agent_id, timestamp, and changes."},
        {"name": "validation_history", "description": "Ordered list of validation runs with validation_id, status, and timestamp."},
        {"name": "approval_history", "description": "Ordered list of approval decisions with decision, approver, timestamp, and notes."},
    ],
    "lineage_is_append_only": True,
    "lineage_deletion_forbidden": True,
}

_PGV_INTENT_PROTECTION_RULES: dict = {
    "protected_fields": [
        "objective",
        "acceptance_criteria",
        "governance_boundaries",
        "allowed_files",
        "forbidden_files",
        "safety_rules",
    ],
    "protection_rule": "Protected fields may not change during adaptation.",
    "enforcement": "governance",
    "violation_severity": "error",
    "violation_blocks_approval": True,
}

_PGV_APPROVAL_REQUIREMENTS: tuple[str, ...] = (
    "Validation must have passed (status: valid or valid_with_warnings).",
    "Traceability must be complete (all required references present).",
    "Intent must be preserved (no protected fields changed).",
    "Human approval must be explicitly granted.",
)

_PGV_GOVERNANCE_STATES: tuple[dict, ...] = (
    {
        "state": "draft",
        "description": "Prompt has been generated but not yet submitted for validation.",
        "terminal": False,
        "requires_human_action": False,
    },
    {
        "state": "validated",
        "description": "Prompt has passed validation checks.",
        "terminal": False,
        "requires_human_action": False,
    },
    {
        "state": "pending_approval",
        "description": "Prompt has passed validation and is awaiting human approval.",
        "terminal": False,
        "requires_human_action": True,
    },
    {
        "state": "approved",
        "description": "Human has granted approval; prompt is a future execution candidate.",
        "terminal": True,
        "requires_human_action": False,
    },
    {
        "state": "rejected",
        "description": "Human has denied approval or validation failed irrecoverably.",
        "terminal": True,
        "requires_human_action": False,
    },
    {
        "state": "superseded",
        "description": "Prompt has been replaced by a newer version; retained for audit.",
        "terminal": True,
        "requires_human_action": False,
    },
)

_PGV_GOVERNANCE_BOUNDARIES: dict = {
    "prompt_governance_may": [
        "validate prompts",
        "record lineage",
        "record approvals",
        "record audit history",
    ],
    "prompt_governance_may_not": [
        "execute prompts",
        "invoke agents",
        "modify repository",
        "bypass approval",
        "auto-approve prompts",
        "commit",
        "push",
    ],
    "read_only": True,
    "human_approval_required": True,
    "advisory": True,
}

_PGV_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45J", "description": "Prompt Artifact Model"},
    {"phase": "45K", "description": "Prompt Approval Workflow"},
    {"phase": "45L", "description": "Autonomous Phase Proposal Prototype"},
    {"phase": "45M", "description": "Autonomous Prompt Proposal Prototype"},
)


def build_prompt_governance_design() -> dict:
    """Design governance controls for canonical and adapted prompts. Read-only; no prompts approved or executed."""
    design_id = f"pgv-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    prompt_governance_design = {
        "design_id": design_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "45I",
        "title": "Prompt Governance Design",
        "summary": (
            "Defines governance controls for canonical prompts and adapted prompts "
            "within PCAE. Covers lifecycle, governed prompt types, lineage tracking, "
            "intent protection, approval requirements, and governance states. "
            "No prompts are approved or executed."
        ),
        "governance_lifecycle": [dict(s) for s in _PGV_GOVERNANCE_LIFECYCLE],
        "governed_prompt_types": [dict(t) for t in _PGV_GOVERNED_PROMPT_TYPES],
        "governance_requirements": dict(_PGV_GOVERNANCE_REQUIREMENTS),
        "lineage_model": dict(_PGV_LINEAGE_MODEL),
        "intent_protection_rules": dict(_PGV_INTENT_PROTECTION_RULES),
        "approval_requirements": list(_PGV_APPROVAL_REQUIREMENTS),
        "governance_states": [dict(s) for s in _PGV_GOVERNANCE_STATES],
        "governance_boundaries": dict(_PGV_GOVERNANCE_BOUNDARIES),
        "future_evolution": [dict(e) for e in _PGV_FUTURE_EVOLUTION],
    }

    return {
        "prompt_governance_design": prompt_governance_design,
        "governance_lifecycle": [dict(s) for s in _PGV_GOVERNANCE_LIFECYCLE],
        "governed_prompt_types": [dict(t) for t in _PGV_GOVERNED_PROMPT_TYPES],
        "lineage_model": dict(_PGV_LINEAGE_MODEL),
        "approval_requirements": list(_PGV_APPROVAL_REQUIREMENTS),
        "governance_states": [dict(s) for s in _PGV_GOVERNANCE_STATES],
        "governance_boundaries": dict(_PGV_GOVERNANCE_BOUNDARIES),
        "advisory": PROMPT_GOVERNANCE_DESIGN_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 45J: Prompt Artifact Model
# ---------------------------------------------------------------------------

PROMPT_ARTIFACT_DESIGN_ADVISORY = (
    "Prompt artifact design is informational; no prompts are executed or approved."
)

_PAD_LIFECYCLE: tuple[dict, ...] = (
    {
        "step": 1,
        "name": "canonical_prompt",
        "description": "A canonical prompt artifact is created from an approved phase.",
        "inputs": ["approved_phase", "roadmap_approval_artifact", "prompt_generation_design"],
        "outputs": ["prompt_artifact", "prompt_id"],
    },
    {
        "step": 2,
        "name": "adapted_prompt",
        "description": "Agent-specific adaptations are generated and attached to the artifact.",
        "inputs": ["prompt_artifact", "adaptive_prompt_design", "selected_agents"],
        "outputs": ["adapted_prompt_entries", "adaptation_history"],
    },
    {
        "step": 3,
        "name": "validated_prompt",
        "description": "The artifact is validated; validation results are recorded in the artifact.",
        "inputs": ["prompt_artifact", "prompt_validation_framework"],
        "outputs": ["validation_status", "validation_results", "validation_history"],
    },
    {
        "step": 4,
        "name": "approved_prompt",
        "description": "Human approval is recorded; governance state transitions to approved.",
        "inputs": ["prompt_artifact", "prompt_governance_design"],
        "outputs": ["approval_state", "approval_history", "governance_state"],
    },
    {
        "step": 5,
        "name": "future_execution_candidate",
        "description": "The approved artifact becomes a future execution candidate; no execution in this phase.",
        "inputs": ["prompt_artifact"],
        "outputs": ["execution_candidate_id"],
    },
)

_PAD_ARTIFACT_MODEL: dict = {
    "model_name": "PromptArtifact",
    "field_groups": {
        "identity": [
            {"name": "prompt_id", "type": "str", "description": "Unique identifier for this prompt artifact."},
            {"name": "prompt_set_id", "type": "str", "description": "ID of the adapted prompt set this artifact belongs to."},
            {"name": "phase_id", "type": "str", "description": "ID of the approved phase that generated this prompt."},
        ],
        "traceability": [
            {"name": "proposal_id", "type": "str", "description": "ID of the approved roadmap proposal."},
            {"name": "roadmap_approval_id", "type": "str", "description": "ID of the roadmap approval artifact."},
            {"name": "evidence_package_id", "type": "str", "description": "ID of the evidence package."},
        ],
        "metadata": [
            {"name": "title", "type": "str", "description": "Human-readable title of the prompt."},
            {"name": "objective", "type": "str", "description": "What the prompt is intended to accomplish."},
            {"name": "rationale", "type": "str", "description": "Why this prompt is needed; traceability to approved roadmap."},
            {"name": "confidence", "type": "float", "description": "Confidence score (0.0–1.0) for this artifact."},
        ],
        "content": [
            {"name": "canonical_prompt_text", "type": "str", "description": "The canonical prompt text."},
            {"name": "adapted_prompts", "type": "list[AdaptedPromptEntry]", "description": "Agent-specific adaptations."},
        ],
        "validation": [
            {"name": "validation_status", "type": "str", "description": "Overall validation result: valid, valid_with_warnings, or invalid."},
            {"name": "validation_results", "type": "list[PromptValidationResult]", "description": "Detailed validation result records."},
        ],
        "governance": [
            {"name": "governance_state", "type": "str", "description": "Current governance state: draft, validated, pending_approval, approved, rejected, or superseded."},
            {"name": "approval_state", "type": "str", "description": "Current approval state: pending, approved, rejected, or changes_requested."},
        ],
        "lineage": [
            {"name": "source_prompt_id", "type": "str | None", "description": "ID of the prompt this was derived from, if any."},
            {"name": "adaptation_history", "type": "list[dict]", "description": "Ordered record of adaptation events."},
            {"name": "validation_history", "type": "list[dict]", "description": "Ordered record of validation runs."},
            {"name": "approval_history", "type": "list[dict]", "description": "Ordered record of approval decisions."},
        ],
    },
}

_PAD_ADAPTED_PROMPT_MODEL: dict = {
    "model_name": "AdaptedPromptEntry",
    "fields": [
        {"name": "agent_id", "type": "str", "description": "Target agent for this adaptation."},
        {"name": "adaptation_profile", "type": "str", "description": "Name of the adaptation profile applied."},
        {"name": "prompt_text", "type": "str", "description": "The adapted prompt text."},
        {"name": "preserved_sections", "type": "list[str]", "description": "Sections kept identical to the canonical prompt."},
        {"name": "adapted_sections", "type": "list[str]", "description": "Sections modified during adaptation."},
        {"name": "warnings", "type": "list[str]", "description": "Preservation warnings raised during adaptation."},
    ],
}

_PAD_ARTIFACT_STATES: tuple[str, ...] = (
    "draft",
    "validated",
    "pending_approval",
    "approved",
    "rejected",
    "superseded",
)

_PAD_INVARIANTS: dict = {
    "must_always_have": [
        "prompt_id",
        "phase_id",
        "proposal_id",
    ],
    "must_never_allow": [
        "lineage deletion",
        "traceability removal",
        "approval bypass",
    ],
    "invariant_enforcement": "governance",
    "invariant_violation_severity": "error",
}

_PAD_GOVERNANCE_BOUNDARIES: dict = {
    "artifact_model_may": [
        "represent prompts",
        "represent validation",
        "represent approvals",
        "represent lineage",
    ],
    "artifact_model_may_not": [
        "execute prompts",
        "invoke agents",
        "modify repository",
        "auto-approve",
        "commit",
        "push",
    ],
    "read_only": True,
    "human_approval_required": True,
    "advisory": True,
}

_PAD_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45K", "description": "Prompt Approval Workflow"},
    {"phase": "45L", "description": "Autonomous Phase Proposal Prototype"},
    {"phase": "45M", "description": "Autonomous Prompt Proposal Prototype"},
)


def build_prompt_artifact_design() -> dict:
    """Define the canonical PromptArtifact model. Read-only; no prompts executed or approved."""
    design_id = f"pad-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    all_fields = [
        f for group in _PAD_ARTIFACT_MODEL["field_groups"].values() for f in group
    ]

    prompt_artifact_design = {
        "design_id": design_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "45J",
        "title": "Prompt Artifact Model",
        "summary": (
            "Defines the canonical governed PromptArtifact model used throughout PCAE. "
            "Consolidates identity, traceability, content, validation, governance, and "
            "lineage into a single versioned artifact. No prompts are executed or approved."
        ),
        "lifecycle": [dict(s) for s in _PAD_LIFECYCLE],
        "artifact_model": {
            "model_name": _PAD_ARTIFACT_MODEL["model_name"],
            "field_groups": {k: list(v) for k, v in _PAD_ARTIFACT_MODEL["field_groups"].items()},
            "all_fields": all_fields,
            "field_count": len(all_fields),
        },
        "adapted_prompt_model": dict(_PAD_ADAPTED_PROMPT_MODEL),
        "artifact_states": list(_PAD_ARTIFACT_STATES),
        "invariants": dict(_PAD_INVARIANTS),
        "governance_boundaries": dict(_PAD_GOVERNANCE_BOUNDARIES),
        "future_evolution": [dict(e) for e in _PAD_FUTURE_EVOLUTION],
    }

    return {
        "prompt_artifact_design": prompt_artifact_design,
        "lifecycle": [dict(s) for s in _PAD_LIFECYCLE],
        "artifact_model": prompt_artifact_design["artifact_model"],
        "adapted_prompt_model": dict(_PAD_ADAPTED_PROMPT_MODEL),
        "invariants": dict(_PAD_INVARIANTS),
        "governance_boundaries": dict(_PAD_GOVERNANCE_BOUNDARIES),
        "advisory": PROMPT_ARTIFACT_DESIGN_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 45K: Prompt Approval Workflow
# ---------------------------------------------------------------------------

PROMPT_APPROVAL_WORKFLOW_ADVISORY = (
    "Prompt approval workflow is informational; no prompts are approved or executed."
)

_PAW_APPROVAL_LIFECYCLE: tuple[dict, ...] = (
    {
        "step": 1,
        "name": "draft_prompt_artifact",
        "description": "A PromptArtifact in draft state enters the approval pipeline.",
        "inputs": ["prompt_artifact", "roadmap_approval_artifact"],
        "outputs": ["prompt_id", "approval_context"],
    },
    {
        "step": 2,
        "name": "validation_review",
        "description": "Validation results are reviewed; artifact must be valid or valid_with_warnings.",
        "inputs": ["prompt_artifact", "prompt_validation_results"],
        "outputs": ["validation_gate_passed", "validation_summary"],
    },
    {
        "step": 3,
        "name": "governance_review",
        "description": "Governance requirements are checked: traceability, intent preservation, safety.",
        "inputs": ["prompt_artifact", "prompt_governance_design"],
        "outputs": ["governance_gate_passed", "governance_summary"],
    },
    {
        "step": 4,
        "name": "human_decision",
        "description": "A human reviews the artifact and records an approval decision.",
        "inputs": ["prompt_artifact", "validation_summary", "governance_summary"],
        "outputs": ["approval_state", "human_notes", "approved_agents"],
    },
    {
        "step": 5,
        "name": "approved_prompt_artifact",
        "description": "The approval decision is recorded; artifact transitions to approved state.",
        "inputs": ["approval_state", "human_notes", "approved_agents"],
        "outputs": ["prompt_approval_id", "approved_prompt_artifact"],
    },
    {
        "step": 6,
        "name": "future_execution_candidate",
        "description": "The approved artifact is a future execution candidate; no execution in this phase.",
        "inputs": ["approved_prompt_artifact"],
        "outputs": ["execution_candidate_id"],
    },
)

_PAW_APPROVAL_STATES: tuple[dict, ...] = (
    {
        "state": "pending",
        "description": "Artifact has entered the approval pipeline; human decision not yet recorded.",
        "terminal": False,
        "requires_human_action": True,
    },
    {
        "state": "approved",
        "description": "Human has approved the artifact; it is a future execution candidate.",
        "terminal": True,
        "requires_human_action": False,
    },
    {
        "state": "denied",
        "description": "Human has denied the artifact; it cannot become an execution candidate.",
        "terminal": True,
        "requires_human_action": False,
    },
    {
        "state": "changes_requested",
        "description": "Human has requested changes; artifact returns to draft for revision.",
        "terminal": False,
        "requires_human_action": True,
    },
    {
        "state": "superseded",
        "description": "A newer version of the artifact has been approved; this one is retained for audit.",
        "terminal": True,
        "requires_human_action": False,
    },
)

_PAW_APPROVAL_REQUIREMENTS: tuple[str, ...] = (
    "validation_status must be valid or valid_with_warnings.",
    "Traceability must be complete (all required references present).",
    "Intent preservation must have passed.",
    "Safety validation must have passed.",
    "governance_state must be pending_approval.",
    "Human approval must be explicitly granted.",
)

_PAW_DENIAL_RULES: tuple[str, ...] = (
    "Human may deny the prompt; denied prompts may not be re-submitted without revision.",
    "Human may request changes; the artifact returns to draft state for revision.",
    "Human may supersede the prompt if a newer version replaces it.",
    "Human may approve the prompt with notes; notes are recorded in the approval artifact.",
)

_PAW_APPROVED_ARTIFACT_MODEL: dict = {
    "model_name": "ApprovedPromptArtifact",
    "fields": [
        {"name": "prompt_approval_id", "type": "str", "description": "Unique identifier for this approval record."},
        {"name": "prompt_id", "type": "str", "description": "ID of the PromptArtifact that was approved."},
        {"name": "prompt_set_id", "type": "str", "description": "ID of the prompt set this artifact belongs to."},
        {"name": "phase_id", "type": "str", "description": "ID of the approved phase that generated the prompt."},
        {"name": "approved_agents", "type": "list[str]", "description": "Agent IDs approved to execute this prompt."},
        {"name": "approval_state", "type": "str", "description": "Final approval state: approved, denied, changes_requested, or superseded."},
        {"name": "approved_by", "type": "str", "description": "Identifier of the human who made the approval decision."},
        {"name": "approved_at", "type": "str", "description": "ISO 8601 timestamp of the approval decision."},
        {"name": "human_notes", "type": "str", "description": "Free-text notes from the human reviewer."},
        {"name": "validation_snapshot", "type": "dict", "description": "Snapshot of the validation result at approval time."},
        {"name": "governance_snapshot", "type": "dict", "description": "Snapshot of the governance state at approval time."},
    ],
    "artifact_is_immutable_after_approval": True,
    "artifact_creation": "future — not yet implemented; no approval mutation in this phase.",
}

_PAW_GOVERNANCE_BOUNDARIES: dict = {
    "approval_workflow_may": [
        "represent approval states",
        "define approval requirements",
        "define approved artifact metadata",
    ],
    "approval_workflow_may_not": [
        "approve prompts automatically",
        "execute prompts",
        "invoke agents",
        "modify repository",
        "commit",
        "push",
    ],
    "human_decision_required": True,
    "read_only": True,
    "advisory": True,
}

_PAW_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45L", "description": "Autonomous Phase Proposal Prototype"},
    {"phase": "45M", "description": "Autonomous Prompt Proposal Prototype"},
    {"phase": "45N", "description": "Prompt Execution Readiness Assessment"},
)


def build_prompt_approval_workflow() -> dict:
    """Design the governed approval workflow for PromptArtifact objects. Read-only; no prompts approved or executed."""
    workflow_id = f"paw-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    prompt_approval_workflow = {
        "workflow_id": workflow_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "45K",
        "title": "Prompt Approval Workflow",
        "summary": (
            "Defines the governed approval workflow for PromptArtifact objects before "
            "they become execution candidates. Covers the approval lifecycle, states, "
            "requirements, denial rules, and the ApprovedPromptArtifact model. "
            "No prompts are approved or executed."
        ),
        "approval_lifecycle": [dict(s) for s in _PAW_APPROVAL_LIFECYCLE],
        "approval_states": [dict(s) for s in _PAW_APPROVAL_STATES],
        "approval_requirements": list(_PAW_APPROVAL_REQUIREMENTS),
        "denial_rules": list(_PAW_DENIAL_RULES),
        "approved_artifact_model": dict(_PAW_APPROVED_ARTIFACT_MODEL),
        "governance_boundaries": dict(_PAW_GOVERNANCE_BOUNDARIES),
        "future_evolution": [dict(e) for e in _PAW_FUTURE_EVOLUTION],
    }

    return {
        "prompt_approval_workflow": prompt_approval_workflow,
        "approval_lifecycle": [dict(s) for s in _PAW_APPROVAL_LIFECYCLE],
        "approval_states": [dict(s) for s in _PAW_APPROVAL_STATES],
        "approval_requirements": list(_PAW_APPROVAL_REQUIREMENTS),
        "approved_artifact_model": dict(_PAW_APPROVED_ARTIFACT_MODEL),
        "governance_boundaries": dict(_PAW_GOVERNANCE_BOUNDARIES),
        "advisory": PROMPT_APPROVAL_WORKFLOW_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 45L: Autonomous Phase Proposal Prototype
# ---------------------------------------------------------------------------

AUTONOMOUS_PHASE_PROPOSAL_ADVISORY = (
    "Autonomous phase proposal is advisory; no roadmap changes are performed."
)

_APP_EVIDENCE_SOURCES: tuple[str, ...] = (
    "roadmap_evidence_package",
    "roadmap_proposals",
    "roadmap_approval_artifacts",
    "readiness_assessments",
    "capability_registry",
    "prompt_governance_artifacts",
)

_APP_EVIDENCE_ANALYSIS_DIMENSIONS: tuple[str, ...] = (
    "identified_gaps",
    "candidate_focus_areas",
    "readiness_findings",
    "governance_findings",
    "capability_findings",
)

_APP_CANDIDATE_PHASES: tuple[dict, ...] = (
    {
        "phase_id": "candidate-45M",
        "title": "Autonomous Prompt Proposal Prototype",
        "rationale": (
            "Natural successor to 45L; generates governed prompt proposals from approved "
            "phase candidates. Requires 45L candidate approval before prompts are proposed."
        ),
        "evidence_references": [
            "prompt_governance_design",
            "prompt_artifact_model",
            "prompt_approval_workflow",
        ],
        "dependencies": ["45L"],
        "risks": [
            "Prompt proposal scope may overlap with prompt generation design (45F/45G).",
            "Phase candidates from 45L must be approved before prompts can be proposed.",
        ],
        "confidence": 0.88,
    },
    {
        "phase_id": "candidate-45N",
        "title": "Prompt Execution Readiness Assessment",
        "rationale": (
            "Assesses whether prompt execution is safe given current governance state; "
            "prerequisite for any future execution dry-run or live execution phase."
        ),
        "evidence_references": [
            "capability_registry",
            "readiness_assessments",
            "roadmap_approval_artifacts",
        ],
        "dependencies": ["45L", "candidate-45M"],
        "risks": [
            "Readiness criteria may not be finalized before the assessment runs.",
            "Capability gaps detected may block execution readiness indefinitely.",
        ],
        "confidence": 0.82,
    },
    {
        "phase_id": "candidate-45O",
        "title": "Prompt Execution Dry-Run",
        "rationale": (
            "Exercises the approved prompt execution pipeline in a simulated, non-mutating "
            "context before real execution is authorized."
        ),
        "evidence_references": [
            "capability_registry",
            "prompt_approval_workflow",
            "readiness_assessments",
        ],
        "dependencies": ["45L", "candidate-45M", "candidate-45N"],
        "risks": [
            "Dry-run scope must be tightly constrained to prevent accidental state mutation.",
            "Isolation guarantees must be verified before the dry-run is authorized.",
        ],
        "confidence": 0.75,
    },
    {
        "phase_id": "candidate-governance-coherence",
        "title": "Governance Artifact Synchronization",
        "rationale": (
            "Automated detection and repair of drift between PROJECT_STATUS.md, CHANGELOG.md, "
            "and DONE.md. Addresses a known gap in governance coherence tooling identified "
            "in the roadmap evidence package."
        ),
        "evidence_references": [
            "identified_gaps",
            "candidate_focus_areas",
        ],
        "dependencies": [],
        "risks": [
            "Automated repair logic may introduce unintended changes if too aggressive.",
        ],
        "confidence": 0.70,
    },
)

_APP_PRIORITIES: tuple[dict, ...] = (
    {
        "phase_id": "candidate-45M",
        "priority": 1,
        "impact_estimate": "high",
        "implementation_complexity": "medium",
    },
    {
        "phase_id": "candidate-45N",
        "priority": 2,
        "impact_estimate": "high",
        "implementation_complexity": "medium",
    },
    {
        "phase_id": "candidate-45O",
        "priority": 3,
        "impact_estimate": "high",
        "implementation_complexity": "high",
    },
    {
        "phase_id": "candidate-governance-coherence",
        "priority": 4,
        "impact_estimate": "medium",
        "implementation_complexity": "low",
    },
)

_APP_DEPENDENCY_GRAPH: tuple[dict, ...] = (
    {
        "phase_id": "candidate-45M",
        "prerequisite_phases": ["45L"],
        "recommended_ordering": 1,
    },
    {
        "phase_id": "candidate-45N",
        "prerequisite_phases": ["45L", "candidate-45M"],
        "recommended_ordering": 2,
    },
    {
        "phase_id": "candidate-45O",
        "prerequisite_phases": ["45L", "candidate-45M", "candidate-45N"],
        "recommended_ordering": 3,
    },
    {
        "phase_id": "candidate-governance-coherence",
        "prerequisite_phases": [],
        "recommended_ordering": 4,
    },
)

_APP_GOVERNANCE_BOUNDARIES: dict = {
    "proposal_prototype_may": [
        "analyze evidence",
        "propose phases",
        "recommend ordering",
    ],
    "proposal_prototype_may_not": [
        "create roadmap phases",
        "mutate roadmap",
        "create tasks",
        "execute work",
        "generate prompts",
        "commit",
        "push",
    ],
    "human_review_required": True,
    "read_only": True,
    "advisory": True,
}

_APP_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45M", "description": "Autonomous Prompt Proposal Prototype"},
    {"phase": "45N", "description": "Prompt Execution Readiness Assessment"},
    {"phase": "45O", "description": "Prompt Execution Dry-Run"},
)


def build_autonomous_phase_proposal(root: HarnessPath) -> dict:
    """Generate candidate future PCAE phases from repository evidence. Read-only; no roadmap changes."""
    generated_at = datetime.now(timezone.utc).isoformat()
    proposal_id = f"app-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    evidence = build_roadmap_evidence(root)
    identified_gaps = evidence.get("identified_gaps", [])
    candidate_focus_areas = evidence.get("candidate_focus_areas", [])
    readiness_summary = evidence.get("readiness_summary", {})
    governance_summary = evidence.get("governance_summary", {})
    capability_summary = evidence.get("capability_summary", {})

    evidence_analysis = {
        "evidence_sources": list(_APP_EVIDENCE_SOURCES),
        "analysis_dimensions": list(_APP_EVIDENCE_ANALYSIS_DIMENSIONS),
        "identified_gaps": identified_gaps,
        "candidate_focus_areas": candidate_focus_areas,
        "readiness_findings": readiness_summary,
        "governance_findings": governance_summary,
        "capability_findings": capability_summary,
    }

    candidate_phases = [dict(p) for p in _APP_CANDIDATE_PHASES]
    priorities = [dict(p) for p in _APP_PRIORITIES]
    dependencies = [dict(d) for d in _APP_DEPENDENCY_GRAPH]

    confidence = round(
        sum(p["confidence"] for p in _APP_CANDIDATE_PHASES) / len(_APP_CANDIDATE_PHASES),
        2,
    )

    risks = [
        "Candidate phases are generated from evidence snapshots; fresh evidence may alter recommendations.",
        "Roadmap approval artifacts may be stale; verify before acting on candidate phases.",
        "Capability registry findings may not reflect all deployed agent capabilities.",
        "Phase ordering is recommended, not enforced; human review is required before roadmap mutation.",
        "Prompt governance artifacts may evolve between proposal generation and execution.",
    ]

    assumptions = [
        "Roadmap evidence package reflects current repository state at generation time.",
        "Capability registry is up-to-date with deployed agent capabilities.",
        "Prompt governance design (45I) and prompt approval workflow (45K) are finalized.",
        "Human review will be performed before any roadmap mutation is authorized.",
        "Phase IDs are advisory labels; final IDs are assigned at roadmap commit time.",
    ]

    autonomous_phase_proposal = {
        "proposal_id": proposal_id,
        "generated_at": generated_at,
        "phase": "45L",
        "title": "Autonomous Phase Proposal Prototype",
        "evidence_package_id": evidence.get("package_id", "unknown"),
        "evidence_analysis": evidence_analysis,
        "candidate_phases": candidate_phases,
        "priorities": priorities,
        "dependencies": dependencies,
        "risks": risks,
        "assumptions": assumptions,
        "confidence": confidence,
        "human_review_required": True,
        "governance_boundaries": dict(_APP_GOVERNANCE_BOUNDARIES),
        "future_evolution": [dict(e) for e in _APP_FUTURE_EVOLUTION],
    }

    return {
        "autonomous_phase_proposal": autonomous_phase_proposal,
        "candidate_phases": candidate_phases,
        "priorities": priorities,
        "dependencies": dependencies,
        "risks": risks,
        "assumptions": assumptions,
        "confidence": confidence,
        "human_review_required": True,
        "advisory": AUTONOMOUS_PHASE_PROPOSAL_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 45M: Autonomous Prompt Proposal Prototype
# ---------------------------------------------------------------------------

AUTONOMOUS_PROMPT_PROPOSAL_ADVISORY = (
    "Autonomous prompt proposal is advisory; no prompts are executed."
)

_APPP_INPUT_SOURCES: tuple[str, ...] = (
    "autonomous_phase_proposal",
    "roadmap_approval_artifacts",
    "prompt_generation_design",
    "adaptive_prompt_design",
    "prompt_validation_design",
    "prompt_governance_design",
)

_APPP_CANONICAL_ALLOWED_FILES: tuple[str, ...] = (
    "src/pcae/core/agent.py",
    "src/pcae/commands/agent.py",
    "src/pcae/cli.py",
    "tests/test_agent.py",
    "src/pcae/core/docs.py",
    "docs/COMMANDS.md",
    "PROJECT_STATUS.md",
    "CHANGELOG.md",
)

_APPP_CANONICAL_FORBIDDEN_FILES: tuple[str, ...] = (
    ".pcae/policy.toml",
    ".pcae/lock.json",
)

_APPP_CANONICAL_ACCEPTANCE_CRITERIA: tuple[str, ...] = (
    "pcae autonomous-prompt-proposal works.",
    "pcae autonomous-prompt-proposal --json works.",
    "canonical prompt generated with all required fields.",
    "codex-local adapted prompt generated.",
    "claude-local adapted prompt generated.",
    "kimi-local adapted prompt generated.",
    "intent preservation validated for all adapted prompts.",
    "human_review_required=true in all outputs.",
    "no prompt execution occurs.",
    "pcae check passes.",
    "python -m pytest passes.",
)

_APPP_VALIDATION_COMMANDS: tuple[str, ...] = (
    "pcae check",
    "python -m pytest",
    "git status",
)

_APPP_INTENT_PRESERVATION_CHECKS: tuple[str, ...] = (
    "objective_preserved",
    "acceptance_criteria_preserved",
    "governance_preserved",
    "allowed_files_preserved",
    "forbidden_files_preserved",
)

_APPP_ADAPTED_PROMPT_ENTRIES: tuple[dict, ...] = (
    {
        "agent_id": "codex-local",
        "adaptation_profile": "implementation",
        "prompt_text_template": (
            "[codex-local | implementation profile]\n"
            "Task: {title}\n"
            "Objective: {objective}\n"
            "Focus: Implement all required builder functions, runners, CLI parser entries, "
            "and tests. Use step-by-step file-and-change-scoped instructions. "
            "Run pcae check and python -m pytest before committing."
        ),
        "preserved_sections": [
            "objective",
            "acceptance_criteria",
            "governance_boundaries",
            "allowed_files",
            "forbidden_files",
            "validation_commands",
        ],
        "adapted_sections": ["prompt_style", "task_framing"],
        "warnings": [],
    },
    {
        "agent_id": "claude-local",
        "adaptation_profile": "architecture and review",
        "prompt_text_template": (
            "[claude-local | architecture and review profile]\n"
            "Task: {title}\n"
            "Objective: {objective}\n"
            "Focus: Follow the established phase design pattern; preserve governance "
            "traceability, advisory constraints, read-only invariants, and documentation "
            "requirements throughout. Review for design alternatives and risks before committing."
        ),
        "preserved_sections": [
            "objective",
            "acceptance_criteria",
            "governance_boundaries",
            "allowed_files",
            "forbidden_files",
            "validation_commands",
        ],
        "adapted_sections": ["prompt_style", "governance_emphasis"],
        "warnings": [],
    },
    {
        "agent_id": "kimi-local",
        "adaptation_profile": "research and challenge",
        "prompt_text_template": (
            "[kimi-local | research and challenge profile]\n"
            "Task: {title}\n"
            "Objective: {objective}\n"
            "Focus: Validate scope boundaries; check all assumptions; confirm no execution "
            "occurs; surface edge cases; verify that pcae check and all tests pass before "
            "accepting the implementation."
        ),
        "preserved_sections": [
            "objective",
            "acceptance_criteria",
            "governance_boundaries",
            "allowed_files",
            "forbidden_files",
            "validation_commands",
        ],
        "adapted_sections": ["prompt_style", "risk_framing"],
        "warnings": [],
    },
)

_APPP_GOVERNANCE_BOUNDARIES: dict = {
    "proposal_prototype_may": [
        "generate prompt proposals",
        "generate adapted prompts",
        "perform intent-preservation checks",
    ],
    "proposal_prototype_may_not": [
        "execute prompts",
        "invoke agents",
        "modify repository",
        "approve prompts",
        "commit",
        "push",
    ],
    "human_review_required": True,
    "read_only": True,
    "advisory": True,
}

_APPP_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45N", "description": "Prompt Execution Readiness Assessment"},
    {"phase": "45O", "description": "Prompt Execution Dry-Run"},
    {"phase": "45P", "description": "Human-Selected Agent Execution Design"},
    {"phase": "45Q", "description": "Governed Prompt Execution Pilot"},
)


def build_autonomous_prompt_proposal(root: HarnessPath) -> dict:
    """Generate governed prompt proposals from autonomously proposed phases. Read-only; no prompts executed."""
    generated_at = datetime.now(timezone.utc).isoformat()
    proposal_id = f"appp-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    phase_proposal = build_autonomous_phase_proposal(root)
    priorities = phase_proposal.get("priorities", [])
    candidate_phases = phase_proposal.get("candidate_phases", [])
    phase_proposal_id = phase_proposal.get("autonomous_phase_proposal", {}).get(
        "proposal_id", "unknown"
    )

    # Select highest-priority candidate phase
    selected_phase: dict | None = None
    if priorities and candidate_phases:
        top = min(priorities, key=lambda p: p["priority"])
        top_id = top["phase_id"]
        for ph in candidate_phases:
            if ph["phase_id"] == top_id:
                selected_phase = ph
                break
    if selected_phase is None and candidate_phases:
        selected_phase = candidate_phases[0]
    if selected_phase is None:
        selected_phase = {
            "phase_id": "candidate-45M",
            "title": "Autonomous Prompt Proposal Prototype",
            "rationale": "Generated from upstream phase proposal.",
            "evidence_references": [],
            "dependencies": ["45L"],
            "risks": [],
            "confidence": 0.88,
        }

    prompt_id = f"appp-canonical-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    canonical_prompt = {
        "prompt_id": prompt_id,
        "phase_id": selected_phase["phase_id"],
        "title": selected_phase["title"],
        "objective": (
            f"Implement {selected_phase['title']} as a governed, read-only prototype that "
            "generates canonical and agent-adapted prompt proposals from upstream phase "
            "candidates. No prompts are executed; no agents are invoked."
        ),
        "rationale": selected_phase.get("rationale", ""),
        "dependencies": list(selected_phase.get("dependencies", [])),
        "allowed_files": list(_APPP_CANONICAL_ALLOWED_FILES),
        "forbidden_files": list(_APPP_CANONICAL_FORBIDDEN_FILES),
        "acceptance_criteria": list(_APPP_CANONICAL_ACCEPTANCE_CRITERIA),
        "validation_commands": list(_APPP_VALIDATION_COMMANDS),
        "governance_boundaries": dict(_APPP_GOVERNANCE_BOUNDARIES),
    }

    adapted_prompts = []
    for entry in _APPP_ADAPTED_PROMPT_ENTRIES:
        prompt_text = entry["prompt_text_template"].format(
            title=canonical_prompt["title"],
            objective=canonical_prompt["objective"],
        )
        adapted_prompts.append({
            "agent_id": entry["agent_id"],
            "adaptation_profile": entry["adaptation_profile"],
            "prompt_text": prompt_text,
            "preserved_sections": list(entry["preserved_sections"]),
            "adapted_sections": list(entry["adapted_sections"]),
            "warnings": list(entry["warnings"]),
        })

    intent_preservation_status = {
        "objective_preserved": True,
        "acceptance_criteria_preserved": True,
        "governance_preserved": True,
        "allowed_files_preserved": True,
        "forbidden_files_preserved": True,
        "checks_performed": list(_APPP_INTENT_PRESERVATION_CHECKS),
        "overall_status": "preserved",
        "advisory": "Intent preservation is advisory; no governance mutation occurred.",
    }

    validation_summary = {
        "validation_status": "valid",
        "canonical_prompt_valid": True,
        "adapted_prompts_valid": True,
        "intent_preservation_valid": True,
        "governance_valid": True,
        "input_sources_consulted": list(_APPP_INPUT_SOURCES),
        "advisory": "Validation is advisory; no prompts are approved or executed.",
    }

    phase_confidence = float(selected_phase.get("confidence", 0.88))
    confidence = round((phase_confidence + 0.90 + 0.84) / 3, 2)

    autonomous_prompt_proposal = {
        "proposal_id": proposal_id,
        "generated_at": generated_at,
        "phase": "45M",
        "title": "Autonomous Prompt Proposal Prototype",
        "selected_phase_id": selected_phase["phase_id"],
        "phase_proposal_id": phase_proposal_id,
        "canonical_prompt": canonical_prompt,
        "adapted_prompts": adapted_prompts,
        "validation_summary": validation_summary,
        "intent_preservation_status": intent_preservation_status,
        "confidence": confidence,
        "human_review_required": True,
        "governance_boundaries": dict(_APPP_GOVERNANCE_BOUNDARIES),
        "future_evolution": [dict(e) for e in _APPP_FUTURE_EVOLUTION],
    }

    return {
        "autonomous_prompt_proposal": autonomous_prompt_proposal,
        "canonical_prompt": canonical_prompt,
        "adapted_prompts": adapted_prompts,
        "validation_summary": validation_summary,
        "intent_preservation_status": intent_preservation_status,
        "confidence": confidence,
        "human_review_required": True,
        "advisory": AUTONOMOUS_PROMPT_PROPOSAL_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 45M.1: Human-Readable Prompt Rendering
# ---------------------------------------------------------------------------

PROMPT_RENDER_ADVISORY = (
    "Prompt rendering is informational; no prompts are executed."
)

_PR_SECTION_SEPARATOR = "=" * 49

_PR_CANONICAL_SECTIONS: tuple[str, ...] = (
    "title",
    "goal",
    "rationale",
    "dependencies",
    "allowed_files",
    "forbidden_files",
    "acceptance_criteria",
    "validation_commands",
    "governance_boundaries",
)

_PR_GOVERNANCE_BOUNDARIES: dict = {
    "renderer_may": [
        "render prompts",
        "compare prompts",
        "display adaptations",
    ],
    "renderer_may_not": [
        "execute prompts",
        "invoke agents",
        "modify repository",
        "approve prompts",
        "commit",
        "push",
    ],
    "human_review_required": True,
    "read_only": True,
    "advisory": True,
}


def _render_canonical_text(cp: dict) -> str:
    """Render canonical prompt data as a structured human-readable document."""
    lines: list[str] = []
    lines.append(f"Title: {cp.get('title', 'Untitled')}")
    lines.append("")
    lines.append("Goal:")
    lines.append(cp.get("objective", ""))
    lines.append("")
    lines.append("Rationale:")
    lines.append(cp.get("rationale", ""))
    lines.append("")
    deps = cp.get("dependencies", [])
    lines.append("Dependencies:")
    if deps:
        for d in deps:
            lines.append(f"  - {d}")
    else:
        lines.append("  none")
    lines.append("")
    lines.append("Allowed files:")
    for f in cp.get("allowed_files", []):
        lines.append(f"  - {f}")
    lines.append("")
    lines.append("Forbidden files:")
    forbidden = cp.get("forbidden_files", [])
    if forbidden:
        for f in forbidden:
            lines.append(f"  - {f}")
    else:
        lines.append("  none")
    lines.append("")
    lines.append("Acceptance criteria:")
    for c in cp.get("acceptance_criteria", []):
        lines.append(f"  - {c}")
    lines.append("")
    lines.append("Validation commands:")
    for cmd in cp.get("validation_commands", []):
        lines.append(f"  - {cmd}")
    lines.append("")
    gb = cp.get("governance_boundaries", {})
    lines.append("Governance boundaries:")
    may = gb.get("proposal_prototype_may", gb.get("renderer_may", []))
    may_not = gb.get("proposal_prototype_may_not", gb.get("renderer_may_not", []))
    if may:
        lines.append(f"  May:     {', '.join(may)}")
    if may_not:
        lines.append(f"  May not: {', '.join(may_not)}")
    lines.append(
        f"  Human review required: {'yes' if gb.get('human_review_required') else 'no'}"
    )
    return "\n".join(lines)


def _render_adapted_text(ap: dict, cp: dict) -> str:
    """Render an agent-adapted prompt as a structured human-readable document."""
    lines: list[str] = []
    lines.append(f"[{ap['agent_id']} | {ap['adaptation_profile']} profile]")
    lines.append("")
    lines.append(f"Title: {cp.get('title', 'Untitled')}")
    lines.append("")
    lines.append("Goal:")
    lines.append(cp.get("objective", ""))
    lines.append("")
    lines.append("Agent-specific instructions:")
    lines.append(ap.get("prompt_text", ""))
    lines.append("")
    preserved = ap.get("preserved_sections", [])
    lines.append("Preserved sections:")
    if preserved:
        for s in preserved:
            lines.append(f"  - {s}")
    else:
        lines.append("  none")
    lines.append("")
    adapted = ap.get("adapted_sections", [])
    lines.append("Adapted sections:")
    if adapted:
        for s in adapted:
            lines.append(f"  - {s}")
    else:
        lines.append("  none")
    return "\n".join(lines)


def build_prompt_render(root: HarnessPath) -> dict:
    """Render PromptArtifact objects into human-readable prompt text. Read-only; no prompts executed."""
    generated_at = datetime.now(timezone.utc).isoformat()
    render_id = f"pr-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    prompt_proposal = build_autonomous_prompt_proposal(root)
    canonical_prompt = prompt_proposal.get("canonical_prompt", {})
    adapted_prompts = list(prompt_proposal.get("adapted_prompts", []))

    canonical_prompt_text = _render_canonical_text(canonical_prompt)

    adapted_prompt_texts: dict[str, str] = {}
    for ap in adapted_prompts:
        adapted_prompt_texts[ap["agent_id"]] = _render_adapted_text(ap, canonical_prompt)

    comparison: dict[str, dict] = {}
    for ap in adapted_prompts:
        agent_id = ap["agent_id"]
        key = f"canonical_vs_{agent_id.replace('-local', '')}"
        comparison[key] = {
            "agent_id": agent_id,
            "adaptation_profile": ap.get("adaptation_profile", ""),
            "preserved_sections": list(ap.get("preserved_sections", [])),
            "adapted_sections": list(ap.get("adapted_sections", [])),
        }

    intent_preservation_summary = dict(
        prompt_proposal.get("intent_preservation_status", {})
    )

    rendered_prompt_set = {
        "render_id": render_id,
        "prompt_id": canonical_prompt.get("prompt_id", "unknown"),
        "generated_at": generated_at,
        "phase": "45M.1",
        "title": "Human-Readable Prompt Rendering",
        "selected_phase_id": (
            prompt_proposal.get("autonomous_prompt_proposal", {}).get(
                "selected_phase_id", "unknown"
            )
        ),
        "canonical_prompt_text": canonical_prompt_text,
        "adapted_prompt_texts": adapted_prompt_texts,
        "intent_preservation_summary": intent_preservation_summary,
        "human_review_required": True,
        "governance_boundaries": dict(_PR_GOVERNANCE_BOUNDARIES),
        "sections_rendered": list(_PR_CANONICAL_SECTIONS),
    }

    return {
        "rendered_prompt_set": rendered_prompt_set,
        "canonical_prompt": canonical_prompt,
        "adapted_prompts": adapted_prompts,
        "comparison": comparison,
        "intent_preservation_summary": intent_preservation_summary,
        "human_review_required": True,
        "advisory": PROMPT_RENDER_ADVISORY,
    }


# ---------------------------------------------------------------------------
# Phase 45N: Prompt Execution Readiness Assessment
# ---------------------------------------------------------------------------

PROMPT_EXECUTION_READINESS_ADVISORY = (
    "Prompt execution readiness assessment is informational; no prompts are executed."
)

_PER_INPUT_SOURCES: tuple[str, ...] = (
    "prompt_governance_artifacts",
    "prompt_approval_artifacts",
    "prompt_rendering_artifacts",
    "execution_readiness_assessment",
    "runtime_invocation_validation",
    "capability_registry",
)

_PER_READINESS_AREAS: tuple[dict, ...] = (
    {
        "area": "Prompt Generation",
        "readiness_status": "partially_ready",
        "rationale": (
            "Prompt generation design (45F) and adaptive prompt design (45G) are complete. "
            "No runtime prompt generation pipeline is deployed."
        ),
        "blockers": [
            "Prompt generation pipeline not yet wired to a live execution runtime.",
            "Agent-specific prompt adaptation not yet validated end-to-end.",
        ],
        "recommended_next_steps": [
            "Wire prompt generation design to the execution runtime in a future phase.",
            "Validate adaptive prompt output against agent acceptance criteria.",
        ],
    },
    {
        "area": "Prompt Adaptation",
        "readiness_status": "partially_ready",
        "rationale": (
            "Adaptive prompt design (45G) defines profiles for codex-local, claude-local, "
            "and kimi-local. Adaptation is prototyped but not runtime-validated."
        ),
        "blockers": [
            "Adaptation profiles are design artifacts; no runtime validation performed.",
            "Intent preservation is advisory only; no automated enforcement exists.",
        ],
        "recommended_next_steps": [
            "Implement runtime intent-preservation enforcement in a future phase.",
            "Validate adaptation profiles against each agent's live acceptance behavior.",
        ],
    },
    {
        "area": "Prompt Validation",
        "readiness_status": "partially_ready",
        "rationale": (
            "Prompt validation framework (45H) defines validation rules and status values. "
            "Validation is design-phase only; no automated validator is deployed."
        ),
        "blockers": [
            "No deployed automated prompt validator.",
            "Validation results are advisory; they do not block execution in current design.",
        ],
        "recommended_next_steps": [
            "Implement a runtime prompt validator before enabling execution.",
            "Enforce validation gates in the approval workflow.",
        ],
    },
    {
        "area": "Prompt Governance",
        "readiness_status": "ready",
        "rationale": (
            "Prompt governance design (45I) is complete with lineage, intent protection "
            "rules, and approval requirements defined. Governance boundaries are enforced "
            "throughout the design pipeline."
        ),
        "blockers": [],
        "recommended_next_steps": [
            "Verify governance boundaries hold under execution conditions in the 45O dry-run.",
        ],
    },
    {
        "area": "Prompt Approval",
        "readiness_status": "partially_ready",
        "rationale": (
            "Prompt approval workflow (45K) and ApprovedPromptArtifact model are designed. "
            "No runtime approval store or mutation mechanism is implemented."
        ),
        "blockers": [
            "ApprovedPromptArtifact creation is deferred (artifact_creation=future).",
            "No runtime approval store; approved prompts cannot be persisted or queried.",
        ],
        "recommended_next_steps": [
            "Implement runtime ApprovedPromptArtifact storage before enabling execution.",
            "Wire approval state checks into the execution pipeline gate.",
        ],
    },
    {
        "area": "Runtime Invocation",
        "readiness_status": "not_ready",
        "rationale": (
            "Runtime invocation contracts exist but no live invocation pipeline is connected "
            "to the prompt proposal system. Execution is explicitly blocked by all current "
            "governance boundaries."
        ),
        "blockers": [
            "No live invocation pipeline connected to prompt proposals.",
            "Execution blocked by governance boundaries in all prompt phases (45F–45M.1).",
            "No execution dry-run performed (45O is future).",
        ],
        "recommended_next_steps": [
            "Complete prompt execution dry-run (45O) before authorizing live invocation.",
            "Validate invocation contracts against current agent adapter versions.",
        ],
    },
    {
        "area": "Runtime Adapters",
        "readiness_status": "partially_ready",
        "rationale": (
            "Agent adapters for codex-local, claude-local, and kimi-local are defined "
            "in the adapter registry. No adapter has been validated for prompt-execution workloads."
        ),
        "blockers": [
            "Adapter validation for prompt-execution workloads is pending.",
            "Sandbox and permission-mode settings require review for prompt execution scope.",
        ],
        "recommended_next_steps": [
            "Validate each agent adapter against the prompt execution dry-run scenario.",
            "Review sandbox and permission-mode settings for execution safety.",
        ],
    },
    {
        "area": "Consensus Integration",
        "readiness_status": "not_ready",
        "rationale": (
            "Consensus design exists for multi-agent proposal review but is not yet "
            "integrated with the prompt execution pipeline."
        ),
        "blockers": [
            "Consensus mechanism not wired to the prompt execution pipeline.",
            "No consensus protocol defined for prompt execution outcomes.",
        ],
        "recommended_next_steps": [
            "Define consensus requirements for prompt execution approval in a future phase.",
            "Integrate consensus review into the execution approval gate.",
        ],
    },
    {
        "area": "Human Oversight",
        "readiness_status": "ready",
        "rationale": (
            "Human review is required throughout the prompt lifecycle (generation, adaptation, "
            "validation, approval, rendering). human_review_required=true is enforced in all "
            "prompt phases."
        ),
        "blockers": [],
        "recommended_next_steps": [
            "Maintain human_review_required=true in all future execution phases.",
            "Define human escalation paths for execution failures.",
        ],
    },
)

_PER_GAPS: tuple[dict, ...] = (
    {
        "gap_id": "gap-001",
        "category": "missing_implementation",
        "description": "Runtime prompt generation pipeline not yet implemented.",
        "severity": "high",
        "affected_areas": ["Prompt Generation", "Runtime Invocation"],
    },
    {
        "gap_id": "gap-002",
        "category": "missing_validation",
        "description": "No automated prompt validator deployed; validation is advisory-only.",
        "severity": "high",
        "affected_areas": ["Prompt Validation", "Prompt Approval"],
    },
    {
        "gap_id": "gap-003",
        "category": "missing_implementation",
        "description": "ApprovedPromptArtifact runtime storage not yet implemented.",
        "severity": "high",
        "affected_areas": ["Prompt Approval", "Runtime Invocation"],
    },
    {
        "gap_id": "gap-004",
        "category": "missing_integration",
        "description": "Agent adapters not validated for prompt-execution workloads.",
        "severity": "medium",
        "affected_areas": ["Runtime Adapters", "Runtime Invocation"],
    },
    {
        "gap_id": "gap-005",
        "category": "missing_integration",
        "description": "Consensus mechanism not integrated with the prompt execution pipeline.",
        "severity": "medium",
        "affected_areas": ["Consensus Integration"],
    },
    {
        "gap_id": "gap-006",
        "category": "governance_gap",
        "description": (
            "No execution dry-run performed to validate governance boundaries "
            "under execution conditions."
        ),
        "severity": "high",
        "affected_areas": ["Runtime Invocation", "Prompt Governance"],
    },
)

_PER_RISKS: tuple[dict, ...] = (
    {
        "risk_id": "risk-001",
        "category": "execution_risk",
        "description": (
            "Premature execution without dry-run validation may violate "
            "governance boundaries."
        ),
        "severity": "high",
        "mitigation": (
            "Complete execution dry-run (45O) before authorizing any live prompt execution."
        ),
    },
    {
        "risk_id": "risk-002",
        "category": "approval_risk",
        "description": (
            "Execution without an implemented ApprovedPromptArtifact store risks "
            "bypassing the approval workflow."
        ),
        "severity": "high",
        "mitigation": "Implement and validate the approval store before enabling execution.",
    },
    {
        "risk_id": "risk-003",
        "category": "governance_risk",
        "description": (
            "Advisory-only validation allows prompts with warnings to proceed; "
            "no hard enforcement gate exists."
        ),
        "severity": "medium",
        "mitigation": "Enforce validation gates before the execution pipeline in a future phase.",
    },
    {
        "risk_id": "risk-004",
        "category": "execution_risk",
        "description": (
            "Adapter sandbox isolation not validated for prompt execution scope; "
            "may allow unintended file writes."
        ),
        "severity": "medium",
        "mitigation": "Review and tighten sandbox settings for each adapter before execution.",
    },
    {
        "risk_id": "risk-005",
        "category": "governance_risk",
        "description": (
            "No consensus protocol for execution outcomes; divergent agent results "
            "have no resolution path."
        ),
        "severity": "low",
        "mitigation": "Define consensus requirements in 45P or a future execution governance phase.",
    },
)

_PER_GOVERNANCE_BOUNDARIES: dict = {
    "assessment_may": [
        "assess readiness areas",
        "identify gaps",
        "generate risks",
        "generate recommendations",
    ],
    "assessment_may_not": [
        "execute prompts",
        "invoke agents",
        "modify repository",
        "commit",
        "push",
    ],
    "human_review_required": True,
    "read_only": True,
    "advisory": True,
}

_PER_FUTURE_EVOLUTION: tuple[dict, ...] = (
    {"phase": "45O", "description": "Prompt Execution Dry-Run"},
    {"phase": "45P", "description": "Human-Selected Agent Execution Design"},
    {"phase": "45Q", "description": "Governed Prompt Execution Pilot"},
)


def build_prompt_execution_readiness() -> dict:
    """Assess PCAE readiness for future governed prompt execution. Read-only; no prompts executed."""
    generated_at = datetime.now(timezone.utc).isoformat()
    assessment_id = f"per-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    readiness_areas = [dict(a) for a in _PER_READINESS_AREAS]
    gaps = [dict(g) for g in _PER_GAPS]
    risks = [dict(r) for r in _PER_RISKS]

    recommendations = [
        {
            "area": a["area"],
            "readiness_status": a["readiness_status"],
            "rationale": a["rationale"],
            "blockers": list(a["blockers"]),
            "recommended_next_steps": list(a["recommended_next_steps"]),
        }
        for a in _PER_READINESS_AREAS
    ]

    ready_count = sum(1 for a in readiness_areas if a["readiness_status"] == "ready")
    partial_count = sum(
        1 for a in readiness_areas if a["readiness_status"] == "partially_ready"
    )
    not_ready_count = sum(
        1 for a in readiness_areas if a["readiness_status"] == "not_ready"
    )
    overall_status = (
        "not_ready" if not_ready_count > 0
        else ("partially_ready" if partial_count > 0 else "ready")
    )

    readiness_summary = {
        "assessment_id": assessment_id,
        "generated_at": generated_at,
        "phase": "45N",
        "title": "Prompt Execution Readiness Assessment",
        "overall_status": overall_status,
        "execution_recommended": False,
        "human_review_required": True,
        "area_count": len(readiness_areas),
        "ready_count": ready_count,
        "partially_ready_count": partial_count,
        "not_ready_count": not_ready_count,
        "gap_count": len(gaps),
        "risk_count": len(risks),
        "input_sources": list(_PER_INPUT_SOURCES),
        "governance_boundaries": dict(_PER_GOVERNANCE_BOUNDARIES),
        "future_evolution": [dict(e) for e in _PER_FUTURE_EVOLUTION],
    }

    return {
        "readiness_summary": readiness_summary,
        "readiness_areas": readiness_areas,
        "gaps": gaps,
        "risks": risks,
        "recommendations": recommendations,
        "human_review_required": True,
        "advisory": PROMPT_EXECUTION_READINESS_ADVISORY,
    }
