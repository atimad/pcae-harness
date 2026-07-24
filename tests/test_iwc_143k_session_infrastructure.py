"""Phase 143K unit tests: Interactive Workflow session infrastructure.

Covers identity, state enumeration, serialization round-trip, invariant
validation, the ``SessionRepository`` interface contract, Session
Coordinator construction/behavior, and deterministic failures for
unimplemented (out-of-143K-scope) paths. No test in this module exercises
workflow behavior (evidence, clarification, preview, confirmation,
cancellation/expiry/abandonment execution, publication, CHGR creation) --
that is 143K's explicit no-go boundary.
"""

from __future__ import annotations

from typing import Dict, Iterable

import pytest

from pcae.interactive_workflow.errors import (
    InvalidIdentifierError,
    InvalidSessionStateError,
    InvariantViolationError,
    PersistenceUnavailableError,
    SerializationFailureError,
    SessionNotFoundError,
    UnsupportedVersionError,
)
from pcae.interactive_workflow.models.session import (
    SCHEMA_VERSION,
    Session,
    SessionState,
    TERMINAL_STATES,
)
from pcae.interactive_workflow.persistence.migration import MigrationRegistry
from pcae.interactive_workflow.persistence.repository import (
    CHGR_STORAGE_PREFIX,
    SessionRepository,
)
from pcae.interactive_workflow.serialization.schema import from_payload, to_payload
from pcae.interactive_workflow.session.coordinator import SessionCoordinator
from pcae.interactive_workflow.session.identity import (
    SESSION_ID_PREFIX,
    generate_session_id,
    is_valid_session_id,
    validate_session_id,
)
from pcae.interactive_workflow.state_machine.transitions import (
    TRANSITION_TABLE,
    is_valid_transition,
    permitted_exits,
)
from pcae.interactive_workflow.validation.invariants import (
    validate_identifier,
    validate_known_state,
    validate_required_metadata,
    validate_session,
    validate_terminal_integrity,
    validate_version,
)


# --- Identity -----------------------------------------------------------


def test_generated_session_id_has_cds_prefix_and_validates():
    session_id = generate_session_id()
    assert session_id.startswith(SESSION_ID_PREFIX)
    assert validate_session_id(session_id) == session_id
    assert is_valid_session_id(session_id)


def test_generated_session_ids_are_unique():
    ids = {generate_session_id() for _ in range(200)}
    assert len(ids) == 200


def test_session_id_rejects_chgr_prefix():
    with pytest.raises(InvalidIdentifierError):
        validate_session_id("chgr-11111111-1111-4111-8111-111111111111")


@pytest.mark.parametrize(
    "bad_id",
    [
        "",
        "CDS-not-a-uuid",
        "cds-11111111-1111-4111-8111-111111111111",
        "CDS-11111111-1111-1111-8111-111111111111",
        11,
        None,
    ],
)
def test_invalid_session_ids_rejected(bad_id):
    assert is_valid_session_id(bad_id) is False
    with pytest.raises(InvalidIdentifierError):
        validate_session_id(bad_id)


def test_session_identity_carries_no_authority_information():
    # Structural check: identity is a bare CDS-<uuid4>, with no owner,
    # role, or authority token embeddable/derivable from it.
    session_id = generate_session_id()
    body = session_id[len(SESSION_ID_PREFIX):]
    assert body.count("-") == 4
    assert all(part.isalnum() for part in body.split("-"))


# --- State enumeration ----------------------------------------------------


def test_exactly_ten_canonical_states():
    assert len(list(SessionState)) == 10
    assert {s.value for s in SessionState} == {
        "Created",
        "EvidenceReady",
        "AwaitingDecision",
        "AwaitingClarification",
        "DecisionSelected",
        "AwaitingConfirmation",
        "Confirmed",
        "Cancelled",
        "Expired",
        "Abandoned",
    }


def test_terminal_states_are_exactly_four():
    assert TERMINAL_STATES == {
        SessionState.CONFIRMED,
        SessionState.CANCELLED,
        SessionState.EXPIRED,
        SessionState.ABANDONED,
    }


def test_transition_table_covers_every_state_exactly_once():
    assert set(TRANSITION_TABLE.keys()) == set(SessionState)


def test_terminal_states_have_empty_exit_sets():
    for state in TERMINAL_STATES:
        assert permitted_exits(state) == frozenset()


