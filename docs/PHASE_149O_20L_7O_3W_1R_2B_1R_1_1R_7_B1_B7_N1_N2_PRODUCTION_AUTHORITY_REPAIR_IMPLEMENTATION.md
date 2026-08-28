# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.7 — B1/B7/N1/N2 Production Authority Repair Implementation

Status: **IMPLEMENTED — INDEPENDENT VERIFICATION PENDING — REAL AUTHORITY
STILL UNAVAILABLE.** This phase implements only the structural production
authority repair frozen by `.1R.6`. It does not implement Gate-5/Gate-9
coordinator wiring, Permission Broker policy integration, real FIDO2, a
protected approval UI, runtime capability, or execution.

## 1. Phase identity and entry state

- Phase ID: `149O.20L.7O.3W.1R.2B.1R.1.1R.7`.
- Title: B1/B7/N1/N2 Production Authority Repair Implementation.
- Human authorization: explicit authorization for the primary operator to
  implement, validate, commit, finalize, and push this phase only.
- Phase-entry commit: `b85e903c62f386f3c5a45747ded5ff7682b77267`.
- Planning baseline: Phase
  `149O.20L.7O.3W.1R.2B.1R.1.1R.6`, Option A — structural repair with a
  hard deterministic-NON-REAL rejection boundary.
- Entry Git state: clean, `main...origin/main`, `origin/main..HEAD = 0`.
- Entry runtime state: `not_implemented / Observed / observe / unavailable`,
  zero runtime plugins and zero runtime capabilities.

The `.1R.6` architecture was implementable without contradiction. No STOP
condition was encountered and no substitute architecture was selected.

## 2. Primary sources and contracts inspected

The implementation was reconciled against the full `.1R.6` planning report;
the `.1R.5`, `.1R.5.2`, and `.1R.5.2.1` verifier implementation/repair/
independent-verification reports; the `.3.2.2.1` HPAC foundation verification;
the original B1/B7/N1/N2 finding material; the current approval, presentation,
proof, lifecycle, approval-store, consumption-store, authority, dispatch, PB,
and verifier production modules; and these active contracts:

- RIHAC-001 v2.0;
- RIASC-001 v3.0;
- HPAC-001 v2.0;
- PBRD-001 v2.0;
- RDGO-001 v3.0;
- RPAC-001 v1.0;
- PBPA-001 / `POL-005`.

No contract was modified. The existing `runtime_authority.py` persisted model
continues to encode the older frozen RIASC-001 v1.0 envelope because both the
contract files and canonical approval-store structure were explicitly outside
this phase's modification matrix. That legacy envelope cannot yield production
authority today: the production boundary now requires current HPAC provenance
and hard-rejects the only implemented NON-REAL mechanism. A future schema/store
migration is separate work and is not silently claimed here.

## 3. Production-file matrix

Exactly three production files changed relative to the fixed entry SHA:

| File | Mapping | Result |
|---|---|---|
| `src/pcae/core/runtime_authority.py` | B1, N1, N2 | Exact-object/content-bound projection provenance; canonical approval ID/store resolution; freshly reverified principal-derived provenance; NON-REAL hard stop. |
| `src/pcae/core/runtime_dispatch_permission.py` | B7 and B1 consumption currentness | Durable dispatch-identity registry reread at request construction; authority projection revalidation before the existing structural PB request projection. |
| `src/pcae/core/hpac_verifier.py` | F2 / HPAC-REQ-054 Step 4 prerequisite | Independent exact `Challenge` digest recomputation and a reusable fresh canonical-store re-verification boundary. |

The approval store, Gate-9 consumption module, PB foundation/POL-005, contracts,
provider adapters, runtime coordinator, UI, and authentication mechanisms are
byte-untouched by this implementation.

## 4. B1 repair — non-transferable authority projection

Before this phase, `ValidatedAuthorityProjection` carried one module singleton
seal. `dataclasses.replace()` could copy that seal while changing authority
fields, so possession of a copied object transferred trust.

