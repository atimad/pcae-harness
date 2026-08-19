# Phase 149O.20L.7O.2H.1 — HMIC-001 v1.5 Trust-Enrollment / Signing Authority-Scope Alignment Independent Verification

## Verdict

**NOT VERIFIED — HMIC SOURCE-SCOPE CLOSURE AND CONTRACT CONSISTENCY DEFECTS.**

This independent-verification phase preserved two newly demonstrated Blocking findings. It did not modify production source or a normative contract, and it performed no certification, provisioning, readiness integration, or activation.

The 2H.0 seven-member `CertificationRecord.contract_versions` repair is independently verified and its entering finding can close at that narrow representation boundary. The wider 2H 35/7 authority-scope alignment cannot close because an actually reached authority-bearing dependency, `src/pcae/core/paths.py`, is outside the frozen identity. Current normative HMIC-REQ-076 also still prescribes reading “the four frozen contracts” during a ceremony that “proceeds exactly,” contradicting the current seven-contract rule.

## Fixed evidence points and environment

- True phase-entry commit: `973258b991f0df21b9996fe29adc5c13ca06dc7b`.
- Fixed HMIC-001 v1.4 checkpoint immediately before 2H: `e65b4ce0bd17800f85e0858c78032bd968d1d574`.
- Substantive 2H commit: `7e789c707375e721a57e984194ce64c8e7d69810`.
- Fixed completed post-2H/pre-2H.0 checkpoint: `0893f40afd5258e1ba85fb197f708095dfcc7dbc`.
- Substantive 2H.0 repair commit: `fb0146bee1fddded0365e67f395edda7d318fde3`.
- 2H.0 editorial narrowing/status commit: `d935c28faa427864bc80c87661af41c924ff8c91`.
- Host: Darwin; project interpreter: `.venv/bin/python`, Python 3.9.6; pytest 8.4.2; cryptography 44.0.3.
- Independent historical inspection used detached disposable worktrees, never `git stash`.
- Current HMIC contract header: HMIC-001 v1.5.

## Independent historical reconstruction

AST literal extraction from each fixed Git object, paired with mechanical HMIC-REQ-050 extraction, produced:

| State | Source-relative | Root-relative | Frozen total | Contract identities | Record required keys |
|---|---:|---:|---:|---:|---:|
| v1.4 (`e65b4ce`) | 23 | 7 | 30 | 5 | 4 |
| post-2H/pre-2H.0 (`0893f40a`) | 26 | 9 | 35 | 7 | 6 |
| current phase entry (`973258b`) | 26 | 9 | 35 | 7 | 7 |

The v1.4 frozen set was:

1. `src/pcae/core/hatp_mandatory_cutover.py`
2. `src/pcae/core/hatp_ag_authority.py`
3. `src/pcae/core/hatp_rollback_consumption.py`
4. `src/pcae/core/hatp_bootstrap.py`
5. `src/pcae/core/human_approval_trusted_provenance.py`
6. `src/pcae/core/repository_identity.py`
7. `src/pcae/core/rollback_approval_evidence.py`
8. `src/pcae/core/hatp_evidence_store.py`
9. `src/pcae/core/hatp_signed_evidence.py`
10. `src/pcae/core/agent.py`
11. `src/pcae/commands/agent.py`
12. `src/pcae/cli.py`
13. `src/pcae/core/permission_broker.py`
14. `src/pcae/core/permission_broker_foundation.py`
15. `src/pcae/core/hatp_providers.py`
16. `src/pcae/core/hatp_fido2_provider.py`
17. `src/pcae/core/hatp_piv_provider.py`
18. `src/pcae/core/hatp_hardware_credentials.py`
19. `src/pcae/core/hatp_mandatory_certification.py`
20. `src/pcae/core/hatp_class_b_topology_verifier.py`
21. `src/pcae/core/hatp_environment_lock_verifier.py`
22. `src/pcae/core/hatp_class_b_conformance.py`
23. `src/pcae/core/hatp_deployment_binding_admin.py`
24. `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
25. `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`
26. `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`
27. `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`
28. `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
29. `scripts/hatp_certification_admin.py`
30. `scripts/hatp_deployment_binding_admin.py`

