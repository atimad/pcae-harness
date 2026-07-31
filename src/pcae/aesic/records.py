"""Stage 1 result and Authority Evaluation Record (AER) value types
(AESIC-001 v1.3 §5.2.1, §8; AESIC-REQ-056, AESIC-REQ-118, AESIC-REQ-122).

Both types are immutable, AESIC-001-owned value types -- never AEMIC-001
types, never modifications of ``AuthorityEvaluationOutcome``'s own frozen
shape. This module defines no schema file (AESIC-REQ-056's own "prose
only -- no schema" discipline); it defines exactly the plain-``dict``
serialization every other durable record in this codebase uses
(``compute_record_digest``, reused unmodified from
``pcae.governance.publication.record``, AESIC-REQ-055).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from pcae.authority_evaluation.errors import MalformedDeclarationError
from pcae.authority_evaluation.models import AuthorityEvaluationOutcome
from pcae.authority_evaluation.serialization import outcome_from_payload, outcome_to_payload
from pcae.governance.publication.record import compute_record_digest

AER_RECORD_FAMILY = "authority_evaluation_record"
AER_SCHEMA_VERSION = "aesic-authority-evaluation-record/1.0"
STAGE_1_RESULT_SCHEMA_VERSION = "aesic-stage-1-evaluation-result/1.0"
CANONICAL_POINTER_SCHEMA_VERSION = "aesic-authority-evaluation-pointer/1.0"


def _non_empty_str(value: object, field_name: str) -> str:
    if not isinstance(value, str) or value == "":
        raise MalformedDeclarationError(f"{field_name!s} must be a non-empty str, got {value!r}.")
    return value


@dataclass(frozen=True)
class Stage1EvaluationResult:
    """The immutable return type of ``evaluate_stage_1`` (AESIC-REQ-122).

    Carries exactly three fields: the unmodified Stage 1
    ``AuthorityEvaluationOutcome``, this invocation's own ``evaluation_id``
    (§16.8), and a verbatim copy of ``session.session_id`` at the moment
    Stage 1 ran. Never persisted as its own, independently-addressable
    artifact (AESIC-REQ-064/080) -- a caller may retain it in memory and
    hand it back, unmodified, to ``evaluate_stage_2`` as ``stage_1_result``.
    """

    outcome: AuthorityEvaluationOutcome
    evaluation_id: str
    session_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, AuthorityEvaluationOutcome):
            raise MalformedDeclarationError(
                f"Stage1EvaluationResult.outcome must be an AuthorityEvaluationOutcome, "
                f"got {self.outcome!r}."
            )
        _non_empty_str(self.evaluation_id, "Stage1EvaluationResult.evaluation_id")
        _non_empty_str(self.session_id, "Stage1EvaluationResult.session_id")


def stage_1_result_to_payload(result: Stage1EvaluationResult) -> Dict[str, Any]:
    return {
        "outcome": outcome_to_payload(result.outcome),
        "evaluation_id": result.evaluation_id,
        "session_id": result.session_id,
        "schema_version": STAGE_1_RESULT_SCHEMA_VERSION,
    }


def stage_1_result_from_payload(payload: Dict[str, Any]) -> Stage1EvaluationResult:
    try:
        return Stage1EvaluationResult(
            outcome=outcome_from_payload(payload["outcome"]),
            evaluation_id=payload["evaluation_id"],
            session_id=payload["session_id"],
        )
    except KeyError as exc:
        raise MalformedDeclarationError(
            f"Stage1EvaluationResult payload missing required field: {exc}."
        ) from exc


def stage_1_evidence_equivalent(
    left: Optional[Stage1EvaluationResult], right: Optional[Stage1EvaluationResult]
) -> bool:
    """AESIC-REQ-129's deterministic Stage-1-evidence-equivalence rule.

    ``evaluation_id`` is deliberately excluded (AESIC-REQ-098's own
    per-invocation uniqueness would otherwise make every distinct Stage 1
    invocation "not equivalent" regardless of substantive content).
    ``evaluated_at`` is excluded for the same reason AESIC-REQ-121's own
    comparison (1) excludes it: metadata neither ``evaluate()`` nor this
    equivalence test branches on.
    """

    if left is None and right is None:
        return True
    if (left is None) != (right is None):
        return False
    assert left is not None and right is not None
    if left.session_id != right.session_id:
        return False
    lo, ro = left.outcome, right.outcome
    return (
        lo.template_ref == ro.template_ref
        and lo.template_version == ro.template_version
        and lo.claimed_identity == ro.claimed_identity
        and lo.evaluation_result == ro.evaluation_result
        and lo.declaration_ref == ro.declaration_ref
        and lo.citation_text == ro.citation_text
        and lo.evaluator_version == ro.evaluator_version
        and lo.schema_version == ro.schema_version
    )


@dataclass(frozen=True)
class AuthorityEvaluationRecord:
    """The immutable Authority Evaluation Record (AER), Stage 2's sole
    persisted output (AESIC-REQ-051, AESIC-REQ-056).

    ``stage_1_outcome_ref`` is an inline, verbatim, byte-for-byte embedded
    copy (AESIC-REQ-118) -- never a pointer into any separately-persisted
    Stage 1 artifact, because none exists or may ever exist.
    """

    record_id: str
    package_id: str
    evaluation_id: str
    outcome: AuthorityEvaluationOutcome
    evaluated_at: str
    stage_1_outcome_ref: Optional[Stage1EvaluationResult] = None
    record_family: str = field(default=AER_RECORD_FAMILY)
    stage: str = field(default="stage_2")
    schema_version: str = field(default=AER_SCHEMA_VERSION)
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        _non_empty_str(self.record_id, "AuthorityEvaluationRecord.record_id")
        _non_empty_str(self.package_id, "AuthorityEvaluationRecord.package_id")
        _non_empty_str(self.evaluation_id, "AuthorityEvaluationRecord.evaluation_id")
        if not isinstance(self.outcome, AuthorityEvaluationOutcome):
            raise MalformedDeclarationError(
                f"AuthorityEvaluationRecord.outcome must be an AuthorityEvaluationOutcome, "
                f"got {self.outcome!r}."
            )
        _non_empty_str(self.evaluated_at, "AuthorityEvaluationRecord.evaluated_at")
        if self.record_family != AER_RECORD_FAMILY:
            raise MalformedDeclarationError(
                f"AuthorityEvaluationRecord.record_family must equal exactly "
                f"{AER_RECORD_FAMILY!r}, got {self.record_family!r}."
            )
        if self.stage != "stage_2":
            raise MalformedDeclarationError(
                f"AuthorityEvaluationRecord.stage must equal exactly 'stage_2', got {self.stage!r}."
            )
        if self.stage_1_outcome_ref is not None and not isinstance(
            self.stage_1_outcome_ref, Stage1EvaluationResult
        ):
            raise MalformedDeclarationError(
                "AuthorityEvaluationRecord.stage_1_outcome_ref must be a "
                f"Stage1EvaluationResult or None, got {self.stage_1_outcome_ref!r}."
            )


def _aer_content_payload(record: AuthorityEvaluationRecord) -> Dict[str, Any]:
    """The AER's own content, excluding ``record_digest`` -- the exact
    input ``compute_record_digest`` hashes (AESIC-REQ-055)."""

    payload: Dict[str, Any] = {
        "record_id": record.record_id,
        "record_family": record.record_family,
        "package_id": record.package_id,
        "evaluation_id": record.evaluation_id,
        "stage": record.stage,
        "outcome": outcome_to_payload(record.outcome),
        "evaluated_at": record.evaluated_at,
        "schema_version": record.schema_version,
    }
    if record.stage_1_outcome_ref is not None:
        payload["stage_1_outcome_ref"] = stage_1_result_to_payload(record.stage_1_outcome_ref)
    else:
        payload["stage_1_outcome_ref"] = None
    return payload


def aer_to_payload(record: AuthorityEvaluationRecord) -> Dict[str, Any]:
    """Serialize ``record`` to a plain, JSON-compatible ``dict``, digested
    (AESIC-REQ-055, AESIC-REQ-083 -- AES owns computing/attaching the
    digest; no downstream consumer recomputes or overrides it)."""

    payload = _aer_content_payload(record)
    payload["record_digest"] = compute_record_digest(payload)
    return payload


def aer_from_payload(payload: Dict[str, Any]) -> AuthorityEvaluationRecord:
    try:
        stage_1_payload = payload.get("stage_1_outcome_ref")
        stage_1_outcome_ref = (
            stage_1_result_from_payload(stage_1_payload) if stage_1_payload is not None else None
        )
        return AuthorityEvaluationRecord(
            record_id=payload["record_id"],
            package_id=payload["package_id"],
            evaluation_id=payload["evaluation_id"],
            outcome=outcome_from_payload(payload["outcome"]),
            evaluated_at=payload["evaluated_at"],
            stage_1_outcome_ref=stage_1_outcome_ref,
            record_family=payload.get("record_family", AER_RECORD_FAMILY),
            stage=payload.get("stage", "stage_2"),
            schema_version=payload.get("schema_version", AER_SCHEMA_VERSION),
            record_digest=payload.get("record_digest", ""),
        )
    except KeyError as exc:
        raise MalformedDeclarationError(
            f"AuthorityEvaluationRecord payload missing required field: {exc}."
        ) from exc


def verify_aer_digest(payload: Dict[str, Any]) -> bool:
    """Recompute the AER's own digest over its content and compare against
    the stored ``record_digest`` (§8.4)."""

    content = {key: value for key, value in payload.items() if key != "record_digest"}
    return compute_record_digest(content) == payload.get("record_digest")


@dataclass(frozen=True)
class CanonicalPointer:
    """The mutable, ``package_id``-keyed canonical pointer index
    (AESIC-REQ-119 item 2, AESIC-REQ-126). Its own content is exactly five
    fields; ``pointer_digest`` covers the other four."""

    package_id: str
    evaluation_id: str
    record_id: str
    record_digest: str
    pointer_digest: str = field(default="")
    schema_version: str = field(default=CANONICAL_POINTER_SCHEMA_VERSION)


def _pointer_content_payload(pointer: CanonicalPointer) -> Dict[str, Any]:
    return {
        "package_id": pointer.package_id,
        "evaluation_id": pointer.evaluation_id,
        "record_id": pointer.record_id,
        "record_digest": pointer.record_digest,
        "schema_version": pointer.schema_version,
    }


def pointer_to_payload(pointer: CanonicalPointer) -> Dict[str, Any]:
    content = _pointer_content_payload(pointer)
    payload = dict(content)
    payload["pointer_digest"] = _compute_pointer_digest(content)
    return payload


def _compute_pointer_digest(content: Dict[str, Any]) -> str:
    # Reuse the same hashing convention compute_record_digest uses, applied
    # to the pointer's own four fields (package_id, evaluation_id,
    # record_id, record_digest) -- compute_record_digest itself only ever
    # strips a top-level "record_digest" key, which would incorrectly strip
    # the pointer's own record_digest field. Hash under a neutral key name
    # instead so all four fields are covered.
    return compute_record_digest({"pointer_content": content})


def pointer_from_payload(payload: Dict[str, Any]) -> CanonicalPointer:
    try:
        return CanonicalPointer(
            package_id=payload["package_id"],
            evaluation_id=payload["evaluation_id"],
            record_id=payload["record_id"],
            record_digest=payload["record_digest"],
            pointer_digest=payload.get("pointer_digest", ""),
            schema_version=payload.get("schema_version", CANONICAL_POINTER_SCHEMA_VERSION),
        )
    except KeyError as exc:
        raise MalformedDeclarationError(f"CanonicalPointer payload missing required field: {exc}.") from exc


def verify_pointer_digest(payload: Dict[str, Any]) -> bool:
    content = {
        "package_id": payload.get("package_id"),
        "evaluation_id": payload.get("evaluation_id"),
        "record_id": payload.get("record_id"),
        "record_digest": payload.get("record_digest"),
        "schema_version": payload.get("schema_version", CANONICAL_POINTER_SCHEMA_VERSION),
    }
    return _compute_pointer_digest(content) == payload.get("pointer_digest")


__all__ = [
    "AER_RECORD_FAMILY",
    "AER_SCHEMA_VERSION",
    "STAGE_1_RESULT_SCHEMA_VERSION",
    "CANONICAL_POINTER_SCHEMA_VERSION",
    "Stage1EvaluationResult",
    "stage_1_result_to_payload",
    "stage_1_result_from_payload",
    "stage_1_evidence_equivalent",
    "AuthorityEvaluationRecord",
    "aer_to_payload",
    "aer_from_payload",
    "verify_aer_digest",
    "CanonicalPointer",
    "pointer_to_payload",
    "pointer_from_payload",
    "verify_pointer_digest",
]
