# Phase 92D.8.2 — Canonical Completion Artifact Refresh Guard

## Root Cause

92D.8.1 detected mismatches but the workflow was still too easy to misuse: canonical report and metadata could reference a different phase ID, commit timing wasn't tolerant, and validation comparison wasn't check-name-aware.

## Fixes

### 1. Phase ID Freshness

Canonical report must mention the current phase ID. If it mentions a different phase, trust is downgraded.

### 2. Commit Timing Tolerance

Canonical report is written BEFORE `pcae phase complete`, so it can't know the final commit hash. Only flag stale commit references (different commit explicitly labeled as phase commit).

### 3. Check-Name-Aware Validation

Only compare validation totals when the same check name appears in BOTH canonical content and metadata. No false mismatches from unrelated numeric tokens.

## No-Go

No Telegram polling, inbound, remote shell, /run, enforcement, shell interception, wrappers, backend invocation.
