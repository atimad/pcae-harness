# Phase 149O.20L.7O.2H.3 — HMIC-001 v1.6 Paths Source-Scope Closure and Seven-Contract Ceremony Consistency Repair Independent Verification

## 1. Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — HMIC-001 v1.6 REPAIR COMPLETE.**

Phase 149O.20L.7O.2H.2's claims were not accepted as proof. This phase
independently reconstructed the historical defect at the fixed pre-repair
commit, re-extracted the current contract membership, re-walked HMIC-REQ-052
limb (d) at symbol level, exercised disposable digest and writer state, and
adversarially reconstructed the historical HMIC-REQ-145 guard.

The result is clean at the repair boundary:

- `B-149O.20L.7O.2H.1-1`: **INDEPENDENTLY CONFIRMED CLOSED AT HMIC
  SOURCE-CLOSURE / PRODUCTION-IDENTITY BOUNDARY**.
- `B-149O.20L.7O.2H.1-2`: **INDEPENDENTLY CONFIRMED CLOSED AT HMIC
  CONTRACT-CONSISTENCY / HISTORICAL-GUARD BOUNDARY**.
- `B-149O.20L.7O.2G-1`: **INDEPENDENTLY CONFIRMED CLOSED AT HMIC CONTRACT +
  PRODUCTION IDENTITY BOUNDARY**.
- `B-149O.20L.7O.2H-1` remains **INDEPENDENTLY CONFIRMED CLOSED AT HMIC
  CERTIFICATION-RECORD / CONTRACT-IDENTITY REPRESENTATION BOUNDARY**.
- BF-1 and BF-2 remain independently closed at the HATP Trust-Enrollment /
  signing implementation boundary.
- `B-149O.20L.7O.2F.3-1` and `B-149O.20L.7O.2F.3-2` remain independently
  closed at the HATP signing-consumer implementation boundary.

One new Non-Blocking repository-memory consistency finding is recorded in
§20. It does not contradict or weaken the HMIC repair.

## 2. Fixed Evidence and Environment

- Phase-entry commit: `2d1c4d583f1baa7254725ae92cc8574e49ac2063`.
- Substantive 2H.2 repair commit: `69467afb980c5ab90a18bd180ae7236d062f0e99`.
- Historical pre-2H.2 commit: `bb652aa4d18b5568e15feaf98c525ce0a6bd9a01`
  (the first parent of `69467afb`).
- Fixed worktree: detached at `bb652aa4`, outside the repository working
  tree; no stash was used.
- Platform: macOS Darwin 25.6.0, arm64.
- Interpreter: CPython 3.9.6 from `.venv/bin/python`.
- pytest: 8.4.2; pytest-xdist: 3.8.0.
- Current HMIC version: `HMIC-001 v1.6`.
- Entry state: clean `main`, `origin/main..HEAD = 0`, no active task before
  the governed 2H.3 task was opened; runtime Observed / observe / unavailable.

## 3. Historical Reproduction

Direct extraction from `bb652aa4` established:

- HMIC-001 was v1.5.
- HMIC-REQ-050 contained 26 `src/pcae/`-relative and 9 repository-root-
  relative members: 35 total.
- `_CONTRACT_IDENTITY_FILES` contained seven IDs.
- `_CONTRACT_VERSIONS_REQUIRED_KEYS` contained the same seven IDs.
- `src/pcae/core/paths.py` was absent from the frozen identity.
- normative HMIC-REQ-076 said the exact creation ceremony read “the four
  frozen contracts' own version headers,” while normative HMIC-REQ-067 said
  seven entries, no more and no fewer.
- the historical generic HMIC-REQ-145 extraction regex ran until the next
  requirement heading containing a parenthesized subtitle. HMIC-REQ-071
  through HMIC-REQ-076 have plain headings; HMIC-REQ-077 is the next matching
  parenthesized heading. The old window therefore accidentally included
  HMIC-REQ-076.

The historical 35-member digest, independently recomputed from the detached
worktree, was
`f58eacc4954ce02b752edf4507ed60afdff09a2778f90f68e6d3790cfeb4ac3f`.

## 4. Exact Historical 35-Member Set

Sorted canonical repository-relative membership:

