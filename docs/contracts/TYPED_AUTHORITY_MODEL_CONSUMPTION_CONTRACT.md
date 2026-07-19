# Typed Authority Model Consumption Contract

## Contract identity and status

**Contract:** TAMC-001  
**Version:** 1.0  
**Status:** FROZEN  
**Frozen by:** Phase 137B — Typed Authority Model Consumption Contract Freeze

TAMC-001 v1.0 is the sole authoritative contract governing consumption of
the Stage 3 Typed Authority Model. Future implementation phases SHALL
reference this contract and SHALL NOT redefine consumption behavior locally.

The Phase 137A architecture is the approved design basis for this contract.
Where architecture prose and this contract differ in force, this contract is
normative. Existing Stage 3 contracts remain authoritative for schema shape,
typed representation, registry, and manifest content; TAMC-001 governs only
how those artifacts and their outputs may be consumed.

This is contract text only. It does not implement, activate, authorize, or
integrate a consumer. It does not grant runtime, lifecycle, or authority
capability.

## 0. Normative language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**, **SHOULD**,
**SHOULD NOT**, and **MAY** are normative. `SHALL` and `MUST` state binding
requirements; `SHALL NOT` and `MUST NOT` state binding prohibitions; `SHOULD`
states a requirement from which deviation requires explicit governed
justification; and `MAY` states a permission within all other requirements.

A **consumer** is the smallest operation that reads, validates, transforms,
compares, serializes, deserializes, displays, or reports on an in-scope
artifact. A component that also owns an independently governed side effect
SHALL keep that side effect outside its consumption operation. Calling a
component an Allowed Consumer does not authorize all behavior of that
component.

## 1. Purpose

TAMC-REQ-001: Every present and future consumer SHALL obey the permitted-use,
prohibition, invariant, ownership, neutrality, provenance, error-handling,
compatibility, and compliance requirements in this contract.

TAMC-REQ-002: Permitted consumption SHALL be read-only, deterministic,
idempotent, side-effect free, provenance-preserving, authority-neutral,
lifecycle-neutral, and runtime-neutral.

TAMC-REQ-003: Consumer output SHALL be explainable from the exact in-scope
artifact content and provenance that produced it. A consumer SHALL NOT emit an
untraceable conclusion.

TAMC-REQ-004: Compliance with TAMC-001 grants permission to observe and
describe representations only. It grants no permission to establish facts as
operative, change governed state, or execute actions.

## 2. Scope

TAMC-REQ-005: This contract applies to consumption of all sixteen frozen
Typed Authority Model record families:

1. `authority_epoch`
2. `authority_state`
3. `certification`
4. `compatibility_state`
5. `concurrency_conflict`
6. `cutover_candidate`
7. `cutover_request`
8. `human_authorization`
9. `marker_authority_binding`
10. `notification_authority_binding`
11. `publication_attempt`
12. `publication_evidence`
13. `quarantine_record`
14. `readiness_package`
15. `receipt_authority_binding`
16. `recovery_journal_entry`

TAMC-REQ-006: This contract also applies to consumption of the Stage 3 schema
registry, companion-schema manifest, serialization outputs,
deserialization outputs, and every validation output derived from an
in-scope artifact.

TAMC-REQ-007: Scope is independent of surface or implementation language. It
includes CLI, reporting, diagnostics, bootstrap, session-state,
reconciliation, packaging, inspection, repository-intelligence, and future
tooling consumers.

TAMC-REQ-008: A wrapper, adapter, cache, renderer, summary, export, or
downstream consumer of a consumption result SHALL NOT evade this contract.
An output remains governed while it carries or derives from in-scope content.

## 3. Non-goals and frozen posture

TAMC-REQ-009: TAMC-001 SHALL NOT introduce or authorize execution, authority
activation, lifecycle mutation, cutover, publication, recovery,
compatibility execution, or any runtime capability change.

TAMC-REQ-010: TAMC-001 SHALL NOT authorize a producer, writer, persistence
mechanism, authority resolver, authority pointer, migration, rehearsal,
cutover mechanism, or legacy-retirement mechanism.

TAMC-REQ-011: The runtime posture remains:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

No consumer conforming to TAMC-001 may cause any element of this posture to
change.

## 4. Consumer classification

Classification is exhaustive. A consumer is Allowed, Future, or Forbidden.
An unclassified behavior is not Allowed.

### 4.1 Allowed Consumers

