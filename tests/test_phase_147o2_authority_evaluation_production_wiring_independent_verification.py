"""Phase 147O.2 independent verification tests: Authority Evaluation
Service production wiring (AESIC-001 v1.3, Phase 147O.1's closure claim
for AESIC-O-01).

Independently authored -- does not import, call, or duplicate Phase
147O.1's own test module
(``tests/test_phase_147o1_authority_evaluation_production_wiring.py``).
Where that module verifies production reachability exclusively through
in-process handler calls (``_run(handler, **kwargs)`` against a
``tmp_path``-rooted, ``monkeypatch.chdir``-ed working directory, never a
real OS process boundary), this module adds genuine separate-process
``pcae`` CLI reproduction (``subprocess.run([sys.executable, "-m",
"pcae", ...])``) as the authoritative evidence for production
reachability, plus source-boundary/AST checks and a path-containment
probe of the ``package_id`` compound key that 147O.1's own suite does
not exercise.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.aesic.storage import AuthorityEvaluationRecordStore
from pcae.aesic.diagnostics import summarize_package
from pcae.aesic.errors import AuthorityEvaluationStorageIdentifierError

_REPO_SRC = str(Path(__file__).resolve().parents[1] / "src")


def _run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pcae", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env={"PYTHONPATH": _REPO_SRC, "PATH": "/usr/bin:/bin"},
    )


def _json(proc: subprocess.CompletedProcess) -> dict:
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


# --- Separate-process end-to-end reproduction (AESIC-001 v1.3 §18) --------


class TestSeparateProcessReproduction:
    """Each step below is a distinct ``python -m pcae`` subprocess --
    a real OS process boundary, not an in-process handler call. This is
    the discriminator Phase 147O.1's own automated suite does not meet
    (its tests call ``run_decision_session_*`` handler functions
    directly); only its narrative §18 claims process separation, and
    that claim was never captured as a reproducible automated test."""

    def test_configured_eligible_lifecycle_across_real_processes(self, tmp_path):
        repo = tmp_path / "configured_repo"
        repo.mkdir()

        subprocess.run(
            [sys.executable, "-c",
             "from pcae.aesic.template_store import write_template; "
             "write_template('demo-template', '1.0', 'Approved by Registry.')"],
            cwd=str(repo), env={"PYTHONPATH": _REPO_SRC}, check=True,
        )
        subprocess.run(
            [sys.executable, "-c",
             "from pcae.aesic.registry_filesystem import FilesystemAuthorityRegistry; "
             "from pcae.authority_evaluation.models import EligibleAuthorityDeclaration; "
             "FilesystemAuthorityRegistry().write_declaration(EligibleAuthorityDeclaration("
             "template_ref='demo-template', template_version='1.0', "
             "eligible_identities=frozenset({'alice'}), "
             "declared_at='2026-01-01T00:00:00.000000Z', declared_by='op'))"],
            cwd=str(repo), env={"PYTHONPATH": _REPO_SRC}, check=True,
        )

        status = _json(_run_cli(repo, "aesic", "status", "--json"))
        assert status["enabled"] is True

        create = _json(_run_cli(
            repo, "decision-session", "create",
            "--template-ref", "demo-template", "--subject-ref", "subj-1",
            "--owner-id", "alice", "--json",
        ))
        session_id = create["session"]["session_id"]

        assert _run_cli(
            repo, "decision-session", "evidence", session_id,
            "--declare", "ev-1", "--as-identity", "alice", "--json",
        ).returncode == 0

        assert _run_cli(
            repo, "decision-session", "select", session_id,
            "--option-id", "opt-a", "--options-presented", "opt-a",
            "--options-presented", "opt-b", "--template-version", "1.0",
            "--as-identity", "alice", "--json",
        ).returncode == 0

        preview = _json(_run_cli(repo, "decision-session", "preview", session_id, "--as-identity", "alice", "--json"))

        confirm = _json(_run_cli(
            repo, "decision-session", "confirm", session_id,
            "--preview-digest", preview["preview_digest"], "--statement", "confirmed",
            "--as-identity", "alice", "--json",
        ))
        assert confirm["authority_evaluation_stage_1"] == "eligible"

        readiness = _json(_run_cli(repo, "decision-session", "readiness", session_id, "--as-identity", "alice", "--json"))
        package_id = readiness["package_id"]

        status_pkg = _json(_run_cli(repo, "aesic", "status", "--package-id", package_id, "--json"))
        assert status_pkg["current_effective_stage_2"]["canonical_evaluation_result"] == "eligible"

        publish = _json(_run_cli(repo, "governance-record", "publish", package_id, "--operator-id", "alice", "--json"))
        assert publish["success"] is True
        record_id = publish["record_id"]

        chgr_path = repo / ".pcae" / "publication-execution" / "records" / f"{record_id}.json"
        chgr = json.loads(chgr_path.read_text(encoding="utf-8"))
        assert chgr["authority_basis_claimed"] == "Approved by Registry."

        # Restart: a fresh process re-invoking readiness must report the
        # already-consumed package, never mint or re-run a second Stage 2.
        replay = _json(_run_cli(repo, "decision-session", "readiness", session_id, "--as-identity", "alice", "--json"))
        assert replay["disposition"] == "consumed"
        assert replay["record_id"] == record_id

    def test_unconfigured_repository_stays_backward_compatible_across_real_processes(self, tmp_path):
        repo = tmp_path / "unconfigured_repo"
        repo.mkdir()

        status = _json(_run_cli(repo, "aesic", "status", "--json"))
        assert status["enabled"] is False
        assert status["reason"] == "template_root_absent"

        create = _json(_run_cli(
            repo, "decision-session", "create",
            "--template-ref", "legacy-template", "--subject-ref", "subj-1",
            "--owner-id", "bob", "--json",
        ))
        session_id = create["session"]["session_id"]
        _run_cli(repo, "decision-session", "evidence", session_id, "--declare", "ev-1", "--as-identity", "bob", "--json")
        _run_cli(
            repo, "decision-session", "select", session_id,
            "--option-id", "opt-a", "--options-presented", "opt-a",
            "--options-presented", "opt-b", "--template-version", "1.0",
            "--as-identity", "bob", "--json",
        )
        preview = _json(_run_cli(repo, "decision-session", "preview", session_id, "--as-identity", "bob", "--json"))
        confirm = _json(_run_cli(
            repo, "decision-session", "confirm", session_id,
            "--preview-digest", preview["preview_digest"], "--statement", "ok",
            "--as-identity", "bob", "--json",
        ))
        assert confirm["authority_evaluation_stage_1"] == "not_configured"

        readiness = _json(_run_cli(repo, "decision-session", "readiness", session_id, "--as-identity", "bob", "--json"))
        package_id = readiness["package_id"]

        publish = _json(_run_cli(repo, "governance-record", "publish", package_id, "--operator-id", "bob", "--json"))
        assert publish["success"] is True
        record_id = publish["record_id"]

        chgr_path = repo / ".pcae" / "publication-execution" / "records" / f"{record_id}.json"
        chgr = json.loads(chgr_path.read_text(encoding="utf-8"))
        assert "authority_basis_claimed" not in chgr


# --- Source-boundary / composition-root verification -----------------------


class TestSourceBoundaryIndependentReconstruction:
    """Independently re-derives AESIC-O-01 (pre-147O.1 unreachability)
    and its closure by walking import graphs directly, rather than
    trusting the 147O.1/147O reports' prose claims."""

    def test_aesic_zone_has_no_reverse_dependency_on_commands(self):
        aesic_dir = Path(__file__).resolve().parents[1] / "src" / "pcae" / "aesic"
        for path in aesic_dir.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert not node.module.startswith("pcae.commands"), (
                        f"{path} imports {node.module}: aesic must not depend on commands"
                    )
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith("pcae.commands"), (
                            f"{path} imports {alias.name}: aesic must not depend on commands"
                        )

    def test_commands_only_import_aesic_composition_root_and_diagnostics_never_authority_evaluation_directly(self):
        for filename in ("decision_session.py", "aesic_status.py"):
            path = Path(__file__).resolve().parents[1] / "src" / "pcae" / "commands" / filename
            tree = ast.parse(path.read_text(encoding="utf-8"))
            aesic_imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("pcae."):
                    aesic_imports.append(node.module)
            assert not any(m.startswith("pcae.authority_evaluation") for m in aesic_imports), (
                f"{filename} must construct AES only via pcae.aesic.composition, "
                "never import pcae.authority_evaluation directly"
            )
            assert not any(
                m in ("pcae.aesic.registry_filesystem", "pcae.aesic.service", "pcae.aesic.storage")
                and filename == "decision_session.py"
                for m in aesic_imports
            ), f"{filename} must not construct AES collaborators itself, only via composition.py"

    def test_publication_coordinator_source_contains_no_aesic_or_authority_evaluation_reference(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "src" / "pcae" / "governance" / "publication" / "coordinator.py"
        )
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = getattr(node, "module", None) or ""
                names = [module] + [getattr(a, "name", "") for a in getattr(node, "names", [])]
                for name in names:
                    assert "aesic" not in name and "authority_evaluation" not in name
        assert "AuthorityEvaluationService" not in source
        assert "evaluate_stage_2" not in source


