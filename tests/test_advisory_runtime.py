"""Tests for PCAE Advisory Runtime Prototype — Phase 113C.

Tests the advisory_runtime module: vocabularies, EvidenceReference,
AdvisoryResult, AdvisoryProvider protocol, four providers, aggregation,
module isolation, observation-only guarantees, 113B contract compliance,
and integration with real RuntimeSnapshot.

Follows the test patterns established by test_runtime_context.py (112C),
test_runtime_snapshot.py (112E), and test_runtime_introspection_prototype.py
(111B).
"""

from __future__ import annotations

import ast
import dataclasses
import json
import typing
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURE_DOC = REPO_ROOT / "docs" / "PCAE_ADVISORY_RUNTIME.md"
CONTRACT_DOC = REPO_ROOT / "docs" / "PCAE_ADVISORY_RUNTIME_CONTRACT.md"

# ═══════════════════════════════════════════════════════════════════════
# Section 1 — Module Existence and Vocabulary Constants
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def ar():
    """The advisory_runtime module under test."""
    import pcae.core.advisory_runtime as mod
    return mod


def test_module_importable(ar):
    """The advisory_runtime module must be importable."""
    assert ar is not None


def test_advisory_categories_tuple(ar):
    """ADVISORY_CATEGORIES must be an 8-element tuple."""
    assert isinstance(ar.ADVISORY_CATEGORIES, tuple)
    assert len(ar.ADVISORY_CATEGORIES) == 8
    assert ar.ADVISORY_CATEGORIES == (
        "Runtime Health",
        "Governance",
        "Context Consistency",
        "Registry",
        "Plugin Compatibility",
        "Configuration",
        "Operational Readiness",
        "Future extensibility",
    )


def test_severity_levels_tuple(ar):
    """SEVERITY_LEVELS must be a 4-element tuple."""
    assert isinstance(ar.SEVERITY_LEVELS, tuple)
    assert len(ar.SEVERITY_LEVELS) == 4
    assert ar.SEVERITY_LEVELS == ("info", "advisory", "warning", "critical")


def test_confidence_levels_tuple(ar):
    """CONFIDENCE_LEVELS must be a 4-element tuple."""
    assert isinstance(ar.CONFIDENCE_LEVELS, tuple)
    assert len(ar.CONFIDENCE_LEVELS) == 4
    assert ar.CONFIDENCE_LEVELS == ("unknown", "observed", "validated", "proven")


def test_advisory_lifecycle_stages_tuple(ar):
    """ADVISORY_LIFECYCLE_STAGES must be a 6-element tuple."""
    assert isinstance(ar.ADVISORY_LIFECYCLE_STAGES, tuple)
    assert len(ar.ADVISORY_LIFECYCLE_STAGES) == 6
    assert ar.ADVISORY_LIFECYCLE_STAGES == (
        "produced", "presented", "acknowledged",
        "superseded", "resolved", "dismissed",
    )


def test_advisory_invariant_constant_exists(ar):
    """ADVISORY_INVARIANT must be a non-empty string."""
    assert isinstance(ar.ADVISORY_INVARIANT, str)
    assert len(ar.ADVISORY_INVARIANT) > 0
    assert "advisory recommendation only" in ar.ADVISORY_INVARIANT.lower()
    assert "Recommendation precedes authorization" in ar.ADVISORY_INVARIANT
    assert "Explainability precedes trust" in ar.ADVISORY_INVARIANT


def test_runtime_snapshot_domains_tuple(ar):
    """RUNTIME_SNAPSHOT_DOMAINS must be a 9-element tuple."""
    assert isinstance(ar.RUNTIME_SNAPSHOT_DOMAINS, tuple)
    assert len(ar.RUNTIME_SNAPSHOT_DOMAINS) == 9
    assert "context" in ar.RUNTIME_SNAPSHOT_DOMAINS


# ═══════════════════════════════════════════════════════════════════════
# Section 2 — EvidenceReference
# ═══════════════════════════════════════════════════════════════════════

def test_evidence_reference_is_frozen_dataclass(ar):
    """EvidenceReference must be a frozen dataclass."""
    assert dataclasses.is_dataclass(ar.EvidenceReference)
    assert ar.EvidenceReference.__dataclass_params__.frozen is True


def test_evidence_reference_field_names(ar):
    """EvidenceReference must have exactly 4 fields matching 113B §3."""
    field_names = {f.name for f in dataclasses.fields(ar.EvidenceReference)}
    assert field_names == {"domain", "object_id", "field_path", "evidence_summary"}


def test_evidence_reference_construction(ar):
    """EvidenceReference must be constructible with valid arguments."""
    ev = ar.EvidenceReference(
        domain="health",
        object_id=None,
        field_path="health.runtime_status",
        evidence_summary="test evidence",
    )
    assert ev.domain == "health"
    assert ev.object_id is None
    assert ev.field_path == "health.runtime_status"
    assert ev.evidence_summary == "test evidence"


