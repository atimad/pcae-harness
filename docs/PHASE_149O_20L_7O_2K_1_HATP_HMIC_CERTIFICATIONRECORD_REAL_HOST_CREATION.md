# Phase 149O.20L.7O.2K.1 — HATP HMIC CertificationRecord Real-Host Creation

**Status: BLOCKED / NOT EXECUTED.**

## 1. Mandate

Execute the single real-effect node selected by 149O.20L.7O.2K — creation
(create-only) of one current HMIC `CertificationRecord` via the existing
protected admin ceremony `scripts/hatp_certification_admin.py create` on
`hac-dell`. No activation, no FIDO2 enrollment, no Principal/Signer/
DeploymentBinding creation, no readiness/HATP/Permission-Broker change.

## 2. What was done (all read-only; no protected-state write; no source
change)

1. Entry inspection on the Mac repository: `git status`, `git log`,
   `pcae health`, `pcae check`, `pcae status coherence`,
   `pcae doctor task-memory`, `pcae push check`, `pcae runtime inspect`,
   `pcae notify status`, `pcae phase-report show --latest` — all
   confirmed 2K complete, repository clean, `origin/main..HEAD` = 0, no
   prior active real-effect phase, runtime unchanged
   (Observed/observe/unavailable).
2. Read `scripts/hatp_certification_admin.py` in full (the ceremony HMIC-
   001 v1.6 actually exposes) and the relevant sections of
   `src/pcae/core/hatp_mandatory_certification.py` (derive_* functions,
   `_CONTRACT_IDENTITY_FILES`, `CertificationRecord`, error classes).
3. Confirmed there is **no separate "election" artifact/mechanism** for
   HMIC certification distinct from HMIC-REQ-076 steps 1-6 themselves
   (step 2: out-of-band human review of a canonical phase report as the
   `--verification-record-path` locator; step 5: explicit human
   confirmation of the tool-derived target tuple, either via an
   interactive TTY prompt or the script's own documented `--assume-yes`
   flag "for non-interactive/scripted admin invocation only"). 2K's own
   report already uses "election" only as an informal analogy to HPSE/
   HBDC's more formal election concept — grep across
   `src/pcae/core/*.py` found no `ElectionRecord`/election class tied to
   HMIC certification.
