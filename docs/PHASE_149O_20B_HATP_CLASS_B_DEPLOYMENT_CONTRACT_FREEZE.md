# Phase 149O.20B — HATP Class-B Deployment Contract Freeze

## 1. Charter and Mandate

Contract-freeze-only phase. Freeze, as a new bound contract (HBDC-001 v1.0), the OS-principal separation (DRA-REQ-001), Protected Root ownership/permissions (DRA-REQ-002), and the agent-environment-lock requirement (DRA-REQ-003) named by `docs/PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_ARCHITECTURE.md`, as concrete, testable normative requirements. Real Class-B provisioning and real activation remain out of scope until this phase and its own independent verification (149O.20C) exist and are independently reviewed. This phase MUST NOT modify `src/pcae/**` or `scripts/**`, provision OS principals, create real protected state, or change runtime/PB/POL-005/COMP-002.

## 2. Baseline (149O.20A Result)

Latest completed phase: 149O.20A — HATP Deployment Readiness Architecture. Status: completed, report completeness: complete. Commits: c0253d07, de944f10, 62370e56, 65fca7d9, 14aa56a8. Pushed: yes, origin/main..HEAD: 0. Result: HATP DEPLOYMENT READINESS ARCHITECTURE COMPLETE — IMPLEMENTATION VERIFIED — REAL DEPLOYMENT NOT AUTHORIZED — REAL ACTIVATION NOT AUTHORIZED. HMIC-REQ-063 disposition: OPTION C. Installation model: Model A. Deployment-readiness requirements DRA-REQ-001..003 (plus DRA-REQ-004..011) named but not yet frozen as a testable contract. All nine stop conditions (DRA-S1..S9) NOT TRIGGERED.

## 3. Initial Inspection (This Phase)

