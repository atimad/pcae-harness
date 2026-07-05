# PCAE Canonical Artifact Promotion

## Purpose

Canonical artifact promotion is the final repository-state step after a
transition has been validated and certified. Phase 114A implements the first
promotion pipeline for phase reports only.

No repository artifact should become canonical by writing `latest.*` directly.
Canonical artifacts must move through the promotion lifecycle:

Draft -> Validated -> Certified -> Canonical

Rejected and Quarantined artifacts are terminal non-canonical states. They may
remain available for diagnosis or forensic review, but they must never update
canonical `latest.*` pointers.

## State Machine

Implemented states:

- `draft`
- `validated`
- `certified`
- `canonical`
- `rejected`
- `quarantined`

Allowed transitions:

| From | To |
| --- | --- |
| Draft | Validated, Rejected |
| Validated | Certified, Rejected, Quarantined |
| Certified | Canonical, Quarantined |
| Canonical | terminal |
| Rejected | terminal |
| Quarantined | terminal |

Only `certified -> canonical` may write canonical artifact paths.

## Promotion API

The reusable implementation lives in
`src/pcae/core/canonical_artifact_promotion.py`.

Primary API:

- `promote_artifact(...)`
- `quarantine_artifact(...)`
- `can_transition(...)`

`promote_artifact(...)` accepts an artifact type, artifact ID, source state,
versioned artifact paths, and canonical artifact paths. It writes files only
when `source_state == ArtifactState.CERTIFIED`.

All other source states fail closed:

- rejected artifacts do not write versioned or canonical artifacts
- quarantined artifacts do not write versioned or canonical artifacts through promotion
- draft and validated artifacts do not become canonical

`quarantine_artifact(...)` writes quarantine paths only. It never writes
canonical paths.

## Phase Report Integration

Phase reports are the first artifact class routed through this promotion
pipeline:

- `write_phase_report(...)` renders timestamped report artifacts and canonical
  `latest.md` / `latest.json` through `promote_artifact(...)`
- `write_quarantined_report(...)` writes only quarantine artifacts through
  `quarantine_artifact(...)`

Successful report output remains compatible: valid phase completions and task
finish report finalizations still produce timestamped markdown/JSON artifacts
and `latest.md` / `latest.json`.

Rejected and quarantined reports never overwrite `latest.md` or `latest.json`.

## Future Artifact Classes

The promotion API is intentionally artifact-type neutral. Future artifact
classes can reuse it by supplying their own artifact type, artifact ID,
versioned paths, canonical paths, and rendered content.

114A intentionally does not integrate unrelated artifact classes yet.

## Compatibility Boundaries

This promotion hardening does not modify:

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
