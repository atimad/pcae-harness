"""Phase 134E.1: Canonical Engineering Evidence Executable Model.

Implements the first executable code model for Canonical Engineering
Evidence, per the frozen Track 133 contract (``docs/PHASE_133_CANONICAL_
ENGINEERING_EVIDENCE_ARCHITECTURE.md``, ``..._CONTRACT.md``, independently
verified by ``..._CONTRACT_VERIFICATION.md``) and Track 134's finalization
contract (``docs/PHASE_134_CANONICAL_PHASE_FINALIZATION_AND_REPORTING_
LIFECYCLE_CONTRACT.md``).

**This module is not yet active lifecycle authority.** It is an isolated,
disconnected executable model, exactly as 133G's own implementation
roadmap requires of its first executable-code phase ("133H" in that
roadmap's numbering; "134E.1" in this repository's Track 134 numbering):
"the smallest safe next step because derived views cannot be correctly
implemented before their sole authority exists and is independently
testable... explicitly disconnected from active report rendering and
notification delivery." Nothing in ``pcae.core.phase_reports``,
``pcae.core.notifications``, ``pcae.core.notification_certification``,
``pcae.core.repository_transition_validator``, or any CLI command imports
this module, and this module imports none of them. The current governed
reporting and finalization path remains the sole active authority until a
later migration/integration phase explicitly wires this model in.

Disconnected by design, mirroring ``core/evidence.py`` (Phase 115C)'s own
isolation discipline: stdlib imports only, zero internal PCAE imports,
zero side effects, zero I/O, zero network, zero execution capability.

Eleven conceptual evidence categories (133D Section 7 / 133E Section 7,
unchanged, frozen as a category list with "no schema, no implementation"):
phase identity, engineering actions, architectural impact, implementation
impact, verification evidence, governance evidence, test evidence,
technical debt observations, engineering knowledge, runtime state,
repository state. This module is the first schema for those categories,
refined into the fields below per the smallest coherent grouping that
satisfies PFR-001's thirteen report sections (133B Section 3) as future
consumers, without flattening evidence into an unstructured dictionary.

The 133F "uncertainty/limitations are material evidence under Non-
Omission" clarification (recorded as a NON-BLOCKING clarification pending
future contract amendment, but treated as binding implementation guidance
by 133G Sections 6/8/11) is implemented here as first-class, non-droppable
structure: ``uncertainty`` and ``limitations`` are dedicated tuple fields,
never free-text footnotes, and validation rejects a finalized record that
discards them silently.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any


SCHEMA_VERSION = "1.0"

#: Versions this module can read/validate. 134E.1 introduces the smallest
#: executable version contract: a single supported version today, with
#: unsupported versions rejected fail-closed (never silently coerced) and
#: future additive versions expected to extend, not replace, this set.
SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({SCHEMA_VERSION})


# ═══════════════════════════════════════════════════════════════════════
# Frozen enumerations
# ═══════════════════════════════════════════════════════════════════════


class PhaseClass(str, Enum):
    """The six phase classes PFR-001 defines applicability rules for
    (133B Section 6), named here per this repository's own Track 134
    planning-phase terminology (134D). These correspond to 133B's own
    six canonical columns as follows: ARCHITECTURE -> Architecture;
    CONTRACT -> Contract Freeze and Contract Verification (both are
    contract-class phases distinguished by the ``contract_stage`` a
    caller may record in ``objective``/provenance, not by a second enum
    value here); PLANNING -> Prototype Plan; IMPLEMENTATION -> Prototype
    Implementation; VERIFICATION -> Independent Verification;
    REVIEW_HARDENING -> a repository-specific phase type (e.g. 134B.1-
    134B.3's own hardening phases) that 133C Section 6 confirms "maps
    onto the existing six columns without requiring new rows" -- carried
    here as a distinct tag for phase-type bookkeeping, not as a seventh
    PFR-001 content-requirement column.
    """

    ARCHITECTURE = "architecture"
    CONTRACT = "contract"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"
    REVIEW_HARDENING = "review_hardening"


class Applicability(str, Enum):
    """Explicit disposition of one evidence category for one record.

    Never silently omit a required category (133E Section 15
    Completeness). Every category-level field on ``CanonicalEngineering
    Evidence`` is paired with an ``Applicability`` value in
    ``applicability`` distinguishing genuinely-empty-because-inapplicable
    from missing-because-broken.
    """

    PRESENT = "present"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    OMITTED_INVALID_INPUT = "omitted_invalid_input"


class FindingClassification(str, Enum):
    """The uniform finding classification scheme (133B Section 9),
    applied identically across every governed phase from that point
    forward."""

    CONFIRMED = "confirmed"
    NON_BLOCKING = "non_blocking"
    BLOCKING = "blocking"


class EvidenceRecordState(str, Enum):
    """The mutable-construction -> validated -> finalized boundary
    (Evidence Integrity Contract, 133E Section 5): evidence is mutable
    during capture/normalization/validation and becomes immutable the
    moment it becomes the canonical record for its phase.

    ``SUPERSEDED`` marks a finalized record a later, explicitly governed
    correction has replaced -- 134E.1 prepares this field only; it does
    not implement the correction workflow itself (133E Section 5 leaves
    the correction mechanism to a future phase; 134E.1's own scope
    excludes it as a Strict Non-Goal).
    """

    DRAFT = "draft"
    FINALIZED = "finalized"
    SUPERSEDED = "superseded"


# ═══════════════════════════════════════════════════════════════════════
# Freeze / unfreeze helpers (mirrors core/evidence.py's own convention)
# ═══════════════════════════════════════════════════════════════════════


def _freeze_json_value(value: Any) -> Any:
    """Deep-freeze a JSON-compatible value: dict -> MappingProxyType,
    list/tuple -> tuple, scalars pass through. Prevents a caller-held
    mutable reference from altering a "frozen" dataclass field in place
    after construction (``@dataclass(frozen=True)`` alone only prevents
    reassignment, not in-place mutation of a mutable field's contents).
    """

    if isinstance(value, dict):
        return MappingProxyType({k: _freeze_json_value(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json_value(v) for v in value)
    return value


def _unfreeze_json_value(value: Any) -> Any:
    """Inverse of ``_freeze_json_value`` for JSON serialization."""

    if isinstance(value, MappingProxyType):
        return {k: _unfreeze_json_value(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_unfreeze_json_value(v) for v in value]
    return value


# ═══════════════════════════════════════════════════════════════════════
# Secret-shape detection — no secrets, credentials, or delivery
# destinations belong in engineering evidence (this model has no such
# field by design; this is a defense-in-depth check on free-text fields).
# ═══════════════════════════════════════════════════════════════════════

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"PCAE_[A-Z_]*(TOKEN|SECRET|KEY|PASSWORD|CHAT_ID)\s*[:=]\s*\S+"),
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{25,}\b"),  # Telegram bot-token shape
)


def _contains_likely_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SECRET_PATTERNS)


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════
# Validation result — deterministic, inspectable (never a bare bool)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    field: str
    blocking: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "field": self.field,
            "blocking": self.blocking,
        }


# ═══════════════════════════════════════════════════════════════════════
# Identity — mirrors phase_reports.CanonicalPhaseIdentity's shape by
# convention (phase_id / phase_name / source), not by import, so this
# module stays isolated from the report-generation subsystem it must not
# depend on. Callers construct this from an already-resolved
# CanonicalPhaseIdentity; this module never re-resolves phase identity
# itself -- it is not a new identity authority (Cardinality: exactly one
# canonical evidence object per governed phase, 133D Section 3/5/13).
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class EvidencePhaseIdentity:
    """The governed phase identity this evidence record is bound to.

    ``phase_id``/``phase_name`` always originate from the same
    already-resolved source (mirrors ``CanonicalPhaseIdentity``'s own
    "never mixed across sources" rule) -- this type does not resolve
    identity, it only carries an already-resolved one.
    """

    phase_id: str
    phase_name: str
    source: str

    def __post_init__(self) -> None:
        if not self.phase_id:
            raise ValueError("EvidencePhaseIdentity.phase_id must be non-empty")
        if not self.phase_name:
            raise ValueError("EvidencePhaseIdentity.phase_name must be non-empty")
        if not self.source:
            raise ValueError("EvidencePhaseIdentity.source must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidencePhaseIdentity":
        return cls(
            phase_id=data["phase_id"],
            phase_name=data["phase_name"],
            source=data["source"],
        )


@dataclass(frozen=True)
class EvidenceIdentity:
    """Stable, deterministic identity for one canonical evidence record.

    Deliberately not a random UUID: identity is the governed phase
    identity plus a monotonic record version, exactly per 133G Section
    5.2's own guidance ("Identity is the governed phase identity, not
    free text") and the frozen one-record-per-phase cardinality. Two
    identical constructions for the same phase/version always produce
    the same ``evidence_id`` -- no entropy, no process-specific state, no
    model/agent identity, no delivery-channel state.
    """

    phase: EvidencePhaseIdentity
    record_version: int = 1
    correction_of: str | None = None

    def __post_init__(self) -> None:
        if self.record_version < 1:
            raise ValueError("EvidenceIdentity.record_version must be >= 1")
        if self.record_version == 1 and self.correction_of is not None:
            raise ValueError(
                "EvidenceIdentity.record_version == 1 cannot declare correction_of"
            )
        if self.record_version > 1 and self.correction_of is None:
            raise ValueError(
                "EvidenceIdentity.record_version > 1 must declare correction_of"
            )

    @property
    def evidence_id(self) -> str:
        return f"{self.phase.phase_id}#{self.record_version}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "phase": self.phase.to_dict(),
            "record_version": self.record_version,
            "correction_of": self.correction_of,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceIdentity":
        return cls(
            phase=EvidencePhaseIdentity.from_dict(data["phase"]),
            record_version=data["record_version"],
            correction_of=data.get("correction_of"),
        )


# ═══════════════════════════════════════════════════════════════════════
# Provenance — every material element must be traceable
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class EvidenceProvenanceRecord:
    """Traces one material evidence element back to its source.

    ``covers`` names the evidence category/field this provenance record
    supports (e.g. ``"test_results"``); derived report text is never the
    sole source -- ``source_artifact``/``source_command`` must reference
    something outside this record itself (a file, a governed command, a
    repository/runtime observation).
    """

    covers: str
    source_artifact: str
    source_command: str | None
    source_phase_id: str | None
    derivation_path: str
    verification_state: str
    observed_at: str | None = None

    def __post_init__(self) -> None:
        if not self.covers:
            raise ValueError("EvidenceProvenanceRecord.covers must be non-empty")
        if not self.source_artifact:
            raise ValueError(
                "EvidenceProvenanceRecord.source_artifact must be non-empty"
            )
        if not self.derivation_path:
            raise ValueError(
                "EvidenceProvenanceRecord.derivation_path must be non-empty"
            )
        if not self.verification_state:
            raise ValueError(
                "EvidenceProvenanceRecord.verification_state must be non-empty"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "covers": self.covers,
            "source_artifact": self.source_artifact,
            "source_command": self.source_command,
            "source_phase_id": self.source_phase_id,
            "derivation_path": self.derivation_path,
            "verification_state": self.verification_state,
            "observed_at": self.observed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceProvenanceRecord":
        return cls(
            covers=data["covers"],
            source_artifact=data["source_artifact"],
            source_command=data.get("source_command"),
            source_phase_id=data.get("source_phase_id"),
            derivation_path=data["derivation_path"],
            verification_state=data["verification_state"],
            observed_at=data.get("observed_at"),
        )


# ═══════════════════════════════════════════════════════════════════════
# Uncertainty and limitations — material evidence, never free-text
# footnotes (133F's uncertainty/limitations-under-Non-Omission
# clarification, treated as binding implementation guidance here).
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class UncertaintyItem:
    category: str
    description: str
    affected_evidence: tuple[str, ...]
    source: str
    verification_state: str
    resolution_status: str = "unresolved"

    def __post_init__(self) -> None:
        if not self.category:
            raise ValueError("UncertaintyItem.category must be non-empty")
        if not self.description:
            raise ValueError("UncertaintyItem.description must be non-empty")
        if not self.affected_evidence:
            raise ValueError(
                "UncertaintyItem.affected_evidence must name at least one "
                "affected evidence category"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "description": self.description,
            "affected_evidence": list(self.affected_evidence),
            "source": self.source,
            "verification_state": self.verification_state,
            "resolution_status": self.resolution_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UncertaintyItem":
        return cls(
            category=data["category"],
            description=data["description"],
            affected_evidence=tuple(data["affected_evidence"]),
            source=data["source"],
            verification_state=data["verification_state"],
            resolution_status=data.get("resolution_status", "unresolved"),
        )


@dataclass(frozen=True)
class LimitationItem:
    category: str
    description: str
    affected_evidence: tuple[str, ...]
    resolution_status: str = "unresolved"

    def __post_init__(self) -> None:
        if not self.category:
            raise ValueError("LimitationItem.category must be non-empty")
        if not self.description:
            raise ValueError("LimitationItem.description must be non-empty")
        if not self.affected_evidence:
            raise ValueError(
                "LimitationItem.affected_evidence must name at least one "
                "affected evidence category"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "description": self.description,
            "affected_evidence": list(self.affected_evidence),
            "resolution_status": self.resolution_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LimitationItem":
        return cls(
            category=data["category"],
            description=data["description"],
            affected_evidence=tuple(data["affected_evidence"]),
            resolution_status=data.get("resolution_status", "unresolved"),
        )


# ═══════════════════════════════════════════════════════════════════════
# Findings and repairs — CONFIRMED / NON_BLOCKING / BLOCKING, never
# overwritten by their own repair
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class FindingRecord:
    finding_id: str
    classification: FindingClassification
    description: str
    affected_component: str

    def __post_init__(self) -> None:
        if not self.finding_id:
            raise ValueError("FindingRecord.finding_id must be non-empty")
        if not self.description:
            raise ValueError("FindingRecord.description must be non-empty")
        if not self.affected_component:
            raise ValueError("FindingRecord.affected_component must be non-empty")
        if not isinstance(self.classification, FindingClassification):
            raise ValueError(
                f"FindingRecord.classification must be a FindingClassification, "
                f"got {self.classification!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "classification": self.classification.value,
            "description": self.description,
            "affected_component": self.affected_component,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FindingRecord":
        return cls(
            finding_id=data["finding_id"],
            classification=FindingClassification(data["classification"]),
            description=data["description"],
            affected_component=data["affected_component"],
        )


@dataclass(frozen=True)
class RepairRecord:
    """A repair preserves its original finding -- it never replaces it.

    ``original_finding`` is retained in full; ``resulting_status`` is the
    new classification after repair (typically CONFIRMED), distinct from
    ``original_finding.classification`` (typically BLOCKING or
    NON_BLOCKING) which is never altered in place.
    """

    original_finding: FindingRecord
    repair_action: str
    affected_artifact: str
    verification_evidence: str
    resulting_status: FindingClassification

    def __post_init__(self) -> None:
        if not self.repair_action:
            raise ValueError("RepairRecord.repair_action must be non-empty")
        if not self.affected_artifact:
            raise ValueError("RepairRecord.affected_artifact must be non-empty")
        if not self.verification_evidence:
            raise ValueError("RepairRecord.verification_evidence must be non-empty")
        if self.original_finding.classification == FindingClassification.CONFIRMED:
            raise ValueError(
                "RepairRecord.original_finding must not already be CONFIRMED "
                "(nothing to repair)"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_finding": self.original_finding.to_dict(),
            "repair_action": self.repair_action,
            "affected_artifact": self.affected_artifact,
            "verification_evidence": self.verification_evidence,
            "resulting_status": self.resulting_status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepairRecord":
        return cls(
            original_finding=FindingRecord.from_dict(data["original_finding"]),
            repair_action=data["repair_action"],
            affected_artifact=data["affected_artifact"],
            verification_evidence=data["verification_evidence"],
            resulting_status=FindingClassification(data["resulting_status"]),
        )


# ═══════════════════════════════════════════════════════════════════════
# Governance / test / repository / runtime snapshots
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class GovernanceResultItem:
    name: str
    status: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("GovernanceResultItem.name must be non-empty")
        if not self.status:
            raise ValueError("GovernanceResultItem.status must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GovernanceResultItem":
        return cls(name=data["name"], status=data["status"])


@dataclass(frozen=True)
class TestResultItem:
    name: str
    result: str
    status: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("TestResultItem.name must be non-empty")
        if not self.status:
            raise ValueError("TestResultItem.status must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "result": self.result, "status": self.status}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestResultItem":
        return cls(name=data["name"], result=data.get("result", ""), status=data["status"])


_VALID_PUSHED_STATUSES: frozenset[str] = frozenset({
    "pushed", "not_pushed", "nothing_to_push", "clean", "unknown",
})


@dataclass(frozen=True)
class RepositoryStateSnapshot:
    commit: str | None
    branch: str | None
    pushed_status: str
    origin_main_head_count: int
    clean: bool

    def __post_init__(self) -> None:
        if self.pushed_status not in _VALID_PUSHED_STATUSES:
            raise ValueError(
                f"RepositoryStateSnapshot.pushed_status {self.pushed_status!r} "
                f"is not one of {sorted(_VALID_PUSHED_STATUSES)}"
            )
        if self.origin_main_head_count < 0:
            raise ValueError(
                "RepositoryStateSnapshot.origin_main_head_count must be >= 0"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit": self.commit,
            "branch": self.branch,
            "pushed_status": self.pushed_status,
            "origin_main_head_count": self.origin_main_head_count,
            "clean": self.clean,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepositoryStateSnapshot":
        return cls(
            commit=data.get("commit"),
            branch=data.get("branch"),
            pushed_status=data["pushed_status"],
            origin_main_head_count=data["origin_main_head_count"],
            clean=data["clean"],
        )


_VALID_RUNTIME_STATES: frozenset[str] = frozenset({"Observed", "Unknown"})
_VALID_EXECUTION_AVAILABILITY: frozenset[str] = frozenset({
    "unavailable", "available", "unknown",
})


@dataclass(frozen=True)
class RuntimeStateSnapshot:
    runtime_state: str
    maximum_capability: str
    execution_availability: str

    def __post_init__(self) -> None:
        if self.runtime_state not in _VALID_RUNTIME_STATES:
            raise ValueError(
                f"RuntimeStateSnapshot.runtime_state {self.runtime_state!r} "
                f"is not one of {sorted(_VALID_RUNTIME_STATES)}"
            )
        if self.execution_availability not in _VALID_EXECUTION_AVAILABILITY:
            raise ValueError(
                f"RuntimeStateSnapshot.execution_availability "
                f"{self.execution_availability!r} is not one of "
                f"{sorted(_VALID_EXECUTION_AVAILABILITY)}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_state": self.runtime_state,
            "maximum_capability": self.maximum_capability,
            "execution_availability": self.execution_availability,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuntimeStateSnapshot":
        return cls(
            runtime_state=data["runtime_state"],
            maximum_capability=data["maximum_capability"],
            execution_availability=data["execution_availability"],
        )


@dataclass(frozen=True)
class CommitPushInfo:
    commits: tuple[str, ...]
    pushed_status: str
    origin_main_head_count: int

    def __post_init__(self) -> None:
        if self.pushed_status not in _VALID_PUSHED_STATUSES:
            raise ValueError(
                f"CommitPushInfo.pushed_status {self.pushed_status!r} is not "
                f"one of {sorted(_VALID_PUSHED_STATUSES)}"
            )
        if self.origin_main_head_count < 0:
            raise ValueError("CommitPushInfo.origin_main_head_count must be >= 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "commits": list(self.commits),
            "pushed_status": self.pushed_status,
            "origin_main_head_count": self.origin_main_head_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommitPushInfo":
        return cls(
            commits=tuple(data["commits"]),
            pushed_status=data["pushed_status"],
            origin_main_head_count=data["origin_main_head_count"],
        )


@dataclass(frozen=True)
class CorrectionMetadata:
    """Prepared fields only -- 134E.1 does not implement the governed
    correction workflow itself (Strict Non-Goal); this shape exists so a
    future phase can wire in correction without a schema-breaking change.
    """

    is_correction: bool = False
    supersedes_evidence_id: str | None = None
    reason: str | None = None
    authority: str | None = None

    def __post_init__(self) -> None:
        if self.is_correction and not self.supersedes_evidence_id:
            raise ValueError(
                "CorrectionMetadata.is_correction requires supersedes_evidence_id"
            )
        if self.is_correction and not self.reason:
            raise ValueError("CorrectionMetadata.is_correction requires reason")
        if not self.is_correction and self.supersedes_evidence_id is not None:
            raise ValueError(
                "CorrectionMetadata.supersedes_evidence_id set without "
                "is_correction=True"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_correction": self.is_correction,
            "supersedes_evidence_id": self.supersedes_evidence_id,
            "reason": self.reason,
            "authority": self.authority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CorrectionMetadata":
        return cls(
            is_correction=data.get("is_correction", False),
            supersedes_evidence_id=data.get("supersedes_evidence_id"),
            reason=data.get("reason"),
            authority=data.get("authority"),
        )


# ═══════════════════════════════════════════════════════════════════════
# The canonical evidence record itself
# ═══════════════════════════════════════════════════════════════════════

#: Categories that require an explicit Applicability entry. Every one of
#: these must appear as a key in ``applicability`` -- silent absence is
#: itself a validation failure (133E Section 15 Completeness).
REQUIRED_APPLICABILITY_CATEGORIES: frozenset[str] = frozenset({
    "engineering_actions",
    "architectural_findings",
    "implementation_findings",
    "verification_findings",
    "defects_discovered",
    "defects_repaired",
    "incorrect_assumptions_corrected",
    "technical_debt_reviewed",
    "technical_debt_introduced",
    "notable_engineering_knowledge",
    "no_go_confirmations",
    "architectural_boundary_confirmations",
})

#: Per 133B Section 6: implementation/verification findings are the only
#: two categories whose *mandatory presence* varies by phase class in a
#: named, frozen way. All others are mandatory-applicable-or-explicitly-
#: not-applicable across every class (informational completeness is a
#: 134E.3 concern; here we only enforce that the *disposition* is never
#: silently missing).
_PHASE_CLASS_MANDATORY_PRESENT: dict[PhaseClass, frozenset[str]] = {
    PhaseClass.IMPLEMENTATION: frozenset({"implementation_findings"}),
    PhaseClass.VERIFICATION: frozenset({"verification_findings"}),
}


@dataclass(frozen=True)
class CanonicalEngineeringEvidence:
    """One immutable, versioned Canonical Engineering Evidence record.

    Not yet active lifecycle authority (see module docstring). Construct
    via keyword arguments; call :meth:`validate` to obtain a deterministic,
    inspectable list of :class:`ValidationIssue`; call :meth:`finalize` to
    obtain a ``state=FINALIZED`` record once no blocking issue remains.
    Finalized records are never mutated in place -- a correction produces
    a new record with ``record_version`` incremented and ``correction_of``
    set, referencing the prior record's ``evidence_id``; the prior record
    itself is untouched.
    """

    identity: EvidenceIdentity
    phase_class: PhaseClass
    task_id: str | None
    objective: str
    engineering_actions: tuple[str, ...]
    architectural_findings: tuple[FindingRecord, ...]
    implementation_findings: tuple[FindingRecord, ...]
    verification_findings: tuple[FindingRecord, ...]
    defects_discovered: tuple[FindingRecord, ...]
    defects_repaired: tuple[RepairRecord, ...]
    incorrect_assumptions_corrected: tuple[RepairRecord, ...]
    technical_debt_reviewed: tuple[FindingRecord, ...]
    technical_debt_introduced: tuple[FindingRecord, ...]
    notable_engineering_knowledge: tuple[str, ...]
    governance_results: tuple[GovernanceResultItem, ...]
    test_results: tuple[TestResultItem, ...]
    repository_state: RepositoryStateSnapshot
    runtime_state: RuntimeStateSnapshot
    no_go_confirmations: tuple[str, ...]
    architectural_boundary_confirmations: tuple[str, ...]
    track_progress: str
    recommended_next_phase: str
    commit_and_push: CommitPushInfo
    provenance: tuple[EvidenceProvenanceRecord, ...]
    uncertainty: tuple[UncertaintyItem, ...]
    limitations: tuple[LimitationItem, ...]
    correction: CorrectionMetadata
    applicability: MappingProxyType
    created_at: str
    schema_version: str = SCHEMA_VERSION
    state: EvidenceRecordState = EvidenceRecordState.DRAFT
    finalized_at: str | None = None

    # ── Construction-time structural invariants ─────────────────────

    def __post_init__(self) -> None:
        if self.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(
                f"Unsupported schema_version {self.schema_version!r}; "
                f"supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
            )
        if not isinstance(self.phase_class, PhaseClass):
            raise ValueError(
                f"phase_class must be a PhaseClass, got {self.phase_class!r}"
            )
        if not self.objective:
            raise ValueError("objective must be non-empty")
        if not self.track_progress:
            raise ValueError("track_progress must be non-empty")
        if not self.created_at:
            raise ValueError("created_at must be non-empty")
        missing_applicability = REQUIRED_APPLICABILITY_CATEGORIES - set(
            self.applicability.keys()
        )
        if missing_applicability:
            raise ValueError(
                "applicability is missing required categories: "
                f"{sorted(missing_applicability)}"
            )
        if self.state == EvidenceRecordState.FINALIZED and not self.finalized_at:
            raise ValueError("FINALIZED state requires finalized_at")
        if self.state != EvidenceRecordState.FINALIZED and self.finalized_at:
            raise ValueError("finalized_at set without state == FINALIZED")

    # ── Validation ────────────────────────────────────────────────────

    def validate(self) -> tuple[ValidationIssue, ...]:
        """Deterministic, inspectable validation. Never coerces invalid
        evidence into valid evidence -- callers must repair and
        reconstruct. Returns an empty tuple iff the record may be
        finalized.
        """

        issues: list[ValidationIssue] = []

        # Required identity fields.
        if not self.identity.phase.phase_id:
            issues.append(ValidationIssue(
                "missing_phase_identity", "phase identity is required",
                "identity.phase",
            ))

        # Phase/task consistency: task_id, if present, must not be blank.
        if self.task_id is not None and not self.task_id.strip():
            issues.append(ValidationIssue(
                "invalid_task_identity", "task_id must be non-empty if present",
                "task_id",
            ))

        # Allowed phase classes already enforced by the enum type itself
        # at construction; nothing further to check here.

        # Required category applicability per phase class.
        for category, required in _PHASE_CLASS_MANDATORY_PRESENT.items():
            if self.phase_class != category:
                continue
            for field_name in required:
                disposition = self.applicability.get(field_name)
                if disposition == Applicability.NOT_APPLICABLE:
                    issues.append(ValidationIssue(
                        "contradictory_applicability",
                        f"{field_name} cannot be NOT_APPLICABLE for phase "
                        f"class {self.phase_class.value!r}",
                        field_name,
                    ))

        # Contradictory statuses: applicability says PRESENT but tuple is
        # empty, or applicability says NOT_APPLICABLE/UNAVAILABLE/UNKNOWN
        # but tuple is non-empty.
        tuple_categories: dict[str, tuple] = {
            "engineering_actions": self.engineering_actions,
            "architectural_findings": self.architectural_findings,
            "implementation_findings": self.implementation_findings,
            "verification_findings": self.verification_findings,
            "defects_discovered": self.defects_discovered,
            "defects_repaired": self.defects_repaired,
            "incorrect_assumptions_corrected": self.incorrect_assumptions_corrected,
            "technical_debt_reviewed": self.technical_debt_reviewed,
            "technical_debt_introduced": self.technical_debt_introduced,
            "notable_engineering_knowledge": self.notable_engineering_knowledge,
            "no_go_confirmations": self.no_go_confirmations,
            "architectural_boundary_confirmations": self.architectural_boundary_confirmations,
        }
        for field_name, values in tuple_categories.items():
            disposition = self.applicability.get(field_name)
            if disposition == Applicability.PRESENT and not values:
                issues.append(ValidationIssue(
                    "contradictory_status",
                    f"{field_name} marked PRESENT but contains no entries",
                    field_name,
                ))
            if disposition in (
                Applicability.NOT_APPLICABLE,
                Applicability.UNAVAILABLE,
                Applicability.UNKNOWN,
                Applicability.OMITTED_INVALID_INPUT,
            ) and values:
                issues.append(ValidationIssue(
                    "contradictory_status",
                    f"{field_name} marked {disposition.value} but contains "
                    f"{len(values)} entries",
                    field_name,
                ))
            # Missing uncertainty/limitations where certainty is
            # unsupported: an UNKNOWN/UNAVAILABLE disposition must be
            # explained by at least one uncertainty or limitation entry
            # naming this category.
            if disposition in (Applicability.UNKNOWN, Applicability.UNAVAILABLE):
                named = {u.category for u in self.uncertainty} | {
                    u for item in self.uncertainty for u in item.affected_evidence
                } | {
                    field_name_ for item in self.limitations
                    for field_name_ in item.affected_evidence
                }
                if field_name not in named:
                    issues.append(ValidationIssue(
                        "missing_uncertainty_disclosure",
                        f"{field_name} is {disposition.value} but no "
                        "uncertainty/limitation entry names it",
                        field_name,
                    ))

        # Invalid finding classifications already enforced by
        # FindingRecord's own __post_init__ at construction time.

        # Invalid repair relationships already enforced by RepairRecord's
        # own __post_init__ (original_finding must not already be
        # CONFIRMED).

        # Invalid commit information.
        for commit in self.commit_and_push.commits:
            if not commit or not re.match(r"^[0-9a-f]{7,40}$", commit):
                issues.append(ValidationIssue(
                    "invalid_commit", f"commit {commit!r} is not a valid hash",
                    "commit_and_push.commits",
                ))

        # Correction/supersession consistency already enforced by
        # CorrectionMetadata's own __post_init__.
        if self.correction.is_correction and self.identity.correction_of is None:
            issues.append(ValidationIssue(
                "correction_identity_mismatch",
                "correction.is_correction is True but identity.correction_of "
                "is not set",
                "identity.correction_of",
            ))
        if (
            self.correction.is_correction
            and self.identity.correction_of != self.correction.supersedes_evidence_id
        ):
            issues.append(ValidationIssue(
                "correction_identity_mismatch",
                "identity.correction_of does not match "
                "correction.supersedes_evidence_id",
                "identity.correction_of",
            ))

        # Duplicate finding identifiers within one record.
        seen_ids: set[str] = set()
        for findings in (
            self.architectural_findings, self.implementation_findings,
            self.verification_findings, self.defects_discovered,
            self.technical_debt_reviewed, self.technical_debt_introduced,
        ):
            for finding in findings:
                if finding.finding_id in seen_ids:
                    issues.append(ValidationIssue(
                        "duplicate_finding_identifier",
                        f"finding_id {finding.finding_id!r} appears more than once",
                        "finding_id",
                    ))
                seen_ids.add(finding.finding_id)

        # Secret-shape rejection across free-text fields.
        free_text_fields: dict[str, str] = {"objective": self.objective}
        for i, action in enumerate(self.engineering_actions):
            free_text_fields[f"engineering_actions[{i}]"] = action
        for i, note in enumerate(self.notable_engineering_knowledge):
            free_text_fields[f"notable_engineering_knowledge[{i}]"] = note
        for text_field, text_value in free_text_fields.items():
            if _contains_likely_secret(text_value):
                issues.append(ValidationIssue(
                    "likely_secret_material",
                    f"{text_field} appears to contain secret/credential material",
                    text_field,
                ))

        return tuple(issues)

    # ── Finalization / immutability ──────────────────────────────────

    def finalize(self) -> "CanonicalEngineeringEvidence":
        """Return a new, FINALIZED record if no BLOCKING validation issue
        remains. Never mutates ``self`` -- the frozen dataclass makes
        that impossible at the language level; this method also never
        returns ``self`` with fields patched, always a fresh object, so a
        caller's reference to the draft remains a draft.
        """

        if self.state == EvidenceRecordState.FINALIZED:
            raise ValueError("record is already FINALIZED")
        issues = self.validate()
        blocking = [i for i in issues if i.blocking]
        if blocking:
            raise ValueError(
                "cannot finalize: "
                + "; ".join(f"{i.code}: {i.message}" for i in blocking)
            )
        import dataclasses

        return dataclasses.replace(
            self,
            state=EvidenceRecordState.FINALIZED,
            finalized_at=_utc_now_iso(),
        )

    def superseded(self) -> "CanonicalEngineeringEvidence":
        """Mark a finalized record SUPERSEDED (a later correction record
        exists). Prepared for future correction workflow use only.
        """

        if self.state != EvidenceRecordState.FINALIZED:
            raise ValueError("only a FINALIZED record may become SUPERSEDED")
        import dataclasses

        return dataclasses.replace(self, state=EvidenceRecordState.SUPERSEDED)

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d: dict[str, Any] = {
            "schema_version": self.schema_version,
            "identity": self.identity.to_dict(),
            "phase_class": self.phase_class.value,
            "task_id": self.task_id,
            "objective": self.objective,
            "engineering_actions": list(self.engineering_actions),
            "architectural_findings": [f.to_dict() for f in self.architectural_findings],
            "implementation_findings": [f.to_dict() for f in self.implementation_findings],
            "verification_findings": [f.to_dict() for f in self.verification_findings],
            "defects_discovered": [f.to_dict() for f in self.defects_discovered],
            "defects_repaired": [r.to_dict() for r in self.defects_repaired],
            "incorrect_assumptions_corrected": [
                r.to_dict() for r in self.incorrect_assumptions_corrected
            ],
            "technical_debt_reviewed": [f.to_dict() for f in self.technical_debt_reviewed],
            "technical_debt_introduced": [f.to_dict() for f in self.technical_debt_introduced],
            "notable_engineering_knowledge": list(self.notable_engineering_knowledge),
            "governance_results": [g.to_dict() for g in self.governance_results],
            "test_results": [t.to_dict() for t in self.test_results],
            "repository_state": self.repository_state.to_dict(),
            "runtime_state": self.runtime_state.to_dict(),
            "no_go_confirmations": list(self.no_go_confirmations),
            "architectural_boundary_confirmations": list(
                self.architectural_boundary_confirmations
            ),
            "track_progress": self.track_progress,
            "recommended_next_phase": self.recommended_next_phase,
            "commit_and_push": self.commit_and_push.to_dict(),
            "provenance": [p.to_dict() for p in self.provenance],
            "uncertainty": [u.to_dict() for u in self.uncertainty],
            "limitations": [l.to_dict() for l in self.limitations],
            "correction": self.correction.to_dict(),
            "applicability": {k: v.value for k, v in sorted(self.applicability.items())},
            "created_at": self.created_at,
            "state": self.state.value,
            "finalized_at": self.finalized_at,
        }
        if include_digest:
            d["record_digest"] = self.compute_digest()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CanonicalEngineeringEvidence":
        return cls(
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            identity=EvidenceIdentity.from_dict(data["identity"]),
            phase_class=PhaseClass(data["phase_class"]),
            task_id=data.get("task_id"),
            objective=data["objective"],
            engineering_actions=tuple(data.get("engineering_actions", [])),
            architectural_findings=tuple(
                FindingRecord.from_dict(x) for x in data.get("architectural_findings", [])
            ),
            implementation_findings=tuple(
                FindingRecord.from_dict(x) for x in data.get("implementation_findings", [])
            ),
            verification_findings=tuple(
                FindingRecord.from_dict(x) for x in data.get("verification_findings", [])
            ),
            defects_discovered=tuple(
                FindingRecord.from_dict(x) for x in data.get("defects_discovered", [])
            ),
            defects_repaired=tuple(
                RepairRecord.from_dict(x) for x in data.get("defects_repaired", [])
            ),
            incorrect_assumptions_corrected=tuple(
                RepairRecord.from_dict(x)
                for x in data.get("incorrect_assumptions_corrected", [])
            ),
            technical_debt_reviewed=tuple(
                FindingRecord.from_dict(x) for x in data.get("technical_debt_reviewed", [])
            ),
            technical_debt_introduced=tuple(
                FindingRecord.from_dict(x) for x in data.get("technical_debt_introduced", [])
            ),
            notable_engineering_knowledge=tuple(
                data.get("notable_engineering_knowledge", [])
            ),
            governance_results=tuple(
                GovernanceResultItem.from_dict(x) for x in data.get("governance_results", [])
            ),
            test_results=tuple(
                TestResultItem.from_dict(x) for x in data.get("test_results", [])
            ),
            repository_state=RepositoryStateSnapshot.from_dict(data["repository_state"]),
            runtime_state=RuntimeStateSnapshot.from_dict(data["runtime_state"]),
            no_go_confirmations=tuple(data.get("no_go_confirmations", [])),
            architectural_boundary_confirmations=tuple(
                data.get("architectural_boundary_confirmations", [])
            ),
            track_progress=data["track_progress"],
            recommended_next_phase=data.get("recommended_next_phase", ""),
            commit_and_push=CommitPushInfo.from_dict(data["commit_and_push"]),
            provenance=tuple(
                EvidenceProvenanceRecord.from_dict(x) for x in data.get("provenance", [])
            ),
            uncertainty=tuple(
                UncertaintyItem.from_dict(x) for x in data.get("uncertainty", [])
            ),
            limitations=tuple(
                LimitationItem.from_dict(x) for x in data.get("limitations", [])
            ),
            correction=CorrectionMetadata.from_dict(data.get("correction", {})),
            applicability=MappingProxyType({
                k: Applicability(v) for k, v in data.get("applicability", {}).items()
            }),
            created_at=data["created_at"],
            state=EvidenceRecordState(data.get("state", EvidenceRecordState.DRAFT.value)),
            finalized_at=data.get("finalized_at"),
        )

    # ── Digest ────────────────────────────────────────────────────────

    def compute_digest(self) -> str:
        """Deterministic SHA-256 digest over the canonical serialized
        representation, excluding the digest field itself and excluding
        approved timestamps (``created_at``, ``finalized_at``) so that
        equivalent evidence content produces an equivalent digest
        regardless of when it was constructed or finalized -- matching
        the frozen determinism rule ("equivalent engineering activity
        shall produce equivalent canonical evidence, except approved
        timestamps," 133D Section 11 / 133E Section 8). Rendering and
        delivery state are never part of this model, so they cannot leak
        into the digest by construction.
        """

        d = self.to_dict(include_digest=False)
        d.pop("created_at", None)
        d.pop("finalized_at", None)
        canonical = json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()
