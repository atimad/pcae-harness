# Phase 149O.20L.7O.2H.0 — HMIC v1.5 CertificationRecord Contract-Version Closed-Schema Alignment Repair

**Phase-entry commit:** `0893f40a` (Phase 149O.20L.7O.2H: close governed task, transition to idle)

**Status:** Narrow production/documentation repair only. No certification, no HATP activation, no FIDO2 provisioning, no real Principal/Signer enrollment, no real `DeploymentBinding`, no `hac-dell` mutation, no readiness-semantics change, no CBV-S10 closure, no runtime-capability change. No HMIC contract version bump — HMIC-001 v1.5 already normatively required seven `contract_versions` entries; only production conformance and two stale editorial cross-references were repaired.

## Verdict

**HMIC v1.5 CERTIFICATIONRECORD CONTRACT-VERSION CLOSED-SCHEMA ALIGNMENT REPAIRED — INDEPENDENT VERIFICATION PENDING**

`_CONTRACT_VERSIONS_REQUIRED_KEYS`: 6 → 7 members (added `HBDC-001`), now exactly equal to `_CONTRACT_IDENTITY_FILES`'s membership.
Frozen content/source identity: **35 members** (unchanged).
Contract-version identity (`_CONTRACT_IDENTITY_FILES` / `derive_contract_versions`): **7 members** (unchanged).
`B-149O.20L.7O.2H-1`: **REPAIRED — CONTRACT-VERSION RECORD/DERIVATION ALIGNMENT RESTORED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED**.
`B-149O.20L.7O.2G-1`: **ALIGNED — 35-MEMBER CONTENT/SOURCE IDENTITY IMPLEMENTED — 7-MEMBER CONTRACT IDENTITY IMPLEMENTED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED** (untouched by this phase).
HMIC certification: **NOT PERFORMED**. HATP activation: **NOT PERFORMED**.
Runtime: **Observed / observe / unavailable** (unchanged).

## 1. Entering State

- Phase 149O.20L.7O.2H (HMIC-001 v1.4-to-v1.5 Contract Evolution and Production Alignment: Trust-Enrollment/Signing Closure Limb (d)) confirmed complete at phase-entry commit `0893f40a`.
- Repository clean, zero commits ahead of `origin/main`, HMIC-001 v1.5, `_FROZEN_AUTHORITY_BEARING_FILES` = 35, `_CONTRACT_IDENTITY_FILES` = 7 members, `_CONTRACT_VERSIONS_REQUIRED_KEYS` = 6 members. Runtime unchanged (Observed/observe/unavailable). `pcae health`/`pcae check`/`pcae status coherence`/`pcae doctor task-memory`/`pcae push check`/`pcae runtime inspect`/`pcae notify status`/`pcae phase-report show --latest` all consistent with a clean, completed 2H.

## 2. Reason for This Phase

2H's own §59.17/§59.19 (contract) and its production comments disclosed, but did not repair, a divergence: `_CONTRACT_IDENTITY_FILES` (Wave B, `derive_contract_versions`) has seven members including `HBDC-001`; `_CONTRACT_VERSIONS_REQUIRED_KEYS` (Wave A, `CertificationRecord.contract_versions` closed-schema acceptance, consumed by `_require_contract_versions`) was left at six, omitting `HBDC-001`. 2H's own narrative characterized this as "a pre-existing, disclosed, out-of-scope drift," attempting a "Wave A vs. Wave B" terminology distinction to justify leaving it unrepaired.

## 3. Reproduction (Before Repair)

Constructed `derive_contract_versions(root)`'s live seven-member mapping on this repository and passed it to `_require_contract_versions`:

```
derive_contract_versions -> {'HMRC-001': '1.1', 'HATP-001': '1.0', 'HSCE-001': '1.3',
                              'RAE-001': '1.0', 'HBDC-001': '1.2', 'HPSE-001': '1.1',
                              'HHCE-001': '1.1'}
SEVEN-MEMBER: REJECTED -> contract_versions: has unrecognized contract entries: ['HBDC-001']
SIX-MEMBER (no HBDC): parsed OK
```

Direct reproduction of `B-149O.20L.7O.2H-1`: `derive_contract_versions`'s own current output could never itself parse as a `CertificationRecord.contract_versions` value. Worse, `validate_active_hatp_mandatory_independent_verification_certification`'s own §31 step 10 (`hatp_mandatory_certification.py` line 2113: `if dict(current_contract_versions) != dict(record.contract_versions)`) compares the *current* seven-member derived mapping against a *stored* record's contract_versions, which the closed schema capped at six members — meaning **no stored `CertificationRecord`, however constructed, could ever pass step 10** before this repair. This is load-bearing, not cosmetic: any future real certification ceremony would derive seven, be unable to store seven (parser rejects `HBDC-001` as "unrecognized"), store six instead, and then have its own step-10 self-comparison permanently fail with `CONTRACT_MISMATCH` from the moment of creation.

