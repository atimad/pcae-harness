"""Phase 145G.2V independent verification (partial: contract-diff,
state-machine, identity/authority, option-binding, replay/mutation
slices only -- persistence/application/CLI/e2e/security/regression are
covered by a parallel verification effort).

These tests were written from an INDEPENDENT re-derivation of expected
behavior from IWC-001 v1.2's frozen ten-state table (§4.4), IWC-REQ-018/
051/052/063 (human-only selection, no inference), IWC-REQ-022 (identity-
bound resumption), and IWPC-001 v1.2 §5.3 (IWPC-REQ-192-196), BEFORE
reading Phase 145G.2's own canonical report -- not written to reproduce
that report's own test suite (``test_phase_145g2_decision_selection_cli_
repair.py``), which is treated here as a claim to be checked, not a
source of truth.

Uses the real CLI handlers (``pcae.commands.decision_session``) and the
real ``SessionApplicationService`` -- no monkeypatching of production
collaborators.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from datetime import datetime, timezone

import pytest

from pcae.commands.decision_session import (
    EXIT_GENERIC_DOMAIN_FAILURE,
    EXIT_INVALID_STATE_TRANSITION,
    EXIT_SUCCESS,
    build_application_context,
    run_decision_session_cancel,
    run_decision_session_confirm,
    run_decision_session_create,
    run_decision_session_evidence,
    run_decision_session_preview,
    run_decision_session_readiness,
    run_decision_session_select,
    run_decision_session_status,
)
from pcae.commands.governance_record import run_governance_record_publish
from pcae.interactive_workflow.application.errors import SessionInvalidTransitionApplicationError
from pcae.interactive_workflow.models.session import Session, SessionState
from pcae.interactive_workflow.persistence.filesystem_orchestration_store import (
    FilesystemOrchestrationStore,
    OrchestrationRecord,
)
from pcae.interactive_workflow.persistence.filesystem_repository import FilesystemSessionRepository
from pcae.interactive_workflow.state_machine.transitions import TRANSITION_TABLE


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _Args:
    def __init__(self, **kwargs):
        self.json = True
        # Phase 145G.3: every fixture/session in this file is owned by
        # "alice" (the default in ``_create_session``/``_evidence_ready``)
        # -- default the new required identity claim to match.
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
    yield tmp_path


def _create_session(owner_id="alice"):
    exit_code, payload = _run(
        run_decision_session_create, template_ref="tmpl-1", subject_ref="subj-1", owner_id=owner_id
    )
    assert exit_code == EXIT_SUCCESS
    return payload["session"]["session_id"]


def _evidence_ready(session_id=None, owner_id="alice"):
    session_id = session_id or _create_session(owner_id)
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
    """Direct session-state construction, used ONLY to reach states no
    real CLI-only sequence can produce (Cancelled/Expired/Abandoned/
    AwaitingClarification/Confirmed reached without going through the
    full happy path), so every one of the ten states can be attacked
    with ``select``, matching the task's explicit requirement to test
    "states not explicitly enumerated" in the contract."""

    repo = FilesystemSessionRepository()
    session = repo.load(session_id)
    updated = Session(
        session_id=session.session_id,
        owner_identity=overrides.pop("owner_identity", session.owner_identity),
        template_ref=session.template_ref,
        subject_ref=session.subject_ref,
        session_state=overrides.pop("session_state"),
        schema_version=session.schema_version,
        created_at=session.created_at,
        updated_at=_now(),
        human_selection_id=overrides.pop("human_selection_id", session.human_selection_id),
        human_rationale_text=session.human_rationale_text,
        human_conditions_text=session.human_conditions_text,
        disclosure_acknowledgements=session.disclosure_acknowledgements,
        template_version=overrides.pop("template_version", session.template_version),
        options_presented=overrides.pop("options_presented", session.options_presented),
        decision_maker_evidence_kind=session.decision_maker_evidence_kind,
        metadata=session.metadata,
    )
    repo.persist(updated)
    return updated


# ===========================================================================
# Part I/II: contract-diff and state-machine cross-check (TRANSITION_TABLE
# itself already verified against git history separately; this checks the
# APPLICATION LAYER's own guard matches that table exactly for `select`).
# ===========================================================================


ALL_STATES = list(SessionState)


@pytest.mark.parametrize("state", ALL_STATES)
def test_select_state_machine_matrix(state):
    """For EVERY one of the ten states, attempt `select` via the real CLI
    and confirm the result matches what IWC-001's own frozen ten-state
    table + IWPC-REQ-192 jointly require: only EvidenceReady/
    AwaitingDecision may succeed; every other state (including terminal
    states and DecisionSelected itself) must fail closed with
    invalid_state_transition."""

    session_id = _create_session()
    if state is SessionState.CREATED:
        pass  # already Created
    elif state is SessionState.EVIDENCE_READY:
        session_id = _evidence_ready(session_id)
    elif state is SessionState.AWAITING_DECISION:
        session_id = _evidence_ready(session_id)
        exit_code, _ = _select(session_id)
        # can't reach AwaitingDecision via select (it jumps straight to
        # DecisionSelected); bridge directly instead, since no other CLI
        # command opens AwaitingDecision from EvidenceReady alone.
        _bridge_session_state(session_id, session_state=SessionState.AWAITING_DECISION)
    else:
        _bridge_session_state(session_id, session_state=state)

    exit_code, payload = _select(session_id)

    if state in (SessionState.EVIDENCE_READY, SessionState.AWAITING_DECISION):
        assert exit_code == EXIT_SUCCESS, f"expected select to succeed from {state}, got {payload}"
        assert payload["session"]["session_state"] == "DecisionSelected"
    else:
        assert exit_code == EXIT_INVALID_STATE_TRANSITION, (
            f"expected select to be REJECTED from {state} with invalid_state_transition, "
            f"got exit={exit_code} payload={payload}"
        )
        assert payload["error_type"] == "invalid_state_transition"


def test_select_rejects_second_call_after_decision_selected():
    """Single-use per IWPC-REQ-193: a session already DecisionSelected
    must reject a second select, even with byte-identical inputs."""

    session_id = _evidence_ready()
    exit_code, _ = _select(session_id)
    assert exit_code == EXIT_SUCCESS

    exit_code, payload = _select(session_id)  # identical inputs
    assert exit_code == EXIT_INVALID_STATE_TRANSITION
    assert payload["error_type"] == "invalid_state_transition"


def test_preview_transitions_decision_selected_to_awaiting_confirmation():
    """Independently re-derived from IWC-001's own state table (§4.4):
    AwaitingConfirmation is defined as "Preview generated, awaiting
    Confirmation" -- so first successful preview construction MUST move
    DecisionSelected -> AwaitingConfirmation. Confirms the claimed repair
    is real, not just documented."""

    session_id = _evidence_ready()
    _select(session_id)
    exit_code, status_before = _run(run_decision_session_status, session_id=session_id)
    assert status_before["session"]["session_state"] == "DecisionSelected"

    exit_code, _ = _run(run_decision_session_preview, session_id=session_id)
    assert exit_code == EXIT_SUCCESS

    exit_code, status_after = _run(run_decision_session_status, session_id=session_id)
    assert status_after["session"]["session_state"] == "AwaitingConfirmation"


def test_preview_second_call_idempotent_no_further_transition():
    session_id = _evidence_ready()
    _select(session_id)
    _run(run_decision_session_preview, session_id=session_id)
    exit_code1, p1 = _run(run_decision_session_preview, session_id=session_id)
    exit_code2, status = _run(run_decision_session_status, session_id=session_id)
    assert exit_code1 == EXIT_SUCCESS
    assert status["session"]["session_state"] == "AwaitingConfirmation"


# ===========================================================================
# Part III: Identity / authority verification
# ===========================================================================


def test_select_command_has_identity_flag_in_parser():
    """Phase 145G.3 closes F-145G.2V-1: this test originally asserted the
    Blocking finding itself (``select`` had NO identity-distinguishing
    flag at all). It now asserts the repair -- ``select`` accepts exactly
    one identity-shaped flag, ``--as-identity``, not multiple competing
    ones (the repair's own "one explicit production identity claim
    channel" requirement)."""

    from pcae.cli import build_parser

    parser = build_parser()
    # Walk the parser tree to find the decision-session select subparser's
    # own option strings.
    found = None
    for action in parser._subparsers._group_actions:
        for choice_name, subparser in action.choices.items():
            if choice_name != "decision-session":
                continue
            for sub_action in subparser._subparsers._group_actions:
                for inner_name, inner_parser in sub_action.choices.items():
                    if inner_name == "select":
                        found = inner_parser
    assert found is not None, "could not locate decision-session select subparser"

    option_strings = set()
    for action in found._actions:
        option_strings.update(action.option_strings)

    identity_like = {
        opt
        for opt in option_strings
        if any(tok in opt for tok in ("identity", "principal", "--as", "owner", "acting"))
    }
    assert identity_like == {"--as-identity"}, (
        f"expected exactly one identity-distinguishing flag (--as-identity) on "
        f"`select`, found: {identity_like}. Full option set: {option_strings}"
    )


def test_select_rejects_mismatched_identity_regardless_of_os_environment(monkeypatch):
    """Phase 145G.3 closes F-145G.2V-1: this test originally documented
    that `select` succeeded unconditionally regardless of simulated
    OS-level identity, because no enforcement point existed at all. It now
    confirms the opposite -- a claimed identity that does not match the
    session's bound owner_identity ('alice') is rejected, and this is
    governed entirely by the explicit --as-identity claim, never by OS
    environment state (which remains irrelevant, exactly as before)."""

    session_id = _evidence_ready(owner_id="alice")

    monkeypatch.setenv("USER", "mallory")
    monkeypatch.setenv("USERNAME", "mallory")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "mallory")
    monkeypatch.setenv("PCAE_IDENTITY", "mallory")
    monkeypatch.setenv("PCAE_AGENT_ID", "mallory-agent")

    # A mismatched explicit claim is rejected...
    exit_code, payload = _select(session_id, as_identity="mallory")
    assert exit_code == 6
    assert payload["error_type"] == "identity_binding_mismatch"

    # ...while the correct explicit claim still succeeds, proving OS
    # environment state played no role in either outcome.
    exit_code, payload = _select(session_id, as_identity="alice")
    assert exit_code == EXIT_SUCCESS

    context = build_application_context()
    session = context.session_service.load_session(session_id)
    assert session.owner_identity == "alice"


