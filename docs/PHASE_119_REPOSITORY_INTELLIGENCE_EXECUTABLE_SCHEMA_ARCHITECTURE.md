# Phase 119G - Repository Intelligence Executable Schema Architecture

## Purpose

Phase 119G defines how PCAE should later translate the frozen Repository
Intelligence artifact contract into executable schema artifacts without
changing contract meaning, adding authority, or enabling execution.

This phase is architecture only. It creates no executable schema, JSON
Schema file, Python model, Pydantic model, dataclass, validator, command,
test, prototype, extraction engine, graph builder, impact engine, runtime
behavior, Repository Skill behavior, Advisory behavior, Evidence behavior,
Decision Evaluation behavior, Repository State behavior, Permission Broker
behavior, schema directory, or Telegram inbound capability.

## Architecture Context

Track B asks whether PCAE can understand the repository itself. Phases
118A through 118E defined Repository Knowledge, Historical Memory, Change
Impact Analysis, Dependency Knowledge Graph, and Advisory Reasoning
Expansion. Phase 118R reviewed that architecture set. Phase 119A froze the
Repository Intelligence contract, 119B verified it, 119C defined
conceptual schema architecture, 119D reviewed the conceptual schemas, 119E
froze the artifact contract, and 119F verified that artifact contract.

119G is the next step in the same governed sequence. It does not implement
schemas. It defines the architectural rules a later executable-schema
contract freeze and schema implementation must follow.

## Contract Basis

This architecture is constrained by:

- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_ARTIFACT_CONTRACT_VERIFICATION.md`
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_ARTIFACT_CONTRACT_FREEZE.md`
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_CONCEPTUAL_SCHEMA_REVIEW.md`
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_CONCEPTUAL_SCHEMA_ARCHITECTURE.md`
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_CONTRACT_VERIFICATION.md`
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_CONTRACT_FREEZE.md`
- `docs/PHASE_118_REPOSITORY_INTELLIGENCE_ARCHITECTURE_REVIEW.md`
- `docs/PHASE_118_REPOSITORY_KNOWLEDGE_ARCHITECTURE.md`
- `docs/PHASE_118_HISTORICAL_MEMORY_ARCHITECTURE.md`
- `docs/PHASE_118_CHANGE_IMPACT_ANALYSIS_ARCHITECTURE.md`
- `docs/PHASE_118_DEPENDENCY_KNOWLEDGE_GRAPH_ARCHITECTURE.md`
- `docs/PHASE_118_ADVISORY_REASONING_EXPANSION_ARCHITECTURE.md`

Supporting boundaries remain owned by Repository State, Evidence, Decision
Evaluation, Repository Skills, Advisory Repository Skills, Advisory Context
Packages, Advisory Runtime, Runtime Context, Runtime Inspect, lifecycle
artifacts, release governance, transition validation, and no-go boundary
documents.

## Definition of Executable Schema

An executable schema is a future machine-readable artifact that can
validate the structure of Repository Intelligence artifacts against the
frozen artifact contract. It may later be represented as JSON Schema,
Python models, or another governed schema format, but this phase does not
choose or create such an implementation.

An executable schema may later support conformance checks by testing
field presence, field type, allowed vocabulary values, object shape, array
item shape, schema version declarations, artifact family declarations,
and required boundary-disclosure fields.

An executable schema does not decide. It does not authorize. It does not
execute. It does not enforce repository actions. It does not replace
Decision Evaluation, Evidence, Repository State, Repository Transition
Validator, Permission Broker, Advisory Runtime, or lifecycle commands.

## Executable Schema vs Conceptual Schema

A conceptual schema is an architecture description. It explains artifact
purpose, field meaning, relationships, invariants, boundary language, and
future constraints without committing to implementation form.

An executable schema is a future validation artifact. It encodes selected
parts of that architecture as machine-checkable structure. It is narrower
than the conceptual schema because it can only validate what is explicit
in artifact data. It cannot prove claim truth, architectural sufficiency,
source adequacy, or advisory quality.

Future executable schemas must derive from the frozen artifact contract,
not directly from illustrative conceptual examples. Conceptual examples
remain non-normative.

## Executable Schema vs Artifact Contract

The artifact contract is the normative source of meaning. It freezes the
common envelope, twelve artifact family contracts, invariants, vocabulary,
forbidden claims, conformance states, compatibility matrix, and future
constraints.

An executable schema is a partial mechanical expression of that contract.
It can fail an artifact for structural non-conformance, but passing schema
validation never means the artifact is true, sufficient, accepted
Evidence, an approved decision, an authorized action, or execution
permission.

