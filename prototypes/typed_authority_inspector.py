"""Prototype-only explicit-artifact Typed Authority Model inspector.

This module implements the single Allowed ``inspection`` consumer selected by
TAMP-001 v1.0 and governed by TAMC-001 v1.0.  It is intentionally not imported
or registered by any production surface.  The operation accepts one explicit
record and explicit schema-package/source context, reuses the frozen Stage 3
owners, and returns an immutable observation.  It performs no discovery,
persistence, authority resolution, lifecycle interpretation, or execution.
"""

from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
from typing import Any, Literal, Union

from pcae.cltr.authority import (
    AuthorityEpoch,
    AuthorityState,
    Certification,
    CompatibilityState,
    ConcurrencyConflict,
    CutoverCandidate,
    CutoverRequest,
    FinalizationReceiptAuthorityBinding,
    HumanAuthorization,
    MarkerAuthorityBinding,
    NotificationAuthorityBinding,
    OpaqueJsonValue,
    PublicationAttempt,
    PublicationEvidence,
    QuarantineRecord,
    ReadinessPackage,
    RecoveryJournalEntry,
)
from pcae.cltr.authority.errors import TypedModelError
from pcae.cltr.authority.serialization import to_canonical_bytes
from pcae.schema_runtime import (
    ManifestIntegrityError,
    OutcomeStatus,
    SchemaRegistryError,
    build_offline_registry,
    load_and_verify_manifest,
    parse_strict_json,
    validate_record_shape,
)

CONSUMER_ID = "tamp-001-explicit-artifact-inspector"
TAMC_CONTRACT_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSION = "1.0"
SUPPORTED_MODEL_VERSION = "1.0"
MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/manifest.schema.json"
REPRESENTATION_ONLY_DISCLOSURE = (
    "This inspection describes a representation only; governed lifecycle "
    "semantics remain authoritative, no authority is inferred or activated, "
    "and execution is unavailable."
)
UNAVAILABLE = "unavailable"


# Explicit governed binding only.  It contains no discovery, fallback, policy,
# or schema logic; each value is the frozen Stage 3 model owner.
_MODEL_BY_FAMILY: dict[str, type] = {
    "authority_epoch": AuthorityEpoch,
    "authority_state": AuthorityState,
    "certification": Certification,
    "compatibility_state": CompatibilityState,
    "concurrency_conflict": ConcurrencyConflict,
    "cutover_candidate": CutoverCandidate,
    "cutover_request": CutoverRequest,
    "human_authorization": HumanAuthorization,
    "marker_authority_binding": MarkerAuthorityBinding,
    "notification_authority_binding": NotificationAuthorityBinding,
    "publication_attempt": PublicationAttempt,
    "publication_evidence": PublicationEvidence,
    "quarantine_record": QuarantineRecord,
    "readiness_package": ReadinessPackage,
    "receipt_authority_binding": FinalizationReceiptAuthorityBinding,
    "recovery_journal_entry": RecoveryJournalEntry,
}


@dataclasses.dataclass(frozen=True)
class ExplicitArtifactContext:
    """All ambient-looking inputs required by one inspection operation.

    Paths are caller-supplied operation inputs.  The inspector never derives
    them from the working directory, environment, repository, or filename.
    ``source_location`` may be the explicit ``UNAVAILABLE`` sentinel.
    """

    source_artifact_identity: str
    source_location: str
    schema_package_identity: str
    package_root: Path
    manifest_path: Path
    tamc_contract_version: str = TAMC_CONTRACT_VERSION
    manifest_schema_id: str = MANIFEST_SCHEMA_ID