The current literal 35-member set is that exact 30-member superset plus the independently computed five-member delta:

1. `src/pcae/core/hatp_signing_ceremony.py`
2. `src/pcae/core/hatp_hardware_credential_admin.py`
3. `src/pcae/core/hatp_principal_signer_admin.py`
4. `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md`
5. `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`

There were zero removals. Thus the implemented literal membership transition is exactly 30 → 35, with 26 `src/pcae`-relative and 9 repository-root-relative entries.

## v1.4 → v1.5 semantic contract diff

The exact diff from `e65b4ce` to the current contract was classified block by block:

- **Normative authority change:** v1.5 adds HMIC-REQ-052 limb (d), anchored on `production_sign_rollback_evidence` plus the non-reachable hardware-credential and Principal/Signer administrative writers. It also adds the corresponding completeness/attack obligations.
- **Normative count/membership consequence:** HMIC-REQ-050 changes 30 → 35 and enumerates the five additions; HMIC-REQ-053/067/069 change the contract identity/content rule from five to seven, adding HPSE-001 and HHCE-001.
- **Non-normative explanation:** rationale and attack rows explain why signing consumers, enrollment writers, and same-version contract drift require binding.
- **Editorial/cross-reference repair:** the v1.5 header/dependency references, the HMIC-REQ-032 example, and HMIC-REQ-103 summary were updated. The current HMIC-REQ-076 occurrence was not repaired and is a Blocking inconsistency described below.
- **Phase-history/analysis appendix:** the later 2H/2H.0 narrative records phase reasoning and has no independent authority over the numbered requirements.

No v1.4 authority member or requirement was removed. No existing normative authority requirement was weakened. The intentional semantic expansion is confined to the Trust-Enrollment/signing closure and its two new contract identities. The version bump from 1.4 to 1.5 is internally appropriate for that expansion, subject to the two current defects.

## Current requirement and identity reconstruction

HMIC-REQ-050’s literal enumeration equals the production frozen constants exactly: 26 + 9 = 35. `src/pcae/core/hatp_mandatory_certification.py` is itself member 19 and therefore nominally self-bound.

The seven identities independently derived from HMIC-REQ-067, production identity paths, and live headers are:

| Contract ID | Exact path | Live version |
|---|---|---:|
| HMRC-001 | `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` | 1.1 |
| HATP-001 | `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` | 1.0 |
| HSCE-001 | `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md` | 1.3 |
| RAE-001 | `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md` | 1.0 |
| HBDC-001 | `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` | 1.2 |
| HPSE-001 | `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` | 1.1 |
| HHCE-001 | `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` | 1.1 |

The historical five-member identity is the first five rows. The exact two-contract identity delta is HPSE-001 and HHCE-001, with no removal. IDs and paths are unique. Versions are parsed from live headers, not hard-coded results. Every one of the seven paths is independently present in the frozen content set, satisfying HMIC-REQ-053’s dual binding. Mechanically:

`HMIC normative version IDs == _CONTRACT_IDENTITY_FILES IDs == _CONTRACT_VERSIONS_REQUIRED_KEYS == CertificationRecord closed-schema domain == seven IDs`.

## Limb (d), call graph, and transitive closure

The historical v1.4 HMIC-REQ-052 had exactly limbs (a), (b), and (c). v1.5 adds distinct limb (d). Symbol-level reconstruction found:

- The signing anchor reaches the real production authority path: `production_sign_rollback_evidence` → `sign_rollback_evidence` → `resolve_signing_context` → durable Principal/Signer/credential/provider checks → AG3/AG5 evidence resolution → provider `request_signature` → post-touch authority-state revalidation → publication. It is not merely the cutover module’s `importlib.import_module` check.
- The hardware-credential and Principal/Signer enrollment writers are not reachable from the signing anchor and are therefore separately named writer anchors, matching the contract’s dual-anchor construction.
- The three added production modules are necessary and byte-identical to their independently verified implementation boundaries: signing equals `b229e423`; both enrollment admin modules equal `021175c9`; no later semantic diff exists.

Dependency classification:

- **Bound:** all previously frozen HATP, evidence, provider, agent, permission, Class-B, and DeploymentBinding modules actually reached by limb (d), plus the three new anchor modules.
- **Justifiably excluded on the exact reached path:** `git_status.py` and `tasks.py` are imported at module level by `agent.py`, but `build_rollback_review` and `lookup_promotion_execution_record` call none of their symbols. `provenance.py` is reached only for post-write audit/telemetry in the enrollment writers and does not determine the constructed authority record before durable readback.
- **Missing / Blocking:** `paths.py`; the actually reached `HarnessPath.join` and `.path` select authority-bearing AG3/AG5 evidence and registry locations.

### B-149O.20L.7O.2H.1-1 — unbound reached path authority

**Blocking.** A fresh disposable checkout contained the production package and all 35 bound files. Genuine and attacker AG3 job records carried different commit SHAs. The canonical 35-file implementation digest was recorded. Only disposable, unbound `src/pcae/core/paths.py` was changed so `HarnessPath.join(".pcae/remote/jobs")` redirected to the attacker directory. The actual production `build_rollback_review` result changed from `111…111` to `222…222`; the 35-file digest remained byte-for-byte identical.

Therefore changing an actually reached PCAE-owned symbol can alter an authority-bearing signing input while all certified bytes remain unchanged. This directly defeats HMIC-REQ-052 closure. The prior exclusion precedent is inapplicable because this is execution dependence, not mere transitive importability.

## CertificationRecord repair reconstruction

Against fixed post-2H/pre-2H.0 source:

- `len(_CONTRACT_IDENTITY_FILES) == 7`;
- `len(_CONTRACT_VERSIONS_REQUIRED_KEYS) == 6`;
- exact difference: `{HBDC-001}`.

The historical implementation’s actual `derive_contract_versions(...)` produced all seven live entries. Passing that mapping to historical `_require_contract_versions(...)` failed because HBDC-001 was “unrecognized.” Removing HBDC-001 produced a six-member mapping that parsed, despite being incapable of matching the true current derivation. This independently reproduces the core `B-149O.20L.7O.2H-1` defect.

HMIC-REQ-032/053/067/069 independently require one exact, seven-member `CertificationRecord.contract_versions` mapping. “Wave A” and “Wave B” are implementation organization labels with no normative significance. Current source has exact set equality, not merely equal lengths.

Fresh disposable tests established:

- complete seven-member derive → parse round trip: accepted;
- missing HBDC-001, HPSE-001, or HHCE-001: rejected closed;
- unknown eighth key: rejected closed;
- duplicate JSON object key: rejected by strict parsing;
- non-string version: rejected closed;
- `derive_certification_id()` changes when any one of all seven entries changes;
- active validation: exact seven-member mapping → `VALID`; wrong HBDC/HPSE/HHCE → `CONTRACT_MISMATCH`;
- historical six-member/v1.4 record → `MALFORMED` at strict record parsing, before implementation or contract comparison, and never `VALID`;
- an unknown additional member cannot form a record and fails closed.

This independently proves the 2H.0 production repair at the CertificationRecord representation boundary.

## Digest, same-version drift, and self-binding

Disposable state proved every one of the exact five additions changes `implementation_scope_digest` when its bytes change. For HBDC-001, HPSE-001, and HHCE-001, a body-only mutation with the version header unchanged left `contract_versions` unchanged but changed `implementation_scope_digest`, confirming dual binding.

For self-binding, two unchanged live derivations were identical; mutating only disposable `hatp_mandatory_certification.py` changed the digest; restoring/discarding the fixture restored determinism. No stale digest cache was observed.

## HMIC text hygiene and 2H.0 semantic classification

All current occurrences of “four/five/six/seven contracts,” `contract_versions`, SS20/SS22, and Wave A/Wave B were classified. Historical appendix wording is intentionally contextual; current explanatory counts consistent with seven are non-normative; HMIC-REQ-032/053/067/069/076/103 are current normative text.

The 2H.0 contract diff made two substantive textual edits:

- HMIC-REQ-032’s illustrative mapping changed from four to all seven and its cross-reference changed SS22 → SS20: clarification/example and cross-reference repair.
- HMIC-REQ-103 step 10 changed “four frozen contracts” → “seven bound contracts”: stale prose repair clarifying HMIC-REQ-067/069’s already-existing rule.

