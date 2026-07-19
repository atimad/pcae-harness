# Typed Authority Model Consumption Read-Only Prototype Implementation

## Implementation identity

**Phase:** 137E  
**Prototype:** TAMP-001 explicit-artifact inspector  
**Governing contract:** TAMC-001 v1.0  
**Status:** prototype-only; no production integration

Phase 137E implements exactly the single consumer selected by TAMP-001: an
explicit-artifact Typed Authority Model record inspector. The implementation
is [typed_authority_inspector.py](../../prototypes/typed_authority_inspector.py),
with isolated evidence in
[test_typed_authority_inspector_137e.py](../../tests/test_typed_authority_inspector_137e.py).
Nothing imports or registers the prototype in a command, report, bootstrap,
runtime, lifecycle, notification, publication, recovery, or authority path.

The prototype remains representation-only. Runtime is unchanged:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

## Architecture and implemented components

The physical implementation is deliberately one module. Its four conceptual
responsibilities match TAMP-001 without creating a generic consumer framework:

| Component | Implementation | Boundary |
|---|---|---|
| Inspection orchestrator | `inspect_explicit_artifact()` | Sequences existing owners and returns one success or failure value; performs no discovery or persistence. |
| Explicit family dispatch | `_MODEL_BY_FAMILY` | Binds the sixteen frozen manifest families to their existing typed-model classes; unknown families fail closed. |
| Provenance assembly | `_provenance_bundle()` and `_collect_named_values()` | Copies complete typed claims and identifies structural provenance fields; performs no enrichment or dereference. |
| Immutable result boundary | `InspectionSuccess`, `InspectionFailure`, `OpaqueJsonValue` | Returns defensively copied nested content and deterministic canonical bytes; exposes no operative status. |

`ExplicitArtifactContext` requires caller-supplied source identity/location,
schema-package identity, package root, manifest path, manifest schema identity,
and TAMC version. No path, family, version, latest artifact, or source identity
is derived from the working directory, environment, Git, wall clock, network,
or mutable PCAE state.

The read-only data flow is:

1. Strictly parse exactly one supplied byte string using the existing
   duplicate-key-rejecting parser.
2. Require explicit source/package/TAMC context.
3. Build the existing offline-only registry from the explicit package root.
4. Verify the frozen manifest through the existing manifest integrity owner.
5. Resolve exactly one manifest family and registry schema identity.
6. Enforce the frozen schema/model versions and identity agreement.
7. Run the existing Draft 2020-12 shape validator.
8. Construct and serialize the exact existing frozen family model.
9. Require lossless typed round-trip equality.
10. Return an immutable inspection observation with full claims, provenance,
    distinct schema/model outcomes, and the unconditional representation-only
    disclosure.

No step follows a record reference, performs semantic/lifecycle/governance
validation, determines authority, or invokes execution.

## Deterministic failure boundary

Failure precedence is frozen as parse, explicit provenance context, registry,
manifest, family/version/identity dispatch, schema validation, model
validation, then lossless provenance assembly. Stable outcomes include:

- `malformed_artifact`
- `required_provenance_failed`
- `registry_failure` and `registry_entry_missing`
- `manifest_failure` and `manifest_entry_missing`
- `unknown_record_family`
- `unsupported_schema_version`
- `unsupported_model_version`
- `family_identity_mismatch`
- `schema_validation_failed`
- `model_validation_failed`

Failures contain normalized messages and declared identity/version facts when
known. They contain no partial success, stack text, retry instruction,
fallback, repair, inferred authority, or recommended action.

## Provenance preservation

Every successful result preserves separately:

- explicit source artifact identity and location;
- explicit schema-package identity;
- SHA-256 of the exact supplied bytes, labeled as derived;
- declared record digest, without replacement by the input digest;
- record family and identity;
- schema identity/version and typed-model contract version;
- selected verified manifest entry and registry resource facts;
- separate schema and model validation observations;
- the complete lossless typed record as namespaced `record_claims`;
- structural references, limitations, uncertainty, opaque/extensions content,
  disclosures, and derivation pointers; and
- the fixed representation-only, lifecycle-authoritative, execution-unavailable
  disclosure.

Nested output is held through the existing immutable `OpaqueJsonValue` owner.
Every `to_dict()` call receives a fresh copy, so a downstream mutation cannot
alter the inspection result.

## TAMC-001 compliance evidence

The table references TAMC-001 rather than redefining it. Requirements 074–076
govern independent contract verification and were completed in Phase 137C;
they are not implementation behavior owned by this phase.

