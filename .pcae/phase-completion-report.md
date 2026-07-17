# Phase 136AC Complete — Stage 3 Typed Authority Model Authority Core Independent Verification

## Phase identity

- Phase ID: `136AC`
- Status: completed
- Classification: independent verification (Authority Core — `AuthorityEpoch`, `AuthorityState` only; no other record-family model)
- Report completeness: complete

## Scope

Independently re-derive and verify the Phase 136AB Authority Core typed
models (`AuthorityEpoch`, `AuthorityState`) against the frozen executable
schemas directly, without trusting Phase 136AB's prose, tests, fixtures,
helper functions, or field-mapping claims. Bounded repair of reproduced
Blocking defects only. No later record-family model, semantic validator,
repository, persistence, authority resolver, or runtime integration.

## Summary

Independently re-derived both models' field tables directly from
`records/authority_epoch.schema.json`/`records/authority_state.schema.json`
(via `json.load` on the raw schema documents plus
`pcae.schema_runtime.build_offline_registry`/`validate_record_shape` —
shared, non-authority-specific Layer 2 infrastructure, not 136AB test
code), then constructed an entirely new adversarial test module,
`tests/test_cltr_authority_136ac_authority_core_independent.py` (104
independent test functions, several parametrized, all passing, 1 skipped
because `src/pcae/runtime` does not exist in this checkout). No fixture,
helper function, expected-field-set constant, or expected-value literal
was imported from `tests/test_cltr_authority_136ab_authority_core.py`.

Verified independently: exact field/required/optional/nullable sets for
both records against the live schema; strict discriminator/enum/
identifier/digest/reference-family rejection with no coercion;
`predecessor_epoch`/`generation_binding`/`authoritative_generation`/
`uncertainty` absent-vs-null-vs-typed distinctions and every conditional
branch (`activation_state`↔`generation_binding`,
`authority_kind`↔`authoritative_generation`,
`verification_state`↔`uncertainty`); references to never-existing targets
construct successfully with zero filesystem/socket access (instrumented);
exact timestamp wire-string preservation (no `Z`↔`+00:00` normalization,
no clock read); lossless round trip including post-serialization mutation
isolation; recursive immutability at every nesting level; structural
equality (same ID/digest with one differing field, including a bare
timestamp-string difference, compares unequal); zero forbidden operational
method names anywhere in the module (AST-verified) and both model classes
expose only dunder methods plus `from_dict`/`to_dict`;
schema-valid-but-operationally-fabricated records (referencing epochs and
publication-evidence records that have never existed) construct
successfully, confirming zero cross-record semantic validation at this
layer; neither model has a `cas_expectation` field and `hashlib.sha256`
is never invoked during construction/serialization; zero later-group
model classes anywhere in the package (AST-verified) and the 136M scope
guard independently confirmed narrowed to forbid exactly the 14
later-group names, `AuthorityEpoch`/`AuthorityState` correctly absent
from it; zero production runtime imports in either direction (independent
AST import-graph scan); zero side effects (subprocess/socket/env/
write-mode-open all instrumented); fresh wheel/sdist build with isolated
installed-wheel construction and construction outside the repository
checkout.

One NON-BLOCKING finding disclosed, not repaired: **CONFIRMED-136AC-1** —
all four `EnumClass(raw_str)` construction call sites in
`authority_core.py` (`activation_state`, `authority_kind`,
`verification_state`, `compatibility_mode`, and transitively
`authority_role`) let a bare stdlib `ValueError` propagate uncaught on an
unrecognized member, rather than wrapping it in
`TypedModelConstructionError`. The value is still rejected — fail-closed,
no coercion, no silent acceptance — so no Blocking category is triggered;
only the exception type is inconsistent with the module's own documented
error hierarchy. 136AB's own focused test suite already encodes this
behavior as expected (`pytest.raises(ValueError)`, not
`pytest.raises(auth_errors.TypedModelConstructionError)`) rather than
disclosing it — exactly the kind of implementation-derived expectation
this phase was chartered not to trust blindly. No repair was made (bounded
repair is authorized only for reproduced Blocking defects).

