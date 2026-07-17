# `cltr_cutover` schema package (Phase 136H shared core through Phase 136V/136W Group 11 -- executable-schema track CLOSED, see Phase 136X)

Packaged, non-authoritative Stage 3 Companion Executable Schema resources,
governed by `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0`. This directory
implements Implementation Group 1 (shared core, Phase 136H), Implementation
Group 2 (`AuthorityEpoch`, `AuthorityState`, Phase 136J, independently
verified by Phase 136K), Implementation Group 3 (`CutoverRequest`,
`ReadinessPackage`, Phase 136L, independently verified by Phase 136M),
Implementation Group 4 (`HumanAuthorization`, `CutoverCandidate`,
`Certification`, Phase 136N, independently verified by Phase 136O),
Implementation Group 5 (`PublicationAttempt`, `PublicationEvidence`,
Phase 136P, independently verified by Phase 136Q), the frozen
contract's own Sec.46 Group 8 (`ConcurrencyConflict`,
`RecoveryJournalEntry`, Phase 136R, independently verified by Phase 136S),
Implementation Group 10 (`NotificationAuthorityBinding`,
`MarkerAuthorityBinding`, `ReceiptAuthorityBinding`, Phase 136T,
independently verified by Phase 136U), and Implementation Group 11
(`CompatibilityState`, `QuarantineRecord`, Phase 136V, independently
verified by Phase 136W), per
`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`
Sec.46 and `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`
Sec.13. Per the frozen contract's own Sec.46 table, `ConcurrencyConflict`
and `RecoveryJournalEntry` are one atomic group (8), paired per
CSCH-EXEC-REQ-062's per-group atomicity rule -- 136P/136Q had deliberately
deferred both together, disclosing the same discrepancy against the
task-prompt's looser "expected" inventory framing at each of those phases;
136R implements the pair in full, per explicit confirmation that the frozen
contract governs over prompt text (see
`docs/PHASE_136_RECOVERY_SCHEMA_IMPLEMENTATION.md` for the full disclosure).

**Group 11 is the final row of Sec.46's table -- there is no Group 12.**
The full track (Groups 1-5, 8, 10, 11; Group 9 is schema-less by design,
see below) is independently reviewed as one closed system in Phase 136X
(`docs/PHASE_136_EXECUTABLE_SCHEMA_TRACK_FINAL_REVIEW_AND_NEXT_LAYER_READINESS.md`),
which is the authoritative closure record for this package and supersedes
this README wherever the two disagree.

## Package location

Packaged inside the Python package (`src/pcae/schema_resources/cltr_cutover/`,
not the repository-root `schemas/` directory used by
`schemas/repository_intelligence/`), per Phase 136F's Option A packaging
decision (`docs/PHASE_136_DRAFT_2020_12_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_PREREQUISITE.md`
Sec.11): `packages = ["src/pcae"]` already includes non-`.py` files nested
under `src/pcae/**` in both the wheel and sdist with no extra hatchling
configuration, and `importlib.resources` gives install-mode-independent
lookup.

## Layout

```
cltr_cutover/
  README.md              (this file)
  manifest.schema.json    governs manifest.json
  manifest.json           deterministic, digest-verified index of shared/* and records/*
  shared/
    envelope.schema.json      companion_envelope, timestamp
    enums.schema.json         7 shared typed authority enums + record_family
    identity.schema.json      record_identity, migration_epoch, phase_identity,
                               transition_identity, principal_identifier,
                               generation_identity
    digest.schema.json        sha256_hex + 6 semantically-named digest aliases
    references.schema.json    record_reference, epoch_reference,
                               generation_reference, proof_reference,
                               cas_expectation (Implementation Group 4,
                               third embedding site added Group 5)
    failures.schema.json      shared reason_code vocabulary (24 values)
    limitations.schema.json   limitation_entry, limitations_array,
                               authority_disclosure
  records/
    authority_epoch.schema.json      AuthorityEpoch (Implementation Group 2)
    authority_state.schema.json      AuthorityState (Implementation Group 2)
    cutover_request.schema.json      CutoverRequest (Implementation Group 3)
    readiness_package.schema.json    ReadinessPackage (Implementation Group 3)
    human_authorization.schema.json  HumanAuthorization (Implementation Group 4)
    cutover_candidate.schema.json    CutoverCandidate (Implementation Group 4)
    certification.schema.json       Certification (Implementation Group 4)
    publication_attempt.schema.json  PublicationAttempt (Implementation Group 5)
    publication_evidence.schema.json PublicationEvidence (Implementation Group 5)
    concurrency_conflict.schema.json     ConcurrencyConflict (contract Group 8)
    recovery_journal_entry.schema.json   RecoveryJournalEntry (contract Group 8)
    notification_authority_binding.schema.json  NotificationAuthorityBinding (Group 10)
    marker_authority_binding.schema.json         MarkerAuthorityBinding (Group 10)
    receipt_authority_binding.schema.json        ReceiptAuthorityBinding (Group 10)
    compatibility_state.schema.json      CompatibilityState (Group 11, final group)
    quarantine_record.schema.json        QuarantineRecord (Group 11, final group)
```

