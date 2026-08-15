# Phase 149O.20L.7D.8 — Class-B Verifier Source Repair Independent Verification

## 1. Scope and disposition

**Verification-only.** No production verifier source modified, no
contracts modified, no Dell mutation, no redeployment, no Dell venv
reinstall, no Action-9 change, no REQ-036 repair, no CHGR created or
amended, no DeploymentBinding, no certification, no activation. This
phase independently re-derives, from primary source and immutable git
objects, whether the two repairs Phase 149O.20L.7D.7 reported are
correct, minimal, complete, and fail-closed — without treating 7D.7's
own report, tests, or classifications as oracle.

## 2. True phase-entry commit and pre-repair baseline

- **Phase-entry commit (immutable, git-object evidence):**
  `8a18f73dd33a6ba81ef3626a53c1fa83a3a0c866` ("Phase 149O.20L.7D.6:
  restore idle-task standard allowed-file list") — the direct parent of
  the repair commit, confirmed via `git log -1 73ea8b23^`.
- **Repair commit:** `73ea8b237a2fd4b6c0f22987eea7f748bcc97ca2`.
- **Non-production sync commit:** `0355d06127f2abce382d60763f7b2d8b5fea9598`
  (PROJECT_STATUS.md/CHANGELOG.md only).
- **Repaired candidate HEAD at phase entry into 7D.8 (identical
  production bytes to 73ea8b23):** `28bf137b5dc95d024e8913b678dce0501a46fd0f`.
- **Baseline reconstruction method:** a disposable `git worktree
  --detach` checkout of `8a18f73d` (not a `git stash`), used for every
  pre-repair execution and regression comparison in this report, with
  `PYTHONPATH` pointed at the worktree's own `src/` to shadow the
  editable-install pointer that would otherwise resolve imports back to
  the live repository's repaired code.

## 3. Exact production diff (independently reconstructed)

`git diff 8a18f73d..73ea8b23` touches exactly three production files,
plus one new doc and two test files (non-production):

| File | Production? | Change |
|---|---|---|
| `src/pcae/core/hatp_class_b_conformance.py` | yes | 1 line: `distribution("pcae")` → `distribution("pcae-harness")` (line 72) |
| `src/pcae/core/hatp_environment_lock_verifier.py` | yes | 1 line: same literal change (line 339) |
| `src/pcae/core/hatp_class_b_topology_verifier.py` | yes | +87/-1 lines: new `_symlink_effective_write_access` helper (lines 400-483) + one dispatch-line change inside `_effective_write_access` (line 503) |
| `docs/PHASE_149O_20L_7D_7_...md` | no | new report |
| `tests/test_phase_149o_20i_hatp_class_b_topology_verifier.py` | no | 1 test renamed/updated to the new, more specific reason code (`symlink_parent_chain_writable` replacing `path_is_symlink`), same expected outcome (`write is True`) |
| `tests/test_phase_149o_20l_7d_7_...py` | no | new 587-line companion test module |

**Unrelated production changes found: zero**, confirmed by full-diff
inspection line-by-line, not by trusting 7D.7's own count.

Direct inspection of the topology-verifier diff confirms:
`_is_symlink_unsafe` (the unconditional symlinked-ancestor rejection
used by `_ancestor_chain_safe`) is untouched; the new function reuses
`_ancestor_chain_safe` and `_effective_write_access` rather than
introducing parallel write-access logic.

## 4. HBDC-001 v1.0 primary-contract reconstruction

Read directly from `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`:

- **HBDC-REQ-022** (§12): Model A (editable install from canonical repo
  working tree) is the only authorized deployment model.
- **HBDC-REQ-030** (§13): `sitecustomize.py`/`usercustomize.py`,
  wherever present on the resolved production `sys.path`, SHALL be
  admin-controlled and agent-unwritable, or absent.
- **HBDC-REQ-035** (§13): editable-install link metadata SHALL be
  admin-controlled and agent-unwritable in production.
- **HBDC-REQ-036** (§13): launcher/wrapper configuration SHALL be
  admin-controlled and agent-unwritable.
- **HBDC-REQ-042** (§16): `repository_instance_id` confers no authority
  alone; `DeploymentBinding` is the controlling artifact.

This independent re-read matches 7D.6/7D.7's own rendering byte-for-byte
on normative content; it was re-derived from the contract file directly,
not copied from their report prose.

## 5. Distribution-identity ground truth (HBDC-REQ-022/035)

- `pyproject.toml`: `[project] name = "pcae-harness"`; wheel
  `packages = ["src/pcae"]` (import name `pcae`, distinct from the PEP
  621 project/distribution name); `[project.scripts] pcae =
  "pcae.cli:main"`.
- Real, unmocked lookup on this host:
  `importlib.metadata.distribution("pcae-harness")` **resolves**
  (`pcae_harness-0.1.0.dist-info`); `importlib.metadata.distribution
  ("pcae")` **raises `PackageNotFoundError`**.
- Repo-wide grep (independent of 7D.7's own grep): exactly two
  `importlib.metadata.distribution(...)` call sites in `src/`, both
  reading `"pcae-harness"`. Zero stray `"pcae"`-keyed lookups remain.

**Independent pre-repair reproduction, executed for real** (not string
inspection) — the immutable pre-repair function, run against this
host's actual installed metadata inside the disposable worktree:

```
PRE-REPAIR _check_model_a_deployment(0):
  ClassBCheckResult(check_id='HBDC-REQ-022', satisfied=False,
    status='pcae_distribution_metadata_not_found', evidence=())
```

The repaired function, run against the same real environment:

```
REPAIRED HEAD _check_model_a_deployment(0):
  ClassBCheckResult(check_id='HBDC-REQ-022', satisfied=True,
    status='model_a_editable_install_confirmed',
    evidence=('/opt/homebrew/.../pcae_harness-0.1.0.dist-info',))
REPAIRED HEAD _check_editable_install_metadata(0, {0}):
  ClassBCheckResult(check_id='HBDC-REQ-035', satisfied=False,
    status='editable_install_metadata_agent_writable', evidence=(...))
```

This proves the repair does not merely stop raising an exception — it
reaches and evaluates the actual downstream `direct_url.json`/RECORD
evidence in both directions (REQ-022 satisfied here because this dev
host is a genuine editable install; REQ-035 correctly reports
`agent_writable` for uid 0/root, proving the negative-property direction
is also reachable, not silently suppressed).

Invalid-case fail-closed behavior (companion suite,
`test_req_022_invalid_case_absent_distribution_remains_fail_closed`,
`test_req_035_invalid_case_absent_distribution_remains_fail_closed`):
forcing `PackageNotFoundError` from a monkeypatched
`importlib.metadata.distribution` still yields `satisfied=False,
status=pcae_distribution_metadata_not_found` for both checks — no
permissive fallback was introduced by the repair.

## 6. Symlink / effective-write-access repair (HBDC-REQ-030)

### 6.1 Independent pre-repair reproduction

The immutable pre-repair `_effective_write_access`, executed for real
against a constructed Dell-equivalent-safe topology (root-owned parent
0755, root-owned target 0644, agent principal distinct from the file
owner and its group) inside the disposable worktree:

```
PRE-REPAIR Dell-equivalent-safe symlink: True path_is_symlink (...)
```

Confirms the actual reported defect: an unconditional false positive on
a genuinely safe, admin-controlled symlink.

### 6.2 New helper — line-by-line understanding

`_symlink_effective_write_access` (topology_verifier.py:400-483):
depth-guarded (`_SYMLINK_CHAIN_GUARD = 64`) recursive function that
evaluates, in order: (1) the symlink's own parent-directory chain via
`_ancestor_chain_safe` (replacement channel); (2) the resolved target's
mutability, recursing through itself for chained symlinks or through
`_effective_write_access` for a terminal non-symlink target; (3) the
target's own ancestor chain (`_ancestor_chain_safe` again) if the target
itself is non-writable, since a non-writable file can still be replaced
via a writable containing directory; (4) broken links, unreadable
links, inspection errors, and chain-guard exhaustion all resolve to
`None` (indeterminate), never `False`.

**Caller inventory (independently reconstructed via grep, not trusted
from the "ten callers" count in 7D.7's report):** `_effective_write_access`
has real call sites at `hatp_class_b_topology_verifier.py:553` (internal,
inside `_ancestor_chain_safe`), `:668` (`_resolve_trusted_executable_with_effective_access`,
HBDC-REQ-038), `:836` (`_check_write_authority`, HBDC-REQ-007), `:866`
(`_check_group_effective_access`, HBDC-REQ-007/015); and, via the
`from ... import _effective_write_access` at `hatp_environment_lock_verifier.py:36`,
ten further call sites at lines 91, 111, 144, 159, 185, 229, 298, 355,
358, 379 — mapping respectively to `_check_interpreter_unwritable`
(REQ-027), `_check_venv_lock` (REQ-026), `_check_pythonpath` (REQ-028,
two call sites), `_check_user_site` (REQ-029), `_check_customization_modules`
(REQ-030), `_check_pth_files` (REQ-031), `_check_editable_install_metadata`
(REQ-035), `_check_launcher` (REQ-036 — via the shared primitive, not
touched by this repair's own logic). Total matches 7D.7's claimed count;
independently reconstructed, not merely counted from their report.

Confirmed by direct inspection: `_check_customization_modules`
(`hatp_environment_lock_verifier.py:176-192`) — the actual HBDC-REQ-030
compliance check — calls `_effective_write_access` on the real
`sitecustomize.py`/`usercustomize.py` candidate path, so the repair
reaches the real REQ-030 determination, not an isolated helper (also
directly exercised by this phase's own companion test
`test_req_030_customization_module_check_routes_through_repaired_symlink_helper`).

### 6.3 Adversarial symlink topology matrix (independently constructed, disposable, non-`/tmp` fixtures)

**Note on fixture placement:** this host's `/tmp` (`/private/tmp`) is
mode `1777` (world-writable, sticky bit) at the top level. Since
`_ancestor_chain_safe` correctly walks *every* ancestor up to the
filesystem root (HBDC-REQ-017/020), any fixture under `/tmp` is
unconditionally, correctly classified unsafe regardless of its own leaf
permissions — that is genuinely correct verifier behavior, but it makes
`/tmp` unusable for constructing a *safe* test topology. All safe-case
fixtures were built under `$HOME` instead (ancestor chain `/Users`
`0755`, `$HOME` `0750`, neither world-writable), matching the real
Dell topology's `/etc`, `/usr` chain. The ACL channel was stubbed closed
(`_acl_grants_agent_write = lambda *_: False`) to isolate this repair
from the orthogonal, already-independently-verified (149O.20J series)
ACL-tool-trust-resolution concern — on this real dev Mac, several `PATH`
entries are owned by the interactive user, so unstubbed ACL-tool
resolution genuinely, correctly fails closed for a reason unrelated to
this repair.

| Case | Topology | Result | Reason code |
|---|---|---|---|
| Dell-equivalent safe | admin parent/target, no channel open | **safe** (`False`) | `symlink_fully_closed` |
| Replacement attack | writable symlink parent, safe target | **unsafe** (`True`) | `symlink_parent_chain_writable` |
| Target mutation attack | safe parent, writable target | **unsafe** (`True`) | `symlink_target_writable:world_writable` |
| Target-ancestor attack | safe parent, non-writable target, writable target-ancestor | **unsafe** (`True`) | `symlink_target_writable:symlink_target_ancestor_writable` |
| Effective supplementary-group attack | target group-writable, agent's *supplementary* (non-primary) group matches | **unsafe** (`True`) | `...agent_group_membership_grants_write`; negative control (no matching group) → **safe** |
| ACL-only attack | mode bits fully closed, ACL grants target write | **unsafe** (`True`) | `...acl_grants_agent_write` |
| Chained symlinks, safe | two hops, safe final target | **safe** (`False`) | `symlink_fully_closed` |
| Chained symlinks, unsafe | two hops, unsafe final target | **unsafe** (`True`) | `...world_writable` |
| Broken link | target does not exist | **indeterminate** (`None`), never `False` | `path_missing` |
| Symlink loop | A→B→A | **indeterminate** (`None`), never `False` | `path_missing` |
| Relative symlink | resolved via link's own parent, CWD changed to `/` | **safe** (`False`) | `symlink_fully_closed` |
| Inspection failure | `os.readlink` raises for a reason distinct from "missing target" | **not safe** (`None`), never `False` | `symlink_unreadable` |

All twelve cases independently reproduced against the real, repaired
production code (`src/pcae/core/hatp_class_b_topology_verifier.py`,
`_effective_write_access`), formalized as the 28-test companion module
(§10 below), run three consecutive times with zero flake.

**Finding (non-blocking, accuracy note, not a security defect):** for a
*top-level* broken or looping symlink, Python's `Path.exists()` (called
first, inside `_effective_write_access`, before dispatch to
`_symlink_effective_write_access`) already resolves through the full
symlink chain and returns `False`, so the outer function returns
`(None, "path_missing", ())` *before* `_symlink_effective_write_access`
is ever entered. `_symlink_effective_write_access`'s own internal
`target_exists`/broken-target check (`"symlink_target_broken"`) is
therefore unreachable for a first-hop broken/looping link through the
real public entry point — only the depth-guard
(`"symlink_chain_guard_exceeded"`, for a legitimately long but
fully-resolving chain) and the explicit-`readlink`-failure path
(`"symlink_unreadable"`) are genuinely reachable in normal operation.
The *outcome* is unaffected — both code paths fail closed to
indeterminate — this is dead-code/defense-in-depth, not a functional or
security defect, and does not change the REQ-030 verdict below.

### 6.4 TOCTOU classification (§28)

The verifier makes only a snapshot-time topology assessment (per its
own docstrings: "never returns early," walks the full chain "at the
moment inspected"). It offers no stronger guarantee than that — no
claim of cryptographic or runtime-execution-time immutability is made
or newly introduced by this repair. This is the same accepted residual
already named by HMIC-REQ-063/HBDC-REQ-040-041 (Option C: admin-
controlled, agent-unwritable *configuration*, not executed-code
attestation). This repair neither closes nor expands that residual.

## 7. Historical Class-B regression sweep (149O.20J series)

Ran `pytest -k "149o_20j" -m fast_green` against both the repaired HEAD
and, via `PYTHONPATH`-shadowed worktree, the immutable pre-repair
commit:

- **Pre-repair:** 9 failed, 106 passed, 1 skipped.
- **Post-repair:** 11 failed, 104 passed, 1 skipped.
- **Net-new (2):** `test_aggregator_module_unchanged` and
  `test_environment_lock_verifier_unchanged`
  (`test_phase_149o_20j_3_...py`) — clean-tree byte-pin assertions
  expecting the topology/environment-lock modules unchanged since an
  older phase entry; expected to break by a legitimate later source
  repair, not a functional regression.
- **The other 9 pre-existing failures** (both before and after this
  repair, identical in both runs): stale historical-finding-reproduction
  assertions already superseded by earlier repairs not touched by 7D.7
  (e.g. `test_agent_effective_gid_not_in_getgroups_can_be_missed`
  asserts `os.getegid()` is absent from `_current_agent_identity`'s
  source — false today, since `_current_agent_identity` already reads
  `os.getegid()` at line 155, a fix from an earlier phase this old test
  was never updated to reflect; `test_deep_ancestor_writable_beyond_immediate_parent_is_caught`
  asserts the ancestor walk stops at the first proven-safe ancestor —
  contradicted by `_ancestor_chain_safe`'s own current, deliberate,
  documented "never returns early" full-walk discipline, repaired in an
  earlier 149O.20J.3 phase).
- **No prior J-series security property (ancestor-chain walk, macOS ACL
  parsing, effective GID, ACL-only write detection, writesecurity/chown
  reclassification) reopened** — every *logic* assertion in that suite
  still passes in both runs; only already-stale byte-pin/finding-
  reproduction assertions fail, in both runs or newly.

## 8. Full fast_green regression-gate adjudication

Both runs used the identical interpreter/environment
(`~/repos/pcae-harness/.venv`, which has the `hatp-hardware` extra
installed — the bare `/opt/homebrew` `python3` cannot even *collect*
the suite, since `tests/test_phase_149o_7_hatp_class_b_activation_independent_verification.py`
imports `fido2`, an unrelated, pre-existing environment-provisioning
gap, not a code defect).

- **Pre-repair baseline** (disposable `git worktree --detach 8a18f73d`,
  `PYTHONPATH`-shadowed so imports resolve to the worktree's own source,
  not a `git stash`): `pytest -m fast_green` → **166 failed, 7191
  passed, 4 skipped, 9 errors** (438s).
- **Post-repair** (repaired HEAD, same environment): `pytest -m
  fast_green` → **181 failed, 7202 passed, 4 skipped, 9 errors** (506s).
- **Exact test-ID diff** (`comm` against sorted `FAILED`/`ERROR` lists):
  174 failures/errors identical in both runs; **16 net-new**; **1
  resolved** (present pre-repair, absent post-repair).

### 8.1 Net-new failures (16), individually adjudicated

**15 of 16 — expected stale byte-pin/clean-tree assertions**, each
parametrized or direct-asserting that one of the three repaired modules'
bytes are unchanged since an earlier phase entry (`149O.20J.3`,
`149O.20K.2`, `149O.20K.3`, `149O.20L.1B`, `149O.20L.3`, `149O.20L.4`).
These are exactly the expected consequence of a legitimate, intentional
production-source change — **expected stale historical assertion**,
requiring a future test-migration phase (not this one) to re-pin against
the new bytes. None of these is a current authority/functional gate;
each asserts historical byte-identity, not a live security property.

**1 of 16 — `tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`
— test defect, unrelated subsystem, independently confirmed.** This
test spawns `python -m pcae shell-gate audit verify` with `cwd=REPO_ROOT`,
where `REPO_ROOT = Path(__file__).resolve().parent.parent` — i.e. it
resolves to *wherever the test file physically lives*. Run inside the
`PYTHONPATH`-shadowed worktree, `REPO_ROOT` is the disposable worktree
(clean, minimal `.pcae/` state) and the test passes in isolation. Run
against the live repository (post-repair HEAD), `REPO_ROOT` is the real,
actively-governed repo with ~3,963 accumulated provenance events and an
active session — and the same command, invoked directly (not via
pytest), independently reproducibly hangs with zero output for 6+
seconds and deterministically times out at the test's hardcoded 15s
limit, regardless of which commit is checked out. This has nothing to
do with the distribution-name or symlink-write-access verifier code
(`shell_gate.py` is a wholly separate subsystem) — it is a pre-existing
timing/state-coupling sensitivity in the test's own `REPO_ROOT` choice,
confirmed by direct, source-independent reproduction. **Classification:
test defect (the test itself is wrong to couple its timeout to live-
repo audit-log state), not a functional or security regression.**

### 8.2 Resolved failure (1) — pre-existing flake, not attributable to this repair

`tests/test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record`
failed pre-repair, passed post-repair. Direct inspection shows this test
mutates and re-reads the real, shared `_audit_dir()` state
(`record_files[0]`, order- and content-dependent on whatever audit
records already exist there) — the same statefulness class as the
`test_audit_verify_cli` case above, in the same unrelated subsystem.
Not attributable to the distribution-name or symlink repair; recorded
here for completeness, not claimed as something this repair fixed.

### 8.3 Byte-pin / authority-bearing-pin inventory

Every broken pin identified above protects **HMIC v1.3 source identity**
of the three repaired modules specifically (via
`implementation_scope_digest`, §9 below) — no pin protecting frozen
verifier *contract* bytes, certification artifacts, or implementation
digests *outside* the three intentionally-repaired modules was broken.
No pin requires downstream regeneration in this phase (no certification
exists yet to regenerate against, §9.3).

### 8.4 Fast-green verdict

**REGRESSION CLEAN WITH EXPECTED HISTORICAL TEST MIGRATION REQUIRED.**
Every net-new failure is either an explicitly historical/stale byte-pin
assertion (14) or an independently-confirmed, source-independent,
pre-existing test-environment defect in an unrelated subsystem (1, plus
1 resolved in the same unrelated subsystem). Zero functional or
authority-bearing regressions. The word "green" is not used unqualified,
since the canonical `pytest -m fast_green` gate does not pass outright
(181 failures present) — this verdict names precisely which category
every one of them falls into.

## 9. HMIC v1.3 source-identity consequences

- **Membership (independently reconstructed, not deferred to module
  docstrings):** `_FROZEN_SRC_PCAE_RELATIVE_FILES` in
  `hatp_mandatory_certification.py` — 22 entries — includes all three
  repaired modules (`core/hatp_class_b_topology_verifier.py`,
  `core/hatp_environment_lock_verifier.py`,
  `core/hatp_class_b_conformance.py`) as its last three entries.
  `_FROZEN_AUTHORITY_BEARING_FILES` (22 src + 6 contract/script entries)
  independently confirmed `len(...) == 28`, matching the module's own
  `assert` at import time (line 1013) — v1.3's full 28-file scope.
- **Pre/post `implementation_scope_digest`**, computed via the
  production `derive_implementation_scope_digest()` against both trees:
  - Pre-repair (worktree `8a18f73d`):
    `b728d368ee830d1e6f6e3c1fc44ca97d4826e3cf124c47c7c549b307dd1a545d`
  - Post-repair (HEAD `28bf137b`):
    `4e3452ba3647df6ccebf2bd093b78c4ae4b8d6eacc3de8212e09ba14804ad2ac`
  - **Digests differ**, as expected: 3 of the 28 frozen files' bytes
    changed.
- **Contract identity:** `git diff 8a18f73d..HEAD --name-only --
  docs/contracts/` returns **zero files** — no contract byte changed.
  Contract identity is unchanged; only implementation/source identity
  changed. These are independently confirmed as distinct, non-conflated
  facts.
- **Existing certification consequence:** no certification artifact
  exists anywhere in `.pcae/` (no file matching `*certification*` or
  `*deploymentbinding*`) — there is nothing existing that could become
  stale, historical, or not-applicable; this is simply **not
  applicable**, since no certification has ever been issued for this
  repository (consistent with "HATP: NOT READY" throughout the 149O
  series).
- **Dell consequence:** Dell's deployed SHA
  `7a3fa971304521cdcb44251e07ef1966baec686a` is confirmed (`git
  merge-base --is-ancestor`) to be an ancestor of the pre-repair
  baseline itself, **68 commits behind** even `8a18f73d` — i.e. Dell's
  deployed source identity predates the diagnosis (7D.6) and the repair
  (7D.7) entirely, not merely "not yet updated with the fix." Mac
  repaired source and Dell deployed source diverge intentionally and by
  a wide, pre-existing margin.
- **Current CHGR (`chgr-541cb08c313b4f8884970172d37c5a1d`) consequence:**
  read directly — published `2026-08-15T07:54:39Z`, hours before the
  7D.7 repair commit (`14:10:25Z` same day). Its `decision_subject` and
  `rationale` scope exclusively to the Phase 149O.20L.7D.3 Action-6
  file-mode repair and the retained Actions-1-5 Dell baseline; its
  `conditions` explicitly exclude any Dell mutation, DeploymentBinding,
  Boundary C/A. It says nothing about, and by publication-time ordering
  *cannot* reference, the verifier source repair or a new source SHA.
  **It does not authorize deployment of the repaired HEAD** — confirmed
  from the record's own primary text, not inferred.

## 10. Independent companion test suite

New module:
`tests/test_phase_149o_20l_7d_8_class_b_verifier_source_repair_independent_verification.py`
— 28 tests, independently authored (imports nothing from 7D.7's own
test module), covering: distribution-identity ground truth and repair
(valid + invalid/fail-closed cases for both REQ-022 and REQ-035); the
full 12-case adversarial symlink matrix from §6.3; the unmodified
`_is_symlink_unsafe` primitive; the real HBDC-REQ-030 call path via
`_check_customization_modules`; HMIC frozen-set membership and count;
contract-file non-modification; and a phase-level guardrail asserting no
`DeploymentBinding`/certification artifact exists in `.pcae/`.

- Run three consecutive times against repaired HEAD: **28 passed, 0
  failed, 0 flaked**, each run.
- **Differential validity check:** the same 28-test module, copied
  (never committed) into the `PYTHONPATH`-shadowed pre-repair worktree
  and run there: **14 passed, 14 failed** — confirming the 14
  repair-dependent tests genuinely discriminate pre- from post-repair
  behavior (not vacuously true), while the 14 repair-independent tests
  (invalid-case fail-closed behavior, HMIC membership, contract
  non-modification, the self-contained pre-repair-literal reproduction,
  broken/loop indeterminacy, the `_is_symlink_unsafe`-unmodified check,
  and the no-DeploymentBinding guardrail) correctly hold in both states.

## 11. REQ-036 reconfirmation (not repaired)

Direct code inspection: `_check_launcher`
(`hatp_environment_lock_verifier.py:368-382`) is byte-for-byte outside
this repair's diff region (only line 339 changed in this file). Its
logic — `shutil.which("pcae")`, `None` → `no_configured_production_launcher_detected`
— is unchanged. 7D.6's own primary Dell evidence
(`docs/PHASE_149O_20L_7D_6_...md` §19-20) independently re-read: Action
9's actual frozen `PATH` is `/usr/bin:/bin:/usr/sbin:/sbin`, excluding
`/opt/pcae/runtime/venv/bin` (the only `PATH` directory where `pcae`
resolves); the documented counterfactual (widening `PATH` to include
that directory) resolves `_check_launcher` to an admin-controlled,
agent-unwritable executable — but that widened `PATH` was not applied
or authorized this phase or any prior phase. **HBDC-REQ-036 remains
OPEN**, unchanged and unrepaired, exactly as 7D.6 left it.

## 12. Future redeployment mutation surface (not implemented)

Because HMIC source identity changed (§9), a future proposition/CHGR
authorizing real-host progression would need to describe, precisely,
that it replaces:

1. The Dell's checked-out source tree (currently pinned at
   `7a3fa971304521cdcb44251e07ef1966baec686a`, 68+ commits behind) —
   fetch/checkout to the repaired candidate SHA `28bf137b5dc95d024e8913b678dce0501a46fd0f`.
2. Nothing in the editable-install `.pth`/`direct_url.json` metadata
   itself needs regeneration for a pure `.py`-content change under an
   existing editable install (no distribution rename, no dependency
   change) — but this must be *verified fresh* on the Dell at execution
   time, not assumed from this Mac-only phase.
3. Fresh `implementation_scope_digest` computation against the deployed
   Dell tree post-checkout, to confirm it matches the Mac-verified value
   above (`4e3452ba...`).
4. A corrected Action-9 invocation `PATH` including
   `/opt/pcae/runtime/venv/bin` (§11), since REQ-036 remains open and
   the counterfactual fix is already documented.
5. An exact rollback/read-back procedure back to the pinned old SHA.
6. Expected real-host residual after all of the above:
   `{HBDC-REQ-042}` only (the architecturally-mandated
   `DeploymentBinding`-absence residual) — not REQ-036, if and only if
   the PATH correction in (4) is included in that future authority.

This phase does not implement, execute, or authorize any of the above.

## 13. Governance results

- **pcae_health:** healthy
- **pcae_check:** passed
- **pcae_status_coherence:** coherent
- **pcae_doctor_task_memory:** warnings (pre-existing — historical
  `tasks/done/` entries missing from `tasks/DONE.md`, predating this
  phase, outside this phase's allowed-file scope, not remediated here)
- **pcae_push_check:** clean (nothing_to_push, at phase entry)
- **pcae_runtime_inspect:** Observed / observe / unavailable
- **pcae_notify_status:** telegram configured/enabled
- **pcae_phase_report_reconcile (149O.20L.7D.7):** not_delivered
  (telegram send failed on 7D.7's own dispatch — pre-existing, read-only
  inspection only, no mutation performed)

## 14. Test results

- **production_diff_reconstructed_from_immutable_git_objects:** exactly
  3 production files changed between `8a18f73d` and `73ea8b23`, zero
  unrelated changes. (passed)
- **hbdc_001_requirements_reconstructed_from_primary_contract:**
  independently re-read, matches 7D.6/7D.7's own text. (passed)
- **distribution_ground_truth_confirmed_pcae_harness:** real
  `importlib.metadata` lookup on this host; `pyproject.toml` cross-
  checked. (passed)
- **req_022_035_pre_repair_reproduction_executed_not_inspected:**
  immutable pre-repair function, executed for real in a disposable
  worktree, reproduces `pcae_distribution_metadata_not_found`. (passed)
- **req_022_035_repaired_downstream_semantics_verified:** repaired
  function reaches real `direct_url.json`/RECORD evidence in both
  positive and negative directions; invalid-case fail-closed confirmed
  via monkeypatched `PackageNotFoundError`. (passed)
- **req_030_pre_repair_reproduction_executed_not_inspected:** immutable
  pre-repair function returns unconditional `True`/`path_is_symlink` on
  a genuinely safe Dell-equivalent topology, executed for real. (passed)
- **req_030_adversarial_symlink_matrix_twelve_cases:** replacement,
  target-mutation, target-ancestor, supplementary-group, ACL-only,
  chained safe/unsafe, broken, loop, relative, inspection-failure — all
  independently reproduced with correct fail-closed/unsafe
  classification. (passed)
- **caller_inventory_independently_reconstructed:** 14 real call sites
  (13 external + 1 internal) via grep, mapped to their HBDC-REQ; matches
  7D.7's claimed count via independent reconstruction, not by trusting
  the count. (passed)
- **historical_j_series_no_functional_regression:** 9 pre-existing
  failures identical pre/post; 2 net-new, both expected clean-tree
  byte-pins; zero logic-assertion regressions. (passed)
- **fast_green_full_ab_diff_worktree_baseline:** pre-repair 166F/7191P/9E,
  post-repair 181F/7202P/9E; 174 common, 16 net-new (15 expected
  byte-pin + 1 independently-confirmed unrelated test defect), 1
  resolved (same unrelated subsystem). (passed)
- **fast_green_verdict:** REGRESSION CLEAN WITH EXPECTED HISTORICAL TEST
  MIGRATION REQUIRED. (passed)
- **hmic_membership_independently_reconstructed:** all three modules
  confirmed among the 22 `_FROZEN_SRC_PCAE_RELATIVE_FILES` / 28
  `_FROZEN_AUTHORITY_BEARING_FILES`. (passed)
- **hmic_pre_post_digest_computed_via_canonical_tooling:** digests
  differ (`b728d368...` → `4e3452ba...`), confirming source-identity
  change; contract-file bytes independently confirmed unchanged.
  (passed)
- **dell_source_identity_confirmed_ancestor_and_stale:** Dell's pinned
  SHA independently confirmed an ancestor of, and 68 commits behind,
  even the pre-repair baseline. (passed)
- **chgr_scope_independently_read_does_not_bind_repaired_source:**
  `chgr-541cb08c...` read directly; published before the repair commit;
  scope text excludes any Dell mutation and does not reference the
  verifier repair. (passed)
- **req_036_reconfirmed_unchanged_not_repaired:** `_check_launcher`
  byte-identical to phase entry; PATH exclusion re-confirmed from 7D.6
  primary evidence. (passed)
- **companion_suite_independently_authored_and_stable:** 28 tests, 3
  consecutive runs, 28/28 passed each time, does not import 7D.7's test
  module. (passed)
- **companion_suite_differential_validity_confirmed:** same 28 tests
  against the pre-repair worktree: 14 pass / 14 fail — proves the suite
  genuinely discriminates repair-dependent behavior. (passed)
- **no_source_mutation_this_phase:** `git diff --stat` against
  `src/pcae/core/hatp_class_b_conformance.py`,
  `hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`
  empty at phase entry and remains empty; only this doc + new test file
  + task-lifecycle/PROJECT_STATUS/CHANGELOG files touched. (passed)
- **no_dell_interaction_this_phase:** no SSH, sudo, or Dell-targeting
  command issued. (passed)
- **no_chgr_no_deploymentbinding_no_certification_this_phase:** none
  created; confirmed by `find .pcae -iname '*deploymentbinding*'` /
  `'*certification*'` returning zero matches, unchanged from phase
  entry. (passed)
- **bootstrap_session_reporting_tests:** not_applicable_this_phase --
  this phase does not modify session bootstrap/reporting surfaces.
  (not_applicable_this_phase)
- **report_notification_tests:** not_applicable_this_phase -- this
  phase does not modify report-notification surfaces.
  (not_applicable_this_phase)

## 15. No-Go Confirmations

This phase performed independent verification only. No production
verifier source was modified — `git diff` against
`hatp_class_b_conformance.py`, `hatp_class_b_topology_verifier.py`, and
`hatp_environment_lock_verifier.py` remains empty for the whole phase.
No contract file was modified. No Dell command of any kind was issued —
no SSH, no sudo, no read or write against `hac-dell`. No Dell venv was
reinstalled or altered. No Action 9 was rerun, modified, or referenced
as an adjudication attempt. No HBDC-REQ-036 repair was made — the
launch wrapper, Dell environment, and Action-9 PATH remain untouched
and REQ-036 remains OPEN. No CHGR was created, amended, or republished
— `chgr-541cb08c313b4f8884970172d37c5a1d` remains exactly as 7D.3
published it. No DeploymentBinding was created. No HMIC certification,
HATP_MANDATORY activation, or Cutover Record was created. No repaired
source was redeployed, fetched, or checked out on any real host beyond
this phase's own disposable, local `git worktree` (created and used for
comparison purposes only, never pushed, never touched Dell). No
--no-verify flag was used. No force push was used. No raw
git commit/push bypassing the governed CLI was used. No historical or
currently-failing test was modified or migrated in this phase — every
net-new failure identified in §8.1 is left exactly as found, with the
future migration surface named but not executed.

## 16. Defect verdicts

- **B-149O.20L.7D.6-1** (distribution-name lookup, HBDC-REQ-022/035):
  **INDEPENDENTLY CONFIRMED REPAIRED IN MAC SOURCE — NOT YET DEPLOYED.**
- **B-149O.20L.7D.6-3** (symlink false-positive, HBDC-REQ-030):
  **INDEPENDENTLY CONFIRMED REPAIRED IN MAC SOURCE — NOT YET DEPLOYED.**
- **B-149O.20L.7D.6-2** (REQ-036 Action-9 PATH defect): **OPEN —
  ACTION-9 INVOCATION/PROPOSITION DEFECT.** Not touched this phase.
- **HBDC-REQ-042:** **EXPECTED RESIDUAL** (no `DeploymentBinding`
  exists; not a repair finding).
- **Dell:** **OLD SOURCE STILL DEPLOYED** (`7a3fa971...`, 68+ commits
  behind pre-repair baseline) — **Actions 1-8 preserved, untouched**.
- **HMIC:** repaired source changes `implementation_scope_digest`
  (HMIC implementation/source identity); contract identity (bound
  contract bytes) unchanged; no existing certification artifact is
  affected since none exists. Deployment/certification consequences
  **pending** a future authorized phase.
- **Boundary C / Boundary A:** **NOT AUTHORIZED.**
- **HATP:** **NOT READY.**
- **Runtime:** Observed / observe / unavailable.

## 17. Recommended next phase

Per the governing instruction's §53/§55: since source verification is
clean (regression-clean-with-expected-migration, both repairs
independently confirmed), the next phase should **not** simply
redeploy. Recommend:

**Phase 149O.20L.7D.9 — Repaired-Source Redeployment + Action-9
Invocation Amendment Proposition.** A proposition/authority phase
(analysis + CHGR, no execution) binding together: (1) the independently
verified repaired source SHA `28bf137b5dc95d024e8913b678dce0501a46fd0f`;
(2) the Dell source update from `7a3fa971...` to that SHA; (3) any
required editable-install/venv refresh verification (per §12); (4) the
HMIC source-identity consequence (§9) and what future certification
would need to re-derive; (5) the corrected Action-9 PATH including
`/opt/pcae/runtime/venv/bin`; (6) an exact rollback/read-back procedure;
(7) expected real Action-9 residual `{HBDC-REQ-042}` only; (8) no
DeploymentBinding; (9) no Boundary C/A. Phase 149O.20L.7E remains
blocked until repaired source is independently verified (this phase),
explicitly authorized for Dell redeployment (149O.20L.7D.9), deployed,
and Action 9 re-run using the corrected, authorized invocation with
exactly `{HBDC-REQ-042}` measured.

## 18. origin/main..HEAD and push status at phase entry

`origin/main..HEAD`: 0 commits (main was fully synced with origin at
phase entry). `git rev-list --count origin/main..HEAD`: 0. `pcae push
check`: clean (nothing_to_push) at phase entry.
