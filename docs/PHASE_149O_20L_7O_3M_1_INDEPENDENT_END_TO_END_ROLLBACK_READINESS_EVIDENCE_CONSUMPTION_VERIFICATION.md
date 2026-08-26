# Phase 149O.20L.7O.3M.1 — Independent End-to-End Rollback Readiness / Evidence Consumption Verification

**Status:** COMPLETE — VERIFIED WITH NON-BLOCKING FINDINGS  
**Phase type:** VERIFICATION-ONLY. No `src/pcae` production source modified. No release action.  
**Repository:** `~/repos/pcae-harness`  
**Out of scope and not inspected:** `~/repos/pcae-deepseek-research`  
**Article:** STOPPED — not read, modified, or published  
**Public release:** `v0.4.2` unchanged at `bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`  
**Runtime:** `Observed / observe / unavailable`, unchanged

## 1. Objective

Independently verify or refute Phase `149O.20L.7O.3M`'s central claim that
`pcae rollback --per-id ...` already computed and consumed rollback
preparation evidence on a real invocation before `3M`, with no prior
`--dry-run` prerequisite, and that `3M` changed only immediate evidence
visibility. This phase did not trust `3M`'s prose, source interpretation,
tests, contract adjudication, or regression attribution.

## 2. Methodology

The phase used fixed commits, a detached pre-`3M` worktree, direct source and
contract reading, fresh disposable repositories, out-of-process CLI calls,
an independently authored 26-test suite, and targeted/shared regressions.
No helper or test function from `3M`'s test file was imported.

```text
phase_entry_commit = 8907df05536e1c817634f06b443eb8edbceb5ade
pre_3m_commit      = 7b19314591c2f954b727a3a96746747e38a55bb1
integration_commit = e632a2dfee77b8f83e03af1a34ad78aa7136c447
entry_current_head = 8907df05536e1c817634f06b443eb8edbceb5ade
v0.4.2_commit       = bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4
```

The fixed pre-`3M` tree was materialized at commit `7b193145` and executed in
a separate Python interpreter. A/B scenarios used fresh PER/ECP fixtures in
separate repositories so current imports could not contaminate baseline
behavior.

## 3. Pre-3M graph

Direct reading and execution of `7b193145` established:

```text
pcae rollback --per-id PER
  -> commands.agent.run_rollback
  -> core.agent.build_rollback_execution
  -> local PER lookup and mechanical eligibility checks
  -> local ECP lookup and in-progress guard
  -> file_plan = successful PER file_results paths
  -> divergence_check = live per-file hash comparison
  -> if dry_run: return preview, no RER, no file effect
  -> create/persist RER containing file_plan + divergence_check
  -> if conflict: persist aborted_divergence and return
  -> HATP_MANDATORY gate, or default mutation Permission Broker gate
  -> restore/remove loop over file_plan
  -> persist RER after every file and at terminal status
  -> return terminal result
```

The baseline real scenario was invoked without any earlier dry-run. It
completed, removed the promoted file, and persisted both evidence fields in
the RER. A baseline divergence scenario persisted
`status=aborted_divergence` and performed no effect.

## 4. Post-3M graph

The graph is identical except for an in-process `_evidence_summary` dict
created from the already computed locals and merged into four post-evidence
terminal results. `run_rollback` now renders the additional result fields.
No new computation, gate, branch, effect, schema, or store was added.

## 5. Dry-run prerequisite adjudication

**Verdict: NOT REQUIRED.**

Before `3M`, both `dry_run=True` and a real invocation reached the same
unconditional `file_plan` derivation and `_rer_check_divergence(...)` call.
The only branch distinction occurred afterward. The CLI defined
`--dry-run` with `action="store_true"`; omitting it directly selected the real
path. Fresh pre-`3M` execution proved the real path needed no prior preview.

## 6. Contract semantics

The contracts do not impose a hidden preview ceremony:

- HMRC-REQ-012 specifies `[--dry-run]` as an optional AG5 CLI flag.
- HMRC describes dry-run as advisory/diagnostic and explicitly permits it to
  return before mandatory real-effect authority consumption.
- RAE-REQ-027 leaves PER status/payload checks with AG5 itself.
- RAE-REQ-029 defines AG5 as a separate, explicitly invoked standalone
  command, not automatic recovery.
- RAE-REQ-061 requires human review to disclose target, scope, task, and
  repository context, but does not require that disclosure to be produced by
  `pcae rollback --dry-run`.
- RAE-REQ-065 requires a fresh rollback attempt and fresh Permission Broker
  request after approval evidence exists; it does not require a prior preview.

Therefore dry-run was intended as **optional diagnostics**, not required
human review, evidence preparation, an eligibility prerequisite, or a
test-only convenience.

## 7. Evidence definition

### `file_plan`

