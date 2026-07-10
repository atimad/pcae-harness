from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.repository_intelligence.change_impact import (
    ChangeImpactRequest,
    build_change_impact_report,
)
from pcae.repository_intelligence.cross_artifact_integration import (
    IntegrationGenerationError,
    build_integration_content,
    generate_cross_artifact_integration,
)
from pcae.repository_intelligence.cross_artifact_integration.integration_validation import (
    validate_integration_package,
)
from pcae.repository_intelligence.dependency_graph import generate_dependency_graph
from pcae.repository_intelligence.snapshot_generator import generate_snapshot

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _real_artifacts(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Generate real RKS, DKG, and Change Impact artifacts against the
    real repository (mirroring 126e/127e's own established fixture
    pattern of testing against real data, not only synthetic
    fixtures)."""
    snapshot_result = generate_snapshot(REPO_ROOT, output_dir=tmp_path / "rks")
    snapshot_path = Path(snapshot_result["latest_path"])

    graph_result = generate_dependency_graph(
        snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "dkg"
    )
    dkg_path = Path(graph_result["latest_path"])

    snapshot = _load_json(snapshot_path)
    entity_ids = [e["entity_id"] for e in snapshot["architectural_entities"]][:3]
    request = ChangeImpactRequest(
        requested_change="test change for 130E fixtures",
        repository_scope=str(snapshot_path),
        target_entities=tuple(entity_ids),
    )
    report = build_change_impact_report(snapshot_path, request)
    change_impact_path = tmp_path / "change_impact.json"
    change_impact_path.write_text(json.dumps(report.to_dict()))

    return snapshot_path, dkg_path, change_impact_path


# ── Determinism ──────────────────────────────────────────────────────────────


class TestDeterministicIntegrationGeneration:
    def test_equivalent_inputs_produce_equivalent_package(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)

        result_a = generate_cross_artifact_integration(
            change_impact_path, dkg_path, repo_root=REPO_ROOT, output_dir=tmp_path / "int_a"
        )
        result_b = generate_cross_artifact_integration(
            change_impact_path, dkg_path, repo_root=REPO_ROOT, output_dir=tmp_path / "int_b"
        )
        package_a = _load_json(Path(result_a["latest_path"]))
        package_b = _load_json(Path(result_b["latest_path"]))

        package_a["integration_metadata"]["generated_at_utc"] = "TS"
        package_b["integration_metadata"]["generated_at_utc"] = "TS"

        assert package_a == package_b

    def test_counts_are_stable_across_runs(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        result_a = generate_cross_artifact_integration(
            change_impact_path, dkg_path, repo_root=REPO_ROOT, output_dir=tmp_path / "int_a"
        )
        result_b = generate_cross_artifact_integration(
            change_impact_path, dkg_path, repo_root=REPO_ROOT, output_dir=tmp_path / "int_b"
        )
        assert result_a["entity_resolution_count"] == result_b["entity_resolution_count"]
        assert result_a["dependency_context_count"] == result_b["dependency_context_count"]
        assert result_a["unresolved_identity_count"] == result_b["unresolved_identity_count"]


# ── Relationship / identity resolution ──────────────────────────────────────


class TestChangeImpactDependencyGraphIntegration:
    def test_entities_present_in_dkg_are_resolved(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        assert content["entity_resolutions"], "expected at least one resolvable entity in real repo data"
        assert content["unresolved_identities"] == []

    def test_dependency_context_reuses_existing_schema_shape(self, tmp_path: Path) -> None:
        """130D Section 6: populate dependency_context_reference, don't
        invent a parallel structure -- required fields must match the
        frozen 119U $def exactly."""
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        assert content["dependency_context"], "expected at least one dependency_context entry"
        for ctx in content["dependency_context"]:
            assert set(ctx.keys()) == {
                "context_id",
                "context_type",
                "reference_locator",
                "source_attribution",
                "limitations",
            }
            assert ctx["context_type"] in ("graph_node", "graph_edge", "dependency_knowledge_graph_snapshot", "dependency_claim", "unknown")
            assert set(ctx["reference_locator"].keys()) == {"locator_type", "locator_value"}

    def test_unresolved_entity_never_guessed(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        report = _load_json(change_impact_path)
        report["impacted_entities"].append(
            {"entity_id": "entity:does/not/exist.py", "entity_name": "ghost", "entity_path": "does/not/exist.py"}
        )
        bad_path = tmp_path / "change_impact_with_ghost.json"
        bad_path.write_text(json.dumps(report))

        content = build_integration_content(
            bad_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        unresolved_ids = {u["entity_id"] for u in content["unresolved_identities"]}
        assert "entity:does/not/exist.py" in unresolved_ids
        resolved_ids = {r["entity_id"] for r in content["entity_resolutions"]}
        assert "entity:does/not/exist.py" not in resolved_ids

    def test_no_fuzzy_or_partial_matching(self, tmp_path: Path) -> None:
        """An entity_path that is a near-miss (case difference, trailing
        slash) of a real DKG node must remain unresolved, never fuzzy-matched."""
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        report = _load_json(change_impact_path)
        real_path = report["impacted_entities"][0]["entity_path"]
        near_miss_path = real_path.upper() + "  "
        report["impacted_entities"] = [
            {"entity_id": "entity:near-miss", "entity_name": "near-miss", "entity_path": near_miss_path}
        ]
        near_miss_ci = tmp_path / "change_impact_near_miss.json"
        near_miss_ci.write_text(json.dumps(report))

        content = build_integration_content(
            near_miss_ci, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        assert content["entity_resolutions"] == []
        assert len(content["unresolved_identities"]) == 1


# ── Identifier preservation ──────────────────────────────────────────────────


class TestIdentifierPreservation:
    def test_no_replacement_identifiers_are_minted(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        dkg = _load_json(dkg_path)
        real_node_ids = {n["node_id"] for n in dkg["nodes"]}

        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        for resolution in content["entity_resolutions"]:
            assert resolution["resolved_node_id"] in real_node_ids

    def test_entity_id_cited_verbatim(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        change_impact = _load_json(change_impact_path)
        real_entity_ids = {e["entity_id"] for e in change_impact["impacted_entities"]}

        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        for resolution in content["entity_resolutions"]:
            assert resolution["entity_id"] in real_entity_ids


# ── Provenance / evidence / uncertainty / limitation / boundary ─────────────


class TestProvenancePreservation:
    def test_every_dependency_context_entry_has_full_provenance(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        for ctx in content["dependency_context"]:
            for attribution in ctx["source_attribution"]:
                assert attribution["source_id"]
                assert attribution["source_locator"]["locator_value"]
                assert attribution["source_verification_state"]
                assert attribution["source_limitations"]

    def test_referenced_artifacts_carry_schema_version(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        dkg_ref = next(
            r for r in content["referenced_artifacts"] if r["artifact_type"] == "dependency_knowledge_graph_snapshot"
        )
        assert dkg_ref["executable_schema_version"] == "119S.1.0-json-schema"


class TestLimitationPropagation:
    def test_integration_limitations_present(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        assert content["limitations"]
        for ctx in content["dependency_context"]:
            assert ctx["limitations"]


class TestBoundaryDisclosurePropagation:
    def test_boundary_disclosures_all_true(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        disclosures = content["boundary_disclosures"]
        for field in (
            "read_only",
            "no_execution",
            "non_decision",
            "advisory_non_authority",
            "decision_evaluation_required",
            "no_repository_mutation",
            "no_lifecycle_mutation",
            "no_evidence_replacement",
            "no_repository_state_replacement",
        ):
            assert disclosures[field] is True

    def test_boundary_notes_disclose_derivative_and_human_approval(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        notes_text = " ".join(content["boundary_notes"]).lower()
        assert "derivative" in notes_text
        assert "human approval" in notes_text


# ── Validation / determinism-of-ordering ─────────────────────────────────────


class TestValidation:
    def test_valid_package_passes_validation(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        validate_integration_package(content)  # must not raise

    def test_rejects_duplicate_context_ids(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        if not content["dependency_context"]:
            pytest.skip("no dependency_context entries generated for this repository state")
        content["dependency_context"].append(dict(content["dependency_context"][0]))
        with pytest.raises(IntegrationGenerationError):
            validate_integration_package(content)

    def test_rejects_dangling_entity_resolution_reference(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        content = build_integration_content(
            change_impact_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        if not content["entity_resolutions"]:
            pytest.skip("no entity_resolutions generated for this repository state")
        content["entity_resolutions"][0]["dependency_context_reference"] = "context:does-not-exist"
        with pytest.raises(IntegrationGenerationError):
            validate_integration_package(content)


# ── Fail-closed behavior ──────────────────────────────────────────────────────


class TestFailClosedBehavior:
    def test_missing_change_impact_file_fails_closed(self, tmp_path: Path) -> None:
        _, dkg_path, _ = _real_artifacts(tmp_path)
        with pytest.raises(IntegrationGenerationError, match="not found"):
            build_integration_content(
                tmp_path / "does-not-exist.json", dkg_path, generated_at_utc="2026-01-01T00:00:00Z"
            )

    def test_missing_dependency_graph_file_fails_closed(self, tmp_path: Path) -> None:
        _, _, change_impact_path = _real_artifacts(tmp_path)
        with pytest.raises(IntegrationGenerationError, match="not found"):
            build_integration_content(
                change_impact_path, tmp_path / "does-not-exist.json", generated_at_utc="2026-01-01T00:00:00Z"
            )

    def test_corrupted_change_impact_fails_closed(self, tmp_path: Path) -> None:
        _, dkg_path, _ = _real_artifacts(tmp_path)
        bad_path = tmp_path / "corrupted.json"
        bad_path.write_text("{not valid json")
        with pytest.raises(IntegrationGenerationError, match="not valid JSON"):
            build_integration_content(bad_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z")

    def test_change_impact_missing_impacted_entities_fails_closed(self, tmp_path: Path) -> None:
        _, dkg_path, _ = _real_artifacts(tmp_path)
        bad_path = tmp_path / "no_entities.json"
        bad_path.write_text(json.dumps({"foo": "bar"}))
        with pytest.raises(IntegrationGenerationError, match="impacted_entities"):
            build_integration_content(bad_path, dkg_path, generated_at_utc="2026-01-01T00:00:00Z")

    def test_dkg_missing_snapshot_identity_fails_closed(self, tmp_path: Path) -> None:
        _, _, change_impact_path = _real_artifacts(tmp_path)
        bad_dkg = tmp_path / "bad_dkg.json"
        bad_dkg.write_text(json.dumps({"nodes": []}))
        with pytest.raises(IntegrationGenerationError, match="snapshot_identity"):
            build_integration_content(change_impact_path, bad_dkg, generated_at_utc="2026-01-01T00:00:00Z")

    def test_dkg_incompatible_schema_version_fails_closed(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        dkg = _load_json(dkg_path)
        dkg["snapshot_identity"]["executable_schema_version"] = "999Z.9.9-json-schema"
        bad_dkg = tmp_path / "incompatible_dkg.json"
        bad_dkg.write_text(json.dumps(dkg))
        with pytest.raises(IntegrationGenerationError, match="unsupported"):
            build_integration_content(change_impact_path, bad_dkg, generated_at_utc="2026-01-01T00:00:00Z")

    def test_dkg_missing_nodes_fails_closed(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        dkg = _load_json(dkg_path)
        del dkg["nodes"]
        bad_dkg = tmp_path / "no_nodes_dkg.json"
        bad_dkg.write_text(json.dumps(dkg))
        with pytest.raises(IntegrationGenerationError, match="nodes"):
            build_integration_content(change_impact_path, bad_dkg, generated_at_utc="2026-01-01T00:00:00Z")

    def test_optional_reference_artifact_invalid_fails_closed(self, tmp_path: Path) -> None:
        rks_path, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        bad_rks = tmp_path / "bad_rks_ref.json"
        bad_rks.write_text(json.dumps({"no_identity": True}))
        with pytest.raises(IntegrationGenerationError, match="snapshot_identity"):
            build_integration_content(
                change_impact_path,
                dkg_path,
                generated_at_utc="2026-01-01T00:00:00Z",
                repository_knowledge_snapshot_path=bad_rks,
            )


# ── Read-only guarantees ──────────────────────────────────────────────────────


class TestReadOnlyGuarantees:
    def test_source_artifacts_never_mutated(self, tmp_path: Path) -> None:
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        dkg_before = dkg_path.read_bytes()
        ci_before = change_impact_path.read_bytes()

        generate_cross_artifact_integration(
            change_impact_path, dkg_path, repo_root=REPO_ROOT, output_dir=tmp_path / "int_out"
        )

        assert dkg_path.read_bytes() == dkg_before
        assert change_impact_path.read_bytes() == ci_before

    def test_real_repository_generation_never_mutates_tasks_done(self, tmp_path: Path) -> None:
        tasks_done = REPO_ROOT / "tasks" / "done"
        before = sorted(p.name for p in tasks_done.glob("*.md"))
        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        generate_cross_artifact_integration(
            change_impact_path, dkg_path, repo_root=REPO_ROOT, output_dir=tmp_path / "int_out"
        )
        after = sorted(p.name for p in tasks_done.glob("*.md"))
        assert before == after


# ── No reasoning / no execution ──────────────────────────────────────────────


class TestNoReasoningNoExecutionModules:
    def test_no_reasoning_module_exists(self) -> None:
        with pytest.raises(ModuleNotFoundError):
            import pcae.repository_intelligence.cross_artifact_integration.reasoning  # noqa: F401

    def test_no_traversal_module_exists(self) -> None:
        with pytest.raises(ModuleNotFoundError):
            import pcae.repository_intelligence.cross_artifact_integration.traversal  # noqa: F401

    def test_builder_module_has_no_execution_related_imports(self) -> None:
        import ast

        source_path = (
            REPO_ROOT
            / "src"
            / "pcae"
            / "repository_intelligence"
            / "cross_artifact_integration"
            / "integration_builder.py"
        )
        tree = ast.parse(source_path.read_text())
        forbidden = {"subprocess", "os.system", "shell_gate"}
        found: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module)
        assert not (found & forbidden), f"forbidden imports found: {found & forbidden}"


# ── CLI ────────────────────────────────────────────────────────────────────


class TestCLIGeneration:
    def test_cli_generate_writes_latest_and_timestamped(self, tmp_path: Path) -> None:
        import argparse

        from pcae.commands.repository_intelligence import (
            run_repository_intelligence_cross_artifact_integration_generate,
        )

        _, dkg_path, change_impact_path = _real_artifacts(tmp_path)
        output_dir = tmp_path / "cli_output"
        args = argparse.Namespace(
            change_impact=str(change_impact_path),
            dependency_graph=str(dkg_path),
            repository_knowledge_snapshot=None,
            historical_memory=None,
            advisory_context=None,
            output=str(output_dir),
            pretty=False,
            json=True,
        )
        rc = run_repository_intelligence_cross_artifact_integration_generate(args)
        assert rc == 0
        assert (output_dir / "latest.json").exists()

    def test_cli_generate_fails_closed_on_missing_input(self, tmp_path: Path) -> None:
        import argparse

        from pcae.commands.repository_intelligence import (
            run_repository_intelligence_cross_artifact_integration_generate,
        )

        args = argparse.Namespace(
            change_impact=str(tmp_path / "missing.json"),
            dependency_graph=str(tmp_path / "missing_dkg.json"),
            repository_knowledge_snapshot=None,
            historical_memory=None,
            advisory_context=None,
            output=str(tmp_path / "cli_output_fail"),
            pretty=False,
            json=False,
        )
        rc = run_repository_intelligence_cross_artifact_integration_generate(args)
        assert rc == 1
