# PCAE v0.2.0 Draft Release Notes

Status: official v0.2.0 release notes. Phase 117E prepared the release
metadata and release-facing repository state; Phase 117E.1 repaired the
publication gap by publishing the official Git tag and GitHub Release.
No PyPI or package publication is part of this release.

## Release Positioning

PCAE v0.2.0 is a governed, non-executing AI coding lifecycle harness.
It is intended to make AI-assisted software engineering auditable,
evidence-based, scoped, and human-authoritative. It is not an
autonomous coding agent.

The v0.2 posture is intentionally conservative:

- runtime state is `Observed`
- execution capability is unavailable
- maximum plugin capability is `observe`
- no runtime plugins are registered
- advisory evidence does not authorize action
- dry-run output does not enforce or authorize action
- human approval remains authoritative

## Highlights

- Frozen v0.2 architecture following the 115Z -> 116A -> 116B -> 116C
  -> 116D -> 116F review chain.
- Repository State Kernel and Repository Transition Validator contracts
  define centralized repository-state validation.
- Canonical phase-report promotion, trust gating, quarantine, and
  pushed-state reconciliation are documented and exercised through
  governed lifecycle commands.
- Evidence Framework, Decision Evaluation, Repository Skills, Advisory
  Provider, Advisory Repository Skills, and Advisory Context Package
  contracts are frozen for v0.2.
- Runtime introspection reports the current non-executing posture via
  `pcae runtime inspect --json`.
- `pcae agent verify-handoff` provides cross-agent handoff safety
  verification.
- `pcae session bootstrap --compact --profile implementation` provides
  compact governed session context without relaxing governance.
- Telegram remains outbound-only for phase-report delivery.
- Quality baseline verified by Phase 117C: full suite `18063 passed`;
  `fast_green` `4390 passed`.

## What Is Included

- Governed task/session/phase lifecycle.
- Task contracts and repository policy checks.
- Governed commit and push readiness workflows.
- Canonical phase reports and trust validation.
- Repository transition validation and report quarantine.
- Runtime inspection and runtime-snapshot governance surfaces.
- Read-only project intelligence commands.
- Advisory/evidence architecture with explicit non-authorizing
  boundaries.
- Documentation for the frozen v0.2 architecture and release posture.

## What Is Not Included

- No live AI backend invocation.
- No autonomous coding agent behavior.
- No execution capability.
- No shell mediation.
- No Telegram inbound command path.
- No REST API, dashboard, or Web UI.
- No model integration.
- No hidden authorization path through advisory evidence, dry-run
  output, scope matches, notification state, repository skills, or
  model identity.

## Installation

For local development or repository adoption:

```zsh
python3 -m venv .venv
source .venv/bin/activate
pip install -e /path/to/pcae-harness
pcae init
pcae health
pcae check
pcae runtime inspect --json
```

For contributing to PCAE itself:

```zsh
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pcae health
pcae check
python -m pytest -m "fast_green" -n auto -ra --durations=100
```

## Release Validation Baseline

Phase 117C established the current quality baseline:

| Validation | Result |
| --- | --- |
| Focused governance suites | `130 passed` |
| Full suite | `18063 passed` |
| Fast-green suite | `4390 passed` |
| Runtime posture | `Observed`, execution unavailable |
| Registered runtime plugins | `0` |
| Handoff verification | safe to continue |

Phase 117D release preparation re-verified the release-facing
documentation and reran the required release-prep validation gates.
Phase 117E.1 verified and repaired external publication.

## Upgrade Notes

The package metadata reports `0.2.0` for the v0.2.0 GitHub Release.
This release does not publish to PyPI or publish package artifacts.

## Known Boundaries

PCAE intentionally separates evidence, advice, approval, authorization,
execution eligibility, and execution. In v0.2.0, execution eligibility
does not become live execution. Advisory evidence can inform human
review, but it cannot authorize or perform repository mutation.

## Release Status

Released as v0.2.0 by Phase 117E.1.
