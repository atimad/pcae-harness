# Repository Intelligence Schemas

Phase 119K introduced the first standalone JSON Schema artifacts for
Repository Intelligence. Phase 119M added the first artifact-family
schema on top of the verified shared components. Phase 119O added the
Repository Knowledge Snapshot schema as the first content-bearing
artifact-family schema. Phase 119Q added the Historical Memory Snapshot
schema as the next content-bearing artifact-family schema because
Historical Memory is the temporal layer over Repository Knowledge. Phase
119S adds the Dependency Knowledge Graph Snapshot schema as the next
content-bearing artifact-family schema because the Dependency Knowledge
Graph is the structural relationship layer over Repository Knowledge.
These schemas live outside `src` so they remain language-neutral
contract artifacts rather than runtime code.

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
- `artifacts/historical_memory_snapshot.schema.json`
- `artifacts/dependency_knowledge_graph_snapshot.schema.json`

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

The Historical Memory Snapshot schema is the third artifact-family schema
and the second content-bearing artifact-family schema. It structurally
represents source-attributed historical events, historical claims,
historical sources, phase lineage, release lineage, decision history,
repair and hardening history, supersession and correction history,
historical relationships, unknowns and gaps, limitations, boundary
disclosures, and disclaimers. It follows Repository Knowledge Snapshot
because Historical Memory describes how repository architecture,
contracts, capabilities, releases, repairs, hardening, and decisions
evolved over time. It does not perform historical extraction, git history
analysis, repository scanning, timeline generation, or lifecycle
validation.

The Dependency Knowledge Graph Snapshot schema is the fourth
artifact-family schema and the third content-bearing artifact-family
schema. It structurally represents a source-attributed, graph-shaped
view of repository relationships: snapshot identity, graph metadata,
graph nodes, graph edges, dependency claims, dependency sources, Evidence
links, dependency paths, graph views, clusters, external references,
unknowns and gaps, limitations, boundary disclosures, and disclaimers.
It follows Historical Memory Snapshot because the Dependency Knowledge
Graph is the structural relationship layer over Repository Knowledge,
complementing the temporal layer Historical Memory already represents.
It does not perform dependency extraction, dependency scanning,
repository scanning, graph construction, graph traversal, graph query
execution, or impact analysis.

Not implemented in this slice:

- additional artifact-family schemas beyond the four listed above
- validators or validation libraries
- CLI commands
- Python models, Pydantic models, or dataclasses
- automated tests or fixtures
- repository extraction, historical extraction, dependency extraction,
  dependency scanning, git history analysis, repository scanning,
  timeline generation, graph construction, graph traversal, graph query
  execution, impact analysis, or Advisory behavior

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

The Historical Memory Snapshot schema structurally represents declared
source-attributed historical memory. It does not validate source truth,
source existence, Evidence sufficiency, historical truth, historical
completeness, chronological completeness, lifecycle standing, Repository
State validity, Decision Evaluation outcomes, execution safety,
derivation correctness, release approval, or whether any historical
claim is sufficient for action. Schema conformance is not historical
truth, is not completeness, is not approval, is not execution permission,
is not lifecycle standing, is not Decision Evaluation, is not Evidence
truth, and is not Repository State truth.

The Dependency Knowledge Graph Snapshot schema structurally represents a
declared, source-attributed, graph-shaped relationship view. It does not
validate source truth, source existence, Evidence sufficiency, dependency
truth, dependency completeness, graph correctness, lifecycle standing,
Repository State validity, Decision Evaluation outcomes, execution
safety, or derivation correctness. Schema conformance is not dependency
truth, is not dependency completeness, is not graph construction, is not
graph queryability, is not impact analysis, is not approval, is not
execution permission, is not lifecycle standing, is not Decision
Evaluation, is not Evidence truth, and is not Repository State truth.

Future validators must preserve the same boundary. Other
artifact-family schemas remain future work.

## Next Phase

The recommended next phase is:

`119T - Repository Intelligence Executable Schema Verification: Dependency Knowledge Graph Snapshot`

That phase should verify JSON validity, reference consistency, contract
alignment, shared component reuse, graph/non-graph boundary preservation,
relationship source attribution, uncertainty preservation, and
authority-creep safety before another content-bearing artifact-family
schema is implemented.