4. Attempted local derivation of the certification input tuple against
   the Mac working tree: `derive_repository_instance_id` fails closed
   (`RepositoryIdentityUnavailableError`) because no
   `.pcae/repository-identity.json` exists on the Mac clone — confirming
   the ceremony must run against the actual deployment source root, not
   the Mac working tree (consistent with HMIC-001's binding target being
   the *deployment instance's* source).
5. Fresh, read-only precheck on `hac-dell` (SSH, `BatchMode=yes`, no
   mutation — `ls`/`stat`/`getfacl`/`git log`/`cat`/`find`/`grep` only,
   several routed through passwordless `sudo -n` where required for
   read access under the Protected Root's `root:pcae 0750` permissions):
   - Host identity: hostname `atila-Latitude-E5470`, machine-id
     `54ff22ce400b475aa0d55cb68f4a3334`, `Linux ... 7.0.0-28-generic
     ... x86_64` — matches expected values.
   - SSH login identity is `codex` (uid 1003, groups `codex,sudo,users`)
     — **not** a member of the `pcae` group, and the Protected Root's
     group permission is `r-x` only (no group write) — so `codex` has no
     direct write access to the Protected Root; only `root` (via
     passwordless `sudo -n`) does. This refines HMIC-REQ-013's "Class-B
     Protected Administrator OS principal" to mean effectively "root",
     reachable from `codex` only through `sudo`.
   - Protected Root `/etc/pcae/hatp/trust-store`: exists, directory, not
     a symlink, `root:pcae`, mode `0750`, no extended ACL entries (base
     POSIX perms only), safe ancestor chain (`/etc/pcae/hatp` and
     `/etc/pcae` both `root:root 0755`) — **freshly compliant**,
     consistent with 2J's frozen envelope.
   - Certification state: `certifications.json` and
     `certification-bindings.json` are both **absent** under the
     Protected Root — confirms no CertificationRecord and no active
     binding exist, consistent with 2K's evidence.
   - `RepositoryIdentity` on the deployment source
     (`/opt/pcae/runtime/src/.pcae/repository-identity.json`):
     `repository_instance_id = 0107866f-af7c-40b4-8317-74e71acb05ca` —
     **matches** the phase spec's expected value exactly.

## 3. BLOCKING finding: source parity is not established (spec §38/§13/§40)

The deployment canonical source root's actual git `HEAD` is
`b0840e96a7ffb12308e95828aa5927c3e7c770c0` ("Phase 149O.20L.7L.6: repair
commit-hash mention in canonical staging report for finalization gate").
The Mac repository — the intended, currently-verified implementation
state this phase entered with — is at `0e8923c4` (Phase
149O.20L.7O.2K). **The deployment source is 260 commits behind** the
intended current implementation (`git log --oneline b0840e96..HEAD` on
the Mac clone = 260 commits), spanning phases 149O.20L.7M through
149O.20L.7O.2K inclusive.

This is not a cosmetic drift. Concretely:

- The deployment's own copy of
  `src/pcae/core/hatp_mandatory_certification.py::_CONTRACT_IDENTITY_FILES`
  contains only **5** entries (`HMRC-001`, `HATP-001`, `HSCE-001`,
  `RAE-001`, `HBDC-001`) — it predates phase 149O.20L.7O.2H, which added
  `HPSE-001` and `HHCE-001` to reach the current v1.5/v1.6 seven-member
  set.
- `docs/contracts/` on the deployment host has **no HMIC-001 contract
  file at all** (`ls .../docs/contracts/ | grep -i hmic` returned
  nothing) — the deployment predates HMIC-001 existing at its current
  path/identity in this repository's contract set.

Running `create` against the deployment root (`--repository-root
/opt/pcae/runtime/src`) would therefore derive `contract_versions` with
only 5 members, not the required 7, and would bind an
`implementation_commit`/`implementation_scope_digest` corresponding to a
source tree that is materially, structurally different from the
currently verified 36/7 HMIC-001 v1.6 architecture this phase was
chartered to certify. This directly triggers spec §13 ("If current
main/source no longer represents the independently verified 36/7
identity architecture: STOP"), §38 ("If source parity is not
established: STOP. Do not sync/deploy source during this phase unless an
explicitly authorized prerequisite already covers that mutation"), and
§40's explicit "source parity unresolved" human-stop condition.

Deploying/syncing the current Mac source to `/opt/pcae/runtime/src` to
close this gap is **not** an action this phase is authorized to take
(§37/§38 both explicitly forbid it absent a separately authorized
prerequisite already covering that mutation; none exists).

## 4. Disposition

Per §29 ("If any precondition fails before mutation: perform no
protected-state write... finish the phase truthfully as BLOCKED/NOT
EXECUTED") and §45 ("Create Blocking findings for any unexpected...
source-parity failure"), this phase stops here.

**No mutation of any kind was performed** — not on the Protected Root,
not on `certifications.json`/`certification-bindings.json`, not on any
HATP/HMIC state, not on Mac or deployment source. Every host interaction
was read-only (`ls`, `stat`, `getfacl`, `git log`/`status`/`remote`,
`cat`, `find`, `grep`), several routed through passwordless `sudo -n`
strictly for read access, never for a write/chmod/chown/deploy action.

Independently of the source-parity blocker, this phase also confirms
that HMIC-REQ-076 step 5's human confirmation of the tool-derived target
tuple is a genuine, irreducible human step (not a formal separate
"election" artifact) that this phase — even absent the source-parity
blocker — could not have autonomously fabricated on a live production
write per governing-prompt guidance; it is noted here for the record but
is not the controlling blocker, since source parity fails first and
independently.

## 5. Recommended next phase

A **source-synchronization phase** (redeploy/update
`/opt/pcae/runtime/src` on `hac-dell` to the current governed `main`
HEAD, through whatever governed redeployment mechanism the repository
already uses — see phase 149O.20L.7M "Dell Redeployment ..." for
precedent) must run and be independently verified **before** any future
attempt at 149O.20L.7O.2K's selected HMIC CertificationRecord creation
node. Only after source parity is re-established should a successor
phase re-run this phase's read-only prechecks fresh and, if a human with
genuine Protected Admin Authority is available to supply
`--certified-by` and the HMIC-REQ-076 step 5 confirmation, invoke the
create ceremony.
