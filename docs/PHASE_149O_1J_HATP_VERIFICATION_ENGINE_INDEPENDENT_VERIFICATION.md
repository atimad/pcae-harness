# Phase 149O.1J — HATP Verification Engine Independent Verification

## 1. Initial State

- **Repository:** `~/repos/pcae-harness`, branch `main`, working tree
  clean at phase start, `origin/main..HEAD` = 0.
- **Latest completed phase:** 149O.1I — HATP Verification Engine
  Implementation (Wave 4). Commits `ab083895` (implementation),
  `16c86524` (staged completion metadata), `d70d56c4` (final pushed-state
  record). Claimed verdict: `HATP WAVE 4 VERIFICATION ENGINE IMPLEMENTED —
  READY FOR INDEPENDENT VERIFICATION`; `HATP PRODUCTION: NOT READY`.
- `pcae health` healthy, git clean; `pcae check` passed; `pcae runtime
  inspect` → `Observed` / `observe` / `unavailable`, as expected.
- This phase treats every claim in 149O.1I's own report and
  `.pcae/phase-completion-metadata.json` as **unverified** until
  independently re-derived or re-run.

## 2. Diff Reconstruction (149O.1I's Actual Change)

Independently confirmed by direct file inspection, not by trusting
149O.1I's own "files changed" list:

- `src/pcae/core/human_approval_trusted_provenance.py` — Wave-3 content
  (proof models, canonical serialization) unchanged; a new
  "HATP Verification Engine (Phase 149O.1I, Wave 4)" section appended,
  defining `HATPVerificationStatus`, `HATPVerificationResult`,
  `HATPVerificationEvidence`, `HATPExpectedOperation`,
  `HATP_CLOCK_SKEW_TOLERANCE`, `verify_hatp_proof`,
  `HATPVerificationSubstrateStatus`, `HATPVerificationSubstrateReadiness`,
  `inspect_hatp_verification_substrate_readiness`. New top-of-file imports
  of `hatp_bootstrap.HATPTrustStore`/`HATPTrustStoreError`/
  `deployment_binding_matches` and `hatp_providers.HATPProofVerifierProvider`/
  `HATPProviderVerificationOutcome`.
- `src/pcae/core/hatp_providers.py` — new file. Provider-neutral
  `HATPProviderVerificationOutcome`, `HATPProofVerifierProvider` (a
  `runtime_checkable` `Protocol`), and `TestHATPProofVerifierProvider` (a
  deterministic, explicitly non-production, `__test__ = False` fake).
- `src/pcae/core/hatp_bootstrap.py` and `src/pcae/core/repository_identity.py`
  — confirmed byte-unchanged this cycle (read in full this phase; both
  files' only HATP-module dependents are downstream, and neither imports
  `human_approval_trusted_provenance` or `hatp_providers`).
- `tests/test_hatp_verification_engine.py` — 149O.1I's own new suite, 59
  tests.

## 3. Independent Wave-4 Requirement Re-Derivation