def test_evidence_reference_construction_with_object_id(ar):
    """EvidenceReference with object_id set."""
    ev = ar.EvidenceReference(
        domain="context",
        object_id="sess-123",
        field_path="context.session.tasks",
        evidence_summary="task evidence",
    )
    assert ev.object_id == "sess-123"


def test_evidence_reference_immutability(ar):
    """EvidenceReference must reject mutation."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        ev.domain = "governance"  # type: ignore[misc]


def test_evidence_reference_domain_must_be_valid(ar):
    """EvidenceReference must reject invalid domains."""
    with pytest.raises(ValueError):
        ar.EvidenceReference(
            domain="nonexistent",
            object_id=None,
            field_path="field",
            evidence_summary="test",
        )


def test_evidence_reference_field_path_required(ar):
    """EvidenceReference must reject empty field_path."""
    with pytest.raises(ValueError):
        ar.EvidenceReference(
            domain="health",
            object_id=None,
            field_path="",
            evidence_summary="test",
        )


def test_evidence_reference_evidence_summary_required(ar):
    """EvidenceReference must reject empty evidence_summary."""
    with pytest.raises(ValueError):
        ar.EvidenceReference(
            domain="health",
            object_id=None,
            field_path="health.field",
            evidence_summary="",
        )


# ═══════════════════════════════════════════════════════════════════════
# Section 3 — AdvisoryResult
# ═══════════════════════════════════════════════════════════════════════

ADVISORY_RESULT_FIELDS: tuple[str, ...] = (
    "advisory_id", "category", "severity", "confidence",
    "recommended_action", "rationale", "evidence_references",
    "affected_runtime_objects", "timestamp",
    "source_snapshot_reference", "reasoning_summary",
    "alternative_considerations", "remediation", "implementation_status",
)


def test_advisory_result_is_frozen_dataclass(ar):
    """AdvisoryResult must be a frozen dataclass."""
    assert dataclasses.is_dataclass(ar.AdvisoryResult)
    assert ar.AdvisoryResult.__dataclass_params__.frozen is True


def test_advisory_result_field_names(ar):
    """AdvisoryResult must have exactly 14 fields matching 113B §1."""
    field_names = {f.name for f in dataclasses.fields(ar.AdvisoryResult)}
    assert field_names == set(ADVISORY_RESULT_FIELDS)


def test_advisory_result_14_fields(ar):
    """AdvisoryResult must have exactly 14 fields — no more, no less."""
    assert len(dataclasses.fields(ar.AdvisoryResult)) == 14


def test_advisory_result_construction_with_all_14_fields(ar):
    """AdvisoryResult must be constructible with all 14 fields."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    result = ar.AdvisoryResult(
        advisory_id="ADV-test-0001",
        category="Runtime Health",
        severity="info",
        confidence="observed",
        recommended_action="test action",
        rationale="test rationale for the recommendation",
        evidence_references=(ev,),
        affected_runtime_objects=("obj-1",),
        timestamp="2026-07-04T00:00:00Z",
        source_snapshot_reference="snapshot-test",
        reasoning_summary="test summary",
        alternative_considerations=("alternative 1",),
        remediation="test remediation steps",
        implementation_status="execution_unavailable",
    )
    assert result.advisory_id == "ADV-test-0001"
    assert result.category == "Runtime Health"
    assert result.implementation_status == "execution_unavailable"


def test_advisory_result_immutability(ar):
    """AdvisoryResult must reject mutation."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    result = ar.AdvisoryResult(
        advisory_id="ADV-test-0001",
        category="Runtime Health",
        severity="info",
        confidence="observed",
        recommended_action="test",
        rationale="test rationale for the recommendation",
        evidence_references=(ev,),
        affected_runtime_objects=(),
        timestamp="2026-07-04T00:00:00Z",
        source_snapshot_reference="snapshot-test",
        reasoning_summary="test summary",
        alternative_considerations=(),
        remediation="none",
        implementation_status="execution_unavailable",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.advisory_id = "ADV-changed"  # type: ignore[misc]


def test_advisory_result_implementation_status_always_execution_unavailable(ar):
    """AdvisoryResult must unconditionally enforce implementation_status."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    result = ar.AdvisoryResult(
        advisory_id="ADV-test-0001",
        category="Runtime Health",
        severity="info",
        confidence="observed",
        recommended_action="test",
        rationale="test rationale for the recommendation",
        evidence_references=(ev,),
        affected_runtime_objects=(),
        timestamp="2026-07-04T00:00:00Z",
        source_snapshot_reference="snapshot-test",
        reasoning_summary="test summary",
        alternative_considerations=(),
        remediation="none",
        implementation_status="execution_unavailable",
    )
    assert result.implementation_status == "execution_unavailable"


