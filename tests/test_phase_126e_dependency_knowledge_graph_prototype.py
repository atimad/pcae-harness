from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.repository_intelligence.dependency_graph import (
    GraphGenerationError,
    build_graph_content,
    generate_dependency_graph,
)
from pcae.repository_intelligence.dependency_graph.graph_validation import (
    validate_graph,
)
from pcae.repository_intelligence.snapshot_generator import generate_snapshot

REPO_ROOT = Path(__file__).resolve().parent.parent


def _snapshot_path(tmp_path: Path) -> Path:
    result = generate_snapshot(REPO_ROOT, output_dir=tmp_path / "snapshot")
    return Path(result["latest_path"])


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _write_snapshot(tmp_path: Path, snapshot: dict, name: str = "snapshot.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(snapshot, sort_keys=True))
    return path


class TestDeterministicGraphGeneration:
    def test_equivalent_snapshot_produces_equivalent_graph(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        result_a = generate_dependency_graph(
            snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "graph_a"
        )
        result_b = generate_dependency_graph(
            snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "graph_b"
        )
        graph_a = _load_json(Path(result_a["latest_path"]))
        graph_b = _load_json(Path(result_b["latest_path"]))

        graph_a["envelope"]["generated_at_utc"] = "TS"
        graph_b["envelope"]["generated_at_utc"] = "TS"
        graph_a["snapshot_identity"]["snapshot_created_at_utc"] = "TS"
        graph_b["snapshot_identity"]["snapshot_created_at_utc"] = "TS"

        assert graph_a == graph_b

    def test_node_and_edge_counts_are_stable(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        result_a = generate_dependency_graph(
            snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "graph_a"
        )
        result_b = generate_dependency_graph(
            snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "graph_b"
        )
        assert result_a["node_count"] == result_b["node_count"]
        assert result_a["edge_count"] == result_b["edge_count"]


class TestGraphModel:
    def test_repository_root_node_present(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        node_ids = {node["node_id"] for node in graph["nodes"]}
        assert "node:repository" in node_ids
        repository_node = next(n for n in graph["nodes"] if n["node_id"] == "node:repository")
        assert repository_node["node_type"] == "repository"

    def test_source_file_entities_map_to_file_node_type(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = _load_json(snapshot_path)
        source_file_entities = [
            e for e in snapshot["architectural_entities"] if e["entity_type"] == "source_file"
        ]
        assert source_file_entities, "expected at least one source_file entity in a real snapshot"

        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        file_nodes = [n for n in graph["nodes"] if n["node_type"] == "file"]
        assert len(file_nodes) == len(source_file_entities)

    def test_directory_entities_map_to_module_node_type(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = _load_json(snapshot_path)
        module_entities = [
            e for e in snapshot["architectural_entities"] if e["entity_type"] == "module"
        ]
        assert module_entities

        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        module_nodes = [n for n in graph["nodes"] if n["node_type"] == "module"]
        assert len(module_nodes) == len(module_entities)

    def test_all_non_root_edges_are_containment_related_to(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        assert graph["edges"], "expected at least one containment edge"
        for edge in graph["edges"]:
            assert edge["edge_type"] == "related_to"
            assert edge["source_node_id"] == "node:repository"

    def test_no_import_or_depends_on_edges_from_current_generator(self, tmp_path: Path) -> None:
        # Track 120 does not parse imports; this is an inherited
        # limitation (126D Section 5.2), not a builder defect.
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        depends_on_edges = [e for e in graph["edges"] if e["edge_type"] == "depends_on"]
        assert depends_on_edges == []
        unknown_subjects = {u["unknown_subject"] for u in graph["unknowns_gaps"]}
        assert "import and dependency relationships" in unknown_subjects

    def test_no_class_or_function_nodes(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        node_types = {n["node_type"] for n in graph["nodes"]}
        assert "class" not in node_types
        assert "function" not in node_types
        unknown_subjects = {u["unknown_subject"] for u in graph["unknowns_gaps"]}
        assert "class- and function-level entities" in unknown_subjects

    def test_graph_completeness_state_is_partial(self, tmp_path: Path) -> None:
        # Resolves 126C Finding 3: v1 output must never claim
        # complete_claimed_by_source.
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        assert graph["graph_metadata"]["graph_completeness_state"] == "partial"


class TestNodeValidation:
    def test_valid_graph_passes_validation(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        validate_graph(graph)  # must not raise

    def test_rejects_duplicate_node_identifiers(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        graph["nodes"].append(dict(graph["nodes"][0]))
        with pytest.raises(GraphGenerationError, match="duplicate node_id"):
            validate_graph(graph)

    def test_rejects_invalid_node_type(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        graph["nodes"][0]["node_type"] = "not_a_real_node_type"
        with pytest.raises(GraphGenerationError, match="invalid node_type"):
            validate_graph(graph)


class TestEdgeValidation:
    def test_rejects_duplicate_edge_identifiers(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        graph["edges"].append(dict(graph["edges"][0]))
        with pytest.raises(GraphGenerationError, match="duplicate edge_id"):
            validate_graph(graph)

    def test_rejects_invalid_edge_type(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        graph["edges"][0]["edge_type"] = "not_a_real_edge_type"
        with pytest.raises(GraphGenerationError, match="invalid edge_type"):
            validate_graph(graph)

    def test_rejects_invalid_edge_endpoint(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        graph["edges"][0]["target_node_id"] = "node:does-not-exist"
        with pytest.raises(GraphGenerationError, match="unknown target_node_id"):
            validate_graph(graph)


class TestFailClosedBehavior:
    def test_missing_snapshot_file_fails_closed(self, tmp_path: Path) -> None:
        with pytest.raises(GraphGenerationError):
            build_graph_content(tmp_path / "nonexistent.json", generated_at_utc="2026-01-01T00:00:00Z")

    def test_unsupported_schema_version_fails_closed(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = _load_json(snapshot_path)
        snapshot["snapshot_identity"]["executable_schema_version"] = "999Z.9.9-json-schema"
        bad_path = _write_snapshot(tmp_path, snapshot, name="bad_version.json")
        with pytest.raises(GraphGenerationError):
            build_graph_content(bad_path, generated_at_utc="2026-01-01T00:00:00Z")

    def test_missing_architectural_entities_fails_closed(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = _load_json(snapshot_path)
        snapshot["architectural_entities"] = []
        bad_path = _write_snapshot(tmp_path, snapshot, name="empty_entities.json")
        with pytest.raises(GraphGenerationError, match="no architectural entities"):
            build_graph_content(bad_path, generated_at_utc="2026-01-01T00:00:00Z")

    def test_empty_snapshot_limitations_surfaces_query_layer_fallback_note(
        self, tmp_path: Path
    ) -> None:
        # The Track 121 Query Layer's limitation_lookup category always
        # supplies a synthetic "missing_data" limitation note when a
        # snapshot declares none (established behavior already relied
        # on identically by Track 122/123 consumers) -- so this does
        # not fail closed at the graph layer. Instead, verify the
        # fallback note is honestly surfaced rather than silently
        # dropped, preserving the fail-closed *spirit* without
        # duplicating Query Layer behavior this builder does not own.
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = _load_json(snapshot_path)
        snapshot["snapshot_limitations"] = []
        bad_path = _write_snapshot(tmp_path, snapshot, name="no_limitations.json")
        graph = build_graph_content(bad_path, generated_at_utc="2026-01-01T00:00:00Z")
        descriptions = {item.get("limitation_description", "") for item in graph["snapshot_limitations"]}
        assert any("no limitation records" in d.lower() for d in descriptions)

    def test_missing_architectural_entities_key_fails_closed(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = _load_json(snapshot_path)
        del snapshot["architectural_entities"]
        bad_path = _write_snapshot(tmp_path, snapshot, name="missing_entities_key.json")
        with pytest.raises(GraphGenerationError):
            build_graph_content(bad_path, generated_at_utc="2026-01-01T00:00:00Z")

    def test_missing_boundary_disclosures_fails_closed(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = _load_json(snapshot_path)
        snapshot["boundary_disclosures"] = {}
        snapshot["disclaimers"] = {}
        bad_path = _write_snapshot(tmp_path, snapshot, name="no_boundary.json")
        with pytest.raises(GraphGenerationError):
            build_graph_content(bad_path, generated_at_utc="2026-01-01T00:00:00Z")

    def test_missing_repository_commit_fails_closed(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = _load_json(snapshot_path)
        snapshot["envelope"]["repository_context"]["repository_commit"] = None
        bad_path = _write_snapshot(tmp_path, snapshot, name="no_commit.json")
        with pytest.raises(GraphGenerationError, match="repository_commit"):
            build_graph_content(bad_path, generated_at_utc="2026-01-01T00:00:00Z")


class TestSerializationDeterminism:
    def test_persisted_graph_is_sorted_and_stable(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        result = generate_dependency_graph(
            snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "graph"
        )
        latest_text = Path(result["latest_path"]).read_text()
        # serialize_deterministic_json(pretty=False) => compact, sorted keys.
        assert '"nodes"' in latest_text
        reparsed = json.loads(latest_text)
        node_ids = [n["node_id"] for n in reparsed["nodes"]]
        assert node_ids == sorted(node_ids)
        edge_ids = [e["edge_id"] for e in reparsed["edges"]]
        assert edge_ids == sorted(edge_ids)

    def test_pretty_and_compact_serialization_both_valid_json(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        compact_result = generate_dependency_graph(
            snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "compact", pretty=False
        )
        pretty_result = generate_dependency_graph(
            snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "pretty", pretty=True
        )
        compact_text = Path(compact_result["latest_path"]).read_text()
        pretty_text = Path(pretty_result["latest_path"]).read_text()
        assert "\n" not in compact_text
        assert "\n" in pretty_text
        assert json.loads(compact_text) == json.loads(pretty_text)


class TestPersistence:
    def test_latest_and_timestamped_files_both_written(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        result = generate_dependency_graph(
            snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "graph"
        )
        assert Path(result["latest_path"]).is_file()
        assert Path(result["graph_path"]).is_file()
        assert Path(result["latest_path"]) != Path(result["graph_path"])

    def test_persistence_never_mutates_source_snapshot(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        before = snapshot_path.read_text()
        generate_dependency_graph(snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "graph")
        after = snapshot_path.read_text()
        assert before == after

    def test_default_output_directory_distinct_from_snapshot_directory(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        result = generate_dependency_graph(
            snapshot_path, repo_root=tmp_path, output_dir=None
        )
        graph_path = Path(result["latest_path"])
        assert "dependency-graph" in str(graph_path)
        assert graph_path != snapshot_path


class TestProvenanceLimitationBoundaryPropagation:
    def test_every_node_has_source_attribution(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        for node in graph["nodes"]:
            assert node["source_attribution"]

    def test_every_edge_has_source_attribution(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        for edge in graph["edges"]:
            assert edge["source_attribution"]

    def test_every_node_and_edge_has_limitations(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        for node in graph["nodes"]:
            assert node["limitations"]
        for edge in graph["edges"]:
            assert edge["limitations"]

    def test_boundary_disclosures_and_disclaimer_present(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        assert graph["boundary_disclosures"]
        assert graph["disclaimers"]
        assert graph["dependency_knowledge_graph_snapshot_disclaimer"]

    def test_inherited_snapshot_limitations_propagate(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = _load_json(snapshot_path)
        source_limitation_descriptions = {
            item["limitation_description"] for item in snapshot["snapshot_limitations"]
        }
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        graph_limitation_descriptions = {
            item["limitation_description"] for item in graph["snapshot_limitations"]
        }
        assert source_limitation_descriptions.issubset(graph_limitation_descriptions)


class TestSchemaRequiredFieldConformance:
    """Independent structural check against the frozen 119S/119T schema.

    No jsonschema validator library is available in this environment
    (consistent with the rest of the 119-124 line); this mirrors the
    scripted required-field/enum checks used throughout that line.
    """

    def test_all_required_top_level_fields_present(self, tmp_path: Path) -> None:
        import json as _json

        schema_path = (
            REPO_ROOT
            / "schemas"
            / "repository_intelligence"
            / "artifacts"
            / "dependency_knowledge_graph_snapshot.schema.json"
        )
        schema = _json.loads(schema_path.read_text())
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        for field in schema["required"]:
            assert field in graph, f"missing required top-level field: {field}"

    def test_graph_node_required_fields_present(self, tmp_path: Path) -> None:
        import json as _json

        schema_path = (
            REPO_ROOT
            / "schemas"
            / "repository_intelligence"
            / "artifacts"
            / "dependency_knowledge_graph_snapshot.schema.json"
        )
        schema = _json.loads(schema_path.read_text())
        required = schema["$defs"]["graph_node"]["required"]
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        for node in graph["nodes"]:
            for field in required:
                assert field in node, f"node {node.get('node_id')} missing {field}"

    def test_graph_edge_required_fields_present(self, tmp_path: Path) -> None:
        import json as _json

        schema_path = (
            REPO_ROOT
            / "schemas"
            / "repository_intelligence"
            / "artifacts"
            / "dependency_knowledge_graph_snapshot.schema.json"
        )
        schema = _json.loads(schema_path.read_text())
        required = schema["$defs"]["graph_edge"]["required"]
        snapshot_path = _snapshot_path(tmp_path)
        graph = build_graph_content(snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")
        for edge in graph["edges"]:
            for field in required:
                assert field in edge, f"edge {edge.get('edge_id')} missing {field}"


class TestNoTraversalNoReasoningNoExecution:
    def test_no_graph_traversal_module_exists(self) -> None:
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(
                "pcae.repository_intelligence.dependency_graph.graph_traversal"
            )

    def test_no_query_module_exists(self) -> None:
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(
                "pcae.repository_intelligence.dependency_graph.graph_query"
            )

    def test_builder_module_has_no_execution_related_imports(self) -> None:
        import ast

        module_path = (
            REPO_ROOT
            / "src"
            / "pcae"
            / "repository_intelligence"
            / "dependency_graph"
            / "graph_builder.py"
        )
        tree = ast.parse(module_path.read_text())
        forbidden = {"subprocess", "os.system", "shell_gate"}
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_names.add(node.module)
        assert not (imported_names & forbidden)