TAMC-REQ-012: Exactly the following consumer categories are Allowed, and only
while the consumption operation satisfies every requirement of TAMC-001:

- bootstrap reporting;
- session-state reporting;
- report generation;
- CLI display;
- diagnostics;
- reconciliation;
- schema validation;
- serialization and deserialization;
- packaging;
- inspection; and
- future read-only repository intelligence.

TAMC-REQ-013: Every Allowed Consumer SHALL remain read-only. An Allowed
category names a permitted observation purpose, not permission to mutate,
persist, execute, authorize, dispatch, publish, recover, or progress
lifecycle.

TAMC-REQ-014: If an Allowed surface normally persists its own report,
session, metadata, or other output, the consumption operation SHALL return a
value without performing that persistence. Only the independently governed
owner of the outer output may persist it under that owner's existing
contract. The persisted output SHALL retain all provenance and neutrality
disclosures required here.

TAMC-REQ-015: Reconciliation MAY identify agreement, disagreement, or missing
comparable data. It SHALL NOT decide which representation is authoritative,
repair either representation, or trigger a response.

TAMC-REQ-016: Packaging MAY include frozen artifacts and verify their
presence or integrity. It SHALL NOT activate or execute packaged content.

### 4.2 Future Consumers

TAMC-REQ-017: The following categories are Future Consumers and are not
authorized by TAMC-001 v1.0:

- shadow comparison;
- semantic validation;
- cutover analysis; and
- migration planning.

TAMC-REQ-018: Before a Future Consumer may become Allowed, a dedicated future
Architecture phase and a dedicated future Contract Freeze phase SHALL both
be completed through governed lifecycle semantics. Those phases SHALL define
the consumer's exact inputs, outputs, ownership, errors, provenance, and
neutrality and SHALL explicitly preserve TAMC-001's invariants.

TAMC-REQ-019: A Future Consumer SHALL NOT become Allowed by implementation,
deployment, record presence, convention, or inference. Its future frozen
contract SHALL explicitly reclassify it and reference TAMC-001 or a governed
successor. Until then, it remains unauthorized.

### 4.3 Forbidden Consumers

TAMC-REQ-020: A consumer is Forbidden if it activates authority, modifies
lifecycle, changes authority state, executes a runtime action, bypasses
lifecycle, or infers authority solely from model presence, validity, or
successful deserialization.

TAMC-REQ-021: Forbidden Consumers SHALL NOT be designed, implemented,
integrated, invoked, or described as TAMC-001-compliant. Any such act is a
contract breach and requires governed rejection or removal; it cannot be
waived by local code or documentation.

## 5. Consumer invariants

Every compliant consumer SHALL satisfy all of the following for every
consumption operation:

TAMC-REQ-022: Treat each typed model and its nested values as immutable.

TAMC-REQ-023: Never mutate a record, a value derived from it for the purpose
of simulating record mutation, the registry, or the manifest.

TAMC-REQ-024: Never establish, activate, transfer, select, or revoke
authority.

TAMC-REQ-025: Never infer authority, authorization, approval,
certification, completion, publication status, execution permission, or
operative state from record existence, validity, content, or location.

TAMC-REQ-026: Never infer lifecycle state or progression from an in-scope
artifact.

TAMC-REQ-027: Never repair malformed records, coerce incompatible records,
fill absent required values, resolve uncertainty, or fabricate missing
information.

TAMC-REQ-028: Preserve provenance, record identity, schema identity and
version, typed-model version information when present, digest identity,
references, limitations, uncertainty, and derivation.

TAMC-REQ-029: Remain deterministic: identical input bytes, explicitly
provided context, and contract version SHALL produce identical output or
identical failure. Wall clock, randomness, process history, network state,
ambient filesystem state, and unordered traversal SHALL NOT affect the
result.

TAMC-REQ-030: Remain idempotent and replay-neutral: repeated consumption
SHALL produce the same result and SHALL create no accumulated effect.

TAMC-REQ-031: Remain side-effect free: consumption SHALL NOT write files or
state, open network connections, launch processes, dispatch notifications,
invoke governed commands, or cause any external mutation.

TAMC-REQ-032: Remain explainable: every restatement and derivation SHALL be
traceable to identified input fields, and direct content SHALL be
distinguishable from derived output.

## 6. Ownership contract

TAMC-REQ-033: Responsibility SHALL have exactly one owner. A consumer SHALL
NOT duplicate, shadow, replace, or partially assume another owner's
responsibility.

