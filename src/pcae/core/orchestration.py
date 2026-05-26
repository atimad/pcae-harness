from __future__ import annotations

from pcae.core.paths import HarnessPath
from pcae.core.policy import AgentRegistryEntry, OrchestrationPolicy, load_policy

# Each workflow is a sequence of (role, label) pairs.
# role  – the agent registry role used for agent assignment
# label – the human-friendly work_type shown in output
_WORKFLOW_STEPS: dict[str, tuple[tuple[str, str], ...]] = {
    "documentation": (
        ("architecture", "architecture review"),
        ("documentation", "documentation"),
        ("governance", "governance validation"),
    ),
    "implementation": (
        ("implementation", "implementation"),
        ("tests", "tests"),
        ("governance", "governance validation"),
    ),
    "validation": (
        ("governance", "governance validation"),
        ("validation", "validation"),
        ("analysis", "analysis review"),
    ),
    "release": (
        ("governance", "governance validation"),
        ("validation", "provenance verification"),
        ("documentation", "release notes/documentation"),
    ),
}


def _resolve_agent(
    registry: tuple[AgentRegistryEntry, ...],
    orchestration: OrchestrationPolicy,
    role: str,
) -> dict:
    matches = [entry for entry in registry if role in entry.roles]

    if not matches:
        return {
            "recommended_agent": orchestration.default_agent,
            "reason": f"No agent declares role '{role}'; using orchestration default.",
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
        "recommended_agent": chosen.agent_id,
        "reason": f"Agent '{chosen.agent_id}' declares role '{role}'.",
        "matched_role": role,
        "fallback_used": False,
    }


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
    rec = _resolve_agent(policy.agent_registry, policy.orchestration, work_type)
    return {
        "work_type": work_type,
        "recommended_agent": rec["recommended_agent"],
        "reason": rec["reason"],
        "matched_role": rec["matched_role"],
        "fallback_used": rec["fallback_used"],
    }


def build_workflow_plan(root: HarnessPath, workflow: str) -> dict:
    policy = load_policy(root)
    if not policy.valid:
        raise ValueError(policy.error or "Invalid policy.")

    registry = policy.agent_registry
    orchestration = policy.orchestration
    steps_template = _WORKFLOW_STEPS.get(workflow)

    if steps_template is None:
        return {
            "workflow": workflow,
            "recommendation_note": (
                "Recommendations are advisory; the user may override them."
            ),
            "steps": [
                {
                    "step": 1,
                    "work_type": workflow,
                    "assigned_agent": orchestration.default_agent,
                    "recommended_agent": orchestration.default_agent,
                    "reason": (
                        f"Unknown workflow '{workflow}'; using orchestration default."
                    ),
                }
            ],
        }

    steps = []
    for i, (role, label) in enumerate(steps_template, 1):
        rec = _resolve_agent(registry, orchestration, role)
        steps.append(
            {
                "step": i,
                "work_type": label,
                "assigned_agent": rec["recommended_agent"],
                "recommended_agent": rec["recommended_agent"],
                "reason": rec["reason"],
            }
        )

    return {
        "workflow": workflow,
        "recommendation_note": (
            "Recommendations are advisory; the user may override them."
        ),
        "steps": steps,
    }


def _governance_checkpoint_for(work_type: str) -> str | None:
    if "governance" in work_type:
        return "pcae check"
    if "provenance" in work_type:
        return "pcae provenance session current"
    return None


def build_workflow_simulation(root: HarnessPath, workflow: str) -> dict:
    plan = build_workflow_plan(root, workflow)
    steps = []
    for step in plan["steps"]:
        steps.append(
            {
                "step": step["step"],
                "assigned_agent": step["assigned_agent"],
                "recommended_agent": step["recommended_agent"],
                "work_type": step["work_type"],
                "reason": step["reason"],
                "governance_checkpoint": _governance_checkpoint_for(step["work_type"]),
            }
        )

    return {
        "workflow": plan["workflow"],
        "status": "planned",
        "execution_mode": "simulation",
        "recommendation_note": plan["recommendation_note"],
        "steps": steps,
    }
