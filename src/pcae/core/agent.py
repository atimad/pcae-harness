from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess

from pcae.core.git_status import read_git_branch
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

_ADAPTER_INSPECT_ADVISORY_BY_AGENT_TYPE: dict[str, str] = {
    "claude": CLAUDE_ADAPTER_INSPECT_ADVISORY,
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
