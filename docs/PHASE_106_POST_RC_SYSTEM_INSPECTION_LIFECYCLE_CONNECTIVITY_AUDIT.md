# Phase 106G — v0.1 Post-RC System Inspection / Lifecycle Connectivity Audit

## Purpose

Inspect PCAE `v0.1.0-rc1` as a running system — not just as documentation
— before starting the v0.2 autonomy track. Determine whether the v0.1
lifecycle (bootstrap, task, phase, report-trust, notification, push-check)
is actually connected and automated, or whether some of what the golden
workflow describes as "connected" is really manual sequencing held
together by operator discipline and phase-brief instructions.

## Scope

Read-only inspection of the current codebase (`src/pcae/`), test suite,
and documentation as of `v0.1.0-rc1` (commit `d155dddc`). Empirical
reproduction of trust-gate behavior using the actual validator functions
(no mocking of PCAE's own logic). One tiny, findings-driven documentation
correction is in scope if discovered; no source-code behavior changes.

## Non-Goals

No runtime enforcement; no autonomous execution; no real backend
invocation; no adapter execution; no subprocess/shell execution beyond
existing lifecycle/test/packaging/tag-verification command behavior; no
network calls outside the existing Telegram outbound path and ordinary
git remote verification; no shell interception; no Telegram
inbound/polling; no remote shell; no `/run`; no automatic apply/apply
execution/patch parsing; no commit/push authorization changes beyond the
existing governed lifecycle; no real AI backend calls; no executable
artifact-only invocation path; no execution enablement flag or toggle; no
cryptographic signing; no remote attestation; no database-backed audit
storage; no shell mediation; no rollback execution, file mutation
rollback, or automatic restore; no git reset/checkout/revert execution;
**no new tag created** (no `v0.1.0-rc1`-adjacent or `v0.1.0` tag of any
kind). v0.2 implementation is explicitly out of scope — this phase only
decides whether v0.1 is coherent enough to proceed to it.

## Current v0.1.0-rc1 State

Verified at the start of this phase:

| Check | Result |
|---|---|
| `v0.1.0-rc1` exists locally | yes |
| `v0.1.0-rc1` exists on origin | yes (`b47ce1817a697eab6bee8ef158ba50d96e57c3bb`) |
| Final `v0.1.0` tag exists | no |
| `origin/main..HEAD` | 0 |
| Working tree | clean |
| `pcae health` | healthy (idle) |
| `pcae check` | passed |
| `pcae doctor task-memory` | clean |
| `pcae push check` | clean (nothing to push) |
| Active/latest phase report trust | complete (phase_id `106F`) |
| Telegram runtime | loaded, configured, enabled (outbound only) |

## Inspection Methodology

1. Enumerated every CLI subcommand touching bootstrap, task, phase, and
   report-trust behavior via `pcae --help` and targeted `--help` calls.
2. Read the actual implementation of each finalize/dispatch/gate code
   path (`commands/task.py`, `commands/phase.py`, `commands/push.py`,
   `commands/phase_reports.py`, `commands/session.py`,
   `commands/agent.py`, `core/phase_report_trust.py`,
   `core/phase_reports.py`).
3. Where two code paths appeared to implement similar logic, diffed
   their actual behavior by **importing and calling the real functions
   directly** with an identical synthetic report — not by reading
   docstrings alone — to confirm or refute suspected divergence.
4. Cross-referenced `docs/RELEASE_SCOPE_V0_1.md` and
   `docs/V0_1_GOLDEN_WORKFLOW.md` against the actual command set and test
   suite to find commands that exist but are undocumented, or golden-workflow
   claims not backed by an automated check.
5. Re-ran the full validation baseline (fast-green, combined regression,
   release/lifecycle regression, bootstrap/session/report regression) to
   confirm the inspection didn't rely on a stale test baseline.

## Bootstrap Command Inventory

The entire bootstrap-related surface is **one CLI command family**:
`pcae session <subcommand>` (`write`, `read`, `update`, `start`, `end`,
`bootstrap`, `continuity-check`). There is no separate top-level
`pcae bootstrap` command.

| Command | Implementation | Test coverage | Status | Golden workflow? | Risks | Recommended action |
|---|---|---|---|---|---|---|
| `pcae session bootstrap --agent-id <id>` | `commands/session.py::run_session_bootstrap` (lock-acquiring path) | `tests/test_session.py` (~30 tests, e.g. `test_session_bootstrap_*`) | Supported, mature | **No** — not mentioned in `docs/V0_1_GOLDEN_WORKFLOW.md` or `docs/RELEASE_SCOPE_V0_1.md` | None functional; documentation gap only | Add to golden workflow as the recommended agent/session start command, or explicitly document why it's excluded |
| `pcae session bootstrap --compact [--profile ...]` | `commands/session.py::_run_compact_bootstrap` (read-only path) | `tests/test_session.py` | Supported, read-only, no lock mutation | No | None | Same as above |
| `pcae session bootstrap --sync-lock` | same command, backend-lock rehydration flag | `tests/test_session.py` (`test_74w2_bootstrap_rehydrates_*`) | Supported, internal/advanced | No | None (already gated to recognized backends) | Document as advanced/optional flag if bootstrap is added to golden workflow |
| `pcae session start` | `commands/session.py` | `tests/test_session.py` | Supported, minimal (no args) | No | Low — narrow scope | Leave as-is; internal/diagnostic |
| `pcae session end` | `commands/session.py` | `tests/test_session.py` (`test_session_end_*`) | Supported | No | Low | Leave as-is |
| `pcae session write` / `read` / `update` | `commands/session.py` | `tests/test_session.py` | Supported, low-level snapshot I/O | No | Low — used internally by other commands | Internal plumbing; correctly excluded from golden workflow |
| `pcae session continuity-check` | `commands/session.py` | `tests/test_session.py` (`test_71j_continuity_check_*`) | Supported, read-only | No | Low | Could be added to golden workflow's diagnostics list |

**Finding:** none of the bootstrap commands are obsolete, duplicated, or
unsafe. The family is coherent and well-tested. The only issue is a
**documentation gap**: `pcae session bootstrap` is the actual command
this project's own agents have used throughout its history (visible in
this project's own session history) to start a governed work session —
richer than `pcae health` alone (it also reports active task, provenance
event count, latest handoff, push readiness, and Telegram runtime in one
call) — yet it is not named anywhere in `docs/V0_1_GOLDEN_WORKFLOW.md` or
`docs/RELEASE_SCOPE_V0_1.md`.

## Bootstrap-Session Reporting Review

`bootstrap_session_reporting_tests` is a **required key name** in
`core/phase_report_trust.py::REQUIRED_TEST_FIELDS` and
`core/phase_reports.py::_REQUIRED_BASE_TEST_RESULT_KEYS` — every phase's
canonical `test_results` mapping must carry this key with a non-placeholder
value, or the report is trust-incomplete.

**Finding:** there is no test file named `tests/test_bootstrap_session_reporting.py`
(confirmed: `find tests -iname "*bootstrap*"` returns nothing). Every prior
phase (including this one, per its own validation command list) has
supplied the value `"present_in_canonical_metadata"` for this field —
a self-referential placeholder rather than a pointer to a real, separately
countable test suite. The underlying feature it is meant to represent
(bootstrap session output correctness) **is** genuinely tested — across
`tests/test_session.py`, `tests/test_context.py`, `tests/test_docs.py`,
`tests/test_phase.py`, `tests/test_agent.py`, `tests/test_task.py`,
`tests/test_phase_reports.py`, and the phase-report-trust-gate test
files — just not under a single file matching the metadata field's name.
This is a **naming/documentation mismatch**, not a functional gap: the
capability is tested, but the required field's name suggests a dedicated
suite that doesn't exist as such.

## Task Lifecycle Review

`pcae task new` → `pcae task show/update` → `pcae commit implementation`
→ `pcae task finish --commit` is fully wired: task creation writes a
contract file that `pcae check`/`pcae health` enforce scope against
(file-level + zone-level, both independently checked); `commit
implementation` stages only explicitly-requested paths while preserving
unrelated pre-existing staged files (Phase 79A contract, unchanged);
`task finish --commit` moves the task to `tasks/done/`, updates
`tasks/DONE.md`, and — since Phase 105C — calls
`_finalize_task_report_and_notify()` to build, trust-validate, and
(conditionally) dispatch the phase-completion report. This part of the
chain is real automation, not documentation: it fires on every governed
`task finish --commit` call whether or not the operator remembers to run
anything else.

## Phase Lifecycle Review

`pcae phase complete --summary "..."` is a **second, independent**
finalization entry point (`commands/phase.py::_finalize_report_and_notify`)
that also reads `.pcae/phase-completion-metadata.json`, builds a trial
report, trust-validates it, and dispatches. Per its own module docstring
in `commands/task.py` (verbatim): *"This is the actual PCAE phase-closing
workflow; `pcae phase complete` already does this ... but is not part of
that workflow in day-to-day use."* Both paths exist, are both maintained,
and diverge in gating strength (see "Phase-Report Trust Review" below).
`pcae phase complete` is the only one of the two that **hard-fails** by
default on an incomplete report (Phase 105D); `task finish --commit` never
blocks task completion on trust — by design, since it runs pre-push and a
report is expected to be push-state-incomplete at that point.

## Phase-Report Trust Review

Two independently-evolved schemas exist and are inconsistently combined
across the three call sites that gate on them:

| Call site | Schema(s) used | Includes OLD (95M.1) full check (`files_changed>0`, no-go count, etc.)? | Includes push-state fields? |
|---|---|---|---|
| `pcae phase complete` (`commands/phase.py`) | `validate_finalization_gate` (OLD) **AND** `compute_final_trust(push_state_aware=True)` (105A/105B) | **Yes** | Yes |
| `pcae task finish --commit` (`commands/task.py`) | `validate_phase_report_trust` + `_apply_push_state_gate` (105A/105B only) | **No** | Yes |
| `pcae push check` (`commands/push.py`) | `compute_final_trust(push_state_aware=False)` (105A/105B only) | **No** | No (by design, 105D) |

**Finding (empirically reproduced, not inferred):** a synthetic report
with `files_changed=0` but every other field populated (health/check/
task-memory/push-check all green, `no_go` text present, push-state
fields all final) evaluates as follows:

```
task.py dispatch_allowed (trial_trust.complete):        True
phase.py gate[finalizable]:                              False
phase.py trust_result.complete:                           True
phase.py dispatch_allowed (gate AND trust_result):        False
gate blockers: ['files_changed missing or zero',
  "no_go_confirmations too short (0 items, require 11+ ...)",
  "report completeness is 'partial', not complete",
  'missing trust fields: files_changed']
```

`pcae phase complete` correctly refuses to finalize/dispatch this report
(the intended behavior after the Phase 105D hard-fail fix).
`pcae task finish --commit` would **dispatch it as a final, trusted
Telegram notification**, because its dispatch decision was never given
the same `gate["finalizable"] AND trust_result.complete` combination that
`phase complete` received in 105D — only the 105A/105B-plus-push-state
half of it. No existing test in `tests/test_task_finish_report_trust_notification.py`
or `tests/test_task_finish_notification_ordering.py` exercises
`files_changed=0` (both only test `files_changed_count=2`), so this gap
has no regression coverage today.

This is the single most release-relevant finding in this audit: the
report-trust hard-fail guarantee that Phase 105D established for `phase
complete` is **not symmetrically applied** to the finalize path that the
v0.1 golden workflow actually recommends for day-to-day use (`task finish
--commit`).

## Push-Check / Release Gate Review

`pcae push check`'s `phase_report_trust` gate deliberately checks content
completeness only (105D design decision, documented in
`docs/RELEASE_SCOPE_V0_1.md` and `docs/V0_1_GOLDEN_WORKFLOW.md`) — it does
not require push-state fields to already say "pushed," to avoid
deadlocking the normal pre-push task-finish-then-push sequence. This part
is intentional and correctly documented. It shares the same
"no-OLD-schema" gap identified above (a `files_changed=0` report would
also show `Phase report trust: passed` in `push check`), but this is
lower severity than the task-finish dispatch gap, since push-check is
advisory-only for push readiness and does not itself send a notification.

## Telegram Outbound Notification Review

Outbound-only, confirmed: no inbound handler exists anywhere in
`core/notifications.py` (unchanged since 105C). Dispatch is correctly
suppressed for incomplete/partial reports in both finalize paths (per the
gates above — `task finish --commit`'s suppression is just gated on the
weaker of the two schema combinations). The idempotency marker
`.pcae/phase-reports/.last-notified.json` currently reads
`{"phase_id": "106D", "commit": "f61dcb46"}` — a residual artifact from an
operator-caught correction during Phase 106E (an initial `task finish`
call read stale 106D metadata before that phase's own metadata was
written, causing one incorrectly-attributed send that was manually
corrected via a follow-up `phase complete` re-dispatch). Because `phase
complete`'s dispatch path never writes this marker (only `task finish`
does), and every finalize call since has correctly reported
`skipped_incomplete` pre-push, the marker has never been overwritten with
accurate content. This is inert (it can only cause a problem if a future
`task finish --commit` runs for `phase_id="106D"` at the exact commit
`f61dcb46` again, which cannot happen), but it is stale bookkeeping.
It is deliberately **not** hand-edited in this phase — doing so would mean
fabricating marker content that no real dispatch produced, which is worse
than leaving it honestly stale. It is documented here as a known,
inert artifact and left as a small state-hygiene item for a future phase
(see "Recommended Fixes Before Final v0.1.0").

