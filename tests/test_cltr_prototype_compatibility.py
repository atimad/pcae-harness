from __future__ import annotations

import json
from pathlib import Path

from pcae.cltr_prototype import compatibility

FIXTURES = Path(__file__).parent / "fixtures" / "cltr_prototype"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_legacy_artifact_no_transition_id_disclosed_honestly():
    fixture = _load("legacy_artifact_no_transition_id.json")
    result = compatibility.classify_legacy_artifact(FIXTURES.parent.parent.parent / fixture["artifact_path"], fixture["artifact_kind"])
    assert "transition_id" in result.missing_fields
    assert result.classification == "conformant_with_legacy_adapter"


def test_legacy_artifact_never_invents_transition_id():
    fixture = _load("legacy_artifact_no_transition_id.json")
    result = compatibility.classify_legacy_artifact(FIXTURES.parent.parent.parent / fixture["artifact_path"], fixture["artifact_kind"])
    assert "transition_id" not in result.disclosed_identity


def test_stale_report_conflict_detected():
    fixture = _load("stale_report.json")
    declared = fixture["declared_identity"]
    result = compatibility.classify_legacy_artifact(
        FIXTURES.parent.parent.parent / fixture["narrative_artifact_path"], fixture["narrative_artifact_kind"], declared_identity=declared
    )
    assert result.classification == "conflicting"
    assert result.limitation is not None


def test_narrative_identity_confidence_disclosed():
    fixture = _load("stale_report.json")
    result = compatibility.classify_legacy_artifact(
        FIXTURES.parent.parent.parent / fixture["narrative_artifact_path"], fixture["narrative_artifact_kind"]
    )
    assert result.identity_confidence == "narrative_parsed_comparison_only"


def test_nonexistent_artifact_classified_unverifiable():
    result = compatibility.classify_legacy_artifact(Path("/nonexistent/path/report.md"), "canonical_report")
    assert result.classification == "unverifiable"


def test_never_mutates_source_artifact(tmp_path):
    artifact = tmp_path / "metadata.json"
    original_content = json.dumps({"phase_id": "134E"})
    artifact.write_text(original_content)
    compatibility.classify_legacy_artifact(artifact, "completion_metadata")
    assert artifact.read_text() == original_content
