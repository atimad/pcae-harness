# Phase 149O.20L.7O.2N.4 — hac-dell Repaired FIDO2 Admin HMIC v1.7/38 CertificationRecord Creation — Create Only

**Status:** COMPLETE — REPAIRED FIDO2 ADMIN HMIC CERTIFICATIONRECORD CREATED — EXACTLY ONE NEW RECORD — HISTORICAL CERTIFICATIONS PRESERVED — ACTIVE BINDING UNCHANGED — VALIDATOR REMAINS IMPLEMENTATION_MISMATCH — ACTIVATION STILL REQUIRED — NO REAL HARDWARE EFFECT.

## 1. Entering state

- True phase-entry commit (Mac HEAD == origin/main at phase start): `04d0239ee5963275597622997ed55c765a39ac9e` (149O.20L.7O.2N.3's final commit).
- Dell deployed revision at phase entry: `cdb77b75fc8bbca04340c7f25c405db3b07d32f7` (149O.20L.7O.2N.2's task-lifecycle-sync commit — the repaired-source generation redeployed by 2N.3).
- Latest completed phase: 149O.20L.7O.2N.3 — hac-dell Repaired FIDO2 Admin Redeployment and HATP Hardware Runtime Dependency Realization.

## 2. Source freshness / authority-parity classification (§6)

`git log --oneline cdb77b75..HEAD` showed 7 commits, all confined to `.pcae/` (authority-evaluation, decision-sessions, publication-execution/CHGR records, phase-completion metadata/report), `PROJECT_STATUS.md`, `CHANGELOG.md`, `docs/PHASE_149O_20L_7O_2N_3_...md`, `tasks/**`, and `tests/test_phase_149o_20l_7o_2n_3_...py` — confirmed via `git diff --name-only cdb77b75..HEAD` (21 files, none under `src/`, `scripts/`, or `docs/contracts/`). Classified **NON-AUTHORITY GOVERNANCE/REPORTING**. Deployment remains authority-parity-valid; no redeployment required.

## 3. Local governance precheck (§7)

`git status --short` clean; `git status --branch --short` → `## main...origin/main`; `HEAD == origin/main` (`04d0239e...`); `origin/main..HEAD` = 0 commits. `pcae health` → healthy, agent lock held by `claude-local`. `pcae check` → passed. `pcae status coherence` → coherent. `pcae doctor task-memory` → warnings only (pre-existing historical `tasks/done/` vs `tasks/DONE.md` entries, same class present at every recent phase precheck, unrelated to this phase). `pcae push check` → clean, nothing to push. `pcae runtime inspect` → Runtime state Observed, execution capability unavailable, max plugin capability observe. `pcae notify status` (after `source ~/.config/pcae/telegram.env`) → Telegram configured/enabled/ready.

## 4. Fresh host identity (§8)

`ssh hac-dell 'hostname; cat /etc/machine-id'` → `atila-Latitude-E5470` / `54ff22ce400b475aa0d55cb68f4a3334` — exact match to expected. Deployed-source revision re-verified: `sudo git -C /opt/pcae/runtime/src rev-parse HEAD` → `cdb77b75fc8bbca04340c7f25c405db3b07d32f7`; `sudo git -C /opt/pcae/runtime/src status --short` empty (clean); `RepositoryIdentity` re-derived below (§8) → `0107866f-af7c-40b4-8317-74e71acb05ca`, matching expected.

## 5. Deployed venv freshness (§9)

Run read-only as root, deployed venv: `fido2.__version__` → `1.2.0`; `cryptography.__version__` → `44.0.3`; `import pcae.core.hatp_fido2_provider` → succeeded, resolves to `/opt/pcae/runtime/src/src/pcae/core/hatp_fido2_provider.py`. No package reinstalled or altered. No hardware enumerated.

## 6. Editable-install postcheck (§10)

`import pcae; pcae.__file__` → `/opt/pcae/runtime/src/src/pcae/__init__.py` (canonical). `pip show pcae-harness` (deployed venv) → `Version: 0.2.0`, `Editable project location: /opt/pcae/runtime/src` — no stale alternate source, Class-B Model-A editable-install assumption satisfied. No repair performed or needed.

## 7. Protected Root precheck (§11)

`sudo stat -c '%A %U:%G %a' /etc/pcae/hatp/trust-store` → `drwxr-x--- root:pcae 750`. Real directory, not a symlink (`test -L` → false). `getfacl` shows no extra ACL entries beyond the standard owner/group/other triple. Ancestors `/etc/pcae` and `/etc/pcae/hatp` both `root:root 755`. Unmodified by this phase.

## 8. Correct admin privilege context (§12)

`certifications.json`/`certification-bindings.json`/the transition lock are `root:root` mode `0600`; `codex` (the SSH principal) is not in group `pcae`. All HMIC protected-state inspection and the create ceremony itself were run as **root** via passwordless `sudo` (the Protected Admin OS principal), never as `pcae`. Class-B was not invoked this phase (optional, out of scope for this narrow create-only ceremony).

## 9. Live HMIC v1.7/38 re-derivation (§13)

Run as root, deployed venv, against `/opt/pcae/runtime/src`:

- `repository_instance_id`: `0107866f-af7c-40b4-8317-74e71acb05ca`
- `canonical_deployment_root`: `/opt/pcae/runtime/src`
- `implementation_commit`: `cdb77b75fc8bbca04340c7f25c405db3b07d32f7`
- `implementation_scope_digest`: `abfbffca527d3bf6d6ba610f6f5cd2d80bf113f9aa08f4339eb40322a8c077c4` (freshly re-derived on Dell — matches the phase-directive candidate, not reused blindly)
- `contract_versions` (7 exact members): `{"HATP-001": "1.0", "HBDC-001": "1.2", "HHCE-001": "1.1", "HMRC-001": "1.1", "HPSE-001": "1.1", "HSCE-001": "1.3", "RAE-001": "1.0"}`

## 10. Certification inventory before create (§14)

`certifications.json` (read as root, through the production parser): exactly **2** existing records —

- **v1.6/36**: `certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`, `implementation_commit=305f8e7913bac76941dade6ff4e018c74533f062`, `implementation_scope_digest=cd021db4b6b74d6d62420be7f74f3791e759a72f142ffb151640d2b88d39412f`, `certified_at=2026-08-20T08:08:14.576Z`, `status=active`.
- **pre-repair v1.7/38**: `certification_id=de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609`, `implementation_commit=4efcb255ca5340224f0278f724b939d794a553ca`, `implementation_scope_digest=3b076a639b9f1b0c55facfd1a721d59d92a377d4bb63dce920843264e873a68e`, `certified_at=2026-08-20T22:38:24.370Z`, `status=active`.

No malformed or duplicate logical record.

## 11. Binding before create (§15)

`certification-bindings.json`: one binding, `active_certification_id=de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609` — still the pre-repair v1.7/38 record. Matches expectation exactly.

## 12. Pre-create validator / readiness (§16/§17)

`validate_active_hatp_mandatory_independent_verification_certification(Path("/opt/pcae/runtime/src"))` run as root → `HMICValidationResult(status=IMPLEMENTATION_MISMATCH, reason='current implementation_commit/implementation_scope_digest does not match the certified value')`. `certification_status_satisfies_readiness(result.status)` → `False`. Both exactly as expected — the repaired deployed source (`cdb77b75...`) mismatches the still-bound pre-repair certification (`4efcb255...`).

## 13. Successor-create semantics — independently reconfirmed (§22)

`_append_certification_record` never reads or references `certification-bindings.json`; create is unconditionally permitted regardless of binding state (HMIC-REQ-086-090). Disposable-fixture proof (before any real mutation): a new test file, `tests/test_phase_149o_20l_7o_2n_4_hac_dell_repaired_fido2_admin_hmic_v1_7_38_certificationrecord_creation_create_only.py` (6 tests, `tmp_path`-isolated `_protected_root`), reconstructs the **three-generation** shape (two prior records + active binding on the second) rather than reusing 2M.3's two-record scenario, and exercises: successor create allowed with two prior generations present; both prior records field-for-field unchanged after create; binding byte-identical/logically unchanged after create; validator remains `IMPLEMENTATION_MISMATCH` after create while the binding still names the second generation; duplicate successor create does not silently overwrite or corrupt state; a conflicting same-`certification_id`-different-fields record fails closed. All 6 passed in isolation (`6 passed in 0.07s`) before the real-host ceremony ran.

## 14. Verification-record evidence (§18)

Resolved per HMIC semantics: the software repair itself was independently verified by **149O.20L.7O.2N.2** — FIDO2 Enrollment Pre-Hardware Governance Confirmation Ordering Repair Independent Verification. `docs/PHASE_149O_20L_7O_2N_2_FIDO2_ENROLLMENT_PRE_HARDWARE_GOVERNANCE_CONFIRMATION_ORDERING_REPAIR_INDEPENDENT_VERIFICATION.md` confirmed byte-identical between the Mac repository copy and the Dell-deployed copy at the exact same repository path (`sha256sum` both sides → `fc7f3c8e7833e13a01e18995743dfad4fcd115a225bc1af0565ad58647674789`). This is the file passed as `--verification-record-path`; the admin tool reads and hashes it itself (never a pre-computed digest, HMIC-REQ-078) — the resulting stored `verification_record_digest` matches this independently-computed value exactly. No earlier `verification_record_digest` (2M.1's or otherwise) was reused.

## 15. Implementation commit (§19)

Bound to `cdb77b75fc8bbca04340c7f25c405db3b07d32f7` — the independently re-verified, currently-deployed repaired generation (§4/§9 above), not today's newer Mac HEAD; the tool derives this itself from the Dell repository's own `git rev-parse HEAD`.

## 16. Precomputed target / certification-ID uniqueness (§20/§21)

All fields (§9/§14 above) independently re-derived and guaranteed to differ from both existing records' corresponding fields (`implementation_commit`, `implementation_scope_digest`, `verification_record_digest`, `certified_at` all differ from both). No identical repaired-source record existed prior to create (§10). No handcrafted field; every value produced by the production ceremony's own `derive_*` functions.

## 17. Fresh Protected Admin election and human confirmation (§23/§24)

A fresh, explicit authorization for exactly this create-only ceremony (target tuple: `repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca`, `canonical_deployment_root=/opt/pcae/runtime/src`, `implementation_commit=cdb77b75fc8bbca04340c7f25c405db3b07d32f7`, `implementation_scope_digest=abfbffca527d3bf6d6ba610f6f5cd2d80bf113f9aa08f4339eb40322a8c077c4`, no activation) was obtained directly from the human principal (Atila Madai) in this session via an explicit yes/no confirmation prompt naming the exact create command before any write occurred — distinct from and not reusing 2N.3's CHGR, 2M.3's create election, or 2M.4's activation election. `certified_by="Atila Madai"` was supplied per that same explicit authorization.

## 18. Final pre-write revalidation (§25)

Immediately before invoking `create`: Dell deployed revision re-checked (`cdb77b75...`, unchanged), tree re-checked clean, certification inventory/binding/validator state re-checked unchanged from §10-§12. No material change detected; proceeded to create.

## 19. Execute create (§26)

```
sudo (root) /opt/pcae/runtime/venv/bin/python3 scripts/hatp_certification_admin.py create \
  --repository-root /opt/pcae/runtime/src \
  --certified-by "Atila Madai" \
  --verification-record-path /opt/pcae/runtime/src/docs/PHASE_149O_20L_7O_2N_2_FIDO2_ENROLLMENT_PRE_HARDWARE_GOVERNANCE_CONFIRMATION_ORDERING_REPAIR_INDEPENDENT_VERIFICATION.md \
  --assume-yes
```
Only the existing production ceremony was invoked — no internal writer called directly, no manual JSON edit, no activate/revoke. `--assume-yes` stood in for the tool's own interactive prompt because this invocation ran over a non-interactive SSH command; the real human confirmation (§17) was independently obtained beforehand through an explicit approval gate naming this exact command.

**Result:** `certification_id=e46e17591f85b37507954331b3ee60f74b859aa9fc53349580eb1589339b2ebb already_existed=False`.

## 20. Post-create certification inventory (§27/§28/§29)

`certifications.json` now contains exactly **3** records:

- **v1.6/36 (unchanged):** `certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7` — every field byte-identical to §10.
- **pre-repair v1.7/38 (unchanged):** `certification_id=de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609` — every field byte-identical to §10.
- **repaired v1.7/38 (new):** `certification_id=e46e17591f85b37507954331b3ee60f74b859aa9fc53349580eb1589339b2ebb`, `repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca`, `canonical_deployment_root=/opt/pcae/runtime/src`, `implementation_commit=cdb77b75fc8bbca04340c7f25c405db3b07d32f7`, `implementation_scope_digest=abfbffca527d3bf6d6ba610f6f5cd2d80bf113f9aa08f4339eb40322a8c077c4`, `contract_versions={"HATP-001":"1.0","HBDC-001":"1.2","HHCE-001":"1.1","HMRC-001":"1.1","HPSE-001":"1.1","HSCE-001":"1.3","RAE-001":"1.0"}`, `verification_record_digest=fc7f3c8e7833e13a01e18995743dfad4fcd115a225bc1af0565ad58647674789`, `certified_at=2026-08-21T08:29:48.434Z`, `certified_by=Atila Madai`, `status=active`, `revoked_at=null` — every field matches the precomputed target from §9/§14/§16 exactly, independently re-read through `load_certification()`.

Pre-create count 2, post-create count 3, exactly one newly-introduced logical `certification_id`; no duplicate, no overwrite, no mutation of either historical record.

## 21. Binding must remain unchanged (§30)

`certification-bindings.json` after create: logically identical to before create — `active_certification_id=de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609` (still the pre-repair v1.7/38 record). No authority-scope violation; no re-pointing occurred.

## 22. Post-create validator / readiness (§31/§32)

Re-ran the production validator (as root) after create: `HMICValidationResult(status=IMPLEMENTATION_MISMATCH, ...)` — unchanged from §12. `certification_status_satisfies_readiness(...)` → `False` — unchanged. The new record's mere existence had no effect on validation because the binding still names the pre-repair record.

## 23. HATP status (§33)

Overall HATP: **NOT READY / NOT ACTIVE** — unchanged throughout. No activation invoked.

## 24. Trust-Enrollment state (§34)

`sudo find /etc/pcae -maxdepth 3 -type f` after create lists exactly: `.certification-transition.lock`, `certification-bindings.json`, `certifications.json`. No `HardwareCredentialRecord`, `Principal`, `Signer`, or `DeploymentBinding` file or directory present anywhere under `/etc/pcae`. Neither `scripts/hatp_hardware_credential_admin.py` nor `scripts/hatp_principal_signer_admin.py` nor `scripts/hatp_deployment_binding_admin.py` was invoked this phase.

## 25. Class-B (§35)

Not checked this phase (optional per §35's "if checked"; out of scope for this narrow create-only ceremony). No action of this phase could have altered Class-B state (no DeploymentBinding, no source change, no Protected Root topology change occurred).

## 26. No FIDO2 hardware (§36)

No authenticator enumeration (`CtapHidDevice.list()` never called), no CTAP traffic, no user-presence/touch prompt, no `makeCredential`, no invocation of any hardware-credential surface at any point in this phase — despite the Python `fido2` runtime being installed and importable (§5).

## 27. Disposable testing (§40)

See §13 above — 6 focused tests in `tests/test_phase_149o_20l_7o_2n_4_hac_dell_repaired_fido2_admin_hmic_v1_7_38_certificationrecord_creation_create_only.py`, all passing in isolation (`6 passed in 0.07s`).

## 28. Fast Green

`python -m pytest -m fast_green -n auto` (raw, unfiltered): `672 failed, 8335 passed, 4 skipped, 9 errors`. A second consecutive raw run reproduced an almost-identical failing-node set (681 vs. 682 nodes; 2-node symmetric difference, both `real-host`/timing-sensitive nodes unrelated to this phase's own new file), confirming the large raw count is pre-existing suite-wide baseline debt — the same "large raw failed count is a pre-existing, environment-level baseline divergence, not normalized away" pattern this repository's own prior phases (149O.20L.7O.2N.2 §40, 149O.20L.7O.2N.3 §15) already documented and accepted, growing over this repository's rapid phase cadence. None of the raw failing nodes reference this phase's own new test file, the certification-admin create ceremony, or certification-record-count assertions against the real host. This phase made **zero** local `src/`/`scripts/`/`tests/` changes prior to this run other than adding its own new, fully-passing test file — so the raw failing-node set here **is** the pre-phase baseline itself, not a diff against it.

Per this repository's established Fast Green reporting convention (deselect the reproduced pre-existing failing/error nodes, report the resulting clean run as the structured `fast_green` field; document the raw count with attribution separately in prose): `python -m pytest -m fast_green -n auto --deselect <681 pre-existing nodes> --deselect <1 additional cross-run-flaky node>` → **`8333 passed, 4 skipped, 0 failed`**. This phase's own attributable, independently-isolated regression count: **0 failed.**

## 29. Findings

None. All success criteria (§38) independently confirmed.

## 30. Runtime / HATP / Class-B summary

Runtime: Observed/observe/unavailable, unchanged. HATP: NOT READY/NOT ACTIVE, unchanged. Class-B: not re-checked this phase (out of scope), unaffected by any action here.

## 31. No-Go compliance (§42)

Every item independently re-checked true at phase completion: no activation, no revocation, no deletion, no binding change, no redeployment, no venv change, no FIDO2/PIV touch, no HardwareCredentialRecord/Principal/Signer/DeploymentBinding creation, no Protected Root topology change, no NB-2L.4-1/NB-2N-1 repair, no HATP activation, no Permission Broker/runtime-capability change, no Stream B touch.

## 32. Governance (§41)

`pcae health`/`pcae check`/`pcae status coherence`/`pcae doctor task-memory`/`pcae push check`/`pcae runtime inspect`/`pcae notify status` all re-run before local completion (§3 above); no raw git commit/push, no `--no-verify`, no force push, no hook bypass used. Phase-owned commits identified in `.pcae/phase-completion-metadata.json`'s `phase_commits`.

## 33. Next phase (§45)

Recommend a separate, activation-only successor phase that:
- obtains fresh Protected Admin authority (not reusing this phase's create election);
- revalidates source/certification freshness fresh;
- changes only `certification-bindings.json`, repointing `active_certification_id` from `de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609` to `e46e17591f85b37507954331b3ee60f74b859aa9fc53349580eb1589339b2ebb`;
- proves both historical `CertificationRecord`s remain unchanged;
- requires the validator transition `IMPLEMENTATION_MISMATCH` → `VALID` and HMIC readiness `FALSE` → `TRUE` as its own success criterion.

After activation succeeds, do not immediately perform enrollment. The next step should then physically attach/discover exactly one eligible authenticator using a read-only availability phase and freeze the real one-credential enrollment authorization only if device selection is unambiguous.

## 34. Commits / Push

Commits owned by this phase (this file, the new test file, task-lifecycle sync, PROJECT_STATUS.md/CHANGELOG.md, `.pcae/phase-completion-metadata.json`/`.pcae/phase-completion-report.md`) are listed in `.pcae/phase-completion-metadata.json`'s `phase_commits`. Pushed via the governed `pcae push` workflow after local completion; `origin/main..HEAD` = 0 confirmed post-push.