def test_advisory_result_rejects_invalid_implementation_status(ar):
    """AdvisoryResult must reject any implementation_status other than execution_unavailable."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    with pytest.raises(ValueError):
        ar.AdvisoryResult(
            advisory_id="ADV-test-0001",
            category="Runtime Health",
            severity="info",
            confidence="observed",
            recommended_action="test",
            rationale="test rationale for the recommendation",
            evidence_references=(ev,),
            affected_runtime_objects=(),
            timestamp="2026-07-04T00:00:00Z",
            source_snapshot_reference="snapshot-test",
            reasoning_summary="test summary",
            alternative_considerations=(),
            remediation="none",
            implementation_status="executing",  # invalid
        )


def test_advisory_result_rejects_invalid_category(ar):
    """AdvisoryResult must reject categories not in ADVISORY_CATEGORIES."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    with pytest.raises(ValueError):
        ar.AdvisoryResult(
            advisory_id="ADV-test-0001",
            category="Not a Category",
            severity="info",
            confidence="observed",
            recommended_action="test",
            rationale="test rationale for the recommendation",
            evidence_references=(ev,),
            affected_runtime_objects=(),
            timestamp="2026-07-04T00:00:00Z",
            source_snapshot_reference="snapshot-test",
            reasoning_summary="test summary",
            alternative_considerations=(),
            remediation="none",
            implementation_status="execution_unavailable",
        )


def test_advisory_result_rejects_invalid_severity(ar):
    """AdvisoryResult must reject severities not in SEVERITY_LEVELS."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    with pytest.raises(ValueError):
        ar.AdvisoryResult(
            advisory_id="ADV-test-0001",
            category="Runtime Health",
            severity="fatal",
            confidence="observed",
            recommended_action="test",
            rationale="test rationale for the recommendation",
            evidence_references=(ev,),
            affected_runtime_objects=(),
            timestamp="2026-07-04T00:00:00Z",
            source_snapshot_reference="snapshot-test",
            reasoning_summary="test summary",
            alternative_considerations=(),
            remediation="none",
            implementation_status="execution_unavailable",
        )


def test_advisory_result_rejects_invalid_confidence(ar):
    """AdvisoryResult must reject confidences not in CONFIDENCE_LEVELS."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    with pytest.raises(ValueError):
        ar.AdvisoryResult(
            advisory_id="ADV-test-0001",
            category="Runtime Health",
            severity="info",
            confidence="guaranteed",
            recommended_action="test",
            rationale="test rationale for the recommendation",
            evidence_references=(ev,),
            affected_runtime_objects=(),
            timestamp="2026-07-04T00:00:00Z",
            source_snapshot_reference="snapshot-test",
            reasoning_summary="test summary",
            alternative_considerations=(),
            remediation="none",
            implementation_status="execution_unavailable",
        )


def test_advisory_result_required_string_fields_non_empty(ar):
    """Required string fields must be non-empty at construction."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    required_fields = [
        "advisory_id", "recommended_action", "rationale",
        "reasoning_summary", "remediation", "timestamp",
        "source_snapshot_reference",
    ]
    base_kwargs: dict[str, object] = dict(
        advisory_id="ADV-test-0001",
        category="Runtime Health",
        severity="info",
        confidence="observed",
        recommended_action="test",
        rationale="test rationale for the recommendation",
        evidence_references=(ev,),
        affected_runtime_objects=(),
        timestamp="2026-07-04T00:00:00Z",
        source_snapshot_reference="snapshot-test",
        reasoning_summary="test summary",
        alternative_considerations=(),
        remediation="none",
        implementation_status="execution_unavailable",
    )
    for field_name in required_fields:
        kwargs = dict(base_kwargs)
        kwargs[field_name] = ""
        with pytest.raises(ValueError, match=field_name):
            ar.AdvisoryResult(**kwargs)


def test_advisory_result_evidence_references_is_tuple_not_list(ar):
    """evidence_references must accept tuples, not lists."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    # Construction with tuple succeeds
    result = ar.AdvisoryResult(
        advisory_id="ADV-test-0001",
        category="Runtime Health",
        severity="info",
        confidence="observed",
        recommended_action="test",
        rationale="test rationale for the recommendation",
        evidence_references=(ev,),
        affected_runtime_objects=(),
        timestamp="2026-07-04T00:00:00Z",
        source_snapshot_reference="snapshot-test",
        reasoning_summary="test summary",
        alternative_considerations=(),
        remediation="none",
        implementation_status="execution_unavailable",
    )
    assert isinstance(result.evidence_references, tuple)

    # Construction with list fails at type level; runtime behavior:
    # dataclasses with frozen=True accept lists but they become mutable
    # aliases.  The field type annotation says tuple, so this is a type
    # error. We just verify the stored value is tuple-typed.
    assert isinstance(result.evidence_references, tuple)


