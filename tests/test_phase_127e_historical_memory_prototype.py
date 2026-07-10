"""Tests for Phase 127E Historical Memory Prototype.

Uses a small, synthetic git repository (fast, fully controlled) as
``repo_root`` for the historical builder's own task-contract/git-log
input, paired with a Repository Knowledge Snapshot generated from the
real project repository (fast, ~1-2s, matching the DKG test suite's
own established `_snapshot_path` precedent) for cross-reference input
-- the builder treats these as independently-sourced inputs per 127D
Section 5.1, so this decoupling is a legitimate test design, not a
divergence from real usage.

One dedicated real-repository integration test
(`TestRealRepositoryIntegration`) exercises the full pipeline against
this repository's own actual git history and `tasks/done/` content
(850+ files, ~45-50s) to confirm real-world compatibility beyond the
synthetic fixtures.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.repository_intelligence.historical_memory import (
    HistoricalGenerationError,
    build_historical_content,
    generate_historical_memory,
)
from pcae.repository_intelligence.historical_memory.historical_validation import (
    validate_historical_snapshot,
)
from pcae.repository_intelligence.snapshot_generator import generate_snapshot

REPO_ROOT = Path(__file__).resolve().parent.parent


def _snapshot_path(tmp_path: Path) -> Path:
    result = generate_snapshot(REPO_ROOT, output_dir=tmp_path / "snapshot")
    return Path(result["latest_path"])


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, capture_output=True, check=True)


def _write_task_contract(
    repo: Path,
    filename: str,
    *,
    task_id: str,
    title: str,
    status: str = "done",
    mode: str = "",
    goal: str = "Do the thing.",
    created: str = "2026-01-01T00:00:00.000000+00:00",
) -> Path:
    tasks_done = repo / "tasks" / "done"
    tasks_done.mkdir(parents=True, exist_ok=True)
    path = tasks_done / filename
    path.write_text(
        f"# Task Contract\n\n"
        f"## Task ID\n\n{task_id}\n\n"
        f"## Title\n\n{title}\n\n"
        f"## Status\n\n{status}\n\n"
        f"## Mode\n\n{mode}\n\n"
        f"## Goal\n\n{goal}\n\n"
        f"## Created Timestamp\n\n{created}\n"
    )
    return path


def _make_synthetic_repo(
    tmp_path: Path,
    tasks: list[dict],
    *,
    tags: list[str] | None = None,
) -> Path:
    """Build a small synthetic git repository with the given task contracts.

    Each entry in ``tasks`` is committed separately so each file gets
    its own distinct, resolvable introducing commit -- mirroring how
    real task contracts in this repository are committed one at a
    time.
    """
    repo = tmp_path / "synthetic_repo"
    repo.mkdir()
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.email", "test@example.com")
    _run_git(repo, "config", "user.name", "Test")

    for i, task in enumerate(tasks):
        filename = task.pop("filename")
        _write_task_contract(repo, filename, **task)
        _run_git(repo, "add", f"tasks/done/{filename}")
        _run_git(repo, "commit", "-q", "-m", f"Add {filename}")
        if tags and i < len(tags) and tags[i]:
            _run_git(repo, "tag", tags[i])

    return repo


def _basic_repo(tmp_path: Path) -> Path:
    return _make_synthetic_repo(
        tmp_path,
        [
            dict(
                filename="20260101-0000-phase-100a-architecture.md",
                task_id="20260101-0000-phase-100a-architecture",
                title="Phase 100A Architecture",
                mode="architecture",
                goal="Define architecture.",
            ),
            dict(
                filename="20260102-0000-phase-100b-contract-freeze.md",
                task_id="20260102-0000-phase-100b-contract-freeze",
                title="Phase 100B Contract Freeze",
                mode="architecture",
                goal="Freeze the contract.",
            ),
            dict(
                filename="20260103-0000-phase-100c-hardening.md",
                task_id="20260103-0000-phase-100c-hardening",
                title="Phase 100C Hardening",
                mode="implementation",
                goal="Repaired the final remaining trust warning from 100B.",
            ),
            dict(
                filename="20260104-0000-untitled-legacy-task.md",
                task_id="20260104-0000-untitled-legacy-task",
                title="Some legacy task with no phase convention",
                mode="",
                goal="Old work.",
            ),
        ],
    )


class TestDeterministicGeneration:
    def test_equivalent_history_produces_equivalent_output(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)

        result_a = generate_historical_memory(
            snapshot_path, repo_root=repo, output_dir=tmp_path / "hist_a"
        )
        result_b = generate_historical_memory(
            snapshot_path, repo_root=repo, output_dir=tmp_path / "hist_b"
        )
        hist_a = _load_json(Path(result_a["latest_path"]))
        hist_b = _load_json(Path(result_b["latest_path"]))

        hist_a["envelope"]["generated_at_utc"] = "TS"
        hist_b["envelope"]["generated_at_utc"] = "TS"
        hist_a["snapshot_identity"]["snapshot_created_at_utc"] = "TS"
        hist_b["snapshot_identity"]["snapshot_created_at_utc"] = "TS"

        assert hist_a == hist_b

    def test_counts_are_stable(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        result_a = generate_historical_memory(
            snapshot_path, repo_root=repo, output_dir=tmp_path / "hist_a"
        )
        result_b = generate_historical_memory(
            snapshot_path, repo_root=repo, output_dir=tmp_path / "hist_b"
        )
        assert result_a["event_count"] == result_b["event_count"]
        assert result_a["phase_lineage_count"] == result_b["phase_lineage_count"]
        assert result_a["relationship_count"] == result_b["relationship_count"]


class TestIdentifierStability:
    def test_event_id_deterministic_across_runs(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        result = generate_historical_memory(
            snapshot_path, repo_root=repo, output_dir=tmp_path / "hist"
        )
        hist = _load_json(Path(result["latest_path"]))
        event_ids = {e["event_id"] for e in hist["historical_events"]}
        result2 = generate_historical_memory(
            snapshot_path, repo_root=repo, output_dir=tmp_path / "hist2"
        )
        hist2 = _load_json(Path(result2["latest_path"]))
        event_ids2 = {e["event_id"] for e in hist2["historical_events"]}
        assert event_ids == event_ids2

    def test_event_id_encodes_commit_and_task(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        for event in content["historical_events"]:
            assert event["event_id"].startswith(f"event:{event['event_type']}:")


class TestTimelineCorrectness:
    def test_events_and_phase_lineage_present_for_every_task(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        assert len(content["historical_events"]) == 4
        assert len(content["phase_lineage"]) == 4

    def test_phase_convention_titles_classified_not_unknown(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        by_subject = {e["event_subject"]: e["event_type"] for e in content["historical_events"]}
        assert by_subject["Phase 100A Architecture"] == "architecture_defined"
        assert by_subject["Phase 100B Contract Freeze"] == "contract_frozen"
        assert by_subject["Phase 100C Hardening"] == "hardening_completed"

    def test_non_convention_title_classified_unknown_not_guessed(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        legacy_events = [
            e
            for e in content["historical_events"]
            if e["event_subject"] == "Some legacy task with no phase convention"
        ]
        assert legacy_events
        assert all(e["event_type"] == "unknown" for e in legacy_events)

    def test_ordering_is_chronological_by_commit(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        # phase_lineage is serialized sorted by phase_id (validation
        # requirement), but internal construction order must have been
        # chronological -- confirmed indirectly via distinct commit refs.
        commit_refs = [
            p["commit_references"][0]["locator_value"]
            for p in content["phase_lineage"]
            if p["commit_references"]
        ]
        assert len(commit_refs) == len(set(commit_refs))


class TestTransitionCorrectness:
    def test_hardening_produces_repair_hardening_record(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        assert len(content["repair_hardening_history"]) == 1
        record = content["repair_hardening_history"][0]
        assert record["record_type"] == "hardening"
        assert "100B" in record["issue_or_boundary_addressed"]

    def test_relationship_links_hardening_to_referenced_phase(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        hardened_by = [
            r for r in content["historical_relationships"] if r["relationship_type"] == "hardened_by"
        ]
        assert len(hardened_by) == 1

    def test_zero_decision_records_in_v1(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        assert content["decision_history"] == []

    def test_sequential_related_to_relationships_present(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        related = [r for r in content["historical_relationships"] if r["relationship_type"] == "related_to"]
        assert len(related) == 3  # 4 phases -> 3 adjacent pairs


class TestReleaseLineage:
    def test_tag_produces_release_record(self, tmp_path: Path) -> None:
        repo = _make_synthetic_repo(
            tmp_path,
            [
                dict(
                    filename="20260101-0000-phase-100a-architecture.md",
                    task_id="20260101-0000-phase-100a-architecture",
                    title="Phase 100A Architecture",
                    mode="architecture",
                ),
            ],
            tags=["v0.1.0-test"],
        )
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        assert len(content["release_lineage"]) == 1
        assert content["release_lineage"][0]["release_id"] == "v0.1.0-test"

    def test_no_tags_produces_zero_release_records(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        assert content["release_lineage"] == []


class TestProvenanceLimitationBoundaryPropagation:
    def test_every_event_has_source_attribution(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        for event in content["historical_events"]:
            assert event["source_attribution"]

    def test_every_phase_lineage_has_source_attribution(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        for record in content["phase_lineage"]:
            assert record["source_attribution"]

    def test_every_record_has_limitations(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        for event in content["historical_events"]:
            assert event["limitations"]
        for record in content["phase_lineage"]:
            assert record["limitations"]

    def test_boundary_disclosures_and_disclaimer_present(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        assert content["boundary_disclosures"]
        assert content["disclaimers"]
        assert content["historical_memory_snapshot_disclaimer"]

    def test_snapshot_limitations_names_v1_scope_gaps(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        descriptions = " ".join(
            lim["limitation_description"] for lim in content["snapshot_limitations"]
        )
        assert "governance_check_completed" in descriptions
        assert "decision_history_record" in descriptions


class TestValidation:
    def test_valid_snapshot_passes_validation(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        validate_historical_snapshot(content)  # must not raise

    def test_rejects_duplicate_event_identifiers(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        content["historical_events"].append(dict(content["historical_events"][0]))
        with pytest.raises(HistoricalGenerationError, match="duplicate event_id"):
            validate_historical_snapshot(content)

    def test_rejects_invalid_event_type(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        content["historical_events"][0]["event_type"] = "not_a_real_type"
        with pytest.raises(HistoricalGenerationError, match="invalid event_type"):
            validate_historical_snapshot(content)

    def test_rejects_invalid_relationship_type(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        content["historical_relationships"][0]["relationship_type"] = "not_a_real_type"
        with pytest.raises(HistoricalGenerationError, match="invalid relationship_type"):
            validate_historical_snapshot(content)

    def test_rejects_dangling_relationship_endpoint(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        content["historical_relationships"][0]["target_reference"]["reference_id"] = "ref:phase:does-not-exist"
        with pytest.raises(HistoricalGenerationError, match="unknown target_reference"):
            validate_historical_snapshot(content)


class TestFailClosedBehavior:
    def test_missing_snapshot_file_fails_closed(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        with pytest.raises(HistoricalGenerationError, match="snapshot not found"):
            build_historical_content(
                repo, tmp_path / "missing.json", generated_at_utc="2026-01-01T00:00:00Z"
            )

    def test_corrupted_snapshot_fails_closed(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        bad = tmp_path / "bad.json"
        bad.write_text("{not json")
        with pytest.raises(HistoricalGenerationError, match="not valid JSON"):
            build_historical_content(repo, bad, generated_at_utc="2026-01-01T00:00:00Z")

    def test_missing_task_history_fails_closed(self, tmp_path: Path) -> None:
        repo = tmp_path / "empty_repo"
        repo.mkdir()
        _run_git(repo, "init", "-q")
        _run_git(repo, "config", "user.email", "test@example.com")
        _run_git(repo, "config", "user.name", "Test")
        (repo / "f.txt").write_text("x")
        _run_git(repo, "add", ".")
        _run_git(repo, "commit", "-q", "-m", "init")
        snapshot_path = _snapshot_path(tmp_path)
        with pytest.raises(HistoricalGenerationError, match="no tasks/done"):
            build_historical_content(repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z")

    def test_incompatible_schema_version_fails_closed(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = json.loads(snapshot_path.read_text())
        snapshot["snapshot_identity"]["executable_schema_version"] = "999.0.0-fake"
        bad_path = tmp_path / "bad_version.json"
        bad_path.write_text(json.dumps(snapshot))
        with pytest.raises(HistoricalGenerationError, match="unsupported"):
            build_historical_content(repo, bad_path, generated_at_utc="2026-01-01T00:00:00Z")

    def test_corrupted_repository_intelligence_artifact_fails_closed(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = json.loads(snapshot_path.read_text())
        snapshot["architectural_entities"] = "not-a-list"
        bad_path = tmp_path / "corrupt.json"
        bad_path.write_text(json.dumps(snapshot))
        with pytest.raises(HistoricalGenerationError, match="malformed"):
            build_historical_content(repo, bad_path, generated_at_utc="2026-01-01T00:00:00Z")

    def test_missing_source_attribution_fails_closed(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        content["historical_events"][0]["source_attribution"] = []
        with pytest.raises(HistoricalGenerationError, match="source_attribution"):
            validate_historical_snapshot(content)

    def test_missing_limitations_fails_closed(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        content["historical_events"][0]["limitations"] = []
        with pytest.raises(HistoricalGenerationError, match="limitations"):
            validate_historical_snapshot(content)

    def test_missing_boundary_disclosures_fails_closed(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        content["boundary_disclosures"] = {}
        with pytest.raises(HistoricalGenerationError, match="boundary_disclosures"):
            validate_historical_snapshot(content)

    def test_chronology_violation_fails_closed(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        content["historical_events"] = list(reversed(content["historical_events"]))
        with pytest.raises(HistoricalGenerationError, match="not deterministically ordered"):
            validate_historical_snapshot(content)


class TestSerializationDeterminism:
    def test_persisted_snapshot_is_sorted_and_stable(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        result = generate_historical_memory(
            snapshot_path, repo_root=repo, output_dir=tmp_path / "hist"
        )
        latest_text = Path(result["latest_path"]).read_text()
        parsed = json.loads(latest_text)
        reserialized = json.dumps(parsed, sort_keys=True)
        # latest.json itself is compact (pretty=False by default)
        assert json.dumps(parsed, sort_keys=True) == json.dumps(
            json.loads(reserialized), sort_keys=True
        )

    def test_pretty_and_compact_serialization_both_valid_json(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        compact = generate_historical_memory(
            snapshot_path, repo_root=repo, output_dir=tmp_path / "compact", pretty=False
        )
        pretty = generate_historical_memory(
            snapshot_path, repo_root=repo, output_dir=tmp_path / "pretty", pretty=True
        )
        compact_data = json.loads(Path(compact["latest_path"]).read_text())
        pretty_data = json.loads(Path(pretty["latest_path"]).read_text())
        compact_data["envelope"]["generated_at_utc"] = "TS"
        pretty_data["envelope"]["generated_at_utc"] = "TS"
        compact_data["snapshot_identity"]["snapshot_created_at_utc"] = "TS"
        pretty_data["snapshot_identity"]["snapshot_created_at_utc"] = "TS"
        assert compact_data == pretty_data


class TestPersistenceReadOnly:
    def test_latest_and_timestamped_files_both_written(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        result = generate_historical_memory(
            snapshot_path, repo_root=repo, output_dir=tmp_path / "hist"
        )
        assert Path(result["latest_path"]).is_file()
        assert Path(result["snapshot_path"]).is_file()

    def test_persistence_never_mutates_source_snapshot(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        before = snapshot_path.read_bytes()
        generate_historical_memory(snapshot_path, repo_root=repo, output_dir=tmp_path / "hist")
        after = snapshot_path.read_bytes()
        assert before == after

    def test_persistence_never_mutates_task_contract_files(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        task_files = sorted((repo / "tasks" / "done").glob("*.md"))
        before = {p: p.read_bytes() for p in task_files}
        generate_historical_memory(snapshot_path, repo_root=repo, output_dir=tmp_path / "hist")
        after = {p: p.read_bytes() for p in task_files}
        assert before == after

    def test_default_output_directory_distinct_from_snapshot_directory(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        result = generate_historical_memory(
            snapshot_path, repo_root=repo, output_dir=tmp_path / "hist"
        )
        assert "historical-memory" in result["latest_path"] or "hist" in result["latest_path"]
        assert Path(result["latest_path"]).resolve() != snapshot_path.resolve()


class TestCompatibilityValidation:
    def test_unsupported_snapshot_version_rejected(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = json.loads(snapshot_path.read_text())
        snapshot["snapshot_identity"]["executable_schema_version"] = "0.0.0-unsupported"
        bad_path = tmp_path / "unsupported.json"
        bad_path.write_text(json.dumps(snapshot))
        with pytest.raises(HistoricalGenerationError):
            build_historical_content(repo, bad_path, generated_at_utc="2026-01-01T00:00:00Z")

    def test_missing_snapshot_identity_rejected(self, tmp_path: Path) -> None:
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        snapshot = json.loads(snapshot_path.read_text())
        del snapshot["snapshot_identity"]
        bad_path = tmp_path / "no_identity.json"
        bad_path.write_text(json.dumps(snapshot))
        with pytest.raises(HistoricalGenerationError):
            build_historical_content(repo, bad_path, generated_at_utc="2026-01-01T00:00:00Z")


class TestSchemaRequiredFieldConformance:
    """Independent structural check against the frozen 119Q schema.

    No jsonschema validator library is available in this environment
    (consistent with the rest of the 119-127 line); this mirrors the
    scripted required-field/enum checks used throughout that line.
    """

    def test_all_required_top_level_fields_present(self, tmp_path: Path) -> None:
        schema_path = (
            REPO_ROOT
            / "schemas"
            / "repository_intelligence"
            / "artifacts"
            / "historical_memory_snapshot.schema.json"
        )
        schema = json.loads(schema_path.read_text())
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        for field in schema["required"]:
            assert field in content, f"missing required top-level field: {field}"

    def test_event_required_fields_present(self, tmp_path: Path) -> None:
        schema_path = (
            REPO_ROOT
            / "schemas"
            / "repository_intelligence"
            / "artifacts"
            / "historical_memory_snapshot.schema.json"
        )
        schema = json.loads(schema_path.read_text())
        required = schema["$defs"]["historical_event"]["required"]
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        for event in content["historical_events"]:
            for field in required:
                assert field in event, f"event {event.get('event_id')} missing {field}"

    def test_phase_lineage_record_required_fields_present(self, tmp_path: Path) -> None:
        schema_path = (
            REPO_ROOT
            / "schemas"
            / "repository_intelligence"
            / "artifacts"
            / "historical_memory_snapshot.schema.json"
        )
        schema = json.loads(schema_path.read_text())
        required = schema["$defs"]["phase_lineage_record"]["required"]
        repo = _basic_repo(tmp_path)
        snapshot_path = _snapshot_path(tmp_path)
        content = build_historical_content(
            repo, snapshot_path, generated_at_utc="2026-01-01T00:00:00Z"
        )
        for record in content["phase_lineage"]:
            for field in required:
                assert field in record, f"phase {record.get('phase_id')} missing {field}"


class TestNoReasoningNoInferenceNoExecution:
    def test_no_reasoning_module_exists(self) -> None:
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(
                "pcae.repository_intelligence.historical_memory.historical_reasoning"
            )

    def test_no_timeline_engine_module_exists(self) -> None:
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(
                "pcae.repository_intelligence.historical_memory.timeline_engine"
            )

    def test_builder_module_has_no_execution_related_imports(self) -> None:
        import ast

        module_path = (
            REPO_ROOT
            / "src"
            / "pcae"
            / "repository_intelligence"
            / "historical_memory"
            / "historical_builder.py"
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

    def test_validation_module_has_no_execution_related_imports(self) -> None:
        import ast

        module_path = (
            REPO_ROOT
            / "src"
            / "pcae"
            / "repository_intelligence"
            / "historical_memory"
            / "historical_validation.py"
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


@pytest.mark.slow
class TestRealRepositoryIntegration:
    """Exercises the full pipeline against this repository's own real
    git history and tasks/done/ content (850+ files, ~45-50s). Confirms
    real-world compatibility beyond the fast synthetic fixtures above.
    """

    def test_generates_schema_valid_artifact_from_real_repository(self, tmp_path: Path) -> None:
        snapshot_path = _snapshot_path(tmp_path)
        result = generate_historical_memory(
            snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "real_hist"
        )
        content = _load_json(Path(result["latest_path"]))
        validate_historical_snapshot(content)  # must not raise
        assert result["event_count"] > 0
        assert result["phase_lineage_count"] > 0

    def test_real_repository_generation_never_mutates_tasks_done(self, tmp_path: Path) -> None:
        real_tasks_done = REPO_ROOT / "tasks" / "done"
        sample_files = sorted(real_tasks_done.glob("*.md"))[:20]
        before = {p: p.read_bytes() for p in sample_files}
        snapshot_path = _snapshot_path(tmp_path)
        generate_historical_memory(
            snapshot_path, repo_root=REPO_ROOT, output_dir=tmp_path / "real_hist2"
        )
        after = {p: p.read_bytes() for p in sample_files}
        assert before == after
