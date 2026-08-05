# Phase 149O.1F.1 — HATP Production Trust-Store Path Hardening

## Scope

Narrow foundation repair of `B-149O.1F-1` only: the production HATP
trust-store root resolver. Owns `src/pcae/core/hatp_bootstrap.py`
(`_default_production_trust_root`) plus focused tests and this
document. No Wave 3 (proof schema/serialization/verifier), no provider
(FIDO2/PIV), no human-presence signer, no Class-B OS user/ACL
provisioning, no RAE/AG3/AG5 integration. HATP-001 v1.0 is
byte-unchanged.

## Pre-repair reproduction (Blocking finding B-149O.1F-1)

`HATPTrustStore.production()` called `_default_production_trust_root()`,
which returned `Path.home() / ".pcae-hatp" / "trust-store"`.
`Path.home()` on POSIX is `Path(os.path.expanduser("~"))`, and
`os.path.expanduser` consults `os.environ["HOME"]` before falling back
to any OS account lookup. Reproduced directly against the pre-repair
module:

```python
os.environ["HOME"] = "/tmp/attacker-controlled-home"
Path.home()  # -> PosixPath('/tmp/attacker-controlled-home')
HATPTrustStore.production().root
# -> PosixPath('/tmp/attacker-controlled-home/.pcae-hatp/trust-store')
```

An attacker who writes a `registry.json` under that redirected root and
then calls `resolve_deployment_authorization()` for a repository/root
pair it fabricated end to end receives a real, non-`None`
`DeploymentBinding` — no admin, no separate OS principal, no
out-of-band provisioning involved (this was exactly what
`tests/test_phase_149o_1f_hatp_repository_identity_trust_store_foundation_independent_verification.py::test_home_redirection_enables_self_authored_deployment_authorization`
demonstrated, historically, before this repair; that test is retained
in place and now records the after-repair secure behavior — see
"149O.1F suite disposition" below).

## Root cause

The authoritative production trust-root **location** depended on
ordinary, agent-controllable process environment (`$HOME`). The trust
record format, the deployment-binding model, and the repository
identity model were not the defect (149O.1F's independent verification
confirmed all of those sound). Protected trust-store *contents* plus an
attacker-selectable authoritative *root* is not protected authority.

## Candidate resolver analysis

Three candidates were evaluated (governing-prompt items 78-92):

1. **`pwd.getpwuid(os.geteuid()).pw_dir`** (real OS-account home,
   bypassing `$HOME`). Removes environment redirection, but in the
   frozen two-principal Class-B topology (HATP-REQ-028), the *Agent* OS
   principal's own effective UID resolves to the *Agent's own home* —
   a directory the agent owns and can write to. This is the
   "agent-home trap": environment-hardening alone does not remove
   agent authority over the resolved root. Rejected as insufficient on
   its own.
2. **Trusted discovery of the Human/Admin principal's identity**, then
   resolving *that* principal's OS home. Requires a way to name the
   Human/Admin principal that is itself not agent-writable/agent-
   selectable — no such mechanism exists yet in this repository
   (would require a new trusted deployment-configuration surface,
   explicitly out of scope for a narrow repair per item 82/126).
3. **A fixed, platform-level system path**, owned/provisioned by the
   Human/Admin principal out of band, with no dependency on *any*
   process-user identity at all. Selected.

## Selected authoritative root strategy

`_default_production_trust_root()` now returns a hardcoded,
platform-keyed constant:

- macOS (`sys.platform == "darwin"`): `/Library/Application Support/PCAE/HATP/trust-store`
- Linux (`sys.platform == "linux"`): `/etc/pcae/hatp/trust-store`
- Any other `sys.platform` value, or `os.name != "posix"`: raises
  `HATPBootstrapUnsupportedPlatformError` (fail closed; no
  environment-derived fallback, per items 12-13/60/63).

The resolver reads no environment variable, no CLI argument, no
constructor parameter, no repository state, and no current working
directory — it is a pure function of `os.name`/`sys.platform`. This
sidesteps the agent-home trap entirely: the returned path is never
"whoever is currently running this process's home directory" for
*any* principal, agent or admin. It is a single, well-known machine
location that a Human/Admin deployment step is expected to create and
own; this module never creates it (see "No auto-provisioning" below).

