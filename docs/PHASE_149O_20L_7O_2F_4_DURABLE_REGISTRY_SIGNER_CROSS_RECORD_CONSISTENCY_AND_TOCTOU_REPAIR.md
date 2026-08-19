# Phase 149O.20L.7O.2F.4 — Durable-Registry Signer Cross-Record Consistency and TOCTOU Repair

**Date:** 2026-08-19  
**Mode:** governed narrow repair  
**Phase-entry commit:** `a11087483a77ce646a848d8ac9cd47598089d78f`  
**Verdict:** **DURABLE-REGISTRY SIGNER CROSS-RECORD CONSISTENCY AND TOCTOU REPAIR IMPLEMENTED — INDEPENDENT VERIFICATION PENDING**

## 1. Result

The Model-B signing consumer now rejects inconsistent durable authority
state before any hardware interaction and compares a complete immutable
authority-state snapshot immediately before publication. The two
Blocking findings from 2F.3 are repaired, not self-closed:

- **B-149O.20L.7O.2F.3-1 — REPAIRED; INDEPENDENT VERIFICATION PENDING;
  NOT CLOSED.** A binding/signer principal conflict now raises
  `no_authorized_signer` before `request_signature()` and publishes
  nothing.
- **B-149O.20L.7O.2F.3-2 — REPAIRED; INDEPENDENT VERIFICATION PENDING;
  NOT CLOSED.** A signer/provider conflict now has the same pre-touch,
  zero-publication result.

BF-1 and BF-2 remain **INDEPENDENTLY CONFIRMED CLOSED AT THE HATP
TRUST-ENROLLMENT / SIGNING IMPLEMENTATION BOUNDARY**. The repair does not
call `credential_identity()`, does not change non-resident enrollment,
and does not change Model B.

## 2. Governance and fixed baseline

Entry was clean on `main`, `origin/main..HEAD = 0`, with canonical 2F.3
complete and 2F.4 planned. Runtime was and remains **Observed / observe /
unavailable**. The exact entry commit was frozen in a detached worktree:

`/tmp/pcae-149o-20l-7o-2f-4.2aqaJa/entry`

No stash was used. The repository `.venv` was used for both trees.

## 3. Contracts and primary-source derivation

Entering versions were HSCE-001 v1.2, HPSE-001 v1.1, HHCE-001 v1.1,
HBDC-001 v1.2, and HATP-001 v1.0. Primary-source reconstruction found:

- HSCE-REQ-018 makes the durable binding plus active PrincipalRecord,
  SignerRecord, HardwareCredentialRecord, and matching provider profile
  the canonical signer source.
- HSCE-REQ-024 already requires any missing active record or provider
  mismatch to fail `no_authorized_signer`.
- HPSE defines a signer as one key enrolled under exactly one principal
  and provider; HPSE-REQ-062 makes SignerRecord plus
  HardwareCredentialRecord the joint durable signer identity.
- HBDC producer checks prevent new inconsistent records, but the signing
  consumer cannot treat producer validation as proof that historical
  persisted state remains coherent.
- HSCE-REQ-080's six-step text omitted the signer principal/profile and
  record-key equality predicates even though REQ-018/024 required them.
- HSCE-REQ-083 required full resolution to run twice but explicitly made
  only `(principal_id, signer_key_id)` differences dispositive. It was
  genuinely ambiguous for same-identity authority changes.

Therefore HSCE-001 is minimally clarified to **v1.3**. Only
HSCE-REQ-080 and HSCE-REQ-083 change in place; the mechanically extracted
sequence remains exactly `001..084`, with no additions, removals, gaps,
or renumbering. REQ-080 states the already-normative cross-record
predicates. REQ-083 now compares the complete semantic resolution
snapshot. No other contract is amended.

## 4. Production repair scope

Exactly one production file changed:

- `src/pcae/core/hatp_signing_ceremony.py`

No provider, registry reader/writer, deployment producer, bootstrap,
proof verifier, CLI, script, runtime, Permission Broker, or certification
source changed.

`HATPSignerResolution` is the one new internal frozen type. It captures:

- repository identity and canonical deployment root;
- resolved production provider profile;
- complete DeploymentBinding;
- complete SignerRecord;
- complete PrincipalRecord;
- complete HardwareCredentialRecord.

Frozen dataclass equality is semantic field equality. It neither compares
mutable object identity nor invents a registry version field.

## 5. Initial consistency matrix

