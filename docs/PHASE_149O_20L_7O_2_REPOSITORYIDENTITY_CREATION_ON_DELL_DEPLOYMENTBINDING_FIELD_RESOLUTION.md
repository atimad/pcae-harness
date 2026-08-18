# Phase 149O.20L.7O.2 — RepositoryIdentity Creation on Dell + DeploymentBinding Field Resolution / Proposition Drafting

## 0. Status

**Attempted real mutation on `hac-dell`; failed safely, no state change.** One, and only one, mutation was attempted: a direct call to the canonical `ensure_repository_identity(root)` (`src/pcae/core/repository_identity.py`), executed as the `pcae` OS principal against the real deployed checkout at `/opt/pcae/runtime/src`. It raised `PermissionError` before any bytes were written. No `DeploymentBinding` field resolution/proposition drafting was reached, since it depends on a materialized `repository_id` that was never produced. No `DeploymentBinding` create/rotate/revoke, no certification, no Boundary C/A, no HATP activation, no election, no CHGR — none attempted.

**Phase-entry commit:** `1de42d49` (`Phase 149O.20L.7O.1: sync active task after phase-complete staging`). `origin/main == HEAD`, 0 commits ahead/behind, working tree clean at entry.

## 1. Entry Checks (read-only)

```
git status --short                    → (clean)
git status --branch --short           → ## main...origin/main
git rev-parse HEAD                    → 1de42d49728fe76998090668b303bccd77062e88
git rev-list --count origin/main..HEAD → 0
pcae health                           → healthy, git clean
pcae check                            → passed
pcae status coherence                 → coherent
pcae doctor task-memory               → warnings (pre-existing, unrelated — same historical
                                          tasks/done/ vs DONE.md sync gap carried forward from
                                          7O/7O.1; outside this phase's allowed-file scope)
pcae push check                       → clean, nothing_to_push
pcae runtime inspect                  → Observed / observe / unavailable
pcae notify status                    → telegram configured/enabled
pcae phase-report show --latest       → 149O.20L.7O.1 canonical report; recommended next phase =
                                          149O.20L.7O.2 (this phase)
pcae phase-report reconcile --phase-id 149O.20L.7O.1
                                       → reconciled, 2 generations promoted, marker
                                          already_dispatched, checkpoint completed, receipt
                                          finalized, mutation: none
```

## 2. Source-Currentness Gate

```
git diff --stat b0840e96a7ffb12308e95828aa5927c3e7c770c0..HEAD -- src/pcae/ scripts/ docs/contracts/ schemas/ pyproject.toml
  → (no output)
```

Zero authority-bearing drift between the deployed candidate SHA and Mac HEAD. Proceeded.

## 3. Independent Reconstruction of the Creation Command

Read `src/pcae/core/repository_identity.py` in full, directly (not taken from the governing prompt). Confirmed schema (`schema_version`, `repository_instance_id`, `created_at`), atomic-write idiom (`tempfile.mkstemp` in the target directory → `fsync` → `os.replace`), symlink rejection at target and immediate parent, and `ensure_repository_identity(root)`'s idempotent read-first/generate-if-absent semantics — all as independently confirmed by phase 7O.1 and re-confirmed here.

**No identity-only CLI subcommand exists.** The only production call site is `commands/init.py::run_init`, which calls `ensure_repository_identity(root)` but *also* runs `init_harness()` (`write_missing_files()` against `INIT_TEMPLATES`, potentially creating/overwriting unrelated `.pcae/**` template files) and `install_hooks()`. Running `pcae init` against the real Dell deployment would exceed this phase's mutation wall. The narrowest production-supported operation is therefore a direct, out-of-band invocation of `ensure_repository_identity(HarnessPath.cwd())`, importing the same unmodified production module — not a reimplementation, not a broader CLI command.

## 4. Executing Principal

Fresh SSH to `hac-dell` as `codex` confirmed `codex` (uid 1003, groups `codex`,`sudo`,`users`) cannot even `cd` into `/opt/pcae/runtime/src` (`Permission denied` — not a member of group `pcae`). `/etc/passwd` lists `pcae:x:1004:1004:PCAE agent principal:/home/pcae:/usr/sbin/nologin` — a dedicated, nologin system principal, matching phase 7O.1's own §10 finding that identity creation must run as `pcae`, not bare `root`/`codex` (a root-owned, `0600` file would be unreadable by the very `pcae` principal that reads it back at runtime). `codex` has passwordless `sudo (ALL:ALL) NOPASSWD:ALL`, used only to enter the `pcae` principal context (`sudo -n -u pcae ...`), never to write as `root` directly.

