# Phase 149O.20L.7O.2A — RepositoryIdentity Write-Path Provisioning Gap Architecture + Remediation Proposition

## 0. Phase Identity and Type

**Architecture + remediation-proposition preparation only.** No Dell
mutation, no `RepositoryIdentity` creation, no `DeploymentBinding`, no
election, no CHGR, no certification, no Boundary C, no HATP activation.
Read-only Dell inspection is permitted and was used.

**Phase-entry commit:** `fc65ca51781c36219d338194d7c4e9abb0374b29`
(`Phase 149O.20L.7O.2: repair fast_green field with real
deselected-confirmation counts`). `origin/main == HEAD`, 0 commits
ahead/behind, working tree clean at entry.

## 1. Entering State (independently reconfirmed, not assumed)

```
git status --short                    → (clean)
git rev-parse HEAD                    → fc65ca51781c36219d338194d7c4e9abb0374b29
pcae check --json                     → passed, git_status.changed_file_count = 0
pcae push check                       → clean, nothing_to_push
```

Dell source (via fresh read-only SSH, `sudo -n -u pcae`, this session):

```
git -C /opt/pcae/runtime/src rev-parse HEAD
                                       → b0840e96a7ffb12308e95828aa5927c3e7c770c0  [matches phase brief]
ls .pcae/repository-identity.json     → No such file or directory (absent, confirmed live)
find /etc/pcae/hatp/trust-store       → empty (DeploymentBinding registry absent, confirmed live)
stat .pcae                            → root:pcae 750
getfacl -p .pcae                      → user::rwx / group::r-x / other::--- (no ACL entries beyond
                                          the POSIX mode itself — confirmed live, not inferred)
```

`RepositoryIdentity` remains ABSENT. `DeploymentBinding` remains ABSENT.
Exactly matches the phase brief's stated entering state.

## 2. Trust Wall (preserved throughout this phase)

- Allowing `RepositoryIdentity` creation ≠ making all `.pcae` state
  agent-writable.