| Responsibility | Sole owner | Consumer boundary |
|---|---|---|
| Executable schema shape, required/optional fields, enums, and discriminators | Frozen Stage 3 executable schemas in `src/pcae/schema_resources/cltr_cutover/**` | Consumers SHALL NOT redefine or relax shape. |
| Typed representation, local model invariants, immutability, and serialization | Frozen Stage 3 typed models in `src/pcae/cltr/authority/*.py` | Consumers SHALL NOT create substitute representations or bypass model invariants. |
| Schema conformance | Stage 3 Draft 2020-12 validation engine | Consumers may request schema validation but SHALL NOT substitute another validation class. |
| Semantic validation | A future semantic-validation architecture and contract; no current owner is authorized to implement it | Current consumers SHALL NOT claim or perform it. |
| Lifecycle state and progression | Governed lifecycle mechanisms (`pcae task`, phase reporting/completion, and governed successors) | Consumers may cite lifecycle output but SHALL NOT change or infer lifecycle state. |
| Governance policy and compliance determination | PCAE governance mechanisms and governed review | Consumers SHALL NOT waive or redefine governance. |
| Runtime capability and execution availability | PCAE Runtime Architecture and runtime governance | Consumers SHALL NOT grant or activate capability. |
| Reporting-surface composition and any independently authorized output persistence | The individual governed reporting surface | The consumption operation supplies read-only content only and SHALL NOT persist it. |
| Authority origination and operative authority determination | Governed lifecycle semantics alone | No model, schema, validator, report, runtime surface, or consumer owns authority. |

TAMC-REQ-034: The lifecycle owner owns state progression; authority
origination is a distinct governed semantic consequence of that lifecycle.
This distinction SHALL NOT be used to create a second authority owner or a
second lifecycle owner.

## 7. Authority contract

**Representation SHALL NEVER establish authority.**

TAMC-REQ-035: Authority SHALL ALWAYS originate from governed lifecycle
semantics, never from representation, validation, consumption, storage,
location, naming, freshness, digest agreement, or record count.

TAMC-REQ-036: The existence or validity of a typed record SHALL NEVER imply:

- authorization;
- completion;
- approval;
- certification;
- publication;
- execution;
- runtime permission; or
- any other operative authority state.

TAMC-REQ-037: When output could plausibly be mistaken for an authority
determination, the consumer SHALL disclose that it reports a representation
only and that governed lifecycle semantics remain authoritative.

TAMC-REQ-038: A consumer MAY state that a record contains a particular claim
or field value. It SHALL NOT restate that claim as an operative fact.

## 8. Validation contract

TAMC-REQ-039: The five validation classes are distinct and SHALL NOT be
substituted, collapsed, or used as evidence that another class passed.

| Validation class | Normative question | Owner |
|---|---|---|
| Schema validation | Does serialized input conform to its frozen Draft 2020-12 schema? | Stage 3 validation engine and executable schema |
| Model validation | Does the typed object satisfy its model-local construction invariants? | The corresponding frozen typed model |
| Semantic validation | Are cross-record meanings contextually valid? | Future owner only; not currently authorized |
| Lifecycle validation | Is observed information consistent with governed lifecycle state? | Existing lifecycle/governance checks, only if explicitly extended by a future phase |
| Governance validation | Does the proposed or actual consumption comply with governing contracts and task boundaries? | PCAE governance and governed review |

TAMC-REQ-040: Schema-valid or model-valid SHALL NOT be treated as
semantic-valid, lifecycle-valid, governance-valid, authoritative, or
executable.

TAMC-REQ-041: A consumer SHALL NOT claim semantic or record-aware lifecycle
validation unless a dedicated future architecture and contract expressly
authorize that exact responsibility.

## 9. Provenance contract

TAMC-REQ-042: A consumer SHALL preserve, without silent deletion or
replacement:

- origin;
- source artifact identity or location;
- schema identity and schema version;
- typed-model version information, when supplied by the model or input
  context;
- digest, including declared file or record digest as applicable;
- record identity;
- all references and their family/identity/digest fields;
- derivation chain and the distinction between source content and derived
  content;
- limitations;
- uncertainty and deferred/opaque disclosures; and
- authority-neutrality disclosures.

