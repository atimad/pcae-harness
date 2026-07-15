"""Centrally recorded conservative limits for schema_runtime infrastructure.

Phase 136F prerequisite infrastructure. These limits bound generic
Layer-1/Layer-2 schema-validation inputs; they carry no authority
semantics and are independent of any Stage 3 record contract.
"""
from __future__ import annotations

# Maximum size, in bytes, of a single JSON document passed to the strict parser.
DEFAULT_MAX_INPUT_BYTES = 5 * 1024 * 1024

# Maximum size, in bytes, of a single schema resource file loaded from disk.
DEFAULT_MAX_SCHEMA_RESOURCE_BYTES = 1 * 1024 * 1024

# Maximum number of validation issues returned by shape validation.
DEFAULT_MAX_ISSUE_COUNT = 200

# Maximum number of schema resources accepted into a single offline registry.
DEFAULT_MAX_REGISTRY_RESOURCES = 500
