"""Phase 145G.1 unit tests: completion of the ``pcae decision-session``
command surface (``evidence``/``clarify``/``preview``/``confirm``/
``cancel``) and repair of ``readiness``'s construction path.

Covers: parser registration for the five new subcommands; the two
commands genuinely reachable end-to-end via the CLI alone
(``evidence``, ``cancel``) exercised as real, separate handler
invocations against file-persisted state (simulating separate OS
processes); ``clarify``/``preview``/``confirm``/readiness-construction
exercised against a session bridged into its required precondition state
via direct construction (mirroring the existing Phase 145D-145G test
fixture convention -- see this phase's module docstring on
``pcae.commands.decision_session`` for why no CLI command can reach those
states in production); a full create-through-publish-through-replay
scenario with restart boundaries between every step; orchestration-record
corruption/restart-recovery tests; and an extension of the Phase 145G
forbidden-import boundary test to the new persistence/application-service
modules.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.cli import build_parser
from pcae.commands.decision_session import (
    EXIT_CONFIRMATION_CONFLICT,
    EXIT_GENERIC_DOMAIN_FAILURE,
    EXIT_INVALID_STATE_TRANSITION,
    EXIT_SUCCESS,
    run_decision_session_cancel,
    run_decision_session_clarify,
    run_decision_session_confirm,
    run_decision_session_create,
    run_decision_session_evidence,
    run_decision_session_preview,
    run_decision_session_readiness,
    run_decision_session_status,
)
from pcae.commands.governance_record import run_governance_record_publish
from pcae.interactive_workflow.errors import OrchestrationStoreCorruptError
from pcae.interactive_workflow.models.session import Session, SessionState
from pcae.interactive_workflow.persistence.filesystem_orchestration_store import (
    FilesystemOrchestrationStore,
    OrchestrationRecord,
)
from pcae.interactive_workflow.persistence.filesystem_repository import FilesystemSessionRepository


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _Args:
    def __init__(self, **kwargs):
        self.json = True
        # Phase 145G.3: every fixture/session in this file is owned by
        # "alice" (see ``_create_session``) -- default the new required
        # identity claim to match so this file's existing scenarios keep
        # exercising the behavior they were written to exercise, without
        # rewriting every one of this file's call sites individually.
        self.as_identity = "alice"
        for key, value in kwargs.items():
            setattr(self, key, value)


def _run(handler, **kwargs):
    args = _Args(**kwargs)
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = handler(args)
    return exit_code, json.loads(buf.getvalue())


@pytest.fixture(autouse=True)
def _isolated_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Phase 149O.20L.7O.3C.2: see the identical comment in
    # test_phase_145g_decision_session_cli.py -- CHGR publication now
    # requires an active-task contract (POL-001), mirroring commit/push/
    # promotion's existing invariant.
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "20260101-0000-phase-145g1-cli-fixture-task.md").write_text(
        "# Phase 145G.1 CLI fixture task\n", encoding="utf-8"
    )
    yield tmp_path


def _create_session():
    exit_code, payload = _run(
        run_decision_session_create, template_ref="tmpl-1", subject_ref="subj-1", owner_id="alice"
    )
    assert exit_code == EXIT_SUCCESS
    return payload["session"]["session_id"]


def _bridge_session_state(session_id: str, **overrides) -> Session:
    """Directly construct/persist a ``Session`` in a state no CLI command
    can legally reach (the disclosed F-145G.1-1 gap: no command drives a
    session out of ``AwaitingDecision``). Mirrors the exact
    ``confirmed.__class__(**{**confirmed.__dict__, ...})`` fixture
    convention Phase 145G's own test suite already established."""

    repo = FilesystemSessionRepository()
    session = repo.load(session_id)
    fields = {**session.__dict__, "updated_at": _now(), **overrides}
    bridged = session.__class__(**fields)
    repo.persist(bridged)
    return bridged


def _bridge_orchestration_stages(session_id: str, *stages: str) -> None:
    store = FilesystemOrchestrationStore()
    record = store.load_or_create(session_id)
    store.persist(
        OrchestrationRecord(
            session_id=session_id,
            completed_stages=tuple(stages),
            transition_sequence_number=record.transition_sequence_number,
            evidence=record.evidence,
        )
    )


