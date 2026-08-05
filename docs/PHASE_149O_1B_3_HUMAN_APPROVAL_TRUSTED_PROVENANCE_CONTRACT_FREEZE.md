# Phase 149O.1B.3: Human Approval Trusted Provenance Contract Freeze

**Phase type:** normative Human Approval Trusted Provenance contract
freeze. No implementation, no `src/pcae/**` change, no repository
identity implementation, no OS changes, no ACL/sudoers change, no
hardware signer/provider implementation, no approver registry
implementation, no `rollback_approval_evidence.py` change, no AG3/AG5
wiring, no Permission Broker change, no POL-004 change, no Runtime
Enforcement change.

**Status:** completed. **Freeze verdict: HATP-001 v1.0 FROZEN — HUMAN
APPROVAL TRUST BOUNDARY COMPLETE.**

## 1. Starting Position (independently reconfirmed)

- `git status --short`: clean. `git status --branch --short`:
  `## main...origin/main`. `git rev-list --count origin/main..HEAD`: 0.
- Latest completed phase: 149O.1B.2 — **CANONICAL REPOSITORY IDENTITY
  ARCHITECTURE DEFINED — READY TO RESUME HATP CONTRACT FREEZE**, commit
  `2034bdc0`, pushed (finalization commits `aa1119c1`, `3a8bdf3b`).
- `pcae health`: healthy, all required files present, git status clean,
  agent lock held by `claude-local`, session continuity verified.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: clean, no inconsistencies.
- `pcae push check`: nothing to push (branch main, working tree clean,
  0 unpushed commits, health healthy, check passed, task memory clean,
  phase report trust passed, phase report identity passed).
- `pcae runtime inspect`: Runtime state Observed, execution capability
  unavailable, maximum plugin capability observe, registry empty,
  0 plugins, 0 capabilities, Permission Broker status
  `execution_unavailable`, governance posture non-executing — unchanged.
- `source ~/.config/pcae/telegram.env` then `pcae notify status`:
  Telegram sink available/configured/enabled, token and chat ID
  present, auto-finalization hook available with `telegram` configured
  sink — unchanged from prior phases.
- `pcae phase-report show --latest`: 149O.1B.2's canonical report,
  recommending 149O.1B.3 as next phase — consistent.
- `pcae phase-report reconcile --phase-id 149O.1B.2`: reconciled, 1
  generation promoted, marker `already_dispatched`, checkpoint
  completed, receipt finalized, mutation none (inspection only).

## 2. Architecture Baseline Confirmed Not Reopened

Per the governing prompt, the following selections from 149O.1A,
149O.1B, 149O.1B.1, and 149O.1B.2 are frozen inputs to this phase and
are **not reopened**:

- **Root 1 (Proof Production):** HATP Model A — hardware-backed
  external signing key, non-exportable, fresh physical human-presence
  event per approval proof.
- **Root 2A (Device/Provider Genuineness):** externally anchored
  provider/device attestation; proves hardware class only, not
  identity/authority.
- **Root 2B (Bootstrap/Authorization Authority):** Bootstrap Model
  Class B, separate OS security context; v1 two-principal topology
  (Agent OS principal; Human/Admin OS principal combining
  human-approver and bootstrap-administrator roles).
- **Repository scope:** CRI Model A, two-layer model — Layer 1,
  repository-local random `repository_id` (no authority by itself);
  Layer 2, admin-owned protected deployment binding (the sole source of
  repository-scoped authority).
- **Deployment status:** current repository deployment remains NOT
  READY (same OS user for human and agent). This does not block
  contract freeze; it blocks operational enablement.
- **B-149O-1 through B-149O-4:** remain OPEN, unchanged.

This phase's entire job was the one prerequisite chain 149O.1A/149O.1B/
149O.1B.1/149O.1B.2 built toward but did not close: freezing the actual
normative HATP-001 contract text now that all three trust roots and the
repository-identity dependency are architecturally resolved.

## 3. Primary-Source Reconstruction

All four architecture documents and the RAE-001 contract were read in
full (not summarized from phase-report prose) before drafting HATP-001:

- `docs/PHASE_149O_1A_HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT_AND_TRUST_BOUNDARY_ARCHITECTURE.md`
  (556 lines) — Threat A definition, HATP Model A selection, the two
  trust roots, `HumanApprovalProvenanceProof` conceptual shape, the
  proof-payload field table, the verification-status vocabulary, the
  repository-binding deferral, the bootstrap-trust open questions.
