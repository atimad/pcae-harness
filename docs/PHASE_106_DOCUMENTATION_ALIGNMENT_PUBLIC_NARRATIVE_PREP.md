# Phase 106J — v0.1 Documentation Alignment / Public Narrative Prep

> **Amendment (106J.1):** `docs/PUBLIC_NARRATIVE_BRIEF_V0_1.md`, created
> in this phase and referenced throughout this document, was removed in
> Phase 106J.1 as a documentation-hygiene repair — article-support source
> material does not belong in the tracked product/release doc set. See
> `docs/PHASE_106_PUBLIC_NARRATIVE_ARTIFACT_HYGIENE_REPAIR.md` for the
> full rationale and the durable facts that remain in the release docs.
> The rest of this document is preserved as an accurate historical record
> of what 106J did; links below to the removed brief are historical, not
> live.

## Purpose

Align the full PCAE v0.1 documentation set with the verified post-repair
state established by Phases 106G (audit), 106H (repair), and 106I
(end-to-end verification), so README, release docs, and golden-workflow
docs tell one consistent story — and prepare factual source material for
a later, external LinkedIn article, without writing that article in this
repository.

## Scope

Minimal, targeted edits to `README.md` and the existing v0.1 release doc
set (`RELEASE_SCOPE_V0_1.md`, `V0_1_GOLDEN_WORKFLOW.md`,
`RELEASE_HANDOFF_V0_1_RC1.md`, `RELEASE_NOTES_V0_1_DRAFT.md`,
`RELEASE_CANDIDATE_V0_1_CHECKLIST.md`); two new documents (this one, and
`docs/PUBLIC_NARRATIVE_BRIEF_V0_1.md`); new tests. No source-code changes
in this phase.

## Non-Goals

No runtime enforcement; no autonomous execution; no real backend
invocation; no adapter execution; no subprocess/shell execution beyond
existing lifecycle/test/docs-verification command behavior; no network
calls outside the existing Telegram outbound path and ordinary git remote
verification; no shell interception; no Telegram inbound/polling; no
remote shell; no `/run`; no automatic apply/apply execution/patch
parsing; no commit/push authorization changes beyond the existing
governed lifecycle; no real AI backend calls; no executable
artifact-only invocation path; no execution enablement flag or toggle;
no cryptographic signing; no remote attestation; no database-backed
audit storage; no shell mediation; no rollback execution, file mutation
rollback, or automatic restore; no git reset/checkout/revert execution;
**no new tag created**; no v0.2 implementation started; **no LinkedIn
article written or committed to this repository**.

## Current v0.1.0-rc1 State

| Check | Result |
|---|---|
| `v0.1.0-rc1` exists locally and on origin | yes (`b47ce1817a697eab6bee8ef158ba50d96e57c3bb`) |
| Final `v0.1.0` tag | does not exist |
| `origin/main..HEAD` | 0 |
| Working tree | clean |
| Fast-green | 4390/4390 fully green |
| `pcae doctor task-memory` | clean |
| `pcae push check` | clean |
| Trust-gate symmetry | verified (106H repair, 106I live-CLI re-verification) |
| Bootstrap/session reporting | verified (358/358, 106I) |

## Documentation Inventory

Public/release-facing docs reviewed in this phase: `README.md`,
`docs/RELEASE_SCOPE_V0_1.md`, `docs/V0_1_GOLDEN_WORKFLOW.md`,
`docs/RELEASE_HANDOFF_V0_1_RC1.md`, `docs/RELEASE_NOTES_V0_1_DRAFT.md`,
`docs/RELEASE_CANDIDATE_V0_1_CHECKLIST.md`, `docs/INSTALLATION.md`
(the "v0.1 notes" section), `docs/V0_1_CLEAN_SMOKE_TEST.md`. Phase-record
docs (`docs/PHASE_106_*.md`) were treated as source-of-truth history, not
edited except where explicitly noted.

## Alignment Methodology

1. Grepped every public/release doc for staleness markers (old test
   counts, old commit hashes, references to unresolved findings that
   have since been repaired).
2. Cross-checked each doc's claims against this session's own verified
   facts (106F tag creation, 106G finding, 106H repair, 106I live-CLI
   re-verification) rather than re-deriving them from scratch.
3. Ran `python -m pytest --collect-only -q` to get the actual current
   test count for `README.md`'s status line, replacing the stale
   hand-maintained figure.
4. Re-ran the existing doc-content test suites after every edit to catch
   any accidental break of an existing exact-string assertion.

## README Alignment Result

**Before:** `README.md` had zero mentions of `v0.1`, `v0.1.0-rc1`, or
"release candidate" anywhere, and its status line cited "7,278 tests
passing. 87 phases completed" — stale by roughly 5,600 tests.

**After:** Status line now states `v0.1.0-rc1` is tagged and pushed,
cites the current test count (12,900+; fast-green gate 4390/4390 fully
green), explicitly says v0.1 does not execute code/invoke a backend/
mediate a shell, and links `docs/RELEASE_SCOPE_V0_1.md`,
`docs/V0_1_GOLDEN_WORKFLOW.md`, and `docs/RELEASE_HANDOFF_V0_1_RC1.md`.
Added those three docs to the Resource table for discoverability.
`docs/ROADMAP.md`'s own staleness was judged lower-priority (internal
planning artifact, not release-facing) and left for a future phase.

## Release Scope Alignment Result

