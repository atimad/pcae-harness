"""Phase 115S: First Advisory Provider Integration (Current Acting Model).

Verifies ``CurrentActingModelAdvisoryProvider`` -- the first real
(non-mock) ``AdvisoryProvider`` -- conforms to 115R's abstraction,
answers exactly one bounded pilot question
("Is the repository state internally consistent?"), is stateless with
no retries/multi-turn, reuses the unmodified Normalizer and Evidence
Builder, and carries no lifecycle authority, execution capability, or
backend-specific dependency.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.core.advisory_repository_skills import (
    AdvisoryProvider,
    AdvisoryRequest,
    RepositoryConsistencyAdvisorySkill,
    normalize_advisory_response,
)
from pcae.core.current_acting_model_advisory_provider import (
    PILOT_QUESTION,
    CurrentActingModelAdvisoryProvider,
    build_repository_consistency_skill_with_current_model,
)
from pcae.core.evidence import EvidenceConfidence, EvidenceDeterminism, EvidenceFreshness
from pcae.core.paths import HarnessPath
from pcae.core.repository_skills import RepositorySkillContext, RepositorySkillStatus


def _success_content(findings=("finding one", "finding two"), confidence=0.85, references=("PROJECT_STATUS.md",), limitations="Reviewed committed state only."):
    return json.dumps({
        "findings": list(findings),
        "confidence_signal": confidence,
        "references": list(references),
        "limitations": limitations,
    })


def _request() -> AdvisoryRequest:
    return AdvisoryRequest(bounded_context="ctx", question="repository_consistency_review", response_schema_hint="h")


# ═══════════════════════════════════════════════════════════════════════
# Objective 1: conforms to AdvisoryProvider
# ═══════════════════════════════════════════════════════════════════════

class TestConformsToAdvisoryProvider:
    def test_is_an_advisory_provider(self):
        assert isinstance(CurrentActingModelAdvisoryProvider("x"), AdvisoryProvider)

    def test_declares_backend_kind_and_determinism(self):
        provider = CurrentActingModelAdvisoryProvider("x")
        assert provider.backend_kind == "current_acting_model"
        assert provider.determinism == EvidenceDeterminism.PROBABILISTIC
        assert provider.provider_id == "current_acting_model_advisory_provider"

    def test_rejects_empty_raw_content_when_succeeded_true(self):
        with pytest.raises(ValueError, match="raw_content must be non-empty"):
            CurrentActingModelAdvisoryProvider("", succeeded=True)

    def test_allows_empty_raw_content_when_succeeded_false(self):
        provider = CurrentActingModelAdvisoryProvider("", succeeded=False)
        response = provider.invoke(_request())
        assert response.succeeded is False


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 / constraints: provider boundary, one request/response
# ═══════════════════════════════════════════════════════════════════════

class TestProviderBoundaryAndSingleUse:
    def test_invoke_returns_raw_advisory_response_only(self):
        from pcae.core.advisory_repository_skills import RawAdvisoryResponse
        provider = CurrentActingModelAdvisoryProvider(_success_content())
        response = provider.invoke(_request())
        assert isinstance(response, RawAdvisoryResponse)
        assert type(response) is RawAdvisoryResponse

    def test_invoke_return_type_is_never_evidence(self):
        from pcae.core.evidence import Evidence, EvidenceCollection
        provider = CurrentActingModelAdvisoryProvider(_success_content())
        response = provider.invoke(_request())
        assert not isinstance(response, Evidence)
        assert not isinstance(response, EvidenceCollection)

    def test_second_invoke_raises_no_retry(self):
        provider = CurrentActingModelAdvisoryProvider(_success_content())
        provider.invoke(_request())
        with pytest.raises(RuntimeError, match="stateless and single-use"):
            provider.invoke(_request())

    def test_one_request_one_response(self):
        provider = CurrentActingModelAdvisoryProvider(_success_content())
        response = provider.invoke(_request())
        assert response.provider_id == provider.provider_id
        assert response.succeeded is True

    def test_no_conversation_state_beyond_single_use_guard(self):
        provider = CurrentActingModelAdvisoryProvider(_success_content())
        public_state = {k: v for k, v in vars(provider).items() if not k.startswith("_")}
        assert public_state == {}


# ═══════════════════════════════════════════════════════════════════════
# Objective 3: normalization boundary -- reuses unmodified Normalizer
# ═══════════════════════════════════════════════════════════════════════

class TestNormalizationBoundary:
    def test_raw_response_normalizes_via_existing_normalizer(self):
        provider = CurrentActingModelAdvisoryProvider(_success_content())
        raw = provider.invoke(_request())
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "succeeded"
        assert len(normalized.findings) == 2

    def test_malformed_raw_content_normalizes_to_failed(self):
        provider = CurrentActingModelAdvisoryProvider("not json {{{")
        raw = provider.invoke(_request())
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "failed"

    def test_unauthorized_field_rejected_same_as_mock_provider(self):
        payload = {"findings": ["x"], "limitations": "l", "verdict": "accept"}
        provider = CurrentActingModelAdvisoryProvider(json.dumps(payload))
        raw = provider.invoke(_request())
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "failed"

    def test_no_bespoke_normalizer_logic_in_new_module(self):
        import pcae.core.current_acting_model_advisory_provider as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "def normalize" not in source
        assert "normalization_status" not in source


# ═══════════════════════════════════════════════════════════════════════
# Objective 4: evidence boundary -- reuses unmodified Evidence Builder
# ═══════════════════════════════════════════════════════════════════════

class TestEvidenceBoundary:
    def test_evidence_is_probabilistic_and_model_produced(self, tmp_path):
        skill = build_repository_consistency_skill_with_current_model(_success_content())
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.SUCCESS
        for item in result.evidence:
            assert item.determinism == EvidenceDeterminism.PROBABILISTIC
            assert "current_acting_model_advisory_provider" in item.provenance.produced_from
            assert item.provenance.deterministic_origin is False

    def test_evidence_is_confidence_labelled(self, tmp_path):
        skill = build_repository_consistency_skill_with_current_model(_success_content(confidence=0.9))
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert all(item.confidence == EvidenceConfidence.HIGH for item in result.evidence)

    def test_evidence_is_limitations_labelled(self, tmp_path):
        skill = build_repository_consistency_skill_with_current_model(
            _success_content(limitations="specific limitation text"),
        )
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert all(item.limitations == "specific limitation text" for item in result.evidence)

    def test_evidence_no_bespoke_evidence_builder_logic_in_new_module(self):
        import pcae.core.current_acting_model_advisory_provider as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "def build_evidence" not in source

    def test_skill_manifest_still_declares_advisory_only(self):
        manifest = RepositoryConsistencyAdvisorySkill.manifest
        assert manifest.model_produced is True
        assert manifest.determinism == EvidenceDeterminism.PROBABILISTIC
        assert manifest.side_effect_policy == "none"


class TestNeverSoleAuthorityForAccept:
    def test_advisory_evidence_alone_cannot_satisfy_a_blocking_invariant(self, tmp_path):
        """Advisory evidence uses EvidenceCategory.AI_REVIEW and carries
        no Evidence ID any of the six frozen invariant families (115E)
        look up -- so it structurally cannot influence
        phase_identity_consistency, push_state_consistency,
        metadata_consistency, report_completeness,
        runtime_execution_unavailable, or canonical_promotion_eligibility
        on its own, regardless of confidence."""
        from pcae.core.decision_evaluation import EvaluationContext, evaluate
        from pcae.core.evidence import EvidenceCollection

        skill = build_repository_consistency_skill_with_current_model(_success_content(confidence=1.0))
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        context = EvaluationContext(
            evidence=result.evidence, evaluation_id="e", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        evaluation = evaluate(context)
        assert evaluation.blocking_failures == ()
        assert evaluation.summary.startswith("6 invariants evaluated: 0 pass")
        assert isinstance(result.evidence, EvidenceCollection)


# ═══════════════════════════════════════════════════════════════════════
# Objective 6: failure behavior
# ═══════════════════════════════════════════════════════════════════════

class TestFailureBehavior:
    def test_unavailable_advisory_yields_unknown_evidence(self, tmp_path):
        skill = build_repository_consistency_skill_with_current_model("", succeeded=False)
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.SUCCESS
        item = result.evidence.by_id("E-advisory-repo-consistency-001")
        assert item.freshness == EvidenceFreshness.UNKNOWN
        assert item.confidence == EvidenceConfidence.UNKNOWN

    def test_malformed_advisory_response_yields_unknown_evidence(self, tmp_path):
        skill = build_repository_consistency_skill_with_current_model("not json")
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.SUCCESS
        item = result.evidence.by_id("E-advisory-repo-consistency-001")
        assert item.freshness == EvidenceFreshness.UNKNOWN

    def test_never_silent_success_on_malformed_response(self, tmp_path):
        skill = build_repository_consistency_skill_with_current_model("{}")
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        for item in result.evidence:
            assert item.confidence != EvidenceConfidence.HIGH
            assert item.confidence != EvidenceConfidence.MEDIUM

    def test_reused_provider_instance_raises_never_silently_retries(self, tmp_path):
        provider = CurrentActingModelAdvisoryProvider(_success_content())
        context = RepositorySkillContext(root=HarnessPath(tmp_path), strict=True)
        skill = RepositoryConsistencyAdvisorySkill(provider)
        skill.invoke(context)
        with pytest.raises(RuntimeError, match="stateless and single-use"):
            skill.invoke(context)

    def test_provider_exception_becomes_explicit_skill_failure_not_silent(self, tmp_path):
        provider = CurrentActingModelAdvisoryProvider(_success_content())
        provider.invoke(_request())  # exhaust it
        skill = RepositoryConsistencyAdvisorySkill(provider)
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.FAILED
        assert result.failure_reason
        assert len(result.evidence) == 0


# ═══════════════════════════════════════════════════════════════════════
# Safety / no execution / no mutation / no lifecycle authority
# ═══════════════════════════════════════════════════════════════════════

class TestSafetyAndIsolation:
    def test_never_mutates_repository(self, tmp_path):
        import subprocess
        (tmp_path / "README.md").write_text("hello\n")
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
        before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if ".git" not in p.parts)
        skill = build_repository_consistency_skill_with_current_model(_success_content())
        skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if ".git" not in p.parts)
        assert before == after

    def test_no_network_or_execution_primitives_in_code(self):
        import re
        import pcae.core.current_acting_model_advisory_provider as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        code = re.sub(r'""".*?"""', "", source, flags=re.DOTALL)
        for forbidden in (
            "socket.", "urllib", "requests.", "http.client", "httpx",
            "subprocess", "os.system", "Popen(", "exec(", "eval(",
            "random.", "uuid.uuid4",
        ):
            assert forbidden not in code, forbidden

    def test_no_network_module_imported(self):
        import pcae.core.current_acting_model_advisory_provider as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in ("socket", "urllib", "requests", "httpx", "http.client", "subprocess"):
            assert not any(forbidden in line for line in import_lines)

    def test_no_backend_specific_dependency(self):
        import ast
        import pcae.core.current_acting_model_advisory_provider as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    names.add(alias.name)
            elif isinstance(node, (ast.Name, ast.Attribute)):
                names.add(getattr(node, "id", getattr(node, "attr", "")))
            elif isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                names.add(node.name)
        joined = " ".join(names).lower()
        for forbidden in ("deepseek", "claude", "openai", "glm", "qwen", "codex", "mcp", "anthropic"):
            assert forbidden not in joined, forbidden

    @pytest.mark.parametrize("module_path", [
        "pcae.core.decision_evaluation",
        "pcae.core.repository_transition_validator",
        "pcae.core.repository_transition_integration",
        "pcae.core.repository_skills",
        "pcae.core.repository_skills_integration",
        "pcae.commands.phase",
        "pcae.commands.task",
        "pcae.commands.push",
        "pcae.core.notification_certification",
        "pcae.core.handoff_verification",
        "pcae.core.post_push_canonicalization",
        "pcae.commands.runtime_inspect",
        "pcae.core.advisory_repository_skills",
    ])
    def test_module_never_references_current_acting_model_provider(self, module_path):
        import importlib
        module = importlib.import_module(module_path)
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "current_acting_model_advisory_provider" not in source

    def test_no_lifecycle_or_validator_import_in_new_module(self):
        import pcae.core.current_acting_model_advisory_provider as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in (
            "pcae.commands", "notification_certification", "handoff_verification",
            "post_push_canonicalization", "repository_transition_validator",
            "repository_transition_integration", "decision_evaluation",
        ):
            assert not any(forbidden in line for line in import_lines)

    def test_default_registry_unaffected(self):
        from pcae.core.repository_skills import build_default_registry
        registry = build_default_registry()
        skill_ids = {s.manifest.skill_id for s in registry.list_skills()}
        assert "repository_consistency_advisory_skill" not in skill_ids
        assert len(registry.list_skills()) == 4

    def test_execution_availability_still_unavailable_for_real_repo(self):
        from pcae.core.repository_skills_integration import collect_evidence_via_repository_skills
        repo_root = HarnessPath(Path(__file__).resolve().parents[1])
        evidence = collect_evidence_via_repository_skills(repo_root)
        assert evidence.by_id("E-runtime-002").observed_value == "unavailable"


# ═══════════════════════════════════════════════════════════════════════
# Pilot scope: exactly one bounded question
# ═══════════════════════════════════════════════════════════════════════

class TestPilotScope:
    def test_pilot_question_constant_defined(self):
        assert PILOT_QUESTION == "Is the repository state internally consistent?"

    def test_skill_objective_is_repository_consistency_only(self):
        assert RepositoryConsistencyAdvisorySkill.objective == "repository_consistency_review"

    def test_helper_does_not_expose_arbitrary_question_parameter(self):
        import inspect
        sig = inspect.signature(build_repository_consistency_skill_with_current_model)
        assert "question" not in sig.parameters
        assert "objective" not in sig.parameters

    def test_end_to_end_pilot_pipeline(self, tmp_path):
        skill = build_repository_consistency_skill_with_current_model(_success_content())
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.SUCCESS
        assert len(result.evidence) == 2