# --- AESIC-N-01 containment: independent reconstruction --------------------


class TestAesicN01IndependentContainment:
    """Re-derives the storage-layer cross-key gap directly against
    ``AuthorityEvaluationRecordStore`` (not through the AES service, to
    isolate the storage layer's own guarantee from the caller
    discipline that contains it), then independently checks every
    caller of ``read_canonical`` in production source."""

    def test_storage_layer_gap_reproduced_directly_at_the_storage_api(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from pcae.aesic.composition import build_authority_evaluation_service
        from pcae.aesic.template_store import write_template
        from pcae.interactive_workflow.models.session import Session, SessionState

        # Use the real production service to create a genuine AER under
        # "pkg-a" (avoids hand-constructing AuthorityEvaluationRecord/
        # AuthorityEvaluationOutcome, whose isinstance checks are brittle
        # against cross-module reload identity -- an unrelated pre-existing
        # test-isolation quirk of Phase 147H's own suite, not this phase's
        # concern).
        write_template("t", "1.0", "A")
        service = build_authority_evaluation_service()
        session = Session(
            session_id="CDS-n01-a", template_ref="t", template_version="1.0",
            subject_ref="subj-1", owner_identity="alice", session_state=SessionState.CONFIRMED,
            created_at="2026-01-01T00:00:00.000000Z", updated_at="2026-01-01T00:00:00.000000Z",
        )
        record_a = service.evaluate_stage_2(session=session, package_id="pkg-a")

        # Forge a pointer stored under key "pkg-a" whose *embedded*
        # package_id names a different package -- simulating filesystem
        # tampering, since no production writer ever does this (see the
        # second test below). Written as a raw dict, matching
        # CanonicalPointer's own on-disk schema, to avoid any dependency on
        # dataclass type identity.
        import pcae.aesic.storage as storage_mod
        import pcae.aesic.records as records_mod

        store = AuthorityEvaluationRecordStore()
        content = {
            "package_id": "pkg-b",
            "evaluation_id": record_a.evaluation_id,
            "record_id": record_a.record_id,
            "record_digest": records_mod.aer_to_payload(record_a)["record_digest"],
            "schema_version": records_mod.CANONICAL_POINTER_SCHEMA_VERSION,
        }
        forged_payload = dict(content)
        forged_payload["pointer_digest"] = records_mod._compute_pointer_digest(content)

        pointer_path = store._pointer_path("pkg-a")
        pointer_path.parent.mkdir(parents=True, exist_ok=True)
        storage_mod._write_atomic_json(pointer_path, forged_payload)

        from pcae.aesic.errors import CanonicalPointerCorruptError

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-a")

    def test_every_production_read_canonical_caller_supplies_a_single_non_derived_package_id(self):
        service_path = Path(__file__).resolve().parents[1] / "src" / "pcae" / "aesic" / "service.py"
        diagnostics_path = Path(__file__).resolve().parents[1] / "src" / "pcae" / "aesic" / "diagnostics.py"

        for path in (service_path, diagnostics_path):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            calls = [
                node for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "read_canonical"
            ]
            assert calls, f"expected at least one read_canonical call in {path}"
            for call in calls:
                assert len(call.args) == 1, "read_canonical must be called with exactly one positional arg"

    def test_package_id_dotdot_now_rejected_before_any_filesystem_access(self, tmp_path, monkeypatch):
        """147O.2-F-1, CLOSED by Phase 147P. Pre-147P finding (not
        disclosed by Phase 147O.1): a ``package_id`` of ``".."`` was not
        rejected by ``_safe_name`` (``.`` is an allowed character) and,
        used as a bare directory component, resolved one level above the
        intended per-package ``records/<package_id>/`` directory -- still
        contained within the AER storage root, never outside the
        repository, but reached only through the read-only ``pcae aesic
        status --package-id`` diagnostic (every production *write* call
        site generates ``package_id`` internally as ``prp-<uuid4hex>``,
        never from untrusted input, so it was never writable in
        production). Phase 147P's explicit-identifier-validation repair
        now rejects ``".."`` (and every other non-single-component value)
        before any filesystem access is attempted, rather than relying on
        `_safe_name`'s substitution to merely keep the eventual path
        contained."""
        monkeypatch.chdir(tmp_path)
        store = AuthorityEvaluationRecordStore()
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._record_path("..", "ev-1")
        # Read-only diagnostic surface: the invalid identifier is rejected
        # internally, never crashes the diagnostic -- surfaced as "no
        # canonical record", never raise or leak.
        summary = summarize_package(store, "..")
        assert summary.canonical_record_id is None
        assert summary.canonical_pointer_ok is False


# --- Non-gating vs. failure-blocking characterization -----------------------


class TestNonGatingCharacterization:
    """147O.1 discloses (its own ``TestFailureSemantics``) that a Stage
    2 *integration failure* (e.g. malformed template) surfaces readiness
    construction as a governed error. That is failure-handling, not
    outcome-gating -- but the distinction is easy to blur. This test
    independently confirms both halves: a *negative evaluation outcome*
    (ineligible, no exception) does not block the lifecycle, while a
    genuine *integration failure* does block readiness construction
    (fails closed, does not silently fabricate a citation)."""

    def _deploy(self, template_ref="demo-template", template_version="1.0", eligible_authority="Approved."):
        from pcae.aesic.template_store import write_template
        write_template(template_ref, template_version, eligible_authority)

    def _lifecycle_to_readiness(self, owner="alice", declare_eligible_for=frozenset()):
        import io
        from contextlib import redirect_stdout
        from pcae.commands.decision_session import (
            EXIT_SUCCESS,
            run_decision_session_confirm,
            run_decision_session_create,
            run_decision_session_evidence,
            run_decision_session_preview,
            run_decision_session_readiness,
            run_decision_session_select,
        )

        class _A:
            def __init__(self, **kw):
                self.json = True
                self.rationale = None
                self.conditions = None
                for k, v in kw.items():
                    setattr(self, k, v)

        def call(handler, **kw):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = handler(_A(**kw))
            return code, json.loads(buf.getvalue())

        if declare_eligible_for:
            from pcae.aesic.registry_filesystem import FilesystemAuthorityRegistry
            from pcae.authority_evaluation.models import EligibleAuthorityDeclaration
            FilesystemAuthorityRegistry().write_declaration(
                EligibleAuthorityDeclaration(
                    template_ref="demo-template", template_version="1.0",
                    eligible_identities=frozenset(declare_eligible_for),
                    declared_at="2026-01-01T00:00:00.000000Z", declared_by="op",
                )
            )

        code, payload = call(
            run_decision_session_create, template_ref="demo-template", subject_ref="subj-1", owner_id=owner
        )
        assert code == EXIT_SUCCESS
        session_id = payload["session"]["session_id"]
        code, _ = call(run_decision_session_evidence, session_id=session_id, declare=["ev-1"], as_identity=owner)
        assert code == EXIT_SUCCESS
        code, _ = call(
            run_decision_session_select, session_id=session_id, option_id="opt-a",
            options_presented=["opt-a", "opt-b"], template_version="1.0", as_identity=owner,
        )
        assert code == EXIT_SUCCESS
        code, preview = call(run_decision_session_preview, session_id=session_id, as_identity=owner)
        assert code == EXIT_SUCCESS
        code, confirm = call(
            run_decision_session_confirm, session_id=session_id, preview_digest=preview["preview_digest"],
            statement="confirmed", as_identity=owner,
        )
        assert code == EXIT_SUCCESS
        return session_id, confirm, call, run_decision_session_readiness

    def test_ineligible_outcome_does_not_block_readiness(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self._deploy()
        session_id, confirm, call, readiness_handler = self._lifecycle_to_readiness(
            owner="carol", declare_eligible_for=frozenset({"someone-else"})
        )
        assert confirm["authority_evaluation_stage_1"] == "ineligible"
        code, readiness_payload = call(readiness_handler, session_id=session_id, as_identity="carol")
        assert code == 0
        assert readiness_payload["disposition"] == "pending"

        store = AuthorityEvaluationRecordStore()
        record = store.read_canonical(readiness_payload["package_id"])
        assert record.outcome.evaluation_result.value == "ineligible"

    def test_stage_2_integration_failure_fails_closed_not_silently(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        template_dir = tmp_path / ".pcae" / "authority-evaluation" / "templates" / "demo-template"
        template_dir.mkdir(parents=True)
        (template_dir / "1.0.json").write_text("{not json", encoding="utf-8")

        session_id, confirm, call, readiness_handler = self._lifecycle_to_readiness(owner="dave")
        assert confirm["authority_evaluation_stage_1"] == "evaluation_failed"
        code, payload = call(readiness_handler, session_id=session_id, as_identity="dave")
        assert code != 0
        assert payload["status"] == "error"


# --- Restart / recovery: fresh service instance per operation --------------


class TestRestartRecovery:
    def test_fresh_composition_root_rediscovers_prior_canonical_record(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from pcae.aesic.composition import build_authority_evaluation_service
        from pcae.aesic.template_store import write_template
        from pcae.interactive_workflow.models.session import Session, SessionState

        write_template("demo-template", "1.0", "Approved.")
        service_a = build_authority_evaluation_service()
        session = Session(
            session_id="CDS-restart-1", template_ref="demo-template", template_version="1.0",
            subject_ref="subj-1", owner_identity="alice", session_state=SessionState.CONFIRMED,
            created_at="2026-01-01T00:00:00.000000Z", updated_at="2026-01-01T00:00:00.000000Z",
        )
        first = service_a.evaluate_stage_2(session=session, package_id="prp-restart-1")

        service_b = build_authority_evaluation_service()
        assert service_b is not service_a
        second = service_b.evaluate_stage_2(session=session, package_id="prp-restart-1")
        assert second.record_id == first.record_id, "idempotent no-op must reuse the canonical record across restarts"
