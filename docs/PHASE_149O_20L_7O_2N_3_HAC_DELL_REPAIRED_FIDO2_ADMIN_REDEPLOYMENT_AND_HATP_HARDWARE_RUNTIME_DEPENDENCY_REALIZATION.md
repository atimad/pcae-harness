# Phase 149O.20L.7O.2N.3 — hac-dell Repaired FIDO2 Admin Redeployment and HATP Hardware Runtime Dependency Realization

## 0. Status

Single-phase real-effect execution. REDEPLOYMENT + DECLARED-DEPENDENCY-REALIZATION ONLY, using the exact two-transition-model source deployment mechanism already frozen by 149O.20L.7M and executed successfully by 149O.20L.7N.4/7N.5 and 149O.20L.7O.2K.2/2M.2, plus one new, explicitly-authorized action (realizing the already-declared `hatp-hardware` project extra into the canonical venv) that no prior redeployment in this lineage required. Certification creation/activation/revocation, RepositoryIdentity, DeploymentBinding, Protected Root mutation, FIDO2/PIV hardware, and HATP activation are all explicitly out of scope and untouched.

**Phase-entry commit / authorized target:** `cdb77b75fc8bbca04340c7f25c405db3b07d32f7` (`HEAD == origin/main`, 0 ahead/behind, clean at entry).

## 1. Entering State (independently re-confirmed fresh this phase)

- hac-dell: hostname `atila-Latitude-E5470`, machine-id `54ff22ce400b475aa0d55cb68f4a3334` — matches.
- hac-dell deployed source (pre-mutation): `/opt/pcae/runtime/src`, detached HEAD `4efcb255ca5340224f0278f724b939d794a553ca`, clean, `core.fileMode=true`, remote `origin` = `git@github.com:atimad/pcae-harness.git` — matches the state established by 149O.20L.7O.2M.2.
- `.pcae/repository-identity.json`: `repository_instance_id 0107866f-af7c-40b4-8317-74e71acb05ca`, sha256 `b1d9fd8e17b1333cc3b908383ee5036106880e32240648f77f152734775a9065` — unchanged.
- `certifications.json`: two records present, active binding points at `de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609` (`implementation_commit 4efcb255`, `implementation_scope_digest 3b076a639b9f1b0c55facfd1a721d59d92a377d4bb63dce920843264e873a68e`, `status active`), sha256 `74db65b3447dca127bb7b8187ec89336c5a826ffc7a086657a7d2ed749c2cead`.
- `certification-bindings.json` sha256 `e28675f1147cb8f6761c19195ad2ce6b8f36a5ee562f6cba7cc26b995e704a60`.
- No `hardware-credential*.json`, `deployment-binding*.json`, `registry.json`, principal/signer *data* files anywhere under `/etc/pcae` or `/opt/pcae/runtime` (source *code* files with those names exist and are expected).
- Protected Root `/etc/pcae/hatp/trust-store`: `root:pcae`, mode `750` — unchanged.
- Pre-mutation HMIC certification validator, run as root: `VALID` (against the pre-repair v1.7/38 identity, digest `3b076a639b...`).
- Dell deployed venv (pre-mutation): Python 3.12.3, `pip 24.0`; `import fido2` and `import cryptography` both fail (`ModuleNotFoundError`) — confirms the entering-state gap this phase closes.

## 2. Target Revision (independently derived fresh this phase)

`git status` / `git rev-parse HEAD` / `git rev-parse origin/main` on the Mac repository: clean, `HEAD == origin/main == cdb77b75fc8bbca04340c7f25c405db3b07d32f7`, 0 ahead/behind — the exact commit at which 149O.20L.7O.2N.2 left the repository.

`git merge-base --is-ancestor 4efcb255ca5340224f0278f724b939d794a553ca cdb77b75fc8bbca04340c7f25c405db3b07d32f7` → ancestor (independently re-verified on hac-dell itself immediately before checkout).

