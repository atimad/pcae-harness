# Phase 149O.20L.7M — Dell Redeployment + DeploymentBinding First-Use Sequencing Architecture

## 0. Status

**Architecture/design only.** No human election initiated. No CHGR published. No Dell mutation (read-only Dell access was not needed and was not used — all evidence below is reconstructed from primary local sources: git, contracts, production source, and prior phase docs). No RepositoryIdentity created. No DeploymentBinding created. No producer invoked against Dell. No HMIC certification performed. Boundary C, Boundary A, HATP activation, and Cutover Record all remain untouched and **NOT AUTHORIZED**.

**Phase-entry commit:** `b0840e96a7ffb12308e95828aa5927c3e7c770c0` (`Phase 149O.20L.7L.6: repair commit-hash mention in canonical staging report for finalization gate`). `origin/main == HEAD`, 0 commits ahead, working tree clean at entry.

**Reconciliation:** `pcae phase-report reconcile --phase-id 149O.20L.7L.6` → `delivery_recorded_bookkeeping_incomplete`, 2 generations promoted, marker `already_dispatched`, checkpoint `completed_receipt_best_effort_incomplete`, receipt absent, mutation **none** (inspection only). No prior-phase artifact was altered by this phase.

## 1. Purpose and Method

Phase 149O.20L.7L.6 independently closed the last open HMIC source-scope finding (F-7L-5, F-7L-7) and confirmed HMIC-001 v1.4's 30-member frozen scope and `implementation_scope_digest` are correct and stable. The live Dell deployment remains at the older, independently verified candidate `28bf137b5dc95d024e8913b678dce0501a46fd0f`. This phase does not execute anything. It reconstructs, entirely from primary sources (git, contracts, production source, the governing CHGR, and prior architecture docs), the exact governed sequence required to (a) move Dell from `28bf137b...` to the current independently verified candidate, and (b) perform the first real RepositoryIdentity + DeploymentBinding transition afterward — and selects the architecturally correct model among three candidates (A: redeploy-first; B: SHA-bound combined proposition; C: two-CHGR sequence).

## 2. Entry Checks (this phase, read-only)

```
git status --short                     -> (clean)
git status --branch --short            -> ## main...origin/main
git log --oneline -160                 -> reviewed (149O.20L.7L.x / 7K / 7J / 7H / 7G / 7F / 7E / 7D.x / 7C / 7B / 7A chain)
git log --oneline origin/main..HEAD    -> (empty)
git rev-list --count origin/main..HEAD -> 0
pcae health                            -> healthy; active task idle (post-149O.20L.7L.6); git clean
pcae check                             -> passed
pcae status coherence                  -> coherent
pcae doctor task-memory                -> warnings (pre-existing: historical tasks/done/
                                           entries predating this phase, missing from
                                           tasks/DONE.md — unrelated, not remediated here,
                                           outside this phase's allowed-file scope)
pcae push check                        -> clean (nothing_to_push); task memory warnings;
                                           lifecycle review missing; phase report trust/
                                           identity both passed
pcae runtime inspect                   -> Observed / observe / unavailable
pcae notify status                     -> telegram configured/enabled/ready
pcae phase-report show --latest        -> 149O.20L.7L.6 canonical report, consistent,
                                           recommends 149O.20L.7M (this phase)
pcae phase-report reconcile --phase-id 149O.20L.7L.6 -> delivery_recorded_bookkeeping_incomplete,
                                           mutation none
pcae session bootstrap --agent-id claude-code-149o-20l-7m -> healthy, check passed,
                                           readiness "blocked" only because the active
                                           task is the expected idle placeholder
                                           (stale-vs-report by design until this
                                           phase's own task is opened)
```

No Dell SSH session was opened this phase. Dell's Boundary-P provisioning state and its deployed SHA (`28bf137b...`) were independently, freshly re-verified on the same day by 149O.20L.7D.11/7E; re-deriving them a third time from a fresh live session would add no new evidence for a phase whose scope is sequencing architecture, not deployment measurement. This is stated explicitly per §2 of the governing prompt, not left implicit.

## 3. Terminology Freeze (existing canonical names — none invented)

| Term | Canonical source | Meaning |
|---|---|---|
| `RepositoryIdentity` | `src/pcae/core/repository_identity.py`; HATP-001 §17 | CRI Layer 1: repository-local, randomly generated (UUID4), agent-writable, non-authoritative identifier. |
| `DeploymentBinding` | `src/pcae/core/hatp_bootstrap.py` (schema); `src/pcae/core/hatp_deployment_binding_admin.py` (producer, HBDC-REQ-056..070) | CRI Layer 2: admin-owned, agent-unwritable, Protected-Root-resident authority artifact binding `repository_id -> canonical_deployment_root -> principal_id/signer_key_id/provider_profile -> authority_scope -> status`. |
| `CHGR` | `.pcae/publication-execution/records/*.json`, `contract_id: CHGR-001` | Canonical Human Governance Record: an immutable, published election record. |
| `chgr-0e37ed1340b14311826722c4dbf3e856` | `.pcae/publication-execution/records/chgr-0e37ed1340b14311826722c4dbf3e856.json` | The governing CHGR for the *current* Dell source (candidate `28bf137b...`) and Action-9 PATH amendment. Its "condition 6" exclusion list and "condition 7" scope limit are the load-bearing text for this phase's whole analysis (§13-15). |
| "Candidate" | This phase | The exact commit that would become Dell's *next* deployed source, distinct from the *current* Dell SHA (`28bf137b...`). |
| "Two-transition model" | This phase (§23-24) | The collapsed Model A/C architecture: one authority-bearing decision for source redeployment, a second, separate authority-bearing decision for first-use identity+binding. |

## 4. Deriving the Current Candidate SHA (do not assume HEAD)

Per §4 of the governing prompt, HEAD must not be assumed to be the correct candidate without checking for later unverified authority-bearing drift. The last **independently verified** phase is 149O.20L.7L.6, whose own commit `b0840e96a7ffb12308e95828aa5927c3e7c770c0` is:

```
$ git rev-parse HEAD
b0840e96a7ffb12308e95828aa5927c3e7c770c0
$ git rev-list --count origin/main..HEAD
0
$ git merge-base --is-ancestor HEAD origin/main && echo ok
ok
```

`HEAD == origin/main`, and nothing has landed since 149O.20L.7L.6's own finalization commits (which are themselves the independently verified state — 149O.20L.7L.6 *is* the phase that closed the last open source-scope findings). There is no unverified authority-bearing drift beyond it to strip. **Candidate SHA = `b0840e96a7ffb12308e95828aa5927c3e7c770c0`.**

## 5. Authority-Relevant Drift, Candidate vs. HEAD

Since candidate == HEAD by §4, this check is trivially empty by construction (`git diff --stat HEAD HEAD` is empty across every path class named in §5 of the prompt: `src/pcae/**`, `scripts/**`, `docs/contracts/**`, `pyproject.toml`, schemas, authority-bearing tests). No further stripping was required.

## 6. Candidate Contract Versions, Digest, and 30-Member Set

