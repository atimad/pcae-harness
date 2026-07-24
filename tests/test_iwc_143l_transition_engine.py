"""Phase 143L unit tests: Interactive Workflow Transition Engine.

Covers the Transition Registry, Transition Validator, Transition Policy,
and Transition Engine: every legal transition, every illegal transition,
terminal-state enforcement from every terminal state, identity/version
preservation, transition metadata correctness, determinism, fail-closed
behavior, the Phase 143I.1 (B-1) regression matrix, and the required
adversarial scenarios. No test in this module exercises workflow
orchestration, evidence, clarification, preview, confirmation,
cancellation/expiry/abandonment *execution*, publication, or CHGR
creation -- that is Phase 143L's explicit no-go boundary.
"""

from __future__ import annotations

from typing import List, Tuple

import pytest

from pcae.interactive_workflow.errors import (
    DuplicateTransitionError,
    InvalidTransitionError,
    InvalidTransitionSequenceError,
    TerminalStateViolationError,
    TransitionError,
    UnknownStateError,
    UnsupportedTransitionError,
    UnsupportedVersionError,
)
from pcae.interactive_workflow.models.session import (
    SCHEMA_VERSION,
    Session,
    SessionState,
    TERMINAL_STATES,
)
from pcae.interactive_workflow.state_machine.engine import TransitionEngine, TransitionResult
from pcae.interactive_workflow.state_machine.metadata import TransitionMetadata
from pcae.interactive_workflow.state_machine.policy import TransitionPolicy
from pcae.interactive_workflow.state_machine.registry import TransitionRegistry
from pcae.interactive_workflow.state_machine.transitions import TRANSITION_TABLE
from pcae.interactive_workflow.state_machine.validator import TransitionValidator

_TS = "2026-07-24T05:00:00+00:00"
_ALL_STATES: Tuple[SessionState, ...] = tuple(SessionState)
_NON_TERMINAL_STATES: Tuple[SessionState, ...] = tuple(
    state for state in SessionState if state not in TERMINAL_STATES
)


def _make_session(state: SessionState = SessionState.CREATED, **overrides) -> Session:
    fields = dict(
        session_id="CDS-11111111-1111-4111-8111-111111111111",
        owner_identity="owner",
        template_ref="template-ref",
        subject_ref="subject-ref",
        session_state=state,
        created_at=_TS,
        updated_at=_TS,
    )
    fields.update(overrides)
    return Session(**fields)


def _all_legal_pairs() -> List[Tuple[SessionState, SessionState]]:
    return [
        (source, target)
        for source, targets in TRANSITION_TABLE.items()
        for target in sorted(targets, key=lambda state: state.value)
    ]


def _all_illegal_pairs() -> List[Tuple[SessionState, SessionState]]:
    pairs = []
    for source in _ALL_STATES:
        for target in _ALL_STATES:
            if source == target:
                continue
            if target in TRANSITION_TABLE[source]:
                continue
            pairs.append((source, target))
    return pairs


# ---------------------------------------------------------------------------
# Transition Registry
# ---------------------------------------------------------------------------


def test_registry_all_states_matches_session_state_enum():
    registry = TransitionRegistry()
    assert registry.all_states() == frozenset(SessionState)


@pytest.mark.parametrize("source,target", _all_legal_pairs())
def test_registry_is_registered_true_for_every_legal_pair(source, target):
    registry = TransitionRegistry()
    assert registry.is_registered(source, target) is True


@pytest.mark.parametrize("source,target", _all_illegal_pairs())
def test_registry_is_registered_false_for_every_illegal_pair(source, target):
    registry = TransitionRegistry()
    assert registry.is_registered(source, target) is False


@pytest.mark.parametrize("state", _ALL_STATES)
def test_registry_is_terminal_matches_terminal_states(state):
    registry = TransitionRegistry()
    assert registry.is_terminal(state) is (state in TERMINAL_STATES)


def test_registry_all_transitions_matches_table_cardinality():
    registry = TransitionRegistry()
    expected_count = sum(len(targets) for targets in TRANSITION_TABLE.values())
    assert len(list(registry.all_transitions())) == expected_count


def test_registry_all_transitions_is_deterministic_across_calls():
    registry = TransitionRegistry()
    assert list(registry.all_transitions()) == list(registry.all_transitions())


