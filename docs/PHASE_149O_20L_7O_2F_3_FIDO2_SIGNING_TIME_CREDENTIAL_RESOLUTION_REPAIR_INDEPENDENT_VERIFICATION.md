# Phase 149O.20L.7O.2F.3 — FIDO2 Signing-Time Credential Resolution Repair Independent Verification

**Date:** 2026-08-19  
**Mode:** verification-only  
**Phase-entry commit:** `ba904f19342453e0de21771a02e45206b81e6048`  
**Pre-repair commit used for historical reproduction:** `55d7ca8b9160595e03cd6a1d0a74bdade5f4ce16`  
**Verdict:** **NOT VERIFIED — NEW SIGNING-AUTHORITY DEFECT**

## 1. Executive result

The two original failure mechanisms were independently reproduced and
their narrow repairs were confirmed:

- **BF-1 — INDEPENDENTLY CONFIRMED CLOSED at the signing-time
  credential-identity dependency boundary.** No production caller of
  `credential_identity()` remains. The current signing path resolves an
  explicit credential ID from durable state and reaches the FIDO2
  `request_signature()` boundary without calling that unavailable method.
- **BF-2 — INDEPENDENTLY CONFIRMED CLOSED at the HATP trust-enrollment /
  signing implementation boundary.** `enroll_credential()` still creates
  a non-resident credential, but `request_signature()` uses the explicit
  durable `signer_key_id` in CTAP2 `allow_list`; a fresh independent
  real-writer end-to-end test produced and cryptographically verified a
  signed envelope.

The repair as a whole is nevertheless **not verified**. Two new Blocking
signing-authority defects were independently demonstrated. The repaired
resolver accepts schema-valid historical/inconsistent trust state where:

1. `DeploymentBinding.principal_id != SignerRecord.principal_id`; or
2. `SignerRecord.provider_profile` differs from the binding, credential,
   and resolved production provider.

In both failure-handling scenarios the resolver touches the provider and publishes an
envelope instead of failing `no_authorized_signer` before touch. The
normal producer prevents creating these states today, and downstream
`verify_hatp_proof()` rejects the resulting envelope, so no valid HATP
authority is obtained. That downstream defense does not satisfy the
signing contract's pre-touch fail-closed obligation and does not make an
unauthorized hardware touch plus publication acceptable.

No production repair was attempted. A separately governed repair phase
is required.

## 2. Governance and entering state

Initial state was independently inspected before work:

- branch `main`, clean at entry;
- `origin/main..HEAD = 0`;
- exact entry commit `ba904f19342453e0de21771a02e45206b81e6048`;
- no active governed phase, only the post-2F.2 idle task;
- `pcae health` healthy, `pcae check` passed, status coherent, push clean;
- Telegram configured and enabled;
- runtime unchanged: **Observed / observe / unavailable**,
  `execution_unavailable`, non-executing;
- no production `DeploymentBinding` and no production hardware credential.

The idle task was transitioned through `pcae task transition` to the
2F.3 task. `pcae phase start --agent-id codex-local` then refused a
duplicate acquisition because the immediately preceding governed handoff
had already transferred and retained the `codex-local` lock. Health/check
recognized the exact 2F.3 active task with that lock held.

An isolated detached worktree was created at the exact entry commit:

`/tmp/pcae-149o-20l-7o-2f-3.IIzK8i/baseline`

Historical BF-1 reproduction used a second detached worktree at
`55d7ca8b`; git stash was not used as the baseline mechanism.

## 3. Contracts and version identity

Entering contract versions were proven directly:

| Contract | Version | Requirement sequence |
|---|---:|---:|
| HPSE-001 | 1.1 | `001..074`, sequential |
| HHCE-001 | 1.1 | `001..052`, sequential |
| HSCE-001 | 1.2 | `001..084`, sequential |
| HBDC-001 | 1.2 | `001..076`, sequential |

The fixed v1.1→v1.2 HSCE diff is 278 insertions and 11 deletions.
v1.1 SHA-256 is
`f5d5943667acd0b46ff9976fa1e18629baf849bad5cd1d3b7fc7f1aac4b8d2a2`;
v1.2 SHA-256 is
`dc6a6235970e0a0a5cbbfd1e4cf2508fc8b02041c136c4c95cd9de08138cbcde`.
The only existing requirement identities changed were:

- HSCE-REQ-018 — proof signer source moved to durable binding state;
- HSCE-REQ-024 — unauthorized-signer and profile mismatch conditions;
- HSCE-REQ-047 — explanatory text for the unchanged error/exit pairing;
- HSCE-REQ-078 — requirement count.

New requirements are exactly HSCE-REQ-080..084. No requirement was
removed or renumbered. HPSE, HHCE, and HBDC were byte-unchanged by 2F.2.

Two contract findings remain relevant:

- HSCE-REQ-024 requires provider-profile mismatch at the resolved record
  checks to fail, but HSCE-REQ-080 step 4 only requires signer status and
  omits the signer's principal/profile relationships. The implementation
  follows the weaker step and violates REQ-024.
- HSCE-REQ-083 deliberately compares only the re-resolved
  `(principal_id, signer_key_id)` pair. It does not bind a complete
  `DeploymentBinding` version/digest or credential-record identity.

## 4. Production call graph

The actual production path, reconstructed from parser registration and
call sites rather than symbol-name search, is:

```text
pcae.cli.main
  -> pcae hatp sign rollback parser handler
  -> commands.hatp.run_hatp_sign_rollback
  -> production_sign_rollback_evidence                 (zero overrides)
  -> sign_rollback_evidence
     -> resolve_signing_context
        -> live AG3 job / AG5 PER
        -> live RAE Decision + Binding
        -> repository identity
     -> HATPTrustStore.production
     -> create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)
     -> _resolve_deployment_binding_signer
        1. resolve_canonical_deployment_root
        2. resolve_deployment_authorization(repository_id, root)
        3. compare DeploymentBinding provider profile
        4. lookup active SignerRecord
        5. lookup active PrincipalRecord
        6. lookup active HardwareCredentialRecord + profile
     -> render preview and require human confirmation
     -> canonicalize_hatp_proof_payload
     -> Fido2HardwareProvider.request_signature(explicit signer_key_id)
     -> re-resolve operation context
     -> re-run signer resolution and compare identity tuple
     -> build_hatp_signed_evidence_envelope
     -> HATPEvidenceStore.publish

Later authority consumption:
  -> verify_hatp_proof
     -> live signer/principal/authority/DeploymentBinding cross-checks
     -> Fido2HardwareProvider.verify
        -> credential ID, type, origin, challenge, RP hash
        -> durable COSE public key signature
        -> authenticator UP bit
```

The creation-side signing orchestrator intentionally does not call
`verify_hatp_proof`; stored envelope existence is not authority. The
downstream frozen verifier is the authority checkpoint.

## 5. BF-1 historical reproduction and current-path proof

At `55d7ca8b`, the actual `_resolve_signer` body was executed with the
real `Fido2HardwareProvider`. It called `credential_identity()` and
raised:

```text
ProviderUnavailableError
  caused by HATPProviderUnavailableError:
  credential_identity() requires ... a discoverable/resident credential
```

Trust lookup and `request_signature()` were never reached. This is the
original BF-1 failure class, demonstrated behaviorally rather than
inferred from a call token.

Against current source, the full orchestrator resolved the binding's
credential ID, called `request_signature()` exactly once with that ID,
published an envelope, and recorded zero `credential_identity()` calls.
An AST caller inventory of every production `.py` file found zero calls.
The only remaining occurrences are:

| Location | Classification |
|---|---|
| `hatp_providers.py` | interface declaration |
| `hatp_fido2_provider.py` | unconditional-unavailable concrete method |
| `hatp_piv_provider.py` | deferred/unavailable placeholder |

No signing, enrollment, certification, HATP verification, or other
authority-bearing production caller remains. BF-1's exact dependency is
therefore closed.

## 6. BF-2 reproduction and non-resident proof

The current `enroll_credential()` CTAP2 `make_credential` call passes no
`options`/`rk` argument; the enrolled credential is unambiguously
non-resident (`rk=false` default). The current FIDO2 signing method takes
an explicit hexadecimal `signer_key_id`, decodes it, and supplies it as
the sole CTAP2 `get_assertion(... allow_list=[credential])` entry. No
resident discovery occurs.

