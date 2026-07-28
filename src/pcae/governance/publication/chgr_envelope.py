"""CHGR schema-envelope construction utilities (Phase 146G; CHGR-001 §26,
CHGR-REQ-194, CHGR-REQ-204/205).

Loads the packaged, offline CHGR schema registry and manifest exactly
once (module-level cache -- 146F §4.2 point 2's "built once" guidance),
reusing ``schema_runtime``'s already-generic infrastructure unchanged
(``build_offline_registry``, ``load_and_verify_manifest``,
``validate_record_shape``) -- the same machinery
``src/pcae/governance/inspection.py`` already uses to inspect CHGR
artifacts, pointed at the same packaged ``chgr_root()``. No new
manifest-parsing or schema-loading code is added by this module.
"""
from __future__ import annotations

import functools
from datetime import datetime, timezone
from typing import Any, Dict

from pcae.governance.publication.errors import ChgrSchemaConformanceError
from pcae.schema_resources import chgr_root
from pcae.schema_runtime import (
    VerifiedManifest,
    build_offline_registry,
    validate_record_shape,
)
from pcae.schema_runtime import load_and_verify_manifest as _load_and_verify_manifest
from pcae.schema_runtime.registry import SchemaRegistry

_MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/chgr/manifest.schema.json"

RECORD_FAMILIES = (
    "human_governance_record",
    "human_confirmation_evidence",
    "governance_record_provenance",
    "governance_record_integrity",
)


class ChgrManifestLookupError(ChgrSchemaConformanceError):
    """A record family required by this construction path has no exactly-
    one entry in the verified CHGR manifest -- a construction-time
    failure (146F §3.1), never a silently-omitted envelope field."""


@functools.lru_cache(maxsize=1)
def _load_chgr_schema_context() -> tuple[SchemaRegistry, VerifiedManifest]:
    with chgr_root() as package_root:
        registry = build_offline_registry(package_root)
        manifest = _load_and_verify_manifest(
            package_root / "manifest.json",
            package_root=package_root,
            registry=registry,
            manifest_schema_id=_MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    return registry, manifest


def chgr_schema_registry() -> SchemaRegistry:
    """The offline-verified CHGR schema registry, built once and reused
    (CHGR-REQ-204/205's fail-closed gate validates against this)."""

    registry, _manifest = _load_chgr_schema_context()
    return registry


def _manifest_entry_for(record_family: str) -> Dict[str, Any]:
    _registry, manifest = _load_chgr_schema_context()
    matches = [
        entry
        for entry in manifest.document["entries"]
        if entry.get("family") == record_family and entry.get("file_path", "").startswith("records/")
    ]
    if len(matches) != 1:
        raise ChgrManifestLookupError(
            f"Expected exactly one manifest entry for CHGR record family {record_family!r}, "
            f"found {len(matches)}."
        )
    return matches[0]


def chgr_timestamp(value: str) -> str:
    """Normalize an ISO-8601 timestamp to the CHGR envelope's required
    literal ``Z``-suffixed shape, preserving the UTC instant unchanged
    (146F Risk R-3): every ``_now_iso()`` helper in this repository emits
    a ``+00:00``-suffixed string, never ``Z``, which
    ``envelope.schema.json#/$defs/timestamp`` rejects. This is a
    serialization-format normalization only, never a content
    re-derivation (compatible with PEC-REQ-113: the represented instant
    in time is unchanged, only its string encoding)."""

    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def envelope_for(record_family: str, record_id: str, created_at: str) -> Dict[str, Any]:
    """Build the six of the seven universal ``chgr_envelope`` fields
    (``shared/envelope.schema.json``) that do not depend on the artifact's
    own finalized content -- ``record_digest`` is intentionally omitted;
    the caller fills it in last, after every other field is finalized
    (146F §3.2's "digest computed last" sequencing note). ``schema_id``/
    ``schema_version``/``contract_version`` are read verbatim from the
    verified manifest -- never hardcoded independently (CHGR-REQ-194)."""

    if record_family not in RECORD_FAMILIES:
        raise ChgrManifestLookupError(f"Unknown CHGR record family: {record_family!r}")
    entry = _manifest_entry_for(record_family)
    _registry, manifest = _load_chgr_schema_context()
    return {
        "schema_id": entry["schema_id"],
        "schema_version": entry["schema_version"],
        "contract_version": manifest.document["contract_version"],
        "record_type": record_family,
        "record_id": record_id,
        "created_at": chgr_timestamp(created_at),
    }


def validate_chgr_artifact(artifact: Dict[str, Any]):
    """Thin wrapper over ``schema_runtime.validate_record_shape``,
    dispatching on the artifact's own already-manifest-sourced
    ``schema_id`` -- no separately hardcoded schema-id table (CHGR-REQ-194's
    "never hardcoded independently elsewhere" restated for validation
    dispatch)."""

    return validate_record_shape(artifact, schema_id=artifact["schema_id"], registry=chgr_schema_registry())


__all__ = [
    "ChgrManifestLookupError",
    "RECORD_FAMILIES",
    "chgr_schema_registry",
    "chgr_timestamp",
    "envelope_for",
    "validate_chgr_artifact",
]