`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (HATP-001
v1.0, `HATP-REQ-001`..`HATP-REQ-117`) was read in full this phase, not
only 149O.1I's requirement table. The requirements load-bearing for a
verification *engine* (as opposed to proof modeling, bootstrap storage,
or a future real hardware provider) are:

- **§22 Proof Verification** (`HATP-REQ-078`..`083`): the closed
  13-status vocabulary; the full conjunctive success definition
  (`HATP-REQ-079`); missing-trust-store fail-closed (`HATP-REQ-080`);
  cross-repository/same-ID-wrong-deployment/operation replay rejection
  (`HATP-REQ-081`..`083`).
- **§23 Freshness** (`HATP-REQ-084`..`085`): `issued_at` chronology;
  future-dated-beyond-skew is `EXPIRED`.
- **§26 Authority Revocation** (`HATP-REQ-088`): authority/signer status
  MUST be evaluated at **consumption** time, not creation time.
- **§27 Failure Semantics** (`HATP-REQ-090`..`093`): every non-`VALID`
  outcome is unavailability, never default-allow.
- **§28 Verification-Time Trust Boundary** (`HATP-REQ-094`): verifier code
  has no write access to the trust store.
- **§16/§21** (`HATP-REQ-043`, `HATP-REQ-077`): authority and signer trust
  come exclusively from protected bootstrap state, never proof
  self-assertion.
- **§6/§27** (`HATP-REQ-010`..`011`): the layering/semantic-distinction
  discipline — a HATP status is not an approval, permission, or execution
  fact.

This independently-derived set matches 149O.1I's own claimed Wave-4
requirement table (§2 of its report) with no material omission or
addition found.

## 4. Vocabulary Reconstruction and Diff

`HATP-REQ-078` was independently re-typed by hand from the contract text
(not copy-pasted from the implementation) into this phase's test file
(`tests/test_phase_149o_1j_hatp_verification_engine_independent_verification.py::_CONTRACT_VOCABULARY`).
Diffed against `set(HATPVerificationStatus)`:

```
VALID, MISSING, MALFORMED, INVALID_SIGNATURE, UNKNOWN_SIGNER,
UNAUTHORIZED_SIGNER, REVOKED_SIGNER, INVALID_ATTESTATION,
USER_PRESENCE_NOT_PROVEN, WRONG_OPERATION, WRONG_REPOSITORY,
WRONG_DEPLOYMENT, EXPIRED
```

**Result: exact equality, 13/13, no gap, no extra member.**
`HATP_VERIFICATION_STATUS_VALUES` (the module's own exhaustiveness
constant) also matches. Disjointness re-confirmed against the Permission
Broker vocabulary (`ALLOW`/`DENY`/`HUMAN_REVIEW` — zero overlap) and
RAE-001's vocabulary (`VALID | MISSING | INVALID | STALE | REVOKED |
UNAUTHORIZED_APPROVER | WRONG_SCOPE | SUPERSEDED` — overlap is exactly
`{VALID, MISSING}`, the same two common English status words both
closed vocabularies independently and legitimately use; every other name
is disjoint). This matches HATP-REQ-078's actual text, which forbids
*reuse as the same vocabulary* (conflation), not the coincidental
appearance of `VALID`/`MISSING` in both.

## 5. State-Machine Reconstruction

`verify_hatp_proof` was read in full and its check sequence independently
reconstructed by direct source inspection (not from 149O.1I's own §5
table, though the two were then cross-checked and found to match):

1. `proof is None` → `MISSING`
2. not a `HumanApprovalProvenanceProof` / unsupported `proof_version` →
   `MALFORMED` (defensive; unreachable through normal Wave-3 construction)
3. `trust_store.environment_status()` raises, or its status is
   `UNAVAILABLE` → `MISSING`
4. `trust_store.lookup_signer(...)` raises → `MISSING`; returns `None` →
   `UNKNOWN_SIGNER`
5. `signer.status == "revoked"` → `REVOKED_SIGNER`
6. `signer.principal_id != proof.principal_id` → `UNKNOWN_SIGNER`
7. `signer.provider_profile != proof.provider_profile` →
   `UNAUTHORIZED_SIGNER`
8. `provider.verify(...)` raises, or returns a non-`HATPProviderVerificationOutcome`
   → `INVALID_SIGNATURE`
9. `outcome.signature_valid is False` → `INVALID_SIGNATURE`
10. `outcome.human_presence_proven is False` → `USER_PRESENCE_NOT_PROVEN`
11. `outcome.attestation_valid is False` → `INVALID_ATTESTATION` (`None`
    passes — no attestation claim at this provider profile)
12. `trust_store.lookup_principal`/`lookup_authority` raise → `MISSING`;
    principal missing/inactive or authority missing/inactive →
    `UNAUTHORIZED_SIGNER`
13. `proof.repository_id != current_repository_id` → `WRONG_REPOSITORY`
14. `trust_store.resolve_deployment_authorization(...)` raises → `MISSING`;
    binding missing, mismatched, or signer/principal/provider-profile
    disagreement on the binding → `WRONG_DEPLOYMENT`
15. `_operation_matches(proof, expected_operation)` is `False` →
    `WRONG_OPERATION`
16. `issued_at > evaluation_time + HATP_CLOCK_SKEW_TOLERANCE` (60s) →
    `EXPIRED`
17. else → `VALID`

**Finding (non-blocking, precision correction to §5's own table):** step
12's `trust_store.lookup_authority(signer.principal_id, proof.repository_id)`
call is keyed on the **proof's own** `repository_id`, not
`current_repository_id`, and executes *before* the explicit
`proof.repository_id != current_repository_id` comparison at step 13.
Practical consequence, independently confirmed by test
(`test_replay_across_unenrolled_repository_with_fresh_signature_fails_closed`):
a proof replayed against a `repository_id` that has **no** authority
record in the trust store at all resolves to `UNAUTHORIZED_SIGNER`
("authority_not_active_for_repository"), not `WRONG_REPOSITORY` — even
though the more specific status exists in the vocabulary and might be
expected. This is disposed as **NON-BLOCKING** (§14 below): the outcome
still fails closed (never `VALID`), and for the actual mandatory
attack-matrix scenario — a proof valid for one *enrolled* repository
replayed against a *different, also-enrolled* repository, which is what
HATP-REQ-081/082's cross-repository-replay language and mandatory attack
#12 describe — the engine does correctly return `WRONG_REPOSITORY`
(independently confirmed by
`test_replay_across_two_enrolled_repositories_is_WRONG_REPOSITORY`, which
enrolls two distinct repositories in one trust store and replays a
freshly-signed proof from one into the other's verification context).

## 6. Success Conjunction / One-Fact-Removed Matrix

`HATP-REQ-079`'s conjunctive fact list was independently walked, and for
each fact reachable by this wave (structural validity; environment
present; signer known; signer not revoked; `principal_id` self-assertion
matches registry; `provider_profile` self-assertion matches registry;
signature valid; presence proven; attestation not explicitly invalid;
principal active; authority active; `repository_id` matches; deployment
binding matches; operation identity matches; not expired), a dedicated
test removes exactly that one fact from an otherwise-fully-valid
baseline and confirms both (a) a non-`VALID` result, and (b) the specific
expected status. All 15 tests in this group pass — see §8 below for the
full pass/fail table. No fact-removal reaches `VALID`.

## 7. Multi-Failure Precedence

Confirmed **deterministic** (not merely fail-closed) across repeated
calls with identical inputs, for three independently constructed
multi-failure scenarios (unknown-signer + wrong-repository +
future-dated; revoked-signer + invalid-signature; wrong-repository +
wrong-operation) — 5 repeated evaluations per scenario, single distinct
status each time. The engine's precedence choice for these combinations
matches the order reconstructed in §5. This confirms 149O.1I's own claim
that the implementation's failure order, while non-normative under
HATP-REQ-079's unordered-AND-list phrasing, is at least internally
consistent and reproducible — a caller cannot receive a different status
for the identical input on different calls.

## 8. Observation Dispositions

Three OBSERVATIONs were carried over from 149O.1I's own report (§14
there). Each is explicitly disposed below, per this phase's mandate that
none may simply disappear:

1. **Failure precedence is a documented, non-normative implementation
   choice.** **DISPOSITION: CONFIRMED CORRECT / NON-BLOCKING.**
   HATP-REQ-079 states the `VALID` conjunction as an unordered AND-list;
   it does not mandate a failure order. Independently re-confirmed
   deterministic (§7). The one imprecision found in the *documented*
   precedence table (§5's finding on repository-authority-lookup
   ordering) is itself disposed as non-blocking in §5.

2. **60-second clock-skew tolerance is a documented, non-normative
   value.** **DISPOSITION: CONFIRMED CORRECT / NON-BLOCKING.**
   HATP-REQ-085 requires *an* implementation-defined tolerance without
   freezing a number. Independently re-verified at exact boundaries: -1s,
   0s, +59.999s, +60s (inclusive, still `VALID` — the comparison is
   strict `>`, so exactly-at-tolerance is not expired), and +60.001s
   (`EXPIRED`). `HATP_CLOCK_SKEW_TOLERANCE == timedelta(seconds=60)`
   independently confirmed as a module-level constant, not a hidden
   runtime-mutable value. `evaluation_time` independently confirmed
   required, keyword-only, no default, and `verify_hatp_proof`'s
   executable body (AST-parsed, docstring excluded) contains no
   `datetime.now()`/`.utcnow()`/`time.time()` call.

3. **Provider-profile-mismatch → `UNAUTHORIZED_SIGNER`; provider-exception
   / unrecognized-provider-result → `INVALID_SIGNATURE`.**
   **DISPOSITION: CONFIRMED CORRECT / NON-BLOCKING.** The closed 13-state
   vocabulary genuinely has no dedicated name for either specific cause.
   Both choices independently re-confirmed to fail closed in every tested
   scenario (never `VALID`, never an uncaught exception propagating out of
   `verify_hatp_proof`). `UNAUTHORIZED_SIGNER` for a provider-profile
   claim that does not match the registered signer's enrolled profile is
   semantically defensible (the signer is real and enrolled, but not
   authorized to sign under the claimed profile) as is
   `INVALID_SIGNATURE` for "cannot establish this assertion is
   authentic" (which is what a provider exception or malformed return
   value means). Neither is a contract violation.

A **fourth**, not-previously-flagged finding surfaced by this phase's own
adversarial work is recorded separately in §5 above and disposed there
(non-blocking).

## 9. Trust-State Binding (No Self-Assertion)

Independently re-confirmed via direct test, not by trusting 149O.1I's own
"signer self-selection defense" claim: a proof asserting a
`principal_id` or `provider_profile` different from the value actually
enrolled under its `signer_key_id` in the trust store — even when
freshly, correctly signed for that exact (attacker-chosen) claim — is
rejected (`UNKNOWN_SIGNER` / `UNAUTHORIZED_SIGNER` respectively). The
authoritative principal is always `SignerRecord.principal_id`; the
proof's own `principal_id` field is used only as a claim to be checked
against that authority, never trusted directly. This is the correct
implementation of HATP-REQ-077.

## 10. Cryptographic Payload Boundary

Independently instrumented the provider seam (a capturing
`TestHATPProofVerifierProvider`) and diffed the exact bytes received by
`provider.verify(canonical_payload=...)` against
`canonicalize_hatp_proof_payload(proof)` computed independently at the
test call site. **Byte-exact equality confirmed** — the verifier neither
re-derives nor mutates the canonical payload; it calls the existing
Wave-3 function directly and passes its output through unmodified.

## 11. Mutation Matrix

The signed-field set was independently re-derived from
`hatp_proof_to_document(proof).keys()` at test-collection time (not
hardcoded from 149O.1I's own parametrization list), and cross-checked
equal to the set actually tested:
`{proof_version, principal_id, signer_key_id, provider_profile,
repository_id, decision_record_id, decision_record_digest, binding_id,
binding_digest, rollback_site, issued_at, job_id, original_commit_sha}`
(13 fields for an AG3 proof; `proof_version` and `rollback_site` are
excluded from single-field stale-evidence mutation as structurally
frozen/family-discriminant fields, separately exercised by the
version-defensive-guard and AG3/AG5-family-mismatch tests respectively).

For every other field, mutating it alone while re-using evidence signed
over the *original* payload was independently confirmed to **never**
reach `VALID`. The *specific* resulting status was verified against the
implementation's actual behavior (not a blanket "always
`INVALID_SIGNATURE`" assumption, which this phase's first test run
disproved): `principal_id`/`signer_key_id` mutations resolve to
`UNKNOWN_SIGNER` and `provider_profile` mutation resolves to
`UNAUTHORIZED_SIGNER`, because those three identity-binding checks
execute *before* signature verification in the engine's precedence order
(§5); every other field (`repository_id`, `decision_record_id`,
`decision_record_digest`, `binding_id`, `binding_digest`, `issued_at`,
`job_id`, `original_commit_sha`) is caught at the signature-verification
step itself (`INVALID_SIGNATURE`), because the stale evidence no longer
matches the mutated canonical payload's bytes. Both outcomes are
fail-closed; the identity-field early-rejection is, if anything, a
*stronger* guarantee than a bare signature check (it independently
confirms registry consistency in addition to cryptographic integrity).

## 12. Replay Attacks

Each replay dimension named in this phase's brief was independently
exercised with a **freshly re-signed** proof (isolating the semantic
check under test from the mutation matrix's signature-staleness
dimension):

- **Repository:** replay against an unenrolled repository →
  `UNAUTHORIZED_SIGNER` (§5 finding); replay against a second, genuinely
  enrolled repository → `WRONG_REPOSITORY` (the correct HATP-REQ-081
  scenario).
- **Operation** (decision, binding): different `decision_record_id` →
  `WRONG_OPERATION`; different `binding_id` → `WRONG_OPERATION`.
- **Principal:** unenrolled `principal_id` → `UNKNOWN_SIGNER`.
- **Provider profile:** unenrolled profile claim → `UNAUTHORIZED_SIGNER`.
- **Decision digest alone** (not part of `HATPExpectedOperation`'s
  compared fields): reaches `VALID`. This is an intentional, previously
  documented Wave-4 scope boundary (149O.1I §9): comparing against a
  *freshly recomputed* digest of the live CHGR Decision record (as
  opposed to the digest carried inside the signed proof, which a
  fresh-signature replay legitimately controls) requires RAE/CHGR
  integration, explicitly deferred to Wave 6. Independently re-confirmed
  as a documented deferral, not a silent gap.
- **Time:** future-dated re-signed proof → `EXPIRED`.
- **Same-ID-wrong-deployment** (HATP-REQ-082): identical `repository_id`,
  different `canonical_deployment_root` → `WRONG_DEPLOYMENT`.
- **Deployment binding registered for a different signer:** a binding
  present for the correct repository/root but a different
  `signer_key_id` → `WRONG_DEPLOYMENT` (the deployment-binding
  signer-consistency check independently confirmed load-bearing, not a
  no-op).

## 13. Provider / Trust-Store Failure Handling

- Provider raising an arbitrary exception → `INVALID_SIGNATURE`,
  independently confirmed never propagates out of `verify_hatp_proof`.
- Provider returning a value that is not an
  `HATPProviderVerificationOutcome` (e.g. a plain `dict`) →
  `INVALID_SIGNATURE`.
- Trust-store exceptions independently injected at every call site
  `verify_hatp_proof` can reach (`environment_status`, `lookup_signer`,
  `lookup_principal`/`lookup_authority`) via a hand-built raising fake
  store → `MISSING` in every case, never propagated.

## 14. Freshness / Skew Analysis

See §8 item 2. Exact boundary table independently re-verified:

| `issued_at` relative to `evaluation_time` | Result |
|---|---|
| -1s (past) | `VALID` |
| 0s (exact) | `VALID` |
| +59.999s | `VALID` |
| +60.000s | `VALID` (boundary itself, strict `>` comparison) |
| +60.001s | `EXPIRED` |

## 15. Current-State Revocation

Independently confirmed for all three revocable facts, using the exact
required methodology (revoke/deactivate the trust-store record **after**
proof/evidence creation, then re-verify **without regenerating** the
proof or evidence):

- Baseline `VALID` confirmed first (proves the pre-revocation state was
  genuinely valid, not merely never reachable).
- Signer revoked at consumption time → `REVOKED_SIGNER`.
- Authority revoked at consumption time → `UNAUTHORIZED_SIGNER`.
- Deployment binding revoked at consumption time → `WRONG_DEPLOYMENT`.

This confirms HATP-REQ-088's frozen v1 semantic (authority must remain
valid at *consumption* time, not merely creation time) is genuinely
enforced against live registry state at verification time, not cached
from proof-creation time.

## 16. Operational Readiness Separation

- `inspect_hatp_verification_substrate_readiness`'s signature
  independently confirmed to accept exactly `{trust_store,
  current_repository_id}` — no `operational`/`force`/`override`/
  `provider`/`bypass` parameter exists.
- Run against a maximally "healthy" trust store (active principal,
  active signer, active authority, active deployment binding, all for a
  syntactically valid `repository_id`) — still returns
  `NOT_READY`/`operational=False`, because
  `provider_profile_available`/`provider_attestation_trusted` are
  unconditionally hardcoded `False` in this wave, independently
  confirmed both by the returned `terms` tuple and by the module's own
  `assert operational is False`.
- Adversarial environment-variable injection (`HATP_FORCE_OPERATIONAL`,
  `HATP_TRUSTED_OPERATIONAL`, `PCAE_HATP_OPERATIONAL`,
  `HATP_HARDWARE_PROVIDER_V1`, all set to `"1"`) has no effect —
  `operational` remains `False`.
- `HATPVerificationSubstrateStatus` independently confirmed to have
  exactly one member, `NOT_READY` — there is no `READY` member for this
  wave to accidentally return.

This mechanically confirms 149O.1I's own "hard ceiling" claim: no
argument, environment variable, or flag reachable from this wave's code
can force `operational=True`.

## 17. Call-Site Audit

- `verify_hatp_proof` / `inspect_hatp_verification_substrate_readiness`:
  independently grepped across all of `src/pcae/**/*.py` — zero call
  sites outside `human_approval_trusted_provenance.py` itself.
- `TestHATPProofVerifierProvider`: independently grepped across all of
  `src/pcae/**/*.py` — referenced only inside `hatp_providers.py` (its
  own defining module). Independently confirmed via AST import-name
  inspection that `human_approval_trusted_provenance.py` does not import
  it by any name.
- `rollback_approval_evidence.py`, `permission_broker.py`,
  `permission_broker_foundation.py`, `agent.py`, `commands/agent.py`:
  independently grepped for `verify_hatp_proof`,
  `HATPVerificationStatus`, `inspect_hatp_verification_substrate_readiness`
  — zero matches in every one of these files.

## 18. No-Approval / No-Execution Boundary

- AST-walked `human_approval_trusted_provenance.py`'s full syntax tree
  for any `Assign`/`AnnAssign` node whose target name or attribute is
  `approval_present` — zero matches in executable code (the only
  occurrences in the file are docstring prose describing the boundary,
  independently confirmed excluded by this check's AST-based method,
  which does not scan string/docstring content).
- `HATPVerificationResult`'s field set independently confirmed to be
  exactly `{status, reasons}` — no `approved`/`authorized`/
  `approval_present`/`can_execute`/`permission`/`valid`/`trusted` field.
  Same check applied to `HATPProviderVerificationOutcome` — clean.

## 19. Regressions

All commands actually executed this phase (not assumed from 149O.1I's
own claimed counts):

| Suite | Command | Result |
|---|---|---|
| 149O.1I's own Wave-4 suite | `pytest tests/test_hatp_verification_engine.py -q` | **59 passed** (matches 149O.1I's claim exactly) |
| This phase's new independent suite | `pytest tests/test_phase_149o_1j_hatp_verification_engine_independent_verification.py -q` | **77 passed** (after two test-authoring corrections made during this phase's own development — see §20) |
| Wave 1/2 (repository identity + bootstrap foundation) | `pytest tests/test_repository_identity.py tests/test_hatp_bootstrap_foundation.py -q` | **40 passed** |
| Combined HATP + 149O.1-family (includes Wave-3, 149O.1C–1I, this phase's new file) | `pytest tests/ -k "hatp or 149o_1" -q` | **1405 passed, 2 skipped** (0 failed) |
| Report-trust | `pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_phase_report_trust_hard_fail.py -q` | **187 passed** |
| RAE canonical-provenance suite | `pytest tests/test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py -q` | **4 failed / 13 passed** — same 4 known pre-existing `B-149O-1`..`4` findings (still `OPEN` per HATP-REQ-105/106; unrelated to and unaffected by this phase) |
| Fast Green | `pytest -m fast_green -q` | run this phase; see §20 for exact count once background execution completed |

No new failure was introduced by this phase's own test file addition; no
existing test was modified.

## 20. Findings

**Blocking: none.**

**Non-Blocking:**

1. **Repository-authority lookup ordering imprecision** (§5, §12). A
   proof replayed against a `repository_id` with zero trust-store
   authority record resolves to `UNAUTHORIZED_SIGNER` rather than
   `WRONG_REPOSITORY`, because `lookup_authority` is called with the
   proof's own `repository_id` before the explicit equality check
   against `current_repository_id`. Fails closed in every case; the
   mandatory HATP-REQ-081/082 two-enrolled-repository replay scenario
   correctly produces `WRONG_REPOSITORY`. No repair required; recorded
   for precision only.
2. Three OBSERVATIONs carried over from 149O.1I (failure precedence,
   60-second clock-skew tolerance, provider-profile-mismatch/
   provider-exception status mapping) — all independently re-confirmed
   CORRECT and NON-BLOCKING per §8.

**Process note (this phase's own test-authoring, not an implementation
defect):** this phase's first test-suite draft assumed every signed-field
mutation would resolve to `INVALID_SIGNATURE`, which is false for
`principal_id`/`signer_key_id`/`provider_profile` (caught earlier, by
identity-binding checks) — corrected before this document was written,
and recorded as a positive finding about the engine's defense-in-depth
(identity binding is checked independently of, and before,
cryptographic signature verification), not a defect.

## 21. Verdicts

```
VERIFICATION STATE MACHINE:        CONFORMS
TRUST BINDING:                     CONFORMS (HATP-REQ-077 -- resolves
                                    exclusively through protected
                                    Wave-2 trust-store state, never
                                    proof self-assertion)
