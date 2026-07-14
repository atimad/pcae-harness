"""Digest contract (135I §15) — SHA-256, hex lowercase, full coverage minus
self-exclusion of ``record_digest``."""

from __future__ import annotations

import hashlib

from pcae.cltr.canonicalization import canonicalize, canonicalize_dict
from pcae.cltr.models import ProductionCltrRecord

ALGORITHM = "sha256"
EXPECTED_HEX_LENGTH = 64


def compute_record_digest(record: ProductionCltrRecord) -> str:
    """135I §15.2-§15.4: digest input is the canonical bytes of the record
    with ``record_digest`` itself omitted from the object being digested."""

    canonical_bytes = canonicalize(record, include_digest=False)
    return hashlib.sha256(canonical_bytes).hexdigest()


def compute_dict_digest(value: dict) -> str:
    return hashlib.sha256(canonicalize_dict(value)).hexdigest()


def verify_record_digest(record: ProductionCltrRecord) -> bool:
    """135I §15.5 — recompute and compare byte-for-byte; never repaired."""

    if not record.record_digest:
        return False
    if not is_well_formed_digest(record.record_digest):
        return False
    return compute_record_digest(record) == record.record_digest


def is_well_formed_digest(value: str) -> bool:
    if not isinstance(value, str) or len(value) != EXPECTED_HEX_LENGTH:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()