After this phase:

1. projections are identity-keyed (`eq=False`) and registered only by a
   successful production validator return path;
2. the registered revalidation context binds the exact canonical approval
   store, verifier-authenticated principal, invocation context, and consumption
   lookup;
3. every authority field, including principal/proof/mechanism/assurance and
   invocation identity, participates in a recomputed content-binding digest;
4. a consumer requires both exact-object registry provenance and an intact
   digest; and
5. PB request projection freshly reruns canonical approval, HPAC, expiry, and
   consumption validation at the supplied current time before using the
   projection.

A shallow copy, `dataclasses.replace`, manually reconstructed object, or
same-object field mutation is not registered/intact authority. A projection
also cannot be transferred to another invocation because its invocation and
subject/scope binding are checked independently. This is not a bearer token
and does not use `AuthenticatedHumanPrincipal` as a transferable seal.

Because no PRODUCTION HPAC mechanism exists, production cannot currently emit
a positive projection. The B1 unit tests use tightly scoped same-process test
scaffolding to exercise identity/content checks only; that scaffolding is not
imported by production and never asserts deterministic authentication is real.

Disposition:

```text
B1: REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED
```

## 5. B7 repair — dispatch-time canonical identity reread

Before this phase, request construction checked a public-field digest but did
not reread the durable `RuntimeDispatchIdentityTracker` records. A generated
identity could therefore be reused after its canonical registry state changed.

After this phase, `RuntimeDispatchIdentity` retains its exact tracker and the
request builder calls `RuntimeDispatchIdentityTracker.revalidate()` at the
dispatch-request construction choke point. Revalidation:

- traverses only existing trusted, non-symlinked directories and creates
  nothing;
- rereads the invocation, idempotency, and attempt records;
- requires ordinary one-link regular files and no symlink following;
- requires each decoded record to equal the exact closed expected dictionary;
- binds the identity to the same tracker object and its original registration
  digest; and
- rejects missing, corrupt, linked, substituted, extended, or changed state.

This remains Gate-2 identity registry currentness, not the future Gate-9
`dispatch_attempted` transaction. It performs no consumption and no effect.

Disposition:

```text
B7: REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED
```

## 6. N1 repair — canonical approval ID resolution

Before this phase, `validate_approval` accepted a caller-created
`RuntimeInvocationApproval` if its shape, constants, and digest passed.

After this phase, the authority path accepts an opaque valid approval ID and
requires the exact existing `RuntimeInvocationApprovalStore`. It loads the
record afresh, requires lookup identity equality, then performs the ordered
RIHAC structural, binding, freshness, expiry, consumption, and HPAC checks.
Arbitrary paths, malformed IDs, duck-typed/fake stores, copied JSON, recomputed
digests, and caller-created approval objects cannot establish authority.

The legacy positional object form remains only as a diagnostic tripwire for
old callers: it can return earlier fail-closed schema/binding diagnostics, but
it unconditionally returns
`noncanonical_approval_reference:caller_supplied_object` before HPAC trust or
projection construction. Validation rereads but does not mutate the store.

Disposition:

```text
N1: REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED
```

## 7. N2 repair — verifier-derived human provenance

Before this phase, production approval creation accepted caller-authored
`approver_id` and `identity_evidence_kind` strings.

After this phase, those keywords are rejecting compatibility tripwires. The
production creator requires an exact object registered by
`verify_human_authentication`, freshly reruns the complete verifier against its
retained canonical stores and exact challenge, checks the exact invocation and
approval bindings, derives `approver_id` from `principal.principal_id`, and
derives the approval identity from `principal.approval_id`. Type, field
equality, copied slots, plausible strings, and a serialized reconstruction do
not establish verifier provenance.

The same fresh verifier-owned provenance check runs during canonical approval
validation. Authentication and approval remain separate: a principal result
does not itself create an approval; a canonical approval record bound to the
same invocation must also exist.

Disposition:

```text
N2: REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED
```

## 8. Deterministic NON-REAL hard rejection

