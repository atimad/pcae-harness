"""Packaged, non-authoritative schema resources (Phase 136F, extended 136H, 136J, 136L, 136N, 136P).

Resolves PREREQUISITE-136E-1: the previous wheel/sdist packaging did
not include any schema-resource directory. Phase 136F proved the
packaging mechanism using a generic packaging smoke-test schema
(``smoke/generic_smoke_record.schema.json``); Phase 136H added the
Stage 3 Companion Executable Schema shared core
(``cltr_cutover/shared/*``, Implementation Group 1); Phase 136J added
Implementation Group 2, the AuthorityEpoch and AuthorityState record
schemas; Phase 136L added Implementation Group 3, the CutoverRequest
and ReadinessPackage record schemas; Phase 136N added Implementation
Group 4, the HumanAuthorization, CutoverCandidate, and Certification
record schemas; Phase 136P adds Implementation Group 5, the
PublicationAttempt and PublicationEvidence record schemas
(``cltr_cutover/records/*``); Phase 136R adds the frozen contract's own
Sec.46 Group 8, the ConcurrencyConflict and RecoveryJournalEntry record
schemas, paired atomically per CSCH-EXEC-REQ-062, while still packaging
the shared core and smoke schema unchanged.

No typed model, semantic validator, or authority resolver/state/pointer
is packaged here, and no Group 9+ record schema (QuarantineRecord,
CompatibilityState, and beyond) exists yet. Schema validity of a packaged
record never itself establishes lifecycle authority, cutover eligibility,
authorization, certification authenticity, publication success, or
recovery truth. See ``cltr_cutover/README.md`` and
``docs/PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_IMPLEMENTATION.md``
/ ``docs/PHASE_136_AUTHORITY_CORE_SCHEMA_IMPLEMENTATION.md``
/ ``docs/PHASE_136_REQUEST_AND_READINESS_SCHEMA_IMPLEMENTATION.md``
/ ``docs/PHASE_136_AUTHORIZATION_AND_CANDIDATE_SCHEMA_IMPLEMENTATION.md``
/ ``docs/PHASE_136_PUBLICATION_SCHEMA_IMPLEMENTATION.md``
/ ``docs/PHASE_136_RECOVERY_SCHEMA_IMPLEMENTATION.md``
for the full disposition.
"""
from __future__ import annotations

from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from typing import Iterator


@contextmanager
def smoke_schema_root() -> Iterator[Path]:
    """Yield a real filesystem path to the packaged generic smoke-schema root.

    Works from an editable install, an installed wheel, or a source
    checkout. Performs no network access.
    """
    package_root = resources.files(__package__) / "smoke"
    with resources.as_file(package_root) as path:
        yield path


@contextmanager
def cltr_cutover_root() -> Iterator[Path]:
    """Yield a real filesystem path to the packaged ``cltr_cutover`` root.

    Contains the Implementation Group 1 shared core (Phase 136H):
    ``shared/*.schema.json``, ``manifest.schema.json``, ``manifest.json``,
    ``README.md``; the Implementation Group 2 record schemas (Phase
    136J): ``records/authority_epoch.schema.json``,
    ``records/authority_state.schema.json``; the Implementation Group 3
    record schemas (Phase 136L): ``records/cutover_request.schema.json``,
    ``records/readiness_package.schema.json``; the Implementation
    Group 4 record schemas (Phase 136N):
    ``records/human_authorization.schema.json``,
    ``records/cutover_candidate.schema.json``,
    ``records/certification.schema.json``; and the Implementation
    Group 5 record schemas (Phase 136P):
    ``records/publication_attempt.schema.json``,
    ``records/publication_evidence.schema.json``; and the frozen
    contract's own Sec.46 Group 8 record schemas (Phase 136R):
    ``records/concurrency_conflict.schema.json``,
    ``records/recovery_journal_entry.schema.json``. No ``bindings/`` or
    ``views/`` directory exists, and no Group 9+ record schema exists yet.
    Works from an editable install, an installed wheel, or a source
    checkout. Performs no network access.
    """
    package_root = resources.files(__package__) / "cltr_cutover"
    with resources.as_file(package_root) as path:
        yield path


@contextmanager
def chgr_root() -> Iterator[Path]:
    """Yield a real filesystem path to the packaged ``chgr`` root.

    Contains the Canonical Human Governance Record (CHGR) schema family
    (Phase 143E, CHGR-001 v1.0): ``shared/*.schema.json``,
    ``manifest.schema.json``, ``manifest.json``, ``README.md``, and the six
    implemented ``records/*.schema.json`` types (``decision_template``,
    ``human_governance_record``, ``human_confirmation_evidence``,
    ``governance_record_provenance``, ``governance_record_integrity``,
    ``governance_record_lifecycle_event``). Wholly independent of
    ``cltr_cutover`` -- no shared file, ``$ref``, or Python module is reused
    across the two packages (CHGR-001 Sec.16/Sec.19.1). Works from an
    editable install, an installed wheel, or a source checkout. Performs no
    network access.
    """
    package_root = resources.files(__package__) / "chgr"
    with resources.as_file(package_root) as path:
        yield path


@contextmanager
def rollback_approval_root() -> Iterator[Path]:
    """Yield a real filesystem path to the packaged ``rollback_approval`` root.

    Contains the Rollback Approval Evidence schema family (Phase 149L;
    RAE-001 v1.0, ``docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md``):
    ``manifest.schema.json``, ``manifest.json``, and two
    ``records/*.schema.json`` types (``rollback_approval_binding``,
    ``rollback_approval_revocation``). A new, dedicated package sibling to
    ``chgr`` and ``cltr_cutover``, not nested inside either -- RAE-REQ-003
    forbids storing this family under ``cltr_cutover``, and it is not a
    CHGR-001 record family (RAE-REQ-016). Works from an editable install,
    an installed wheel, or a source checkout. Performs no network access.
    """
    package_root = resources.files(__package__) / "rollback_approval"
    with resources.as_file(package_root) as path:
        yield path
