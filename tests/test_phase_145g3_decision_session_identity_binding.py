"""Phase 145G.3 unit tests: decision-session identity-bound resumption
enforcement (closes F-145G.2V-1, IWC-REQ-022/IWC-REQ-151).

Covers: the new required ``--as-identity`` claim on every mutating
``decision-session`` command (``evidence``, ``select``, ``clarify``,
``preview``, ``confirm``, ``cancel``, ``readiness``); exact-match
enforcement (no case-folding, no whitespace normalization); structural
(CLI-layer) rejection of missing/malformed claims distinct from
application-layer rejection of well-formed-but-wrong claims; identity
enforcement ahead of every idempotent early-return path (`cancel`,
`readiness`); `status`/`create` deliberately unaffected; a genuine,
owner-vs-impostor CLI-only end-to-end reproduction; and the closed
error-taxonomy/exit-code additions.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

import pytest

from pcae.cli import build_parser
from pcae.commands.decision_session import (
    EXIT_GENERIC_DOMAIN_FAILURE,
    EXIT_IDENTITY_BINDING_MISMATCH,
    EXIT_SUCCESS,
    build_application_context,
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
from pcae.interactive_workflow.application.errors import SessionIdentityMismatchApplicationError
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.persistence.filesystem_repository import FilesystemSessionRepository


class _Args:
    def __init__(self, **kwargs):
        self.json = True
        self.rationale = None
        self.conditions = None
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
    yield tmp_path


def _create_session(owner_id="alice"):
    exit_code, payload = _run(
        run_decision_session_create, template_ref="tmpl-1", subject_ref="subj-1", owner_id=owner_id
    )
    assert exit_code == EXIT_SUCCESS
    return payload["session"]["session_id"]


def _evidence_ready(owner_id="alice"):
    session_id = _create_session(owner_id)
    exit_code, _ = _run(
        run_decision_session_evidence, session_id=session_id, declare=["ev-1"], as_identity=owner_id
    )
    assert exit_code == EXIT_SUCCESS
    return session_id


def _decision_selected(owner_id="alice"):
    session_id = _evidence_ready(owner_id)
    exit_code, _ = _run(
        run_decision_session_select,
        session_id=session_id,
        option_id="opt-a",
        options_presented=["opt-a", "opt-b"],
        template_version="v1",
        as_identity=owner_id,
    )
    assert exit_code == EXIT_SUCCESS
    return session_id


def _awaiting_confirmation(owner_id="alice"):
    session_id = _decision_selected(owner_id)
    exit_code, payload = _run(
        run_decision_session_preview, session_id=session_id, as_identity=owner_id
    )
    assert exit_code == EXIT_SUCCESS
    return session_id, payload["preview_digest"]


def _confirmed(owner_id="alice"):
    session_id, digest = _awaiting_confirmation(owner_id)
    exit_code, _ = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=digest,
        statement="confirmed",
        as_identity=owner_id,
    )
    assert exit_code == EXIT_SUCCESS
    return session_id


# --- CLI parser: --as-identity required on every mutating command, absent
#     from create/status ------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["decision-session", "evidence", "CDS-x", "--declare", "e"],
        [
            "decision-session", "select", "CDS-x", "--option-id", "a",
            "--options-presented", "a", "--template-version", "v1",
        ],
        ["decision-session", "clarify", "CDS-x", "--question", "q", "--answer", "a"],
        ["decision-session", "preview", "CDS-x"],
        ["decision-session", "confirm", "CDS-x", "--preview-digest", "d", "--statement", "s"],
        ["decision-session", "cancel", "CDS-x", "--reason", "r"],
        ["decision-session", "readiness", "CDS-x"],
    ],
)
def test_as_identity_is_required_on_every_mutating_command(argv):
    with pytest.raises(SystemExit):
        build_parser().parse_args(argv)


def test_create_and_status_have_no_as_identity_flag():
    for argv, subcommand_index in (
        (["decision-session", "create", "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o"], 2),
        (["decision-session", "status", "CDS-x"], 2),
    ):
        args = build_parser().parse_args(argv)
        assert not hasattr(args, "as_identity")


# --- Application-layer enforcement: exact match, no normalization -----------


def test_select_rejects_case_different_claim():
    session_id = _evidence_ready(owner_id="alice")
    exit_code, payload = _run(
        run_decision_session_select,
        session_id=session_id,
        option_id="opt-a",
        options_presented=["opt-a"],
        template_version="v1",
        as_identity="Alice",
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH
    assert payload["error_type"] == "identity_binding_mismatch"


def test_select_rejects_claim_with_incidental_whitespace():
    session_id = _evidence_ready(owner_id="alice")
    exit_code, payload = _run(
        run_decision_session_select,
        session_id=session_id,
        option_id="opt-a",
        options_presented=["opt-a"],
        template_version="v1",
        as_identity=" alice ",
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH
    assert payload["error_type"] == "identity_binding_mismatch"


def test_select_succeeds_with_exact_matching_claim():
    session_id = _evidence_ready(owner_id="alice")
    exit_code, payload = _run(
        run_decision_session_select,
        session_id=session_id,
        option_id="opt-a",
        options_presented=["opt-a"],
        template_version="v1",
        as_identity="alice",
    )
    assert exit_code == EXIT_SUCCESS


# --- Structural (CLI-layer) vs. semantic (application-layer) failures ------


def test_evidence_rejects_empty_as_identity_as_invalid_request():
    session_id = _create_session("alice")
    exit_code, payload = _run(
        run_decision_session_evidence, session_id=session_id, declare=["e"], as_identity=""
    )
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_evidence_rejects_control_character_as_identity_as_invalid_request():
    session_id = _create_session("alice")
    exit_code, payload = _run(
        run_decision_session_evidence, session_id=session_id, declare=["e"], as_identity="alice\nmallory"
    )
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_evidence_rejects_oversized_as_identity_as_invalid_request():
    session_id = _create_session("alice")
    exit_code, payload = _run(
        run_decision_session_evidence, session_id=session_id, declare=["e"], as_identity="a" * 513
    )
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_evidence_rejects_well_formed_wrong_claim_as_identity_mismatch():
    session_id = _create_session("alice")
    exit_code, payload = _run(
        run_decision_session_evidence, session_id=session_id, declare=["e"], as_identity="mallory"
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH
    assert payload["error_type"] == "identity_binding_mismatch"
    assert payload["session_id"] == session_id


def test_unicode_identity_is_accepted_structurally_and_compared_exactly():
    session_id = _create_session("étienne")  # "étienne"
    exit_code, _ = _run(
        run_decision_session_evidence, session_id=session_id, declare=["e"], as_identity="étienne"
    )
    assert exit_code == EXIT_SUCCESS


# --- status: deliberately unaffected (read-only, not resumption) -----------


def test_status_succeeds_for_any_caller_no_identity_flag_needed():
    session_id = _create_session("alice")
    exit_code, payload = _run(run_decision_session_status, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "Created"


# --- Idempotent-early-return paths still enforce identity ------------------


def test_cancel_rejects_mismatched_identity_even_against_already_cancelled_session():
    session_id = _create_session("alice")
    exit_code, _ = _run(
        run_decision_session_cancel, session_id=session_id, reason="first", as_identity="alice"
    )
    assert exit_code == EXIT_SUCCESS

    # Session is now Cancelled -- cancel is normally idempotent-by-key, but
    # a mismatched identity must still be rejected, not silently accepted
    # via the idempotent early-return path.
    exit_code, payload = _run(
        run_decision_session_cancel, session_id=session_id, reason="second", as_identity="mallory"
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH
    assert payload["error_type"] == "identity_binding_mismatch"

    # The correct owner may still replay the idempotent cancel.
    exit_code, payload = _run(
        run_decision_session_cancel, session_id=session_id, reason="second", as_identity="alice"
    )
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["session_state"] == "Cancelled"


def test_readiness_rejects_mismatched_identity_even_on_cache_hit_path():
    session_id = _confirmed(owner_id="alice")
    exit_code, first = _run(
        run_decision_session_readiness, session_id=session_id, as_identity="alice"
    )
    assert exit_code == EXIT_SUCCESS

    # A second `readiness` call would normally hit the idempotent-by-key
    # "existing package" branch -- confirm a mismatched identity is still
    # rejected rather than transparently returning the cached package.
    exit_code, payload = _run(
        run_decision_session_readiness, session_id=session_id, as_identity="mallory"
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH
    assert payload["error_type"] == "identity_binding_mismatch"

    exit_code, second = _run(
        run_decision_session_readiness, session_id=session_id, as_identity="alice"
    )
    assert exit_code == EXIT_SUCCESS
    assert second["package_id"] == first["package_id"]


# --- Every mutating command rejects a mismatched identity -------------------


def test_clarify_rejects_mismatched_identity():
    session_id = _evidence_ready(owner_id="alice")
    repo = FilesystemSessionRepository()
    session = repo.load(session_id)
    bridged = session.__class__(
        **{**session.__dict__, "session_state": SessionState.AWAITING_CLARIFICATION}
    )
    repo.persist(bridged)

    exit_code, payload = _run(
        run_decision_session_clarify,
        session_id=session_id,
        question="q",
        answer="a",
        as_identity="mallory",
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH
    assert payload["error_type"] == "identity_binding_mismatch"


def test_preview_rejects_mismatched_identity():
    session_id = _decision_selected(owner_id="alice")
    exit_code, payload = _run(
        run_decision_session_preview, session_id=session_id, as_identity="mallory"
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH
    assert payload["error_type"] == "identity_binding_mismatch"


def test_confirm_rejects_mismatched_identity():
    session_id, digest = _awaiting_confirmation(owner_id="alice")
    exit_code, payload = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=digest,
        statement="mallory confirms",
        as_identity="mallory",
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH
    assert payload["error_type"] == "identity_binding_mismatch"

    # Session must remain untouched (still AwaitingConfirmation, not
    # Confirmed by the impostor).
    context = build_application_context()
    session = context.session_service.load_session(session_id)
    assert session.session_state == SessionState.AWAITING_CONFIRMATION


# --- Session-not-found takes precedence over identity mismatch -------------


def test_identity_mismatch_never_masks_session_not_found():
    exit_code, payload = _run(
        run_decision_session_evidence,
        session_id="CDS-00000000-0000-4000-8000-000000000000",
        declare=["e"],
        as_identity="anyone",
    )
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "session_not_found"


# --- Genuine CLI-only owner-vs-impostor end-to-end reproduction ------------


def test_owner_reaches_publication_impostor_is_rejected_at_every_step():
    """Full create -> evidence -> select -> preview -> confirm -> readiness
    chain succeeds for the true owner; the identical sequence attempted by
    an impostor identity is rejected, deterministically, at every single
    step, and never mutates the session."""

    session_id = _create_session("alice")

    exit_code, payload = _run(
        run_decision_session_evidence, session_id=session_id, declare=["e"], as_identity="mallory"
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH

    exit_code, payload = _run(
        run_decision_session_evidence, session_id=session_id, declare=["e"], as_identity="alice"
    )
    assert exit_code == EXIT_SUCCESS

    exit_code, payload = _run(
        run_decision_session_select,
        session_id=session_id,
        option_id="opt-a",
        options_presented=["opt-a"],
        template_version="v1",
        as_identity="mallory",
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH

    exit_code, payload = _run(
        run_decision_session_select,
        session_id=session_id,
        option_id="opt-a",
        options_presented=["opt-a"],
        template_version="v1",
        as_identity="alice",
    )
    assert exit_code == EXIT_SUCCESS

    exit_code, payload = _run(
        run_decision_session_preview, session_id=session_id, as_identity="mallory"
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH

    exit_code, payload = _run(
        run_decision_session_preview, session_id=session_id, as_identity="alice"
    )
    assert exit_code == EXIT_SUCCESS
    digest = payload["preview_digest"]

    exit_code, payload = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=digest,
        statement="mallory confirms",
        as_identity="mallory",
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH

    exit_code, payload = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=digest,
        statement="alice confirms",
        as_identity="alice",
    )
    assert exit_code == EXIT_SUCCESS

    exit_code, payload = _run(
        run_decision_session_readiness, session_id=session_id, as_identity="mallory"
    )
    assert exit_code == EXIT_IDENTITY_BINDING_MISMATCH

    exit_code, payload = _run(
        run_decision_session_readiness, session_id=session_id, as_identity="alice"
    )
    assert exit_code == EXIT_SUCCESS
    assert payload["package_id"].startswith("prp-")


# --- Direct application-service call, bypassing CLI structural checks -----


def test_application_service_itself_enforces_identity_independent_of_cli():
    session_id = _create_session("alice")
    context = build_application_context()
    with pytest.raises(SessionIdentityMismatchApplicationError):
        context.session_service.submit_evidence(session_id, ["e"], caller_identity="mallory")

    session = context.session_service.submit_evidence(session_id, ["e"], caller_identity="alice")
    assert session.session_state == SessionState.EVIDENCE_READY
