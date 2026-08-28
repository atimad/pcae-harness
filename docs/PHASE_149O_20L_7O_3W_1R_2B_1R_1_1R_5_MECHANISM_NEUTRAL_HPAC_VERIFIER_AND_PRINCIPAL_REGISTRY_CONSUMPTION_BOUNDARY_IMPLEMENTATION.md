# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5 — Mechanism-Neutral HPAC Verifier
# and Principal-Registry Consumption Boundary Implementation

**Phase type:** Implementation. New, isolated module (`hpac_verifier.py`)
and its dedicated test file only. No `runtime_authority.py`,
`runtime_dispatch_permission.py`, `runtime_invocation_approval_store.py`,
or Permission Broker change. No B1/B7/N1/N2 repair. No real FIDO2. No
real protected UI. Runtime remains `Observed` / `observe` / `unavailable`.

**Predecessor:** Phase `149O.20L.7O.3W.1R.2B.1R.1.1R.4` (planning/
reconciliation). This phase implements exactly that document's §7–§30
scope: the standalone, mechanism-neutral HPAC verifier and
principal-registry consumption boundary, as its own governed phase before
B1/B7/N1/N2 repair.

**Finding disposition:** MECHANISM-NEUTRAL HPAC VERIFIER: IMPLEMENTED —
INDEPENDENT VERIFICATION PENDING — NOT YET CERTIFIED. This phase does not
independently certify itself.

---

## 1. `.1R.4` plan mapping

Implements `.1R.4` §7 (verifier responsibilities, ten-step
`HPAC-REQ-054` sequence), §8 (non-responsibilities), §9 (canonical-only
input contracts), §10 (`AuthenticatedHumanPrincipal` output contract),
§11–§21 (trust/provenance, anti-transfer, assurance classification,
credential relationship, UP/UV, lifecycle/Gate-5/Gate-9/Gate-10
boundaries), §26–§29 (failure model, error taxonomy, no caller-forgeable
boolean authority, ephemeral-only persistence), and §30/§31 (threat
matrix and test plan). `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md`
§18 (`HPAC-REQ-054` through `HPAC-REQ-060`) was re-read directly as the
authoritative sequence text; `.1R.4`'s own eight-step paraphrase (§7) is
consistent with it and was not relied on over the primary contract.

## 2. Contracts read

`docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (§4–§21,
`HPAC-REQ-001`–`HPAC-REQ-062` region covering the registry, presentation,
proof, verification-sequence, and assurance-model sections). The
`RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` (RIHAC-001) and
`RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` (RIASC-001) references
in `.1R.4`'s own text were consulted at the source-code level via
`runtime_invocation_approval_store.py`/`runtime_authority.py`'s existing
`RuntimeInvocationApproval`/`ApprovalSubject` dataclasses, not re-derived
from contract prose, since no change to those files is in scope here.

## 3. Files changed

- **New:** `src/pcae/core/hpac_verifier.py` — the verifier module.
- **New:** `tests/test_hpac_verifier.py` — 27 focused/adversarial tests.
- **Modified (test-only, exclusion-list update):**
  `tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py`,
  `tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py`,
  `tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py`
  — each had a "zero pre-existing production consumers of the foundation"
  regression assertion that this phase's own deliverable (the verifier
  legitimately importing the foundation stores) necessarily changes. Each
  was updated to exclude exactly `hpac_verifier.py` as the one sanctioned
  consumer, while continuing to assert no *other*, unexpected consumer
  exists. See §13 below for why this is the correct fix rather than a
  regression.
- **Updated:** `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`,
  task/report/metadata artifacts (governance bookkeeping only).

No production trust-path file (`human_principal_registry.py`,
`approval_presentation.py`, `human_authentication_proof.py`,
`hpac_lifecycle.py`, `runtime_authority.py`,
`runtime_dispatch_permission.py`, `runtime_invocation_approval_store.py`,
`runtime_invocation_authority_consumption.py`) was modified.

## 4. Verifier implementation summary

`verify_human_authentication(...)` executes `HPAC-REQ-054`'s ten-step
sequence against real (fixture-authority) foundation stores, short-
circuiting on the first failure (`HPAC-REQ-055` — no later step runs as a
shortcut):

1. Resolve the canonical proof by `proof_id` only
   (`HumanAuthenticationProofStore.resolve_canonical`).
2. Resolve the principal and require `active` status
   (`HumanPrincipalRegistryStore.resolve_canonical_principal`).
3. Resolve the credential, require `active` status, and require it be
   bound to the resolved principal
   (`resolve_canonical_credential` + explicit `principal_id` equality).
4. Mechanism compatibility + assertion-material check (credential
   `mechanism_id` must equal proof `mechanism_id`; both must be the
   deterministic non-real fixture — see §9 below for why no real
   cryptographic check exists yet).
5. Presentation evidence: canonical resolution
   (`TrustedApprovalPresentationStore.resolve_canonical`) re-verifies
   installed-mechanism provenance, exact attestation bytes, and
   subject/visible-fact binding; the verifier additionally checks
   `presentation.approval_id == approval_id` (the caller-supplied binding
   parameter) and `presentation.approval_subject_digest ==
   proof.approval_subject_digest`.
6. Challenge-state consistency is enforced via the lifecycle chain's
   genesis binding (§9 below — no standalone canonical `Challenge` store
   exists in the foundation).
7. UP/UV: both must be `True` (defense-in-depth; canonical proof storage
   already structurally forecloses a `False` value, see §8).
8. Freshness: `proof.authenticated_at <= now` and
   `presentation.canonical_subject.expires_at >= now`.
9. Full canonical lifecycle chain resolution
   (`HPACLifecycleStore.resolve_canonical_chain`, provenance-checked) and
   genesis-binding cross-check against every proof field.
10. Idempotent-or-fresh `PROOF_VERIFIED_AND_BOUND` transition via
    `bind_gate5_canonical` (existing method, not reimplemented), then
    construction of the ephemeral `AuthenticatedHumanPrincipal`.

## 5. Canonical input model

Every authority-bearing value is resolved by the verifier itself through
its owning canonical store; the only inputs accepted from the caller are
opaque identifiers (`proof_id`, `approval_id`) plus operational parameters
(`now`, `occurred_at`, `gate5_writer`, `verifier_version`,
`require_real_assurance`). No `PrincipalRecord`, `CredentialRecord`,
`TrustedApprovalPresentationEvidence`, `HumanAuthenticationProof`, or
`LifecycleEvent` object can be passed in and trusted directly — this
matches `.1R.4` §9's table exactly for every input it lists **except**
`RuntimeInvocationApproval` (see §9 below for that one deliberate,
documented deviation).

## 6. Principal registry consumption result

`_resolve_principal`/`_resolve_credential` never mutate the registry
(`enroll_*`/`revoke_*` are never called), resolve exclusively through
`resolve_canonical_principal`/`resolve_canonical_credential`, reject
missing/non-`active` records, and reject a credential not bound to the
claimed principal. Confirmed by
`test_revoked_principal_rejected`,
`test_revoked_credential_rejected`,
`test_credential_not_bound_to_claimed_principal_rejected`,
`test_unknown_proof_id_rejected` (transitively exercises unknown
principal via an absent proof).

## 7. Credential relationship result

Mechanism compatibility (`credential.mechanism_id == proof.mechanism_id`)
is checked explicitly and independently of the registry's own status
checks; a credential enrolled under a different mechanism than the
proof claims is rejected before any assurance is granted
(`test_mechanism_substitution_rejected`). No FIDO2-specific credential
logic is imported; the check is a plain field-equality against the
existing `CredentialRecord.mechanism_id`.

## 8. Presentation validation result

Delegated entirely to `TrustedApprovalPresentationStore.resolve_canonical`
(HPAC-REQ-092 exact schema, installed-mechanism provenance, and B-3
display/subject binding are already independently verified there,
`.1R.3.2.2.1`) plus two verifier-owned cross-checks:
`presentation.approval_id == approval_id` and
`presentation.approval_subject_digest == proof.approval_subject_digest`.
No presentation object is ever accepted from a caller; only
`presentation_id`/`presentation_digest` (via the resolved proof's own
`trusted_presentation_ref`) select which record is resolved.

## 9. Proof validation result

Resolved once via `HumanAuthenticationProofStore.resolve_canonical`; its
fields (`principal_id`, `credential_id`, `mechanism_id`,
`challenge_digest`, `approval_subject_digest`, `trusted_presentation_ref`,
`up`, `uv`, `authenticated_at`) drive every subsequent step. **Deliberate
scope decision, documented here rather than silently applied:** `.1R.4`
§9's input table lists "Canonical approval/challenge... resolved via
`RuntimeInvocationApprovalStore` (existing)" as a verifier input. This
phase's implementation does **not** call `RuntimeInvocationApprovalStore`.
Reasons:

- `.1R.4` §36's own *restated*, no-go-bounded scope for this phase lists
  only "canonical principal-registry consumption; trusted proof/
  presentation/lifecycle resolution needed by the verifier" — it does not
  mention the approval store there, unlike the broader §9 table.
- `CanonicalRuntimeApprovalSubject` (the HPAC-side subject the
  presentation/proof/lifecycle chain is bound to) and
  `RuntimeInvocationApproval`/`ApprovalSubject` (the RIASC-side record
  `RuntimeInvocationApprovalStore` persists) are structurally similar but
  not identical types in this codebase today, and no adapter between them
  exists yet. Building one would be new production logic beyond "the
  mechanism-neutral HPAC verifier; canonical principal-registry
  consumption; trusted proof/presentation/lifecycle resolution" (§36's own
  words), and `.1R.4` §19 explicitly assigns that kind of
  projection-construction work to a *future* Gate 5, not this phase.
- `runtime_invocation_approval_store.py` is one of the three files the
  B1/B7/N1/N2 repair phase (`...1R.6`, §34 step C) is scoped to modify;
  this phase intentionally minimizes its surface contact with that file
  rather than introduce a first (read-only) production dependency on it
  ahead of that repair phase's own scoping decision.

Net effect: `approval_id` is consumed here purely as a caller-supplied
binding key checked for equality against records that already carry it
(`presentation.approval_id`, lifecycle `binding["approval_id"]`) — never
as authority, and never resolved as a separate record. This is a narrower
implementation than §9's table literally describes, not a broader one; no
authority wall is weakened by it. Flagged explicitly as a limitation
(§18) for `...1R.5.1`'s independent verifier and for `...1R.6`'s eventual
RIASC integration to confirm or revise.

**Assertion verification (`HPAC-REQ-054` step 6, "verify assertion against
the resolved credential's public verification material"):** no real
cryptographic mechanism exists in this repository yet — the primary v2
FIDO2 mechanism is Layer 6, a later phase (`.1R.4` §25/§34 step E). This
implementation follows the exact same categorical-rejection discipline
`approval_presentation.py`'s `_verify_installed_attestation` already uses
for the identical "no real verifier implemented" boundary: `credential.
mechanism_id`/`proof.mechanism_id` must both equal the fixed deterministic
non-real mechanism ID, or verification is rejected outright — no attempt
at real signature math against `credential.public_key` is made or faked.

## 10. Lifecycle/replay result

`resolve_canonical_chain` (provenance-checked) is used exclusively; the
verifier never calls the structural-only `resolve_chain`. Genesis binding
is cross-checked against every relevant proof field
(`approval_id`, `principal_id`, `credential_id`, `mechanism_id`,
`challenge_digest`, `approval_subject_digest`, `trusted_presentation_ref`)
before any state transition is attempted. A chain not yet at
`PROOF_VERIFIED` is rejected (`test_lifecycle_not_yet_verified_state_rejected`).
An already-`PROOF_VERIFIED_AND_BOUND` chain with a matching
`approval_digest` is accepted idempotently without re-calling
`bind_gate5_canonical` (`test_idempotent_same_binding_reverification_succeeds`);
a mismatched `approval_digest` at that state is rejected as cross-binding
replay. `approval_digest` itself is `presentation.approval_subject_digest`
— the canonical digest of the exact subject the human presentation bound
to — reusing an existing digest rather than inventing a new one, since no
`RuntimeInvocationApproval` integration exists in this phase (§9).

## 11. UP result / 12. UV result

Both must be `True`; enforced by `_check_up_uv`, called unconditionally
after presentation resolution. Canonical proof storage already
structurally forecloses a `False` UP or UV from ever reaching a
store-resolved proof (`human_authentication_proof.py`'s
`_validate_proof_document`), so this is redundant defense-in-depth, not
the only enforcement point — documented explicitly in the module
docstring of `_check_up_uv` rather than left implicit. Tested directly
against the internal guard (`test_up_false_rejected_internal_guard`,
`test_uv_false_rejected_internal_guard`) since the store path cannot
produce a resolvable counterexample.

## 13. Assurance-class result

`_authority_class_of` requires every resolved record (principal,
credential, presentation, proof) to agree on `authority_class`, then
copies that value onto `AuthenticatedHumanPrincipal.assurance_class` —
never caller-declared. All fixture-authority end-to-end tests assert
`assurance_class is HPACAuthorityClass.FIXTURE_NON_REAL`, including with
`up=True, uv=True`
(`test_deterministic_success_remains_non_real_even_with_up_and_uv_true`).
`require_real_assurance=True` rejects unless every resolved record's
`authority_class` is `PRODUCTION`; since no production HPAC writer exists
in this repository yet (`hpac_foundation.py`'s own docstring), this flag
can currently only ever reject — itself the correct fail-closed behavior,
confirmed by `test_fixture_to_real_upgrade_rejected`.

## 14. Deterministic NON-REAL result

Confirmed by the two tests above plus
`test_canonical_valid_deterministic_verification_succeeds_at_non_real_assurance`.

## 15. Verifier-result provenance/anti-forgery result

`AuthenticatedHumanPrincipal` has no public constructor (`_seal` guard,
`test_caller_constructed_verifier_result_rejected`), cannot be pickled or
deep-copied (`__reduce__` raises,
`test_verifier_result_cannot_be_pickled`,
`test_copied_verifier_result_is_not_equal_to_a_fresh_one`), and compares
by identity only, not shape
(`test_verifier_result_equality_is_identity_only`) — a byte-identical-
looking second instance from a second `verify_human_authentication` call
is never `==` to the first.

## 16. Invocation-binding result

`presentation.canonical_subject.subject.invocation_id` is copied onto the
result. `test_approval_id_substitution_rejected` and
`test_valid_result_for_invocation_a_cannot_be_reused_for_invocation_b`
confirm a proof/approval_id pairing that crosses invocations is rejected
before any principal is authenticated.

## 17. Gate-5 relationship

`verify_human_authentication` is exactly the reusable core a future Gate
5 will call (`.1R.4` §19); it does not construct RDGO-001 §6's own
Gate-5-specific projection object, and every call re-runs the full
sequence fresh (no cross-call caching), per `HPAC-REQ-058`.

## 18. Gate-9 non-consumption result

Confirmed by static analysis
(`test_gate9_consumption_store_is_never_referenced_by_the_verifier`,
AST-import check in
`test_hpac_verifier_module_does_not_import_pb_or_runtime_authority_modules`):
`hpac_verifier.py` never imports
`runtime_invocation_authority_consumption`, never writes a consumption
record, and never advances proof lifecycle beyond
`PROOF_VERIFIED_AND_BOUND`.

## 19. Production consumer inventory

```
grep -rl "hpac_verifier" src/pcae --include="*.py" | grep -v "hpac_verifier.py$"   → (empty)
grep -rn "hpac_verifier" src/pcae/core/runtime_authority.py
                          src/pcae/core/runtime_dispatch_permission.py            → (empty)