`docs/RELEASE_SCOPE_V0_1.md`'s "Known Limitations" and "Release
Blockers" sections referenced the README staleness and the (at-the-time
open) `task finish`/`phase complete` inconsistency as still-outstanding.
Both are now marked **Resolved**, with pointers to the phases that
resolved them (106J for README, 106H/106I for the trust-gate asymmetry).
The "Release Checklist" section's two remaining unchecked items
("README.md / ROADMAP.md brought current," "v0.1 tag/release notes
drafted") are now checked and expanded to record the full 106E–106J
sequence.

## Golden Workflow Alignment Result

`docs/V0_1_GOLDEN_WORKFLOW.md`'s `phase complete`-vs-`task finish`
clarity note (added in 106G) said the audit "recommends unifying them in
a future phase" — accurate at the time, stale now that 106H actually did
the unification of their *combination logic* and 106I verified it live.
Replaced with a "Trust-gate symmetry (106G/106H/106I)" paragraph stating
the current, verified behavior. The doc's trailing "Recommended Next
Phase" section still named 106E as "recommended next" (a leftover from
106C's original authoring) — replaced with a "Phase History" section
naming the actual phases that touched this document.

## Installation/Smoke Docs Alignment Result

`docs/INSTALLATION.md`'s "v0.1 notes" section and
`docs/V0_1_CLEAN_SMOKE_TEST.md` were reviewed and found already accurate
— no packaging/install behavior changed in 106G/106H/106I, so no edit was
needed.

## Release Handoff Alignment Result

`docs/RELEASE_HANDOFF_V0_1_RC1.md` had no mention of the post-tag
audit/repair/verify cycle at all (it predates 106G). Added a "Post-RC
Verification (106G–106I)" section summarizing the finding, repair, and
live-CLI re-verification, with the current post-cycle baseline numbers.
Updated "Known Limitations" to drop the now-resolved README item and
reflect the shared trust-gate combination logic from 106H.

## Release Notes Alignment Result

`docs/RELEASE_NOTES_V0_1_DRAFT.md` (still a draft, not published) had no
mention of the post-RC cycle. Added one highlight bullet describing the
audit-repair-verify cycle, and updated "Known Limitations" to match the
handoff doc's corrected wording.

## Post-RC Audit/Repair/Verification Alignment Result

`docs/PHASE_106_POST_RC_SYSTEM_INSPECTION_LIFECYCLE_CONNECTIVITY_AUDIT.md`,
`docs/PHASE_106_RC_AUDIT_FINDINGS_REPAIR.md`, and
`docs/PHASE_106_RC_END_TO_END_VERIFICATION_FULL_PHASE_CHECK.md` were
re-read in full and found internally consistent with each other and with
this phase's own summary — no edits needed; they are treated as the
authoritative historical record and linked from the release-facing docs
above rather than duplicated.

## Safety/No-Go Claim Review

Searched every edited document and the two new documents for any
language that could be read as claiming autonomous execution, runtime
enforcement, backend invocation, shell mediation, Telegram inbound, or
rollback execution as *already implemented*. None found — every mention
of these capabilities in the edited/created docs is explicitly framed as
"not implemented," "v0.2 target," or "does not exist." Verified
programmatically by this phase's own test suite
(`test_documentation_alignment_public_narrative_v0_1.py`).

## Command/Workflow Consistency Review

Confirmed all edited docs now agree on:
- Preferred v0.1 completion path: `pcae skill invoke phase-finalization
  <PHASE_ID>` → `pcae commit implementation` → `pcae task finish
  --commit` → `pcae push check` → `pcae push`.
- `pcae phase complete`'s role: available, not deprecated, used for the
  post-push corrected-re-dispatch case; shares the same hard-fail trust
  gate as `task finish --commit` since 106H.
- `pcae phase-report trust` / `pcae phase-report show --latest --trust`
  are verification/inspection commands, not part of the finalize/dispatch
  decision path.
- Partial reports are never treated as final trusted handoffs by any
  command.
- Telegram is outbound-only and report-trust aware everywhere it is
  mentioned.

## Public Narrative Facts

See `docs/PUBLIC_NARRATIVE_BRIEF_V0_1.md` for the full brief. In summary:
PCAE v0.1 is a governed, non-executing AI coding lifecycle harness;
`v0.1.0-rc1` is tagged and pushed; fast-green is 4390/4390; a real
post-release audit found and repaired a genuine bug (the trust-gate
asymmetry) and the fix was verified through the live CLI, not just unit
tests — a concrete, honest story of catching and fixing a real issue
before calling the release candidate done.

## Article Talking Points

"Making AI coding governable"; "from chat-driven coding to controlled
engineering lifecycle"; "why I built a governance harness before
enabling autonomy"; "the hard part is not making agents act, it is
making action accountable." Full detail and suggested tones in
`docs/PUBLIC_NARRATIVE_BRIEF_V0_1.md`.

## Article No-Claims / Avoid List

Do not claim PCAE is autonomous, executes code, safely controls shell
commands, is production-ready for autonomous agents, or replaces human
approval; do not overstate safety; do not imply v0.2 capabilities already
exist. Full list in `docs/PUBLIC_NARRATIVE_BRIEF_V0_1.md`.

## Remaining Documentation Risks

1. `docs/ROADMAP.md` remains stale (internal planning artifact, judged
   lower priority than `README.md`); a future phase should either update
   it or explicitly retire it in favor of `PROJECT_STATUS.md`/
   `CHANGELOG.md` as the source of truth for current state.
2. `docs/RELEASE_NOTES_V0_1_DRAFT.md` remains an unpublished draft — if
   the operator later publishes a GitHub Release, its content should be
   promoted at that time, not before.
3. No new risks were introduced by this phase's edits — all changes were
   additive corrections to already-accurate surrounding text, verified
   by re-running each affected doc's existing test suite.

## Recommended Next Phase

106K — v0.1 Public Article Drafting Support / Effectiveness Evaluation
Framework.