Neither created a new authority rule, so retaining HMIC v1.5 for those edits was justified.

### B-149O.20L.7O.2H.1-2 — HMIC-REQ-076 ceremony contradiction

**Blocking.** HMIC-REQ-076 is current normative text, not history. It states certification creation “proceeds exactly,” yet step 4 says `contract_versions` is computed by reading “the four frozen contracts’ own version headers.” HMIC-REQ-067 simultaneously mandates “Seven entries, no more, no fewer,” and HMIC-REQ-032/053/069/103 consistently operate on seven.

The stale four-contract instruction materially misstates the current creation ceremony; following it produces a record the current closed schema rejects. The broad older byte-identity test that incidentally spans HMIC-REQ-076 because of an imprecise extraction boundary is over-broad. Correcting current authority prose would expose a brittle test, not invalidate a legitimate historical guarantee. Incorrect normative text cannot be preserved solely to satisfy that guard.

## Regression and behavior evidence

- Fresh 2H.1 suite: **43 passed**, 0 failed. It was authored independently and treats preserved-defect reproductions as passing evidence tests.
- Focused HMIC/CertificationRecord/Trust-Enrollment/signing/DeploymentBinding selection: **512 passed** in 9.67 seconds.
- Wider fixed/current comparison:
  - current: 12 failed, 773 passed, 1 skipped;
  - fixed v1.4: 12 failed, 704 passed, 1 skipped;
  - exact FAILED-node set difference: empty; ERROR-node set difference: empty.
- The 12 common historical/stale FAILED node IDs were:
  1. `tests/test_phase_149o_19_5b_hmic_identity_derivation.py::TestFrozenFileManifest::test_manifest_has_exactly_25_entries`
  2. `tests/test_phase_149o_19_5b_hmic_identity_derivation.py::TestFrozenFileManifest::test_manifest_has_no_duplicate_entries`
  3. `tests/test_phase_149o_19_5b_hmic_identity_derivation.py::TestFrozenFileManifest::test_canonical_paths_are_25_and_lexicographically_sorted`
  4. `tests/test_phase_149o_20i_hatp_class_b_topology_verifier.py::test_current_module_not_in_hmic_frozen_scope`
  5. `tests/test_phase_149o_20i_hatp_class_b_conformance.py::test_zero_authority_callers_across_src_pcae`
  6. `tests/test_phase_149o_20i_hatp_class_b_conformance.py::test_three_modules_not_in_current_hmic_frozen_scope`
  7. `tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_lock_independent_implementation_verification.py::test_zero_production_authority_consumers_repo_wide`
  8. `tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_lock_independent_implementation_verification.py::test_cutover_certification_admin_scripts_do_not_reference_new_modules`
  9. `tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_lock_independent_implementation_verification.py::test_new_modules_absent_from_current_hmic_frozen_source_set`
  10. `tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_lock_independent_implementation_verification.py::test_agent_effective_gid_not_in_getgroups_can_be_missed`
  11. `tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_lock_independent_implementation_verification.py::test_deep_ancestor_writable_beyond_immediate_parent_is_caught`
  12. `tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_lock_independent_implementation_verification.py::test_20i_own_structural_suites_still_pass_as_a_regression_signal_only`

Bounded direct regressions reconfirmed BF-1 (`credential_identity` has zero production call sites) and BF-2 (non-resident FIDO2 uses the explicit `signer_key_id`). Existing focused production tests reconfirmed binding/signer-principal and signer/provider inconsistencies fail pre-touch, post-touch state revalidation remains active, and disposable HardwareCredential/Principal/Signer/continuous-two-lock/DeploymentBinding writers retain their behavior. No contrary evidence reopens BF-1, BF-2, `B-149O.20L.7O.2F.3-1`, or `B-149O.20L.7O.2F.3-2`.

The current frozen set retains all five Class-B/DeploymentBinding members: topology verifier, environment-lock verifier, conformance module, DeploymentBinding producer, and its script. CBV-S1 remains satisfied at its previously established source-binding boundary. CBV-S10 remains OPEN.

## Fast Green