def test_terminal_states_never_appear_as_a_permitted_exit_into_another_terminal():
    # A terminal state may be *reached* from an active state, but no
    # terminal state transitions into a different terminal state (that
    # would require a non-empty exit set, which terminal states never
    # have -- already covered above), and no terminal state transitions
    # back into an active state.
    for state, exits in TRANSITION_TABLE.items():
        if state in TERMINAL_STATES:
            assert exits == frozenset()


@pytest.mark.parametrize(
    ("current", "target", "expected"),
    [
        (SessionState.CREATED, SessionState.EVIDENCE_READY, True),
        (SessionState.CREATED, SessionState.AWAITING_DECISION, False),
        (SessionState.AWAITING_DECISION, SessionState.AWAITING_CLARIFICATION, True),
        (SessionState.AWAITING_CLARIFICATION, SessionState.AWAITING_DECISION, True),
        (SessionState.AWAITING_CONFIRMATION, SessionState.CONFIRMED, True),
        (SessionState.CONFIRMED, SessionState.CANCELLED, False),
        (SessionState.CANCELLED, SessionState.CREATED, False),
    ],
)
def test_is_valid_transition_matches_table(current, target, expected):
    assert is_valid_transition(current, target) is expected


def test_is_valid_transition_rejects_non_state_values():
    assert is_valid_transition("Created", SessionState.EVIDENCE_READY) is False
    assert is_valid_transition(SessionState.CREATED, "EvidenceReady") is False


def test_every_active_state_can_reach_every_terminal_state_directly_or_indirectly():
    # Structural sanity: no active state is a dead end that cannot ever
    # reach Cancelled/Expired/Abandoned (IWC-REQ-045/046/047, 143I.1's
    # widening).
    active_states = set(SessionState) - TERMINAL_STATES
    for state in active_states:
        exits = permitted_exits(state)
        assert exits & {SessionState.CANCELLED, SessionState.EXPIRED, SessionState.ABANDONED}


# --- Serialization ----------------------------------------------------


def _make_session(**overrides) -> Session:
    fields = dict(
        session_id=generate_session_id(),
        owner_identity="user:atila",
        template_ref="template:example-v1",
        subject_ref="subject:example-1",
        session_state=SessionState.CREATED,
        created_at="2026-07-24T00:00:00+00:00",
        updated_at="2026-07-24T00:00:00+00:00",
    )
    fields.update(overrides)
    return Session(**fields)


def test_serialization_round_trip_preserves_every_field():
    session = _make_session(
        human_selection_id="option-1",
        human_rationale_text="because",
        human_conditions_text="none",
        disclosure_acknowledgements=("ack-1", "ack-2"),
        metadata={"k": "v"},
    )
    payload = to_payload(session)
    restored = from_payload(payload)
    assert restored == session


def test_serialization_payload_has_schema_version():
    session = _make_session()
    payload = to_payload(session)
    assert payload["schema_version"] == SCHEMA_VERSION


def test_from_payload_rejects_unknown_schema_version():
    session = _make_session()
    payload = to_payload(session)
    payload["schema_version"] = "some-future-version/9.9"
    with pytest.raises(UnsupportedVersionError):
        from_payload(payload)


def test_from_payload_rejects_malformed_payload():
    with pytest.raises(SerializationFailureError):
        from_payload({"schema_version": SCHEMA_VERSION})


def test_serialization_excludes_out_of_scope_fields():
    session = _make_session()
    payload = to_payload(session)
    for excluded_key in ("preview_digest", "evidence", "confirmation", "publication", "chgr"):
        assert excluded_key not in payload


# --- Invariant validation ----------------------------------------------------


def test_validate_identifier_accepts_generated_id():
    session_id = generate_session_id()
    assert validate_identifier(session_id) == session_id


def test_validate_known_state_rejects_non_member():
    with pytest.raises(InvalidSessionStateError):
        validate_known_state("Created")  # a string, not a SessionState member


def test_validate_terminal_integrity_rejects_exit_from_terminal():
    with pytest.raises(InvalidSessionStateError):
        validate_terminal_integrity(SessionState.CONFIRMED, SessionState.CANCELLED)


def test_validate_terminal_integrity_allows_no_op_on_terminal():
    validate_terminal_integrity(SessionState.CONFIRMED, SessionState.CONFIRMED)


