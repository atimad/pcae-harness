# Phase 149O.20L.7O.2B.1 -- RepositoryIdentity Creation Independent Real-Host Verification

## 1. Scope

Verification-only phase. Independently verifies the real-host
`RepositoryIdentity` created on `hac-dell` by Phase 149O.20L.7O.2B,
from primary production source and a fresh, read-only SSH session.
7O.2B's report, scripts, companion tests, prior SSH session, and
captured UUID are treated as non-authoritative claims to be
independently re-derived, not as an oracle.

No RepositoryIdentity created or replaced. No DeploymentBinding
created/rotated/revoked. No election initiated. No CHGR published. No
Protected Root mutation. No certification. No Boundary C. No HATP
activation. No Dell mutation of any kind -- every remote command this
phase issued was read-only (`stat`, `cat`, `ls`, `getfacl`, `find`,
`git rev-parse`/`status`, and a locally-authored, freshly-written
Python script that calls only `read_repository_identity`,
`validate_repository_identity_document`,
`derive_implementation_scope_digest`, and
`verify_class_b_deployment_conformance` -- never
`ensure_repository_identity` or any DeploymentBinding writer).

## 2. Phase-entry state

- Phase-entry commit: `a462d879` (Phase 149O.20L.7O.2B: close task,
  transition to idle).
- `pcae health`: healthy, all required files present, git status
  clean.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: pre-existing, unrelated warnings only
  (30 active-task-file / `tasks/DONE.md` sync warnings dating back to
  prior phases, none touching RepositoryIdentity/DeploymentBinding
  state; not repaired this phase -- out of scope).
- `pcae push check`: nothing to push (branch up to date with
  `origin/main`, working tree clean at phase entry).
