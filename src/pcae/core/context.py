from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.check import run_checks
from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.policy import load_policy
from pcae.core.provenance import build_provenance_timeline


CONTEXT_PACK_ADVISORY = (
    "This pack reduces context size but does not relax governance constraints."
)

CONTEXT_PACK_OPERATIONAL_RULES: tuple[str, ...] = (
    "Phase prompt is authoritative; it supersedes PROJECT_STATUS.md if they conflict.",
    "PROJECT_STATUS.md is background context, not a source of truth when conflicting with the phase prompt.",
    "Do not infer stale tasks from older governance documents.",
    "Do not modify files outside the active task scope.",
    "Always run pcae check and python -m pytest before committing.",
)

CONTEXT_PACK_VALIDATION_COMMANDS: tuple[str, ...] = (
    "pcae health",
    "pcae check",
    "python -m pytest",
    "git status",
)

_PROJECT_STATUS_RELATIVE_PATH = Path("PROJECT_STATUS.md")


@dataclass(frozen=True)
class ContextPack:
    active_task: dict | None
    governance_state: dict
    orchestration_state: dict
    provenance_summary: dict
    roadmap_summary: dict
    operational_rules: tuple[str, ...]
    validation_commands: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "active_task": self.active_task,
            "advisory": self.advisory,
            "governance_state": self.governance_state,
            "operational_rules": list(self.operational_rules),
            "orchestration_state": self.orchestration_state,
            "provenance_summary": self.provenance_summary,
            "roadmap_summary": self.roadmap_summary,
            "validation_commands": list(self.validation_commands),
        }


def _parse_project_status(root: HarnessPath) -> tuple[str, list[str]]:
    path = root.join(_PROJECT_STATUS_RELATIVE_PATH)
    if not path.is_file():
        return "unknown", []
    lines = path.read_text(encoding="utf-8").splitlines()
    current_phase = "unknown"
    next_items: list[str] = []
    section: str | None = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Current Phase"):
            section = "current_phase"
            continue
        if stripped.startswith("## Next"):
            section = "next"
            continue
        if stripped.startswith("## "):
            section = None
            continue
        if section == "current_phase" and stripped and not stripped.startswith("#"):
            current_phase = stripped
            section = None
        elif section == "next" and stripped.startswith("-"):
            next_items.append(stripped)
    return current_phase, next_items


def build_context_pack(root: HarnessPath) -> ContextPack:
    health = build_health_data(root)
    check_result = run_checks(root)
    policy = load_policy(root)
    provenance = build_provenance_timeline(root)
    current_phase, next_items = _parse_project_status(root)

    lock = health["agent_lock"]
    governance_state = {
        "agent_lock_state": lock,
        "check_status": "passed" if check_result.passed else "failed",
        "health_status": health["overall_status"],
        "session_continuity": health["session_continuity"],
    }

    orchestration_state = {
        "default_agent": policy.orchestration.default_agent if policy.valid else None,
        "orchestration_policy_summary": policy.orchestration.to_dict() if policy.valid else None,
        "registered_agents": [entry.to_dict() for entry in policy.agent_registry],
    }

    latest_event = None
    if provenance.latest_event is not None:
        e = provenance.latest_event
        latest_event = {
            "event_type": e.event_type,
            "summary": e.summary,
            "timestamp": e.timestamp,
        }

    provenance_summary = {
        "event_count": provenance.event_count,
        "latest_event": latest_event,
    }

    roadmap_summary = {
        "current_phase": current_phase,
        "next": next_items,
    }

    return ContextPack(
        active_task=health["active_task"],
        governance_state=governance_state,
        orchestration_state=orchestration_state,
        provenance_summary=provenance_summary,
        roadmap_summary=roadmap_summary,
        operational_rules=CONTEXT_PACK_OPERATIONAL_RULES,
        validation_commands=CONTEXT_PACK_VALIDATION_COMMANDS,
        advisory=CONTEXT_PACK_ADVISORY,
    )