def test_registry_permitted_targets_delegates_to_table():
    registry = TransitionRegistry()
    for state in _ALL_STATES:
        assert registry.permitted_targets(state) == TRANSITION_TABLE[state]


# ---------------------------------------------------------------------------
# Legal transitions (every contractually permitted transition)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("source,target", _all_legal_pairs())
def test_every_legal_transition_passes_validator(source, target):
    session = _make_session(state=source)
    TransitionValidator().validate(session, target)  # must not raise


@pytest.mark.parametrize("source,target", _all_legal_pairs())
def test_every_legal_transition_applies_via_engine(source, target):
    session = _make_session(state=source)
    engine = TransitionEngine()
    result = engine.apply(session, target, sequence_number=0)
    assert isinstance(result, TransitionResult)
    assert result.session.session_state == target


@pytest.mark.parametrize("source,target", _all_legal_pairs())
def test_every_legal_transition_reports_is_legal_true(source, target):
    session = _make_session(state=source)
    assert TransitionEngine().is_legal(session, target) is True


# ---------------------------------------------------------------------------
# Illegal transitions (every forbidden transition)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("source,target", _all_illegal_pairs())
def test_every_illegal_transition_rejected_by_validator(source, target):
    session = _make_session(state=source)
    with pytest.raises(TransitionError):
        TransitionValidator().validate(session, target)


@pytest.mark.parametrize("source,target", _all_illegal_pairs())
def test_every_illegal_transition_rejected_by_engine(source, target):
    session = _make_session(state=source)
    engine = TransitionEngine()
    with pytest.raises(TransitionError):
        engine.apply(session, target, sequence_number=0)


@pytest.mark.parametrize("source,target", _all_illegal_pairs())
def test_every_illegal_transition_reports_is_legal_false(source, target):
    session = _make_session(state=source)
    assert TransitionEngine().is_legal(session, target) is False


@pytest.mark.parametrize("state", _ALL_STATES)
def test_duplicate_no_op_transition_always_rejected(state):
    session = _make_session(state=state)
    with pytest.raises(DuplicateTransitionError):
        TransitionValidator().validate(session, state)


# ---------------------------------------------------------------------------
# Terminal-state enforcement (attempt transition from every terminal state)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("terminal_state", sorted(TERMINAL_STATES, key=lambda s: s.value))
def test_terminal_state_rejects_every_non_self_target(terminal_state):
    session = _make_session(state=terminal_state)
    for target in _ALL_STATES:
        if target == terminal_state:
            continue
        with pytest.raises(TerminalStateViolationError):
            TransitionValidator().validate(session, target)


@pytest.mark.parametrize("terminal_state", sorted(TERMINAL_STATES, key=lambda s: s.value))
def test_terminal_state_engine_apply_never_succeeds(terminal_state):
    session = _make_session(state=terminal_state)
    engine = TransitionEngine()
    for target in _ALL_STATES:
        with pytest.raises(TransitionError):
            engine.apply(session, target, sequence_number=0)


@pytest.mark.parametrize("terminal_state", sorted(TERMINAL_STATES, key=lambda s: s.value))
def test_terminal_state_has_empty_registry_exit_set(terminal_state):
    assert TransitionRegistry().permitted_targets(terminal_state) == frozenset()


# ---------------------------------------------------------------------------
# Identity preservation
# ---------------------------------------------------------------------------


def test_transition_preserves_session_identity():
    session = _make_session(state=SessionState.CREATED)
    result = TransitionEngine().apply(session, SessionState.EVIDENCE_READY, sequence_number=0)
    assert result.session.session_id == session.session_id
    assert result.metadata.session_id == session.session_id


def test_original_session_object_is_not_mutated():
    session = _make_session(state=SessionState.CREATED)
    original_state = session.session_state
    TransitionEngine().apply(session, SessionState.EVIDENCE_READY, sequence_number=0)
    assert session.session_state == original_state


# ---------------------------------------------------------------------------
# Version preservation
# ---------------------------------------------------------------------------


def test_transition_preserves_schema_version():
    session = _make_session(state=SessionState.CREATED)
    result = TransitionEngine().apply(session, SessionState.EVIDENCE_READY, sequence_number=0)
    assert result.session.schema_version == session.schema_version == SCHEMA_VERSION