def test_confirm_and_cancel_also_reject_mismatched_identity(monkeypatch):
    """Phase 145G.3 closes F-145G.2V-1: broader finding, not limited to
    `select` -- this test originally documented that `cancel` also
    accepted no identity input at all (a systemic CLI pattern, not a
    select-specific regression). It now confirms `cancel` rejects a
    mismatched identity claim too, including under a simulated 'mallory'
    OS environment, and that the correct claim still succeeds."""

    session_id = _create_session(owner_id="alice")
    monkeypatch.setenv("USER", "mallory")

    exit_code, payload = _run(
        run_decision_session_cancel, session_id=session_id, reason="mallory cancels", as_identity="mallory"
    )
    assert exit_code == 6
    assert payload["error_type"] == "identity_binding_mismatch"

    exit_code, payload = _run(
        run_decision_session_cancel, session_id=session_id, reason="alice cancels", as_identity="alice"
    )
    assert exit_code == EXIT_SUCCESS


# ===========================================================================
# Part IV: Option-binding verification
# ===========================================================================


def test_option_not_in_presented_set_rejected_at_cli():
    session_id = _evidence_ready()
    exit_code, payload = _select(session_id, option_id="opt-ZZZ", options_presented=["opt-a", "opt-b"])
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_duplicate_presented_ids_rejected_at_cli():
    session_id = _evidence_ready()
    exit_code, payload = _select(session_id, options_presented=["opt-a", "opt-a", "opt-b"])
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_empty_presented_set_rejected_at_cli():
    session_id = _evidence_ready()
    exit_code, payload = _select(session_id, options_presented=[])
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE
    assert payload["error_type"] == "invalid_request"


