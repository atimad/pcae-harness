"""Immutable Publication Coordinator models (Phase 144C; PEC-001 §2, §6).

Three frozen dataclasses, each a pure value object with no behavior beyond
structural validation in ``__post_init__``, mirroring the discipline every
``interactive_workflow`` model already follows (e.g.
``PublicationReadinessPackage``):

- ``PublicationAuthorizationEvent`` -- the concrete, auditable evidence of
  a Publication Authorization Event (PEC-REQ-004, PEC-REQ-038): operator
  identity, timestamp, and the exact ``package_id`` named. Carries no
  authority beyond itself (PEC-REQ-092) and is never reusable once
  consumed (PEC-REQ-033).
- ``PublicationExecutionContext`` -- immutable per-attempt context used
  for deterministic execution, diagnostics, and replay protection
  (governing prompt, "PublicationExecutionContext"). Owns no authority
  decision.
- ``PublicationExecutionResult`` -- immutable, deterministic report of one
  Publication Execution attempt's outcome (governing prompt,
  "PublicationExecutionResult"). Carries no authority decision, no mutable
  reference, and no Interactive Workflow state.
"""
from __future__ import annotations

import dataclasses
from typing import Optional, Tuple

PUBLICATION_EXECUTION_SCHEMA_VERSION = "governance-publication-execution/0.1"


def _require_nonempty_str(owner: str, field_name: str, value: object) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{owner}.{field_name} must be a non-empty string, got {value!r}.")


@dataclasses.dataclass(frozen=True)
class PublicationAuthorizationEvent:
    """The concrete, auditable occurrence that constitutes Publication
    Authorization (PEC-REQ-004). Every field here is required evidence
    per PEC-REQ-038: operator identity, invocation timestamp, and the
    exact ``package_id`` this event names (never a class, batch, or
    future set of packages -- PEC-REQ-040)."""

    event_id: str
    operator_id: str
    package_id: str
    invoked_at: str

    def __post_init__(self) -> None:
        _require_nonempty_str("PublicationAuthorizationEvent", "event_id", self.event_id)
        _require_nonempty_str("PublicationAuthorizationEvent", "operator_id", self.operator_id)
        _require_nonempty_str("PublicationAuthorizationEvent", "package_id", self.package_id)
        _require_nonempty_str("PublicationAuthorizationEvent", "invoked_at", self.invoked_at)


@dataclasses.dataclass(frozen=True)
class PublicationExecutionContext:
    """Immutable per-attempt execution context (governing prompt,
    "Purpose: deterministic execution, diagnostics, replay protection.
    No authority ownership."). Carries no field asserting authorization
    or readiness -- both remain owned exactly where PEC-001 §5/§8 assigns
    them."""

    attempt_id: str
    package_id: str
    session_id: str
    operator_id: str
    authorization_event_id: str
    authorization_invoked_at: str
    evaluated_at: str
    schema_version: str = PUBLICATION_EXECUTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "attempt_id",
            "package_id",
            "session_id",
            "operator_id",
            "authorization_event_id",
            "authorization_invoked_at",
            "evaluated_at",
            "schema_version",
        ):
            _require_nonempty_str(
                "PublicationExecutionContext", field_name, getattr(self, field_name)
            )


@dataclasses.dataclass(frozen=True)
class PublicationExecutionResult:
    """Immutable, deterministic report of one Publication Execution
    attempt (governing prompt, "PublicationExecutionResult"). Include
    only: success/failure, publication identifier, deterministic
    diagnostics, timestamps, and immutable execution metadata. Never
    includes an authority decision, a mutable reference, or Interactive
    Workflow state."""

    attempt_id: str
    success: bool
    package_id: str
    session_id: str
    record_id: Optional[str]
    diagnostics: Tuple[str, ...]
    evaluated_at: str
    completed_at: str
    error_type: Optional[str] = None
    failure_reason: Optional[str] = None
    schema_version: str = PUBLICATION_EXECUTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise ValueError(
                f"PublicationExecutionResult.success must be a bool, got {self.success!r}."
            )
        for field_name in ("attempt_id", "package_id", "evaluated_at", "completed_at", "schema_version"):
            _require_nonempty_str("PublicationExecutionResult", field_name, getattr(self, field_name))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))
        if self.success:
            if not self.record_id:
                raise ValueError(
                    "PublicationExecutionResult.record_id must be non-empty when success is True."
                )
            if self.error_type is not None or self.failure_reason is not None:
                raise ValueError(
                    "PublicationExecutionResult must not carry error_type/failure_reason "
                    "when success is True."
                )
        else:
            if self.record_id is not None:
                raise ValueError(
                    "PublicationExecutionResult.record_id must be None when success is False; "
                    "no CHGR was created (PEC-REQ-052)."
                )
            if not self.error_type or not self.failure_reason:
                raise ValueError(
                    "PublicationExecutionResult must carry error_type and failure_reason "
                    "when success is False."
                )


__all__ = [
    "PUBLICATION_EXECUTION_SCHEMA_VERSION",
    "PublicationAuthorizationEvent",
    "PublicationExecutionContext",
    "PublicationExecutionResult",
]
