# PCAE v0.1 — Release Notes (Draft)

## Release Name

PCAE v0.1 — Governed AI Coding Lifecycle Harness

## Release Status

**Candidate draft.** Prepared in Phase 106E for operator review. Not yet
tagged or published — tag creation is a separate, explicitly-approved
follow-up (Phase 106F).

## Positioning

PCAE v0.1 is a governed, **non-executing** AI coding lifecycle harness. It
makes an AI coding agent's *process* governable — task scope, phase
completion, commit/push sequencing, and trustworthy human notification —
without executing code, invoking a real AI backend, or mediating a shell
on the agent's behalf. Human authority remains final at every step.

## Highlights

- **Governed task/phase lifecycle** — task contracts with allowed
  files/zones, scope enforcement (advisory or blocking), and a full
  task/phase state machine (`pcae task new/show/update/pause/resume/
  finish/list`).
- **Task contracts** — every unit of work is scoped in writing before it
  starts; `pcae check`/`pcae health` flag out-of-scope changes.
- **Report-trust hard-fail gates** — `pcae phase complete` refuses to
  complete on an incomplete/invalid phase-completion report by default;
  `pcae push check` fails on a content-incomplete latest report.
- **Phase-report trust CLI** — `pcae phase-report trust` and `pcae
  phase-report show --trust` inspect report completeness (missing
  fields, disallowed placeholders) at any time.
- **Task-finish report/Telegram integration** — `pcae task finish
  --commit` automatically finalizes and trust-validates the phase report,
  dispatching notification only when it is genuinely complete — never a
  partial report.
- **v0.1 golden workflow** — a concrete, command-verified operator
  workflow from start-of-phase through post-completion verification
  (`docs/V0_1_GOLDEN_WORKFLOW.md`), smoke-tested against a fresh `git
  clone`.
- **Packaging/install smoke validation** — editable install, non-editable
  install, and `python -m build` (sdist + wheel) all verified in
  throwaway virtual environments; two packaging defects found and fixed.
- **Fast-green 4390/4390** — the full fast-green governance/core test
  gate is fully green with zero known failures.
- **Clean task-memory and push-check** — `pcae doctor task-memory` and
  `pcae push check` both report clean/ready state.
- **Telegram outbound notifications** — optional summary + document
  delivery on phase completion; entirely outbound, no inbound handler.
- **No-go registry** — a canonical, contract-tested registry
  (`docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`) of execution boundaries
  PCAE does not cross in v0.1.
- **Shared safety/authorization contract** — 12 authorization flags (all
  `False`) and 5 safety flags (all `True`) consolidated across the
  evidence/decision/coordinator layers.

## Installation Summary

```bash
git clone <repo-url>
cd pcae-harness
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pcae --help
```

Non-editable install (`pip install .`) and building distributable
artifacts (`python -m build`, producing sdist + wheel) are also verified
— see `docs/V0_1_CLEAN_SMOKE_TEST.md` for the exact, copy-pasteable
command sequence used to validate this. Full details:
`docs/INSTALLATION.md`.

## Quickstart / Golden Workflow Pointer

See `docs/V0_1_GOLDEN_WORKFLOW.md` for the full, command-verified
operator workflow. Minimal shape:

```bash
pcae health && pcae check && pcae doctor task-memory
pcae task new "<title>" --goal "<goal>" --mode implementation \
  --allowed-file <path> --allowed-zone <zone>
# ... do the work ...
pcae commit implementation --path <file> --message "<message>"
pcae task finish --staged-file-aware --commit "<completion message>"
pcae push check && pcae push --staged-file-aware
```

## Safety Boundary

- Non-executing by design: no code path in v0.1 runs agent-authored code
  or shell commands without a human driving the CLI.
- Does not invoke a real AI backend.
- Does not mediate shell commands.
- Does not apply patches automatically.
- Does not perform rollback execution.
- Telegram is outbound-only — there is no inbound handler or command
  reception path.
- All authorization flags are `False`; all safety flags
  (`simulation_only`, `no_execution`, `evidence_only`, `non_authorizing`,
  `design_only`) are `True`.

## Known Limitations

- `README.md`'s headline test/phase counts predate the current repo
  state; tracked as a documentation-currency item, not a functional
  defect.
- Two independent report-trust schemas exist internally (legacy 95M.1 and
  105A/105B); not unified in v0.1.
- `pcae push check`'s report-trust gate checks content completeness only,
  not push-state fields, by deliberate design (avoids deadlocking the
  normal task-finish-then-push sequence).
- Package version is static in `pyproject.toml`, not derived from git
  tags.

## What Is Not Included

- Autonomous execution of agent-authored code or commands.
- Runtime enforcement (permission broker / shell gate remain evidence-only
  classification prototypes).
- Real AI backend invocation or adapter execution.
- Shell mediation or interception.
- Telegram inbound / polling / remote command reception.
- Automatic patch application.
- Rollback execution.
- Cryptographic signing, remote attestation, or database-backed audit
  storage.
- Production multi-agent autonomous orchestration.

## v0.2 Autonomy Preview

v0.2 is the target release for governed autonomy: runtime enforcement,
governed real backend invocation, adapter execution under human-approval
gates, durable audit persistence, and rollback execution governance. None
of this exists yet; v0.1 is the non-executing governance foundation it
will be built on top of.

## Recommended Tag Name

`v0.1.0-rc1` — not created in this phase; requires explicit operator
approval (see `docs/RELEASE_CANDIDATE_V0_1_CHECKLIST.md`).
