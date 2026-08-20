# Phase 149O.20L.7O.2K.5 — HATP HMIC Certification Activation (Existing Certification Binding Only)

## 0. Phase Entry State

- True phase-entry commit: `b6c61849` (`origin/main` identical, `origin/main..HEAD` = 0, working tree clean).
- Latest completed phase: 149O.20L.7O.2K.4, which froze a bounded activation-only authorization envelope for `certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7` without executing it.

## 1. Authority-Parity Classification

All 20 commits/files changed since the deployed revision (`305f8e7913bac76941dade6ff4e018c74533f062`) were classified NON-AUTHORITY GOVERNANCE/REPORTING: `.pcae/` decision-session/publication-execution artifacts, `CHANGELOG.md`, `PROJECT_STATUS.md`, phase docs, task lifecycle files, and phase-specific test files for 2K.2/2K.3/2K.4. None touch the 36 HMIC frozen files, the 7 bound contracts, the certification admin ceremony, the HMIC validator, or repository/deployment identity semantics. No redeployment performed or required.

## 2. Fresh Host Identity (hac-dell)

- `machine-id`: `54ff22ce400b475aa0d55cb68f4a3334` — matched.
- `hostname`: `atila-Latitude-E5470` — matched.
- `RepositoryIdentity`: `0107866f-af7c-40b4-8317-74e71acb05ca` — matched (read from `/opt/pcae/runtime/src/.pcae/repository-identity.json`).
- Deployed revision: `git -C /opt/pcae/runtime/src rev-parse HEAD` = `305f8e7913bac76941dade6ff4e018c74533f062`, detached HEAD, clean.

## 3. Protected Root Precheck

`/etc/pcae/hatp/trust-store`: real directory, not a symlink, owner `root:pcae`, mode `750`, default ACL rejects `other`. Ancestors (`/etc/pcae/hatp`, `/etc/pcae`, `/etc`) `root:root 755`. Compliant; no repair performed.

## 4. Fresh HMIC Identity (re-derived on hac-dell via production code)

- HMIC version: v1.6.
- `_FROZEN_AUTHORITY_BEARING_FILES`: 36 entries (exact).
- Bound contract identities: 7 (exact).
- `repository_instance_id`: `0107866f-af7c-40b4-8317-74e71acb05ca`.
- `canonical_deployment_root`: `/opt/pcae/runtime/src`.
- `implementation_commit`: `305f8e7913bac76941dade6ff4e018c74533f062`.
- `implementation_scope_digest`: `cd021db4b6b74d6d62420be7f74f3791e759a72f142ffb151640d2b88d39412f`.
- `contract_versions` (7): HATP-001 1.0, HBDC-001 1.2, HHCE-001 1.1, HMRC-001 1.1, HPSE-001 1.1, HSCE-001 1.3, RAE-001 1.0.

## 5. Existing CertificationRecord Revalidation

Loaded through `load_certification()` (production parser) on hac-dell. Every authority-sensitive field matched the fresh Step 4 derivation exactly: `certification_id`, `repository_instance_id`, `canonical_deployment_root`, `implementation_commit`, `implementation_scope_digest`, all 7 `contract_versions`. `status="active"`, `certified_by="Atila Madai"`, `certified_at="2026-08-20T08:08:14.576Z"`. `certifications.json` bytes SHA-256 (pre-write): `df6e2db036f36c30bd673f0ab3ce4fbf1158810d1821c98d87f8e13ecf10255a` (912 bytes).

## 6. Current State Prechecks (before activation)

- Binding: `certification-bindings.json` absent (state A — activation candidate, no conflict).
- HMIC validator (fresh): `MISSING`.
- HMIC readiness: `False`.

## 7. Contract/Source Re-Read (Section 4 requirement)

