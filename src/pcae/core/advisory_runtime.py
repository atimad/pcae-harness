"""Advisory Runtime Prototype — Phase 113C.

Observation-only implementation of the Advisory Runtime architecture
frozen in 113A and the contracts frozen in 113B. Introduces advisory
reasoning only — no authorization, no execution, no enforcement.

Architecture:
    Advisory Providers (4 initial) consume RuntimeSnapshot only and
    produce AdvisoryResults.  The Advisory Runtime coordinates
    providers, aggregates results, deduplicates, sorts
    deterministically, and returns a read-only tuple.

Isolation guarantees:
    - Consumes RuntimeSnapshot only — never mutates it.
    - Never calls PermissionBroker.evaluate().
    - Never invokes plugins.
    - Never executes commands.
    - Never authorizes or denies.
    - Stdlib imports plus one internal import (RuntimeSnapshot).

References:
    docs/PCAE_ADVISORY_RUNTIME.md               (113A architecture)
    docs/PCAE_ADVISORY_RUNTIME_CONTRACT.md       (113B contract)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from pcae.core.runtime_snapshot import RuntimeSnapshot


# ═══════════════════════════════════════════════════════════════════════
# Frozen Vocabularies
# ═══════════════════════════════════════════════════════════════════════

#: The nine Runtime Snapshot domains (112E/112F) — used by
#: EvidenceReference validation to ensure every evidence reference
#: points to a real, frozen domain.
RUNTIME_SNAPSHOT_DOMAINS: tuple[str, ...] = (
    "runtime",
    "registry",
    "plugins",
    "capabilities",
    "health",
    "governance",
    "state",
    "version",
    "context",
)

#: The eight Advisory Categories frozen by 113A §4, with extension rules
#: frozen by 113B §4. An open taxonomy — new categories may be added
#: freely; an existing category's meaning is frozen once published.
ADVISORY_CATEGORIES: tuple[str, ...] = (
    "Runtime Health",
    "Governance",
    "Context Consistency",
    "Registry",
    "Plugin Compatibility",
    "Configuration",
    "Operational Readiness",
    "Future extensibility",
)

#: The four Severity Levels frozen by 113A §3, meanings frozen by 113B §5.
#: Never blocks, denies, or authorizes — severity is a hint to human
#: attention, never an enforcement signal.
SEVERITY_LEVELS: tuple[str, ...] = (
    "info",
    "advisory",
    "warning",
    "critical",
)

#: The four Confidence Levels reused verbatim from this codebase's own
#: capability-discovery vocabulary (113A §3), meanings frozen by 113B §5
#: in the advisory context.
CONFIDENCE_LEVELS: tuple[str, ...] = (
    "unknown",
    "observed",
    "validated",
    "proven",
)

#: The six-stage Advisory Lifecycle frozen by 113B §6. A fourth, distinct
#: lifecycle vocabulary — not to be conflated with 110A's Runtime State
#: Model, 110B's Plugin Lifecycle, or 112A's Context Lifecycle.
ADVISORY_LIFECYCLE_STAGES: tuple[str, ...] = (
    "produced",
    "presented",
    "acknowledged",
    "superseded",
    "resolved",
    "dismissed",
)

#: The fixed invariant restated on every AdvisoryResult by whichever
#: Presentation renders it (113B §2). Never a per-instance field since
#: it never varies. Restated here as a module-level constant so every
#: consumer can access it identically.
ADVISORY_INVARIANT: str = (
    "This is an advisory recommendation only. No execution or "
    "authorization follows automatically from it — a human decides, "
    "per 'Recommendation precedes authorization' (113A) and "
    "'Explainability precedes trust' (113B)."
)

#: Severity-to-rank mapping for deterministic sorting. Lower rank
#: appears first (critical=0, then warning, advisory, info).
_SEVERITY_RANK: dict[str, int] = {
    "critical": 0,
    "warning": 1,
    "advisory": 2,
    "info": 3,
}


# ═══════════════════════════════════════════════════════════════════════
# EvidenceReference — 113B §3
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class EvidenceReference:
    """A pointer into a specific Runtime Snapshot field that produced a
    finding, per 113B §3. Evidence is referenced, never stored durably
    (no evidence database, no audit persistence). ``object_id`` is set
    only when the evidence concerns a specific identified object rather
    than a domain-wide fact.

    Four fields frozen by 113B §3:
        domain — one of the nine RuntimeSnapshot domains
        object_id — a specific plugin/context/capability id, or None
        field_path — dot-path into the domain's fields
        evidence_summary — a short gloss of what the evidence shows
    """

    domain: str
    object_id: str | None
    field_path: str
    evidence_summary: str

    def __post_init__(self) -> None:
        if self.domain not in RUNTIME_SNAPSHOT_DOMAINS:
            raise ValueError(
                f"EvidenceReference domain must be one of "
                f"{RUNTIME_SNAPSHOT_DOMAINS}, got {self.domain!r}"
            )
        if not self.field_path:
            raise ValueError("EvidenceReference field_path must be non-empty")
        if not self.evidence_summary:
            raise ValueError("EvidenceReference evidence_summary must be non-empty")


# ═══════════════════════════════════════════════════════════════════════
# AdvisoryResult — 113B §1 (fourteen fields)
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class AdvisoryResult:
    """One frozen advisory recommendation, per 113A §3 and 113B §1.
    Analytical only — never executes, never authorizes, never denies.

    Every result carries the full 8-facet explainability contract
    (113B §2) realized through specific fields, and the fixed invariant
    ``ADVISORY_INVARIANT`` is restated by whichever Presentation renders
    this result.

    Fourteen fields frozen by 113B §1 (113A's nine, extended by five,
    with ``recommendation`` reconciled into 113A's existing
    ``recommended_action`` rather than duplicated):
    """

    # 113A's nine fields
    advisory_id: str
    category: str
    severity: str
    confidence: str
    recommended_action: str
    rationale: str
    evidence_references: tuple[EvidenceReference, ...]
    affected_runtime_objects: tuple[str, ...]
    timestamp: str
    # 113B's five new fields
    source_snapshot_reference: str
    reasoning_summary: str
    alternative_considerations: tuple[str, ...]
    remediation: str
    implementation_status: str

    def __post_init__(self) -> None:
        if not self.advisory_id:
            raise ValueError("AdvisoryResult advisory_id must be non-empty")
        if self.category not in ADVISORY_CATEGORIES:
            raise ValueError(
                f"AdvisoryResult category must be one of "
                f"{ADVISORY_CATEGORIES}, got {self.category!r}"
            )
        if self.severity not in SEVERITY_LEVELS:
            raise ValueError(
                f"AdvisoryResult severity must be one of "
                f"{SEVERITY_LEVELS}, got {self.severity!r}"
            )
        if self.confidence not in CONFIDENCE_LEVELS:
            raise ValueError(
                f"AdvisoryResult confidence must be one of "
                f"{CONFIDENCE_LEVELS}, got {self.confidence!r}"
            )
        if self.implementation_status != "execution_unavailable":
            raise ValueError(
                "AdvisoryResult implementation_status must be "
                f"'execution_unavailable', got {self.implementation_status!r}"
            )
        if not self.timestamp:
            raise ValueError("AdvisoryResult timestamp must be non-empty")
        if not self.recommended_action:
            raise ValueError("AdvisoryResult recommended_action must be non-empty")
        if not self.rationale:
            raise ValueError("AdvisoryResult rationale must be non-empty")
        if not self.reasoning_summary:
            raise ValueError("AdvisoryResult reasoning_summary must be non-empty")
        if not self.remediation:
            raise ValueError("AdvisoryResult remediation must be non-empty")
        if not self.source_snapshot_reference:
            raise ValueError(
                "AdvisoryResult source_snapshot_reference must be non-empty"
            )


# ═══════════════════════════════════════════════════════════════════════
# AdvisoryProvider Protocol — 113C
# ═══════════════════════════════════════════════════════════════════════

class AdvisoryProvider(Protocol):
    """Protocol for an advisory analysis provider. Each provider reads
    exactly one RuntimeSnapshot and produces zero-or-more AdvisoryResult
    records. Providers must never inspect Runtime internals beyond what
    the RuntimeSnapshot surface exposes, must never call
    PermissionBroker.evaluate(), must never invoke plugins, and must
    never execute commands."""

    def analyze(self, snapshot: RuntimeSnapshot) -> tuple[AdvisoryResult, ...]:
        """Produce zero-or-more advisory recommendations from one
        RuntimeSnapshot. Pure analysis only — never mutates the
        snapshot, never executes, never authorizes."""
        ...


# ═══════════════════════════════════════════════════════════════════════
# Provider: RuntimeHealthProvider
# ═══════════════════════════════════════════════════════════════════════

class RuntimeHealthProvider:
    """Checks the RuntimeSnapshot's ``health`` domain (HealthInfo, 111B).

    Reads: execution_availability, runtime_status, registry_status,
    plugin_count, capability_count, metadata_validity,
    current_runtime_state, current_maximum_plugin_capability.

    Category: ``"Runtime Health"``.
    """

    def analyze(self, snapshot: RuntimeSnapshot) -> tuple[AdvisoryResult, ...]:
        health = snapshot.health
        results: list[AdvisoryResult] = []

        # ── Execution availability — always "unavailable" ──────────────
        if health.execution_availability == "unavailable":
            results.append(_make_result(
                category="Runtime Health",
                severity="info",
                confidence="proven",
                summary="Execution availability confirmed: execution remains unavailable",
                rationale=(
                    "The Runtime's execution_availability field reports "
                    f"'{health.execution_availability}' — the expected, "
                    "proven invariant. No execution capability exists in "
                    "this codebase (confirmed by 113B's 25 no-go gates, "
                    "all passed)."
                ),
                action="No action needed. This is the expected state.",
                remediation="None. Execution capability is correctly unavailable.",
                evidence=(EvidenceReference(
                    domain="health",
                    object_id=None,
                    field_path="health.execution_availability",
                    evidence_summary=(
                        f"execution_availability = {health.execution_availability!r} "
                        "(expected: 'unavailable')"
                    ),
                ),),
                affected=(),
                alternatives=(),
            ))

        # ── Runtime status — always "not_implemented" ─────────────────
        if health.runtime_status == "not_implemented":
            results.append(_make_result(
                category="Runtime Health",
                severity="info",
                confidence="proven",
                summary="Runtime not implemented: honest self-report confirmed",
                rationale=(
                    "The Runtime's runtime_status field reports "
                    f"'{health.runtime_status}' — an honest self-report "
                    "that no live Runtime instance exists. This is the "
                    "expected state for v0.1.0-rc1."
                ),
                action="No action needed. Runtime implementation is a future concern.",
                remediation="None at this phase. v0.2 targets autonomy Level 3.",
                evidence=(EvidenceReference(
                    domain="health",
                    object_id=None,
                    field_path="health.runtime_status",
                    evidence_summary=(
                        f"runtime_status = {health.runtime_status!r} "
                        "(expected: 'not_implemented')"
                    ),
                ),),
                affected=(),
                alternatives=(),
            ))

        # ── Registry status ───────────────────────────────────────────
        results.append(_make_result(
            category="Runtime Health",
            severity="info",
            confidence="observed",
            summary=f"Registry status: {health.registry_status}",
            rationale=(
                f"The Registry reports status '{health.registry_status}'. "
                "This is a metadata-level report; no live registry "
                "verification is performed by this provider."
            ),
            action="No action needed. Registry status is informational.",
            remediation="None.",
            evidence=(EvidenceReference(
                domain="health",
                object_id=None,
                field_path="health.registry_status",
                evidence_summary=(
                    f"registry_status = {health.registry_status!r}"
                ),
            ),),
            affected=(),
            alternatives=(),
        ))

        # ── Plugin count ──────────────────────────────────────────────
        if health.plugin_count == 0:
            results.append(_make_result(
                category="Runtime Health",
                severity="info",
                confidence="observed",
                summary="No plugins registered — expected in prototype phase",
                rationale=(
                    f"Plugin count is {health.plugin_count}. No plugins "
                    "are registered, which is expected in this prototype "
                    "phase. A plugin registry exists but contains no entries."
                ),
                action="No action needed.",
                remediation="None.",
                evidence=(EvidenceReference(
                    domain="health",
                    object_id=None,
                    field_path="health.plugin_count",
                    evidence_summary=f"plugin_count = {health.plugin_count}",
                ),),
                affected=(),
                alternatives=(),
            ))

        # ── Capability count ──────────────────────────────────────────
        if health.capability_count == 0:
            results.append(_make_result(
                category="Runtime Health",
                severity="info",
                confidence="observed",
                summary="No capabilities registered — expected in prototype phase",
                rationale=(
                    f"Capability count is {health.capability_count}. "
                    "No capabilities are declared, which is expected."
                ),
                action="No action needed.",
                remediation="None.",
                evidence=(EvidenceReference(
                    domain="health",
                    object_id=None,
                    field_path="health.capability_count",
                    evidence_summary=f"capability_count = {health.capability_count}",
                ),),
                affected=(),
                alternatives=(),
            ))

        # ── Metadata validity ─────────────────────────────────────────
        if health.metadata_validity == "valid":
            results.append(_make_result(
                category="Runtime Health",
                severity="info",
                confidence="observed",
                summary="Registry metadata is internally consistent",
                rationale=(
                    f"Metadata validity reports '{health.metadata_validity}'. "
                    "The registry's stored metadata is internally consistent."
                ),
                action="No action needed.",
                remediation="None.",
                evidence=(EvidenceReference(
                    domain="health",
                    object_id=None,
                    field_path="health.metadata_validity",
                    evidence_summary=(
                        f"metadata_validity = {health.metadata_validity!r}"
                    ),
                ),),
                affected=(),
                alternatives=(),
            ))

        # ── Current runtime state — always "Observed" ─────────────────
        if health.current_runtime_state == "Observed":
            results.append(_make_result(
                category="Runtime Health",
                severity="info",
                confidence="proven",
                summary="Runtime state is Observed — the maximum current state",
                rationale=(
                    f"Current runtime state is '{health.current_runtime_state}'. "
                    "This is the maximum state reachable without execution "
                    "capability (per 110A's 8-state model)."
                ),
                action="No action needed. This is the expected maximum state.",
                remediation="None. 'Observed' is the ceiling until execution is enabled.",
                evidence=(EvidenceReference(
                    domain="health",
                    object_id=None,
                    field_path="health.current_runtime_state",
                    evidence_summary=(
                        f"current_runtime_state = "
                        f"{health.current_runtime_state!r} (expected: 'Observed')"
                    ),
                ),),
                affected=(),
                alternatives=(),
            ))

        # ── Maximum plugin capability — always "observe" ──────────────
        if health.current_maximum_plugin_capability == "observe":
            results.append(_make_result(
                category="Runtime Health",
                severity="info",
                confidence="proven",
                summary="Maximum plugin capability is 'observe' — the ceiling",
                rationale=(
                    f"Maximum plugin capability is "
                    f"'{health.current_maximum_plugin_capability}'. "
                    "'observe' is the highest capability any plugin can "
                    "declare today. No plugin can enforce, execute, or "
                    "authorize."
                ),
                action="No action needed. This is the expected capability ceiling.",
                remediation="None. 'observe' is the correct ceiling.",
                evidence=(EvidenceReference(
                    domain="health",
                    object_id=None,
                    field_path="health.current_maximum_plugin_capability",
                    evidence_summary=(
                        f"current_maximum_plugin_capability = "
                        f"{health.current_maximum_plugin_capability!r} "
                        "(expected: 'observe')"
                    ),
                ),),
                affected=(),
                alternatives=(),
            ))

        return tuple(results)


# ═══════════════════════════════════════════════════════════════════════
# Provider: GovernanceProvider
# ═══════════════════════════════════════════════════════════════════════

class GovernanceProvider:
    """Checks the RuntimeSnapshot's ``governance`` domain
    (GovernanceInfo, 111B).

    Reads: non_executing_posture, broker_implementation_status,
    observed_command_paths, execution_capability.

    Category: ``"Governance"``.
    """

    def analyze(self, snapshot: RuntimeSnapshot) -> tuple[AdvisoryResult, ...]:
        gov = snapshot.governance
        results: list[AdvisoryResult] = []

        # ── Non-executing posture — always True ───────────────────────
        results.append(_make_result(
            category="Governance",
            severity="info",
            confidence="proven",
            summary="Non-executing posture confirmed — the governance guarantee holds",
            rationale=(
                f"non_executing_posture is {gov.non_executing_posture}. "
                "This is the absolute governance guarantee: the harness "
                "will not execute commands. Every governance phase "
                "since 107A has upheld this invariant."
            ),
            action="No action needed. This is the expected, proven posture.",
            remediation="None. Non-executing posture is the correct state.",
            evidence=(EvidenceReference(
                domain="governance",
                object_id=None,
                field_path="governance.non_executing_posture",
                evidence_summary=(
                    f"non_executing_posture = {gov.non_executing_posture} "
                    "(expected: True)"
                ),
            ),),
            affected=(),
            alternatives=(),
        ))

        # ── Broker implementation status ──────────────────────────────
        results.append(_make_result(
            category="Governance",
            severity="info",
            confidence="proven",
            summary="Permission Broker: execution unavailable",
            rationale=(
                f"broker_implementation_status is "
                f"'{gov.broker_implementation_status}'. The Permission "
                "Broker exists as a decision model (108A) but cannot "
                "enforce or execute decisions."
            ),
            action="No action needed.",
            remediation="None.",
            evidence=(EvidenceReference(
                domain="governance",
                object_id=None,
                field_path="governance.broker_implementation_status",
                evidence_summary=(
                    f"broker_implementation_status = "
                    f"{gov.broker_implementation_status!r}"
                ),
            ),),
            affected=(),
            alternatives=(),
        ))

        # ── Observed command paths ────────────────────────────────────
        results.append(_make_result(
            category="Governance",
            severity="info",
            confidence="observed",
            summary=f"Observation integrations active: {gov.observed_command_paths}",
            rationale=(
                f"{gov.observed_command_paths} observation integration(s) "
                "are active (INT-001 through INT-004). Each is "
                "observation-only — none can execute, authorize, or "
                "mutate state."
            ),
            action="No action needed. Observation integrations are read-only by design.",
            remediation="None.",
            evidence=(EvidenceReference(
                domain="governance",
                object_id=None,
                field_path="governance.observed_command_paths",
                evidence_summary=(
                    f"observed_command_paths = {gov.observed_command_paths}"
                ),
            ),),
            affected=(),
            alternatives=(),
        ))

        # ── Execution capability — always "unavailable" ───────────────
        results.append(_make_result(
            category="Governance",
            severity="info",
            confidence="proven",
            summary="Execution capability: unavailable — confirmed",
            rationale=(
                f"execution_capability is '{gov.execution_capability}'. "
                "No execution capability exists. This is the expected, "
                "proven invariant for v0.1.0-rc1."
            ),
            action="No action needed.",
            remediation="None. Execution capability is correctly unavailable.",
            evidence=(EvidenceReference(
                domain="governance",
                object_id=None,
                field_path="governance.execution_capability",
                evidence_summary=(
                    f"execution_capability = {gov.execution_capability!r} "
                    "(expected: 'unavailable')"
                ),
            ),),
            affected=(),
            alternatives=(),
        ))

        return tuple(results)


# ═══════════════════════════════════════════════════════════════════════
# Provider: RuntimeContextProvider
# ═══════════════════════════════════════════════════════════════════════

class RuntimeContextProvider:
    """Checks the RuntimeSnapshot's ``context`` domain (RuntimeContext, 112C).

    Reads: context (may be None), context.session (may be None),
    session.session_id, session.tasks, session.observation.

    Handles ``context is None`` gracefully — this is not an error; it
    means ``.pcae/session.json`` does not exist (uninitialized repo).

    Category: ``"Context Consistency"``.
    """

    def analyze(self, snapshot: RuntimeSnapshot) -> tuple[AdvisoryResult, ...]:
        ctx = snapshot.context
        results: list[AdvisoryResult] = []

        if ctx is None:
            results.append(_make_result(
                category="Context Consistency",
                severity="advisory",
                confidence="observed",
                summary="No Runtime Context available — session state absent",
                rationale=(
                    "The RuntimeSnapshot's context field is None. This "
                    "means .pcae/session.json does not exist — the "
                    "repository may be uninitialized, or no governed "
                    "session has been bootstrapped. Without a session, "
                    "no task/phase/intent state can be reported."
                ),
                action=(
                    "If this is a governed PCAE repository, run "
                    "'pcae session bootstrap --agent-id <id>' to initialize "
                    "session state."
                ),
                remediation=(
                    "Run 'pcae session bootstrap --agent-id <agent-id>' "
                    "to create .pcae/session.json and establish session state."
                ),
                evidence=(EvidenceReference(
                    domain="context",
                    object_id=None,
                    field_path="context",
                    evidence_summary="context is None — no session state exists",
                ),),
                affected=("RuntimeContext",),
                alternatives=(
                    "The repo may not be a PCAE-governed repo at all; "
                    "this is valid for non-PCAE directories.",
                ),
            ))
            return tuple(results)

        # Context exists — check session
        session = ctx.session

        if session is None:
            results.append(_make_result(
                category="Context Consistency",
                severity="advisory",
                confidence="observed",
                summary="Runtime Context exists but has no session",
                rationale=(
                    "RuntimeContext exists (lifecycle_stage="
                    f"'{ctx.lifecycle_stage}') but its session field is "
                    "None. This is an unusual state — a context without "
                    "a session cannot report any meaningful operational "
                    "state."
                ),
                action="Verify session state integrity.",
                remediation="Re-bootstrap the session if this persists.",
                evidence=(EvidenceReference(
                    domain="context",
                    object_id=None,
                    field_path="context.session",
                    evidence_summary="context.session is None",
                ),),
                affected=("RuntimeContext", "RuntimeSession"),
                alternatives=(),
            ))
            return tuple(results)

        # ── Session exists — report session state ─────────────────────
        task_count = len(session.tasks)
        if task_count == 0:
            results.append(_make_result(
                category="Context Consistency",
                severity="info",
                confidence="observed",
                summary="Session is idle — no active tasks",
                rationale=(
                    f"Session '{session.session_id}' exists (lifecycle_stage="
                    f"'{session.lifecycle_stage}') but has no active tasks. "
                    "The repository is in an idle state between phases."
                ),
                action="No action needed. Idle is a valid session state.",
                remediation="None.",
                evidence=(EvidenceReference(
                    domain="context",
                    object_id=session.session_id,
                    field_path="context.session.tasks",
                    evidence_summary=(
                        f"session.tasks is empty (session_id="
                        f"{session.session_id!r})"
                    ),
                ),),
                affected=(session.session_id,),
                alternatives=(),
            ))
        else:
            for task in session.tasks:
                results.append(_make_result(
                    category="Context Consistency",
                    severity="info",
                    confidence="observed",
                    summary=f"Active task: {task.title or task.task_id}",
                    rationale=(
                        f"Session '{session.session_id}' has active task "
                        f"'{task.task_id}' (title: '{task.title}', "
                        f"lifecycle_stage: '{task.lifecycle_stage}')."
                    ),
                    action="Continue governed work on this task.",
                    remediation="None.",
                    evidence=(EvidenceReference(
                        domain="context",
                        object_id=task.task_id,
                        field_path="context.session.tasks",
                        evidence_summary=(
                            f"task_id={task.task_id!r}, "
                            f"title={task.title!r}, "
                            f"lifecycle_stage={task.lifecycle_stage!r}"
                        ),
                    ),),
                    affected=(task.task_id, session.session_id),
                    alternatives=(),
                ))

        # ── Observation context ───────────────────────────────────────
        if session.observation is not None:
            obs = session.observation
            integration_list = ", ".join(obs.consulted_integrations) if obs.consulted_integrations else "none"
            results.append(_make_result(
                category="Context Consistency",
                severity="info",
                confidence="observed",
                summary=f"Observation active: {len(obs.consulted_integrations)} integration(s)",
                rationale=(
                    f"Observation context '{obs.observation_id}' is active "
                    f"(lifecycle_stage: '{obs.lifecycle_stage}'). "
                    f"Consulted integrations: {integration_list}. "
                    "All are observation-only."
                ),
                action="No action needed.",
                remediation="None.",
                evidence=(EvidenceReference(
                    domain="context",
                    object_id=obs.observation_id,
                    field_path="context.session.observation",
                    evidence_summary=(
                        f"observation_id={obs.observation_id!r}, "
                        f"integrations=[{integration_list}]"
                    ),
                ),),
                affected=(obs.observation_id, session.session_id),
                alternatives=(),
            ))

        return tuple(results)


# ═══════════════════════════════════════════════════════════════════════
# Provider: RegistryProvider
# ═══════════════════════════════════════════════════════════════════════

class RegistryProvider:
    """Checks the RuntimeSnapshot's ``registry`` domain
    (RegistrySnapshot, 110E).

    Reads: registered_plugin_count, registered_capability_count,
    registry_status, metadata_validity, plugin_ids, capabilities.

    Category: ``"Registry"``.
    """

    def analyze(self, snapshot: RuntimeSnapshot) -> tuple[AdvisoryResult, ...]:
        reg = snapshot.registry
        results: list[AdvisoryResult] = []

        # ── Registry status ───────────────────────────────────────────
        results.append(_make_result(
            category="Registry",
            severity="info",
            confidence="observed",
            summary=f"Registry status: {reg.registry_status}",
            rationale=(
                f"The Runtime Registry reports status "
                f"'{reg.registry_status}'. This is the registry's own "
                "self-reported health, not an external verification."
            ),
            action="No action needed.",
            remediation="None.",
            evidence=(EvidenceReference(
                domain="registry",
                object_id=None,
                field_path="registry.registry_status",
                evidence_summary=f"registry_status = {reg.registry_status!r}",
            ),),
            affected=(),
            alternatives=(),
        ))

        # ── Plugin count ──────────────────────────────────────────────
        results.append(_make_result(
            category="Registry",
            severity="info",
            confidence="observed",
            summary=f"Registered plugins: {reg.registered_plugin_count}",
            rationale=(
                f"The registry contains {reg.registered_plugin_count} "
                "registered plugin(s). In this prototype phase, zero "
                "plugins are expected."
            ),
            action="No action needed.",
            remediation="None.",
            evidence=(EvidenceReference(
                domain="registry",
                object_id=None,
                field_path="registry.registered_plugin_count",
                evidence_summary=(
                    f"registered_plugin_count = {reg.registered_plugin_count}"
                ),
            ),),
            affected=(),
            alternatives=(),
        ))

        # ── Capability count ──────────────────────────────────────────
        results.append(_make_result(
            category="Registry",
            severity="info",
            confidence="observed",
            summary=f"Registered capabilities: {reg.registered_capability_count}",
            rationale=(
                f"The registry declares {reg.registered_capability_count} "
                "capability/capabilities. In this prototype phase, zero "
                "are expected."
            ),
            action="No action needed.",
            remediation="None.",
            evidence=(EvidenceReference(
                domain="registry",
                object_id=None,
                field_path="registry.registered_capability_count",
                evidence_summary=(
                    f"registered_capability_count = "
                    f"{reg.registered_capability_count}"
                ),
            ),),
            affected=(),
            alternatives=(),
        ))

        # ── Metadata validity ─────────────────────────────────────────
        results.append(_make_result(
            category="Registry",
            severity="info",
            confidence="observed",
            summary=f"Registry metadata: {reg.metadata_validity}",
            rationale=(
                f"Registry metadata validity is '{reg.metadata_validity}'. "
                "This confirms the registry's stored metadata is internally "
                "consistent according to its own validity rules."
            ),
            action="No action needed.",
            remediation="None.",
            evidence=(EvidenceReference(
                domain="registry",
                object_id=None,
                field_path="registry.metadata_validity",
                evidence_summary=f"metadata_validity = {reg.metadata_validity!r}",
            ),),
            affected=(),
            alternatives=(),
        ))

        # ── Plugin IDs ────────────────────────────────────────────────
        if reg.plugin_ids:
            plugin_list = ", ".join(reg.plugin_ids)
            results.append(_make_result(
                category="Registry",
                severity="info",
                confidence="observed",
                summary=f"Registered plugin IDs: {plugin_list}",
                rationale=(
                    f"The registry lists {len(reg.plugin_ids)} plugin "
                    f"ID(s): {plugin_list}."
                ),
                action="No action needed.",
                remediation="None.",
                evidence=(EvidenceReference(
                    domain="registry",
                    object_id=None,
                    field_path="registry.plugin_ids",
                    evidence_summary=f"plugin_ids = [{plugin_list}]",
                ),),
                affected=reg.plugin_ids,
                alternatives=(),
            ))

        # ── Capability IDs ────────────────────────────────────────────
        if reg.capabilities:
            cap_list = ", ".join(reg.capabilities)
            results.append(_make_result(
                category="Registry",
                severity="info",
                confidence="observed",
                summary=f"Registered capability IDs: {cap_list}",
                rationale=(
                    f"The registry lists {len(reg.capabilities)} "
                    f"capability/capabilities: {cap_list}."
                ),
                action="No action needed.",
                remediation="None.",
                evidence=(EvidenceReference(
                    domain="registry",
                    object_id=None,
                    field_path="registry.capabilities",
                    evidence_summary=f"capabilities = [{cap_list}]",
                ),),
                affected=reg.capabilities,
                alternatives=(),
            ))

        return tuple(results)


# ═══════════════════════════════════════════════════════════════════════
# Aggregation
# ═══════════════════════════════════════════════════════════════════════

def _severity_rank(severity: str) -> int:
    """Map severity to a sort-rank integer. Lower = more urgent.
    critical=0, warning=1, advisory=2, info=3. Unknown severities
    sort last (rank 99) as a fail-closed precaution."""
    return _SEVERITY_RANK.get(severity, 99)


def _deduplicate(results: list[AdvisoryResult]) -> list[AdvisoryResult]:
    """Deduplicate results by fingerprint: (category, evidence domain
    tuple, evidence field_path tuple).  Keep the first occurrence
    (deterministic since provider iteration order is fixed)."""
    seen: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
    kept: list[AdvisoryResult] = []
    for result in results:
        domains = tuple(ev.domain for ev in result.evidence_references)
        field_paths = tuple(ev.field_path for ev in result.evidence_references)
        fingerprint = (result.category, domains, field_paths)
        if fingerprint not in seen:
            seen.add(fingerprint)
            kept.append(result)
    return kept


def _sort_results(results: list[AdvisoryResult]) -> list[AdvisoryResult]:
    """Sort deterministically: by severity rank, then category
    alphabetically, then first evidence field_path alphabetically."""
    return sorted(
        results,
        key=lambda r: (
            _severity_rank(r.severity),
            r.category,
            r.evidence_references[0].field_path if r.evidence_references else "",
        ),
    )


def _assign_ids(
    results: list[AdvisoryResult],
) -> list[AdvisoryResult]:
    """Assign stable, deterministic advisory IDs after sorting.
    Format: ``ADV-{category_slug}-{seq:04d}``."""
    counter: dict[str, int] = {}
    assigned: list[AdvisoryResult] = []
    for result in results:
        slug = result.category.lower().replace(" ", "_")
        counter[slug] = counter.get(slug, 0) + 1
        new_id = f"ADV-{slug}-{counter[slug]:04d}"
        assigned.append(_replace(result, advisory_id=new_id))
    return assigned


def _derive_source_ref(snapshot: RuntimeSnapshot, timestamp: str) -> str:
    """Derive the source snapshot reference from session context if
    available, falling back to a timestamp-based reference."""
    if snapshot.context is not None and snapshot.context.session is not None:
        sid = snapshot.context.session.session_id
        return f"snapshot-{sid}"
    return f"snapshot-{timestamp}"


def _aggregate(
    results: list[AdvisoryResult],
    snapshot: RuntimeSnapshot,
    timestamp: str,
) -> tuple[AdvisoryResult, ...]:
    """Aggregate raw provider results: set shared fields, deduplicate,
    sort, assign IDs, return as immutable tuple."""
    source_ref = _derive_source_ref(snapshot, timestamp)

    # Set shared fields on every result
    stamped: list[AdvisoryResult] = []
    for r in results:
        stamped.append(_replace(
            r,
            timestamp=timestamp,
            source_snapshot_reference=source_ref,
        ))

    deduped = _deduplicate(stamped)
    sorted_results = _sort_results(deduped)
    identified = _assign_ids(sorted_results)

    return tuple(identified)


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _make_result(
    *,
    category: str,
    severity: str,
    confidence: str,
    summary: str,
    rationale: str,
    action: str,
    remediation: str,
    evidence: tuple[EvidenceReference, ...],
    affected: tuple[str, ...],
    alternatives: tuple[str, ...],
) -> AdvisoryResult:
    """Construct an AdvisoryResult with placeholder values for fields
    that are set during aggregation (advisory_id, timestamp,
    source_snapshot_reference)."""

    return AdvisoryResult(
        advisory_id="pending",  # Assigned during aggregation
        category=category,
        severity=severity,
        confidence=confidence,
        recommended_action=action,
        rationale=rationale,
        evidence_references=evidence,
        affected_runtime_objects=affected,
        timestamp="pending",  # Set during aggregation
        source_snapshot_reference="pending",  # Set during aggregation
        reasoning_summary=summary,
        alternative_considerations=alternatives,
        remediation=remediation,
        implementation_status="execution_unavailable",
    )


def _replace(result: AdvisoryResult, **kwargs: object) -> AdvisoryResult:
    """Return a new AdvisoryResult with specified fields replaced.
    Uses dataclasses.replace internally — this is a thin wrapper
    that preserves the frozen invariant."""
    from dataclasses import replace
    return replace(result, **kwargs)


# ═══════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════

def build_advisory_results(snapshot: RuntimeSnapshot) -> tuple[AdvisoryResult, ...]:
    """Produce the complete set of advisory recommendations for one
    RuntimeSnapshot.

    Coordinates all providers, aggregates results, deduplicates, sorts
    deterministically, and assigns stable advisory IDs.  Pure function
    — never mutates the snapshot, never executes, never authorizes,
    never calls PermissionBroker.evaluate().

    Returns:
        A tuple of AdvisoryResult records, sorted by severity (critical
        first), then category, then evidence field_path. The tuple may
        be empty if no provider produced results (unlikely — the health
        and governance providers always produce results for known
        invariants).
    """

    now = datetime.now(timezone.utc).isoformat()

    providers: tuple[AdvisoryProvider, ...] = (
        RuntimeHealthProvider(),
        GovernanceProvider(),
        RuntimeContextProvider(),
        RegistryProvider(),
    )

    collected: list[AdvisoryResult] = []
    for provider in providers:
        collected.extend(provider.analyze(snapshot))

    return _aggregate(collected, snapshot, now)
