# Phase 119E - Repository Intelligence Artifact Contract Freeze

## Purpose

Phase 119E freezes the Repository Intelligence artifact contract: the
canonical rules that all future Repository Intelligence artifacts must obey.
It defines what artifacts must contain, preserve, disclose, and never imply.

This phase is artifact-contract-freeze only. It does not create executable
schemas, JSON Schema, Pydantic models, dataclasses, validators, contract
verifiers, CLIs, automated tests, Repository Intelligence extraction,
Repository Knowledge extraction, Historical Memory extraction, Change
Impact Analysis engines, Dependency Knowledge Graph construction, graph
query engines, Advisory behavior changes, Advisory Runtime changes,
Advisory Context Package changes, Evidence subsystem changes, Repository
Skills changes, Decision Evaluation changes, source code, tests, runtime
behavior, execution, authorization, enforcement, lifecycle behavior,
Permission Broker behavior, Repository State behavior, Repository
Transition Validator behavior, Notification Policy behavior, REST,
Dashboard, Web UI, provider orchestration, autonomous coding, model
capability expansion, automatic patch generation, automatic refactoring,
repository mutation, or Telegram inbound capability.

## Contract Freeze Context

Track B asks whether PCAE can understand the repository itself without
granting new authority. The PCAE sequence for Track B is:

architecture → review → contract freeze → verification → conceptual
schema architecture → conceptual schema review → artifact contract freeze
→ artifact contract verification → prototype planning

Phases completed before this one:

| Phase | Name | Role |
| --- | --- | --- |
| 118A–118E | Repository Intelligence Architecture | Defined the initial architecture stack |
| 118R | Architecture Review | Reviewed the stack; found it coherent |
| 119A | Contract Freeze | Froze the Repository Intelligence contract |
| 119B | Contract Verification | Verified the contract as internally consistent, testable, future-enforceable |
| 119C | Conceptual Schema Architecture | Defined twelve conceptual schema families |
| 119D | Conceptual Schema Review | Reviewed schema families; found them coherent and ready for artifact contract freeze with minor clarifications |

Phase 119E now freezes the artifact contracts. After this freeze, artifact
contract verification (119F) can confirm the artifact contracts are
internally consistent and ready to constrain prototype planning and
executable schema work.

## Contract Basis

This artifact contract freeze is based on:

- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_CONCEPTUAL_SCHEMA_REVIEW.md` —
  concludes the conceptual schema family set is coherent and ready for
  artifact contract freeze with minor clarifications.
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_CONCEPTUAL_SCHEMA_ARCHITECTURE.md` —
  defines the twelve conceptual schema families, common artifact envelope,
  relationships, invariants, derivation model, versioning model, and
  boundary representations.
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_CONTRACT_VERIFICATION.md` —
  verifies the 119A contract as internally consistent, testable, and
  future-enforceable.
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_CONTRACT_FREEZE.md` —
  freezes the Repository Intelligence architectural contract and invariants.
- `docs/PHASE_118_REPOSITORY_INTELLIGENCE_ARCHITECTURE_REVIEW.md` —
  concludes the 118A–118E architecture set is coherent and ready for
  contract freeze.
- `docs/PHASE_118_REPOSITORY_KNOWLEDGE_ARCHITECTURE.md` —
  defines Repository Knowledge as foundational architectural understanding.
- `docs/PHASE_118_HISTORICAL_MEMORY_ARCHITECTURE.md` —
  defines Historical Memory as the temporal layer inside Repository Knowledge.
- `docs/PHASE_118_CHANGE_IMPACT_ANALYSIS_ARCHITECTURE.md` —
  defines Change Impact Analysis as read-only change-scoped reasoning.
- `docs/PHASE_118_DEPENDENCY_KNOWLEDGE_GRAPH_ARCHITECTURE.md` —
  defines the Dependency Knowledge Graph as the relationship layer.
- `docs/PHASE_118_ADVISORY_REASONING_EXPANSION_ARCHITECTURE.md` —
  defines how Advisory may consume Repository Intelligence context.

Supporting boundaries include Repository State, Evidence, Decision
Evaluation, Repository Skills, Advisory Repository Skills, Advisory
Context Packages, Advisory Runtime, Runtime Context, Runtime Inspect,
canonical lifecycle artifacts, phase reports, release governance,
transition validation, and v0.2 no-go boundaries.

## Contract Status

This document is the **initial Repository Intelligence artifact contract
freeze**. It freezes the conceptual artifact contracts that all future
Repository Intelligence artifacts must obey.

The contract is implementation-independent. Any future JSON Schema,
Pydantic model, dataclass, validator, extractor, CLI, report format,
skill surface, or serialization must conform to this contract unless a
later governed contract revision explicitly changes it.

## Artifact Contract Definition

A Repository Intelligence artifact contract is a frozen set of rules that
governs what a specific family of Repository Intelligence artifacts must
contain, may contain, must disclose, must preserve, and must never imply.

An artifact contract:

- **freezes** required conceptual fields and their meanings;
- **freezes** optional conceptual fields and their meanings;
- **freezes** conditional fields and their triggering conditions;
- **freezes** boundary disclaimers that must appear verbatim or in
  substantively equivalent form;
- **freezes** invariants that every artifact in the family must preserve;
- **forbids** specific claims and implications;
- **defines** what makes an artifact conforming, conforming with
  observations, partially conforming, non-conforming, or unable to be
  assessed;
- **constrains** future executable schema, prototype, query, report,
  skill-surface, and Advisory consumer work.

An artifact contract does not:

- prescribe implementation language, library, or format;
- prescribe serialization format;
- prescribe storage layout;
- prescribe extraction algorithm;
- validate artifacts automatically (that is a future verifier concern);
- execute, mutate, authorize, or enforce.

## Artifact Family Inventory

### Frozen Artifact Families

This contract freezes twelve artifact families. Every future Repository
Intelligence artifact must belong to exactly one of these families (or one
future family added by a governed contract revision):

1. **Repository Intelligence Package** — top-level bundle/index for a set
   of related Repository Intelligence artifacts.
2. **Repository Knowledge Snapshot** — foundational semantic snapshot of
   repository architecture and entities.
3. **Historical Memory Snapshot** — temporal layer describing how repository
   architecture and lifecycle evolved.
4. **Dependency Knowledge Graph Snapshot** — graph view of repository
   relationships inside Repository Knowledge.
5. **Change Impact Report** — read-only impact context for a proposed or
   observed change.
6. **Advisory Intelligence Context Package** — bounded, provenance-preserving
   context package for non-authoritative Advisory use.
7. **Source Attribution Record** — links a claim to its supporting
   repository or lifecycle source. Cross-cutting.
8. **Evidence Link Record** — bridges Repository Intelligence claims to
   Evidence artifacts or evidence candidates. Cross-cutting.
9. **Uncertainty / Verification State** — describes what is known, unknown,
   verified, inferred, stale, or decision-required. Cross-cutting.
10. **Conflict / Supersession Record** — preserves disagreement, staleness,
    and replacement history. Cross-cutting.
11. **Query Result** — read-only answer to a Repository Intelligence question.
12. **Contract Conformance Record** — descriptive inspection of whether an
    artifact conforms to the Repository Intelligence contract.

### Artifact Families Deferred to Future Work

The following are intentionally not frozen by this contract. Future phases
may freeze them as additional families or as profiles of existing families:

- **Release Intelligence Snapshot** — release-scoped repository intelligence.
  Deferred because Track B has not yet defined release-intelligence scope.
- **Contract Map Snapshot** — cross-artifact contract relationship map.
  Deferred because it requires at least two frozen artifact contracts to
  map between, and the first executable schema work should inform its shape.
- **Cross-Repository Intelligence Package** — intelligence spanning multiple
  repositories. Deferred because Track B is scoped to single-repository
  understanding.
- **Artifact Provenance Chain Record** — full derivation chain across
  multiple artifacts. Deferred because the derivation disclosure contract
  (see Mandatory Derivation Disclosure Contract) provides sufficient
  per-artifact provenance for the initial freeze; full-chain records can
  be added later.

Future phases may also define specialized profiles of existing families
(e.g., `release_knowledge_snapshot` as a profile of `repository_knowledge_snapshot`).
Such profiles must preserve all invariants of the parent family.

## Common Artifact Envelope Contract

Every Repository Intelligence artifact must carry a common envelope. The
envelope identifies, versions, attributes, and bounds the artifact.