## 5. Fresh Dell Read-Only Preflight (as `pcae`)

```
id                                    → uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)
hostname                              → atila-Latitude-E5470                       [exact match]
/etc/machine-id                       → 54ff22ce400b475aa0d55cb68f4a3334            [exact match]
git -c safe.directory=... rev-parse HEAD
                                       → b0840e96a7ffb12308e95828aa5927c3e7c770c0    [exact match]
git status --short                    → (clean)
git symbolic-ref -q HEAD              → (none) → DETACHED                          [as expected]
ls -la .pcae/repository-identity.json → No such file or directory                  [absent, confirmed]
stat .pcae, .pcae/.., src, runtime, pcae, opt
                                       → all directories, owner root, group pcae,
                                          mode 750 throughout — no symlinks anywhere in the chain
find /etc/pcae/hatp/trust-store       → directory exists, empty (no registry.json)  [binding absent]
ls /opt/pcae/runtime/                 → bin/, src/, venv/ all present, root:pcae 0750
derive_implementation_scope_digest()  → 65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8
                                          [exact match to expected/entering value]
verify_class_b_deployment_conformance()
                                       → NON_COMPLIANT; HBDC-REQ-042 = False,
                                          no_repository_identity_present,
                                          evidence=('/opt/pcae/runtime/src',)
```

**One discrepancy from the phase brief's stated baseline, independently found, not assumed:** the brief characterized `HBDC-REQ-042` as the "sole residual." The live 39-check aggregator run also shows `HBDC-REQ-036 = False` (`no_configured_production_launcher_detected`) — a second, pre-existing, unrelated residual not mentioned in the brief. It does not affect this phase's scope (identity creation only) and was not investigated further, but is recorded here rather than silently accepted.

Every other preflight item matched expected state exactly. Proceeded to mutation.

## 6. Target Path

Independently derived (not copied from the brief): `REPOSITORY_IDENTITY_RELATIVE_PATH = ".pcae" / "repository-identity.json"`, relative to `HarnessPath.cwd()` when the process's working directory is `/opt/pcae/runtime/src`. Full path: `/opt/pcae/runtime/src/.pcae/repository-identity.json` — matches the brief's conceptual expectation, confirmed live rather than trusted.

## 7. Path Safety

`.pcae/` and every ancestor (`src`, `runtime`, `pcae`, `opt`) confirmed to be real directories, none a symlink (`stat %F` all report `directory`), owner `root`, group `pcae`, mode `750`. No pre-existing `repository-identity.json` (§5). No malformed artifact. No race-inducing unexpected file. Safe to proceed to the single authorized mutation.

## 8. The Single Authorized Mutation — Executed

Exact command (via `sudo -n -u pcae`, cwd `/opt/pcae/runtime/src`):

```python
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity
root = HarnessPath.cwd()
identity = ensure_repository_identity(root)
```

**Result: `PermissionError: [Errno 13] Permission denied: '/opt/pcae/runtime/src/.pcae/.tmp-repository-identity-jb4vw0gf'`.**

`_write_atomic()`'s `tempfile.mkstemp(dir=".pcae")` call — the very first filesystem write attempt inside `ensure_repository_identity` — failed. Root cause, independently diagnosed: `.pcae/` is mode `750` (`rwxr-x---`), owner `root`, group `pcae`. The `pcae` principal is a member of group `pcae`, which grants only `r-x` (read + traverse), **not write**, on that directory. No OS principal other than `root` (the directory's owner) can currently create a file inside `.pcae/` on Dell. This is a **provisioning gap in the deployed directory permissions**, not a defect in `repository_identity.py`'s logic — the module's atomic-write idiom behaved exactly as designed (fail closed, no partial state) when denied write access.

This is a genuinely new finding beyond phase 7O.1's own §10 analysis. 7O.1 correctly predicted that running the *creation* as `root` (rather than `pcae`) would produce a file the `pcae` principal couldn't later *read*. This phase found a stricter, prior problem: even the "correct" principal (`pcae`) cannot *write* the file in the first place, because the directory's group bit lacks write access. Both findings are consistent (both trace to the same `root:pcae 0750` topology) but this one blocks step 1, not step 2.

## 9. No Retry — State Inspection First

Per this phase's own governing constraint, no immediate retry was attempted. Instead, state was inspected directly:

```
find .pcae -maxdepth 1 -name ".tmp-repository-identity-*"  → (no matches — no stray temp file)
ls .pcae/repository-identity.json                          → No such file or directory (unchanged)
```

**Nothing was persisted.** The failure occurred before any bytes reached disk (`mkstemp` itself is the call that raised) — this is unambiguously "no identity persisted," not "identity persisted despite reported failure." No possibility of a duplicate or orphaned identity exists.

## 10. Escalation Considered and Rejected

Running the same call as `root` (via bare `sudo -n python3 -c ...`) would very likely succeed at the OS level — `root` owns `.pcae/`. This was deliberately **not attempted**, for two independently sufficient reasons: (a) it is not the correct principal per §4/7O.1 §10 — the resulting file would be `root`-owned and, at the module's own `0600`-no-chmod default, unreadable by the `pcae` principal that every downstream consumer (`_check_deployment_identity`, HMIC's identity resolver, HATP producers) runs as, silently converting "absent" into "present but unreadable" for every future read; (b) fixing the underlying permission (`chmod g+w .pcae` or re-provisioning `.pcae/` as `pcae`-owned) is itself a mutation not authorized by this phase's mutation wall (only "first RepositoryIdentity creation" is authorized; directory-permission changes are a distinct administrative act). Both would have been scope violations dressed as workarounds.

## 11. Post-Failure Invariant Re-Verification

```
find .pcae -name ".tmp-repository-identity-*"   → none (no leaked temp file)
derive_implementation_scope_digest()            → 65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8  [unchanged]
git rev-parse HEAD                              → b0840e96a7ffb12308e95828aa5927c3e7c770c0  [unchanged]
git status --short                              → (clean, unchanged)
verify_class_b_deployment_conformance()          → NON_COMPLIANT; HBDC-REQ-042 = False,
                                                     no_repository_identity_present  [unchanged —
                                                     identical to §5, confirms the failure had zero
                                                     side effect on diagnostic state]
/etc/pcae/hatp/trust-store listing               → still empty  [DeploymentBinding still absent]
```

All invariants hold exactly as they did before the attempted mutation.

## 12. DeploymentBinding Field Resolution — Not Reached

Steps 23-43 of the governing prompt (binding-field reconstruction, producer preview, proposition drafting) are gated on a materialized `repository_id`, which does not exist. Consistent with this, and independently re-confirmed rather than assumed: phase 7O.1 §17-§19 already found `principal_id`, `signer_key_id`, `provider_profile`, and `authority_scope` unresolvable from any canonical source, with the production trust-store registry (`/etc/pcae/hatp/trust-store/registry.json`) confirmed empty again this session (§5). Even had identity creation succeeded, the binding proposition would independently have landed on "Outcome B" (fields unresolved) rather than a materializable proposition. This phase does not need to re-litigate that finding — it is orthogonal to, and independent of, the identity-creation failure.

## 13. No DeploymentBinding, No Election, No CHGR, No Certification — Proof

- No `create_deployment_binding`/`preview_create_deployment_binding` call was made anywhere this phase (real or disposable).
- No election (APPROVE/DECLINE/AMEND) was presented.
- No CHGR was published or written; none read this phase either (not needed — 7O.1 already read both existing CHGRs and found neither authorizes this mutation, and neither is implicated by a failed, no-op attempt).
- No certification function was invoked; only the pure, read-only `derive_implementation_scope_digest()` was called, both pre- and post-attempt.
- No `git fetch`/`checkout`/`chmod`/`chown` was issued against Dell's source tree. No venv or wrapper file was touched. No directory permission was changed (§10).
- The only Dell commands issued this phase: `id`, `hostname`, `cat /etc/machine-id`, `git rev-parse`/`status`/`symbolic-ref` (via `-c safe.directory=` override, not a persistent git config write), `stat`, `find`, `ls`, and the two Python invocations in §5/§8/§11 (digest read, HBDC diagnostic read, and the single failed `ensure_repository_identity()` attempt) — all via `sudo -n -u pcae`.

## 14. Phase Outcome