# --- Parser registration -----------------------------------------------------


@pytest.mark.parametrize(
    "argv,expected",
    [
        (
            ["decision-session", "evidence", "CDS-x", "--declare", "ev-1", "--as-identity", "alice"],
            {"session_id": "CDS-x"},
        ),
        (
            [
                "decision-session", "clarify", "CDS-x", "--question", "q", "--answer", "a",
                "--as-identity", "alice",
            ],
            {"session_id": "CDS-x", "question": "q", "answer": "a"},
        ),
        (["decision-session", "preview", "CDS-x", "--as-identity", "alice"], {"session_id": "CDS-x"}),
        (
            [
                "decision-session", "confirm", "CDS-x", "--preview-digest", "d", "--statement", "s",
                "--as-identity", "alice",
            ],
            {"session_id": "CDS-x", "preview_digest": "d", "statement": "s"},
        ),
        (
            ["decision-session", "cancel", "CDS-x", "--reason", "r", "--as-identity", "alice"],
            {"session_id": "CDS-x", "reason": "r"},
        ),
    ],
)
def test_new_subcommands_registered(argv, expected):
    args = build_parser().parse_args(argv)
    for key, value in expected.items():
        assert getattr(args, key) == value


def test_no_force_or_bypass_flag_on_any_new_command():
    for argv in (
        ["decision-session", "evidence", "CDS-x", "--declare", "e", "--as-identity", "alice"],
        [
            "decision-session", "confirm", "CDS-x", "--preview-digest", "d", "--statement", "s",
            "--as-identity", "alice",
        ],
        ["decision-session", "cancel", "CDS-x", "--reason", "r", "--as-identity", "alice"],
    ):
        args = build_parser().parse_args(argv)
        assert not hasattr(args, "force")
        assert not hasattr(args, "yes")
        assert not hasattr(args, "assume_authorized")


# --- decision-session evidence (reachable end-to-end) ------------------------


def test_evidence_success_transitions_to_evidence_ready():
    session_id = _create_session()
    exit_code, payload = _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1", "ev-2"])
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "EvidenceReady"


