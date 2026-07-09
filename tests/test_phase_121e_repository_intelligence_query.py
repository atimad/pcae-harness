from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.repository_intelligence.query import QueryExecutionError, QueryRequest
from pcae.repository_intelligence.query.query_engine import execute_query
from pcae.repository_intelligence.query.snapshot_loader import (
    SUPPORTED_EXECUTABLE_SCHEMA_VERSION,
    SnapshotCompatibilityError,
    SnapshotLoadError,
    load_snapshot,
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


def test_snapshot_loading_and_schema_compatibility(tmp_path):
    path = _snapshot_path(tmp_path)
    snapshot = load_snapshot(path)
    assert (
        snapshot["snapshot_identity"]["executable_schema_version"]
        == SUPPORTED_EXECUTABLE_SCHEMA_VERSION
    )


def test_unsupported_schema_version_rejected(tmp_path):
    path = _snapshot_path(tmp_path)
    snapshot = _load_json(path)
    snapshot["snapshot_identity"]["executable_schema_version"] = "future-version"
    incompatible = _write_snapshot(tmp_path, snapshot, "future.json")

    with pytest.raises(SnapshotCompatibilityError):
        load_snapshot(incompatible)


def test_corrupted_snapshot_fails_closed(tmp_path):
    path = tmp_path / "corrupt.json"
    path.write_text("{not json")

    with pytest.raises(SnapshotLoadError):
        load_snapshot(path)


def test_entity_lookup_preserves_attribution_limitations_and_boundaries(tmp_path):
    path = _snapshot_path(tmp_path)
    result = execute_query(
        path,
        QueryRequest(category="entity_lookup", target="entity:src/pcae/cli.py"),
    ).to_dict()

    assert result["result_status"] == "ok"
    assert [record["entity_id"] for record in result["records"]] == [
        "entity:src/pcae/cli.py"
    ]
    assert result["attribution"]
    assert all(item["source_id"] for item in result["attribution"])
    assert result["limitations"]
    assert result["boundary_disclosures"]
    assert result["disclaimers"]
    assert (
        result["source_artifact"]["executable_schema_version"]
        == SUPPORTED_EXECUTABLE_SCHEMA_VERSION
    )


def test_capability_lookup_missing_data_is_deterministic_unknown(tmp_path):
    path = _snapshot_path(tmp_path)
    result = execute_query(
        path,
        QueryRequest(category="capability_lookup", target="missing-capability"),
    ).to_dict()

    assert result["result_status"] == "unknown"
    assert result["records"] == []
    assert result["unknowns"] == [
        "No capability matched target 'missing-capability'."
    ]
    assert any(
        limitation["limitation_type"] == "missing_data"
        for limitation in result["limitations"]
    )


def test_contract_lookup_absent_optional_section_returns_unknown(tmp_path):
    path = _snapshot_path(tmp_path)
    result = execute_query(
        path,
        QueryRequest(category="architectural_contract_lookup", target="contract:x"),
    ).to_dict()

    assert result["result_status"] == "unknown"
    assert result["records"] == []
    assert result["unknowns"] == [
        "No architectural contract matched target 'contract:x'."
    ]


def test_attribution_lookup_returns_attribution_records(tmp_path):
    path = _snapshot_path(tmp_path)
    result = execute_query(
        path,
        QueryRequest(category="attribution_lookup", target="entity:src/pcae/cli.py"),
    ).to_dict()

    assert result["result_status"] == "ok"
    assert result["records"]
    assert result["attribution"] == result["records"]
    assert result["records"][0]["source_id"] == "source:src/pcae/cli.py"


def test_limitation_and_boundary_queries(tmp_path):
    path = _snapshot_path(tmp_path)
    limitations = execute_query(
        path,
        QueryRequest(category="limitation_lookup"),
    ).to_dict()
    boundary = execute_query(path, QueryRequest(category="boundary_lookup")).to_dict()

    assert limitations["records"]
    assert limitations["limitations"]
    assert boundary["records"] == [
        {
            "boundary_disclosures": boundary["boundary_disclosures"],
            "disclaimers": boundary["disclaimers"],
        }
    ]


def test_unsupported_query_rejected(tmp_path):
    path = _snapshot_path(tmp_path)
    with pytest.raises(QueryExecutionError):
        execute_query(path, QueryRequest(category="graph_traversal", target="x"))


def test_unknown_entity_handling_is_explicit(tmp_path):
    path = _snapshot_path(tmp_path)
    result = execute_query(
        path,
        QueryRequest(category="entity_lookup", target="entity:not-present"),
    ).to_dict()

    assert result["result_status"] == "unknown"
    assert result["records"] == []
    assert result["unknowns"] == ["No architectural entity matched target 'entity:not-present'."]


def test_repeated_query_execution_is_deterministic(tmp_path):
    path = _snapshot_path(tmp_path)
    request = QueryRequest(category="entity_lookup", target="entity:src/pcae/cli.py")
    first = execute_query(path, request).to_dict()
    second = execute_query(path, request).to_dict()
    assert first == second


def test_query_is_read_only_for_snapshot_file(tmp_path):
    path = _snapshot_path(tmp_path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()

    execute_query(path, QueryRequest(category="boundary_lookup"))

    after = hashlib.sha256(path.read_bytes()).hexdigest()
    assert after == before


def test_missing_snapshot_fails_closed(tmp_path):
    missing = tmp_path / "missing.json"
    with pytest.raises(SnapshotLoadError):
        load_snapshot(missing)


def test_missing_attribution_on_content_record_fails_closed(tmp_path):
    path = _snapshot_path(tmp_path)
    snapshot = _load_json(path)
    snapshot["architectural_entities"][0]["source_attribution"] = []
    target = snapshot["architectural_entities"][0]["entity_id"]
    broken = _write_snapshot(tmp_path, snapshot, "missing-attribution.json")

    with pytest.raises(QueryExecutionError):
        execute_query(broken, QueryRequest(category="entity_lookup", target=target))


def test_cli_query_json_output(tmp_path):
    path = _snapshot_path(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pcae",
            "repository-intelligence",
            "query",
            "--snapshot",
            str(path),
            "--entity",
            "entity:src/pcae/cli.py",
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["result_status"] == "ok"
    assert data["records"][0]["entity_id"] == "entity:src/pcae/cli.py"
