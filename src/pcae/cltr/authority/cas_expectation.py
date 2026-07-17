"""``CasExpectation`` (136Y plan Sec.5, Sec.13; schema source:
``shared/references.schema.json#/$defs/cas_expectation``).

Never a standalone document with its own ``record_id``; embedded only at
the sites the executable schema embeds it (``CutoverCandidate``,
``Certification``, ``PublicationAttempt`` -- all implemented in a future
group, not this one). Every field is unconditionally required -- no
wildcard on a missing expected value, which is precisely the mechanism
preventing a missing value from being treated as an unbound wildcard.
"""

from __future__ import annotations

import dataclasses

from pcae.cltr.authority.digest import PointerDigest, Sha256Digest
from pcae.cltr.authority.enums import (
    AuthorityKind,
    CompatibilityMode,
    JournalLockState,
    LegacyLifecycleStateWire,
    RecordFamily,
)
from pcae.cltr.authority.identity import MigrationEpochToken
from pcae.cltr.authority.references import GenerationReference, RecordReference, require_family


@dataclasses.dataclass(frozen=True)
class CasExpectation:
    """The embedded compare-and-swap expectation component. No optional
    sub-fields exist to apply the absent-vs-null sentinel to."""

    expected_authority_kind: AuthorityKind
    expected_authority_epoch: RecordReference
    expected_authoritative_generation: GenerationReference
    expected_authority_pointer_digest: PointerDigest
    expected_authority_state_digest: Sha256Digest
    expected_migration_epoch: MigrationEpochToken
    expected_source_lifecycle_state: LegacyLifecycleStateWire
    expected_compatibility_mode: CompatibilityMode
    expected_journal_lock_state: JournalLockState
    expected_request_reference: RecordReference
    expected_certification_reference: RecordReference

    def __post_init__(self) -> None:
        require_family(self.expected_authority_epoch, RecordFamily.AUTHORITY_EPOCH)
        require_family(self.expected_request_reference, RecordFamily.CUTOVER_REQUEST)
        require_family(self.expected_certification_reference, RecordFamily.CERTIFICATION)


__all__ = ["CasExpectation"]
