from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.check import run_checks
from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.policy import load_policy
from pcae.core.provenance import build_provenance_timeline
from pcae.core.tasks import find_latest_active_task


CONTEXT_PACK_ADVISORY = (
    "Optimization reduces context size without relaxing governance constraints."
)

# ---------------------------------------------------------------------------
# Work-mode profiles
# ---------------------------------------------------------------------------

PROFILE_UNIVERSAL = "universal"
PROFILE_IMPLEMENTATION = "implementation"
PROFILE_DOCUMENTATION = "documentation"
PROFILE_VALIDATION = "validation"
PROFILE_HANDOFF = "handoff"


@dataclass(frozen=True)
class WorkModeProfile:
    profile_type: str
    emphasized_sections: tuple[str, ...]


WORK_MODE_PROFILES: dict[str, WorkModeProfile] = {
    PROFILE_UNIVERSAL: WorkModeProfile(
        profile_type=PROFILE_UNIVERSAL,
        emphasized_sections=(
            "active_task",
            "governance_state",
            "orchestration_state",
            "provenance_summary",
            "roadmap_summary",
        ),
    ),
    PROFILE_IMPLEMENTATION: WorkModeProfile(
        profile_type=PROFILE_IMPLEMENTATION,
        emphasized_sections=(
            "active_task",
            "scope_boundaries",
            "validation_commands",
            "roadmap_summary",
            "operational_rules",
        ),
    ),
    PROFILE_DOCUMENTATION: WorkModeProfile(
        profile_type=PROFILE_DOCUMENTATION,
        emphasized_sections=(
            "roadmap_summary",
            "operational_rules",
            "orchestration_state",
        ),
    ),
    PROFILE_VALIDATION: WorkModeProfile(
        profile_type=PROFILE_VALIDATION,
        emphasized_sections=(
            "governance_state",
            "validation_commands",
            "provenance_summary",
        ),
    ),
    PROFILE_HANDOFF: WorkModeProfile(
        profile_type=PROFILE_HANDOFF,
        emphasized_sections=(
            "governance_state",
            "provenance_summary",
            "bootstrap_handoff_notes",
            "orchestration_state",
        ),
    ),
}


def resolve_profile(name: str | None) -> tuple[WorkModeProfile, bool]:
    """Return (profile, is_unknown_fallback).

    Falls back to the universal profile for None or unknown names.
    The boolean is True only when an unrecognised name triggered fallback.
    """
    if name is None or name == PROFILE_UNIVERSAL:
        return WORK_MODE_PROFILES[PROFILE_UNIVERSAL], False
    if name in WORK_MODE_PROFILES:
        return WORK_MODE_PROFILES[name], False
    return WORK_MODE_PROFILES[PROFILE_UNIVERSAL], True


# ---------------------------------------------------------------------------
# Compact bootstrap prompt
# ---------------------------------------------------------------------------

BOOTSTRAP_COMPACT_ADVISORY = (
    "Bootstrap compression reduces token usage without relaxing governance constraints."
)

_STALE_CONTEXT_RULE = (
    "Phase prompt is authoritative. "
    "PROJECT_STATUS.md is background. "
    "Do not infer stale work from older docs."
)


def build_bootstrap_prompt(pack: ContextPack, profile: WorkModeProfile) -> str:
    """Return a compact governed bootstrap prompt string."""
    lines: list[str] = []

    lines.append(f"[PCAE Bootstrap | {profile.profile_type} profile]")

    if pack.active_task is not None:
        task_id = pack.active_task.get("id", "unknown")
        task_title = pack.active_task.get("title", "Untitled")
        lines.append(f"Active task: {task_id} — {task_title}")
    else:
        lines.append("Active task: none")

    gs = pack.governance_state
    lock = gs.get("agent_lock_state") or {}
    lock_str = (
        f"held by {lock.get('agent_id', 'unknown')}"
        if lock and lock.get("locked")
        else "free"
    )
    lines.append(
        f"Governance: health={gs['health_status']}, "
        f"check={gs['check_status']}, "
        f"session={gs['session_continuity']}, "
        f"lock={lock_str}"
    )

    rs = pack.roadmap_summary
    lines.append(f"Phase: {rs['current_phase']}")
    lines.append(f"Emphasized: {', '.join(profile.emphasized_sections)}")

    lines.append("Rules:")
    for rule in pack.operational_rules:
        lines.append(f"  - {rule}")

    lines.append(f"Validate: {' | '.join(pack.validation_commands)}")
    lines.append(f"Stale-context: {_STALE_CONTEXT_RULE}")
    lines.append("Bootstrap: pcae session bootstrap --agent-id <id>")
    lines.append("Handoff: pcae phase handoff")

    os_ = pack.orchestration_state
    lines.append(
        f"Orchestration: {os_.get('advisory_recommendation_semantics', 'User remains authoritative.')}"
    )
    lines.append("Vendor-neutral: not tailored to any specific AI agent or provider.")

    return "\n".join(lines)

CONTEXT_PACK_UNIVERSAL_AGENT_NOTE = (
    "This context pack is vendor-neutral and universal. "
    "It is not tailored to any specific AI agent or provider."
)

CONTEXT_PACK_ORCHESTRATION_USER_AUTHORITY = (
    "Advisory recommendations are non-binding. The human user remains authoritative."
)

CONTEXT_PACK_BOOTSTRAP_HANDOFF_NOTES: tuple[str, ...] = (
    "Use `pcae session bootstrap --agent-id <id>` to initialize a fresh agent session.",
    "Use `pcae phase handoff` to transfer work between agents.",
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
    scope_boundaries: dict
    governance_state: dict
    orchestration_state: dict
    provenance_summary: dict
    roadmap_summary: dict
    operational_rules: tuple[str, ...]
    validation_commands: tuple[str, ...]
    bootstrap_handoff_notes: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "active_task": self.active_task,
            "advisory": self.advisory,
            "bootstrap_handoff_notes": list(self.bootstrap_handoff_notes),
            "governance_state": self.governance_state,
            "operational_rules": list(self.operational_rules),
            "orchestration_state": self.orchestration_state,
            "provenance_summary": self.provenance_summary,
            "roadmap_summary": self.roadmap_summary,
            "scope_boundaries": self.scope_boundaries,
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
        "advisory_recommendation_semantics": CONTEXT_PACK_ORCHESTRATION_USER_AUTHORITY,
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

    active_task_obj = find_latest_active_task(root)
    if active_task_obj is not None:
        scope_boundaries = {
            "allowed_files": list(active_task_obj.allowed_files),
            "forbidden_files": list(active_task_obj.forbidden_files),
        }
    else:
        scope_boundaries = {"allowed_files": [], "forbidden_files": []}

    return ContextPack(
        active_task=health["active_task"],
        scope_boundaries=scope_boundaries,
        governance_state=governance_state,
        orchestration_state=orchestration_state,
        provenance_summary=provenance_summary,
        roadmap_summary=roadmap_summary,
        operational_rules=CONTEXT_PACK_OPERATIONAL_RULES,
        validation_commands=CONTEXT_PACK_VALIDATION_COMMANDS,
        bootstrap_handoff_notes=CONTEXT_PACK_BOOTSTRAP_HANDOFF_NOTES,
        advisory=CONTEXT_PACK_ADVISORY,
    )
