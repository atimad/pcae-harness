from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_risk_register_json() -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "risk-register", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


def test_risk_register_exits_successfully():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "risk-register", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0


def test_risk_register_output_is_valid_json():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "risk-register", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    data = json.loads(result.stdout)
    assert isinstance(data, dict)


def test_risk_register_envelope_fields():
    data = _run_risk_register_json()
    assert "schema_version" in data
    assert "generated_at" in data
    assert "source_command" in data
    assert "repository_root" in data
    assert "risks" in data
    assert "risk_count" in data
    assert "warnings" in data
    assert "errors" in data
    assert "safety_notes" in data


def test_risk_register_risks_is_list():
    data = _run_risk_register_json()
    assert isinstance(data["risks"], list)


def test_risk_register_risk_count_matches():
    data = _run_risk_register_json()
    assert data["risk_count"] == len(data["risks"])


def test_risk_register_required_fields():
    data = _run_risk_register_json()
    required = [
        "risk_id",
        "risk_type",
        "risk_status",
        "risk_title",
        "risk_description",
        "risk_severity",
        "risk_likelihood",
        "risk_exposure",
        "source_phase",
        "source_artifact",
        "source_event",
        "source_decision",
        "source_commit",
        "risk_owner",
        "human_review_required",
        "affected_files",
        "affected_agents",
        "affected_commands",
        "blocking_condition",
        "mitigation",
        "acceptance_rationale",
        "accepted_by",
        "supersedes",
        "superseded_by",
        "related_risks",
        "related_artifacts",
        "related_events",
        "related_decisions",
        "evidence_level",
        "last_reviewed_phase",
        "next_review_phase",
        "safety_notes",
    ]
    assert len(data["risks"]) > 0
    for risk in data["risks"][:5]:
        for field in required:
            assert field in risk, f"Missing field: {field} in risk {risk.get('risk_id')}"


def test_risk_register_risks_are_deterministic():
    data1 = _run_risk_register_json()
    data2 = _run_risk_register_json()
    ids1 = [r["risk_id"] for r in data1["risks"]]
    ids2 = [r["risk_id"] for r in data2["risks"]]
    assert ids1 == ids2


def test_risk_register_risks_ordered_deterministically():
    data1 = _run_risk_register_json()
    data2 = _run_risk_register_json()
    order1 = [(r["source_phase"], r["risk_type"], r["risk_id"]) for r in data1["risks"]]
    order2 = [(r["source_phase"], r["risk_type"], r["risk_id"]) for r in data2["risks"]]
    assert order1 == order2


def test_risk_register_risk_ids_stable():
    data1 = _run_risk_register_json()
    data2 = _run_risk_register_json()
    for r1, r2 in zip(data1["risks"], data2["risks"]):
        assert r1["risk_id"] == r2["risk_id"]


def test_risk_register_has_required_initial_risks():
    data = _run_risk_register_json()
    types = {r["risk_type"] for r in data["risks"]}
    assert "read_only_boundary_risk" in types
    assert "storage_boundary_risk" in types
    assert "backend_invocation_risk" in types
    assert "authority_inference_risk" in types
    assert "raw_push_exception_risk" in types
    assert "hook_bypass_exception_risk" in types
    assert "stale_signal_risk" in types
    assert "implementation_scope_risk" in types
    assert "test_coverage_risk" in types
    assert "next_phase_risk" in types


def test_risk_register_status_values_explicit():
    data = _run_risk_register_json()
    valid_statuses = {"active", "accepted", "mitigated", "deferred", "blocked",
                      "closed", "superseded", "stale_signal", "unknown"}
    for risk in data["risks"]:
        assert risk["risk_status"] in valid_statuses, (
            f"Invalid status {risk['risk_status']} in {risk['risk_id']}"
        )


def test_risk_register_severity_likelihood_exposure_explicit():
    data = _run_risk_register_json()
    valid_severity = {"low", "medium", "high", "critical", "unknown"}
    valid_likelihood = {"unlikely", "possible", "likely", "observed", "unknown"}
    valid_exposure = {"low", "medium", "high", "critical", "unknown"}
    for risk in data["risks"]:
        assert risk["risk_severity"] in valid_severity
        assert risk["risk_likelihood"] in valid_likelihood
        assert risk["risk_exposure"] in valid_exposure