def test_transition_rejects_unknown_schema_version():
    session = _make_session(state=SessionState.CREATED, schema_version="bogus/0.0")
    engine = TransitionEngine()
    with pytest.raises(UnsupportedVersionError):
        engine.apply(session, SessionState.EVIDENCE_READY, sequence_number=0)


# ---------------------------------------------------------------------------
# Metadata correctness
# ---------------------------------------------------------------------------


def test_transition_metadata_fields_are_correct():
    session = _make_session(state=SessionState.CREATED)
    result = TransitionEngine().apply(
        session,
        SessionState.EVIDENCE_READY,
        sequence_number=3,
        reason="evidence attached",
        timestamp=_TS,
    )
    assert result.metadata.previous_state == SessionState.CREATED
    assert result.metadata.new_state == SessionState.EVIDENCE_READY
    assert result.metadata.transition_timestamp == _TS
    assert result.metadata.transition_sequence_number == 3
    assert result.metadata.transition_reason == "evidence attached"


def test_transition_metadata_reason_defaults_to_none():
    session = _make_session(state=SessionState.CREATED)
    result = TransitionEngine().apply(session, SessionState.EVIDENCE_READY, sequence_number=0)
    assert result.metadata.transition_reason is None


def test_transition_metadata_carries_no_authority_field():
    metadata_fields = set(TransitionMetadata.__dataclass_fields__.keys())
    assert metadata_fields == {
        "session_id",
        "previous_state",
        "new_state",
        "transition_timestamp",
        "transition_sequence_number",
        "transition_reason",
    }


@pytest.mark.parametrize(
    "bad_sequence_number",
    [-1, "0", 1.5, True, None],
)
def test_transition_metadata_rejects_bad_sequence_number(bad_sequence_number):
    with pytest.raises(InvalidTransitionError):
        TransitionMetadata(
            session_id="CDS-11111111-1111-4111-8111-111111111111",
            previous_state=SessionState.CREATED,
            new_state=SessionState.EVIDENCE_READY,
            transition_timestamp=_TS,
            transition_sequence_number=bad_sequence_number,
        )


def test_transition_metadata_rejects_non_state_previous_state():
    with pytest.raises(InvalidTransitionError):
        TransitionMetadata(
            session_id="CDS-11111111-1111-4111-8111-111111111111",
            previous_state="Created",
            new_state=SessionState.EVIDENCE_READY,
            transition_timestamp=_TS,
            transition_sequence_number=0,
        )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_repeated_apply_with_identical_inputs_yields_identical_outcome():
    session = _make_session(state=SessionState.CREATED)
    engine = TransitionEngine()
    first = engine.apply(
        session, SessionState.EVIDENCE_READY, sequence_number=0, timestamp=_TS
    )
    second = engine.apply(
        session, SessionState.EVIDENCE_READY, sequence_number=0, timestamp=_TS
    )
    assert first.session == second.session
    assert first.metadata == second.metadata


def test_validator_and_engine_agree_on_every_pair():
    registry = TransitionRegistry()
    validator = TransitionValidator(registry)
    engine = TransitionEngine(registry=registry, validator=validator)
    for source in _ALL_STATES:
        for target in _ALL_STATES:
            session = _make_session(state=source)
            validator_says_legal = True
            try:
                validator.validate(session, target)
            except TransitionError:
                validator_says_legal = False
            assert engine.is_legal(session, target) is validator_says_legal


# ---------------------------------------------------------------------------
# Fail-closed behavior
# ---------------------------------------------------------------------------


def test_failed_apply_raises_before_constructing_a_result():
    session = _make_session(state=SessionState.CONFIRMED)
    engine = TransitionEngine()
    with pytest.raises(TransitionError):
        engine.apply(session, SessionState.CANCELLED, sequence_number=0)
    # session itself must remain untouched (frozen dataclass -- structural
    # guarantee, reasserted here as an explicit regression check).
    assert session.session_state == SessionState.CONFIRMED


# ---------------------------------------------------------------------------
# Phase 143I.1 (B-1) regression matrix
# ---------------------------------------------------------------------------

