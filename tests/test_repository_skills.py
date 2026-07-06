"""Phase 115J: Repository Skills Prototype.

Tests the first Repository Skills framework implemented in
``src/pcae/core/repository_skills.py``: the common ``RepositorySkill``
contract, ``RepositorySkillManifest``, ``RepositorySkillContext``,
``RepositorySkillResult``, ``RepositorySkillRegistry``, and four
deterministic skills wrapping 115D's Evidence Providers unmodified.
Skills produce evidence; they never decide. This module is
disconnected by design -- not called by the Repository Transition
Validator, Decision Evaluation, any lifecycle command, or Notification
Policy. These tests call it directly.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pcae.core.evidence import EvidenceCategory, EvidenceCollection, EvidenceConfidence, EvidenceDeterminism
from pcae.core.paths import HarnessPath
from pcae.core.repository_skills import (
    GitRepositorySkill,
    MetadataRepositorySkill,
    RepositorySkill,
    RepositorySkillCapability,
    RepositorySkillContext,
    RepositorySkillManifest,
    RepositorySkillRegistry,
    RepositorySkillResult,
    RepositorySkillStatus,
    ReportRepositorySkill,
    RuntimeRepositorySkill,
    build_default_registry,
)

ALL_SKILL_CLASSES = (
    GitRepositorySkill,
    RuntimeRepositorySkill,
    ReportRepositorySkill,
    MetadataRepositorySkill,
)


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "a@b.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "a"], cwd=path, check=True, capture_output=True)
    (path / "README.md").write_text("hello\n")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=path, check=True, capture_output=True)


def _ctx(tmp_path: Path, strict: bool = False) -> RepositorySkillContext:
    return RepositorySkillContext(root=HarnessPath(tmp_path), strict=strict)


class TestSkillContract:
    def test_abstract_base_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            RepositorySkill()  # type: ignore[abstract]

    def test_each_skill_declares_manifest(self):
        for cls in ALL_SKILL_CLASSES:
            assert isinstance(cls.manifest, RepositorySkillManifest)

    def test_each_skill_has_invoke_method(self):
        for cls in ALL_SKILL_CLASSES:
            assert hasattr(cls, "invoke")
            assert callable(cls.invoke)

    def test_each_skill_declares_at_least_one_capability(self):
        for cls in ALL_SKILL_CLASSES:
            assert len(cls.manifest.capabilities) >= 1

    def test_each_skill_declares_deterministic_determinism(self):
        for cls in ALL_SKILL_CLASSES:
            assert cls.manifest.determinism == EvidenceDeterminism.DETERMINISTIC

    def test_each_skill_declares_none_side_effect_policy(self):
        for cls in ALL_SKILL_CLASSES:
            assert cls.manifest.side_effect_policy == "none"

    def test_each_skill_manifest_carries_no_model_identity_field(self):
        forbidden_names = {"agent_id", "model", "model_id", "backend", "backend_id", "vendor"}
        for cls in ALL_SKILL_CLASSES:
            import dataclasses
            field_names = {f.name for f in dataclasses.fields(cls.manifest)}
            assert not (field_names & forbidden_names)


class TestManifest:
    def test_rejects_empty_skill_id(self):
        with pytest.raises(ValueError, match="skill_id"):
            RepositorySkillManifest(
                skill_id="", name="x", version="1.0",
                capabilities=(RepositorySkillCapability.GIT_ANALYSIS,),
                determinism=EvidenceDeterminism.DETERMINISTIC,
                confidence_policy=EvidenceConfidence.HIGH,
                evidence_categories=(EvidenceCategory.GIT,),
                required_inputs=(),
            )

    def test_rejects_empty_capabilities(self):
        with pytest.raises(ValueError, match="capabilities"):
            RepositorySkillManifest(
                skill_id="x", name="x", version="1.0",
                capabilities=(),
                determinism=EvidenceDeterminism.DETERMINISTIC,
                confidence_policy=EvidenceConfidence.HIGH,
                evidence_categories=(EvidenceCategory.GIT,),
                required_inputs=(),
            )

    def test_rejects_non_none_side_effect_policy(self):
        with pytest.raises(ValueError, match="side_effect_policy"):
            RepositorySkillManifest(
                skill_id="x", name="x", version="1.0",
                capabilities=(RepositorySkillCapability.GIT_ANALYSIS,),
                determinism=EvidenceDeterminism.DETERMINISTIC,
                confidence_policy=EvidenceConfidence.HIGH,
                evidence_categories=(EvidenceCategory.GIT,),
                required_inputs=(),
                side_effect_policy="commit",
            )

    def test_rejects_invalid_failure_policy(self):
        with pytest.raises(ValueError, match="failure_policy"):
            RepositorySkillManifest(
                skill_id="x", name="x", version="1.0",
                capabilities=(RepositorySkillCapability.GIT_ANALYSIS,),
                determinism=EvidenceDeterminism.DETERMINISTIC,
                confidence_policy=EvidenceConfidence.HIGH,
                evidence_categories=(EvidenceCategory.GIT,),
                required_inputs=(),
                failure_policy="ignore",
            )

    def test_model_produced_and_experimental_default_false(self):
        manifest = RepositorySkillManifest(
            skill_id="x", name="x", version="1.0",
            capabilities=(RepositorySkillCapability.GIT_ANALYSIS,),
            determinism=EvidenceDeterminism.DETERMINISTIC,
            confidence_policy=EvidenceConfidence.HIGH,
            evidence_categories=(EvidenceCategory.GIT,),
            required_inputs=(),
        )
        assert manifest.model_produced is False
        assert manifest.experimental is False

    def test_all_eight_capabilities_are_frozen(self):
        values = {c.value for c in RepositorySkillCapability}
        assert values == {
            "git_analysis", "runtime_analysis", "architecture_analysis",
            "documentation_analysis", "report_analysis", "metadata_analysis",
            "dependency_analysis", "ai_review",
        }


class TestRegistryRegistration:
    def test_register_and_get(self):
        registry = RepositorySkillRegistry()
        skill = GitRepositorySkill()
        registry.register(skill)
        assert registry.get("git_repository_skill") is skill

    def test_get_unknown_skill_id_returns_none(self):
        registry = RepositorySkillRegistry()
        assert registry.get("nonexistent") is None

    def test_duplicate_skill_id_rejected(self):
        registry = RepositorySkillRegistry()
        registry.register(GitRepositorySkill())
        with pytest.raises(ValueError, match="Duplicate skill_id"):
            registry.register(GitRepositorySkill())

    def test_list_skills(self):
        registry = build_default_registry()
        ids = {s.manifest.skill_id for s in registry.list_skills()}
        assert ids == {
            "git_repository_skill", "runtime_repository_skill",
            "report_repository_skill", "metadata_repository_skill",
        }

    def test_list_manifests(self):
        registry = build_default_registry()
        manifests = registry.list_manifests()
        assert len(manifests) == 4
        assert all(isinstance(m, RepositorySkillManifest) for m in manifests)


class TestSkillLookup:
    def test_filter_by_capability(self):
        registry = build_default_registry()
        git_skills = registry.filter_by_capability(RepositorySkillCapability.GIT_ANALYSIS)
        assert [s.manifest.skill_id for s in git_skills] == ["git_repository_skill"]

    def test_filter_by_capability_no_match(self):
        registry = build_default_registry()
        ai_skills = registry.filter_by_capability(RepositorySkillCapability.AI_REVIEW)
        assert ai_skills == ()

    def test_filter_by_category(self):
        registry = build_default_registry()
        runtime_skills = registry.filter_by_category(EvidenceCategory.RUNTIME)
        assert [s.manifest.skill_id for s in runtime_skills] == ["runtime_repository_skill"]

    def test_filter_by_category_matches_push_state_for_git_skill(self):
        registry = build_default_registry()
        push_state_skills = registry.filter_by_category(EvidenceCategory.PUSH_STATE)
        assert [s.manifest.skill_id for s in push_state_skills] == ["git_repository_skill"]


class TestDeterministicSkillsReturnEvidenceCollection:
    def test_git_skill_returns_evidence_collection(self, tmp_path):
        _init_git_repo(tmp_path)
        result = GitRepositorySkill().invoke(_ctx(tmp_path))
        assert result.status == RepositorySkillStatus.SUCCESS
        assert isinstance(result.evidence, EvidenceCollection)
        assert len(result.evidence) > 0

    def test_runtime_skill_returns_evidence_collection(self, tmp_path):
        result = RuntimeRepositorySkill().invoke(_ctx(tmp_path))
        assert result.status == RepositorySkillStatus.SUCCESS
        assert isinstance(result.evidence, EvidenceCollection)
        assert len(result.evidence) == 3

    def test_report_skill_returns_evidence_collection(self, tmp_path):
        result = ReportRepositorySkill().invoke(_ctx(tmp_path))
        assert result.status == RepositorySkillStatus.SUCCESS
        assert isinstance(result.evidence, EvidenceCollection)
        assert len(result.evidence) > 0

    def test_metadata_skill_returns_evidence_collection(self, tmp_path):
        result = MetadataRepositorySkill().invoke(_ctx(tmp_path))
        assert result.status == RepositorySkillStatus.SUCCESS
        assert isinstance(result.evidence, EvidenceCollection)
        assert len(result.evidence) > 0

    def test_git_skill_evidence_reuses_115d_evidence_ids(self, tmp_path):
        _init_git_repo(tmp_path)
        result = GitRepositorySkill().invoke(_ctx(tmp_path))
        ids = {item.evidence_id for item in result.evidence}
        assert ids == {"E-git-001", "E-git-002", "E-git-003", "E-git-004", "E-git-005"}

    def test_no_report_present_returns_exists_false_evidence(self, tmp_path):
        result = ReportRepositorySkill().invoke(_ctx(tmp_path))
        exists_item = result.evidence.by_id("E-report-001")
        assert exists_item is not None
        assert exists_item.observed_value is False


class TestMultiSkillInvocation:
    def test_invoke_many_returns_one_result_per_skill(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        results = registry.invoke_many(
            ("git_repository_skill", "runtime_repository_skill"), _ctx(tmp_path),
        )
        assert len(results) == 2
        assert all(r.status == RepositorySkillStatus.SUCCESS for r in results)

    def test_invoke_all_runs_every_registered_skill(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        results = registry.invoke_all(_ctx(tmp_path))
        assert len(results) == 4
        assert {r.skill_id for r in results} == {
            "git_repository_skill", "runtime_repository_skill",
            "report_repository_skill", "metadata_repository_skill",
        }

    def test_invoke_unknown_skill_id_returns_failed_result(self, tmp_path):
        registry = build_default_registry()
        result = registry.invoke("nonexistent", _ctx(tmp_path))
        assert result.status == RepositorySkillStatus.FAILED
        assert result.failure_reason


class TestEvidenceMerging:
    def test_merge_combines_all_success_results(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        results = registry.invoke_all(_ctx(tmp_path))
        merged = registry.merge_evidence(results)
        assert isinstance(merged, EvidenceCollection)
        expected_total = sum(len(r.evidence) for r in results)
        assert len(merged) == expected_total

    def test_merge_excludes_failed_results(self, tmp_path):
        registry = build_default_registry()
        failed = RepositorySkillResult(
            skill_id="broken", status=RepositorySkillStatus.FAILED, failure_reason="boom",
        )
        success = GitRepositorySkill().invoke(_ctx(tmp_path))
        merged = registry.merge_evidence((failed, success))
        assert len(merged) == len(success.evidence)

    def test_merge_of_all_default_skills_has_no_duplicate_ids(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        results = registry.invoke_all(_ctx(tmp_path))
        merged = registry.merge_evidence(results)
        ids = [item.evidence_id for item in merged]
        assert len(ids) == len(set(ids))


class TestFailureBehavior:
    def test_result_with_failed_status_requires_failure_reason(self):
        with pytest.raises(ValueError, match="failure_reason"):
            RepositorySkillResult(skill_id="x", status=RepositorySkillStatus.FAILED)

    def test_success_result_can_have_empty_evidence(self):
        result = RepositorySkillResult(skill_id="x", status=RepositorySkillStatus.SUCCESS)
        assert result.evidence == EvidenceCollection()

    def test_provider_internal_failure_degrades_to_unknown_evidence_not_skill_failure(self, tmp_path):
        """115D providers already degrade internal failures to honest
        UNKNOWN evidence rather than raising -- the wrapping skill
        therefore reports SUCCESS (it did produce evidence), and that
        evidence is itself honestly UNKNOWN. No git repo exists at
        tmp_path here, so branch/status/ahead/behind collection fails
        gracefully at the provider level."""
        result = GitRepositorySkill().invoke(_ctx(tmp_path))
        assert result.status == RepositorySkillStatus.SUCCESS
        from pcae.core.evidence import EvidenceFreshness
        assert any(item.freshness == EvidenceFreshness.UNKNOWN for item in result.evidence)

    def test_strict_context_reraises_unexpected_failure(self, tmp_path, monkeypatch):
        skill = RuntimeRepositorySkill()

        def _boom(self, context):
            raise RuntimeError("synthetic failure")

        import pcae.core.evidence_providers as providers_module
        monkeypatch.setattr(providers_module.RuntimeEvidenceProvider, "collect", _boom)

        with pytest.raises(RuntimeError, match="synthetic failure"):
            skill.invoke(_ctx(tmp_path, strict=True))

    def test_non_strict_context_returns_explicit_failure_on_unexpected_exception(self, tmp_path, monkeypatch):
        skill = RuntimeRepositorySkill()

        def _boom(self, context):
            raise RuntimeError("synthetic failure")

        import pcae.core.evidence_providers as providers_module
        monkeypatch.setattr(providers_module.RuntimeEvidenceProvider, "collect", _boom)

        result = skill.invoke(_ctx(tmp_path, strict=False))
        assert result.status == RepositorySkillStatus.FAILED
        assert "synthetic failure" in result.failure_reason

    def test_no_silent_success_on_failure(self, tmp_path, monkeypatch):
        skill = GitRepositorySkill()

        def _boom(self, context):
            raise RuntimeError("boom")

        import pcae.core.evidence_providers as providers_module
        monkeypatch.setattr(providers_module.GitEvidenceProvider, "collect", _boom)

        result = skill.invoke(_ctx(tmp_path, strict=False))
        assert result.status == RepositorySkillStatus.FAILED
        assert len(result.evidence) == 0


class TestNoMutation:
    def test_git_skill_does_not_change_working_tree(self, tmp_path):
        _init_git_repo(tmp_path)
        before = subprocess.run(
            ["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True,
        ).stdout
        GitRepositorySkill().invoke(_ctx(tmp_path))
        after = subprocess.run(
            ["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True,
        ).stdout
        assert before == after == ""

    def test_no_skill_module_imports_subprocess_directly(self):
        import pcae.core.repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "import subprocess" not in source
        assert "subprocess.run" not in source

    def test_registry_has_no_write_methods(self):
        forbidden = {"commit", "push", "finalize", "notify", "promote", "authorize", "mutate", "execute"}
        public_methods = {
            name for name in dir(RepositorySkillRegistry)
            if not name.startswith("_") and callable(getattr(RepositorySkillRegistry, name))
        }
        assert not (public_methods & forbidden)


class TestNoAiSlmLlmSkill:
    def test_no_advisory_or_probabilistic_skill_registered_by_default(self):
        registry = build_default_registry()
        for skill in registry.list_skills():
            assert skill.manifest.determinism == EvidenceDeterminism.DETERMINISTIC
            assert skill.manifest.model_produced is False

    def test_ai_review_capability_declared_but_unimplemented(self):
        registry = build_default_registry()
        ai_skills = registry.filter_by_capability(RepositorySkillCapability.AI_REVIEW)
        assert ai_skills == ()

    def test_no_deepseek_or_model_backend_import_in_module_source(self):
        import pcae.core.repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in ("deepseek", "openai", "anthropic", "glm", "qwen"):
            assert not any(forbidden in line.lower() for line in import_lines)


class TestNoLifecycleIntegration:
    def test_module_never_imports_lifecycle_commands(self):
        import pcae.core.repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        assert not any("pcae.commands" in line for line in import_lines)

    def test_module_never_imports_decision_evaluation(self):
        import pcae.core.repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        assert not any("decision_evaluation" in line for line in import_lines)

    def test_module_never_imports_repository_transition_validator(self):
        import pcae.core.repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        assert not any("repository_transition_validator" in line for line in import_lines)

    def test_phase_complete_command_never_reads_repository_skills(self):
        import pcae.commands.phase as phase_module
        source = Path(phase_module.__file__).read_text(encoding="utf-8")
        assert "repository_skills" not in source

    def test_task_command_never_reads_repository_skills(self):
        import pcae.commands.task as task_module
        source = Path(task_module.__file__).read_text(encoding="utf-8")
        assert "repository_skills" not in source


class TestExecutionUnavailable:
    def test_no_skill_manifest_declares_execution_capability(self):
        registry = build_default_registry()
        for manifest in registry.list_manifests():
            assert manifest.side_effect_policy == "none"

    def test_module_never_imports_subprocess_or_os_system(self):
        import pcae.core.repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "import subprocess" not in source
        assert "os.system" not in source
        assert "Popen(" not in source
