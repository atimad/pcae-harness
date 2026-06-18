from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from pcae.core.architecture import (
    ADR_INSPECTION_ADVISORY as _ADR_INSPECTION_ADVISORY,
    get_adr_registry,
)
from pcae.core.check import run_checks
from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.strategic_lineage import strategic_continuity_summary
from pcae.core.policy import load_policy
from pcae.core.provenance import build_provenance_timeline
from pcae.core.tasks import find_latest_active_task


ARCHITECTURE_MEMORY_ADVISORY = _ADR_INSPECTION_ADVISORY


def _build_architecture_memory_summary(root: HarnessPath) -> dict:
    """Return a compact read-only architecture memory summary.

    Includes decision count, accepted count, latest decision, and advisory.
    Does not include full ADR bodies.
    """
    registry = get_adr_registry(root)
    decision_count = len(registry)
    accepted_count = sum(1 for adr in registry if adr.status == "accepted")
    latest_decision = None
    if registry:
        last = registry[-1]
        latest_decision = {
            "id": last.decision_id,
            "status": last.status,
            "title": last.title,
        }
    return {
        "accepted_count": accepted_count,
        "advisory": ARCHITECTURE_MEMORY_ADVISORY,
        "decision_count": decision_count,
        "latest_decision": latest_decision,
    }


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