No `bindings/` or `views/` directory exists as a separate top-level
directory -- the three Group 10 binding schemas live directly under
`records/`, per the same layout as every other record family. Group 9
(`ReconciliationResult`) has no persisted schema at all per Sec.29 -- it is
a derived, computed, read-only output, not merely deferred; it is not, and
per the frozen contract will never be, a schema file in this package. No
Group 12 exists; Group 11 is confirmed the final row of the frozen
contract's Sec.46 table (re-verified independently at Phase 136W and again
at Phase 136X).

`CutoverRequest` and `ReadinessPackage` are created in a non-circular order
(repaired by Phase 136D): `readiness_package` is created first, its
identity content-derived solely from its own bound fields; `cutover_request`
is created second, binding to the already-existing `readiness_package` via
an opaque `record_reference` (id+digest+family), never a live `$ref` into
that schema file. No versioned "request-v2" re-creation exists or is
required. `HumanAuthorization` is created after both, binding to them via
`request_reference`/`readiness_reference`; `CutoverCandidate` and
`Certification` follow, per Phase 136E's Group 4 dependency ordering. No
schema-level `$ref` cycle exists among any Group 1-4 file.

The embedded `cas_expectation` component (Sec.24), deferred since Phase
136H (`DEFERRED-136H-1`), was added in Phase 136N in
`shared/references.schema.json`, used at two sites in that phase:
`cutover_candidate.schema.json` and `certification.schema.json`. Phase 136P
added the third and final embedding site, `publication_attempt.schema.json`.
Every one of its 11 expected-state fields is unconditionally required --
missing values are never wildcards. Neither Group 8 record embeds
`cas_expectation` -- Sec.27/Sec.28's field tables do not name it, so the
embedding-site count remains exactly three.

`ConcurrencyConflict` and `RecoveryJournalEntry` (Phase 136R) are
independent siblings within Group 8 -- neither's field table references
the other, so no manifest-declared or `$ref` cycle exists between them.
Both reference only already-existing, earlier-group families
(`cutover_request`, `authority_state`, `publication_attempt`).
`RecoveryJournalEntry`'s hash chain (`prior_entry_digest`) points strictly
backward to the immediately preceding entry's own digest, with `null`
reserved for exactly `sequence == 0` -- non-circular by construction.

## What this package is not

- **No runtime record is ever stored here.** This tree contains schema
  *definitions* only (Sec.3.2).
- **`CASExpectation` (as a standalone family) and `ReconciliationResult`
  are not, and per the frozen contract will never be, implemented as
  schema files.** `CASExpectation` is embedded (Sec.24) at three sites,
  never a standalone schema; `ReconciliationResult` is a derived runtime
  output (Sec.29), not a persisted schema.
- **No schema in this package establishes lifecycle authority.** Schema
  validity proves shape only (Sec.1, Sec.40). `AuthorityState`'s and
  `PublicationEvidence`'s `authority_role` may structurally carry the
  value `"authoritative"` (Sec.9), but `is_authoritative` remains
  `const false` unconditionally on both (disclosed limitations
  NON-BLOCKING-136J-1 and NON-BLOCKING-136P-2) -- schema validity never
  itself resolves, creates, or persists current authority.
  A `CutoverRequest` requests; a `ReadinessPackage` reports evidence; a
  `HumanAuthorization` records a recorded decision to permit a scoped
  attempt (never proof that a real human made it); a `CutoverCandidate`
  proposes a bounded attempt; a `Certification` records evidence-based
  verification of a candidate; a `PublicationAttempt` describes an
  attempted publication operation (never performs one); a
  `PublicationEvidence` describes a claimed publication outcome (never
  proves it true); a `ConcurrencyConflict` describes a claimed concurrent
  conflict (never resolves it or selects a winner); a
  `RecoveryJournalEntry` describes a claimed recovery-journal fact (never
  executes the recorded recovery action). None of the nine authorizes,
  certifies, publishes, resolves, recovers, or activates anything in
  reality. Legacy lifecycle remains the sole production authority; CLTR
  remains derivative. The same non-authoritative posture extends
  unconditionally to the five Group 10/11 families
  (`NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
  `ReceiptAuthorityBinding`, `CompatibilityState`, `QuarantineRecord`):
  each describes a claimed binding, compatibility posture, or quarantine
  state, never resolves or enforces one. See Phase 136X for the
  full 16-family disclosure-consistency review.

See `docs/PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_IMPLEMENTATION.md`,
`docs/PHASE_136_AUTHORITY_CORE_SCHEMA_IMPLEMENTATION.md`,
`docs/PHASE_136_REQUEST_AND_READINESS_SCHEMA_IMPLEMENTATION.md`,
`docs/PHASE_136_AUTHORIZATION_AND_CANDIDATE_SCHEMA_IMPLEMENTATION.md`,
`docs/PHASE_136_PUBLICATION_SCHEMA_IMPLEMENTATION.md`,
`docs/PHASE_136_RECOVERY_SCHEMA_IMPLEMENTATION.md`,
`docs/PHASE_136_NOTIFICATION_MARKER_RECEIPT_BINDING_SCHEMA_IMPLEMENTATION.md`,
`docs/PHASE_136_COMPATIBILITY_STATE_QUARANTINE_RECORD_SCHEMA_IMPLEMENTATION.md`,
and `docs/PHASE_136_EXECUTABLE_SCHEMA_TRACK_FINAL_REVIEW_AND_NEXT_LAYER_READINESS.md`
(the track-closure record) for the full implementation and review reports.
