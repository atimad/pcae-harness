# PCAE Repository Transition Validator — Architecture

**Status:** Architecture / design only. No implementation exists yet.
**Origin:** Phase 113S, formalizing a principle exposed by the 113X
cross-agent governance incident (a different implementing agent,
Claude-DeepSeek, produced a canonical phase report — accepted at face
value by the tooling of the time — whose commits and test results were
stale, carried over from an earlier phase, and whose emptied
`recommended_next_phase` field the finalization gate did not catch
before `pcae push check` was asked directly).

## 0. Core Principle

> PCAE does not trust the intelligence of the agent.
> PCAE trusts only repository state that satisfies continuously
> verified engineering invariants.

Restated as a three-step discipline:

1. **Model proposes.** Any agent — human or AI, any vendor, any
   capability level — may propose a repository transition.
2. **PCAE validates.** A single, deterministic, model-agnostic
   validator evaluates the proposal against repository state and a
   fixed set of invariants.
3. **Repository advances only through valid state transitions.** No
   transition may become canonical (visible to `latest.json`/`latest.md`,
   pushed, or notified) unless the validator accepts it.

This is not a new capability layer. It is the formalization, as a named
architectural component, of a discipline PCAE's finalization gate and
`pcae push check` have partially enforced piecemeal since Phase 92B —
made explicit, complete, and independent of any particular agent's
diligence.

## 1. Repository State

PCAE considers "repository state" to be the union of the following,
each independently observable and independently verifiable — never
inferred from another:

| State component | Source of truth |
|---|---|
| Git state | `git log`, `git status`, `git rev-list` |
| Working tree | `git status --short`, `git diff` |
| Active task | `tasks/active/*.md` (task contract) |
| Phase identity | `resolve_canonical_phase_identity()` (113X.4): active task contract > phase-completion metadata > active lifecycle context > explicit CLI argument |
| Project status | `PROJECT_STATUS.md` (`## Current Phase`, `## Phase X Complete` sections) |
| Phase reports | `.pcae/phase-reports/latest.{md,json}`, `.pcae/phase-reports/quarantine/*` |
| Phase-completion metadata | `.pcae/phase-completion-metadata.json` |
| Architecture status | `build_architecture_status()` output (113X.5): `completed`, `completed_phase_ids`, `in_progress`, `planned` |
| Test results | Structured `test_results` dict plus live pytest re-runs |
| Governance checks | `pcae health`, `pcae check`, `pcae doctor task-memory` |
| Notification state | `.pcae/phase-reports/.last-notified.json`, `notification_result` |
| Push state | `origin/main..HEAD`, `pcae push check` |
| Runtime state | `pcae runtime inspect` (`Observed`/execution capability) |
| Execution availability | Permission Broker status (`execution_unavailable`) |

Each component has exactly one authoritative reader. No component is
ever derived by parsing another component's free text (this is the
113X.4 lesson generalized: phase identity was the first field repaired
this way; the validator generalizes the same discipline to every field
above).

## 2. Proposed Transition

A **proposed transition** is a request, made by any agent, to move
repository state from one point to another. PCAE recognizes (at
minimum) these transition kinds:

- `start_task` — create `tasks/active/*.md`
- `modify_files` — change working-tree content within task scope
- `run_validation` — execute test/governance commands
- `commit` — create a git commit
- `finish_task` — move task to `tasks/done/`, update `tasks/DONE.md`
- `complete_phase` — write/attempt a canonical phase report
- `push` — advance `origin/main`
- `notify` — dispatch an external notification (Telegram, etc.)
- `update_status` — edit `PROJECT_STATUS.md` / roadmap material
- `produce_report` — any artifact claiming to represent phase outcome

The proposing agent **never** has the authority to make its own
proposal canonical. It can only submit a transition (current state →
target state) for validation. This is symmetric with how `pcae phase
complete` already works today (it writes a *trial* report and asks
`validate_finalization_gate()` before anything is promoted) — the
validator generalizes this pattern to every transition kind above, not
just phase completion.

