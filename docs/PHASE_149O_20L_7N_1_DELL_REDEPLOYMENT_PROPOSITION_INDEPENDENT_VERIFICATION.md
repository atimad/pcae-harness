# Phase 149O.20L.7N.1 — Dell Current-Source Redeployment Proposition Independent Authority Verification

## 0. Status

**Verification-only.** No human election initiated. No APPROVE/DECLINE/AMEND presented. No CHGR published. No Dell access, no Dell mutation. No RepositoryIdentity created. No DeploymentBinding created. No producer create/rotate/revoke invocation. No HMIC certification. Boundary C, Boundary A, HATP activation, and Cutover Record all remain untouched and **NOT AUTHORIZED**.

**Phase-entry commit:** `25a0cd32f042ffd2cc412e19e9ed5b905674a6b6` (`Phase 149O.20L.7N: sync active task after phase-complete staging`). `origin/main == HEAD`, 0 commits ahead/behind, working tree clean at entry.

**Subject of this phase:** independently re-verify, from first principles and without treating 149O.20L.7N's own prose or companion test module as an oracle, the complete Dell current-source redeployment proposition materialized by Phase 149O.20L.7N (`docs/PHASE_149O_20L_7N_DELL_CURRENT_SOURCE_REDEPLOYMENT_PROPOSITION_AUTHORITY_PREPARATION.md`).

## 1. Entry Checks (read-only reconciliation)

```
git status --short                          -> (empty, clean)
git status --branch --short                  -> ## main...origin/main
git rev-list --count origin/main..HEAD       -> 0
pcae health                                   -> Overall status: healthy
pcae check                                    -> PCAE check passed
pcae status coherence                         -> Status: coherent
pcae doctor task-memory                       -> pre-existing DONE.md-listing warnings only (unrelated, long-standing)
pcae push check                               -> Health: healthy; Check: passed; Mode: nothing_to_push
pcae runtime inspect                          -> Runtime state: Observed; Execution capability: unavailable
pcae notify status                            -> Telegram configured, enabled, ready
pcae phase-report show --latest               -> 149O.20L.7N, status completed, pushed
pcae phase-report reconcile --phase-id 149O.20L.7N -> reconciled, mutation: none
```

All entry checks passed. No blocking condition found before verification work began.

## 2. Note on the 41-Hex-Character Caveat in the Task Brief (§1)

The 7N.1 task brief cautioned that the given hashes `28bf137b5dc95d024e8913b678dce0501a46fd0f` and `b0840e96a7ffb12308e95828aa5927c3e7c770c0` "are one character too long for real Git SHA-1/SHA-256 object ids" and instructed to try a 40-char prefix if the literal did not resolve.

**Independently measured (`wc -c` on each literal, `echo -n` to avoid a trailing newline):**

```
len("b0840e96a7ffb12308e95828aa5927c3e7c770c0") == 40
len("28bf137b5dc95d024e8913b678dce0501a46fd0f") == 40
```

**Both hashes are, in fact, exactly 40 hex characters — ordinary Git SHA-1 object ids — and both resolve directly via `git cat-file -t <sha>` to `commit` without any truncation.** The task brief's caveat is itself factually incorrect for this phase's specific input hashes (it may be defensive boilerplate intended for a different/hypothetical scenario). This is reported explicitly per the brief's own instruction to "treat this itself as a fact to verify/report on" rather than silently reconciling it. No truncation was applied anywhere in this verification.

## 3. Canonical Proposition Artifact (§4)

- **Canonical path:** `docs/PHASE_149O_20L_7N_DELL_CURRENT_SOURCE_REDEPLOYMENT_PROPOSITION_AUTHORITY_PREPARATION.md`
- **Containing commit:** `b0ba8b8189f87720718f9e8050750ec41842c7b8` (`Phase 149O.20L.7N: Dell Current-Source Redeployment Proposition + Authority Preparation`)
- **Proposition identifier:** none formally assigned yet — no `pcae decision-session`/`pcae governance-record` artifact exists for this transition (verified §10 below); the document's own §63/§64 explicitly state the future election tool must bind the exact `decision_subject`/`conditions` text and the candidate SHA (`b0840e96a7ffb12308e95828aa5927c3e7c770c0`), not this document's own commit hash, as the authoritative reference.
- **Immutability:** the document is a normal tracked Git blob under `docs/`; it is immutable at its authoring commit (any future edit would be a new commit/blob) but is not schema-frozen or checksum-pinned by any machinery today. This is a **gap**, discussed in §12 (Machine-Bound vs. Report-Only Evidence) below.
- **Companion test:** `tests/test_phase_149o_20l_7n_dell_current_source_redeployment_proposition_authority_preparation.py` (33 tests, all passing — re-confirmed this phase, §11).
- **Consumption by future election tooling:** none of `pcae decision-session create/select/confirm` or `pcae governance-record publish` currently reads this markdown document programmatically. A human/future phase must transcribe the exact SHA/command/condition text (§67 of the 7N document) into the election tool's own fields. This is disclosed explicitly by the 7N document itself (§64) and is **not** a defect introduced this phase, but it is a real authority-binding gap flagged for the next phase (see §13/verdict below).

## 4. True Proposition Baseline (§5)