The Option-A hard stop is owned by `runtime_authority.py` at both production
authority transitions:

- `create_runtime_invocation_approval` rejects any freshly verified principal
  whose assurance is not `HPACAuthorityClass.PRODUCTION`;
- `validate_approval` rejects the same condition before emitting a projection.

The deterministic mechanism continues to verify principal, credential, proof,
presentation, invocation, UP, UV, lifecycle, and provenance bindings. Even
with all those facts valid, its `FIXTURE_NON_REAL` assurance cannot create or
validate production approval authority. The test-only approval constructor is
in `tests/_rdw3w_helpers.py`, is explicitly named test-only, bypasses no
production store or authority boundary, and is forbidden from production
imports by AST regression tests.

Required result: **PASS — deterministic NON-REAL is recognized as verified
test evidence and hard-rejected as real production human authority.**

## 9. Current-state revalidation and restart semantics

`AuthenticatedHumanPrincipal` registration now retains a private verification
context: canonical principal registry, presentation/descriptor/proof/lifecycle
stores, exact challenge and proof/approval IDs, writer capability, verifier
version, and age bound. `reverify_authenticated_principal` reruns the complete
ordered verifier and requires the refreshed binding to equal the consumed
principal's principal, credential, mechanism, approval, invocation, proof, and
presentation IDs.

This detects between-authentication changes to:

- principal status;
- credential status;
- proof/challenge freshness;
- presentation content/current provenance;
- lifecycle state and binding;
- approval expiry/current store content;
- invocation identity;
- consumption state; and
- assurance/mechanism eligibility.

Temporary refreshed evidence is removed from the strong-reference registries
after comparison, avoiding registry growth while preserving the original
exact authority object.

The registry remains deliberately process-local and is not reconstructed from
serialized fields. A restart loses provenance; persisted approval/proof fields
alone cannot recreate it, and re-authentication is required. This preserves the
`.1R.6` restart model and introduces no restart-surviving fake authority.

## 10. HPAC-REQ-054 Step 4 and F2/F3/F4/F7

F2 / Step 4 became a production-consumption prerequisite in `.1R.6` and is
implemented here. `verify_human_authentication` now requires the exact
ephemeral `Challenge`, independently recomputes its canonical digest from the
complete fixed field set, and compares it with the challenge, proof,
principal/credential, approval-subject, and presentation bindings before
presentation and assertion trust are emitted. Tests reject both a changed
challenge with an unrecomputed digest and a self-consistent recomputed
challenge substituted against the canonical proof.

The literal HPAC-REQ-054 order is preserved: Step 3 mechanism eligibility;
Step 4 challenge recomputation; Step 5 canonical presentation; Step 6 assertion
material; Step 7 UP+UV; Step 8 chronological freshness; Step 9 lifecycle; then
result construction.

- F2: **REPAIRED — independent verification pending; not self-closed.**
- F3: unchanged/deferred planning-document “eight-step” label debt.
- F4: unchanged/deferred cosmetic historical test-name overclaim.
- F7: unchanged non-blocking trust-model boundary. Registry provenance resists
  caller-supplied objects/data, not arbitrary code already able to mutate
  trusted Python process memory. This phase does not claim process isolation.

## 11. Gate, PB, runtime, FIDO2, and UI boundaries

- Gate 5: no RDGO coordinator created or wired. The repair provides reusable
  validation primitives only. The existing structural PB request builder calls
  projection currentness validation as the tiny `.1R.6` B1 consumption hook;
  this is not a Gate-5 coordinator.
- Gate 9: `runtime_invocation_authority_consumption.py` is unchanged and inert.
  No approval/proof consumption, atomic transaction, retry consumption, or
  production caller exists.
- Gate 10: unchanged; no dispatch or external effect.
- Permission Broker: PB foundation/evaluator and `POL-005` are unchanged. No
  production policy consumer was added. The pre-existing structural
  `runtime_dispatch` request builder remains the only projection consumer, and
  a real `simulation_only=False` request remains universally denied.
