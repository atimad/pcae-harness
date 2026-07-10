"""Cross-Artifact Knowledge Integration validation (130D pipeline).

Fail-closed structural validation of a constructed integration
package before persistence, mirroring the established pattern in
``historical_validation.py`` / DKG's own validation checks: reject
missing provenance, missing limitations, missing boundary disclosures,
duplicate identifiers, and invalid references -- never silently drop
or repair them.
"""

from __future__ import annotations

from typing import Any

from pcae.repository_intelligence.cross_artifact_integration.integration_builder import (
    IntegrationGenerationError,
)


def validate_integration_package(integration: dict[str, Any]) -> None:
    _validate_top_level_fields(integration)
    _validate_referenced_artifacts(integration)
    _validate_dependency_context(integration)
    _validate_deterministic_ordering(integration)
    _validate_limitations_present(integration)
    _validate_boundary_disclosures_present(integration)


def _validate_top_level_fields(integration: dict[str, Any]) -> None:
    required = (
        "integration_metadata",
        "referenced_artifacts",
        "dependency_context",
        "entity_resolutions",
        "unresolved_identities",
        "limitations",
        "boundary_disclosures",
        "boundary_notes",
        "cross_artifact_integration_package_disclaimer",
    )
    missing = [field for field in required if field not in integration]
    if missing:
        raise IntegrationGenerationError(
            "integration package is missing required top-level field(s): "
            + ", ".join(missing)
        )


def _validate_referenced_artifacts(integration: dict[str, Any]) -> None:
    refs = integration["referenced_artifacts"]
    if not refs:
        raise IntegrationGenerationError(
            "integration package declares zero referenced_artifacts; "
            "a derivative package must reference at least one source artifact"
        )
    ids = [ref["artifact_id"] for ref in refs]
    if len(ids) != len(set(ids)):
        raise IntegrationGenerationError("referenced_artifacts contains duplicate artifact_id values")


def _validate_dependency_context(integration: dict[str, Any]) -> None:
    contexts = integration["dependency_context"]
    context_ids = [ctx["context_id"] for ctx in contexts]
    if len(context_ids) != len(set(context_ids)):
        raise IntegrationGenerationError("dependency_context contains duplicate context_id values")

    referenced_context_ids = {
        item["dependency_context_reference"] for item in integration["entity_resolutions"]
    }
    if not referenced_context_ids.issubset(set(context_ids)):
        raise IntegrationGenerationError(
            "entity_resolutions references a dependency_context_reference "
            "that does not exist in dependency_context -- invalid cross-artifact reference"
        )

    for ctx in contexts:
        if not ctx.get("source_attribution"):
            raise IntegrationGenerationError(
                f"dependency_context entry {ctx.get('context_id')!r} is missing source_attribution"
            )
        if not ctx.get("limitations"):
            raise IntegrationGenerationError(
                f"dependency_context entry {ctx.get('context_id')!r} is missing limitations"
            )


def _validate_deterministic_ordering(integration: dict[str, Any]) -> None:
    ref_ids = [ref["artifact_id"] for ref in integration["referenced_artifacts"]]
    if ref_ids != sorted(ref_ids):
        raise IntegrationGenerationError("referenced_artifacts is not deterministically ordered by artifact_id")

    context_ids = [ctx["context_id"] for ctx in integration["dependency_context"]]
    if context_ids != sorted(context_ids):
        raise IntegrationGenerationError("dependency_context is not deterministically ordered by context_id")

    entity_ids = [item["entity_id"] for item in integration["entity_resolutions"]]
    if entity_ids != sorted(entity_ids):
        raise IntegrationGenerationError("entity_resolutions is not deterministically ordered by entity_id")

    unresolved_ids = [item["entity_id"] for item in integration["unresolved_identities"]]
    if unresolved_ids != sorted(unresolved_ids):
        raise IntegrationGenerationError("unresolved_identities is not deterministically ordered by entity_id")


def _validate_limitations_present(integration: dict[str, Any]) -> None:
    if not integration["limitations"]:
        raise IntegrationGenerationError("integration package is missing required limitations")


def _validate_boundary_disclosures_present(integration: dict[str, Any]) -> None:
    disclosures = integration["boundary_disclosures"]
    required_true_fields = (
        "read_only",
        "no_execution",
        "non_decision",
        "advisory_non_authority",
        "decision_evaluation_required",
        "no_repository_mutation",
        "no_lifecycle_mutation",
        "no_evidence_replacement",
        "no_repository_state_replacement",
    )
    missing_or_false = [
        field for field in required_true_fields if disclosures.get(field) is not True
    ]
    if missing_or_false:
        raise IntegrationGenerationError(
            "integration package boundary_disclosures missing or false for: "
            + ", ".join(missing_or_false)
        )
    if not integration["boundary_notes"]:
        raise IntegrationGenerationError("integration package is missing required boundary_notes")
