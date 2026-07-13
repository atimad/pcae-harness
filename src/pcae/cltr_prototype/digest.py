"""SHA-256 record digesting and verification (135E §7).

The digest is computed over the canonicalized record content, excluding the
`record_digest` field itself (self-exclusion). A standalone `verify()`
function recomputes the digest independently and compares byte-for-byte.
"""

from __future__ import annotations

import hashlib

from pcae.cltr_prototype.canonicalization import canonicalize
from pcae.cltr_prototype.models import TransitionRecord


def digest(record: TransitionRecord) -> str:
    """Compute the SHA-256 hex digest of a record's sealed content."""

    canonical_bytes = canonicalize(record, include_digest=False)
    return hashlib.sha256(canonical_bytes).hexdigest()


def seal(record: TransitionRecord) -> TransitionRecord:
    """Return a new record with `record_digest` computed and set."""

    return record.with_updates(record_digest=digest(record))


def verify(record: TransitionRecord, expected_digest: str) -> bool:
    """Recompute the digest and compare byte-for-byte against `expected_digest`."""

    return digest(record) == expected_digest


def verify_self(record: TransitionRecord) -> bool:
    """Verify a sealed record's own stored `record_digest` matches its content."""

    if record.record_digest is None:
        return False
    return verify(record, record.record_digest)
