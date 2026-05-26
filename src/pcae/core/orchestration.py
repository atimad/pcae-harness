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


def recommend_agent(root: HarnessPath, work_type: str) -> dict:
    policy = load_policy(root)
    if not policy.valid:
        raise ValueError(policy.error or "Invalid policy.")
    registry = policy.agent_registry
    orchestration = policy.orchestration

    matches = [entry for entry in registry if work_type in entry.roles]

    if not matches:
        return {
            "work_type": work_type,
            "recommended_agent": orchestration.default_agent,
            "reason": f"No agent declares role '{work_type}'; using orchestration default.",
            "matched_role": None,
            "fallback_used": True,
        }

    chosen = matches[0]
    if len(matches) > 1:
        for entry in matches:
            if entry.agent_id == orchestration.default_agent:
                chosen = entry
                break

    return {
        "work_type": work_type,
        "recommended_agent": chosen.agent_id,
        "reason": f"Agent '{chosen.agent_id}' declares role '{work_type}'.",
        "matched_role": work_type,
        "fallback_used": False,
    }
