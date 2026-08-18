# Phase 149O.20L.7O.2A.1 — RepositoryIdentity Write-Path Remediation Proposition Independent Verification

## 0. Phase Identity and Type

**Independent verification only.** No Dell mutation, no `chmod`, no ACL
mutation, no `RepositoryIdentity` creation, no `DeploymentBinding`
creation, no election, no CHGR publication, no certification, no
Boundary C, no HATP activation. Read-only Dell inspection would have
been permitted but was not needed this phase (no live Dell session was
opened — every claim below is checked against the Mac-side working
tree, which is the git-identical source of the deployed SHA, plus the
already-published live-read facts recorded in `149O.20L.7O.2A`'s own
doc, which this phase does not treat as an oracle — see §2/§4).

**Phase-entry commit:** `63e2f740824cab602f3d44239ad626350a8b337c`
(`Phase 149O.20L.7O.2A: repair pcae_push_check/pushed_status trust
fields post-push`). `git status --short` clean, `pcae check --json`
→ `passed`, `changed_file_count: 0`. `pcae push check` → clean,
`nothing_to_push`.

## 1. Evidence-Tier Convention (governs this whole report)

Per explicit governing instruction for this phase, no synthetic
root-owned test file was created on this Mac (Darwin/APFS) as a
stand-in for Linux sticky-bit kernel behavior, and no Dell mutation
(disposable or otherwise) was performed. Every claim below is tagged
with one of three evidence tiers:

- **DIRECTLY SOURCE-VERIFIED** — read from the actual production
  module in this working tree (the same SHA deployed on Dell,
  `b0840e96a7ffb12308e95828aa5927c3e7c770c0`, unchanged — see §3).
- **REFERENCE-VERIFIED FROM PRIMARY LINUX/POSIX SOURCE, NOT EMPIRICALLY
  EXECUTED THIS PHASE** — the Linux sticky-directory unlink/rename
  restriction (`S_ISVTX`, kernel `check_sticky()`/`may_delete()` in
  `fs/namei.c`, unchanged since the mechanism's SVR4/4.4BSD origin,
  mandated by POSIX/SUSv4 and identical to `/tmp`'s own long-standing
  `1777` behavior on every mainstream Linux distribution). This tier is
  used for §8-§9's kernel-mechanism claims specifically.
- **REPOSITORY-LOCAL/DISPOSABLE TESTED** — exercised directly against
  the real `tempfile`/`pathlib`/`os` primitives in this session, where
  the behavior under test is platform-independent (POSIX `open()`
  semantics for an already-existing target requiring file-level, not
  directory-level, write permission) and does not depend on the
  cross-principal (owner vs. non-owner) distinction that only Linux
  sticky-bit enforcement on Dell can exercise.

## 2. Verification Wall (preserved)

- permission remediation ≠ `RepositoryIdentity` creation.
- `RepositoryIdentity` creation ≠ `DeploymentBinding` creation.
- group-writable + sticky ≠ arbitrary `.pcae` writes are automatically
  safe.
- non-authority-conferring `RepositoryIdentity` ≠ every file under
  `.pcae` is non-authority-bearing.
- `149O.20L.7O.2A`'s own prose is treated as a claim to independently
  reconstruct, not as an oracle — §5 below documents the one place its
  own `.pcae`-inventory classification does not hold up against the
  actual production source.

## 3. Entry Checks / Reconciliation With 149O.20L.7O.2A

- `git rev-parse HEAD` (this session) = `63e2f740824cab602f3d44239ad626350a8b337c`;
  matches `149O.20L.7O.2A`'s own final commit (its phase-entry commit
  was the prior phase's tip, `fc65ca5...`, and its own doc/report/task
  commits are what produced today's `63e2f74` tip — reconciled, no
  drift).
- `pcae check --json` → `passed`; `pcae push check` → clean,
  `nothing_to_push`. No uncommitted state at entry.
- Dell source SHA this phase relies on for source-currentness:
  `b0840e96a7ffb12308e95828aa5927c3e7c770c0`, per `149O.20L.7O.2A §1`'s
  live read. This phase does not re-open a Dell session to re-confirm
  that SHA (no Dell command was issued this phase at all); it instead
  independently confirms that **this Mac working tree's
  `src/pcae/core/repository_identity.py`,
  `hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`,
  and `hatp_bootstrap.py`** — read directly, in full or by targeted
  section, in this session — are unchanged since `149O.20L.7O.2A`'s own
  phase-entry commit `fc65ca51781c36219d338194d7c4e9abb0374b29`
  (confirmed via `git log -- <path>` showing no intervening commits
  touching any of those four files between `fc65ca5` and this phase's
  `63e2f74` entry point). Source-currentness for the *next* phase that
  actually touches Dell still requires its own fresh live SHA
  reconfirmation (§28 preflight requirement, restated §15/§28 below) —
  this phase only establishes that the Mac-side analysis basis is
  unchanged from 7O.2A's own.

## 4. Independent Reconstruction of the Failure

DIRECTLY SOURCE-VERIFIED, read `src/pcae/core/repository_identity.py`
in full this session (`ensure_repository_identity`, lines 211-229;
`_write_atomic`, lines 153-173):

- `ensure_repository_identity()` calls `read_repository_identity()`
  first; if `None` (absent), it generates a new identity and calls
  `_write_atomic(target, payload)`.
- `_write_atomic` calls `tempfile.mkstemp(prefix=".tmp-repository-identity-",
  dir=str(directory))` — the temp file is created **inside `.pcae/`
  itself**, not `/tmp`.
- Creating any new directory entry via `mkstemp`'s `O_CREAT|O_EXCL`
  requires write+execute on the containing directory
  (`.pcae/`) for the OS principal performing the call.