The independent end-to-end verification used:

```text
real Fido2HardwareProvider.enroll_credential (mocked HID/CTAP transport)
  -> real register_credential
  -> real enroll_principal
  -> real enroll_signer
  -> real create_deployment_binding
  -> real sign_rollback_evidence
  -> real Fido2HardwareProvider.request_signature
     (mocked physical CTAP response signed by an in-memory EC private key)
  -> real HATPEvidenceStore publication/load
  -> real Fido2HardwareProvider.verify against registered COSE public key
```

The assertion was cryptographically valid, payload/challenge-bound, and
carried the UP flag. This independently proves BF-2's non-resident shape
is compatible with Model B.

## 7. DeploymentBinding resolution and deterministic selection

The protected registry parser rejects duplicate `DeploymentBinding`
records for one `repository_id`; the producer also rejects a second
conflicting binding. `resolve_deployment_authorization` requires active
status plus exact repository ID and canonical deployment root. Multiple
unrelated active `SignerRecord`s introduce no first-match behavior:
lookup is by the one binding's exact `signer_key_id`.

Defensive checks confirmed fail-closed handling for no binding, revoked/wrong-root binding,
duplicate binding, missing/revoked signer, missing/revoked principal,
missing/revoked credential, binding profile mismatch, credential profile
mismatch, and registry parse/access failure. These fail before
`request_signature()`.

The resolver did **not** preserve all trust relationships, however. It:

```python
signer = lookup_signer(binding.signer_key_id)
principal = lookup_principal(binding.principal_id)
...
return signer.principal_id, signer.signer_key_id
```

It never checks signer principal equality or signer profile equality.

## 8. Blocking findings

### B-149O.20L.7O.2F.3-1 — binding/signer principal conflict accepted

A valid chain was produced using real writers, then the schema-valid
registry was rewritten to model historical corruption: binding principal
A, signer key K enrolled to principal B, both principals active. The real
parser accepted the state and the resolver returned `(B, K)`. The full
orchestrator touched the provider and published an envelope.

This means governance identity is not actually resolved exclusively from
the binding as HSCE-REQ-018/080 claim. It also violates the required
historical/malformed-state fail-closed and blind-touch ordering.

**Disposition:** Blocking. No repair performed.

### B-149O.20L.7O.2F.3-2 — SignerRecord provider mismatch accepted

With a FIDO2 binding and FIDO2 credential but a schema-valid active
SignerRecord carrying a PIV profile, the resolver returned success. The
full orchestrator touched the FIDO2 provider and published an envelope.
This directly violates HSCE-REQ-024's requirement that a provider-profile
mismatch at the resolved records fail `no_authorized_signer`.

**Disposition:** Blocking. No repair performed.

Downstream `verify_hatp_proof()` rejects both envelopes, so neither scenario
creates valid operational authority. The defects remain Blocking at the
signing implementation boundary because the ceremony performs a physical
touch and publishes evidence for a state its own contract says is
unauthorized.

## 9. Hardware possession and registry-only defense

Model B only chooses identity. The production zero-override CLI still
constructs the real production provider. The sole success path calls
`request_signature()` exactly once; registry records alone cannot bypass
that call. With provider unavailability injected at the transport
boundary, no envelope was published.

FIDO2 signs a WebAuthn assertion over a SHA-256 challenge derived from
the exact canonical proof payload. Verification independently checks
credential ID, client-data type/origin/challenge, RP ID hash, signature
against the durable COSE key, and fresh user presence. An assertion from
another credential was rejected. A fake or malformed registry-only
assertion may be structurally stored by the creation-side envelope store,
but cannot become `VALID` at authority consumption.

## 10. Blind-touch and fail-closed ordering

Valid current-state ordering is context → binding/signer/credential
resolution → preview → explicit confirmation → hardware touch. Missing,
duplicate, revoked, wrong-repository/root, unsupported/mismatched binding
or credential state fails before touch.

