"""Phase 115D: Repository Evidence Provider Prototype.

Tests the deterministic Repository Evidence Providers implemented in
``src/pcae/core/evidence_providers.py``: the common ``EvidenceProvider``
contract, and the four concrete providers (Git/Runtime/Report/Metadata).
Providers collect evidence; they never decide. This module is
disconnected by design -- not called by the Repository Transition
Validator, any lifecycle command, Notification Policy, or ``pcae agent
verify-handoff``. These tests call it directly.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.core.evidence import EvidenceCollection, EvidenceConfidence, EvidenceDeterminism, EvidenceFreshness
from pcae.core.evidence_providers import (
    EvidenceProvider,
    EvidenceProviderContext,
    EvidenceProviderResult,
    GitEvidenceProvider,
    MetadataEvidenceProvider,
    ReportEvidenceProvider,
    RuntimeEvidenceProvider,
)
from pcae.core.paths import HarnessPath

ALL_PROVIDER_CLASSES = (
    GitEvidenceProvider,
    RuntimeEvidenceProvider,
    ReportEvidenceProvider,
    MetadataEvidenceProvider,
)


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "a@b.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "a"], cwd=path, check=True, capture_output=True)
    (path / "README.md").write_text("hello\n")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=path, check=True, capture_output=True)


def _init_git_repo_with_remote(path: Path, remote_path: Path) -> None:
    _init_git_repo(remote_path)
    subprocess.run(["git", "clone", str(remote_path), str(path)], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "a@b.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "a"], cwd=path, check=True, capture_output=True)


class TestProviderContract:
    def test_each_provider_declares_provider_id(self):
        for cls in ALL_PROVIDER_CLASSES:
            assert isinstance(cls.provider_id, str) and cls.provider_id

    def test_each_provider_declares_producer(self):
        for cls in ALL_PROVIDER_CLASSES:
            assert isinstance(cls.producer, str) and cls.producer

    def test_each_provider_declares_determinism(self):
        for cls in ALL_PROVIDER_CLASSES:
            assert isinstance(cls.determinism, EvidenceDeterminism)

    def test_each_provider_declares_categories(self):
        for cls in ALL_PROVIDER_CLASSES:
            assert isinstance(cls.categories, tuple) and len(cls.categories) > 0

    def test_each_provider_declares_required_inputs(self):
        for cls in ALL_PROVIDER_CLASSES:
            assert isinstance(cls.required_inputs, tuple) and len(cls.required_inputs) > 0

    def test_each_provider_declares_scope(self):
        for cls in ALL_PROVIDER_CLASSES:
            assert isinstance(cls.scope, str) and cls.scope

    def test_each_provider_declares_limitations(self):
        for cls in ALL_PROVIDER_CLASSES:
            assert isinstance(cls.limitations, tuple)

    def test_abstract_base_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            EvidenceProvider()

    def test_each_provider_has_collect_method(self):
        for cls in ALL_PROVIDER_CLASSES:
            assert callable(getattr(cls, "collect"))


class TestEachProviderReturnsEvidenceCollection:
    def test_git_provider_returns_result_with_collection(self, tmp_path):
        _init_git_repo(tmp_path)
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = GitEvidenceProvider().collect(ctx)
        assert isinstance(result, EvidenceProviderResult)
        assert isinstance(result.evidence, EvidenceCollection)
        assert len(result.evidence) > 0

    def test_runtime_provider_returns_result_with_collection(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = RuntimeEvidenceProvider().collect(ctx)
        assert isinstance(result, EvidenceProviderResult)
        assert isinstance(result.evidence, EvidenceCollection)
        assert len(result.evidence) == 3

    def test_report_provider_returns_result_with_collection(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = ReportEvidenceProvider().collect(ctx)
        assert isinstance(result, EvidenceProviderResult)
        assert isinstance(result.evidence, EvidenceCollection)
        assert len(result.evidence) > 0

    def test_metadata_provider_returns_result_with_collection(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = MetadataEvidenceProvider().collect(ctx)
        assert isinstance(result, EvidenceProviderResult)
        assert isinstance(result.evidence, EvidenceCollection)
        assert len(result.evidence) > 0


class TestGitEvidenceFields:
    def test_branch_evidence_present(self, tmp_path):
        _init_git_repo(tmp_path)
        subprocess.run(["git", "branch", "-m", "main"], cwd=tmp_path, check=True, capture_output=True)
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = GitEvidenceProvider().collect(ctx)
        branch_ev = result.evidence.by_id("E-git-001")
        assert branch_ev is not None
        assert branch_ev.observed_value == "main"

    def test_clean_working_tree_evidence(self, tmp_path):
        _init_git_repo(tmp_path)
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = GitEvidenceProvider().collect(ctx)
        clean_ev = result.evidence.by_id("E-git-002")
        assert clean_ev.observed_value == "clean"

    def test_dirty_working_tree_evidence(self, tmp_path):
        _init_git_repo(tmp_path)
        (tmp_path / "new_file.txt").write_text("uncommitted\n")
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = GitEvidenceProvider().collect(ctx)
        dirty_ev = result.evidence.by_id("E-git-002")
        assert dirty_ev.observed_value == "dirty"

    def test_ahead_behind_and_pushed_when_in_sync(self, tmp_path):
        remote = tmp_path / "remote.git"
        clone = tmp_path / "clone"
        _init_git_repo_with_remote(clone, remote)
        ctx = EvidenceProviderContext(root=HarnessPath(clone))
        result = GitEvidenceProvider().collect(ctx)
        assert result.evidence.by_id("E-git-003").observed_value == 0
        assert result.evidence.by_id("E-git-004").observed_value == 0
        assert result.evidence.by_id("E-git-005").observed_value == "pushed"

    def test_ahead_evidence_when_local_commit_unpushed(self, tmp_path):
        remote = tmp_path / "remote.git"
        clone = tmp_path / "clone"
        _init_git_repo_with_remote(clone, remote)
        (clone / "extra.txt").write_text("extra\n")
        subprocess.run(["git", "add", "-A"], cwd=clone, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "extra"], cwd=clone, check=True, capture_output=True)
        ctx = EvidenceProviderContext(root=HarnessPath(clone))
        result = GitEvidenceProvider().collect(ctx)
        assert result.evidence.by_id("E-git-003").observed_value == 1
        assert result.evidence.by_id("E-git-005").observed_value == "not_pushed"

    def test_categories_are_git_and_push_state(self, tmp_path):
        _init_git_repo(tmp_path)
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = GitEvidenceProvider().collect(ctx)
        seen_categories = {e.category.value for e in result.evidence}
        assert seen_categories == {"git", "push_state"}


class TestRuntimeEvidenceFields:
    def test_runtime_state_evidence(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = RuntimeEvidenceProvider().collect(ctx)
        state_ev = result.evidence.by_id("E-runtime-001")
        assert state_ev is not None
        assert isinstance(state_ev.observed_value, str) and state_ev.observed_value

    def test_execution_availability_evidence(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = RuntimeEvidenceProvider().collect(ctx)
        exec_ev = result.evidence.by_id("E-runtime-002")
        assert exec_ev.observed_value == "unavailable"

    def test_maximum_capability_evidence(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = RuntimeEvidenceProvider().collect(ctx)
        cap_ev = result.evidence.by_id("E-runtime-003")
        assert cap_ev.observed_value == "observe"


class TestReportEvidenceFields:
    def test_no_report_present_returns_exists_false(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = ReportEvidenceProvider().collect(ctx)
        exists_ev = result.evidence.by_id("E-report-001")
        assert exists_ev.observed_value is False

    def test_report_present_returns_phase_id_and_completeness(self, tmp_path):
        reports_dir = tmp_path / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "latest.json").write_text(json.dumps({
            "phase_id": "99Z",
            "report_completeness": "complete",
            "recommended_next_phase": "99Z.1 — Next Thing",
            "canonical_report_used": True,
            "trust_warnings": [],
        }))
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = ReportEvidenceProvider().collect(ctx)
        assert result.evidence.by_id("E-report-001").observed_value is True
        assert result.evidence.by_id("E-report-002").observed_value == "99Z"
        assert result.evidence.by_id("E-report-003").observed_value == "complete"
        assert result.evidence.by_id("E-report-004").observed_value == "99Z.1 — Next Thing"
        assert result.evidence.by_id("E-report-005").observed_value == "consistent"

    def test_report_with_trust_warnings_is_inconsistent(self, tmp_path):
        reports_dir = tmp_path / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "latest.json").write_text(json.dumps({
            "phase_id": "99Z",
            "report_completeness": "partial",
            "recommended_next_phase": "99Z.1",
            "canonical_report_used": True,
            "trust_warnings": ["canonical report and metadata disagree"],
        }))
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = ReportEvidenceProvider().collect(ctx)
        assert result.evidence.by_id("E-report-005").observed_value == "inconsistent"


class TestMetadataEvidenceFields:
    def test_no_metadata_present_returns_exists_false(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = MetadataEvidenceProvider().collect(ctx)
        exists_ev = result.evidence.by_id("E-metadata-001")
        assert exists_ev.observed_value is False

    def test_metadata_present_returns_declared_fields(self, tmp_path):
        pcae_dir = tmp_path / ".pcae"
        pcae_dir.mkdir(parents=True)
        (pcae_dir / "phase-completion-metadata.json").write_text(json.dumps({
            "phase_id": "99Z",
            "pushed_status": "pushed",
            "origin_main_head_count": 0,
            "recommended_next_phase": "99Z.1 — Next Thing",
        }))
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = MetadataEvidenceProvider().collect(ctx)
        assert result.evidence.by_id("E-metadata-001").observed_value is True
        assert result.evidence.by_id("E-metadata-002").observed_value == "99Z"
        assert result.evidence.by_id("E-metadata-003").observed_value == "pushed"
        assert result.evidence.by_id("E-metadata-004").observed_value == 0
        assert result.evidence.by_id("E-metadata-005").observed_value == "99Z.1 — Next Thing"


class TestNoMutation:
    def test_git_provider_does_not_change_working_tree(self, tmp_path):
        _init_git_repo(tmp_path)
        before = subprocess.run(
            ["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True,
        ).stdout
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        GitEvidenceProvider().collect(ctx)
        after = subprocess.run(
            ["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True,
        ).stdout
        assert before == after

    def test_git_provider_creates_no_new_files(self, tmp_path):
        _init_git_repo(tmp_path)
        before = set(tmp_path.rglob("*"))
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        GitEvidenceProvider().collect(ctx)
        after = set(tmp_path.rglob("*"))
        assert before == after

    def test_report_provider_does_not_write_files(self, tmp_path):
        before = list(tmp_path.rglob("*"))
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        ReportEvidenceProvider().collect(ctx)
        after = list(tmp_path.rglob("*"))
        assert before == after

    def test_metadata_provider_does_not_write_files(self, tmp_path):
        before = list(tmp_path.rglob("*"))
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        MetadataEvidenceProvider().collect(ctx)
        after = list(tmp_path.rglob("*"))
        assert before == after

    def test_evidence_collection_is_immutable_after_collect(self, tmp_path):
        _init_git_repo(tmp_path)
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = GitEvidenceProvider().collect(ctx)
        import dataclasses
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.evidence.items = ()


class TestNoModelIdentity:
    """115B: providers never depend on model/agent identity. No field
    anywhere in the provider contract, result, or produced evidence
    carries a model/agent/backend identity."""

    def test_no_model_identity_field_on_provider_result(self):
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(EvidenceProviderResult)}
        assert not (field_names & {"model_id", "agent_id", "backend_id", "vendor"})

    def test_no_model_identity_field_on_provider_context(self):
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(EvidenceProviderContext)}
        assert not (field_names & {"model_id", "agent_id", "backend_id", "vendor"})

    def test_source_module_never_references_model_identity(self):
        import pcae.core.evidence_providers as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("model_id", "agent_id", "backend_id", "vendor="):
            assert forbidden not in source


class TestDeterministicClassification:
    def test_all_four_providers_declare_deterministic(self):
        for cls in ALL_PROVIDER_CLASSES:
            assert cls.determinism is EvidenceDeterminism.DETERMINISTIC

    def test_all_produced_evidence_declares_deterministic(self, tmp_path):
        _init_git_repo(tmp_path)
        reports_dir = tmp_path / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "latest.json").write_text(json.dumps({
            "phase_id": "99Z", "report_completeness": "complete",
            "recommended_next_phase": "99Z.1", "canonical_report_used": True,
            "trust_warnings": [],
        }))
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps({
            "phase_id": "99Z", "pushed_status": "pushed",
            "origin_main_head_count": 0, "recommended_next_phase": "99Z.1",
        }))
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        for cls in ALL_PROVIDER_CLASSES:
            result = cls().collect(ctx)
            for ev in result.evidence:
                assert ev.determinism is EvidenceDeterminism.DETERMINISTIC


class TestGracefulUnknownEvidence:
    def test_git_provider_no_origin_main_degrades_to_unknown(self, tmp_path):
        _init_git_repo(tmp_path)
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = GitEvidenceProvider().collect(ctx)
        ahead_ev = result.evidence.by_id("E-git-003")
        assert ahead_ev.freshness == EvidenceFreshness.UNKNOWN
        assert ahead_ev.confidence == EvidenceConfidence.UNKNOWN
        assert ahead_ev.observed_value == "unavailable"

    def test_git_provider_no_crash_without_origin(self, tmp_path):
        _init_git_repo(tmp_path)
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = GitEvidenceProvider().collect(ctx)
        assert len(result.evidence) == 5

    def test_report_provider_missing_report_no_crash(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = ReportEvidenceProvider().collect(ctx)
        for evidence_id in ("E-report-002", "E-report-003", "E-report-004", "E-report-005"):
            ev = result.evidence.by_id(evidence_id)
            assert ev.observed_value == "unavailable"
            assert ev.freshness == EvidenceFreshness.UNKNOWN

    def test_metadata_provider_missing_metadata_no_crash(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = MetadataEvidenceProvider().collect(ctx)
        for evidence_id in ("E-metadata-002", "E-metadata-003", "E-metadata-004", "E-metadata-005"):
            ev = result.evidence.by_id(evidence_id)
            assert ev.observed_value == "unavailable"

    def test_runtime_provider_strict_reraises_on_failure(self, tmp_path, monkeypatch):
        import pcae.core.runtime_snapshot as runtime_snapshot_module

        def _boom(root, registry):
            raise RuntimeError("simulated snapshot failure")

        monkeypatch.setattr(runtime_snapshot_module, "build_runtime_snapshot", _boom)
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path), strict=True)
        with pytest.raises(RuntimeError, match="simulated snapshot failure"):
            RuntimeEvidenceProvider().collect(ctx)

    def test_runtime_provider_non_strict_degrades_on_failure(self, tmp_path, monkeypatch):
        import pcae.core.runtime_snapshot as runtime_snapshot_module

        def _boom(root, registry):
            raise RuntimeError("simulated snapshot failure")

        monkeypatch.setattr(runtime_snapshot_module, "build_runtime_snapshot", _boom)
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path), strict=False)
        result = RuntimeEvidenceProvider().collect(ctx)
        ev = result.evidence.by_id("E-runtime-001")
        assert ev.observed_value == "unavailable"
        assert ev.freshness == EvidenceFreshness.UNKNOWN

    def test_report_provider_corrupt_json_non_strict_degrades(self, tmp_path):
        reports_dir = tmp_path / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "latest.json").write_text("{ not valid json")
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path), strict=False)
        result = ReportEvidenceProvider().collect(ctx)
        ev = result.evidence.by_id("E-report-001")
        assert ev.observed_value == "unavailable"

    def test_report_provider_corrupt_json_strict_raises(self, tmp_path):
        reports_dir = tmp_path / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "latest.json").write_text("{ not valid json")
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path), strict=True)
        with pytest.raises(Exception):
            ReportEvidenceProvider().collect(ctx)


class TestSerializationCompatibilityWithEvidence:
    def test_git_provider_evidence_round_trips(self, tmp_path):
        _init_git_repo(tmp_path)
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = GitEvidenceProvider().collect(ctx)
        d = result.evidence.to_dict()
        text = json.dumps(d)
        restored = EvidenceCollection.from_dict(json.loads(text))
        assert restored == result.evidence

    def test_runtime_provider_evidence_round_trips(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = RuntimeEvidenceProvider().collect(ctx)
        text = json.dumps(result.evidence.to_dict())
        restored = EvidenceCollection.from_dict(json.loads(text))
        assert restored == result.evidence

    def test_report_provider_evidence_round_trips(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = ReportEvidenceProvider().collect(ctx)
        text = json.dumps(result.evidence.to_dict())
        restored = EvidenceCollection.from_dict(json.loads(text))
        assert restored == result.evidence

    def test_metadata_provider_evidence_round_trips(self, tmp_path):
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        result = MetadataEvidenceProvider().collect(ctx)
        text = json.dumps(result.evidence.to_dict())
        restored = EvidenceCollection.from_dict(json.loads(text))
        assert restored == result.evidence

    def test_all_evidence_items_are_evidence_instances(self, tmp_path):
        _init_git_repo(tmp_path)
        ctx = EvidenceProviderContext(root=HarnessPath(tmp_path))
        for cls in ALL_PROVIDER_CLASSES:
            result = cls().collect(ctx)
            from pcae.core.evidence import Evidence
            for ev in result.evidence:
                assert isinstance(ev, Evidence)