On the actual development host, `/Library/Application Support` is
`root:admin`, mode `755` — writable only by `root`, not by the
ordinary (non-`sudo`) admin-group user this repository runs under, so
the module cannot and does not create `PCAE/HATP/trust-store` under it
itself.

### Why `$HOME`/`USER`/`LOGNAME`/`XDG_*`/`CWD` cannot redirect it

None of these are read by the resolver at all after the repair — the
function body contains no `os.environ` access, no `Path.home()` call,
no `expanduser()` call, and no `os.getcwd()` call. This is enforced by
a source-level AST guard
(`test_resolver_source_has_no_forbidden_environment_reads`,
`test_no_path_home_anywhere_in_module_authoritative_path`) in the new
regression suite, in addition to the behavioral spoof-matrix tests.

### Agent-owned-home analysis

Because the resolver never derives a path from any OS home directory
(agent's or otherwise), a fake registry planted under the agent's own
real home (`~/.pcae-hatp/trust-store`, the *old* location) is
categorically irrelevant to the new resolver — verified by
`test_fake_registry_under_agent_owned_actual_home_not_authoritative`.

### Future Class-B principal compatibility

A fixed system path is compatible with the frozen two-principal
topology (HATP-REQ-028) without requiring the Agent process to
discover the Human/Admin principal's identity at runtime: provisioning
(creating the directory, setting ownership/ACL so the Agent principal
has read-only access) is a deployment-time Human/Admin action, wholly
outside this module, matching HATP-REQ-030's "owned/administered by
the Human/Admin OS principal" requirement directly.

### Fixed-system-path vs OS-home decision

Fixed system path was chosen over further per-user-home refinement
because it requires no new trusted-identity-discovery mechanism (item
82/126's off-ramp), is simpler, and is a closer match to
HATP-REQ-026's "OS-enforced security context" framing than a home
directory the running process may itself own.

## Unsupported-platform behavior

Any `sys.platform` other than `darwin`/`linux` (including all Windows
values) raises `HATPBootstrapUnsupportedPlatformError` from
`_default_production_trust_root()` — `HATPTrustStore.production()`
propagates the exception rather than falling back to an
environment-derived path. Verified by
`test_non_posix_platform_fails_closed` and
`test_unrecognized_posix_platform_fails_closed` (`sys.platform`
monkeypatched to simulate `nt` / `freebsd13`).

## Missing-root / unsafe-root behavior (unchanged downstream)

`HATPTrustStore._load_registry()`/`environment_status()` are unchanged:
if the resolved fixed root does not exist on the host (expected on an
unprovisioned dev machine — confirmed: neither
`/Library/Application Support/PCAE/HATP/trust-store` nor
`/etc/pcae/hatp/trust-store` exists on this repository's current
development host), `environment_status()` returns `UNAVAILABLE`
(`trust_store_missing`), not a weaker or different result. If a root
existed but were agent-writable/parent-writable/symlinked,
`inspect_bootstrap_environment` still classifies it
`UNSAFE_CONFIGURATION` exactly as before — none of that logic changed.

## Production factory / constructor discipline (unchanged)

`HATPTrustStore.production()` still takes no arguments
(`test_production_factory_takes_no_root_argument`). The
`_test_only_root` constructor parameter remains a private,
underscore-prefixed, test-only composition seam, never reachable
through `.production()`. A repository-wide search
(`test_no_production_call_site_passes_a_caller_controlled_root`) found
no `src/pcae/**` call site constructing `HATPTrustStore(...)` outside
the test-injection keyword. The factory does not create, `mkdir`, or
write anything (`test_production_factory_does_not_create_or_provision_root`).

## Regressions

| Suite | Result |
|---|---|
| `tests/test_repository_identity.py` + `tests/test_hatp_bootstrap_foundation.py` + `tests/test_phase_149o_1e_*.py` | 51 passed (unchanged) |
| `tests/test_phase_149o_1f_hatp_repository_identity_trust_store_foundation_independent_verification.py` | 22 passed (unchanged count; two exploit assertions flipped in place, see below) |
| `tests/test_phase_149o_1f_1_hatp_production_trust_store_path_hardening.py` (new) | 30 passed |
| Combined 149O.1E + 149O.1F + 149O.1F.1 | 103 passed |
| `tests/test_phase_149o_1c_*.py` (HATP-001 contract independent verification) | 95 passed (unchanged) |
| `tests/test_phase_149o_1d_*.py` (implementation plan) | 32 passed on a clean tree (transiently reported 31 passed/1 failed while this repair's diff was still uncommitted — see "Dirty-tree-only test disposition" below) |
| RAE/Permission-Broker/Agent subset (`test_rollback_approval_evidence_*`, `test_permission_broker*`, `test_agent.py`) | 4608 passed |
| Fast Green (`-m fast_green -n auto`) | 4431 passed (unchanged baseline) |
| Full suite (`-n auto`, uncommitted diff) | 27964 passed / 88 failed / 10 skipped |

### Full-suite failure triage

The 88 full-suite failures were root-caused by re-running the exact
same 88 node IDs against a `git stash`-clean tree (this repair's diff
temporarily removed, then restored via `stash pop`):

- **75 already fail identically on the clean, unmodified tree**
  (confirmed by direct re-run) — pre-existing, unrelated packaging/
  wheel-build tests (`test_cltr_authority_*`, `test_cltr_cutover_*`,
  `test_schema_runtime_packaging.py`, `test_chgr_packaging.py`) and a
  handful of other pre-existing failures including
  `test_phase_149d_rwmpc_contract_independent_verification.py::TestNoProductionModification::test_src_pcae_untouched_by_phase_149d`.
  Zero of these are touched by this repair's diff.
- **11 are `pytest-xdist` parallel-worker isolation flakes**
  (`test_backend_cli.py`, two CLTR "side-effect-free reimport" checks,
  five `test_permission_broker_observation_verification.py`
  parametrizations, two `test_runtime_snapshot.py` tests,
  `test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`):
  fail under `-n auto`, pass consistently under `-n0` (serial), both
  before and after this repair's diff — pre-existing test-isolation
  debt, not a behavioral regression.
- **2 are dirty-tree-only, self-resolving checks**:
  `test_phase_149o_1d_human_approval_trusted_provenance_implementation_plan.py::TestProductionBoundaryUnchanged::test_no_src_pcae_files_modified_this_phase`
  and
  `test_strategic_lineage.py::test_65j_current_approved_lineage_must_match_live_branch_phase`
  compare live `git diff HEAD`/branch-lineage state against `HEAD`;
  they fail only while this phase's `src/pcae/**` diff is uncommitted
  and `PROJECT_STATUS.md` still names the prior phase, and are
  expected (and confirmed) to pass again once this phase's commits and
  `PROJECT_STATUS.md` update land.

**Zero new failures are attributable to the trust-root resolver
repair.**

### 149O.1F suite disposition

Per the governing charter for this phase, the historical 149O.1F
exploit-detector tests were not deleted or left silently
contradicting the current secure behavior. They were updated in place
to record the flip explicitly: before this repair,
`test_home_environment_variable_redirects_production_trust_store` and
`test_home_redirection_enables_self_authored_deployment_authorization`
asserted the `HOME` redirection **succeeded**; they now assert it is
**blocked**, with an updated section banner documenting the historical
finding and pointing to this document and to
`tests/test_phase_149o_1f_1_hatp_production_trust_store_path_hardening.py`
as the authoritative post-repair suite. `test_xdg_variables_have_no_effect_observation`
and `test_cwd_has_no_effect_on_production_path` were adjusted to
compare against the live production root rather than a
`Path.home()`-based expectation (the underlying observation —
"XDG/CWD have no effect" — is unchanged; only the *baseline* root
changed shape).

`test_no_production_source_changed_by_this_verification_phase` was
additionally corrected to pin its `git diff` comparison to 149O.1F's
own commit (`7a0134cd~1..7a0134cd`) rather than a bare `git diff
HEAD`, which was never actually a phase-attribution check (a clean
tree always satisfies `git diff HEAD == []` regardless of which phase
is active) and would have spuriously failed during any later phase's
legitimate `src/pcae/**` work, including this one.

`tests/test_hatp_bootstrap_foundation.py::test_production_ignores_environment_overrides`
(149O.1E) was widened to additionally set `HOME` and assert the
resolved root is unaffected — the original version predated this
finding and only checked four HATP-specific guessed variable names,
never the actual dependency.

## B-149O.1F-1 closure

**B-149O.1F-1 CLOSED — PRODUCTION TRUST-STORE ROOT NO LONGER
AGENT-REDIRECTABLE.**

Closure basis (not merely "`Path.home()` was replaced"): the original
exploit was re-run against the repaired module and now fails —
`HOME` (set, unset, empty, `.`, `/tmp/attacker`), `USER`, `LOGNAME`,
`USERNAME`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, and `CWD`, individually
and combined, leave the resolved production root unchanged; a fake
registry planted under any of those redirected/attacker locations
(including the agent's own real OS home) is never read by
`HATPTrustStore.production()`.

## Preserved invariants (regression floor)

All independently verified by the new suite, unchanged from 149O.1E/
149O.1F: same-user readiness never reports `READY`
(`test_same_user_readiness_still_never_ready`); same-ID-wrong-root
rejected (`test_same_id_wrong_root_still_rejected`); duplicate
deployment bindings fail closed
(`test_duplicate_deployment_bindings_still_rejected`); revoked bindings
never match (`test_revoked_binding_still_rejected`); production factory
signature unchanged; no new public mutation methods; no
`approval_present`/`HATP_TRUSTED_OPERATIONAL` symbol introduced.

## Requirement trace

- **HATP-REQ-030**: trust store owned/administered by Human/Admin —
  the fixed system path is the kind of location a Human/Admin
  deployment step provisions and owns; this module never provisions it.
- **HATP-REQ-032**: never `repo/.pcae/**` — unchanged, still true; new
  test `test_production_root_not_repo_local`.
- **HATP-REQ-034**: normal runtime SHALL NOT redirect the trust store
  through an untrusted environment variable — this is the requirement
  B-149O.1F-1 violated and this repair now satisfies (full spoof
  matrix in the new suite).
- **HATP-REQ-035**: no CLI override flag — unchanged; `.production()`
  still takes no arguments.
- **HATP-REQ-026/028**: OS-enforced Class-B security context, frozen
  two-principal topology — the fixed-path selection was made
  specifically to avoid the "agent-home trap" that a naive
  environment-only fix would have left open under that topology.

## Runtime / deployment status (unchanged)

Runtime remains Observed / observe / unavailable. Current same-user
development deployment remains **NOT READY** (unaffected by this
repair — `inspect_bootstrap_environment`'s same-OS-principal check is
untouched). **HATP PRODUCTION: NOT READY** — this repair hardens the
software resolver; it does not provision a Class-B deployment. Waves
3-7 remain unimplemented. No proof schema, serializer, verifier,
FIDO2/PIV provider, human-presence signer, RAE integration, AG3/AG5
integration, or activation symbol (`approval_present`,
`HATP_TRUSTED_OPERATIONAL`) was introduced. B-149O-1 through B-149O-4
remain OPEN, unaffected. F-149O.1C-1 remains pending Wave-3
proof-schema implementation. F-149O.1C-2 remains editorial debt only.
HATP-001 v1.0, RAE-001 v1.0, RWMPC-001 v1.0, PBPC-001 v1.2, PBPA-001
v1.0, and CHGR-001 all remain byte-unchanged (confirmed via targeted
`git diff --name-only` against `docs/contracts/**` and the frozen RAE/
Permission-Broker/agent module list).

## Phase verdict

**HATP TRUST-STORE PATH HARDENING IMPLEMENTED — READY FOR INDEPENDENT
RE-VERIFICATION.**

Foundation status: Wave 1 IMPLEMENTED (unchanged); Wave 2 REPAIRED,
PENDING INDEPENDENT RE-VERIFICATION (not self-certified as fully
verified by the phase that performed the repair).

## Recommended next phase

**149O.1F.2 — HATP Repository Identity + Trust-Store Foundation
Independent Re-Verification.** Should independently re-run the full
149O.1F attack surface against the repaired module — especially the
`HOME`/environment spoof matrix, the agent-home-trap scenario, the
fixed/system-path semantics (parent writability, symlink replacement,
missing root, wrong owner), caller injection, same-user readiness, and
copy/root binding — before any Wave 3 work begins.
