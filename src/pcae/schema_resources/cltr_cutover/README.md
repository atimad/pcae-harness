# `cltr_cutover` schema package (Phase 136H: shared core only)

Packaged, non-authoritative Stage 3 Companion Executable Schema resources,
governed by `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0`. This directory
implements **only** Implementation Group 1 (shared core), per
`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`
Sec.46 and `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`
Sec.13.

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
  manifest.json           deterministic, digest-verified index of shared/*
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
```

No `records/`, `bindings/`, or `views/` directory exists yet -- those are
reserved for future implementation groups (2-11) and are **not** created by
this phase, matching `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0` Sec.3.1's
"reserved, not required to be created before needed" rule.

## What this package is not

- **No runtime record is ever stored here.** This tree contains schema
  *definitions* only (Sec.3.2).
- **No authority-bearing record schema exists here.** `AuthorityEpoch`,
  `AuthorityState`, `CutoverRequest`, `ReadinessPackage`,
  `HumanAuthorization`, `CutoverCandidate`, `Certification`,
  `CASExpectation`, `PublicationAttempt`, `PublicationEvidence`,
  `ConcurrencyConflict`, `RecoveryJournal`, `ReconciliationResult`,
  `Quarantine`, the three binding schemas, and `CompatibilityState` are
  **not implemented** by this phase.
- **No schema in this package establishes lifecycle authority.** Schema
  validity proves shape only (Sec.1, Sec.40). Legacy lifecycle remains the
  sole production authority; CLTR remains derivative.

See `docs/PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_IMPLEMENTATION.md`
for the full implementation report.