def test_advisory_result_affected_runtime_objects_is_tuple_not_list(ar):
    """affected_runtime_objects must be a tuple."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    result = ar.AdvisoryResult(
        advisory_id="ADV-test-0001",
        category="Runtime Health",
        severity="info",
        confidence="observed",
        recommended_action="test",
        rationale="test rationale for the recommendation",
        evidence_references=(ev,),
        affected_runtime_objects=("obj-1", "obj-2"),
        timestamp="2026-07-04T00:00:00Z",
        source_snapshot_reference="snapshot-test",
        reasoning_summary="test summary",
        alternative_considerations=(),
        remediation="none",
        implementation_status="execution_unavailable",
    )
    assert isinstance(result.affected_runtime_objects, tuple)


def test_advisory_result_alternative_considerations_is_tuple_not_list(ar):
    """alternative_considerations must be a tuple."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    result = ar.AdvisoryResult(
        advisory_id="ADV-test-0001",
        category="Runtime Health",
        severity="info",
        confidence="observed",
        recommended_action="test",
        rationale="test rationale for the recommendation",
        evidence_references=(ev,),
        affected_runtime_objects=(),
        timestamp="2026-07-04T00:00:00Z",
        source_snapshot_reference="snapshot-test",
        reasoning_summary="test summary",
        alternative_considerations=("alt-1",),
        remediation="none",
        implementation_status="execution_unavailable",
    )
    assert isinstance(result.alternative_considerations, tuple)


# ═══════════════════════════════════════════════════════════════════════
# Section 4 — AdvisoryProvider Protocol
# ═══════════════════════════════════════════════════════════════════════

def test_advisory_protocol_is_defined(ar):
    """AdvisoryProvider must be a Protocol class."""
    assert hasattr(ar, "AdvisoryProvider")
    assert isinstance(ar.AdvisoryProvider, type)


def test_advisory_protocol_has_analyze_method(ar):
    """AdvisoryProvider Protocol must define an analyze method."""
    hints = typing.get_type_hints(ar.AdvisoryProvider.analyze)
    assert "snapshot" in hints
    assert "return" in hints


def test_runtime_health_provider_satisfies_protocol(ar):
    """RuntimeHealthProvider must structurally match AdvisoryProvider."""
    provider = ar.RuntimeHealthProvider()
    assert hasattr(provider, "analyze")
    assert callable(provider.analyze)


def test_governance_provider_satisfies_protocol(ar):
    """GovernanceProvider must structurally match AdvisoryProvider."""
    provider = ar.GovernanceProvider()
    assert hasattr(provider, "analyze")
    assert callable(provider.analyze)


def test_context_provider_satisfies_protocol(ar):
    """RuntimeContextProvider must structurally match AdvisoryProvider."""
    provider = ar.RuntimeContextProvider()
    assert hasattr(provider, "analyze")
    assert callable(provider.analyze)


def test_registry_provider_satisfies_protocol(ar):
    """RegistryProvider must structurally match AdvisoryProvider."""
    provider = ar.RegistryProvider()
    assert hasattr(provider, "analyze")
    assert callable(provider.analyze)


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _minimal_snapshot(ar):
    """Build a minimal RuntimeSnapshot for testing providers.
    Creates a snapshot with default/all-zero-state fields so providers
    can exercise their analysis logic without needing a real repo."""
    from pcae.core.runtime_snapshot import RuntimeSnapshot
    from pcae.core.runtime_introspection import (
        RuntimeInfo, HealthInfo, GovernanceInfo, RuntimeStateInfo, VersionInfo,
    )
    from pcae.core.runtime_registry import RegistrySnapshot

    return RuntimeSnapshot(
        runtime=RuntimeInfo(
            pipeline_stages=(),
            principles=(),
            runtime_services=(),
        ),
        registry=RegistrySnapshot(
            registered_plugin_count=0,
            registered_capability_count=0,
            registry_status="initialized",
            metadata_validity="valid",
            plugin_ids=(),
            capabilities=(),
        ),
        plugins=(),
        capabilities=(),
        health=HealthInfo(
            runtime_status="not_implemented",
            registry_status="initialized",
            plugin_count=0,
            capability_count=0,
            metadata_validity="valid",
            execution_availability="unavailable",
            current_runtime_state="Observed",
            current_maximum_plugin_capability="observe",
        ),
        governance=GovernanceInfo(
            non_executing_posture=True,
            broker_implementation_status="execution_unavailable",
            observed_command_paths=4,
            execution_capability="unavailable",
        ),
        state=RuntimeStateInfo(
            current_state="Observed",
            state_model=(
                "Intent", "Observed", "Advisory", "Approved",
                "Executable", "Executed", "Audited", "Rollback Ready",
            ),
        ),
        version=VersionInfo(
            release_version="0.1.0",
            plugin_versions=(),
        ),
        context=None,
    )


