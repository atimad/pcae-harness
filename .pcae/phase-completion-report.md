# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R Complete — Privileged Production Factory Consumer-Authenticity Blast-Radius Reconstruction and Normative Repair Adjudication

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R`
- Alias: **N16-5-F-5-B2** (operator readability only; the full canonical CPIPC id is authoritative in task state, lifecycle, reports, completion metadata, evidence, and canonical project status)
- Status: **COMPLETE** — read-only / architecture-and-normative-adjudication (no `src/pcae`/`scripts`/contract-text mutation)
- Predecessor: **N16-5-F-5-B1-IV** (COMPLETE — verification-only; F-5-B1: NOT VERIFIED / BLOCKED)
- B2_0 (phase-entry SHA) = `7b744ebadbfc19860b55e6040adff4122cd12494`

## Verdict

- **F-5-B1: still NOT VERIFIED / BLOCKED (unchanged)**
- **F-5: CERTIFICATION BLOCKED PENDING F-5-B2 REPAIR (successor N16-5-F-5-B2-IMPL)**
- **N-16-5: NOT CLOSED**
- **N-16-6 / N-16-7: OPEN / UNTOUCHED (N-16-7 strictly last)**

## What was found

Exhaustively inventoried every `_detect_caller_module`/`_caller_module` use in the
repository (exactly 2 source files) and found **four** privileged factories share the
ungated primitive, not the three previously reported: `production_writer`,
`certification_writer`, `recognized_certification_read_authority`,
`mint_protected_presentation_evidence_writer`. Freshly reproduced the consumer-identity
spoof directly against each of the four (disposable `tmp_path`-scoped protected roots
only) from a diagnostic test module that is a member of no consumer allowlist:
`production_writer`, `certification_writer`, and `mint_protected_presentation_evidence_writer`
each return a genuine, fully-usable writer capability to the spoofing caller
(classification **B — full authority**); `recognized_certification_read_authority`
returns a genuine read handle but escalation to `.writer(...)` remains independently
denied (classification **A — partial gate**, re-confirming F-5-B1-IV). The static
source-scanning guard is exactly 2 hits in `src/pcae`, both the legitimate coordinator
forwarding sites — confirmed as a repository-local fact, not a runtime boundary.

**H-3 reconciled precisely, not restated:** source/contract/five-role semantics
unchanged, but H-3's **consumer-authenticity assurance is INVALIDATED** — an ordinary
caller obtains a full `CertificationWriterHandle` directly from `certification_writer`,
not merely via escalation from a different authority object as previously examined.

**Contract already sufficient:** `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
§32 already defines factory-consumer recognition as "the importing / calling source
module" — "a build-time / import-time fact" — reused by reference across all four
factories via one contract. **Verdict: IMPLEMENTATION BUG UNDER SUFFICIENT CONTRACT →
IMPLEMENTATION-ONLY REPAIR SUFFICIENT** (single-contract). Five candidate repair
architectures were compared without preselecting one; the evidence-supported direction
reuses existing PCAE trust machinery and requires no second trust root. Full detail,
the per-factory matrix, and the contract citations are in the canonical report:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_N16_5_F_5_B2.md`.

## Evidence

- Fresh diagnostic suite: **14/14 passed** (`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_n16_5_f5b2.py`), including live spoof reproduction for all four factories.
- `git diff --name-only 7b744eba..HEAD -- src/pcae scripts pyproject.toml docs/contracts` — EMPTY, confirmed by the suite's own `test_31`.
- Static-guard hit count confirmed exactly 2 (both legitimate) via direct `git grep`, encoded as `test_20`.
- Contract §32 text confirmed present byte-for-byte via direct file read, encoded as `test_30`.
- No production, contract, dependency, or protected-host state changed. No real ceremony, no live protected-root mutation, no FIDO2/YubiKey interaction anywhere in this phase.

## Required successor (derived, NOT begun)

**N16-5-F-5-B2-IMPL** — *Privileged Production Factory Consumer-Authenticity Repair* —
repair the consumer-authorization check for all four affected factories atomically
under the shared HPAC-PAWA-001 §32 predicate, followed by a dedicated re-verification
IV before any fresh **N16-5-FINAL-CERT** (a new CPIPC-valid id, never a reused
completed/blocked one) may be authorized. Do not begin N16-5-F-5-B2-IMPL in this phase;
it requires its own explicit human authorization. REPORTING-UX-1 remains open
(non-blocking). N-16-6 / N-16-7 remain OPEN / UNTOUCHED; N-16-7 strictly last.

## Governance

- Tests run: 14 (fresh diagnostic suite)
- Pushed: pending
- Phase commits: `c6863828`, `6c7b1745`, `8a94ecbe`
