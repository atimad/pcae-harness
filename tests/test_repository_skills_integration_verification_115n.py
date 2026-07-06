"""Phase 115N: Repository Skills Integration Verification & Compatibility.

Verification-only phase re-proving, from a fresh angle, that 115M's
Repository Skills evidence-acquisition adapter
(``pcae.core.repository_skills_integration``) is fully behavior-
preserving: same evidence, same Decision Evaluation results, same
Repository Transition Validator verdicts, same lifecycle behavior. No
Repository Skill, Evidence Provider, Decision Evaluation, Repository
Transition Validator, lifecycle command, Notification Policy,
Canonical Artifact Promotion, Push-State Reconciliation, or Post-Push
Canonicalization is modified by this phase -- this module only reads
and asserts against the existing, unmodified implementation.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pcae.core.decision_evaluation import InvariantStatus, evaluate
from pcae.core.evidence import EvidenceCollection, EvidenceDeterminism
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


# ═══════════════════════════════════════════════════════════════════════
# Objective 1: evidence equivalence, per deterministic skill
# ═══════════════════════════════════════════════════════════════════════

class TestEvidenceEquivalencePerSkill:
    """Repository Skills path -> EvidenceCollection A == direct Evidence
    Provider path -> EvidenceCollection A, for every deterministic skill,
    exercised through 115M's own public integration functions (not just
    the raw skill/provider classes 115K already compared)."""

    @pytest.mark.parametrize("skill_id,prefix", [
        ("git_repository_skill", "E-git-"),
        ("runtime_repository_skill", "E-runtime-"),
        ("report_repository_skill", "E-report-"),
        ("metadata_repository_skill", "E-metadata-"),
    ])
    def test_single_skill_registry_matches_full_provider_subset(self, tmp_path, skill_id, prefix):
        _init_git_repo(tmp_path)
        registry = RepositorySkillRegistry()
        registry.register(next(cls() for cls in ALL_SKILL_CLASSES if cls.manifest.skill_id == skill_id))
        via_single_skill = collect_evidence_via_repository_skills(HarnessPath(tmp_path), registry=registry)
        via_full_providers = collect_evidence_via_evidence_providers(HarnessPath(tmp_path))
        expected_ids = {i.evidence_id for i in via_full_providers if i.evidence_id.startswith(prefix)}
        actual_ids = {i.evidence_id for i in via_single_skill}
        assert actual_ids == expected_ids
        for evidence_id in expected_ids:
            provider_item = via_full_providers.by_id(evidence_id)
            skill_item = via_single_skill.by_id(evidence_id)
            assert provider_item.observed_value == skill_item.observed_value
            assert provider_item.freshness == skill_item.freshness
            assert provider_item.confidence == skill_item.confidence
            assert provider_item.determinism == skill_item.determinism

    def test_full_registry_equivalence_holds_on_real_repository(self):
        provider_evidence = collect_evidence_via_evidence_providers(REPO_ROOT)
        skill_evidence = collect_evidence_via_repository_skills(REPO_ROOT)
        assert {i.evidence_id for i in provider_evidence} == {i.evidence_id for i in skill_evidence}
        for item in provider_evidence:
            assert item.observed_value == skill_evidence.by_id(item.evidence_id).observed_value

    def test_equivalence_is_stable_across_repeated_invocations(self, tmp_path):
        _init_git_repo(tmp_path)
        for _ in range(5):
            provider_evidence = collect_evidence_via_evidence_providers(HarnessPath(tmp_path))
            skill_evidence = collect_evidence_via_repository_skills(HarnessPath(tmp_path))
            assert {i.evidence_id for i in provider_evidence} == {i.evidence_id for i in skill_evidence}


# ═══════════════════════════════════════════════════════════════════════
# Objective 2: Decision Evaluation compatibility
# ═══════════════════════════════════════════════════════════════════════

class TestDecisionEvaluationCompatibility:
    def _pair(self, root: HarnessPath):
        provider_context = build_evaluation_context_from_evidence_providers(
            root, evaluation_id="115n-verify", repository_snapshot_reference="HEAD",
            evaluation_timestamp="fixed-t",
        )
        skill_context = build_evaluation_context_from_repository_skills(
            root, evaluation_id="115n-verify", repository_snapshot_reference="HEAD",
            evaluation_timestamp="fixed-t",
        )
        return evaluate(provider_context), evaluate(skill_context)

    def test_identical_invariant_evaluation_on_synthetic_repo(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_result, skill_result = self._pair(HarnessPath(tmp_path))
        assert provider_result.invariant_results == skill_result.invariant_results

    def test_identical_invariant_evaluation_on_real_repo(self):
        provider_result, skill_result = self._pair(REPO_ROOT)
        assert provider_result.invariant_results == skill_result.invariant_results

    def test_identical_blocking_failures(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_result, skill_result = self._pair(HarnessPath(tmp_path))
        assert provider_result.blocking_failures == skill_result.blocking_failures

    def test_identical_warnings(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_result, skill_result = self._pair(HarnessPath(tmp_path))
        assert provider_result.warnings == skill_result.warnings

    def test_identical_informational(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_result, skill_result = self._pair(HarnessPath(tmp_path))
        assert provider_result.informational == skill_result.informational

    def test_identical_explanation_references(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_result, skill_result = self._pair(HarnessPath(tmp_path))
        assert provider_result.explanation_reference == skill_result.explanation_reference

    def test_identical_summary_text(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_result, skill_result = self._pair(HarnessPath(tmp_path))
        assert provider_result.summary == skill_result.summary

    def test_full_evaluation_result_equality(self, tmp_path):
        _init_git_repo(tmp_path)
        provider_result, skill_result = self._pair(HarnessPath(tmp_path))
        assert provider_result == skill_result

    def test_equivalence_holds_on_repository_with_no_reports_or_metadata(self, tmp_path):
        """A minimal repo (evidence mostly UNKNOWN) is a harder case than
        the fully-populated real repo -- both paths must still agree."""
        _init_git_repo(tmp_path)
        provider_result, skill_result = self._pair(HarnessPath(tmp_path))
        assert provider_result == skill_result
        # Confirm this really is the harder, mostly-unresolved case.
        assert any(r.status is InvariantStatus.UNKNOWN for r in provider_result.invariant_results)


# ═══════════════════════════════════════════════════════════════════════
# Objective 3: Transition Validator compatibility
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


class TestTransitionValidatorCompatibility:
    def test_fully_consistent_state_still_accepts(self):
        result = validate_transition(_certified_state(), _complete_phase_transition(), _target())
        assert result.verdict == TransitionVerdict.ACCEPT
        assert result.violations == ()

    def test_identity_mismatch_still_rejects_with_same_violation(self):
        result = validate_transition(
            _certified_state(metadata_phase_id="113B"), _complete_phase_transition(), _target(),
        )
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "phase_identity_consistency" for v in result.violations)

    def test_partial_report_completeness_still_quarantines(self):
        result = validate_transition(
            _certified_state(report_completeness="partial"), _complete_phase_transition(), _target(),
        )
        assert result.verdict == TransitionVerdict.QUARANTINE
        assert any(v.invariant == "report_completeness" for v in result.violations)

    def test_execution_available_still_rejects(self):
        result = validate_transition(
            _certified_state(execution_availability="available"), _complete_phase_transition(), _target(),
        )
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "no_execution_availability_unless_contracted" for v in result.violations)

    def test_certified_to_canonical_promotion_still_accepts(self):
        result = validate_transition(
            _certified_state(artifact_state=ArtifactState.CERTIFIED),
            _complete_phase_transition(),
            _target(artifact_state=ArtifactState.CANONICAL),
        )
        assert result.verdict == TransitionVerdict.ACCEPT

    def test_blocked_to_canonical_promotion_still_rejects(self):
        result = validate_transition(
            _certified_state(artifact_state=ArtifactState.BLOCKED),
            _complete_phase_transition(),
            _target(artifact_state=ArtifactState.CANONICAL),
        )
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "canonical_promotion_eligibility" for v in result.violations)

    def test_verdict_and_violations_are_deterministic_across_repeated_calls(self):
        state = _certified_state(metadata_phase_id="113B")
        transition = _complete_phase_transition()
        target = _target()
        results = [validate_transition(state, transition, target) for _ in range(5)]
        assert len({r.verdict for r in results}) == 1
        assert len({r.violations for r in results}) == 1

    def test_validator_adapter_evidence_ids_subset_of_skill_path_evidence(self):
        adapter_evidence = build_evidence_from_repository_state(_certified_state())
        skill_evidence = collect_evidence_via_repository_skills(REPO_ROOT)
        assert {i.evidence_id for i in adapter_evidence} <= {i.evidence_id for i in skill_evidence}

    def test_validator_module_still_has_no_repository_skills_dependency(self):
        import pcae.core.repository_transition_validator as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "repository_skills" not in source


# ═══════════════════════════════════════════════════════════════════════
# Objective 4: lifecycle compatibility
# ═══════════════════════════════════════════════════════════════════════

class TestLifecycleCompatibility:
    """115N runs no lifecycle command itself (that would need real repo
    mutation outside this phase's scope) -- it instead re-confirms, at
    the source level, that no lifecycle command's behavior could have
    changed because none of them reference the 115M integration module
    or repository_skills at all. Full lifecycle behavior is exercised
    by the existing suites this phase's Validation section runs
    unmodified (test_repository_transition_validator_phase_complete_
    integration.py, test_repository_transition_validator_task_finish_
    integration.py, test_task_finish_notification_ordering.py,
    test_phase_reports*.py, test_notification*.py)."""

    @pytest.mark.parametrize("module_path", [
        "pcae.commands.phase",
        "pcae.commands.task",
        "pcae.commands.push",
        "pcae.core.repository_transition_integration",
        "pcae.core.notification_certification",
        "pcae.core.handoff_verification",
        "pcae.core.post_push_canonicalization",
        "pcae.commands.runtime_inspect",
    ])
    def test_lifecycle_module_never_references_repository_skills(self, module_path):
        import importlib
        module = importlib.import_module(module_path)
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "repository_skills" not in source

    def test_decision_evaluation_import_surface_unchanged(self):
        import pcae.core.decision_evaluation as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in ("evidence_providers", "repository_skills", "repository_transition_validator"):
            assert not any(forbidden in line for line in import_lines)

    def test_repository_skills_integration_module_still_not_wired_anywhere(self):
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
# Objective 5: registry behavior
# ═══════════════════════════════════════════════════════════════════════

class TestRegistryBehaviorVerification:
    def test_registration_order_deterministic(self):
        registry = build_default_registry()
        ids = [s.manifest.skill_id for s in registry.list_skills()]
        assert ids == [
            "git_repository_skill", "runtime_repository_skill",
            "report_repository_skill", "metadata_repository_skill",
        ]

    def test_invocation_order_matches_requested_order(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        requested = ("metadata_repository_skill", "git_repository_skill", "runtime_repository_skill")
        context = RepositorySkillContext(root=HarnessPath(tmp_path))
        results = registry.invoke_many(requested, context)
        assert tuple(r.skill_id for r in results) == requested

    def test_merge_is_order_independent(self, tmp_path):
        _init_git_repo(tmp_path)
        registry = build_default_registry()
        context = RepositorySkillContext(root=HarnessPath(tmp_path))
        forward = registry.invoke_many(
            ("git_repository_skill", "runtime_repository_skill", "report_repository_skill", "metadata_repository_skill"),
            context,
        )
        backward = registry.invoke_many(
            ("metadata_repository_skill", "report_repository_skill", "runtime_repository_skill", "git_repository_skill"),
            context,
        )
        assert (
            {i.evidence_id for i in registry.merge_evidence(forward)}
            == {i.evidence_id for i in registry.merge_evidence(backward)}
        )

    def test_duplicate_skill_registration_rejected(self):
        registry = RepositorySkillRegistry()
        registry.register(GitRepositorySkill())
        with pytest.raises(ValueError, match="Duplicate skill_id"):
            registry.register(GitRepositorySkill())

    def test_registry_lookup_stable_across_calls(self):
        registry = build_default_registry()
        assert registry.get("git_repository_skill") is registry.get("git_repository_skill")

    def test_collect_via_repository_skills_default_registry_matches_explicit_default_registry(self, tmp_path):
        _init_git_repo(tmp_path)
        implicit = collect_evidence_via_repository_skills(HarnessPath(tmp_path))
        explicit = collect_evidence_via_repository_skills(
            HarnessPath(tmp_path), registry=build_default_registry(),
        )
        assert {i.evidence_id for i in implicit} == {i.evidence_id for i in explicit}


# ═══════════════════════════════════════════════════════════════════════
# Objective 6: compatibility path (old provider path still functional)
# ═══════════════════════════════════════════════════════════════════════

class TestCompatibilityPathStillFunctional:
    def test_direct_provider_classes_still_importable_and_functional(self, tmp_path):
        from pcae.core.evidence_providers import (
            EvidenceProviderContext,
            GitEvidenceProvider,
            MetadataEvidenceProvider,
            ReportEvidenceProvider,
            RuntimeEvidenceProvider,
        )
        _init_git_repo(tmp_path)
        context = EvidenceProviderContext(root=HarnessPath(tmp_path))
        for provider_cls in (
            GitEvidenceProvider, RuntimeEvidenceProvider, ReportEvidenceProvider, MetadataEvidenceProvider,
        ):
            result = provider_cls().collect(context)
            assert isinstance(result.evidence, EvidenceCollection)
            assert len(result.evidence) > 0

    def test_collect_evidence_via_evidence_providers_still_functional(self, tmp_path):
        _init_git_repo(tmp_path)
        result = collect_evidence_via_evidence_providers(HarnessPath(tmp_path))
        assert isinstance(result, EvidenceCollection)
        assert len(result) > 0

    def test_build_evaluation_context_from_evidence_providers_still_functional(self, tmp_path):
        _init_git_repo(tmp_path)
        context = build_evaluation_context_from_evidence_providers(
            HarnessPath(tmp_path), evaluation_id="e", repository_snapshot_reference="HEAD",
        )
        result = evaluate(context)
        assert len(result.invariant_results) == 6

    def test_no_regression_in_provider_required_inputs(self):
        from pcae.core.evidence_providers import (
            GitEvidenceProvider,
            MetadataEvidenceProvider,
            ReportEvidenceProvider,
            RuntimeEvidenceProvider,
        )
        pairs = (
            (GitRepositorySkill, GitEvidenceProvider),
            (RuntimeRepositorySkill, RuntimeEvidenceProvider),
            (ReportRepositorySkill, ReportEvidenceProvider),
            (MetadataRepositorySkill, MetadataEvidenceProvider),
        )
        for skill_cls, provider_cls in pairs:
            assert skill_cls.manifest.required_inputs == provider_cls.required_inputs


# ═══════════════════════════════════════════════════════════════════════
# Objective 7: isolation (evidence only, never decide/mutate/execute/...)
# ═══════════════════════════════════════════════════════════════════════

class TestIsolationVerification:
    def test_skills_path_is_read_only(self, tmp_path):
        _init_git_repo(tmp_path)
        before = subprocess.run(
            ["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True,
        ).stdout
        collect_evidence_via_repository_skills(HarnessPath(tmp_path))
        after = subprocess.run(
            ["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True,
        ).stdout
        assert before == after

    def test_skills_path_creates_no_new_files(self, tmp_path):
        _init_git_repo(tmp_path)
        before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if ".git" not in p.parts)
        collect_evidence_via_repository_skills(HarnessPath(tmp_path))
        after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if ".git" not in p.parts)
        assert before == after

    def test_integration_module_has_no_write_authority_functions(self):
        import pcae.core.repository_skills_integration as module
        forbidden = {"commit", "push", "finalize", "notify", "authorize", "execute", "mutate"}
        public_names = {name for name in dir(module) if not name.startswith("_")}
        assert not (public_names & forbidden)

    def test_integration_module_source_has_no_execution_primitives(self):
        import pcae.core.repository_skills_integration as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("subprocess", "os.system", "Popen(", "exec(", "eval("):
            assert forbidden not in source

    def test_evaluate_never_called_from_within_the_new_module(self):
        """Decision Evaluation is invoked only by callers of this
        module's build_evaluation_context_from_* helpers -- never
        internally decided upon here."""
        import pcae.core.repository_skills_integration as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "evaluate(" not in source

    def test_no_result_object_carries_a_verdict_or_authorization_field(self):
        result = RepositorySkillResult(skill_id="x", status=RepositorySkillStatus.SUCCESS)
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(result)}
        assert not (field_names & {"verdict", "authorized", "committed", "pushed", "notified"})


# ═══════════════════════════════════════════════════════════════════════
# Objective 8: AI boundary
# ═══════════════════════════════════════════════════════════════════════

class TestAiBoundaryVerification:
    _FORBIDDEN_VENDORS = ("deepseek", "glm", "qwen", "claude", "gpt", "codex", "slm")

    def test_no_forbidden_vendor_skill_ids_registered(self):
        registry = build_default_registry()
        skill_ids = {s.manifest.skill_id for s in registry.list_skills()}
        for forbidden in self._FORBIDDEN_VENDORS:
            assert not any(forbidden in skill_id.lower() for skill_id in skill_ids)

    def test_no_advisory_skills_registered(self):
        from pcae.core.evidence import EvidenceDeterminism as ED
        registry = build_default_registry()
        for manifest in registry.list_manifests():
            assert manifest.determinism == ED.DETERMINISTIC
            assert manifest.model_produced is False

    def test_no_model_produced_evidence_in_merged_output(self, tmp_path):
        _init_git_repo(tmp_path)
        evidence = collect_evidence_via_repository_skills(HarnessPath(tmp_path))
        for item in evidence:
            assert item.determinism == EvidenceDeterminism.DETERMINISTIC

    def test_ai_review_capability_has_zero_registered_skills(self):
        from pcae.core.repository_skills import RepositorySkillCapability
        registry = build_default_registry()
        assert registry.filter_by_capability(RepositorySkillCapability.AI_REVIEW) == ()

    def test_integration_module_has_no_forbidden_vendor_imports(self):
        import pcae.core.repository_skills_integration as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        for forbidden in ("deepseek", "glm", "qwen", "gpt", "codex"):
            assert not any(forbidden in line.lower() for line in import_lines)

    def test_repository_skills_module_still_has_only_four_deterministic_skills(self):
        registry = build_default_registry()
        assert len(registry.list_skills()) == 4


# ═══════════════════════════════════════════════════════════════════════
# Objective 9: execution boundary
# ═══════════════════════════════════════════════════════════════════════

class TestExecutionBoundaryVerification:
    def test_real_repository_execution_availability_is_unavailable(self):
        evidence = collect_evidence_via_repository_skills(REPO_ROOT)
        assert evidence.by_id("E-runtime-002").observed_value == "unavailable"

    def test_runtime_execution_unavailable_invariant_passes(self):
        context = build_evaluation_context_from_repository_skills(
            REPO_ROOT, evaluation_id="e", repository_snapshot_reference="HEAD",
        )
        result = evaluate(context)
        runtime_result = next(
            r for r in result.invariant_results if r.invariant_id == "runtime_execution_unavailable"
        )
        assert runtime_result.status is InvariantStatus.PASS

    def test_runtime_inspect_reports_observed_state_and_observe_capability(self):
        import json
        proc = subprocess.run(
            ["python", "-m", "pcae", "runtime", "inspect", "--json"],
            cwd=REPO_ROOT.path, capture_output=True, text=True, timeout=30,
        )
        data = json.loads(proc.stdout)
        health = data["health"]
        assert health["execution_availability"] == "unavailable"
        assert health["current_runtime_state"] == "Observed"
        assert health["current_maximum_plugin_capability"] == "observe"


# ═══════════════════════════════════════════════════════════════════════
# Objective 10: fast_green discrepancy investigation
# ═══════════════════════════════════════════════════════════════════════

class TestFastGreenDiscrepancyInvestigation:
    """115M's final report recorded 4389/4390 fast_green with one
    failure: tests/test_dry_run_simulation.py::Test89dMatrixReadOnly::
    test_pytest_dry_run_not_blocked. This class proves the failure is a
    pre-existing, idle-state-dependent condition in
    core/permission_broker.py's ``_broker_decide`` -- unrelated to any
    115M or 115N change -- not a regression, not a flake, and not the
    intended behavior of the test itself (whose own comment expects
    "may require task", not a hard block)."""

    def test_permission_broker_module_untouched_by_115m_or_115n(self):
        """Neither 115M's nor 115N's own source files import or
        reference permission_broker/advisory/shell_gate/dry_run at
        all -- the discrepancy cannot be caused by this repository
        skills work."""
        for module_name in (
            "pcae.core.repository_skills_integration",
        ):
            import importlib
            module = importlib.import_module(module_name)
            source = Path(module.__file__).read_text(encoding="utf-8")
            for forbidden in ("permission_broker", "advisory", "shell_gate", "dry_run"):
                assert forbidden not in source

    def test_failure_reproduces_only_when_idle_not_with_an_active_task(self, tmp_path):
        """Root cause: core/permission_broker.py's ``_broker_decide``
        hits its 1d branch (``sg_decision == "requires_active_task" and
        task_contract is None``) whenever no active task exists,
        mapping a plain ``python -m pytest ...`` command to the hard-
        block decision ``blocked_by_task_contract`` -- which sets
        ``would_block=True`` and leaves ``would_require_active_task``
        (a *different* advisory decision, never produced by this
        branch) ``False``. The failing test's own assertion
        (``would_block is False or would_require_active_task``)
        therefore fails specifically when idle. This test reproduces
        both states directly against a synthetic ``tmp_path`` (no
        subprocess, no mutation of the real repository, no dependency
        on this phase's own currently-active task): with no
        ``tasks/active/`` directory, the command hard-blocks; with one
        present, it resolves to an allowed decision. This is the exact
        mechanism, isolated and reproduced deterministically."""
        from pcae.core.dry_run import build_simulation

        command = "python -m pytest tests/test_dry_run_simulation.py -q"

        idle = build_simulation(tmp_path, requested_command=command)
        assert idle["would_block"] is True
        assert idle["would_require_active_task"] is False
        assert idle["simulation_decision"] == "would_block_by_task_contract"

        active_dir = tmp_path / "tasks" / "active"
        active_dir.mkdir(parents=True)
        (active_dir / "x.md").write_text("## Allowed Files\n- foo.py\n", encoding="utf-8")
        with_task = build_simulation(tmp_path, requested_command=command)
        assert with_task["would_block"] is False

    def test_permission_broker_hard_block_branch_exists_and_is_documented(self):
        import pcae.core.permission_broker as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert 'sg_decision == "requires_active_task" and task_contract is None' in source
        assert "blocked_by_task_contract" in source