- `pcae runtime inspect`: Runtime state Observed, execution capability
  unavailable, maximum plugin capability observe -- matches expected
  entering state, unchanged.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest`: showed 149O.20L.7O.2B's own
  self-reported values (identity `0107866f-af7c-40b4-8317-
  74e71acb05ca`, HBDC residual `HBDC-REQ-042` /
  `no_active_deployment_binding_matches_repository_and_root`) --
  recorded here as the claim under test, not trusted.
- `pcae phase-report reconcile --phase-id 149O.20L.7O.2B`: reconciled,
  inspection-only, no mutation.

## 3. Primary-source RepositoryIdentity contract reconstruction

Read fresh this phase, directly:
`src/pcae/core/repository_identity.py`.

Independently recovered (not derived from 7O.2B's prose):

- **Artifact path**: `.pcae/repository-identity.json`, relative to
  the `HarnessPath` root (`REPOSITORY_IDENTITY_RELATIVE_PATH`).
- **Closed field set**: exactly `schema_version`,
  `repository_instance_id`, `created_at`
  (`_REQUIRED_FIELDS = frozenset({...})`). `validate_repository_
  identity_document` raises `RepositoryIdentityMalformedError` on any
  unknown field, any missing field, or a `schema_version` other than
  the module constant `SCHEMA_VERSION = 1`.
- **UUID grammar**: `repository_instance_id` must parse as
  `uuid.UUID`, `version == 4`, and `str(parsed) == value.lower()`
  (canonical lowercase textual form, no normalization slack) --
  `is_valid_repository_instance_id`.
- **`created_at` grammar**: fail-closed ISO-8601 parse
  (`_parse_iso_timestamp`), timezone-aware only; the generator writes
  `"%Y-%m-%dT%H:%M:%S.%f"[:-3] + "Z"` (millisecond-precision,
  `Z`-suffixed).
- **Generation algorithm**: `_generate_repository_identity` ->
  `schema_version=1`, `repository_instance_id=str(uuid.uuid4())`,
  `created_at` as above.
- **Serializer**: `json.dumps(identity.to_dict(), indent=2,
  sort_keys=True) + "\n"`.
- **Read validation**: `read_repository_identity` rejects a symlinked
  target or symlinked parent (`_reject_symlink`), returns `None` only
  when the file is genuinely absent, and raises
  `RepositoryIdentityMalformedError` (never a silent partial result)
  on unreadable/non-JSON/schema-invalid content. Missing and malformed
  are deliberately distinct outcomes.
- **Unknown-field / malformed-file behavior**: fail closed, never
  auto-repaired or silently regenerated (module docstring, item 25 of
  the governing prompt lineage).
- **Symlink behavior**: refused, not followed, at both the target and
  its parent, both before *and* after the temp-file write in
  `_write_atomic` (double-check brackets the `os.replace`).
- **Idempotency semantics**: `ensure_repository_identity` calls
  `read_repository_identity` first; if it returns a non-`None` value,
  `ensure_repository_identity` returns it **immediately**, with zero
  writes -- the atomic-write path (`tempfile.mkstemp` + `fsync` +
  `os.replace`) is only reached when `existing is None`. This is a
  structural, source-level proof of read-only-in-effect behavior for
  an already-valid identity; no empirical re-invocation was needed or
  performed (see §17 disposition below).
- **Write mechanics**: `tempfile.mkstemp(prefix=".tmp-repository-
  identity-", dir=<same directory>)`, write, `flush`, `fsync`,
  `os.replace` (atomic rename), `finally`-block cleanup of any
  leftover temp name. `tempfile.mkstemp` creates the file `0600` by
  default -- the module performs no explicit `chmod`/`chown`; the
  `pcae:pcae 0600` mode on Dell is the OS default for the `pcae`
  process's `mkstemp` call, not a module-level mode directive.
- No import of HATP, the Permission Broker, RAE, or any authority
  concept anywhere in the module (independently re-read in full, not
  taken from the docstring claim).

Also read `src/pcae/core/hatp_class_b_conformance.py`
(`_check_deployment_identity`) to independently reconstruct the
reason-transition branch (see §9 below), and
`src/pcae/core/hatp_mandatory_certification.py` (location of
`derive_implementation_scope_digest`).

## 4. Fresh SSH session

A new SSH session to `hac-dell` was opened this phase (SSH connection
established directly by this phase's tooling; not a reattachment to
any session used by 7O.2B). All remote commands issued this phase --
listed individually in the sections below -- are read-only.
Passwordless `sudo -n -u pcae` was used to read files as the `pcae` OS
principal (matching the file's own owner) where required for access;
`sudo -n` was also used, unauthenticated read-only (`ls`/`stat`/
`getfacl`), to inspect `/etc/pcae` (root-owned tree).

## 5. Machine identity (freshly verified)

| Check | Observed | Expected |
|---|---|---|
| `hostname` | `atila-Latitude-E5470` | `atila-Latitude-E5470` |
| `/etc/machine-id` | `54ff22ce400b475aa0d55cb68f4a3334` | `54ff22ce400b475aa0d55cb68f4a3334` |
| `uname -m` | `x86_64` | (host arch, consistent with prior phases) |
| `/etc/os-release` | Ubuntu 24.04.3 LTS (noble) | consistent with prior phases |

No mismatch. Not blocking.

## 6. Source identity

```
git -c safe.directory=/opt/pcae/runtime/src rev-parse HEAD
```

Result: `b0840e96a7ffb12308e95828aa5927c3e7c770c0` -- matches expected
exactly.

- Detached HEAD: confirmed (`git symbolic-ref -q HEAD` fails).
- `git status --porcelain=v1`: empty -- tracked tree clean.
- No source mutation performed (read-only `git rev-parse`/`status`
  only; the `-c safe.directory=...` flag is a one-off, non-persistent
  override -- it does not write to any config file -- used in place of
  a `git config --global` mutation, deliberately, to avoid a
  collateral host config write).

## 7. `.pcae` topology

```
stat -c "%U:%G %a %F" /opt/pcae/runtime/src/.pcae
getfacl -p /opt/pcae/runtime/src/.pcae
realpath /opt/pcae/runtime/src/.pcae
readlink -f /opt/pcae/runtime/src
```

Result: `root:pcae 1770`, real directory, no extended/default ACL
(only standard `user::rwx` / `group::rwx` / `other::---` entries plus
the sticky flag `--t`), `realpath` resolves to the literal path
itself, no ancestor symlink redirection on `/opt/pcae/runtime/src`.
Matches expected `.pcae: root:pcae 1770` exactly. Permission-
remediation state (149O.20L.7O.2A.4/7O.2A.5) remains intact.

## 8. Exact RepositoryIdentity path, artifact bytes, and hash

Independently derived path (from §3, not copied from 7O.2B):
`/opt/pcae/runtime/src/.pcae/repository-identity.json`.

```
stat -c "%U:%G %a %F %s bytes mtime=%y" <path>
readlink -f <path>
stat -c "%h" <path>
cat <path>
sha256sum <path>
```

Results:

- Type: regular file, not a symlink (`readlink -f` resolves to the
  literal path).
- Link count: `1` (no unexpected hardlink).
- Owner:group / mode: `pcae:pcae 0600`.
- Size: 138 bytes. mtime: `2026-08-18 14:53:43.508343931 +0200`.
- SHA-256: `b1d9fd8e17b1333cc3b908383ee5036106880e32240648f77f152734775a9065`
- Raw bytes (verbatim):

```json
{
  "created_at": "2026-08-18T12:53:43.508Z",
  "repository_instance_id": "0107866f-af7c-40b4-8317-74e71acb05ca",
  "schema_version": 1
}
```

Canonical field names present, sorted-key JSON, matches the
`_write_atomic`/serializer contract in §3 exactly (`json.dumps(...,
indent=2, sort_keys=True) + "\n"`).

## 9. Exact identity value, UUID semantics, schema validation

Parsed through the actual production reader
(`read_repository_identity`) and re-validated explicitly against the
raw JSON via `validate_repository_identity_document`, both invoked
live on `hac-dell` as the `pcae` principal (read-only):

- `repository_instance_id`: `0107866f-af7c-40b4-8317-74e71acb05ca` --
  matches expected exactly. No mismatch; nothing to block.
- UUID version: `4` (`uuid.UUID(...).version == 4`).
- Canonical textual representation: `str(uuid.UUID(...)) ==
  repository_instance_id` -- `True`, no normalization discrepancy.
- `is_valid_repository_instance_id(...)`: `True`.
- `schema_version`: `1`, matches `SCHEMA_VERSION`.
- Field set: exactly `{created_at, repository_instance_id,
  schema_version}` -- no unknown field, no missing field.
- `validate_repository_identity_document` re-run explicitly on the
  raw parsed JSON (not just the already-validated `read_repository_
  identity` return value): re-validated `repository_instance_id`
  matches the first read exactly. No malformed-serialization finding.

## 10. File metadata / parent-child trust relationship

- Identity file: `pcae:pcae 0600` -- matches the current producer
  behavior (OS-default `mkstemp` mode, per §3; independently derived
  from source, not merely observed).
- Parent `.pcae`: `root:pcae 1770` (§7).
- This is the intended RI-D topology: an admin-owned, sticky,
  agent-writable-within-directory parent containing an
  agent(`pcae`)-owned, agent-only-readable child artifact. Ownership
  of the identity file by `pcae` is a filesystem fact only -- it does
  not, by itself, confer any binding/certification authority
  (HATP-REQ-051/063, HBDC-REQ-068; see §16).

## 11. Temp-file residue

Directory listing of `/opt/pcae/runtime/src/.pcae/` shows no entry
matching the canonical producer pattern `.tmp-repository-identity-*`.
Confirmed via both a direct `grep` filter and full `ls -la` review of
the directory contents. No unrelated host temp-state scan performed
(out of scope per phase instructions).

## 12. Idempotency

Per §3's source-level proof, `ensure_repository_identity` performs
**zero writes** whenever `read_repository_identity` already returns a
valid identity -- it returns immediately after the read. Because this
was proven from primary source before any remote action, and the
persisted identity independently validates (§9), this phase did
**not** invoke `ensure_repository_identity` at all -- read-only
verification (`read_repository_identity` +
`validate_repository_identity_document`) fully discharges the
idempotency requirement without incurring any mutation risk. No
before/after SHA-256/mtime/inode/UUID comparison across an
`ensure_repository_identity` call was needed or performed, consistent
with the phase instruction that a verification phase must not risk
mutation merely to prove idempotency when source-level proof already
suffices.

## 13. Single durable identity

```
sudo -n -u pcae find /opt/pcae -name repository-identity.json
sudo -n -u pcae find /etc/pcae -name repository-identity.json
```

Result: exactly one match, the canonical path itself, under
`/opt/pcae`; none under `/etc/pcae`. Search scoped narrowly to known
PCAE deployment paths, per phase instructions -- no broader host scan.
(The `find` invocations emitted a benign `Failed to restore initial
working directory: /home/codex: Permission denied` stderr line, an
artifact of the `sudo -n -u pcae env -i ... python3` subprocess's
`cwd` handling under the SSH login shell's own home directory
permissions -- it did not affect `find`'s stdout result or perform
any write.)

## 14. Git cleanliness

`git status --porcelain=v1` on `/opt/pcae/runtime/src` (as `pcae`,
with the one-off `safe.directory` override): empty. Consistent with
`RepositoryIdentity` living under `.pcae/`, which the repository's
`.gitignore` excludes (confirmed present as
`/opt/pcae/runtime/src/.pcae/.gitignore`, listed in the directory
inventory in §13's `find` context and previously established in
6E/7O.2A phases as covering `.pcae/*` runtime-local state). Git
cleanliness is treated as corroborating evidence only, not as proof of
identity validity -- validity was independently established in §9
through the production schema reader.

## 15. HMIC digest

Invoked live, read-only: `derive_implementation_scope_digest(root)`
via the freshly authored verification script (imported from
`/opt/pcae/runtime/src/src`, the deployed, drift-free tree confirmed
current in §6).

Result: `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8`
-- matches expected exactly. RepositoryIdentity presence/creation has
no effect on implementation/source identity (the digest is unchanged
from the phase-entry expected value and from 7O.2B's own prior
report).

## 16. DeploymentBinding absence / Protected Root / certification absence

```
sudo -n ls -la /etc/pcae/hatp/trust-store
sudo -n stat -c "%U:%G %a %F" /etc/pcae/hatp/trust-store
sudo -n getfacl -p /etc/pcae/hatp/trust-store
sudo -n find /etc/pcae -maxdepth 3 -printf "%p %u:%g %m %y\n"
```

Results:

- `/etc/pcae/hatp/trust-store`: empty (only `.`/`..` entries), owner
  `root:pcae`, mode `750`, no extended/default ACL beyond the
  standard three entries. No `DeploymentBinding` artifact present.
- Full `/etc/pcae` tree to depth 3: `/etc/pcae` (`root:root 755`),
  `/etc/pcae/hatp` (`root:root 755`), `/etc/pcae/hatp/trust-store`
  (`root:pcae 750`) -- unchanged from the expected/prior-verified
  baseline.
- Because `CertificationRecord`/`CertificationBinding` documents are
  the same trust-store's contents (per `hatp_mandatory_certification.
  py`'s persistence model, independently read this phase), an empty
  trust-store directory is direct, sufficient evidence of certification
  absence as well as `DeploymentBinding` absence -- no separate
  certification-specific artifact path exists to check.

No create/preview mutation path was called against the trust store;
only `ls`/`stat`/`getfacl`/`find` (root-level read-only) were used.

## 17. Canonical HBDC (run live, twice, for determinism)

Invoked live, read-only, via the same freshly authored script:
`verify_class_b_deployment_conformance(root)`, called twice
sequentially in one process.

**Run 1** -- overall: `NON_COMPLIANT`. 34 total checks. 33
`satisfied=True`; sole failing check:

```
HBDC-REQ-042  False  no_active_deployment_binding_matches_repository_and_root
```

`HBDC-REQ-036` (`launcher_agent_unwritable`): `True`. Every other
check `True` (full 34-row table captured in the phase transcript;
identical requirement-ID/status/reason set to 7O.2B's self-reported
run, now independently re-derived rather than trusted).

**Run 2** -- overall: `NON_COMPLIANT`, same status. Programmatic
comparison of `(check_id, satisfied, status)` across both runs:
identical (`run1_run2_identical: True`).

## 18. Reason-transition semantics (source-proven, not merely observed)

Read `_check_deployment_identity` in
`src/pcae/core/hatp_class_b_conformance.py` directly. The function:

1. Resolves the canonical deployment root.
2. Calls `read_repository_identity(root)`.
   - If it returns `None` -> `ClassBCheckResult("HBDC-REQ-042", False,
     "no_repository_identity_present", ...)`.
3. If an identity is present, loads the production `HATPTrustStore`
   and looks up `load_repository_enrollment(identity.
   repository_instance_id)`, then checks
   `deployment_binding_matches(binding, repository_id=..., 
   canonical_deployment_root=...)`.
   - If it does not match (including the "no binding at all" case) ->
     `ClassBCheckResult("HBDC-REQ-042", False,
     "no_active_deployment_binding_matches_repository_and_root", ...)`.
   - Only an exact match yields
     `"deployment_binding_matches_repository_and_root"`, `satisfied=True`.

This is the exact branch that fired on Dell: `read_repository_identity`
now returns a non-`None`, independently-validated identity (§9), so
control reaches the binding-match branch; the (independently
confirmed, §16) empty trust store means no matching binding exists,
producing `no_active_deployment_binding_matches_repository_and_root`
-- not `no_repository_identity_present`. Verified from the actual
consumer branch/logic, not merely by observing the returned string.

## 19. HBDC-REQ-068 / RepositoryIdentity authority semantics

Re-read HBDC-REQ-068 (`docs/PHASE_149O_20L_7G_...md` and
`docs/PHASE_149O_20L_7I_...md`, both independently located this
phase):

> Repository identity (Layer 1) creation is not itself gated by this
> section's election requirement (HBDC-REQ-056..066 govern
> `DeploymentBinding` only); nothing in this amendment alters
> HATP-REQ-048's existing disposition that repository-identity
> creation confers no authority and needs no approval.

Confirmed, from this text plus the independently re-read source (§3,
§18):

- RepositoryIdentity existence does **not** grant authority.
- It does **not** make HBDC compliant (§17: `NON_COMPLIANT` with the
  identity present).
- It does **not** permit execution (Runtime remains
  Observed/observe/unavailable, §21).
- It does **not** satisfy the `DeploymentBinding` requirement
  (`HBDC-REQ-042` remains failing, for a *different* reason than
  before, but still failing).

RI-D semantics (RepositoryIdentity present != independently verified;
verified != authorized; instance ID != permission; identity
prerequisite != authority) held intact throughout this phase. No
binding-proposition work was begun.

## 20. Mutation inventory (independent reconstruction)

From filesystem metadata gathered this phase (§7, §8, §11, §13, §16):

- Exactly one `RepositoryIdentity` artifact exists, at the canonical
  path, with link count 1 (consistent with a single atomic
  create-then-rename, not an in-place edit or hardlink).
- No temp-file residue matching the producer's pattern remains (§11)
  -- consistent with the `finally`-block cleanup in `_write_atomic`
  having run to completion after a successful `os.replace`.
- mtime (`2026-08-18 14:53:43 +0200`) is a single point in time, not
  multiple distinct mtimes across retries.
- No `DeploymentBinding` exists (§16).
- No source mutation (`git status --porcelain` empty, §6, both this
  phase and consistent with 7O.2B's own report).
- No `chmod`/`chown`/`setfacl` evidence: `.pcae`'s mode/owner (§7) and
  the trust-store's mode/owner (§16) match the pre-established
  baseline exactly; the identity file's own `pcae:pcae 0600` is
  accounted for by `mkstemp`'s OS-default mode (§3, §10), not a
  separate `chmod` call (no `chmod`/`chown`/`os.chmod`/`os.chown` call
  exists anywhere in `repository_identity.py`, independently confirmed
  by reading the full file).
- No Protected Root mutation (§16, unchanged tree).

This is consistent with, and does not contradict, 7O.2B's own claimed
mutation inventory -- but was reconstructed independently from
current filesystem evidence and source, not copied from that report.
No host audit/journal facility was consulted (none was needed; the
available filesystem evidence was sufficient and broad host forensics
were out of scope per phase instructions).

## 21. Permission-remediation relation / architecture-history.json

- `.pcae`'s `root:pcae 1770` topology (§7) is the same topology this
  identity creation occurred under -- confirmed by inspecting it
  fresh this phase, not merely citing 149O.20L.7O.2A.4/7O.2A.5.
  P-A' is not reopened; no new evidence contradicts it.
- `architecture-history.json` (present in the `.pcae` directory
  listing gathered in §13's `find` context, `854` bytes, dated `Aug
  15 12:06` -- unchanged mtime, predating this phase and 7O.2B's own
  identity-creation mtime of `14:53:43` on `Aug 18`) was not written by
  this identity creation. P-A's separate write-pattern issue with
  `architecture-history.json` is carried forward unchanged and is not
  repaired here (out of scope, per phase instructions).

## 22. Sticky-bit evidence qualification

Restated precisely, per phase instructions: the successful
RepositoryIdentity creation (by 7O.2B, independently corroborated by
this phase's filesystem evidence) empirically demonstrates only that
the `pcae` principal can create a `pcae`-owned file under a `.pcae`
directory with mode `1770`. It does **not** empirically demonstrate
sticky-bit protection of *root-owned* files from unlink/rename by a
non-owning principal -- no root-owned file under `.pcae` was created,
deleted, or renamed by any principal other than its owner during this
observation window. That specific protection claim remains
reference-verified (from POSIX sticky-bit semantics and prior
phases' architectural review) rather than empirically re-tested this
phase or by 7O.2B.

## 23. Runtime state

`pcae runtime inspect` (local) confirmed unchanged:
`Observed / observe / unavailable`, execution capability unavailable,
maximum plugin capability observe, registry empty. No activation
performed or implied by this phase.

## 24. Final verdict

**INDEPENDENTLY VERIFIED -- REPOSITORYIDENTITY MATERIALIZATION
COMPLETE**

No mismatch was found against any expected value in the phase prompt.
Every check in §5-§23 either matched the expected value exactly or was
independently derived from primary source and cross-confirmed against
live, freshly-observed remote state.

## 25. Clean-outcome summary

- RepositoryIdentity: PRESENT / INDEPENDENTLY VERIFIED.
- `repository_instance_id`: `0107866f-af7c-40b4-8317-74e71acb05ca`.
- UUID: v4, canonical form.
- File: `pcae:pcae 0600`.
- `.pcae`: `root:pcae 1770`.
- DeploymentBinding: ABSENT.
- Protected Root: UNCHANGED / EMPTY.
- Source: `b0840e96a7ffb12308e95828aa5927c3e7c770c0`, UNCHANGED.
- HMIC digest: `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8`, UNCHANGED.
- HBDC: NON_COMPLIANT, sole residual `HBDC-REQ-042`, reason
  `no_active_deployment_binding_matches_repository_and_root`.
- Runtime: Observed / observe / unavailable.

## 26. Recommended next phase

**149O.20L.7O.2C -- DeploymentBinding First-Use Field Resolution
Architecture**, per the phase prompt's own §36 direction: resolve
`principal_id`, `signer_key_id`, `provider_profile`, and
`authority_scope` from primary architecture and actual Dell state,
using the now-exact independently verified `repository_instance_id`
(`0107866f-af7c-40b4-8317-74e71acb05ca`); must not invent values;
must determine whether existing signer/provider prerequisites suffice
or new provisioning architecture is required; must not initiate an
election unless all fields are canonically resolved and a separately
verified proposition phase is reached. The strategic breakpoint
(pause before Boundary C, then DeepSeek Harness comparative study and
PCAE Runtime Adapter/Plugin Architecture) is preserved and not begun
here.

## 27. Governance / tests / commits / push

- No raw `git commit`/`push`; no `--no-verify`; no force push; no
  bypass.
- No Dell mutation of any kind this phase (all remote commands
  read-only, enumerated above).
- Local governed checks: `pcae health` healthy, `pcae check` passed,
  `pcae status coherence` coherent.
- Tests: `python -m pytest -n auto` run this phase (see fast_green /
  full-suite results recorded in the phase-completion report).
- Commits, pushed status, and `origin/main..HEAD` are recorded in the
  canonical phase-completion report generated by `pcae phase
  complete`.
