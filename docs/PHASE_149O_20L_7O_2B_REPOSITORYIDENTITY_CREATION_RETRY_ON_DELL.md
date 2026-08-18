# Phase 149O.20L.7O.2B -- RepositoryIdentity Creation Retry on Dell

## 1. Scope

Real-host mutation phase. Retries the previously blocked first
RepositoryIdentity creation on `hac-dell`, now that the `.pcae`
write-path remediation (`root:pcae 1770`) has been human-authorized,
independently authority-verified, executed (149O.20L.7O.2A.4), and
independently re-verified on the real host (149O.20L.7O.2A.5).

Exactly one canonical `ensure_repository_identity()` call was
performed as the `pcae` OS principal, followed by mandatory read-back
and verification. No DeploymentBinding was created. No election was
initiated. No certification occurred.

## 2. Phase-entry state

- Phase-entry commit: `62a202d0` (Phase 149O.20L.7O.2B: open task for
  RepositoryIdentity creation retry on Dell).
- `pcae check`: passed.
- `pcae health`: healthy, all required files present, git status
  clean.
- Active task reconciled with 149O.20L.7O.2A.5 (prior idle placeholder
  closed, dedicated `Phase 149O.20L.7O.2B` task opened).
- No production-source modification made locally this phase.

## 3. Source-currentness gate

Compared local Mac `HEAD` against the deployed candidate SHA
`b0840e96a7ffb12308e95828aa5927c3e7c770c0` across all authority-bearing
paths:

```
git diff --stat b0840e96a7ffb12308e95828aa5927c3e7c770c0 HEAD -- \
  src/pcae/ scripts/ docs/contracts/ schemas/ pyproject.toml
```

Result: empty diff. No drift. Safe to proceed against the currently
deployed candidate; identity was not created against stale source.

## 4. Re-derived identity-only operation

Read `src/pcae/core/repository_identity.py` and
`src/pcae/commands/init.py` fresh this phase (not copied from 7O.2's
plan).

Confirmed:

- `ensure_repository_identity(root: HarnessPath) -> RepositoryIdentity`
  is idempotent ensure/create: existing valid identity returned
  unchanged; missing identity generated atomically
  (`tempfile.mkstemp` + `fsync` + `os.replace`, same directory);
  malformed identity fails closed (`RepositoryIdentityMalformedError`),
  never silently regenerated.
- The module imports nothing from HATP, the Permission Broker, RAE, or
  any other authority concept (frozen invariant, HATP-REQ-051/063) --
  independently confirmed by reading the full file, not merely its
  docstring claim.
- `pcae init` (`commands/init.py::run_init`) performs materially
  broader mutations (writes missing template files via
  `write_missing_files`, installs Git hooks) in addition to calling
  `ensure_repository_identity`. It was **not** used.
- Narrowest safe production operation: a direct
  `ensure_repository_identity(HarnessPath(Path("/opt/pcae/runtime/src")))`
  call, `HarnessPath` being a trivial frozen dataclass wrapper
  (`src/pcae/core/paths.py`) with no side effects of its own.

## 5. Executing principal

Re-confirmed live topology: `pcae` OS principal (uid 1004, gid 1004,
group `pcae`) exists on `hac-dell`. Administrative `sudo` (passwordless
for the `codex` SSH user) was used only to enter the `pcae` principal
context via `sudo -n -u pcae env -i ...`, never to run the operation as
root or as `codex` directly.

## 6. Fresh Dell preflight (pre-mutation)

New SSH session. All checks independently re-derived, none trusted
from a prior phase's report:

| Check | Result |
|---|---|
| hostname | `atila-Latitude-E5470` (expected) |
| machine-id | `54ff22ce400b475aa0d55cb68f4a3334` (expected) |
| deployed source SHA | `b0840e96a7ffb12308e95828aa5927c3e7c770c0` (expected) |
| detached HEAD | yes |
| tracked tree clean | yes (`git status --porcelain=v1` empty) |
| `.pcae` owner:group mode | `root:pcae 1770` (expected) |
| `.pcae` extended/default ACL | none (`getfacl -p` shows only standard `user::`/`group::`/`other::` entries) |
| RepositoryIdentity file | absent |
| temp identity residue | none |
| DeploymentBinding / trust-store | empty (only `.`/`..`, dated Aug 15) |
| certification artifacts | none found under `.pcae` or `/etc/pcae` |
| Protected Root | unchanged |
| HMIC digest (live) | `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` (expected, matches exactly) |
| canonical HBDC (run 1) | `NON_COMPLIANT`, sole residual `HBDC-REQ-042` / `no_repository_identity_present`, `HBDC-REQ-036` True, 34 total checks |
| canonical HBDC (run 2, determinism) | identical to run 1 |

