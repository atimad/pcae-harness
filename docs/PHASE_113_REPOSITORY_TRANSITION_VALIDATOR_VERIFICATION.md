# Phase 113V — Repository Transition Validator Verification & Compatibility

**Status:** Complete. Verification only — no integration, no enforcement,
no Telegram dispatch repair.

## Purpose

Independently re-verify the observation-only Repository Transition
Validator prototype implemented in 113U
(`src/pcae/core/repository_transition_validator.py`) against the
contract frozen in 113T and the architecture defined in 113S. Confirm
model purity, determinism, the verdict contract, the 7 implemented
invariants, the canonical promotion model, the notification eligibility
model, and model-agnostic behavior — and confirm compatibility with
every subsystem this prototype touches or is adjacent to.

## 1. Validator Model Purity — Verified

Directly confirmed, not assumed:

- `grep -rln "repository_transition_validator" src/` returns only the
  module's own file — no other `src/` file references it.
- `grep -rn "validate_transition\|RepositoryState\|TransitionVerdict\|ArtifactState" src/pcae/commands/`
  returns nothing — zero command-path integration.
- `git diff --stat 785f6c64~1 HEAD -- src/` (the entire 113S→113U
  commit range) shows exactly one file changed under `src/`:
  `src/pcae/core/repository_transition_validator.py` (344 lines added,
  0 removed elsewhere). No other source file was touched across the
  whole sequence.
- `git diff --stat 785f6c64~1 HEAD -- src/pcae/core/runtime_snapshot.py src/pcae/core/advisory_runtime.py src/pcae/core/permission_broker.py src/pcae/core/phase_report_trust.py`
  is empty — none of these four files changed at all across 113S–113U.
- The only importer of the module, anywhere in the repository, is
  `tests/test_repository_transition_validator.py`.

**Conclusion**: no lifecycle enforcement, no report promotion
enforcement, no notification enforcement, and no Runtime/Advisory/
Permission Broker behavior change exists anywhere in this prototype or
its surrounding phases. This is exactly what "observation-only" claims.

## 2. Deterministic Behavior — Verified

Re-ran the same `(RepositoryState, ProposedTransition,
ExpectedTargetState)` input through `validate_transition` 50 times in a
single process: all 50 results had an identical `verdict` and an
identical `violations` tuple. Combined with the module containing no
`time`, `random`, `os.environ`, or filesystem access anywhere in its
implementation (confirmed by reading the full 344-line module), this
establishes determinism structurally, not just empirically for this one
run.

## 3. Verdict Contract — Verified

`{v.value for v in TransitionVerdict}` == exactly
`{"accept", "reject", "quarantine", "requires_human_review"}` — four
values, no more, no fewer. No fifth value exists in the enum.

## 4. Implemented Invariants — Re-Verified

`STRUCTURAL_INVARIANTS` contains exactly the 7 families the 113U brief
committed to, confirmed by direct set comparison against the module's
own frozen tuple:

1. `phase_identity_consistency`
2. `metadata_consistency`
3. `report_completeness`
4. `recommended_next_phase_presence`
5. `canonical_promotion_eligibility`
6. `notification_eligibility`
7. `no_execution_availability_unless_contracted`

All 7 are independently exercised by `tests/test_repository_transition_validator.py`'s
36 tests (re-run clean in this phase, see §"Tests Run" below), each
with both a triggering case and a non-triggering case.

## 5. Canonical Promotion Model — Verified

Iterated all 6 `ArtifactState` values against
`promotion_allowed(state, ArtifactState.CANONICAL)`: `True` only for
`ArtifactState.CERTIFIED`, `False` for `DRAFT`, `BLOCKED`, `REJECTED`,
`QUARANTINED`. Cross-checked against `validate_transition` itself
(not just the standalone helper): proposing `ArtifactState.CANONICAL`
as a target from a `BLOCKED` current state rejects via the
`canonical_promotion_eligibility` invariant; from `CERTIFIED`, accepts.

## 6. Notification Eligibility Model — Verified