- **Type:** `list[str]`.
- **Derivation:** paths from the selected local PER's `file_results` whose
  `outcome == "success"`; user-specified paths are impossible.
- **Identity:** indirectly bound to repository-local `per_id`, its `ecp_id`,
  and the locally loaded PER/ECP records.
- **Persistence:** absent from a dry-run artifact because dry-run persists no
  RER; persisted as `RollbackExecutionRecord.file_plan` for every real
  post-precondition attempt.
- **Semantics:** an operational/mechanical scope input—the restore/remove loop
  iterates it. It is not approval, permission, or readiness authority.

### `divergence_check`

- **Type:** dict with `file_checks`, `blocking`, and `blocking_paths`; each
  file check carries `path`, `status`, and `current_hash`.
- **Derivation:** current repository file hashes compared with ECP
  `before_hash`/`after_hash` for the just-derived plan.
- **Identity/freshness:** bound in-call to the selected local ECP, plan, and
  current repository filesystem state.
- **Persistence:** same RER behavior as `file_plan`.
- **Semantics:** authoritative for the mechanical divergence safety gate;
  still not approval, Permission Broker authority, HATP authority, or runtime
  capability.

Other relevant inputs are PER terminal status and
`rollback_payload_available` (mechanical eligibility), the RER (audit and
resume receipt), HATP evidence (human-approval evidence), and the Permission
Broker decision (permission). These are deliberately separate layers.

## 8. Evidence consumption

Pre-`3M`, the evidence was genuinely consumed, not merely computed:

- `divergence["blocking"]` selected the zero-effect conflict return before
  either authority gate.
- `file_plan` defined `entries_by_path`, `status_by_path`, and every path
  entered by the effect loop.
- per-file divergence status selected skip versus restore/remove.
- evidence selected the RER's initial status and terminal result behavior.

The evidence does not feed the HATP or default PB decision as an authority
claim. Those gates remain separate and subsequent.

## 9. Readiness search

**Scoped verdict: NO DISTINCT AG5 READINESS CONCEPT.**

No type, artifact, state transition, store, or consumer in the
`pcae rollback --per-id` graph represents “ready,” “prepared,”
“safe-to-evaluate,” or “ready-for-effect.” The path directly evaluates
mechanical eligibility, current divergence, and authority on each call.

Repository-wide search did find objects named rollback readiness in other
subsystems: an unimplemented `RuntimeContext.RollbackContext` stub,
design-only backend invocation readiness, AG3 remote rollback review, and
CLTR migration rehearsal status. None is read by AG5, binds `{per_id,
ecp_id}`, or gates `build_rollback_execution`. This makes `3M`'s unqualified
phrase “no typed readiness concept anywhere in `src/pcae`” overbroad, while
leaving its scoped AG5 conclusion correct.

## 10. Contract requirement adjudication

**New authoritative readiness required for the implemented scope: NO.**

The existing in-call checks already provide current mechanical evidence and
the existing HATP/PB layers provide authority. Adding a second readiness
object for immediate result surfacing would duplicate state without adding a
consumer or resolving an unmet safety requirement.

## 11. Promotion-time persistence analysis

**`3M` rejection classification: CORRECT.**

A promotion-time readiness/evidence object would be separated in time from
the rollback effect and could become stale through:

- HEAD change;
- branch change;
- worktree/file change;
- PER replacement or changed `file_results`/status/payload availability;
- ECP replacement or changed hashes/before-content;
- active-task change;
- HATP evidence expiry/revocation/supersession;
- a different rollback target (`per_id`/`ecp_id`).

A valid design would need, at minimum: repository identity; `per_id` and
`ecp_id`; immutable PER/ECP digests; exact plan and per-file before/after/current
hashes; HEAD and branch binding where authority requires them; task binding;
creation time and expiry policy; invalidation rules for every state change;
single-attempt/replay semantics; lifecycle ownership; supersession; failure
semantics; and mandatory live revalidation immediately before effect. No
current contract grants those semantics. Implementing persistence without
them would create a stale-cache hazard; with live recomputation retained, the
artifact would be observability only and still not authoritative readiness.

## 12. 3M diff audit

The exact product delta from `7b193145` to `e632a2df` is:

- `src/pcae/core/agent.py`: +23/-0;
- `src/pcae/commands/agent.py`: +13/-0.

No contract, schema resource, version file, or RER version changed. The core
additions create `_evidence_summary` and merge existing locals into returns.
The CLI additions print those returned fields. Existing eligibility checks,
dry-run branch, divergence gate, HATP branch selection, PB invocation,
restore/remove statements, mutation order, terminal status computation, and
exit-code expression are unchanged.

## 13. Terminal paths

Five early errors occur before evidence can be validly derived:
`per_not_found`, `per_status_not_eligible`, `rollback_payload_unavailable`,
`ecp_not_found`, and `rollback_already_in_progress`. Their omission of
`file_plan`/`divergence_check` is truthful because preparation did not occur.

