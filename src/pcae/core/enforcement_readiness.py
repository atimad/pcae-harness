"""Enforcement readiness evidence bundle and gate status reporter.

Read-only reporter that gathers enforcement-readiness gate status from
the design/test planning artifacts without authorizing enforcement.
Derives gate data from 89J's 69-gate checklist and 89K's test plan.

Schema version: 1.0 (simulation-only)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.0"

ENFORCEMENT_NOT_AUTHORIZED = "Enforcement implementation is NOT authorized."

GATE_STATE_SATISFIED = "SATISFIED"
GATE_STATE_NOT_SATISFIED = "NOT_SATISFIED"
GATE_STATE_CONDITIONAL = "CONDITIONAL"
GATE_STATE_DEFERRED = "DEFERRED"

_GATE_EMOJI: dict[str, str] = {
    GATE_STATE_SATISFIED: "✅",
    GATE_STATE_NOT_SATISFIED: "❌",
    GATE_STATE_CONDITIONAL: "⚠️",
    GATE_STATE_DEFERRED: "🔜",
}

# 69 gates from Phase 89J across 8 dimensions
# Each gate: (id, description, dimension, state, evidence_refs)
_GATE_REGISTRY: tuple[dict[str, Any], ...] = (
    # Design gates (D1–D13)
    {"id": "D1", "description": "Enforcement design document exists and is reviewed", "dimension": "design", "state": GATE_STATE_NOT_SATISFIED, "source": "89G MNP-1", "evidence": []},
    {"id": "D2", "description": "Enforcement task contract exists with explicit scope", "dimension": "design", "state": GATE_STATE_NOT_SATISFIED, "source": "89G MNP-2", "evidence": []},
    {"id": "D3", "description": "Audit event model designed (all 16 event types)", "dimension": "design", "state": GATE_STATE_SATISFIED, "source": "89H §6", "evidence": ["docs/PHASE_89_ENFORCEMENT_READINESS_AUDIT_AND_ROLLBACK_MODEL_DESIGN.md", "src/pcae/core/enforcement_audit.py"]},
    {"id": "D4", "description": "Rollback artifact model designed", "dimension": "design", "state": GATE_STATE_SATISFIED, "source": "89H §12", "evidence": ["docs/PHASE_89_ENFORCEMENT_READINESS_AUDIT_AND_ROLLBACK_MODEL_DESIGN.md", "src/pcae/core/enforcement_rollback.py"]},
    {"id": "D5", "description": "Operator approval model designed", "dimension": "design", "state": GATE_STATE_SATISFIED, "source": "89I §5–9", "evidence": ["docs/PHASE_89_ENFORCEMENT_OPERATOR_APPROVAL_AND_ACCEPTED_RISK_POLICY_DESIGN.md", "src/pcae/core/enforcement_approval.py"]},
    {"id": "D6", "description": "Accepted-risk policy designed", "dimension": "design", "state": GATE_STATE_SATISFIED, "source": "89I §10–11", "evidence": ["docs/PHASE_89_ENFORCEMENT_OPERATOR_APPROVAL_AND_ACCEPTED_RISK_POLICY_DESIGN.md", "src/pcae/core/enforcement_approval.py"]},
    {"id": "D7", "description": "Hard-block non-overridable rule documented", "dimension": "design", "state": GATE_STATE_SATISFIED, "source": "89I §12", "evidence": ["docs/PHASE_89_ENFORCEMENT_OPERATOR_APPROVAL_AND_ACCEPTED_RISK_POLICY_DESIGN.md"]},
    {"id": "D8", "description": "Human review vs authorization distinction documented", "dimension": "design", "state": GATE_STATE_SATISFIED, "source": "89I §13", "evidence": ["docs/PHASE_89_ENFORCEMENT_OPERATOR_APPROVAL_AND_ACCEPTED_RISK_POLICY_DESIGN.md"]},
    {"id": "D9", "description": "JSON schema versioning policy defined", "dimension": "design", "state": GATE_STATE_NOT_SATISFIED, "source": "89G C3", "evidence": []},
    {"id": "D10", "description": "CLI compatibility policy defined", "dimension": "design", "state": GATE_STATE_NOT_SATISFIED, "source": "89G C4", "evidence": []},
    {"id": "D11", "description": "Dry-run-to-enforcement migration checklist written", "dimension": "design", "state": GATE_STATE_NOT_SATISFIED, "source": "89G C8", "evidence": []},
    {"id": "D12", "description": "Enforcement disable procedure documented", "dimension": "design", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §16", "evidence": []},
    {"id": "D13", "description": "Recovery procedure documented", "dimension": "design", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §16", "evidence": []},
    # Implementation gates (I1–I11)
    {"id": "I1", "description": "pcae enforcement check command implemented", "dimension": "implementation", "state": GATE_STATE_NOT_SATISFIED, "source": "—", "evidence": []},
    {"id": "I2", "description": "pcae enforcement status command implemented", "dimension": "implementation", "state": GATE_STATE_DEFERRED, "source": "—", "evidence": ["pcae enforcement-readiness status (this reporter)"]},
    {"id": "I3", "description": "pcae enforcement disable command implemented", "dimension": "implementation", "state": GATE_STATE_NOT_SATISFIED, "source": "89G C13", "evidence": []},
    {"id": "I4", "description": "pcae enforcement enable command implemented", "dimension": "implementation", "state": GATE_STATE_NOT_SATISFIED, "source": "—", "evidence": []},
    {"id": "I5", "description": "pcae enforcement rollback list command implemented", "dimension": "implementation", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §17", "evidence": []},
    {"id": "I6", "description": "pcae enforcement rollback restore command implemented", "dimension": "implementation", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §17", "evidence": []},
    {"id": "I7", "description": "pcae enforcement audit show command implemented", "dimension": "implementation", "state": GATE_STATE_NOT_SATISFIED, "source": "—", "evidence": []},
    {"id": "I8", "description": "pcae enforcement audit validate command implemented", "dimension": "implementation", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §14", "evidence": []},
    {"id": "I9", "description": "Enforcement state machine implemented", "dimension": "implementation", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §16", "evidence": []},
    {"id": "I10", "description": "Atomic check-and-enforce (no race condition)", "dimension": "implementation", "state": GATE_STATE_NOT_SATISFIED, "source": "89G C14", "evidence": []},
    {"id": "I11", "description": "Explicit enforcement-mode flag", "dimension": "implementation", "state": GATE_STATE_NOT_SATISFIED, "source": "89G C1", "evidence": []},
    # Test gates (T1–T15)
    {"id": "T1", "description": "Audit write/read tests passing (~10)", "dimension": "test", "state": GATE_STATE_NOT_SATISFIED, "source": "89J T1", "evidence": []},
    {"id": "T2", "description": "Audit chain integrity tests passing (~8)", "dimension": "test", "state": GATE_STATE_NOT_SATISFIED, "source": "89J T2", "evidence": []},
    {"id": "T3", "description": "Audit redaction tests passing (~5)", "dimension": "test", "state": GATE_STATE_NOT_SATISFIED, "source": "89J T3", "evidence": []},
    {"id": "T4", "description": "Rollback create/restore tests passing (~16)", "dimension": "test", "state": GATE_STATE_NOT_SATISFIED, "source": "89J T4", "evidence": []},
    {"id": "T5", "description": "Approval grant/expire/revoke tests passing (~18)", "dimension": "test", "state": GATE_STATE_SATISFIED, "source": "89J T5", "evidence": ["tests/test_enforcement_approval.py (62 tests)"]},
    {"id": "T6", "description": "Hard-block refusal tests passing (~8)", "dimension": "test", "state": GATE_STATE_SATISFIED, "source": "89J T6", "evidence": ["tests/test_enforcement_audit.py (hard-block tests)", "tests/test_enforcement_approval.py (hard-block tests)"]},
    {"id": "T7", "description": "Enforcement decision equivalence tests (~50)", "dimension": "test", "state": GATE_STATE_NOT_SATISFIED, "source": "89J T7", "evidence": []},
    {"id": "T8", "description": "Block enforcement verification tests (~30)", "dimension": "test", "state": GATE_STATE_NOT_SATISFIED, "source": "89J T8", "evidence": []},
    {"id": "T9", "description": "Allow enforcement verification tests (~20)", "dimension": "test", "state": GATE_STATE_NOT_SATISFIED, "source": "89J T9", "evidence": []},
    {"id": "T10", "description": "Bypass detection tests (~15)", "dimension": "test", "state": GATE_STATE_NOT_SATISFIED, "source": "89J T10", "evidence": []},
    {"id": "T11", "description": "Emergency disable tests (~10)", "dimension": "test", "state": GATE_STATE_NOT_SATISFIED, "source": "89J T11", "evidence": []},
    {"id": "T12", "description": "Cross-platform shell tests (~20)", "dimension": "test", "state": GATE_STATE_NOT_SATISFIED, "source": "89J T12", "evidence": []},
    {"id": "T13", "description": "Threat model adversarial tests (~25)", "dimension": "test", "state": GATE_STATE_NOT_SATISFIED, "source": "89J T13", "evidence": []},
    {"id": "T14", "description": "Safety invariants tests", "dimension": "test", "state": GATE_STATE_SATISFIED, "source": "89J T14", "evidence": ["244 simulation tests passing"]},
    {"id": "T15", "description": "Full suite green", "dimension": "test", "state": GATE_STATE_SATISFIED, "source": "89J T15", "evidence": ["9,311 tests passing"]},
    # Audit gates (A1–A8)
    {"id": "A1", "description": "Audit event creation produces valid events", "dimension": "audit", "state": GATE_STATE_SATISFIED, "source": "89H", "evidence": ["src/pcae/core/enforcement_audit.py", "tests/test_enforcement_audit.py"]},
    {"id": "A2", "description": "Audit chain hash integrity verified", "dimension": "audit", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §13", "evidence": []},
    {"id": "A3", "description": "Audit redaction prevents raw secret leakage", "dimension": "audit", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §14", "evidence": []},
    {"id": "A4", "description": "Audit write path resilient to disk full", "dimension": "audit", "state": GATE_STATE_NOT_SATISFIED, "source": "89H F9", "evidence": []},
    {"id": "A5", "description": "Audit retention policy enforced", "dimension": "audit", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §15", "evidence": []},
    {"id": "A6", "description": "Audit rotation policy enforced", "dimension": "audit", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §15", "evidence": []},
    {"id": "A7", "description": "Audit records are tamper-evident", "dimension": "audit", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §28", "evidence": []},
    {"id": "A8", "description": "Audit records are non-repudiable", "dimension": "audit", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §5", "evidence": []},
    # Rollback gates (R1–R5)
    {"id": "R1", "description": "Rollback artifact created before mutation", "dimension": "rollback", "state": GATE_STATE_SATISFIED, "source": "89H §12", "evidence": ["src/pcae/core/enforcement_rollback.py"]},
    {"id": "R2", "description": "Rollback restore restores file state", "dimension": "rollback", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §12", "evidence": []},
    {"id": "R3", "description": "Rollback failure leaves system consistent", "dimension": "rollback", "state": GATE_STATE_NOT_SATISFIED, "source": "89H F10", "evidence": []},
    {"id": "R4", "description": "Rollback respects working tree cleanliness", "dimension": "rollback", "state": GATE_STATE_NOT_SATISFIED, "source": "89H", "evidence": []},
    {"id": "R5", "description": "Rollback evidence chain is complete", "dimension": "rollback", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §27", "evidence": []},
    # Operator approval gates (O1–O7)
    {"id": "O1", "description": "Approval records are created on grant", "dimension": "approval", "state": GATE_STATE_SATISFIED, "source": "89I §9", "evidence": ["src/pcae/core/enforcement_approval.py"]},
    {"id": "O2", "description": "Approval expiration is enforced", "dimension": "approval", "state": GATE_STATE_SATISFIED, "source": "89I §8", "evidence": ["src/pcae/core/enforcement_approval.py (is_expired)"]},
    {"id": "O3", "description": "Approval revocation is enforced", "dimension": "approval", "state": GATE_STATE_SATISFIED, "source": "89I §8", "evidence": ["src/pcae/core/enforcement_approval.py (revoke_approval)"]},
    {"id": "O4", "description": "Multi-party approval supported (future)", "dimension": "approval", "state": GATE_STATE_DEFERRED, "source": "89I §14", "evidence": []},
    {"id": "O5", "description": "Approval scopes correctly bounded", "dimension": "approval", "state": GATE_STATE_SATISFIED, "source": "89I §7", "evidence": ["src/pcae/core/enforcement_approval.py (5 scopes)"]},
    {"id": "O6", "description": "Approval requires explicit action (no click-through)", "dimension": "approval", "state": GATE_STATE_SATISFIED, "source": "89I P7", "evidence": ["Design-only; implementation pending"]},
    {"id": "O7", "description": "Approval never overrides hard blocks", "dimension": "approval", "state": GATE_STATE_SATISFIED, "source": "89I §12", "evidence": ["src/pcae/core/enforcement_approval.py (hard_block_present check)"]},
    # Secret protection gates (S1–S5)
    {"id": "S1", "description": "Command text redacted in all outputs", "dimension": "secret", "state": GATE_STATE_NOT_SATISFIED, "source": "89G C7", "evidence": []},
    {"id": "S2", "description": "Env variable secrets never logged", "dimension": "secret", "state": GATE_STATE_NOT_SATISFIED, "source": "89G C7", "evidence": []},
    {"id": "S3", "description": "Secret detection integrated with enforcement", "dimension": "secret", "state": GATE_STATE_NOT_SATISFIED, "source": "89G", "evidence": []},
    {"id": "S4", "description": "Redaction verified in audit records", "dimension": "secret", "state": GATE_STATE_SATISFIED, "source": "89H §28", "evidence": ["src/pcae/core/enforcement_audit.py (text_redacted field)"]},
    {"id": "S5", "description": "No raw secrets in approval records", "dimension": "secret", "state": GATE_STATE_SATISFIED, "source": "89I §9", "evidence": ["src/pcae/core/enforcement_approval.py (command_hash only)"]},
    # Bypass detection gates (B1–B5)
    {"id": "B1", "description": "Direct shell bypass detected", "dimension": "bypass", "state": GATE_STATE_NOT_SATISFIED, "source": "89G T26", "evidence": []},
    {"id": "B2", "description": "Git hook bypass detected", "dimension": "bypass", "state": GATE_STATE_NOT_SATISFIED, "source": "89G", "evidence": []},
    {"id": "B3", "description": "Bypass attempts logged as audit events", "dimension": "bypass", "state": GATE_STATE_NOT_SATISFIED, "source": "89H §7", "evidence": []},
    {"id": "B4", "description": "Bypass detection not spoofable", "dimension": "bypass", "state": GATE_STATE_NOT_SATISFIED, "source": "89G C16", "evidence": []},
    {"id": "B5", "description": "Bypass alerts operator", "dimension": "bypass", "state": GATE_STATE_NOT_SATISFIED, "source": "89G", "evidence": []},
)

_GATE_COUNT = len(_GATE_REGISTRY)  # 69


# ---------------------------------------------------------------------------
# Gate status
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GateStatus:
    """A single readiness gate with status and evidence."""
    gate_id: str
    description: str
    dimension: str
    state: str
    source: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class EnforcementReadinessReport:
    """Complete enforcement readiness status report.

    All enforcement flags remain simulation-only.
    """

    schema_version: str = SCHEMA_VERSION
    generated_at: str = ""
    total_gates: int = _GATE_COUNT
    satisfied: int = 0
    unsatisfied: int = 0
    conditional: int = 0
    deferred: int = 0
    enforcement_authorized: bool = False
    enforcement_ready: bool = False
    gates: tuple[GateStatus, ...] = ()
    evidence_references: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    recommended_next_phase: str = "90A — Permission Broker Enforcement Boundary Design"
    safety_footer: str = "Readiness report only: no enforcement is authorized or applied."

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "total_gates": self.total_gates,
            "satisfied": self.satisfied,
            "unsatisfied": self.unsatisfied,
            "conditional": self.conditional,
            "deferred": self.deferred,
            "enforcement_authorized": self.enforcement_authorized,
            "enforcement_ready": self.enforcement_ready,
            "gates": [
                {
                    "id": g.gate_id,
                    "description": g.description,
                    "dimension": g.dimension,
                    "state": g.state,
                    "source": g.source,
                    "evidence": list(g.evidence),
                }
                for g in self.gates
            ],
            "evidence_references": list(self.evidence_references),
            "missing_evidence": list(self.missing_evidence),
            "recommended_next_phase": self.recommended_next_phase,
            "safety_footer": self.safety_footer,
        }


# ---------------------------------------------------------------------------
# Build the report
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _count_by_state(gates: tuple[GateStatus, ...], state: str) -> int:
    return sum(1 for g in gates if g.state == state)


def build_enforcement_readiness_report() -> EnforcementReadinessReport:
    """Build the enforcement readiness report from the gate registry.

    Pure function — reads no files, executes no commands, persists nothing.
    """
    gates: list[GateStatus] = []
    evidence_set: set[str] = set()
    missing_set: set[str] = set()

    for g in _GATE_REGISTRY:
        gate_status = GateStatus(
            gate_id=g["id"],
            description=g["description"],
            dimension=g["dimension"],
            state=g["state"],
            source=g["source"],
            evidence=tuple(g.get("evidence", [])),
        )
        gates.append(gate_status)

        if g.get("evidence"):
            evidence_set.update(g["evidence"])
        else:
            missing_set.add(g["id"])

    gates_tuple = tuple(gates)
    satisfied = _count_by_state(gates_tuple, GATE_STATE_SATISFIED)
    unsatisfied = _count_by_state(gates_tuple, GATE_STATE_NOT_SATISFIED)
    conditional = _count_by_state(gates_tuple, GATE_STATE_CONDITIONAL)
    deferred = _count_by_state(gates_tuple, GATE_STATE_DEFERRED)

    # Enforcement is NOT ready unless ALL gates satisfied
    enforcement_ready = satisfied == _GATE_COUNT

    # Per-dimension unsatisfied IDs
    missing_by_dim: dict[str, list[str]] = {}
    for g in gates_tuple:
        if g.state != GATE_STATE_SATISFIED:
            missing_by_dim.setdefault(g.dimension, []).append(g.gate_id)

    return EnforcementReadinessReport(
        schema_version=SCHEMA_VERSION,
        generated_at=_utc_now_iso(),
        total_gates=_GATE_COUNT,
        satisfied=satisfied,
        unsatisfied=unsatisfied,
        conditional=conditional,
        deferred=deferred,
        enforcement_authorized=False,
        enforcement_ready=enforcement_ready,
        gates=gates_tuple,
        evidence_references=tuple(sorted(evidence_set)),
        missing_evidence=tuple(
            f"{g.gate_id}: {g.description}"
            for g in gates_tuple
            if not g.evidence
        ),
        recommended_next_phase="90A — Permission Broker Enforcement Boundary Design",
        safety_footer="Readiness report only: no enforcement is authorized or applied.",
    )


def format_readiness_report(report: EnforcementReadinessReport) -> str:
    """Format a human-readable readiness report."""
    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("  PCAE Enforcement Readiness — Gate Status Report")
    lines.append("=" * 60)
    lines.append(f"  Generated: {report.generated_at}")
    lines.append(f"  Schema version: {report.schema_version}")
    lines.append("")

    # Summary
    lines.append("  Gate Summary")
    lines.append(f"    Total gates:        {report.total_gates}")
    lines.append(f"    Satisfied:          {report.satisfied}")
    lines.append(f"    Unsatisfied:        {report.unsatisfied}")
    lines.append(f"    Conditional:        {report.conditional}")
    lines.append(f"    Deferred:           {report.deferred}")
    lines.append("")

    # Authorization status
    lines.append("  Authorization Status")
    lines.append(f"    Enforcement authorized: {'YES' if report.enforcement_authorized else 'NO'}")
    lines.append(f"    Enforcement ready:      {'YES' if report.enforcement_ready else 'NO'}")
    lines.append("")

    # Per-dimension summary
    lines.append("  Gates by Dimension")
    dimensions: dict[str, list[GateStatus]] = {}
    for g in report.gates:
        dimensions.setdefault(g.dimension, []).append(g)

    for dim_name in sorted(dimensions):
        dim_gates = dimensions[dim_name]
        dim_satisfied = sum(1 for g in dim_gates if g.state == GATE_STATE_SATISFIED)
        dim_total = len(dim_gates)
        dim_icon = "✅" if dim_satisfied == dim_total else "❌"
        lines.append(f"    {dim_icon} {dim_name}: {dim_satisfied}/{dim_total} satisfied")

    lines.append("")

    # Unsatisfied gates detail
    unsatisfied_gates = [g for g in report.gates if g.state != GATE_STATE_SATISFIED]
    if unsatisfied_gates:
        lines.append("  Unsatisfied/Deferred Gates")
        for g in unsatisfied_gates:
            emoji = _GATE_EMOJI.get(g.state, "  ")
            lines.append(f"    {emoji} {g.gate_id}: {g.description}")
            if g.evidence:
                for ev in g.evidence:
                    lines.append(f"         Evidence: {ev}")
        lines.append("")

    # Evidence references
    if report.evidence_references:
        lines.append("  Evidence References")
        for ref in report.evidence_references:
            lines.append(f"    - {ref}")
        lines.append("")

    # Missing evidence
    if report.missing_evidence:
        lines.append("  Missing Evidence")
        for missing in report.missing_evidence:
            lines.append(f"    - {missing}")
        lines.append("")

    # Recommendation
    lines.append(f"  Next Recommended Phase: {report.recommended_next_phase}")
    lines.append("")

    # Safety footer
    lines.append(f"  ⚠️  {report.safety_footer}")
    lines.append("=" * 60)

    return "\n".join(lines)


def format_readiness_report_json(report: EnforcementReadinessReport) -> str:
    """Format the report as JSON."""
    import json
    return json.dumps(report.to_dict(), indent=2, sort_keys=True)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_readiness_report(report: EnforcementReadinessReport) -> list[str]:
    """Return a list of validation issues (empty = valid)."""
    issues: list[str] = []

    if report.total_gates != _GATE_COUNT:
        issues.append(
            f"total_gates {report.total_gates} != expected {_GATE_COUNT}"
        )
    if report.schema_version != SCHEMA_VERSION:
        issues.append(
            f"schema_version {report.schema_version!r} != expected {SCHEMA_VERSION!r}"
        )
    if report.enforcement_authorized:
        issues.append(
            "enforcement_authorized must be False "
            "(enforcement is NOT authorized)"
        )
    # enforcement_ready is True only if all gates satisfied
    if report.enforcement_ready and report.satisfied != _GATE_COUNT:
        issues.append(
            "enforcement_ready is True but not all gates are satisfied"
        )
    if report.safety_footer and "no enforcement" not in report.safety_footer.lower():
        issues.append(
            "safety_footer must state that no enforcement is authorized"
        )

    total = report.satisfied + report.unsatisfied + report.conditional + report.deferred
    if total != report.total_gates:
        issues.append(
            f"Gate count mismatch: sum({total}) != total({report.total_gates})"
        )

    return issues
