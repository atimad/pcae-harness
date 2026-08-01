"""Phase 147O.1 unit tests: Authority Evaluation Service production
wiring (AESIC-001 v1.3, closes AESIC-O-01).

Covers: the composition root's enablement decision
(``pcae.aesic.composition``), Stage 1 reachability through
``decision-session confirm``, Stage 2 reachability through
``decision-session readiness``, real AER/canonical-pointer persistence,
CHGR citation-only wiring through ``governance-record publish``,
backward compatibility (legacy packages, unconfigured repositories),
non-gating semantics, failure semantics, the new ``pcae aesic status``
diagnostics surface, and continued AESIC-N-01 non-reachability through
this phase's new production callers.
"""

from __future__ import annotations

import ast
import io
import json
from pathlib import Path

import pytest

from pcae.aesic.composition import (
    build_authority_evaluation_service,
    describe_authority_evaluation_configuration,
)
from pcae.aesic.registry_filesystem import FilesystemAuthorityRegistry
from pcae.aesic.storage import AuthorityEvaluationRecordStore
from pcae.aesic.template_store import write_template
from pcae.authority_evaluation.models import EligibleAuthorityDeclaration
from pcae.commands.aesic_status import run_aesic_status
from pcae.commands.decision_session import (
    EXIT_SUCCESS,
    build_application_context,
    run_decision_session_confirm,
    run_decision_session_create,
    run_decision_session_evidence,
    run_decision_session_preview,
    run_decision_session_readiness,
    run_decision_session_select,
)
from pcae.commands.governance_record import run_governance_record_publish
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.serialization.publication_handoff_schema import (
    from_payload as package_from_payload,
    to_payload as package_to_payload,
)


class _Args:
    def __init__(self, **kwargs):
        self.json = True
        self.rationale = None
        self.conditions = None
        self.as_identity = "alice"
        for key, value in kwargs.items():
            setattr(self, key, value)


def _run(handler, **kwargs):
    args = _Args(**kwargs)
    buf = io.StringIO()
    from contextlib import redirect_stdout

    with redirect_stdout(buf):
        exit_code = handler(args)
    return exit_code, json.loads(buf.getvalue())


@pytest.fixture(autouse=True)
def _isolated_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield tmp_path


def _deploy_template(template_ref="demo-template", template_version="1.0", eligible_authority="Approved."):
    write_template(template_ref, template_version, eligible_authority)


def _declare_eligible(identities, template_ref="demo-template", template_version="1.0"):
    registry = FilesystemAuthorityRegistry()
    registry.write_declaration(
        EligibleAuthorityDeclaration(
            template_ref=template_ref,
            template_version=template_version,
            eligible_identities=frozenset(identities),
            declared_at="2026-01-01T00:00:00.000000Z",
            declared_by="test-operator",
        )
    )


def _create_session(owner_id="alice", template_ref="demo-template"):
    exit_code, payload = _run(
        run_decision_session_create, template_ref=template_ref, subject_ref="subj-1", owner_id=owner_id
    )
    assert exit_code == EXIT_SUCCESS
    return payload["session"]["session_id"]


def _confirmed(owner_id="alice", template_ref="demo-template", template_version="1.0"):
    session_id = _create_session(owner_id, template_ref)
    exit_code, _ = _run(
        run_decision_session_evidence, session_id=session_id, declare=["ev-1"], as_identity=owner_id
    )
    assert exit_code == EXIT_SUCCESS
    exit_code, _ = _run(
        run_decision_session_select,
        session_id=session_id,
        option_id="opt-a",
        options_presented=["opt-a", "opt-b"],
        template_version=template_version,
        as_identity=owner_id,
    )
    assert exit_code == EXIT_SUCCESS
    exit_code, preview_payload = _run(run_decision_session_preview, session_id=session_id, as_identity=owner_id)
    assert exit_code == EXIT_SUCCESS
    exit_code, confirm_payload = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=preview_payload["preview_digest"],
        statement="confirmed",
        as_identity=owner_id,
    )
    assert exit_code == EXIT_SUCCESS
    return session_id, confirm_payload


# --- Composition / enablement -----------------------------------------------


