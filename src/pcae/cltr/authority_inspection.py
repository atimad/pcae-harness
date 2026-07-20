"""Production Typed Authority Model consumer: explicit-artifact inspection.

Implements TAMPC-001 v1.0 (`docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`)
per the Phase 137J implementation plan
(`docs/IMPLEMENTATION_PLAN_TYPED_AUTHORITY_MODEL_CONSUMER.md`). This module
is the sole owner of the validation pipeline behind ``pcae authority
inspect <path>`` (`src/pcae/commands/authority_inspect.py`): parsing,
package-owned Stage 3 resource resolution, manifest/registry verification,
family/version/identity resolution, schema validation, typed-model
construction, immutable observation construction, and provenance assembly.

This module performs no CLI argument parsing, no rendering, no lifecycle
mutation, no authority resolution or activation, no runtime-capability
decision, no notification dispatch, and no repository discovery. It reads
only the explicitly supplied artifact bytes handed to it by the CLI layer
and installed package resources via ``pcae.schema_resources.cltr_cutover_root()``.

Every successful inspection is a representation-only observation: it does
not prove authority, authorization, lifecycle completion, publication,
certification effectiveness, runtime permission, execution permission,
cutover approval, recovery permission, or semantic truth.
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
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import (
    ManifestIntegrityError,
    OutcomeStatus,
    SchemaRegistryError,
    build_offline_registry,
    load_and_verify_manifest,
    parse_strict_json,
    validate_record_shape,
)

CONSUMER_ID = "pcae-authority-inspect-v1"
TAMPC_CONTRACT_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSION = "1.0"
SUPPORTED_MODEL_VERSION = "1.0"
MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/manifest.schema.json"
REPRESENTATION_ONLY_DISCLOSURE = (
    "This inspection describes a representation only; it does not prove "
    "authority, authorization, lifecycle completion, publication, "
    "certification effectiveness, runtime permission, execution "
    "permission, cutover approval, recovery permission, or semantic "
    "truth. Governed lifecycle semantics remain authoritative; execution "
    "is unavailable."
)
UNAVAILABLE = "unavailable"

# Static, module-private family dispatch. No plugin registry, no dynamic
# import based on artifact content (TAMPC-REQ-008, TAMPC-REQ-055).
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
class InspectionObservation:
    """Immutable, provenance-complete observation of one representation.

    Ordinary attribute assignment/deletion is rejected by ``frozen=True``,
    which raises ``dataclasses.FrozenInstanceError`` from its own generated
    ``__setattr__``/``__delattr__`` (TAMPC-REQ-078). This does not, and is
    not claimed to, defeat a caller who deliberately invokes
    ``object.__setattr__`` — that residual bypass is out of TAMPC-001's
    threat model and is not required to be defeated.
    """

    source_artifact_identity: str
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
    tampc_contract_version: str = TAMPC_CONTRACT_VERSION
    outcome: Literal["inspected"] = "inspected"

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "consumer_identity": self.consumer_identity,
            "tampc_contract_version": self.tampc_contract_version,
            "source_artifact_identity": self.source_artifact_identity,
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
    """Stable fail-closed result. No partial inspection success exists."""

    outcome: str
    message: str
    source_artifact_identity: str
    input_digest: str
    record_family: str = UNAVAILABLE
    schema_identity: str = UNAVAILABLE
    schema_version: str = UNAVAILABLE
    model_version: str = UNAVAILABLE
    disclosure: str = REPRESENTATION_ONLY_DISCLOSURE
    consumer_identity: str = CONSUMER_ID
    tampc_contract_version: str = TAMPC_CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "message": self.message,
            "consumer_identity": self.consumer_identity,
            "tampc_contract_version": self.tampc_contract_version,
            "source_artifact_identity": self.source_artifact_identity,
            "input_digest": self.input_digest,
            "record_family": self.record_family,
            "schema_identity": self.schema_identity,
            "schema_version": self.schema_version,
            "model_version": self.model_version,
            "disclosure": self.disclosure,
        }

    def to_canonical_bytes(self) -> bytes:
        return to_canonical_bytes(self.to_dict())


InspectionOutcome = Union[InspectionObservation, InspectionFailure]

# Public failure identifiers, in TAMPC-001 §17 precedence order (informative
# only — actual precedence is enforced by the pipeline's early-return order
# in ``inspect_artifact_at_path``, not by this tuple).
FAILURE_IDENTIFIERS = (
    "input_not_found",
    "input_not_a_file",
    "input_unreadable",
    "malformed_artifact",
    "registry_failure",
    "manifest_failure",
    "unknown_record_family",
    "manifest_entry_missing",
    "unsupported_schema_version",
    "unsupported_model_version",
    "family_identity_mismatch",
    "registry_entry_missing",
    "schema_validation_failed",
    "model_validation_failed",
    "required_provenance_failed",
)


def _safe_text(value: object) -> str:
    return value if type(value) is str and value else UNAVAILABLE


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
        model_version=_safe_text(record.get("contract_version")),
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
    source_artifact_identity: str,
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
            "source_artifact_identity": source_artifact_identity,
            "consumer_identity": CONSUMER_ID,
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


def inspect_artifact_at_path(
    path: Path, *, artifact_bytes: bytes, json_output: bool = False
) -> InspectionOutcome:
    """Inspect one caller-supplied artifact and return exactly one outcome.

    ``path`` is the caller-supplied path identity (used only as a display
    identity, never re-read by this function). ``artifact_bytes`` is the
    exact bytes already read by the CLI layer's bounded read (Stage 1,
    owned by ``authority_inspect.py``); this function owns every stage
    from parsing onward and performs no filesystem I/O of its own beyond
    the package-owned Stage 3 resource resolution below. ``json_output``
    selects nothing about the returned value's content (TAMPC-REQ-105
    requires human/JSON field parity); it is accepted for signature
    compatibility with a future internal caller and is otherwise inert.

    Failure precedence: parse -> resource resolution -> manifest -> family/
    version/identity dispatch -> registry entry -> schema -> model ->
    lossless round trip -> required-field presence. No stage retries,
    repairs, falls back, or performs an external side effect.
    """

    del json_output  # accepted-but-inert per TAMPC-REQ-023 (Section 5)
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

    try:
        with cltr_cutover_root() as package_root:
            try:
                registry = build_offline_registry(package_root)
            except (OSError, SchemaRegistryError, ValueError):
                return _failure(
                    "registry_failure",
                    "The installed offline Stage 3 registry could not be built.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            try:
                manifest = load_and_verify_manifest(
                    package_root / "manifest.json",
                    package_root=package_root,
                    registry=registry,
                    manifest_schema_id=MANIFEST_SCHEMA_ID,
                    excluded_relative_paths=frozenset({"manifest.schema.json"}),
                )
            except (OSError, ManifestIntegrityError, SchemaRegistryError, ValueError):
                return _failure(
                    "manifest_failure",
                    "The installed Stage 3 manifest failed frozen integrity verification.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            family = record.get("record_type")
            if type(family) is not str or family not in _MODEL_BY_FAMILY:
                return _failure(
                    "unknown_record_family",
                    "The declared record family is not supported by TAMPC-001/1.0.",
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

            schema_version = record.get("schema_version")
            if schema_version != SUPPORTED_SCHEMA_VERSION or manifest_entry.get("schema_version") != schema_version:
                return _failure(
                    "unsupported_schema_version",
                    "The declared schema version is not the frozen supported version.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )
            model_version = record.get("contract_version")
            if model_version != SUPPORTED_MODEL_VERSION:
                return _failure(
                    "unsupported_model_version",
                    "The declared typed-model contract version is not supported.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            schema_id = record.get("schema_id")
            if schema_id != manifest_entry.get("schema_id"):
                return _failure(
                    "family_identity_mismatch",
                    "The declared family, record type, and schema identity do not agree.",
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
                    "The record does not conform to its frozen Draft 2020-12 schema.",
                    source_artifact_identity=source_artifact_identity,
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
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            if typed_wire != record:
                return _failure(
                    "required_provenance_failed",
                    "The frozen typed-model round trip did not preserve the complete record.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            required = ("record_id", "record_digest", "schema_id", "schema_version", "contract_version")
            if any(type(typed_wire.get(key)) is not str or not typed_wire[key] for key in required):
                return _failure(
                    "required_provenance_failed",
                    "Required record identity, version, or digest provenance is unavailable.",
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                    record=record,
                )

            return InspectionObservation(
                source_artifact_identity=source_artifact_identity,
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
                    source_artifact_identity=source_artifact_identity,
                    input_digest=input_digest,
                ),
            )
    except OSError:
        return _failure(
            "registry_failure",
            "The installed Stage 3 package resources could not be resolved.",
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
            record=record,
        )


__all__ = [
    "CONSUMER_ID",
    "FAILURE_IDENTIFIERS",
    "InspectionFailure",
    "InspectionObservation",
    "InspectionOutcome",
    "MANIFEST_SCHEMA_ID",
    "REPRESENTATION_ONLY_DISCLOSURE",
    "SUPPORTED_MODEL_VERSION",
    "SUPPORTED_SCHEMA_VERSION",
    "TAMPC_CONTRACT_VERSION",
    "UNAVAILABLE",
    "inspect_artifact_at_path",
]
