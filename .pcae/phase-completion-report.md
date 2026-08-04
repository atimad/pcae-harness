# Phase 149O Complete — Rollback Approval Evidence Canonical-Provenance Hardening Independent Verification

**Phase ID:** 149O
**Mode:** Independent verification only (no production repair, no contract
amendment)
**Predecessor:** 149N (Rollback Approval Evidence Canonical-Provenance
Hardening — completed, claimed ALL 149M BLOCKING FINDINGS CLOSED)
**Date:** 2026-08-04
**Status:** completed
**Pushed:** pushed

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_ROLLBACK_APPROVAL_EVIDENCE_CANONICAL_PROVENANCE_HARDENING_INDEPENDENT_VERIFICATION.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149O independently reconstructed Phase 149N's exact production diff
(one file, `src/pcae/core/rollback_approval_evidence.py`, no `UNRELATED`
hunk) and independently reproduced all four original Phase 149M findings
(B-149M-1/2/3/4) as CLOSED — 149M's own unmodified 53-test suite: 53/53
passed (was 49/4 before 149N).

Per the governing phase prompt's mandatory "Critical New Adversarial
Question," this phase did not stop at reconstructing the original four
attacks. It directly attacked the two *new* provenance mechanisms 149N
introduced:

1. **CHGR publication receipt** (`_chgr_record_has_publication_receipt`)
   — checks for a `published/<package_id>.json` marker naming the target
   `record_id`.
2. **Binding canonical creation registration**
   (`_binding_is_canonically_created`) — checks for a
   `creation-registry/<lookup_key>.json` file whose declared fields match
   the Binding.

Three independent, live exploits confirmed **BLOCKING**:

1. A fully hand-authored CHGR record paired with a fully hand-authored
   `published/*.json` receipt marker (neither ever produced by
   `PublicationCoordinator`), used with the real
   `create_rollback_approval_binding` API, resolves `approval_present=True`.
2. A genuine, published Decision paired with a fully hand-authored
   Binding and a fully hand-authored, field-matching creation
   registration (never produced by `create_rollback_approval_binding`)
   resolves `approval_present=True`.
3. Both combined — every artifact hand-authored, zero calls anywhere to
   `create_rollback_approval_decision` or `create_rollback_approval_binding`
   — still resolves `approval_present=True`.

Root cause: both new mechanisms' `O_CREAT|O_EXCL` writes guarantee only
race-detection for an *existing* key; neither authenticates a *brand-new*
key's content. B-149M-1/2's forgery target relocated one layer outward
(to `creation-registry/`/`published/`), not removed. This is not
threat-model overreach: 149M's four original attacks already used the
identical "write a self-consistent file into a canonical directory"
capability against `records/`/`bindings/`; 149O applied the same,
already-in-scope capability one hop further along the trust chain 149N
built.

All of 149N's genuine strengths against *mismatched/incomplete*
provenance were independently reconfirmed (missing/orphan/tampered
registration correctly rejected, atomic Binding rollback on
registration-write failure, forged-newer-denial non-interference,
directory-injection hardening, canonical positive control and
supersession) — the hardening is undermined specifically by *fresh,
mutually-consistent forgery of both new artifacts at once*.

17 new independently-authored tests
(`tests/test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py`,
zero fixture/helper reuse from 149L/149M/149N): 13 passed, 4
`pytest.fail("BLOCKING: ...")` documenting the exploits above (plus a
fresh-forgery-under-a-new-key variant), matching 149M's own suite's
convention for a live-reproduced finding.

Also found and worked around (non-blocking, environmental, pre-dates
149N): the committed local `.venv` (Python 3.9.6) cannot execute
`PublicationCoordinator.execute` at all (`fromisoformat` rejects
`Z`-suffixed timestamps pre-3.11); all suite runs in this report used a
disposable Python 3.14.5 venv instead.

Zero regressions across 149M/149N/149L/149J/CHGR/TAM-CLTR/IWC/AESIC/
Permission-Broker/rollback/Wave-1/Fast-Green (all match the 149N baseline
exactly). Zero production/contract changes; AG3/AG5/Permission-Broker
boundary files byte-unchanged. Runtime remains Observed/observe/
unavailable before and after.

**Verdict: NOT VERIFIED — BLOCKING CANONICAL-PROVENANCE FINDINGS.**

**Root-provenance verdict: PROVENANCE ROOT NOT VERIFIED — BLOCKING.**

**Evidence substrate readiness: NOT READY.**

Recommended next phase: **149O.1 — RAE Trusted Provenance Root
Hardening** — narrowly scoped to strengthening
`_chgr_record_has_publication_receipt` and the Binding
canonical-creation-registration check so each ties to a fact a
direct-filesystem-write attacker cannot also fabricate. Classified as an
RAE-local reuse defect, not a `PublicationRecordStore`/CHGR-wide
canonicality defect; no CHGR-001/RAE-001/Permission-Broker boundary
change expected. Do not proceed to a 149P AG3/AG5 integration planning
phase until the provenance root independently re-verifies. See
`docs/PHASE_149O_ROLLBACK_APPROVAL_EVIDENCE_CANONICAL_PROVENANCE_HARDENING_INDEPENDENT_VERIFICATION.md`
for full detail.