@dataclasses.dataclass(frozen=True)
class InspectionSuccess:
    """Immutable, provenance-complete observation of one representation."""

    source_artifact_identity: str
    source_location: str
    schema_package_identity: str
    input_digest: str
    record_family: str
    record_identity: str
    schema_identity: str
    schema_version: str
    model_version: str
    declared_record_digest: str
    manifest_entry: OpaqueJsonValue
    registry_resource: OpaqueJsonValue
    schema_validation: OpaqueJsonValue
    model_validation: OpaqueJsonValue
    record_claims: OpaqueJsonValue
    provenance: OpaqueJsonValue
    disclosure: str = REPRESENTATION_ONLY_DISCLOSURE
    consumer_identity: str = CONSUMER_ID
    tamc_contract_version: str = TAMC_CONTRACT_VERSION
    outcome: Literal["inspected"] = "inspected"

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "consumer_identity": self.consumer_identity,
            "tamc_contract_version": self.tamc_contract_version,
            "source_artifact_identity": self.source_artifact_identity,
            "source_location": self.source_location,
            "schema_package_identity": self.schema_package_identity,
            "input_digest": self.input_digest,
            "record_family": self.record_family,
            "record_identity": self.record_identity,
            "schema_identity": self.schema_identity,
            "schema_version": self.schema_version,
            "model_version": self.model_version,
            "declared_record_digest": self.declared_record_digest,
            "manifest_entry": self.manifest_entry.to_json(),
            "registry_resource": self.registry_resource.to_json(),
            "validation": {
                "schema": self.schema_validation.to_json(),
                "model": self.model_validation.to_json(),
                "semantic": "not_performed",
                "lifecycle": "not_performed",
                "governance": "not_performed",
            },
            "record_claims": self.record_claims.to_json(),
            "provenance": self.provenance.to_json(),
            "disclosure": self.disclosure,
        }

    def to_canonical_bytes(self) -> bytes:
        return to_canonical_bytes(self.to_dict())


@dataclasses.dataclass(frozen=True)
class InspectionFailure:
    """Stable fail-closed result with no partial inspection success."""

    outcome: str
    message: str
    source_artifact_identity: str
    source_location: str
    input_digest: str
    record_family: str = UNAVAILABLE
    schema_identity: str = UNAVAILABLE
    schema_version: str = UNAVAILABLE
    model_version: str = UNAVAILABLE
    disclosure: str = REPRESENTATION_ONLY_DISCLOSURE
    consumer_identity: str = CONSUMER_ID
    tamc_contract_version: str = TAMC_CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def to_canonical_bytes(self) -> bytes:
        return to_canonical_bytes(self.to_dict())


InspectionResult = Union[InspectionSuccess, InspectionFailure]


def _safe_text(value: object) -> str:
    return value if type(value) is str and value else UNAVAILABLE


def _failure(
    category: str,
    message: str,
    *,
    context: ExplicitArtifactContext,
    input_digest: str,
    record: dict[str, Any] | None = None,
) -> InspectionFailure:
    record = record or {}
    return InspectionFailure(
        outcome=category,
        message=message,
        source_artifact_identity=_safe_text(context.source_artifact_identity),
        source_location=_safe_text(context.source_location),
        input_digest=input_digest,
        record_family=_safe_text(record.get("record_type")),
        schema_identity=_safe_text(record.get("schema_id")),
        schema_version=_safe_text(record.get("schema_version")),
        model_version=_safe_text(record.get("contract_version")),
        tamc_contract_version=context.tamc_contract_version,
    )


def _collect_named_values(value: Any, names: frozenset[str]) -> list[dict[str, Any]]:
    """Copy named provenance-bearing values without interpreting them."""

    found: list[dict[str, Any]] = []
    stack: list[tuple[str, Any]] = [("", value)]
    while stack:
        pointer, current = stack.pop()
        if type(current) is dict:
            for key in sorted(current, reverse=True):
                child = current[key]
                child_pointer = f"{pointer}/{key}"
                if key in names or key.endswith("_reference") or key.endswith("_references"):
                    found.append({"instance_path": child_pointer, "value": child})
                stack.append((child_pointer, child))
        elif type(current) is list:
            for index in range(len(current) - 1, -1, -1):
                stack.append((f"{pointer}/{index}", current[index]))
    return sorted(found, key=lambda item: item["instance_path"])


