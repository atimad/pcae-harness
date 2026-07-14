"""Schema identity constants — CLTR-SCHEMA-001 v1.0.1 (Phase 135I §1, 135J §21.4).

This module carries only identity/version literals. No behavior.
"""

from __future__ import annotations

SCHEMA_ID = "CLTR-SCHEMA-001"
SCHEMA_FAMILY = "pcae.cltr"
SCHEMA_VERSION = "1.0.1"
CONTRACT_VERSION = "CLTR-001/1.0"
COMPATIBILITY_ID = "pcae.cltr.v1"
CANONICAL_NAMESPACE = "pcae.cltr.v1"

#: This production implementation writes and accepts exactly one
#: schema_version: 1.0.1 (135J §21.4's repair of 135I's Blocking
#: adapter-completeness gap). 1.0.0 predates that repair and is explicitly
#: unsupported by this writer/reader, per the phase brief's requirement
#: that "1.0.0" and any unrecognized version fail closed rather than being
#: silently accepted or best-effort interpreted (135I §2.7).
SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})


def is_supported_schema_version(version: str) -> bool:
    """135I §2.7 — any version other than the exact supported one fails closed."""

    return version in SUPPORTED_SCHEMA_VERSIONS