- `docs/PHASE_149O_1B_HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT_FREEZE.md`
  (524 lines) — the three-mechanism bootstrap investigation (distinct
  OS user: absent; external KMS: absent; GitHub review gate:
  structurally insufficient), Bootstrap Model Class B selection, the
  mandatory bootstrap-trust-statement template (all fields "not yet
  true"), the B-149O finding-cause mapping.
- `docs/PHASE_149O_1B_1_HUMAN_APPROVAL_BOOTSTRAP_AUTHORITY_ARCHITECTURE.md`
  (925 lines) — the three-principal naming, the two-principal v1
  decision, the same-user challenge (No), the filesystem/trust-store
  ownership model, the root-termination statement, the enrollment and
  approval workflows, the repository-identity BLOCKING flag.
- `docs/PHASE_149O_1B_2_CANONICAL_REPOSITORY_IDENTITY_ARCHITECTURE.md`
  (571 lines) — the required-identity-properties list, the rejected
  candidate survey, CRI Model A selection, the two-layer model, the
  three mandatory security statements, the worktree/single-ID decisions,
  the `.pcae/.gitignore` observation, the contract-ownership decision,
  the HATP-freeze-readiness YES answer.
- `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md` (1052 lines)
  — exact field names reused by reference in HATP-001's canonical
  payload (`governance_record_reference.record_id`/`record_digest`,
  `evidence_id`, `rollback_operation_reference`, `job_id`/
  `original_commit_sha` for AG3, `per_id`/`ecp_id` for AG5,
  `expires_at` 24h TTL), the `RAE-REQ-###` numbering convention mirrored
  by `HATP-REQ-###`, and the closing-section order
  (Findings/Blocking-Condition Check/Versioning/Verdict/Readiness
  Status/Next Phase) mirrored in HATP-001's own closing sections.

Compatibility contracts were independently re-verified by direct header
read (not trusted from phase-report prose): RAE-001 v1.0 FROZEN,
CHGR-001 v1.3 FROZEN, IWC-001 v1.2 FROZEN, RWMPC-001 v1.0 FROZEN
(partial coverage, unrelated to HATP), PBPA-001 v1.0 FROZEN, PBPC-001
v1.2 FROZEN (amended, unrelated finding closed), TAMC-001 v1.0 FROZEN,
TAMPC-001 v1.1 FROZEN, AESIC-001 v1.3 FROZEN, AEM-001 v1.0 FROZEN. None
required amendment.

## 4. Contract Artifact

`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` was
created this phase. Identity: **HATP-001**, canonical title "Human
Approval Trusted Provenance Contract", **Version 1.0**, **Status:
FROZEN**. 47 numbered sections (Purpose through Recommended Next Phase),
matching or exceeding the governing prompt's 35-section minimum list —
the additional sections (Root Architecture Summary, Verification-Time
Trust Boundary, Open Rollback-Evidence Findings, Repository Identity
Contract Ownership, Current Deployment Readiness, Threat-Capability
Matrix, Mandatory Future Acceptance Attack Matrix, Compatibility
Reconfirmation, Full Requirement Traceability, Blocking-Condition
Check, Requirement Sequence Verification) were added to keep every
governing-prompt item (1-141) traceable to an exact section rather than
folding unrelated content into the minimum list's section names.

## 5. Requirement Inventory

`HATP-REQ-001` through `HATP-REQ-117` inclusive: 117 sequential
normative requirements, no gaps, no duplicates, one per normative
sentence or closed table (verified by direct grep count, §11 below).
Every mandatory item from the governing prompt's numbered list
(1-141) is covered by at least one requirement or an explicit frozen
table (canonical payload field table §20, verification vocabulary §22,
threat-capability matrix §38, acceptance attack matrix §39,
blocking-condition check §42).

## 6. Proof Model

`HumanApprovalProvenanceProof`, `proof_version = 1`, binding:
`principal_id`, `signer_key_id`, `provider_profile`, `repository_id`,
`decision_record_id`/`decision_record_digest` (reusing RAE-001's
`governance_record_reference`), `binding_id`/`binding_digest` (reusing
RAE-001's `evidence_id` and the Binding record's own content-integrity
digest), `rollback_site` (AG3 | AG5, family-locked), the AG3 pair
(`job_id`, `original_commit_sha`) or the AG5 pair (`per_id`, `ecp_id`),
`issued_at`, `proof_version`. The raw canonical local deployment path is
explicitly excluded from the portable proof — deployment verification
happens separately via the protected registry (HATP-REQ-070).

## 7. Bootstrap Model

Bootstrap Model Class B frozen: two-principal v1 topology (Agent OS
principal; Human/Admin OS principal). Trusted bootstrap store:
Human/Admin-owned, agent-unwritable, protected at file and
parent-directory level (mutation, replacement, unlink, rename,
parent-directory replacement, permission weakening, ACL modification).
Self-enrollment, verifier-key replacement, and registry deletion are
each frozen as denied-by-OS-boundary, not application convention
(HATP-REQ-040, HATP-REQ-041, HATP-REQ-042).

## 8. Repository Identity and Deployment Binding

CRI Model A frozen as HATP's repository-scope dependency (HATP-REQ-046).
`repository_id` (Layer 1) is not a credential, not authority-bearing,
not caller-selectable (HATP-REQ-047, HATP-REQ-051). The protected
deployment binding (Layer 2) is the sole source of repository-scoped
authority (HATP-REQ-052). Every copy/clone/fork/worktree/rename/restore/
reidentity scenario from the governing prompt (§53-§67) is frozen with
an explicit expected outcome (HATP-REQ-055 through HATP-REQ-066).

## 9. Human-Presence and Provider Semantics

One human-presence event produces at most one proof (HATP-REQ-017).
`HATP_HARDWARE_PROVIDER_V1` is frozen as a security-property profile,
not a vendor/protocol name; FIDO2 and PIV are explicitly not declared
interchangeable, and arbitrary-payload signing is not assumed from a
protocol that does not provide it (HATP-REQ-019, HATP-REQ-020). No
software-key downgrade is permitted without explicit future-profile
support (HATP-REQ-021).

## 10. Enrollment, Authority, Rotation, Revocation

Enrollment establishes who may approve, never approves anything itself
(HATP-REQ-038). Approval-time authority mutation is forbidden
(HATP-REQ-039). Authority MUST remain valid at proof-**consumption**
time, not merely creation time (HATP-REQ-088) — re-derived and
confirmed against the governing prompt's own instruction to re-derive
before freezing (§93). Key rotation and revocation are Human/Admin-only,
never agent-driven (HATP-REQ-086, HATP-REQ-087).

## 11. Requirement Sequence Verification

```
$ grep -c '^\*\*HATP-REQ-' docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md
117
$ grep -oE 'HATP-REQ-[0-9]+' docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md | sort -u -t- -k3 -n | head -1
HATP-REQ-001
$ grep -oE 'HATP-REQ-[0-9]+' docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md | sort -u -t- -k3 -n | tail -1
HATP-REQ-117
```

No gap, no duplicate, confirmed by direct count against the file, not
narrative claim.

## 12. Compatibility Findings

- **RAE-001 v1.0: COMPATIBLE AS-IS.** HATP supplies an additional
  required condition before `approval_present` may be derived True; no
  RAE-001 field, requirement, or lifecycle rule changes.
- **CHGR-001 v1.3: COMPATIBLE AS-IS.**
- **RWMPC-001 v1.0: no amendment.**
- **PBPA-001 v1.0 / PBPC-001 v1.2: no amendment.** POL-004 continues to
  interpret the truthful `approval_present` fact only.
- **IWC-001 v1.2: no amendment.** Confirmation remains distinct from
  approval.
- **AESIC-001 v1.3 / AEM-001 v1.0: no amendment.** Remain
  disclosure-only.
- **TAMC-001 v1.0 / TAMPC-001 v1.1: no amendment.** `human_authorization`
  reused only as non-normative structural precedent, never composed.

## 13. Threat Matrix and Acceptance Attacks

Threat A frozen unchanged from 149O.1A. Threat-capability matrix (12
rows) and mandatory future acceptance attack matrix (20 attacks, each
with a stated expected outcome) are both frozen in HATP-001 §38-§39.

## 14. B-149O Findings — Future Closure Mapping

B-149O-1 through B-149O-4 **remain OPEN**. No repair attempted this
phase (architecture/contract-freeze-only scope). Closure requires HATP
implementation, RAE-001/HATP-001 integration, AG3/AG5 Permission Broker
wiring, and independent adversarial verification — none implemented
this phase. Mapping preserved verbatim from 149O.1B §12 in HATP-001
§35 (HATP-REQ-105/106).

## 15. Blocking-Condition Check

All thirteen blocking conditions from the governing prompt's list (§129)
were independently checked against HATP-001's actual requirement text
and found resolved; see HATP-001 §42 for the full table. The one
condition intentionally **not** required for contract freeze — current
live provisioning of the Class-B OS boundary — is explicitly carried
forward as NOT READY (HATP-001 §37, §42 HATP-REQ-115), consistent with
the governing prompt's own instruction that contract freeze does not
imply deployment readiness (§20, §84-§85, §125).

## 16. Freeze Verdict

```
HATP-001 v1.0 FROZEN
— HUMAN APPROVAL TRUST BOUNDARY COMPLETE
```

## 17. Production Boundary

```
$ git diff --name-only 2034bdc0..HEAD -- src/pcae/
(empty)
```

Zero `src/pcae/**` files touched this phase. Only this phase's own
contract and architecture documents under `docs/**`, task-lifecycle
files under `tasks/**`, `PROJECT_STATUS.md`, `CHANGELOG.md`, and
`.pcae/phase-completion-metadata.json` / `.pcae/phase-completion-report.md`
changed.

## 18. Existing Contract Boundary

Zero changes to RAE-001, RWMPC-001, PBPC-001, PBPA-001, CHGR-001,
IWC-001, TAMC-001/TAMPC-001, AESIC-001/AEM-001 — confirmed by
`git diff --name-only` showing no path under any of their filenames.

## 19. No OS Changes

No OS accounts created. No ACLs changed. No sudoers changed. No HATP
trust store created. No hardware device configured. Confirmed via
`git status --short` (repository-scoped) and by not having issued any
OS-administration command this phase.

## 20. Runtime Boundary

Before and during this phase: `pcae runtime inspect` confirms Runtime
state Observed, maximum capability observe, execution availability
unavailable — unchanged.

## 21. Fast Green

```
$ python -m pytest -m fast_green -n auto -q
4391 passed
```

Exact match to the entering baseline recorded by 149O.1B.2, no flake,
no new failures introduced by the two new documentation files (neither
is imported or exercised by any test collector).

## 22. Governance Validation

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae doctor task-memory`: clean. `pcae push check`: (rerun
after this phase's commits — see completion metadata for the
post-commit result). `pcae runtime inspect`: Observed / observe /
unavailable. `pcae notify status` (after sourcing
`~/.config/pcae/telegram.env`): Telegram configured/enabled/ready. All
remained clean throughout.

## 23. Implementation Readiness

```
HATP architecture:           DEFINED
HATP contract:                FROZEN (this phase)
HATP implementation:          NOT IMPLEMENTED
Class-B OS boundary:          NOT PROVISIONED
Repository identity:          NOT IMPLEMENTED
RAE / HATP integration:       NOT IMPLEMENTED
AG3 / AG5:                    UNWIRED
```

## 24. Chapter 149 Status

Still incomplete. Outstanding after this successful HATP freeze:

- HATP contract independent verification
- HATP implementation planning
- Repository identity implementation planning
- Class-B deployment implementation planning
- HATP implementation
- HATP independent verification
- RAE/HATP integration
- RAE re-verification
- AG3/AG5 integration planning
- AG3/AG5 implementation
- Integration verification
- TK1/TK2/TK3 re-affirmation

## 25. Confirmations (governing-prompt required final-report list)

- B-149O-1 through B-149O-4 remain OPEN until HATP implementation, RAE
  integration, and independent verification close them.
- No HATP production implementation was created.
- No repository-identity production implementation was created.
- No Class-B OS security boundary was provisioned.
- Current HATP bootstrap environment remains NOT READY.
- No RAE production integration was implemented.
- No AG3 Permission Broker integration was implemented.
- No AG5 Permission Broker integration was implemented.
- No rollback execution behavior changed.
- RAE-001 v1.0 remains unchanged — no Blocking incompatibility was
  found, so no amendment was needed or attempted.
- RWMPC-001 v1.0 remains unchanged. PBPC-001 v1.2 remains unchanged.
  PBPA-001 v1.0 remains unchanged. CHGR-001 remains unchanged.
- IWC confirmation remains distinct from approval. AESIC/AEM remain
  disclosure-only.
- No illegal CHGR/TAM composition was introduced.
- No POL-001..012 meaning was changed. No POL-013+ was added.
- TK1/TK2/TK3 remain deferred.
- No Runtime Enforcement behavior changed. No Prompt Generation, Prompt
  Dispatch, or agent invocation capability was implemented. Runtime
  remains Observed, maximum capability remains observe, and execution
  availability remains unavailable.

## 26. Recommended Next Phase

Per §16's clean freeze verdict and the governing prompt's own
next-phase logic (freeze succeeded; do not move directly to
implementation planning):

**149O.1C — Human Approval Trusted Provenance Contract Independent
Verification.**