def test_malformed_path_like_option_id_is_accepted_as_opaque_string():
    """No sanitization of option-id content is claimed anywhere in the
    contract text (IWPC-REQ-194 only requires SET MEMBERSHIP, not
    format); confirm this is in fact the implementation's behavior --
    path-like strings pass straight through as opaque data. This is not
    presented as a defect (no contract requirement is violated), but
    documents the actual behavior for the record."""

    session_id = _evidence_ready()
    exit_code, payload = _select(
        session_id, option_id="../../etc/passwd", options_presented=["../../etc/passwd", "opt-b"]
    )
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["human_selection_id"] == "../../etc/passwd"


def test_domain_layer_independently_enforces_option_membership_bypassing_cli():
    """Call SessionApplicationService.select_decision DIRECTLY, bypassing
    the CLI's own structural pre-checks entirely, to determine whether
    membership validation is ALSO domain-enforced or CLI-only."""

    session_id = _evidence_ready()
    context = build_application_context()
    # InvalidSelectionError (raised by select_decision's own membership
    # check) is caught and rewrapped as SessionInvalidTransitionApplicationError
    # by _run_orchestration_body -- this IS domain-layer enforcement
    # (the application-service boundary, independent of the CLI's own
    # pre-check), it just surfaces under the shared taxonomy wrapper.
    with pytest.raises(SessionInvalidTransitionApplicationError):
        context.session_service.select_decision(
            session_id,
            option_id="not-presented",
            options_presented=("opt-a", "opt-b"),
            template_version="v1",
            caller_identity="alice",
        )


