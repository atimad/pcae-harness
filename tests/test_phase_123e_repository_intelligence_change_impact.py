from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.repository_intelligence.change_impact import (
    CHANGE_IMPACT_NON_AUTHORITY_DISCLAIMER,
    ChangeImpactBuilderError,
    ChangeImpactRequest,
    ChangeImpactValidationError,
    build_change_impact_report,
    serialize_change_impact_report,
)
from pcae.repository_intelligence.change_impact.validation import validate_change_request
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


def _logical_report(report) -> dict:
    data = report.to_dict()
    data["report_metadata"].pop("assembly_timestamp")
    return data


def test_change_impact_report_preserves_attribution_limitations_and_boundaries(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    request = ChangeImpactRequest(
        requested_change="Adjust repository intelligence reporting.",
        target_entities=(target,),
    )

    report = build_change_impact_report(path, request)

    assert [entity["entity_id"] for entity in report.impacted_entities] == [target]
    assert report.impact_relationships[0]["relationship_type"] == "declared_change_target"
    assert report.attribution_bundle
    assert all(item["source_id"] for item in report.attribution_bundle)
    assert report.limitation_bundle
    assert report.boundary_disclosure_bundle["boundary_disclosures"]
    assert report.boundary_disclosure_bundle["disclaimers"]
    assert (
        report.boundary_disclosure_bundle["non_authority_disclaimer"]
        == CHANGE_IMPACT_NON_AUTHORITY_DISCLAIMER
    )
    assert report.report_metadata["change_request"]["requested_change"].startswith(
        "Adjust"
    )
    assert report.report_metadata["query_requests"] == [
        {"category": "entity_lookup", "target": target}
    ]
    assert (
        report.report_metadata["source_artifacts"][0]["executable_schema_version"]
        == "119O.1.0-json-schema"
    )


def test_change_impact_builder_uses_query_layer_only(monkeypatch, tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    calls = []

    from pcae.repository_intelligence.change_impact import change_impact_builder

    original_execute_query = change_impact_builder.execute_query

    def recording_execute_query(snapshot_path, query_request):
        calls.append(query_request.normalized())
        return original_execute_query(snapshot_path, query_request)

    monkeypatch.setattr(
        change_impact_builder, "execute_query", recording_execute_query
    )

    build_change_impact_report(
        path,
        ChangeImpactRequest(
            requested_change="Inspect exact target.", target_entities=(target,)
        ),
    )

    assert calls == [{"category": "entity_lookup", "target": target, "filters": {}, "projection": []}]


def test_repeated_change_impact_generation_is_deterministic(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    request = ChangeImpactRequest(
        requested_change="Change requested.", target_entities=(target,)
    )

    first = _logical_report(build_change_impact_report(path, request))
    second = _logical_report(build_change_impact_report(path, request))

    assert first == second


def test_serialize_change_impact_report_is_deterministic_json(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    report = build_change_impact_report(
        path,
        ChangeImpactRequest(
            requested_change="Change requested.", target_entities=(target,)
        ),
    )

    serialized = serialize_change_impact_report(report)
    pretty = serialize_change_impact_report(report, pretty=True)

    data = json.loads(serialized)
    assert data["impacted_entities"][0]["entity_id"] == target
    assert "\n" not in serialized
    assert "\n" in pretty
    assert json.loads(pretty) == data


def test_unknown_target_is_reported_without_inference(tmp_path):
    path = _snapshot_path(tmp_path)
    request = ChangeImpactRequest(
        requested_change="Change requested.", target_entities=("missing-entity",)
    )

    report = build_change_impact_report(path, request)

    assert report.impacted_entities == ()
    assert report.impact_relationships == ()
    assert report.unknowns
    assert report.report_metadata["unknowns"] == list(report.unknowns)


def test_invalid_change_request_fails_closed():
    with pytest.raises(ChangeImpactValidationError):
        validate_change_request(
            ChangeImpactRequest(requested_change=" ", target_entities=("entity:x",))
        )
    with pytest.raises(ChangeImpactValidationError):
        validate_change_request(
            ChangeImpactRequest(requested_change="x", target_entities=())
        )
    with pytest.raises(ChangeImpactValidationError):
        validate_change_request(
            ChangeImpactRequest(
                requested_change="x",
                target_entities=("entity:x",),
                evaluation_scope=("graph_traversal",),
            )
        )


def test_builder_rejects_invalid_request(tmp_path):
    path = _snapshot_path(tmp_path)
    with pytest.raises(ChangeImpactBuilderError):
        build_change_impact_report(
            path, ChangeImpactRequest(requested_change="x", target_entities=())
        )


def test_missing_snapshot_fails_closed(tmp_path):
    with pytest.raises(ChangeImpactBuilderError):
        build_change_impact_report(
            tmp_path / "missing.json",
            ChangeImpactRequest(
                requested_change="x", target_entities=("entity:x",)
            ),
        )


def test_corrupted_repository_intelligence_response_fails_closed(tmp_path):
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not json")
    with pytest.raises(ChangeImpactBuilderError):
        build_change_impact_report(
            corrupt,
            ChangeImpactRequest(
                requested_change="x", target_entities=("entity:x",)
            ),
        )


def test_unsupported_schema_version_fails_closed(tmp_path):
    path = _snapshot_path(tmp_path)
    snapshot = _load_json(path)
    snapshot["snapshot_identity"]["executable_schema_version"] = "future-version"
    broken = _write_snapshot(tmp_path, snapshot, "future.json")

    with pytest.raises(ChangeImpactBuilderError):
        build_change_impact_report(
            broken,
            ChangeImpactRequest(
                requested_change="x", target_entities=("entity:x",)
            ),
        )


def test_missing_attribution_fails_closed(tmp_path):
    path = _snapshot_path(tmp_path)
    snapshot = _load_json(path)
    snapshot["architectural_entities"][0]["source_attribution"] = []
    target = snapshot["architectural_entities"][0]["entity_id"]
    broken = _write_snapshot(tmp_path, snapshot, "missing-attribution.json")

    with pytest.raises(ChangeImpactBuilderError):
        build_change_impact_report(
            broken, ChangeImpactRequest(requested_change="x", target_entities=(target,))
        )


def test_missing_limitation_fails_closed(tmp_path):
    path = _snapshot_path(tmp_path)
    snapshot = _load_json(path)
    snapshot["snapshot_limitations"] = []
    snapshot["architectural_entities"][0]["limitations"] = []
    target = snapshot["architectural_entities"][0]["entity_id"]
    broken = _write_snapshot(tmp_path, snapshot, "missing-limitation.json")

    with pytest.raises(ChangeImpactBuilderError):
        build_change_impact_report(
            broken, ChangeImpactRequest(requested_change="x", target_entities=(target,))
        )


def test_missing_boundary_disclosure_fails_closed(tmp_path):
    path = _snapshot_path(tmp_path)
    snapshot = _load_json(path)
    snapshot["boundary_disclosures"] = {}
    snapshot["disclaimers"] = {}
    target = snapshot["architectural_entities"][0]["entity_id"]
    broken = _write_snapshot(tmp_path, snapshot, "missing-boundary.json")

    with pytest.raises(ChangeImpactBuilderError):
        build_change_impact_report(
            broken, ChangeImpactRequest(requested_change="x", target_entities=(target,))
        )


def test_change_impact_generation_is_read_only_for_snapshot_file(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()

    build_change_impact_report(
        path,
        ChangeImpactRequest(
            requested_change="Change requested.", target_entities=(target,)
        ),
    )

    after = hashlib.sha256(path.read_bytes()).hexdigest()
    assert after == before


def test_change_impact_report_contains_no_authority_fields(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    report = build_change_impact_report(
        path,
        ChangeImpactRequest(
            requested_change="Change requested.", target_entities=(target,)
        ),
    )
    data = report.to_dict()
    forbidden_keys = {"recommendation", "decision", "reasoning", "advisory_result"}
    assert forbidden_keys.isdisjoint(data.keys())


def test_cli_change_impact_json_output(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pcae",
            "repository-intelligence",
            "change-impact",
            "--snapshot",
            str(path),
            "--change",
            "Change requested.",
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
    assert data["impacted_entities"][0]["entity_id"] == target


def test_cli_change_impact_writes_output_file(tmp_path):
    path = _snapshot_path(tmp_path)
    target = _first_entity_id(tmp_path)
    output_path = tmp_path / "impact.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pcae",
            "repository-intelligence",
            "change-impact",
            "--snapshot",
            str(path),
            "--change",
            "Change requested.",
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
    assert written["impacted_entities"][0]["entity_id"] == target


def test_cli_change_impact_missing_snapshot_fails_closed(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pcae",
            "repository-intelligence",
            "change-impact",
            "--snapshot",
            str(tmp_path / "missing.json"),
            "--change",
            "Change requested.",
            "--entity",
            "entity:x",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 1
    assert "Error" in result.stderr
