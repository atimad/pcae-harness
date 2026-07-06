"""Phase 115C: Repository Evidence Framework Prototype (Runtime Objects Only).

Implements the runtime representation of the Evidence contract frozen by
Phase 115B (``docs/PCAE_REPOSITORY_EVIDENCE_FRAMEWORK.md`` and
``docs/PCAE_EVIDENCE_PROVIDER_CONTRACT.md``): immutable ``Evidence``,
``EvidenceCollection``, the four frozen enumerations, ``EvidenceReference``,
and ``EvidenceProvenance``.

Evidence informs Repository Decisions. Evidence does not decide, does not
mutate repository state, does not promote artifacts, does not send
notifications, and does not become a Repository State Kernel primitive.

Disconnected by design: nothing in this module is imported by the
Repository Transition Validator (``core/repository_transition_validator.py``),
any Decision Framework, any lifecycle command, Notification Policy, or
``pcae agent verify-handoff``. This module is pure data modeling — stdlib
imports only, zero internal PCAE imports, zero side effects, zero I/O.

``EvidenceReference`` here (``evidence_id`` + optional ``note``) is a
distinct, intentionally simpler type from
``core/advisory_runtime.py``'s ``EvidenceReference`` (113B §3: ``domain``/
``object_id``/``field_path``/``evidence_summary``). The two serve
different citation models — Advisory Runtime cites a Runtime Snapshot
field path, while the Evidence Framework cites a stable Evidence ID within
one decision evaluation (115B "Explanation Reference Model") — and are not
meant to be unified; see
``docs/PHASE_115C_REPOSITORY_EVIDENCE_PROTOTYPE.md``.

Execution capability remains unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any


# ═══════════════════════════════════════════════════════════════════════
# Frozen Enumerations — 115B "Evidence Categories" / "Determinism Model" /
# "Confidence Model" / "Freshness Model"
# ═══════════════════════════════════════════════════════════════════════

class EvidenceCategory(str, Enum):
    """The 15 frozen Evidence categories (115B "Evidence Categories").

    ``UNKNOWN`` is a containment category, not a shortcut — 115B: unknown-
    category evidence should lower confidence or require human review when
    it matters to a blocking decision.
    """

    GIT = "git"
    TASK = "task"
    PHASE = "phase"
    REPORT = "report"
    METADATA = "metadata"
    ARCHITECTURE = "architecture"
    RUNTIME = "runtime"
    PUSH_STATE = "push_state"
    NOTIFICATION = "notification"
    GOVERNANCE = "governance"
    TEST_RESULT = "test_result"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    AI_REVIEW = "ai_review"
    UNKNOWN = "unknown"


class EvidenceDeterminism(str, Enum):
    """The 5 frozen determinism levels (115B "Determinism Model").

    Determinism never lets evidence bypass invariants — it is declared by
    the (future) provider and may inform, never override, a decision.
    """

    DETERMINISTIC = "deterministic"
    REPRODUCIBLE_EXTERNAL = "reproducible_external"
    PROBABILISTIC = "probabilistic"
    HUMAN_ASSERTED = "human_asserted"
    UNKNOWN = "unknown"


class EvidenceConfidence(str, Enum):
    """The 4 frozen confidence levels (115B "Confidence Model").

    Confidence describes trust in the evidence item, not permission to
    accept a transition. A high-confidence failure of a blocking invariant
    still blocks; a low-confidence positive signal does not authorize
    acceptance.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class EvidenceFreshness(str, Enum):
    """The 4 frozen freshness levels (115B "Freshness Model").

    Stale evidence is preserved and labelled, never silently discarded or
    chosen over current evidence.
    """

    CURRENT = "current"
    STALE = "stale"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


