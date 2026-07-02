# PCAE v0.1 — Public Narrative Brief

This is **source material**, not the article. It exists so a later
LinkedIn article (drafted outside this repository) can be written from
verified facts instead of memory or aspiration. Nothing in this document
is a commitment to publish; it is a factual brief for whoever drafts that
article next (Phase 106K).

## One-Paragraph Project Summary

PCAE (Persistent Constrained Agentic Engineering Harness) is a governed,
**non-executing** lifecycle harness for AI-assisted software engineering.
It tracks task scope, validates whether a phase's completion report can
be trusted before treating it as final, and reports outbound to a human
via Telegram — without ever executing code, invoking a real AI backend,
or mediating a shell on an agent's behalf. `v0.1.0-rc1` is tagged and
pushed, fast-green tested (4390/4390), and has been through a dedicated
post-release audit, repair, and re-verification cycle.

## Why PCAE Exists

Long AI-assisted coding sessions accumulate risk that isn't about the AI
"going rogue" — it's about ordinary process failure at scale: an agent
loses context across a long session, a phase gets marked "done" before
its report is actually trustworthy, a human isn't told when something
finished, or two people's understanding of what's in scope silently
diverge. None of that requires malice or a runaway agent; it just
requires enough steps and enough time. PCAE was built to make that
process *governable* — auditable, scoped, and honestly reported — before
attempting to make the AI's actions themselves more autonomous.

## Problem Statement

- AI coding can be powerful but hard to govern across long-running work.
- Agents can drift from the original task, lose context, produce weak or
  incomplete handoffs, or claim a phase is "done" before the evidence
  supports that.
- Without a scope contract, nothing stops an agent from touching files
  outside what was actually asked.
- Without a trust gate on completion reports, "done" can mean anything —
  including work that's actually still partial.
- Without outbound reporting, a human may not learn a long session
  finished (or stalled) until they happen to check.

## What v0.1 Achieved

- **Governed task/phase lifecycle** — every unit of work is scoped in
  writing (`pcae task new`) before it starts; `pcae check`/`pcae health`
  flag out-of-scope changes.
- **Task/phase discipline** — a real state machine (task new → work →
  governed commit → task finish), not an informal convention.
- **Report-trust hard-fail gates** — a phase-completion report can be
  rejected as incomplete/untrustworthy before it's treated as final;
  Telegram is never sent for a partial report.
- **A documented, command-verified golden workflow** — the exact sequence
  an operator runs, smoke-tested against a genuinely fresh clone.
- **Telegram outbound reports** — a human is notified when a phase
  completes, with the full report attached, entirely outbound.
- **A tagged release candidate** — `v0.1.0-rc1`, created and pushed after
  an explicit, gated readiness review.
- **Clean, fully-green tests** — fast-green 4390/4390, with zero known
  failures.
- **Packaging/install smoke validation** — editable install, non-editable
  install, and built sdist/wheel all verified in throwaway environments.
- **A real post-release audit-repair-verify cycle** — after tagging, a
  dedicated audit (106G) found a genuine bug (two completion commands
  disagreeing about whether a report was trustworthy enough to send), it
  was fixed with a shared helper (106H), and the fix was re-verified
  through the live CLI, not just unit tests (106I).

## What v0.1 Intentionally Does Not Do

- **No autonomous execution** — no code path runs agent-authored code or
  shell commands without a human driving the CLI.
- **No runtime enforcement** — the permission-broker/shell-gate layers
  remain evidence-only classification prototypes; nothing is enforced at
  runtime yet.
- **No backend invocation** — no code path calls a real AI backend API.
- **No shell mediation** — PCAE does not intercept or mediate arbitrary
  shell commands.
- **No Telegram inbound** — outbound notification only; there is no
  inbound handler or remote-command path anywhere in the codebase.

## Honest Positioning

- This is a **work-in-progress governance harness**, not a finished
  product.
- `v0.1.0-rc1` is a **release candidate for non-executing lifecycle
  governance** — it governs the process around AI-assisted coding, not
  the AI's actions themselves.
- It is **not** a finished autonomous coding platform, and it does not
  claim to be one anywhere in its own documentation.
- Governed autonomy (real backend invocation, enforced runtime gates) is
  the explicit **v0.2** target — not built yet, not claimed as built.

## Suggested Article Angles

1. "Making AI coding governable" — framing PCAE as a governance layer,
   not an execution layer.
2. "From chat-driven coding to controlled engineering lifecycle" —
   contrasting ad hoc AI-assisted coding with a scoped, reported,
   trust-gated process.
3. "Why I built a governance harness before enabling autonomy" — the
   deliberate v0.1-before-v0.2 sequencing.
4. "The hard part is not making agents act; it is making action
   accountable" — the throughline of the whole project: scope, trust,
   and reporting come before capability.

## Suggested Article Tone Options

- **Technical engineering note** — architecture, the report-trust gate,
  the audit-repair-verify cycle as a case study in catching your own
  bugs.
- **Founder/build-in-public reflection** — why this project exists, what
  was learned building it, what's next.
- **Governance/safety-focused post** — the case for governing process
  before granting capability, using PCAE as a concrete example.
- **Practical lessons learned** — what actually broke (the trust-gate
  asymmetry), how it was found, how it was fixed and verified.

## Facts That Can Be Cited

- `v0.1.0-rc1` was tagged (`git tag -a v0.1.0-rc1`) and pushed to origin
  in Phase 106F.
- Fast-green test gate: **4390/4390 passing**, fully green, zero known
  failures.
- Release/lifecycle regression suites: green across every checked phase
  (e.g. 421/421, 1497/1497, 77/77 depending on the specific suite/phase).
- `python -m build` (sdist + wheel) succeeded; the built wheel
  smoke-installed cleanly in a fresh virtual environment.
- A post-release-candidate audit (106G) found a real, empirically
  reproducible trust-gate asymmetry between two completion commands.
- That finding was repaired (106H) and independently re-verified via the
  live CLI in an isolated scratch environment, not only unit tests
  (106I) — both commands were shown to produce matching blocker text for
  the same incomplete report.
- Bootstrap/session reporting (`pcae session bootstrap`) was verified as
  part of the same post-release cycle (358/358 passing).

## No-Claims / Avoid List

When drafting the article (Phase 106K or later), do **not**:

- Say PCAE is autonomous.
- Say PCAE executes code.
- Say PCAE safely controls shell commands.
- Say PCAE is production-ready for autonomous agents.
- Say PCAE replaces human approval.
- Overstate safety — "governed" and "audited" are accurate; "safe" or
  "guaranteed correct" are not claims this project makes about the code
  an agent writes. PCAE attests to *process* completeness (scope, tests
  reported, trust fields present), not to code quality or security.
- Imply v0.2 capabilities already exist. v0.2 (real backend invocation,
  runtime enforcement) is a stated future target, not shipped work.
