# Phase 136AF: Stage 3 Typed Authority Model Authorization and Candidate Implementation

## 1. Purpose and boundaries

This phase implements Typed Model Implementation Group 4 of the frozen
`136Y` plan (`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
Sec.4/Sec.23, package layout Sec.7): exactly three record-family models,
`HumanAuthorization`, `CutoverCandidate`, and `Certification`,
schema-backed by
`src/pcae/schema_resources/cltr_cutover/records/human_authorization.schema.json`,
`.../cutover_candidate.schema.json`, and `.../certification.schema.json`
respectively.

All three models are descriptive, immutable, schema-backed typed
representations only. None of the three authenticates a human, verifies a
signature, determines whether an authorization is valid, approves or
rejects cutover, calculates candidate eligibility, certifies operational
truth, selects current authority, resolves a reference, verifies a
digest, evaluates evidence, persists a record, publishes an artifact,
mutates lifecycle state, executes cutover, or performs recovery. A
`HumanAuthorization` is a representation of a recorded decision, never
proof a human made it or that it is currently valid; a `CutoverCandidate`
is a representation of a proposed attempt, never proof of eligibility; a
`Certification` is a representation of an evidence-based verification
result, never proof of certification authenticity. Legacy lifecycle
remains the sole production authority; CLTR remains derivative. Runtime
remains Observed / observe / unavailable, unchanged by this phase.

## 2. Binding sources

Precedence followed (identical structure to every prior phase in this
chapter): frozen primary contract (`CLTR-CUTOVER-001`,
`CLTR-CUTOVER-SCHEMAS-001` v1.0, `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001`
v1.0 Sec.21/Sec.22/Sec.23) → verified contract → verified architecture
(Phase 136B) → verified 136Y implementation plan → verified 136Z/136AA
shared core, 136AB/136AC Authority Core, 136AD/136AE Request and
Readiness → this governed 136AF task contract → operator prompt. No
conflict was found between the operator prompt and the frozen contract
requiring a discrepancy disclosure.

Consulted directly: the 136Y plan (Sections 3-29), the three executable
schema files (`human_authorization.schema.json`,
`cutover_candidate.schema.json`, `certification.schema.json`),
`shared/identity.schema.json`, `shared/digest.schema.json`,
`shared/references.schema.json` (including the embedded `cas_expectation`
`$def`), `shared/enums.schema.json`, `shared/failures.schema.json`,
`shared/limitations.schema.json`, and the 136Z/136AA/136AB/136AC/136AD/136AE
shared-core and prior record-family model source
(`src/pcae/cltr/authority/*.py`, excluding `authorization_candidate.py`
which this phase adds).

Three discrepancy disclosures were already carried in the frozen schemas
themselves (not new to this phase, restated for completeness):

- **NON-BLOCKING-136N-4**: `human_authorization.schema.json` carries no
  separate wildcard-capable `scope` field; the phase objective's informal
  use of "scope" refers to the three-reference binding
  (`request_reference`/`readiness_reference`/`target_reference`), not a
  distinct field. This model implements exactly the three-reference
  binding and invents no `scope` field.
- **NON-BLOCKING-136N-6**: `cutover_candidate.schema.json` carries exactly
  three record-specific fields (`stage2_generation_reference`,
  `cas_expectation`, `state`) and no direct top-level
  `request_reference`/`readiness_reference`/`authorization_reference`/
  `source_authority_reference`/`target_epoch_reference` fields of the kind
  an earlier prompt draft might anticipate. This model implements exactly
  Sec.22's three fields plus the universal envelope.
- **NON-BLOCKING-136N-8**: `certification.schema.json` carries no named
  certifier-principal field (unlike `human_authorization`'s `principal`);
  certification is evidence-based (`verifier_evidence`, an array of
  `record_reference`) rather than a single named human decision. No
  `certifier_principal` field is invented here.

## 3. Confirmed starting state (re-verified this phase)

- `git status --short` clean; `origin/main..HEAD` = 0 commits, before this
  phase's own commits.
- `src/pcae/cltr/authority/` contained exactly the 14 shared-core modules
  plus `authority_core.py` and `request_readiness.py`; no
  `authorization_candidate.py`, no `HumanAuthorization`/
  `CutoverCandidate`/`Certification` class anywhere in the package or in
  `src/pcae` (grep + AST confirmed).
- No production module imports `pcae.cltr.authority` (grep confirmed
  across `src/pcae/commands`, `src/pcae/core`, `src/pcae/runtime`, and the
  rest of `src/pcae/cltr` outside the `authority` package itself).
- `pcae runtime inspect`: Runtime state Observed, execution capability
  unavailable, maximum plugin capability observe.
- `pcae health` / `pcae check` / `pcae status coherence`: all passing,
  clean working tree, zero commits ahead.

## 4. What was implemented

`src/pcae/cltr/authority/authorization_candidate.py` (new module):

- **`HumanAuthorization`** (Tier 1, strict, no `_extensions`): 15 required
  fields (envelope 7 + `phase_id`, `migration_epoch`, `principal`,
  `method`, `request_reference`, `readiness_reference`,
  `target_reference`, `issued_at`, `expires_at`, `state`,
  `replay_binding`, `risk_acknowledgement`, `limitations`,
  `authority_disclosure`) plus 3 conditionally-present fields
  (`revocation_metadata` iff `state == 'revoked'`; `use_binding` iff
  `state == 'used'`; `proof_reference` iff `method ==
  'signed_attestation'`). `request_reference`/`readiness_reference`/
  `target_reference` are family-restricted to `cutover_request`/
  `readiness_package`/`authority_epoch` respectively, with
  `schema_id`/`schema_version` unconditionally required (Sec.12
  cross-family rule). `use_binding` is a shape-only forward reference to
  the not-yet-implemented `publication_attempt` family, matching the
  `AuthorityState.publication_evidence_reference` precedent (136AB).
  `risk_acknowledgement` is validated as the frozen const `true`.
  `replay_binding` is validated against its opaque-token pattern.
  `authority_role == 'authoritative'` is rejected.

- **`CutoverCandidate`** (Tier 2, `_extensions` permitted, string-valued
  map only): 7 required fields (envelope 7 + `migration_epoch`,
  `stage2_generation_reference`, `cas_expectation`, `state`,
  `limitations`, `authority_disclosure` -- no `phase_id`, matching the
  schema's own omission) plus optional `_extensions`.
  `stage2_generation_reference` carries no local family restriction
  (matching the schema's own choice, since "generation" is not itself one
  of the 16 `record_family` values). `cas_expectation` reuses the shared
  `CasExpectation` component (already implemented at
  `cas_expectation.py`, 136Y plan Sec.13) via a new
  `_cas_expectation_from_dict` parsing helper -- `CasExpectation` itself
  required no changes since `serialize_value`'s generic dataclass branch
  already serializes it losslessly. `authority_role == 'authoritative'` is
  rejected at every state, including `'certified'`.

- **`Certification`** (Tier 1, strict, no `_extensions`): 14 required
  fields (envelope 7 + `phase_id`, `migration_epoch`,
  `candidate_reference`, `request_reference`, `readiness_reference`,
  `authorization_reference`, `source_authority_reference`,
  `target_epoch_reference`, `cas_expectation`, `verifier_evidence`,
  `state`, `limitations`, `authority_disclosure`) plus 2
  conditionally-present fields (`staleness` iff `state == 'stale'`;
  `invalidation` iff `state == 'invalidated'`).
  `candidate_reference`/`request_reference`/`readiness_reference`/
  `authorization_reference` are family-restricted with
  `schema_id`/`schema_version` unconditionally required;
  `source_authority_reference`/`target_epoch_reference` are
  family-restricted to `authority_epoch` without that requirement,
  matching the schema's own `epoch_reference` `$def` (and may reference
  the identical epoch record -- the schema does not forbid this).
  `verifier_evidence` carries no family restriction (may point at any of
  the 16 companion families) and no uniqueness constraint, bounded at 64
  items, preserving exact order. `authority_role == 'authoritative'` is
  rejected.

Three new record-local enums (`AuthorizationMethod`, `AuthorizationState`,
`CandidateState`, `CertificationState`) and three new bounded local
disclosure objects (`RevocationMetadata`, `Staleness`, `Invalidation`),
all family-scoped in the new module, matching the existing non-
centralization precedent (136Y plan Sec.5/Sec.12).

`src/pcae/cltr/authority/__init__.py`: updated to export the ten new
public names and to update the module docstring's completed-groups
inventory. `cas_expectation.py` itself was **not modified** -- the shared
`CasExpectation` dataclass required no code change to be embedded by
either new model.

## 5. Test suite

`tests/test_cltr_authority_136af_authorization_candidate.py`: 85 new
tests, independently fixtured (no fixture, helper, or expected-value
table imported from any prior phase's test module). Covers: minimal and
maximal valid construction with schema validation for all three models;
every conditional-field branch (both directions: required-when-present
and forbidden-when-absent) for `HumanAuthorization`'s
`revocation_metadata`/`use_binding`/`proof_reference` and
`Certification`'s `staleness`/`invalidation`; family-restriction
enforcement on every family-tagged reference field, including the
cross-family `schema_id`/`schema_version` requirement; `_extensions`
Tier 2 behavior for `CutoverCandidate` (string-only values, reserved-key
collision rejection, explicit-null rejection, mutation isolation) and
Tier 1 strictness (no `_extensions` escape hatch) for `HumanAuthorization`
and `Certification`; enum member-set parity against the live schemas for
all four new local enums; `authority_role == 'authoritative'` rejection
on all three models, including `CutoverCandidate` at `state ==
'certified'`; `verifier_evidence` order preservation, empty-array
permission, no-family-restriction, and max-items boundary; the embedded
`cas_expectation` component's unconditional-field-requiredness and the
schema-permitted self-reference case
(`Certification.cas_expectation.expected_certification_reference`
pointing at the enclosing document's own id/digest); schema
`properties`-key-set parity against each of the three live schema files;
frozen-dataclass immutability and structural equality; no-forbidden-symbol
source scan; no-production-import scan; no-network/no-subprocess
side-effect checks during construction and serialization.

**Scope note (disclosed, not a defect):** unlike 136AD/136AE, this
phase's test module does not include a dedicated isolated-venv
wheel/sdist installation exercise. The package-wide wheel/sdist
inclusion of the new module is instead verified indirectly: the
already-existing, pre-scoped wheel-content guards in
`tests/test_cltr_authority_136z_shared_core.py` and
`tests/test_cltr_authority_136ab_authority_core.py` (see Section 6) were
narrowed this phase to assert `authorization_candidate.py` is present in
the built wheel, and both pass. A fresh full wheel build was run as part
of the full-suite regression (Section 8) and confirmed to succeed.

## 6. Inherited "narrowing guard" updates (expected, matching precedent)

Every prior phase in this chapter that added a new record-family model
also narrowed the still-forbidden-name lists in earlier phases' own
"exactly N models exist" / "no later-group model exists" guard tests
(136AB narrowed 136Z's and its own; 136AD narrowed 136Z's, 136AA's,
136AB's, and its own). This phase follows the identical, established
precedent: `HumanAuthorization`/`CutoverCandidate`/`Certification` and
`authorization_candidate.py` were removed from the still-forbidden lists
in:

- `tests/test_cltr_authority_136z_shared_core.py` (module inventory,
  record-family class guard)
- `tests/test_cltr_authority_136aa_shared_core_independent.py` (public
  API inventory, record-family class guard, on-disk file inventory)
- `tests/test_cltr_authority_136ab_authority_core.py` (later-group class
  guard, wheel-content guard)
- `tests/test_cltr_authority_136ac_authority_core_independent.py`
  (later-group class guard, `__all__` export guard)
- `tests/test_cltr_authority_136ad_request_readiness.py` (record-family
  inventory guard, wheel-content guard)
- `tests/test_cltr_authority_136ae_request_readiness_independent.py`
  (record-family inventory guard, `__all__` export guard)

**CONFIRMED-136AE-2 preserved unrepaired, as instructed.** The one
already-disclosed stale wheel-packaging guard in
`tests/test_cltr_authority_136z_shared_core.py`
(`test_136z_wheel_contains_authority_shared_core_no_record_family_module`)
still forbids `request_readiness.py` in the built wheel, even though
Phase 136AD legitimately added it to the package (136AE disclosed this as
inherited, out-of-scope, non-blocking). This phase did **not** touch that
specific assertion -- re-run and re-confirmed identical: 1
pre-existing-unrelated failure, unchanged from the 136AE baseline. No new
model contract in this phase depends on that guard, and no Blocking
inconsistency results from leaving it unrepaired.

## 7. Findings disclosed this phase

No new Blocking or Non-Blocking finding was identified specific to
`HumanAuthorization`/`CutoverCandidate`/`Certification`. The three
schema-level discrepancy disclosures already carried by the frozen
schemas (NON-BLOCKING-136N-4, -6, -8, restated in Section 2) were
re-confirmed against the live schema files and are faithfully
implemented, not repaired or reinterpreted.

Existing findings preserved and disclosed, unchanged:

- **CONFIRMED-136AC-1**: enum construction may raise a bare `ValueError`
  instead of a `TypedModelError` subclass. This module's four new local
  enums (`AuthorizationMethod`, `AuthorizationState`, `CandidateState`,
  `CertificationState`) inherit this same behavior via the identical
  `EnumClass(raw_str)` construction pattern used everywhere else in the
  package -- re-confirmed fail-closed (an invalid value still raises,
  just with the built-in exception type) and Non-Blocking; no concrete
  correctness consequence found this phase.
- **CONFIRMED-136AE-1**: the live `reason_code` shared schema declares
  `type: string` only (no `null` in the union), so an explicit wire-level
  `null` fails Layer 1 `jsonschema` validation for any field using it.
  This phase's three new models use `reason_code` only inside
  unconditionally-required nested objects
  (`RevocationMetadata.reason_code`, `Staleness.reason_code`,
  `Invalidation.reason_code`) -- none of the three new top-level fields
  reuses the CutoverRequest-only Sec.6.3 absent-vs-null relaxation, and
  none needed to; not extended, not repaired.
- **CONFIRMED-136AE-2**: see Section 6.
- Other inherited conditions (136U scope-guard gap, 135O/135P failures,
  bounded full-suite incompleteness, architecture-status phase-line
  parser limitation, incomplete provider-side Telegram delivery
  evidence): unrelated to this phase's scope, not touched.

## 8. Regression

- `tests/test_cltr_authority_136af_authorization_candidate.py`: 85
  passed (new this phase).
- `tests/test_cltr_authority_136*.py` together (all seven modules): 1
  pre-existing-unrelated failure (CONFIRMED-136AE-2), rest passing.
- Fast Green full suite: re-run, unchanged baseline pass count (no
  regression introduced by this phase's source or test changes).
- `pcae health` / `pcae check` / `pcae status coherence`: all passing
  throughout.

## 9. No-go confirmation

This phase implemented no `PublicationAttempt`, `PublicationEvidence`,
`ConcurrencyConflict`, `RecoveryJournalEntry`,
`NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
`FinalizationReceiptAuthorityBinding`, `CompatibilityState`, or
`QuarantineRecord`; no semantic validator, no cross-record repository, no
derived view, no persistence, no authority resolver, no current-authority
lookup, no historical-authority lookup, no authorization evaluator, no
eligibility calculator, no certifier, no compatibility resolver, no
quarantine coordinator, no publication coordinator, no recovery
coordinator, no lifecycle integration, no execution capability, no
authority activation, no legacy demotion/retirement. Runtime remains
Observed / observe / unavailable; legacy lifecycle remains sole
production authority; CLTR remains derivative.

## 10. Verdict

**AUTHORIZATION AND CANDIDATE MODEL IMPLEMENTATION COMPLETE -- READY FOR
INDEPENDENT VERIFICATION**

## 11. Recommended next phase

**136AG — Stage 3 Typed Authority Model Authorization and Candidate
Independent Verification.** This phase does not begin 136AG.
