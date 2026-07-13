"""Deterministic canonical serialization for digesting (135E §6-§7).

- UTF-8, no BOM.
- Keys sorted lexicographically (ASCII) at every nesting level.
- Compact separators, no incidental whitespace.
- Enum values are emitted as their exact string identifiers.
- A field absent because its state has not been reached yet is omitted
  entirely; `None` is reserved for a field that is explicitly, meaningfully
  empty.
- Commit sets are serialized as a sorted list (by hash, ascending) —
  a serialization convenience, not a semantic ordering claim.
"""

from __future__ import annotations

import dataclasses
import enum
import json
from collections.abc import Mapping
from typing import Any, Optional

from pcae.cltr_prototype.models import (
    CommitClassificationResult,
    CommitDeclaration,
    CommitOwnershipClassification,
    CommitRole,
    EvidenceRef,
    EvidenceType,
    EvidenceVerificationStatus,
    FailureClassification,
    Identity,
    SpineState,
    TransitionRecord,
)


def _to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, enum.Enum):
        return value.value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        out = {}
        for f in dataclasses.fields(value):
            field_value = getattr(value, f.name)
            jsonable = _to_jsonable(field_value)
            if jsonable is None and field_value is None:
                # Explicitly-None fields are meaningful absence markers for
                # some fields (e.g. task_id) — preserve as null. Fields that
                # simply were never reached are handled by the record-level
                # omission logic in `record_to_dict`, not here.
                out[f.name] = None
            else:
                out[f.name] = jsonable
        return out
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [_to_jsonable(v) for v in value]
        if all(isinstance(v, str) for v in items):
            return sorted(items)
        return items
    if isinstance(value, Mapping):
        return {str(k): _to_jsonable(v) for k, v in sorted(value.items())}
    return value


def record_to_dict(record: TransitionRecord, *, include_digest: bool = True) -> dict:
    """Convert a record to a plain dict, omitting fields not yet reached.

    `include_digest=False` excludes `record_digest` from the output — used
    when computing the digest input itself (135E §7's self-exclusion rule).
    """

    raw = _to_jsonable(record)
    result = {}
    for key, value in raw.items():
        if key == "record_digest" and not include_digest:
            continue
        if value is None and key not in ("task_id",):
            # Omit not-yet-reached optional fields entirely (never emit as
            # null) except task_id, which is explicitly nullable content.
            continue
        if isinstance(value, (list, tuple)) and len(value) == 0:
            # An explicitly declared empty collection (e.g. declared_commits
            # = []) is still meaningful and is retained.
            result[key] = value
            continue
        result[key] = value
    return result


def canonicalize(record: TransitionRecord, *, include_digest: bool = True) -> bytes:
    """Deterministic canonical byte form for digesting and on-disk output."""

    as_dict = record_to_dict(record, include_digest=include_digest)
    return json.dumps(
        as_dict,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _evidence_ref_from_dict(d: Optional[dict]) -> Optional[EvidenceRef]:
    if d is None:
        return None
    return EvidenceRef(
        evidence_id=d["evidence_id"],
        evidence_type=EvidenceType(d["evidence_type"]),
        transition_id=d["transition_id"],
        phase_id=d["phase_id"],
        verification_status=EvidenceVerificationStatus(d["verification_status"]),
        source_path=d.get("source_path"),
        digest=d.get("digest"),
        source_revision=d.get("source_revision"),
        observation_timestamp=d.get("observation_timestamp"),
        limitation=d.get("limitation"),
    )


def record_from_dict(d: dict) -> TransitionRecord:
    """Reconstruct a `TransitionRecord` from a plain dict (the reverse of
    `record_to_dict`). Used by `verifier.py` and `persistence.py` readers to
    independently re-check a persisted record's content — this function
    performs no repair; it either reconstructs faithfully or raises.
    """

    allowed_record_fields = {field.name for field in dataclasses.fields(TransitionRecord)}
    unknown_record_fields = set(d) - allowed_record_fields
    if unknown_record_fields:
        raise ValueError(f"unknown TransitionRecord field(s): {sorted(unknown_record_fields)}")
    if d.get("schema_version", "cltr-prototype-0.1") != "cltr-prototype-0.1":
        raise ValueError(f"unsupported schema_version: {d.get('schema_version')!r}")
    if d.get("contract_version", "CLTR-001/1.0") != "CLTR-001/1.0":
        raise ValueError(f"unsupported contract_version: {d.get('contract_version')!r}")

    identity_dict = d["identity"]
    unknown_identity_fields = set(identity_dict) - {field.name for field in dataclasses.fields(Identity)}
    if unknown_identity_fields:
        raise ValueError(f"unknown Identity field(s): {sorted(unknown_identity_fields)}")
    identity = Identity(
        transition_id=identity_dict["transition_id"],
        phase_id=identity_dict["phase_id"],
        repository_identity=identity_dict["repository_identity"],
        branch_identity=identity_dict["branch_identity"],
        task_id=identity_dict.get("task_id"),
    )

    declared_commits = tuple(
        CommitDeclaration(commit_hash=c["commit_hash"], declared_role=CommitRole(c["declared_role"]))
        for c in d.get("declared_commits", [])
    )
    commit_classifications = tuple(
        CommitClassificationResult(
            commit_hash=c["commit_hash"],
            classification=CommitOwnershipClassification(c["classification"]),
            reason=c.get("reason", ""),
        )
        for c in d.get("commit_classifications", [])
    )
    evidence_refs = tuple(_evidence_ref_from_dict(e) for e in d.get("evidence_refs", []))

    return TransitionRecord(
        identity=identity,
        spine_state=SpineState(d["spine_state"]),
        source_revision=d["source_revision"],
        schema_version=d.get("schema_version", "cltr-prototype-0.1"),
        contract_version=d.get("contract_version", "CLTR-001/1.0"),
        final_revision=d.get("final_revision"),
        final_revision_provisional=d.get("final_revision_provisional", True),
        prior_state=SpineState(d["prior_state"]) if d.get("prior_state") else None,
        projected_state=d.get("projected_state"),
        certified_state=d.get("certified_state"),
        quarantined=d.get("quarantined", False),
        superseded=d.get("superseded", False),
        superseded_by=d.get("superseded_by"),
        declared_commits=declared_commits,
        commit_classifications=commit_classifications,
        evidence_refs=evidence_refs,
        report_binding=_evidence_ref_from_dict(d.get("report_binding")),
        metadata_binding=_evidence_ref_from_dict(d.get("metadata_binding")),
        snapshot_binding=_evidence_ref_from_dict(d.get("snapshot_binding")),
        checkpoint_binding=_evidence_ref_from_dict(d.get("checkpoint_binding")),
        promotion_binding=_evidence_ref_from_dict(d.get("promotion_binding")),
        notification_binding=_evidence_ref_from_dict(d.get("notification_binding")),
        marker_binding=_evidence_ref_from_dict(d.get("marker_binding")),
        receipt_binding=_evidence_ref_from_dict(d.get("receipt_binding")),
        architecture_status_binding=_evidence_ref_from_dict(d.get("architecture_status_binding")),
        timestamps=d.get("timestamps", {}),
        failure_classification=FailureClassification(d.get("failure_classification", "none")),
        limitations=tuple(d.get("limitations", [])),
        compatibility_metadata=d.get("compatibility_metadata", {}),
        record_digest=d.get("record_digest"),
    )


def canonicalize_dict(value: dict) -> bytes:
    """Canonicalize an arbitrary plain dict (used by non-record derivatives)."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