## 3. Transition Validator

```
validate_transition(
    current_state:   RepositoryState,
    proposed:        ProposedTransition,
    target_state:    RepositoryState,
    invariants:      InvariantSet,
) -> TransitionVerdict
```

`TransitionVerdict` is exactly one of:

- `ACCEPT` — the transition may become canonical.
- `REJECT` — the transition is refused; no canonical state changes.
- `QUARANTINE` — an artifact is retained for inspection but never
  promoted to `latest`/canonical.
- `REQUIRES_HUMAN_REVIEW` — the transition cannot proceed without
  explicit human approval.

The validator is a pure function of its four inputs. It does not
consult the proposing agent's identity, self-reported confidence, or
free-text narrative. This is what makes it model-agnostic (§9) and
what closes the exact gap 113X exposed: a report's own prose said the
right thing ("2 pre-existing failures unrelated") while its structured
fields said something else (all green) — a validator that reads
structure, never prose, cannot be fooled by prose being more honest (or
less) than data.

## 4. Invariants

The validator evaluates the following invariants (at minimum) on every
transition. Each invariant is boolean-decidable from repository state
alone — never from agent self-report:

1. **Phase identity consistency** — the proposed transition's phase_id
   agrees with every other source that can independently derive one
   (active task contract, metadata, lifecycle context); disagreement is
   never advisory.
2. **Active task consistency** — a transition that requires an active
   task (e.g. `finish_task`) has one; a transition that requires task
   absence (e.g. starting a new one) doesn't collide with an existing
   one.
3. **Allowed file scope** — every file touched by the transition
   matches the active task's declared allowed-files/allowed-zones.
4. **Commit lineage** — commits attributed to a transition are real,
   reachable, and their messages do not reference a *different* phase
   than the one being finalized (the 113D defect this generalizes: a
   report's `commits` field must be verified against `git log`, not
   merely copied from wherever a metadata file last held them).
5. **Report completeness** — all required structured fields
   (`files_changed`, `tests_run`/`test_results`, `commits`,
   `pushed_status`, `recommended_next_phase`, etc.) are present and
   non-empty.
6. **Report trust** — the report passes both the current and legacy
   trust gates (`validate_phase_report_trust`, `validate_finalization_gate`)
   without requiring `--allow-partial-report`.
7. **Metadata consistency** — `.pcae/phase-completion-metadata.json`
   was actually rewritten for *this* transition, not inherited unedited
   from a prior one (the root cause of the 113D defect: identity
   resolved correctly from the active task contract while commits and
   test_results silently rode along on stale metadata).
8. **Architecture status consistency** — `completed`/`in_progress`/
   `planned` remain independently derived and mutually exclusive; no
   phase appears in two incompatible categories.
9. **Recommended-next-phase consistency** — the structured
   `recommended_next_phase` field, the free-text summary, and
   Architecture Status's `planned` entry all agree.
10. **Test result consistency** — structured `test_results` values are
    not contradicted by the report's own summary prose, and were
    produced by an actual test run in this transition's window (not
    carried over from an earlier one).
11. **Push state consistency** — `pushed_status` and
    `origin_main_head_count` reflect the real, current
    `git rev-list --left-right --count origin/main...HEAD`.
12. **Notification eligibility** — see §7.
13. **Single final notification** — at most one canonical "phase
    complete" notification is ever dispatched per phase (closing the
    idempotency-guard asymmetry documented, but not fixed, in 113XR:
    `pcae task finish --commit`'s path has a
    `.last-notified.json` guard; `pcae phase complete`'s does not).
14. **No execution availability unless explicitly enabled by future
    contract** — every transition is evaluated under the standing
    assumption that `execution_availability == "unavailable"`; a
    transition that would change this must fail closed until an
    explicit, separately-frozen execution-enablement contract exists.
15. **No canonical artifact promotion when blocked** — if any invariant
    above fails, `latest.json`/`latest.md` are never written or
    overwritten (quarantine or rejection only — see §6).

