# Phase 149O.20D.1 — HMIC v1.2 HBDC Content-Identity Binding Contract Repair

## 1. Charter

CONTRACT REPAIR / TRUST-MODEL REPAIR ONLY. Repair finding **B-149O.20D-1**: Phase 149O.20D bound `HBDC-001` into HMIC-001's `contract_versions` (HMIC-REQ-067, v1.2) but left its document bytes outside `implementation_scope_digest`, disclosing at HMIC-REQ-145 that a same-version, content-only edit to `HBDC-001` would leave certification identity unchanged — a repository-controlled actor could weaken HBDC deployment rules without necessarily invalidating an existing certification, contradicting the Option-A purpose 149O.20C independently verified. Modifies no `src/pcae/**` file, no `scripts/**` file, and no existing contract other than `HMIC-001` itself (`HBDC-001` byte-unchanged). Implements no production code, no Class-B verifier, no environment lock, no certification, no active binding, no activation.

## 2. Baseline (149O.20D Result)

149O.20D — HMIC v1.2 HBDC Bound-Contract Identity Evolution — completed (commits `a029a672`, `5671448a`, `4d7489db`; pushed; `origin/main..HEAD` = 0). HMIC-001 v1.1 → v1.2: `contract_versions` widened 4 → 5 (`HBDC-001` added, HMIC-REQ-067). HMIC-REQ-145 added, disclosing that `HBDC-001`'s binding is version-header-comparison only — same-version content-only byte drift is not certification-visible. 24-file `implementation_scope_digest` enumeration (HMIC-REQ-050) left unchanged. Production `_CONTRACT_IDENTITY_FILES` still 4-member (disclosed, intentional, fail-closed divergence). Recommended next phase: 149O.20E (independent verification) — not authorized/not started prior to this repair.

## 3. Initial Inspection (This Phase)

```
git status --short                                -> clean
git status --branch --short                        -> ## main...origin/main
git rev-list --count origin/main..HEAD             -> 0
pcae health                                         -> healthy
pcae check                                          -> passed
pcae status coherence                               -> coherent
pcae doctor task-memory                             -> warnings (pre-existing, unrelated — stale tasks/done/ vs tasks/DONE.md sync gaps, predating this phase)
pcae push check                                     -> nothing_to_push
pcae runtime inspect                                -> Observed / observe / unavailable
pcae notify status                                  -> telegram configured/enabled/ready
pcae phase-report show --latest                     -> 149O.20D, completed, complete, pushed, origin/main..HEAD 0
pcae phase-report reconcile --phase-id 149O.20D     -> reconciled, mutation: none (inspection only)
```

All expected preconditions confirmed: repo clean, in sync with origin, 149O.20D completed, HMIC-001 v1.2, HMIC-REQ-145 present, production still 4-member `contract_versions`, HBDC absent from the 24-file digest set, no real provisioning/certification/activation, HATP NOT READY, runtime Observed/observe/unavailable.

## 4. Primary Sources Read

