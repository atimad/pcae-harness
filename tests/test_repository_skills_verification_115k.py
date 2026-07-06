"""Phase 115K: Repository Skills Verification & Compatibility.

Verification-only phase proving 115J's Repository Skills prototype
(``src/pcae/core/repository_skills.py``) is deterministic, read-only,
evidence-only, and fully compatible with the existing Evidence
Provider (115D) and Decision Evaluation (115E) architecture. No new
skill is implemented here; no Repository Skill is wired into Decision
Evaluation or the Repository Transition Validator by this phase --
this module only *proves*, via tests, that such wiring would be safe
in a future integration-design phase, without performing it.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pcae.core.decision_evaluation import EvaluationContext, InvariantStatus, evaluate
from pcae.core.evidence import EvidenceCollection
from pcae.core.evidence_providers import (
    EvidenceProviderContext,
    GitEvidenceProvider,
    MetadataEvidenceProvider,
    ReportEvidenceProvider,
    RuntimeEvidenceProvider,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_skills import (
    GitRepositorySkill,
    MetadataRepositorySkill,
    RepositorySkillContext,
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


def _provider_ctx(tmp_path: Path, strict: bool = False) -> EvidenceProviderContext:
    return EvidenceProviderContext(root=HarnessPath(tmp_path), strict=strict)


# ═══════════════════════════════════════════════════════════════════════
# Objective 1: skill purity
# ═══════════════════════════════════════════════════════════════════════

class TestSkillPurity:
    def test_every_skill_invocation_is_read_only(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        before = subprocess.run(
            ["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True,
        ).stdout
        registry.invoke_all(_ctx(tmp_path))
        after = subprocess.run(
            ["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True,
        ).stdout
        assert before == after

    def test_every_skill_produces_only_evidence_collection(self, tmp_path):
        _init_git_repo(tmp_path)
        for cls in ALL_SKILL_CLASSES:
            result = cls().invoke(_ctx(tmp_path))
            assert isinstance(result.evidence, EvidenceCollection)

    def test_no_skill_result_carries_a_transition_verdict_field(self):
        field_names = {f.name for f in __import__("dataclasses").fields(RepositorySkillResult)}
        assert "verdict" not in field_names
        assert {"skill_id", "status", "evidence", "failure_reason"} <= field_names

    def test_no_skill_creates_new_files_on_disk(self, tmp_path):
        _init_git_repo(tmp_path)
        before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if ".git" not in p.parts)
        build_default_registry().invoke_all(_ctx(tmp_path))
        after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if ".git" not in p.parts)
        assert before == after

    def test_no_manifest_or_result_field_identifies_a_proposing_model(self):
        import dataclasses
        forbidden = {"agent_id", "model", "model_id", "backend", "backend_id", "vendor", "proposer"}
        for cls in ALL_SKILL_CLASSES:
            manifest_fields = {f.name for f in dataclasses.fields(cls.manifest)}
            assert not (manifest_fields & forbidden)
        result_fields = {f.name for f in dataclasses.fields(RepositorySkillResult)}
        assert not (result_fields & forbidden)

    def test_evidence_provenance_producer_is_a_class_label_not_an_agent_identity(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        results = registry.invoke_all(_ctx(tmp_path))
        merged = registry.merge_evidence(results)
        producers = {item.provenance.producer for item in merged}
        for producer in producers:
            assert producer.endswith("Provider")
            assert producer.lower() not in ("claude", "deepseek", "gpt", "codex", "human")


# ═══════════════════════════════════════════════════════════════════════
# Objective 2: registry determinism
# ═══════════════════════════════════════════════════════════════════════

class TestRegistryDeterminism:
    def test_skill_registration_order_is_preserved_deterministically(self):
        registry = build_default_registry()
        ids = [s.manifest.skill_id for s in registry.list_skills()]
        assert ids == [
            "git_repository_skill", "runtime_repository_skill",
            "report_repository_skill", "metadata_repository_skill",
        ]

    def test_skill_lookup_is_deterministic_across_repeated_calls(self):
        registry = build_default_registry()
        first = registry.get("git_repository_skill")
        second = registry.get("git_repository_skill")
        assert first is second

    def test_list_skills_ordering_is_stable_across_repeated_calls(self):
        registry = build_default_registry()
        first = [s.manifest.skill_id for s in registry.list_skills()]
        second = [s.manifest.skill_id for s in registry.list_skills()]
        assert first == second

    def test_multi_skill_invocation_order_matches_requested_order(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        requested = ("metadata_repository_skill", "git_repository_skill", "runtime_repository_skill")
        results = registry.invoke_many(requested, _ctx(tmp_path))
        assert tuple(r.skill_id for r in results) == requested

    def test_duplicate_skill_ids_rejected_deterministically(self):
        registry = RepositorySkillRegistry()
        registry.register(GitRepositorySkill())
        for _ in range(3):
            with pytest.raises(ValueError, match="Duplicate skill_id"):
                registry.register(GitRepositorySkill())

    def test_merged_evidence_collection_is_deterministic_across_repeated_runs(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        merges = []
        for _ in range(10):
            results = registry.invoke_all(_ctx(tmp_path))
            merges.append(registry.merge_evidence(results))
        first_ids = tuple(item.evidence_id for item in merges[0])
        for merged in merges[1:]:
            assert tuple(item.evidence_id for item in merged) == first_ids
            for a, b in zip(merges[0], merged):
                assert a.observed_value == b.observed_value
                assert a.freshness == b.freshness
                assert a.confidence == b.confidence

    def test_merge_order_is_independent_of_invocation_order(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        forward = registry.invoke_many(
            ("git_repository_skill", "runtime_repository_skill", "report_repository_skill", "metadata_repository_skill"),
            _ctx(tmp_path),
        )
        backward = registry.invoke_many(
            ("metadata_repository_skill", "report_repository_skill", "runtime_repository_skill", "git_repository_skill"),
            _ctx(tmp_path),
        )
        forward_ids = {item.evidence_id for item in registry.merge_evidence(forward)}
        backward_ids = {item.evidence_id for item in registry.merge_evidence(backward)}
        assert forward_ids == backward_ids


# ═══════════════════════════════════════════════════════════════════════
# Objective 3: provider compatibility
# ═══════════════════════════════════════════════════════════════════════

class TestProviderCompatibility:
    def test_git_skill_evidence_matches_direct_provider_evidence(self, tmp_path):
        _init_git_repo(tmp_path)
        direct = GitEvidenceProvider().collect(_provider_ctx(tmp_path)).evidence
        via_skill = GitRepositorySkill().invoke(_ctx(tmp_path)).evidence
        assert {i.evidence_id for i in direct} == {i.evidence_id for i in via_skill}
        for item in direct:
            counterpart = via_skill.by_id(item.evidence_id)
            assert counterpart is not None
            assert counterpart.observed_value == item.observed_value
            assert counterpart.freshness == item.freshness
            assert counterpart.confidence == item.confidence

    def test_runtime_skill_evidence_matches_direct_provider_evidence(self, tmp_path):
        direct = RuntimeEvidenceProvider().collect(_provider_ctx(tmp_path)).evidence
        via_skill = RuntimeRepositorySkill().invoke(_ctx(tmp_path)).evidence
        for item in direct:
            counterpart = via_skill.by_id(item.evidence_id)
            assert counterpart is not None
            assert counterpart.observed_value == item.observed_value

    def test_report_skill_evidence_matches_direct_provider_evidence(self, tmp_path):
        direct = ReportEvidenceProvider().collect(_provider_ctx(tmp_path)).evidence
        via_skill = ReportRepositorySkill().invoke(_ctx(tmp_path)).evidence
        for item in direct:
            counterpart = via_skill.by_id(item.evidence_id)
            assert counterpart is not None
            assert counterpart.observed_value == item.observed_value

    def test_metadata_skill_evidence_matches_direct_provider_evidence(self, tmp_path):
        direct = MetadataEvidenceProvider().collect(_provider_ctx(tmp_path)).evidence
        via_skill = MetadataRepositorySkill().invoke(_ctx(tmp_path)).evidence
        for item in direct:
            counterpart = via_skill.by_id(item.evidence_id)
            assert counterpart is not None
            assert counterpart.observed_value == item.observed_value

    def test_skill_and_provider_declare_the_same_determinism(self):
        pairs = (
            (GitRepositorySkill, GitEvidenceProvider),
            (RuntimeRepositorySkill, RuntimeEvidenceProvider),
            (ReportRepositorySkill, ReportEvidenceProvider),
            (MetadataRepositorySkill, MetadataEvidenceProvider),
        )
        for skill_cls, provider_cls in pairs:
            assert skill_cls.manifest.determinism == provider_cls.determinism

    def test_skill_required_inputs_match_wrapped_provider(self):
        pairs = (
            (GitRepositorySkill, GitEvidenceProvider),
            (RuntimeRepositorySkill, RuntimeEvidenceProvider),
            (ReportRepositorySkill, ReportEvidenceProvider),
            (MetadataRepositorySkill, MetadataEvidenceProvider),
        )
        for skill_cls, provider_cls in pairs:
            assert skill_cls.manifest.required_inputs == provider_cls.required_inputs


# ═══════════════════════════════════════════════════════════════════════
# Objective 4: failure behavior
# ═══════════════════════════════════════════════════════════════════════

class TestFailureBehaviorVerification:
    def test_missing_git_repository_degrades_to_unknown_not_silent_success(self, tmp_path):
        from pcae.core.evidence import EvidenceFreshness
        result = GitRepositorySkill().invoke(_ctx(tmp_path))
        assert result.status == RepositorySkillStatus.SUCCESS
        assert all(item.freshness == EvidenceFreshness.UNKNOWN for item in result.evidence)

    def test_missing_report_and_metadata_files_degrade_to_unknown(self, tmp_path):
        from pcae.core.evidence import EvidenceFreshness
        report_result = ReportRepositorySkill().invoke(_ctx(tmp_path))
        metadata_result = MetadataRepositorySkill().invoke(_ctx(tmp_path))
        assert report_result.evidence.by_id("E-report-001").observed_value is False
        assert metadata_result.evidence.by_id("E-metadata-001").observed_value is False
        # exists=False is itself a valid CURRENT observation (not UNKNOWN);
        # only the fields that could not be derived degrade to UNKNOWN.
        assert metadata_result.evidence.by_id("E-metadata-002").freshness == EvidenceFreshness.UNKNOWN

    def test_no_result_ever_reports_success_with_a_failure_reason_set(self, tmp_path):
        _init_git_repo(tmp_path)
        for cls in ALL_SKILL_CLASSES:
            result = cls().invoke(_ctx(tmp_path))
            if result.status == RepositorySkillStatus.SUCCESS:
                assert result.failure_reason is None

    def test_explicit_failure_never_carries_evidence(self, tmp_path, monkeypatch):
        import pcae.core.evidence_providers as providers_module

        def _boom(self, context):
            raise RuntimeError("synthetic")

        monkeypatch.setattr(providers_module.GitEvidenceProvider, "collect", _boom)
        result = GitRepositorySkill().invoke(_ctx(tmp_path, strict=False))
        assert result.status == RepositorySkillStatus.FAILED
        assert len(result.evidence) == 0
        assert result.failure_reason


# ═══════════════════════════════════════════════════════════════════════
# Objective 5: no hidden integration
# ═══════════════════════════════════════════════════════════════════════

class TestNoHiddenIntegration:
    @pytest.mark.parametrize("module_path", [
        "pcae.core.decision_evaluation",
        "pcae.core.repository_transition_validator",
        "pcae.core.repository_transition_integration",
        "pcae.commands.phase",
        "pcae.commands.task",
        "pcae.commands.push",
        "pcae.core.notification_certification",
        "pcae.core.handoff_verification",
        "pcae.core.post_push_canonicalization",
    ])
    def test_module_never_references_repository_skills(self, module_path):
        import importlib
        module = importlib.import_module(module_path)
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "repository_skills" not in source, f"{module_path} unexpectedly references repository_skills"

    def test_runtime_inspect_command_never_references_repository_skills(self):
        import pcae.commands.runtime_inspect as runtime_inspect_module
        source = Path(runtime_inspect_module.__file__).read_text(encoding="utf-8")
        assert "repository_skills" not in source

    def test_repository_skills_module_never_imports_lifecycle_or_decision_or_validator(self):
        import pcae.core.repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in (
            "decision_evaluation", "repository_transition_validator",
            "pcae.commands", "notification_certification", "handoff_verification",
        ):
            assert not any(forbidden in line for line in import_lines)


# ═══════════════════════════════════════════════════════════════════════
# Objective 6: AI boundary
# ═══════════════════════════════════════════════════════════════════════

class TestAiBoundaryVerification:
    def test_no_deepseek_glm_qwen_claude_backed_skill_registered(self):
        registry = build_default_registry()
        skill_ids = {s.manifest.skill_id for s in registry.list_skills()}
        for forbidden in ("deepseek", "glm", "qwen", "claude", "gpt", "codex"):
            assert not any(forbidden in skill_id.lower() for skill_id in skill_ids)

    def test_no_skill_declares_model_produced_true(self):
        registry = build_default_registry()
        for manifest in registry.list_manifests():
            assert manifest.model_produced is False

    def test_no_skill_declares_probabilistic_or_human_asserted_determinism(self):
        from pcae.core.evidence import EvidenceDeterminism
        registry = build_default_registry()
        for manifest in registry.list_manifests():
            assert manifest.determinism == EvidenceDeterminism.DETERMINISTIC

    def test_no_evidence_item_produced_by_default_skills_is_model_produced(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        results = registry.invoke_all(_ctx(tmp_path))
        merged = registry.merge_evidence(results)
        for item in merged:
            assert item.determinism.value == "deterministic"

    def test_ai_review_capability_has_zero_registered_skills(self):
        from pcae.core.repository_skills import RepositorySkillCapability
        registry = build_default_registry()
        assert registry.filter_by_capability(RepositorySkillCapability.AI_REVIEW) == ()


# ═══════════════════════════════════════════════════════════════════════
# Objective 7: execution boundary
# ═══════════════════════════════════════════════════════════════════════

class TestExecutionBoundaryVerification:
    def test_module_source_contains_no_execution_primitives(self):
        import pcae.core.repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("subprocess", "os.system", "Popen(", "exec(", "eval("):
            assert forbidden not in source

    def test_registry_public_api_has_no_write_authority_methods(self):
        forbidden = {"commit", "push", "finalize", "notify", "authorize", "execute", "mutate"}
        public_methods = {
            name for name in dir(RepositorySkillRegistry)
            if not name.startswith("_") and callable(getattr(RepositorySkillRegistry, name))
        }
        assert not (public_methods & forbidden)

    def test_skill_manifests_all_declare_none_side_effect_policy(self):
        registry = build_default_registry()
        for manifest in registry.list_manifests():
            assert manifest.side_effect_policy == "none"

    def test_no_skill_class_defines_a_commit_or_push_method(self):
        forbidden = {"commit", "push", "finalize", "notify", "authorize_execution", "execute"}
        for cls in ALL_SKILL_CLASSES:
            public_methods = {name for name in dir(cls) if not name.startswith("_")}
            assert not (public_methods & forbidden)


# ═══════════════════════════════════════════════════════════════════════
# Objective 8: serialization / Decision Evaluation compatibility
# ═══════════════════════════════════════════════════════════════════════

class TestSerializationAndDecisionEvaluationCompatibility:
    def test_skill_evidence_survives_to_dict_from_dict_round_trip(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        results = registry.invoke_all(_ctx(tmp_path))
        merged = registry.merge_evidence(results)
        payload = merged.to_dict()
        restored = EvidenceCollection.from_dict(payload)
        assert {i.evidence_id for i in restored} == {i.evidence_id for i in merged}
        for item in merged:
            restored_item = restored.by_id(item.evidence_id)
            assert restored_item.observed_value == item.observed_value

    def test_skill_evidence_is_json_serializable(self, tmp_path):
        import json
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        merged = registry.merge_evidence(registry.invoke_all(_ctx(tmp_path)))
        serialized = json.dumps(merged.to_dict())
        assert isinstance(serialized, str)
        assert json.loads(serialized)["items"]

    def test_merged_skill_evidence_is_a_valid_decision_evaluation_context_input(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        merged = registry.merge_evidence(registry.invoke_all(_ctx(tmp_path)))
        context = EvaluationContext(
            evidence=merged, evaluation_id="115k-verification", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        result = evaluate(context)
        assert len(result.invariant_results) == 6
        for invariant_result in result.invariant_results:
            assert invariant_result.status is not None

    def test_merged_skill_evidence_resolves_all_six_invariants_no_not_applicable(self, tmp_path):
        """Unlike 115F's narrow RepositoryState adapter (which leaves
        push_state_consistency/metadata_consistency/
        canonical_promotion_eligibility permanently NOT_APPLICABLE, a
        documented limitation), the full 115D provider evidence a
        Repository Skill exposes verbatim is rich enough for every
        invariant to resolve PASS/FAIL rather than NOT_APPLICABLE --
        a genuine compatibility finding, not a change in behavior."""
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        merged = registry.merge_evidence(registry.invoke_all(_ctx(tmp_path)))
        context = EvaluationContext(
            evidence=merged, evaluation_id="115k-verification", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        result = evaluate(context)
        not_applicable = [
            r.invariant_id for r in result.invariant_results
            if r.status is InvariantStatus.NOT_APPLICABLE
        ]
        assert not_applicable == []

    def test_decision_evaluation_explanation_references_resolve_against_skill_evidence(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        merged = registry.merge_evidence(registry.invoke_all(_ctx(tmp_path)))
        context = EvaluationContext(
            evidence=merged, evaluation_id="115k-verification", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        result = evaluate(context)
        for ref in result.explanation_reference:
            assert merged.by_id(ref.evidence_id) is not None

    def test_evaluate_is_not_wired_from_repository_skills_module(self):
        """Objective 8 explicitly forbids integration: this module must
        never itself call decision_evaluation.evaluate -- only this
        *test* does, to prove compatibility without performing
        integration in source."""
        import pcae.core.repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "evaluate(" not in source
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        assert not any("decision_evaluation" in line for line in import_lines)
