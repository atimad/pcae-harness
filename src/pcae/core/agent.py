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
    # Declared agents (registered for future use; not yet configured or available)
    AgentEntry(
        agent_id="kimi-local",
        agent_type="kimi",
        role="analysis",
        status=AGENT_STATUS_DECLARED,
        capabilities=(
            "code_analysis",
            "documentation",
            "research",
        ),
        preferred_workloads=("analysis", "documentation"),
    ),
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
        adapter_type=ADAPTER_TYPE_UNDECLARED,
        executable_hint=None,
        requires_manual_setup=True,
        configuration_notes="Adapter not yet declared. Configure adapter before use.",
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


def read_agent_stale_after_seconds(root: HarnessPath) -> int:
    policy = load_policy(root)
    if not policy.valid:
        raise ValueError(policy.error or "Invalid policy.")
    return policy.agent_stale_after_seconds