def _freeze_json_value(value: Any) -> Any:
    """Best-effort deep freeze of a JSON-compatible value.

    ``@dataclass(frozen=True)`` only prevents reassigning a field; it does
    not stop a caller from mutating a dict/list they handed to the
    constructor, nor does it stop a caller mutating a returned dict/list in
    place (the pattern already established in ``core/runtime_registry.py``
    for ``PluginDescriptor.manifest``). Dicts become read-only
    ``MappingProxyType`` views; lists become tuples; scalars pass through
    unchanged.
    """

    if isinstance(value, dict):
        return MappingProxyType({k: _freeze_json_value(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json_value(v) for v in value)
    return value


def _unfreeze_json_value(value: Any) -> Any:
    """Inverse of ``_freeze_json_value`` for JSON-compatible serialization.

    ``MappingProxyType``/``tuple`` are not directly ``json.dumps``-able in
    the shapes ``dict``/``list`` callers expect back from ``to_dict()``.
    """

    if isinstance(value, MappingProxyType):
        return {k: _unfreeze_json_value(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_unfreeze_json_value(v) for v in value]
    return value


# ═══════════════════════════════════════════════════════════════════════
# EvidenceReference — 115B "Explanation Reference Model"
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class EvidenceReference:
    """A citation of one Evidence ID, per 115B's Explanation Reference
    Model: decision explanations must be able to cite Evidence IDs such as
    ``E-git-001``. Nothing more than the ID and an optional human-readable
    note is frozen for this shape.
    """

    evidence_id: str
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("EvidenceReference evidence_id must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {"evidence_id": self.evidence_id, "note": self.note}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceReference":
        return cls(evidence_id=data["evidence_id"], note=data.get("note"))


# ═══════════════════════════════════════════════════════════════════════
# EvidenceProvenance — metadata only, no runtime behavior
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class EvidenceProvenance:
    """Provenance metadata exposed by every ``Evidence`` object.

    Purely descriptive: it carries no behavior and is never consulted by
    any decision logic in this module (there is none). ``producer`` may
    repeat the owning ``Evidence.producer`` value or be a more specific
    descriptor (e.g. ``"git_provider@v1"``); ``produced_from`` names the
    originating command/process/input (e.g. ``"git status --porcelain"``);
    ``deterministic_origin`` records whether the originating process
    itself is deterministic, independent of the Evidence item's own
    declared ``determinism`` classification.
    """

    producer: str
    produced_from: str
    timestamp: str
    deterministic_origin: bool

    def __post_init__(self) -> None:
        if not self.producer:
            raise ValueError("EvidenceProvenance producer must be non-empty")
        if not self.produced_from:
            raise ValueError("EvidenceProvenance produced_from must be non-empty")
        if not self.timestamp:
            raise ValueError("EvidenceProvenance timestamp must be non-empty")
        if not isinstance(self.deterministic_origin, bool):
            raise ValueError(
                "EvidenceProvenance deterministic_origin must be a bool, "
                f"got {self.deterministic_origin!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "producer": self.producer,
            "produced_from": self.produced_from,
            "timestamp": self.timestamp,
            "deterministic_origin": self.deterministic_origin,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceProvenance":
        return cls(
            producer=data["producer"],
            produced_from=data["produced_from"],
            timestamp=data["timestamp"],
            deterministic_origin=data["deterministic_origin"],
        )


# ═══════════════════════════════════════════════════════════════════════
# Evidence — 115B "Evidence Contract" (14 frozen fields + provenance)
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Evidence:
    """One immutable Evidence item, per 115B's frozen Evidence Contract.

    The 14 required fields are exactly the fields frozen by 115B. Category,
    freshness, confidence, and determinism accept either the matching enum
    member or its raw string value; both are normalized to the enum member
    in ``__post_init__`` (invalid values raise ``ValueError`` via the
    enum's own constructor). ``references``, ``observed_value``, and
    ``expected_value`` are defensively frozen so no caller-held mutable
    reference can change this item after construction.

    ``provenance`` is an additional field (Objective 5 of Phase 115C, not
    itself one of 115B's 14 frozen fields) exposing ``EvidenceProvenance``
    metadata on every item.

    Evidence does not decide. Evidence does not mutate repository state.
    No mutation is possible after construction: the dataclass is frozen,
    ``references``/``observed_value``/``expected_value`` are deep-frozen,
    and no method on this class writes to any field.
    """

    evidence_id: str
    source: str
    category: EvidenceCategory
    producer: str
    timestamp_utc: str
    freshness: EvidenceFreshness
    confidence: EvidenceConfidence
    determinism: EvidenceDeterminism
    scope: str
    references: tuple[str, ...]
    observed_value: Any
    explanation: str
    provenance: EvidenceProvenance
    expected_value: Any = None
    limitations: str = ""

    def __post_init__(self) -> None:
        for field_name in ("evidence_id", "source", "producer", "timestamp_utc", "scope", "explanation"):
            if not getattr(self, field_name):
                raise ValueError(f"Evidence {field_name} must be non-empty")

        object.__setattr__(self, "category", EvidenceCategory(self.category))
        object.__setattr__(self, "freshness", EvidenceFreshness(self.freshness))
        object.__setattr__(self, "confidence", EvidenceConfidence(self.confidence))
        object.__setattr__(self, "determinism", EvidenceDeterminism(self.determinism))

        if not isinstance(self.provenance, EvidenceProvenance):
            raise ValueError(
                f"Evidence provenance must be an EvidenceProvenance, got {self.provenance!r}"
            )

        object.__setattr__(self, "references", tuple(self.references))
        object.__setattr__(self, "observed_value", _freeze_json_value(self.observed_value))
        object.__setattr__(self, "expected_value", _freeze_json_value(self.expected_value))

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "category": self.category.value,
            "producer": self.producer,
            "timestamp_utc": self.timestamp_utc,
            "freshness": self.freshness.value,
            "confidence": self.confidence.value,
            "determinism": self.determinism.value,
            "scope": self.scope,
            "references": list(self.references),
            "observed_value": _unfreeze_json_value(self.observed_value),
            "expected_value": _unfreeze_json_value(self.expected_value),
            "explanation": self.explanation,
            "limitations": self.limitations,
            "provenance": self.provenance.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evidence":
        return cls(
            evidence_id=data["evidence_id"],
            source=data["source"],
            category=data["category"],
            producer=data["producer"],
            timestamp_utc=data["timestamp_utc"],
            freshness=data["freshness"],
            confidence=data["confidence"],
            determinism=data["determinism"],
            scope=data["scope"],
            references=tuple(data.get("references", ())),
            observed_value=data.get("observed_value"),
            explanation=data["explanation"],
            provenance=EvidenceProvenance.from_dict(data["provenance"]),
            expected_value=data.get("expected_value"),
            limitations=data.get("limitations", ""),
        )


# ═══════════════════════════════════════════════════════════════════════
# EvidenceCollection — ordered container, no decision logic
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class EvidenceCollection:
    """An ordered, immutable collection of ``Evidence`` items.

    Structural only: lookup, iteration, and filtering by category/source/
    determinism/confidence. No decision logic and no evaluation live here
    — conflicting or low-confidence evidence is preserved exactly as
    given, per 115B's Conflict Semantics ("Providers never silently choose
    one conflicting item... evaluate the conflict centrally in the
    Decision Framework"), which this module does not implement.

    Duplicate ``evidence_id`` values within one collection are rejected at
    construction and at ``add()`` time. Adding evidence never mutates an
    existing collection — ``add()`` returns a new ``EvidenceCollection``.
    """

    items: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        items = tuple(self.items)
        object.__setattr__(self, "items", items)
        seen: set[str] = set()
        for item in items:
            if item.evidence_id in seen:
                raise ValueError(
                    f"Duplicate evidence_id in EvidenceCollection: {item.evidence_id!r}"
                )
            seen.add(item.evidence_id)

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __contains__(self, evidence_id: object) -> bool:
        return any(item.evidence_id == evidence_id for item in self.items)

    def by_id(self, evidence_id: str) -> Evidence | None:
        for item in self.items:
            if item.evidence_id == evidence_id:
                return item
        return None

    def by_category(self, category: EvidenceCategory | str) -> "EvidenceCollection":
        category = EvidenceCategory(category)
        return EvidenceCollection(tuple(item for item in self.items if item.category == category))

    def by_source(self, source: str) -> "EvidenceCollection":
        return EvidenceCollection(tuple(item for item in self.items if item.source == source))

    def by_determinism(self, determinism: EvidenceDeterminism | str) -> "EvidenceCollection":
        determinism = EvidenceDeterminism(determinism)
        return EvidenceCollection(
            tuple(item for item in self.items if item.determinism == determinism)
        )

    def by_confidence(self, confidence: EvidenceConfidence | str) -> "EvidenceCollection":
        confidence = EvidenceConfidence(confidence)
        return EvidenceCollection(
            tuple(item for item in self.items if item.confidence == confidence)
        )

    def add(self, evidence: Evidence) -> "EvidenceCollection":
        if evidence.evidence_id in self:
            raise ValueError(
                f"Duplicate evidence_id, already present in collection: {evidence.evidence_id!r}"
            )
        return EvidenceCollection(self.items + (evidence,))

    def to_dict(self) -> dict[str, Any]:
        return {"items": [item.to_dict() for item in self.items]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceCollection":
        return cls(tuple(Evidence.from_dict(item) for item in data.get("items", ())))