```text
docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md
docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md
docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md
docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md
docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md
docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md
docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md
scripts/hatp_certification_admin.py
scripts/hatp_deployment_binding_admin.py
src/pcae/cli.py
src/pcae/commands/agent.py
src/pcae/core/agent.py
src/pcae/core/hatp_ag_authority.py
src/pcae/core/hatp_bootstrap.py
src/pcae/core/hatp_class_b_conformance.py
src/pcae/core/hatp_class_b_topology_verifier.py
src/pcae/core/hatp_deployment_binding_admin.py
src/pcae/core/hatp_environment_lock_verifier.py
src/pcae/core/hatp_evidence_store.py
src/pcae/core/hatp_fido2_provider.py
src/pcae/core/hatp_hardware_credential_admin.py
src/pcae/core/hatp_hardware_credentials.py
src/pcae/core/hatp_mandatory_certification.py
src/pcae/core/hatp_mandatory_cutover.py
src/pcae/core/hatp_piv_provider.py
src/pcae/core/hatp_principal_signer_admin.py
src/pcae/core/hatp_providers.py
src/pcae/core/hatp_rollback_consumption.py
src/pcae/core/hatp_signed_evidence.py
src/pcae/core/hatp_signing_ceremony.py
src/pcae/core/human_approval_trusted_provenance.py
src/pcae/core/permission_broker.py
src/pcae/core/permission_broker_foundation.py
src/pcae/core/repository_identity.py
src/pcae/core/rollback_approval_evidence.py
```

## 5. Exact Current 36-Member Set and Delta

Independent current extraction produced 27 `src/pcae/`-relative plus 9
repository-root-relative members. Every path exists, no duplicate exists,
and every historical member remains. Sorted canonical membership:

```text
docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md
docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md
docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md
docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md
docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md
docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md
docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md
scripts/hatp_certification_admin.py
scripts/hatp_deployment_binding_admin.py
src/pcae/cli.py
src/pcae/commands/agent.py
src/pcae/core/agent.py
src/pcae/core/hatp_ag_authority.py
src/pcae/core/hatp_bootstrap.py
src/pcae/core/hatp_class_b_conformance.py
src/pcae/core/hatp_class_b_topology_verifier.py
src/pcae/core/hatp_deployment_binding_admin.py
src/pcae/core/hatp_environment_lock_verifier.py
src/pcae/core/hatp_evidence_store.py
src/pcae/core/hatp_fido2_provider.py
src/pcae/core/hatp_hardware_credential_admin.py
src/pcae/core/hatp_hardware_credentials.py
src/pcae/core/hatp_mandatory_certification.py
src/pcae/core/hatp_mandatory_cutover.py
src/pcae/core/hatp_piv_provider.py
src/pcae/core/hatp_principal_signer_admin.py
src/pcae/core/hatp_providers.py
src/pcae/core/hatp_rollback_consumption.py
src/pcae/core/hatp_signed_evidence.py
src/pcae/core/hatp_signing_ceremony.py
src/pcae/core/human_approval_trusted_provenance.py
src/pcae/core/paths.py
src/pcae/core/permission_broker.py
src/pcae/core/permission_broker_foundation.py
src/pcae/core/repository_identity.py
src/pcae/core/rollback_approval_evidence.py
```

Exact set delta:

```text
+ src/pcae/core/paths.py
- (none)
```

The current working-tree digest was
`cd021db4b6b74d6d62420be7f74f3791e759a72f142ffb151640d2b88d39412f`.
The value is state-specific evidence, not a pinned expected digest.

## 6. Paths Symbol-Level Reachability and Authority Sensitivity

The independent chains are:

```text
AG3
production_sign_rollback_evidence
→ sign_rollback_evidence
→ resolve_signing_context
→ _resolve_ag3_operation
→ agent.build_rollback_review
→ HarnessPath.join
→ .pcae/remote/jobs/<job_id>.json
→ commit_sha
→ original_commit_sha in Ag3OperationReference

AG5
production_sign_rollback_evidence
→ sign_rollback_evidence
→ resolve_signing_context
→ _resolve_ag5_operation
→ agent.lookup_promotion_execution_record
→ HarnessPath.path
→ .pcae/promotion-executions/<per_id>.json
→ ecp_id in Ag5OperationReference
```

Both operation references enter the preview and signed canonical payload
before hardware touch. In a disposable fixture, changing only the reached
`HarnessPath.join` behavior redirected the AG3 job lookup from a record with
`original_commit_sha = 111...111` to one with `222...222`. The independently
recomputed historical 35-member digest remained identical because paths.py
was not a historical member. This reproduces `B-149O.20L.7O.2H.1-1` without
using 2H.2's test or report.

With the current 36-member identity, two unchanged derivations were equal;
a disposable bytes-only paths.py mutation changed the digest. The real
working tree was never mutated.

## 7. Complete Limb-(d) Closure

Fresh AST and symbol-level inspection classified reached production source:

- **BOUND:** signing ceremony, `agent.py`'s two operation-record readers,
  trust-store/DeploymentBinding readers, repository identity, rollback
  approval evidence, HATP proof canonicalization, hardware-provider
  selection and FIDO2/PIV provider implementations, hardware-credential
  reader, evidence envelope/store, both Trust-Enrollment writers, the shared
  DeploymentBinding registry writer primitives, and `paths.py`.
- **JUSTIFIABLY NON-AUTHORITY:** `provenance.py`, reached only after each
  writer's durable mutation and readback to append audit evidence.
- **JUSTIFIABLY NON-AUTHORITY:** `git_status.py::read_git_branch` and
  `tasks.py::find_latest_active_task`, reached only inside provenance event
  construction to populate audit metadata.
- **MISSING / BLOCKING:** none.

The two writer docstrings name future standalone Protected Admin scripts,
but `scripts/hatp_hardware_credential_admin.py` and
`scripts/hatp_principal_signer_admin.py` do not exist; there is no live
caller source omitted from the current closure.

The three exclusions were challenged experimentally. Two disposable
credential registrations were run with different `read_git_branch` and
`find_latest_active_task` behavior. Their durable
`hardware-credentials.json` bytes were identical; only audit metadata could
differ. `append_provenance_event` has neither protected registry root as an
input and runs only after the locked write/readback completes. These symbols
do not gate, select, validate, or change a credential, Principal, Signer,
provider, signing context, or protected registry record.

## 8. Contract/Production and Seven-Contract Equality

The exact HMIC-REQ-050 literal set equals production
`_frozen_canonical_paths()` entry-for-entry after canonicalization, not merely
by count. Presentation semantics also agree: 27 source-relative entries are
prefixed with `src/pcae/`; the 9 other entries remain repository-root
relative.

`_CONTRACT_IDENTITY_FILES` and `_CONTRACT_VERSIONS_REQUIRED_KEYS` are exactly
the same seven-ID set:

```text
HATP-001 HBDC-001 HHCE-001 HMRC-001 HPSE-001 HSCE-001 RAE-001
```

Live derived versions were:

```text
HATP-001 1.0
HBDC-001 1.2
HHCE-001 1.1
HMRC-001 1.1
HPSE-001 1.1
HSCE-001 1.3
RAE-001 1.0
```

The derive→CertificationRecord parse→serialize→parse round trip succeeded.
Missing HBDC, HPSE, or HHCE was rejected independently; an unknown eighth
entry was rejected. The certification admin's `certify` path calls
`derive_contract_versions` and supplies its complete result to
`CertificationRecord`; no four/five/six-member truncation exists.

## 9. HMIC-REQ-076 and Contract Consistency Sweep

Historical v1.5 HMIC-REQ-076 was genuinely normative: “Certification
creation proceeds exactly,” followed by step 4's four-contract instruction.
It contradicted normative HMIC-REQ-067's seven-entry closed set.

Current v1.6 HMIC-REQ-076 requires reading each of the exact seven bound
contracts' own live version headers. HMIC-REQ-067, HMIC-REQ-069,
HMIC-REQ-103 step 10, `derive_contract_versions`, CertificationRecord, and
the certification admin ceremony all agree.

The whole-document count sweep classified occurrences as follows:

- current normative: 36 frozen files and seven `contract_versions` entries;
- historical-version context: four under v1.0/v1.1, five under v1.2, 35
  under v1.5, and older 24/25/28/30-member phase histories;
- non-normative analysis/attack rows: legacy replay cases and prior-phase
  mechanics;
- current stale/incorrect normative occurrence: none.

## 10. Historical Guard Reconstruction and Verification

The guard originated in Phase 149O.20L.7L.6 and protected the exact
HMIC-REQ-145 repaired closure text established at commit `85616f4b`. The old
generic regex required the next requirement heading to contain a
parenthesized subtitle. It therefore included the neighboring HMIC-REQ-071
through HMIC-REQ-076 text and stopped only before HMIC-REQ-077.

Independent adversarial tests proved the repaired guard:

1. exact historical HMIC-REQ-145 bytes pass unchanged;
2. mutation inside the protected HMIC-REQ-145 text fails equality;
3. mutation only to neighboring HMIC-REQ-076 leaves the HMIC-REQ-145
   equality unchanged.

The test diff changes only extraction boundaries. The baseline commit
`85616f4b`, exact expected HMIC-REQ-145 bytes, and equality assertion remain
unchanged. No expected bytes were repinned, and no mutation within
HMIC-REQ-145 was newly accepted. The guard repair is not evidence laundering.