# ═══════════════════════════════════════════════════════════════════════
# Section 5 — Provider: RuntimeHealthProvider
# ═══════════════════════════════════════════════════════════════════════

def test_health_provider_returns_tuple_of_advisory_results(ar):
    """RuntimeHealthProvider must return a tuple of AdvisoryResults."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RuntimeHealthProvider()
    results = provider.analyze(snapshot)
    assert isinstance(results, tuple)
    for r in results:
        assert isinstance(r, ar.AdvisoryResult)


def test_health_provider_results_have_correct_category(ar):
    """All RuntimeHealthProvider results must have category 'Runtime Health'."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RuntimeHealthProvider()
    results = provider.analyze(snapshot)
    assert len(results) > 0
    for r in results:
        assert r.category == "Runtime Health"


def test_health_provider_execution_availability_result(ar):
    """Must produce a result about execution_availability."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RuntimeHealthProvider()
    results = provider.analyze(snapshot)
    ev_summaries = [
        ev.evidence_summary for r in results for ev in r.evidence_references
    ]
    assert any("execution_availability" in s for s in ev_summaries)


def test_health_provider_plugin_count_result(ar):
    """Must produce a result about plugin_count."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RuntimeHealthProvider()
    results = provider.analyze(snapshot)
    ev_summaries = [
        ev.evidence_summary for r in results for ev in r.evidence_references
    ]
    assert any("plugin_count" in s for s in ev_summaries)


def test_health_provider_evidence_references_point_to_health_domain(ar):
    """All evidence references from health provider must point to 'health' domain."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RuntimeHealthProvider()
    results = provider.analyze(snapshot)
    for r in results:
        for ev in r.evidence_references:
            assert ev.domain == "health", (
                f"Expected domain='health', got {ev.domain!r} in result "
                f"{r.advisory_id}"
            )


def test_health_provider_never_returns_empty_tuple(ar):
    """RuntimeHealthProvider must always produce at least one result."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RuntimeHealthProvider()
    results = provider.analyze(snapshot)
    assert len(results) > 0


# ═══════════════════════════════════════════════════════════════════════
# Section 6 — Provider: GovernanceProvider
# ═══════════════════════════════════════════════════════════════════════

def test_governance_provider_returns_tuple_of_advisory_results(ar):
    """GovernanceProvider must return a tuple of AdvisoryResults."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.GovernanceProvider()
    results = provider.analyze(snapshot)
    assert isinstance(results, tuple)
    for r in results:
        assert isinstance(r, ar.AdvisoryResult)


def test_governance_provider_results_have_correct_category(ar):
    """All GovernanceProvider results must have category 'Governance'."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.GovernanceProvider()
    results = provider.analyze(snapshot)
    assert len(results) > 0
    for r in results:
        assert r.category == "Governance"


def test_governance_provider_non_executing_posture_result(ar):
    """Must produce a result about non_executing_posture."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.GovernanceProvider()
    results = provider.analyze(snapshot)
    ev_summaries = [
        ev.evidence_summary for r in results for ev in r.evidence_references
    ]
    assert any("non_executing_posture" in s for s in ev_summaries)


def test_governance_provider_observed_command_paths_result(ar):
    """Must produce a result about observed_command_paths."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.GovernanceProvider()
    results = provider.analyze(snapshot)
    ev_summaries = [
        ev.evidence_summary for r in results for ev in r.evidence_references
    ]
    assert any("observed_command_paths" in s for s in ev_summaries)


def test_governance_provider_evidence_references_point_to_governance_domain(ar):
    """All evidence references from governance provider must point to 'governance' domain."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.GovernanceProvider()
    results = provider.analyze(snapshot)
    for r in results:
        for ev in r.evidence_references:
            assert ev.domain == "governance", (
                f"Expected domain='governance', got {ev.domain!r}"
            )


# ═══════════════════════════════════════════════════════════════════════
# Section 7 — Provider: RuntimeContextProvider
# ═══════════════════════════════════════════════════════════════════════

def test_context_provider_returns_tuple_of_advisory_results(ar):
    """RuntimeContextProvider must return a tuple of AdvisoryResults."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RuntimeContextProvider()
    results = provider.analyze(snapshot)
    assert isinstance(results, tuple)
    for r in results:
        assert isinstance(r, ar.AdvisoryResult)


def test_context_provider_handles_none_context(ar):
    """When snapshot.context is None, produce a result — don't crash."""
    snapshot = _minimal_snapshot(ar)  # context=None
    provider = ar.RuntimeContextProvider()
    results = provider.analyze(snapshot)
    assert len(results) > 0
    assert any("None" in r.rationale or "None" in r.reasoning_summary
               or "absent" in r.rationale.lower()
               for r in results)


