# Phase 149O.20D — HMIC v1.2 HBDC Bound-Contract Identity Evolution

## 1. Charter

CONTRACT-EVOLUTION-ONLY phase, per 149O.20C's own recommendation and HBDC-001's own HBDC-REQ-048 prerequisite. Evolve HMIC-001 v1.1 → v1.2 so that HBDC-001 v1.0's deployment-trust semantics become certification-identity-visible: add `HBDC-001` as a fifth `contract_versions` member (HMIC-REQ-067). Modifies no `src/pcae/**` file, no `scripts/**` file, and no other bound contract (HMRC-001/HATP-001/HSCE-001/RAE-001/RWMPC-001/PBPA-001/PBPC-001/HBDC-001 itself). Provisions nothing, certifies nothing, activates nothing.

## 2. Baseline (149O.20C Result)

149O.20C — HATP Class-B Deployment Contract Independent Verification — completed (commits `10406396`, `6f7c32b4`, `dd56fc82`, `4fadf229`; pushed; `origin/main..HEAD` = 0). HBDC-001 v1.0: **INDEPENDENTLY VERIFIED WITH NON-BLOCKING FINDINGS — HATP CLASS-B DEPLOYMENT CONTRACT CONFORMS** (55 requirements, 8 invariants, 21 frozen + 9 additional adversarial attack scenarios, zero Blocking findings). Class-B: **CONTRACT VERIFIED — NOT PROVISIONED**. HBDC-001's self-binding disposition: **Option A independently re-verified correct** — HBDC-001 absent from both `contract_versions` and `implementation_scope_digest`, empirically confirmed against live production source. 149O.20C's own §12 recorded a critical terminology disambiguation, preserved verbatim by this phase (§7 below): the governing prompt's "8 → 9" bound-contract framing describes the **total frozen-contract corpus**, distinct from HMIC-001's own 4-member `contract_versions` field.

## 3. Initial Inspection (This Phase)

```
git status --short                              -> clean
git status --branch --short                      -> ## main...origin/main
git rev-list --count origin/main..HEAD           -> 0
pcae health                                       -> healthy
pcae check                                        -> passed
pcae status coherence                             -> coherent
pcae doctor task-memory                           -> warnings (pre-existing, unrelated — 6 active-task files / tasks/DONE.md sync gaps, predating this phase)
pcae push check                                   -> nothing_to_push
pcae runtime inspect                              -> Observed / observe / unavailable
pcae notify status                                -> telegram configured/enabled
pcae phase-report show --latest                   -> 149O.20C, completed, complete, pushed, origin/main..HEAD 0
pcae phase-report reconcile --phase-id 149O.20C   -> reconciled, mutation: none (inspection only)
```

All expected preconditions confirmed: repo clean, in sync with origin, 149O.20C completed, HBDC verified, Option A independently verified, HMIC still v1.1 at phase entry, HBDC absent from current HMIC contract identity, production `contract_versions` still 4-member, no real deployment/certification/activation, HATP NOT READY, runtime Observed/observe/unavailable.

## 4. Primary Sources Read

