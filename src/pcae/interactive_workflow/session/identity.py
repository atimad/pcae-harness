"""Session identity: ``CDS-<uuid4>`` (IWC-001 v1.1 §4.1, IWC-REQ-033-035).

"CDS" = Confirmable Decision Session. Identity generation is:

- immutable (a session never changes its own identifier),
- globally unique (uuid4, collision-resistant, no central counter),
- lifecycle-independent (the identifier carries no state information),
- authority-neutral (the identifier carries no authority/ownership claim
  -- ownership is a separate ``Session.owner_identity`` field, never
  encoded into the identifier itself).

Structurally distinct in prefix and allocation timing from CHGR's
``chgr-<uuid4>`` (assigned only at confirmed Publication, CHGR-001 §9) and
from any Typed Authority Model identifier. A session identifier must never
be pre-minted as, reused as, or substituted for a future CHGR's own
identifier.
"""

from __future__ import annotations

import re
import uuid

from pcae.interactive_workflow.errors import InvalidIdentifierError

SESSION_ID_PREFIX = "CDS-"

_UUID4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_SESSION_ID_PATTERN = re.compile(rf"^{re.escape(SESSION_ID_PREFIX)}(?P<uuid>.+)$")


def generate_session_id() -> str:
    """Allocate a new, globally-unique, authority-neutral session id."""

    return f"{SESSION_ID_PREFIX}{uuid.uuid4()}"


def validate_session_id(value: str) -> str:
    """Validate ``value`` matches the ``CDS-<uuid4>`` syntax exactly.

    Returns ``value`` unchanged on success. Raises
    ``InvalidIdentifierError`` on any shape mismatch -- never repairs,
    normalizes case, or strips whitespace on the caller's behalf.
    """

    if not isinstance(value, str):
        raise InvalidIdentifierError(f"Session identifier must be a string, got {type(value)!r}.")
    match = _SESSION_ID_PATTERN.match(value)
    if match is None:
        raise InvalidIdentifierError(
            f"Session identifier {value!r} does not start with {SESSION_ID_PREFIX!r}."
        )
    candidate_uuid = match.group("uuid")
    if not _UUID4_PATTERN.match(candidate_uuid):
        raise InvalidIdentifierError(
            f"Session identifier {value!r} does not carry a well-formed uuid4 suffix."
        )
    return value


def is_valid_session_id(value: str) -> bool:
    try:
        validate_session_id(value)
    except InvalidIdentifierError:
        return False
    return True


__all__ = [
    "SESSION_ID_PREFIX",
    "generate_session_id",
    "validate_session_id",
    "is_valid_session_id",
]
