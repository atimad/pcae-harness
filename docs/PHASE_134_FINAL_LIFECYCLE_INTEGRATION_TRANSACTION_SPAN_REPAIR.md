# Phase 134E.10.1 — Final Lifecycle Integration Transaction-Span Repair

## 1. Executive Summary

Repairs the central BLOCKING finding 134E.10V independently established:
`src/pcae/core/finalization_transaction.py` was a post-success observer,
invoked strictly *after* certification, promotion, and physical dispatch
had already completed via the entirely unmodified legacy path, with no
ability to prevent, reject, or accurately classify a failure in any of the
seven newly-integrated modules. The repair inverts control:
`run_finalization_transaction()` now accepts a `promote_and_dispatch`
callback and invokes it **only if** the seven modules' mandatory
pre-promotion stages (evidence capture, extraction, view composition,
rendering) succeed first. A pre-promotion failure means the callback —
which wraps the existing, entirely unmodified `finalize_phase_report`/
`write_phase_report`/`dispatch` machinery — is never invoked at all: no
promotion, no dispatch, no marker, no receipt. All four production entry
points (`phase.py`, `task.py`, `phase_reports.py`, `notifications.py`)
were rewired accordingly; `push.py` needed no separate change (it funnels
through `phase.py`). Full-suite regression is an exact match to the
established clean baseline (182 pre-existing failures, zero new, zero
pollution); `fast_green` remains deterministic at 4391/4391 across three
runs.

## 2. Repair Methodology

"Re-derive, then repair the smallest correct thing." 134D's own text for
134E.10 (re-read directly from `docs/PHASE_134_CANONICAL_PHASE_
FINALIZATION_IMPLEMENTATION_PLAN.md` §3, quoted in full in `docs/
PHASE_134_FINAL_LIFECYCLE_INTEGRATION_INDEPENDENT_VERIFICATION.md` §3) was
re-confirmed unchanged before writing any code. 134E.10V's own finding —
that the transaction ran after, not before, certification/promotion/
dispatch — was independently reproduced again at the start of this phase
(same line-number trace: `finalize_phase_report()` calls preceded
`run_finalization_transaction()` calls in every entry point) before being
treated as the repair target, per this track's own discipline of never
trusting a predecessor phase's claim without re-derivation.

## 3. Requirement-to-Code Map (Before Repair)

