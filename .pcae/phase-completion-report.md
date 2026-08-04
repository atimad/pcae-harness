# Phase 149M Complete — Rollback Approval Evidence Implementation Independent Verification

**Phase ID:** 149M
**Mode:** Independent production implementation verification (verification-only;
zero `src/pcae/**` changes, zero `docs/contracts/**` changes; no repair,
no AG3/AG5 wiring, no rollback execution behavior change)
**Predecessor:** 149L (Rollback Approval Evidence Implementation —
completed, verdict RAE EVIDENCE SUBSTRATE IMPLEMENTED — READY FOR
INDEPENDENT VERIFICATION)
**Date:** 2026-08-04
**Status:** completed
**Pushed:** pushed

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149M_ROLLBACK_APPROVAL_EVIDENCE_IMPLEMENTATION_INDEPENDENT_VERIFICATION.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149M independently verified Phase 149L's production implementation
of RAE-001 v1.0's approval-evidence substrate
(`src/pcae/core/rollback_approval_evidence.py`,
`src/pcae/schema_resources/rollback_approval/**`). Independently
reconstructed 149L's exact production diff against the pre-149L baseline
(`1ece0258`): one new module, four new schema/manifest files, one
additive `schema_resources/__init__.py` accessor — no `UNRELATED` hunk.
Independently re-confirmed `agent.py`, `commands/agent.py`,
`mutation_permission.py`, `permission_broker_foundation.py`,
`permission_broker.py`, and `docs/contracts/**` byte-unchanged.

Built a dedicated, independently-constructed adversarial test suite
(`tests/test_phase_149m_rollback_approval_evidence_implementation_independent_verification.py`,
53 tests, no fixture reuse from 149L's own new test files) attacking
canonicality/provenance, AG3/AG5 exact-match binding, family lock, the
`approval_present` strict conjunction, TTL/timezone boundaries,
revocation, supersession, replay/retry, lookup ambiguity, path
traversal, digest tampering, authority validation, and fail-closed
behavior.

**Found four BLOCKING defects, all one root cause**: the module's
canonicality enforcement reduces to digest self-consistency plus
reference to a real CHGR record's *declared* fields — never proof the
record was produced by the legitimate creation API
(`create_rollback_approval_binding`/`create_rollback_approval_decision`/`PublicationCoordinator`).

1. **F1** — A hand-authored Binding file, written directly into the
   canonical `bindings/` directory (bypassing
   `create_rollback_approval_binding` entirely), referencing a genuine,
   real published Decision but with an arbitrary
   `rollback_operation_reference`, resolves `VALID`/`approval_present=True`
   — bypassing RAE-REQ-019's at-most-one-active-Binding-per-Decision
   rule, which is enforced only at the creation-API call site, never at
   resolution time.
2. **F2** — A fully hand-authored CHGR-record-shaped file, written
   directly to CHGR's own `records/` path (no Confirmation, Authorization
   Event, or Publication having actually occurred), is accepted as
   canonical by `_resolve_decision_ref`; a Binding referencing it —
   created through the real `create_rollback_approval_binding` API —
   resolves `VALID`/`approval_present=True`.
3. **F4a** — A verbatim byte-for-byte copy of a legitimate Binding's
   serialized content, placed under a brand-new `evidence_id` filename,
   resolves `VALID` under that new filename — the store's filename-keyed
   lookup and the payload's internal `evidence_id` field are never
   cross-checked.
4. **F4b (HIGH PRIORITY)** — A hand-authored Binding with a forged later
   `created_at`, referencing the same real Decision and the same
   operation reference as a legitimate, still-fresh Binding, causes the
   legitimate Binding to resolve `SUPERSEDED` — a working
   denial-of-evidence attack requiring only filesystem write access to
   the already-canonical evidence directory.

One **NON-BLOCKING** regression, independently reproduced against the
pre-149L baseline in an isolated worktree: 149L's module docstring's
prose mention of `pcae.cltr.authority.*` (explaining what the module does
**not** import) trips three unrelated, naive string-scanning TAM/CLTR
regression-guard tests (`test_136z_no_production_module_string_references_authority_import`,
two `test_...no_production_...module_imports_authority_package` variants)
that 149L's own phase report did not surface. No actual import boundary
violation exists (independently AST-confirmed).

All other RAE-001 v1.0 dimensions were independently verified
**CONFORMS**: closed decision/validation-result vocabularies; AG3/AG5
exact-match operation binding; cross-family and unknown-family rejection;
denied-decision handling; missing-evidence handling; TTL boundary
(inclusive-stale-at-24h, confirmed via the module's own private
frozen-clock test hook); malformed/future/naive-timestamp rejection;
revocation; fail-closed validator-error handling; strict-conjunction
derivation; zero Permission Broker/`mutation_permission`/`agent`/Runtime-Enforcement
import (AST-confirmed); and the disclosed human-trust STRATEGIC_GAP
honestly preserved, not overclaimed.

Regression suites: 149L self-tests 77 passed (unchanged); 149J regression
49 passed (unchanged); CHGR 226 passed / 2 pre-existing (independently
reproduced against pre-149L baseline); TAM/CLTR 5672 passed / 61 failed
(58 pre-existing, 3 new — all the F5 finding above); IWC 693 passed;
AESIC 431 passed (unchanged); Permission Broker 981 passed (unchanged);
rollback 461 passed / 4 (this phase's own confirmed findings); Wave-1 34
passed; Fast Green 4391 passed (unchanged). Runtime reconfirmed
Observed/observe/unavailable before and after.

**Verdict: NOT VERIFIED — BLOCKING RAE-001 IMPLEMENTATION FINDINGS.**

**Integration readiness: NOT READY** for AG3/AG5 rollback-integration
planning until F1/F2/F4 are repaired.

Recommended next phase: **149N — Rollback Approval Evidence
Canonical-Provenance Hardening** — a narrowly-scoped repair phase closing
F1/F2/F4a/F4b/F5, followed (only after it verifies clean) by a dedicated
integration-planning phase for AG3/AG5. Implementation should not proceed
directly. See
`docs/PHASE_149M_ROLLBACK_APPROVAL_EVIDENCE_IMPLEMENTATION_INDEPENDENT_VERIFICATION.md`
for full detail.
