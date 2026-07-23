"""Read-only, non-authoritative CHGR artifact inspection (Phase 143E).

Implements the business logic behind ``pcae governance-record inspect
<path>`` (``src/pcae/commands/governance_record.py``): parsing, packaged
CHGR schema resource resolution, manifest/registry verification,
record-type/version/identity resolution, schema validation, and
disclosure-complete observation construction. This module owns no CLI
argument parsing, no rendering, no lifecycle mutation, no authority
resolution, no runtime-capability decision, and no repository discovery. It
reads only the explicitly supplied artifact bytes handed to it by the CLI
layer and installed package resources via
``pcae.schema_resources.chgr_root()``.

Every successful inspection is a representation-only observation: it does
not prove authority, authorization, lifecycle completion, or that the
represented governance act was valid, applicable, current, or performed by
an authorized human. Declared fields (what the artifact itself asserts) and
verified fields (what this module actually confirmed) are kept visually
distinct in the returned observation -- inspection never upgrades a
declared claim into a verified one.
"""
from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
from typing import Any, Literal, Union

from pcae.schema_resources import chgr_root
from pcae.schema_runtime import (
    ManifestIntegrityError,
    OutcomeStatus,
    SchemaRegistryError,
    build_offline_registry,
    load_and_verify_manifest,
    parse_strict_json,
    validate_record_shape,
)

CONSUMER_ID = "pcae-governance-record-inspect-v1"
CHGR_CONTRACT_VERSION = "CHGR-001/1.0"
SUPPORTED_SCHEMA_VERSION = "1.0"
_MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/chgr/manifest.schema.json"
_UNAVAILABLE = "unavailable"

_REPRESENTATION_ONLY_DISCLOSURE = (
    "Successful schema validation means only that an artifact conforms to "
    "the CHGR representation contract. It does not establish that the "
    "represented governance act was valid, applicable, current, or "
    "performed by an authorized human. Governed lifecycle semantics remain "
    "authoritative; execution is unavailable."
)

_KNOWN_RECORD_TYPES = frozenset(
    {
        "decision_template",
        "human_governance_record",
        "human_confirmation_evidence",
        "governance_record_provenance",
        "governance_record_integrity",
        "governance_record_lifecycle_event",
    }
)


@dataclasses.dataclass(frozen=True)
class InspectionObservation:
    """Immutable, disclosure-complete observation of one CHGR artifact.

    ``declared_*`` fields are copied verbatim from the artifact and never
    independently confirmed by inspection alone (that is ``pcae
    governance-record verify``'s job); this dataclass keeps declared and
    verified information visually separate on purpose.
    """

    source_artifact_identity: str
    input_digest: str
    record_family: str
    record_identity: str
    schema_identity: str
    schema_version: str
    declared_record_digest: str
    manifest_entry: dict[str, Any]
    registry_resource: dict[str, Any]
    record_claims: dict[str, Any]
    disclosure: str = _REPRESENTATION_ONLY_DISCLOSURE
    consumer_identity: str = CONSUMER_ID
    chgr_contract_version: str = CHGR_CONTRACT_VERSION
    outcome: Literal["inspected"] = "inspected"

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "consumer_identity": self.consumer_identity,
            "chgr_contract_version": self.chgr_contract_version,
            "source_artifact_identity": self.source_artifact_identity,
            "input_digest": self.input_digest,
            "record_family": self.record_family,
            "record_identity": self.record_identity,
            "schema_identity": self.schema_identity,
            "schema_version": self.schema_version,
            "declared_record_digest": self.declared_record_digest,
            "manifest_entry": self.manifest_entry,
            "registry_resource": self.registry_resource,
            "validation": {"schema": "shape_conformant", "authority": "not_performed", "verification": "not_performed"},
            "record_claims": self.record_claims,
            "disclosure": self.disclosure,
        }


@dataclasses.dataclass(frozen=True)
class InspectionFailure:
    """Stable fail-closed result. No partial inspection success exists."""

    outcome: str
    message: str
    source_artifact_identity: str
    input_digest: str
    record_family: str = _UNAVAILABLE
    schema_identity: str = _UNAVAILABLE
    schema_version: str = _UNAVAILABLE
    disclosure: str = _REPRESENTATION_ONLY_DISCLOSURE
    consumer_identity: str = CONSUMER_ID
    chgr_contract_version: str = CHGR_CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "message": self.message,
            "consumer_identity": self.consumer_identity,
            "chgr_contract_version": self.chgr_contract_version,
            "source_artifact_identity": self.source_artifact_identity,
            "input_digest": self.input_digest,
            "record_family": self.record_family,
            "schema_identity": self.schema_identity,
            "schema_version": self.schema_version,
            "disclosure": self.disclosure,
        }


InspectionOutcome = Union[InspectionObservation, InspectionFailure]


def _safe_text(value: object) -> str:
    return value if type(value) is str and value else _UNAVAILABLE


