"""Phase 115T: Advisory Provider Verification & Compatibility.

Verification-only phase re-proving that 115S's first real Advisory
Provider integration (``CurrentActingModelAdvisoryProvider``) is
safely contained, behavior-compatible, failure-isolated, and portable
to future providers. No new provider is implemented, no DeepSeek/GLM/
Codex-specific integration is added, no provider selection or model
configuration exists, and no lifecycle command, Decision Evaluation,
Repository Transition Validator, or Repository Skills runtime is
modified by this phase -- this module only reads and asserts against
115R's and 115S's existing, unmodified implementation.
"""
from __future__ import annotations

import ast
import dataclasses
import json
from pathlib import Path

import pytest

from pcae.core.advisory_repository_skills import (
    AdvisoryProvider,
    AdvisoryRequest,
    MockAdvisoryProvider,
    NormalizedAdvisoryResponse,
    RawAdvisoryResponse,
    RepositoryConsistencyAdvisorySkill,
    build_evidence_from_normalized,
    normalize_advisory_response,
)
from pcae.core.current_acting_model_advisory_provider import (
    PILOT_QUESTION,
    CurrentActingModelAdvisoryProvider,
    build_repository_consistency_skill_with_current_model,
)
from pcae.core.decision_evaluation import EvaluationContext, InvariantStatus, evaluate
from pcae.core.evidence import (
    Evidence,
    EvidenceCategory,
    EvidenceCollection,
    EvidenceConfidence,
    EvidenceDeterminism,
    EvidenceFreshness,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_skills import RepositorySkillContext, RepositorySkillStatus
from pcae.core.repository_transition_validator import (
    ArtifactState,
    ExpectedTargetState,
    ProposedTransition,
    RepositoryState,
    TransitionKind,
    TransitionVerdict,
    validate_transition,
)

ADVISORY_MODULES = (
    "pcae.core.advisory_repository_skills",
    "pcae.core.current_acting_model_advisory_provider",
)


def _success_content(findings=("finding one", "finding two"), confidence=0.85, references=("f.py",), limitations="l"):
    return json.dumps({
        "findings": list(findings),
        "confidence_signal": confidence,
        "references": list(references),
        "limitations": limitations,
    })


def _request() -> AdvisoryRequest:
    return AdvisoryRequest(bounded_context="ctx", question="repository_consistency_review", response_schema_hint="h")


# ═══════════════════════════════════════════════════════════════════════
# Objective 1: behavioral containment
# ═══════════════════════════════════════════════════════════════════════

class TestBehavioralContainment:
    _FORBIDDEN_PUBLIC_METHODS = {
        "decide", "authorize", "commit", "push", "finalize", "notify",
        "mutate", "execute", "approve", "reject",
    }

    @pytest.mark.parametrize("cls", [
        CurrentActingModelAdvisoryProvider,
        RepositoryConsistencyAdvisorySkill,
    ])
    def test_no_forbidden_public_method_exists(self, cls):
        public_methods = {name for name in dir(cls) if not name.startswith("_")}
        assert not (public_methods & self._FORBIDDEN_PUBLIC_METHODS)

    def test_provider_result_carries_no_verdict_or_authorization_field(self):
        field_names = {f.name for f in dataclasses.fields(RawAdvisoryResponse)}
        assert not (field_names & {"verdict", "authorized", "committed", "pushed", "notified"})

    def test_advisory_skill_never_mutates_repository(self, tmp_path):
        import subprocess
        (tmp_path / "README.md").write_text("hello\n")
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
        before_log = subprocess.run(["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True).stdout
        before_files = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if ".git" not in p.parts)
        skill = build_repository_consistency_skill_with_current_model(_success_content())
        skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        after_log = subprocess.run(["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True).stdout
        after_files = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if ".git" not in p.parts)
        assert before_log == after_log
        assert before_files == after_files

    def test_advisory_module_never_imports_validator_and_cannot_bypass_it(self):
        for module_name in ADVISORY_MODULES:
            import importlib
            module = importlib.import_module(module_name)
            source = Path(module.__file__).read_text(encoding="utf-8")
            import_lines = [
                line for line in source.splitlines()
                if line.strip().startswith("from ") or line.strip().startswith("import ")
            ]
            for forbidden in ("repository_transition_validator", "TransitionVerdict", "validate_transition"):
                assert not any(forbidden in line for line in import_lines), forbidden

    def test_validator_module_never_references_advisory_modules(self):
        import pcae.core.repository_transition_validator as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "advisory_repository_skills" not in source
        assert "current_acting_model_advisory_provider" not in source

    def test_advisory_evidence_cannot_alone_reach_accept(self, tmp_path):
        """Advisory-only evidence, fed through Decision Evaluation
        alone, must never resolve any invariant to PASS -- confirming
        it structurally cannot be sole authority for Accept."""
        skill = build_repository_consistency_skill_with_current_model(_success_content(confidence=1.0))
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        context = EvaluationContext(
            evidence=result.evidence, evaluation_id="e", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        evaluation = evaluate(context)
        pass_count = sum(1 for r in evaluation.invariant_results if r.status is InvariantStatus.PASS)
        assert pass_count == 0

    def test_advisory_evidence_does_not_override_disagreeing_deterministic_evidence(self, tmp_path):
        """Mixing advisory evidence with deterministic evidence that
        would otherwise fail must still fail -- advisory evidence
        never overrides or masks a deterministic disagreement."""
        from pcae.core.repository_skills_integration import build_evaluation_context_from_evidence_providers

        deterministic_context = build_evaluation_context_from_evidence_providers(
            HarnessPath(tmp_path), evaluation_id="e", repository_snapshot_reference="HEAD",
            evaluation_timestamp="t",
        )
        deterministic_only = evaluate(deterministic_context)

        skill = build_repository_consistency_skill_with_current_model(_success_content(confidence=1.0))
        advisory_result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        combined_items = tuple(deterministic_context.evidence) + tuple(advisory_result.evidence)
        combined_context = EvaluationContext(
            evidence=EvidenceCollection(combined_items), evaluation_id="e",
            evaluation_timestamp="t", repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        combined = evaluate(combined_context)
        assert combined.blocking_failures == deterministic_only.blocking_failures


# ═══════════════════════════════════════════════════════════════════════
# Objective 2: pipeline boundaries
# ═══════════════════════════════════════════════════════════════════════

class TestPipelineBoundaries:
    def test_provider_invoke_returns_raw_advisory_response_only(self):
        provider = CurrentActingModelAdvisoryProvider(_success_content())
        response = provider.invoke(_request())
        assert type(response) is RawAdvisoryResponse

    def test_normalizer_returns_normalized_advisory_response_only(self):
        provider = CurrentActingModelAdvisoryProvider(_success_content())
        raw = provider.invoke(_request())
        normalized = normalize_advisory_response(raw)
        assert type(normalized) is NormalizedAdvisoryResponse

    def test_evidence_builder_returns_evidence_collection_only(self):
        normalized = normalize_advisory_response(RawAdvisoryResponse(
            raw_content=_success_content(), provider_id="p", succeeded=True,
        ))
        collection = build_evidence_from_normalized(
            normalized, provider_id="p", producer="Skill", category=EvidenceCategory.AI_REVIEW,
            scope="s", evidence_id_prefix="E-t",
        )
        assert type(collection) is EvidenceCollection
        for item in collection:
            assert type(item) is Evidence

    def test_decision_evaluation_only_accepts_evidence_collection(self):
        with pytest.raises((TypeError, ValueError)):
            EvaluationContext(
                evidence="not a collection", evaluation_id="e", evaluation_timestamp="t",
                repository_snapshot_reference="HEAD", evaluation_version="1.0",
            )

    def test_decision_evaluation_module_has_no_advisory_provider_dependency(self):
        import pcae.core.decision_evaluation as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in ("advisory_repository_skills", "current_acting_model_advisory_provider"):
            assert not any(forbidden in line for line in import_lines)

    def test_transition_validator_remains_sole_verdict_authority(self):
        state = RepositoryState(
            phase_id="113U",
            active_task_phase_id="113U",
            metadata_phase_id="113U",
            lifecycle_current_phase_id="113T",
            lifecycle_current_phase_completed=True,
            commits=("abc12345",),
            files_changed=3,
            test_results={"focused": "10/10 (passed)"},
            recommended_next_phase="113V — Repository Transition Validator Verification & Compatibility",
            report_completeness="complete",
            pushed_status="pushed",
            origin_main_head_count=0,
            notification_already_dispatched=False,
            notification_transport_enabled=True,
            artifact_state=ArtifactState.CERTIFIED,
            execution_availability="unavailable",
        )
        result = validate_transition(
            state, ProposedTransition(kind=TransitionKind.COMPLETE_PHASE, payload={}),
            ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U"),
        )
        assert result.verdict == TransitionVerdict.ACCEPT
        assert result.violations == ()


# ═══════════════════════════════════════════════════════════════════════
# Objective 3: failure isolation
# ═══════════════════════════════════════════════════════════════════════

class TestFailureIsolation:
    def _evidence_for_raw(self, raw: RawAdvisoryResponse) -> EvidenceCollection:
        normalized = normalize_advisory_response(raw)
        return build_evidence_from_normalized(
            normalized, provider_id=raw.provider_id, producer="Skill",
            category=EvidenceCategory.AI_REVIEW, scope="s", evidence_id_prefix="E-t",
        )

    def test_provider_unavailable(self):
        raw = RawAdvisoryResponse(raw_content="", provider_id="p", succeeded=False)
        collection = self._evidence_for_raw(raw)
        assert len(collection) == 1
        assert collection.by_id("E-t-001").freshness == EvidenceFreshness.UNKNOWN

    def test_malformed_response(self):
        raw = RawAdvisoryResponse(raw_content="not json {{{", provider_id="p", succeeded=True)
        collection = self._evidence_for_raw(raw)
        assert collection.by_id("E-t-001").freshness == EvidenceFreshness.UNKNOWN

    def test_missing_confidence_defaults_to_low_never_high(self):
        payload = {"findings": ["x"], "limitations": "l"}
        raw = RawAdvisoryResponse(raw_content=json.dumps(payload), provider_id="p", succeeded=True)
        collection = self._evidence_for_raw(raw)
        for item in collection:
            assert item.confidence == EvidenceConfidence.LOW

    def test_missing_limitations_never_empty(self):
        payload = {"findings": ["x"], "confidence_signal": 0.9}
        raw = RawAdvisoryResponse(raw_content=json.dumps(payload), provider_id="p", succeeded=True)
        collection = self._evidence_for_raw(raw)
        for item in collection:
            assert item.limitations

    def test_unexpected_advisory_content_extra_fields_ignored_not_crashed(self):
        payload = {
            "findings": ["x"], "limitations": "l", "confidence_signal": 0.5,
            "unexpected_extra_field": {"nested": "value"}, "another_surprise": [1, 2, 3],
        }
        raw = RawAdvisoryResponse(raw_content=json.dumps(payload), provider_id="p", succeeded=True)
        normalized = normalize_advisory_response(raw)
        assert normalized.normalization_status == "succeeded"

    def test_empty_findings_response(self):
        payload = {"findings": [], "limitations": "l"}
        raw = RawAdvisoryResponse(raw_content=json.dumps(payload), provider_id="p", succeeded=True)
        collection = self._evidence_for_raw(raw)
        assert collection.by_id("E-t-001").freshness == EvidenceFreshness.UNKNOWN

    def test_no_scenario_ever_produces_high_or_medium_confidence_from_failure(self):
        failure_scenarios = (
            RawAdvisoryResponse(raw_content="", provider_id="p", succeeded=False),
            RawAdvisoryResponse(raw_content="not json", provider_id="p", succeeded=True),
            RawAdvisoryResponse(raw_content=json.dumps({"findings": []}), provider_id="p", succeeded=True),
            RawAdvisoryResponse(raw_content=json.dumps({"findings": ["x"], "limitations": "l", "verdict": "accept"}), provider_id="p", succeeded=True),
        )
        for raw in failure_scenarios:
            collection = self._evidence_for_raw(raw)
            for item in collection:
                assert item.confidence in (EvidenceConfidence.UNKNOWN, EvidenceConfidence.LOW)

    def test_failure_never_raises_out_of_the_skill(self, tmp_path):
        """No lifecycle failure: a failed advisory scenario must
        complete the skill invocation without an uncaught exception."""
        skill = build_repository_consistency_skill_with_current_model("not json")
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.SUCCESS

    def test_failure_does_not_affect_deterministic_evidence_evaluation(self, tmp_path):
        from pcae.core.repository_skills_integration import build_evaluation_context_from_evidence_providers
        deterministic_context = build_evaluation_context_from_evidence_providers(
            HarnessPath(tmp_path), evaluation_id="e", repository_snapshot_reference="HEAD",
            evaluation_timestamp="t",
        )
        baseline = evaluate(deterministic_context)

        failed_advisory = self._evidence_for_raw(
            RawAdvisoryResponse(raw_content="not json", provider_id="p", succeeded=True),
        )
        combined_items = tuple(deterministic_context.evidence) + tuple(failed_advisory)
        combined_context = EvaluationContext(
            evidence=EvidenceCollection(combined_items), evaluation_id="e",
            evaluation_timestamp="t", repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        combined = evaluate(combined_context)
        assert combined.blocking_failures == baseline.blocking_failures
        assert combined.warnings == baseline.warnings


# ═══════════════════════════════════════════════════════════════════════
# Objective 4: nondeterminism containment
# ═══════════════════════════════════════════════════════════════════════

class TestNondeterminismContainment:
    _VARIED_RAW_CONTENTS = (
        _success_content(findings=("a",), confidence=0.95),
        _success_content(findings=("a", "b", "c"), confidence=0.1),
        _success_content(findings=("single finding",), confidence=0.5),
        json.dumps({"findings": ["x", 123, None, {"finding": "y"}], "limitations": "l"}),
        json.dumps({"findings": ["only one"], "confidence_signal": "not-a-number", "limitations": "l"}),
    )

    @pytest.mark.parametrize("raw_content", _VARIED_RAW_CONTENTS)
    def test_normalized_output_always_conforms_to_schema(self, raw_content):
        raw = RawAdvisoryResponse(raw_content=raw_content, provider_id="p", succeeded=True)
        normalized = normalize_advisory_response(raw)
        assert isinstance(normalized.findings, tuple)
        assert all(isinstance(f, str) for f in normalized.findings)
        assert normalized.confidence_signal is None or isinstance(normalized.confidence_signal, (int, float))
        assert isinstance(normalized.references, tuple)
        assert isinstance(normalized.limitations, str) and normalized.limitations
        assert normalized.normalization_status in ("succeeded", "partial", "failed")

    @pytest.mark.parametrize("raw_content", _VARIED_RAW_CONTENTS)
    def test_evidence_always_probabilistic_and_model_produced(self, raw_content, tmp_path):
        skill = build_repository_consistency_skill_with_current_model(raw_content)
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        for item in result.evidence:
            assert item.determinism == EvidenceDeterminism.PROBABILISTIC
            assert item.provenance.deterministic_origin is False
            assert "current_acting_model_advisory_provider" in item.provenance.produced_from

    @pytest.mark.parametrize("raw_content", _VARIED_RAW_CONTENTS)
    def test_confidence_limitations_provenance_always_present(self, raw_content, tmp_path):
        skill = build_repository_consistency_skill_with_current_model(raw_content)
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        for item in result.evidence:
            assert item.confidence is not None
            assert item.limitations
            assert item.provenance is not None

    @pytest.mark.parametrize("raw_content", _VARIED_RAW_CONTENTS)
    def test_advisory_evidence_never_alone_authorizes_accept_across_variation(self, raw_content, tmp_path):
        skill = build_repository_consistency_skill_with_current_model(raw_content)
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        context = EvaluationContext(
            evidence=result.evidence, evaluation_id="e", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        evaluation = evaluate(context)
        assert sum(1 for r in evaluation.invariant_results if r.status is InvariantStatus.PASS) == 0


# ═══════════════════════════════════════════════════════════════════════
# Objective 5: backend portability (test-only stand-ins, nothing implemented)
# ═══════════════════════════════════════════════════════════════════════

class _FakeFutureBackendProvider(AdvisoryProvider):
    """A test-local stand-in proving the pipeline is backend-agnostic.
    Not a real integration of any named backend -- exists only in this
    test file, never in ``src/``, and is deleted along with the test
    process. Demonstrates that any ``backend_kind`` conforms without
    touching the skill, Normalizer, or Evidence Builder."""

    determinism = EvidenceDeterminism.PROBABILISTIC

    def __init__(self, backend_kind: str, raw_content: str) -> None:
        self.backend_kind = backend_kind
        self.provider_id = f"fake_{backend_kind}_provider"
        self._raw_content = raw_content

    def invoke(self, request: AdvisoryRequest) -> RawAdvisoryResponse:
        return RawAdvisoryResponse(raw_content=self._raw_content, provider_id=self.provider_id, succeeded=True)


class TestBackendPortability:
    @pytest.mark.parametrize("backend_kind", [
        "current_acting_model", "deepseek", "glm_zai", "qwen", "codex", "local_slm",
    ])
    def test_same_skill_class_works_with_any_backend_kind(self, backend_kind, tmp_path):
        provider = _FakeFutureBackendProvider(backend_kind, _success_content())
        skill = RepositoryConsistencyAdvisorySkill(provider)
        result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        assert result.status == RepositorySkillStatus.SUCCESS
        assert len(result.evidence) == 2

    def test_decision_evaluation_unaware_of_backend_kind(self, tmp_path):
        for backend_kind in ("current_acting_model", "deepseek", "glm_zai"):
            provider = _FakeFutureBackendProvider(backend_kind, _success_content(confidence=1.0))
            skill = RepositoryConsistencyAdvisorySkill(provider)
            result = skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
            context = EvaluationContext(
                evidence=result.evidence, evaluation_id="e", evaluation_timestamp="t",
                repository_snapshot_reference="HEAD", evaluation_version="1.0",
            )
            evaluation = evaluate(context)
            assert sum(1 for r in evaluation.invariant_results if r.status is InvariantStatus.PASS) == 0

    def test_no_real_backend_provider_implemented_in_source(self):
        import re
        for module_name in ADVISORY_MODULES:
            import importlib
            module = importlib.import_module(module_name)
            source = Path(module.__file__).read_text(encoding="utf-8")
            code = re.sub(r'""".*?"""', "", source, flags=re.DOTALL).lower()
            for forbidden in ("deepseek", "glm", "qwen", "codex", "local_slm", "anthropic", "openai"):
                assert forbidden not in code, f"{module_name}: {forbidden}"

    def test_transition_validator_and_decision_evaluation_unmodified_by_portability(self):
        for module_name in (
            "pcae.core.decision_evaluation",
            "pcae.core.repository_transition_validator",
        ):
            import importlib
            module = importlib.import_module(module_name)
            source = Path(module.__file__).read_text(encoding="utf-8")
            assert "backend_kind" not in source


# ═══════════════════════════════════════════════════════════════════════
# Objective 6: pilot scope enforcement
# ═══════════════════════════════════════════════════════════════════════

class TestPilotScopeEnforcement:
    def test_only_one_advisory_question_supported(self):
        assert PILOT_QUESTION == "Is the repository state internally consistent?"
        assert RepositoryConsistencyAdvisorySkill.objective == "repository_consistency_review"

    def test_no_other_review_scope_present_in_advisory_modules(self):
        for module_name in ADVISORY_MODULES:
            import importlib
            module = importlib.import_module(module_name)
            source = Path(module.__file__).read_text(encoding="utf-8").lower()
            for forbidden in (
                "code_review", "architecture_review", "security_review",
                "planning_advice", "autonomous_repair", "refactoring_advice",
                "bug_finding",
            ):
                assert forbidden not in source, forbidden

    def test_helper_and_skill_have_no_question_override_parameter(self):
        import inspect
        helper_sig = inspect.signature(build_repository_consistency_skill_with_current_model)
        assert "question" not in helper_sig.parameters
        assert "objective" not in helper_sig.parameters
        init_sig = inspect.signature(RepositoryConsistencyAdvisorySkill.__init__)
        assert "objective" not in init_sig.parameters
        assert "question" not in init_sig.parameters

    def test_only_one_concrete_advisory_repository_skill_class_exists(self):
        import pcae.core.advisory_repository_skills as module
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        concrete_skill_classes = {
            name for name in class_names
            if name.endswith("AdvisorySkill") and name != "AdvisoryRepositorySkill"
        }
        assert concrete_skill_classes == {"RepositoryConsistencyAdvisorySkill"}


# ═══════════════════════════════════════════════════════════════════════
# Objective 7: no hidden configuration
# ═══════════════════════════════════════════════════════════════════════

class TestNoHiddenConfiguration:
    def test_no_provider_registry_class_defined(self):
        for module_name in ADVISORY_MODULES:
            import importlib
            module = importlib.import_module(module_name)
            tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
            class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
            assert not any("registry" in name.lower() for name in class_names)

    def test_no_backend_selection_function_defined(self):
        for module_name in ADVISORY_MODULES:
            import importlib
            module = importlib.import_module(module_name)
            tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
            func_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
            assert not any("select" in name.lower() and "backend" in name.lower() for name in func_names)
            assert not any(name.lower() in ("select_provider", "choose_provider", "get_provider") for name in func_names)

    def test_no_api_key_or_secret_config_referenced(self):
        for module_name in ADVISORY_MODULES:
            import importlib
            module = importlib.import_module(module_name)
            source = Path(module.__file__).read_text(encoding="utf-8").lower()
            for forbidden in ("api_key", "apikey", "secret_key", "os.environ", "getenv"):
                assert forbidden not in source, f"{module_name}: {forbidden}"

    def test_no_split_model_configuration_present(self):
        for module_name in ADVISORY_MODULES:
            import importlib
            module = importlib.import_module(module_name)
            source = Path(module.__file__).read_text(encoding="utf-8").lower()
            for forbidden in ("writer_model", "split_model", "advisory_model_config"):
                assert forbidden not in source

    def test_no_network_specific_configuration_present(self):
        for module_name in ADVISORY_MODULES:
            import importlib
            module = importlib.import_module(module_name)
            source = Path(module.__file__).read_text(encoding="utf-8").lower()
            for forbidden in ("base_url", "endpoint", "host=", "port=", "timeout_ms"):
                assert forbidden not in source

    def test_policy_toml_unmodified_by_advisory_work(self):
        policy_path = Path(__file__).resolve().parents[1] / ".pcae" / "policy.toml"
        if policy_path.exists():
            text = policy_path.read_text(encoding="utf-8").lower()
            assert "advisory_provider" not in text
            assert "deepseek" not in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 8: no execution capability
# ═══════════════════════════════════════════════════════════════════════

class TestNoExecutionCapability:
    def test_real_repository_execution_availability_unavailable(self):
        from pcae.core.repository_skills_integration import collect_evidence_via_repository_skills
        repo_root = HarnessPath(Path(__file__).resolve().parents[1])
        evidence = collect_evidence_via_repository_skills(repo_root)
        assert evidence.by_id("E-runtime-002").observed_value == "unavailable"

    def test_runtime_execution_unavailable_invariant_passes(self):
        from pcae.core.repository_skills_integration import build_evaluation_context_from_repository_skills
        repo_root = HarnessPath(Path(__file__).resolve().parents[1])
        context = build_evaluation_context_from_repository_skills(
            repo_root, evaluation_id="e", repository_snapshot_reference="HEAD",
        )
        result = evaluate(context)
        runtime_result = next(r for r in result.invariant_results if r.invariant_id == "runtime_execution_unavailable")
        assert runtime_result.status is InvariantStatus.PASS

    def test_advisory_modules_contain_no_execution_primitive(self):
        import re
        for module_name in ADVISORY_MODULES:
            import importlib
            module = importlib.import_module(module_name)
            source = Path(module.__file__).read_text(encoding="utf-8")
            code = re.sub(r'""".*?"""', "", source, flags=re.DOTALL)
            for forbidden in ("subprocess", "os.system", "Popen(", "exec(", "eval("):
                assert forbidden not in code, forbidden

    def test_default_registry_still_exactly_four_deterministic_skills(self):
        from pcae.core.repository_skills import build_default_registry
        registry = build_default_registry()
        assert len(registry.list_skills()) == 4
        skill_ids = {s.manifest.skill_id for s in registry.list_skills()}
        assert "repository_consistency_advisory_skill" not in skill_ids