## Release Artifact / Tag Review

Confirmed: `v0.1.0-rc1` exists locally and on `origin`
(`b47ce1817a697eab6bee8ef158ba50d96e57c3bb`, pointing at commit
`d155dddcf56e7ec17ed558f234d6148799192290`); no `v0.1.0` tag exists
locally or remotely; `origin/main..HEAD` is `0`. No governed
`pcae tag`/`release` command exists (confirmed again in this phase via
`pcae --help` and a source grep) — this remains an accurately-documented
gap from Phase 106F, not a new finding.

## Golden Workflow Alignment Review

Every command explicitly listed in `docs/V0_1_GOLDEN_WORKFLOW.md`'s
required/optional command tables was re-verified against the live CLI in
this phase (`--help` on each) and all resolve correctly. The workflow's
description of `task finish --commit`'s pre-push behavior
(`skipped_incomplete`) and `push check`'s content-only trust gate both
match actual behavior exactly. The one alignment gap found is the
bootstrap-command omission described above — the golden workflow does not
mention `pcae session bootstrap` at all, despite it being real,
supported, tested infrastructure this project's own operating history
relies on.

## Lifecycle Connectivity Map

```
pcae session bootstrap --agent-id <id>      [NOT part of documented golden workflow — see finding]
  -> (reports health/check/active-task/provenance/handoff/push/telegram in one call)

pcae task new                                [fully automated: writes task contract]
  -> pcae check / pcae health                [fully automated, hard-fail via pre-commit hook]
  -> ... implementation work ...
  -> pcae commit implementation               [fully automated, staged-file-aware]
  -> pcae skill invoke phase-finalization <ID> [MANUAL RITUAL — see Automation Gaps]
  -> pcae task finish --commit                [fully automated dispatch DECISION,
                                                 but gated by the WEAKER trust schema
                                                 combination — see Phase-Report Trust Review]
       -> finalize_phase_report()              [fully automated: writes report artifacts]
       -> trust validation (105A/105B + push-state only)  [automated, warning-only —
                                                             never blocks task finish]
       -> Telegram outbound dispatch           [automated, gated on the above —
                                                  correctly suppressed pre-push]
  -> pcae push check                          [fully automated; content-only trust gate,
                                                 hard-fail on missing/placeholder fields]
  -> pcae push --staged-file-aware            [fully automated, governed]
  -> branch pushed; origin/main..HEAD = 0     [verified, not automatically re-checked
                                                 by any command after push]

(separately, optional/manual)
pcae phase complete --summary "..."           [MANUAL command, not part of the
                                                 task-finish flow; hard-fails by default
                                                 on the STRONGER combined trust schema;
                                                 used in this project's own practice to
                                                 re-dispatch a corrected report after push]
```

