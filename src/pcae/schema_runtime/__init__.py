"""Generic Draft 2020-12 schema-validation infrastructure (Phase 136F).

Prerequisite infrastructure only, in preparation for Stage 3 companion
executable schema authoring (CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0).
This package implements no Stage 3 record schema, typed model, semantic
validator, authority resolver, or authority state. Legacy lifecycle
remains the sole production authority; CLTR remains derivative.
"""
from __future__ import annotations

from .errors import (
    ERROR_CODES,
    SchemaRegistryError,
    SchemaResourceError,
    SchemaResourceNotFoundError,
    SchemaRuntimeError,
)
from .json_parser import parse_strict_json
from .limits import (
    DEFAULT_MAX_INPUT_BYTES,
    DEFAULT_MAX_ISSUE_COUNT,
    DEFAULT_MAX_NESTING_DEPTH,
    DEFAULT_MAX_RECORD_DEPTH,
    DEFAULT_MAX_REGISTRY_RESOURCES,
    DEFAULT_MAX_SCHEMA_RESOURCE_BYTES,
)
from .loader import (
    LoadedSchemaResource,
    discover_schema_files,
    load_schema_package,
    load_schema_resource,
)
from .manifest import (
    ManifestIntegrityError,
    VerifiedManifest,
    VerifiedManifestEntry,
    load_and_verify_manifest,
)
from .models import (
    JsonParseResult,
    OutcomeStatus,
    SchemaResourceInfo,
    ShapeValidationResult,
    ValidationIssue,
)
from .registry import SchemaRegistry, build_offline_registry
from .validation import validate_record_shape

__all__ = [
    "ERROR_CODES",
    "SchemaRuntimeError",
    "SchemaResourceError",
    "SchemaResourceNotFoundError",
    "SchemaRegistryError",
    "parse_strict_json",
    "DEFAULT_MAX_INPUT_BYTES",
    "DEFAULT_MAX_ISSUE_COUNT",
    "DEFAULT_MAX_NESTING_DEPTH",
    "DEFAULT_MAX_RECORD_DEPTH",
    "DEFAULT_MAX_REGISTRY_RESOURCES",
    "DEFAULT_MAX_SCHEMA_RESOURCE_BYTES",
    "LoadedSchemaResource",
    "discover_schema_files",
    "load_schema_package",
    "load_schema_resource",
    "ManifestIntegrityError",
    "VerifiedManifest",
    "VerifiedManifestEntry",
    "load_and_verify_manifest",
    "JsonParseResult",
    "OutcomeStatus",
    "SchemaResourceInfo",
    "ShapeValidationResult",
    "ValidationIssue",
    "SchemaRegistry",
    "build_offline_registry",
    "validate_record_shape",
]