TAMC-REQ-043: If an item of provenance is not present in the input or
explicitly provided context, the consumer SHALL identify it as unavailable
when relevant and SHALL NOT fabricate it. Preservation does not authorize an
ambient lookup to obtain missing provenance.

TAMC-REQ-044: A summary SHALL preserve enough identity and derivation
information for a downstream reader to identify the exact source record and
distinguish copied facts from computed statements. Brevity SHALL NOT justify
provenance loss.

TAMC-REQ-045: A consumer SHALL preserve the declared digest as provenance.
It MAY separately report a deterministic integrity comparison when schema
validation or diagnostics owns that operation, but SHALL NOT overwrite,
silently replace, or discard the declared digest.

## 10. Runtime contract

TAMC-REQ-046: A consumer SHALL NOT execute, dispatch, authorize, mutate,
persist, publish, recover, roll back, quarantine, or activate runtime
capability.

TAMC-REQ-047: A consumer SHALL NOT trigger, schedule, gate, recommend to an
automated actor, or conditionally invoke an executable action from record
content.

TAMC-REQ-048: Consumers SHALL remain observation-only. Consumption SHALL NOT
change Runtime's Observed / observe / unavailable posture.

## 11. Lifecycle contract

TAMC-REQ-049: A consumer SHALL NOT advance, complete, pause, resume, replace,
or otherwise alter lifecycle state; complete a phase; authorize cutover;
create authority; or cause a lifecycle transition.

TAMC-REQ-050: Lifecycle remains the sole owner of lifecycle progression and
the sole origin of authority semantics. A record MAY be cited by a report,
metadata item, receipt, marker, checkpoint, notification, or Architecture
Status output, but SHALL NOT substitute for the governed mechanism that owns
that artifact or event.

TAMC-REQ-051: Any lifecycle mutation performed by an outer component SHALL
be independently authorized and SHALL NOT be caused, gated, or justified by
the consumption result. Otherwise the component is a Forbidden Consumer.

## 12. Error-handling contract

TAMC-REQ-052: A consumer SHALL fail deterministically for:

- malformed records;
- absent schema-required references or structurally malformed references;
- unsupported schema versions;
- incompatible or unsupported model versions;
- unknown record families;
- record-family, `record_type`, or schema-identity mismatch;
- partial records;
- corrupted, contradictory, or unverifiable required provenance; and
- any input for which safe, contract-compliant interpretation is not
  uniquely defined.

TAMC-REQ-053: Failure SHALL be stable for the same input and explicitly
provided context. A consumer SHALL NOT silently retry, fall back, coerce,
repair, infer, fabricate, select a nearby version, or substitute a default.

TAMC-REQ-054: References are structural identity/digest/family values, not
authority to access the filesystem, network, registry, or another service.
A missing required reference value is an error. Failure to find a referenced
target in an explicitly supplied, in-memory comparison set MAY be reported
as deterministic missing-reference output where that Allowed operation owns
the comparison; it SHALL NOT trigger ambient dereferencing or imply that the
target does not exist globally.

TAMC-REQ-055: An unsupported future schema or model version SHALL be
rejected, even when it appears backward compatible, until a governed
contract revision explicitly authorizes support.

## 13. Extensibility contract

TAMC-REQ-056: Future record families SHALL be additive. Adding a family
SHALL NOT alter the meaning, classification, obligations, or accepted inputs
of an existing consumer.

TAMC-REQ-057: Existing family-generic compliant consumers SHALL continue
operating without modification for their already-supported inputs. A generic
consumer MAY consume a future family only when its dispatch and provenance
rules do not rely on a frozen family enumeration and a governed contract has
authorized the family.

TAMC-REQ-058: A family-specific consumer SHALL explicitly opt in through a
governed change before consuming a future family. It SHALL NOT silently
interpret an unknown family.

TAMC-REQ-059: Adding a family SHALL NOT change an Allowed, Future, or
Forbidden classification. Classification is determined by behavior.

## 14. Security contract

TAMC-REQ-060: Consumers SHALL preserve recursive immutability and SHALL NOT
use subclassing, monkeypatching, `object.__setattr__`, serialization tricks,
or mutable aliases to bypass it.

TAMC-REQ-061: Consumers SHALL preserve declared digest integrity, provenance,
limitations, and uncertainty through every derived output.

TAMC-REQ-062: Consumers SHALL remain replay-neutral and authority-neutral.
Reading a record again or after process restart SHALL create no new effect or
stronger claim.