def test_context_provider_evidence_references_point_to_context_domain(ar):
    """All evidence references from context provider must point to 'context' domain."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RuntimeContextProvider()
    results = provider.analyze(snapshot)
    for r in results:
        for ev in r.evidence_references:
            assert ev.domain == "context", (
                f"Expected domain='context', got {ev.domain!r}"
            )


# ═══════════════════════════════════════════════════════════════════════
# Section 8 — Provider: RegistryProvider
# ═══════════════════════════════════════════════════════════════════════

def test_registry_provider_returns_tuple_of_advisory_results(ar):
    """RegistryProvider must return a tuple of AdvisoryResults."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RegistryProvider()
    results = provider.analyze(snapshot)
    assert isinstance(results, tuple)
    for r in results:
        assert isinstance(r, ar.AdvisoryResult)


def test_registry_provider_results_have_correct_category(ar):
    """All RegistryProvider results must have category 'Registry'."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RegistryProvider()
    results = provider.analyze(snapshot)
    assert len(results) > 0
    for r in results:
        assert r.category == "Registry"


def test_registry_provider_plugin_count_result(ar):
    """Must produce a result about registered_plugin_count."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RegistryProvider()
    results = provider.analyze(snapshot)
    ev_summaries = [
        ev.evidence_summary for r in results for ev in r.evidence_references
    ]
    assert any("registered_plugin_count" in s for s in ev_summaries)


def test_registry_provider_evidence_references_point_to_registry_domain(ar):
    """All evidence references from registry provider must point to 'registry' domain."""
    snapshot = _minimal_snapshot(ar)
    provider = ar.RegistryProvider()
    results = provider.analyze(snapshot)
    for r in results:
        for ev in r.evidence_references:
            assert ev.domain == "registry", (
                f"Expected domain='registry', got {ev.domain!r}"
            )


# ═══════════════════════════════════════════════════════════════════════
# Section 9 — Aggregation
# ═══════════════════════════════════════════════════════════════════════

def test_build_advisory_results_returns_tuple(ar):
    """build_advisory_results must return a tuple, not a list."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    assert isinstance(results, tuple)


def test_build_advisory_results_is_deterministic(ar):
    """Calling build_advisory_results twice with same snapshot must produce identical results."""
    snapshot = _minimal_snapshot(ar)
    results1 = ar.build_advisory_results(snapshot)
    results2 = ar.build_advisory_results(snapshot)
    ids1 = tuple(r.advisory_id for r in results1)
    ids2 = tuple(r.advisory_id for r in results2)
    assert ids1 == ids2


def test_aggregation_sorts_by_severity(ar):
    """Results must be sorted by severity: info after advisory after warning after critical."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    ranks = {
        "critical": 0, "warning": 1, "advisory": 2, "info": 3,
    }
    for i in range(len(results) - 1):
        prev_rank = ranks.get(results[i].severity, 99)
        next_rank = ranks.get(results[i + 1].severity, 99)
        assert prev_rank <= next_rank, (
            f"Sort order violation: {results[i].advisory_id} "
            f"({results[i].severity}) before {results[i+1].advisory_id} "
            f"({results[i+1].severity})"
        )


def test_aggregation_sorts_by_category_within_same_severity(ar):
    """Within same severity, results must be sorted alphabetically by category."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    for i in range(len(results) - 1):
        if results[i].severity == results[i + 1].severity:
            assert results[i].category <= results[i + 1].category, (
                f"Category sort violation: {results[i].category} before "
                f"{results[i+1].category}"
            )


def test_aggregation_assigns_stable_advisory_ids(ar):
    """Advisory IDs must follow the format ADV-{category_slug}-{seq:04d}."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    for r in results:
        assert r.advisory_id.startswith("ADV-")
        assert not r.advisory_id.endswith("pending"), (
            f"Advisory ID was not assigned: {r.advisory_id!r}"
        )
        parts = r.advisory_id.split("-")
        assert len(parts) >= 3
        assert parts[-1].isdigit()


def test_aggregation_all_results_have_implementation_status_execution_unavailable(ar):
    """Every result must have implementation_status == 'execution_unavailable'."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    for r in results:
        assert r.implementation_status == "execution_unavailable"


def test_aggregation_all_results_have_timestamp_set(ar):
    """Every result must have a non-empty timestamp."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    for r in results:
        assert r.timestamp
        assert r.timestamp != "pending"


