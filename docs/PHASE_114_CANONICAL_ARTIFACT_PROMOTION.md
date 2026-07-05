# Phase 114A — Canonical Artifact Promotion & Quarantine Hardening

## Status

Completed.

Phase 114A implements the canonical artifact promotion pipeline for phase
reports. It hardens the step after Repository Transition Validator acceptance:
certified reports may become canonical, while rejected and quarantined reports
remain non-canonical.

## Promotion Summary

Added `src/pcae/core/canonical_artifact_promotion.py`, a reusable promotion
module with:

- `ArtifactState`
- frozen state-transition rules
- `promote_artifact(...)`
- `quarantine_artifact(...)`
- structured promotion diagnostics

The module is generic enough for future artifact classes, but this phase
integrates only phase reports.

## Artifact Lifecycle

The implemented lifecycle is:

Draft -> Validated -> Certified -> Canonical

Terminal non-canonical states:

- Rejected
- Quarantined

Only `Certified -> Canonical` writes canonical artifact paths.

## Phase Report Integration

`write_phase_report(...)` now routes timestamped report writes and
`latest.md` / `latest.json` writes through `promote_artifact(...)`.

`write_quarantined_report(...)` now routes quarantine writes through
`quarantine_artifact(...)`.

Successful lifecycle behavior is preserved: accepted phase reports still
produce the same timestamped markdown/JSON artifacts and `latest.*` outputs.
The promotion step is now explicit and deterministic.

## Quarantine Summary

Quarantined phase reports remain under `.pcae/phase-reports/quarantine/`.
They retain diagnostic blockers and report content for forensic review.

Quarantined artifacts:

- never become canonical
- never overwrite `latest.md`
- never overwrite `latest.json`

Rejected artifacts likewise never write or overwrite `latest.*`.

## Diagnostics

Promotion diagnostics report:

- `validated`
- `certified`
- `promoted`
- `rejected`
- `quarantined`

The phase-report writer returns `promotion_status` in its path result. Existing
callers that use the traditional `markdown`, `json`, `latest_markdown`, and
`latest_json` keys remain compatible.

## Compatibility Guarantees

This phase does not modify:

- notification enforcement
- `pcae push check`
- Runtime Snapshot
- Runtime Inspect
- Permission Broker
- execution runtime
- authorization
- plugins
- Telegram inbound
- REST
- Web UI
- Dashboard

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.

## Validation

Validation completed:

- focused promotion/report compatibility: `172 passed`
- phase lifecycle/report suite: `1039 passed`
- governance/autonomy/runtime/advisory/plugin group: `3830 passed`
- release/lifecycle regression: `1571 passed`
- fast_green: `4390 passed`
- `pcae health`: healthy
- `pcae check`: passed
- `pcae doctor task-memory`: clean
- `pcae push check`: nothing_to_push, health/check passed
- `pcae session bootstrap --compact --profile implementation`: completed
- `pcae runtime inspect --json`: execution availability `unavailable`, runtime state `Observed`, maximum plugin capability `observe`
- `pcae notify status`: checked before and after sourcing Telegram env
- `pcae skill invoke phase-finalization 114A`: resolved, target status completed

## Recommended Next Phase

114B — Notification Enforcement & Idempotency
