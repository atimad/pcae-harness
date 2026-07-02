# PCAE v0.1 — Effectiveness Evaluation Framework

## Purpose

Define how to measure whether PCAE v0.1 actually helps AI-assisted
software engineering, as distinct from simply documenting what it does.
This framework is the evaluation methodology; it is not itself an
evaluation report — running it against real projects/tasks is future
work (see "Future Evaluation Phases"). It is written against the current
release candidate, `v0.1.0-rc1` — non-executing, governance/lifecycle
only. **PCAE is not autonomous**: every evaluation criterion below
assumes a human is driving the CLI throughout, and none of them measure
or assume any capability beyond that.

## Scope

A committed, product/release-relevant methodology document: evaluation
thesis, baseline/treatment definition, metrics, a 100-point scoring
rubric, sample evaluation tasks, a controlled-comparison method,
longitudinal real-project metrics, and an interpretation guide. This
document does not itself run an evaluation, collect data, or score any
specific project — it defines how a future phase would do that.

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
**no new tag created**; no v0.2 implementation started. This document
does not claim PCAE is autonomous, that runtime enforcement is
implemented, or that Telegram inbound exists — PCAE v0.1 remains a
**non-executing** governance/lifecycle harness, and is evaluated as one.

## Evaluation Thesis

**PCAE v0.1 should not be evaluated primarily by raw implementation
speed.** A human driving an AI agent directly, with no governance layer,
will often produce a first working version of a small task faster than
the same work routed through task contracts, commit governance, and
report-trust gates. That comparison, taken alone, makes PCAE look like
pure overhead.

The correct comparison is: **trusted completion per unit of human
supervision.** PCAE's value proposition is not "makes the AI faster." It
is "makes it possible for a human to supervise less closely and still
trust what 'done' means" — by making scope explicit, catching
incomplete/partial completion claims before they're treated as final,
producing a reviewable audit trail, and reporting outbound so the human
doesn't have to keep checking. Speed is a secondary metric; supervision
cost, trust, and continuity are primary.

## Baseline: AI Coding Without PCAE

An AI coding agent operating directly in a repository, with no task
contract, no report-trust gate, and no structured completion report:
the human gives instructions in natural language, the agent edits files
and runs commands directly, and "done" is whatever the agent says in its
final message. Completion trust depends entirely on the human
re-reading the diff and remembering the original ask. Nothing prevents
scope drift, nothing catches a report that's actually still partial, and
nothing survives a session boundary except what the human wrote down
themselves.

## Treatment: AI Coding With PCAE v0.1

The same AI agent, in the same repository, but every unit of work is
scoped in writing first (`pcae task new`), file/zone changes outside
that scope are flagged (`pcae check`/`pcae health`), completion is
routed through a structured report with a hard-fail trust gate
(`pcae task finish --commit` / `pcae phase complete`), and a human is
notified outbound with the full report attached (Telegram). PCAE
performs none of the actual code-writing, testing, or shell work itself
— it governs the process around it. This is the exact distinction the
evaluation is meant to surface: does governing the process produce
measurably better outcomes than not governing it, and at what cost?

## When PCAE Should Help

- Multi-phase, multi-session work where context would otherwise be lost
  between sessions.
- Work where "is this actually done?" is genuinely hard to answer by
  eye (large diffs, many files, subtle regressions).
- Work where a human is not watching every step and needs a trustworthy
  signal for when to look.
- Work where scope creep is a real risk (a task that could easily balloon
  into touching unrelated files).
- Release-adjacent work where hygiene (tests green, docs current, commits
  attributable) matters as much as the code itself.

## When PCAE Is Likely Overkill

- A single, short, one-off change with an obvious, easily-eyeballed
  diff (e.g. fixing one typo, bumping one version string).
- Pure exploration/prototyping where there is no real "done" to trust
  yet.
- A human who is already watching every single step in real time, where
  the reporting/notification layer adds nothing they don't already know.
- Extremely short sessions where the task-contract/report-trust overhead
  (creating a contract, writing a structured report) exceeds the work
  itself.

## Measurable Metrics

**Primary metric:** trusted completion per unit of human supervision —
operationalized as (number of phases the human could correctly consider
"safely done" without re-reading the full diff or session transcript) ÷
(minutes of active human attention required).

