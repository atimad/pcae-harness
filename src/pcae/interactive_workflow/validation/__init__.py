"""Reusable invariant validation framework (Phase 143K).

Structural invariants only -- valid identifier, known state, terminal-
state integrity, required metadata, version compatibility. Workflow
semantics (e.g. "is this transition desirable," "has Confirmation
actually occurred") are never validated here; that is deferred to the
phases that implement the behavior (143L onward).
"""

from __future__ import annotations

from pcae.interactive_workflow.validation.invariants import (
    validate_identifier,
    validate_known_state,
    validate_required_metadata,
    validate_session,
    validate_terminal_integrity,
    validate_version,
)

__all__ = [
    "validate_identifier",
    "validate_known_state",
    "validate_required_metadata",
    "validate_session",
    "validate_terminal_integrity",
    "validate_version",
]