| Item | Value |
|---|---|
| True 7N phase-entry commit | `b83d6623c0dea24bad699f52aa6861804a0f29dd` (independently confirmed from the 7N document's own §0 statement and cross-checked against `git log`) |
| Proposition creation commit | `b0ba8b8189f87720718f9e8050750ec41842c7b8` |
| Final 7N-line commits (finalization) | `065b3ec0`, `30071fc3`, `748a4d13`, `25a0cd32` |
| Current HEAD (7N.1 entry) | `25a0cd32f042ffd2cc412e19e9ed5b905674a6b6` |
| origin/main (7N.1 entry) | `25a0cd32f042ffd2cc412e19e9ed5b905674a6b6` (identical to HEAD) |

## 5. Candidate Object Authenticity (§6)

```
git cat-file -t b0840e96a7ffb12308e95828aa5927c3e7c770c0   -> commit
git rev-parse b0840e96a7ffb12308e95828aa5927c3e7c770c0      -> b0840e96a7ffb12308e95828aa5927c3e7c770c0 (exact round-trip, no abbreviation)
git merge-base --is-ancestor b0840e96a7... HEAD              -> exit 0 (ancestor)
git merge-base --is-ancestor b0840e96a7... origin/main       -> exit 0 (ancestor)
git cat-file -t 28bf137b5dc95d024e8913b678dce0501a46fd0f     -> commit
git merge-base --is-ancestor 28bf137b... b0840e96a7...        -> exit 0 (old is ancestor of candidate)
```

Full unabbreviated 40-hex SHA used throughout — no moving-ref substitution anywhere in this verification. **Independently confirmed: candidate is a genuine, ancestor-verified commit object.**

## 6. Candidate Currentness — Authority-Drift Check (§7)

At 7N.1 entry, HEAD is **13 commits** ahead of the candidate (7N's own document recorded 8, measured at 7N's own close before 7N's finalization commits landed — both counts are correct at their respective measurement times; the delta grew by 5 as 7N's own finalization sequence (§0.20L.7N task-close, metadata sync, report sync) added commits after 7N's internal §62 recheck).

```
git diff --stat b0840e96a7ffb12308e95828aa5927c3e7c770c0 HEAD -- src/pcae scripts docs/contracts schemas pyproject.toml
    -> (empty — zero changes)
```

**Full name-status of all 13 intervening commits' changed files:**

```
M  .pcae/phase-completion-metadata.json
M  .pcae/phase-completion-report.md
M  CHANGELOG.md
M  PROJECT_STATUS.md
A  docs/PHASE_149O_20L_7M_DELL_REDEPLOYMENT_DEPLOYMENTBINDING_FIRST_USE_SEQUENCING_ARCHITECTURE.md
A  docs/PHASE_149O_20L_7N_DELL_CURRENT_SOURCE_REDEPLOYMENT_PROPOSITION_AUTHORITY_PREPARATION.md
M  tasks/DONE.md
A  tasks/active/20260817-1358-...-post-149o-20l-7m.md
A  tasks/active/20260817-1815-...-post-149o-20l-7n.md
A  tasks/done/20260817-1343-phase-149o-20l-7m-....md
A  tasks/done/20260817-1728-phase-149o-20l-7n-....md
A  tests/test_phase_149o_20l_7m_....py
A  tests/test_phase_149o_20l_7n_....py
```

Every one of the 13 files is governance bookkeeping (`.pcae/phase-completion-*`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`), the 7M/7N architecture docs themselves, or their companion test files. **None touch `src/pcae/**`, `scripts/**`, `docs/contracts/**`, `schemas/**`, or `pyproject.toml`.**

**Independently reconfirmed: no authority-bearing drift. Candidate remains current. CANDIDATE NOT STALE.**

## 7. Candidate Contracts (§8) — read directly from candidate blobs

```
git show b0840e96a7...:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md | grep '**Version:**'
    -> **Version:** 1.1
git show b0840e96a7...:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md | grep '**Version:**'
    -> **Version:** 1.4
git show b0840e96a7...:docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md | grep '**Version:**'
    -> **Version:** 1.1
```

**HBDC-001 = 1.1, HMIC-001 = 1.4, HMRC-001 = 1.1 — exact match to proposition claims, read from candidate blobs, not inherited from prose.**

## 8. Candidate Contract-Version Derivation (§9) / HMIC Digest (§10) / Frozen Membership (§11)

Run against a **fresh, disposable, detached `git worktree`** at the exact candidate SHA (`git worktree add --detach <scratch> b0840e96a7...`), invoking the canonical production function directly — not copying the constant from 7N's prose:

```python
from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest
from pcae.core.paths import HarnessPath
from pathlib import Path
derive_implementation_scope_digest(HarnessPath(Path('.').resolve()))
```

**Result:** `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` — **64 hex characters, a well-formed SHA-256 hex digest** (the algorithm's real output length; no length anomaly, contrary to the brief's precautionary flag). **Exact match to the expected value.**

**Frozen set:** `len(_FROZEN_AUTHORITY_BEARING_FILES) == 30`, independently enumerated in the same disposable worktree — 23 `src/pcae/`-relative + 7 repository-root-relative, byte-identical member list to the proposition's §4/§6. Both DeploymentBinding producer surfaces (`core/hatp_deployment_binding_admin.py`, `scripts/hatp_deployment_binding_admin.py`) independently confirmed present.

## 9. Frozen-Path Health (§12)

For all 30 candidate members, independently verified in the disposable worktree: path exists (tried both `src/pcae/`-relative and repo-root-relative resolution per member type); repository-relative; normalized (`os.path.normpath`); regular file (`Path.is_file()`); not a symlink (`Path.is_symlink()` false); no duplicate normalized path across the 30. **Result: zero issues, all 30 healthy.**

## 10. Candidate Tree Inventory (§13)

Freshly enumerated directly against `git ls-tree -r b0840e96a7... ` (no reliance on the candidate worktree's on-disk state, which could theoretically diverge from the tree object; the tree object itself was read):

```
git ls-tree -r b0840e96a7... --name-only | wc -l                 -> 4200
git ls-tree -r b0840e96a7...  | awk '{print $1}' | sort | uniq -c -> 4186 100644 / 14 100755
git ls-tree -r b0840e96a7...  | awk '$1=="120000"'                -> (none)
git ls-tree -r b0840e96a7...  | awk '$1=="160000"'                -> (none)
git ls-tree -r b0840e96a7...  | awk '$1!="100644" && $1!="100755"' -> (empty)
```

**Independently reproduced exactly: 4200 total, 4186×100644, 14×100755, 0 symlinks, 0 submodules, 0 other modes.** Exact match to proposition claims.

## 11. Mode-Map Compatibility (§14) / Mode-Mapping Rehearsal (§84)

Applied the proposition's exact literal mode-normalization commands (§19 of the 7N document) against the disposable candidate worktree:

```
find . -type d -exec chmod 0750 {} \;
find . -type f -perm -u+x -exec chmod 0750 {} \;
find . -type f ! -perm -u+x -exec chmod 0640 {} \;
```

Followed by an **independent Python `os.lstat` cross-check against all 4200 tracked paths** (not reusing the proposition's own read-back script, only its documented method):

```
total 4200, ok640 4186, ok750 14, other 0, mismatches 0
```

**All 4200 paths map correctly. Zero mismatches. No blanket chmod strips executable bits** — the `find -perm -u+x` branch correctly preserves the 14 files Git already marked executable.

## 12. Exact Old→Candidate Diff (§15) / Changed-File Classification (§16)

```
git diff --stat 28bf137b... b0840e96a7... -- src scripts docs/contracts pyproject.toml
```

```
 docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md                              |   64 +-
 docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md| 1364 +++++++++++++++++++-
 scripts/hatp_deployment_binding_admin.py                                        |  245 ++
 src/pcae/core/hatp_deployment_binding_admin.py                                  |  953 ++++++++++++++
 src/pcae/core/hatp_mandatory_certification.py                                   |   46 +-
 5 files changed, 2598 insertions(+), 74 deletions(-)
```

**Exactly five files — matches proposition's claimed count exactly, independently reconfirmed.** No sixth authority-relevant file omitted (checked across the same `src scripts docs/contracts schemas pyproject.toml` surface used for the currentness check, §6 above — `schemas/` diff is empty between old and candidate).

**Blob and SHA-256 identities, independently recomputed (`git rev-parse <sha>:<path>`, `git show <sha>:<path> | shasum -a 256`):**

| # | File | Classification | Candidate Git blob | Candidate SHA-256 |
|---|---|---|---|---|
| 1 | `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` | Contract (HBDC-001 v1.0→v1.1) | `ccc4efba78b39633b63f25e1415b915598a49772` | `f9a82b53abe74f73de2158adc8063785ab1a96460ef4bac9a1c48e96cee3d370` |
| 2 | `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` | Contract (HMIC-001 v1.1→v1.4) | `1c6ad765533b36262319005a9f1517b0182c8b7a` | `6fe5fed66617218f74ffc252a76738bdf067f1b8bb4532430931789a091382f8` |
| 3 | `scripts/hatp_deployment_binding_admin.py` | Producer (new admin script) | `286db838d573ef9311a6d0df78a6842b5f4ef296` | `fe7869362431d74a46a64b8db825311914c7b4c34d46ad72ee09fd4df3dcfcdb` |
| 4 | `src/pcae/core/hatp_deployment_binding_admin.py` | Producer / new frozen-set member | `c7950f302ba5714764de5fa0fd86699a07cfad1c` | `582785eb3468a506aeaa3ff00cb906181a1e649ff83afcb9a05916465999f02e` |
| 5 | `src/pcae/core/hatp_mandatory_certification.py` | HMIC membership implementation | `1b965cc53f2ad2ef6c3814d64129a4b748179f9f` | `6894f8de03cf35abd5e006b23fe6798f1234c6cafc718c7db17f05a22a7749b3` |

**All five blob SHAs and SHA-256 hashes independently recomputed and byte-identical to the proposition's table.** Redeployment requires each: two are the amended HMIC-001/HBDC-001 contracts the candidate implements; two are the new DeploymentBinding producer surfaces (frozen-set additions); one is `hatp_mandatory_certification.py` itself, updated to include the new frozen-set constant and digest derivation. All five are authority-bearing.

## 13. Packaging Comparison (§17)

```
git diff --stat 28bf137b... b0840e96a7... -- pyproject.toml   -> (empty)
```

**Independently confirmed: `pyproject.toml` byte-unchanged.** Sole runtime dependency (`jsonschema>=4.18,<5`) and console-script entry point (`pcae = "pcae.cli:main"`) unchanged. **No packaging drift. The "venv RETAIN UNCHANGED" decision is consistent with the actual diff — proposition complete on this axis.**

## 14. Editable-Install Model (§18)

Not independently re-verified this phase against live Dell (no Dell access performed — consistent with 7N.1's own scope and the 7N document's own disclosure that it is cited, not re-measured, evidence). The proposition's reasoning — that both `.pth` and `direct_url.json` bind resolution to the *directory* `/opt/pcae/runtime/src`, not to specific bytes, so an in-place `checkout --detach` swap is consumed automatically by the existing editable install without reinstall — is internally consistent with standard Python editable-install (`pip install -e`) semantics and is not contradicted by any local evidence. **This item's freshness depends on live Dell re-measurement immediately before mutation (§14 below), which correctly remains a future execution phase's responsibility, not this phase's or 7N's.**

## 15. Venv Mutation Prohibition (§19)

Searched the entire proposition document's literal command blocks for `pip install`, `pip uninstall`, venv recreation, dependency update, or site-package mutation commands:

```
grep -niE "pip install|pip uninstall|venv create|python3 -m venv|rm -rf .*venv" <doc>
```

**Zero matches as literal commands.** The only occurrences of "pip install" in the document are in prohibition prose (§10: "no `pip install -e` re-run..."; explicit prohibition list). **No contradiction found between the "retain unchanged" claim and any literalized command.**

## 16. Wrapper Retention (§20)

Expected wrapper digest, as stated in the proposition: `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`.

**Independently measured hex length:** 64 characters — a well-formed SHA-256 hex digest, no anomaly. This value is cited evidence from prior live-Dell phases (149O.20L.7B through 7D.9), not re-measured against live Dell this phase (no Dell access performed). Searched the proposition document's literal command blocks for any wrapper write/mutation (`pcae-launch` appears only in read-back `sha256sum` verification commands, §11/§30 of the 7N doc) — **zero wrapper-mutating commands found.**

## 17. Entering Dell Baseline (§21) / Baseline Freshness Policy (§22)

The 7N document's §12 baseline table (machine identity, `pcae` principal, Protected Root, Retained Actions 1–5, source credential metadata, old source SHA, tree/mode inventory, venv state, wrapper state, absent RepositoryIdentity/DeploymentBinding, runtime state) is cited from prior independently-verified live-Dell evidence (149O.20L.7A/7D.1/7D.9/7D.11/7E) and is **not re-measured this phase** — no live Dell access was performed, consistent with the task brief's "No live Dell access is necessary unless local evidence is inadequate." Local evidence (Git history, contract text, source tree) was adequate to complete this phase's scope without touching Dell.

**Baseline freshness policy independently endorsed:** using previously-verified Dell state as a *proposition precondition* is appropriate for proposition-readiness purposes, provided (as the 7N document's own §13 correctly requires) a future execution phase re-reads live state immediately before any mutation and STOPs on any mismatch. 7N.1 does not need to, and did not, assume the Dell baseline remains unchanged today — it only verifies the proposition's own internal consistency and command correctness.

## 18. Source Credential Assumptions (§23)

Verified the proposition references only credential *metadata* (path `/root/.ssh/pcae_harness_deploy_ed25519`, ownership, mode, GitHub deploy-key fingerprint) — no private key material appears anywhere in the document (confirmed by a full-text scan for PEM/private-key markers: none found). No credential rotation or reprovisioning is proposed in scope.

## 19. Literal Preflight Commands (§24) / First Mutating Command (§25)

Classified every command block in the proposition document:

- **Read-only preflight:** §13 (baseline re-check), §16 (`git cat-file -t <candidate>` object-type check).
- **Forward mutation begins at §17:** `git checkout --detach b0840e96a7...` — the first command that alters the Dell working tree/`HEAD`. (`git fetch` in §15 only adds objects to the local object store; it does not touch the working tree or `HEAD` — see §21 below on fetch mutability classification.)
- **Ownership (§18) and mode normalization (§19)** are further forward-mutation steps, correctly sequenced after checkout.

No command labeled preflight performs a write. **Clear, unambiguous preflight/mutation boundary — independently confirmed at exactly the same point (`checkout --detach`) the proposition itself identifies (§58/§63 of the 7N doc).**

## 20. Fetch Semantics (§26) / Fetch Mutability Classification (§27)

```
sudo git -C /opt/pcae/runtime/src fetch origin b0840e96a7ffb12308e95828aa5927c3e7c770c0
```

Exact commit object targeted, no branch name, no `git pull` anywhere in the document (confirmed by text scan — the only "pull" mentions are explicit prohibition prose). **The 7N document itself (§58) already correctly classifies `fetch` as adding-objects-only, distinct from the working-tree mutation; it does not mischaracterize `fetch` as pure read-only preflight — it is placed under "Forward mutation" in the document's own §57 command-classification table**, which is the fact-correct classification (fetch does mutate the local object/ref database even though it doesn't touch the working tree). No correction needed here.

## 21. Object Verification (§28) / Exact Checkout (§29)

```
sudo git -C /opt/pcae/runtime/src cat-file -t b0840e96a7ffb12308e95828aa5927c3e7c770c0   -> must equal: commit
sudo git -C /opt/pcae/runtime/src checkout --detach b0840e96a7ffb12308e95828aa5927c3e7c770c0
```

Object-type check correctly sequenced after fetch, before checkout. Checkout targets the full, unabbreviated candidate SHA — **no branch used anywhere in the checkout command.**

## 22. Ownership Commands (§30) / Mode-Normalization Commands (§31)

```
sudo chown -R root:pcae /opt/pcae/runtime/src
```

Scoped exactly to `/opt/pcae/runtime/src` — text-scanned for any broader `/opt/pcae` or system-wide chown: **none found.**

**Adversarial review of the mode-normalization commands (§31 — filenames with spaces/tabs/newlines, executable non-obvious files, hidden files):**

```
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \;
```

These use `find ... -exec ... {} \;`, which passes each matched path directly to `chmod` as a single argument with **no shell word-splitting** — safe against filenames containing spaces, tabs, or any other whitespace. **This is not the unsafe `for x in $(...)` pattern** the checklist explicitly warns against; no instance of that pattern was found anywhere in the document (confirmed by text scan). Executable classification derives from Git's own on-disk executable bit as `git checkout` already set it from the index — not filename pattern-matching. **Independently rehearsed against the actual candidate tree (§11 above): confirmed zero tracked paths contain spaces or tabs in this specific candidate tree** (`git ls-tree -r <candidate> --name-only | grep -cE ' |\t'` → 0), so the attack surface, while structurally handled safely by the command construction, is not even currently populated. **No defect found.**

## 23. Full Read-Back Commands (§32) / Full Tracked-Content Comparison (§33)

The proposition's §20 (7N doc) specifies: `rev-parse HEAD` exact match; `symbolic-ref -q HEAD` non-zero (detached); `status --short --untracked-files=all` empty; `remote get-url origin` exact match; `ls-files | wc -l` = 4200; `ls-tree` mode histogram; an independent `os.lstat` cross-check against **all** 4200 paths; and `git diff <candidate> -- . | wc -l` = 0 (full tracked-byte comparison, not `git status` alone). **This is a robust, non-`git-status`-only method of proving tracked-byte identity** — satisfies the checklist's requirement not to rely only on `git status`. `--untracked-files=all` (not the default) is correctly specified, which is the form that surfaces untracked files inside untracked directories too — appropriate given RepositoryIdentity must remain absent and no `.pcae/repository-identity.json` should silently appear as an untracked file.

## 24. Thirty-File Live Identity Read-Back (§34)

§22 of the 7N document explicitly loops over **all 30** frozen-set canonical paths (not a sample), diffing each against the candidate commit and requiring `wc -l` = 0 for every one. **No sampling — full coverage confirmed by inspection of the command's own text** ("Future execution must compare deployed bytes for all 30 HMIC authority-bearing files").

## 25. HMIC Digest Command (§35) / Contract-Version Command (§36)

```
sudo -u pcae sh -c "cd /opt/pcae/runtime/src && env -i HOME=/home/pcae PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1 /opt/pcae/runtime/venv/bin/python3 -c '...'"
```

Runs under `env -i` (fully reset environment) with an explicit `PATH` that places the deployed venv's interpreter first and `PYTHONNOUSERSITE=1` (disables user-site imports) — this correctly prevents accidental import of any Mac/other-checkout `pcae` package via `PYTHONPATH` leakage or user-site packages. `cd /opt/pcae/runtime/src` before invocation ensures the deployed candidate tree, not any other path, is what Python's `sys.path`/relative-import resolution sees first. The contract-version command (§24 of the 7N doc) equivalently instructs reading from the **deployed** candidate tree, not this document. **No accidental-import risk identified in the literalized command.**

## 26. Producer Import Check (§37) / Admin-Script Check (§38)

§25 of the 7N doc imports `pcae.core.hatp_deployment_binding_admin` and asserts `m.__file__` resolves under `/opt/pcae/runtime/src/src/pcae/core/hatp_deployment_binding_admin.py` — **import only, no function invocation** (confirmed by reading the command literally: a single `import` + `print(m.__file__)`, no call expression). §26 checks the admin script's existence and byte-match via `git diff ... | wc -l` — **no `create`/`rotate`/`revoke` subcommand invocation anywhere.** Both independently confirmed safe.

## 27. Agent-Reachability Check (§39)

§27 of the 7N doc includes a read-only regression check (`sudo -u pcae env -i ... which pcae`) re-verifying the producer's non-agent-reachable posture, reusing the diagnostic already established at 7D.9/7D.11. **Present and sufficient — not omitted.** Classification: desirable-and-included, not merely "would be nice."

## 28. Venv Read-Back (§40) / Wrapper Read-Back (§41)

§29 (venv) requires re-reading `.pth`, `direct_url.json`, distribution identity, interpreter path, and permissions, expecting byte/state unchanged. §30 (wrapper) requires an exact `sha256sum` comparison against `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`. Both literalized as exact commands with exact expected values — **no vague "verify unchanged" without a concrete check.**

## 29. Optional HBDC Diagnostic (§42) / Expected Result (§43) / Failure Policy (§44) / Unexpected COMPLIANT (§45)

§33 of the 7N doc includes the exact Action-9 read-only diagnostic (`verify_class_b_deployment_conformance()`), recovered verbatim from 7D.9/7D.11. **Expected result stated explicitly:** `NON_COMPLIANT` with exactly one failing requirement, `HBDC-REQ-042` (`no_repository_identity_present`).

**This phase attempted a local, explicitly non-authoritative simulation** of this diagnostic against the disposable candidate worktree on this Mac. The result was `NON_COMPLIANT` with **many** failing requirements beyond just `HBDC-REQ-042` (protected-root-absent, venv-not-provisioned, ownership-model-mismatch checks, etc.) — because this Mac's disposable worktree lacks Dell's actual provisioned environment (no `/etc/pcae/hatp/trust-store` Protected Root, no dedicated `pcae` principal/venv/ownership model). **This local result is not evidence the proposition's expected-Dell-result claim is wrong** — it demonstrates only that the diagnostic function executes and correctly discriminates conditions; the specific *set* of failing requirements is a direct function of the host's actual provisioned state, which only Dell (not any local Mac worktree) replicates. The proposition's `NON_COMPLIANT {HBDC-REQ-042}`-only claim for Dell rests on Dell's Actions 1–8 provisioning (Protected Root, principal, venv, ownership) already being in place there per the cited 7D.9/7D.11 evidence — consistent with, but not independently re-confirmable without, live Dell access. **This is disclosed as a genuine limitation of this phase's verification, not resolved by local simulation, and correctly deferred to live re-measurement at execution time** (§44's failure policy: any other failure set → STOP, no auto-repair, disclose to operator; §45: unexpected `COMPLIANT` → STOP/investigate, never treated as success). Both policies are present and adversarially sound as written.

## 30. Source-Transition Success Condition (§46)

Confirmed the proposition's own §38/§46 explicitly define success as candidate-source-exact + venv/wrapper-retained + expected-residual-explained — **not** contingent on HBDC `COMPLIANT`. Correct per the two-transition (Model A/C) architecture.

## 31. Rollback Target Authenticity (§47) / Locality Precondition (§48) / Network-Independence (§49) / Content Verification (§50–51)

```
git cat-file -t 28bf137b5dc95d024e8913b678dce0501a46fd0f   -> commit
```

**Independently confirmed a valid commit object** (§5 above). The 7N document's §34 correctly derives local-object presence on Dell from Git's structural HEAD-reachability guarantee (the old SHA is the checkout's current `HEAD` at the moment forward mutation begins, and Git never GCs the current `HEAD` of a checkout) rather than from an assumption dependent on a recent fetch.

**Independent local rehearsal performed** (disposable clone, not the working repository):

```
git clone <repo> rehearsal-clone
cd rehearsal-clone && git checkout --detach 28bf137b...     # old
git checkout --detach b0840e96a7...                          # candidate ("forward")
git remote remove origin                                     # sever network entirely
git checkout --detach 28bf137b...                             # rollback
```

**Result: rollback succeeded with `HEAD` exactly `28bf137b...`, `status --short --untracked-files=all` empty, and zero network access after `git remote remove origin`.** This concretely rehearses (not merely asserts) the network-independence claim of §35/§49. The proposition's §35 rollback commands additionally restore old filesystem-mode mapping (`chown` + the three `find`-based `chmod` passes) — the rehearsal above confirms only the Git-object layer; filesystem-mode restoration is the same already-adversarially-reviewed command construction as §22 above, applied symmetrically.

## 32. Rollback Trigger Matrix (§52)

The 7N document's §36 table was independently reconstructed by re-reading the raw command/read-back sections (§20–§30, §33) rather than trusting the table's own prose:

| Trigger | Before/after source mutation | Rollback? (independently confirmed) |
|---|---|---|
| Fetch/object failure (§16, before checkout) | before | STOP only, no rollback needed (nothing mutated yet) |
| Checkout failure (§17) | at mutation boundary | Yes |
| Ownership failure (§18) | after | Yes |
| Mode failure (§19/§21) | after | Yes |
| Clean-tree mismatch (§20) | after | Yes |
| Content mismatch (§20/§22) | after | Yes |
| HMIC digest mismatch (§23) | after | Yes |
| Producer/import failure (§25/§27) | after | Yes |
| Venv mismatch (§29) | after | Yes |
| Wrapper mismatch (§30) | after | Yes |
| Unexpected HBDC result (§33, any set other than exactly `{HBDC-REQ-042}`, or unexpected `COMPLIANT`) | after | Yes — STOP and diagnose (rollback if diagnosis cannot resolve without deviating from the proposition) |
| Expected `NON_COMPLIANT {HBDC-REQ-042}` | after | **No** — expected residual |

No ambiguous branch found. **Matches the proposition's own table exactly on independent reconstruction.**

## 33. Fetch-Only Failure (§53) / Post-Success Fetched Objects (§54) / No-Ops 55–57

- **§53:** if fetch mutates the object database but checkout never begins, the proposition does not invent an unnecessary rollback for this case — correctly treated as benign, no cleanup required (fetched-but-unused objects are ordinary Git garbage, harmless).
- **§54:** candidate and historical objects coexisting after success is not source-state ambiguity, since `HEAD`/read-back are exact — correctly documented, not treated as a problem.
- **§55–57:** independently confirmed no rollback command touches the SSH deploy credential, requires venv reinstall, or touches the wrapper — the rollback command block (§35 of the 7N doc) contains exactly: `checkout --detach`, `chown`, three `chmod` `find` passes, and read-back checks. No credential, `pip`, or wrapper-path command appears.

## 34. RepositoryIdentity / DeploymentBinding / Trust-Store / Certification / Activation / Permission Broker Exclusions (§58–63)

Full-text scan of the proposition document for each prohibited pattern:

| Search term | Occurrences found |
|---|---|
| `pcae init` | 0 as a command; 1 as explicit prohibition prose (§31 of 7N doc) |
| `ensure_repository_identity` | 0 |
| `.pcae/repository-identity.json` write | 0 (only referenced as "must remain absent") |
| DeploymentBinding create/rotate/revoke as literal commands | 0 (only prohibition prose and admin-script byte-match/import-only checks) |
| Trust-store writes (other than read-only inspection) | 0 |
| Certification admin invocation | 0 |
| `HATP_MANDATORY` write / Cutover Record | 0 |
| Permission Broker / POL-005 / COMP-002 mutation | 0 |

**Zero occurrences of any prohibited action anywhere in the proposition's literalized command set.** All are either absent entirely or referenced only in explicit prohibition prose.

## 35. Historical CHGR Inventory (§64) — independently enumerated, not assumed

```
find .pcae/publication-execution/records -iname 'chgr-*.json'
```

**Exactly four `chgr-*` records found** (distinct from the `chgrprov-*`/`chgrconf-*`/`chgrintg-*` provisional/confirmation/integrity records also present in the same directory, which are not final CHGRs): `chgr-0e37ed1340b14311826722c4dbf3e856`, `chgr-96a0ce12756e4cc892492a87af1db832`, `chgr-d4343fa51b9743f3abaeb87a881a78b1`, `chgr-541cb08c313b4f8884970172d37c5a1d` — **matches the proposition's four known records exactly; no additional CHGR found.**

## 36. Historical CHGR Inapplicability (§65)

For each of the four records, the record's own persisted JSON was read directly (`decision_subject` field) and searched for the candidate SHA `b0840e96a7ffb12308e95828aa5927c3e7c770c0`:

| CHGR | `decision_subject` (first 120 chars) | Candidate SHA present? |
|---|---|---|
| `chgr-0e37ed1340b14311826722c4dbf3e856` | "Phase 149O.20L.7D.9: repaired-source Dell redeployment (candidate SHA `28bf137b...`) + Action-9 invocation PATH amendment..." | **No** — names only the *old* SHA as its own candidate, not `b0840e96a7...` |
| `chgr-96a0ce12756e4cc892492a87af1db832` | "Boundary-P provisioning authorization for Class-B target Dell..." | No |
| `chgr-d4343fa51b9743f3abaeb87a881a78b1` | "Boundary-P provisioning authorization for Class-B target Option B (Atilas-MacBook-Pro.local)..." | No |
| `chgr-541cb08c313b4f8884970172d37c5a1d` | "Amended continuation authorization for Dell Class-B Boundary-P provisioning...repairs Action 6 file-mode defect..." | No |

**Independently confirmed by each record's own persisted text: none authorizes the `28bf137b...`→`b0840e96a7...` transition.** No fallback exists.

## 37. D3-3 Status (§66)

Carried exactly as stated: **CLOSED FOR CURRENT CONTINUATION / MACHINE-READABLE SUPERSESSION HARDENING GAP RETAINED.** No `predecessor_record_id`/`successor_record_id` linkage exists between any of the four historical CHGRs and a future fresh CHGR (independently confirmed: `pcae governance-record publish --help` shows no supersession-linkage flag). No supersession is claimed by this phase either.

## 38. Decision Subject (§67)

**Discrepancy found and reported (see verdict, §41 below):** the 7N document's §42 claims the draft `decision_subject` text is "218 characters." **Independently recomputed by extracting the exact quoted string from the document and calling `len()` on it: the true length is 232 characters, not 218.** Both figures are well within the CHGR-001 schema's actual `decision_subject.maxLength`, independently confirmed by reading `src/pcae/schema_resources/chgr/records/human_governance_record.schema.json` directly: `"maxLength": 500`. **The 218-vs-232 discrepancy does not change the pass/fail outcome against the real 500-character limit and does not affect human understanding of scope — it is a self-reported arithmetic error in the proposition document, not a structural defect.** Subject text itself: concise, identifies Dell source redeployment, names both old and candidate SHA unambiguously, contains no first-use authorization language (independently text-scanned).

## 39. Decision Rationale (§68) / Proposition Conditions (§69) / Proposition Exclusions (§70)

Adversarially re-read §43 (rationale) — cites §1/§2/§3/§4/§5 exact facts, not "update Dell to latest" or any vague language. All 12 numbered conditions in §44 are objective, measurable, tied to the exact host/SHA pair, and fail-closed (each specifies an exact STOP behavior). §45's exclusion list explicitly names RepositoryIdentity, DeploymentBinding, first-use election, Boundary C, HMIC certification, Boundary A, Cutover Record, `HATP_MANDATORY` activation, Permission Broker/POL-005/COMP-002, repository onboarding, `hac-windows` — **a human does not need to infer any of these; all are explicit.**

## 40. Preview Fidelity (§71) / Machine-Bound vs. Report-Only Evidence (§72) / Proposition Digest/Binding (§73–74)

The proposition's §46 preview text was read in full and independently checked against §1–§45's own material facts: exact source transition, exact mutation path (`/opt/pcae/runtime/src` only), exact candidate tree inventory, exact venv/wrapper decisions, exact rollback target, exact exclusions — **all present in the preview text itself, not only in surrounding phase-report prose.** No material fact was found present only in the phase-report/CHANGELOG narrative but absent from the election-bound §46 preview.

**Genuine gap (not a blocker, but material to the authority-binding verdict):** as noted in §3 above, **no tooling today reads this markdown document programmatically to bind it into a decision session or CHGR.** `pcae decision-session create`/`pcae governance-record publish` take free-text arguments a human/future-phase operator must transcribe; there is no hash/digest of this document's content stored anywhere that a future election could check for staleness or tampering (no "proposition commit SHA" field bound into any schema). §63/§64 of the 7N document correctly *recommend* binding to the candidate source SHA rather than the document's own commit SHA — which is the right mitigation — but nothing enforces that the exact §46 preview text (as opposed to a paraphrase) is what a human actually sees at election time. **This is an authority-binding gap in the surrounding tooling, not a defect in the proposition's own content.**

## 41. Proof of No Election / No CHGR / No Dell Mutation / No First-Use Artifact (§75–78)

```
find .pcae/decision-sessions -name '*.json' | xargs grep -l b0840e96a7ffb12308e95828aa5927c3e7c770c0   -> (zero matches, 12 sessions checked, none reference the candidate SHA)
ls .pcae/publication-execution/published/                                                                -> only prp-*.json (publication-readiness-package previews), no chgr-*.json
find . -iname '*repository-identity.json*'                                                                -> none
find . -iname '*deploymentbinding*' -path '*records*'                                                     -> none (only source files scripts/hatp_deployment_binding_admin.py, src/pcae/core/hatp_deployment_binding_admin.py — code, not a created binding record)
```

**No election state, no CHGR, no RepositoryIdentity, no DeploymentBinding, no certification record exists for this transition.** This phase performed **zero** SSH/network access to any Dell host — confirmed by this phase's own command log (no `ssh`, `scp`, or Dell-hostname-targeted command was ever invoked in this verification; every command above targeted only this Mac's local Git object store and disposable local clones/worktrees).

## 42. Runtime State (§79)

```
pcae runtime inspect
    -> Runtime status: not_implemented
    -> Runtime state:  Observed
    -> Execution capability: unavailable
    -> Maximum plugin capability: observe
```

**Reconfirmed unchanged: Observed / observe / unavailable.**

## 43. Regression Baseline (§80)

This phase's own working tree was clean at entry and remained free of any production-code (`src/pcae/**`) modification throughout — only a new doc (this file) and a new independent test file were added. Because no production code changed, the "before" and "after" states are identical for regression purposes; no `git stash -u` A/B comparison was needed.

**Targeted regression run** (authority-relevant surfaces: HMIC certification, Class-B conformance/topology, DeploymentBinding, governance-record, decision-session, repository-identity):

```
pytest -k "hatp_mandatory_certification or hatp_class_b or hatp_deployment_binding or governance_record or decision_session or repository_identity" --ignore=tests/test_phase_149o_7_hatp_class_b_activation_independent_verification.py
    -> 749 passed, 33 failed, 2 skipped
```

The 33 failures are all instances of a **pre-existing, known pattern**: older companion test modules (from phases 149O.20I, 149O.20K.2/.3, 149O.20L.3/.20L.4) that pin an expected byte-identity check against *their own phase-entry commit* rather than live HEAD — as HEAD has advanced through many subsequent phases, those pinned expectations naturally drift and fail, independent of any change this phase made. This is the exact same failure-mode class the finalization gotchas for this repository document elsewhere ("pin companion test candidate-SHA checks to the frozen phase-entry commit instead of live HEAD"). **None of the 33 failing tests belong to this phase's allowed-file scope, and none were caused by any edit this phase performed (this phase changed zero production files).** One additional test module (`test_phase_149o_7_hatp_class_b_activation_independent_verification.py`) fails to *collect* entirely due to a pre-existing missing optional dependency (`fido2` not installed in this environment) — also unrelated and pre-existing.

**This phase's own new test file, run in isolation (the authoritative `fast_green` signal for this phase's own deliverable):**

```
pytest tests/test_phase_149o_20l_7n_1_dell_redeployment_proposition_independent_verification.py
    -> 51 passed
```

7N's own companion test, re-run to confirm it still passes unmodified:

```
pytest tests/test_phase_149o_20l_7n_dell_current_source_redeployment_proposition_authority_preparation.py
    -> 33 passed
```

## 44. Independent Proposition Tests (§81)

**New file:** `tests/test_phase_149o_20l_7n_1_dell_redeployment_proposition_independent_verification.py` — **51 tests, all passing.** Does **not** import 7N's companion test module anywhere (verified by inspection — no `from tests.test_phase_149o_20l_7n_...` or equivalent import exists in the new file); every fixture (candidate/old SHA, expected digest, expected changed-file blob hashes, historical CHGR ids) is independently re-typed from the source-of-truth Git objects/schema files, not copied via import. Coverage includes, per the required checklist: candidate SHA authenticity/hex-length/currentness; recomputed digest and 30-member set against a **disposable worktree** (not the live checkout); exact five-file diff and blob hashes; exact tree-inventory histogram; command literalization (fetch-exact-SHA, no `git pull`, detached checkout, no `for x in $(...)` word-splitting, no bare `pip install` command, scoped `chown`); a genuine network-severed rollback rehearsal in a disposable clone; a full 4200-path mode-mapping rehearsal; absence of RepositoryIdentity/DeploymentBinding/election/CHGR state; proposition decision-subject length and schema-limit cross-check; runtime-state reconfirmation.

## 45. Command Dry Analysis (§82) / Rollback Rehearsal (§83) / Mode Rehearsal (§84)

No Dell command was executed. All literalized commands were locally parsed and reviewed for shell syntax, quoting, ordering, and path safety (§19–§31 above). A local, explicitly non-authoritative simulation of the source-transition (checkout swap) and rollback was rehearsed in a disposable clone (§31 above — succeeded, network-severed). The exact mode-mapping logic was rehearsed against all 4200 candidate paths in a disposable worktree (§11 above — zero mismatches). None of this simulation is claimed to be equivalent to a live Dell run; it verifies only Git/filesystem-semantics correctness of the bound commands themselves, as instructed.

## 46. Literal-Command and Factual-Proposition Defects (§85–86)

**Literal-command review:** no unsafe, incomplete, or wrong command was found. The mode-normalization `find -exec` pattern is safe against whitespace-containing filenames (§22 above). No `git pull`, no branch-based checkout, no unscoped `chown`, no bare `pip install`/venv-mutating command anywhere in the literalized set.

**Factual-proposition review:** SHA, digest, frozen-set count, tree inventory, five-file diff, and all five changed-file blob/SHA-256 hashes were **all independently reconfirmed exactly matching** the proposition (§5–§12 above). The **one factual discrepancy found** is the decision-subject character count (§38 above: claimed 218, independently measured 232) — a self-reported arithmetic error that does not change any pass/fail outcome (both values are well under the real 500-char schema limit) and does not mislead a human about scope, SHA identity, or command content.

## 47. Final Verdict (§87)

## **VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR ELECTION**

All facts, commands, rollback, and scope were independently reconstructed and matched the proposition exactly, with two bounded, non-blocking findings that do not affect human understanding or execution safety:

1. **Decision-subject character-count error** (§38/§46): proposition states 218 characters; independently measured 232. Both are well within the real 500-character schema limit (`human_governance_record.schema.json`'s `decision_subject.maxLength`). Recommend the next phase (7N.2, election drafting) recompute and cite the correct length when finalizing the CHGR's `decision_subject`.
2. **Authority-binding tooling gap** (§40): no machinery today programmatically binds the exact `docs/PHASE_149O_20L_7N_...md` document content/commit into a decision session or CHGR — a human/future-phase operator must transcribe the proposition text by hand into election-tool fields, with no automated staleness/tamper check against the source document. This is a pre-existing tooling gap across the whole CHGR/decision-session subsystem, not something 7N or 7N.1 introduced or could unilaterally close; it should be disclosed to the human at election time (7N.2) as a residual limitation, consistent with the same category of disclosed-but-not-closed limitation this project already carries for D3-3 (§37) and HMIC-REQ-063 (7N document §28).

No candidate staleness, no factual defect affecting SHA/digest/diff/count identity, no unsafe or incomplete command, no rollback defect, and no authority-model blocker were found. The task brief's own 41-hex-character caveat was independently checked and found to be inapplicable to these specific hashes (§2 above) — reported, not silently corrected.

## 48. Expected Clean State — Confirmed (§88)

| Item | Value |
|---|---|
| Redeployment proposition | VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR ELECTION |
| Human election | NOT INITIATED |
| CHGR | NOT CREATED |
| Candidate | `b0840e96a7ffb12308e95828aa5927c3e7c770c0` |
| Dell (per cited prior evidence, not re-measured this phase) | still at `28bf137b5dc95d024e8913b678dce0501a46fd0f` |
| RepositoryIdentity | absent |
| DeploymentBinding | absent |
| HMIC certification | absent |
| Boundary C / Boundary A | not authorized |
| Runtime | Observed / observe / unavailable |

## 49. Recommended Next Phase (§89)

**149O.20L.7N.2 — Dell Current-Source Redeployment Human Election + CHGR Publication.**

Should: re-check proposition currentness immediately before presenting it (repeat §6's authority-drift check against HEAD/origin/main at that phase's own entry); present the exact canonical proposition (§46 preview text of the 7N document) to the human, explicitly disclosing this phase's two non-blocking findings (§47 above), particularly the corrected 232-character decision-subject length; collect APPROVE/DECLINE/AMEND; require separate confirmation before publishing; publish a canonical CHGR binding the candidate SHA (`b0840e96a7ffb12308e95828aa5927c3e7c770c0`) and old SHA (`28bf137b5dc95d024e8913b678dce0501a46fd0f`) directly in `decision_subject`/`conditions`; perform **zero** Dell mutation; stop. Only after a **149O.20L.7N.3 — Dell Current-Source Redeployment Authority Independent Verification** phase re-confirms the published CHGR's authority should any execution phase (149O.20L.7P or equivalent) begin.

## Governance

Normal governed PCAE lifecycle used throughout (`pcae task`, `pcae commit implementation`, `pcae phase complete`, `pcae push`). No raw `git commit`/`git push`. No `--no-verify`. No force push. No hook/finalization bypass.

## Proof of No Prohibited Action

- **No election initiated:** §41 — zero decision sessions reference the candidate SHA.
- **No CHGR published:** §41 — `.pcae/publication-execution/published/` contains only `prp-*.json` preview records, no `chgr-*.json`.
- **No Dell mutation:** §41 — zero SSH/network commands targeting any Dell host were issued this phase; all commands targeted this Mac's local Git store and disposable local clones/worktrees only.
- **No RepositoryIdentity created:** §41 — no `.pcae/repository-identity.json` or equivalent file exists anywhere in this repository checkout.
- **No DeploymentBinding created:** §41/§34 — no binding record exists; only source code for the (uninvoked) producer/admin script.
- **No certification performed:** §25 — the HMIC digest recomputation is source-identity only, explicitly not characterized as certification.
- **No activation:** §42/§48 — Boundary C/A/HATP all remain `NOT AUTHORIZED`.