**Supporting metrics:**

- Scope control: out-of-scope file/zone changes flagged before commit,
  as a fraction of total changes.
- Report/handoff quality: fraction of completion reports that pass the
  trust gate on first attempt vs. require repair.
- Regression avoidance: regressions introduced per phase, and whether
  they were caught before or after being reported as "done."
- Release hygiene: fraction of phases with clean `push check` / task-memory
  / fast-green state at close.
- Auditability: fraction of "what happened in phase X?" questions
  answerable from committed artifacts alone, without asking the agent.
- Continuity: fraction of multi-session work where context was preserved
  correctly across a session boundary.
- Recovery: number of partial/stale completion claims caught and
  corrected before being treated as final.
- Governance overhead: time/interaction cost of the governed workflow
  itself (task setup, report writing, trust-gate repair cycles), measured
  separately from the underlying engineering work.

## Scoring Rubric (100 points)

| Dimension | Points | What it measures |
|---|---|---|
| Task correctness | 20 | Did the delivered work actually do what was asked? |
| Test/regression safety | 20 | Were regressions caught before being reported as done? |
| Scope control | 15 | Did work stay within its declared scope, or was drift caught? |
| Report/handoff quality | 15 | Was the completion report accurate, complete, and trustworthy on first read? |
| Commit/release hygiene | 10 | Clean, attributable commits; clean push/task-memory state at close? |
| Human supervision cost | 10 | How much active human attention was required to trust the outcome? |
| Time efficiency | 5 | Wall-clock/interaction cost relative to the work delivered. |
| Documentation quality | 5 | Were docs/status updated accurately alongside the change? |

Time efficiency and documentation quality are deliberately weighted
lowest (5 points each) — consistent with the evaluation thesis that raw
speed is not the primary success criterion, while correctness, safety,
scope, and trustworthy reporting (70 of 100 points combined) are.

### Optional Supplementary Metrics

- Number of partial reports caught (before being treated as final).
- Number of scope violations prevented.
- Number of stale docs/status issues caught.
- Number of repair phases required (e.g. 106H, 106J.1 in this project's
  own history).
- Average human interventions per phase.
- Time to trusted completion (not time to first draft).
- Number of "what happened?" reconstruction moments where the audit
  trail alone answered the question.
- Regression count.
- Release blocker count at RC/tag time.

## Sample Evaluation Tasks

A representative task set for a controlled comparison should include a
mix of task shapes, since PCAE's expected advantage varies by shape:

1. **Single-file bug fix** (small, low scope-drift risk) — tests whether
   PCAE overhead is noticeable when the baseline case is already easy.
2. **Multi-file feature addition** (moderate scope, several files) —
   tests scope control and report quality under realistic complexity.
3. **Multi-session refactor** (spans more than one sitting) — tests
   continuity across a session boundary, PCAE's strongest expected
   advantage.