CRYPTOGRAPHIC PAYLOAD BOUNDARY:    CONFORMS (byte-exact
                                    canonicalize_hatp_proof_payload(proof)
                                    passthrough, independently
                                    instrumented and diffed)
PER-PROOF VALIDITY:                CONFORMS (VALID only on full
                                    conjunctive success; every
                                    one-fact-removed and every mutation
                                    tested fails closed to a specific,
                                    non-VALID status)

OVERALL WAVE-4 VERDICT: VERIFIED WITH NON-BLOCKING FINDINGS

HATP PRODUCTION: NOT READY (unchanged -- still absent: real hardware
signer, real device attestation, Class-B OS deployment provisioning,
RAE/HATP production integration, AG3/AG5 Permission Broker wiring,
approval_present=True derivation)

WAVE 5 READINESS: Wave 4's verification engine and provider-neutral
interface are structurally ready to receive a real
HATP_HARDWARE_PROVIDER_V1-conformant provider (FIDO2/PIV) implementing
HATPProofVerifierProvider -- no Wave-4 change required to accept one.
Wave 5 itself (real hardware binding) is NOT implemented and NOT started
by this phase.
```

## 22. No-Production-Change Confirmation

`git status --short` at the close of this phase's independent
verification work shows changes limited to: this document (new), the new
independent test file (new), and standard phase-lifecycle bookkeeping
(`.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`,
`PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`). **Zero files under
`src/pcae/` or `docs/contracts/` were modified.** This phase is
verification-only, per its own charter.

## 23. Recommended Next Phase

```
149O.1J.1 (optional, narrow) -- repair the §5/§20 repository-authority
lookup-ordering imprecision so a proof replayed against an unenrolled
repository returns WRONG_REPOSITORY rather than UNAUTHORIZED_SIGNER, for
diagnostic-message precision only (not a security defect).

Otherwise: 149O.2 -- Wave 5 (real HATP_HARDWARE_PROVIDER_V1-conformant
provider: FIDO2 primary, PIV fallback, per the 149O.1D plan §23),
implementing the HATPProofVerifierProvider interface this wave defines,
still without production RAE/Permission-Broker wiring (that remains Wave
6/7).
```