If a future executable schema and the artifact contract disagree, the
artifact contract wins until a governed contract revision explicitly
changes the contract.

## Non-Authority Principle

Executable schemas and validators must be non-authoritative inspection
tools. Their output may be useful evidence about artifact shape, but it
must not be treated as a repository decision.

Schema validity means only: this artifact appears to satisfy the schema
checks that were run. It does not mean:

- the artifact is true;
- all sources are sufficient;
- all evidence candidates are accepted Evidence;
- Advisory recommendation quality is approved;
- Decision Evaluation has approved anything;
- a repository mutation is permitted;
- command execution is allowed;
- lifecycle state may change;
- a phase may complete without separate governed lifecycle checks.

## Schema Family Architecture

Future executable schemas should preserve the twelve frozen artifact
families from 119E. Each family should receive a schema because each has a
distinct purpose, body field set, boundary disclaimer profile, and
cross-cutting record convention.

| Future schema family | Contract source |
| --- | --- |
| Repository Intelligence Package Schema | Repository Intelligence Package Contract |
| Repository Knowledge Snapshot Schema | Repository Knowledge Snapshot Contract |
| Historical Memory Snapshot Schema | Historical Memory Snapshot Contract |
| Dependency Knowledge Graph Snapshot Schema | Dependency Knowledge Graph Snapshot Contract |
| Change Impact Report Schema | Change Impact Report Contract |
| Advisory Intelligence Context Package Schema | Advisory Intelligence Context Package Contract |
| Source Attribution Record Schema | Source Attribution Record Contract |
| Evidence Link Record Schema | Evidence Link Record Contract |
| Uncertainty / Verification State Schema | Uncertainty / Verification State Contract |
| Conflict / Supersession Record Schema | Conflict / Supersession Record Contract |
| Query Result Schema | Query Result Contract |
| Contract Conformance Record Schema | Contract Conformance Record Contract |

The four deferred families from 119E should not receive executable
schemas until a later contract phase freezes them.

## Shared Schema Component Architecture

Future executable schemas should use shared components for common
contract concepts so family schemas cannot drift independently.

Recommended shared components:

- common artifact envelope;
- repository context;
- phase context;
- release context;
- producer identity;
- artifact reference;
- derivation disclosure;
- source attribution record;
- evidence link record;
- verification state vocabulary;
- uncertainty state vocabulary;
- conflict state vocabulary;
- supersession state vocabulary;
- boundary disclosure;
- limitation record;
- non-decision disclaimer;
- non-authority disclaimer;
- no-execution disclaimer;
- conformance status vocabulary.

Shared components should not become a separate authority layer. They are
reuse mechanisms for preserving the frozen contract consistently.

## Common Artifact Envelope Representation

The common artifact envelope should be represented as a required shared
schema component embedded or composed into each artifact-family schema.
Future schemas should preserve the 119E classification of required,
conditional, and optional envelope fields.

The envelope should validate identity fields, family/type fields, version
fields, repository context fields, producer fields, source attribution,
evidence links, uncertainty and verification states, conflict and
supersession summaries, boundary disclaimers, derivation disclosures,
limitations, and references according to their frozen contract meaning.

The envelope must not add implied authority. A valid envelope does not
make the artifact canonical repository state, accepted Evidence, a
decision, or an execution plan.

## Field Classification Architecture

Future executable schemas should represent field classes as follows:

| Field class | Future schema role |
| --- | --- |
| Required fields | Must be present and structurally valid for the artifact family. |
| Conditional fields | Must be present when the contract condition is structurally observable or declared by the artifact. |
| Optional fields | May be absent; when present they must satisfy the same structural and boundary constraints as required fields. |
| Forbidden fields | Must be absent when they encode forbidden claim semantics or authority expansion. |
| Forbidden implications | Should trigger warning or review paths unless they are structurally represented as explicit forbidden fields. |

119F identified a derivation field classification mismatch between the
envelope table and mandatory derivation disclosure language. Future
schema contract freeze should resolve that mismatch before implementation
so schemas do not encode an ambiguity.

## Structural Validation

Structural validation is the proper first responsibility of future
executable schemas. It may check:

- required field existence;
- field type;
- object shape;
- array item shape;
- enum or vocabulary value membership;
- artifact family and artifact type alignment;
- declared contract version;
- declared schema concept version;
- future executable schema version;
- required boundary-disclosure field presence;
- required source attribution or evidence gap marker presence;
- required evidence link or evidence gap marker presence;
- reference object shape;
- conditional field presence when the triggering condition is explicit;
- absence of explicitly prohibited fields.

