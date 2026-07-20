# Phase 137S — Canonical Phase ID Parser Independent Verification

## Objective

Independently verify Phase 137R's Canonical Phase ID Parser
implementation against the frozen CPIPC-001 v1.0 contract
(`docs/contracts/CANONICAL_PHASE_ID_PARSING_CONTRACT.md`), re-deriving
expected behavior solely from CPIPC-001, Phase 137P's architecture, and
applicable lifecycle architecture — not from 137R's own report or
implementation decisions. Verification phase only; runtime remained
Observed / observe / unavailable throughout.

## Verdict

**NOT VERIFIED as fully conformant.** One Blocking defect was
independently demonstrated and repaired minimally in this phase (see
Repair, below). Several additional non-blocking conformance gaps were
independently found and are disclosed, unrepaired, for a future governed
phase — consistent with 137R's own report, which already disclosed some
of them as deliberately out of its scope.

`src/pcae/core/phase_id.py` itself (grammar, representation, parser API,
parsing semantics, comparison semantics, error taxonomy, security
requirements) was independently re-derived from CPIPC-001 §4–§11 and
§16 and found conformant, with one minor error-taxonomy misclassification
noted below.

## Independent re-derivation and grammar/behavior verification

Re-derived the grammar (§4), representation (§5), parser API (§8),
parsing semantics (§9), comparison semantics (§10), and error taxonomy
(§11) directly from CPIPC-001 and constructed adversarial fixtures
independent of `tests/test_phase_id.py`, including: reserved forms
(`"134"`, `"007A"`), malformed dotted forms (`"134E.V1"`, `"134.A"`,
`"134..A"`, `"134A."`, `"134A..1"`), whitespace variants, case variants,
the exceptional branch (`113X.1`), and extreme-length series
(`"999999999999999999999A"`). Findings:

- Grammar acceptance/rejection, normalization, uppercasing, branch
  spreadsheet-column rollover comparison (`AA > B`), the exceptional-
  branch exclusion, `not_comparable` as a first-class outcome, and the
  absence of an artificial total ordering all matched CPIPC-001 exactly.