No mismatch found. Proceeded.

HMIC digest and HBDC diagnostic were invoked via disposable,
locally-authored, read-only Python scripts (`sys.path.insert(0,
"/opt/pcae/runtime/src/src")`, then
`derive_implementation_scope_digest(HarnessPath(Path("/opt/pcae/runtime/src")))`
and
`verify_class_b_deployment_conformance(HarnessPath(Path("/opt/pcae/runtime/src")))`
respectively), `scp`'d to `/tmp` on `hac-dell`, executed as:

```
sudo -n -u pcae env -i \
  PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  HOME=/home/pcae PYTHONNOUSERSITE=1 \
  python3 /tmp/<script>.py
```

## 7. Path safety

Exact identity target: `/opt/pcae/runtime/src/.pcae/repository-identity.json`.

- Absent: confirmed.
- Not a symlink: confirmed.
- No temp-file residue (`.tmp-repository-identity-*`): confirmed.
- Parent `.pcae`: real directory (`stat -c %F` -> `directory`, not a
  symlink).
- `realpath /opt/pcae/runtime/src/.pcae` == the literal path itself;
  `readlink -f /opt/pcae/runtime/src` == the literal path itself. No
  ancestor symlink redirection.

## 8. Independent command safety review

Reviewed the exact invocation before mutation:

```python
sys.path.insert(0, "/opt/pcae/runtime/src/src")
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity
identity = ensure_repository_identity(HarnessPath(Path("/opt/pcae/runtime/src")))
```

Confirmed:

- Imports the deployed production module tree at
  `/opt/pcae/runtime/src/src` (the currently-verified, drift-free
  SHA), not the local Mac checkout.
- `root` argument is exactly `/opt/pcae/runtime/src`.
- Operation is only `ensure_repository_identity` -- no `pcae init`, no
  template writes, no hook installation.
- Executed as `pcae` (`sudo -n -u pcae`).
- No binding/trust-store import or call anywhere in
  `repository_identity.py` (independently re-confirmed by reading the
  full file, not trusting its docstring alone).

No objection. Proceeded.

## 9. Single creation attempt

Executed exactly once:

- Invoking principal: `pcae` (confirmed via `sudo -n -u pcae whoami`
  immediately prior).
- Exact command: `sudo -n -u pcae env -i PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin HOME=/home/pcae PYTHONNOUSERSITE=1 python3 /tmp/ri_create.py`.
- Exit status: `0`.
- Timestamp bracket: `2026-08-18T12:53:43.429Z` (before) /
  `2026-08-18T12:53:43.524Z` (after); `created_at` recorded by the
  producer as `2026-08-18T12:53:43.508Z`.
- Result printed: `repository_instance_id: 0107866f-af7c-40b4-8317-74e71acb05ca`,
  `schema_version: 1`.

No failure occurred; the failure-before-retry adjudication procedure
(§12 of the governing prompt) was not exercised.

## 10. Immediate success read-back

Read the canonical artifact immediately after the creation call:

```
{
  "created_at": "2026-08-18T12:53:43.508Z",
  "repository_instance_id": "0107866f-af7c-40b4-8317-74e71acb05ca",
  "schema_version": 1
}
```

- Path: `/opt/pcae/runtime/src/.pcae/repository-identity.json`.
- SHA-256: `b1d9fd8e17b1333cc3b908383ee5036106880e32240648f77f152734775a9065`.
- Owner:group: `pcae:pcae`.
- Mode: `600`.
- File type: regular file.
- Symlink state: not a symlink.

## 11. Expected file metadata

Producer uses `tempfile.mkstemp` (creates with mode `0600` by
default) + `os.fsync` + `os.replace`, run as the `pcae` principal.
Actual result matches production behavior exactly: `pcae:pcae 0600`,
regular file.

## 12. UUID verification

```python
uuid.UUID('0107866f-af7c-40b4-8317-74e71acb05ca')
# version: 4
# str(v) == '0107866f-af7c-40b4-8317-74e71acb05ca': True
```

Syntactically valid UUID, version 4, exactly one persisted value. Not
regenerated or normalized.

## 13. Idempotency verification

Invoked the identical safe `ensure_repository_identity` operation one
additional time (current producer semantics still guarantee
idempotency per §12 of `repository_identity.py`):

