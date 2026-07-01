# Phase 99A — Governed Execution Attempt Boundary Design

## 1. Purpose

Design the boundary model for a future governed execution attempt. Define what
PCAE would consider an "execution attempt," which prerequisites must exist,
which hard no-go conditions always block it, how attempts are identified and
audited, and how deny/abort/fail-closed behavior works.

**Boundary design only. No execution. No enforcement.**

## 2. Governed Execution Attempt Definition

A governed execution attempt is a **future**, explicitly scoped, human-approved,
audited, rollback-aware operation that would seek permission to cross from
evidence-only preflight into an execution-capable boundary.

**No such boundary exists yet.** 99A does not create it, enable it, or authorize it.
99A only defines the boundary, vocabulary, and evidence expectations.

## 3. Non-Attempt Activities

The following are NOT execution attempts:
- Reading docs, inspecting repo state, generating reports
- Running tests through the normal development lifecycle
- Generating Phase 97/98 preflight artifacts
- Showing/verifying artifacts, computing digests
- Writing evidence-only dry-run artifacts, phase reports
- Sending outbound Telegram notifications
- Governed commits/pushes under existing PCAE lifecycle

These activities must not be confused with permission for AI backend execution,
adapter execution, shell mediation, apply, rollback, commit, or push.

## 4. Attempt Lifecycle (14 valid states)

| State | Meaning |
|---|---|
| `unavailable` | Attempt concept not available |
| `not_requested` | No attempt has been requested |
| `request_drafted` | Attempt request drafted, not yet preflighted |
| `preflight_required` | Preflight evidence required before consideration |
| `preflight_failed` | Preflight evidence failed verification |
| `approval_required` | Human approval required |
| `audit_required` | Audit readiness required |
| `rollback_required` | Rollback readiness required |
| `denied` | Attempt denied (no-go, missing evidence, unsafe) |
| `aborted_before_execution` | Aborted before any execution boundary |
| `blocked_by_no_go` | Hard-blocked by no-go conditions |
| `blocked_by_missing_evidence` | Hard-blocked by missing prerequisites |
| `blocked_by_failed_verification` | Hard-blocked by failed verification |
| `ready_for_design_review_only` | Design review ready, not execution ready |

**9 future-only states** never available: `executing`, `executed`, `running`,
`invoked`, `applied`, `committed`, `pushed`, `success`, `execution_complete`.

## 5. Hard No-Go Conditions

Non-overridable: missing/invalid 97/98 preflights, unsafe auth flags, no-go
conditions, missing/expired/revoked approval, missing audit/rollback, failed
verification, unknown schema, conflicting safety flags, requested
backend/adapter/subprocess/shell/network/Telegram-inbound/apply/rollback/
commit/push, bypass permissions, secret material.

## 6. Denial Reasons (26)

`denied_missing_phase97_preflight` through `denied_secret_material_detected`.
All denial keeps authorization flags False. All denial is fail-closed.

## 7. Model

`GovernedExecutionAttemptBoundary` — design-only, non-executing dataclass.
14 attempt states, 26 denial reasons, 12 auth flags (all False), SHA-256 digest.

## 8. Tests (20)

`test_governed_execution_attempt_boundary.py`: design-only invariants, state
validation, denial semantics, digest, safety, no-execution guards.

## 9. Next Phase

**99B — Governed Execution Attempt Contract Freeze**
