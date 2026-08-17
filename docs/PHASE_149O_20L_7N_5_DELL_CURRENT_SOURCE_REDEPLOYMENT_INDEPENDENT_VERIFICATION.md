# Phase 149O.20L.7N.5 — Dell Current-Source Redeployment Independent Verification

## 0. Status

**Verification-only. INDEPENDENTLY VERIFIED — CURRENT SOURCE DEPLOYMENT COMPLETE.** This phase independently re-derived every claim of Phase 149O.20L.7N.4 from primary source and a fresh, read-only SSH session to `hac-dell`, without importing or trusting 7N.4's report, evidence module, or any prior SSH session as an oracle. No Dell mutation was performed. No RepositoryIdentity or DeploymentBinding was created. No HMIC certification was performed. Boundary C/A and HATP activation remain untouched and **NOT AUTHORIZED**.

**Phase-entry commit:** `6678bb98` (`Phase 149O.20L.7N.4: repair pcae_push_check literal for finalization gate`). `origin/main == HEAD`, 0 commits ahead/behind, working tree clean at entry.

## 1. Local Entry Checks

- `git status --short` / `--branch --short`: clean, `origin/main..HEAD` = 0 commits.
- `pcae health`: healthy, all required files present, git status clean.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: only pre-existing DONE.md-listing warnings (unrelated to this phase).
- `pcae push check`: not_ready at entry (no canonical phase report yet — expected before finalization).
- `pcae runtime inspect`: Runtime state Observed / observe / unavailable, Permission Broker `execution_unavailable`, governance posture non-executing — matches expected §1/§40.
- `pcae notify status`: Telegram configured/enabled.
- `pcae phase-report show --latest`: none found (expected pre-finalization).
- `pcae phase-report reconcile --phase-id 149O.20L.7N.4`: status `conflict`, blocker "no promoted report generation found for phase" (no canonical report was ever promoted for 7N.4 — carried forward as observation, not repaired in this phase).

## 2. Local Candidate Reconstruction

```
git cat-file -t b0840e96a7ffb12308e95828aa5927c3e7c770c0   -> commit
git cat-file -t 28bf137b5dc95d024e8913b678dce0501a46fd0f    -> commit
git merge-base --is-ancestor b0840e96... origin/main         -> true (ancestor)
```

Old→candidate diff (`git diff --stat 28bf137b...b0840e96`) spans 104 files across the whole 7D–7N phase chain (not a 5-file diff — the two SHAs are separated by many phases). The **five HMIC/HBDC-bound-contract files** that changed and matter for byte-identity purposes were identified from that diff plus the frozen-set definition:

1. `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001)
2. `docs/PHASE_.../HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` → actually `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` (HMIC-001)
3. `scripts/hatp_deployment_binding_admin.py` (producer admin ceremony script)
4. `src/pcae/core/hatp_deployment_binding_admin.py` (producer core module)
5. `src/pcae/core/hatp_mandatory_certification.py` (frozen-set / HMIC implementation module)

Source locations independently found via grep (not assumed): `derive_implementation_scope_digest` at `src/pcae/core/hatp_mandatory_certification.py:1213`; frozen-set constants `_FROZEN_SRC_PCAE_RELATIVE_FILES` / `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` / `_FROZEN_AUTHORITY_BEARING_FILES` at lines 960–1025 (`assert len(...) == 30`, HMIC-REQ-050 v1.4); `derive_contract_versions` at line 1274.

30-member frozen set reconstructed locally: 23 `src/pcae/`-relative + 7 repository-root-relative (5 bound contracts + 2 admin scripts) = 30. Matches the live Dell reconstruction exactly (§6 below).

## 3. Fresh SSH Session and Machine Identity

A fresh `ssh hac-dell` session was opened (no reuse of prior session state).

| Item | Expected | Live | Match |
|---|---|---|---|
| hostname | `atila-Latitude-E5470` | `atila-Latitude-E5470` | Yes |
| `/etc/machine-id` | `54ff22ce400b475aa0d55cb68f4a3334` | `54ff22ce400b475aa0d55cb68f4a3334` | Yes |
| `uname -m` | — | `x86_64` | — |
| `/etc/os-release` | — | Ubuntu 24.04.3 LTS (Noble Numbat) | — |

All remote commands were read-only (`git rev-parse`, `git status`, `git ls-tree`, `git hash-object`, `stat`, `find`, `sha256sum`, `id`, `cat` of non-secret files, and read-only Python imports/function calls). `sudo` was required for `codex`'s SSH principal to read root:pcae-owned paths (0750); no write/mutating command was ever issued.

## 4. Exact Live Source SHA / Detached / Clean State

```
sudo git -C /opt/pcae/runtime/src rev-parse HEAD  -> b0840e96a7ffb12308e95828aa5927c3e7c770c0   (exact match)
sudo git -C /opt/pcae/runtime/src symbolic-ref -q HEAD -> exit 1 (no symbolic ref: detached)
sudo git -C /opt/pcae/runtime/src status          -> "HEAD detached at b0840e96" / "nothing to commit, working tree clean"
sudo git -C /opt/pcae/runtime/src config --get core.fileMode -> true
sudo git -C /opt/pcae/runtime/src remote -v       -> origin git@github.com:atimad/pcae-harness.git (fetch/push)
sudo git -C /opt/pcae/runtime/src diff --stat HEAD -> (empty)
```

## 5. Candidate Tree Inventory (Independent, Live)

`sudo git -C /opt/pcae/runtime/src ls-tree -r --long HEAD`, independently enumerated and tallied (not taken from the 7N.4 report):

- Total tracked paths: **4200**
- Mode `100644`: **4186**
- Mode `100755`: **14**
- Mode `120000` (symlink): **0**
- Mode `160000` (submodule/gitlink): **0**

Exact match to expected.

## 6. Complete Filesystem-Mode Verification (All 4200 Paths)

Independently enumerated via `git ls-tree -r -z HEAD` (NUL-delimited, path-safe for spaces/special characters), and for every one of the 4200 entries, `stat -c %a` was run against the live on-disk path and compared to the expected mapping (`100644 → 0640`, `100755 → 0750`).

**Result: 4200/4200 checked, 0 mismatches.**

## 7. Directory Mode / Trust Model

All 142 tracked directories under `/opt/pcae/runtime/src` are `750 root:pcae`. `find ... -perm -o+w` returned no world-writable paths. No writable-path regression found.

## 8. Complete Tracked-Content Identity

`git status` (clean) plus `git diff --stat HEAD` (empty) plus an independent hash-based per-blob comparison (§9) together establish tracked-content identity — not `git status` alone.

## 9. Five Changed-File and Full 30-File HMIC Byte Identity

Independent method: local candidate blob SHAs were computed via `git cat-file --batch-check` against `b0840e96...:<path>` for all 30 canonical HMIC authority-bearing paths (§2/§6 list). These 30 `(sha, path)` pairs were transferred to Dell over the existing SSH channel (no separate untrusted channel) and, on Dell, `sudo git -C /opt/pcae/runtime/src hash-object -- <path>` was run **fresh, independently** for each of the 30 live files and compared byte-for-byte to the local candidate blob SHA.

**Result: 30/30 OK, 0 mismatches.** (This set includes all five HBDC/HMIC-bound-contract and producer files identified in §2.)

## 10. Live Frozen-Set Reconstruction

On Dell, under the deployed venv and deployed candidate source, `_FROZEN_AUTHORITY_BEARING_FILES` was imported and printed directly from `pcae.core.hatp_mandatory_certification`:

```
FROZEN_COUNT: 30
```

The live-printed 30-entry list matches the locally reconstructed list (§2) entry-for-entry, same order. Zero divergence.

## 11. Live HMIC Implementation/Source Digest

Computed live, on Dell, under the deployed venv (`/opt/pcae/runtime/venv/bin/python3`) and deployed candidate source, by actually invoking `derive_implementation_scope_digest(HarnessPath(Path("/opt/pcae/runtime/src")))` from `pcae.core.hatp_mandatory_certification` (imported fresh from `/opt/pcae/runtime/src/src`, run as the `pcae` OS principal via `sudo -u pcae`, sanitized environment):

```
DIGEST: 65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8
```

**Exact match to expected.** Not a copied/pasted value — the function was actually executed read-only on Dell this session.

## 12. HMIC/HBDC Contract Identity

Local contract-source inspection: `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` states **Contract ID: HMIC-001, Version: 1.4**. `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` states **Contract: HBDC-001, Version: 1.1**.

Live, on Dell, `derive_contract_versions(HarnessPath(...))` was invoked and returned:

```
{'HMRC-001': '1.1', 'HATP-001': '1.0', 'HSCE-001': '1.1', 'RAE-001': '1.0', 'HBDC-001': '1.1'}
```

Matches the contract-source `Depends on` line (`HMRC-001 v1.1, HATP-001 v1.0, HSCE-001 v1.1, RAE-001 v1.0, HBDC-001 v1.1`) exactly. Contract identity kept distinct from implementation/source digest per §12 requirement.

## 13. Producer Module / Admin Script Availability

Read-only import on Dell (`sudo -u pcae`, sanitized env, deployed venv):

```
import pcae.core.hatp_deployment_binding_admin as m
FILE: /opt/pcae/runtime/src/src/pcae/core/hatp_deployment_binding_admin.py
HAS_CREATE: True   (attribute presence only checked — create/rotate/revoke never invoked)
```

`__file__` correctly resolves under `/opt/pcae/runtime/src/src`. Source bytes match candidate (§9, included in the 30-file check).

`scripts/hatp_deployment_binding_admin.py` exists on the deployed tree; bytes match candidate (§9). Only `--help` was executed (no mutating subcommand `create|rotate|revoke` was ever invoked):

```
usage: hatp_deployment_binding_admin.py [-h] {create,rotate,revoke} ...
Protected-admin HBDC-001 v1.1 DeploymentBinding create/rotate/revoke ceremony.
Not reachable from the ordinary pcae CLI or any agent-executed code path...
```

## 14. Agent/Runtime Reachability

Local static grep of `src/pcae/cli.py`, `src/pcae/core/agent.py`, `src/pcae/commands/agent.py` for `hatp_deployment_binding_admin` returned **zero matches** — the producer remains unreachable from ordinary PCAE runtime/agent import paths at the candidate commit.

## 15. Venv / Wrapper State

- `.pth`: `/opt/pcae/runtime/venv/lib/python3.12/site-packages/_editable_impl_pcae_harness.pth` → `/opt/pcae/runtime/src/src` (matches expected base path).
- `direct_url.json`: `{"dir_info": {"editable": true}, "url": "file:///opt/pcae/runtime/src"}`.
- Interpreter: Python 3.12.3.
- `pcae_harness-0.2.0.dist-info` mtime unchanged since initial provisioning (no reinstall evidence).
- Wrapper `sha256sum /opt/pcae/runtime/bin/pcae-launch`: `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32` — **64 hex characters, a standard-length SHA-256 hex digest** (the spec's caveat about the expected string being "unusually long" was checked explicitly: `len() == 64`, not longer than a normal SHA-256). Actual computed value matches the expected value exactly, character for character.
- Wrapper owner/mode: `750 root:pcae`.

## 16. RepositoryIdentity / DeploymentBinding / Certification Absence

- `/opt/pcae/runtime/src/.pcae/repository-identity.json`: **absent**.
- `/etc/pcae/hatp/trust-store`: `750 root:pcae`, directory listing **empty** (no `registry.json`, no binding/certification files of any name found via recursive `find`).
- No `CertificationRecord`/`CertificationBinding`/active-certification state present anywhere under the Protected Root.

## 17. Protected Root Integrity

`/etc/pcae/hatp/trust-store`: owner `root:pcae`, mode `750`, empty. Unchanged in shape from the state 7N.4 was expected to leave it in (source-only redeployment never touches this path).

## 18. pcae Principal State

```
id pcae -> uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)   (no supplementary groups)
getent passwd pcae -> pcae:x:1004:1004:PCAE agent principal:/home/pcae:/usr/sbin/nologin
sudo -l -U pcae -> "User pcae is not allowed to run sudo on atila-Latitude-E5470."
```

No privilege drift.

## 19. HBDC Independent Diagnostic (Run Twice)

Exact read-only Action-9 command (recovered from the canonical proposition, §33, not from 7N.4's report), run twice independently:

**Run 1:**
```
NON_COMPLIANT
... (33 requirements True) ...
HBDC-REQ-042 False no_repository_identity_present
```

**Run 2:**
```
NON_COMPLIANT
['HBDC-REQ-042']
```

Identical result both times — deterministic. Sole failure: `HBDC-REQ-042` / `no_repository_identity_present`. All other checked requirements `True`.

## 20. Governing and Historical CHGR Integrity

```
pcae governance-record verify .pcae/publication-execution/records/chgr-71bd24f9d3d742d6baac772e480fc876.json -> outcome: verified
pcae governance-record verify .pcae/publication-execution/records/chgr-d4343fa51b9743f3abaeb87a881a78b1.json -> outcome: verified
pcae governance-record verify .pcae/publication-execution/records/chgr-96a0ce12756e4cc892492a87af1db832.json -> outcome: verified
pcae governance-record verify .pcae/publication-execution/records/chgr-541cb08c313b4f8884970172d37c5a1d.json -> outcome: verified
pcae governance-record verify .pcae/publication-execution/records/chgr-0e37ed1340b14311826722c4dbf3e856.json -> outcome: verified
```

`git status --short` against all five record paths: empty (byte-unchanged by this phase). Governing CHGR `lifecycle_state: published`, `selected_option_id: approve` — not marked consumed/executed by this phase (this phase does not use the canonical machinery that would do so).

## 21. Mutation Inventory Reconstruction

`sudo git -C /opt/pcae/runtime/src reflog show HEAD`:

```
b0840e96 HEAD@{0}: checkout: moving from 28bf137b... to b0840e96...
28bf137b HEAD@{1}: checkout: moving from 7a3fa971... to 28bf137b...
7a3fa971 HEAD@{2}: checkout: moving from main to 7a3fa971...
5b5d4a5f HEAD@{3}: clone: from github.com:atimad/pcae-harness.git
```

Only a single detached-checkout event moved the tree from the old source to the candidate — consistent with exactly: fetched candidate object, detached checkout to candidate, (ownership/mode normalization, not reflog-visible but independently confirmed via §6/§7's live state). No other host mutation is evident in the reflog.

## 22. Old Rollback Object Locality

```
sudo git -C /opt/pcae/runtime/src cat-file -t 28bf137b5dc95d024e8913b678dce0501a46fd0f -> commit
```

Present locally on Dell.

## 23. Source Credential Metadata (No Byte Read)

```
/root/.ssh/pcae_harness_deploy_ed25519      -rw------- root:root  432 bytes, mtime Aug 15 08:32
/root/.ssh/pcae_harness_deploy_ed25519.pub  -rw-r--r-- root:root  119 bytes, mtime Aug 15 08:32
```

Metadata only read; private key bytes were never read. mtimes predate the 7N.4 redeployment (mutation), consistent with no credential rotation during redeployment.

## 24. Unrelated Dell Scope / Project Root / Permission Broker

- `/opt/pcae/projects`: empty — no managed project repo was created there.
- No files outside `/opt/pcae/runtime/src` and `/opt/pcae/runtime/venv`/`bin` (already-known provisioning paths) show a newer mtime than initial Aug 15 provisioning.
- Permission Broker (`POL-005`/`COMP-002`, `src/pcae/core/permission_broker_foundation.py`): this file is one of the 30 byte-verified HMIC files (§9) — confirmed byte-identical to candidate, so no PB/POL-005/COMP-002 mutation occurred.
- `hac-windows` was never inspected, per instruction.

## 25. Runtime State

`pcae runtime inspect` (local, Mac canonical runtime): `Observed` / `observe` / `unavailable` — unchanged. No activation performed or authorized.

## 26. Carried Findings (Unchanged, Not Repaired This Phase)

- DeploymentBinding audit-failure-after-durable-mutation gap.
- Permissive timestamp parser.
- HMIC-REQ-103 revocation-validation gap.
- HMIC-REQ-063 executed-byte provenance limitation.

## 27. Regression / Local Test Evidence

- `tests/test_phase_149o_20l_7n_4_dell_current_source_redeployment_execution.py`: 32/32 passed (used only as a static baseline of already-persisted repo state — not trusted as an oracle for this phase's own live-Dell findings).
- A broader keyword-scoped sweep (`hmic`/`hbdc`/`class_b`/`deployment_binding`, `-m fast_green`) shows a pre-existing local macOS baseline with many failures unrelated to this phase (host-environment-sensitive tests written against the Linux/Dell production target, and one pre-existing collection error from a missing local `fido2` package). **This phase made zero production source changes**, so there are no net-new failures attributable to it; the pre-existing baseline is carried forward unchanged.

## 28. Final Classification

- **Source currency:** CURRENT VERIFIED SOURCE DEPLOYED.
- **Combined Boundary-P + source status:** BOUNDARY-P PHYSICAL PROVISIONING + CURRENT SOURCE DEPLOYMENT INDEPENDENTLY VERIFIED.
- **HMIC:** HMIC v1.4 IMPLEMENTATION/SOURCE IDENTITY INDEPENDENTLY VERIFIED DEPLOYED — NOT CERTIFIED.
- **HBDC:** NON_COMPLIANT, sole residual `HBDC-REQ-042` (`no_repository_identity_present`); not COMPLIANT.

## 29. Final Verdict

**INDEPENDENTLY VERIFIED — CURRENT SOURCE DEPLOYMENT COMPLETE.**

RepositoryIdentity absent. DeploymentBinding absent. Boundary C/A not authorized. HATP not ready. Runtime Observed/observe/unavailable.

## 30. Recommended Next Phase

**149O.20L.7O — RepositoryIdentity + DeploymentBinding First-Use Proposition Preparation** (per the two-transition model from Phase 7M), which should resolve the RepositoryIdentity random-generation/preview issue and be able to use the producer on the actual current Dell source for read-only preview/analysis only. This phase does **not** initiate or elect 7O — it is a recommendation only.
