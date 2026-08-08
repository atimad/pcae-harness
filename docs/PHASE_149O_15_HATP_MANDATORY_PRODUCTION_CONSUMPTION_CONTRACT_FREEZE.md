# Phase 149O.15 — HATP Mandatory Production Consumption Contract Freeze

Phase type: **CONTRACT FREEZE ONLY**. No production source under
`src/pcae/` was modified. No existing contract (`HSCE-001`, `HATP-001`,
`RAE-001`, `RWMPC-001`, `PBPA-001`, `PBPC-001`) was modified. This phase
creates exactly one new contract:
`docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
(**HMRC-001 v1.0**).

## 0. Baseline

- Latest completed phase: 149O.14 — HATP AG3/AG5 Mandatory Production
  Consumption Architecture. Status: completed, report complete, pushed
  (commits d3ab9b4a, 73c431bc, d9b1fa68; `origin/main..HEAD` = 0 at
  phase entry). Verdict: HATP AG3/AG5 MANDATORY PRODUCTION CONSUMPTION
  ARCHITECTURE: SELECTED.
- HATP production state: **NOT READY**.
- Runtime: Observed / observe / unavailable. Permission Broker:
  `execution_unavailable`.
- B-149O-1..4: INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY
  — SYSTEM EXECUTION CLOSURE DEFERRED. Not closed by this phase.

## 1. Initial Inspection (performed and confirmed)

`git status --short` clean; `git status --branch --short` showed
`## main...origin/main` with zero divergence; `git rev-list --count
origin/main..HEAD` = 0. `pcae health` → healthy. `pcae check` → passed.
`pcae status coherence` → coherent. `pcae doctor task-memory` →
warnings, pre-existing and unrelated (a stale duplicate active-task
file left over from the 149O.6 era, and several `tasks/done/` entries
missing from `tasks/DONE.md`, predating this phase). `pcae push check`
→ clean, nothing to push. `pcae runtime inspect` → Observed / observe /
unavailable, Permission Broker `execution_unavailable`. `pcae notify
status` → Telegram configured, enabled, ready. `pcae phase-report show
--latest` and `pcae phase-report reconcile --phase-id 149O.14` both
confirmed 149O.14 completed/complete/pushed, no mutation needed.

The stale duplicate active-task file
(`tasks/active/20260807-1634-idle-awaiting-next-governed-phase-post-149o-6.md`)
was removed as task-lifecycle hygiene while opening this phase's task
(see the task-lifecycle commit); it dated from well before 149O.7 and
was never valid alongside the current 149O.14 idle placeholder.

## 2. Primary Sources Read Directly

`docs/PHASE_149O_14_HATP_AG3_AG5_MANDATORY_PRODUCTION_CONSUMPTION_ARCHITECTURE.md`
(full, including the exact MC-1..MC-13 invariants and the exact
45-scenario future attack matrix — reconciled verbatim rather than
trusted from this prompt's paraphrase), `docs/contracts/
HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md` (HSCE-001 v1.1,
including `HATPEvidenceStore.load` and the evidence-ID domain rule),
`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`
(HATP-001 v1.0), `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`
(RAE-001 v1.0, including the exact `approval_present` conjunction),
`docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`
(PBPA-001 v1.0, POL-005's exact `simulation_only` rule),
`docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`
(PBPC-001 v1.2, `implementation_status="execution_unavailable"` and the
truthful-`simulation_only=False`-resolves-`DENY` finding), and
`docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`
(RWMPC-001 v1.0, the `EXECUTION_CLASS_ROLLBACK` classification and its
own §12.1 BLOCKING finding on rollback-class PB satisfiability).

Production source read directly (not trusted from prior phase-report
prose): `core/hatp_evidence_store.py` (`HATPEvidenceStore.load`,
explicit-ID-only, no verification performed there), `core/
hatp_ag_authority.py` (`resolve_ag3_gated_rollback_authority`,
`resolve_ag5_gated_rollback_authority`, confirmed the PB request they
build is unconditionally `simulation_only=True`), `core/
rollback_approval_evidence.py` (the exact `approval_present` derivation
chain including `resolve_rollback_approval_evidence_with_hatp`),
`core/human_approval_trusted_provenance.py` (`verify_hatp_proof`'s
exact ordered check sequence and closed `HATPVerificationStatus`
vocabulary), `core/permission_broker.py` /
`core/permission_broker_foundation.py` (the `DECISION_ALLOW/DENY/
HUMAN_REVIEW` vocabulary, `ExecutionDisabledRule`/POL-005's exact
`simulation_only` trigger condition, and the `COMPONENT_REGISTRY`
confirming `COMP-002`/`COMP-008` remain `not_implemented`), `core/
agent.py` (`execute_rollback` and `build_rollback_execution`'s exact
current signatures, gate sequences, and effect calls — `_run_git_revert`
for AG3, the real `write_text`/`write_bytes`/`unlink` loop for AG5),
`commands/agent.py` (confirmed both real CLI call sites pass zero HATP
kwargs today), `commands/hatp.py` (the existing `pcae hatp sign
rollback --site {ag3|ag5}` grammar), and `cli.py` (confirmed standard
argparse wiring for `hatp`, `rollback`, and `remote rollback`
subcommands).

## 3. Central Finding This Contract Had To Resolve

149O.14 documented, but explicitly left open, the tension between
"the mandatory boundary must place a real PB decision in the path" and
"the current architecture's PB request is fixed at
`simulation_only=True`, and PBPC-001 already establishes that a
truthful `simulation_only=False` request deterministically resolves
`DENY` given today's `execution_unavailable` runtime posture." This
phase resolved that tension explicitly, rather than leaving it to a
future implementer, as **HMRC-001 §12 / MC-14 (the Effect-Truthful PB
Requirement)**: a real AG3/AG5 effect may only cross the Mandatory
Consumption Boundary on the strength of a PB decision obtained from a
request that truthfully represents the attempt as `simulation_only=
False` and resolves `ALLOW`. Because today's architecture cannot
produce such a decision (`COMP-002`/`COMP-008` remain
`not_implemented`), the direct, accepted consequence is that
`HATP_MANDATORY` does not, by itself, guarantee rollback availability —
post-cutover real effects fail closed until a narrowly-scoped,
rollback-specific execution-enforcement capability exists. This
resolution was chosen over the alternative (accepting a
`simulation_only=True` `ALLOW` as sufficient) because the latter would
mean the contract could claim an "enforced mandatory boundary" while a
real mutation still proceeded under a merely-simulated permission
result — exactly the kind of false "mandatory" claim the contract
freeze was required to avoid.

## 4. What Was Frozen

See `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
(HMRC-001 v1.0) for the full normative text. Summary:

- **Contract ID:** HMRC-001 v1.0 ("HATP Mandatory Rollback Consumption
  Contract"), chosen over the candidate "HPC-001" for scope precision
  (rollback-specific, not general production consumption).
- **Evidence-reference syntax:** exactly `--hatp-evidence-id
  <evidence_id>` on both `pcae remote rollback execute <job_id>` (AG3)
  and `pcae rollback --per-id <per_id>` (AG5); no alias; no other flag
  added.
- **Canonical consumption chain:** explicit `evidence_id` →
  `HATPEvidenceStore.load` → `HATPSignedEvidenceEnvelope` → the
  existing, unmodified `resolve_rollback_approval_evidence_with_hatp`
  conjunction → `approval_present` → the existing PB request shape →
  PB decision → MC-14 effect-truthfulness gate → real effect.
- **Old-hook disposition:** `hatp_evidence_id` retained and promoted
  to the sole canonical locator parameter; `hatp_proof` and
  `hatp_evidence` deprecated/internal-only, forbidden as production
  caller input on the mandatory path.
- **Cutover model:** `LEGACY_COMPATIBLE → PREPARED → HATP_MANDATORY`,
  no direct skip, no reverse transition available to ordinary
  principals, Class-B Protected Activation Authority only, stored as a
  new admin-owned Cutover Record under the existing Class-B protected
  trust root (never agent-writable `.pcae/`), with an explicit
  monotonicity mechanism (a separate write-once baseline marker) so
  record deletion/corruption cannot silently downgrade a
  previously-activated deployment to `LEGACY_COMPATIBLE`.
- **Legacy disposition:** `rollback_approval_state` and `pcae remote
  rollback approve` remain fully authoritative pre-cutover and in
  `PREPARED`; post-cutover, the approve command deterministically
  refuses (no mutation, no silent success) and `rollback_approval_state`
  becomes historical/migration metadata only — never a fallback
  authority, never part of an OR-condition.
- **Effect boundary:** inside `execute_rollback` immediately before
  `_run_git_revert`, and inside `build_rollback_execution` immediately
  before the first real file mutation — covering direct function calls,
  not just the CLI.
- **Failure semantics:** a closed, fail-closed enumeration of every
  load/verification failure mode, with no post-cutover legacy fallback
  under any of them.
- **Security invariants:** MC-1..MC-13 carried forward from the 149O.14
  architecture doc, plus a new **MC-14** (the Effect-Truthful PB
  Requirement, §3 above).
- **Attack matrix:** all 45 scenarios from the 149O.14 architecture
  document, reconciled and re-counted (exactly 45, no reduction, no
  addition), each with a frozen expected result citing the relevant
  `HMRC-REQ` clause.
- **B-149O-1..4 closure criteria:** frozen (HMRC-001 §32) — not met by
  this phase; remain INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY
  BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED.

## 5. What Was Explicitly Not Done

No production code was modified. `HSCE-001` v1.1, `HATP-001` v1.0,
`RAE-001` v1.0, `RWMPC-001` v1.0, `PBPA-001` v1.0, and `PBPC-001` v1.2
were read but not amended — `git diff --stat -- docs/contracts/` for
those six files is empty. No cutover state was implemented. No
Permission Broker behavior changed. No `POL-005` change. No `COMP-002`
capability was implemented. No rollback dispatch behavior changed. No
Class-B provisioning occurred. No HATP production activation occurred.

## 6. Carried-Forward, Non-Blocking Items

- **149O.12B-Obs-PY39-1** (Python 3.9/3.10 timestamp defect): does not
  block this contract freeze, and does not block 149O.16 (contract
  verification). It must be repaired before the first mandatory-
  consumption *implementation* phase that follows 149O.16.
- **149O.5-F-3** and the three remaining stale boundary-test snapshots
  from 149O.13: no semantic consequence for this contract; anticipated
  future test-widening item only.

## 7. Contract Verification Test

`tests/test_phase_149o_15_hatp_mandatory_production_consumption_contract_freeze.py`
independently re-verifies, by direct source and document inspection
rather than by trusting this report's prose: the frozen contract ID/
version, the requirement-ID sequence and count, the MC-1..MC-14
invariant sequence, the 45-attack-matrix count, the exact evidence flag
string, the mode-state vocabulary and transition rule, absence of any
`legacy_approved OR hatp_valid`-shaped language, the protected-storage
requirement, AG3/AG5 gate ownership text, old-hook disposition
presence, PB/COMP-002 separation language, and re-confirms (independent
of the contract's own prose) the underlying current-state source facts
the contract depends on: AG3's real effect path and its sole legacy
gate, AG5's real effect path and its absence of any human-approval
gate, the inert Wave-7 hooks and their zero real-caller usage,
`HATPEvidenceStore`'s explicit-ID-only `load` API,
`hatp_ag_authority`'s unconditional `simulation_only=True` PB request,
`ExecutionDisabledRule`/POL-005's exact trigger condition, and that no
`src/pcae/**` or existing `docs/contracts/**` file differs from the
phase-entering commit.

## 8. Required Final Report

- **Phase ID:** 149O.15
- **Status:** completed
- **Report completeness:** complete
- **Files changed:** `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
  (new), `docs/PHASE_149O_15_HATP_MANDATORY_PRODUCTION_CONSUMPTION_CONTRACT_FREEZE.md`
  (new), `tests/test_phase_149o_15_hatp_mandatory_production_consumption_contract_freeze.py`
  (new), plus `PROJECT_STATUS.md`/`CHANGELOG.md` and task-lifecycle
  bookkeeping files.
- **Production files changed:** none (`git diff --name-only -- src/pcae/`
  against the phase-entering commit is empty).
- **New contract ID / version:** HMRC-001 v1.0.
- **Requirement count:** HMRC-REQ-001 through HMRC-REQ-085.
- **Security invariant count:** 14 (MC-1..MC-14).
- **Attack-matrix count:** 45.
- **HSCE-001 / HATP-001 / RAE-001 / RWMPC-001 / PBPA-001 / PBPC-001
  byte status:** all unchanged.
- **Current AG3 real effect path:** `pcae remote rollback execute` →
  `run_remote_rollback_execute` → `execute_rollback` →
  `_run_git_revert`, gated only by legacy `rollback_approval_state ==
  "approved"` plus structural preconditions.
- **Current AG5 real effect path:** `pcae rollback --per-id` →
  `run_rollback` → `build_rollback_execution` → real file
  write/unlink loop, gated only by PER-status/divergence/payload
  structural checks — no human-approval gate exists today.
- **Frozen AG3 evidence-reference syntax:** `pcae remote rollback
  execute <job_id> --hatp-evidence-id <evidence_id> [--json]`.
- **Frozen AG5 evidence-reference syntax:** `pcae rollback --per-id
  <per_id> --hatp-evidence-id <evidence_id> [--dry-run] [--json]`.
- **Canonical evidence loader:** `HATPEvidenceStore.load(evidence_id)`
  (existing, unmodified).
- **Canonical consumption object:** `HATPSignedEvidenceEnvelope`
  (existing, unmodified).
- **Raw hook disposition:** `hatp_evidence_id` retained/canonical;
  `hatp_proof` deprecated/internal-only, forbidden on the mandatory
  path; `hatp_evidence` same disposition as `hatp_proof`.
- **Consumption-time verification owner:** `verify_hatp_proof`
  (HATP-001, unmodified), invoked via the existing
  `resolve_rollback_approval_evidence_with_hatp` adapter.
- **Approval derivation owner:** the existing, unmodified 3-term
  conjunction in `rollback_approval_evidence.py`
  (`_derive_hatp_gated_approval_present`).
- **PB handoff owner:** `hatp_ag_authority.py`'s existing
  `build_permission_broker_request`/`PermissionBroker().evaluate` call,
  reused unmodified in shape; gated additionally by the new MC-14
  effect-truthfulness rule.
- **AG3 mandatory gate point:** inside `execute_rollback`, immediately
  before `_run_git_revert`.
- **AG5 mandatory gate point:** inside `build_rollback_execution`,
  immediately before the first real file mutation.
- **Direct-call bypass prevention:** gate lives inside the effect
  functions themselves, not the CLI layer.
- **Mode vocabulary:** `LEGACY_COMPATIBLE`, `PREPARED`,
  `HATP_MANDATORY`.
- **Mode transition rule:** `LEGACY_COMPATIBLE → PREPARED →
  HATP_MANDATORY` only; no skip; no reverse transition for ordinary
  principals.
- **Cutover storage:** new admin-owned Cutover Record under the
  existing Class-B protected HATP trust root (not `.pcae/`).
- **Cutover schema:** `version` (strict int), `repository_instance_id`,
  `mode`, `activated_at`, `activated_by` — closed v1 schema.
- **Cutover authority:** Class-B Protected Activation Authority only.
- **Cutover monotonicity:** enforced via a separate write-once
  deployment-baseline marker distinguishing "never activated" from
  "activated, record now missing/corrupt."
- **Cutover cache prohibition:** every effect attempt reads current
  mode fresh; no process-local or any other cache.
- **Cutover corruption/deletion behavior:** fail-closed-mandatory-
  equivalent if the baseline shows prior activation; `LEGACY_COMPATIBLE`
  only if the baseline shows the deployment was never activated.
- **Activation prerequisites:** Class-B deployment validity, HATP
  substrate operational, HSCE signing available, mandatory-consumption
  implementation present and independently verified, production
  dependency provenance valid, Protected Activation Authority
  available. Execution-enforcement capability (MC-14) is explicitly
  NOT a prerequisite for activation — its absence instead makes
  post-cutover effects fail closed, an accepted consequence.
- **Legacy approve command, pre-cutover:** current behavior, fully
  authoritative.
- **Legacy approve command, `PREPARED`:** identical to pre-cutover,
  optionally with a deprecation warning; never a second authority.
- **Legacy approve command, post-cutover:** deterministic refusal, no
  mutation, no silent success, no authority.
- **`rollback_approval_state`, pre-cutover:** authoritative, unchanged.
- **`rollback_approval_state`, post-cutover:** historical/migration
  metadata only; never independently authorizes effect.
- **AG5 structural status checks:** preserved unconditionally in every
  Consumption Mode; not removed or weakened by HATP's introduction.
- **Pending legacy approvals at cutover:** not grandfathered; authority
  evaluated at effect-attempt time only.
- **Missing/invalid evidence post-cutover:** mandatory failure, no
  legacy fallback.
- **Expired/revoked/wrong evidence:** fail closed via existing HATP
  verifier statuses.
- **PB `HUMAN_REVIEW`:** effect prohibited.
- **PB `DENY`:** effect prohibited.
- **PB `ALLOW`:** insufficient alone; must additionally satisfy MC-14
  (truthful `simulation_only=False`).
- **Real-effect/PB enforcement rule:** MC-14, §3/§4 above — the central
  resolved question.
- **POL-005 status:** unchanged.
- **COMP-002 separation:** explicitly maintained; this contract governs
  rollback-specific authority consumption only, never general execution
  capability.
- **Requirement inventory:** HMRC-REQ-001..085 (see contract §26 index).
- **MC-1..MC-14:** all frozen (contract §27).
- **45-attack matrix:** frozen (contract §29).
- **B-149O-1..4 closure criteria:** frozen, not met (contract §32).
- **149O.13 findings disposition:** unaffected by this phase; no
  reopening.
- **149O.5-F-3 status:** unchanged, no semantic consequence for this
  contract.
- **149O.12B-Obs-PY39-1 sequencing:** unchanged — non-blocking for
  149O.15/149O.16, must be repaired before the first mandatory-
  consumption implementation phase.
- **Contract self-consistency:** confirmed (contract §33).
- **Contract-freeze tests:** new file, described in §7 above.
- **Contract verdict:** `HMRC-001 v1.0: FROZEN — READY FOR INDEPENDENT
  CONTRACT VERIFICATION` (not VERIFIED).
- **HATP production readiness:** remains NOT READY.
- **Recommended next phase:** 149O.16 — HATP Mandatory Production
  Consumption Contract Independent Verification.

**Explicit confirmations:** No production source was modified. HSCE-001
v1.1 remained byte-unchanged. HATP-001 v1.0 remained byte-unchanged.
RAE-001 v1.0 remained byte-unchanged. PB contracts/policies
(RWMPC-001, PBPA-001, PBPC-001) remained byte-unchanged. No AG3/AG5
mandatory consumption was implemented. No legacy approval behavior
changed. No Cutover Record was created. No Permission Broker behavior
changed. `POL-005` remained unchanged. No `COMP-002` capability was
implemented. No rollback dispatch behavior changed. No Class-B
provisioning occurred. No HATP production activation occurred. Signing
evidence remains distinct from approval, permission, capability, and
execution. B-149O-1..4 remain independently verified at the HATP-gated
authority boundary with system execution closure deferred. HATP
production remains NOT READY. Runtime remains Observed / observe /
unavailable.
