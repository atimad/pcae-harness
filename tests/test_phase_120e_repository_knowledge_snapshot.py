from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.repository_intelligence.snapshot_generator import (
    SnapshotGenerationError,
    generate_snapshot,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_schema(relative: str) -> dict:
    return json.loads(
        (REPO_ROOT / "schemas" / "repository_intelligence" / relative).read_text()
    )


def _check_required(obj: dict, schema: dict) -> list[str]:
    errors = []
    for field in schema.get("required", []):
        if field not in obj:
            errors.append(f"missing required field '{field}'")
    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}).keys())
        for key in obj:
            if key not in allowed:
                errors.append(f"unexpected field '{key}'")
    return errors


def _generate(tmp_path: Path, name: str = "out") -> tuple[dict, dict]:
    output_dir = tmp_path / name
    result = generate_snapshot(REPO_ROOT, output_dir=output_dir)
    snapshot = json.loads(Path(result["latest_path"]).read_text())
    return result, snapshot


def test_deterministic_generation(tmp_path):
    _, snapshot_a = _generate(tmp_path, "a")
    _, snapshot_b = _generate(tmp_path, "b")

    def strip(snap: dict) -> dict:
        snap = json.loads(json.dumps(snap))
        snap["envelope"]["generated_at_utc"] = "TS"
        snap["snapshot_identity"]["snapshot_created_at_utc"] = "TS"
        return snap

    assert strip(snapshot_a) == strip(snapshot_b)


def test_schema_conformance_top_level(tmp_path):
    _, snapshot = _generate(tmp_path)
    rks_schema = _load_schema("artifacts/repository_knowledge_snapshot.schema.json")
    errors = _check_required(snapshot, rks_schema)
    assert errors == []


def test_schema_conformance_envelope(tmp_path):
    _, snapshot = _generate(tmp_path)
    envelope_schema = _load_schema("shared/common_artifact_envelope.schema.json")
    errors = _check_required(snapshot["envelope"], envelope_schema)
    assert errors == []


def test_schema_conformance_entities_and_claims(tmp_path):
    _, snapshot = _generate(tmp_path)
    rks_schema = _load_schema("artifacts/repository_knowledge_snapshot.schema.json")
    uv_schema = _load_schema("shared/uncertainty_verification_state.schema.json")
    entity_schema = rks_schema["$defs"]["architectural_entity"]
    claim_schema = rks_schema["$defs"]["knowledge_claim"]

    assert len(snapshot["architectural_entities"]) >= 1
    for entity in snapshot["architectural_entities"]:
        assert _check_required(entity, entity_schema) == []
        assert entity["entity_type"] in rks_schema["$defs"]["entity_type"]["enum"]
        assert _check_required(entity["verification_state"], uv_schema) == []

    assert len(snapshot["knowledge_claims"]) >= 1
    for claim in snapshot["knowledge_claims"]:
        assert _check_required(claim, claim_schema) == []
        assert claim["claim_status"] in uv_schema["$defs"]["state_value"]["enum"]


def test_attribution_completeness(tmp_path):
    _, snapshot = _generate(tmp_path)
    sar_schema = _load_schema("shared/source_attribution_record.schema.json")
    locator_types = set(
        sar_schema["$defs"]["source_locator"]["properties"]["locator_type"]["enum"]
    )

    for entity in snapshot["architectural_entities"]:
        assert entity["source_attribution"], "entity missing source_attribution"
        for source in entity["source_attribution"]:
            assert source["source_locator"]["locator_type"] in locator_types
            assert source["source_locator"]["locator_value"]

    for claim in snapshot["knowledge_claims"]:
        assert claim["source_attribution"], "claim missing source_attribution"

    assert len(snapshot["knowledge_sources"]) >= 1


def test_limitation_attachment(tmp_path):
    _, snapshot = _generate(tmp_path)
    assert len(snapshot["snapshot_limitations"]) >= 1
    for entity in snapshot["architectural_entities"]:
        assert len(entity["limitations"]) >= 1


def test_disclaimer_attachment(tmp_path):
    _, snapshot = _generate(tmp_path)
    disc_schema = _load_schema("shared/disclaimer.schema.json")
    for field, definition in disc_schema["properties"].items():
        assert snapshot["disclaimers"][field] == definition["const"]
        assert snapshot["envelope"]["disclaimers"][field] == definition["const"]
    rks_schema = _load_schema("artifacts/repository_knowledge_snapshot.schema.json")
    assert (
        snapshot["repository_knowledge_snapshot_disclaimer"]
        == rks_schema["properties"]["repository_knowledge_snapshot_disclaimer"]["const"]
    )


def test_boundary_disclosure_attachment(tmp_path):
    _, snapshot = _generate(tmp_path)
    bd_schema = _load_schema("shared/boundary_disclosure.schema.json")
    for field in bd_schema["required"]:
        assert snapshot["boundary_disclosures"][field] is True
        assert snapshot["envelope"]["boundary_disclosures"][field] is True


def test_persistence_writes_latest_and_timestamped(tmp_path):
    result, _ = _generate(tmp_path)
    latest = Path(result["latest_path"])
    timestamped = Path(result["snapshot_path"])
    assert latest.is_file()
    assert timestamped.is_file()
    assert latest.name == "latest.json"
    assert timestamped.parent.name == "snapshots"
    assert json.loads(latest.read_text()) == json.loads(timestamped.read_text())


def test_latest_snapshot_updates_without_deleting_history(tmp_path):
    output_dir = tmp_path / "persist"
    result_1 = generate_snapshot(REPO_ROOT, output_dir=output_dir)
    result_2 = generate_snapshot(REPO_ROOT, output_dir=output_dir)

    snapshots_dir = output_dir / "snapshots"
    assert len(list(snapshots_dir.glob("*.json"))) == 2
    assert Path(result_1["snapshot_path"]).is_file()
    assert Path(result_2["snapshot_path"]).is_file()
    assert (output_dir / "latest.json").is_file()


def test_invalid_input_handling_non_git_directory(tmp_path):
    non_git_dir = tmp_path / "not-a-repo"
    non_git_dir.mkdir()
    with pytest.raises(SnapshotGenerationError):
        generate_snapshot(non_git_dir, output_dir=tmp_path / "out")


def test_unknown_handling_declares_unknowns(tmp_path):
    _, snapshot = _generate(tmp_path)
    assert len(snapshot["unknowns"]) >= 1
    assert all(isinstance(item, str) and item for item in snapshot["unknowns"])


def test_fail_closed_no_persistence_on_failure(tmp_path):
    non_git_dir = tmp_path / "not-a-repo-2"
    non_git_dir.mkdir()
    output_dir = tmp_path / "should-not-exist"
    with pytest.raises(SnapshotGenerationError):
        generate_snapshot(non_git_dir, output_dir=output_dir)
    assert not output_dir.exists()


@pytest.mark.integration
def test_cli_generate_json_output(tmp_path):
    output_dir = tmp_path / "cli-out"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pcae",
            "repository-intelligence",
            "snapshot",
            "generate",
            "--output",
            str(output_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "artifact_id" in data
    assert Path(data["latest_path"]).is_file()