| Required lifecycle stage (134D / corrective brief's 21-stage list) | Pre-repair location | Pre-repair authority | Pre-repair ordering | Repair required |
|---|---|---|---|---|
| 1-2. Identity/config resolution | Each entry point, independently | Entry point | Before certification (unchanged) | No |
| 3. Repository/governance observation | `_apply_canonical_and_trust`/`validate_finalization_gate` | Existing, unmodified | Before certification (unchanged) | No |
| 4-8. Evidence/extraction/views | `finalization_transaction.py` | New module | **After** promotion+dispatch | **Yes** |
| 9. Architecture Status | `build_architecture_status()`, called before certification | Existing, unmodified | Before certification (unchanged) | No |
| 10. Consistency/derived correctness | `validate_derived_correctness`/`validate_internal_report_coherence` | Existing, unmodified, 134E.9V-hardened | Before certification (unchanged) | No |
| 11-13. Snapshot/rendering/digest | `finalization_transaction.py` | New module | **After** promotion+dispatch | **Yes** |
| 14-15. Promotion readiness/promotion | `finalize_phase_report`/`write_phase_report` | Existing, unmodified | **Before** the new pipeline ran at all | **Yes** (ordering relative to new pipeline) |
| 16-18. Delivery purpose/prepare/dispatch | Existing `dispatch()` path | Existing, unmodified | **Before** the new pipeline ran at all | **Yes** (ordering relative to new pipeline) |
| 19. Receipt persistence | `finalization_transaction.py` | New module | After dispatch (correct — receipts are inherently post-hoc) | No (already correctly ordered) |
| 20. Logical-completion marker | `write_notification_dispatch_marker` | Existing, unmodified | Inside promotion+dispatch, before the new pipeline ran | No (correct authority; ordering relative to the new pipeline is now also correct since promotion+dispatch is now the thing the transaction gates) |
| 21. Final lifecycle result | Each entry point's own return value | Entry point | Independent of the new pipeline's outcome | **Yes** |

The repair required was precisely stages 4-8/11-18/21: move the seven
modules' mandatory stages *before* promotion+dispatch, and make the entry
point's final result depend on the transaction's outcome, not merely on
whether the legacy path happened to succeed.

## 4. Control-Inversion Design

`run_finalization_transaction(*, phase_id, phase_name, report, gate,
promote_and_dispatch, transaction_root=None, receipt_root=None)`.
`promote_and_dispatch: Callable[[], dict]` is a zero-argument callback the
caller supplies, wrapping the caller's own existing, entirely unmodified
promotion/dispatch logic — this is 134D's own explicit permission ("wrap
it behind the transaction; treat it as an adapter") applied literally, not
a reimplementation of `finalize_phase_report`/`write_phase_report`/
`dispatch`.

Sequence, per call:

1. Resume check: if a prior transaction for identical certified content
   (`report_digest` + `finalization_snapshot_id`) already completed,
   short-circuit — **the callback is not invoked** (Section 8).
2. Gate check: if the caller-supplied gate is not finalizable, or the
   trial report's own `report_completeness != "complete"`, return
   `"gate_not_passed"` — **the callback is not invoked**, exactly as
   before this repair.
3. **Mandatory pre-promotion stages** (`_build_pre_promotion_artifacts`):
   evidence capture, extraction (both profiles), view composition (both
   views), rendering (both formats). Any exception here is caught, the
   transaction returns `"pre_promotion_certification_failed"`, and **the
   callback is never called**.
4. Only if step 3 fully succeeds: `promotion_result = promote_and_dispatch()`.
   An exception, or a returned dict with `blocked`/`report_error` truthy,
   yields `"promotion_and_dispatch_failed"` and stops the transaction
   there (no further steps run).
5. Post-dispatch receipt modeling (best-effort, non-fatal — Section 6):
   reads `promotion_result["report"].notification_result` (the *real*,
   now-promoted report's real dispatch outcome, not the pre-promotion
   trial report's), gated on the 134E.10V receipt-honesty repair
   (`success: True` required, otherwise skip with an explicit limitation)
   — unchanged from 134E.10V.
6. Return a `TransactionResult` whose `promotion_and_dispatch` field
   carries the callback's own return value, so the entry point can
   continue using it exactly as it used the direct `finalize_phase_
   report()` return value before this repair.

## 5. Entry-Point Convergence Result

All four production entry points now build a local `_promote_and_dispatch`
closure wrapping their own existing promotion/dispatch logic, verbatim
(no behavior change inside the closures beyond what `_dispatch_manual_
report_notification`/raw `dispatch()` calls in `phase_reports.py`/
`notifications.py` needed — see below), and route it through
`run_finalization_transaction`:

- **`phase.py`** (`run_phase_complete`): `_promote_and_dispatch()` wraps
  the existing `finalize_phase_report(...)` call (including its
  `PCAE_NOTIFY_ENABLED` suppression `finally` block, unchanged). Invoked
  through the transaction only when the trial gate passed **and**
  `--allow-partial-report` was not used — that explicit human override
  keeps its exact pre-existing unconditional-proceed behavior (calling
  `_promote_and_dispatch()` directly, bypassing the new gating), since the
  override's entire purpose is to proceed despite blockers; making the new
  pipeline's mandatory stages a second, unbypassable gate on top of an
  explicit human override would itself be a regression.
- **`task.py`** (`_finalize_task_report_and_notify`): `_promote_and_
  dispatch()` wraps the existing `finalize_phase_report(...)` call. Routed
  through the transaction when the trial gate passed; on
  `pre_promotion_certification_failed`/`promotion_and_dispatch_failed`,
  returns a structured failure dict instead of the prior success shape —
  callers already handle non-`"finalized"` status dicts.
- **`phase_reports.py`** (`run_phase_report_create`): `_promote_and_
  dispatch()` wraps `write_phase_report(...)` followed by `_dispatch_
  manual_report_notification(...)`, and (new, since this function never
  set it before) populates `report.notification_result` from the
  dispatch outcome so the transaction's receipt-honesty gate has real data
  to read.
- **`notifications.py`** (`run_notify_send_report`): this entry point has
  no promotion step (the report was already promoted by a prior entry
  point's run) — only dispatch. `_promote_and_dispatch()` wraps the
  existing `dispatch(event, [sink])` call and marker write, and likewise
  now populates `report.notification_result` (previously never set on
  this path either).
- **`push.py`**: unchanged — `_reconcile_post_push()` still calls `phase.
  py`'s `_finalize_report_and_notify`, which now itself routes through the
  repaired transaction; no separate change was needed or made.

Source-scan tests (`TestSharedBoundary::
test_entry_point_supplies_promote_and_dispatch_callback`) confirm all four
command files contain `promote_and_dispatch=_promote_and_dispatch`,
proving the wiring is real, not merely present in one file.

## 6. Pre-Promotion vs. Post-Promotion Failure Propagation

| Stage | Failure behavior | Canonical artifacts changed? | External delivery? | Marker? | Receipt? | Retry eligible? |
|---|---|---|---|---|---|---|
| Identity/gate check | Callback never invoked; `"gate_not_passed"` | No | No | No | No | Yes |
| Evidence capture (mandatory, pre-promotion) | Callback never invoked; `"pre_promotion_certification_failed"` | **No** | **No** | **No** | No | Yes |
| Extraction/composition/rendering (mandatory, pre-promotion) | Same as above | **No** | **No** | **No** | No | Yes |
| `promote_and_dispatch` callback itself raises | `"promotion_and_dispatch_failed"`; no further steps | Depends on how far the legacy function got before raising (unchanged from pre-repair legacy behavior — the legacy function's own internal fail-closed guarantees, e.g. quarantine-not-latest on a blocked gate, are untouched) | Depends on the same | Depends on the same | No | Yes, per the legacy function's own existing recovery paths (unchanged) |
| `promote_and_dispatch` returns `blocked`/`report_error` | `"promotion_and_dispatch_failed"` | No (legacy function's own quarantine behavior, unmodified) | No | No | No | Yes |
| Post-dispatch receipt modeling (best-effort) | `"completed_receipt_best_effort_incomplete"`; promotion/dispatch **already irreversibly succeeded** above | **Yes, correctly** (promotion already happened) | **Yes, correctly** (dispatch already happened) | **Yes, correctly** (marker already written by the callback) | No (explicit limitation recorded) | N/A — nothing to retry, the logical completion already exists |

The critical new property (Section 1's repair target): every row above
the post-dispatch-receipt row now correctly shows **no promotion, no
delivery, no marker** on failure — this was previously impossible to
express, since the legacy path ran unconditionally before the new
pipeline was ever reached.

## 7. Pre-Commit and Post-Commit Boundaries

The authoritative, irreversible commit point remains exactly where it
already was: inside `promote_and_dispatch()`'s own legacy machinery
(`finalize_phase_report`'s write of `latest.md`/`latest.json`, and
`dispatch()`'s real send). This repair does not — and, per Section 10's
honest scope disclosure, does not attempt to — introduce filesystem or
transport-level atomicity beyond what those existing functions already
provide (no two-phase commit, no rollback of a partially-written
`latest.json`; that remains exactly as reliable, and exactly as limited,
as it was before this phase). What changed is *what is allowed to run
before* that commit point: previously, nothing (the legacy path ran
unconditionally); now, the seven modules' mandatory stages, with genuine
veto power. Everything before `promote_and_dispatch()` is called is fully
reversible (nothing has been written or sent); everything after it
returns is irreversible, exactly as before this repair.

## 8. Resumability, Strengthened

134E.10's original resumability only prevented the new pipeline's own
post-hoc steps from re-running — the legacy path itself was never gated by
the checkpoint at all (each CLI invocation independently called `finalize_
phase_report` regardless of any transaction checkpoint state, relying
solely on the pre-existing `.last-notified.json` marker for dispatch
dedup). After this repair, a resumed transaction (`existing.status ==
"completed"` for identical `report_digest`/`finalization_snapshot_id`)
returns immediately via `_result_from_checkpoint()` **without invoking
`promote_and_dispatch` at all** — meaning a retry can structurally never
re-promote or re-dispatch for content already known to be finalized, a
strictly stronger guarantee than existed before. Proven by `TestResumability::
test_second_call_for_same_certified_content_does_not_reinvoke_callback`
(the second call's callback is `_never_call_promote_and_dispatch`, which
raises `AssertionError` if invoked — it is not) and the same test's
digest/snapshot/extraction/view/rendering-digest equality assertions
across the two calls.

## 9. Receipt Honesty (Preserved, Unchanged)

134E.10V's receipt-honesty repair (delivery modeling and receipt creation
gated on the *real*, promoted report's `notification_result["success"]`)
is preserved exactly, with one necessary adjustment: it now reads
`promotion_result["report"].notification_result` (the report object
`promote_and_dispatch()` actually returns) rather than the pre-promotion
trial `report` parameter — because promotion now genuinely happens inside
this function, the "real" report with a populated `notification_result` is
only available after the callback returns. `phase_reports.py`'s and
`notifications.py`'s entry points, which never set `report.notification_
result` before this phase (confirmed via `grep`, zero prior matches),
now do so explicitly inside their own `_promote_and_dispatch` closures, so
the receipt gate has real data on every entry point, not just `phase.py`/
`task.py`.

## 10. Honest Scope Disclosure: What This Repair Does *Not* Wrap

134D's abstract phrase for 134E.10 is "a single, explicitly resumable
transaction spanning commit → push → certification → promotion → delivery
→ completion." This repair's corrective brief itself provides a concrete,
minimum 21-stage sequence (`docs/PHASE_134_FINAL_LIFECYCLE_INTEGRATION_
TRANSACTION_SPAN_REPAIR` task prompt, "Required transaction architecture")
that **begins at "resolve canonical phase identity"** and ends at "return
the final lifecycle result" — it does not list a raw `git commit`/`git
push` stage. This repair adopts the concrete list as authoritative for
what "spans commit → push" means in practice: this codebase's own governed
lifecycle already treats `pcae commit`/`pcae push` as prior, separate,
human/CLI-driven governed actions that happen *before* `pcae phase
complete`/`task finish` are ever invoked (per the established 17-step
lifecycle pattern) — not as steps inside a single finalization function
call. This repair's transaction spans identity resolution through final
result for **one finalization attempt**; it does not reach backward to
wrap the git commit/push commands themselves. This is a disclosed
interpretation choice, not a silent narrowing — flagged explicitly here
exactly as 134E.10's own scope decisions were flagged in its own report,
per this track's established disclosure discipline. If a future phase
determines this interpretation was too narrow, that determination belongs
to 134E.10.1V's own independent re-derivation, not to this phase's own
self-assessment.

## 11. Focus Tests

`tests/test_finalization_transaction_134e10.py` rewritten in full for the
callback-based API (37 tests, all passing): end-to-end happy path with
callback-invocation proof; the 134E.10V receipt-honesty case; rendering
divergence disclosure; **five parametrized mandatory-stage-failure tests**
(`TestPrePromotionGatingIsAuthoritative`, one per stage: evidence capture,
extraction, phase report view, operator report view, rendering) each
proving the callback is never invoked; callback-exception and
callback-blocked-result handling; explicit marker-non-persistence proof on
pre-promotion failure; explicit receipt-after-callback ordering proof;
gate enforcement (both caller-supplied and defense-in-depth); strengthened
resumability (Section 8); storage-identifier path-traversal rejection;
shared-boundary source-scan tests (now including the new `promote_and_
dispatch=_promote_and_dispatch` wiring check); external-delivery
isolation.

## 12. Regression Tests

- Broader affected regression (`test_phase_reports.py`, `test_task_finish_
  report_trust_notification.py`, `test_notification_certification_
  idempotency.py`, `test_post_push_canonicalization.py`, `test_report_
  consistency_derived_correctness_134e9.py`): 257 passed, 1 pre-existing
  unrelated failure (`TestPhase126G1CommitTrustMetadataRepair::
  test_report_completeness_reaches_complete_via_cli_alone`, unchanged).
- Seven-subsystem module suite + verification siblings + transaction
  suite: 931/932 (1 pre-existing, previously-isolated unrelated failure,
  unchanged).
- Full-suite regression: 19,359 passed, 182 failed — exact node-ID match
  to the established clean baseline, zero new failures, zero pollution
  (`git status --short .pcae/` clean before and after every run in this
  phase).
- `fast_green`: 4391 passed, 0 failed across three consecutive runs
  (parallel twice, serial once), identical selected-test count throughout.
- `compileall`: clean.

## 13. Governance Results

- `pcae check`, `pcae health`, `pcae doctor task-memory`, `pcae push
  check`: all clean/healthy/passed throughout this phase.
- Governed commit/push/task/phase commands only; no raw `git commit`, no
  raw `git push`, no `--no-verify`, no force push.
- Runtime remained Observed/observe/unavailable throughout — this phase
  touched zero runtime/execution code.

## 14. Findings Summary

| # | Finding | Classification |
|---|---|---|
| 1 | `finalization_transaction.py` ran strictly after certification/promotion/dispatch, unable to gate them | **BLOCKING — repaired via control inversion (Sections 4-6)** |
| 2 | Receipt honesty (gated on real dispatch outcome) | **CONFIRMED preserved, adapted to read from the promoted report** |
| 3 | Resumability now structurally prevents re-promotion/re-dispatch on retry | **CONFIRMED, strengthened** |
| 4 | This repair does not wrap raw `pcae commit`/`pcae push` | **Disclosed scope interpretation, not a defect** (Section 10) |
| 5 | Full-suite/fast_green regression | **CONFIRMED**, exact baseline match, zero new failures |
| 6 | Historical artifacts (134E.8 through 134E.10V reports, snapshots, digests, markers, receipts) | **CONFIRMED unmodified** — this phase touched zero files under `docs/PHASE_134_*` other than adding this new document, zero files under `tasks/done/` other than adding this phase's own task contracts |

## 15. No-Go Confirmations

No 134F work began. No new execution capability was introduced. No new
communication channel was introduced. No Repository Intelligence
authority expansion, Decision Evaluation change, PFN-001 change, or
PFR-001 change occurred. No raw git commit/push, `--no-verify`, or force
push was used. No external test delivery occurred — every new/updated
test in this phase constructs synthetic, in-memory `promote_and_dispatch`
closures with zero real I/O, isolated `tmp_path` transaction/receipt
roots, and the autouse `_isolate_external_notifications` fixture applies
regardless. No historical report was rewritten or deleted. No second
ordinary completion was created for any already-completed phase.

## 16. Recommended Next Phase

**134E.10.1V — Final Lifecycle Integration Transaction-Span Repair
Independent Verification** (matching this track's established
dotted-corrective-then-`V` convention — e.g. 134E.9 → 134E.9.1 →
134E.9V). 134E.10.1V has not begun. 134F has not begun.
