# Phase 136AX: Lifecycle Bootstrap & Session State Reporting Repair

## 1. Purpose and boundaries

Repairs the lifecycle bootstrap, session-state derivation, and reporting
defects that have repeatedly produced incomplete, stale, truncated, or
internally inconsistent PCAE status output across `pcae session
bootstrap`, `pcae health`, `pcae check`, `pcae status coherence`, `pcae
governance audit`, `pcae architecture-status inspect`, canonical phase
metadata, and canonical phase reports.

This is a governance-infrastructure repair phase only. It makes **no**
changes to Stage 3 schemas, shared companion-schema definitions, or the
`pcae.cltr.authority` typed authority model package, and authorizes
**no** new execution capability. Runtime remains `Observed` / `observe`
/ `unavailable` throughout (unchanged by this phase; verified in
Section 8). Phase 137A (Typed Authority Model Consumption Architecture)
was **not** begun.

## 2. Root cause

**A single root cause explains the majority of the reported symptoms**:
this repository's phase-ID grammar assumed exactly one mainline branch
letter (`\d+[A-Z]`, e.g. `"136A"`, `"136W"`). Track 136 exhausted single
letters A-Z and rolled over into two-letter mainline suffixes
(`136Z -> 136AA -> ... -> 136AW -> 136AX`), which the single-letter
grammar cannot match at all — the phase-ID capture group simply fails,
and every regex built on top of it (declaration-line parsing,
recommendation parsing, commit-contamination detection, phase-queue
validation, task-title phase extraction) fails or falls back to a
degraded path along with it.

This grammar had already been independently reimplemented **at least
nine times** across the codebase, with inconsistent letter-count
handling:

| Location | Letter count before repair | Consequence |
|---|---|---|
| `pcae.core.phase_reports._CANONICAL_TITLE_PHASE_ID_RE` | exactly 1 | canonical-report-title identity extraction failed for `136AW`+ |
| `pcae.core.phase_reports._COMPLETED_PHASE_HEADER_RE` | exactly 1 | `"## Phase 136AW Complete"` headers (once written) would not be recognized as completed |
| `pcae.core.phase_reports._PHASE_LABEL_LINE_RE` | exactly 1 | phase-label text extraction failed |
| `pcae.core.phase_reports._CURRENT_PHASE_LINE_RE` | exactly 1 | **the exact, reproduced cause of "## Current Phase section present but its phase-ID/title line did not parse -- current phase could not be identified"** |
| `pcae.core.phase_reports` (base-phase comparison, `validate_phase_identity`) | exactly 1 | a third, independently-broken re-implementation (also `\d{3}` fixed-3-digit) of "find the Current Phase declaration line" |
| `pcae.core.phase_reports._COMMIT_SUBJECT_PHASE_TOKEN_RE` | exactly 1 | commit-contamination detection silently blind for two-letter-suffix phases (deliberately conservative "skip if unresolved" masked the gap) |
| `pcae.core.architecture_status.PHASE_ID_RE` | exactly 1 | `is_valid_phase_id("136AW")` was `False`; `parse_phase_id` returned `None` |
| `pcae.core.architecture_status.validate_architecture_status` (`in_progress` back-reference regex) | exactly 1 | validator could not recognize a two-letter-suffix ID inside an `in_progress` display string |
| `pcae.core.context` (active-task-vs-current-phase mismatch detection) | exactly 1 | mismatch detection silently inert for two-letter-suffix phases |
| `pcae.core.tasks.phase_text_from_title` | exactly 1 | task-title phase-ID extraction failed |
| `pcae.commands.phase._VALID_PHASE_ID_RE` (advisory phase-queue validator) | exactly 1, no letter-suffix subphase | `pcae phase queue audit` would flag a genuinely valid `"136AX"` entry as `invalid phase_id` |

By contrast, `pcae.core.check._PHASE_CODE_RE` (`r"\b(\d+[A-Z][\d.A-Z]*)\b"`)
and `pcae.core.agent._TSA_PHASE_CODE_RE` already correctly handled
multi-letter suffixes via a trailing `[\d.A-Z]*` class — direct evidence
that different commands used genuinely different, disagreeing grammars
for the same identifier, exactly the "duplicated regexes" / "no shared
canonical reader" failure mode this phase was asked to investigate.

