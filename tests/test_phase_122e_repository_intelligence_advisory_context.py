from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.advisory.context import (
    AdvisoryContextBuilderError,
    AdvisoryContextRequest,
    RepositoryIntelligenceContextPackage,
    build_advisory_context,
    serialize_context_package,
)
from pcae.advisory.context.context_package import NON_AUTHORITY_DISCLAIMER
from pcae.advisory.context.context_validation import (
    AdvisoryContextValidationError,
    validate_context_request,
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


def _first_entity_id(tmp_path: Path) -> str:
    snapshot = _load_json(_snapshot_path(tmp_path))
    return snapshot["architectural_entities"][0]["entity_id"]


# ── Deterministic context assembly / Query Layer integration ────────────


def test_entity_context_preserves_attribution_limitations_and_boundaries(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    request = AdvisoryContextRequest(
        category="entity_lookup", advisory_purpose="test purpose", target=target
    )

    package = build_advisory_context(path, request)

    assert isinstance(package, RepositoryIntelligenceContextPackage)
    assert [record["entity_id"] for record in package.selected_repository_intelligence] == [
        target
    ]
    assert package.attribution_bundle
    assert all(item["source_id"] for item in package.attribution_bundle)
    assert package.limitation_bundle
    assert package.boundary_disclosure_bundle["boundary_disclosures"]
    assert package.boundary_disclosure_bundle["disclaimers"]
    assert (
        package.boundary_disclosure_bundle["non_authority_disclaimer"]
        == NON_AUTHORITY_DISCLAIMER
    )
    assert package.context_metadata["advisory_purpose"] == "test purpose"
    assert package.context_metadata["query_request"] == {
        "category": "entity_lookup",
        "target": target,
    }
    assert (
        package.context_metadata["source_artifact"]["executable_schema_version"]
        == "119O.1.0-json-schema"
    )


def test_capability_context_missing_data_is_deterministic_unknown(tmp_path):
    path = _snapshot_path(tmp_path)
    request = AdvisoryContextRequest(
        category="capability_lookup",
        advisory_purpose="test purpose",
        target="missing-capability",
    )

    package = build_advisory_context(path, request)

    assert package.selected_repository_intelligence == ()
    assert package.attribution_bundle == ()
    assert package.context_metadata["result_status"] == "unknown"
    assert package.context_metadata["unknowns"]


def test_limitation_and_boundary_lookup_categories_never_require_attribution(tmp_path):
    path = _snapshot_path(tmp_path)
    limitations_request = AdvisoryContextRequest(
        category="limitation_lookup", advisory_purpose="test purpose"
    )
    boundary_request = AdvisoryContextRequest(
        category="boundary_lookup", advisory_purpose="test purpose"
    )

    limitations_package = build_advisory_context(path, limitations_request)
    boundary_package = build_advisory_context(path, boundary_request)

    assert limitations_package.selected_repository_intelligence
    assert limitations_package.attribution_bundle == ()
    assert boundary_package.boundary_disclosure_bundle["boundary_disclosures"]


# ── Determinism ──────────────────────────────────────────────────────────


def test_repeated_context_assembly_is_deterministic(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    request = AdvisoryContextRequest(
        category="entity_lookup", advisory_purpose="test purpose", target=target
    )

    first = build_advisory_context(path, request).to_dict()
    second = build_advisory_context(path, request).to_dict()

    # Compare logical content (context_metadata minus the declared,
    # non-load-bearing assembly_timestamp) rather than requiring literal
    # wall-clock equality, matching the contract's "logically identical"
    # reproducibility guarantee (122B S14) rather than byte-identical output.
    assert "assembly_timestamp" in first["context_metadata"]
    first["context_metadata"].pop("assembly_timestamp")
    second["context_metadata"].pop("assembly_timestamp")
    assert first == second


# ── Serialization ────────────────────────────────────────────────────────


def test_serialize_context_package_is_deterministic_json(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    request = AdvisoryContextRequest(
        category="entity_lookup", advisory_purpose="test purpose", target=target
    )
    package = build_advisory_context(path, request)

    serialized = serialize_context_package(package)
    pretty = serialize_context_package(package, pretty=True)

    data = json.loads(serialized)
    assert data["selected_repository_intelligence"][0]["entity_id"] == target
    assert "\n" not in serialized
    assert "\n" in pretty
    assert json.loads(pretty) == data


# ── Fail-closed behavior ─────────────────────────────────────────────────


def test_invalid_context_request_unsupported_category_fails_closed():
    with pytest.raises(AdvisoryContextValidationError):
        validate_context_request(
            AdvisoryContextRequest(
                category="graph_traversal", advisory_purpose="x", target="y"
            )
        )


def test_invalid_context_request_missing_purpose_fails_closed():
    with pytest.raises(AdvisoryContextValidationError):
        validate_context_request(
            AdvisoryContextRequest(category="entity_lookup", advisory_purpose="   ", target="y")
        )


def test_invalid_context_request_missing_target_fails_closed():
    with pytest.raises(AdvisoryContextValidationError):
        validate_context_request(
            AdvisoryContextRequest(category="entity_lookup", advisory_purpose="x")
        )


def test_builder_rejects_unsupported_category(tmp_path):
    path = _snapshot_path(tmp_path)
    request = AdvisoryContextRequest(
        category="graph_traversal", advisory_purpose="x", target="y"
    )
    with pytest.raises(AdvisoryContextBuilderError):
        build_advisory_context(path, request)


def test_missing_snapshot_fails_closed(tmp_path):
    missing = tmp_path / "missing.json"
    request = AdvisoryContextRequest(
        category="entity_lookup", advisory_purpose="x", target="entity:x"
    )
    with pytest.raises(AdvisoryContextBuilderError):
        build_advisory_context(missing, request)


def test_corrupted_repository_intelligence_fails_closed(tmp_path):
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not json")
    request = AdvisoryContextRequest(
        category="entity_lookup", advisory_purpose="x", target="entity:x"
    )
    with pytest.raises(AdvisoryContextBuilderError):
        build_advisory_context(corrupt, request)


def test_unsupported_schema_version_fails_closed(tmp_path):
    path = _snapshot_path(tmp_path)
    snapshot = _load_json(path)
    snapshot["snapshot_identity"]["executable_schema_version"] = "future-version"
    incompatible = _write_snapshot(tmp_path, snapshot, "future.json")

    request = AdvisoryContextRequest(
        category="entity_lookup", advisory_purpose="x", target="entity:x"
    )
    with pytest.raises(AdvisoryContextBuilderError):
        build_advisory_context(incompatible, request)


def test_missing_attribution_on_content_record_fails_closed(tmp_path):
    path = _snapshot_path(tmp_path)
    snapshot = _load_json(path)
    snapshot["architectural_entities"][0]["source_attribution"] = []
    target = snapshot["architectural_entities"][0]["entity_id"]
    broken = _write_snapshot(tmp_path, snapshot, "missing-attribution.json")

    request = AdvisoryContextRequest(
        category="entity_lookup", advisory_purpose="x", target=target
    )
    with pytest.raises(AdvisoryContextBuilderError):
        build_advisory_context(broken, request)


def test_missing_boundary_disclosure_fails_closed(tmp_path):
    path = _snapshot_path(tmp_path)
    snapshot = _load_json(path)
    snapshot["boundary_disclosures"] = {}
    snapshot["disclaimers"] = {}
    broken = _write_snapshot(tmp_path, snapshot, "no-boundary.json")

    request = AdvisoryContextRequest(category="boundary_lookup", advisory_purpose="x")
    with pytest.raises(AdvisoryContextBuilderError):
        build_advisory_context(broken, request)


def test_max_records_bound_adds_disclosed_limitation(tmp_path):
    path = _snapshot_path(tmp_path)
    snapshot = _load_json(path)
    snapshot["snapshot_limitations"].append(
        {
            "limitation_type": "scope_limitation",
            "limitation_description": "A second synthetic limitation for bound testing.",
        }
    )
    bounded_source = _write_snapshot(tmp_path, snapshot, "multi-limitation.json")

    request = AdvisoryContextRequest(
        category="limitation_lookup", advisory_purpose="x", max_records=1
    )
    package = build_advisory_context(bounded_source, request)
    assert len(package.selected_repository_intelligence) == 1
    assert any(
        limitation.get("limitation_type") == "context_bound"
        for limitation in package.limitation_bundle
    )


def test_max_records_must_be_positive():
    with pytest.raises(AdvisoryContextValidationError):
        validate_context_request(
            AdvisoryContextRequest(
                category="limitation_lookup", advisory_purpose="x", max_records=0
            )
        )


# ── Read-only guarantees ──────────────────────────────────────────────────


def test_context_assembly_is_read_only_for_snapshot_file(tmp_path):
    path = _snapshot_path(tmp_path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()

    build_advisory_context(
        path, AdvisoryContextRequest(category="boundary_lookup", advisory_purpose="x")
    )

    after = hashlib.sha256(path.read_bytes()).hexdigest()
    assert after == before


def test_context_package_contains_no_reasoning_or_recommendation_fields(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    package = build_advisory_context(
        path,
        AdvisoryContextRequest(
            category="entity_lookup", advisory_purpose="x", target=target
        ),
    )
    data = package.to_dict()
    forbidden_keys = {"recommendation", "decision", "reasoning", "advisory_result"}
    assert forbidden_keys.isdisjoint(data.keys())


# ── CLI integration ──────────────────────────────────────────────────────


def test_cli_advisory_context_build_json_output(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pcae",
            "advisory",
            "context",
            "build",
            "--snapshot",
            str(path),
            "--entity",
            target,
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["selected_repository_intelligence"][0]["entity_id"] == target


def test_cli_advisory_context_build_missing_snapshot_fails_closed(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pcae",
            "advisory",
            "context",
            "build",
            "--snapshot",
            str(tmp_path / "missing.json"),
            "--entity",
            "entity:x",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 1
    assert "Error" in result.stderr


def test_cli_advisory_context_build_writes_output_file(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    output_path = tmp_path / "context.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pcae",
            "advisory",
            "context",
            "build",
            "--snapshot",
            str(path),
            "--entity",
            target,
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    written = json.loads(output_path.read_text())
    assert written["selected_repository_intelligence"][0]["entity_id"] == target