After evidence computation, every terminal path is covered:

1. dry-run — already returned both fields before `3M`;
2. divergence conflict — `3M` adds `file_plan`; `divergence_check` already
   existed;
3. HATP mandatory denial — `3M` adds both;
4. default PB denial — `3M` adds both;
5. final completed/partial/failed result — `3M` adds both through the common
   final return.

Fresh tests exercised dry-run, divergence, HATP denial, PB denial, completed,
partial, and failed outcomes.

## 14. Result/persistence consistency

For every real post-evidence terminal path with an RER, returned
`file_plan` and `divergence_check` equal the fields in the persisted record.
They are the same objects computed once in-call; there is no duplicate
recomputation. Dry-run intentionally has no RER.

## 15. CLI behavior

Out-of-process literal calls proved:

- a real eligible rollback without prior dry-run completed, removed the file,
  persisted an RER, printed per-file outcome and the full divergence check;
- dry-run printed `file_plan` and `would_block`, left the file unchanged, and
  created no RER;
- blocked results print both full evidence fields when available;
- JSON includes both additive fields and retains truthful non-authority fields
  and failure exit codes;
- no source or test consumer assumes an exact rollback-result key set.

Human output is intentionally summarized and asymmetric: success prints the
plan equivalently as per-file results rather than a second `file_plan:` line,
and dry-run prints `would_block` rather than the full divergence dict. JSON is
complete. The summaries do not imply permission, readiness authority, or
success on a denied/failed result.

## 16. Evidence non-authority

A clean plan and non-blocking divergence plus a forced PB `DENY` produced:
zero file effect, `rollback_permission_denied`, a terminal denied RER, and
truthful evidence in both return and record. `execution_allowed` remained
`False`. Evidence cannot upgrade authority.

## 17. Human boundary

The sole production caller is `commands.agent.run_rollback`, reached only by
explicit CLI invocation. The governance disclosure remains
`automatic_rollback_allowed=False` and
`rollback_requires_explicit_human_command=True`. Evidence preparation never
initiates rollback independently.

## 18. Permission Broker sequencing

Default ordering remains:

```text
eligibility -> preparation -> divergence/RER -> Permission Broker -> effect
```

Clean evidence calls the default adapter exactly once. Divergence calls it
zero times. PB denial performs zero root mutation. No alternate production
caller or effect loop bypass exists.

## 19. HATP isolation

`HATP_MANDATORY` resolves the dedicated HATP consumption path and never calls
the default mutation adapter. Missing evidence denied before effect, persisted
the existing terminal RER state, and surfaced evidence. `3M` did not alter
HATP decision inputs, mode resolution, or gate ordering.

## 20. Dry-run compatibility

Dry-run works on pre- and post-`3M` trees, computes equivalent evidence,
performs no root effect, invokes neither authority gate, and creates no RER or
new readiness state.

## 21. Real rollback without prior dry-run

Passed both in the fixed pre-`3M` interpreter and through the installed current
CLI. Preparation was computed, divergence evaluated, PB evaluated, and effect
performed only after all gates. This directly confirms `3M`'s central claim.

## 22. Identity/freshness

Evidence is repository-local because PER/ECP lookup and current-file hashing
are rooted in the invocation's `HarnessPath`. Two repositories with the same
`per_id` produced different divergence results from their own current files;
no cross-repository evidence reuse occurred. Operation identity is `{per_id,
ecp_id}`; HATP approval evidence separately binds HEAD, branch, and task where
applicable.

## 23. Restart/idempotency

- denied attempt then retry: evidence recomputed; later ALLOW completed;
- divergence then correction: first result `conflict`, retry `pending`, then
  effect completed;
- successful re-entry: current state recomputed as `already_reverted`, path
  skipped, `reverted=False`, status remained completed;
- dry-run repetition is equivalent and creates no artifacts;
- each real attempt creates the existing per-attempt RER audit receipt; no new
  readiness artifact or cache exists.

## 24. Side effects

Preparation itself is read-only. A dry-run creates neither RER nor root
mutation. A real attempt creates the existing bounded RER before authority
gates and updates it for audit/restart; this is record-state mutation, not the
root file effect. No root write/unlink occurs before HATP/PB allows it.

## 25. Product-value adjudication

- **Consumption gain:** none; evidence already affected behavior.
- **Choreography reduction:** one follow-up `rollback-execution show` command
  is no longer needed to see post-evidence terminal details.
- **Visibility gain:** real and useful, especially on denials/failures.
- **Governance gain:** no new authority, safety gate, or contract.

Before `3M`, evidence was internally computed, consumed, and persisted but
needed a second command for complete inspection. After `3M`, the initiating
command immediately returns/surfaces it.

