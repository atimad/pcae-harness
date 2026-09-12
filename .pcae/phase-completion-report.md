# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1 — Caller/Client Integration Architecture for Privileged Helper Consumption

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
- Alias: **N16-5-F-5-TB-CALLER-INTEGRATION-ARCH** (operator readability only; the full canonical CPIPC id is authoritative)
- Status: **COMPLETE**
- Predecessor: **N16-5-F-5-TB-REPLAY-STORE-FIFO-HARDEN** (COMPLETE), entry HEAD == `origin/main` == `3be2b318`
- CPIPC: valid direct `.1` successor of the predecessor — independently re-derived via `pcae.core.phase_id` (`is_valid` True; same series `149`; same branch `O`; exactly one appended `.1` segment, 61 vs 60; `compare` = less; exact canonical text; unique against `git log --all -F --grep`; no conflicting active governed phase); alias display-only, no discrepancy

## Summary

Architecture-only phase (no production implementation). Independently
inventoried every current production caller of the HPAC/PAWA
privileged-authority subsystem and every remaining legacy in-process
authority mechanism from primary source. Top-line finding: **zero
orchestration-layer (CLI/agent-reachable) production callers exist
today** — the entire subsystem is a self-contained `src/pcae/core/`
island reached only by 4 standalone, unpackaged `scripts/hpac_*.py`
admin launchers. Exactly four legacy in-process factory functions were
found in `hpac_protected_admin_writer.py` (`production_writer`,
`certification_writer`, `recognized_certification_read_authority`,
`mint_protected_presentation_evidence_writer`), each gated by the
`_detect_caller_module`/`_verified_production_caller_name` frame-pinning
mechanism the predecessor lineage (N16-5-F5B2R2-IMPL) already proved
insufficient. `hpac_certification_coordinator.py` has zero live
production callers today (real ceremony deferred to the not-yet-begun
N16-5-FINAL-CERT), flagged as noteworthy but non-blocking.

Every one of the 5 closed helper operations (`admin_mutation`,
`certification_write`, `certification_read`, `ceremony_entry`,
`presentation_evidence_write`) maps cleanly onto an existing in-process
factory/consumer pair. **No caller was found requiring a sixth
operation or a read outside the closed typed set; no contract/schema gap
was discovered.**

Designed (architecture only, not implemented): the typed client
request-builder architecture, the one-shot transport-client
architecture, launcher design considerations, the platform model
(Linux/macOS-fail-closed/deterministic-NON_REAL), the request
identity/currentness/replay-binding model, timeout/no-auto-retry
semantics, error mapping, response-trust model, no-authority-export
requirement, Gate5/RHAMP/challenge/assertion/proof-verifier integration
flows preserving every named semantic wall, the one-shot process model,
multi-operation orchestration and cross-operation binding, partial-
workflow failure semantics, the absolute no-legacy-fallback rule, a
legacy-path retirement plan, a 6-slice migration order derived from the
actual caller inventory, a concrete first implementation slice, and a
20-row threat matrix.

**Zero production source, contract, schema, or dependency changes this
phase.** The bulk of the source inventory and drafting was performed by
a bounded delegated research worker (read-only, no commit/push/
finalization/task/production-mutation authority); the primary operator
independently re-verified every load-bearing factual claim directly
against source before accepting it (see the canonical Phase Report's
Independent Verification Log).

`fast_green` attribution performed via the governed
`pcae phase fast-green-attribution` tool (isolated-worktree
baseline-vs-candidate comparison). First run against candidate `75f605c4`
produced one attributable node
(`tests/test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record`)
— the same node the immediate predecessor phase's own report
independently documented as spuriously flaky. A `--rerun-node` isolated
rerun passed the node cleanly, `attributable_failures: []`. Final run
against the truly pushed candidate `6900c1a4` (baseline `3be2b318`)
independently reproduced a clean `attributable_failures: []` directly,
no rerun needed. Tool status: **PASS**.

Contract trio byte-unchanged throughout this phase (`git diff` against
`origin/main` for `docs/contracts/` empty). No schema or dependency
change. 0 live protected-host writes; 0 real ceremony; no FIDO2/YubiKey;
no production principal. Runtime `Observed` / `observe` / `unavailable`;
0 plugins / 0 capabilities; first governed runtime external effect
**ABSENT / UNREACHABLE**.

**Verdict: N16-5-F-5-TB-CALLER-INTEGRATION-ARCH COMPLETE.** Caller/client
integration architecture: **DEFINED / READY FOR IMPLEMENTATION**.
Production caller migration: **NOT BEGUN**. Legacy authority retirement:
**PLANNED / NOT BEGUN**. macOS same-file-object execution: **FAIL-CLOSED
/ NOT IMPLEMENTED** (untouched). Helper foundation: **REMAINS
INDEPENDENTLY VERIFIED**. Replay durability: **REMAINS VERIFIED /
HARDENED**. F-5-B2 **BLOCKED PENDING REMAINING PLATFORM / CALLER
MIGRATION / PACKAGING SLICES**; F-5 **CERTIFICATION BLOCKED**; **N-16-5
NOT CLOSED**; N-16-6 / N-16-7 **OPEN / UNTOUCHED** (N-16-7 strictly
last). This phase begins neither the migration itself, macOS
same-file-object implementation, packaging/install, real certification,
N-16-6, nor N-16-7.

Full detail: `docs/PHASE_N16_5_F_5_TB_CALLER_INTEGRATION_ARCH.md`.

## Contract Baseline

| Contract | File | Version |
|---|---|---|
| HPAC-PAWA-001 | `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` | v2.0 |
| HPAC-PAWA-HELPER-001 | `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` | v1.0 |
| HPAC-PPA-001 | `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` | v2.0 |

Byte-unchanged before and after this phase's work (`git diff` against
`origin/main` for `docs/contracts/` empty).

## Production Changes Performed

**None.** This is an architecture-only phase per the authorization
prompt's absolute stop boundary. `git diff` against `origin/main` for
`src/pcae/`, `scripts/`, `docs/contracts/`, `schemas/`,
`pyproject.toml` is empty for the entire duration of this phase.

## Recommended Next

The first concrete implementation slice named in the canonical Phase
Report: a read-only `certification_read` client library
(`src/pcae/core/hpac_pawa_helper_client.py`) migrating
`hpac_verifier.py`'s read path, with the named guard tests. **NOT
begun.** Requires fresh explicit human authorization. Beyond that, per
the absolute stop boundary: no migration of any other operation, no
macOS same-file-object implementation, no packaging/install, no real
certification, no N-16-6, no N-16-7 without fresh explicit human
authorization for each.
