from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from pcae.advisory.context.advisory_context_builder import build_advisory_context
from pcae.advisory.context.context_request import AdvisoryContextRequest
from pcae.repository_intelligence.change_impact import (
    ChangeImpactRequest,
    build_change_impact_report,
)
from pcae.repository_intelligence.cross_artifact_integration import (
    generate_cross_artifact_integration,
)
from pcae.repository_intelligence.dependency_graph import generate_dependency_graph
from pcae.repository_intelligence.historical_memory import generate_historical_memory
from pcae.repository_intelligence.snapshot_generator import generate_snapshot
from pcae.repository_intelligence.service import (
    ServiceRequest,
    ServiceResponse,
    execute_service_request,
)
from pcae.repository_intelligence.service.errors import (
    MalformedServiceRequestError,
    UnsupportedServiceRequestError,
)
from pcae.repository_intelligence.service.request import normalize_service_request, resolve_scope
from pcae.repository_intelligence.unified_query.routing import (
    ADVISORY_CONTEXT,
    CHANGE_IMPACT,
    CROSS_ARTIFACT_INTEGRATION,
    DEPENDENCY_KNOWLEDGE_GRAPH,
    HISTORICAL_MEMORY,
    REPOSITORY_KNOWLEDGE_SNAPSHOT,
    SIX_ARTIFACT_FAMILIES,
)
from pcae.repository_intelligence.query.snapshot_loader import (
    SnapshotCompatibilityError,
    SnapshotLoadError,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _build_real_artifacts(tmp_path: Path) -> dict[str, Path]:
    """Generate real artifacts for all six covered families against the
    real repository (mirroring 131E's own established fixture pattern)."""
    snapshot_result = generate_snapshot(REPO_ROOT, output_dir=tmp_path / "rks")
    rks_path = Path(snapshot_result["latest_path"])

    graph_result = generate_dependency_graph(rks_path, repo_root=REPO_ROOT, output_dir=tmp_path / "dkg")
    dkg_path = Path(graph_result["latest_path"])

    hm_result = generate_historical_memory(rks_path, repo_root=REPO_ROOT, output_dir=tmp_path / "hm")
    hm_path = Path(hm_result["latest_path"])

    snapshot = _load_json(rks_path)
    entity_ids = [e["entity_id"] for e in snapshot["architectural_entities"]][:3]
    ci_request = ChangeImpactRequest(
        requested_change="132E test fixtures",
        repository_scope=str(rks_path),
        target_entities=tuple(entity_ids),
    )
    report = build_change_impact_report(rks_path, ci_request)
    ci_path = tmp_path / "change_impact.json"
    ci_path.write_text(json.dumps(report.to_dict()))

    adv_request = AdvisoryContextRequest(
        category="entity_lookup", advisory_purpose="132E test fixtures", target=entity_ids[0]
    )
    adv_package = build_advisory_context(rks_path, adv_request)
    adv_path = tmp_path / "advisory_context.json"
    adv_path.write_text(json.dumps(adv_package.to_dict()))

    cai_result = generate_cross_artifact_integration(
        ci_path, dkg_path, repo_root=REPO_ROOT, output_dir=tmp_path / "cai"
    )
    cai_path = Path(cai_result["latest_path"])

    return {
        REPOSITORY_KNOWLEDGE_SNAPSHOT: rks_path,
        DEPENDENCY_KNOWLEDGE_GRAPH: dkg_path,
        HISTORICAL_MEMORY: hm_path,
        CHANGE_IMPACT: ci_path,
        ADVISORY_CONTEXT: adv_path,
        CROSS_ARTIFACT_INTEGRATION: cai_path,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def real_artifacts(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Generate all six real artifacts exactly once for the whole test
    module (learned from 131E: per-test regeneration is prohibitively
    slow because Historical Memory generation walks full git history).
    Every test in this module only reads these artifacts, never
    mutates them (confirmed independently by TestReadOnlyGuarantees)."""
    tmp_path = tmp_path_factory.mktemp("service_fixtures")
    return _build_real_artifacts(tmp_path)


@pytest.fixture(scope="module")
def target_entity(real_artifacts: dict[str, Path]) -> str:
    snapshot = _load_json(real_artifacts[REPOSITORY_KNOWLEDGE_SNAPSHOT])
    return snapshot["architectural_entities"][0]["entity_id"]


# ── Request validation ──────────────────────────────────────────────────────


class TestRequestValidation:
    def test_entity_request_requires_no_families(self) -> None:
        request = ServiceRequest(kind="entity", target="x", families=(DEPENDENCY_KNOWLEDGE_GRAPH,))
        with pytest.raises(ValueError):
            normalize_service_request(request)

    def test_artifact_request_requires_exactly_one_family(self) -> None:
        with pytest.raises(ValueError):
            normalize_service_request(ServiceRequest(kind="artifact", target="x", families=()))
        with pytest.raises(ValueError):
            normalize_service_request(
                ServiceRequest(
                    kind="artifact",
                    target="x",
                    families=(DEPENDENCY_KNOWLEDGE_GRAPH, HISTORICAL_MEMORY),
                )
            )

    def test_scoped_request_requires_at_least_one_family(self) -> None:
        with pytest.raises(ValueError):
            normalize_service_request(ServiceRequest(kind="scoped", target="x", families=()))

    def test_unknown_family_is_malformed(self) -> None:
        with pytest.raises(ValueError):
            normalize_service_request(ServiceRequest(kind="scoped", target="x", families=("bogus",)))

    def test_duplicate_families_are_malformed(self) -> None:
        with pytest.raises(ValueError):
            normalize_service_request(
                ServiceRequest(
                    kind="scoped",
                    target="x",
                    families=(DEPENDENCY_KNOWLEDGE_GRAPH, DEPENDENCY_KNOWLEDGE_GRAPH),
                )
            )

    def test_empty_target_is_malformed(self) -> None:
        with pytest.raises(ValueError):
            normalize_service_request(ServiceRequest(kind="entity", target=""))

    def test_composite_requires_target_none(self) -> None:
        inner = ServiceRequest(kind="entity", target="x")
        with pytest.raises(ValueError):
            normalize_service_request(ServiceRequest(kind="composite", target="y", composite_targets=(inner,)))

    def test_composite_requires_at_least_one_target(self) -> None:
        with pytest.raises(ValueError):
            normalize_service_request(ServiceRequest(kind="composite", composite_targets=()))

    def test_composite_rejects_nested_composite(self) -> None:
        inner_composite = ServiceRequest(kind="composite", composite_targets=(ServiceRequest(kind="entity", target="x"),))
        with pytest.raises(ValueError):
            normalize_service_request(ServiceRequest(kind="composite", composite_targets=(inner_composite,)))

    def test_unsupported_kind_is_malformed(self) -> None:
        with pytest.raises(ValueError):
            normalize_service_request(ServiceRequest(kind="bogus", target="x"))


# ── Scope resolution ─────────────────────────────────────────────────────────


class TestScopeResolution:
    def test_entity_resolves_to_all_six_families_in_fixed_order(self) -> None:
        request = ServiceRequest(kind="entity", target="x")
        assert resolve_scope(request) == SIX_ARTIFACT_FAMILIES

    def test_scoped_resolves_to_fixed_order_regardless_of_input_order(self) -> None:
        request = ServiceRequest(
            kind="scoped", target="x", families=(HISTORICAL_MEMORY, REPOSITORY_KNOWLEDGE_SNAPSHOT)
        )
        resolved = resolve_scope(request)
        assert resolved == tuple(f for f in SIX_ARTIFACT_FAMILIES if f in resolved)
        assert set(resolved) == {HISTORICAL_MEMORY, REPOSITORY_KNOWLEDGE_SNAPSHOT}

    def test_artifact_resolves_to_single_family(self) -> None:
        request = ServiceRequest(kind="artifact", target="x", families=(CHANGE_IMPACT,))
        assert resolve_scope(request) == (CHANGE_IMPACT,)


# ── Service lifecycle / single-target requests ──────────────────────────────


class TestServiceLifecycle:
    def test_entity_request_composes_all_applicable_families(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        request = ServiceRequest(kind="entity", target=target_entity)
        response = execute_service_request(request, artifact_paths=real_artifacts)
        assert response.result_status == "ok"
        assert REPOSITORY_KNOWLEDGE_SNAPSHOT in response.families
        assert len(response.composition_metadata) == 6

    def test_artifact_request_scopes_to_one_family(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        request = ServiceRequest(kind="artifact", target=target_entity, families=(DEPENDENCY_KNOWLEDGE_GRAPH,))
        response = execute_service_request(request, artifact_paths=real_artifacts)
        assert set(response.families.keys()) <= {DEPENDENCY_KNOWLEDGE_GRAPH}
        assert len(response.composition_metadata) == 1

    def test_scoped_request_never_exceeds_allow_list(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        request = ServiceRequest(
            kind="scoped",
            target=target_entity,
            families=(REPOSITORY_KNOWLEDGE_SNAPSHOT, HISTORICAL_MEMORY),
        )
        response = execute_service_request(request, artifact_paths=real_artifacts)
        assert set(response.families.keys()) <= {REPOSITORY_KNOWLEDGE_SNAPSHOT, HISTORICAL_MEMORY}
        called_families = {entry["family"] for entry in response.composition_metadata}
        assert called_families == {REPOSITORY_KNOWLEDGE_SNAPSHOT, HISTORICAL_MEMORY}


# ── Unified Query reuse ─────────────────────────────────────────────────────


class TestUnifiedQueryReuse:
    def test_rks_family_result_matches_direct_unified_query_call(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        from pcae.repository_intelligence.unified_query import (
            UnifiedQueryRequest,
            execute_unified_query,
        )

        direct = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target_entity),
            artifact_paths={REPOSITORY_KNOWLEDGE_SNAPSHOT: real_artifacts[REPOSITORY_KNOWLEDGE_SNAPSHOT]},
        )
        request = ServiceRequest(kind="artifact", target=target_entity, families=(REPOSITORY_KNOWLEDGE_SNAPSHOT,))
        response = execute_service_request(request, artifact_paths=real_artifacts)
        assert response.families[REPOSITORY_KNOWLEDGE_SNAPSHOT]["references"] == list(direct.references)

    def test_track_121_query_layer_unaffected(self) -> None:
        from pcae.repository_intelligence.query.query_request import SUPPORTED_QUERY_CATEGORIES

        assert SUPPORTED_QUERY_CATEGORIES == frozenset(
            {
                "entity_lookup",
                "capability_lookup",
                "architectural_contract_lookup",
                "attribution_lookup",
                "limitation_lookup",
                "boundary_lookup",
            }
        )

    def test_unified_query_routing_table_unaffected(self) -> None:
        from pcae.repository_intelligence.unified_query.routing import ROUTING_TABLE

        assert len(ROUTING_TABLE) == 7
        assert "change_impact_to_dependency_node" in ROUTING_TABLE


# ── Composite requests ───────────────────────────────────────────────────────


class TestCompositeRequests:
    def test_composite_composes_independent_inner_responses(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        inner_a = ServiceRequest(kind="entity", target=target_entity)
        inner_b = ServiceRequest(kind="artifact", target=target_entity, families=(DEPENDENCY_KNOWLEDGE_GRAPH,))
        request = ServiceRequest(kind="composite", composite_targets=(inner_a, inner_b))
        response = execute_service_request(request, artifact_paths=real_artifacts)
        assert len(response.composite_responses) == 2
        assert response.families == {}

    def test_composite_never_correlates_across_targets(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        inner_a = ServiceRequest(kind="entity", target=target_entity)
        inner_b = ServiceRequest(kind="entity", target="entity:does-not-exist")
        request = ServiceRequest(kind="composite", composite_targets=(inner_a, inner_b))
        response = execute_service_request(request, artifact_paths=real_artifacts)
        statuses = {r.request_metadata["target"]: r.result_status for r in response.composite_responses}
        assert statuses[target_entity] == "ok"
        assert statuses["entity:does-not-exist"] == "unknown"
        # A miss on one target never influences the other's own result.
        resolved_response = next(r for r in response.composite_responses if r.request_metadata["target"] == target_entity)
        assert resolved_response.result_status == "ok"

    def test_composite_ordering_is_deterministic(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        inner_a = ServiceRequest(kind="entity", target="zzz-target")
        inner_b = ServiceRequest(kind="entity", target=target_entity)
        request = ServiceRequest(kind="composite", composite_targets=(inner_a, inner_b))
        response = execute_service_request(request, artifact_paths=real_artifacts)
        targets = [r.request_metadata["target"] for r in response.composite_responses]
        assert targets == sorted(targets)


# ── Deterministic composition ───────────────────────────────────────────────


class TestDeterministicComposition:
    def test_equivalent_request_produces_equivalent_response(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        request = ServiceRequest(kind="entity", target=target_entity, include_evidence=True)
        response_a = execute_service_request(request, artifact_paths=real_artifacts).to_dict()
        response_b = execute_service_request(request, artifact_paths=real_artifacts).to_dict()
        assert response_a == response_b

    def test_composition_metadata_order_is_fixed_family_order(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        request = ServiceRequest(kind="entity", target=target_entity)
        response = execute_service_request(request, artifact_paths=real_artifacts)
        called_order = [entry["family"] for entry in response.composition_metadata]
        assert called_order == list(SIX_ARTIFACT_FAMILIES)


# ── Provenance preservation ──────────────────────────────────────────────────


class TestProvenancePreservation:
    def test_provenance_matches_source_unified_query_call(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        from pcae.repository_intelligence.unified_query import (
            UnifiedQueryRequest,
            execute_unified_query,
        )

        direct = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target_entity),
            artifact_paths={REPOSITORY_KNOWLEDGE_SNAPSHOT: real_artifacts[REPOSITORY_KNOWLEDGE_SNAPSHOT]},
        )
        request = ServiceRequest(kind="artifact", target=target_entity, families=(REPOSITORY_KNOWLEDGE_SNAPSHOT,))
        response = execute_service_request(request, artifact_paths=real_artifacts)
        composed_provenance = response.families[REPOSITORY_KNOWLEDGE_SNAPSHOT]["references"][0]["provenance"]
        direct_provenance = direct.references[0]["provenance"]
        assert composed_provenance == direct_provenance

    def test_composition_metadata_never_nested_in_provenance(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        request = ServiceRequest(kind="entity", target=target_entity)
        response = execute_service_request(request, artifact_paths=real_artifacts)
        for family_content in response.families.values():
            for reference in family_content["references"]:
                assert "composition_metadata" not in reference["provenance"]


# ── Evidence preservation ───────────────────────────────────────────────────


class TestEvidencePreservation:
    def test_evidence_omitted_by_default(self, real_artifacts: dict[str, Path], target_entity: str) -> None:
        request = ServiceRequest(kind="artifact", target=target_entity, families=(REPOSITORY_KNOWLEDGE_SNAPSHOT,))
        response = execute_service_request(request, artifact_paths=real_artifacts)
        assert response.families[REPOSITORY_KNOWLEDGE_SNAPSHOT]["evidence"] == []

    def test_evidence_verbatim_when_requested(self, real_artifacts: dict[str, Path], target_entity: str) -> None:
        snapshot = _load_json(real_artifacts[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        source_record = snapshot["architectural_entities"][0]
        request = ServiceRequest(
            kind="artifact",
            target=target_entity,
            families=(REPOSITORY_KNOWLEDGE_SNAPSHOT,),
            include_evidence=True,
        )
        response = execute_service_request(request, artifact_paths=real_artifacts)
        evidence = response.families[REPOSITORY_KNOWLEDGE_SNAPSHOT]["evidence"]
        assert evidence
        assert evidence[0]["content"] == source_record


# ── Uncertainty / limitation propagation ────────────────────────────────────


class TestUncertaintyAndLimitationPropagation:
    def test_uncertainty_present_on_total_miss(self, real_artifacts: dict[str, Path]) -> None:
        request = ServiceRequest(kind="entity", target="entity:does-not-exist-anywhere")
        response = execute_service_request(request, artifact_paths=real_artifacts)
        assert response.result_status == "unknown"
        assert response.uncertainty

    def test_limitations_present_when_family_skipped(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        partial_paths = dict(real_artifacts)
        del partial_paths[HISTORICAL_MEMORY]
        request = ServiceRequest(
            kind="scoped", target=target_entity, families=(REPOSITORY_KNOWLEDGE_SNAPSHOT, HISTORICAL_MEMORY)
        )
        response = execute_service_request(request, artifact_paths=partial_paths)
        assert any("historical_memory" in lim.get("limitation_description", "") for lim in response.limitations)


# ── Boundary disclosure propagation ─────────────────────────────────────────


class TestBoundaryDisclosurePropagation:
    REQUIRED_FIELDS = (
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

    def test_all_nine_fields_present_and_true(self, real_artifacts: dict[str, Path], target_entity: str) -> None:
        request = ServiceRequest(kind="entity", target=target_entity)
        response = execute_service_request(request, artifact_paths=real_artifacts)
        for field_name in self.REQUIRED_FIELDS:
            assert response.boundary_disclosures.get(field_name) is True

    def test_boundary_disclosures_match_unified_query_object_exactly(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        from pcae.repository_intelligence.unified_query.boundary import (
            unified_query_boundary_disclosures,
        )

        request = ServiceRequest(kind="entity", target=target_entity)
        response = execute_service_request(request, artifact_paths=real_artifacts)
        assert response.boundary_disclosures == unified_query_boundary_disclosures()


# ── Composition metadata ────────────────────────────────────────────────────


class TestCompositionMetadata:
    def test_composition_metadata_is_structurally_separate_field(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        request = ServiceRequest(kind="entity", target=target_entity)
        response = execute_service_request(request, artifact_paths=real_artifacts)
        data = response.to_dict()
        assert "composition_metadata" in data
        assert isinstance(data["composition_metadata"], list)
        for entry in data["composition_metadata"]:
            assert "family" in entry
            assert "category" in entry
            assert "status" in entry

    def test_composition_metadata_never_states_entity_content_claims(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        request = ServiceRequest(kind="entity", target=target_entity)
        response = execute_service_request(request, artifact_paths=real_artifacts)
        allowed_keys = {"family", "category", "status", "reason", "result_status"}
        for entry in response.composition_metadata:
            assert set(entry.keys()) <= allowed_keys


# ── Identity reuse ───────────────────────────────────────────────────────────


class TestIdentityReuse:
    def test_exact_match_required_no_fuzzy_resolution(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        near_misses = [
            target_entity + "/",
            target_entity.upper(),
            " " + target_entity,
            target_entity[:-1],
        ]
        for near_miss in near_misses:
            request = ServiceRequest(kind="entity", target=near_miss)
            response = execute_service_request(request, artifact_paths=real_artifacts)
            assert response.result_status == "unknown", f"near-miss {near_miss!r} incorrectly resolved"

    def test_no_identity_derivation_function_in_service_package(self) -> None:
        import pcae.repository_intelligence.service.service_engine as engine_module

        source = Path(engine_module.__file__).read_text()
        assert "def _node_id_for_entity" not in source
        assert "def find_by_id" not in source


# ── Fail-closed behavior ─────────────────────────────────────────────────────


class TestFailClosedBehavior:
    def test_missing_artifact_recorded_as_limitation_not_swallowed(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        request = ServiceRequest(kind="artifact", target=target_entity, families=(DEPENDENCY_KNOWLEDGE_GRAPH,))
        response = execute_service_request(request, artifact_paths={})
        assert response.limitations
        assert response.composition_metadata[0]["status"] == "skipped"

    def test_incompatible_artifact_recorded_as_limitation(self, tmp_path: Path, target_entity: str) -> None:
        bad_path = tmp_path / "bad_dkg.json"
        bad_path.write_text(json.dumps({"snapshot_identity": {"executable_schema_version": "wrong"}}))
        request = ServiceRequest(kind="artifact", target=target_entity, families=(DEPENDENCY_KNOWLEDGE_GRAPH,))
        response = execute_service_request(request, artifact_paths={DEPENDENCY_KNOWLEDGE_GRAPH: bad_path})
        assert response.limitations
        assert response.composition_metadata[0]["status"] == "failed"

    def test_malformed_request_fails_closed(self, real_artifacts: dict[str, Path]) -> None:
        with pytest.raises(MalformedServiceRequestError):
            execute_service_request(ServiceRequest(kind="entity", target=None), artifact_paths=real_artifacts)

    def test_unsupported_request_kind_fails_closed(self, real_artifacts: dict[str, Path]) -> None:
        with pytest.raises(MalformedServiceRequestError):
            execute_service_request(ServiceRequest(kind="bogus", target="x"), artifact_paths=real_artifacts)


# ── Silent-omission regression (131F) ───────────────────────────────────────


class TestSilentOmissionRegression:
    """Directly re-tests, one layer up, the exact defect class 131F
    independently discovered and 132B Section 15 binds this lineage to
    treat as BLOCKING: a request that cannot be satisfied must never
    silently return an empty 'ok'-equivalent response."""

    def test_total_miss_never_returns_silent_ok(self, real_artifacts: dict[str, Path]) -> None:
        request = ServiceRequest(kind="entity", target="entity:totally-unresolvable-target")
        response = execute_service_request(request, artifact_paths=real_artifacts)
        assert response.result_status != "ok"
        assert response.uncertainty or response.limitations
        assert not any(content["references"] for content in response.families.values())

    def test_no_artifact_paths_never_returns_silent_ok(self) -> None:
        request = ServiceRequest(kind="entity", target="entity:anything")
        response = execute_service_request(request, artifact_paths={})
        assert response.result_status != "ok"
        assert response.limitations or response.uncertainty

    def test_composite_inner_miss_is_explicit_not_silent(self, real_artifacts: dict[str, Path]) -> None:
        inner = ServiceRequest(kind="entity", target="entity:composite-unresolvable")
        request = ServiceRequest(kind="composite", composite_targets=(inner,))
        response = execute_service_request(request, artifact_paths=real_artifacts)
        assert len(response.composite_responses) == 1
        inner_response = response.composite_responses[0]
        assert inner_response.result_status == "unknown"
        assert inner_response.uncertainty or inner_response.limitations


# ── Read-only guarantees ─────────────────────────────────────────────────────


class TestReadOnlyGuarantees:
    def test_artifacts_unchanged_after_request(self, real_artifacts: dict[str, Path], target_entity: str) -> None:
        checksums_before = {family: _sha256(path) for family, path in real_artifacts.items()}
        request = ServiceRequest(kind="entity", target=target_entity, include_evidence=True)
        execute_service_request(request, artifact_paths=real_artifacts)
        checksums_after = {family: _sha256(path) for family, path in real_artifacts.items()}
        assert checksums_before == checksums_after

    def test_no_new_files_written_by_request(self, real_artifacts: dict[str, Path], target_entity: str) -> None:
        fixtures_root = next(iter(real_artifacts.values())).parent.parent
        before = {p for p in fixtures_root.rglob("*") if p.is_file()}
        request = ServiceRequest(kind="entity", target=target_entity)
        execute_service_request(request, artifact_paths=real_artifacts)
        after = {p for p in fixtures_root.rglob("*") if p.is_file()}
        assert before == after

    def test_no_write_call_in_service_package(self) -> None:
        import pcae.repository_intelligence.service as service_package

        package_dir = Path(service_package.__file__).parent
        for py_file in package_dir.glob("*.py"):
            source = py_file.read_text()
            assert "open(" not in source or "'w'" not in source
            assert "write_text" not in source
            assert "json.dump(" not in source


# ── Compatibility / regression ──────────────────────────────────────────────


class TestCompatibilityRegression:
    def test_response_is_closed_shape(self, real_artifacts: dict[str, Path], target_entity: str) -> None:
        request = ServiceRequest(kind="entity", target=target_entity)
        response = execute_service_request(request, artifact_paths=real_artifacts)
        data = response.to_dict()
        allowed_keys = {
            "request_metadata",
            "result_status",
            "families",
            "composition_metadata",
            "limitations",
            "uncertainty",
            "boundary_disclosures",
            "boundary_notes",
            "composite_responses",
            "determinism",
        }
        assert set(data.keys()) <= allowed_keys

    def test_service_response_is_a_dataclass_instance(
        self, real_artifacts: dict[str, Path], target_entity: str
    ) -> None:
        request = ServiceRequest(kind="entity", target=target_entity)
        response = execute_service_request(request, artifact_paths=real_artifacts)
        assert isinstance(response, ServiceResponse)

    def test_track_130_cross_artifact_integration_unaffected(self, real_artifacts: dict[str, Path]) -> None:
        package = _load_json(real_artifacts[CROSS_ARTIFACT_INTEGRATION])
        assert "entity_resolutions" in package
        assert "unresolved_identities" in package
        assert "boundary_disclosures" in package

    def test_unified_query_response_shape_unaffected(self) -> None:
        from pcae.repository_intelligence.unified_query.response import UnifiedQueryResponse
        import dataclasses

        field_names = {f.name for f in dataclasses.fields(UnifiedQueryResponse)}
        assert field_names == {
            "query_metadata",
            "references",
            "evidence",
            "limitations",
            "uncertainty",
            "boundary_disclosures",
            "boundary_notes",
            "result_status",
        }
