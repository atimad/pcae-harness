# `cltr_cutover` schema package (Phase 136H shared core + Phase 136J Group 2)

Packaged, non-authoritative Stage 3 Companion Executable Schema resources,
governed by `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0`. This directory
implements Implementation Group 1 (shared core, Phase 136H) and
Implementation Group 2 (`AuthorityEpoch`, `AuthorityState`, Phase 136J),
per `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`
Sec.46 and `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`
Sec.13. Implementation Group 2 is not yet independently verified; that is
Phase 136K's responsibility.

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
                               generation_reference, proof_reference
    failures.schema.json      shared reason_code vocabulary (24 values)
    limitations.schema.json   limitation_entry, limitations_array,
                               authority_disclosure
  records/
    authority_epoch.schema.json   AuthorityEpoch (Implementation Group 2)
    authority_state.schema.json   AuthorityState (Implementation Group 2)
```

No `bindings/` or `views/` directory exists yet, and no Implementation
Group 3+ record schema (`CutoverRequest`, `ReadinessPackage`, and beyond)
exists yet -- those are reserved for future implementation groups and are
**not** created by this phase, matching
`CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0` Sec.3.1's "reserved, not
required to be created before needed" rule and Sec.46/CSCH-EXEC-REQ-062's
per-group independent-verification gate (Group 3 is sequenced after
Group 2's own independent verification, Phase 136K).

## What this package is not

- **No runtime record is ever stored here.** This tree contains schema
  *definitions* only (Sec.3.2).
- **`CutoverRequest`, `ReadinessPackage`, `HumanAuthorization`,
  `CutoverCandidate`, `Certification`, `CASExpectation`,
  `PublicationAttempt`, `PublicationEvidence`, `ConcurrencyConflict`,
  `RecoveryJournal`, `ReconciliationResult`, `Quarantine`, the three
  binding schemas, and `CompatibilityState` are not implemented** by this
  phase.
- **No schema in this package establishes lifecycle authority.** Schema
  validity proves shape only (Sec.1, Sec.40). `AuthorityState`'s
  `authority_role` may structurally carry the value `"authoritative"`
  (Sec.9), but its `is_authoritative` field remains `const false`
  unconditionally (disclosed limitation NON-BLOCKING-136J-1) -- schema
  validity never itself resolves, creates, or persists current authority.
  Legacy lifecycle remains the sole production authority; CLTR remains
  derivative.

See `docs/PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_IMPLEMENTATION.md`
and `docs/PHASE_136_AUTHORITY_CORE_SCHEMA_IMPLEMENTATION.md` for the full
implementation reports.