- `RepositoryIdentity` is non-authority-conferring (per
  `repository_identity.py`'s own module docstring, HATP-REQ-051/063) ≠
  arbitrary `.pcae` mutation is safe.
- Write permission required ≠ a broad group-writable directory is
  necessarily correct.

`chmod 0770` was not selected by convenience — see §7-§10.

## 3. `.pcae` Contents and Ownership Model — Full Reconstruction

Two independent sources were read: the git-tracked baseline (what a
fresh checkout of the deployed SHA actually contains) and
`.pcae/.gitignore` (what the harness itself declares must exist at
runtime but is deliberately *not* checked in — i.e., every artifact
class the running agent is expected to create locally).

**Git-tracked baseline (17 top-level entries, confirmed live on Dell —
§1 `stat`/`ls -la` reproduced identically to the Mac-side `git
ls-files` inventory below):**

```
.pcae/.gitignore
.pcae/architecture-history.json
.pcae/audit/**
.pcae/authority-evaluation/**
.pcae/decision-sessions/**
.pcae/exports/.gitignore
.pcae/fleet-exports/.gitignore
.pcae/fleet.json
.pcae/phase-completion-metadata.json
.pcae/phase-completion-report.md
.pcae/phase-metadata-repairs.log
.pcae/policy.toml
.pcae/publication-execution/**
.pcae/repository-intelligence/**
.pcae/skills/**
.pcae/strategic-lineage.json
.pcae/strategic_reviews.json
```

All 17 confirmed present on Dell, all `root:pcae`, file mode `640` /
directory mode `750` — i.e. `pcae`-group-readable, `pcae`-not-writable,
exactly as the directory's own mode dictates. **Their canonical mutation
path is a governed `git commit` on the maintaining machine followed by a
redeployment (Actions 1-9's own sequence), not a live direct-filesystem
write by the `pcae` runtime process on Dell.** These are
**repository-local descriptive/administrator-controlled state**: version
history, governed decision-session records, policy, phase-completion
provenance, published skills — none of it is written by the running
agent process in place.

**`.pcae/.gitignore`'s own 34 entries — everything the harness declares
as runtime-local and *not* checked in, i.e., everything the running
agent is architecturally expected to create/write on a live deployment:**

```
session.json                    agent-lock.json           repository-identity.json
provenance-history.json         provenance-exports/       runtime-snapshots/
context-packs/                  continuity-packs/         governance-exports/
architecture/                   architecture-exports/     remote/
lifecycle-reviews/              handoffs/                 phase-queue.json
phase-audits/                   phase-prompts/             phase-reports/
notifications/                  delivery-receipts/        finalization-transactions/
shell-gate-audit/               backend-invocations/      backend-reviews/
backend-apply-plans/            backend-apply-readiness/  backend-manual-apply-packages/
backend-lifecycle-demos/        backend-adapter-preflights/
real-adapter-approvals/         real-adapter-invocation-plans/
artifact-only-real-invocation-dry-runs/
artifact-only-invocation-boundaries/
evidence-chain-bundles/         orchestration-plans/      execution-adjacent-plans/
execution-boundary-proof/       claude-runtime-evidence/
```

**Critical finding, independently derived, not stated in the phase
brief: the write-path gap is not narrow to
`repository-identity.json`.** Every single one of the ~34 entries above
requires `pcae` to create a file or directory directly inside `.pcae/`
(or a first-level subdirectory of it) the first time the corresponding
feature runs on Dell — `session.json` at session start, `agent-lock.json`
at lock acquisition, `provenance-history.json` at the first provenance
event, `phase-reports/` at the first phase report write, and so on. On
Dell's current `root:pcae 0750` topology, **all of them will fail with
the identical `PermissionError` at `tempfile.mkstemp`/`os.mkdir`** that
this phase's predecessor (149O.20L.7O.2) hit for
`repository-identity.json` specifically — RepositoryIdentity is simply
the first one the governed sequence happens to exercise. Any remediation
model must therefore be evaluated against the *whole* write-required set
above, not against a single filename.

**Authority classification of the write-required set:** none of it is
HATP-authority-bearing. `RepositoryIdentity` explicitly confers no
authority (module docstring, HATP-REQ-051/063). The controlling
authority artifact — `DeploymentBinding` — is read from
`HATPTrustStore.production()`, whose fixed root is
`/etc/pcae/hatp/trust-store` (`hatp_bootstrap.py` line 223,
`_LINUX_FIXED_TRUST_ROOT`), **entirely outside `.pcae/`**. Session
state, provenance, phase reports, backend-invocation records, etc. are
operational/audit state, not approval or authority state. This
significantly changes the risk profile of any `.pcae`-scoped
group-write grant — see §8.

## 4. RepositoryIdentity Producer Filesystem Requirements

Read `src/pcae/core/repository_identity.py` in full, directly (line
references below are to that file as of the phase-entry commit).

- **Target path:** `REPOSITORY_IDENTITY_RELATIVE_PATH = Path(".pcae") /
  "repository-identity.json"` (line 32), joined against
  `HarnessPath.cwd()` by the caller (`ensure_repository_identity`, line
  211).
- **Parent directory expectation:** `_write_atomic` (line 153) calls
  `directory.mkdir(parents=True, exist_ok=True)` — tolerant of an
  already-existing `.pcae/`, which is the live Dell case; this call is a
  no-op there, not the source of the failure.
- **Temp-file location:** same directory as the target
  (`tempfile.mkstemp(prefix=".tmp-repository-identity-",
  dir=str(directory))`, line 163) — never `/tmp` or any other location;
  the atomic-rename idiom requires same-filesystem, same-directory
  placement.
- **Atomic rename:** `os.replace(tmp_name, path)` (line 170) after
  `fsync` (line 168) — POSIX rename semantics, requires write+execute on
  the containing directory for both the temp file's creation and its
  rename-in-place.
- **File mode:** never explicitly set. `tempfile.mkstemp` creates its
  temp file at mode `0600` **regardless of the process umask** (CPython
  stdlib behavior — `mkstemp` uses `os.O_CREAT | os.O_EXCL` with a fixed
  `0600` file-creation mode, one of the few stdlib calls that does not
  defer to umask). `os.replace` preserves the temp file's mode/ownership
  across the rename. No `os.chmod`/`os.chown` call exists anywhere in
  this module.
- **Owner/group inheritance:** whatever OS principal executes the
  `mkstemp` call owns the resulting file; its group is that principal's
  effective primary group (standard POSIX file-creation semantics, no
  `setgid` bit observed on `.pcae/` — `stat` mode `750`, no `S_ISGID`).
- **Symlink protections:** `_reject_symlink(path)` (line 146) is called
  *twice* — once before `mkstemp` and once after `fsync`, before
  `os.replace` (lines 162, 169) — checking both the target path itself
  and its parent directory. This is a TOCTOU-narrowing double-check, not
  a single point-in-time test.
- **fsync behavior:** `handle.flush()` then `os.fsync(handle.fileno())`
  (lines 167-168) before replace — crash-consistent, standard durable-
  write idiom, matching the project's other `_write_atomic`
  implementations (`cltr/persistence.py`,
  `governance/publication/storage.py`, per this module's own comment,
  line 156-158).

**Minimum filesystem capability needed by the `pcae` principal on
`.pcae/` itself:** the ability to (a) create a new directory entry
(`mkstemp`'s `O_CREAT`) and (b) rename over/into an entry in the same
directory (`os.replace`). Both are directory-level operations under
POSIX — file-level permissions on the *target* filename are irrelevant
before it exists. No `chmod`/`chown` ability on `.pcae/` itself is
needed by the producer. Ownership of the *resulting* file is automatic
(creator becomes owner); no explicit post-creation `chown` step exists
or is needed.

## 5. Exact Creation Semantics — POSIX vs ACL Granularity

The producer needs, at minimum: **create** (new directory entry) and
**rename** (replace the temp name with the final name) rights on
`.pcae/`. It does **not** need `delete_child` as an independent right in
any way the producer itself exercises — `os.replace` targeting a
not-yet-existing final path is a rename-into, not a delete-then-create.
(The `finally: os.unlink(tmp_name)` at line 172-173 only fires on the
exception path, cleaning up its own temp file — still a delete of a
file `pcae` itself created, i.e. within its own ACL/mode-derived
create-right, not requiring authority over *other* principals' files.)

**Critical POSIX/Linux distinction the phase brief's own framing (its
§5/§9, "create permission only", "delete_child permission",
"rename permission" as if independently selectable) does not hold on
this filesystem class:**

- Read `hatp_class_b_topology_verifier.py`'s existing Linux ACL check,
  `_acl_grants_agent_write_linux` (lines 188-215): it parses `getfacl
  -p`'s `tag:qualifier:perms` triples and treats **any** entry
  containing the single letter `w` as write-granting — there is no
  separate token for "may create a new entry" vs. "may remove/rename an
  existing entry" in POSIX draft-1003.1e ACLs (the only ACL model Linux
  ext4 implements). This is unlike the macOS NFSv4-style ACL vocabulary
  the same module also parses (`_acl_grants_agent_write_macos`, lines
  334+, which *does* distinguish `add_file` from `delete_child` as
  separate rights) — the phase brief's §5/§9 wording describing
  independently grantable `add_file`/`delete_child`/`rename` rights is
  macOS ACL vocabulary, and **does not apply to Dell's ext4/Linux POSIX
  ACL filesystem.**
- On Linux, a single `w` bit — whether set via classic group-mode or via
  a POSIX ACL `group:pcae:rwx` entry — grants **both** "create a new
  entry" and "unlink or rename any entry in the directory, regardless of
  that entry's own owner or mode" (the traditional Unix directory-write
  rule; see `man 2 unlink`, `man 7 path_resolution`). **There is no
  POSIX-ACL-only way to grant `pcae` "create in `.pcae/`" without also
  granting it "delete/rename anything else already in `.pcae/`,
  including the `root`-owned governed files inventoried in §3."**
- The only orthogonal Linux/POSIX lever that separates these two rights
  is the **sticky bit** (`S_ISVTX`, `chmod +t`, classic `/tmp`
  semantics): with the sticky bit set on a group/other-writable
  directory, a non-owner (even with directory write permission) may
  still create new entries but may **not** unlink or rename an entry it
  does not own, unless it is also the directory's owner or `root`. This
  is confirmed by kernel behavior (`fs/namei.c`, `check_sticky()`),
  independent of any distro/host specifics, and does not require ACL
  tooling to reason about. **Neither `_mode_and_group_write_access` nor
  `_acl_grants_agent_write_linux` in this codebase currently inspects
  `S_ISVTX`** — a disclosed, pre-existing gap in the HBDC checkers
  themselves (not introduced by this phase, and out of this phase's
  scope to repair, but material to remediation-model selection: those
  checkers would still report a sticky-bit-protected directory as
  simply "group-writable," collapsing the very distinction this
  section derives). This is recorded as a follow-up finding, not
  repaired here (§17).

## 6. Desired Final RepositoryIdentity Ownership/Mode

Independently derived from the producer's own code (§4), not assumed:
because `_write_atomic` never calls `os.chmod`/`os.chown`, and
`tempfile.mkstemp` always creates at mode `0600` regardless of umask,
the file that results from a correctly-executed
`ensure_repository_identity()` call, run as the `pcae` OS principal, is
**`pcae:pcae 0600`** — owner-only readable and writable, group and
other with no access at all. This is confirmed, not merely predicted:
7O.1 §10 and 7O.2 §4/§10 both independently reached the identical
conclusion from the same source read. This phase reconfirms it directly
from the producer source (§4) as its own independent basis, and treats
it as authoritative: `pcae:pcae 0600` is the only architecture-correct
end state, because every downstream consumer
(`_check_deployment_identity`, HMIC's identity resolver) itself runs as
`pcae` and needs only owner-level read access. A `root`-owned `0600`
file (the escalation-to-root path considered and rejected in 7O.2 §10)
is not merely suboptimal — it is a strictly worse outcome (fail-open to
"present but unreadable," converting a clean absent-state into a
silently unusable one for every future reader).

## 7. Remediation Models — Comparison

### Model P-A — `.pcae/` group-writable (e.g. `root:pcae 0770`)

Grants `pcae` create+rename+delete/unlink on **every** entry in
`.pcae/`, including all 17 `root`-owned governed files/directories in
§3 — regardless of those files' own individual modes, per the
directory-write-implies-delete rule (§5). **Rejected as the primary
model** (see attack in §8), but see P-A′ below.

### Model P-A′ — group-writable + sticky bit (`root:pcae 1770`)

Adds `S_ISVTX` to P-A. `pcae` can still create any new entry inside
`.pcae/` (covering the entire §3 write-required inventory in one grant,
with no per-artifact-class enumeration needed), but can no longer
unlink/rename `root`-owned entries it did not itself create — only its
own files. This closes the specific attack in §8 while requiring no
production code change. **This is the strongest POSIX-only candidate**;
see §17 for its one disclosed side effect (HBDC checker blind spot).

### Model P-B — narrow POSIX ACL, mode unchanged at `0750`

`setfacl -m group:pcae:rwx /opt/pcae/runtime/src/.pcae`. As derived in
§5, Linux POSIX ACLs cannot separate "create" from "delete/rename" —
a `group:pcae:rwx` ACL entry is **functionally identical in blast
radius to Model P-A** (full write, including delete/rename of
`root`-owned entries), merely expressed via `setfacl` instead of
`chmod`. It does not by itself improve on P-A's risk profile. **An ACL
entry cannot itself carry a sticky-bit-equivalent restriction** — POSIX
ACLs have no analog to `S_ISVTX`; the sticky bit is a mode bit, entirely
orthogonal to the ACL mechanism, and must be set via `chmod` regardless
of whether ACLs are also used. **Therefore Model P-B, if selected, must
still be combined with the sticky bit to be equivalent-or-better than
P-A′, and adds only ACL-tooling complexity (a `setfacl` dependency,
`getfacl`-based verification) without a corresponding security benefit
over P-A′ on this filesystem.** Not recommended as a standalone model
over P-A′.

### Model P-C — dedicated writable RepositoryIdentity subpath

E.g. `.pcae/agent-writable/` as a `pcae`-owned (or `root:pcae 0770`)
subdirectory, with the producer changed to write
`repository-identity.json` (and, by the §3 finding, every other
runtime-local artifact) under that subpath instead of directly under
`.pcae/`. **Requires a production code change**
(`REPOSITORY_IDENTITY_RELATIVE_PATH` and the ~34 other paths in
`.pcae/.gitignore`'s own list would all need to move, plus every
consumer that reads them), a schema/path migration with its own
governance and testing burden, and a compatibility question for
existing deployments/tests that assume the current flat layout. Given
that P-A′ closes the actual attack (§8) with zero production-code
change and no path migration, P-C is **not the minimum-safe model**,
though it remains architecturally valid as a *future* hardening (full
separation of admin-owned vs. agent-owned state under two distinct,
independently-permissioned roots) — noted as a candidate for a later,
separately-governed phase, not this one.

### Model P-D — administrator pre-creates the file

Rejected outright per the phase brief's own constraint and this
phase's own reconfirmation (§6, §10 of 7O.2): a `root`-created file
would be `root`-owned, and, absent an explicit `chown`/`chmod` step the
producer itself never performs, would not be readable by `pcae`. Doing
so would also bypass the canonical identity producer (`_generate_
repository_identity`'s UUID4 generation, `_write_atomic`'s crash-
consistency), which the phase brief explicitly forbids accepting.
Rejected.

### Model P-E — not applicable

No additional evidence-supported model beyond P-A/P-A′/P-B/P-C/P-D was
identified from the producer source, the `.gitignore` inventory, or the
live Dell ACL/mode read (§1).

**Selected model: P-A′ — `chmod 1770 /opt/pcae/runtime/src/.pcae`
(owner `root`, group `pcae`, mode `1770`: `rwxrwx--T`).** Minimum
production-code change (none), covers the full §3 write-required
inventory (not just `repository-identity.json`), and closes the
delete/rename attack in §8 via the sticky bit — the only POSIX
mechanism on this filesystem class that does so without an ACL
dependency or a code/schema migration.

## 8. Broad Group-Write Attack — Evaluated

Under plain **P-A** (`0770`, no sticky bit), `pcae` (a `nologin`,
non-sudo, non-root principal — §4 of 7O.2, reconfirmed unchanged this
session) could, via ordinary `unlink(2)`/`rename(2)` on directory-write
authority alone, regardless of the target file's own owner/mode:

- **Replace or delete any of the 17 `root`-owned governed files** in
  §3 — `policy.toml`, `phase-completion-metadata.json`,
  `phase-completion-report.md`, `architecture-history.json`,
  `strategic-lineage.json`, `authority-evaluation/**`,
  `decision-sessions/**`, `publication-execution/**` (which,
  per `PHASE_149O_20L_7F...md`'s own consumer inventory, is where
  governance/publication records such as CHGRs live), and
  `repository-intelligence/**`.
- **Create arbitrarily-named files**, including names colliding with
  future admin-authored artifacts (a TOCTOU/race surface against any
  future admin write that does not itself use the same
  symlink-rejecting atomic idiom `repository_identity.py` uses).
- **Not** obtain HATP authority: `DeploymentBinding`/`HATPTrustStore`
  live at `/etc/pcae/hatp/trust-store`, wholly outside `.pcae/` (§3,
  §12) and unaffected by any `.pcae`-scoped permission change. This
  bounds the attack to **audit/governance-record self-tampering**, not
  authority escalation — a real but categorically different risk than
  "the agent could grant itself execution/approval rights."
- **Could** indirectly influence HMIC: `hatp_mandatory_certification.py`
  (line 191, HMIC-REQ-036) names `core/repository_identity.py` and
  `core/hatp_class_b_conformance.py` as members of its frozen-source
  certification scope, and 7F's test suite confirms both are HMIC-
  frozen-scope members. HMIC's own frozen-scope membership is a
  *source-file* list (checked against the git-committed SHA), not a
  `.pcae/` runtime-artifact list, so a `.pcae`-scoped write grant does
  not itself let `pcae` alter what HMIC certifies — but `pcae` deleting
  or corrupting `.pcae/publication-execution/**`/`decision-sessions/**`
  (where governance/publication records are persisted, per §8 above)
  could degrade the *evidentiary record* HMIC/decision-session tooling
  reads back, a downstream audit-integrity concern distinct from
  certification-scope tampering itself.

**Verdict: plain P-A (no sticky bit) is unacceptable** — not because it
grants authority, but because it grants unrestricted delete/rename over
governed audit/provenance/decision-session state that has no other
integrity protection at the filesystem layer. **P-A′ (sticky bit)
closes exactly this gap**: `pcae` retains full create rights (needed for
the entire §3 write-required inventory) but the kernel (`check_sticky()`)
refuses `unlink`/`rename` of any entry `pcae` does not own, which is
every one of the 17 `root`-owned governed entries.

## 9. ACL Derivation (POSIX/Linux, ext4)

Dell's root filesystem is `ext4` (confirmed live, §1, `mount` output:
`/dev/nvme0n1p6 on / type ext4 (rw,relatime)`), kernel `7.0.0-28-generic`
(Ubuntu 24.04.3 LTS, confirmed live). Modern Linux kernels (≥4.5) enable
POSIX ACL support for ext4 without requiring an explicit `acl` mount
option; `setfacl`/`getfacl` are present on the host (`/usr/bin/setfacl`,
`/usr/bin/getfacl`, confirmed live, §1). No ACL entries currently exist
on `.pcae/` beyond the POSIX-mode-derived defaults (`getfacl -p`
confirmed, §1) — the directory is unambiguously POSIX-mode-only today.

As derived in §5: the minimum POSIX ACL that would grant `pcae` "create"
also grants "delete/rename of everything," because Linux POSIX ACLs
carry only `r`/`w`/`x`, not the separate `add_file`/`delete_child`
rights the macOS NFSv4 ACL model (and the phase brief's phrasing)
implies. **No ACL-only grant achieves the minimum-safe outcome on this
filesystem without also setting the sticky bit** — and once the sticky
bit is set, plain group-mode `0770` (P-A′) already achieves the same
effective-write outcome as an ACL grant would, with zero additional
tooling dependency. **ACL (Model P-B) is therefore not selected**: it is
not unsafe by itself when combined with the sticky bit, but it is
strictly redundant with P-A′ on this filesystem, adds a `setfacl`
dependency, and (per §5) is not independently verifiable as "narrower"
than the mode-bit equivalent it collapses to.

## 10. Symlink/Path Protections

Unaffected by the choice between P-A/P-A′/P-B: `_reject_symlink` (§4)
already independently refuses both the target path and its parent if
either is a symlink, at two points in the write sequence, regardless of
the directory's own permission bits. This phase's own read-only preflight
(§1) reconfirmed no symlink exists anywhere in `.pcae/`'s ancestor chain
(`stat %F` on `.pcae`, `src`, `runtime`, `pcae`, `opt` — all report
`directory`, per 7O.2 §7, unchanged this session). No remediation model
in §7 introduces a new symlink-substitution surface: P-A′ changes only
mode bits on an already-verified-non-symlink directory; it does not
change how `_reject_symlink` operates. This mirrors 7O.2's own
"existing Class-B effective-write semantics" (its own §10 framing) —
this phase reuses, not reinvents, that reasoning.

## 11. HBDC Impact Simulation

Simulated (read-only, no mutation) by reproducing the exact corrected
canonical Action-9 invocation live on Dell this session:

```
sudo -u pcae sh -c "cd /opt/pcae/runtime/src && env -i \
  HOME=/home/pcae PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1 \
  /opt/pcae/runtime/venv/bin/python3 -c '
from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance as v
r = v()
print(\"status:\", r.status.value)
for c in r.checks:
    if not c.satisfied:
        print(c.check_id, c.status)
'"
```

Result, live, this session: `status: NON_COMPLIANT` /
`HBDC-REQ-042 no_repository_identity_present` — **the sole residual**,
exactly matching the originally expected baseline (see §13-14). No
`.pcae` permission change was made to obtain this result — it is the
*current*, unremediated state, confirming the corrected Action-9
invocation itself (not a directory-permission change) is what resolves
`HBDC-REQ-036` (§13-14).

**Would P-A′ break any other HBDC requirement?** Reviewed against every
`HBDC-REQ-0{25..39}` environment-lock check
(`hatp_environment_lock_verifier.py`) and every Class-B topology check
(`hatp_class_b_topology_verifier.py`): none of them evaluate
`/opt/pcae/runtime/src/.pcae` as their subject path. The topology/
environment-lock checks are scoped to the venv, the interpreter, the
launcher, `PYTHONPATH`/`sys.path`, the editable-install metadata, and
the authority-module origin containment root (`repo_root`, resolved from
`src/pcae/**`'s own package location) — **not** `.pcae/`. `HBDC-REQ-042`
(the only check that reads inside `.pcae/`, via
`repository_identity.read_repository_identity`) reads a file it expects
to eventually exist; it does not fail *because* `.pcae/` is writable —
it fails because the file is absent. Changing `.pcae/`'s mode to `1770`
does not touch any of `HBDC-REQ-016/017/020`'s authority-module-
containment-root reasoning (that root is `src/pcae/`'s installed
package directory, confirmed by reading
`_check_module_origin_containment`, unrelated to `.pcae/`). **No other
HBDC requirement is broken by P-A′.** The one caveat already disclosed
in §5: the existing `_mode_and_group_write_access`/`_acl_grants_agent_
write_linux` primitives, if ever pointed at `.pcae/` by a *future* HBDC
check, would report it "group-writable" without distinguishing the
sticky-bit protection — a latent false-positive risk for any *future*
check, not a present one (no current `HBDC-REQ-0xx` check targets
`.pcae/`'s own mode).

## 12. Protected Root Distinction — Reconfirmed Unaffected

`/opt/pcae/runtime/src/.pcae` (this phase's subject) and
`/etc/pcae/hatp/trust-store` (`_LINUX_FIXED_TRUST_ROOT`,
`hatp_bootstrap.py` line 223 — the `DeploymentBinding` trust store,
Protected Root) are **structurally distinct filesystem locations with
no ancestor relationship** (`/opt/...` vs. `/etc/...`). Confirmed live
this session unchanged: `find /etc/pcae/hatp/trust-store` — directory
exists, empty, no `registry.json` (§1). **No remediation model in §7
touches, references, or requires any change to `/etc/pcae/hatp/
trust-store`.** This phase makes zero change — proposed or executed —
to the Protected Root.

## 13. HBDC-REQ-036 Discrepancy — Independent Reconstruction

`_check_launcher` (`hatp_environment_lock_verifier.py` lines 368-382)
implements `HBDC-REQ-036`:

```python
def _check_launcher(agent_uid, agent_gids):
    launcher = shutil.which("pcae")
    if launcher is None:
        return ClassBCheckResult("HBDC-REQ-036", False, "no_configured_production_launcher_detected", ())
    ...
```

`shutil.which("pcae")` resolves purely against the calling process's
**current `PATH` environment variable** — it performs no venv
activation, no absolute-path fallback. Phase `149O.20L.7D.9`
(`REQ-036 Reconstruction — Old vs. Corrected Action-9 Invocation`, its
§15-16) already independently diagnosed and fixed exactly this class of
failure once before: the *old*, CHGR-authorized Action-9 environment
used `PATH=/usr/bin:/bin:/usr/sbin:/sbin`, which excludes
`/opt/pcae/runtime/venv/bin` — the only directory containing the
admin-controlled `pcae` launcher — causing `which("pcae")` to return
`None`. The *corrected* invocation prepends
`/opt/pcae/runtime/venv/bin` to `PATH`.

## 14. Canonical Action-9 Re-Test — Classification

Reconstructed and reproduced live, read-only, this session (both
commands executed as `pcae` via `sudo -n -u pcae`, cwd
`/opt/pcae/runtime/src`, no argument accepted from any external input,
no mutation — `verify_class_b_deployment_conformance()` performs no
filesystem write):

**(A) Plain `sudo -n -u pcae bash -c '...'` with no explicit `PATH`
override** — reproduces `sudo`'s own default environment. Confirmed live
this session: `sudo -n -u pcae bash -c 'echo $PATH'` →
`/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin`
— **does not include** `/opt/pcae/runtime/venv/bin`. Running the HBDC
aggregator under this environment, live:

```
status: NON_COMPLIANT
HBDC-REQ-036 no_configured_production_launcher_detected
HBDC-REQ-042 no_repository_identity_present
```

**Exactly reproduces 149O.20L.7O.2's own observed two-residual
result.**

**(B) The exact corrected canonical Action-9 invocation** (§11, explicit
`PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin`, `env
-i`-reset environment):

```
status: NON_COMPLIANT
HBDC-REQ-042 no_repository_identity_present
```

**`HBDC-REQ-036` passes** under (B) — sole residual is `HBDC-REQ-042`,
exactly the originally expected baseline the phase brief itself refers
to.

**Classification: A — invocation/config mismatch.** `149O.20L.7O.2`'s
diagnostic read of `verify_class_b_deployment_conformance()` did not use
the corrected, `venv/bin`-inclusive `PATH` that `149O.20L.7D.9`'s own
CHGR-track Action-9 amendment already established as necessary; it
appears to have relied on `sudo`'s own default (`secure_path`-derived)
environment instead, which — independently confirmed live, side-by-side,
this session — reproduces the exact discrepancy byte-for-byte. This is
**not** a real host regression (B), **not** a reporting error (C) — the
diagnostic function itself behaved correctly given the environment it
was actually invoked under — and **not** an "other" (D) classification.
The launcher itself (`/opt/pcae/runtime/venv/bin/pcae`) exists, is
resolvable, and is confirmed `pcae`-unwritable (`launcher_agent_
unwritable`, the `True` outcome under (B)) — it was never missing or
untrustworthy; it was simply not on the `PATH` the diagnostic process
happened to inherit. **`HBDC-REQ-036` does not block first-use
continuation and does not require repair** — only invocation discipline
(future preflight/diagnostic reads on Dell must use the corrected,
already-authorized Action-9 environment, not a bare `sudo -n -u pcae`
default). `HBDC-REQ-042` (`no_repository_identity_present`) remains the
sole genuine architectural residual, unchanged from the pre-7O.2
baseline.

## 15. RepositoryIdentity Retry Preconditions (Unchanged From Brief, Reconfirmed)

Future retry may occur only after: (a) `.pcae/`'s permission remediation
(§17) is independently verified, (b) source is unchanged from
`b0840e96a7ffb12308e95828aa5927c3e7c770c0` (or a newer commit re-verified
zero-drift per the source-currentness gate 7O.2 §2 used), (c) identity
is still absent (re-confirmed, not assumed), (d) no stray temp files
exist, (e) the HBDC baseline is understood using the corrected Action-9
invocation (§13-14, not the bare-`sudo` default), and (f) the `pcae`
principal can perform the canonical atomic creation — which, after
P-A′, it can.

## 16. Remediation Authority Classification

Changing `/opt/pcae/runtime/src/.pcae`'s deployed filesystem permissions
is a real-host administrative mutation, structurally identical in kind
to the original Boundary-P provisioning mutation
(`root:pcae 0750`) that phases `149O.20L.7B`/`7B.1`/`7B.2`/`7C` required
an explicit human `APPROVE`/`AMEND` election and decision-session capture
for (`class-b-boundary-p-provisioning-authorization`,
`5c8847923ba209ea270cb53138fb7e006b2e5f5c`-scoped). Per that governing
precedent — "proposal ≠ approval; approval ≠ provisioning," restated
explicitly in `7B` before its own election — **this phase classifies
`.pcae` permission remediation as a governed topology mutation requiring
its own explicit human election and decision-session capture**, not
"ordinary admin authorization" performed unelected merely because the
user controls the host. It is not authorized by any existing CHGR: the
sole prior Dell CHGR (`chgr-541cb08c313b4f8884970172d37c5a1d`, §15,
`149O.20L.7D.9`) scopes to the repaired Action-6 sequence and Actions
7-9's `PATH`/invocation semantics — it does not name `.pcae`'s own mode
or ACL state, and its own condition 6 text (reconfirmed in `7F`'s test
suite, `TestGoverningChgrCondition6`) explicitly excludes further
mutation without a fresh, separate election.

## 17. Exact Remediation Proposition (Not Executed This Phase)

- **Exact target path:** `/opt/pcae/runtime/src/.pcae` on `hac-dell`.
- **Exact before state:** owner `root`, group `pcae`, mode `750`
  (`drwxr-x---`), no ACL entries beyond the mode-derived defaults
  (confirmed live, §1).
- **Exact after state:** owner `root`, group `pcae`, mode `1770`
  (`drwxrwx--T`) — group write added, sticky bit added, other-access
  unchanged (none).
- **Exact command (for the future, separately-elected execution
  phase):** `sudo chmod 1770 /opt/pcae/runtime/src/.pcae`, executed as
  `root` (via `codex`'s existing passwordless `sudo`), from a
  fully-specified, non-interactive invocation matching this project's
  own established real-host command discipline (`§61`-style: absolute
  path, no glob, no ambient `cd` reliance) — the exact literal command
  string is deferred to that phase's own proposition materialization
  step, per §19 (permission proposition and identity creation must not
  be combined in one phase; this phase performs analysis and comparison
  only, per its own mutation wall).
- **Exact read-back:** `stat -c '%U:%G %a' /opt/pcae/runtime/src/.pcae`
  → expect `root:pcae 1770`; `getfacl -p` → expect unchanged (no ACL
  entries; P-A′ uses mode bits only, no `setfacl`).
- **Exact rollback:** `sudo chmod 750 /opt/pcae/runtime/src/.pcae`,
  independently checkable via the same `stat` read-back → expect
  `root:pcae 750`. No ACL state to roll back (P-A′ introduces none).
- **Exact HBDC expected effect:** no `HBDC-REQ-0xx` check changes status
  as a direct result of this chmod alone (§11) — `HBDC-REQ-042` remains
  `False`/`no_repository_identity_present` until a *separate*, later-
  governed `RepositoryIdentity` creation phase runs (§15, §19).
- **Exact exclusions:** no change to `/etc/pcae/hatp/trust-store` (§12);
  no `RepositoryIdentity` creation; no `DeploymentBinding` creation; no
  `git`/venv/wrapper mutation; no other file under `.pcae/` touched.
- **Disclosed follow-up (not this phase's scope):** `_mode_and_group_
  write_access`/`_acl_grants_agent_write_linux` do not currently inspect
  `S_ISVTX` (§5, §11) — if a future HBDC check is ever added that
  targets `.pcae/`'s own writability, that check (not this
  remediation) would need sticky-bit awareness to avoid a false
  "unsafely writable" positive against a P-A′-remediated directory.

## 18. Rollback

Defined above (§17) — a single `chmod 750` restores the exact prior
mode, independently checkable via `stat`, with no ACL state to reverse
(P-A′ never introduces one). No data-loss risk: the sticky bit and group
write bit are additive-only; no existing entries are moved, renamed, or
deleted by applying or reverting this chmod.

## 19. Sequencing — Not Combined With Identity Creation

This phase performs **analysis and proposition comparison only**. The
required future sequence, unchanged from the phase brief's own framing:

1. This proposition (149O.20L.7O.2A, complete).
2. A dedicated election/authority-capture phase (§16) — `APPROVE`/
   `DECLINE`/`AMEND` on the P-A′ `chmod 1770` proposition, decision-
   session captured, mirroring `7B`/`7B.1`/`7B.2`/`7C`'s own precedent.
3. A dedicated, narrow permission-execution phase — the single `chmod`
   mutation, independently verified read-back.
4. An independent-verification phase confirming the new mode/ACL state
   matches §17's "after" exactly, with no unintended side effect.
5. A `RepositoryIdentity` retry phase — the exact, already-reconstructed
   command from `7O.2`'s own §3/§8 (`ensure_repository_identity(root)`,
   run as `pcae`), requiring no further design work.

No permission mutation and no identity-creation attempt occur in the
same phase, preserving failure isolation exactly as the brief requires.

## 20. Final Verdict

**PERMISSION REMEDIATION PROPOSITION READY — ELECTION NOT INITIATED.**
A minimum-safe, zero-production-code-change remediation model (P-A′:
`chmod 1770`, group-write + sticky bit) has been derived, compared
against four alternatives, attack-tested against the specific threat the
phase brief raised (broad group-write enabling deletion of governed
`.pcae` state), and confirmed to leave `/etc/pcae/hatp/trust-store` and
every `HBDC-REQ-0{25..39}`/topology check unaffected. `HBDC-REQ-036` is
independently reconstructed and live-reclassified as an
invocation/config mismatch (Classification A), not a blocking
regression — confirmed by side-by-side live reproduction of both the
mismatched and corrected Action-9 environments this session. No election
has been initiated; that is this phase's own explicit boundary (§16,
§19).

## 21. Expected Safe Outcome — Confirmed

No Dell mutation occurred (§1, all commands read-only:
`id`/`hostname`/`git rev-parse|status`/`stat`/`find`/`ls`/`getfacl`, and
two pure-read Python calls — `verify_class_b_deployment_conformance()`
via two environment variants). `RepositoryIdentity` remains absent
(confirmed post-session, unchanged). `DeploymentBinding` remains absent
(trust-store confirmed still empty). `.pcae` remains unchanged —
`root:pcae 0750`, confirmed both before and after this session's Dell
reads. `HBDC-REQ-036` status is explicitly resolved/classified (§13-14).

## 22. Strategic Breakpoint

Unchanged, unreached, not begun this phase: the strategic breakpoint
(pause before Boundary C to begin the DeepSeek Harness comparative study
and the PCAE Runtime Adapter/Plugin architecture) remains gated on a
first-use `RepositoryIdentity` + `DeploymentBinding` + a clean,
independently-verified `COMPLIANT` HBDC on real Dell — none of which
this phase performed or was authorized to perform.

## Proof of No Mutation / No Forbidden Action

- **No Dell mutation:** every Dell command this session was one of
  `id`, `hostname`, `git rev-parse`/`status`/`symbolic-ref` (via `-c
  safe.directory=` override, not a persistent config write), `stat`,
  `find`, `ls`, `getfacl -p`, `mount`, `uname`, `cat /etc/os-release`,
  and pure-read Python (`verify_class_b_deployment_conformance()`,
  which performs no filesystem write — confirmed by reading its own
  call chain in §11/§4). No `chmod`/`chown`/`setfacl`/`git commit`/`git
  push`/venv/wrapper command was issued anywhere this phase.
- **No RepositoryIdentity created:** `ls .pcae/repository-identity.json`
  → absent, confirmed both at phase entry (§1) and unchanged (no write
  command of any kind was issued against that path this phase).
- **No DeploymentBinding created:** `/etc/pcae/hatp/trust-store`
  confirmed empty (§1), no `create_deployment_binding`-shaped call made,
  no write to that path attempted.
- **No election, no CHGR:** no decision-session or governance-record
  publish command was issued this phase.
- **No certification, no Boundary C, no HATP activation:** no
  certification function invoked (only the pure, read-only Class-B
  diagnostic); no Boundary-C-scoped code touched; no HATP activation
  command issued.

## Tests

`tests/test_phase_149o_20l_7o_2a_repositoryidentity_write_path_provisioning_gap_architecture.py`
— proves, against live production source (not simulation, except where
`tmp_path` fixtures isolate genuinely destructive/host-specific
behavior): the `.gitignore`-derived write-required inventory, the
`mkstemp`-derived `0600`/no-chown producer behavior, the Linux ACL
single-`w`-granularity fact (§5), the current HBDC-checker sticky-bit
blind spot (§5/§11, disclosed not repaired), `HBDC-REQ-036`'s live
`PATH`-dependence (mechanized via `monkeypatch`, no Dell access
required, reproducing the classification mechanism from §13-14
locally/portably), the Protected Root path distinctness (§12), and the
no-`RepositoryIdentity`-created / no-production-code-changed proof.

## Governance Results

- `pcae_check`: passed
- `pcae_health`: healthy
- `pcae_status_coherence`: coherent
- `pcae_push_check`: clean at entry
- No `src/pcae/**` production code changed this phase (doc + test +
  task/status governance files only)
- `fast_green`: **7806 passed, 5 skipped, 0 failed, 0 errors** (deselected
  confirmation run). Raw run with this phase's own changes present: 265
  failed, 7806 passed, 5 skipped, 10 errors. Independently confirmed via a
  live `git stash -u`/pop A/B comparison this phase (not merely cited from
  a prior phase): with this phase's changes removed, the identical suite
  produces 256 failed, 7791 passed, 5 skipped, 10 errors — i.e. 256 of the
  265 raw failures, and all 10 errors, are pre-existing and fully
  reproduce with zero relation to this phase's changes (which touch no
  `src/pcae/**` file). The remaining 9
  (`test_backend_cli.py::Test95TOrchCLI::test_missing_step_blocks`,
  `TestApplyPlanShow::test_show_after_create`,
  `TestBackendReviewApprove::test_approve_json_no_execution`/
  `test_approve_json_no_secrets`/`test_approve_succeeds_with_correct_ids`/
  `test_approve_updates_latest`,
  `test_backend_invocations.py::Test94UPreflightArtifactCLI::test_verify_latest_after_save`,
  `test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`,
  `TestRedactionSafety::test_token_env_redacted_in_persisted`) do not
  appear in the baseline A/B run, but were independently re-run in
  isolation (`-n0`, no `xdist` worker contention, this phase's changes
  present) and all 9 passed — confirmed `xdist` parallel-worker
  contention/flakiness (these tests exercise real subprocess/CLI/file-
  persistence paths sensitive to shared scratch state under parallel
  workers), not a regression attributable to this phase's content. The 10
  errors: 1 whole-module collection failure
  (`test_phase_149o_7_hatp_class_b_activation_independent_verification.py`,
  pre-existing missing-dependency/environment gap, `--ignore`d rather
  than `--deselect`ed for the confirmation run since collection errors are
  not individually node-addressable) plus 9 same-file fixture-setup
  errors in `test_phase_149o_20e_hmic_v1_2_hbdc_bound_contract_identity_independent_verification.py`
  — both pre-existing, matching `149O.20L.7O.1`'s own prior
  characterization of this exact error set.
- `report_notification_tests`: not_applicable_this_phase
- `bootstrap_session_reporting_tests`: not_applicable_this_phase

## Recommended Next Phase

A dedicated, human-governed election/decision-session-capture phase for
the P-A′ (`chmod 1770 /opt/pcae/runtime/src/.pcae`) proposition
materialized in §17 — mirroring `149O.20L.7B`/`7B.1`/`7B.2`/`7C`'s own
Boundary-P election precedent (§16) — followed, only after that
election and a dedicated execution + independent-verification phase, by
a `RepositoryIdentity` creation retry using the exact, already-
reconstructed command from `149O.20L.7O.2` §3/§8.