The two Blocking cross-record gaps violate this property: inconsistent
principal or signer-profile state reaches touch and publication. Thus the
six nominal steps occur in the documented order, but the step predicates
are incomplete.

## 11. State revalidation across the operation boundary

The production orchestrator re-resolves operation context and reruns
signer resolution after the provider returns, before envelope publication.
Independent state-change scenarios produced these results:

| Mid-ceremony change | Result |
|---|---|
| Binding rotates A→B | candidate discarded, no publication |
| Principal revoked | discarded |
| Signer revoked | discarded |
| Credential revoked | discarded |
| Credential provider profile changed | discarded |
| Binding provider profile changed | discarded |
| Non-matching synthetic credential assertion | verifier rejects |
| Same signer/principal, binding authority field rewrite | accepted/published |
| Same credential ID/profile, public key rewrite | accepted/published; later verification fails |

HSCE-REQ-083 literally requires comparison only of the identity tuple, so
same-identity binding rewrites are a contract gap as well as an
implementation observation. HBDC rotation changes `valid_from` even when
identity is unchanged, but HSCE carries no binding version/digest.

## 12. Non-Blocking findings

- **NBF-1 — tuple-only binding recheck.** Same-identity binding authority
  rewrites are invisible. A repair phase must explicitly decide whether
  to bind the entire authority-relevant record or declare exact permitted
  same-identity transitions; tuple equality must not be assumed sufficient.
- **NBF-2 — credential-record identity race.** A same-ID/profile public-key
  rewrite is not detected before publication. Consumption rejects the old
  signature against the new key, preventing authority, but the ceremony
  stores unusable evidence after touch.
- **NBF-3 — HSCE text drift.** §46's migration paragraph says no production
  CLI exists, despite the live `commands/hatp.py`/`cli.py` wiring.
  HSCE-REQ-082 also cites REQ-013 for exactly-one touch although REQ-027 is
  the relevant possession requirement.

## 13. Surfaces B–E regression

The independent Surface B–E suite passed:

```text
126 passed in 3.62s
```

This covered HHCE registration/revocation/idempotency/conflict/locking;
Principal/Signer enrollment and continuous two-lock ordering; Principal
`revoked_at` parsing; and DeploymentBinding producer cross-validation,
round trip, concurrency, rotation, and revocation. A separately selected
35-node exact surface slice also passed (`35 passed in 0.83s`).

The producer correctly prevents the two inconsistent states found above.
The defect is the signing consumer's failure to defend against historical
or schema-valid inconsistent state, not a regression in Surfaces B–E.

## 14. Interpreter and focused verification

- `.venv/bin/python`: Python 3.9.6
- `pytest`: 8.4.2
- `fido2`: 1.2.0
- `cryptography`: 44.0.3
- affected FIDO2/signing/enrollment/binding collection: 460 tests

New independent file:

`tests/test_phase_149o_20l_7o_2f_3_independent_verification.py`

Result: `18 passed in 0.40s`. It does not import the 2F.2 phase test
module and contains historical execution, current closure, real-writer
cryptographic end-to-end, malformed-state, blind-touch, TOCTOU,
wrong-authenticator, and both Blocking reproductions.

Broader affected regression initially produced nine failures; one was a
transient task-contract syntax error introduced during phase setup and
was corrected, after which health/check and that node passed. The
remaining exact eight nodes all reproduced at the untouched phase-entry
commit: six obsolete Wave-5 source/contract/non-integration assertions,
one Python-3.11 assertion under the repository's intended Python 3.9
venv, and one obsolete pre-HATP-consumption call-site assertion. They are
pre-existing, not 2F.3 regressions. Final broader affected result:
`564 passed, 2 skipped, 8 pre-existing failures`.

## 15. Independent Fast Green regression delta

Fixed entry worktree:

```text
8160 passed, 4 skipped, 304 failed, 9 errors, 26884 deselected
```

Current verification tree:

```text
8160 passed, 4 skipped, 304 failed, 9 errors, 26902 deselected
```

The deselection difference is exactly the 18 newly added independent
tests, which deliberately carry no inherited `fast_green` marker and were
run directly as the focused independent suite. JUnit comparison produced:

```text
baseline non-passing: 313
current non-passing:  313
net-new FAILED/ERROR node IDs: 0
fixed FAILED/ERROR node IDs:   0
```

There is therefore no net-new Fast Green regression. The 304 failures and
9 setup errors are the identical pre-existing node-ID set on both sides,
dominated by historical frozen-byte/version/current-state assertions and
the known nine HMIC scratch-tree setup errors.

Committed-source confirmation at substantive governed commit
`bb117b599a9c13d760fdfa603bd8a454b287c95e` produced:

```text
8159 passed, 4 skipped, 305 failed, 9 errors, 26902 deselected
post-commit delta vs entry: 1 net-new non-passing node
tests/.../test_head_equals_origin_main
```

That one node checks only whether the newly created governed commit has
already been pushed. It was a push-state observation, not a source or
functional regression. After the governed push, the node passed (`1
passed`). No other committed-source FAILED/ERROR node differed from
entry.

The fixed entry worktree and current tree used the same `.venv`, extras,
and explicit `PYTHONPATH` for their own source roots. No 2F.2
deselection/exclusion set was reused. Exact JUnit FAILED/ERROR node-ID
sets were derived independently and every net-new node was inspected.

## 16. HMIC transitive source and contract identity consequence

The current HMIC v1.4 identity is 30 files / five contracts:
HMRC-001 v1.1, HATP-001 v1.0, HSCE-001 v1.2, RAE-001 v1.0, and HBDC-001
v1.2. HSCE/HBDC are therefore already represented correctly.

Fresh transitive analysis found the exact missing authority surfaces:

- `src/pcae/core/hatp_hardware_credential_admin.py`
- `src/pcae/core/hatp_principal_signer_admin.py`

Their authority-affecting dependencies are already bound. Generic
`core/paths.py` and post-write audit-only `core/provenance.py` do not
change accepted registry content or verification outcomes. No companion
admin scripts exist today, so nonexistent paths are not proposed.

`hatp_signing_ceremony.py` and `commands/hatp.py` remain creation-side.
Their artifacts receive no verification trust credit and are
independently revalidated by the frozen consumption chain, so they should
not be added solely because 2F.2 changed the producer.

Exact future HMIC candidate delta:

- frozen file set **30→34**: add both writer modules plus the HHCE and
  HPSE contract documents;
- contract-version set **5→7**: add `HHCE-001: 1.1` and `HPSE-001: 1.1`;
- HMIC-REQ-053 requires those two new contract-version members' content
  bytes in `implementation_scope_digest`.

No HMIC amendment or certification was performed.

## 17. Capability status and next phase

The original credential-identity/resident-key mechanisms are repaired,
but trust-enrollment/signing implementation capability is **not complete**
because the durable resolver is not fail-closed across its cross-record
authority relationships.

Even after repair and independent verification, operational readiness
would still require real FIDO2 provisioning, credential registration,
principal/signer enrollment, a real DeploymentBinding, HMIC alignment
and independent verification, HBDC-compliant host state, certification,
and activation. None exists now.

The exact next phase is:

**149O.20L.7O.2F.4 — Durable-Registry Signer Cross-Record Consistency and
TOCTOU Repair.**

It should amend HSCE-001 to reconcile REQ-024/080, require exact
`SignerRecord.principal_id` and provider-profile equality before touch,
return the binding-authorized tuple only after those checks, explicitly
dispose of same-identity binding/credential rewrite semantics, implement
the narrow repair, and add defensive failure-handling checks. It must be followed by its own
independent verification. Only after those phases should the separate
HMIC 30→34 / five→seven alignment phase precede any real first use.

## 18. No-go and source-scope confirmation

- No production `.py` file modified.
- No script or frozen contract modified.
- No physical hardware provisioned or touched.
- No production credential registered.
- No real principal or signer enrolled.
- No real DeploymentBinding created.
- No Dell or Protected Root mutation.
- No election or CHGR publication.
- No HMIC amendment/certification.
- No Permission Broker or runtime-capability change.
- No PIV implementation.
- Stream B (`~/repos/pcae-deepseek-research`) was not touched, read, or
  awaited.
- Runtime remains **Observed / observe / unavailable**.
