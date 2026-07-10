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
from pcae.repository_intelligence.unified_query import (
    UnifiedQueryRequest,
    UnifiedQueryResponse,
    execute_unified_query,
)
from pcae.repository_intelligence.unified_query.errors import (
    RoutingAmbiguityError,
    UnsupportedQueryCategoryError,
)
from pcae.repository_intelligence.unified_query.request import normalize_request
from pcae.repository_intelligence.unified_query.routing import (
    ADVISORY_CONTEXT,
    CHANGE_IMPACT,
    CROSS_ARTIFACT_INTEGRATION,
    DEPENDENCY_KNOWLEDGE_GRAPH,
    HISTORICAL_MEMORY,
    REPOSITORY_KNOWLEDGE_SNAPSHOT,
    ROUTING_TABLE,
    route,
)
from pcae.repository_intelligence.unified_query.unified_query_engine import (
    MalformedRequestError,
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
    real repository (mirroring 126E/127E/130E's own established fixture
    pattern of testing against real data, not only synthetic
    fixtures)."""
    snapshot_result = generate_snapshot(REPO_ROOT, output_dir=tmp_path / "rks")
    rks_path = Path(snapshot_result["latest_path"])

    graph_result = generate_dependency_graph(rks_path, repo_root=REPO_ROOT, output_dir=tmp_path / "dkg")
    dkg_path = Path(graph_result["latest_path"])

    hm_result = generate_historical_memory(rks_path, repo_root=REPO_ROOT, output_dir=tmp_path / "hm")
    hm_path = Path(hm_result["latest_path"])

    snapshot = _load_json(rks_path)
    entity_ids = [e["entity_id"] for e in snapshot["architectural_entities"]][:3]
    ci_request = ChangeImpactRequest(
        requested_change="131E test fixtures",
        repository_scope=str(rks_path),
        target_entities=tuple(entity_ids),
    )
    report = build_change_impact_report(rks_path, ci_request)
    ci_path = tmp_path / "change_impact.json"
    ci_path.write_text(json.dumps(report.to_dict()))

    adv_request = AdvisoryContextRequest(
        category="entity_lookup", advisory_purpose="131E test fixtures", target=entity_ids[0]
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
    module (not once per test function).

    Generation involves a full repository scan plus a git-history walk
    (Historical Memory) and is expensive; every test in this module
    only reads these already-generated, already-verified-read-only
    artifacts (never mutates them -- confirmed independently by
    TestReadOnlyGuarantees), so sharing one generation across the
    module is safe and does not weaken any test's own assertions.
    """
    tmp_path = tmp_path_factory.mktemp("unified_query_fixtures")
    return _build_real_artifacts(tmp_path)


# ── Request normalization ──────────────────────────────────────────────────


class TestRequestNormalization:
    def test_normalization_sorts_filters(self) -> None:
        request = UnifiedQueryRequest(category="rks_entity_lookup", filters={"b": "2", "a": "1"})
        normalized = normalize_request(request)
        assert list(normalized["filters"].keys()) == ["a", "b"]

    def test_normalization_is_deterministic(self) -> None:
        request = UnifiedQueryRequest(category="rks_entity_lookup", target="x", filters={"z": "1"})
        assert normalize_request(request) == normalize_request(request)

    def test_empty_category_is_malformed(self) -> None:
        with pytest.raises(ValueError):
            normalize_request(UnifiedQueryRequest(category=""))

    def test_non_string_target_is_malformed(self) -> None:
        request = UnifiedQueryRequest.__new__(UnifiedQueryRequest)
        object.__setattr__(request, "category", "rks_entity_lookup")
        object.__setattr__(request, "target", 123)
        object.__setattr__(request, "include_evidence", False)
        object.__setattr__(request, "filters", {})
        with pytest.raises(ValueError):
            normalize_request(request)


# ── Deterministic routing ───────────────────────────────────────────────────


class TestRouting:
    def test_single_family_categories_route_to_exactly_one_family(self) -> None:
        for category in (
            "rks_entity_lookup",
            "dependency_node_lookup",
            "historical_event_lookup",
            "change_impact_entity_lookup",
            "advisory_context_item_lookup",
            "cross_artifact_reference_lookup",
        ):
            families = route(category)
            assert len(families) == 1

    def test_declared_multi_family_category_routes_to_multiple_families(self) -> None:
        families = route("change_impact_to_dependency_node")
        assert len(families) > 1

    def test_unsupported_category_fails_closed(self) -> None:
        with pytest.raises(UnsupportedQueryCategoryError):
            route("no_such_category")

    def test_undeclared_multi_family_category_raises_routing_ambiguity(self) -> None:
        bad_table = dict(ROUTING_TABLE)
        bad_table["undeclared_multi_family"] = (
            REPOSITORY_KNOWLEDGE_SNAPSHOT,
            HISTORICAL_MEMORY,
        )
        with pytest.raises(RoutingAmbiguityError):
            route("undeclared_multi_family", table=bad_table)

    def test_routing_is_a_pure_deterministic_function(self) -> None:
        assert route("rks_entity_lookup") == route("rks_entity_lookup")

    def test_no_heuristic_matching_of_category_names(self) -> None:
        # A near-miss category name must not be silently accepted.
        with pytest.raises(UnsupportedQueryCategoryError):
            route("rks_entity_lookup ")  # trailing whitespace
        with pytest.raises(UnsupportedQueryCategoryError):
            route("RKS_ENTITY_LOOKUP")  # case variant


# ── Single-family queries ───────────────────────────────────────────────────


class TestSingleFamilyQueries:
    def test_rks_entity_lookup(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target),
            artifact_paths=paths,
        )
        assert response.result_status == "ok"
        assert len(response.references) == 1
        assert response.references[0]["originating_record"] == target

    def test_dependency_node_lookup(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        graph = _load_json(paths[DEPENDENCY_KNOWLEDGE_GRAPH])
        target = graph["nodes"][0]["node_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="dependency_node_lookup", target=target),
            artifact_paths=paths,
        )
        assert response.result_status == "ok"
        assert response.references[0]["originating_record"] == target

    def test_historical_event_lookup(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[HISTORICAL_MEMORY])
        events = snapshot["historical_events"]
        if not events:
            pytest.skip("no historical events in this fixture generation")
        target = events[0]["event_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="historical_event_lookup", target=target),
            artifact_paths=paths,
        )
        assert response.result_status == "ok"
        assert response.references[0]["originating_record"] == target

    def test_change_impact_entity_lookup(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        report = _load_json(paths[CHANGE_IMPACT])
        target = report["impacted_entities"][0]["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="change_impact_entity_lookup", target=target),
            artifact_paths=paths,
        )
        assert response.result_status == "ok"
        assert response.references[0]["originating_record"] == target

    def test_advisory_context_item_lookup(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        package = _load_json(paths[ADVISORY_CONTEXT])
        item = package["selected_repository_intelligence"][0]
        target = item.get("entity_id") or item.get("capability_id") or item.get("contract_id")
        response = execute_unified_query(
            UnifiedQueryRequest(category="advisory_context_item_lookup", target=target),
            artifact_paths=paths,
        )
        assert response.result_status == "ok"
        assert len(response.references) == 1

    def test_cross_artifact_reference_lookup(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        package = _load_json(paths[CROSS_ARTIFACT_INTEGRATION])
        if not package["entity_resolutions"]:
            pytest.skip("no entity resolutions in this fixture generation")
        target = package["entity_resolutions"][0]["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="cross_artifact_reference_lookup", target=target),
            artifact_paths=paths,
        )
        assert response.result_status == "ok"
        assert response.references[0]["originating_record"] == target


# ── Multi-family queries ────────────────────────────────────────────────────


class TestMultiFamilyQueries:
    def test_change_impact_to_dependency_node(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        package = _load_json(paths[CROSS_ARTIFACT_INTEGRATION])
        if not package["entity_resolutions"]:
            pytest.skip("no entity resolutions in this fixture generation")
        resolution = package["entity_resolutions"][0]
        response = execute_unified_query(
            UnifiedQueryRequest(category="change_impact_to_dependency_node", target=resolution["entity_id"]),
            artifact_paths=paths,
        )
        assert response.result_status == "ok"
        assert response.references[0]["originating_record"] == resolution["resolved_node_id"]
        assert "Cross-Artifact Integration" in response.references[0]["provenance"]["derivation_path"]

    def test_multi_family_query_requires_all_declared_families(self, real_artifacts: dict[str, Path]) -> None:
        # Copy before mutating -- `real_artifacts` is a module-scoped,
        # shared fixture; deleting a key from it directly would corrupt
        # every other test in this module that runs after this one.
        paths = dict(real_artifacts)
        del paths[CROSS_ARTIFACT_INTEGRATION]
        with pytest.raises(SnapshotLoadError):
            execute_unified_query(
                UnifiedQueryRequest(category="change_impact_to_dependency_node", target="anything"),
                artifact_paths=paths,
            )


# ── Unresolved / unsupported routing ────────────────────────────────────────


class TestUnresolvedAndUnsupportedRouting:
    def test_unresolved_identifier_produces_explicit_record(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        response = execute_unified_query(
            UnifiedQueryRequest(category="dependency_node_lookup", target="node:does-not-exist"),
            artifact_paths=paths,
        )
        assert response.result_status == "unknown"
        assert not response.references
        assert response.uncertainty
        assert response.uncertainty[0]["uncertainty_state"] == "unresolved"

    def test_unsupported_query_category_fails_closed(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        with pytest.raises(UnsupportedQueryCategoryError):
            execute_unified_query(
                UnifiedQueryRequest(category="not_a_real_category"),
                artifact_paths=paths,
            )


# ── Identity resolution ─────────────────────────────────────────────────────


class TestIdentityResolution:
    def test_exact_match_required_no_fuzzy_resolution(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        graph = _load_json(paths[DEPENDENCY_KNOWLEDGE_GRAPH])
        real_node_id = graph["nodes"][0]["node_id"]

        near_misses = [
            real_node_id + "/",
            real_node_id.upper(),
            " " + real_node_id,
            real_node_id[:-1],
        ]
        for near_miss in near_misses:
            response = execute_unified_query(
                UnifiedQueryRequest(category="dependency_node_lookup", target=near_miss),
                artifact_paths=paths,
            )
            assert response.result_status == "unknown", f"near-miss {near_miss!r} incorrectly resolved"
            assert response.uncertainty[0]["uncertainty_state"] == "unresolved"

    def test_unresolved_identity_is_explicit_not_omitted(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target="entity:does-not-exist"),
            artifact_paths=paths,
        )
        assert response.uncertainty
        record = response.uncertainty[0]
        assert record["entity_id"] == "entity:does-not-exist"
        assert "unresolved_reason" in record


# ── Provenance completeness ─────────────────────────────────────────────────


class TestProvenanceCompleteness:
    REQUIRED_ELEMENTS = (
        "authoritative_artifact",
        "originating_record",
        "source_locator",
        "schema_version",
        "derivation_path",
        "verification_state",
    )

    def test_all_six_elements_present(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target),
            artifact_paths=paths,
        )
        provenance = response.references[0]["provenance"]
        for element in self.REQUIRED_ELEMENTS:
            assert element in provenance, f"missing provenance element: {element}"

    def test_verification_state_falls_back_to_unknown_not_omitted(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        report = _load_json(paths[CHANGE_IMPACT])
        target = report["impacted_entities"][0]["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="change_impact_entity_lookup", target=target),
            artifact_paths=paths,
        )
        state = response.references[0]["provenance"]["verification_state"]
        assert state["state_value"] in {"unknown", "verified", "unverified"}


# ── Evidence preservation ───────────────────────────────────────────────────


class TestEvidencePreservation:
    def test_evidence_omitted_by_default(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target),
            artifact_paths=paths,
        )
        assert response.evidence == ()

    def test_evidence_verbatim_when_requested(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        source_record = snapshot["architectural_entities"][0]
        target = source_record["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target, include_evidence=True),
            artifact_paths=paths,
        )
        assert response.evidence
        assert response.evidence[0]["content"] == source_record


# ── Uncertainty / limitation propagation ────────────────────────────────────


class TestUncertaintyAndLimitationPropagation:
    def test_limitations_propagate_from_source_artifact(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target),
            artifact_paths=paths,
        )
        assert response.limitations
        source_descriptions = {
            item.get("limitation_description") for item in snapshot["snapshot_limitations"]
        }
        response_descriptions = {item.get("limitation_description") for item in response.limitations}
        assert response_descriptions <= source_descriptions | response_descriptions
        assert source_descriptions & response_descriptions

    def test_uncertainty_present_on_miss_absent_on_hit(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        hit = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target), artifact_paths=paths
        )
        miss = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target="entity:nope"), artifact_paths=paths
        )
        assert hit.uncertainty == ()
        assert miss.uncertainty != ()


# ── Boundary disclosure attachment ──────────────────────────────────────────


class TestBoundaryDisclosureAttachment:
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

    def test_all_nine_fields_present_and_true(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target),
            artifact_paths=paths,
        )
        for field_name in self.REQUIRED_FIELDS:
            assert response.boundary_disclosures.get(field_name) is True

    def test_disclosures_present_even_on_unresolved_query(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target="entity:nope"),
            artifact_paths=paths,
        )
        for field_name in self.REQUIRED_FIELDS:
            assert response.boundary_disclosures.get(field_name) is True


# ── Deterministic responses ─────────────────────────────────────────────────


class TestDeterministicResponses:
    def test_equivalent_query_produces_equivalent_response(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        request = UnifiedQueryRequest(category="rks_entity_lookup", target=target)
        response_a = execute_unified_query(request, artifact_paths=paths).to_dict()
        response_b = execute_unified_query(request, artifact_paths=paths).to_dict()
        assert response_a == response_b

    def test_response_ordering_is_identifier_lexicographic(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target, include_evidence=True),
            artifact_paths=paths,
        )
        record_ids = [r["originating_record"] for r in response.references]
        assert record_ids == sorted(record_ids)
        evidence_ids = [e.get("record_id", "") for e in response.evidence]
        assert evidence_ids == sorted(evidence_ids)


# ── Fail-closed behavior / exception handling ───────────────────────────────


class TestFailClosedBehavior:
    def test_missing_artifact_fails_closed(self, tmp_path: Path) -> None:
        with pytest.raises(SnapshotLoadError):
            execute_unified_query(
                UnifiedQueryRequest(category="rks_entity_lookup", target="x"),
                artifact_paths={REPOSITORY_KNOWLEDGE_SNAPSHOT: tmp_path / "does-not-exist.json"},
            )

    def test_incompatible_artifact_fails_closed(self, tmp_path: Path) -> None:
        bad_path = tmp_path / "bad_dkg.json"
        bad_path.write_text(json.dumps({"snapshot_identity": {"executable_schema_version": "wrong"}}))
        with pytest.raises(SnapshotCompatibilityError):
            execute_unified_query(
                UnifiedQueryRequest(category="dependency_node_lookup", target="x"),
                artifact_paths={DEPENDENCY_KNOWLEDGE_GRAPH: bad_path},
            )

    def test_malformed_request_fails_closed(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        with pytest.raises(MalformedRequestError):
            execute_unified_query(UnifiedQueryRequest(category=""), artifact_paths=paths)

    def test_no_silent_omission_on_unresolved_target(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target="entity:ghost"),
            artifact_paths=paths,
        )
        # A miss must be recorded, never silently dropped with an
        # otherwise-empty, unremarkable "ok" response.
        assert response.result_status == "unknown"
        assert response.uncertainty


# ── Read-only guarantees ────────────────────────────────────────────────────


class TestReadOnlyGuarantees:
    def test_artifacts_unchanged_after_query(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        checksums_before = {family: _sha256(path) for family, path in paths.items()}

        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target, include_evidence=True),
            artifact_paths=paths,
        )

        checksums_after = {family: _sha256(path) for family, path in paths.items()}
        assert checksums_before == checksums_after

    def test_no_new_files_written_by_query(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        fixtures_root = next(iter(paths.values())).parent.parent
        before = {p for p in fixtures_root.rglob("*") if p.is_file()}
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target),
            artifact_paths=paths,
        )
        after = {p for p in fixtures_root.rglob("*") if p.is_file()}
        assert before == after