## Automation Coverage Map

| Connection | Classification |
|---|---|
| `pcae task new` → scope enforcement (`check`/`health`) | Fully automated, hard-fail enforced |
| `pcae commit implementation` staged-file preservation | Fully automated |
| `task finish --commit` → report finalization | Fully automated |
| `task finish --commit` → trust validation | Automated but **warning-only**, and gated on the weaker (105A/105B + push-state) schema only |
| `task finish --commit` → Telegram dispatch | Automated, correctly suppressed pre-push, but inherits the weaker trust gate above |
| `phase complete` → report finalization + trust | Fully automated, **hard-fail enforced** on the stronger combined schema |
| `phase-finalization` skill invocation | **Documented but not automated** — see Manual Ritual Inventory |
| `push check` → trust gate | Automated, hard-fail enforced, but content-only (deliberately excludes push-state; also lacks the OLD-schema check) |
| `push` → branch push | Fully automated, governed |
| Tag creation/push | **Manual command required** (no governed tag command exists; documented gap since 106F) |
| Bootstrap → golden workflow | **Documented but not automated into the workflow at all** (bootstrap isn't mentioned) |
| `.last-notified.json` accuracy | **Unclear/stale** — see Telegram review |

## Manual Ritual Inventory

1. **`pcae skill invoke phase-finalization <PHASE_ID>`**, required by every
   phase's own operating-rules brief before completion. Traced to
   `core/agent.py::build_skill_invocation_targeting` /
   `_sit_infer_target_type`: a bare phase ID like `"106G"` only resolves if
   it appears in a static `roadmap_registry` built from
   `build_capability_roadmap_intelligence`, or matches an actual
   `tasks/active/<id>.md` / `tasks/done/<id>.md` filename (task contract
   files are timestamp-prefixed, e.g.
   `20260702-0054-phase-106g-...md`, never a bare phase code), or a known
   capability/track name. A bare phase code such as `106G` matches none of
   these, so the command returns `target_type_unresolved` (a blocker,
   nonzero exit) for **every phase**, not just this one — confirmed by
   this project's own history: every phase report since at least 105B
   records the identical `target_type_unresolved` outcome. This ritual
   currently has **zero functional effect**; it is run because the
   operating rules say to, not because it changes any command's behavior.
2. **Manually rewriting `.pcae/phase-completion-metadata.json` twice per
   phase** (once pre-push with `pushed_status: "not_pushed"`, once
   post-push with `pushed_status: "pushed"`) to get a final, correctly-
   attributed Telegram send. This is inherent to the pre-push/post-push
   sequencing (a report genuinely cannot know its own final push state
   before the push happens), not a defect — but it is a real, repeated
   manual step not automated by any single command, and it is the exact
   mechanism that produced the 106E metadata-timing mistake noted above.
3. **Re-running `pcae phase complete` after push** solely to trigger a
   corrected, final Telegram dispatch, since `task finish --commit`
   already ran (pre-push, correctly suppressed) and nothing else in the
   golden workflow re-triggers dispatch after `pushed_status` changes to
   `"pushed"`.

## Duplicate / Overlapping Command Inventory

| Pair | Why both exist | Preferred for v0.1 | Docs make this clear? | Consolidation needed? |
|---|---|---|---|---|
| `pcae phase complete` vs. `pcae task finish --commit` | `phase complete` predates the 105C task-finish integration and was never removed; `task finish --commit` is the integrated, golden-workflow path | `task finish --commit` for the golden workflow; `phase complete` for a manual, hard-fail-enforced, post-push corrected re-dispatch | Partially — `docs/V0_1_GOLDEN_WORKFLOW.md` labels `phase complete` "optional, lower-level," but does not explain *why* an operator would still need it (the post-push re-dispatch use case) | **Yes, recommended for v0.2**: either unify the two finalize functions behind one shared, consistently-gated implementation, or make the post-push re-dispatch case an explicit `task finish`/`push` follow-up step instead of a second top-level command |
| `pcae phase-report trust` vs. `pcae phase-report show --latest --trust` | Genuinely complementary, not duplicative: `trust` is a focused, scriptable JSON gate check; `show --trust` renders the full report with a trust footer for human reading | Both — used for different purposes | Yes, both are documented with distinct purposes | No |
| `pcae session bootstrap` vs. `pcae health` + `pcae push check` + `pcae notify status` | `session bootstrap` composes overlapping information (health, active task, push readiness, Telegram runtime) into one call, plus agent-lock acquisition | `session bootstrap` for agent/session start (not currently documented as such); the individual commands remain useful standalone | No — bootstrap isn't mentioned in the golden workflow at all | Recommend documenting, not consolidating — the individual commands still have independent value |

## Findings

1. **(Release-impacting)** `task finish --commit`'s Telegram-dispatch trust
   gate omits the OLD (95M.1) schema's full completeness check that `phase
   complete`'s gate includes since Phase 105D — empirically confirmed a
   `files_changed=0` report would dispatch via `task finish --commit` but
   be correctly refused by `phase complete`. No regression test covers
   this case for `task finish`.
2. **(Documentation gap, not release-blocking)** `pcae session bootstrap`
   and the rest of the `pcae session` command family are absent from
   `docs/RELEASE_SCOPE_V0_1.md` and `docs/V0_1_GOLDEN_WORKFLOW.md`, despite
   being real, tested, and used in this project's own operating practice.
3. **(Naming mismatch, cosmetic)** `bootstrap_session_reporting_tests` is a
   required trust-schema field name with no correspondingly-named test
   file; the capability it represents is tested, but scattered across
   many files under different names.
4. **(Non-functional ritual, not release-blocking)** `pcae skill invoke
   phase-finalization <PHASE_ID>` cannot resolve a bare phase code for any
   phase in this project's history; it is a required step in every phase
   brief but has zero functional effect today.
5. **(Stale bookkeeping, inert)** `.pcae/phase-reports/.last-notified.json`
   still holds `{"phase_id": "106D", "commit": "f61dcb46"}` from a
   corrected 106E dispatch mistake; harmless but inaccurate.
6. **(Design duplication, documented but not fully explained)** `phase
   complete` and `task finish --commit` implement independent, diverging
   finalize logic; the golden workflow does not explain why an operator
   still needs `phase complete` after `task finish --commit`.

No finding contradicts the core v0.1 safety claims: non-execution,
outbound-only Telegram, and the authorization/safety flag contract all
remain intact and correctly enforced everywhere checked.

## Release Impact

None of the findings above compromise the non-execution boundary, the
authorization/safety flag contract, or the release artifacts themselves.
Finding 1 (trust-gate asymmetry) is a real correctness gap in the
*reporting trust* system — a report that should be treated as
incomplete could be dispatched as final via the documented golden-workflow
path — but it does not affect code execution, scope enforcement, or the
tag/artifact state, and requires a specific, narrow trigger condition
(an OLD-schema-specific defect that the newer schema alone doesn't catch)
that has not been observed in any of this project's own phase reports to
date. `v0.1.0-rc1` remains suitable for external trial use with this
caveat documented; it is not, on its own, a reason to withhold the RC.

## Recommended Fixes Before Final v0.1.0

1. Apply the same `gate["finalizable"] AND trust_result.complete`
   combination `phase complete` uses to `task finish --commit`'s dispatch
   decision in `commands/task.py::_finalize_task_report_and_notify`
   (small, targeted change to one function; add a regression test with
   `files_changed=0`).
2. Add `pcae session bootstrap` (and, at minimum, `continuity-check`) to
   `docs/V0_1_GOLDEN_WORKFLOW.md` and `docs/RELEASE_SCOPE_V0_1.md`'s
   included-capabilities list, or explicitly document why it is
   intentionally excluded from the v0.1 supported surface. **(Done as a
   tiny doc correction in this phase — see the "Environment Setup"
   addition to `docs/V0_1_GOLDEN_WORKFLOW.md`.)**
3. Give `.pcae/phase-reports/.last-notified.json` real, accurate content
   the next time a genuine push-state-complete dispatch naturally
   overwrites it (not by hand-editing it out of band) — or add a small
   repair command that can be told the true last-sent phase/commit.
4. Add one line to `docs/V0_1_GOLDEN_WORKFLOW.md` explaining *why*
   `phase complete` is still needed after `task finish --commit` (the
   post-push corrected re-dispatch case), since this is currently
   something an operator has to infer from practice rather than read.

## Deferred Improvements for v0.2

1. Unify `commands/task.py`'s and `commands/phase.py`'s finalize/dispatch
   logic behind one shared function, eliminating the possibility of the
   two schemas diverging again as either evolves independently.
2. Either make `pcae skill invoke phase-finalization` resolve real phase
   IDs (e.g. by deriving the roadmap registry from `tasks/done/` /
   `CHANGELOG.md` instead of a static table) or remove it from the
   required per-phase ritual if it is not going to be made functional.
3. Consider renaming or re-scoping the `bootstrap_session_reporting_tests`
   trust field to something that maps to an actual, dedicated test
   target, or document explicitly that it is intentionally a
   presence-only marker.
4. Consider whether `pcae phase complete` and `pcae task finish --commit`
   should be consolidated into a single command with an explicit
   "re-dispatch corrected report" mode, removing the need for two
   separate top-level finalize commands.

## Recommended Next Phase

**106H — v0.1 RC Audit Findings Repair.** The trust-gate asymmetry
(Finding 1) is real, empirically demonstrated, and touches the exact
guarantee the v0.1 release notes claim ("report-trust hard-fail gates");
it should be repaired and covered by a regression test before treating
v0.1.0-rc1's reporting-trust story as final, even though it does not rise
to the level of blocking external trial use of the RC itself. 107A (v0.2
roadmap) should follow once 106H closes this gap.