Canonical current run (`.venv/bin/python -m pytest -m fast_green -n auto`): **8227 passed, 4 skipped, 306 failed, 9 errors**, 133.51 seconds. After adding the 43 fresh tests to the marker set, an independent current rerun produced **8270 passed, 4 skipped, 306 failed, 9 errors**, 135.98 seconds: the 43-test increment was entirely passing and the non-passing totals were identical. Fixed v1.4 run: **8159 passed, 4 skipped, 305 failed, 9 errors**, 146.73 seconds. The large common non-passing population is historical phase-pinned debt, including the same nine old 25-file fixture errors.

The sole additional current failure was `tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`. Independent isolated rerun reproduced its hard 15-second subprocess timeout. The underlying read-only command completed in 14.21 seconds and reported 178084 records, including one pre-existing tampered record dated 2026-06-29. This phase changed no shell-gate/audit code or state. Classification: durable host-load/timing and pre-existing audit-state failure, not a current functional regression; Fast Green is nevertheless reported honestly as non-green.

## Finding adjudication

- `B-149O.20L.7O.2G-1`: **NOT CLOSED — 35/7 LITERAL MEMBERSHIP ALIGNED, BUT HMIC SOURCE CLOSURE IS INCOMPLETE.** The required “limb (d) complete” acceptance limb fails because `paths.py` is reached and unbound.
- `B-149O.20L.7O.2H-1`: **INDEPENDENTLY CONFIRMED CLOSED AT HMIC CERTIFICATION-RECORD / CONTRACT-IDENTITY REPRESENTATION BOUNDARY.** The historical seven-vs-six defect, normative seven-member representation rule, current set equality, derive→parse consistency, certification-ID sensitivity, validation behavior, and incomplete-record closed failure were all independently demonstrated. This closure does not cure the separate HMIC-REQ-076 ceremony-text defect.
- `B-149O.20L.7O.2H.1-1`: **BLOCKING — OPEN.** `paths.py` is an unbound, actually reached authority dependency.
- `B-149O.20L.7O.2H.1-2`: **BLOCKING — OPEN.** HMIC-REQ-076 materially contradicts the seven-contract creation rule.

## No authority upgrade and operational state

Phase-owned diffs are limited to governed task/memory/report artifacts and the fresh verification test. Production and `docs/contracts/**` have zero phase diff. The fixed macOS production trust-store and hardware-credential directories were absent at final read-only inspection. No `certifications.json`, active binding, trust registry, hardware credential registry, Principal, Signer, or DeploymentBinding was created. No write command targeting hac-dell or Protected Root ran.

- HMIC certification: **NOT PERFORMED**.
- Certification activation: **NOT PERFORMED**.
- Trust enrollment / FIDO2 provisioning: **NOT PERFORMED**.
- Real DeploymentBinding: **ABSENT / NOT CREATED**.
- HATP: **NOT READY / NOT ACTIVE**.
- Permission Broker and readiness: **UNCHANGED**.
- Runtime: **Observed / observe / unavailable**, registry empty, execution unavailable.
- hac-dell / Protected Root: **NOT MUTATED**.

HMIC validity remains distinct from approval, permission, capability, execution, and operational readiness.

## Narrowest subsequent repair

The exact next phase should be:

**149O.20L.7O.2H.2 — HMIC-001 v1.6 Paths Source-Scope Closure and Seven-Contract Ceremony Consistency Repair.**

Its narrow scope should add `core/paths.py` to HMIC-REQ-050 and the production frozen source set (27 + 9 = 36), align the closure rationale and digest-sensitive tests, correct HMIC-REQ-076 from four to seven, and narrow the brittle historical byte-window guard. Because adding a certified input changes normative authority identity, this should be an HMIC version evolution, followed by a separate independent-verification phase. It must not certify, provision, integrate readiness, activate HATP, wire CBV-S10, or touch Stream B.

## Phase-owned commits and push status

- `0fc4f940` — `Phase 149O.20L.7O.2H.1: start governed independent verification`.
- Final evidence/report and lifecycle commits: recorded in canonical completion metadata after governed finalization.
- Push and `origin/main..HEAD`: recorded after governed push/final checks.
