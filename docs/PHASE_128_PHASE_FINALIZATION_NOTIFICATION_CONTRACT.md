# Phase 128B.2 - Phase Finalization Notification Contract

## 1. Purpose

This contract elevates notification from an implementation detail to a
governed lifecycle invariant.

Phase 128B.1 repaired a mechanical gap: `pcae phase-report create` (a
documented recovery path) never dispatched a notification at all.
While investigating that gap, a more fundamental governance question
surfaced: *why* is notification allowed to be a code path that some
completion routes wire in and others silently omit?

The answer this contract fixes: the canonical phase report is not
merely documentation. For long-running autonomous engineering
sessions — where a human operator is not watching the terminal in
real time — the canonical report, delivered to the operator's
notification sink, **is the authoritative completion signal**. A
phase that finishes without that signal reaching the operator has not
actually finished from the operator's point of view, regardless of
what the repository's own git history or `.pcae/phase-reports/`
directory says.

Therefore: notification is not something a completion command may
optionally wire up. It is part of what "governed phase finalization"
*means*. This contract defines that meaning, once, canonically, for
every current and future completion path — so no future completion
path can repeat 128B.1's root cause (a completion path that produces a
trust-complete canonical report but never notifies) by omission.

This phase is governance documentation only. It is not part of
Historical Memory, introduces no runtime capability, and makes no
Repository Intelligence, Historical Memory, schema, or notification
implementation change. It governs behavior that 128B.1 already
implemented; it does not implement anything new itself.

## 2. Contract Authority

This document is the canonical Phase Finalization Notification
Contract unless explicitly superseded by a future governed
contract-amendment phase. It is global governance — it applies to
every PCAE phase, past, present, and future, not to any one
architectural track. It does not amend, and remains compatible with,
every existing governance contract (125B, 127B, the 128 series) and
every existing notification mechanism (126G, 126G.1, 128B.1's
certification/marker infrastructure).

No future phase may reinterpret this contract as authorizing a
notification-format change, a canonical-report-format change, a
trust-assessment change, or any runtime-behavior change without its
own separate, explicitly scoped governed contract-amendment phase.

## 3. Governance Rationale

Three observations, each independently sufficient to justify this
contract, converge:

1. **The operator is not synchronous with the agent.** Autonomous
   engineering sessions run phase after phase without a human present
   at every completion boundary. The notification is the only signal
   that reaches the operator outside of the repository itself.
2. **128B.1's root cause was structural, not incidental.** The defect
   was not a bug in one function — it was the absence of a governing
   rule that every completion path must satisfy. Without such a rule,
   any future completion path (a new recovery command, a new
   automation entrypoint) can reintroduce the same class of gap by
   simply not wiring in dispatch, exactly as `pcae phase-report
   create` did not.
3. **The canonical report already carries trust semantics; notification
   had none.** `report_completeness`, trust assessment, and the
   finalization gate already treat the canonical report as an
   artifact with binding correctness requirements. Notification, by
   contrast, was purely a best-effort side effect with no lifecycle
   status of its own. This contract closes that asymmetry: dispatch
   (or a durable, recorded failure to dispatch) becomes as mandatory a
   component of finalization as trust assessment already is.

## 4. Phase Finalization Notification Invariant — PFN-001

> **PFN-001**: Every terminal phase outcome shall produce exactly one
> trusted canonical phase report delivered to the configured
> notification sink. Notification delivery — or an explicit, durable
> delivery-failure record — is a mandatory component of governed phase
> finalization. Silent notification omission is prohibited.

PFN-001 is binding on every governed phase from this contract forward.
It is stated once here and referenced, not restated, by every future
phase and every future completion-path implementation.

Three clauses, read together:

- **"exactly one"** — not zero (the 128B.1 defect), not more than one
  (the duplicate-dispatch risk 128B.1 also closed).
- **"trusted canonical phase report"** — Section 5 defines this
  precisely; an untrusted or partial report never satisfies PFN-001.