## 4. Primary Evidence — HMIC-001 v1.5 Is Unambiguous

Read directly from `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` (§20, §17, §31), never from prior phases' summaries:

- **HMIC-REQ-067** (§20): *"Seven entries, no more, no fewer, as of v1.5."*
- **HMIC-REQ-069** (§20): validation *"SHALL compare each `contract_versions` entry — seven entries as of v1.5 — against the named contract's own current, live version header,"* and explicitly classes *"a required contract key absent from a stored record"* as a mismatch (`CONTRACT_MISMATCH`/`MALFORMED`).
- **HMIC-REQ-053** (§17): *"every `contract_versions` member (HMIC-REQ-067, seven entries) receives both bindings uniformly — no `contract_versions` member is exempted from the digest binding."*
- **HMIC-REQ-032** (§11): defines `contract_versions` as one field on `CertificationRecord` — there is no HMIC-001 textual basis anywhere for a narrower "Wave A closed-schema acceptance set" distinct from Wave B's own `derive_contract_versions` output. "Wave A"/"Wave B" are production-module organizational labels (`hatp_mandatory_certification.py`'s own docstring), never HMIC-001 contract vocabulary; the contract names one field, `contract_versions`, with one required membership.

Conclusion: this is **Outcome A** (of the governing task's three possible outcomes) — HMIC-001 v1.5 already unambiguously requires all seven current contract identities inside `CertificationRecord.contract_versions`. The contract does not need to change; production must conform to it.

Two forward-looking normative passages (§23/HMIC-REQ-076's creation-ceremony step 4; §31/HMIC-REQ-103's validation-algorithm step 10) still read *"the four frozen contracts' own ... version headers"* — stale text never updated across the v1.1 (HBDC), v1.3 (HPSE precursor), and v1.5 (HHCE) widenings. This is real textual drift inside HMIC-001 itself, but it is illustrative/summary prose, not a competing normative enumeration (HMIC-REQ-067/069 are the actual enumeration and are unambiguous). The §31/HMIC-REQ-103 occurrence is corrected in this phase to "seven bound contracts'" as the smallest possible additive editorial clarification — not a new normative statement, and not requiring a version bump. The textually-identical §23/HMIC-REQ-076 occurrence is deliberately left unedited: a prior independent-verification phase's own regression guard (`tests/test_phase_149o_20l_7l_6_contract_preamble_and_relative_import_guard_repair_independent_verification.py::test_hmic_req_145_closure_paragraph_present_and_unchanged`) asserts a byte-identical block anchored on HMIC-REQ-145's own text; its regex-based extraction only stops at the next *parenthetical-titled* `**HMIC-REQ-NNN (` marker, and HMIC-REQ-076 has no parenthetical title, so the guarded window incidentally spans past HMIC-REQ-145's own text into HMIC-REQ-076's unrelated creation-ceremony prose. Editing that occurrence would fail an unrelated prior phase's own regression check for no compensating benefit (both occurrences carry identical, purely illustrative meaning); it is reproduced verbatim, out of this phase's own repair scope.

## 5. HMIC-REQ-053 Interaction

2G.1 established that every `contract_versions` member receives both content binding and version binding uniformly. HMIC-REQ-053's own v1.5 text (§4 above) states this applies to *"every `contract_versions` member (HMIC-REQ-067, seven entries)"* — the same collection HMIC-REQ-032 names as `CertificationRecord.contract_versions`. There is no vocabulary distinction in the contract text between "contract_versions member" (REQ-053) and "CertificationRecord.contract_versions entry" (REQ-032) — they are the same term. `HBDC-001`'s omission from the closed-schema acceptance set was therefore plainly inconsistent with the contract's own REQ-053, not a legitimate narrower reading.

## 6. Historical HBDC-001 Reconstruction

- **Phase 149O.20D** (`5671448a`): widened `_CONTRACT_IDENTITY_FILES`-equivalent contract text (HMIC-REQ-067) from four to five members, adding `HBDC-001` — contract-only; explicitly deferred production alignment.
- **Phase 149O.20F** (`d3be5440`): production alignment for 149O.20D's contract change. Widened `_CONTRACT_IDENTITY_FILES` from four to five entries (adding `HBDC-001`). Did **not** touch `_CONTRACT_VERSIONS_REQUIRED_KEYS`, which remained at four members. Git diff of this commit confirms only `_CONTRACT_IDENTITY_FILES` (and its surrounding comment) changed — `_CONTRACT_VERSIONS_REQUIRED_KEYS` is absent from this commit's diff entirely.
- **Phase 149O.20G** (`78990e92`): independent verification of 149O.20F. Its own commit message and test diff confirm it verified "5/5-contract dual equality" for `_CONTRACT_IDENTITY_FILES` only — a repository-wide search of its test-file changes finds zero references to `_CONTRACT_VERSIONS_REQUIRED_KEYS` or `_require_contract_versions`. **The Wave A closed-schema gap was never independently verified or adjudicated by any prior phase** — not by 149O.20G, and not by any subsequent phase before this one. It was first *named* (not adjudicated) by 149O.20L.7O.2G's own analysis, reconfirmed present by 2G.1, and left deliberately unrepaired by 2H with a "disclosed, out-of-scope" framing that this phase's primary-source re-derivation finds unsupported by HMIC-001's own text.

Conclusion: the omission was an **implementation oversight at 149O.20F** (a Wave A/Wave B split that the contract's own text never draws), never a decision independently verified as correct, and never something the contract's own vocabulary supports as a legitimate narrower subset.

## 7. Certification ID Consequence

`derive_certification_id` (HMIC-REQ-038) incorporates `contract_versions` directly into the SHA-256 digest input via `canonical_serialize`. It performs no key-set validation itself (accepts whatever mapping the caller assembles from `derive_contract_versions`). A disposable test (`test_certification_id_changes_when_contract_versions_mapping_changes`) proves a `contract_versions` mapping mutation changes `certification_id`; `test_certification_id_derivation_accepts_full_seven_member_mapping` proves the full seven-member mapping derives a valid 64-hex-character ID. Before this repair, a real ceremony deriving `certification_id` from the true seven-member mapping could never subsequently *store* a matching `CertificationRecord` (the parser would reject the seven-member `contract_versions` it just hashed) — a structural inconsistency between certification-ID derivation and closed-schema storage, now resolved.

## 8. Active-Validation Consequence

`validate_active_hatp_mandatory_independent_verification_certification`'s §31 step 10 (line ~2113) recomputes `derive_contract_versions` fresh and compares by dict equality against `record.contract_versions`. Tested explicitly for all five governing-task cases (`TestActiveValidationCases`, isolated fixture repo, never the real Protected Root):

- **Case 1** (stored six-member record, HBDC-001 omitted): now **cannot even be constructed** — `_require_contract_versions` fails closed (`CertificationMalformedError`, missing required key) before a record ever reaches storage. Pre-repair this shape *was* the only constructible shape; post-repair it is impossible to admit.
- **Case 2** (stored seven-member record, all correct): **VALID**.
- **Case 3** (seven members, wrong `HBDC-001` version): **CONTRACT_MISMATCH**.
- **Case 4** (correct `HBDC-001`, wrong `HPSE-001` version): **CONTRACT_MISMATCH**.
- **Case 5** (all seven current versions correct): **VALID**.

Wrong `HHCE-001` version independently tested: **CONTRACT_MISMATCH**. All five cases fail closed exactly as HMIC-REQ-069's "no compatibility-mapping table exists" rule requires.

## 9. Admin-Construction Consequence

No real HMIC certification admin tool exists in production (`grep` for `def certify`/`activate_hmic`/`revoke_hmic`/`hmic_admin` across `src/pcae/` finds nothing outside `parse_certification_record`'s own single `CertificationRecord(...)` construction site) — confirming the governing task's own premise that no real ceremony has ever executed. `test_parse_certification_record_roundtrip_retains_all_seven` proves the one production construction path (`parse_certification_record` → `certification_record_to_document`) now retains all seven identities through a full parse/serialize round-trip, so a future real ceremony cannot "derive 7 → serialize/drop one → write 6" or "derive 7 → parser rejects its own record."

## 10. Repair

`src/pcae/core/hatp_mandatory_certification.py`: `_CONTRACT_VERSIONS_REQUIRED_KEYS` widened from six to exactly seven members — `frozenset({"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001", "HPSE-001", "HHCE-001"})` — now exactly equal to `_CONTRACT_IDENTITY_FILES`'s membership. The misleading "Wave A vs. Wave B, disclosed, out-of-scope" comment block is replaced with one citing HMIC-REQ-067/069/053's own text and explaining why no such distinction exists in the contract.

`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`: one stale "the four frozen contracts' own ... version headers" passage (§31/HMIC-REQ-103) corrected to "the seven bound contracts' own ... version headers"; the textually-identical §23/HMIC-REQ-076 occurrence intentionally left unedited (reasoning above). §11/HMIC-REQ-032's illustrative `contract_versions` example widened to show all seven current members (with a note that the versions shown are illustrative and §20 is the authoritative current key set), and its stale `(§22)` cross-reference corrected to `(§20)` (§20 is "Contract Binding Set," the section that actually defines the set; §22 is "Non-Authoritative Repo-Local Signals," unrelated). No requirement's normative *authority* semantics were weakened; no HMIC version bump — HMIC-001 v1.5 already unambiguously required seven members before this phase's edits.

## 11. 35/7 Alignment and Closure Limb (d) — Unchanged

This repair touches only `_CONTRACT_VERSIONS_REQUIRED_KEYS` and the two stale cross-references above. `_FROZEN_AUTHORITY_BEARING_FILES` (35), `_FROZEN_SRC_PCAE_RELATIVE_FILES` (26), `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (9), `_CONTRACT_IDENTITY_FILES` (7), closure limb (d)'s text, and the three Trust-Enrollment/signing source files are byte-for-byte unmodified by this phase — verified by `test_thirty_five_file_frozen_identity_unchanged`, `test_frozen_src_and_root_relative_counts_unchanged`, `test_closure_limb_d_text_unchanged`, `test_limb_d_source_files_present_in_frozen_src_set`, and by `git diff --stat` showing zero lines changed in `hatp_signing_ceremony.py`, `hatp_hardware_credential_admin.py`, `hatp_principal_signer_admin.py`, `HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md`, `HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` since phase entry.

## 12. Historical Certification Compatibility

No stored certification exists on any host today (confirmed via `pcae runtime inspect` and the absence of any real admin tool, §9 above), so no historical record required disposition adjudication in practice. Structurally, `test_case1_stored_six_member_record_cannot_even_be_parsed` proves the disposition any surviving pre-repair six-member record shape would receive: `MALFORMED` (missing required key), via the closed-schema parser itself — never a silent upgrade, never an invented compatibility mode, exactly as HMIC-REQ-069's "no compatibility-mapping table exists" rule requires.

## 13. New Findings

None beyond `B-149O.20L.7O.2H-1` itself, whose disposition is recorded below. The one repaired "four frozen contracts" cross-reference (§31/HMIC-REQ-103) and the one intentionally-untouched occurrence (§23/HMIC-REQ-076, deferred to avoid an unrelated prior-phase byte-identity regression guard) are recorded as editorial drift within this same phase, not as a separate finding — they carried no independent functional consequence (illustrative prose only, never consulted by any production code path).

## 14. Finding Disposition

**`B-149O.20L.7O.2H-1` — HMIC v1.5 Contract-Version Identity / CertificationRecord Closed-Schema Divergence: REPAIRED — CONTRACT-VERSION RECORD/DERIVATION ALIGNMENT RESTORED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.** This phase does not close its own finding; only a future independent-verification phase (149O.20L.7O.2H.1) may.

**`B-149O.20L.7O.2G-1` — ALIGNED — 35-MEMBER CONTENT/SOURCE IDENTITY IMPLEMENTED — 7-MEMBER CONTRACT IDENTITY IMPLEMENTED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.** Untouched by this phase; retained exactly as 2H left it.

## 15. No-Go Confirmations

No HMIC certification was created or activated. No HATP activation was performed. No FIDO2 hardware was provisioned or touched. No real Principal was enrolled. No real Signer was enrolled. No real `DeploymentBinding` was created. No `hac-dell` or Protected Root state was mutated. No readiness/activation semantics were changed. No Permission Broker or runtime-capability state was changed. No PIV implementation was performed. No CBV-S10 wiring was performed. No Stream B content was touched. No real production certification, provisioning, or enrollment of any kind occurred at any point in this phase.

## 16. CBV-S1 / CBV-S10

Unaffected. Class-B topology/environment-lock/conformance verifiers, the `DeploymentBinding` producer/admin script, and CBV-S1's own binding remain untouched — this phase's `--allowed-file` scope never includes any Class-B verifier or `DeploymentBinding` source file. CBV-S10 remains OPEN, untouched, exactly as 2H left it.

## 17. Recommended Next Phase

**149O.20L.7O.2H.1 — HMIC-001 v1.5 Trust-Enrollment/Signing Authority-Scope Alignment Independent Verification.** Must independently reconstruct, without trusting this document's narrative: HMIC-REQ-052/closure limb (d) and the 35/7 identity from 2H (unchanged by this phase); this phase's own `B-149O.20L.7O.2H-1` reproduction, primary-source re-derivation (HMIC-REQ-067/069/053/032), historical-HBDC reconstruction, and the seven-member repair itself — including whether the two stale-cross-reference editorial fixes were within scope and correctly minimal. Does not begin certification, provisioning, readiness work, or activation.