Structural validation should produce descriptive conformance findings, not
decisions.

## Semantic Validation

Semantic validation is a future validation layer above raw schema checks.
It may inspect relationships among structured fields, sources, evidence
links, uncertainty, conflict, supersession, derivation disclosure, and
boundary claims.

Semantic validation may check:

- whether a source attribution record supports a specific structured
  claim field;
- whether a source staleness state is disclosed;
- whether an evidence link with accepted status references an actual
  Evidence subsystem acceptance artifact;
- whether a `conflicting` uncertainty state references conflict records;
- whether supersession fields preserve superseded artifacts or claims;
- whether derivation disclosure is complete for a derived artifact;
- whether forbidden structured statuses or fields appear;
- whether an Advisory context package preserves non-authority markers.

Semantic validation remains non-authoritative. It can identify possible
non-conformance and review needs. It cannot prove truth or authorize
action.

## Manual and Future-Governance Validation

Some checks must remain manual or governed by future review workflows:

- claim truth;
- source sufficiency;
- architectural interpretation quality;
- advisory recommendation quality;
- whether natural-language prose implies forbidden authority;
- whether a repository relationship is directionally correct;
- whether uncertainty is appropriate rather than merely well-formed;
- whether a stale or superseded artifact should still be consumed;
- whether contract drift has occurred;
- whether a schema-valid artifact should be used in a phase decision.

These checks should not be hidden behind schema-pass language.

## Forbidden Claim Validation Architecture

Future validators may help detect forbidden claims, but they must not
pretend to solve natural-language truth or implication completely.

Detection should be layered:

- explicit prohibited fields are rejected structurally;
- prohibited status values are rejected structurally;
- required non-decision, non-authority, and no-execution disclaimers are
  checked structurally;
- structured forbidden flags or authority markers are rejected;
- string-pattern preflight checks may identify high-risk prose for
  review;
- manual review remains required for implication, framing, and contextual
  authority creep.

Forbidden claim findings should be reported as conformance risks or
non-conformance findings. They must not become allow/block decisions.

## Source Attribution Validation Architecture

Schema-level validation should check source attribution record shape,
source type vocabulary, artifact reference vocabulary, support-level
vocabulary, staleness disclosure, conditional path/digest fields, and
presence of at least one source attribution record or explicit unsupported
claim marker where the contract permits one.

Semantic validation may check whether claim-bearing fields reference
source attribution records and whether support levels are compatible with
known, inferred, weak, stale, or unverified states.

Manual review remains responsible for source sufficiency and whether the
source genuinely supports the claim.

## Evidence Link Validation Architecture

Schema-level validation should check Evidence Link Record shape, evidence
type vocabulary, support strength vocabulary, candidate-or-accepted state,
decision-evaluation eligibility, related artifact references, and
evidence gap marker structure.

Semantic validation may check that accepted evidence states reference an
Evidence subsystem acceptance artifact and that candidate evidence is not
presented as accepted Evidence.

Evidence remains owned by the Evidence subsystem. An Evidence Link Record
bridges to Evidence; it does not replace Evidence and does not become
accepted Evidence by schema validation.

## Uncertainty and Verification-State Validation Architecture

Future schemas should encode the frozen uncertainty and verification state
values as explicit vocabularies. They should validate state presence,
state value membership, verification method fields when required, and
supporting source references.

Semantic validation may check state compatibility. For example, a
`verified` state should disclose a verification method, `conflicting`
should reference conflict records, and stale source states should not be
silently represented as current.

A schema-valid state remains a disclosure, not proof that the assigned
state is correct.

## Conflict and Supersession Validation Architecture

Future schemas should require conflict and supersession records to
preserve disagreement, staleness, replacement history, conflict sources,
resolution state, superseded item details when applicable, superseding
artifact references when applicable, and preserved history.

Semantic validation may check that conflicting claims remain inspectable
and that supersession is additive rather than destructive. It may also
check that result/query artifacts referencing superseded artifacts expose
that supersession state.

Conflict and supersession validation must preserve history. It must not
become cleanup, deletion, or canonical-history rewriting.

## Derivation Disclosure Validation Architecture

Future schemas should require derived artifacts to disclose derivation
inputs, method, rule family, contract basis, and limitations according to
the resolved artifact contract. They should validate the presence and
shape of disclosure fields, not the correctness of derivation itself.

Semantic validation may check that derivation disclosures reference valid
sources, artifact references, contract versions, and producer identity.