| Relationship/state | Enforcement | Failure timing |
|---|---|---|
| repository + canonical root → active binding | existing `resolve_deployment_authorization` Layer 1/2 check | pre-touch |
| binding provider = selected production provider | existing, retained | pre-touch |
| binding signer key = SignerRecord key | added explicit consumer check | pre-touch |
| binding principal = SignerRecord principal | added explicit consumer check | pre-touch |
| signer provider = binding/selected provider | added explicit consumer check | pre-touch |
| binding principal = PrincipalRecord identity | added explicit consumer check | pre-touch |
| binding signer key = HardwareCredentialRecord key | added explicit consumer check | pre-touch |
| credential provider = binding/signer/selected provider | existing check, now part of four-way consistency | pre-touch |
| binding/signer/principal/credential active | existing checks retained | pre-touch |

Missing, revoked, malformed, wrong-repository, wrong-root, conflicting,
or inaccessible state fails closed. The consumer never repairs,
normalizes, rewrites, or guesses historical state.

## 6. Historical malformed-state reproduction after repair

Tests construct real schema-valid `registry.json` documents that current
writers cannot create:

1. binding principal A, signer key K owned by principal B;
2. FIDO2 binding/credential, signer key K with provider `PIV`.

The real `HATPTrustStore` parser accepts both documents as schema-valid.
The repaired signing resolver rejects each with `NoAuthorizedSignerError`
before the synthetic provider boundary. Assertions prove zero hardware
requests and zero envelope files.

## 7. State revalidation across the operation boundary

The ceremony captures `HATPSignerResolution` before preview/touch, reruns
the identical six-step resolution after the provider returns, and compares
the complete value before envelope construction/publication. A failed
second resolution or unequal snapshot becomes
`EvidenceSerializationFailureError`; the candidate assertion is discarded.

Serial defensive cases prove zero publication after:

- binding signer rotation;
- binding principal change with a still-resolvable signer;
- signer principal or provider change;
- principal, signer, or credential revocation;
- credential provider change;
- binding provider change;
- same-identity binding `authority_scope` or `valid_from` rewrite;
- same-ID credential public-key rewrite.

Repository identity is independently reread through the existing signing
context comparison; canonical deployment root and the complete binding
are included in the signer snapshot.

## 8. Hardware and authority boundary

The production success path still requires exactly one
`Fido2HardwareProvider.request_signature()` call. Registry records do not
produce a signature. A valid registry with provider unavailability
publishes nothing. The existing real FIDO2 verifier test rejects a
non-matching synthetic credential assertion. The coherent synthetic
end-to-end path still publishes and cryptographically verifies an
assertion against the intended durable COSE public key and UP flag.

Thus registries resolve/constrain governance identity; hardware alone
proves possession and signs. Neither substitutes for the other.

## 9. BF-1/BF-2 regression

An AST caller inventory over every production Python file reports zero
calls to `credential_identity()`. Remaining occurrences are only the
provider protocol declaration and FIDO2/PIV method definitions/comments.

`Fido2HardwareProvider.enroll_credential()` remains unchanged and omits
CTAP2 `options`/`rk`, producing a non-resident credential. Signing still
passes the durable hexadecimal signer key as the explicit CTAP2
`allow_list` credential ID. The full real-writer/non-resident synthetic
test from 2F.3 remains green.

## 10. Production call graph

```text
pcae.cli.main
  -> commands.hatp.run_hatp_sign_rollback
  -> production_sign_rollback_evidence
  -> sign_rollback_evidence
     -> resolve_signing_context
        -> live AG3 job / AG5 PER
        -> live RAE Decision + RollbackApprovalBinding
        -> repository identity
     -> HATPTrustStore.production
     -> create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)
     -> _resolve_deployment_binding_signer
        -> resolve_canonical_deployment_root
        -> resolve_deployment_authorization(repository_id, root)
        -> binding/provider check
        -> active SignerRecord + key/principal/provider checks
        -> active PrincipalRecord + identity check
        -> active HardwareCredentialRecord + key/provider checks
        -> HATPSignerResolution snapshot A
     -> render preview / explicit confirmation
     -> canonicalize_hatp_proof_payload
     -> Fido2HardwareProvider.request_signature(explicit signer_key_id)
     -> resolve_signing_context again
     -> _resolve_deployment_binding_signer again → snapshot B
     -> compare context A/B and signer snapshots A/B
     -> build_hatp_signed_evidence_envelope
     -> HATPEvidenceStore.publish
```