def _provenance_bundle(
    record: dict[str, Any],
    *,
    context: ExplicitArtifactContext,
    input_digest: str,
) -> OpaqueJsonValue:
    named = frozenset(
        {
            "authority_disclosure",
            "derivation",
            "extensions",
            "limitations",
            "opaque",
            "uncertainty",
        }
    )
    bundle = {
        "origin": {
            "source_artifact_identity": context.source_artifact_identity,
            "source_location": context.source_location,
            "schema_package_identity": context.schema_package_identity,
        },
        "record_identity": record["record_id"],
        "record_family": record["record_type"],
        "schema_identity": record["schema_id"],
        "schema_version": record["schema_version"],
        "model_version": record["contract_version"],
        "declared_record_digest": record["record_digest"],
        "derived_input_digest": input_digest,
        "copied_provenance_values": _collect_named_values(record, named),
        "complete_typed_record_claims": record,
        "derivation": {
            "copied_fields": "complete_typed_record_claims and copied_provenance_values",
            "derived_fields": ["derived_input_digest"],
            "external_references_followed": False,
        },
        "authority_neutrality": REPRESENTATION_ONLY_DISCLOSURE,
    }
    return OpaqueJsonValue.from_json(bundle)


def inspect_explicit_artifact(
    record_bytes: bytes,
    *,
    context: ExplicitArtifactContext,
) -> InspectionResult:
    """Inspect one caller-supplied Stage 3 record and return one value.

    Failure precedence is parse -> explicit provenance context -> registry ->
    manifest -> family/version/identity dispatch -> schema -> model -> lossless
    provenance assembly.  No branch retries, repairs, falls back, dereferences a
    record reference, mutates an input, or performs an external side effect.
    """

    if type(record_bytes) is not bytes:
        record_bytes = b""
        input_digest = hashlib.sha256(record_bytes).hexdigest()
        return _failure(
            "malformed_artifact",
            "The supplied artifact must be exact bytes.",
            context=context,
            input_digest=input_digest,
        )
    input_digest = hashlib.sha256(record_bytes).hexdigest()

    parsed = parse_strict_json(record_bytes, require_top_level_object=True)
    if parsed.status is not OutcomeStatus.VALID or type(parsed.value) is not dict:
        return _failure(
            "malformed_artifact",
            "The supplied artifact is not a strict JSON object.",
            context=context,
            input_digest=input_digest,
        )
    record: dict[str, Any] = parsed.value

    if (
        not context.source_artifact_identity
        or not context.source_location
        or not context.schema_package_identity
        or context.tamc_contract_version != TAMC_CONTRACT_VERSION
    ):
        return _failure(
            "required_provenance_failed",
            "Explicit source, package, and TAMC-001/1.0 context is required.",
            context=context,
            input_digest=input_digest,
            record=record,
        )

    try:
        registry = build_offline_registry(context.package_root)
    except (OSError, SchemaRegistryError, ValueError):
        return _failure(
            "registry_failure",
            "The explicit offline Stage 3 registry could not be built.",
            context=context,
            input_digest=input_digest,
            record=record,
        )

    try:
        manifest = load_and_verify_manifest(
            context.manifest_path,
            package_root=context.package_root,
            registry=registry,
            manifest_schema_id=context.manifest_schema_id,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    except (OSError, ManifestIntegrityError, SchemaRegistryError, ValueError):
        return _failure(
            "manifest_failure",
            "The explicit Stage 3 manifest failed frozen integrity verification.",
            context=context,
            input_digest=input_digest,
            record=record,
        )

    family = record.get("record_type")
    if type(family) is not str or family not in _MODEL_BY_FAMILY:
        return _failure(
            "unknown_record_family",
            "The declared record family is not supported by TAMC-001/1.0.",
            context=context,
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
            context=context,
            input_digest=input_digest,
            record=record,
        )
    manifest_entry = manifest_entries[0]

    schema_version = record.get("schema_version")
    if schema_version != SUPPORTED_SCHEMA_VERSION or manifest_entry.get("schema_version") != schema_version:
        return _failure(
            "unsupported_schema_version",
            "The declared schema version is not the frozen supported version.",
            context=context,
            input_digest=input_digest,
            record=record,
        )
    model_version = record.get("contract_version")
    if model_version != SUPPORTED_MODEL_VERSION:
        return _failure(
            "unsupported_model_version",
            "The declared typed-model contract version is not supported.",
            context=context,
            input_digest=input_digest,
            record=record,
        )

    schema_id = record.get("schema_id")
    if schema_id != manifest_entry.get("schema_id"):
        return _failure(
            "family_identity_mismatch",
            "The declared family, record type, and schema identity do not agree.",
            context=context,
            input_digest=input_digest,
            record=record,
        )
    try:
        resource_info = registry.resource_info(schema_id)
    except SchemaRegistryError:
        return _failure(
            "registry_entry_missing",
            "The explicit offline registry has no entry for the declared schema identity.",
            context=context,
            input_digest=input_digest,
            record=record,
        )

    shape_result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    if shape_result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE:
        return _failure(
            "registry_failure",
            "The offline registry could not resolve the declared schema graph.",
            context=context,
            input_digest=input_digest,
            record=record,
        )
    if shape_result.status is not OutcomeStatus.VALID:
        return _failure(
            "schema_validation_failed",
            "The record does not conform to its frozen Draft 2020-12 schema.",
            context=context,
            input_digest=input_digest,
            record=record,
        )

    model_class = _MODEL_BY_FAMILY[family]
    try:
        model = model_class.from_dict(record, schema_version=schema_version)
        typed_wire = model.to_dict()
    except (TypedModelError, TypeError, ValueError):
        return _failure(
            "model_validation_failed",
            "The record could not be constructed by its frozen typed model.",
            context=context,
            input_digest=input_digest,
            record=record,
        )

    if typed_wire != record:
        return _failure(
            "required_provenance_failed",
            "The frozen typed-model round trip did not preserve the complete record.",
            context=context,
            input_digest=input_digest,
            record=record,
        )

    required = ("record_id", "record_digest", "schema_id", "schema_version", "contract_version")
    if any(type(typed_wire.get(key)) is not str or not typed_wire[key] for key in required):
        return _failure(
            "required_provenance_failed",
            "Required record identity, version, or digest provenance is unavailable.",
            context=context,
            input_digest=input_digest,
            record=record,
        )

    return InspectionSuccess(
        source_artifact_identity=context.source_artifact_identity,
        source_location=context.source_location,
        schema_package_identity=context.schema_package_identity,
        input_digest=input_digest,
        record_family=family,
        record_identity=typed_wire["record_id"],
        schema_identity=schema_id,
        schema_version=schema_version,
        model_version=model_version,
        declared_record_digest=typed_wire["record_digest"],
        manifest_entry=OpaqueJsonValue.from_json(manifest_entry),
        registry_resource=OpaqueJsonValue.from_json(
            {
                "schema_id": resource_info.schema_id,
                "relative_path": resource_info.relative_path,
                "sha256": resource_info.sha256,
                "size_bytes": resource_info.size_bytes,
            }
        ),
        schema_validation=OpaqueJsonValue.from_json(
            {"status": "shape_conformant", "schema_id": shape_result.schema_id, "issues": []}
        ),
        model_validation=OpaqueJsonValue.from_json(
            {"status": "constructed_and_losslessly_serialized", "model": model_class.__name__}
        ),
        record_claims=OpaqueJsonValue.from_json(typed_wire),
        provenance=_provenance_bundle(
            typed_wire,
            context=context,
            input_digest=input_digest,
        ),
    )


__all__ = [
    "CONSUMER_ID",
    "ExplicitArtifactContext",
    "InspectionFailure",
    "InspectionResult",
    "InspectionSuccess",
    "MANIFEST_SCHEMA_ID",
    "REPRESENTATION_ONLY_DISCLOSURE",
    "TAMC_CONTRACT_VERSION",
    "UNAVAILABLE",
    "inspect_explicit_artifact",
]
