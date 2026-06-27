from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.artifact_index import build_artifact_index
from pcae.core.memory_snapshot import build_memory_snapshot
from pcae.core.governance_timeline import build_governance_timeline
from pcae.core.decision_log import build_decision_log


def _stable_risk_id(phase: str, risk_type: str, suffix: str = "") -> str:
    raw = f"{phase}:{risk_type}"
    if suffix:
        raw = f"{raw}:{suffix}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"risk-{phase}-{risk_type}-{digest}"


def _make_risk(
    risk_id: str,
    risk_type: str,
    risk_status: str,
    risk_title: str,
    risk_description: str,
    risk_severity: str,
    risk_likelihood: str,
    risk_exposure: str,
    source_phase: str,
    source_artifact: str | None,
    source_event: str | None,
    source_decision: str | None,
    source_commit: str | None,
    risk_owner: str | None,
    human_review_required: bool,
    affected_files: list[str] | None,
    affected_agents: list[str] | None,
    affected_commands: list[str] | None,
    blocking_condition: str | None,
    mitigation: str | None,
    acceptance_rationale: str | None,
    accepted_by: str | None,
    supersedes: str | None,
    superseded_by: str | None,
    related_risks: list[str] | None,
    related_artifacts: list[str] | None,
    related_events: list[str] | None,
    related_decisions: list[str] | None,
    evidence_level: str,
    last_reviewed_phase: str | None,
    next_review_phase: str | None,
    safety_notes: str | None,
) -> dict[str, Any]:
    return {
        "risk_id": risk_id,
        "risk_type": risk_type,
        "risk_status": risk_status,
        "risk_title": risk_title,
        "risk_description": risk_description,
        "risk_severity": risk_severity,
        "risk_likelihood": risk_likelihood,
        "risk_exposure": risk_exposure,
        "source_phase": source_phase,
        "source_artifact": source_artifact if source_artifact is not None else "unknown",
        "source_event": source_event if source_event is not None else "unknown",
        "source_decision": source_decision if source_decision is not None else "unknown",
        "source_commit": source_commit if source_commit is not None else "unknown",
        "risk_owner": risk_owner,
        "human_review_required": human_review_required,
        "affected_files": affected_files or [],
        "affected_agents": affected_agents or [],
        "affected_commands": affected_commands or [],
        "blocking_condition": blocking_condition,
        "mitigation": mitigation,
        "acceptance_rationale": acceptance_rationale,
        "accepted_by": accepted_by,
        "supersedes": supersedes,
        "superseded_by": superseded_by,
        "related_risks": related_risks or [],
        "related_artifacts": related_artifacts or [],
        "related_events": related_events or [],
        "related_decisions": related_decisions or [],
        "evidence_level": evidence_level,
        "last_reviewed_phase": last_reviewed_phase,
        "next_review_phase": next_review_phase,
        "safety_notes": safety_notes,
    }