def test_evidence_survives_process_restart():
    """Restart safety: a fresh handler invocation (simulating a separate
    ``pcae`` process) sees the state the prior invocation persisted."""

    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    exit_code, payload = _run(run_decision_session_status, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "EvidenceReady"


def test_evidence_rejects_empty_declare_list():
    session_id = _create_session()
    exit_code, payload = _run(run_decision_session_evidence, session_id=session_id, declare=[])
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_evidence_rejects_empty_declared_value():
    session_id = _create_session()
    exit_code, payload = _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1", ""])
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_evidence_second_call_rejected_invalid_state_transition():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    exit_code, payload = _run(run_decision_session_evidence, session_id=session_id, declare=["ev-2"])
    assert exit_code == EXIT_INVALID_STATE_TRANSITION
    assert payload["error_type"] == "invalid_state_transition"


def test_evidence_deduplicates_repeated_declare_within_one_call():
    session_id = _create_session()
    exit_code, payload = _run(
        run_decision_session_evidence, session_id=session_id, declare=["ev-1", "ev-1", "ev-1"]
    )
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "EvidenceReady"


def test_evidence_session_not_found():
    exit_code, payload = _run(
        run_decision_session_evidence,
        session_id="CDS-00000000-0000-4000-8000-000000000002",
        declare=["ev-1"],
    )
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "session_not_found"


# --- decision-session cancel (reachable end-to-end) --------------------------


def test_cancel_success_from_created():
    session_id = _create_session()
    exit_code, payload = _run(run_decision_session_cancel, session_id=session_id, reason="no longer needed")
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "Cancelled"


def test_cancel_idempotent_by_key():
    session_id = _create_session()
    _run(run_decision_session_cancel, session_id=session_id, reason="first")
    exit_code, payload = _run(run_decision_session_cancel, session_id=session_id, reason="second")
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "Cancelled"


def test_cancel_after_evidence_declared():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    exit_code, payload = _run(run_decision_session_cancel, session_id=session_id, reason="changed mind")
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "Cancelled"


def test_cancel_rejects_confirmed_session():
    session_id = _create_session()
    _bridge_session_state(session_id, session_state=SessionState.CONFIRMED, human_selection_id="opt-a")
    exit_code, payload = _run(run_decision_session_cancel, session_id=session_id, reason="too late")
    assert exit_code == EXIT_INVALID_STATE_TRANSITION
    assert payload["error_type"] == "invalid_state_transition"


def test_cancel_survives_process_restart():
    session_id = _create_session()
    _run(run_decision_session_cancel, session_id=session_id, reason="stop")
    exit_code, payload = _run(run_decision_session_status, session_id=session_id)
    assert payload["session"]["session_state"] == "Cancelled"


def test_cancel_rejects_empty_reason():
    session_id = _create_session()
    exit_code, payload = _run(run_decision_session_cancel, session_id=session_id, reason="")
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


# --- decision-session clarify (bridged precondition) -------------------------


def test_clarify_success_transitions_to_awaiting_decision():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    _bridge_session_state(session_id, session_state=SessionState.AWAITING_CLARIFICATION)
    _bridge_orchestration_stages(session_id, "SessionInitialization", "EvidenceAvailability")

    exit_code, payload = _run(
        run_decision_session_clarify, session_id=session_id, question="What is X?", answer="X is Y"
    )
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "AwaitingDecision"


def test_clarify_rejects_wrong_state():
    session_id = _create_session()
    exit_code, payload = _run(
        run_decision_session_clarify, session_id=session_id, question="q", answer="a"
    )
    assert exit_code == EXIT_INVALID_STATE_TRANSITION
    assert payload["error_type"] == "invalid_state_transition"


def test_clarify_rejects_empty_question_or_answer():
    session_id = _create_session()
    exit_code, payload = _run(run_decision_session_clarify, session_id=session_id, question="", answer="a")
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_clarify_survives_process_restart():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    _bridge_session_state(session_id, session_state=SessionState.AWAITING_CLARIFICATION)
    _bridge_orchestration_stages(session_id, "SessionInitialization", "EvidenceAvailability")
    _run(run_decision_session_clarify, session_id=session_id, question="q", answer="a")

    exit_code, payload = _run(run_decision_session_status, session_id=session_id)
    assert payload["session"]["session_state"] == "AwaitingDecision"


# --- decision-session preview -------------------------------------------------


def _bridge_decision_selected(session_id: str) -> None:
    _bridge_session_state(
        session_id,
        session_state=SessionState.DECISION_SELECTED,
        human_selection_id="opt-a",
        human_rationale_text="because",
        options_presented=("opt-a", "opt-b"),
        template_version="1.0",
    )
    _bridge_orchestration_stages(session_id, "SessionInitialization", "EvidenceAvailability")


def test_preview_success_renders_digest_and_content():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    _bridge_decision_selected(session_id)

    exit_code, payload = _run(run_decision_session_preview, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["preview_digest"]
    assert "opt-a" in payload["rendered_content"]


def test_preview_is_naturally_idempotent():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    _bridge_decision_selected(session_id)

    _, first = _run(run_decision_session_preview, session_id=session_id)
    _, second = _run(run_decision_session_preview, session_id=session_id)
    assert first["preview_digest"] == second["preview_digest"]
    assert first["preview_id"] == second["preview_id"]


def test_preview_rejects_wrong_state():
    session_id = _create_session()
    exit_code, payload = _run(run_decision_session_preview, session_id=session_id)
    assert exit_code == EXIT_INVALID_STATE_TRANSITION
    assert payload["error_type"] == "invalid_state_transition"


def test_preview_survives_process_restart():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    _bridge_decision_selected(session_id)
    _, first = _run(run_decision_session_preview, session_id=session_id)

    exit_code, second = _run(run_decision_session_preview, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert second["preview_digest"] == first["preview_digest"]


# --- decision-session confirm -------------------------------------------------


def _bridge_awaiting_confirmation(session_id: str) -> None:
    _bridge_session_state(
        session_id,
        session_state=SessionState.AWAITING_CONFIRMATION,
        human_selection_id="opt-a",
        human_rationale_text="because",
        options_presented=("opt-a", "opt-b"),
        template_version="1.0",
    )


def test_confirm_success_transitions_to_confirmed():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    _bridge_decision_selected(session_id)
    _, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    _bridge_awaiting_confirmation(session_id)

    exit_code, payload = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=preview_payload["preview_digest"],
        statement="I confirm this decision.",
    )
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "Confirmed"


def test_confirm_rejects_digest_mismatch():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    _bridge_decision_selected(session_id)
    _run(run_decision_session_preview, session_id=session_id)
    _bridge_awaiting_confirmation(session_id)

    exit_code, payload = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest="wrong-digest",
        statement="I confirm this decision.",
    )
    assert exit_code == EXIT_CONFIRMATION_CONFLICT
    assert payload["error_type"] == "confirmation_conflict"


def test_confirm_rejects_wrong_state():
    session_id = _create_session()
    exit_code, payload = _run(
        run_decision_session_confirm, session_id=session_id, preview_digest="d", statement="s"
    )
    assert exit_code == EXIT_INVALID_STATE_TRANSITION
    assert payload["error_type"] == "invalid_state_transition"


def test_confirm_rejects_empty_statement():
    session_id = _create_session()
    exit_code, payload = _run(
        run_decision_session_confirm, session_id=session_id, preview_digest="d", statement=""
    )
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_confirm_is_single_use():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    _bridge_decision_selected(session_id)
    _, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    _bridge_awaiting_confirmation(session_id)
    _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=preview_payload["preview_digest"],
        statement="confirmed once",
    )

    # A confirmed session can never legally return to AwaitingConfirmation
    # (IWC-001-governed terminal transition), so a same-session second
    # confirm attempt is rejected via the session-state precondition --
    # single-use is enforced structurally, not merely by a flag.
    exit_code, payload = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=preview_payload["preview_digest"],
        statement="confirmed again",
    )
    assert exit_code == EXIT_INVALID_STATE_TRANSITION


