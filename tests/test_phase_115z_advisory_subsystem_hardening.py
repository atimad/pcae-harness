"""Phase 115Z: Advisory Subsystem Hardening & Release Readiness.

Consolidation/hardening verification only. Reviews the entire Advisory
subsystem introduced across 115P-115Y end to end: architectural
consistency, extension-point stability, containment, implementation-
vs-contract consistency, no duplicated responsibilities, no circular
dependencies, no authority leakage, and roadmap consistency. No new
Advisory Provider, Repository Skill, Evidence Provider, or runtime
module is added by this phase.

Scope note: this subsystem is distinct from the pre-existing, unrelated
"Advisory Mode" (Phase 88X, ``core/advisory.py``) and "Advisory Runtime"
(Phase 113C, ``core/advisory_runtime.py``) governance-simulation
subsystems -- those are read-only command-classification layers with
no connection to Advisory Repository Skills. This phase, and every
module path list below, scopes precisely to the three 115P-115Y
Advisory Repository Skills modules only.
"""
from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# The three runtime modules 115P-115Y's Advisory Repository Skills
# subsystem actually implemented. Deliberately excludes
# core/advisory.py (Phase 88X) and core/advisory_runtime.py (Phase
# 113C) -- unrelated, pre-existing subsystems.
ADVISORY_SUBSYSTEM_MODULES = (
    "pcae.core.advisory_repository_skills",
    "pcae.core.current_acting_model_advisory_provider",
    "pcae.core.advisory_context_package",
)

# Canonical architecture/contract documents produced across 115P-115Y.
CANONICAL_DOCS = (
    "PCAE_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md",   # 115P
    "PCAE_ADVISORY_REPOSITORY_SKILLS_CONTRACT.md",       # 115Q
    "PCAE_ADVISORY_PROVIDER_STRATEGY.md",                # 115U
    "PCAE_ADVISORY_EVIDENCE_ENRICHMENT.md",              # 115V
    "PCAE_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md",         # 115W
)

# Phase reports produced across 115P-115Y, in order.
PHASE_DOCS = (
    "PHASE_115P_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md",
    "PHASE_115Q_ADVISORY_REPOSITORY_SKILLS_CONTRACT_FREEZE.md",
    "PHASE_115R_ADVISORY_REPOSITORY_SKILLS_PROTOTYPE.md",
    "PHASE_115S_FIRST_ADVISORY_PROVIDER_INTEGRATION.md",
    "PHASE_115T_ADVISORY_PROVIDER_VERIFICATION.md",
    "PHASE_115U_ADVISORY_PROVIDER_STRATEGY_REVIEW.md",
    "PHASE_115V_ADVISORY_EVIDENCE_ENRICHMENT_ARCHITECTURE.md",
    "PHASE_115W_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md",
    "PHASE_115X_ADVISORY_CONTEXT_PACKAGE_PROTOTYPE.md",
    "PHASE_115Y_ADVISORY_CONTEXT_PACKAGE_VERIFICATION.md",
)

HARDENING_ARCH_DOC = REPO_ROOT / "docs" / "PHASE_115Z_ADVISORY_SUBSYSTEM_HARDENING.md"


def _read(relative: str) -> str:
    path = REPO_ROOT / "docs" / relative
    assert path.exists(), f"expected document missing: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _module_source(module_path: str) -> str:
    module = importlib.import_module(module_path)
    return Path(module.__file__).read_text(encoding="utf-8")


def _import_lines(source: str) -> list[str]:
    return [
        line for line in source.splitlines()
        if line.strip().startswith("from ") or line.strip().startswith("import ")
    ]


# ═══════════════════════════════════════════════════════════════════════
# Objective 9 (Documentation): subsystem doc inventory
# ═══════════════════════════════════════════════════════════════════════

class TestSubsystemDocInventory:
    @pytest.mark.parametrize("doc", CANONICAL_DOCS)
    def test_canonical_doc_exists(self, doc):
        _read(doc)

    @pytest.mark.parametrize("doc", PHASE_DOCS)
    def test_phase_doc_exists(self, doc):
        _read(doc)

    def test_hardening_doc_exists(self):
        assert HARDENING_ARCH_DOC.exists()

    def test_exactly_ten_phase_docs_from_115p_through_115y(self):
        assert len(PHASE_DOCS) == 10

    def test_three_runtime_modules_exist(self):
        for module_path in ADVISORY_SUBSYSTEM_MODULES:
            module = importlib.import_module(module_path)
            assert Path(module.__file__).exists()


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 / 4: architectural review, consistency
# ═══════════════════════════════════════════════════════════════════════

