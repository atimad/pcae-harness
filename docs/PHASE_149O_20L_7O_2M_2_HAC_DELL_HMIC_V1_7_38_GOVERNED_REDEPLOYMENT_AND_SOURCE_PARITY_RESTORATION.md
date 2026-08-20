# Phase 149O.20L.7O.2M.2 — hac-dell HMIC v1.7/38 Governed Redeployment and Source-Parity Restoration

## 0. Status

Single-phase real-effect execution. REDEPLOYMENT ONLY, using the exact two-transition-model deployment mechanism already frozen by 149O.20L.7M and executed successfully by 149O.20L.7N.4/7N.5 and 149O.20L.7O.2K.2. Certification creation/activation/revocation, RepositoryIdentity, DeploymentBinding, Protected Root mutation, FIDO2/PIV hardware, and HATP activation are all explicitly out of scope and untouched.

**Phase-entry commit / authorized target:** `4efcb255ca5340224f0278f724b939d794a553ca` (`HEAD == origin/main`, 0 ahead/behind, clean at entry).

## 1. Entering State (independently re-confirmed fresh this phase)

- hac-dell: hostname `atila-Latitude-E5470`, machine-id `54ff22ce400b475aa0d55cb68f4a3334` — matches.
- Administrative identity `codex`; deployment identity `pcae`.
- hac-dell deployed source: `/opt/pcae/runtime/src`, detached HEAD `305f8e7913bac76941dade6ff4e018c74533f062`, clean, `core.fileMode=true`, remote `origin` = `git@github.com:atimad/pcae-harness.git` — matches the state established by 149O.20L.7O.2K.2.
- `.pcae/repository-identity.json`: `repository_instance_id 0107866f-af7c-40b4-8317-74e71acb05ca`, sha256 `b1d9fd8e17b1333cc3b908383ee5036106880e32240648f77f152734775a9065` — unchanged from 2K.2.
- `certifications.json` (root:root 0600 under `/etc/pcae/hatp/trust-store`, root:pcae 0750): one active record, `certification_id 2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`, `implementation_commit 305f8e79`, `implementation_scope_digest cd021db4b6b74d6d62420be7f74f3791e759a72f142ffb151640d2b88d39412f`, `status active`, `certified_by Atila Madai`, sha256 `df6e2db036f36c30bd673f0ab3ce4fbf1158810d1821c98d87f8e13ecf10255a`.
- `certification-bindings.json`: one binding for `(0107866f-af7c-40b4-8317-74e71acb05ca, /opt/pcae/runtime/src)` -> the record above, sha256 `8eb4a33aa4f1d365a572a072a12982e66e0cbaca7a9ca3692fb5c16b9e8f4374`.
- No `hardware-credential*.json`, `deployment-binding*.json`, `registry.json`, principal/signer files anywhere under `/etc/pcae` or `/opt/pcae/runtime`.
- Protected Root `/etc/pcae/hatp/trust-store`: directory, `root:pcae`, mode `750` — unchanged.
- Pre-mutation tree inventory (Mac target): `4463` tracked paths (`4442x100644`, `21x100755`).
- Old->candidate diff (`305f8e79..4efcb255`): 76 files changed, `61 A / 14 M / 1 R`, **zero deletions**; `pyproject.toml` byte-unchanged (no dependency/venv action required).
- Pre-mutation HMIC certification validator, run **as root** (the trust-store files are `root:root` mode `0600` — unreadable by `pcae`; running as `pcae` mis-reports `MALFORMED` due to a plain permission-denied read, not a real schema defect): `VALID` — "certification is valid: repository, deployment, implementation, contract, and revocation checks all passed", matching the prior HMIC v1.6/36 deployed identity.

## 2. Target Revision (independently derived fresh this phase)

`git status` / `git rev-parse HEAD` / `git rev-parse origin/main` / `git log --oneline origin/main..HEAD` / `git log --oneline HEAD..origin/main` all independently re-run at phase entry: clean, `HEAD == origin/main == 4efcb255ca5340224f0278f724b939d794a553ca`, 0 ahead/behind. This is the exact commit at which 149O.20L.7O.2M.1 (HMIC v1.7/38, independently verified) left the repository — no later phase-opening-only commits exist to chase; the repo is at rest.

`git merge-base --is-ancestor 305f8e7913bac76941dade6ff4e018c74533f062 4efcb255ca5340224f0278f724b939d794a553ca` -> ancestor (exit 0).

**Authorized deployment commit (frozen): `4efcb255ca5340224f0278f724b939d794a553ca`.**

## 3. Local HMIC Identity (production code, pre-deployment)