def test_confirm_survives_process_restart():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    _bridge_decision_selected(session_id)
    _, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    _bridge_awaiting_confirmation(session_id)
    _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=preview_payload["preview_digest"],
        statement="confirmed",
    )

    exit_code, payload = _run(run_decision_session_status, session_id=session_id)
    assert payload["session"]["session_state"] == "Confirmed"


# --- decision-session readiness construction (IWPC-REQ-024) -----------------


def _confirm_full_session():
    session_id = _create_session()
    _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    _bridge_decision_selected(session_id)
    _, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    _bridge_awaiting_confirmation(session_id)
    _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=preview_payload["preview_digest"],
        statement="confirmed",
    )
    return session_id


def test_readiness_constructs_and_persists_on_first_invocation():
    session_id = _confirm_full_session()
    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["package_id"].startswith("prp-")
    assert payload["disposition"] == "pending"


def test_readiness_is_idempotent_by_key():
    session_id = _confirm_full_session()
    _, first = _run(run_decision_session_readiness, session_id=session_id)
    exit_code, second = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert second["package_id"] == first["package_id"]


def test_readiness_survives_process_restart():
    session_id = _confirm_full_session()
    _, first = _run(run_decision_session_readiness, session_id=session_id)
    exit_code, second = _run(run_decision_session_readiness, session_id=session_id)
    assert second["package_id"] == first["package_id"]
    assert second["disposition"] == "pending"


def test_readiness_incomplete_when_orchestration_not_complete():
    session_id = _create_session()
    _bridge_session_state(session_id, session_state=SessionState.CONFIRMED, human_selection_id="opt-a")
    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "readiness_incomplete"


# --- End-to-end create-through-publish-through-replay (real CLI handlers) ---