Provider construction is inert; device enumeration/touch occurs only in
`request_signature()` after all initial consistency checks and preview.

## 11. Defensive and bounded test results

- new 2F.4 defensive file: **30 passed**;
- signing + 2F.2 + converted 2F.3 repair regressions + 2F.4: **117 passed**;
- Surface B-E core bounded regression: **100 passed**;
- broader affected suite: **661 passed, 2 skipped, 13 failed**.

The broader affected entry worktree produced **631 passed, 2 skipped,
13 failed** against the same nine pre-existing test modules. Exact JUnit
comparison: 13/13 identical non-passing node IDs, zero net-new, zero
fixed. All 13 are pre-existing stale historical source/contract-scope
assertions, one Python-3.11 expectation under the required Python 3.9
environment, or an obsolete pre-HATP-consumption call-site assertion.

## 12. Fast Green exact-node comparison

Fixed entry:

`8160 passed, 4 skipped, 304 failed, 9 errors, 26902 deselected`

Current pre-commit:

`8138 passed, 4 skipped, 326 failed, 9 errors, 26932 deselected`

The 30 additional deselections are exactly the new non-marker repair
tests, run directly. JUnit comparison found 22 net-new failed nodes and
zero new errors. Every node was inspected: all 22 are historical tests
whose own phase contract asserts that `src/pcae` or contract files are
unchanged/clean in the current working tree. They are expected stale
phase-identity assertions for this authorized production+contract repair,
not functional failures. They span phases 149O.1G, 149O.14, 149O.17,
149O.19.4/19.5E.4, 149O.20A/20C/20D/20D.1/20E/20H/20K/20K.1/20L.1,
149O.20L.7D.9/10, and 149O.20L.7E. No unexplained functional node was
introduced. A committed-source rerun is recorded before finalization.

## 13. Interpreter/environment

The repository `.venv` uses Python 3.9.6, pytest 8.4.2, fido2 1.2.0,
and cryptography 44.0.3. Both baseline and current runs use that same
environment with `PYTHONPATH` pointed at their own source root.

## 14. HMIC consequence

Current HMIC v1.4 binds 30 files and five contract identities.
`hatp_signing_ceremony.py` remains creation-side and is not presently
HMIC-bound; its output receives no verification trust credit and is
revalidated by the frozen consumption chain. Its transitive
authority-sensitive dependencies (trust reader, credential reader,
provider/verifier, proof/envelope/evidence store, repository identity,
RAE and agent record readers) are already bound where they affect
consumption authority.

HSCE contract bytes are already in the 30-file implementation digest,
and `derive_contract_versions()` now mechanically returns
`HSCE-001: 1.3`; no contract-version-set member is added by this phase,
but the existing HSCE member changes `1.2 → 1.3`. No certification exists
to revoke, and no HMIC amendment/certification is performed.

The prior future alignment candidate remains 30→34 files and five→seven
contracts: add the hardware-credential and principal/signer writer
modules plus HHCE-001 v1.1 and HPSE-001 v1.1 contract bytes/versions.
Its HSCE member must now be v1.3, not v1.2. Independent verification of
this repair remains the immediate prerequisite before HMIC alignment.

## 15. Findings and dispositions

Blocking findings: none newly discovered.

Non-Blocking findings: none newly discovered. The 2F.3 tuple-only
binding and same-ID credential rewrite observations are resolved by the
v1.3 semantic snapshot, pending independent verification.

- BF-1: independently confirmed closed at the implementation boundary.
- BF-2: independently confirmed closed at the implementation boundary.
- B-149O.20L.7O.2F.3-1: repaired, IV pending, not closed.
- B-149O.20L.7O.2F.3-2: repaired, IV pending, not closed.
- Overall 2F.2 repair: remains not independently verified until 2F.5.

## 16. No-go confirmations

No physical hardware was provisioned or touched. No real credential was
registered. No real principal or signer was enrolled. No real
DeploymentBinding was created. No Dell or Protected Root state was
mutated. No election or CHGR was initiated. No HMIC amendment,
certification, or activation occurred. No Permission Broker, runtime,
PIV, or Stream-B action occurred.

## 17. Completion and next phase

Phase-owned commits, pushed status, final `origin/main..HEAD`, and
canonical report identity are recorded through the governed completion
lifecycle.

The exact recommended next phase is:

**149O.20L.7O.2F.5 — Durable-Registry Signer Cross-Record Consistency and
TOCTOU Repair Independent Verification**

This phase does not begin or authorize 2F.5.
