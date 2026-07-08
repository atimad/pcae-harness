# Phase 119H - Repository Intelligence Executable Schema Contract Freeze

## Purpose

Phase 119H freezes the initial Repository Intelligence executable schema
contract. This contract defines the binding rules future executable
schemas, validators, and schema-valid artifacts must obey so they
preserve the frozen Repository Intelligence artifact contract without
adding authority, execution, mutation, or decision-making.

This phase is contract-freeze only. It creates no executable schema, JSON
Schema file, Python model, Pydantic model, dataclass, validator,
contract verifier, CLI, automated test, prototype, schema directory,
extractor, graph builder, impact engine, Repository Skill behavior,
Advisory behavior, Evidence behavior, Decision Evaluation behavior,
Repository State behavior, Permission Broker behavior, runtime behavior,
execution capability, or Telegram inbound capability.

## Contract Freeze Context

Track B asks whether PCAE can understand the repository itself while
preserving read-only, non-executing, non-authoritative boundaries.

Phases 118A through 118E defined the Repository Intelligence architecture
stack. Phase 118R reviewed that stack. Phase 119A froze the Repository
Intelligence contract. Phase 119B verified that contract. Phase 119C
defined conceptual schema architecture. Phase 119D reviewed it. Phase
119E froze the Repository Intelligence artifact contract. Phase 119F
verified that artifact contract. Phase 119G defined how future
executable schemas should be architected.

119H now freezes the contract that any future executable schema work must
obey before executable schema implementation, validator implementation,
schema verification tooling, tests, or prototype planning begins.

## Contract Basis

This contract is based on:

- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_EXECUTABLE_SCHEMA_ARCHITECTURE.md`
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

Supporting boundary contracts remain owned by:

- `docs/PCAE_REPOSITORY_STATE_KERNEL.md`
- `docs/PHASE_115B_REPOSITORY_EVIDENCE_CONTRACT_FREEZE.md`
- `docs/PCAE_DECISION_FRAMEWORK.md`
- `docs/PHASE_115I_REPOSITORY_SKILLS_CONTRACT_FREEZE.md`
- `docs/PHASE_115Q_ADVISORY_REPOSITORY_SKILLS_CONTRACT_FREEZE.md`
- `docs/PHASE_115W_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md`
- `docs/PHASE_113_ADVISORY_RUNTIME_CONTRACT_FREEZE.md`
- `docs/PHASE_112_RUNTIME_CONTEXT_CONTRACT_FREEZE.md`
- `docs/PHASE_111_RUNTIME_INSPECT_VERIFICATION.md`
- `docs/PHASE_92_PHASE_REPORT_ARTIFACT_MODEL.md`
- `docs/PHASE_117D_V0_2_RELEASE_CANDIDATE_PREPARATION.md`
- `docs/PHASE_113_REPOSITORY_TRANSITION_VALIDATOR_CONTRACT_FREEZE.md`

## Contract Status

This document is the initial Repository Intelligence executable schema
contract freeze.

It freezes executable schema purpose, scope, schema families, shared
schema components, field-classification rules, validation boundaries,
validator constraints, compatibility rules, generator constraints,
Repository Skills exposure constraints, Advisory consumer constraints,
Decision Evaluation boundaries, and read-only/no-execution boundaries.

Any future executable schema implementation, validator implementation,
schema verification CLI, or schema-valid artifact generator must conform
to this contract unless a later governed contract revision explicitly
changes it.

## Executable Schema Contract Definition

An executable schema contract in PCAE is the frozen set of structural
and boundary-preserving rules that future machine-readable executable
schemas must encode.

This contract is not itself an executable schema. It is the normative
source that constrains future executable schemas. It freezes:

- what future executable schemas are for;
- which artifact families they cover;
- which shared components they reuse;
- what they may validate structurally;
- what they must not claim to validate;
- what remains semantic validation;
- what remains manual or future-governance validation;
- what makes future schemas, validators, and schema-valid artifacts
  non-conforming.

## Executable Schema Purpose Contract

Future executable schemas exist to validate Repository Intelligence
artifact structure and to support future schema-conformance checks.

They may validate field presence, field type, object shape, array shape,
declared vocabulary membership, reference shape, required disclaimers,
declared version fields, and structurally observable conditional fields.

They do not exist to:

- authorize repository actions;
- approve execution;
- produce governance verdicts;
- replace Decision Evaluation;
- replace Evidence;
- replace Repository State;
- convert Advisory recommendations into approval;
- claim that an artifact is true simply because it is schema-valid.

## Executable Schema Non-Authority Contract

Future executable schemas and validators:

- do not decide;
- do not authorize;
- do not execute;
- do not enforce repository actions;
- do not mutate repository state;
- do not mutate lifecycle state;
- do not replace Decision Evaluation;
- do not replace Evidence;
- do not replace Repository State;
- do not bypass Repository Transition Validator;
- do not grant Permission Broker authority;
- do not convert Advisory recommendations into approval.

Schema validity is descriptive only. It means the artifact satisfied the
schema checks that were run. It does not mean the artifact is true,
sufficient, accepted Evidence, a valid decision, an approved action, or
execution permission.

## Schema Family Contract

The initial executable schema family set is frozen to the same twelve
artifact families frozen in 119E:

1. Repository Intelligence Package Schema
2. Repository Knowledge Snapshot Schema
3. Historical Memory Snapshot Schema
4. Dependency Knowledge Graph Snapshot Schema
5. Change Impact Report Schema
6. Advisory Intelligence Context Package Schema
7. Source Attribution Record Schema
8. Evidence Link Record Schema
9. Uncertainty / Verification State Schema
10. Conflict / Supersession Record Schema
11. Query Result Schema
12. Contract Conformance Record Schema

No additional top-level executable schema family is frozen by this
contract. Deferred artifact families from 119E remain out of scope until
they receive their own governed artifact contract freeze.

## Shared Schema Component Contract

The following reusable executable schema components are frozen as the
shared building blocks for future schema implementation:

- common artifact envelope;
- repository context;
- phase context;
- release context;
- producer identity;
- artifact reference;
- derivation record;
- source attribution record;
- evidence link record;
- verification state enum;
- uncertainty state enum;
- conflict state;
- supersession state;
- boundary disclosure;
- limitation record;
- non-decision disclaimer;
- non-authority disclaimer;
- no-execution disclaimer;
- conformance status vocabulary.

These shared components are frozen as reusable contract concepts. They
do not become a new authority layer.

## Common Artifact Envelope Schema Contract

Future executable schemas must represent the 119E common artifact
envelope as a reusable shared schema component used by all twelve schema
families.

The future executable schema representation of the common envelope must
preserve:

- artifact identity;
- artifact family and artifact type;
- artifact contract version;
- schema concept version;
- future executable schema version;
- repository identity;
- repository revision or snapshot context;
- producer identity;
- generated-at timestamp;
- source attribution presence;
- evidence link presence or governed gap marker;
- verification state;
- uncertainty state;
- conflict state;
- supersession state;
- limitations;
- required boundary disclosures;
- derivation disclosures when applicable;
- optional and conditional envelope fields exactly as governed by the
  artifact contract.

The envelope schema must not silently change the meaning of any 119E
envelope field.

## Field Classification Contract

Future executable schemas must preserve four field classes plus one
implication boundary:

- Required fields: must exist and be structurally valid.
- Conditional fields: must exist when the contract condition is true and
  structurally observable from artifact content or declared context.
- Optional fields: may be absent; if present they must be structurally
  valid and boundary-preserving.
- Forbidden fields: must not appear if they encode forbidden claim or
  authority semantics.
- Forbidden implications: may trigger warnings or manual review but are
  not treated as fully solved by schema logic alone.

Field classification must preserve the 119E artifact contract and the
119F verification findings. In particular, future schema work must not
ignore the 119F finding that derivation field classification requires
clarification before implementation.

## Structural Validation Contract

Future executable schemas may validate structurally:

- required field existence;
- field type;
- object shape;
- array item shape;
- vocabulary or enum membership;
- artifact family and artifact type alignment;
- declared contract version;
- declared schema concept version;
- declared executable schema version;
- required boundary-disclosure field presence;
- source attribution presence or permitted unsupported marker;
- evidence link presence or permitted evidence gap marker;
- reference object shape;
- structurally observable conditional fields;
- absence of explicitly prohibited fields;
- presence of required conflict, supersession, derivation, limitation, or
  disclaimer fields when the contract condition is declared.

Future executable schemas must not claim that structural validity proves
truth, sufficiency, or actionability.

## Semantic Validation Boundary Contract

Future executable schemas must not pretend to prove:

- source truth;
- source sufficiency;
- claim truth;
- derivation correctness;
- evidence sufficiency;
- advisory quality;
- architectural correctness;
- decision validity;
- action approval.

Semantic validation may exist as a separate future layer above structural
schema checks. That layer may inspect relationships among structured
fields, but it remains non-authoritative and cannot replace Decision
Evaluation or human review.

## Manual and Future-Governance Validation Boundary Contract

The following remain manual or future-governance validation concerns:

- whether a claim is true;
- whether a source actually supports a claim;
- whether supporting sources are sufficient;
- whether a derivation method was truly deterministic;
- whether an evidence link is materially sufficient;
- whether Advisory quality is acceptable;
- whether architectural interpretation is correct;
- whether a schema-valid artifact should be used in a governance
  decision;
- whether a stale or superseded artifact remains appropriate to consume;
- whether prose implies forbidden authority despite formal disclaimers.

Future executable schema work must not collapse these concerns into
mechanical schema success.

## Forbidden Claim Validation Contract

Future forbidden-claim checks may use only bounded, conservative
approaches such as:

- prohibited fields;
- prohibited enum or status values;
- required disclaimers;
- explicit boundary fields;
- structured forbidden flags;
- conservative string-pattern preflight warnings;
- manual review triggers.

Future validators must not claim full natural-language truth analysis or
full implication analysis. They may flag likely violations conservatively
but must fail closed to review rather than claim semantic certainty they
cannot justify.

## Source Attribution Validation Contract

Future schema-level source attribution validation must preserve the 119E
source attribution contract by validating:

- source attribution record shape;
- source locator vocabulary;
- artifact reference vocabulary;
- support-level vocabulary;
- source type vocabulary;
- staleness disclosure fields;
- required conditional fields such as path or digest/commit reference;
- presence of source attribution on claim-bearing artifacts unless the
  contract explicitly permits uncertainty or unsupported markers.

Future semantic validation may check whether structured claims reference
source attribution records and whether support levels are compatible with
declared verification or uncertainty states.

No future executable schema may claim source sufficiency or source truth
purely from structure.

## Evidence Link Validation Contract

Future executable schemas must preserve the Evidence boundary by treating
Evidence Link Records as bridge records, not accepted Evidence.

Schema-level validation may enforce:

- evidence link record shape;
- evidence type vocabulary;
- support strength vocabulary;
- candidate-or-accepted state vocabulary;
- decision-evaluation eligibility vocabulary;
- related artifact references;
- evidence gap marker shape.

Future semantic validation may verify that any
`accepted_by_evidence_subsystem` state references an actual Evidence
subsystem artifact. It must not replace the Evidence subsystem’s
authority over accepted Evidence.

## Uncertainty / Verification-State Validation Contract

Future executable schemas must preserve the frozen uncertainty and
verification-state vocabularies from 119E and the semantic distinction
identified in 119F.

Future schemas must require:

- `verification_state`;
- `uncertainty_state`;
- required supporting sources;
- `verification_method` where the contract requires it;
- state-linked rationale or references where the contract requires them.

Future schema work must not collapse unknown, unverified, inferred,
stale, superseded, conflicting, partially verified, and verified states
into a simplified success/failure model.

## Conflict / Supersession Validation Contract

Future executable schemas must preserve conflict and supersession as
first-class visibility requirements, not cleanup behavior.

Future schema representations must preserve:

- conflict record shape;
- conflict source references;
- conflict type vocabulary;
- resolution-state vocabulary;
- superseded item details where required;
- superseding artifact reference where required;
- supersession reason where required;
- preserved history.

No future executable schema may allow supersession to delete or conceal
conflicting or superseded history.

## Derivation Disclosure Validation Contract

Future executable schemas must preserve derivation disclosure as a
contract requirement for derived artifacts.

Future schema-level validation must require, where applicable:

- derivation inputs;
- derivation method;
- derivation rule family;
- derivation limitations;
- derivation nondeterminism exclusions;
- contract-version and source references sufficient to describe the
  derivation claim.

Future schema work must not require derivation correctness proof at the
structural-schema layer. That remains semantic or future-governance
validation.

## Versioning and Compatibility Contract

Future executable schema work must preserve four distinct version
concepts:

- artifact contract version;
- schema concept version;
- executable schema version;
- repository snapshot or repository revision identity.

Compatibility policy is frozen as follows:

- Backward compatibility means newer executable schemas can validate
  older contract-compatible artifacts without changing their meaning.
- Forward compatibility means older consumers must fail closed or warn
  when they encounter unsupported newer schema versions.
- Breaking changes include removing required fields, changing field
  semantics, weakening boundary disclaimers, changing vocabulary
  meaning, or converting descriptive schema outcomes into authority.
- Deprecation must be explicit, source-attributed, and versioned.
- Migration expectations must be documented before any artifact rewrite
  or canonical promotion behavior changes.
- Stale schemas must remain inspectable and explicitly marked stale.
- Superseded schemas must remain inspectable and explicitly linked to
  their replacements.

Future executable schema implementations must not silently change
conceptual meaning across versions.

## Future File Organization Contract

Future executable schema files are strongly recommended to live under:

- `schemas/repository_intelligence/`

This contract freezes that recommendation as the preferred canonical
location because it preserves a language-neutral distinction between the
normative executable schema artifacts and any future language-specific
access layers.

This phase does not create the directory.

## Future Validator Contract

Future validators may:

- validate artifact structure;
- report conformance findings;
- report missing required fields;
- report invalid vocabulary values;
- report invalid reference shape;
- report missing disclaimers;
- report source-attribution gaps;
- report evidence-link gaps;
- report uncertainty/conflict/supersession disclosure gaps;
- report likely forbidden-claim risks conservatively;
- emit descriptive conformance summaries.

Future validators may not:

- authorize action;
- approve execution;
- approve commit or push;
- mutate repository state;
- mutate lifecycle state;
- send notifications as a side effect of validation;
- replace Decision Evaluation;
- replace Evidence;
- replace Repository State;
- replace Repository Transition Validator;
- bypass Permission Broker or execution boundaries;
- report `safe_to_push`, `execution_approved`, `authorize_mutation`, or
  equivalent verdicts.

A future validator is non-conforming if it crosses any of these
authority boundaries.

## Future Test Contract

Future executable schema implementation phases must include tests, but
this contract creates none.

The future minimum test contract should cover:

- valid artifact fixtures;
- invalid artifact fixtures;
- required-field failures;
- conditional-field failures;
- optional-field acceptance;
- forbidden-field failures;
- source-attribution fixtures;
- evidence-link fixtures;
- uncertainty fixtures;
- conflict/supersession fixtures;
- derivation-disclosure fixtures;
- disclaimer-preservation fixtures;
- compatibility fixtures;
- stale and superseded schema fixtures;
- validator non-authority fixtures;
- Contract Conformance Record fixtures.

No future implementation phase should claim executable schema completion
without satisfying the frozen test expectations appropriate to its scope.

## Artifact Generation Contract

Future artifact generators that emit schema-valid Repository
Intelligence artifacts must:

- declare the artifact contract version;
- declare the schema concept version;
- declare the executable schema version;
- declare repository snapshot or revision identity;
- preserve the common envelope;
- preserve required, conditional, optional, and forbidden field rules;
- preserve source attribution;
- preserve evidence links or explicit gap markers;
- preserve uncertainty and verification disclosure;
- preserve conflict and supersession visibility;
- preserve derivation disclosure where required;
- preserve boundary disclaimers;
- preserve limitations;
- avoid authority-expanding claims.

Future generators must not:

- convert schema validity into approval;
- hide unknowns or uncertainty;
- collapse conflicting or stale state into clean state;
- present candidate Evidence as accepted Evidence;
- emit artifacts that imply Advisory or schema validation can bypass
  Decision Evaluation.

## Repository Skills Integration Contract

Future Repository Skills may expose schema validation or artifact
inspection only as read-only inspection capability.

They may:

- inspect schema-validity status;
- summarize conformance findings;
- surface source, evidence, uncertainty, conflict, or disclaimer gaps;
- package source-attributed context for other non-authoritative
  consumers.

They may not:

- treat schema validity as permission;
- authorize lifecycle transitions;
- authorize execution;
- replace Decision Evaluation;
- replace Evidence;
- replace Repository State;
- mutate repository or lifecycle state.

## Advisory Consumer Integration Contract

Future Advisory consumers may use schema-valid Repository Intelligence
artifacts as bounded, source-attributed context.

They must not treat schema validity as:

- approval;
- authorization;
- execution permission;
- Decision Evaluation equivalence;
- evidence acceptance;
- permission to bypass uncertainty, conflict, limitations, or evidence
  gaps.

Advisory output remains non-authoritative even when its inputs are
schema-valid.

## Decision Evaluation Boundary Contract

Schema validity is not decision validity.

A schema-valid artifact is not an approved action.

A schema-valid artifact is not authorization.

A schema-valid artifact is not execution permission.

Decision Evaluation remains the only PCAE component responsible for
actual governance decisions over repository actions.

## Read-Only and No-Execution Boundary Contract

Future executable schemas and validators remain read-only and
non-executing.

They may inspect artifacts and report findings. They may not:

- run commands;
- mediate shells;
- invoke runtimes;
- apply patches;
- trigger tests;
- mutate repository files as a validation side effect;
- mutate lifecycle state;
- claim execution safety;
- enable execution capability.

Execution capability remains unavailable. Maximum runtime capability
remains `observe`.

## Non-Conformance Examples

The following future behaviors would violate this contract:

1. A schema allows `execution_approved: true`.
2. A validator reports `safe_to_push`.
3. A validator mutates repository state after validation.
4. A schema omits source-attribution requirements for claim-bearing
   artifacts.
5. A schema collapses `unknown` and `verified` into one success state.
6. A schema removes supersession history when a newer artifact exists.
7. A schema-valid artifact claims Decision Evaluation can be bypassed.
8. A Repository Skill treats schema validity as permission to execute.
9. An Advisory consumer treats schema validity as approval.
10. A validator treats accepted Evidence state as satisfiable without an
    Evidence subsystem reference.

## Contract-Preserving Examples

The following future behaviors would preserve this contract:

1. A schema requires the common envelope, source attribution, evidence
   links, uncertainty states, and boundary disclaimers for a Repository
   Knowledge Snapshot.
2. A validator reports missing `verification_method` for a
   `partially_verified` state but does not recommend action approval.
3. A Query Result artifact is schema-valid yet still carries
   non-decision and no-execution disclaimers.
4. A Repository Skill exposes a read-only conformance summary plus cited
   source/evidence gaps.
5. An Advisory consumer uses schema-valid artifacts as bounded context
   while preserving uncertainty and non-authority wording.
6. A stale schema is still inspectable and explicitly superseded by a
   newer version rather than silently replaced.

## Future Executable Schema Conformance Checklist

Future executable schema implementation phases should satisfy the
following checklist:

- [ ] Every schema family maps to one frozen 119E artifact family.
- [ ] The common envelope is represented as a reusable shared component.
- [ ] Required, conditional, optional, and forbidden fields preserve the
  contract meaning.
- [ ] Source attribution vocabulary is enforced structurally where
  applicable.
- [ ] Evidence-link vocabulary is enforced structurally where applicable.
- [ ] Uncertainty and verification states preserve the frozen vocabularies.
- [ ] Conflict and supersession history remain visible and non-destructive.
- [ ] Derivation disclosures are required for derived artifacts.
- [ ] Boundary disclaimers are required where the contract requires them.
- [ ] Forbidden-claim checks remain conservative and non-authoritative.
- [ ] Schema validity is never described as approval or authorization.
- [ ] Validator output cannot issue governance verdicts.
- [ ] Compatibility policy, stale-schema handling, and superseded-schema
  handling are explicit.
- [ ] Repository Skills exposure remains read-only and non-authoritative.
- [ ] Advisory consumption remains non-authoritative and bounded.
- [ ] Tests cover valid, invalid, boundary, vocabulary, compatibility,
  and non-authority cases.

## Risks

- Schema-validity language may still be interpreted by humans as
  approval.
- Validator scope may creep into Decision Evaluation territory.
- Forbidden-claim detection may remain incomplete for implication-heavy
  prose.
- Future executable schemas may drift from 119E artifact semantics.
- Version changes may silently alter conceptual meaning if compatibility
  discipline is weak.
- Source attribution may become formally present but substantively weak.
- Evidence-link structure may be mistaken for accepted Evidence.
- Repository Skills or Advisory surfaces may overstate the meaning of
  schema success.

## Open Questions

- Should 119I verify this executable schema contract before any schema
  implementation phase begins?
- Should future validator findings use a single severity vocabulary or
  separate structural and semantic severity vocabularies?
- Should Contract Conformance Records be emitted directly by validators
  or only generated by a separate review layer?
- How should future schema-valid artifacts represent partial structural
  validity without creating a human-factors “approved enough” shortcut?
- Which 119F clarification items should be resolved in the next contract
  verification phase versus deferred to a later contract revision?

## Recommended Next Phase

Recommended next phase: 119I - Repository Intelligence Executable Schema
Contract Verification.

Reason: before implementing executable schemas, PCAE should verify that
this executable schema contract is internally consistent, testable, and
safe against validator authority creep.

## Non-Goals

This phase did not implement:

- executable schema;
- JSON Schema;
- Pydantic model;
- dataclass;
- validator;
- artifact contract verifier;
- schema verification CLI;
- automated tests;
- schema directories;
- repository intelligence extraction;
- repository knowledge extraction;
- historical memory extraction;
- change impact analysis engine;
- dependency graph construction;
- graph query engine;
- advisory behavior changes;
- advisory runtime changes;
- advisory context package changes;
- evidence subsystem changes;
- repository skills changes;
- decision evaluation changes;
- runtime behavior changes;
- source code changes;
- test code changes;
- execution;
- shell mediation;
- Permission Broker changes;
- lifecycle redesign;
- REST;
- Dashboard;
- Web UI;
- Telegram inbound;
- provider selection;
- multi-model orchestration;
- autonomous coding;
- model capability expansion;
- repository mutation;
- runtime plugin changes;
- repository state changes;
- test execution through repository intelligence;
- automatic patch generation;
- automatic refactoring.