def test_risk_register_accepted_risk_not_treated_as_mitigation():
    data = _run_risk_register_json()
    for risk in data["risks"]:
        if risk["risk_status"] == "accepted":
            assert risk["acceptance_rationale"] is not None, (
                f"Accepted risk {risk['risk_id']} must have acceptance_rationale"
            )
            assert risk["mitigation"] is None, (
                f"Accepted risk {risk['risk_id']} must not have mitigation (accepted != mitigated)"
            )


def test_risk_register_accepted_risk_safety_note():
    data = _run_risk_register_json()
    assert data["safety_notes"]["accepted_risk_is_not_mitigation"] is True


def test_risk_register_stale_signal_visible():
    data = _run_risk_register_json()
    stale = [r for r in data["risks"] if r["risk_status"] == "stale_signal"]
    assert len(stale) > 0, "No stale_signal risks found"
    stale_types = {r["risk_type"] for r in stale}
    assert "stale_signal_risk" in stale_types


def test_risk_register_must_never_repeat_visible():
    data = _run_risk_register_json()
    mnr = [r for r in data["risks"] if r["risk_type"] == "must_never_repeat_risk"]
    assert len(mnr) > 0, "No must_never_repeat_risk found"
    raw_push = [r for r in data["risks"] if r["risk_type"] == "raw_push_exception_risk"]
    assert len(raw_push) > 0, "No raw_push_exception_risk found"
    hook_bypass = [r for r in data["risks"] if r["risk_type"] == "hook_bypass_exception_risk"]
    assert len(hook_bypass) > 0, "No hook_bypass_exception_risk found"


def test_risk_register_artifact_index_used():
    data = _run_risk_register_json()
    assert data["safety_notes"]["artifact_index_used"] is True


def test_risk_register_memory_snapshot_used():
    data = _run_risk_register_json()
    assert data["safety_notes"]["memory_snapshot_used"] is True


def test_risk_register_governance_timeline_used():
    data = _run_risk_register_json()
    assert data["safety_notes"]["governance_timeline_used"] is True


def test_risk_register_decision_log_used():
    data = _run_risk_register_json()
    assert data["safety_notes"]["decision_log_used"] is True


def test_risk_register_unknown_not_encoded_as_false():
    data = _run_risk_register_json()
    for risk in data["risks"]:
        if risk["source_artifact"] is not None:
            assert risk["source_artifact"] is not False
        if risk["source_event"] is not None:
            assert risk["source_event"] is not False
        if risk["source_commit"] is not None:
            assert risk["source_commit"] is not False
        assert risk["risk_severity"] is not False
        assert risk["risk_likelihood"] is not False
        assert risk["risk_exposure"] is not False


def test_risk_register_no_cache_files_created():
    repo_root = Path(__file__).resolve().parent.parent
    pcae_dir = repo_root / ".pcae"
    cache_dir = pcae_dir / "cache"
    risk_dir = pcae_dir / "risks"
    before_cache = cache_dir.exists()
    before_risk = risk_dir.exists()
    _run_risk_register_json()
    if not before_cache:
        assert not cache_dir.exists(), ".pcae/cache/ was created"
    if not before_risk:
        assert not risk_dir.exists(), ".pcae/risks/ was created"


def test_risk_register_no_repository_files_created():
    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=repo_root,
    )
    before = result.stdout
    _run_risk_register_json()
    result2 = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=repo_root,
    )
    assert result2.stdout == before, "risk-register modified repository files"


def test_risk_register_no_authority_inference():
    data = _run_risk_register_json()
    notes = data["safety_notes"]
    assert notes["risk_register_is_read_only"] is True
    assert notes["risk_register_does_not_authorize_execution"] is True
    assert notes["risk_register_does_not_authorize_backend_invocation"] is True
    assert notes["risk_register_does_not_authorize_adoption"] is True
    assert notes["risk_register_does_not_authorize_commit_or_push"] is True


def test_risk_register_no_generated_cache():
    data = _run_risk_register_json()
    assert data["safety_notes"]["generated_cache_created"] is False
    assert data["safety_notes"]["pcae_storage_created"] is False


def test_risk_register_schema_version():
    data = _run_risk_register_json()
    assert data["schema_version"] == "0.1"


def test_risk_register_source_command():
    data = _run_risk_register_json()
    assert data["source_command"] == "pcae risk-register"


def test_artifact_index_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "artifact-index", "--json"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["record_count"] > 0


def test_memory_snapshot_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "memory-snapshot", "--json"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "snapshot" in data


def test_governance_timeline_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "governance-timeline", "--json"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["event_count"] > 0


def test_decision_log_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "decision-log", "--json"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["decision_count"] > 0
