# Phase 93D Complete — Shell Gate Audit Persistence Design

## Summary

Phase 93D defines how Phase 93C audit evidence should be persisted as durable
audit artifacts in `.pcae/shell-gate-audit/`. Design-only — no implementation.

## Design Decisions

- Individual JSON files with timestamped naming
- `latest.json` pointer (matches phase-reports convention)
- SHA-256 per-record digest for tamper detection
- Redacted commands only; no raw secrets persisted
- Broker event cross-reference via broker_event_id
- Audit persistence failure is non-fatal to shell-gate check
- Retention: 100 max files, 30-day age limit

## Future CLI

- pcae shell-gate audit show --latest
- pcae shell-gate audit list --limit N
- pcae shell-gate audit verify

## Non-Goals

No implementation of persistence, shell interception, wrappers, enforcement,
backend invocation, or command execution.

## Recommended Next Phase

93E — Shell Gate Audit Persistence Implementation
