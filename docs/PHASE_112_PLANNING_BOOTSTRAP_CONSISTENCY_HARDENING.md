# Phase 112B.1 — Planning & Bootstrap Consistency Hardening

## Purpose

Repair `tasks/TODO.md`, which had presented a stale 90-series roadmap
as current work long after it was superseded, and harden `pcae session
bootstrap`'s orientation behavior so a stale planning artifact cannot
mislead a new session again — before starting 112C. Governance/
planning/bootstrap hygiene only: no Runtime Context implementation, no
runtime execution, no persistence implementation, and no file under
`src/pcae/core/` beyond the bootstrap orientation logic itself.

## Scope

- `tasks/TODO.md` — repaired: the 90-series table is relabeled
  historical and clearly marked as superseded; a new "Current Roadmap
  (112-series)" table reflects 112A/112B/112B.1 as complete, 112C as
  the confirmed next phase, and 112D/112E/113A as explicitly tentative
  candidates, not a committed queue.
- `src/pcae/core/context.py` — two additions to the compact bootstrap
  prompt (`build_bootstrap_prompt`, `build_context_pack`): an explicit
  `Recommended next phase: ...` line extracted from
  `PROJECT_STATUS.md`'s own inline sentence, and an explicit `Planning
  note: ...` line comparing `tasks/TODO.md`'s own "🔜 Next" marker
  against the current phase number, stating plainly which source is
  authoritative and why the other was ignored when they disagree. One
  new operational rule added to `CONTEXT_PACK_OPERATIONAL_RULES`
  stating this precedence directly.
- `docs/PHASE_112_PLANNING_BOOTSTRAP_CONSISTENCY_HARDENING.md` — this
  document.
- `tests/test_bootstrap_todo_consistency.py` — new regression coverage
  proving the precedence holds.

No `docs/ROADMAP.md` change (see Limitations — its own staleness is a
related, separate finding, out of this phase's scope to fully repair).

## 1. Stale Planning Artifact Finding

**What was actually stale, corrected.** The phase brief that opened
this work characterized the finding as "`pcae session bootstrap
--compact --profile implementation` reported that `tasks/TODO.md`
still shows an old 90-series roadmap and correctly treated it as
stale." Direct inspection of `src/pcae/core/context.py` and
`src/pcae/commands/session.py` (this phase's own investigation, before
any change) found that **`pcae session bootstrap` did not reference
`tasks/TODO.md` at all** — no code path read that file, compared it to
anything, or printed anything about it. The "stale TODO" observation
that preceded this phase was a human/agent-level inference made by
reading `tasks/TODO.md` directly and noticing it still listed 90C as
"🔜 Next" while `PROJECT_STATUS.md` recorded Phase 112A/112B as
current — a real and correct observation, but one the bootstrap tool
itself was not making. This distinction matters: fixing only
`tasks/TODO.md`'s content would have repaired the artifact but left
the tool blind to the exact same class of drift recurring in the
future. This phase repairs both — the artifact (§4) and the tool's own
blindness to it (§3) — rather than assuming the tool already handled
half the problem.

**A related, second-order finding.** `docs/ROADMAP.md` — the file
`tasks/TODO.md` itself points to as "the canonical roadmap" — has its
own "Current State" section still describing "90 phases" and "Current
phase: 90B complete" (dated "June 2026" in its own text), unchanged
since long before this arc's 107–112-series phases. Every phase from
110A through 112B evaluated `docs/ROADMAP.md` against its own content
and concluded "no change needed," reasoning that the roadmap's
standing *principles* (points 1–10, and the Long-Term Runtime Vision
section) still cover new work at a coarser grain — a conclusion this
phase does not dispute. But that evaluation never addressed the
concrete "Current State" phase-count table specifically, which is
exactly as stale as `tasks/TODO.md`'s table was. Repairing it fully is
out of this phase's scope (a 273-line document, and the brief scopes
this phase to `tasks/TODO.md` specifically) — named honestly here as a
limitation (§6), not silently left for a future session to
rediscover from scratch.

## 2. Source-of-Truth Precedence

Frozen, in order, for planning/orientation questions ("what phase are
we on," "what comes next," "what should I work on"):

1. **Active task contract** (`tasks/active/*.md`) — the most scoped,
   most current statement of what is actually being worked on right
   now; supersedes everything below it when one exists.
2. **The phase prompt given for the current session** — per the
   existing, unchanged operational rule ("Phase prompt is
   authoritative; it supersedes `PROJECT_STATUS.md` if they conflict").
3. **`PROJECT_STATUS.md`'s `## Current Phase` section** — the
   canonical record of the last completed phase and the recommended
   next phase, maintained every phase per `AGENTS.md`'s own standing
   instruction.
4. **Canonical roadmap docs** (`docs/ROADMAP.md`) — long-term product
   direction and standing principles; authoritative for *why* and
   *in what order class* of work happens, not for the specific current
   phase number (§1's finding: its own phase-count snapshot lags).
5. **`tasks/TODO.md`** — planning scratch space and candidate/tentative
   future work; informational only, never authoritative over (3) or
   (4) when they disagree.
6. **`tasks/DONE.md` historical record** — authoritative for *what has
   already happened*, never for what should happen next.
7. **Stale handoff snippets / old phase notes** — lowest precedence;
   useful color, never a instruction to act on without corroboration
   from (1)–(3).

This precedence was previously implicit (scattered across
`AGENTS.md`, `CONTEXT_PACK_OPERATIONAL_RULES`, and this session's own
practice) but not written down as a single ordered list anywhere. It is
frozen here as documentation only — no new enforcement mechanism is
introduced; `pcae check`/`pcae health` continue to operate exactly as
before.

## 3. Bootstrap Behavior

**Before this phase:** `pcae session bootstrap --compact` printed the
current phase (from `PROJECT_STATUS.md`, correctly prioritized over
any phase prompt/handoff text) but never explicitly stated the
*recommended next phase* as its own line, and said nothing about
`tasks/TODO.md` at all.

**After this phase**, two lines are added to the compact bootstrap
prompt, both derived entirely from files bootstrap already reads
(`PROJECT_STATUS.md`, `tasks/TODO.md`) — no new file is introduced as
an input:

- `Recommended next phase: <phase-id> — <title>` — extracted directly
  from `PROJECT_STATUS.md`'s own "Recommended next repo phase: ..."
  sentence (a real, consistently-formatted sentence present in every
  phase's `## Current Phase` section since 108D, verified directly
  against this file's own history rather than assumed).
- `Planning note: ...` — compares `tasks/TODO.md`'s own "🔜 Next"
  table row against the phase number in `PROJECT_STATUS.md`'s current
  phase line. When `tasks/TODO.md` names an older, already-superseded
  phase as next, the note states plainly: which source was selected as
  authoritative (`PROJECT_STATUS.md`), which was stale
  (`tasks/TODO.md`), and that the stale source was ignored. When the
  two already agree (the state after this phase's own `tasks/TODO.md`
  repair, §4), the note instead confirms consistency rather than
  staying silent — so an agent doesn't have to wonder whether the
  check ran at all.

A new operational rule was added to `CONTEXT_PACK_OPERATIONAL_RULES`
stating the same precedence directly: `"tasks/TODO.md is informational
planning notes only; it never outranks PROJECT_STATUS.md's current
phase or recommended next phase."` This rule is included in every
bootstrap's `Rules:` block going forward, exported context packs, and
continuity packs, since all three already flow the same
`CONTEXT_PACK_OPERATIONAL_RULES` tuple through unchanged code paths.

**What was not changed:** the non-compact `pcae session bootstrap
--agent-id <id>` path (`run_session_bootstrap`) already printed a
"Recommended next phase" line via the phase-report path (`latest_report
.get("recommended_next_phase")`) — that path needed no change. Only
the compact path (`build_bootstrap_prompt`), which every profile-based
bootstrap invocation in this session uses, was missing it.

## 4. Repaired Roadmap State

`tasks/TODO.md` now has a "Current Roadmap (112-series)" table listing
112A/112B/112B.1 as complete and 112C as the confirmed next phase
(matching `PROJECT_STATUS.md` exactly), with 112D/112E/113A explicitly
labeled tentative candidates rather than a committed queue — no phase
activation is inferred ahead of an explicit human decision, per
`tasks/DECISIONS.md`'s own standing rule on Phase Activation Governance.
The former 90-series table is preserved under a new "Historical:
Production v1 Path (90-series, superseded)" heading, every row
relabeled from a bare status word to an explicit "Historical — not
current" (or "✅ Complete", where that remained accurate on inspection)
so it can never again be read as an active roadmap. The "Future
Explorations" list's own pre-existing "Stale roadmap detection" item is
marked partially addressed, pointing back to this phase, rather than
silently left stale itself.

## 5. Validation

`pcae session bootstrap --compact --profile implementation` was run
after both the `tasks/TODO.md` repair and the bootstrap code change.
Confirmed:

- No obsolete 90-series roadmap is presented as current work anywhere
  in bootstrap output (bootstrap never read `tasks/TODO.md` before this
  phase, and does not surface its historical table now).
- `Recommended next phase: 112C — Runtime Context Prototype
  (Observation-Only)` prints explicitly.
- Once `tasks/TODO.md`'s own next-phase marker was updated to 112C
  (§4), the `Planning note:` line confirms consistency rather than
  flagging staleness — proving the mechanism responds to the real file
  content, not a hardcoded phase ID.
- Bootstrap still exits successfully in the idle/no-active-task state.

## 6. Limitations

- `docs/ROADMAP.md`'s own "Current State" section (§1) remains stale
  (still describes "90 phases," "June 2026," "90B complete") — a
  second, related but distinct planning-artifact staleness this phase
  does not repair, since the brief scopes this phase to
  `tasks/TODO.md` specifically and a full roadmap-document refresh is
  a substantially larger effort. Flagged here so a future phase does
  not have to rediscover it independently.
- The `Planning note:` comparison is a simple leading-integer
  comparison between `tasks/TODO.md`'s "🔜 Next" phase ID and
  `PROJECT_STATUS.md`'s current-phase ID — it does not understand
  letter-suffix phases (e.g. `112B.1` vs `112B`) beyond their shared
  leading integer, and does not detect staleness for a `tasks/TODO.md`
  that names a *future*, not-yet-reached phase incorrectly (only a
  *past*, already-superseded one). This is intentionally minimal —
  "do not overbuild" — and sufficient for the concrete finding this
  phase repairs.
- No enforcement, no automatic `tasks/TODO.md` rewriting, and no
  `pcae check`/`pcae health` gate change was introduced; the
  precedence (§2) and the new bootstrap lines (§3) are informational
  only, consistent with every other advisory surface in this codebase.

## No-Go Confirmations

No Runtime Context implementation. No runtime execution. No plugin
loading. No plugin invocation. No persistence implementation. No
database. No serialization. No shell mediation. No backend invocation.
No adapter invocation. No execution enablement. No Permission Broker
enforcement. No audit persistence. No rollback execution. No emergency
stop. No Telegram inbound. No REST endpoint. No web UI. No daemon. No
background worker. No automatic apply. `implementation_status` remains
unconditionally `"execution_unavailable"` on every Permission Broker
decision. Current maximum runtime state remains `Observed`. Current
maximum plugin capability remains `observe`. `v0.1.0-rc1` remains
non-executing by design. v0.2 remains the autonomy target (Level 3, not
Level 4/5). GitHub Release for `v0.1.0-rc1` and branch protection on
`main` are unchanged. No new tag. No new GitHub Release. No PyPI/
GitHub Packages publication.

## Recommended Next Phase

**112C — Runtime Context Prototype (Observation-Only).**
