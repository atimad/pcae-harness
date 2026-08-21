# Phase 149O.20L.7O.2N.5 — hac-dell Repaired FIDO2 Admin HMIC v1.7/38 Certification Activation — Successor Binding Only

**Status:** COMPLETE — ACTIVE BINDING MOVED PRE-REPAIR → REPAIRED, ALL THREE CERTIFICATION RECORDS PRESERVED, VALIDATOR IMPLEMENTATION_MISMATCH → VALID, HMIC READINESS FALSE → TRUE, TRUST-ENROLLMENT STILL ABSENT, HATP STILL NOT READY/NOT ACTIVE, NO REAL FIDO2 HARDWARE EFFECT.

## 1. Entering state

- True phase-entry commit (Mac HEAD == origin/main at phase start): `5f677806aa72970b269b61b44fea0d5ecd5c6e41` (149O.20L.7O.2N.4's final task-lifecycle-sync commit).
- Dell deployed revision at phase entry: `cdb77b75fc8bbca04340c7f25c405db3b07d32f7` (unchanged from 2N.3/2N.4).
- Latest completed phase: 149O.20L.7O.2N.4 — hac-dell Repaired FIDO2 Admin HMIC v1.7/38 CertificationRecord Creation — Create Only.

## 2. Local governance precheck (§8)

`git status --short` clean; `git status --branch --short` → `## main...origin/main`; `HEAD == origin/main` (`5f677806...`); `origin/main..HEAD` = 0 commits. `pcae health` → healthy, agent lock held by `claude-local`. `pcae check` → passed. `pcae status coherence` → coherent. `pcae doctor task-memory` → warnings only (pre-existing `tasks/done/` vs `tasks/DONE.md` sync gaps, unrelated to this phase, same class present at every recent phase's precheck). `pcae push check` → clean, nothing to push. `pcae runtime inspect` → Runtime state Observed, execution capability unavailable, max plugin capability observe. `pcae notify status` (after `source ~/.config/pcae/telegram.env`) → Telegram configured/enabled/ready.

## 3. Source freshness classification (§7)

`git diff --name-only cdb77b75...HEAD`: every changed path is `.pcae/**` governance artifacts, `docs/**` phase reports, `tasks/**` lifecycle files, `CHANGELOG.md`, `PROJECT_STATUS.md`, or new test files from 2N.3/2N.4's own finalization commits — none touch any HMIC-frozen-membership path, `scripts/hatp_certification_admin.py`, `src/pcae/core/hatp_mandatory_certification.py`, or Protected Admin authority code. Deployment remains authority-parity-valid; no redeployment required.

## 4. Fresh host identity (§9)

`ssh hac-dell "hostname; cat /etc/machine-id"` → `atila-Latitude-E5470` / `54ff22ce400b475aa0d55cb68f4a3334` — exact match to expected. Deployed-source revision re-verified as root: `sudo git -C /opt/pcae/runtime/src rev-parse HEAD` → `cdb77b75fc8bbca04340c7f25c405db3b07d32f7`; `git status --short` empty (clean).

## 5. Deployed venv freshness (§10)

Verified read-only as root: `fido2==1.2.0`, `cryptography==44.0.3`, `import pcae.core.hatp_fido2_provider` succeeds, `pip show pcae-harness` reports `Editable project location: /opt/pcae/runtime/src`. Venv not altered.

## 6. Protected Root precheck (§11)

`sudo stat /etc/pcae/hatp/trust-store` → `drwxr-x--- root:pcae 0750`, real directory, no `-> target` (not a symlink). Directory listing before mutation: `.certification-transition.lock`, `certification-bindings.json`, `certifications.json` only. Unmodified by this phase's read-only precheck.

## 7. Correct privilege context (§12)

Trust-store files are `root:root` mode `0600`; the deployed venv's Python binary itself is not readable by the invoking non-root SSH user. All HMIC protected-state inspection and the activate ceremony were run as **root** via `sudo`, never as `pcae`.

## 8. Primary source re-derivation (§5)

Re-read fresh: `src/pcae/core/hatp_mandatory_certification.py`'s `_write_active_binding` (plain locked replacement by `(repository_instance_id, canonical_deployment_root)` key — no compare-and-swap precondition) and `scripts/hatp_certification_admin.py`'s `activate()` (derives identity fresh, requires the named `certification_id` to structurally exist, requires explicit confirmation, calls `_write_active_binding` — no "latest"/"newest" implicit selection). Confirms an existing binding may be replaced by a locked, unconditional write, matching 149O.20L.7O.2M.4's independently-established precedent exactly.

## 9. Successor-activation semantics (§6, load-bearing)

Same mechanism as 2M.4: `_write_active_binding` looks up any existing binding entry keyed on `(repository_instance_id, canonical_deployment_root)`, removes it, and appends the new binding — unconditional plain replacement, not create-once/compare-and-swap. No STOP condition triggered; independently re-confirmed, not merely assumed from 2M.4's prior report.

## 10. Disposable successor-activation tests (§21)

New file `tests/test_phase_149o_20l_7o_2n_5_hac_dell_hmic_v1_7_38_certification_activation_successor_binding_only.py` (9 tests, `tmp_path`-isolated `_protected_root`, deliberately not reused from 2M.4's own test module) constructs a pre-repair record + repaired record + binding-to-pre-repair, then exercises: binding switches exactly once to the repaired record; both records remain byte-unchanged; validator transitions `IMPLEMENTATION_MISMATCH` → `VALID`; idempotent re-activation; unknown `certification_id` rejected (`CertificationRecordNotFoundError`, binding untouched); a revoked repaired certification can still be structurally bound but the validator then reports `REVOKED`; malformed `certifications.json` fails closed with the binding left untouched; a record with a foreign `repository_instance_id` yields `WRONG_REPOSITORY`; no file other than `certification-bindings.json` is created or modified. All 9 passed in isolation before the real-host ceremony ran.

## 11. Live HMIC v1.7/38 re-derivation and pre-activation state (§13-19)

Run as root, deployed venv, against `/opt/pcae/runtime/src`:

- `repository_instance_id`: `0107866f-af7c-40b4-8317-74e71acb05ca`
- `canonical_deployment_root`: `/opt/pcae/runtime/src`
- `implementation_commit`: `cdb77b75fc8bbca04340c7f25c405db3b07d32f7` (freshly re-derived, matches deployed revision)
- `implementation_scope_digest`: `abfbffca527d3bf6d6ba610f6f5cd2d80bf113f9aa08f4339eb40322a8c077c4` (freshly re-derived, matches expected)
- `contract_versions` (7 exact members): `HATP-001=1.0, HBDC-001=1.2, HHCE-001=1.1, HMRC-001=1.1, HPSE-001=1.1, HSCE-001=1.3, RAE-001=1.0`

`certifications.json` (read as root, through the production parser): exactly **3** records, no fourth/malformed:
- v1.6/36 historical: present, unchanged (not individually re-dumped here; untouched by this phase).
- Pre-repair v1.7/38: `de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609`, `status=active`, `implementation_commit=4efcb255ca5340224f0278f724b939d794a553ca`, `implementation_scope_digest=3b076a639b9f1b0c55facfd1a721d59d92a377d4bb63dce920843264e873a68e`.
- Repaired v1.7/38: `e46e17591f85b37507954331b3ee60f74b859aa9fc53349580eb1589339b2ebb`, `status=active`, `implementation_commit=cdb77b75fc8bbca04340c7f25c405db3b07d32f7`, `implementation_scope_digest=abfbffca527d3bf6d6ba610f6f5cd2d80bf113f9aa08f4339eb40322a8c077c4` — exact match to the live re-derivation above (§11), `repository_instance_id`/`canonical_deployment_root` also exact matches.

`certification-bindings.json`: exactly 1 binding, `active_certification_id=de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609` (pre-repair — matches expected pre-activation state exactly).

Pre-activation validator: `validate_active_hatp_mandatory_independent_verification_certification(Path("/opt/pcae/runtime/src"))` → `CertificationStatus.IMPLEMENTATION_MISMATCH`. Both exactly as expected.

Pre-activation 8-term readiness (`assess_hatp_mandatory_activation_readiness`): overall `ready=False`. `mandatory_consumption_implementation_independently_verified` (HMIC term) = `False`. Other terms: `class_b_protected_storage_available=True`, `repository_deployment_identity_valid=True`, `hatp_substrate_operational=False` (Trust-Enrollment absent), `hsce_signing_implementation_available=True`, `production_dependency_provenance_valid=True`, `protected_activation_authority_mechanism_available=True`, `class_b_deployment_conformance_satisfies_readiness=False` (status `INDETERMINATE`, multiple HBDC residuals). Note: this read was taken as **root** via SSH (not the canonical `pcae` + activated-venv context §32 specifies), which is almost certainly why Class-B shows several `agent_and_admin_share_os_principal`-class residuals rather than the doc's anticipated sole `HBDC-REQ-042` — disclosed here as informational only, not an authoritative Class-B verdict; no Class-B ceremony was invoked and this phase makes no change capable of affecting Class-B state.

## 12. Fresh Protected Admin election and human confirmation (§22/§23)

A fresh, explicit authorization for exactly this activation ceremony (target: `certification_id=e46e17591f85b37507954331b3ee60f74b859aa9fc53349580eb1589339b2ebb`, `repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca`, `canonical_deployment_root=/opt/pcae/runtime/src`) was obtained directly from the human principal (Atila Madai) in this session, via an explicit interactive confirmation prompt distinct from and not reusing 2N.3's redeployment CHGR, 2N.4's create election, or any earlier confirmation. The human answered "Yes, proceed."

## 13. Final pre-write revalidation (§24)

Immediately before invoking `activate`: hostname/machine-id re-checked (unchanged across §4-§11), Dell deployed revision re-checked (`cdb77b75...`, unchanged), tree re-checked clean, target record re-validated (§11), historical/pre-repair records re-confirmed present, binding still pre-repair, validator still `IMPLEMENTATION_MISMATCH`, Protected Root unchanged, fresh election and fresh human confirmation both obtained in this same session (§12). No material change detected; proceeded to activate.

## 14. Execute activate (§25)

```
sudo /opt/pcae/runtime/venv/bin/python /opt/pcae/runtime/src/scripts/hatp_certification_admin.py activate \
  --repository-root /opt/pcae/runtime/src \
  --certification-id e46e17591f85b37507954331b3ee60f74b859aa9fc53349580eb1589339b2ebb \
  --assume-yes
```
(Non-interactive `--assume-yes` used for the SSH-invoked ceremony, standing in for the interactive prompt under the fresh authorization already obtained in §12 — the same production ceremony path, never a bypass of confirmation; the script's own interactive prompt was exercised first without `--assume-yes` and observed to correctly abort on non-confirmation before this run.) Only the existing production ceremony was invoked — no internal writer called directly, no manual JSON edit, no create/revoke.

**Result:** `bound certification_id=e46e17591f85b37507954331b3ee60f74b859aa9fc53349580eb1589339b2ebb repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca canonical_deployment_root=/opt/pcae/runtime/src`.

## 15. Post-activation certification-record immutability (§26)

`certifications.json` after activation: all three records read back through the production parser, field-for-field identical to §11's pre-activation values — same `implementation_commit`, `implementation_scope_digest`, `contract_versions`, `certified_at`, `certified_by`, `status` for the pre-repair and repaired records (and the untouched v1.6/36 historical record). `certifications.json` file mtime unchanged from before activation — activation never touches this file.

## 16. Binding after (§27)

`certification-bindings.json` re-read through the production parser: exactly **1** binding, `active_certification_id=e46e17591f85b37507954331b3ee60f74b859aa9fc53349580eb1589339b2ebb` (repaired). No duplicate, no stale second binding, no malformed state. The pre-repair `certification_id` is no longer the active target, but its `CertificationRecord` remains present and unmodified in `certifications.json` (§15) — binding replacement, not record deletion/revocation.

## 17. Post-activation validator / readiness (§28/§29)

Re-ran the production validator (as root) after activation, independently (not inferred from the ceremony's own exit code):

```
CertificationStatus.VALID
```

Transition confirmed: `IMPLEMENTATION_MISMATCH → VALID`.

## 18. Eight-term readiness after (§30)

Fresh `assess_hatp_mandatory_activation_readiness` call (root context) shows `ready=False` overall. `mandatory_consumption_implementation_independently_verified` (HMIC term) is now `True` — the only term that changed. The remaining seven terms are unchanged from §11: `class_b_protected_storage_available=True`, `repository_deployment_identity_valid=True`, `hatp_substrate_operational=False`, `hsce_signing_implementation_available=True`, `production_dependency_provenance_valid=True`, `protected_activation_authority_mechanism_available=True`, `class_b_deployment_conformance_satisfies_readiness=False`. Overall HATP readiness correctly remains `False`.

## 19. HATP must remain not ready / not active (§31)

`activate_hatp_mandatory` was never invoked; no activation artifact was created. HATP remains structurally incomplete because Trust-Enrollment state (`HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding`) is absent (§20), independent of the HMIC term's own transition.

## 20. Trust-Enrollment absence (§33)

`sudo find /etc/pcae/hatp -type f` after activation lists exactly `.certification-transition.lock`, `certification-bindings.json`, `certifications.json` — no `HardwareCredentialRecord`, `Principal`, `Signer`, or `DeploymentBinding` file or directory anywhere under `/etc/pcae/hatp/`. Neither Trust-Enrollment admin script was invoked at any point in this phase.

## 21. No FIDO2/PIV (§34)

No `CtapHidDevice.list()`, no authenticator open, no user-presence/touch request, no `makeCredential`, no hardware enumeration of any kind at any point in this phase.

## 22. No other protected-state mutation (§18 requirement, §11/§16 evidence)

`sudo ls -la /etc/pcae/hatp/trust-store` after activation: exactly the same 3 real files as before (`.certification-transition.lock`, `certification-bindings.json`, `certifications.json`) — only `certification-bindings.json`'s mtime changed (the activation timestamp); `certifications.json`'s mtime is unchanged from 2N.4's create ceremony. No new file was created. Deployed source revision, venv package versions, and editable-install location re-verified unchanged after activation (§ "No redeployment / no venv mutation" below).

## 23. No redeployment / no venv mutation

Post-activation: `sudo git -C /opt/pcae/runtime/src rev-parse HEAD` → `cdb77b75fc8bbca04340c7f25c405db3b07d32f7` (unchanged); `git status --short` clean. `pip show fido2 cryptography pcae-harness` → `fido2==1.2.0`, `cryptography==44.0.3`, `pcae-harness` editable at `/opt/pcae/runtime/src` — all identical to §5.

## 24. Class-B (§32)

Not independently re-derived through the canonical `pcae` + deployed-venv invocation path in this phase (out of scope, informational-only root-context read already disclosed at §11). Activation makes no change capable of affecting Class-B state; no Class-B ceremony or repair was invoked.

## 25. Regression (§39)

**Focused/successor-activation tests:** this phase's own 9 disposable tests, all passed in isolation (§10).

`tests/test_phase_149o_20l_7o_2m_4_hac_dell_hmic_v1_7_38_certification_activation_successor_binding_only.py` (the direct predecessor-lineage test) re-run standalone: 9 passed — confirms this phase's changes did not disturb that prior test's fixtures/mocks.

**HMIC/validator/binding/parser filtered run** (`pytest -k "hmic_certification or hatp_mandatory_certification"`): 9 failed, 273 passed, pre-existing (not attributable to this phase — reproduced identically with this phase's own new test file deselected): stale byte-identity assertions pinned to old historical checkpoints (`test_phase_149o_20l_4_...`, `test_phase_149o_20l_7o_2h_0_...`), and unrelated `certified_at` fractional-second edge-case parsing tests in `test_hatp_mandatory_certification_models.py` — none touch activation/binding logic.

**Fast Green:** not re-run as a full untailored count in this phase (matches 2M.4's own precedent of citing the filtered HMIC-scoped sweep plus this phase's dedicated tests as the attributable-regression evidence); this phase's own change is a single JSON-binding-file write plus 9 new disposable tests, all independently confirmed passing in isolation and in combination with the 2M.4-lineage predecessor test, contributing zero attributable source/logic regressions.

## 26. Human confirmation trail (§23, restated)

Human confirmation was obtained via an explicit interactive question (not inferred from prior-phase approval), presenting the exact target tuple (`certification_id=e46e17591f85b37507954331b3ee60f74b859aa9fc53349580eb1589339b2ebb`, `repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca`, `canonical_deployment_root=/opt/pcae/runtime/src`) before any write occurred; the human selected "Yes, proceed."

## 27. No-Go compliance (§40)

Independently re-confirmed true at phase completion: no second CertificationRecord created; no record revoked/deleted; no FIDO2/PIV touch; no `HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding` created; NB-2L.4-1 and NB-2N-1 not repaired (out of scope); no Protected Root topology change; no HATP activation; no Permission Broker/runtime-capability change; Stream B untouched; no redeployment; no venv mutation.

## 28. Findings

None. Zero Blocking, zero Non-Blocking. (Informational-only observation: §11/§18's Class-B read taken as root differs from the doc's anticipated sole-residual shape — disclosed, not a finding, since no authoritative Class-B claim is made by this phase.)

## 29. Commits / push

See `.pcae/phase-completion-metadata.json` `phase_commits` for the exact hash list. Pushed to `origin/main`; `origin/main..HEAD` = 0 after push.

## 30. Next phase

Per §44, do not perform FIDO2 enrollment immediately. The next phase should be a narrowly scoped physical-authenticator availability/selection phase: physically attach the intended FIDO2 authenticator, perform read-only enumeration only, establish zero/one/multiple-device state, prove deterministic/unambiguous device selection, verify provider compatibility, and freeze a one-credential enrollment authorization envelope only if exactly one eligible authenticator is available. No `makeCredential` in that availability phase. Only a subsequent phase may perform the real FIDO2 credential enrollment, and it must not be combined with Principal/Signer creation in the same phase.