`notification_eligible()` re-confirmed to require all 5 conditions
simultaneously (finalized, certified, push clean, not already
dispatched, transport enabled) — a fully-eligible `RepositoryState`
returns `(True, ())`; flipping any single one of the 5 fields
independently (already tested in 113U's own suite, re-run clean here)
flips eligibility to `False` with a non-empty reason. **Real Telegram
dispatch was not touched or repaired in this phase** — this model
remains a pure structural check, disconnected from any live transport.

## 7. Model-Agnostic Behavior — Verified

`dataclasses.fields()` on both `RepositoryState` and
`ProposedTransition` confirmed directly: neither type has a field named
`agent`, `agent_id`, `model`, `model_id`, `proposer`, or `identity` (or
any field at all beyond `kind`/`payload` for `ProposedTransition`).
113U's own test (`test_agent_identity_in_payload_does_not_affect_verdict`)
re-ran clean, confirming a `payload={"agent": "Claude"}` vs.
`payload={"agent": "Claude-DeepSeek"}` vs. no `agent` key at all
produce byte-identical verdicts for the same `RepositoryState`.

## 8. Compatibility Verification

| Subsystem | Compatibility finding |
|---|---|
| 113S architecture | The 14-component `RepositoryState` model, 12 `TransitionKind` values, 4 `TransitionVerdict` values, and 6 `ArtifactState` values in the prototype match 113S's architecture document field-for-field (verified by direct comparison against `docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR.md`). |
| 113T contract | The prototype's invariant `classification`/`force` fields, the canonical-promotion-only-from-Certified rule, and the notification-eligibility 5-condition model all match 113T's frozen contract (`docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR_CONTRACT.md`) exactly. |
| 113U prototype | Re-verified in place — no drift since 113U; the module is unchanged by this phase. |
| Runtime Snapshot | Unchanged (confirmed via `git diff --stat`, §1). The validator never imports or calls into `runtime_snapshot.py`. |
| Advisory Runtime | Unchanged (confirmed via `git diff --stat`, §1). No overlap: the validator does not evaluate advisory recommendations. |
| Permission Broker | Unchanged (confirmed via `git diff --stat`, §1). The `no_execution_availability_unless_contracted` invariant checks a `RepositoryState` field the caller must populate from the Broker's real status — it does not query the Broker itself, and does not grant or deny anything. |
| Phase report trust | Unchanged (confirmed via `git diff --stat`, §1). `validate_finalization_gate()`/`validate_phase_identity()`/`validate_phase_report_trust()` remain the actual, sole enforcement mechanism for `pcae phase complete` and `pcae task finish --commit` today — the prototype does not intercept, wrap, or shadow any of them. |

No incompatibility found in any of the six.

## 9. Future Integration Targets

**Ready for future enforcement** (pure, structural, no live I/O
required beyond what a caller already has available at
`pcae phase complete`/`pcae task finish --commit` time):

- `phase_identity_consistency`
- `metadata_consistency`
- `recommended_next_phase_presence`
- `canonical_promotion_eligibility`
- `no_execution_availability_unless_contracted`

**Ready with caveats** (structurally implemented, but eligibility
depends on state fields a real caller must populate honestly from live
sources — the validator itself does no I/O):

- `report_completeness` — caller must supply real `test_results`/`commits`,
  not synthetic placeholders.
- `notification_eligibility` — caller must supply the real
  `.last-notified.json` state and real transport-enabled status.

**Still need live I/O** (not implemented in this prototype; require a
future adapter layer that reads git/filesystem state and populates
`RepositoryState` before calling the pure validator):

- `commit_lineage` — requires reading real `git log` commit messages
  and cross-checking them against the claimed phase_id (the exact 113D
  defect class).
- `architecture_status_consistency` — requires reading
  `build_architecture_status()`'s live output.
- `push_state_consistency` — requires a live
  `git rev-list --left-right --count origin/main...HEAD`.
- `test_result_consistency` — requires reconciling structured
  `test_results` fields against an actual just-run pytest invocation,
  not merely checking the fields are non-empty.

**The 113S/113T-documented single-canonical-transition-authority
requirement** (`pcae phase complete` and `pcae task finish --commit`
must route through one promotion function) remains entirely
unaddressed by this prototype — it requires modifying
`commands/phase.py` and `commands/task.py`, which is explicitly out of
scope for an "observation-only" prototype and remains a target for a
future integration phase (113W, per this phase's own recommendation).

**The notification asymmetry** (`pcae skill invoke phase-finalization
<phase-id>` reports `target_unresolved` for every 113X.*/113S/113T/113U/
113V-style special phase ID, while the phase's own canonical report can
be fully Certified/Canonical) was re-checked directly in this phase:

```
pcae skill invoke phase-finalization --target 113V --target-type phase
```

still returns `blocked` / `target_unresolved: Phase '113V' not found in
roadmap registry` — reconfirmed present, unchanged, and, per this
phase's explicit instruction, **not repaired here**. It remains
documented as a future validator integration target exactly as 113T/113U
left it.

## Tests Run

- `python -m pytest tests/test_repository_transition_validator*.py -n auto -q -ra --durations=100` — 246 passed.
- `python -m pytest tests/test_*runtime* tests/test_*contract* tests/test_*autonomy* tests/test_*plugin* tests/test_*advisory* -n auto -q -ra --durations=100` — 3784 passed.
- `python -m pytest -m "fast_green" -n auto -ra --durations=100` — 4390 passed.
- `python -m pytest tests/test_task*.py tests/test_*task* tests/test_*phase* tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_notifications.py tests/test_notifications_cli.py tests/test_telegram_notifications.py -n auto -q -ra --durations=100` — **encountered a reproducible environmental hang, documented below rather than a clean pass/fail count.**

### Environmental Finding: Reproducible macOS Fork-Contention Hang (Unrelated to This Phase's Work)

While running the required task/phase/notifications test command above, the
run repeatedly stalled (confirmed via process CPU-time sampling showing zero
progress across multiple real-time intervals, then confirmed via `sample`
stack traces) inside a `subprocess.run(..., capture_output=True)` call --
most directly reproduced as `pcae project-state --json` (one of
`test_phase85_integration.py`'s six commands) taking ~16s in isolation but
stalling indefinitely when forked from within an already-large pytest
process. This reproduced across four independent attempts: under `-n auto`
twice (different workers, different points in the run), and under `-n 0`
(fully sequential) once, ruling out xdist concurrency as the sole cause.
Stack samples in every case showed the same shape: one thread blocked in
`_pthread_cond_wait`/`__psynch_cvwait` (a mutex/semaphore wait) while a
second thread was blocked in a `read()` syscall on a subprocess pipe with no
writer -- consistent with a known class of macOS-specific Python
`subprocess`-after-`fork()` fragility in processes carrying substantial
imported-module/thread state (which a large pytest collection run
accumulates), unrelated to xdist parallelism specifically.

This is a pre-existing, already-documented condition (project memory notes
an "open perf issue in test_phase85/87_integration.py" predating this
phase) now further characterized: it is not merely slow, it can manifest as
an outright indefinite stall on this host, in both parallel and sequential
execution modes. It is **not caused by, or related to, this phase's work or
113S/113T/113U's validator**: `git diff --stat` (§1 above) already confirms
zero `src/` changes beyond the validator module across the entire
113S→113U→113V range, and `pcae project-state --json` shares no code path
with `repository_transition_validator.py`. Confirmed independently: running
`pcae artifact-index`, `memory-snapshot`, `governance-timeline`,
`decision-log`, and `risk-register` individually (the other 5 of
`test_phase85_integration.py`'s 6 commands) all complete normally in a few
seconds each; only `project-state` reproduces the stall.

This is recorded as a repair candidate for a future phase (not this one,
which is verification-only): either mark `test_phase85_integration.py`/
`test_phase87_integration.py` to run in a fresh subprocess-per-test
isolation mode, add `pytest-timeout` to bound any single test, or
investigate `project-state`'s own subprocess-spawning implementation for
the specific fork pattern that triggers this contention.

## No New Tests Required

No gaps were found in 113U's existing 36-test suite during this
verification — every objective in this phase's brief was independently
re-confirmable using the existing test suite plus direct interactive
re-verification (§1–§7 above). No new test file was added.

## No-Go Confirmation

No lifecycle integration added. No Telegram dispatch repair added. No
enforcement implemented. No Advisory Runtime, Runtime Snapshot, Runtime
Context, Runtime Registry, or Permission Broker changes. No change to
any existing lifecycle enforcement path. Execution capability remains
unavailable.

## Recommended Next Phase

113W — Repository Transition Validator Integration Design.