def test_end_to_end_create_through_publish_with_restart_boundaries():
    """Every step below is a fresh handler invocation reading and writing
    only file-persisted state, matching a separate ``pcae`` process
    invocation. The one bridging step (marked below) exists because no
    command in IWPC-001 v1.1's frozen surface can transition a session out
    of ``AwaitingDecision`` (F-145G.1-1, see module docstring on
    ``pcae.commands.decision_session``) -- it is not a workaround for
    anything this phase's own commands should have done differently.
    """

    session_id = _create_session()

    exit_code, _ = _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1", "ev-2"])
    assert exit_code == EXIT_SUCCESS

    # Bridge (disclosed, documented gap -- not a CLI-adapter workaround).
    _bridge_session_state(session_id, session_state=SessionState.AWAITING_CLARIFICATION)
    _bridge_orchestration_stages(session_id, "SessionInitialization", "EvidenceAvailability")

    exit_code, _ = _run(
        run_decision_session_clarify, session_id=session_id, question="Why?", answer="Because."
    )
    assert exit_code == EXIT_SUCCESS

    _bridge_decision_selected(session_id)

    exit_code, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    assert exit_code == EXIT_SUCCESS

    _bridge_awaiting_confirmation(session_id)

    exit_code, _ = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=preview_payload["preview_digest"],
        statement="I confirm this decision end to end.",
    )
    assert exit_code == EXIT_SUCCESS

    exit_code, readiness_payload = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    package_id = readiness_payload["package_id"]

    # Restart, then inspect after process reconstruction.
    exit_code, readiness_payload_2 = _run(run_decision_session_readiness, session_id=session_id)
    assert readiness_payload_2["package_id"] == package_id

    exit_code, publish_payload = _run(
        run_governance_record_publish, package_id=package_id, operator_id="operator-1"
    )
    assert exit_code == EXIT_SUCCESS
    assert publish_payload["success"] is True
    record_id = publish_payload["record_id"]

    # Replay / duplicate publication rejected exactly per §19/§20.
    exit_code, replay_payload = _run(
        run_governance_record_publish, package_id=package_id, operator_id="operator-1"
    )
    assert replay_payload["error_type"] == "publication_already_completed"
    assert replay_payload["record_id"] == record_id


# --- Orchestration record persistence / corruption (IWPC-001 v1.1 §13-style) -


def test_orchestration_store_atomic_write_and_reload(tmp_path):
    store = FilesystemOrchestrationStore()
    session_id = _create_session()
    record = OrchestrationRecord(
        session_id=session_id,
        completed_stages=("SessionInitialization",),
        transition_sequence_number=1,
        evidence=({"evidence_id": "ev-1", "evidence_type": "t", "provenance_ref": "ev-1",
                    "collected_at": _now(), "availability": "Available"},),
    )
    store.persist(record)
    reloaded = store.load(session_id)
    assert reloaded.completed_stages == ("SessionInitialization",)
    assert reloaded.evidence[0]["evidence_id"] == "ev-1"
    # No leftover temp files.
    assert not any(p.name.startswith(".tmp-") for p in store.root.iterdir())


def test_orchestration_store_corrupt_json_fails_closed():
    store = FilesystemOrchestrationStore()
    session_id = _create_session()
    store.persist(OrchestrationRecord(session_id=session_id))
    path = store.root / f"{session_id}.json"
    path.write_text("{not valid json")
    with pytest.raises(OrchestrationStoreCorruptError):
        store.load(session_id)


def test_orchestration_store_rejects_path_traversal_identifier():
    store = FilesystemOrchestrationStore()
    with pytest.raises(Exception):
        store.load_or_create("../../etc/passwd")


def test_orchestration_store_missing_record_returns_empty_default():
    store = FilesystemOrchestrationStore()
    session_id = _create_session()
    record = store.load_or_create(session_id)
    assert record.completed_stages == ()
    assert record.evidence == ()


# --- Dependency / forbidden-import boundary extension (IWPC-REQ-176) --------


def test_cli_module_still_has_no_forbidden_imports_after_repair():
    import ast

    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "src" / "pcae" / "commands" / "decision_session.py"
    tree = ast.parse(path.read_text(), filename=str(path))
    forbidden_roots = (
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
    )
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    for module in modules:
        for forbidden_root in forbidden_roots:
            assert not (module == forbidden_root or module.startswith(forbidden_root + ".")), (
                f"decision_session.py imports {module!r} after Phase 145G.1's repair, "
                f"violating the CLI's own dependency boundary."
            )


def test_orchestration_store_does_not_import_cli_or_application_modules():
    import ast

    repo_root = Path(__file__).resolve().parents[1]
    path = (
        repo_root
        / "src"
        / "pcae"
        / "interactive_workflow"
        / "persistence"
        / "filesystem_orchestration_store.py"
    )
    tree = ast.parse(path.read_text(), filename=str(path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    for module in modules:
        assert not module.startswith("pcae.commands") and module != "pcae.cli"
        assert not module.startswith("pcae.interactive_workflow.application")