## 26. Candidate A completion verdict

**B. CANDIDATE A WAS ALREADY FUNCTIONALLY COMPLETE; 3M ADDS EVIDENCE
VISIBILITY ONLY.**

If Candidate A's objective is automatic preparation and pre-effect
consumption, it was complete before selection. `3M` closes an operator
observability/usability gap, not a functional consumption gap.

## 27. Release significance

**Recommendation: bundle with the next mature capability.** The change is
patch-compatible and useful, but no authority, safety, or functional
consumption capability changed. `v0.4.2` remains unchanged; no `v0.4.3`, tag,
release, or publication was created in this phase. Phase `3N` should make the
human product/release decision.

## 28. Fresh tests

`tests/test_phase_149o_20l_7o_3m_1_independent_rollback_readiness_evidence_consumption_verification.py`
contains 26 independent tests. Result: **26 passed**. Categories cover fixed
pre-`3M` execution, dry-run, evidence consumption, all terminal paths,
returned/persisted equality, non-authority, PB/HATP sequencing, freshness,
no readiness cache, retry/idempotency, CLI/JSON, runtime, schema, consumers,
and A/B comparison.

## 29. A/B comparison

Identical fresh scenarios against A=`7b193145` and B=current post-`3M` showed
the same status, effect, RER evidence, authority behavior, and idempotency.
The bounded difference is result/output visibility: the baseline completed
result omitted both evidence keys while its RER contained them; B returns
them immediately.

## 30. Regressions

- rollback/3F/3F.1/AG5/HATP/CLI/core subset: **188 passed**, 4,378
  deselected;
- legacy `18D` suite: **20 passed, 5 failed** on current and identically
  **20 passed, 5 failed** at pre-`3M` `7b193145`; failures are frozen-history
  assertions, not functional regressions;
- Permission Broker, mutation permission, push, publication,
  rollback-approval persistence/validation, and RI combined: **601 passed**;
- publication packaging environment: 2 tests could not run because the
  active Python lacks the optional `build` module; the same suite excluding
  those packaging-only cases passed **85/85**;
- RI/Advisory 3J + 3J.1: included, **46 passed**.

## 31. Fast Green

Fixed baseline/candidate attribution is recorded in
`.pcae/fast-green-attribution/` and the canonical metadata. The final
machine-produced result is populated after the verification commit is frozen;
functional attributable regressions must remain zero for completion.

## 32. Findings

### NB-1 — repository-wide readiness wording was overbroad

Explicit readiness-named types exist in unrelated, non-AG5 subsystems. No
distinct AG5 readiness concept exists. **NON-BLOCKING:** the scoped design and
implementation conclusion remains correct.

### NB-2 — human output is summarized asymmetrically

Success represents `file_plan` via per-file results; dry-run represents the
divergence dict via `would_block`; JSON provides full evidence. **NON-BLOCKING:**
no result is misleading and authority is never implied.

### INF-1 — state-sensitive frozen-history suite

The five `18D` failures compare current history with a historical phase-entry
snapshot and reproduce identically before `3M`. **CONFIRMED, NON-BLOCKING,
NOT REPAIRED.**

### INF-2 — optional packaging dependency absent

Two representative publication packaging tests require `python -m build`,
which is unavailable in this interpreter. **ENVIRONMENTAL, NON-BLOCKING.**

**Blocking findings: 0.**

## 33. Final verdict

```text
ROLLBACK PREPARATION / EVIDENCE:
ALREADY AUTOMATIC BEFORE 3M

MANUAL DRY-RUN PREREQUISITE:
NONE

3M PRODUCT CHANGE:
EVIDENCE VISIBILITY / IMMEDIATE SURFACING

NEW AUTHORITATIVE READINESS:
NOT REQUIRED

EVIDENCE:
ALREADY CONSUMED PRE-EFFECT

EVIDENCE NON-AUTHORITY:
VERIFIED

PERMISSION BROKER:
SEPARATE / PRESERVED

HUMAN TRIGGER:
PRESERVED

HATP:
UNCHANGED

RUNTIME:
Observed / observe / unavailable

ATTRIBUTABLE REGRESSIONS:
0 required; final machine attribution recorded at completion

CANDIDATE A:
ALREADY FUNCTIONALLY COMPLETE; 3M ADDS VISIBILITY ONLY

BLOCKING:
0
```

Production source modified: **NO**. Publication performed: **NO**. Article:
**STOPPED**. Private research repository: **not inspected**.

## 34. Recommended next phase

**149O.20L.7O.3N — Post-Rollback Evidence Visibility Release and Capability
Priority Decision.**

That decision-only phase should decide whether the evidence-visibility patch
merits a quick patch release or should be bundled with the next mature
capability, remove Candidate A from the functional consumption-gap queue, and
select the next genuine capability gap. Stop after `3M.1`.
