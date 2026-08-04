# Phase 149N Complete — Rollback Approval Evidence Canonical-Provenance Hardening

**Phase ID:** 149N
**Mode:** Bounded production hardening of canonical provenance for RAE-001
evidence (closes all four Phase 149M BLOCKING findings; no AG3/AG5
wiring, no rollback execution behavior change, no contract amendment)
**Predecessor:** 149M (Rollback Approval Evidence Implementation
Independent Verification — completed, verdict NOT VERIFIED — BLOCKING
RAE-001 IMPLEMENTATION FINDINGS)
**Date:** 2026-08-04
**Status:** completed
**Pushed:** pushed

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149N_ROLLBACK_APPROVAL_EVIDENCE_CANONICAL_PROVENANCE_HARDENING.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149N closed all four Phase 149M BLOCKING findings (F1, F2, F4a,
F4b / B-149M-1..4) against the Phase 149L production implementation of
RAE-001 v1.0's approval-evidence substrate
(`src/pcae/core/rollback_approval_evidence.py`). All four findings shared
one root cause: canonicality enforcement reduced to digest
self-consistency plus reference-field agreement, never proof that the
artifact's creating process was the legitimate one.

Repair, exactly one production file touched:

1. **F2 closure** — new `_chgr_record_has_publication_receipt` predicate
   cross-checks a referenced CHGR `record_id` against
   `PublicationRecordStore`'s own `published/<package_id>.json`
   idempotency-marker receipt (the root trust anchor: an
   independently-written artifact produced only at the successful
   conclusion of a real `PublicationCoordinator.execute` call), called
   from `resolve_rollback_approval_evidence`.
2. **F1 closure** — new filename-keyed canonical creation registration
   (`.pcae/rollback-approval-evidence/creation-registry/<evidence_id>.json`),
   written exclusively (`O_CREAT | O_EXCL`) by `create_rollback_approval_binding`
   alone, immediately after the Binding file, with atomic rollback of the
   Binding file if registration fails; checked at resolution time before
   any other RAE-REQ-038 condition.
3. **F4a closure** — the canonicality check is keyed by the store's
   filename-derived lookup key, not the payload's own internal
   `evidence_id` field, so a verbatim copy of a legitimate Binding placed
   under a new filename has no matching registration for that filename.
4. **F4b closure** — `_is_superseded` now filters supersession candidates
   to canonically-created records (same registration check, per
   candidate's own lookup key) before comparing `created_at`, so a
   hand-authored Binding with a forged, later timestamp is never even
   considered a supersession candidate.

Two additional narrow hardenings surfaced while writing adversarial
controls: a malformed file dropped into the canonical `bindings/`
directory no longer poisons resolution of unrelated, legitimate evidence
(directory-injection defense); Binding-creation registration failure
rolls back the just-written Binding file so no orphan-trusted artifact
can exist (atomicity). The non-blocking **F5** finding (docstring prose
containing the literal substring `pcae.cltr.authority.*`, tripping three
naive string-scan TAM/CLTR regression guards) was also repaired by
rewording — no code or import change.

11 new dedicated tests
(`tests/test_phase_149n_rollback_approval_evidence_canonical_provenance_hardening.py`)
independently reproduce and close B-149M-1/2/3/4, each paired with a
positive canonical control, plus directory-injection, atomicity, and
forged-denial-non-interference controls. Phase 149M's own 53-test
adversarial suite, re-run completely unmodified, now passes in full (was
49 passed / 4 failed — the 4 are exactly F1/F2/F4a/F4b). Phase 149L's 77
self-tests pass unmodified (positive-path evidence undisturbed).

Regression suites: 149J 49 passed (unchanged); CHGR 228 passed / 2
pre-existing (unchanged); TAM/CLTR 5675 passed / 58 pre-existing failed
(was 5672/61 — the 3 F5 failures gone); IWC 693 passed; AESIC 431 passed;
Permission Broker 981 passed; rollback 476 passed / 0 failed (149M's own
4 findings now pass); Wave-1 34 passed; Fast Green 4391 passed — all
unchanged or improved, zero new regressions. `git diff --stat` confirms
exactly one production file touched (247 insertions / 11 deletions),
`docs/contracts/**` empty, and the AG3/AG5/Permission-Broker/
mutation-permission boundary files byte-unchanged. No AG3/AG5 Permission
Broker integration exists; no production code consumes
`approval_present`/`derive_rollback_approval_present`/
`resolve_rollback_approval_evidence` outside the module itself. Runtime
reconfirmed Observed/observe/unavailable before and after.

**Verdict: CANONICAL-PROVENANCE HARDENING COMPLETE — ALL 149M BLOCKING
FINDINGS CLOSED.**

**Integration readiness:** RAE evidence substrate **READY FOR
INDEPENDENT RE-VERIFICATION** (not yet "ready for AG3/AG5 integration" —
reserved for a future verification phase).

Recommended next phase: **149O — Rollback Approval Evidence
Canonical-Provenance Hardening Independent Verification** — must
independently reconstruct and attack all four closed findings without
relying on 149N's own test suite. Do not proceed directly to rollback
integration planning. See
`docs/PHASE_149N_ROLLBACK_APPROVAL_EVIDENCE_CANONICAL_PROVENANCE_HARDENING.md`
for full detail.
