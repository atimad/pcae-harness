# Phase 149O.20L.7O.2K.2 — hac-dell Governed Source Synchronization / Redeployment and Source-Parity Restoration

## 0. Status

Single-phase compressed proposition + independent-style re-derivation + human election + CHGR publication + execution + post-deployment verification, following the exact deployment mechanism established and executed once already by 149O.20L.7N through 7N.5 (the "two-transition model" from 149O.20L.7M). Certification, RepositoryIdentity, DeploymentBinding, Protected Root, and all first-use/HATP-activation surfaces are explicitly out of scope and untouched.

**Phase-entry commit:** `305f8e7913bac76941dade6ff4e018c74533f062`. `origin/main == HEAD`, 0 commits ahead/behind, working tree clean at entry (only this task's own new files untracked).

## 1. Entering State (independently re-confirmed fresh this phase)

- hac-dell: hostname `atila-Latitude-E5470`, machine-id `54ff22ce400b475aa0d55cb68f4a3334` — matches.
- hac-dell deployed source: `/opt/pcae/runtime/src`, detached HEAD `b0840e96a7ffb12308e95828aa5927c3e7c770c0`, clean, `core.fileMode=true`, remote `origin` = `git@github.com:atimad/pcae-harness.git`.
- hac-dell `.pcae/repository-identity.json`: `repository_instance_id 0107866f-af7c-40b4-8317-74e71acb05ca` (pre-existing, gitignored, NOT part of the tracked tree — untouched by any source-checkout transition; created by an earlier, separately-governed first-use phase, not this one).
- No `deployment-binding*.json`, `certifications.json`, `certification-bindings.json`, `hardware-credential*.json`, or `registry.json` anywhere under `/opt/pcae/runtime`.
- Protected Root `/etc/pcae/hatp/trust-store`: `root:pcae`, mode `750`, empty.
- Pre-mutation tree inventory: `4200` tracked paths (`4186×100644`, `14×100755`), independently re-enumerated this phase.
- Wrapper `/opt/pcae/runtime/bin/pcae-launch` sha256 `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`.
- venv: editable install, `.pth` → `/opt/pcae/runtime/src/src` (path-bound, not byte-bound); `direct_url.json` → `file:///opt/pcae/runtime/src` (`editable: true`).

## 2. Target Revision (independently derived fresh this phase — not reused from 2K.1's phase-entry commit)

`git status --short` / `--branch --short` / `git log --oneline origin/main..HEAD` / `git rev-list --count origin/main..HEAD` / `git rev-parse HEAD` / `git rev-parse origin/main` all independently re-run: repository clean, `HEAD == origin/main == 305f8e7913bac76941dade6ff4e018c74533f062`, 0 ahead/behind.

The nine commits between 2K.1's phase-entry commit (`0e8923c4`) and this phase's entry commit (`305f8e79`) are all 2K.1's own governance/report bookkeeping; `git diff --stat 0e8923c4..305f8e79 -- src/pcae scripts docs/contracts schemas pyproject.toml` is empty — zero authority-bearing drift.

**Authorized deployment commit (frozen): `305f8e7913bac76941dade6ff4e018c74533f062`.**

## 3. Deployment Content Model / Repository Root Resolution (independently re-derived, per prompt §7/§9)

`/opt/pcae/runtime/src` is confirmed (via the live `.pth`/`direct_url.json`, the live 4200-path tree inventory matching this Mac repository's own tracked-file count, and the presence of `docs/contracts/`, `scripts/`, `.pcae/` under it) to be a **full git checkout of the repository root**, not a `src/pcae/`-only export. HMIC canonical paths (`docs/contracts/...`, `scripts/...`, `core/paths.py`, etc.) resolve directly beneath it. No new root-arrangement ambiguity — this matches the precedent established and independently verified by 149O.20L.7N.5.

## 4. Old→Candidate Diff (independently classified)

```
git merge-base --is-ancestor b0840e96a7ffb12308e95828aa5927c3e7c770c0 305f8e7913bac76941dade6ff4e018c74533f062 -> ancestor (exit 0)
git diff --stat b0840e96a7...305f8e79 -- (repo root)   -> 287 files changed, 44222 insertions(+), 660 deletions(-)
git diff --name-status b0840e96a7...305f8e79            -> 202 A, 59 M, 26 R099, 0 D (zero file removals)
git diff --name-only b0840e96a7...305f8e79 -- pyproject.toml -> (empty, byte-unchanged)
```

Zero deletions means **file-removal policy (prompt §16) is inapplicable this transition** — a plain overlay via `git checkout --detach` cannot leave stale executable authority code, since no tracked file is removed between old and candidate. `pyproject.toml` byte-unchanged — no dependency/package parity action required (prompt §18: not triggered).

## 5. HMIC Architecture Independently Reconstructed (local, pre-deployment)

```
_FROZEN_AUTHORITY_BEARING_FILES: 36 members (independently enumerated from src/pcae/core/hatp_mandatory_certification.py)
derive_implementation_scope_digest(HarnessPath(repo_root)) -> cd021db4b6b74d6d62420be7f74f3791e759a72f142ffb151640d2b88d39412f
derive_contract_versions(HarnessPath(repo_root)) -> {HMRC-001: 1.1, HATP-001: 1.0, HSCE-001: 1.3, RAE-001: 1.0, HBDC-001: 1.2, HPSE-001: 1.1, HHCE-001: 1.1}   (7 members)
_CERTIFICATION_RECORD_REQUIRED_FIELDS -> 7 required keys (ALLOWED_FIELDS minus optional revoked_at)
```

This is the expected post-deployment target architecture — HMIC v1.6, 36 frozen members, 7 contract identities, 7 CertificationRecord required keys, matching the phase prompt's stated current identity.

## 6. Deployment Mechanism (reused verbatim from 149O.20L.7N/7N.4 — no new mechanism invented)

Exactly the mechanism established by 149O.20L.7M ("two-transition model") and executed once already by 149O.20L.7N.4: hac-dell's own git checkout fetches the exact candidate SHA (no branch, no `git pull`, no `rsync`/`scp`) from the existing `origin` remote (deploy key already provisioned and already used for the prior transition), verifies the fetched object is a commit, performs a `git checkout --detach` to the exact SHA, restores `root:pcae` ownership, and normalizes file modes from Git's own executable bit (`100644→0640`, `100755→0750`) via a two-branch `find`, never a blanket `chmod`. venv and wrapper are retained unchanged (§4 above proves `pyproject.toml` byte-identity; the editable install and wrapper are both structurally path-bound, not byte-bound, exactly as 7N/7N.5 independently proved for the prior transition).

### Exact Mutation Envelope

**READ-ONLY PRECHECK** (run fresh immediately before mutation):
```
ssh hac-dell hostname
ssh hac-dell cat /etc/machine-id
sudo -n -u pcae git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src rev-parse HEAD
sudo -n -u pcae git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src status --short
sudo -n -u pcae git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src symbolic-ref -q HEAD   (expect exit 1, detached)
```

**AUTHORIZED SOURCE MUTATION** (scoped exactly to `/opt/pcae/runtime/src`):
```
sudo -n -u pcae git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src fetch origin 305f8e7913bac76941dade6ff4e018c74533f062
sudo -n -u pcae git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src cat-file -t 305f8e7913bac76941dade6ff4e018c74533f062   (expect "commit")
sudo -n -u pcae git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src checkout --detach 305f8e7913bac76941dade6ff4e018c74533f062
sudo -n chown -R root:pcae /opt/pcae/runtime/src
sudo -n -u pcae git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src ls-tree -r -z --name-only HEAD -- | while IFS= read -r -d '' f; do mode=$(sudo -n -u pcae git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src ls-tree HEAD -- "$f" | cut -d' ' -f1); if [ "$mode" = "100755" ]; then sudo -n chmod 0750 "/opt/pcae/runtime/src/$f"; else sudo -n chmod 0640 "/opt/pcae/runtime/src/$f"; fi; done
sudo -n find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
```

**READ-ONLY POSTCHECK**: full re-derivation per §7 below.

**ROLLBACK** (only if postcheck deviates): `git checkout --detach b0840e96a7ffb12308e95828aa5927c3e7c770c0`, re-chown, re-normalize modes, identical mechanism, network-independent (SHA already local from the prior 7N.4 transition's git history).

## 7. Post-Deployment Independent Re-Verification (performed after mutation — see phase report Test Results)

HEAD/detached/clean/remote/fileMode; 4200-path (net file-count unchanged, zero deletions in the diff) mode inventory; zero `git diff --stat HEAD` drift; the 36 HMIC frozen-set files re-derived live on Dell; live `derive_implementation_scope_digest` and `derive_contract_versions` invoked under the deployed venv; `scripts/hatp_certification_admin.py --help` only (no `create`); `hatp_deployment_binding_admin.py` presence-only; Class-B diagnostic (expected residual: `NON_COMPLIANT`, sole reason `HBDC-REQ-042`); RepositoryIdentity file byte-unchanged; DeploymentBinding/certification/hardware-credential/registry files still absent; Protected Root unchanged; venv/wrapper unchanged.

## 8. Exclusions (bound directly in the CHGR's own text)

No RepositoryIdentity create/rotate. No DeploymentBinding create/rotate/revoke. No HMIC certification. No Boundary C/Boundary A/HATP_MANDATORY activation. No Cutover Record. No Permission Broker/POL-005/COMP-002 change. No venv reinstall. No wrapper mutation. No repository onboarding. No unrelated Dell user/service/`hac-windows` access.

## 9. Recommended Next Phase

If source parity is restored: a fresh successor phase that re-runs 149O.20L.7O.2K.1's complete read-only prechecks against the newly deployed source (treated as fresh evidence, not this phase's report alone) and then performs only the HMIC CertificationRecord `create` action, with a fresh Protected Admin Authority election and explicit human confirmation at that time.
