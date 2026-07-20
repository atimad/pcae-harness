"""Explicit-only identity resolution (135E §8, CLTR-001 §5).

This module accepts identity exclusively via explicit, named fields in a
declared input dict. It has zero code path that reads a report title,
Architecture Status label, filename, commit subject, or recent Git history as
an identity source (135D.1's central lesson, 135E §8.3/§8.4/§21).
"""

from __future__ import annotations

import re
from typing import Optional

from pcae.core import phase_id as canonical_phase_id
from pcae.cltr_prototype.models import Identity

TRANSITION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


class IdentityErrorKind:
    MISSING_FIELD = "missing_field"
    MALFORMED = "malformed"
    TRUNCATED = "truncated"
    AMBIGUOUS = "ambiguous"


class IdentityError(Exception):
    def __init__(self, kind: str, field: str, detail: str):
        self.kind = kind
        self.field = field
        self.detail = detail
        super().__init__(f"IdentityError({kind}, field={field}): {detail}")


_REQUIRED_FIELDS = ("transition_id", "phase_id", "repository_identity", "branch_identity")


def _validate_phase_id(raw: str) -> None:
    if not isinstance(raw, str) or not raw:
        raise IdentityError(IdentityErrorKind.MISSING_FIELD, "phase_id", "empty or non-string phase_id")
    # Phase 137R: structural recognition is now owned exclusively by the
    # canonical Phase ID parser (CPIPC-001 §6, §9). This module's own,
    # explicit-only identity boundary (CLTR-001 §5, 135D.1) additionally
    # requires the declared string to carry no incidental whitespace —
    # the canonical parser strips whitespace before matching (CPIPC-REQ-
    # 032), so that check is layered on top here, not inside the shared
    # grammar.
    if raw.strip() != raw:
        raise IdentityError(IdentityErrorKind.TRUNCATED, "phase_id", f"{raw!r} did not round-trip exactly")
    if not canonical_phase_id.is_valid(raw):
        raise IdentityError(IdentityErrorKind.MALFORMED, "phase_id", f"{raw!r} does not match the dotted phase-ID grammar")


def _validate_plain_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise IdentityError(IdentityErrorKind.MISSING_FIELD, field_name, f"{field_name} is required and must be a non-empty string")
    return value


def validate_transition_id(value: object) -> str:
    """Validate a transition ID as one opaque, filesystem-safe segment.

    Persistence uses transition IDs as immutable generation-directory names.
    Restricting the prototype ID grammar here prevents path separators,
    traversal components, absolute paths, drive prefixes, and Unicode lookalike
    separators from ever reaching that boundary.
    """

    value = _validate_plain_id(value, "transition_id")
    if TRANSITION_ID_RE.fullmatch(value) is None:
        raise IdentityError(
            IdentityErrorKind.MALFORMED,
            "transition_id",
            "transition_id must be one ASCII alphanumeric/underscore/hyphen path segment",
        )
    return value


def resolve_identity(declared: dict) -> Identity:
    """Resolve an `Identity` from an explicit declared-field dict.

    `declared` must be a plain mapping containing only explicit,
    caller-supplied values. This function never reads a filename, title,
    commit subject, or the live repository to fill in a missing field —
    a missing required field is always an `IdentityError`, never a fallback.
    """

    if not isinstance(declared, dict):
        raise IdentityError(IdentityErrorKind.MALFORMED, "declared", "identity input must be a dict")

    for required in _REQUIRED_FIELDS:
        if required not in declared:
            raise IdentityError(IdentityErrorKind.MISSING_FIELD, required, f"{required} was not explicitly declared")

    transition_id = validate_transition_id(declared["transition_id"])
    _validate_phase_id(declared["phase_id"])
    phase_id = declared["phase_id"]
    repository_identity = _validate_plain_id(declared["repository_identity"], "repository_identity")
    branch_identity = _validate_plain_id(declared["branch_identity"], "branch_identity")

    task_id: Optional[str] = declared.get("task_id")
    if task_id is not None and not isinstance(task_id, str):
        raise IdentityError(IdentityErrorKind.MALFORMED, "task_id", "task_id, if present, must be a string")
    if task_id == "":
        raise IdentityError(IdentityErrorKind.MISSING_FIELD, "task_id", "task_id, if declared, must not be an empty string (use null/absent instead)")

    return Identity(
        transition_id=transition_id,
        phase_id=phase_id,
        repository_identity=repository_identity,
        branch_identity=branch_identity,
        task_id=task_id,
    )


def identities_equal(a: Identity, b: Identity, *, field_name: str = "transition_id") -> bool:
    """Byte-for-byte identity equality (CLTR-001 §5.2 — no fuzzy comparison)."""

    return getattr(a, field_name) == getattr(b, field_name)


def check_identity_conflict(declared_identity: Identity, embedded_identity: dict) -> Optional[IdentityError]:
    """Compare a resolved `Identity` against another artifact's own claimed
    identity fields (e.g. a narrative report's embedded phase_id).

    This is the direct 135D.1 rehearsal (135E §8.4): the explicit,
    already-resolved identity always wins; a disagreement is reported as a
    conflict, never silently repaired in either direction. This function
    performs comparison only — it has no write path.
    """

    for field_name, value in embedded_identity.items():
        if not hasattr(declared_identity, field_name):
            continue
        declared_value = getattr(declared_identity, field_name)
        if declared_value is not None and value is not None and declared_value != value:
            return IdentityError(
                IdentityErrorKind.AMBIGUOUS,
                field_name,
                f"declared {field_name}={declared_value!r} disagrees with embedded {field_name}={value!r}",
            )
    return None