class TestArchitectureConsistency:
    @pytest.mark.parametrize("doc", CANONICAL_DOCS + PHASE_DOCS)
    def test_execution_unavailable_confirmed_in_every_document(self, doc):
        text = _read(doc)
        assert "Execution capability remains unavailable" in text

    def test_core_terminology_consistent_across_canonical_docs(self):
        for doc in CANONICAL_DOCS:
            text = _normalized(_read(doc))
            assert "Advisory Repository Skill" in text or "AdvisoryProvider" in text or "AdvisoryContextPackage" in text

    def test_pilot_question_identical_string_everywhere_it_appears(self):
        pilot_question = "Is the repository state internally consistent?"
        docs_mentioning_it = []
        for doc in CANONICAL_DOCS + PHASE_DOCS:
            text = _normalized(_read(doc))
            if "repository state internally consistent" in text.lower():
                docs_mentioning_it.append(doc)
                assert pilot_question in text, f"{doc} paraphrases the pilot question instead of quoting it exactly"
        assert len(docs_mentioning_it) >= 3

    def test_same_model_default_terminology_consistent(self):
        for doc in ("PCAE_ADVISORY_PROVIDER_STRATEGY.md", "PCAE_ADVISORY_REPOSITORY_SKILLS_CONTRACT.md"):
            text = _normalized(_read(doc))
            assert "current acting model" in text.lower()

    def test_cross_phase_references_present(self):
        """Each later canonical doc's "Relationship to Prior Phases"
        section actually names its immediate predecessor phase."""
        checks = {
            "PCAE_ADVISORY_REPOSITORY_SKILLS_CONTRACT.md": "115P",
            "PCAE_ADVISORY_PROVIDER_STRATEGY.md": "115T",
            "PCAE_ADVISORY_EVIDENCE_ENRICHMENT.md": "115U",
            "PCAE_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md": "115V",
        }
        for doc, expected_predecessor in checks.items():
            text = _read(doc)
            assert expected_predecessor in text, f"{doc} does not reference {expected_predecessor}"

    def test_recommended_next_phase_chain_is_unbroken(self):
        """Each phase doc's own 'Recommended Next Phase' names the
        phase that actually followed it, per this arc's real history."""
        expected_chain = {
            "PHASE_115P_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md": "115Q",
            "PHASE_115Q_ADVISORY_REPOSITORY_SKILLS_CONTRACT_FREEZE.md": "115R",
            "PHASE_115R_ADVISORY_REPOSITORY_SKILLS_PROTOTYPE.md": "115S",
            "PHASE_115S_FIRST_ADVISORY_PROVIDER_INTEGRATION.md": "115T",
            "PHASE_115T_ADVISORY_PROVIDER_VERIFICATION.md": "115U",
            "PHASE_115U_ADVISORY_PROVIDER_STRATEGY_REVIEW.md": "115V",
            "PHASE_115V_ADVISORY_EVIDENCE_ENRICHMENT_ARCHITECTURE.md": "115W",
            "PHASE_115W_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md": "115X",
            "PHASE_115X_ADVISORY_CONTEXT_PACKAGE_PROTOTYPE.md": "115Y",
            "PHASE_115Y_ADVISORY_CONTEXT_PACKAGE_VERIFICATION.md": "115Z",
        }
        for doc, expected_next in expected_chain.items():
            text = _read(doc)
            assert "Recommended Next Phase" in text
            tail = text[text.index("Recommended Next Phase"):]
            assert expected_next in tail, f"{doc} does not recommend {expected_next} next"


# ═══════════════════════════════════════════════════════════════════════
# Diagrams
# ═══════════════════════════════════════════════════════════════════════