- **"or an explicit, durable delivery-failure record"** — PFN-001 does
  not require that a network-unreachable Telegram sink somehow still
  succeed. It requires that failure be *recorded*, not silently
  absorbed. A recorded failure satisfies the invariant; a silent one
  never does.

## 5. Canonical Report Authority

The canonical phase report — the trust-assessed artifact written to
`.pcae/phase-reports/latest.json`/`latest.md` (or the phase's own
timestamped sibling) — is the **only** report authorized for
notification.

Notification shall never be generated from:

- console/terminal output;
- a temporary or intermediate summary;
- partial or unassessed metadata;
- an ad hoc status message composed outside the canonical report
  pipeline.

Notification content always reflects the trusted canonical report
byte-for-byte in substance — restating, for governance purposes, the
content-fidelity property 126G already established at the
implementation level (canonical markdown embedded directly in the
notification event, not an independently regenerated summary) and
128B.1 already verified end-to-end against a real Telegram delivery.
This contract makes that property a governance requirement, not
merely an implementation choice that happened to be correct.

## 6. Terminal Outcomes

PFN-001 applies uniformly to every terminal phase outcome — a phase
does not need to succeed to require a notification; it needs to
*end*:

- **completed** phases — the ordinary case;
- **partially completed** phases — a report finalized under an
  explicit override (e.g. `--allow-partial-report`) still requires a
  notification, distinctly labeled as partial (matching 113X.3's
  existing "partial warning" event kind, now a governance requirement
  rather than an implementation nicety);
- **incomplete** phases — a report that never reached trust
  completeness still requires the operator be told *that it did not*,
  not silence;
- **failed** phases — a phase that errors out still terminates, and
  the operator still needs to know;
- **blocked** phases — quarantined by the finalization gate (113X.1
  semantics); PFN-001 does not weaken quarantine (a blocked report is
  never promoted to canonical/notified as if it were trusted), but the
  *fact* of being blocked is itself a terminal outcome requiring
  observability, not literal Telegram dispatch of an untrusted report
  (Section 5 already forbids that) — see Section 9's failure-contract
  distinction between "notification of success" and "durable record
  that dispatch could not occur."
- **governance-aborted** phases — a phase halted by governance
  intervention still terminates and still requires a durable
  completion/abort signal;
- **trusted recovery paths** — a report produced via any recovery
  command (128B.1's `pcae phase-report create` repair; any future
  recovery command) that reaches the same trust-complete state as the
  primary path is held to the identical PFN-001 obligation — a
  recovery path is not a lesser-governed path.

**Every terminal outcome produces exactly one canonical report.** A
phase does not get to skip report generation because it failed or was
blocked — it gets a report whose `status`/`report_completeness`
honestly reflects the outcome, and PFN-001 governs what happens to
that report next (dispatch, or a durable failure record).

## 7. Finalization Lifecycle

The governed lifecycle, binding from this contract forward:

```
Phase work complete
        |
        v
Canonical report generated
        |
        v
Trust assessment
        |
        v
Canonical report finalized
        |
        v
Exactly one notification dispatched
        |
        v
Delivery acknowledged
     or
Durable delivery failure recorded
        |
        v
Phase finalized
```

**Notification is part of finalization. It is not a post-finalization
side effect.** This is the single sentence this contract exists to
establish. Before this contract, notification was implemented as
something that happens *after* the canonical report is written, on a
best-effort basis, with no lifecycle status of its own — exactly the
structure that allowed `pcae phase-report create` to skip it entirely
without violating anything, because nothing said it couldn't. Under
this contract, "phase finalized" is not reached until either delivery
is acknowledged or a durable delivery-failure record exists. A
completion path that writes the canonical report and stops there,
without one of those two outcomes, has not completed finalization —
it has completed report generation, a strictly smaller thing.

This restates, and makes binding, the sequencing 128B.1's own repair
already implements (certify → dispatch → mark-notified, always after
report write and trust assessment, never before) — this contract is
the governance statement of why that sequencing is correct, not a new
sequencing.

## 8. Delivery Guarantees

Every governed completion path shall guarantee:

- **exactly one notification** per trusted canonical report — no
  fewer (the 128B.1 defect class), no more (the duplicate-dispatch
  class 128B.1's idempotency marker prevents);
- **trusted report only** — Section 5; an untrusted report is never
  the subject of a normal-completion notification;
- **dispatch after report trust completion** — Section 7's ordering;
  dispatch is never attempted before the report it carries has been
  written and trust-assessed;
- **identical notification regardless of lifecycle path** — a
  `completed` phase notification looks the same in structure whether
  produced by the primary completion command or a recovery command;
- **identical notification regardless of recovery path** — restated
  from the previous point for emphasis: `pcae phase complete`, `pcae
  phase-report create`, and any future recovery command must produce
  structurally identical notification content for the same trusted
  report, per Section 5's canonical-report-authority rule;
- **idempotent dispatch** — re-invoking any completion or recovery
  path for a phase/commit that already notified is a safe no-op, never
  a re-send;
- **duplicate prevention** — the corollary of idempotency: two
  different governed paths (e.g. `pcae phase-report create` followed
  by `pcae notify send-report --latest`) must not each independently
  dispatch for the same trusted report.

128B.1's shared certification (`certify_notification_transition()`)
and idempotency-marker (`.pcae/phase-reports/.last-notified.json`)
mechanism already satisfies every guarantee in this section, verified
by 128B.1's own regression suite and real-Telegram verification. This
contract does not require re-implementing that mechanism — it requires
that every *future* completion path be built to satisfy these same
guarantees, using that mechanism or its governed successor, rather
than reinventing dispatch logic independently (the mistake that
produced the original gap).

## 9. Failure Contract

Notification failures shall:

- **never silently disappear** — a failed dispatch attempt (transport
  unreachable, sink misconfigured, API error) must be recorded
  somewhere durable and inspectable, not merely printed to a terminal
  that may not be watched;
- **become durable governance records** — restating 113X.3's existing
  "notification_outcome is always one of ATTEMPTED/SENT/SKIPPED_WITH_
  REASON/FAILED_WITH_REASON, always present" property as a binding
  governance requirement, not an implementation nicety that a future
  refactor could quietly drop;
- **remain observable** — `pcae notify status`, `pcae phase-report
  trust`, and the canonical report's own persisted
  `notification_result` field must together always answer "was this
  phase's notification sent, and if not, why" without requiring the
  operator to have been watching the original command's live output;
- **never invalidate the canonical report** — a notification failure
  is a delivery-layer fact, never a correctness judgment on the report
  itself; a canonical report that is trust-complete remains
  trust-complete regardless of whether its notification succeeded,
  restating 113X.3's existing separation between report trust and
  notification outcome.

A durable failure record satisfies PFN-001's "or an explicit, durable
delivery-failure record" clause (Section 4). What PFN-001 forbids is
the silent third option: a failed or never-attempted dispatch that
leaves no trace anywhere the operator or a future auditor could find
it — exactly the class of gap 128B.1 fixed for `pcae phase-report
create` (which, before that repair, did not even attempt dispatch, let
alone record an attempt).

## 10. Supported Completion Paths

PFN-001 applies equally, with no path receiving weaker treatment, to:

- `pcae phase complete` — the primary completion command;
- `pcae phase-report create` — the governed recovery command (128B.1
  repair target);
- governed recovery paths generally, including `pcae notify
  send-report --latest` (128B.1's second repair target) and any
  future recovery command reached when the primary path is rejected
  by the repository transition validator;
- **future governed completion paths** — any completion command not
  yet built must be designed to satisfy PFN-001 from its first version,
  not retrofitted later. This is the primary forward-looking purpose
  of stating PFN-001 as a named, numbered invariant: a future phase
  introducing a new completion path can cite "PFN-001" directly as an
  acceptance criterion, rather than this gap needing to be
  independently rediscovered the way 128B.1 rediscovered it.

## 11. Cross-Track Compatibility

This governance contract applies globally, across every architectural
track, not to Historical Memory specifically. It must remain
compatible with:

- **Repository Intelligence** (Tracks 119-124) — no behavioral
  dependency; PFN-001 governs how *any* phase's completion is
  notified, independent of what subsystem that phase touched;
- **Dependency Knowledge Graph** (Track 126) — same;
- **Historical Memory** (Track 127, Track 128's own hardening chapter)
  — same; this contract is filed under the 128 series because it was
  discovered during Track 128 work, but it does not govern Historical
  Memory's own behavior and Historical Memory does not govern it;
- **future architectural chapters** — any future track's own phases
  inherit PFN-001 automatically, as global governance, without needing
  to restate or re-derive it.

This contract introduces no behavioral dependency on any subsystem. A
phase that touches zero Repository Intelligence, zero Historical
Memory, and zero Dependency Knowledge Graph content is exactly as
bound by PFN-001 as a phase that touches all three — PFN-001 is a
property of *phase finalization itself*, not of any artifact family a
phase happens to produce.

## 12. Governance Contract

This contract preserves, unchanged:

- **observe-only runtime** — PFN-001 governs a documentation/
  notification concern, not execution; runtime state remains
  `Observed`;
- **execution unavailable** — maximum plugin capability remains
  `observe`; Permission Broker status remains `execution_unavailable`;
  no phase governed by PFN-001 gains execution capability by virtue of
  sending a notification;
- **reproducibility** — PFN-001 does not touch determinism of any
  artifact; it governs delivery of an already-deterministic canonical
  report;
- **auditability** — PFN-001 strengthens auditability (Section 9's
  durable-failure-record requirement) rather than weakening it;
- **explainability** — every notification, under PFN-001, traces
  directly and only to the canonical report that authorized it
  (Section 5); there is no notification content this contract permits
  that cannot be explained by pointing at the canonical report.

## 13. Strict Non-Goals

This phase does not:

- redesign Telegram (the sink implementation is unchanged);
- redesign reporting (canonical report generation is unchanged);
- redesign trust assessment (unchanged);
- redesign phase completion (unchanged);
- redesign notification implementation (128B.1's certification/marker
  mechanism already satisfies this contract; nothing here requires
  re-implementing it);
- change notification format (unchanged);
- change canonical report format (unchanged);
- modify runtime behavior (unchanged; runtime remains
  Observed/observe/execution-unavailable);
- introduce execution capability (none introduced);
- modify Repository Intelligence (no file under
  `src/pcae/repository_intelligence/**` touched);
- modify Historical Memory (no Historical Memory file touched);
- modify schemas (no schema file touched);
- modify source code (no `src/**` file touched by this phase);
- modify test code (no `tests/**` file touched by this phase).

This phase establishes governance only. It documents a rule that
128B.1's own implementation already satisfies; it authorizes no new
implementation work, and none was performed.

## 14. Relationship to 128B.1 and Future Phases

- **128B.1** (already complete) is this contract's proof of
  correctness in practice: its certify → dispatch → mark-notified
  sequencing, applied identically across `pcae phase complete`, `pcae
  phase-report create`, and `pcae notify send-report --latest`,
  already satisfies every guarantee in Sections 4, 8, and 9. This
  contract retroactively names what 128B.1 built as the canonical
  pattern, and makes it binding for every future completion path
  rather than leaving it as one repair's own implementation choice.
- **Any future phase introducing a new completion, recovery, or
  finalization path** must design that path to satisfy PFN-001 from
  its first version — citing this contract directly — rather than
  requiring a future 128B.1-style incident to discover the gap again.
- **128C — Historical Memory Review & Hardening Contract Verification**
  is unaffected by this contract's content (PFN-001 is orthogonal to
  Historical Memory's own domain) and resumes as the next planned
  Track 128 phase after this governance interlude.

## 15. Acceptance

128B.2 is complete when this contract is frozen as the canonical
Phase Finalization Notification Contract, PFN-001 is defined and
binding for every future PCAE phase, project status reflects 128B.2
completion, runtime remains `Observed`/`observe`/execution-unavailable,
no implementation occurred, and Track 128's roadmap resumes at 128C —
Historical Memory Review & Hardening Contract Verification.