A second, compounding defect sits on top of the phase-ID grammar: the
declaration-line and `"Recommended next phase:"` sentence regexes
captured only up to the first physical newline (`(.+)$` under
`re.MULTILINE` without `re.DOTALL`), and the latter additionally
required `"Recommended"` to start a physical line (`^...$`). This
repository hand-wraps prose across multiple physical lines and routinely
embeds the recommendation sentence mid-paragraph (e.g. `"...the
re-derived contract exactly. Recommended next phase: **136AV — Stage
3\nTyped Authority Model Whole-Model Integration Verification**."`) —
so the sentence essentially never matched real content, and when a
declaration line did match by coincidence, its title was silently
truncated at the wrap point. This is the reproduced cause of "Planned or
Recommended Next Phase entries truncated" and (via
`pcae.core.status.check_project_status_current_phase`'s `first_line()`
call, a fourth independent parser) of `pcae governance audit`'s "Current
phase: ..." line being chopped mid-sentence.

A third, independent defect: `pcae.commands.phase`'s finalization path
(`_finalize_report_and_notify`) read `.pcae/phase-completion-
metadata.json`'s `files_changed` field with `len()` on **any** truthy
value that was not an `int` — including a malformed `str` — silently
fabricating a nonsensical count (`len("not a number of files") == 22`,
unrelated to any real file count). The same function's
`validation_results`/`governance_results` reads used `meta.get(key, [])`,
whose default only applies when the key is **absent**; an explicit JSON
`null` (key present, value `null`) returns `None`, and the old code
iterated it directly (`for vr in test_results_raw:`), raising
`TypeError` and unconditionally blocking `pcae phase complete`/`pcae
task finish` on a non-critical display field. A list item that was not
itself a `dict` raised `AttributeError` for the same reason. All three
are display-only summary fields — never governance-critical (they never
gate finalization) — so a malformed value must degrade safely, not crash
finalization and not fabricate evidence.