## 11. v1.5 → v1.6 and Production Diff Classification

The contract change is additive:

- source-scope membership: add unchanged `core/paths.py`;
- closure semantics: name the exact reached `HarnessPath.join`/`.path`
  chains in HMIC-REQ-052(d);
- ceremony semantics: replace the stale four-contract HMIC-REQ-076 phrase
  with the exact seven-contract live-header rule;
- count consequences: 26+9=35 becomes 27+9=36;
- explanatory/history: v1.6 amendment record, attack 43, and §60;
- editorial: count/version cross-references aligned to v1.6.

No authority requirement is weakened, no member is removed, contract
identity remains seven, and no readiness or activation semantic is added.

The substantive production diff changes only
`src/pcae/core/hatp_mandatory_certification.py`: it appends
`"core/paths.py"` and updates its literal cardinality/self-description.
`src/pcae/core/paths.py` is byte-identical from pre-repair to repair commit.
Signing, enrollment, DeploymentBinding, readiness, and Permission Broker
source are unchanged.

## 12. Old Certification Invalidation and Self-Binding

A disposable active CertificationRecord containing the current seven
contract identities but a 35-member implementation digest was validated
against current source. Repository/deployment/status checks were made valid;
the first failure was HMIC-REQ-103 step 9:
`CertificationStatus.IMPLEMENTATION_MISMATCH`. The old identity cannot be a
valid v1.6 identity. No real certification state was used or created.

`src/pcae/core/hatp_mandatory_certification.py` remains frozen. Two
unchanged disposable derivations were identical; a bytes-only mutation of
that file changed the digest. No cache or self-exemption was observed.

## 13. Class-B and Signing/Trust-Enrollment Preservation

All five requested Class-B members remain frozen:

- `hatp_class_b_topology_verifier.py`
- `hatp_environment_lock_verifier.py`
- `hatp_class_b_conformance.py`
- `hatp_deployment_binding_admin.py`
- `scripts/hatp_deployment_binding_admin.py`

CBV-S1 remains satisfied at its established source-binding boundary.

Bounded current regression: 128 passed across the signing ceremony,
FIDO2 signing-time credential repair, cross-record conflict repair, durable
registry TOCTOU repair, and their independent verification suites. It
confirmed zero production `credential_identity()` use, non-resident
enrollment, exact signer-key lookup, binding/signer-principal conflict and
signer/provider conflict failure before hardware touch, and post-touch
authority-state revalidation. Fresh disposable 2H.3 tests additionally
registered a HardwareCredential, enrolled a Principal, and enrolled its
Signer successfully. DeploymentBinding producer source is byte-unchanged.

## 14. Fresh Independent Test Suite

New suite:

```text
tests/test_phase_149o_20l_7o_2h_3_hmic_paths_source_scope_and_seven_contract_consistency_independent_verification.py
30 passed in 1.50s
```

It covers the 29 required areas, including the three exclusion
classifications and a separate disposable writer-path case. It imports or
copies no 2H.2 test helper.

## 15. Fixed/Current Focused Comparison

Identical 12-node selection in both trees:

```text
fixed bb652aa4: 12 passed, FAILED = {}, ERROR = {}
current:        12 passed, FAILED = {}, ERROR = {}
current-only FAILED/ERROR = {}
fixed-only FAILED/ERROR = {}
```

The nodes cover BF-1/BF-2, revoked signer/principal, provider-profile
mismatch, both 2F.3 Blocking repairs, post-touch semantic snapshot, and the
HMIC-REQ-145 guard.

## 16. Fast Green

Fast Green was run sequentially, never concurrently with another full
campaign. Two current runs reproduced the same raw result:

```text
current: 8278 passed, 326 failed, 9 errors, 4 skipped, 105 warnings
fixed:   8271 passed, 305 failed, 9 errors, 4 skipped, 105 warnings
```

Unique failed/error node counts: current 335, fixed 314. Delta: 22
current-only and 1 fixed-only.

The 22 current-only nodes were inspected individually:

- 21 are historical phase-boundary tests whose names/assertions explicitly
  demand v1.5, 35/26+9, paths non-membership, the stale four-contract phrase,
  or pre-repair 2H.1 findings. Their failure is the intended consequence of
  the v1.6 repair, not a new functional regression.
- `tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`
  timed out at 15 seconds. Isolated rerun also timed out at 15 seconds. The
  underlying command completed in 16 seconds and reported the one pre-existing
  tampered shell-audit record among 178,889 records. No shell-gate or CLI
  production source changed in the repair window.
