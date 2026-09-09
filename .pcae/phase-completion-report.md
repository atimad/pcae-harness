# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R Complete — Privileged Production Factory Consumer-Authenticity Repair — F-5-B2 Implementation

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R`
- Alias: **N16-5-F-5-B2-IMPL** (operator readability only; the full canonical CPIPC id is authoritative in task state, lifecycle, reports, completion metadata, evidence, and canonical project status)
- Status: **COMPLETE** — F-5-B2 REPAIR IMPLEMENTED / IV PENDING
- Predecessor: **N16-5-F-5-B2** (COMPLETE — read-only/adjudication-only; blast radius reconstructed, contract adjudicated SUFFICIENT)
- I0 (phase-entry SHA) = `585f6b42f3bd221b20f38cd97d41b8d3fc5207ee`

## Verdict

- **F-5-B2: REPAIR IMPLEMENTED / IV PENDING**
- **F-5: CERTIFICATION BLOCKED PENDING F-5-B2 IV (successor N16-5-F-5-B2-IV)**
- **N-16-5: NOT CLOSED**
- **N-16-6 / N-16-7: OPEN / UNTOUCHED (N-16-7 strictly last)**

## What was repaired

Repaired the single shared consumer-identity primitive `_detect_caller_module` in
`src/pcae/core/hpac_protected_admin_writer.py`, the root cause the predecessor's
blast-radius reconstruction identified as shared by all four privileged factories:
`production_writer`, `certification_writer`, `recognized_certification_read_authority`,
`mint_protected_presentation_evidence_writer`. The caller-controlled early return
(`if explicit is not None: return explicit`) was removed; the `_caller_module`
keyword argument is retained on all four factories for signature continuity only
and is now unconditionally ignored — consumer identity is always derived from real
call-stack provenance. This closes the finding for all four factories atomically
since they share one primitive.

No new trust root; no `HPAC-PAWA-001` or other contract byte changed; no
`PawaOperation`/role/failure-code/schema/dependency change; the production
consumer allowlists (`AUTHORIZED_FACTORY_CONSUMERS`, `_TEST_FACTORY_CONSUMERS`,
`_CERTIFICATION_TEST_CONSUMERS`, `_READ_AUTHORITY_TEST_CONSUMERS`) are
byte-unchanged.

## Evidence

- New dedicated suite: **49/49 passed** (`tests/test_phase_n16_5_f5b2_impl_consumer_authenticity.py`) — per-factory spoof denial (exact/near-miss/prefix/suffix/empty/wildcard) and legitimate-caller success via genuine call provenance.
- A/B regression attribution (targeted band, `git stash`-verified immutable baseline): baseline 1770 passed/36 failed vs. repaired-and-committed tree 1824 passed/0 failed attributable to this repair (all 36 baseline failures reproduce unchanged; the sole transient extra failure at the uncommitted stage was a "clean git diff" artifact, independently reconfirmed passing post-commit).
- Load-bearing mutation proof: reverting the fix fails 10/49 new-suite tests; restoring returns 49/49 green.
- Clean-installed wheel (`python -m build --wheel`, disposable `/tmp` venv, external script outside repo/tests tree): caller-supplied-name spoof against all four factories — **4/4 DENIED**; legitimate production path confirmed working from the installed package.
- `git diff --stat -- docs/` — EMPTY (contracts byte-unchanged).
- No production, contract, dependency, or protected-host state changed beyond the one authorized source file. No real ceremony, no live protected-root mutation, no FIDO2/YubiKey interaction anywhere in this phase.
- Full detail, per-factory matrix, mechanism rationale, and threat-model boundary are in the canonical report:
  `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_N16_5_F5B2_IMPL.md`.

## Required successor (derived, NOT begun)

**N16-5-F-5-B2-IV** — *Independent Verification of Privileged Production Factory
Consumer-Authenticity Repair — F-5-B2* — must independently attack all four factories
(including clean-installed external-caller attacks) and re-establish consumer
authenticity for each; must not be split so any one factory remains uncertified. Only
after this IV succeeds may a fresh **N16-5-FINAL-CERT** (a new CPIPC-valid id, never a
reused completed/blocked one) be authorized. Do not begin N16-5-F-5-B2-IV in this
phase; it requires its own explicit human authorization. N-16-6 / N-16-7 remain OPEN /
UNTOUCHED; N-16-7 strictly last.

## Governance

- Tests run: 1823 (targeted regression band) + 49 (new implementation suite)
- Pushed: pushed
- Phase commit: `b88478df`
