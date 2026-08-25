"""Phase 145G unit tests: ``pcae decision-session`` +
``pcae governance-record publish`` CLI/transport adapter (IWPC-001 v1.1).

Covers: parser/registration, session command surface (create/status/
readiness -- the three IWPC-001-frozen ``decision-session`` commands this
phase implements), publish command surface, exit-code/error-taxonomy
mapping, JSON output determinism, output sanitization (no raw exception
text/traceback/paths), the dependency/forbidden-import boundary, and
security paths (path traversal, empty-identity rejection). Does not test
``evidence``/``clarify``/``preview``/``confirm``/``cancel`` -- this phase
does not implement them (see ``pcae.commands.decision_session``'s module
docstring for the disclosed reason).
"""

from __future__ import annotations

import ast
import io
import json
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.cli import build_parser
from pcae.commands.decision_session import (
    EXIT_AUTHORIZATION_REPLAY,
    EXIT_GENERIC_DOMAIN_FAILURE,
    EXIT_STALE_AUTHORIZATION,
    EXIT_SUCCESS,
    _EXIT_CODE_BY_ERROR_TYPE,
    build_application_context,
    run_decision_session_create,
    run_decision_session_readiness,
    run_decision_session_status,
)
from pcae.commands.governance_record import run_governance_record_publish
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    FilesystemPendingReadinessStore,
)
from pcae.interactive_workflow.persistence.filesystem_repository import FilesystemSessionRepository
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _Args:
    """Minimal ``argparse.Namespace``-alike for direct handler invocation."""

    def __init__(self, **kwargs):
        self.json = True
        # Phase 145G.3: default the new required identity claim to match
        # this file's predominant fixture owner ("alice") so existing
        # scenarios keep exercising what they were written to exercise;
        # call sites against a differently-owned session override it
        # explicitly.
        self.as_identity = "alice"
        for key, value in kwargs.items():
            setattr(self, key, value)


def _run(handler, **kwargs) -> tuple[int, dict]:
    args = _Args(**kwargs)
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = handler(args)
    output = buf.getvalue()
    return exit_code, json.loads(output)


@pytest.fixture(autouse=True)
def _isolated_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Phase 149O.20L.7O.3C.2: CHGR publication is now covered by the
    # Permission Broker (POL-001 "Missing Active Task", the same
    # existing invariant `pcae commit`/`push`/promotion already require)
    # via `PublicationApplicationService.hand_off`'s new gate. Every
    # test in this file exercises publication in an isolated repo with
    # no PCAE task lifecycle of its own, so a minimal active-task
    # contract is provided here so POL-001 evaluates truthfully rather
    # than this file's own scenarios becoming an unintended proxy for
    # "no active task" coverage (that scenario is covered directly by
    # the 3C.2 phase's own test suite instead).
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "20260101-0000-phase-145g-cli-fixture-task.md").write_text(
        "# Phase 145G CLI fixture task\n", encoding="utf-8"
    )
    yield tmp_path


def _make_confirmed_session_with_package(package_id: str = "pubpkg-test-1"):
    exit_code, payload = _run(
        run_decision_session_create,
        template_ref="tmpl-1",
        subject_ref="subj-1",
        owner_id="alice",
    )
    assert exit_code == EXIT_SUCCESS
    session_id = payload["session"]["session_id"]

    repo = FilesystemSessionRepository()
    session = repo.load(session_id)
    confirmed = session.with_state(SessionState.CONFIRMED, _now())
    confirmed = confirmed.__class__(**{**confirmed.__dict__, "human_selection_id": "opt-a"})
    repo.persist(confirmed)

    pkg = PublicationReadinessPackage(
        package_id=package_id,
        session_id=session_id,
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=7,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview_id="preview-1",
        preview_digest="a" * 64,
        confirmation_request_id="req-1",
        confirmation_response_id="resp-1",
        built_at=_now(),
        decision_subject="subj-1",
        template_id="tmpl-1",
        template_version="1.0",
        selected_option_id="opt-a",
        rationale_text="because",
        conditions_text=None,
        options_presented=("opt-a", "opt-b"),
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "alice",
            "captured_at": _now(),
        },
        preview_rendered_content="rendered",
        confirmation_statement="accepted",
        confirmation_timestamp=_now(),
    )
    store = FilesystemPendingReadinessStore()
    store.create(pkg, persisted_at=_now())
    return session_id, package_id


# --- Parser / registration --------------------------------------------------