### Required Envelope Fields

These fields must appear in every artifact:

| Field | Type | Meaning |
| --- | --- | --- |
| `artifact_id` | string | Stable, unique identifier for the artifact instance within its family and repository context. |
| `artifact_type` | string | Family name from the frozen set: `repository_intelligence_package`, `repository_knowledge_snapshot`, `historical_memory_snapshot`, `dependency_knowledge_graph_snapshot`, `change_impact_report`, `advisory_intelligence_context_package`, `source_attribution_record`, `evidence_link_record`, `uncertainty_verification_state`, `conflict_supersession_record`, `query_result`, `contract_conformance_record`. |
| `artifact_family` | string | Same as `artifact_type` for the twelve frozen families; may differ for future specialized profiles (e.g., `repository_knowledge_snapshot` family with profile `release_knowledge_snapshot`). |
| `artifact_contract_version` | string | Contract version the artifact was built against. Frozen initial value: `119E.1.0`. |
| `schema_concept_version` | string | Conceptual schema version. Frozen initial value: `119C.1.0-concept`. Distinct from `artifact_contract_version`: the conceptual schema describes the artifact shape; the contract version describes the frozen rules. |
| `repository_identity` | object | Repository identity. Must include `identity_type` (one of: `canonical_remote_url`, `local_path_fingerprint`, `repository_name`, `composite`) and `identity_value`. When `identity_type` is `composite`, must include both `canonical_remote_url` and `local_path_fingerprint`. |
| `repository_commit` | string or null | Git commit SHA the artifact describes. Value `null` when the artifact does not describe a specific commit (e.g., a package-as-plan). |
| `generated_at_utc` | string | ISO 8601 UTC timestamp of artifact creation. |
| `producer` | object | Producer identity. Must include `producer_type` (one of: `human`, `phase`, `tool`, `skill`, `extractor`, `unknown`) and `producer_identity` (human-readable identifier). |
| `source_attribution` | array | At least one Source Attribution Record (embedded or referenced) describing the artifact's own evidential basis. |
| `evidence_links` | array | At least one Evidence Link Record (embedded or referenced) bridging to Evidence. |
| `verification_state` | string | One of the frozen uncertainty/verification state values (see Uncertainty / Verification State Contract). |
| `uncertainty_state` | string | One of the frozen uncertainty/verification state values. |
| `conflict_state` | string or `none` | Conflict presence summary. Value `none` when no conflicts exist. |
| `supersession_state` | string or `current` | Supersession status. Value `current` when not superseded. |
| `read_only_boundary` | string | Frozen value: `This artifact is descriptive and read-only. It does not mutate repository state, lifecycle state, or any other PCAE subsystem state.` |
| `decision_boundary` | string | Frozen value: `This artifact is not a decision. Decision Evaluation is the sole decision maker in PCAE. This artifact provides context only.` |
| `execution_boundary` | string | Frozen value: `This artifact does not execute commands, invoke runtimes, mediate shells, route execution, or authorize execution. Execution remains unavailable.` |
| `limitations` | array of strings | Known limitations of the artifact. Must not be empty; use `["no known limitations"]` only when none are identified. |

### Conditional Envelope Fields

These fields must appear when the stated condition is met:

| Field | Condition | Type | Meaning |
| --- | --- | --- | --- |
| `repository_branch` | Required when branch context is known and relevant | string or null | Branch or ref name. |
| `release_context` | Required when the artifact relates to a specific release | string or null | Release tag or identifier. |
| `phase_context` | Required when the artifact relates to a PCAE phase | object | Phase identity with `phase_id` and optional `task_id`, `phase_report_id`. |

### Optional Envelope Fields

These fields may appear but are not required:

| Field | Type | Meaning |
| --- | --- | --- |
| `derivation_method` | string | Human-readable derivation method or rule family. |
| `derivation_inputs` | array of artifact references | Artifacts this artifact was derived from. |
| `derivation_rule_family` | string | Named rule family used in derivation. |
| `derivation_tool` | object | Tool or producer identity for the derivation step. |
| `derivation_limitations` | array of strings | Known limitations of the derivation method. |
| `derivation_nondeterminism_exclusions` | array of strings | Aspects explicitly excluded from deterministic claims. |
| `related_artifacts` | array of artifact references | Related artifacts not captured by `derivation_inputs`. |

### Cross-Cutting Record Convention

Cross-cutting records (Source Attribution Record, Evidence Link Record,
Uncertainty / Verification State, Conflict / Supersession Record) use a
dual convention:

- **Embedded**: the record is included inline inside the artifact. This is
  the default for artifact-scoped records (records that describe this
  artifact's own state).
- **Referenced**: the record is identified by an artifact reference. This
  is used when the record is shared across artifacts, independently
  versioned, or produced by a different producer.

The envelope carries embedded summaries. Detailed records may be embedded
or referenced. The convention per family is stated in each family's
contract below.

### Forbidden Envelope Claims

The common envelope must not include any field that:

- asserts authorization (`authorized_by`, `approved_by`, `permission_granted`);
- implies execution permission (`execution_allowed`, `may_execute`);
- implies mutation permission (`mutation_allowed`, `may_mutate`);
- implies lifecycle authority (`lifecycle_transition_valid`, `phase_approved`);
- replaces Decision Evaluation (`decision`, `verdict`, `ruling`);
- replaces Evidence (`evidence_accepted`, `evidence_verified`);
- replaces Repository State (`repository_state`, `state_snapshot`);
- implies Advisory authority (`advisory_approval`, `advisory_decision`).

## Repository Intelligence Package Contract

**Role**: Top-level bundle and index. Groups related Repository Intelligence
artifacts for one repository snapshot or analysis context.

**Boundary**: Container only. Does not merge component authority, decide,
execute, mutate, or replace underlying artifacts.

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `package_subject` | string | What this package describes. |
| `package_scope` | string | Scope boundary for included artifacts. |
| `package_source_set` | array of embedded Source Attribution Records | Sources supporting package assembly decisions. |
| `package_verification_state` | string | One of the frozen uncertainty/verification state values. |
| `package_limitations` | array of strings | Known limitations of the package as a whole. |

### Conditional Fields

| Field | Condition | Type | Meaning |
| --- | --- | --- | --- |
| `repository_knowledge_snapshot` | Required when a Repository Knowledge Snapshot exists for this context | artifact reference | Reference to the knowledge snapshot. |
| `historical_memory_snapshot` | Required when a Historical Memory Snapshot exists for this context | artifact reference | Reference to the historical memory snapshot. |
| `dependency_knowledge_graph_snapshot` | Required when a Dependency Knowledge Graph Snapshot exists for this context | artifact reference | Reference to the graph snapshot. |

### Optional Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `change_impact_reports` | array of artifact references | Included change impact reports. |
| `advisory_intelligence_context_packages` | array of artifact references | Included advisory context packages. |
| `query_results` | array of artifact references | Included query results. |
| `contract_conformance_records` | array of artifact references | Included conformance records. |
| `package_metadata` | object | Additional package-level metadata. |

### Materialization Order

The package must be materialized after component artifacts exist
(package-as-aggregation) in early prototypes. The package-as-plan form
(package materialized before components) is permitted only when every
component reference carries `ref_materialization_state` with value
`pending` or `not_yet_materialized`.

### Cross-Cutting Convention

- Source Attribution Records: embedded in `package_source_set` for
  package-assembly sources; referenced for per-component sources.
- Evidence Link Records: embedded summary in envelope; detailed records
  referenced.
- Uncertainty / Verification State: embedded summary in envelope.
- Conflict / Supersession Record: embedded summary in envelope; detailed
  records referenced.

### Frozen Boundary Disclaimer

> This Repository Intelligence Package is a container and index. It does
> not merge the authority of its component artifacts, decide, execute,
> mutate repository state, replace Evidence, replace Decision Evaluation,
> or expand Advisory authority beyond what each component artifact
> individually permits.

## Repository Knowledge Snapshot Contract

**Role**: Foundational architectural understanding of what the repository
contains and how entities relate at a given repository snapshot.

**Boundary**: Descriptive only. Not Repository State. Does not decide
whether the repository is valid, correct, or complete.

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `architectural_entities` | array of objects | Repository entities. Each entity has at minimum `entity_id`, `entity_type`, `entity_name`, and `entity_path`. |
| `capabilities` | array of objects | Discovered or documented capabilities. Each has at minimum `capability_id`, `capability_name`, and `capability_source`. |
| `subsystems` | array of objects | Architectural subsystems. Each has at minimum `subsystem_id`, `subsystem_name`, and `subsystem_boundary`. |
| `knowledge_relationships` | array of objects | Relationships between entities. Each has at minimum `relationship_id`, `from_entity_id`, `to_entity_id`, `relationship_type`, and `source_attribution`. |
| `knowledge_claims` | array of objects | Assertions about the repository. Each has at minimum `claim_id`, `claim_text`, `claim_subject`, and `source_attribution`. |
| `knowledge_sources` | array of embedded Source Attribution Records | Sources supporting the snapshot's claims. |
| `evidence_links` | array of embedded Evidence Link Records | Bridges from knowledge claims to Evidence. |
| `unknowns` | array of strings | Explicitly declared unknowns and gaps. Must not be empty. |
| `snapshot_limitations` | array of strings | Known limitations of this snapshot. |

### Optional Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `commands_and_cli_surfaces` | array of objects | CLI and command surfaces. |
| `contracts` | array of objects | Known contracts and their locations. |
| `documentation_references` | array of source locators | Known documentation locations. |
| `test_references` | array of source locators | Known test locations. |
| `ownership_markers` | array of objects | Ownership and maintainer information when discoverable. |

### Cross-Cutting Convention

- Source Attribution Records: embedded for snapshot-level claims;
  referenced when shared with other artifacts.
- Evidence Link Records: embedded.
- Uncertainty / Verification State: embedded summary in envelope; detailed
  records referenced.
- Conflict / Supersession Record: embedded summary; detailed records
  referenced.

### Frozen Boundary Disclaimer

> This Repository Knowledge Snapshot describes repository architecture
> and entity relationships. It is not Repository State and does not
> decide whether the repository is valid, correct, or complete.

## Historical Memory Snapshot Contract

**Role**: Temporal layer describing how repository architecture, contracts,
capabilities, decisions, repairs, hardening, and releases evolved over time.

**Boundary**: Temporal Repository Knowledge. Not model memory, conversation
memory, or rewritten history. Historical records are preserved even when
superseded.

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `historical_subjects` | array of objects | Subjects tracked through history. Each has at minimum `subject_id`, `subject_type`, and `subject_name`. |
| `phase_events` | array of objects | PCAE phase lifecycle events. Each has at minimum `event_id`, `phase_id`, `event_type`, `event_timestamp_utc`, and `source_attribution`. |
| `lineage_records` | array of objects | Sequential lineage. Each has at minimum `lineage_id`, `subject_id`, `previous_state`, `new_state`, `event_id`, and `timestamp_utc`. |
| `supersession_records` | array of embedded Conflict / Supersession Records | Supersession and replacement history. |
| `historical_claims` | array of objects | Claims about historical events. Each has `claim_id`, `claim_text`, and `source_attribution`. |
| `historical_sources` | array of embedded Source Attribution Records | Sources supporting historical claims. |
| `evidence_links` | array of embedded Evidence Link Records | Bridges to Evidence. |
| `stale_or_conflicting_history` | array of objects | Known stale, conflicting, or uncertain historical records. |
| `limitations` | array of strings | Known limitations. |

### Optional Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `release_events` | array of objects | Release events. |
| `decision_events` | array of objects | Governed decision events. |
| `repair_events` | array of objects | Repair and hardening events. |
| `hardening_events` | array of objects | Hardening-specific events. |
| `contract_freeze_events` | array of objects | Contract freeze and revision events. |
| `lifecycle_report_events` | array of objects | Phase report and lifecycle report events. |
| `correction_records` | array of objects | Historical corrections with preserved original and corrected values. |

### Cross-Cutting Convention

- Source Attribution Records: embedded for historical claims; referenced
  when shared.
- Evidence Link Records: embedded.
- Uncertainty / Verification State: embedded summary in envelope; detailed
  records referenced.
- Conflict / Supersession Record: embedded for supersession history;
  detailed records referenced for cross-artifact conflicts.

### Frozen Boundary Disclaimer

> This Historical Memory Snapshot describes temporal evolution of
> repository architecture and lifecycle. It is not model memory,
> conversation memory, or rewritten history. Historical records are
> preserved even when superseded.

## Dependency Knowledge Graph Snapshot Contract

**Role**: Graph view of repository relationships inside Repository
Knowledge. Entities as nodes, repository-derived relationships as typed
directional edges.

**Boundary**: Graph view inside Repository Knowledge. Not a graph database,
runtime orchestrator, command router, execution planner, or Decision
Evaluation component.

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `graph_subject` | string | What the graph describes. |
| `graph_scope` | string | Scope boundary for included nodes and edges. |
| `nodes` | array of objects | Graph nodes. Each has at minimum `node_id`, `node_type`, `node_label`, and `source_attribution`. |
| `edges` | array of objects | Graph edges. Each has at minimum `edge_id`, `from_node_id`, `to_node_id`, `edge_type`, `direction`, and `source_attribution`. |
| `dependency_claims` | array of objects | Claims about dependencies. Each has `claim_id`, `claim_text`, `from_entity`, `to_entity`, `dependency_type`, and `source_attribution`. |
| `dependency_types` | array of strings | Edge type vocabulary. Frozen initial vocabulary: `imports`, `calls`, `references`, `configures`, `extends`, `implements`, `depends_on_contract`, `documents`, `tests`, `owns`, `releases_with`, `governed_by`. |
| `source_attributions` | array of embedded Source Attribution Records | Sources supporting graph construction. |
| `evidence_links` | array of embedded Evidence Link Records | Bridges to Evidence. |
| `graph_limitations` | array of strings | Known limitations. |

### Optional Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `dependency_strengths` | array of objects | Strength classification per edge or edge type. |
| `dependency_scopes` | array of objects | Scope classification per edge or edge type. |
| `dependency_paths` | array of objects | Named or significant dependency paths. |
| `graph_views` | array of objects | Named filtered views over the graph. |
| `graph_snapshot_metadata` | object | Graph construction metadata. |

### Cross-Cutting Convention

- Source Attribution Records: embedded for graph construction sources;
  referenced for shared entity sources.
- Evidence Link Records: embedded.
- Uncertainty / Verification State: embedded summary in envelope; detailed
  records referenced.
- Conflict / Supersession Record: embedded summary; detailed records
  referenced.

### Frozen Boundary Disclaimer

> This Dependency Knowledge Graph Snapshot is a graph view inside
> Repository Knowledge. It is not a graph database, runtime orchestrator,
> command router, execution planner, or Decision Evaluation component.

## Change Impact Report Contract

**Role**: Describes what may be affected by a proposed or observed
repository change.

**Boundary**: Impact context only. Does not predict by hidden model
inference, authorize change, decide safety, run tests, generate patches,
or execute.

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `change_subject` | object | The proposed or observed change. Must include `change_description`, `change_type`, and `change_scope`. |
| `impact_scope` | string | Scope boundary for impact assessment. |
| `impact_subjects` | array of objects | What may be affected. Each has at minimum `subject_id`, `subject_type`, `subject_name`, and `impact_category` (one of: `direct`, `indirect`, `potential`, `unknown`). |
| `impacted_entities` | array of artifact references | Entities affected, referencing Repository Knowledge Snapshot entities. |
| `impact_surfaces` | array of strings | Named architectural surfaces affected. |
| `impact_relationships` | array of objects | How impacts relate. Each has `from_impact`, `to_impact`, and `relationship_type`. |
| `blast_radius` | object | Blast radius estimate with `direct_scope`, `indirect_scope`, and `uncertainty_note`. |
| `direct_impacts` | array of objects | Directly affected entities and surfaces. |
| `indirect_impacts` | array of objects | Indirectly or potentially affected entities and surfaces. |
| `unknown_impacts` | array of strings | Explicitly declared unknown impact areas. Must not be empty. |
| `required_evidence` | array of objects | Evidence needed to reduce impact uncertainty. |
| `source_attributions` | array of embedded Source Attribution Records | Sources supporting impact claims. |
| `evidence_links` | array of embedded Evidence Link Records | Bridges to Evidence. |

### Optional Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `impact_paths` | array of objects | Impact propagation paths through the dependency graph. |
| `historical_impacts` | array of objects | Similar historical changes and their observed impacts. |
| `contract_impacts` | array of objects | Contract or invariant implications. |
| `test_impacts` | array of objects | Test surfaces that may need attention. |
| `documentation_impacts` | array of objects | Documentation that may need updating. |
| `advisory_impacts` | array of objects | Advisory context implications. |
| `governance_impacts` | array of objects | Governance or lifecycle implications. |

### Frozen Non-Decision Disclaimer

> This Change Impact Report provides impact context only. It does not
> predict by hidden model inference, authorize change, decide whether a
> change is safe, approve or reject a change, run tests, generate
> patches, refactor automatically, or execute. Decision Evaluation
> remains the sole decision maker in PCAE. This report is read-only and
> descriptive.

### Frozen No-Execution Disclaimer

> This Change Impact Report does not execute commands, run tests, invoke
> runtimes, apply changes, or mediate shells. Execution remains
> unavailable.

### Cross-Cutting Convention

- Source Attribution Records: embedded.
- Evidence Link Records: embedded.
- Uncertainty / Verification State: embedded summary in envelope; detailed
  records referenced.
- Conflict / Supersession Record: embedded summary; detailed records
  referenced.

## Advisory Intelligence Context Package Contract

**Role**: Bounded, provenance-preserving package of Repository Intelligence
context for non-authoritative Advisory use.

**Boundary**: Advisory context only. Advisory may become more informed
through this package. Advisory must not become more authoritative.

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `advisory_subject` | string | What Advisory is being asked about. |
| `context_scope` | string | Scope boundary for included context. |
| `context_budget` | object | Budget constraints: `max_artifacts`, `max_source_records`, `max_evidence_links`, `context_size_estimate`. |
| `context_inputs` | array of objects | Context inputs considered and selected. |
| `uncertainty_statements` | array of objects | Explicit uncertainty statements. |
| `evidence_gaps` | array of strings | Declared gaps in available evidence. |
| `handoff_to_decision_evaluation` | object | Handoff note with `handoff_context` and `non_decision_marker: true`. |
| `trust_class` | string | Trust classification. Frozen values: `source_attributed`, `partially_attributed`, `advisory_inferred`, `unverified`. |
| `provenance_notes` | array of strings | Provenance and chain-of-context notes. |
| `limitations` | array of strings | Known limitations. |

### Conditional Fields

| Field | Condition | Type | Meaning |
| --- | --- | --- | --- |
| `repository_knowledge_references` | Required when Repository Knowledge context is included | array of artifact references | Knowledge snapshot references. |
| `historical_memory_references` | Required when Historical Memory context is included | array of artifact references | Historical memory references. |
| `dependency_knowledge_graph_references` | Required when graph context is included | array of artifact references | Graph snapshot references. |
| `change_impact_report_references` | Required when impact context is included | array of artifact references | Impact report references. |

### Optional Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `evidence_links` | array of embedded Evidence Link Records | Bridges to Evidence. |
| `advisory_claims` | array of objects | Claims Advisory may make. |
| `advisory_explanations` | array of objects | Explanations Advisory may offer. |
| `advisory_recommendations` | array of objects | Recommendations Advisory may suggest. Each must carry `non_authority_marker: true`. |

### Frozen Non-Authority Disclaimer

> This Advisory Intelligence Context Package provides bounded context for
> Advisory use. Advisory may become more informed through this package.
> Advisory must not become more authoritative. Advisory recommendations
> are non-binding. Decision Evaluation is the sole decision maker in
> PCAE. This package does not authorize, decide, execute, or enforce.

### Cross-Cutting Convention

- Source Attribution Records: referenced (context sources are tracked in
  referenced artifacts).
- Evidence Link Records: embedded.
- Uncertainty / Verification State: embedded summary in envelope; detailed
  records referenced.
- Conflict / Supersession Record: referenced.

## Source Attribution Record Contract

**Role**: Links a Repository Intelligence assertion to its supporting
repository or lifecycle source. Cross-cutting — used by all other artifact
families.

**Boundary**: Source identification and support classification only. Does
not verify correctness of the source.

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `source_id` | string | Unique identifier for this source record. |
| `source_type` | string | Type of source. Frozen values: `file`, `commit`, `phase_report`, `task_contract`, `decision_record`, `evidence_record`, `release_tag`, `architecture_document`, `contract_document`, `test_file`, `configuration_file`, `dependency_manifest`, `lifecycle_artifact`. |
| `source_locator` | object | Locator using frozen source locator vocabulary (see Source Locator Vocabulary). Must include `locator_type` and `locator_value`. |
| `source_claim_relationship` | string | How the source relates to the claim. Frozen values: `supports`, `contradicts`, `supersedes`, `documents`, `constrains`, `verifies`, `references`, `introduces`, `modifies`, `hardens`. |
| `source_support_level` | string | Strength of support. Frozen values: `direct`, `indirect`, `implied`, `weak`, `contextual`, `historical`. |
| `source_verification_state` | string | One of the frozen uncertainty/verification state values. |
| `source_staleness_state` | string | Staleness. Frozen values: `current`, `stale_since_commit`, `stale_since_phase`, `superseded`, `unknown`. |
| `source_limitations` | array of strings | Known limitations of this source. |

### Conditional Fields

| Field | Condition | Type | Meaning |
| --- | --- | --- | --- |
| `source_path` | Required when `source_type` is file-based | string | Path relative to repository root. |
| `source_digest_or_commit_reference` | Required when the source has a content digest or commit reference | string | Content hash or commit SHA. |

### Cross-Cutting Convention

Source Attribution Records are leaf records. They do not embed other
cross-cutting records beyond the common envelope summary. When a source
attribution itself needs evidential support, that is recorded via an
Evidence Link Record in the parent artifact.

### Frozen Boundary Disclaimer

> This Source Attribution Record identifies and classifies a supporting
> source. It does not verify the correctness, completeness, or authority
> of the source. Source verification state is recorded separately.

## Evidence Link Record Contract

**Role**: Bridges Repository Intelligence claims to Evidence artifacts or
evidence candidates. Cross-cutting — used by all other artifact families.

**Boundary**: Bridge/candidate record only. Not itself accepted Evidence
unless a future governed Evidence path admits it.

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `evidence_id` | string | Unique identifier for this evidence link. |
| `evidence_type` | string | Type of evidence link. Frozen values: `evidence_candidate`, `evidence_reference`, `evidence_derived`, `evidence_gap_marker`. |
| `evidence_source` | object | Where the evidence comes from. Must include `source_type` and `source_identity`. |
| `supported_claim` | object | The claim this evidence supports or contradicts. Must include `claim_id` and `claim_summary`. |
| `support_strength` | string | Strength of evidential support. Frozen values: `strong`, `moderate`, `weak`, `contradicts`, `inconclusive`. |
| `candidate_or_accepted_state` | string | Frozen values: `candidate`, `accepted_by_evidence_subsystem`, `rejected_by_evidence_subsystem`, `unsubmitted`. |
| `decision_evaluation_eligibility` | string | Frozen values: `eligible`, `not_eligible_evidence_gap`, `not_eligible_candidate_only`, `not_eligible_insufficient_strength`. |
| `limitations` | array of strings | Known limitations. |

### Optional Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `verification_state` | string | One of the frozen uncertainty/verification state values. |
| `related_artifacts` | array of artifact references | Related Repository Intelligence artifacts. |

### Cross-Cutting Convention

Evidence Link Records are leaf records. They do not embed other
cross-cutting records beyond the common envelope summary. An Evidence Link
Record may reference a Source Attribution Record via `related_artifacts`
when the evidence derives from a specific source.

### Frozen Boundary Disclaimer

> This Evidence Link Record bridges Repository Intelligence claims to
> Evidence. It is not itself accepted Evidence unless a future governed
> Evidence path admits it. The `candidate_or_accepted_state` field
> records the current Evidence subsystem status. This record does not
> replace, bypass, or preempt the Evidence subsystem.

## Uncertainty / Verification State Contract

**Role**: Describes what is known, unknown, verified, inferred, stale, or
decision-required for a claim or artifact. Cross-cutting.

**Boundary**: State vocabulary and rationale only. Not a decision, approval,
rejection, or authorization.

### Frozen State Values

| Value | Meaning |
| --- | --- |
| `known` | The claim or artifact state is established from governed sources. |
| `unknown` | The claim or artifact state is not established. |
| `unverified` | The claim or artifact state has not been verified. |
| `partially_verified` | The claim or artifact state has been partially verified. |
| `weak` | The claim or artifact state has weak evidential support. |
| `possible` | The claim or artifact state is possible but not confirmed. |
| `inferred` | The claim or artifact state is inferred, not directly sourced. |
| `advisory_only` | The claim or artifact state derives from Advisory context only. |
| `decision_required` | A decision is needed to resolve the state. |
| `verified` | The claim or artifact state has been verified. |
| `invalid` | The claim or artifact state has been found invalid. |
| `stale` | The claim or artifact state is stale relative to current repository context. |
| `superseded` | The claim or artifact state has been superseded. |
| `conflicting` | The claim or artifact state is in conflict with another claim or artifact. |

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `state_value` | string | One of the frozen state values above. |
| `state_reason` | string | Why this state applies. |
| `supporting_sources` | array of referenced Source Attribution Records | Sources supporting the state assessment. |
| `state_limitations` | array of strings | Known limitations of this state assessment. |
| `timestamp_or_snapshot_context` | object | When this state was assessed and in what snapshot context. |

### Conditional Fields

| Field | Condition | Type | Meaning |
| --- | --- | --- | --- |
| `verification_method` | Required when state is `verified` or `partially_verified` | string | How verification was performed. |
| `reviewer_or_producer` | Required when state was assigned by a specific reviewer or producer | object | Reviewer or producer identity. |

### Optional Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `required_evidence` | array of strings | Evidence that would improve or change this state. |

### Frozen Boundary Disclaimer

> This Uncertainty / Verification State record describes what is known,
> unknown, verified, or uncertain about a claim or artifact. It is a
> descriptive state label and rationale. It does not decide, approve,
> reject, block, or authorize.

## Conflict / Supersession Record Contract

**Role**: Preserves disagreement, staleness, and replacement history.
Cross-cutting.

**Boundary**: Preservation of conflicting and superseded records. Not
cleanup, not resolution enforcement. Conflicting records are preserved
even when superseded.

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `conflict_id` | string | Unique identifier for this conflict or supersession record. |
| `conflicting_claims` | array of objects | Claims in conflict. Each has `claim_id`, `claim_text`, and `claim_source`. |
| `conflict_sources` | array of referenced Source Attribution Records | Sources of conflicting claims. |
| `conflict_type` | string | Nature of conflict. Frozen values: `direct_contradiction`, `partial_overlap`, `source_disagreement`, `version_divergence`, `interpretation_difference`, `scope_difference`, `temporal_inconsistency`. |
| `resolution_state` | string | Frozen values: `unresolved`, `resolved_by_supersession`, `resolved_by_clarification`, `resolution_deferred`, `preserved_as_historical`. |
| `preserved_history` | array of objects | Historical state preserved even after resolution. |
| `current_context_note` | string | How to interpret this record in the current repository context. |
| `limitations` | array of strings | Known limitations. |

### Conditional Fields

| Field | Condition | Type | Meaning |
| --- | --- | --- | --- |
| `superseded_artifact_or_claim` | Required when resolution involves supersession | object | Must include `superseded_id` and `superseded_summary`. |
| `superseded_by` | Required when a superseding artifact exists | artifact reference | Reference to the superseding artifact. |
| `supersession_reason` | Required when resolution is by supersession | string | Why the artifact or claim was superseded. |

### Optional Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `verification_state` | string | One of the frozen uncertainty/verification state values. |

### Frozen Boundary Disclaimer

> This Conflict / Supersession Record preserves disagreement, staleness,
> and replacement history. Conflict and supersession are part of the
> inspectable Repository Intelligence record, not cleanup chores.
> Conflicting records are preserved even when superseded. This record
> does not resolve conflicts, enforce resolution, or decide which claim
> is correct.

## Query Result Contract

**Role**: Read-only answer to a Repository Intelligence question.

**Boundary**: Read-only description and summarization. Not decision,
mutation, authorization, enforcement, or execution.

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `query_id` | string | Unique identifier for this query. |
| `query_type` | string | Type of query. Frozen values: `entity_lookup`, `relationship_lookup`, `dependency_path`, `impact_scope`, `historical_lineage`, `contract_conformance`, `source_trace`, `evidence_sweep`, `uncertainty_sweep`, `cross_artifact_search`. |
| `query_subject` | string | What the query is about. |
| `query_scope` | string | Scope boundary. |
| `query_inputs` | object | Query parameters and input constraints. |
| `result_entities` | array of objects | Entities matching the query. |
| `source_attributions` | array of embedded or referenced Source Attribution Records | Sources for result entities. |
| `uncertainty` | object | Uncertainty across result entities. |
| `conflicts` | array of referenced Conflict / Supersession Records | Conflicts relevant to the result. |
| `supersession` | array of referenced Conflict / Supersession Records | Supersession relevant to the result. |
| `evidence_links` | array of referenced Evidence Link Records | Evidence links relevant to the result. |
| `result_limitations` | array of strings | Known limitations. |

### Optional Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `result_relationships` | array of objects | Relationships matching the query. |

### Frozen Non-Decision Disclaimer

> This Query Result is a read-only answer to a Repository Intelligence
> question. It describes and summarizes. It does not decide, mutate,
> authorize, enforce, execute, approve, reject, block, or promote.

### Cross-Cutting Convention

- Source Attribution Records: embedded for result-level sources;
  referenced for per-entity sources.
- Evidence Link Records: referenced.
- Uncertainty / Verification State: embedded summary in envelope; detailed
  records referenced.
- Conflict / Supersession Record: referenced.

## Contract Conformance Record Contract

**Role**: Describes whether a Repository Intelligence artifact conforms to
the 119A/119B contract and this 119E artifact contract.

**Boundary**: Descriptive inspection result only. Not a Decision Evaluation
verdict. Does not approve, reject, block, promote, or quarantine.

### Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| *(common envelope)* | — | All required and conditional envelope fields. |
| `artifact_under_review` | artifact reference | The artifact being inspected. |
| `contract_version` | string | Contract version checked against. Frozen initial value: `119A.1.0/119E.1.0`. |
| `invariant_checks` | array of objects | Per-invariant check results. Each has `invariant_id`, `invariant_description`, `check_result` (one of: `conforms`, `violation`, `unable_to_assess`), and `check_detail`. |
| `source_attribution_check` | object | Must include `check_result` and `detail`. |
| `determinism_check` | object | Must include `check_result` and `detail`. |
| `read_only_check` | object | Must include `check_result` and `detail`. |
| `decision_boundary_check` | object | Must include `check_result` and `detail`. |
| `advisory_non_authority_check` | object | Must include `check_result` and `detail`. |
| `execution_boundary_check` | object | Must include `check_result` and `detail`. |
| `uncertainty_preservation_check` | object | Must include `check_result` and `detail`. |
| `conflict_preservation_check` | object | Must include `check_result` and `detail`. |
| `supersession_preservation_check` | object | Must include `check_result` and `detail`. |
| `conformance_status` | string | Frozen non-decision values: `conforms`, `conforms_with_observations`, `partial_conformance`, `non_conformance`, `unable_to_assess`. |
| `violations` | array of objects | Documented violations. Each has `invariant_id`, `violation_description`, and `affected_fields`. |
| `limitations` | array of strings | Known limitations of this conformance check. |
| `reviewer_or_verifier_identity` | object | Who or what performed the conformance check. Must include `reviewer_type` and `reviewer_identity`. |

### Frozen Non-Decision Status Vocabulary

The `conformance_status` field must use only these values. No status value
implies approval, rejection, blocking, promotion, quarantine, or lifecycle
action:

| Status | Meaning |
| --- | --- |
| `conforms` | The artifact meets all checked contract invariants. |
| `conforms_with_observations` | The artifact meets invariants but has noteworthy boundary conditions or limitations that do not rise to violations. |
| `partial_conformance` | The artifact meets some invariants and does not meet others, with violations documented. |
| `non_conformance` | The artifact does not meet the checked invariants. |
| `unable_to_assess` | The conformance check could not complete. |

### Frozen Non-Decision Disclaimer

Every Contract Conformance Record must include this disclaimer verbatim:

> This conformance record describes whether the inspected artifact meets
> the Repository Intelligence contract invariants at the time of
> inspection. It does not approve, reject, block, promote, quarantine,
> authorize, or decide. Decision Evaluation remains the sole decision
> maker in PCAE. This record is read-only and descriptive.

## Mandatory Artifact Invariants

Every Repository Intelligence artifact must preserve these invariants.
A future conformance verifier will check them.

### Identity and Context Invariants

1. Every artifact must disclose its `artifact_type` (artifact family).
2. Every artifact must disclose its `artifact_contract_version`.
3. Every artifact must disclose its `repository_identity`.
4. Every artifact must disclose its `repository_commit` or explicitly state
   `null` with a reason when no commit applies.

### Source Attribution Invariants

5. Every claim-bearing artifact must include source attribution for each
   claim, or explicitly mark the claim as `unknown`, `unverified`,
   `inferred`, or `advisory_only`.
6. No claim may be presented as canonical or verified without source
   attribution that meets the source attribution contract.

### Evidence Link Invariants

7. Every artifact must include at least one Evidence Link Record bridging
   to Evidence or explicitly marking an evidence gap.
8. No Evidence Link Record may claim `accepted_by_evidence_subsystem`
   status unless the Evidence subsystem has accepted it.

### Uncertainty / Verification Invariants

9. Every artifact must disclose its `verification_state` and
   `uncertainty_state`.
10. Every uncertainty-bearing artifact must preserve uncertainty; it must
    not collapse `unknown` or `unverified` into `known` without new
    verification.
11. Every verification claim must disclose the verification method.

### Conflict / Supersession Invariants

12. Every conflict-bearing artifact must preserve conflicting claims and
    sources.
13. Every supersession-bearing artifact must preserve supersession history
    and the superseded record.
14. Superseded records must remain inspectable; they must not be deleted
    or overwritten.

### Boundary Invariants

15. Every artifact must preserve the read-only boundary.
16. Every artifact must preserve the no-execution boundary.
17. Every artifact must preserve the non-decision boundary.
18. Every advisory-facing artifact must preserve Advisory non-authority.
19. No artifact may claim or imply authorization to mutate repository state.
20. No artifact may claim or imply execution approval or execution permission.
21. No artifact may claim or imply that it replaces Decision Evaluation.
22. No artifact may claim or imply that it replaces Repository State.
23. No artifact may claim or imply that it replaces Evidence.
24. No artifact may claim or imply that Advisory recommendations are
    authoritative or binding.

### Producer Invariants

25. Every artifact must disclose its producer identity.

### Limitations Invariants

26. Every artifact must disclose its known limitations.
27. An artifact that declares `["no known limitations"]` when limitations
    exist is non-conforming.

## Mandatory Source Attribution Contract

Every claim in a Repository Intelligence artifact that is not explicitly
marked `unknown`, `unverified`, `inferred`, or `advisory_only` must be
supported by at least one Source Attribution Record.

### Source Locator Vocabulary (Frozen)

| Locator type | Meaning | Example value |
| --- | --- | --- |
| `file_path` | Path relative to repository root | `src/pcae/commands/phase.py` |
| `file_path_line` | File path with line or line range | `src/pcae/commands/phase.py:42-58` |
| `file_path_symbol` | File path with symbol name | `src/pcae/commands/phase.py::complete_phase` |
| `file_path_section` | File path with Markdown section heading | `docs/ARCHITECTURE.md#Repository State` |
| `phase_id` | PCAE phase identifier | `119A` |
| `phase_report_id` | PCAE phase report artifact identifier | `20260708-0757-phase-119a` |
| `task_id` | PCAE task identifier | `20260708-0842-phase-119d` |
| `commit_sha` | Git commit hash | `abc123def456` |
| `tag` | Git tag | `v0.2.0` |
| `release_id` | GitHub Release or release tag | `v0.2.0` |
| `evidence_id` | Evidence artifact identifier | `ev_20260708_001` |
| `decision_id` | Decision Evaluation record identifier | `de_20260708_001` |
| `contract_document_section` | Named contract document and section | `119A#Repository Knowledge Contract` |
| `canonical_report_id` | Canonical phase report identifier | `latest-phase-report` |

Future implementation may add locator types but must not remove or rename
these frozen types.

### Artifact Reference Vocabulary (Frozen)

| Field | Classification | Meaning |
| --- | --- | --- |
| `ref_artifact_id` | Required | Stable identifier of the referenced artifact. |
| `ref_artifact_type` | Required | One of the twelve frozen `artifact_type` values. |
| `ref_relationship` | Required | One of: `contains`, `references`, `depends_on`, `derived_from`, `supersedes`, `documents`, `verifies`, `packages`, `context_for`. |
| `ref_materialization_state` | Conditional | Required when the referenced artifact may not yet exist. Values: `materialized`, `pending`, `not_yet_materialized`. |
| `ref_description` | Optional | Human-readable description of why the reference exists. |

The `ref_relationship` values are frozen. Future implementation may extend
but must not remove or rename these values.

### Source Attribution Rules

- Canonical claims require source attribution with `source_support_level`
  of `direct` or `indirect`.
- Claims marked `inferred` must disclose the inference basis and carry
  `source_support_level` of `implied`, `weak`, or `contextual`.
- Claims marked `advisory_only` must carry the Advisory non-authority
  disclaimer.
- A source marked `stale` does not invalidate the claim but must be
  disclosed.
- A source that `contradicts` a claim must be preserved alongside the
  claim, not omitted.

## Mandatory Evidence Link Contract

Every Repository Intelligence artifact must bridge to Evidence through at
least one Evidence Link Record.

### Evidence Link Rules

- An artifact that has no evidence links must include an Evidence Link
  Record with `evidence_type: evidence_gap_marker` and a description of
  the gap.
- An Evidence Link Record with `candidate_or_accepted_state: candidate`
  must not be presented as accepted Evidence.
- An Evidence Link Record with `candidate_or_accepted_state:
  accepted_by_evidence_subsystem` must reference the Evidence subsystem
  artifact that accepted it.
- An Evidence Link Record must not claim to replace, bypass, or preempt
  the Evidence subsystem.

## Mandatory Uncertainty / Verification Contract

Every artifact must disclose uncertainty and verification state.

### Uncertainty Rules

- `unknown` must be used when the state is not established, not when the
  producer prefers not to disclose.
- `inferred` must disclose the inference method or basis.
- `advisory_only` must carry the Advisory non-authority disclaimer.
- `verified` must disclose the verification method.
- `stale` must disclose the commit or phase relative to which it is stale.
- `superseded` must reference the superseding artifact or claim.
- `conflicting` must reference the Conflict / Supersession Record.

### Prohibited Uncertainty Collapses

An artifact must not:

- change `unknown` to `known` without new source attribution.
- change `unverified` to `verified` without documented verification.
- change `conflicting` to `resolved` without documenting resolution.
- omit `stale` when the artifact's sources are known to be stale.

## Mandatory Conflict / Supersession Contract

Every artifact must preserve conflict and supersession history.

### Conflict Rules

- Conflicting claims must both be preserved; neither may be deleted.
- A conflict record must identify both (or all) conflicting claims.
- Resolution state `unresolved` is valid; conflicts do not need to be
  resolved to be recorded.
- Resolution state `preserved_as_historical` must be used when the
  conflict is no longer active but the history is retained.

### Supersession Rules

- A superseded artifact or claim must remain inspectable.
- The supersession record must preserve what was superseded, what
  superseded it, and why.
- Supersession does not delete or overwrite the superseded record.

## Mandatory Derivation Disclosure Contract

Every artifact that is derived from other artifacts must disclose its
derivation.

### Derivation Rules

- `derivation_inputs` must list all input artifacts when derivation
  occurred.
- `derivation_method` must describe the derivation method in
  human-readable form.
- `derivation_rule_family` must name the rule family when rules were used.
- `derivation_limitations` must disclose known limitations of the
  derivation method.
- `derivation_nondeterminism_exclusions` must list aspects explicitly
  excluded from deterministic claims.
- An artifact that is not derived (e.g., a human-authored source
  attribution record) may omit derivation fields.

### Prohibited Derivation Claims

- An artifact must not claim deterministic derivation when
  nondeterministic methods (e.g., model inference) contributed to the
  result without disclosure.
- An artifact must not claim `derivation_method: repository-derived rules`
  when model inference was the actual method.

## Mandatory Versioning / Snapshot Contract

Every artifact must relate itself to repository and lifecycle version
context.

### Versioning Rules

- `artifact_contract_version` identifies the frozen contract version the
  artifact obeys. Initial frozen value: `119E.1.0`.
- `schema_concept_version` identifies the conceptual schema version.
  Initial frozen value: `119C.1.0-concept`.
- `repository_commit` identifies the repository commit the artifact
  describes, or `null` with reason.
- `repository_branch` identifies the branch context when known.
- `release_context` identifies the release when the artifact relates to
  a release.
- `phase_context` identifies the PCAE phase when the artifact relates to
  a phase.
- `generated_at_utc` records when the artifact was created.

### Versioning Distinctions

The contract distinguishes:

| Concept | Field | Meaning |
| --- | --- | --- |
| Contract version | `artifact_contract_version` | Which frozen contract rules the artifact obeys. |
| Schema concept version | `schema_concept_version` | Which conceptual schema describes the artifact shape. |
| Repository version | `repository_commit` | Which repository state the artifact describes. |
| Artifact identity | `artifact_id` | Which specific artifact instance this is. |

Future executable schema versions must map to both a contract version and
a schema concept version.

## Forbidden Artifact Claims

No Repository Intelligence artifact may include any field, claim, or
implication that:

### Authorization and Execution

1. Asserts that an action is authorized (`action_authorized`, `may_proceed`).
2. Asserts that execution is approved (`execution_approved`, `may_execute`).
3. Asserts that a commit is permitted (`commit_permitted`, `may_commit`).
4. Asserts that a push is permitted (`push_permitted`, `may_push`).
5. Asserts that a lifecycle transition is valid (`transition_valid`,
   `phase_approved`).
6. Asserts or implies that execution is available through Repository
   Intelligence.

### Decision Evaluation

7. Claims to replace, bypass, or preempt Decision Evaluation.
8. Uses verdict language (`approved`, `rejected`, `blocked`, `passed`,
   `failed`) as an artifact-level conclusion.
9. Claims that an artifact's description constitutes a decision.

### Repository State and Evidence

10. Claims to replace, bypass, or preempt Repository State.
11. Claims to replace, bypass, or preempt Evidence.
12. Presents an Evidence Link Record with `candidate` state as accepted
    Evidence.

### Advisory Authority

13. Presents an Advisory recommendation as authoritative or binding.
14. Claims that Advisory context implies Advisory approval.
15. Omits the `non_authority_marker` on an Advisory recommendation.

### Model Inference

16. Presents model-inferred content as canonical truth without governed
    source attribution.
17. Presents model inference as deterministic derivation.
18. Omits the `inferred` uncertainty state when model inference
    contributed to the result.

### Mutation

19. Claims or implies permission to mutate repository state.
20. Claims or implies permission to mutate lifecycle state.
21. Claims or implies that the artifact itself performs mutation.

### Canonical and Lifecycle

22. Claims canonical status (`is_canonical: true`) without a governed
    promotion path.
23. Claims to represent PCAE's official position without governed
    authorization.
24. Asserts phase completion, task completion, or lifecycle transition.

## Artifact Conformance Model

### Conformance States

An artifact is assessed against this contract. The conformance status
values are:

| Status | Definition |
| --- | --- |
| `conforms` | All required fields present. All conditional fields present when conditions are met. All invariants preserved. All boundary disclaimers present and correct. No forbidden claims present. All source attribution meets the source attribution contract. |
| `conforms_with_observations` | As `conforms`, but with noteworthy boundary conditions or limitations documented. Observations do not rise to violations but deserve attention. |
| `partial_conformance` | Some invariants met, some violated. Violations are documented. The artifact is partially usable but non-conformance is declared. |
| `non_conformance` | Required fields missing, invariants violated, boundary disclaimers missing or incorrect, or forbidden claims present. The artifact does not meet the contract. |
| `unable_to_assess` | The conformance check could not complete (e.g., referenced artifacts unavailable, repository context missing). |

### What Makes an Artifact Non-Conforming

An artifact is non-conforming if any of these conditions hold:

1. A required common envelope field is missing.
2. A required family-specific field is missing.
3. A conditional field is missing when its triggering condition is met.
4. A boundary disclaimer is missing or substantively altered.
5. A claim lacks required source attribution and is not marked `unknown`,
   `unverified`, `inferred`, or `advisory_only`.
6. An Evidence Link Record is missing and no `evidence_gap_marker` is
   present.
7. `verification_state` or `uncertainty_state` is missing.
8. A forbidden claim (see Forbidden Artifact Claims) is present.
9. The `conformance_status` in a Contract Conformance Record uses a value
   outside the frozen vocabulary.
10. `candidate_or_accepted_state: accepted_by_evidence_subsystem` is used
    without a valid Evidence subsystem reference.
11. The `limitations` field is empty or declares `["no known limitations"]`
    when limitations are known to exist.

### Staleness and Supersession of the Artifact Itself

An artifact is `stale` when its `repository_commit` no longer reflects the
current repository state and the artifact has not been regenerated. An
artifact is `superseded` when a later artifact of the same family
explicitly supersedes it.

Staleness and supersession are declared in the envelope's
`supersession_state` field. They do not make the artifact non-conforming;
they describe its relationship to current repository context.

## Contract Compatibility Matrix

| Artifact Family | Repository Knowledge | Historical Memory | Dependency Graph | Change Impact | Evidence | Repository Skills | Advisory | Decision Evaluation | Repository State | Lifecycle |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Repository Intelligence Package | contains or references | contains or references | contains or references | contains or references | evidence links only | no direct relationship | context for Advisory | non-decision boundary | descriptive only | phase context only |
| Repository Knowledge Snapshot | — (is foundational) | provides entity basis | provides entity basis | provides impact basis | evidence links only | no direct relationship | context for Advisory | non-decision boundary | descriptive only | no authority |
| Historical Memory Snapshot | temporal layer of | — (is temporal RK) | provides temporal edges | provides historical impacts | evidence links only | no direct relationship | context for Advisory | non-decision boundary | descriptive only | phase events recorded |
| Dependency Knowledge Graph Snapshot | relationship layer of | consumes temporal context | — (is graph RK) | provides dependency paths | evidence links only | no direct relationship | context for Advisory | non-decision boundary | descriptive only | no authority |
| Change Impact Report | consumes RK entities | consumes historical impacts | consumes dependency paths | — (is impact) | evidence links only | no direct relationship | context for Advisory | non-decision boundary | descriptive only | no authority |
| Advisory Intelligence Context Package | may reference | may reference | may reference | may reference | evidence links only | no direct relationship | non-authoritative context | handoff to DE | descriptive only | no authority |
| Source Attribution Record | leaf record | leaf record | leaf record | leaf record | leaf record | leaf record | leaf record | leaf record | leaf record | leaf record |
| Evidence Link Record | bridge to Evidence | bridge to Evidence | bridge to Evidence | bridge to Evidence | bridge only | bridge only | bridge to Evidence | provides candidates | bridge only | bridge only |
| Uncertainty / Verification State | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting |
| Conflict / Supersession Record | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting | cross-cutting |
| Query Result | may query | may query | may query | may query | evidence links only | no direct relationship | context for Advisory | non-decision boundary | descriptive only | no authority |
| Contract Conformance Record | inspects conformance | inspects conformance | inspects conformance | inspects conformance | inspects conformance | inspects conformance | inspects conformance | non-decision boundary | inspects conformance | inspects phase context |

**Key:**

- **contains or references** — the artifact may embed or reference artifacts of that type.
- **no direct relationship** — the artifact family has no defined relationship to that subsystem.
- **descriptive only** — the artifact may describe but not mutate, decide, or authorize.
- **non-decision boundary** — the artifact must not cross into decision territory.
- **evidence links only** — the artifact may bridge to Evidence via Evidence Link Records but must not replace or bypass Evidence.
- **bridge only** — the Evidence Link Record bridges but does not replace.
- **cross-cutting** — the record is used across all artifact families.
- **leaf record** — the Source Attribution Record is a leaf; it does not embed other cross-cutting records.
- **context for Advisory** — the artifact may provide context for Advisory but Advisory remains non-authoritative.
- **handoff to DE** — the Advisory Intelligence Context Package includes a handoff note to Decision Evaluation.
- **no authority** — the artifact has no authority over that subsystem.
- **phase context only** — the artifact may reference phase context but has no lifecycle authority.
- **phase events recorded** — Historical Memory records phase events descriptively.
- **inspects conformance** — the Contract Conformance Record inspects artifacts for contract conformance.
- **inspects phase context** — the Contract Conformance Record may inspect phase-related fields.

## Future Executable Schema Constraints

Future phases may translate this artifact contract into executable schemas
(JSON Schema, Pydantic models, dataclasses, validators). They must obey
these constraints.

### Permitted

- Create JSON Schema files, Pydantic models, dataclasses, or validators
  that implement the frozen field names, types, and classifications in
  this contract.
- Create conformance validators that check whether an artifact meets the
  frozen invariants.
- Create tests that verify schema implementations conform to this contract.
- Create read-only artifact instances that conform to this contract.
- Extend the source locator vocabulary with additional locator types.
- Extend the artifact reference vocabulary with additional relationship
  types.
- Create conceptual-to-executable mapping documents that trace each
  executable schema element to its contract source.

### Prohibited

- Remove or rename frozen fields without a governed contract revision.
- Change frozen status vocabulary values or their meanings.
- Change required/optional/conditional classifications without a governed
  contract revision.
- Add execution, mutation, authorization, or enforcement through schema
  implementation.
- Add fields that carry forbidden claim semantics (see Forbidden Artifact
  Claims).
- Convert model inference into canonical truth without governed artifact
  attribution.
- Bypass Decision Evaluation.
- Replace Evidence.
- Replace Repository State.
- Turn artifact schemas into runtime orchestration.
- Expand Advisory authority beyond what is frozen in this contract.

## Future Prototype Constraints

Future prototype phases may produce read-only Repository Intelligence
artifacts. They must obey these constraints.

### Permitted

- Produce read-only artifacts conforming to this contract.
- Inspect repository files, commits, tags, phase reports, and lifecycle
  artifacts as sources.
- Create source-attributed snapshots using governed sources.
- Produce verification-only outputs (do not decide or authorize).
- Produce query/report artifacts that describe and summarize.
- Materialize artifacts in any order provided the package materialization
  order contract is preserved.
- Use embedded cross-cutting records exclusively in early prototypes
  (deferring the embedded/referenced distinction until referential
  integrity mechanisms exist).

### Prohibited

- Execute commands, invoke runtimes, or mediate shells as Repository
  Intelligence behavior.
- Mutate repository state, lifecycle state, or any PCAE subsystem state.
- Enforce, authorize, or block.
- Change Advisory behavior authority.
- Bypass lifecycle governance.
- Present prototype artifacts as canonical without governed promotion.
- Commit or push through Repository Intelligence behavior.

## Future Query / Report Constraints

Future phases that expose query or report capabilities over Repository
Intelligence artifacts must obey these constraints.

### Permitted

- Query artifacts by artifact type, repository commit, phase context, or
  cross-cutting state.
- Produce Query Result artifacts conforming to the Query Result contract.
- Aggregate, summarize, and compare artifacts.
- Surface uncertainty, conflict, and supersession without resolving them.

### Prohibited

- Query results that use decision or verdict language.
- Query interfaces that accept mutation, execution, or authorization
  commands.
- Query results that omit uncertainty, conflict, or supersession when
  present in source artifacts.
- Query results that present model-inferred answers as canonical without
  governed source attribution.

## Repository Skills Exposing Artifacts — Constraints

Future Repository Skills that expose Repository Intelligence artifacts
must obey these constraints.

### Permitted

- Present read-only artifact content to humans or Advisory.
- Filter, sort, and format artifact content.
- Surface source attribution, uncertainty, and limitations alongside
  artifact content.

### Prohibited

- Present artifact content as decisions, approvals, or authorizations.
- Omit boundary disclaimers when presenting artifact content.
- Present `candidate` Evidence Link Records as accepted Evidence.
- Present Advisory recommendations without the `non_authority_marker`.
- Accept or execute mutation commands through artifact presentation.

## Advisory Consumer Constraints

Future Advisory behavior that consumes Repository Intelligence artifacts
must obey these constraints.

### Permitted

- Consume Advisory Intelligence Context Packages as bounded context.
- Reference Repository Knowledge, Historical Memory, Dependency Graph,
  and Change Impact Reports in explanations and recommendations.
- Surface uncertainty, evidence gaps, and limitations in Advisory output.
- Produce more informed explanations, recommendations, and handoff context.

### Prohibited

- Treat Advisory recommendations as authoritative or binding.
- Claim that Advisory context implies Advisory approval.
- Omit the non-authority disclaimer from Advisory output that draws on
  Repository Intelligence.
- Use Repository Intelligence to expand Advisory's decision-making
  authority.
- Execute, mutate, authorize, or enforce based on Repository Intelligence
  context.

## Minor Clarifications from 119D Addressed

Phase 119D identified six clarifications needed before or during artifact
contract freeze. This section records where each is addressed.

1. **Canonical field names and minimal required fields** — Addressed by the
   per-family contracts above, which freeze canonical field names in
   lowercase snake_case and classify every field as required, optional, or
   conditional.

2. **Required versus optional/conditional envelope fields** — Addressed by
   the Common Artifact Envelope Contract, which classifies every envelope
   field as required, conditional (with triggering condition stated), or
   optional.

3. **Embedded versus referenced cross-cutting records** — Addressed by the
   Cross-Cutting Record Convention in the Common Artifact Envelope Contract
   and the per-family cross-cutting conventions. The dual convention
   (embedded for artifact-scoped records, referenced for shared records) is
   frozen.

4. **Repository Intelligence Package materialization order** — Addressed by
   the Materialization Order section in the Repository Intelligence Package
   Contract. Package-as-aggregation (components first, package last) is the
   default. Package-as-plan is permitted only with `ref_materialization_state`
   markers.

5. **Contract Conformance Record non-decision wording** — Addressed by the
   Frozen Non-Decision Status Vocabulary and Frozen Non-Decision Disclaimer
   in the Contract Conformance Record Contract. The five status values use
   descriptive language; the disclaimer is required verbatim.

6. **Source locator vocabulary and artifact reference vocabulary** —
   Addressed by the Source Locator Vocabulary and Artifact Reference
   Vocabulary tables in the Mandatory Source Attribution Contract. Fourteen
   locator types and nine reference relationship types are frozen.

## Risks

- Frozen field names could be misinterpreted as implementation requirements
  before prototype planning.
- The embedded-versus-referenced distinction could be collapsed in early
  prototypes that always embed, losing referential integrity for shared
  records.
- `conforms` status could be read as "approved" despite the frozen
  non-decision wording.
- `candidate_or_accepted_state` boundary could erode if Evidence subsystem
  integration is deferred.
- Source locator vocabulary may need extension for non-Git repositories.
- Package materialization order may be ignored in early prototypes that
  materialize the package first without `pending` markers.
- The twelve-family inventory may feel complete enough that future work
  defers adding genuinely needed families.
- The per-family contracts are detailed enough that a future phase may
  treat them as executable schema specifications rather than conceptual
  contracts.
- Contract versioning (`119E.1.0`) may need a revision governance process
  that does not yet exist.

## Open Questions

1. Should the first executable schema contract freeze target the common
   envelope alone, a single artifact family, or all twelve families at once?
2. What minimum fixture set exercises all frozen field classifications
   (required, optional, conditional) and all cross-cutting conventions?
3. Should Contract Conformance Record verification remain fully manual
   until executable schemas exist, or can partial automated checks against
   the frozen envelope fields begin earlier?
4. Should `repository_identity` default to `composite` with both URL and
   local-path identity in multi-remote or air-gapped repositories?
5. Whether future prototype phases should be required to produce a Contract
   Conformance Record alongside each prototype artifact, or whether
   conformance checking can be deferred.
6. Whether the frozen `dependency_types` vocabulary is sufficient for the
   first prototype or will need immediate extension.
7. How should future Advisory Context Package sections carry Repository
   Intelligence references without unbounded prompt content?
8. Which conformance checks should remain manual until an extractor or
   executable schema exists?

## Recommended Next Phase

Recommended next phase: **119F — Repository Intelligence Artifact Contract
Verification**.

Reason: before executable schema architecture or prototype planning, PCAE
should verify that the frozen artifact contract is internally consistent,
testable, and ready to constrain future schema and prototype work. The
artifact contract freeze (119E) should be followed by artifact contract
verification (119F), mirroring the sequence contract freeze (119A) →
contract verification (119B) that preceded conceptual schema work.

119F should verify:

- internal consistency across all twelve family contracts;
- that no family contract contradicts another;
- that the common envelope contract is sufficient for all families;
- that all 119A/119B invariants are preserved;
- that the forbidden claims list is complete against the current contract;
- that the conformance model can be applied to each family;
- that future executable schema and prototype phases have clear,
  non-conflicting constraints.
