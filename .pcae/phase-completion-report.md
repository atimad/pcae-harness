# Phase 149O.1R Complete — Phase Report Evidence-Coherence Validator + Suppression Plumbing Repair

**Phase ID:** 149O.1R
**Mode:** cross-cutting phase-report trust implementation repair (production + tests)
**Predecessor:** 149O.1H.1R (HATP Repair Phase Evidence-Coherence / Canonical Report Trust Repair — completed, verdict `NOT REPAIRED`, root-caused the failure to two report-generation defects and recommended this bounded repair)
**Date:** 2026-08-06
**Status:** completed
**Pushed:** pending
**origin/main..HEAD:** pending

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_1R_PHASE_REPORT_EVIDENCE_COHERENCE_VALIDATOR_REPAIR.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149O.1H.1 repaired exactly the two Blocking findings Phase
149O.1H's independent verification recorded (not repaired) in
`src/pcae/core/human_approval_trusted_provenance.py` (Wave 3). Both
defects were independently reproduced against the unmodified module
first, then repaired.

**B-149O.1H-1 CLOSED** — timestamp canonicalization was not injective:
the canonical renderer truncated (not rounded) to millisecond
precision, so two individually-accepted, sub-millisecond-apart
`issued_at` instants (`.0001Z` vs `.0009Z`) canonicalized to identical
bytes/digest. Repaired by narrowing the accepted `issued_at` domain
instead of the canonical format: a new shared `_require_issued_at`
validator rejects any timestamp carrying non-zero fractional-second
precision below one millisecond, before model acceptance. The
millisecond-precision canonical renderer and every pre-existing golden
vector are byte-unchanged; independently re-confirmed by recomputing
the AG3/AG5 golden digests directly from `test_hatp_canonical_
serialization.py`'s own fixture constants.

**B-149O.1H-2 CLOSED** — direct dataclass construction enforced
strictly less than `parse_hatp_proof` (only AG3/AG5 family agreement
was checked in `__post_init__`). Repaired via a shared `_require_*`
validator layer (`_require_proof_version` with an explicit `bool`
exclusion for the boolean-is-int-subclass trap,
`_require_repository_instance_id`, `_require_rollback_site`,
`_require_issued_at`, plus the pre-existing `_require_nonempty_str`/
`_require_sha256_hex`/`_require_commit_sha`) called from both
`parse_hatp_proof` and every model's `__post_init__`
(`HumanApprovalProvenanceProof`, `Ag3OperationReference`,
`Ag5OperationReference`), so direct construction now enforces the
identical structural domain the parser enforces.

Zero contract text, zero Wave-1/2/RAE/Permission-Broker/agent file
changes (`git diff --name-only HEAD --` against each: empty).
93 new tests in
`tests/test_phase_149o_1h_1_hatp_timestamp_constructor_domain_hardening.py`;
8 tests in the 149O.1H independent-verification suite updated in place
(not deleted) to record the before/after flip, following the same
convention 149O.1F.1 used for its own historical verification suite.

**F-149O.1C-1** remains independently confirmed implemented (untouched
by this repair). Regressions: Wave-3 pre-existing suites 100 passed
(unchanged); 149O.1H suite 166 passed (unchanged total); new repair
suite 93 passed; combined 359 passed; foundation 103 passed (unchanged);
149O.1F.2 suite 90 passed (unchanged); RAE/Permission-Broker/agent
regression 5 failed/5631 passed (identical count to 149O.1H's own
baseline, same pre-existing unrelated failures); Fast Green 4531 passed
(identical to entering baseline, no regression). Runtime remains
Observed / observe / unavailable throughout.

**Wave-3 repair verdict: HATP WAVE 3 BLOCKING FINDINGS REPAIRED — READY
FOR INDEPENDENT RE-VERIFICATION** (self-assessment only; Wave 3 status
is REPAIRED — PENDING INDEPENDENT RE-VERIFICATION, not VERIFIED). HATP
PRODUCTION remains NOT READY. `B-149O-1` through `B-149O-4` remain
OPEN, unaffected. `F-149O.1C-2` remains editorial debt only. HATP-001
v1.0 remains byte-unchanged.

**Recommended next phase:** 149O.1H.2 — HATP Proof Models + Canonical
Serialization Independent Re-Verification (Wave 4 must not begin until
this independently re-verifies both repairs from scratch).

See
`docs/PHASE_149O_1H_1_HATP_TIMESTAMP_CANONICALIZATION_CONSTRUCTOR_DOMAIN_HARDENING.md`
for the full analysis.