```
_FROZEN_AUTHORITY_BEARING_FILES: 38 members
derive_implementation_scope_digest(repo_root) -> 3b076a639b9f1b0c55facfd1a721d59d92a377d4bb63dce920843264e873a68e
derive_contract_versions(repo_root) -> {HMRC-001: 1.1, HATP-001: 1.0, HSCE-001: 1.3, RAE-001: 1.0, HBDC-001: 1.2, HPSE-001: 1.1, HHCE-001: 1.1}
RepositoryIdentity expectation: 0107866f-af7c-40b4-8317-74e71acb05ca
```

Includes both newly-frozen admin scripts: `scripts/hatp_hardware_credential_admin.py`, `scripts/hatp_principal_signer_admin.py`.

## 4. Fresh Change Authority

A fresh CHGR was obtained via the governed `pcae decision-session` workflow (template `class-b-boundary-p-provisioning-authorization` v1.0, owner/human identity "Atila Madai"), independent of and not reusing 2K.2's authority:

- Session `CDS-08a5564c-50fb-4153-a329-ee6b62f82910`: create -> evidence -> select (`approve`, distinct rationale + 17 numbered conditions naming both exact SHAs, the exact command envelope, and all exclusions) -> preview (digest `037f34ff49fb904b280b3a8d66107a7791c4a7de7680bbdbd21efce30c9ed426`) -> **confirm** (distinct human CONFIRM statement, same preview digest) -> readiness (package `prp-127921067df84d6d8c0d2bd943e39888`).
- Published: `pcae governance-record publish prp-127921067df84d6d8c0d2bd943e39888 --operator-id "Atila Madai"` -> **`chgr-d8329c0a5874483ba6766774b8562cbb`**.
- `pcae governance-record verify` on the published record: `schema_shape` / `digest_self_consistency` / `lifecycle_structural_legality` all `passed`; the three relational checks (`confirmation_binding`, `provenance_consistency`, `template_resolution`) `skipped` for lack of separately-supplied related-artifact args (identical pattern to every prior CHGR in this lineage).

Excludes explicitly (bound directly in the CHGR's own condition text): certification create/activate/revoke and any write to `certifications.json`/`certification-bindings.json`; Protected Root mutation; FIDO2/PIV hardware touch; HardwareCredentialRecord/Principal/Signer/DeploymentBinding creation; Boundary C/Boundary A/HATP_MANDATORY activation; Permission Broker/POL-005/COMP-002 change; repository/project onboarding; venv/wrapper mutation.

## 5. Deployment Mechanism (reused verbatim, one necessary adaptation)

Exactly the mechanism established by 149O.20L.7M / 149O.20L.7N.4 / 149O.20L.7O.2K.2: hac-dell's own git checkout fetches the exact candidate SHA from the existing `origin` remote (no branch, no `git pull`, no `rsync`/`scp`), verifies the fetched object is a commit, performs `git checkout --detach`, restores `root:pcae` ownership, and normalizes file modes from Git's own executable bit (`100644->0640`, `100755->0750`) via a two-branch `find`, never a blanket `chmod`.

**One necessary, disclosed adaptation from 2K.2's literal command text:** `git fetch`/`cat-file`/`checkout` were run **as root** rather than `sudo -n -u pcae git ...`. Live precheck showed `.git/FETCH_HEAD` (and the rest of `.git/`'s internal loose files) are `root:pcae` mode `0640` -- group `pcae` has read-only access, not write -- so `pcae`-user `git fetch` fails closed with `Permission denied` (confirmed; not attempted as a workaround, this is the actual filesystem state produced by the prior transition's own mode-normalization, which does not touch `.git/` internals since they are not part of `git ls-tree`'s tracked-file walk). Running the identical commands as root (the same identity already required to read the trust-store validator state, see §1) succeeds and is within the CHGR's authorized scope (source-checkout transition at `/opt/pcae/runtime/src`, condition 4's command sequence) -- no new mechanism, host, path, or credential was introduced.

### Exact Mutation Envelope (as executed)

```
sudo -n git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src fetch origin 4efcb255ca5340224f0278f724b939d794a553ca
sudo -n git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src cat-file -t 4efcb255ca5340224f0278f724b939d794a553ca   # "commit"
sudo -n git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src checkout --detach 4efcb255ca5340224f0278f724b939d794a553ca
sudo -n chown -R root:pcae /opt/pcae/runtime/src
# per-tracked-file mode normalization from `git ls-tree -r -z HEAD` (100755 -> 0750, else 0640)
sudo -n find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
```

