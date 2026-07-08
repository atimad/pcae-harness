# Repository Intelligence Schemas

Phase 119K introduces the first standalone JSON Schema artifacts for
Repository Intelligence. These schemas live outside `src` so they remain
language-neutral contract artifacts rather than runtime code.

## Scope

Implemented in this slice:

- `shared/common_artifact_envelope.schema.json`
- `shared/repository_context.schema.json`
- `shared/phase_context.schema.json`
- `shared/release_context.schema.json`
- `shared/derivation_record.schema.json`
- `shared/source_attribution_record.schema.json`
- `shared/evidence_link_record.schema.json`
- `shared/uncertainty_verification_state.schema.json`
- `shared/conflict_supersession_record.schema.json`
- `shared/boundary_disclosure.schema.json`
- `shared/limitation_record.schema.json`
- `shared/disclaimer.schema.json`

Not implemented in this slice:

- artifact-family schemas
- validators or validation libraries
- CLI commands
- Python models, Pydantic models, or dataclasses
- automated tests or fixtures
- repository extraction, graph construction, impact analysis, or Advisory
  behavior

## JSON Schema Draft

The shared schemas use JSON Schema Draft 2020-12:

```text
https://json-schema.org/draft/2020-12/schema
```

Draft 2020-12 is used because it is a modern stable JSON Schema draft with
good support for standalone schema artifacts, `$defs`, and cross-file
references.

## Contract Basis

These shared schemas are constrained by:

- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_EXECUTABLE_SCHEMA_CONTRACT_VERIFICATION.md`
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_EXECUTABLE_SCHEMA_ARCHITECTURE.md`
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_ARTIFACT_CONTRACT_VERIFICATION.md`
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_ARTIFACT_CONTRACT_FREEZE.md`

## Boundary

Schema conformance means structural conformance only. These schemas do not:

- prove source truth or evidence sufficiency
- validate derivation correctness
- establish Repository State
- replace Evidence
- replace Decision Evaluation
- grant Advisory authority
- authorize execution or repository mutation
- establish lifecycle standing

Future validators must preserve the same boundary.

## Next Phase

The recommended next phase is:

`119L - Repository Intelligence Executable Schema Verification: Shared Components`

That phase should verify JSON validity, reference consistency, contract
alignment, and authority-creep safety before artifact-family schemas are
implemented.