- **HBDC-001:** `v1.1` (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md:6`), frozen by 149O.20B, amended by 149O.20L.7G (§16.1 producer/rotation/revocation requirements, HBDC-REQ-056..070). Status line: "FROZEN — PENDING INDEPENDENT VERIFICATION (v1.1 amendment)"; HBDC-REQ-001..055 remain independently verified per 149O.20C, unmodified.
- **HMIC-001:** `v1.4` (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md:4`), status "FROZEN ... PENDING INDEPENDENT VERIFICATION" carried through the 7K→7L.5 repair chain, independently re-confirmed unamended by 149O.20L.7L.6 itself (this is a re-verification phase's own subject, not new territory for 7M).
- **`implementation_scope_digest`**, recomputed live this phase directly against production source (`hatp_mandatory_certification.derive_implementation_scope_digest`):

  ```
  65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8
  ```

  Matches the value independently reconstructed by 149O.20L.7L.6's own canonical report exactly.
- **30-member frozen authority-bearing file set** (`hatp_mandatory_certification._FROZEN_AUTHORITY_BEARING_FILES`, `assert len(...) == 30` at line 1025): 23 `src/pcae`-relative files (core certification/HATP/agent/CLI/permission-broker/provider modules, including `core/repository_identity.py` and `core/hatp_deployment_binding_admin.py`) + 7 repository-root-relative files (four bound contracts and `scripts/hatp_certification_admin.py` / `scripts/hatp_deployment_binding_admin.py`). Full enumeration reproduced verbatim in the companion test module (§68).

## 7. Candidate Tree Inventory

```
$ git ls-tree -r HEAD | awk '{print $1}' | sort | uniq -c
4186 100644
  14 100755
```
4200 total tracked blobs; 0 symlinks (`120000`); 0 submodules (`160000`). `src/pcae/` — 454 entries, all `100644` (zero executables). `scripts/` — 4 entries: 3× `100644`, 1× `100755` (`check-docs-updated.sh`); both admin scripts (`hatp_certification_admin.py`, `hatp_deployment_binding_admin.py`) are `100644`, invoked as `python scripts/....py`, not directly executed, despite carrying a shebang line.

## 8. Old Dell Source State (`28bf137b5dc95d024e8913b678dce0501a46fd0f`)

Reconfirmed from canonical prior evidence (149O.20L.7D.11 §SS3/SS11, 149O.20L.7E §2/§5 live Dell read-back) — no fresh Dell access performed or needed this phase:

```
$ git merge-base --is-ancestor 28bf137b5dc95d024e8913b678dce0501a46fd0f HEAD && echo ok
ok
$ git ls-tree -r 28bf137b5dc95d024e8913b678dce0501a46fd0f | awk '{print $1}' | sort | uniq -c
4097 100644
  11 100755
```
4108 total tracked blobs at the old SHA. 149O.20L.7D.11/7E independently confirmed Dell's live `/opt/pcae/runtime/src` `git rev-parse HEAD` reads exactly `28bf137b...`, detached, clean, zero content drift.

## 9. Old→Candidate Authority-Relevant Diff (do not collapse into "source update")

```
$ git diff --stat 28bf137b5dc95d024e8913b678dce0501a46fd0f HEAD -- src/ scripts/ docs/contracts/ pyproject.toml
 docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md                    |   64 +-
 docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_..._CONTRACT.md | 1364 +++++++++++
 scripts/hatp_deployment_binding_admin.py                              |  245 ++
 src/pcae/core/hatp_deployment_binding_admin.py                        |  953 ++++++
 src/pcae/core/hatp_mandatory_certification.py                         |   46 +-
 5 files changed, 2598 insertions(+), 74 deletions(-)
$ git rev-list --count 28bf137b5dc95d024e8913b678dce0501a46fd0f..HEAD
134
```
`pyproject.toml` is byte-unchanged; no schema file under authority-relevant scope changed. Exact classification, not collapsed:

1. **HBDC v1.0 → v1.1** (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`): adds §16.1 (DeploymentBinding producer/rotation/revocation normative requirements, HBDC-REQ-056..070) and CBD-9/CBD-10; no existing requirement 001..055 modified.
2. **No producer → producer** (`src/pcae/core/hatp_deployment_binding_admin.py`, 953 new lines; `scripts/hatp_deployment_binding_admin.py`, 245 new lines): the DeploymentBinding creation/rotation/revocation/preview machinery did not exist at `28bf137b...`; it is wholly new at the candidate.
3. **HMIC v1.3 → v1.4** (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`, +1364 lines net): binds the new producer pair into `contract_versions`/frozen scope (149O.20L.7K), then a chain of same-version text repairs (7L.1, 7L.3, 7L.5) correcting stale claims and widening the AST-import guard — no requirement renumbered, HMIC-REQ-050's file count moved 28 → 30.
4. **28 → 30 source members** (`src/pcae/core/hatp_mandatory_certification.py`, +46/−? lines net): the two new producer-pair files added to `_FROZEN_AUTHORITY_BEARING_FILES`.
5. **Contract-text repairs** (F-7L-1/F-7L-2/F-7L-5/F-7L-7, all inside the same two contract files already counted above): stale "not yet operative" attack-matrix language, a stale intro-paragraph restatement, and an AST-guard relative-import gap — deployment-relevant because they are inside the bound contract text whose bytes participate in `implementation_scope_digest`, not separately enumerable files.

No other source change between `28bf137b...` and candidate touches `src/`, `scripts/`, `docs/contracts/`, or `pyproject.toml` — the wider 104-file / 24,868-insertion diff (§7 tree-inventory delta of +92 tracked paths) is entirely test files, non-contract docs, and `.pcae/` governance-record bookkeeping, none of it authority-bearing per HMIC-REQ-050's own enumeration.

## 10. Venv Reinstall Decision

**Not required.** Evidence:
- `pip show -f pcae-harness` confirms an **editable install** (`Editable project location: /Users/atilamadai/repos/pcae-harness`); `python3 -c "import pcae; print(pcae.__file__)"` resolves to the live source tree, not a copied/frozen artifact — path-bound, not byte-bound.
- `pyproject.toml`'s sole runtime dependency, `jsonschema>=4.18,<5`, is byte-unchanged between `28bf137b...` and candidate (`pyproject.toml` has zero diff, §9). The optional `hatp-hardware` extra (`fido2`, `cryptography`) is unneeded for this producer chain.
- This matches the mechanism decision already recorded and executed for the *current* Dell redeployment (`28bf137b...`) in `docs/PHASE_149O_20L_7D_9_...PROPOSITION.md` SS13 ("no venv reinstall — path-bound not byte-bound") and re-confirmed live by 7D.11/7E. The same reasoning applies unchanged to a source update from `28bf137b...` to the new candidate: an in-place `git fetch`+`checkout --detach` swap inside `/opt/pcae/runtime/src` suffices; `/opt/pcae/runtime/venv` does not need rebuilding.

## 11. Wrapper Update Decision

**Wrapper retained, unchanged.** The launch wrapper (`/opt/pcae/runtime/bin/pcae-launch`) lives at a fixed path *outside* this git repository's tracked tree — it is not `git`-cloned, so a source-tree checkout swap inside `/opt/pcae/runtime/src` is structurally incapable of mutating it. Its digest, `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`, is asserted as a fixed constant (`WRAPPER_DIGEST`) across the entire 7B→7E test chain and re-verified live each phase — always unchanged. Candidate→HEAD's diff (§9) touches no wrapper-adjacent mechanism (`pyproject.toml`'s single console-script entry, `pcae = pcae.cli:main`, is byte-unchanged). No current-architecture requirement forces a wrapper change; if a future phase's proposition needed one, that would be a materially different, separately-authorized action — not silently folded into a source-only redeployment.

## 12. Deployment Producer Availability Analysis

Reconstructed directly from `src/pcae/core/hatp_deployment_binding_admin.py` and `scripts/hatp_deployment_binding_admin.py`:

- **Must producer code physically exist on Dell before an exact first-use preview?** Yes, for an *exact*, Dell-bound preview. The module ships genuine read-only preview functions (`preview_create_deployment_binding`, `preview_rotate_deployment_binding`, `preview_revoke_deployment_binding`, returning a `DeploymentBindingPreview`/`DeploymentBindingPreviewKind` enum, exposed via `scripts/hatp_deployment_binding_admin.py --preview`), but they execute against a `HarnessPath` root and a `HATPTrustStore` — to preview Dell's *actual* future binding exactly, the code must run *against Dell's real files*, which requires the producer to already be deployed there.
- **Can a preview be generated on Mac against modeled Dell state?** Only a *generic/structural* preview (field names, preview-kind logic, error taxonomy) — not one carrying Dell's real `repository_id` or real `canonical_deployment_root` resolution, both of which depend on files that exist only on Dell.
- **Does the admin script require a local RepositoryIdentity?** Yes, strictly. `_resolve_repository_id` calls the read-only `read_repository_identity` and raises `RepositoryIdentityMissingError` if absent — the module explicitly documents that it "never calls `ensure_repository_identity()` itself, and never silently creates one as a side effect of a binding operation." No RepositoryIdentity → no valid preview *or* creation is possible, generic or exact.
- **Does preview depend on live Protected Root contents?** Yes — `canonical_deployment_root` resolution and the trust-store read for conflict/no-op detection both read real filesystem state.
- **Does preview need root/admin privilege?** Per prior provisioning evidence (149O.20L.7A), `/opt/pcae/runtime` and the Protected Root (`/etc/pcae/hatp/trust-store`) are `root:pcae`-owned, mode `0750` — reading/writing either requires membership in the `pcae` group or root, i.e., privileged execution context on Dell, not an unprivileged agent action.

**Consequence for Models A/B/C:** an *exact*, Dell-bound DeploymentBinding preview cannot exist until (a) candidate source is deployed on Dell, **and** (b) a RepositoryIdentity already exists on Dell. Both are downstream of source redeployment. This is the central fact driving §20-24's model selection.

## 13. RepositoryIdentity Creation Path on Dell

`src/pcae/core/repository_identity.py`, `ensure_repository_identity(root)`:

```python
def ensure_repository_identity(root: HarnessPath) -> RepositoryIdentity:
    existing = read_repository_identity(root)
    if existing is not None:
        return existing
    identity = _generate_repository_identity()
    target = root.join(REPOSITORY_IDENTITY_RELATIVE_PATH)
    payload = json.dumps(identity.to_dict(), indent=2, sort_keys=True) + "\n"
    _write_atomic(target, payload.encode("utf-8"))
    return identity
```

- **Path:** `.pcae/repository-identity.json`, relative to the repository root (on Dell: `/opt/pcae/runtime/src/.pcae/repository-identity.json`).
- **Bytes/schema:** exactly `{schema_version: 1, repository_instance_id: <uuid4>, created_at: <ISO-8601Z>}` — closed field set, unknown fields rejected on read.
- **Ownership/mode:** written via `tempfile.mkstemp` + `os.fdopen`/`fsync`/`os.replace` (`_write_atomic`); no explicit `chmod` — POSIX `mkstemp` default (`0600`) is retained, no group/world-readable mode is deliberately set.
- **Git-ignored status:** confirmed — `.pcae/.gitignore` line 4 lists `repository-identity.json`. Verified: no such file exists in this Mac checkout (never generated here).
- **Audit/provenance behavior:** none beyond the file write itself; `ensure_repository_identity` performs no separate audit-log call in this module.
- **Idempotency:** exists+valid → returned unchanged, no rewrite; missing → generated once, atomically; exists+malformed → **fails closed** (`RepositoryIdentityMalformedError`), never silently regenerated. Symlink rejection on both target and parent, before and after write.

**Not created this phase.**

## 14. Is RepositoryIdentity Part of Redeployment?

**No — derived, not assumed.** A source checkout landing at `/opt/pcae/runtime/src` via `git fetch`+`checkout` is a filesystem/VCS operation entirely disjoint from `ensure_repository_identity()`/`pcae init`, which is an explicit, separate function call. `.pcae/repository-identity.json` is git-ignored precisely because it must *not* travel with the source tree (§13) — it is host-local, generated fresh (or preserved, if already present) independent of which commit is checked out. Source redeployment therefore neither creates nor destroys a RepositoryIdentity; it is orthogonal machinery that must be invoked as its own explicit step.

## 15. RepositoryIdentity Authority Classification

Reconstructed from `docs/PHASE_149O_20L_7F_REPOSITORY_DEPLOYMENT_IDENTITY_AND_BINDING_ARCHITECTURE.md` §28 ("Repository-Identity Creation vs. the Election Requirement") and HATP-REQ-048 (repository identity "confers no authority by itself" / "grants no HATP authority," needs no human approval) — **not inferred from condition 6's silence**, per the governing prompt's explicit instruction: condition 6 (§16 below) is read exhaustively, and RepositoryIdentity creation is not among its six named exclusions (venv reinstall, wrapper mutation, DeploymentBinding, Boundary C, Boundary A, Cutover Record/Permission Broker/COMP-002 change, repository onboarding). 7F's own §28 conclusion — that identity creation "would not itself pre-decide, narrow, or partially satisfy any part of the DeploymentBinding election" because it grants no authority — is independently re-affirmed here from the same primary sources (HATP-REQ-048, HBDC-REQ-042's "identity alone confers no authority" text, CBD-5). **Classification: no election required; not part of the DeploymentBinding election's scope; does not require its own CHGR.** This is the load-bearing fact that makes the two-transition model's second stage internally two-part (unelected identity step, then elected binding step) rather than two full elections.

## 16. CHGR Condition 6 — Exact Wording, Re-Read Directly

Recovered by reading `.pcae/publication-execution/records/chgr-0e37ed1340b14311826722c4dbf3e856.json` directly (not via a doc's citation of it):

> **6)** "No venv reinstall, no wrapper mutation, no DeploymentBinding, no Boundary C, no Boundary A, no Cutover Record, no Permission Broker/POL-005/COMP-002 change, and no repository onboarding are authorized by this election, in this or any future phase, without a fresh, separate election."

This is an **exhaustive exclusion list of six named categories**, not a positive grant. RepositoryIdentity creation is not named. What it prohibits, exactly:
- Combined redeployment+binding proposition using *this* CHGR as authority for the binding half — **prohibited** ("no DeploymentBinding ... without a fresh, separate election").
- Combined identity+binding proposition — condition 6 does not name identity at all, so it neither prohibits nor requires anything about identity; identity's non-authority status (§15) is what actually settles that question, not condition 6.
- Only reuse of *old* authority — no; condition 6 explicitly extends to *this* CHGR itself and to *any future phase*, not merely to prior CHGRs. A brand-new, otherwise-valid future election that tried to bundle DeploymentBinding creation into the *same* election as something condition 6 already covers would still need to be that election's *own fresh* act — condition 6 is forward-referring to the DeploymentBinding decision needing its own dedicated election, wherever it occurs.

## 17. Old CHGR Applicability — No Fallback

Two applicability questions, both independently confirmed **no**:

- **Can `chgr-0e37ed1340b14311826722c4dbf3e856` authorize the *candidate* redeployment (to `b0840e96...`)?** No. Its own condition 7, read directly from the same JSON: *"This CHGR authorizes exactly the source-identity transition to `28bf137b5dc95d024e8913b678dce0501a46fd0f` and the Action-9 PATH amendment described in SS15-16 — no other source SHA, branch, or ref is authorized."* `decision_subject` names `28bf137b...` explicitly. The candidate is a different SHA.
- **Can it authorize RepositoryIdentity or DeploymentBinding creation?** No — condition 6 (§16) explicitly excludes DeploymentBinding without a fresh election, and `decision_subject`/`rationale` scope the whole record to the redeployment-to-`28bf137b...` + PATH-amendment decision only; RepositoryIdentity is outside its subject entirely.
- Two older historical CHGRs (`chgr-96a0ce12756e4cc892492a87af1db832`, `chgr-541cb08c313b4f8884970172d37c5a1d`) were already independently confirmed by 149O.20L.7E §4 not to contain the candidate SHA in either `decision_subject` or `rationale` — re-confirmed here as still applicable (byte-unchanged, §21).
- A fourth, older, git-tracked CHGR — `chgr-d4343fa51b9743f3abaeb87a881a78b1` (`decision_subject`: "Boundary-P provisioning authorization for Class-B target Option B ... per L.5A doc §19 proposition", `created_at` 2026-08-14, one-shot plan/commit-bound to Git commit `2e97651ef9366e6427b26ea061deac827b6485e9`, HMIC-001 v1.3/HBDC-001 v1.0) — independently found this phase via a direct filesystem enumeration of `.pcae/publication-execution/records/chgr-*.json` (not assumed from any prior doc's count). Its `conditions` text explicitly excludes "HMIC certification/binding/revocation (Boundary C)" and is plan/commit-bound to a different commit and an earlier HMIC/HBDC version pair than the candidate — it cannot authorize the candidate transition, RepositoryIdentity creation, or DeploymentBinding creation either.

**No fallback exists.** Four CHGRs exist in total; none authorizes the candidate transition or any first-use action.

## 18. Does Source Redeployment Require a Fresh CHGR?

**Yes — derived, not assumed.** `chgr-0e37ed1340b14311826722c4dbf3e856`'s own condition 7 is not merely silent about later SHAs; it affirmatively states it authorizes "exactly" `28bf137b...` and "no other source SHA, branch, or ref." A redeployment to the candidate (`b0840e96...`) is definitionally a different SHA. Per the exact same election-scoping logic condition 6 uses for DeploymentBinding, the governance architecture's pattern (every prior Dell-affecting phase in this chain — 7A, 7D.9, 7D.11 — required its own dedicated CHGR keyed to the specific candidate SHA) is not incidental; it is how `chgr-0e37ed...` was itself worded and how every predecessor CHGR in this repo's history operates. **A fresh, dedicated source-redeployment CHGR is required** before the candidate can be deployed to Dell.

## 19. Model A — Redeploy First (Full Specification)

1. Materialize an exact candidate-source deployment proposition (candidate SHA `b0840e96...`, old→candidate diff per §9, venv/wrapper decisions per §10-11, tree/mode-mapping per §7, rollback target per §8).
2. Human election (APPROVE/DECLINE/AMEND) on that proposition.
3. Confirmation capture.
4. CHGR publication, scoped exactly to the redeployment (mirroring `chgr-0e37ed...`'s own condition-7 pattern of naming exactly one SHA).
5. Independent authority verification (a dedicated verification phase, per §26 of this document — every authority-bearing execution retains its own independent verification, never combined).
6. Redeploy candidate source (fetch+checkout+mode-remap+read-back, per the same mechanism already used and verified for `28bf137b...`, §10).
7. Independent real-host source verification (SHA read-back, digest/tree confirmation, wrapper-digest re-confirmation).
8. Separately prepare a RepositoryIdentity/DeploymentBinding proposition — at this point, RepositoryIdentity can be created on Dell (§15, no election needed) so the proposition can bind an *exact*, real `repository_id` (§20 below resolves why this ordering is required, not optional).
9. Fresh election on that first-use proposition (satisfies condition 6 literally, §16).
10. Binding transition (create + independent verification, per §26).

## 20. Model A Advantages

- Producer physically exists on Dell before any binding preview is attempted — an *exact*, not generic, preview becomes possible (§12).
- Source-currentness is unambiguous at every step: the binding proposition is built against source already confirmed deployed, not source promised-to-be-deployed.
- An exact Dell-local dry-run (`--preview`) is possible, because RepositoryIdentity already exists by the time the binding proposition is drafted.
- The binding proposition is based on actual post-redeployment state (real `repository_id`, real resolved `canonical_deployment_root`), not a modeled approximation.
- Source rollback is fully isolated from any authority-artifact creation — if redeployment fails, nothing about RepositoryIdentity or DeploymentBinding has been touched yet.

## 21. Model A Disadvantages

- An extra CHGR/election cycle versus a single combined proposition.
- A temporary window where source is upgraded but the live HBDC evaluation still fails `no_repository_identity_present` (or, once identity exists, `no_active_deployment_binding_matches_repository_and_root`) — i.e., a deliberate, disclosed non-compliant intermediate state, not a defect.
- Additional deployment phase count in this project's phase-numbering scheme.

**Assessment:** these are real costs, but not architectural drawbacks — they are the direct, necessary consequence of §12's producer-availability fact (exact preview requires deployed producer + existing identity) combined with §18's fresh-CHGR requirement. No cheaper model avoids them without accepting a strictly worse preview-fidelity or rollback-isolation trade (§22-24).

## 22. Model B — SHA-Bound Combined Proposition (Full Specification)

One proposition binding: exact candidate SHA; source redeployment; mode mapping; venv/wrapper retention (§10-11); RepositoryIdentity creation; DeploymentBinding content; authority evidence; expected HBDC result — executed as one governed transition after one election.

## 23. Repository-ID Preview Problem (Critical — Determines Model B's Viability)

`_generate_repository_identity()` (§13) calls `uuid.uuid4()` with **no parameter to accept a caller-supplied or preselected value**, and `ensure_repository_identity()` is the *only* production entry point — it writes immediately the first time it is called on a repository lacking an identity; there is no separate "generate but don't persist" or "generate with a caller-supplied UUID" mode anywhere in `repository_identity.py`. Consequently:

- The exact future `repository_id` **cannot** be known at proposition-drafting time unless identity generation is executed first — and execution, by definition, is not something a pre-election proposition can have already done and still call itself "pre-election."
- Architecture does not support "identity UUID generated during proposition preparation without publication" as a distinct mode — generation *is* persistence, atomically, in the same call.
- Architecture does not support "identity creation can accept a preselected UUID" — no such parameter exists.
- The only remaining option — "proposition binds generation semantics rather than exact value" — is available (bind the *rule*: "a fresh UUID4 will be generated by `ensure_repository_identity()` at execution time"), but this means a human approving a Model B proposition is approving a rule, not the actual `repository_id` field value that will appear in the resulting `DeploymentBinding`.

**This is a real weakness, not a false concern.** Since RepositoryIdentity creation itself needs no election (§15), the only way to give a human an *exact* `repository_id` to review is to create the identity before the election — which, if bundled inside "one combined proposition," means the proposition's own preparation must already execute part of what it claims to be proposing. That collapses Model B's "one proposition, one election, one execution" claim: identity generation would have to happen either (a) before the election (making it not really part of the same governed transition, contradicting Model B's own premise), or (b) the human approves an inexact/rule-bound preview rather than exact content, contradicting §22's "exact expected repository ID if knowable before creation" requirement, which turns out **not to be knowable**.

## 24. Model B Rollback Complexity

Failure sequence: source update succeeds → RepositoryIdentity creation succeeds → binding creation fails.

- **Source:** could in principle be rolled back independently (§8's rollback target still applies), but doing so after a RepositoryIdentity now exists at the new source's `.pcae/` location leaves an identity created under semantics belonging to a source version that is no longer deployed — the identity itself is source-version-agnostic (§13's schema has no source-SHA field), so this is survivable, but only by accident of schema design, not by architectural intent within Model B's own single-proposition framing.
- **Identity:** per §15's non-authority status and the "leave once legitimately created" principle (§30 below), identity should not be deleted merely because a later step in the *same combined operation* failed — but Model B never separately decided this; it inherited it opportunistically from Layer-1/Layer-2 independence, not from its own design.
- **Binding:** genuinely failed to create — nothing to roll back (the module's own preview-then-create pattern means a failed create is a no-op on the trust store in the success path, but see §28's audit-gap carry-forward for the *durable-mutation-with-audit-failure* case, which is a different, narrower failure mode).
- **Net assessment:** Model B's rollback question does not have a clean, single, pre-decided answer — it only resolves correctly because Layers 1 and 2 happen to be independent by pre-existing architecture (§15), not because Model B itself designed for this. A model whose safety depends on an accidental property of unrelated architecture, rather than its own explicit design, is weaker than one (§19) that never creates the ambiguity in the first place.

## 25. Model B Preview Fidelity

Per §23, a human reviewing a Model B proposition before the producer exists on Dell and before RepositoryIdentity exists cannot see the exact `repository_id` field, and — per §12 — cannot see an exact `canonical_deployment_root` resolution either (that also depends on live Dell filesystem state reachable only once source is deployed there). **Marked as a weakness**, consistent with the governing prompt's instruction (§22): "If preview is approximate rather than exact: mark as weakness." Model B can offer, at best, a structurally-exact-but-value-approximate preview (field names and validation rules known; `repository_id`, `valid_from`, and privilege-dependent `canonical_deployment_root` resolution not knowable exactly).

## 26. Model C — Two-CHGR Sequence (Full Specification)

- **CHGR-1:** source redeployment only — election, publication, execution, independent verification, exactly mirroring §19 steps 1-7.
- **CHGR-2:** RepositoryIdentity + DeploymentBinding first use — RepositoryIdentity creation (no election, §15) performed as an administrative step once source (and hence the identity/binding producer code) is deployed, then a DeploymentBinding proposition drafted against the now-real `repository_id`, election, publication, execution, independent verification.

## 27. Three-Way Distinction — Do Models A and C Collapse?

**Yes — they collapse into the same practical sequence; this is stated, not disguised.** Model A's step 4 ("CHGR") and step 9 ("fresh election... satisfies condition 6") are, in substance, exactly Model C's "CHGR-1" and "CHGR-2." Model A's prose never named the second decision point "a CHGR" explicitly, but §15-16 establish that any DeploymentBinding-authorizing election *must* be recorded as a fresh CHGR to satisfy condition 6 — so Model A's step-9 election necessarily *becomes* Model C's CHGR-2 the moment it is published. The only genuine difference is terminological (Model A's prose emphasizes the redeploy-then-prepare *ordering*; Model C's prose emphasizes the *authority-record count*), not architectural. Going forward, this document refers to the collapsed A/C architecture as the **"two-transition model"**, contrasted with Model B, the **"one-transition (combined) model."**

Model A did leave one thing implicit that Model C's explicit "CHGR-2: RepositoryIdentity + DeploymentBinding" framing states directly: whether identity creation needs *its own* authority record separate from the binding's. §15 already answers this — no, identity needs no election at all — so "CHGR-2" is precise only insofar as it means "the DeploymentBinding election, with identity creation as an unelected administrative prerequisite step performed just before drafting that election's proposition," not "two things separately elected." This document adopts that precise reading.

## 28. Authority Separation, Preview Fidelity, Rollback Isolation, Failure Containment, Source-Currentness, Producer-Availability, Audit-Clarity — Model Comparison

| Criterion | Two-transition model (A/C) | One-transition model (B) |
|---|---|---|
| **Authority separation** | Clean: one CHGR authorizes source mutation only; a second, later CHGR authorizes identity-adjacent binding creation only. No single record spans unrelated boundaries. | One CHGR would authorize source mutation *and* binding creation together — spans two boundaries condition 6 treats as requiring independent, fresh authorization. |
| **Preview fidelity** | Exact: binding proposition drafted after real identity exists (§19 step 8); human sees real `repository_id`, real resolved `canonical_deployment_root`. | Approximate: `repository_id` cannot be known pre-election (§23); `canonical_deployment_root` resolution also unavailable pre-deployment (§12). Marked weakness (§25). |
| **Rollback isolation** | Source rollback (§8 target) is fully independent of identity/binding, because nothing identity/binding-related exists yet when a source-only transition might need rolling back (§19 disadvantage, accepted). | Rollback boundaries are not independently pre-decided; correctness depends on Layers 1/2's incidental independence, not on Model B's own design (§24). |
| **Failure containment** | Each stage's failure modes (fetch/checkout/mode-mismatch for stage 1; identity/binding-creation/audit failure for stage 2) are isolated to that stage; an earlier successfully-verified stage is never put in question by a later stage's failure. | A binding-creation failure inside a combined operation raises the question of whether to also unwind an already-succeeded source update and/or identity creation — genuinely ambiguous (§24). |
| **Source-currentness** | Strongest: producer first use always occurs against source independently verified *and already deployed* (§19 step 7 precedes step 8). | Weaker: the combined proposition's binding half is approved before the producer is confirmed deployed and working on Dell. |
| **Producer availability** | Producer confirmed physically present on Dell (§19 step 6-7) before any binding operation is attempted — strongest evidence. | Producer's presence on Dell would only be confirmed as part of the same combined execution the binding half also depends on — weaker evidence at approval time. |
| **Audit clarity** | A future auditor reads two CHGRs, each answering one clean question ("who authorized source deployment," "who authorized first binding, against which already-confirmed source and repository identity"). | A future auditor reads one CHGR answering a compound question, with `repository_id` and `canonical_deployment_root` values that did not exist in the approved text at election time — weaker audit trail. |

## 29. CHGR Condition-6 Criterion

Condition 6's phrase "without a fresh, separate election" is read here (§16) as requiring the DeploymentBinding decision to be its own dedicated election — separate from any *other* decision, including a source-redeployment decision, not merely separate from *prior* CHGRs. Model B's attempt to fold "fresh" (i.e., newly published, not reused) together with "combined with redeployment" does not satisfy "separate" under this reading: "separate" modifies *election*, and an election that simultaneously authorizes source mutation and DeploymentBinding creation is not separate from the source-mutation decision, even though it would be fresh (newly published) relative to prior CHGRs. **The two-transition model satisfies condition 6 cleanly; Model B's satisfaction is textually disputable and, given §23's preview-fidelity failure, moot in practice — it is properly rejected for the preview reason alone, independent of the condition-6 interpretation question.**

## 30. Carried-Forward Findings — Consequence for First-Use Sequencing

- **First-use audit gap (149O.20L.7J §17):** live fault-injection showed `create_deployment_binding` can durably mutate the trust store while an unrelated exception in the audit path propagates uncaught, leaving zero audit records for a real mutation — a real, named, non-blocking finding, explicitly carried forward, not repaired at v1.1/v1.4. **Consequence for this phase:** the two-transition model's stage-2 execution phase (§35 step 7) must, at minimum, independently re-verify audit-record presence immediately after any real `create_deployment_binding` call and treat a missing-audit/present-mutation state as requiring the same STOP-and-read-only-adjudicate discipline condition 5 of `chgr-0e37ed...` already establishes for unexpected HBDC results (§32) — this is a sequencing/verification-discipline requirement for the *future* execution phase, not a repair performed in 7M (explicitly out of scope, §69 of the governing prompt: "Do not repair in 7M").
- **Timestamp-parser gap (`hatp_bootstrap._parse_iso_timestamp` more permissive than the strict producer-output grammar):** scoped entirely to the *consumer* read path, not the producer's own output — HBDC-REQ-067 binds the producer's own `valid_from`/`created_at` values to the strict canonical grammar regardless of the permissive reader. **Consequence:** first-use generated artifacts (a real RepositoryIdentity's `created_at`, a real DeploymentBinding's `valid_from`) are protected on the *write* side because the producer always emits strict-grammar timestamps; the *known* residual risk is only that some other, already-existing malformed timestamp elsewhere could still be misread — irrelevant to a fresh first-use creation. Not repaired, not blocking.
- **HMIC revocation-validation gap (HMIC-REQ-103, revoking a binding after certification leaves certification `VALID`):** asymmetric handling (rich for certification-side revocation, none for binding-side) — real, incomplete, explicitly deferred to a future HMIC-001 amendment. **Consequence for first creation/certification sequencing:** does not block creating the *first* binding (no certification exists yet to be left stale by it) — it is a later-lifecycle concern (post-certification revocation), correctly out of scope for 7M's first-use architecture, as the governing prompt anticipated ("Likely later lifecycle issue, but derive" — confirmed).
- **HMIC-REQ-063 (executed-byte provenance, out of scope, v1.0):** `implementation_scope_digest` binds on-disk byte content, not proof that the running interpreter resolves imports to those exact files (shadowing, `sitecustomize`, `PYTHONPATH` injection, editable-install redirects could in principle diverge). **Consequence:** the future redeployment execution phase's independent verification (§19 step 7) must not overstate what a matching digest proves — it proves on-disk byte identity, not executed-code identity. This document does not overstate it either.

## 31. Current Candidate Source Identity (Summary — Future Proposition Input, Not Authorized Here)

- **Commit SHA:** `b0840e96a7ffb12308e95828aa5927c3e7c770c0` (§4).
- **HBDC-001:** v1.1. **HMIC-001:** v1.4 (§6).
- **`implementation_scope_digest`:** `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` (§6).
- **30-member frozen set:** confirmed via live `_FROZEN_AUTHORITY_BEARING_FILES` enumeration (§6), reproduced in the companion test module (§68).
- **Tree inventory:** 4200 tracked blobs, 4186×`100644`, 14×`100755`, 0 symlinks, 0 submodules (§7).

Not authorized for deployment by this phase.

## 32. Candidate Currentness

Confirmed ancestor of `origin/main` (in fact, identical to it) and no later authority-bearing drift exists beyond it (§4-5). If a future proposition-preparation phase re-derives this at a later date and HEAD has moved, it must re-run §4-5's check rather than assume this phase's answer still holds.

## 33. Rollback Candidate

**`28bf137b5dc95d024e8913b678dce0501a46fd0f`** — the currently deployed Dell SHA (§8), independently re-confirmed live by 149O.20L.7D.11/7E, unchanged since. This is the correct rollback target unless Dell's deployed state changes before the future redeployment executes, in which case that future phase must re-derive the rollback target from a fresh live read, not from this document. Both `28bf137b...` and the candidate are already present as local git objects in this repository (`git cat-file -t` succeeds for both), making rollback network-independent once the redeployment phase's own git remote/object-fetch step has completed.

## 34. Deployment Source Identity Consequence (Expected, Post-Redeploy, Pre-Anything-Else)

After a future candidate redeploy alone (before any identity/binding step): Dell's `implementation_scope_digest` becomes `65ff8ab0...` (matching §6); HMIC v1.4 becomes locally present; the DeploymentBinding producer becomes available and invocable; **still no certification** — HBDC evaluation would move from whatever residual it currently reports at `28bf137b...` toward `no_repository_identity_present` (if no identity exists yet) or later `no_active_deployment_binding_matches_repository_and_root` (once identity exists but before a binding is created) — never `COMPLIANT` from source redeployment alone.

## 35. RepositoryIdentity Generation Determinism

**Non-deterministic (random UUID4), confirmed from source, not assumed** (§13, §23). No production code path accepts a pre-selected value. This is the fact that determines the model selection: it forces the two-transition model's ordering (identity created only once source — and hence the identity-creation code path itself — is already deployed and runnable on the real target), and it is the specific reason Model B cannot deliver an exact pre-election preview (§23).

## 36. DeploymentBinding Preview-Input Analysis

Per `_deployment_binding_to_document` and `AuthorityEvidence` (§12 supporting research):

| Field | Known before execution? |
|---|---|
| `principal_id`, `signer_key_id`, `provider_profile`, `authority_scope` | Yes — caller-supplied via `AuthorityEvidence`, resolvable at proposition-drafting time (subject to §38's resolution gap) |
| `repository_id` | **No** — derived read-only from an *existing* RepositoryIdentity; not knowable until identity is created (§23) |
| `canonical_deployment_root` | **No**, exactly — deterministic *function* is known (`resolve_canonical_deployment_root`), but its resolved value depends on live target-host filesystem state (§12) |
| `valid_from` | No — generated at execution time (`_canonical_timestamp_now()`) |
| `status` | No — execution-computed (`"active"`) |
| `revoked_at` | Not applicable to creation (only set by a later `revoke_deployment_binding` call) |

## 37. Timestamp-Preview Analysis

`valid_from` is generated fresh at execution and cannot be bound to an exact future wall-clock value by a pre-election proposition without inventing a value the architecture does not support presetting. Per the governing prompt's own instruction (§47): approval should depend on the **canonical-generation rule** ("`valid_from` is set to `_canonical_timestamp_now()` at the moment of execution, using the strict canonical grammar HBDC-REQ-067 requires"), not an impossible exact pre-committed timestamp. This document does not manufacture a fake exact value.

## 38. Signer / Provider / Scope Resolution

HBDC-REQ-058: `principal_id`, `signer_key_id`, `provider_profile`, `authority_scope` "SHALL be drawn from the admin's own enrollment context, not from repository-local state or agent-supplied input." No canonical derivation formula, registry, or fixed vocabulary exists anywhere in this repository for these four values — the producer validates only non-empty-string shape, with no cross-validation against any `principals`/`signers` registry (an explicitly deferred gap noted in 149O.20L.7H). **This document does not invent values.** A future first-use proposition-preparation phase must resolve these as a genuine administrative enrollment decision (who is the approving human's PCAE `principal_id`, which signing key, which provider profile, what scope) — not derive them from source, because no derivation exists to find.

## 39. First Binding Target / Subject

**`/opt/pcae/runtime/src`** — the current PCAE runtime repository's own deployed checkout, confirmed as the canonical deployment root per `docs/PHASE_149O_20L_7A_...PREFLIGHT.md` (line ~367, "Canonical deployment root / Model-A install (HBDC-REQ-022-024)"). **Not** a future managed-project repository — that concept remains undesigned and explicitly out of scope (149O.20L.7F §18/§42, re-confirmed here).

## 40. Principal

Per §38, no canonical convention exists to derive `principal_id` from. It must be resolved as an explicit enrollment-context decision by a future proposition-preparation phase, informed by whatever PCAE principal identity has already been assigned to the approving human's signing key (per HATP-001 §17's "admin principal assigns a PCAE principal_id to that key" model, `docs/PHASE_149O_1B_1_...ARCHITECTURE.md` line ~558) — not assumed to equal a Unix username or any other convenient stand-in.

## 41. Trust-Store Target

**`/etc/pcae/hatp/trust-store`** (the Protected Root's default production location on Linux, `HATPTrustStore.production()` / `_default_production_trust_root()`), admin-owned, agent-unwritable, holding the DeploymentBinding registry. No write performed or proposed this phase.

## 42. Expected Post-Binding HBDC Result (Disposable / Local Model Only)

Modeled, not measured live: once (a) candidate source is deployed on Dell, (b) a valid RepositoryIdentity exists there, and (c) a valid, active, matching DeploymentBinding exists in the Protected Root, and all current Boundary-P physical state remains intact (unchanged from 149O.20L.7E/7D.11's independently verified provisioning) — the expected `verify_class_b_deployment_conformance` result is **COMPLIANT**. This is a disposable, local-model expectation derived from reading `_check_deployment_identity`'s own evaluation order and terminal branches (matches the same subject-alignment already independently confirmed clean by 149O.20L.7F §43) — **not a claim that live Dell is, or will be, compliant**; only a future phase's live measurement can establish that.

## 43. Unexpected-HBDC Policy (For the Future Execution Phase)

Mirroring `chgr-0e37ed...`'s own condition 5 pattern (mandatory STOP-for-read-only-adjudication on any unexpected Action-9 residual): if a future first-use execution phase's live HBDC result differs from §42's expected `COMPLIANT`, that phase must **STOP**, not certify, and not repair anything under its own authority or broaden authority to explain the discrepancy. Whether source, identity, or binding should be rolled back in that event is an operation-type-specific decision (§44-45), not a blanket policy — a STOP is universal; an automatic rollback is not.

## 44. Binding-Failure Rollback Policy

The producer already provides a first-class `revoke_deployment_binding` lifecycle operation (HBDC-REQ-056..070) — a correctly created binding that later becomes undesirable (e.g., HBDC fails for an unrelated reason after certification) should be **revoked, not deleted**, using that existing lifecycle mechanism, never an ad hoc file removal. A binding should not be automatically revoked purely because of a downstream, unrelated HBDC failure without a governed decision to do so — automatic revocation on any anomaly would itself be a silent authority action.

## 45. RepositoryIdentity Rollback Policy

If identity is created and a subsequent binding-creation attempt fails, **the identity should remain.** Reasoning, not assumption: identity is non-authoritative (§15) and idempotent-safe to keep (§13 — re-running `ensure_repository_identity()` against an existing valid identity is a no-op read, never a rewrite); deleting it would not "undo" anything authority-relevant, but *would* destabilize `repository_id` continuity for any subsequent binding attempt (a new identity would mean a new UUID, requiring the *next* proposition to be redrafted against a different value). Leaving a legitimately created identity in place is the architecturally favored answer, matching the governing prompt's own expectation (§55).

## 46. Source-Rollback Policy After Identity/Binding Mutation (Model-B-Specific Risk, Explicitly Analyzed)

If source update and binding creation happened inside the *same* operation (Model B) and later needed source-only rollback, the resulting state would have a DeploymentBinding created under the *newer* candidate's semantics (schema/contract version) while the deployed source reverts to the *older* SHA's semantics — a binding whose provenance no longer matches the source that's actually running. This is a genuine, Model-B-specific hazard with no clean resolution inside Model B's own single-transition framing; it does not arise under the two-transition model, because source-only rollback (§33) can only ever occur *before* stage 2 (identity/binding) has begun, by construction of the ordering in §19/§26-27.

## 47. Selected Model

**The two-transition model (Model A and Model C, collapsed per §27).** Evidence-based rationale, not "fewer phases":

1. **Producer-availability (§12) and RepositoryIdentity-determinism (§23, §35) jointly force the ordering.** An exact, non-approximate first-use preview is architecturally impossible before both the producer is deployed and a RepositoryIdentity already exists — both are downstream of source redeployment. Any model that tries to preview an exact DeploymentBinding before redeployment is describing something the codebase cannot actually produce.
2. **CHGR condition 6 and condition 7, read directly (§16-18), both point the same direction:** condition 7 already requires a fresh CHGR for any SHA beyond `28bf137b...`; condition 6 already requires a fresh, separate election for DeploymentBinding. Two separate authority-bearing decisions were already anticipated by the existing governance record's own text — the two-transition model is not inventing new caution, it is executing what condition 6/7 already specify.
3. **Rollback isolation (§24, §46) and failure containment (§28) are strictly cleaner** in the two-transition model — no scenario exists where an in-progress combined operation leaves source, identity, and binding in a mutually inconsistent authority state.
4. **Audit clarity (§28) is strictly better:** two clean questions, two clean answers, versus one compound question whose approved-text values (`repository_id`, `canonical_deployment_root`) would not match the eventually-created record's actual values under Model B.
5. **Model B's own core premise — that a human can approve exact future binding content before the producer exists and before identity exists — is factually false** (§23, §25), independent of any preference for fewer phases.

## 48. Future Phase Decomposition (Two-Transition Model)

Using this project's own canonical phase-naming convention (`Phase 149O.20L.7<letter>[.<n>]`, dedicated verification phases following each execution phase, matching the 7D.9→7D.10→7D.11 and 7A→...→7E pattern already established for the *current* Dell redeployment):

1. **149O.20L.7N — Dell Current-Source Redeployment Proposition + Authority Preparation.** Materialize the exact candidate-redeployment proposition (candidate SHA, diff, venv/wrapper decisions, rollback target, exact commands) — no election yet.
2. **149O.20L.7N.1 (or 7O) — Redeployment Proposition Independent Authority Verification.** Independently re-verify the proposition's factual claims before it is presented for election (mirrors 7D.9→7D.10's pattern).
3. **149O.20L.7O (or 7P) — Redeployment Election + CHGR Publication.** First point at which a human sees APPROVE/DECLINE/AMEND for the source transition. Publication only — no Dell mutation in the same phase (mirrors `chgr-0e37ed...`'s own rationale: "This approval authorizes publication of a fresh CHGR ... It does NOT authorize any Dell mutation").
4. **149O.20L.7P (or 7Q) — Redeployment Execution.** Actual fetch+checkout+mode-remap+read-back against live Dell, per the elected proposition, exactly.
5. **149O.20L.7Q (or 7R) — Redeployment Independent Real-Host Verification.** Independent live re-confirmation of the new deployed SHA, digest, wrapper-digest invariance, and HBDC residual.
6. **149O.20L.7R (or 7S) — First-Use Identity/Binding Proposition Preparation.** RepositoryIdentity created on Dell (no election, §15) as an administrative step; DeploymentBinding proposition drafted against the now-real `repository_id` and `canonical_deployment_root`; `principal_id`/`signer_key_id`/`provider_profile`/`authority_scope` resolved (§38-40) — no election yet.
7. **149O.20L.7S (or 7T) — First-Use Proposition Independent Authority Verification.**
8. **149O.20L.7T (or 7U) — First-Use Election + CHGR Publication.** First point at which a human sees APPROVE/DECLINE/AMEND for DeploymentBinding creation — satisfies condition 6.
9. **149O.20L.7U (or 7V) — First-Use Execution + HBDC Re-Adjudication.** Actual `create_deployment_binding` call, immediate audit-presence re-verification (§30's carried-forward-finding discipline), live HBDC re-measurement against §42's expected `COMPLIANT`, STOP-and-adjudicate per §43 if it differs.
10. **149O.20L.7V (or 7W) — First-Use Independent Real-Host Verification.**
11. **149O.20L.7W (or 7X) — Boundary-C Preparation.** Only after step 10 confirms COMPLIANT — still not Boundary-C authorization itself.

Exact letter assignment is left to whichever phase actually opens 7N, per this project's convention of assigning the next letter at task-creation time, not pre-reserving letters this phase cannot verify remain free.

## 49. Do Not Combine Independent Verification

Every authority-bearing execution step in §48 (steps 4, 9) retains its own dedicated independent-verification phase (steps 5, 10) — none is combined with its execution phase, matching this repository's own unbroken pattern (7D.11 was independently verified by 7E; 7D.9's proposition was independently verified by 7D.10; every HMIC contract amendment in the 7K→7L.6 chain was independently re-verified by its own following phase).

## 50. First-Use Election Timing

**Not initiated this phase.** Per §48, the first point a human sees APPROVE/DECLINE/AMEND for DeploymentBinding creation is step 8 (149O.20L.7T or equivalent) — after source redeployment (steps 1-5) has already completed, been independently verified, and after RepositoryIdentity + an exact binding proposition (step 6) have been prepared and independently verified (step 7).

## 51. Source-Redeployment Election Timing

**Not initiated this phase.** Per §48, the first point a human sees APPROVE/DECLINE/AMEND for source redeployment is step 3 (149O.20L.7O or equivalent) — after this phase (7M, architecture) and a dedicated proposition-preparation phase (7N) and its own independent verification (7N.1/7O) have completed.

## 52. Existing CHGR Preservation

All four historical CHGRs (`chgr-0e37ed1340b14311826722c4dbf3e856`, `chgr-96a0ce12756e4cc892492a87af1db832`, `chgr-541cb08c313b4f8884970172d37c5a1d`, `chgr-d4343fa51b9743f3abaeb87a881a78b1`) remain **unchanged** this phase — confirmed: `git status --short .pcae/publication-execution/records/` reports empty (no diff). No consumed/superseded lifecycle semantics were invented; each remains exactly as scoped by its own text (§17-18).

## 53. D3-3 Status

**Carried, unchanged: CLOSED FOR CURRENT CONTINUATION / MACHINE-READABLE SUPERSESSION HARDENING GAP RETAINED** (originally established 149O.20L.7E §4/§50). Re-examined against this phase's sequencing architecture: the two-transition model's future phases (§48) will each publish their own dedicated, SHA-scoped CHGR (mirroring `chgr-0e37ed...`'s own condition-7 exact-SHA-naming pattern) — this does not change D3-3's applicability. No machine-readable supersession machinery is designed or implemented by this phase; the same manual, text-scoped applicability-checking discipline used throughout §17-18 remains the operative mechanism for future phases as well.

## 54. No Dell Mutation

No SSH session to any Dell host was opened this phase (§2). All Dell-state facts used here (deployed SHA, wrapper digest, Boundary-P provisioning) are cited from 149O.20L.7D.11/7E's own independently verified, same-week live evidence — not re-measured, and explicitly stated as such (§2), per the governing prompt's "prefer primary local evidence if sufficient" instruction (§65).

## 55. No Contract/Source Implementation

`git diff --name-only b0840e96a7ffb12308e95828aa5927c3e7c770c0..HEAD -- src/pcae/ scripts/ docs/contracts/ schemas/` at commit time (verified in §61) returns empty for all of `src/pcae/**`, `scripts/**`, and `docs/contracts/**` — this phase's only new tracked content is the architecture document itself and its companion test module.

## 56. Proof of No Identity/Binding/Election/CHGR/Certification

- No `.pcae/repository-identity.json` exists in this repository (checked, §13) — none was created.
- No new file exists anywhere in `.pcae/publication-execution/records/` beyond the three CHGRs already present pre-phase (§52) — none published.
- No `registry.json`, `certifications.json`, `certification-bindings.json`, or `active-certification.json` exists anywhere in the repository — no certification of any kind exists or was performed.
- No election of any kind (APPROVE/DECLINE/AMEND) was initiated — this document contains no rendered election UI, no confirmation-evidence artifact, no `chgrconf-*` record.
- No Boundary C or Boundary A action was taken; `pcae runtime inspect` (§2) is unchanged from entry (Observed / observe / unavailable).
- No HATP activation occurred.

## 57. Companion Tests

`tests/test_phase_149o_20l_7m_dell_redeployment_deploymentbinding_first_use_sequencing_architecture.py` — see §68 for coverage; run as part of this phase's own fast-green confirmation (§61).

## 58. Governance Results (This Phase)

- **pcae_health:** healthy
- **pcae_check:** passed
- **pcae_status_coherence:** coherent
- **pcae_doctor_task_memory:** warnings (pre-existing, unrelated — same historical `tasks/done/`/`tasks/DONE.md` gap carried since well before this phase, outside this phase's allowed-file scope, not remediated here)
- **pcae_push_check (entry):** clean (nothing_to_push)
- **pcae_runtime_inspect:** Observed / observe / unavailable (unchanged)
- **pcae_notify_status:** telegram configured/enabled
- **pcae_phase_report_reconcile (149O.20L.7L.6):** `delivery_recorded_bookkeeping_incomplete`, mutation none

## 59. Final Verdict

**SEQUENCING ARCHITECTURE DEFINED — READY FOR PROPOSITION PREPARATION.**

The two-transition model (Model A and Model C, collapsed, §27, §47) is clearly selected, with no blocking architecture gap: RepositoryIdentity's determinism/preview limitation (§23, §35) is a real constraint that *determines the ordering*, but does not block the two-transition model — it only rules out Model B. No open question in §1-58 remains unresolved in a way that would prevent a future phase from drafting the redeployment proposition (149O.20L.7N).

## 60. Expected Clean Outcome (Confirmed, This Phase's Exit State)

```
HMIC source-scope thread        CLOSED (149O.20L.7L.6, unchanged by this phase)
Dell Boundary P                 INDEPENDENTLY VERIFIED (149O.20L.7E, unchanged)
Dell source                     stale relative to current candidate (28bf137b... vs b0840e96...)
Current Mac candidate           IDENTIFIED EXACTLY (b0840e96a7ffb12308e95828aa5927c3e7c770c0, §4)
Redeployment architecture       DEFINED (this phase, §19/§48 step 1-5)
First-use architecture          DEFINED (this phase, §19/§48 step 6-10)
RepositoryIdentity               NOT CREATED
DeploymentBinding                 NOT CREATED
Source redeployment              NOT EXECUTED
Election                         NOT INITIATED
Boundary C / Boundary A          NOT AUTHORIZED
Runtime                          Observed / observe / unavailable (unchanged)
```

## 61. Commits, Push State, Governance Trail

```
$ git diff --name-only b0840e96a7ffb12308e95828aa5927c3e7c770c0..HEAD -- src/pcae/ scripts/ docs/contracts/
(empty)
```
This phase's own commits (task lifecycle open; doc + test addition; PROJECT_STATUS.md/CHANGELOG.md sync; task lifecycle close to idle; phase-completion metadata + canonical report sync) are itemized in the finalization commit sequence recorded by `pcae phase complete`. `origin/main..HEAD` count and pushed status are recorded at finalization time (§ Recommended Next Phase, below, and the canonical phase report).

## 62. Recommended Next Phase

**149O.20L.7N — Dell Current-Source Redeployment Proposition + Authority Preparation.** Scope, per §48 step 1: materialize the exact candidate-redeployment proposition — candidate SHA `b0840e96a7ffb12308e95828aa5927c3e7c770c0`, the old→candidate diff (§9), the venv-reinstall-not-required and wrapper-retained decisions (§10-11), exact tree/mode-mapping (§7), the rollback target `28bf137b5dc95d024e8913b678dce0501a46fd0f` (§33), and the exact future fetch+checkout+read-back command sequence (§9's mechanism, no commands executed). This is a proposition-preparation phase, not an election phase — no human election is initiated in 7N; per §51, the first election occurs later, in 7O or equivalent.
