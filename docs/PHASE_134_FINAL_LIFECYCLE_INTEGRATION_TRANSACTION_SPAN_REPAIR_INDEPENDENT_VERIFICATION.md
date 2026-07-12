# Phase 134E.10.1V — Final Lifecycle Integration Transaction-Span Repair Independent Verification

## 1. Executive Summary

Independently verified both 134E.10.1's transaction-span control-inversion
repair and 134E.10.1.1's commit-attribution repair via re-derivation from
134D and direct reproduction against real source and git history — not
trust in either phase's own report, comments, function names, or the
tests written during those implementation phases. **Verdict: both
repairs hold.** Control inversion genuinely gates promotion and dispatch
behind the seven integrated modules' mandatory pre-promotion stages;
commit attribution is now explicit and provenance-bound with a working
cross-phase rejection mechanism. One genuine, real gap was found and is
disclosed as **NON-BLOCKING**: `detect_cross_phase_commit_contamination()`
silently skips commit hashes that don't resolve to real commits (by
deliberate design, to remain permissive for this codebase's own
extensive hermetic-test convention using synthetic hashes) — meaning a
fabricated hash in an explicitly-declared `phase_commits` list currently
passes unchallenged. This is real but bounded: it does not let a
*genuine* prior-phase commit through (the actual defect this track
exists to prevent), and closing it robustly would require a design
change this phase judged out of proportion to repair as a corrective
verification action. Zero BLOCKING findings. Full-suite regression is an
exact node-ID match to the established clean baseline; `fast_green`
remains deterministic at 4391/4391 across three runs.

## 2. Verification Methodology

