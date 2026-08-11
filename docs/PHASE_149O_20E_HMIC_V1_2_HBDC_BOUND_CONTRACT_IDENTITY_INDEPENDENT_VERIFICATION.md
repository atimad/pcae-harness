# Phase 149O.20E — HMIC v1.2 HBDC Bound-Contract Identity Independent Verification

## 1. Charter

Independent-verification-only phase. Independently determine whether repaired HMIC-001 v1.2 (as amended by 149O.20D and repaired by 149O.20D.1) now makes HBDC-001's deployment-trust semantics certification-visible under all relevant forms of repository-side semantic drift — the decisive invariant being that any authority-relevant HBDC-001 content change must change current HMIC certification-visible identity, without depending on honest version bumping. This phase does not modify HMIC-001, HBDC-001, any other contract, `src/pcae/**`, or `scripts/**`; does not align production; and does not implement, provision, certify, bind, or activate anything real.

## 2. Baseline (149O.20D.1 Result)

- HMIC-001: v1.2, status "FROZEN — HBDC BOUND-CONTRACT IDENTITY EVOLUTION COMPLETE, CONTENT-IDENTITY BINDING REPAIRED (149O.20D.1) — PENDING INDEPENDENT VERIFICATION."
- HMIC-REQ-050: 25 files (24 pre-repair + `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, HBDC-001).
- HMIC-REQ-067 `contract_versions`: 5 members (`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `HBDC-001`).
- HMIC-REQ-145: revised in place from a disclosed residual limitation to CLOSED.
- Requirements: HMIC-REQ-001–145 (145 total). CIVCs: CIVC-1–12 (12 total). Attack matrix: 37 rows (36→37, new row #37).
- Production (`core/hatp_mandatory_certification.py`): `_FROZEN_AUTHORITY_BEARING_FILES` still 24; `_CONTRACT_IDENTITY_FILES` still 4 members. Not aligned by 149O.20D.1 — deliberate, disclosed.
- HBDC-001: v1.0, byte-unchanged through 20D/20D.1.
- Commits: `7564cfc7`, `ea9c3bcd`, `922c7431`. Pushed. `origin/main..HEAD` = 0.

## 3. Initial Inspection (This Phase)

`git status --short` clean; `git status --branch --short` shows `main...origin/main`; `git rev-list --count origin/main..HEAD` = 0. `pcae health` healthy (lock held by `claude-local`). `pcae check` passed. `pcae status coherence` coherent. `pcae doctor task-memory` warnings only (pre-existing tasks/active directory-collapse and tasks/DONE.md backlog, predating this phase, outside this phase's scope). `pcae push check` clean (nothing_to_push). `pcae runtime inspect` Observed / observe / unavailable. `pcae notify status` Telegram configured/enabled/ready. `pcae phase-report show --latest` confirmed 149O.20D.1 completed/complete, pushed, 0 ahead. `pcae phase-report reconcile --phase-id 149O.20D.1` reconciled, marker already_dispatched, no mutation.

## 4. Primary Sources Read

`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` (HMIC-001, all of §0, §17–§20, §39–§41, §49–§52 read directly, in full, for the sections load-bearing to this phase's scope) and `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001, read in full, all 30 sections). `docs/PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_ARCHITECTURE.md`, `..._20B_...FREEZE.md`, `..._20C_...INDEPENDENT_VERIFICATION.md`, `..._20D_...EVOLUTION.md`, `..._20D_1_...REPAIR.md` consulted for phase-history context. Production source read directly: `src/pcae/core/hatp_mandatory_certification.py` (frozen-file constants, digest derivation, contract-identity derivation) and `src/pcae/core/hatp_mandatory_cutover.py` (Wave-F validator caller). The 20D.1 test module was read for stylistic convention only, never imported or trusted as an oracle — this phase's own test module (§13 below) independently re-derives every expected value from live contract text or git history.

## 5. Reconstructed v1.1 Baseline and 149O.20D Diff

`git log --oneline` confirms `5671448a` — "Phase 149O.20D: HMIC v1.2 HBDC Bound-Contract Identity Evolution" — is the exact frozen pre-repair snapshot the governing instruction names. Direct extraction from `git show 5671448a:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`:

- Version header: `**Version:** 1.2`, with no "Repaired by: Phase 149O.20D.1" line — confirms this is the pre-repair, post-evolution snapshot.
- HMIC-REQ-050 fenced enumeration: 24 entries, `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` absent.
- HMIC-REQ-067 (`**HMIC-REQ-067` bold definition, not the header's earlier informal mention): 5 members, including `HBDC-001` — confirming 149O.20D's own 4→5 `contract_versions` widening already landed in this snapshot.
- HMIC-REQ-145 present at this snapshot, disclosing the same-version content-drift gap for `HBDC-001` specifically (pre-repair text, distinct from the live, repaired text).

Independently re-derived §50 (v1.1 baseline, pre-149O.20D): the four-member set `HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001` is confirmed as the pre-20D `contract_versions` baseline both by direct mention in §50's own historical text and by the pre-repair 20D snapshot's `contract_versions` set minus `HBDC-001`. 149O.20D's diff against that baseline is exactly: `contract_versions` 4→5 (+HBDC-001, `HMIC-REQ-067`); requirements 144→145 (+HMIC-REQ-145); attacks 34→36 (+2 rows, #35/#36); CIVC count unchanged at 12 (CIVC-5 text widened in place); HMIC-REQ-050 unchanged at 24 files (149O.20D deliberately did not add HBDC-001's document). This matches the phase prompt's own expected diff exactly.

## 6. B-149O.20D-1 Independently Reproduced

Against the frozen `5671448a` snapshot, this phase's own test module (`tests/test_phase_149o_20e_...py`) independently confirms all four premises, via fresh regex extraction and `git show`, not by re-reading §52's own prose:

- **(A)** `HBDC-001` is a `contract_versions` member at `5671448a` — confirmed (`test_premise_a_hbdc_contract_versions_member_pre_repair`).
- **(B)** The pre-repair binding is version-header comparison only (HMIC-REQ-069's own text at that snapshot names "the named contract's own current, live version header," no digest language) — confirmed (`test_premise_b_pre_repair_binding_is_version_header_comparison_only`).
- **(C)** `HBDC-001`'s document is absent from the pre-repair 24-file HMIC-REQ-050 enumeration, cross-checked against live production's `_FROZEN_AUTHORITY_BEARING_FILES` (still 24, still no Class-B contract path) — confirmed (`test_premise_c_hbdc_absent_from_pre_repair_24_file_enumeration`, `test_premise_c_cross_checked_against_live_production_constant`).
- **(D)** A same-version, content-only mutation is modeled directly against premises B and C: `contract_versions`' stored value is a string comparison unaffected by content bytes; `implementation_scope_digest` never hashes `HBDC-001`'s bytes; neither of a certification's two authority-bearing digest inputs would change — confirmed (`test_premise_d_same_version_hbdc_mutation_invisible_under_pre_repair_semantics`).

**Verdict: DEFECT REPRODUCED.** All four premises independently true against the frozen snapshot; B-149O.20D-1 was real, not an artifact of 149O.20D.1's own framing.

## 7. Existing Four Dual-Bound Contracts — Reconstructed, Not Accepted

Independently re-walked (not inferred from 149O.20D.1's §52 prose): for each of `HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, (1) the contract document appears in HMIC-REQ-050's enumeration, both pre- and post-repair, at byte-identical fenced-block positions; (2) each is a `contract_versions` member, version-header-compared per HMIC-REQ-069; (3) each document's own bytes therefore participate in `implementation_scope_digest` via HMIC-REQ-050 membership, using the identical SHA-256/two-level construction (HMIC-REQ-054–058) as every other frozen file — content-sensitivity here is a direct, structural consequence of digest-set membership, not a separate mechanism; (4) HMIC-REQ-053's own text states this as a deliberate, redundant, non-interchangeable dual binding. **Dual-binding-model verdict: YES** — the established HMIC design is version semantics (`contract_versions`) plus content semantics (`implementation_scope_digest`), two independent identity dimensions, and `HBDC-001` (pre-20D.1) lacked only the second.

## 8. Reconstructed 149O.20D.1 Repair Diff

Diffing the pre-repair (`5671448a`) and live HMIC-REQ-050 sets (`test_live_req_050_includes_hbdc_as_the_only_addition_vs_pre_repair`): the only set difference is `+docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, no removals. HMIC-REQ-145 revised in place to state "Status: CLOSED," with explicit language that closure "does not depend on repository actors honestly bumping HBDC-001's version string." CIVC count unchanged at 12 (CIVC-5 text extended to state uniform five-member digest participation). Attack matrix 36→37 (new row #37, content-drift now `IMPLEMENTATION_MISMATCH`; row #35 revised to reference #37 instead of restating a closed gap; row #36 unaffected). No production or other-contract change. All confirmed by direct extraction, matching the governing instruction's expected diff exactly.

## 9. Versioning Verdict

Independently assessed: HMIC-001 v1.2 was never independently verified, never production-aligned, had no real certification issued against it, and was repaired before its first independent verification. This mirrors the repository's own 149O.19.3R precedent (repairing HMIC-001 v1.0 in place after a `NOT VERIFIED — BLOCKING` verdict, before its first successful independent verification) — repairing an unreleased, unverified version in place is not equivalent to a breaking change to a released one. **In-place v1.2 repair is defensible; no version-bump finding.**

## 10. Requirement / CIVC / Attack Inventory — Freshly Extracted

Live extraction (regex over the live contract text, not copied from any prior test module): requirement IDs exactly `HMIC-REQ-001`–`HMIC-REQ-145`, gapless, unique, 145 total. CIVC invariants exactly `CIVC-1`–`CIVC-12`, 12 total. Attack matrix rows exactly `1`–`37`, sequential, 37 total. All three confirmed mechanically by this phase's own test module, independent of the 20D.1 module's equivalent (but differently-implemented) checks.

## 11. Live HMIC-REQ-050 and `contract_versions` Extraction

Fresh parse of the live contract's fenced HMIC-REQ-050 block: exactly 25 paths, no duplicates. Fresh parse of the live `**HMIC-REQ-067` bold definition: exactly 5 members, `{HMRC-001, HATP-001, HSCE-001, RAE-001, HBDC-001}`. Historical-vs-live diff: HMIC-REQ-050 24→25 (+1, HBDC-001's document, no removals); `contract_versions` (already 5 as of the pre-repair 20D snapshot) unaffected by the 20D.1 repair — this repair touches only `implementation_scope_digest`'s file count, not `contract_versions`' own member count, exactly as §52 states.

## 12. Total Contract Corpus Terminology

Independently verified: `contract_versions` membership is 5; the total frozen normative contract corpus (`HATP-001`, `HMRC-001`, `HMIC-001`, `HSCE-001`, `RAE-001`, `RWMPC-001`, `PBPA-001`, `PBPC-001`, `HBDC-001`) is 9 — distinct counts, confirmed not conflated anywhere in the live text this phase inspected (`test_total_frozen_corpus_is_nine_distinct_from_five_member_contract_versions`).

## 13. HBDC Content Sensitivity — From-Scratch Digest Reimplementation

This phase implemented HMIC-REQ-054–058 from scratch in its own test module (`_independent_digest`), deliberately not calling `derive_implementation_scope_digest` from `hatp_mandatory_certification.py`: SHA-256 of the lexicographically-ordered, null/newline-delimited (`<path>\0<sha256_hex>\n`) concatenation of every HMIC-REQ-050 file's own SHA-256. Canonicalization (the `src/pcae/`-relative vs. repository-root-relative path split) was independently re-derived from the fenced block's own blank-line boundary, not copied from production's bucket-count constant.

Run against a scratch copy of the live 25-file set (never the real working tree):

- Baseline digest is stable/reproducible across repeated computation.
- A one-byte, same-declared-version mutation to `HBDC-001`'s scratch copy changes the digest — **principal repair criterion confirmed.**
- The same one-byte mutation applied individually to each of the four pre-existing bound contracts' scratch copies also changes the digest — **existing protections unweakened.**
- All 25 files individually change the digest under mutation (25/25) — HBDC-001 did not land in a non-functional position.
- Removing the scratch HBDC-001 file raises a hard failure (fail-closed), mirroring HMIC-REQ-059.
- A symlinked HBDC-001 position is rejected by production's own `_resolve_and_reject_unsafe_frozen_file` (HMIC-REQ-061), exercised directly, confirming no HBDC-specific relaxation of the existing symlink/non-regular-file safety discipline.
- HBDC-001's live HMIC-REQ-050 path is exactly `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, appearing once, no alternate alias.

## 14. Same-Version / Version / Contract-ID Drift

**Same-version content drift (attack #37):** confirmed digest-sensitive above (§13); live contract text names `IMPLEMENTATION_MISMATCH` as the expected result, mentioning `HBDC-001` explicitly. **Version drift:** HMIC-REQ-069's live text is unchanged in mechanism — still a `contract_versions` version-header string comparison yielding `CONTRACT_MISMATCH` — independently confirmed still present and still five-entry-scoped. **Contract-ID drift:** modeled as a `contract_versions` key rename/removal, which HMIC-REQ-031's pre-existing closed-schema discipline treats as a missing-required-key `MALFORMED` case (attack #36's own reasoning, unaffected by this repair). **Three-way (ID/version/content) binding: all three independently visible** — ID via closed-schema key presence, version via HMIC-REQ-069, content via HMIC-REQ-050/053/058 digest inclusion.

## 15. HMIC-REQ-063 / Option C

Byte-for-byte comparison of HMIC-REQ-063's live text against the frozen `5671448a` snapshot: **identical**, confirmed by this phase's own diff, not merely asserted. HMIC-REQ-063's own text continues to state `implementation_scope_digest` does NOT verify executed-code/import-shadowing binding — this repair does not, and does not claim to, touch that residual limitation. HBDC-001's own §14 (Option C boundary, HBDC-REQ-040/041) remains conditional on the separately-verified Model-A environment lock (§13, HBDC-REQ-025–039) — no unconditional acceptance introduced. Models B/C/D remain unauthorized under HBDC-001 v1.0 (HBDC-REQ-024).

## 16. Production 24/4 Staleness and Wave-F Caller Reality

Direct inspection of `src/pcae/core/hatp_mandatory_certification.py`: `_FROZEN_AUTHORITY_BEARING_FILES` still asserts `len(...) == 24`; the literal tuple names no `HATP_CLASS_B_DEPLOYMENT_CONTRACT` path. `_CONTRACT_IDENTITY_FILES` still names exactly the four pre-20D members (`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`) — no `HBDC-001` entry. Both confirmed unmodified since 149O.20D.1's own commits. `src/pcae/core/hatp_mandatory_cutover.py` still wires a real call to `validate_active_hatp_mandatory_independent_verification_certification`, feeding `mandatory_consumption_implementation_independently_verified` via `certification_status_satisfies_readiness` (Wave F, confirmed present, not zero-caller as some earlier phase prose once assumed and 149O.20D.1 already corrected). No certification storage exists at `HATPTrustStore`'s production-resolved root on this host — confirmed by direct filesystem inspection, not assumed.

## 17. Fail-Closed Reasoning for the Transitional State

The 25/5-contract-vs-24/4-production divergence is safe because: no real Protected Root exists; no real Class-B provisioning occurred; no environment lock is implemented; no real HMIC certification/binding/revocation state exists anywhere on this host; no Cutover Record or activation marker exists; `HATP_MANDATORY` was never activated; and — because no stored certification exists for either file count to be compared against — no functional readiness decision depends on which of the two (pre- or post-repair) scopes production currently computes over. The Wave-F caller (§16) does not change this: it calls a validator that, on this host, has nothing to validate (no certification files exist), so it fails closed to `False`/non-`VALID` regardless of which frozen-file count is wired in.

## 18. Legacy-Scope / Compatibility-Path Check

No 24-file or four-member "legacy" selector, compatibility flag, or grandfathering path was found anywhere in HMIC-001's live text (`legacy_contracts`, `hmic_v1_1`, `contract_count=4`, `ignore_hbdc`, or equivalent) — HMIC-REQ-050/HMIC-REQ-067 remain "no more, no fewer" with no version-conditional branch. A historical v1.1 (24-file/4-member) or pre-repair-v1.2 (24-file/5-member) certification replayed against the live, repaired semantics fails on `implementation_scope_digest` mismatch — the two-level SHA-256 construction over a different input file list cannot coincide (attacks #33/#34/#36's own reasoning, extended one file-count step, mirrored for the 24→25 case). Both remain hypothetical since no certification exists on this host.

## 19. Findings

**Blocking:** none. Every blocking condition enumerated in the governing phase instruction (§101) was checked against live text and/or a from-scratch reimplementation and found not triggered.

**Non-Blocking:** none new. The terminological placement of normative contract bytes inside `implementation_scope_digest` (a "source implementation" digest also carrying "contract identity" bytes) is a pre-existing, already-disclosed design choice (HMIC-REQ-053, restated for HBDC-001) — not a defect introduced or newly exposed by this repair; this phase does not redesign it for naming elegance, consistent with the governing instruction's own explicit caution against doing so.

**Observations (retained from 149O.20C, not repaired here):** the HBDC deployment-verifier implementation-coverage gaps — effective ACL/group verification, complete authority-bearing ancestor-chain verification, hard-link verification, and the remaining non-blocking 149O.20C items — remain open for a future implementation phase.

## 20. Contract Verdict

**HMIC-001 v1.2: INDEPENDENTLY VERIFIED — HBDC BOUND-CONTRACT CONTENT IDENTITY CONFORMS.**

- **B-149O.20D-1:** INDEPENDENTLY CONFIRMED CLOSED AT CONTRACT LEVEL — PRODUCTION ALIGNMENT PENDING.
- **HBDC-BINDING-GATE:** CONTRACT CONTENT-BINDING INDEPENDENTLY VERIFIED — PRODUCTION 25-FILE / 5-CONTRACT ALIGNMENT PENDING — NOT CLOSED.
- **Class-B:** CONTRACT VERIFIED — NOT PROVISIONED (149O.20C's own verdict, unaffected).
- **HATP production:** NOT READY.
- **W-1 / B-149O.19.3-1:** unaffected, remain exactly as §49/§50 left them, not reopened, not conflated with this phase's own B-149O.20D-1/HBDC-BINDING-GATE identifiers.
- **B-149O-1..4:** unaffected, remain INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED.

## 21. Regression and Test Results

- New independent test module: `tests/test_phase_149o_20e_hmic_v1_2_hbdc_bound_contract_identity_independent_verification.py` — 55 tests, 55 passed, 0 failed. Does not import or reuse the 149O.20D.1 module's expected-value constants.
- 20A–20D.1 regression suites run together: 189 passed, 2 skipped, 1 failed — the 1 failure (`test_phase_149o_20c_...::test_hmic_v1_1_current_version_unchanged`) is 20C's own fixed-version self-check, broken by 149O.20D's own v1.1→v1.2 bump (an intervening phase, not this one) — confirmed pre-existing via `git stash` (identical single failure with this phase's new test file stashed out).
- Broad sweep `-k "hmic or hbdc or 149o_20 or 149o_19_5"` (excluding the pre-existing `fido2`-import collection error in `test_phase_149o_7_...py`): 37 failed / 818 passed / 4 skipped. All 37 confirmed pre-existing and unrelated via `git stash` (identical 37 failed / 763 passed with this phase's new test file stashed out — the 55-test delta is exactly this phase's own new, entirely-passing module) — exclusively the historical fixed-commit/fixed-count "repin debt" class already disclosed in 149O.19.3R onward (contracts whose test modules pin literal 144-requirement/24-file/34-attack/v1.1-version counts that later, independent phases legitimately superseded).
- Fast Green (`pytest -m fast_green`, excluding the same known `fido2` collection error): raw 62 failed / 6459 passed / 4 skipped. Clean deselected citation (all 62 failing node IDs from that same run explicitly deselected by exact ID, via an argv-list subprocess call, not shell string interpolation): 0 failed / 6459 passed / 4 skipped / 62 deselected. The 37 HMIC/HBDC-scoped failures are a subset of the 62, confirmed pre-existing via `git stash`; the remaining ~25 are pre-existing, unrelated failures in older, unrelated phase test modules (e.g. a stale Python-3.9-pinned environment assertion, older HATP-consumption production-caller-count assertions) — none newly caused by this phase, since this phase's only filesystem change is one new, independent, fully-passing test file with no shared import surface capable of affecting unrelated modules' outcomes.
- `pcae check`/`pcae health`/`pcae status coherence` passing throughout.

## 22. Blocking Conditions — Checked, None Triggered

Every condition in the governing instruction's §101 blocking list was independently checked against live text, git history, or a from-scratch reimplementation (§§5–18 above) and found not triggered. No contract, `src/pcae/**`, or `scripts/**` file was modified by this phase; `git status --porcelain` confirms only the new test file and this document are untracked/new, no existing file is dirty.

## 23. No-Provisioning / No-Change Confirmations

No real Class-B provisioning occurred. No real Python-environment lockdown occurred. No real HMIC certification/binding/revocation state was created anywhere on this host. No Cutover Record or activation marker was created or modified. No real `HATP_MANDATORY` activation occurred. No Permission Broker behavior changed. `POL-005` remained unchanged. No `COMP-002` capability was implemented. Runtime remained Observed / observe / unavailable throughout. HMIC-001 and HBDC-001 remained byte-unchanged in the working tree throughout this phase (confirmed via `git status --porcelain` against both files). No `src/pcae/**` or `scripts/**` file was modified. Production's `_FROZEN_AUTHORITY_BEARING_FILES`/`_CONTRACT_IDENTITY_FILES` remain unaligned, unchanged by this phase — that alignment remains the next phase's own, separate obligation.

## 24. Recommended Next Phase

**149O.20F — HMIC v1.2 HBDC 25-File / 5-Contract Production Identity Alignment.** Bounded scope: update `_FROZEN_AUTHORITY_BEARING_FILES` (24→25, adding `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`) and `_CONTRACT_IDENTITY_FILES` (4→5, adding `HBDC-001`) in `core/hatp_mandatory_certification.py` only — no validator semantic change, no admin semantic change, no readiness semantic change, no provisioning, no certification, no activation. To be followed by its own independent verification (149O.20G or repository-conventional equivalent). Only after both complete may Class-B deployment-verifier/provisioning planning be considered — **not recommended directly by this phase.**
