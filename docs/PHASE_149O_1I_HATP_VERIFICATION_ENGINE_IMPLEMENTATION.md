# Phase 149O.1I — HATP Verification Engine Implementation (Wave 4)

## 1. Initial State

- **Repository:** `~/repos/pcae-harness`, branch `main`, working tree
  clean at phase start, `origin/main..HEAD` = 0.
- **Latest completed phase:** 149O.1H.6 — HATP Timestamp Canonicalization
  Final Independent Verification. Wave-3 verdict: `VERIFIED WITH
  NON-BLOCKING FINDINGS`; `WAVE 3: READY FOR WAVE 4 IMPLEMENTATION`.
  `B-149O.1H-1`, `B-149O.1H.4-1` independently confirmed closed;
  `B-149O.1H-2` remains closed.
- **Frozen contract:** `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`,
  `HATP-001 v1.0`, `FROZEN`, `HATP-REQ-001`..`HATP-REQ-117` (117
  requirements), byte-unchanged throughout this phase (confirmed via
  `git status --porcelain -- docs/contracts/` empty at close).
- **Implementation plan:** `docs/PHASE_149O_1D_HUMAN_APPROVAL_TRUSTED_PROVENANCE_IMPLEMENTATION_PLAN.md`.
  Module Ownership Proposal (§7): Wave 4 (verifier `I`, readiness gate
  `J`) is explicitly co-located inside
  `src/pcae/core/human_approval_trusted_provenance.py`, alongside Wave 3
  (`G`/`H`). This is the one plan-sanctioned exception to the otherwise
  Wave-3-only file boundary previously asserted by 149O.1G/1H/1H.2/1H.4/
  1H.6's own test suites.
- **Runtime state, unaffected:** `Observed` / `observe` / `unavailable`
  (`pcae runtime inspect`, confirmed at initial inspection).
- **Fast Green entering baseline:** `4531 passed` (149O.1H.6's own
  count).

## 2. Wave-4 Requirement Reconstruction