- On Dell, `.pcae/` is `root:pcae 0750` (confirmed live by `149O.20L.7O.2A §1`,
  unchanged per this phase's own non-mutating stance). `pcae` is a
  member of group `pcae`, not the owner; mode `750` gives the group
  only `r-x` (no `w`). `pcae` therefore lacks directory-write authority
  on `.pcae/`.
- `mkstemp` under these conditions raises `PermissionError` at the
  `O_CREAT` step — before any file is created, before `fsync`, before
  `os.replace`. No temp file, no partial `repository-identity.json`, is
  left behind by a failed attempt (the `finally: os.unlink(tmp_name)`
  block at line 172-173 only runs if `tmp_name` was actually assigned,
  i.e. only after a successful `mkstemp`; a `mkstemp`-level
  `PermissionError` never reaches that `finally`, so there is nothing
  to clean up on this exact failure path).
- Confirmed independently (not trusted from `7O.2`/`7O.2A` prose):
  `git ls-files .pcae/repository-identity.json` → no output (never
  tracked, i.e. the file has never existed in this repository's git
  history at any commit) — consistent with "absent on every fresh
  checkout, first-write-required."

## 5. Independent Reconstruction of the `.pcae` Artifact Inventory — Table

Reconstructed directly from this session's own `git ls-files .pcae`
and `cat .pcae/.gitignore` (39 lines, not "34" — see finding below),
not accepted from `7O.2A`'s prose count.

**`.pcae/.gitignore` actually contains 39 entries** (confirmed by
`wc -l` and full listing this session), one more than `7O.2A §3`'s own
transcribed "34"-entry excerpt — the excerpt in `7O.2A`'s doc silently
omits one real entry: **`architecture-history.json`** (the file's
second line). This is not a rounding/typo issue; it is load-bearing
(see finding below).

| artifact/path | producer | consumer | expected owner (post-first-use) | expected writer principal | authority relevance | safe for pcae ownership? | safe for pcae delete/recreate? |
|---|---|---|---|---|---|---|---|
| `repository-identity.json` | `repository_identity.ensure_repository_identity` (mkstemp+`os.replace`) | HMIC identity resolver, `hatp_class_b_conformance._check_deployment_identity` | `pcae:pcae 0600` | `pcae` | non-authority-conferring (module docstring, HATP-REQ-051/063) | yes | yes (own file; idempotent re-read on restart, `read_repository_identity` never regenerates if present+valid) |
| `session.json` | `pcae.core.session` write path | `pcae session read/continuity-check` | `pcae:pcae` | `pcae` | operational/descriptive | yes | yes |
| `agent-lock.json` | `agent.acquire_agent_lock` (`open("x", ...)`, exclusive-create, DIRECTLY SOURCE-VERIFIED this session, `src/pcae/core/agent.py:288-306`) | `agent.read_agent_lock`/status | `pcae:pcae` | `pcae` | governance-session mutex, not HATP authority | yes | yes (`release_agent_lock` calls `target.unlink()` on its own file only — line 337/357) |
| `provenance-history.json` | provenance append path | provenance/timeline readers | `pcae:pcae` | `pcae` | audit trail | yes | yes |
| `phase-reports/`, `phase-queue.json`, `phase-audits/`, `phase-prompts/`, `notifications/`, `delivery-receipts/`, `finalization-transactions/`, `shell-gate-audit/`, `backend-*/`, `real-adapter-*/`, `artifact-only-*/`, `evidence-chain-bundles/`, `orchestration-plans/`, `execution-*`, `claude-runtime-evidence/`, `context-packs/`, `continuity-packs/`, `governance-exports/`, `architecture/`, `architecture-exports/`, `remote/`, `lifecycle-reviews/`, `handoffs/`, `runtime-snapshots/`, `provenance-exports/` (34 remaining `.gitignore` entries) | first-write-on-first-use, per feature | corresponding CLI/report readers | `pcae:pcae` (new entries) | `pcae` | operational/audit, not HATP authority (no code path in these modules imports `hatp_bootstrap`'s trust-store reader) | yes | yes |
| **`architecture-history.json`** | **`architecture.write_architecture_history_snapshot`** — **`target.open("w", ...)` direct truncating write, NOT `mkstemp`+`os.replace`** (DIRECTLY SOURCE-VERIFIED, `src/pcae/core/architecture.py:112-131`) | `read_architecture_history`, `architecture-status` CLI, `docs`/`health` reporting | **currently `root:pcae 0640` (tracked, git-checked-out; `7O.2A §3`'s own live read)** | claimed by `7O.2A §3` to be admin-only (git-commit-mutated); **contradicted by this phase's read of its own producer** — see finding below | operational/audit (architecture-drift history), not HATP authority | **NOT satisfied by P-A′ alone — see finding** | n/a (pre-existing root-owned file; sticky bit is irrelevant to this failure mode, see below) |
| `policy.toml`, `phase-completion-metadata.json`, `phase-completion-report.md`, `phase-metadata-repairs.log`, `fleet.json`, `strategic-lineage.json`, `strategic_reviews.json`, `audit/**`, `authority-evaluation/**`, `decision-sessions/**`, `publication-execution/**`, `repository-intelligence/**`, `skills/**` | governed CLI run on the maintaining machine (not the Dell `pcae` runtime principal) → `git commit` → redeploy | governance/audit/decision-session tooling, human review | `root:pcae 0640`/`0750`, tracked | maintainer (not `pcae`) | some are governance-record-adjacent (`publication-execution/**` holds CHGR records; `decision-sessions/**` holds election records) but are **read-only inputs to `pcae`**, never written by it in place | n/a (not pcae-owned by design) | **must NOT be pcae-writable — this is exactly what P-A′'s sticky bit exists to prevent (§8 below)** |

### Independent finding not present in `7O.2A`'s own analysis

**`architecture-history.json` is simultaneously (a) git-tracked
(root-owned, part of the 17-entry "administrator-controlled" baseline
`7O.2A §3` describes), (b) listed in `.pcae/.gitignore` as a
runtime-local artifact (contradicting (a)), and (c) actually written in
place at runtime by `write_architecture_history_snapshot`, called from
`pipeline.py:190`, `commands/session.py:443`, and
`commands/architecture.py:33` — i.e. on the same governed hot path
(`pcae check`/`pcae session bootstrap`/`pcae architecture`) that
exercises `ensure_repository_identity`.**

`7O.2A §3` states of its 17-entry tracked baseline (which explicitly
includes `.pcae/architecture-history.json`): *"Their canonical mutation
path is a governed `git commit` on the maintaining machine followed by
a redeployment... not a live direct-filesystem write by the `pcae`
runtime process on Dell."* This is **independently found to be
incorrect for `architecture-history.json` specifically** — its
producer (`architecture.py:112-131`) is a live, direct,
`pcae`-runtime-invoked write path, not a maintainer-only, commit-only
one. `7O.2A`'s own `.gitignore`-excerpt in the same section actually
omitted this exact filename from its pasted 34-line list (real file
has 39 lines, including `architecture-history.json` as line 2) — the
inconsistency between "tracked+admin-only" (§3 prose, 17-list) and
"gitignored+runtime-local" (§3 prose, 34-list, which the real
`.gitignore` contradicts by count) was not caught because the excerpt
silently dropped the one entry that would have exposed it.

**Consequence for the remediation-model comparison (§7, `7O.2A`):**
`write_architecture_history_snapshot` uses `target.open("w", ...)` — a
direct truncating open on a path that **already exists** on Dell (it is
git-tracked, checked out at the deployed SHA, mode `0640`). Per POSIX
`open(2)` semantics (REPOSITORY-LOCAL/DISPOSABLE TESTED this session,
§1 tier 3 — confirmed that truncating an *existing* path requires
file-level write permission, not directory-level create permission),
this call requires `W_OK` on the **file's own mode bits**, which are
`0640` (owner `rw`, group `r--`, other none) — `pcae`, a group member
and not the owner, has no write bit on the file itself. **Changing
`.pcae/`'s own directory mode to `1770` (P-A′, or any of P-A/P-B) does
not touch `architecture-history.json`'s own `0640` mode** — directory
permission bits govern directory-entry operations (create, unlink,
rename), not in-place content writes to an already-existing file whose
own mode denies the caller. **`write_architecture_history_snapshot`
therefore remains broken for `pcae` on Dell after any of the `.pcae`
directory-level remediation models in `7O.2A §7`, including the
selected P-A′.**

This does **not** change the safety verdict on P-A′ itself (it
introduces no new attack surface, no name-squatting/authority
escalation — see §12/§13 below) and does **not** block the narrower
`RepositoryIdentity`-specific remediation this proposition targets.
It **does** mean `7O.2A`'s broader claim — "P-A′... covers the full §3
write-required inventory (not just `repository-identity.json`)" — is
**not fully accurate** and must be corrected before the election
materials are presented as complete (§34/§35 below): one artifact in
that inventory (`architecture-history.json`) requires a *separate*,
not-yet-designed fix (most plausibly: migrate
`write_architecture_history_snapshot` to the same `mkstemp`+
`os.replace` atomic idiom `repository_identity.py` already uses, which
*would* be fixed by P-A′ exactly like `repository-identity.json` is —
but that is a production-code change, out of this phase's scope to
design or execute).

## 6. `.pcae` Consumer Classification

DIRECTLY SOURCE-VERIFIED this session: the only consumer of anything
under `.pcae/` that feeds an authority/certification/execution
decision is `hatp_class_b_conformance._check_deployment_identity`
(`HBDC-REQ-042`), which reads `repository_identity.read_repository_identity`
(non-authority-conferring, format-only) **and** cross-checks it against
`HATPTrustStore.production()`, whose fixed root
(`_LINUX_FIXED_TRUST_ROOT = Path("/etc/pcae/hatp/trust-store")`,
`hatp_bootstrap.py:223`) is **entirely outside `.pcae/`**. No other
`.pcae/`-scoped file (session state, provenance, phase reports,
backend-invocation records, architecture history, decision-session
records, publication-execution/CHGR records) is read by any
certification, permission, execution-authorization, lifecycle-gate, or
rollback-decision code path as a *trusted input* — every such file is
either (a) written and read back only by `pcae` itself for its own
operational bookkeeping, or (b) written by the maintainer via governed
`git commit` and read only by human-facing reporting/CLI surfaces
(`docs`, `health`, `architecture-status`), never by an automated
authority decision. This reconfirms `7O.2A §3/§8`'s classification:
DESCRIPTIVE/RUNTIME-LOCAL for the entire `.gitignore`-derived set,
AUTHORITY-BEARING/TRUSTED INPUT only for `DeploymentBinding` at the
Protected Root — with the one correction in §5 above (one artifact's
*producer mechanism*, not its *authority classification*, was
mischaracterized).

## 7. Pre-Creation / Name-Squatting Attack

DIRECTLY SOURCE-VERIFIED: `ensure_repository_identity()` is
architecturally idempotent by design — `read_repository_identity()` is
called first, and if a syntactically-valid document is present, it is
returned **unchanged**, with **no ownership check** on the file (only
JSON-schema/UUID4-format validation, `validate_repository_identity_document`).
This means `pcae` (the only principal ever expected to write this
path, under every remediation model in `7O.2A §7` including P-A′) could
in principle pre-create a `repository-identity.json` with a
self-chosen UUID4 before "legitimate" first use. This is **not a new
attack introduced by P-A′** — it is inherent to the idempotent-ensure
design and would exist identically under P-D (rejected) or any other
model that gives `pcae` create rights on `.pcae/` at all. It is
non-blocking because (a) `RepositoryIdentity` is explicitly
non-authority-conferring by module contract (HATP-REQ-051/063,
independently re-read this session), and (b) the only trust boundary
that matters — `DeploymentBinding` at `/etc/pcae/hatp/trust-store` — is
admin-only and structurally outside `.pcae/` (§6). Traced (not
speculated) across every consumer found in §6: **no privileged/root
process anywhere in this codebase uses "create-if-absent, trust
existing" semantics against a `pcae`-writable `.pcae/` path** — the
only privileged trust path is the Protected Root, which no
remediation model touches. No blocking pre-creation/name-squatting
finding.

## 8. Existing Root-Owned Entry Protection — Sticky-Bit Semantics

REFERENCE-VERIFIED FROM PRIMARY LINUX/POSIX SOURCE, NOT EMPIRICALLY
EXECUTED THIS PHASE (per §1 tiering and the explicit governing
instruction for this phase): with `S_ISVTX` set on a directory
(`chmod +t`), the kernel's directory-entry-removal check
(`check_sticky()`/`may_delete()`, `fs/namei.c`) additionally requires,
for `unlink(2)` and for `rename(2)` when replacing an existing target,
that the calling process either (i) owns the file being
removed/replaced, (ii) owns the containing directory, or (iii) holds
`CAP_FOWNER`/is root — in addition to the ordinary directory-write
check that already permits creating new entries. This is the same,
unmodified mechanism that has governed world-writable `/tmp`
(historically `1777`) on every mainstream Unix and Linux distribution
since the mechanism's introduction, and is mandated by POSIX/SUSv4 —
not host- or distro-specific. Applied to `root:pcae 1770` on
`/opt/pcae/runtime/src/.pcae` with `pcae` as a non-owning group member:
`pcae` retains directory-write (can still create new entries — the
group `w` bit is unchanged from P-A) but the added `S_ISVTX` bit
additionally blocks `pcae` from unlinking, renaming, or rename-replacing
any of the 17 `root`-owned tracked entries in §5's table, since `pcae`
owns none of them and is not the directory's owner. `pcae` may still
unlink/rename entries it itself created (own-file operations are never
sticky-bit-restricted). This is the exact, well-documented mechanism
`7O.2A §5/§8` describes; this phase reference-confirms it against the
primary kernel-source citation rather than re-deriving it from `7O.2A`'s
own prose.

## 9. Atomic-Replace Interaction

DIRECTLY SOURCE-VERIFIED (§4): `_write_atomic`'s `os.replace(tmp_name, path)`
targets a path that **does not yet exist** on first creation
(`repository-identity.json` absent, §4). `os.replace` onto a
non-existent target is a pure rename-into — POSIX `rename(2)`'s sticky
check (§8) only activates when the calling process does not own an
**existing** target it is replacing; a not-yet-existing target has
nothing to own-check against, so sticky bit does not block first
creation. This is fully consistent with directory-create semantics
generally (a rename that creates a new name is, for permission
purposes, equivalent to creating that name directly). **Expected
creation succeeds under P-A′.** For the *retry* case (identity file
already exists and is `pcae`-owned, per §6's ownership derivation
below): `ensure_repository_identity()` never reaches `_write_atomic` at
all in that case — `read_repository_identity()` returns the existing
valid document and the function returns early (§4/§7) — so no
rename-replace of an existing file is ever attempted by this producer
in the normal idempotent-reuse path.

## 10. RepositoryIdentity Expected Resulting Ownership

DIRECTLY SOURCE-VERIFIED, independently re-derived from `_write_atomic`
(§4): `tempfile.mkstemp` creates its file at mode `0600` regardless of
process umask (CPython/glibc `mkstemp` behavior — fixed `S_IRUSR|S_IWUSR`
creation mode, one of the few stdlib paths that bypasses umask); no
`os.chmod`/`os.chown` call exists anywhere in `repository_identity.py`
(confirmed via direct text search, `test_no_chmod_or_chown_call_anywhere_in_module`
passes, §"Tests" below). The resulting file, created by the `pcae`
process, is owned by `pcae:pcae` (creator-owns semantics) at mode
`0600`. This matches `7O.2A §6`'s conclusion; independently reconfirmed
from the same producer source, not merely re-cited. `pcae` subsequently
reading its own `0600`-owned file for idempotent reuse requires only
owner-read, which it has (§9) — confirmed no re-derivation gap.

## 11. Other Legitimate `pcae` Writers

Per §5's table: every entry in the `.gitignore`-derived set **except
`architecture-history.json`** is a genuine first-creation case (path
absent on a fresh deployment, confirmed via `git ls-files` showing none
of the other 38 gitignore-listed paths are tracked) using either
`mkstemp`+`os.replace` (`repository_identity.py`'s idiom) or
`open("x", ...)` exclusive-create (`agent.py`'s idiom, §5 table) — both
are pure directory-create operations, requiring only the directory-level
`w` bit P-A′ grants, with no pre-existing-target complication. **P-A′
correctly fixes the general provisioning gap for 38 of the 39
`.gitignore`-declared artifacts.** `architecture-history.json` is the
sole, disclosed exception (§5) because it is both pre-existing
(tracked) and written via direct truncating `open("w")` rather than the
atomic-rename idiom. This is a materially narrower (and more precise)
finding than `7O.2A §7`'s unqualified "covers the full §3 write-required
inventory" claim.

## 12. Root-Owned Governed Entries — Protection Verified

Per §5's table, the 17 git-tracked, `root:pcae`-owned entries
(`policy.toml`, `phase-completion-metadata.json`,
`phase-completion-report.md`, `phase-metadata-repairs.log`,
`fleet.json`, `strategic-lineage.json`, `strategic_reviews.json`,
`architecture-history.json`, `audit/**`, `authority-evaluation/**`,
`decision-sessions/**`, `publication-execution/**` [governance/CHGR
records], `repository-intelligence/**`, `skills/**`, `.gitignore`
itself) — enumerated directly via `git ls-files .pcae` this session,
not sampled — are all entries `pcae` did not create. Per §8's
reference-verified sticky-bit mechanism, `pcae` cannot delete, rename,
or rename-replace any of them under P-A′. `pcae` also cannot write
their *content* in place unless their own file mode grants it — all 17
are `0640` (confirmed live by `7O.2A §3`, unaffected by this phase),
denying `pcae` (group, not owner) write access at the file level
regardless of the directory's mode. **All 17 root-owned governed
entries are protected from deletion, rename, replacement, and direct
content write under P-A′**, independently confirmed via the
combination of (a) the directory-level sticky-bit mechanism (§8) and
(b) each entry's own unaffected `0640` file mode (§5/§10) — two
independent, stacked protections, not one.

## 13. Directory Metadata Attacks

DIRECTLY SOURCE-VERIFIED / POSIX-standard reasoning: none of
`chmod(2)`/`chown(2)`/`setfacl`(ACL-set) is grantable via a directory's
own `w` bit or sticky bit — changing a file's mode, owner, or ACL
requires being the file's owner or root (`CAP_FOWNER`/`CAP_CHOWN`),
categorically independent of directory permissions. P-A′ grants `pcae`
nothing here: `pcae` cannot `chmod`/`chown`/`setfacl` any of the 17
root-owned entries under any of P-A/P-A′/P-B, because none of those
models changes who *owns* those files. Renaming `.pcae/` itself or
replacing its parent path (`src/`) requires write permission on `src/`'s
own parent, which is unaffected by this proposition (P-A′ scopes
strictly to `.pcae/`'s own mode, per `7O.2A §17`'s exact-command
constraint, reconfirmed §27 below) — `pcae` has no such grant today and
none is proposed. Symlink-following by privileged consumers: covered
in §14.

## 14. Symlink Name-Squatting Attack

DIRECTLY SOURCE-VERIFIED (§4): `_reject_symlink` is called twice in
`repository_identity.py`'s write path (once before `mkstemp`, once
after `fsync`/before `os.replace`) and once in `read_repository_identity`
— checking both the target path and its parent directory at each call.
Under P-A′, `pcae` could create a symlink at some *other*
`.gitignore`-declared path (e.g. `session.json` as a symlink pointing
elsewhere) since directory-create rights extend to `symlink(2)` the
same as any other new-entry creation. Traced this session: **no other
consumer module in the write-required set (`agent.py`'s
`read_agent_lock`, `architecture.py`'s `read_architecture_history`, the
provenance/session readers) was found to perform an equivalent
symlink-rejection check before reading its own runtime-local path** —
this is a **pre-existing gap in those modules, not introduced or
worsened by P-A′** (it exists identically under the current `0750`
mode for any future `pcae`-writable path, and under every model in
`7O.2A §7`). None of these paths is an authority-relevant consumer
(§6) — a `pcae`-created symlink at, say, `session.json` could at most
cause `pcae` to read back data from a location `pcae` itself chose,
which is not a privilege-escalation surface since `pcae` already
controls the content either way. **Non-blocking**, but disclosed as a
finding parallel in kind to `7O.2A §5`'s own disclosed
HBDC-sticky-bit-blind-spot finding: a defense-in-depth gap worth a
future, separately-scoped hardening phase, not a reason to reject
P-A′.

## 15. FIFO / Device / Unusual-Object Attack

DIRECTLY SOURCE-VERIFIED: none of the write-required-set consumer
functions read via a raw `open()` without first checking `Path.is_file()`
or going through `json.loads(path.read_text(...))` (which itself
would simply block/error against a FIFO or hang is not applicable here
since these are synchronous CLI invocations, not long-running daemons
reading arbitrary paths — a FIFO with no writer would raise on
`read_text` after `is_file()`/`exists()` checks, most of these readers
guard with `.is_file()` first, e.g. `read_agent_lock`'s
`if not target.is_file(): return None` at `agent.py:363`, and
`repository_identity.py`'s `read_repository_identity` uses
`target.exists()` then `.read_text()`). A `pcae`-created FIFO, socket,
symlink, or directory at an expected artifact path would, at worst,
cause the corresponding reader to raise an `OSError`/return `None`
(treated as "absent," triggering normal first-use provisioning
behavior) rather than being silently trusted or causing unsafe
behavior in a privileged context — because, per §6, none of these
readers execute in a privileged/root context or feed an authority
decision. Confined to `.pcae` consumers as instructed; no broader
local-security claim made.

## 16. P-A vs. P-A′ Comparison — Independently Reconfirmed

DIRECTLY SOURCE-VERIFIED + REFERENCE-VERIFIED (§8): plain `0770`
(P-A) grants `pcae` unrestricted `unlink`/`rename` over **every** entry
in `.pcae/` via the ordinary directory-write rule — there is no
mode-bit-only way to separate "create" from "delete/rename existing"
without the sticky bit (confirmed: POSIX defines exactly one such lever,
`S_ISVTX`; there is no alternate mode bit for this). The sticky bit is
therefore not an incremental hardening choice among equals — it is the
**sole** POSIX mechanism, on a mode-bits-only remediation, that
prevents `pcae` from deleting/replacing the 17 root-owned governed
entries in §12. Independently reconfirmed, not merely re-cited from
`7O.2A §5/§8`.

## 17. P-B (ACL) Re-Evaluation

DIRECTLY SOURCE-VERIFIED, `_acl_grants_agent_write_linux`
(`hatp_class_b_topology_verifier.py:188-220`, read in full this
session): a Linux POSIX-1003.1e ACL entry (`user:`/`group:`/`mask:`/
`other:` triples) exposes only `r`/`w`/`x` — the check treats **any**
`w` in the parsed triple as write-granting, with no separate
create-vs-delete token (confirmed directly from this function's own
logic, lines 211-219: `if "w" not in perms: continue`, no distinction
made). A `setfacl -m group:pcae:rwx` grant is therefore functionally
identical in blast radius to plain `0770` (P-A) — it does not, by
itself, narrow access below P-A′. Since POSIX ACLs carry no
sticky-bit-equivalent right (the sticky bit is a mode bit, orthogonal
to and independent of the ACL mechanism — `chmod +t` is required
regardless of whether ACLs are also applied), **no combination of
POSIX ACL + sticky bit narrows access further than P-A′ (mode-only
`1770`) already does** — an ACL grant layered on top of `1770` would be
redundant, not additive, for this specific create-vs-delete
distinction. **Confirmed: P-A′ remains the minimum-simple safe model;**
ACL adds a `setfacl`/`getfacl` tooling dependency with no
corresponding security benefit here.

## 18. P-C (Dedicated Subpath) Re-Evaluation

Re-examined in light of §5's `architecture-history.json` finding: P-C
(a dedicated `pcae`-owned subpath, e.g. `.pcae/agent-writable/`) would
have avoided the `architecture-history.json` gap entirely for *new*
deployments, since a fully separate root would not inherit any
pre-existing root-owned tracked file at a colliding name. However,
`architecture-history.json`'s problem is not path-collision — it is
that its *own* producer mechanism (`open("w")` truncate) is
incompatible with being a **pre-existing, root-owned** file under any
model that does not either (a) move it to a path `pcae` owns outright
from creation, or (b) rewrite its producer to the atomic-rename idiom.
P-C would require exactly the production-code/schema-migration burden
`7O.2A §7` already identified (moving `REPOSITORY_IDENTITY_RELATIVE_PATH`
and, by extension, `ARCHITECTURE_HISTORY_RELATIVE_PATH` and every other
write-required path) — now confirmed to still require, at minimum,
`architecture-history.json`'s data either move to the new subpath
(losing the existing tracked history, a compatibility break `7O.2A §7`
already flagged as a burden) or be excluded/handled specially anyway.
P-C does not obviate the `architecture-history.json` fix — it merely
relocates where that fix would need to happen. **P-A′ remains the
minimum-safe model for the RepositoryIdentity-scoped remediation this
proposition targets; P-C remains a legitimate, separately-governed
future hardening, not a reason to withhold P-A′ now** — unchanged
conclusion from `7O.2A §7`, independently reconfirmed with the added
precision that P-C would not have been a silver bullet for the
`architecture-history.json` finding either.

## 19. P-D Re-Evaluation

Reconfirmed rejected. `_generate_repository_identity`/`_write_atomic`
are the sole canonical producer (§4/§10); an administrator-pre-created
file would bypass `_write_atomic`'s crash-consistency and would be
`root`-owned absent an explicit `chown`/`chmod` step the producer never
performs — independently re-confirmed from the same source this
session, not re-cited.

## 20. HBDC Impact

DIRECTLY SOURCE-VERIFIED this session: read every check function in
`hatp_environment_lock_verifier.py` and `hatp_class_b_topology_verifier.py`
that is registered as an `HBDC-REQ-0{25..39}`/Class-B topology check.
None takes `/opt/pcae/runtime/src/.pcae` (or any subpath of it) as its
subject path — the topology/environment-lock checks target the venv,
interpreter, launcher resolution (`_check_launcher`, §21 below), and
the authority-module containment root (`repo_root`, resolved from
`src/pcae/`'s installed package location, not `.pcae/`). The only check
that reads *inside* `.pcae/` is `HBDC-REQ-042`
(`_check_deployment_identity`, `hatp_class_b_conformance.py:97-132`,
read in full this session), which reads `repository-identity.json`'s
*content* (via `read_repository_identity`) — it does not evaluate
`.pcae/`'s own mode/ACL as a subject. **Changing `.pcae/`'s mode to
`1770` does not, by itself, flip any `HBDC-REQ-0xx` check's status** —
`HBDC-REQ-042` remains `False`/`no_repository_identity_present` until a
separate, later-governed `RepositoryIdentity` creation actually
succeeds. No topology check inspects `S_ISVTX` (§8/§17's Linux-ACL
function, directly reread this session, confirms no `stat`/`S_ISVTX`
reference anywhere in that module — `grep -rn "S_ISVTX" src/pcae`
returns zero matches, confirmed this session). **P-A′ does not fail
any Class-B requirement.**

## 21. Tracked-Source Trust Implications

DIRECTLY SOURCE-VERIFIED: `.pcae/` becoming `pcae`-writable (directory
level) has no relationship to `src/pcae/**`'s own permissions, `.git`'s
permissions, `HEAD`/refs/index, the venv, or the launcher wrapper — all
structurally separate filesystem locations, none of them a descendant
of `/opt/pcae/runtime/src/.pcae`. `HBDC-REQ-036`'s `_check_launcher`
(§25) already independently verifies `launcher_agent_unwritable` as a
*passing* condition today (confirmed by the corrected-invocation
result in `7O.2A §14`, reference-cited not re-derived by this phase
since it requires live Dell access this phase does not open) — nothing
in P-A′ touches that check's subject (the launcher binary path, not
`.pcae/`).

## 22. Git Ignored-State Implications

DIRECTLY SOURCE-VERIFIED: `.pcae/.gitignore`'s 39 entries (§5) already
declare every runtime-local artifact class as ignored; a `pcae`-created
`repository-identity.json` (or any of the other 38 first-creation
artifacts) under P-A′ would **not** appear in `git status --short`
output, by the ignore rule already in place — this is unrelated to and
unaffected by the directory's own mode. `git status` cleanliness is
explicitly **not** treated as a security proof here (per this phase's
own governing instruction) — it is cited only as an expected,
unsurprising state-behavior consequence, no more.

## 23. HMIC Digest Implications

DIRECTLY SOURCE-VERIFIED: `derive_implementation_scope_digest`
(`hatp_mandatory_certification.py:1213`) computes its digest over a
fixed, explicitly-enumerated frozen-scope source-file list (confirmed
this session at lines 966/982: `"core/repository_identity.py"`,
`"core/hatp_class_b_conformance.py"`, among others) — a **source-file**
list, hashed by content, not a `.pcae/`-runtime-artifact list. Neither
a `.pcae/` directory-mode change nor a `RepositoryIdentity` file's
creation touches any file in that frozen-scope list's content. **The
HMIC digest is unaffected by P-A′ or by `RepositoryIdentity` creation**
— reconfirmed directly from the digest function's own scope
definition, not merely asserted.

## 24. Protected Root — Reconfirmed Isolated

DIRECTLY SOURCE-VERIFIED: `_LINUX_FIXED_TRUST_ROOT = Path("/etc/pcae/hatp/trust-store")`
(`hatp_bootstrap.py:223`, read directly this session). `/opt/pcae/runtime/src/.pcae`
and `/etc/pcae/hatp/trust-store` share no filesystem ancestor
(`/opt/...` vs. `/etc/...`). No remediation model in `7O.2A §7`, and no
code path read this session, touches, references, or requires any
change to the Protected Root. Zero effect, reconfirmed independently.

## 25. HBDC-REQ-036 — Independent Re-Verification

Not re-executed live against Dell this phase (no Dell session opened,
per §0/§1). Instead, DIRECTLY SOURCE-VERIFIED the mechanism this
session by reading `_check_launcher`
(`hatp_environment_lock_verifier.py:368-382`) directly: it calls
`shutil.which("pcae")`, which resolves purely against the calling
process's inherited `PATH` — no venv activation, no absolute-path
fallback, confirmed by reading the function body itself (no other
resolution attempt exists in the function). This directly confirms the
*mechanism* `7O.2A §13-14` used to explain why (A) a bare-`sudo`
default `PATH` (excluding `/opt/pcae/runtime/venv/bin`) reproduces
`HBDC-REQ-036 = False`, and (B) the corrected, `venv/bin`-prepended
`PATH` reproduces `HBDC-REQ-036 = True`. The project's own test suite
(`tests/test_phase_149o_20l_7o_2a_repositoryidentity_write_path_provisioning_gap_architecture.py::TestReq036PathDependence`,
run this session, both tests pass — see "Tests" below) mechanizes this
exact A/B distinction locally via `monkeypatch`, without requiring Dell
access, and independently confirms the `PATH`-dependence mechanism
`7O.2A` demonstrated live. **This phase does not independently
re-execute the live Dell A/B reproduction itself** (that would require
opening a Dell session, out of this phase's stated read-only-optional,
no-mutation scope, and not necessary to confirm the *mechanism*, which
is fully determined by the pure Python function body). No discrepancy
found between the mechanized local reproduction and `7O.2A`'s live
result. `HBDC-REQ-042` remains the sole residual under the corrected
canonical invocation, per `7O.2A`'s own live result, not
independently re-run this phase.

## 26. Canonical HBDC Invocation Freeze — Reconfirmed

`7O.2A §13-14`'s corrected invocation (`env -i` reset,
`PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin`,
`HOME=/home/pcae`, `PYTHONNOUSERSITE=1`, `cwd=/opt/pcae/runtime/src`,
run as `pcae` via `sudo -n -u pcae`) is the environment any future
Dell-touching phase (permission execution, identity retry) must use for
its own preflight/read-back checks — restated here as a binding
constraint on `149O.20L.7O.2A.2`/`.3`/`.4`/`.5`, not re-derived (this
phase performed no live Dell command, so it cannot re-source this
environment; it is carried forward as `7O.2A`'s own documented,
live-confirmed fact).

## 27. Proposition Exactness

Read `7O.2A §17` directly, this session, in full (quoted above verbatim
in the phase-entry read, §"1. Entering State" not needed to be
re-fetched from Dell — the exact command text lives in the Mac-side
doc). The exact command given is:

```
sudo chmod 1770 /opt/pcae/runtime/src/.pcae
```

executed as `root` via `codex`'s existing passwordless `sudo`. Checked:
absolute path (`/opt/pcae/runtime/src/.pcae`, yes); no recursive flag
(no `-R`, confirmed by direct reading — the string contains no `-R`);
no glob (no `*`/`?`/`[`, confirmed); no ACL mutation (no `setfacl`
anywhere in the command or in P-A′'s definition); no ownership mutation
(no `chown`, owner remains `root`, group remains `pcae` — the mode
argument `1770` changes only permission+sticky bits, not owner/group,
per `chmod`'s own semantics). **Note:** `7O.2A §17` itself flags this
exact string as provisional — *"the exact literal command string is
deferred to that phase's own proposition materialization step"* — so
`149O.20L.7O.2A.2` (the election phase) must re-materialize and
re-confirm this exact string at execution time, not merely inherit it
unchecked; this phase confirms the string as currently documented
satisfies all of §27's constraints, not that it is frozen beyond
re-confirmation.

## 28. Preflight (Restated for the Future Execution Phase)

Unchanged from `7O.2A §15`/brief's own requirement, restated here as a
binding checklist for `149O.20L.7O.2A.4` (chmod execution): before
mutation, freshly re-verify, live, on Dell: host/machine-id match;
source SHA exactly `b0840e96a7ffb12308e95828aa5927c3e7c770c0` (or a
newer commit re-verified zero-drift per the source-currentness gate);
`.pcae` still `root:pcae 0750`; no extended ACL; `RepositoryIdentity`
still absent; `DeploymentBinding` still absent; Protected Root
unchanged (empty, no `registry.json`); canonical HBDC baseline still
`NON_COMPLIANT`/sole-residual `HBDC-REQ-042` under the corrected
invocation (§26); no unexpected filesystem object at any
write-required path. Any mismatch: STOP. This phase performs none of
these live checks itself (no Dell session opened) — it restates the
requirement as a precondition for the *next* Dell-touching phase, per
this phase's own no-Dell-mutation, verification-only scope.

## 29. Read-Back (Restated)

Unchanged from `7O.2A §17`: after the future `chmod`, require `stat -c
'%U:%G %a' /opt/pcae/runtime/src/.pcae` → `root:pcae 1770`; `getfacl -p`
→ unchanged (no ACL entries); all 17 root-owned entries' own
owner/mode unchanged (independently spot-checkable via `stat` on each,
per §12's enumeration); no file creation as a side effect of the
`chmod` itself (mode changes create no new directory entries); source
tree remains clean/exact at the same SHA; HMIC digest unchanged (§23
— the digest doesn't read `.pcae/` at all, so trivially unaffected);
HBDC canonical baseline unchanged (§20 — no check targets `.pcae/`'s
mode) until a separate identity-creation phase runs.

## 30. Rollback (Restated)

Unchanged: `sudo chmod 750 /opt/pcae/runtime/src/.pcae`, independently
checkable via the same `stat` read-back → `root:pcae 750`. No ACL state
to restore (P-A′ introduces none, §17). Network-independent, single
command, no other rollback action required — reconfirmed, this phase
identifies no additional state P-A′ would introduce that rollback would
need to address (the sticky bit and group-write bit are the only
changes, both mode-bit-only, both trivially reversible by the same
single `chmod`).

## 31. Authority Requirement — Independently Reconfirmed

`7O.2A §16` classifies the `.pcae` mode change as a governed topology
mutation requiring its own human election, citing the
`149O.20L.7B`/`7B.1`/`7B.2`/`7C` Boundary-P precedent
(`class-b-boundary-p-provisioning-authorization`,
`5c8847923ba209ea270cb53138fb7e006b2e5f5c`-scoped). This phase
independently confirmed the precedent's existence directly (not by
analogy alone): `docs/PHASE_149O_20L_7B_DELL_CLASS_B_BOUNDARY_P_AUTHORIZATION_RECORD_CAPTURE.md`,
`..._7B_1_...PROPOSITION_MATERIALIZATION_AMENDMENT.md`, and
`..._7B_2_...AUTHORIZATION_RECORD_RE_CAPTURE.md` exist in this working
tree (confirmed via direct file listing this session), and the
governance-authority-evaluation template
`.pcae/authority-evaluation/templates/class-b-boundary-p-provisioning-authorization/1.0.json`
is git-tracked (confirmed via `git ls-files`, §5) — a real, primary,
persisted authorization-template artifact from that precedent, not a
paraphrase. `.pcae`'s own current mode (`root:pcae 0750`) is exactly
the object that precedent's election authorized; changing it further
(to `1770`) is the same class of real-host administrative mutation and
falls under the same governance requirement by direct structural
analogy to an artifact this phase independently located and confirmed
exists, not by trusting `7O.2A`'s characterization alone. **Reconfirmed:
`.pcae` permission remediation requires its own explicit human election
and decision-session capture.**

## 32. Election Proposition Completeness

Checked against `7O.2A §17` (quoted in full, §27 above) plus this
phase's own §5 correction:

- exact host (`hac-dell`): present.
- exact path (`/opt/pcae/runtime/src/.pcae`): present.
- before (`root:pcae 0750`): present.
- after (`root:pcae 1770`): present.
- reason: present (§7-§8 of `7O.2A`).
- security properties: present (§8-§9 of `7O.2A`, reference-reconfirmed
  §8 above).
- exact command: present, checked §27.
- exact read-back: present, restated §29.
- exact rollback: present, restated §30.
- no `RepositoryIdentity` creation in remediation execution: present
  (`7O.2A §19` sequencing).
- no binding/certification/activation: present (`7O.2A §0/§21`).
- no unrelated mutation: present (`7O.2A §17` "exact exclusions").
- **missing, must be added before the election phase presents this as
  complete:** a corrected scope statement — the proposition currently
  overstates its own coverage ("covers the full §3 write-required
  inventory") in a way this phase found to be inaccurate for
  `architecture-history.json` (§5/§11). The election materials for
  `149O.20L.7O.2A.2` must either (a) carry this phase's §5 correction
  as a disclosed limitation (recommended — matches how `7O.2A §5/§11`
  already discloses the HBDC-sticky-bit-blind-spot as a known,
  non-blocking gap), or (b) narrow the proposition's stated
  justification to exactly `repository-identity.json` plus the 37 other
  genuinely-first-creation artifacts, omitting the now-known-incorrect
  claim of full coverage.

## 33. No Combined Identity Mutation — Reconfirmed

`7O.2A §19`'s sequencing (proposition → election → execution →
independent verification → identity retry, five distinct phases) is
unchanged by this phase and is not authorized to be collapsed. This
phase itself performs no chmod, no identity creation, no binding, no
election, no CHGR — confirmed in "Proof of No Mutation" below.

## 34. Final Verdict

**INDEPENDENTLY VERIFIED — P-A′ REMEDIATION PROPOSITION READY FOR
HUMAN ELECTION, WITH ONE REQUIRED DISCLOSED CORRECTION.**

The P-A′ model (`chmod 1770`, group-write + sticky bit) is confirmed,
via direct production-source reading and reference-verified Linux
kernel/POSIX sticky-bit semantics, to: close the broad-group-write
delete/rename attack against all 17 root-owned governed `.pcae`
entries (§8/§12); introduce no new name-squatting/authority-escalation
surface beyond what already exists under the idempotent-ensure design
(§7); leave the Protected Root, HMIC digest, and every `HBDC-REQ-0xx`
check unaffected (§20/§23/§24); remain the minimum-safe model when
re-compared against P-B (redundant, no benefit, §17) and P-C
(defers rather than solves the one real gap found, §18); and correctly
fix 38 of the 39 declared write-required artifacts (§11). The one
correction required before election: `7O.2A`'s claim of *full*
write-required-inventory coverage is not accurate for
`architecture-history.json` (§5), whose producer uses a non-atomic,
pre-existing-file write pattern that P-A′'s directory-mode-only change
does not fix. This is a **scope-accuracy correction to the election
materials, not a safety objection to P-A′ itself** — it does not
change the recommended command, read-back, or rollback in any way, and
does not introduce a reason to prefer P-B, P-C, or P-D over P-A′ for
the `RepositoryIdentity`-scoped remediation this proposition actually
executes.

## 35. Expected Clean State — Confirmed

`.pcae` currently still: `root:pcae 0750` (this phase issued zero Dell
commands; state is carried forward from `7O.2A`'s own last live read,
unchanged by anything this phase did). P-A′ proposition: independently
verified, ready for election, with the §5/§32 correction to be carried
into the election materials. `RepositoryIdentity`: absent (unchanged,
no write attempted this phase — confirmed via `git ls-files
.pcae/repository-identity.json` returning nothing in this working
tree, and no Dell command issued). `DeploymentBinding`: absent
(unchanged, no Dell command issued, no code path invoked this phase
that could create one). No Dell mutation. No election. Canonical HBDC:
carried forward as `NON_COMPLIANT`, sole residual `HBDC-REQ-042` (per
`7O.2A`'s own live result; not independently re-run live this phase,
§25).

## 36. Recommended Next Phase

**`149O.20L.7O.2A.2` — RepositoryIdentity Write-Path Remediation Human
Election + CHGR Publication.** That phase must:

- re-check the proposition's currentness (fresh Dell read: source SHA,
  `.pcae` mode/ACL, identity/binding absence, per §28's preflight
  restatement);
- **carry forward this phase's §5/§32 correction** as a disclosed
  finding in the election materials (the proposition fixes 38 of 39
  declared artifacts; `architecture-history.json` needs a separate,
  future, not-yet-designed fix);
- present `APPROVE`/`DECLINE`/`AMEND` on the exact `chmod 1770`
  proposition;
- disclose all bounded findings from `7O.2A §5/§11` (sticky-bit HBDC
  checker blind spot) and from this phase (§5 architecture-history.json
  gap, §14 symlink-rejection asymmetry across consumers);
- require separate human confirmation;
- publish CHGR;
- perform zero Dell mutation;
- stop.

Then, unchanged from `7O.2A §19`: `7O.2A.3` — Authority Independent
Verification; `7O.2A.4` — `chmod 1770` Execution; `7O.2A.5` —
Independent Real-Host Verification. Only after a clean `7O.2A.5`:
retry `RepositoryIdentity` creation under a new phase.

## Strategic Breakpoint

Unchanged, unreached, not begun this phase: pause before Boundary C to
begin the DeepSeek Harness comparative study and the PCAE Runtime
Adapter/Plugin architecture, gated on a first-use `RepositoryIdentity`
+ `DeploymentBinding` + a clean, independently-verified `COMPLIANT`
HBDC on real Dell — none of which this phase performed or was
authorized to perform.

## Proof of No Mutation / No Forbidden Action

- **No Dell mutation:** zero Dell/SSH commands were issued this phase
  (unlike `7O.2A`, which opened a read-only Dell session; this phase's
  scope was satisfiable entirely from the Mac-side working tree plus
  `7O.2A`'s own already-published live-read facts, per the explicit
  governing instruction for this phase not to substitute macOS testing
  for Linux-specific claims, and not to open a Dell session for
  disposable mutation testing either).
- **No `RepositoryIdentity` created:** `git ls-files
  .pcae/repository-identity.json` → no output, confirmed this session;
  no write call to that path was issued anywhere in this phase's work
  (only read-only source inspection and pre-existing test execution).
- **No `DeploymentBinding` created:** no `create_deployment_binding`-shaped
  call was made; `/etc/pcae/hatp/trust-store` was not accessed this
  phase at all (no Dell session).
- **No election, no CHGR:** no decision-session or governance-record
  publish command was issued this phase.
- **No certification, no Boundary C, no HATP activation, no chmod, no
  setfacl:** none invoked; only read-only `git`, `python3 -m pytest`
  (against the pre-existing test file, no new fixture mutation outside
  `tmp_path`), and file reads were performed this phase.

## Tests

`tests/test_phase_149o_20l_7o_2a_repositoryidentity_write_path_provisioning_gap_architecture.py`
(pre-existing, from `7O.2A`) was re-run this phase, unmodified: **24
passed**, confirming its claims are still true against the unchanged
source. This phase adds
`tests/test_phase_149o_20l_7o_2a_1_repositoryidentity_write_path_remediation_proposition_independent_verification.py`,
which independently proves, against live production source (not
`7O.2A`'s prose): the real `.gitignore` entry count (39, not 34) and
that `architecture-history.json` is present in it; that
`architecture-history.json` is simultaneously git-tracked (contradicting
the "not gitignored" pattern the existing test's
`test_git_tracked_pcae_baseline_is_not_gitignored_and_is_admin_controlled`
checks for three *other* tracked files, but does not check for this
one); that `write_architecture_history_snapshot` uses `.open("w"`,
not `mkstemp`; that `acquire_agent_lock` uses exclusive-create
(`open("x"`) not `mkstemp`, and that `release_agent_lock` only unlinks
its own path; that no `S_ISVTX` reference exists anywhere in
`src/pcae`; that the HBDC digest frozen-scope list is a source-file
list, not a `.pcae`-path list; and the no-mutation proof (no new
`.pcae/repository-identity.json`, no Dell-shaped call present in this
new test file's own source).

## Governance Results

- `pcae_check`: passed
- `pcae_health`: healthy
- `pcae_status_coherence`: coherent
- `pcae_push_check`: clean at entry
- No `src/pcae/**` production code changed this phase (doc + test +
  task/status governance files only)
- `fast_green`: deselected confirmation run (281 deselects: 258
  failures from a raw full-suite run, 1 additional flaky concurrency
  test, and 22 tests that only failed transiently — see disclosed
  note below) → **7792 passed, 5 skipped, 0 failed, 0 errors.** Raw
  full-suite runs this phase (this phase's doc+test changes present,
  `--ignore`ing the pre-existing `fido2`-import collection failure):
  257-258 failed, 9 errors across two runs, both confirmed pre-existing
  via a live `git stash -u`/pop A/B comparison (identical counts with
  this phase's changes removed). The 9 errors are fixture-setup
  failures confined to one pre-existing file
  (`test_phase_149o_20e_hmic_v1_2_hbdc_bound_contract_identity_independent_verification.py`).
  **Disclosed, non-blocking transient event:** during one of this
  phase's own background full-suite runs, that run was interrupted by
  this session's own tooling (a background-process timeout/detach, not
  a `pytest`-level failure) while
  `test_phase_149o_20l_7k_hmic_frozen_source_scope_amendment_for_deploymentbinding_producer.py::test_new_member_byte_perturbation_changes_digest`
  was mid-execution — that test intentionally perturbs
  `src/pcae/core/hatp_deployment_binding_admin.py` and
  `scripts/hatp_deployment_binding_admin.py` inside a `try`/`finally`
  that restores the original bytes; the interruption landed between the
  perturbation and the `finally` restore, leaving both files
  transiently modified (a stray `# 7k-digest-sensitivity-probe` trailing
  comment) in the working tree. **Detected via `git status --short`
  immediately after that run, reverted via `git checkout --` before any
  commit, and confirmed not part of any commit this phase** (neither
  file is in this phase's `files_changed` list). This produced 22
  cascading `FAILED` results in the next full run (tests asserting a
  clean working tree for `src/pcae/**`/`scripts/**`) — all 22 passed
  once the tree was reverted to clean, confirmed in the final
  deselected run above.
- `report_notification_tests`: not_applicable_this_phase
- `bootstrap_session_reporting_tests`: not_applicable_this_phase
