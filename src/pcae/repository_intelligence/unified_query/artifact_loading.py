"""Artifact resolution: load each covered family's own artifact read-only (131D Section 3 stage 4).

Reuses Track 121's existing ``SnapshotLoadError``/``SnapshotCompatibilityError``
exceptions (131D Section 8's plan) rather than defining new ones for
missing/incompatible artifacts. Reuses Track 121's own
``load_snapshot`` for Repository Knowledge Snapshot directly; every
other family gets a thin, additive loader in this module that performs
the same two-stage "read + validate identity/version" shape
``load_snapshot`` and ``integration_builder.py``'s own loaders already
establish -- no new persistence mechanism, no write capability
anywhere in this module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pcae.repository_intelligence.query.snapshot_loader import (
    SnapshotCompatibilityError,
    SnapshotLoadError,
)
from pcae.repository_intelligence.query.snapshot_loader import load_snapshot as _load_rks

DEPENDENCY_KNOWLEDGE_GRAPH_SCHEMA_VERSION = "119S.1.0-json-schema"
HISTORICAL_MEMORY_SCHEMA_VERSION = "119Q.1.0-json-schema"

# Change Impact and Advisory Context real generator output carries no
# executable_schema_version field at all (see load_change_impact/
# load_advisory_context docstrings). Track 130's own
# integration_builder.py already established this exact sentinel for
# Change Impact's own provenance element 4; reused here verbatim for
# both families rather than inventing a second sentinel.
NOT_APPLICABLE_PROTOTYPE_SHAPE = "not_applicable_prototype_shape"


def _read_json_artifact(path: Path, label: str) -> dict[str, Any]:
    """Generic, artifact-shape-agnostic read (mirrors ``_load_json_artifact``).

    File-existence and JSON-shape checks only; artifact-specific
    compatibility checks are each caller's own responsibility, exactly
    as ``integration_builder.py``'s own ``_load_json_artifact`` already
    documents this same two-stage division of responsibility.
    """
    if not path.is_file():
        raise SnapshotLoadError(f"{label} not found: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SnapshotLoadError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise SnapshotLoadError(f"{label} JSON root must be an object")
    return data


def load_repository_knowledge_snapshot(path: Path) -> dict[str, Any]:
    """Reuses Track 121's own ``load_snapshot`` directly -- not reimplemented."""
    return _load_rks(path)


def load_dependency_knowledge_graph(path: Path) -> dict[str, Any]:
    graph = _read_json_artifact(path, "Dependency Knowledge Graph")
    identity = graph.get("snapshot_identity")
    if not isinstance(identity, dict):
        raise SnapshotCompatibilityError("Dependency Knowledge Graph snapshot_identity is missing or invalid")
    version = identity.get("executable_schema_version")
    if version != DEPENDENCY_KNOWLEDGE_GRAPH_SCHEMA_VERSION:
        raise SnapshotCompatibilityError(
            f"unsupported Dependency Knowledge Graph executable schema version: {version!r}"
        )
    return graph


def load_historical_memory(path: Path) -> dict[str, Any]:
    snapshot = _read_json_artifact(path, "Historical Memory Snapshot")
    identity = snapshot.get("snapshot_identity")
    if not isinstance(identity, dict):
        raise SnapshotCompatibilityError("Historical Memory snapshot_identity is missing or invalid")
    version = identity.get("executable_schema_version")
    if version != HISTORICAL_MEMORY_SCHEMA_VERSION:
        raise SnapshotCompatibilityError(
            f"unsupported Historical Memory executable schema version: {version!r}"
        )
    return snapshot


def load_change_impact(path: Path) -> dict[str, Any]:
    """Validated against the real generator's output shape, not the
    frozen schema's nominal field names.

    Independently confirmed during 131E's own implementation (not
    previously documented by 130A-131D): the real Change Impact Report
    generator (``change_impact_report.py``) emits ``impacted_entities``/
    ``limitation_bundle``/``boundary_disclosure_bundle``/
    ``report_metadata`` and carries no ``report_identity`` field and no
    ``executable_schema_version`` field at all -- this diverges from
    ``change_impact_report.schema.json``'s own declared top-level field
    names (``affected_entities``/``report_limitations``/
    ``boundary_disclosures``/``report_identity``). Track 130's own
    ``integration_builder.py`` already consumes the real shape (not the
    schema's nominal one) and already uses the literal sentinel
    ``"not_applicable_prototype_shape"`` for this artifact's schema
    version in provenance -- this loader follows that same, already-
    proven precedent rather than validating a field that does not
    exist in real output. This is a genuine, pre-existing Track 123
    schema-conformance gap, out of scope to repair in this phase
    (documented as a known limitation, not modified).
    """
    report = _read_json_artifact(path, "Change Impact Report")
    if not isinstance(report.get("impacted_entities"), list):
        raise SnapshotCompatibilityError("Change Impact Report is missing required field: impacted_entities")
    if not isinstance(report.get("limitation_bundle"), list) or not report.get("limitation_bundle"):
        raise SnapshotCompatibilityError("Change Impact Report is missing required limitations")
    if not isinstance(report.get("boundary_disclosure_bundle"), dict) or not report.get(
        "boundary_disclosure_bundle"
    ):
        raise SnapshotCompatibilityError("Change Impact Report is missing required boundary disclosures")
    return report


def load_advisory_context(path: Path) -> dict[str, Any]:
    """Validated against the real builder's output shape, not the
    frozen schema's nominal field names.

    Independently confirmed during 131E's own implementation (not
    previously documented by 130A-131D): the real Advisory Context
    Builder (``context_package.py``) emits
    ``selected_repository_intelligence``/``limitation_bundle``/
    ``boundary_disclosure_bundle``/``context_metadata`` and carries no
    ``package_identity`` field and no ``executable_schema_version``
    field at all -- the same class of divergence from
    ``advisory_intelligence_context_package.schema.json``'s own
    declared top-level field names (``package_identity``/
    ``context_items``/``package_scope``) independently found for
    Change Impact above. A genuine, pre-existing Track 122
    schema-conformance gap, out of scope to repair in this phase
    (documented as a known limitation, not modified).
    """
    package = _read_json_artifact(path, "Advisory Intelligence Context Package")
    if not isinstance(package.get("selected_repository_intelligence"), list):
        raise SnapshotCompatibilityError(
            "Advisory Context package is missing required field: selected_repository_intelligence"
        )
    if not isinstance(package.get("limitation_bundle"), list) or not package.get("limitation_bundle"):
        raise SnapshotCompatibilityError("Advisory Context package is missing required limitations")
    if not isinstance(package.get("boundary_disclosure_bundle"), dict) or not package.get(
        "boundary_disclosure_bundle"
    ):
        raise SnapshotCompatibilityError("Advisory Context package is missing required boundary disclosures")
    return package


def load_cross_artifact_integration(path: Path) -> dict[str, Any]:
    """Cross-Artifact Integration packages carry no ``executable_schema_version``.

    Confirmed by direct inspection (131C Section 3.1 / 131E's own
    grounding): the package reuses Change Impact's own frozen
    ``dependency_context_reference`` shape rather than declaring an
    independent artifact schema, so there is no version field to check
    here beyond structural presence of the package's own required
    keys.
    """
    package = _read_json_artifact(path, "Cross-Artifact Integration Package")
    if not isinstance(package.get("integration_metadata"), dict):
        raise SnapshotCompatibilityError(
            "Cross-Artifact Integration Package integration_metadata is missing or invalid"
        )
    return package
