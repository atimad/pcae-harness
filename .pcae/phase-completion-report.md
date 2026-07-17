# Phase 136AF Complete — Stage 3 Typed Authority Model Authorization and Candidate Implementation

## Phase identity

- Phase ID: `136AF`
- Status: completed
- Classification: implementation (Typed Model Implementation Group 4 — `HumanAuthorization`, `CutoverCandidate`, `Certification` only; no other record-family model)
- Report completeness: complete

## Scope

Implement Typed Model Implementation Group 4 of the frozen `136Y` plan:
exactly three record-family models, `HumanAuthorization`,
`CutoverCandidate`, and `Certification`, as frozen, immutable,
schema-backed, lossless typed representations only. No authentication,
signature verification, authorization-validity determination, cutover
approval/rejection, candidate-eligibility calculation, certification of
operational truth, authority selection, reference resolution, digest
verification, evidence evaluation, persistence, publication, lifecycle
mutation, cutover execution, or recovery permitted.

## Summary

New module `src/pcae/cltr/authority/authorization_candidate.py`
implements three frozen, recursively-immutable dataclasses, each with an
independently re-derived field table from the live executable schemas
(`records/human_authorization.schema.json`,
`records/cutover_candidate.schema.json`,
`records/certification.schema.json`).

`HumanAuthorization` (Tier 1 strict, no `_extensions`) enforces its three
conditional-field pairs (`revocation_metadata` iff `state == "revoked"`;
`use_binding` iff `state == "used"`; `proof_reference` iff `method ==
"signed_attestation"`) and the cross-family `schema_id`/`schema_version`
requirement on its three family-tagged references
(`request_reference`/`readiness_reference`/`target_reference`, restricted
to `cutover_request`/`readiness_package`/`authority_epoch`
respectively). `use_binding` is a shape-only forward reference to the
not-yet-implemented `publication_attempt` family, matching the
`AuthorityState.publication_evidence_reference` precedent (136AB).
`risk_acknowledgement` is validated as the frozen const `true`.
`authority_role == "authoritative"` is rejected.

`CutoverCandidate` (Tier 2, `_extensions` permitted, string-valued map
only) embeds the already-implemented shared `CasExpectation` component
unchanged — `cas_expectation.py` required no code change, since
`serialize_value`'s generic dataclass branch already serializes it
losslessly; only a new `_cas_expectation_from_dict` parsing helper was
added. Carries no `phase_id` field, matching the schema's own omission.
`authority_role == "authoritative"` is rejected at every state, including
`"certified"`.

`Certification` (Tier 1 strict, no `_extensions`) carries no
certifier-principal field by design — certification is evidence-based
(`verifier_evidence`, an unrestricted-family array of `record_reference`,
bounded at 64 items, order-preserving, no uniqueness constraint) rather
than a single named human decision. Enforces its `staleness`/
`invalidation` conditional pair. `source_authority_reference`/
`target_epoch_reference` are family-restricted to `authority_epoch`
without the cross-family `schema_id` requirement, matching the schema's
own `epoch_reference` `$def`, and may reference the identical epoch
record (the schema does not forbid this). `authority_role ==
"authoritative"` is rejected.

New standalone test module
`tests/test_cltr_authority_136af_authorization_candidate.py` (85 tests,
all passing), independently fixtured — no fixture, helper, or
expected-value table imported from any prior phase's test module.
Covers construction/round-trip, every conditional-field branch in both
directions, family-restriction enforcement, `_extensions` Tier 1/Tier 2
behavior, enum member-set parity against the live schemas, schema
`properties`-key-set parity, frozen-dataclass immutability, structural
equality, no-forbidden-symbol source scan, no-production-import scan,
and no-network/no-subprocess side-effect checks.

Following the established narrowing precedent (136AB narrowed 136Z's own
guard when it added `AuthorityEpoch`/`AuthorityState`; 136AD narrowed
136Z/136AA/136AB/136AC's guards when it added
`CutoverRequest`/`ReadinessPackage`), this phase narrowed the
still-forbidden-name lists in six earlier test modules (`136z`, `136aa`,
`136ab`, `136ac`, `136ad`, `136ae`) to authorize
`HumanAuthorization`/`CutoverCandidate`/`Certification` and the new
`authorization_candidate.py` module; every other later-group name/module
in each guard remains forbidden, re-confirmed passing.

**CONFIRMED-136AE-2 preserved unrepaired, as instructed.** The one
already-disclosed stale wheel-packaging guard in
`tests/test_cltr_authority_136z_shared_core.py`
(`test_136z_wheel_contains_authority_shared_core_no_record_family_module`)
still forbids `request_readiness.py` in the built wheel, though Phase
136AD legitimately added it to the package. Re-run and re-confirmed
identical — this phase's own changes did not touch that assertion.

Regression: 1 pre-existing-unrelated failure (CONFIRMED-136AE-2) across
all seven `test_cltr_authority_136*` modules together, rest passing;
Fast Green 4391 passed (unchanged baseline). Full detail in
`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_AUTHORIZATION_CANDIDATE_IMPLEMENTATION.md`.

## No-Go confirmations

- No later-group record-family model (`PublicationAttempt`,
  `PublicationEvidence`, `ConcurrencyConflict`, `RecoveryJournalEntry`,
  `NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
  `FinalizationReceiptAuthorityBinding`, `CompatibilityState`,
  `QuarantineRecord`) was implemented.
- No semantic validator, cross-record repository, persistence, or
  derived view was implemented.
- No authority resolver, current-authority lookup, or
  historical-authority lookup was implemented.
- No authorization evaluator or eligibility calculator was implemented.
- No cryptographic verification, runtime execution, or lifecycle
  mutation occurred.
- No authority epoch changed; no legacy authority was demoted or
  retired; no CLTR authority was created.
- No new production dependency was introduced.
- No production runtime module imports `pcae.cltr.authority`.
- No network, filesystem-write, or subprocess side effect occurs during
  construction or serialization of any of the three models.
- No execution capability was introduced.
- No production schema was changed by this phase.
- No Blocking finding was identified; CONFIRMED-136AC-1 and
  CONFIRMED-136AE-1/-2 are disclosed as inherited Non-Blocking and were
  not repaired.

## Verdict

**AUTHORIZATION AND CANDIDATE MODEL IMPLEMENTATION COMPLETE — READY FOR
INDEPENDENT VERIFICATION**

Recommended next phase: 136AG — Stage 3 Typed Authority Model
Authorization and Candidate Independent Verification.

Runtime remains Observed / observe / execution unavailable. Legacy
lifecycle remains the sole production authority; CLTR remains
derivative.