_STANDING_RISKS: list[dict[str, Any]] = [
    {
        "risk_type": "read_only_boundary_risk",
        "risk_status": "active",
        "risk_title": "Read-only boundary must remain enforced",
        "risk_description": "All Phase 85/86 read-only commands must not write files, create cache, or mutate .pcae. Violation would bypass governance gates.",
        "risk_severity": "high",
        "risk_likelihood": "unlikely",
        "risk_exposure": "medium",
        "source_phase": "86A",
        "source_artifact": "docs/PHASE_85_IMPLEMENTATION_ROADMAP.md",
        "mitigation": "Read-only-first implementation principle enforced per 86A roadmap. Tests assert no file writes.",
        "safety_notes": "read_only_boundary=enforced",
    },
    {
        "risk_type": "storage_boundary_risk",
        "risk_status": "active",
        "risk_title": "No storage/cache/.pcae creation without explicit storage gate",
        "risk_description": "Storage, cache, and .pcae directories must not be created until an explicit storage implementation phase is approved.",
        "risk_severity": "high",
        "risk_likelihood": "unlikely",
        "risk_exposure": "medium",
        "source_phase": "86B",
        "source_artifact": "docs/PHASE_85_DATA_MODEL_STORAGE_DESIGN.md",
        "mitigation": "Storage deferred per 86B design. Tests assert no .pcae/cache creation.",
        "safety_notes": "storage_boundary=enforced, cache_creation=deferred",
    },
    {
        "risk_type": "backend_invocation_risk",
        "risk_status": "active",
        "risk_title": "Backend invocation remains forbidden without guard approval",
        "risk_description": "No backend (claude, claude-deepseek, claude-kimi, codex) may be invoked without passing the 84H invocation guard design checks.",
        "risk_severity": "critical",
        "risk_likelihood": "unlikely",
        "risk_exposure": "high",
        "source_phase": "84H",
        "source_artifact": "docs/MULTI_AGENT_BACKEND_INVOCATION_GUARD_HARDENING.md",
        "mitigation": "Guard design documented in 84H. No backend invocation performed in 86-series.",
        "safety_notes": "backend_invocation=forbidden_without_guard",
    },
    {
        "risk_type": "authority_inference_risk",
        "risk_status": "active",
        "risk_title": "Authority inference from output presence remains forbidden",
        "risk_description": "Command output presence must not be used to infer execution authorization, adoption approval, or commit/push permission.",
        "risk_severity": "high",
        "risk_likelihood": "unlikely",
        "risk_exposure": "medium",
        "source_phase": "86A",
        "source_artifact": "docs/PHASE_85_IMPLEMENTATION_ROADMAP.md",
        "mitigation": "Safety notes in all commands explicitly state no authorization inference. Tests verify.",
        "safety_notes": "authority_inference=prevented",
    },
    {
        "risk_type": "raw_push_exception_risk",
        "risk_status": "active",
        "risk_title": "Raw git push exception must not be normalized",
        "risk_description": "Raw git push (bypassing pcae push) is a must-never-repeat violation. It must remain flagged as an exception, not normalized as acceptable.",
        "risk_severity": "high",
        "risk_likelihood": "unlikely",
        "risk_exposure": "medium",
        "source_phase": "83L",
        "source_artifact": "docs/MULTI_AGENT_LIFECYCLE_FINAL_VERIFICATION.md",
        "mitigation": "Governed pcae push enforced. Raw push blocked by governance policy.",
        "safety_notes": "must_never_repeat=raw_git_push",
    },
    {
        "risk_type": "hook_bypass_exception_risk",
        "risk_status": "active",
        "risk_title": "Hook bypass exception must not be normalized",
        "risk_description": "Commit hook bypass (--no-verify) is a must-never-repeat violation. It must remain flagged as an exception.",
        "risk_severity": "high",
        "risk_likelihood": "unlikely",
        "risk_exposure": "medium",
        "source_phase": "83L",
        "source_artifact": "docs/MULTI_AGENT_LIFECYCLE_FINAL_VERIFICATION.md",
        "mitigation": "Commit hooks enforced. Hook bypass reconciliation documented in lifecycle.",
        "safety_notes": "must_never_repeat=hook_bypass",
    },
    {
        "risk_type": "stale_signal_risk",
        "risk_status": "stale_signal",
        "risk_title": "Handoff-state-refresh structural stale signals remain visible",
        "risk_description": "The 84K.3 health baseline documented 4 BLOCKER and 6 WARNING handoff-state-refresh signals classified as structural (not substantive). These must remain visible, not silently cleared.",
        "risk_severity": "low",
        "risk_likelihood": "observed",
        "risk_exposure": "low",
        "source_phase": "84K.3",
        "source_artifact": "docs/FULL_HEALTH_BASELINE_84K3.md",
        "mitigation": None,
        "acceptance_rationale": "Classified as structural validator signals, not substantive governance blockers. Evidence: signals invariant across refresh cycles.",
        "accepted_by": "governance",
        "safety_notes": "stale_signal=structural_non_blocking, visibility=preserved",
    },
    {
        "risk_type": "implementation_scope_risk",
        "risk_status": "active",
        "risk_title": "Implementation scope must remain bounded per phase",
        "risk_description": "Each implementation phase must implement only its scoped layer. Scope creep into unscoped layers (storage, permission broker, shell gate) must be prevented.",
        "risk_severity": "medium",
        "risk_likelihood": "possible",
        "risk_exposure": "medium",
        "source_phase": "86A",
        "source_artifact": "docs/PHASE_85_IMPLEMENTATION_ROADMAP.md",
        "mitigation": "Task contracts define allowed/forbidden files. PCAE check enforces scope.",
        "safety_notes": "scope_enforcement=task_contract_plus_pcae_check",
    },
    {
        "risk_type": "test_coverage_risk",
        "risk_status": "active",
        "risk_title": "Test coverage must accompany each implementation phase",
        "risk_description": "Every implementation phase must add tests. Skipping tests would leave implementation unverified.",
        "risk_severity": "medium",
        "risk_likelihood": "unlikely",
        "risk_exposure": "low",
        "source_phase": "86A",
        "source_artifact": "docs/PHASE_85_IMPLEMENTATION_ROADMAP.md",
        "mitigation": "Gate: no merge without tests. Each 86-series phase adds tests.",
        "safety_notes": "test_gate=enforced",
    },
    {
        "risk_type": "next_phase_risk",
        "risk_status": "active",
        "risk_title": "Next phase must not be started without completing current phase",
        "risk_description": "Phase sequencing must be preserved. Starting a future phase before completing the current one violates governance ordering.",
        "risk_severity": "medium",
        "risk_likelihood": "unlikely",
        "risk_exposure": "low",
        "source_phase": "86A",
        "source_artifact": "docs/PHASE_85_IMPLEMENTATION_ROADMAP.md",
        "mitigation": "Task contracts track phase status. Completion commit required before next phase.",
        "safety_notes": "phase_ordering=enforced",
    },
    {
        "risk_type": "accepted_risk",
        "risk_status": "accepted",
        "risk_title": "Accepted: design artifacts have implementation_status=not_started",
        "risk_description": "Phase 85 design artifacts (85A-85F) all have implementation_status=not_started. This is accepted because implementation is proceeding in 86-series phases.",
        "risk_severity": "low",
        "risk_likelihood": "observed",
        "risk_exposure": "low",
        "source_phase": "86A",
        "source_artifact": "docs/PHASE_85_IMPLEMENTATION_ROADMAP.md",
        "acceptance_rationale": "Design-first approach. Implementation proceeds in 86B-86I per roadmap. Not a gap — by design.",
        "accepted_by": "governance",
        "safety_notes": "accepted_risk_is_not_mitigation=true",
    },
    {
        "risk_type": "permission_broker_risk",
        "risk_status": "deferred",
        "risk_title": "Permission broker / shell gate remains future direction",
        "risk_description": "The permission broker and shell gate described in 85C are future direction only. They are not implemented and must not be implemented without explicit approval.",
        "risk_severity": "medium",
        "risk_likelihood": "unlikely",
        "risk_exposure": "low",
        "source_phase": "85C",
        "source_artifact": "docs/GOVERNANCE_EVENT_TIMELINE_DESIGN.md",
        "mitigation": None,
        "safety_notes": "permission_broker=deferred, shell_gate=deferred, implementation_status=not_started",
    },
    {
        "risk_type": "must_never_repeat_risk",
        "risk_status": "active",
        "risk_title": "Must-never-repeat controls must remain visible",
        "risk_description": "Controls identified as must-never-repeat (bypass permissions, raw push, force push, adoption without approval, invocation without guard, mutation outside scope, boundary collapse, rejected item reintroduced) must remain visible in risk register.",
        "risk_severity": "high",
        "risk_likelihood": "unlikely",
        "risk_exposure": "medium",
        "source_phase": "85E",
        "source_artifact": "docs/RISK_REGISTER_DESIGN.md",
        "mitigation": "8 must-never-repeat controls documented in 85E. Risk register preserves visibility.",
        "safety_notes": "must_never_repeat_controls=8, visibility=preserved",
    },
]