class TestComposition:
    def test_disabled_when_template_root_absent(self):
        status = describe_authority_evaluation_configuration()
        assert status.enabled is False
        assert status.reason == "template_root_absent"
        assert build_authority_evaluation_service() is None

    def test_disabled_when_template_root_empty(self, tmp_path):
        Path(".pcae/authority-evaluation/templates").mkdir(parents=True)
        status = describe_authority_evaluation_configuration()
        assert status.enabled is False
        assert status.reason == "template_root_empty"
        assert build_authority_evaluation_service() is None

    def test_disabled_when_template_root_not_a_directory(self):
        Path(".pcae/authority-evaluation").mkdir(parents=True)
        Path(".pcae/authority-evaluation/templates").write_text("not a directory", encoding="utf-8")
        status = describe_authority_evaluation_configuration()
        assert status.enabled is False
        assert status.reason == "template_root_not_a_directory"
        assert build_authority_evaluation_service() is None

    def test_enabled_when_template_deployed(self):
        _deploy_template()
        status = describe_authority_evaluation_configuration()
        assert status.enabled is True
        assert status.reason == "template_root_populated"
        service = build_authority_evaluation_service()
        assert service is not None

    def test_composition_is_deterministic_and_uncached(self):
        assert build_authority_evaluation_service() is None
        _deploy_template()
        # A second, independent call re-derives from current filesystem
        # state -- no cached "disabled" decision from the first call.
        assert build_authority_evaluation_service() is not None

    def test_composition_root_reused_not_a_second_container(self):
        ctx = build_application_context()
        assert ctx.session_service is not None


# --- Production reachability --------------------------------------------------