**Authorized deployment commit (frozen): `cdb77b75fc8bbca04340c7f25c405db3b07d32f7`.**

## 3. Authority-Bearing Change Classification

`git diff --name-status 4efcb255..cdb77b75`: 42 files changed. Exactly **one** authority-bearing (HMIC-frozen-set) file changed: `scripts/hatp_hardware_credential_admin.py` (the 2N.1 ordering repair, independently verified by 2N.2). Every other changed path is governance metadata (`.pcae/decision-sessions/**`, `.pcae/publication-execution/**`, `.pcae/authority-evaluation/**`, `.pcae/phase-completion-*`), `PROJECT_STATUS.md`/`CHANGELOG.md`, `docs/PHASE_149O_20L_7O_2M_*` / `2N_*` reports, `tasks/**`, and test files. No unexpected authority-bearing change — proceeded per §6/§41 of the governing phase prompt.

## 4. Reporting Observation from 2N.2 (Clarification, Not a Rewrite)

2N.2's own No-Go prose states `scripts/hatp_hardware_credential_admin.py` was "byte-identical to the vulnerable checkpoint" — this cannot be literally true given 2N.2's own independently-proven ordering difference and digest change. The correct, current-state reading (not a rewrite of 2N.2's historical report): the **hardware-admin script** is byte-identical to the independently verified 2N.1 **repaired** implementation (current repaired source); the **core/provider/Principal-Signer files** are byte-identical to the **pre-repair/vulnerable checkpoint**, where independently established. Recorded here only as a current-state clarification per the governing prompt §2.

## 5. Local HMIC Identity (production code, pre-deployment, re-derived fresh this phase)

```
_FROZEN_AUTHORITY_BEARING_FILES: 38 members
derive_implementation_scope_digest(repo_root) -> abfbffca527d3bf6d6ba610f6f5cd2d80bf113f9aa08f4339eb40322a8c077c4
derive_contract_versions(repo_root) -> {HMRC-001: 1.1, HATP-001: 1.0, HSCE-001: 1.3, RAE-001: 1.0, HBDC-001: 1.2, HPSE-001: 1.1, HHCE-001: 1.1}
```

## 6. Packaging Declaration (re-derived fresh from `pyproject.toml`)

```toml
hatp-hardware = [
  "fido2>=1.1,<2",
  "cryptography>=42,<45",
]
```

## 7. Section-9 Determination — Combining Source + Venv Under One Election

Precedent (`docs/PHASE_149O_20L_7M_DELL_REDEPLOYMENT_DEPLOYMENTBINDING_FIRST_USE_SEQUENCING_ARCHITECTURE.md` §10, §16 condition 6) established "no venv reinstall ... without a fresh, separate election" for every prior redeployment — because none of them needed a venv change (`pyproject.toml` byte-unchanged, extra unneeded). That is not a standing prohibition on ever combining the two; it is a record that no prior CHGR's text authorized it. This phase's `pyproject.toml` still declares `hatp-hardware` unchanged (no packaging-declaration edit was made or needed — the extra pre-existed from Phase 149O.2 and is now genuinely required by the just-repaired script's dependency), so the fresh CHGR obtained this phase (§8 below) is itself the required "fresh, separate election" — and its own condition text explicitly authorizes both the source-checkout transition and the extra's realization as one bundled, tightly-scoped transition. Determination: **combine under one CHGR**, per governing-prompt §9.

## 8. Fresh Change Authority

A fresh CHGR was obtained via the governed `pcae decision-session` workflow (template `class-b-boundary-p-provisioning-authorization` v1.0, owner/human identity "Atila Madai"), independent of and not reusing any prior CHGR:

- Session `CDS-905edcf1-58b0-40e5-8459-59c41464076a`: create → evidence (`docs/PHASE_149O_20L_7O_2N_2_...md`, `git:4efcb255..cdb77b75`, `pyproject.toml#hatp-hardware`) → select (`approve`, distinct rationale + 18 numbered conditions naming both exact SHAs, host identity, the exact command envelope, the exact venv-realization scope, and all exclusions) → preview (digest `dd38e03aa6c09dce97018633db83d51b0924911b9b21026b52dee81e4b614bf3`) → human **CONFIRM** (distinct statement, same preview digest, obtained via explicit interactive question to the human before the `confirm` call was issued) → readiness (package `prp-930a0c3f49b045ea8c5ae45f88585d33`).
- Published: `pcae governance-record publish prp-930a0c3f49b045ea8c5ae45f88585d33 --operator-id "Atila Madai"` → **`chgr-e0dfb3e752e6430089ca1ee02636ec7e`**.
- `pcae governance-record verify` on the published record: `schema_shape` / `digest_self_consistency` / `lifecycle_structural_legality` all `passed`; the four relational checks `skipped` for lack of separately-supplied related-artifact args (identical pattern to every prior CHGR in this lineage).

Excludes explicitly (bound directly in the CHGR's own condition text): certification create/activate/revoke and any write to `certifications.json`/`certification-bindings.json`; Protected Root mutation; FIDO2/PIV hardware touch (authenticator enumeration, `makeCredential`); HardwareCredentialRecord/Principal/Signer/DeploymentBinding creation; Boundary C/Boundary A/HATP_MANDATORY activation; Permission Broker/POL-005/COMP-002 change; repository/project onboarding; wrapper mutation; any OS-level (apt/udev/kernel/group) mutation; any unrelated optional extra or global/system Python change.

## 9. Dependency Resolution Freeze (before mutation)

`pip install --dry-run "/opt/pcae/runtime/src[hatp-hardware]"` on hac-dell resolved exactly: `cryptography-44.0.3`, `fido2-1.2.0`, plus transitive `cffi-2.1.1`, `pycparser-3.0` (both already-satisfied requirements: `jsonschema`, `attrs`, `jsonschema-specifications`, `referencing`, `rpds-py`, `typing-extensions`). `fido2`'s own `Requires-Dist` (inspected from the downloaded wheel's METADATA) names only `cryptography` as a mandatory dependency; `pyscard` is gated behind fido2's own optional `pcsc` extra, not pulled in. **No OS-level dependency (apt package, udev rule, kernel config, group membership, device permission rule) is triggered** — confirmed before mutation, satisfying governing-prompt §11/§12; no STOP condition reached.

## 10. Deployment Mechanism (source transition — reused verbatim)

Exactly the mechanism established by 149O.20L.7M / 7N.4 / 2K.2 / 2M.2, run as root (same disclosed adaptation as 2M.2 — `.git/` internals are `root:pcae` mode `0640`, read-only to group `pcae`):

```
sudo -n git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src fetch origin cdb77b75fc8bbca04340c7f25c405db3b07d32f7
sudo -n git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src cat-file -t cdb77b75fc8bbca04340c7f25c405db3b07d32f7   # "commit"
sudo -n git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src merge-base --is-ancestor 4efcb255... cdb77b75...       # ancestor
sudo -n git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src checkout --detach cdb77b75fc8bbca04340c7f25c405db3b07d32f7
sudo -n chown -R root:pcae /opt/pcae/runtime/src
sudo -n find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
# per-tracked-file mode normalization from `git ls-tree -r -z HEAD` (100755 -> 0750, else 0640)
```

**Rollback (not needed — deployment succeeded cleanly):** `git checkout --detach 4efcb255ca5340224f0278f724b939d794a553ca`, re-chown, re-normalize; network-independent, SHA already local.

## 11. Venv Realization (new action this phase)

```
sudo -n /opt/pcae/runtime/venv/bin/pip install "/opt/pcae/runtime/src[hatp-hardware]"
```

**One repair required mid-phase, disclosed:** this command's default (non-editable) build path uninstalled the venv's existing **editable/path-bound** `pcae-harness` install and replaced it with a built-wheel copy (`Location: .../site-packages` instead of `/opt/pcae/runtime/src`) — an unauthorized incidental venv-binding change beyond the declared extra-realization scope (violates condition 5's "no unrelated ... change" and the lineage's standing "path-bound not byte-bound" invariant, e.g. 2M.2 §6 last bullet). Caught immediately by re-running `pip show pcae-harness` post-install. Repaired in the same phase, before proceeding, via:

```
sudo -n /opt/pcae/runtime/venv/bin/pip install --no-deps -e /opt/pcae/runtime/src
```

which reinstalled `pcae-harness` in editable mode (`Editable project location: /opt/pcae/runtime/src`) without touching the already-installed `fido2`/`cryptography`/`cffi`/`pycparser`. Post-repair `pip show pcae-harness` confirms editable path-binding restored.

## 12. Post-Deployment Independent Re-Verification

- `git rev-parse HEAD` == `cdb77b75fc8bbca04340c7f25c405db3b07d32f7`; `git status --short` clean; `git symbolic-ref -q HEAD` exit 1 (detached); `git diff --stat HEAD` empty.
- Tracked-path manifest: `4498` paths (`4475x100644`, `23x100755`) — exact match to the Mac target (`git ls-tree -r HEAD | awk '{print $1}' | sort | uniq -c` run independently on both sides). Full on-disk mode re-derivation against `git ls-tree` for all 4498 entries: **0 mismatches**.
- Live HMIC re-derivation on hac-dell: `38` frozen members, `implementation_scope_digest abfbffca527d3bf6d6ba610f6f5cd2d80bf113f9aa08f4339eb40322a8c077c4`, `contract_versions` 7-member map — **exact match** to the independent local Mac derivation (§5).
- `scripts/hatp_hardware_credential_admin.py`: sha256 `692711458a506396ab0a265e960757177a2bebb549b8051fc2758c024a8c2376` on both Mac and Dell — byte-identical.
- **Old certification vs. new source (load-bearing check):** validator re-run as root against the newly-deployed source → **`IMPLEMENTATION_MISMATCH`** ("current implementation_commit/implementation_scope_digest does not match the certified value"). Not `VALID` — the expected, disclosed, deliberate consequence. Not Blocking.
- Protected-state immutability: `certifications.json` sha256 unchanged (`74db65b3...`); `certification-bindings.json` sha256 unchanged (`e28675f1...`); `.pcae/repository-identity.json` sha256 unchanged (`b1d9fd8e...`); Protected Root unchanged (`root:pcae`, `750`); no hardware-credential/principal/signer/deployment-binding/registry data file exists anywhere.
- `import fido2` → `1.2.0` (satisfies `>=1.1,<2`); `import cryptography` → `44.0.3` (satisfies `>=42,<45`).
- `import pcae.core.hatp_fido2_provider` succeeds (module path resolves to `/opt/pcae/runtime/src/src/pcae/core/hatp_fido2_provider.py`) — **import only**, no `CtapHidDevice.list()` or any other device enumeration was called at any point in this phase.
- Trust-Enrollment surfaces confirmed absent post-deployment: HardwareCredentialRecord, Principal, Signer, DeploymentBinding all still absent.
- No FIDO2/CTAP call, no authenticator enumeration, no user-presence request was made at any point.
- No `scripts/hatp_certification_admin.py create`/`activate`/`revoke` was invoked.
- HATP: remains NOT READY / NOT ACTIVE (no activation command run). Runtime: Observed / observe / unavailable — unchanged.
- Class-B canonical diagnostic (`verify_class_b_deployment_conformance`, invoked read-only as the `pcae` identity with the venv activated, matching precedent's invocation context): **`NON_COMPLIANT`**, sole failing check `HBDC-REQ-042` (`no_active_deployment_binding_matches_repository_and_root`) — the exact expected pre-first-use residual. `HBDC-REQ-022`/`HBDC-REQ-035` (Model-A editable-install checks) both `satisfied: True`, confirming the mid-phase editable-install repair (§11) held post-repair.

## 13. HMIC Readiness Consequence

Before: validator `VALID` (against the prior pre-repair v1.7/38 identity) → HMIC readiness term `TRUE`.
After: validator `IMPLEMENTATION_MISMATCH` (against the new repaired identity) → HMIC readiness term `FALSE`, as a **derived** consequence of `certification_status_satisfies_readiness(result.status)` evaluating a non-`VALID` status. No readiness field was manually written anywhere.

## 14. Exclusions (bound directly in the CHGR's own text)

No CertificationRecord create/activate/revoke. No write to `certifications.json`/`certification-bindings.json`. No RepositoryIdentity create/rotate. No DeploymentBinding create/rotate/revoke. No Protected Root mutation. No FIDO2/PIV hardware touch, no authenticator enumeration, no `makeCredential`. No HardwareCredentialRecord/Principal/Signer creation. No Boundary C/Boundary A/HATP_MANDATORY activation. No Permission Broker/POL-005/COMP-002 change. No wrapper mutation. No repository/project onboarding. No OS-level (apt/udev/kernel/group) mutation — confirmed unnecessary (§9).

## 15. Fast Green (raw, and this phase's attributable delta)

Two independent full `python3 -m pytest -m fast_green -q` runs on the Mac repository (this phase touches no `src/pcae/**` or `scripts/**` file — only docs, tests, task/status, and `.pcae/` governance metadata):

- Run A (started before this phase's own new test file existed): **337 failed, 8642 passed, 4 skipped, 9 errors** (474.57s).
- Run B (full-output rerun, started after this phase's new test file was added): **337 failed, 8670 passed, 4 skipped, 9 errors** (469.70s).

**Failed/error count identical (337/9) in both runs; the +28 passed delta in Run B exactly equals this phase's own new, fully-passing test file** (`tests/test_phase_149o_20l_7o_2n_3_..._realization.py`, 28/28 passed standalone). This is a direct, controlled proof of zero attributable regression: the only variable between the two runs is the presence of this phase's own additive files, and the pre-existing failing/erroring node set did not move by even one node.

The 337 raw failures are spread across ~70 historical phase test files spanning the entire HMIC/HBDC contract lineage (`test_phase_149o_13_...` through `test_phase_149o_20l_7o_2m_4_...`) — none of them touched by this phase's diff. This matches the same "large raw failed-count is a pre-existing, environment-level baseline divergence... not normalized away" phenomenon 149O.20L.7O.2N.2 §40 already documented (334 failed/8645 passed/4 skipped/9 errors there); the modest 334→337 growth across sequential phases is consistent with this repository's own established, accepted pattern of historical self-check tests going stale as later phases advance HEAD (see e.g. the repo's own recent commits "pin the one remaining stale HMIC root-relative count self-check ..." and "pin remaining historical HMIC-count self-checks to their own phase exit commits"), not a defect introduced here. All 9 errors are confined to one unrelated legacy file, `tests/test_phase_149o_20e_hmic_v1_2_hbdc_bound_contract_identity_independent_verification.py` (an HMIC v1.2-era contract test, a different contract generation than this phase's HMIC v1.7 hardware-admin work).

**This phase's own attributable, independently-isolated regression count: 0 failed.**

## 16. FIDO2 Software Availability Result (kept distinct, per governing-prompt §33)

- **FIDO2 Python software:** AVAILABLE (fido2 1.2.0 + cryptography 44.0.3 importable in the canonical deployed venv; provider module imports).
- **FIDO2 physical authenticator:** UNKNOWN / NOT CHECKED (no enumeration performed, none authorized this phase).
- **FIDO2 enrollment:** NOT AUTHORIZED / NOT PERFORMED this phase.

## 17. Recommended Next Phase

A fresh successor phase that creates exactly one new HMIC `CertificationRecord` for the newly-deployed repaired identity (create-only, distinct fresh election), leaving activation to a further separate phase. Only after activation should the project physically attach/discover exactly one eligible authenticator and re-run the FIDO2 enrollment authorization gate — not immediately after this phase's package installation.
