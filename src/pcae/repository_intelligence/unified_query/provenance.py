"""Complete six-element provenance attachment (131B Section 9 / 131D Section 10).

Closes 131C's independently-identified gap: elements 1/3/4 already had
real precedent in ``query_engine.py``'s ``_source_artifact``; elements
2 (originating record), 5 (derivation path), and 6 (verification
state) did not. This module makes all six explicit and mandatory for
every reference this package emits.
"""

from __future__ import annotations

from typing import Any

from pcae.repository_intelligence.attribution import verification_state as _verification_state

DIRECT_DERIVATION_PATH = "direct"


def build_provenance(
    *,
    authoritative_artifact: str,
    originating_record: str,
    source_locator_path: str,
    schema_version: str,
    derivation_path: str,
    record_verification_state: str | None,
    commit_sha: str,
) -> dict[str, Any]:
    """Build the mandatory six-element provenance record for one reference.

    All six elements below are always present. Element 6
    (verification state) uses the ``"unknown"`` state value (a real,
    declared member of ``uncertainty_verification_state.schema.json``'s
    own ``state_value`` enum) when the source record carries no
    verification state of its own -- an explicit value, never an
    omitted field (131B Section 9's "fails closed on incomplete chain"
    is satisfied by always emitting a value, not by requiring every
    source schema to be retrofitted first).
    """
    state_value = record_verification_state or "unknown"
    return {
        # Element 1: authoritative artifact.
        "authoritative_artifact": authoritative_artifact,
        # Element 2: originating record.
        "originating_record": originating_record,
        # Element 3: source locator.
        "source_locator": {"locator_type": "file_path", "locator_value": source_locator_path},
        # Element 4: schema version.
        "schema_version": schema_version,
        # Element 5: derivation path.
        "derivation_path": derivation_path,
        # Element 6: verification state.
        "verification_state": _verification_state(
            state_value=state_value,
            state_reason=(
                "carried forward from the source record's own declared state"
                if record_verification_state
                else "source record declares no verification_state/uncertainty_state field"
            ),
            commit_sha=commit_sha,
            state_limitations=[
                "This verification state reflects only the referenced record's "
                "own declaration (or its absence); Unified Query performs no "
                "independent verification of its own."
            ],
        ),
    }
