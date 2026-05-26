from __future__ import annotations

from pcae.core.paths import HarnessPath
from pcae.core.policy import OrchestrationPolicy, load_policy


def load_orchestration_policy(root: HarnessPath) -> OrchestrationPolicy:
    policy = load_policy(root)
    if not policy.valid:
        raise ValueError(policy.error or "Invalid policy.")
    return policy.orchestration


def build_orchestration_data(root: HarnessPath) -> dict:
    orchestration = load_orchestration_policy(root)
    return orchestration.to_dict()