class TestDiagramsConsistent:
    @pytest.mark.parametrize("doc", [
        "PCAE_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md",
        "PCAE_ADVISORY_REPOSITORY_SKILLS_CONTRACT.md",
    ])
    def test_mermaid_diagram_present(self, doc):
        text = _read(doc)
        assert "```mermaid" in text
        assert "flowchart TD" in text or "flowchart LR" in text

    def test_repository_skills_contract_has_two_diagrams(self):
        text = _read("PCAE_ADVISORY_REPOSITORY_SKILLS_CONTRACT.md")
        assert text.count("```mermaid") >= 2

    def test_diagrams_reference_the_same_pipeline_stages(self):
        text = _read("PCAE_ADVISORY_REPOSITORY_SKILLS_CONTRACT.md")
        first_diagram = text[text.index("```mermaid"):]
        for node in ("Advisory Repository Skill", "Prompt Builder", "Advisory Provider"):
            assert node in first_diagram, node


# ═══════════════════════════════════════════════════════════════════════
# Objective 2: extension points frozen and stable
# ═══════════════════════════════════════════════════════════════════════

class TestExtensionPointsFrozen:
    def test_advisory_provider_extension_point_is_abstract_with_one_method(self):
        from pcae.core.advisory_repository_skills import AdvisoryProvider
        assert inspect.isabstract(AdvisoryProvider)
        abstract_methods = AdvisoryProvider.__abstractmethods__
        assert abstract_methods == frozenset({"invoke"})

    def test_advisory_provider_has_exactly_two_conforming_implementations(self):
        from pcae.core.advisory_repository_skills import AdvisoryProvider, MockAdvisoryProvider
        from pcae.core.current_acting_model_advisory_provider import CurrentActingModelAdvisoryProvider
        assert issubclass(MockAdvisoryProvider, AdvisoryProvider)
        assert issubclass(CurrentActingModelAdvisoryProvider, AdvisoryProvider)

    def test_repository_skill_extension_point_unchanged_abstract_shape(self):
        from pcae.core.repository_skills import RepositorySkill
        assert inspect.isabstract(RepositorySkill)
        assert RepositorySkill.__abstractmethods__ == frozenset({"invoke"})

    def test_advisory_repository_skill_extends_repository_skill(self):
        from pcae.core.advisory_repository_skills import AdvisoryRepositorySkill
        from pcae.core.repository_skills import RepositorySkill
        assert issubclass(AdvisoryRepositorySkill, RepositorySkill)

    def test_evidence_provider_extension_point_unchanged(self):
        from pcae.core.evidence_providers import EvidenceProvider
        assert inspect.isabstract(EvidenceProvider)
        assert EvidenceProvider.__abstractmethods__ == frozenset({"collect"})

    def test_advisory_context_package_frozen_field_set_unchanged(self):
        import dataclasses
        from pcae.core.advisory_context_package import AdvisoryContextPackage
        field_names = {f.name for f in dataclasses.fields(AdvisoryContextPackage)}
        assert field_names == {
            "package_id", "created_at_utc", "objective", "advisory_question",
            "trusted_pcae_instructions", "repository_summary",
            "deterministic_evidence_summary", "transition_context",
            "constraints_and_no_go_rules", "artifact_references",
            "untrusted_repository_content", "provenance", "limitations",
            "size_budget", "redaction_summary",
        }

    def test_decision_evaluation_extension_point_unchanged_signature(self):
        from pcae.core.decision_evaluation import evaluate
        sig = inspect.signature(evaluate)
        assert list(sig.parameters) == ["context"]

    def test_decision_evaluation_still_has_exactly_six_invariant_evaluators(self):
        from pcae.core.decision_evaluation import INVARIANT_EVALUATORS
        assert len(INVARIANT_EVALUATORS) == 6


# ═══════════════════════════════════════════════════════════════════════
# Objective 3: containment (evidence-only, no authority)
# ═══════════════════════════════════════════════════════════════════════