**Rollback (not needed -- deployment succeeded cleanly):** `git checkout --detach 305f8e7913bac76941dade6ff4e018c74533f062`, re-chown, re-normalize; network-independent, SHA already local.

## 6. Post-Deployment Independent Re-Verification

- `git rev-parse HEAD` == `4efcb255ca5340224f0278f724b939d794a553ca`; `git status --short` clean; `git symbolic-ref -q HEAD` exit 1 (detached); `git diff --stat HEAD` empty.
- Tracked-path manifest: `4463` paths (`4442x100644`, `21x100755`) -- exact match to the Mac target. Full on-disk mode re-derivation against `git ls-tree` for all 4463 entries: **0 mismatches**.
- Live HMIC re-derivation on hac-dell (under the deployed venv): `38` frozen members (includes both new admin scripts), `implementation_scope_digest 3b076a639b9f1b0c55facfd1a721d59d92a377d4bb63dce920843264e873a68e`, `contract_versions` 7-member map -- **exact match** to the independent local Mac derivation (§3).
- Both admin scripts: sha256 byte-identical to the Mac target (`hatp_hardware_credential_admin.py` `1013d78484d4c31ec4369ca02af406d6a00c822243fe26ac3dba630fd3ed8517`; `hatp_principal_signer_admin.py` `a4bfde42afb5290b29869f761bcaa6d9257d4166e9076028e56c3f0d8ae43f43`). `--help` only: hardware admin's public surface is exactly `{enroll, revoke}` -- no `recover`. No mutating subcommand invoked.
- **Old certification vs. new source (load-bearing check):** validator re-run as root against the newly-deployed source -> **`IMPLEMENTATION_MISMATCH`** ("current implementation_commit/implementation_scope_digest does not match the certified value"). Not `VALID` -- the expected, disclosed, deliberate consequence. Not Blocking.
- Protected-state immutability: `certifications.json` sha256 unchanged (`df6e2db0...`); `certification-bindings.json` sha256 unchanged (`8eb4a33a...`); `.pcae/repository-identity.json` sha256 unchanged (`b1d9fd8e...`); Protected Root unchanged (`root:pcae`, `750`); no hardware-credential/principal/signer/deployment-binding/registry file created anywhere.
- Class-B canonical diagnostic, invoked as the deployment identity `pcae` with the venv activated (matching the precedent's actual invocation context -- `which pcae` only resolves once the venv's console-script shim is on `PATH`; invoking as root or without the venv activated produces spurious additional failures that are an artifact of the wrong invocation identity/PATH, not real drift, and were explicitly diagnosed and discarded before recording this result): **`NON_COMPLIANT`**, sole failing check `HBDC-REQ-042` (`no_active_deployment_binding_matches_repository_and_root`) -- the exact expected pre-first-use residual.
- HATP: remains NOT READY / NOT ACTIVE. Runtime: Observed / observe / unavailable -- unchanged.
- Trust-Enrollment surfaces confirmed absent post-deployment: HardwareCredentialRecord, Principal, Signer, DeploymentBinding all still absent.
- No FIDO2/CTAP call, no authenticator enumeration, no user-presence request was made at any point.
- No `scripts/hatp_certification_admin.py create`/`activate`/`revoke` was invoked.
- Dependency/venv: `pyproject.toml` byte-unchanged between old and new source; venv/wrapper untouched (both are structurally path-bound, not byte-bound, as independently re-confirmed by every prior transition in this lineage).

## 7. HMIC Readiness Consequence

Before: validator `VALID` (against the prior v1.6/36 identity) -> HMIC readiness term `TRUE`.
After: validator `IMPLEMENTATION_MISMATCH` (against the new v1.7/38 identity) -> HMIC readiness term `FALSE`, as a **derived** consequence of `certification_status_satisfies_readiness(result.status)` evaluating a non-`VALID` status. No readiness field was manually written anywhere.

## 8. Exclusions (bound directly in the CHGR's own text)

No CertificationRecord create/activate/revoke. No write to `certifications.json`/`certification-bindings.json`. No RepositoryIdentity create/rotate. No DeploymentBinding create/rotate/revoke. No Protected Root mutation. No FIDO2/PIV hardware touch. No HardwareCredentialRecord/Principal/Signer creation. No Boundary C/Boundary A/HATP_MANDATORY activation. No Permission Broker/POL-005/COMP-002 change. No venv reinstall. No wrapper mutation. No repository/project onboarding.

## 9. Recommended Next Phase

A fresh successor phase that creates exactly one new HMIC `CertificationRecord` for the newly-deployed v1.7/38 identity (create-only, distinct fresh election), leaving activation to a further separate phase. Real FIDO2 enrollment remains out of scope until after activation.