_B1_REPAIRED_CELLS: Tuple[Tuple[SessionState, SessionState], ...] = (
    (SessionState.CREATED, SessionState.CANCELLED),
    (SessionState.CREATED, SessionState.EXPIRED),
    (SessionState.CREATED, SessionState.ABANDONED),
    (SessionState.EVIDENCE_READY, SessionState.CANCELLED),
    (SessionState.AWAITING_CLARIFICATION, SessionState.CANCELLED),
    (SessionState.AWAITING_CLARIFICATION, SessionState.EXPIRED),
    (SessionState.AWAITING_CLARIFICATION, SessionState.ABANDONED),
    (SessionState.DECISION_SELECTED, SessionState.ABANDONED),
    (SessionState.AWAITING_CONFIRMATION, SessionState.ABANDONED),
)


@pytest.mark.parametrize("source,target", _B1_REPAIRED_CELLS)
def test_b1_repaired_cell_remains_permitted(source, target):
    """IWC-001 v1.1 §4.4 (widened by Phase 143I.1) -- each of these cells
    was missing in v1.0 (B-1) and must remain present and functional
    through the Transition Engine, not just present in the raw table."""

    session = _make_session(state=source)
    result = TransitionEngine().apply(session, target, sequence_number=0)
    assert result.session.session_state == target


@pytest.mark.parametrize("state", _NON_TERMINAL_STATES)
def test_every_non_terminal_state_has_universal_cancel_expire_abandon_exit(state):
    """IWC-REQ-045/046/047/160: every non-terminal state must be able to
    reach Cancelled, Expired, and Abandoned -- the exact requirement set
    B-1 found violated in IWC-001 v1.0."""

    registry = TransitionRegistry()
    targets = registry.permitted_targets(state)
    assert SessionState.CANCELLED in targets
    assert SessionState.EXPIRED in targets
    assert SessionState.ABANDONED in targets


# ---------------------------------------------------------------------------
# Adversarial testing
# ---------------------------------------------------------------------------


def test_adversarial_unknown_source_state():
    session = _make_session(state=SessionState.CREATED)
    object.__setattr__(session, "session_state", "NotAState")
    with pytest.raises(UnknownStateError):
        TransitionEngine().apply(session, SessionState.EVIDENCE_READY, sequence_number=0)


def test_adversarial_unknown_destination_state():
    session = _make_session(state=SessionState.CREATED)
    with pytest.raises(UnknownStateError):
        TransitionEngine().apply(session, "NotAState", sequence_number=0)


def test_adversarial_transition_replay_same_sequence_number_rejected():
    session = _make_session(state=SessionState.CREATED)
    engine = TransitionEngine()
    result = engine.apply(session, SessionState.EVIDENCE_READY, sequence_number=0)
    with pytest.raises(InvalidTransitionSequenceError):
        engine.apply(
            result.session,
            SessionState.AWAITING_DECISION,
            sequence_number=0,
            previous_sequence_number=result.metadata.transition_sequence_number,
        )


def test_adversarial_terminal_replay():
    session = _make_session(state=SessionState.CANCELLED)
    with pytest.raises(TerminalStateViolationError):
        TransitionEngine().apply(session, SessionState.EXPIRED, sequence_number=0)


def test_adversarial_reverse_transition():
    session = _make_session(state=SessionState.EVIDENCE_READY)
    with pytest.raises(UnsupportedTransitionError):
        TransitionEngine().apply(session, SessionState.CREATED, sequence_number=0)


def test_adversarial_skipped_transition():
    session = _make_session(state=SessionState.CREATED)
    with pytest.raises(UnsupportedTransitionError):
        TransitionEngine().apply(session, SessionState.CONFIRMED, sequence_number=0)


def test_adversarial_duplicate_transition():
    session = _make_session(state=SessionState.AWAITING_DECISION)
    with pytest.raises(DuplicateTransitionError):
        TransitionEngine().apply(session, SessionState.AWAITING_DECISION, sequence_number=0)


def test_adversarial_invalid_metadata_sequence_number():
    with pytest.raises(InvalidTransitionError):
        TransitionMetadata(
            session_id="CDS-11111111-1111-4111-8111-111111111111",
            previous_state=SessionState.CREATED,
            new_state=SessionState.EVIDENCE_READY,
            transition_timestamp=_TS,
            transition_sequence_number=-5,
        )


