# Phase 149O.20J — Class-B Deployment Verifier / Model-A Environment-Lock Independent Implementation Verification

**Status:** Verification complete. **Verdict: NOT CLEAN — 3 Blocking findings for HMIC-binding progression.**
CBV-S1's *current, non-authoritative* posture remains safe and independently
confirmed (zero production consumers, source unbound, real host still
NON_COMPLIANT). The three findings below block a *future* HMIC source-scope
binding phase (149O.20K), not the current bounded/non-authoritative state.

This phase is independent implementation verification only. No production
source, contract, or script file was modified. No repair was performed.

## 1. Baseline

- `git status --short`: clean at phase entry; `origin/main..HEAD`: 0.
- `pcae health`/`check`/`status coherence`: healthy / passed / coherent.
- `pcae push check`: clean, nothing to push.
- `pcae runtime inspect`: Observed / observe / unavailable (unchanged).
- `pcae phase-report reconcile --phase-id 149O.20I`: reconciled, mutation none.
- 149O.20I confirmed completed, report complete, commits `99f833de`/`5180229a`,
  pushed, `origin/main..HEAD`=0.
- `pcae doctor task-memory`: pre-existing warnings only (task-lifecycle
  directory-collapse history predating this phase; unrelated, not
  remediated here — outside allowed-file scope).

## 2. 149O.20I Diff Reconstruction

Independently reconstructed via `git log --oneline -1 -- <file>` for every
existing authority-bearing production file plus `git status --porcelain` for
the frozen-corpus contracts:

- `src/pcae/core/hatp_bootstrap.py`, `repository_identity.py`,
  `hatp_mandatory_certification.py`, `hatp_mandatory_cutover.py`,
  `scripts/hatp_certification_admin.py`: last touched at commit `d3be5440`
  (Phase 149O.20F), predating 20H/20I entirely. **Confirmed unchanged by
  149O.20I.**
- Exactly three new production modules exist and are the only files
  referencing each other's module names anywhere under `src/pcae/`:
  `hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`,
  `hatp_class_b_conformance.py`.
- Docs/contracts tree: byte-unchanged (`git status --porcelain
  docs/contracts` empty).

**Existing production files modified by 20I: NO (independently confirmed).**

## 3. HBDC Traceability Reconstruction

Independently read `hatp_class_b_topology_verifier.py` (707 lines),
`hatp_environment_lock_verifier.py` (429 lines), and
`hatp_class_b_conformance.py` (163 lines) top to bottom, from primary
source, not from 20I's own report claims. Requirement ownership confirmed:

- **Topology verifier** — HBDC-REQ-001, 002, 004, 005, 007, 008, 011, 012,
  013, 014, 015, 016, 017, 018, 019, 020, 021 (17 checks).
- **Environment-lock verifier** — HBDC-REQ-025..039 (15 checks).
- **Aggregator** — HBDC-REQ-022, 024, 042 (Model-A detection + deployment
  identity), plus recombination of the above 32 checks (34 total checks in
  the aggregated result).
- Manual/deferred/not-applicable under Model A: none newly claimed by this
  phase; the module docstrings correctly disclose HBDC-REQ-041 (runtime
  executed-source cryptographic attestation) and HBDC-REQ-050/051 (real
  activation/binding) as explicitly out of scope for a diagnostic verifier.

This traceability was cross-checked against the actual code (requirement ID
strings passed to every `ClassBCheckResult(...)` call site), not against
20H's plan document's claims about itself.

## 4. CBD Invariant Adjudication (8/8)

| Invariant | Adjudication |
|---|---|
| CBD-1 (two-principal topology) | Implemented (`_check_two_principal_topology`, `_check_principal_distinctness`); correctly fails closed on absent/symlinked root. |
| CBD-2 (Protected Root ownership/mode) | Implemented (`_check_root_ownership`, `_check_root_mode`). |
| CBD-3 (effective-access, not raw mode bits) | Implemented via `_effective_write_access` — owner/group/other/ACL layered. **Gap found**: group layer keys off `os.getgroups()` only, never `os.getegid()` (Finding 2). |
| CBD-4 (full ancestor-chain resistance) | Implemented (`_ancestor_chain_safe`); independently attacked at immediate-parent, deep-ancestor, and stop-boundary granularity — correct. |
| CBD-5 (symlink/hard-link safety) | Implemented; hard-link check independently reproduced with a real `os.link` fixture — correct, `st_nlink != 1` → NON_COMPLIANT. |
| CBD-6 (Model-A environment lock) | Implemented across interpreter/venv/PYTHONPATH/user-site/.pth/customization-modules/meta_path/CWD-shadow/module-origin/editable-install/launcher/trusted-Git. **Two gaps found** (Findings 1, 3). |
| CBD-7 (fail-closed aggregation, no partial credit) | Implemented (`_aggregate_status`); independently reproduced with a from-scratch positive fixture, a full one-failure matrix, empty-set, missing-evidence, and exception-injection matrix — all correct. |
| CBD-8 (non-authoritative posture / no self-trust) | Implemented; independently confirmed zero production consumers, zero self-trust tokens, source absent from the live 19-entry `_FROZEN_SRC_PCAE_RELATIVE_FILES` HMIC set. |