- Second call returned the same `repository_instance_id`
  (`0107866f-af7c-40b4-8317-74e71acb05ca`) and the same `created_at`.
- File SHA-256 after the second call: unchanged
  (`b1d9fd8e17b1333cc3b908383ee5036106880e32240648f77f152734775a9065`).
- File mtime after the second call: unchanged
  (`2026-08-18 14:53:43.508343931 +0200`, matching the original
  `created_at` to the millisecond).

No file replacement, no second identity generation. Not blocking.

## 14. Identity generation count

Established from persisted-artifact evidence (SHA-256 and mtime
stability across both calls), not inferred from function return values
alone: exactly one durable RepositoryIdentity value exists.

## 15. Git cleanliness

- `HEAD` on `hac-dell`: still `b0840e96a7ffb12308e95828aa5927c3e7c770c0`.
- Detached: yes.
- Tracked tree: clean (`git status --porcelain=v1` empty).
- Identity file: covered by `.pcae/.gitignore`
  (`repository-identity.json` entry present), so it is ignored
  exactly as intended -- not a tracked-source mutation.
- No tracked source bytes changed.

## 16. HMIC digest (post-mutation)

Recomputed live (same disposable script as §6, re-scp'd and re-run
after mutation):

```
65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8
```

Unchanged from pre-mutation baseline. RepositoryIdentity creation had
no effect on the HMIC implementation-scope digest, consistent with
RepositoryIdentity remaining outside HMIC implementation/source
identity.

## 17. DeploymentBinding absence

```
sudo -n ls -la /etc/pcae/hatp/trust-store
  total 8
  drwxr-x--- 2 root pcae 4096 Aug 15 08:55 .
  drwxr-xr-x 3 root root 4096 Aug 15 08:55 ..
```

Still empty. No producer create/rotate/revoke invoked this phase.

## 18. Certification absence

`find /opt/pcae/runtime/src/.pcae -iname '*certif*'` and
`find /etc/pcae -iname '*certif*'`: both empty. Still absent.

## 19. Protected Root

`/etc/pcae/hatp/trust-store`: owner `root:pcae`, mode `750`, no
extended ACL, contents unchanged (still only `.`/`..`, dated Aug 15,
predating this phase). Read-only verified, not touched.

## 20. Canonical HBDC after identity creation

Run 1 (post-mutation):

```
status: ClassBConformanceStatus.NON_COMPLIANT
failing checks: [('HBDC-REQ-042', 'no_active_deployment_binding_matches_repository_and_root')]
HBDC-REQ-036: True
total checks: 34
```

Run 2 (determinism, immediately after):

```
status: ClassBConformanceStatus.NON_COMPLIANT
failing checks: [('HBDC-REQ-042', 'no_active_deployment_binding_matches_repository_and_root')]
HBDC-REQ-036: True
total checks: 34
```

Identical across both runs. `HBDC` remains `NON_COMPLIANT` as
expected; sole residual `HBDC-REQ-042` transitioned exactly from
`no_repository_identity_present` (pre-mutation) to
`no_active_deployment_binding_matches_repository_and_root`
(post-mutation) -- the expected production vocabulary for "identity
now present, binding still missing." `HBDC-REQ-042` did not
unexpectedly become `True`. No other requirement failed. All other 33
checks remained `True` in both runs.

## 21. HBDC determinism

Confirmed identical across two consecutive runs both pre- and
post-mutation (four total runs, §6 and §20).

## 22. RepositoryIdentity authority wall

Status: **REPOSITORYIDENTITY MATERIALIZED**. This creation confers no
authority, requires no HBDC-REQ-068 human approval, and does not by
itself change HBDC compliance. It is not described as authorized,
permitted, certified, or activated.

## 23. Frozen repository_id for evidence

`repository_instance_id = 0107866f-af7c-40b4-8317-74e71acb05ca` is the
exact, sole, canonical value now persisted on `hac-dell`. This is the
only `repository_id` acceptable for the later DeploymentBinding
proposition. No new identity was or should be created for that
phase's convenience.

## 24. Binding field resolution

Deliberately **not** performed this phase. `principal_id`,
`signer_key_id`, `provider_profile`, and `authority_scope` remain
unresolved, per 7O.1's independent finding. Left for a dedicated
future phase.

## 25. architecture-history.json

Not touched. Its separate, previously-identified producer-semantics
issue remains deferred, unchanged, and outside this phase's scope.

## 26. Sticky-bit qualification

