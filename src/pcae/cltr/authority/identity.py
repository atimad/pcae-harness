"""Identifier wrapper types (136Y plan Sec.13; schema source:
``shared/identity.schema.json``).

Dedicated, distinct wrapper types are used for every identifier kind the
schema layer itself already distinguishes, rather than one bare ``str``
used everywhere -- so, for example, a generation identifier can never
silently masquerade as a generic ``record_id``, matching
``identity.schema.json``'s own stated purpose.

Every wrapper: preserves the exact wire string; validates only the
contract-authorized local syntax (a single anchored regex, matching the
executable schema's own pattern); never performs target lookup,
repository access, existence assertion, or authority inference.
"""

from __future__ import annotations

import dataclasses
import re

from pcae.cltr.authority.errors import InvalidIdentifierError

_RECORD_IDENTITY_PATTERN = re.compile(r"^[a-z][a-z0-9-]{7,127}$")
_GENERATION_IDENTITY_PATTERN = re.compile(r"^[a-z][a-z0-9-]{7,127}$")
_MIGRATION_EPOCH_PATTERN = re.compile(r"^(?!.*\.\.)[a-z0-9._-]{1,64}$")
_PHASE_IDENTITY_PATTERN = re.compile(r"^[A-Za-z0-9.]{1,16}$")
_TRANSITION_IDENTITY_PATTERN = re.compile(r"^trans-[a-z0-9-]{2,122}$")
_PRINCIPAL_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._@-]{1,256}$")


def _validate(value: str, pattern: re.Pattern, type_name: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise InvalidIdentifierError(
            f"{type_name}: value does not match the required wire shape"
        )
    return value


@dataclasses.dataclass(frozen=True)
class RecordId:
    """Generic ``record_id`` shape: lowercase-only, family-prefixed,
    8-128 characters total."""

    value: str

    def __post_init__(self) -> None:
        _validate(self.value, _RECORD_IDENTITY_PATTERN, "RecordId")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class GenerationId:
    """Distinct wrapper over the same charset/length rule as ``RecordId``,
    kept as a separate type so a generation identifier can never silently
    masquerade as a generic ``record_id``."""

    value: str

    def __post_init__(self) -> None:
        _validate(self.value, _GENERATION_IDENTITY_PATTERN, "GenerationId")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class MigrationEpochToken:
    """Opaque migration-epoch token, 1-64 characters, lowercase-only."""

    value: str

    def __post_init__(self) -> None:
        _validate(self.value, _MIGRATION_EPOCH_PATTERN, "MigrationEpochToken")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class PhaseIdentity:
    """Repository phase-ID token (e.g. ``"136C"``), 1-16 characters."""

    value: str

    def __post_init__(self) -> None:
        _validate(self.value, _PHASE_IDENTITY_PATTERN, "PhaseIdentity")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class TransitionId:
    """Deterministic digest-derived transition ID, ``trans-`` prefix."""

    value: str

    def __post_init__(self) -> None:
        _validate(self.value, _TRANSITION_IDENTITY_PATTERN, "TransitionId")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class PrincipalIdentifier:
    """Non-secret principal identifier, 1-256 characters, ASCII-only,
    may be email-shaped. Does not verify the principal against any
    identity provider or authentication system."""

    value: str

    def __post_init__(self) -> None:
        _validate(self.value, _PRINCIPAL_IDENTIFIER_PATTERN, "PrincipalIdentifier")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


__all__ = [
    "RecordId",
    "GenerationId",
    "MigrationEpochToken",
    "PhaseIdentity",
    "TransitionId",
    "PrincipalIdentifier",
]