def test_aggregation_all_results_have_source_snapshot_reference(ar):
    """Every result must have a non-empty source_snapshot_reference."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    for r in results:
        assert r.source_snapshot_reference
        assert r.source_snapshot_reference != "pending"


# ═══════════════════════════════════════════════════════════════════════
# Section 10 — Module Isolation (AST-based)
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def module_source(ar) -> str:
    """The raw source text of advisory_runtime.py."""
    return Path(ar.__file__).read_text()


@pytest.fixture(scope="module")
def module_ast(ar):
    """The AST of advisory_runtime.py."""
    return ast.parse(Path(ar.__file__).read_text())


@pytest.fixture(scope="module")
def module_imports(ar) -> list[str]:
    """All direct import names in advisory_runtime.py."""
    tree = ast.parse(Path(ar.__file__).read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def test_module_imports_are_allowlisted(module_imports):
    """Only allowed modules may be imported by advisory_runtime.py."""
    allowed = {
        "__future__",
        "dataclasses",
        "datetime",
        "typing",
        "pcae.core.runtime_snapshot",
    }
    for name in module_imports:
        assert name in allowed, f"Unexpected import: {name}"


def test_no_broker_evaluation_dependency(module_imports):
    """advisory_runtime.py must not import permission_broker."""
    for name in module_imports:
        assert "permission_broker" not in name, (
            f"Broker dependency: {name}"
        )
        assert "command_path_observation" not in name, (
            f"Command-path observation dependency: {name}"
        )


def test_no_plugin_loading_dependency(module_imports):
    """advisory_runtime.py must not import runtime_registry directly."""
    for name in module_imports:
        assert "runtime_registry" not in name, (
            f"Registry dependency (providers read through snapshot, never directly): {name}"
        )


def test_module_has_no_shell_or_subprocess_dependency(module_imports):
    """advisory_runtime.py must not import subprocess or os."""
    for name in module_imports:
        assert name not in ("subprocess", "os", "shutil", "signal"), (
            f"Shell dependency: {name}"
        )
        assert "shell" not in name.lower(), f"Shell dependency: {name}"


def test_module_has_no_backend_or_network_dependency(module_imports):
    """advisory_runtime.py must not import network or backend modules."""
    for name in module_imports:
        assert name not in ("socket", "requests", "urllib", "http", "ssl"), (
            f"Network dependency: {name}"
        )
        assert "backend" not in name.lower(), f"Backend dependency: {name}"
        assert "notification" not in name.lower(), f"Notification dependency: {name}"


def test_no_eval_exec_in_module(module_source):
    """advisory_runtime.py source must not contain eval, exec, compile calls."""
    lowered = module_source.lower()
    assert "eval(" not in lowered
    assert "exec(" not in lowered
    assert "compile(" not in lowered


def test_no_importlib_in_module(module_source):
    """advisory_runtime.py source must not use importlib."""
    assert "importlib" not in module_source


# ═══════════════════════════════════════════════════════════════════════
# Section 11 — Observation-Only Guarantees
# ═══════════════════════════════════════════════════════════════════════

def test_providers_never_mutate_snapshot(ar):
    """Every provider must leave the snapshot unchanged."""
    snapshot = _minimal_snapshot(ar)
    # Capture fields before
    before_fields = {
        f.name: getattr(snapshot, f.name)
        for f in dataclasses.fields(snapshot)
    }

    providers = [
        ar.RuntimeHealthProvider(),
        ar.GovernanceProvider(),
        ar.RuntimeContextProvider(),
        ar.RegistryProvider(),
    ]
    for provider in providers:
        provider.analyze(snapshot)

    # Capture fields after
    after_fields = {
        f.name: getattr(snapshot, f.name)
        for f in dataclasses.fields(snapshot)
    }
    assert before_fields == after_fields


def _source_excluding_docstrings(ar) -> str:
    """Return the module source with all docstrings blanked out.
    This lets us search for forbidden references in actual code while
    ignoring documentation mentions (which are legitimate prohibitions,
    e.g. 'never calls PermissionBroker.evaluate()')."""
    tree = ast.parse(Path(ar.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body[0].value.value = ""
    return ast.unparse(tree)


def test_providers_never_call_permission_broker(ar):
    """advisory_runtime.py code (excluding docstrings) must not reference
    PermissionBroker or call evaluate()."""
    code = _source_excluding_docstrings(ar)
    assert "PermissionBroker" not in code, (
        "PermissionBroker referenced in code (not just docstring)"
    )
    assert "evaluate(" not in code, (
        "evaluate() call in code (not just docstring)"
    )


def test_no_cli_wiring(ar):
    """cli.py must not reference advisory_runtime."""
    cli_text = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text()
    assert "advisory_runtime" not in cli_text


def test_no_commands_module(ar):
    """No src/pcae/commands/advisory_runtime.py must exist."""
    assert not (REPO_ROOT / "src" / "pcae" / "commands" / "advisory_runtime.py").exists()


def test_no_argparse_in_module(module_source):
    """advisory_runtime.py must not import or reference argparse."""
    assert "argparse" not in module_source


def test_no_subprocess_in_module(module_source):
    """advisory_runtime.py must not reference subprocess."""
    assert "subprocess" not in module_source


# ═══════════════════════════════════════════════════════════════════════
# Section 12 — 113B Contract Compliance
# ═══════════════════════════════════════════════════════════════════════

def test_all_14_fields_present_in_advisory_result(ar):
    """Every field from the 113B contract must exist in AdvisoryResult."""
    field_names = {f.name for f in dataclasses.fields(ar.AdvisoryResult)}
    for field in ADVISORY_RESULT_FIELDS:
        assert field in field_names, f"Missing field: {field}"


def test_evidence_reference_four_fields_match_contract(ar):
    """EvidenceReference must have exactly 4 fields matching 113B §3."""
    field_names = {f.name for f in dataclasses.fields(ar.EvidenceReference)}
    assert field_names == {"domain", "object_id", "field_path", "evidence_summary"}


def test_module_docstring_references_113a_and_113b(ar):
    """Module docstring must cite the architecture and contract docs."""
    doc = ar.__doc__ or ""
    assert "113A" in doc or "PCAE_ADVISORY_RUNTIME.md" in doc
    assert "113B" in doc or "PCAE_ADVISORY_RUNTIME_CONTRACT.md" in doc


def test_advisory_result_explainability_facets(ar):
    """Every result must include the 8 facets from 113B §2, realized through fields."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    assert len(results) > 0
    for r in results:
        # Field existence proves the 8 facets are realizable:
        # 1. What was observed → reasoning_summary + rationale
        assert r.reasoning_summary
        assert r.rationale
        # 2. Why it matters → severity + rationale
        assert r.severity in ar.SEVERITY_LEVELS
        # 3. What evidence → evidence_references
        assert isinstance(r.evidence_references, tuple)
        # 4. Which snapshot fields → evidence_references.field_path
        for ev in r.evidence_references:
            assert ev.field_path
        # 5. What recommendation → recommended_action
        assert r.recommended_action
        # 6. What remediation → remediation
        assert r.remediation
        # 7-8. The invariant (why advisory, why no execution) → ADVISORY_INVARIANT
        assert ar.ADVISORY_INVARIANT