Manual review or future governed replay remains responsible for deciding
whether derivation was actually deterministic and contract-preserving.

## Versioning and Compatibility Architecture

Future executable schemas should distinguish at least four version
concepts:

- artifact contract version;
- schema concept version;
- executable schema version;
- repository snapshot or revision identity.

The artifact contract version identifies the normative contract basis.
The schema concept version identifies the conceptual architecture lineage.
The executable schema version identifies the implementation schema
artifact. The repository snapshot identity identifies the repository state
from which the artifact was derived or about which it speaks.

Backward compatibility should mean a newer schema can validate older
contract-compatible artifacts without changing their meaning. Forward
compatibility should mean older consumers can recognize unsupported newer
schema versions and fail closed or warn without interpreting unknown
fields as authority.

Breaking changes include removing required fields, changing field
semantics, changing vocabulary meaning, weakening boundary disclaimers,
turning manual checks into authoritative schema decisions, or changing
the distinction between Evidence, Decision Evaluation, Repository State,
and Repository Intelligence.

Deprecation should be explicit, versioned, and source-attributed. Stale or
superseded schemas should remain inspectable and should not be silently
deleted. Migration expectations should be documented before any artifact
rewriting occurs.

## File Organization Architecture

Future executable schema files should live in a dedicated language-neutral
schema area, recommended as:

- `schemas/repository_intelligence/`

This location is preferable because it makes schemas first-class
artifacts without implying they are Python runtime modules. A future
implementation may optionally expose packaged accessors under
`src/pcae/schemas/repository_intelligence/`, but source-package accessors
should mirror the canonical schema artifacts rather than become the
normative source. `docs/schemas/repository_intelligence/` is less
appropriate for canonical executable schemas because it may blur prose
documentation with machine-readable validation artifacts.

This phase does not create any of these directories.

## Validator Architecture

A future validator may:

- validate artifact structure;
- report schema conformance;
- report missing required fields;
- report invalid vocabulary values;
- report invalid artifact references;
- report missing boundary disclaimers;
- report missing source attribution;
- report missing evidence links or gap markers;
- report possible forbidden claims;
- report unverifiable source links;
- emit Contract Conformance Record candidates.

A future validator may not:

- authorize action;
- approve execution;
- mutate repository state;
- move task contracts;
- promote phase reports;
- send notifications as a side effect of validation;
- run shell commands;
- replace Decision Evaluation;
- replace Evidence;
- replace Repository State;
- replace Repository Transition Validator;
- grant Permission Broker approval;
- produce canonical Repository Intelligence without source attribution;
- treat validation success as advisory recommendation approval.

Validator output should be descriptive and reviewable. It should preserve
input artifacts and produce source-attributed findings.

## Test Architecture

Future executable schemas should have tests only after schema contract
freeze and schema implementation are explicitly authorized.

Recommended future test families:

- schema fixture tests;
- valid artifact fixtures;
- invalid artifact fixtures;
- missing required field fixtures;
- conditional field fixtures;
- forbidden field fixtures;
- boundary disclaimer fixtures;
- forbidden claim prose preflight fixtures;
- source attribution fixtures;
- evidence link fixtures;
- uncertainty state fixtures;
- conflict and supersession fixtures;
- derivation disclosure fixtures;
- version compatibility fixtures;
- stale schema fixtures;
- Contract Conformance Record fixtures.

This phase creates no tests and no fixtures.

## Artifact Generation Constraints

Future artifact generators must:

- declare artifact contract version, schema concept version, executable
  schema version, and repository snapshot identity;
- preserve the common artifact envelope;
- preserve family-specific required, conditional, and optional fields;
- include source attribution or permitted unsupported markers;
- include evidence links or permitted evidence gap markers;
- disclose uncertainty and verification state;
- preserve conflict and supersession history;
- disclose derivation method and limitations for derived artifacts;
- include boundary disclaimers where required;
- avoid forbidden fields, statuses, and authority implications;
- emit artifacts read-only without mutating repository state or lifecycle
  state;
- avoid presenting schema validity as approval.

Generators must not hide unknowns, collapse uncertainty, convert
candidate Evidence into accepted Evidence, or turn advisory context into
Decision Evaluation output.

## Repository Skills Integration Architecture

Future Repository Skills may expose schema validation and artifact
inspection as read-only capabilities. They may report conformance,
summarize structural issues, surface source/evidence gaps, and package
source-attributed context for Advisory.

