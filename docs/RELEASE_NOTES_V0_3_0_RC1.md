# PCAE v0.3.0-rc1 Release Notes

## What Is New

v0.3.0-rc1 ships the first concrete, working intake path that connects
an external AI coding agent's actual proposed change to PCAE's existing
governed execution-activation/promotion/rollback chain:

- **`pcae intake create/show/list`** — a generic JSON contract for
  submitting a proposed file change ("this file, this new content,
  against this base commit") to PCAE for governance. Any tool can
  produce this JSON; PCAE does not require or assume any particular
  coding agent.
- A **thin Claude Code reference adapter**
  (`scripts/claude_code_intake_adapter.py`) that translates a Claude
  Code session's reported file changes into the generic contract. It is
  the first reference producer, not a normative or required part of the
  contract.
- A reproducible, real (not scripted-narrative) **deny + allow demo**:
  an in-scope proposal is accepted, reviewed, and promoted into the
  repository; an out-of-scope proposal is rejected before it can reach
  any promotion path — both leave an inspectable audit trail.
- A **5-minute quick-start** (`docs/QUICKSTART_V0_3.md`) exercised
  start-to-finish against this release's actual clean wheel install.

## Why It Matters

Previous releases (v0.1.0-rc1, v0.2.0) built the governance kernel —
task scope, commit/push governance, the human-gated
approval/audit/promotion/rollback chain — but nothing fed a real
external agent's proposed change into that chain. v0.3.0-rc1 closes
that gap: PCAE now governs a session you actually run, not only a
synthetic fixture.

## 5-Minute Quickstart

See [`docs/QUICKSTART_V0_3.md`](QUICKSTART_V0_3.md) for the full,
mechanically-verified walkthrough: install → `pcae init` → `pcae task
new` (scope a task) → submit a proposal → inspect → review → promote →
inspect the audit trail.

## Reference Workflow

```
external agent / any tool  -->  thin adapter (optional)  -->  generic PCAE intake
                                                                     |
                                                                     v
                          existing governed review/promotion/rollback chain (unchanged)
```

- `pcae intake create` accepts or rejects a proposal against the active
  task's scope, the real repository's fingerprint/base-commit, and a
  per-file content hash — never on the producer's word alone.
- An accepted proposal becomes an Execution Change Package (ECP) that
  still requires an explicit human `pcae promotion-review create
  --promotion-authorized` and `pcae promote` before anything is written
  to the repository.
- A rejected proposal (e.g. an out-of-scope path) produces no ECP and
  no promotion path is reachable — verified directly, not asserted.

## Claude Code Reference Adapter

`scripts/claude_code_intake_adapter.py` is distributed with the source
checkout (the install path this release documents:
`git clone` + `pip install -e .`), not inside the built wheel/sdist —
wheel-only installs will not include it. Any tool, including a hand-
written script, can produce the same generic JSON contract directly
(see the Quickstart's "Generic Producer" appendix); the adapter is a
convenience for Claude Code users, not a requirement.

## Generic Producer Support

You do not need Claude Code, or any specific agent, to use PCAE's
intake path. `docs/QUICKSTART_V0_3.md` includes a worked example of the
generic JSON contract shape any tool can emit directly.

## Security / Governance Semantics

These distinctions are unchanged and load-bearing:

- **Intake acceptance is not authorization.** `execution_allowed` and
  `promotion_authorized` are never set by intake; they remain `False`
  on every artifact the intake module produces.
- **Accepted is not promotion-authorized.** A separate, explicit human
  `pcae promotion-review create --promotion-authorized` step is always
  required before `pcae promote` can act.
- **Promotion is not general runtime execution.** `pcae promote` writes
  only the specific approved paths from a reviewed EPR; it never
  commits, pushes, or executes anything else, and remains the only
  command (with `pcae rollback`) that mutates the root repository.
- **Producer identity metadata is not authenticated human authority.**
  A producer's `producer.kind` field is a label, not a verified
  identity; reviewer identity on `promotion-review create` is likewise
  CLI-supplied, not authenticated — an existing, documented governance
  boundary, unchanged by this release.

## Current Limitations

- **No autonomous/live runtime execution.** Runtime posture remains
  `Observed` / `observe` / `execution_unavailable`, unchanged since
  v0.2.0. PCAE does not run your coding agent for you.
- **Text-only, `content_after`-oriented proposal model.** No diff/patch
  application, no binary content path, for intake candidates in this
  release.
- **Scoped to the currently active governed task.** Intake validates
  against the single active task's scope, not a multi-task queue.
- **Not published to PyPI.** Install from a source checkout
  (`pip install -e .` or the built wheel/sdist attached to this
  release) — true of v0.1/v0.2 as well.
- **macOS/Linux exercised; Windows not claimed for the intake path.**
  A documented, Non-Blocking gap exists in the intake path's absolute-
  path admission check for pure-backslash Windows-style paths; it is
  backstopped by the independent task-scope check and not exploitable
  on the only currently supported (POSIX) runtime. No Windows support
  is promised for this feature.
- **Repository-fingerprint is a content hash, not a location-bound
  identity.** Two independently created repositories with
  byte-identical genesis commit(s) would share the same fingerprint by
  design (stable across clones/forks of the same history); this is not
  an impersonation vector against an unrelated real repository.
- **Claude Code is a reference integration, not a full native harness
  integration** — a thin translation script, not a Claude-Code-specific
  contract.

## Known Issues

- Historical Fast Green / FGSC non-blocking test drift, unrelated to
  intake/ECP/promotion (see `docs/PHASE_149O_20L_7O_2U_5_V0_3_RELEASE_CANDIDATE_PREPARATION.md`
  for the exact attributed counts at RC time).
- Pre-existing `pcae doctor task-memory` warnings, documented across
  multiple prior phases.
- HATP / FIDO2 / WebAuthn: architecture complete, not activated, not on
  the v0.3 critical path — optional hardware-backed enterprise trust
  layer, not required or enforced for this release's default path.
- Permission Broker: designed (Phase 148), not yet consumed by any live
  enforcement path.

## Upgrade / Install Notes

```bash
git clone <this-repository-url>
cd pcae-harness
pip install -e .
```

or install the wheel/sdist attached to this GitHub release. No v0.2 →
v0.3 migration steps are required — the intake path is additive; no
existing command's behavior changed.

## Feedback

This is a release candidate. If you try the quickstart or the intake
path against your own repository and hit friction — confusing output,
an unexpected rejection, a step that doesn't match the docs — please
open an issue.