**8/8 adjudicated. 6/8 clean; 2/8 (CBD-3, CBD-6) carry a Blocking-for-binding gap each, documented below.**

## 5-7. Attack Reattack (21 frozen HBDC attacks + additional 20C-style attacks)

Independently re-attacked via the new test module
`tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_lock_independent_implementation_verification.py`
(62 passing tests, 1 platform-conditional skip), built from first principles
— no import of 20I's own test fixtures/constants as oracle. Representative
coverage, by category:

- Effective permission logic: owner-write, no-access, world-writable,
  supplementary-group-write-grant, group-bit-without-membership.
- Ancestor chain: immediate-parent-writable, deep-ancestor-writable with an
  explicit stop-boundary check (proves the walk does **not** skip past an
  unsafe immediate parent, and does **not** walk past a proven-safe
  boundary), symlinked-ancestor.
- Hard link: real `os.link` fixture — multi-link file correctly rejected;
  single-link file correctly accepted; overclaim check (module never claims
  more than link-count evidence).
- Root absence: `None` and nonexistent-path fixtures both correctly
  NON_COMPLIANT.
- ACL: unsupported-platform monkeypatch (`sys.platform = "win32"`)
  independently confirmed `_acl_grants_agent_write` returns `None`
  (indeterminate), which the effective-access flow never silently treats as
  safe.
