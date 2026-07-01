# PCAE v0.1 — Release Scope Freeze

## Release Name

**PCAE v0.1 — Governed AI Coding Lifecycle Harness**

## Release Type

Scope freeze / documentation phase (106A). Non-executing by design. No
runtime enforcement. No autonomous execution.

## Release Intent

PCAE v0.1 governs AI-assisted coding lifecycle discipline — task contracts,
scope/lifecycle enforcement, commit/push governance, and phase-completion
report trust — without ever executing, mediating, or authorizing an AI
backend's actual code-writing or shell activity. It makes an agent's
*process* governable (what it may touch, whether its completion claims are
trustworthy, whether a human was told) without claiming to make the agent's
*output* safe by construction. Human authority remains final at every step.

## Target Users

Engineers and teams who already use an AI coding agent (Claude Code, Codex,
or similar) and want a lightweight, local, non-executing layer that:
enforces task-scoped file boundaries, requires trustworthy phase-completion
reporting before a phase is considered "done," and sends outbound
notifications of that reporting to a human, without adding a new execution
surface of its own.

## Supported Use Case

A human operator drives an AI coding agent through PCAE's governed
lifecycle commands (`task new` → agent does the work → `commit
implementation` → `task finish --commit`), with PCAE tracking scope,
validating phase-completion report trust, and optionally notifying the
operator via Telegram. All actual code writing, shell commands, and git
operations remain performed by the human/agent through their existing
tools — PCAE observes, gates, and records; it does not perform them.

## Unsupported Use Cases

- Unattended/autonomous agent operation with no human in the loop.
- Using PCAE as a sandbox, shell mediator, or execution broker.
- Using PCAE's Telegram integration for remote command/control.
- Relying on PCAE to catch or roll back a bad code change after the fact —
  it has no rollback execution capability.
- Treating `pcae push check` / `pcae phase complete` passing as a
  correctness or security guarantee about the code itself — they attest to
  *process* completeness (scope, tests reported, trust fields present),
  not to code quality.

## Included v0.1 Capabilities

- **Task/phase lifecycle discipline** — `pcae task new/show/update/pause/
  resume/finish/list`, active task contracts with allowed files/zones,
  enforcement mode.
- **Governed commit/push workflow** — `pcae commit implementation`, `pcae
  task finish --commit` (staged-file-aware), `pcae push`, `pcae push
  check`. No raw `git commit`/`git push` required or assumed for governed
  closure.
- **Phase report trust validator** (105A) — `validate_phase_report_trust()`
  / `select_active_phase_report()` in `core/phase_report_trust.py`: detects
  missing required fields and disallowed placeholders (`TBD`, `pending`,
  `not captured`, `unknown`), classifies complete/partial/invalid.
- **Report trust CLI** (105B) — `pcae phase-report trust` (`--metadata`,
  `--report`, `--phase-id`, `--json`; exit 0/1/2) and `pcae phase-report
  show --trust`.
- **Hard-fail trust gates** (105D) — `pcae phase complete` refuses
  (exit 1) to complete on an incomplete/invalid report by default
  (`--allow-partial-report` is the explicit, logged override); `pcae push
  check` fails on a content-incomplete latest phase report.
- **Task-finish report/notification integration** (105C, 105C.1) — `pcae
  task finish --commit` automatically finalizes and trust-validates the
  phase report from `.pcae/phase-completion-metadata.json`, and dispatches
  Telegram only when the report is push-state complete (never sends a
  partial report as final; `.pcae/phase-reports/.last-notified.json`
  prevents duplicate sends).
- **Phase report canonical metadata** — `.pcae/phase-completion-metadata.json`,
  `.pcae/phase-completion-report.md`, `.pcae/phase-reports/*.json|*.md`.
- **Canonical no-go registry** — `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`
  (RE-NOGO-001..017), frozen with contract tests.
- **Shared safety/authorization contract** — 12 authorization flags (all
  False) and 5 safety flags (all True) consolidated across the
  evidence/decision/coordinator layers (Phase 104C).
- **Telegram outbound notifications** — summary + document delivery on
  phase completion, gated by `PCAE_NOTIFY_ENABLED`/`PCAE_NOTIFY_SINKS`.
- **`pcae health` / `pcae check` / `pcae doctor task-memory` / `pcae push
  check`** — governance-state, scope, and task-memory-consistency checks,
  all read-only except for their own governed state files.
- **Evidence-only runtime-readiness artifacts** — the evidence
  bundle/decision-engine/coordinator layers (Phases 101–104) remain
  design/model-only: they produce structured evidence and decisions but
  perform no runtime invocation.
- **Explicit no-execution posture** — every phase report's No-Go
  Confirmations section and every governed command's help text states the
  execution boundary explicitly; no command in this list writes outside
  its declared task scope or invokes a shell/backend beyond git plumbing
  already used by the lifecycle commands themselves.