def test_validate_terminal_integrity_rejects_untabled_transition():
    with pytest.raises(InvalidSessionStateError):
        validate_terminal_integrity(SessionState.CREATED, SessionState.AWAITING_CONFIRMATION)


def test_validate_terminal_integrity_accepts_tabled_transition():
    validate_terminal_integrity(SessionState.CREATED, SessionState.EVIDENCE_READY)


def test_validate_required_metadata_raises_on_missing_key():
    with pytest.raises(InvariantViolationError):
        validate_required_metadata({"a": 1}, ["a", "b"])


def test_validate_required_metadata_passes_when_present():
    validate_required_metadata({"a": 1, "b": 2}, ["a", "b"])


def test_validate_version_rejects_unknown_version():
    with pytest.raises(UnsupportedVersionError):
        validate_version("unknown/0.0")


def test_validate_session_accepts_well_formed_session():
    session = _make_session()
    assert validate_session(session) is session


# --- SessionRepository interface contract -------------------------------


class _InMemorySessionRepository(SessionRepository):
    """Minimal in-memory test double -- exists only to exercise the
    interface contract; not a production implementation."""

    def __init__(self) -> None:
        self._store: Dict[str, Session] = {}

    def create(self, session: Session) -> None:
        if session.session_id in self._store:
            raise ValueError("session already exists")
        self._store[session.session_id] = session

    def load(self, session_id: str) -> Session:
        try:
            return self._store[session_id]
        except KeyError as exc:
            raise SessionNotFoundError(str(session_id)) from exc

    def persist(self, session: Session) -> None:
        if session.session_id not in self._store:
            raise SessionNotFoundError(session.session_id)
        self._store[session.session_id] = session

    def exists(self, session_id: str) -> bool:
        return session_id in self._store

    def list_session_ids(self) -> Iterable[str]:
        return list(self._store.keys())


class _BrokenSessionRepository(SessionRepository):
    """Test double whose every method refuses -- used to prove callers
    that depend on ``SessionRepository`` propagate persistence failure
    rather than swallowing it."""

    def create(self, session: Session) -> None:
        raise PersistenceUnavailableError("backing store unavailable")

    def load(self, session_id: str) -> Session:
        raise PersistenceUnavailableError("backing store unavailable")

    def persist(self, session: Session) -> None:
        raise PersistenceUnavailableError("backing store unavailable")

    def exists(self, session_id: str) -> bool:
        raise PersistenceUnavailableError("backing store unavailable")

    def list_session_ids(self) -> Iterable[str]:
        raise PersistenceUnavailableError("backing store unavailable")


def test_session_repository_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        SessionRepository()  # abstract -- no concrete backend selected in 143K


def test_session_repository_chgr_storage_prefix_is_governance_records():
    assert CHGR_STORAGE_PREFIX == ".pcae/governance-records/"


def test_in_memory_repository_round_trip():
    repo = _InMemorySessionRepository()
    session = _make_session()
    repo.create(session)
    assert repo.exists(session.session_id)
    assert repo.load(session.session_id) == session
    assert session.session_id in list(repo.list_session_ids())


def test_in_memory_repository_load_missing_raises_session_not_found():
    repo = _InMemorySessionRepository()
    with pytest.raises(SessionNotFoundError):
        repo.load(generate_session_id())


# --- Migration hook skeleton -------------------------------------------


def test_migration_registry_raises_for_unregistered_version():
    registry = MigrationRegistry()
    with pytest.raises(UnsupportedVersionError):
        registry.hook_for("some-old-version/0.0")


def test_migration_registry_registers_and_looks_up_hook():
    registry = MigrationRegistry()
    hook = lambda payload: dict(payload)
    registry.register("old/0.1", hook)
    assert registry.hook_for("old/0.1") is hook
    assert "old/0.1" in registry.known_versions()


# --- Session Coordinator skeleton -------------------------------------------


def test_coordinator_construction_requires_repository():
    repo = _InMemorySessionRepository()
    coordinator = SessionCoordinator(repo)
    assert coordinator is not None


def test_coordinator_create_session_persists_via_repository():
    repo = _InMemorySessionRepository()
    coordinator = SessionCoordinator(repo)
    session = coordinator.create_session(
        owner_identity="user:atila",
        template_ref="template:example-v1",
        subject_ref="subject:example-1",
    )
    assert session.session_state == SessionState.CREATED
    assert repo.exists(session.session_id)