Read in full, directly: `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` (HMIC-001 v1.1, all 50 sections, 144 requirements, 12 invariants, 34-row attack matrix, §49/§50 historical amendment sections); `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001 v1.0, all 30 sections); `docs/PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_ARCHITECTURE.md`; `docs/PHASE_149O_20B_HATP_CLASS_B_DEPLOYMENT_CONTRACT_FREEZE.md`; `docs/PHASE_149O_20C_HATP_CLASS_B_DEPLOYMENT_CONTRACT_INDEPENDENT_VERIFICATION.md` (§12's terminology disambiguation in particular). Read production source directly: `src/pcae/core/hatp_mandatory_certification.py` (`_FROZEN_AUTHORITY_BEARING_FILES`, `_CONTRACT_IDENTITY_FILES`, `derive_contract_versions`, `_CONTRACT_VERSIONS_REQUIRED_KEYS`) and `src/pcae/core/hatp_mandatory_cutover.py` (`_assess_hatp_mandatory_activation_readiness_at_root`).

**Discovery not anticipated by the governing prompt, independently found by this phase's own source reading, not assumed from any prior phase-report summary:** `hatp_mandatory_cutover.py` no longer contains the literal hard-coded `mandatory_consumption_implementation_independently_verified = False` ceiling HMIC-001 §49/§50 both describe. Phase 149O.19.5F ("Wave F," gated by Stop Condition W-1, confirmed closed at 149O.19.5E.4 — predating and independent of the 149O.20A–D track) already wired a real, fresh call to `validate_active_hatp_mandatory_independent_verification_certification` into the readiness assessment, mapped via `certification_status_satisfies_readiness`. This phase corrects HMIC-001's own §51 text to state this accurately rather than silently repeating §50's now-stale "zero production callers" framing (§8 below).

## 5. Reconstruction of the v1.1 Baseline (This Phase, Before Editing)

Mechanically re-extracted directly from live contract text and cross-checked against production:

| Item | v1.1 value | Cross-checked against |
|---|---|---|
| Contract version | 1.1 | header line |
| Requirement IDs | `HMIC-REQ-001`–`HMIC-REQ-144`, 144 total, no gaps/dupes | regex extraction |
| CIVC invariants | `CIVC-1`–`CIVC-12`, 12 total | regex extraction |
| Attack matrix | 34 rows, sequential 1–34 | regex extraction |
| `implementation_scope_digest` frozen file set (HMIC-REQ-050) | 24 files, exact | `_FROZEN_AUTHORITY_BEARING_FILES` (`assert len(...) == 24`) |
| `contract_versions` set (HMIC-REQ-067) | `HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001` — 4 members | `_CONTRACT_IDENTITY_FILES` (literal 4-tuple) |

No discrepancy found between contract text and production. The 24-file alignment (`149O.19.5E.3`-class work) has already occurred, prior to this phase.

## 6. Reconstruction of HBDC-001's Status (This Phase)

Directly re-read `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`: HBDC-001 v1.0, 55 requirements, 8 invariants, 21-row attack matrix, `INDEPENDENTLY VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS` (149O.20C). Directly re-read `hatp_mandatory_certification.py`: `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` appears in neither `_FROZEN_AUTHORITY_BEARING_FILES` nor `_CONTRACT_IDENTITY_FILES`. This phase independently confirms 149O.20C's own empirical finding; it does not merely accept it.

## 7. Terminology Precision (149O.20C §12, Preserved Exactly)

The governing prompt's "current HMIC bound-contract set: 8 → target 9" framing describes the **total frozen-contract corpus** — `HATP-001`, `HMRC-001`, `HMIC-001`, `HSCE-001`, `RAE-001`, `RWMPC-001`, `PBPA-001`, `PBPC-001` (8, becoming 9 with `HBDC-001`) — a distinct notion from HMIC-001's own `contract_versions` binding field (HMIC-REQ-067), which is 4 members pre-amendment and **5**, not 9, post-amendment. This phase reports both counts explicitly throughout and never conflates them.

## 8. Option-A Rationale, Re-Derived

HBDC-001 determines whether a Model-A deployment's environment-lock state is sufficient to invoke HMIC-REQ-063's Option-C accepted-residual branch instead of its BLOCKING branch. If HBDC-001's own normative text could be edited — weakened, broadened, an attack row softened — without that edit changing anything HMIC-001's certification identity tracks, an existing `VALID` certification could continue to read as "Option-C conditions independently verified sufficient" while the deployment rules a human reviewer actually approved had since been quietly weakened. This is the identical class of risk `contract_versions` already exists to close for `HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001` (HMIC-REQ-069). HBDC-001 is not a downstream *policy* concern like `RWMPC-001`/`PBPA-001`/`PBPC-001` (HMIC-REQ-068) — it is a prerequisite-topology contract a Model-A certification's Option-C reliance directly depends on. Frozen normatively at revised HMIC-REQ-067 (§20 of the contract).

## 9. HMIC Version Evolution

HMIC-001 v1.1 → **v1.2**. Bound-contract identity semantics materially changed (contract_versions widened 4→5); this is not silently retained as v1.1, consistent with repository precedent (§49/§50's own version-bump discipline).

## 10. Contract Status

HMIC-001 v1.2: **FROZEN — HBDC BOUND-CONTRACT IDENTITY EVOLUTION COMPLETE — PENDING INDEPENDENT VERIFICATION.** Not claimed VERIFIED.

## 11. Bound-Contract Enumeration — Decision and Rationale

HBDC-001 joins `contract_versions` (HMIC-REQ-067 widened 4→5), **not** `implementation_scope_digest` (HMIC-REQ-050 unchanged, exactly 24 files). Three independent reasons: (1) HBDC-REQ-048's own text sets the required floor: *"at minimum, its version tracked in `contract_versions`"* — this phase implements exactly that floor; (2) HBDC-001 §17's own "Rejected alternatives" analysis already rejected introducing a second, parallel protected-binding mechanism for HBDC-001 in favor of reusing `contract_versions`; (3) the governing phase instruction's own repeated default expectation is that the 24-file enumeration remains unchanged unless direct analysis proves otherwise, and no such proof was found — HBDC-REQ-048's literal minimum is fully satisfiable without it.

The original four `contract_versions` members (`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`) are preserved unchanged. The delta is exactly `+ HBDC-001`.

## 12. HBDC Version Binding and Content Digest — Honest Disclosure

HBDC-001's `contract_versions` binding uses the identical mechanism as the other four members: version-header comparison (HMIC-REQ-069), tamper-detected via `certification_id`'s own digest (HMIC-REQ-038). Unlike `HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001`, HBDC-001 does **not** additionally receive `implementation_scope_digest` content-digest binding (§11 above). Consequence, named explicitly at new requirement **HMIC-REQ-145**: a version-bumped HBDC-001 revision is certification-visible; a same-version, content-only HBDC-001 edit is **not** certification-visible under v1.2. This is a disclosed residual limitation, not a silent gap — mirroring the disclosure discipline HMIC-REQ-063 already established. A future contract revision MAY close this by additionally digest-binding HBDC-001's document bytes; v1.2 neither requires nor forbids that.

## 13. HMIC Self-Change

HMIC-001 v1.1 → v1.2 changes HMIC-001's own contract bytes. HMIC-001 remains outside `contract_versions` (unchanged from v1.1 — it is the contract *defining* the binding, not a member of it) and outside `implementation_scope_digest` (unchanged). A hypothetical old certification's `contract_versions` payload (4 members) is rejected under v1.2 via HMIC-REQ-031's pre-existing closed-schema discipline (missing required `HBDC-001` key → `MALFORMED`), documented as attack #36.

## 14. HBDC Semantic-Drift and Replay Attacks (New Attack Rows #35, #36)

- **#35 (HBDC semantic-drift-after-certification):** HBDC-001 revised to a new version, or removed/replaced, after a hypothetical certification's active pointer names it → `CONTRACT_MISMATCH` or the general missing/unsafe-file failure, via HMIC-REQ-069's five-member comparison. Same-version content-only drift is the disclosed HMIC-REQ-145 exception.
- **#36 (legacy four-member `contract_versions` replay):** a hypothetical pre-v1.2 certification presented once production is realigned to five members → `MALFORMED` via HMIC-REQ-031's missing-required-key rejection; no `legacy_contract_set=True`/`bound_contract_count=4`/`ignore_hbdc=True` override exists or is introduced. **Not yet operative** until production identity derivation is realigned (a distinct future phase) — mirrors attack #33's identical caveat.

No caller-suppliable legacy-scope override of any kind exists anywhere in the amended text.

## 15. 24-File Implementation-Source Scope — Preserved, Verified

HMIC-REQ-050's twenty-four-file enumeration is byte-identical before and after this phase (mechanically confirmed: 24 lines extracted from the fenced block, matching the pre-phase set exactly). `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` was NOT added as a 25th entry.

## 16. HMIC-REQ-063 / Option C — Preserved, Not Solved

HMIC-REQ-063's text is byte-unchanged. Binding HBDC-001 into `contract_versions` makes HBDC-001's *stated* requirements drift-visible (subject to §12's residual limitation); it does not implement, and does not claim to implement, cryptographic executed-source or runtime-module-resolution attestation. Option C remains exactly as conditional as 149O.20A/149O.20C established; Model A remains the sole HBDC-001-authorized deployment model.

## 17. Contract-First Temporary Divergence — Fail-Closed Rationale

At the end of this phase: HMIC-001 v1.2 names a 5-member `contract_versions` set; `core/hatp_mandatory_certification.py`'s `_CONTRACT_IDENTITY_FILES` still implements the 4-member v1.1 set, unchanged by this phase. **CONTRACT/PRODUCTION BOUND-CONTRACT IDENTITY DIVERGENCE — intentional, fail-closed.** Corrected framing (§4 above): a real production caller of the validator exists (Wave F, predating this phase), but no `certifications.json`/`certification-bindings.json` file exists anywhere on this host (independently re-confirmed by filesystem inspection), so every fresh validation call returns `MISSING`, mapping the readiness fact to `False` regardless of which `contract_versions` cardinality (4 or 5) production computes over. Real Class-B remains unprovisioned; no real HMIC certification exists; HATP production remains NOT READY; no real activation is authorized by this phase.

## 18. HBDC-BINDING-GATE Status (New Gate Identifier)

**HBDC-BINDING-GATE: CONTRACT-LEVEL EVOLUTION COMPLETE — INDEPENDENT CONTRACT VERIFICATION PENDING — PRODUCTION FIVE-MEMBER `contract_versions` ALIGNMENT PENDING.** Not CLOSED. Distinct from `W-1` (§50 — the HMIC validator/admin *source-file* binding, already independently verified per 149O.19.5E.2/3/4, unaffected and not reopened by this phase) and from `B-149O.19.3-1` (§49 — the provider-layer four-file finding, independently closed, unaffected).

## 19. Requirement / CIVC / Attack Inventory — After Amendment

Requirement IDs: `HMIC-REQ-001`–`HMIC-REQ-145` (145 total, no gaps, no duplicates — mechanically verified). HMIC-REQ-067/068/069 revised in place; exactly one new ID minted and appended, HMIC-REQ-145. CIVC invariants: `CIVC-1`–`CIVC-12` (12 total, unchanged in count — CIVC-5 strengthened in place). Attack matrix: 34 → **36** rows (two new: #35, #36; no pre-existing row removed).

## 20. Artifact Schema, Validation Vocabulary, Validator Algorithm — Unchanged

`CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION`/`CERTIFICATION_BINDINGS_DOCUMENT_SCHEMA_VERSION` remain 1. `CertificationRecord`/`CertificationBinding` field sets unchanged — only `contract_versions`' entry count (within its existing `Mapping[str, str]` shape) grows 4→5. Validation Status vocabulary (HMIC-REQ-106) unchanged — `CONTRACT_MISMATCH`/`MALFORMED` already suffice for every v1.2 rejection scenario; no new status introduced. Validation algorithm's structural shape (§31) unchanged — step 10 now compares five entries.

## 21. Regression and Governance Checks

New test module `tests/test_phase_149o_20d_hmic_v1_2_hbdc_bound_contract_identity_evolution.py` (44 tests) — all passing. Mechanically re-extracted and verified: contract version 1.2; `contract_versions` 5-member set; 24-file frozen set byte-identical; total-corpus-vs-`contract_versions` terminology distinction stated and not conflated; requirement IDs 1–145 no gaps/dupes; CIVC 1–12; attack matrix 36 rows sequential, rows #35/#36 present and named; HMIC-REQ-063 byte-unchanged; Option C not converted to unconditional; production divergence section present, fail-closed; HBDC-BINDING-GATE named; W-1/B-149O.19.3-1 not reopened; contract-evolution verdict present; next phase 149O.20E named, not provisioning; HBDC-001 itself and all seven other pre-existing bound contracts clean/byte-unchanged in the working tree (`git status --porcelain`); no `src/pcae/**`/`scripts/**` file dirty; production `_CONTRACT_IDENTITY_FILES` still exactly the 4-member set (expected, disclosed divergence); Wave-F validator call present and unmodified; no real certification storage files exist anywhere in the repository.

Ran full HMIC/HBDC-relevant regression sweep (§27 below) and repository-standard Fast Green (§27).

## 22. Blocking Conditions — Checked, None Triggered

HMIC clearly binds HBDC (contract_versions, HMIC-REQ-067) — yes. HBDC added with weaker identity semantics than the other four — no (same version-header mechanism; the one asymmetry, absence of digest-binding, is honestly disclosed at HMIC-REQ-145, not hidden). HBDC content-byte drift would not invalidate certification context — disclosed limitation for same-version drift only (HMIC-REQ-145); version-bumped drift is caught. Old v1.1/four-member certification grandfathered — no (attack #36, HMIC-REQ-031 closed-schema rejection). Caller can choose legacy scope — no. Original four bound contracts dropped — no. 24-file source scope changed — no. HBDC added to source digest instead of contract identity — no. HMIC-REQ-063 falsely declared solved — no. Option C unconditional — no. HBDC-001 itself modified — no. Production code modified — no. Class-B provisioning — no. Environment-lock implementation — no. Real certification/binding — no. Real activation — no. PB/POL-005/COMP-002 changed — no. Runtime state changed — no.

## 23. Contract-Evolution Verdict

```
HMIC-001 v1.2: FROZEN — HBDC BOUND-CONTRACT IDENTITY EVOLUTION COMPLETE
— PENDING INDEPENDENT VERIFICATION

HBDC binding gate: CONTRACT-LEVEL EVOLUTION COMPLETE
— INDEPENDENT CONTRACT VERIFICATION PENDING
— PRODUCTION FIVE-MEMBER ALIGNMENT PENDING

Class-B: CONTRACT VERIFIED — NOT PROVISIONED
HATP: NOT READY
```

Not claimed: HBDC binding complete. Not claimed: ready for provisioning.

## 24. Required Next Phase

**149O.20E — HMIC v1.2 HBDC Bound-Contract Identity Independent Verification.** Must independently: reconstruct the pre-amendment 4-member baseline and this amendment's diff; independently re-derive HBDC-001 as the correct, sufficient fifth member; independently verify the total-corpus-vs-`contract_versions` terminology is correctly restated (8→9 corpus, 4→5 `contract_versions`); independently verify version-bumped HBDC-001 drift would change certification identity once production realigns, and independently verify/honestly restate the same-version byte-drift residual limitation (HMIC-REQ-145) rather than silently accepting or overclaiming it; independently verify legacy four-member replay rejection and its "not yet operative" caveat; independently verify the 24-file source scope remains exactly 24; independently verify HMIC-REQ-063/Option-C preserved; independently verify production remains intentionally, fail-closed-ly stale at four members; confirm no real provisioning/certification/activation occurred. If 149O.20E passes, next is **not** Class-B provisioning — it is a bounded production-alignment phase (recommended `149O.20F`) updating `_CONTRACT_IDENTITY_FILES` from four to five, followed by that alignment's own independent verification. Only after both complete may Class-B provisioning planning be considered.

## 25. Explicit Confirmations (Restated for the Phase Report)

HBDC-001 v1.0 remained byte-unchanged. Only HMIC-001 changed among the existing normative contracts. No production source (`src/pcae/**`) was modified. No `scripts/**` file was modified. HMIC's independently verified 24-file implementation-source identity remained unchanged. HBDC-001 was added to HMIC's `contract_versions` bound-contract identity, not to the 24-file source digest. The original four `contract_versions` members were preserved. HBDC byte drift (version-bumped case) becomes certification-visible once production is aligned to v1.2; same-version byte drift is a disclosed, not-yet-closed residual limitation (HMIC-REQ-145). Old HMIC v1.1/four-member certifications are not grandfathered. No legacy-scope selector was introduced. HMIC-REQ-063 remains an explicit residual limitation. Option C remains conditional on HBDC-001 Model-A environment-lock conformance. No real Class-B provisioning occurred. No real Python-environment lockdown occurred. No real HMIC certification/binding/revocation state was created. No Cutover Record or activation marker was created/modified. No real `HATP_MANDATORY` activation occurred. No Permission Broker behavior changed. `POL-005` remained unchanged. No `COMP-002` capability was implemented. Runtime remained Observed/observe/unavailable. Class-B remains **CONTRACT VERIFIED — NOT PROVISIONED**. HATP production remains **NOT READY**.

## 26. W-1 / B-149O.19.3-1 / B-149O-1..4 Status

`W-1` remains exactly as 149O.19.5E.4 left it (repaired at contract level, independently verified, production-aligned, closed at the implementation-identity boundary) — not reopened, narrowed, or widened by this phase; this phase's own new prerequisite is tracked separately as `HBDC-BINDING-GATE` (§18), per the governing instruction's own caution not to misuse `W-1`'s name. `B-149O.19.3-1` remains independently closed, unaffected. `B-149O-1..4` remain **INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED**, unchanged by this phase, no upgrade.

## 27. Regression Suite Output

See the phase completion report for exact Fast Green and broad-sweep figures, recorded at phase close.
