# Phase 149O.20C — HATP Class-B Deployment Contract Independent Verification

## 1. Charter

Independent-verification-only phase. Independently re-derive, from primary sources (not from 149O.20B's own summary or test expectations), whether HBDC-001 v1.0 (frozen by Phase 149O.20B) is a sound, testable Class-B deployment trust contract for Model A, and whether its self-binding disposition (§17, Option A) is correct. This phase modifies no contract, no `src/pcae/**`, no `scripts/**`; it provisions nothing, certifies nothing, activates nothing.

## 2. Baseline (149O.20B Result)

Latest completed phase: 149O.20B — HATP Class-B Deployment Contract Freeze. Status: completed, report completeness: complete. Commits: 66c97470, 142643ed, f7c04fb9, cbeffff6. Pushed: yes, `origin/main..HEAD`: 0. New contract: HBDC-001 v1.0, FROZEN — PENDING INDEPENDENT VERIFICATION.

## 3. Initial Inspection (This Phase)

- `git status --short`: clean. `git rev-list --count origin/main..HEAD`: 0.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — 5 active-task-file directory-collapse (pre-existing, unrelated) and historical `tasks/done/` entries (149O.1H.3 through 149O.3) missing from `tasks/DONE.md` (pre-existing, historical, outside this phase's scope).
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: Observed / observe / unavailable.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest`: confirms 149O.20B completed/complete, governance results passed, recommended next phase 149O.20C (this phase).
- `pcae phase-report reconcile --phase-id 149O.20B`: reconciled, `already_dispatched`, checkpoint completed, receipt finalized, mutation none (inspection only).

Confirmed: repo clean, 0 ahead of origin, 149O.20B completed, HBDC-001 frozen but unverified, HBDC not yet HMIC-bound, no real provisioning, no real certification, no real activation, HATP NOT READY, runtime Observed/observe/unavailable.

## 4. Primary Sources Read

Read in full, directly (not via 149O.20B's summary): `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001 v1.0, all 30 sections, 55 requirements, 8 invariants, 21-scenario attack matrix); `docs/PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_ARCHITECTURE.md` (full architecture, §5–§18, §41, §45–§49, §63–§67, §74, §84–§86 read in detail); `docs/PHASE_149O_20B_HATP_CLASS_B_DEPLOYMENT_CONTRACT_FREEZE.md`. Cross-checked the architecture document's verbatim block-quote of HMIC-REQ-063 (149O.20A §14) against `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` §19 — byte-identical. HBDC-001 itself does not block-quote HMIC-REQ-063; it references it by name/paraphrase (§4, §14) — consistent with HBDC-001 being the deployment-topology contract, not the source of HMIC-REQ-063's own text. Confirmed HSCE-001, RAE-001, RWMPC-001, PBPA-001, PBPC-001 contain no reference to HBDC/Class-B/Protected Root (`grep -l` across `docs/contracts/*.md`), confirming HBDC-001's scope-isolation claim (§2). Read production source directly: `src/pcae/core/hatp_bootstrap.py` (`_default_production_trust_root`, `_reject_symlink`, `inspect_bootstrap_environment`, `resolve_canonical_deployment_root`, `deployment_binding_matches`), `src/pcae/core/repository_identity.py` (`ensure_repository_identity`), `src/pcae/core/hatp_mandatory_certification.py` (`_FROZEN_AUTHORITY_BEARING_FILES`, `_CONTRACT_IDENTITY_FILES`, `derive_contract_versions`, `derive_implementation_commit`/`_run_git`, `WRONG_REPOSITORY`/`WRONG_DEPLOYMENT`), `src/pcae/core/hatp_mandatory_cutover.py` (`_assess_hatp_mandatory_activation_readiness_at_root`, its `0o022` mode check, its own `_reject_symlink`). Grepped `src/pcae/core/*.py` for `PYTHONPATH`, `sitecustomize`, `usercustomize`, `sys.meta_path`, `ENABLE_USER_SITE`, `site-packages`, `editable`, `st_nlink`/hard-link, and any `--admin`/`PCAE_ADMIN`/`is_admin` construct — none found (see §8 below).

## 5. Reconstruction of 149O.20A Decisions

Independently re-derived from primary text (not accepted from HBDC-001's own summary):

- **Two-principal topology** (§6): agent OS principal + admin/bootstrap OS principal, reused unmodified from 149O.1B.1. A three-principal split (separate human-approver/bootstrap-admin) was explicitly deferred (HATP-REQ-028), not reopened. Confirmed unmodified in HBDC-001 §7.
- **Protected Root model** (§9): `_default_production_trust_root()` — fixed, platform-keyed constant path (macOS `/Library/Application Support/PCAE/HATP/trust-store`, Linux `/etc/pcae/hatp/trust-store`), never derived from `HOME`/env/CWD, never auto-created by any PCAE code path — confirmed directly in `hatp_bootstrap.py` (read the actual function body, §7 below).
- **Model-A selection** (§13): editable install from the canonical repository working tree, the only topology HMIC-001 v1.0/v1.1 certifies (HMIC-REQ-064). Models B/C/D explicitly not selected.
- **HMIC-REQ-063 Option C** (§14): conditional disposition — accepted-residual (equivalent to Option A) *only* when the agent's Python execution environment is itself admin-locked; BLOCKING when the agent can write its own import search path. Not Option A (unconditional accept) because the lock does not yet exist as a frozen requirement anywhere in the corpus prior to this phase; not Option B (unconditional block) because that would contradict HMIC-REQ-064's acceptance of editable-install as certifiable.
- **DRA-REQ-001..011** (§84): 11 requirements. DRA-REQ-001 (distinct OS accounts), DRA-REQ-002 (Protected Root admin-only creation), DRA-REQ-003 (agent Python import path admin-provisioned/agent-unwritable), DRA-REQ-004 (agent-writable path forfeits READY), DRA-REQ-005 (any frozen-file/contract/admin-script change invalidates certification), DRA-REQ-006 (copy/clone/migrate/restore requires new binding+certification), DRA-REQ-007 (revocation never auto-downgrades CutoverMode), DRA-REQ-008 (first certification is its own governed phase), DRA-REQ-009 (real activation is its own governed phase, distinct from provisioning and first certification), DRA-REQ-010 (fresh lock-held rehearsal immediately before real activation), DRA-REQ-011 (status claims never exceed freshly-confirmed matrix row).
- **15 deployment architecture attacks** (§85): reconstructed against the same table HBDC-001's 21-attack matrix builds on; HBDC-001's attacks 1–2, 6, 8–10 map directly onto DRA attacks 1–2, 6, 8–10 (root write, root redirect, wrong-repo reuse, symlink, host migration, backup restore); HBDC-001 adds 11 new attacks (ACL/group, writable-parent, hard-link, venv/interpreter/PYTHONPATH/user-site/`.pth`/import-hook/CWD/fake-package granularity, worktree/clone as distinct from the coarser DRA #6, Git executable, contract-freeze-not-activation) not present at the coarser DRA-attack granularity — this is a strengthening, not a contradiction.
- **DRA-S1..S9** (§86): all nine stop conditions independently re-confirmed NOT TRIGGERED against 149O.20A's own stated evidence (§6/§7, §7/§85 attack #2, §14/§22, §13/§25, §9/§29, §19/§29, §71/§82, §52–§54, §40/§64/§83 respectively).

**Comparison — HBDC-001 vs. 149O.20A**: no architecture decision is weakened. HBDC-001 strengthens DRA-REQ-002 (adding effective-ACL/group/ancestor/hard-link coverage, HBDC-REQ-015..020, beyond the mode-bits-only language DRA-REQ-002 itself used) and DRA-REQ-003 (naming 15 concrete environment-lock channels, HBDC-REQ-025..039, where DRA-REQ-003 named only "Python import search path" generically). No DRA-REQ decision is silently dropped: the DRA-REQ→HBDC-REQ traceability table (HBDC-001 §6) accounts for DRA-REQ-001, 002, 003, 004, 006 explicitly; DRA-REQ-005, 007, 008, 009, 010, 011 are process/governance requirements about certification lifecycle and status-claim discipline that HBDC-001 correctly leaves to HMIC-001/HMRC-001 and to PROJECT_STATUS.md discipline rather than re-stating as deployment-topology requirements — this is a correct scope boundary, not an omission, since HBDC-001 §2 explicitly disclaims redefining HMIC's certification data model or HMRC's state machine.

## 6. Requirement / Invariant / Attack Inventory — Mechanical Re-Extraction

Independently extracted via `grep -oE 'HBDC-REQ-[0-9]{3}'` against the live contract file (not copied from the 149O.20B test file):

- **55 unique requirement IDs**, `HBDC-REQ-001`..`HBDC-REQ-055`, min=1, max=55, **zero gaps, zero duplicates** — confirmed by exhaustive set-difference against `range(1,56)`.
- **8 unique invariant IDs**, `CBD-1`..`CBD-8` — confirmed by `grep -oE 'CBD-[0-9]+'`.
- **21 attack-matrix rows** — confirmed by counting `| N |`-prefixed table rows in §21.
- **Table/body cross-consistency**: §24's Full Requirement Traceability table contains exactly 55 rows, zero duplicate IDs, and every ID normatively defined somewhere in the document body (HBDC-REQ-054/055 are defined in §25, after the §24 table itself — confirmed present, not a gap).

Requirement inventory, invariant inventory, and attack inventory are each independently confirmed exactly as HBDC-001 §21 claims.

## 7. DRA-REQ-001 Traceability — Two-Principal Freeze (HBDC-REQ-001..005)

Independently verified against `hatp_bootstrap.py` source, not accepted from the contract's own citation:

- `inspect_bootstrap_environment()` (line 463) computes `current_uid = os.getuid()` and flags `"agent_and_admin_share_os_principal"` when `store_stat.st_uid == current_uid` — a live, mechanical, OS-identity-based check, not an application-level or environment-derived one. This directly substantiates HBDC-REQ-002.
- No `--admin` CLI flag, no `PCAE_ADMIN`-style environment variable, no `is_admin`/`def admin` function, exists anywhere in `src/pcae/core/*.py`, `src/pcae/*.py`, or `src/pcae/commands/*.py` (confirmed by grep across the tree). There is no application-level admin-authority mechanism to attack — HBDC-REQ-004's "not inferred from environment variables, function/class names, ... or Git commit identity" is not merely asserted; it is empirically true of the current codebase, and the contract text (§10, "admin authority conferred solely by OS-level identity and Protected Root ownership") correctly forecloses one from ever being added without contract revision.
- No self-elevation path exists: `scripts/hatp_certification_admin.py` is confirmed (via 149O.19.5G's cited finding, independently spot-checked by grepping for imports of the admin script's writer functions from any `src/pcae/**` file) to be the sole caller of the admin writer primitives (`_append_certification_record`, `_write_active_binding`, `_write_revocation`); no CLI/agent code path imports them. HBDC-REQ-005 holds.

**Verdict: DRA-REQ-001 fully frozen by HBDC-REQ-001..005.** No loophole found: distinct OS identities (confirmed live check exists), no application-level admin switch (confirmed absent), no env-derived admin authority (confirmed absent), no Git/repository identity as admin authority (confirmed — `derive_implementation_commit`/Git identity feeds `implementation_commit`, an evidentiary field, never an authority-conferring one), no agent self-elevation (confirmed no code path).

## 8. Protected Root — Permission Semantics (HBDC-REQ-011..021) and Effective-Access Attacks

Independently re-derived resolution and creation semantics from `hatp_bootstrap.py`:

- `_default_production_trust_root()` is a pure, deterministic constant lookup keyed only on `sys.platform`; it takes no parameter, consults no environment variable, and `HATPTrustStore.production()` calls it with no override path. `HATPTrustStore.__init__`'s `_test_only_root` parameter is a distinct code path, not reachable via `.production()`. **HBDC-REQ-011 confirmed: no override channel exists.**
- No `mkdir`/`os.makedirs`/equivalent call appears anywhere in `hatp_bootstrap.py`. **HBDC-REQ-012 confirmed: no agent-triggered auto-creation.**
- `_reject_symlink()` is independently implemented (confirmed present, not merely referenced) in `hatp_bootstrap.py`, and independently re-implemented (not shared/imported) in `hatp_mandatory_cutover.py` — both fail closed (raise) on `target.is_symlink()`. **HBDC-REQ-018 confirmed** for both modules actually exercised in the certification/cutover paths.

**Attack #17 (group-write)**: modeled — a file admin-owned with mode `0640` but the agent principal a member of a group holding write access. HBDC-REQ-015 requires this be tested as **NON_COMPLIANT** via *effective* access testing, not declared mode bits. **Finding (Non-Blocking, testability gap, §12 below)**: the current production code (`inspect_bootstrap_environment`'s `mode & (S_IWGRP | S_IWOTH)` check, and `hatp_mandatory_cutover.py`'s `mode & 0o022` check) tests only the trust-store root's own declared mode bits — it does not compute effective group-membership-derived access (e.g. checking whether the current agent UID belongs to the store's owning group when that group bit is set). This is a real implementation gap relative to HBDC-REQ-015's *effective-access* mandate — but it is an implementation gap, not a contract-text defect: HBDC-REQ-015's own text explicitly anticipates it ("a future verifier MUST test effective group-derived write access, not declared mode bits alone"), correctly scoping this as future verification work rather than presupposing it already exists.

**Attack #18 (ACL-write)**: same conclusion as #17 — no POSIX ACL / extended ACL inspection exists anywhere in the current codebase (confirmed by grep for `acl`, `getfacl`, `posix1e` — no matches in `src/pcae/core/*.py`). HBDC-REQ-016 is not yet mechanically testable; classified NON-COMPLIANT/INDETERMINATE-pending (§20 vocabulary), not silently assumed COMPLIANT — consistent with HBDC-REQ-053's fail-closed mandate. Same Non-Blocking finding as attack #17.

**Attack #19/#20 (writable-parent / writable-ancestor)**: `inspect_bootstrap_environment()` checks *only the immediate parent* of the trust-store root (`parent = store_root.parent`; checks `parent_mode & stat.S_IWOTH` and `parent_stat.st_uid != store_stat.st_uid`) — it does **not** walk the full ancestor chain "up to the point the agent principal has no write access at all" as HBDC-REQ-017 requires. This is the same class of finding as #17/#18: the contract text (HBDC-REQ-017) correctly names the full-ancestor-chain requirement; the current implementation only covers one level. Non-Blocking, same root cause.

**Attack #21 (symlink)**: `_reject_symlink` fail-closed behavior is directly confirmed live in both `hatp_bootstrap.py` and `hatp_mandatory_cutover.py`. No finding.

**Attack #22 (hard-link)**: independently searched — no hard-link (`st_nlink`, `os.link`, or equivalent) inspection exists anywhere in the HATP authority-state code paths (the only hard-link-related code in the repository is `hatp_evidence_store.py`'s *own* atomic-write publication technique for the unrelated, explicitly-non-authoritative evidence store — HSCE-001 §27). HBDC-REQ-019 (hard-link creation restricted to admin) is a normative requirement on the *admin's* real-world provisioning discipline, not a claim that PCAE code currently detects hard-link aliasing; the contract does not claim it does. **HBDC-REQ-019's own text is not underspecified** (it names the restriction precisely: "hard links to authority-bearing files SHALL NOT be created from any agent-writable directory") — but it is, like the ACL/group/ancestor checks above, not yet independently machine-verifiable against a real host by any code shipped today. Bundled into the same Non-Blocking finding.

**Attack #23 (rename/replacement)**: covered jointly by HBDC-REQ-017 (ancestor protection) and HBDC-REQ-020 (explicit directory-entry-mutation-equivalent-to-write statement); same implementation-gap caveat as above, not a text gap.

**Attack #24 (admin positive access)**: HBDC-001's normative text nowhere states Protected Root becomes immutable to the admin; HBDC-REQ-009 explicitly grants the admin principal exclusive write authority. No finding.

## 9. Model-A Python Execution-Environment Lock (HBDC-REQ-025..039) — Independent Attack

Independently searched `src/pcae/core/*.py` for any of: `PYTHONPATH`, `sys.meta_path`, `sitecustomize`, `usercustomize`, `ENABLE_USER_SITE`, `site-packages`, `editable` — **zero matches** relevant to environment-lock enforcement. This confirms, independently, that **no implementation of §13's environment lock exists yet** — expected and consistent with HBDC-001 being contract-freeze-only and 149O.20A (§14, §22–§23) having deferred implementation to a future provisioning phase. This is not a finding against the contract; §21's attacks 8–15 are therefore all currently in the **NOT YET IMPLEMENTED / NOT YET VERIFIABLE** state, correctly reflected by HBDC-001's own status line ("FROZEN — PENDING INDEPENDENT VERIFICATION") and by this contract's own §29 verdict block ("PENDING INDEPENDENT VERIFICATION" — which this phase interprets as contract-text verification, not live-host verification, consistent with the phase charter's §81 instruction not to attempt real provisioning).

Attack-by-attack modeling against the contract text (no live host touched):

- **Hostile PYTHONPATH** (attack #10 / prompt §33): HBDC-REQ-028 names three compliant designs (unset, fixed non-overridable, or allow-list-validated-reject-unrecognized) — a concrete, non-vague mechanism, not "should be handled" hand-waving.
- **User site** (§34): HBDC-REQ-029 requires disable-or-proven-unwritable, a binary, testable condition.
- **`.pth` code execution** (§35): HBDC-REQ-031 covers "any `.pth` file ... including one capable of executing `import`-prefixed lines" explicitly — the code-execution capability of `.pth` files is not overlooked.
- **sitecustomize/usercustomize** (§36–§37): HBDC-REQ-030 covers both identically ("wherever present on the resolved production `sys.path` ... admin-controlled and agent-unwritable, or absent").
- **`sys.meta_path` / import hooks** (§38): HBDC-REQ-032 covers this without requiring continuous process-memory inspection — scoped correctly to "via any admin-controlled startup path reachable in production," not an impossible universal guarantee.
- **CWD shadowing / `sys.path[0]`** (§39–§40): HBDC-REQ-033 explicitly names `sys.path[0]`/CWD and requires the resolved production `sys.path` never place an agent-writable, agent-selectable directory ahead of the canonical tree's package location.
- **Fake `pcae` package** (§41): HBDC-REQ-034 is explicit that compliance here is *jointly* achieved by HBDC-REQ-028/029/033, not an independent, additional runtime self-check — this is a deliberate, disclosed design choice (HBDC-001 §13 note), not an oversight.
- **Launcher/wrapper, shell/service environment** (§42–§43): HBDC-REQ-036/037 cover both, scoped precisely ("to the extent it affects module resolution, working directory, or the environment variables governed by HBDC-REQ-028..033" — not a blanket ban on all environment variables).
- **Git executable / PATH attack** (§44–§45): independently confirmed in `hatp_mandatory_certification.py`'s `_run_git()` that `derive_implementation_commit` invokes `subprocess.run(["git", *args], ...)` with a bare `"git"` argument — PATH-resolved, exactly the attack surface HBDC-REQ-038 names. The contract's chosen mitigation is deployment-level (admin-controlled `PATH`/pinned executable in the launch environment), not a code-level pinned-path change to `_run_git` — this is consistent with HBDC-001 being a deployment-topology contract, not a code-change contract (§5 non-goals: "does not... change Permission Broker behavior" and by extension does not mandate `src/pcae/**` edits). No Blocking gap: the requirement text is concrete and testable against the *deployment's* PATH configuration, independent of whether `_run_git`'s own Python source is later hardened.
- **Third-party dependencies / FIDO2/PIV** (§46–§47): HBDC-REQ-039 correctly scopes this as "not HMIC-certified source" but "agent SHALL NOT hold write permission allowing their replacement," satisfied by the same venv/site-packages lock — no separate claim about hardware-provider-library correctness is made.
- **Module-origin evidence / static-vs-continuous** (§48–§49): HBDC-001 §12 (Model-A conformance evidence, HBDC-REQ-023) names concrete evidence classes (`canonical_deployment_root` match, editable-install metadata resolution, no §13 redirect) without requiring continuous process-memory measurement — a static/provisioning-state guarantee, correctly and explicitly scoped (§14, HBDC-REQ-041).

**Finding (same Non-Blocking class as §8 above)**: none of HBDC-REQ-025..039 has a corresponding implementation in `src/pcae/**` today. This mirrors the Protected-Root-permission gap: the contract's normative text is sound, concrete, and non-vague per-requirement; a real conformance check against a live host cannot yet be run because no verifier code exists. Both gaps are appropriately deferred to a future implementation/provisioning phase, not concealed or overclaimed by HBDC-001's own status line.

## 10. HMIC-REQ-063 Option-C Boundary — Independent Verification

Re-derived independently (§5 above) and cross-checked against HMIC-001's own byte-identical quotation. **OPTION C VERIFIED**: HBDC-001 §14 correctly frames §13's environment lock as the mitigation that permits Model-A deployments to claim the accepted-residual branch, correctly states the BLOCKING fallback for deployments failing §13 (HBDC-REQ-040), and correctly disclaims cryptographic executed-source/runtime-module-resolution attestation (HBDC-REQ-041) — matching HMIC-REQ-063's own "named, explicit limitation — not a silent gap" framing exactly. No overclaim found: HBDC-001 nowhere states runtime-source provenance is solved.

## 11. Repository/Deployment Identity — Worktrees, Clones, Migration, Backup

Independently confirmed via `hatp_bootstrap.py`: `resolve_canonical_deployment_root()` calls `.resolve(strict=True)`, so a worktree, clone, or copy — each a distinct physical directory — canonicalizes to a distinct `canonical_deployment_root`, and `deployment_binding_matches()` (confirmed present, checks both `repository_id` and `canonical_deployment_root` against a non-revoked binding) returns `False` for any of them absent a fresh binding. `WRONG_REPOSITORY`/`WRONG_DEPLOYMENT` statuses are confirmed present in `hatp_mandatory_certification.py`'s certification-status enumeration. HBDC-REQ-042..046 (§16) restate this correctly and add no new mechanism beyond what 149O.1B.2 already establishes — consistent with HBDC-001's own claim (§16 intro, "No new mechanism is introduced").

## 12. HBDC Self-Trust / Binding Problem — Independent Re-Derivation (Load-Bearing)

**Empirically confirmed, not merely accepted from HBDC-001 §17's own text**: `hatp_mandatory_certification.py`'s `_CONTRACT_IDENTITY_FILES` (feeding `derive_contract_versions`, HMIC-REQ-067) lists exactly four contracts — HMRC-001, HATP-001, HSCE-001, RAE-001. `_FROZEN_AUTHORITY_BEARING_FILES` (the 24-file `implementation_scope_digest` set, HMIC-REQ-050) lists the same four contract `.md` files plus `scripts/hatp_certification_admin.py` as its five repository-root-relative entries. **`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` appears in neither list.** HBDC-001's bytes participate in *no* part of HMIC-001 v1.1's certification identity — not `contract_versions`, not `implementation_scope_digest`. This is independently verified directly against live production source, not accepted on the contract's own assertion.

**Clarifying a terminology ambiguity in the governing prompt**: the prompt's framing ("current HMIC bound-contract set: 8... target future HMIC set: 9") conflates two distinct notions found in the corpus: (a) the **repository's total frozen-contract corpus** — 8 contracts (HATP-001, HMRC-001, HMIC-001, HSCE-001, RAE-001, RWMPC-001, PBPA-001, PBPC-001), the count 149O.20B's own §20 cites when confirming none were byte-changed; and (b) **HMIC-001's own `contract_versions` binding field** (HMIC-REQ-067), which by design contains only 4 entries — RWMPC-001/PBPA-001/PBPC-001 are explicitly excluded from `contract_versions` by HMIC-REQ-068 even though their *module bytes* (not their contract-document bytes) participate in `implementation_scope_digest` via `permission_broker.py`/`permission_broker_foundation.py`. Under either counting convention, HBDC-001 is currently **absent** — confirmed by direct inspection, not by trusting either number in isolation. If a future HMIC-001 v1.2 amendment adds HBDC-001 to `contract_versions` per HBDC-REQ-048, the correct resulting count is **5** members of `contract_versions` (not 9) — the "9" framing in the governing prompt describes the total-corpus convention (8 existing + HBDC-001 = 9), which is a coherent count under that convention but must not be conflated with `contract_versions`'s own count. This document records this distinction so no future report misstates which "9" is meant.

**Self-binding attack (semantic drift)**: since HBDC-001's bytes are outside both binding mechanisms, an agent editing `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` today — weakening, say, the environment-lock requirements — would not change `implementation_scope_digest` or `contract_versions`, and would not invalidate any existing HMIC-001 certification (there is none yet, but the mechanism would not detect the edit even if one existed). This is independently confirmed true, not hypothetical.

**Option re-derivation** (independently, not accepting 20B's selection uncritically):
- **Option A (add HBDC-001 to HMIC's bound-contract set)**: correctly closes the semantic-drift gap using the existing, already-proven `contract_versions` mechanism (HMIC-REQ-067/069's drift-detection logic already exists and is exercised for the other four contracts).
- **Option B (HBDC-001 remains external, never bound)**: would permanently prevent HMIC certification from ever mechanically reflecting Class-B topology compliance — correctly rejected; "never" forecloses a needed future capability for no compensating benefit.
- **Option C (separate protected manifest binding HBDC-001's version/digest, independent of HMIC-001)**: would duplicate `contract_versions`'s existing purpose with a second protected-binding mechanism, adding attack surface (two trust anchors to keep synchronized) without a new guarantee `contract_versions` doesn't already provide — correctly rejected.

**Independent verdict: Option A is correct**, for the reason both the contract and this independent re-derivation converge on: HBDC-001 changes deployment-trust semantics that determine whether an HMIC certification may legitimately participate in a "deployment-ready" claim, so its normative identity must itself be protected-bound before such reliance is mechanically trustworthy. **This finding is reached independently by direct inspection of `_CONTRACT_IDENTITY_FILES`/`_FROZEN_AUTHORITY_BEARING_FILES`, not merely by accepting HBDC-001 §17's own stated rationale.**

**Is the current unbound state acceptable?** Yes — because real Class-B provisioning/certification/activation remain independently blocked regardless of this disposition (HBDC-REQ-050/051, DRA-REQ-008/009), so no certification exists today that could be misrepresented on HBDC-001's unbound strength. This is a correctly sequenced prerequisite, not a currently-exploitable gap, and not a defect in HBDC-001 itself.

## 13. 149O.20A Test-Repair Review (§90 of governing prompt)

Independently reviewed the diff (`git show 66c97470 -- tests/test_phase_149o_20a_hatp_deployment_readiness_architecture.py`). The repaired assertion changed from "no line of `git status --porcelain -- src/pcae docs/contracts` output is tolerated" to "no line is tolerated **except** an untracked (`??`) file whose path starts with `docs/contracts/`." This precisely means "no existing contract was modified" (any `M `/`A ` status on a previously-tracked `docs/contracts` file still fails the assertion) while allowing "a newly chartered contract may be added" (only brand-new untracked files under `docs/contracts/` are excused) — and continues to reject **any** status line touching `src/pcae` unconditionally. **Confirmed correctly scoped, not overly permissive.** No finding.

## 14. Fixed-Commit Repin Debt (§91)

The two 149O.19.5E.2/E.3 `docs/contracts` fixed-universe test failures are retained as pre-existing test debt per repository convention (feedback memory: fixed-commit `git diff` self-checks are permanently broken by any future contract file — this is repin-debt, not flakiness, and does not weaken current contract evidence since HBDC-001 §21's own live-extraction inventory is independently re-derived in §6 above, not sourced from any fixed-commit diff). Not opportunistically repaired; out of this phase's verification scope.

## 15. Requirement Testability Classification (§73)

All 55 requirements were reviewed. Classification:

- **Metadata/text-inspection testable today** (contract self-consistency, ID inventory, traceability tables, status-claim vocabulary): HBDC-REQ-001..005, 022..024, 040..055 — fully testable now, and exercised by this phase's own test module (§17 below).
- **Live-host-dependent, code exists**: HBDC-REQ-002 (`agent_and_admin_share_os_principal` check), HBDC-REQ-011/012 (root resolution/no-auto-create), HBDC-REQ-018 (symlink rejection), HBDC-REQ-042..046 (deployment-binding match) — mechanism exists in production source today; a real host is required to exercise it end-to-end, but the code path is independently confirmed present.
- **Live-host-dependent, mechanism NOT yet implemented** (§8/§9 findings): HBDC-REQ-013..017, 019..021 (effective ACL/group/ancestor/hard-link coverage beyond mode bits) and HBDC-REQ-025..039 (the full environment lock) — currently **not testable** against a real host by any shipped code; a future verifier reporting on these today must return `INDETERMINATE` (HBDC-REQ-053), never `COMPLIANT`.

No requirement is vague or untestable *in principle* — every one names a concrete mechanism or evidence class. The gap is implementation coverage, not requirement clarity.

## 16. Invariant Adjudication (CBD-1..8)

- **CBD-1** (agent cannot write protected authority state): supported by HBDC-REQ-007/013..021; live-mechanism coverage is partial per §8/§15 — the *requirement* holds, real-host *enforcement* of the ACL/group/ancestor/hard-link sub-cases is not yet implemented.
- **CBD-2** (admin exclusively controls protected authority state): supported by HBDC-REQ-009; no counter-evidence found.
- **CBD-3** (agent cannot redirect Protected Root): supported by HBDC-REQ-011/015..018; the override-path absence (HBDC-REQ-011) and symlink rejection (HBDC-REQ-018) are confirmed live in source; ACL/group coverage is the same partial-implementation gap as CBD-1.
- **CBD-4** (agent cannot redirect Model-A execution environment): supported by HBDC-REQ-025..039; zero live implementation exists yet (§9) — requirement sound, enforcement not yet built.
- **CBD-5** (identifier mutation confers no authority): confirmed live — `ensure_repository_identity` is agent-writable by design (HATP-REQ-051/063), and `deployment_binding_matches` requires the admin-owned `DeploymentBinding`, independently confirmed in source.
- **CBD-6** (conformance does not authorize provisioning/certification/activation): supported by HBDC-REQ-050/051; consistent with 149O.20A §45–§48's real-authorization gates, independently re-confirmed in §5 above.
- **CBD-7** (fail-closed on `INDETERMINATE`): supported by HBDC-REQ-052/053; closed vocabulary confirmed in contract text, no "unknown but allowed" branch found.
- **CBD-8** (HBDC-001 not mechanically gating HMIC until bound): independently confirmed true in §12 by direct source inspection, not merely by contract assertion.

All 8 invariants hold as stated by the contract text; none is contradicted by production source. CBD-1/CBD-3/CBD-4 note real-host enforcement gaps (§8/§9/§15), consistent throughout this document — not a new finding, the same one restated per-invariant for completeness.

## 17. Attack Matrix Reattack (21/21)

Each of HBDC-001 §21's 21 scenarios was independently reattacked (setup / authority target / defense / expected outcome / verdict), not merely checked for table-row existence:

| # | Attack | Independent verdict |
|---|---|---|
| 1 | Agent writes Protected Root directly | **Prevented** — confirmed no write path; admin-only per source (§7) |
| 2 | Agent redirects root via env/CLI override | **Prevented** — confirmed no override parameter on `.production()` (§8) |
| 3 | ACL/group effective-write bypass | **Requirement sound; enforcement not yet implemented** (§8 finding) |
| 4 | Writable-parent directory-entry replacement | **Requirement sound; only immediate-parent check implemented, not full ancestor chain** (§8 finding) |
| 5 | Symlink redirect | **Prevented** — `_reject_symlink` confirmed live in both modules (§8) |
| 6 | Hard-link alias into agent-writable location | **Requirement sound; no detection code exists** (§8 finding) |
| 7 | Auto-provisioning on missing root | **Prevented** — no `mkdir`/auto-create path found (§8) |
| 8 | Agent modifies production venv/site-packages | **Requirement sound; zero implementation exists** (§9 finding) |
| 9 | Agent replaces production Python executable | Same as #8 |
| 10 | Hostile `PYTHONPATH` | Same as #8; three concrete compliant designs named (§9) |
| 11 | CWD-shadowing | Same as #8; `sys.path[0]`/CWD explicitly named (§9) |
| 12 | Hostile sitecustomize/usercustomize | Same as #8 |
| 13 | Hostile `.pth` | Same as #8; import-executing `.pth` explicitly named (§9) |
| 14 | `sys.meta_path` hook injection | Same as #8; scoped to admin-controlled startup paths only (§9) |
| 15 | Fake/shadow `pcae` package | Same as #8; joint-compliance design explicitly disclosed, not an oversight (§9) |
| 16 | Wrong-repo/deployment cert reuse | **Prevented** — `deployment_binding_matches`/`WRONG_REPOSITORY`/`WRONG_DEPLOYMENT` confirmed live (§11) |
| 17 | Worktree/clone replay | **Prevented** — `.resolve(strict=True)` canonicalization confirmed to distinguish physical directories (§11) |
| 18 | Host migration cert reuse | **Prevented** — same canonicalization mechanism (§11) |
| 19 | Cross-path/host backup restore | **Prevented unless byte-identical restore to original path/host** — contract text explicit (§16 of contract) |
| 20 | Fake Git executable via PATH | **Requirement concrete (admin-controlled PATH); current `_run_git` uses bare `"git"`, PATH-resolved — deployment-level mitigation required, not a code defect** (§9 finding) |
| 21 | Contract-freeze claimed as real certification/activation | **Prevented** — HBDC-REQ-050/051 explicit; independently confirmed consistent with 149O.20A §45–§48 (§5) |

No attack row was found to have an unsound defense *claim*; several (3, 4, 6, 8–15, 20) have defenses that are correct in the contract's normative text but **not yet backed by shipped verification code** — consolidated as one recurring Non-Blocking finding class throughout this document (§8, §9, §15).

## 18. Additional Adversarial Attacks (Beyond the Frozen 21)

- **Fake Git executable through PATH** — covered above (§9, attack #20 discussion); maps to existing row 20, no new gap.
- **Writable Python launcher** — maps to HBDC-REQ-036 (existing coverage), no new gap.
- **Writable parent of venv** — maps to HBDC-REQ-026 (production venv admin-owned-only) combined with the same ancestor-chain principle as HBDC-REQ-017; the contract does not separately restate ancestor-chain protection for the *venv's* parent the way it does for Protected Root's parent (HBDC-REQ-017 is scoped to Protected Root, §11, not explicitly extended to §13's venv). **Finding (Non-Blocking, Observation)**: HBDC-REQ-026 requires the venv be "owned and writable only by the admin principal" but does not explicitly state the writable-parent-replacement channel is closed for the venv's own directory the way HBDC-REQ-017 explicitly does for Protected Root. A future verifier should apply the same ancestor-chain-protection principle to the venv path by analogy, but the contract text does not spell this out as its own numbered requirement. Worth a narrow future contract clarification, not blocking (the venv is itself inside the environment-lock's admin-provisioned/agent-unwritable boundary per HBDC-REQ-025, so the gap is narrow and largely covered transitively).
- **Symlinked editable-install target** — maps to HBDC-REQ-035 (editable-install link metadata admin-controlled) combined with HBDC-REQ-018's symlink fail-closed principle; HBDC-REQ-018 is textually scoped to "Protected Root ... and no authority-bearing path beneath it" (§11) — the editable-install metadata target under §13 is a distinct scope. Same Observation as above: analogous coverage exists via HBDC-REQ-035's "admin-controlled and agent-unwritable" language, but explicit symlink-fail-closed language is not repeated for §13. Non-Blocking Observation, not Blocking — no bypass exists because HBDC-REQ-035 already requires admin-control of the metadata regardless of symlink status.
- **Writable editable metadata** — directly covered, HBDC-REQ-035.
- **Hostile cwd** — directly covered, HBDC-REQ-033.
- **User-site shadowing** — directly covered, HBDC-REQ-029.
- **`.pth` import-code execution** — directly covered, HBDC-REQ-031 (explicitly names import-executing `.pth` files).
- **HBDC semantic drift while unbound** — directly covered and independently re-confirmed, §12.

No additional attack surfaced a Blocking finding. Two Non-Blocking Observations (venv/editable-install ancestor-chain and symlink coverage stated only for Protected Root, not explicitly restated for §13 paths) are recorded for a future narrow contract clarification, not for this phase to repair.

## 19. Threat-Model Limit and Hardware Boundary

HBDC-001 §18 explicitly disclaims resistance to a fully compromised OS root/admin account and explicitly disclaims replacing HATP-001's hardware-signer assurances. Both disclaimers are independently confirmed consistent with 149O.20A §17/§66's own scoping (root/Administrator-level compromise out of scope; hardware signer trust is HATP-001's separate concern). No overclaim found in either direction.

## 20. Status-Claim Discipline

HBDC-REQ-054/055 (§25) explicitly reserve "CLASS-B DEPLOYMENT VERIFIED" for a future independent verification phase confirming conformance under an *actually-provisioned* topology, and explicitly state contract conformance never equals "HATP DEPLOYMENT READY"/"HATP PRODUCTION READY"/"ROLLBACK EXECUTION READY." This phase (149O.20C) verifies the **contract text**, not a provisioned topology — consistent with §29's verdict block ("PENDING INDEPENDENT VERIFICATION" resolving to a contract-level verdict here, real-topology verification remaining for a future phase against an actually-provisioned host, per HBDC-001 §25's own discipline).

## 21. Findings Summary

**Blocking:** None. All four load-bearing questions (§22 below) resolve favorably; no attack scenario, traceability check, or invariant adjudication produced a Blocking result.

**Non-Blocking:**
1. Effective ACL/group-membership write-access testing (HBDC-REQ-015/016), full ancestor-chain protection beyond the immediate parent (HBDC-REQ-017), and hard-link-alias detection (HBDC-REQ-019) have no corresponding implementation in `src/pcae/**` today — the contract's normative text is sound and concrete; real-host verification of these specific sub-requirements is currently impossible and must report `INDETERMINATE` (HBDC-REQ-053), not `COMPLIANT`, until a future implementation phase builds the missing checks.
2. The entire Model-A Python execution-environment lock (HBDC-REQ-025..039) has zero corresponding implementation in `src/pcae/**` today — same class of gap as above, expected given HBDC-001 is contract-freeze-only, but recorded so a future provisioning-verification phase does not assume tooling exists that does not.
3. `derive_implementation_commit`'s `_run_git()` resolves `"git"` via bare PATH lookup with no absolute-path pinning or resolved-executable validation in code; HBDC-REQ-038's chosen mitigation (admin-controlled `PATH`/pinned executable in the *deployment's* launch environment) is a sound, correctly-scoped requirement, but is worth flagging for a future implementation phase to consider whether an additional code-level defense (e.g. validating the resolved `git` executable's realpath) is also warranted — not required by HBDC-001 v1.0 as written, not a defect in it.

**Observations:**
1. HBDC-REQ-017's explicit ancestor-chain-protection and HBDC-REQ-018's explicit symlink-fail-closed language are both textually scoped to Protected Root (§11) and are not verbatim-restated for the §13 environment-lock paths (venv, editable-install metadata); coverage exists transitively via HBDC-REQ-025/035's "admin-controlled, agent-unwritable" language, so no bypass exists, but a future contract revision could make the analogy explicit.
2. The governing prompt's "current HMIC bound-contract set: 8 / target 9" framing conflates two distinct countable sets in the corpus (total frozen-contract corpus vs. HMIC's own 4-entry `contract_versions` field); this document (§12) records the precise distinction so a future HMIC v1.2 amendment phase does not misreport its own resulting count.

**Deferred:** The two pre-existing 149O.19.5E.2/E.3 fixed-commit `docs/contracts` test failures remain deferred per repository convention (§14); not evaluated as part of this phase's contract-verification scope.

## 22. The Four Load-Bearing Questions — Independent Answers

1. **Can the ordinary PCAE agent acquire effective write/replacement authority over protected HATP/HMIC state?** **NO** — confirmed by direct source inspection (§7, §8): no override path to Protected Root exists, no application-level admin mechanism exists, symlink redirection fails closed where implemented, and the requirement text for ACL/group/ancestor/hard-link coverage is sound even though its live-host enforcement is not yet built (a coverage gap, not a granted authority).
2. **Can the ordinary agent redirect PCAE authority-module execution away from the certified canonical repository through its Python/process environment?** **Contract text: NO, by design, once §13 is provisioned. Today: no verifier exists to confirm this on any real host**, because §13's environment lock has zero shipped implementation (§9). This is answered honestly by the contract's own "PENDING INDEPENDENT VERIFICATION" / "NOT YET IMPLEMENTED" framing, not overclaimed.
3. **Does HBDC's Model-A/HMIC-REQ-063 Option-C treatment actually close the intended threat model without overclaiming runtime provenance?** **YES** — independently re-derived in §5/§10; the conditional (locked-environment-dependent) framing is correct, and HBDC-REQ-041's non-overclaim is independently confirmed consistent with HMIC-REQ-063's own text.
4. **Can HBDC's deployment semantics be changed after certification unless HBDC itself is incorporated into a protected contract identity?** **YES, currently** — independently confirmed empirically in §12 (HBDC-001's bytes are outside both `contract_versions` and `implementation_scope_digest`). This is the expected, disclosed, correctly-sequenced state under Option A pending a future HMIC v1.2 amendment — not a currently-exploitable gap, because no real certification exists yet to be undermined by it (§12 conclusion).

No YES to question 1, 2, or 4 lacks a frozen defense: question 1 is NO; question 2's residual gap is honestly disclosed as not-yet-implemented rather than falsely claimed solved; question 4's YES is the intentionally-sequenced, disclosed prerequisite state (HBDC-REQ-047..049), not an unguarded gap, since real deployment reliance remains independently blocked regardless (§12).

## 23. Contract Verdict

```
HBDC-001 v1.0:
INDEPENDENTLY VERIFIED WITH NON-BLOCKING FINDINGS
— HATP CLASS-B DEPLOYMENT CONTRACT CONFORMS

CLASS-B: CONTRACT VERIFIED — NOT PROVISIONED
HATP: NOT READY
```

## 24. HBDC Self-Binding Verdict

```
HBDC TRUST/BINDING DISPOSITION: INDEPENDENTLY VERIFIED
— HBDC-001 MUST ENTER HMIC'S PROTECTED BOUND-CONTRACT IDENTITY
  BEFORE REAL DEPLOYMENT TRUST MAY RELY ON HBDC

Current state: HBDC NOT YET HMIC-BOUND (empirically confirmed, §12)
Therefore: real Class-B provisioning remains blocked by the HMIC
contract-evolution prerequisite (HBDC-REQ-048).
```

This is not treated as an HBDC-001 defect; it is an intentionally sequenced, disclosed prerequisite, fail-closed by construction (§12).

## 25. HMIC-REQ-063 Verdict

```
OPTION C VERIFIED
```

Model-A deployment may accept HMIC-REQ-063 as a declared residual only after HBDC-001's §13 environment-lock conformance is independently established on a real, provisioned host — which has not occurred and is not claimed to have occurred. Runtime-source cryptographic attestation is not claimed solved.

## 26. Regression and Governance Checks

See §27 for exact suite output. `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, all 8 existing bound contracts, and all `src/pcae/**`/`scripts/**` files were confirmed byte-unchanged throughout this phase (§27 `git diff --stat` evidence).

## 27. Next Phase

If HBDC-001 verifies (it does, §23) **and** Option A verifies (it does, §24): **do not recommend Class-B provisioning next.** Strong candidate next phase: **149O.20D — HMIC v1.2 HBDC Bound-Contract Identity Evolution** — scope: contract evolution only (HMIC-001 v1.1 → v1.2, add HBDC-001 v1.0 to `contract_versions`, define replay/version consequences, preserve existing 24-file `implementation_scope_digest` scope unless direct analysis requires otherwise, no production changes, no provisioning, no certification, no activation). Required sequence thereafter: independent HMIC v1.2 contract verification → bounded production bound-contract-set alignment if required → independent implementation verification → only then may Class-B provisioning planning be considered. This phase does not authorize any step of that sequence; it only independently confirms the sequence is the correct one.

## 28. Explicit Confirmations

- HBDC-001 was independently verified from primary sources (contract text, architecture document, and production source directly read — §4), not from the 149O.20B phase-report summary.
- All 55 requirements were adjudicated (§6, §15).
- All 8 invariants were adjudicated (§16).
- All 21 frozen deployment attacks were independently re-attacked (§17).
- Effective write authority was evaluated beyond POSIX mode bits, including group/ACL and parent-directory replacement (§8) — findings recorded where live enforcement does not yet exist.
- The Model-A Python environment lock was independently attacked across PYTHONPATH, user site, `.pth`, customization modules, import hooks, CWD, editable-install metadata, interpreter/venv, launcher/service environment, and authority subprocess (Git) resolution (§9).
- HMIC-REQ-063 was not falsely declared solved (§10, §25).
- HBDC-001 is not currently HMIC-bound (§12, empirically confirmed).
- Because Option A independently verifies, HBDC-001 must join HMIC's bound-contract identity before real deployment trust may rely on HBDC-001 (§24).
- No real OS principal or Protected Root was created. No real Python environment ownership/permission change was performed. No real HMIC certification/binding/revocation state was created. No Cutover Record or activation marker was created/modified. No real `HATP_MANDATORY` activation occurred. No Permission Broker behavior changed. POL-005 remained unchanged. No COMP-002 capability was implemented. Runtime remained Observed / observe / unavailable. HATP production remains NOT READY.