def test_decision_session_parser_registered():
    parser = build_parser()
    args = parser.parse_args(
        ["decision-session", "create", "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o"]
    )
    assert args.decision_session_command == "create"
    assert args.template_ref == "t"


def test_decision_session_status_and_readiness_registered():
    parser = build_parser()
    args = parser.parse_args(["decision-session", "status", "CDS-abc"])
    assert args.session_id == "CDS-abc"
    args = parser.parse_args(
        ["decision-session", "readiness", "CDS-abc", "--as-identity", "alice", "--json"]
    )
    assert args.session_id == "CDS-abc"
    assert args.json is True


def test_governance_record_publish_registered():
    parser = build_parser()
    args = parser.parse_args(["governance-record", "publish", "pkg-1", "--operator-id", "bob"])
    assert args.package_id == "pkg-1"
    assert args.operator_id == "bob"


def test_decision_session_create_requires_all_arguments():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["decision-session", "create", "--template-ref", "t"])


def test_publish_requires_operator_id():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["governance-record", "publish", "pkg-1"])


def test_no_force_or_bypass_flag_exists_on_publish():
    args = build_parser().parse_args(
        ["governance-record", "publish", "pkg-1", "--operator-id", "bob"]
    )
    assert not hasattr(args, "force")
    assert not hasattr(args, "assume_authorized")


# --- decision-session create -------------------------------------------------


def test_create_success_renders_session_and_state():
    exit_code, payload = _run(
        run_decision_session_create, template_ref="tmpl-1", subject_ref="subj-1", owner_id="alice"
    )
    assert exit_code == EXIT_SUCCESS
    assert payload["status"] == "success"
    assert payload["session"]["session_state"] == "Created"
    assert payload["session"]["session_id"].startswith("CDS-")
    assert payload["schema_version"] == "iwpc-transport/1.0"


@pytest.mark.parametrize("field", ["template_ref", "subject_ref", "owner_id"])
def test_create_rejects_empty_required_fields(field):
    kwargs = {"template_ref": "t", "subject_ref": "s", "owner_id": "o"}
    kwargs[field] = ""
    exit_code, payload = _run(run_decision_session_create, **kwargs)
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["status"] == "error"
    assert payload["error_type"] == "invalid_request"


def test_create_is_non_idempotent_distinct_session_ids():
    _, first = _run(run_decision_session_create, template_ref="t", subject_ref="s", owner_id="o")
    _, second = _run(run_decision_session_create, template_ref="t", subject_ref="s", owner_id="o")
    assert first["session"]["session_id"] != second["session"]["session_id"]


# --- decision-session status --------------------------------------------------