def test_adversarial_invalid_version():
    session = _make_session(state=SessionState.CREATED, schema_version="not-a-real-version")
    with pytest.raises(UnsupportedVersionError):
        TransitionEngine().apply(session, SessionState.EVIDENCE_READY, sequence_number=0)


def test_adversarial_malformed_session_missing_attributes():
    class _NotASession:
        pass

    with pytest.raises(InvalidTransitionError):
        TransitionEngine().apply(_NotASession(), SessionState.EVIDENCE_READY, sequence_number=0)


def test_adversarial_negative_sequence_number_rejected():
    session = _make_session(state=SessionState.CREATED)
    with pytest.raises(InvalidTransitionSequenceError):
        TransitionEngine().apply(session, SessionState.EVIDENCE_READY, sequence_number=-1)


def test_adversarial_non_monotonic_sequence_number_rejected():
    session = _make_session(state=SessionState.CREATED)
    with pytest.raises(InvalidTransitionSequenceError):
        TransitionEngine().apply(
            session, SessionState.EVIDENCE_READY, sequence_number=1, previous_sequence_number=5
        )


# ---------------------------------------------------------------------------
# Transition Policy (direct coverage)
# ---------------------------------------------------------------------------


def test_policy_accepts_first_transition_with_no_previous_sequence():
    TransitionPolicy().validate_sequence(None, 0)  # must not raise


def test_policy_accepts_strictly_increasing_sequence():
    TransitionPolicy().validate_sequence(0, 1)  # must not raise


def test_policy_rejects_equal_sequence():
    with pytest.raises(InvalidTransitionSequenceError):
        TransitionPolicy().validate_sequence(3, 3)


def test_policy_rejects_decreasing_sequence():
    with pytest.raises(InvalidTransitionSequenceError):
        TransitionPolicy().validate_sequence(3, 2)


# ---------------------------------------------------------------------------
# Structural compatibility (143K session/persistence/serialization/
# validation/error hierarchy)
# ---------------------------------------------------------------------------


def test_transition_result_session_round_trips_through_serialization():
    from pcae.interactive_workflow.serialization.schema import from_payload, to_payload

    session = _make_session(state=SessionState.CREATED)
    result = TransitionEngine().apply(session, SessionState.EVIDENCE_READY, sequence_number=0)
    payload = to_payload(result.session)
    restored = from_payload(payload)
    assert restored == result.session


def test_transition_result_session_passes_143k_invariant_validation():
    from pcae.interactive_workflow.validation.invariants import validate_session

    session = _make_session(state=SessionState.CREATED)
    result = TransitionEngine().apply(session, SessionState.EVIDENCE_READY, sequence_number=0)
    validate_session(result.session)  # must not raise


def test_transition_engine_errors_are_interactive_workflow_errors():
    from pcae.interactive_workflow.errors import InteractiveWorkflowError

    for error_type in (
        UnknownStateError,
        DuplicateTransitionError,
        TerminalStateViolationError,
        UnsupportedTransitionError,
        InvalidTransitionSequenceError,
        InvalidTransitionError,
    ):
        assert issubclass(error_type, TransitionError)
        assert issubclass(error_type, InteractiveWorkflowError)


def test_state_machine_package_exports_transition_engine_surface():
    import pcae.interactive_workflow.state_machine as state_machine

    for name in (
        "TransitionEngine",
        "TransitionResult",
        "TransitionMetadata",
        "TransitionPolicy",
        "TransitionRegistry",
        "TransitionValidator",
    ):
        assert hasattr(state_machine, name)


# ---------------------------------------------------------------------------
# Explicit no-go boundary (this phase implements no orchestration/
# confirmation/publication/CHGR capability)
# ---------------------------------------------------------------------------


def test_transition_engine_has_no_confirmation_or_publication_method():
    engine = TransitionEngine()
    for forbidden_name in (
        "confirm",
        "publish",
        "orchestrate_evidence",
        "perform_confirmation",
        "perform_publication",
        "create_chgr",
    ):
        assert not hasattr(engine, forbidden_name)


def test_transition_engine_never_writes_under_governance_records(tmp_path, monkeypatch):
    import os

    monkeypatch.chdir(tmp_path)
    session = _make_session(state=SessionState.CREATED)
    TransitionEngine().apply(session, SessionState.EVIDENCE_READY, sequence_number=0)
    assert not os.path.isdir(tmp_path / ".pcae" / "governance-records")