def test_domain_layer_does_NOT_enforce_no_duplicates_bypassing_cli():
    """Adversarial finding: the CLI structurally rejects duplicate
    --options-presented values (decision_session.py's own
    `len(set(presented)) != len(presented)` check), but
    SessionApplicationService.select_decision itself performs NO
    duplicate check -- only membership (`option_id not in presented`).
    Calling the service directly with a duplicated options_presented
    tuple that still contains option_id should therefore SUCCEED,
    demonstrating duplicate-rejection is CLI-layer-only, not
    domain-enforced."""

    session_id = _evidence_ready()
    context = build_application_context()
    session = context.session_service.select_decision(
        session_id,
        option_id="opt-a",
        options_presented=("opt-a", "opt-a", "opt-b"),
        template_version="v1",
        caller_identity="alice",
    )
    assert session.session_state == SessionState.DECISION_SELECTED
    assert session.options_presented == ("opt-a", "opt-a", "opt-b")


def test_domain_layer_does_NOT_enforce_nonempty_template_version_bypassing_cli():
    """Similarly: the CLI requires --template-version non-empty
    (_require_nonempty), but does the domain layer independently
    enforce it? If not, a non-CLI caller (a different transport) could
    persist a session with an empty template_version, silently
    stranding it (per the contract's own admission that
    PublicationHandoff.validate_completeness requires it non-empty)."""

    session_id = _evidence_ready()
    context = build_application_context()
    session = context.session_service.select_decision(
        session_id,
        option_id="opt-a",
        options_presented=("opt-a", "opt-b"),
        template_version="",
        caller_identity="alice",
    )
    assert session.session_state == SessionState.DECISION_SELECTED
    assert session.template_version == ""
    # Downstream consequence: this session can never reach readiness, per
    # the contract's own docstring admission. Confirmed here directly.
    _run(run_decision_session_preview, session_id=session_id)
    exit_code, payload = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=payload_digest(session_id),
        statement="I confirm.",
    )
    assert exit_code == EXIT_SUCCESS  # confirm doesn't check template_version
    exit_code, _ = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_GENERIC_DOMAIN_FAILURE  # stranded: readiness_incomplete


def payload_digest(session_id):
    exit_code, payload = _run(run_decision_session_preview, session_id=session_id)
    return payload["preview_digest"]


def test_cross_session_option_substitution_succeeds_no_cross_session_validation():
    """Adversarial: options 'presented' for session A's Decision Template
    are supplied when selecting for session B. Since options_presented
    is caller-declared with NO Decision Template resolver anywhere
    (disclosed explicitly in the contract text), there is no mechanism
    that could even detect this -- confirm it silently succeeds."""

    session_a = _evidence_ready()
    session_b = _evidence_ready()
    # Use option ids that look like they belong to session_a's template
    exit_code, payload = _select(
        session_b,
        option_id="session-a-only-option",
        options_presented=["session-a-only-option", "another-a-option"],
    )
    assert exit_code == EXIT_SUCCESS, (
        "cross-session option substitution is not rejected -- there is no "
        "Decision Template resolver to detect it (matches contract's own "
        "disclosed judgment call, IWPC-REQ-192's caller-declared design)."
    )


def test_reordered_options_presented_do_not_affect_selection_validity():
    session_id = _evidence_ready()
    exit_code, payload = _select(session_id, option_id="opt-b", options_presented=["opt-b", "opt-a", "opt-c"])
    assert exit_code == EXIT_SUCCESS
    assert payload["session"]["options_presented"] == ["opt-b", "opt-a", "opt-c"]


# ===========================================================================
# Part VI: Replay / mutation verification -- no last-write-wins anywhere
# ===========================================================================


