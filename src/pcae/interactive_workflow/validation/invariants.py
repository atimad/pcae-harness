"""Structural invariant validators (Phase 143K).

Each function validates exactly one concern and raises on failure; none
of them repair, coerce, or silently accept a value outside its rule.
``validate_session`` composes the individual checks for convenience but
adds no additional rule of its own.
"""

from __future__ import annotations

from typing import Iterable, Mapping

from pcae.interactive_workflow.errors import (
    InvalidSessionStateError,
    InvariantViolationError,
    UnsupportedVersionError,
)
from pcae.interactive_workflow.models.session import (
    SCHEMA_VERSION,
    Session,
    SessionState,
    TERMINAL_STATES,
)
from pcae.interactive_workflow.session.identity import validate_session_id
from pcae.interactive_workflow.state_machine.transitions import is_valid_transition

_KNOWN_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})


def validate_identifier(session_id: str) -> str:
    """Raise ``InvalidIdentifierError`` unless ``session_id`` matches
    ``CDS-<uuid4>`` exactly."""

    return validate_session_id(session_id)


def validate_known_state(state: SessionState) -> SessionState:
    """Raise ``InvalidSessionStateError`` unless ``state`` is one of the
    ten canonical ``SessionState`` members."""

    if not isinstance(state, SessionState):
        raise InvalidSessionStateError(f"{state!r} is not a known SessionState.")
    return state


def validate_terminal_integrity(
    current_state: SessionState, proposed_state: SessionState
) -> None:
    """Raise ``InvalidSessionStateError`` if ``current_state`` is terminal
    and ``proposed_state`` differs from it (IWC-001 v1.1 §4.4: no
    terminal state has any exit), or if the transition is otherwise
    absent from the widened transition table."""

    validate_known_state(current_state)
    validate_known_state(proposed_state)
    if current_state == proposed_state:
        return
    if current_state in TERMINAL_STATES:
        raise InvalidSessionStateError(
            f"{current_state.value} is terminal and admits no exit "
            f"(attempted transition to {proposed_state.value})."
        )
    if not is_valid_transition(current_state, proposed_state):
        raise InvalidSessionStateError(
            f"{current_state.value} -> {proposed_state.value} is not a "
            "permitted transition (IWC-001 v1.1 §4.4)."
        )


def validate_required_metadata(
    metadata: Mapping[str, object], required_keys: Iterable[str]
) -> None:
    """Raise ``InvariantViolationError`` if any of ``required_keys`` is
    absent from ``metadata``."""

    missing = [key for key in required_keys if key not in metadata]
    if missing:
        raise InvariantViolationError(f"Missing required metadata key(s): {missing}.")


def validate_version(schema_version: str) -> str:
    """Raise ``UnsupportedVersionError`` unless ``schema_version`` is one
    this package explicitly recognizes."""

    if schema_version not in _KNOWN_SCHEMA_VERSIONS:
        raise UnsupportedVersionError(f"Unsupported schema_version: {schema_version!r}.")
    return schema_version


def validate_session(session: Session) -> Session:
    """Run every structural invariant applicable to a standalone
    ``Session`` (identifier, known state, version). Terminal-integrity is
    a two-state check and is validated separately via
    ``validate_terminal_integrity`` at the point a transition is
    proposed."""

    validate_identifier(session.session_id)
    validate_known_state(session.session_state)
    validate_version(session.schema_version)
    return session


__all__ = [
    "validate_identifier",
    "validate_known_state",
    "validate_terminal_integrity",
    "validate_required_metadata",
    "validate_version",
    "validate_session",
]
