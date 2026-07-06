"""Phase 115M: Repository Skills Integration Prototype.

Proves ``pcae.core.repository_skills_integration`` (the new Stage 3
adapter 115L's architecture document anticipated) is behavior-
preserving: "same evidence, same decisions, better architecture."

- The pre-115M Evidence Provider path
  (``collect_evidence_via_evidence_providers``) still works unmodified.
- The 115M Repository Skills path
  (``collect_evidence_via_repository_skills``) produces a semantically
  equivalent ``EvidenceCollection``.
- Decision Evaluation (``core/decision_evaluation.py``) produces
  identical ``EvaluationResult`` objects regardless of which path
  supplied its ``EvaluationContext``.
- The Repository Transition Validator's own verdicts and evidence-ID
  scheme are unaffected -- this module is not wired into
  ``validate_transition``, any lifecycle command, Notification Policy,
  Canonical Artifact Promotion, Push-State Reconciliation, or Post-Push
  Canonicalization.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pcae.core.decision_evaluation import EvaluationContext, InvariantStatus, evaluate
from pcae.core.evidence import Evidence, EvidenceCollection, EvidenceDeterminism
from pcae.core.paths import HarnessPath
from pcae.core.repository_skills import (
    GitRepositorySkill,
    RepositorySkillContext,
    RepositorySkillRegistry,
    build_default_registry,
)
from pcae.core.repository_skills_integration import (
    build_evaluation_context_from_evidence_providers,
    build_evaluation_context_from_repository_skills,
    collect_evidence_via_evidence_providers,
    collect_evidence_via_repository_skills,
)
from pcae.core.repository_transition_validator import (
    ArtifactState,
    ExpectedTargetState,
    ProposedTransition,
    RepositoryState,
    TransitionKind,
    TransitionVerdict,
    build_evidence_from_repository_state,
    validate_transition,
)

REPO_ROOT = HarnessPath(Path(__file__).resolve().parents[1])


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "a@b.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "a"], cwd=path, check=True, capture_output=True)
    (path / "README.md").write_text("hello\n")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=path, check=True, capture_output=True)


def _semantically_equal(a: Evidence, b: Evidence) -> bool:
    """Equality ignoring the two wall-clock timestamp fields (each path
    calls ``datetime.now()`` independently, so those legitimately
    differ) -- every other field must match exactly."""
    return (
        a.evidence_id == b.evidence_id
        and a.source == b.source
        and a.category == b.category
        and a.producer == b.producer
        and a.freshness == b.freshness
        and a.confidence == b.confidence
        and a.determinism == b.determinism
        and a.scope == b.scope
        and a.references == b.references
        and a.observed_value == b.observed_value
        and a.expected_value == b.expected_value
        and a.explanation == b.explanation
        and a.limitations == b.limitations
        and a.provenance.producer == b.provenance.producer
        and a.provenance.produced_from == b.provenance.produced_from
        and a.provenance.deterministic_origin == b.provenance.deterministic_origin
    )


# ═══════════════════════════════════════════════════════════════════════
# Objective 1: skill-based evidence acquisition
# ═══════════════════════════════════════════════════════════════════════

class TestSkillBasedEvidenceAcquisition:
    def test_collect_via_repository_skills_returns_evidence_collection(self, tmp_path):
        _init_git_repo(tmp_path)
        result = collect_evidence_via_repository_skills(HarnessPath(tmp_path))
        assert isinstance(result, EvidenceCollection)
        assert len(result) > 0

    def test_collect_via_repository_skills_covers_all_four_default_skills(self, tmp_path):
        _init_git_repo(tmp_path)
        result = collect_evidence_via_repository_skills(HarnessPath(tmp_path))
        ids = {item.evidence_id for item in result}
        assert any(i.startswith("E-git-") for i in ids)
        assert any(i.startswith("E-runtime-") for i in ids)
        assert any(i.startswith("E-report-") for i in ids)
        assert any(i.startswith("E-metadata-") for i in ids)

    def test_collect_via_repository_skills_accepts_a_custom_registry(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = RepositorySkillRegistry()
        registry.register(GitRepositorySkill())
        result = collect_evidence_via_repository_skills(HarnessPath(tmp_path), registry=registry)
        ids = {item.evidence_id for item in result}
        assert ids and all(i.startswith("E-git-") for i in ids)

    def test_collect_via_repository_skills_uses_default_registry_by_default(self, tmp_path):
        _init_git_repo(tmp_path)
        explicit = collect_evidence_via_repository_skills(
            HarnessPath(tmp_path), registry=build_default_registry(),
        )
        implicit = collect_evidence_via_repository_skills(HarnessPath(tmp_path))
        assert {i.evidence_id for i in explicit} == {i.evidence_id for i in implicit}

    def test_only_deterministic_skills_are_used(self, tmp_path):
        _init_git_repo(tmp_path)
        result = collect_evidence_via_repository_skills(HarnessPath(tmp_path))
        for item in result:
            assert item.determinism == EvidenceDeterminism.DETERMINISTIC


# ═══════════════════════════════════════════════════════════════════════
# Objective 2: provider path preserved
# ═══════════════════════════════════════════════════════════════════════

class TestProviderPathStillWorks:
    def test_collect_via_evidence_providers_returns_evidence_collection(self, tmp_path):
        _init_git_repo(tmp_path)
        result = collect_evidence_via_evidence_providers(HarnessPath(tmp_path))
        assert isinstance(result, EvidenceCollection)
        assert len(result) > 0

    def test_collect_via_evidence_providers_matches_manual_direct_calls(self, tmp_path):
        _init_git_repo(tmp_path)
        from pcae.core.evidence_providers import (
            EvidenceProviderContext,
            GitEvidenceProvider,
            MetadataEvidenceProvider,
            ReportEvidenceProvider,
            RuntimeEvidenceProvider,
        )
        context = EvidenceProviderContext(root=HarnessPath(tmp_path))
        manual_ids = set()
        for provider_cls in (
            GitEvidenceProvider, RuntimeEvidenceProvider, ReportEvidenceProvider, MetadataEvidenceProvider,
        ):
            manual_ids |= {i.evidence_id for i in provider_cls().collect(context).evidence}
        via_helper = collect_evidence_via_evidence_providers(HarnessPath(tmp_path))
        assert {i.evidence_id for i in via_helper} == manual_ids

    def test_evidence_providers_still_importable_and_unmodified_shape(self):
        from pcae.core.evidence_providers import GitEvidenceProvider
        assert GitEvidenceProvider.provider_id == "git_provider"
        assert GitEvidenceProvider.determinism == EvidenceDeterminism.DETERMINISTIC


# ═══════════════════════════════════════════════════════════════════════
# Objective 3: evidence equivalence
# ═══════════════════════════════════════════════════════════════════════

class TestEvidenceEquivalence:
    def test_same_evidence_ids_from_both_paths(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_evidence = collect_evidence_via_evidence_providers(HarnessPath(tmp_path))
        skill_evidence = collect_evidence_via_repository_skills(HarnessPath(tmp_path))
        assert {i.evidence_id for i in provider_evidence} == {i.evidence_id for i in skill_evidence}

    def test_every_item_semantically_equal_across_paths(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_evidence = collect_evidence_via_evidence_providers(HarnessPath(tmp_path))
        skill_evidence = collect_evidence_via_repository_skills(HarnessPath(tmp_path))
        for item in provider_evidence:
            counterpart = skill_evidence.by_id(item.evidence_id)
            assert counterpart is not None
            assert _semantically_equal(item, counterpart), (
                f"{item.evidence_id} differs between provider and skill paths"
            )

    def test_equivalence_holds_against_the_real_repository_root(self):
        provider_evidence = collect_evidence_via_evidence_providers(REPO_ROOT)
        skill_evidence = collect_evidence_via_repository_skills(REPO_ROOT)
        assert {i.evidence_id for i in provider_evidence} == {i.evidence_id for i in skill_evidence}
        for item in provider_evidence:
            counterpart = skill_evidence.by_id(item.evidence_id)
            assert _semantically_equal(item, counterpart)

    def test_equivalence_holds_on_a_repository_with_no_reports_or_metadata(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_evidence = collect_evidence_via_evidence_providers(HarnessPath(tmp_path))
        skill_evidence = collect_evidence_via_repository_skills(HarnessPath(tmp_path))
        assert provider_evidence.by_id("E-report-001").observed_value is False
        assert skill_evidence.by_id("E-report-001").observed_value is False
        for item in provider_evidence:
            assert _semantically_equal(item, skill_evidence.by_id(item.evidence_id))


# ═══════════════════════════════════════════════════════════════════════
# Objective 4: Decision Evaluation equivalence
# ═══════════════════════════════════════════════════════════════════════

class TestDecisionEvaluationEquivalence:
    def _contexts(self, root: HarnessPath) -> tuple[EvaluationContext, EvaluationContext]:
        provider_context = build_evaluation_context_from_evidence_providers(
            root, evaluation_id="115m-equivalence", repository_snapshot_reference="HEAD",
            evaluation_timestamp="fixed-t",
        )
        skill_context = build_evaluation_context_from_repository_skills(
            root, evaluation_id="115m-equivalence", repository_snapshot_reference="HEAD",
            evaluation_timestamp="fixed-t",
        )
        return provider_context, skill_context

    def test_evaluate_result_identical_for_both_paths(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_context, skill_context = self._contexts(HarnessPath(tmp_path))
        assert evaluate(provider_context) == evaluate(skill_context)

    def test_evaluate_result_identical_on_the_real_repository(self):
        provider_context, skill_context = self._contexts(REPO_ROOT)
        assert evaluate(provider_context) == evaluate(skill_context)

    def test_six_invariants_evaluated_for_both_paths(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_context, skill_context = self._contexts(HarnessPath(tmp_path))
        assert len(evaluate(provider_context).invariant_results) == 6
        assert len(evaluate(skill_context).invariant_results) == 6

    def test_explanation_references_resolve_against_skill_evidence(self, tmp_path):
        _init_git_repo(tmp_path)
        _, skill_context = self._contexts(HarnessPath(tmp_path))
        result = evaluate(skill_context)
        for ref in result.explanation_reference:
            assert skill_context.evidence.by_id(ref.evidence_id) is not None


# ═══════════════════════════════════════════════════════════════════════
# Objective 5: Repository Transition Validator compatibility
# ═══════════════════════════════════════════════════════════════════════

def _certified_state(**overrides) -> RepositoryState:
    base = dict(
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
    base.update(overrides)
    return RepositoryState(**base)


def _complete_phase_transition(**payload) -> ProposedTransition:
    return ProposedTransition(kind=TransitionKind.COMPLETE_PHASE, payload=payload)


def _target(**overrides) -> ExpectedTargetState:
    base = dict(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
    base.update(overrides)
    return ExpectedTargetState(**base)


class TestValidatorVerdictCompatibility:
    """Re-runs 113U/115F's own regression scenarios verbatim: 115M adds
    a new evidence-acquisition adapter but touches no line of
    ``repository_transition_validator.py``, so these verdicts must be
    byte-identical to the pre-115M suite."""

    def test_fully_consistent_state_still_accepts(self):
        result = validate_transition(_certified_state(), _complete_phase_transition(), _target())
        assert result.verdict == TransitionVerdict.ACCEPT
        assert result.violations == ()

    def test_identity_mismatch_still_rejects(self):
        result = validate_transition(
            _certified_state(metadata_phase_id="113B"), _complete_phase_transition(), _target(),
        )
        assert result.verdict == TransitionVerdict.REJECT

    def test_partial_report_completeness_still_quarantines(self):
        result = validate_transition(
            _certified_state(report_completeness="partial"), _complete_phase_transition(), _target(),
        )
        assert result.verdict == TransitionVerdict.QUARANTINE

    def test_execution_available_still_rejects(self):
        result = validate_transition(
            _certified_state(execution_availability="available"), _complete_phase_transition(), _target(),
        )
        assert result.verdict == TransitionVerdict.REJECT

    def test_validator_adapter_evidence_ids_are_a_subset_of_skill_path_evidence_ids(self):
        """Proves 'equivalent Evidence IDs': every Evidence ID the
        validator's own 115F adapter cites also exists (with the same
        meaning) in the richer skill-path EvidenceCollection."""
        adapter_evidence = build_evidence_from_repository_state(_certified_state())
        skill_evidence = collect_evidence_via_repository_skills(REPO_ROOT)
        adapter_ids = {i.evidence_id for i in adapter_evidence}
        skill_ids = {i.evidence_id for i in skill_evidence}
        assert adapter_ids <= skill_ids
        assert "E-report-003" in adapter_ids

    def test_validator_module_does_not_import_the_new_integration_module(self):
        import pcae.core.repository_transition_validator as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "repository_skills_integration" not in source
        assert "repository_skills" not in source


# ═══════════════════════════════════════════════════════════════════════
# Objective 6: no lifecycle behavior change / no hidden integration
# ═══════════════════════════════════════════════════════════════════════

class TestNoLifecycleBehaviorChange:
    @pytest.mark.parametrize("module_path", [
        "pcae.core.decision_evaluation",
        "pcae.core.repository_skills",
        "pcae.core.repository_transition_validator",
        "pcae.core.repository_transition_integration",
        "pcae.commands.phase",
        "pcae.commands.task",
        "pcae.commands.push",
        "pcae.core.notification_certification",
        "pcae.core.handoff_verification",
        "pcae.core.post_push_canonicalization",
        "pcae.commands.runtime_inspect",
    ])
    def test_module_never_references_the_new_integration_module(self, module_path):
        import importlib
        module = importlib.import_module(module_path)
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "repository_skills_integration" not in source

    def test_decision_evaluation_still_imports_only_evidence(self):
        import pcae.core.decision_evaluation as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in ("evidence_providers", "repository_skills", "repository_transition_validator"):
            assert not any(forbidden in line for line in import_lines)

    def test_new_module_does_not_import_lifecycle_or_notification_or_validator(self):
        import pcae.core.repository_skills_integration as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in (
            "pcae.commands", "notification_certification", "handoff_verification",
            "post_push_canonicalization", "repository_transition_validator",
            "repository_transition_integration",
        ):
            assert not any(forbidden in line for line in import_lines)


# ═══════════════════════════════════════════════════════════════════════
# Objective 7: no AI/SLM/DeepSeek; execution remains unavailable
# ═══════════════════════════════════════════════════════════════════════

class TestNoAiIntegrationAndExecutionUnavailable:
    def test_new_module_has_no_ai_or_vendor_imports(self):
        import pcae.core.repository_skills_integration as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in ("deepseek", "glm", "qwen", "gpt", "codex"):
            assert not any(forbidden in line.lower() for line in import_lines)

    def test_default_registry_has_no_ai_backed_skill_ids(self):
        registry = build_default_registry()
        skill_ids = {s.manifest.skill_id for s in registry.list_skills()}
        for forbidden in ("deepseek", "glm", "qwen", "claude", "gpt", "codex"):
            assert not any(forbidden in skill_id.lower() for skill_id in skill_ids)

    def test_new_module_source_has_no_execution_primitives(self):
        import pcae.core.repository_skills_integration as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("subprocess", "os.system", "Popen(", "exec(", "eval("):
            assert forbidden not in source

    def test_execution_availability_evidence_is_unavailable_for_the_real_repository(self):
        skill_evidence = collect_evidence_via_repository_skills(REPO_ROOT)
        exec_item = skill_evidence.by_id("E-runtime-002")
        assert exec_item is not None
        assert exec_item.observed_value == "unavailable"

    def test_execution_availability_evidence_agrees_between_both_paths(self):
        provider_evidence = collect_evidence_via_evidence_providers(REPO_ROOT)
        skill_evidence = collect_evidence_via_repository_skills(REPO_ROOT)
        assert (
            provider_evidence.by_id("E-runtime-002").observed_value
            == skill_evidence.by_id("E-runtime-002").observed_value
            == "unavailable"
        )

    def test_runtime_execution_unavailable_invariant_passes_for_skill_path(self, tmp_path):
        _init_git_repo(tmp_path)
        context = build_evaluation_context_from_repository_skills(
            HarnessPath(tmp_path), evaluation_id="e", repository_snapshot_reference="HEAD",
            evaluation_timestamp="t",
        )
        result = evaluate(context)
        runtime_result = next(
            r for r in result.invariant_results if r.invariant_id == "runtime_execution_unavailable"
        )
        assert runtime_result.status is InvariantStatus.PASS