def _failure(
    category: str,
    message: str,
    *,
    source_artifact_identity: str,
    input_digest: str,
    record: dict[str, Any] | None = None,
) -> InspectionFailure:
    record = record or {}
    return InspectionFailure(
        outcome=category,
        message=message,
        source_artifact_identity=_safe_text(source_artifact_identity),
        input_digest=input_digest,
        record_family=_safe_text(record.get("record_type")),
        schema_identity=_safe_text(record.get("schema_id")),
        schema_version=_safe_text(record.get("schema_version")),
    )


def inspect_artifact_at_path(path: Path, *, artifact_bytes: bytes, json_output: bool = False) -> InspectionOutcome:
    """Inspect one caller-supplied CHGR artifact and return exactly one outcome.

    ``path`` is the caller-supplied path identity (display only, never
    re-read). ``artifact_bytes`` is the exact bytes already read by the
    CLI layer's bounded read. Performs no filesystem I/O beyond the
    package-owned CHGR schema resource resolution below, no mutation, and
    no network access.

    Failure precedence: parse -> resource resolution -> manifest ->
    record-type dispatch -> registry entry -> schema.
    """
    del json_output  # accepted-but-inert, for signature parity with the CLI layer
    source_artifact_identity = str(path)
    input_digest = hashlib.sha256(artifact_bytes).hexdigest()

    parsed = parse_strict_json(artifact_bytes, require_top_level_object=True)
    if parsed.status is not OutcomeStatus.VALID or type(parsed.value) is not dict:
        return _failure(
            "malformed_artifact",
            "The supplied artifact is not a strict JSON object.",
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
        )
    record: dict[str, Any] = parsed.value

    if "schema_id" not in record or "record_type" not in record:
        return _failure(
            "phase_report_or_non_chgr_artifact",
            "The supplied artifact carries no CHGR envelope (schema_id/record_type); "
            "it is not a CHGR artifact of any kind.",
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
            record=record,
        )

    try:
        with chgr_root() as package_root:
            try:
                registry = build_offline_registry(package_root)
            except (OSError, SchemaRegistryError, ValueError):
                return _failure(
                    "registry_failure",
                    "The installed offline CHGR schema registry could not be built.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            try:
                manifest = load_and_verify_manifest(
                    package_root / "manifest.json",
                    package_root=package_root,
                    registry=registry,
                    manifest_schema_id=_MANIFEST_SCHEMA_ID,
                    excluded_relative_paths=frozenset({"manifest.schema.json"}),
                )
            except (OSError, ManifestIntegrityError, SchemaRegistryError, ValueError):
                return _failure(
                    "manifest_failure",
                    "The installed CHGR schema manifest failed frozen integrity verification.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            family = record.get("record_type")
            if type(family) is not str or family not in _KNOWN_RECORD_TYPES:
                return _failure(
                    "unknown_record_family",
                    "The declared record_type is not a CHGR family implemented this increment.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            manifest_entries = [
                raw
                for raw in manifest.document["entries"]
                if raw.get("family") == family and raw.get("file_path", "").startswith("records/")
            ]
            if len(manifest_entries) != 1:
                return _failure(
                    "manifest_entry_missing",
                    "The verified manifest does not contain exactly one entry for the declared family.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )
            manifest_entry = manifest_entries[0]

            schema_id = record.get("schema_id")
            if schema_id != manifest_entry.get("schema_id"):
                return _failure(
                    "family_identity_mismatch",
                    "The declared record_type and schema_id do not agree.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            try:
                resource_info = registry.resource_info(schema_id)
            except SchemaRegistryError:
                return _failure(
                    "registry_entry_missing",
                    "The installed offline registry has no entry for the declared schema identity.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            shape_result = validate_record_shape(record, schema_id=schema_id, registry=registry)
            if shape_result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE:
                return _failure(
                    "registry_failure",
                    "The offline registry could not resolve the declared schema graph.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )
            if shape_result.status is not OutcomeStatus.VALID:
                return _failure(
                    "schema_validation_failed",
                    "The artifact does not conform to its declared CHGR schema.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            return InspectionObservation(
                source_artifact_identity=source_artifact_identity,
                input_digest=input_digest,
                record_family=family,
                record_identity=_safe_text(record.get("record_id")),
                schema_identity=schema_id,
                schema_version=_safe_text(record.get("schema_version")),
                declared_record_digest=_safe_text(record.get("record_digest")),
                manifest_entry=dict(manifest_entry),
                registry_resource={
                    "schema_id": resource_info.schema_id,
                    "relative_path": resource_info.relative_path,
                    "sha256": resource_info.sha256,
                    "size_bytes": resource_info.size_bytes,
                },
                record_claims=dict(record),
            )
    except OSError:
        return _failure(
            "registry_failure",
            "The installed CHGR package resources could not be resolved.",
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
            record=record,
        )


__all__ = [
    "CONSUMER_ID",
    "CHGR_CONTRACT_VERSION",
    "SUPPORTED_SCHEMA_VERSION",
    "InspectionFailure",
    "InspectionObservation",
    "InspectionOutcome",
    "inspect_artifact_at_path",
]
