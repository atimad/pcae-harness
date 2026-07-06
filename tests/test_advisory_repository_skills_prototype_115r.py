"""Phase 115R: Advisory Repository Skills Prototype.

Implements and verifies the framework 115P designed and 115Q froze as
contract, using only a deterministic ``MockAdvisoryProvider``. No real
model backend is implemented or invoked anywhere in this suite.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.core.evidence import (
    EvidenceCategory,
    EvidenceCollection,
    EvidenceConfidence,
    EvidenceDeterminism,
    EvidenceFreshness,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_skills import RepositorySkillContext, RepositorySkillStatus
from pcae.core.advisory_repository_skills import (
    DEFAULT_ADVISORY_CONSTRAINTS,
    AdvisoryProvider,
    AdvisoryRequest,
    MockAdvisoryProvider,
    NormalizedAdvisoryResponse,
    NORMALIZATION_STATUSES,
    RawAdvisoryResponse,
    RepositoryConsistencyAdvisorySkill,
    build_advisory_request,
    build_evidence_from_normalized,
    normalize_advisory_response,
)


def _success_raw(findings=("finding one", "finding two"), confidence=0.8, references=("f.py",), limitations="l", provider_id="mock_advisory_provider"):
    return RawAdvisoryResponse(
        raw_content=json.dumps({
            "findings": list(findings),
            "confidence_signal": confidence,
            "references": list(references),
            "limitations": limitations,
        }),
        provider_id=provider_id,
        succeeded=True,
    )


# ═══════════════════════════════════════════════════════════════════════
# AdvisoryRequest
# ═══════════════════════════════════════════════════════════════════════

class TestAdvisoryRequest:
    def test_constructs_with_all_frozen_fields(self):
        request = AdvisoryRequest(
            bounded_context="ctx", question="q", response_schema_hint="hint", timeout_seconds=5.0,
        )
        assert request.bounded_context == "ctx"
        assert request.question == "q"
        assert request.response_schema_hint == "hint"
        assert request.timeout_seconds == 5.0

    def test_default_timeout(self):
        request = AdvisoryRequest(bounded_context="ctx", question="q", response_schema_hint="hint")
        assert request.timeout_seconds == 10.0

    def test_rejects_empty_bounded_context(self):
        with pytest.raises(ValueError, match="bounded_context"):
            AdvisoryRequest(bounded_context="", question="q", response_schema_hint="h")

    def test_rejects_empty_question(self):
        with pytest.raises(ValueError, match="question"):
            AdvisoryRequest(bounded_context="ctx", question="", response_schema_hint="h")

    def test_rejects_non_positive_timeout(self):
        with pytest.raises(ValueError, match="timeout_seconds"):
            AdvisoryRequest(bounded_context="ctx", question="q", response_schema_hint="h", timeout_seconds=0)

    def test_is_frozen(self):
        request = AdvisoryRequest(bounded_context="ctx", question="q", response_schema_hint="h")
        with pytest.raises(Exception):
            request.question = "other"  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════════
# Prompt Builder
# ═══════════════════════════════════════════════════════════════════════

class TestPromptBuilder:
    def test_builds_advisory_request(self, tmp_path):
        request = build_advisory_request(
            HarnessPath(tmp_path), evidence_categories=(EvidenceCategory.AI_REVIEW,),
            objective="repository_consistency_review",
        )
        assert isinstance(request, AdvisoryRequest)
        assert request.question == "repository_consistency_review"

    def test_bounded_context_includes_requested_categories(self, tmp_path):
        request = build_advisory_request(
            HarnessPath(tmp_path), evidence_categories=(EvidenceCategory.AI_REVIEW,),
            objective="o",
        )
        assert "ai_review" in request.bounded_context

    def test_rejects_empty_objective(self, tmp_path):
        with pytest.raises(ValueError, match="objective"):
            build_advisory_request(HarnessPath(tmp_path), evidence_categories=(EvidenceCategory.AI_REVIEW,), objective="")

    def test_rejects_empty_evidence_categories(self, tmp_path):
        with pytest.raises(ValueError, match="evidence_categories"):
            build_advisory_request(HarnessPath(tmp_path), evidence_categories=(), objective="o")

    def test_default_constraints_applied(self, tmp_path):
        request = build_advisory_request(
            HarnessPath(tmp_path), evidence_categories=(EvidenceCategory.AI_REVIEW,), objective="o",
        )
        for constraint in DEFAULT_ADVISORY_CONSTRAINTS:
            assert constraint in request.bounded_context

    def test_prompt_builder_signature_has_no_provider_parameter(self):
        import inspect
        sig = inspect.signature(build_advisory_request)
        assert "provider" not in sig.parameters

    def test_deterministic_given_same_inputs(self, tmp_path):
        r1 = build_advisory_request(HarnessPath(tmp_path), evidence_categories=(EvidenceCategory.AI_REVIEW,), objective="o")
        r2 = build_advisory_request(HarnessPath(tmp_path), evidence_categories=(EvidenceCategory.AI_REVIEW,), objective="o")
        assert r1 == r2


# ═══════════════════════════════════════════════════════════════════════
# MockAdvisoryProvider
# ═══════════════════════════════════════════════════════════════════════

class TestMockAdvisoryProvider:
    def test_is_an_advisory_provider(self):
        assert isinstance(MockAdvisoryProvider(), AdvisoryProvider)

    def test_declares_deterministic_backend_kind(self):
        provider = MockAdvisoryProvider()
        assert provider.backend_kind == "deterministic_mock"
        assert provider.determinism == EvidenceDeterminism.DETERMINISTIC

    def test_returns_canned_response_for_matching_question(self):
        raw = _success_raw()
        provider = MockAdvisoryProvider({"q1": raw})
        request = AdvisoryRequest(bounded_context="ctx", question="q1", response_schema_hint="h")
        assert provider.invoke(request) is raw

    def test_returns_default_response_for_unmatched_question(self):
        provider = MockAdvisoryProvider({})
        request = AdvisoryRequest(bounded_context="ctx", question="unmatched", response_schema_hint="h")
        response = provider.invoke(request)
        assert isinstance(response, RawAdvisoryResponse)
        assert response.succeeded is True

    def test_custom_default_response_used(self):
        custom_default = _success_raw(findings=("custom default",))
        provider = MockAdvisoryProvider({}, default_response=custom_default)
        request = AdvisoryRequest(bounded_context="ctx", question="anything", response_schema_hint="h")
        assert provider.invoke(request) is custom_default

    def test_repeatable_across_many_calls(self):
        raw = _success_raw()
        provider = MockAdvisoryProvider({"q1": raw})
        request = AdvisoryRequest(bounded_context="ctx", question="q1", response_schema_hint="h")
        results = [provider.invoke(request) for _ in range(10)]
        assert all(r is raw for r in results)

    def test_supports_deterministic_failure_scenario(self):
        failure = RawAdvisoryResponse(raw_content="", provider_id="mock_advisory_provider", succeeded=False)
        provider = MockAdvisoryProvider({"q1": failure})
        request = AdvisoryRequest(bounded_context="ctx", question="q1", response_schema_hint="h")
        response = provider.invoke(request)
        assert response.succeeded is False

    def test_no_network_or_execution_primitives_in_code(self):
        import re
        import pcae.core.advisory_repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        code = re.sub(r'""".*?"""', "", source, flags=re.DOTALL)
        for forbidden in (
            "socket.", "urllib", "requests.", "http.client", "httpx",
            "subprocess", "os.system", "Popen(", "exec(", "eval(",
            "random.", "uuid.uuid4",
        ):
            assert forbidden not in code, forbidden

    def test_no_forbidden_backend_names_in_imports_or_identifiers(self):
        import ast
        import pcae.core.advisory_repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    names.add(alias.name)
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                names.add(node.name)
        joined = " ".join(names).lower()
        for forbidden in ("deepseek", "claude", "openai", "glm", "qwen", "codex", "mcp"):
            assert forbidden not in joined, forbidden


# ═══════════════════════════════════════════════════════════════════════
# Response Normalizer
# ═══════════════════════════════════════════════════════════════════════

class TestResponseNormalizer:
    def test_succeeded_response_normalizes_fully(self):
        normalized = normalize_advisory_response(_success_raw())
        assert normalized.normalization_status == "succeeded"
        assert len(normalized.findings) == 2

    def test_provider_failure_normalizes_to_failed(self):
        raw = RawAdvisoryResponse(raw_content="", provider_id="p", succeeded=False)
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "failed"
        assert normalized.findings == ()

    def test_unparseable_json_normalizes_to_failed(self):
        raw = RawAdvisoryResponse(raw_content="not json {{{", provider_id="p", succeeded=True)
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "failed"

    def test_non_object_json_normalizes_to_failed(self):
        raw = RawAdvisoryResponse(raw_content=json.dumps([1, 2, 3]), provider_id="p", succeeded=True)
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "failed"

    def test_missing_findings_normalizes_to_failed(self):
        raw = RawAdvisoryResponse(raw_content=json.dumps({"limitations": "l"}), provider_id="p", succeeded=True)
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "failed"

    def test_empty_findings_list_normalizes_to_failed(self):
        raw = RawAdvisoryResponse(raw_content=json.dumps({"findings": []}), provider_id="p", succeeded=True)
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "failed"

    @pytest.mark.parametrize("field", ["verdict", "commit", "push", "authorized", "execute", "finalize"])
    def test_unauthorized_field_rejected(self, field):
        payload = {"findings": ["x"], "limitations": "l", field: True}
        raw = RawAdvisoryResponse(raw_content=json.dumps(payload), provider_id="p", succeeded=True)
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "failed"

    def test_partial_findings_drops_invalid_entries(self):
        payload = {"findings": ["valid one", 123, None, {"finding": "valid two"}, {"bad": "shape"}], "limitations": "l"}
        raw = RawAdvisoryResponse(raw_content=json.dumps(payload), provider_id="p", succeeded=True)
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "partial"
        assert normalized.findings == ("valid one", "valid two")

    def test_missing_limitations_defaults_to_honest_placeholder(self):
        payload = {"findings": ["x"]}
        raw = RawAdvisoryResponse(raw_content=json.dumps(payload), provider_id="p", succeeded=True)
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "succeeded"
        assert normalized.limitations

    def test_non_numeric_confidence_signal_dropped(self):
        payload = {"findings": ["x"], "limitations": "l", "confidence_signal": "high"}
        raw = RawAdvisoryResponse(raw_content=json.dumps(payload), provider_id="p", succeeded=True)
        normalized = normalize_advisory_response(raw)
        assert normalized.confidence_signal is None

    def test_normalizer_output_is_normalized_advisory_response(self):
        normalized = normalize_advisory_response(_success_raw())
        assert isinstance(normalized, NormalizedAdvisoryResponse)
        assert normalized.normalization_status in NORMALIZATION_STATUSES

    def test_normalized_response_rejects_invalid_status(self):
        with pytest.raises(ValueError, match="normalization_status"):
            NormalizedAdvisoryResponse(
                findings=("x",), confidence_signal=None, references=(), limitations="l",
                normalization_status="bogus",
            )

    def test_normalized_response_requires_findings_unless_failed(self):
        with pytest.raises(ValueError, match="finding"):
            NormalizedAdvisoryResponse(
                findings=(), confidence_signal=None, references=(), limitations="l",
                normalization_status="succeeded",
            )

    def test_normalized_response_requires_non_empty_limitations(self):
        with pytest.raises(ValueError, match="limitations"):
            NormalizedAdvisoryResponse(
                findings=("x",), confidence_signal=None, references=(), limitations="",
                normalization_status="succeeded",
            )

    def test_failed_status_allows_empty_findings(self):
        normalized = NormalizedAdvisoryResponse(
            findings=(), confidence_signal=None, references=(), limitations="l",
            normalization_status="failed",
        )
        assert normalized.findings == ()


# ═══════════════════════════════════════════════════════════════════════
# Evidence Builder
# ═══════════════════════════════════════════════════════════════════════

class TestEvidenceBuilder:
    def _normalized_success(self, **overrides):
        base = dict(
            findings=("finding one", "finding two"), confidence_signal=0.8,
            references=("f.py",), limitations="l", normalization_status="succeeded",
        )
        base.update(overrides)
        return NormalizedAdvisoryResponse(**base)

    def test_builds_one_evidence_item_per_finding(self):
        collection = build_evidence_from_normalized(
            self._normalized_success(), provider_id="mock_advisory_provider",
            producer="Test Skill", category=EvidenceCategory.AI_REVIEW,
            scope="repository_consistency_review", evidence_id_prefix="E-test",
        )
        assert len(collection) == 2

    def test_every_item_is_probabilistic(self):
        collection = build_evidence_from_normalized(
            self._normalized_success(), provider_id="p", producer="Skill",
            category=EvidenceCategory.AI_REVIEW, scope="s", evidence_id_prefix="E-t",
        )
        for item in collection:
            assert item.determinism == EvidenceDeterminism.PROBABILISTIC

    def test_confidence_labelled_from_signal(self):
        collection = build_evidence_from_normalized(
            self._normalized_success(confidence_signal=0.9), provider_id="p", producer="Skill",
            category=EvidenceCategory.AI_REVIEW, scope="s", evidence_id_prefix="E-t",
        )
        assert all(item.confidence == EvidenceConfidence.HIGH for item in collection)

    def test_low_confidence_when_signal_missing(self):
        collection = build_evidence_from_normalized(
            self._normalized_success(confidence_signal=None), provider_id="p", producer="Skill",
            category=EvidenceCategory.AI_REVIEW, scope="s", evidence_id_prefix="E-t",
        )
        assert all(item.confidence == EvidenceConfidence.LOW for item in collection)

    def test_limitations_preserved_on_every_item(self):
        collection = build_evidence_from_normalized(
            self._normalized_success(limitations="specific limitation"), provider_id="p", producer="Skill",
            category=EvidenceCategory.AI_REVIEW, scope="s", evidence_id_prefix="E-t",
        )
        assert all(item.limitations == "specific limitation" for item in collection)

    def test_provenance_preserved_and_marks_model_produced_via_provider_id(self):
        collection = build_evidence_from_normalized(
            self._normalized_success(), provider_id="mock_advisory_provider", producer="Skill",
            category=EvidenceCategory.AI_REVIEW, scope="s", evidence_id_prefix="E-t",
        )
        for item in collection:
            assert "mock_advisory_provider" in item.provenance.produced_from
            assert item.provenance.deterministic_origin is False

    def test_references_carried_through(self):
        collection = build_evidence_from_normalized(
            self._normalized_success(references=("a.py", "b.py")), provider_id="p", producer="Skill",
            category=EvidenceCategory.AI_REVIEW, scope="s", evidence_id_prefix="E-t",
        )
        for item in collection:
            assert item.references == ("a.py", "b.py")

    def test_failed_normalization_produces_single_unknown_evidence_item(self):
        failed = NormalizedAdvisoryResponse(
            findings=(), confidence_signal=None, references=(), limitations="l",
            normalization_status="failed",
        )
        collection = build_evidence_from_normalized(
            failed, provider_id="p", producer="Skill",
            category=EvidenceCategory.AI_REVIEW, scope="s", evidence_id_prefix="E-t",
        )
        assert len(collection) == 1
        item = collection.by_id("E-t-001")
        assert item.freshness == EvidenceFreshness.UNKNOWN
        assert item.confidence == EvidenceConfidence.UNKNOWN

    def test_output_is_evidence_collection(self):
        collection = build_evidence_from_normalized(
            self._normalized_success(), provider_id="p", producer="Skill",
            category=EvidenceCategory.AI_REVIEW, scope="s", evidence_id_prefix="E-t",
        )
        assert isinstance(collection, EvidenceCollection)


# ═══════════════════════════════════════════════════════════════════════
# End-to-end advisory pipeline / Repository Skill integration
# ═══════════════════════════════════════════════════════════════════════

class TestEndToEndAdvisoryPipeline:
    def test_successful_pipeline_produces_evidence(self, tmp_path):
        provider = MockAdvisoryProvider({"repository_consistency_review": _success_raw()})
        skill = RepositoryConsistencyAdvisorySkill(provider)
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.SUCCESS
        assert len(result.evidence) == 2
        assert result.failure_reason is None

    def test_default_provider_is_mock_advisory_provider(self, tmp_path):
        skill = RepositoryConsistencyAdvisorySkill()
        assert isinstance(skill._provider, MockAdvisoryProvider)
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.SUCCESS

    def test_pipeline_is_deterministic_across_repeated_invocations(self, tmp_path):
        provider = MockAdvisoryProvider({"repository_consistency_review": _success_raw()})
        skill = RepositoryConsistencyAdvisorySkill(provider)
        context = RepositorySkillContext(root=HarnessPath(tmp_path))
        first = skill.invoke(context)
        second = skill.invoke(context)
        assert [i.observed_value for i in first.evidence] == [i.observed_value for i in second.evidence]
        assert [i.confidence for i in first.evidence] == [i.confidence for i in second.evidence]

    def test_skill_manifest_declares_advisory_shape(self):
        manifest = RepositoryConsistencyAdvisorySkill.manifest
        assert manifest.determinism == EvidenceDeterminism.PROBABILISTIC
        assert manifest.model_produced is True
        assert manifest.side_effect_policy == "none"

    def test_skill_never_mutates_repository(self, tmp_path):
        import subprocess
        (tmp_path / "README.md").write_text("hello\n")
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
        before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if ".git" not in p.parts)
        skill = RepositoryConsistencyAdvisorySkill(MockAdvisoryProvider({"repository_consistency_review": _success_raw()}))
        skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if ".git" not in p.parts)
        assert before == after


class TestDeterministicFailureHandling:
    def test_provider_level_failure_yields_unknown_evidence(self, tmp_path):
        failure = RawAdvisoryResponse(raw_content="", provider_id="mock_advisory_provider", succeeded=False)
        provider = MockAdvisoryProvider({"repository_consistency_review": failure})
        skill = RepositoryConsistencyAdvisorySkill(provider)
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.SUCCESS
        assert len(result.evidence) == 1
        item = result.evidence.by_id("E-advisory-repo-consistency-001")
        assert item.freshness == EvidenceFreshness.UNKNOWN

    def test_malformed_response_yields_unknown_evidence(self, tmp_path):
        malformed = RawAdvisoryResponse(raw_content="not json", provider_id="mock_advisory_provider", succeeded=True)
        provider = MockAdvisoryProvider({"repository_consistency_review": malformed})
        skill = RepositoryConsistencyAdvisorySkill(provider)
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.SUCCESS
        item = result.evidence.by_id("E-advisory-repo-consistency-001")
        assert item.freshness == EvidenceFreshness.UNKNOWN
        assert item.confidence == EvidenceConfidence.UNKNOWN

    def test_never_silent_success_failed_normalization_is_never_pass_confidence(self, tmp_path):
        malformed = RawAdvisoryResponse(raw_content="{}", provider_id="mock_advisory_provider", succeeded=True)
        provider = MockAdvisoryProvider({"repository_consistency_review": malformed})
        skill = RepositoryConsistencyAdvisorySkill(provider)
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        for item in result.evidence:
            assert item.confidence != EvidenceConfidence.HIGH

    def test_explicit_skill_failure_when_provider_raises(self, tmp_path):
        class RaisingProvider(AdvisoryProvider):
            backend_kind = "deterministic_mock"
            determinism = EvidenceDeterminism.DETERMINISTIC
            provider_id = "raising_provider"

            def invoke(self, request):
                raise RuntimeError("synthetic failure")

        skill = RepositoryConsistencyAdvisorySkill(RaisingProvider())
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.FAILED
        assert result.failure_reason
        assert len(result.evidence) == 0

    def test_strict_context_reraises_provider_exception(self, tmp_path):
        class RaisingProvider(AdvisoryProvider):
            backend_kind = "deterministic_mock"
            determinism = EvidenceDeterminism.DETERMINISTIC
            provider_id = "raising_provider"

            def invoke(self, request):
                raise RuntimeError("synthetic failure")

        skill = RepositoryConsistencyAdvisorySkill(RaisingProvider())
        with pytest.raises(RuntimeError, match="synthetic failure"):
            skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path), strict=True))


# ═══════════════════════════════════════════════════════════════════════
# No model invocation / no network / no execution / no lifecycle wiring
# ═══════════════════════════════════════════════════════════════════════

class TestNoRealModelOrLifecycleIntegration:
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
    ])
    def test_module_never_references_advisory_repository_skills(self, module_path):
        import importlib
        module = importlib.import_module(module_path)
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "advisory_repository_skills" not in source

    def test_advisory_module_does_not_import_lifecycle_or_decision_or_validator(self):
        import pcae.core.advisory_repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in (
            "decision_evaluation", "repository_transition_validator",
            "repository_transition_integration", "repository_skills_integration",
            "pcae.commands",
        ):
            assert not any(forbidden in line for line in import_lines)

    def test_default_registry_unaffected_by_advisory_module(self):
        from pcae.core.repository_skills import build_default_registry
        registry = build_default_registry()
        skill_ids = {s.manifest.skill_id for s in registry.list_skills()}
        assert "repository_consistency_advisory_skill" not in skill_ids
        assert len(registry.list_skills()) == 4

    def test_no_network_module_imported(self):
        import pcae.core.advisory_repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in ("socket", "urllib", "requests", "httpx", "http.client"):
            assert not any(forbidden in line for line in import_lines)

    def test_no_subprocess_module_imported(self):
        import pcae.core.advisory_repository_skills as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        assert not any("subprocess" in line for line in import_lines)

    def test_execution_availability_still_unavailable_for_real_repo(self):
        from pcae.core.repository_skills_integration import collect_evidence_via_repository_skills
        repo_root = HarnessPath(Path(__file__).resolve().parents[1])
        evidence = collect_evidence_via_repository_skills(repo_root)
        assert evidence.by_id("E-runtime-002").observed_value == "unavailable"