**Outcome C — REPOSITORYIDENTITY CREATION FAILED — NO STATE CHANGE**, with a specific, independently diagnosed root cause: `/opt/pcae/runtime/src/.pcae/` is mode `750`, group `pcae`, granting the `pcae` principal read+traverse but not write. No OS principal other than `root` can currently write into that directory; using `root` would produce an identity file the `pcae` principal (i.e., every real runtime consumer) cannot subsequently read, which is a worse outcome than not creating it. RepositoryIdentity remains absent; DeploymentBinding remains absent; HBDC remains `NON_COMPLIANT` with residuals `HBDC-REQ-042` (unchanged) and `HBDC-REQ-036` (pre-existing, unrelated, newly noted §5). No `DeploymentBinding` field resolution or proposition drafting occurred, since it was correctly gated on an identity value that was never produced.

## 15. Recommended Remediation (Not Performed This Phase)

A dedicated, narrowly-scoped administrative phase should either (a) grant the `pcae` group write access on `/opt/pcae/runtime/src/.pcae/` (e.g. `chmod 770` or equivalent, executed by `root`, under its own governance and independent verification), or (b) re-provision `.pcae/` as directly `pcae`-owned rather than `root`-owned-`pcae`-group. Either change is itself a real-host provisioning mutation and, per this phase's own mutation wall, was correctly not attempted here. This phase's finding (§8, §10) should be treated as that future phase's entry-state justification.

## 16. Strategic Breakpoint

Unchanged, unreached. Preserved per the governing prompt's own framing: pause before Boundary C only after a first-use `DeploymentBinding` and a clean, independently-verified `COMPLIANT` HBDC on real Dell — neither reached this phase.

## 17. Tests / Governance Results

No production code changed this phase (`src/pcae/**`, `scripts/**`, `docs/contracts/**`, `schemas/**`, `tests/**`, `pyproject.toml` all untouched — verification/administrative-attempt phase only).

- `pcae_check`: passed
- `pcae_health`: healthy
- `pcae_status_coherence`: coherent
- `pcae_doctor_task_memory`: warnings (pre-existing, unrelated — carried forward, outside this phase's allowed-file scope)
- `pcae_push_check`: clean (at entry)
- `pcae_runtime_inspect`: Observed / observe / unavailable
- `pcae_notify_status`: telegram configured/enabled
- `pcae_phase_report_reconcile_149O_20L_7O_1`: reconciled, mutation none
- `source_currentness`: passed — zero `src/pcae/**` drift between deployed SHA and Mac HEAD
- `dell_fresh_preflight`: passed — machine-id/hostname/SHA/HMIC-digest/identity-absence/binding-absence all exact matches; one unrelated pre-existing discrepancy noted (§5, HBDC-REQ-036)
- `repository_identity_creation_attempt`: failed safely — `PermissionError` on first write, zero bytes persisted, no stray temp file, root cause independently diagnosed as a directory-permission provisioning gap (§8)
- `no_retry_performed`: passed — state was inspected, not blindly retried, per governing constraint (§9)
- `escalation_to_root_considered_and_rejected`: passed — documented reasoning (§10), no `root`-owned write attempted
- `post_failure_invariants`: passed — HMIC digest, HEAD SHA, git cleanliness, HBDC diagnostic, trust-store emptiness all unchanged (§11)
- `deploymentbinding_field_resolution`: not reached — correctly gated on absent identity; orthogonal prior finding (7O.1) re-confirmed still applicable (§12)
- `no_deploymentbinding_no_election_no_chgr_no_certification`: passed (§13)
- `report_notification_tests`: not_applicable_this_phase
- `bootstrap_session_reporting_tests`: not_applicable_this_phase
- `fast_green`: not re-run this phase — no `src/pcae/**`/`tests/**` change occurred; prior phase's (149O.20L.7O.1) confirmation run stands unaffected: 7789 passed, 5 skipped, 0 failed, 0 errors (deselected pre-existing-failure set)

## 18. Final Verdict

**REPOSITORYIDENTITY CREATION FAILED — NO STATE CHANGE.** The failure is a real-host directory-permission provisioning gap, independently diagnosed to its exact root cause, not a defect in `repository_identity.py`'s production logic (which behaved correctly: fail-closed, atomic, no partial state, no silent escalation). RepositoryIdentity and DeploymentBinding both remain absent on Dell, exactly as at phase entry. No mutation of any kind was left in a half-applied state.

## 19. Recommended Next Phase

A narrow, dedicated, human-governed administrative phase to remediate the `/opt/pcae/runtime/src/.pcae/` directory-permission gap (§15) on `hac-dell` — outside this phase's own mutation wall — after which **149O.20L.7O.2** (or its numeric successor, per this project's task-creation convention) should be re-attempted using the exact same independently-reconstructed command (§3, §8), which requires no further design work, only the permission fix as a precondition.
