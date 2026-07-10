"""Cross-Artifact Knowledge Integration deterministic construction (130D pipeline).

Consumes existing, already-verified Repository Intelligence artifacts --
a Change Impact Report and a Dependency Knowledge Graph Snapshot are
required; a Repository Knowledge Snapshot, a Historical Memory
Snapshot, and an Advisory Intelligence Context Package are optional,
read-only reference inputs (130D Section 3). Produces a derivative,
read-only integrated knowledge package: references only, never new
knowledge (130B Section 1/130D Section 4).

Per 130C's own independent discovery and 130D's explicit strategic
decision, this builder does not invent a new schema structure for its
primary relationship category. Change Impact's own frozen executable
schema (119U) already declares a ``dependency_context_reference``
shape (``context_id``/``context_type``/``reference_locator``/
``source_attribution``/``limitations``) with ``context_type`` already
including ``"graph_node"``/``"graph_edge"``. This builder populates
that existing shape rather than defining a parallel one (130D Section
6's "architectural simplification").

No relationship is created without direct, deterministic support via
an already-existing stable identifier on both endpoints (130B Section
5 / 130D Section 12). No fuzzy matching, no probabilistic matching, no
heuristic matching, no silent merges. This module never imports
``subprocess`` -- consistent with every non-``git_source.py`` module in
this package family.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pcae.repository_intelligence.attribution import (
    limitation_record,
    source_attribution_record,
)
from pcae.repository_intelligence.dependency_graph.graph_builder import (
    _node_id_for_entity,
)
from pcae.repository_intelligence.query.snapshot_loader import (
    SnapshotCompatibilityError,
    SnapshotLoadError,
    load_snapshot,
)

ARTIFACT_CONTRACT_VERSION = "119E.1.0"
SCHEMA_CONCEPT_VERSION = "119C.1.0-concept"

DKG_EXECUTABLE_SCHEMA_VERSION = "119S.1.0-json-schema"

INTEGRATION_PACKAGE_DISCLAIMER = (
    "This Cross-Artifact Knowledge Integration Package is a derivative, "
    "read-only reference layer over existing Repository Intelligence "
    "artifacts. It creates no new repository knowledge, performs no "
    "reasoning, inference, ranking, or Decision Evaluation, and never "
    "supersedes the authority of any source artifact it references. "
    "Human approval remains unchanged."
)

BOUNDARY_DISCLOSURES = {
    "read_only": True,
    "no_execution": True,
    "non_decision": True,
    "advisory_non_authority": True,
    "decision_evaluation_required": True,
    "no_repository_mutation": True,
    "no_lifecycle_mutation": True,
    "no_evidence_replacement": True,
    "no_repository_state_replacement": True,
}

# 130D Section 15 / 130C Finding (130C Section 11): "derivative nature"
# and "human approval unchanged" have no dedicated boundary_disclosure
# schema field -- expressed here via the existing free-text
# boundary_notes array rather than inventing a new schema field.
BOUNDARY_NOTES = [
    "This package is derivative: it contains references only and never "
    "becomes an independent evidence source.",
    "This package does not alter, bypass, or replace human approval "
    "authority.",
]

_INTEGRATION_SCOPE_LIMITATION = (
    "This Cross-Artifact Knowledge Integration prototype v1 implements "
    "exactly one relationship category: Change Impact affected/impacted "
    "entities referenced against Dependency Knowledge Graph nodes, "
    "resolved only via each Dependency Knowledge Graph node's own "
    "deterministic identifier formula applied to the entity path already "
    "present on each Change Impact impacted entity. Repository Knowledge "
    "Snapshot, Historical Memory, and Advisory Context are consumed, "
    "where supplied, only as cited reference artifacts -- no relationship "
    "is derived to or from them in this prototype. This is an intentional "
    "scope boundary (130D Section 2/6), not a builder defect."
)


class IntegrationGenerationError(RuntimeError):
    """Raised when the Cross-Artifact Knowledge Integration Builder must fail closed."""


def _load_json_artifact(path: Path, label: str) -> dict[str, Any]:
    """Load an arbitrary Repository Intelligence artifact JSON file.

    Generic, artifact-shape-agnostic loading only (file exists, is
    valid JSON, root is an object). Artifact-specific compatibility
    checks (schema version, required fields) are the caller's
    responsibility -- mirrors ``load_snapshot``'s own two-stage design
    (``query.snapshot_loader``) without assuming every consumed
    artifact shares Repository Knowledge Snapshot's own envelope shape
    (Change Impact's real prototype output does not: 130D's own
    grounding confirmed it has no ``snapshot_identity``/``envelope``
    field at all).
    """
    if not path.is_file():
        raise IntegrationGenerationError(f"{label} not found: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise IntegrationGenerationError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise IntegrationGenerationError(f"{label} JSON root must be an object: {path}")
    return data


def _load_dependency_graph(path: Path) -> dict[str, Any]:
    try:
        graph = load_snapshot(path)
    except (SnapshotLoadError, SnapshotCompatibilityError):
        # load_snapshot's own compatibility check is Repository
        # Knowledge Snapshot-specific (119O); re-load generically and
        # apply the Dependency Knowledge Graph's own version check
        # below instead of trusting an RKS-shaped error message.
        graph = _load_json_artifact(path, "Dependency Knowledge Graph")
    identity = graph.get("snapshot_identity")
    if not isinstance(identity, dict):
        raise IntegrationGenerationError("Dependency Knowledge Graph snapshot_identity is missing or invalid")
    version = identity.get("executable_schema_version")
    if version != DKG_EXECUTABLE_SCHEMA_VERSION:
        raise IntegrationGenerationError(
            f"unsupported Dependency Knowledge Graph executable schema version: {version!r}"
        )
    if not isinstance(graph.get("nodes"), list):
        raise IntegrationGenerationError("Dependency Knowledge Graph is missing required field: nodes")
    return graph


def _load_change_impact_report(path: Path) -> dict[str, Any]:
    report = _load_json_artifact(path, "Change Impact Report")
    if not isinstance(report.get("impacted_entities"), list):
        raise IntegrationGenerationError("Change Impact Report is missing required field: impacted_entities")
    if not isinstance(report.get("limitation_bundle"), list) or not report.get("limitation_bundle"):
        raise IntegrationGenerationError("Change Impact Report is missing required limitations")
    if not isinstance(report.get("boundary_disclosure_bundle"), dict) or not report.get(
        "boundary_disclosure_bundle"
    ):
        raise IntegrationGenerationError("Change Impact Report is missing required boundary disclosures")
    return report


def _dependency_context_reference(
    *,
    context_id: str,
    context_type: str,
    reference_locator_type: str,
    reference_locator_value: str,
    dkg_artifact_id: str,
    dkg_path: str,
) -> dict[str, Any]:
    """A ``dependency_context_reference``-shaped dict (119U's own $def,
    reused verbatim per 130D Section 6 -- no parallel structure)."""
    source_attribution = [
        source_attribution_record(
            source_id=f"source:dependency-knowledge-graph:{dkg_artifact_id}",
            source_type="file",
            locator_type="file_path",
            locator_value=dkg_path,
            source_claim_relationship="references",
            source_support_level="direct",
            source_verification_state="verified",
            source_staleness_state="current",
            source_limitations=[
                "Node existence and identifier observed via direct read of the "
                "cited Dependency Knowledge Graph Snapshot file; graph "
                "structure was not traversed."
            ],
        )
    ]
    return {
        "context_id": context_id,
        "context_type": context_type,
        "reference_locator": {
            "locator_type": reference_locator_type,
            "locator_value": reference_locator_value,
        },
        "source_attribution": source_attribution,
        "limitations": [
            limitation_record(
                limitation_type="scope_limitation",
                limitation_description=(
                    "This reference declares that the cited Dependency "
                    "Knowledge Graph node exists and shares a deterministic "
                    "identifier derivation with the referencing Change "
                    "Impact entity. It does not assert anything about the "
                    "node's own structural relationships (edges) -- no "
                    "graph traversal was performed."
                ),
            )
        ],
    }


def _artifact_reference(
    *, artifact_type: str, artifact_id: str, executable_schema_version: str, path: str
) -> dict[str, Any]:
    return {
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "executable_schema_version": executable_schema_version,
        "source_locator": {"locator_type": "file_path", "locator_value": path},
    }


def build_integration_content(
    change_impact_path: Path,
    dependency_graph_path: Path,
    *,
    generated_at_utc: str,
    repository_knowledge_snapshot_path: Path | None = None,
    historical_memory_path: Path | None = None,
    advisory_context_path: Path | None = None,
) -> dict[str, Any]:
    """Build the deterministic Cross-Artifact Knowledge Integration package.

    Fails closed (``IntegrationGenerationError``) on any missing,
    invalid, or incompatible required source artifact. Optional
    reference artifacts (Repository Knowledge Snapshot, Historical
    Memory, Advisory Context), if supplied, must themselves be valid
    or generation fails closed -- but their absence alone is not an
    error (130D Section 3's own "where appropriate" scoping).
    """
    change_impact = _load_change_impact_report(change_impact_path)
    dkg = _load_dependency_graph(dependency_graph_path)

    dkg_identity = dkg["snapshot_identity"]
    dkg_artifact_id = dkg_identity.get("snapshot_id", "unknown")
    node_by_id = {
        node["node_id"]: node
        for node in dkg["nodes"]
        if isinstance(node, dict) and node.get("node_id")
    }

    referenced_artifacts: list[dict[str, Any]] = [
        _artifact_reference(
            artifact_type="dependency_knowledge_graph_snapshot",
            artifact_id=dkg_artifact_id,
            executable_schema_version=dkg_identity.get("executable_schema_version", "unknown"),
            path=str(dependency_graph_path),
        ),
        _artifact_reference(
            artifact_type="change_impact_report",
            artifact_id=change_impact.get("report_metadata", {}).get(
                "assembly_timestamp", "unknown"
            ),
            executable_schema_version="not_applicable_prototype_shape",
            path=str(change_impact_path),
        ),
    ]

    optional_inputs = (
        (repository_knowledge_snapshot_path, "repository_knowledge_snapshot"),
        (historical_memory_path, "historical_memory_snapshot"),
        (advisory_context_path, "advisory_intelligence_context_package"),
    )
    for opt_path, artifact_type in optional_inputs:
        if opt_path is None:
            continue
        artifact = _load_json_artifact(opt_path, artifact_type)
        identity = artifact.get("snapshot_identity") or {}
        if not isinstance(identity, dict) or not identity:
            raise IntegrationGenerationError(
                f"{artifact_type} at {opt_path} is missing snapshot_identity"
            )
        referenced_artifacts.append(
            _artifact_reference(
                artifact_type=artifact_type,
                artifact_id=identity.get("snapshot_id", "unknown"),
                executable_schema_version=identity.get(
                    "executable_schema_version", "unknown"
                ),
                path=str(opt_path),
            )
        )

    dependency_context: list[dict[str, Any]] = []
    entity_resolutions: list[dict[str, Any]] = []
    unresolved_identities: list[dict[str, Any]] = []

    for entity in change_impact["impacted_entities"]:
        if not isinstance(entity, dict):
            continue
        entity_id = entity.get("entity_id")
        entity_path = entity.get("entity_path")
        if not entity_id:
            continue
        if not entity_path:
            unresolved_identities.append(
                {
                    "entity_id": entity_id,
                    "uncertainty_state": "unresolved",
                    "unresolved_reason": (
                        "Change Impact impacted entity has no entity_path; "
                        "the Dependency Knowledge Graph node identifier "
                        "formula requires one and none is available."
                    ),
                }
            )
            continue

        candidate_node_id = _node_id_for_entity(entity_path)
        node = node_by_id.get(candidate_node_id)
        if node is None:
            unresolved_identities.append(
                {
                    "entity_id": entity_id,
                    "uncertainty_state": "unresolved",
                    "unresolved_reason": (
                        f"No Dependency Knowledge Graph node with identifier "
                        f"{candidate_node_id!r} exists in the referenced graph "
                        "snapshot; identity is not merged, guessed, or "
                        "fuzzy-matched."
                    ),
                }
            )
            continue

        context_id = f"context:graph-node:{node['node_id']}"
        dependency_context.append(
            _dependency_context_reference(
                context_id=context_id,
                context_type="graph_node",
                reference_locator_type="file_path",
                reference_locator_value=entity_path,
                dkg_artifact_id=dkg_artifact_id,
                dkg_path=str(dependency_graph_path),
            )
        )
        entity_resolutions.append(
            {
                "entity_id": entity_id,
                "dependency_context_reference": context_id,
                "resolved_node_id": node["node_id"],
            }
        )

    limitations = [
        limitation_record(
            limitation_type="scope_limitation",
            limitation_description=_INTEGRATION_SCOPE_LIMITATION,
        )
    ]

    integration: dict[str, Any] = {
        "integration_metadata": {
            "integration_configuration": "change_impact_dependency_graph_v1",
            "generated_at_utc": generated_at_utc,
            "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
            "schema_concept_version": SCHEMA_CONCEPT_VERSION,
        },
        "referenced_artifacts": sorted(
            referenced_artifacts, key=lambda ref: ref["artifact_id"]
        ),
        "dependency_context": sorted(
            dependency_context, key=lambda ctx: ctx["context_id"]
        ),
        "entity_resolutions": sorted(
            entity_resolutions, key=lambda item: item["entity_id"]
        ),
        "unresolved_identities": sorted(
            unresolved_identities, key=lambda item: item["entity_id"]
        ),
        "limitations": limitations,
        "boundary_disclosures": dict(BOUNDARY_DISCLOSURES),
        "boundary_notes": list(BOUNDARY_NOTES),
        "cross_artifact_integration_package_disclaimer": INTEGRATION_PACKAGE_DISCLAIMER,
    }
    return integration
