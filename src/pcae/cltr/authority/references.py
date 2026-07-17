"""Reference wrapper types (136Y plan Sec.13; schema source:
``shared/references.schema.json``).

A reference-typed field holds an id+digest(+family) tuple only. No
reference type or function in this module dereferences, existence-checks,
resolves authority for, or performs a network/repository lookup against
the object it names -- a valid reference never implies the referenced
record exists, is current, or is authoritative (contract Sec.1/Sec.40).
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from pcae.cltr.authority.digest import GenerationDigest, PointerDigest, ReferencedRecordDigest
from pcae.cltr.authority.enums import RecordFamily
from pcae.cltr.authority.errors import WrongFamilyReferenceError
from pcae.cltr.authority.identity import GenerationId, MigrationEpochToken, RecordId
from pcae.cltr.authority.sentinels import ABSENT, AbsentType


@dataclasses.dataclass(frozen=True)
class RecordReference:
    """Stable id+digest+family reference tuple
    (``shared/references.schema.json#/$defs/record_reference``).

    ``schema_id``/``schema_version`` are conditionally present (required
    only where a reference crosses a family boundary whose schema-version
    compatibility is not otherwise implied by context); absent by default,
    distinguished from an explicit ``null`` via the ``ABSENT`` sentinel.
    """

    record_id: RecordId
    record_digest: ReferencedRecordDigest
    record_family: RecordFamily
    schema_id: Optional[str] | AbsentType = ABSENT
    schema_version: Optional[str] | AbsentType = ABSENT


@dataclasses.dataclass(frozen=True)
class EpochReference:
    """A shared reference shape binding a companion record to a migration
    epoch and, optionally, a specific authority-epoch record's digest.
    This is a reference shape only; it does not define or authorize an
    ``AuthorityEpoch``/``AuthorityState`` record schema."""

    migration_epoch: MigrationEpochToken
    epoch_digest: PointerDigest | None | AbsentType = ABSENT


@dataclasses.dataclass(frozen=True)
class GenerationReference:
    """Stable id+digest generation reference. Always paired
    (``generation_id`` + ``generation_digest``) -- no bare, unpaired
    generation ID exists anywhere in this package. A valid reference never
    implies the referenced generation is certified, authoritative, or
    that publication of it succeeded."""

    generation_id: GenerationId
    generation_digest: GenerationDigest


def require_family(reference: RecordReference, expected: RecordFamily) -> RecordReference:
    """Fail-closed family-restriction check for an embedding site that
    requires a specific ``record_family`` constant (e.g.
    ``CasExpectation.expected_authority_epoch`` requiring
    ``RecordFamily.AUTHORITY_EPOCH``).

    Mirrors the executable schema's ``allOf`` + ``const`` restriction
    pattern at the Python level via a discriminant check, rather than
    three separate classes per restricted site. Returns the reference
    unchanged when it matches; raises ``WrongFamilyReferenceError``
    otherwise -- never silently coerces or substitutes the family tag.
    """

    if reference.record_family is not expected:
        raise WrongFamilyReferenceError(
            f"expected record_family={expected.value!r}, "
            f"got {reference.record_family.value!r}"
        )
    return reference


__all__ = [
    "RecordReference",
    "EpochReference",
    "GenerationReference",
    "require_family",
]
