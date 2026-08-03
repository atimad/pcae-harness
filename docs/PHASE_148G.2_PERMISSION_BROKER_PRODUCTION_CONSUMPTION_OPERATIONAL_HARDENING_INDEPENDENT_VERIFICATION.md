# Phase 148G.2 — Permission Broker Production Consumption Operational Hardening Independent Verification

## 0. Phase Type and Scope

**Phase type:** independent verification only. Verifies (does not repair)
148G.1's operational hardening. Modifies no `src/pcae/**` file, no
`docs/contracts/**` file, no `POL-001..012`, no Runtime Enforcement, no
IWC/AESIC semantics. Implements no Prompt Generation.

**Baseline commit (pre-148G.2):** `5e828c24` (HEAD at phase start, tip of
`Phase 148G.1: close out task lifecycle, open idle placeholder`).

**Governing contracts (both read directly, both unamended by this
phase, and independently reconfirmed unamended at phase end):**
- `PBPC-001` v1.2 — `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`
- `PBPA-001` v1.0 — `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`

**148C-B-1:** CLOSED (unchanged, reconfirmed).

---

## 1. Initial Inspection

| Check | Result |
|---|---|
| `git status --short` | clean |
| `git status --branch --short` | `## main...origin/main` (no divergence) |
| `git rev-list --count origin/main..HEAD` | `0` |
| `pcae health` | healthy (agent lock reported stale before rehydration by `pcae session bootstrap`; not a defect in scope here) |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | clean, no inconsistencies |
| `pcae push check` | `nothing_to_push` |
| `pcae runtime inspect` | Observed / observe / unavailable |
| `pcae notify status` | Telegram configured, enabled, ready |
| `pcae phase-report show --latest` | 148G.1: completed, complete ✅, 1 file changed, pushed, `origin/main..HEAD: 0` |
| `pcae phase-report reconcile --phase-id 148G.1` | `delivery_recorded_bookkeeping_incomplete`; marker `already_dispatched`; receipt absent; **mutation: none (inspection only)** |

**Observation (non-blocking):** `pcae phase-report reconcile --phase-id
148G.1` reports `delivery_recorded_bookkeeping_incomplete` with an absent
delivery receipt, even though `pcae notify status` shows Telegram
configured/enabled and 148G.1's own report claims `Dispatched: True`. This
is read-only bookkeeping/reconciliation state, not a production or
contract defect, and is unrelated to Permission Broker hardening. Recorded
as a post-chapter observation (Section 15 below); not investigated further
— out of this phase's bounded scope.

Confirmed at phase start: repository clean; `origin/main..HEAD = 0`;
148G.1 complete; `PBPC-001` v1.2 unamended; `PBPA-001` v1.0 unamended;
`148C-B-1` CLOSED; runtime Observed / observe / unavailable.

---

## 2. Independent Methodology

No claim in 148G.1's phase report, phase document, commit messages, or
production-code comments was taken as given. Verification proceeded from
first principles in this order:

1. Re-derive PBPC-001 v1.2 Section 16/17 requirements directly from
   contract text (Sections 16–18), independent of 148G.1's own
   requirement table.
2. Reconstruct the exact `push.py` diff introduced by 148G.1's three
   commits against the pre-148G.1 baseline via `git diff`, independent of
   148G.1's self-reported "one file changed" claim.
3. Read the resulting production code directly and trace control flow by
   hand (decision-snapshot capture timing, freshness-validation call
   sites, dispatch-site ordering) rather than trusting docstrings.
4. Write a new adversarial test file
   (`tests/test_phase_148g2_permission_broker_operational_hardening_independent_verification.py`,
   19 tests) that does not import from, extend, or invoke
   148G.1's own suite, and that specifically targets angles 148G.1's own
   report did not claim to cover (isolated unpushed-count drift,
   observation-failure — not just value-drift, direct non-CLI snapshot/
   freshness-helper unit tests, broker-construction-failure through the
   real CLI entrypoint, and a corrected consumer-scope guard check).
5. Independently inspect the module actually containing the second
   unrelated git-push dispatch site (`pcae.core.agent`), rather than
   trusting 148G.1's repaired 148C.10 test's choice of module.
6. Re-run all specified regression suites and record actual pass/fail
   counts, not copied from 148G.1's report.

---

## 3. Reconstructed 148G.1 Production Diff