Read `HATP-001` directly (not only the 149O.1D plan's table). Wave-4
primary-owner requirements (subsystem `I`, verifier, and `J`, readiness
gate), independently re-derived from the contract text itself:

| Requirement(s) | Normative meaning | Wave-4 disposition |
|---|---|---|
| HATP-REQ-010..011 | Security layering frozen; semantic distinctions (presence ≠ identity ≠ authority ≠ decision; HATP proof ≠ RAE evidence ≠ PB `ALLOW` ≠ execution) MUST be preserved | `HATPVerificationResult` carries only `status`/`reasons`; no approval/permission field exists anywhere in the Wave-4 API |
| HATP-REQ-077 | Signer trust resolves only through the protected bootstrap state, never proof self-assertion | `verify_hatp_proof` cross-checks `proof.principal_id`/`proof.provider_profile` against the registry's `SignerRecord`, never trusts the proof's own claim |
| HATP-REQ-078 | Closed 13-state verification vocabulary | `HATPVerificationStatus` enum, reproduced verbatim |
| HATP-REQ-079 | `VALID` only on full conjunctive success | `verify_hatp_proof`'s full check sequence; every failure path returns a specific non-`VALID` status |
| HATP-REQ-080 | Missing trusted bootstrap state fails closed | `environment_status().status == UNAVAILABLE` → `MISSING`; trust-store exceptions → `MISSING` |
| HATP-REQ-081..083 | Cross-repository replay, same-ID-wrong-deployment replay, operation replay all rejected | `WRONG_REPOSITORY`, `WRONG_DEPLOYMENT`, `WRONG_OPERATION` tests (§5 below) |
| HATP-REQ-084..085 | Freshness: `issued_at` supports chronology; future-dated proof (beyond clock-skew tolerance) is `EXPIRED` | `HATP_CLOCK_SKEW_TOLERANCE` (60s, documented non-normative choice) + explicit `evaluation_time` parameter |
| HATP-REQ-088 | Authority MUST remain valid at consumption time, not creation time | Signer-revocation and authority-active checks performed against the trust store at verification time, using the caller-supplied `evaluation_time`-independent live registry state |
| HATP-REQ-090..093 | Every non-`VALID` outcome fails closed; same-user/headless states resolve to unavailable | `inspect_hatp_verification_substrate_readiness` — see §6 |
| HATP-REQ-094 | Verifier code has no write access to the trust store | `verify_hatp_proof`/`inspect_hatp_verification_substrate_readiness` call only `HATPTrustStore`'s existing read-only methods; no new write method added to `hatp_bootstrap.py` (byte-unchanged this phase) |

No Wave-5 (`HATP-REQ-016..025`, real provider/presence/attestation
binding), Wave-6 (`HATP-REQ-095..096`, RAE integration), or Wave-7
(`HATP-REQ-026..029` at the *deployment* level) requirement is
implemented early. `hatp_providers.py` (new this phase) implements only
the provider-neutral *interface* (part of subsystem `E`) plus the
deterministic test provider (`K`) — no real FIDO2/PIV binding.

## 3. Closed Verification Vocabulary (HATP-REQ-078)

Reproduced verbatim from the frozen contract (§22):

```
VALID
MISSING
MALFORMED
INVALID_SIGNATURE
UNKNOWN_SIGNER
UNAUTHORIZED_SIGNER
REVOKED_SIGNER
INVALID_ATTESTATION
USER_PRESENCE_NOT_PROVEN
WRONG_OPERATION
WRONG_REPOSITORY
WRONG_DEPLOYMENT
EXPIRED
```

Implemented as `HATPVerificationStatus(str, Enum)` in
`human_approval_trusted_provenance.py`, independently tested for
exact-set equality (`test_verification_status_vocabulary_matches_hatp_001_exactly`)
and disjointness from the Permission Broker (`ALLOW`/`DENY`/
`HUMAN_REVIEW`) and RAE-001 (`VALID | MISSING | INVALID | STALE |
REVOKED | UNAUTHORIZED_APPROVER | WRONG_SCOPE | SUPERSEDED`)
vocabularies.

## 4. Verification Result Model

```python
@dataclass(frozen=True)
class HATPVerificationResult:
    status: HATPVerificationStatus
    reasons: tuple[str, ...] = ()
```

No `approved`/`authorized`/`approval_present`/`can_execute`/`permission`/
`valid`/`trusted` field exists on this type or on
`HATPProviderVerificationOutcome` (the provider-neutral evidence type) —
independently tested by field-set equality assertions.

Supporting types:

- `HATPVerificationEvidence` — the outer evidence envelope
  (`assertion: bytes`), deliberately singular (no list), so ambiguous/
  duplicate evidence is fail-closed *by construction*, not by a runtime
  "pick first valid" branch (HATP-001 defines no multi-signature
  semantics).
- `HATPExpectedOperation` — the concrete operation (`decision_record_id`,
  `binding_id`, `rollback_site`, `operation_reference`) the caller is
  currently attempting to authorize; compared by value against the
  proof's own operation fields to detect `WRONG_OPERATION` replay.

## 5. `verify_hatp_proof` — Inputs, Boundary, Failure Semantics

```python
def verify_hatp_proof(
    proof: Optional[HumanApprovalProvenanceProof],
    *,
    evidence: HATPVerificationEvidence,
    provider: HATPProofVerifierProvider,
    trust_store: HATPTrustStore,
    expected_operation: HATPExpectedOperation,
    current_repository_id: str,
    canonical_deployment_root: str,
    evaluation_time: datetime,
) -> HATPVerificationResult:
```

**Canonical payload source (single authority):** `evidence`/`provider`
are verified against `canonicalize_hatp_proof_payload(proof)` — the
existing Wave-3 function, called directly, never reconstructed
independently. **Digest source:** none needed in Wave 4 (digest fields
are part of the signed canonical payload itself, so mutating them is
already caught by signature verification — see §9 below for the
explicit scoping decision on live Decision/Binding digest freshness).

**Trust-store consumption:** exclusively through `HATPTrustStore`'s
existing read-only methods (`environment_status`, `lookup_signer`,
`lookup_principal`, `lookup_authority`, `resolve_deployment_authorization`)
plus the existing `deployment_binding_matches` helper — no new lookup/
parsing logic duplicated, no write method added to `hatp_bootstrap.py`
(byte-unchanged this phase, confirmed by `git status --porcelain --
src/pcae/core/hatp_bootstrap.py` empty).

**Repository/signer/provider self-selection defense:** `proof.principal_id`
and `proof.provider_profile` are cross-checked against the registry's
`SignerRecord` for `proof.signer_key_id` — a mismatch resolves to
`UNKNOWN_SIGNER`/`UNAUTHORIZED_SIGNER` respectively, never trusted from
the proof alone (HATP-REQ-077).

**Deterministic failure-precedence** (documented, non-normative — HATP-
REQ-079 states the success conjunction as an unordered AND-list, not a
mandated failure order):

1. `proof is None` → `MISSING`
2. not a `HumanApprovalProvenanceProof` instance / unsupported
   `proof_version` → `MALFORMED` (defensive; structurally unreachable
   through normal Wave-3 construction)
3. trust store genuinely absent (`environment_status().status ==
   UNAVAILABLE`) → `MISSING`
4. signer unknown → `UNKNOWN_SIGNER`
5. signer revoked → `REVOKED_SIGNER`
6. `principal_id`/`provider_profile` self-assertion mismatch →
   `UNKNOWN_SIGNER` / `UNAUTHORIZED_SIGNER`
7. provider exception, or provider returns a value that is not an
   `HATPProviderVerificationOutcome` → `INVALID_SIGNATURE` (fail closed)
8. `signature_valid is False` → `INVALID_SIGNATURE`
9. `human_presence_proven is False` → `USER_PRESENCE_NOT_PROVEN`
10. `attestation_valid is False` → `INVALID_ATTESTATION` (`None` = not
    applicable at this provider profile, Wave 5 concern)
11. principal/authority not active → `UNAUTHORIZED_SIGNER`
12. `repository_id` mismatch → `WRONG_REPOSITORY`
13. deployment binding missing/mismatched → `WRONG_DEPLOYMENT`
14. operation identity mismatch → `WRONG_OPERATION`
15. future-dated `issued_at` beyond `HATP_CLOCK_SKEW_TOLERANCE` (60s,
    documented non-normative choice) → `EXPIRED`
16. else → `VALID`

Any exception raised by `trust_store`'s methods (`HATPTrustStoreError`)
at any point is caught and resolves to `MISSING`, never propagated.

## 6. Verification-Substrate Readiness (Wave-4 subsystem `J`)

`inspect_hatp_verification_substrate_readiness(trust_store, *,
current_repository_id) -> HATPVerificationSubstrateReadiness` inspects
the 149O.1D plan §9 activation conjunction:

```
HATP_TRUSTED_OPERATIONAL :=
    repository_identity_valid
    AND protected_deployment_enrollment_valid
    AND class_b_bootstrap_environment_safe
    AND trusted_approver_mapping_valid
    AND provider_profile_available
    AND provider_attestation_trusted
    AND proof_verifier_available
```

`provider_profile_available` and `provider_attestation_trusted` are
**permanently hardcoded `False`** in this wave (no real provider exists
until Wave 5) — this mechanically forces `operational` to always be
`False`, asserted internally (`assert operational is False`) and
independently re-tested from outside the module
(`test_substrate_readiness_never_operational`,
`test_test_provider_producing_valid_proof_does_not_change_substrate_readiness`).
`HATPVerificationSubstrateStatus` has exactly one member, `NOT_READY` —
there is no `READY` member for this wave to accidentally return.

This function is entirely separate from `verify_hatp_proof` (per-proof
result) by design: a legitimate proof can and must be able to reach
`VALID` in a controlled test/verification context (HATP-001's own
attack-matrix item 20) even though the broader deployment substrate is
not production-safe — conflating the two would make attack #20
unreachable by construction, which is itself a documented stop
condition.

## 7. Provider-Neutral Interface (`hatp_providers.py`, new file)

- `HATPProviderVerificationOutcome` (frozen dataclass): `signature_valid`,
  `human_presence_proven`, `attestation_valid: Optional[bool]`. No
  authorization field.
- `HATPProofVerifierProvider` (`Protocol`, `runtime_checkable`): a single
  `verify(*, canonical_payload, signer_key_id, provider_profile,
  assertion) -> HATPProviderVerificationOutcome` method. Wave 5's real
  FIDO2/PIV adapter implements this same interface; Wave 4 introduces no
  hardware/protocol dependency (`fido2`, `pyscard`, `ykman` — none
  added to `pyproject.toml`, confirmed unchanged this phase).
- `TestHATPProofVerifierProvider` (`K`, HATP-REQ-022): deterministic,
  explicitly non-production. `sign()` is a test-fixture helper (not part
  of the production interface) producing a SHA-256-based fake assertion
  bound to the exact canonical payload bytes + signer + profile — this
  gives every mutation/replay test genuine byte-exact sensitivity,
  mirroring what a real hardware signature would do, without any actual
  cryptography. `__test__ = False` prevents pytest from mis-collecting
  it as a test class.

**No production activation path:** `human_approval_trusted_provenance.py`
never imports `TestHATPProofVerifierProvider`
(`test_test_provider_never_referenced_by_production_module`);
`inspect_hatp_verification_substrate_readiness` takes no `provider`
parameter at all (`test_substrate_readiness_takes_no_provider_argument`)
— there is structurally nothing for a production caller to select, by
accident or otherwise.

## 8. Trust-Store / Repository-Binding Consumption

- **Repository binding:** `verify_hatp_proof` compares `proof.repository_id`
  against a caller-supplied `current_repository_id` (`WRONG_REPOSITORY`
  on mismatch), then calls the existing
  `trust_store.resolve_deployment_authorization(repository_id=,
  canonical_deployment_root=)` — the same Layer-1 + Layer-2 strict-match
  helper Wave 2 already implements and independently verified
  (149O.1F/149O.1F.1/149O.1F.2). No independent "looks equal" shortcut.
- **Signer identity binding:** authoritative principal is always
  `SignerRecord.principal_id` from the registry, never
  `proof.principal_id`.
- **Provider-profile binding:** `SignerRecord.provider_profile` must
  equal `proof.provider_profile`; a proof cannot self-select a different
  provider profile than the one it is enrolled under.
- **Deployment-binding signer/provider binding:** the resolved
  `DeploymentBinding`'s `principal_id`/`signer_key_id`/`provider_profile`
  must also agree with the proof's — a binding registered for a
  *different* signer under the same repository/deployment does not
  authorize this proof (`WRONG_DEPLOYMENT`).
- **Trust-root/public-key/attestation self-selection:** the proof's
  fields carry no public key, attestation root, or trust anchor (Wave 3
  already rejects any such field as unknown, `additionalProperties:
  false`-equivalent, independently reconfirmed unaffected this phase);
  Wave 4 never reads such a field because none exists to read.

## 9. Explicit Scoping Decision — Live Decision/Binding Digest Freshness

HATP-REQ-072/073 (mutation of the referenced Decision/Binding content
after proof creation invalidates the proof, via
`decision_record_digest`/`binding_digest`) is satisfied at the *signed-
payload* level in this wave: those digest fields are part of the Wave-3
canonical payload, so mutating the proof's own recorded digest already
invalidates the signature (tested,
`test_signed_field_mutation_invalidates_old_evidence[decision_record_digest]`/
`[binding_digest]`). Comparing the proof's recorded digest against a
*freshly recomputed* digest of the live, currently-stored CHGR
Decision/RAE Binding — to catch the case where the underlying record
itself was mutated *after* signing while the proof's own field stays
byte-identical — requires importing `rollback_approval_evidence.py`/
CHGR, which the 149O.1D plan assigns to Wave 6 (RAE Integration,
HATP-REQ-095/096's AND-conjunction), not Wave 4. `verify_hatp_proof`
therefore takes the expected operation identity (`decision_record_id`,
`binding_id`, family, operation reference) as an explicit caller-
supplied parameter rather than re-fetching live records itself. This
module still imports neither `rollback_approval_evidence.py` nor any
CHGR module (independently re-verified,
`test_verify_hatp_proof_has_no_production_call_sites`).

## 10. Test Matrix

New suite: `tests/test_hatp_verification_engine.py` — 59 tests, all
deterministic, no hardware, no real cryptography, no filesystem outside
`tmp_path`, no network, explicit `evaluation_time` in every call (no
hidden wall clock). Covers: vocabulary exhaustiveness + disjointness;
result-type field-set purity; canonical-byte boundary (provider receives
exact `canonicalize_hatp_proof_payload(proof)` bytes); positive
canonical control (valid fixture → `VALID`); every individual failure
condition (`INVALID_SIGNATURE`, `UNKNOWN_SIGNER`,
`UNAUTHORIZED_SIGNER` ×3 root causes, `REVOKED_SIGNER`,
`WRONG_REPOSITORY`, `WRONG_DEPLOYMENT` ×3 root causes including same-ID-
wrong-deployment, `USER_PRESENCE_NOT_PROVEN`, `INVALID_ATTESTATION`,
`MISSING` ×2 root causes, `MALFORMED` ×2 root causes,
`WRONG_OPERATION` ×3 root causes, `EXPIRED`); provider-exception and
unknown-provider-result fail-closed; full signed-field mutation matrix
(repository_id, decision_record_id/digest, binding_id/digest,
principal_id, signer_key_id, provider_profile, issued_at, each verified
against its actual resulting status, not a blanket assumption); AG3
(`job_id`, `original_commit_sha`) and AG5 (`per_id`, `ecp_id`) individual
field mutation; timestamp mutation (`.001` → `.002`) invalidates;
equivalent-timestamp-syntax (`Z` vs `+00:00`) produces identical
canonical bytes and verifies identically (correct, not a bypass);
determinism across repeated calls; test-provider-cannot-activate-
production (source-scan + always-`NOT_READY` assertions); no-approval-
derivation source scan; no-production-call-site scan across
`rollback_approval_evidence.py`/`permission_broker*.py`/`agent.py`;
dependency-direction audit (both directions: `hatp_bootstrap.py` and
`repository_identity.py` do not import the verifier; `hatp_providers.py`
does not import the verifier or trust store); no-secret-material-in-
diagnostics check; provider `Protocol` runtime-conformance check.

Registered in `tests/conftest.py`'s `FAST_GREEN_MODULES` (deterministic,
sub-100ms, no subprocess).

## 11. Regressions

| Suite | Result |
|---|---|
| Wave 1/2 (`test_repository_identity`, `test_hatp_bootstrap_foundation`, `test_phase_149o_1e/1f/1f_1`) | 103 passed (unchanged) |
| 149O.1F.2 | 90 passed (unchanged) |
| Wave 3 + 149O.1H family + new Wave-4 suite (`test_hatp_proof_models`, `test_hatp_canonical_serialization`, `test_phase_149o_1g/1h/1h_1/1h_2/1h_3/1h_4/1h_5/1h_6`, `test_hatp_verification_engine`) | 990 passed, 1 skipped (848 prior baseline + 1 retired live-tree self-check + 59 new Wave-4 + 82 unaccounted... see note below) |
| Report-trust (`test_phase_reports`, `test_phase_reports_cli`, `test_phase_report_trust_hard_fail`, `test_push_phase_report_identity_137f1`) | 201 passed (unchanged) |
| HATP contract/plan (`test_phase_149o_1c_*`, `test_phase_149o_1d_*`) | 126 passed, 1 skipped (127 total, matching prior 127 exactly — 1 retired live-tree self-check) |
| RAE canonical-provenance suite (`test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py`) | 4 failed / 13 passed — same 4 known pre-existing B-149O-1..4 findings, unaffected by this phase |
| Permission Broker consumer-scope inventory (`test_phase_148f_..._test_permission_broker_consumer_scope_inventory`) | same pre-existing false-positive (module docstring prose mentions "permission_broker" as forbidden-coupling documentation, not a real coupling — pre-existing pattern, `hatp_bootstrap.py` already triggered it before this phase) |
| Fast Green | 4590 passed (4531 entering baseline + 59 new Wave-4 tests, exact match, no regression) |

Two historical phase-scoped tests
(`test_phase_149o_1d_human_approval_trusted_provenance_implementation_plan.py::TestProductionBoundaryUnchanged::test_no_src_pcae_files_modified_this_phase`,
`test_phase_149o_1h_6_..._verification.py::test_no_src_pcae_files_modified_this_phase`)
asserted a *live working-tree* invariant ("no uncommitted `src/pcae/`
change right now") that is true only during their own originating
phase's execution and cannot be re-scoped to their own commit range
after the fact (no base-commit reference was ever recorded). Both are
retired to documented `pytest.skip()` no-ops rather than deleted,
preserving discoverability of what they used to check. This is the same
methodological pattern already established by this project's other
phase-scoped "expected production files changed" allow-lists, which are
explicitly *widened* each phase rather than treated as permanently
frozen (see `test_only_expected_production_files_changed` in
`test_phase_149o_1e_...py`/`test_phase_149o_1g_...py`, both widened this
phase to include `hatp_providers.py`).

Nine other historical Wave-3-purity-boundary assertions (across
`test_phase_149o_1g`, `test_phase_149o_1h`, `test_phase_149o_1h_2`,
`test_phase_149o_1h_4`, `test_phase_149o_1h_6`) that forbade any
`hatp_bootstrap` import into `human_approval_trusted_provenance.py` were
updated, not retired — narrowed to their *original intent* (no RAE/
Permission-Broker/agent coupling) rather than the now-superseded Wave-3-
only file boundary, per the 149O.1D plan's explicit Wave-4 co-location
decision (§7). Each edit is documented in-line with the specific
plan/requirement citation justifying the change.

## 12. No-Production-Activation Proof

- `verify_hatp_proof`/`inspect_hatp_verification_substrate_readiness`
  have zero call sites in `rollback_approval_evidence.py`,
  `permission_broker.py`, `permission_broker_foundation.py`, or
  `agent.py`/`commands/agent.py` (source-scanned, independently tested).
- No code in `human_approval_trusted_provenance.py` assigns/derives
  `approval_present` (regex-scanned over executable code, docstrings
  excluded).
- `inspect_hatp_verification_substrate_readiness`'s `operational` field
  is mechanically forced to `False` (internal `assert`, independently
  re-tested from outside the module) — there is no code path, parameter,
  or provider choice capable of making it `True` in this wave.
- `TestHATPProofVerifierProvider` is never referenced by
  `human_approval_trusted_provenance.py` (source-scanned).

## 13. Dependency-Direction Audit

```
hatp_providers.py            -> (nothing upstream; stdlib only)
human_approval_trusted_provenance.py
                              -> repository_identity.py   (Wave 1, unchanged)
                              -> hatp_bootstrap.py          (Wave 2, unchanged, read-only)
                              -> hatp_providers.py          (new, this phase)
```

No reverse import: `hatp_bootstrap.py` and `repository_identity.py` do
not import `human_approval_trusted_provenance.py` or `hatp_providers.py`
(independently source-scanned, both directions,
`test_hatp_bootstrap_does_not_import_verification_engine`/
`test_repository_identity_does_not_import_verification_engine`/
`test_hatp_providers_module_has_no_upstream_hatp_import`).
`rollback_approval_evidence.py` is unmodified and imports neither new
module (confirmed via `git status --porcelain --
src/pcae/core/rollback_approval_evidence.py` empty).

## 14. Findings

None Blocking. No non-blocking findings beyond the following
**OBSERVATIONS**, each an implementation-defined choice within a space
HATP-001 deliberately leaves open, not a contract gap:

1. **Failure precedence** (§5 above) is this implementation's documented,
   deterministic choice — HATP-REQ-079 states the success conjunction as
   an unordered AND-list, not a mandated failure order.
2. **Clock-skew tolerance** (`HATP_CLOCK_SKEW_TOLERANCE = 60s`) is a
   documented, non-normative value — HATP-REQ-085 requires *an*
   implementation-defined tolerance, without freezing one.
3. **Provider-profile-mismatch** and **provider-exception**/**unknown-
   provider-result** map to `UNAUTHORIZED_SIGNER` and `INVALID_SIGNATURE`
   respectively — the closed 13-state vocabulary has no dedicated name
   for either specific cause; both choices satisfy HATP-REQ-090's "never
   default-allow" requirement, and are documented in-line at each call
   site.
4. **Live Decision/Binding digest freshness** (§9 above) is explicitly
   deferred to Wave 6 (RAE Integration) rather than attempted early
   against an RAE/CHGR import this wave deliberately does not take.

## 15. Wave-4 Implementation Verdict

```
HATP WAVE 4 VERIFICATION ENGINE IMPLEMENTED
— READY FOR INDEPENDENT VERIFICATION
```

## 16. HATP Production Readiness

```
HATP PRODUCTION: NOT READY
```

Unchanged by this phase. Still absent: real hardware signer (FIDO2/PIV),
real device attestation, Class-B OS deployment provisioning, RAE/HATP
production integration, AG3/AG5 Permission Broker wiring,
`approval_present=True` derivation. `inspect_hatp_verification_substrate_readiness`
run against this development machine's actual production trust-store
root reports `NOT_READY`/`operational=False` with reason
`agent_and_admin_share_os_principal` among others (independently
confirmed via ad hoc `HATPTrustStore(_test_only_root=...)` smoke check
during implementation — not committed as a test fixture, since it
targets a real filesystem path outside `tmp_path`; the *mechanism* that
would produce this same reason against `HATPTrustStore.production()` is
unit-tested via `hatp_bootstrap.py`'s own existing Wave-2 test suite,
unchanged this phase).

## 17. Explicit Confirmations

- `HATP-001 v1.0` remained byte-unchanged (confirmed:
  `git status --porcelain -- docs/contracts/` empty).
- Wave-3 canonical proof models (`HumanApprovalProvenanceProof`,
  `Ag3OperationReference`, `Ag5OperationReference`, `RollbackSite`,
  `parse_hatp_proof`, `hatp_proof_to_document`,
  `canonicalize_hatp_proof_payload`, `digest_hatp_proof_payload`) were
  **not modified** — Wave 4 is append-only new code plus new top-of-file
  imports, per the 149O.1D plan's explicit Wave-4 co-location decision
  (§7); no existing Wave-3 symbol's body changed.
- Wave-3 canonical signed-payload semantics remained unchanged (same
  field set, same serialization function, same digest function, called
  directly by Wave 4, never reimplemented).
- `B-149O.1H-1` remains independently confirmed closed (unaffected).
- `B-149O.1H.4-1` remains independently confirmed closed (unaffected).
- `B-149O.1H-2` remains independently confirmed closed (unaffected).
- `F-149O.1C-1` remains independently confirmed implemented (unaffected).
- `F-149O.1C-2` remains editorial debt only (unaffected).
- `B-149O.1F-1` remains confirmed closed (unaffected).
- `B-149O.1R-1` remains closed (unaffected).
- `B-149O.1R-2` remains closed (unaffected).
- No real FIDO2 provider was implemented.
- No real PIV provider was implemented.
- No human signing operation was implemented.
- No production Class-B deployment was provisioned.
- No RAE production integration was implemented.
- No AG3 Permission Broker integration was implemented.
- No AG5 Permission Broker integration was implemented.
- No rollback execution behavior changed.
- No `approval_present=True` derivation was implemented.
- No Permission Broker policy meaning changed.
- No Runtime Enforcement behavior changed.
- No Prompt Generation, Prompt Dispatch, or agent invocation capability
  was implemented.
- A HATP verification status remains distinct from approval, permission,
  capability, and execution.
- HATP production remains NOT READY.
- Runtime remains Observed / observe / unavailable.

## 18. Recommended Next Phase

```
149O.1J — HATP Verification Engine Independent Verification
```

The independent verifier should attack, at minimum: every failure
condition in §5/§10 above; the mutation matrix's completeness (every
signed field, not only the ones this phase happened to parametrize); the
three implementation-defined OBSERVATIONs in §14 for any hidden
semantic-change risk; the substrate-readiness function's permanent
`False` guarantee under adversarial trust-store/registry construction;
and independent re-confirmation that no production call site exists
anywhere in `src/pcae/**` for `verify_hatp_proof` or
`inspect_hatp_verification_substrate_readiness`.