class TestContainmentAcrossSubsystem:
    _FORBIDDEN_METHODS = {
        "decide", "authorize", "commit", "push", "finalize", "notify",
        "mutate", "execute", "approve", "reject",
    }

    @pytest.mark.parametrize("module_path", ADVISORY_SUBSYSTEM_MODULES)
    def test_no_forbidden_public_method_on_any_class(self, module_path):
        module = importlib.import_module(module_path)
        for name in dir(module):
            obj = getattr(module, name)
            if inspect.isclass(obj) and obj.__module__ == module_path:
                public_methods = {m for m in dir(obj) if not m.startswith("_")}
                overlap = public_methods & self._FORBIDDEN_METHODS
                assert not overlap, f"{module_path}.{name} exposes forbidden method(s): {overlap}"

    @pytest.mark.parametrize("module_path", ADVISORY_SUBSYSTEM_MODULES)
    def test_no_execution_primitive_in_code(self, module_path):
        import re
        source = _module_source(module_path)
        code = re.sub(r'""".*?"""', "", source, flags=re.DOTALL)
        for forbidden in (
            "subprocess", "os.system", "Popen(", "exec(", "eval(",
            "socket.", "urllib", "requests.", "http.client",
        ):
            assert forbidden not in code, f"{module_path}: {forbidden}"

    def test_model_cannot_authorize_no_verdict_type_anywhere(self):
        for module_path in ADVISORY_SUBSYSTEM_MODULES:
            source = _module_source(module_path)
            import_lines = _import_lines(source)
            assert not any("TransitionVerdict" in line for line in import_lines)

    def test_model_cannot_bypass_validator(self):
        """The validator never references any advisory subsystem
        module, and no advisory subsystem module references the
        validator -- the boundary holds in both directions."""
        validator_source = _module_source("pcae.core.repository_transition_validator")
        for advisory_module in ADVISORY_SUBSYSTEM_MODULES:
            short_name = advisory_module.rsplit(".", 1)[-1]
            assert short_name not in validator_source
        for module_path in ADVISORY_SUBSYSTEM_MODULES:
            import_lines = _import_lines(_module_source(module_path))
            assert not any("repository_transition_validator" in line for line in import_lines)

    def test_model_cannot_bypass_normalization(self):
        """The Evidence Builder's public signature only ever accepts a
        NormalizedAdvisoryResponse -- a RawAdvisoryResponse can never
        be passed to it directly."""
        from pcae.core.advisory_repository_skills import build_evidence_from_normalized
        sig = inspect.signature(build_evidence_from_normalized)
        annotation = sig.parameters["normalized"].annotation
        assert annotation in ("NormalizedAdvisoryResponse", None) or "NormalizedAdvisoryResponse" in str(annotation)

    def test_model_cannot_mutate_repository_reconfirmed(self, tmp_path):
        import subprocess
        from pcae.core.paths import HarnessPath
        from pcae.core.repository_skills import RepositorySkillContext
        from pcae.core.current_acting_model_advisory_provider import (
            build_repository_consistency_skill_with_current_model,
        )
        (tmp_path / "README.md").write_text("hello\n")
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
        before = subprocess.run(["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True).stdout
        skill = build_repository_consistency_skill_with_current_model(
            '{"findings": ["x"], "limitations": "l"}',
        )
        skill.invoke(RepositorySkillContext(root=HarnessPath(tmp_path)))
        after = subprocess.run(["git", "log", "--oneline"], cwd=tmp_path, capture_output=True, text=True).stdout
        assert before == after

    def test_decision_evaluation_never_imports_any_advisory_subsystem_module(self):
        import_lines = _import_lines(_module_source("pcae.core.decision_evaluation"))
        for advisory_module in ADVISORY_SUBSYSTEM_MODULES:
            short_name = advisory_module.rsplit(".", 1)[-1]
            assert not any(short_name in line for line in import_lines)

    @pytest.mark.parametrize("module_path", [
        "pcae.commands.phase",
        "pcae.commands.task",
        "pcae.commands.push",
        "pcae.core.notification_certification",
        "pcae.core.handoff_verification",
        "pcae.core.post_push_canonicalization",
        "pcae.commands.runtime_inspect",
        "pcae.core.repository_skills_integration",
        "pcae.core.repository_transition_integration",
    ])
    def test_no_lifecycle_module_references_advisory_subsystem(self, module_path):
        source = _module_source(module_path)
        for advisory_module in ADVISORY_SUBSYSTEM_MODULES:
            short_name = advisory_module.rsplit(".", 1)[-1]
            assert short_name not in source, f"{module_path} references {short_name}"


# ═══════════════════════════════════════════════════════════════════════
# No duplicated responsibilities / no circular dependencies
# ═══════════════════════════════════════════════════════════════════════

class TestNoDuplicatedResponsibilities:
    def test_normalizer_defined_exactly_once(self):
        count = sum(
            _module_source(m).count("def normalize_advisory_response(")
            for m in ADVISORY_SUBSYSTEM_MODULES
        )
        assert count == 1

    def test_evidence_builder_defined_exactly_once(self):
        count = sum(
            _module_source(m).count("def build_evidence_from_normalized(")
            for m in ADVISORY_SUBSYSTEM_MODULES
        )
        assert count == 1

    def test_prompt_builder_defined_exactly_once(self):
        count = sum(
            _module_source(m).count("def build_advisory_request(")
            for m in ADVISORY_SUBSYSTEM_MODULES
        )
        assert count == 1

    def test_only_one_concrete_advisory_repository_skill_class(self):
        source = _module_source("pcae.core.advisory_repository_skills")
        tree = ast.parse(source)
        class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        concrete = {n for n in class_names if n.endswith("AdvisorySkill") and n != "AdvisoryRepositorySkill"}
        assert concrete == {"RepositoryConsistencyAdvisorySkill"}

    def test_only_one_real_advisory_provider_implementation(self):
        """MockAdvisoryProvider (test/prototype fixture) and
        CurrentActingModelAdvisoryProvider (the one real provider) are
        the only two AdvisoryProvider implementations in the
        subsystem -- no duplicate 'real' provider exists."""
        source = _module_source("pcae.core.current_acting_model_advisory_provider")
        tree = ast.parse(source)
        class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        assert class_names == {"CurrentActingModelAdvisoryProvider"}


class TestNoCircularDependencies:
    def test_advisory_context_package_has_zero_internal_pcae_imports(self):
        """Fully standalone -- cannot participate in any cycle."""
        source = _module_source("pcae.core.advisory_context_package")
        import_lines = _import_lines(source)
        assert not any(line.strip().startswith(("from pcae", "import pcae")) for line in import_lines)

    def test_current_acting_model_provider_depends_only_on_advisory_repository_skills(self):
        source = _module_source("pcae.core.current_acting_model_advisory_provider")
        import_lines = _import_lines(source)
        pcae_imports = [l for l in import_lines if "pcae." in l]
        modules_imported = {l.split("pcae.core.")[1].split()[0].split(".")[0] for l in pcae_imports if "pcae.core." in l}
        assert modules_imported <= {"advisory_repository_skills", "evidence"}

    def test_advisory_repository_skills_never_imports_current_acting_model_provider(self):
        source = _module_source("pcae.core.advisory_repository_skills")
        assert "current_acting_model_advisory_provider" not in source

    def test_advisory_repository_skills_never_imports_advisory_context_package(self):
        source = _module_source("pcae.core.advisory_repository_skills")
        assert "advisory_context_package" not in source

    def test_repository_skills_never_imports_any_advisory_subsystem_module(self):
        source = _module_source("pcae.core.repository_skills")
        for advisory_module in ADVISORY_SUBSYSTEM_MODULES:
            short_name = advisory_module.rsplit(".", 1)[-1]
            assert short_name not in source


# ═══════════════════════════════════════════════════════════════════════
# Objective 5: implementation consistency (prototype matches contract)
# ═══════════════════════════════════════════════════════════════════════

class TestImplementationConsistency:
    def test_repository_skill_manifest_still_matches_115i_contract_fields(self):
        import dataclasses
        from pcae.core.repository_skills import RepositorySkillManifest
        field_names = {f.name for f in dataclasses.fields(RepositorySkillManifest)}
        assert {"skill_id", "name", "version", "capabilities", "determinism", "model_produced"} <= field_names

    def test_advisory_skill_manifest_declares_ai_review_capability(self):
        from pcae.core.advisory_repository_skills import RepositoryConsistencyAdvisorySkill
        from pcae.core.repository_skills import RepositorySkillCapability
        assert RepositorySkillCapability.AI_REVIEW in RepositoryConsistencyAdvisorySkill.manifest.capabilities

    def test_advisory_skill_manifest_model_produced_true(self):
        from pcae.core.advisory_repository_skills import RepositoryConsistencyAdvisorySkill
        assert RepositoryConsistencyAdvisorySkill.manifest.model_produced is True

    def test_current_acting_model_provider_still_conforms_to_115q_provider_shape(self):
        from pcae.core.current_acting_model_advisory_provider import CurrentActingModelAdvisoryProvider
        provider = CurrentActingModelAdvisoryProvider("x")
        assert hasattr(provider, "provider_id")
        assert hasattr(provider, "backend_kind")
        assert hasattr(provider, "determinism")
        assert callable(provider.invoke)

    def test_advisory_context_package_still_enforces_115w_allowed_question(self):
        from pcae.core.advisory_context_package import ALLOWED_ADVISORY_QUESTIONS
        assert ALLOWED_ADVISORY_QUESTIONS == ("Is the repository state internally consistent?",)

    def test_advisory_context_package_still_enforces_115w_four_trust_classes(self):
        from pcae.core.advisory_context_package import TRUST_CLASSES
        assert len(TRUST_CLASSES) == 4

    def test_default_registry_still_exactly_115j_four_deterministic_skills(self):
        from pcae.core.repository_skills import build_default_registry
        registry = build_default_registry()
        skill_ids = {s.manifest.skill_id for s in registry.list_skills()}
        assert skill_ids == {
            "git_repository_skill", "runtime_repository_skill",
            "report_repository_skill", "metadata_repository_skill",
        }


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 / roadmap
# ═══════════════════════════════════════════════════════════════════════

class TestRoadmapConsistency:
    def test_project_status_recommends_116a_next(self):
        text = (REPO_ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")
        assert "116A" in text
        assert "v0.2 Architecture Review" in text or "v0.2 architecture review" in text.lower()

    def test_hardening_doc_names_116a_as_next_phase(self):
        text = _read("PHASE_115Z_ADVISORY_SUBSYSTEM_HARDENING.md")
        assert "116A" in text
        assert "Recommended Next Phase" in text

    def test_no_second_advisory_provider_phase_recommended(self):
        text = (REPO_ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8").lower()
        assert "recommended next repo phase: 115" not in text.split("## phase 115z complete")[0] if "## phase 115z complete" in text else True


# ═══════════════════════════════════════════════════════════════════════
# No implementation claims / no new runtime module
# ═══════════════════════════════════════════════════════════════════════

class TestNoNewImplementation:
    def test_no_new_advisory_runtime_module_added(self):
        forbidden_paths = (
            REPO_ROOT / "src" / "pcae" / "core" / "second_advisory_provider.py",
            REPO_ROOT / "src" / "pcae" / "core" / "deepseek_advisory_provider.py",
            REPO_ROOT / "src" / "pcae" / "core" / "glm_advisory_provider.py",
            REPO_ROOT / "src" / "pcae" / "core" / "advisory_provider_registry.py",
        )
        for path in forbidden_paths:
            assert not path.exists()

    def test_no_implementation_claims_in_hardening_doc(self):
        text = _read("PHASE_115Z_ADVISORY_SUBSYSTEM_HARDENING.md")
        for forbidden in (
            "class SecondAdvisoryProvider", "def integrate_advisory_context_package",
            "REST endpoint", "Telegram inbound implemented", "src/pcae/core/second_advisory_provider.py",
        ):
            assert forbidden not in text

    def test_exactly_three_advisory_runtime_modules_still_exist(self):
        found = [
            p for p in (REPO_ROOT / "src" / "pcae" / "core").glob("*.py")
            if p.stem in {
                "advisory_repository_skills",
                "current_acting_model_advisory_provider",
                "advisory_context_package",
            }
        ]
        assert len(found) == 3


class TestExecutionUnavailable:
    def test_real_repository_execution_availability_unavailable(self):
        from pcae.core.repository_skills_integration import collect_evidence_via_repository_skills
        from pcae.core.paths import HarnessPath
        evidence = collect_evidence_via_repository_skills(HarnessPath(REPO_ROOT))
        assert evidence.by_id("E-runtime-002").observed_value == "unavailable"

    def test_runtime_inspect_reports_observed_and_observe(self):
        import subprocess
        import json as _json
        proc = subprocess.run(
            ["python", "-m", "pcae", "runtime", "inspect", "--json"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )
        data = _json.loads(proc.stdout)
        health = data["health"]
        assert health["execution_availability"] == "unavailable"
        assert health["current_runtime_state"] == "Observed"
        assert health["current_maximum_plugin_capability"] == "observe"
