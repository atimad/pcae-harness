# Phase 149O.20L.7O.2J — HATP Class-B Real Host Protected Root Provisioning Authorization

## 0. Phase Identity and Type

**Phase:** 149O.20L.7O.2J
**Type:** AUTHORIZATION/PLANNING ONLY. No SSH to hac-dell (read or write). No
`mkdir`/`chown`/`chmod`/`setfacl`/`install`/system change of any kind on
hac-dell. No Protected Root creation. No credential enrollment. No
certification. No DeploymentBinding. No HATP activation. This phase's only
artifacts are this document, its companion phase-local evidence test file,
and ordinary task/lifecycle/report/PROJECT_STATUS.md/CHANGELOG.md
bookkeeping.
**Phase-entry commit:** `8871b4bf34009b3db29a2d4f83cf78f3e93d2c6a`
**Basis:** `docs/PHASE_149O_20L_7O_2I_HATP_REMAINING_PREREQUISITE_STATE_AND_SEQUENCING_RECONCILIATION.md`
(read directly, not from summary); `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
(HBDC-001 v1.2, read directly); `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
(HMIC-001 v1.6, read directly); `src/pcae/core/hatp_bootstrap.py` and
`src/pcae/core/hatp_mandatory_cutover.py` (read directly); and the full,
primary chronological chain of real (unmocked) hac-dell host-evidence
phases 149O.20L.7B through 149O.20L.7O.2B.1 (each read directly, not
inherited from any intervening summary — see §1).

## 1. Central Finding, Stated First

**The premise this phase was asked to authorize — that Protected Root
provisioning on hac-dell is a still-open, unperformed real-effect action —
is factually false, as demonstrated by primary evidence already committed
to this repository.**

The governing phase prompt (based on 149O.20L.7O.2I §7/§8/§13/§16/§18)
states Protected Root existence on hac-dell is "ABSENT (no host-side
provisioning phase has run)" and lists it as the DAG's first unmet node.
149O.20L.7O.2I reached that conclusion by citing "149O.20L.3/.4" as "the
most recent dated calls in this work-stream" for real-host state. That
citation is itself wrong: 149O.20L.3/.4 are dated 2026-08-14 and concern
*readiness-contract wiring*, not a real hac-dell inspection. The repository
contains **five** later real, unmocked, read-only hac-dell inspection
phases that 149O.20L.7O.2I did not incorporate:

| Phase | Date | Finding on Protected Root (`/etc/pcae/hatp/trust-store`) |
|---|---|---|
| 149O.20L.7E | 2026-08-15 | `root:pcae 750`, ACL `user::rwx group::r-x other::---` (no extra grants), not a symlink, ancestors `/etc/pcae/hatp`, `/etc/pcae`, `/etc` all `root:root 755` |
| 149O.20L.7N.5 | 2026-08-18 | `root:pcae 750`, empty, unchanged in shape; confirms 7N.4's source-only redeployment never touched this path |
| 149O.20L.7O.2A.5 | 2026-08-18 | Protected Root path/owner/mode/ACL unchanged from the pre-established state; explicitly logged as "DeploymentBinding / Protected Root: absent/unchanged" (absent refers to binding *content*, not the directory) |
| 149O.20L.7O.2B | 2026-08-18 | Retained as the baseline 2B.1 below independently re-derives |
| 149O.20L.7O.2B.1 | 2026-08-18 (one day before 2I) | Independently re-ran `stat`/`getfacl`/`find` against `/etc/pcae/hatp/trust-store`: `root:pcae 750`, ACL confirmed, not a symlink, full `/etc/pcae` tree to depth 3 confirmed safe; ran `verify_class_b_deployment_conformance` live, twice, deterministically: **34 total checks, 33 `satisfied=True`, sole failing check `HBDC-REQ-042` (`no_active_deployment_binding_matches_repository_and_root`)** |