class TestProductionReachability:
    def test_stage_1_unreachable_without_configuration(self):
        _, confirm_payload = _confirmed()
        assert confirm_payload["authority_evaluation_stage_1"] == "not_configured"

    def test_stage_1_reachable_through_confirm(self):
        _deploy_template()
        _, confirm_payload = _confirmed()
        # No Registry declaration -> declaration is None -> indeterminate,
        # never an error; still proves Stage 1 actually ran.
        assert confirm_payload["authority_evaluation_stage_1"] == "indeterminate"

    def test_stage_1_eligible_end_to_end(self):
        _deploy_template()
        _declare_eligible({"alice"})
        _, confirm_payload = _confirmed()
        assert confirm_payload["authority_evaluation_stage_1"] == "eligible"

    def test_stage_2_reachable_and_aer_persisted(self):
        _deploy_template()
        _declare_eligible({"alice"})
        session_id, _ = _confirmed()
        exit_code, readiness_payload = _run(
            run_decision_session_readiness, session_id=session_id, as_identity="alice"
        )
        assert exit_code == EXIT_SUCCESS
        package_id = readiness_payload["package_id"]

        store = AuthorityEvaluationRecordStore()
        record = store.read_canonical(package_id)
        assert record is not None
        assert record.outcome.evaluation_result.value == "eligible"
        assert record.outcome.citation_text == "Approved."

    def test_chgr_receives_current_effective_citation(self):
        _deploy_template()
        _declare_eligible({"alice"})
        session_id, _ = _confirmed()
        exit_code, readiness_payload = _run(
            run_decision_session_readiness, session_id=session_id, as_identity="alice"
        )
        assert exit_code == EXIT_SUCCESS
        package_id = readiness_payload["package_id"]

        exit_code, publish_payload = _run(
            run_governance_record_publish, package_id=package_id, operator_id="alice"
        )
        assert exit_code == EXIT_SUCCESS
        assert publish_payload["success"] is True
        record_id = publish_payload["record_id"]
        chgr_path = Path(".pcae/publication-execution/records") / f"{record_id}.json"
        chgr = json.loads(chgr_path.read_text(encoding="utf-8"))
        assert chgr["authority_basis_claimed"] == "Approved."

    def test_publication_coordinator_never_touches_aesic(self):
        import pcae.governance.publication.coordinator as coordinator_module

        source = Path(coordinator_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "aesic" not in node.module
                assert "authority_evaluation" not in node.module
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "aesic" not in alias.name
                    assert "authority_evaluation" not in alias.name


# --- Backward compatibility ---------------------------------------------------


class TestBackwardCompatibility:
    def test_publish_succeeds_without_authority_evaluation_configured(self):
        session_id, _ = _confirmed()
        exit_code, readiness_payload = _run(
            run_decision_session_readiness, session_id=session_id, as_identity="alice"
        )
        assert exit_code == EXIT_SUCCESS
        package_id = readiness_payload["package_id"]
        exit_code, publish_payload = _run(
            run_governance_record_publish, package_id=package_id, operator_id="alice"
        )
        assert exit_code == EXIT_SUCCESS
        assert publish_payload["success"] is True
        record_id = publish_payload["record_id"]
        chgr_path = Path(".pcae/publication-execution/records") / f"{record_id}.json"
        chgr = json.loads(chgr_path.read_text(encoding="utf-8"))
        assert "authority_basis_claimed" not in chgr or chgr.get("authority_basis_claimed") is None

    def test_legacy_payload_shape_unaffected_by_new_optional_fields(self):
        """A package carrying no Authority Evaluation data serializes to
        the exact same payload shape as before Phase 147O.1 -- no new
        keys appear, so a pre-existing on-disk digest still verifies."""

        package = PublicationReadinessPackage(
            package_id="prp-legacy",
            session_id="CDS-11111111-1111-4111-8111-111111111111",
            session_state=SessionState.CONFIRMED,
            transition_sequence_number=1,
            evidence_refs=("ev-1",),
            clarification_refs=(),
            audit_refs=(),
            preview_id="prev-1",
            preview_digest="digest-1",
            confirmation_request_id="cnf-req-1",
            confirmation_response_id="cnf-res-1",
            built_at="2026-01-01T00:00:00.000000Z",
        )
        payload = package_to_payload(package)
        assert "authority_evaluation_ref" not in payload
        assert "citation_text" not in payload

    def test_legacy_stored_payload_deserializes_with_none_evaluation_fields(self):
        legacy_payload = {
            "schema_version": "interactive-workflow-publication-handoff/0.1",
            "package_id": "prp-legacy",
            "session_id": "CDS-11111111-1111-4111-8111-111111111111",
            "session_state": "Confirmed",
            "transition_sequence_number": 1,
            "evidence_refs": ["ev-1"],
            "clarification_refs": [],
            "audit_refs": [],
            "preview_id": "prev-1",
            "preview_digest": "digest-1",
            "confirmation_request_id": "cnf-req-1",
            "confirmation_response_id": "cnf-res-1",
            "built_at": "2026-01-01T00:00:00.000000Z",
        }
        package = package_from_payload(legacy_payload)
        assert package.authority_evaluation_ref is None
        assert package.citation_text is None

    def test_round_trip_payload_idempotent_for_legacy_shaped_package(self):
        """A payload produced by ``to_payload`` for a package with no
        Authority Evaluation data round-trips through ``from_payload``
        back to the exact same payload -- the regression this guards:
        before the fix, ``from_payload`` always set
        ``authority_evaluation_ref``/``citation_text`` to ``None`` on
        the reconstructed package, but ``to_payload`` unconditionally
        re-emitted them as new keys, so a second round-trip produced a
        payload (and therefore a digest) that disagreed with the first
        -- silently breaking every pre-existing on-disk record on next
        read."""

        package = PublicationReadinessPackage(
            package_id="prp-legacy",
            session_id="CDS-11111111-1111-4111-8111-111111111111",
            session_state=SessionState.CONFIRMED,
            transition_sequence_number=1,
            evidence_refs=(),
            clarification_refs=(),
            audit_refs=(),
            preview_id="prev-1",
            preview_digest="digest-1",
            confirmation_request_id="cnf-req-1",
            confirmation_response_id="cnf-res-1",
            built_at="2026-01-01T00:00:00.000000Z",
        )
        first_payload = package_to_payload(package)
        second_payload = package_to_payload(package_from_payload(first_payload))
        assert first_payload == second_payload


# --- Non-gating semantics ------------------------------------------------------


class TestNonGating:
    def test_indeterminate_stage_1_does_not_block_confirmation(self):
        _deploy_template()
        session_id, confirm_payload = _confirmed()
        assert confirm_payload["session"]["session_state"] == "Confirmed"
        assert confirm_payload["authority_evaluation_stage_1"] == "indeterminate"

    def test_indeterminate_stage_2_does_not_block_readiness_or_publication(self):
        _deploy_template()
        session_id, _ = _confirmed()
        exit_code, readiness_payload = _run(
            run_decision_session_readiness, session_id=session_id, as_identity="alice"
        )
        assert exit_code == EXIT_SUCCESS
        package_id = readiness_payload["package_id"]
        exit_code, publish_payload = _run(
            run_governance_record_publish, package_id=package_id, operator_id="alice"
        )
        assert exit_code == EXIT_SUCCESS
        assert publish_payload["success"] is True


# --- Failure semantics ----------------------------------------------------------


class TestFailureSemantics:
    def test_stage_1_malformed_template_does_not_block_confirmation(self):
        template_dir = Path(".pcae/authority-evaluation/templates/demo-template")
        template_dir.mkdir(parents=True)
        (template_dir / "1.0.json").write_text("not valid json", encoding="utf-8")

        session_id, confirm_payload = _confirmed()
        assert confirm_payload["session"]["session_state"] == "Confirmed"
        assert confirm_payload["authority_evaluation_stage_1"] == "evaluation_failed"

    def test_stage_2_malformed_template_surfaces_as_governed_error_not_a_crash(self):
        template_dir = Path(".pcae/authority-evaluation/templates/demo-template")
        template_dir.mkdir(parents=True)
        (template_dir / "1.0.json").write_text("not valid json", encoding="utf-8")

        session_id, _ = _confirmed()
        exit_code, payload = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
        assert exit_code != EXIT_SUCCESS
        assert payload["status"] == "error"
        assert payload["error_type"] == "internal_error"


# --- Diagnostics ------------------------------------------------------------------


class TestDiagnostics:
    def test_status_reports_disabled_when_unconfigured(self):
        exit_code, payload = self._run_json()
        assert exit_code == 0
        assert payload["enabled"] is False

    def test_status_reports_enabled_when_configured(self):
        _deploy_template()
        exit_code, payload = self._run_json()
        assert exit_code == 0
        assert payload["enabled"] is True

    def test_status_reports_package_summary(self):
        _deploy_template()
        _declare_eligible({"alice"})
        session_id, _ = _confirmed()
        exit_code, readiness_payload = _run(
            run_decision_session_readiness, session_id=session_id, as_identity="alice"
        )
        assert exit_code == EXIT_SUCCESS
        package_id = readiness_payload["package_id"]

        exit_code, payload = self._run_json(package_id=package_id)
        assert exit_code == 0
        assert payload["current_effective_stage_2"]["canonical_evaluation_result"] == "eligible"

    def test_status_never_mutates(self, tmp_path):
        before = sorted(p for p in Path(".pcae").rglob("*") if p.is_file())
        self._run_json()
        after = sorted(p for p in Path(".pcae").rglob("*") if p.is_file())
        assert before == after

    @staticmethod
    def _run_json(package_id=None, **kwargs):
        args = _Args(package_id=package_id, **kwargs)
        buf = io.StringIO()
        from contextlib import redirect_stdout

        with redirect_stdout(buf):
            exit_code = run_aesic_status(args)
        return exit_code, json.loads(buf.getvalue())


# --- AESIC-N-01 continued containment ------------------------------------------


class TestAesicN01Containment:
    def test_diagnostics_read_canonical_call_is_single_key_only(self):
        """`summarize_package`/`read_canonical` accept exactly one key
        (``package_id``); no caller anywhere -- including this phase's
        new diagnostics surface -- can supply a mismatched compound
        (package_id, evaluation_id) pair through this method."""

        import inspect

        sig = inspect.signature(AuthorityEvaluationRecordStore.read_canonical)
        params = [p for p in sig.parameters if p != "self"]
        assert params == ["package_id"]

    def test_composition_module_never_calls_write_pointer_or_write_record(self):
        import pcae.aesic.composition as composition_module

        source = Path(composition_module.__file__).read_text(encoding="utf-8")
        assert "write_pointer" not in source
        assert "write_record" not in source

    def test_aesic_status_command_never_calls_write_pointer_or_write_record(self):
        import pcae.commands.aesic_status as status_module

        source = Path(status_module.__file__).read_text(encoding="utf-8")
        assert "write_pointer" not in source
        assert "write_record" not in source