- **Fast-green baseline tracking** — `python -m pytest -m fast_green -n
  auto` as the standard development gate (~4390 tests, ~1 min).
- **`report_notification_tests` / `bootstrap_session_reporting_tests`** —
  required trust-schema fields tracked in every phase's canonical metadata.

## Excluded v0.1 Capabilities

- Autonomous execution (no capability exists to run agent-authored code or
  commands without a human driving the CLI).
- Runtime enforcement (permission broker / shell gate remain
  classification prototypes — `pcae permission-broker evaluate`, `pcae
  shell-gate check` — evidence-only, all `*_performed` flags False).
- Real backend invocation (no code path calls an actual AI backend API).
- Adapter execution.
- Shell/subprocess/network mediation beyond the lifecycle/test commands'
  own existing git/pytest subprocess calls (unchanged since long before
  this phase).
- Shell interception.
- Telegram inbound / Telegram polling / remote shell / `/run` — outbound
  delivery only; no inbound handler exists anywhere in `core/notifications.py`.
- Automatic apply / patch parsing for execution.
- Rollback execution (the `pcae rollback` / promotion chain described in
  README.md's artifact-lifecycle table is a separate, still evidence-only
  design track, not part of the v0.1 golden workflow below).
- Commit/push authorization changes beyond the existing governed lifecycle
  (`pcae commit implementation`, `pcae task finish --commit`, `pcae push`).
- Execution enablement flag or toggle. `execution_enablement_flag_present`
  exists as an evidence field in `core/backend_invocations.py` and is
  hard-set to `False` everywhere — it records absence, it is not itself a
  toggle that can be flipped to enable execution.
- Cryptographic signing, remote attestation, database-backed audit storage.
- Production multi-agent autonomous orchestration (`pcae orchestration
  simulate/validate` remain advisory simulations, not live orchestration).

## Supported Golden Workflow

Verified against the current CLI (`pcae --help` and each subcommand's
`--help`) in this session — every command below exists and runs as shown.

```
# One-time / per-session setup
source ~/.config/pcae/telegram.env
pcae health
pcae check
pcae doctor task-memory
pcae notify status

# Start a governed unit of work
pcae task new "<title>" --goal "<goal>" --mode implementation \
  --allowed-file <path> --allowed-zone <zone>

# ... AI agent / human does the work ...

pcae commit implementation --path <file> --message "<message>"
# (repeat commit implementation for each logical commit)

pcae task finish --staged-file-aware --commit "<completion message>"
# → finalizes + trust-validates the phase report; dispatches Telegram
#   only if .pcae/phase-completion-metadata.json is present and the
#   report is push-state complete; otherwise "skipped_incomplete"

pcae push check
pcae push --staged-file-aware   # or: pcae push

# Inspect trust state at any time
pcae phase-report show --latest --trust
pcae phase-report trust --json
```

**Optional, lower-level finalization path** (manual/ad hoc, not required
for the golden workflow): `pcae phase complete --summary "..."` — hard-fails
by default on incomplete trust; add `--allow-partial-report` to override
(still never dispatches Telegram for a partial report).

No commands were invented for this workflow; all were exercised via
`--help` or direct invocation during this phase.

## Experimental / Internal Commands

Present in the CLI, exercised in the test suite, but **not** part of the
v0.1 supported golden workflow — evidence-only, design/prototype-stage, or
oriented at PCAE's own future roadmap rather than day-to-day use:
`pcae permission-broker *`, `pcae shell-gate *`, `pcae orchestration *`,
`pcae governance *`, `pcae runtime *`, `pcae strategic-continuity *`,
`pcae irg-challenge`, `pcae capability *`, `pcae skill *`, `pcae exec`,
`pcae fleet *`, `pcae daemon *`, and the write/execution-track command
families (`write-authorization`, `execution-request`, `execution-review`,
etc.). These remain useful for PCAE's own internal governance
dogfooding and roadmap validation but are not documented as user-facing
v0.1 features; a `pcae --help` listing them is not, by itself, a claim
that they are production-supported.

## Safety Claims (Allowed)

- Non-executing by design.
- Governs the AI-assisted coding lifecycle (task scope, phase reporting,
  commit/push sequencing).
- Does not autonomously execute code.
- Does not mediate shell commands.
- Does not invoke real AI backends.
- Does not apply patches automatically.
- Does not perform rollback execution.
- Does not provide Telegram inbound control.
- Report-trust hard-fail gates prevent incomplete/placeholder-containing
  phase reports from being treated as a final, release-ready completion.
- All authorization flags are False and all safety flags
  (`simulation_only`, `no_execution`, `evidence_only`, `non_authorizing`,
  `design_only`) are True across the evidence/decision/coordinator layers.

