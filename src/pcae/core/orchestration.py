from __future__ import annotations

from pcae.core.paths import HarnessPath
from pcae.core.policy import AgentRegistryEntry, OrchestrationPolicy, load_policy


def load_orchestration_policy(root: HarnessPath) -> OrchestrationPolicy:
    policy = load_policy(root)
    if not policy.valid:
        raise ValueError(policy.error or "Invalid policy.")
    return policy.orchestration


def build_orchestration_data(root: HarnessPath) -> dict:
    orchestration = load_orchestration_policy(root)
    return orchestration.to_dict()


def load_agent_registry(root: HarnessPath) -> tuple[AgentRegistryEntry, ...]:
    policy = load_policy(root)
    if not policy.valid:
        raise ValueError(policy.error or "Invalid policy.")
    return policy.agent_registry


def build_agent_registry_data(root: HarnessPath) -> list[dict]:
    registry = load_agent_registry(root)
    return [entry.to_dict() for entry in registry]