This list is deliberately extensible: the invariant set is versioned
data, not code baked into one function, so a future phase can add an
invariant without redesigning the validator's shape.

## 5. Accept / Reject / Quarantine / Human-Review Semantics

- **Accept** — the transition satisfies every invariant. The target
  state may become canonical: `latest.json`/`latest.md` may be written,
  the commit may land, the push may proceed, notification may be
  considered (subject to §7).
- **Reject** — one or more invariants fail in a way that makes the
  transition invalid on its face (e.g. files touched outside task
  scope, phase identity conflict). No canonical state changes at all —
  not even a quarantined artifact. The proposing agent must revise the
  proposal and resubmit.
- **Quarantine** — the transition produced a real artifact (e.g. a
  phase report) that is structurally complete enough to retain for
  inspection, but fails one or more trust/completeness invariants. The
  artifact is written to a quarantine location (mirroring the existing
  `.pcae/phase-reports/quarantine/*.blocked.{md,json}` convention) and
  is never promoted to `latest`. A human or a corrected resubmission
  can later review it.
- **Requires human review** — the transition cannot be mechanically
  resolved as accept or reject (e.g. an invariant is ambiguous, or the
  transition kind is one PCAE has flagged as always requiring a human,
  such as any future execution-enablement transition). The transition
  is held pending explicit approval; no canonical state changes until
  approval is recorded.

These four outcomes are exhaustive and mutually exclusive for any given
transition.

## 6. Canonical Artifact Promotion

Artifacts move through a fixed set of states. Promotion is one-directional
and gated:

1. **Draft** — an in-progress artifact under construction by the
   proposing agent; not yet submitted to the validator.
2. **Blocked** — submitted, evaluated, and rejected outright (§5
   Reject). Not retained as a distinguishable artifact beyond the
   validator's own rejection reasons.
3. **Quarantined** — submitted, evaluated, and quarantined (§5
   Quarantine). Retained on disk (mirroring
   `.pcae/phase-reports/quarantine/`) for inspection, never overwrites
   `latest`.
4. **Certified** — submitted, evaluated, and accepted (§5 Accept). The
   artifact has passed every invariant and is eligible for promotion.
5. **Canonical / latest** — the certified artifact has been promoted:
   it is now `latest.json`/`latest.md` (or the equivalent canonical
   location for the transition kind in question).

**Only certified artifacts may become canonical.** A draft, blocked, or
quarantined artifact can never become `latest` through any path. This
is already true today for phase reports specifically (`finalize_phase_report()`'s
`gate` parameter routes to `write_quarantined_report()` instead of
`write_phase_report()`); the validator generalizes the same discipline
to every artifact kind the transition model covers, not phase reports
alone.

## 7. Notification Eligibility

Telegram, or any future notification transport, may dispatch a
"phase complete" notification only when **all** of the following hold
simultaneously:

- The phase is finalized (an Accept verdict was reached).
- The canonical report is Certified (§6) — not draft, blocked, or
  quarantined.
- Push state is clean (`origin/main..HEAD == 0` for the relevant
  commits).
- No notification has already been dispatched for this phase
  (single-final-notification invariant, §4.13).
- The transport itself is configured and enabled
  (`PCAE_NOTIFY_ENABLED=1`, sink credentials present).