- The one fixed-only node was a clean-HEAD/origin assertion; the governed
  current task necessarily makes the current worktree dirty while verification
  artifacts are authored.

Raw Fast Green is non-green. Attributable new functional regression count:
**zero**.

## 17. No Authority Upgrade

Read-only Git diffs, runtime inspection, and disposable-state boundaries
confirmed:

- no HMIC certification or active pointer was created;
- no certification was activated;
- no FIDO2/PIV device provisioning or real credential registration occurred;
- no real Principal or Signer enrollment occurred;
- no real DeploymentBinding was created;
- no Dell or Protected Root state was mutated;
- no readiness integration or HATP activation occurred;
- no Permission Broker or execution-capability code changed;
- no PIV or Stream-B work occurred.

Runtime remains **Observed / observe / unavailable** with zero runtime
plugins.

## 18. Finding Adjudication

### B-149O.20L.7O.2H.1-1

Historical omission and authority sensitivity were reproduced; current
membership and digest sensitivity were independently proven; the complete
limb-(d) closure has no remaining missing authority source.

**INDEPENDENTLY CONFIRMED CLOSED AT HMIC SOURCE-CLOSURE /
PRODUCTION-IDENTITY BOUNDARY.**

### B-149O.20L.7O.2H.1-2

Historical normative contradiction was reproduced; current seven-contract
semantics are consistent; no other current normative contradiction remains;
the historical guard retains its exact intended invariant.

**INDEPENDENTLY CONFIRMED CLOSED AT HMIC CONTRACT-CONSISTENCY /
HISTORICAL-GUARD BOUNDARY.**

### B-149O.20L.7O.2G-1

Exact source/content identity, transitive limb-(d) closure, seven contract
contents, seven version identities, and production equality are complete.

**INDEPENDENTLY CONFIRMED CLOSED AT HMIC CONTRACT + PRODUCTION IDENTITY
BOUNDARY.**

### Other prior findings

`B-149O.20L.7O.2H-1`, BF-1, BF-2,
`B-149O.20L.7O.2F.3-1`, and `B-149O.20L.7O.2F.3-2` remain independently
closed at their previously stated boundaries.

## 19. Final Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — HMIC-001 v1.6 PATHS SOURCE-SCOPE
CLOSURE AND SEVEN-CONTRACT CEREMONY CONSISTENCY REPAIR COMPLETE.**

This verdict verifies the repair only. It is not certification,
provisioning, readiness, activation, or execution authority.

## 20. New Non-Blocking Finding and Exact Next Phase

`NB-149O.20L.7O.2H.3-1` — **CBV-S10 status is inconsistent in current
repository memory.** The authoritative current-phase narrative and late HMIC
history carry “CBV-S10 remains OPEN,” while PROJECT_STATUS's completed Phase
149O.20L.4 record says all 18 closure criteria passed and CBV-S10 was
independently confirmed closed at the readiness-contract + production-
integration boundary; live production also contains that integration. This
does not affect HMIC v1.6 source/contract identity, so it is Non-Blocking for
2H.3. It does make immediately choosing certification, provisioning, or
activation from summary memory unsafe.

Other prerequisites remain real regardless of that documentary discrepancy:
no real HMIC certification, credential, Principal, Signer, or
DeploymentBinding exists; the selected Class-B environment is not proven
ready here; HATP is not active.

Exact recommended next phase:

**149O.20L.7O.2I — HATP Remaining-Prerequisite State and Sequencing
Reconciliation.** Analysis/reconciliation only: re-derive the current status
of CBV-S10 and every remaining certification, Class-B, Trust-Enrollment,
DeploymentBinding, readiness, and activation prerequisite from live primary
contracts/source/protected-state observations; publish one exact ordered
governed sequence. Do not certify, provision, enroll, create a
DeploymentBinding, integrate readiness, or activate HATP in that phase.

## 21. Commits and Push State

Phase-owned governed commits through evidence publication:

```text
88dba687  independently verify HMIC v1.6 repair
1ac1951d  record independent verification evidence
f8b37477  commit independent verification artifacts
9466a8a1  publish independent verification evidence
aa9ed273  reconcile completion metadata
3c6e0a24  close evidence publication task
33bb49cc  prepare pending push metadata
c0ed7aeb  complete pending report evidence
6a0c650a  stage pending canonical report
a2aac7db  open governed push finalization
```

The governed push completed through `a2aac7db`; `origin/main..HEAD = 0`
at promotion preflight. Final local report-promotion bookkeeping follows the
same governed lifecycle. No raw `git commit` or `git push` is used.