def test_status_success_reports_no_readiness_package():
    _, created = _run(run_decision_session_create, template_ref="t", subject_ref="s", owner_id="o")
    session_id = created["session"]["session_id"]
    exit_code, payload = _run(run_decision_session_status, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["readiness_package_status"] == "none"
    assert payload["session"]["session_state"] == "Created"


def test_status_session_not_found():
    exit_code, payload = _run(
        run_decision_session_status, session_id="CDS-00000000-0000-4000-8000-000000000000"
    )
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "session_not_found"


def test_status_invalid_session_identifier():
    exit_code, payload = _run(run_decision_session_status, session_id="not-a-session-id")
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_status_reports_pending_readiness_then_consumed_after_publication():
    """Repaired by Phase 145H.2 (IWPC-001 v1.4 IWPC-REQ-198): a
    session_id-keyed lookup now reaches a consumed/ record too, so
    ``decision-session status`` reports "consumed" (not "none") once the
    bound package has been published."""

    session_id, package_id = _make_confirmed_session_with_package()
    exit_code, payload = _run(run_decision_session_status, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["readiness_package_status"] == "pending"

    _run(run_governance_record_publish, package_id=package_id, operator_id="bob")

    exit_code, payload = _run(run_decision_session_status, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["readiness_package_status"] == "consumed"


# --- decision-session readiness ----------------------------------------------


def test_readiness_incomplete_when_no_package_exists():
    _, created = _run(run_decision_session_create, template_ref="t", subject_ref="s", owner_id="o")
    session_id = created["session"]["session_id"]
    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id, as_identity="o")
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "readiness_incomplete"
    assert payload["session_id"] == session_id


def test_readiness_reports_existing_pending_package():
    session_id, package_id = _make_confirmed_session_with_package()
    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["package_id"] == package_id
    assert payload["disposition"] == "pending"
    assert payload["record_id"] is None


def test_readiness_session_not_found():
    exit_code, payload = _run(
        run_decision_session_readiness, session_id="CDS-00000000-0000-4000-8000-000000000001"
    )
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "session_not_found"


# --- Phase 145H.2: post-consumption readiness uniqueness (IWPC-001 v1.4 §35) --


def _chgr_record_count() -> int:
    """Phase 146G: one Publication Execution now durably persists four
    independently schema-validated CHGR-001 v1.2 artifacts, not one flat
    record -- callers comparing against this count check for exactly one
    Publication Execution's worth (4), never a duplicate/partial set."""
    records_dir = Path(".pcae") / "publication-execution" / "records"
    if not records_dir.exists():
        return 0
    return len(list(records_dir.glob("*.json")))


def test_readiness_before_publication_is_idempotent():
    session_id, package_id = _make_confirmed_session_with_package()
    exit_code_1, payload_1 = _run(run_decision_session_readiness, session_id=session_id)
    exit_code_2, payload_2 = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code_1 == exit_code_2 == EXIT_SUCCESS
    assert payload_1["package_id"] == payload_2["package_id"] == package_id
    assert payload_1["disposition"] == payload_2["disposition"] == "pending"


def test_original_h1_defect_no_longer_reproducible():
    """Reproduces 145H's own live-CLI Blocking Finding H-1 sequence
    exactly (readiness -> publish -> readiness again -> publish again) and
    verifies: no second package_id is minted, no second CHGR is created,
    and the second publish is correctly rejected as a replay."""

    session_id, package_id = _make_confirmed_session_with_package()

    exit_code, first_readiness = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert first_readiness["disposition"] == "pending"

    exit_code, publish_result = _run(
        run_governance_record_publish, package_id=package_id, operator_id="bob"
    )
    assert exit_code == EXIT_SUCCESS
    record_id = publish_result["record_id"]
    assert _chgr_record_count() == 4

    exit_code, second_readiness = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert second_readiness["package_id"] == package_id, "a second package_id must never be minted"
    assert second_readiness["disposition"] == "consumed"
    assert second_readiness["record_id"] == record_id

    exit_code, replay = _run(run_governance_record_publish, package_id=package_id, operator_id="bob")
    assert exit_code == EXIT_AUTHORIZATION_REPLAY
    assert replay["error_type"] == "publication_already_completed"
    assert replay["record_id"] == record_id
    assert _chgr_record_count() == 4, "no second CHGR set may ever be created for the same session"


def test_readiness_after_publication_repeated_reports_same_consumed_identity():
    session_id, package_id = _make_confirmed_session_with_package()
    _run(run_governance_record_publish, package_id=package_id, operator_id="bob")

    exit_code_1, payload_1 = _run(run_decision_session_readiness, session_id=session_id)
    exit_code_2, payload_2 = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code_1 == exit_code_2 == EXIT_SUCCESS
    assert payload_1 == payload_2
    assert payload_1["package_id"] == package_id
    assert payload_1["disposition"] == "consumed"
    assert _chgr_record_count() == 4


def test_readiness_persists_consumed_identity_across_restart():
    """Persistence across restart: each ``_run`` call builds a brand-new
    ``ApplicationContext`` (fresh store/repository instances reading from
    disk, simulating a new process) and still reports the same,
    already-consumed package identity -- nothing is cached in-process."""

    session_id, package_id = _make_confirmed_session_with_package()
    _run(run_governance_record_publish, package_id=package_id, operator_id="bob")

    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["package_id"] == package_id
    assert payload["disposition"] == "consumed"


def test_readiness_after_failed_publication_remains_pending():
    session_id, package_id = _make_confirmed_session_with_package()
    exit_code, payload = _run(
        run_governance_record_publish, package_id="pubpkg-does-not-exist", operator_id="bob"
    )
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE

    exit_code, readiness = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert readiness["package_id"] == package_id
    assert readiness["disposition"] == "pending"
    assert readiness["record_id"] is None


def test_readiness_fails_closed_on_duplicate_historical_records():
    """IWPC-REQ-204: a repository already carrying two readiness records
    for one session_id (pre-145H.2 historical inconsistency) must fail
    closed with persistence_corrupt, never silently pick one."""

    session_id, _package_id = _make_confirmed_session_with_package(package_id="pubpkg-dup-a")
    dup_pkg = PublicationReadinessPackage(
        package_id="pubpkg-dup-b",
        session_id=session_id,
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=7,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview_id="preview-1",
        preview_digest="a" * 64,
        confirmation_request_id="req-1",
        confirmation_response_id="resp-1",
        built_at=_now(),
        decision_subject="subj-1",
        template_id="tmpl-1",
        template_version="1.0",
        selected_option_id="opt-a",
        rationale_text="because",
        conditions_text=None,
        options_presented=("opt-a", "opt-b"),
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "alice",
            "captured_at": _now(),
        },
        preview_rendered_content="rendered",
        confirmation_statement="accepted",
        confirmation_timestamp=_now(),
    )
    FilesystemPendingReadinessStore().create(dup_pkg, persisted_at=_now())

    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "persistence_corrupt"


# --- governance-record publish ------------------------------------------------


def test_publish_success_renders_verbatim_result():
    session_id, package_id = _make_confirmed_session_with_package()
    exit_code, payload = _run(run_governance_record_publish, package_id=package_id, operator_id="bob")
    assert exit_code == EXIT_SUCCESS
    assert payload["status"] == "success"
    assert payload["success"] is True
    assert payload["package_id"] == package_id
    assert payload["session_id"] == session_id
    assert payload["record_id"].startswith("chgr-")


def test_publish_replay_already_completed():
    _, package_id = _make_confirmed_session_with_package()
    _run(run_governance_record_publish, package_id=package_id, operator_id="bob")
    exit_code, payload = _run(run_governance_record_publish, package_id=package_id, operator_id="bob")
    assert exit_code == EXIT_AUTHORIZATION_REPLAY
    assert payload["error_type"] == "publication_already_completed"
    assert payload["record_id"].startswith("chgr-")


def test_publish_package_not_found():
    exit_code, payload = _run(
        run_governance_record_publish, package_id="pubpkg-does-not-exist", operator_id="bob"
    )
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "artifact_not_found"


def test_publish_rejects_empty_operator_id():
    _, package_id = _make_confirmed_session_with_package()
    exit_code, payload = _run(run_governance_record_publish, package_id=package_id, operator_id="")
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_publish_rejects_path_traversal_package_id():
    exit_code, payload = _run(
        run_governance_record_publish, package_id="../../../etc/passwd", operator_id="bob"
    )
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"
    assert "etc/passwd" not in payload["message"]


def test_publish_stale_session_rejected():
    session_id, package_id = _make_confirmed_session_with_package()
    repo = FilesystemSessionRepository()
    session = repo.load(session_id)
    expired = session.with_state(SessionState.EXPIRED, _now())
    repo.persist(expired)

    exit_code, payload = _run(run_governance_record_publish, package_id=package_id, operator_id="bob")
    assert exit_code == EXIT_STALE_AUTHORIZATION
    assert payload["error_type"] == "artifact_stale"


def test_publish_no_stack_trace_or_exception_class_leaked(capsys):
    _run(run_governance_record_publish, package_id="does-not-exist", operator_id="bob")
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "Traceback" not in combined
    assert "Error(" not in combined
    assert "PendingReadiness" not in combined


# --- Exit-code / error-taxonomy contract (IWPC-001 v1.1 §9, §19) ------------


_CLOSED_ERROR_TAXONOMY = {
    "invalid_request",
    "invalid_state_transition",
    "malformed_artifact",
    "unsupported_version",
    "artifact_not_found",
    "artifact_stale",
    "artifact_binding_mismatch",
    "confirmation_required",
    "confirmation_conflict",
    "authorization_required",
    "authorization_invalid",
    "authority_not_established",
    "publication_conflict",
    "publication_already_completed",
    "persistence_conflict",
    "persistence_corrupt",
    "internal_error",
    "readiness_incomplete",
    "session_not_found",
    "template_not_found",
    "subject_not_found",
    "stale_authorization",
    "authorization_replay",
    "invalid_package",
    "domain_error",
    "identity_binding_mismatch",
}


def test_error_taxonomy_is_closed_and_fully_mapped():
    assert set(_EXIT_CODE_BY_ERROR_TYPE.keys()) == _CLOSED_ERROR_TAXONOMY


def test_every_exit_code_is_within_0_to_6():
    for exit_code in _EXIT_CODE_BY_ERROR_TYPE.values():
        assert 0 <= exit_code <= 6


def test_error_type_exit_class_assignments_match_iwpc_req_050():
    assert _EXIT_CODE_BY_ERROR_TYPE["artifact_stale"] == 5
    assert _EXIT_CODE_BY_ERROR_TYPE["stale_authorization"] == 5
    assert _EXIT_CODE_BY_ERROR_TYPE["authorization_replay"] == 4
    assert _EXIT_CODE_BY_ERROR_TYPE["publication_already_completed"] == 4
    assert _EXIT_CODE_BY_ERROR_TYPE["confirmation_conflict"] == 3
    assert _EXIT_CODE_BY_ERROR_TYPE["artifact_binding_mismatch"] == 3
    assert _EXIT_CODE_BY_ERROR_TYPE["invalid_state_transition"] == 2
    assert _EXIT_CODE_BY_ERROR_TYPE["identity_binding_mismatch"] == 6


# --- JSON output determinism (IWPC-REQ-044/045) ------------------------------


def test_json_output_is_sorted_and_deterministic():
    args = _Args(template_ref="t", subject_ref="s", owner_id="o")
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_decision_session_create(args)
    output = buf.getvalue()
    keys = list(json.loads(output).keys())
    assert keys == sorted(keys)
    assert output.count("{") == output.count("}")  # single top-level object, no stray text


def test_json_mode_emits_only_json_on_stdout():
    args = _Args(template_ref="t", subject_ref="s", owner_id="o")
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_decision_session_create(args)
    json.loads(buf.getvalue())  # raises if anything but JSON is on stdout


# --- Dependency / forbidden-import boundary (IWPC-001 v1.1 §25, IWPC-REQ-176) --

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DECISION_SESSION_MODULE = _REPO_ROOT / "src" / "pcae" / "commands" / "decision_session.py"
_GOVERNANCE_RECORD_MODULE = _REPO_ROOT / "src" / "pcae" / "commands" / "governance_record.py"

_FORBIDDEN_IMPORT_ROOTS = (
    "pcae.interactive_workflow.orchestration",
    "pcae.interactive_workflow.evidence",
    "pcae.interactive_workflow.clarification",
    "pcae.interactive_workflow.preview",
    "pcae.interactive_workflow.confirmation",
    "pcae.interactive_workflow.state_machine",
    "pcae.interactive_workflow.audit",
    "pcae.interactive_workflow.publication_handoff",
    "pcae.governance.publication.storage",
    "pcae.governance.publication.record",
    "pcae.governance.publication.serialization",
    "pcae.lifecycle",
    "pcae.core.permission_broker",
    "pcae.core.permission_broker_foundation",
)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _imported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
    return names


@pytest.mark.parametrize("path", [_DECISION_SESSION_MODULE, _GOVERNANCE_RECORD_MODULE], ids=lambda p: p.name)
def test_cli_module_has_no_forbidden_imports(path: Path):
    modules = _imported_modules(path)
    for module in modules:
        for forbidden_root in _FORBIDDEN_IMPORT_ROOTS:
            assert not (module == forbidden_root or module.startswith(forbidden_root + ".")), (
                f"{path.name} imports {module!r}, coupling the CLI adapter to "
                f"{forbidden_root!r} in violation of IWPC-001's Dependency Contract."
            )


@pytest.mark.parametrize("path", [_DECISION_SESSION_MODULE, _GOVERNANCE_RECORD_MODULE], ids=lambda p: p.name)
def test_cli_module_imports_no_private_names(path: Path):
    names = _imported_names(path)
    for name in names:
        assert not name.startswith("_") or name == "_", (
            f"{path.name} imports private name {name!r}; the CLI adapter must use only "
            "public boundary methods of the subsystems it depends on."
        )


def test_interactive_workflow_does_not_import_cli_modules():
    interactive_workflow_root = _REPO_ROOT / "src" / "pcae" / "interactive_workflow"
    for path in interactive_workflow_root.rglob("*.py"):
        modules = _imported_modules(path)
        for module in modules:
            assert not module.startswith("pcae.commands") and module != "pcae.cli", (
                f"{path} imports {module!r}; Interactive Workflow must never import CLI code."
            )


def test_governance_publication_does_not_import_cli_modules():
    publication_root = _REPO_ROOT / "src" / "pcae" / "governance" / "publication"
    for path in publication_root.glob("*.py"):
        modules = _imported_modules(path)
        for module in modules:
            assert not module.startswith("pcae.commands") and module != "pcae.cli", (
                f"{path} imports {module!r}; Publication must never import CLI code."
            )


# --- Runtime neutrality (IWPC-REQ-013) ---------------------------------------


def test_build_application_context_has_no_import_time_side_effects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    context = build_application_context()
    assert not (tmp_path / ".pcae").exists()
    assert context.session_service is not None
    assert context.publication_service is not None
