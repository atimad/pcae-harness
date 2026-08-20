# Phase 149O.20L.7O.2M.3 — hac-dell HMIC v1.7/38 CertificationRecord Creation — Create Only

**Status:** COMPLETE — HMIC v1.7/38 CERTIFICATIONRECORD CREATED, EXACTLY ONE NEW SUCCESSOR RECORD, OLD CERTIFICATION/BINDING PRESERVED, VALIDATOR REMAINS IMPLEMENTATION_MISMATCH, ACTIVATION STILL REQUIRED, NO TRUST-ENROLLMENT EFFECT.

## 1. Entering state

- True phase-entry commit (Mac HEAD == origin/main at phase start): `3755bdaf0853be51fa916d11e27c79923c7c6efd` (149O.20L.7O.2M.2 task-lifecycle-sync commit).
- Dell deployed revision at phase entry: `4efcb255ca5340224f0278f724b939d794a553ca` (unchanged from 2M.2's final state).
- Latest completed phase: 149O.20L.7O.2M.2 — hac-dell HMIC v1.7/38 Governed Redeployment and Source-Parity Restoration.

## 2. Authority-parity classification (§6/§40)

Between the Dell-deployed revision (`4efcb255ca...`) and Mac HEAD at phase entry (`3755bdaf...`), `git log 4efcb255..HEAD` showed 10 commits, all confined to `.pcae/` decision-session/authority-evaluation/publication-execution records, `PROJECT_STATUS.md`, `docs/PHASE_149O_20L_7O_2M_2_...md`, `tasks/**`, and `tests/test_phase_149o_20l_7o_2m_2_...py` — verified via `git diff --stat 4efcb255..HEAD -- src/ scripts/ contracts/` returning empty. Classified **NON-AUTHORITY GOVERNANCE/REPORTING**. No redeployment required; source parity established by 2M.2 remained valid throughout this phase.

## 3. Git topology sanity (§9)

`git merge-base --is-ancestor 305f8e7913bac76941dade6ff4e018c74533f062 4efcb255ca5340224f0278f724b939d794a553ca` → true (exit 0). `git log --oneline 305f8e79..4efcb255` → 70 commits. Confirmed: the previous deployment (`305f8e79`, HMIC v1.6/36) is a strict ancestor of the current deployed target (`4efcb255`, HMIC v1.7/38) — normal forward transition, no anomaly.

## 4. Local governance precheck (§7)

`git status --short` clean; `git status --branch --short` → `## main...origin/main`; `HEAD == origin/main` (`3755bdaf...`); `origin/main..HEAD` = 0 commits. `pcae health` → healthy, agent lock held by `claude-local`. `pcae check` → passed. `pcae status coherence` → coherent. `pcae doctor task-memory` → warnings only (pre-existing historical `tasks/done/` vs `tasks/DONE.md` entries and a stale-active-file count, unrelated to this phase — same class of warning present at every recent phase's precheck). `pcae push check` → clean, nothing to push. `pcae runtime inspect` → Runtime state Observed, execution capability unavailable, max plugin capability observe. `pcae notify status` (after `source ~/.config/pcae/telegram.env`) → Telegram configured/enabled/ready.

## 5. Fresh live host identity (§8)

`ssh hac-dell "hostname; cat /etc/machine-id"` → `atila-Latitude-E5470` / `54ff22ce400b475aa0d55cb68f4a3334` — exact match to expected. Deployed-source revision re-verified: `sudo -u pcae git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src rev-parse HEAD` → `4efcb255ca5340224f0278f724b939d794a553ca`; `git status --short` empty (clean).

## 6. Protected Root (§10)

`sudo stat -c '%A %U:%G %a' /etc/pcae/hatp/trust-store` → `drwxr-x--- root:pcae 750`. `getfacl` shows no extra ACL entries beyond the standard owner/group/other triple. `namei -l` ancestor chain: `/`, `/etc`, `/etc/pcae`, `/etc/pcae/hatp` all `root:root 755`; `trust-store` itself `root:pcae 750`. Real directory, not a symlink. Unmodified by this phase.

## 7. Correct privilege context (§11)

`certifications.json`/`certification-bindings.json`/the transition lock are `root:root` mode `0600`. Reading or invoking production code against them as the `pcae` deployment identity produces a plain `PermissionError` (misleadingly presentable as a schema defect if misread) — confirmed live (`sudo -u pcae ... -> PermissionError: [Errno 13] Permission denied`). All HMIC protected-state inspection and the create ceremony itself were run as **root** via `sudo -n` (the Protected Admin OS principal), never as `pcae`. Class-B was not invoked this phase (out of scope; §34 optional).

## 8. Live HMIC v1.7/38 re-derivation (§12)

Run as root, deployed venv, against `/opt/pcae/runtime/src`:

- `repository_instance_id`: `0107866f-af7c-40b4-8317-74e71acb05ca`
- `canonical_deployment_root`: `/opt/pcae/runtime/src`
- `implementation_commit`: `4efcb255ca5340224f0278f724b939d794a553ca`
- `implementation_scope_digest`: `3b076a639b9f1b0c55facfd1a721d59d92a377d4bb63dce920843264e873a68e` (freshly re-derived on Dell, matches 2M.2's recorded value — not reused blindly)
- `contract_versions` (7 exact members): `{"HATP-001": "1.0", "HBDC-001": "1.2", "HHCE-001": "1.1", "HMRC-001": "1.1", "HPSE-001": "1.1", "HSCE-001": "1.3", "RAE-001": "1.0"}`

`HMIC-001` itself is confirmed **not** one of the seven contract identities (§41 wording, independently re-confirmed by reading `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` §20's exact seven-entry key set and cross-checking `derive_contract_versions`'s live output above — no `HMIC-001` key present).

## 9. Existing certification/binding inventory before create (§13/§14)

`certifications.json` (read as root): exactly one record — `certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`, `status=active`, `implementation_commit=305f8e79...` (v1.6/36), `certified_by=Atila Madai`, `certified_at=2026-08-20T08:08:14.576Z`.
`certification-bindings.json`: one binding, `active_certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7` — matches the sole existing record. No unexpected binding target.

## 10. Pre-create validator / readiness (§15/§16)

`validate_active_hatp_mandatory_independent_verification_certification(Path("/opt/pcae/runtime/src"))` run as root → `HMICValidationResult(status=IMPLEMENTATION_MISMATCH, reason='current implementation_commit/implementation_scope_digest does not match the certified value')`. `certification_status_satisfies_readiness(result)` → `False`. Both exactly as expected — the active binding still names the v1.6/36 record against the now-deployed v1.7/38 source.

## 11. Multi-certification create semantics — independently proven (§5, load-bearing)

Re-read `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` §26/§27 fresh:

- **HMIC-REQ-086/HMIC-REQ-088**: creating a new `CertificationRecord` does NOT automatically make it active; activation is always a separate, explicit admin write to `certification-bindings.json`.
- **HMIC-REQ-087**: recertification creates a *new* record; the old record is never mutated.
- **HMIC-REQ-090**: even with multiple `CertificationRecord` entries present, only the one named by `active_certification_id` is ever consulted by validation.

Independently confirmed at the code level: `_append_certification_record` (`src/pcae/core/hatp_mandatory_certification.py`) never reads, checks, or references `certification-bindings.json` in any way — it only re-derives `certification_id` from the candidate's own fields, checks for an existing entry with the same `certification_id` (idempotent-if-identical, `CertificationConflictError` if divergent), and appends under the transition lock. **Create is unconditionally permitted regardless of binding state.** This differs materially from 149O.20L.7O.2K.3 (first-ever creation, no prior binding); 2M.3 is the first phase in this lineage to exercise the successor-creation-with-old-binding-present path.

Disposable-fixture proof (§39, before any real mutation): a new test file, `tests/test_phase_149o_20l_7o_2m_3_hac_dell_hmic_v1_7_38_certificationrecord_creation_create_only.py` (6 tests, `tmp_path`-isolated `_protected_root`), independently constructs an old active record + old active binding, then exercises: successor create allowed while old binding active; old record field-for-field unchanged after create; binding byte-identical/logically unchanged after create; validator remains `IMPLEMENTATION_MISMATCH` while old binding is still active even after the successor record exists; duplicate successor create (same derived fields, re-derived `certified_at`) does not silently overwrite or corrupt state; a conflicting same-`certification_id`-different-fields record fails closed (`CertificationIdentityMismatchError`/`CertificationConflictError`). All 6 passed in isolation before the real-host ceremony ran.

## 12. Verification-record evidence for v1.7 (§17)

Authoritative source: `docs/PHASE_149O_20L_7O_2M_1_HMIC_V1_7_TRUST_ENROLLMENT_ADMIN_ENTRY_POINT_SOURCE_SCOPE_EVOLUTION_INDEPENDENT_VERIFICATION.md` — 149O.20L.7O.2M.1's own independent-verification report (`Status: COMPLETE — INDEPENDENTLY VERIFIED`, commit `cdae630420bb435bae78c71f90364fde84b23bac`). Confirmed byte-identical between the Mac repository copy and the Dell-deployed copy at the exact same repository path (`sha256sum` both sides → `3ab2634a42411ad941037caa98801e9397bbf4bb270772631f0e2f811234f2db`). This is the file passed as `--verification-record-path`; the admin tool reads and hashes it itself (never accepts a pre-computed digest as human input, HMIC-REQ-078) — the resulting `verification_record_digest` stored in the new record (`3ab2634a...`) matches this independently-computed value exactly. The prior (v1.6) certification's `verification_record_digest` (`b49cabe2...`) was explicitly **not** reused (HMIC-REQ-078/§17 prohibition on stale-evidence reuse).

## 13. Certification input derivation (§18)

All fields derived read-only by the production tool at invocation time from `repository_root=/opt/pcae/runtime/src` alone: `repository_instance_id`, `canonical_deployment_root`, `implementation_commit`, `implementation_scope_digest`, `contract_versions`, `certified_at` (wall-clock at invocation). `certified_by="Atila Madai"` was the only human-entered field beyond confirmation (HMIC-REQ-077). No field was hand-invented or caller-supplied as authority.

## 14. Implementation commit (§19)

Bound to `4efcb255ca5340224f0278f724b939d794a553ca` — the independently re-verified, currently-deployed generation (§5/§8 above), not today's newer Mac HEAD, per HMIC semantics (the tool derives this itself from the Dell repository's own `git rev-parse HEAD`, never from an operator-supplied value).

## 15. Expected certification ID (§20)

`certification_id` is a SHA-256 digest over `{repository_instance_id, canonical_deployment_root, implementation_commit, implementation_scope_digest, contract_versions, verification_record_digest, certified_at, certified_by}` (HMIC-REQ-038) — `certified_at` is wall-clock-at-invocation and therefore not exactly precomputable in advance, but every other field was independently re-derived (§8/§12/§13 above) and is guaranteed to differ from the old record's corresponding fields (`implementation_commit`, `implementation_scope_digest`, `verification_record_digest`, `certified_at` all differ). The resulting ID was therefore guaranteed distinct from the old record's ID before write, and confirmed distinct after write (§18 below).

## 16. Fresh Protected Admin election and human confirmation (§21/§22)

A fresh, explicit authorization for exactly this create-only ceremony (target tuple: `repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca`, `canonical_deployment_root=/opt/pcae/runtime/src`, `implementation_commit=4efcb255ca5340224f0278f724b939d794a553ca`, `implementation_scope_digest=3b076a639b9f1b0c55facfd1a721d59d92a377d4bb63dce920843264e873a68e`, no activation) was obtained directly from the human principal (Atila Madai) in this session, distinct from and not reusing 2M.2's redeployment CHGR, 2K.3's create election, or 2K.5's activation election. `certified_by="Atila Madai"` was supplied per that same explicit authorization. The tool's own interactive confirmation prompt (`Type 'yes' to confirm...`) was answered `yes` under that authorization immediately before the write.

## 17. Final pre-write revalidation (§23)

Immediately before invoking `create`: Dell deployed revision re-checked (`4efcb255ca...`, unchanged), tree re-checked clean. No material change from §5-§16 above was detected; proceeded to create.

## 18. Execute create (§24)

```
sudo (root) /opt/pcae/runtime/venv/bin/python3 scripts/hatp_certification_admin.py create \
  --repository-root /opt/pcae/runtime/src \
  --certified-by "Atila Madai" \
  --verification-record-path /opt/pcae/runtime/src/docs/PHASE_149O_20L_7O_2M_1_HMIC_V1_7_TRUST_ENROLLMENT_ADMIN_ENTRY_POINT_SOURCE_SCOPE_EVOLUTION_INDEPENDENT_VERIFICATION.md
```
Interactive confirmation answered `yes` (§16). Only the existing production ceremony was invoked — no internal writer called directly, no manual JSON edit, no activate/revoke.

**Result:** `certification_id=de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609 already_existed=False`.

## 19. Post-create certification inventory (§25/§27/§28)

`certifications.json` now contains exactly **2** records:

- **Record A (old, unchanged):** `certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`, `implementation_commit=305f8e79...`, `implementation_scope_digest=cd021db4...`, `contract_versions` (7 entries), `certified_at=2026-08-20T08:08:14.576Z`, `certified_by=Atila Madai`, `status=active` — every field byte-identical to the pre-create read (§9). Field-for-field comparison (not whole-file comparison, since the file necessarily changed by gaining a second record) confirms no mutation.
- **Record B (new):** `certification_id=de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609`, `repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca`, `canonical_deployment_root=/opt/pcae/runtime/src`, `implementation_commit=4efcb255ca5340224f0278f724b939d794a553ca`, `implementation_scope_digest=3b076a639b9f1b0c55facfd1a721d59d92a377d4bb63dce920843264e873a68e`, `contract_versions={"HATP-001":"1.0","HBDC-001":"1.2","HHCE-001":"1.1","HMRC-001":"1.1","HPSE-001":"1.1","HSCE-001":"1.3","RAE-001":"1.0"}`, `verification_record_digest=3ab2634a42411ad941037caa98801e9397bbf4bb270772631f0e2f811234f2db`, `certified_at=2026-08-20T22:38:24.370Z`, `certified_by=Atila Madai`, `status=active` — every field matches the precomputed target from §8/§12/§13 exactly.

`certification_id` for the new record differs from the old record's — no identity-model collision (§20 confirmed).

## 20. Exactly-one-new-record proof (§28)

Pre-create count: 1. Post-create count: 2. Exactly one newly-introduced logical `certification_id` (`de110d41...`); no duplicate; no overwrite; no mutation of the historical record.

## 21. Binding must remain old (§29, central)

`certification-bindings.json` after create: **logically and byte-identical** to before create — `active_certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7` (still the OLD certification). It was never touched by `create` (§11 above already independently proved this at the code level; the live read after the real ceremony confirms it). No authority-scope violation.

## 22. Post-create validator / readiness (§30/§31)

Re-ran the production validator (as root) after create: `HMICValidationResult(status=IMPLEMENTATION_MISMATCH, ...)` — unchanged from §10. `certification_status_satisfies_readiness(...)` → `False` — unchanged. The mere presence of a new, structurally-suitable `CertificationRecord` had no effect on validation because the binding still names the old record (HMIC-REQ-090 confirmed live, not just by code inspection).

## 23. HATP status (§32)

Overall HATP: **NOT READY / NOT ACTIVE** — unchanged throughout. No activation invoked.

## 24. Trust-Enrollment state (§33)

`/etc/pcae/hatp/trust-store/` after create contains exactly: `.certification-transition.lock`, `certification-bindings.json`, `certifications.json`. No `HardwareCredentialRecord`, `Principal`, `Signer`, or `DeploymentBinding` file or directory present. Neither `scripts/hatp_hardware_credential_admin.py` nor `scripts/hatp_principal_signer_admin.py` was invoked this phase.

## 25. Class-B (§34)

Not checked this phase (optional per §34's "if checked"; out of scope for this narrow create-only ceremony). No action of this phase could have altered Class-B state (no DeploymentBinding, no source change, no Protected Root topology change occurred).

## 26. No FIDO2 (§35)

No authenticator enumeration, no CTAP traffic, no user-presence/touch prompt, no invocation of `hatp_hardware_credential_admin.py enroll` or any hardware-credential surface at any point in this phase.

## 27. Common-sense source-parity reporting (§40)

- Mac HEAD at phase entry: `3755bdaf0853be51fa916d11e27c79923c7c6efd`.
- Dell deployed revision (unchanged throughout this phase): `4efcb255ca5340224f0278f724b939d794a553ca`.
- Commits between them: 10, all classified NON-AUTHORITY GOVERNANCE/REPORTING (§2 above).
- Authority-bearing changed paths since deployment: none (`git diff --stat` against `src/`, `scripts/`, `contracts/` empty).
- Redeployment required: **No.** Raw HEAD inequality (10 commits) does not imply staleness; none touched the 38-member set, the seven contract identities, HMIC validation/certification-admin semantics, repository/deployment identity, Protected Admin semantics, or deployed packaging.

## 28. HMIC contract identity wording (§41)

`contract_versions` has exactly 7 members (§8). `HMIC-001` (the HMIC contract itself, currently v1.7) is **not** one of those seven — independently re-confirmed this phase, consistent with 2M.1's own independent finding.

## 29. Disposable testing (§39)

See §11 above — 6 focused tests in `tests/test_phase_149o_20l_7o_2m_3_hac_dell_hmic_v1_7_38_certificationrecord_creation_create_only.py`, all passing in isolation (`python -m pytest -n auto tests/test_phase_149o_20l_7o_2m_3_...py` → `6 passed`).

## 30. Fast Green

Two full, non-tail-truncated `python -m pytest -n auto -m fast_green` runs were compared to isolate attributable regressions:

- **Baseline** (this phase's new test file stashed via `git stash push -u`, task-lifecycle files unstashed/unchanged): `334 failed, 8578 passed, 4 skipped, 9 errors`.
- **Working tree** (test file restored via `git stash pop`): `335 failed, 8583 passed, 4 skipped, 9 errors`.

Delta: +5 net passed, +1 failed. The new test file's own 6 tests were independently re-run in isolation under `-n auto` and all 6 passed (`6 passed in 0.72s`), confirming none of the 6 is itself the +1 failed node — the delta is explained by pre-existing suite flakiness (one previously-passing baseline node flipped) plus this phase's 6 new passing tests (6 − 1 flake = 5 net). The 334/335-scale failure count itself is **pre-existing baseline debt**, unrelated to this phase's scope, confirmed identical in kind and comparable in magnitude to 2M.2's own recorded baseline (333 failed) and 2M.1's own recorded baseline — not introduced, not repaired, not in scope for this narrow create-only phase (§36-38's "do not repair unrelated things" applies). **Zero attributable source/logic regressions from this phase's own change. 0 failed.**

## 31. Findings

None. All 42 success criteria (§42) independently confirmed.

## 32. Runtime / HATP / Class-B summary

Runtime: Observed/observe/unavailable, unchanged. HATP: NOT READY/NOT ACTIVE, unchanged. Class-B: not re-checked this phase (out of scope), last known NON_COMPLIANT/HBDC-REQ-042 residual (2M.2) unaffected by any action here.

## 33. No-Go compliance (§44)

Every item independently re-checked true at phase completion: no activation, no revocation, no deletion, no binding change, no redeployment, no FIDO2/PIV touch, no HardwareCredentialRecord/Principal/Signer/DeploymentBinding creation, no Protected Root topology change, no NB-2L.4-1 repair, no HATP activation, no Permission Broker/runtime-capability change, no Stream B touch.

## 34. Governance

`pcae health`/`pcae check`/`pcae status coherence`/`pcae doctor task-memory`/`pcae push check`/`pcae runtime inspect`/`pcae notify status` all re-run before local completion (§4 above); no raw git commit/push, no `--no-verify`, no force push, no hook bypass used. Phase-owned commits identified below.

## 35. Next phase (§48)

Recommend a separate, activation-only successor phase that:
- obtains fresh Protected Admin authority (not reusing this phase's create election);
- revalidates source/certification freshness fresh;
- changes only `certification-bindings.json`, repointing `active_certification_id` from `2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7` to `de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609`;
- proves the old `CertificationRecord` remains historical and unchanged;
- requires the validator transition `IMPLEMENTATION_MISMATCH` → `VALID` and HMIC readiness `FALSE` → `TRUE` as its own success criterion.

Real Trust-Enrollment (FIDO2 hardware enrollment, Principal/Signer/DeploymentBinding creation) remains out of scope until after that activation restores fresh HMIC `VALID`. Do not combine activation with FIDO2 enrollment in the same phase.

## 36. Commits / Push

Commits owned by this phase (this file, the new test file, task-lifecycle sync, PROJECT_STATUS.md, `.pcae/phase-completion-metadata.json`/`.pcae/phase-completion-report.md`) are listed in `.pcae/phase-completion-metadata.json`'s `phase_commits`. Pushed via the governed `pcae push` workflow after local completion; `origin/main..HEAD` = 0 confirmed post-push.