- Runtime: `not_implemented / Observed / observe / unavailable`; zero runtime
  plugins and zero runtime capabilities.
- Real authentication: no FIDO2, WebAuthn, CTAP, physical authenticator,
  hardware enumeration, attestation, credential ceremony, or enrollment.
- Real approval interface: no protected UI, trusted display, approval CLI,
  enrollment CLI, or human interaction ceremony.

Zero-effect statement for this phase:

```text
Runtime Enforcement calls = 0
Shell Gate calls = 0
runtime subprocess calls = 0
provider/network calls = 0
hardware operations = 0
credential operations = 0
Gate-9 consumption = 0
Gate-10 effects = 0
```

The subprocesses used by tests are local test-runner/clean-import/cross-process
identity checks only; no runtime or provider subprocess path was invoked.

## 12. Defensive tests

`tests/test_runtime_authority_production_repair_3w1r2b1r1117.py` adds 41
phase-specific cases. It covers:

- Step-4 challenge tamper and self-consistent substitution rejection;
- N1 caller object/copy/noncanonical ID/fake store/store reread/no mutation;
- N2 caller strings/copied principal/NON-REAL creation and validation;
- invocation substitution and lost-process provenance;
- revoked principal/credential, expired proof/challenge/approval, changed
  presentation/lifecycle, consumed approval, and same-binding idempotence;
- B1 copied/mutated/invocation-transferred projections;
- B7 valid registry reread plus unregistered, deleted, and changed records;
- no PB authority after NON-REAL rejection and unchanged `POL-005` denial;
- test-fixture isolation, exact production-file allowlist, seven contracts plus
  POL-005 byte identity, consumer inventory, and forbidden effect/FIDO/UI
  imports.

Historical affected tests were updated only where the production API now
requires exact challenge, canonical store, verifier principal, current time,
or B7 tracker lifetime. No adversarial premise was weakened; old tests now
assert the repaired fail-closed boundary. The two historical tests that demand
an `object.__new__` object be `not isinstance` remain unmodified in premise and
continue to fail on both baseline and candidate as designed evidence.

## 13. Regression evidence and fixed-SHA attribution

Immutable baseline: `b85e903c62f386f3c5a45747ded5ff7682b77267` in a
detached disposable worktree.

| Scope | Baseline | Candidate | Attribution |
|---|---:|---:|---|
| New `.1R.7` adversarial suite | not present | 41 passed | all new cases pass |
| New suite + three passing verifier suites | N/A | 117 passed | pass |
| Exact 14-file affected-existing scope | 462 passed, 2 failed | 462 passed, 2 failed | identical two historical node IDs; candidate-only nonpassing = 0 |
| 21-file HPAC/foundation scope | 458 passed, 54 failed | 458 passed, 54 failed | exact failure-name identity; candidate-only nonpassing = 0 |
| Canonical approval store | N/A | 27 passed | pass |

Therefore:

```text
UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0
```

The required raw `python -m pytest -n auto` command collected 38,170 tests
but aborted before execution because one historical test module embeds fresh
UUIDs in parametrized node IDs independently in each xdist worker. This is the
known xdist random-UUID collection instability, not a candidate failure.

The complete-coverage fallback was then run without changing code:

1. `python -m pytest -n auto --ignore=<UUID-parametrized-module>`:
   38,004 items — 37,286 passed, 690 historical failures, 9 historical setup
   errors, 18 skipped, 1 xfailed.
2. The excluded module serially: 165 passed, 1 historical snapshot failure.

Combined coverage: all 38,170 items — 37,451 passed, 691 historical failures,
9 historical errors, 18 skipped, 1 xfailed. The failures are the repository's
historical phase-snapshot, HATP/HMIC/Class-B host/order/state, packaging-tool,
and evidence tests. Exact fixed-SHA attribution, rather than this intentionally
heterogeneous aggregate, establishes candidate-only regression count zero.