```

Zero production consumers of `hpac_verifier.py` exist anywhere in
`src/pcae` after this phase, confirmed both by the greps above and by
`test_zero_production_consumers_of_hpac_verifier_module` (AST-based,
runs on every test invocation rather than only at authoring time).

## 20. PB isolation result

`hpac_verifier.py` never imports `runtime_dispatch_permission` or any
`permission_broker`-named module (AST-checked). It returns no `ALLOW`/
`DENY` decision and evaluates no POL policy.

## 21. Runtime isolation result

`hpac_verifier.py` never imports `runtime_authority`. No
`subprocess`/`socket`/network/hardware call exists anywhere in the
module (it performs only filesystem-backed canonical-store resolution
via the existing foundation stores).

## 22. B1 / B7 / N1 / N2 status

Unchanged. `runtime_authority.py`, `runtime_dispatch_permission.py`, and
`runtime_invocation_approval_store.py` are untouched by this phase (the
last is not even imported, see §9). Status remains: contract closed /
implementation open for all four.

## 23. Foundation regression result

Full existing HPAC foundation test family (`test_hpac_approval_
presentation.py`, `test_hpac_authentication_proof.py`, `test_hpac_
authenticator_deterministic.py`, `test_hpac_authority_consumption.py`,
`test_hpac_lifecycle.py`, `test_hpac_principal_registry.py`, and the six
`.3.2*`/`.3.1` phase-specific test files) re-run alongside the new
`test_hpac_verifier.py`. A fixed-SHA A/B (baseline `817b788a`, this
phase's working tree via `git stash`) confirms the failures below are
**pre-existing and reproduce identically without this phase's changes**:

- 11 consistently-failing `test_blocking_reproduction_*`/`test_
  deterministic_attestation_encoding_has_contract_extra_fields`-style
  tests across `test_hpac_foundation_independent_verification_
  3w1r2b1r111r31.py` and `test_hpac_trust_root_repair_independent_
  verification_3w1r2b1r111r321.py` — identical failure set and identical
  error text (`HPACMalformedError: ... must be exactly one safe path
  component`, `HPACLifecycleStateError: invalid lifecycle predecessor
  relation`, etc.) present at baseline `817b788a` with none of this
  phase's changes applied.
- 1–2 additional order-dependent flakes
  (`test_deterministic_authenticator_is_non_real_but_no_real_verifier_
  exists_to_enforce_allowlist`,
  `test_concurrent_conflicting_successors_have_one_canonical_winner`)
  that pass in file-level isolation but intermittently fail only when
  run alongside the full combined suite, reproducing at baseline with the
  identical combined-suite command and absent when run in isolation —
  consistent with `.1R.4` §32's documented "historical state-sensitive
  tests remain known debt," not a regression this phase introduces.

Three pre-existing regression tests (§3 above) asserted "zero production
consumers of the foundation" as an absolute; this phase's deliverable is
itself the first sanctioned consumer, so those three assertions were
updated (not weakened) to exclude exactly `hpac_verifier.py` by name
while continuing to assert no *other* consumer exists. This is a
necessary, intentional test update tracking the phase's own purpose, not
a masked regression — verified by re-reading each modified assertion's
diff: the only change is one additional excluded filename per test.

## 24. Focused verifier tests

27 tests in `tests/test_hpac_verifier.py`, all passing:
happy-path/assurance classification (3), canonical-resolution-only
inputs (6), presentation/invocation/approval binding (4), UP/UV
defense-in-depth (2), lifecycle state/replay (3), fixture-to-real
upgrade (1), anti-forgery/anti-transfer (4), zero-consumer/zero-effect
static checks (3), non-canonical proof handling (1).

```
python -m pytest tests/test_hpac_verifier.py -q
27 passed
```

## 25. Fixed-SHA regression attribution

Baseline: `817b788a` (this phase's immediate predecessor's finalization
commit — no working-tree changes). Candidate: this phase's working tree.
A/B comparison via `git stash -u` / `git stash pop` (three separate runs,
covering the two-file "zero consumer" pair, the full 11-file HPAC
foundation family, and the single previously-passing-in-isolation flaky
test) confirms:

- Zero new failures introduced by this phase's `hpac_verifier.py` or
  `tests/test_hpac_verifier.py`.
- The three test-file edits in §3 are the only change to pre-existing
  test files, and each is a documented, minimal, one-line exclusion-set
  addition — not a weakened assertion.

## 26. Unexplained attributable regression count

**0.**

## 27. Runtime state

```
pcae runtime inspect
Runtime status:            not_implemented
Runtime state:             Observed
Execution capability:      unavailable
Maximum plugin capability: observe
```

Unchanged by this phase. No runtime, subprocess, network, or hardware
call exists anywhere in `hpac_verifier.py` or its test file.

## 28. No-FIDO2 proof

`grep -i "fido\|webauthn\|ctap"` over `hpac_verifier.py` and
`tests/test_hpac_verifier.py`: no match. The only mechanism identity the
verifier accepts is `hpac.deterministic.test-only.v1`
(`_ELIGIBLE_MECHANISM_IDS`); every other mechanism ID is rejected
(`test_unsupported_mechanism_id_rejected`).

## 29. No-UI proof

No terminal prompt, CLI approval flow, or display/rendering code exists
in `hpac_verifier.py`. It is a pure function-and-dataclass module over
existing canonical stores.

## 30. Delegated-worker governance confirmation

This phase was executed by the primary operator under the human's
explicit authorization for exactly
`149O.20L.7O.3W.1R.2B.1R.1.1R.5`, per the governing prompt's §38. No
delegated worker performed any commit, finalization, or push action.

## 31. Findings

None newly discovered that block this phase's own acceptance criteria.
One documented scope deviation from `.1R.4` §9's input table (§9 above):
the verifier does not resolve `RuntimeInvocationApproval` via
`RuntimeInvocationApprovalStore`, consuming `approval_id` only as an
opaque binding key. This is flagged as an open question for
`...1R.5.1`'s independent verification and for `...1R.6`'s eventual
production-authority repair to confirm, revise, or formally freeze.

## 32. Implementation verdict

**MECHANISM-NEUTRAL HPAC VERIFIER: IMPLEMENTED — INDEPENDENT VERIFICATION
PENDING — NOT YET CERTIFIED.**

Acceptance criteria (§39 of the governing prompt) status:

| Criterion | Status |
|---|---|
| Mechanism-neutral HPAC verifier | IMPLEMENTED |
| Principal registry consumption | CANONICAL / READ-ONLY |
| Presentation consumption | CANONICAL / PROVENANCE-VALIDATED |
| Proof consumption | CANONICAL / PROVENANCE-VALIDATED |
| Lifecycle validation | CURRENT / NON-CONSUMING (writes only `PROOF_VERIFIED_AND_BOUND`, never Gate-9 consumption) |
| UP | VALIDATED |
| UV | VALIDATED |
| Assurance class | PRESERVED |
| Deterministic path | VERIFIED LOGICALLY, REMAINS NON-REAL |
| Verifier result | NON-AUTHORIZING / NON-PB / NON-EXECUTING / NOT CALLER-FORGEABLE / INVOCATION-BOUND |
| Gate 9 | NOT CONSUMED |
| B1/B7/N1/N2 | NOT REPAIRED |
| PB integration | NONE |
| Runtime integration | NONE |
| Real FIDO2 | NONE |
| Real protected UI | NONE |
| External runtime effects | ZERO |
| Runtime | Observed / observe / unavailable |
| Unexplained attributable regressions | 0 |

## 33. Commits

See `git log` for this phase's commit sequence, subject-prefixed
`Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5:`.

## 34. Pushed status / origin/main..HEAD

Recorded in this phase's canonical completion metadata
(`.pcae/phase-completion-metadata.json`) at finalization time.

## 35. Recommended next phase

**149O.20L.7O.3W.1R.2B.1R.1.1R.5.1** — Independent Verification of
Mechanism-Neutral HPAC Verifier and Principal-Registry Consumption
Boundary Implementation. Requires separate explicit human authorization
before starting. Scope: fresh, independently-authored reproduction of
`.1R.4`'s full §30 threat matrix and §31 test plan against this phase's
`hpac_verifier.py`, plus explicit re-derivation and adjudication of §9's
`RuntimeInvocationApprovalStore` scope deviation. No production change.

This phase does **not** begin `...1R.5.1`, B1/B7/N1/N2 repair, real
FIDO2, or real protected UI. Execution enablement is untouched; POL-005
is unmodified.
