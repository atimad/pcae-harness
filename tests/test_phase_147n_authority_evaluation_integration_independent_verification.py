"""Phase 147N — Authority Evaluation Integration Independent Implementation
Verification: an independently authored adversarial test suite against the
Phase 147M implementation of AESIC-001 v1.3.

This suite is deliberately NOT a copy or superset of
``tests/test_phase_147m_authority_evaluation_integration.py``. It targets
attack surfaces and structural invariants derived directly from AESIC-001
v1.3 and the Phase 147J architecture baseline, reconstructed independently
(Phase 147N §2's independent-reconstruction discipline), and exercises real
filesystem persistence, real concurrency, and real source inspection rather
than relying on Phase 147M's own stated conclusions.

Organized by verification area (see
docs/verification/PHASE_147N_AUTHORITY_EVALUATION_INTEGRATION_INDEPENDENT_IMPLEMENTATION_VERIFICATION.md
§4 for the full requirement-verification matrix cross-referencing these
tests).
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from pcae.authority_evaluation.errors import MalformedDeclarationError
from pcae.authority_evaluation.evaluation import evaluate
from pcae.authority_evaluation.models import (
    AuthorityEvaluationOutcome,
    EligibleAuthorityDeclaration,
    EvaluationResult,
)
from pcae.aesic import diagnostics as diag_mod
from pcae.aesic import errors as err_mod
from pcae.aesic.diagnostics import summarize_package
from pcae.aesic.errors import (
    AuthorityEvaluationRecordConflictError,
    AuthorityEvaluationRecordCorruptError,
    AuthorityEvaluationServiceRegistryCorruptError,
    AuthorityEvaluationServiceRegistryUnavailableError,
    AuthorityEvaluationStorageIdentifierError,
    CanonicalPointerCorruptError,
    CanonicalPointerUpdateFailedError,
    DecisionTemplateResolutionFailedError,
    Stage1HandoffInvalidError,
    Stage1HandoffInvalidReason,
)
from pcae.aesic.records import (
    AuthorityEvaluationRecord,
    CanonicalPointer,
    Stage1EvaluationResult,
    _compute_pointer_digest,
    aer_to_payload,
    pointer_to_payload,
)
from pcae.aesic.registry_filesystem import FilesystemAuthorityRegistry
from pcae.aesic.service import AuthorityEvaluationService
from pcae.aesic.storage import AuthorityEvaluationRecordStore
from pcae.aesic.template_store import write_template
from pcae.governance.publication.models import PublicationAuthorizationEvent
from pcae.governance.publication.record import build_publication_record
from pcae.interactive_workflow.application.session_service import SessionApplicationService
from pcae.interactive_workflow.models.session import Session, SessionState
from pcae.interactive_workflow.publication_handoff.handoff import PublicationHandoff
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.identity import generate_session_id

# NOTE: every production symbol this suite exercises is imported here, at
# module (collection) time, deliberately -- never re-imported inside a test
# function body. Phase 147H's own independent-verification suite
# (tests/test_phase_147h_authority_evaluation_independent_verification.py)
# legitimately deletes `pcae.authority_evaluation`/forbidden-root entries
# from ``sys.modules`` and reimports them to prove import-time purity; when
# both suites run in the same pytest process, a LOCAL (function-body) import
# executed after that reload would silently bind to a *different* class
# object than the one already-loaded collaborators (e.g. ``aesic.records``,
# ``aesic.storage``) hold, breaking ``isinstance``/``is`` identity checks
# for reasons unrelated to this suite's own logic. Binding everything once,
# here, avoids that cross-test interaction entirely.

_TS = "2026-01-01T00:00:00Z"
_REPO_ROOT = Path(__file__).resolve().parents[1]

# The last commit before Phase 147M began touching src/pcae/aesic/** (the
# Phase 147H close-out commit). Used to independently re-derive "the
# evaluator package is byte-for-byte unchanged" rather than trusting Phase
# 147M's own report of that fact.
_PHASE_147H_COMMIT = "f6142750"


def _outcome(
    *,
    template_ref="tpl-1",
    template_version="v1",
    claimed_identity="alice",
    result=EvaluationResult.ELIGIBLE,
    citation_text="Only Finance may approve.",
    declaration_ref="tpl-1::v1",
) -> AuthorityEvaluationOutcome:
    if result is not EvaluationResult.ELIGIBLE:
        citation_text = None
    return AuthorityEvaluationOutcome(
        template_ref=template_ref,
        template_version=template_version,
        claimed_identity=claimed_identity,
        evaluation_result=result,
        declaration_ref=declaration_ref,
        citation_text=citation_text,
        evaluated_at=_TS,
        evaluator_version="aem-evaluator/1.0",
    )


def _session(session_id=None, owner_identity="alice", template_ref="tpl-1", template_version="v1"):
    return Session(
        session_id=session_id or generate_session_id(),
        owner_identity=owner_identity,
        template_ref=template_ref,
        subject_ref="subj-1",
        session_state=SessionState.CONFIRMED,
        created_at=_TS,
        updated_at=_TS,
        template_version=template_version,
    )


def _build_service(tmp_path, eligible=("alice",), template_ref="tpl-1", template_version="v1", citation="Only Finance may approve."):
    tpl_root = tmp_path / "templates"
    reg_root = tmp_path / "registry"
    store_root = tmp_path / "records"
    write_template(template_ref, template_version, citation, root=tpl_root)
    registry = FilesystemAuthorityRegistry(root=reg_root)
    registry.write_declaration(
        EligibleAuthorityDeclaration(
            template_ref=template_ref,
            template_version=template_version,
            eligible_identities=frozenset(eligible),
            declared_at=_TS,
            declared_by="governance",
        )
    )
    store = AuthorityEvaluationRecordStore(root=store_root)
    service = AuthorityEvaluationService(registry, store, template_root=tpl_root)
    return service, store, registry


# ===========================================================================
# 1. Package and Ownership / Architectural Leakage (spec §5, §6)
# ===========================================================================


class TestArchitecturalLeakage:
    """Independently search for orchestration/import leakage across the
    package boundaries AESIC-001 §5.1 and Phase 147J establish, by parsing
    real source files with ``ast`` rather than trusting prose claims."""

    def _imports(self, path: Path) -> set:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        return names

    def test_evaluator_package_never_imports_registry_or_storage_or_aesic(self):
        pkg = _REPO_ROOT / "src" / "pcae" / "authority_evaluation"
        # evaluation.py/models.py must never import the Registry (concrete
        # or abstract) or the aesic integration package. __init__.py's own
        # re-export of registry.py is expected (it is the package's own
        # public surface, not a leakage path) so it is excluded here.
        for path in pkg.glob("*.py"):
            if path.name in ("__init__.py", "registry.py"):
                continue
            imports = self._imports(path)
            for forbidden in ("pcae.aesic", "pcae.authority_evaluation.registry"):
                assert not any(name.startswith(forbidden) for name in imports), (
                    f"{path} imports {forbidden!r}-prefixed module(s): {imports}"
                )

    def test_evaluation_module_imports_no_registry_concrete_or_abstract(self):
        path = _REPO_ROOT / "src" / "pcae" / "authority_evaluation" / "evaluation.py"
        imports = self._imports(path)
        assert not any("registry" in name for name in imports), imports

    def test_publication_coordinator_never_imports_aesic_or_evaluator(self):
        path = _REPO_ROOT / "src" / "pcae" / "governance" / "publication" / "coordinator.py"
        imports = self._imports(path)
        assert not any(name.startswith("pcae.aesic") for name in imports), imports
        assert not any(name.startswith("pcae.authority_evaluation") for name in imports), imports
        source = path.read_text(encoding="utf-8")
        assert "AuthorityEvaluationService" not in source
        assert "evaluation_result" not in source

    def test_only_session_service_in_interactive_workflow_imports_aesic(self):
        """AES orchestration must enter Interactive Workflow through exactly
        one call site (``session_service.py``); every other module in the
        package must remain unaware of ``pcae.aesic`` (AESIC-REQ-005/091)."""

        iw_root = _REPO_ROOT / "src" / "pcae" / "interactive_workflow"
        offenders = []
        for path in iw_root.rglob("*.py"):
            if path.name == "session_service.py":
                continue
            imports = self._imports(path)
            if any(name.startswith("pcae.aesic") for name in imports):
                offenders.append(str(path))
        assert offenders == [], f"Unexpected aesic import(s) outside session_service.py: {offenders}"

    def test_registry_filesystem_adapter_has_no_lifecycle_or_persistence_orchestration_symbols(self):
        path = _REPO_ROOT / "src" / "pcae" / "aesic" / "registry_filesystem.py"
        source = path.read_text(encoding="utf-8")
        for forbidden in ("evaluate_stage_1", "evaluate_stage_2", "write_record", "write_pointer", "AuthorityEvaluationRecord"):
            assert forbidden not in source, f"registry_filesystem.py unexpectedly references {forbidden!r}"

    def test_decision_template_resolution_is_aes_internal_not_a_public_export(self):
        init_path = _REPO_ROOT / "src" / "pcae" / "aesic" / "__init__.py"
        assert "DecisionTemplateResolution" not in init_path.read_text(encoding="utf-8")

    def test_evaluator_package_byte_for_byte_unchanged_since_phase_147h(self):
        """Independently re-derive Phase 147M's claim via git history rather
        than accepting the implementation report's own assertion."""

        result = subprocess.run(
            ["git", "diff", f"{_PHASE_147H_COMMIT}..HEAD", "--", "src/pcae/authority_evaluation/"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout == "", (
            "src/pcae/authority_evaluation/ has changed since the Phase 147H "
            f"commit; diff:\n{result.stdout}"
        )


# ===========================================================================
# 2. Evaluator Purity (spec §6)
# ===========================================================================


class TestEvaluatorPurity:
    def test_evaluate_is_deterministic_across_repeated_calls(self):

        decl = EligibleAuthorityDeclaration(
            template_ref="tpl-1", template_version="v1", eligible_identities=frozenset({"alice"}),
            declared_at=_TS, declared_by="governance",
        )
        results = [
            evaluate(
                template_ref="tpl-1", template_version="v1", claimed_identity="alice",
                declaration=decl, evaluated_at=_TS, evaluator_version="aem-evaluator/1.0",
                citation_text="X",
            )
            for _ in range(25)
        ]
        assert len(set(results)) == 1

    def test_evaluate_performs_no_filesystem_access(self, monkeypatch):

        def _boom(*args, **kwargs):
            raise AssertionError("evaluate() must never touch the filesystem")

        monkeypatch.setattr("builtins.open", _boom)
        decl = EligibleAuthorityDeclaration(
            template_ref="tpl-1", template_version="v1", eligible_identities=frozenset({"alice"}),
            declared_at=_TS, declared_by="governance",
        )
        outcome = evaluate(
            template_ref="tpl-1", template_version="v1", claimed_identity="alice",
            declaration=decl, evaluated_at=_TS, evaluator_version="aem-evaluator/1.0",
            citation_text="X",
        )
        assert outcome.evaluation_result is EvaluationResult.ELIGIBLE


# ===========================================================================
# 3. AES Ownership / Public Interface Closure (spec §7, §8)
# ===========================================================================


class TestAesOwnership:
    def test_aes_constructor_takes_no_ambient_global_state(self, tmp_path):
        service_a, store_a, _ = _build_service(tmp_path / "a")
        service_b, store_b, _ = _build_service(tmp_path / "b", eligible=("bob",))
        assert service_a._registry is not service_b._registry
        assert service_a._aer_store is not service_b._aer_store
        aer = service_a.evaluate_stage_2(session=_session(owner_identity="alice"), package_id="pkg-1")
        assert store_b.read_canonical("pkg-1") is None
        assert aer.outcome.evaluation_result is EvaluationResult.ELIGIBLE

    def test_evaluate_stage_2_ignores_out_of_band_stage_1_outcome_field_tampering(self, tmp_path):
        """A caller cannot smuggle a fabricated ELIGIBLE Stage 1 result past
        AES's own fresh Stage 2 evaluation: even if Stage 1 evidence is
        forged with matching session/template identity, Stage 2 always
        re-derives its own outcome from a fresh Registry lookup, never
        trusting Stage 1's embedded ``evaluation_result``."""

        service, store, _ = _build_service(tmp_path, eligible=("alice",))
        session = _session(owner_identity="mallory")  # NOT eligible
        forged_outcome = _outcome(claimed_identity="mallory", result=EvaluationResult.ELIGIBLE, citation_text="Forged.")
        forged_stage_1 = Stage1EvaluationResult(
            outcome=forged_outcome, evaluation_id="aeval-forged", session_id=session.session_id
        )
        aer = service.evaluate_stage_2(session=session, package_id="pkg-1", stage_1_result=forged_stage_1)
        # Fresh Stage 2 evaluation must disclose the TRUE result (INELIGIBLE),
        # never the forged Stage 1 ELIGIBLE claim.
        assert aer.outcome.evaluation_result is EvaluationResult.INELIGIBLE
        assert aer.outcome.citation_text is None


# ===========================================================================
# 4. Decision Template Resolution (spec §9)
# ===========================================================================


class TestDecisionTemplateResolutionAttacks:
    def test_declaration_and_citation_bound_to_one_resolved_document_not_two_independent_reads(self, tmp_path):
        """Both citation_text and the Registry lookup must key off the exact
        same (template_ref, template_version) pair the session carries --
        an attacker cannot cause citation substitution by supplying a
        session whose template identity disagrees with what was actually
        registered."""

        service, store, _ = _build_service(tmp_path, template_ref="tpl-1", template_version="v1", citation="V1 citation.")
        write_template("tpl-1", "v2", "V2 citation.", root=service._resolution._template_root)
        session_v1 = _session(template_ref="tpl-1", template_version="v1")
        aer = service.evaluate_stage_2(session=session_v1, package_id="pkg-1")
        assert aer.outcome.citation_text == "V1 citation."

    def test_malformed_template_document_rejected_not_silently_defaulted(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        tpl_root = service._resolution._template_root
        path = tpl_root / "tpl-1" / "v1.json"
        path.write_text(json.dumps({"template_ref": "tpl-1", "template_version": "v1"}))  # missing eligible_authority

        with pytest.raises(DecisionTemplateResolutionFailedError):
            service.evaluate_stage_2(session=_session(), package_id="pkg-1")

    def test_template_path_identity_mismatch_rejected(self, tmp_path):
        """A template document stored at (tpl-1, v1)'s own path but whose
        embedded identity claims a different template must fail closed,
        never silently accepted under the requested identity."""

        service, store, _ = _build_service(tmp_path)
        tpl_root = service._resolution._template_root
        path = tpl_root / "tpl-1" / "v1.json"
        payload = json.loads(path.read_text())
        payload["template_ref"] = "tpl-OTHER"
        path.write_text(json.dumps(payload))

        with pytest.raises(DecisionTemplateResolutionFailedError):
            service.evaluate_stage_2(session=_session(), package_id="pkg-1")

    def test_empty_citation_template_rejected(self, tmp_path):
        service, store, _ = _build_service(tmp_path, citation="   ")

        with pytest.raises(DecisionTemplateResolutionFailedError):
            service.evaluate_stage_2(session=_session(), package_id="pkg-1")

    def test_missing_template_version_not_silently_resolved_to_latest(self, tmp_path):
        """AESIC-REQ-036: resolution must never fall back to "latest" when
        the exact requested version is absent."""

        service, store, _ = _build_service(tmp_path, template_version="v1")
        session_v2 = _session(template_version="v2")

        with pytest.raises(DecisionTemplateResolutionFailedError):
            service.evaluate_stage_2(session=session_v2, package_id="pkg-1")


# ===========================================================================
# 5. Registry Boundary (spec §10)
# ===========================================================================


class TestRegistryAttacks:
    def test_registry_record_identity_disagreement_with_storage_path_fails_closed(self, tmp_path):
        service, store, registry = _build_service(tmp_path)
        reg_root = registry._root
        path = reg_root / "tpl-1" / "v1.json"
        payload = json.loads(path.read_text())
        payload["template_version"] = "v2"  # disagrees with its own storage path
        path.write_text(json.dumps(payload))

        with pytest.raises(AuthorityEvaluationServiceRegistryCorruptError):
            service.evaluate_stage_2(session=_session(), package_id="pkg-1")

    def test_registry_missing_directory_yields_indeterminate_not_error(self, tmp_path):
        """AESIC-REQ-044: "no Declaration" is an ordinary outcome (INDETERMINATE),
        never an unavailable/corrupt error, even when the Registry root
        directory itself has never been created."""

        tpl_root = tmp_path / "templates"
        write_template("tpl-1", "v1", "Some citation.", root=tpl_root)
        registry = FilesystemAuthorityRegistry(root=tmp_path / "never-created")
        store = AuthorityEvaluationRecordStore(root=tmp_path / "records")
        service = AuthorityEvaluationService(registry, store, template_root=tpl_root)
        aer = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        assert aer.outcome.evaluation_result is EvaluationResult.INDETERMINATE

    def test_registry_corrupt_json_raises_translated_error(self, tmp_path):
        service, store, registry = _build_service(tmp_path)
        path = registry._root / "tpl-1" / "v1.json"
        path.write_text("{not valid json")

        with pytest.raises(AuthorityEvaluationServiceRegistryCorruptError):
            service.evaluate_stage_2(session=_session(), package_id="pkg-1")

    def test_restart_equivalence_fresh_registry_instance_same_result(self, tmp_path):
        service, store, registry = _build_service(tmp_path)
        aer1 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        fresh_registry = FilesystemAuthorityRegistry(root=registry._root)
        fresh_store = AuthorityEvaluationRecordStore(root=store._root)
        fresh_service = AuthorityEvaluationService(fresh_registry, fresh_store, template_root=service._resolution._template_root)
        aer2 = fresh_service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        assert aer2.record_id == aer1.record_id  # idempotent no-op across process boundary


# ===========================================================================
# 6. Stage 1 Advisory Semantics (spec §11, §12)
# ===========================================================================


class TestStage1AdvisorySemantics:
    def test_stage_1_creates_no_aer_and_no_pointer(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        service.evaluate_stage_1(session=_session())
        assert store.list_evaluation_ids("pkg-anything") == ()
        assert store.read_pointer("pkg-anything") is None

    def test_stage_1_failure_does_not_prevent_independent_stage_2_success(self, tmp_path):
        """Registry unavailable at Stage 1 time must not become an
        unauthorized gate on Stage 2 succeeding later once the Registry is
        restored -- Stage 1 is advisory and its failure carries no
        persistent consequence."""

        service, store, registry = _build_service(tmp_path)
        import os

        reg_file = registry._root / "tpl-1" / "v1.json"
        original = reg_file.read_bytes()
        os.chmod(reg_file, 0o000)
        try:
            with pytest.raises(Exception):
                service.evaluate_stage_1(session=_session())
        finally:
            os.chmod(reg_file, 0o644)
        aer = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        assert aer.outcome.evaluation_result is EvaluationResult.ELIGIBLE

    def test_stage_1_outcome_never_becomes_effective_without_fresh_stage_2(self, tmp_path):
        """A stale Stage 1 ELIGIBLE outcome, computed before a registry
        change removed eligibility, must never itself become the effective
        citation -- only a fresh Stage 2 evaluation can."""

        service, store, registry = _build_service(tmp_path, eligible=("alice",))
        stage_1 = service.evaluate_stage_1(session=_session(owner_identity="alice", session_id="s1"))
        assert stage_1.outcome.evaluation_result is EvaluationResult.ELIGIBLE

        # Revoke eligibility between Stage 1 and Stage 2.
        registry.write_declaration(
            EligibleAuthorityDeclaration(
                template_ref="tpl-1", template_version="v1", eligible_identities=frozenset({"someone-else"}),
                declared_at=_TS, declared_by="governance",
            )
        )
        aer = service.evaluate_stage_2(
            session=_session(owner_identity="alice", session_id="s1"), package_id="pkg-1", stage_1_result=stage_1
        )
        assert aer.outcome.evaluation_result is EvaluationResult.INELIGIBLE


# ===========================================================================
# 7. Stage1EvaluationResult Attacks (spec §12)
# ===========================================================================


class TestStage1EvaluationResultAttacks:
    def test_frozen_dataclass_rejects_attribute_mutation(self, tmp_path):
        service, _, _ = _build_service(tmp_path)
        s1 = service.evaluate_stage_1(session=_session())
        with pytest.raises(Exception):
            s1.evaluation_id = "hacked"  # type: ignore[misc]

    def test_omitted_required_field_rejected_at_construction(self):
        with pytest.raises(TypeError):
            Stage1EvaluationResult(outcome=_outcome(), evaluation_id="x")  # type: ignore[call-arg]

    def test_empty_evaluation_id_rejected(self):

        with pytest.raises(MalformedDeclarationError):
            Stage1EvaluationResult(outcome=_outcome(), evaluation_id="", session_id="s1")

    def test_non_outcome_type_rejected(self):

        with pytest.raises(MalformedDeclarationError):
            Stage1EvaluationResult(outcome="not-an-outcome", evaluation_id="e1", session_id="s1")  # type: ignore[arg-type]


# ===========================================================================
# 8. Stage 2 Ordering (spec §13)
# ===========================================================================


class TestStage2Ordering:
    def test_stage_1_handoff_validation_happens_before_any_registry_or_store_access(self, tmp_path, monkeypatch):
        """AESIC-REQ-124: invalid Stage 1 handoff must fail before resolution
        or persistence is even attempted -- verified by making both the
        Registry and the store explode if touched."""

        service, store, registry = _build_service(tmp_path)

        def _boom_registry(*args, **kwargs):
            raise AssertionError("Registry must not be consulted before Stage 1 handoff validation")

        def _boom_store(*args, **kwargs):
            raise AssertionError("Store must not be written before Stage 1 handoff validation")

        monkeypatch.setattr(FilesystemAuthorityRegistry, "resolve", _boom_registry)
        monkeypatch.setattr(AuthorityEvaluationRecordStore, "write_record", _boom_store)

        bad_stage_1 = Stage1EvaluationResult(outcome=_outcome(), evaluation_id="e1", session_id="wrong-session")
        with pytest.raises(Stage1HandoffInvalidError):
            service.evaluate_stage_2(session=_session(session_id="real-session"), package_id="pkg-1", stage_1_result=bad_stage_1)

    def test_no_state_mutation_on_stage_2_validation_failure(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        bad_stage_1 = Stage1EvaluationResult(outcome=_outcome(), evaluation_id="e1", session_id="wrong-session")
        with pytest.raises(Stage1HandoffInvalidError):
            service.evaluate_stage_2(session=_session(session_id="real-session"), package_id="pkg-1", stage_1_result=bad_stage_1)
        assert store.list_evaluation_ids("pkg-1") == ()
        assert store.read_pointer("pkg-1") is None


# ===========================================================================
# 9. Idempotency Equivalence Matrix (spec §14)
# ===========================================================================


class TestIdempotencyMatrix:
    def test_fully_equivalent_retry_is_a_no_op(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        aer1 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        aer2 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        assert aer1.record_id == aer2.record_id
        assert len(store.list_evaluation_ids("pkg-1")) == 1

    def test_stage_1_absent_then_present_is_not_equivalent(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        stage_1 = service.evaluate_stage_1(session=_session(session_id="s1"))
        aer2 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1", stage_1_result=stage_1)
        assert len(store.list_evaluation_ids("pkg-1")) == 2
        assert store.read_canonical("pkg-1").record_id == aer2.record_id

    def test_stage_1_present_then_absent_is_not_equivalent(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        stage_1 = service.evaluate_stage_1(session=_session(session_id="s1"))
        service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1", stage_1_result=stage_1)
        aer2 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        assert len(store.list_evaluation_ids("pkg-1")) == 2
        assert store.read_canonical("pkg-1").record_id == aer2.record_id

    def test_changed_citation_via_template_version_bump_is_not_equivalent(self, tmp_path):
        service, store, _ = _build_service(tmp_path, template_version="v1", citation="v1 text")
        write_template("tpl-1", "v2", "v2 text", root=service._resolution._template_root)
        service._registry.write_declaration(
            EligibleAuthorityDeclaration(
                template_ref="tpl-1", template_version="v2", eligible_identities=frozenset({"alice"}),
                declared_at=_TS, declared_by="governance",
            )
        )
        service.evaluate_stage_2(session=_session(session_id="s1", template_version="v1"), package_id="pkg-1")
        aer2 = service.evaluate_stage_2(session=_session(session_id="s1", template_version="v2"), package_id="pkg-1")
        assert len(store.list_evaluation_ids("pkg-1")) == 2
        assert aer2.outcome.citation_text == "v2 text"

    def test_changed_session_identity_is_not_equivalent(self, tmp_path):
        service, store, _ = _build_service(tmp_path, eligible=("alice", "bob"))
        service.evaluate_stage_2(session=_session(session_id="s1", owner_identity="alice"), package_id="pkg-1")
        aer2 = service.evaluate_stage_2(session=_session(session_id="s2", owner_identity="bob"), package_id="pkg-1")
        assert len(store.list_evaluation_ids("pkg-1")) == 2
        assert store.read_canonical("pkg-1").record_id == aer2.record_id

    def test_evaluation_id_and_evaluated_at_excluded_from_equivalence(self, tmp_path):
        """Two separately-timed, separately-identified Stage 2 invocations
        with substantively identical inputs must still collapse to one
        canonical AER -- metadata fields must not defeat idempotency."""

        service, store, _ = _build_service(tmp_path)
        aer1 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        import time

        time.sleep(0.01)
        aer2 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        # An idempotent no-op returns the ORIGINAL canonical AER verbatim
        # (including its original evaluation_id/record_id) -- the fresh
        # evaluation_id generated internally for the second invocation's
        # own comparison is discarded, never persisted, confirming no
        # unnecessary AER growth on equivalent retry.
        assert aer1.evaluation_id == aer2.evaluation_id
        assert aer1.record_id == aer2.record_id
        assert len(store.list_evaluation_ids("pkg-1")) == 1


# ===========================================================================
# 10. Compound-Key Verification (spec §15)
# ===========================================================================


class TestCompoundKey:
    def test_same_identity_different_packages_do_not_collide(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        aer_a = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-A")
        aer_b = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-B")
        assert aer_a.record_id != aer_b.record_id
        assert store.read_canonical("pkg-A").record_id == aer_a.record_id
        assert store.read_canonical("pkg-B").record_id == aer_b.record_id

    def test_path_traversal_package_id_is_rejected(self, tmp_path):
        """147P persistence-boundary hardening: a ``package_id`` that is
        not a single valid storage path component is now REJECTED before
        any filesystem access (fail-closed), not silently sanitized into a
        different-but-safe filename. Supersedes this test's pre-147P form
        (``test_path_traversal_package_id_is_neutralized``), which asserted
        the old ``_safe_name``-based neutralization behavior; per 147P's
        explicit directive, invalid identifiers must be rejected, not
        rewritten."""
        service, store, _ = _build_service(tmp_path)
        malicious_package_id = "../../etc/pwned"
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            service.evaluate_stage_2(session=_session(), package_id=malicious_package_id)
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._record_path(malicious_package_id, "ev-1")
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store.read_canonical(malicious_package_id)


# ===========================================================================
# 11. AER Corruption Handling (spec §16)
# ===========================================================================


class TestAerCorruption:
    def test_field_changed_without_digest_update_fails_closed(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        aer = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        path = store._record_path("pkg-1", aer.evaluation_id)
        payload = json.loads(path.read_text())
        payload["outcome"]["evaluation_result"] = "ineligible"
        path.write_text(json.dumps(payload))

        with pytest.raises(AuthorityEvaluationRecordCorruptError):
            store.read_record("pkg-1", aer.evaluation_id)

    def test_truncated_record_file_fails_closed(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        aer = service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        path = store._record_path("pkg-1", aer.evaluation_id)
        raw = path.read_text()
        path.write_text(raw[: len(raw) // 2])

        with pytest.raises(AuthorityEvaluationRecordCorruptError):
            store.read_record("pkg-1", aer.evaluation_id)

    def test_conflicting_duplicate_write_rejected(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        record = AuthorityEvaluationRecord(
            record_id="aer-1", package_id="pkg-1", evaluation_id="ev-1", outcome=_outcome(), evaluated_at=_TS,
        )
        store.write_record(record)
        conflicting = AuthorityEvaluationRecord(
            record_id="aer-2", package_id="pkg-1", evaluation_id="ev-1",  # same compound key
            outcome=_outcome(claimed_identity="mallory", result=EvaluationResult.INDETERMINATE, citation_text=None, declaration_ref=None),
            evaluated_at=_TS,
        )

        with pytest.raises(AuthorityEvaluationRecordConflictError):
            store.write_record(conflicting)

    def test_identical_duplicate_write_is_a_safe_no_op(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        record = AuthorityEvaluationRecord(
            record_id="aer-1", package_id="pkg-1", evaluation_id="ev-1", outcome=_outcome(), evaluated_at=_TS,
        )
        store.write_record(record)
        store.write_record(record)  # must not raise
        assert store.read_record("pkg-1", "ev-1").record_id == "aer-1"


# ===========================================================================
# 12. Canonical Pointer Integrity — INCLUDING a cross-key relocation gap
# ===========================================================================


class TestCanonicalPointerIntegrity:
    def test_pointer_digest_tamper_detected(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        path = store._pointer_path("pkg-1")
        payload = json.loads(path.read_text())
        payload["pointer_digest"] = "0" * 64
        path.write_text(json.dumps(payload))
        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-1")

    def test_pointer_referencing_missing_aer_detected(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        path = store._pointer_path("pkg-1")
        payload = json.loads(path.read_text())
        payload["evaluation_id"] = "nonexistent-eval-id"
        # Recompute a *valid* pointer_digest over the tampered content so the
        # digest check alone doesn't catch it -- isolating the "missing AER"
        # check specifically.

        content = {k: payload[k] for k in ("package_id", "evaluation_id", "record_id", "record_digest", "schema_version")}
        payload["pointer_digest"] = _compute_pointer_digest(content)
        path.write_text(json.dumps(payload))
        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-1")

    def test_CROSS_KEY_RELOCATION_pointer_content_disagreeing_with_query_key_now_rejected(self, tmp_path):
        """AESIC-N-01, CLOSED by Phase 147P: AESIC-001 v1.3 §18 requires
        "wrong compound key" pointer substitution to be rejected -- a
        corrupted pointer must never silently resolve. This test
        independently reproduces the exact pre-147P attack (see this
        test's pre-147P form,
        ``test_CROSS_KEY_RELOCATION_pointer_content_disagrees_with_query_key_not_rejected``,
        which demonstrated the store returning package A's AER for a
        package B query with no exception) and confirms ``read_canonical``
        now enforces that the *requested* storage key (the pointer file's
        own location) is authoritative over the pointer content's own
        embedded ``package_id`` -- fail-closed, ``CanonicalPointerCorruptError``,
        no fallback lookup under the embedded key. This is reproducible via
        ordinary filesystem access to the pointer store; it is not
        reachable through AES's own normal ``evaluate_stage_2`` write path
        (which always constructs pointer.package_id == the argument it was
        given), so it remains a defense-in-depth / fail-closed read-path
        guarantee, not a live exploit through the public AES API.
        """

        service, store, _ = _build_service(tmp_path)
        aer_a = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-A")

        # Legitimate, self-consistent pointer content for pkg-A, digest valid.
        legit_payload = pointer_to_payload(
            CanonicalPointer(
                package_id="pkg-A",
                evaluation_id=aer_a.evaluation_id,
                record_id=aer_a.record_id,
                record_digest=aer_to_payload(aer_a)["record_digest"],
            )
        )
        # Relocate this VALID pointer payload to package B's own pointer path.
        forged_path = store._pointer_path("pkg-B")
        forged_path.parent.mkdir(parents=True, exist_ok=True)
        forged_path.write_text(json.dumps(legit_payload, indent=2, sort_keys=True))

        # Before 147P: silently returned pkg-A's AER for a pkg-B query.
        # After 147P: the requested key ("pkg-B") disagrees with the
        # pointer's own embedded key ("pkg-A") -- fail closed.
        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-B")

        # The legitimate, same-key read is unaffected.
        assert store.read_canonical("pkg-A").record_id == aer_a.record_id


# ===========================================================================
# 13. Supersession — multi-generation (spec §19)
# ===========================================================================


class TestSupersessionMultiGeneration:
    def test_three_generation_history_retained_and_pointer_advances_each_time(self, tmp_path):
        service, store, registry = _build_service(tmp_path, eligible=("alice",))
        gen1 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        assert gen1.outcome.evaluation_result is EvaluationResult.ELIGIBLE

        registry.write_declaration(
            EligibleAuthorityDeclaration(
                template_ref="tpl-1", template_version="v1", eligible_identities=frozenset({"someone-else"}),
                declared_at=_TS, declared_by="governance",
            )
        )
        gen2 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        assert gen2.outcome.evaluation_result is EvaluationResult.INELIGIBLE
        assert gen2.record_id != gen1.record_id

        registry.write_declaration(
            EligibleAuthorityDeclaration(
                template_ref="tpl-1", template_version="v1", eligible_identities=frozenset({"alice"}),
                declared_at=_TS, declared_by="governance",
            )
        )
        gen3 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        assert gen3.outcome.evaluation_result is EvaluationResult.ELIGIBLE
        # gen3's content matches gen1's content exactly, but it is compared
        # only against the *current* AER (gen2), so a genuinely new,
        # distinct record is created rather than "restoring" gen1.
        assert gen3.record_id not in (gen1.record_id, gen2.record_id)

        assert len(store.list_evaluation_ids("pkg-1")) == 3
        assert store.read_canonical("pkg-1").record_id == gen3.record_id
        # All three generations remain individually retrievable (audit trail).
        for gen in (gen1, gen2, gen3):
            assert store.read_record("pkg-1", gen.evaluation_id) is not None

    def test_older_generation_retry_cannot_roll_back_the_pointer(self, tmp_path):
        service, store, registry = _build_service(tmp_path, eligible=("alice",))
        service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        registry.write_declaration(
            EligibleAuthorityDeclaration(
                template_ref="tpl-1", template_version="v1", eligible_identities=frozenset({"someone-else"}),
                declared_at=_TS, declared_by="governance",
            )
        )
        gen2 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        assert store.read_canonical("pkg-1").record_id == gen2.record_id
        # Restore eligibility to match gen1's original content and retry --
        # must move FORWARD to a new record, never revive gen1 as canonical.
        registry.write_declaration(
            EligibleAuthorityDeclaration(
                template_ref="tpl-1", template_version="v1", eligible_identities=frozenset({"alice"}),
                declared_at=_TS, declared_by="governance",
            )
        )
        gen3 = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        assert store.read_canonical("pkg-1").record_id == gen3.record_id
        assert gen3.record_id != gen2.record_id


# ===========================================================================
# 14. Post-AER / Pre-Pointer Crash Recovery — real filesystem (spec §20)
# ===========================================================================


class TestCrashRecovery:
    def test_recovery_creates_a_second_distinct_aer_rather_than_rediscovering_the_orphan(self, tmp_path, monkeypatch):
        """FINDING (see verification doc, AESIC-N-02, Informational): Because
        ``evaluation_id`` is a fresh UUID per invocation and idempotency
        dedup is keyed against the *canonical pointer* (not a compound-key
        history scan), a retry after a post-AER/pre-pointer crash does not
        "rediscover" and reuse the orphaned, already-committed AER --  it
        always produces a second, content-equivalent AER and a fresh
        pointer. The final state is still correct (exactly one valid
        current-effective pointer, no data loss, orphan remains durably
        auditable) but this diverges from a literal reading of "committed
        AER is rediscovered" in Phase 147N's own spec text. Documented as
        Informational: the eventual state is correct; the mechanism is
        additive-history rather than rediscovery."""

        service, store, _ = _build_service(tmp_path)

        def _boom(self, pointer):
            raise OSError("simulated pointer write failure")

        monkeypatch.setattr(AuthorityEvaluationRecordStore, "write_pointer", _boom)
        with pytest.raises(CanonicalPointerUpdateFailedError):
            service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        monkeypatch.undo()

        assert store.read_canonical("pkg-1") is None
        orphan_ids = store.list_evaluation_ids("pkg-1")
        assert len(orphan_ids) == 1

        # Fresh service instance, simulating a full process restart.
        fresh_store = AuthorityEvaluationRecordStore(root=store._root)
        fresh_service = AuthorityEvaluationService(service._registry, fresh_store, template_root=service._resolution._template_root)
        recovered = fresh_service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")

        assert fresh_store.read_canonical("pkg-1").record_id == recovered.record_id
        all_ids = fresh_store.list_evaluation_ids("pkg-1")
        assert len(all_ids) == 2  # orphan + recovered, both durable
        assert recovered.evaluation_id in all_ids
        # The pre-crash orphan is still readable and content-equivalent.
        orphan = fresh_store.read_record("pkg-1", orphan_ids[0])
        assert orphan.outcome.evaluation_result == recovered.outcome.evaluation_result

    def test_repeated_recovery_attempts_are_each_individually_idempotent_once_pointer_exists(self, tmp_path, monkeypatch):
        service, store, _ = _build_service(tmp_path)

        def _boom(self, pointer):
            raise OSError("simulated pointer write failure")

        monkeypatch.setattr(AuthorityEvaluationRecordStore, "write_pointer", _boom)
        with pytest.raises(CanonicalPointerUpdateFailedError):
            service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        monkeypatch.undo()

        recovered = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        again = service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1")
        assert again.record_id == recovered.record_id
        assert len(store.list_evaluation_ids("pkg-1")) == 2  # no further growth


# ===========================================================================
# 15. Concurrency (spec §22) — real threads, real filesystem
# ===========================================================================


class TestConcurrency:
    def test_concurrent_equivalent_invocations_converge_to_one_valid_current_effective_pointer(self, tmp_path):
        service, store, _ = _build_service(tmp_path)
        results = []
        errors = []

        def worker():
            try:
                results.append(service.evaluate_stage_2(session=_session(session_id="s1"), package_id="pkg-1"))
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], errors
        assert len(results) == 8
        # The canonical pointer must resolve to a record that IS one of the
        # AERs actually produced (no corruption, no dangling reference),
        # even though disclosed last-write-wins concurrency (AESIC-REQ-120)
        # means it is not necessarily any specific one of them.
        canonical = store.read_canonical("pkg-1")
        assert canonical is not None
        produced_ids = {r.record_id for r in results}
        assert canonical.record_id in produced_ids
        # All content is substantively equivalent (same evaluation inputs).
        assert all(r.outcome.evaluation_result is EvaluationResult.ELIGIBLE for r in results)

    def test_concurrent_distinct_supersessions_leave_exactly_one_valid_pointer(self, tmp_path):
        """Two threads race to supersede with genuinely DIFFERENT content
        (different claimed identities via different sessions) -- verify no
        partial/corrupt pointer state results, whichever wins."""

        service, store, _ = _build_service(tmp_path, eligible=("alice", "bob"))
        results = []
        errors = []

        def worker(identity):
            try:
                results.append(
                    service.evaluate_stage_2(
                        session=_session(session_id="s1", owner_identity=identity), package_id="pkg-1"
                    )
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(identity,)) for identity in ("alice", "bob") for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], errors
        canonical = store.read_canonical("pkg-1")
        assert canonical is not None  # never corrupt/unreadable
        produced_ids = {r.record_id for r in results}
        assert canonical.record_id in produced_ids


# ===========================================================================
# 16. Disclosure-Only / Non-Gating (spec §28)
# ===========================================================================


class TestNonGating:
    def test_ineligible_stage_2_outcome_does_not_prevent_readiness_package_construction(self, tmp_path):

        service, store, _ = _build_service(tmp_path, eligible=("someone-else",))
        session = _session(owner_identity="alice")
        aer = service.evaluate_stage_2(session=session, package_id="pkg-1")
        assert aer.outcome.evaluation_result is EvaluationResult.INELIGIBLE

        # An INELIGIBLE (or INDETERMINATE) outcome must never itself raise
        # or block -- it is disclosure-only. Verify no exception occurs
        # when building a package without a citation (contract: absent
        # authority_evaluation_ref/citation_text is the ordinary, non-error
        # case per AESIC-REQ-058).
        pkg = PublicationReadinessPackage(
            package_id="prp-1", session_id=session.session_id, session_state=session.session_state,
            transition_sequence_number=0, evidence_refs=(), clarification_refs=(), audit_refs=(),
            preview_id="prev-1", preview_digest="d" * 64, confirmation_request_id="req-1",
            confirmation_response_id="resp-1", built_at=_TS,
            authority_evaluation_ref=None, citation_text=None,
        )
        assert pkg.authority_evaluation_ref is None

    def test_evaluation_result_enum_never_imported_by_publication_coordinator_for_branching(self):
        path = _REPO_ROOT / "src" / "pcae" / "governance" / "publication" / "coordinator.py"
        source = path.read_text(encoding="utf-8")
        assert "EvaluationResult" not in source
        assert "AuthorityEvaluation" not in source


# ===========================================================================
# 17. CHGR Citation-Only Integration (spec §27)
# ===========================================================================


class TestChgrCitationOnlyBoundary:
    def test_only_citation_text_flows_into_authority_basis_claimed_not_full_aer(self, tmp_path):

        service, store, _ = _build_service(tmp_path)
        session = _session(owner_identity="alice")
        aer = service.evaluate_stage_2(session=session, package_id="pkg-1")
        assert aer.outcome.evaluation_result is EvaluationResult.ELIGIBLE

        pkg = PublicationReadinessPackage(
            package_id="pkg-1", session_id=session.session_id, session_state=session.session_state,
            transition_sequence_number=0, evidence_refs=(), clarification_refs=(), audit_refs=(),
            preview_id="prev-1", preview_digest="d" * 64, confirmation_request_id="req-1",
            confirmation_response_id="resp-1", built_at=_TS,
            decision_subject="subj-1", template_id="tpl-1", template_version="1.0",
            selected_option_id="approve", options_presented=("approve", "reject"),
            decision_maker_identity_evidence={"evidence_kind": "typed_confirmation_only", "identifier": "alice", "captured_at": _TS},
            preview_rendered_content="Rendered preview.", confirmation_statement="confirmed",
            confirmation_timestamp=_TS,
            authority_evaluation_ref={
                "record_id": aer.record_id,
                "record_digest": aer_to_payload(aer)["record_digest"],
                "record_family": aer.record_family,
            },
            citation_text=aer.outcome.citation_text,
        )
        event = PublicationAuthorizationEvent(
            event_id="evt-1", operator_id="alice", package_id="pkg-1", invoked_at=_TS,
        )
        bundle = build_publication_record(pkg, event, "chgr-00000001", _TS)
        hgr = bundle["human_governance_record"]
        assert hgr.get("authority_basis_claimed") == aer.outcome.citation_text
        # The full AER, its record_id, and its evaluation_result must NEVER
        # appear inline inside the CHGR body.
        serialized = json.dumps(hgr)
        assert aer.record_id not in serialized
        assert "evaluation_result" not in serialized
        assert "eligible" not in serialized.lower() or "eligible" not in json.dumps(hgr.get("authority_basis_claimed", "")).lower()

    def test_absent_authority_evaluation_leaves_disclosed_limitation_not_silent_omission(self, tmp_path):

        session = _session(owner_identity="alice")
        pkg = PublicationReadinessPackage(
            package_id="pkg-1", session_id=session.session_id, session_state=session.session_state,
            transition_sequence_number=0, evidence_refs=(), clarification_refs=(), audit_refs=(),
            preview_id="prev-1", preview_digest="d" * 64, confirmation_request_id="req-1",
            confirmation_response_id="resp-1", built_at=_TS,
            decision_subject="subj-1", template_id="tpl-1", template_version="1.0",
            selected_option_id="approve", options_presented=("approve", "reject"),
            decision_maker_identity_evidence={"evidence_kind": "typed_confirmation_only", "identifier": "alice", "captured_at": _TS},
            preview_rendered_content="Rendered preview.", confirmation_statement="confirmed",
            confirmation_timestamp=_TS,
            authority_evaluation_ref=None, citation_text=None,
        )
        event = PublicationAuthorizationEvent(
            event_id="evt-1", operator_id="alice", package_id="pkg-1", invoked_at=_TS,
        )
        bundle = build_publication_record(pkg, event, "chgr-00000001", _TS)
        hgr = bundle["human_governance_record"]
        assert "authority_basis_claimed" not in hgr
        assert any("authority_basis_claimed" in lim for lim in hgr.get("limitations", []))


# ===========================================================================
# 18. Readiness Package Construction (spec §21, §25)
# ===========================================================================


class TestReadinessPackageConstraints:
    def test_citation_text_required_whenever_authority_evaluation_ref_present(self):

        with pytest.raises(ValueError):
            PublicationReadinessPackage(
                package_id="pkg-1", session_id=generate_session_id(), session_state=SessionState.CONFIRMED,
                transition_sequence_number=0, evidence_refs=(), clarification_refs=(), audit_refs=(),
                preview_id="prev-1", preview_digest="d" * 64, confirmation_request_id="req-1",
                confirmation_response_id="resp-1", built_at=_TS,
                authority_evaluation_ref={"record_id": "r1", "record_digest": "d1", "record_family": "authority_evaluation_record"},
                citation_text=None,  # missing despite ref present
            )

    def test_citation_text_forbidden_when_ref_absent(self):

        with pytest.raises(ValueError):
            PublicationReadinessPackage(
                package_id="pkg-1", session_id=generate_session_id(), session_state=SessionState.CONFIRMED,
                transition_sequence_number=0, evidence_refs=(), clarification_refs=(), audit_refs=(),
                preview_id="prev-1", preview_digest="d" * 64, confirmation_request_id="req-1",
                confirmation_response_id="resp-1", built_at=_TS,
                authority_evaluation_ref=None,
                citation_text="orphan citation with no ref",
            )

    def test_incomplete_authority_evaluation_ref_rejected(self):

        with pytest.raises(ValueError):
            PublicationReadinessPackage(
                package_id="pkg-1", session_id=generate_session_id(), session_state=SessionState.CONFIRMED,
                transition_sequence_number=0, evidence_refs=(), clarification_refs=(), audit_refs=(),
                preview_id="prev-1", preview_digest="d" * 64, confirmation_request_id="req-1",
                confirmation_response_id="resp-1", built_at=_TS,
                authority_evaluation_ref={"record_id": "r1"},  # missing record_digest/record_family
                citation_text="text",
            )


# ===========================================================================
# 19. Interactive Workflow Integration Surface (spec §24)
# ===========================================================================


class TestWorkflowIntegrationSurface:
    def test_session_service_defaults_to_none_service_preserving_legacy_behavior(self):
        import inspect


        sig = inspect.signature(SessionApplicationService.__init__)
        assert sig.parameters["authority_evaluation_service"].default is None

    def test_evaluate_authority_stage_1_returns_none_without_configured_service(self, tmp_path, monkeypatch):

        # Construct with a None collaborator (legacy path) and verify no
        # AttributeError / no accidental Registry access is attempted.
        svc = object.__new__(SessionApplicationService)
        svc._authority_evaluation_service = None
        result = SessionApplicationService.evaluate_authority_stage_1(svc, "nonexistent-session-id")
        assert result is None


# ===========================================================================
# 20. Error Taxonomy Distinctness (spec §21 phase spec section)
# ===========================================================================


class TestErrorTaxonomyDistinctness:
    def test_all_integration_errors_share_one_common_base_and_are_mutually_distinct_types(self):

        base = err_mod.AuthorityEvaluationIntegrationError
        names = [
            "AuthorityEvaluationServiceRegistryUnavailableError",
            "AuthorityEvaluationServiceRegistryCorruptError",
            "DecisionTemplateNotFoundError",
            "DecisionTemplateMalformedError",
            "DecisionTemplateCitationEmptyError",
            "DecisionTemplateResolutionFailedError",
            "Stage1HandoffInvalidError",
            "CanonicalPointerCorruptError",
            "CanonicalPointerUpdateFailedError",
            "AuthorityEvaluationRecordConflictError",
            "AuthorityEvaluationRecordCorruptError",
            "AuthorityEvaluationSerializationError",
        ]
        classes = [getattr(err_mod, n) for n in names]
        assert len(set(classes)) == len(classes)  # all distinct
        for cls in classes:
            assert issubclass(cls, base)
        # No two are subclasses of each other (a flat, non-collapsing taxonomy).
        for i, a in enumerate(classes):
            for b in classes[i + 1:]:
                assert not issubclass(a, b) and not issubclass(b, a), (a, b)

    def test_stage1_handoff_invalid_reason_is_a_closed_four_member_enum(self):
        assert {m.value for m in Stage1HandoffInvalidReason} == {
            "malformed", "session_mismatch", "identity_mismatch", "template_mismatch",
        }

    def test_broad_except_does_not_collapse_registry_unavailable_into_corrupt(self, tmp_path):
        from pcae.aesic.errors import (
            AuthorityEvaluationServiceRegistryCorruptError,
            AuthorityEvaluationServiceRegistryUnavailableError,
        )

        service, store, registry = _build_service(tmp_path)
        import os

        reg_file = registry._root / "tpl-1" / "v1.json"
        os.chmod(reg_file, 0o000)
        try:
            with pytest.raises(AuthorityEvaluationServiceRegistryUnavailableError) as exc_info:
                service.evaluate_stage_2(session=_session(), package_id="pkg-1")
            assert not isinstance(exc_info.value, AuthorityEvaluationServiceRegistryCorruptError)
        finally:
            os.chmod(reg_file, 0o644)


# ===========================================================================
# 21. Diagnostics (read-only, non-control-surface) (spec §30)
# ===========================================================================


class TestDiagnosticsAreReadOnlyAndNeverGate:
    def test_summarize_package_never_raises_on_corrupt_pointer(self, tmp_path):

        service, store, _ = _build_service(tmp_path)
        service.evaluate_stage_2(session=_session(), package_id="pkg-1")
        path = store._pointer_path("pkg-1")
        payload = json.loads(path.read_text())
        payload["pointer_digest"] = "0" * 64
        path.write_text(json.dumps(payload))

        summary = summarize_package(store, "pkg-1")
        assert summary.canonical_pointer_ok is False
        assert summary.canonical_record_id is None

    def test_diagnostics_module_exposes_no_mutation_functions(self):

        for name in dir(diag_mod):
            if name.startswith("_"):
                continue
            obj = getattr(diag_mod, name)
            if callable(obj) and not isinstance(obj, type):
                assert not any(kw in name for kw in ("write", "delete", "persist", "create", "evaluate"))