## Forbidden Claims

Do not describe v0.1 as: autonomous execution; runtime enforcement (as
opposed to runtime-enforcement *readiness evidence*); capable of real
backend invocation; capable of adapter execution; capable of shell,
subprocess, or network mediation beyond existing lifecycle/test plumbing;
capable of automatic patch application; capable of rollback execution;
offering Telegram inbound remote control; production-safe multi-agent
autonomous coding; or able to grant execution authorization of any kind.

## Known Limitations

- `README.md` and `docs/ROADMAP.md` are stale relative to actual repo
  state (README cites "7,278 tests / 87 phases," ROADMAP cites "90 phases
  / June 2026" — actual state at this phase is 106A, ~13,000+ tests). Not
  fixed in this phase (out of 106A's scope: documentation-content freeze,
  not documentation-accuracy repair); tracked as a release blocker below.
- Two independent, overlapping report-trust schemas exist in this
  codebase (the pre-existing 95M.1 `assess_completeness()` schema and the
  105A/105B `validate_phase_report_trust()` schema) — documented across
  105B/105C.1/105D's own docs; not unified in v0.1.
- `pcae push check`'s phase-report-trust gate deliberately does not
  require push-state fields (`pushed_status`/`origin_main_head`/
  `pcae_push_check`) to already say "pushed" (105D design decision, to
  avoid deadlocking the normal task-finish-then-push sequence) — it only
  checks report *content* completeness.
- **(106B, resolved)** The 3 previously-known fast-green failures were
  triaged and fixed in Phase 106B — see
  `docs/PHASE_106_RELEASE_CRITICAL_WARNING_FAST_GREEN_TRIAGE.md`. Fast-green
  is now fully green (4390/4390). This bullet is retained as a record of a
  limitation that existed at 106A and no longer exists.

## Release Blockers

| Item | Classification |
|---|---|
| 3 fast-green failures (`Test94UPreflightArtifact`, `Test94UPreflightArtifactCLI`, `TestBackendShow`) | **Resolved (106B)** — root-caused and fixed; fast-green is fully green |
| `pcae_doctor_task_memory` state | Currently **clean** — no blocker |
| Install/packaging state (no `pip install pcae` / PyPI artifact verified in this phase) | **Must document before v0.1** — installation is `docs/INSTALLATION.md` source-checkout based; not validated as a clean-install smoke test in this phase |
| README/ROADMAP staleness (test counts, phase counts) | **Must document before v0.1**; recommend fixing before public release, not blocking internal scope freeze |
| Golden workflow not independently smoke-tested end-to-end as a single scripted run (only exercised command-by-command as of 106A) | **Must document before v0.1** — recommend a dedicated smoke-test phase (candidate: 106C) |
| Telegram configuration reliance (`~/.config/pcae/telegram.env`, user-specific, not part of the repo) | **Must document before v0.1** — Telegram is optional; golden workflow must work with it entirely unset |
| Hard-fail coverage is `pcae phase complete` + `pcae push check` only; `pcae task finish --commit` remains warning-only pre-push by design (105C.1/105D) | Not a blocker — documented, intentional design |
| Release-grade "zero hidden failures" test run | **Resolved (106B)** — fast-green now has zero known failures |

As of 106B, nothing remains classified **must fix before v0.1** beyond
what's already resolved. 106C (recommended next) should scripted-smoke-test
the golden workflow end-to-end.

## Validation Baseline (as of 106B)

| Check | Result |
|---|---|
| 106B fast-green failure repro/fix | 22/22 passed (all 3 known failures now pass) |
| Focused release-triage tests | see `tests/test_release_critical_triage_v0_1.py` |
| `test_backend_invocations.py` full suite | 761/761 passed |
| `test_backend_cli.py` full suite | 307/307 passed |
| 105D trust hard-fail tests | 29/29 passed |
| `test_phase.py` full suite | 886/886 passed |
| Focused hard-fail/push-check tests | 360/360 passed |
| Push-check/task lifecycle regression | 404/404 passed |
| `report_notification_tests` | 219/219 passed |
| `bootstrap_session_reporting_tests` | present_in_canonical_metadata |
| Combined regression (preflight/artifact/trust/contract/readiness/boundary/attempt/no_go/runtime_enforcement/evidence_bundle/decision/coordinator) | 2220/2220 passed |
| Fast-green | **4390/4390 — fully green, no known failures** |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae doctor task-memory` | clean |
| `pcae push check` | clean |
| Telegram runtime | loaded, configured, enabled |

## Release Checklist

- [x] Report trust validator implemented and CLI-reachable (105A/105B)
- [x] Task-finish report/notification integration (105C/105C.1)
- [x] Hard-fail trust gates for `phase complete` / `push check` (105D)
- [x] v0.1 scope frozen in writing (this document)
- [x] Fast-green fully green, 3 known failures fixed (106B)
- [x] Golden workflow documented and command-verified (106C — see
      `docs/V0_1_GOLDEN_WORKFLOW.md`, the required release artifact for
      the v0.1 operator workflow)
- [x] Golden workflow smoke-tested from a genuinely clean checkout (106D
      — see `docs/PHASE_106_PACKAGING_INSTALLATION_CLEAN_SMOKE_TEST.md`)
- [x] Clean-install validation performed (106D — editable, non-editable,
      and built sdist/wheel install all verified; 2 packaging defects
      found and fixed)
- [ ] README.md / ROADMAP.md brought current with actual state
- [ ] v0.1 tag/release notes drafted

## v0.2 Full-Autonomy Roadmap Boundary

v0.2 autonomy is **out of scope for v0.1** and requires separate
design → implementation → freeze → hardening → review passes for:

- Runtime enforcement implementation (permission broker moving from
  evidence/classification to actually mediating commands).
- Permission broker enforcement (live decision application, not just
  `pcae permission-broker evaluate` simulation).
- Shell/subprocess/network mediation.
- Governed backend invocation (real AI backend calls under contract).
- Adapter execution.
- Human approval enforcement (turning today's evidence-only approval
  *models* into an enforced gate).
- Durable audit persistence (today's audit trail is file-based/append-only
  local artifacts, not a database-backed store — and database-backed audit
  storage is explicitly excluded even for v0.2 planning purposes per this
  phase's no-go boundary; any future audit-storage upgrade needs its own
  design phase).
- Rollback execution governance (the `pcae rollback`/promotion chain is
  designed but not wired to real execution).
- Output capture/redaction for real backend output.
- Emergency stop/abort.
- Execution enablement design (the flag/toggle mechanism itself, not just
  its absence).
- End-to-end safety proof before any execution capability ships.
- Telegram inbound or remote control, if desired at all — would need its
  own authentication/authorization design, separate from outbound
  delivery.
- A release-grade test suite with no hidden/pre-existing failures.

## Golden Workflow

`docs/V0_1_GOLDEN_WORKFLOW.md` is the required release artifact defining
the exact v0.1 operator workflow: start-of-phase, implementation,
pre-finalization, finalization (report/notify/commit/push), and
post-completion verification, with required vs. optional commands and the
unsupported-flows list. Every command in it was verified against the live
CLI in Phase 106C, and smoke-tested from a genuinely clean checkout in
Phase 106D.

## Packaging / Install / Clean-Smoke-Test Status (106D)

**Clean install: passed.** Editable install, non-editable local install,
and built sdist/wheel (`python -m build`) were all verified in throwaway
virtual environments outside this repository. Two release-critical
packaging defects were found and fixed:

1. `pcae health`/`pcae check` crashed with an unhandled traceback when run
   outside a git repository (now fails with a clear one-line error).
2. The sdist swept in the entire repository checkout by default (44,399
   files, including local `.claude/` settings and `.pcae/` runtime state)
   — the wheel was already correctly scoped; the sdist now is too (117
   files, `src/pcae` + `README.md` + `LICENSE` + `pyproject.toml`).

No remaining packaging blockers before a v0.1 release candidate. See
`docs/PHASE_106_PACKAGING_INSTALLATION_CLEAN_SMOKE_TEST.md` and
`docs/V0_1_CLEAN_SMOKE_TEST.md`.

## Recommended Next Phases

**106B — Release-Critical Warning / Fast-Green Triage — complete.** The 3
fast-green failures were root-caused and fixed (fast-green now 4390/4390);
`pcae doctor task-memory` confirmed clean. See
`docs/PHASE_106_RELEASE_CRITICAL_WARNING_FAST_GREEN_TRIAGE.md`.

**106C — Golden Workflow Stabilization — complete.** The v0.1 golden
workflow is documented and command-verified. See
`docs/V0_1_GOLDEN_WORKFLOW.md`.

**106D — Packaging / Installation / Clean-Smoke Test — complete.**
Packaging metadata, editable/non-editable install, and build artifacts
verified in clean environments; 2 defects found and fixed. See
`docs/PHASE_106_PACKAGING_INSTALLATION_CLEAN_SMOKE_TEST.md`.

**106E — v0.1 Release Candidate** (recommended next). Prepare the release
candidate with a final checklist, release notes, and tag-readiness review.

**106D — Packaging / Installation / Clean-Smoke Test** (recommended next).
Validate installation/packaging and run the golden workflow from a
genuinely clean checkout, followed by a documentation-accuracy pass
(README/ROADMAP reconciliation) before any v0.1 tag is cut.