The Fast Green baseline-resolver weakness, UUID collection instability, missing
`build` packaging dependency in some historical tests, and HATP/HMIC/Class-B
host/order sensitivity remain separately classified infrastructure debt. None
was repaired in `.1R.7`.

## 14. Contract byte identity and consumer inventory

Frozen SHA-256 values after implementation:

| Artifact | SHA-256 |
|---|---|
| RIHAC-001 | `38d98e9b6bfee3d1097628b73f7fdcd70ca932a9dfda9007e764c0e9e90a04d0` |
| RIASC-001 | `a47869ba315a55b829982d03989c755aa753af9fef52667d7775ead31a95f608` |
| HPAC-001 | `24fd6fac04ea174d5387c4c945f5055896b77c466c149cd8d13dd3353db0567b` |
| PBRD-001 | `e0799d464af603b4be559c6be4607d2519635eea933ffd1cdde0e02d0e77ffef` |
| RDGO-001 | `24e1eefaedf4c63bc221e6460fecf3c055b88d9d7ba230a76d3ec113f511f5ab` |
| RPAC-001 | `395f6b9d3f1779fb312f66e06819176417db6380193d1f5fee52668d43260c89` |
| PBPA-001 | `6daf404b608fd410a8e8c4551f06e76268e49abe056c96db49c1ecca99db02b2` |
| PB foundation / POL-005 source | `2eb7c1068736c10018482f6787ae9cbd7cf4cf8ceaeeac728e18b75dec2639d1` |

Production consumer inventory:

- `hpac_verifier` / `AuthenticatedHumanPrincipal`: consumed only by lazy,
  scoped calls inside `runtime_authority.py` approval creation/validation and
  its projection revalidation context.
- canonical approval store: `runtime_authority.validate_approval` loads by ID;
  the store implementation is unchanged.
- RIHAC projection: emitted/registered only in `runtime_authority.py` and
  consumed only by the existing structural adapter in
  `runtime_dispatch_permission.py`.
- no RDGO coordinator, Gate-9, runtime effect, provider adapter, or new PB
  evaluator consumer exists.

## 15. Findings and limitations

No new Blocking implementation defect was found.

Newly explicit, non-blocking limitations:

1. The frozen persisted approval envelope still uses RIASC-001 v1.0 fields;
   changing it requires a separately governed schema/store migration. The hard
   NON-REAL stop prevents this from becoming real authority today.
2. A genuinely successful B1 production projection cannot be integration-tested
   until a real PRODUCTION HPAC mechanism and protected approval act exist.
   Current tests prove the structural anti-transfer/currentness mechanics only.
3. Same-process arbitrary memory mutation remains F7 and is not process
   isolation.
4. Full-suite aggregate health is historically non-green; fixed-SHA affected
   and foundation identity comparisons are the attribution authority.

The historical `.3` governance incident remains unchanged:

```text
DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
```

No delegated worker was used in this phase. All lifecycle mutations are by the
human-authorized primary operator for `.1R.7`; the prior incident grants no
precedent.

## 16. Verdict and next phase

```text
B1/B7/N1/N2 PRODUCTION AUTHORITY REPAIR:
IMPLEMENTED
— INDEPENDENT VERIFICATION PENDING
— REAL AUTHORITY STILL UNAVAILABLE
```

The only recommended next phase is:

**149O.20L.7O.3W.1R.2B.1R.1.1R.8 — Independent Verification of B1/B7/N1/N2
Production Authority Repair Implementation**

It is not begun or authorized by this report. Gate-5/Gate-9 coordinator wiring
remains a distinct, unscheduled later chapter with no invented phase ID.

## 17. Governed finalization record

This document is authored before the governed commit/push/finalization sequence
so it can be part of the reviewed implementation change set. The authoritative
commit list, pushed status, and final `origin/main..HEAD` value are recorded by
the canonical `.pcae` phase report/metadata generated by `pcae phase complete`
and reconciled after `pcae push`. No raw Git commit/push, `--no-verify`, force
push, history rewrite, or hook bypass is used.