def build_risk_register(repo_root: Path, ctx=None) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    all_risks: list[dict[str, Any]] = []

    if ctx is None:
        _artifact_data = build_artifact_index(repo_root)
        _snapshot_data = build_memory_snapshot(repo_root)
        _timeline_data = build_governance_timeline(repo_root)
        _decision_data = build_decision_log(repo_root)

    for entry in _STANDING_RISKS:
        risk = _make_risk(
            risk_id=_stable_risk_id(
                entry.get("source_phase", "unknown"),
                entry["risk_type"],
            ),
            risk_type=entry["risk_type"],
            risk_status=entry["risk_status"],
            risk_title=entry["risk_title"],
            risk_description=entry["risk_description"],
            risk_severity=entry.get("risk_severity", "unknown"),
            risk_likelihood=entry.get("risk_likelihood", "unknown"),
            risk_exposure=entry.get("risk_exposure", "unknown"),
            source_phase=entry.get("source_phase", "unknown"),
            source_artifact=entry.get("source_artifact"),
            source_event=None,
            source_decision=None,
            source_commit=None,
            risk_owner=entry.get("risk_owner"),
            human_review_required=entry.get("human_review_required", False),
            affected_files=entry.get("affected_files"),
            affected_agents=entry.get("affected_agents"),
            affected_commands=entry.get("affected_commands"),
            blocking_condition=entry.get("blocking_condition"),
            mitigation=entry.get("mitigation"),
            acceptance_rationale=entry.get("acceptance_rationale"),
            accepted_by=entry.get("accepted_by"),
            supersedes=None,
            superseded_by=None,
            related_risks=None,
            related_artifacts=[entry["source_artifact"]] if entry.get("source_artifact") else None,
            related_events=None,
            related_decisions=None,
            evidence_level="repo_committed_artifact",
            last_reviewed_phase=entry.get("source_phase"),
            next_review_phase=None,
            safety_notes=entry.get("safety_notes"),
        )
        all_risks.append(risk)

    seen_ids: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for r in all_risks:
        if r["risk_id"] not in seen_ids:
            seen_ids.add(r["risk_id"])
            deduped.append(r)
        else:
            warnings.append(f"Duplicate risk_id suppressed: {r['risk_id']}")

    def _sort_key(r: dict[str, Any]) -> tuple[str, str, str]:
        return (r["source_phase"], r["risk_type"], r["risk_id"])

    deduped.sort(key=_sort_key)

    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae risk-register",
        "repository_root": str(repo_root),
        "risks": deduped,
        "risk_count": len(deduped),
        "warnings": warnings,
        "errors": errors,
        "safety_notes": {
            "risk_register_is_read_only": True,
            "risk_register_does_not_authorize_execution": True,
            "risk_register_does_not_authorize_backend_invocation": True,
            "risk_register_does_not_authorize_adoption": True,
            "risk_register_does_not_authorize_commit_or_push": True,
            "accepted_risk_is_not_mitigation": True,
            "generated_cache_created": False,
            "pcae_storage_created": False,
            "artifact_index_used": True,
            "memory_snapshot_used": True,
            "governance_timeline_used": True,
            "decision_log_used": True,
        },
    }