- `git status --short`: clean.
- `git log --oneline origin/main..HEAD`: empty; `git rev-list --count origin/main..HEAD`: 0.
- `pcae health`: healthy; active task at start: idle post-149O.20A; agent lock held by claude-local; git status clean.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — 5 active task files present (tasks/active/ directory-collapse, a known pre-existing repo quirk unrelated to this phase) and several `tasks/done/` entries from 149O.1H.3 through 149O.3 missing from `tasks/DONE.md` (pre-existing, historical, outside this phase's allowed-file scope, not remediated here).
- `pcae push check`: clean (nothing_to_push).
- `pcae runtime inspect`: Observed / observe / unavailable.
- `pcae notify status`: Telegram configured, enabled, ready.
- `pcae phase-report show --latest`: confirms 149O.20A completed/complete, all governance results passed, recommended next phase 149O.20B (this phase).
- `pcae phase-report reconcile --phase-id 149O.20A`: `delivery_recorded_bookkeeping_incomplete` — notification was dispatched and the canonical report is present/consistent; only receipt bookkeeping is incomplete. Non-blocking, inspection-only, no mutation performed; noted for the record and not remediated here (outside this phase's charter, which is contract-freeze only).

## 4. Primary Sources Read

Read in full: `docs/PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_ARCHITECTURE.md`; `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (HATP-001 v1.0); `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` (HMIC-001 v1.1, including the exact text of HMIC-REQ-063 and HMIC-REQ-064); `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` (HMRC-001 v1.0); `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md` (HSCE-001 v1.1); `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md` (RAE-001 v1.0); `docs/PHASE_149O_1B_1_HUMAN_APPROVAL_BOOTSTRAP_AUTHORITY_ARCHITECTURE.md`; `docs/PHASE_149O_1B_2_CANONICAL_REPOSITORY_IDENTITY_ARCHITECTURE.md`. Cross-checked against production source: `src/pcae/core/hatp_bootstrap.py`, `src/pcae/core/repository_identity.py`, `src/pcae/core/hatp_mandatory_certification.py`, `src/pcae/core/hatp_mandatory_cutover.py`. Requirements were not frozen from the 149O.20A phase-report summary alone; the architecture document, contract texts, and production source were each read directly.

## 5. Contract Identity

`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` — Contract ID **HBDC-001**, version **1.0**, status **FROZEN — PENDING INDEPENDENT VERIFICATION**. Depends on HATP-001 v1.0, HMIC-001 v1.1, HMRC-001 v1.0 (all unamended, byte-unchanged). New, dedicated requirement namespace `HBDC-REQ-###`; DRA-REQ IDs are not reused or renumbered.

## 6. DRA-REQ → HBDC-REQ Traceability

| DRA-REQ | Mapping |
|---|---|
| DRA-REQ-001 (OS-principal separation) | HBDC-REQ-001..005 |
| DRA-REQ-002 (Protected Root ownership/permissions) | HBDC-REQ-011..021 |
| DRA-REQ-003 (agent Python environment lock) | HBDC-REQ-025..041 |
| DRA-REQ-004 (agent-writable path forfeits READY) | HBDC-REQ-040 |
| DRA-REQ-006 (recertification on copy/clone/migrate/restore) | HBDC-REQ-043..046 |

## 7. Principal Model

Two OS principals frozen for v1.0, unmodified from 149O.1B.1/149O.20A: agent OS principal, admin OS principal. No third principal introduced (HBDC-REQ-001..003). Admin authority is never inferred from environment variables, function names, file ownership, or Git identity (HBDC-REQ-004); the agent has no self-elevation path (HBDC-REQ-005).

## 8. Protected Root Model

Protected Root resolves solely via `HATPTrustStore.production()`'s fixed platform paths, with no override channel (HBDC-REQ-011) and no agent-triggered auto-creation (HBDC-REQ-012). Ownership/effective-permission model frozen in HBDC-001 §11: admin ownership (HBDC-REQ-013), mode excludes group/other write consistent with the existing `0o022` check already implemented in `hatp_mandatory_cutover.py` (HBDC-REQ-014), effective group/ACL access must be tested, not just mode bits (HBDC-REQ-015/016), ancestor directories must be non-agent-writable to close the writable-parent replacement channel (HBDC-REQ-017), symlinks fail closed (HBDC-REQ-018), hard links restricted to admin (HBDC-REQ-019), and agent-side code fails closed rather than auto-provisioning (HBDC-REQ-021).

## 9. Agent/Admin Permission Model

Agent MAY read/execute/validate/inspect; MUST NOT write any authority-bearing state, with the sole carved-out exception of artifacts other bound contracts already designate agent-writable and non-authoritative (`.pcae/hatp-evidence/`, `.pcae/repository-identity.json`) (HBDC-REQ-006..008). Admin holds exclusive write authority over Protected Root, HMIC certification/binding/revocation state, `DeploymentBinding` records, the hardware-credential registry, Cutover Record transitions, and environment-lock provisioning; admin write authority does not itself confer ordinary runtime execution authority (HBDC-REQ-009/010).

## 10. Model-A Deployment and Canonical Repository Root

Model A (editable install from the canonical repository working tree) is the sole authorized v1.0 deployment model, consistent with HMIC-REQ-064 (HBDC-REQ-022/024). Conformance evidence for Model-A is enumerated (HBDC-REQ-023): canonical-deployment-root match against the active `DeploymentBinding`, editable-install metadata resolution into that same tree, and no environment-lock channel redirecting resolution elsewhere.

## 11. Agent Python Execution-Environment Lock (DRA-REQ-003)

Fully concretized in HBDC-001 §13 (HBDC-REQ-025..039): production venv/site-packages/interpreter admin-owned and agent-unwritable; `PYTHONPATH` not agent-settable; user-site disabled or proven agent-unwritable; `sitecustomize`/`usercustomize`/`.pth` files admin-controlled or absent; no agent-installable `sys.meta_path` hook; CWD-shadowing and fake-package-shadowing closed via the same three requirements; editable-install link metadata and launcher/wrapper configuration admin-controlled; shell environment cannot inject authority-changing variables; Git executable resolution agent-unreplaceable for authority-derivation subprocess calls; third-party authority dependencies agent-unreplaceable via the venv lock.

## 12. HMIC-REQ-063 Relationship

HBDC-001 §14 states explicitly: the §13 environment lock is the concrete mitigation permitting a Model-A deployment to claim HMIC-REQ-063's OPTION C accepted-residual branch (HBDC-REQ-040); a deployment failing §13 falls into the BLOCKING branch. Compliance is explicitly not represented as cryptographic executed-source attestation (HBDC-REQ-041), preserving HMIC-REQ-063's own named, honest limitation.

## 13. Third-Party/Git Dependency Disposition

Git executable resolution for authority-derivation subprocesses (`derive_implementation_commit`) must be admin-controlled/agent-unreplaceable (HBDC-REQ-038). Third-party dependencies, including FIDO2/PIV hardware-provider libraries, are not HMIC-certified source under v1.0 but are covered by the same venv/site-packages write lock (HBDC-REQ-039) — no separate dependency-pinning mechanism is introduced.

## 14. Repository/Deployment Identity, Worktrees, Clones, Host Migration, Backup/Restore

`repository_instance_id` confers no authority alone (HBDC-REQ-042). Worktrees, clones/copies, host migrations, and cross-path/cross-host backup restores each independently require their own `DeploymentBinding` and (if claimed) certification; none implicitly inherits another instance's Class-B authority (HBDC-REQ-043..046), consistent with 149O.1B.2's unmodified worktree/clone scope.

## 15. Threat-Model Limits

No claim of resistance to a fully compromised OS root/admin account. No claim that this filesystem/environment contract replaces HATP-001's hardware-signer assurances.

## 16. HBDC Trust/Binding Disposition (Load-Bearing Decision)

**Selected: Option A.** HBDC-001 is not, as of v1.0, one of HMIC-001's bound contracts (not in `contract_versions`, not part of the 24-file `implementation_scope_digest`). Before any deployment may be represented as satisfying HMIC-REQ-063's Option-C branch on the strength of this contract in a *mechanically gated* way, HBDC-001 must be added to HMIC-001's bound-contract set via a future HMIC-001 v1.2 amendment (HBDC-REQ-048) — **not performed by this phase**, requiring its own governed phase and independent verification. Until then, HBDC-001 conformance is evidentiary/advisory only (HBDC-REQ-049). Rejected alternatives (Option B — never bind; Option C — separate protected manifest) and their rejection rationale are recorded in HBDC-001 §17.

## 17. Real-Authorization Gates

Successful future HBDC-001 conformance does not itself authorize real Protected Root creation, real OS principal provisioning, real HMIC certification, real active binding, real Cutover Record transition, or real `HATP_MANDATORY` activation (HBDC-REQ-050). This contract freeze itself authorizes none of those actions either (HBDC-REQ-051).

## 18. Requirements, Invariants, Attack Matrix

HBDC-001 v1.0 defines 55 requirements (`HBDC-REQ-001`..`HBDC-REQ-055`, sequential, no gaps/duplicates — see the contract's §24 Full Requirement Traceability), 8 security invariants (`CBD-1`..`CBD-8`, §19), and a 21-scenario attack matrix (§21). Blocking-condition checklist (§22/§26) confirms no open finding from the phase charter.

## 19. Tests

`tests/test_phase_149o_20b_hatp_class_b_deployment_contract_freeze.py` mechanically verifies: requirement-ID inventory (unique, gapless, count 55); invariant-ID inventory (CBD-1..CBD-8); attack-matrix row inventory (21, no duplicate index); DRA-REQ-001..003 mapping presence; the Option-C/Model-A-only boundary statement; the two-principal statement; Protected Root agent-non-write/admin-write statement; parent-path/ACL/group coverage; the full Python-environment-lock checklist (venv, PYTHONPATH, user site, `.pth`, sitecustomize/usercustomize, import hooks, CWD shadowing); the HMIC-REQ-063 no-overclaim statement; the contract-binding disposition statement (§17/§110); and the real-authorization-gate statement (freeze ≠ provisioning ≠ certification ≠ activation).

## 20. No Production/Contract Diff

Zero `src/pcae/**` files changed. Zero `scripts/**` files changed. All eight existing bound contracts (HATP-001, HMRC-001, HMIC-001 v1.1, HSCE-001, RAE-001, RWMPC-001, PBPA-001, PBPC-001) confirmed byte-unchanged at exit. New files this phase: this document, the HBDC-001 contract document, and the contract-completeness test module — plus PROJECT_STATUS.md/CHANGELOG.md/task-lifecycle updates.

## 21. No Real State Change

No real Class-B provisioning occurred. No OS principal, group, or ACL was created or changed. No real Protected Root was created. No real HMIC certification, active binding, or revocation state was created. No Cutover Record or activation marker was created or modified. No `HATP_MANDATORY` activation occurred. No Permission Broker behavior changed. POL-005 unchanged. COMP-002 not implemented. No hardware credential or device state changed. Runtime remains Observed / observe / unavailable. HATP production remains NOT READY.

## 22. Findings

None. No Blocking or Non-Blocking findings identified against this phase's own charter.

## 23. Contract Verdict

```
HATP CLASS-B DEPLOYMENT CONTRACT:
HBDC-001 v1.0 — FROZEN
— PENDING INDEPENDENT VERIFICATION
— REAL PROVISIONING NOT AUTHORIZED
— REAL ACTIVATION NOT AUTHORIZED
```

## 24. Recommended Next Phase

149O.20C — HATP Class-B Deployment Contract Independent Verification. Must independently reconstruct 149O.20A's decisions, re-derive the two-principal model, independently attack Protected Root permission semantics and ACL/group/writable-parent loopholes, independently attack the Model-A Python environment lock, independently test the OPTION-C boundary, independently verify HBDC-001's contract-binding/self-trust disposition (§16 above), and verify no real provisioning or activation occurred during this phase. Must not recommend provisioning directly. If it confirms the HMIC v1.2 prerequisite, that conclusion must be independently re-derived, not merely accepted, before any HMIC amendment is authorized. HATP production remains NOT READY; runtime remains Observed / observe / unavailable.