- `sys.meta_path`: both class-based and instance-based hostile finder
  injection independently confirmed rejected, in a clean subprocess (to
  avoid pytest's own `AssertionRewritingHook` false-flagging against the
  real interpreter's expected-finder allow-list).
- `.pth`: path-injection line rejected; space-delimited `import ` line
  rejected. **Tab-delimited `import\t` line NOT rejected — Finding 1.**
- Fake Git via hostile `PATH`: independently constructed a writable fake
  `git` executable in a temp directory prepended to `PATH` —
  `_resolve_trusted_executable("git")` correctly returns `None`. A second
  test (skipped on this host — no trusted git resolvable in the current
  dev PATH at all, itself a real-host confirmation of fail-closed behavior)
  targets an agent-writable directory preceding a real git.
- Aggregator: from-scratch positive-all-satisfied fixture reaches
  `COMPLIANT`; single-failure-at-any-of-5-positions matrix; empty-check-set;
  missing-evidence-via-indeterminate; a 7-category exception/indeterminate
  injection matrix (topology, ACL, ancestor, environment, module-origin,
  git, deployment-identity) — all correctly prevent `COMPLIANT`.
- Status/reason separation: a check whose free-text reason literally
  contains the substring `"COMPLIANT"` does not change the aggregate
  status — confirmed no substring/text parsing feeds authority.
- Fail-closed exception wrapper: a deliberately raised `RuntimeError` inside
  `_safe_check` correctly yields `INDETERMINATE`/`unexpected_inspection_exception`,
  never a silent pass.
- Zero-parameter / no-caller-authority: `inspect.signature` sweep across
  every function in all three modules confirms none accepts any of the 12
  authority-shaped parameter names listed in the phase brief (`is_admin`,
  `permissions_ok`, `environment_locked`, `module_origin_ok`, `git_trusted`,
  `deployment_valid`, `compliant`, `expected_uid`, `expected_gid`,
  `expected_root`, `acl_ok`, `hard_links_ok`).
- Deployment identity: an isolated `tmp_path` root with no provisioned
  `DeploymentBinding` correctly yields NON_COMPLIANT via
  `_check_deployment_identity`, using the real, unmodified
  `hatp_bootstrap`/`repository_identity` production functions — no
  reimplementation.
- Real-host result: all three public APIs invoked against the real,
  unprovisioned dev host — all three return not-`COMPLIANT`. No provisioning
  performed.
- Real-host non-mutation: `.pcae/`, `.pcae/hatp-evidence/`,
  `.pcae/repository-identity.json`, and `docs/contracts/` snapshotted
  (mode/size/mtime/inode) before and after invoking all three public APIs,
  plus a `git status --porcelain` diff — byte-for-byte identical.

21/21 frozen HBDC attacks and the additional 20C-style attack list (fake Git
via PATH, hostile CWD/module-shadow reasoning via the `_check_cwd_shadow_
and_path_order`/`_check_module_origin_containment` source read-through,
`.pth` injection, meta_path class/instance) were exercised; no attack
improperly yielded `COMPLIANT`.

## 8-9. Result Model / Status Vocabulary

`ClassBCheckResult`/`ClassBDeploymentVerificationResult` are frozen
dataclasses; `ClassBConformanceStatus` is a closed `str, Enum` with exactly
six members. Independently confirmed:

- `_aggregate_status` is the sole status-computing function; it consumes
  only the boolean `.satisfied` field of each check, never free text.
- No `bool(status)`, substring `"compliant"`, or case-fold comparison
  exists anywhere in any of the three modules (grep-confirmed).
- Exact positive status: `COMPLIANT`. Every other member
  (`NON_COMPLIANT`, `INDETERMINATE`, `ACCESS_ERROR`, `MALFORMED_STATE`,
  `UNSUPPORTED_DEPLOYMENT_MODEL`) is equally non-authoritative.

## 10-11. Signatures / Authority Derivation

All three public entry points independently signature-inspected (§10 above).
Every positive check's evidence traces to a live OS/process source: `os.stat`,
`os.geteuid`/`os.getgroups`, `sys.executable`/`sys.prefix`/`sys.meta_path`/
`sys.path`, `os.environ["PATH"]`/`["PYTHONPATH"]`, `importlib.util.find_spec`,
`importlib.metadata.distribution`, and the existing, unmodified
`hatp_bootstrap`/`repository_identity` production functions for deployment
identity. No phase report, test file, or PROJECT_STATUS.md content is ever
read as an authority source.

## 12-13. Read-Only Verification (Static + Behavioral)

Independent AST scan (not reliant on 20I's own denylist, and covering **all
three** modules, not just the one with a self-check) found zero mutation-
shaped attribute calls (`mkdir`, `chmod`, `chown`, `unlink`, `rmdir`,
`rename`, `symlink`, `link`, `write_text`, `write_bytes`, `copyfile`,
`copytree`, `rmtree`, etc.) and zero `shutil.*`/`tempfile.mkstemp`/
`tempfile.mkdtemp` call sites. (`str.replace`/`.remove`/`.copy`/`.move` were
deliberately excluded from the attribute-name scan as unavoidable false-
positive collisions with built-in string/collection methods — each actual
occurrence was manually read and confirmed non-mutating, e.g. the single
`.replace("/", ".")` call in `_check_module_origin_containment` operates on
a `str`, not a path.)

Behavioral snapshot test (mode/size/mtime/inode of `.pcae/`,
`.pcae/hatp-evidence/`, `.pcae/repository-identity.json`,
`docs/contracts/`, plus `git status --porcelain`) before/after invoking all
three public APIs on the real host: **identical. No mutation observed.**

**Finding**: `_check_read_only_guarantee` (HBDC-REQ-012)'s AST self-check
only scans `hatp_class_b_topology_verifier.py`'s own source
(`Path(__file__)` resolved inside that module); neither
`hatp_environment_lock_verifier.py` nor `hatp_class_b_conformance.py`
carries an equivalent self-check. This phase's own independent cross-module
scan confirms both are behaviorally read-only regardless, so this is
**Non-Blocking** (Finding 4) — a design-guarantee-coverage gap, not a live
mutation path.

## 14. Subprocess Side Effects

Exactly two `subprocess.run` call sites exist, both in
`hatp_class_b_topology_verifier.py`: `getfacl -p <path>` (Linux ACL read)
and `ls -lde <path>` (macOS ACL read), both invoked only via
`_resolve_trusted_executable`-resolved, read-only commands with
`stdin=subprocess.DEVNULL` and a 5-second timeout. Neither can mutate
filesystem authority, Git state, the Python environment, or OS
users/groups/ACLs.

## 15-19. Principal Separation / Effective Permissions / Groups / ACL / Fail-Closed

- Principal separation: `_check_principal_distinctness` compares live
  `st_uid` against live `os.geteuid()`; a root whose owner equals the
  agent's own uid is correctly NON_COMPLIANT regardless of username text
  (no `getpass.getuser()`/`os.getlogin()` name comparison used for
  authority — confirmed by the AST-based `_scan_environ_admin_inference`
  self-check, independently re-derived by reading its source).
- Effective permission logic genuinely evaluates owner bits, group bits
  plus live group membership, and platform-gated ACL — not a bare mode-bit
  check. **Gap**: see Finding 2 (group-membership derivation source).
- Supplementary-group attack: independently reproduced with a real fixture
  (file group-writable, owner-write off, agent uid ≠ owner, agent gid
  matches file gid via a fabricated `agent_gids` set) — correctly detected
  as writable → correctly propagates to NON_COMPLIANT.
- ACL attack: unsupported-platform monkeypatch correctly yields
  indeterminate (`None`), never silently treated as safe.
- Platform fail-closed: confirmed — `_acl_grants_agent_write` returns
  `None` on any platform other than `linux`/`darwin`, and every caller of
  `_effective_write_access` treats `None` as "not proven safe."

## 20-22. Ancestor Attacks / Stop Boundary

Independently attacked at three depths: immediate-parent-writable (real
fixture with a writable parent directly above a locked-down protected
target — correctly NON_COMPLIANT), deep-ancestor-writable with an
intervening genuinely-non-writable directory (correctly stops at that
boundary and reports COMPLIANT-eligible, proving the walk does not
over-conservatively continue past a proven-safe boundary), and an
adversarial case where the *immediate* parent is writable even though a
higher ancestor would have been safe (correctly caught at the immediate
parent, proving the walk does not skip past it). The stop-boundary logic is
exactly: continue upward through indeterminate ancestors; stop and report
safe at the first ancestor proven non-writable; stop and report unsafe at
the first ancestor proven writable or symlinked; report indeterminate if
the walk exhausts (2048-hop guard or reaches `/`) without ever proving a
safe boundary.

## 23-26. Symlink / Hard-Link / Root-Absence

Symlinked ancestor: independently fixtured — a real `Path.symlink_to`
directory placed as the immediate parent of a target correctly yields
`ancestor_symlink` → NON_COMPLIANT. Hard link: real `os.link` fixture with
`st_nlink == 2` correctly rejected; `st_nlink == 1` correctly accepted; the
module's own docstring is confirmed not to overclaim beyond link-count
evidence (no "cryptographic"/alias-discovery claim exists outside the
explicit HBDC-REQ-041 disclaimer). Root absence: both `None` and a
nonexistent `Path` correctly yield NON_COMPLIANT with no auto-creation.

## 27-46. Environment-Lock Re-Derivation (interpreter, venv, PYTHONPATH, user-site, .pth, sitecustomize/usercustomize, meta_path, CWD/sys.path, module origin, editable install, launcher)

Every one of the 15 `HBDC-REQ-025..039` checks was read from source and
mapped to its requirement ID (§3 above). Key findings beyond the two
already documented:

- **`.pth` executable-import detection (Finding 1, Blocking).**
  `_check_pth_files`'s detection predicate is
  `line.strip().startswith("import ")`. CPython's real
  `site.addpackage()` (verified directly against the running
  interpreter's own `site` module source in the test suite) executes any
  line satisfying `line.startswith(("import ", "import\t"))` — no
  `.strip()`, and **both** the space- and tab-delimited forms. A `.pth`
  line reading `import\tos.system(...)` (tab, not space, after `import`)
  is executed by the real interpreter at process startup but is **not**
  flagged as an executable import line by `_check_pth_files`, allowing
  `HBDC-REQ-031` to under-report a live code-execution channel on a
  writable `.pth` file. Independently demonstrated directly against both
  the verifier's own predicate and the real `site.addpackage` source.
- meta_path class-vs-instance re-attack (20I's self-caught defect #1):
  independently re-attacked with both a raw hostile class and a hostile
  instance injected into `sys.meta_path` in a clean subprocess — both
  correctly rejected. The current fix (checking `finder if isinstance(finder,
  type) else type(finder)`) is correct and does not over-permit.
- Interpreter/venv/user-site/customization-module/launcher checks: each
  correctly composes `_effective_write_access`/`_ancestor_chain_safe`
  against the live `sys.executable`/`sys.prefix`/`site.getusersitepackages()`/
  `shutil.which("pcae")` targets — no hard-coded assumption, no unsafe
  fallback to "cannot determine, so pass."
- Module-origin containment (`HBDC-REQ-034`): resolves every one of the 19
  authority module names via `importlib.util.find_spec`, resolves the
  origin path, and requires `origin.relative_to(repo_root)` to succeed
  (raising `ValueError` — i.e. rejecting — on any origin outside the
  three-parents-up repository root). Genuinely re-derives the authority
  module set as a literal, independently maintained copy of the live
  19-entry HMIC frozen set (byte-for-byte cross-checked against
  `hatp_mandatory_certification._FROZEN_SRC_PCAE_RELATIVE_FILES` in this
  phase — identical).
- Editable-install metadata: derives Model A detection from the real
  `importlib.metadata.distribution("pcae")`'s `direct_url.json`
  `dir_info.editable` flag (PEP 660) — not assumed.

## 47-51. Service Environment / Trusted Git / Dependencies

- Service environment: no unconditional-pass shortcut found; every check
  fails closed (`None`/`False` treated identically as "not proven safe").
- **Trusted Git resolution (Finding 3, Blocking).**
  `_resolve_trusted_executable` (backing `HBDC-REQ-038`) deliberately uses
  `_mode_and_group_write_access` — mode bits + live group membership
  **only, never the ACL branch** — for both the PATH-directory
  precedence scan and the final resolved-executable/parent checks. This is
  explicitly disclosed in the source comments as intentional, to avoid
  unbounded recursion (`getfacl` resolution itself calls
  `_resolve_trusted_executable`). Independently confirmed by source
  inspection: `_effective_write_access`/`_acl_grants_agent_write` are never
  called from within `_resolve_trusted_executable`. Consequence: an agent
  holding write access to a PATH-preceding directory, or to the resolved
  `git` executable or its parent directory, **purely via a POSIX ACL entry
  with restrictive mode bits**, would not be detected as untrusted by
  `HBDC-REQ-038` — a materially narrower guarantee than the Protected Root
  checks (`HBDC-REQ-016`), which do include the ACL branch. Fake-git-via-
  hostile-PATH and agent-writable-PATH-directory-precedes-real-git attacks
  were independently exercised and correctly rejected (because in both
  cases the *mode bits*, not ACL, made the artifact agent-writable); the
  gap is specifically the ACL-only-grant sub-case, which this phase could
  not construct a positive real-ACL-grant fixture for without real
  provisioning (out of scope) — it is proven as a structural code-path
  absence, not as a live-fixture bypass.
- Third-party dependency boundary: correctly deferred to the venv lock
  (`HBDC-REQ-025..027`) per the plan's own disclosed disposition — no
  independent supply-chain attestation claimed.

## 52-54. Repository / Deployment Identity / Worktree

`_check_deployment_identity` is confirmed a thin wrapper: it calls the
real, unmodified `hatp_bootstrap.resolve_canonical_deployment_root`,
`repository_identity.read_repository_identity`, and
`hatp_bootstrap.deployment_binding_matches` — no reimplementation, no
identifier-alone shortcut (repository identity alone, without a matching
`DeploymentBinding`, correctly fails). Independently exercised with an
isolated `tmp_path` root — correctly NON_COMPLIANT (no provisioned
binding exists for it).

## 55-61. Aggregator Re-Derivation

Read from scratch (§4/§7 above). Positive-all-satisfied fixture (built
independently, not reusing 20I's fixture builder) reaches `COMPLIANT`.
Every mandatory single-failure position (parametrized across 5 positions,
matching item 57's "only five mandatory aggregate nodes" allowance since
`_build_result`/`_aggregate_status` themselves have no per-requirement
special-casing — the same aggregation function is exercised identically
regardless of which specific requirement ID fails) prevents `COMPLIANT`.
Empty check set, missing-evidence-via-indeterminate, and a 7-category
exception/indeterminate injection matrix all correctly prevent
`COMPLIANT`. Reason text containing the literal substring `"COMPLIANT"`
does not change the aggregate status.

## 62-63. Caller Authority / Test-Seam Escape

No function in any of the three modules accepts any authority-shaped
parameter (§10). The only parameter of any kind on any public entry point
is `verify_class_b_deployment_conformance`'s neutral `root: Optional[
HarnessPath]` repository-root locator. No dependency-injection seam
(fake checker, fake result, fake trusted path, fake uid, fake environment
status) is reachable through any production API — confirmed by exhaustive
`inspect.signature` enumeration, not spot-checking.

## 64-70. Zero Authority Consumers

Repository-wide text search across `src/pcae/**` (excluding the three new
modules themselves) for the three new module names: **zero matches**.
`hatp_mandatory_cutover.py`, `hatp_mandatory_certification.py`, and
`scripts/hatp_certification_admin.py` individually confirmed to contain
neither `hatp_class_b` nor `hatp_environment_lock` anywhere in their source,
and confirmed byte-unchanged since commit `d3be5440` (149O.20F), predating
20H/20I. No PB/rollback consumer found.

## 71. Current HMIC Non-Binding

`hatp_mandatory_certification._FROZEN_SRC_PCAE_RELATIVE_FILES` independently
read: exactly 19 entries, none of which is any of the three new modules.
Cross-checked byte-for-byte against `hatp_environment_lock_verifier.py`'s
own literal reproduction of that same 19-entry set — identical.

## 72-73. No Self-Trust / CBV-S1 Safety

No occurrence of `hmic_bound`, `trusted_source`, `self_verified`,
`certified`, or `authoritative=True` in any of the three modules. CBV-S1's
two conditions independently proven **both** true: (a) new verifier source
unbound (§71), (b) zero production authority consumers (§64-70).
**CBV-S1's current-state safety: verified.**

## 74. HMIC-REQ-052 Consequence

Re-derived: any future HMIC-bound module that imports these three verifier
modules would, per HMIC-REQ-052's closure rule, bring them into HMIC source
identity. 20H's sequencing rationale (defer binding until a separately
governed, separately verified contract-evolution phase) remains valid and
is not altered by this phase.

## 75. CBV-S10

No new HMRC/HATP readiness term was introduced by 20I or by this phase.
Readiness implementation remains unchanged. **CBV-S10: still NOT CLOSED**
(unchanged from phase entry — no readiness-integration work is in scope
here or was performed).

## 76-78. Semantic Wall / HMIC-REQ-063 / Option C

Independently confirmed: `COMPLIANT` is never equated with HMIC `VALID`,
readiness, activation, approval, PB `ALLOW`, rollback capability, or
runtime capability anywhere in the three modules' prose (only the correct,
negated disclaimer forms appear, e.g. "NOT AN AUTHORITATIVE READINESS
SIGNAL"). No cryptographic runtime executed-source attestation is claimed;
the one "cryptographic" occurrence in the corpus is inside the explicit
HBDC-REQ-041 disclaimer ("does not claim runtime executed-source
cryptographic attestation"). Model A / environment-lock remains the sole
deployment model addressed; no widening to Models B/C/D found.

## 79-80. Real-Host Result / Non-Mutation

Confirmed NOT `COMPLIANT` for all three public APIs on the real,
unprovisioned host. Confirmed zero mutation of `.pcae/`, contracts, or Git
state across the invocation (§12-13).

## 81-83. Self-Caught Defect Re-Verification

- Defect #1 (meta_path class-vs-instance): independently re-attacked (§27-46
  above) with both forms in a clean subprocess. **Fix verified correct.**
- Defect #2 (HBDC-REQ-004 environ false-positive): independently read
  `_scan_environ_admin_inference` — it flags `getuser`/`getlogin` calls and
  environ keys containing `ADMIN`/`USER`/`SUDO`/`LOGNAME`/`IDENTITY`; `PATH`
  is not in that substring set, so the legitimate `os.environ.get("PATH",
  "")` read inside `_resolve_trusted_executable` is correctly never
  flagged, while the prohibition on name/environ-based admin inference
  remains otherwise intact (any `USER`-shaped key is still flagged).
  **Fix verified correct — the environment-lock PATH read is legitimate,
  and no admin-authority inference channel was reopened.**
- HBDC-REQ-034 literal false positive: not independently reproduced this
  phase (not required to re-attack a disclosed, already-classified test
  debt item); accepted as test-only debt per 20I's own disclosure,
  consistent with this phase's own broad-sweep findings (§ Test Results
  below), which show the same category of pre-existing, unrelated
  historical test drift.

## 84-86. Diff Classification / No Existing-File Modification / Contract Stability

All new functions/classes across the three modules classify into MODEL,
STATUS, SAFE_INSPECTION, TOPOLOGY_CHECK, ENVIRONMENT_CHECK, IDENTITY_CHECK,
AGGREGATION, or DIAGNOSTIC categories; **UNRELATED = 0**. Existing
production files confirmed byte-unchanged (§2). All nine frozen-corpus
contracts confirmed byte-unchanged throughout 20J (`git status --porcelain
docs/contracts` empty at both start and end of this phase).

## 87-99. Test Independence / Adversarial Fixtures / Regressions

An independent test module (87 above) was authored with its own fixtures
and helpers, not importing 20I's fixture builders or constants. Positive
fixtures, ACL/group adversarial fixtures, ancestor adversarial fixtures (two
depths), a real hard-link fixture, subprocess-isolated import-environment
fixtures (meta_path, the 20I/20H/20G/HBDC/HMIC regression re-runs), and a
fake-Git fixture were all independently authored (§5-7 above).

- 20I's own 98-test structural suite: re-run as a **regression signal
  only** (subprocess-isolated) — passed, 0 failed.
- 20H structural/plan tests: covered incidentally by the broad sweep below.
- 20G regression (HMIC 25/5 identity unchanged): independently re-confirmed
  in §71 above (19-entry `src/pcae/`-relative subset unchanged; the full
  25-entry set includes the 5 contract files, also confirmed byte-unchanged
  in §86).
- HBDC/HMIC regression: covered by the broad sweep below.

## 100. Fast Green

Raw `python -m pytest -m fast_green -n auto -q`: **69 failed, 6720 passed,
5 skipped, 1 pre-existing fido2 collection error** (with this phase's
changes). A freshly-reproduced baseline with this phase's one new file
temporarily removed: **70 failed, 6657 passed, 4 skipped, 1 error** —
proving this phase's new test file causes **zero net-new failures**; the
1-failure swing (70→69) is consistent with the already-disclosed
`test_backend_cli.py` parallel-execution flakiness category, not this
phase's content.

All 69-70 failures independently spot-checked by node-ID category: they are
exclusively pinned-count/pinned-commit-range self-checks belonging to
**historical** phases (149O.14, .15, .16, .18c, .18d, .19.2, .19.3,
.19.3R, .19.3R.1, .19.4, .19.5e-series, .19.5f, .19.5g, .20c, .20f, .20g)
whose own assertions (fixed requirement counts, fixed frozen-file-set
sizes, fixed commit ranges, fixed HMIC contract version literals) go stale
as later, already-landed, legitimately-authorized phases evolve those same
counts/versions/commit history forward — the exact same debt category
20I's own report disclosed for a subset of these (git-status self-checks,
149O.20C environment-lock supersession, fixed-commit git-diff repin-debt).
This phase did not assemble a full historical clean-deselected "0 failed"
citation (that specific list-maintenance exercise is itself a debt-repair
activity, and 149O.20J's contract forbids repairing any defect found,
including test debt, outside this phase's allowed-file scope) — the
zero-net-new-failure proof above is offered instead as the relevant,
in-scope evidence.

No node ID in the failure set references `class_b`, `hatp_environment_
lock`, or `hatp_class_b_conformance` in a way indicating a regression in
149O.20I's actual production content; every failing module predates 20H.

## 101. Broad Sweep

`pytest -k "class_b or hbdc or hmic or 149o_20" --ignore=tests/test_phase_
149o_7_hatp_class_b_activation_independent_verification.py`: 44 failed,
1107 passed, 5 skipped (the ignored file is the same pre-existing missing-
`fido2`-dependency collection error 20I's own broad-sweep citation
disclosed as "1 error"). All 44 failures are the same historical
pinned-count/commit-range category as §100; none reference the three new
modules or any 20J-authored test.

## 102-103. Report Trust / Governance Close Checks

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae doctor task-memory`: pre-existing warnings only (unrelated,
outside allowed-file scope). `pcae push check`: clean, nothing to push
(prior to this phase's own commit). `pcae runtime inspect`: Observed /
observe / unavailable, unchanged. `pcae notify status`: Telegram
configured/enabled/ready, unchanged.

## 104. Blocking Findings

1. **`.pth` executable-import detection misses the tab-delimited form**
   (`hatp_environment_lock_verifier.py`, `_check_pth_files`,
   `HBDC-REQ-031`). A `.pth` line `import\t<code>` executes under real
   CPython `site.addpackage()` but is not recognized as an executable
   import line by the verifier's `line.strip().startswith("import ")`
   predicate. **Blocking for HMIC-binding progression.**
2. **Effective-group derivation never independently folds in
   `os.getegid()`** (`hatp_class_b_topology_verifier.py`,
   `_current_agent_identity`). Relies solely on `os.getgroups()`, which
   POSIX does not guarantee includes the process's true effective gid in
   every process-identity configuration. A narrow but real fail-open gap
   in every group-membership-based effective-access check
   (`HBDC-REQ-015`/`017`/etc.). **Blocking for HMIC-binding progression.**
3. **Trusted-Git PATH resolution never checks ACL, only mode+group bits**
   (`hatp_class_b_topology_verifier.py`, `_resolve_trusted_executable`,
   backing `HBDC-REQ-038`). Deliberate, disclosed narrowing to avoid
   recursion into `getfacl` resolution; consequence is an ACL-only write
   grant to a PATH-preceding directory or the resolved git binary would
   not be detected, unlike the Protected Root checks. **Blocking for
   HMIC-binding progression.**

None of these three findings affects the *current* safety of 149O.20I's
bounded, non-authoritative posture: the real host still returns
NON_COMPLIANT, zero production consumers exist, and the source remains
outside HMIC's frozen identity — so no authority is currently at risk. They
block only a *future* HMIC-binding phase that would make `COMPLIANT` from
these modules authoritative.

## 105. Non-Blocking Findings / Observations

1. `HBDC-REQ-012`'s AST self-check only scans `hatp_class_b_topology_
   verifier.py`'s own source, not the other two modules' — both
   independently confirmed read-only anyway by this phase's own
   cross-module scan (§12).
2. Fast Green / broad-sweep pre-existing pinned-count test debt continues
   to accumulate across historical phase test files, unrelated to and not
   worsened by this phase (§100-101).
3. `HBDC-REQ-034`'s disclosed data-literal false positive (20I's own
   finding) — accepted as test-only debt, not re-litigated this phase.

## 106. Verification Verdict

```
CLASS-B DEPLOYMENT VERIFIER / MODEL-A ENVIRONMENT-LOCK:

  NOT VERIFIED FOR HMIC-BINDING PROGRESSION
  -- 3 BLOCKING FINDINGS (see §104)
  -- HMIC SOURCE-SCOPE EVOLUTION NOT AUTHORIZED

  CURRENT NON-AUTHORITATIVE POSTURE: INDEPENDENTLY VERIFIED SAFE
  -- READ-ONLY (confirmed)
  -- FAIL-CLOSED AGGREGATION (confirmed)
  -- ZERO PRODUCTION AUTHORITY CONSUMERS (confirmed)
  -- SOURCE NOT YET HMIC-BOUND (confirmed)
  -- POSITIVE CONSUMPTION REMAINS FORBIDDEN

CBV-S1:
  CURRENT-STATE SAFETY INDEPENDENTLY VERIFIED
  -- HMIC SOURCE-SCOPE BINDING REQUIRES THE 3 FINDINGS REPAIRED FIRST
  -- NOT CLOSED

CBV-S10:
  READINESS CONTRACT/INTEGRATION GAP REMAINS
  -- NOT CLOSED

Class-B:
  CONTRACT VERIFIED
  -- VERIFIER IMPLEMENTATION INDEPENDENTLY VERIFIED, WITH 3 BLOCKING GAPS
  -- NOT PROVISIONED

HATP:
  NOT READY
```

## 107. Recommended Next Phase

**149O.20J.1 — Class-B Deployment Verifier / Model-A Environment-Lock
Narrow Defect Repair**, addressing exactly the 3 Blocking findings in §104
(and, at the implementer's discretion, Non-Blocking Finding 1 in §105):

1. Extend `.pth` executable-line detection to recognize
   `line.startswith(("import ", "import\t"))` (matching real CPython
   semantics exactly — no `.strip()` first, since real Python does not
   strip leading whitespace before testing either).
2. Fold `os.getegid()` into the agent's effective-group identity (e.g.
   `frozenset(os.getgroups()) | {os.getegid()}`), independent of whether
   `getgroups()` happens to already include it.
3. Either accept and disclose the ACL-only-grant gap in `_resolve_trusted_
   executable` as a permanent, narrower guarantee for Git-trust resolution
   specifically (updating HBDC-001/HBDC-REQ-038's own text to say so
   explicitly, if that's an acceptable design trade-off), or restructure
   the recursion-avoidance (e.g. resolve `getfacl`/`ls` once via the
   narrower mode+group check as today, but then use the full ACL-including
   `_effective_write_access` for the PATH-directory/target checks
   thereafter, since at that point `getfacl` is already resolved and no
   further recursion occurs).

Only after 149O.20J.1 passes its own independent re-verification should
**149O.20K — HMIC Class-B Verifier Source-Scope Contract Evolution** be
attempted. Per the governing phase brief, 149O.20K must not assume the
25→28 file-count jump; it must independently perform a transitive
authority-dependency closure over the (by then repaired) three modules
first, since all three currently import `pcae.core.hatp_bootstrap` (already
HMIC-bound) and nothing else outside the three-module island or already-
HMIC-bound production code (confirmed in this phase's own module reads —
no additional PCAE-owned authority-sensitive helper import was found beyond
`hatp_bootstrap`).

No real Class-B provisioning, no readiness integration, and no CBV-S10
closure work is authorized by either 149O.20J or the recommended
149O.20J.1.