def test_coordinator_create_session_generates_valid_identity():
    repo = _InMemorySessionRepository()
    coordinator = SessionCoordinator(repo)
    session = coordinator.create_session("user:a", "template:t", "subject:s")
    assert is_valid_session_id(session.session_id)


def test_coordinator_load_session_returns_persisted_record():
    repo = _InMemorySessionRepository()
    coordinator = SessionCoordinator(repo)
    created = coordinator.create_session("user:a", "template:t", "subject:s")
    loaded = coordinator.load_session(created.session_id)
    assert loaded == created


def test_coordinator_load_missing_session_raises_deterministically():
    repo = _InMemorySessionRepository()
    coordinator = SessionCoordinator(repo)
    with pytest.raises(SessionNotFoundError):
        coordinator.load_session(generate_session_id())


def test_coordinator_persist_session_round_trips_through_repository():
    repo = _InMemorySessionRepository()
    coordinator = SessionCoordinator(repo)
    session = coordinator.create_session("user:a", "template:t", "subject:s")
    updated = session.with_state(SessionState.EVIDENCE_READY, updated_at="2026-07-24T01:00:00+00:00")
    coordinator.persist_session(updated)
    assert coordinator.load_session(session.session_id).session_state == SessionState.EVIDENCE_READY


def test_coordinator_validate_state_accepts_valid_transition():
    repo = _InMemorySessionRepository()
    coordinator = SessionCoordinator(repo)
    session = coordinator.create_session("user:a", "template:t", "subject:s")
    coordinator.validate_state(session, SessionState.EVIDENCE_READY)


def test_coordinator_validate_state_rejects_invalid_transition():
    repo = _InMemorySessionRepository()
    coordinator = SessionCoordinator(repo)
    session = coordinator.create_session("user:a", "template:t", "subject:s")
    with pytest.raises(InvalidSessionStateError):
        coordinator.validate_state(session, SessionState.AWAITING_CONFIRMATION)


def test_coordinator_propagates_persistence_failure_on_create():
    coordinator = SessionCoordinator(_BrokenSessionRepository())
    with pytest.raises(PersistenceUnavailableError):
        coordinator.create_session("user:a", "template:t", "subject:s")


def test_coordinator_propagates_persistence_failure_on_load():
    coordinator = SessionCoordinator(_BrokenSessionRepository())
    with pytest.raises(PersistenceUnavailableError):
        coordinator.load_session(generate_session_id())


def test_coordinator_perform_publication_fails_deterministically_permanently():
    # As of Phase 143O, ``orchestrate_evidence`` and ``perform_confirmation``
    # are legitimately implemented (thin delegation to a caller-supplied
    # ``WorkflowOrchestrator`` -- see
    # tests/test_iwc_143o_session_coordination_publication_handoff.py for
    # their coverage) and are no longer zero-argument ``NotImplementedError``
    # stubs, so they are no longer parametrized here. ``perform_publication``
    # remains a permanent, zero-argument ``NotImplementedError`` -- IWC-REQ-171
    # leaves Publication Handoff execution ownership an explicitly open
    # question no phase (including 143O) closes.
    repo = _InMemorySessionRepository()
    coordinator = SessionCoordinator(repo)
    with pytest.raises(NotImplementedError):
        coordinator.perform_publication()


def test_coordinator_registers_lifecycle_hooks_without_invoking_them():
    repo = _InMemorySessionRepository()
    coordinator = SessionCoordinator(repo)
    calls = []
    coordinator.register_lifecycle_hook(lambda session: calls.append(session))
    coordinator.create_session("user:a", "template:t", "subject:s")
    # 143K implements no transition-execution path that invokes hooks;
    # registration alone must not trigger a call.
    assert calls == []


# --- No-authority / no-CHGR structural guarantees -------------------------


def test_session_model_has_no_chgr_identifier_field():
    session = _make_session()
    for field_name in ("chgr_id", "chgr_identifier", "confirmation_digest", "publication_ref"):
        assert not hasattr(session, field_name)


def test_session_coordinator_has_no_publish_or_confirm_that_succeeds():
    repo = _InMemorySessionRepository()
    coordinator = SessionCoordinator(repo)
    assert not hasattr(coordinator, "publish")
    assert not hasattr(coordinator, "confirm")