Read in full, directly: `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` (HMIC-001 v1.2, all 51 sections, 145 requirements, 12 invariants, 36-row attack matrix, §49/§50/§51 historical amendment sections — read before any edit was made); `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001 v1.0, all 30 sections, §17's own "Rejected alternatives" analysis in particular); `docs/PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_ARCHITECTURE.md`; `docs/PHASE_149O_20B_HATP_CLASS_B_DEPLOYMENT_CONTRACT_FREEZE.md`; `docs/PHASE_149O_20C_HATP_CLASS_B_DEPLOYMENT_CONTRACT_INDEPENDENT_VERIFICATION.md`; `docs/PHASE_149O_20D_HMIC_V1_2_HBDC_BOUND_CONTRACT_IDENTITY_EVOLUTION.md`. Read production source directly: `src/pcae/core/hatp_mandatory_certification.py` (`_FROZEN_AUTHORITY_BEARING_FILES`, `assert len(...) == 24`, `_CONTRACT_IDENTITY_FILES`).

## 5. Defect Independently Reproduced (Before Editing)

Confirmed all four premises directly against the pre-repair git snapshot (commit `5671448a`) and live production, not assumed from the governing prompt:

| Premise | Confirmed | Evidence |
|---|---|---|
| (A) HBDC-001 is a `contract_versions` member | Yes | HMIC-REQ-067 pre-repair text: "Five entries... under v1.2," names `HBDC-001` |
| (B) Binding is declared-version-only | Yes | HMIC-REQ-069/145 pre-repair text: version-header comparison, not content digest |
| (C) HBDC-001 absent from the 24-file digest set | Yes | HMIC-REQ-050 pre-repair fenced block: 24 lines, no HBDC entry; `_FROZEN_AUTHORITY_BEARING_FILES` (`== 24`) does not name it either |
| (D) Same-version byte mutation is invisible | Yes | Modeled: given (B) and (C), a hypothetical `HBDC-001` byte mutation A→B with Contract ID/Version held constant changes neither binding's stored value — a certification bound to bytes A would continue validating against bytes B |

All four premises true — the finding is real, not reassessed away. Reconstructed the existing four dual-bound contracts' own mechanism (HMRC-001/HATP-001/HSCE-001/RAE-001): each is directly enumerated in HMIC-REQ-050, so its document bytes SHA-256-digest into `implementation_scope_digest` (HMIC-REQ-054/056-058) **in addition to** its `contract_versions` version-header check — HMIC-REQ-053 states this explicitly as a deliberately redundant, non-interchangeable pair of bindings. `HBDC-001` had only the second binding.

## 6. Repair Options Evaluated

| Option | Mechanism | Disposition |
|---|---|---|
| A | New `contract_id`/`contract_version`/`contract_content_digest` schema field | Rejected — requires a new `CertificationRecord` schema field and validation-algorithm step where the existing `implementation_scope_digest` mechanism already provides content-sensitivity without one |
| B | Add HBDC-001's document to `implementation_scope_digest` (HMIC-REQ-050) | **Selected** |
| C | Separate `bound_contract_content_digest` component, scoped to `contract_versions` members only | Rejected — requires the same new schema field as A; the underlying "prefer reusing an existing mechanism over a parallel one" reasoning HBDC-001 §17 already applied to a different (external-manifest) alternative applies with equal force here; would leave the four pre-existing bound contracts covered by two different mechanisms |
| D | Repository-conventional equivalent | None found — every prior "make a file's content certification-visible" case (original 18-file set, B-149O.19.3-1's 4-file repair, W-1's 2-file addition) used HMIC-REQ-050 enumeration |

## 7. Selected Repair — Option B

`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (`HBDC-001`) is the twenty-fifth entry in HMIC-REQ-050's frozen file enumeration, identically to how the other four bound contracts' documents already participate. Rationale: reuses an existing, already-verified mechanism; requires **no** schema change (`implementation_scope_digest` already supports content-sensitivity generically); is the *identical* mechanism HMIC-REQ-145's own pre-repair text already named as the available closing option; does not conflict with HBDC-001's own "Rejected alternatives" text (that rejected a manifest *external* to HMIC-001, not extension of HMIC-001's own existing digest set); does not modify `HBDC-001` itself — its inclusion is achieved entirely by naming its path inside `HMIC-001`'s own enumeration.

## 8. Content-Drift, Version-Drift, and Contract-ID-Drift Semantics

Same `HBDC-001` ID, same declared Version `v1.0`, different normative bytes now changes `implementation_scope_digest` (and therefore `certification_id`) — a certification bound to the pre-mutation digest fails at §31 step 9, yielding `IMPLEMENTATION_MISMATCH` (attack matrix row #37, new). Version-bumped `HBDC-001` revision remains additionally caught by `contract_versions`' version-header comparison (`CONTRACT_MISMATCH`, row #35, revised). Contract-ID mutation remains caught via HMIC-REQ-031's missing-required-key `MALFORMED` path (row #36, unaffected). HBDC-001 missing/unreadable/symlinked/non-regular now falls under the same HMIC-REQ-059/061/062 fail-closed rules as every other frozen file. Both binding mechanisms now apply to all five `contract_versions` members uniformly — HMIC-REQ-053 revised to state this; no `contract_versions` member is exempted.

## 9. Contract Version Decision

HMIC-001 remains **v1.2** — not bumped to v1.2.1/v1.3. Rationale, mirroring the 149O.19.3R precedent (§49 of the contract) for repairing HMIC-001 v1.0 in place after a `NOT VERIFIED` verdict: v1.2 has never been independently verified (149O.20E has not yet run) and no implementation of v1.2 has ever been built or certified against it — repairing a contract before its first successful independent verification is a repair of the same unreleased version, not a breaking change to a released one.

## 10. HMIC-REQ-145 Disposition

Revised in place from a disclosed residual limitation to **CLOSED** — not deleted, not renumbered. States explicitly: the closure does not depend on repository actors honestly bumping `HBDC-001`'s version string; content bytes, not merely a declared version, now determine certification-visible identity. Does not claim to solve HMIC-REQ-063's separate executed-code/import-shadowing limitation, which remains unaffected.

## 11. HBDC-REQ-048 Cross-Check

HBDC-REQ-048's own text sets a floor: "at minimum, its version tracked in `contract_versions`." This repair satisfies that floor (unchanged) and exceeds it — "at minimum" leaves headroom this repair uses; HBDC-REQ-048 is not reinterpreted downward.

## 12. Source/Contract Identity Separation and 24-File Scope

`implementation_scope_digest` continues to bind two categorically different kinds of files under one algorithm (production source under `src/pcae/`, normative-contract documents under `docs/contracts/`), exactly as it already did before this repair — this repair does not blur that distinction, it extends an already-mixed enumeration by one more `docs/contracts/*.md` entry, the identical category the other four contract documents occupy. HMIC-REQ-050's twenty-four-file scope is explicitly, justifiably widened to twenty-five: 149O.20D's own decision to leave it at 24 rested on an "absent proof otherwise" default; this repair phase supplies exactly that proof (B-149O.20D-1). No other file was added, removed, or reordered. `contract_versions` membership remains 5; total frozen contract corpus remains 9 — this repair touches only `implementation_scope_digest`'s file count, not either count.

## 13. Artifact Schema, Canonicalization, Validator, Admin Ceremony — Unchanged Contractually

`CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION`/`CERTIFICATION_BINDINGS_DOCUMENT_SCHEMA_VERSION` remain 1. `CertificationRecord`/`CertificationBinding` field sets unchanged — `implementation_scope_digest` remains a single SHA-256 hex field; only the file *set* HMIC-REQ-058 hashes grows by one. `CertificationStatus` vocabulary unchanged — `IMPLEMENTATION_MISMATCH` already exists and suffices. Validation algorithm's structural shape unchanged — step 9 recomputes over 25 files. HMIC-REQ-055/056/057 already fully specify canonicalization for any HMIC-REQ-050 entry, including the twenty-fifth — no ambiguity introduced. `certification_id`'s derivation algorithm (HMIC-REQ-038) is unchanged; its *values* will differ post-alignment, an expected consequence of a wider digest input. No caller-suppliable HBDC digest/version override exists or is introduced; a future validator/admin ceremony derives HBDC-001's content contribution fresh from live bytes, identically to every other frozen entry — none of this is implemented by this phase.

## 14. Requirement / CIVC / Attack Inventory — After Repair

Requirement IDs: `HMIC-REQ-001`–`HMIC-REQ-145` (145 total, unchanged — no new ID minted; HMIC-REQ-050/052/053/069/145 revised in place). CIVC invariants: `CIVC-1`–`CIVC-12` (12 total, unchanged — CIVC-5 strengthened in place). Attack matrix: 36 → **37** rows (one new: #37, HBDC same-version content drift now `IMPLEMENTATION_MISMATCH`; #35 revised in place to point to #37 instead of restating the closed gap; #36 unaffected).

## 15. Existing Four Contracts — Protections Preserved

`HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001`'s positions within HMIC-REQ-050, their digest inputs, and HMIC-REQ-053's redundancy rule are byte-identical before and after this repair — independently confirmed via diff of the pre-repair (`5671448a`) and live enumerations: the only set difference is the single new `HBDC-001` entry.

## 16. HMIC-REQ-063 / Option C — Unaffected, Not Solved

HMIC-REQ-063's text is byte-identical before and after this repair (independently diffed against the `5671448a` snapshot). This repair concerns normative-contract semantic drift for a `contract_versions` member's document, not executed-source provenance or import-shadowing — that limitation remains named, disclosed, unsolved. Option C remains exactly as conditional as 149O.20A/149O.20C/149O.20D established; Model A remains the sole HBDC-001-authorized deployment model.

## 17. Production Remains Stale — Fail-Closed, Disclosed

`_FROZEN_AUTHORITY_BEARING_FILES` still asserts `== 24`; `_CONTRACT_IDENTITY_FILES` still implements the 4-member set — neither was modified by this phase. This is an intentional, disclosed future-phase obligation (`149O.20F`, unchanged in name from 149O.20D's own recommendation), not an oversight. No `certifications.json`/`certification-bindings.json` file exists anywhere on this host (independently re-confirmed by filesystem inspection), so fail-closed holds regardless of which file count or `contract_versions` cardinality production currently computes over.

## 18. HBDC-BINDING-GATE Status

**HBDC-BINDING-GATE: CONTRACT CONTENT-BINDING REPAIR COMPLETE — INDEPENDENT VERIFICATION PENDING — PRODUCTION ALIGNMENT PENDING.** Not CLOSED. `W-1` and `B-149O.19.3-1` remain exactly as §49/§50 of the contract left them, unaffected, not reopened, using a distinct identifier space from this phase's own `B-149O.20D-1`/`HBDC-BINDING-GATE`.

## 19. Regression and Governance Checks

New test module `tests/test_phase_149o_20d_1_hmic_v1_2_hbdc_content_identity_binding_repair.py` (55 tests, all passing) — independently reproduces the pre-repair defect from the frozen `5671448a` git snapshot; verifies the repaired live contract (25-file enumeration, 37-row attack matrix, HMIC-REQ-145 CLOSED); verifies version/Contract-ID drift detection intact; verifies the other four bound contracts' protections unweakened; verifies HMIC-001 remains v1.2; verifies no schema/canonicalization/status-vocabulary change; verifies HMIC-REQ-063 byte-unchanged; verifies HBDC-001 and all seven other pre-existing bound contracts clean in the working tree; verifies no `src/pcae/**`/`scripts/**` file dirty; verifies production remains stale (24 files, 4-member set); verifies HBDC-BINDING-GATE/B-149O.20D-1/W-1/B-149O.19.3-1 status text; verifies requirement/CIVC counts unchanged. The pre-existing `tests/test_phase_149o_20d_hmic_v1_2_hbdc_bound_contract_identity_evolution.py` (149O.20D's own test module) was updated in place — following the 149O.19.3R precedent for repairing an earlier phase's own live-text assertions — to test the current, repaired contract state, while preserving the historical pre-repair 24-file constant, not deleting it (98 tests total across both modules, all passing).

Broad HMIC/HBDC sweep (`pytest -k "hmic or hbdc or 149o_20 or 149o_19_5"`, `test_phase_149o_7_...` excluded — pre-existing, unrelated `fido2` import error in this environment, present identically with and without this repair): repaired state 41 failed / 759 passed / 4 skipped; git-stash baseline (pre-repair) re-run: 23 failed / 723 passed / 4 skipped. Diffed precisely: the 18 additional failures are exclusively pre-existing test modules from earlier phases (149O.19.5B/5E.1-4/5F/5G, 149O.20A, 149O.20C) whose own tests re-derive `implementation_scope_digest`'s file count or a fixed-commit `git diff`/`git status` self-check live against the current contract text — the identical "repin-debt" class 149O.20D's own amendment already caused for earlier-still phases (149O.19.5E.1 onward), not a new class introduced by this repair's own logic. Spot-verified one representative case directly (149O.20A's own `git status --porcelain` self-check): the sole reported offending line is `M docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`, exactly the one contract this repair is chartered to modify.

Fast Green (`pytest -m fast_green`, same exclusion): 68 failed / 6398 passed / 4 skipped. Of the 68: 41 are the broad-sweep set above (18 newly appearing repin-debt, 23 pre-existing); the remaining 27 are entirely in production-source-dependent test files this phase's own zero-`src/pcae/**`-diff (independently confirmed via `git status --porcelain -- src/pcae`, empty) proves cannot be caused by this repair — timestamp-parsing quirks, Python-interpreter-version checks, and rollback-CLI-surface tests unrelated to HMIC-001's text, plus a handful more of the same fixed-commit-self-check class against unrelated pre-phase commits (149O.14, 149O.19.2, 149O.1G). This phase's own 55 new tests, and the 149O.20D module's updated 43 tests, all pass.

## 20. Blocking Conditions — Checked, None Triggered

Same-version HBDC byte drift remains certification-invisible — no (row #37, `IMPLEMENTATION_MISMATCH`). HBDC protection depends only on declared version — no (content digest now required). Caller can provide expected HBDC digest — no. Old 4-member scope selectable — no. HBDC ceases to be mandatory — no. Existing four contract protections weakened — no (byte-identical positions/bindings, independently diffed). Source/contract identity semantics ambiguous — no. Artifact representation noncanonical — no. HMIC-REQ-063 falsely solved — no. Option C unconditional — no. HBDC-001 modified — no. Production code modified — no. Class-B provisioned — no. Environment lock implemented — no. Real certification/binding/activation — no. PB/POL-005/COMP-002 changed — no. Runtime changed — no.

## 21. Required Verdict

```
HMIC HBDC CONTENT-IDENTITY BINDING: REPAIRED AT CONTRACT LEVEL
— SAME-VERSION HBDC CONTENT DRIFT NOW CERTIFICATION-VISIBLE
— PENDING INDEPENDENT VERIFICATION
— PRODUCTION ALIGNMENT PENDING

B-149O.20D-1: REPAIRED AT CONTRACT LEVEL
— INDEPENDENT VERIFICATION PENDING
— NOT CLOSED

HBDC-BINDING-GATE: CONTRACT CONTENT-BINDING REPAIR COMPLETE
— INDEPENDENT VERIFICATION PENDING
— PRODUCTION ALIGNMENT PENDING
```

Not claimed: HBDC binding complete. Not claimed: ready for provisioning.

## 22. Required Next Phase

**149O.20E — HMIC v1.2 HBDC Bound-Contract Identity Independent Verification** (unchanged in name from 149O.20D's own recommendation), scope now additionally including independent verification of this repair: re-confirm B-149O.20D-1's pre-repair defect from the `5671448a` snapshot; independently re-derive that Option B is the correct, sufficient, minimal repair; independently test that a same-version `HBDC-001` content mutation changes `implementation_scope_digest`; independently verify version/Contract-ID-drift detection and the other four contracts' protections; independently verify the 25-file/5-member sets; independently verify HMIC-REQ-063/Option-C preserved; independently verify production remains fail-closed-ly stale at the pre-repair 24-file/4-member sets; confirm no real provisioning/certification/activation occurred. If 149O.20E passes (now covering both the 149O.20D amendment and this repair), next is the bounded implementation-alignment phase 149O.20D already recommended (`149O.20F`), updating both `_FROZEN_AUTHORITY_BEARING_FILES` and `_CONTRACT_IDENTITY_FILES`, followed by that alignment's own independent verification. Only after both complete may Class-B provisioning planning be considered.

## 23. Explicit Confirmations

The repair protects HBDC content, not merely its declared version. A same-version HBDC semantic edit is certification-visible. The protection does not depend on repository actors honestly bumping a version. `HBDC-001` itself remained byte-unchanged during this repair. No production source (`src/pcae/**`) was modified. No `scripts/**` file was modified. No other existing contract was modified. No Class-B deployment/provisioning occurred. No real certification/binding/revocation state was created. No real activation occurred. Runtime remained Observed / observe / unavailable. HATP production remains **NOT READY**.

## 24. W-1 / B-149O.19.3-1 / B-149O-1..4 Status

Unaffected, not reopened, not conflated with this phase's own `B-149O.20D-1`/`HBDC-BINDING-GATE` identifiers — `W-1` remains repaired at the contract level with production alignment/independent verification pending exactly as 149O.19.5E.4 left it; `B-149O.19.3-1` remains independently closed; `B-149O-1..4` remain **INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED**, unchanged by this phase.