- **Minor, non-blocking**: `_classify_invalid` in `phase_id.py`
  misclassifies input where branch letters exist but are separated from
  `series` by a stray `.` (e.g. `"134.A"`, `"134..A"`) as `missing_branch`
  ("a numeric series was present with no branch letters at all" —
  CPIPC-001 §11's own stated meaning for that kind). Branch letters are
  in fact present in this input, just misplaced; the correct kind per
  the taxonomy's own semantics is closer to `invalid_syntax`. This does
  not cause any false acceptance or silent truncation — the input is
  still correctly rejected — only the reported error kind is imprecise.
  Disclosed, not repaired (non-blocking, no observable governance
  impact found).
- The canonical parser performs no filesystem, repository, or network
  access anywhere in its source; every public function is a pure
  function of its arguments; no module-level mutable state exists
  (CPIPC-001 §16 confirmed by direct source inspection, not by trusting
  137R's own claim).

## Consumer inventory verification

Per this phase's brief, 137R's claimed migration inventory
(`docs/CANONICAL_PHASE_ID_PARSER_MIGRATION.md`) was not trusted; a fresh
`grep`-based re-inventory of `src/pcae/` was performed independently for
any Phase-ID-shaped recognition, validation, normalization, comparison,
or serialization logic.

### Blocking defect found and repaired: `core/context.py`

`docs/CANONICAL_PHASE_ID_PARSER_MIGRATION.md` row 6 claims `core/context.py`
was "Migrated, inline regexes removed," delegating to
`canonical_phase_id.find_first_token`, `match_leading_token`, and
`same_branch`. That claim is accurate for `_detect_phase_ambiguity` and
`_todo_roadmap_status`, but incomplete: a separate, un-migrated regex,
`_RECOMMENDED_NEXT_PHASE_RE`, remained in the same file inside
`_extract_recommended_next_phase` (used by `pcae session bootstrap`'s
`roadmap_summary.recommended_next_phase`), undetected by 137R's own
consumer inventory and unmentioned by its migration record.

`_RECOMMENDED_NEXT_PHASE_RE` required the literal historical phrase
`"Recommended next repo phase: <id> — <title> (not"` and searched the
**entire** `PROJECT_STATUS.md` file (not the current phase's own
section) for the first match. Since every phase since 134E.8 phrases
this sentence `"Recommended next phase: ..."` (no `"repo"`, no trailing
`"(not..."` clause — a wording change `phase_reports.py`'s own
`architecture_status` extraction path was already repaired for, in
134E.8/136AX, precisely because of this exact failure mode), the regex
never matched the current phase's own recommendation and instead
matched whichever historical section still used the old phrasing.

This was independently reproduced live, not hypothetically: at this
phase's bootstrap (`pcae session bootstrap --compact`, prior to any
repair), `roadmap_summary.recommended_next_phase` returned `137I.1V —
Finalization Ordering Deadlock Independent Verification` — a phase
completed several phases before 137R — instead of the actual current
recommendation, `137S`. This is the same phase-identity ambiguity
`pcae session bootstrap` itself flagged and halted on at the start of
this phase.

**Repair applied** (minimum necessary, per this phase's governing
brief): `_extract_recommended_next_phase` now bounds its search to
`PROJECT_STATUS.md`'s `"## Current Phase"` section only, reusing
`phase_reports.py`'s already-correct, already-tested
`_CURRENT_PHASE_SECTION_RE` and `_extract_recommended_next_phase_values`
(the exact fix already applied there for this identical defect class in
134E.8/136AX) instead of maintaining a second, independently-drifting
implementation of the same "recommended next phase" extraction — direct
elimination of a duplicate implementation per CPIPC-REQ-018/CPIPC-REQ-052,
not a compatibility shim around the old regex. `_RECOMMENDED_NEXT_PHASE_RE`
was removed outright.

Verified: `_extract_recommended_next_phase` now returns `"137S —
Canonical Phase ID Parser Independent Verification"` against the real
repository `PROJECT_STATUS.md`. `tests/test_bootstrap_todo_consistency.py`
(18 tests, including `test_recommended_next_phase_matches_real_project_status`,
a live-repository assertion) pass unmodified.

### Additional conformance gaps found — disclosed, not repaired (non-blocking)

Per this phase's minimum-necessary-repair scope, the following were
independently found and are disclosed for a future governed phase
rather than repaired here:

- **`core/phase_reports.py` residual duplicates.** 137R's own migration
  record already discloses (in "Residual, out-of-scope duplication")
  several phase-ID-shaped regexes in this file beyond the three CPIPC-001
  §14 named for it (`_LEADING_PHASE_REFERENCE_RE`, the Architecture
  Status consistency checker's closures, `_COMPLETED_PHASE_HEADER_RE`
  and siblings, `rec_id_match`). Independent re-inventory confirms these
  exist and additionally identifies a hand-rolled "same series" ad hoc
  string-prefix comparison inside test-evidence-classification logic
  (`re.match(r"^\d+", token).group(0) == current_series.group(0)`,
  around line 1357) — the specific pattern CPIPC-REQ-043 prohibits
  ("not reconstructed ad hoc by callers via string-prefix checks").
  137R's own report already scoped these out ("137R implements exactly
  the frozen §14 inventory... out of this phase's scope"); this
  verification confirms that disclosure is accurate and the residual
  logic is real, not resolving it.
- **Four consumers entirely outside CPIPC-001 §14's ten-row inventory**,
  meaning Phase 137P's original "independent, from-scratch" grep sweep
  (which found "fifteen distinct call sites across ten files") did not
  in fact find every Phase-ID-recognizing call site in the repository:
  - `core/tasks.py:phase_text_from_title` — own regex
    (`r"(?P<phase>\d+[A-Z]+)\s*:\s*(?P<label>.+)"`).
  - `core/governance_timeline.py:_extract_commit_events` — own regex
    pair extracting a Phase ID from commit-log prose.
  - `src/pcae/repository_intelligence/historical_memory/historical_builder.py:_PHASE_REF_IN_TEXT_RE`
    — notably **narrower** than the canonical grammar (`\d{2,3}[A-Za-z]`
    caps series at 2–3 digits and branch at exactly one letter), meaning
    it would silently fail to recognize a valid canonical Phase ID with
    a 1- or 4+-digit series or a rolled-over two-letter branch (e.g.
    `"136AX"`).
  - `src/pcae/commands/session.py:_extract_phase_number` — own regex
    duplicating series+branch extraction.
  Each is an independent, non-delegating Phase ID grammar implementation
  in violation of CPIPC-REQ-018/019/020's codebase-wide (not
  §14-table-scoped) ownership requirement. None were part of 137R's
  claimed migration scope, so they are not evidence 137R's own claims
  were false — they are evidence CPIPC-001's full codebase-wide
  ownership guarantee is not yet realized, which is exactly the gap the
  already-anticipated next phase (137T — repository-wide conformance)
  exists to close.