def test_conflicting_second_selection_with_different_option_rejected():
    session_id = _evidence_ready()
    exit_code, _ = _select(session_id, option_id="opt-a", options_presented=["opt-a", "opt-b"])
    assert exit_code == EXIT_SUCCESS

    exit_code, payload = _select(session_id, option_id="opt-b", options_presented=["opt-a", "opt-b"])
    assert exit_code == EXIT_INVALID_STATE_TRANSITION
    assert payload["error_type"] == "invalid_state_transition"

    # Confirm no mutation occurred: original selection is intact.
    context = build_application_context()
    session = context.session_service.load_session(session_id)
    assert session.human_selection_id == "opt-a"


def test_changed_rationale_on_retry_does_not_overwrite():
    session_id = _evidence_ready()
    _select(session_id, rationale="original reason")
    _select(session_id, rationale="ATTACKER OVERWRITE ATTEMPT")

    context = build_application_context()
    session = context.session_service.load_session(session_id)
    assert session.human_rationale_text == "original reason", (
        "no last-write-wins path exists: a second select call must never "
        "overwrite an already-recorded rationale"
    )


def test_replay_after_preview_rejected():
    session_id = _evidence_ready()
    _select(session_id)
    _run(run_decision_session_preview, session_id=session_id)
    exit_code, payload = _select(session_id)
    assert exit_code == EXIT_INVALID_STATE_TRANSITION


def test_replay_after_confirmation_rejected():
    session_id = _evidence_ready()
    _select(session_id)
    _, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    digest = preview_payload["preview_digest"]
    exit_code, _ = _run(
        run_decision_session_confirm, session_id=session_id, preview_digest=digest, statement="I confirm."
    )
    assert exit_code == EXIT_SUCCESS

    exit_code, payload = _select(session_id)
    assert exit_code == EXIT_INVALID_STATE_TRANSITION


def test_replay_after_readiness_and_publication_rejected():
    session_id = _evidence_ready()
    _select(session_id)
    _, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    digest = preview_payload["preview_digest"]
    _run(run_decision_session_confirm, session_id=session_id, preview_digest=digest, statement="I confirm.")
    exit_code, readiness_payload = _run(run_decision_session_readiness, session_id=session_id)
    assert exit_code == EXIT_SUCCESS

    exit_code, payload = _select(session_id)
    assert exit_code == EXIT_INVALID_STATE_TRANSITION


def test_replay_after_cancellation_rejected():
    session_id = _evidence_ready()
    exit_code, _ = _run(run_decision_session_cancel, session_id=session_id, reason="no longer needed")
    assert exit_code == EXIT_SUCCESS
    exit_code, payload = _select(session_id)
    assert exit_code == EXIT_INVALID_STATE_TRANSITION
    assert payload["error_type"] == "invalid_state_transition"


def test_tampered_persisted_options_presented_is_not_re_validated_on_read():
    """After a successful select, directly tamper with the persisted
    session's options_presented field (simulating file corruption or a
    hostile actor with filesystem access) and confirm `status`/`preview`
    do not re-validate that the (now-tampered) options_presented set
    still structurally contains human_selection_id -- there is no
    read-time re-validation anywhere, only write-time (at select)."""

    session_id = _evidence_ready()
    _select(session_id, option_id="opt-a", options_presented=["opt-a", "opt-b"])

    repo = FilesystemSessionRepository()
    session = repo.load(session_id)
    tampered = Session(
        session_id=session.session_id,
        owner_identity=session.owner_identity,
        template_ref=session.template_ref,
        subject_ref=session.subject_ref,
        session_state=session.session_state,
        schema_version=session.schema_version,
        created_at=session.created_at,
        updated_at=_now(),
        human_selection_id=session.human_selection_id,  # still "opt-a"
        human_rationale_text=session.human_rationale_text,
        human_conditions_text=session.human_conditions_text,
        disclosure_acknowledgements=session.disclosure_acknowledgements,
        template_version=session.template_version,
        options_presented=("opt-c", "opt-d"),  # tampered: no longer contains opt-a!
        decision_maker_evidence_kind=session.decision_maker_evidence_kind,
        metadata=session.metadata,
    )
    repo.persist(tampered)

    # status and preview both succeed with no re-validation of the
    # (now-inconsistent) options_presented/human_selection_id relationship.
    exit_code, status_payload = _run(run_decision_session_status, session_id=session_id)
    assert exit_code == EXIT_SUCCESS
    exit_code, preview_payload = _run(run_decision_session_preview, session_id=session_id)
    assert exit_code == EXIT_SUCCESS, (
        "preview succeeded even though options_presented no longer contains "
        "human_selection_id -- confirms no read-time structural re-validation "
        "exists between these two fields anywhere in the read path."
    )