Re-read `src/pcae/core/hatp_mandatory_certification.py` and `scripts/hatp_certification_admin.py` directly (not relying on 2K.4's prior reading). Confirmed independently:
- `activate()` writes only `certification-bindings.json` via `_write_active_binding` (single write primitive, no other file touched).
- `CertificationRecord` is immutable — `activate()` never calls `_append_certification_record`/`_write_revocation`.
- `activate()` performs only a structural existence/parse precondition on the target record (via `load_certification`/`_load_certification_record`) — never requires Trust-Enrollment, Class-B COMPLIANT, or any Wave-D `VALID` pre-check.
- Confirmation semantics: `confirm=False` raises `ConfirmationDeclinedError`, no write occurs; `main()`'s `--assume-yes` bypasses only the interactive prompt, not the `confirm` boolean itself.
- Idempotency: repeated `activate()` calls with the same `certification_id` overwrite the single-entry binding with byte-identical content (verified structurally in disposable testing, §8).

## 8. Disposable Testing (isolated `_protected_root`, hac-dell, never the real Protected Root)

All 9 exercised scenarios passed:

| Case | Result |
|---|---|
| Activate absent binding | success, correct binding written |
| Idempotent replay (same cert, twice) | second call returns identical `ActivateCeremonyResult` |
| Conflicting binding (different cert already bound) | activation overwrites the single-entry pointer to the new target — this is the ceremony's documented behavior, not a defect |
| Missing CertificationRecord | raises `CertificationRecordNotFoundError`, no write |
| Revoked CertificationRecord | activation structurally succeeds (writer != validator, per contract) |
| Wrong repository/deployment root | N/A — `activate()` never accepts caller-supplied `repository_instance_id`/`canonical_deployment_root` (HMIC-REQ-045) |
| `confirm=False` | raises `ConfirmationDeclinedError`, `certification-bindings.json` not created |
| Malformed record elsewhere in store | N/A — `activate()` loads only the target `certification_id`, no whole-store scan |
| CertificationRecord immutability across `activate()` | `certifications.json` bytes unchanged before/after |

No production source changed; no disposable test touched `/etc/pcae/hatp/trust-store`.

## 9. Protected Admin Election and Human Confirmation

Fresh election specific to this activation (not reused from 2K.2's redeployment CHGR or 2K.3's create election). Human confirmation obtained explicitly via a dedicated confirmation prompt naming: `certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`, `repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca`, `canonical_deployment_root=/opt/pcae/runtime/src`, operation=activate. Confirmed by Atila Madai before mutation; not inferred from "continue" or an earlier phase's approval.

## 10. Final Pre-Write Revalidation

Immediately before mutation: host identity, deployment revision, deployment cleanliness, HMIC 36/7, CertificationRecord identity/state, active-binding absence, Protected Root — all re-checked in this same session, no material change detected between precheck and write.

## 11. Execution

```
sudo bash -c 'cd /opt/pcae/runtime/src && /opt/pcae/runtime/venv/bin/python3 scripts/hatp_certification_admin.py activate --repository-root /opt/pcae/runtime/src --certification-id 2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7 --assume-yes'
```

Output: `bound certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7 repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca canonical_deployment_root=/opt/pcae/runtime/src`. Exit status 0. Actor: Protected Administrator OS principal on hac-dell (`sudo`), invoked interactively by Atila Madai via this session. Timestamp: 2026-08-20 ~11:31 local (hac-dell file mtime).

## 12. Postcheck Results

- **CertificationRecord immutability**: `certifications.json` SHA-256 post-write = `df6e2db036f36c30bd673f0ab3ce4fbf1158810d1821c98d87f8e13ecf10255a`, 912 bytes — byte-identical to pre-write (§5). PASS.
- **Binding content**: exactly one `CertificationBinding` entry: `repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca`, `canonical_deployment_root=/opt/pcae/runtime/src`, `active_certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`. No duplicate keys. PASS.
- **Validator (fresh, independent re-derivation)**: `CertificationStatus.VALID`.
- **HMIC readiness**: `True` (`certification_status_satisfies_readiness(VALID)`).
- **Other readiness terms** (`assess_hatp_mandatory_activation_readiness`, hac-dell, post-write):
  - `class_b_protected_storage_available` = True (unchanged)
  - `repository_deployment_identity_valid` = True (unchanged)
  - `hatp_substrate_operational` = **False** (unchanged — `NOT_READY`, `class_b_bootstrap_environment_not_safe` and related bootstrap-trust-store reasons)
  - `hsce_signing_implementation_available` = True (unchanged)
  - `mandatory_consumption_implementation_independently_verified` = **True** (the only term this phase changed — was `False`/`MISSING` before)
  - `production_dependency_provenance_valid` = True (unchanged)
  - `protected_activation_authority_mechanism_available` = True (unchanged)
  - `class_b_deployment_conformance_satisfies_readiness` = **False** (unchanged — `INDETERMINATE`, `HBDC-REQ-002`/`HBDC-REQ-007` residuals)
  - **Overall `ready`: False.**
- **HATP activation state**: `activate_hatp_mandatory` was never invoked. HATP remains NOT ACTIVE, NOT READY (overall `ready=False` above).
- **Adjacent trust records**: `/etc/pcae/hatp/trust-store` contains exactly three files post-write — `.certification-transition.lock` (unchanged), `certifications.json` (unchanged), `certification-bindings.json` (new). No `hardware-credentials.json`, no principal/signer records, no `DeploymentBinding` artifact created.
- **HardwareCredentialRecord / Principal / Signer / DeploymentBinding**: all confirmed ABSENT (no such files exist under the Protected Root or elsewhere in `.pcae`/deployment state).
- **No FIDO2**: no authenticator enumeration, no CTAP call, no hardware touch performed this phase.
- **Runtime**: unchanged — `pcae runtime inspect` unchanged (`Observed` / `observe` / `unavailable`).

## 13. Class-B Diagnostic Discipline

Not re-run this phase (activation does not depend on the Class-B numeric count, per governing prompt §24). `class_b_deployment_conformance_satisfies_readiness` was read as part of the standard `assess_hatp_mandatory_activation_readiness` conjunction above (§12) and observed unchanged (`INDETERMINATE`) — no separate improvised diagnostic invocation was used as authority.

## 14. Governance / Local Checks

`pcae health` (healthy), `pcae check` (passed), `pcae status coherence` (coherent), `pcae doctor task-memory` (pre-existing DONE.md-listing warnings only, unrelated to this phase), `pcae push check` (clean before phase-owned commits), `pcae runtime inspect` (unchanged), Telegram notification foundation confirmed configured/enabled.

## 15. Findings

None. All success criteria (§36 of the governing prompt) satisfied: fresh authority-bearing source parity, correct host identity, Protected Root compliant, HMIC exact 36/7, existing CertificationRecord exact/current, no conflicting active binding, fresh activate election, fresh human confirmation, activation wrote only the intended binding, CertificationRecord remained byte-identical, binding points exactly to the intended certification, validator independently returned VALID, HMIC readiness became TRUE, unrelated readiness terms unchanged, HATP did not activate, no FIDO2/Principal/Signer/DeploymentBinding created, runtime unchanged.

## 16. Next DAG Node

Not pre-authorized by this phase. With HMIC now `VALID`, the sole remaining blocking residual toward Class-B/`HBDC-REQ-042` readiness is `DeploymentBinding` absence, which itself depends on the still-unresolved FIDO2 administrative-entrypoint gap (`scripts/hatp_hardware_credential_admin.py` / `scripts/hatp_principal_signer_admin.py` standalone admin-script entrypoints do not yet exist) and the Trust-Enrollment sequence ahead of it. A future phase should re-derive this fresh from actual post-2K.5 state rather than assume this ordering.