4. **Release-preparation task** (docs/tests/tag hygiene, similar in
   shape to this project's own 106A–106J.1 phases) — tests release
   hygiene and auditability directly.
5. **Deliberately ambiguous/underspecified task** — tests whether scope
   control and report-trust gating catch premature "done" claims that a
   baseline run would likely accept at face value.

## Controlled Comparison Method

1. For each sample task, run it twice with the same underlying AI agent
   and model: once as the baseline (no PCAE), once as the treatment
   (full PCAE golden workflow).
2. Use the same task description, given to a human reviewer who does not
   watch the agent work in either run, only reviews the final result and
   whatever artifacts exist (a full transcript for baseline; the
   governed report/commit trail for treatment).
3. Score both runs independently against the 100-point rubric above,
   using only what the reviewer can actually observe from what each
   method produced (not by re-running the agent to find out what "really"
   happened) — this is the point: does PCAE's artifact trail make
   correct evaluation possible without doing that re-run?
4. Record supervision cost separately: how long did the reviewer need to
   spend, and how many follow-up questions did they need to ask the
   agent, to reach a scoring decision they were confident in?
5. Repeat across multiple task shapes (see sample tasks above) rather
   than relying on a single comparison — PCAE's advantage is expected to
   vary significantly by task shape.

## Longitudinal Real-Project Metrics

For an existing project with real phase history (such as this
repository's own 106A–106J.1 sequence), longitudinal metrics can be
computed directly from committed artifacts without a controlled
experiment:

- Repair-phase ratio: number of dedicated repair/hygiene phases (e.g.
  106H, 106J.1) ÷ total phases in a release cycle.
- Trust-gate catch rate: number of times a report-trust gate correctly
  blocked or flagged an incomplete/stale report (e.g. the 106E metadata-
  timing mistake, corrected the same phase) ÷ total finalize attempts.
- Fast-green stability: fraction of phases where the fast-green gate
  remained fully green at phase close, and time-to-fix when it wasn't
  (e.g. 106B's triage of 3 pre-existing failures).
- Documentation drift interval: how many phases elapsed between a doc
  becoming stale (e.g. README's test count) and it being caught/fixed.
- Notification reliability: fraction of phase completions that produced
  a correctly-attributed outbound report on the first attempt, vs.
  requiring a corrected re-dispatch.

These are retrospective, not predictive — they describe how well the
governed process performed on the project that built PCAE itself, which
is informative but not a substitute for the controlled comparison above
run on other projects.

## Expected Advantages

- Continuity across sessions and phases — a governed task contract and
  report survive a context reset in a way an ungoverned chat transcript
  does not.
- Auditability — "what happened in phase X" is answerable from committed
  artifacts (`.pcae/phase-reports/`, `PROJECT_STATUS.md`, `CHANGELOG.md`)
  without needing to ask the agent or re-read a full transcript.
- Scope control — out-of-scope changes are flagged mechanically, not
  left to human vigilance alone.
- Catching stale/partial completion claims — the report-trust hard-fail
  gate exists specifically to prevent "done" from being accepted before
  it's actually true.
- Release hygiene — fast-green, task-memory, and push-check gates create
  a consistent bar for what "ready" means.

## Expected Disadvantages / Overhead

- Process overhead on short, simple tasks — creating a task contract and
  a structured report is real cost that doesn't pay for itself on a
  one-line fix.
- Learning curve — the golden workflow (`task new` → `commit
  implementation` → `task finish --commit` → `push`) has to be learned
  and followed correctly, unlike ad hoc direct editing.
- Repair-phase cost — governance systems can themselves have bugs (this
  project's own 106H/106J.1 are direct examples); repairing them is real
  overhead, even though catching and fixing them is also evidence the
  system works as designed.
- Does not improve code quality directly — PCAE attests to *process*
  completeness (scope, tests reported, trust fields present), not to
  whether the underlying code is well-written or secure.

## Interpretation Guide

- A high score on task correctness/test safety with a low score on
  scope control or report quality suggests the *engineering* was fine
  but the *governance process* wasn't followed rigorously — a training/
  discipline gap, not a PCAE design flaw.
- A high supervision-cost score in the treatment run that isn't offset
  by continuity/auditability gains suggests the task was a poor fit for
  governed workflow (see "When PCAE Is Likely Overkill").
- A treatment run that scores lower than baseline on time efficiency but
  higher on trusted-completion-per-supervision-minute is the expected,
  intended outcome — that trade is the thesis being tested, not a
  failure.
- Repeated repair-phase cycles (like 106H, 106J.1) are not disqualifying
  on their own — the relevant question is whether they were caught by
  the governance system itself (a working immune response) or by
  external accident.

## Release Relevance

This framework is release-relevant because it gives future maintainers
and evaluators a concrete, falsifiable way to ask "is this actually
worth the overhead?" rather than relying on the project's own
self-description. It is committed to `docs/` (not
`.pcae-local/`) because it is methodology, not article-support scratch
material — the same distinction Phase 106J.1 established when removing
`docs/PUBLIC_NARRATIVE_BRIEF_V0_1.md`.

## Future Evaluation Phases

This document defines the methodology only. Future phases could:

1. Run the controlled comparison (see "Controlled Comparison Method")
   against real task shapes and publish scored results.
2. Compute the longitudinal metrics above against this project's own
   full phase history as a worked example.
3. Extend the rubric based on what the first real evaluation run
   reveals is missing or miscalibrated.

None of this is performed in Phase 106K — this document is the
methodology, not the evaluation report.
