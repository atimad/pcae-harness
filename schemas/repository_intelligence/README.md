# Repository Intelligence Schemas

Phase 119K introduced the first standalone JSON Schema artifacts for
Repository Intelligence. Phase 119M added the first artifact-family
schema on top of the verified shared components. Phase 119O adds the
Repository Knowledge Snapshot schema as the first content-bearing
artifact-family schema. These schemas live outside `src` so they remain
language-neutral contract artifacts rather than runtime code.

## Scope

Implemented in this slice:

Shared components:

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

Artifact-family schemas:

- `artifacts/contract_conformance_record.schema.json`
- `artifacts/repository_knowledge_snapshot.schema.json`

The Contract Conformance Record schema is the first artifact-family
schema because it records structural contract conformance without
performing repository extraction, graph construction, impact analysis,
Advisory behavior, Decision Evaluation, execution, enforcement, or
repository mutation.

The Repository Knowledge Snapshot schema is the second artifact-family
schema and the first content-bearing artifact-family schema. It
structurally represents source-attributed repository knowledge claims,
repository entities, capabilities, subsystems, relationships, contract
references, documentation references, Evidence links, unknowns,
limitations, boundary disclosures, and disclaimers. It does not perform
repository scanning or Repository Knowledge extraction.

Not implemented in this slice:

- additional artifact-family schemas beyond the two listed above
- validators or validation libraries
- CLI commands
- Python models, Pydantic models, or dataclasses
- automated tests or fixtures
- repository extraction, repository scanning, graph construction, impact
  analysis, or Advisory behavior

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

The Contract Conformance Record schema structurally represents an
artifact under review, contract basis, invariant checks, named
conformance checks, conformance status, violations, limitations,
boundary disclosures, disclaimers, and reviewer/verifier identity. It
does not validate source truth, evidence sufficiency, derivation
correctness, natural-language forbidden claims, lifecycle standing,
Repository State validity, Decision Evaluation outcomes, execution
safety, or remediation correctness.

The Repository Knowledge Snapshot schema structurally represents
declared source-attributed knowledge. It does not validate source truth,
source existence, Evidence sufficiency, claim truth, repository
knowledge completeness, lifecycle standing, Repository State validity,
Decision Evaluation outcomes, execution safety, or derivation
correctness.

Future validators must preserve the same boundary. Other
artifact-family schemas remain future work.

## Next Phase

The recommended next phase is:

`119P - Repository Intelligence Executable Schema Verification: Repository Knowledge Snapshot`

That phase should verify JSON validity, reference consistency, contract
alignment, shared component reuse, source attribution, uncertainty
preservation, and authority-creep safety before another content-bearing
artifact-family schema is implemented.