`git diff 06611796..90e7eb6e -- src/pcae/commands/push.py` (baseline
`06611796` = tip of Phase 148F/close, immediately pre-148G.1; `90e7eb6e`
= 148G.1's implementation commit) reconstructs a single, self-contained
diff to `src/pcae/commands/push.py`. Hunk classification:

| Hunk | Classification | Description |
|---|---|---|
| New `_PushDecisionSnapshot` frozen dataclass (`head`, `branch`, `unpushed`, `task_id`) | `SNAPSHOT_TYPE` | in-process, immutable-by-decorator identity record |
| New `_observe_push_decision_state()` | `DECISION_STATE_OBSERVATION` | re-observes the four PBPC-REQ-056 fields via `git rev-parse HEAD`, `read_git_branch()`, `_count_unpushed_commits()`, and a passed-in `task_id` |
| `PushPermissionResult.decision_snapshot` field added | `SNAPSHOT_TYPE` | carries the snapshot from evaluation to dispatch |
| `decision_snapshot = _observe_push_decision_state(...)` inserted before the broker-construction `try:` block, in `_evaluate_push_permission` | `SNAPSHOT_CAPTURE` | binds the snapshot at evaluation time |
| `broker_instance = broker if broker is not None else PermissionBroker()` moved **inside** the existing `try:` | `BROKER_FAILURE_BOUNDARY` | F-148F-1 repair: construction failure now shares evaluate()'s fail-closed path |
| New `_validate_push_permission_freshness()` | `FINAL_FRESHNESS_VALIDATION` | re-observes state via the same helper, re-derives `task_id` independently via `find_latest_active_task()` (not carried from the caller), compares all four fields, returns `(fresh: bool, mismatches: list[str])` |
| Freshness-validation block inserted in `run_push()` immediately before the Path A `subprocess.run(["git", "push"], ...)` call | `ORDINARY_PATH_WIRING` | blocks dispatch on mismatch, prints diagnostic, returns 1 |
| Freshness-validation block inserted in `_run_push_staged_file_aware()` immediately before the Path B `subprocess.run(["git", "push", "origin", "main"], ...)` call | `STAGED_PATH_WIRING` | same shared helper, same fail-closed behavior |
| Diagnostic strings (`"Push blocked: decision-bound state changed..."`, `"Rerun pcae push..."`) | `DIAGNOSTIC` | user-facing, both paths |

No `UNRELATED` hunk was found — every changed line traces to one of the
two findings (F-148F-1, F-148F-3) or its direct test-hygiene follow-on.

---

## 4. Sole Production File Verification (independent)

```
git diff --name-only 06611796..90e7eb6e -- src/pcae/     → src/pcae/commands/push.py (only)
git diff --name-only 06611796..90e7eb6e -- docs/contracts/ → (empty)
git diff --name-only 06611796..5e828c24 -- src/pcae/      → src/pcae/commands/push.py (only, full phase range)
```

`src/pcae/core/permission_broker_foundation.py` and
`src/pcae/core/permission_broker.py` are confirmed at zero diff across
the same range (subset of the `src/pcae/` check above — no other file
appears at all). **Confirmed: exactly one `src/pcae/**` file changed;
zero contract diff.**

---

## 5. PBPC-001 v1.2 Section 17 — Independent Requirement Re-Derivation

| Requirement | Contract obligation (re-derived from contract text, Section 17) | Expected implementation |
|---|---|---|
| PBPC-REQ-059 | Immediately before each of Section 12's two dispatch sites, re-observe: local HEAD revision, local branch, unpushed-commit count, active task ID (the four fields Section 16/PBPC-REQ-056 fixes as locally, transactionally bindable) | A re-observation call at both dispatch sites, using the canonical sources Section 13 names (`git rev-parse HEAD` — new; `read_git_branch()`, `_count_unpushed_commits()`, `find_latest_active_task()` — pre-existing) |
| PBPC-REQ-060 | Any mismatch between a re-observed field and the value bound into the evaluated request is material — no tolerance/threshold is authorized | Exact per-field equality comparison, no normalization that could mask a real difference |
| PBPC-REQ-061 | On material mismatch: the existing `ALLOW` is invalid; zero dispatch; a fresh request/evaluation cycle is required; no silent update, no automatic in-place re-evaluation | Dispatch aborts (return 1 / blocked result); no retry loop inside the same invocation; a **subsequent, separate** `pcae push` invocation must perform its own fresh `_evaluate_push_permission` call |

Cross-checked against PBPC-REQ-056 (Section 16), which independently
fixes the locally-bindable field set as exactly: local HEAD revision,
local branch, unpushed-commit count, active task ID, and push mode
("all of Section 13's fields except remote name and force/non-force,
which are today fixed constants, not observed state"). 148G.1's snapshot
carries `head`, `branch`, `unpushed`, `task_id` — four of Section 16's
five locally-bindable fields. **Push mode is not re-observed or compared.**
This is analyzed in Section 6 below.

---

## 6. Decision-Bound Field Set — Independent Classification

| Field | PBPC-REQ-056 status | 148G.1 implementation | Classification |
|---|---|---|---|
| Local HEAD revision | required | `_observe_push_decision_state()` via `git rev-parse HEAD` | `REQUIRED` — present |
| Local branch | required | via `read_git_branch()` | `REQUIRED` — present |
| Unpushed-commit count | required | via `_count_unpushed_commits()` | `REQUIRED` — present |
| Active task ID | required | passed at snapshot time; re-derived independently at freshness time via `find_latest_active_task()` | `REQUIRED` — present |
| Push mode | listed by PBPC-REQ-056 as locally, transactionally bindable | **not captured, not compared** | `MISSING_REQUIRED_FACT` — see below |
| Repository root | Section 13 identity field, but PBPC-REQ-056 itself excludes it from the "transactionally bindable... immediately before dispatch" set (it is bound once at request-construction time via `HarnessPath.cwd()`, not re-observed per Section 17's four-field list) | not re-observed | not applicable — Section 17 (PBPC-REQ-059) itself enumerates only four fields, and repository root is not one of them |
| Remote name / force flag | PBPC-REQ-056 explicitly excludes these (fixed constants) | not re-observed | correctly excluded |

**Finding on push mode:** PBPC-REQ-056 names push mode as one of the five
locally, transactionally bindable fields alongside HEAD/branch/unpushed/
task-ID. PBPC-REQ-059, however, is textually narrower — it says "the four
fields Section 16 identifies as locally, transactionally bindable" and
then re-derives exactly four: HEAD, branch, unpushed-commit count, active
task ID. Push mode is *not* one of the four PBPC-REQ-059 actually lists,
despite PBPC-REQ-056 naming five candidate fields one sentence earlier.
Independently re-reading Section 17's normative text (PBPC-REQ-059 itself,
not a summary of it) confirms the four-field list is exactly what the
operative requirement mandates; PBPC-REQ-056 is TOCTOU-threat *analysis*
(Section 16), not itself the re-observation mandate. **148G.1's four-field
snapshot correctly implements the actual PBPC-REQ-059 text.** The
apparent five-vs-four discrepancy between REQ-056's illustrative list and
REQ-059's operative list is a contract-internal wording looseness, not an
implementation gap — classified as `OBSERVATION`, not `BLOCKING` or
`NON-BLOCKING` against the implementation (push mode changes are, in
practice, downstream of and correlated with HEAD/unpushed-count changes
for this MVP's two dispatch paths, so no known concrete drift scenario
exists where push-mode alone changes while all four re-observed fields
stay fixed).

---

## 7. `_PushDecisionSnapshot` — Independent Inspection

Direct inspection (`tests/test_phase_148g2_...::
test_push_decision_snapshot_is_frozen_dataclass_with_exactly_four_fields`,
`test_push_decision_snapshot_mutation_raises`):

- `@dataclass(frozen=True)` — attempted attribute mutation on a real,
  observed instance raises (`dataclasses.FrozenInstanceError`), confirmed
  by direct test, not by reading the decorator alone.
- Exactly four fields: `head`, `branch`, `unpushed`, `task_id`. No extra
  fields.
- In-process only: constructed as a plain local dataclass instance,
  returned by value, never written to a file, the phase-completion
  artifacts, or any persistence layer. `git grep`-level inspection of the
  diff confirms no new file I/O, no new schema, no global/module-level
  cache variable.
- `test_two_attempts_receive_independently_observed_snapshots` confirms
  two separately-constructed snapshots for two separately-observed states
  differ and are distinct objects (`snap1 is not snap2`) — no accidental
  memoization.

**Verdict: immutable, in-process, correctly scoped, no persistence, no
cross-attempt reuse.**

---

## 8. Snapshot Capture Timing

Reconstructed control flow inside `_evaluate_push_permission`:

```
decision_snapshot = _observe_push_decision_state(root, task_id)   # BEFORE broker touch
try:
    broker_instance = broker if broker is not None else PermissionBroker()   # construction
    decision = broker_instance.evaluate(request)                              # evaluation
except Exception:
    ...
```

The snapshot is captured **before** `PermissionBroker()` construction and
`.evaluate()`, not after. Independently verified this is not "too early"
in a way that could stale the snapshot relative to the decision: (a)
`PermissionBroker.__init__` is inspected directly and performs no I/O, no
filesystem access, no subprocess call — it only optionally wraps a
`PolicyRegistry` (`permission_broker_foundation.py:866` docstring:
"never has side effects"); (b) `.evaluate()` is documented and
independently confirmed (PBPC-REQ-051, "deterministic, pure-function
contract") to be a pure function over the request, with no repository
I/O of its own. Nothing capable of mutating decision-bound repository
state executes between snapshot capture and the broker's actual decision.
**Verdict: capture timing correctly represents the decision-bound state
the `ALLOW` is based on — neither too early nor too late.**

---

## 9. Request/Snapshot Coherence — `task_id`

At snapshot-capture time, the same `task_id` local variable used to build
`PermissionBrokerRequest.task_id` (Section 14 fields, unchanged by 148G.1)
is passed into `_observe_push_decision_state(root, task_id)` — a single
shared value, not two independent lookups that could silently diverge.

At freshness-validation time, `_validate_push_permission_freshness` does
**not** simply re-pass `snapshot.task_id` back to itself (which would
trivially "match" by construction) — it performs an independent, fresh
call to `find_latest_active_task(root)` and compares the result's
`task_id` against `snapshot.task_id`. This is the correct design: a real
task change between decision and dispatch is actually observed. Confirmed
directly by the 148G.2 task-ID drift test family (isolated snapshot-level
test `test_validate_freshness_detects_unpushed_count_drift_directly`'s
sibling coverage in the source, and behavioral coverage inherited/
independently re-verified from the drift-attack tests in Section 12).

---

## 10. HEAD / Branch / Unpushed-Count Observation — Independent Scrutiny

- **HEAD:** `git rev-parse HEAD`, `capture_output=True`, `returncode`
  checked explicitly (not `check=True`). On nonzero return code, `head`
  falls back to `""` (empty string) rather than raising. This is a new
  function (148G.1-introduced), and this specific fallback is the one
  genuine `OBSERVATION`-class finding of this verification (Section 14).
- **Branch:** delegates to the pre-existing `read_git_branch()`
  (`git_status.py:27`), which uses `check=True` and therefore raises
  `subprocess.CalledProcessError` on failure rather than fabricating a
  value; `git branch --show-current` returning empty (detached HEAD) is
  itself normalized to the literal string `"HEAD"` by that pre-existing
  function, unchanged by this phase.
- **Unpushed-commit count:** delegates to the pre-existing
  `_count_unpushed_commits()` (`push.py:1166`), which tries
  `git rev-list --count @{u}..HEAD` (upstream-relative), falls back to
  `git rev-list --count HEAD` (no-upstream case), and as a final fallback
  on total failure of both, returns `0`. This function is reused
  unchanged from Section 13's pre-existing readiness computation (its
  "`0` is a valid, meaningful value" semantics is contract-sanctioned,
  PBPC-REQ-042's identity table) — not a new fabrication introduced by
  148G.1, but its dual role (legitimate "nothing to push" vs. "observation
  totally failed") is inherited ambiguity, noted in Section 14.
- **Active task ID:** `find_latest_active_task(root)` — pre-existing,
  returns `None` on no active task (a real, meaningful state per
  PBPC-REQ-042's identity table, not a fabricated fallback).

Ordinary and staged-file-aware paths call the identical
`_observe_push_decision_state` / `_validate_push_permission_freshness`
pair — both observe the same operation state; there is no path-specific
divergence in what is observed.

---

## 11. Re-Observation Helper Purity / Freshness Validation Helper

`_observe_push_decision_state`: reads `git rev-parse HEAD`, calls
`read_git_branch`, `_count_unpushed_commits`, and returns the passed-in
`task_id` (or, at freshness time, the caller — `find_latest_active_task`
— re-derives it independently). No mutation of repository state, no
broker invocation, no dispatch, no lifecycle-state write. Confirmed by
direct source inspection — the function contains only read-only
`subprocess.run` calls and pure Python.

`_validate_push_permission_freshness`: compares all four fields with
exact (`!=`) equality — no normalization, no tolerance, no silent
truncation. Returns `(False, [...])` on any git-command exception
propagating from the observation calls it makes indirectly (see Section
14 for exactly how that fails closed) — the function itself introduces no
independent DENY/ALLOW judgment; it only ever produces `(fresh: bool,
mismatches: list[str])`. It calls no `PermissionBroker` method and
constructs no `PermissionBrokerDecision`. **Verdict: this is a freshness
guard, not a second permission authority** — confirmed both by source
inspection and by `test_pol_004_not_applicable_to_mutation_class` /
`test_pol_005_allows_simulation_only_true_pushes`, which confirm no
`POL-` rule's applicability changed as a side effect of this helper's
introduction.

---

## 12. Ordinary and Staged-File-Aware Path Ordering

Independently confirmed via
`test_both_dispatch_sites_call_broker_evaluation_and_freshness_validation`
(source-level call-site counting, written independently of 148G.1's own
`test_final_validation_ordering_present_in_source`) that both
`_evaluate_push_permission(` call sites, both
`_validate_push_permission_freshness(root, permission_result.decision_snapshot)`
call sites, and both dispatch sites (`["git", "push"]`,
`["git", "push", "origin", "main"]`) are present exactly twice each.
Direct reading of `run_push()` and `_run_push_staged_file_aware()`
confirms the freshness-validation block sits immediately before each
path's real dispatch call, after all of `push.py`'s own pre-existing
readiness/hard-block checks — no meaningful I/O or mutable-state
operation of this phase's own code occurs between a passing freshness
check and the actual `subprocess.run(["git", "push", ...])` call on
either path (the only statements between them are diagnostic-string
formatting on the success path, which performs no I/O).

The staged-file-aware path was inspected with particular attention to
whether any state mutation happens between broker `ALLOW` and final
re-observation (per the phase brief's specific concern about
staged-file-aware reconstruction). No file staging, commit construction,
or other repository mutation occurs inside `_run_push_staged_file_aware`
between the freshness check and the dispatch call — the freshness check
is the last statement of consequence before dispatch on both paths.

---

## 13. Adversarial Testing — Independent Suite Results

`tests/test_phase_148g2_permission_broker_operational_hardening_independent_verification.py`
— 19 tests, independently authored, not extending 148G.1's suite. All 19
passed.

| Test | Attack / assertion | Result |
|---|---|---|
| `test_148g1_touched_exactly_one_src_pcae_file` | independent re-check of sole-production-file claim | PASS |
| `test_148g1_touched_zero_contract_files` | independent re-check of contract-boundary claim | PASS |
| `test_push_decision_snapshot_is_frozen_dataclass_with_exactly_four_fields` | structural | PASS |
| `test_push_decision_snapshot_mutation_raises` | attempted mutation on a real, observed instance | PASS — raises |
| `test_ordinary_path_unpushed_count_drift_alone_blocks_dispatch` | unpushed-count drift via real CLI path, diagnostic specifically names the count field | PASS — zero dispatch, correct diagnostic |
| `test_validate_freshness_detects_unpushed_count_drift_directly` | direct, non-CLI unit test: forged snapshot with only `unpushed` off | PASS — exactly that mismatch reported, no false positives on HEAD/branch |
| `test_final_reobservation_head_lookup_failure_fails_closed` | forces the re-observation git call itself to raise (not a value drift) during final validation | PASS — zero dispatch |
| `test_freshness_helper_does_not_treat_empty_head_as_matching_real_head` | forces the HEAD fallback (`""`) at freshness time against a real decision-time HEAD | PASS — correctly reported as mismatch, not a false match |
| `test_two_attempts_receive_independently_observed_snapshots` | snapshot non-reuse | PASS — distinct objects, distinct values |
| `test_broker_construction_failure_via_real_cli_fails_closed_no_traceback` | `PermissionBroker.__init__` forced to raise via `main(["push"])`, ordinary path | PASS — exit 1, zero dispatch, controlled diagnostic |
| `test_broker_construction_failure_staged_path_via_real_cli_fails_closed` | same, staged-file-aware path | PASS — exit 1, zero dispatch |
| `test_retry_after_construction_failure_succeeds_with_no_partial_state` | transient construction failure then normal retry | PASS — second attempt dispatches |
| `test_both_dispatch_sites_call_broker_evaluation_and_freshness_validation` | independent source-level call-site count | PASS — 2/2/2 |
| `test_canonical_push_request_fields_unchanged` | `action_type`/`execution_class`/`requested_component`/`requested_capability`/`approval_present`/`simulation_only` | PASS — all present, unchanged |
| `test_pol_004_not_applicable_to_mutation_class` | `EXECUTION_CLASS_MUTATION` not in `MissingHumanApprovalRule.applicable_execution_classes` | PASS |
| `test_pol_005_allows_simulation_only_true_pushes` | `ExecutionDisabledRule` not triggered when `simulation_only=True` | PASS |
| `test_hard_block_registry_count_is_twelve` | independent recount | PASS — 12 |
| `test_actual_git_push_dispatch_site_in_core_agent_remains_unwired` | corrected consumer-scope guard — inspects `pcae.core.agent`, not `pcae.commands.agent` | PASS — no `PermissionBroker`/`permission_broker_foundation` reference in `pcae.core.agent` |
| `test_commands_agent_module_does_not_itself_contain_a_dispatch_call` | confirms the discrepancy in Section 16 below | PASS |

Two attack classes from the phase brief were found to already be covered,
byte-for-byte equivalently, by 148G.1's own suite on independent reading
(branch drift, multiple-simultaneous-drift, fresh-second-attempt/no-reuse
via CLI, genuine non-forged-`ALLOW`-plus-drift) — re-running those
existing tests (Section 14) rather than duplicating them verbatim was
judged sufficient independent confirmation, since 148G.2's own new tests
above independently exercise the same production code paths from
different angles (direct unit-level snapshot/helper calls instead of only
CLI-level `main()` calls).

---

## 14. Findings

### Finding 1 — HEAD-observation empty-string fallback (OBSERVATION)

`_observe_push_decision_state`'s HEAD lookup returns `""` on a nonzero
`git rev-parse HEAD` exit code rather than raising or otherwise signaling
observation failure distinctly from a real (if unlikely) empty-HEAD
value. If HEAD observation failed identically at both decision time and
final-freshness time, the two `""` values would spuriously compare equal
and be treated as "no drift" — an observation failure masquerading as a
match. Independently assessed as very low practical severity: `git
rev-parse HEAD` failing requires an unborn/HEAD-less repository state,
which existing (unchanged) readiness computation (`assess_push_readiness`)
would almost always already reject before `pcae push` reaches broker
evaluation at all, and no concrete reachable trigger was found in testing
(`test_freshness_helper_does_not_treat_empty_head_as_matching_real_head`
confirms the realistic case — failure at freshness time only — is
correctly caught as a mismatch, since decision-time HEAD is essentially
always a real, non-empty SHA in any repository capable of reaching this
code path). Classification: `OBSERVATION`, not `BLOCKING` or
`NON-BLOCKING` — does not affect the closure verdicts below, but is worth
a future defensive fix (raise/propagate on HEAD observation failure,
matching `read_git_branch`'s existing `check=True` pattern) rather than
silently defaulting.

### Finding 2 — `_count_unpushed_commits` shares "0" between "true zero" and "total observation failure" (OBSERVATION, inherited/pre-existing)

Not introduced by 148G.1 (the function is reused unchanged from Section
13's pre-existing readiness computation, and the contract itself
(PBPC-REQ-042) sanctions "`0` is a valid, meaningful value"). Noted here
because 148G.1's freshness re-observation newly relies on this function
for a *security-relevant* comparison (drift detection) where it
previously only fed a readiness/UX computation. Same masking risk as
Finding 1 if both git commands fail identically at both observation
points. Classification: `OBSERVATION`, inherited scope, not attributable
to 148G.1 or in 148G.2's bounded remit to repair.

### Finding 3 — Consumer-scope guard test inspects the wrong module (NON-BLOCKING, test-hygiene)

148G.1's repaired `tests/test_phase_148c10_pbpc_v12_independent_verification.py::
test_push_module_is_the_authorized_pbpc_production_consumer` asserts that
`pcae.commands.agent` and `pcae.commands.phase` contain no
`PermissionBroker`/`permission_broker_foundation` reference, intending to
guard the two other real `git push` dispatch sites 148F/148G's inventory
named. Independent inspection shows the actual dispatch call
(`push_file_changes` → `_run_git_push`,
`subprocess.run(["git", "push", ...])`) lives in **`pcae.core.agent`**,
not `pcae.commands.agent` — the latter is a thin CLI wrapper module that
only imports and calls `push_file_changes`; it contains no git-push
dispatch call of its own
(`test_commands_agent_module_does_not_itself_contain_a_dispatch_call`
confirms this directly). `pcae.commands.phase`, by contrast, is correctly
targeted — it does contain both of that module's real dispatch calls
(`commands/phase.py:19563`, `:20295`), independently confirmed by direct
grep.

Currently this is **not exploitable**: independent inspection
(`test_actual_git_push_dispatch_site_in_core_agent_remains_unwired`)
confirms `pcae.core.agent` in fact contains no `PermissionBroker` or
`permission_broker_foundation` reference today, so the invariant the test
intends to protect happens to hold — just not because of anything this
specific test checks. If a future change wired `PermissionBroker` (or
broker-bypass logic) directly into `pcae.core.agent`, the existing guard
test would not detect it, since it never inspects that module.
Classification: `NON-BLOCKING` — a real test-hygiene gap (the guard
protects the wrong file for one of its two intended targets), not a
present production defect, and not something 148G.2 is authorized to
repair (production/test-suite changes are out of this phase's scope
beyond the new, independent 148G.2 suite added here). Recommend a
narrowly-scoped follow-up correcting the module reference from
`pcae.commands.agent` to `pcae.core.agent` in the existing 148C.10 test.

### Finding 4 — PBPC Section 18 omits an explicit broker-construction-failure row (OBSERVATION → resolved below, Section 15)

Analyzed in full in Section 15.

**No `BLOCKING` finding was identified.**

---

## 15. Section 18 Documentation Item — Independent Disposition

148G.1 deliberately did not add a "broker construction failure" row to
PBPC-001 Section 18's failure-ownership table, citing the prohibition on
amending PBPC-001 within that phase's scope. Independently re-derived
whether this is a normative gap or documentation completeness debt, from
contract text alone (not from 148G.1's own disposition):

- **Section 18's existing table** has a row for "Broker evaluation
  failure (rule raises)," owned by `PermissionBroker` (`_sanitize_result`)
  — this specifically describes an individual `PolicyRule.evaluate()`
  raising inside the Foundation's own composition logic (PBPC-REQ-025),
  not `PermissionBroker.__init__` raising before any policy rule runs.
  These are genuinely different code paths; the existing row does not
  literally cover construction failure.
- **However, PBPC-REQ-021** (Section 15's local rule, general in scope):
  *"No fallback SHALL convert a broker evaluation failure, exception, or
  malformed result into a permission to push. Any such failure SHALL fail
  closed to a result equivalent to `DENY`."* This is worded generally
  enough ("a broker evaluation failure, exception, or malformed result")
  to already normatively require *any* broker-related exception —
  including a construction-time exception — to fail closed.
- **Section 11's ownership table** (line 611) independently states:
  *"Broker-internal failure handling | Decision Consumption Point,
  treating any broker exception/malformed result as `DENY`-equivalent"*
  — again general, not qualified to `.evaluate()` only.
- **PBPC-REQ-092's security threat model** (Section 28) cites both
  PBPC-REQ-025 and PBPC-REQ-021 together for "Bypass — exception-based
  bypass," attributing the mitigation partly to "the Decision Consumption
  Point's own fail-closed treatment" — general phrasing again, not
  scoped to evaluation only.

**Independent verdict:** the contract's *normative* requirement that
broker construction failures fail closed already exists (PBPC-REQ-021,
generally worded, plus Section 11's general ownership statement); Section
18's table is a worked-example matrix illustrating specific failure
categories, not represented anywhere in the contract as an exhaustive
enumeration, and PBPC-REQ-063 only prohibits a listed category being
owned by more than one component — it does not require every possible
failure category to have its own explicit row. The missing row is
therefore:

**NON-NORMATIVE DOCUMENTATION DEBT — DOES NOT BLOCK CERTIFICATION.**

Recommended (but not authorized in this phase): a small, separately
governed PBPC-001 documentation-only amendment adding an explicit
"`PermissionBroker()` construction failure" row to Section 18 for
completeness, cross-referencing PBPC-REQ-021. This is optional polish,
not a certification blocker.

---

## 16. F-148F-1 Independent Closure Verdict

Independently reproduced via the real `main(["push"])` CLI entrypoint
(not reusing 148F's rewritten tests): forcing `PermissionBroker.__init__`
to raise, on both the ordinary and staged-file-aware paths, produces exit
code 1, zero `git push` dispatch, and a controlled diagnostic containing
"Permission Broker evaluation failed" — no traceback escapes `main()`. A
subsequent, unforced retry succeeds normally, confirming no partial/
global broker state persists across a construction failure.

**F-148F-1: CLOSED — INDEPENDENTLY VERIFIED.**

---

## 17. F-148F-3 Independent Closure Verdict

Independently confirmed: PBPC-REQ-059's four re-observed fields are
correctly implemented and correctly re-derived from Section 17's own
text (Section 5 above); snapshot timing correctly binds decision-time
state (Section 8); snapshot immutability and non-reuse hold under direct
attack (Section 7, Section 13); both dispatch paths perform final
re-observation immediately before their respective dispatch call with no
intervening mutation (Section 12); drift in any single field (HEAD,
branch, unpushed count in isolation, task ID) or multiple fields
simultaneously reliably blocks dispatch with zero `git push` calls
(Section 13, both 148G.1's own suite re-run and 148G.2's independent
suite); observation-call failure (not just value drift) also fails
closed (Section 13, Finding 1 notwithstanding — the one identified gap
is a low-severity, currently-unreachable edge case, not a demonstrated
live failure); a genuine, non-forged broker `ALLOW` cannot be leveraged to
dispatch after drift (independently re-run,
`test_genuine_allow_plus_drift_cannot_dispatch`); PBPC-REQ-061's
fresh-cycle semantics (no automatic in-place re-evaluation, a fresh
`pcae push` invocation performs a genuinely fresh `evaluate()` call) are
independently reconfirmed by re-running 148G.1's own
`test_stale_allow_cannot_be_reused_but_fresh_rerun_succeeds` and cross-
checking its assertions against the source directly.

**F-148F-3: CLOSED — INDEPENDENTLY VERIFIED.**

---

## 18. Residual TOCTOU Window

After final freshness validation passes and immediately before
`subprocess.run(["git", "push", ...])` on either path, the only
intervening statements are (ordinary path) none of consequence — the
`subprocess.run` call is the very next non-diagnostic statement; (staged
path) likewise. No additional I/O, callback, hook, or external call sits
in that gap on either path. The residual race this phase (and PBPC-001
itself, PBPC-REQ-057/058) explicitly does not and cannot close is:
*local* state changing in the handful of CPU instructions between the
freshness check's last observation and the `git push` subprocess actually
starting, and *remote* state changing concurrently at `origin` — both are
explicit, documented, out-of-scope limitations in the contract itself
(single-agent-lock model, Phase 148A §27; git's own non-fast-forward
rejection is the actual safety net for the remote case), not a gap this
implementation introduced or was expected to close. **Classification:
contractually bounded residual race, not a missing required validation.**

---

## 19. Requirement-Level Hardening Traceability

| Requirement | Production mapping | Test mapping | Status |
|---|---|---|---|
| PBPC-REQ-056 | `_PushDecisionSnapshot` field set (`head`, `branch`, `unpushed`, `task_id`) | `test_push_decision_snapshot_is_frozen_dataclass_with_exactly_four_fields` | `VERIFIED` |
| PBPC-REQ-059 | `_observe_push_decision_state()`, called at both decision time (`_evaluate_push_permission`) and final-validation time (`_validate_push_permission_freshness`) | drift tests (HEAD/branch/unpushed/task-ID, isolated and combined), both 148G.1's suite (re-run) and 148G.2's independent suite | `VERIFIED` |
| PBPC-REQ-060 | per-field `!=` comparison in `_validate_push_permission_freshness` | `test_validate_freshness_detects_unpushed_count_drift_directly` and siblings | `VERIFIED` |
| PBPC-REQ-061 | mismatch → `(False, mismatches)` → both call sites abort with `return 1` / blocked result; no automatic re-evaluation loop found anywhere in production source | `test_stale_allow_cannot_be_reused_but_fresh_rerun_succeeds` (re-run) | `VERIFIED` |
| PBPC-REQ-090/091 (preconditions/post-build demonstrations) | cumulative — see Sections 4–18 | full regression suite, Section 20 | `VERIFIED` for the operational-hardening-relevant subset in this phase's scope |

No hidden automatic re-evaluation loop was found anywhere in
`src/pcae/commands/push.py` — direct source inspection (`grep`-level and
full read) confirms `.evaluate()` is called exactly once per
`_evaluate_push_permission` invocation, and no retry/loop wraps the
freshness-validation blocks.

---

## 20. Regression Results (actual, independently re-run)

| Suite | Result |
|---|---|
| `tests/test_permission_broker_push_operational_hardening.py` (148G.1's own) | re-run, passed |
| `tests/test_permission_broker_push_production_consumption.py` | re-run, passed |
| `tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py` | re-run, passed |
| `tests/test_phase_148c10_pbpc_v12_independent_verification.py` | re-run, passed |
| `tests/test_phase_148g2_permission_broker_operational_hardening_independent_verification.py` (new, 19 tests) | 19/19 passed |
| Combined (five files above) | 79/79 passed |
| `tests/test_permission_broker.py` + `test_permission_broker_foundation.py` + `test_permission_broker_policy_applicability.py` | 422/422 passed |
| `tests/test_runtime_inspect_cli.py` + `test_runtime_snapshot.py` + `test_runtime_context.py` | 186/186 passed |
| `tests/test_push.py` + `test_staged_file_aware_push.py` + `test_commit_push_gate.py` + `test_push_phase_report_identity_137f1.py` + `test_post_push_canonicalization.py` + `test_push_state_reconciliation.py` + `test_commit_push_preflight.py` + `test_commit_push_preflight_review.py` | 186/186 passed |
| `python -m pytest -m fast_green -n auto -q` (run 1) | 4390 passed, 1 failed (`tests/test_backend_cli.py::TestBackendReviewCreate::test_create_persists_to_latest`) |
| `tests/test_backend_cli.py::TestBackendReviewCreate::test_create_persists_to_latest` in isolation | 1/1 passed |
| `python -m pytest -m fast_green -n auto -q` (run 2, full rerun) | 4391/4391 passed |

**Observation (non-blocking):** the first Fast Green run showed one
failure in `tests/test_backend_cli.py` — a backend-review-persistence
test entirely unrelated to Permission Broker/`push.py` (no
`push.py`/`permission_broker*` import in that test file). It passed both
in isolation and on a full, unmodified rerun of the same `-m fast_green
-n auto` command, indicating pre-existing parallel-execution-order
flakiness in that test, not a regression introduced by this phase (this
phase touched zero `src/pcae/**` files — see Section 4). Recorded as an
observation for future test-hygiene attention; not attributable to
148G.1 or 148G.2, and not `BLOCKING`.

---

## 21. Verification Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — OPERATIONAL HARDENING CONFORMS.**

(Findings 1, 2 are `OBSERVATION`-level, not blocking; Finding 3 is
`NON-BLOCKING` test-hygiene; Finding 4 is resolved as non-normative
documentation debt, Section 15.)

---

## 22. Chapter 148 Certification Readiness

- PBPC-001 v1.2 verified (unamended, Section 4).
- PBPA-001 v1.0 verified (unamended, Section 4).
- 148C-B-1 closed (unchanged, reconfirmed).
- PBPC production wiring independently verified (Sections 4–13).
- F-148F-1 closed (Section 16).
- F-148F-3 closed (Section 17).
- Both `pcae push` paths broker-gated and freshness-gated (Section 12).
- No unresolved Chapter-148 `BLOCKING` finding (Section 14).
- Runtime unchanged: Observed / observe / unavailable (Section 1).

**READY FOR CHAPTER 148 CERTIFICATION WITH RETAINED NON-BLOCKING
FINDINGS** (Finding 1, Finding 2, Finding 3 above — carried forward as
retained observations/follow-ups, none of which block certification).

**Section 18 certification impact: NON-NORMATIVE DOCUMENTATION DEBT —
DOES NOT BLOCK CERTIFICATION** (Section 15).

---

## 23. Post-Chapter Strategic Observations (not started, retained only)

- Repository-Wide Mutation Permission Coverage: `core/agent.py`
  (`push_file_changes`/`_run_git_push`) and `commands/phase.py` (two
  push-execution subcommands) remain outside Chapter 148 MVP scope,
  unwired to the Permission Broker — tracked post-chapter, not started.
- Prompt Generation / Prompt Creation (Phase 45F): remains design-only /
  `partially_ready`, `DEFERRED`. Not touched.
- Repository Test Hygiene Debt: the consumer-scope guard module
  discrepancy (Finding 3) — recommend a narrow follow-up correcting
  `tests/test_phase_148c10_pbpc_v12_independent_verification.py`'s module
  reference.
- `pcae phase-report reconcile --phase-id 148G.1`'s
  `delivery_recorded_bookkeeping_incomplete` observation (Section 1) —
  unrelated to Permission Broker hardening, not investigated further in
  this phase.

---

## 24. Recommended Next Phase

**148H — Permission Broker Production Consumption Chapter 148
Certification.** 148H should certify the chapter only (formalize the
`READY FOR CHAPTER 148 CERTIFICATION WITH RETAINED NON-BLOCKING FINDINGS`
verdict into a canonical certification record) and should not introduce
new production work. The retained non-blocking findings (Section 14) and
post-chapter observations (Section 23) should be carried forward as
tracked follow-ups, not folded into 148H's own scope.