Fresh regression evidence: the new 104-test suite plus fresh reruns of
`test_cltr_authority_136ab_authority_core.py` +
`test_cltr_authority_136aa_shared_core_independent.py` +
`test_cltr_authority_136z_shared_core.py` — 514 passed together (excluding
the new suite's own separate 104/1-skip run). Bounded
Authority-Core-adjacent sweep (`cltr_authority` + `cltr_cutover_136*` +
`canonicalization` + `digest` + `models` + `validation` +
`schema_runtime` + `runtime_registry` + `runtime_enforcement_no_go_
registry_contract` + `runtime_service_registry_architecture`): 3220
passed, 9 skipped, 1 failed — the 1 failure is
`test_136u_no_runtime_code_references_group10_families_outside_schema_
resources`, identical to the 136U scope-guard gap Phase 136AA's own
independent verification report already disclosed (its Sec.9), caused by
`enums.py` (introduced in Phase 136Z, unchanged by 136AB or this phase)
containing `RecordFamily` enum member string values that trip a
`git grep`-based guard predating that enum. `test_cltr_135o_integration.py`
+ `test_cltr_migration_135p_verification.py`: 21 passed, 8 failed —
identical to the pre-existing, previously disclosed cluster, all in code
paths unrelated to `pcae.cltr.authority`. Fast Green: 4391 passed
(unchanged baseline). Zero new failures anywhere.

No production schema was changed. No new production dependency was
introduced. No record-family model beyond the existing two was
implemented; no semantic validator, repository, persistence, or authority
resolver exists. No production runtime module imports
`pcae.cltr.authority`. Legacy lifecycle remains the sole production
authority; CLTR remains derivative; runtime remains Observed / observe /
execution unavailable.

Verdict: **AUTHORITY CORE VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR
REQUEST AND READINESS MODEL IMPLEMENTATION**.

## Findings

- CONFIRMED-136AC-1 (CONFIRMED, NON-BLOCKING, not repaired this phase):
  enum-field construction failures across both models raise bare
  `ValueError`, not a `TypedModelError` subclass.
- 136AA-3 / disclosed-136U (inherited, CONFIRMED, unrelated, not this
  phase's scope to repair): pre-existing 136U scope guard still
  incorrectly flags `enums.py`'s frozen `RecordFamily` enum members.
- 136AA-4 (inherited, CONFIRMED, unrelated): the 8 pre-existing
  `test_cltr_135o_integration.py`/`test_cltr_migration_135p_verification.py`
  failures, unrelated to `cltr.authority`.

No Blocking finding was identified.

## Recommended next phase

**136AD — Stage 3 Typed Authority Model Request and Readiness
Implementation** (`CutoverRequest`, `ReadinessPackage` only). This phase
does not begin 136AD.

## No-Go confirmation

No `CutoverRequest`, `ReadinessPackage`, `HumanAuthorization`,
`CutoverCandidate`, `Certification`, `PublicationAttempt`,
`PublicationEvidence`, `ConcurrencyConflict`, `RecoveryJournalEntry`,
`NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
`FinalizationReceiptAuthorityBinding`, `CompatibilityState`, or
`QuarantineRecord` was implemented; no semantic validator, cross-record
repository, persistence, authority resolver, compatibility resolver,
quarantine coordinator, publication coordinator, recovery coordinator,
lifecycle integration, execution capability, authority activation, or
legacy demotion/retirement logic was implemented. Runtime remains
Observed / observe / unavailable; legacy lifecycle remains sole
production authority; CLTR remains derivative.

## Telegram / notification evidence

- Dispatch attempted: yes (`pcae phase-report create`, this phase's
  finalization).
- Provider success evidence persisted: yes — CLI reported
  `[telegram]: OK — Telegram: summary sent, document sent`.
- Failure evidence persisted: not applicable (dispatch succeeded).
- Reason not attempted: not applicable.
- `PCAE_NOTIFY_ENABLED` presence was verified (sourced from
  `~/.config/pcae/telegram.env`); its value was not disclosed or logged.
- No secret (token/chat ID value) was printed at any point in this
  phase's session.

Full detail:
`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_AUTHORITY_CORE_INDEPENDENT_VERIFICATION.md`.
