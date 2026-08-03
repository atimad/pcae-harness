# Phase 149C — Repository-Wide Mutation Permission Coverage Contract Freeze

## 0. Baseline

- Latest completed phase: 149B (`47e690af`, `5dc3b29f`, pushed,
  `origin/main..HEAD` = 0).
- Chapter 148 (`pcae push` MVP): CERTIFIED WITH RETAINED NON-BLOCKING
  FINDINGS.
- Chapter 149 capability: Repository-Wide Mutation Permission Coverage.
- Selected architecture: Model E — Hybrid (149B).
- Runtime before this phase: `Observed` / `observe` / `unavailable`.
- Pre-phase checks (all ran clean): `pcae health`, `pcae check`,
  `pcae status coherence`, `pcae doctor task-memory`, `pcae push check`,
  `pcae runtime inspect`, `pcae notify status`,
  `pcae phase-report show --latest`,
  `pcae phase-report reconcile --phase-id 149B` (reconciled, no
  mutation).

## 1. Phase Type

Normative contract freeze only. No `src/pcae/**` change. No PBPC-001 or
PBPA-001 amendment. No POL-013+. No Prompt Generation/Dispatch/agent
invocation. No runtime capability elevation.

## 2. Independent Mutation Inventory Reconstruction

149B reported 13 real, CLI-reachable production mutation dispatch
sites. This phase did not trust that count — it re-read
`src/pcae/commands/push.py`, `src/pcae/core/agent.py`,
`src/pcae/commands/task.py`, and `src/pcae/commands/phase.py` directly,
grepping for `git commit`/`git push`/`git revert`/`git reset` subprocess
dispatch and direct filesystem write/unlink calls, and independently
arrived at the same 13 sites (see contract Section 4 for the full
table with exact file:line references). This is an independent
confirmation, not an assumption carried over from 149B.

Two structural findings, made directly from source rather than from
149B's prose:

- `pcae promote`'s `build_promotion_execution` (`agent.py`) contains
  **two** distinct mutation sites, not one: the per-file apply loop
  (write/unlink into `approved_paths`, lines ~93390-93417) and a
  separate promotion-failure restore path (writing back
  `before_content`, lines ~93820-93841). The restore path is, in
  substance, a rollback operation, not an apply operation — this
  distinction drives the contract's execution-class resolution
  (Section 4 below).
- `commands/task.py` contains three, not two, git-commit dispatch call
  sites: two internal branches of `pcae task finish --commit`
  (pathspec-scoped vs. repo-wide, lines 308/316) plus
  `pcae task finish recover` (line 1100).

## 3. Contract Identity

`RWMPC-001` was confirmed as the correct identifier — no existing
repository-conventional identifier collides with it, and it follows
the same `<ABBREVIATION>-001` pattern as `PBPC-001`/`PBPA-001`.
Contract text: `docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`.

## 4. Key Satisfiability Findings

### 4.1 `simulation_only` — resolved, no gap