This phase's successful file creation only demonstrates that `pcae`
can create its own allowed runtime-local file under a `1770`-mode
directory it has group write access to. It does **not** empirically
verify sticky-bit unlink/rename protection against other principals;
that remains reference-verified only, pending a separate empirical
test.

## 27. Mutation inventory

Exactly the expected real-host mutations, no others:

1. Creation of `/opt/pcae/runtime/src/.pcae/repository-identity.json`
   (one atomic `tempfile.mkstemp` + `fsync` + `os.replace` cycle).
2. Producer's temporary file (`.tmp-repository-identity-*`),
   transient, replaced by the atomic rename -- no residue confirmed
   both immediately after creation (§10) and after the idempotent
   re-invoke (§13).
3. Metadata intrinsic to that atomic creation (owner `pcae:pcae`, mode
   `0600`, mtime).

The second (idempotent) `ensure_repository_identity` call performed no
new mutation -- it read existing valid state and returned it
unchanged, confirmed by unchanged SHA-256 and mtime. Not counted as a
second mutation.

No DeploymentBinding create/rotate/revoke. No Protected Root mutation.
No certification. No Boundary A/C activity. No HATP activation. No
source fetch/checkout. No chmod/chown/ACL change. No venv/wrapper
change. No Permission Broker change. No unrelated Dell mutation.

## 28. Final verdict

**REPOSITORYIDENTITY MATERIALIZED SUCCESSFULLY -- INDEPENDENT VERIFICATION PENDING**

## 29. Resulting state

- RepositoryIdentity: **PRESENT** --
  `repository_instance_id = 0107866f-af7c-40b4-8317-74e71acb05ca`.
- Metadata: canonical (`schema_version: 1`, valid ISO-8601
  `created_at`, closed field set, `pcae:pcae 0600`).
- DeploymentBinding: **ABSENT**.
- HBDC: **NON_COMPLIANT**, sole residual `HBDC-REQ-042`, reason
  `no_active_deployment_binding_matches_repository_and_root`.
- HMIC digest: unchanged
  (`65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8`).
- Source: unchanged (`b0840e96a7ffb12308e95828aa5927c3e7c770c0`,
  detached, clean).
- Runtime: Observed / observe / unavailable (unchanged; not probed
  further this phase).

## 30. Tests

No `src/pcae/**` files were modified this phase (real-host operational
phase only). Local Fast Green suite re-run at phase close to confirm
no regression from task-lifecycle file changes:

```
pytest -m fast_green
```

(See governance results below for the recorded outcome used in the
canonical trust fields.)

## 31. Governance results

- `pcae check`: passed.
- `pcae health`: healthy.
- Local governed task lifecycle used throughout (`pcae task
  transition`, `pcae task update --allowed-file ...`, `pcae commit
  implementation`) -- no raw `git commit`, no `--no-verify`, no force
  push, no bypass.
- No `pcae init`, DeploymentBinding, certification, Boundary A/C, or
  HATP activation command was ever invoked, locally or on Dell.

## 32. Commits

- `62a202d0` -- Phase 149O.20L.7O.2B: open task for RepositoryIdentity
  creation retry on Dell.
- (this report and phase-completion metadata commit(s) follow.)

## 33. Pushed status / origin/main..HEAD

To be confirmed at push time via `pcae push check` / `pcae push`; see
phase-completion metadata for the final trust-field values.

## 34. Recommended next phase

**149O.20L.7O.2B.1 -- RepositoryIdentity Creation Independent
Real-Host Verification.**

Independently, from a fresh SSH session, without trusting this
report, this phase's read-backs, or its scripts as an oracle, re-verify:

- exact `repository_id` (`0107866f-af7c-40b4-8317-74e71acb05ca`);
- UUID version and format;
- serialization/schema;
- owner/group/mode;
- idempotency;
- Git cleanliness;
- HMIC digest;
- HBDC reason transition;
- DeploymentBinding absence;
- Protected Root;
- mutation inventory.

Only after a clean 7O.2B.1 should a dedicated DeploymentBinding
field-resolution/proposition phase begin. Binding field resolution
(`principal_id`, `signer_key_id`, `provider_profile`,
`authority_scope`) is explicitly not performed here.

## Strategic breakpoint (carried forward, unchanged)

After eventual DeploymentBinding first-use execution and clean
independent real-host verification yields the expected HBDC state,
pause before Boundary C. Then begin:

1. DeepSeek Harness vs PCAE Comparative Architecture Study.
2. PCAE Runtime Adapter + Plugin Architecture.

Not begun here.
