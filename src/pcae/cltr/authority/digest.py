"""Digest wrapper types (136Y plan Sec.14; schema source:
``shared/digest.schema.json``).

Every digest-typed field is a distinct wrapper type over the shared
64-character lowercase-hex shape (``sha256_hex``), format-validated at
construction. Construction never computes a missing digest, replaces an
incorrect digest, verifies external evidence, claims cryptographic trust,
or mutates content to make it match a digest. Digest *computation*, if
ever needed, belongs to a separate pure utility delegating to
``pcae.cltr.digest`` (the existing, unchanged Layer-3 digest module) --
never inside a constructor here.

A constructed instance's value is exactly the string the wire payload
supplied -- proof of well-formed shape only, never proof of correctness.
"""

from __future__ import annotations

import dataclasses
import re

from pcae.cltr.authority.errors import InvalidDigestError

_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _validate_sha256_hex(value: str, type_name: str) -> str:
    if not isinstance(value, str) or not _SHA256_HEX_PATTERN.fullmatch(value):
        raise InvalidDigestError(
            f"{type_name}: value is not a well-formed 64-character lowercase "
            "hexadecimal SHA-256 digest"
        )
    return value


@dataclasses.dataclass(frozen=True)
class Sha256Digest:
    """Generic bare ``sha256_hex`` value, used where no more specific
    named alias applies (e.g. ``CasExpectation.expected_authority_state_digest``)."""

    value: str

    def __post_init__(self) -> None:
        _validate_sha256_hex(self.value, "Sha256Digest")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class RecordDigest:
    """The digest of the companion record document itself."""

    value: str

    def __post_init__(self) -> None:
        _validate_sha256_hex(self.value, "RecordDigest")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class ReferencedRecordDigest:
    """The digest of a record referenced by a ``record_reference`` tuple."""

    value: str

    def __post_init__(self) -> None:
        _validate_sha256_hex(self.value, "ReferencedRecordDigest")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class GenerationDigest:
    """The digest of a lifecycle generation referenced by a
    ``generation_reference`` tuple."""

    value: str

    def __post_init__(self) -> None:
        _validate_sha256_hex(self.value, "GenerationDigest")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class PointerDigest:
    """The digest carried by an authority-pointer-shaped reference."""

    value: str

    def __post_init__(self) -> None:
        _validate_sha256_hex(self.value, "PointerDigest")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class JournalEntryDigest:
    """The digest of a prior recovery-journal entry in a hash chain.
    Chain-integrity *verification* is a Layer 4 responsibility, not
    implemented by this type -- it stores the digest string only."""

    value: str

    def __post_init__(self) -> None:
        _validate_sha256_hex(self.value, "JournalEntryDigest")

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


__all__ = [
    "Sha256Digest",
    "RecordDigest",
    "ReferencedRecordDigest",
    "GenerationDigest",
    "PointerDigest",
    "JournalEntryDigest",
]