| Contract category | Requirements | Phase 137E evidence |
|---|---:|---|
| Consumer Classification | 001–021 | Exactly one Allowed `inspection` function exists. Static tests prove no production import/registration and no Future or Forbidden surface. |
| Consumer Invariants | 022–032 | Sixteen-family lossless inspection, canonical-byte replay equality, package/input before-after hashes, immutable nested output, and explicit derivation tests. |
| Ownership | 033–034 | Direct calls to strict parser, offline registry, manifest verifier, Draft 2020-12 validator, and frozen `from_dict`/`to_dict`; no schema, validator, registry, manifest, model, lifecycle, or authority rule is copied. |
| Authority | 035–038 | Claims remain under `record_claims`; operative-looking authorization data never changes result class; the neutrality disclosure is unconditional; no operative top-level label exists. |
| Validation | 039–041 | Schema and model outcomes are separate; semantic, lifecycle, and governance fields explicitly say `not_performed`; distinct schema/model failure tests exist. |
| Provenance | 042–045 | Exact input and declared digests remain separate; all identities/versions, full claims, references, limitations, disclosures, and derivation are asserted field-by-field. Invalid explicit provenance fails closed. |
| Runtime | 046–048 | Static import/reachability test excludes runtime/execution/process/network paths. Live pre/post verification confirms Observed / observe / unavailable. |
| Lifecycle | 049–051 | Static import/reachability test excludes task/phase/session/report owners; inspection has no outer mutation callback; lifecycle-looking claims remain claims. Live PCAE state checks are unchanged. |
| Error Handling | 052–055 | Strict malformed/duplicate-key rejection, unknown-family rejection, exact version rejection, schema/model/provenance/registry/manifest failures, normalized messages, and deterministic replay evidence. |
| Extensibility | 056–059 | Exact governed dispatch contains sixteen families; unknown families cannot be dynamically discovered or silently interpreted; existing behavior is independent of filesystem order. |
| Security | 060–064 | Existing recursive immutability, fresh-copy output, package/input non-mutation hashes, offline registry, no secret-bearing underlying exception text, and fail-closed untrusted input tests. |
| Compatibility | 065–067 | TAMC and Stage 3 versions are pinned to `1.0`; unknown schema/model versions fail without nearby-version fallback; no local behavior supersedes TAMC-001. |
| No-Go | 068–069 | AST/import and production-import scans prove no authority resolver/persistence/pointer/activation, runtime adapter, lifecycle mutation, semantic engine, publication/recovery/cutover/quarantine execution, or legacy bridge is reachable. |
| Compliance process | 070–073 | Tests name applicable requirement ranges, inputs and expected outcomes; this document records provenance, side-effect, and leakage evidence; the human-authorized Phase 137E task contract supplies implementation authority. |

This evidence covers all implementation-applicable TAMC requirements 001–073.
Conformance proves only this isolated observation boundary and grants no
production integration authority.

## Limitations and known restrictions

- The prototype is not a supported production API and has no compatibility
  promise beyond TAMC-001/TAMP-001 verification.
- It accepts exactly one in-memory byte string per operation and only explicit
  local Stage 3 package context.
- It does not accept paths as record input, scan a repository, locate a latest
  artifact, cache results, persist output, or render a CLI/report.
- It supports exactly the sixteen TAMC-001 v1.0 families at Stage 3 schema and
  typed-model version `1.0`.
- It validates strict JSON shape and typed-model local invariants only. It does
  not validate record semantics, cross-record consistency, lifecycle,
  governance, authority, freshness, executability, or declared record digest
  correctness.
- References are copied as structural claims and are never dereferenced.
- Manifest/registry/package facts are observations about explicitly supplied
  frozen resources, never authority or publication facts.
- A process importing Python modules may use normal interpreter bytecode-cache
  behavior; the inspection operation itself performs no write. Verification
  runs disable bytecode writes when measuring side effects.

## Future extension boundary

The only extension point is an explicitly governed addition to the family
dispatch binding after a future TAMC revision and matching frozen Stage 3
schema/model/manifest change authorize that family. There is no plugin,
callback, policy, renderer, dynamic-import, discovery, execution, or
persistence hook.

No production use follows automatically. A future production consumer first
requires a separately authorized architecture, contract, implementation, and
independent verification sequence. The next phase is only:

**137F — Typed Authority Model Consumption Prototype Independent Verification**

Phase 137F must independently re-derive the implementation and adversarially
attempt to demonstrate authority, lifecycle, runtime, provenance, mutation,
version, error-order, or import-isolation violations before any broader
consumer implementation is considered.