No phase between 7O.2B.1 (2026-08-18) and 7O.2I (2026-08-19) touched
hac-dell (7O.2I itself performed no SSH, by its own §7). No teardown,
reset, or redeployment of `/etc/pcae/hatp/trust-store` is recorded
anywhere in this chain — 7N.5 and 7O.2A.5 each explicitly confirm the
source-only redeployment and RepositoryIdentity-write-path work of their
own phases never touched Protected Root. There is therefore **no
evidentiary gap and no elapsed real-effect event** between 7O.2B.1's
measurement and today that could explain 7O.2I's "ABSENT" claim; it is a
reconciliation error in 7O.2I, not a stale-but-then-true fact.

Independently re-read against HBDC-001 (§10-11): `root:pcae` ownership
matches HBDC-REQ-013 (admin-owned; `codex`/root is the admin principal,
`pcae` is the agent principal per 7E Action 2 — group ownership by the
agent's own group is a read-traversal grant, not a write grant, addressed
next); mode `750` (`0o750 & 0o022 == 0`) matches HBDC-REQ-014 exactly,
including the contract's own "recommended concrete mode" language; ACL
`user::rwx group::r-x other::---` grants the `pcae` group read+execute
only, never write, satisfying HBDC-REQ-015/016 (group-derived effective
write access is absent — `r-x` cannot write); ancestors `/etc/pcae/hatp`,
`/etc/pcae`, `/etc` all `root:root 755` (root-owned, agent has no write
anywhere in the ancestor chain) satisfies HBDC-REQ-017; "not a symlink"
(explicitly checked, repeated across 7E/7O.2B.1) satisfies HBDC-REQ-018.
**Protected Root, as it exists today on hac-dell, independently and
currently satisfies HBDC-REQ-011 through HBDC-REQ-018 in full.**

This finding is **Blocking** against treating "authorize Protected Root
creation" as this phase's deliverable (§40 of the governing prompt: "Do
not force a provisioning phase merely because 2I predicted it"). It is
**not** blocking against this phase's other work: defining Protected
Root's exact contractual specification (needed regardless, as a durable
verification baseline) and correcting the DAG so a future phase does not
repeat 2I's error.

## 2. What This Phase Therefore Authorizes

Nothing is authorized for **creation**. Instead, this phase freezes a
narrow **read-only re-verification envelope** — the exact precondition
check a future real-effect phase (certification, hardware-credential
enrollment, or DeploymentBinding creation, each of which legitimately
still requires host provisioning/verification work) MUST run against
Protected Root, immediately before relying on it, to guard against
staleness/TOCTOU between this phase's evidence and that future phase's
execution. This mirrors HBDC-REQ-021's own fail-closed requirement and
the phase prompt's own §27 TOCTOU instruction. See §7 below.

## 3. Primary Contract Reconstruction (§5 of Governing Prompt)

Read directly, not from prose summary:

- **HBDC-001 v1.2** (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`):
  §9 (admin/agent authority split, HBDC-REQ-004/006/007/009/010), §10-11
  (Protected Root definition/resolution/ownership/permissions/path-safety,
  HBDC-REQ-011..021), §12 (Model-A deployment/canonical root), §19
  (security invariants CBD-1..CBD-N), §21 (attack matrix rows 1-7), §31
  (DeploymentBinding producer contract, HBDC-REQ-056..068).
- **HMIC-001 v1.6** (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`):
  frozen 36-member source identity / 7-member `contract_versions`
  unchanged by this phase (verified §10 below).
- **`src/pcae/core/hatp_bootstrap.py`**: `_default_production_trust_root`
  (lines 233-257), `_LINUX_FIXED_TRUST_ROOT`/`_MACOS_FIXED_TRUST_ROOT`
  constants (lines 229-230), `HATPTrustStore.production()` (lines 536-541).
- **`src/pcae/core/hatp_mandatory_cutover.py`**: the eight-term readiness
  conjunction (`_assess_hatp_mandatory_activation_readiness_at_root`),
  specifically `class_b_protected_storage_available` (lines ~805-813) and
  `protected_activation_authority_mechanism_available` (lines ~890-936).