`PermissionBrokerRequest.simulation_only`'s own docstring (Phase 108A)
defines it as tracking whether the Foundation has an execution
boundary (`COMP-002`, `not_implemented`) — not whether the calling
command will really mutate. `push.py`'s production consumer already
sets `simulation_only=True` on `pcae push`'s real dispatch request
(the field's own load-bearing precedent). Independent testing
confirmed setting `simulation_only=False` for any real mutation
unconditionally triggers POL-005 DENY (`ExecutionDisabledRule` is
"unconditionally active by construction" pending `COMP-002`) — a
Foundation-wide condition, not specific to any mutation class. This
contract applies the existing, already-established `True` value
uniformly, rather than reinterpreting it — no POL-005 weakening, no
gap.

### 4.2 Execution-class mapping for promotion/file-apply — resolved

149B (§21/§22) explicitly left this open as a STRATEGIC_POLICY_GAP.
Independent resolution: `EXECUTION_CLASS_MUTATION` and
`EXECUTION_CLASS_ROLLBACK` already exist in
`permission_broker_foundation.py` and differ by *operation semantics*
(new mutation vs. revert-to-prior-state), not by target-file risk.
Promotion's apply loop (AG4) writes new approved content — truthfully
`MUTATION`, matching push/commit. Promotion's failure-restore path
(AG5) reverts to previously recorded `before_content` — truthfully
`ROLLBACK`, matching `execute_rollback`'s `git revert`. This resolves
149B's open mapping question using only the existing taxonomy; no new
execution class or POL-013 was needed or added.

### 4.3 Rollback approval evidence — genuine, scoped blocking gap

`POL-004` (`MissingHumanApprovalRule`) applies to
`EXECUTION_CLASS_ROLLBACK` but not `EXECUTION_CLASS_MUTATION`
(re-verified directly against `permission_broker_foundation.py:459-468`,
matching 149B's finding). Every rollback-class legacy flag examined
(`--promotion-authorized`, `approve_rollback`, `change_approval_state`,
`--approve-keep`/`--approved-by`/`--reason`) is either an
unauthenticated CLI self-declaration or a bare state toggle — none is
trusted approval evidence. A truthful rollback-class request therefore
necessarily carries `approval_present=False`, which POL-004 correctly
routes to `HUMAN_REVIEW` — zero dispatch, by design. This is recorded
as a **BLOCKING** finding (contract Section 12.1), not papered over:
rollback coverage (AG3, AG5) cannot be implemented until a future,
narrowly scoped phase defines a legitimate approval-evidence source.
The blocking finding is severable — it does not prevent freezing or
future-implementing the nine `MUTATION`-class sites, whose
satisfiability is independently confirmed with no gap.

### 4.4 Legacy adoption-pipeline duplication — reaffirmed

Independently reconfirmed 149B's finding: `pcae remote *`, `pcae
promote`, and backend-created-output-adoption (`phase.py` PH1/PH2)
are three separately-built "adopt produced changes" pipelines sharing
no code and no common permission gate. The contract's disposition
table (Section 14) routes the two duplicate push implementations
(PH2, PH3) onto the canonical push adapter rather than legitimizing a
third and fourth independent implementation.

## 5. Task-Finish Commit Disposition (Explicitly Justified, Not Assumed)

`pcae task finish --commit`/`recover` (TK1-TK3) are real `git commit`
dispatches. This phase did not exclude them by default. Justification
for `LIFECYCLE_INTERNAL / DEFERRED_COVERAGE` rather than
`BROKER_WIRE`: the staged-file-aware conflict check mechanically
restricts these commits to task-closure paths only (it blocks the
commit if any other staged content is present) — they cannot commit
arbitrary repository content, unlike the other 10 in-scope sites. They
remain classified `in scope` for the taxonomy (Section 2 of the
contract) and revisit is required if this mechanical restriction is
ever weakened.

## 6. Satisfiability Matrix

See contract Section 12 for the full matrix (commit / push / promotion
apply / rollback, each with truthful field values, POL-004
applicability, POL-005 result, resolvable decision, and satisfiability
verdict). Summary: 8 of 13 sites (all `MUTATION`-class) are fully
satisfiable now; 2 of 13 sites (`ROLLBACK`-class, AG3/AG5) are blocked
on missing approval evidence; 3 of 13 sites (TK1-TK3) are
out-of-immediate-scope with an explicit, evidenced rationale.

## 7. PBPA-001 / PBPC-001 Compatibility

Both remain unamended. `git diff --name-only 45e32236..HEAD --
docs/contracts/` shows only the new `RWMPC-001` file added — no
existing contract text touched (verified below, Section 10).

## 8. Threat Model

See contract Section 16. Notably: the self-modification threat (`pcae
promote` reaching `src/pcae/**`) is why `build_promotion_execution`'s
apply loop (AG4) is the highest-priority `BROKER_WIRE` site in the
disposition table — this contract requires broker coverage for it but
does not itself add a protected-path hard block, since no existing
authority establishes one and this phase is not authorized to invent
one.

## 9. Findings Classification

- **BLOCKING (scoped):** Rollback-class (AG3, AG5) Permission Broker
  coverage is not satisfiable without a future approval-evidence
  phase (Section 4.3 / contract Section 12.1).
- **RESOLVED (was STRATEGIC_POLICY_GAP in 149B):** File-apply
  execution-class mapping (Section 4.2).
- **RESOLVED (was open in 149B):** `simulation_only` semantics for
  non-push mutation classes (Section 4.1).
- **OBSERVATION:** PBPA-001 and PBPC-001 required no amendment to
  support this contract.
- **OBSERVATION:** `push.py`'s existing duplicate request-construction
  (698/898) is a pre-existing consolidation target this contract binds
  a future implementation phase to address (contract RWMPC-REQ-036),
  not something 149C itself touches.
- **NON-BLOCKING:** Task-finish commit sites (TK1-TK3) remain
  deliberately unwired, with rationale recorded (Section 5).
- **DEFERRED:** Prompt Creation/Dispatch, agent invocation, runtime
  capability activation — untouched, per 149A/149B.

## 10. Boundary Verification

```
git diff --name-only 45e32236..HEAD -- src/pcae/
```
Expected and confirmed: empty (only new documentation files were
added by this phase: the RWMPC-001 contract and this phase document).

```
git diff --name-only 45e32236..HEAD -- \
  docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md \
  docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md
```
Expected and confirmed: empty. PBPC-001 remains v1.2. PBPA-001 remains
v1.0.

`pcae runtime inspect`, run before and after: `Runtime state: Observed`,
`Execution capability: unavailable`, `Maximum plugin capability:
observe`, `Permission Broker status: execution_unavailable` —
unchanged.

## 11. Contract Freeze Verdict

**RWMPC-001 v1.0 FROZEN.** Full coverage frozen and implementation-
satisfiable now for 8 of 13 sites (all `EXECUTION_CLASS_MUTATION`);
classification and requirements frozen but implementation blocked for
2 of 13 sites (`EXECUTION_CLASS_ROLLBACK`, pending a future
approval-evidence phase — Section 12.1 of the contract); 3 of 13 sites
(task-finish commits) frozen as `LIFECYCLE_INTERNAL / DEFERRED_COVERAGE`
with explicit justification. No `BLOCKING` finding against the
contract's own internal logic remains unresolved; the one `BLOCKING`
finding is a scoped, severable prerequisite for a *future*
implementation phase's rollback-coverage slice, not a defect in this
contract.

## 12. No-Go Confirmations

No `src/pcae/**` file was modified by this phase. No existing contract
text (PBPC-001, PBPA-001) was modified. No POL-001..012 meaning was
changed. No POL-013+ was added. No new Permission Broker production
consumer was implemented. No existing mutation path was modified,
activated, or exercised — every finding above is independent
observation of pre-existing code. No Prompt Generation capability was
implemented. No Prompt Dispatch capability was implemented. No agent
invocation capability was implemented. No runtime execution capability
was enabled — Runtime remains Observed, maximum capability remains
observe, execution availability remains unavailable. No change was
made to Interactive Workflow Confirmation semantics; it remains
distinct from approval. No change was made to Authority
Evaluation/AESIC, which remains disclosure-only. No approval was
fabricated — the rollback-class gap (Section 4.3) is recorded as
unresolved rather than closed with a self-declared flag.

## 13. Recommended Next Phase

**149D — Repository-Wide Mutation Permission Coverage Contract
Independent Verification.** 149D should independently reconstruct the
mutation inventory, scope, request mapping, approval semantics,
simulation semantics, PBPA applicability, policy satisfiability,
non-bypassability requirements, and Chapter-148 compatibility, and
specifically re-adjudicate the rollback-class blocking finding
(Section 12.1 of RWMPC-001) before any implementation phase is
authorized. A separate, narrowly scoped approval-evidence
architecture/contract phase is required before rollback-class
(`EXECUTION_CLASS_ROLLBACK`) Permission Broker coverage can be
implemented; this is not 149D's job to resolve, only to confirm is
correctly identified.