# ── Compatibility / regression ──────────────────────────────────────────────


class TestCompatibilityRegression:
    def test_response_is_closed_six_category_shape(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target),
            artifact_paths=paths,
        )
        data = response.to_dict()
        allowed_keys = {
            "query_metadata",
            "result_status",
            "references",
            "evidence",
            "limitations",
            "uncertainty",
            "boundary_disclosures",
            "boundary_notes",
            "determinism",
        }
        assert set(data.keys()) <= allowed_keys

    def test_unified_query_response_is_a_dataclass_instance(self, real_artifacts: dict[str, Path]) -> None:
        paths = real_artifacts
        snapshot = _load_json(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]
        response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target),
            artifact_paths=paths,
        )
        assert isinstance(response, UnifiedQueryResponse)

    def test_track_130_cross_artifact_integration_unaffected(self, real_artifacts: dict[str, Path]) -> None:
        """Independently re-confirms Track 130's own generator still
        produces its own real, unmodified output shape after this
        package's addition (no shared mutable state, no monkeypatching)."""
        paths = real_artifacts
        package = _load_json(paths[CROSS_ARTIFACT_INTEGRATION])
        assert "entity_resolutions" in package
        assert "unresolved_identities" in package
        assert "boundary_disclosures" in package

    def test_track_121_query_layer_unaffected(self) -> None:
        """Confirms Track 121's own QueryRequest/SUPPORTED_QUERY_CATEGORIES
        remain untouched by this package's addition."""
        from pcae.repository_intelligence.query.query_request import (
            SUPPORTED_QUERY_CATEGORIES,
        )

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

    def test_rks_entity_lookup_matches_track_121_query_engine_directly(
        self, real_artifacts: dict[str, Path]
    ) -> None:
        """The rks_entity_lookup handler must delegate to, not diverge
        from, Track 121's own existing query engine."""
        from pcae.repository_intelligence.query.query_engine import evaluate_query
        from pcae.repository_intelligence.query.query_request import QueryRequest
        from pcae.repository_intelligence.query.snapshot_loader import load_snapshot

        paths = real_artifacts
        snapshot = load_snapshot(paths[REPOSITORY_KNOWLEDGE_SNAPSHOT])
        target = snapshot["architectural_entities"][0]["entity_id"]

        direct_result = evaluate_query(snapshot, QueryRequest(category="entity_lookup", target=target))
        unified_response = execute_unified_query(
            UnifiedQueryRequest(category="rks_entity_lookup", target=target),
            artifact_paths=paths,
        )
        assert len(unified_response.references) == len(direct_result.records)
        assert unified_response.references[0]["originating_record"] == direct_result.records[0]["entity_id"]