## Historical regression replay

Replayed the specific historical defects CPIPC-001 exists to foreclose
against the live canonical parser: single-letter and multi-letter
suffix truncation (137F.1V/137MV.1 class), dotted-suffix truncation,
the `repository_transition_integration.py` sibling defect, and the
113X.3 branch-comparison defect. None reproduce against
`src/pcae/core/phase_id.py`; `tests/test_phase_id.py`'s 62 dedicated
regression tests pass, and this phase's own independent adversarial
fixtures (above) found no additional instance of silent truncation.

## Determinism, security, packaging

Confirmed by direct repeated invocation and source inspection (not
trusted from 137R's claim): identical input yields identical
`PhaseId`/error output across repeated calls; no filesystem, network, or
governance access anywhere in `phase_id.py`; no module-level mutable
state. Packaging verification (editable install vs. clean checkout) was
not separately exercised in this phase beyond the existing test-suite
invocation, which runs against the editable install already in place;
no packaging-specific defect was found or expected given the module's
pure-stdlib (`re`, `dataclasses`, `typing`) dependency surface.

## Regression testing

- `python -m pytest -n auto` (full suite): 1851 passed, 1 skipped, 1
  failed — the failure
  (`TestPhase128B1NotificationDispatchReliabilityRepair::test_public_reconciliation_requires_report_marker_checkpoint_and_receipt`)
  independently confirmed present and identical on unmodified `main` via
  `git stash` before this phase's repair was applied; unrelated to
  Phase ID parsing.
- `tests/test_bootstrap_todo_consistency.py` (18 tests, including the
  live-repository `test_recommended_next_phase_matches_real_project_status`
  assertion): pass after repair.
- `pcae health`, `pcae check`, `pcae doctor task-memory`, `pcae push
  check`: clean after repair.
- Runtime confirmed unchanged throughout: Observed / observe /
  unavailable.

## Non-Goals (restated, honored)

This phase did not: redesign CPIPC-001 or Phase 137P's architecture,
migrate the disclosed-but-out-of-scope `phase_reports.py` residuals or
the four newly-found out-of-inventory files, resolve
`cltr/authority/identity.PhaseIdentity`'s deliberately-deferred
charset-reservation risk, or repair the minor error-taxonomy
misclassification noted above (none independently Blocking).

## Recommended Next Phase

**137T — Canonical Phase ID Parser Operational Hardening & Repository-Wide
Conformance**

Purpose: perform the repository-wide conformance sweep this
verification phase's findings motivate — migrate or explicitly contract-
revise the disclosed `phase_reports.py` residuals and the four newly-
found out-of-inventory consumers (`core/tasks.py`, `core/governance_timeline.py`,
`historical_builder.py`, `commands/session.py`), resolve
`cltr/authority/identity.PhaseIdentity`'s charset-reservation risk, and
correct the minor `missing_branch`/`invalid_syntax` error-taxonomy
misclassification, so CPIPC-001's parser-ownership guarantee
(CPIPC-REQ-018) holds without qualification across the entire codebase,
not only the ten-row §14 inventory as originally scoped.