**Intermediate reports must never be externally dispatched.** A
quarantined or blocked report may still generate an internal signal
(the existing partial-warning notification model from 113X.3 — "PHASE
FINALIZED BUT REPORT PARTIAL", distinctly titled and severity-flagged)
but never the normal "Phase COMPLETED" event, and never for a report
that hasn't reached at least Certified state.

## 8. Semantic vs. Structural Boundary

This is the line the validator exists to enforce, restated as a table:

| Models own (semantic) | PCAE owns (structural) |
|---|---|
| Code design | Identity |
| Implementation strategy | Lifecycle |
| Explanations | Scope |
| Remediation suggestions | Reports |
| Prose narrative / summaries | Commits |
| Judgment calls about *what* to build | Pushes |
| | Notifications |
| | Canonical state |

A model may write an excellent summary, a correct implementation, and a
well-reasoned remediation — and PCAE will still reject, quarantine, or
require human review of the transition if the *structural* facts
(identity, scope, commit lineage, report completeness, trust) don't
independently check out. Conversely, a model's summary being wrong,
incomplete, or even self-contradictory does not by itself invalidate a
transition if every structural invariant independently holds — but in
practice a wrong summary is usually a symptom of a structural problem,
which is exactly why 113D's stale `test_results` (a structural defect)
happened to coexist with prose that had partially self-corrected (a
semantic detail) without ever fixing the structural problem itself.

## 9. Model-Agnostic Behavior

The validator's four inputs (current state, proposed transition, target
state, invariants) contain no field for "which model proposed this."
The same invariant set applies identically whether the proposing agent
is Claude, Claude-DeepSeek, Codex, Qwen, a human operator, or any future
model. This is not a policy preference — it is a structural property of
the validator's signature: there is nowhere in `validate_transition()`'s
inputs to plumb an agent identity through to a different outcome.

This closes the actual lesson of 113X: the problem was never "Claude-
DeepSeek is untrustworthy specifically." The problem was that no
model's output was being verified against repository ground truth
before being promoted. A model-agnostic validator makes "which model do
we trust more" the wrong question to ask — the right question is
"did this specific proposed transition pass every invariant," which has
the same answer regardless of authorship.

## 10. Future Integration

This architecture is designed to integrate with, without requiring
redesign of, the following existing and future subsystems:

- **Task lifecycle** (`pcae task new/update/finish`) — `start_task`,
  `modify_files`, `finish_task` transitions route through the validator
  in place of today's `check_task_zone_scope()`/`check_task_file_scope()`
  ad hoc checks, which become one invariant family among many.
- **Phase lifecycle** (`pcae phase complete`) — `complete_phase`
  transitions route through the validator in place of today's
  `validate_finalization_gate()`/`validate_phase_identity()`, which
  become the report-completeness and identity invariant families.
- **Commit governance** — `commit` transitions gain a lineage invariant
  (§4.4) that can be checked *before* a commit is made, not only
  retroactively when a report references it.
- **Push governance** (`pcae push check`) — `push` transitions become a
  direct validator consumer instead of a separately-implemented trust
  gate that happens to agree with the report's own gate today.
- **Notification runtime** — `notify` transitions are gated purely by
  §7's eligibility rule, replacing today's scattered
  `PCAE_NOTIFY_ENABLED`/`_classify_notification_outcome()` checks with
  one deterministic eligibility function.
- **Runtime Snapshot / Advisory Runtime** — remain out of scope for the
  validator's *content* (it never inspects Runtime Snapshot data), but
  any future transition that would touch `execution_availability` is
  automatically a `REQUIRES_HUMAN_REVIEW` candidate under invariant
  §4.14 until a dedicated execution-enablement contract is frozen.
- **Future intent/approval/execution layers** — when execution
  capability is eventually introduced, "propose an execution" becomes
  another transition kind, and "no execution without explicit
  authorization" becomes another invariant in the same set — the
  validator's shape does not need to change, only its invariant data.

## 11. Non-Goals (This Phase)

This document defines architecture only. Explicitly out of scope for
Phase 113S:

- No `validate_transition()` function is implemented.
- No change to Advisory Runtime, Runtime Snapshot, Runtime Context, or
  Permission Broker behavior.
- No change to execution, authorization, plugin, Telegram inbound,
  REST, Web UI, or audit-persistence capability.
- No change to the existing `validate_finalization_gate()`/
  `validate_phase_identity()`/`pcae push check` code paths — this
  document describes how they will eventually be *subsumed*, not a
  change to how they work today.

Execution capability remains unavailable; this phase does not change
that in any way.
