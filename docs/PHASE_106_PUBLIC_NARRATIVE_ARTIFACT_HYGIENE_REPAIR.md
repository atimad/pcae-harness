# Phase 106J.1 — Public Narrative Artifact Hygiene Repair

## Purpose

Remove a documentation-hygiene mistake from Phase 106J: a public
narrative brief intended as source material for a future external
LinkedIn article was committed as tracked repository documentation. It
is useful for article drafting, but it is not product/release
documentation a repo user needs, and it does not belong in the same
tracked-doc set as `README.md` or `docs/RELEASE_SCOPE_V0_1.md`. This
phase removes it, establishes an explicitly-ignored local workspace for
this kind of working material going forward, and updates the tests/docs
that referenced it.

## Scope

Delete `docs/PUBLIC_NARRATIVE_BRIEF_V0_1.md`; add `.pcae-local/` to
`.gitignore`; add a small amendment note to
`docs/PHASE_106_DOCUMENTATION_ALIGNMENT_PUBLIC_NARRATIVE_PREP.md`
(historical record preserved, not rewritten); replace the
brief-dependent tests in
`tests/test_documentation_alignment_public_narrative_v0_1.py` with
tests that check the alignment *document* rather than the removed
brief; add a new dedicated hygiene test file. No source-code changes.

## Non-Goals

No runtime enforcement; no autonomous execution; no real backend
invocation; no adapter execution; no subprocess/shell execution beyond
existing lifecycle/test/docs-verification command behavior; no network
calls outside the existing Telegram outbound path and ordinary git
remote verification; no shell interception; no Telegram inbound/polling;
no remote shell; no `/run`; no automatic apply/apply execution/patch
parsing; no commit/push authorization changes beyond the existing
governed lifecycle; no real AI backend calls; no executable
artifact-only invocation path; no execution enablement flag or toggle;
no cryptographic signing; no remote attestation; no database-backed
audit storage; no shell mediation; no rollback execution, file mutation
rollback, or automatic restore; no git reset/checkout/revert execution;
**no new tag created**; **the LinkedIn article itself is not written or
committed in this phase** (nor was it in 106J — this phase repairs where
its *source material* lived, not whether it existed).

## Why Public Narrative Artifacts Do Not Belong in Tracked Product Docs

`README.md`, `docs/RELEASE_SCOPE_V0_1.md`,
`docs/V0_1_GOLDEN_WORKFLOW.md`, `docs/RELEASE_HANDOFF_V0_1_RC1.md`, and
`docs/RELEASE_NOTES_V0_1_DRAFT.md` exist to answer a repo user's
question: *what is this project, how do I use it, and what state is the
release candidate in?* A public narrative brief answers a different
question — *what should I say about this project on LinkedIn, and in
what tone?* — aimed at the maintainer preparing external content, not at
someone cloning the repo to use PCAE. Mixing the two in the same tracked
doc set:

- Adds noise to the product documentation a repo user actually needs.
- Implicitly signals that marketing/narrative framing is part of the
  project's committed artifact set, which it should not be.
- Creates a maintenance burden — every time release facts change, both
  the release docs *and* the narrative brief need updating, doubling the
  drift surface (this already happened once: 106J's own brief already
  needed the same "trust-gate symmetry verified" fact the release docs
  needed, duplicated in two places).

The durable, product-relevant *facts* the brief cited (v0.1.0-rc1
tagged, fast-green 4390/4390, non-executing by design, v0.2 is the
autonomy target) already live in the release docs independently of the
brief — removing the brief loses no fact a repo user needs.

## What Was Removed

- `docs/PUBLIC_NARRATIVE_BRIEF_V0_1.md` — deleted in this phase. Its
  content (project summary, problem statement, article angles/tones,
  citable facts, no-claims/avoid list) was article-support scratch
  material, not durable product documentation, per the operator's
  explicit hygiene decision for this phase.

No other files matched LinkedIn/article/draft/talking-points naming
conventions in the tracked doc set — this was the only artifact of its
kind.

## What Durable Facts Remain in Release Docs

Every fact the removed brief cited already exists, independently, in the
durable release docs it drew from:

| Fact | Still documented in |
|---|---|
| `v0.1.0-rc1` tagged and pushed | `docs/RELEASE_HANDOFF_V0_1_RC1.md`, `README.md` |
| Fast-green 4390/4390 fully green | `README.md`, `docs/RELEASE_HANDOFF_V0_1_RC1.md`, `docs/RELEASE_SCOPE_V0_1.md` |
| Non-executing by design | `README.md`, `docs/RELEASE_SCOPE_V0_1.md`, `docs/RELEASE_HANDOFF_V0_1_RC1.md` |
| v0.2 is the autonomy target | `README.md`, `docs/RELEASE_SCOPE_V0_1.md`, `docs/RELEASE_HANDOFF_V0_1_RC1.md` |
| Report-trust hard-fail gates | `docs/RELEASE_SCOPE_V0_1.md`, `docs/V0_1_GOLDEN_WORKFLOW.md` |
| Golden workflow, preferred completion path | `docs/V0_1_GOLDEN_WORKFLOW.md` |
| Telegram outbound-only | `docs/RELEASE_SCOPE_V0_1.md`, `docs/V0_1_GOLDEN_WORKFLOW.md` |
| Post-RC audit-repair-verify cycle (106G–106I) | `docs/RELEASE_HANDOFF_V0_1_RC1.md`, `docs/RELEASE_NOTES_V0_1_DRAFT.md` |

Article-specific framing (suggested angles, tone options, an "avoid
list" phrased for a marketing audience) was **not** migrated anywhere —
it has no home in durable product docs, by design.

## Ignored Local Workspace Convention

`.pcae-local/` is now listed in `.gitignore`. It is never committed; no
files were created inside it in this phase (verified: `git status
--ignored` shows `.pcae-local/` itself ignored, and the directory does
not exist in the tracked tree). Intended structure for future
article-support work:

```
.pcae-local/article-drafts/       # LinkedIn article drafts, any revision
.pcae-local/public-narrative/     # brief-style source material, if regenerated
.pcae-local/evaluation-notes/     # informal effectiveness-evaluation notes
```

This is a convention, not enforced tooling — no code path in PCAE reads,
writes, or depends on `.pcae-local/`'s contents or structure.

## How Future Article-Support Phases Should Handle Drafts

1. Any regenerated public-narrative source material should be written
   under `.pcae-local/public-narrative/`, not `docs/`.
2. Any LinkedIn article draft should be written under
   `.pcae-local/article-drafts/`, not `docs/`, and never committed via a
   governed commit command.
3. A committed **effectiveness evaluation framework** (if built in 106K)
   is a different kind of artifact — it evaluates whether PCAE's
   governance claims hold up, which *is* product/release-relevant — and
   may be committed to `docs/` if it documents durable, factual
   evaluation criteria rather than article framing.
4. If a future phase needs to re-derive narrative facts, it should pull
   them from the durable release docs (the table above), not recreate a
   second copy of them in a new tracked brief.

## Release Impact

None negative. This phase removes a documentation-hygiene artifact that
was never referenced by any product/release doc a repo user depends on
(confirmed: no `README.md` or release-doc link pointed to the removed
file). `v0.1.0-rc1`'s tag, artifacts, and all prior phase findings are
unaffected.

## Recommended Next Phase

106K — v0.1 Effectiveness Evaluation Framework / External Article Source
Packet. An evaluation framework may be committed if it is
product/release-relevant; any article source packet must be generated
under `.pcae-local/` or external storage; the article itself must not be
committed; the final LinkedIn rewrite happens outside the repo/chat
workflow after this project has prepared factual material.