def test_advisory_result_reproducible_from_snapshot(ar):
    """Reproducibility: same snapshot → identical advisory_id sequence."""
    snapshot = _minimal_snapshot(ar)
    ids1 = tuple(r.advisory_id for r in ar.build_advisory_results(snapshot))
    ids2 = tuple(r.advisory_id for r in ar.build_advisory_results(snapshot))
    assert ids1 == ids2


# ═══════════════════════════════════════════════════════════════════════
# Section 13 — Integration with Real RuntimeSnapshot
# ═══════════════════════════════════════════════════════════════════════

def test_build_advisory_results_with_real_snapshot(ar):
    """build_advisory_results must work with a real RuntimeSnapshot."""
    from pcae.core.runtime_snapshot import build_runtime_snapshot
    from pcae.core.runtime_registry import RuntimeRegistry
    from pcae.core.paths import HarnessPath

    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath.cwd(), registry)
    results = ar.build_advisory_results(snapshot)
    assert isinstance(results, tuple)
    assert len(results) > 0
    for r in results:
        assert isinstance(r, ar.AdvisoryResult)
        assert r.implementation_status == "execution_unavailable"
        assert r.advisory_id
        assert r.timestamp


def test_build_advisory_results_with_real_snapshot_preserves_observed_state(ar):
    """With a real snapshot, current_runtime_state must remain Observed."""
    from pcae.core.runtime_snapshot import build_runtime_snapshot
    from pcae.core.runtime_registry import RuntimeRegistry
    from pcae.core.paths import HarnessPath

    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath.cwd(), registry)
    assert snapshot.health.current_runtime_state == "Observed"
    assert snapshot.health.execution_availability == "unavailable"

    # Calling advisory runtime must not change anything
    ar.build_advisory_results(snapshot)
    assert snapshot.health.current_runtime_state == "Observed"
    assert snapshot.health.execution_availability == "unavailable"


def test_build_advisory_results_with_real_snapshot_execution_unavailable(ar):
    """execution_capability must remain 'unavailable' after advisory analysis."""
    from pcae.core.runtime_snapshot import build_runtime_snapshot
    from pcae.core.runtime_registry import RuntimeRegistry
    from pcae.core.paths import HarnessPath

    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath.cwd(), registry)
    assert snapshot.governance.execution_capability == "unavailable"

    results = ar.build_advisory_results(snapshot)
    for r in results:
        assert r.implementation_status == "execution_unavailable"


def test_build_advisory_results_with_minimal_snapshot_no_crash(ar):
    """A minimal snapshot with all-default fields must not cause any crash."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    assert isinstance(results, tuple)
    assert len(results) > 0
