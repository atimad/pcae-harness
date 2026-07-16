# `cltr_cutover` schema package (Phase 136H shared core + Phase 136J Group 2 + Phase 136L Group 3 + Phase 136N Group 4)

Packaged, non-authoritative Stage 3 Companion Executable Schema resources,
governed by `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0`. This directory
implements Implementation Group 1 (shared core, Phase 136H), Implementation
Group 2 (`AuthorityEpoch`, `AuthorityState`, Phase 136J, independently
verified by Phase 136K), Implementation Group 3 (`CutoverRequest`,
`ReadinessPackage`, Phase 136L, independently verified by Phase 136M), and
Implementation Group 4 (`HumanAuthorization`, `CutoverCandidate`,
`Certification`, Phase 136N), per
`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`
Sec.46 and `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`
Sec.13. Implementation Group 4 is not yet independently verified; that is
Phase 136O's responsibility.

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
                               cas_expectation (Implementation Group 4)
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
```

No `bindings/` or `views/` directory exists yet, and no Implementation
Group 5+ record schema (`PublicationAttempt`, `PublicationEvidence`, and
beyond) exists yet -- those are reserved for future implementation groups
and are **not** created by this phase, matching
`CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0` Sec.3.1's "reserved, not
required to be created before needed" rule and Sec.46/CSCH-EXEC-REQ-062's
per-group independent-verification gate (Group 5 is sequenced after
Group 4's own independent verification, Phase 136O).

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
136H (`DEFERRED-136H-1`), is added by this phase in
`shared/references.schema.json`, used at exactly two sites in this phase:
`cutover_candidate.schema.json` and `certification.schema.json`. Every one
of its 11 expected-state fields is unconditionally required -- missing
values are never wildcards.

## What this package is not

- **No runtime record is ever stored here.** This tree contains schema
  *definitions* only (Sec.3.2).
- **`CASExpectation` (as a standalone family), `PublicationAttempt`,
  `PublicationEvidence`, `ConcurrencyConflict`, `RecoveryJournal`,
  `ReconciliationResult`, `Quarantine`, the three binding schemas, and
  `CompatibilityState` are not implemented** by this phase.
- **No schema in this package establishes lifecycle authority.** Schema
  validity proves shape only (Sec.1, Sec.40). `AuthorityState`'s
  `authority_role` may structurally carry the value `"authoritative"`
  (Sec.9), but its `is_authoritative` field remains `const false`
  unconditionally (disclosed limitation NON-BLOCKING-136J-1) -- schema
  validity never itself resolves, creates, or persists current authority.
  A `CutoverRequest` requests; a `ReadinessPackage` reports evidence; a
  `HumanAuthorization` records a recorded decision to permit a scoped
  attempt (never proof that a real human made it); a `CutoverCandidate`
  proposes a bounded attempt; a `Certification` records evidence-based
  verification of a candidate. None of the five authorizes, certifies, or
  publishes anything in reality. Legacy lifecycle remains the sole
  production authority; CLTR remains derivative.

See `docs/PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_IMPLEMENTATION.md`,
`docs/PHASE_136_AUTHORITY_CORE_SCHEMA_IMPLEMENTATION.md`,
`docs/PHASE_136_REQUEST_AND_READINESS_SCHEMA_IMPLEMENTATION.md`, and
`docs/PHASE_136_AUTHORIZATION_AND_CANDIDATE_SCHEMA_IMPLEMENTATION.md` for
the full implementation reports.