"Re-derive. Do not trust." Applied specifically to distrust: 134E.10.1's
own claim that "a shared callback automatically creates an authoritative
transaction" (re-traced via fresh `grep` across all four command files,
not accepted from the phase's own report prose); 134E.10.1.1's own claim
that commit-subject text is safe evidence (independently re-derived the
exact invariant — subject text may only *reject*, never *prove*
ownership — and checked the source against it); and the 37/12/18 tests
written during the two implementation phases (re-run as corroborating
evidence, never as a substitute for direct reproduction — every
significant claim in this report was independently reproduced via a
fresh Python REPL invocation or `git log`, not merely re-read from an
existing test's assertion).

## 3. Re-Derived 134D Transaction-Span Requirement Matrix

| Stage | Authoritative input | Authoritative output | Responsible component | Required ordering | Reversible? | Failure behavior |
|---|---|---|---|---|---|---|
| Identity/config resolution | CLI args, `.pcae/phase-completion-metadata.json` | `phase_id`, `phase_name` | Entry point | Before all else | Reversible | Entry point returns early |
| Repository/governance observation | `build_architecture_status()`, gate inputs | `trial_report`, `gate` | Existing, unmodified `_apply_canonical_and_trust`/`validate_finalization_gate` | Before pre-promotion stages | Reversible | `gate_not_passed`, callback never invoked |
| CEE/extraction/views/rendering | Certified `trial_report` | Evidence/extraction/view/render digests | `finalization_transaction.py` (new) | After gate passes, before promotion | Reversible | `pre_promotion_certification_failed`, callback never invoked |
| Promotion + dispatch | `promote_and_dispatch()` callback | Written `latest.md`/`latest.json`, real dispatch attempt | Existing, unmodified `finalize_phase_report`/`write_phase_report`/`dispatch`, invoked *by* the transaction | Only after pre-promotion succeeds | **Irreversible** | `promotion_and_dispatch_failed` |
| Receipt modeling | Real `notification_result` from the promoted report | Receipt (if real dispatch succeeded) | `finalization_transaction.py` (new), post-dispatch | After promotion+dispatch return | Reversible (best-effort) | `completed_receipt_best_effort_incomplete`, promotion/dispatch unaffected |
| Logical marker | `all_ok` from real dispatch results | `.last-notified.json` entry | Existing, unmodified, inside the callback | Inside promotion+dispatch, before receipt modeling | **Irreversible** | Not written on dispatch failure |

Independently re-confirmed against actual source (Section 4), not
accepted from 134E.10.1's own 21-stage framing.

## 4. Actual Runtime Ordering — Fresh Trace

Re-traced via `grep -n` across all four command files (line numbers
current as of this verification, not re-cited from 134E.10.1's own
report):

- **`phase.py`**: `_promote_and_dispatch()` closure defined (wraps
  `finalize_phase_report`) → `if gate.get("finalizable") and not
  allow_partial_report:` → `run_finalization_transaction(...,
  promote_and_dispatch=_promote_and_dispatch)` → else direct call
  (Section 6).
- **`task.py`**: identical shape — closure defined, `if gate.get
  ("finalizable"):` gates transaction entry, else direct call.
- **`phase_reports.py`**: `_gate = validate_finalization_gate(...)`
  computed *before* the closure; `_promote_and_dispatch()` wraps
  `write_phase_report` + `_dispatch_manual_report_notification`, setting
  `report.notification_result` explicitly (this entry point never set it
  before this session's own repairs); `if _gate.get("finalizable"):`
  gates transaction entry.
- **`notifications.py`**: `_promote_and_dispatch()` wraps `dispatch()` +
  `write_notification_dispatch_marker`; the transaction is entered
  unconditionally here because `gate["finalizable"]` was already checked
  earlier in the function with an explicit `return 1` — re-confirmed
  directly, not assumed.
- **`push.py`**: `_reconcile_post_push()` still calls `phase.py`'s
  `_finalize_report_and_notify` — transitively inherits the repaired
  ordering with zero code of its own to re-verify.

**Confirmed: in every path where the trial gate genuinely passes and no
explicit human override is used, pre-promotion certification now runs
strictly *before* promotion, dispatch, and marker persistence** — the
central property 134E.10V found missing and 134E.10.1 was built to fix.

## 5. Callback Inversion — Independently Challenged

Per the brief's own instruction that the callback's mere existence is
not sufficient proof: five direct, fresh reproductions (not re-runs of
existing tests, though the existing 37-test suite corroborates each):

```python
# 1. Callback invoked only after ALL mandatory pre-promotion stages pass
with mock.patch("pcae.core.finalization_transaction._capture_evidence",
                 side_effect=RuntimeError):
    result = run_finalization_transaction(..., promote_and_dispatch=cb)
# -> status == "pre_promotion_certification_failed"; cb never called (verified via a callback that raises AssertionError if invoked)
```

```python
# 2. Callback failure causes overall transaction failure
result = run_finalization_transaction(..., promote_and_dispatch=raising_cb)
# -> status == "promotion_and_dispatch_failed"
```

```python
# 3. A resumed transaction for identical content does NOT reinvoke the callback
first = run_finalization_transaction(...)   # completed
second = run_finalization_transaction(..., promote_and_dispatch=never_call_cb)
# -> status == "resumed_completed"; never_call_cb (raises if invoked) never fires
```

No marker exists before callback completion (the marker write lives
*inside* the callback, in the legacy `finalize_phase_report`/`dispatch`
code the callback wraps — confirmed by direct source read: the marker
write statement is textually inside the closure body in all four command
files). No receipt exists before real dispatch evidence (Section 8).
Every entry point's own return/exit path was re-checked to confirm it
derives from `txn_result.status`, not merely from whether the legacy
call "ran": `phase.py` and `task.py` both explicitly `return False`/a
structured failure dict on `pre_promotion_certification_failed` or
`promotion_and_dispatch_failed`, never silently proceeding to print
"success."

## 6. No Competing Legacy Authority

`grep -n` for every call to `finalize_phase_report`, `write_phase_report`,
`dispatch(`, `write_notification_dispatch_marker` across all five entry
points confirms exactly one call site each, always inside a
`_promote_and_dispatch` closure. The only place `_promote_and_dispatch()`
is invoked *directly* (not via the transaction) is the `else` branch of
`if gate.get("finalizable") and not allow_partial_report:` — covering
two cases: (a) the pre-existing, explicit `--allow-partial-report` human
override, which must keep its exact pre-existing unconditional-proceed
behavior (not a bypass — an intentional, disclosed, unchanged escape
hatch); (b) the trial gate already failed for unrelated reasons (e.g. a
95M.1/105A schema blocker) — in this case `finalize_phase_report`'s own
internal, unmodified gate-enforcement (113X.1's quarantine finding)
already prevents promotion regardless of whether the new pipeline ran.
Neither case allows promotion/dispatch to succeed when it shouldn't;
neither is a "second completion authority." **CONFIRMED, not BLOCKING.**

The `.pcae/skills/phase-finalization/SKILL.md` file was independently
inspected in full: it is pure prompt/instruction text ("no subprocess
execution" stated explicitly in its own body) that guides an operator to
run the same governed CLI commands already traced above — not an
independent code path.

## 7. Seven-Subsystem Authority Classification (Re-Derived)

| Module | 134E.10V's classification | 134E.10.1V's re-derived classification |
|---|---|---|
| Canonical Engineering Evidence | Compatibility projection | **Required validating participant** — its own construction failure now genuinely blocks promotion (Section 5, test 1). Still not "authoritative" over report *content* (it doesn't determine what the certified report says — Section 8) but now authoritative over whether finalization *proceeds at all*. |
| Evidence Extraction | Compatibility projection | Required validating participant, same reasoning — extraction failure is one of the five parametrized mandatory-stage-failure cases directly re-confirmed passing. |
| Phase Report View | Post-success comparison artifact | Required validating participant — composition failure blocks promotion identically. |
| Operator Report View | Post-success comparison artifact | Required validating participant, same. |
| Rendering | Comparison-copy renderer | Required validating participant for *whether finalization proceeds*; still a **comparison-copy renderer for content** — canonical stored/delivered bytes are unchanged, still produced by the legacy `PhaseReport.render_markdown()`/notification renderer (Section 8). |
| Delivery Pipeline | Shadow/receipt-projection pipeline | **Unchanged — still a shadow/receipt-projection pipeline.** The real dispatch remains `pcae.core.notifications.dispatch()`, called from inside the legacy-wrapping callback, never through `delivery_pipeline.py`'s own adapters. |
| Delivery Receipt | Receipt-projection, honesty-gated | Unchanged classification, now additionally gated on the real, post-promotion report's dispatch outcome (already true since 134E.10V's own repair). |

**Important distinction, independently derived, not assumed:** none of
the seven modules gained authority over report *content* or the *actual
dispatch mechanism* — that distinction from 134E.10V's own finding still
holds. What changed is narrower but real: five of the seven (CEE,
extraction, both views, rendering) gained authority over **whether
finalization is allowed to proceed at all** — a failure in any of them
now structurally prevents the irreversible legacy machinery from ever
running. This is 134D's actual completion criterion ("no irreversible
success may occur outside the authoritative transaction in a way that a
later required stage cannot prevent") and is satisfied. It is a
materially different and stronger claim than 134E.10V found true, and it
does not claim more than is actually true (the two never-authoritative
subsystems, Delivery Pipeline and Delivery Receipt, are honestly
described as such).

## 8. Rendering and Canonical Bytes — Re-Confirmed

Direct source read (not re-cited): canonical stored report bytes are
produced by `PhaseReport.render_markdown()`, called inside
`finalize_phase_report`/`write_phase_report`, unchanged by either
134E.10.1 or 134E.10.1.1. Terminal/Telegram bytes are produced by the
existing `TelegramSink`/`phase_report_to_notification_event`, likewise
unchanged. The new renderer (`_rendering.render(...)`, called inside the
transaction's pre-promotion stage) produces an independent, disclosed-
as-possibly-divergent comparison copy — re-confirmed via a fresh
`test_unresolved_rendering_divergence_is_disclosed_not_hidden` run: the
divergence is recorded as a limitation, never silently reconciled, and
never blocks promotion by itself (matching 134A's own invariant against
silent strengthening — a rendering *disagreement* is disclosed evidence,
not corrected evidence). 134D permits the legacy renderer as an adapter
per its own "wrap it behind the transaction" language; disagreement is
handled by disclosure, consistent with that permission.

## 9. Promotion and Physical Dispatch — Re-Confirmed

Promotion occurs exclusively inside `promote_and_dispatch()`, consuming
the same `trial_report`/certified content the pre-promotion stages
already validated — no second, different report object is constructed
for promotion (the entry-point-specific duplicate-object-construction
quirk disclosed in 134E.10.1's own report, itself pre-existing and
unrelated to the control-inversion repair, is unchanged and re-confirmed
unaffected). Exactly one physical dispatch decision per logical
completion — re-confirmed via the existing `.last-notified.json` marker
mechanism (unmodified) and via this session's own live governed
completions of 134E.10.1 and 134E.10.1.1, both of which showed exactly
one dispatch (`already dispatched (idempotent)` on the follow-up
`pcae notify send-report --latest` check in both cases — direct
production evidence, not test-only). PFN-001 unchanged; automatic
Telegram configuration resolution unchanged (confirmed via `pcae notify
status` showing the same "Notify enabled: True" auto-hook behavior as in
every prior phase this session).

## 10. Receipt Honesty — Re-Verified Post-Adaptation

Re-confirmed the 134E.10V repair survived the callback-based
restructuring correctly: `finalization_transaction.py`'s post-dispatch
step reads `promotion_result["report"].notification_result` — the *real*
promoted report's real outcome, not the pre-promotion trial report's
(which never has a populated `notification_result` at all, since
dispatch hasn't happened yet when the trial report is built). Direct
re-derivation of what each receipt field is actually evidenced by:

- **Callback invocation**: proven (the receipt step is unreachable
  otherwise).
- **Real adapter invocation**: NOT proven by the receipt itself — the
  receipt's own "delivery" step uses the in-memory recording adapter,
  never the real `TelegramSink`. What IS proven is that
  `report.notification_result["success"]` was `True`, i.e. the real,
  separate dispatch (via `dispatch()`, inside the same callback, before
  the receipt step runs) self-reported success.
- **Remote API acceptance**: not evidenced beyond the sink's own
  self-reported HTTP success — unchanged limitation from every prior
  phase in this track.
- **Remote message identifier**: not captured anywhere in this codebase
  — unchanged.
- **End-user receipt**: never claimed.

No receipt in this codebase claims generalized-adapter execution when
only the legacy compatibility path ran — confirmed by direct source
read: the receipt is built from the recording adapter's own
`DeliveryExecutionResult`, and nothing in `delivery_receipt.py` or
`finalization_transaction.py` asserts it represents a `TelegramSink`
invocation.

## 11. Logical Marker Ordering — Failure-Case Re-Verification

Re-confirmed via direct reproduction and the existing test suite: the
marker write (inside `finalize_phase_report`'s own `all_ok` check,
unmodified) happens strictly before the transaction's own receipt step
even begins (receipt step runs only after `promote_and_dispatch()`
*returns*, and the marker is written inside that same call, before
return). Cases directly reasoned through against actual code:

| Case | Marker written? | Receipt written? | Canonical state |
|---|---|---|---|
| Promotion succeeds, dispatch fails | No (marker gated on `all_ok`) | No (`notification_result["success"]` False) | Promoted, not dispatched, not marked |
| Dispatch succeeds, receipt creation fails | Yes (marker precedes receipt step) | No (`completed_receipt_best_effort_incomplete`) | Promoted, dispatched, marked, receipt absent — accurately represented, never silently upgraded |
| Dispatch succeeds, receipt persistence fails (disk error) | Yes | No | Same as above |
| Receipt succeeds, marker somehow fails (would require a bug inside `finalize_phase_report` itself, out of this phase's scope) | N/A — marker precedes receipt in the actual call order, so this ordering cannot occur as stated | — | Not a reachable state given current ordering |
| Marker already exists for identical content | Transaction resumes (`resumed_completed`), callback not re-invoked | Unchanged from prior run | No duplicate marker write |
| Bookkeeping commit changes, phase/digest unchanged | Same resume behavior (digest is content-derived, not commit-derived) | Unchanged | No duplicate |

## 12. Failure-Propagation Matrix (Re-Confirmed via the 5 Parametrized Tests)

Re-ran and independently inspected `TestPrePromotionGatingIsAuthoritative`'s
five parametrized tests (evidence, extraction, phase report view,
operator report view, rendering): each independently proves, for its own
stage, that the callback (checked via an `AssertionError`-raising
sentinel, not a mere call counter) is never invoked, `promotion_and_
dispatch` is `None`, and the limitation string explicitly states
"promote_and_dispatch was NOT invoked." All five pass. Post-promotion
failure modes (`promote_and_dispatch` raises; returns `blocked`/`report_
error`) independently re-run and confirmed to produce
`"promotion_and_dispatch_failed"` with no receipt.

## 13. Retry and Resumability — Challenged

Direct reproduction beyond the existing test suite's own cases:
- Same phase, same snapshot, same digest → resume, callback not
  re-invoked (re-confirmed).
- Same phase, different snapshot (different summary text) → distinct
  transaction record, own callback invocation, own receipt — re-confirmed
  via `TestResumability::test_distinct_certified_content_does_not_
  collide_with_prior_completion`, independently re-read (not merely
  re-run) to confirm the assertion actually checks callback-invocation
  count, not just digest inequality.
- Promotion succeeded but dispatch failed → no marker (Section 11) →
  `notification_result["success"]` False → no receipt → **a subsequent
  retry with the SAME trial content would still see the checkpoint as
  `"completed"` (since pre-promotion stages succeeded and the callback
  itself didn't raise) and would NOT re-invoke the callback** — this is
  the one genuinely subtle scenario re-derivation surfaced: a dispatch
  failure inside an otherwise-successful callback call does not, by
  itself, cause a future retry to re-attempt dispatch, because the
  transaction's own resumability is keyed on *content* digest, not on
  *dispatch outcome*. This matches the transaction's own documented
  contract (it never re-decides completeness or re-promotes) and is
  **not** a defect — dispatch failure recovery is, and remains, the
  responsibility of the existing, separate `.last-notified.json`-marker-
  driven retry path (`pcae notify send-report --latest`, which checks
  the marker independently and is unaffected by the transaction's own
  checkpoint) — confirmed this is exactly the mechanism this session's
  own governed completions relied on when push-time reconciliation
  dispatched before the explicit `pcae phase complete` call ran (Section
  9). **CONFIRMED, not BLOCKING** — but worth stating precisely rather
  than glossing over, since the brief explicitly asked this scenario be
  challenged.

## 14. Correction and Supersession

Neither 134E.10.1 nor 134E.10.1.1 (nor this verification phase) exercises
a `correction`/`supersession` delivery purpose in production — out of
134E.7's own frozen non-goals, unchanged. 134E.10.1.1 itself is this
track's own real-world instance of a "correction" in the informal sense
(a corrective report under its own dotted identity), independently
re-confirmed (Section 15) to use its own distinct logical-completion
marker entry, never reusing 134E.10.1's.

## 15. Authoritative Commit-Ownership Model, Re-Derived

| Hash | Date | Subject | Parent | Independently re-derived owner |
|---|---|---|---|---|
| `1844b05b` | 2026-07-12 02:51:05 | "Finish Phase 134E.10V test-evidence-key correction task" | `b48c6b9f` | **134E.10V** |
| `a17efc1b` | 2026-07-12 09:46:21 | "Phase 134E.10.1: Final Lifecycle Integration Transaction-Span Repair" | `1844b05b` | **134E.10.1** |
| `36266ac7` | 2026-07-12 09:46:26 | "Finish Phase 134E.10.1 task" | `a17efc1b` | **134E.10.1** |
| `3bde236b` | 2026-07-12 09:47:58 | "Sync Phase 134E.10.1 completion metadata" | `36266ac7` | **134E.10.1** |
| `441a2142` | 2026-07-12 09:47:59 | "Finish Phase 134E.10.1 metadata sync task" | `3bde236b` | **134E.10.1** |
| `6015f545` | 2026-07-12 10:37:31 | "Phase 134E.10.1.1: Phase-Owned Commit Attribution Repair" | `441a2142` | **134E.10.1.1** |
| `84f7811f` | 2026-07-12 10:37:36 | "Finish Phase 134E.10.1.1 task" | `6015f545` | **134E.10.1.1** |

Every value independently re-derived via fresh `git log -1 --format="%ai
/ %s / parent:%P" <hash>` calls in this phase, not copied from 134E.10.1.1's
own table. Exact agreement confirmed. `1844b05b` is unambiguously **not**
134E.10.1's, confirmed a fourth independent way (beyond subject,
timestamp gap, and parent-of-`a17efc1b` relationship already established):
the live, governed production report for 134E.10.1.1 itself shows
`Commits: 6015f545, 84f7811f` — direct proof the repair is live and
correctly excludes `1844b05b` from any current phase's own attribution.

## 16. Blind-Fallback Removal — Re-Confirmed

`grep -n "git log" src/pcae/commands/phase.py` returns zero matches for
any `--oneline`/`-N`-style recent-commit pattern; `def _gather_commits`
is confirmed absent (`grep -c` = 0). The sole fallback when `phase_commits`
is absent from metadata is `commits = []` with an explicit `"unresolved
(no phase_commits declared in metadata)"` attribution string — re-derived
by direct source read, not re-cited.

## 17. Subject-Detector Authority Assessment

Direct source read of every call site of `detect_cross_phase_commit_
contamination()` (two: `phase.py`, `task.py`) confirms the return value
is used *exclusively* to `append` to `gate["blockers"]` and set
`gate["finalizable"] = False` — there is no code path anywhere that reads
an *empty* result from this function and uses it to set `commit_
attribution`, mark completeness, or otherwise treat "no contradiction
found" as positive proof. **This satisfies the brief's critical
invariant exactly: commit-subject text is rejection-only evidence, never
ownership-establishing evidence. CONFIRMED, not BLOCKING.**

Grammar re-verified directly (Section 18) across: plain phase IDs,
V-suffixed, single-dotted, doubly-dotted, doubly-dotted-then-lettered,
lowercase (subject-side; case-normalized before comparison), commits with
no phase token (silently skipped, confirmed via a controlled regex
probe, not a live-history search), and unresolvable/synthetic hashes
(silently skipped, Section 19). Revert and merge commits were not found
in this repository's own history to test directly (this repo does not
appear to use `git revert`/merge commits in its governed workflow); the
function's own behavior for such a commit would be identical to any
other real commit — subject-parsed, compared, skipped if no phase token
matches. Not independently re-tested with a constructed revert/merge
commit given this repo's governance rules forbid introducing test
commits into real history; the function's logic makes no special case
for commit *type*, only subject *content*, so this is architecturally
covered without needing a dedicated fixture.

## 18. Doubly-Dotted Phase-ID Behavior — Re-Verified

Re-run directly against `134E.10`, `134E.10V`, `134E.10.1`, `134E.10.1V`,
`134E.10.1.1` across all three relevant parsers
(`_extract_canonical_title_phase_id`, the repaired `_leading_phase_id`,
`_COMMIT_SUBJECT_PHASE_TOKEN_RE`): all three now agree, all five forms
parse without truncation. One disclosed, non-exploitable asymmetry:
`_extract_canonical_title_phase_id` requires an uppercase letter
component (matching this codebase's own canonical-title convention,
never violated in practice since governed report titles are always
machine-generated in uppercase); the commit-subject regex has no such
restriction (case-normalized by the caller instead). **CONFIRMED,
NON-BLOCKING** (disclosed asymmetry, not exploitable given actual
production title-generation behavior).

## 19. Malformed/Unresolvable Commit Hash — Genuine Finding, NON-BLOCKING

**Reproduction:** `detect_cross_phase_commit_contamination(["deadbeef00"],
"999X.1-fake-hash-test")` returns `[]` — zero warnings — because
`git log -1 --format=%s deadbeef00` fails (`returncode != 0`) in the real
repository, and the function is deliberately designed to skip
unresolvable hashes rather than reject them (its own docstring states
this explicitly, to remain "permissive for hermetic test fixtures" —
this session's own test suites construct synthetic hashes like
`"abc12345"` throughout, e.g. `test_report_consistency_derived_
correctness_134e9.py`'s own `_report()` fixture).

**Consequence:** a phase whose `.pcae/phase-completion-metadata.json`
declares a *fabricated* `phase_commits` hash (never a real commit)
currently passes the cross-phase check silently — the structural
"commits must be non-empty" check (Section 5 of 134E.10.1.1's own
report, re-confirmed in this phase) is satisfied by any non-empty list
regardless of hash validity, and no other check in this codebase
verifies hash *resolvability*.

**Why NON-BLOCKING, not BLOCKING:** this does not reproduce or reopen
the actual defect this track exists to close (a *genuine* prior-phase
commit silently misattributed) — it is a narrower, adjacent gap
(a *fabricated* commit silently accepted). Closing it would require
either (a) making hash resolution mandatory everywhere, which would
break this session's own extensive hermetic-test convention across
dozens of pre-existing test files using synthetic hashes, or (b) a new
opt-in "verify hash resolution" mode distinguishing production from test
context — a real design addition, not a "smallest safe repair" available
to a verification phase. Disclosed here, not silently omitted, with a
recommended future follow-up.

## 20. Explicit `phase_commits` Provenance

Re-confirmed via direct source read: `phase_commits` must be declared in
`.pcae/phase-completion-metadata.json` *before* `pcae phase complete`/
`task finish` is invoked — it is read once, at trial-report-construction
time, and baked into `report.commits`, which flows into
`compute_report_digest`/`compute_finalization_snapshot_id` (both
unmodified) — meaning the declared commit list is bound into the
immutable finalization snapshot exactly like every other certified
field. Post-certification metadata edits cannot retroactively alter an
already-sealed report's own `commits` list (the sealed `PhaseReport`
object, not the mutable metadata file, is what `compute_report_digest`
hashes).

## 21. Missing `phase_commits` — Exhaustive Case Re-Derivation

| Metadata state | `report.commits` | `report_completeness` |
|---|---|---|
| `phase_commits` key absent | `[]` (via `phase.py`'s repaired fallback) | Incomplete (structural `commits` trust-field gap, Section 5 pre-existing check) |
| `phase_commits: []` (explicit empty) | `[]` | Incomplete, same mechanism |
| `phase_commits: null` | Treated as absent by `meta.get("phase_commits", [])`'s own default — `[]` | Incomplete, same mechanism |
| `phase_commits` malformed (e.g. a plain string, not a list) | `meta_hashes` comprehension would raise or produce `[]` depending on the malformed shape — re-derived: a non-list value passed to the list comprehension `for c in phase_commits_meta` would raise `TypeError` if not iterable, or silently produce `[]`/garbage if iterable-but-wrong-shape (e.g. a string iterates character-by-character) | Either an uncaught exception (fail-closed by crash, acceptable but not graceful) or Incomplete via the empty-list path — **not** silently "complete" in either case |
| Single unknown/fabricated hash declared | `["deadbeef00"]` (non-empty) | **Complete is reachable** — Section 19's disclosed gap |
| Mixed current-phase + prior-phase hash | Cross-phase check fires on the prior-phase hash | Incomplete (blocked) |
| Source revision only, no phase_commits | `[]` via fallback | Incomplete |
| Bookkeeping commit only, correctly attributed | Non-empty, passes cross-phase check | Complete (correct — a phase legitimately consisting only of a bookkeeping commit is not itself invalid) |

## 22. Cross-Phase Ownership Detection Against Real Archives

Re-run `detect_cross_phase_commit_contamination` against every commit
hash appearing in this session's own `.pcae/phase-reports/latest.json`
snapshots for 134E.10, 134E.10V, 134E.10.1, and 134E.10.1.1 (to the
extent still present on disk — `.pcae/phase-reports/` is gitignored/
ephemeral per 127D's established finding, so only the current session's
own local state was available, not a full historical archive) — no
additional contamination found beyond the already-known and already-
repaired `1844b05b` case. No shared/correction/supersession scenario
exists in this track's actual history to test against a real example;
the mechanism's *design* (Section 17) supports narrow, explicit,
provenance-bearing shared classification if 134D ever authorizes it, but
none currently exists, and none was fabricated for this verification.

## 23. Both Finalization Paths — Consistency Confirmed

`phase.py` and `task.py` both call `detect_cross_phase_commit_
contamination(commits, phase_id)` with identical semantics immediately
after their respective `validate_finalization_gate` calls — re-confirmed
via direct diff of the two call sites, functionally identical apart from
variable naming. `phase_reports.py` and `notifications.py` do not
independently call this function — a real, disclosed asymmetry (matching
134E.10.1.1's own disclosure that the defect was isolated to `phase.py`'s
own fallback, `task.py`'s was already safe, and `phase_reports.py`/
`notifications.py` never had a recent-commit-guessing fallback to begin
with, since they operate on already-declared or already-set commits, not
a fresh `_gather_commits()`-style guess). **NON-BLOCKING**: the two
entry points lacking the additive contamination check were never at risk
of the *root-cause* defect (they have no blind-guess fallback), so the
asymmetry is a defense-in-depth gap, not a live exposure.

## 24. Historical Preservation

All nine relevant Track 134 documents (134E.8 repair, 134E.8.1 incident
repair, 134E.9 validation, 134E.9.1 correction, 134E.9V verification,
134E.10 implementation, 134E.10V verification, 134E.10.1 repair,
134E.10.1.1 correction) confirmed present, zero deletions via `git log
--diff-filter=D`. `.pcae/phase-reports/` remains ephemeral/gitignored per
127D's established finding — this verification did not, and could not,
independently audit a full historical receipt/marker archive beyond
current local state, consistent with every prior phase's own identical
limitation.

## 25. External-Delivery Isolation

Re-confirmed: `tests/conftest.py`'s autouse `_isolate_external_
notifications` fixture applies to every test in every suite re-run this
phase; no test in this phase's own (zero new) additions sets a live
notification variable (this phase added no new test file — Section 19's
finding was reproduced via direct REPL invocation, not a committed
test). No production marker, receipt, or checkpoint was written during
this phase's own regression runs (`git status --short .pcae/` clean
after every run). `pcae architecture-status inspect`/`pcae phase-report
consistency` re-confirmed side-effect-free.

## 26. Full-Suite Baseline Comparison

Identical methodology to every prior phase in this track: `python -m
pytest tests/ -q -ra -n auto`, same environment, same command. Result:
19,371 passed, 182 failed — **exact node-ID set equality** (`comm -13`/
`comm -23` against the established 182-failure baseline both empty) —
zero new failures, zero fixed/flaky failures, zero accidental
deselection (identical total collected count consistent with zero new
tests added this phase), zero marker changes. Correctly classified as
baseline-equivalent, not "passed."

## 27. Repeated Fast-Green

```
python -m pytest -m "fast_green" -n auto -ra -q   (parallel, run 1)
4391 passed, 70.28s

python -m pytest -m "fast_green" -n auto -ra -q   (parallel, run 2)
4391 passed, 70.75s

python -m pytest -m "fast_green" -n 0 -ra -q       (serial)
4391 passed, 15162 deselected, 197.14s
```

Identical selected-test count and zero failures across all three runs.
Zero repository pollution, zero external delivery in any run.

## 28. Compileall and Focused Regressions

`python -m compileall -q src tests`: clean. Broader affected regression
(`test_finalization_transaction_134e10.py` [37], `test_commit_
attribution_repair_134e10_1_1.py` [12], `test_rc_audit_findings_repair.py`
[18], `test_phase_reports.py`, `test_task_finish_report_trust_
notification.py`, `test_notification_certification_idempotency.py`,
`test_post_push_canonicalization.py`, `test_report_consistency_derived_
correctness_134e9.py`, `test_architecture_status_generation_repair_
134e8.py`, `test_architecture_status_generation_independent_
verification_134e8v.py`): 426 passed, 1 pre-existing unrelated failure
(`TestPhase126G1CommitTrustMetadataRepair::test_report_completeness_
reaches_complete_via_cli_alone`, independently re-confirmed unchanged
from every prior phase's own disclosure).

## 29. Architecture Status

`pcae architecture-status inspect` (pre-finalization state): current
phase `134E.10.1.1 (completed)`, planned `134E.10.1V — Final Lifecycle
Integration [Transaction-Span Repair Independent Verification]`, Tracks
132–134 represented, no stale `132F`, no completed/planned overlap,
`Validation: passed`. Re-derived independently, not re-cited.

## 30. Findings Summary

| # | Finding | Classification |
|---|---|---|
| 1 | Control inversion genuinely gates promotion/dispatch behind mandatory pre-promotion stages, across all four entry points | **CONFIRMED** |
| 2 | No competing legacy authority; the two non-transaction call sites are the pre-existing `--allow-partial-report` override and the gate-already-failed case, both safe | **CONFIRMED** |
| 3 | The phase-finalization skill is documentation only, not a bypass | **CONFIRMED** |
| 4 | Seven subsystems: five gained real gating authority over whether finalization proceeds; none gained authority over report content or the physical dispatch mechanism | **CONFIRMED**, precisely stated |
| 5 | Receipt honesty preserved and correctly adapted to read the post-promotion report | **CONFIRMED** |
| 6 | Logical marker ordering correct in every failure case reasoned through | **CONFIRMED** |
| 7 | A dispatch failure inside an otherwise-successful callback does not, by itself, trigger transaction-level retry (recovery is the existing marker-driven path's responsibility) | **CONFIRMED**, precisely stated, not a defect |
| 8 | Commit-subject detection used exclusively as rejection evidence, never positive proof | **CONFIRMED** |
| 9 | Doubly-dotted phase-ID parsing consistent across all three relevant regexes (one disclosed, non-exploitable case-sensitivity asymmetry in the title regex) | **CONFIRMED / NON-BLOCKING** |
| 10 | Missing/empty `phase_commits` cannot reach "complete" (pre-existing structural check, independent of 134E.10.1/134E.10.1.1's own additions) | **CONFIRMED** |
| 11 | Fabricated/unresolvable commit hashes in an explicitly-declared `phase_commits` list currently pass the cross-phase check silently | **NON-BLOCKING — genuine gap, disclosed, not repaired (design change out of proportion for this phase)** |
| 12 | `phase_reports.py`/`notifications.py` lack the additive contamination check `phase.py`/`task.py` have | **NON-BLOCKING — asymmetry disclosed; neither entry point was ever exposed to the root-cause defect** |
| 13 | All 7 relevant commits' ownership independently re-derived and matches every prior claim exactly | **CONFIRMED** |
| 14 | Historical preservation, external-delivery isolation, full-suite baseline, fast_green, Architecture Status | **CONFIRMED**, all intact |

**Zero unresolved BLOCKING findings.**

## 31. Governance Results

- `pcae check`, `pcae health`, `pcae doctor task-memory`, `pcae push
  check`: clean/healthy/passed throughout.
- Governed commit/push/task/phase commands only; no raw `git commit`, no
  raw `git push`, no `--no-verify`, no force push.
- Runtime remained Observed/observe/unavailable throughout — this phase
  touched zero runtime/execution code and added zero new source files.

## 32. Explicit Confirmations

- No external test delivery occurred (Section 25).
- Exactly one ordinary logical completion is produced for `134E.10.1V`,
  at this phase's own governed finalization.
- Physical-vs-logical delivery limitation unchanged from every prior
  phase: a receipt/marker proves a local dispatch attempt and its
  self-reported outcome, never independently-verified remote acceptance
  or end-user receipt.
- Runtime remains Observed; execution remains unavailable.
- 134F has not begun.

## 33. Recommended Next Phase

**134F — Whole-Lifecycle Independent Verification**, recommended only
because zero unresolved BLOCKING findings remain across this phase's own
re-derivation of both 134E.10.1 and 134E.10.1.1. 134F has not begun and
is not begun by this phase.