Repository Skills must not treat schema validation as permission. They
must not execute, mutate, enforce, bypass Decision Evaluation, replace
Evidence, replace Repository State, or convert validation findings into
approval.

## Advisory Consumer Integration Architecture

Future Advisory consumers may consume schema-valid artifacts as bounded,
source-attributed context. Schema validity can help Advisory understand
artifact shape and limitations, but it must not be treated as
recommendation approval.

Advisory outputs that use schema-valid Repository Intelligence must still
preserve source attribution, uncertainty, non-authority language,
Decision Evaluation boundaries, and no-execution language when relevant.

## Decision Evaluation Boundary Preservation

Schema validity differs from decision validity. A schema-valid artifact is
not an approved action. It is not authorization. It is not execution
permission. It is not a TransitionResult. It is not a push approval. It is
not phase completion.

Decision Evaluation remains the only PCAE component responsible for
repository governance decisions. Repository Intelligence artifacts may
provide context or Evidence candidates only.

## Read-Only and No-Execution Boundary Preservation

Future executable schemas and validators must remain read-only. They may
inspect artifacts and produce conformance findings. They must not mutate
repository content, lifecycle state, task state, phase reports, release
state, Evidence state, Decision Evaluation state, or Repository State.

Execution remains unavailable. Schema validation must not invoke shell
commands, run tests, apply patches, generate refactors, route commands,
mediate execution, or claim that execution is safe.

## Future Executable Schema Contract Freeze Readiness

PCAE is ready to proceed to an executable schema contract freeze after
119G, provided that the next phase freezes the implementation-neutral
schema contract before any schema files are created.

The next contract freeze should decide:

- canonical schema family names;
- canonical shared component names;
- exact representation of required, conditional, optional, and forbidden
  fields;
- derivation disclosure classification repair;
- exact schema version naming;
- compatibility policy;
- future file layout;
- validator output vocabulary;
- conformance finding severity vocabulary;
- how Contract Conformance Records relate to validator output;
- which forbidden claim checks are structural, semantic, or manual;
- which test fixture families are required before implementation.

No schema implementation should begin until that freeze is complete.

## Risks

- Schema validity may be mistaken for action approval.
- Validator authority may creep into Decision Evaluation territory.
- Semantic validation may overreach and pretend to prove truth.
- Schema artifacts may drift from the frozen artifact contract.
- Executable schemas may silently change conceptual semantics.
- Source attribution may be reduced to a formal field rather than real
  support.
- Evidence links may be mistaken for accepted Evidence.
- Forbidden claim detection may become brittle.
- Generated artifacts may appear more certain than they are.
- Repository Skills may treat validation as permission.
- Advisory may treat validation as recommendation approval.
- Schema file placement may imply runtime authority if stored only under
  source modules.
- Stale schemas may remain available without clear supersession markers.

## Open Questions

- Should the first implementation phase create all twelve schemas at once
  or begin with the common envelope and cross-cutting records?
- Should Contract Conformance Records be generated by validators or
  authored separately from validator output?
- What severity vocabulary should future validators use for warnings,
  possible forbidden claims, semantic review needs, and hard structural
  non-conformance?
- How should future validators represent natural-language forbidden-claim
  risk without presenting AI or pattern matching as definitive truth?
- Should schema version identifiers include the artifact contract version
  directly or reference it through a separate field only?
- Which compatibility fixtures are required before Repository Skills may
  expose schema validation?

## Recommended Next Phase

Recommended next phase: 119H - Repository Intelligence Executable Schema
Contract Freeze.

Reason: before any executable schema files, validators, fixtures, or
implementation are created, PCAE should freeze the exact executable schema
contract that will govern those later artifacts.

## Non-Goals Confirmation

Phase 119G did not implement an executable schema, JSON Schema, Pydantic
model, dataclass, validator, artifact contract verifier, schema
verification CLI, automated test, schema directory, Repository
Intelligence extraction, Repository Knowledge extraction, Historical
Memory extraction, Change Impact Analysis engine, Dependency Knowledge
Graph construction, graph query engine, Advisory behavior change,
Advisory Runtime change, Advisory Context Package change, Evidence
subsystem change, Repository Skills change, Decision Evaluation change,
runtime behavior change, source code change, test code change, execution,
shell mediation, Permission Broker change, lifecycle redesign, REST,
Dashboard, Web UI, Telegram inbound capability, provider selection,
multi-model orchestration, autonomous coding, model capability expansion,
repository mutation, runtime plugin change, Repository State change, test
execution through Repository Intelligence, automatic patch generation, or
automatic refactoring.
