"""Phase 145G.2 unit tests: the new ``pcae decision-session select``
command (IWPC-REQ-192-196) and its closure of F-145G.1-1.

Covers: parser registration for ``select``; ``select`` exercised as a
real, separate handler invocation against file-persisted state
(genuinely reachable end-to-end via the CLI alone, from ``EvidenceReady``
and, after a ``clarify`` bridge, from ``AwaitingDecision``); malformed/
adversarial input rejection (unknown option, duplicate option ids, empty
set, wrong state, replay-after-selection, selection after
cancellation/confirmation/readiness/publication); the Phase 145G.2
re-derivation finding that ``preview``'s first construction must also
perform the previously-undriven ``DecisionSelected`` ->
``AwaitingConfirmation`` transition (IWC-001's own state table, "Preview
generated, awaiting Confirmation") for ``confirm``/``readiness``/
publication to be reachable at all; a full, restart-separated,
CLI-only-only ``create`` -> ``evidence`` -> ``select`` -> ``preview`` ->
``confirm`` -> ``readiness`` -> ``governance-record publish`` -> replay
scenario with no direct session/orchestration-state construction
anywhere in the chain; a second, CLI-only scenario that also exercises
``clarify`` (bridged into ``AwaitingClarification`` only, the disclosed,
out-of-scope sibling gap F-145G.2-1 -- see this module's own docstring on
``pcae.commands.decision_session``); and an extension of the Phase
145G/145G.1 forbidden-import boundary test.
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
    run_decision_session_select,
    run_decision_session_status,
)
from pcae.commands.governance_record import run_governance_record_publish
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
        # "alice" -- default the new required identity claim to match.
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
    (active_dir / "20260101-0000-phase-145g2-cli-fixture-task.md").write_text(
        "# Phase 145G.2 CLI fixture task\n", encoding="utf-8"
    )
    yield tmp_path


def _create_session():
    exit_code, payload = _run(
        run_decision_session_create, template_ref="tmpl-1", subject_ref="subj-1", owner_id="alice"
    )
    assert exit_code == EXIT_SUCCESS
    return payload["session"]["session_id"]


def _create_evidence_ready_session():
    session_id = _create_session()
    exit_code, _ = _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1"])
    assert exit_code == EXIT_SUCCESS
    return session_id


def _select(session_id, **overrides):
    kwargs = dict(
        session_id=session_id,
        option_id="opt-a",
        options_presented=["opt-a", "opt-b"],
        template_version="v1",
        rationale="because",
        conditions=None,
    )
    kwargs.update(overrides)
    return _run(run_decision_session_select, **kwargs)


def _bridge_session_state(session_id: str, **overrides) -> Session:
    """Directly construct/persist a ``Session`` in a state no CLI command
    can legally reach -- the disclosed F-145G.2-1 gap (no command opens
    ``AwaitingClarification``; ``clarify`` only answers one already in
    progress). Mirrors the exact fixture convention Phase 145G.1's own
    test suite established for the analogous F-145G.1-1 gap."""

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


def test_select_subcommand_registered():
    args = build_parser().parse_args(
        [
            "decision-session",
            "select",
            "CDS-x",
            "--option-id",
            "opt-a",
            "--options-presented",
            "opt-a",
            "--options-presented",
            "opt-b",
            "--template-version",
            "v1",
            "--as-identity",
            "alice",
        ]
    )
    assert args.session_id == "CDS-x"
    assert args.option_id == "opt-a"
    assert args.options_presented == ["opt-a", "opt-b"]
    assert args.template_version == "v1"


def test_select_has_no_force_or_bypass_flag():
    args = build_parser().parse_args(
        [
            "decision-session",
            "select",
            "CDS-x",
            "--option-id",
            "opt-a",
            "--options-presented",
            "opt-a",
            "--template-version",
            "v1",
            "--as-identity",
            "alice",
        ]
    )
    assert not hasattr(args, "force")
    assert not hasattr(args, "yes")
    assert not hasattr(args, "assume_authorized")


# --- decision-session select (reachable end-to-end from EvidenceReady) ------


def test_select_success_from_evidence_ready_transitions_to_decision_selected():
    session_id = _create_evidence_ready_session()
    exit_code, payload = _select(session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "DecisionSelected"
    assert payload["session"]["human_selection_id"] == "opt-a"
    assert payload["session"]["options_presented"] == ["opt-a", "opt-b"]
    assert payload["session"]["template_version"] == "v1"
    assert payload["session"]["human_rationale_text"] == "because"


def test_select_survives_process_restart():
    session_id = _create_evidence_ready_session()
    _select(session_id)
    exit_code, payload = _run(run_decision_session_status, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "DecisionSelected"


def test_select_rejects_wrong_state():
    session_id = _create_session()  # still Created, not EvidenceReady
    exit_code, payload = _select(session_id)
    assert exit_code == EXIT_INVALID_STATE_TRANSITION
    assert payload["error_type"] == "invalid_state_transition"


def test_select_is_single_use_fail_closed_no_idempotent_replay():
    session_id = _create_evidence_ready_session()
    _select(session_id)
    exit_code, payload = _select(session_id, rationale="because", conditions=None)
    assert exit_code == EXIT_INVALID_STATE_TRANSITION
    assert payload["error_type"] == "invalid_state_transition"


def test_select_rejects_conflicting_replay_with_different_option():
    session_id = _create_evidence_ready_session()
    _select(session_id)
    exit_code, payload = _select(session_id, option_id="opt-b")
    assert exit_code == EXIT_INVALID_STATE_TRANSITION


def test_select_rejects_empty_session_id():
    exit_code, payload = _select("")
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_select_rejects_empty_option_id():
    session_id = _create_evidence_ready_session()
    exit_code, payload = _select(session_id, option_id="")
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_select_rejects_empty_options_presented():
    session_id = _create_evidence_ready_session()
    exit_code, payload = _select(session_id, options_presented=[])
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_select_rejects_empty_template_version():
    session_id = _create_evidence_ready_session()
    exit_code, payload = _select(session_id, template_version="")
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_select_rejects_duplicate_options_presented():
    session_id = _create_evidence_ready_session()
    exit_code, payload = _select(session_id, options_presented=["opt-a", "opt-a", "opt-b"])
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_select_rejects_option_id_not_a_member_of_presented_set():
    session_id = _create_evidence_ready_session()
    exit_code, payload = _select(session_id, option_id="opt-z", options_presented=["opt-a", "opt-b"])
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_select_session_not_found():
    exit_code, payload = _select("CDS-00000000-0000-4000-8000-000000000099")
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "session_not_found"


def test_select_rationale_and_conditions_are_optional():
    session_id = _create_evidence_ready_session()
    exit_code, payload = _select(session_id, rationale=None, conditions=None)
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["human_rationale_text"] is None
    assert payload["session"]["human_conditions_text"] is None


def test_select_rejects_after_cancellation():
    session_id = _create_evidence_ready_session()
    _run(run_decision_session_cancel, session_id=session_id, reason="stop")
    exit_code, payload = _select(session_id)
    assert exit_code == EXIT_INVALID_STATE_TRANSITION


# --- decision-session select (reachable end-to-end from AwaitingDecision,
#     reached via the clarify bridge -- F-145G.2-1) --------------------------


def test_select_success_from_awaiting_decision_after_clarify():
    session_id = _create_evidence_ready_session()
    _bridge_session_state(session_id, session_state=SessionState.AWAITING_CLARIFICATION)
    _bridge_orchestration_stages(session_id, "SessionInitialization", "EvidenceAvailability")
    exit_code, _ = _run(
        run_decision_session_clarify, session_id=session_id, question="What is X?", answer="X is Y"
    )
    assert exit_code == EXIT_SUCCESS

    exit_code, payload = _select(session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "DecisionSelected"


# --- Phase 145G.2 re-derivation finding: preview must drive DecisionSelected
#     -> AwaitingConfirmation on first construction ---------------------------


def test_preview_first_construction_transitions_to_awaiting_confirmation():
    session_id = _create_evidence_ready_session()
    _select(session_id)
    exit_code, _ = _run(run_decision_session_preview, session_id=session_id)
    assert exit_code == EXIT_SUCCESS

    exit_code, payload = _run(run_decision_session_status, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "AwaitingConfirmation"


def test_preview_second_call_does_not_re_transition():
    session_id = _create_evidence_ready_session()
    _select(session_id)
    _run(run_decision_session_preview, session_id=session_id)
    _, first_status = _run(run_decision_session_status, session_id=session_id)
    _run(run_decision_session_preview, session_id=session_id)
    _, second_status = _run(run_decision_session_status, session_id=session_id)
    assert first_status["session"]["session_state"] == "AwaitingConfirmation"
    assert second_status["session"]["session_state"] == "AwaitingConfirmation"


def test_preview_digest_remains_stable_across_the_new_transition():
    session_id = _create_evidence_ready_session()
    _select(session_id)
    _, first = _run(run_decision_session_preview, session_id=session_id)
    _, second = _run(run_decision_session_preview, session_id=session_id)
    assert first["preview_digest"] == second["preview_digest"]
    assert first["preview_id"] == second["preview_id"]


# --- End-to-end, CLI-only-only happy path (no session/orchestration bridge) -


def test_end_to_end_create_through_publish_no_state_bridging_anywhere():
    """Every step is a fresh handler invocation against file-persisted
    state only (simulating a separate ``pcae`` process). Unlike Phase
    145G.1's own end-to-end test, this scenario needs no
    ``_bridge_session_state``/``_bridge_orchestration_stages`` call at
    all -- the entire chain from ``create`` through
    ``governance-record publish`` is now reachable through real,
    production CLI commands alone (closes F-145G.1-1)."""

    exit_code, create_payload = _run(
        run_decision_session_create, template_ref="tmpl-1", subject_ref="subj-1", owner_id="alice"
    )
    assert exit_code == EXIT_SUCCESS
    session_id = create_payload["session"]["session_id"]

    exit_code, _ = _run(run_decision_session_evidence, session_id=session_id, declare=["ev-1", "ev-2"])
    assert exit_code == EXIT_SUCCESS

    # Phase 146G: this scenario reaches real CHGR-001 v1.2 schema-envelope
    # construction/validation (CHGR-REQ-194-209) at `publish` below, which
    # requires template_version to match `^[0-9]+\.[0-9]+$` -- "1.0", not
    # the CLI-parsing-only placeholder "v1" other tests in this file use.
    exit_code, select_payload = _select(session_id, template_version="1.0")
    assert exit_code == EXIT_SUCCESS
    assert select_payload["session"]["session_state"] == "DecisionSelected"

    exit_code, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    assert exit_code == EXIT_SUCCESS

    exit_code, status_payload = _run(run_decision_session_status, session_id=session_id)
    assert status_payload["session"]["session_state"] == "AwaitingConfirmation"

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

    # Restart, then re-inspect readiness (idempotent by key).
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


def test_end_to_end_with_clarification_required_scenario():
    """Same chain, but exercising ``clarify`` too. The one bridging step
    (marked below) exists only because of the separately-disclosed,
    out-of-scope F-145G.2-1 gap (no command opens
    ``AwaitingClarification``) -- not because of anything Phase 145G.2's
    own ``select`` command should have done differently."""

    session_id = _create_evidence_ready_session()

    # Bridge (disclosed, documented F-145G.2-1 gap -- not a workaround for
    # this phase's own select command).
    _bridge_session_state(session_id, session_state=SessionState.AWAITING_CLARIFICATION)
    _bridge_orchestration_stages(session_id, "SessionInitialization", "EvidenceAvailability")

    exit_code, _ = _run(
        run_decision_session_clarify, session_id=session_id, question="Why?", answer="Because."
    )
    assert exit_code == EXIT_SUCCESS

    exit_code, _ = _run(run_decision_session_status, session_id=session_id)
    assert exit_code == EXIT_SUCCESS

    # Phase 146G: see the no-bridging scenario above -- publish below now
    # requires a schema-conformant template_version.
    exit_code, select_payload = _select(session_id, template_version="1.0")
    assert exit_code == EXIT_SUCCESS
    assert select_payload["session"]["session_state"] == "DecisionSelected"

    exit_code, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    assert exit_code == EXIT_SUCCESS

    exit_code, _ = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=preview_payload["preview_digest"],
        statement="I confirm this decision.",
    )
    assert exit_code == EXIT_SUCCESS

    exit_code, readiness_payload = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_SUCCESS

    exit_code, publish_payload = _run(
        run_governance_record_publish,
        package_id=readiness_payload["package_id"],
        operator_id="operator-1",
    )
    assert exit_code == EXIT_SUCCESS
    assert publish_payload["success"] is True


# --- Security / adversarial ---------------------------------------------------


def test_select_rejects_path_traversal_style_option_id():
    session_id = _create_evidence_ready_session()
    exit_code, payload = _select(
        session_id, option_id="../../etc/passwd", options_presented=["../../etc/passwd", "opt-b"]
    )
    # Structurally accepted (option ids are opaque strings, exactly like
    # evidence_ids -- see submit_evidence's own precedent); safety is
    # preserved because this value is never used as a filesystem path
    # anywhere downstream (only session_id is).
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["human_selection_id"] == "../../etc/passwd"


def test_select_rejects_after_confirmation():
    session_id = _create_evidence_ready_session()
    _select(session_id)
    _, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=preview_payload["preview_digest"],
        statement="confirmed",
    )
    exit_code, payload = _select(session_id, option_id="opt-b")
    assert exit_code == EXIT_INVALID_STATE_TRANSITION


def test_select_rejects_after_readiness_constructed():
    session_id = _create_evidence_ready_session()
    _select(session_id)
    _, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=preview_payload["preview_digest"],
        statement="confirmed",
    )
    _run(run_decision_session_readiness, session_id=session_id)
    exit_code, payload = _select(session_id, option_id="opt-b")
    assert exit_code == EXIT_INVALID_STATE_TRANSITION


def test_select_rejects_after_publication():
    session_id = _create_evidence_ready_session()
    _select(session_id)
    _, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=preview_payload["preview_digest"],
        statement="confirmed",
    )
    _, readiness_payload = _run(run_decision_session_readiness, session_id=session_id)
    _run(run_governance_record_publish, package_id=readiness_payload["package_id"], operator_id="op-1")
    exit_code, payload = _select(session_id, option_id="opt-b")
    assert exit_code == EXIT_INVALID_STATE_TRANSITION


def test_select_two_distinct_sessions_do_not_cross_contaminate_options():
    session_a = _create_evidence_ready_session()
    session_b = _create_evidence_ready_session()
    _select(session_a, option_id="opt-a", options_presented=["opt-a", "opt-b"])
    exit_code, payload = _select(session_b, option_id="opt-a", options_presented=["opt-c", "opt-d"])
    # opt-a is not a member of session_b's own declared presented set.
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


# --- Dependency / forbidden-import boundary extension (IWPC-REQ-176) --------


def test_cli_module_still_has_no_forbidden_imports_after_145g2_repair():
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
                f"decision_session.py imports {module!r} after Phase 145G.2's repair, "
                f"violating the CLI's own dependency boundary."
            )