TAMC-REQ-063: Consumption SHALL NOT escalate privilege, grant capability,
bypass governance, weaken validation, or convert read permission into write
or execution permission.

TAMC-REQ-064: Untrusted or malformed content SHALL fail closed at the owning
validation boundary. Error text and diagnostics SHALL NOT disclose secrets or
invent authoritative interpretation.

## 15. Compatibility contract

TAMC-REQ-065: TAMC-001 and future Typed Authority Model consumption
contracts SHALL remain backward compatible for already-supported inputs and
frozen meanings unless a governed contract revision explicitly supersedes a
requirement and states its compatibility impact.

TAMC-REQ-066: Backward compatibility SHALL NOT be interpreted as permission
to accept an unknown schema version, unknown model version, unknown family,
weaker validation, missing provenance, or forbidden behavior.

TAMC-REQ-067: A governed revision SHALL identify its predecessor, version,
changed requirements, migration effect, affected consumer classes, and
whether it is backward compatible. Local implementation behavior SHALL NOT
supersede TAMC-001.

## 16. No-Go contract

TAMC-REQ-068: A consumption implementation SHALL NOT introduce, contain,
invoke, or serve as a bridge to any of the following:

- authority resolver;
- authority persistence;
- authority pointer;
- authority activation;
- runtime execution;
- execution adapters;
- lifecycle mutation;
- cutover execution;
- publication execution;
- recovery execution;
- rollback execution;
- compatibility execution;
- quarantine execution;
- semantic decision engine; or
- legacy retirement or bypass.

TAMC-REQ-069: Renaming, wrapping, splitting, deferring, or making a No-Go
operation conditional does not make it compliant. None may be introduced by
a phase whose authority is limited to Typed Authority Model consumption.

## 17. Compliance requirements

TAMC-REQ-070: Every future consumption implementation SHALL provide
traceable evidence for compliance with:

1. Consumer Classification;
2. Consumer Invariants;
3. Ownership Contract;
4. Authority Contract;
5. Validation Contract;
6. Provenance Contract;
7. Runtime Contract;
8. Lifecycle Contract;
9. Error-Handling Contract;
10. Extensibility Contract;
11. Security Contract;
12. Compatibility Contract; and
13. No-Go Contract.

TAMC-REQ-071: Compliance evidence SHALL identify the applicable TAMC
requirement IDs, inputs, expected output or deterministic failure, provenance
retention, side-effect checks, and negative tests for authority, lifecycle,
and runtime leakage.

TAMC-REQ-072: A future implementation SHALL be non-conformant if any
mandatory evidence is absent, any requirement is weakened locally, or any
Forbidden behavior is reachable.

TAMC-REQ-073: Conformance to TAMC-001 does not itself authorize
implementation. Each implementation still requires an explicit governed
phase with an in-scope task contract.

## 18. Contract verification requirements

TAMC-REQ-074: Independent contract verification SHALL review TAMC-001 v1.0
for consistency, completeness, ambiguity, conflicting requirements,
ownership overlap, authority leakage, lifecycle leakage, runtime leakage,
and provenance loss.

TAMC-REQ-075: Verification SHALL re-derive the exact Allowed, Future, and
Forbidden classifications from the frozen contract; confirm all sixteen
families and every in-scope infrastructure artifact are covered; and
adversarially test the boundaries between reporting and persistence,
validation classes, representation and authority, missing references and
ambient lookup, backward compatibility and unknown-version rejection, and
additive families and explicit opt-in.

TAMC-REQ-076: Contract verification is review only. It SHALL NOT implement a
consumer, modify Stage 3 artifacts, integrate runtime behavior, or change the
Observed / observe / unavailable posture.

## 19. Phase 137B freeze confirmation

Phase 137B freezes consumer obligations, invariants, classifications,
ownership boundaries, authority boundaries, validation boundaries,
provenance obligations, runtime neutrality, lifecycle neutrality,
deterministic error handling, extensibility, security, compatibility,
compliance evidence, and No-Go conditions as TAMC-001 v1.0.

No implementation is authorized by this freeze. No production consumer is
added. No Stage 3 schema, registry, manifest, or typed model is modified.
Runtime remains Observed / observe / unavailable.

## 20. Recommended next phase

**137C — Typed Authority Model Consumption Contract Independent
Verification.**

Phase 137C should independently re-derive and adversarially verify TAMC-001
v1.0 before any implementation work is authorized.