- **`src/pcae/core/hatp_class_b_conformance.py`**: `_check_deployment_identity`
  (the exact branch producing `HBDC-REQ-042`'s current failing reason).

No requirement text below is invented; each is cited to its `HBDC-REQ-###`
identifier per §3 above.

## 4. Host Identity — Classification (§4 of Governing Prompt)

| Item | Value | Classification |
|---|---|---|
| alias | `hac-dell` | VERIFIED HISTORICAL / STABLE EVIDENCE (repeatedly re-confirmed through 2026-08-18) |
| machine-id | `54ff22ce400b475aa0d55cb68f4a3334` | VERIFIED HISTORICAL / STABLE EVIDENCE — re-confirmed exact-match at 7E (08-15); **MUST BE RECHECKED IMMEDIATELY BEFORE any future mutation** per this phase's own §7 envelope |
| hostname | `atila-Latitude-E5470` | VERIFIED HISTORICAL / STABLE EVIDENCE — same re-check rule |
| OS | Ubuntu 24.04.3 LTS (Noble Numbat) | VERIFIED HISTORICAL / STABLE EVIDENCE |
| architecture | amd64 / x86_64 (`uname -m`) | VERIFIED HISTORICAL / STABLE EVIDENCE |
| administrative identity | `codex` (root/sudo-capable OS principal) | VERIFIED HISTORICAL / STABLE EVIDENCE |
| deployment/execution identity | `pcae` — `uid=1004(pcae) gid=1004(pcae)`, no supplementary groups, not in `sudo`, shell `/usr/sbin/nologin`, home `/home/pcae` | VERIFIED HISTORICAL / STABLE EVIDENCE (7E Action 2, unchanged through 7O.2B.1) — **already exists; no user-creation action is needed** (§9 below) |
| canonical source root | `/opt/pcae/runtime/src` | VERIFIED HISTORICAL / STABLE EVIDENCE — HEAD `28bf137b...`, detached, clean (7O.2B.1) |
| RepositoryIdentity | `0107866f-af7c-40b4-8317-74e71acb05ca` | VERIFIED HISTORICAL / STABLE EVIDENCE — present and independently validated (7O.2B.1 §9); creation confers no authority (HATP-REQ-048) |
| Protected Root | `/etc/pcae/hatp/trust-store` | VERIFIED HISTORICAL / STABLE EVIDENCE — **already exists, already compliant** (§1); freshness re-check still required per §7 before any future phase relies on it for a real-effect act |

This phase performed **no SSH, no live remote inspection** (§34 of the
governing prompt honored). All rows above are reconstructed strictly from
already-committed primary evidence in this repository, dated as cited.

## 5. Define the Protected Root (§6 of Governing Prompt)

Exact canonical path, per `_default_production_trust_root()`
(`src/pcae/core/hatp_bootstrap.py:233-257`), a pure deterministic
platform-keyed constant lookup with no override surface:

- Linux (hac-dell's actual platform): **`/etc/pcae/hatp/trust-store`**
  (`_LINUX_FIXED_TRUST_ROOT`, line 230).
- macOS (not applicable to hac-dell, recorded for completeness):
  `/Library/Application Support/PCAE/HATP/trust-store`.

This is not derived, inferred, or invented by this phase — it is read
directly from the sole production resolution function, matches the path
independently measured by every real-host phase 7E through 7O.2B.1, and
is not a "Blocking planning gap": the path is normatively fixed by
source, exactly as HBDC-REQ-011 requires.

## 6. Parent / Ancestor Requirements (§7 of Governing Prompt)

| Path | Expected owner | Group | Mode | ACL | Symlink | Agent (`pcae`) write? | Admin (`codex`/root) write? | Mount relationship |
|---|---|---|---|---|---|---|---|---|
| `/etc` | `root:root` | — | `755` | none | no | No | Yes (root) | host root filesystem |
| `/etc/pcae` | `root:root` | — | `755` | none | no | No | Yes (root) | same |
| `/etc/pcae/hatp` | `root:root` | — | `755` | none | no | No | Yes (root) | same |
| `/etc/pcae/hatp/trust-store` (Protected Root itself) | `root:pcae` | `pcae` | `750` | `user::rwx group::r-x other::---`, no extra grants | no | **No** (group has `r-x`, not `w`) | Yes (root) | same |

All rows independently confirmed at 7O.2B.1 (2026-08-18, "Full `/etc/pcae`
tree to depth 3"). No replacement/rename is possible by the agent
principal at any level (ancestors are entirely root-owned, `755`, no
group/other write). A safe leaf sitting beneath these ancestors is
therefore not resting on an unsafe parent — HBDC-REQ-017/020 are jointly
satisfied end-to-end, not merely at the leaf.

## 7. The Actual Deliverable — Frozen Re-Verification Envelope

Because Protected Root already exists in the exact required state, the
only future real-effect action this phase can responsibly authorize is a
**read-only, fail-closed re-verification precondition check**, to be run
by whichever future real-effect phase (certification, HHCE/FIDO2
enrollment, HPSE Principal/Signer enrollment, or DeploymentBinding
creation — see §8) is the actual next node, immediately before that
phase relies on Protected Root's state. This is not itself a mutation and
requires no new host action.

### 7.1 Command Envelope (frozen, not executed by this phase)

All commands below are **READ-ONLY PRECHECK**. No command in this
envelope is a mutation; none is authorized to run by this phase; each
future phase that uses it must run it itself, fresh, at its own entry.

```
sudo -n stat -c "%U:%G %a %F" /etc/pcae/hatp/trust-store
sudo -n getfacl -p /etc/pcae/hatp/trust-store
sudo -n find /etc/pcae -maxdepth 3 -printf "%p %u:%g %m %y\n"
sudo -n find /etc/pcae/hatp/trust-store -type f
cat /etc/machine-id
hostname
cat /etc/os-release
uname -m
sudo -n git -C /opt/pcae/runtime/src rev-parse HEAD
id pcae
```

No `getent passwd pcae` mutation risk; no arbitrary shell; no open-ended
`sudo sh -c "..."`. Every command above is a fixed, fully-specified,
individually-auditable invocation.

### 7.2 Pass/Fail Classification of the Precheck

- **PASS** (future phase may proceed to its own real-effect act, subject
  to that act's own separate authorization): owner `root:pcae`, mode
  `750`, ACL exactly `user::rwx group::r-x other::---` with no additional
  entries, not a symlink, all three named ancestors `root:root 755`,
  `machine-id`/`hostname`/OS/arch/source-SHA all exact-match §4's table.
- **FAIL — STOP, OPERATOR REVIEW REQUIRED** (future phase MUST NOT
  proceed to any mutation): any mismatch in owner, mode, ACL, symlink
  status, ancestor safety, or host identity; `stat`/`getfacl`/`find`
  raising an unexpected error; Protected Root missing entirely (would
  itself indicate an unexplained regression from today's verified
  state, not a normal "not yet provisioned" condition — treat as
  Blocking, not as "proceed to create").
- This phase deliberately does **not** authorize a "create if absent"
  branch. Given §1's evidence, an absence at future-phase time would be
  an anomaly (something removed it), not the expected starting state —
  fail-closed per HBDC-REQ-021, no silent auto-provisioning path.

### 7.3 Existing-Path Matrix (§12 of Governing Prompt)

| Observed state | Classification |
|---|---|
| A. Path does not exist | BLOCK — OPERATOR REVIEW REQUIRED (anomalous; contradicts §1's verified baseline) |
| B. Exists, compliant (current known state) | NO-OP / VERIFY — proceed to the future phase's own separately-authorized act |
| C. Exists, wrong owner | BLOCK — OPERATOR REVIEW REQUIRED |
| D. Exists, wrong mode | BLOCK — OPERATOR REVIEW REQUIRED |
| E. Has unexpected ACL entries | BLOCK — OPERATOR REVIEW REQUIRED |
| F. Is a symlink | BLOCK — OPERATOR REVIEW REQUIRED (fail-closed, HBDC-REQ-018) |
| G. Is a file, not a directory | BLOCK — OPERATOR REVIEW REQUIRED |
| H. Contains unexpected contents (anything other than an empty directory or a legitimately-written `registry.json`/binding/certification file created by a properly-authorized later phase) | BLOCK — OPERATOR REVIEW REQUIRED |
| I. Sits beneath an unsafe ancestor | BLOCK — OPERATOR REVIEW REQUIRED |

No automatic `chmod`/`chown`/ACL repair of existing content is authorized
by this envelope under any row. Creation-vs-repair distinction (§13 of
governing prompt) is moot given §1: there is no creation action to
authorize, and repair of unknown drifted state is explicitly out of
scope — any drift is BLOCK, full stop, matching the governing prompt's
"prefer fail-closed behavior when current state does not match the
expected creation model."

## 8. Filesystem / Mount, Sudo, and Deployment-Identity (§§14, 16, 17)

- **Filesystem/mount:** HBDC-001 does not normatively constrain
  filesystem type, mount options, or network/overlay/bind-mount
  properties beyond the permission/ownership/ACL/symlink requirements
  already covered (§6). No filesystem-type precheck is added beyond what
  §7.1 already captures (owner/mode/ACL/symlink), because no contract
  text requires more. This phase does not overclaim guarantees the
  contract does not make.
- **Sudo/admin authority:** every command in §7.1 either needs no
  elevation (`hostname`, `uname`, `cat /etc/machine-id`,
  `cat /etc/os-release`, `id pcae`) or needs only `sudo -n` (non-
  interactive, already the established pattern in every real-host phase
  since 7A) for root-owned-path read access. No new sudo scope is
  requested; `codex`'s existing broad sudo capability does not enlarge
  what this authorization covers (per the governing prompt's own §16 —
  PCAE authorization remains narrower than OS capability).
- **Deployment identity (`pcae` user):** already exists, already
  verified (§4). No user-creation action is authorized or needed by any
  future Protected-Root-adjacent phase. A separate user-provisioning
  phase is not required — that prerequisite is already closed.

## 9. Protected Root Content Boundary (§§18-20 of Governing Prompt)

Protected Root currently contains **zero files** (confirmed 7N.5,
7O.2A.5, 7O.2B.1). This phase reaffirms the boundary the governing
prompt states: Protected Root *topology* provisioning (already done, §1)
is strictly distinct from populating it with `registry.json`,
`CertificationRecord`/`CertificationBinding`, `DeploymentBinding`,
hardware-credential records, Principal/Signer state, or any
environment-lock/activation marker. None of those exist; none is
authorized by this phase; none is authorized by the historical Protected
Root creation this phase examined either (that act, whenever it occurred
under the 149O.20L.6 Boundary-P election, created directory topology
only — content remains empty to this day, independently re-confirmed
three times since).

## 10. Corrected Prerequisite DAG (Repairs 149O.20L.7O.2I §16/§18)

```
RepositoryIdentity/canonical root (existing, verified)
        |
        v
Protected Root provisioning on hac-dell   <-- ALREADY DONE, VERIFIED (this phase, §1)
        |
        +--> class_b_protected_storage_available   <-- TRUE on hac-dell (topology exists)
        |--> protected_activation_authority_mechanism_available  <-- TRUE on hac-dell (mode 750 excludes group/other write)
        |
        v
Class-B host provisioning / topology + environment-lock  <-- ALREADY DONE (7E Actions 1-5, all present; 7O.2B.1: 33/34 checks pass)
        |
        v
class_b_deployment_conformance_satisfies_readiness  <-- STILL NON_COMPLIANT, sole residual HBDC-REQ-042
                                                          (no_active_deployment_binding_matches_repository_and_root)
        |
        v
Readiness ready=True  <-- NOT YET (row 8 unmet; rows 4/7 now TRUE, contra 2I's table)

Hardware credential enrollment (HHCE)  <-- NOT DONE, independent of readiness
        |
        v
Principal/Signer enrollment (HPSE)  <-- NOT DONE
        |
        v
DeploymentBinding  <-- NOT DONE; this is what would flip HBDC-REQ-042/row 8

HMIC CertificationRecord creation  <-- NOT DONE, independent branch, depends only on
        |                              already-verified source identity
        v
Activation gate: ready=True AND valid CertificationRecord AND human authorization AND no revocation
```

**The first unmet node with no unmet prerequisite of its own is no longer
Protected Root provisioning — it is already satisfied.** Two independent
candidates now occupy that position: (a) HMIC CertificationRecord
creation (depends only on source identity, already verified — no upstream
gap), and (b) hardware-credential (FIDO2) enrollment, the first link in
the enrollment→Signer→DeploymentBinding chain that would close
HBDC-REQ-042. Selecting between them, and authoring either one's own
frozen authorization envelope, is **out of scope for this phase**
(2J is Protected-Root-scoped only, per its own charter) and is deferred
to the next phase (§13).

## 11. Human Authorization / Freshness / Source Binding (§§30-33)

Because this phase authorizes **no mutation**, no new CHGR election is
required for 2J itself (mirrors 149O.20L.6's own posture: election is
required only at the actual real-effect boundary). The §7 re-verification
envelope this phase freezes is bound to:

- **Host identity:** exact match on `machine-id`
  `54ff22ce400b475aa0d55cb68f4a3334`, hostname `atila-Latitude-E5470`,
  Ubuntu 24.04.3, x86_64. Any mismatch invalidates the envelope —
  re-evaluation required, not silent proceed.
- **Source revision:** phase-entry commit `8871b4bf...` of this repo;
  HMIC-001 v1.6 (36/7, unchanged, §12 below); HBDC-001 v1.2 (unchanged).
  A future phase running under a materially different commit/contract
  version must re-derive §7 from primary source again, not reuse this
  document's tables uncritically.
- **Target path:** `/etc/pcae/hatp/trust-store` exactly, no substitution.
- **Single-use / expiration:** the §7 envelope is a **precheck**, re-run
  fresh at each future phase's own entry (§7.2) — it is not a one-time
  credential and does not itself expire, but its *result* is valid only
  for the invocation that produced it (no caching across phases, per the
  TOCTOU note below).
- **TOCTOU (§27):** between a future phase's own precheck and any
  mutation it performs elsewhere (e.g. writing a `DeploymentBinding`),
  it MUST re-stat Protected Root's mode/owner/ACL/symlink status
  immediately before that mutation, not rely on this document's or its
  own earlier-in-phase precheck's cached result. No transactional
  filesystem guarantee is claimed.

## 12. Regression / Unchanged-State Proof (§38 of Governing Prompt)

- **HMIC-001:** v1.6, unchanged. Frozen source identity: 27
  `src/pcae/`-relative + 9 repository-root-relative = **36 members**,
  independently re-counted from `_FROZEN_SRC_PCAE_RELATIVE_FILES`/
  `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` this phase
  (`src/pcae/core/hatp_mandatory_certification.py`). Contract-identity
  `contract_versions` set: 7 members, unchanged.
- **HBDC-001:** v1.2, unchanged (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
  header re-read this phase).
- **Class-B verifier / readiness / runtime:** no `src/pcae/**` file was
  modified by this phase (verified by the phase-local test suite's
  `git diff --name-only <entry-commit> -- src docs/contracts` check,
  mirroring 149O.20L.7O.2I's own pattern).
- **No remote state mutation:** no SSH connection was opened to hac-dell
  by this phase, read-only or otherwise (§34 honored).
- **Lifecycle/reporting:** unaffected; ordinary task/phase-completion
  bookkeeping only.

Fast Green: run and cited honestly in the final report (§14 below), not
placeholder-valued.

## 13. No-Go (§39 of Governing Prompt) — All Honored, None Performed

This phase did not: SSH-mutate hac-dell; `mkdir` Protected Root (it
already exists); `chown`; `chmod`; set or remove ACL; create the `pcae`
user (it already exists); create a group; install packages; alter
sudoers; create an HMIC certification; create trust records; provision
FIDO2/PIV; create a `HardwareCredentialRecord`; enroll a Principal;
enroll a Signer; create a `DeploymentBinding`; change readiness; activate
HATP; change the Permission Broker; change runtime capability; touch
Stream B.

## 14. Findings

**Finding 2J-1 (repairs 149O.20L.7O.2I, non-blocking to this phase's own
completion, Blocking against 2I's DAG record as currently written):**
149O.20L.7O.2I §7/§8/§13 row 4/row 7/§16/§18 incorrectly states Protected
Root is "ABSENT" on hac-dell and is the DAG's first unmet node. Primary
evidence already in this repository (149O.20L.7E, 149O.20L.7N.5,
149O.20L.7O.2A.5, 149O.20L.7O.2B.1 — all dated 2026-08-15 through
2026-08-18, all real/unmocked/read-only) shows Protected Root already
exists on hac-dell and already satisfies HBDC-REQ-011 through
HBDC-REQ-018 in full, with `class_b_deployment_conformance_satisfies_readiness`'s
sole residual failure being `HBDC-REQ-042`
(`no_active_deployment_binding_matches_repository_and_root`), not
anything Protected-Root-related. 149O.20L.7O.2I's own citation of
"149O.20L.3/.4" as "the most recent dated calls" for real-host state is
the root cause: those phases (2026-08-14) predate every one of the five
real-host phases above and are not host-inspection phases at all. See §1
of this document for the full reconstruction. **Disposition: this
phase's own document (§1, §10) constitutes the repair; 149O.20L.7O.2I's
own text is not edited in place (out of this phase's allowed-file scope
and not requested) — the correction is recorded here and should be
carried forward by PROJECT_STATUS.md and the next phase (§16).**

No other Blocking finding was found: the exact Protected Root path is
normatively fixed and derivable (§5); ownership/mode/ACL semantics are
unambiguous and independently confirmed compliant (§1, §6); the `pcae`
deployment identity already exists, is not a missing prerequisite (§4,
§8); rollback is moot because no creation action is authorized (§7); real
host identity is bound safely from primary evidence (§4, §11); the
dependency graph does not require anything to precede what is already
provisioned.

## 15. Verdict

**F — PREMISE FALSIFIED BY PRIMARY EVIDENCE: PROTECTED ROOT ALREADY
PROVISIONED AND VERIFIED HBDC-REQ-011..018 COMPLIANT ON HAC-DELL. NO
CREATION AUTHORIZATION IS ISSUED OR REQUIRED. A NARROW READ-ONLY
RE-VERIFICATION ENVELOPE (§7) IS FROZEN FOR ANY FUTURE PHASE THAT RELIES
ON PROTECTED ROOT'S STATE. 149O.20L.7O.2I'S PREREQUISITE DAG IS CORRECTED
(§10); THE TRUE FIRST UNMET NODE IS HMIC CERTIFICATION CREATION OR
HARDWARE-CREDENTIAL (FIDO2) ENROLLMENT — SELECTING BETWEEN THEM IS
DEFERRED TO THE NEXT PHASE, NOT DECIDED HERE.**

Expected state, confirmed:

```
HATP PROTECTED ROOT PROVISIONING: ALREADY COMPLETE (VERIFIED, NOT PERFORMED BY THIS PHASE)
REAL HOST MUTATION (THIS PHASE): NOT PERFORMED
HMIC: v1.6 / 36 / 7 -- unchanged
HMIC certification: ABSENT
Trust enrollment: ABSENT
DeploymentBinding: ABSENT
HATP: NOT READY / NOT ACTIVE
Runtime: Observed / observe / unavailable
```

## 16. Recommended Next Phase

**149O.20L.7O.2K — HATP Prerequisite DAG Correction and Next Real-Effect
Node Selection (HMIC Certification vs. Hardware-Credential Enrollment)** —
analysis-only. Should formally amend PROJECT_STATUS.md's/149O.20L.7O.2I's
carried-forward DAG record to reflect §10 of this document, then choose
and author its own narrow authorization envelope (mirroring this phase's
own §7 discipline) for whichever of HMIC CertificationRecord creation or
FIDO2 hardware-credential enrollment is selected as the actual next
real-effect step. Not started, not authorized by this phase.

## 17. Governance

Used governed PCAE lifecycle only (`pcae task new`, `pcae commit`,
`pcae phase complete`, `pcae push`) — no raw `git commit`/`git push`, no
`--no-verify`, no force push, no hook bypass, no lifecycle bypass.
Pre-finalization checks (`pcae health`, `pcae check`, `pcae status
coherence`, `pcae doctor task-memory`, `pcae push check`, `pcae runtime
inspect`) run and recorded in the final report, not assumed.