def build_bootstrap_prompt(
    pack: ContextPack,
    profile: WorkModeProfile,
    handoff: dict | None = None,
) -> str:
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
    if handoff is not None:
        lines.append(f"Last handoff: {handoff.get('summary', 'unknown')}")
        lines.append(f"  Handoff at: {handoff.get('created_at', 'unknown')}")
        lines.append(f"  Latest commit: {handoff.get('latest_commit', 'unknown')}")
        lines.append(f"  Task: {handoff.get('task_state', 'unknown')}")
        handoff_review = handoff.get("lifecycle_review")
        if handoff_review:
            lines.append(f"  Review: {handoff_review}")
        lines.append(f"  Next action: {handoff.get('recommended_next_action', 'unknown')}")
        lines.append(f"Phase (from PROJECT_STATUS.md): {rs['current_phase']}")
    else:
        lines.append(f"Phase: {rs['current_phase']}")
    lines.append(f"Emphasized: {', '.join(profile.emphasized_sections)}")

    continuity = pack.strategic_continuity
    current_lineage = continuity.get("current")
    if isinstance(current_lineage, dict):
        lines.append(f"Strategic Decision: {current_lineage['lineage_id']}")
        lines.append(
            f"Activated: {current_lineage['activated_phase_id']} "
            f"on {current_lineage['selected_branch_id']}"
        )
        lines.append(f"Decision Basis: {current_lineage['decision_basis']}")
        lines.append(f"Reason: {current_lineage['rationale']}")
        deferred = continuity.get("deferred_alternatives") or []
        deferred_text = "; ".join(
            f"{alternative['phase_id']} ({alternative['reason']})"
            for alternative in deferred[:3]
        )
        lines.append(f"Deferred Alternatives: {deferred_text or 'none'}")
        referenced_findings = continuity.get("referenced_review_findings") or []
        findings_text = "; ".join(
            f"{reference['review_id']} ({reference['finding_count']} findings)"
            for reference in referenced_findings[:3]
        )
        lines.append(f"Referenced Review Findings: {findings_text or 'none'}")
        lines.append("Details: pcae strategic-continuity show current")

    irg = pack.irg_review_summary
    if irg.get("bootstrap_line"):
        lines.append(irg["bootstrap_line"])
        lines.append(irg.get("authority_line", ""))

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

    mem = pack.architecture_memory
    decision_count = mem.get("decision_count", 0)
    accepted_count = mem.get("accepted_count", 0)
    latest = mem.get("latest_decision")
    latest_text = latest["id"] if isinstance(latest, dict) and "id" in latest else "none"
    lines.append(
        f"Architecture memory: {decision_count} decisions ({accepted_count} accepted),"
        f" latest: {latest_text}"
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Context pack export
# ---------------------------------------------------------------------------

CONTEXT_PACK_EXPORT_RELATIVE_DIR = Path(".pcae") / "context-packs"


def export_context_pack(
    root: HarnessPath,
    pack: ContextPack,
    profile: WorkModeProfile,
    exported_at: datetime | None = None,
) -> tuple[Path, str]:
    """Write a compact context pack to .pcae/context-packs/.

    Returns (relative_path, exported_at_iso).
    """
    timestamp = exported_at or datetime.now(timezone.utc)
    filename = f"context-pack-{timestamp.strftime('%Y%m%d-%H%M%S')}.txt"
    relative_path = CONTEXT_PACK_EXPORT_RELATIVE_DIR / filename
    target = root.join(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = build_bootstrap_prompt(pack, profile)
    target.write_text(content + "\n", encoding="utf-8")
    return relative_path, timestamp.isoformat()


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
    "Always run pcae check and python -m pytest -n auto before committing.",
)

CONTEXT_PACK_VALIDATION_COMMANDS: tuple[str, ...] = (
    "pcae health",
    "pcae check",
    "python -m pytest -n auto",
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
    architecture_memory: dict
    strategic_continuity: dict
    irg_review_summary: dict

    def to_dict(self) -> dict:
        return {
            "active_task": self.active_task,
            "advisory": self.advisory,
            "architecture_memory": self.architecture_memory,
            "bootstrap_handoff_notes": list(self.bootstrap_handoff_notes),
            "governance_state": self.governance_state,
            "irg_review_summary": self.irg_review_summary,
            "operational_rules": list(self.operational_rules),
            "orchestration_state": self.orchestration_state,
            "provenance_summary": self.provenance_summary,
            "roadmap_summary": self.roadmap_summary,
            "scope_boundaries": self.scope_boundaries,
            "strategic_continuity": self.strategic_continuity,
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
    from pcae.core.agent import build_irg_loop_integration

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
        architecture_memory=_build_architecture_memory_summary(root),
        strategic_continuity=strategic_continuity_summary(root),
        irg_review_summary=build_irg_loop_integration(root),
    )


# ---------------------------------------------------------------------------
# Continuity restore packs
# ---------------------------------------------------------------------------

CONTINUITY_PACK_RELATIVE_DIR = Path(".pcae") / "continuity-packs"

CONTINUITY_PACK_VENDOR_NEUTRAL_NOTE = (
    "This continuity pack is vendor-neutral and universal. "
    "It is not tailored to any specific AI agent or provider."
)

CONTINUITY_PACK_STALE_CONTEXT_SUPPRESSION_RULES: tuple[str, ...] = (
    "Phase prompt is authoritative. PROJECT_STATUS.md is background.",
    "Do not infer stale tasks from older governance documents.",
    "Do not modify files outside the active task scope.",
)

CONTINUITY_PACK_GOVERNANCE_CONTINUITY_NOTE = (
    "Continuity pack is governance-complete and vendor-neutral."
)

CONTINUITY_PACK_INCLUDED_SECTIONS: tuple[str, ...] = (
    "active task summary",
    "governance state",
    "orchestration state",
    "provenance summary",
    "runtime snapshot metadata",
    "compact context pack",
    "compact bootstrap prompt",
    "operational rules",
    "validation commands",
    "stale-context suppression rules",
    "bootstrap continuity",
    "vendor-neutral note",
    "architecture memory",
)

# Known optional keys that are not required for pack validity but are
# recognized by this PCAE version and excluded from future-version warnings.
_CONTINUITY_PACK_OPTIONAL_KEYS: frozenset[str] = frozenset({"architecture_memory"})


@dataclass(frozen=True)
class ContinuityPack:
    exported_at: str
    profile_type: str
    active_task_summary: dict | None
    governance_state: dict
    orchestration_state: dict
    provenance_summary: dict
    runtime_snapshot_metadata: dict
    compact_context_pack: dict
    compact_bootstrap_prompt: str
    operational_rules: tuple[str, ...]
    validation_commands: tuple[str, ...]
    stale_context_suppression_rules: tuple[str, ...]
    vendor_neutral_note: str
    bootstrap_continuity: tuple[str, ...]
    architecture_memory: dict

    def to_dict(self) -> dict:
        return {
            "active_task_summary": self.active_task_summary,
            "architecture_memory": self.architecture_memory,
            "bootstrap_continuity": list(self.bootstrap_continuity),
            "compact_bootstrap_prompt": self.compact_bootstrap_prompt,
            "compact_context_pack": self.compact_context_pack,
            "exported_at": self.exported_at,
            "governance_state": self.governance_state,
            "operational_rules": list(self.operational_rules),
            "orchestration_state": self.orchestration_state,
            "profile_type": self.profile_type,
            "provenance_summary": self.provenance_summary,
            "runtime_snapshot_metadata": self.runtime_snapshot_metadata,
            "stale_context_suppression_rules": list(self.stale_context_suppression_rules),
            "validation_commands": list(self.validation_commands),
            "vendor_neutral_note": self.vendor_neutral_note,
        }


def build_continuity_pack(
    root: HarnessPath,
    profile: WorkModeProfile,
    exported_at: datetime | None = None,
) -> ContinuityPack:
    """Build a portable governed continuity restore pack."""
    from pcae.core.status import preview_runtime_snapshot

    timestamp = exported_at or datetime.now(timezone.utc)
    pack = build_context_pack(root)
    snapshot_preview = preview_runtime_snapshot(root)
    bootstrap_prompt = build_bootstrap_prompt(pack, profile)

    active_task_summary = None
    if pack.active_task is not None:
        active_task_summary = {
            "id": pack.active_task.get("id"),
            "status": pack.active_task.get("status"),
            "title": pack.active_task.get("title"),
        }

    return ContinuityPack(
        exported_at=timestamp.isoformat(),
        profile_type=profile.profile_type,
        active_task_summary=active_task_summary,
        governance_state=pack.governance_state,
        orchestration_state=pack.orchestration_state,
        provenance_summary=pack.provenance_summary,
        runtime_snapshot_metadata=snapshot_preview.runtime_summary,
        compact_context_pack=pack.to_dict(),
        compact_bootstrap_prompt=bootstrap_prompt,
        operational_rules=pack.operational_rules,
        validation_commands=pack.validation_commands,
        stale_context_suppression_rules=CONTINUITY_PACK_STALE_CONTEXT_SUPPRESSION_RULES,
        vendor_neutral_note=CONTINUITY_PACK_VENDOR_NEUTRAL_NOTE,
        bootstrap_continuity=pack.bootstrap_handoff_notes,
        architecture_memory=pack.architecture_memory,
    )


def export_continuity_pack(
    root: HarnessPath,
    continuity_pack: ContinuityPack,
) -> tuple[Path, str]:
    """Write a continuity restore pack to .pcae/continuity-packs/.

    Returns (relative_path, exported_at_iso).
    """
    ts = datetime.fromisoformat(continuity_pack.exported_at)
    filename = f"continuity-pack-{ts.strftime('%Y%m%d-%H%M%S')}.json"
    relative_path = CONTINUITY_PACK_RELATIVE_DIR / filename
    target = root.join(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(continuity_pack.to_dict(), fh, indent=2, sort_keys=True)
        fh.write("\n")
    return relative_path, continuity_pack.exported_at


# ---------------------------------------------------------------------------
# Continuity pack inspection
# ---------------------------------------------------------------------------

CONTINUITY_PACK_INSPECTION_ADVISORY = (
    "Continuity pack inspection is advisory; no runtime state is changed."
)

CONTINUITY_PACK_REQUIRED_KEYS: tuple[str, ...] = (
    "exported_at",
    "profile_type",
    "active_task_summary",
    "governance_state",
    "orchestration_state",
    "provenance_summary",
    "runtime_snapshot_metadata",
    "compact_context_pack",
    "compact_bootstrap_prompt",
    "operational_rules",
    "validation_commands",
    "stale_context_suppression_rules",
    "vendor_neutral_note",
    "bootstrap_continuity",
)


@dataclass(frozen=True)
class ContinuityPackInspection:
    valid: bool
    exported_at: str
    profile_type: str
    included_sections: tuple[str, ...]
    continuity_summary: dict
    portability_notes: tuple[str, ...]
    safety_notes: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "advisory": self.advisory,
            "continuity_summary": self.continuity_summary,
            "exported_at": self.exported_at,
            "included_sections": list(self.included_sections),
            "portability_notes": list(self.portability_notes),
            "profile_type": self.profile_type,
            "safety_notes": list(self.safety_notes),
            "valid": self.valid,
        }


def inspect_continuity_pack(path: Path) -> ContinuityPackInspection:
    """Read and inspect a continuity pack file. Raises ValueError for invalid packs."""
    if not path.is_file():
        raise ValueError(f"Continuity pack not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid continuity pack JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValueError("Invalid continuity pack: top-level JSON value must be an object.")

    missing = [key for key in CONTINUITY_PACK_REQUIRED_KEYS if key not in data]
    if missing:
        raise ValueError(
            f"Invalid continuity pack: missing required field(s): {', '.join(missing)}."
        )

    exported_at = data["exported_at"]
    if not isinstance(exported_at, str) or not exported_at:
        raise ValueError("Invalid continuity pack: exported_at must be a non-empty string.")
    profile_type = data["profile_type"]
    if not isinstance(profile_type, str) or not profile_type:
        raise ValueError("Invalid continuity pack: profile_type must be a non-empty string.")

    gs = data.get("governance_state") or {}
    os_ = data.get("orchestration_state") or {}
    ps = data.get("provenance_summary") or {}
    at = data.get("active_task_summary")

    included_sections = []
    for section in CONTINUITY_PACK_INCLUDED_SECTIONS:
        key = section.replace(" ", "_").replace("-", "_")
        # map canonical section names to JSON keys
        _section_key_map = {
            "active task summary": "active_task_summary",
            "architecture memory": "architecture_memory",
            "bootstrap continuity": "bootstrap_continuity",
            "compact bootstrap prompt": "compact_bootstrap_prompt",
            "compact context pack": "compact_context_pack",
            "governance state": "governance_state",
            "operational rules": "operational_rules",
            "orchestration state": "orchestration_state",
            "provenance summary": "provenance_summary",
            "runtime snapshot metadata": "runtime_snapshot_metadata",
            "stale-context suppression rules": "stale_context_suppression_rules",
            "validation commands": "validation_commands",
            "vendor-neutral note": "vendor_neutral_note",
        }
        json_key = _section_key_map.get(section, key)
        if json_key in data and data[json_key] is not None:
            included_sections.append(section)

    continuity_summary = {
        "active_task": at,
        "architecture_memory_present": bool(data.get("architecture_memory")),
        "compact_bootstrap_prompt_present": bool(data.get("compact_bootstrap_prompt")),
        "compact_context_pack_present": bool(data.get("compact_context_pack")),
        "governance_check": gs.get("check_status"),
        "governance_health": gs.get("health_status"),
        "orchestration_default_agent": os_.get("default_agent"),
        "provenance_event_count": ps.get("event_count"),
        "stale_context_suppression_present": bool(
            data.get("stale_context_suppression_rules")
        ),
        "vendor_neutral_note_present": bool(data.get("vendor_neutral_note")),
    }

    return ContinuityPackInspection(
        valid=True,
        exported_at=exported_at,
        profile_type=profile_type,
        included_sections=tuple(included_sections),
        continuity_summary=continuity_summary,
        portability_notes=(
            "Continuity pack was read for inspection only; runtime state was not restored.",
            "Continuity packs are portable, governance-complete, vendor-neutral exports.",
            "No governance artifacts were modified during inspection.",
        ),
        safety_notes=(
            "Inspection only; no files were written or mutated.",
            "Runtime state is not restored or changed.",
            "Continuity packs are read-only exports.",
        ),
        advisory=CONTINUITY_PACK_INSPECTION_ADVISORY,
    )


# ---------------------------------------------------------------------------
# Continuity pack compatibility analysis
# ---------------------------------------------------------------------------

CONTINUITY_PACK_COMPATIBILITY_ADVISORY = (
    "Continuity compatibility analysis is advisory; no runtime state is changed."
)

_CONTINUITY_RUNTIME_METADATA_REQUIRED_KEYS: tuple[str, ...] = (
    "governance_health_status",
    "governance_check_status",
    "active_task",
    "agent_lock_state",
    "session_continuity_status",
    "provenance_event_count",
)


@dataclass(frozen=True)
class ContinuityCompatibilityCheck:
    name: str
    passed: bool
    message: str

    def to_dict(self) -> dict:
        return {"message": self.message, "name": self.name, "passed": self.passed}


@dataclass(frozen=True)
class ContinuityCompatibilityReport:
    compatible: bool
    support_level: str
    compatibility_checks: tuple[ContinuityCompatibilityCheck, ...]
    warnings: tuple[str, ...]
    continuity_summary: dict
    advisory: str

    def to_dict(self) -> dict:
        return {
            "advisory": self.advisory,
            "compatible": self.compatible,
            "compatibility_checks": [c.to_dict() for c in self.compatibility_checks],
            "continuity_summary": self.continuity_summary,
            "support_level": self.support_level,
            "warnings": list(self.warnings),
        }


def _dedup_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


def analyze_continuity_pack_compatibility(path: Path) -> ContinuityCompatibilityReport:
    """Return deterministic read-only compatibility analysis for a continuity pack.

    Raises ValueError for file-not-found, invalid JSON, or non-object JSON.
    """
    if not path.is_file():
        raise ValueError(f"Continuity pack not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid continuity pack JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValueError("Invalid continuity pack: top-level JSON value must be an object.")

    checks: list[ContinuityCompatibilityCheck] = []
    warnings: list[str] = []

    # Check 1: structure validity (reaching this point confirms basic structure)
    checks.append(ContinuityCompatibilityCheck(
        name="continuity_pack_structure_validity",
        passed=True,
        message="Continuity pack is a valid JSON object.",
    ))

    # Check 2: required continuity sections presence
    missing = [k for k in CONTINUITY_PACK_REQUIRED_KEYS if k not in data]
    sections_ok = not missing
    if sections_ok:
        sections_msg = "All required continuity sections are present."
    else:
        sections_msg = (
            "Missing required continuity section(s): " + ", ".join(missing) + "."
        )
        warnings.append(sections_msg)
    checks.append(ContinuityCompatibilityCheck(
        name="required_continuity_sections_presence",
        passed=sections_ok,
        message=sections_msg,
    ))

    # Check 3: governance state presence
    gs = data.get("governance_state") or {}
    gov_ok = (
        isinstance(gs, dict)
        and "health_status" in gs
        and "check_status" in gs
    )
    gov_msg = (
        "Governance state is present with health and check status."
        if gov_ok
        else "Governance state is missing or incomplete (expected health_status and check_status)."
    )
    if not gov_ok:
        warnings.append(gov_msg)
    checks.append(ContinuityCompatibilityCheck(
        name="governance_state_presence",
        passed=gov_ok,
        message=gov_msg,
    ))

    # Check 4: compact bootstrap presence
    bootstrap = data.get("compact_bootstrap_prompt")
    bootstrap_ok = isinstance(bootstrap, str) and bool(bootstrap)
    bootstrap_msg = (
        "Compact bootstrap prompt is present."
        if bootstrap_ok
        else "Compact bootstrap prompt is missing or empty."
    )
    if not bootstrap_ok:
        warnings.append(bootstrap_msg)
    checks.append(ContinuityCompatibilityCheck(
        name="compact_bootstrap_presence",
        passed=bootstrap_ok,
        message=bootstrap_msg,
    ))

    # Check 5: operational rules presence
    op_rules = data.get("operational_rules")
    op_ok = isinstance(op_rules, list) and len(op_rules) > 0
    op_msg = (
        "Operational rules are present."
        if op_ok
        else "Operational rules are missing or empty."
    )
    if not op_ok:
        warnings.append(op_msg)
    checks.append(ContinuityCompatibilityCheck(
        name="operational_rules_presence",
        passed=op_ok,
        message=op_msg,
    ))

    # Check 6: stale-context suppression presence
    stale = data.get("stale_context_suppression_rules")
    stale_ok = isinstance(stale, list) and len(stale) > 0
    stale_msg = (
        "Stale-context suppression rules are present."
        if stale_ok
        else "Stale-context suppression rules are missing or empty."
    )
    if not stale_ok:
        warnings.append(stale_msg)
    checks.append(ContinuityCompatibilityCheck(
        name="stale_context_suppression_presence",
        passed=stale_ok,
        message=stale_msg,
    ))

    # Check 7: vendor-neutral note presence
    vn_note = data.get("vendor_neutral_note")
    vn_ok = isinstance(vn_note, str) and bool(vn_note)
    vn_msg = (
        "Vendor-neutral note is present."
        if vn_ok
        else "Vendor-neutral note is missing or empty."
    )
    if not vn_ok:
        warnings.append(vn_msg)
    checks.append(ContinuityCompatibilityCheck(
        name="vendor_neutral_note_presence",
        passed=vn_ok,
        message=vn_msg,
    ))

    # Check 8: runtime snapshot metadata compatibility
    rsm = data.get("runtime_snapshot_metadata")
    if isinstance(rsm, dict):
        missing_rsm = [k for k in _CONTINUITY_RUNTIME_METADATA_REQUIRED_KEYS if k not in rsm]
        rsm_ok = not missing_rsm
        if rsm_ok:
            rsm_msg = "Runtime snapshot metadata contains all expected governance fields."
        else:
            rsm_msg = (
                "Runtime snapshot metadata is missing expected field(s): "
                + ", ".join(missing_rsm) + "."
            )
            warnings.append(rsm_msg)
    else:
        rsm_ok = False
        rsm_msg = "Runtime snapshot metadata is missing or not an object."
        warnings.append(rsm_msg)
    checks.append(ContinuityCompatibilityCheck(
        name="runtime_snapshot_metadata_compatibility",
        passed=rsm_ok,
        message=rsm_msg,
    ))

    # Check 9: future-version warning support (unexpected top-level keys)
    # Known optional keys are excluded from the future-version warning.
    _all_known_keys = set(CONTINUITY_PACK_REQUIRED_KEYS) | _CONTINUITY_PACK_OPTIONAL_KEYS
    extra_keys = [k for k in data if k not in _all_known_keys]
    no_extra = not extra_keys
    if no_extra:
        future_msg = "No future-version indicators detected; pack conforms to known schema."
    else:
        future_msg = (
            "Unexpected top-level key(s) detected: "
            + ", ".join(sorted(extra_keys))
            + ". Pack may have been exported by a newer PCAE version."
        )
        warnings.append(future_msg)
    checks.append(ContinuityCompatibilityCheck(
        name="future_version_warning_support",
        passed=no_extra,
        message=future_msg,
    ))

    # Check 10: architecture memory presence (advisory; does not affect compatible)
    arch_mem = data.get("architecture_memory")
    arch_ok = isinstance(arch_mem, dict) and bool(arch_mem)
    arch_msg = (
        "Architecture memory is present."
        if arch_ok
        else "Architecture memory is absent; pack may have been exported before Phase 36L."
    )
    checks.append(ContinuityCompatibilityCheck(
        name="architecture_memory_presence",
        passed=arch_ok,
        message=arch_msg,
    ))

    # Determine support level
    if not sections_ok:
        support_level = "unsupported"
        warnings.append("No migration or automatic conversion is available.")
    elif warnings:
        support_level = "partially-supported"
    else:
        support_level = "supported"

    at = data.get("active_task_summary") or {}
    continuity_summary = {
        "active_task_id": at.get("id") if isinstance(at, dict) else None,
        "active_task_title": at.get("title") if isinstance(at, dict) else None,
        "exported_at": data.get("exported_at"),
        "governance_check": gs.get("check_status") if isinstance(gs, dict) else None,
        "governance_health": gs.get("health_status") if isinstance(gs, dict) else None,
        "profile_type": data.get("profile_type"),
    }

    return ContinuityCompatibilityReport(
        compatible=support_level == "supported",
        support_level=support_level,
        compatibility_checks=tuple(checks),
        warnings=tuple(_dedup_preserving_order(warnings)),
        continuity_summary=continuity_summary,
        advisory=CONTINUITY_PACK_COMPATIBILITY_ADVISORY,
    )


# ---------------------------------------------------------------------------
# Continuity pack manifest
# ---------------------------------------------------------------------------

CONTINUITY_MANIFEST_ADVISORY = (
    "Continuity manifests are advisory; the user remains authoritative."
)


def _reverse_text_sort_key(value: str) -> str:
    return "".join(chr(0x10FFFF - ord(ch)) for ch in value)


@dataclass(frozen=True)
class ContinuityManifestEntry:
    filename: str
    exported_at: object
    profile_type: object
    governance_health: object
    governance_check: object
    active_task_id: object
    compatibility_status: str
    support_level: str
    vendor_neutral: bool
    stale_context_suppression_present: bool
    compact_bootstrap_present: bool

    def to_dict(self) -> dict:
        return {
            "active_task_id": self.active_task_id,
            "compact_bootstrap_present": self.compact_bootstrap_present,
            "compatibility_status": self.compatibility_status,
            "exported_at": self.exported_at,
            "filename": self.filename,
            "governance_check": self.governance_check,
            "governance_health": self.governance_health,
            "profile_type": self.profile_type,
            "stale_context_suppression_present": self.stale_context_suppression_present,
            "support_level": self.support_level,
            "vendor_neutral": self.vendor_neutral,
        }


@dataclass(frozen=True)
class ContinuityManifest:
    pack_count: int
    latest_pack: dict | None
    manifest_entries: tuple[ContinuityManifestEntry, ...]
    compatibility_summary: dict
    advisory: str

    def to_dict(self) -> dict:
        return {
            "advisory": self.advisory,
            "compatibility_summary": self.compatibility_summary,
            "latest_pack": self.latest_pack,
            "manifest_entries": [e.to_dict() for e in self.manifest_entries],
            "pack_count": self.pack_count,
        }


def _continuity_manifest_entry_sort_key(
    entry: ContinuityManifestEntry,
) -> tuple[int, str, str]:
    exported_at = entry.exported_at if isinstance(entry.exported_at, str) else ""
    missing = 0 if exported_at else 1
    return (missing, _reverse_text_sort_key(exported_at), entry.filename)


def _continuity_manifest_entry(path: Path) -> ContinuityManifestEntry:
    filename = path.name
    try:
        compat = analyze_continuity_pack_compatibility(path)
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return ContinuityManifestEntry(
            filename=filename,
            exported_at=None,
            profile_type=None,
            governance_health=None,
            governance_check=None,
            active_task_id=None,
            compatibility_status="incompatible",
            support_level="unsupported",
            vendor_neutral=False,
            stale_context_suppression_present=False,
            compact_bootstrap_present=False,
        )
    gs = data.get("governance_state") or {}
    at = data.get("active_task_summary")
    return ContinuityManifestEntry(
        filename=filename,
        exported_at=data.get("exported_at"),
        profile_type=data.get("profile_type"),
        governance_health=gs.get("health_status") if isinstance(gs, dict) else None,
        governance_check=gs.get("check_status") if isinstance(gs, dict) else None,
        active_task_id=at.get("id") if isinstance(at, dict) else None,
        compatibility_status="compatible" if compat.compatible else "incompatible",
        support_level=compat.support_level,
        vendor_neutral=bool(data.get("vendor_neutral_note")),
        stale_context_suppression_present=bool(
            data.get("stale_context_suppression_rules")
        ),
        compact_bootstrap_present=bool(data.get("compact_bootstrap_prompt")),
    )


def _continuity_manifest_summary(
    entries: tuple[ContinuityManifestEntry, ...],
) -> dict:
    summary: dict[str, int] = {
        "compatible": 0,
        "incompatible": 0,
        "partially-supported": 0,
        "supported": 0,
        "unsupported": 0,
    }
    for entry in entries:
        if entry.compatibility_status == "compatible":
            summary["compatible"] += 1
        else:
            summary["incompatible"] += 1
        if entry.support_level in summary:
            summary[entry.support_level] += 1
    return summary


def build_continuity_manifest(root: HarnessPath) -> ContinuityManifest:
    """Return a deterministic read-only index of exported continuity packs."""
    packs_dir = root.join(CONTINUITY_PACK_RELATIVE_DIR)
    if not packs_dir.is_dir():
        entries: tuple[ContinuityManifestEntry, ...] = ()
        return ContinuityManifest(
            pack_count=0,
            latest_pack=None,
            manifest_entries=entries,
            compatibility_summary=_continuity_manifest_summary(entries),
            advisory=CONTINUITY_MANIFEST_ADVISORY,
        )
    entries = tuple(
        sorted(
            (
                _continuity_manifest_entry(path)
                for path in packs_dir.iterdir()
                if path.is_file() and path.suffix == ".json"
            ),
            key=_continuity_manifest_entry_sort_key,
        )
    )
    latest = entries[0].to_dict() if entries else None
    return ContinuityManifest(
        pack_count=len(entries),
        latest_pack=latest,
        manifest_entries=entries,
        compatibility_summary=_continuity_manifest_summary(entries),
        advisory=CONTINUITY_MANIFEST_ADVISORY,
    )


# ---------------------------------------------------------------------------
# Continuity pack retention planning
# ---------------------------------------------------------------------------

CONTINUITY_RETENTION_KEEP_COUNT = 5

CONTINUITY_RETENTION_ADVISORY = (
    "Continuity retention planning is advisory; no continuity packs are deleted."
)


@dataclass(frozen=True)
class ContinuityRetentionPlan:
    pack_count: int
    keep_count: int
    prune_candidate_count: int
    keep: tuple[str, ...]
    prune_candidates: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "advisory": self.advisory,
            "keep": list(self.keep),
            "keep_count": self.keep_count,
            "pack_count": self.pack_count,
            "prune_candidate_count": self.prune_candidate_count,
            "prune_candidates": list(self.prune_candidates),
        }


def plan_continuity_retention(root: HarnessPath) -> ContinuityRetentionPlan:
    """Return a read-only retention plan for exported continuity packs.

    Keeps the latest CONTINUITY_RETENTION_KEEP_COUNT packs; marks the rest as
    prune candidates.  Never deletes or mutates any file.
    """
    manifest = build_continuity_manifest(root)
    entries = manifest.manifest_entries  # already sorted newest-first
    keep = tuple(e.filename for e in entries[:CONTINUITY_RETENTION_KEEP_COUNT])
    prune_candidates = tuple(
        e.filename for e in entries[CONTINUITY_RETENTION_KEEP_COUNT:]
    )
    return ContinuityRetentionPlan(
        pack_count=manifest.pack_count,
        keep_count=len(keep),
        prune_candidate_count=len(prune_candidates),
        keep=keep,
        prune_candidates=prune_candidates,
        advisory=CONTINUITY_RETENTION_ADVISORY,
    )