A fourth, narrower defect: `pcae.commands.task._read_lifecycle_current_
phase_line()` returned only the *first physical source line* of the
Current Phase section, then `resolve_canonical_phase_identity()` checked
that returned string for a literal `"(completed)"` substring to decide
whether the lifecycle fallback identity source could be used. Because
the `"(completed)"` marker is often on a *later* physical line than the
phase-ID/title (this repository's actual wrapping convention), an
already-completed current phase could look not-yet-completed to that
check — a genuine current/completed conflation risk, though narrow
(this source is only consulted when both `active_task_title` and
`metadata.phase_id` are absent).

## 3. Authoritative state-source map

| State | Canonical source | Consumers | Classification |
|---|---|---|---|
| Active governed phase / task | `tasks/active/*.md` task contract | `pcae check`, `pcae health`, `pcae session bootstrap` | canonical |
| Latest completed phase, status, recommendation | `.pcae/phase-reports/latest.json` (immutable, written once per finalization) | `pcae session bootstrap` | canonical |
| `.pcae/phase-completion-metadata.json` | mutable, hand-edited scratch input to the *next* finalization | `pcae phase complete`, `pcae task finish`, `pcae notify send-report` | **not** canonical for "what did the last phase report" — see Limitations |
| Current phase declaration / recommendation prose | `PROJECT_STATUS.md`'s `## Current Phase` section | `build_architecture_status()`, `check_project_status_current_phase()`, `_read_lifecycle_current_phase_line()` | derivative (hand-authored prose, not generated) |
| Architecture Status (`completed`/`in_progress`/`planned`) | `build_architecture_status()`, derived from `PROJECT_STATUS.md` at report-generation/inspection time | `pcae architecture-status inspect`, embedded in every phase report's `architecture_status` field | derivative, regenerated on demand, never manually maintained |
| Notification dispatch outcome (last completed phase) | `latest.json`'s `notification_result` field | `pcae session bootstrap` (Phase 136AX: now surfaced; see Section 6) | canonical, was previously unread by bootstrap |
| Sink configuration (Telegram token/chat-id/enabled) | process environment (`PCAE_TELEGRAM_*`, `PCAE_NOTIFY_ENABLED`) | `pcae session bootstrap`, `pcae notify status` | canonical for "is a sink configured", **not** authoritative for "was the last dispatch sent" |
| `bootstrap_session_reporting_tests` / `report_notification_tests` result | free-text values inside `.pcae/phase-completion-metadata.json`'s `validation_results`, authored by the completing agent | phase-report trust gate (`REQUIRED_TEST_FIELDS`) | canonical once persisted into the immutable report; author-supplied, not code-computed (see Section 7) |

**Precedence rule** (already correctly implemented and preserved,
confirmed by direct inspection): canonical machine-readable metadata
(`.pcae/phase-reports/latest.json`, `.pcae/phase-completion-metadata.json`)
takes precedence over `PROJECT_STATUS.md` prose wherever both exist for
the same fact — `pcae session bootstrap`'s "Recommended next phase" line
was already sourced from `latest.json`, never from `PROJECT_STATUS.md`.
The defect this phase repairs was never "the wrong source won" — it was
that `PROJECT_STATUS.md`-derived consumers (`build_architecture_status`,
`pcae governance audit`) could not parse the current, correctly-worded
prose at all, making the *derivative* view wrong or empty even though
the canonical view was already right. Section 6's live-repository proof
confirms both views now agree.

## 4. Production repairs

All repairs are narrow, targeted at the reproduced defects above, and
none touch Stage 3 schemas or the authority package.

1. **Unified phase-ID branch-letter grammar to one-or-more
   (`[A-Z]+`)** across every location in the table in Section 2:
   `pcae/core/phase_reports.py` (`_CANONICAL_TITLE_PHASE_ID_RE`,
   `_COMPLETED_PHASE_HEADER_RE`, `_PHASE_LABEL_LINE_RE`,
   `_CURRENT_PHASE_LINE_RE`, `_COMMIT_SUBJECT_PHASE_TOKEN_RE`, and the
   base-phase comparison in `validate_phase_identity`, which now reuses
   the shared `_CURRENT_PHASE_SECTION_RE`/`_CURRENT_PHASE_LINE_RE`
   instead of a third, independently-broken `\d{3}[A-Z]` pattern),
   `pcae/core/architecture_status.py` (`PHASE_ID_RE`, and the
   `in_progress` back-reference regex in `validate_architecture_status`),
   `pcae/core/context.py`, `pcae/core/tasks.py`,
   `pcae/commands/phase.py` (`_VALID_PHASE_ID_RE`).

2. **New `_match_current_phase_declaration()`**, a single shared,
   two-tier declaration-line parser used by every consumer (replaces
   direct regex matching at all three call sites). Tier one
   (`_CURRENT_PHASE_LINE_WITH_STATUS_RE`) captures the title with
   `re.DOTALL`, bounded to the nearest recognized status marker
   (`(completed|not started|in progress|blocked|partial|cancelled)`)
   rather than the first physical newline — preserves a wrapped title in
   full while remaining bounded (never open-ended into the rest of the
   section's prose). Tier two (`_CURRENT_PHASE_LINE_NO_STATUS_RE`) is
   the original, letter-count-fixed single-physical-line grammar,
   applied only when tier one finds no status marker at all — this
   repository's convention does not universally include one (e.g.
   `"Phase 134E.10.1V.1 — Completed-Phase Architecture Status Transition
   Repair."`, no trailing parenthetical), and requiring one
   unconditionally regressed that shape during this phase's own
   verification (Section 9). A declaration with no status marker is
   treated as not-completed, exactly matching the pre-136AX substring
   check's behavior for the same input — never guessed as completed.

3. **`_RECOMMENDED_NEXT_PHASE_RE` replaced** by
   `_RECOMMENDED_NEXT_PHASE_LABEL_RE` (locates the label anywhere in the
   bounded section text, not just at a physical line start) plus
   `_extract_recommended_next_phase_values()`, which extracts the value
   using this repository's two actual authoring conventions: a
   `**bold**` span (delimiter = the first closing `**`, immune to an
   incidental period inside the span, e.g. a parenthetical like
   `"(implementing only \`ConcurrencyConflict\` and
   \`RecoveryJournalEntry\`)"` that follows the closing `**`), or a
   plain sentence terminated by `". "`/end-of-text. Whitespace
   (including embedded newlines) is normalized to single spaces.
   Recommendation extraction remains scoped only to the current phase's
   own bounded section text (the 134E.8 whole-file-fallback removal is
   preserved; the fallback is not reintroduced).

4. **`pcae.core.status.check_project_status_current_phase()`** (used by
   `pcae governance audit`) now delegates to the shared
   `_CURRENT_PHASE_LINE_RE` for a full, untruncated declaration instead
   of `first_line(read_markdown_section_text(...))`, falling back to the
   previous (still-truncating, but never worse) behavior only when the
   shared parser cannot identify a declaration line at all.

5. **`pcae.commands.task._read_lifecycle_current_phase_line()`** now
   reuses `_CURRENT_PHASE_SECTION_RE`/`_CURRENT_PHASE_LINE_RE` instead of
   returning only the first physical line, so the `"(completed)"` status
   marker is reliably present when the identity-resolution fallback
   checks for it, regardless of where the declaration wraps.

6. **`pcae.commands.phase`'s `files_changed` handling**: `len()` is only
   ever called on an `int` or `list` value now; any other truthy shape
   (e.g. a malformed string) falls through to the git-derived fallback
   count instead of fabricating a number. `validation_results`/
   `governance_results` are only iterated when they are actually a
   `list` (an explicit `null` or other malformed shape degrades to an
   empty dict, never crashes); non-`dict` list items are skipped rather
   than raising. The equivalent `pcae.commands.task._finalize_task_
   report_and_notify()` read of `validation_results` received the same
   explicit-`null` guard.

7. **`pcae.commands.session.run_session_bootstrap`**: the
   em-dash-only dash split at the active-task/recommended-phase
   comparison now splits on the same `[—–-]` character class used
   throughout `phase_reports.py` (was a narrower, independently
   maintained special case that silently did nothing for an en dash).
   Bootstrap now also prints a `"Last phase notification: ..."` line,
   sourced from `latest.json`'s already-loaded `notification_result`
   field (never read before), via a new `_format_notification_result()`
   helper that keeps "sink configured/enabled" (environment-derived,
   printed on the existing `"Telegram runtime: ..."` line) and "did the
   *last phase's own* dispatch attempt succeed" (report-derived)
   visibly distinct, without changing dispatch behavior in any way.

8. **`PROJECT_STATUS.md`**: the live `## Current Phase` section for
   136AW was missing the `"Recommended next phase:"` sentence entirely
   (it only said "Phase 137A ... was **not** begun in this phase"),
   which is why `build_architecture_status()` correctly-but-unhelpfully
   reported "no planned phase disclosed" while `pcae session bootstrap`
   (reading canonical metadata) already showed `"Recommended next
   phase: 137A — ..."`. Added the convention-following sentence
   (`"Recommended next phase: **137A — Typed Authority Model Consumption
   Architecture** (not started)."`) so both views agree — see Section 6
   for the live proof.

## 5. Test repairs

One, narrowly scoped and test-only. Fixing `validate_phase_identity`'s
current-phase parsing (Section 4, item 1) to correctly resolve `136AW`
exposed a **masked bug in `tests/test_rc_audit_findings_repair.py`'s own
`_current_project_phase_id()` helper**: it carried the identical
single-mainline-letter grammar this phase repairs everywhere else
(`\d{3}[A-Z]`, not `\d{3}[A-Z]+`), silently truncating the live
repository's current phase to `"136A"`. Before this phase's repair,
`validate_phase_identity` *also* failed to parse `"Phase 136AW"` at all,
so the phase-identity mismatch comparison never ran — the two bugs
coincidentally canceled out and the test passed by accident, not because
its expectation was correct. After the repair, the production
comparison correctly resolves `"136AW"`, and the test's own truncated
`"136A"` now legitimately fails the (now-working) comparison it exercises.

This is exactly the "historical test whose expectation is made obsolete
by this repair, reviewed against its original invariant before being
changed" case the repair policy anticipates: the helper's *invariant*
("read the real, current, exact phase identity from `PROJECT_STATUS.md`
for use in a synthetic report") was never in question — only its
grammar was wrong, in the same way and for the same reason as every
other repaired location in Section 2's table. Applied the identical
one-character fix (`[A-Z]` → `[A-Z]+`) to this one test helper only; no
other test expectation, fixture, or assertion in that file was touched.

## 6. Live-repository proof

Before this phase's repair, run against the unmodified tree (git
`stash`-verified):

```
$ pcae architecture-status inspect
...
## Current Phase section present but its phase-ID/title line did not
parse -- current phase could not be identified
current phase section has no explicit 'Recommended next phase' sentence
-- no planned phase disclosed
```

After the repair (current tree, run live):

```
$ pcae architecture-status inspect
...
Current phase: 136AW (completed)

Planned:
  - 137A — Typed Authority Model Consumption Architecture
...
Validation: passed
```

```
$ pcae governance audit
  - project_status_current_phase: pass (Current phase: Phase 136AW —
    Stage 3 Typed Authority Model Final Review and Stage-Exit Readiness
    Assessment (completed))
```

`build_architecture_status()["planned"][0]` now equals
`.pcae/phase-completion-metadata.json`'s `recommended_next_phase` field
exactly — the two-source disagreement the root-cause analysis found is
closed (also asserted directly in
`tests/test_phase_136ax_lifecycle_bootstrap_reporting_repair.py::TestRecommendedNextPhaseParsing::test_live_repo_136aw_recommendation_matches_canonical_metadata`).

## 7. `bootstrap_session_reporting_tests` applicability

Confirmed by direct source inspection (no code path computes or defaults
this value): `bootstrap_session_reporting_tests` and
`report_notification_tests` are two of the three `REQUIRED_TEST_FIELDS`
in `pcae.core.phase_report_trust`. Both are **author-supplied free text**
inside `.pcae/phase-completion-metadata.json`'s `validation_results`
dict, carried through unchanged into the immutable persisted report.
`"not_applicable"` is not a hardcoded default anywhere in `src/pcae` for
either field — it only appears where a completing agent wrote it,
describing that the category genuinely was not exercised that phase
(e.g. no Telegram dispatch was attempted because `PCAE_NOTIFY_ENABLED`
was deliberately unset for that run).

Governing rule going forward: `bootstrap_session_reporting_tests` is
**applicable and must be reported `passed`/`failed`** — never
`not_applicable` — for any governed phase whose own scope exercises
`pcae session bootstrap`, `pcae health`, `pcae check`, or `pcae status
coherence` against real repository state, since that exercise is direct,
observable evidence, not merely "bootstrap was invoked once in
passing." It is only legitimately `not_applicable` when a phase's scope
never invokes or inspects any of those commands at all. This phase's own
canonical metadata reports it `passed`, with the evidence being this
phase's own repeated live invocations in Section 6 plus the dedicated
regression suite in Section 9.

## 8. Governance boundaries confirmed

No authority resolution, activation, transfer, or cutover occurred. No
publication, marker, finalization-receipt, migration, recovery,
rollback, compatibility, or quarantine operation occurred. No Stage 3
schema, shared companion-schema definition, or `pcae.cltr.authority`
production module was read for modification (confirmed:
`tests/test_phase_136ax_lifecycle_bootstrap_reporting_repair.py::TestGovernanceBoundaries`
asserts none of the changed modules import the authority package).
Runtime state remains `Observed` / `observe` / `unavailable`
(`pcae architecture-status inspect`'s Runtime block, reproduced in
Section 6, is unchanged by this phase). No lifecycle mutation occurred
outside the standard governed `pcae task` / `pcae phase-report` / `pcae
phase complete` finalization path.

## 9. Regression evidence

New dedicated module:
`tests/test_phase_136ax_lifecycle_bootstrap_reporting_repair.py` — 36
tests covering the two-letter mainline suffix grammar, wrapped/unwrapped
current-phase parsing (including malformed-input and no-section
limitation disclosure, Unicode en-dash, and a declaration line with no
status marker at all), recommended-next-phase parsing precedence and
no-fabrication, `pcae governance audit` parity with
`build_architecture_status`, the `_read_lifecycle_current_phase_line`
completed-marker fix, phase-completion/task-finish malformed-metadata
crash regressions (string `files_changed`, explicit-`null`
`validation_results`/`governance_results`, non-dict list items),
notification-result state formatting (including no-secret-disclosure),
and governance-boundary confirmation. All 36 pass.

`python -m pytest -m "fast_green" -n auto`: **4391 passed, 0 failed** —
matches the 136AW-recorded baseline exactly.

Full repository suite (`-m "not slow"`, `-n auto`, freshly run): **21
failed / 24396 passed / 9 skipped**. Every one of the 21 failures was
individually reproduced identically on the unmodified tree via `git
stash` comparison and confirmed pre-existing and unrelated to this
phase's changed files:

- `test_advisory_runtime_contract.py` / `test_advisory_runtime_architecture.py`
  — `test_no_new_directory_added_for_advisory` (x2)
- `test_cltr_authority_136aj_recovery_concurrency.py` /
  `test_cltr_authority_136am_notification_authority_binding_independent.py`
  — package (re)import side-effect-free checks; pass in isolation, fail
  only under full-suite parallel collection order — the same
  order-dependent test-infrastructure flake class 136AW's own report
  disclosed for `test_136z_absent_pickle_round_trip_preserves_identity`
- `test_rendering_134e5.py::test_current_report_generation_remains_unchanged`
- `test_finalization_transaction_134e10.py` (x5) —
  `completed_receipt_best_effort_incomplete` vs `completed` status
  mismatch, unrelated to lifecycle-reporting parsing
- `test_cltr_migration_135p_verification.py` (x4, one per entry point)
- `test_bootstrap_todo_consistency.py` (x2) — a stale `"132F"`
  expectation baked into `tasks/TODO.md` fixture text, unrelated to
  `PROJECT_STATUS.md` parsing
- `test_cltr_135o_integration.py` (x4)
- `test_phase_reports.py::TestPhase128B1NotificationDispatchReliabilityRepair::test_public_reconciliation_requires_report_marker_checkpoint_and_receipt`

**Two genuine regressions were found and repaired during this phase's
own verification** (not left in the final count above): fixing the
current-phase-declaration parser correctly enough to resolve `"136AW"`
exposed two tests whose own fixtures/helpers depended on the *old*,
broken behavior — `tests/test_completed_phase_architecture_transition_134e10_1v_1.py`
(a fixture with no status-marker parenthetical at all, which the
first-draft repair's marker-*required* grammar rejected; fixed by adding
the two-tier `_match_current_phase_declaration()` fallback in Section 4)
and `tests/test_rc_audit_findings_repair.py` (a masked bug in the test's
own `_current_project_phase_id()` helper — see Section 5). Both are
green in the final run above.

## 10. Limitations and deferred items

- **`.pcae/phase-completion-metadata.json` remains a mutable, reused
  scratch artifact**, not versioned per-phase. It is read directly by
  both `pcae phase complete` and `pcae task finish`/`pcae notify
  send-report`, and can legitimately hold values in preparation for the
  *next* finalization that disagree with the last *persisted* report
  (confirmed live during this phase's own investigation: the scratch
  file briefly held `"(passed)"` text for `report_notification_tests`/
  `bootstrap_session_reporting_tests` while the immutable `latest.json`
  correctly recorded `"(not_applicable)"` for 136AW). This is a known,
  pre-existing property of the finalization design, not a defect this
  phase introduced or was asked to redesign (that would be a lifecycle-
  authority change, out of this phase's authorized scope) — callers
  needing "what did the last *completed* phase actually report" must
  read `.pcae/phase-reports/latest.json`, never the scratch metadata
  file, and this document records that precedence explicitly (Section
  3) for future reference.
- **`pcae governance audit`'s `project_status_next` check** looks for a
  `"## Next"` Markdown heading that this repository's `PROJECT_STATUS.md`
  convention does not use at all (it uses per-phase `"## Current Phase"`
  sections instead) — this check fails unconditionally on this
  repository and is unrelated to any defect reproduced in this phase.
  Redesigning or retiring that check is a separate, narrower follow-on,
  not undertaken here to keep this repair scoped to reproduced defects.
- **No single shared "lifecycle state" reader module was introduced.**
  `pcae session bootstrap`, `pcae health`/`pcae check` (which report no
  phase state at all), and `PROJECT_STATUS.md`-derived consumers
  (`build_architecture_status`, `check_project_status_current_phase`,
  `_read_lifecycle_current_phase_line`) still read from different
  sources by design (canonical `latest.json` vs. derivative hand-authored
  prose) — this is correct per the precedence rule in Section 3, not a
  defect. What this phase did unify is the *parsing grammar* shared by
  the `PROJECT_STATUS.md`-derived consumers (now three call sites reuse
  `phase_reports._CURRENT_PHASE_SECTION_RE`/`_CURRENT_PHASE_LINE_RE`
  instead of three-to-four independently broken reimplementations). A
  full merge of `pcae health`/`pcae check`/`pcae status coherence` into
  one shared phase-state-reporting component would be a materially
  larger architectural change than a narrow reporting repair authorizes,
  and is left as a deferred item for a dedicated follow-on phase should
  it be prioritized.
- `pcae.core.status.recommend_next_roadmap_phase()`'s helper
  `_read_current_project_phase()` (a fourth PROJECT_STATUS.md "Current
  Phase" reader, used only by `pcae roadmap next`) was left unchanged:
  it already returns the full, untruncated first non-blank line (no
  `first_line()`-style truncation), so it was not exhibiting any of the
  reproduced symptoms, and touching it would be scope expansion beyond
  the reproduced defects.

## 11. Verdict

**REPAIRED — READY FOR INDEPENDENT VERIFICATION.**

All symptoms reproduced in Section 2 are closed by a direct, narrow fix
at their confirmed root cause (Section 4), with live-repository proof
(Section 6) and dedicated regression coverage (Section 9). No Stage 3 or
runtime-capability boundary was crossed (Section 8). The one legitimately
open item (Section 10's scratch-metadata-file mutability) is a
pre-existing, disclosed property of the finalization design, not a
defect within this phase's reproduced scope.
